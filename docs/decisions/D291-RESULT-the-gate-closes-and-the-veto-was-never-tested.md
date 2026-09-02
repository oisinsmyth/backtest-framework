# D291 RESULT — the gate closes, and the veto was never actually tested

**Status:** RESULT. Pre-registered at `a1fbc14`, clarified at `4603b68`, runner
at `a6be9f0`, all committed before this file existed (R8).
**Date:** 2026-09-02
**Area:** Strategy research · **personal track**

**Holdout reads spent: 0. Programme total: 0.** Nothing is promoted and no
primitive here has touched the holdout.

---

## The one-line result

**0 of 254 evaluated cells clear both paired `t` ≥ 2 and the best-of-272 floor
of +3.67.** The best cell in the study reaches `t` +2.92.

And a second result that matters more than the first: **87 of those cells — the
entire veto arm — should never have been scored, because the control I
pre-registered for them is not turnover-matched.** That is D279's error, it is
written in CLAUDE.md in as many words, and I designed it into the
pre-registration anyway.

---

## 1. The gate arm — valid, and it closes

167 cells. The statistic is the per-bar paired difference against A alone at
N′ = the mean surviving count.

| A | B | f | k | Δ bp | **t** | conf bp | ctrl bp | null p95 | z | bars |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `dist_52w_high` | `price_log` | 0.50 | 20 | +241.55 | **+2.92** | +312.64 | +71.09 | +2.94 | +1.53 | 1555 |
| `hist_L` | `macd_line` | 0.50 | 5 | +44.64 | +2.43 | +62.63 | +17.99 | +2.22 | +1.89 | 2997 |
| `rev_21` | `dist_52w_high` | 0.90 | 10 | +43.07 | +2.02 | +245.00 | +201.92 | +1.92 | +1.71 | 942 |
| `hist_L` | `rsi` | 0.25 | 5 | +38.42 | +1.93 | +45.05 | +6.63 | +1.69 | +1.94 | 3023 |
| `dist_52w_high` | `dist_lvn` | 0.50 | 20 | +127.67 | +1.75 | +191.47 | +63.79 | +2.49 | +0.60 | 1834 |
| `macd_hist` | `rsi` | 0.75 | 20 | +15.12 | +1.63 | +60.76 | +45.64 | +1.33 | +2.00 | 3185 |
| `hist_L` | `rsi` | 0.50 | 5 | +22.88 | +1.61 | +58.71 | +35.84 | +0.97 | +2.27 | 3118 |
| `macd_hist` | `rev_5` | 0.75 | 20 | +15.23 | +1.60 | +62.02 | +46.80 | +1.22 | +2.18 | 3186 |
| `hist_L` | `macd_hist` | 0.50 | 5 | +20.31 | +1.52 | +55.12 | +34.81 | +1.48 | +1.48 | 3100 |
| `rev_5` | `macd_hist` | 0.90 | 5 | +3.63 | +1.50 | +26.10 | +22.46 | +2.09 | +0.74 | 3187 |

**Key.** `A` primary, `B` filter, `f` fraction of B's ranking retained, `k` the
horizon inherited from A's D290 spread peak. **`Δ bp`** the mean per-bar
difference, confluence minus control, in basis points. **`t`** the paired
t-statistic on that difference — *the* statistic, not the confluence's own.
`conf bp` / `ctrl bp` the two books' own per-bar means, shown so the difference
can be read against its level. `null p95` the 95th percentile of this cell's own
rotate-B null; `z` where the observed sits in that null's distribution. `bars`
the number of bars on which all four legs are simultaneously active.

**Whole-arm summary:** `t` mean −0.07, median −0.09, 47% positive, 2% at `t` ≥ 2.
**Δ bp mean −7.1.** The gate arm's central tendency is *slightly negative*.

### The dose-response runs the wrong way — and this is the finding

| f | cells | t p50 | t mean | frac t > 0 | names kept |
|--:|--:|--:|--:|--:|--:|
| **0.90** | 44 | **+0.25** | +0.04 | 55% | 91% of N |
| 0.75 | 43 | +0.07 | +0.02 | 51% | 88% |
| 0.50 | 40 | −0.05 | +0.06 | 50% | 81% |
| **0.25** | 40 | **−0.33** | −0.39 | 32% | 65% |

