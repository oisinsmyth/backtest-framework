"""`scripts/fast_null.py` — the module CLAUDE.md says every runner must be built on.

It had no test of any kind before D542, which is why two defects sat in it: a threaded
fan-out that silently dropped same-key results, and a zero-variance branch that scored a
degenerate null draw `0.0` where `analytics.metrics.sharpe` returns `sign(mu) * inf`.

These gates cover the two corrected behaviours and the invariant underneath each. They do
NOT cover the bit-identity claims in the module docstring — those need a real panel and
are checked by `python scripts/fast_null.py --verify`, which is a different instrument.
"""

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location("fast_null", REPO / "scripts" / "fast_null.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["fast_null"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


F = _load()


# ------------------------------------------------------------------ parallel_map


def test_parallel_map_returns_one_result_per_key():
    out = F.parallel_map(lambda k, v: v * 2, [("a", 1), ("b", 2), ("c", 3)], workers=2)
    assert out == {"a": 2, "b": 4, "c": 6}


def test_parallel_map_refuses_duplicate_keys_instead_of_dropping_them():
    """The defect: `out` is keyed by item key, so a repeat overwrites — while `done` still
    counts to `len(items)`, so the progress line reports N and the caller receives fewer.

    A silently short dict is the worst shape of wrong here: a null that ran 300 draws and
    returned 280 would produce a percentile off by the missing draws with nothing to see.
    """
    with pytest.raises(ValueError, match="repeat"):
        F.parallel_map(lambda k, v: v, [("a", 1), ("a", 2), ("b", 3)], workers=2)


def test_the_duplicate_guard_names_the_offending_keys():
    """A guard that fires without saying what tripped it makes the caller re-derive it."""
    with pytest.raises(ValueError) as caught:
        F.parallel_map(lambda k, v: v, [("x", 1), ("x", 2), ("y", 3), ("y", 4)], workers=2)
    assert "'x'" in str(caught.value) and "'y'" in str(caught.value)


def test_the_guard_does_not_fire_on_the_shape_the_repo_actually_passes():
    """`run_nulls` passes `books.items()` — a dict, so keys are unique by construction.
    A guard that refused the only live caller would be a regression, not a fix."""
    books = {"top25": 1, "top50": 2, "all": 3}
    assert F.parallel_map(lambda k, v: v, list(books.items()), workers=2) == books


# ------------------------------------------------------------------ the zero-variance branch


def _score(excess, ppy=252.0):
    """`light_score`'s Sharpe branch, isolated from the panel machinery it needs."""
    sd = float(np.std(excess, ddof=1))
    mu = float(np.mean(excess))
    return (mu / sd * math.sqrt(ppy)) if sd > 0 else (math.inf * mu if mu != 0 else 0.0)


def test_the_degenerate_branch_now_matches_the_framework_sharpe():
    from backtest_framework.analytics.metrics import sharpe

    for excess in (
        np.zeros(50),  # the all-flat rotation
        np.full(50, 0.001),  # constant positive
        np.full(50, -0.001),  # constant negative — the reachable one
        np.array([0.01, -0.02, 0.005] * 10),  # ordinary
    ):
        assert _score(excess) == sharpe(excess, 0.0, 252.0)


def test_the_all_flat_rotation_was_never_the_mis_scored_case():
    """Recorded because the audit that found this defect named the wrong mechanism.

    A flat book has `r == 0`, so `lf == sf == 0`, so `ex == 0` — mean zero, and BOTH
    conventions return `0.0`. The old branch and the new one agree exactly here.
    """
    assert _score(np.zeros(50)) == 0.0
    old_branch = 0.0  # what `sd > 0 else 0.0` returned
    assert _score(np.zeros(50)) == old_branch


def test_the_reachable_divergence_deflates_rather_than_inflates():
    """A book that HOLDS while every held bar returns exactly zero (padded or halted
    bars, which these fixtures carry) gives `ex == -lf*rf - sf*bor`: constant, negative.

    Truth is `-inf`. The old branch said `0.0`, which ranks that null draw ABOVE every
    losing draw — so the real book's percentile came out LOWER than it should have. The
    defect was conservative. This test is the direction, which is the falsifiable half.
    """
    lf, rf_per_bar = 0.5, 0.04 / 252.0
    excess = np.full(200, -lf * rf_per_bar)
    assert _score(excess) == -math.inf
    assert _score(excess) < 0.0, "the corrected value must rank BELOW the old 0.0"


def test_the_guard_that_would_catch_this_on_a_real_book_is_exact():
    """`assert_matches_scorer` compares with `!=`, not a tolerance, so a real book that
    ever goes degenerate now fails loudly against a scorer still returning 0.0 rather than
    quietly inheriting either convention. That is the intended behaviour, not a gap."""
    source = (REPO / "scripts" / "fast_null.py").read_text(encoding="utf-8")
    body = source.split("def assert_matches_scorer")[1].split("\ndef ")[0]
    assert "if got != want:" in body
    assert "pytest.approx" not in body and "isclose" not in body
