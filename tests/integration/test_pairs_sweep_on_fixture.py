"""The XLE/XOP z-score pairs sweep end to end on the bundled fixture, offline.

Runs the full equity cost stack at 0x/0.5x/1x/2x/4x and checks two properties on real data:
net P&L never rises as costs are scaled up, and the 0x run equals a run with no cost stack.
"""

from pathlib import Path

import pytest

from backtest_framework.costs.bricks import PercentOfNotionalSpread
from backtest_framework.costs.equity_bricks import (
    BorrowFee,
    IBKRCommission,
    ImpactParams,
    MarginInterest,
    SqrtImpact,
)
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.csv_fixture import load_fixture_csv
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.sweep import run_cost_sweep
from backtest_framework.instruments.equity import Equity
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.strategies.zscore_pairs import ZScorePairsStrategy

TOLERANCE = 1e-6
REPO = Path(__file__).resolve().parent.parent.parent
FIXTURE = REPO / "data" / "fixtures" / "xle_xop_daily_2015_2024.csv"
STARTING_CASH = 100_000.0

# Calibrated on the full fixture: a mild look-ahead in the cost parameters, never in the signal.
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
INSTRUMENTS = {"XLE": Equity(symbol="XLE"), "XOP": Equity(symbol="XOP")}


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


@pytest.fixture(scope="module")
def bars_by_instrument():
    return load_fixture_csv(FIXTURE)


def test_fixture_is_present_and_plausible(bars_by_instrument):
    assert set(bars_by_instrument) == {"XLE", "XOP"}
    for symbol, series in bars_by_instrument.items():
        assert len(series) > 2000  # ~10 years of daily bars
        # OHLC consistency to a float tolerance, not exactly: the fixture has one epsilon
        # artifact from the provider's adjustment arithmetic (XOP 2018-10-24, close < low by
        # 1.2e-16 relative). This is a smoke check; the validator is the real sanity gate.
        for tb in series:
            tol = 1e-9 * tb.bar.close
            assert tb.bar.low - tol <= tb.bar.close <= tb.bar.high + tol, (symbol, tb)


def test_sweep_on_real_fixture_is_monotonic_and_logs_trials(bars_by_instrument, tmp_path):
    registry = TrialRegistry(tmp_path / "trials.sqlite")
    sweep = run_cost_sweep(
        bars_by_instrument=bars_by_instrument,
        instruments=INSTRUMENTS,
        make_strategies=make_strategies,
        base_cost_stack=build_cost_stack(),
        allocator=ConstantSplitAllocator(),
        starting_cash=STARTING_CASH,
        multipliers=(0.0, 0.5, 1.0, 2.0, 4.0),
        trial_registry=registry,
        trial_id_prefix="e2e",
        config=CONFIG,
        snapshot_id=FIXTURE.name,
        seed=0,
    )

    # Net P&L is monotonically non-increasing in the cost multiplier, on real data.
    pnls = [pnl for _, pnl in sweep.net_pnls()]
    assert all(later <= earlier + TOLERANCE for earlier, later in zip(pnls, pnls[1:]))

    # One trial per multiplier, carrying the fixture as snapshot_id.
    assert len(registry) == 5
    trial = registry.get_trial("e2e-1.0x")
    assert trial.snapshot_id == FIXTURE.name
    assert trial.config["cost_multiplier"] == 1.0


def test_zero_multiplier_equals_zero_cost_run_on_real_fixture(bars_by_instrument):
    sweep = run_cost_sweep(
        bars_by_instrument=bars_by_instrument,
        instruments=INSTRUMENTS,
        make_strategies=make_strategies,
        base_cost_stack=build_cost_stack(),
        allocator=ConstantSplitAllocator(),
        starting_cash=STARTING_CASH,
        multipliers=(0.0,),
    )
    zero_cost = run_backtest(
        bars_by_instrument=bars_by_instrument,
        instruments=INSTRUMENTS,
        strategies=make_strategies(),
        cost_stack=CostStack(),
        allocator=ConstantSplitAllocator(),
        starting_cash=STARTING_CASH,
    )

    assert sweep.runs[0].result.final_nav == pytest.approx(zero_cost.final_nav, rel=TOLERANCE)
