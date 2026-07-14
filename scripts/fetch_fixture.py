"""One-time (manual, network) fetch of the XLE/XOP daily fixture (D70).

Writes data/fixtures/xle_xop_daily_2015_2024.csv + .meta.json, and prints realized
daily sigma and mean daily volume per symbol — those numbers get hardcoded into
scripts/run_first_result.py's SqrtImpact params, with the full-sample-calibration
caveat stated there and in D70.

Run: uv run python scripts/fetch_fixture.py
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import yfinance as yf

from backtest_framework.data.yfinance_source import _bars_from_dataframe
from backtest_framework.data.csv_fixture import save_fixture_csv

SYMBOLS = ("XLE", "XOP")
START, END = date(2015, 1, 1), date(2024, 12, 31)
OUT = Path(__file__).resolve().parent.parent / "data" / "fixtures" / "xle_xop_daily_2015_2024.csv"


def main() -> int:
    bars_by_symbol = {}
    volumes_by_symbol = {}
    for symbol in SYMBOLS:
        df = yf.Ticker(symbol).history(start=START, end=END, interval="1d")
        if df.empty:
            print(f"ERROR: empty response for {symbol}", file=sys.stderr)
            return 1
        bars = _bars_from_dataframe(df)
        bars_by_symbol[symbol] = bars
        volumes_by_symbol[symbol] = [float(v) for v in df["Volume"]]

        closes = [tb.bar.close for tb in bars]
        daily_returns = [math.log(b / a) for a, b in zip(closes, closes[1:])]
        sigma = statistics.stdev(daily_returns)
        mean_volume = statistics.fmean(volumes_by_symbol[symbol])
        print(f"{symbol}: {len(bars)} bars, realized daily sigma={sigma:.6f}, mean volume={mean_volume:,.0f}")

    save_fixture_csv(OUT, bars_by_symbol, volumes_by_symbol)
    meta = {
        "symbols": list(SYMBOLS),
        "start": START.isoformat(),
        "end": END.isoformat(),
        "interval": "1d",
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "yfinance Ticker.history (auto_adjust=True default: prices are dividend/split adjusted "
        "- see D70's caveat; raw prices + dividend flows are Step 7 / D6)",
    }
    OUT.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"wrote {OUT} and {OUT.with_suffix('.meta.json').name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
