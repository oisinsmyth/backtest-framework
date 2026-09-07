# D380 — the volatility tilt: `zr` scored alone, the measurement D280 said it could not make

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). **Nothing here is a
result.** No cell has been scored, no null has been run, no book is proposed.
**Date:** 2026-09-08 · **Area:** signal research · **personal track**

**No holdout testing. Holdout reads spent by this record: 0. Programme total: 1** (D371,
2026-09-07). `data/fixtures/us_shorts_daily_holdout2.csv.gz` exists and is **unspent**; this record
does not touch it, and D357's short candidate retains its prior claim.

**Number.** `D380` was free at the time of writing. A concurrent session is active on `master`; if
this number collides at merge, renumber this file — nothing references it yet.

---

## 0. What this record is, and the one claim it is NOT built on

**[D280](D280-the-forecast-precheck.md) part 4C** found the composite `zh + zv + za + zr` reaching
a cross-sectional IC of **−0.01373 at t −5.07** on all live names — described in `PICKUP.md` §5
item 5 as *"the only directional statistic in that record that clears its own multiplicity"*, and
recorded there, since 2026-09-02, as **needing its own pre-registration and never having been
run.** This is that pre-registration.

**D280 also names, in its own words, the gap that makes the result unusable as it stands:**

> *"`zr` alone was never scored, so this record **CANNOT** say how much of −0.01373 is the
> volatility term by itself. That is not recoverable from the artefacts and needs its own
> measurement."*

**and it says which way the tilt points**, which is the opposite of the intuitive reading:

> *"The gain is entirely `zr`. Flip its sign and the IC goes positive (+0.00116). **This is a
> volatility tilt, not a stronger `hist_L`** — a `+zr` term pushes high-range names *out* of an
> ascending short ranking, so the book shorts the **quieter** names."*

**So the thing to measure is `zr` on its own, and the direction under test is "short the calm
names", not "short the volatile ones".**

### 0a. A claim withdrawn before it could be built on

`docs/research/the-signal-hunt-part2.md` §7e asserted that C1b's `VOL_XS` result had *"re-found
the same object"* as D280's tilt. **That was wrong and is corrected there.** The two live on
different axes:

| | axis | direction |
|---|---|---|
| **D280's tilt** (this record) | **cross-sectional**, ranks names within a bar | short the **calmer** names |
| **C1b's `VOL_XS`** (not this record) | **time-series**, one market-level number per bar | high market vol → the loser cohort drifts **up** |

**This record therefore rests on ONE instrument — D280's IC and its t −5.07 — and claims no
corroboration from C1b.** If a reader wants the market-state result, it is a separate candidate
needing a separate record.

---

## 1. What is under test

**Q: how much of D280's −0.01373 is the volatility term alone, and does a book built on it earn
anything gross?**

This is a **two-stage record** and the stages are not both authorised at once:

- **STAGE 0 is a MEASUREMENT** — score `zr` alone as a cross-sectional IC, exactly as D280 scored
  the composite. It scores no book and admits nothing. **If Stage 0 fails its bar, the record
  stops there and the tilt is closed as a candidate.**
- **STAGE 1 runs only if Stage 0 clears**, and is the R15 signal test: a gross mean per trade above
  its nulls.

**Stage 1's construction is frozen in §3 before Stage 0 is run**, so that a clearing Stage 0
cannot be followed by a construction chosen to suit it.

---

## 2. Stage 0 — `zr` alone

