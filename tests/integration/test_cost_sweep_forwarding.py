"""`run_cost_sweep` must forward every `run_backtest` argument it accepts.

The sweep adds no semantics of its own, so its 1x run must be bit-identical to `run_backtest`
called directly with the same arguments. Each forwarding test also checks that the argument
changes the result. Without that check the comparison would pass whether or not the sweep
forwards the argument, because both runs would silently use the default.
"""

import inspect
from datetime import datetime, timedelta

import pytest

from backtest_framework.costs.bricks import PercentOfNotionalSpread
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.dataview import MissingVolumeError
from backtest_framework.engine.risk import RiskLimits
from backtest_framework.engine.strategy import ScheduledWeightStrategy
from backtest_framework.engine.sweep import run_cost_sweep
from backtest_framework.instruments.equity import Equity
from backtest_framework.pipeline.sizing import TargetWeight
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.simulator.fills import Bar

DAYS = [datetime(2021, 1, 4, 16, 0) + timedelta(days=i) for i in range(8)]
# Opens differ from the previous close, so a close fill and a next-open fill land on different
# prices and the fill_timing case can tell them apart.
OPENS = [100.0, 101.0, 99.0, 103.0, 104.0, 102.0, 105.0, 107.0]
CLOSES = [101.0, 99.0, 103.0, 104.0, 102.0, 105.0, 107.0, 106.0]
VOLUMES = [100.0, 300.0, 100.0, 300.0, 300.0, 100.0, 300.0, 100.0]
WEIGHTS = [0.5, 0.5, 0.0, 0.8, 0.8, 0.2, 0.2, 0.0]


def _bars(opens, closes):
    return [
        TimestampedBar(day, Bar(open=o, high=max(o, c) + 1.0, low=min(o, c) - 1.0, close=c))
        for day, o, c in zip(DAYS, opens, closes)
    ]


BARS = {"X": _bars(OPENS, CLOSES)}
INSTRUMENTS = {"X": Equity(symbol="X", quantity_precision=8)}
STACK = CostStack(trade_bricks=(PercentOfNotionalSpread(bps=10.0),))
STARTING_CASH = 100_000.0

# A 2-for-1 split before bar 4: as-traded prices halve from there on; the split-adjusted view
# halves the bars before it instead.
SPLIT_DAY = DAYS[4]
RAW_SPLIT_BARS = {"X": _bars(OPENS[:4] + [p / 2 for p in OPENS[4:]], CLOSES[:4] + [p / 2 for p in CLOSES[4:]])}
VIEW_SPLIT_BARS = {"X": _bars([p / 2 for p in OPENS[:4]] + [p / 2 for p in OPENS[4:]],
                              [p / 2 for p in CLOSES[:4]] + [p / 2 for p in CLOSES[4:]])}


def scheduled():
    return [ScheduledWeightStrategy(strategy_id="s", weights_by_instrument={"X": WEIGHTS})]


class VolumeGatedStrategy:
    """Holds 0.6 of capital on bars whose volume exceeds 200, flat otherwise. It calls
    `require_volume`, so it raises when the engine was given no volume series."""

    strategy_id = "volume"

    def generate_targets(self, views):
        view = views["X"]
        volume = view.require_volume(view.current_index)
        weight = 0.6 if volume is not None and volume > 200.0 else 0.0
        return [TargetWeight(strategy_id=self.strategy_id, instrument_id="X", weight=weight)]


def volume_gated():
    return [VolumeGatedStrategy()]


class PriceLevelStrategy:
    """Holds 0.6 of capital while the close it sees is above 75, 0.2 otherwise. Its decisions
    depend on which price series it is shown, so it separates view bars from execution bars."""

    strategy_id = "level"

    def generate_targets(self, views):
        view = views["X"]
        weight = 0.6 if view.current_bar.close > 75.0 else 0.2
        return [TargetWeight(strategy_id=self.strategy_id, instrument_id="X", weight=weight)]


def price_level():
    return [PriceLevelStrategy()]


