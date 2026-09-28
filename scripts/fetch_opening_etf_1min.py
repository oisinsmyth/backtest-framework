"""SPY and QQQ one-minute bars for the opening agent-state model's A6 (index-arbitrage basis), from Alpha Vantage
(OA-A4: the principal, 2026-09-28, "Alpha Vantage 1-min, SPY+QQQ").

    python scripts/fetch_opening_etf_1min.py [--cache DIR]     # resumable; a cached slice is never re-fetched

It uses the same fetcher, key and rate limiter as the ledger's energy ETFs (`fetch_etf_intraday.py`, via
`fetch_ledger_free.py --alphavantage`): `TIME_SERIES_INTRADAY`, interval 1min, one month per request, unadjusted,
extended hours. Slices go to `<cache>/1min/<SYM>/<YYYY-MM>.json.gz`, where `<cache>` defaults to this checkout's
`data/raw/alphavantage` (a gitignored cache; a worktree passes the main checkout's).

Months 2015-10 → 2026-09: a warm-up for ATR20 and the 20-day fair ratio before 2016-01-04, the in-sample to 2025-02,
and the vault months, which are downloaded and never read before the joint vault run (the seal is the loader's,
`reserved_from="2025-03-01"`, OA-A1). Alpha Vantage prints a bar only in a minute with a trade. The key is never
printed.
"""
from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import sys
import time
import urllib.error
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SYMS = ("SPY", "QQQ")
MONTHS = ("2015-10", "2026-09")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", type=Path, default=REPO / "data" / "raw" / "alphavantage")
    a = ap.parse_args(argv)
    spec = importlib.util.spec_from_file_location("fetch_etf_intraday", REPO / "scripts" / "fetch_etf_intraday.py")
    assert spec is not None and spec.loader is not None
    av = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(av)
    setattr(av, "INTERVAL", "1min")  # noqa: B010 -- fetch_slice and slice_path read it at call time
    setattr(av, "CACHE", a.cache)  # noqa: B010
    key = av.api_key()
    limiter = av.RateLimiter(av.MIN_INTERVAL)
    todo = [(s, m) for s in SYMS for m in av.months(*MONTHS) if not av.slice_path(s, m).exists()]
    print(f"{len(todo)} slices to fetch into {a.cache} at {av.REQUESTS_PER_MIN}/min, "
          f"ETA {len(todo) * av.MIN_INTERVAL / 60:.1f} min", flush=True)
    fails = 0
    for i, (sym, month) in enumerate(todo, 1):
        path = av.slice_path(sym, month)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            payload = av.fetch_slice(sym, month, key, limiter)
        except (RuntimeError, urllib.error.URLError, TimeoutError, OSError) as exc:
            fails += 1
            print(f"  [{i}/{len(todo)}] {sym} {month}: FAILED {str(exc)[:120]}", flush=True)
            if fails >= av.MAX_CONSECUTIVE_FAILURES:
                raise SystemExit("stopping: consecutive failures") from exc
            time.sleep(min(60.0 * fails, 300.0))
            continue
        fails = 0
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(payload, fh)
        if i % 25 == 0 or i == len(todo):
            print(f"  [{i}/{len(todo)}] {sym} {month}: {len(av.series_of(payload)):,} bars", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
