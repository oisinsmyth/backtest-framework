"""One-time (manual, network) fetch of the BTC/ETH daily fixture (D108).

Same shape as the equity fixtures (D70/D88): raw OHLCV + an events sidecar + a meta
sidecar, committed to git so the data is immutable-by-diff. Two crypto-specific
notes:

- **Bar boundary is 00:00 UTC, fixed.** yfinance serves BTC-USD/ETH-USD daily bars
  stamped at 00:00+00:00; `_bars_from_dataframe` strips tzinfo, so the fixture
  carries naive 00:00 timestamps that mean exactly UTC midnight. No alternative
  boundary is offered or tested — that's deliberately out of scope.
- **The events tables are empty by construction.** Spot crypto has no dividends and
  no splits. They're written anyway so the snapshot pipeline (clean -> validate ->
  SnapshotStore) takes its normal path rather than a special case.

BTC and ETH are fetched over the same calendar range but have different inception
(ETH-USD starts 2017-11-09). They are NOT inner-joined here: the breakout study runs
one single-instrument backtest per symbol (the N=1 case of D64), so BTC keeps its
full history instead of being truncated to ETH's start by D45 alignment.

Run: uv run python scripts/fetch_crypto_fixture.py
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from backtest_framework.data.corporate_actions import CorporateActions, save_events_json
from backtest_framework.data.csv_fixture import save_fixture_csv
from backtest_framework.data.yfinance_source import EquityDataSource

SYMBOLS = ("BTC-USD", "ETH-USD")
START, END = date(2015, 1, 1), date(2025, 12, 31)
OUT = Path(__file__).resolve().parent.parent / "data" / "fixtures" / "crypto_daily_2015_2025_raw.csv.gz"


def main() -> int:
    source = EquityDataSource()
    bars_by_symbol, volumes_by_symbol = {}, {}

    for symbol in SYMBOLS:
        bars, volumes, dividends, splits = source.get_raw_history(symbol, START, END)
        if not bars:
            print(f"ERROR: empty response for {symbol}", file=sys.stderr)
            return 1
        if dividends or splits:
            # Loud rather than silently dropped: spot crypto having a corporate
            # action means the provider frame is not what this fixture assumes.
            print(
                f"ERROR: {symbol} returned {len(dividends)} dividends / {len(splits)} splits — "
                "spot crypto should have neither; refusing to write a fixture whose "
                "empty events sidecar would be a lie (D48)",
                file=sys.stderr,
            )
            return 1
        hours = {tb.timestamp.hour for tb in bars}
        if hours != {0}:
            print(f"ERROR: {symbol} bars are not all stamped 00:00 — saw hours {sorted(hours)}", file=sys.stderr)
            return 1

        bars_by_symbol[symbol] = bars
        volumes_by_symbol[symbol] = volumes
        closes = [tb.bar.close for tb in bars]
        returns = [math.log(b / a) for a, b in zip(closes, closes[1:])]
        sigma = statistics.stdev(returns)
        print(
            f"{symbol}: {len(bars)} bars, {bars[0].timestamp.date()} -> {bars[-1].timestamp.date()}, "
            f"daily sigma={sigma:.6f} (annualised {sigma * math.sqrt(365):.1%}), "
            f"mean volume={statistics.fmean(volumes):,.0f}"
        )

    save_fixture_csv(OUT, bars_by_symbol, volumes_by_symbol)
    save_events_json(
        OUT.parent / "crypto_daily_2015_2025_raw_events.json",
        CorporateActions(
            dividends_by_symbol={s: [] for s in SYMBOLS}, splits_by_symbol={s: [] for s in SYMBOLS}
        ),
    )
    meta = {
        "symbols": list(SYMBOLS),
        "start": START.isoformat(),
        "end": END.isoformat(),
        "interval": "1d",
        "bar_boundary": "00:00 UTC, fixed (D108) — timestamps stored naive, meaning UTC midnight",
        "first_bar": {s: bars_by_symbol[s][0].timestamp.isoformat() for s in SYMBOLS},
        "last_bar": {s: bars_by_symbol[s][-1].timestamp.isoformat() for s in SYMBOLS},
        "bar_count": {s: len(bars_by_symbol[s]) for s in SYMBOLS},
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "yfinance Ticker.history(auto_adjust=False, actions=True); spot crypto has no "
        "dividends or splits, so the events sidecar is empty by construction (D108)",
        "alignment_note": "NOT inner-joined across symbols — the study runs one single-instrument "
        "backtest per symbol so BTC keeps its pre-2017 history (D45 would otherwise truncate it "
        "to ETH's inception)",
    }
    (OUT.parent / "crypto_daily_2015_2025_raw.meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    print(f"wrote {OUT.name} ({OUT.stat().st_size / 1e6:.2f} MB) + events + meta")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
