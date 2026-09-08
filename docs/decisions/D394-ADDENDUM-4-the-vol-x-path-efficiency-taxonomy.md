# D394 ADDENDUM 4 — the volatility × path-efficiency taxonomy: the prior holds at one window, fails at two, and nothing survives its own multiplicity

**Status:** ADDENDUM 4. **EXPLORATORY** — hypothesis generation on the training ledger. No null, no
hurdle, nothing selected, fitted or admitted (R15). **Nothing closed.**
**Date:** 2026-09-09 · Runner: `scripts/run_d394_vol_er_grid.py` · Artifact:
`data/d394_vol_er_grid.json` · **Holdout reads: 0.**

---

## 1. The taxonomy, with one axis corrected

ER measures the **shape** of a path (net ÷ travel, scale-free); volatility measures its **size**.

| | low ER — wanders | high ER — direct |
|---|---|---|
| **low vol** | **DEAD** — small, nowhere | **GRIND** — small, one way |
| **high vol** | **CHOP** — big, nowhere | **TREND** — big, one way |

*The principal's note placed low-vol/high-ER as "flat" and low-vol/low-ER as "slow trending". It is
the reverse: flat is low-vol/**low**-ER; a slow trend is low-vol/**high**-ER.*

**The prior, declared in the runner before any number:** this is a reversal book, so
**CHOP > DEAD > TREND** — thrashing is noise, and noise is what mean-reverts.

---

## 2. The noise floor, computed before the cells were read

**2,753 trades per cell, per-trade std ≈ 498 ⇒ SE ≈ 9.49 bp per cell.** A *random* 9-way split of
the same ledger produces a maximum cell mean of **+19.75 on average, p95 +28.10**.

> **Cells scatter by tens of basis points on nothing at all, against a cost bar of 61.48.**

---

## 3. Cap 5 — the corners, by window

| ER window | DEAD | GRIND | **CHOP** | TREND | prior | best cell | beats noise? |
|---|--:|--:|--:|--:|---|--:|---|
| **5** | +7.48 | +9.06 | **+21.17** | **−12.64** | **HOLDS** | +21.64 | no |
| **21** | +3.63 | −4.19 | **+28.39** | +11.36 | fails | **+28.39** | *marginally* |
| **63** | +13.44 | +4.83 | **+1.90** | +9.44 | fails | +17.60 | no |
| 5/63 ratio | +3.14 | +12.27 | +18.96 | +2.30 | — | +18.96 | no |

**CHOP is the best corner at windows 5 and 21 — and the WORST at 63.** The answer flips with the
lookback, which is the tell that this is not a stable structure.

**The prior holds only at ER window 5** — the window that matches the 5-bar hold. That is weakly
consistent with *the relevant path shape being the one measured over the horizon you trade*, and it
is a hypothesis, not a finding, because the cell does not beat noise.

---

## 4. AND THE ONE CELL THAT BEAT ITS FLOOR DOES NOT SURVIVE THE CORRECT FLOOR

`ER_21 / hivol / loER` (CHOP) at **+28.39** cleared the 9-cell p95 of +28.10 — **by 0.29 bp.**

**But 36 cells were run, not 9** (4 window definitions × 9). The floor must be the maximum over
what was actually searched:

| | mean of max | **p95 of max** |
|---|--:|--:|
| max of 9 cells | +18.77 | +28.69 |
| **max of 36 cells** | +24.78 | **+32.96** |

*(Normal approximation at SE 9.49; it reproduces the empirical 9-cell p95 of +28.10 to within
0.6 bp, so it is calibrated.)*

> **Best observed across the whole search: +28.39. Correct floor: +32.96. It does not clear.**
> **Nothing in the taxonomy survives its own multiplicity.**

---

## 5. What the grid actually shows: volatility, again, and ER adding nothing stable

**Every high-vol row has P(left) ≈ P(right) ≈ 15–17%; every low-vol row has ≈ 5–6% on both sides.**
That is [Addendum 2](D394-ADDENDUM-2-the-oracle-tail-bound.md)'s finding reappearing: **volatility
sets tail thickness symmetrically, and the ER axis does not break the symmetry in any cell.**

The z-scores against the book mean run mostly within ±1.5, with two cells beyond |z| = 2 — about
what 36 cells produce by chance.

**No cell in any window covers the 61.48 bp round trip. The best is less than half of it.**

---

## 6. The answer to the question asked

**"Are there any other combinations that would lend itself to this strategy?"** On this evidence,
**no — not from volatility, path efficiency, or their interaction, at any of four window
definitions including a short/long ratio.**

**What remains untested and would be a genuinely different axis** — each needing its own
pre-registration (D289's fourth amendment):

1. **Path shape measured over the HOLD rather than before it.** Every ER here is backward-looking
   at entry. The prior holding only at window 5 hints the horizon match matters.
2. **Cross-sectional rather than per-name conditioning** — how the name's path compares to its
   peers that day, rather than to its own history.
3. **Something one-sided in the OUTCOME.** Eleven observables now fail the asymmetry test, and the
   working hypothesis from Addendum 3 stands: on this construction the two tails are the same
   phenomenon seen twice.

**None of this closes the avenue — only the principal does (R15).**

---

**Status footer.** Exploratory. No null, no holdout read, nothing admitted, nothing retired.
`docs/BOOK.md` holds S1 and S2, neither at capital; `docs/BOOK_PROP.md` is empty.
