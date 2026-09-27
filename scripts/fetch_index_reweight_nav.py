"""D634 §2: the ProShares historical NAV CSVs for Gate R0's published-return check, through the recorder (the
principal, 2026-09-27: "Yes, download them").

    uv run python scripts/fetch_index_reweight_nav.py
    uv run python scripts/fetch_index_reweight_nav.py --dry-run

UGL/GLL track the Bloomberg Gold Subindex and AGQ/ZSL the Bloomberg Silver Subindex, at +2x and -2x daily. UCD/CMD
tracked the Bloomberg Commodity Index itself; they are fetched to see whether their history covers the in-sample
years. Each fund's benchmark and its dates are sourced from its filings before any NAV is compared (D634 §2). The
URL template is `fetch_fund_nav.py`'s (printed on ProShares' UCO page), and each URL returned HTTP 200 to a HEAD
request on 2026-09-27. Same recorder job (`proshares_nav`), same 2-second floor. Rows dated 2025-03-01 or later are
recorded and never read before the joint vault run (IR-A1).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.recorder import RateLimiter, Recorder, fetcher  # noqa: E402

FUNDS = ("UGL", "GLL", "AGQ", "ZSL", "UCD", "CMD")
NAV_URL = "https://accounts.profunds.com/etfdata/ByFund/{ticker}-historical_nav.csv"
JOB = "proshares_nav"
ROOT = REPO / "data" / "raw" / "recorder"
MIN_INTERVAL = 2.0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if a.dry_run:
        for t in FUNDS:
            print(f"  {t:<5} {NAV_URL.format(ticker=t)}", flush=True)
        return 0
    rec, limiter, total = Recorder(ROOT), RateLimiter(MIN_INTERVAL), 0
    for t in FUNDS:
        url = NAV_URL.format(ticker=t)
        r = rec.record(JOB, t, fetcher(url, limiter=limiter), ext="csv", source_url=url, method="fetched")
        total += r.bytes
        print(f"  {t:<5} {r.bytes:>9,} bytes  sha {r.sha256[:12]}  {r.path}", flush=True)
    print(f"  {len(FUNDS)} record(s), {total:,} bytes, under {ROOT / JOB}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
