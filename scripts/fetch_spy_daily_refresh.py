"""SPY daily refresh for the joint vault run's D680 input path (docs/internal/JOINT_RUN_CHECKLIST.md s.2.3). The cached
data/raw/alphavantage/daily/SPY.json.gz ends 2026-08-26, so G0's use list would drop 16 vault sessions; the principal
approved the refresh on 2026-09-30. It is written to a SEPARATE file, never over the cache, for
`joint_d680_vault.py --spy PATH`, which reads its date KEYS only.

    uv run python scripts/fetch_spy_daily_refresh.py [--data-root D]   # one call -> D/raw/alphavantage/daily_refresh/

Same request, key handling and structural success check as fetch_etf_holdout.py (Alpha Vantage returns HTTP 200 on
errors, so no "Time Series (Daily)" key means failure). The file has the cache's shape: {date: {five fields}}. Nothing
here parses a price; the printout is the key count and the first and last date keys.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import fetch_etf_holdout as H  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data", help="the checkout's data/ (a worktree has none)")
    a = ap.parse_args()
    out_dir = a.data_root / "raw" / "alphavantage" / "daily_refresh"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"SPY_{time.strftime('%Y%m%d')}.json.gz"
    if out.exists():
        raise SystemExit(f"{out.name} exists; refusing to overwrite")
    key = H.api_key()
    body = H._get({"function": "TIME_SERIES_DAILY", "symbol": "SPY", "outputsize": "full"}, key, H.RateLimiter(1.0))
    payload = json.loads(body)
    if "Time Series (Daily)" not in payload:
        raise SystemExit(f"Alpha Vantage returned no series: {str(payload)[:160]}")
    series = payload["Time Series (Daily)"]
    with gzip.open(out, "wt", encoding="utf-8") as f:
        json.dump(series, f)
    keys = sorted(series)
    print(f"wrote {out}: {len(keys)} date keys, {keys[0]} -> {keys[-1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
