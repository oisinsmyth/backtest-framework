# D606 — The error budget becomes code, and the zero-contribution term's delta is exactly zero because the column is DROPPED, not fitted at zero

**Status:** Committed
**Date:** 2026-09-21
**Category:** Testing
**Source:** The six User-Doc-Deposit pre-registrations.
`SETTLEMENT_FLOW_LEDGER_PREREG.md` §8A.1 "Error budget" (lines 478-487), deposit decision
D28 (line 1014) and unit tests 48-49 (lines 754-755);
`INDEX_REWEIGHT_FLOW_PREREG.md` §5A.1 (lines 156-159) and unit tests 19-20 (lines 367-368);
`OPENING_AGENT_STATE_PREREG.md` §7.3 "Parameter budget" (lines 155-158), §1 line 21, the
retention rule (lines 176-178) and unit test 13 (line 348). Builds on D593 (`Fold`,
`leave_one_year_out`, `purged`, `assert_partition`), D588 (`power.py`'s
render-validates-first shape), D592 (`programme.py`'s `results/` path mapping), D22/D28/D85
(`walk_forward.py`), D48 (raise loudly), D78/D537 (property-test settings), D550 (newline
pinning) and R16 (exact reproduction). Sits beside `research/cointegration.py` without
touching it.

## Decision

Two new library modules, `src/backtest_framework/validation/fit.py` and
`src/backtest_framework/validation/error_budget.py`. `validation/__init__.py` stays empty.
No existing file is edited, no script is touched, no fixture is read, and no strategy
return is computed.

### `fit.py` — least squares, log loss, the parameter budget, the retention rule

| | units / contract |
|---|---|
| `OLSFit(coef, resid, se_ols, se_nw, n, k, nw_lag)` | frozen, `eq=False`; `coef[j]` is units of `y` per unit of column `j`; nothing annualised or in bp |
| `ols(y, X, *, nw_lag=0, intercept=False) -> OLSFit` | **bit-identical to `scripts/run_d365_momentum_buffer.py:762 ols`**; raises on `n <= k`, on any non-finite entry, on `nw_lag >= n`, and on a rank-deficient design **naming the column** |
| `rolling_ols(y, x, window)` | **bit-identical to `scripts/prescreen_cross_sectional.py:147 rolling_ols`**, returning `(alpha, beta, resid_sd, n)`; `resid_sd` is ddof = 2 |
| `multiclass_log_loss(p, y, *, eps=None) -> float` | mean `-log p[y]`, dimensionless; rows must sum to 1 within 1e-12; a zero probability on the realised class **raises** unless `eps` is given |
| `FeatureBudget(non_base_classes=3, ceiling=36)` | `.max_features == 11`, `.parameters(F) == non_base_classes * (F + 1)`, `.assert_within(F)` raising `FeatureBudgetError` |
| `retention_check(logloss_prev, logloss_new, dv_prev, dv_new, *, rel=0.02) -> RetentionResult(kept, rel_reduction, dv_not_reduced, reason)` | both clauses reported whichever one decided |

### `error_budget.py` — the budget, its page, and the stage-order gate

| | units / contract |
|---|---|
| `Term(name, predict)` | frozen; `predict(X) -> (n,)` is the term's design column, in the study's own units |
| `ols_fitter(terms, *, nw_lag=0) -> (fit_fn, predict_fn)` | the reference fitter; **drops an exactly-zero training column** |
| `oos_error(folds, X, y, fit_fn, predict_fn, active) -> OOSError(mse, n, per_fold)` | `mse` is POOLED, `sum(sse) / sum(n)`, in squared units of `y`; the test index never enters the fit |
| `FoldError(label, n, sse)` | `sse` squared units of `y`; `.mse` is a property, never a stored field |
| `leave_one_term_out(folds, X, y, fit_fn, predict_fn, terms) -> list[TermContribution]` | `delta_mse = mse_without - mse_full`, ranked DESCENDING, rank 1-based |
| `ErrorBudgetRow`, `_ERROR_BUDGET_REQUIRED`, `validate_error_budget(rows)` | raises naming the first offending row and field; **empty input fails** |
| `write_error_budget_md(rows, path, *, study, stage, date=None) -> Path` | validates before writing a byte; ASCII, LF, deterministic |
| `error_budget_page_path(study) -> Path` | `docs/results/<STUDY>_ERROR_BUDGET.md` |
| `StageOrder(registered, decision_log_path)`, `ReorderEntry`, `StageOrderError` | `.next(planned_order, *, completed=(), today=None) -> str`; `.effective_order(as_of)`; `.entries()` |

### The three things that are decisions and not implementation

**1. The zero-contribution term's column is DROPPED from the design; it is not fitted at
zero. That is the only way unit 48 is an equality.** Ledger 48 and index 19 say *"changes
OOS MSE by zero"* and *"leaves OOS error unchanged"*, and this module asserts
`delta_mse == 0.0` — not `abs(delta) < eps`. A zero column left in the design makes the
least-squares problem rank deficient, and the surviving coefficients of a rank-deficient
solve are not a bitwise function of which zero columns are present: they move in the last
places, the predictions move with them, and the measured delta comes out near 1e-17 instead
of at 0. `ols_fitter` therefore builds the full design and the reduced design from the same
non-zero columns, so the two are **the same matrix byte for byte** and the delta is the same
double minus itself. `fit.ols` refuses a rank-deficient design outright, which is the other
half of the same decision: a fitter that kept the column raises rather than returning a
delta of 1e-17. The exactness claim is stated precisely — *a term whose column is exactly
zero on every TRAINING block* — and a term zero on train but non-zero on test qualifies too,
because the fitted model never carried it. That boundary has its own test.

**2. `ols` solves by the normal equations and uses `np.linalg.lstsq` only as a rank oracle.**
The brief for this work asked for an `lstsq` solve AND for `==` equality with D365's
`inv(X'X)` solve, and **measured, those two are incompatible.** On a 60x3 Gaussian design
with an intercept column the two solves differ by up to **4.4e-16**; on the six-row design
of the golden, whose exact answer is the integer pair `(4, 3)`, `lstsq` returns
`0x1.7ffffffffffffp+1` = 2.9999999999999996 for the second coefficient. D365's numbers are
what this programme has published, and "Exactness, not tolerance" outranks a preference for
one LAPACK driver over another, so the solve is D365's — asserted `==` by `tobytes()` on
arbitrary synthetic designs and every `nw_lag` in `{0, 1, 5, 12}`, not on one lucky design —
and `lstsq` supplies the **rank and the singular values**, which is what naming a
linearly dependent column requires and which `np.linalg.inv` cannot give. The measurement is
re-run in `tests/unit/test_fit.py` rather than quoted from here: the test asserts that the
two solves agree well inside any usable tolerance **and are not the same doubles**, so the
fact stays checked rather than remembered.

**3. The sign convention is stated because §8A.1 does not fix it.**
`delta_mse = mse_without - mse_full`; positive means removing the term made the
out-of-sample forecast worse, and *"ranking terms by attributable error"* is read as that
quantity, descending. The phrase admits the opposite reading — the error a badly-modelled
term leaves behind — and nothing in either document disambiguates it. The module says which
it computes, in the docstring and on the rendered page, rather than leaving a reader to
infer it from a table.

### Where the page lives, and why none is committed

The deposit names `results/<study>/ERROR_BUDGET.md` and there is no root `results/` tree
here. Same mapping `validation/programme.py:21-26` recorded for `PROGRAMME_REGISTRY.md`, and
the same reason `power.py:write_power_md` gave for declining to invent one:

    results/settlement_flow/ERROR_BUDGET.md -> docs/results/SETTLEMENT_FLOW_ERROR_BUDGET.md
    results/index_reweight/ERROR_BUDGET.md  -> docs/results/INDEX_REWEIGHT_ERROR_BUDGET.md

**No page is committed by D606, because no study has run** and a rendered page with no study
behind it is a claim about nothing. A test asserts that `docs/results/` holds no
`*_ERROR_BUDGET.md`, so committing one later is a deliberate act with a red test in front of
it.

### The stage-order gate refuses four different things, in cause order

Ledger 49 / index 20 is *"the code refuses to run a reordered stage unless a matching
decision-log entry exists"*, and a single check would have hidden three other failures
behind that one message. `StageOrder.next` refuses, in this order:

1. **any stage outside `registered`, before the log is read at all** — deposit D28, *"No new,
   unregistered stage can be added this way"*. No log entry can smuggle one in, because the
   log is not consulted;
2. a `planned_order` that is not a permutation of `registered` (dropping a stage is a
   different pre-registration, not a reordering);
3. a reordering that moves a stage in `completed` — §8A.1 permits reordering *"among
   not-yet-run stages"* only;
4. a `planned_order` that is not the order in force today, naming the missing entry — **and
   saying so specifically when a matching entry exists but is dated AFTER the run date**,
   which is the exact failure the *"logged before the next stage runs"* clause was written
   against and which a generic "no entry" message would misdiagnose.

The log is a JSON-lines **chain**: each entry's `from_order` must equal the order in force
when it was written, `before_stage` must be the first position at which `from_order` and
`to_order` differ (checked, not trusted), dates must not go backwards, and a missing log
file is an empty log — which **fails closed**, so a mistyped path refuses every reordering
rather than permitting one.

## Rationale

**The deposit's §8A.1 is a governance clause with an arithmetic core, and only the
arithmetic is obvious.** The leave-one-term-out MSE difference is four lines. What actually
needed building is the part that makes the clause enforceable rather than decorative: that
the order a stage runs in is checked against a dated log before the stage runs, that an
unregistered stage cannot arrive through it, and that the page which ranks the terms cannot
be written from a table that does not add up. R6's lesson is exactly this shape — *"a hurdle
that exists only in prose is worse than no hurdle: it manufactures confidence nobody
earned"* — and §8A.1's "logged before the next stage runs" is prose until something reads
the dates.

**There was no OLS, ridge, logit, log-loss or budget helper anywhere in `src/`.** The three
fitters that exist are a runner function, a pre-screen function and two Engle-Granger
`lstsq` calls, and sklearn and statsmodels are not dependencies of this project. The choice
was to pin to what exists or to add a dependency; pinning is what R16 asks for, and it has
already paid: writing the equality forced the `lstsq`-versus-normal-equations measurement in
item 2 above, which a fresh implementation would have silently gotten wrong in the last
bits and nobody would have noticed until two records disagreed on a fourteenth decimal.

**`validate_error_budget` checks the table, not only the rows, because the defects that
happen here are cross-row.** The per-field loop is `power.py:578`'s shape, cause before
symptom — a row with no observation count has no MSE, so naming its missing rank would send
a reader to the wrong end of the pipeline. Beyond that it refuses: a `delta_mse` that no
longer equals `mse_without - mse_full` (a hand-edited row), rows disagreeing on `mse_full`,
`n_oos` or `n_folds` (two runs pasted into one table), a duplicated term, ranks that are not
a permutation of `1..n`, and a rank column that no longer orders the deltas. Each has its
own message. The page renderer validates before writing a byte, and a test asserts that an
invalid table leaves no partial file behind.

**`retention_check` reports both clauses whichever one decided, and the golden's case (c) is
why.** A stage whose log loss improved by 12.5% — six times the 2% bar — and whose decision
value fell is refused on clause 2. A bare "not kept" reads as a log-loss failure, and the
two clauses have opposite fixes: clause 1 says the features add nothing, clause 2 says they
add something the decision cannot use.

**A clipped log loss hides a broken model behind a merely bad number.** `-log(0)` is `+inf`;
a library that silently clipped it would return a large finite loss, which reads as "a bad
model" when what actually happened is that the model called the observed outcome impossible
— a mislabelled class, a softmax that underflowed, a broken fit. Those need different fixes
and clipping makes them indistinguishable in exactly the place the retention rule reads. The
`eps` argument exists so that a caller who means to clip says so at the call site, where the
record can see it.

## What was measured

| | |
|---|---|
| `fit.ols` vs `run_d365_momentum_buffer.ols` | `coef`, `se_ols`, `se_nw` **byte-identical** on 22 comparisons: 5 seeds x 4 `nw_lag` values in `{0, 1, 5, 12}`, plus a 200-row case and the intercept-convention case |
| `fit.rolling_ols` vs `prescreen_cross_sectional.rolling_ols` | all four outputs **byte-identical**, including the NaN warm-up |
| `np.linalg.lstsq` vs the normal equations | **not** byte-identical: up to 4.4e-16 on a 60x3 Gaussian design; `0x1.7ffffffffffffp+1` where the exact answer is 3 |
| the golden's pooled OOS MSE | 66 / 12 = **5.5**, exactly; leave-one-out 114 / 12 = **9.5** and 138 / 12 = **11.5**, exactly |
| the zero term's delta | **exactly 0.0**, on the golden and on 40 hypothesis-drawn designs |
| the property file's runtime | 66 s -> **1.5 s** after one change: `tmp_path_factory.mktemp` per example created 40 directories per test, and the filesystem rather than the arithmetic was the cost. One session-scoped `scratch` fixture |
| importing d365 to pin against it | **poisons the whole test process**, and it was caught only by running the suite together. See below |
| tests added | 98 (golden 19, unit 67, property 12); 96 `raise` sites across 1,447 lines of new library code |

### The reuse pins COMPILE the runner functions; they do not import the runners, and that is a correction

D593 pinned four runner functions by importing their modules with
`importlib.util.spec_from_file_location`, and I followed it. **That is wrong for
`run_d365_momentum_buffer.py` and the failure is process-wide.** Its line 133 calls
`sys.addaudithook` at module level to install a default-deny holdout guard, and **CPython
has no `removeaudithook`** — the runner's own comment says so. Importing it inside the test
process refuses, for the remaining life of that process, every `open()` of a path containing
"holdout"; it also mutates `sys.path`, installs `memo_load` and loads four more runners.

Measured: with `tests/unit/test_fit.py` importing d365, running it beside
`tests/unit/test_nothing_outside_tests_is_collectable.py` made that gate fail with
`RuntimeError: [HOLDOUT-GUARD] refused to open scripts\run_holdout_test.py`, because the
gate imports every collectable script to check it. **Both files passed alone**, which is the
worst shape a test defect has — it appears only in the full run and it looks like somebody
else's.

`_function_from_runner` now parses the runner's source and compiles **only the `FunctionDef`
it needs**, into a namespace holding `numpy` and nothing else, raising if the name is
missing or defined twice. The pin is not weaker: it is still the runner's own committed
bytes (read as bytes with CRLF normalised first, D550), an edit to `ols` still moves this
test, and no module-level statement runs. The same treatment is given to
`prescreen_cross_sectional`'s `_prefix` and `rolling_ols`.

**This generalises past D606:** any future pin against a `scripts/` runner should compile
the function rather than import the module, because a one-shot runner's module body is
written to do work, not to be imported.

The golden's design was chosen so that **everything is exactly representable**: the two
fitted columns are orthogonal with `X'X = diag(4, 4)` per block, so the inverse is
`diag(0.25, 0.25)` exactly and every coefficient is a quarter of an integer; and every sum
of squares is divisible by 3, so dividing by the pooled 12 is exact. Two quantities are not,
and the `.hand.txt` names both where they appear: the per-fold means 28/6 and 38/6, which
are not asserted at all (the per-fold sums of squares and counts are, and they are
integers), and the multiclass log loss `4 ln(2) / 3`, which is irrational and is asserted to
12 places.

## Disagreements and what is NOT resolved

1. **The brief asked for an `lstsq` solve and for `==` equality with D365. Those are
   incompatible and the equality won.** Recorded in full in item 2 above, with the measured
   hex. A reader who wants the SVD solve has `np.linalg.lstsq` and now also has the number
   that says what it costs.
2. **"Ranking terms by attributable error" is ambiguous in both documents and this module
   picks a reading.** `delta_mse` descending. If the deposit meant the other reading — the
   error a badly-modelled term leaves behind — the ranking inverts and the module's
   docstring is the place that would have to change. Flagged rather than resolved, because
   it is the pre-registration's call and not a library's.
3. **`OLSFit` carries no rank or condition number.** The rank check raises and the fit then
   proceeds, so a caller cannot read how close to singular a design was. The seven fields
   are the ones the brief pinned; adding an eighth is a later decision.
4. **Term-level counterpart checks (§8A.1 item 2) are carried as a STRING and printed, not
   computed.** *"Predicted creations vs realised dShares"*, *"predicted swap-routed exposure
   vs the COT-implied change"* and *"predicted roll flow vs holdings changes"* each need a
   data source and a study. The column exists so that the page has somewhere to put them.
5. **Nothing here has an opinion on whether a study is worth running.** `retention_check`
   returns `kept` because lines 176-178 define it, and nothing else in these two modules
   returns a verdict — the same line D593's `retained_edge` drew.
6. **The page carries no MDE or power column, and D588's `power.py` is deliberately not
   called from it.** `delta_mse` is a difference of two pooled mean squared errors over
   overlapping fits; it has no per-term standard error that leave-one-term-out produces, so
   an SE column would have to be invented. A power statement about an error budget needs a
   variance for the delta — a paired bootstrap over folds is the obvious route and is not
   registered by either deposit document. `POWER.md` and `ERROR_BUDGET.md` stay separate
   pages until something computes that variance.
7. **`oos_error` takes `Fold`s, not `walk_forward_windows`.** The stronger structural guard
   — a `DataView` built from the training slice, so a test bar is unreachable rather than
   merely unused — is the wrong shape for annual folds, exactly as D593 found. The property
   is carried by `Fold`'s construction-time overlap refusal plus a re-check inside
   `oos_error`; the mechanism carrying it is weaker, and the module docstring says so.

## CHANGELOG bullet (draft, for the integrator)

- **D606 — the error budget, the fitting helpers it needs, and the parameter budget.** Two
  library modules: `validation/fit.py` (`OLSFit`/`ols` **bit-identical to
  `run_d365_momentum_buffer.py:762`** across 5 seeds x 4 Newey-West lags and the intercept
  convention, raising on `n <= k`, non-finite input and rank deficiency *naming the column*;
  `rolling_ols` **bit-identical to `prescreen_cross_sectional.py:147`** including the NaN
  warm-up; `multiclass_log_loss` refusing to clip a zero probability on the realised class
  unless asked; `FeatureBudget` giving 11 features from §7.3's `3 x (features + 1) <= 36`;
  `retention_check` reporting both clauses whichever decided) and
  `validation/error_budget.py` (`Term`, `ols_fitter`, `oos_error` on D593's `Fold`s pooling
  `sum(sse)/sum(n)`,
  `leave_one_term_out` ranked by `delta_mse` descending, `ErrorBudgetRow` /
  `validate_error_budget` / `write_error_budget_md` validating before a byte is written, and
  `StageOrder` refusing a reordered stage without a dated, chained decision-log entry —
  ledger 48/49, index 19/20, opening 13). **A zero-contribution term's delta is exactly 0.0
  because the column is DROPPED from the design rather than fitted at zero**, which makes
  the full and reduced designs the same matrix byte for byte; `ols` refuses a rank-deficient
  design outright, which is the other half of it. Measured and recorded: `np.linalg.lstsq`
  is NOT bit-identical to D365's normal equations (up to 4.4e-16; `0x1.7ffffffffffffp+1`
  where the exact answer is 3), so the solve is D365's and `lstsq` is the rank oracle. The
  deposit's `results/<study>/ERROR_BUDGET.md` maps to
  `docs/results/<STUDY>_ERROR_BUDGET.md`; **no page is committed, because no study has
  run**, and a test pins that. 98 tests (golden 19 with hand-worked exact arithmetic — the
  pooled MSE is 66/12 = 5.5 exactly — unit 67, property 12). No strategy return computed; no
  fixture read.
