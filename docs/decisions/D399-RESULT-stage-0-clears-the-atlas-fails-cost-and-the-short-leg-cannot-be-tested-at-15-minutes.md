# D399 RESULT — Stage 0: the construction clears its atlas floor on both sides, fails cost on both, and 72% of the short side's P&L is in names that delist

**Status:** RESULT, **Stage 0 only. STAGE 1 IS NOT AUTHORISED AND WAS NOT RUN.** No null was drawn.
**Admits nothing (R15). Ledger contribution: 0.**
**Date:** 2026-09-09 · Pre-registration: [D399](D399-the-ratcheted-structural-line.md), committed
**before the runner existed** (R8) · Runner: `scripts/run_d399_ratcheted_line.py` ·
Artifact: `data/d399_stage0.json` · **~2 minutes** · **Holdout reads: 0.**

**Predictions: one held, one split, three failed, one not testable.**

---

## 0. THE LOOK-AHEAD I INTRODUCED AND THEN CAUGHT — read this before any number

**The first run of this file reported the primary cell at −34.91 bp (long) and −61.09 (short), every
one of 48 cells negative. That result was my own look-ahead and it is void.**

`d345_event_book.py:11` states the contract: *"Inputs are (T, n) and **ALREADY LAGGED**."* The
kernel treats its mask as **the bar the position OPENS ON**. This record's event reads **bar `t`'s
own close** (`close[t] ≤ L[t]`), and I handed that mask over unshifted — so the book was entering
on the very bar whose down-move created the event, and booking that move.

| | first run (void) | **corrected** | swing |
|---|--:|--:|--:|
| UP primary, gross | −34.91 | **+31.13** | **+66.04** |
| DOWN primary, gross | −61.09 | **+15.03** | **+76.12** |

**The sign is exactly what the defect predicts**, which is how it was spotted: a book that buys
support and shows −35 bp gross against a random draw's ~0 is not a weak signal, it is a bug.

**This is D391's defect, repeated by me, in a record whose own §8 declared `[L]` and whose helper's
docstring names the case verbatim** — `lag_audit.lag1_mask`: *"**Use this when the event reads bar
t itself.**"* I wrote the requirement and did not implement it. The runner now carries
`lag1_mask` + `assert_mask_is_lagged` on every cell and **proves the unlagged mask RAISES.**

