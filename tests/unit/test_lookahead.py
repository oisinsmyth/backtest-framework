"""`validation/lookahead.py` against the runners it was lifted from, exactly (D593).

Gate U. The three halves of this file answer three different questions:

**1. Is the library's lag the runners' lag?** Not "does it look like it" — R16's discipline
applied to code rather than to a published number. The library's `lag1`, `delayed`,
`audit_lag_topn` and `audit_lag_monthend` are asserted **bit-identical** to the four runner
functions they were lifted from, each loaded by file path and never edited:
the runner's `lag1` at `scripts/run_concentrated_short.py:54`;
`skipped` at `scripts/d290_skip_bar_test.py:74`;
`audit_lag` at `scripts/run_overnight_short.py:454`;
`audit_lag` at `scripts/run_d555_tsmom_replication.py:424`.
All four import in about a second and read no fixture at import.

**2. Can the audits fire?** `scripts/run_overnight_long.py:270-276` states the rule that makes
the lag audit mean anything — the synthetic score MUST vary with time, or a lagged and an
unlagged book agree by construction — and `test_a_constant_score_makes_the_audit_blind` is
that rule as a measurement rather than a comment: the audit ACCEPTS an unlagged book under a
constant score and RAISES on the same book under a time-varying one.

**3. What does the static scan see, and what does it not?** The leak canary
(`_leaky_canary_module.py`) must be rejected; `lag1`'s own source and `hold_book`'s must not.
The misses are enumerated in `test_the_scan_cannot_see` — a scan whose blind spots are
undocumented is read as a proof.

No fixture, no strategy return: synthetic grids only.
"""

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path

import numpy as np
import pytest

from backtest_framework.validation.lookahead import (
    ForwardIndexError,
    LabelLeakError,
    assert_no_forward_index,
    audit_lag_monthend,
    audit_lag_topn,
    delayed,
    expect_raise,
    forward_index_sites,
    labels_never_features,
    lag1,
    retained_edge,
)

REPO = Path(__file__).resolve().parents[2]
CANARY = Path(__file__).with_name("_leaky_canary_module.py")


def _load(name: str, filename: str):
    """The runner-loading idiom at `tests/unit/test_fast_null.py:23`. Never edits the runner."""
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


C = _load("run_concentrated_short", "run_concentrated_short.py")  # lag1, top_n
B = _load("run_book_single_names", "run_book_single_names.py")  # hold_book
S = _load("run_overnight_short", "run_overnight_short.py")  # audit_lag (equity)
D290 = _load("d290_skip_bar_test", "d290_skip_bar_test.py")  # skipped()
D555 = _load("run_d555_tsmom_replication", "run_d555_tsmom_replication.py")  # audit_lag (futures)


# --------------------------------------------------------------------------------------------
# synthetic fixtures. No fixture file is read anywhere in this module.
# --------------------------------------------------------------------------------------------
def _grid(n: int = 7, t: int = 40, seed: int = 593, nan_frac: float = 0.15) -> np.ndarray:
    """A float score grid with scattered non-finite cells — the shape `top_n` maps to +inf."""
    rng = np.random.default_rng(seed)
    a = rng.standard_normal((n, t))
    a[rng.random((n, t)) < nan_frac] = np.nan
    return a


def _time_varying_score(n: int, t: int) -> np.ndarray:
    """`run_overnight_long.py:276` verbatim: the rank order rotates every bar."""
    return ((np.arange(n, dtype=float)[:, None] + np.arange(t)[None, :]) % n).astype(float)


def _base(n: int = 7, t: int = 40, seed: int = 4) -> np.ndarray:
    """A qualifying-mask book with column 0 zeroed, as `hold_book` leaves it.

    Some bars carry fewer than N qualifiers and some more, so both branches of the audit —
    "hold every qualifier" and "rank and take N" — are exercised rather than one of them.
    """
    rng = np.random.default_rng(seed)
    mask = (rng.random((n, t)) < 0.7).astype(float)
    base = B.hold_book(mask, np.ones((n, t), dtype=bool))
    base[:, :2] = np.where(rng.random((n, 2)) < 0.3, base[:, :2], 0.0)
    base[:, 0] = 0.0
    return base


def _unlagged_book(base: np.ndarray, score: np.ndarray, n: int) -> np.ndarray:
    """The defect D279 shipped: rank on `score[:, t]` and earn bar t (run_overnight_long:302)."""
    out = np.zeros_like(base)
    for t in range(base.shape[1]):
        q = np.flatnonzero(base[:, t] != 0.0)
        if q.size:
            s = np.where(np.isfinite(score[q, t]), score[q, t], np.inf)
            out[q[np.argsort(s, kind="stable")[:n]], t] = 1.0
    return out


