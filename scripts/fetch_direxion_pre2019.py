"""LETF close-flow Phase 1, the pre-N-PORT half: Direxion SPXL/SPXS from EDGAR, 2015-10-31 -> 2019-10-31 (LETF-A3;
D637 "Before 2019-10: what exists"). Direxion Shares ETF Trust, CIK 1424958; SPXL = Direxion Daily S&P 500 Bull 3X
(series S000022767), SPXS = Direxion Daily S&P 500 Bear 3X (S000022765). Fiscal year ends 31 October.

    uv run python scripts/fetch_direxion_pre2019.py            # fetch (cached) + extract -> data/letf/direxion_pre2019_filings.csv
    uv run python scripts/fetch_direxion_pre2019.py --check    # every known-answer check, printed; exit 1 if a provenance gate fails
    uv run python scripts/fetch_direxion_pre2019.py --selftest # every gate must RAISE on a deliberately broken input

SOURCES (EDGAR only; cached under data/raw/letf/edgar_pre2019/, gitignored; the User-Agent and the <= 8 requests/s
pacing are build_letf_aum.py's). The filing list is read from the trust's submissions shard
CIK0001424958-submissions-002.json (filings 2013-06 -> 2021-06: nothing in it is dated on or after the seal):
- N-CSR (31 Oct) and N-CSRS (30 Apr): Statement of Assets and Liabilities ("Net Assets", "Receivable for Fund shares
  sold", "Payable for Fund shares redeemed") and Statement of Changes in Net Assets (the CURRENT-period column only:
  operations, distributions, proceeds from shares sold, cost of shares redeemed, transaction fees, beginning and end
  net assets, shares sold and repurchased).
- N-Q (31 Jan, 31 Jul) to 2019-01-31, and NPORT-EX for 2019-07-31 (N-Q was replaced by N-PORT Part F; the trust's
  2019-07-31 schedule of investments is filed as NPORT-EX): each fund's "TOTAL NET ASSETS - 100.0% $ x".
- NSAR-A (30 Apr) and NSAR-B (31 Oct), filed through 2017 (N-SAR was rescinded in 2018): item 28 rows A..F (the six
  months of the report period; column 01 = total NAV of shares sold, 04 = total NAV redeemed, in $000s) and item 74T
  (net assets, $000s), for the series whose item 7C name is the fund's. Stored in dollars (x 1000); the quote keeps
  the filed thousands.
- NSAR-A and N-CSRS for 2015-04-30 are also read (before the window), because the FY2015 identity and the NSAR-B
  2015 half-year check need the first half of fiscal 2015.

EVERY NUMBER IS RE-VERIFIABLE FROM THE RAW BYTES. Each CSV row carries a `quote` (at most 15 words) that `--check`
re-finds in the cached document after one fixed normalisation (tags -> space, HTML entities unescaped, whitespace
collapsed; `norm()` below), and the value is re-parsed from the quote's last number. Nothing is typed by hand: every
value is located by a parser whose anchors are asserted (fund names in the table header, the period dates in the
column headers, the column count, one match per row label).

SIGNS ARE AS PRINTED. Statement values carry the statement's sign (parentheses = negative, so cost of shares redeemed
and distributions are negative). N-SAR item 28 redemptions are the form's positive magnitudes (one filed negative is
kept as filed). Identity: end = beginning + operations + distributions + sales + redemptions + transaction fees.

FIELDS beyond the brief's list, and why: `transaction_fees_usd` (a capital-share line without which the statement
identity does not close), `receivable_shares_sold_usd` and `payable_shares_redeemed_usd` (the unsettled creations and
redemptions inside a statement's net assets; they explain the N-CSR vs N-PORT difference at 2019-10-31).

SEAL (A10): nothing dated on or after 2025-03-01 is read.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "letf" / "edgar_pre2019"
OUT = REPO / "data" / "letf" / "direxion_pre2019_filings.csv"
NPORT = REPO / "data" / "letf" / "nport_reports.json"
LOG = RAW / "fetch_log.json"
UA = {"User-Agent": "BacktestFramework research script research@backtest-framework.org"}  # never a personal address
CIK = 1424958
SHARD = "CIK0001424958-submissions-002.json"
RESERVED_FROM = "2025-03-01"
WINDOW = ("2015-10-31", "2019-10-31")
PRE_WINDOW = {("NSAR-A", "2015-04-30"), ("N-CSRS", "2015-04-30")}  # first half of FY2015, for checks
FORMS = {"N-CSR", "N-CSRS", "N-Q", "NSAR-A", "NSAR-B", "NPORT-EX"}
SIDE = {"SPXL": "Bull", "SPXS": "Bear"}
SERIES = {"SPXL": "S000022767", "SPXS": "S000022765"}
NSAR_NAME = {t: f"DIREXION DAILY S&P 500 {s.upper()} 3X SHARES" for t, s in SIDE.items()}
HTML_NAME = {t: rf"Direxion Daily S&P 500 ?®? ?{s} 3X Shares" for t, s in SIDE.items()}
QUARTER_ENDS = [f"{y}-{md}" for y in range(2015, 2020) for md in ("01-31", "04-30", "07-31", "10-31")
                if WINDOW[0] <= f"{y}-{md}" <= WINDOW[1]]
COLS = ["ticker", "field", "value", "period_start", "period_end", "as_of", "form", "accession", "url", "locator",
        "quote", "fetched_utc"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
_log: dict[str, dict] = {}


class GateError(AssertionError):
    pass


def gate(ok: bool, msg: str) -> None:
    if not ok:
        raise GateError(msg)


# ---------------------------------------------------------------- fetching

def _load_log() -> None:
    if not _log and LOG.exists():
        _log.update(json.loads(LOG.read_text(encoding="utf-8")))


def get(url: str, rel: str) -> bytes:
    """build_letf_aum.get()'s cache-and-pace pattern, plus a fetch log so every row can carry its access time. A file
    already in the cache with no log entry (fetched by this study's exploration pass, same User-Agent and pacing) is
    logged with its file mtime as the access time, and says so."""
    _load_log()
    cache = RAW / rel
    if cache.exists():
        if rel not in _log:
            ts = datetime.fromtimestamp(cache.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            _log[rel] = {"url": url, "fetched_utc": ts, "basis": "cache file mtime"}
        return cache.read_bytes()
    time.sleep(0.15)  # <= 8 requests a second
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        b = r.read()
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(b)
    _log[rel] = {"url": url, "fetched_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "basis": "download"}
    return b


def _save_log() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    LOG.write_text(json.dumps(_log, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def filing_list() -> tuple[list[dict], list[tuple[dict, dict]]]:
    """The filings to read, from the submissions shard. Returns (filings, [(used filing, a second accession of the
    same form and report date)]); the second is fetched and must be byte-identical (checked)."""
    s = json.loads(get(f"https://data.sec.gov/submissions/{SHARD}", f"submissions/{SHARD}"))
    gate(max(s["filingDate"]) < RESERVED_FROM, "the submissions shard lists a filing on or after the seal")
    rows = [dict(accession=a, form=f, filed=d, report_date=r, doc=p)
            for a, f, d, r, p in zip(s["accessionNumber"], s["form"], s["filingDate"], s["reportDate"],
                                     s["primaryDocument"])]
    keep = [r for r in rows if r["form"] in FORMS
            and (WINDOW[0] <= r["report_date"] <= WINDOW[1] or (r["form"], r["report_date"]) in PRE_WINDOW)]
    keep.sort(key=lambda r: (r["report_date"], r["form"], r["accession"]))
    out, dups, seen = [], [], {}
    for r in keep:
        r["url"] = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{r['accession'].replace('-', '')}/{r['doc']}"
        r["rel"] = f"docs/{r['accession']}_{r['doc']}"
        k = (r["form"], r["report_date"])
        if k in seen:
            dups.append((seen[k], r))
            continue
        seen[k] = r
        out.append(r)
    return out, dups


def norm(b: bytes) -> str:
    """The ONE normalisation every quote is found under: tags -> space, entities unescaped, whitespace collapsed."""
    t = b.decode("utf-8", "replace")
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t)


# ---------------------------------------------------------------- parsing helpers

TOKEN = re.compile(r"\s*(\$|\(\s*[\d,]+\s*\)|[\d,]*\d|—)")


def num(tok: str) -> int:
    if tok == "—":
        return 0
    neg = tok.startswith("(")
    v = int(re.sub(r"[^\d]", "", tok))
    return -v if neg else v


def row_values(text: str, pos: int, ncols: int) -> list[tuple[int, int, str]]:
    """Value tokens after a row label ending at `pos`: (start, end, token), '$' dropped. Footnote markers (a bare
    digit 1-9 printed after a value) are dropped only when the row has more tokens than columns."""
    toks = []
    while True:
        m = TOKEN.match(text, pos)
        if not m:
            break
        if m.group(1) != "$":
            toks.append((m.start(1), m.end(1), m.group(1)))
        pos = m.end()
    if len(toks) > ncols:
        toks = [t for t in toks if not re.fullmatch(r"[1-9]", t[2])]
    gate(len(toks) == ncols, f"row at {pos}: {len(toks)} values, expected {ncols}: {[t[2] for t in toks]}")
    return toks


def make_quote(text: str, start: int, end: int) -> str:
    """The verbatim normalised text from the row label to the end of the target value, cut from the left to <= 15
    words (the number itself always survives)."""
    q = text[start:end]
    w = q.split(" ")
    while len(w) > 15:
        w = w[1:]
    return " ".join(w)


def iso(d: str) -> str:
    m = re.fullmatch(r"([A-Z][a-z]+) (\d{1,2}), (\d{4})", d)
    gate(bool(m), f"unparsed date {d!r}")
    return f"{m.group(3)}-{MONTHS.index(m.group(1)) + 1:02d}-{int(m.group(2)):02d}"


def fiscal_start(form: str, rd: str) -> str:
    y = int(rd[:4])
    if form in ("N-CSR", "NSAR-B"):
        return f"{y - 1}-11-01" if form == "N-CSR" else f"{y}-05-01"
    return f"{y - 1}-11-01"  # N-CSRS and NSAR-A: six months ended 30 April


def prior_end(form: str, rd: str) -> str:
    y = int(rd[:4])
    return f"{y - 1}-10-31"  # both an N-CSR year and an N-CSRS half start after the prior 31 October


# ---------------------------------------------------------------- extractors

def base(f: dict, tk: str) -> dict:
    return {"ticker": tk, "form": f["form"], "accession": f["accession"], "url": f["url"], "as_of": f["report_date"],
            "fetched_utc": _log[f["rel"]]["fetched_utc"]}


SOC_ROWS = [  # field, label regex, required
    ("operations_usd", r"Net (?:increase|decrease)(?: \((?:increase|decrease)\))? in net assets resulting from operations", True),
    ("sales_usd", r"Proceeds from shares sold", True),
    ("redemptions_usd", r"Cost of shares redeemed", True),
    ("transaction_fees_usd", r"Transaction fees(?: \(Note \d+\))?", False),
    ("distributions_usd", r"Total distributions", False),
    ("net_assets_begin", r"Beginning of (?:year|period)(?:/(?:year|period))?", True),
    ("net_assets", r"End of (?:year|period)(?:/(?:year|period))?", True),
    ("shares_sold", r"Shares sold", True),
    ("shares_redeemed", r"Shares (?:repurchased|redeemed)", True),
]


def statement_of_changes(text: str, f: dict) -> list[dict]:
    anchor = rf"Statements? of Changes in Net Assets (?:{HTML_NAME['SPXL']}|{HTML_NAME['SPXS']})"
    hits = [m.start() for m in re.finditer(anchor, text)]
    gate(len(hits) >= 1, f"{f['accession']}: no Statement of Changes naming SPXL/SPXS")
    rows = []
    done = set()
    for h in hits:
        head_end = text.find("Operations:", h)
        header = text[h:head_end]
        funds = [re.sub(r"\s+\d$", "", n) for n in re.findall(r"Direxion Daily .+? Shares(?: \d(?= ))?", header)]
        periods = re.findall(r"(Year Ended|Six Months Ended) ([A-Z][a-z]+ \d{1,2}, \d{4})", header)
        gate(len(periods) == 2 * len(funds), f"{f['accession']}@{h}: {len(funds)} funds, {len(periods)} period headers")
        end = text.find("The accompanying notes", h)
        gate(0 < head_end < end, f"{f['accession']}@{h}: statement bounds")
        blk = (h, end)
        # a fund's footnote marker in the header ('... Bull 3X Shares 1') -> that footnote's split text
        marks = [re.search(r"(\d)$", n) for n in re.findall(r"Direxion Daily .+? Shares(?: \d(?= ))?", header)]
        notes = dict(re.findall(r"(\d) (Effective [A-Z][a-z]+ \d{1,2}, \d{4}, the Fund had a [^.]*?split)", text[h:end]))

        def split_note(field: str) -> str:
            mk = marks[idx[0]]
            if field not in ("shares_sold", "shares_redeemed") or mk is None or mk.group(1) not in notes:
                return ""
            return f"; footnote {mk.group(1)}: '{notes[mk.group(1)]}' (share amounts for all periods adjusted)"

        for tk in SIDE:
            idx = [i for i, n in enumerate(funds) if re.fullmatch(HTML_NAME[tk], n)]
            if not idx:
                continue
            gate(len(idx) == 1 and tk not in done, f"{f['accession']}: {tk} named twice in Statements of Changes")
            done.add(tk)
            col = 2 * idx[0]
            kind, d = periods[col]
            gate(iso(d) == f["report_date"], f"{f['accession']}: {tk} current column dated {d}, filing {f['report_date']}")
            gate((kind == "Year Ended") == (f["form"] == "N-CSR"), f"{f['accession']}: {tk} period kind {kind}")
            gate(iso(periods[col + 1][1]) == prior_end(f["form"], f["report_date"]),
                 f"{f['accession']}: {tk} prior column dated {periods[col + 1][1]}")
            ps, pe = fiscal_start(f["form"], f["report_date"]), f["report_date"]
            for field, lab, req in SOC_ROWS:
                ms = [m for m in re.finditer(lab, text[blk[0]:blk[1]])]
                if field == "distributions_usd" and not ms:
                    z = re.search(r"Distributions to shareholders:" + r" —" * len(periods) + r"(?= [A-Z])",
                                  text[blk[0]:blk[1]])
                    if z:
                        a = blk[0] + z.start()
                        rows.append({**base(f, tk), "field": field, "value": 0, "period_start": ps, "period_end": pe,
                                     "locator": f"Statement of Changes in Net Assets; row 'Distributions to shareholders:'"
                                                f" (all dashes); column {col + 1} of {len(periods)} ({tk}, {kind} {d})",
                                     "quote": text[a:blk[0] + z.end()]})
                    continue
                if not ms and not req:
                    continue
                gate(len(ms) == 1, f"{f['accession']}: {tk} row {lab!r} matched {len(ms)} times")
                m = ms[0]
                toks = row_values(text, blk[0] + m.end(), len(periods))
                s, e, tok = toks[col]
                e2 = e + 2 if tok.startswith("(") and text[e:e + 2] == " )" else e
                fld, p0, p1 = field, ps, pe
                if field == "net_assets_begin":  # the net assets AT the prior 31 October, as this statement prints them
                    fld, p0, p1 = "net_assets", prior_end(f["form"], f["report_date"]), prior_end(f["form"], f["report_date"])
                elif field == "net_assets":
                    p0 = p1 = f["report_date"]
                rows.append({**base(f, tk), "field": fld, "value": num(tok), "period_start": p0, "period_end": p1,
                             "as_of": p1 if fld == "net_assets" else f["report_date"],
                             "locator": f"Statement of Changes in Net Assets; row '{text[blk[0] + m.start():blk[0] + m.end()]}';"
                                        f" column {col + 1} of {len(periods)} ({tk}, {kind} {d})" + split_note(field),
                             "quote": make_quote(text, blk[0] + m.start(), e2)})
    gate(done == set(SIDE), f"{f['accession']}: Statements of Changes found for {sorted(done)}")
    return rows


SOAL_ROWS = [("net_assets", r"Net Assets(?= \$)", True),
             ("receivable_shares_sold_usd", r"Receivable for Fund shares sold", False),
             ("payable_shares_redeemed_usd", r"Payable for Fund shares redeemed", False)]


def statement_of_assets(text: str, f: dict) -> list[dict]:
    pat = (r"Statements? of Assets and Liabilities (?:\(Unaudited\) )?([A-Z][a-z]+ \d{1,2}, \d{4})(?: \(Unaudited\))?"
           r" ((?:Direxion Daily .+? Shares )+)Assets:")
    rows, done = [], set()
    for m in re.finditer(pat, text):
        funds = re.findall(r"Direxion Daily .+? Shares", m.group(2))
        present = {tk: [i for i, n in enumerate(funds) if re.fullmatch(HTML_NAME[tk], n)] for tk in SIDE}
        if not any(present.values()):
            continue
        gate(iso(m.group(1)) == f["report_date"], f"{f['accession']}: SoAL dated {m.group(1)}")
        end = text.find("The accompanying notes", m.start())
        blk = text[m.start():end]
        for tk, idx in present.items():
            if not idx:
                continue
            gate(len(idx) == 1 and tk not in done, f"{f['accession']}: {tk} twice in SoAL")
            done.add(tk)
            for field, lab, req in SOAL_ROWS:
                ms = list(re.finditer(lab, blk))
                if not ms and not req:
                    continue
                gate(len(ms) >= 1, f"{f['accession']}: {tk} SoAL row {lab!r} missing")
                r0 = ms[0]  # 'Net Assets $' is printed twice (after liabilities and after 'Consist of'): the first
                toks = row_values(text, m.start() + r0.end(), len(funds))
                s, e, tok = toks[idx[0]]
                e2 = e + 2 if tok.startswith("(") and text[e:e + 2] == " )" else e
                pe = f["report_date"]
                rows.append({**base(f, tk), "field": field, "value": num(tok), "period_start": pe, "period_end": pe,
                             "locator": f"Statement of Assets and Liabilities {m.group(1)}; row '{r0.group(0)}'"
                                        f"{' (first)' if field == 'net_assets' else ''}; column {idx[0] + 1} of {len(funds)} ({tk})",
                             "quote": make_quote(text, m.start() + r0.start(), e2)})
    gate(done == set(SIDE), f"{f['accession']}: SoAL found for {sorted(done)}")
    return rows


def schedule_net_assets(text: str, f: dict) -> list[dict]:
    rows = []
    for tk in SIDE:
        pat = HTML_NAME[tk] + r" Schedule of Investments (?:\(Unaudited\) )?([A-Z][a-z]+ \d{1,2}, \d{4})"
        ms = list(re.finditer(pat, text))
        gate(len(ms) == 1, f"{f['accession']}: {tk} schedule header matched {len(ms)} times")
        m = ms[0]
        gate(iso(m.group(1)) == f["report_date"], f"{f['accession']}: {tk} schedule dated {m.group(1)}")
        nxt = text.find("Schedule of Investments", m.end())
        t = re.search(r"TOTAL NET ASSETS - 100\.0% \$ ([\d,]+)", text[m.end():nxt])
        gate(t is not None, f"{f['accession']}: {tk} has no TOTAL NET ASSETS before the next schedule")
        a = m.end() + t.start()
        rows.append({**base(f, tk), "field": "net_assets", "value": num(t.group(1)), "period_start": f["report_date"],
                     "period_end": f["report_date"],
                     "locator": f"Schedule of Investments, {m.group(0)[:-len(m.group(1))].strip()} {m.group(1)}; "
                                "foot line 'TOTAL NET ASSETS - 100.0%'",
                     "quote": text[a:m.end() + t.end()]})
    return rows


def nsar(raw: bytes, f: dict) -> list[dict]:
    t = raw.decode("utf-8", "replace")
    p = re.findall(r"^000 ([AB])0\w{5} (\d\d)/(\d\d)/(\d{4})\s*$", t, re.M)
    gate(len(p) == 1, f"{f['accession']}: {len(p)} report-period lines")
    ab, mm, dd, yy = p[0]
    gate(f"NSAR-{ab}" == f["form"] and f"{yy}-{mm}-{dd}" == f["report_date"],
         f"{f['accession']}: period line {p[0]} vs {f['form']} {f['report_date']}")
    names = re.findall(r"^007 C02(\d\d)00 (.+?)\s*$", t, re.M)
    items: dict[tuple[str, str], tuple[str, str]] = {}
    # [ \t]+, never \s+: an item filed with an empty value (e.g. '074 S000100') must not swallow the next line
    for line in re.findall(r"^(?:007|028|074) [A-Z]\w{6}[ \t]+\S.*$", t, re.M):
        it, code, val = line.split(None, 2)
        gate((it, code) not in items, f"{f['accession']}: item {it} {code} twice")
        items[(it, code)] = (val.strip(), " ".join(line.split()))
    rows = []
    for tk in SIDE:
        ss = [s for s, n in names if n == NSAR_NAME[tk]]
        gate(len(ss) == 1, f"{f['accession']}: series named {NSAR_NAME[tk]!r} found {len(ss)} times")
        s = ss[0]
        loc0 = f"N-SAR series {s} = item 7C '007 C02{s}00 {NSAR_NAME[tk]}'"
        y, m_end = int(yy), int(mm)
        for k, L in enumerate("ABCDEF"):
            mo = m_end - 5 + k
            yr = y if mo >= 1 else y - 1
            mo = mo if mo >= 1 else mo + 12
            last = {2: 29 if yr % 4 == 0 else 28, 4: 30, 6: 30, 9: 30, 11: 30}.get(mo, 31)
            for col, field, what in (("01", "month_sales_usd", "total NAV of shares sold"),
                                     ("04", "month_redemptions_usd", "total NAV of shares redeemed")):
                key = ("028", f"{L}{col}{s}00")
                gate(key in items, f"{f['accession']}: {tk} missing item 028 {key[1]}")
                val, line = items[key]
                rows.append({**base(f, tk), "field": field, "value": int(val) * 1000,
                             "period_start": f"{yr}-{mo:02d}-01", "period_end": f"{yr}-{mo:02d}-{last:02d}",
                             "locator": f"{loc0}; item 28{L} (month {k + 1} of 6) column {col} = {what}, $000s",
                             "quote": line})
        key = ("074", f"T00{s}00")
        gate(key in items, f"{f['accession']}: {tk} missing item 74T")
        val, line = items[key]
        rows.append({**base(f, tk), "field": "net_assets", "value": int(val) * 1000, "period_start": f["report_date"],
                     "period_end": f["report_date"], "locator": f"{loc0}; item 74T net assets, $000s", "quote": line})
    return rows


def extract(f: dict, raw: bytes) -> list[dict]:
    if f["form"].startswith("NSAR"):
        return nsar(raw, f)
    text = norm(raw)
    if f["form"] in ("N-CSR", "N-CSRS"):
        return statement_of_assets(text, f) + statement_of_changes(text, f)
    return schedule_net_assets(text, f)


def build() -> tuple[list[dict], list[tuple[str, str]], list[dict]]:
    fl, dups = filing_list()
    rows, texts = [], {}
    for f in fl:
        raw = get(f["url"], f["rel"])
        rows += extract(f, raw)
        if f["form"].startswith("NSAR"):
            texts[f["accession"]] = norm(raw)
    _, _, flags = nsar_monthly(rows, texts)
    for r in rows:
        if (r["ticker"], r["accession"], r["field"]) in flags:
            r["locator"] += "; " + flags[(r["ticker"], r["accession"], r["field"])]
    for _a, b in dups:
        get(b["url"], b["rel"])
    _save_log()
    for r in rows:
        gate(len(r["quote"].split(" ")) <= 15, f"quote over 15 words: {r['quote']!r}")
        gate(r["as_of"] < RESERVED_FROM and r["period_end"] < RESERVED_FROM, f"sealed date in {r}")
    rows.sort(key=lambda r: (r["ticker"], r["as_of"], r["form"], r["field"], r["period_start"], r["locator"]))
    return rows, dups, fl


def write(rows: list[dict]) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({c: r[c] for c in COLS})


def read_csv() -> list[dict]:
    with OUT.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["value"] = int(r["value"])
    return rows


# ---------------------------------------------------------------- checks

def quote_value(r: dict) -> int:
    if r["form"].startswith("NSAR"):
        return int(r["quote"].split(" ")[-1]) * 1000
    toks = re.findall(r"\(\s*[\d,]+\s*\)|[\d,]*\d|—", r["quote"])
    gate(bool(toks), f"no number in quote {r['quote']!r}")
    return num(toks[-1])


def g_provenance(rows: list[dict], texts: dict[str, str]) -> int:
    """Every row's quote is found in its cached document (normalised) and its value is the quote's last number."""
    for r in rows:
        gate(r["quote"] in texts[r["accession"]], f"quote not in {r['accession']}: {r['quote']!r}")
        gate(quote_value(r) == r["value"], f"value {r['value']} != quote {r['quote']!r}")
        gate(len(r["quote"].split(" ")) <= 15, f"quote over 15 words: {r['quote']!r}")
        gate(r["as_of"] < RESERVED_FROM, f"sealed as_of {r['as_of']}")
    return len(rows)


def one(rows: list[dict], **kw) -> dict | None:
    m = [r for r in rows if all(r[k] == v for k, v in kw.items())]
    gate(len(m) <= 1, f"{len(m)} rows for {kw}")
    return m[0] if m else None


def statement_periods(rows: list[dict]) -> list[tuple[str, str, str, str]]:
    return sorted({(r["ticker"], r["form"], r["accession"], r["as_of"]) for r in rows
                   if r["form"] in ("N-CSR", "N-CSRS") and r["field"] == "sales_usd"})


def soc(rows, tk, acc, field, as_of=None):
    kw = {"ticker": tk, "accession": acc, "field": field}
    c = [r for r in rows if all(r[k] == v for k, v in kw.items()) and r["locator"].startswith("Statement of Changes")
         and (as_of is None or r["as_of"] == as_of)]
    gate(len(c) <= 1, f"{len(c)} SoC rows {kw}")
    return c[0]["value"] if c else None


def g_identity(rows: list[dict]) -> list[str]:
    out = []
    for tk, form, acc, rd in statement_periods(rows):
        begin = soc(rows, tk, acc, "net_assets", prior_end(form, rd))
        end = soc(rows, tk, acc, "net_assets", rd)
        parts = {k: soc(rows, tk, acc, k) for k in ("operations_usd", "distributions_usd", "sales_usd",
                                                    "redemptions_usd", "transaction_fees_usd")}
        missing = [k for k, v in parts.items() if v is None]
        rhs = begin + sum(v or 0 for v in parts.values())
        out.append(f"  {tk} {form:6s} {rd}: begin {begin:,} + ops {parts['operations_usd']:,} + dist "
                   f"{parts['distributions_usd'] if parts['distributions_usd'] is not None else 'no line'} + sold "
                   f"{parts['sales_usd']:,} + redeemed {parts['redemptions_usd']:,} + fees {parts['transaction_fees_usd']} "
                   f"= {rhs:,}; end {end:,}; diff {end - rhs:+,}" + (f" (no line: {missing}, taken as 0)" if missing else ""))
        gate(end == rhs, out[-1])
    return out


def g_internal(rows: list[dict]) -> list[str]:
    """SoAL net assets == SoC end (same filing); each SoC beginning == the previous statement's end."""
    out = []
    for tk, form, acc, rd in statement_periods(rows):
        a = [r for r in rows if r["ticker"] == tk and r["accession"] == acc and r["field"] == "net_assets"
             and r["locator"].startswith("Statement of Assets")]
        gate(len(a) == 1, f"{tk} {acc}: {len(a)} SoAL net assets rows")
        e = soc(rows, tk, acc, "net_assets", rd)
        gate(a[0]["value"] == e, f"{tk} {rd}: SoAL {a[0]['value']:,} != SoC end {e:,}")
        b = soc(rows, tk, acc, "net_assets", prior_end(form, rd))
        prev = [r for r in rows if r["ticker"] == tk and r["form"] == "N-CSR" and r["accession"] != acc
                and r["as_of"] == prior_end(form, rd)
                and r["field"] == "net_assets" and r["locator"].startswith("Statement of Changes")
                and r["period_end"] == prior_end(form, rd)]
        if prev:
            gate(prev[0]["value"] == b, f"{tk} {rd}: beginning {b:,} != prior N-CSR end {prev[0]['value']:,}")
            lab = re.search(r"row '([^']+)'", prev[0]["locator"]).group(1)
            out.append(f"  {tk} {form:6s} {rd}: SoAL = SoC end = {e:,}; beginning {b:,} = the {prior_end(form, rd)} "
                       f"figure printed by N-CSR {prev[0]['accession']} (row '{lab}')")
        else:
            out.append(f"  {tk} {form:6s} {rd}: SoAL = SoC end = {e:,}; beginning {b:,} (no earlier N-CSR read)")
    return out


def g_nsar_74t(rows: list[dict]) -> list[str]:
    out = []
    for r in rows:
        if r["form"].startswith("NSAR") and r["field"] == "net_assets":
            st = [x for x in rows if x["ticker"] == r["ticker"] and x["as_of"] == r["as_of"] and x["field"] == "net_assets"
                  and x["form"] in ("N-CSR", "N-CSRS") and x["locator"].startswith("Statement of Assets")]
            gate(len(st) == 1, f"{r['ticker']} {r['as_of']}: no N-CSR/N-CSRS net assets for 74T")
            d = r["value"] - st[0]["value"]
            out.append(f"  {r['ticker']} {r['form']} {r['as_of']}: 74T {r['value']:,} vs {st[0]['form']} {st[0]['value']:,}"
                       f"  diff {d:+,}")
            gate(-1000 < d <= 1000, out[-1] + "  (beyond one $000 unit)")
    return out


def nsar_sum(rows, tk, acc, field):
    m = [r for r in rows if r["ticker"] == tk and r["accession"] == acc and r["field"] == field]
    gate(len(m) == 6, f"{tk} {acc}: {len(m)} monthly {field} rows")
    return sum(r["value"] for r in m)


def nsar_monthly(rows: list[dict], texts: dict[str, str]) -> tuple[list[str], list[str], dict]:
    """The six months vs (a) the filing's own item 28G total and (b) the statement's half-year (and, for an NSAR-B,
    the statement's full year). Gated on (a) only: a failure of (b) is a property of the filings; it is printed, and
    returned as a flag per (ticker, accession, field) that build() appends to those rows' locator."""
    out, fails, flags = [], [], {}
    filings = sorted({(r["ticker"], r["form"], r["accession"], r["as_of"]) for r in rows if r["form"].startswith("NSAR")})
    for tk, form, acc, rd in filings:
        s = nsar_sum(rows, tk, acc, "month_sales_usd")
        d = nsar_sum(rows, tk, acc, "month_redemptions_usd")
        ser = re.search(r"series (\d\d)", next(r["locator"] for r in rows if r["accession"] == acc and r["ticker"] == tk))
        tot = {}
        for col in ("01", "02", "03", "04"):
            g = re.search(rf"028 G{col}{ser.group(1)}00 (-?\d+)", texts[acc])
            gate(g is not None, f"{acc}: no 028 G{col}")
            tot[col] = int(g.group(1)) * 1000
        gate(s == tot["01"] and d == tot["04"], f"{tk} {acc}: six months {s:,}/{d:,} != 28G {tot['01']:,}/{tot['04']:,}")
        # the statement's half-year: NSAR-A = the N-CSRS column; NSAR-B = N-CSR year less the N-CSRS column
        y = int(rd[:4])
        if form == "NSAR-A":
            src = [(r["accession"], +1) for r in rows if r["form"] == "N-CSRS" and r["as_of"] == rd and r["ticker"] == tk][:1]
            what = f"N-CSRS six months to {rd}"
        else:
            src = ([(r["accession"], +1) for r in rows if r["form"] == "N-CSR" and r["as_of"] == rd and r["ticker"] == tk][:1]
                   + [(r["accession"], -1) for r in rows if r["form"] == "N-CSRS" and r["as_of"] == f"{y}-04-30"
                      and r["ticker"] == tk][:1])
            what = f"N-CSR year to {rd} less N-CSRS six months to {y}-04-30"
        gate(len(src) == (1 if form == "NSAR-A" else 2), f"{tk} {acc}: statements for the half-year not found")
        sold = sum(k * soc(rows, tk, a, "sales_usd") for a, k in src)
        fees = sum(k * (soc(rows, tk, a, "transaction_fees_usd") or 0) for a, k in src)
        red = sum(k * soc(rows, tk, a, "redemptions_usd") for a, k in src)
        line = (f"  {tk} {form} {rd}: 6-month sales {s:,} vs {what}: proceeds {sold:,} (diff {s - sold:+,}), "
                f"proceeds+fees {sold + fees:,} (diff {s - sold - fees:+,}); redemptions {d:,} vs {-red:,} "
                f"(diff {d + red:+,}); 28 col02/03 totals {tot['02']:,}/{tot['03']:,}")
        ok = abs(s - sold - fees) <= 6000 and abs(d + red) <= 6000
        out.append(line + ("" if ok else "  <-- DISAGREES"))
        if not ok:
            fails.append(line)
        year = None
        if form == "NSAR-B":
            ya = src[0][0]
            year = (soc(rows, tk, ya, "sales_usd") + (soc(rows, tk, ya, "transaction_fees_usd") or 0),
                    -soc(rows, tk, ya, "redemptions_usd"))
            out.append(f"      this NSAR-B's six rows vs the N-CSR FULL year: sales diff {s - year[0]:+,}, "
                       f"redemptions diff {d - year[1]:+,}")
        for field, half_diff, total, k in (("month_sales_usd", s - sold - fees, s, 0),
                                           ("month_redemptions_usd", d + red, d, 1)):
            if abs(half_diff) <= 6000:
                continue
            if year is not None and abs(total - year[k]) <= 6000:
                flags[(tk, acc, field)] = (f"CHECK: these six rows sum to the statements' FISCAL-YEAR figure "
                                           f"({year[k]:,}), not the half-year's; they are not six monthly flows as labelled")
            else:
                flags[(tk, acc, field)] = (f"CHECK: these six rows sum to {half_diff:+,} vs the statements' half-year "
                                           f"({what}, proceeds incl. transaction fees)")
        if form == "NSAR-B":  # the full year: NSAR-A + NSAR-B vs the N-CSR year column
            a_acc = [r["accession"] for r in rows if r["form"] == "NSAR-A" and r["as_of"] == f"{y}-04-30" and r["ticker"] == tk]
            if a_acc:
                s2 = s + nsar_sum(rows, tk, a_acc[0], "month_sales_usd")
                d2 = d + nsar_sum(rows, tk, a_acc[0], "month_redemptions_usd")
                ya = src[0][0]
                ys, yf, yr_ = soc(rows, tk, ya, "sales_usd"), soc(rows, tk, ya, "transaction_fees_usd") or 0, soc(rows, tk, ya, "redemptions_usd")
                out.append(f"      full year FY{y}: NSAR-A+B sales {s2:,} vs N-CSR proceeds+fees {ys + yf:,} (diff {s2 - ys - yf:+,});"
                           f" redemptions {d2:,} vs {-yr_:,} (diff {d2 + yr_:+,})")
    return out, fails, flags


def g_nport(rows: list[dict]) -> list[str]:
    nport = json.loads(NPORT.read_text(encoding="utf-8"))
    out = []
    for tk in SIDE:
        rep = [r for r in nport[tk]["reports"] if r["report_date"] == "2019-10-31"]
        gate(len(rep) == 1, f"{tk}: no N-PORT report dated 2019-10-31")
        c = [r for r in rows if r["ticker"] == tk and r["form"] == "N-CSR" and r["as_of"] == "2019-10-31"
             and r["field"] == "net_assets" and r["locator"].startswith("Statement of Assets")]
        gate(len(c) == 1, f"{tk}: no N-CSR 2019-10-31 net assets")
        rec = one(rows, ticker=tk, accession=c[0]["accession"], field="receivable_shares_sold_usd")
        pay = one(rows, ticker=tk, accession=c[0]["accession"], field="payable_shares_redeemed_usd")
        rv, pv = (rec["value"] if rec else 0), (pay["value"] if pay else 0)
        na = rep[0]["net_assets"]
        d = c[0]["value"] - na
        out.append(f"  {tk} 2019-10-31: N-CSR {c[0]['value']:,} vs N-PORT {na:,.2f} ({rep[0]['doc']}): diff {d:+,.2f}"
                   f" ({d / na:+.3%}). N-CSR receivable for shares sold {rv:,}, payable for shares redeemed {pv:,};"
                   f" N-CSR less (receivable - payable) = {c[0]['value'] - rv + pv:,} -> residual vs N-PORT "
                   f"{c[0]['value'] - rv + pv - na:+,.2f}")
    return out


def completeness(rows: list[dict]) -> list[str]:
    out = []
    pref = ["N-CSR", "N-CSRS", "N-Q", "NPORT-EX", "NSAR-A", "NSAR-B"]
    for tk in SIDE:
        out.append(f"  {tk}")
        for q in QUARTER_ENDS:
            c = [r for r in rows if r["ticker"] == tk and r["field"] == "net_assets" and r["as_of"] == q
                 and r["period_end"] == q]
            if not c:
                out.append(f"    {q}  MISSING")
                continue
            c.sort(key=lambda r: pref.index(r["form"]))
            exact = {r["value"] for r in c if not r["form"].startswith("NSAR")}
            gate(len(exact) == 1, f"{tk} {q}: statements print different net assets {sorted(exact)}")
            out.append(f"    {q}  {c[0]['value']:>15,}  {c[0]['form']:8s} {c[0]['accession']}"
                       f"  ({len(c)} rows: {', '.join(sorted({r['form'] for r in c}))}; every statement figure equal)")
    return out


def texts_for(rows: list[dict], fl: list[dict]) -> dict[str, str]:
    by = {f["accession"]: f for f in fl}
    out = {}
    for acc in sorted({r["accession"] for r in rows}):
        out[acc] = norm((RAW / by[acc]["rel"]).read_bytes())
    return out


def check() -> int:
    rows = read_csv()
    fl, dups = filing_list()
    _save_log()
    texts = texts_for(rows, fl)
    hard_fail = []

    def run(name, fn, *a):
        try:
            res = fn(*a)
            print(f"[PASS] {name}")
            if isinstance(res, list):
                print("\n".join(res))
            else:
                print(f"  {res} rows re-found and re-parsed")
        except GateError as e:
            print(f"[FAIL] {name}: {e}")
            hard_fail.append(name)

    print(f"{len(rows)} rows, {len(fl)} filings, CSV {OUT}")
    run("provenance: every quote re-found in the raw document; value = quote's number", g_provenance, rows, texts)
    for a, b in dups:
        ha = hashlib.sha256((RAW / a["rel"]).read_bytes()).hexdigest()
        hb = hashlib.sha256((RAW / b["rel"]).read_bytes()).hexdigest()
        print(f"[{'PASS' if ha == hb else 'FAIL'}] second accession {b['accession']} of {a['accession']} ({a['form']} "
              f"{a['report_date']}, filed {b['filed']}) is byte-identical: sha256 {ha[:16]} / {hb[:16]}")
        if ha != hb:
            hard_fail.append("duplicate")
    run("statement-of-changes identity (every N-CSR/N-CSRS period, each fund)", g_identity, rows)
    run("SoAL = SoC end within a filing; SoC beginning = prior N-CSR end", g_internal, rows)
    run("N-SAR item 74T vs N-CSR/N-CSRS net assets, same date (within one $000 unit)", g_nsar_74t, rows)
    try:
        lines, fails, _ = nsar_monthly(rows, texts)
        print("[PASS] N-SAR six months = the filing's item 28G total" + ("" if not fails else
              f"; [REPORTED] {len(fails)} half-year(s) DISAGREE with the statements (below)"))
        print("\n".join(lines))
    except GateError as e:
        print(f"[FAIL] N-SAR monthly: {e}")
        hard_fail.append("nsar monthly")
    try:
        print("[REPORTED] N-CSR 2019-10-31 vs N-PORT (data/letf/nport_reports.json)")
        print("\n".join(g_nport(rows)))
    except GateError as e:
        print(f"[FAIL] N-PORT comparison: {e}")
        hard_fail.append("nport")
    run("TABLE: net assets at each fiscal quarter-end (primary source first; all non-N-SAR prints equal)",
        completeness, rows)
    print(f"hard gates failed: {hard_fail or 'none'}")
    return 1 if hard_fail else 0


# ---------------------------------------------------------------- selftest

def selftest() -> int:
    """Each gate passes the clean case (the cached filings and the CSV) and RAISES on a deliberate break."""
    rows = read_csv()
    fl, _ = filing_list()
    texts = texts_for(rows, fl)
    g_provenance(rows, texts)
    g_identity(rows)
    g_internal(rows)
    g_nsar_74t(rows)
    nsar_monthly(rows, texts)
    g_nport(rows)
    completeness(rows)

    def must_raise(label: str, fn, *a) -> None:
        try:
            fn(*a)
        except GateError as e:
            print(f"  raises: {label}\n      -> {str(e)[:160]}")
            return
        raise AssertionError(f"gate did not fire: {label}")

    def tweak(pred, **chg) -> list[dict]:
        out = [dict(r) for r in rows]
        r = next(r for r in out if pred(r))
        r.update(chg)
        return out

    soc_sales = lambda r: r["field"] == "sales_usd"  # noqa: E731
    must_raise("a value that is not the quote's number", g_provenance,
               tweak(soc_sales, value=next(r for r in rows if soc_sales(r))["value"] + 1), texts)
    must_raise("a quote not in the document", g_provenance,
               tweak(soc_sales, quote=next(r for r in rows if soc_sales(r))["quote"].replace("1", "7")), texts)
    must_raise("a row on the seal", g_provenance, tweak(soc_sales, as_of=RESERVED_FROM), texts)
    must_raise("identity broken (operations +1)", g_identity,
               tweak(lambda r: r["field"] == "operations_usd", value=next(r for r in rows if r["field"] == "operations_usd")["value"] + 1))
    def same(x: dict):
        return lambda r: all(r[k] == x[k] for k in ("ticker", "accession", "field", "locator", "period_start"))

    first_soal = next(r for r in rows if r["field"] == "net_assets" and r["locator"].startswith("Statement of Assets"))
    must_raise("SoAL != SoC end", g_internal, tweak(same(first_soal), value=first_soal["value"] + 1))
    b16 =next(r for r in rows if r["field"] == "net_assets" and r["form"] == "N-CSR" and r["as_of"] == "2015-10-31"
               and r["locator"].startswith("Statement of Changes") and r["ticker"] == "SPXL"
               and "Beginning" in r["locator"])
    must_raise("a statement's beginning != the prior N-CSR's end (continuity)", g_internal,
               tweak(same(b16), value=b16["value"] + 1))
    t74 = next(r for r in rows if r["form"].startswith("NSAR") and r["field"] == "net_assets")
    must_raise("74T off by $2,000", g_nsar_74t, tweak(same(t74), value=t74["value"] + 2000))
    mo = next(r for r in rows if r["field"] == "month_sales_usd")
    must_raise("a month that no longer sums to item 28G", nsar_monthly, tweak(same(mo), value=mo["value"] + 1000), texts)
    must_raise("two statements printing different net assets for one quarter-end", completeness,
               tweak(same(b16), value=b16["value"] + 1))
    must_raise("the N-CSR 2019-10-31 net assets row missing", g_nport, [r for r in rows if not (r["form"] == "N-CSR" and r["as_of"] == "2019-10-31")])
    # the extractors on broken documents
    fq = next(f for f in fl if f["form"] == "N-Q")
    tq = norm((RAW / fq["rel"]).read_bytes())
    must_raise("N-Q: schedule dated wrong", schedule_net_assets, tq, {**fq, "report_date": "2016-01-30"})
    must_raise("N-Q: TOTAL NET ASSETS line removed", schedule_net_assets,
               tq.replace("TOTAL NET ASSETS - 100.0%", "TOTAL NET ASSETS -"), fq)
    fs = next(f for f in fl if f["form"] == "NSAR-A")
    rs = (RAW / fs["rel"]).read_bytes()
    must_raise("N-SAR: the fund's series name printed twice", nsar,
               rs.replace(b"007 C020300 ", b"007 C020300 DIREXION DAILY S&P 500 BULL 3X SHARES\n007 C020399 "), fs)
    must_raise("N-SAR: wrong report period", nsar, rs, {**fs, "report_date": "2016-10-31"})
    fc = next(f for f in fl if f["form"] == "N-CSR")
    tc = norm((RAW / fc["rel"]).read_bytes())
    statement_of_changes(tc, fc)
    statement_of_assets(tc, fc)

    def after(anchor: str, old: str, new: str) -> str:
        """Replace the first `old` AFTER the SPXL statement's anchor, so the break lands in the block the gate reads."""
        a = re.search(anchor, tc)
        assert a is not None
        i = tc.index(old, a.start())
        return tc[:i] + new + tc[i + len(old):]

    soc_anchor = r"Statements? of Changes in Net Assets " + HTML_NAME["SPXL"]
    soal_anchor = r"Statements? of Assets and Liabilities [A-Z][a-z]+ \d{1,2}, \d{4} Direxion Daily Mid Cap Bull 3X"
    sold = re.search(r"Proceeds from shares sold [\d,]+", tc[re.search(soc_anchor, tc).start():]).group(0)
    must_raise("N-CSR: a Statement of Changes value dropped (column count)", statement_of_changes,
               after(soc_anchor, sold, "Proceeds from shares sold"), fc)
    must_raise("N-CSR: Statement of Changes dated a different year", statement_of_changes, tc,
               {**fc, "report_date": "2014-10-31"})
    must_raise("N-CSR: a row label matched twice", statement_of_changes,
               after(soc_anchor, "Cost of shares redeemed", "Cost of shares redeemed 1 2 3 4 Cost of shares redeemed"), fc)
    must_raise("N-CSR: SoAL fund named twice", statement_of_assets,
               after(soal_anchor, "Direxion Daily Mid Cap Bull 3X Shares", "Direxion Daily S&P 500 ® Bull 3X Shares"), fc)
    must_raise("N-CSR: an extra value in the SoAL Net Assets row (column count)", statement_of_assets,
               after(soal_anchor, "Net Assets $ ", "Net Assets $ — "), fc)
    print("selftest: every gate passes clean and raises on a break")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.check:
        return check()
    rows, dups, fl = build()
    write(rows)
    by: dict[str, int] = {}
    for r in rows:
        by[r["form"]] = by.get(r["form"], 0) + 1
    print(f"{len(fl)} filings read ({len(dups)} second accession(s) fetched and set aside: "
          f"{[(a['accession'], b['accession']) for a, b in dups]}); "
          f"{len(rows)} rows -> {OUT} ({by})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
