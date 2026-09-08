# D393 ADDENDUM — the pre-registered primary cell in money: `up_run_21` clears the base-rate floor, and earns what the score K1 KILLED earns

**Status:** ADDENDUM to [D393 RESULT](D393-RESULT-the-sign-sequence-family.md). **NO NULL WAS RUN.
This is not Stage 1 and admits nothing (R15).**
**Date:** 2026-09-08 · Runner: `scripts/run_d393_sign_sequences.py --probe` · Artifact:
`data/d393_probe.json` · **52 s**
**Holdout reads: 0.** Verified structurally, not assumed — see §5.

---

## 0. The ruling this acts on

The Stage 0 RESULT §4 left the split-K1 verdict with the principal. **The principal gave the
per-score reading on 2026-09-08:** run the survivors. So `up_frac_21` is dropped as a candidate and
**carried here as a positive control**, `up_run_21` and `sign_flips_21` proceed, and multiplicity
becomes **20** rather than 10 for any later Stage 1.

**Why a probe and not Stage 1.** §4's nulls are 7,000 draws over a 10-cell best-of floor. Scaling
D359's measured rates (0.54 s/draw A′, 0.69 B, 0.35 B_c at cap 10) across caps {5,10,20,40,60} × 2
shapes lands near **19–20 h serial**. Spending that on a score with **no measured edge at all** is
the wrong order, so this measures the single cell §3 already froze as primary.

---

## 1. The cell — E1, cap 20, LONG, every event taken

| | `up_run_21` | `sign_flips_21` | `up_frac_21` |
|---|--:|--:|--:|
| | **candidate** | **candidate** | **REFERENCE — K1 killed it** |
| trades (events) | 20,785 (26,236) | 21,086 (38,097) | 21,317 (40,020) |
| **GROSS bp/trade** | **+22.06** | **−4.50** | **+21.62** |
| median | +13.38 | −5.69 | +8.39 |
| win rate | 50.6% | 49.7% | 50.6% |
| t | +3.09 | −0.67 | +3.08 |
| **symmetric trim** | **+18.38** | −7.27 | +19.32 |
| ex-top 1% / ex-bottom 1% | −19.82 / +60.29 | −44.43 / +32.69 | −20.43 / +61.39 |
| measured round trip (PUB) | 61.19 | 52.46 | 60.75 |
| **NET bp/trade** | **−39.13** | −56.97 | −39.13 |
| gross ÷ 2c | **0.36×** | −0.09× | 0.36× |
| breakeven half-spread | +9.91 bp/side | −3.26 | +9.63 |
| **atlas floor (ALL)** | **+12.67 ± 0.93** | +12.57 ± 0.93 | +12.50 ± 0.93 |
| **margin** | **+9.39 ABOVE** | **−17.08 BELOW** | +9.12 ABOVE |

