"""D620 — every 10-Q and 10-K since inception for the six funds' registrants, through the recorder.

    uv run python scripts/fetch_fund_filings.py --index       # re-record the submissions index
    uv run python scripts/fetch_fund_filings.py --plan        # what --documents would fetch, no requests
    uv run python scripts/fetch_fund_filings.py --facts       # XBRL companyfacts, ONE call per registrant
    uv run python scripts/fetch_fund_filings.py --documents   # the primary document of every 10-Q/10-K
    uv run python scripts/fetch_fund_filings.py --prices      # BOIL/KOLD/UCO/SCO daily closes (Alpha Vantage)
    uv run python scripts/fetch_fund_filings.py --report      # requests and bytes on disk, no network
    uv run python scripts/fetch_fund_filings.py --selftest    # every guard proved to RAISE

WHY THIS EXISTS. [D619] established that these six funds are commodity pools, file **zero
N-PORT**, and that the only free historical holdings route is the **Schedule of Investments inside
the quarterly 10-Q and the annual 10-K**, at a 40-90 day lag. D619 recorded three documents — the
latest 10-K of each registrant. This fetches the whole history: **231 documents**, 71 for ProShares
Trust II (which files for BOIL, KOLD, UCO and SCO as series of one registrant), 82 for USO and 78
for UNG.

NOTHING HERE IS RE-IMPLEMENTED. `sec_fetch`, `record_url`, `ISSUERS`, `SUBMISSIONS`, `DOC`,
`text_of`, `MIN_INTERVAL` and the SEC user agent are imported from `scripts/fetch_fund_facts.py`,
which in turn reads `USER_AGENT` and `MAX_RPS` out of `scripts/d331_edgar_deals.py` by AST. That
agent carries a project mailbox and **never the principal's own address**. The import is by path
and not by `sys.path` games; `fetch_fund_facts.py`'s module body reads one file and imports the
recorder, and installs nothing (the D606 lesson about running a runner's module body).

THE OPTIMISATION PASS, AND WHAT IT BOUGHT
------------------------------------------
Projected before the run: 231 documents, paced at `MIN_INTERVAL` = 0.5 s (the reused `MAX_RPS`
= 8.0 floor, an order of magnitude under it because this is one thread), is **116 s of pacing**
plus the transfer of roughly half a gigabyte of HTML — call it 6-9 minutes. One pass was made
before fetching and it removed a whole second pass over the same bytes:

  * **`companyfacts` replaces the balance-sheet parse.** `data.sec.gov/api/xbrl/companyfacts/
    CIK{cik}.json` is ONE call per registrant — three calls — and carries every XBRL-tagged
    `shares outstanding` and `net assets` fact the registrant has ever filed, each with its
    period end, its filing date and its accession. That is exactly the anchor series
    `scripts/project_fund_panel.py` needs, so the Schedule-of-Investments parse never has to find
    a balance sheet: it only has to find the derivative table.
  * **The fetch is resumable and idempotent by key.** A document already recorded for its
    accession is not fetched again, so an interrupted run costs nothing and a second run makes
    zero requests. Measured: the second `--documents` run makes 0 requests.

The remaining cost is irreducible — the Schedule of Investments is in the document and nowhere
else, and there are 231 of them.

RATE AND MANNERS. One thread, `MIN_INTERVAL` between request STARTS, `Recorder.record` for every
byte that arrives. GET only. No key, no login, no purchase.
"""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import os
import sys
import urllib.parse
import urllib.request
from collections.abc import Mapping, Sequence
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.recorder import (  # noqa: E402
    ATTEMPTS,
    BACKOFF_SECONDS,
    TIMEOUT,
    RateLimiter,
    Record,
    Recorder,
)


