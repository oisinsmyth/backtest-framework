# D593 — The deposit's look-ahead controls become code: the runners' lag, a one-bar-delay rerun, a syntactic leak scan, and year folds — and the scan is a tripwire, not a proof

**Status:** Committed
**Date:** 2026-09-21
**Category:** Testing
**Source:** The six User-Doc-Deposit pre-registrations. `SETTLEMENT_FLOW_LEDGER_PREREG.md`
§13A.8 control 6 (one-bar-delay robustness, leak canary; unit tests 70-71),
`OPENING_AGENT_STATE_PREREG.md` §12A control 6, §11 and unit tests 2, 19 and 25, and
`INDEX_REWEIGHT_FLOW_PREREG.md` §0.7, §10 and unit test 9. Extends D32 (`DataView`), D279/R9
(the lag), D290 (the skip-bar rerun), D555 (the futures lag audit) and D588's module shape;
sits beside `validation/walk_forward.py` (D22/D28/D85) without touching it.

## Decision

Two new library modules, `src/backtest_framework/validation/lookahead.py` and
`src/backtest_framework/validation/folds.py`, plus a leak canary under `tests/unit/`.

**`lookahead.py`** — the lag convention, the delay rerun, and the scan:

| | |
|---|---|
| `lag1(a)` | **Bit-identical to `scripts/run_concentrated_short.py:54`** on floating grids |
| `delayed(score, bars)` | `bars` extra applications of `lag1`; bit-identical to `scripts/d290_skip_bar_test.py:79 skipped` |
| `audit_lag_topn(base, score, n, pos) -> int` | Equal to `scripts/run_overnight_short.py:454 audit_lag` |
| `audit_lag_monthend(sign_held, sign_me_pandas, me, live, T) -> int` | Equal to `scripts/run_d555_tsmom_replication.py:424 audit_lag` |
| `retained_edge(edge_fn, score, delays=(0,1,2,3))` | `{delay: edge, "retained_fraction_at_1": float}` |
| `expect_raise(fn, what, log=None) -> bool` | Promoted from `scripts/stage0_d581_gamma_close.py:39` |
| `forward_index_sites(source) -> list[ForwardIndexSite]` | The `ast` scan |
| `assert_no_forward_index(path_or_source)` | Raises `ForwardIndexError` naming the first site |
| `labels_never_features(feature_source, label_names)` | Raises `LabelLeakError` |

**`folds.py`** — `Fold(train_idx, test_idx, label)`, `year_blocks(dates)`,
`leave_one_year_out(dates, *, min_days=200)`, `purged(folds, dates, embargo_days)`,
`era_folds(dates, eras)`, `assert_partition(folds, n)`.

All four runner functions import in about a second by
`importlib.util.spec_from_file_location` and read no fixture at import, so **nothing is
copied**: the equality is asserted against the runners themselves, and none of them is
edited. `validation/__init__.py` stays empty.

### The one deliberate divergence from the runner, and it is a guard

The runner's `lag1` is `np.full_like(a, np.nan)` followed by `out[:, 1:] = a[:, :-1]`, and
`np.full_like` casts the fill to the array's dtype. **Measured, not argued** (numpy 2.4.6,
and `tests/unit/test_lookahead.py` measures it rather than quoting this record):

* on an `int64` grid, column 0 becomes `-9223372036854775808`, with a `RuntimeWarning` and no
  error — a finite number where a "no prior bar" sentinel belongs;
* on a `bool` grid it becomes `True`, which under the ascending `np.argsort` every selector
  here uses ranks column 0 **first**, not last.

`lag1` below raises `TypeError` on any non-floating dtype and `ValueError` on a non-2-D
input. Float grids are bit-identical, tested by `tobytes()` rather than `allclose`.

### `retained_edge` reports a number and never a verdict

The docs' line is *"must keep >= 50% of its edge."* This function does not apply it: the
floor belongs to the pre-registration that declared it, and a helper returning `passed=True`
would assert a study's conclusion from inside its instrument. `retained_fraction_at_1` is
**NaN when the undelayed edge is not positive** — a ratio to a non-positive baseline is not a
retained fraction, and "keeps 80% of its edge" said of a losing construction has no content.

### Purging is per contiguous run, and both ends

`purged` removes the closed calendar interval `[lo - embargo_days, hi + embargo_days]` from
TRAIN around **each contiguous run** of test indices, never around the fold's global span.
Test indices are never removed. On the golden's two-block fold the difference is 10 retained
training sessions against 3: purging the global span is not an embargo but a different
experiment. Both ends, per D555 — a signal with a lookback of L bars is read by the sessions
after a held-out block and reads the sessions before it, so purging one end leaves the other
leaking.

## Rationale

**"The pipeline's static checks must reject it" named a thing that did not exist.** Look-ahead
was enforced here in exactly two places, neither of them a scan of feature code: structurally
on the framework path, by `engine/dataview.py`, where a `DataView` is CONSTRUCTED holding only
the visible bars so there is nothing for an index to reach (D32/D56); and by hand, in runner
audits that re-derive the held set from `score[:, t-1]` in a second implementation. The
600-plus one-shot runners in `scripts/` hold raw `(n_symbols, T)` numpy grids and get
neither — the exact count belongs to `scripts/build_readme_counts.py` and is not restated
here. A
syntactic scan over feature SOURCE is the third instrument, and it is the only one that can
run before a study does.

**Leave-one-year-out existed nowhere.** `validation/walk_forward.py` cuts bar-counted,
contiguous, gapless windows — the strongest guard in the repository and the wrong shape for an
annual event: with about ten January events, no rolling 252/63 window holds a given year out.
D555's `ERAS` is a three-way split that is **reporting only**; it partitions the output and
never the fit, and an era table computed from a model fitted on all three eras is a
description, not a validation.

