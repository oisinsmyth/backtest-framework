"""THE FIRST REAL NUMBER (Step 6, R1's existence-justification gate).

Loads the committed XLE/XOP fixture (offline — no network), runs the z-score pairs
strategy through the real cost stack at 0x/0.5x/1x/2x/4x, logs one trial per
multiplier to the local TrialRegistry, and writes docs/results/first_real_number.md.

Deterministic: same fixture, same config, same output numbers every run.

Run: uv run python scripts/run_first_result.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from backtest_framework.costs.equity_bricks import (
    BorrowFee,
    IBKRCommission,
    ImpactParams,
    MarginInterest,
    SqrtImpact,
)
from backtest_framework.costs.bricks import PercentOfNotionalSpread
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.csv_fixture import load_fixture_csv
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.sweep import render_sweep_table, run_cost_sweep
from backtest_framework.instruments.equity import Equity
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.strategies.zscore_pairs import ZScorePairsStrategy

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "data" / "fixtures" / "xle_xop_daily_2015_2024.csv"
RESULTS = REPO / "docs" / "results" / "first_real_number.md"

STARTING_CASH = 100_000.0

# From scripts/fetch_fixture.py's output on the committed fixture. Full-sample
# calibration - a mild look-ahead in COST parameters (not in the signal); see D70.
IMPACT_PARAMS = {
    "XLE": ImpactParams(sigma_daily=0.018888, adv_shares=41_843_064),
    "XOP": ImpactParams(sigma_daily=0.026665, adv_shares=5_399_803),
}

STRATEGY_PARAMS = dict(lookback=60, entry_z=2.0, exit_z=0.5, leg_weight=1.0)

CONFIG = {
    "strategy": {"type": "zscore_pairs", "pair": ["XLE", "XOP"], **STRATEGY_PARAMS},
    "cost_stack": {
        "trade": [
            {"type": "ibkr_commission_fixed", "per_share": 0.005, "min": 1.00, "cap_pct": 0.01},
            {
                "type": "sqrt_impact",
                "coefficient": 1.0,
                "params": {s: {"sigma_daily": p.sigma_daily, "adv_shares": p.adv_shares} for s, p in IMPACT_PARAMS.items()},
            },
            {"type": "pct_of_notional_spread", "bps": 1.0},
        ],
        "carry_per_leg": [{"type": "borrow_fee", "annual_rate": 0.0025}],
        "carry_portfolio": [{"type": "margin_interest", "annual_rate": 0.06}],
    },
    "starting_cash": STARTING_CASH,
}


def build_cost_stack() -> CostStack:
    return CostStack(
        trade_bricks=(
            IBKRCommission(),
            SqrtImpact(params_by_symbol=IMPACT_PARAMS),
            PercentOfNotionalSpread(bps=1.0),  # half-spread stand-in for liquid ETFs
        ),
        carry_bricks=(BorrowFee(annual_rate=0.0025),),
        portfolio_carry_bricks=(MarginInterest(annual_rate=0.06),),
    )


def make_strategies():
    return [ZScorePairsStrategy(strategy_id="zscore_pairs", instrument_a="XLE", instrument_b="XOP", **STRATEGY_PARAMS)]


def main() -> int:
    bars_by_instrument = load_fixture_csv(FIXTURE)
    instruments = {"XLE": Equity(symbol="XLE"), "XOP": Equity(symbol="XOP")}

    registry = TrialRegistry(REPO / "trial_registry.sqlite")
    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    sweep = run_cost_sweep(
        bars_by_instrument=bars_by_instrument,
        instruments=instruments,
        make_strategies=make_strategies,
        base_cost_stack=build_cost_stack(),
        allocator=ConstantSplitAllocator(),
        starting_cash=STARTING_CASH,
        trial_registry=registry,
        trial_id_prefix=f"first-real-number-{run_stamp}",
        config=CONFIG,
        snapshot_id=FIXTURE.name,
        seed=0,
    )

    n_bars = len(sweep.runs[0].result.equity_curve)
    doc = f"""# The First Real Number — XLE/XOP z-score pairs, full cost sweep

**Date produced:** {datetime.now(timezone.utc).date().isoformat()} · **Snapshot:** `{FIXTURE.name}`
(fetched 2026-07-13, see sidecar `.meta.json`) · **Bars:** {n_bars} aligned daily bars,
2015–2024 · **Starting capital:** ${STARTING_CASH:,.0f} · **Seed:** 0 (no stochastic
components in this run) · Trials logged to the local TrialRegistry as
`first-real-number-{run_stamp}-<multiplier>x`.

This is Phase C's milestone and R1's existence-justification gate
(`DEVELOPMENT_TIMETABLE.md`): the framework's first end-to-end number on real data
through the real cost stack. Per the gate's own words: the number can be ugly; it must
be produced. **It is a milestone of the instrument, not a research claim** — see
caveats.

## Strategy

`ZScorePairsStrategy` (D69): spread = ln(XLE) − ln(XOP), fixed 1:1 log-hedge, rolling
z-score over the previous {STRATEGY_PARAMS['lookback']} bars (never the current one),
enter at |z| > {STRATEGY_PARAMS['entry_z']}, exit at |z| < {STRATEGY_PARAMS['exit_z']},
hold in between, ±{STRATEGY_PARAMS['leg_weight']:.0%} of capital per leg when in a
trade (~200% gross). Hyperparameters chosen a priori, not tuned.

## Cost stack (at 1×)

- Trade: IBKR Fixed commission ($0.005/sh, $1 min, 1% cap — D65) + square-root impact
  (σ/ADV per leg from the fixture — D66) + 1bp half-spread stand-in.
- Carry, per leg: borrow fee 0.25%/yr on short notional (D71).
- Carry, portfolio: margin interest 6%/yr on max(gross − NAV, 0) (D67).

## The sweep (D8)

{render_sweep_table(sweep)}

## Caveats — what this number is NOT (R3: labeled, not hidden)

1. **Famous-pair selection bias (D22):** XLE/XOP was chosen *because* it's the
   canonical pairs example. That is meta-level in-sample selection. Honest pair
   selection inside walk-forward training windows is Step 12.
2. **No fitted parameters, so no train/test split** — the "walk-forward" here is
   bar-by-bar forward simulation with trailing-only data (structurally enforced by
   DataView). Nothing was optimized; nothing needed holding out (D69).
3. **Adjusted prices (D6 gap):** the fixture stores yfinance auto-adjusted closes.
   Return dynamics embed dividends, but commissions/impact are computed on adjusted
   (not raw) notionals — exactly the corruption D6 exists to fix in Step 7. Dividend
   cash flows on the short leg are not separately modeled.
4. **Unhardened data (D24–D26 gaps):** no snapshot checksum, no cleaning report, no
   sanity gate. The fixture is frozen only by being committed to git (D70).
5. **Cost-parameter look-ahead (D70):** σ/ADV for the impact model are calibrated on
   the full sample. This touches cost calibration only, not the trading signal.
6. **IBKR constants unverified against the live page (D65):** the schedule modeled is
   the long-published one; the pricing page 403-blocks automated fetches.

## Reproduction

`uv run python scripts/run_first_result.py` — offline, deterministic from the
committed fixture. The same run is asserted in
`tests/integration/test_first_result_e2e.py` (monotonicity + 0× ≡ zero-cost gates).
"""
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(doc, encoding="utf-8")
    registry.close()

    print(render_sweep_table(sweep))
    print(f"\nwrote {RESULTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