**Mean is ABOVE median on both positive cells**, so the left tail is not doing the work
(CLAUDE.md's tell). The book is two-sided fat-tailed — ex-top and ex-bottom move ~42 and ~38 bp in
opposite directions — so **the symmetric trim (+18.38) is the honest number**, and it still clears
the floor.

---

## 2. THE FINDING, and it is not the one the margin suggests

> **AMENDED 2026-09-08 by [Addendum 2](D393-ADDENDUM-2-the-overlap-and-B_s.md) §1. The
> "parsimonious reading" offered below — that `up_run_21` is `rev_21`'s effect at lower fidelity —
> was tested by §7 of this file and REFUTED: the two books share 2.9% of their trades, and
> deleting every trade `rev_21` takes leaves 20,182 of 20,785 at +19.56 bp. The OBSERVATION that
> the two scores earn the same is unchanged and is stranger than the explanation given here. Read
> §2 as the hypothesis it was.**

> **`up_run_21` (+22.06) and `up_frac_21` (+21.62) earn the same thing, on ~21,000 trades each.**

`up_frac_21` is not a candidate. K1 killed it at **ρ +0.601** to `rev_21`, and the Stage 0 RESULT
called it *"the 21-day return with the magnitude removed"*. `up_run_21` cleared K1 only because
**ρ +0.370** sits under a 0.5 bar.

**A 0.23 gap in correlation produced a 0.44 bp gap in money.** The parsimonious reading is that
`up_run_21` is the same reversal effect at lower fidelity — and FINDINGS §31 already prices that
effect: `rev_21`'s own E1 timing is **+38 bp**. A degraded proxy earning +22 is exactly what that
predicts. Nothing here needs a new mechanism.

**This is not the same claim as "ρ bounds the difference in means" — which is false, and was
corrected on this programme on 2026-09-07.** ρ did not predict the equality; **the equality was
measured.** The point runs the other way: K1's threshold sorted these two scores into different
buckets and *the money did not agree with the sort*.

**K1 is a screen on correlation and it did not do the job the record asked of it.**

---

## 3. `sign_flips_21` — no edge in the pre-registered cell, and a defect in its declared direction

**Gross −4.50 bp/trade, t −0.67, 17.08 bp BELOW its own floor.** The most orthogonal score the
programme has measured (|ρ| ≤ 0.025 against everything) earns nothing as a long on E1.

**And §1's declared mechanism never described it.** §1 declared one direction for all three scores
— *"a low value is a name under sustained one-sided selling"*. That is true of `up_run_21` and
`up_frac_21`. **It is false of `sign_flips_21`, which is blind to direction by construction**: a low
flip count is a name that *trended*, either way. So E1 on it does not isolate sustained selling.

**The diagnostic split** — reported as a diagnostic, **not a candidate cell, not pre-registered**:

| | trades | mean | median |
|---|--:|--:|--:|
| trailing return **down** | 10,778 | **+3.43** | −3.42 |
| trailing return **up** | 13,081 | −8.23 | −8.90 |

The half the mechanism actually claims earns **+3.43 against a +12.57 floor**. **The direction
defect was not hiding an edge.**

**This does not close the score.** Its case was always independence, not standalone edge (RESULT
§5.2), and **only the principal closes an avenue (R15)**.

---

## 4. What the pool test showed — and the declared pool STANDS

§3 declared pool `ALL` with an escape clause: *"if Stage 0's correlations say otherwise the
conditional pool is used instead and the record says the pool changed and why"*. **The tilt rule
(dominant tercile > 45% of events) was written into the runner before any number was seen.**

Events per tercile (lo/mid/hi %, uniform 33/33/33):

| | price | vol | mom |
|---|---|---|---|
| `up_run_21` | 34/33/33 | 34/35/31 | **34/33/33** |
| `sign_flips_21` | 28/34/38 | 37/34/29 | 33/35/32 |
| `up_frac_21` | 36/33/31 | 32/34/34 | **36/33/31** |

**No axis is tilted on any score. The pool does not change, and `ALL` is the operative floor.**

That is a real result and it is the one thing that went the candidate's way: a *decile crossing* is
not momentum-tilted even when the score *level* correlates at ρ +0.370. **The atlas's conditional
pools were not needed** — which matters, because they only span 2,827–19,241 trades at cap 20 and
these cells sit at ~21,000. **Had a tilt appeared, the honest floor would not have existed.** That
gap is now the most urgent of the three atlas gaps owed.

---

## 5. Assertions, and what was taken on trust

- **[L1]** each grid is the processed score at t−1 with row 0 empty, checked in a second
  implementation that never calls `percentile_grid`; **raises on an unshifted grid**.
- **[L2]** 1,200 sampled events re-derived by **direct counting** (`lag_audit.pct_direct`).
- **[E]** every sampled event sits on an eligible bar (D351).
- **[SC]** a constant score reproduces the cap-exit ledger exactly — the score is inert at
  `exit="cap"`, `n_max=None`, as §3's "no slot cap" requires.
- **[C]** `temp/d290_scores.npz` byte-identical across the run.
- **[P]** the JSON was persisted **before** rendering.
- **Holdout: 0 reads, verified not assumed.** The holdout is a **disjoint set of 803 symbols** in
  `us_shorts_daily_holdout.csv.gz` (`run_d357_holdout_read.FIXTURES`, `[DIS]` asserts no overlap).
  This ran on the mining fixture, 1,573 names, 2010-01-04 to 2026-08-26.
- **TAKEN ON TRUST: [T].** The truncation audit was **not** re-run here — it is inherited from the
  module self-test and from Stage 0, which built the scores with the same function. Stated so it is
  a decision and not an omission.

**The top trade was looked at, not quoted** (D322's lesson):

| | bar | date | close → close | raw | ledger |
|---|--:|---|---|--:|--:|
| **GME** | 2766 | 2020-12-29 | 4.84 → 48.40 | **+899%** | +38,435 bp = **8.38%** of the ledger |
| TDS | 3404 | 2023-07-14 | 7.64 → 17.41 | +127.9% | +10,756 bp |
| AAOI | 4053 | 2026-02-13 | 44.46 → 94.07 | +111.6% | +10,193 bp |

**`up_run_21`'s top trade is the January 2021 GME squeeze**, and it is 8.38% of the P&L. **D373's
RESULT is titled "the retired book and one GME trade."** This is the same trade in a new book.

**One thing unresolved, flagged rather than smoothed over.** TDS and AAOI's booked bp track their
raw moves within ~10–20 points; **GME's +899% raw books as +384%**. The hedge and the sizing
convention explain the direction of the gap but not obviously its size. **It is conservative, so it
does not flatter the result — but it should be understood before any Stage 1.**

**A rendering artifact, not a data defect:** `sign_flips_21`'s top trade prints "−10.73% of the
ledger" because the ledger total is negative. The bp figure is right; the share is meaningless when
the denominator is negative.

---

## 6. What this does and does not license

**Does:** `up_run_21` produces a **positive gross mean per trade above the D392 base-rate floor** —
which is the programme's stated signal criterion, on the gross leg.

**Does not:**

1. **The atlas floor is not a null.** It is what a *random* long earns at matched trade count and
   cap. It shares the candidate's **count**, not its **turnover, cohort or timing** — and
   CLAUDE.md's rule is that a control must share the treatment's nuisance. **A′, B and B_s are
   unrun.**
2. **Net is −39.13 at 0.36× the measured round trip.** Gate 1c needs ≥ 1.0×, 2c ≥ 1.5×. **Nothing
   here is tradeable as constructed**, and the breakeven half-spread of +9.91 bp/side sits against
   names whose measured cost is far above it.
3. **One cell of ten has been seen.** The full grid, if ever run, is **no longer being read blind**,
   and any Stage 1 must disclose that. Recorded in the artifact's `caveat` field.

---

## 7. The cheapest decisive next measurement, not run and not authorised

**§2's reading is a hypothesis and it is directly testable two ways, both cheap:**

1. **Held-set overlap.** The share of held name-bars `up_run_21` shares with `up_frac_21` and with
   `rev_21`'s own E1. D365/D373 used exactly this and found **70.1%**. Minutes, no nulls.
2. **`B_s` on the one cell** — swap each event's name for another in the **same `rev_21` decile**
   that day. §4 already declared this null **load-bearing** for precisely this failure mode. At
   ~0.7 s/draw for one cell at cap 20, **2,000 draws is roughly 23 minutes**, not 19 hours.

**Neither is authorised by this file**, and the second is a change to §4's scope (one cell, one
null, rather than the full grid) that only the principal can make.

---

**Status footer.** No null run. Stage 1 not run and not authorised. `docs/BOOK.md` holds S1 and S2,
neither at capital; `docs/BOOK_PROP.md` is empty. **Nothing admitted, no avenue closed, no holdout
read.**
