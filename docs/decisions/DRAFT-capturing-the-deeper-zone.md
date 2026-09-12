# DRAFT — capturing the deeper zone

**Status: PROPOSAL. Uncommitted, no decision number taken.** Nothing here has been run. Written
at the principal's request after D420, for a decision that has not been made.

---

## 1. What the record already says, which is the whole reason for this

Five results, from five different questions, point at the same population:

| record | what it found |
|---|---|
| D412/D413 | later touches of a level pay *more* than the first (T4 inverted) |
| D416 | the deepest collapses — stalls on day 6–10 — bounce hardest (+670 bp on the stall entry) |
| D418 | closes *through* the zone go on to do better than closes that held (+23.6 vs +12.9, weakly) |
| **D420** | **a re-entry — the name's second-or-later zone in a continuing decline — pays +16.70 bp against +9.47 for a first entry; median +12.96 against +4.20; 52% of all touches, 72% of cell 2** |
| D419/D420 | every exclusion rule tried — cooldown, episode, and the structural stop-out — removes exactly this population |

**The deeper zone is the better trade, it is identifiable at the touch, and every rule discussed
so far throws it away.** D416 tried to reach it by entering *later in time* and paid for the wait.
The proposal is to reach it by entering *deeper in price* — on the day the deeper zone is
touched, at the close, which is the entry four execution studies located.

---

## 2. THE ARITHMETIC FIRST — what this can and cannot fix

Stated before the design so the design is not oversold.

- **Pooled, the deeper zone does not clear cost.** A re-entry pays +16.70 gross against a ~27 bp
  neutral round trip: **0.6× coverage**, up from 0.41× for all touches. Better; not tradeable by
  the principal's own rule.
- **In cell 2 it might.** Cell-2 re-entries pay **+31.04** against ~23 bp: **1.35×** per trade —
  and on a 10-slot book at 92% utilisation the cost is ~5.3 bp/bar against a gross that would
  rise from 4.6 toward ~5.7. **Marginally net-positive, on spent data, selected on results.** That
  is the honest size of the prize.
- **It does not reduce turnover.** D420 §3 measured this: on a full book a selection rule swaps
  which names hold the slots and the round trips keep coming. What it changes is the **gross per
  trade**, which is the only lever selection has.
- **Nothing here is out-of-sample.** D420 already found the re-entry premium on this fixture. A
  study built on it can add three things D420 did not measure — **whether depth scales, what the
  book does with depth as a priority, and what the structural definition adds** — but it cannot be
  independent evidence that the premium exists. The confirmation is `holdout2`, and by the
  principal's standing decision it waits for a tradeable indicator.

---

## 3. THREE DEFINITIONS OF "DEEPER", one primary

All three are knowable at the touch-day close. All three are selection conditions on D413's
events; the trade — entry at the touch-day close, five-day hold, no stop — is unchanged.

| | condition | what it is | parameters |
|---|---|---|---|
| **DEEP-1 — re-entry** | the zone was **alive during the name's previous trade** (`a_k ≤ last_exit`) | D420's classification, inverted into a requirement. Already measured at +16.70 | none |
| **DEEP-2 — breach above** | a **higher** zone on the same name was touched and its **far edge traded through** within the last 60 sessions | **the principal's structural framing:** the stack above has *failed*, and this is the next level down. The stop-out consumption inverted into an entry condition | none beyond the zone machinery |
| DEEP-3 — stack depth | the number of distinct zones on the name touched in the trailing 20 sessions: 1, 2, 3+ | does depth *scale*? | the 20-session window |

**Primary: DEEP-2.** Two reasons, both stated so they can be argued with. It is the definition
closest to what the principal described — entry and stop derived from one structure — and it is
the one thing here **D420 did not already look at**, so it is the arm with the most new
information. DEEP-1 is the known baseline it is read against; DEEP-3 is shape.