**Equality is asserted against the runners, not against a paraphrase.** R16's discipline
applied to code: the four functions are loaded by path and compared, so a future edit to
either side reddens rather than drifting. `top_n`'s docstring records what the convention
cost — `corr(hist_L[t], ret[t]) = +0.0737` against `-0.0103` lagged, `top25` at **+2.250
Sharpe unlagged and -0.638 lagged** — and that is the number a second, differently-written
lag would put back at risk.

**The audits are proved able to fire.** `scripts/run_overnight_long.py:270-276` states the
rule that gives the lag audit its teeth — the synthetic score MUST vary with time, or a
lagged and an unlagged book agree by construction — and
`test_a_constant_score_makes_the_audit_blind` is that rule as a measurement: under a constant
score the audit **accepts** an unlagged book, and under `(arange(n)[:,None] +
arange(T)[None,:]) % n` it raises on the same book. Three mutations were run against the
finished suite and all three were caught: flagging a slice's UPPER bound (6 tests), purging
only the trailing side (5 tests), and ranking on `score[:, t]` (3 tests).

## Consequences

### What the scan catches

`forward_index_sites` walks the AST and reports four shapes: `forward_index` (`x[t + 1]`,
`x[1 + t]`, `x[:, t + 1]` — a tuple subscript is flattened first), `forward_slice`
(`x[i + 1:]`, **lower bound only**), `forward_iloc` / `forward_loc` (the same index through a
pandas positional accessor), and `negative_shift` / `negative_roll` (`.shift(-1)`,
`.shift(periods=-3)`, `np.roll(x, -k)`). The canary module is rejected; `lag1`'s own source,
`top_n`'s, `hold_book`'s, `audit_lag`'s and `skipped`'s are not. `x[:t + 1]` — the ordinary
bar-inclusive window — is not flagged, and that is load-bearing: a scan that reddened on it
would have been switched off within a day.

### WHAT THE SCAN CANNOT SEE

Stated here rather than discovered later. Each of the following **is** a look-ahead and each
returns zero sites; `test_the_scan_cannot_see` asserts them as passing cases so they cannot be
quietly forgotten.

1. **Aliasing.** `k = t + 1` on one line and `x[k]` on the next. The offset is syntactically
   gone by the time the subscript is written. Catching it needs constant propagation, which is
   a different instrument.
2. **Helper indirection.** `def nxt(i): return i + 1` and then `x[nxt(t)]`. The scan sees
   calls, not what they return. This is the same blind spot
   `tests/unit/test_nothing_outside_tests_is_collectable.py` records for its own import-time
   scan — a fetch behind a local helper is invisible — and it is inherent to a syntactic tool.
3. **Negative-stride slices.** `x[::-1][t]` reverses the view, so position `t` is the END of
   the series. Nothing about the expression is an addition.
4. **DataFrame `.loc` with a computed label.** `df.loc[label_for(t)]` reads whatever that
   function returns. The near-miss `df.loc[dates[t + 1]]` **is** caught, but only because the
   `t + 1` happens to be written inside a subscript.
5. **`<Name> + <Name>`, deliberately out of scope.** `x[t + k]` is forward only if `k > 0`,
   and the sign of a name is not a syntactic property. Flagging every name-plus-name index
   would flag most correct code.
6. **A name holding a negative.** `k = -1` then `df.shift(k)`.
7. **Anything not in source form**: a leak inside a compiled dependency, a cached derived
   array built by a different script, or a fixture already contaminated upstream.

**So the scan is a tripwire on the shapes that have actually bitten, not a proof of
point-in-time correctness.** The structural guarantee remains `DataView`'s and the empirical
one remains the runner audits'; `assert_no_forward_index` is the cheap third check that can run
on a feature module before any data is loaded. Ledger unit test 71 is satisfied by it — the
canary IS rejected — and the ledger's conclusion, *"if it isn't caught, all results are
invalid"*, must not be read in reverse.

### Tests, and one count this record does not touch

`tests/unit/test_lookahead.py` (66), `tests/unit/test_folds.py` (25),
`tests/golden/test_folds_ledger.py` (20, with hand arithmetic in `test_folds_ledger.hand.txt`
worked on a calendar that never imported this codebase) and
`tests/property/test_lookahead_property.py` (12, D78/D537 conventions) — **123 tests, 5.9 s**.
The canary lives at `tests/unit/_leaky_canary_module.py`: `pyproject.toml`'s
`python_files = ["test_*.py"]` (D546) means pytest never collects it, and
`test_nothing_outside_tests_is_collectable.py` scans only paths outside `tests/`, so it is
neither collected nor forbidden. It is a real file rather than a string constant so that a
linter, a type checker and a human reader all see it as code — a canary written as a string is
one nobody would notice had stopped being leaky.

**The tier counts in `docs/VERIFICATION.md`, `README.md` and the other living documents are
NOT updated by this record.** `scripts/build_readme_counts.py:124` counts `git ls-files`, so
nothing moves until these files are staged; `tests/unit/test_quoted_counts_are_current.py`
will redden on the golden, unit and property tiers at that moment and the quoted counts must
be refreshed in the same commit.

### Not done here

`validation/walk_forward.py`, `scripts/ragged_panel.py` and every runner are untouched, and
no runner yet calls these functions. Wiring `assert_no_forward_index` into a study's entry
point, and `leave_one_year_out` into the index-reweight fit, are separate decisions with their
own pre-registrations. No strategy return was computed and no fixture was read.
