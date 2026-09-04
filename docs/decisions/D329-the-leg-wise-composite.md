# D329 — the leg-wise composite: `hist_L` owns the long leg, `skew_63` owns the short

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

*The number D329 was earlier reserved for an additive composite predictor built
from single-signal rank profiles. That study was cancelled by D328's stop
condition and never filed. This is a different construction with a different
basis, and it takes the number.*

---

## 0. Why this construction, and why now

Every composite this programme has built — D295, D325 — re-ranks **one gate
symmetrically**: the same score picks both legs. **Nothing has ever let one
signal choose the longs and a different signal choose the shorts.**

D328 §11 gives that construction a mechanism. Under the book's own convention —
equal-weight, daily-rebalanced, the sum of one-bar returns — the two legs of
one signal are not symmetric:

| | long leg | short leg | held price |
|---|--:|--:|--:|
| **`hist_L`** rebalancing premium, k=20 | **+78 bp** | **−85 bp** | $8–10 |
| `skew_63` | +20 | **−2** | $21–33 |

A rebalanced long on a bouncy name harvests volatility; a rebalanced short on
the same name pays it. `hist_L` selects bouncy names at both ends, so its short
leg is short the premium. `skew_63`'s short end sits in $30 names at 5–8 bp
half-spread, where there is no premium to pay — and it is the strongest genuine
short-end `t` in D328 (−6.43 at rank 0). `hist_L`'s long end is the strongest
long-end `t` (+2.96, +3.84). **D290's independent per-leg books agree**:
`hist_L`'s best short-only cell is −19.8, `skew_63`'s +116.9.

So the construction is not a search. Each signal is given the leg the per-leg
profile, the rebalancing premium and D290 all say it owns.

## 1. The construction, and what is exact by construction

`rank_single` (D323) returns a `(2, T, n)` array: side 0 is the long-leg rank,
side 1 the short-leg rank. The leg-wise composite is

```
rankT_LW = stack([ rank_single(hist_L)[0],  rank_single(skew_63)[1] ])
```

**`W.simulate` processes the two sides independently** — separate holdings,
separate gate slice, separate cap `depth − len(held)` per side, no
cross-side state. Therefore, in **both** lenses, the leg-wise book's long-leg
trades are **bit-identical** to `hist_L`'s long-leg trades and its short-leg
trades to `skew_63`'s. **Per-leg additivity is not a prediction here; it is
assertion `[L]`.** Anything that is a *sum over trades* — the invariant lens —
composes exactly. What does **not** compose is the book-level path: the bar
series `ret[0] − ret[1]`, its Sharpe, its drawdown, and its costed turnover.
That is where the predictions have content.

## 2. Arms

All at `DEPTH = 2`, `k ∈ {10, 20, 40}`, D306's k-bar horizon, D318 costing on
the variant lens, D326's per-name `2c` on the invariant — **identical to D326**
so the parents reproduce its cells.

| arm | long leg | short leg | role |
|---|---|---|---|
| **H** | `hist_L` | `hist_L` | parent |
| **S** | `skew_63` | `skew_63` | parent |
| **LW** | `hist_L` | `skew_63` | **treatment** |
| **RV** | `skew_63` | `hist_L` | reverse — *against*, each signal on the leg it does not own |

**Both lenses, never compared on the same statistic** (FINDINGS §10; D326's
`rank_cells` guard reused).

## 3. The control: enumerate the partner, do not randomise the membership

CLAUDE.md: a random subset is never a control for a persistent selector;
randomise the *partner*. Here the partner is a whole signal, so the control is
**deterministic enumeration**, not draws:

- **Direction A:** `hist_L` long + **each of the 46** dimensionless D290
  signals short (the 51 less `macd_line`, `macd_hist`, `impulse_nodz`,
  `amihud_21`, `price_log`, excluded by the D328 units audit because they rank
  price or dollar volume). `skew_63` is one of the 46; `hist_L` itself is the
  parent H.
- **Direction B:** **each of the 46** long + `skew_63` short.

At **k=20 only**, both lenses. Every partner is a *real* signal's *real* leg,
so the control shares the treatment's persistence, tilt and cost nuisance. It is
conservative: some partners are genuinely good legs. **p50 and p95 of the 46 are
reported beside the treatment** (R7).

## 4. Predictions

Q1 and Q4 are load-bearing. Q6 is against. Q5 tests the mechanism independently
of who wins.

