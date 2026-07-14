"""The Step 7 pipeline, end to end and OFFLINE, as a repeatable test: committed raw
fixture -> clean -> validate -> snapshot -> engine (adjusted views / as-traded
execution / dividend flows / split scaling) -> sweep. Imports the v2 run script's own
functions by path so the test and docs/results/first_real_number_v2.md cannot drift.
"""

import importlib.util
from pathlib import Path

import pytest

from backtest_framework.costs.stack import CostStack
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.sweep import run_cost_sweep
from backtest_framework.instruments.equity import Equity

TOLERANCE = 1e-6  # D47
REPO = Path(__file__).resolve().parent.parent.parent

_spec = importlib.util.spec_from_file_location("run_first_result_v2", REPO / "scripts" / "run_first_result_v2.py")
_script = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_script)

INSTRUMENTS = {"XLE": Equity(symbol="XLE"), "XOP": Equity(symbol="XOP")}


@pytest.fixture(scope="module")
def pipeline(tmp_path_factory):
    snapshot = _script.create_and_load_snapshot(store_root=tmp_path_factory.mktemp("snapshots"))
    execution, views, declared_dividends, splits = _script.build_run_inputs(snapshot)
    return snapshot, execution, views, declared_dividends, splits


def test_snapshot_freezes_clean_and_unquarantined(pipeline):
    snapshot, *_ = pipeline
    assert snapshot.meta["quarantined"] is False
    assert snapshot.meta["validation"]["passed"] is True
    # The genuine 2020-03-09 crash day is RECORDED as a warning, not hidden (D74).
    warnings = [v for v in snapshot.meta["validation"]["violations"] if not v["hard"]]
    assert warnings


def test_sweep_on_hardened_pipeline_is_monotonic(pipeline):
    snapshot, execution, views, declared_dividends, splits = pipeline
    sweep = run_cost_sweep(
        bars_by_instrument=execution,
        instruments=INSTRUMENTS,
        make_strategies=_script.make_strategies,
        base_cost_stack=_script.build_cost_stack(declared_dividends),
        allocator=ConstantSplitAllocator(),
        starting_cash=_script.STARTING_CASH,
        multipliers=(0.0, 0.5, 1.0, 2.0, 4.0),
        splits_by_instrument=splits,
        view_bars_by_instrument=views,
    )
    pnls = [pnl for _, pnl in sweep.net_pnls()]
    assert all(later <= earlier + TOLERANCE for earlier, later in zip(pnls, pnls[1:]))


def test_zero_multiplier_equals_frictionless_run_with_flows_retained(pipeline):
    # Event flows are NOT frictions and don't scale (D75): the 0x baseline is a run
    # with zero frictions but the SAME dividend flows - not an empty CostStack.
    snapshot, execution, views, declared_dividends, splits = pipeline
    sweep = run_cost_sweep(
        bars_by_instrument=execution,
        instruments=INSTRUMENTS,
        make_strategies=_script.make_strategies,
        base_cost_stack=_script.build_cost_stack(declared_dividends),
        allocator=ConstantSplitAllocator(),
        starting_cash=_script.STARTING_CASH,
        multipliers=(0.0,),
        splits_by_instrument=splits,
        view_bars_by_instrument=views,
    )
    frictionless = run_backtest(
        bars_by_instrument=execution,
        instruments=INSTRUMENTS,
        strategies=_script.make_strategies(),
        cost_stack=CostStack(
            event_flow_bricks=_script.build_cost_stack(declared_dividends).event_flow_bricks
        ),
        allocator=ConstantSplitAllocator(),
        starting_cash=_script.STARTING_CASH,
        splits_by_instrument=splits,
        view_bars_by_instrument=views,
    )
    assert sweep.runs[0].result.final_nav == pytest.approx(frictionless.final_nav, rel=TOLERANCE)