> **Third time in this session that an assertion I declared caught a defect I introduced:** `[W]`
> fired in D398, `[L]` should have fired here and had to be added, and §8's own `h = ∞` / `L[t] −
> L[t−1] == G` errors were corrected in writing before the run. **The declarations are working;
> my implementation of them is what keeps failing.**

---

## 1. The construction produced far more events than predicted, and the reason matters

| | raw touches | primary cell | of which on the 48 with 15m bars |
|---|--:|--:|--:|
| **UP** | 264,501 | **60,698** | 4,218 |
| **DOWN** | 152,612 | **39,792** | 3,156 |

**Q1 predicted fewer than 3,000 per direction and it failed by twenty-fold.** K0 never came close
to firing.

**Why, and it is a property of the ratchet worth keeping.** `L[t] = min(L[t−1] + G, fresh)` does
not run away from price — it tracks the **lower envelope of the fitted support lines**. A line
built that way sits exactly where price keeps returning. **The widening ratchet is a level-finder,
not a distance-maker**, and that is the opposite of what "only ever moves away from price"
suggested.

---

## 2. The hurdles: H2 clears, H3 fails

| primary cell, cap 10 | trades | **gross** | 2c | **net** | **ratio** | atlas p95 | margin |
|---|--:|--:|--:|--:|--:|--:|--:|
| **UP** | 13,768 | **+31.13** | 66.26 | −35.13 | **0.47×** | +10.40 ± 1.05 | **+19.7 SE** |
| **DOWN** | 8,656 | **+15.03** | 81.91 | −66.88 | **0.18×** | +12.00 ± 1.14 | **+2.7 SE** |

- **H2 (atlas) CLEARS on both sides** — the long comfortably, **the short at 2.7 SE, barely outside
  D369/D373's 2-SE UNRESOLVED band.** A thin pass is reported as thin.
- **H3 (cost) FAILS on both.** Gross would have to double on the long and rise 5.5× on the short.
- **Per §6's ordering, H1 and H4 were NOT spent.** No best-of-8 floor, no A′/B_s/C. **Nulls are not
  drawn on a cell that has not cleared the cheap bars**, and this record does not spend them to
  produce a favourable-looking number.

### 2a. Two cells reach 1.0× — and both are HOLD-DRIVEN, so it is amortisation, not edge

| UP cell | cap 5 | cap 10 | **cap 20** | ratio at cap 20 |
|---|--:|--:|--:|--:|
| er10≥0.5 band≤0.5 | +19.47 / **3.89** bp·bar | +41.57 / **4.16** | **+73.06 / 3.66** | **1.10×** |
| er10≥0.5 band≤0.25 | +17.72 / **3.54** | +40.65 / **4.07** | **+66.99 / 3.35** | **1.02×** |

**Gross per trade rises 76% from cap 10 to cap 20 while per-BAR edge falls 12%.** Cost is one round
trip regardless of cap (`two_c` reads only `(row, entry_bar)` — D394 §3), so the entire coverage
gain is **cost amortisation by holding longer**. **14 of 16 cell-families are HOLD-DRIVEN** under
D289's seventh amendment.

> CLAUDE.md states the distinction this record must obey: *"Cost-cutting ≠ edge-sharpening … Say
> which moved: edge per unit exposure, or cost per trade."* **Cost per trade moved. Edge per bar
> did not — it fell.**

---

## 3. Q6 — and it decides Stage 1 on its own

**The question D398 explicitly could not answer: does the short side's P&L live in the names that
delist?**

| primary cell | cap | dead % of **trades** | **dead % of GROSS P&L** |
|---|--:|--:|--:|
| **UP** | 5 / 10 / 20 | 19.4 / 19.2 / 19.3% | **12.7 / 0.7 / 2.7%** |
| **DOWN** | 5 / 10 / 20 | 20.9 / 21.0 / 21.2% | **42.8 / 72.4 / 53.9%** |

> **At the primary cap, dead names are 21.0% of the short side's trades and 72.4% of its gross
> P&L.** Q6 predicted "more than 25%" and **HELD by a wide margin.**
>
> **The long side is the mirror: 19.2% of trades, 0.7% of P&L.** The long leg lives entirely in
> survivors; the short leg does not exist without the dead.

**CONSEQUENCE, and it is a hard blocker rather than a caveat.** The 15-minute fixture is
survivor-only and **cannot be otherwise on this API tier** — `TIME_SERIES_INTRADAY` refuses every
delisted ticker, and 41.6% of the cohort is unreachable there.

> **A Stage 1 short measured on 48 survivors would be measuring the ~28% of the P&L that is not
> where the P&L is. THE SHORT LEG IS NOT TESTABLE AT 15 MINUTES ON THIS FIXTURE**, and no amount of
> care in the intraday layer repairs that.

**This also completes the correction I owed from D398 §2.** There I found survivorship was a ~6%
tilt on state *frequency* and said so, while flagging that the *return* question was unmeasured.
**It is now measured, and on return the effect is enormous.** Frequency was the wrong place to look.

---

## 4. Every prediction, scored (R14)

| | prediction | verdict |
|---|---|---|
| **Q1** | *(against)* fewer than 3,000 events per direction | **FAILED by 20×** — 60,698 and 39,792. §1 gives the mechanism |
| **Q2** | hysteresis: episodes −>15%, median +>15%, frequency moves <3 pp | **SPLIT** — episodes −39.7%/−33.4% ✓, median +67%/+58.5% ✓, **frequency −3.87 pp on UP ✗** (−2.52 pp on DOWN ✓) |
| **Q3** | *(against)* the SHORT side does not clear its atlas floor | **FAILED** — it clears at **+2.7 SE**, thinly |
| **Q4** | the LONG side clears, by less than 2× | **FAILED** — it clears by **2.99×** |
| **Q5** | *(against)* the best cell sits inside its best-of-8 floor | **NOT TESTABLE** — H1 was not spent, because §6 orders H3 first and H3 failed. **Not claimed either way** |
| **Q6** | dead names carry >25% of the SHORT side's gross P&L | **HELD — 72.4%** |

**Three of my four directional predictions were wrong, and Q1 was wrong about the object's basic
behaviour** — I described a ratchet that runs away from price and built one that finds the level
price returns to.

---

## 5. Assertions discharged

| | |
|---|---|
| **[D0]** | at δ = 0, h = 0 the state reproduces **D398 §1 bar-for-bar** — UP 1,554,580, DOWN 961,005 |
| **[R]** | the offset never moves toward price: **4,027,363 low** and **4,029,147 high** non-anchor bars checked, and an under-exercised audit raises |
| **[L]** | every mask shifted before the kernel sees it; **the unlagged mask RAISES** (§0) |
| **[W][E]** | every event past its name's own 252nd own-live bar, and on an eligible bar (D351) |
| **[X]** | four planted breaks caught, including `h = ∞` failing as the control — **the spec's own corrected error, now a test** |
| **[P]** | the JSON persisted before the verdict was rendered |

---

## 6. What Stage 0 settles, and what it does not

**Settles:**
- **The construction is measurable** — K0 never fired, and by 20×.
- **It clears the unconditional base rate on both sides** — the long by 3×, the short thinly.
- **It does not clear cost as pre-registered**, and the two cells that reach 1.0× do so by holding
  longer, not by earning more per bar.
- **The short leg cannot be taken to 15 minutes on this fixture**, on Q6.

**Does not settle:**
- **Whether the search explains the result.** H1's best-of-8 floor is uncomputed. **Any later
  reading of the two 1.0× cells must compute it first** — they are the best of 24 UP cells.
- **Whether the long leg survives a real null.** A′, B_s and C were not drawn.
- **Whether 15 minutes earns its place.** §7's daily-vs-15m comparison is untouched.

**Nothing is retired and no avenue is closed. Only the principal does that (R15).**

---

**Status footer.** Stage 0 of a pre-registered record. `docs/BOOK.md` holds S1 and S2, neither at
capital; `docs/BOOK_PROP.md` is empty. Nothing was admitted and no holdout read was spent.