# --------------------------------------------------------------------------------------------
# 1. the lag, bit-identical to the runners
# --------------------------------------------------------------------------------------------
@pytest.mark.parametrize("seed", [0, 1, 593])
def test_lag1_is_bit_identical_to_the_runner(seed):
    """Equality, not closeness. NaN placement included, via `equal_nan`."""
    a = _grid(seed=seed)
    ours, theirs = lag1(a), C.lag1(a)
    assert ours.dtype == theirs.dtype
    assert ours.shape == theirs.shape
    assert np.array_equal(ours, theirs, equal_nan=True)
    # ...and bit-identical, which `array_equal` does not promise for signed zeros.
    assert ours.tobytes() == theirs.tobytes()


def test_lag1_puts_nan_in_column_zero_and_shifts_the_rest():
    a = _grid(n=3, t=5, nan_frac=0.0)
    out = lag1(a)
    assert np.isnan(out[:, 0]).all(), "column 0 must be NaN: there is no prior bar"
    assert np.array_equal(out[:, 1:], a[:, :-1])


def test_lag1_raises_on_the_two_dtypes_the_runner_silently_corrupts():
    """The one deliberate divergence, and the sentinel it prevents.

    `np.full_like(a, np.nan)` casts the fill to the array's dtype. Both runner values below
    are MEASURED here, not asserted from the docstring, so if numpy's cast ever changes this
    test says so rather than the record going quietly stale.
    """
    ints = np.arange(6, dtype=np.int64).reshape(2, 3)
    bools = np.ones((2, 3), dtype=bool)

    with pytest.warns(RuntimeWarning):
        runner_int = C.lag1(ints)
    assert runner_int[0, 0] == np.iinfo(np.int64).min  # not a NaN, and finite
    runner_bool = C.lag1(bools)
    assert runner_bool[0, 0] is np.True_  # ranks FIRST ascending, not last

    with pytest.raises(TypeError, match="floating grid"):
        lag1(ints)
    with pytest.raises(TypeError, match="floating grid"):
        lag1(bools)


def test_lag1_raises_on_a_one_dimensional_input():
    with pytest.raises(ValueError, match="2-D"):
        lag1(np.arange(5, dtype=float))
    with pytest.raises(IndexError):  # what the runner does with the same input
        C.lag1(np.arange(5, dtype=float))


# --------------------------------------------------------------------------------------------
# 2. delayed(): the SAME lag composed, never a return-grid shift
# --------------------------------------------------------------------------------------------
def test_delayed_two_is_lag1_of_lag1():
    a = _grid()
    assert np.array_equal(delayed(a, 2), lag1(lag1(a)), equal_nan=True)
    assert np.array_equal(delayed(a, 0), a, equal_nan=True)


@pytest.mark.parametrize("bars", [0, 1, 2, 3, 5])
def test_delayed_is_bit_identical_to_d290s_skipped(bars):
    """`scripts/d290_skip_bar_test.py:79 skipped(score, n)` — n extra applications of D279's lag."""
    a = _grid()
    assert np.array_equal(delayed(a, bars), D290.skipped(a, bars), equal_nan=True)


@pytest.mark.parametrize("bars", [1, 2, 3])
def test_delayed_blanks_exactly_the_first_n_columns(bars):
    a = _grid(nan_frac=0.0)
    out = delayed(a, bars)
    assert np.isnan(out[:, :bars]).all()
    assert np.array_equal(out[:, bars:], a[:, : -bars or None])


def test_a_return_grid_shift_is_a_different_object():
    """D290's rule, as arithmetic: delaying the SIGNAL is not advancing the RETURN.

    `delayed(s, 1)[:, t]` is `s[:, t-1]`; a forward shift of the return grid gives
    `r[:, t+1]` at column t. The first pairs bar t's return with bar t-1's score, the second
    pairs bar t's score with bar t+1's return — and they lose OPPOSITE ends of the sample,
    which is the cheapest way to see they are not the same construction.
    """
    s = _grid(nan_frac=0.0)
    r = _grid(seed=99, nan_frac=0.0)

    signal_delayed = delayed(s, 1)
    returns_advanced = np.full_like(r, np.nan)
    returns_advanced[:, :-1] = r[:, 1:]

    assert np.isnan(signal_delayed[:, 0]).all(), "delaying the signal loses the FIRST bar"
    assert np.isnan(returns_advanced[:, -1]).all(), "advancing the return loses the LAST bar"
    assert not np.isnan(signal_delayed[:, -1]).any()
    assert not np.isnan(returns_advanced[:, 0]).any()

    # And the products they score are not the same grid anywhere the two are both defined.
    a = signal_delayed[:, 1:-1] * r[:, 1:-1]
    b = s[:, 1:-1] * returns_advanced[:, 1:-1]
    assert not np.allclose(a, b)


