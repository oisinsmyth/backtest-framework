"""D619 — the ProShares historical NAV series for BOIL, KOLD, UCO and SCO, through the recorder.

    uv run python scripts/fetch_fund_nav.py            # all four, one record each
    uv run python scripts/fetch_fund_nav.py --fund BOIL
    uv run python scripts/fetch_fund_nav.py --dry-run  # print the URLs and stop; no bytes move

WHAT THIS IS, AND WHAT IT IS NOT
--------------------------------
The settlement-flow deposit (`SETTLEMENT_FLOW_LEDGER_PREREG.md` §3.1, line 67) asks for a daily
per-fund panel of

    date, fund, nav, shares_out, aum, futures_notional_by_contract_month, swap_notional,
    source, published_at

**This source carries the first five and none of the last four.** ProShares publishes a free
historical NAV CSV per fund — `Date, ProShares Name, Ticker, NAV, Prior NAV, NAV Change (%),
NAV Change ($), Shares Outstanding (000), Assets Under Management` — with no holdings, no
futures/swap split and no publication timestamp. `scripts/build_fund_panel.py` therefore writes a
panel whose missing columns are **absent rather than null-filled**, and the fixture meta names
them. A column of nulls looks like data that happened to be missing; an absent column says the
source never had it.

Every byte goes through `backtest_framework.data.recorder.Recorder.record` (D608): the response is
kept unmodified under a `fetched_at` name that is never overwritten, a sha256 is stored beside it,
and `fetched_at` is the availability time for any forward test (deposit decision D23).

THE URL PATTERN AND WHERE IT COMES FROM
---------------------------------------
`https://accounts.profunds.com/etfdata/ByFund/{TICKER}-historical_nav.csv`. The UCO form of that
link is printed on the UCO fund page at `https://www.proshares.com/our-etfs/leveraged-and-inverse/uco`
as the fund's "Historical NAV" download; the other three are the same template with the ticker
substituted, and each was confirmed to return HTTP 200 `text/csv` before this script was written.
**UNG and USO 404 on that host** — they are USCF funds, not ProShares — so this script covers four
of the deposit's six and `data/fund_facts/SOURCES.md` says where the other two stand.

NO RESCALING HAPPENS HERE OR ANYWHERE. The earliest rows of each series are on a different scale
(BOIL's last row is `NAV 8000000`, `Shares Outstanding (000) 0`, `AUM 4000400`). The panel builder
EXCLUDES those rows by a declared rule and names the count and dates in the meta; it does not
divide anything by anything. See `build_fund_panel.py`'s `seed_rows`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.recorder import (  # noqa: E402
    RateLimiter,
    Recorder,
    Record,
    fetcher,
)

#: The four ProShares commodity pools of the deposit's §3.1 table (lines 60-63).
PROSHARES_FUNDS = ("BOIL", "KOLD", "UCO", "SCO")

#: The two USCF funds of that table (lines 64-65). NOT fetched here: `uscfinvestments.com` serves
#: its holdings table from a JS endpoint behind `assets/javascript/api_key.php` and publishes no
#: NAV CSV, and `accounts.profunds.com` 404s for both. Recorded in SOURCES.md, not invented here.
USCF_FUNDS = ("UNG", "USO")

NAV_URL = "https://accounts.profunds.com/etfdata/ByFund/{ticker}-historical_nav.csv"
JOB = "proshares_nav"
ROOT = REPO / "data" / "raw" / "recorder"

#: One request start every 2 s, the same floor `scripts/recorder.py` uses. Four files.
MIN_INTERVAL = 2.0


def P(*a: object) -> None:
    """Flush every line: a backgrounded run block-buffers off a tty
    (`run_futures_acquisition.py:105`) and a healthy run then looks hung."""
    print(*a, flush=True)


def nav_url(ticker: str) -> str:
    if ticker not in PROSHARES_FUNDS:
        raise ValueError(
            f"{ticker!r} is not one of the four ProShares funds {PROSHARES_FUNDS}. "
            f"UNG and USO are USCF funds and 404 on this host; no URL is invented for them."
        )
    return NAV_URL.format(ticker=ticker)


def fetch_one(rec: Recorder, ticker: str, limiter: RateLimiter | None = None) -> Record:
    """One fund's historical NAV CSV, recorded raw.

    `published_at` is NOT passed. The CSV states no publication instant — neither a header line
    nor an HTTP `Last-Modified` this code reads — and the recorder records `published_at` only
    when the SOURCE states it. `fetched_at` is the availability time regardless (deposit D23).
    """
    url = nav_url(ticker)
    return rec.record(
        JOB,
        ticker,
        fetcher(url, limiter=limiter),
        ext="csv",
        source_url=url,
        method="fetched",
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fund", action="append", choices=list(PROSHARES_FUNDS), help="default: all four")
    ap.add_argument("--dry-run", action="store_true", help="print the URLs and exit; no bytes move")
    ap.add_argument("--root", default=str(ROOT), help="recorder root (default data/raw/recorder)")
    args = ap.parse_args(argv)

    funds = tuple(args.fund) if args.fund else PROSHARES_FUNDS
    if args.dry_run:
        for t in funds:
            P(f"  {t:<5} {nav_url(t)}")
        P(f"  dry run: {len(funds)} URL(s), nothing fetched")
        return 0

    rec = Recorder(Path(args.root))
    limiter = RateLimiter(MIN_INTERVAL)
    total = 0
    for t in funds:
        r = fetch_one(rec, t, limiter)
        total += r.bytes
        P(f"  {t:<5} {r.bytes:>9,} bytes  sha {r.sha256[:12]}  {r.path}")
    P(f"  {len(funds)} record(s), {total:,} bytes, under {Path(args.root) / JOB}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