**The prediction that would justify the primary:** DEEP-2 pays *more* than DEEP-1 — a breached
zone above is deeper than a merely touched one — at something like +20–25 bp pooled. If it does
not, the structural framing adds nothing to "second zone," and DEEP-1 is the rule.

---

## 4. Both lenses, and the controls that make them mean something

### 4a. Per trade

- **T1** — `mean(r_base | DEEP-2) − mean(r_base | not DEEP-2) > 0` by 2 SE. Reported with the
  CLAUDE.md distribution (mean, median, win, symmetric trim) for both populations.
- **Shape** — DEEP-1 beside it (the known +7.22 gap), and DEEP-3's three buckets: **the
  monotonicity of depth is the shape that says whether this is a gradient or a step.**
- **Per year.** D420 reported the premium pooled across 2010–2026. ADDENDUM 1 found the base
  edge concentrated in 2010–2013. **Whether the depth premium is also front-loaded in time is the
  robustness question that matters most**, and it has not been looked at.

### 4b. The book

D419's simulator, three seeds, with **DEEP-2 as the refill priority** (then cell 2, then random)
on the 50-slot book, and **DEEP-2 as a refill requirement** on a second book. Cell 2 ∩ DEEP-2 on
the 10-slot book as the secondary — this is the cell §2 says might clear.

- **T2** — the DEEP-2-priority book's **net** bp/bar exceeds FIXED's by 2 SE, monthly block
  bootstrap.
- **T3** — it exceeds the p95 of a **matched-count random-priority** control: same number of
  events promoted to the front of the queue, chosen at random, 50 draws. A priority rule on a
  capacity-bound book changes selection whatever it prioritises; the rule must beat a random one.
- **Utilisation, turnover and cost per bar reported** — the check that §2's "does not reduce
  turnover" is true, and that any net gain is gross-per-trade and not a cost artefact.

### 4c. What would have to be true for this to matter

**The cell-2 ∩ DEEP-2 book clears net, against FIXED and against its random control, and the
per-year table shows the premium in the second half of the sample.** That is the bar for calling
this a candidate for the holdout. Anything short of it is a better-understood construction that is
still not tradeable.

---

## 5. Predictions, if this is pre-registered as written

| | prediction | confidence |
|---|---|---|
| X-a | DEEP-2 fires on **15–30%** of touches — computable from D413's events before the run, and it will be computed, not guessed | — |
| X-b | DEEP-2 pays more than DEEP-1: **+20–25 bp** pooled against +16.70 | moderate |
| X-c | DEEP-3 is **monotone**: 3+ > 2 > 1 | moderate |
| X-d | the DEEP-2-priority 50-slot book raises gross per trade toward +18 and net by ~+0.5 bp/bar, **still net-negative** | moderate-high |
| X-e | **cell 2 ∩ DEEP-2 is net-positive on the 10-slot book, inside 2 SE of zero** | low-moderate |
| X-f | the depth premium is **present in both halves of the sample**, unlike the base edge | low |

**X-e and X-f are the study.** X-e is the prize and X-f is whether the prize is real.

---

## 6. What this does not do, and would not

- **Does not read the holdout.** The principal's rule stands; nothing here is a tradeable
  indicator until §4c is met.
- **Does not change the entry price, the hold, or add an exit.** Four studies located those.
- **Does not sweep.** Three definitions, one primary, one window parameter in the shape arm.
- **Does not claim independence from D420.** §2.
- **Is not a pre-registration.** It is the case for writing one, for the principal to accept,
  amend, or decline.

---

## 7. The one alternative worth naming

If the goal is net rather than gross, the other lever the record has found is **trading less**:
D420's random-thinning control at 62% utilisation was net-positive on cell 2, and D419 said a
book trading a tenth as often would pay 0.6 bp/bar in cost. Depth as a *requirement* rather than a
*priority* does both at once — it raises gross per trade *and* thins the pool — which is why §4b
runs both books. A DEEP-2-required cell-2 book would be the sharpest single test of whether this
line has a tradeable trade in it.