Monotone. **The more you filter, the worse it gets**, and the arm's peak sits at
f = 0.90 — the edge of the sweep, climbing towards f = 1.00, which is *no filter
at all*. Under gate 1i an edge peak is "unresolved rather than concluded", and
here what it is climbing towards is the null operator. That is the cleanest
statement the study produces: **on this pool, the best amount of gating is
none.**

---

## 2. The veto arm — VOID, and it is my error

**The pre-registered control was "remove the same count at random, 50 times".
It matches the count. It does not match the turnover.**

`B`'s percentile is autocorrelated, so the names a veto keeps *persist*. A random
removal re-draws every bar, so a name is dropped and re-added for no reason at
all. Every statistic in this study is measured on **fresh entries**. So the two
books are not being compared on the same thing:

| A | B | f | held/bar | veto entries | random entries | **ratio** | veto run | random run |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| `price_log` | `skew_63` | 0.50 | 19.8 | 1.66 | 11.57 | **6.97×** | 11.9 | 1.7 |
| `price_log` | `choch_dist` | 0.90 | 11.8 | 1.38 | 8.77 | **6.37×** | 8.6 | 1.4 |
| `price_log` | `hist_L` | 0.50 | 25.5 | 2.27 | 11.89 | **5.24×** | 11.3 | 2.1 |
| `dist_52w_high` | `skew_63` | 0.25 | 8.4 | 1.31 | 5.38 | **4.11×** | 6.4 | 1.6 |

**Across all 88 veto cells the control enters 2.42× as often at the median, up to
6.97×. Exactly 1% sit inside 0.90–1.10×.** The `price_log` veto holds a name
11.9 bars; its control holds it 1.7.

**The gate's control passes the same audit** — median 0.95×, 66% inside
0.90–1.10× — which is what makes the contrast diagnostic rather than a
property of the fixture.

### The contradiction this explains

46% of veto cells put the observed book above 95% of their own random removals,
while the paired `t` against those same removals has median +0.23. Recomputed
side by side on one cell:

| A | B | paired t | obs bp | random bp | random sd | perm t | perm p |
|---|---|--:|--:|--:|--:|--:|--:|
| `choch_dist` | `hist_L` | +2.28 | +746.5 | −178.7 | 80.1 | **+11.55** | 0.020 |
| `choch_dist` | `price_log` | +1.96 | +797.1 | −168.6 | 96.0 | **+10.06** | 0.020 |
| `choch_dist` | `retrace_leg` | −0.63 | +39.2 | +81.5 | 80.8 | −0.52 | 0.686 |

A veto book earning +746 bp against a random control earning −179 bp is not a
confluence result. **It is a low-turnover book beside a high-turnover one**, and
at these horizons that gap alone moves the mean. The permutation statistic is
the sharper of the two and therefore shows the artifact more loudly, which is
why it looked like the stronger evidence.

**No veto number in this study is readable. The arm is void, not negative.**

---

## 3. Predictions

| | prediction | direction | outcome |
|---|---|---|---|
| **Q1** | no cell beats its control at paired `t` ≥ 2 | AGAINST | **CONFIRMED.** 0 of 254 clear the floor; the best is +2.92 against +3.67 |
| **Q2** | the veto outperforms the gate | for veto | **VOID.** Veto `t` p50 +0.23 against gate −0.09 is exactly what an unmatched-turnover control manufactures. The apparent confirmation is the artifact |
| **Q3** | the dead-name veto cuts long-leg dead share by ≥ 10pp | for | **FAILED, and not marginally.** Median change **+0.1pp**, best **−3.4pp**, worst +7.3pp. **0 of 88 cells reach −10pp** |
| **Q4** | any cell that beats its control fails the rotate-B null | AGAINST | **UNTESTED** — no cell beat its control. Whole-study rotate-B `z`: median +0.26, max +2.86 |
| **Q5** | no cell clears its measured cost | AGAINST | **CONFIRMED**, trivially, since none beat its control |

**Q3 is the one that should change behaviour.** The veto was built on a
measured defect — `price_log`'s long leg holds 33.5% delisted names against
10.7% short — and the operator does not touch it. A filter on a low-ρ partner
removes names essentially at random *with respect to delisting*. So even with a
sound control, the veto's stated mechanism was not operating. **Two independent
reasons the arm says nothing.**