def _load_sibling(name: str, filename: str) -> object:
    """Import a sibling script by path. `fetch_fund_facts.py` reads one file and imports the
    recorder; it installs no hook and starts no client, which is what makes this safe (D606)."""
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    if spec is None or spec.loader is None:  # pragma: no cover - a missing sibling is a broken tree
        raise RuntimeError(f"cannot load scripts/{filename}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


FF = _load_sibling("fetch_fund_facts", "fetch_fund_facts.py")

ISSUERS: dict[str, tuple[str, tuple[str, ...], str]] = FF.ISSUERS  # type: ignore[attr-defined]
SUBMISSIONS: str = FF.SUBMISSIONS  # type: ignore[attr-defined]
DOC: str = FF.DOC  # type: ignore[attr-defined]
MIN_INTERVAL: float = FF.MIN_INTERVAL  # type: ignore[attr-defined]
USER_AGENT: str = FF.USER_AGENT  # type: ignore[attr-defined]
sec_fetch = FF.sec_fetch  # type: ignore[attr-defined]
record_url = FF.record_url  # type: ignore[attr-defined]
text_of = FF.text_of  # type: ignore[attr-defined]

JOB = "sec_fund_filings"
PRICE_JOB = "fund_market_prices"
ROOT = REPO / "data" / "raw" / "recorder"
FILINGS_MD = REPO / "data" / "fund_facts" / "FILINGS.md"

FORMS = ("10-Q", "10-K")
COMPANYFACTS = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

#: The four funds whose daily NAV truth exists (`fund_nav_daily`, D619) and which are NOT in
#: `data/raw/alphavantage/daily_adjusted_etf/` — that cache holds UNG and USO and not these four.
PRICE_TICKERS = ("BOIL", "KOLD", "UCO", "SCO")
AV = "https://www.alphavantage.co/query"
AV_KEY_FILE = Path.home() / ".config" / "alphavantage" / "key"

#: Alpha Vantage's own free-tier floor. `fetch_short_universe.py` uses the same shape.
AV_MIN_INTERVAL = 1.0


class FilingsError(RuntimeError):
    """The index, a document or a price response is not what this fetcher will record."""


def P(*a: object) -> None:
    print(*a, flush=True)


# --------------------------------------------------------------------------------- the index
def _latest_submissions(rec: Recorder, issuer: str) -> Path:
    key = f"{issuer}_submissions"
    got = [r for r in rec.records(JOB, verify=False) if r.key == key]
    if not got:
        raise FilingsError(
            f"no {JOB} record with key {key!r}. Run `--index` first (or `fetch_fund_facts.py "
            f"--index`); this function reads the RECORDED index and never the network."
        )
    return rec.job_dir(JOB) / got[-1].path


def filings_of(raw: Mapping[str, object], issuer: str, forms: Sequence[str] = FORMS) -> list[dict[str, str]]:
    """Every `forms` filing in a recorded submissions index, oldest first.

    **RAISES when the index is paged.** `filings.files` is non-empty exactly when the registrant
    has more filings than one page of `filings.recent` holds, and the older ones then live in
    separate JSON documents. Taking `recent` alone in that case would silently return a TRUNCATED
    history and every count in the record would be wrong by an unknown amount. All three
    registrants here fit in one page today — ProShares Trust II 732 entries back to 2007-10-18,
    USO 641 back to 2005-05-16, UNG 554 back to 2006-10-06 — so the paged branch is not exercised
    by the data and is proved by the selftest instead.
    """
    filings = raw.get("filings")
    if not isinstance(filings, Mapping):
        raise FilingsError(f"{issuer}: submissions document has no `filings` object")
    files = filings.get("files")
    if files:
        names = [str(f.get("name")) for f in files if isinstance(f, Mapping)]
        raise FilingsError(
            f"{issuer}: filings.files is non-empty ({names}). The submissions index is PAGED and "
            f"`filings.recent` is only the newest page, so taking it alone would truncate the "
            f"history silently. Fetch https://data.sec.gov/submissions/<name> for each page and "
            f"merge before using this function."
        )
    recent = filings.get("recent")
    if not isinstance(recent, Mapping):
        raise FilingsError(f"{issuer}: submissions document has no `filings.recent` object")
    need = ("form", "filingDate", "accessionNumber", "primaryDocument", "reportDate")
    missing = [k for k in need if k not in recent]
    if missing:
        raise FilingsError(f"{issuer}: filings.recent is missing {missing}")
    n = len(list(recent["form"]))  # type: ignore[arg-type]
    for k in need:
        if len(list(recent[k])) != n:  # type: ignore[arg-type]
            raise FilingsError(f"{issuer}: filings.recent[{k!r}] has a different length from `form`")
    cik = ISSUERS[issuer][0]
    out: list[dict[str, str]] = []
    for i in range(n):
        form = str(list(recent["form"])[i])  # type: ignore[arg-type]
        if form not in forms:
            continue
        adsh = str(list(recent["accessionNumber"])[i])  # type: ignore[arg-type]
        doc = str(list(recent["primaryDocument"])[i] or "")  # type: ignore[arg-type]
        if not doc:
            raise FilingsError(
                f"{issuer} {adsh} ({form}): no primaryDocument in the index. The document URL "
                f"cannot be built and this filing must not be dropped silently."
            )
        out.append(
            {
                "issuer": issuer,
                "cik": cik,
                "form": form,
                "filed": str(list(recent["filingDate"])[i]),  # type: ignore[arg-type]
                "period_end": str(list(recent["reportDate"])[i] or ""),  # type: ignore[arg-type]
                "accession": adsh,
                "document": doc,
                "url": DOC.format(cik_int=int(cik), adsh_nodash=adsh.replace("-", ""), doc=doc),
            }
        )
    out.sort(key=lambda r: (r["filed"], r["accession"]))
    return out


def plan(rec: Recorder) -> list[dict[str, str]]:
    """Every 10-Q/10-K of every issuer, from the RECORDED index. No requests."""
    rows: list[dict[str, str]] = []
    for issuer in ISSUERS:
        raw = json.loads(_latest_submissions(rec, issuer).read_text(encoding="utf-8"))
        rows.extend(filings_of(raw, issuer))
    return rows


def already(rec: Recorder, job: str) -> dict[str, Record]:
    """key -> the newest record for it. `verify=False`: this is a resume check over hundreds of
    files, and the hashes are verified by `--report` and by every reader."""
    out: dict[str, Record] = {}
    try:
        for r in rec.records(job, verify=False):
            out[r.key] = r
    except FileNotFoundError:
        return {}
    return out


# ------------------------------------------------------------------------------- the prices
def av_key() -> str:
    """Env first, then the file OUTSIDE the repo (`fetch_short_universe.py:407`'s rule). The key
    is never logged, never inlined, and never written into a record's `source_url`."""
    key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if key:
        return key.strip()
    if AV_KEY_FILE.exists():
        return AV_KEY_FILE.read_text(encoding="utf-8").strip()
    raise FilingsError(f"No Alpha Vantage key. Set ALPHAVANTAGE_API_KEY or create {AV_KEY_FILE}.")


def redact(url: str) -> str:
    """The URL with `apikey` replaced by `REDACTED`. **This is what is recorded.**

    `Recorder.record` writes `source_url` into a manifest that is committed, so a URL carrying a
    secret would put the secret in git. The redaction is applied to the string that is RECORDED,
    never to the one that is requested."""
    parts = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
    q = [(k, "REDACTED" if k.lower() == "apikey" else v) for k, v in q]
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(q)))


