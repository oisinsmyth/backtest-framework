"""D38's label gate, reinterpreted per D82: no sector momentum strategy exists in
this codebase to label (the original docs assumed one carried over; it never did).
The gate's intent — strategies outside the market-neutral thesis carry an explicit
honest label, enforced by a grep-style test so labels can't rot — is enforced on the
strategies that DO exist. When a directional strategy is ever added, THIS test is
where its label requirement lives.
"""

import backtest_framework.engine.strategy as strategy_module
import backtest_framework.strategies.zscore_pairs as zscore_module
from backtest_framework.engine.strategy import ScheduledWeightStrategy
from backtest_framework.strategies.zscore_pairs import ZScorePairsStrategy


def test_scheduled_weight_strategy_is_labelled_a_toy():
    text = (strategy_module.__doc__ or "") + (ScheduledWeightStrategy.__doc__ or "")
    assert "toy" in text.lower() or "reference" in text.lower()


def test_zscore_pairs_is_labelled_the_minimal_non_research_strategy():
    text = (zscore_module.__doc__ or "") + (ZScorePairsStrategy.__doc__ or "")
    assert "not phase g" in text.lower() or "honest minimum" in text.lower()


def test_no_unlabelled_directional_strategy_exists_yet():
    # If a sector-momentum (or any directional) strategy lands in
    # backtest_framework.strategies, it must carry a learning/reference label in its
    # module docstring (D38) — extend this test when that happens; do not delete it.
    import pkgutil

    import backtest_framework.strategies as pkg

    module_names = [m.name for m in pkgutil.iter_modules(pkg.__path__)]
    assert module_names == ["zscore_pairs"], (
        f"new strategy module(s) {set(module_names) - {'zscore_pairs'}} added — "
        "give each an honest thesis label (D38/D82) and register it in this test"
    )
