# D610 — The flow ledger becomes code, and the routing identity it registers is exact only at its two endpoints

**Status:** Committed
**Date:** 2026-09-22
**Category:** Model
**Source:** The six User-Doc-Deposit pre-registrations.
`SETTLEMENT_FLOW_LEDGER_PREREG.md` v1.9 §4 (lines 143-171, 320-352), §5.1-5.2 (lines
358-384), §7.1/§7.3 (lines 426-445), §8A.2 (lines 489-500), §8A.3 (line 504), §8A.5
(lines 515-520), §3.1 (lines 67-70), §3.3d (line 128) and required unit tests 1, 2, 3, 5, 6,
8, 9, 12, 37, 38, 39, 40, 41, 42, 43, 44 and 47 (lines 707-753). Builds on D604
(`costs/futures_impact.py`, §5.3/§8A.4 and `depth_bar`'s refusal shape), D606
(`validation/fit.py:ols`, and the rule that a pin against a runner COMPILES the function
rather than importing the module), D586 (`scripts/settlement_windows.py`, `W_start`), D48
(raise loudly), D78/D537 (property-test settings), D39 (the hand file precedes the code),
D546 (pytest imports any path you name) and D550 (CRLF pinned before hashing bytes). Reuses
`scripts/fetch_cftc_cot.py:397 release_date_of` as the COT release rule.

## Decision

One new package, `src/backtest_framework/ledger/`, with four modules and an empty
`__init__.py`: `flows.py` (§4's participant terms and §5.1's aggregation), `update.py`
(§5.2's scalar update and §7.1's timing rule), `rolls.py` (P8a and P8b) and `netting.py`
(§8A.2's swap-dealer calibration and the two point-in-time clocks it needs). One script,
`scripts/ledger_selftest.py --selftest`. No existing file is edited. **No fixture is read,
nothing is written under `data/`, no parameter is fitted from data and no strategy return is
computed.** Every input in every test is synthetic or typed from the deposit's own worked
examples.

**There was no ledger code anywhere.** `costs/futures_impact.py` (D604) implements §5.3 and
§8A.4 and is the only prior implementation of any formula in this document;
`scripts/power_table.py`'s string `"A: P1 rebalance"` is a stage LABEL in §9A's planning
table; `engine/strategy.py`'s "Kalman" is a dropped plan and not this update step. So P1,
P2, the routing split, §5.1's aggregation, §5.2's five lines, §7.1's earliest-pass rule,
P8a's two legs, P8b's exclusion, §8A.2's constrained fit and §8A.5's threshold are all first
implementations.

### `flows.py` — §4's terms and §5.1's sums

| | units / contract |
|---|---|
| `held_return(p_held, settle_prev)` | line 146; dimensionless; both prices strictly positive |
| `q1_notional(aum_prev, L, r, f_fut)` | line 156's NUMERATOR, USD — what line 707 calls "notional before contract conversion" |
| `q1_rebalance(..., multiplier, p_held)` | line 156 in full, CONTRACTS of the traded month, signed (+ = buy, line 143) |
| `var_q1(aum_prev, L, f_fut, sigma_remaining, *, multiplier=None, p_held=None)` | line 160; notional² with neither keyword, contracts² with both, **raises on one** |
| `q2_swap(..., n, ...)` | line 165; `n` in [0, 1] **asserted, never clipped** |
| `route(...) -> (Q1, Q2)` | line 709's split; exact at the endpoints, one ulp wide inside |
| `FlowTerm(name, q, var, active=True)`, `aggregate(terms) -> (mu_total, var_total)` | §5.1 lines 361-362, summed with `math.fsum` so the total is order-independent |
| `held_months(holdings, *, default_to_front=False)` | line 718; weights on `abs` holdings summing to 1; `default_to_front=True` **always raises** |
| `large_lot_threshold(trade_sizes_by_day, day, lookback_days=20, *, quantile=0.90)` | line 518; **nearest rank**; raises on a day ≥ `day` and on a short window |
| `is_large(size, l_min)` | line 753's `>=`, as its own function so the tie cannot be lost inline |

### `update.py` — §5.2 and §7.1

| | |
|---|---|
| `trailing_mean_20(series_by_day, day, lookback_days=20)` | `S_norm`, line 371; raises on any day ≥ `day` (required test 8) |
| `s_pre_z(s_pre, s_norm)` | line 368; a DIFFERENCE, not a standardisation, despite the name |
| `kalman_update(mu, var, p, R, z) -> Update(k, q_hat, var_post, q_rem, sigma_rem)` | lines 380-384; `p` in [0, 1], `var >= 0`, `R > 0` with `math.inf` accepted and `R = 0` refused |
| `entry_decision(candidates, *, passes, w_start, entry_minutes) -> str \| None` | lines 430 and 445; returns one t0 or None and holds no state to re-enter from |

### `rolls.py` — P8a and P8b

`RollSchedule(fractions, start_rule, source)` validating that the fractions sum to exactly
1.0 and that a `source` string exists; `UNG_SCHEDULE` carrying line 327 verbatim;
`RollSchedule.for_fund` **raising for every fund but UNG**; `roll_days(near_expiry,
schedule)`; `roll_legs(phi, n_old, L, p_old, p_new) -> (sell_old, buy_new)`;
`validate_roll(holdings_changes, schedule, *, tol=0.02) -> RollValidation(passes,
fallback_to_p8b, max_abs_deviation, reason)`; `q8b(roll_flag, roll_fraction, beta8, *, fund,
p8a_funds)` returning **exactly `0.0`** for a fund in `p8a_funds`.

### `netting.py` — §8A.2 and the two clocks

`fit_lambda(d_sd, d_sx) -> LambdaFit(lam, se, clipped, lam_unconstrained)`, least squares
through the origin via `validation/fit.py:ols` and projected onto [0, 1];
`consistency_flag(n_hat, se_n, lam, se_lam) -> bool` (line 499);
`FundExposure` / `swap_exposure_predictor(funds)` (line 495);
`cot_usable_from(report_date) -> date` (line 128, required test 41);
`swap_record_time(execution_ts, dissemination_ts)` (line 504, required test 44).

## What the ledger's algebra actually is, and why it is built before any data

§4 through §8A.5 is a **model with no free parameters in its arithmetic**. Every fitted
quantity — `p`, `R`, `n`, `n9`, `h0`, `h1`, `a0..a3`, `b1..b4`, `beta8` — is an ARGUMENT
here, estimated in §8's walk-forward windows by a study that does not exist. What is left is
closed form: a leveraged fund's required rebalance is `AUM L(L-1) r f_fut` divided by the
contract size, its swap-routed twin is the same expression with `(1 - f_fut)(1 - n)`, the
observation folds in through four lines of scalar Kalman algebra, a roll is two legs scaled
by a published fraction, and the netting calibration is one slope through the origin.

That is why **the tests are hand calculations**. There is no fixture to check the arithmetic
against, and there will not be one until Track 2's recorder (D608) has run for months; the
only ground truth available today is a pen. `tests/golden/test_ledger_flows_ledger.hand.txt`
was **written and saved to the working tree before `src/backtest_framework/ledger/` existed
as a directory**, and it carries seven worked cases with the reason each number is exactly
representable in binary64 beside it. Two numbers in this record's tests came out of that
file differing from what the implementation produces, and **both were resolved in favour of
the hand file's statement rather than by editing the hand file** — see "Two places the hand
file and the code disagree" below.

## The exactness claims, and the one that had to be measured before it could be written

**Required unit test 6 is exact on four of its five outputs**, and the golden asserts them
with `==`:

    K = 0.5 x 400 / (0.25 x 400 + 100) = 200 / 200 = 1.0
    Q_hat = 100 + 1.0 x (60 - 0.5 x 100)            = 110.0
    sigma^2_post = (1 - 1.0 x 0.5) x 400            = 200.0
    Q_rem = 0.5 x 110                               = 55.0
    sigma_rem = 0.5 x sqrt(200) = 5 sqrt(2)         = 7.0710678118654752...

Every operand on the path is a binary fraction or a small integer (0.5 is `2^-1`, 0.5 × 0.5
is 0.25, 0.25 × 400 is 100), and a quotient of two equal finite doubles is 1.0 by IEEE-754
rather than by luck. The fifth is irrational and is asserted to 12 places. The golden also
pins the two halves of `K` separately, because an implementation with `(1 - K p)` the wrong
way up would still produce 200 on this particular case.

**`R = math.inf` gives `K == 0.0` exactly**, so line 711's *"with R → ∞, K → 0"* is an
equality here and not a limit: a finite double divided by infinity is a zero. `R = 0` is
refused, because a measurement asserted to have no noise is not something §8 can estimate
and at `p = 0` it makes `K` a `0/0` nan.

**Required unit test 1 is exact only in the document's own left-to-right order, and that is
a measurement.** 0.05 is not a binary fraction. At L = −2:

    1e9 * 6 * 0.05    == 300000000.0            <- the document's order, and its number
    1e9 * (6 * 0.05)  == 300000000.00000006     <- the two small factors grouped first

The L = +2 case is exact under both groupings, so a golden that tested only the long fund
would not have found this. `q1_notional` associates left to right as line 156 writes it, and
`tests/golden/test_ledger_flows_ledger.py` re-runs the comparison rather than quoting it.

## The routing identity is exact at its two endpoints and one ulp wide everywhere else

Required unit test 3 (line 709) says *"`f_fut = 0` routes all rebalance to P2; `f_fut = 1`
routes all to P1"*. Both endpoints are exact, because a product with a 1.0 factor is lossless
and a product with a 0.0 factor is a zero. **Their sum in the interior is not.** `Q1 + Q2` at
`n = 0` is `total × f + total × (1 − f)`, and that is not `total × 1` for every `f`.

This is inherent in the pre-registration, not in the implementation: line 156 and line 165
are **two independent products**, and a `route` that computed `Q2 = (total − Q1)(1 − n)`
would conserve exactly and would no longer be line 165. So `route` computes each half from
its own quoted formula, the tests assert the endpoints with `==`, and the interior is
asserted to a **one-ulp bound** with the count of inexact points pinned so that a change
widening it fails rather than passing quietly.

Measured on the golden's numbers (`AUM = 1e9`, `L = +2`, `r = 0.05`, multiplier 10,000,
`P_held = 3.00`, so `total = 3333.3333333333335` and one ulp is `4.547473508864641e-13`),
over `f = 0.01 ... 0.99`:

| spelling | inexact points of 99 | worst gap |
|---|---:|---|
| `total * f + total * (1 - f)` (the hand file's) | **26** | 1 ulp |
| `route`'s own — numerator, then one division per leg | **51** | 1 ulp |

Both are bounded by the same single ulp and both are in the golden.

## The two interpretation choices, stated as choices

**1. "Two weeks before the near month's expiration" is read as 14 CALENDAR days.** The
alternative — ten BUSINESS days before expiry, four consecutive business days — is equally
consistent with line 327 and gives different dates whenever a weekend or a US holiday falls
in the window. Calendar days won for three reasons: "two weeks" is a calendar phrase and is
what an SEC filing's plain language means; computing business days needs an exchange
calendar and **this record reads no fixture at all**; and a weekday approximation would be
silently wrong on every Thanksgiving and Good Friday while looking right.

**The choice matters less than it appears, because line 327 itself says what resolves it**:
*"The issuer publishes a CSV of anticipated roll dates, subject to change."* `roll_days` is a
RECONSTRUCTION, line 340 sends a reconstruction that disagrees with recorded holdings to
P8b, and `validate_roll` is the check that does it. The docstring says so at the point of
use, and `tests/unit/test_ledger_rolls.py` asserts the unadjusted weekend case explicitly —
`roll_days(2026-03-27)` returns a Friday, a Saturday, a Sunday and a Monday — so the
ambiguity is visible in a test rather than buried in a comment.

**2. The COT release rule is "the Friday of the report's week", and it is this repository's
own.** `scripts/fetch_cftc_cot.py:397 release_date_of` computes it and its header measured
why it is not a flat +3 days: the survey day shifts on holidays, and **2007-01-03 is a
Wednesday because 2007-01-02 was the National Day of Mourning for President Ford**, so +3
would put that release on a Saturday. A report dated on a Friday pushes to the FOLLOWING
Friday (four such dates survive after 1993), because a report cannot be published before it
is surveyed and erring late is the only safe direction for a conditioning variable.

The alternative — inventing a rule here, or a flat lag — was rejected because two
implementations of one convention drifting apart is this repository's most repeated defect.
`netting.py` reimplements the five lines rather than importing them, since `src/` may never
import `scripts/`, and **`tests/unit/test_ledger_netting.py` pins the two against each other
on 12,419 consecutive report dates from 1993-01-01 to 2026-12-31** by compiling that one
function out of the runner's committed bytes (D606's rule: a one-shot runner's module body
is written to do work, not to be imported).

The one divergence is in SHAPE, not in rule: before 1993-01-01 the fetcher returns `""` and
`cot_usable_from` **raises**, because a function that must return a date cannot represent
"we do not know" any other way. The deposit's sample starts in 2016 (§3.3), so it cannot
bite a study that stays inside it, and a study that strays is told.

## Two other decisions worth their own line

**`var_q1` refuses half a unit conversion, because the document's own units do not
reconcile.** Line 160 writes `(AUM x L(L-1) x f_fut)^2 x sigma^2_remaining` — notional
squared, with no contract conversion — while line 156's `Q1` is in contracts. §5.1 then sums
`Q_i` into `mu_total` and `var_Q_i` into `sigma^2_total`, and §5.2's `K` divides one by the
other. **The two must be in consistent units before they meet and the document does not say
which.** `var_q1` returns line 160 verbatim with neither `multiplier` nor `p_held`, returns
contracts-squared with both, and **raises on exactly one**, so the convention is a visible
decision at the call site rather than a library's guess. This is flagged, not resolved: it
is the pre-registration's call.

**`aggregate` sums with `math.fsum`.** §5.1 says *"Σ active Q_i"* and says nothing about an
order; a naive loop makes the ledger's total depend on the order participants happened to be
declared in, so two studies that enabled the same stages in a different sequence would print
different last bits and neither would be wrong. `math.fsum` is correctly rounded and
therefore permutation invariant, and a property test asserts that over reversals and
rotations.

## Two places the hand file and the code disagree, and how each was settled

1. **The interior routing count.** The hand file states 26 of 99 on the spelling it wrote,
   `total × f + total × (1 − f)`. The module's spelling is line 156's — one fraction, so the
   numerator is formed and divided once per leg — and it is inexact at 51. **The hand file
   was not edited.** The golden asserts both numbers, computing the hand file's expression
   inline so its claim stays checked, and the comment says why they differ. A `.hand.txt`
   edited to match the implementation is no longer ground truth.
2. **`held_return(3.30, 3.00)`.** Neither operand is a binary fraction and subtracting 1
   cancels the leading bits, so the result is `0.09999999999999987`, not 0.1 and not the
   `0.10000000000000009` a first guess produces. The unit test pins the double the formula
   actually yields, with a comment saying that a test written as `== 0.1` would be asserting
   a number this expression cannot produce.

## What is NOT built

- **No estimation of `p`, `n`, `n9`, `R`, `h0`, `h1`, `a0..a3`, `b1..b4` or `beta8`.** Those
  are §8, fitted in §10's walk-forward windows against realised in-window flow, and §9B's
  parameter-recovery and decision-relevance procedures for `p`, `h`, `n` and `n9` are a
  study rather than a library function.
- **No creation model (P3/P4), no iNAV or premium (§3.3b, P3.1-P3.6), no attention detector
  (P3.7), no TAS proxy (P5/P6), no P9 restrike logic (§3.1b) and no impact.** Impact is
  D604's `costs/futures_impact.py`; the rest belong to other records. `ledger/__init__.py`
  is empty so that a sibling agent's modules can land in the same package without a merge.
- **No trading rule beyond the two timing constraints.** §7.2's criteria, §7.4's exit ladder
  and §7.6's sizing are not here.
- **No data, of any kind.** Not a fixture, not a fetch, not a file under `data/`. The one
  committed file any test reads is `data/settlement_windows.csv`, through D586's loader, and
  only to avoid typing `14:28:00` into a test.

## What was measured

| | |
|---|---|
| `1e9 * 6 * 0.05` vs `1e9 * (6 * 0.05)` | `300000000.0` vs `300000000.00000006` — the document's association is the exact one |
| required unit test 6 | `K`, `Q_hat`, `sigma^2_post`, `Q_rem` all exact; `sigma_rem = 5 sqrt(2)` is the only irrational |
| `K` at `R = math.inf` | **exactly 0.0**, and `q_hat == mu`, `var_post == var` with `==` |
| the routing identity, `f = 0.01 ... 0.99` | 51 of 99 inexact in the module's spelling, 26 of 99 in the hand file's, **1 ulp in both** |
| `L_min` on 20 days × sizes 1..10 | nearest rank `ceil(0.9 × 200) = 180` → **9.0**, with 40 of 200 trades at or above it — the fat atom line 753's tie clause exists for |
| `fit_lambda` on the hand case | `lam_unconstrained = 16/8 = 2.0` and `se = sqrt(0.5/8) = 0.25`, both exact; clipped to 1.0 |
| `cot_usable_from` vs `fetch_cftc_cot.release_date_of` | **agree on 12,418 consecutive dates**, 1993-01-01 to 2026-12-31; the runner's function compiled, not imported |
| tests added | **42** — unit 25, golden 8, property 9; 1.13 s together |
| guards | 12 refusals and 4 boundary equalities proved in `--selftest`, 27 checks, 0.01 s |

Test counts by file: `tests/unit/test_ledger_flows.py` 8, `tests/unit/test_ledger_update.py`
6, `tests/unit/test_ledger_rolls.py` 6, `tests/unit/test_ledger_netting.py` 5,
`tests/golden/test_ledger_flows_ledger.py` 8, `tests/property/test_ledger_flows_property.py`
9 — **42 test functions**, of which 17 carry a numbered deposit claim.

## Disagreements and what is NOT resolved

1. **The brief asked for `route` to carry "a proof that Q1+Q2 at n=0 equals the unrouted
   total". It does not, in the interior, and the document is why.** Recorded above with the
   measured counts. What is proved is the endpoint identity line 709 actually claims, plus a
   one-ulp bound.
2. **`var_q1`'s unit inconsistency is flagged, not fixed.** The pre-registration writes line
   156 and line 160 in different units and §5.1 sums them. A library cannot decide which one
   §5.2 meant; the function makes the caller say.
3. **`fit_lambda` reports the UNCONSTRAINED slope's standard error, and at a binding boundary
   that is not the constrained estimator's SE.** The constrained estimator has an atom at the
   boundary and no ordinary standard error describes it; line 498 wants the SE as an
   *informative prior* and line 499 puts it inside a two-SE band, so the unconstrained SE is
   the one that says how much the data pins the slope. Reporting zero — a point mass's exact
   variance — would make the consistency check fire on everything. `clipped` travels beside
   it so a reader always sees which case they are in.
4. **The percentile convention in §8A.5 is chosen, not given.** Nearest rank, because line
   753's *"trades exactly at L_min count as large"* is a claim about a real trade and linear
   interpolation returns a size no trade had. A study using numpy's default will get a
   different `L_min` and must say so.
5. **`validate_roll`'s tolerance is declared and arbitrary.** Line 340 says holdings changes
   must "match the computed φ" and does not say how closely. 0.02 absolute admits rounding in
   a published holdings file and refuses a schedule wrong by a whole day. It is an argument.
6. **Required unit test 10 (line 716, "an entry that would complete less than 3 min before
   W_start is rejected") is implemented by `entry_decision` and asserted in
   `tests/unit/test_ledger_update.py`, but is NOT claimed** in the crosswalk, because this
   record's claim list was fixed in advance. It is available for a later claim on the
   existing test.
7. **`entry_decision` takes `w_start` as an argument and never looks it up.** `src/` may not
   import `scripts/` (`tests/unit/test_import_boundaries.py`), and the window table is
   `data/settlement_windows.csv` served by `scripts/settlement_windows.py:147 window_for`
   (D586), which raises rather than defaulting. The tests pull NG's `14:28:00` from that
   loader, which is also what a runner must do.
8. **Nothing here has an opinion on whether the ledger predicts anything.** H1 through H15
   are a study. This record is the arithmetic those hypotheses will be computed with, and it
   makes no claim about their outcome.

## CHANGELOG bullet (draft, for the integrator)

- **D610 — the settlement flow ledger's algebra, built before any data, checked by hand.**
  A new `src/backtest_framework/ledger/` package (`__init__.py` empty): `flows.py` (§4's P1
  and P2 with the `f_fut`/`n` routing, §5.1's `fsum` aggregation, line 718's held-month
  mapping that **has no front-month default**, and §8A.5's nearest-rank `L_min` refusing a
  same-day trade in D604 `depth_bar`'s shape), `update.py` (§5.2's five lines,
  `S_norm`'s trailing window refusing day t, and §7.1's earliest-pass rule under §7.3's
  three-minute constraint, taking `W_start` as an argument because `src/` may not import
  `scripts/`), `rolls.py` (P8a's two legs on `sign(L)`, UNG's four-day 25% schedule carrying
  line 327 verbatim with **`for_fund` raising for every other fund — line 328, "Do not
  assume"**, line 340's holdings validation with its P8b fallback as a FIELD, and P8b
  returning **exactly 0.0** for a fund already in P8a) and `netting.py` (§8A.2's slope
  through the origin via D606's pinned `ols`, **projected onto [0, 1] because for one
  parameter with no intercept the projection IS the constrained argmin**, line 499's
  consistency flag, line 495's predictor **raising on any futures-held term**, and the COT
  and swap-dissemination clocks). Measured and recorded: line 156 is exact in binary64 only
  in the document's own left-to-right order (`1e9*6*0.05` is 3e8; `1e9*(6*0.05)` is
  `300000000.00000006`); required unit test 6 is exact on four of its five outputs and
  `K == 0.0` exactly at `R = inf`; **the P1/P2 routing identity is exact only at the two
  endpoints line 709 names and one ulp wide inside** (51 of 99 interior points in the
  module's spelling, 26 in the hand file's); `cot_usable_from` agrees with
  `fetch_cftc_cot.py:397` on 12,418 consecutive dates. Two interpretation choices are stated
  as choices with their alternatives: "two weeks" as 14 calendar days, and the COT Friday
  rule. 42 tests (golden 8 with hand arithmetic written before the package existed, unit 25,
  property 9) plus `scripts/ledger_selftest.py --selftest`, 27 checks proving 12 guards fire
  and 4 boundary equalities hold. Ledger required unit tests 1, 2, 3, 5, 6, 8, 9, 12, 37, 38,
  39, 40, 41, 42, 43, 44, 47. No strategy return computed; no fixture read; nothing written
  under `data/`.

## Numbered deposit tests claimed

`SETTLEMENT_FLOW_LEDGER_PREREG.md` §12. One function name each; the crosswalk
(`scripts/deposit_test_map.py --scan`) finds them by the number in the function name.

| # | line | function |
|---|---|---|
| 1 | 707 | `tests/golden/test_ledger_flows_ledger.py::test_ledger_1_q1_notional_at_l_plus_two_and_minus_two` |
| 2 | 708 | `tests/unit/test_ledger_flows.py::test_ledger_2_l_plus_one_funds_contribute_zero_rebalance_flow` |
| 3 | 709 | `tests/unit/test_ledger_flows.py::test_ledger_3_f_fut_routes_wholly_to_p1_or_to_p2` |
| 5 | 711 | `tests/unit/test_ledger_update.py::test_ledger_5_p_zero_leaves_the_prior_alone_and_infinite_R_kills_the_gain` |
| 6 | 712 | `tests/golden/test_ledger_flows_ledger.py::test_ledger_6_update_step_on_the_documents_own_numbers` |
| 8 | 714 | `tests/unit/test_ledger_update.py::test_ledger_8_s_norm_excludes_the_evaluation_day_and_everything_after_it` |
| 9 | 715 | `tests/unit/test_ledger_update.py::test_ledger_9_earliest_pass_signals_at_the_first_passing_t0_and_never_re_enters` |
| 12 | 718 | `tests/unit/test_ledger_flows.py::test_ledger_12_flow_lands_on_the_held_months_never_the_front` |
| 37 | 743 | `tests/unit/test_ledger_rolls.py::test_ledger_37_ung_rolls_four_days_at_25_percent_from_two_weeks_before_expiry` |
| 38 | 744 | `tests/golden/test_ledger_flows_ledger.py::test_ledger_38_roll_legs_sign_and_the_price_scaling` |
| 39 | 745 | `tests/unit/test_ledger_rolls.py::test_ledger_39_holdings_at_25_percent_a_day_pass_and_one_big_day_falls_back_to_p8b` |
| 40 | 746 | `tests/unit/test_ledger_rolls.py::test_ledger_40_a_fund_counted_in_p8a_contributes_exactly_zero_to_p8b` |
| 41 | 747 | `tests/unit/test_ledger_netting.py::test_ledger_41_a_cot_week_is_usable_only_from_its_friday_release` |
| 42 | 748 | `tests/golden/test_ledger_flows_ledger.py::test_ledger_42_lambda_is_projected_onto_the_unit_interval_and_the_flag_fires` |
| 43 | 749 | `tests/unit/test_ledger_netting.py::test_ledger_43_the_swap_predictor_never_sees_futures_held_exposure` |
| 44 | 750 | `tests/unit/test_ledger_netting.py::test_ledger_44_swap_records_are_keyed_on_dissemination_not_execution` |
| 47 | 753 | `tests/unit/test_ledger_flows.py::test_ledger_47_large_lot_threshold_is_prior_days_only_and_ties_count_as_large` |

**No `docs/data-available.md` paragraph:** nothing under `data/` is created, changed or read
for content by this record.