def av_fetch(url: str, limiter: RateLimiter):  # type: ignore[no-untyped-def]
    """`sec_fetch`'s shape for Alpha Vantage: same retry ladder, same limiter, no SEC agent."""
    import time
    import urllib.error

    def _fetch() -> tuple[bytes, Mapping[str, str]]:
        delay = BACKOFF_SECONDS
        for attempt in range(ATTEMPTS):
            limiter.wait()
            try:
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                    body = r.read()
                    heads = {str(k).lower(): str(v) for k, v in dict(r.headers).items()}
                    return bytes(body), heads
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
                if attempt == ATTEMPTS - 1:
                    raise FilingsError(f"GET {redact(url)} failed after {ATTEMPTS} attempts: {exc}") from exc
                time.sleep(delay)
                delay *= 2
        raise FilingsError(f"GET {redact(url)}: attempts exhausted")

    return _fetch


def check_av_body(body: bytes, ticker: str) -> dict[str, object]:
    """RAISE on Alpha Vantage's two soft failures, which both arrive as HTTP 200.

    `Note` is the rate limit and `Error Message` is a bad symbol; both would otherwise be recorded
    as a successful fetch of a file with no prices in it."""
    doc = json.loads(body.decode("utf-8"))
    for bad in ("Note", "Information", "Error Message"):
        if bad in doc:
            raise FilingsError(f"{ticker}: Alpha Vantage returned {bad!r}: {str(doc[bad])[:160]}")
    series = doc.get("Time Series (Daily)")
    if not isinstance(series, Mapping) or not series:
        raise FilingsError(f"{ticker}: response carries no non-empty 'Time Series (Daily)'")
    return doc


