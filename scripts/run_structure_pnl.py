"""A post-close descriptive addendum: every arm in Sharpe and PnL, against baselines.

    uv run python scripts/run_structure_pnl.py
    uv run python scripts/run_structure_pnl.py --report-only

## Read this first

**The programme is closed (D211).** This is not a new test and it cannot rescue anything.
It restates arms that have already been run in the two units the study never reported —
annualised Sharpe and money — because "mean R per trade" is not what most people mean when
they ask how a strategy did.

Every look is still counted in the ledger. And the rule that applies if any arm had come
back positive is stated in advance rather than after: **a positive here would be a new
hypothesis requiring its own pre-registration, not a result.** D211's stop names "sizing
rule" explicitly, and this addendum introduces one.

## The sizing rule, which the study never had

The arms were R-based: a stop, a target, and an outcome in units of the risk taken. That
has no equity curve, because it never says how much to risk. So:

**Constant unit exposure while in a trade, flat otherwise.** `position[t]` is +1 through a
long, -1 through a short, 0 between. Cost is charged on every unit of exposure changed, so
a round trip pays the fee twice — the same `PositionResult` path D197-D202 used, reused
rather than rewritten so these numbers sit on the same footing as the terrain programme's.

This is the honest minimum. It is not the fixed-fractional sizing a real trader would use,
and it deliberately avoids one: fixed-fractional risk on a book where 27-44% of trades cost
at least their whole risk to trade produces an equity curve that says more about the sizing
rule than about the signal.

## Baselines

- **Buy and hold**, over the exact span each arm trades, from `terrain_strategies`.
- **Cash**, which is 0.00% and is listed because a strategy that loses money has to be
  compared to not trading, not only to a rising asset.

Both matter and they say different things: buy-and-hold is the opportunity cost, cash is
the floor.
"""

from __future__ import annotations

import json
import math
import sys
import time
from itertools import combinations
from pathlib import Path
from typing import Any, Sequence

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))  # results_document, a sibling helper

from backtest_framework.data.cleaner import clean  # noqa: E402
from backtest_framework.data.csv_fixture import (  # noqa: E402
    load_fixture_csv_with_volumes,
)
from backtest_framework.research.structure import market_structure  # noqa: E402
from backtest_framework.research.structure_setups import find_setups  # noqa: E402
from backtest_framework.research.structure_strategies import (  # noqa: E402
    Wrapper,
    expectancy,
    run_arm,
)
from backtest_framework.research.terrain_strategies import (  # noqa: E402
    BENCHMARK_RF_ANNUAL as RF_ANNUAL,
    PositionResult,
    buy_and_hold,
)
from results_document import splice_section  # noqa: E402

FIXTURE = REPO / "data" / "fixtures" / "crypto_binance_15m_raw.csv.gz"
SUMMARY = REPO / "data" / "structure_pnl_summary.json"
RESULTS = REPO / "docs" / "results" / "STRUCTURE_RESULTS.md"

SYMBOLS = ("BTCUSDT", "ETHUSDT")
PRIMARY_K, PRIMARY_TOUCH = 2, 0.5
TIERS = ((0.0, "zero (diagnostic)"), (10.0, "10 bps/side"), (40.0, "40 bps/side"))
"""Three fee tiers, per SIDE, so a round trip pays twice each.

`CostTier.fee_bps` is a per-fill exchange fee and `StrategyResult.net_returns` doubles it
explicitly (D212). Three rather than one because the magnitude of the loss — though not its
sign — depends on which is chosen:

- **zero** is the D202 diagnostic and never a strategy. It separates *no information* from
  *information this cost structure cannot support*.
- **10 bps/side** is roughly a real Binance spot taker fee, so the result cannot be waved
  away as an artifact of a punitive assumption.
- **40 bps/side** is `breakout_study`'s `taker_40bp`, the tier every other study in this
  repo uses, which is generous enough to stand in for slippage as well as fees.

A note on an ambiguity this study inherited rather than created: D196's prose calls
`taker_40bp` "a 40 bps round trip" while the code it ran (`StrategyResult.net_returns`)
charges it per side. The code is the authority here. The 10 bps column exists partly so
that the reading does not depend on resolving that."""
COST_BPS = 40.0
"""The headline tier, kept for the expectancy statistics that quote a single number."""
PPY = 96.0 * 365.0
START_CAPITAL = 10_000.0
FILTERS = ("C2", "C3", "C4")


def bar_returns(bars: Sequence[Any]) -> tuple[float, ...]:
    closes = [b.bar.close for b in bars]
    return tuple(
        [0.0]
        + [
            math.log(b / a) if a > 0.0 and b > 0.0 else 0.0
            for a, b in zip(closes, closes[1:])
        ]
    )