---

## 4. The 18 cells that produced no statistic

Not thin books. Each of the four legs a paired difference needs is active on
600–1500 of 4187 bars. **It is the four-way intersection that collapses:** at
N = 3 and N = 5 a book re-enters about once a bar and fires on roughly a quarter
of them, so all four coincide on **12–72 bars** against D286's 100-bar floor.
Every one of the 18 is `choch_dist` (N = 5) or `rev_21` (N = 3).

A further **36 of the 254 evaluated cells sit on fewer than 400 common bars**,
concentrated in the same two candidates. **The paired difference is underpowered
at small N by construction** — a property of the design, not of the candidates.

---

## 5. What this closes, and what it explicitly does not

**CLOSED: the gate operator on this pool.** 167 cells, a valid matched-turnover
control, an empirical floor, and a dose-response that runs the wrong way. No
third operator, no re-cut of the ρ band, no widened sweep. As pre-registered.

**NOT CLOSED: the veto.** The pre-registration's stop condition was "if nothing
beats its control, gate and veto are closed". **That condition assumes a
control.** Applying a stop to a comparison that did not happen would be exactly
the D288 error the pre-registration warned about in its own second paragraph —
killing a candidate with the wrong instrument. If the veto is retried it needs a
**persistence-matched** control, not a count-matched one: draw the removals from
a rotated B rather than uniformly, so the control keeps the treatment's holding
run. That is a different study.

**NOT CLOSED: the blend.** Stated in advance and unchanged. The book is
equal-weight, so magnitude belongs at stage-3 sizing; a selection result cannot
speak for a weighting one.

---

## Ledger

| | |
|---|---:|
| **holdout reads spent** | **0** |
| holdout reads, whole programme | **0** |

In-sample looks disclosed and not priced: **272 declared cells** (254 evaluated,
18 without a statistic), plus the four post-hoc diagnostics in this record —
the dead-share check, the control audit, the permutation recomputation and the
intersection count. All four were run *because* a pre-registered prediction
failed or two statistics disagreed, and all four are disclosed here.

## Files

`data/d291_pair_matrix.json` · `data/d291_cells.json` ·
`data/d291_confluence.json` · `data/d291_diagnostics.json` ·
`data/d291_control_audit.json` · `scripts/run_d291_confluence.py` ·
`scripts/d291_diagnostics.py` · `scripts/d291_control_audit.py`

---

# AMENDMENT — 2026-09-03: the floor was the wrong instrument, and the shortlist is not empty

Raised by the principal, in two steps. Both were right, and the record above
framed the result wrongly. Nothing below changes a pre-registered number; it
changes what the numbers are held to mean.

## 1. The pre-registered floor controls the wrong error rate for stage 1

The best-of-272 floor controls the **family-wise** rate: the chance that *any*
cell is a false positive. That is the correct question when a study makes ONE
claim. **Stage 1 makes no claim.** It spends no holdout, closes nothing, and
produces a shortlist to carry forward. The cost asymmetry runs the other way: a
false positive costs one extra candidate at stage 2, a false negative discards a
real signal permanently.

**The floor was also not scale-fair.** Cells' own nulls differ ~7× in spread
(own p95 from +0.40 to +2.94), so a flat `t` threshold demands z ≈ +8 of a
tight-null cell and z ≈ +1.5 of a wide-null one. Redrawn three ways on the same
200 draws (`scripts/d291_floor_scales.py`):

| scale | floor | best observed | clearing |
|---|--:|--:|--:|
| MAX-t (pre-registered) | +3.67 | +2.92 | 0 |
| MAX-Z (scale-fair) | +3.38 | +2.86 | 0 |
| MIN-p (rank-based) | 0.0050 | 0.0050 | 0 |

The unfairness was real and it changed nothing.

**Benjamini-Hochberg — the stage-1 instrument — is harsher, not softer.** On the
163 gate cells: **0 kept at q = 0.05, 0.10, 0.20 and 0.50.** Not a resolution
artifact of 200 draws: at q = 0.50 BH is resolvable from i = 2 (threshold
0.0061) and the observed p(2) = 0.0100.

## 2. WHAT CLOSES THE GATE IS THE DOSE-RESPONSE, NOT THE FLOOR

