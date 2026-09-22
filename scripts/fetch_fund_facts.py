"""D619 — the SEC filings behind `data/fund_facts/SOURCES.md`, fetched through the recorder.

    uv run python scripts/fetch_fund_facts.py --index      # the filing index per issuer
    uv run python scripts/fetch_fund_facts.py --documents  # the latest 10-K of each issuer
    uv run python scripts/fetch_fund_facts.py --grep "cut-off"   # search the RECORDED bytes
    uv run python scripts/fetch_fund_facts.py --validate   # validate data/fund_facts/fund_facts.json

WHY A SEPARATE FETCHER, AND WHAT IT IS FOR
------------------------------------------
Deposit §3.2 (lines 86-92) names four facts to record in `SOURCES.md` for every fund — the
futures/swap split, the creation cut-off and execution lag `lag_c`, whether rebalancing executes
at the settlement price or through TAS, and the index roll schedule — and §P8a (lines 326-329)
says of every fund except UNG: *"to source from each prospectus or index methodology (Q19). Do
not assume."* This script fetches the filings those facts have to come out of. It reads nothing
and decides nothing: the quoting is done by hand against the recorded bytes, which is the same
discipline `data/settlement_flow/SOURCES.md` (D586) states — *"Every quoted sentence below was
read out of the RAW response bytes ... not out of a summary."*

**N-PORT DOES NOT APPLY.** BOIL, KOLD, UCO, SCO, UNG and USO are commodity pools, not '40-Act
funds: ProShares Trust II (CIK 0001415311) and the two USCF partnerships file 424B3, 10-K, 10-Q
and 8-K, and **zero N-PORT**. The free historical holdings route is therefore the Schedule of
Investments inside the quarterly 10-Q and the annual 10-K, at a 40-90 day lag.

THE ATOM INDEX ROUTE IS BLOCKED FROM THIS MACHINE, AND THAT IS RECORDED RATHER THAN WORKED AROUND
--------------------------------------------------------------------------------------------------
`https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=...&type=10-K&output=atom` returns
**HTTP 503 `text/html`** to `urllib.request.urlopen` on every header combination tried on
2026-09-21: the reused SEC user agent alone; that agent plus `Accept-Encoding: gzip, deflate`;
and that agent plus `Accept: application/atom+xml,text/xml,*/*` and an explicit `Host`. Four
attempts each, the retry ladder exhausted. The `data.sec.gov` submissions API —
`https://data.sec.gov/submissions/CIK{cik}.json` — answers HTTP 200 to the SAME headers and
carries the same index (form, filing date, accession, primary document), so that is the route
`--index` records. Nothing is scraped around the block and no other client is reached for.

SEC FAIR ACCESS. `USER_AGENT` and `MAX_RPS` are not restated here: they are read out of
`scripts/d331_edgar_deals.py`'s own source by AST, so this repository keeps ONE descriptive
user agent and one rate floor. That agent carries a project mailbox and **never the principal's
own address** — an email in a request header is personal data leaving the machine, and the one
this repository sends is a project one.
"""

from __future__ import annotations

import argparse
import ast
import gzip
import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
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

JOB = "sec_fund_filings"
ROOT = REPO / "data" / "raw" / "recorder"
FACTS = REPO / "data" / "fund_facts" / "fund_facts.json"

#: issuer key -> (CIK, the funds it files for, a human name)
ISSUERS: dict[str, tuple[str, tuple[str, ...], str]] = {
    "proshares_trust_ii": ("0001415311", ("BOIL", "KOLD", "UCO", "SCO"), "ProShares Trust II"),
    "uso": ("0001327068", ("USO",), "United States Oil Fund, LP"),
    "ung": ("0001376227", ("UNG",), "United States Natural Gas Fund, LP"),
}

#: Recorded for provenance only: this URL 503s from this machine. See the module docstring.
ATOM_BLOCKED = (
    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}"
    "&type={form}&dateb=&owner=include&count=10&output=atom"
)
DOC = "https://www.sec.gov/Archives/edgar/data/{cik_int}/{adsh_nodash}/{doc}"
SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t\r\n ]+")


