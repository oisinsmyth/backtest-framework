"""Look-ahead defences: the lag convention, the one-bar-delay rerun, and a static leak scan (D593).

Three of the User-Doc-Deposit pre-registrations declare the same two look-ahead controls in
identical words, and neither existed as code:

  * `SETTLEMENT_FLOW_LEDGER_PREREG.md` §13A.8 control 6 — *"One-bar-delay robustness: rerun
    with every signal delayed by one extra bar. The strategy must keep >= 50% of its edge"*
    and *"Leak canary: the test harness includes a deliberately leaky feature (using a future
    bar). The pipeline's static checks must reject it. If it isn't caught, all results are
    invalid until the check is fixed."* — unit tests 70 and 71;
  * `OPENING_AGENT_STATE_PREREG.md` §12A control 6, unit tests 2 ("labels never enter
    features (static check on the feature pipeline)"), 19 and 25;
  * `INDEX_REWEIGHT_FLOW_PREREG.md` unit test 9 and §10.

**"The pipeline's static checks" named a thing that did not exist.** Look-ahead was enforced
here in exactly two places, neither of them a scan of feature code: structurally, on the
framework path, by `engine/dataview.py` (a `DataView` is CONSTRUCTED holding only the visible
bars, so `LookAheadError` is raised by an index that resolves past `current_index`); and by
hand, in runner audits, by re-deriving the held set from `score[:, t-1]` in a second
implementation (`scripts/run_overnight_short.py:454`). The 600-plus one-shot runners in
`scripts/` hold raw `(n_symbols, T)` numpy grids and get neither — and a count is deliberately
not quoted here, because `scripts/build_readme_counts.py` owns it. This module is the third
instrument — a syntactic tripwire over feature SOURCE — and the first two halves are lifted
from the runners so that library and runner cannot drift.

THE LAG CONVENTION, and why it is copied rather than reinvented
---------------------------------------------------------------
`lag1` is `scripts/run_concentrated_short.py:54`, whose docstring records what it cost to
learn: `corr(hist_L[t], ret[t]) = +0.0737` against `corr(hist_L[t-1], ret[t]) = -0.0103`, and
`top25` scoring **+2.250 Sharpe unlagged against -0.638 lagged**. R9. `delayed` is D290's
skip-bar rerun (`scripts/d290_skip_bar_test.py`), and it composes the SAME lag rather than
shifting the return grid, for the reason that file gives: the alternative *"would have been a
second, differently-written implementation of the same idea, and this study has already been
bitten by exactly that."* `tests/unit/test_lookahead.py` asserts bit-equality with both
runners rather than restating them.

**One deliberate divergence from the runner, and it is a guard, not a rewrite.** The runner's
`lag1` is `np.full_like(a, np.nan)` followed by a shift, and `np.full_like` casts the fill to
the array's dtype. On an **integer** grid that writes `-9223372036854775808` into column 0
with only a `RuntimeWarning`, and on a **boolean** grid it writes `True` — which, under the
ascending `np.argsort` every selector here uses, ranks column 0 **first** instead of last.
Both are the "no prior bar" sentinel silently becoming a competitive score. `lag1` below
raises on any non-floating dtype; the equality tests pin bit-identity on float grids and
record the two sentinels the runner produces. See D593.

WHAT THIS MODULE IS NOT
-----------------------
It computes no strategy return and reads no fixture. `retained_edge` reports the retained
fraction as a **number** and never a verdict: the docs' >= 50% line is a threshold declared
as a floor, and a runner that returned a pass/fail would be asserting the pre-registration's
conclusion instead of supplying its input.

House style follows `validation/power.py`: stdlib plus numpy, every guard raising loudly
rather than returning a sentinel (D48).
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

__all__ = [
    "ForwardIndexError",
    "ForwardIndexSite",
    "LabelLeakError",
    "assert_no_forward_index",
    "audit_lag_monthend",
    "audit_lag_topn",
    "delayed",
    "expect_raise",
    "forward_index_sites",
    "labels_never_features",
    "lag1",
    "retained_edge",
]


class ForwardIndexError(AssertionError):
    """A feature's SOURCE reads an index strictly after the decision bar.

    An `AssertionError` rather than a bespoke base, so that `expect_raise` — the idiom every
    runner self-test here uses to prove an audit can fire — catches it without a second
    except clause.
    """


class LabelLeakError(AssertionError):
    """A label identifier appears in feature source (opening doc unit tests 2 and 19)."""


# --------------------------------------------------------------------------------------------
# the lag convention
# --------------------------------------------------------------------------------------------
def lag1(a: np.ndarray) -> np.ndarray:
    """Shift a `(n_symbols, T)` score grid one bar forward. Column 0 becomes NaN.

    Bit-identical to `scripts/run_concentrated_short.py:54 lag1` on floating grids, which is
    the convention `hold_book` (`scripts/run_book_single_names.py:112`, `p[:, 1:] =
    mask[:, :-1]`) and `rank_columns` (`scripts/run_mine_neutral.py:244`, "THE LAG IS HERE AND
    NOWHERE ELSE") already hold. Column 0 is NaN *by construction* — there is no prior bar —
    and every selector here maps non-finite to `+inf` so it ranks last.

    Raises on a non-floating dtype and on anything that is not 2-D; see the module docstring
    for the two sentinels the runner writes instead.
    """
    a = np.asarray(a)
    if a.ndim != 2:
        raise ValueError(
            f"lag1 expects a 2-D (n_symbols, T) grid, got shape {a.shape}. The runner's "
            f"version raises IndexError here; this message says which axis is missing."
        )
    if a.dtype.kind != "f":
        raise TypeError(
            f"lag1 expects a floating grid, got dtype {a.dtype}. `np.full_like(a, np.nan)` "
            f"casts the fill to the array's dtype: on int64 column 0 becomes "
            f"{np.iinfo(np.int64).min} (a RuntimeWarning, not an error) and on bool it becomes "
            f"True, which ranks FIRST under the ascending argsort every selector here uses. "
            f"Cast to float before lagging."
        )
    out = np.full_like(a, np.nan)
    out[:, 1:] = a[:, :-1]
    return out


def delayed(score: np.ndarray, bars: int) -> np.ndarray:
    """`bars` extra applications of `lag1` — D290's skip-bar rerun, and the docs' one-bar delay.

    `delayed(s, 0)` is `s` unchanged; `delayed(s, 2)` is `lag1(lag1(s))`. The delay is
    implemented by COMPOSING THE SAME LAG and never by shifting the return grid, per
    `scripts/d290_skip_bar_test.py`'s `skipped(score, n)`. A caller whose selector lags
    internally (`top_n`, `rank_columns`) gets `bars` extra bars on top of that one, which is
    exactly D290's `skip` semantics:

        skip 0   rank on score[t-1], earn from t
        skip 1   rank on score[t-2], earn from t
    """
    if isinstance(bars, bool) or not isinstance(bars, (int, np.integer)):
        raise TypeError(f"bars must be an int, got {type(bars).__name__}")
    if bars < 0:
        raise ValueError(
            f"bars must be >= 0, got {bars}. A negative delay is a look-ahead, which is the "
            f"thing this module exists to refuse."
        )
    out = np.asarray(score)
    for _ in range(int(bars)):
        out = lag1(out)
    return out


def audit_lag_topn(base: np.ndarray, score: np.ndarray, n: int, pos: np.ndarray) -> int:
    """L1. Re-derive the held set from `score[:, t-1]` and assert `pos` matches. Returns bars checked.

    Equal to `scripts/run_overnight_short.py:454 audit_lag` (verbatim copies live at
    `run_unfiltered_ranking.py:93` and `run_descending_ranking.py:134`), and deliberately a
    SECOND implementation rather than a call into `top_n`: *"the point is to disagree with it
    if it is wrong, and a check that shares the code it checks cannot."*

    The `base` guard is the first thing it does. A base whose column 0 is non-zero was not
    produced by `hold_book`, so the whole premise of the audit — that qualification is already
    lagged and only the SELECTION of N from the qualifiers is in question — does not hold.

    THE CALLER'S SELF-TEST MUST USE A TIME-VARYING SCORE. `scripts/run_overnight_long.py:270`
    states the rule: a score constant across columns makes `score[:, t]` and `score[:, t-1]`
    identical and a lagged and an unlagged book then agree by construction, so the audit
    cannot discriminate. The synthetic there is `(arange(n)[:, None] + arange(T)[None, :]) % n`.
    """
    base = np.asarray(base)
    score = np.asarray(score)
    pos = np.asarray(pos)
    if np.any(base[:, 0] != 0.0):
        raise AssertionError("base column 0 is non-zero; hold_book did not lag")
    checked = 0
    for t in range(1, base.shape[1]):
        q = np.flatnonzero(base[:, t] != 0.0)
        if q.size == 0:
            continue
        if q.size <= n:
            want = q
        else:
            s = score[q, t - 1]  # EXPLICITLY the prior bar
            s = np.where(np.isfinite(s), s, np.inf)
            want = q[np.argsort(s, kind="stable")[:n]]
        got = np.flatnonzero(pos[:, t] != 0.0)
        if got.size != want.size or not np.array_equal(np.sort(got), np.sort(want)):
            raise AssertionError(
                f"top{n} bar {t}: held set does not match the rank of score[:, t-1]"
            )
        checked += 1
    return checked


def audit_lag_monthend(
    sign_held: np.ndarray,
    sign_me_pandas: np.ndarray,
    me: Sequence[int],
    live: np.ndarray,
    T: int,
) -> int:
    """The futures generation of the same audit. Returns the number of live held cells.

    Equal to `scripts/run_d555_tsmom_replication.py:424 audit_lag`. The held grid must equal
    the pandas-derived month-end signs shifted to the session AFTER the month-end, rebuilt
    here with a second, independent hold loop — never via the runner's
    `hold_from_month_ends`. `me` is the session index of each month-end; `sign_me_pandas` is
    `(n_roots, len(me))`, derived by a separate pandas month-end membership so that the two
    implementations can disagree.
    """
    sign_held = np.asarray(sign_held)
    sign_me_pandas = np.asarray(sign_me_pandas)
    live = np.asarray(live)
    n = sign_held.shape[0]
    ref = np.zeros((n, T))
    for k in range(len(me)):
        lo = me[k] + 1
        hi = me[k + 1] if k + 1 < len(me) else T - 1
        for t in range(lo, hi + 1):
            ref[:, t] = sign_me_pandas[:, k]
    ref = np.where(live, ref, 0.0)
    bad = np.flatnonzero((ref != sign_held).any(0))
    if bad.size:
        raise AssertionError(
            f"LAG AUDIT: held sign grid differs from the independent derivation on "
            f"{bad.size} sessions (first at index {bad[0]})"
        )
    return int((ref != 0).sum())


def retained_edge(
    edge_fn: Callable[[np.ndarray], float],
    score: np.ndarray,
    delays: Sequence[int] = (0, 1, 2, 3),
) -> dict[int | str, float]:
    """The one-bar-delay rerun: score `edge_fn` on the score grid delayed 0, 1, 2, 3 bars.

    Ledger §13A.8 control 6, unit test 70. Returns each delay's edge keyed by the delay
    itself, plus `"retained_fraction_at_1"` = edge(1) / edge(0).

    **A NUMBER, NEVER A VERDICT.** The docs' line is *"must keep >= 50% of its edge"*; this
    function does not apply it. The floor belongs to the pre-registration that declared it,
    and a helper that returned `passed=True` would be asserting a study's conclusion from
    inside its instrument.

    `retained_fraction_at_1` is **NaN when edge(0) <= 0**, and that is not a failure to
    compute: a ratio to a non-positive baseline is not a retained fraction, and "keeps 80% of
    its edge" said of a losing strategy is a sentence with no content. Sign gates the
    comparison.

    `delays` must be strictly increasing, non-negative and contain both 0 and 1.
    """
    seen = [int(d) for d in delays]
    if len(seen) != len(set(seen)):
        raise ValueError(f"delays must be unique, got {tuple(delays)}")
    if any(b < a for a, b in zip(seen, seen[1:])):
        raise ValueError(f"delays must be increasing, got {tuple(delays)}")
    if any(d < 0 for d in seen):
        raise ValueError(f"delays must be >= 0, got {tuple(delays)}")
    for required in (0, 1):
        if required not in seen:
            raise ValueError(
                f"delays must contain {required}: the retained fraction is edge(1)/edge(0) "
                f"and both legs must be measured, not assumed. Got {tuple(delays)}."
            )

    out: dict[int | str, float] = {}
    for d in seen:
        value = edge_fn(delayed(score, d))
        out[d] = float(value)
    base = out[0]
    out["retained_fraction_at_1"] = (
        float(out[1] / base) if np.isfinite(base) and base > 0.0 else float("nan")
    )
    return out


def expect_raise(
    fn: Callable[[], object],
    what: str,
    log: Callable[[str], None] | None = None,
) -> bool:
    """Assert that `fn()` raises `AssertionError`. Returns True; raises if it did not.

    Promoted from `scripts/stage0_d581_gamma_close.py:39` (and its older sibling
    `scripts/run_d561_trend_sharpenings.py:526 _expect_raise`) because **a self-test that
    cannot fail is worse than none**: every gate here is paired with a deliberately broken
    input that the audit must reject, and the pairing is what makes the passing half mean
    anything.

    Only `AssertionError` is caught, `ForwardIndexError` and `LabelLeakError` among them. A
    `TypeError` from a broken call signature is a bug in the test, not a fired audit, and
    swallowing it would turn a typo into a green light.
    """
    try:
        fn()
    except AssertionError as exc:
        if log is not None:
            log(f"    audit RAISES on {what}: {str(exc)[:70]}")
        return True
    raise AssertionError(f"did NOT raise: {what}")


# --------------------------------------------------------------------------------------------
# the static scan
# --------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class ForwardIndexSite:
    """One syntactic site that reads past the decision bar.

    `line`/`col` locate the offending EXPRESSION (the `t + 1`, not the statement); `snippet`
    is the enclosing subscript or call unparsed, so a reader sees the shape without opening
    the file.
    """

    line: int
    col: int
    snippet: str
    kind: str


#: Subscript receivers whose forward index is reported under its own kind, because a pandas
#: positional accessor reads differently from a numpy grid and the fix is different too.
_PANDAS_ACCESSORS = frozenset({"iloc", "loc", "iat", "at"})

_SNIPPET = 90


def _positive_offset(node: ast.expr) -> int | None:
    """`<Name> + <positive int literal>`, in either order, or None.

    `<Name> + <Name>` is **out of scope and deliberately so**: `x[t + k]` is forward only if
    `k > 0`, and the sign of a name is not a syntactic property. Resolving it would mean
    constant-propagation, which is a different instrument from a tripwire — see D593 for the
    full list of what this scan cannot see.
    """
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Add):
        return None
    for a, b in ((node.left, node.right), (node.right, node.left)):
        if (
            isinstance(a, ast.Name)
            and isinstance(b, ast.Constant)
            and isinstance(b.value, int)
            and not isinstance(b.value, bool)
            and b.value > 0
        ):
            return b.value
    return None


def _is_negative(node: ast.expr) -> bool:
    """A syntactically negative argument: `-1`, `-k`, or a negative literal."""
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return True
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
        and node.value < 0
    )


def _index_elements(node: ast.Subscript) -> list[ast.expr]:
    """The subscript's index expressions, with a tuple subscript (`x[:, t+1]`) flattened."""
    sl = node.slice
    return list(sl.elts) if isinstance(sl, ast.Tuple) else [sl]


def _subscript_sites(node: ast.Subscript) -> list[ForwardIndexSite]:
    accessor = (
        node.value.attr
        if isinstance(node.value, ast.Attribute) and node.value.attr in _PANDAS_ACCESSORS
        else None
    )
    snippet = ast.unparse(node)[:_SNIPPET]
    sites: list[ForwardIndexSite] = []
    for element in _index_elements(node):
        if isinstance(element, ast.Slice):
            # THE LOWER BOUND ONLY. `x[:t+1]` is the standard bar-inclusive window and is
            # correct; `x[t+1:]` starts after the decision bar and is not.
            if element.lower is not None and _positive_offset(element.lower) is not None:
                sites.append(
                    ForwardIndexSite(
                        element.lower.lineno,
                        element.lower.col_offset,
                        snippet,
                        "forward_slice",
                    )
                )
            continue
        if _positive_offset(element) is not None:
            kind = f"forward_{accessor}" if accessor else "forward_index"
            sites.append(ForwardIndexSite(element.lineno, element.col_offset, snippet, kind))
    return sites


def _call_sites(node: ast.Call) -> list[ForwardIndexSite]:
    """`.shift(-k)` and `np.roll(x, -k)`: both move later values into earlier positions."""
    name = node.func.attr if isinstance(node.func, ast.Attribute) else (
        node.func.id if isinstance(node.func, ast.Name) else None
    )
    if name == "shift":
        candidates = [node.args[0]] if node.args else []
        candidates += [kw.value for kw in node.keywords if kw.arg == "periods"]
        kind = "negative_shift"
    elif name == "roll":
        candidates = [node.args[1]] if len(node.args) >= 2 else []
        candidates += [kw.value for kw in node.keywords if kw.arg == "shift"]
        kind = "negative_roll"
    else:
        return []
    snippet = ast.unparse(node)[:_SNIPPET]
    return [
        ForwardIndexSite(node.lineno, node.col_offset, snippet, kind)
        for c in candidates
        if _is_negative(c)
    ]


def forward_index_sites(source: str) -> list[ForwardIndexSite]:
    """Every site in `source` that syntactically reads past the decision bar, in file order.

    Four shapes, and they are the four the deposit docs' leak canary is written in:

      * `forward_index` — `x[t + 1]`, `x[:, t + 1]` (a tuple subscript is flattened first);
      * `forward_slice` — `x[i + 1:]`. The lower bound only: `x[:t + 1]` is the ordinary
        bar-inclusive window and flagging it would have made this scan useless on arrival;
      * `forward_iloc` / `forward_loc` — the same index through a pandas positional accessor,
        reported separately because the fix differs;
      * `negative_shift` / `negative_roll` — `.shift(-1)`, `np.roll(x, -k)`.

    **Backward constructs are not flagged, and that is the load-bearing half.** `lag1`'s
    `out[:, 1:] = a[:, :-1]`, `hold_book`'s `p[:, 1:] = mask[:, :-1]`, `score[q, t - 1]` and
    `df.shift(1)` all pass, which `tests/unit/test_lookahead.py` asserts on the runners' own
    source rather than on a paraphrase of it.
    """
    tree = ast.parse(source)
    sites: list[ForwardIndexSite] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            sites.extend(_subscript_sites(node))
        elif isinstance(node, ast.Call):
            sites.extend(_call_sites(node))
    return sorted(sites, key=lambda s: (s.line, s.col, s.kind))


def _read_source(path_or_source: str | Path) -> tuple[str, str]:
    """(source, origin). A `Path`, or a `str` that is a one-line `.py` path, is read."""
    if isinstance(path_or_source, Path):
        return path_or_source.read_text(encoding="utf-8"), str(path_or_source)
    if "\n" not in path_or_source and path_or_source.endswith(".py"):
        path = Path(path_or_source)
        if not path.exists():
            raise FileNotFoundError(
                f"{path_or_source!r} looks like a path (one line, ends .py) but does not "
                f"exist. Pass a Path, an existing file, or source text."
            )
        return path.read_text(encoding="utf-8"), path_or_source
    return path_or_source, "<source>"


def assert_no_forward_index(path_or_source: str | Path) -> None:
    """Raise `ForwardIndexError` naming the FIRST forward-index site, or return.

    The leak canary of ledger unit test 71 and opening unit test 25: *"a feature built from
    bar t+1 is rejected by the static no-future-data check"*. The first site is named rather
    than all of them, because the contract is rejection — a list of twelve sites and a list of
    one are the same verdict, and the message that matters is where to look first. The count
    is carried in the message so a reader knows whether fixing one is the whole job.
    """
    source, origin = _read_source(path_or_source)
    sites = forward_index_sites(source)
    if not sites:
        return
    first = sites[0]
    raise ForwardIndexError(
        f"{origin}:{first.line}:{first.col} reads past the decision bar "
        f"[{first.kind}]: {first.snippet}"
        + (f"  ({len(sites)} site(s) in total)" if len(sites) > 1 else "")
    )


def labels_never_features(feature_source: str, label_names: Iterable[str]) -> None:
    """Raise `LabelLeakError` if any label identifier appears in feature source.

    `OPENING_AGENT_STATE_PREREG.md` unit test 2 — *"Labels never enter features (static check
    on the feature pipeline)"* — and the same instrument for unit test 19's *"use in-sample
    dates only (static check)"*. That doc's §0 control 6 is what makes it necessary: day-type
    labels *"use the full session and are training targets only, never features."* A label is
    computed from bars after t0 by definition, so a feature that touches one is a look-ahead
    the index scan above cannot see — the forward read happened in the label's own module.

    Three spellings are searched, because a label reaches feature code by all three: a bare
    name (`day_type`), an attribute (`row.day_type`), and a **string constant**
    (`df["day_type"]`), which is how a column is nearly always reached and which a name-only
    scan would miss entirely. A string constant matches only when it is the whole string, so
    a docstring mentioning the label in a sentence does not fire.
    """
    labels = [str(name) for name in label_names]
    if not labels:
        raise ValueError(
            "label_names is empty; a leak check over no labels passes by seeing nothing"
        )
    wanted = set(labels)
    tree = ast.parse(feature_source)
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in wanted:
            hits.append(f"line {node.lineno}: name {node.id}")
        elif isinstance(node, ast.Attribute) and node.attr in wanted:
            hits.append(f"line {node.lineno}: attribute .{node.attr}")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in wanted:
            hits.append(f"line {node.lineno}: string {node.value!r}")
    if hits:
        raise LabelLeakError(
            "label identifier(s) reached the feature pipeline (labels are training targets "
            "only, never features):\n  " + "\n  ".join(sorted(set(hits)))
        )
