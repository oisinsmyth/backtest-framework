# D254 — The wedge breakout on crypto

**Status:** Pre-registered — committed BEFORE the runner exists
**Date:** 2026-08-28
**Area:** Strategy research

---

## Why this study exists, and it is a mechanism test before it is a strategy test

The principal's hypothesis, extended by him to breakouts:

> **A breakout needs continuation, and continuation comes from asset-specific information being
> incorporated gradually. A weighted average cancels exactly that** — constituents break out in
> different directions at different times and the basket smooths it. **An ETF can only break out
> if the whole market does**, which is rare, universally watched, and mean-reverting because it is
> the risk premium.

**The same mechanism that kills shorts on baskets kills breakouts on baskets, for the same reason.**

**The programme has already run the natural experiment and never joined it up:**

| | outcome |
|---|---|
| [D249](D249-the-inverse-wedge-breakout.md) — wedge breakout, 57 ETFs | **failed its rotation null 3/3 on the screen and 3/3 on the holdout** |
| [D140](D140-crypto-universe-selection-policy.md)–D144 — breakout, 63 coins | **real, and concentrated in the assets that DIED** — 67% of wrecks beat matched exposure against 45% of survivors |

Same machinery family, opposite outcomes, and the split falls exactly on the basket/single-asset
line. **This study tests whether that split reproduces under one construction rather than two.**

---

## The rule — D249's, frozen, only the fixture changes

```
armed     converging (g_hi < g_lo) AND channel width <= 2 ATR
trigger   C[t] crosses a level fixed at t-1: centre +/- 2 ATR
U_long    long  the UP break        (D249 measured this leg as flat on ETFs)
D_long    long  the DOWN break      (D249's registered inverse -- FAILED on ETFs)
D_short   short the DOWN break      (the proposal's original leg)
```

`K = 3`, window 252, `ARM_ATR = 2.0`, `ATR_WINDOW = 21`, hold 21 bars. **No parameter is varied.**
`wedge_signals` and the trigger convention are imported unmodified from `run_wedge_inverse.py`.

**Fixture:** [D244](D244-the-book-on-crypto.md)'s frozen 34-coin panel, as [D253](D253-the-book-short-sides-on-crypto.md)
used. `PPY = 365`, `FEE_BPS = 10`, `BORROW = 10%/yr` — the same three overrides, asserted off
outside the block.

**Scoring is D253's pooled model B** (one account, 1/n per coin), because model A ruins on this
universe. **It flatters the arms** — costless continuous rebalancing, no intra-bar margin call —
and the model-A ruin is reported beside it.

---

## The anatomy carries as much weight as the cells

Before any book is scored, the **forward-return table** is computed exactly as D249's was, R9- and
R10-compliant, so it can be set beside the ETF numbers directly:

| horizon | ETF up-break | ETF down-break | ETF spread |
|---:|---:|---:|---:|
| 5 | +6.47% | +14.55% | **−8.08%** |
| 21 | +8.33% | +15.29% | **−6.96%** |
| 42 | +9.47% | +18.31% | **−8.84%** |
| 63 | +8.00% | +18.04% | **−10.05%** |

**On ETFs the spread is negative at every horizon** — down-breaks are the better thing to be long.
**If the mechanism is right, crypto's spread should be positive.** That single sign is the
cleanest test in this record.

---

## Two predictions, both committed before the run

**The principal's:** *"I predict it will at least beat the nulls."*

**Mine, and I agree with him on the headline while expecting it not to matter:**

| | prediction | confidence |
|---|---|---|
| **X-1** | **At least one cell beats its matched-count rotation null at p95 on Sharpe.** Agreeing with the principal | **~70%** |
| **X-2** | **The up/down spread flips sign against ETFs — up-breaks beat down-breaks on crypto.** The direct test of the mechanism | **~70%** |
| **X-3** | **Hurdle E fails on every cell.** 34 coins over ~5 years cannot give 30 entries per name when D249 got a minimum of 5 from 57 ETFs over 12.8 years | **~90%** |
| **X-4** | **`D_short` posts a NEGATIVE CAGR even where it beats its null**, killed by the `sigma^2` convexity drag D253 measured at −58.90%/yr for a permanent short here | **~80%** |
| **X-5** | **R10 concurrency reaches ≥30 of 34 names at once**, against a far lower rotated maximum | **~75%** |

**The meta-prediction, stated plainly: the principal wins his bet and it still is not a strategy.**
D253 is the template — S1_short cleared hurdle H at the **98.7th percentile** and returned
**−10.12%/yr**. **Beating a rotation null demonstrates timing skill; it says nothing about whether
the instrument can be traded.** D253's recorded defect applies here in advance: **H is a skill
test, not a viability test**, so this record adds a viability bar up front.

**What would make me wrong in an interesting way: X-2 failing.** If crypto down-breaks also
outperform up-breaks, the mechanism does not explain the ETF result and the whole line needs
rethinking rather than extending.

## Hurdles

- **H.** Matched-count rotation null at **p95 on Sharpe AND money**, both legs (R10's second
  corollary). Best-of-three floor per D228.
- **V — new, and added because D253 needed it.** A cell is **not** reported as a success unless it
  also posts a **positive net CAGR** after fees, financing and the assumed borrow. **H without V
  is a skill measurement, not a result.**
- **E.** ≥100 pooled and ≥30 entries per symbol.
- **R10 concurrency**, actual against per-symbol-rotated, plus effective instruments.
- **Model-A ruin** reported per cell: worst adverse bar, and the maximum survivable notional.

## Stop

**If no cell clears H *and* V, this is CLOSED.** No parameter sweep, no second arming threshold,
no move to the ragged 63-name universe. The anatomy's sign is recorded either way, because X-2 is
a mechanism finding independent of whether any cell is tradeable.

## Ledger

| count | N |
|---|---:|
| fresh — 3 cells | 3 |
| + the anatomy: 2 directions x 4 horizons | 11 |
| + carried from D253 | 45,957 |
| **total** | **45,968** |
