"""One-time (manual, network) fetch of the RAW XLE/XOP fixture + corporate actions (D6, D70, D76).

Unlike the v1 fixture (auto-adjusted prices), this stores raw unadjusted OHLC plus
explicit dividends/splits tables — the input the hardened pipeline (clean -> validate
-> snapshot, Step 7) starts from. Writes:
  data/fixtures/xle_xop_daily_2015_2024_raw.csv        (bars + volumes)
  data/fixtures/xle_xop_daily_2015_2024_raw_events.json (dividends, splits)
  data/fixtures/xle_xop_daily_2015_2024_raw.meta.json   (fetch metadata)

Also prints realized daily sigma (from raw closes, split-adjusted for return
continuity) and mean volume per symbol for the v2 run's SqrtImpact params.

Run: uv run python scripts/fetch_fixture_v2.py
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

SYMBOLS = ("XLE", "XOP")
START, END = date(2015, 1, 1), date(2024, 12, 31)
OUT = Path(__file__).resolve().parent.parent / "data" / "fixtures" / "xle_xop_daily_2015_2024_raw.csv"


def main() -> int:
    source = EquityDataSource()
    bars_by_symbol, volumes_by_symbol = {}, {}
    dividends_by_symbol, splits_by_symbol = {}, {}

    for symbol in SYMBOLS:
        bars, volumes, dividends, splits = source.get_raw_history(symbol, START, END)
        if not bars:
            print(f"ERROR: empty response for {symbol}", file=sys.stderr)
            return 1
        bars_by_symbol[symbol] = bars
        volumes_by_symbol[symbol] = volumes
        dividends_by_symbol[symbol] = dividends
        splits_by_symbol[symbol] = splits

        # sigma directly on the fetched closes: yfinance auto_adjust=False prices are
        # ALREADY split-adjusted (verified on XOP's 2020-03-30 split — see D75), so
        # the series is return-continuous as-is; adjusting again would fabricate a
        # -139% "return" on the split date. ADV from share volume.
        closes = [tb.bar.close for tb in bars]
        returns = [math.log(b / a) for a, b in zip(closes, closes[1:])]
        sigma = statistics.stdev(returns)
        mean_volume = statistics.fmean(volumes)
        print(
            f"{symbol}: {len(bars)} bars, {len(dividends)} dividends, {len(splits)} splits, "
            f"sigma={sigma:.6f}, mean volume={mean_volume:,.0f}"
        )
        for ts, ratio in splits:
            print(f"  split: {ts.date()} ratio={ratio}")

    actions = CorporateActions(dividends_by_symbol=dividends_by_symbol, splits_by_symbol=splits_by_symbol)
    save_fixture_csv(OUT, bars_by_symbol, volumes_by_symbol)
    save_events_json(OUT.parent / (OUT.stem + "_events.json"), actions)
    meta = {
        "symbols": list(SYMBOLS),
        "start": START.isoformat(),
        "end": END.isoformat(),
        "interval": "1d",
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "yfinance Ticker.history(auto_adjust=False, actions=True) - RAW prices; "
        "dividends/splits stored explicitly per D6",
    }
    OUT.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"wrote {OUT.name}, {OUT.stem}_events.json, {OUT.stem}.meta.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