def test_delayed_refuses_a_negative_delay():
    with pytest.raises(ValueError, match="look-ahead"):
        delayed(_grid(), -1)
    with pytest.raises(TypeError):
        delayed(_grid(), 1.0)


# --------------------------------------------------------------------------------------------
# 3. the lag audits, equal to both runner generations
# --------------------------------------------------------------------------------------------
def test_audit_lag_topn_equals_the_equity_runner_on_a_correctly_lagged_book():
    n_slots = 2
    base = _base()
    sc = _time_varying_score(*base.shape)
    pos = C.top_n(base, sc, n_slots)

    ours = audit_lag_topn(base, sc, n_slots, pos)
    theirs = S.audit_lag(base, sc, n_slots, pos)
    assert ours == theirs
    assert ours > 0, "the audit checked no bars; a gate over an empty set is a green light"


def test_audit_lag_topn_raises_on_an_unlagged_book_and_so_does_the_runner():
    n_slots = 2
    base = _base()
    sc = _time_varying_score(*base.shape)
    unlagged = _unlagged_book(base, sc, n_slots)

    assert expect_raise(lambda: audit_lag_topn(base, sc, n_slots, unlagged), "an unlagged book")
    assert expect_raise(lambda: S.audit_lag(base, sc, n_slots, unlagged), "the runner's audit")


def test_audit_lag_topn_refuses_a_base_that_was_never_lagged():
    """The premise guard: a base with a non-zero column 0 did not come from `hold_book`."""
    base = _base()
    base[:, 0] = 1.0
    sc = _time_varying_score(*base.shape)
    with pytest.raises(AssertionError, match="column 0"):
        audit_lag_topn(base, sc, 2, C.top_n(base, sc, 2))


def test_a_constant_score_makes_the_audit_blind():
    """`run_overnight_long.py:270-276`, measured rather than quoted.

    With a score that does not vary along the time axis, `score[:, t]` and `score[:, t-1]`
    are the same column, so the unlagged book IS the lagged book and the audit passes it.
    That is not a defect in the audit — it is why the self-test's synthetic rotates.
    """
    n_slots = 2
    base = _base()
    n, t = base.shape
    constant = np.tile(np.arange(n, dtype=float)[:, None], (1, t))

    blind = _unlagged_book(base, constant, n_slots)
    assert audit_lag_topn(base, constant, n_slots, blind) > 0, (
        "under a constant score the audit must accept the UNLAGGED book — if this ever "
        "fails, the demonstration below stops proving anything"
    )

    varying = _time_varying_score(n, t)
    assert expect_raise(
        lambda: audit_lag_topn(base, varying, n_slots, _unlagged_book(base, varying, n_slots)),
        "the same unlagged book under a time-varying score",
    )


def _monthend_case(n: int = 3, t: int = 40, seed: int = 555):
    rng = np.random.default_rng(seed)
    me = [9, 19, 29]
    sign_me = rng.choice([-1.0, 0.0, 1.0], size=(n, len(me)))
    live = np.ones((n, t), dtype=bool)
    live[1, 25:] = False  # one root dies mid-sample, so the `live` mask does work
    held = np.zeros((n, t))
    for k, start in enumerate(me):
        end = me[k + 1] if k + 1 < len(me) else t - 1
        for col in range(start + 1, end + 1):
            held[:, col] = sign_me[:, k]
    held = np.where(live, held, 0.0)
    return held, sign_me, me, live, t


def test_audit_lag_monthend_equals_the_futures_runner():
    held, sign_me, me, live, t = _monthend_case()
    ours = audit_lag_monthend(held, sign_me, me, live, t)
    theirs = D555.audit_lag(held, sign_me, me, live, t)
    assert ours == theirs
    assert ours > 0


def test_audit_lag_monthend_raises_on_a_grid_shifted_the_wrong_way():
    """Break what the assertion reads: the held sign grid, moved one session EARLIER.

    A grid rolled left holds the month-end's sign ON the month-end — the one bar the rule may
    not have seen — which is precisely the defect the audit exists to catch.
    """
    held, sign_me, me, live, t = _monthend_case()
    early = np.roll(held, -1, axis=1)
    assert expect_raise(
        lambda: audit_lag_monthend(early, sign_me, me, live, t), "a grid shifted one session early"
    )
    assert expect_raise(
        lambda: D555.audit_lag(early, sign_me, me, live, t), "the runner's audit, same grid"
    )