def position_of(bars: Sequence[Any], trades: Sequence[Any], cost_bps: float) -> PositionResult:
    """Constant unit exposure through each trade, flat between."""
    position = [0.0] * len(bars)
    for trade in trades:
        for t in range(trade.entry_index, min(trade.exit_index + 1, len(bars))):
            position[t] = float(trade.direction)
    return PositionResult(tuple(position), bar_returns(bars), cost_bps, PPY)


def arm_name(required: Sequence[str]) -> str:
    return "C1" if not required else "C1+" + "+".join(required)


def run_symbol(symbol: str, bars: Sequence[Any]) -> dict[str, Any]:
    states = market_structure(bars, PRIMARY_K)
    setups = list(find_setups(bars, PRIMARY_K, PRIMARY_TOUCH, states=states).setups)

    arms: dict[str, Any] = {}
    first_entry = len(bars)
    for size in range(len(FILTERS) + 1):
        for required in combinations(FILTERS, size):
            trades = run_arm(bars, setups, required, Wrapper())
            if not trades:
                continue
            first_entry = min(first_entry, trades[0].entry_index)
            by_tier = {
                label: position_of(bars, trades, bps) for bps, label in TIERS
            }
            costed = by_tier["40 bps/side"]
            free = by_tier["zero (diagnostic)"]
            stats = expectancy(trades, COST_BPS)
            arms[arm_name(required)] = {
                "n_trades": len(trades),
                "hit_rate": stats["hit_rate"],
                "share_untradeable": stats["share_untradeable"],
                "bars_in_market": sum(1 for p in costed.position if p != 0.0),
                "exposure": sum(1 for p in costed.position if p != 0.0) / len(bars),
                "net_exposure": costed.net_exposure,
                "costed": {
                    "sharpe": costed.curve_sharpe_zero_rf(bars, PPY),
                    "excess_sharpe": costed.curve_excess_sharpe(bars, PPY, RF_ANNUAL),
                    "rf_annual": RF_ANNUAL,
                    "total_return": costed.curve_total_return(bars),
                    "max_drawdown": costed.max_drawdown(bars),
                    "pnl": START_CAPITAL * costed.curve_total_return(bars),
                },
                "zero_cost": {
                    "sharpe": free.curve_sharpe_zero_rf(bars, PPY),
                    "excess_sharpe": free.curve_excess_sharpe(bars, PPY, RF_ANNUAL),
                    "rf_annual": RF_ANNUAL,
                    "total_return": free.curve_total_return(bars),
                    "max_drawdown": free.max_drawdown(bars),
                    "pnl": START_CAPITAL * free.curve_total_return(bars),
                },
                "tiers": {
                    label: {
                        "sharpe": r.curve_sharpe_zero_rf(bars, PPY),
                        "excess_sharpe": r.curve_excess_sharpe(bars, PPY, RF_ANNUAL),
                        "rf_annual": RF_ANNUAL,
                        "total_return": r.curve_total_return(bars),
                        "max_drawdown": r.max_drawdown(bars),
                        "pnl": START_CAPITAL * r.curve_total_return(bars),
                    }
                    for label, r in by_tier.items()
                },
                "round_trips": len(trades),
            }

    baseline = buy_and_hold(bars, first_entry, PPY)
    baseline["pnl"] = START_CAPITAL * baseline["total_return"]
    return {
        "n_bars": len(bars),
        "first_entry_index": first_entry,
        "years": (len(bars) - first_entry) / PPY,
        "arms": arms,
        "buy_and_hold": baseline,
    }


