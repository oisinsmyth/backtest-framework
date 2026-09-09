# D398 RESULT — the structural state is a DIRECTION, not a trigger: it is on 95% of the time, and survivorship is a far smaller threat to the short leg than I argued

**Status:** RESULT. A **MEASUREMENT** (D280's class): no return, no cost, no null, no operating
point chosen. **Admits nothing (R15). Ledger contribution: 0.**
**Date:** 2026-09-09 · Pre-registration: [D398](D398-the-structural-state-premise-check.md),
committed **before the runner existed** (R8) · Runner: `scripts/run_d398_state_premise.py` ·
Artifact: `data/d398_state_premise.json` · **30 seconds** · **Holdout reads: 0.**

**Predictions: three held, one split, two FAILED — and both failures were mine, in the direction
that helps the principal's construction.**

---

## 0. The headline

| | |
|---|---|
| **The state is a regime, not a trigger** | UP is on **58.5%** of addressable bars, DOWN **36.2%**. Together **~95%**. The structural trendline chooses a *direction*; it does almost no selecting of *when* |
| **Onset entry is viable after all** | **976 onsets** on the 48 names that have 15-minute bars, against my predicted "fewer than 400". Q2 failed by 2.4× |
| **Survivorship is a ~6% tilt, not a disqualification** | against the **right** denominator the dead cohort's tilt is **1.06 in DOWN and 0.95 in UP** — and Q6 used the wrong denominator |
| **`er63` is an empty filter** | at ≥ 0.5 it retains **0.2–0.4%** of state bars; at ≥ 0.7, **0.0%**. Three of the nine ER cells are unusable |
| **The overlays are direction-neutral** | UP and DOWN retention agree within ~1 pp on **every** one of the twelve overlay cells |
| **The overlays are independent** | **0 of 108** intersections breach 5 pp against the product of the marginals |

---

## 1. The state

| universe | dir | names | episodes | bars in state | % of addressable | med len | p90 | max | names hit |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|
| all 1,573 | **UP** | 1,573 | 9,580 | 1,554,580 | **58.49%** | 99 | 417 | 1,837 | 1,349 |
| all 1,573 | **DOWN** | 1,573 | 9,155 | 961,005 | **36.16%** | 60 | 270 | 1,079 | 1,319 |
| **the 48 with 15m bars** | **UP** | 48 | 452 | 105,832 | **58.26%** | **175** | 556 | 1,640 | 48 |
| **the 48 with 15m bars** | **DOWN** | 48 | 524 | 66,215 | **36.45%** | 92 | 289 | 950 | 48 |

**"Addressable" is eligible × live × past the name's own 252-bar warm-up** — what a book could have
traded at all. 1,573 names, 4,187 bars, 4,137,239 live, 2,858,599 eligible.

> **Nothing here is a trigger.** A state on 58% of bars does not decide when to trade; it decides
> which way. **On the principal's construction the ER and volatility overlays are therefore not
> refinements — they are the entire selection mechanism**, and the record should be designed as
> though the trendline supplies only the sign.

**The 48 behave like the 1,573 on frequency (58.3% vs 58.5%) but their episodes are much longer**
— median 175 bars against 99. They are large survivors; that is what a survivor-only intraday
fixture selects for, and it is visible here rather than assumed.

---

## 2. Q6 was asked against the wrong denominator, and correcting it reverses the conclusion I gave

**Q6 predicted the dead cohort would carry MORE of the DOWN state than its 35.7% share of names.
It carries 20.8%. As written the prediction FAILS.**

**But the headcount share is the wrong denominator and I should have seen it before writing the
prediction.** A dead name is short-lived, and the state costs **252 of its own bars** in warm-up
before it can be in any state at all. So the dead cohort contributes far fewer *addressable* bars
than names, and comparing a share of state bars against a share of names measures **lifespan, not
downtrend**.

| universe | dir | dead % of names | **dead % of addressable bars** | dead % of state bars | **tilt** |
|---|---|--:|--:|--:|--:|
| all 1,573 | UP | 35.7% | **19.6%** | 18.7% | **0.95** |
| all 1,573 | DOWN | 35.7% | **19.6%** | 20.8% | **1.06** |
| the 48 | either | 0.0% | 0.0% | 0.0% | — |

**The tilt is real and it is in the predicted direction — dead names are relatively more DOWN and
less UP — but it is 6%, not the structural effect Q6 asserted.**

> ### THE CORRECTION I OWE THE PRINCIPAL, STATED PLAINLY
>
> I argued in this session that a survivor-only 15-minute fixture would make a two-sided verdict
> **uninterpretable**, because *"a result of 'the long side works and the short side doesn't' is
> precisely what survivorship predicts."* **On the frequency of the state, that overstated the
> problem by a wide margin: dead names carry near-proportional shares of both states.**

**AND THE LIMIT OF THAT CORRECTION, which is not small.** This measures the dead cohort's share of
**BARS**, not of **RETURN**. A name in a downtrend that delists delivers a far larger short return
than a survivor in a downtrend — FINDINGS §18 and §22 are the record of exactly how much a
programme's P&L can live in a handful of extreme trades. **So Q6 answers "how much of the DOWN
state lives in names that die" (≈ proportionally) and does NOT answer "how much of the short leg's
P&L lives there" (unmeasured).** The second question is the one that decides the short leg, and
this record does not touch it.

---

## 3. The overlays

### 3a. Retention — what each leaves of the state (counts, never P&L)

| universe | dir | er10≥.3 | er10≥.5 | er10≥.7 | er21≥.3 | er21≥.5 | er21≥.7 | er63≥.3 | er63≥.5 | er63≥.7 | band≤.10 | band≤.25 | band≤.50 |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| all 1,573 | UP | 48.2% | 22.8% | 7.6% | 30.1% | 7.4% | 0.9% | 7.8% | **0.4%** | **0.0%** | 20.5% | 50.2% | 84.0% |
| all 1,573 | DOWN | 48.9% | 23.4% | 7.9% | 30.9% | 7.8% | 0.9% | 6.7% | **0.3%** | **0.0%** | 21.5% | 51.6% | 82.6% |
| the 48 | UP | 48.9% | 23.2% | 7.7% | 30.7% | 7.8% | 0.9% | 8.6% | **0.2%** | **0.0%** | 20.1% | 50.1% | 84.7% |
| the 48 | DOWN | 49.6% | 24.2% | 8.3% | 31.9% | 8.0% | 0.8% | 6.6% | **0.2%** | **0.0%** | 21.2% | 51.4% | 83.5% |

**Three findings the design should absorb:**

1. **`er63` at ≥ 0.5 and ≥ 0.7 is an empty filter.** Path efficiency over 63 days essentially never
   exceeds 0.5 *inside a trend state* — a 63-bar trend is not a straight line. **Three of the nine
   ER cells are unusable and should be dropped rather than swept.**
2. **The overlays are DIRECTION-NEUTRAL.** UP and DOWN retention agree within ~1 pp on every one of
   the twelve cells. **Neither ER nor the volatility band will, by itself, make the short leg
   behave differently from the long leg.** Whatever separates the two legs has to come from
   somewhere else.
3. **`band ≤ 0.50` retains 83–85% and is barely a filter**; `band ≤ 0.10` retains ~21%.

### 3b. Q5 held, exactly

**0 of 108 intersections breach 5 pp** against the product of the marginals. ER and the volatility
band are independent on this universe, so **combined retention multiplies and is predictable**:
`er21 ≥ 0.5 AND band ≤ 0.25` ≈ 7.4% × 50.2% ≈ **3.7%** of state bars. That is a usable design fact —
the filter stack's cost in events can be computed before it is built.

---

## 4. Every prediction, scored (R14)

| | prediction | verdict |
|---|---|---|
| **Q1** | DOWN between 0.5× and 0.9× of UP bars-in-state | **HELD** — 0.618 on the 1,573, 0.626 on the 48 |
| **Q2** | *(against)* fewer than 400 onsets on the 48, both directions | **FAILED** — **976** (452 UP + 524 DOWN), 2.4× the bar |
| **Q3** | bars-in-state on the 48 exceeds 20,000 per direction | **HELD** — 105,832 and 66,215 |
| **Q4** | median episode length exceeds 63 bars | **SPLIT** — holds on three cells (99, 175, 92); **fails on the 1,573 DOWN at 60**, by three bars |
| **Q5** | intersections within 5 pp of the product | **HELD** — 0 of 108 breach |
| **Q6** | dead share of DOWN state exceeds 35.7% | **FAILED** — 20.8%, and §2 shows the denominator was wrong |

**Why Q2 failed, named.** I estimated onsets from S2's 13.9% exposure and its 63-bar cap. **That
exposure is a POST-CAP, post-no-reentry quantity and the state itself is not capped** — the raw
state runs at 58% with a median episode of 175 bars on these names. Dividing a capped exposure by
a capped hold to recover an entry rate double-counted the cap. **The consequence favours the
construction: onset entry is viable on the 15m-reachable names, and the design does not have to
fall back to state entry for sample size.**

---

## 5. Assertions, all discharged

| | |
|---|---|
| **[S2]** | `g_lo`, `g_hi` and the UP mask **bit-identical** to `run_uptrend_onset`'s own path over 143,355 cells (78,125 UP bars) — the check that proves the ragged scatter is right, since S2 passes the panel `T` where this must pass `len(bars)` |
| **[X]** | a slope perturbed by **1e-12** is caught by that pin |
| **[L]** | **225** truncated-panel recomputes equal the full-panel slope; a shifted grid is caught by `lag_audit.raises_on_broken` |
| **[W]** | **THIS ONE FIRED AND IT WAS RIGHT** — see §6 |
| **[E]** | prep and panel agree on symbols and dates; no eligible bar outside a name's live window; every scatter lands on the name's own live bars |
| **[P]** | the JSON was persisted before anything was rendered |

### 6. [W] caught a real defect, and the fix was to implement the guard rather than relax the check

The first run died on `[W] AA is in UP before its own 252th bar`. **`rolling_fit` clips its window's
lower edge to zero** (`lo = np.clip(t - WINDOW, 0, n_bars)`), so below a name's 252nd bar it fits an
**expanding** window and emits a slope on as few as `MIN_PIVOTS = 3` pivots — possibly over thirty
bars. That is not "a confirmed structural trend over the past year".

**S2 carries exactly this guard and I had omitted it:** `signals` zeroes `up[:, :start]` and `build`
asserts `WINDOW < start`. S2's `start` is a panel-wide index shared with S1; on a ragged panel the
faithful analogue is **per-name**, which is what §2 and §6 of the pre-registration already declared.

**Masking each name's first 252 own bars removes 164,971 UP and 128,674 DOWN state bars — 7.7% of
each.** The runner now asserts that number is non-zero, so the guard cannot quietly become vacuous.

---

## 7. What this changes for the construction, and what it does not

**Changes:**
- **Onset entry is on the table** (Q2 failed). The design does not need state entry for sample size.
- **The trendline is a direction, not a selector.** Design the record accordingly.
- **Drop `er63` at ≥ 0.5 and ≥ 0.7** — they are empty, and sweeping them would be search over
  nothing.
- **Survivorship on state FREQUENCY is a 6% tilt**, not a disqualification. My earlier framing is
  corrected in §2.

**Does not change:**
- **`holdout_intraday_15m` is still not a holdout for a daily signal.** All 16 of its names are in
  the daily mining fixture. Unchanged by anything measured here.
- **The survivorship question on RETURN is still open and still unmeasured** (§2's limit).
- **Nothing about cost**, which D247 measured as the binding constraint at 15 minutes on these
  instruments.
- **No avenue is opened or closed. Only the principal does that (R15).**

---

**Status footer.** A measurement. No strategy was scored, no return was computed, no operating
point was chosen, no 15-minute bar was read, nothing was admitted, and no holdout read was spent.
`docs/BOOK.md` holds S1 and S2, neither at capital; `docs/BOOK_PROP.md` is empty.

---
---

# RESULT, AMENDMENT 9 — the level dead band cuts the 95%, and it is a pure filter: it buys no onsets

**Appended 2026-09-09.** Pre-registered in [D398 §9](D398-the-structural-state-premise-check.md),
committed before the sweep's runner existed. **1 second.** Still a measurement: no P&L, nothing
admitted, no holdout read.

**[D0] δ = 0 reproduces §1 bar-for-bar on all four cells**, asserted — without it the sweep would
be measuring a different object.

## A9.1 The sweep

| δ | ann. | dir | **all 1,573 — % addr** | episodes | med len | **the 48 — % addr** | episodes | med len |
|--:|--:|---|--:|--:|--:|--:|--:|--:|
| 0 | 0.0% | UP | **58.49%** | 9,580 | 99 | **58.26%** | 452 | 175 |
| 0 | 0.0% | DOWN | **36.16%** | 9,155 | 60 | **36.45%** | 524 | 92 |
| 1e-4 | 2.5% | UP | 55.24% | 9,377 | 103 | 55.33% | 457 | 169 |
| 1e-4 | 2.5% | DOWN | 33.24% | 8,830 | 56 | 33.41% | 503 | 87 |
| 2e-4 | 5.2% | UP | 51.92% | 9,290 | 99 | 52.21% | 456 | 166 |
| 2e-4 | 5.2% | DOWN | 30.43% | 8,473 | 53 | 30.63% | 478 | 84 |
| 5e-4 | 13.4% | UP | 41.95% | 8,749 | 89 | 42.73% | 444 | 141 |
| 5e-4 | 13.4% | DOWN | 23.11% | 7,012 | 51 | 23.20% | 387 | 82 |
| **1e-3** | **28.7%** | **UP** | **26.69%** | **6,915** | 73 | **26.97%** | **392** | 106 |
| **1e-3** | **28.7%** | **DOWN** | **14.59%** | **5,253** | 41 | **15.19%** | **317** | 59 |
| 2e-3 | 65.5% | UP | 9.62% | 3,270 | 55 | 8.82% | **170** | 70 |
| 2e-3 | 65.5% | DOWN | 5.93% | 2,755 | 28 | 6.02% | **172** | 38 |

## A9.2 What it says

**The level band does what hysteresis could not.** At **δ = 1e-3 — a trend of 28.7% a year — the
combined state frequency falls from ~95% to ~42%** (UP 26.7%, DOWN 14.6%), and on the 48
15m-reachable names it still leaves **709 onsets** (392 UP + 317 DOWN) across 48 and 46 names.

**δ = 2e-3 is too far.** It drops names entirely — 48 → 40 for UP and 39 for DOWN — which is a
selection effect on top of a filter, and onsets collapse to ~170 a side.

## A9.3 Predictions

| | verdict |
|---|---|
| **Q7** at δ = 1e-4, UP still above 50% | **HELD** — 55.24% and 55.33% |
| **Q8** the halving δ lies in [5e-4, 2e-3] | **HELD** — between 5e-4 (41.95%) and 1e-3 (26.69%) on both universes |
| **Q9** episode count peaks in the interior | **FAILED on three of four cells.** Monotone falling everywhere except the 48's UP, which peaks at δ = 1e-4 by **5 episodes out of 452** — noise, not a peak |
| **Q10** DOWN reaches a given frequency at smaller δ | **HELD** — 25% needs δ ≈ 4.5e-4 for DOWN against ≈ 1e-3 for UP |

> **Q9's failure is the useful one, and it changes the entry design.** I predicted a level
> threshold would *fragment* long episodes before eliminating them, which would have bought onsets
> while removing bars. **It does not: median episode length falls monotonically too** (UP 99 → 55
> on the 1,573). **The band is a pure filter — every onset it removes is gone, and it creates
> none.** So δ is paid for entirely in sample size, and it must be chosen once, on the frequency it
> buys, and never swept against an outcome.

## A9.4 What this does NOT settle

- **The hysteresis and the ratchet are still unbuilt.** §9a's distinction stands: a band on the
  gradient's *change* stabilises the line and leaves frequency alone. It belongs in the
  construction record, with its own mechanism.
- **δ is not chosen here.** 1e-3 is where the arithmetic points; the choice is the principal's.
- **Nothing about return, cost, or the short leg's P&L.** All still open.