| | prediction |
|---|---|
| **Q1** | **LW beats BOTH parents** — on invariant net per trade at every k, and on variant net Sharpe at k=20. *Load-bearing.* |
| **Q2** | Per leg, invariant, every k: `hist_L`'s **long** leg nets more per trade than `skew_63`'s long leg, and `skew_63`'s **short** leg nets more than `hist_L`'s short leg. *Because of `[L]`, Q1's invariant half is exactly Q2; it is stated separately so a partial failure names the leg.* |
| **Q3** | LW's variant **net maxDD is shallower than H's** at k=20, and its net Sharpe exceeds the better parent by **more than 0.10** — the legs of two different signals are less correlated than the two legs of one. |
| **Q4** | **`skew_63` is in the top 3 of 46 short partners** for `hist_L`-long on invariant net per trade, and **`hist_L` is in the top 3 of 46 long partners** for `skew_63`-short. On variant net Sharpe, both in the top 5. *Load-bearing with Q1: Q1 without Q4 means any decent short leg would do.* |
| **Q5** | **The rebalancing premium per trade** (summed ledger P&L minus the compounded P&L recomputed on the same bars, signed for the side), k=20: H's short leg **below −40 bp**, H's long leg **above +40 bp**, LW's short leg **within ±15 bp**. *The mechanism, read directly off the trades.* |
| **Q6** | **RV is worse than BOTH parents** on invariant net per trade at every k and on variant Sharpe at k=20. *Against.* |
| **Q7** | LW's held **long-leg** median half-spread exceeds 30 bp and its **short-leg** median is below 12 bp; its long-leg median price is below half its short-leg median price — a **monotone** tilt across the legs, the paying direction (FINDINGS §14). Its paired round trip is below H's. |

## 5. Stop conditions

- **Q1 and Q4 confirm** → leg ownership is real and specific. LW becomes a
  **stack candidate for a separate pre-registered test** (R8). It does **not**
  enter the book on this.
- **Q1 confirms on the invariant lens and fails on the variant** → the legs
  compose per trade but not as a book: correlation or beta mismatch. A sizing
  question, not a signal one.
- **Q1 fails** → per-leg profiles do not compose into a book, and the D290
  per-leg agreement was coincidence.
- **Q4 fails with Q1 confirmed** → `hist_L`-long carries the effect and the
  short partner is interchangeable. Then the finding is about `hist_L`'s long
  leg, not about `skew_63`.
- **Q5 fails** → the rebalancing mechanism in D328 §11 is wrong, and the
  reinstatement of D327 §2 must be re-examined.
- **Q6 fails** → the effect is not leg ownership; something else in the pairing
  is doing the work.

## 6. Assertions

1. **[L] LEG INDEPENDENCE.** LW's side-0 trade ledger is bit-identical to H's
   side-0 ledger and its side-1 to S's side-1, in **both** lenses; its variant
   bar series `ret[0]` equals H's and `ret[1]` equals S's exactly. *This is the
   composition, proven not assumed.*
2. **[P] THE LEDGER SPANS THE BARS I THINK IT DOES.** Recomputing each trade's
   summed P&L from `(row, entry, age)` on `r1T` and `mkt` reproduces the
   ledger's `pnl` to 1e-12. Only then is the compounded recomputation for Q5
   on the right bars.
3. **[1] HARNESS IDENTITY.** The variant lens reproduces D326's H and S cells
   to 1e-9.
4. **[3] THE LENSES ARE SEPARATED IN CODE** — D326's `rank_cells` raises in both
   directions.
5. **[C] COST DIMENSIONS.** Per-leg `2c` is 2 × that leg's held median
   half-spread; the paired 4× is rejected. Book round trip is the sum of the
   two legs' `2c`.
6. **[4] CAUSALITY.** A rolled `rankT` changes both lenses.
7. **[R] RV IS A DIFFERENT BOOK** from LW — trade sets differ on both sides.
8. **[6] THE SELF-TEST RAISES** on a book handed free money.

*Every assertion is a property of the code. None asserts what the data will
show — that is what §4 is for (D328 `[5]`, D327 `[1]`, D324 `[S]`).*

## 7. Scope

**Out:** a constant-shares short leg — the direct sizing fix D328 §11.3
implies — because it changes the simulator's P&L accumulation and deserves its
own record; composites of more than two signals; any partner outside the 46;
exits beyond D306's k-bar horizon; the overlay; the holdout.

**In:** the four arms at three k, both lenses; the 92-cell partner enumeration
at k=20, both lenses; the per-trade rebalancing premium on every arm.

## 8. Files

`docs/decisions/D329-the-leg-wise-composite.md` (this record) · runner and data
to follow, in separate commits. Prior evidence: `data/d326_both_lenses.json`,
`data/d328_profile_at_depth.json`, `data/d328b_profile_at_depth_compounded.json`,
`data/d290_stage1.json`, D328 §11.