# ---------------------------------------------------------------------------------- FILINGS.md
def filings_markdown(rows: Sequence[Mapping[str, object]], counts: Mapping[str, object]) -> str:
    """`data/fund_facts/FILINGS.md` — the sources list, one line per filing.

    `parsed` is filled by `build_fund_holdings_quarterly.py --index`; this writer takes whatever
    status each row carries and never invents one."""
    head = [
        "# FILINGS — every 10-Q and 10-K of the six funds' registrants (D620)",
        "",
        "Fetched through `Recorder.record` (job `sec_fund_filings`) by",
        "`scripts/fetch_fund_filings.py --documents`; the index comes from",
        "`https://data.sec.gov/submissions/CIK{cik}.json` because the `browse-edgar` atom route",
        "**503s from this machine** (D619). Every row's bytes are on disk under",
        "`data/raw/recorder/sec_fund_filings/` with a sha256 in the job manifest.",
        "",
        "**The four ProShares funds share one registrant**, so one filing covers BOIL, KOLD, UCO",
        "and SCO: the `funds` column names which series the document's Schedule of Investments",
        "is expected to carry, not which it was fetched for.",
        "",
        "| issuer | funds | form | period end | filed | accession | bytes | parsed |",
        "|---|---|---|---|---|---|---:|---|",
    ]
    body = [
        "| {issuer} | {funds} | {form} | {period_end} | {filed} | {accession} | {bytes} | {parsed} |".format(
            issuer=r.get("issuer", ""),
            funds=" ".join(ISSUERS[str(r["issuer"])][1]) if r.get("issuer") in ISSUERS else "",
            form=r.get("form", ""),
            period_end=r.get("period_end", "") or "-",
            filed=r.get("filed", ""),
            accession=r.get("accession", ""),
            bytes=f"{int(str(r.get('bytes') or 0)):,}" if r.get("bytes") else "-",
            parsed=r.get("parsed", "not fetched"),
        )
        for r in rows
    ]
    tail = ["", "## Counts", "", "```json", json.dumps(dict(counts), indent=1), "```", ""]
    return "\n".join(head + body + tail)


def write_filings_md(rows: Sequence[Mapping[str, object]], counts: Mapping[str, object]) -> Path:
    FILINGS_MD.parent.mkdir(parents=True, exist_ok=True)
    FILINGS_MD.write_text(filings_markdown(rows, counts), encoding="utf-8", newline="\n")
    return FILINGS_MD


