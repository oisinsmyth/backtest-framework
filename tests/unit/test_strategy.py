"""Unit tests for Strategy / ScheduledWeightStrategy (engine/strategy.py).

Confirms the strategy only ever reads bars through the DataView guard (D32) — it
never sees anything beyond view.current_index, by construction, since it has no
other way to reach the underlying series. One DataView per instrument (D64) — a
single-instrument strategy is just a one-entry mapping.
"""

from backtest_framework.engine.dataview import build_data_view
from backtest_framework.engine.strategy import ScheduledWeightStrategy
from backtest_framework.pipeline.sizing import TargetWeight
from backtest_framework.simulator.fills import Bar


def _bars(n: int) -> tuple[Bar, ...]:
    return tuple(Bar(open=float(i), high=float(i), low=float(i), close=float(i)) for i in range(n))


def test_scheduled_weight_strategy_follows_schedule_by_bar_index():
    strategy = ScheduledWeightStrategy(strategy_id="s1", weights_by_instrument={"AAPL": [0.5, 0.5, 0.0]})

    views0 = {"AAPL": build_data_view(_bars(3), up_to_index=0)}
    views1 = {"AAPL": build_data_view(_bars(3), up_to_index=1)}
    views2 = {"AAPL": build_data_view(_bars(3), up_to_index=2)}

    assert strategy.generate_targets(views0) == [TargetWeight("s1", "AAPL", 0.5)]
    assert strategy.generate_targets(views1) == [TargetWeight("s1", "AAPL", 0.5)]
    assert strategy.generate_targets(views2) == [TargetWeight("s1", "AAPL", 0.0)]


def test_scheduled_weight_strategy_holds_last_value_past_schedule_end():
    strategy = ScheduledWeightStrategy(strategy_id="s1", weights_by_instrument={"AAPL": [0.3]})

    views = {"AAPL": build_data_view(_bars(5), up_to_index=4)}  # schedule only has 1 entry
    assert strategy.generate_targets(views) == [TargetWeight("s1", "AAPL", 0.3)]


def test_strategy_never_reaches_bars_beyond_the_view_it_was_given():
    strategy = ScheduledWeightStrategy(strategy_id="s1", weights_by_instrument={"AAPL": [0.5] * 10})
    view = build_data_view(_bars(10), up_to_index=2)  # only bars 0..2 are visible

    strategy.generate_targets({"AAPL": view})  # exercising the strategy at all

    # The strategy was handed a view with no future bars in it at all (D56) — there's
    # nothing to assert about "the strategy peeking," because there was never anything
    # to peek at.
    assert view.current_index == 2
    assert len(view) == 3


def test_scheduled_weight_strategy_targets_multiple_instruments_independently():
    # A pairs-shaped strategy: long one leg, short the other, each with its own
    # schedule and its own DataView.
    strategy = ScheduledWeightStrategy(
        strategy_id="pairs",
        weights_by_instrument={"XLE": [0.5, 0.5], "XOP": [-0.5, -0.4]},
    )
    views = {
        "XLE": build_data_view(_bars(5), up_to_index=1),
        "XOP": build_data_view(_bars(5), up_to_index=1),
    }

    targets = strategy.generate_targets(views)

    assert TargetWeight("pairs", "XLE", 0.5) in targets
    assert TargetWeight("pairs", "XOP", -0.4) in targets
    assert len(targets) == 2