def _from_d331(*names: str) -> dict[str, object]:
    """`USER_AGENT` and `MAX_RPS` out of `scripts/d331_edgar_deals.py`, by AST.

    Not `import`: that module body imports `pandas` and `requests` and inserts paths, and a
    runner's module body is not something a fetcher should run (the D606 lesson — importing a
    runner by path runs its module body). Source is read as bytes with CRLF normalised before
    parsing (D550), so the pin does not depend on the checkout's newline policy."""
    path = REPO / "scripts" / "d331_edgar_deals.py"
    tree = ast.parse(path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8"), filename=str(path))
    out: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in names:
                    out[t.id] = ast.literal_eval(node.value)
    missing = sorted(set(names) - set(out))
    if missing:
        raise RuntimeError(f"{path} no longer defines {missing} at top level")
    return out


_D331 = _from_d331("USER_AGENT", "MAX_RPS")
USER_AGENT = str(_D331["USER_AGENT"])
MAX_RPS = float(_D331["MAX_RPS"])
#: `d331_edgar_deals.py:74` — the SEC edge 403s a User-Agent with no email-shaped token, and this
#: one is a PROJECT mailbox. Asserted, because the one thing that must never happen here is the
#: principal's own address travelling in a header.
if "@" not in USER_AGENT:
    raise RuntimeError(f"the reused SEC user agent has no contact token: {USER_AGENT!r}")
HEADERS = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"}

#: Politeness floor. `MAX_RPS` is the CEILING d331 uses across six threads; this script makes a
#: handful of requests on one thread, so it sits an order of magnitude under it.
MIN_INTERVAL = max(1.0 / MAX_RPS, 0.5)


def sec_fetch(url: str, limiter: RateLimiter | None = None) -> Callable[[], tuple[bytes, Mapping[str, str]]]:
    """`recorder.fetcher(url)` with the SEC user agent and gzip transparently decoded.

    The DECODED bytes are what is recorded, and that is deliberate: a gzip stream's bytes depend
    on the server's compressor, so two identical documents could hash differently. What this
    records is the document.
    """

    def _fetch() -> tuple[bytes, Mapping[str, str]]:
        delay = BACKOFF_SECONDS
        for attempt in range(ATTEMPTS):
            if limiter is not None:
                limiter.wait()
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=TIMEOUT) as r:
                    body = r.read()
                    heads = {str(k).lower(): str(v) for k, v in dict(r.headers).items()}
                    if heads.get("content-encoding") == "gzip":
                        body = gzip.decompress(body)
                        heads["content-encoding"] = "gzip (decoded before recording)"
                    return bytes(body), heads
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
                if isinstance(exc, urllib.error.HTTPError) and exc.code == 404:
                    raise
                if attempt == ATTEMPTS - 1:
                    raise RuntimeError(
                        f"GET {url} failed after {ATTEMPTS} attempts (urllib.request.urlopen): "
                        f"{type(exc).__name__}: {exc}"
                    ) from exc
                time.sleep(delay)
                delay *= 2
        raise RuntimeError(f"GET {url}: attempts={ATTEMPTS} exhausted")

    return _fetch


def record_url(rec: Recorder, key: str, url: str, ext: str, limiter: RateLimiter) -> Record:
    r = rec.record(JOB, key, sec_fetch(url, limiter), ext=ext, source_url=url)
    print(f"  {key:<34} {r.bytes:>10,} bytes  sha {r.sha256[:12]}  {r.path}", flush=True)
    return r


