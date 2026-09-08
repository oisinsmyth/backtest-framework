# D393 ADDENDUM 3 — `up_run_21` clears A′ too: the timing is real, and it is worth ~16 bp over random timing in the same names

**Status:** ADDENDUM 3. **Two nulls of four now run, on one cell of ten. H1 is STILL NOT CLEARED
— see §4.** Admits nothing (R15).
**Date:** 2026-09-08 · Runner: `scripts/run_d393_bs_null.py --null A` · Artifact:
`data/d393_aprime_null.json` · 8 processes, 556 s · **Holdout reads: 0.**

---

## 1. A′ — 2,000 draws, each name's events rotated within its OWN eligible bars

The score is rotated **with** the events, which is what makes this a *timing* null rather than a
different book. Names and per-name event counts are held exactly fixed.

| score | observed | p50 | **p95** | SE | margin | verdict |
|---|--:|--:|--:|--:|--:|---|
| **`up_run_21`** *(candidate)* | +22.06 | **+5.74** | **+16.20** | 0.39 | **+5.86** | **ABOVE** |
| `up_frac_21` *(control)* | +21.62 | +3.10 | +13.29 | 0.25 | +8.33 | **ABOVE** |

Draw range −16.77 to +27.03 for the candidate. **Margin +5.86 against SE 0.39 is ~15 SE**, far
outside the 2-SE UNRESOLVED band.

> **Enter the same names at random times and they earn +5.74. Enter them when the signal says to
> and they earn +22.06.** The timing is worth roughly **16 bp per trade**, and that is what the
> candidate is actually claiming.

---

## 2. THE CONTROL'S EXPECTED DIRECTION IS OPPOSITE HERE, and the runner said the wrong thing first

**Under `B_s`, `up_frac_21` MUST die** — it *is* the `rev_21` decile (ρ +0.601), so a B_s that
spared it would have no power and its verdict on the candidate would be worthless. It died (−7.14).

**Under A′, `up_frac_21` SHOULD survive.** `rev_21`'s own E1 timing is real and published at
**+38 bp** (FINDINGS §31). A′ destroys timing and keeps names, so a redundant-but-real timing
effect is *supposed* to clear it. It did (+8.33).

**A correction to this runner, made before these numbers were reported.** The render tagged
`up_frac_21` as *"POSITIVE CONTROL: must be killed"* under **both** nulls — correct for B_s,
**wrong for A′**, where it would have invited exactly the wrong conclusion from a right number. The
label is now null-aware and the reasoning is in the code. **No number changed**; `data/d393_bs_null.json`
and Addendum 2 are unaffected, because "must be killed" was the correct description there.

---

## 3. A CORRECTION TO WHAT I SAID A′ WOULD TEST

Addendum 2 §7 and my report of it said A′ was *"the null for"* the question the overlap check
opened — whether ~+20 bp belongs to the **E1 decile-crossing shape** rather than to any particular
score. **That was imprecise and this file withdraws it.**

**A′ holds the NAMES fixed and destroys the TIMING.** It answers: *does this score's timing beat
random timing in these same names?* — yes, by 16 bp. **It does not ask whether a decile crossing
on some OTHER persistent score would earn the same**, which is the open question.

**Nothing in the record tests that yet, and no existing null does.** It would need a control with
**matched persistence** — a synthetic score with `up_run_21`'s own autocorrelation, crossing its
own decile, at matched event count. D291's rule is why the obvious cheap version does not work:
*a random subset is never a control for a persistent selector*, because it re-draws each bar and
churns. **The question stands open, and naming it is the honest position rather than implying two
nulls have closed it.**

---

## 4. WHERE THE CANDIDATE ACTUALLY STANDS

| bar | value | `up_run_21` | cleared? |
|---|--:|--:|---|
| D392 atlas floor, pool ALL | +12.67 ± 0.93 | +22.06 | ✔ |
| **`B_s`** p95 (same `rev_21` decile) | +18.97 ± 0.31 | +22.06 | ✔ **+3.09** |
| **A′** p95 (rotated timing) | +16.20 ± 0.39 | +22.06 | ✔ **+5.86** |
| **B** (same `rsi` bucket) | — | — | **UNRUN** |
| **C** (random direction) | — | — | **UNRUN** |

**H1 IS NOT CLEARED, and no reading of this file should say it is.** §7 of the pre-registration
requires the p95 of a **best-of-10 floor** — the maximum over the ten-cell grid *within each draw*
— which is strictly higher than any single-cell p95. **Both margins above are upper bounds on what
H1 would see, not results.**

**And it is still not tradeable.** Net **−39.13 bp/trade** at **0.36×** the measured 61.19 bp round
trip, against gate 1c's ≥ 1.0×. **A′ and B_s are statements about signal. Neither is a statement
about money after costs.**

Multiplicity is **20** under the per-score reading. The grid is **not blind** — the primary cell
was seen before either null ran.

---

## 5. Assertions

- **[A′]** reuses D373's `aprime_draw_long` rather than a second rotation, so D351's three checks
  fire inside it. Verified here: **25,997 of 26,236 events moved to a new bar (99.1%)**, per-name
  counts preserved, nothing off the eligible mask — **and the rotation RAISES when handed an
  all-ineligible mask.**
- **[SHARD]** 12 draws in 4 strides reproduce the sequential list bit-identically; one `item_at()`
  definition serves every path; `merge_shards` asserts full coverage and no index in two shards
  before scoring.
- **[P]** persisted before rendering. **Holdout: 0 reads** (mining fixture; the holdout is a
  disjoint symbol set).
- **8 processes, 556 s.** Threads remain the wrong tool for this kernel (0.37×, Addendum 2 §6).

---

## 6. What the record needs next, in order — none of it authorised here

1. **B and C on this cell** — the last two nulls, ~25 min on the same machinery. Cheap, and they
   complete the battery §4 declared.
2. **The other nine cells**, which is the only way H1's best-of-10 floor can be computed. **This is
   not optimisation; it is what the pre-registration already requires.**
3. **Only then, a cost study** — and it needs its own pre-registration (R8), because the binding
   constraint is 22 bp of gross against a 61 bp round trip, not the strength of the signal.
   **CLAUDE.md: cost-cutting and edge-sharpening are different operations and the report must say
   which moved.**

**A parameter sweep over window length, decile width or cap is NOT on this list.** §9 forbids it by
name: *"that is the search that produced D366's gate, which cleared 164 standard errors and then
failed out of sample."* The 21-bar window was fixed before any number was seen, and that is the
only reason it means anything now.

---

**Status footer.** Two nulls of four, one cell of ten, no holdout read, nothing admitted.
`docs/BOOK.md` holds S1 and S2, neither at capital; `docs/BOOK_PROP.md` is empty.
**Only the principal closes a research avenue, or opens the next stage of one (R15).**
