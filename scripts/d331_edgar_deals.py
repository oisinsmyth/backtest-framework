"""D331 -- M&A announcement dates from SEC EDGAR for every symbol in the
us_shorts_daily_raw fixture.

Reproducible pull. Every date in the output traces to a real EDGAR filing
(accession number + URL). Nothing is inferred from prices.

Pipeline
--------
1. Fixture spans      first/last bar per symbol from the CSV (cached in temp/).
2. Symbol -> CIK      (a) https://www.sec.gov/files/company_tickers.json
                      (b) https://www.sec.gov/include/ticker.txt
                      (c) EDGAR full-text search (efts) for the ticker string
                          as a phrase, entity aggregation, dominance rule.
                      Every candidate is checked against the entity's own
                      filing history (submissions API): it must have filed
                      something inside the symbol's window and must have
                      existed as a filer no later than a year after the
                      symbol's first bar -- a recycled ticker fails this.
                      (a)/(b) + consistent  -> "high"
                      (c)     + consistent  -> "low"   (text match, not a map)
                      otherwise             -> "unresolved" (reason recorded)
3. Filings            https://data.sec.gov/submissions/CIK##########.json plus
                      its paginated filings/files. Direct deal forms are taken
                      by form type inside [first_bar - 365d, last_bar]. 8-Ks
                      are taken only when the submissions index lists Item
                      1.01 AND EDGAR full-text search (same CIK, same window,
                      forms=8-K) matches merger language.
4. Output             written to temp/edgar_out/ first, then copied to
                      data/fixtures/us_shorts_daily_raw_deals.json and
                      data/d331_edgar_coverage.txt (also printed) ONLY when
                      the run covered every symbol (no --limit/--symbols)
                      and did not abort. A smoke test never touches data/.

SEC fair-access: descriptive User-Agent with a project contact address (the
SEC edge returns 403 to any User-Agent without an email-shaped token; this is
a project mailbox, not a personal one), <= 8 requests/second across all
threads, retry with backoff on 429/403/5xx. Raw 200 responses are cached under
temp/edgar/ so a re-run does not re-fetch.

Usage
-----
    uv run python scripts/d331_edgar_deals.py            # full pull
    uv run python scripts/d331_edgar_deals.py --limit 30 # smoke test
    uv run python scripts/d331_edgar_deals.py --symbols ABAX,ACAS,AAMRQ
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, "data", "fixtures", "us_shorts_daily_raw.csv.gz")
FIXTURE_META = os.path.join(ROOT, "data", "fixtures", "us_shorts_daily_raw.meta.json")
EVENTS = os.path.join(ROOT, "data", "fixtures", "us_shorts_daily_raw_events.json")
OUT_JSON = os.path.join(ROOT, "data", "fixtures", "us_shorts_daily_raw_deals.json")
OUT_REPORT = os.path.join(ROOT, "data", "d331_edgar_coverage.txt")
CACHE_DIR = os.path.join(ROOT, "temp", "edgar")
OUT_TMP_DIR = os.path.join(ROOT, "temp", "edgar_out")   # outputs land here; copied to data/ only when complete

USER_AGENT = "BacktestFramework research script research@backtest-framework.org"
HEADERS = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"}
MAX_RPS = 8.0
WORKERS = 6
WINDOW_BEFORE_DAYS = 365          # fixture first bar - 1 year

URL_COMPANY_TICKERS = "https://www.sec.gov/files/company_tickers.json"
URL_TICKER_TXT = "https://www.sec.gov/include/ticker.txt"
URL_SUBMISSIONS = "https://data.sec.gov/submissions/{name}"
URL_EFTS = "https://efts.sec.gov/LATEST/search-index"
URL_FILING_INDEX = "https://www.sec.gov/Archives/edgar/data/{cik_int}/{adsh_nodash}/{adsh}-index.htm"

# Forms taken directly from the submissions index (exact form type, no /A).
DIRECT_FORMS = ["DEFM14A", "PREM14A", "SC TO-T", "SC TO-C", "SC 14D9", "425"]

# 8-K merger-language queries for EDGAR full-text search. Each 8-K hit records
# which of these matched. A hit is kept as a deal only if the submissions
# index also lists Item 1.01 on that 8-K.
EFTS_8K_QUERIES = {
    "merger": '"agreement and plan of merger" OR "merger agreement" OR "plan of merger" OR "agreement and plan of reorganization"',
    "tender": '"tender offer"',
    "acquisition": '"acquisition agreement" OR "stock purchase agreement" OR "share purchase agreement"',
}

# Ticker-text resolution queries (dead names). {sym} is the ticker string.
EFTS_TICKER_QUERIES = {
    "efts_ticker_context": '"symbol {sym}" OR "NYSE {sym}" OR "NASDAQ {sym}" OR "NYSE MKT {sym}" OR "NYSE American {sym}" OR "NASDAQ Global Select Market {sym}"',
    "efts_ticker_bare": '"{sym}"',
}
AGREE_MIN_DOCS, AGREE_MIN_SHARE = 3, 0.25   # context query top entity, when bare query agrees
BARE_MIN_DOCS, BARE_MIN_SHARE = 5, 0.60     # bare query alone (context query returned nothing)
CTX_MIN_DOCS, CTX_MIN_SHARE = 10, 0.50      # context query alone (bare query is noise for short tickers)

# Second pass (per-year, issuer forms only). Large-cap tickers are swamped in
# the unrestricted index by banks' structured-note prospectuses ("NYSE: DIS"),
# so the yearly pass looks only at forms an issuer files about itself. It
# yields a SEQUENCE of CIKs when a ticker migrated to a new registrant
# (holding-company reorganisation: Alphabet, APA Corp, Allergan plc ...).
ISSUER_FORMS = "10-K,10-Q,8-K,DEF 14A,20-F,40-F,6-K,S-1,S-4,10-K405,10-KSB,10-QSB"
YEAR_MIN_DOCS, YEAR_MIN_SHARE = 3, 0.50     # a year is assigned to its top entity when ...
YEAR_ALT_MIN_DOCS, YEAR_ALT_RATIO = 5, 2.0  # ... or when it has >= 5 docs and 2x the runner-up
CIK_MIN_YEARS, CIK_MIN_DOCS = 2, 5          # an entity needs 2 assigned years or 5 docs in total
SEGMENT_PAD_DAYS = 365                      # filings taken from first assigned year - 1y .. last + 1y

MAX_EFTS_PAGES = 100  # 100 hits/page; efts caps at 10,000 anyway


# --------------------------------------------------------------------------
# HTTP: rate limit, cache, retry
# --------------------------------------------------------------------------
class Fetcher:
    def __init__(self, cache_dir: str, max_rps: float):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.min_interval = 1.0 / max_rps
        self._lock = threading.Lock()
        self._next_slot = 0.0
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.events: list[str] = []          # rate-limit / error events
        self.n_fetched = 0
        self.n_cached = 0
        self.consecutive_failures = 0
        self.abort = False

    def _wait_slot(self):
        with self._lock:
            now = time.monotonic()
            t = max(now, self._next_slot)
            self._next_slot = t + self.min_interval
        delay = t - time.monotonic()
        if delay > 0:
            time.sleep(delay)

    def _key(self, url: str, params: dict | None) -> str:
        blob = url + "?" + json.dumps(params or {}, sort_keys=True)
        return hashlib.sha1(blob.encode()).hexdigest()

    def log(self, msg: str):
        with self._lock:
            self.events.append(f"{dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}Z {msg}")

    def get(self, url: str, params: dict | None = None, kind: str = "misc") -> str | None:
        """Return response text (200 only). Cached on disk by url+params."""
        sub = os.path.join(self.cache_dir, kind)
        os.makedirs(sub, exist_ok=True)
        path = os.path.join(sub, self._key(url, params) + ".json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                rec = json.load(f)
            with self._lock:
                self.n_cached += 1
            return rec["text"]
        if self.abort:
            return None
        backoff = 1.0
        for attempt in range(7):
            self._wait_slot()
            try:
                r = self.session.get(url, params=params, timeout=60)
            except requests.RequestException as e:
                self.log(f"EXC {type(e).__name__} {url} {params} attempt={attempt}")
                time.sleep(backoff); backoff *= 2
                continue
            if r.status_code == 200 and not (kind.startswith("efts") and '"hits"' not in r.text[:400]):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"url": url, "params": params, "fetched": dt.datetime.now(dt.timezone.utc).isoformat(), "text": r.text}, f)
                with self._lock:
                    self.n_fetched += 1
                    self.consecutive_failures = 0
                return r.text
            if r.status_code == 404:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"url": url, "params": params, "fetched": dt.datetime.now(dt.timezone.utc).isoformat(), "text": None, "status": 404}, f)
                self.log(f"404 {url}")
                return None
            self.log(f"HTTP {r.status_code} {url} {params} attempt={attempt} body={r.text[:80]!r}")
            with self._lock:
                self.consecutive_failures += 1
                if self.consecutive_failures >= 40:
                    self.abort = True
                    self.log("ABORT: 40 consecutive failures -- SEC blocking or rate-limiting persistently")
                    return None
            if r.status_code in (429, 403):
                time.sleep(max(backoff, 10.0))
            else:
                time.sleep(backoff)
            backoff = min(backoff * 2, 60.0)
        self.log(f"GIVEUP {url} {params}")
        return None

    def get_json(self, url: str, params: dict | None = None, kind: str = "misc"):
        t = self.get(url, params, kind)
        return None if t is None else json.loads(t)


# --------------------------------------------------------------------------
# Fixture spans
# --------------------------------------------------------------------------
def fixture_spans() -> dict[str, dict]:
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache = os.path.join(CACHE_DIR, "fixture_spans.json")
    mtime = os.path.getmtime(FIXTURE)
    if os.path.exists(cache):
        with open(cache) as f:
            rec = json.load(f)
        if rec.get("fixture_mtime") == mtime:
            return rec["spans"]
    df = pd.read_csv(FIXTURE, usecols=["timestamp", "symbol"])
    g = df.groupby("symbol")["timestamp"].agg(["min", "max", "count"])
    spans = {s: {"first_bar": r["min"][:10], "last_bar": r["max"][:10], "n_bars": int(r["count"])} for s, r in g.iterrows()}
    with open(cache, "w") as f:
        json.dump({"fixture_mtime": mtime, "spans": spans}, f)
    return spans


def window_for(span: dict) -> tuple[str, str]:
    start = (dt.date.fromisoformat(span["first_bar"]) - dt.timedelta(days=WINDOW_BEFORE_DAYS)).isoformat()
    return start, span["last_bar"]


# --------------------------------------------------------------------------
# Submissions API
# --------------------------------------------------------------------------
_CIK_RE = re.compile(r"\(CIK (\d{10})\)")


def cik10(x) -> str:
    return str(int(x)).zfill(10)


def load_submissions(F: Fetcher, cik: str, win_start: str, win_end: str) -> dict | None:
    """Return {'name','tickers','earliest','latest','filings':[{form,date,adsh,items,doc}...]}.

    `filings` is complete for the window (paginated files overlapping the
    window are fetched); `earliest`/`latest` cover the entity's whole history
    without fetching every page (files carry filingFrom/filingTo)."""
    j = F.get_json(URL_SUBMISSIONS.format(name=f"CIK{cik}.json"), kind="submissions")
    if j is None:
        return None
    recent = j["filings"]["recent"]
    dates = list(recent["filingDate"])
    earliest = min(dates) if dates else None
    latest = max(dates) if dates else None
    chunks = [recent]
    for fl in j["filings"].get("files", []):
        earliest = min(earliest or fl["filingFrom"], fl["filingFrom"])
        latest = max(latest or fl["filingTo"], fl["filingTo"])
        if fl["filingTo"] >= win_start and fl["filingFrom"] <= win_end:
            pj = F.get_json(URL_SUBMISSIONS.format(name=fl["name"]), kind="submissions")
            if pj is not None:
                chunks.append(pj)
    filings = []
    for ch in chunks:
        n = len(ch["form"])
        items = ch.get("items") or [""] * n
        docs = ch.get("primaryDocument") or [""] * n
        for i in range(n):
            d = ch["filingDate"][i]
            if win_start <= d <= win_end:
                filings.append({"form": ch["form"][i], "date": d, "adsh": ch["accessionNumber"][i],
                                "items": items[i] or "", "doc": docs[i] or ""})
    return {"cik": cik, "name": j.get("name"), "tickers": j.get("tickers") or [],
            "former_names": [fn.get("name") for fn in j.get("formerNames") or []],
            "earliest": earliest, "latest": latest, "filings": filings}


def span_consistent(sub: dict, span: dict) -> tuple[bool, str]:
    """Entity must have existed as a filer by first_bar + 365d and have filed
    inside [first_bar - 365d, last_bar]. A recycled ticker fails the first."""
    if sub is None:
        return False, "no submissions"
    if sub["earliest"] is None:
        return False, "entity has no filings"
    limit = (dt.date.fromisoformat(span["first_bar"]) + dt.timedelta(days=365)).isoformat()
    if sub["earliest"] > limit:
        return False, f"entity's earliest filing {sub['earliest']} is after first_bar+365d ({limit}); ticker recycled?"
    if not sub["filings"]:
        return False, "entity filed nothing inside the symbol's window"
    return True, "ok"


# --------------------------------------------------------------------------
# EFTS full-text search
# --------------------------------------------------------------------------
def efts_search(F: Fetcher, q: str, forms: str | None, start: str, end: str, cik: str | None, kind: str,
                max_pages: int = MAX_EFTS_PAGES) -> tuple[list[dict], dict, int]:
    """All hits (paginated) + entity aggregation by CIK + total."""
    params = {"q": q, "dateRange": "custom", "startdt": start, "enddt": end}
    if forms:
        params["forms"] = forms
    if cik:
        params["ciks"] = cik
    hits, agg, total = [], {}, 0
    for page in range(max_pages):
        p = dict(params)
        if page:
            p["from"] = str(page * 100)
        j = F.get_json(URL_EFTS, p, kind=kind)
        if j is None or "hits" not in j:
            F.log(f"EFTS no result q={q!r} cik={cik} page={page}")
            break
        total = j["hits"]["total"]["value"]
        page_hits = j["hits"]["hits"]
        hits.extend(page_hits)
        if page == 0:
            for b in j.get("aggregations", {}).get("entity_filter", {}).get("buckets", []):
                m = _CIK_RE.search(b["key"])
                if m:
                    agg[m.group(1)] = agg.get(m.group(1), 0) + b["doc_count"]
        if len(page_hits) < 100 or len(hits) >= total:
            break
    return hits, agg, total


def _agg_summary(q: str, agg: dict) -> dict:
    ranked = sorted(agg.items(), key=lambda kv: -kv[1])
    tot = sum(agg.values())
    top_cik, top_n = ranked[0]
    return {"query": q, "top_cik": top_cik, "top_docs": top_n, "agg_docs": tot,
            "share": round(top_n / tot, 3) if tot else 0.0, "runner_up": ranked[1:4]}


def resolve_by_efts(F: Fetcher, sym: str, span: dict) -> tuple[str | None, str, dict]:
    """Ticker-string full-text resolution. Returns (cik, method, detail).

    Two independent phrasings -- the ticker in a listing context ("symbol X",
    "NYSE X", "NASDAQ X") and the bare ticker -- must agree on the top entity,
    which must carry >= AGREE_MIN_DOCS docs and >= AGREE_MIN_SHARE of the
    context query's entity buckets. Affiliates (a filing subsidiary, a managed
    vehicle) take the remaining share, which is why a 50% floor failed AMR,
    Abaxis and American Capital in the smoke test. If the context query has
    no hits at all, the bare query alone is accepted only when dominant."""
    start, end = window_for(span)
    end_plus = (dt.date.fromisoformat(end) + dt.timedelta(days=365)).isoformat()
    variants = [sym]
    if len(sym) == 5 and sym.endswith("Q"):
        variants.append(sym[:-1])           # bankruptcy suffix; base ticker in older filings
    detail: dict = {"attempts": []}
    for v in variants:
        q_ctx = EFTS_TICKER_QUERIES["efts_ticker_context"].format(sym=v)
        q_bare = EFTS_TICKER_QUERIES["efts_ticker_bare"].format(sym=v)
        _, agg_ctx, _ = efts_search(F, q_ctx, None, start, end_plus, None, kind="efts_ticker", max_pages=1)
        _, agg_bare, _ = efts_search(F, q_bare, None, start, end_plus, None, kind="efts_ticker", max_pages=1)
        s_ctx = _agg_summary(q_ctx, agg_ctx) if agg_ctx else None
        s_bare = _agg_summary(q_bare, agg_bare) if agg_bare else None
        detail["attempts"].append({"variant": v, "context": s_ctx, "bare": s_bare})
        suffix = "" if v == sym else "(base)"
        if s_ctx and s_bare and s_ctx["top_cik"] == s_bare["top_cik"] \
                and s_ctx["top_docs"] >= AGREE_MIN_DOCS and s_ctx["share"] >= AGREE_MIN_SHARE:
            return s_ctx["top_cik"], "efts_ticker_agree" + suffix, detail
        if s_ctx is None and s_bare and s_bare["top_docs"] >= BARE_MIN_DOCS and s_bare["share"] >= BARE_MIN_SHARE:
            return s_bare["top_cik"], "efts_ticker_bare_dominant" + suffix, detail
        # Short tickers are ordinary words ("AT", "GA", "CEO"): the bare query is
        # noise, so accept the context query alone when it is clearly dominant.
        if s_ctx and s_ctx["top_docs"] >= CTX_MIN_DOCS and s_ctx["share"] >= CTX_MIN_SHARE:
            return s_ctx["top_cik"], "efts_ticker_context_dominant" + suffix, detail
    return None, "efts_ticker_none", detail


def resolve_yearly(F: Fetcher, sym: str, ws: str, we: str) -> tuple[dict, list]:
    """Per-year ticker-context query over issuer forms only.

    Returns ({cik: {"years", "docs", "from", "to"}}, per-year rows). Each year
    goes to its top entity when the year rule holds; an entity is kept when it
    owns >= CIK_MIN_YEARS years or >= CIK_MIN_DOCS docs. Its filing window is
    the assigned years padded by SEGMENT_PAD_DAYS, clipped to [ws, we]."""
    q = EFTS_TICKER_QUERIES["efts_ticker_context"].format(sym=sym)
    rows, per_cik = [], collections.defaultdict(lambda: {"years": [], "docs": 0})
    for y in range(int(ws[:4]), int(we[:4]) + 1):
        s, e = max(ws, f"{y}-01-01"), min(we, f"{y}-12-31")
        if s > e:
            continue
        _, agg, _ = efts_search(F, q, ISSUER_FORMS, s, e, None, kind="efts_ticker_year", max_pages=1)
        if not agg:
            rows.append({"year": y, "top_cik": None})
            continue
        sm = _agg_summary(q, agg)
        ru = sm["runner_up"][0][1] if sm["runner_up"] else 0
        ok = (sm["top_docs"] >= YEAR_MIN_DOCS and sm["share"] >= YEAR_MIN_SHARE) or \
             (sm["top_docs"] >= YEAR_ALT_MIN_DOCS and sm["top_docs"] >= YEAR_ALT_RATIO * ru)
        rows.append({"year": y, "top_cik": sm["top_cik"], "docs": sm["top_docs"], "share": sm["share"],
                     "runner_up_docs": ru, "assigned": ok})
        if ok:
            per_cik[sm["top_cik"]]["years"].append(y)
            per_cik[sm["top_cik"]]["docs"] += sm["top_docs"]
    segs = {}
    for cik, d in per_cik.items():
        if len(d["years"]) >= CIK_MIN_YEARS or d["docs"] >= CIK_MIN_DOCS:
            y0, y1 = min(d["years"]), max(d["years"])
            f = (dt.date(y0, 1, 1) - dt.timedelta(days=SEGMENT_PAD_DAYS)).isoformat()
            t = (dt.date(y1, 12, 31) + dt.timedelta(days=SEGMENT_PAD_DAYS)).isoformat()
            segs[cik] = {"years": d["years"], "docs": d["docs"], "from": max(ws, f), "to": min(we, t), "query": q,
                         "forms": ISSUER_FORMS}
    return segs, rows


def symbol_phrase_docs(F: Fetcher, sym: str, cik: str, start: str, end: str) -> int:
    """Confirmation: how many of the entity's OWN issuer-form documents in the
    window contain the phrase "symbol SYM". Real issuers say 'under the symbol
    "DIS"' in their 10-Ks; the false positives seen in testing (investor
    presentations, S-4s of unrelated small caps) matched only the exchange
    phrasing and never this one."""
    q = f'"symbol {sym}"'
    _, _, total = efts_search(F, q, ISSUER_FORMS, start, end, cik, kind="efts_confirm", max_pages=1)
    return total


def merge_windows(entries: list[dict], ws: str, we: str) -> list[list[str]]:
    """Gaps in [ws, we] not covered by any entry's [from, to]."""
    ivs = sorted((e["from"], e["to"]) for e in entries)
    gaps, cur = [], ws
    for f, t in ivs:
        if f > cur:
            gaps.append([cur, (dt.date.fromisoformat(f) - dt.timedelta(days=1)).isoformat()])
        cur = max(cur, (dt.date.fromisoformat(t) + dt.timedelta(days=1)).isoformat())
    if cur <= we:
        gaps.append([cur, we])
    return gaps


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="only the first N symbols (smoke test)")
    ap.add_argument("--symbols", type=str, default="", help="comma list of symbols")
    ap.add_argument("--workers", type=int, default=WORKERS)
    args = ap.parse_args()
    t0 = time.time()

    spans = fixture_spans()
    with open(FIXTURE_META) as f:
        meta = json.load(f)["symbols"]
    with open(EVENTS) as f:
        ev = json.load(f)
    assert set(spans) == set(meta) == set(ev["dividends"]) == set(ev["splits"]), "symbol lists disagree"
    symbols = sorted(spans)
    if args.symbols:
        symbols = [s for s in args.symbols.split(",") if s in spans]
    if args.limit:
        symbols = symbols[: args.limit]
    dead = {s for s in symbols if meta[s]["cohort"] == "dead"}
    print(f"{len(symbols)} symbols, {len(dead)} dead; window = first_bar - {WINDOW_BEFORE_DAYS}d .. last_bar", flush=True)

    F = Fetcher(CACHE_DIR, MAX_RPS)

    # --- current ticker maps -------------------------------------------------
    ct = F.get_json(URL_COMPANY_TICKERS, kind="maps")
    cur = {v["ticker"].upper(): (cik10(v["cik_str"]), v["title"]) for v in ct.values()}
    tt = F.get(URL_TICKER_TXT, kind="maps")
    txt = {}
    for line in tt.splitlines():
        p = line.split("\t")
        if len(p) == 2:
            txt[p[0].upper()] = cik10(p[1])
    print(f"company_tickers.json: {len(cur)} tickers; ticker.txt: {len(txt)} tickers", flush=True)

    # --- stage 2: resolve + filings per symbol ---------------------------------
    resolution: dict[str, dict] = {}
    deals: dict[str, list] = {}
    eightk_no_101: dict[str, list] = {}
    subs_cache: dict[str, dict | None] = {}
    lock = threading.Lock()

    def get_sub(cik, ws, we):
        key = (cik, ws, we)
        with lock:
            if key in subs_cache:
                return subs_cache[key]
        s = load_submissions(F, cik, ws, we)
        with lock:
            subs_cache[key] = s
        return s

    def work(sym: str):
        span = spans[sym]
        ws, we = window_for(span)
        tried = []
        res = {"cik": None, "method": None, "confidence": "unresolved", "entity": None, "tried": tried}
        candidates = []
        if sym in cur:
            candidates.append((cur[sym][0], "company_tickers.json"))
        if sym in txt and (not candidates or txt[sym] != candidates[0][0]):
            candidates.append((txt[sym], "ticker.txt"))
        chosen = None
        for cik, method in candidates:
            sub = get_sub(cik, ws, we)
            ok, why = span_consistent(sub, span)
            tried.append({"cik": cik, "method": method, "ok": ok, "why": why, "entity": sub["name"] if sub else None})
            if ok:
                chosen = (cik, method, "high", sub)
                break
        if chosen is None:
            cik, method, detail = resolve_by_efts(F, sym, span)
            if cik:
                sub = get_sub(cik, ws, we)
                ok, why = span_consistent(sub, span)
                n_conf = symbol_phrase_docs(F, sym, cik, ws, we)
                if ok and n_conf == 0 and method.startswith("efts_ticker_context_dominant"):
                    ok, why = False, "context query dominant but the entity's own filings never say 'symbol SYM'"
                tried.append({"cik": cik, "method": method, "ok": ok, "why": why, "entity": sub["name"] if sub else None,
                              "efts": detail, "symbol_phrase_docs": n_conf})
                if ok:
                    chosen = (cik, method, "low", sub)
            else:
                tried.append({"cik": None, "method": method, "ok": False,
                              "why": "full-text ticker queries did not agree on a dominant entity", "efts": detail})
        # ---- mapping: an ordered list of {cik, from, to, method, confidence} ----
        # A ticker can belong to a SEQUENCE of registrants (holding-company
        # reorganisation). Pass 1 gives the single best entity; the per-year
        # pass fills the rest of the window, and the record says what covers what.
        mapping: list[dict] = []
        yearly_rows = None
        pred_until = None            # search predecessors before this date
        if chosen is not None:
            cik, method, conf, sub = chosen
            mapping.append({"cik": cik, "entity": sub["name"], "method": method, "confidence": conf,
                            "from": ws, "to": we, "entity_earliest_filing": sub["earliest"],
                            "symbol_phrase_docs": tried[-1].get("symbol_phrase_docs")})
            if sub["earliest"] and sub["earliest"] > span["first_bar"]:
                # entity started filing after the symbol's series began: look for a predecessor
                pred_until = sub["earliest"]
        else:
            # a current-map entity that exists only in the LATER part of the window
            # is a successor registrant: keep it for its own part
            for t in tried:
                if t.get("cik") and t["method"] in ("company_tickers.json", "ticker.txt") and "after first_bar" in t["why"]:
                    sub = get_sub(t["cik"], ws, we)
                    if sub and sub["filings"]:
                        mapping.append({"cik": t["cik"], "entity": sub["name"], "method": t["method"] + "(successor)",
                                        "confidence": "high", "from": sub["earliest"], "to": we,
                                        "entity_earliest_filing": sub["earliest"]})
                        pred_until = sub["earliest"]
                        break
            pred_until = pred_until or we
        if pred_until is not None and pred_until > ws:
            segs, yearly_rows = resolve_yearly(F, sym, ws, pred_until)
            known = {m["cik"] for m in mapping}
            found, rejected = [], []
            for cik2, seg in sorted(segs.items(), key=lambda kv: kv[1]["years"][0]):
                if cik2 in known:
                    continue
                sub2 = get_sub(cik2, seg["from"], seg["to"])
                if sub2 is None or not sub2["filings"]:
                    continue
                n_conf = symbol_phrase_docs(F, sym, cik2, seg["from"], seg["to"])
                entry = {"cik": cik2, "entity": sub2["name"], "method": "efts_ticker_yearly", "confidence": "low",
                         "from": seg["from"], "to": seg["to"], "years": seg["years"], "docs": seg["docs"],
                         "symbol_phrase_docs": n_conf, "entity_earliest_filing": sub2["earliest"]}
                if n_conf == 0:
                    entry["why_rejected"] = "entity's own filings never say 'symbol SYM'"
                    rejected.append(entry)
                    continue
                found.append(entry)
            if rejected:
                res["yearly_rejected"] = rejected
            if found and mapping:
                # the latest predecessor hands over to the known entity: let it run up to the handover + pad
                latest = max(found, key=lambda m: m["to"])
                latest["to"] = min(we, (dt.date.fromisoformat(pred_until) + dt.timedelta(days=SEGMENT_PAD_DAYS)).isoformat())
            mapping.extend(found)
        if not mapping:
            res["yearly"] = yearly_rows
            return sym, res, [], []

        mapping.sort(key=lambda m: (m["to"], m["from"]))
        primary = mapping[-1]                                   # the entity holding the ticker latest
        gaps = merge_windows(mapping, ws, we)
        res.update({"cik": primary["cik"], "method": primary["method"], "confidence": primary["confidence"],
                    "entity": primary["entity"], "window": [ws, we], "ciks": mapping,
                    "coverage": "full" if not gaps else "partial", "uncovered": gaps})
        if yearly_rows is not None:
            res["yearly"] = yearly_rows

        # ---- filings from every mapped entity inside its own window -----------
        out, other, seen = [], [], set()
        for m in mapping:
            cik = m["cik"]
            sub = get_sub(cik, m["from"], m["to"])
            if sub is None:
                continue
            for fl in sub["filings"]:
                if fl["form"] in DIRECT_FORMS and fl["adsh"] not in seen:
                    seen.add(fl["adsh"])
                    out.append(mk_deal(cik, fl, matched=None))
            # 8-K: Item 1.01 in the index AND merger language in full text
            eightk = {fl["adsh"]: fl for fl in sub["filings"] if fl["form"] == "8-K"}
            matched: dict[str, set] = collections.defaultdict(set)
            if eightk:
                for tag, q in EFTS_8K_QUERIES.items():
                    hits, _, _ = efts_search(F, q, "8-K", m["from"], m["to"], cik, kind="efts_8k")
                    for h in hits:
                        adsh = h["_source"].get("adsh")
                        if adsh in eightk:
                            matched[adsh].add(tag)
            for adsh, tags in matched.items():
                if adsh in seen:
                    continue
                seen.add(adsh)
                fl = eightk[adsh]
                items = [x.strip() for x in fl["items"].split(",") if x.strip()]
                rec = mk_deal(cik, fl, matched=sorted(tags))
                (out if "1.01" in items else other).append(rec)
        out.sort(key=lambda r: (r["date"], r["form"], r["accession"]))
        other.sort(key=lambda r: (r["date"], r["accession"]))
        return sym, res, out, other

    def mk_deal(cik, fl, matched):
        adsh = fl["adsh"]
        rec = {"date": fl["date"], "form": fl["form"], "cik": cik, "accession": adsh,
               "url": URL_FILING_INDEX.format(cik_int=int(cik), adsh_nodash=adsh.replace("-", ""), adsh=adsh)}
        if fl["form"] == "8-K":
            rec["items"] = fl["items"]
            rec["matched_queries"] = matched
        return rec

    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(work, s): s for s in symbols}
        for fut in as_completed(futs):
            sym = futs[fut]
            try:
                sym, res, out, other = fut.result()
            except Exception as e:  # keep going; record
                F.log(f"WORKER EXC {sym}: {type(e).__name__}: {e}")
                res, out, other = {"cik": None, "method": "error", "confidence": "unresolved", "error": repr(e)}, [], []
            resolution[sym] = res
            deals[sym] = out
            if other:
                eightk_no_101[sym] = other
            done += 1
            if done % 50 == 0 or done == len(symbols):
                print(f"  {done}/{len(symbols)}  fetched={F.n_fetched} cached={F.n_cached} events={len(F.events)} "
                      f"{time.time()-t0:.0f}s", flush=True)
            if F.abort:
                print("ABORTING on persistent failures; saving partial output", flush=True)
                break

    # --- output ---------------------------------------------------------------
    pulled_on = dt.date.today().isoformat()
    out_json = {
        "pulled_on": pulled_on,
        "source": "SEC EDGAR",
        "user_agent": USER_AGENT,
        "fixture": os.path.basename(FIXTURE),
        "window": f"per symbol: first_bar - {WINDOW_BEFORE_DAYS}d .. last_bar (filing date)",
        "date_semantics": "FILING DATE of the EDGAR filing (not effective, not close).",
        "forms": DIRECT_FORMS + ["8-K (Item 1.01 in the submissions index AND merger-language full-text match)"],
        "queries": {
            "eightk_full_text": EFTS_8K_QUERIES,
            "ticker_resolution_full_text": EFTS_TICKER_QUERIES,
            "ticker_resolution_rule": {
                "efts_ticker_agree": f"context and bare queries name the same top CIK; context top_docs >= {AGREE_MIN_DOCS} and share >= {AGREE_MIN_SHARE}",
                "efts_ticker_bare_dominant": f"context query empty; bare top_docs >= {BARE_MIN_DOCS} and share >= {BARE_MIN_SHARE}",
                "efts_ticker_context_dominant": f"queries disagree (bare query is noise for short tickers); context top_docs >= {CTX_MIN_DOCS} and share >= {CTX_MIN_SHARE}",
                "(base)": "5-letter ticker ending in Q (bankruptcy suffix) also tried without the Q",
                "efts_ticker_yearly": f"second pass: context query per calendar year restricted to forms {ISSUER_FORMS}; "
                                      f"a year is assigned to its top entity when top_docs >= {YEAR_MIN_DOCS} and share >= {YEAR_MIN_SHARE}, "
                                      f"or top_docs >= {YEAR_ALT_MIN_DOCS} and >= {YEAR_ALT_RATIO}x the runner-up; an entity is kept with "
                                      f">= {CIK_MIN_YEARS} assigned years or >= {CIK_MIN_DOCS} docs; its filing window is its assigned years "
                                      f"padded by {SEGMENT_PAD_DAYS}d",
                "(successor)": "current-map entity whose EDGAR history starts after first_bar+365d: kept from its earliest filing; "
                               "predecessors searched with the yearly pass before that date",
            },
        },
        "endpoints": [URL_COMPANY_TICKERS, URL_TICKER_TXT, URL_SUBMISSIONS.format(name="CIK##########.json"),
                      URL_EFTS + "?q=...&forms=...&ciks=...&dateRange=custom&startdt=...&enddt=...&from=..."],
        "confidence_definition": {
            "high": "ticker found in a current SEC ticker map AND the entity's filing history is consistent with the fixture span",
            "low": "ticker resolved by full-text search for the ticker string (dominant entity) AND span-consistent; a text match, not a map",
            "unresolved": "no candidate passed the span-consistency check",
            "note": "top-level cik/method/confidence describe the PRIMARY entity (the one holding the ticker latest). "
                    "resolution[sym].ciks lists every mapped entity with its own window, method and confidence; "
                    "coverage is 'partial' when some of [window] is covered by none, and 'uncovered' lists the gaps. "
                    "Every deal record carries the cik it came from.",
        },
        "span_consistency": "entity's earliest filing <= first_bar + 365d AND >= 1 filing inside the window",
        "complete": not F.abort,
        "resolution": {s: resolution[s] for s in sorted(resolution)},
        "deals": {s: deals[s] for s in sorted(deals)},
        "eightk_merger_language_without_item_101": {s: eightk_no_101[s] for s in sorted(eightk_no_101)},
        "fetch_events": F.events,
    }
    # Write to temp/edgar_out/ first; the data/ paths are replaced only by a
    # COMPLETE full run (every symbol, no --limit/--symbols, no abort), so a
    # smoke test or a cut-short run can never leave a partial output in data/.
    os.makedirs(OUT_TMP_DIR, exist_ok=True)
    tmp_json = os.path.join(OUT_TMP_DIR, os.path.basename(OUT_JSON))
    tmp_report = os.path.join(OUT_TMP_DIR, os.path.basename(OUT_REPORT))
    with open(tmp_json, "w", encoding="utf-8") as f:
        json.dump(out_json, f, indent=1)

    report = build_report(symbols, dead, meta, spans, resolution, deals, eightk_no_101, F, pulled_on, t0)
    with open(tmp_report, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print(f"wrote {tmp_json}\nwrote {tmp_report}")

    full_run = not args.limit and not args.symbols
    all_done = set(resolution) == set(spans) and set(deals) == set(spans)
    if full_run and all_done and not F.abort:
        os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
        shutil.copyfile(tmp_json, OUT_JSON)
        shutil.copyfile(tmp_report, OUT_REPORT)
        print(f"complete full run: copied to {OUT_JSON}\n                   and {OUT_REPORT}")
    else:
        print(f"NOT copied to data/ (full_run={full_run} all_done={all_done} abort={F.abort}); "
              f"output stays in {OUT_TMP_DIR}")


def build_report(symbols, dead, meta, spans, resolution, deals, eightk_no_101, F, pulled_on, t0) -> str:
    L = []
    P = L.append
    n = len(symbols)
    conf = collections.Counter(resolution[s]["confidence"] for s in symbols if s in resolution)
    meth = collections.Counter(resolution[s].get("method") for s in symbols if s in resolution)
    unres = [s for s in symbols if s in resolution and resolution[s]["confidence"] == "unresolved"]
    unres_dead = [s for s in unres if s in dead]
    P("D331 EDGAR M&A-announcement pull -- coverage report")
    P(f"pulled_on: {pulled_on}   runtime: {time.time()-t0:.0f}s   complete: {not F.abort}")
    P(f"user_agent: {USER_AGENT}")
    P(f"requests fetched: {F.n_fetched}   served from temp/edgar cache: {F.n_cached}")
    P("")
    P("SYMBOL -> CIK RESOLUTION")
    P(f"  symbols total      : {n}   (dead {len(dead)}, alive {n-len(dead)})")
    P(f"  resolved high      : {conf.get('high',0)}")
    P(f"  resolved low       : {conf.get('low',0)}")
    P(f"  unresolved         : {conf.get('unresolved',0)}   of which dead names: {len(unres_dead)}, alive: {len(unres)-len(unres_dead)}")
    P("  by method:")
    for m, c in meth.most_common():
        P(f"    {m!s:32s} {c}")
    hd = collections.Counter((resolution[s]["confidence"], s in dead) for s in symbols if s in resolution)
    P("  confidence x cohort:")
    for (c, d), k in sorted(hd.items()):
        P(f"    {c:10s} {'dead' if d else 'alive':5s} {k}")
    multi = [s for s in symbols if s in resolution and len(resolution[s].get("ciks") or []) > 1]
    partial = [s for s in symbols if s in resolution and resolution[s].get("coverage") == "partial"]
    P(f"  symbols mapped to >1 CIK over time (ticker migrated between registrants): {len(multi)}")
    for s in multi[:60]:
        P("    " + s + ": " + " -> ".join(f"{m['cik']}[{m['from'][:4]}..{m['to'][:4]},{m['confidence']}]" for m in resolution[s]["ciks"]))
    if len(multi) > 60:
        P(f"    ... {len(multi)-60} more in the JSON")
    P(f"  symbols whose window is only PARTIALLY covered by mapped entities: {len(partial)}")
    for s in partial[:40]:
        P(f"    {s}: uncovered {resolution[s]['uncovered']}")
    if len(partial) > 40:
        P(f"    ... {len(partial)-40} more in the JSON")
    P("")
    P("UNRESOLVED SYMBOLS (reason of the last candidate tried)")
    for s in unres:
        tried = resolution[s].get("tried") or []
        why = tried[-1]["why"] if tried else resolution[s].get("error", "?")
        cands = ", ".join(f"{t.get('cik')}:{t.get('method')}" for t in tried if t.get("cik"))
        P(f"  {s:6s} {'dead ' if s in dead else 'alive'} {spans[s]['first_bar']}..{spans[s]['last_bar']} | {why}" + (f" | tried {cands}" if cands else ""))
    P("")
    P("DEAL FILINGS")
    with_deal = [s for s in symbols if deals.get(s)]
    P(f"  symbols with >= 1 deal filing : {len(with_deal)} of {conf.get('high',0)+conf.get('low',0)} resolved "
      f"(dead {sum(1 for s in with_deal if s in dead)}, alive {sum(1 for s in with_deal if s not in dead)})")
    P(f"  total deal filings            : {sum(len(v) for v in deals.values())}")
    fc = collections.Counter(r["form"] for v in deals.values() for r in v)
    P("  by form type:")
    for fm, c in fc.most_common():
        P(f"    {fm:10s} {c}")
    tags = collections.Counter(t for v in deals.values() for r in v if r["form"] == "8-K" for t in r["matched_queries"])
    P(f"  8-K Item 1.01 hits by matched query: {dict(tags)}")
    combos = collections.Counter("+".join(r["matched_queries"]) for v in deals.values() for r in v if r["form"] == "8-K")
    P("  8-K Item 1.01 hits by matched-query combination (a 'tender'-only hit is usually a DEBT tender):")
    for k, c in combos.most_common():
        P(f"    {k:30s} {c}")
    P(f"  8-Ks with merger language but NO Item 1.01 (kept aside, not deals): "
      f"{sum(len(v) for v in eightk_no_101.values())} across {len(eightk_no_101)} symbols")
    yrs = collections.Counter(r["date"][:4] for v in deals.values() for r in v)
    P("  deal filings by year: " + ", ".join(f"{y}:{c}" for y, c in sorted(yrs.items())))
    P("")
    P("TOP 20 SYMBOLS BY NUMBER OF DEAL FILINGS")
    top = sorted(with_deal, key=lambda s: -len(deals[s]))[:20]
    for s in top:
        fcs = collections.Counter(r["form"] for r in deals[s])
        P(f"  {s:6s} {len(deals[s]):4d}  {resolution[s]['entity'][:40] if resolution[s].get('entity') else '':40s} "
          + " ".join(f"{k}={v}" for k, v in fcs.most_common()))
    P("")
    P("ERRORS / RATE-LIMIT EVENTS")
    ec = collections.Counter(" ".join(e.split(" ", 3)[1:3]) for e in F.events)
    P(f"  total events: {len(F.events)}   by kind/status: {dict(ec)}")
    hard = [e for e in F.events if e.split(" ", 2)[1] in ("GIVEUP", "ABORT", "EFTS", "WORKER", "404")]
    P(f"  unrecovered (GIVEUP/ABORT/no-result/worker/404): {len(hard)}")
    for e in hard[:40]:
        P("  " + e[:220])
    P(f"  all events (retried 500s included) are in the JSON's fetch_events; first 5:")
    for e in F.events[:5]:
        P("  " + e[:160])
    P("")
    P("NOTES FOR DOWNSTREAM")
    P("  - Dates are FILING dates. 425 / SC TO-C often precede the 8-K by a day or trail it; take the earliest per episode.")
    P("  - 8-K Item 1.01 covers every material definitive agreement (credit facilities, licences, supply deals). The")
    P("    full-text filter keeps only 8-Ks whose text matches the merger/tender/acquisition phrases; an 8-K about a")
    P("    credit agreement that mentions an earlier merger agreement will still pass. matched_queries says which.")
    P("  - Direct forms are taken by exact form type; amendments (/A) are excluded. SC TO-I (issuer self-tender) excluded.")
    P("  - Submissions list filings where the entity is the SUBJECT too (bidder-filed SC TO-T appears under the target).")
    P("  - 425 is filed by acquirers as well; a fixture name that is the BUYER also gets hits. Role is not recorded.")
    P("  - 'low' resolutions came from the ticker string appearing in filing text; verify before relying on one name.")
    P("  - EDGAR full-text search covers 2001 onward; the fixture starts 2010, so no window is truncated by it.")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
