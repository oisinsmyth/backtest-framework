"""Build a loadable 15-minute panel from the as-traded intraday fixture.

`load_panel` refuses a panel whose symbols have different bar counts, and the
committed fixture cleans to lengths between 55,778 and 56,056 -- `clean` drops
bars per symbol for non-finite OHLC, low above high, non-positive volume and
spikes. So the date grid has to be intersected AFTER cleaning, and because
removing a bar can change whether its neighbours are cleaned, the intersection
has to be iterated to a fixed point. Same pattern as `run_book_crypto`, at 57x
the row count.

The source fixture is NOT modified (D24). This writes a derived one.

    uv run python scripts/build_intraday_panel.py                    # the 57 ETFs
    uv run python scripts/build_intraday_panel.py --single-names     # D264's eight

D264 GENERALISED THE PATHS AND NOTHING ELSE. The ETF defaults are unchanged and
`--single-names` merely points the same fixed-point intersection at D264's raw
fixture. Duplicating 130 lines to change two constants is the failure D212
exists to prevent, and the fixed point is the part that took the debugging.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import importlib.util
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


L = _load("d217_ladder", "run_macd_ladder.py")

FIX = REPO / "data" / "fixtures"
SRC = FIX / "etf_intraday_15m_raw.csv.gz"
SRC_EVENTS = FIX / "etf_intraday_15m_raw_events.json"
OUT = FIX / "etf_intraday_15m_panel.csv.gz"
OUT_EVENTS = FIX / "etf_intraday_15m_panel_events.json"

SINGLE = {
    "src": FIX / "single_name_intraday_15m_raw.csv.gz",
    "src_events": FIX / "single_name_intraday_15m_raw_events.json",
    "out": FIX / "single_name_intraday_15m_panel.csv.gz",
    "out_events": FIX / "single_name_intraday_15m_panel_events.json",
}
HOLDOUT = {
    "src": FIX / "holdout_intraday_15m_raw.csv.gz",
    "src_events": FIX / "holdout_intraday_15m_raw_events.json",
    "out": FIX / "holdout_intraday_15m_panel.csv.gz",
    "out_events": FIX / "holdout_intraday_15m_panel_events.json",
}


def main() -> int:
    global SRC, SRC_EVENTS, OUT, OUT_EVENTS
    ap = argparse.ArgumentParser()
    ap.add_argument("--single-names", action="store_true",
                    help="build D264's eight-name panel instead of the 57 ETFs")
    ap.add_argument("--holdout", action="store_true",
                    help="build D278's sixteen-name instrument holdout panel")
    a = ap.parse_args()
    if a.single_names:
        SRC, SRC_EVENTS = SINGLE["src"], SINGLE["src_events"]
        OUT, OUT_EVENTS = SINGLE["out"], SINGLE["out_events"]
    elif a.holdout:
        SRC, SRC_EVENTS = HOLDOUT["src"], HOLDOUT["src_events"]
        OUT, OUT_EVENTS = HOLDOUT["out"], HOLDOUT["out_events"]
    t0 = time.time()
    rows: dict[str, dict[str, list[str]]] = defaultdict(dict)
    with gzip.open(SRC, "rt") as f:
        for r in csv.DictReader(f):
            # NORMALISE THE KEY. The source writes "2018-01-02 09:30:00" while
            # `datetime.isoformat()` emits "2018-01-02T09:30:00"; comparing the two
            # as strings silently matched nothing and emptied the grid on pass 1.
            rows[r["symbol"]][r["timestamp"].replace(" ", "T")] = [
                r["open"], r["high"], r["low"], r["close"], r["volume"]
            ]
    syms = sorted(rows)
    print(f"read {sum(len(v) for v in rows.values()):,} rows, {len(syms)} symbols "
          f"({time.time() - t0:.0f}s)", flush=True)

    grid = sorted(set.intersection(*(set(v) for v in rows.values())))
    print(f"raw timestamp intersection: {len(grid):,}", flush=True)

    def write(stamps):
        with gzip.open(OUT, "wt", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["timestamp", "symbol", "open", "high", "low", "close", "volume"])
            for s in syms:
                r = rows[s]
                for ts in stamps:
                    w.writerow([ts, s, *r[ts]])

    saved = L.FIXTURE
    try:
        L.FIXTURE = OUT
        for it in range(1, 7):
            t1 = time.time()
            write(grid)
            cleaned, _ = L.clean(L.load_fixture_csv(OUT))
            survive = set.intersection(
                *(set(tb.timestamp.isoformat() for tb in cleaned[s]) for s in syms))
            nxt = [g for g in grid if g in survive]
            if not nxt:
                raise SystemExit(
                    "the cleaned intersection is empty -- the timestamp keys do not "
                    "match between the written fixture and the parsed bars")
            print(f"  pass {it}: {len(grid):,} -> {len(nxt):,} "
                  f"({time.time() - t1:.0f}s)", flush=True)
            if len(nxt) == len(grid):
                break
            grid = nxt
        else:  # pragma: no cover - would mean the cleaner is churning
            raise SystemExit("the cleaned grid did not converge")
        write(grid)
    finally:
        L.FIXTURE = saved

    # The events sidecar is WP0's, carried over unchanged -- 1,955 dividends and
    # 12 splits. Rebuilding it here would be restating work D226 already did.
    OUT_EVENTS.write_text(SRC_EVENTS.read_text(encoding="utf-8"), encoding="utf-8")

    sessions = sorted({g[:10] for g in grid})
    print(f"\nwrote {OUT.name}: {len(syms)} x {len(grid):,} bars, "
          f"{len(sessions):,} sessions, {grid[0]} .. {grid[-1]}")
    print(f"bars per session: {len(grid) / len(sessions):.1f}")
    print(f"total {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
