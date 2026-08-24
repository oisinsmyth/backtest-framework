"""Worked trade examples from the fully-stacked arm, selected by a rule fixed in advance.

    uv run python scripts/run_structure_examples.py

Feeds `docs/results/structure_trade_examples.html`. Extraction only — the commentary is
written by hand in the report, and `tests/unit/test_structure_examples.py` pins every
number the report quotes against the JSON this produces, so the two cannot drift
(D176/D183/D186).

## The selection rule, stated before any outcome was looked at

Examples are the easiest thing in a study to cherry-pick, and a report whose examples were
chosen after seeing them is a slideshow. So the rule is mechanical and it is written here
rather than in the report:

From the **fully-stacked arm** — `C1+C2+C3+C4`, the strategy exactly as taught — at the
primary cell (`k=2`, touch band 0.5 ATR), on each symbol, ranked by **net R at 40 bps per
side**:

1. the **best** trade,
2. the **median** trade,
3. the **worst** trade.

Plus, pooled across both symbols, the two trades that bracket the cost mechanism:

4. the **highest cost in R** — the tightest stop, the untradeable archetype,
5. the **lowest cost in R** — the widest stop, the friendliest trade the rule ever produced.

Eight examples, no discretion. The best trade is included deliberately: a report that only
showed losers would be answering a question nobody asked.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Sequence

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.cleaner import clean  # noqa: E402
from backtest_framework.data.csv_fixture import (  # noqa: E402
    load_fixture_csv_with_volumes,
)
from backtest_framework.research.structure import (  # noqa: E402
    CANONICAL_RATIOS,
    RSI_WINDOW,
    fair_value_gaps,
    market_structure,
    ratio_price,
    retracement,
    rsi,
)
from backtest_framework.research.structure_nulls import first_gap_in_leg  # noqa: E402
from backtest_framework.research.structure_setups import (  # noqa: E402
    ATR_WINDOW_15M,
    GOLDEN_RATIO,
    find_setups,
)
from backtest_framework.research.structure_strategies import (  # noqa: E402
    Wrapper,
    _excursions,
    r_multiples,
    run_arm,
)
from backtest_framework.research.terrain import rolling_mean_true_range  # noqa: E402

FIXTURE = REPO / "data" / "fixtures" / "crypto_binance_15m_raw.csv.gz"
SUMMARY = REPO / "data" / "structure_examples_summary.json"

SYMBOLS = ("BTCUSDT", "ETHUSDT")
PRIMARY_K, PRIMARY_TOUCH = 2, 0.5
COST_BPS = 40.0
"""Per side (D212), so a round trip pays 80 bps."""
STACK = ("C2", "C3", "C4")
CONTEXT_BARS = 4
"""Bars of price printed either side of the entry, for the bar table in the report."""

CHART_PAD = 6
"""Bars kept either side of the whole setup, so the chart shows what the structure was
drawn on rather than only the trade. The window runs from the earlier of the change of
character and the impulse leg's start, back `CHART_PAD` bars, through to `CHART_PAD` bars
past the exit."""


def describe(
    bars: Sequence[Any],
    setup: Any,
    trade: Any,
    net_r: float,
    atr: Sequence[float],
    strength: Sequence[float],
    gaps: Sequence[Any],
    symbol: str,
) -> dict[str, Any]:
    """Everything the report needs about one trade, and nothing derived in the report."""
    signal = trade.entry_index - 1
    close = bars[signal].bar.close
    charge = COST_BPS / 10_000.0
    cost_r = charge * (trade.entry_price + trade.exit_price) / trade.risk
    mfe, mae = _excursions(bars, trade)
    midpoint, width = first_gap_in_leg(setup, gaps)
    depth = retracement(setup.leg, close)
    chart_lo = max(0, min(setup.choch_index, setup.leg.start_index) - CHART_PAD)
    chart_hi = min(len(bars) - 1, trade.exit_index + CHART_PAD)

    return {
        "symbol": symbol,
        "direction": trade.direction,
        "side": "long" if trade.direction > 0 else "short",
        "choch": {
            "index": setup.choch_index,
            "timestamp": bars[setup.choch_index].timestamp.isoformat(),
            "level": _choch_level(bars, setup),
        },
        "leg": {
            "start_index": setup.leg.start_index,
            "start_price": setup.leg.start_price,
            "start_timestamp": bars[setup.leg.start_index].timestamp.isoformat(),
            "end_index": setup.leg.end_index,
            "end_price": setup.leg.end_price,
            "end_timestamp": bars[setup.leg.end_index].timestamp.isoformat(),
            "span": setup.leg.span,
            "span_pct": abs(setup.leg.span) / setup.leg.start_price,
        },
        "levels": {
            "fib_618": ratio_price(setup.leg, GOLDEN_RATIO),
            "fib_ladder": {f"{r:.3f}": ratio_price(setup.leg, r) for r in CANONICAL_RATIOS},
            "gap_midpoint": midpoint,
            "gap_width": width,
            "gap_width_atr": (width / atr[signal]) if midpoint is not None else None,
        },
        "entry": {
            "signal_index": signal,
            "index": trade.entry_index,
            "timestamp": bars[trade.entry_index].timestamp.isoformat(),
            "price": trade.entry_price,
            "retracement": depth,
            "rsi": strength[signal],
            "atr": atr[signal],
            "bars_after_choch": signal - setup.choch_index,
        },
        "risk": {
            "stop_price": trade.stop_price,
            "distance": trade.risk,
            "distance_pct": trade.risk / trade.entry_price,
            "distance_atr": trade.risk / atr[signal],
            "target_price": trade.entry_price
            + trade.direction * Wrapper().target_r * trade.risk,
        },
        "exit": {
            "index": trade.exit_index,
            "timestamp": bars[trade.exit_index].timestamp.isoformat(),
            "price": trade.exit_price,
            "reason": trade.reason,
            "bars_held": trade.exit_index - trade.entry_index,
        },
        "outcome": {
            "gross_r": trade.r_multiple,
            "cost_r": cost_r,
            "net_r": net_r,
            "mfe_r": mfe,
            "mae_r": mae,
            "gross_return": trade.gross_return,
        },
        "context_bars": [
            _bar(bars, i)
            for i in range(
                max(0, trade.entry_index - CONTEXT_BARS),
                min(len(bars), trade.entry_index + CONTEXT_BARS + 1),
            )
        ],
        "chart": {
            "first_index": chart_lo,
            "last_index": chart_hi,
            "bars": [_bar(bars, i) for i in range(chart_lo, chart_hi + 1)],
        },
    }


def _bar(bars: Sequence[Any], i: int) -> dict[str, Any]:
    return {
        "index": i,
        "timestamp": bars[i].timestamp.isoformat(),
        "open": bars[i].bar.open,
        "high": bars[i].bar.high,
        "low": bars[i].bar.low,
        "close": bars[i].bar.close,
    }


def _choch_level(bars: Sequence[Any], setup: Any) -> float | None:
    states = market_structure(bars, PRIMARY_K)
    return states[setup.choch_index].choch_level


def main() -> int:
    started = time.time()
    raw, _ = load_fixture_csv_with_volumes(FIXTURE)
    cleaned, _ = clean(raw)

    per_symbol: dict[str, Any] = {}
    pooled: list[dict[str, Any]] = []

    for symbol in SYMBOLS:
        bars = cleaned[symbol]
        print(f"{symbol}: {len(bars):,} bars", flush=True)
        atr = rolling_mean_true_range(bars, ATR_WINDOW_15M)
        strength = rsi(bars, RSI_WINDOW)
        gaps = fair_value_gaps(bars)
        states = market_structure(bars, PRIMARY_K)
        setups = list(find_setups(bars, PRIMARY_K, PRIMARY_TOUCH, states=states).setups)

        trades = run_arm(bars, setups, STACK, Wrapper())
        nets = r_multiples(trades, COST_BPS)
        described = [
            describe(bars, setups[t.setup_index], t, n, atr, strength, gaps, symbol)
            for t, n in zip(trades, nets)
        ]
        pooled.extend(described)

        ranked = sorted(described, key=lambda d: d["outcome"]["net_r"], reverse=True)
        per_symbol[symbol] = {
            "n_trades": len(trades),
            "best": ranked[0],
            "median": ranked[len(ranked) // 2],
            "worst": ranked[-1],
        }

    by_cost = sorted(pooled, key=lambda d: d["outcome"]["cost_r"])
    payload = {
        "produced": time.strftime("%Y-%m-%d"),
        "fixture": FIXTURE.name,
        "arm": "C1+" + "+".join(STACK),
        "primary": {"k": PRIMARY_K, "touch_atr": PRIMARY_TOUCH},
        "cost_bps_per_side": COST_BPS,
        "target_r": Wrapper().target_r,
        "selection_rule": (
            "Fully-stacked arm at the primary cell. Per symbol: best, median and worst by "
            "net R at 40 bps per side. Pooled across symbols: highest and lowest cost in R. "
            "Fixed before any outcome was inspected."
        ),
        "per_symbol": per_symbol,
        "highest_cost": by_cost[-1],
        "lowest_cost": by_cost[0],
        "pooled_n": len(pooled),
        "elapsed_seconds": round(time.time() - started, 1),
    }
    SUMMARY.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nwrote {SUMMARY.name} in {payload['elapsed_seconds']}s "
          f"({payload['pooled_n']} stacked trades across both symbols)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
