# D325 — composites of the new leaders, and whether the premium is synergy or repair

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

> ## AMENDMENT, 2026-09-04 — the declared set named a leader that is not one
>
> **§3's composites were chosen from a defective leaderboard.** D323's
> `rank_single` shorted the *least* extreme names of its own gate; the corrected
> re-run moves the ranking substantially and **`rev_21` falls from 2nd (+0.498) to
> 9th (+0.207)**. It appears in **C2** and **C4**, and both are therefore built on
> a candidate that is no longer a leader.
>
> ### The corrected top four
>
> | | net Sharpe | k | dv | held ½s | p |
> |---|--:|--:|--:|--:|--:|
> | **retrace_leg** | **+0.625** | 20 | n | 19.76 | 0.0198 |
> | **rsi** | **+0.585** | 10 | n | 14.55 | 0.0099 |
> | **macd_hist** | **+0.482** | 40 | Y | 20.01 | 0.0396 |
> | **skew_63** | **+0.467** | 40 | n | 8.29 | 0.0198 |
> | *(incumbent)* | *+0.549* | 10 | Y | — | — |
> | *hist_L alone* | *+0.293* | 40 | Y | 20.01 | 0.0792 |
>
> ### The substitution is MECHANICAL, and the roles are unchanged
>
> **`rev_21` → `skew_63`, and nothing else moves.** Each composite keeps the
> structural role §3 assigned it, so this is a substitution rather than a fresh
> search over the corrected table.
>
> | # | primary | pair | role — unchanged |
> |--:|---|---|---|
> | **C0** | hist_L | macd_hist, rsi | the incumbent |
> | **C1** | retrace_leg | macd_hist, rsi | swap the primary, hold the pair |
> | **C2′** | **skew_63** | macd_hist, rsi | swap the primary, hold the pair *(was rev_21)* |
> | **C3′** | hist_L | retrace_leg, **skew_63** | hold the primary, swap the pair *(was rev_21)* |
> | **C4′** | retrace_leg | **skew_63**, rsi | all three strong *(was rev_21)* |
> | **C5′** | rsi | retrace_leg, **skew_63** | strongest pair member promoted *(was rev_21)* |
>
> ### The caveat this creates, stated rather than buried
>
> **The original set was chosen on defective numbers; this set is chosen on the
> corrected numbers, which are the same numbers the study will score against.**
> There is selection either way and the mechanical substitution limits it without
> removing it. **Any cell that wins here is the product of a set chosen with
> knowledge of the leaderboard**, and its confirmation must be on a construction
> this set was not drawn from.
>
> ### And one prediction is now nearly settled before the run
>
> **The incumbent is a WEAK primary carrying two STRONG pair members.** `hist_L`
> is 7th at +0.293 while `macd_hist` (+0.482) and `rsi` (+0.585) are both top
> four. **That is the repair hypothesis visible in the leaderboard**, and Q3 —
> that the premium shrinks as the primary strengthens — is now the prediction to
> beat rather than a speculation. It stays load-bearing and against.

---

## 0. A closure I claimed and withdrew

D324's record ends *"the entry axis closes for a reason that is not Sharpe."*
**The principal challenged that and it is withdrawn.**

D323 tested **13 candidates as SINGLE signals, at one width, from one shortlist.**
That is not the entry axis. Untouched: composites; the 11 other survivors of
D290's screen; the 27 candidates D290 *rejected* at widths D323 has now shown
invert the ranking; the confluence's own `FRAC`, `N_BASE` and pair choice; and any
signal not already mined.

**D324's Q3 and Q4 do generalise** — four different signals all needed ≤ 6 names
for half their P&L and all put > 51% of it in the cheapest tercile, so the
*fragility* is book-level. **I conflated "the fragility is structural" with "the
entry axis is exhausted".** They are different claims and only the first is
supported.

This is the third recorded instance of that error and it is the one my own memory
file names.

## 1. The gap this study takes, and why it is the largest one

**The incumbent is a composite and every candidate was tested alone.**

```
hist_L ALONE, at the operating point        +0.262      (11th of 13, D323)
the confluence built ON hist_L              +0.549
                                            -------
the composite premium                       +0.287
```

**That is the largest signal-level effect this programme has measured** — larger
than the spread between the top four singles (0.076), larger than dv28 (+0.173),
larger than anything the width work produced. **And no composite of the new
leaders has ever been built.**

## 2. The mechanism question, which is sharper than the horse race

**Why does the confluence beat its own primary by +0.287?** Two hypotheses, and
they predict opposite things:

**(a) SYNERGY.** Averaging quasi-independent signals cancels noise, so a composite
beats any component. **Then a composite of the three STRONG singles should be the
best book in the programme.**

**(b) REPAIR.** `hist_L` is a weak primary and the pair rescues it; the premium
measures how bad the primary was, not how good the combination is. **Then a
composite built on a STRONG primary shows little or no premium**, and the
incumbent's +0.287 is not repeatable.

**D324 already gave evidence for (b) on a different axis:** the confluence puts
51.5% of its P&L in the cheapest tercile where `rsi` alone puts **89.4%** — the
composite *dilutes* its components rather than compounding them.

**Q3 enters (b) as the load-bearing prediction, against the study.**

## 3. The declared composites — six cells, no search

The construction is D295's `build_inputs`, unchanged: a **primary** selects the
25-name gate, and a **pair** re-ranks inside it by mean percentile.

