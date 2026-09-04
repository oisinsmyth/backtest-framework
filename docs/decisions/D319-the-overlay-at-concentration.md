# D319 — the overlay at concentration, and whether its denominator is the problem

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 1. Why this runs before the tilt study

**The overlay is the largest Sharpe effect this programme has produced** —
D297 measured gross Sharpe **+0.512 → +0.728 (+42%)** and maximum drawdown
**−62%** (9,374 → 3,607 bp) while *earning more* in absolute terms, at
**p = 0.0150** against a rate- and persistence-matched null. Four contiguous
thresholds cleared (X = 11, 12, 13, 14) — a hump, not the knife-edge that burned
`hist_L` at N = 25.

**And it is ruled out at the operating point by one cell at one threshold.**
D306 tested X = 12 only, at N = 2, and D318's re-costing puts it at **−3.37
bp/bar**. That is a single point deciding the fate of the biggest effect here.

## 2. There is a named mechanism, not just a suspicion

The overlay's trigger, from `run_d297_overlay.schedule`:

```
shadow = cumsum(book returns)          peak = running max through t-1
dd     = peak - shadow[t-1]
off    = dd >= X * trailing_vol(book)      <- DE-RISK
```

**The threshold is denominated in the book's OWN trailing volatility.** And
[D312 §0](D312-RESULT-the-estimator-not-the-premise.md) measured exactly that
quantity's quality by width:

| | forward-63 correlation of the book's own trailing vol |
|---|--:|
| `N_eff` = 19 | **+0.347** |
| `N_eff` = 10 | +0.185 |
| `N_eff` = 5 | +0.056 |
| **`N_eff` = 2** | **−0.016** |

**At the width the book runs, the overlay divides by noise.** That is a specific,
falsifiable reason for D306's −3.37 that has nothing to do with the overlay's
logic being wrong — and **D313 already measured a replacement denominator**:
universe cross-sectional dispersion, **+0.352 at `N_eff` = 2**.

**So this study is not a parameter search.** It asks whether a measured defect in
one input explains a failed cell, using a replacement that was measured before
this study was designed.

## 3. Arms

| arm | trigger denominator |
|---|---|
| **C — control** | no overlay |
| **O_own** | the book's own trailing vol — **D297's rule as built** |
| **O_univ** | `c(t) × universe cross-sectional dispersion`, D313's mapping, causal |

`O_univ` reuses **D313's declared predictor `xs_all`** and its 252-bar trailing
median calibration `c(t)` unchanged. **No new predictor is introduced and none is
searched** — D313 compared six and this study inherits the one it declared.

## 4. Grid

- **Widths** `N ∈ {2, 3, 19}` — the operating point, the gradient, and **N = 19
  as the reproduction anchor** that must reproduce D297 and D306.
- **Thresholds** `X ∈ {6, 8, 10, 11, 12, 13, 14, 16, 18, 20, 25, 30}` — D297's
  own fine grid, unchanged.
- **Bases** `none` and `target`.
- `s = 0.0` only. D297 measured `s = 0.5` as worse at every X and adding it
  doubles the grid for an axis already answered.

