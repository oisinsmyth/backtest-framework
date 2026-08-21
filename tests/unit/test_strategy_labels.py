"""D38's label gate, reinterpreted per D82: no sector momentum strategy exists in
this codebase to label (the original docs assumed one carried over; it never did).
The gate's intent — strategies outside the market-neutral thesis carry an explicit
honest label, enforced by a grep-style test so labels can't rot — is enforced on the
strategies that DO exist. When a directional strategy is ever added, THIS test is
where its label requirement lives.
"""

import backtest_framework.engine.strategy as strategy_module
import backtest_framework.strategies.breakout as breakout_module
import backtest_framework.strategies.zscore_pairs as zscore_module
from backtest_framework.engine.strategy import ScheduledWeightStrategy
from backtest_framework.strategies.breakout import BreakoutStrategy
from backtest_framework.strategies.zscore_pairs import ZScorePairsStrategy


def test_scheduled_weight_strategy_is_labelled_a_toy():
    text = (strategy_module.__doc__ or "") + (ScheduledWeightStrategy.__doc__ or "")
    assert "toy" in text.lower() or "reference" in text.lower()


def test_zscore_pairs_is_labelled_the_minimal_non_research_strategy():
    text = (zscore_module.__doc__ or "") + (ZScorePairsStrategy.__doc__ or "")
    assert "not phase g" in text.lower() or "honest minimum" in text.lower()


def test_breakout_is_labelled_directional_and_outside_the_market_neutral_thesis():
    """The case D38 was written for, now real (D117). The breakout strategy is long
    or flat on a single high-beta instrument — directional by construction. Its
    docstring must say so, and say what the honest benchmark is, or this fails."""
    text = (breakout_module.__doc__ or "") + (BreakoutStrategy.__doc__ or "")
    lowered = " ".join(text.lower().split())  # line wrapping must not defeat the grep
    assert "directional" in lowered
    assert "not part of this project's market-neutral thesis" in lowered
    assert "buy-and-hold" in lowered  # the benchmark frame it must be judged against


def test_no_unlabelled_directional_strategy_exists_yet():
    # If a sector-momentum (or any directional) strategy lands in
    # backtest_framework.strategies, it must carry a learning/reference label in its
    # module docstring (D38) — extend this test when that happens; do not delete it.
    import pkgutil

    import backtest_framework.strategies as pkg

    registered = {"zscore_pairs", "breakout"}
    module_names = {m.name for m in pkgutil.iter_modules(pkg.__path__)}
    assert module_names == registered, (
        f"new strategy module(s) {module_names - registered} added — "
        "give each an honest thesis label (D38/D82) and register it in this test"
    )