def latest_filing(rec: Recorder, issuer: str, form: str, limiter: RateLimiter) -> dict[str, str]:
    """The most recent `form` for `issuer`, from the recorded submissions index."""
    cik = ISSUERS[issuer][0]
    r = record_url(rec, f"{issuer}_submissions", SUBMISSIONS.format(cik=cik), "json", limiter)
    raw = json.loads((rec.job_dir(JOB) / r.path).read_text(encoding="utf-8"))
    f = raw["filings"]["recent"]
    for i, fm in enumerate(f["form"]):
        if fm == form:
            return {
                "form": fm,
                "filed": f["filingDate"][i],
                "accession": f["accessionNumber"][i],
                "document": f["primaryDocument"][i],
                "report_date": f.get("reportDate", [""] * len(f["form"]))[i],
                "url": DOC.format(
                    cik_int=int(cik),
                    adsh_nodash=f["accessionNumber"][i].replace("-", ""),
                    doc=f["primaryDocument"][i],
                ),
            }
    raise RuntimeError(f"{issuer}: no {form} in the recent submissions index")


def text_of(path: Path) -> str:
    """Tags stripped, entities left alone, whitespace collapsed. For SEARCHING the recorded
    bytes; every quote that reaches `SOURCES.md` is read back out of this text by a human."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    return _WS_RE.sub(" ", _TAG_RE.sub(" ", raw))


# ------------------------------------------------------------------------- the facts validator
FACT_KEYS = ("value", "source_url", "accession", "section", "quote", "fetched_at", "status")
FACT_STATUSES = ("sourced", "unknown")
#: The four facts of deposit §3.2 lines 89-92, plus the expense ratio the fund model leaves None.
REQUIRED_FACTS = (
    "futures_swap_split",
    "creation_cutoff_and_lag",
    "rebalance_execution",
    "roll_schedule",
    "expense_ratio",
)
QUOTE_WORD_LIMIT = 15


class FundFactsError(RuntimeError):
    """`fund_facts.json` does not satisfy the shape §3.2 asks for. Always raised, never warned."""


def validate_fund_facts(doc: Mapping[str, object]) -> dict[str, int]:
    """Raise unless every fund carries all five facts with all seven keys.

    What it enforces, and why each clause is here rather than in prose:

      * every fund in `funds` carries every name in `REQUIRED_FACTS` — a fact that is hard to
        source must appear with `status: "unknown"`, because an ABSENT fact and an UNSOURCED
        fact look the same in a file and mean opposite things;
      * every fact carries all seven keys of the deposit's provenance shape;
      * `status` is `sourced` or `unknown`, and a `sourced` fact has a non-empty `source_url`,
        `accession` and `quote` — "sourced" with no source is the failure this catches;
      * an `unknown` fact has `value` None: a value with `status: "unknown"` is an inference,
        and §P8a says *"Do not assume."*;
      * `lag_c` is 0, 1 or None (§3.2 line 90: *"the lag parameter `lag_c` ∈ {0, 1}"*), and
        lives only on `creation_cutoff_and_lag`;
      * a quote is at most 15 words — this repository's copyright rule, and a long quote is a
        summary wearing quotation marks.

    Returns the counts the record reports: funds, sourced, unknown.
    """
    if not isinstance(doc, Mapping):
        raise FundFactsError(f"fund_facts must be a mapping, got {type(doc).__name__}")
    funds = doc.get("funds")
    if not isinstance(funds, Mapping) or not funds:
        raise FundFactsError("fund_facts has no non-empty `funds` mapping")
    sourced = unknown = 0
    for fund, entry in funds.items():
        if not isinstance(entry, Mapping):
            raise FundFactsError(f"{fund}: entry is {type(entry).__name__}, want a mapping")
        facts = entry.get("facts")
        if not isinstance(facts, Mapping):
            raise FundFactsError(f"{fund}: no `facts` mapping")
        missing = [k for k in REQUIRED_FACTS if k not in facts]
        if missing:
            raise FundFactsError(f"{fund}: missing fact(s) {missing}; an unsourced fact is recorded as unknown, not omitted")
        for name, fact in facts.items():
            where = f"{fund}.{name}"
            if not isinstance(fact, Mapping):
                raise FundFactsError(f"{where}: fact is {type(fact).__name__}, want a mapping")
            absent = [k for k in FACT_KEYS if k not in fact]
            if absent:
                raise FundFactsError(f"{where}: missing key(s) {absent}")
            status = fact["status"]
            if status not in FACT_STATUSES:
                raise FundFactsError(f"{where}: status {status!r} not in {FACT_STATUSES}")
            if status == "sourced":
                for k in ("source_url", "accession", "quote"):
                    if not str(fact.get(k) or "").strip():
                        raise FundFactsError(f"{where}: status 'sourced' with an empty {k}")
                sourced += 1
            else:
                if fact.get("value") is not None:
                    raise FundFactsError(
                        f"{where}: status 'unknown' carries value {fact['value']!r}. "
                        f"Deposit P8a line 328: 'Do not assume.'"
                    )
                unknown += 1
            quote = str(fact.get("quote") or "")
            if len(quote.split()) > QUOTE_WORD_LIMIT:
                raise FundFactsError(f"{where}: quote is {len(quote.split())} words, limit {QUOTE_WORD_LIMIT}")
            if "lag_c" in fact and name != "creation_cutoff_and_lag":
                raise FundFactsError(f"{where}: lag_c belongs only on creation_cutoff_and_lag")
        lag = facts["creation_cutoff_and_lag"].get("lag_c", "missing")
        if lag not in (0, 1, None):
            raise FundFactsError(f"{fund}: lag_c {lag!r} is not 0, 1 or null (deposit 3.2 line 90)")
    p9 = doc.get("p9")
    if not isinstance(p9, list):
        raise FundFactsError("fund_facts has no `p9` list (deposit 3.1b, Q14)")
    for row in p9:
        if not isinstance(row, Mapping) or row.get("status") != "not_sourced":
            raise FundFactsError(f"p9 row must carry status 'not_sourced': {row!r}")
        for k in ("product", "listing", "issuer_site", "question"):
            if not str(row.get(k) or "").strip():
                raise FundFactsError(f"p9 row is missing {k}: {row!r}")
    return {"funds": len(funds), "sourced": sourced, "unknown": unknown, "p9_not_sourced": len(p9)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--index", action="store_true", help="record the submissions filing index per issuer")
    ap.add_argument("--documents", action="store_true", help="record the latest 10-K per issuer")
    ap.add_argument("--grep", help="search the recorded documents for a phrase")
    ap.add_argument("--context", type=int, default=260)
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--root", default=str(ROOT))
    args = ap.parse_args(argv)

    rec = Recorder(Path(args.root))
    limiter = RateLimiter(MIN_INTERVAL)

    if args.validate:
        counts = validate_fund_facts(json.loads(FACTS.read_text(encoding="utf-8")))
        print(f"  fund_facts.json OK: {counts}")
        return 0

    if args.index:
        for issuer, (cik, _funds, name) in ISSUERS.items():
            print(f"  {name} (CIK {cik}); atom route blocked: {ATOM_BLOCKED.format(cik=cik, form='10-K')}")
            record_url(rec, f"{issuer}_submissions", SUBMISSIONS.format(cik=cik), "json", limiter)

    if args.documents:
        found = {}
        for issuer in ISSUERS:
            meta = latest_filing(rec, issuer, "10-K", limiter)
            print(f"  {issuer}: 10-K filed {meta['filed']} accession {meta['accession']}")
            record_url(rec, f"{issuer}_10k", meta["url"], "htm", limiter)
            found[issuer] = meta
        print(json.dumps(found, indent=1))

    if args.grep:
        pat = re.compile(args.grep, re.I)
        for r in rec.records(JOB):
            if not r.path.endswith(".htm"):
                continue
            text = text_of(rec.job_dir(JOB) / r.path)
            hits = list(pat.finditer(text))
            print(f"\n=== {r.key} ({len(hits)} hits, {len(text):,} chars)")
            for m in hits[:12]:
                a, b = max(0, m.start() - args.context // 2), m.end() + args.context
                print(f"  ...{text[a:b].strip()}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