# --------------------------------------------------------------------------------------------
# 4. retained_edge and expect_raise
# --------------------------------------------------------------------------------------------
def test_retained_edge_reports_a_number_and_not_a_verdict():
    """Ledger §13A.8 control 6 / unit test 70.

    `edge_fn` counts the finite cells of the delayed grid, so the answer is hand-checkable:
    the grid is 7 x 40 with no NaN, so delay d leaves 7 x (40 - d) finite cells and the
    retained fraction at one bar is 39/40 = 0.975.
    """
    s = _grid(n=7, t=40, nan_frac=0.0)
    out = retained_edge(lambda g: float(np.isfinite(g).sum()), s)
    assert out[0] == 7 * 40
    assert out[1] == 7 * 39
    assert out[2] == 7 * 38
    assert out[3] == 7 * 37
    assert out["retained_fraction_at_1"] == pytest.approx(39 / 40)
    assert not any(isinstance(v, bool) for v in out.values()), "no verdict, only numbers"
    assert "passed" not in out and "retained" not in out


def test_retained_edge_is_nan_when_the_undelayed_edge_is_not_positive():
    """Sign gates the comparison: 'keeps 80% of its edge' is empty below zero."""
    out = retained_edge(lambda g: -1.0 if np.isnan(g[:, 0]).all() else -2.0, _grid(nan_frac=0.0))
    assert out[0] == -2.0 and out[1] == -1.0
    assert np.isnan(out["retained_fraction_at_1"])


@pytest.mark.parametrize("delays", [(1, 2), (0, 2, 3), (0, 1, 1), (3, 2, 1, 0), (0, -1)])
def test_retained_edge_refuses_a_delay_list_it_cannot_answer_with(delays):
    with pytest.raises(ValueError):
        retained_edge(lambda g: 1.0, _grid(), delays)


def test_expect_raise_is_itself_able_to_fail():
    def raises():
        raise AssertionError("boom")

    assert expect_raise(raises, "a deliberate break") is True

    logged: list[str] = []
    assert expect_raise(raises, "a logged break", log=logged.append) is True
    assert logged and "a logged break" in logged[0]

    with pytest.raises(AssertionError, match="did NOT raise: a quiet gate"):
        expect_raise(lambda: None, "a quiet gate")


def test_expect_raise_does_not_swallow_a_broken_call():
    """A TypeError from a mis-called audit is a bug in the test, not a fired gate."""
    with pytest.raises(TypeError):
        expect_raise(lambda: "x" + 1, "a typo")  # type: ignore[operator]


# --------------------------------------------------------------------------------------------
# 5. the static scan
# --------------------------------------------------------------------------------------------
def test_the_leak_canary_is_caught():
    """Ledger unit test 71 / opening unit test 25, on a real module rather than a string."""
    sites = forward_index_sites(CANARY.read_text(encoding="utf-8"))
    kinds = [s.kind for s in sites]
    assert kinds == ["forward_index", "forward_index", "negative_shift", "forward_slice"], kinds
    with pytest.raises(ForwardIndexError, match=r"reads past the decision bar"):
        assert_no_forward_index(CANARY)


def test_the_canary_names_the_first_site_and_counts_the_rest():
    with pytest.raises(ForwardIndexError) as exc:
        assert_no_forward_index(CANARY)
    message = str(exc.value)
    assert "_leaky_canary_module.py" in message
    assert "close[t + 1]" in message
    assert "4 site(s) in total" in message


def test_the_runners_own_lag_sources_are_not_flagged():
    """The load-bearing half. Backward shifts and `[:, :-1]` are the convention, not a leak."""
    for fn in (C.lag1, C.top_n, B.hold_book, S.audit_lag, D290.skipped):
        source = inspect.getsource(fn)
        assert forward_index_sites(source) == [], f"{fn.__name__} was flagged: {source[:120]}"
        assert_no_forward_index(source)


def test_the_honest_half_of_the_canary_is_not_flagged():
    import ast

    tree = ast.parse(CANARY.read_text(encoding="utf-8"))
    honest = [
        ast.unparse(node)
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.endswith("_honest")
    ]
    assert len(honest) == 3
    for source in honest:
        assert forward_index_sites(source) == [], source


