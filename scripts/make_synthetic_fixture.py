"""Generate the bundled synthetic fixture: two co-moving daily price series, AAA and BBB.

    uv run python scripts/make_synthetic_fixture.py

Writes to data/fixtures/:

- synthetic_pair_daily_raw.csv: OHLCV bars in the split-adjusted frame, not adjusted for
  dividends (the frame a typical provider serves with dividends and splits kept separately).
- synthetic_pair_daily_raw_events.json: AAA's quarterly dividends and BBB's 1-for-4 reverse
  split on 2020-03-30.
- synthetic_pair_daily.csv: the same bars back-adjusted for dividends as well.

The prices are simulated, not market data. A common log-price factor drives both series; BBB
adds a mean-reverting spread, so a z-score pairs strategy has something to trade. 2020-03-09
is a market-wide crash day (AAA -20%, BBB -37%), large enough to draw a validator warning.
The output is deterministic: the same seed gives byte-identical files.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.bars import TimestampedBar  # noqa: E402
from backtest_framework.data.corporate_actions import CorporateActions, save_events_json  # noqa: E402
from backtest_framework.data.csv_fixture import save_fixture_csv  # noqa: E402
from backtest_framework.simulator.fills import Bar  # noqa: E402

SEED = 20150102
OUT = REPO / "data" / "fixtures"
START, END = "2015-01-02", "2024-12-31"
CRASH_DAY = pd.Timestamp("2020-03-09")
SPLIT_DAY, SPLIT_RATIO = datetime(2020, 3, 30), 0.25  # 1-for-4 reverse split
CRASH = {"AAA": -0.20, "BBB": -0.37}
START_PRICE = {"AAA": 40.0, "BBB": 50.0}
MEAN_VOLUME = {"AAA": 40e6, "BBB": 5e6}
QUARTERLY_YIELD = 0.008  # AAA's dividend, as a share of the price before the ex-date


def simulate(rng: np.random.Generator, days: pd.DatetimeIndex) -> dict[str, np.ndarray]:
    """Close-to-close log returns, before dividends."""
    n = len(days)
    market = rng.normal(0.0002, 0.012, n)
    spread = np.zeros(n)
    shocks = rng.normal(0.0, 0.006, n)
    for i in range(1, n):  # AR(1) with a half-life of about 20 days
        spread[i] = 0.966 * spread[i - 1] + shocks[i]
    out = {
        "AAA": market + rng.normal(0.0, 0.004, n),
        "BBB": 1.3 * market + np.diff(spread, prepend=0.0) + rng.normal(0.0, 0.004, n),
    }
    crash = int(np.flatnonzero(days == CRASH_DAY)[0])
    for symbol, move in CRASH.items():
        out[symbol][crash] = np.log1p(move)
    return out


def ohlc(rng: np.random.Generator, closes: np.ndarray) -> list[Bar]:
    opens = np.r_[closes[0], closes[:-1]] * np.exp(rng.normal(0.0, 0.003, len(closes)))
    reach = np.abs(rng.normal(0.0, 0.006, (2, len(closes))))
    highs = np.maximum(opens, closes) * (1.0 + reach[0])
    lows = np.minimum(opens, closes) * (1.0 - reach[1])
    return [Bar(open=float(o), high=float(h), low=float(lo), close=float(c)) for o, h, lo, c in zip(opens, highs, lows, closes)]


def main() -> None:
    rng = np.random.default_rng(SEED)
    days = pd.bdate_range(START, END)
    stamps = [d.to_pydatetime() for d in days]
    returns = simulate(rng, days)

    # AAA pays a dividend on the third Friday of each quarter's last month; the raw close
    # drops by the amount on the ex-date.
    ex_dates = [d for d in days if d.month % 3 == 0 and d.weekday() == 4 and 15 <= d.day <= 21]
    raw_close: dict[str, np.ndarray] = {}
    dividends: list[tuple[datetime, float]] = []
    for symbol, r in returns.items():
        closes = START_PRICE[symbol] * np.exp(np.cumsum(r))
        if symbol == "AAA":
            closes = closes.copy()
            for ex in ex_dates:
                i = days.get_loc(ex)
                amount = round(float(closes[i - 1]) * QUARTERLY_YIELD, 4)
                closes[i:] -= amount
                dividends.append((ex.to_pydatetime(), amount))
        raw_close[symbol] = closes

    raw_bars = {s: [TimestampedBar(t, b) for t, b in zip(stamps, ohlc(rng, c))] for s, c in raw_close.items()}
    volumes = {s: [float(round(v)) for v in MEAN_VOLUME[s] * rng.lognormal(0.0, 0.35, len(days))] for s in raw_close}

    # Back-adjust AAA for dividends: every bar before an ex-date is scaled by (1 - d / prior close).
    factor = np.ones(len(days))
    for ex, amount in dividends:
        i = days.get_loc(pd.Timestamp(ex))
        factor[:i] *= 1.0 - amount / float(raw_close["AAA"][i - 1])
    adjusted = {
        "AAA": [TimestampedBar(tb.timestamp, Bar(*(x * f for x in (tb.bar.open, tb.bar.high, tb.bar.low, tb.bar.close))))
                for tb, f in zip(raw_bars["AAA"], factor)],
        "BBB": raw_bars["BBB"],
    }

    save_fixture_csv(OUT / "synthetic_pair_daily_raw.csv", raw_bars, volumes_by_symbol=volumes)
    save_fixture_csv(OUT / "synthetic_pair_daily.csv", adjusted, volumes_by_symbol=volumes)
    save_events_json(
        OUT / "synthetic_pair_daily_raw_events.json",
        CorporateActions(dividends_by_symbol={"AAA": dividends}, splits_by_symbol={"BBB": [(SPLIT_DAY, SPLIT_RATIO)]}),
    )
    print(f"wrote {len(days)} days for AAA and BBB, {len(dividends)} dividends, 1 split, to {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
