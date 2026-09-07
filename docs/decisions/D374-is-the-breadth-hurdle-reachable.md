# D374 — is the breadth hurdle reachable? Calibrating H4 against its own nulls

**Date:** 2026-09-07
**Kind:** **METHODOLOGY.** This study admits nothing to either book, tests no strategy, and reads no
holdout. Its only product is a verdict on **a hurdle**: keep it, replace it, or retire it.
**Pre-registered under R8 — committed before the runner exists. The result will be committed separately.**

---

## 0. Why this record exists

**Nothing in this programme has ever cleared the names-to-half-P&L breadth bar.**

| study | names to half the P&L | as a share | bar | |
|---|---|---:|---:|---|
| [D371](D371-RESULT-the-momentum-holdout-read.md) (holdout, retired) | 2 of 255 | **0.8%** | — | failed a flat-count version |
| [D373](D373-RESULT-the-winners-dip-is-the-retired-book-and-one-GME-trade.md) | 18 of 796 | **2.26%** | ≥ 10% | **FAIL** |

That is either a real and consistent property of every construction tried here, or **the bar is
unreachable by construction and has been adjudicating studies as failures on no information.**
No study so far can tell those apart, and in D373's §5 I flagged the doubt without resolving it.

**The asymmetry that makes this worth a study.** Every other hurdle in D373 is null-relative — H1, H2
and H3 all compare the observed statistic to A′/B/B_c percentiles. **H4 alone is an absolute number I
chose**, and D373's §5 admits its thresholds were "calibrated to exclude the shape that just failed",
which is an honest statement of provenance and a bad statement of evidence. A bar set to exclude one
observed failure tells you nothing about the next book.

**The fix is the one the programme already applies everywhere else: make it null-relative.** Ask not
*"is 2.26% a small number"* but *"is 2.26% small **for a random book of the same size, in the same
universe, holding the same kind of names**"*.

### What this study does NOT do

- It does not revisit D373's verdict. H1–H3, H5 and H7 stand as committed.
- It does not reopen the D373 avenue. That is the principal's under R15 and is still open.
- It reads **no holdout.** Holdout #1 stays spent, holdout #2 stays unspent.

---

## 1. The construction, frozen

**Exactly D373's primary cell, unchanged, and nothing else:** a fresh `rev_5` dip inside the
`mom_252_21` **top** decile, entered **long** at the next open (D340), hedged against the floored
equal-weight market, exited at a 40-bar cap. Cell **10:90 / cap 40**. Mining prefix only.

Committed ledger to reproduce before anything else runs: **3,932 trades, 796 distinct names, mean
+160.55 bp, median +51.55 bp** (`data/d373_winners_dip_long.json`).

**One cell, not five.** D373 ran five cells because it was *selecting* among them and owed a
best-of-5 floor. **This study selects nothing** — the cell is inherited, not chosen — so the
best-of-N floor is **dropped**, and applying one here would inflate the null against a decision that
is not being made. That is a deliberate departure from D373 and it is stated so it cannot be mistaken
for an oversight.

---

## 2. The statistics under test

Computed per book — observed and every null draw alike — by the **same function**, from the trade
ledger:

| | definition |
|---|---|
| `n_names` | distinct names with at least one trade |
| `names_to_half` | names, ranked by **total P&L per name** descending, needed to reach 50% of the book's total P&L |
| **`names_to_half_share`** | `names_to_half / n_names` — **the quantity H4 gates on** |
| `top1/top5/top10_name_share` | those names' share of total P&L |
| `total_pnl_bp` | the book's total, carried so degenerate draws can be identified rather than silently absorbed |

### 2a. Two defects in the incumbent implementation, declared before any result

**(i) The share statistics are undefined when total P&L ≤ 0.** `four_groups` already returns `None`
in that case. Null draws will hit it — a rotated or swapped book need not be profitable — and D371
saw the neighbouring pathology in the wild (**top-5 share of 142%, top-10 of 231%**, because
everything outside the top five lost money). **Percentiles must not be computed across a mix of
defined and undefined draws.** This study will report the count of degenerate draws per arm and
compute percentiles on the well-defined subset only, stating both numbers side by side.

**(ii) `names_to_half` is computed by `np.searchsorted` on a cumulative sum that is not monotone.**
`per_name` contains negative entries for losing names, so the descending cumulative sum **rises to a
peak and then falls back** to the total. `np.searchsorted` requires a sorted array; on a humped one
its result is not defined. **This may mean D373's published 18 of 796 is wrong.** The runner will
recompute it by an explicit linear scan and assert the two agree on the observed book; **if they
disagree, this record corrects D373's H4 number and says so plainly.** Declared here, before the
comparison is run, so the outcome cannot be presented as anything other than what it is.

