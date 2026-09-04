# D326 — both lenses: is the composite premium a SIGNAL effect or the slot cap?

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. A gap the principal found, and it is worse than a gap

**None of D323, D324 or D325 was scored path-invariantly.** Every one calls
`W.simulate(A, G, DEPTH, True)`, and `slots=True` is the default. The
path-invariant lens exists in that same function, one keyword away, and was never
used.

**These are SIGNAL studies scored entirely through the BOOK.** FINDINGS §10 is
explicit that the path-invariant lens points at the signal and the path-variant
one at the book, and three consecutive signal studies used only the second.

**And at `N_eff` = 2 the slot cap is maximally binding.** D306 measured contention
drag at N = 2 as **−19.12**, the largest magnitude in its table, with negative
meaning *the cap makes the book hold the better names*. So a large part of what
D323 ranked may be **how each signal interacts with a two-slot cap**, not signal
quality.

## 1. The question this settles, and it settles two at once

D325 found a **+0.370** composite premium and I called it synergy. The principal's
reading — that a large, *specific* interaction (the same primary gives +0.454 with
one pair and −0.190 with a stronger one) is evidence of real structure rather than
filtering — is a stronger claim than the record made, and it may be right.

**But specificity is also the signature of overfitting.** There are **858**
(primary, pair) triples over 13 signals; D325 tested six, chosen with knowledge of
the leaderboard, and the incumbent triple was itself selected by a search in
D291/D293.

**The two readings are separable, and this is the test.** If the premium is a
signal effect it should survive **per-trade, no-cap** scoring. If the composite is
really just re-ordering which two names a two-slot cap keeps, **it will vanish.**

## 2. The two lenses, and the rule that governs them

**They are NEVER compared on the same statistic.** FINDINGS §10.

| lens | construction | scored on |
|---|---|---|
| **path-variant** | the slot-limited book, `slots=True` | **net bp/bar**, net Sharpe |
| **path-invariant** | every eligible name held, no cap, `slots=False` | **net per TRADE**, its median and `t`, and mean/`2c` |

**A path-invariant figure is never quoted in bp/bar beside a real book**, and no
row of output carries both. Assertion [3] enforces that structurally.

**Their difference is opportunity cost** — the quantity FINDINGS §10 says nothing
in this programme has measured — and it is reported as its own column, per
construction.

## 3. Cells

- **Constructions:** D325's six composites (`C0`–`C5`) and five singles
  (`hist_L`, `retrace_leg`, `skew_63`, `rsi`, `macd_hist`).
- **`k` ∈ {10, 20, 40}.** **k = 20 is added deliberately** — it is where
  `retrace_leg` peaks after D323's correction and D325's declared grid missed it.
  This discharges D325's owed comparison.
- **`N_eff` = 2, target exit, dv28 off.**
- **11 × 3 × 2 lenses = 66 cells.** Costed per D318 with D321's `[F]`.

**Build risk, declared:** the path-invariant sim holds every eligible name and may
be materially slower. If it is intractable the study is cut to the composites plus
`retrace_leg` and **the cut is named**, not silently taken.

## 4. Cost, per lens

- **Path-variant:** as D318 — held-name round trip × held-name turnover, plus
  IBKR per-share commission.
- **Path-invariant:** the round trip is charged **once per trade**, so
  `net_per_trade = mean gross per trade − rt`. **There is no bp/bar here and none
  is computed.** `2c` is reported beside it, per CLAUDE.md.

## 5. Predictions

Three are against, and Q3 is load-bearing.

| | prediction |
|---|---|
| **Q1** | every path-variant cell reproduces D325 and D323 to floating point. **A harness check** |
| **Q2** | the path-invariant book takes **strictly more trades** and holds strictly more names at every cell. **A harness check on the lens itself** |
| **Q3** | **C4's path-invariant net per trade does NOT exceed `retrace_leg`'s.** *Against — load-bearing.* If the +0.370 premium is the cap, it vanishes when the cap is removed |
| **Q4** | **the path-invariant lens ranks the five singles differently from the path-variant one** — Spearman below +0.7. *If the cap is driving D323's ranking, this is where it shows* |
| **Q5** | opportunity cost — variant minus invariant, per trade — is **positive** for every construction, reproducing D306's finding that the cap *helps* at this width |
| **Q6** | **`retrace_leg` alone at k=20 beats every composite on the path-VARIANT lens**, discharging D325's owed comparison. *Against the composite construction surviving* |
| **Q7** | **the pair effect shrinks path-invariant** — the C0-minus-C3 gap, −0.644 in the book, is materially smaller per trade. *If "which signals combine" is a cap effect rather than a signal one, this is the direct test* |

## 6. Stop conditions

- **Q3 confirms and Q7 confirms** → the composite premium and the pair
  specificity are both **path effects**. The confluence is a way of choosing which
  two names a cap keeps, not a signal interaction, and **D325's synergy reading is
  withdrawn.**
- **Q3 fails** → the premium survives without the cap. **That is a real signal
  interaction**, the principal's reading is right, and the next question is
  whether it is predictable *ex ante* — pair correlation, orthogonality, or
  D291's unused `disagree` term.
- **Q6 fails** → a composite beats the best single on its own best `k`, which
  D325 could not test. It needs its own confirmation.
- **Q1 or Q2 fails** → the lens is misimplemented; nothing else is read.

## 7. Assertions

1. **[1] Reproduction.** Path-variant cells reproduce D325's composites and
   D323's singles to floating point.
2. **[2] THE LENS BITES.** The path-invariant book holds strictly more names per
   bar and takes strictly more trades than the path-variant one, at every cell.
   **A lens that changes nothing is not a lens.**
3. **[3] THE LENSES ARE STRUCTURALLY SEPARATED.** No output record carries both a
   bp/bar figure and a per-trade figure, and the runner must **raise** if asked to
   rank one lens's cells by the other's statistic. FINDINGS §10's rule is enforced
   in code, not in prose.
4. **[4] CAUSALITY.** Scores are lagged, and a time-rotated `rankT` must move both
   lenses.
5. **[F] FILL** — path-variant turnover on names held; the nominal-slot form
   rejected.
6. **[S] SPREAD BASIS** — each round trip is 4× its own held-name median and
   spans across cells.
7. **[C] Cost dimensions** against d295's 52.1893; doubled form rejected.
8. **[5] The self-test raises** on a book handed free money inside the mask.

## 8. Scope

**Out:** width; the exits beyond inheriting `target`; dv28; any construction
outside D325's six composites and the five named singles; the 38 unread D290
candidates; and the holdout.

**This study cannot promote anything.** It re-scores existing constructions
through a lens that should have been used three studies ago. **Its output is a
correction to how D323, D324 and D325 should be read**, and if Q3 confirms, three
records need amending.

## 9. Files

`docs/decisions/D326-both-lenses-on-the-composite-premium.md` (this record) ·
runner and data to follow, in separate commits. Prior evidence:
`data/d323_shortlist.json`, `data/d325_composites.json`,
`data/d306_width_exits.json`.
