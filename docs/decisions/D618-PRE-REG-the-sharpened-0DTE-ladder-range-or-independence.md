# D618 PRE-REGISTRATION — the sharpened 0DTE ladder: range or independence, and the claim that it cannot have both

*Committed before the runner exists (R8). In-sample window, every look disclosed. No return on any
session from 2024-01-01 on is scored here.*

## 0. Why this exists, and what changed between the request and this document

[D614](D614-STAGE-0-RESULT-not-pinning-ten-sessions-carry-the-whole-pull.md) closed the first version of
this line: the **volume**-weighted centroid of same-day-expiring ES option strikes, signed distance from
the 15:30 price, carried **−5.078 bp per sigma** on the 15:30 → 16:00 return — *repulsion* where the
mechanism predicts attraction — at Newey–West t −2.109, with 78.7 % of the slope's numerator from ten
sessions and **81 % from three COVID-crash afternoons**. Verdict: real but not tradeable, the line
closes, and the reading beside it was **not pinning**.

The principal asked on 2026-09-22 for all six sharpenings that record's §7 names, with the staging:
five measured in sample, the aggressor improvement built as a fixture only, the weight scored unsigned
as primary and signed as a named diagnostic.

**A stress test then measured the sharpened objects on the in-sample window before any of this was
pre-registered, and four of the six do not survive contact with their own arithmetic.** Those
measurements are disclosed in §6 as looks. **All six are still built and measured** — that is what was
asked, and the measurement is the deliverable — but they change this document's primary question, and the
change is stated here rather than discovered later:

> The question is no longer *"does the sharpened conditioner order the close?"* It is **"can a signed
> distance from the price to a weighted strike have both range and independence from the day's own
> move?"** — because the measurements say the two are traded off against each other with no interior
> solution, and if that holds it explains D614 retroactively and closes the axis rather than one
> construction.

## 1. The hypothesis, in the runner's own quantities

Near expiry, dealer hedging of a concentrated option position pulls the underlying toward the strikes
carrying that position (long gamma) or pushes it away (short gamma). If so, a conditioner built from
**position** — not turnover — should order the close, and the coefficient should be positive
(attraction) on the unsigned magnitude form.

For that claim to be **identified** at all, the conditioner must satisfy two conditions that have nothing
to do with the outcome. It must carry dispersion that the strike grid alone does not supply, and it must
**not be a restatement of the day's own move**, because the close continuing the day's move is D463's
intraday momentum and is already in the ledger. §3 makes both conditions pre-registered screens applied
before any return is read. Whether a conditioner that is identified is also **worth trading** is a
separate question with a separate bar, in §7, and §3 explains why the two must not be merged.

## 2. The family, fully enumerated, and the primary chosen on mechanism

Per eligible session, over same-day PM-expiring strikes only (`expiry_hhmm >= "15:30"`, which keeps the
four 2016 17:00 expiries and drops the AM-settled quarterly), the object is

```
LADDER(cell) = ( weighted centroid of the cell's strikes  -  P1530 ) / sigma_window
```