The record above led with "0 of 254 clear the floor". That is the pre-registered
verdict and it stands, but **it is not the reason the gate arm closes.**

| f | t p50 | names kept |
|--:|--:|--:|
| 0.90 | +0.25 | 91% of N |
| 0.75 | +0.07 | 88% |
| 0.50 | −0.05 | 81% |
| 0.25 | −0.33 | 65% |

Monotone, arm mean Δ **−7.1 bp**, trend pointing at f = 1.00 — no filter at all.
**No multiplicity correction is involved in reading that**, and it would say the
same thing if this study had run one cell or ten thousand. The floor is a
tiebreak that was never needed.

## 3. AND THE SHORTLIST IS NOT EMPTY — the principal's second point holds

Per-cell p95 against a cell's own rotate-B null is a legitimate stage-1 bar,
because it asks the question confluence actually poses: **does B's CONTENT beat
a B-shaped filter that knows nothing?** 14 of 163 gate cells clear it against
8.2 expected by luck. Taken cell by cell that excess is unremarkable — the
diffuse test lands at **p = 0.055** (14 observed, null p50 9, p95 14).

**But the survivors are not scattered, and that is a different finding.**
Tested against the null's own correlation structure, taking the MAX over
candidates on each draw so the statistic is multiplicity-aware:

| statistic | observed | null p50 | null p95 | P(null ≥ obs) |
|---|--:|--:|--:|--:|
| **most survivors in a single A** | **6** | 3.0 | 5.0 | **0.5%** |
| most survivors in a single B | 4 | 3.0 | 4.0 | 20.5% |
| survivors at f = 0.90 (least filtering) | 1 | 2.0 | 5.0 | 87.5% |

**`hist_L` holds 6 of the 14 survivors, and 0.5% of null draws produce that much
concentration in any candidate.** Its six are five different partners — `rsi`
(f 0.50 and 0.25), `macd_line` (0.50), `rev_5` (0.75 and 0.50), `macd_hist`
(0.50) — clustered at **f ≈ 0.50**, not at the lightly-filtered end.

And the survivors **avoid** f = 0.90: 1 of 44, below the 2.2 expected. So they
are not simply the books closest to A alone, which was the obvious deflationary
explanation and is now ruled out.

## 4. What this changes

**The gate operator is closed as a source of PROMOTABLE cells** — no single
cell survives any family-wise floor, on any scale, and FDR keeps nothing at
q = 0.50. Unchanged from the record above.

**It is NOT closed as a stage-1 screen.** The pre-registered stop condition —
"if nothing beats its control, gate and veto are closed for this pool" — was
written as if stage 1 made a claim. It does not. **Amended: the stop applies to
promotion, not to the shortlist.**

**What stage 1 carries forward is `hist_L` as a primary that responds to
gating at f ≈ 0.50**, on the strength of a concentration that is beyond chance
at p = 0.005 — not the individual cells, which mostly sit at `t` ≈ +1.0 against
their controls.

**The distinction that matters for whatever is built next.** These are two
different questions and the survivors answer only the first:

- **does B add content?** — the `z` against a rotated B. 14 cells say yes.
- **does the confluence beat A alone?** — the raw `t`. Most survivors sit at
  `t` ≈ +1.0. `macd_hist + retrace_leg` at f = 0.50 has `t` **+0.33** with null
  mean −0.96: B's content clearly beats a rotated B, and the book still barely
  beats `hist_L`'s own control.

Third- and higher-order confluence built on these is legitimate stage-1 work and
spends nothing. **It must not treat the 14 as confirmed**, and it inherits their
in-sample selection — which the ledger prices when the holdout is eventually
read, not before.

## Amended ledger

| | |
|---|---:|
| **holdout reads spent** | **0** |
| holdout reads, whole programme | **0** |

Disclosed and not priced, in addition to the 272 declared cells: the three-scale
floor redraw, the BH-FDR reading, the diffuse-count test, and the concentration
test. All four are post-hoc, all four were prompted by the principal's challenge
to the pre-registered floor, and the concentration test is the only one that
found anything.

## Files added

`scripts/d291_floor_scales.py` · `scripts/d291_walkthrough.py` ·
`data/d291_null_surface.npz` (200 draws × 254 cells) ·
`data/d291_floor_scales.json`
