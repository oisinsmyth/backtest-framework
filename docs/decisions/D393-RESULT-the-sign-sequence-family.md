# D393 RESULT — Stage 0: K1 fires for one score of three, and the pre-registration did not anticipate a split

**Status:** RESULT. Stage 0 only. **NO NULL WAS RUN. STAGE 1 IS NOT AUTHORISED — see §4.**
**Date:** 2026-09-08 · Pre-registration: [D393](D393-the-sign-sequence-family.md), committed before
the runner existed. Runner: `scripts/run_d393_sign_sequences.py` · Artifact: `data/d393_stage0.json`
**Holdout reads: 0.** Descriptive; scores nothing, admits nothing (R15).

---

## 0. The verdict

**Q1 held — K1 fires — but only for `up_frac_21`, and the other two scores clear it comfortably.**

Within-bar Spearman, mean over 3,186 bars, on the eligible set:

| | `rev_5` | `rev_21` | `trailing_return` | `mom_252_21` | `rvol21` | K1 |
|---|--:|--:|--:|--:|--:|---|
| **`up_frac_21`** | +0.303 | **+0.601** | +0.448 | +0.058 | −0.111 | **FIRES** |
| `up_run_21` | +0.157 | +0.370 | +0.273 | +0.030 | −0.070 | clears |
| **`sign_flips_21`** | **−0.015** | **−0.025** | **−0.016** | **+0.009** | **+0.004** | **clears** |

**`up_frac_21` is the 21-day return with the magnitude removed** — ρ +0.601 against `rev_21`,
above the 0.5 bar. The share of up days and the sign of the 21-day return are close to the same
statistic, which is what Q1 said would happen and why it was declared against.

**`sign_flips_21` is the most orthogonal score this programme has measured.** Its largest
correlation to *any* of the six references is **0.025**. A count of sign changes shares essentially
nothing with return, momentum or volatility.

**K2 CLEARS** for all three (largest |ρ| **0.114**). **K3 CLEARS** — 2.16 effective inputs of 3
(Li-Ji 3.00), so a run length, a flip count and a mean really are different reductions of the same
sign vector.

---

## 1. Predictions, scored

| | prediction | outcome |
|---|---|---|
| **Q1** | *(against)* K1 fires | **HELD** — `up_frac_21` at +0.601 |
| **Q2** | K2 does not fire; \|ρ\| to `rvol21` under 0.3 | **HELD** — largest 0.114 |
| **Q3** | K3 clears ≥ 2.0 effective inputs | **HELD** — 2.16 |
| **Q4** | *(against)* exposure ≥ 90% — not a flat sleeve | **HELD**, see §2 |
| **Q5** | the book is inside `B_s` | **NOT REACHED** |
| **Q6** | the declared direction holds | **NOT REACHED** |

**Four of four scored predictions held, including both declared against the candidate.**

---

## 2. Exposure — Q4, and it is emphatic

E1 (fresh entry into the bottom decile) over 4,124 defined bars:

| | events | per bar | open at cap 20 |
|---|--:|--:|--:|
| `up_run_21` | 26,236 | 6.36 | **127** |
| `sign_flips_21` | 38,097 | 9.24 | **185** |
| `up_frac_21` | 40,020 | 9.70 | **194** |

**Against ~700 eligible names, none of these is remotely a flat sleeve** — D358's arithmetic
again, and computed before it was predicted as §38 rule 2 requires.

**The atlas floors for the declared pool** (`ALL`, cap 20, long, named in §3 of the
pre-registration before any number was seen): **+11.16, +8.96, +8.67** ± 0.63.

---

## 3. What the runner did NOT do, deliberately

**It did not write the score cache.** `run_d350_long_timing_screen.py:97-102` asserts its pool is
exactly 46 names *and* set-equal to the npz's members; adding a family would make that raise for
D350 and D352, whose 46-name pool and 138-member count are load-bearing in two published records.
The scores were computed in-process through `run_d350.lagged`'s own pipeline with the array passed
in instead of a cache name. **`[C]` asserts `temp/d290_scores.npz` is byte-identical across the
run**, and it is.

**So this is a probe, not a repeatable artifact.** If any of this is promoted, the family has to
enter the cache properly — `AXES["I"]`, `"ABCDEFGH"` → `"...I"` in two places, the `cache_key`
file tuple, and a D371-style merge-rewrite.

**`[T]`** re-ran the truncation audit here rather than trusting the module's self-test: all three
scores causal. **`[L]`** came from `scripts/lag_audit.py` with `raises_on_broken` on an unlagged
mask — **the first record written after that helper existed, and the reason it exists.**

---

## 4. Stage 1 is NOT authorised, and the reason is a gap in my own pre-registration

**§9's stop clause says: *"K1 fires (Q1, expected) → record it and stop."*** K1 fired.

**But it fired for one score of three, and the pre-registration did not contemplate a split.** Its
K1 row says *"it is trailing return with the magnitude thrown away — drop it"*, where "it" is
ambiguous between the score and the family; §7 then prices multiplicity as **10** (2 shapes × 5
caps), which silently assumes **one** score. Two surviving scores make it **20**.

**I am not going to resolve that ambiguity in the direction that lets me continue.** Two readings
are available and only the principal's choice between them is legitimate:

- **Strict:** K1 fired, the record stops, the family is closed. The finding is that the headline
  sign statistic is `rev_21` in disguise.
- **Per-score:** K1 is a per-score kill condition doing its job — `up_frac_21` is dropped and
  `up_run_21` and `sign_flips_21` proceed, at **multiplicity 20** and with the surviving pair
  disclosed as selected by K1 on this data.

**What is NOT available** is sweeping window lengths for a version that decorrelates — §9 forbids
it by name, and it is the search that produced D366's gate.

**My own reading, offered and not acted on:** the per-score reading is defensible — the three
scores were declared in advance, so keeping the two that clear a pre-registered kill condition is
the condition working rather than a search. And `sign_flips_21` at |ρ| ≤ 0.025 against everything
is the most orthogonal input the programme has found, which is exactly what §0 went looking for.
**But that is a ruling, not a measurement, and R15 puts it with the principal.**

---

## 5. What is worth carrying regardless

1. **Magnitude-free does not mean momentum-free — but it depends entirely on which statistic.**
   `up_frac_21` discards magnitude and keeps almost all of `rev_21`'s ordering (+0.601);
   `sign_flips_21` discards magnitude and keeps none of it (−0.025). **"Sign statistics" is not one
   family for this purpose**, and §4.2 of the signal-hunt record treated it as though it were.
2. **A count of sign changes is orthogonal to everything in the catalogue that was tested.** If an
   independent input is wanted for its own sake — a conditioner, a neutralisation axis, a
   diversifier — this is the strongest candidate the programme has measured, and that is true
   whether or not it ever earns anything.
3. **Neither of those makes it a signal.** No forward return was read at Stage 0.

---

**Status footer.** No null run, Stage 1 not run and not authorised. `docs/BOOK.md` holds S1 and S2,
neither at capital; `docs/BOOK_PROP.md` is empty. **Only the principal closes a research avenue —
and here, only the principal opens the remaining half of one (R15).**