def run_both(make_strategies, bars=BARS, **extra):
    """The sweep's 1x run and a direct run_backtest call on identical arguments."""
    swept = run_cost_sweep(
        bars_by_instrument=bars,
        instruments=INSTRUMENTS,
        make_strategies=make_strategies,
        base_cost_stack=STACK,
        allocator=ConstantSplitAllocator(),
        starting_cash=STARTING_CASH,
        multipliers=(1.0,),
        **extra,
    ).runs[0].result
    direct = run_backtest(
        bars_by_instrument=bars,
        instruments=INSTRUMENTS,
        strategies=make_strategies(),
        cost_stack=STACK,
        allocator=ConstantSplitAllocator(),
        starting_cash=STARTING_CASH,
        **extra,
    )
    return swept, direct


def outcome(result):
    return result.equity_curve, result.fills, result.final_positions, result.violations


# (id, strategy factory, bars, the argument under test, the same run without it or with another value)
CASES = [
    ("fill_timing", scheduled, BARS, {"fill_timing": "next_open"}, {}),
    ("volumes", volume_gated, BARS, {"volumes_by_instrument": {"X": VOLUMES}},
     {"volumes_by_instrument": {"X": [100.0] * len(DAYS)}}),
    ("pretrade_risk_gate", scheduled, BARS,
     {"risk_limits": RiskLimits(max_gross_exposure=60_000.0), "enforce_pretrade": True}, {}),
    ("splits", scheduled, RAW_SPLIT_BARS, {"splits_by_instrument": {"X": [(SPLIT_DAY, 2.0)]}}, {}),
    # Splits held fixed so that only the view series differs between the two runs.
    ("view_bars", price_level, RAW_SPLIT_BARS,
     {"splits_by_instrument": {"X": [(SPLIT_DAY, 2.0)]}, "view_bars_by_instrument": VIEW_SPLIT_BARS},
     {"splits_by_instrument": {"X": [(SPLIT_DAY, 2.0)]}}),
]


@pytest.mark.parametrize(("make", "bars", "extra", "baseline"), [c[1:] for c in CASES], ids=[c[0] for c in CASES])
def test_the_sweep_forwards_the_argument_exactly(make, bars, extra, baseline):
    swept, direct = run_both(make, bars=bars, **extra)
    assert outcome(swept) == outcome(direct)

    # The argument must matter in this scenario, or the equality above proves nothing.
    swept_baseline, _ = run_both(make, bars=bars, **baseline)
    assert outcome(swept) != outcome(swept_baseline)


def test_a_volume_strategy_swept_without_volumes_raises():
    """No volume series must crash the sweep, not return flat books for every multiplier."""
    with pytest.raises(MissingVolumeError, match="volume is required"):
        run_cost_sweep(
            bars_by_instrument=BARS,
            instruments=INSTRUMENTS,
            make_strategies=volume_gated,
            base_cost_stack=STACK,
            allocator=ConstantSplitAllocator(),
            starting_cash=STARTING_CASH,
            multipliers=(0.0, 1.0),
        )


def test_every_swept_trial_is_logged_with_the_forwarded_identity(tmp_path):
    """config, snapshot_id and seed change no number in the backtest; they reach the trial
    registry only, so they are checked there."""
    registry = TrialRegistry(tmp_path / "trials.sqlite")
    run_cost_sweep(
        bars_by_instrument=BARS,
        instruments=INSTRUMENTS,
        make_strategies=scheduled,
        base_cost_stack=STACK,
        allocator=ConstantSplitAllocator(),
        starting_cash=STARTING_CASH,
        multipliers=(0.0, 2.0),
        trial_registry=registry,
        trial_id_prefix="fwd",
        config={"strategy": "scheduled"},
        snapshot_id="snapshot-abc",
        seed=7,
    )
    for multiplier in (0.0, 2.0):
        trial = registry.get_trial(f"fwd-{multiplier}x")
        assert trial.snapshot_id == "snapshot-abc"
        assert trial.seed == 7
        assert trial.config == {"strategy": "scheduled", "cost_multiplier": multiplier}


def test_the_sweep_accepts_every_run_backtest_argument():
    """A keyword added to run_backtest and not to the sweep fails here, before any study
    silently sweeps with the default."""
    backtest = set(inspect.signature(run_backtest).parameters)
    sweep = set(inspect.signature(run_cost_sweep).parameters)
    replaced = {
        "strategies": "make_strategies",  # a factory, so each multiplier gets fresh state
        "cost_stack": "base_cost_stack",  # scaled once per multiplier
        "trial_id": "trial_id_prefix",  # one trial id per multiplier
    }
    assert backtest - set(replaced) <= sweep
    assert sweep - backtest == set(replaced.values()) | {"multipliers"}