# ------------------------------------------------------------------------------------ selftest
def selftest() -> int:
    """Every guard shown to accept the good case and then to RAISE on a broken one."""
    good = {
        "filings": {
            "files": [],
            "recent": {
                "form": ["10-Q", "8-K", "10-K"],
                "filingDate": ["2026-08-07", "2026-08-01", "2026-03-01"],
                "accessionNumber": ["0001415311-26-000012", "0001415311-26-000011", "0001415311-26-000003"],
                "primaryDocument": ["q.htm", "k8.htm", "k.htm"],
                "reportDate": ["2026-06-30", "", "2025-12-31"],
            },
        }
    }
    rows = filings_of(good, "proshares_trust_ii")
    P(f"  OK   good index: {len(rows)} filings, forms {[r['form'] for r in rows]}, "
      f"url {rows[-1]['url'][:72]}...")
    P(f"  OK   redact: {redact('https://x.invalid/q?function=F&symbol=BOIL&apikey=SECRET')}")

    breaks: list[tuple[str, object]] = []

    def _paged() -> object:
        bad = json.loads(json.dumps(good))
        bad["filings"]["files"] = [{"name": "CIK0001415311-submissions-001.json"}]
        return filings_of(bad, "proshares_trust_ii")

    def _no_filings() -> object:
        return filings_of({"cik": "1"}, "uso")

    def _no_recent() -> object:
        return filings_of({"filings": {"files": []}}, "uso")

    def _missing_column() -> object:
        bad = json.loads(json.dumps(good))
        del bad["filings"]["recent"]["reportDate"]
        return filings_of(bad, "uso")

    def _ragged() -> object:
        bad = json.loads(json.dumps(good))
        bad["filings"]["recent"]["filingDate"] = ["2026-08-07"]
        return filings_of(bad, "uso")

    def _no_primary_document() -> object:
        bad = json.loads(json.dumps(good))
        bad["filings"]["recent"]["primaryDocument"] = ["", "k8.htm", "k.htm"]
        return filings_of(bad, "uso")

    def _av_rate_limited() -> object:
        return check_av_body(b'{"Note": "Thank you for using Alpha Vantage! Our standard API..."}', "BOIL")

    def _av_bad_symbol() -> object:
        return check_av_body(b'{"Error Message": "Invalid API call."}', "ZZZZ")

    def _av_empty_series() -> object:
        return check_av_body(b'{"Time Series (Daily)": {}}', "BOIL")

    def _no_index_recorded() -> object:
        return _latest_submissions(Recorder(REPO / "temp" / "d620_empty_recorder"), "uso")

    breaks += [
        ("index is paged", _paged),
        ("no filings object", _no_filings),
        ("no filings.recent", _no_recent),
        ("recent missing reportDate", _missing_column),
        ("recent columns ragged", _ragged),
        ("filing with no primaryDocument", _no_primary_document),
        ("AV rate-limit Note", _av_rate_limited),
        ("AV Error Message", _av_bad_symbol),
        ("AV empty series", _av_empty_series),
        ("no submissions index recorded", _no_index_recorded),
    ]

    silent = 0
    for name, fn in breaks:
        try:
            fn()  # type: ignore[operator]
        except FilingsError as exc:
            P(f"  RAISED {name}: {str(exc)[:88]}")
        else:
            silent += 1
            P(f"  DID NOT RAISE {name}  <-- a guard that cannot fire")
    P(f"  selftest: {len(breaks)} breaks, {len(breaks) - silent} fired, {silent} silent")
    return 1 if silent else 0