| axis | levels |
|---|---|
| weight | `abs(gamma) x abs(delta_oi)` · `abs(delta_oi)` · `abs(gamma)` · `abs(gamma) x oi` · `vol_to_1530` (D614's, the known comparator) |
| band | unrestricted · 3 ladder steps · 2 steps · 1 step |
| window | 15:30 → 16:00 (**primary**) · 15:50 → 16:00 |
| gamma anchor | evaluated at P1530 · evaluated at the **prior settle** |

`delta_oi(K) = oi(t, K) − oi(t−1, K)`, from `fut_es_options_eod.csv.gz`, whose `oi` is the prior close's
open interest published before 10:00 ET (D581 gate G2) — so the difference is known long before 15:30
and is not look-ahead. **[D616](D616-FIXTURE-the-open-interest-reference-session.md) added the column
that makes the difference checkable**: `oi_ref_session`, the business date the number describes. A pair
enters only where the two reference sessions are adjacent; the rest are dropped and counted.

**Declared priority order, fixed now.** The cell scored against returns is the **first** one in this
list that passes every screen in §3:

1. `abs(gamma) x abs(delta_oi)`, unrestricted, 15:30 → 16:00, gamma at P1530
2. `abs(delta_oi)`, unrestricted, 15:30 → 16:00
3. `abs(gamma) x abs(delta_oi)`, 3 steps, 15:30 → 16:00, gamma at P1530
4. `abs(delta_oi)`, 3 steps, 15:30 → 16:00
5. `abs(gamma) x oi`, unrestricted, 15:30 → 16:00, gamma at P1530
6. `abs(gamma)`, unrestricted, 15:30 → 16:00, gamma at P1530

The order is by mechanism — position before turnover, unrestricted before a band that throws strikes
away — and **not** by any in-sample t. If no cell in the whole family passes, **nothing is scored against
returns** and the verdict is that the object is degenerate.

## 3. The screens, with their thresholds declared here

Applied to every cell in the family **before any outcome is read**. This is the part of the study that a
spent window cannot corrupt, because it is about the conditioner alone.

```
S1a MEASUREMENT floor  sd(LADDER) >= 0.20                in sigma units of the scored window
S1b placebo floor      sd(LADDER) >= 3 x sd(LADDER of the same cell with FLAT weights)
S2  confound ceiling   abs(corr(LADDER, DAY0)) <= 0.40    DAY0 = the 09:30 -> 15:30 move; D614 section 4's own form
S3  grid ceiling       R2(LADDER on (P1530 mod step)/step) <= 0.25
S4  support floor      median strike count inside the band >= 5
```

**S1 is a measurement condition, not an economic one, and the distinction is load-bearing.** The
temptation is to set the dispersion floor from the cost — and doing that arithmetic honestly shows why it
cannot be done. D614's repulsion arm made **+$2.49 gross a session at sd(LADDER) = 3.07σ** and needed
**1.71×** that to cover the $4.25 round trip. If gross scales with dispersion at a fixed coefficient,
then clearing cost at D614's coefficient would take sd ≈ **5.2σ** — *more* dispersion than the closed
construction had, and more than any cell in this family can have. So **no dispersion floor can stand in
for an economic bar**: a cell must beat D614's coefficient, not merely match its range, and that cannot be
known before the outcome is read. The economic burden therefore stays in §7, on dollars per trade computed
by the runner after the coefficient exists.

What S1 does instead is exclude cells whose dispersion is so small that the conditioner is numerically
indistinguishable from the strike grid it is built on — a cell at sd 0.04σ (the measured kernel-only
placebo) is arithmetic, not information. The absolute floor is set at **0.20σ**, deliberately *below* the
0.238σ the stress test measured for `abs(gamma) x abs(delta_oi)`, so that improvement 1's and 2's cells
are **scored against returns rather than screened out on a threshold chosen after seeing them**. S1b is
the self-calibrating half: whatever a cell's scale, it must carry three times the dispersion its own flat-
weight placebo carries, or the weights are not doing the work.

S3 and S4 exclude construction defects rather than economics: a band of ±5 points is a median of **2**
strikes and **60 %** grid sawtooth, and a two-strike centroid is not a centroid.

A cell failing a screen is **reported with its numbers** — the screens are the study's main output — and
not scored against returns.

## 4. The predictions, checkable, written before the run

1. **No cell has both range and independence.** Every cell whose dispersion exceeds **1.0σ** has
   |corr(LADDER, DAY0)| **above 0.40**, and every cell under 0.40 has dispersion **below 0.30σ**. The
   stress test measured the gamma-weighted centroid at sd 0.144σ with corr +0.002, the pre-session-
   anchored version at sd 3.037σ with corr **−0.546**, and D614's volume centroid at 3.07σ and −0.49.
   Falsified by any cell with sd ≥ 1.0 **and** |corr| ≤ 0.40 — which is the single number this study is
   really about.
2. **`abs(gamma) x abs(delta_oi)` passes S1 and is scored** (predicted sd ≈ 0.24σ, corr ≈ +0.035), and its
   coefficient's implied dollars per trade come out **below the $4.25 round trip** — the cell is
   measurable and uneconomic, which is a different verdict from D614's and must not be reported as the
   same one.
3. **Every band of 2 steps or fewer fails S3 or S4** (predicted grid R² ≈ 0.60 and median 2 strikes at
   ±5 points).
4. **The Δ-OI conditioner is not independent of the two conditioners already measured** — predicted
   corr +0.66 with the OI centroid, +0.33 with the volume centroid. §5's gate decides what follows.
5. If any cell is scored, **the coefficient is positive** (attraction). D614's was negative.

## 5. The Δ-OI gate, named, because this is the one improvement that touches a real defect

Open-interest change is position rather than turnover, which is exactly what D614 §7 said was missing.
Two facts make it a weaker instrument than it looks, and both are stated before the run:

- a 0DTE contract opened on session *t* expires at 16:00 on *t* and **never reaches a close, so it never
  appears in any open-interest print**. `delta_oi` therefore measures session *t−1*'s inventory build,
  not same-day positioning. D581 measured that same-day expiries are only **7–8.5 %** of carried
  |gamma × oi| even in 2023.
- D614 already measured the **level** of the OI-weighted centroid: **+0.024, t +0.35, rank 0.338** —
  nothing. And the Δ centroid correlates **+0.659** with it.

**The gate.** Where a Δ-OI cell is scored, the primary coefficient is on Δ-OI **residualised against both
the OI-weighted centroid and the volume-weighted centroid on the same strike set** (Frisch–Waugh),
reported as the residualised coefficient with its incremental R², and it must clear its null **on the
residual alone**. If the coefficient lives in the shared part, the record says **"volume in disguise"**
and stops. Second leg: Σ|delta_oi| on the 0DTE ladder against that session's own 0DTE traded volume from
D613's panel — if the position change is a small fraction of the turnover, the conditioner is not
measuring expiry-day flow, and that number is reported whatever it says.

## 6. Improvements 5 and 6, and what they are allowed to conclude

**5 — the aggressor side: a fixture, and no verdict.** The side exists only in the `tbbo` year, inside
the reserved slice, so [D617](D617-FIXTURE-the-ES-option-signed-flow-census-from-the-tbbo-year.md) builds
it as a **non-return census** on the principal's instruction, in D510/D511's shape, and the slice stays
unspent for returns. Two things are settled there and neither is a signal: the unsigned (`N`) share of
ES option contracts is **0.0003** on the profiled file, and D485's at-quote agreement is **1.0000**.
Nothing signed is scored against a return in this record. The power arithmetic is written down so the
census cannot be promoted later: ~250 sessions with robust standard errors 4.4× the OLS ones on this
panel puts D614's own effect size at **|t| ≈ 1**. A signed arm on that window is a pilot, not a test.
And the flag signs the *trade*, not the *customer* — makers aggress to hedge — so the residual
assumption is named rather than treated as removed.

**6 — the straddle: the P&L is a non-executable diagnostic; the pin-efficiency ratio carries the
weight.** A short straddle at the centroid strike pays exactly −|S_settle − K*|, which is the quantity
the hypothesis claims is small, so the reference must be the **official settlement** from
`fut_settle_strip.csv.gz`, never the 16:00 minute close. Five reasons it is not a candidate, listed
before it is computed: no option quotes exist before 2025-09 so the spread must be assumed (what
CLAUDE.md forbids after D285's guessed 15 bp against a measured 33.8); a leg finishing ITM
auto-exercises into an ES futures position that exists after 16:00, breaking P2's flatten rule; one ES
option is **$50 a point and indivisible**, so P1 sizing is infeasible rather than merely penalised, and
against a ~4-point credit the measured |10-minute move| has p99 23.8 and max 74.5 points — p99 loss
≈ $950, max ≈ $3,455, which fails P4 by inspection; and no prop firm that permits automation offers
options at all (P6). **The statistic that carries weight is the pin-efficiency ratio**: realised
|S_settle − K*| divided by the market's own 15:50 straddle price at K*, which needs no spread
assumption and tests the mechanism the P&L only gestures at. It is scored against its own placement
null over random strikes.

Also recorded: improvement 6 as originally worded swaps the hypothesis to **variance suppression**, and
D614 §4 already measured that on the one form that cleared both confound guards: **+0.067 against a
standard error of 0.164**.

**The looks this document discloses.** The stress test's measurements are new in-sample looks on a window
D614 §7 declares spent: the dispersion and DAY0-correlation of six candidate conditioners, the grid R²
and strike counts of two bands, the 10- versus 30-minute variance ratio, the Δ-OI coverage and revision
structure, and the straddle's coverage. Two of them are incidental **outcome** correlations and are named
as such: gamma×OI against R2 = **+0.095**, and the ±0 near-money band against R10 ≈ **0.01**. The screens
in §3 and the priority order in §2 were chosen after those looks, which is why the order is by mechanism
and the thresholds are tied to cost rather than to any measured t.

## 7. Nulls, bars and multiplicity

**Nulls.** For any scored cell: D614's **norm-preserving Frisch–Waugh shift null** (the amended one — the
plain rotation of a correlated regressor is anti-conservative, spread 0.298 against a fitted 0.586,
because rolling destroys the collinearity), the **sign-flip null** at 2,000 draws under seed 618, and
week-block and year-block bootstrap standard errors. Enumerated where the group is finite.

**The family-maximum null.** max|t| over every cell that passes the screens, compared against the max|t|
of **the same family recomputed on each null draw** (D228/D288's empirical best-of-N floor). Both bars
must clear: the primary against its own null, and the family max against the family-max null.

The family's size, enumerated rather than multiplied out carelessly: the anchor axis exists only for the
three gamma-bearing weights, so the weight-anchor combinations are 3 × 2 + 2 = **8**, and the family is
8 × 4 bands × 2 windows = **64 cells**. The weights are heavily correlated (gamma×OI and gamma×ΔOI at
**+0.750**), so the effective count is smaller than the nominal one, and the empirical null is what
prices that rather than any correction formula.

**Bars.** The statistical bar is D614's, two-sided with both tails scored and the sign recorded.

**The economic bar is restated in a scale-free unit, because D614's was not.** That one was
pre-registered as 15 bp per sigma of a conditioner whose dispersion turned out **3.07** where about 0.3
had been assumed, which made the threshold meaningless. This one is declared in two forms, both computed
by the runner: **dollars per trade at one MES against the $4.25 round trip** (a cell must return ≥ $4.25
gross per trade at the observed mean |LADDER| to be worth a second look), and **basis points of expected
move at the observed mean |LADDER|**, reported beside the breakeven of 1.21 bp per side.

**The tail bar.** The coefficient excluding the ten largest-|LADDER| sessions must keep its sign and at
least half its magnitude. D614's would have failed this: **−1.19 against −5.08**.

**The estimator ladder** (OLS, HC0, HC3, NW(5), NW(10), week-block) and the tail diagnostics naming the
top contributing sessions with their bars are reported for **every** cell, passing or not, because those
are what exposed D614.

## 8. The audits, each with the break that hits the exact scalar the assertion reads

Every one proven to raise in `--selftest`, and repeated on real data inside `--run`.

| audit | break that must fire it |
|---|---|
| **Δ-OI spans one session** — every pair's two `oi_ref_session` values are adjacent ES sessions, and every `oi` was published before 10:00 ET | shift `oi_ref_session` by one session on 1 % of rows; and replace the check with `ref == ref` and assert the meta-test fires |
| **zero-delta share** inside a band declared from the measured 0.428 median, raising above a ceiling | set every delta to zero (a source dropout) |
| **D526 sentinel** — no used row has `oi == 0` on *t* with `oi_prev > 0` while the strike traded | inject such rows above the declared ceiling |
| **the gamma reduction** reproduced scalar-by-scalar by `b76_gamma_hand` on ≥4 seeded sessions to 1e-9 | divide by the count instead of the weight sum; **permute the gamma vector within the session** (same multiset, wrong strikes) and assert the scalar moves — D581's `audit_f1` checks a *total* and is permutation-invariant, so it cannot catch this; negate d1 |
| **the anchor is the intended one** — the P1530 and prior-settle objects differ beyond a declared threshold | evaluate at the prior settle and assert the right-quantity audit fires (measured sd 0.57σ vs 3.04σ, corr −0.043) |
| **`WEIGHTS BITE`, restated against the PRICE** — raise if median &#124;K_w − P1530&#124; falls below a declared floor in points. D614 compared to the *grid* centroid, which passes trivially for a gamma kernel while the object is degenerate | the gamma-weighted cell as specified, whose measured median distance is ~1.3 points against a 5-point step: **this audit is expected to fire on improvement 1, which is why it exists** |
| **the band is not endogenous** — the selected strike set is identical computed at 09:00 and at 15:30 | anchor the band at P1530 and assert S2's guard fires |
| **window additivity** — `r(15:30→16:00) == r(15:30→15:50) + r(15:50→16:00)` to 1e-12 under D462's endpoint convention | use `close["15:50"]` (off by one minute) and assert additivity raises; assert the strict bar counts 20 and 10; assert sd(r10)/sd(r30) equals the measured 0.659 within tolerance |
| **column mapping by name** — every coefficient extracted by name, never position | read `beta[2]` positionally and assert the audit fires (D614's W1, the reviewer's find) |
| **not singular** — no cell has two columns that are one variable | pass a control equal to the target and assert it raises (D614's placebo cell, whose null p95 reached 6.4e13 before this existed) |
| **kernel-only placebo** — gamma with flat weights (measured sd 0.039σ) must fail its own bar, with `PIN` as its control partner so the singularity guard stays satisfied | give the placebo the real weights and assert it stops failing |
| **grid-only placebo** — D614's, which cleared the *rank* bar at 0.987 with no information in it, so it is scored against the robust t as well | — |
| **sign in money** — a synthetic panel where dealers are short gamma at a known strike and the close is pulled to it | negate the customer-side convention and assert the predicted sign flips (D581's `audit_sign_in_money(flip=True)`) |
| **the straddle's reference** — the expiry intrinsic uses the official settlement | substitute P1600 and assert the P&L moves beyond a declared threshold |
| **declared outputs** — `REQUIRED_OUTPUTS` present in the artifact | drop a block and assert the guard raises |

## 9. Declared outputs

`data/stage0_d618_sharpened_ladder.json`, carrying: the screen table for all 64 cells (sd, corr with
DAY0, grid R², median strike count, pass/fail per screen); the priority order and which cell if any was
scored; for every scored cell the coefficient by name, the estimator ladder, both nulls with p50 and
p95 and the p95's bootstrap SE, the tail diagnostics with the top sessions named and their bars, the
terciles by distance, the era split, the economic bar in dollars and in bp, and the tail bar; the Δ-OI
gate's residualised coefficient and incremental R² and the Σ|Δoi|-to-turnover ratio; the pin-efficiency
ratio with its placement null; the straddle diagnostic with its five infeasibility reasons attached; and
**the component line whatever the verdict** — net Sharpe *and* Sortino at one MES at the cost that size
pays, gross beside net, exposure, hit rate, payoff, maxDD, skew, and the correlation with the admitted
MACD day-session arm, all computed inside the runner (R17 and `COMPONENTS_PROP.md`).

## 10. Disposition, declared in advance

- **Prediction 1 holds — no cell has both sd ≥ 1.0σ and |corr(DAY0)| ≤ 0.40** → the axis of *signed
  distance to a weighted strike* closes for ES 0DTE, whatever the scored cells' coefficients say, because
  the object cannot be both informative and identified. That is the finding this study exists to produce,
  it is a property of the construction rather than of a return, and it retro-explains D614's every
  symptom. Nothing on this axis is pre-registered again without a fixture that changes the arithmetic.
- **Prediction 1 is falsified** → there is a cell worth a forward read, and the line reopens on the
  principal's word. This is the outcome the record would most like to be wrong about.
- **No cell passes the screens at all** → the family is degenerate; no return is scored and no slice is
  spent.
- **A cell passes the screens and fails the statistical bar** → the construction is measured and does not
  order the close; the line stays closed.
- **A cell passes both bars in sample** → it becomes a **candidate for a forward read on the principal's
  word (R15)**, never a result, because this window is spent. The component line is entered in
  `COMPONENTS_PROP.md` on its own standard.
- **The economic bar fails while the statistical bar passes** → recorded as real and not tradeable, as
  D614 was, and the reason named (cost, or range).

The honest prior, stated before the run: **~4 %** that a single sharpened primary would clear both bars
on a reserved slice. The reserved slice lies entirely inside the post-2022-05 era where D614's
coefficient is −0.16; the mechanically sensible bands read nothing; the variance leg is null; and the
only conditioner whose range survives non-circular construction is the day's own move.

*Runner: `scripts/stage0_d618_sharpened_ladder.py`, written after this file is committed.*