@pytest.mark.parametrize(
    "source,kind",
    [
        ("x[t + 1]", "forward_index"),
        ("x[1 + t]", "forward_index"),
        ("x[:, t + 1]", "forward_index"),
        ("x[i + 1:]", "forward_slice"),
        ("x[:, t + 1:]", "forward_slice"),
        ("df.iloc[t + 1]", "forward_iloc"),
        ("df.loc[t + 2]", "forward_loc"),
        ("df.shift(-1)", "negative_shift"),
        ("df.shift(periods=-3)", "negative_shift"),
        ("df.shift(-k)", "negative_shift"),
        ("np.roll(x, -1)", "negative_roll"),
        ("np.roll(x, shift=-k)", "negative_roll"),
    ],
)
def test_every_shape_the_scan_claims_to_catch(source, kind):
    sites = forward_index_sites(source)
    assert [s.kind for s in sites] == [kind], (source, sites)


@pytest.mark.parametrize(
    "source",
    [
        "x[t - 1]",
        "x[:t + 1]",  # the bar-INCLUSIVE window; flagging it would kill the scan on arrival
        "x[:, :t + 1]",
        "x[:, :-1]",
        "x[:, 1:]",
        "out[:, 1:] = a[:, :-1]",
        "df.shift(1)",
        "df.shift(periods=2)",
        "np.roll(x, 1)",
        "np.roll(seg, int(rng.integers(0, seg.size)))",
        "x[t + k]",  # <Name> + <Name>: out of scope, and D593 says so
        "score[q, t - 1]",
        "np.arange(n)[:, None] + np.arange(T)[None, :]",
    ],
)
def test_the_scan_leaves_the_backward_constructions_alone(source):
    assert forward_index_sites(source) == [], source


def test_the_scan_cannot_see():
    """The blind spots, written as passing assertions so they cannot be forgotten.

    Each case below IS a look-ahead and each returns no site. They are the reason this scan
    is a tripwire and not a proof, and they are listed in D593 in these words.
    """
    aliased = "k = t + 1\ny = x[k]\n"  # the offset is computed one statement earlier
    indirect = "def nxt(i):\n    return i + 1\ny = x[nxt(t)]\n"  # helper indirection
    negative_stride = "y = x[::-1][t]\n"  # reversed view: position t is the END of the series
    computed_label = "y = df.loc[dates[t + 1]]\n"  # the leak is in the LABEL, not the index
    variable_shift = "k = -1\ny = df.shift(k)\n"  # a name holding a negative
    for source in (aliased, indirect, negative_stride, variable_shift):
        assert forward_index_sites(source) == [], source
    # The one near-miss: the computed label IS caught, but only because the `t + 1` is
    # written inside a subscript. `df.loc[label_for(t)]` would not be.
    assert [s.kind for s in forward_index_sites(computed_label)] == ["forward_index"]


def test_assert_no_forward_index_accepts_source_a_path_and_a_path_string(tmp_path):
    """Three input shapes, and the one that must NOT be mistaken for source: a missing path."""
    clean = "def f(close, t):\n    return close[t] / close[t - 1]\n"
    assert_no_forward_index(clean)

    written = tmp_path / "clean_feature.py"
    written.write_text(clean, encoding="utf-8")
    assert_no_forward_index(written)  # a Path
    assert_no_forward_index(str(written))  # a one-line str ending .py

    with pytest.raises(ForwardIndexError):
        assert_no_forward_index(str(CANARY))
    with pytest.raises(FileNotFoundError, match="looks like a path"):
        assert_no_forward_index("no/such/module.py")


# --------------------------------------------------------------------------------------------
# 6. labels never enter features
# --------------------------------------------------------------------------------------------
def test_labels_never_features_catches_all_three_spellings():
    """Opening doc unit tests 2 and 19."""
    for source in (
        "def f(row):\n    return day_type * 2\n",
        "def f(row):\n    return row.day_type\n",
        "def f(df):\n    return df['day_type'].shift(1)\n",
    ):
        with pytest.raises(LabelLeakError, match="never features"):
            labels_never_features(source, ["day_type", "fwd_ret"])


def test_labels_never_features_leaves_honest_feature_code_alone():
    source = "def f(df):\n    return df['close'].shift(1) / df['open'] - 1.0\n"
    labels_never_features(source, ["day_type", "fwd_ret"])
    labels_never_features(CANARY.read_text(encoding="utf-8"), ["day_type", "fwd_ret"])


def test_labels_never_features_refuses_an_empty_label_list():
    """A leak check over no labels passes by seeing nothing — six gates here have done that."""
    with pytest.raises(ValueError, match="empty"):
        labels_never_features("x = 1\n", [])