**The quantity.** `zr` as D280 built it: the within-bar z-score of the component D280's part 4C
combined. The runner must **read D280's own definition from its script rather than re-deriving
it**, and assert that recombining `zh + zv + za + zr` from its own components reproduces D280's
published **−0.01373 / t −5.07** before `zr` is scored alone. *(That is this record's `[ID]`, and
it is the check that the object being measured is D280's and not a lookalike.)*

**The measurement.** Mean cross-sectional Spearman IC of lagged `zr` against the next bar's
return, on **all live names** and on the **eligible (floored, F0) set** separately — the two
universes D280 reported, plus the floor D339 imposed after D280 was written.

**The bar, declared now:**

| | |
|---|---|
| **S0-a** | \|mean IC\| of `zr` alone **≥ 0.006** — roughly half the composite's −0.01373. Below that, `zr` is not the source of the composite's edge and D280's attribution is wrong |
| **S0-b** | its **t** clears a **best-of-161** correction, the multiplicity D280 declares for itself (median largest \|t\| **2.86**). A t below that is not evidence, by D280's own standard |
| **S0-c** | the sign is **as D280 states** — the tilt shorts the *calmer* names. A reversal is **DIRECTION-INVERTED** and counts against the mechanism even if the magnitude is good (gate 1h) |

**Stage 0 spends no cells and proposes no rule.** Under R13 it inherits D280's 161 comparisons,
because D280 shaped this search.

---

## 3. Stage 1 — the construction, frozen before Stage 0 runs

Only if Stage 0 clears all three. **Every choice below is D339/D340/D347's standing convention, so
that nothing here is a free parameter:**

- **Universe:** the floored (`keep_v2`), deal-filtered (F0) eligible set, lagged, on bars after the
  hedge is defined.
- **Score:** `zr` alone, within-bar z-score, at **t−1**.
- **Book:** the ranking's own extreme — short the top decile by `zr`-implied calmness in the
  direction Stage 0 confirms — entered at the **next open** (D340), hedged against the floored
  universe's equal-weight return, truncated at delisting.
- **Hold:** cap ∈ {5, 10, 20, 40, 60} **reported in full and not picked** (R14's fourth amendment).
  **Primary is cap 20**, chosen now, before any number is seen, purely as the midpoint of the grid.
- **Borrow:** charged as D337 charges it. **Direction declared: SHORT** (gate 1h).

### 3a. The σ² tax is named as this record's most likely cause of death

**A volatility tilt is precisely the loading the σ² tax prices**, and D280 says so itself
(*"everything in 'what must not be claimed' applies here twice over"*). FINDINGS §1b: the tax took
**59% of D264's gross**. **This record expects that bill and reports it as a line, not a
footnote** — gross, the tax, and the residual, side by side, per §5's H6.

**And PICKUP §3.3 attaches a second one:** overnight drift is a property of *volatility*, not of
equities — high-vol names ran **+13.81%** overnight against **−8.97%** intraday, low-vol the
reverse. **A book sorted on volatility is sorted on that split**, so the overnight/intraday
decomposition is reported per §5's H6 rather than assumed away.

---

## 4. The nulls

All on the primary exit. **Every null's events must satisfy the observed events' eligibility
mask** (D351), asserted per draw batch.

- **A′** — each name's positions rotated in time within its **eligible** bars. **2,000 draws.**
- **B** — each event's name replaced by a random eligible name in the same `rsi` bucket that day.
  **1,000 draws.**
- **B_v** — **load-bearing, and specific to this record.** Each event's name replaced by a random
  eligible name **in the same volatility decile** that day. **2,000 draws.** *This is the null that
  asks whether `zr` carries anything beyond being a volatility sort — the direct analogue of
  D373's `B_c`, and §52's rule applied before the fact rather than after: **before crediting a
  selector, measure what a random member of the same pool on the same day earns.*** If the book
  does not beat `B_v`, `zr` is a volatility bucket and nothing more.
- **C** — random direction on the per-trade ledger. **2,000 draws.**

**Every reported p95 carries its bootstrap SE**, and a margin within **2 SE** of its bar is
recorded **UNRESOLVED**, never passed (D369; D373's convention). **None of these nulls is a finite
group** — they are per-name rotations and replacements — **so C2b's enumeration remedy does not
apply here and the SE must be carried.** That is stated so the absence of enumeration is a decision
rather than an oversight.

---

## 5. The hurdles — and each names its PARTNER, per D289's sixth amendment

**This is the first record written under that amendment**, which requires that a pre-registration
quoting a stage-1 gate names the gate's partner and reports both.

| | hurdle | partner | why |
|---|---|---|---|
| **H1** | **Signal (R15).** Gross mean per trade > 0 and above the p95 of A′, B, **B_v** and C | **H2** | the standing criterion — significance |
| **H2** | **Size.** Gross mean per trade ≥ **1.0×** the measured round trip (gate 1c) **and** the per-bar edge on the deployed base reported at the same hold | **H1** | 1c is monotone in holding period; a cell clearing it while its per-bar edge falls versus a shorter cap is recorded **HOLD-DRIVEN**, not clearing (D289 sixth amendment) |
| **H3** | **Capturability (1e).** Open-entry t ≥ 2.0 **and** retention ≥ 50% | each other | R14's second amendment; 15 of D290's 51 collapsed here |
| **H4** | **Breadth (H4′).** `names_to_half_share` ≥ the **p05 of A′** computed on this study's own draws | — | D374's replacement; a fixed count was the bar's fault, not the book's |
| **H5** | **Independence (1d′), reported at stage 1.** ρ to S1, S2 and the retired S6/C9, against the p95 of the pair distribution **in this candidate's own pool** | **a paired difference of means on matched bars** | D289 sixth amendment: ρ is blind to level. **Failing 1d′ alone is a REPLACEMENT question, not a rejection** |
| **H6** | **Cost, reported not gating.** Net PB and PUB; the held names' **measured** Corwin–Schultz half-spread; breakeven half-spread; **the σ² tax as its own line**; the overnight/intraday split (§3a); turnover, holding run and dead share (1g) | — | R15: cost decides nothing at the signal stage. D285 missed a guessed bar by 0.65 |
| **H7** | **Horizon (1i).** The cap profile reported in full; an edge peak is **horizon-unresolved**, not concluded — **with the per-name effect at the peak beside `t`** | the per-name effect | the fifth amendment's own pairing |

**Both lenses, never on the same statistic** (FINDINGS §10): the path-invariant per-trade reading
and the path-variant deployed book in bp/bar, reported separately.

---

## 6. Predictions

Committed before the runner exists, written in the runner's own quantities. **Q2 is load-bearing;
Q4 is against.**

| | prediction |
|---|---|
| **Q1** | Stage 0 clears S0-a: `zr` alone reaches \|mean IC\| ≥ 0.006. D280 attributes the whole composite gain to it, so a much smaller value would mean the attribution is wrong |
| **Q2** | *(load-bearing)* the Stage-1 book's gross mean per trade is **above the p95 of B_v** — `zr` is not merely a volatility bucket. **This is the prediction most likely to fail**, and if it does the record closes on §52's rule rather than on cost |
| **Q3** | the sign holds: the tilt shorts the **calmer** names (S0-c). D280 states it twice and the mechanism is explicit |
| **Q4** | *(against)* **H6's σ² tax takes ≥ 40% of the gross.** FINDINGS §1b measured 59% on D264; a volatility-sorted book should not do better |
| **Q5** | H5's ρ to S1 and S2 is **below 0.3** — they are ETF-universe constructions and this is single-name; a high value would mean something is wrong with the measurement, not that the books are related |
| **Q6** | the cap profile's peak on gross per trade is **interior**, not at the grid edge — a volatility tilt is a state, not an accumulating drift, so it should not improve monotonically with horizon |

---

## 7. The search cost, stated

**Multiplicity: D280's 161 distinct statistics, inherited in full under [R13](../RULES.md#r13)**,
because D280 shaped this search — the composite, its components and the direction all come from
that record. **Stage 0's bar S0-b is set at D280's own best-of-161 floor for exactly this reason.**

**Stage 1 adds five cells** (the cap grid), of which one is primary and declared in advance, so
H1 is measured against a **best-of-5 floor** — the maximum over the five caps taken **within each
draw**, as D367 and D373 built theirs.

**In-sample looks are bookkeeping, not a bar** (R14's first amendment). **This record spends no
holdout read.**

---

## 8. Assertions the runner must carry

- **[ID]** recombining `zh + zv + za + zr` from this runner's own components reproduces D280's
  published **−0.01373 / t −5.07** before `zr` is scored alone. Without this the object is not
  D280's.
- **[L] Lag audit** — the held set re-derived from `score[:, t−1]` in a **second implementation
  that never calls the selection function**. ~93% of D279's apparent edge was this bug.
- **[S] Sign audit, in money** — a favourable move pays positively on the short; a dividend moves
  long and short oppositely. A sign asserted in prose inverted D280 itself.
- **[E]** every null event satisfies the observed events' eligibility mask (D351), per draw batch.
- **[Bv]** `B_v` draws only from the event's own volatility decile on that bar, and never the event
  name; pool membership asserted per draw.
- **[N]** each null's centre is reported against the universe base rate; a null centred far from it
  fails the run rather than earning a mechanism.
- **[P]** the result JSON is **persisted before it is rendered** (D371 lost its evidence to a
  `KeyError` in a print loop).
- **[X]** the self-test **RAISES** on (a) the tilt's sign flipped and (b) a `B_v` draw taken from
  the wrong volatility decile. **A self-test that cannot fail is worse than none.**

---

## 9. What would make me abandon this

- **Stage 0 fails S0-a or S0-b** → D280's attribution of its composite to `zr` is wrong. **Record
  it and stop.** Do not go looking for which other component carries it: that is a search over
  four terms on a record that already carries 161 comparisons.
- **Q2 fails — the book is inside `B_v`** → `zr` is a volatility bucket, and §52's rule closes it
  the same way it closed the winners' dip. **This is the outcome I consider most likely.**
- **The sign inverts** → DIRECTION-INVERTED, and the record says so rather than re-deriving a
  mechanism for the other direction.
- **Any hurdle needs a holdout read to settle** → **do not spend it.** `order[5100:6300]` is not
  cut for a stage-1 signal test and D357's short candidate has a prior claim.

---

**Status footer.** No runner exists. No cell has been scored. `docs/BOOK.md` holds S1 and S2,
neither at capital; `docs/BOOK_PROP.md` is empty. Nothing in this record is a result, and **only
the principal closes a research avenue (R15).**