The overlay scales the return series and does not touch holdings, so **the whole
grid needs 6 simulations** and the rest is arithmetic (D306's structure).

## 5. Statistics — and the trap that must not be repeated

**Net Sharpe is primary.** The overlay cuts exposure to ~70%, and scoring it on
net bp/bar penalises it for being out of the market — the error D301's null column
made and which made its two overlay rows uninterpretable.

**Return per unit exposure is reported beside it** (D297's `ret/exp`), along with
net bp/bar, gross Sharpe, maxDD, exposure and transition count.

**Costed per D318:** common round trip within a width, per-cell across widths,
plus IBKR per-share commission on the held median price. **The published `sharpe`
columns of D306 and D310 are GROSS Sharpes; every Sharpe in this study is net and
labelled.**

## 6. The null

**D297's rate- and persistence-matched null on the on/off series** — the same
number of de-risking episodes with the same run-length distribution, at unrelated
times. 200 draws, BH-FDR at q = 0.10 across the tested cells.

**D318 noted that re-costing reorders cells, so D300/D306's published p-values no
longer attach to them.** Every cell here gets its null run fresh.

## 7. Predictions

Three are against, and Q5 is load-bearing.

| | prediction |
|---|---|
| **Q1** | at N=19, X=12, `O_own` reproduces D297's +0.728 gross Sharpe and D306's cell to floating point. **A harness check — if it misses, nothing else is read** |
| **Q2** | the denominator's forward-63 correlation reproduces D312's −0.016 / +0.347 at N=2 / N=19. Also a harness check, and the mechanism's premise |
| **Q3** | **`O_own` clears at NO X at N = 2** — D306's single cell generalises across the whole sweep. *Against the study* |
| **Q4** | **`O_univ` beats `O_own` at N = 2 at the matched X = 12.** *For the mechanism* — if the noisy denominator is the defect, replacing it must show |
| **Q5** | **neither overlay arm beats the no-overlay control at N = 2 on net Sharpe, at any X.** *Against — load-bearing.* The overlay's value was width-specific, not denominator-specific |
| **Q6** | D297's hump over X ∈ [10,16] reproduces at N = 19 and **no hump exists at N = 2 for `O_own`** — its Sharpe is flat or monotone in X |
| **Q7** | exposure at the best X is within 10 points of 70% at every width, so a failure at N = 2 is **not** a difference in how often the rule fires |
| **Q8** | `O_univ`'s advantage over `O_own` is **largest at N = 2 and smallest at N = 19**, tracking where the two denominators' quality diverges (−0.016 vs +0.352, against +0.347 vs +0.410). *This is the prediction D313's Q8 got backwards, entered again on a different rule* |

## 8. Stop conditions

- **Q3 and Q5 both confirm** → the overlay is **width-specific**, closed at the
  operating point, and the programme's largest Sharpe effect is unavailable where
  the book actually runs. **Expected.**
- **Q3 fails** — some X clears at N=2 with `O_own` → D306's single cell was a
  threshold artefact, the overlay is back in, and it needs its own confirmation
  before anything else.
- **Q4 confirms and Q5 fails** → the denominator was the defect, D313's universe
  predictor has a use after all, and the overlay works at N = 2 with it. **This is
  the outcome that would matter most and I am not predicting it.**
- **Q1 or Q2 fails** → misimplemented; nothing else is read.

## 9. Assertions

1. **[1] Reproduction.** `N=19/none+overlay` at X=12 reproduces D306's published
   cell and D297's Sharpe to floating point.
2. **[2] CAUSALITY.** `schedule`'s peak and vol read only through `t−1`, and
   D297's own `lag=False` variant **must produce a different book**.
3. **[3] The universe denominator is causal** and its stage-0 statistics reproduce
   `data/d312_universe_forecast.json` exactly.
4. **[4] Exposure and transition cost** are charged: `Σ|Δscale|/2 × rt`, zero on a
   constant scale, monotone in the number of transitions.
5. **[S] SPREAD BASIS.** The round trip is computed from the names held, reported
   per-cell **and** common, and the check **FAILS against the universe median**.
   *New, and owed since D317.*
6. **[5] Every cell is a distinct book.**
7. **[6] The null matches** on episode count and run-length distribution.
8. **[C] Cost dimensions** against d295's 52.1893, doubled form rejected.
9. **[7] The self-test raises** on a book handed free money inside the mask.

## 10. Scope

**Out:** the entry signal; the target's own parameter; the gate; `k`; width beyond
the three anchors; `s`; and any predictor other than D313's declared `xs_all`.

**This tests one input to one rule at three widths.** If `O_univ` works it is a
candidate, not a result, and R8 applies in full.

## 11. Files

`docs/decisions/D319-the-overlay-at-concentration.md` (this record) · runner and
data to follow, in separate commits. Prior evidence:
`data/d297_*.json`, `data/d306_width_exits.json`, `data/d312_universe_forecast.json`,
`data/d318_stack_recost.json`.