---

## 3. The controls, and which one is load-bearing

| arm | what it holds fixed | what its concentration distribution answers |
|---|---|---|
| **A′** per-name time rotation within `elig` (D351) | **the name set and each name's trade count, exactly** | *Given these very names traded this many times each, how concentrated is a book by luck alone?* |
| **B** same-day same-RSI-bucket name swap | the day and the RSI bucket | the same question with the name set re-drawn from a loose pool |
| **B_c** same-day same-**cohort** name swap | the day and top-decile membership | the same with the name set re-drawn from the momentum cohort |

**A′ is load-bearing for this question, and that is a reversal from D373, where B_c was.** The
load-bearing control is a function of the question, not a property of the study: D373 asked whether
*dip timing* beat *cohort membership*, so the control had to re-draw membership. D374 asks whether
concentration is mechanical, so the control must **hold the name set exactly fixed** and vary only
luck. A′ is the only arm that does that. This is stated up front so the result cannot be read against
whichever arm happens to suit it.

**C is excluded, with cause.** Randomising the ledger's direction centres total P&L at zero, which is
exactly the degenerate case of §2a(i). Its share statistics would be dominated by near-zero
denominators. Including it would produce numbers, and they would be noise.

**Draws: A′ 2,000, B 1,000, B_c 2,000** — the same counts D373 used, so the two studies' null draws
are directly comparable. Five parts × 400 (× 200 for B), distinct draw indices, the same
`draw_rng(draw, arm)` keying. At one cell rather than five this should cost roughly a fifth of D373's
~3.9 s/draw; **the estimate will be replaced by the measured marginal rate in the result, not the
cumulative rate the progress log prints** (D373's log read 7.09 s/draw at draw 130 and 5.73 at draw
400 for the same underlying ~3.9).

---

## 4. THE TAIL DIRECTION IS INVERTED, AND THIS IS THE EASIEST THING TO GET WRONG

H1/H2/H3 ask whether an observed statistic is **large** — the comparison is to **p95**.

**H4 asks whether a book is diversified, so more names to half the P&L is better, and concentration
is the LOW tail. The comparison is to p05.** A book is anomalously concentrated when its
`names_to_half_share` sits **below** its nulls.

Writing `p95` anywhere in this runner's H4 path would silently invert the test. The runner will
assert the direction explicitly (§6, `[DIR]`).

---

## 5. The decision rules, pre-registered

**K1 — is the absolute bar reachable?**
Compare **A′'s p50** of `names_to_half_share` to the **10%** bar.
- **p50 < 10%** → a random book with this exact name set does not reach the bar either. **The
  absolute bar is not a concentration test**; it is a test of how fat the return distribution is in
  this universe. **RETIRE the absolute bar.**
- **p50 ≥ 10%** → the bar is reachable, and D373's 2.26% failure carries real information.
- Report B's and B_c's p50 beside it; if the three arms disagree materially, K1 is answered on A′ and
  the disagreement is reported as a finding rather than averaged away.

**K2 — is the observed book actually concentrated?**
Observed `names_to_half_share` (2.26%, subject to §2a(ii)) against **A′'s p05**.
- **below p05** → genuinely more concentrated than luck, for its own name set. **This is the
  replacement hurdle**, and D373's H4 failure survives in a defensible form.
- **at or above p05** → the observed concentration is what this name set produces by chance, and
  D373's H4 FAIL was an artefact of the bar.

**K3 — the same two questions for the top-1 and top-5 name shares**, which D373 *passed* at 5.74% and
20.62% against bars of 15% and 50%. Reachability cuts both ways: a bar that nothing can fail is as
uninformative as one nothing can clear.

**K4 — the replacement, written before the answer is known.** If K1 retires the absolute bar, H4 is
replaced for all future studies by: *`names_to_half_share` at or above the **p05** of A′ computed on
that study's own ledger*, with the top-1 and top-5 name shares at or below their A′ **p95**, and the
count of degenerate draws reported. **A hurdle whose threshold is fixed in advance of the universe is
what failed here; the replacement takes its threshold from the study's own null.**

**This study cannot be "passed" or "failed" by a strategy.** Its outcomes are verdicts on H4.

---

