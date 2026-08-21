"""One-time (manual, NETWORK) fetch of the BTC/ETH INTRADAY fixtures (D160/D161).

Same shape as every other fixture in this repo (D70/D88/D108): raw OHLCV + an events
sidecar + a meta sidecar, committed to git so the data is immutable-by-diff. Everything
downstream of this script is offline and deterministic.

## Why only 1h is fetched as a study base

yfinance's intraday retention was probed before anything was built, and it decides the
whole design of the cost-frequency study (D160):

| interval | history yfinance serves |
|---|---|
| 15m, 30m | 60 days |
| **1h** | **730 days** |
| 4h | not served for `period='max'` |
| 6h | not a valid yfinance interval at all |
| 1d | full history |

So the study fetches **1h over the full 730 days** and RESAMPLES upward to 2h/4h/6h/12h
/1d (`research.breakout_intraday.resample`). Resampling is exact for these factors
because they all divide 24 and the 1h bars are stamped on UTC hour boundaries, so every
bucket aligns to 00:00 UTC. The pay-off is that **every frequency covers the identical
730-day span**, which is what makes frequency the only variable in the comparison.

15m and 30m are fetched too, but only over their available 60 days, and only as a
TURNOVER-AND-COST MEASUREMENT (D163). 60 days does not contain one 252-day walk-forward
training window, so no return claim is made from them and none can be — see
`docs/results/breakout_intraday.md`.

## Crypto-specific checks, inherited from D108

- yfinance stamps BTC-USD/ETH-USD intraday bars in **UTC**; `_bars_from_dataframe`
  strips tzinfo, so the fixture carries naive timestamps that mean exactly UTC. Every
  bar's minute-of-hour is checked against the interval, loudly.
- Spot crypto has no dividends and no splits, so the events sidecar is empty by
  construction. A provider that returns either fails the fetch rather than having its
  events silently dropped — an empty sidecar must not be a lie (D48).
- Symbols are NOT inner-joined: each runs as its own single-instrument backtest (the
  N=1 case of D64), so neither symbol is truncated to the other's coverage by D45.

Run: uv run python scripts/fetch_crypto_intraday.py
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from backtest_framework.data.corporate_actions import CorporateActions, save_events_json
from backtest_framework.data.csv_fixture import save_fixture_csv
from backtest_framework.data.yfinance_source import EquityDataSource

SYMBOLS = ("BTC-USD", "ETH-USD")
FIXTURES = Path(__file__).resolve().parent.parent / "data" / "fixtures"

# yfinance's own retention limits, minus one day of slack so an off-by-one in the
# provider's window arithmetic cannot silently truncate the series.
PLAN: tuple[tuple[str, int, int], ...] = (
    # (interval, lookback days, minutes per bar)
    ("1h", 729, 60),
    ("30m", 59, 30),
    ("15m", 59, 15),
)


def fetch_one(interval: str, lookback_days: int, minutes: int) -> int:
    source = EquityDataSource()
    start, end = date.today() - timedelta(days=lookback_days), date.today()
    out = FIXTURES / f"crypto_intraday_{interval}_raw.csv.gz"

    bars_by_symbol, volumes_by_symbol, per_symbol_meta = {}, {}, {}
    for symbol in SYMBOLS:
        bars, volumes, dividends, splits = source.get_raw_history(symbol, start, end, interval)
        if not bars:
            print(f"ERROR: empty response for {symbol} @ {interval}", file=sys.stderr)
            return 1
        if dividends or splits:
            print(
                f"ERROR: {symbol} @ {interval} returned {len(dividends)} dividends / "
                f"{len(splits)} splits — spot crypto should have neither; refusing to write a "
                "fixture whose empty events sidecar would be a lie (D48)",
                file=sys.stderr,
            )
            return 1

        # Bar-boundary check: the resampling contract (D161) is only exact if every 1h
        # bar sits on a UTC hour boundary. Checked, not assumed.
        bad_minutes = sorted({tb.timestamp.minute % minutes for tb in bars} - {0})
        if bad_minutes:
            print(
                f"ERROR: {symbol} @ {interval} has bars off the {minutes}-minute grid "
                f"(residual minutes {bad_minutes}) — the resampling contract assumes UTC-aligned "
                "buckets and would silently mis-bucket them",
                file=sys.stderr,
            )
            return 1
        if any(tb.timestamp.second or tb.timestamp.microsecond for tb in bars):
            print(f"ERROR: {symbol} @ {interval} has sub-minute timestamps", file=sys.stderr)
            return 1

        # Gap census — reported, never patched. A gap is a fact about the provider, and
        # the resampler drops any bucket it makes incomplete (loudly) rather than
        # fabricating a bar to fill it.
        step = timedelta(minutes=minutes)
        gaps = Counter()
        for a, b in zip(bars, bars[1:]):
            delta = b.timestamp - a.timestamp
            if delta != step:
                gaps[int(delta.total_seconds() // 60)] += 1
        span_bars = int((bars[-1].timestamp - bars[0].timestamp) / step) + 1

        bars_by_symbol[symbol] = bars
        volumes_by_symbol[symbol] = volumes
        closes = [tb.bar.close for tb in bars]
        returns = [math.log(b / a) for a, b in zip(closes, closes[1:])]
        sigma = statistics.stdev(returns)
        bars_per_year = 365.0 * 24 * 60 / minutes
        per_symbol_meta[symbol] = {
            "first_bar": bars[0].timestamp.isoformat(),
            "last_bar": bars[-1].timestamp.isoformat(),
            "bar_count": len(bars),
            "bars_if_gapless": span_bars,
            "missing_bars": span_bars - len(bars),
            "gap_histogram_minutes": {str(k): v for k, v in sorted(gaps.items())},
            "per_bar_sigma": sigma,
            "annualised_sigma": sigma * math.sqrt(bars_per_year),
        }
        print(
            f"{symbol} @ {interval}: {len(bars)} bars, {bars[0].timestamp} -> {bars[-1].timestamp}, "
            f"{span_bars - len(bars)} missing vs a gapless grid, per-bar sigma={sigma:.6f} "
            f"(annualised {sigma * math.sqrt(bars_per_year):.1%})"
        )

    save_fixture_csv(out, bars_by_symbol, volumes_by_symbol)
    save_events_json(
        FIXTURES / f"crypto_intraday_{interval}_raw_events.json",
        CorporateActions(
            dividends_by_symbol={s: [] for s in SYMBOLS}, splits_by_symbol={s: [] for s in SYMBOLS}
        ),
    )
    meta = {
        "symbols": list(SYMBOLS),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "interval": interval,
        "minutes_per_bar": minutes,
        "bar_boundary": "UTC, on the interval grid (D160) — timestamps stored naive, meaning UTC",
        "per_symbol": per_symbol_meta,
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "yfinance Ticker.history(auto_adjust=False, actions=True) via EquityDataSource "
        "(D18); spot crypto has no dividends or splits, so the events sidecar is empty by "
        "construction (D108)",
        "retention_note": "yfinance serves 730 days of 1h, 60 days of 15m/30m, and no 4h or 6h "
        "interval at all — so 1h is the study base and 2h/4h/6h/12h/1d are resampled from it "
        "(D160/D161); 15m and 30m are a 60-day turnover measurement only (D163)",
        "alignment_note": "NOT inner-joined across symbols — one single-instrument backtest per "
        "symbol (the N=1 case of D64), so D45 truncation never applies",
    }
    (FIXTURES / f"crypto_intraday_{interval}_raw.meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    print(f"wrote {out.name} ({out.stat().st_size / 1e6:.2f} MB) + events + meta")
    return 0


def main() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for interval, lookback_days, minutes in PLAN:
        status = fetch_one(interval, lookback_days, minutes)
        if status:
            return status
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