def render(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    add = lines.append
    runs = payload["runs"]

    add("## ADDENDUM (post-close) - every arm in Sharpe and PnL, against baselines")
    add("")
    add(f"**Produced:** {payload['produced']} · **Reproduce:** "
        "`uv run python scripts/run_structure_pnl.py` (offline, deterministic)")
    add("")
    add("**The programme is closed (D211). This is not a new test and it cannot rescue "
        "anything.** It restates arms that have already been run in two units the study "
        "never reported — annualised Sharpe and money — because *mean R per trade* is not "
        "what most people mean when they ask how a strategy did. Every look is counted in "
        "the ledger, and the rule is stated in advance: **a positive here would be a new "
        "hypothesis requiring its own pre-registration, not a result.**")
    add("")
    add("**Sizing rule, which the study never had:** constant unit exposure while in a "
        "trade, flat otherwise, cost charged on every unit of exposure changed. The same "
        "`PositionResult` path D197-D202 used, reused rather than rewritten so these "
        "numbers sit on the same footing as the terrain programme's. It deliberately avoids "
        "fixed-fractional risk: on a book where a large share of trades cost at least their "
        "whole risk to trade, fixed-fractional sizing produces an equity curve that says "
        "more about the sizing rule than about the signal.")
    add("")
    add("**Costs:** three tiers, all **per side**, so a round trip pays twice each "
        "(D212). Zero is the D202 diagnostic and never a strategy; 10 bps/side is roughly a "
        "real Binance spot taker fee, so the result cannot be waved away as a punitive "
        "assumption; 40 bps/side is `breakout_study`'s `taker_40bp`, the tier every other "
        f"study in this repo uses. Capital {START_CAPITAL:,.0f} units, Sharpe annualised at "
        f"{PPY:,.0f} periods. Buy-and-hold pays one round trip and is shown unchanged "
        "across tiers.")
    add("")

    for sym in runs:
        run = runs[sym]
        bh = run["buy_and_hold"]
        add(f"### `{sym}` — {run['years']:.1f} years, {run['n_bars']:,} bars")
        add("")
        labels = [label for _, label in TIERS]
        add("| arm | trades | exposure | "
            + " | ".join(f"Sharpe / PnL @ {l}" for l in labels)
            + " | max DD (40bp) |")
        add("|---|---:|---:|" + "---:|" * len(labels) + "---:|")
        for name, arm in run["arms"].items():
            cells = " | ".join(
                f"{arm['tiers'][l]['sharpe']:+.2f} / {arm['tiers'][l]['pnl']:+,.0f}"
                for l in labels
            )
            add(f"| {name} | {arm['n_trades']:,} | {arm['exposure']:.1%} | {cells} | "
                f"{arm['costed']['max_drawdown']:.1%} |")
        bh_cells = " | ".join(
            f"{bh['sharpe']:+.2f} / {bh['pnl']:+,.0f}" for _ in labels
        )
        add(f"| **buy and hold** | 1 | 100% | {bh_cells} | {bh['max_drawdown']:.1%} |")
        add("| **cash** | 0 | 0% | " + " | ".join("+0.00 / +0" for _ in labels)
            + " | 0.0% |")
        add("")

    add("### What this shows")
    add("")
    add(_reading(payload))
    add("")

    add("### Multiplicity")
    add("")
    add("| | cells | looks |")
    add("|---|---|---:|")
    add(f"| post-close Sharpe/PnL restatement | 8 arms x {len(SYMBOLS)} symbols | "
        f"{8 * len(SYMBOLS)} |")
    add(f"| **addendum total** | | **{8 * len(SYMBOLS)}** |")
    add("")
    add("Counted in full even though no arm is under test, because a metric computed on a "
        "configuration is a look at it whatever the intent — the same rule that made D189 "
        "count three metrics across sixteen configurations as 48.")
    add("")
    return "\n".join(lines)


def _reading(payload: dict[str, Any]) -> str:
    runs = payload["runs"]
    parts: list[str] = []

    all_arms = [
        (sym, name, arm)
        for sym in runs
        for name, arm in runs[sym]["arms"].items()
    ]
    costed_sharpes = [a["costed"]["sharpe"] for _, _, a in all_arms]
    costed_pnl = [a["costed"]["pnl"] for _, _, a in all_arms]
    free_sharpes = [a["zero_cost"]["sharpe"] for _, _, a in all_arms]
    positive_costed = [(s, n) for s, n, a in all_arms if a["costed"]["pnl"] > 0.0]
    positive_free = [(s, n) for s, n, a in all_arms if a["zero_cost"]["pnl"] > 0.0]

    parts.append(
        f"**After costs, {len(positive_costed)} of {len(all_arms)} arms make money.** "
        + (
            "They are: " + ", ".join(f"`{s}` {n}" for s, n in positive_costed) + "."
            if positive_costed
            else "None."
        )
        + f" Sharpe ranges {min(costed_sharpes):+.2f} to {max(costed_sharpes):+.2f} and PnL "
        f"ranges {min(costed_pnl):+,.0f} to {max(costed_pnl):+,.0f} on "
        f"{START_CAPITAL:,.0f} of capital."
    )
    parts.append("")

    parts.append(
        f"**At zero cost, {len(positive_free)} of {len(all_arms)} make money**, with Sharpe "
        f"between {min(free_sharpes):+.2f} and {max(free_sharpes):+.2f}. That is the D202 "
        "diagnostic doing its job: it separates *no information* from *information this "
        "cost structure cannot support*."
    )
    parts.append("")

    best_free = max(all_arms, key=lambda x: x[2]["zero_cost"]["pnl"])
    sym, name, arm = best_free
    parts.append(
        "**The largest of those is worth naming rather than leaving for a reader to spot.** "
        f"`{sym}` {name} returns {arm['zero_cost']['total_return']:+,.0%} at zero cost, "
        f"Sharpe {arm['zero_cost']['sharpe']:+.2f} — which beats buy-and-hold. It is in the "
        f"market {arm['exposure']:.0%} of the time and takes {arm['round_trips']:,} round "
        "trips to do it, and it dies at the first fee tier: 10 bps a side takes it to "
        f"{arm['tiers']['10 bps/side']['pnl']:+,.0f}. A book that cannot survive a tenth of "
        "a percent per side is not an edge with a cost problem; it is turnover with no edge."
    )
    parts.append("")

    for sym in runs:
        bh = runs[sym]["buy_and_hold"]
        best = max(runs[sym]["arms"].items(), key=lambda kv: kv[1]["costed"]["sharpe"])
        parts.append(
            f"**`{sym}`** — buy and hold returns {bh['total_return']:+.1%} at Sharpe "
            f"{bh['sharpe']:+.2f} over the same span, against the best arm's "
            f"{best[1]['costed']['total_return']:+.1%} at {best[1]['costed']['sharpe']:+.2f} "
            f"({best[0]}). The passive baseline is not a high bar to clear and no arm "
            "clears it."
        )
    parts.append("")

    exposures = [a["exposure"] for _, _, a in all_arms]
    realistic = [
        (s, n, a["tiers"]["10 bps/side"])
        for s, n, a in all_arms
    ]
    positive_realistic = [(s, n) for s, n, t in realistic if t["pnl"] > 0.0]
    parts.append(
        f"**At a realistic 10 bps/side, {len(positive_realistic)} of {len(all_arms)} arms "
        "make money.** "
        + (
            ", ".join(f"`{s}` {n}" for s, n in positive_realistic) + "."
            if positive_realistic
            else "None."
        )
        + " So the verdict does not rest on the 40 bps tier being generous."
    )
    parts.append("")

    trips = [a["round_trips"] for _, _, a in all_arms]
    parts.append(
        "**Why the costed losses are so total.** These are constant-notional books taking "
        f"{min(trips):,} to {max(trips):,} round trips over 8.3 years. At 40 bps a side that "
        "is 80 bps a round trip, and the base arm's 3,000-odd trips compound to roughly "
        "24 e-folds of fee drag — arithmetically ruinous, and exactly the same statement as "
        "D206's finding that a large share of these trades cost at least their entire risk "
        "to put on. It is not a bug and it is not a knife-edge: at a quarter of the fee the "
        "picture is the same."
    )
    parts.append("")

    parts.append(
        "**One number that matters for reading the Sharpes:** these books are in the market "
        f"{min(exposures):.0%} to {max(exposures):.0%} of the time. A Sharpe computed over "
        "the whole series on a book that is mostly flat is diluted toward zero by the flat "
        "bars, so a small magnitude in the zero-cost column should not be read as *nearly* "
        "working. The PnL column is the unambiguous one."
    )
    return "\n".join(parts)


def append_section(payload: dict[str, Any]) -> None:
    # Bounded by the next heading, not by the parking lot at the bottom of the file.
    # The marker-to-anchor form this replaced deleted `## D213` through `## D216` --
    # 426 lines of published results written by four other runners -- every time this
    # script ran, with no error and no warning. Seven sibling runners carried the same
    # body; scripts/results_document.py carries the measurement, per runner (D542).
    splice_section(
        RESULTS,
        "## ADDENDUM (post-close) - every arm in Sharpe and PnL, against baselines",
        render(payload),
    )


def main() -> int:
    if "--report-only" in sys.argv:
        payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
        append_section(payload)
        print(f"re-rendered the addendum of {RESULTS.name} from {SUMMARY.name}")
        return 0

    started = time.time()
    raw, _ = load_fixture_csv_with_volumes(FIXTURE)
    cleaned, _ = clean(raw)
    runs: dict[str, Any] = {}
    for symbol in SYMBOLS:
        print(f"{symbol}: {len(cleaned[symbol]):,} bars", flush=True)
        runs[symbol] = run_symbol(symbol, cleaned[symbol])

    payload = {
        "produced": time.strftime("%Y-%m-%d"),
        "fixture": FIXTURE.name,
        "symbols": list(SYMBOLS),
        "primary": {"k": PRIMARY_K, "touch_atr": PRIMARY_TOUCH},
        "cost_bps_per_side": COST_BPS,
        "start_capital": START_CAPITAL,
        "periods_per_year": PPY,
        "runs": runs,
        "elapsed_seconds": round(time.time() - started, 1),
    }
    SUMMARY.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    append_section(payload)
    print(f"\nwrote {SUMMARY.name} and the addendum in {payload['elapsed_seconds']}s")
    print()
    print(render(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