## 6. Assertions the runner must carry

All three of `CLAUDE.md`'s, plus the ones this study's specific risks demand.

| tag | what it proves |
|---|---|
| **`[MIR]`** | the inherited cell reproduces D373's committed 3,932 trades / +160.55 / +51.55 **before any null runs** — otherwise the calibration describes a different book |
| **`[CAL]`** | the concentration function reproduces D373's committed `n_names` 796, `top1` 5.74%, `top5` 20.62%, `top10` 34.04% exactly |
| **`[MONO]`** | `names_to_half` by explicit linear scan **equals** the incumbent `searchsorted` value on the observed book — **and if it does not, the runner reports both and this record corrects D373** (§2a(ii)) |
| **`[DIR]`** | the H4 comparison uses the **low** tail: assert that a synthetic book concentrated into one name scores **below** p05 and a synthetic uniform book scores **above** it (§4) |
| **`[DEG]`** | no percentile is computed over a draw whose `total_pnl_bp ≤ 0`; the excluded count is carried into the artifact, and the runner **refuses to report** if degenerate draws exceed 20% of an arm |
| **`[L]`** | lag audit — the held set re-derived from `score[:, t-1]` by a second implementation that never calls the selection function (inherited from D373, must still fire) |
| **`[S]`** | sign audit in money (inherited, must still fire) |
| **`[E]`** | every null draw's events satisfy the observed events' eligibility mask (D351's lesson; inherited) |
| **`[X]`** | **the one that matters** — every audit above must **RAISE** on a deliberately broken book. Ground truths that make this checkable: a book with all P&L in one name must give `names_to_half_share = 1/n_names` and `top1 = 100%`; a book with identical P&L in every name must give `names_to_half_share ≈ 0.5` |

**Persist before rendering.** The artifact is written before anything is printed — D371 lost a
one-shot measurement to a `KeyError` in a print loop, and D373 hit the same shape twice more and lost
nothing because of this ordering.

---

## 7. The search cost, stated

**There is none, and that is the point.** The cell is inherited from D373 with no re-selection, one
statistic family is scored, three arms, and the decision rules above were written before any of them
ran. No best-of-N floor applies (§1). Under [R13](../RULES.md#r13) this study adds **no** looks to
the multiplicity ledger of any strategy, because it adjudicates a hurdle rather than a strategy.

The one judgement call that is not free: **the choice of A′ as load-bearing** was made in §3 on stated
reasoning, before the numbers. If B and B_c disagree with it, that is reported (K1), not resolved by
preference.

---

## 8. Predictions

Written in the runner's own quantities so each is computable from the artifact.

| | prediction |
|---|---|
| **Q1** | **A′'s p50 of `names_to_half_share` is below 10%** — the bar is unreachable. Point estimate: **2–6%** |
| **Q2** | the observed **2.26%** is **at or above A′'s p05** — the book is *not* unusually concentrated for its own name set, and D373's H4 FAIL was the bar's doing |
| **Q3** | **A′'s p50 of `top1_name_share` is between 4% and 12%**, i.e. D373's observed 5.74% is unremarkable and the 15% bar is one almost nothing fails |
| **Q4** | degenerate draws (`total_pnl_bp ≤ 0`) are **under 5% for A′ and B_c**, and **higher for B** than for either |
| **Q5** | **AGAINST myself:** `[MONO]` finds no discrepancy — the `searchsorted` value equals the linear scan on the observed book, so D373's 18 of 796 stands. I expect the latent defect **not** to have bitten this particular ledger, and I am recording that expectation so a discrepancy counts as a real find rather than a lucky catch |
| **Q6** | B_c's p50 `names_to_half_share` is **within 2 percentage points** of A′'s — concentration is a property of the return distribution, not of which names get selected |

---

## 9. What would make me abandon this

- **Degenerate draws exceed 20% of any arm** → the share statistic is not well defined in this
  universe, `[DEG]` refuses to report percentiles, and the study reports **that** instead. It would
  still answer K1, in a stronger form: a statistic that is undefined for a fifth of random books is
  not fit to gate anything.
- **`[MIR]` or `[CAL]` fails** → the calibration is describing a different book than D373 reported;
  stop and fix the runner, publish nothing.
- **The three arms disagree on K1's direction** (some above 10%, some below) → report the
  disagreement, retire nothing, and say what a decisive version would need.

---

*Pre-registered 2026-09-07. Runner does not exist at the time of this commit (R8). Result to follow
in a separate commit and a separate record.*