# ---------------------------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--index", action="store_true", help="re-record the submissions index per issuer")
    ap.add_argument("--plan", action="store_true", help="what --documents would fetch; no requests")
    ap.add_argument("--facts", action="store_true", help="XBRL companyfacts, one call per registrant")
    ap.add_argument("--documents", action="store_true", help="the primary document of every 10-Q/10-K")
    ap.add_argument("--prices", action="store_true", help="BOIL/KOLD/UCO/SCO daily closes")
    ap.add_argument("--report", action="store_true", help="requests and bytes on disk; writes FILINGS.md")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="stop after N documents (0 = all)")
    ap.add_argument("--root", default=str(ROOT))
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    rec = Recorder(Path(args.root))
    limiter = RateLimiter(MIN_INTERVAL)

    if args.index:
        for issuer, (cik, funds, name) in ISSUERS.items():
            P(f"  {name} (CIK {cik}) for {', '.join(funds)}")
            record_url(rec, f"{issuer}_submissions", SUBMISSIONS.format(cik=cik), "json", limiter)

    if args.plan:
        rows = plan(rec)
        have = already(rec, JOB)
        per: dict[str, dict[str, int]] = {}
        for r in rows:
            d = per.setdefault(r["issuer"], {"10-Q": 0, "10-K": 0, "have": 0})
            d[r["form"]] += 1
            d["have"] += int(r["accession"] in have)
        P(json.dumps(per, indent=1))
        todo = [r for r in rows if r["accession"] not in have]
        P(f"  {len(rows)} filings total, {len(rows) - len(todo)} already recorded, {len(todo)} to fetch")
        P(f"  projected pacing {len(todo) * MIN_INTERVAL:,.0f} s at MIN_INTERVAL={MIN_INTERVAL}s, plus transfer")

    if args.facts:
        for issuer, (cik, _funds, name) in ISSUERS.items():
            P(f"  companyfacts {name}")
            record_url(rec, f"{issuer}_companyfacts", COMPANYFACTS.format(cik=cik), "json", limiter)

    if args.documents:
        rows = plan(rec)
        have = already(rec, JOB)
        todo = [r for r in rows if r["accession"] not in have]
        P(f"  {len(rows)} filings, {len(todo)} to fetch (resume by accession), "
          f"projected pacing {len(todo) * MIN_INTERVAL:,.0f} s plus transfer")
        if args.limit:
            todo = todo[: args.limit]
        got = 0
        for i, r in enumerate(todo, 1):
            P(f"  [{i}/{len(todo)}] {r['issuer']} {r['form']} {r['period_end'] or '-'} {r['accession']}")
            record_url(rec, r["accession"], r["url"], "htm", limiter)
            got += 1
        P(f"  {got} documents recorded")

    if args.prices:
        key = av_key()
        P(f"  key {'env ALPHAVANTAGE_API_KEY' if os.environ.get('ALPHAVANTAGE_API_KEY') else AV_KEY_FILE}")
        av_limiter = RateLimiter(AV_MIN_INTERVAL)
        have = already(rec, PRICE_JOB)
        for t in PRICE_TICKERS:
            if t in have:
                P(f"  {t} already recorded ({have[t].path})")
                continue
            url = (
                f"{AV}?function=TIME_SERIES_DAILY_ADJUSTED&symbol={t}"
                f"&outputsize=full&datatype=json&apikey={key}"
            )
            body_seen: dict[str, object] = {}

            def _fetch(u: str = url, ticker: str = t) -> tuple[bytes, Mapping[str, str]]:
                body, heads = av_fetch(u, av_limiter)()
                check_av_body(body, ticker)
                body_seen["n"] = len(json.loads(body.decode("utf-8"))["Time Series (Daily)"])
                return body, heads

            out = rec.record(PRICE_JOB, t, _fetch, ext="json", source_url=redact(url))
            P(f"  {t:<5} {out.bytes:>9,} bytes  {body_seen.get('n')} days  sha {out.sha256[:12]}")

    if args.report:
        rows = plan(rec)
        have = already(rec, JOB)
        # `parsed` comes from the built fixture when there is one: an accession is PARSED when it
        # contributed at least one row that is not `kind="unparsed"`. Written by this script
        # rather than by the builder because FILINGS.md is the sources list, and a sources list
        # that cannot say which sources were used is half a list.
        parsed_accessions: set[str] = set()
        holdings = REPO / "data" / "fixtures" / "fund_holdings_quarterly.csv.gz"
        if holdings.exists():
            import csv

            with gzip.open(holdings, "rt", encoding="utf-8", newline="") as fh:
                for row in csv.DictReader(fh):
                    if row.get("kind") != "unparsed":
                        parsed_accessions.add(str(row.get("source_accession")))
        for r in rows:
            rec_for_row = have.get(r["accession"])
            r["bytes"] = str(rec_for_row.bytes) if rec_for_row else ""
            r["parsed"] = (
                "not fetched" if rec_for_row is None
                else "parsed" if r["accession"] in parsed_accessions
                else "fetched, no holdings parsed" if holdings.exists()
                else "fetched"
            )
        docs = [r for r in rows if r.get("bytes")]
        total = sum(int(r["bytes"]) for r in docs)
        other = {k: v for k, v in have.items() if k not in {r["accession"] for r in rows}}
        counts = {
            "filings_in_index": len(rows),
            "documents_recorded": len(docs),
            "document_bytes": total,
            "document_megabytes": round(total / 1e6, 1),
            "index_and_companyfacts_records": len(other),
            "index_and_companyfacts_bytes": sum(r.bytes for r in other.values()),
            "per_issuer": {
                iss: {
                    "10-Q": sum(1 for r in rows if r["issuer"] == iss and r["form"] == "10-Q"),
                    "10-K": sum(1 for r in rows if r["issuer"] == iss and r["form"] == "10-K"),
                    "recorded": sum(1 for r in rows if r["issuer"] == iss and r.get("bytes")),
                    "first_filed": min((r["filed"] for r in rows if r["issuer"] == iss), default=""),
                    "last_filed": max((r["filed"] for r in rows if r["issuer"] == iss), default=""),
                }
                for iss in ISSUERS
            },
            "requests_made": len(have),
            "accessions_with_parsed_holdings": len(parsed_accessions),
            "accessions_fetched_with_no_holdings_parsed": sum(
                1 for r in rows if r.get("parsed") == "fetched, no holdings parsed"
            ),
            "user_agent": USER_AGENT,
        }
        P(json.dumps(counts, indent=1))
        P(f"  -> {write_filings_md(rows, counts).relative_to(REPO)}")

    if not any((args.index, args.plan, args.facts, args.documents, args.prices, args.report)):
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