| # | primary | pair | tests |
|--:|---|---|---|
| **C0** | hist_L | macd_hist, rsi | **the incumbent** — the baseline |
| **C1** | retrace_leg | macd_hist, rsi | swap the primary, hold the pair |
| **C2** | rev_21 | macd_hist, rsi | swap the primary, hold the pair |
| **C3** | hist_L | retrace_leg, rev_21 | hold the primary, swap the pair |
| **C4** | retrace_leg | rev_21, rsi | **all three strong** — synergy's best case |
| **C5** | rsi | retrace_leg, rev_21 | the strongest pair member promoted |

**Six composites and nothing else.** The four singles (`hist_L`, `retrace_leg`,
`rev_21`, `rsi`) are carried as **reference rows only**, re-read from D323, not
re-searched.

## 4. Cells and statistics

- **`N_eff` = 2**, target exit, no overlay, **dv28 OFF** — D323's Q7 showed dv28
  is fitted to the confluence and the strong singles prefer it off.
- **`k` ∈ {10, 40}**: the incumbent's best and `retrace_leg`'s best. Two values,
  declared, not swept.
- **12 cells.** Costed per D318 with D321's `[F]` held-name turnover.

**Net Sharpe is primary, AND D324's two composition statistics are co-primary** —
names to half the P&L, and the low-price tercile's share. **D324 established these
diverge from Sharpe**, and a composite that wins on Sharpe while pushing the
low-price share from 51.5% toward `rsi`'s 89.4% has not improved the book.

**A composite must beat the incumbent on net Sharpe AND not be worse on the
low-price share to count as a win.** Declared now, before the numbers.

## 5. The null

**D323's circular time rotation of `rankT`**, 100 draws per cell, which moved
`hist_L`'s gross from +24.62 to +10.90 and so has teeth. **BH-FDR at the
EFFECTIVE test count** (D321's amendment, D323b's pairwise-complete method) with
the nominal reported beside it.

## 6. Predictions

Three are against, and Q3 is load-bearing.

| | prediction |
|---|---|
| **Q1** | **C0 reproduces D323's incumbent cells at k=10 and k=40 to floating point**, and a composite whose pair is set equal to its primary reproduces that primary's single-signal book. **Two harness checks, and the second is the one that proves the composite machinery is right** |
| **Q2** | every composite beats its own primary alone — the premium is real for all six |
| **Q3** | **the premium SHRINKS as the primary gets stronger: C1, C2, C4 and C5 each show a smaller premium over their own primary than C0's +0.287.** *Against — load-bearing.* This is hypothesis (b) |
| **Q4** | **no composite beats the incumbent on net Sharpe AND holds its low-price share at or below 51.5%.** *Against* |
| **Q5** | **C4, the all-strong composite, is NOT the best cell.** *Against — it is synergy's best case and hypothesis (b) says it will disappoint* |
| **Q6** | every composite's low-price share sits **between** its components' — the dilution D324 measured is general, not specific to C0 |
| **Q7** | C3 (hold `hist_L`, swap the pair) beats C0. If the pair is doing the work, a stronger pair should help more than a stronger primary |

## 7. Stop conditions

- **Q3 confirms and Q4 confirms** → the composite premium is **repair, not
  synergy**; the incumbent is not beatable by recombining this shortlist; and the
  next move is the **unread 38 candidates**, not more composites of the read 13.
- **Q3 fails** → synergy is real and composites of strong signals compound. **That
  reopens the entry axis properly** and needs its own confirmation.
- **Q4 fails** → a composite genuinely improves the book on both axes. It is a
  candidate, not a promotion, and R8 applies.
- **Q1 fails** → the composite machinery is wrong and nothing else is read.

## 8. Assertions

1. **[1] Reproduction.** C0 reproduces D323's `incumbent/k10/dv0` and `k40/dv0`
   gross and net to floating point.
2. **[1b] THE DEGENERATE COMPOSITE.** A composite with `pair = (primary, primary)`
   must reproduce that primary's single-signal book **bit-identically**. The mean
   percentile of a signal with itself is its own percentile, so the re-ranking
   collapses to the primary's own order. **If this fails, the composite and single
   paths are not comparable and no cell in this study means anything.**
3. **[2] CAUSALITY.** Every score is lagged in `R.ranked`, and a time-rotated
   `rankT` must produce a different book.
4. **[F] FILL** — turnover on the names held; the nominal-slot form rejected.
5. **[S] SPREAD BASIS** — each rt is 4× its own held-name median, and the rt
   spans materially across cells. **Not** "exceeds the universe median", which
   D324 showed asserts a property of the data rather than the code.
6. **[C] Cost dimensions** against d295's 52.1893; doubled form rejected.
7. **[3] Every cell is a distinct book**, and **C0 ≠ C1 ≠ C4** in particular.
8. **[4] The self-test raises** on a book handed free money inside the mask.

## 9. Scope

**Out:** any primary or pair member outside `{hist_L, macd_hist, rsi,
retrace_leg, rev_21}`; `FRAC` and `N_BASE`; width; the exits; dv28; the 38 unread
D290 candidates — they are the *next* study if Q3 confirms, not this one; and the
holdout.

**This study cannot promote anything.** Six composites is a small declared set
chosen to separate two hypotheses, not to find a maximum. **If it finds one, that
maximum is the product of a six-cell search and must be treated as such.**

## 10. Files

`docs/decisions/D325-composites-of-the-new-leaders.md` (this record) · runner and
data to follow, in separate commits. Prior evidence: `data/d323_shortlist.json`,
`data/d323b_analysis.json`, `data/d324_composition.json`.
