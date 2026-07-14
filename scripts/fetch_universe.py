"""One-time (manual, network) fetch of the broad ETF universe fixture (Phase G, D88).

~55 liquid US ETFs with pre-2015 inception. Coverage policy (D88): a symbol missing
more than 2% of the range's trading days (measured against the modal bar count) is
EXCLUDED and reported in the meta — inner-join alignment across the universe would
otherwise silently truncate everyone to the youngest symbol's start. USO's and OIH's
2020 reverse splits are deliberately in-universe as stress tests for the D75 split
machinery. SPY doubles as the D37 beta benchmark.

Writes data/fixtures/universe_daily_2015_2024_raw.csv.gz (+ events JSON + meta).

Run: uv run python scripts/fetch_universe.py
"""

from __future__ import annotations

import json
import statistics
import time
from datetime import date, datetime, timezone
from pathlib import Path

from backtest_framework.data.corporate_actions import CorporateActions, save_events_json
from backtest_framework.data.csv_fixture import save_fixture_csv
from backtest_framework.data.yfinance_source import EquityDataSource

SYMBOLS = [
    # broad index
    "SPY", "QQQ", "DIA", "IWM", "MDY",
    # sector SPDRs (pre-2015)
    "XLE", "XLF", "XLK", "XLI", "XLV", "XLP", "XLU", "XLB", "XLY",
    # industry
    "XOP", "XME", "XRT", "XHB", "XBI", "IBB", "SMH", "KBE", "KRE", "OIH", "ITB", "IYT",
    # commodities / miners
    "GLD", "SLV", "GDX", "GDXJ", "USO", "UNG",
    # bonds
    "TLT", "IEF", "SHY", "HYG", "LQD", "AGG", "TIP",
    # international
    "EEM", "EFA", "FXI", "EWJ", "EWZ", "EWY", "EWT", "EWA", "EWC", "EWU", "EWG", "EWH", "EWL", "EWQ",
    # real estate / income
    "IYR", "VNQ", "VIG", "VYM",
]
START, END = date(2015, 1, 1), date(2024, 12, 31)
COVERAGE_TOLERANCE = 0.02
OUT = Path(__file__).resolve().parent.parent / "data" / "fixtures" / "universe_daily_2015_2024_raw.csv.gz"


def main() -> int:
    source = EquityDataSource()
    fetched = {}
    failures: dict[str, str] = {}

    for symbol in SYMBOLS:
        for attempt in (1, 2):
            try:
                bars, volumes, dividends, splits = source.get_raw_history(symbol, START, END)
                fetched[symbol] = (bars, volumes, dividends, splits)
                break
            except Exception as exc:  # noqa: BLE001 - report, don't crash the batch
                if attempt == 2:
                    failures[symbol] = f"{type(exc).__name__}: {exc}"
                else:
                    time.sleep(2.0)
        time.sleep(0.5)  # politeness

    modal_bars = statistics.mode(len(v[0]) for v in fetched.values())
    minimum = int(modal_bars * (1 - COVERAGE_TOLERANCE))
    excluded = {s: f"{len(v[0])} bars < required {minimum} (modal {modal_bars})" for s, v in fetched.items() if len(v[0]) < minimum}
    included = {s: v for s, v in fetched.items() if s not in excluded}

    bars_by_symbol = {s: v[0] for s, v in included.items()}
    volumes_by_symbol = {s: v[1] for s, v in included.items()}
    actions = CorporateActions(
        dividends_by_symbol={s: v[2] for s, v in included.items()},
        splits_by_symbol={s: v[3] for s, v in included.items()},
    )

    save_fixture_csv(OUT, bars_by_symbol, volumes_by_symbol)
    save_events_json(OUT.parent / "universe_daily_2015_2024_raw_events.json", actions)
    meta = {
        "symbols_requested": SYMBOLS,
        "symbols_included": sorted(included),
        "symbols_excluded": excluded,
        "fetch_failures": failures,
        "coverage_policy": f"excluded if bars < {1 - COVERAGE_TOLERANCE:.0%} of modal count ({modal_bars})",
        "start": START.isoformat(),
        "end": END.isoformat(),
        "interval": "1d",
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "yfinance auto_adjust=False, actions=True (provider frame: split-adjusted, "
        "dividend-unadjusted - D75); gzipped fixture (D88)",
    }
    (OUT.parent / "universe_daily_2015_2024_raw.meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    n_splits = sum(len(v[3]) for v in included.values())
    n_divs = sum(len(v[2]) for v in included.values())
    print(f"included: {len(included)} symbols, excluded: {len(excluded)}, failed: {len(failures)}")
    for s, why in {**excluded, **failures}.items():
        print(f"  - {s}: {why}")
    print(f"events: {n_divs} dividends, {n_splits} splits")
    for s, v in included.items():
        for ts, ratio in v[3]:
            print(f"  split: {s} {ts.date()} ratio={ratio}")
    print(f"wrote {OUT.name} ({OUT.stat().st_size/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
