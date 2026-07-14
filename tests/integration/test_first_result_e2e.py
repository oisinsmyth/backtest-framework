"""The Step 6 I-gate as a repeatable, OFFLINE test: the XLE/XOP sweep runs end to end
on the committed fixture (no network — the fixture is in git, D70) and both D8 gates
hold on real data. Imports the run script's own config/factories by path, so the test
and docs/results/first_real_number.md can't drift apart silently.
"""

import importlib.util
from pathlib import Path

import pytest

from backtest_framework.costs.stack import CostStack
from backtest_framework.data.csv_fixture import load_fixture_csv
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.sweep import run_cost_sweep
from backtest_framework.instruments.equity import Equity
from backtest_framework.registry.trial_registry import TrialRegistry

TOLERANCE = 1e-6  # D47
REPO = Path(__file__).resolve().parent.parent.parent

_spec = importlib.util.spec_from_file_location("run_first_result", REPO / "scripts" / "run_first_result.py")
_script = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_script)

INSTRUMENTS = {"XLE": Equity(symbol="XLE"), "XOP": Equity(symbol="XOP")}


@pytest.fixture(scope="module")
def bars_by_instrument():
    return load_fixture_csv(_script.FIXTURE)


def test_fixture_is_present_and_plausible(bars_by_instrument):
    assert set(bars_by_instrument) == {"XLE", "XOP"}
    for symbol, series in bars_by_instrument.items():
        assert len(series) > 2000  # ~10 years of daily bars
        # OHLC consistency to a float tolerance, not exactly (D47): the fixture has one
        # genuine epsilon artifact from yfinance's adjustment arithmetic (XOP
        # 2018-10-24, close < low by 1.2e-16 relative). A real sanity gate with
        # explicit thresholds and quarantine is D26 / Step 7 — this is a smoke check.
        for tb in series:
            tol = 1e-9 * tb.bar.close
            assert tb.bar.low - tol <= tb.bar.close <= tb.bar.high + tol, (symbol, tb)


def test_sweep_on_real_fixture_is_monotonic_and_logs_trials(bars_by_instrument, tmp_path):
    registry = TrialRegistry(tmp_path / "trials.sqlite")
    sweep = run_cost_sweep(
        bars_by_instrument=bars_by_instrument,
        instruments=INSTRUMENTS,
        make_strategies=_script.make_strategies,
        base_cost_stack=_script.build_cost_stack(),
        allocator=ConstantSplitAllocator(),
        starting_cash=_script.STARTING_CASH,
        multipliers=(0.0, 0.5, 1.0, 2.0, 4.0),
        trial_registry=registry,
        trial_id_prefix="e2e",
        config=_script.CONFIG,
        snapshot_id=_script.FIXTURE.name,
        seed=0,
    )

    # I-gate: net P&L monotonically non-increasing in the multiplier, on real data.
    pnls = [pnl for _, pnl in sweep.net_pnls()]
    assert all(later <= earlier + TOLERANCE for earlier, later in zip(pnls, pnls[1:]))

    # D20: one trial per multiplier, carrying the fixture as snapshot_id.
    assert len(registry) == 5
    trial = registry.get_trial("e2e-1.0x")
    assert trial.snapshot_id == _script.FIXTURE.name
    assert trial.config["cost_multiplier"] == 1.0


def test_zero_multiplier_equals_zero_cost_run_on_real_fixture(bars_by_instrument):
    sweep = run_cost_sweep(
        bars_by_instrument=bars_by_instrument,
        instruments=INSTRUMENTS,
        make_strategies=_script.make_strategies,
        base_cost_stack=_script.build_cost_stack(),
        allocator=ConstantSplitAllocator(),
        starting_cash=_script.STARTING_CASH,
        multipliers=(0.0,),
    )
    zero_cost = run_backtest(
        bars_by_instrument=bars_by_instrument,
        instruments=INSTRUMENTS,
        strategies=_script.make_strategies(),
        cost_stack=CostStack(),
        allocator=ConstantSplitAllocator(),
        starting_cash=_script.STARTING_CASH,
    )

    assert sweep.runs[0].result.final_nav == pytest.approx(zero_cost.final_nav, rel=TOLERANCE)
