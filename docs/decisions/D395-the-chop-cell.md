# D395 — the CHOP cell: high volatility, low path efficiency, and a search that must be paid for

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). **Nothing here is a
result.** No cell scored, no null run, no book proposed.
**Date:** 2026-09-09 · **Area:** signal research · **personal track** · Requested by the principal.

**No holdout testing. Holdout reads spent by this record: 0. Programme total: 1** (D371).
**Build (R16):** today's panel, `load_ragged(dividend_bound=True)`, `keep_v2` floor, F0, next-open
fill (D340). **Number:** D395, in this branch's reserved D390–D399 block.

---

## 0. THE HONEST PREMISE, and it governs everything below

**This cell was not hypothesised and then tested. It was found by searching 36 cells on this
ledger** ([D394 Addendum 4](D394-ADDENDUM-4-the-vol-x-path-efficiency-taxonomy.md): 3 volatility
terciles × 3 ER terciles × 4 ER window definitions).

**And it has already failed the search-corrected floor once:** observed **+28.39** against a
best-of-36 floor of **+32.96**.

> **So this record's PRIMARY hurdle is not A′, B, B_s or C. It is the SEARCH.** A cell that clears
> every construction null and fails the search floor has shown only that a number picked from 36
> behaves like a number picked from 36.

**A defect in that floor is corrected here, before it is re-run.** Addendum 4 simulated 36
**independent** random subsets. The four ER windows are correlated — `ER_5`, `ER_21`, `ER_63` and
their ratio measure the same thing at different scales — so the effective number of independent
cells is **fewer than 36 and +32.96 is too strict.**

**The exact replacement, declared now:** **a LABEL PERMUTATION.** Hold the 36 real cell
definitions fixed, shuffle the per-trade P&L across trades, recompute all 36 cell means, take the
maximum. Repeat 10,000 times. **This preserves the exact cell structure, sizes and correlations,
so it needs no independence assumption and no normal approximation.** Its p95 is the floor.

---

## 1. The construction, frozen

- **Everything from D393 §3 unchanged:** floored (`keep_v2`), F0, eligible, **E1** on `up_run_21`,
  **long**, every event taken, no slot cap, hedged, next-open fill, truncated at delisting.
- **Hold: cap 5 PRIMARY** (the principal's focus), cap 20 reported beside it.
- **The filter, both legs at t−1, from the same lagged grids the book is built on:**
  - `rvol21` cross-sectional percentile in its **top tercile** among the cell's own trades, **and**
  - `ER_21` (A1's unsigned efficiency ratio, 21 of the name's own bars) in its **bottom tercile**.
- **`ER_21` is named, not chosen at runtime.** Addendum 4 ran four windows; **21 is fixed here
  because it produced the largest number**, and that is exactly why §0's floor is the binding
  hurdle rather than a formality.

**Direction, declared** — and it was declared in Addendum 4's runner before any number was seen:
**LONG.** *A name that has moved a lot and gone nowhere is thrashing; thrashing is noise, and noise
mean-reverts. An efficient move is repricing, and repricing continues.* A result in the opposite
direction is **DIRECTION-INVERTED** and counts against the mechanism.

---

## 2. The hurdles, in the order that decides them

| | hurdle | why |
|---|---|---|
| **H0** | **THE SEARCH FLOOR.** The cell mean exceeds the **p95 of the exact best-of-36 label permutation**, carrying its bootstrap SE; a margin within **2 SE** is **UNRESOLVED**, never passed (D369/D373) | **binding. If H0 fails, §5 stops the record** |
| **H1** | above the p95 of **A′, B, B_s and C**, each with SE and the 2-SE band | the construction battery |
| **H2** | **the atlas floor** for the cell's own conditional pool, not the unconditional one | D392; the filter selects cheap, volatile names |
| **H3** | **Size.** gross ÷ measured round trip ≥ 1.0, **with the per-bar deployed edge beside it** | D289 seventh amendment; **Addendum 5 measured 0.31×** |

**H3 is already known to fail at 0.31×.** It is listed because a record that quietly drops a
failing hurdle is worse than one that reports it.

---

## 3. The nulls, on the FILTERED cell

Every null regenerates the **whole book** and then **re-applies the filter at the null's own event
bars** — because volatility and efficiency are properties of *the name on the day*, and a null that
kept the observed cell's membership would be testing nothing.

- **A′** — per-name time rotation within eligible bars, score rotated with it. **2,000 draws.**
- **B** — same-day, same `rsi` bucket name swap. **2,000 draws** *(not 1,000: D393 Addendum 4
  recorded that B's 1,000 was the lowest count and B was the null that landed in the band)*.
- **B_s** — same-day, same `rev_21` decile name swap. **2,000 draws.**
- **C** — random direction on the observed filtered ledger. **2,000 draws**, no simulation needed.

**[E]** every null event satisfies the observed events' eligibility mask (D351), per draw batch.
**[F]** the filter is recomputed per draw and its tercile cuts come from that draw's own
distribution, never the observed one.

---

## 4. Predictions — three of five declared AGAINST

| | prediction |
|---|---|
| **Q1** | *(against)* **H0 FAILS.** The exact permutation p95 exceeds +28.39, and the record stops at §5. The correlated-window correction raises the observed cell's chance but not enough |
| **Q2** | The cell **clears A′** comfortably. Volatility and efficiency are entry-time properties; rotating a name's events in time destroys the conditioning, so A′ is a weak null here and clearing it means little |
| **Q3** | The cell **clears C** trivially — a direction null on a book with t +2.16 |
| **Q4** | *(against)* **H3 fails at every hold.** Net stays negative; the filter selects into $29.90 names at 43.67 bp a side, and Addendum 5 measured net **−62.29** against the unfiltered book's −56.76 |
| **Q5** | *(against)* **B and B_s bite hardest**, because the filter's power is concentrated in *which names* it selects rather than *when*, and both hold name characteristics fixed |

---

## 5. What would make me abandon this

- **H0 fails** → **record it and stop.** Do not run the construction battery to produce a
  favourable number from a cell the search does not support.
- **The direction inverts** → DIRECTION-INVERTED, counted against the mechanism.
- **Do NOT sweep the ER window, the tercile cuts, or the volatility measure** to rescue a failing
  H0. That is D366's search, which cleared 164 standard errors and then failed out of sample, and
  D393 §9 forbids it by name.
- **Any hurdle needs a holdout read** → **do not spend it.**

---

## 6. Assertions the runner must carry

- **[PERM]** the label permutation reproduces the observed cell means exactly when the identity
  permutation is used, and its 36 cell definitions are the same objects Addendum 4 used.
- **[F]** the filter is recomputed per null draw; **[X]** the self-test RAISES if the observed
  cell's membership is reused.
- **[E]** null events on the eligible mask; **[L]** the filter reads t−1 only, with
  `raises_on_broken`.
- **[N]** each null's centre reported against the cell's own base rate.
- **[P]** the JSON is persisted **before** it is rendered.
- **Four groups** with the top trade **named and its bar printed** (D322).

---

## 7. The search cost, stated

**Disclosed under R13:** D393's ten cells, D394's 126 exit-rule cells, D394 Addendum 3's nine
asymmetry observables, and **Addendum 4's 36 vol×ER cells from which this one was chosen.**
**H0 prices the last of these exactly. The others are disclosed, not summed into a floor no
measurement could clear** (R13's corollary).

**This record spends no holdout read.**

---

**Status footer.** No runner exists. `docs/BOOK.md` holds S1 and S2, neither at capital;
`docs/BOOK_PROP.md` is empty. Nothing here is a result, and **only the principal closes a research
avenue (R15).**
