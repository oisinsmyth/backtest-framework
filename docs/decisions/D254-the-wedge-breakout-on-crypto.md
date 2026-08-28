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

---

## RESULT — CLOSED. X-2 falsified, and it is the most useful thing in this record.

**Produced:** 2026-08-28 · `uv run python scripts/run_wedge_crypto.py` · page
`WEDGE_CRYPTO_RESULTS.md` · 34 coins x 2,899 bars, 5.20 live years, armed on **12.43%** of live
cells, effective instruments **1.80**.

### X-2 — the load-bearing number, and it went the wrong way

| horizon | **crypto up** | **crypto down** | **crypto spread** | *ETF spread* |
|---:|---:|---:|---:|---:|
| 5 | +80.62% (3,490) | +81.40% (2,409) | **−0.78%** | *−8.08%* |
| 10 | +54.96% | +32.28% | **+22.67%** | *−2.16%* |
| 21 | −1.52% | +18.70% | **−20.22%** | *−6.96%* |
| 42 | −36.39% | +7.91% | **−44.30%** | *−8.84%* |
| 63 | −43.95% | +18.55% | **−62.50%** | *−10.05%* |

**The crypto spread is positive at one horizon of five, and strongly NEGATIVE at 21, 42 and 63 —
the same sign as the ETFs and three to six times the magnitude.**

**X-2 is FALSIFIED, and the basket hypothesis therefore does not explain the breakout result.**
This was registered in advance as the outcome that would make the prediction wrong *in an
interesting way*, and it is: down-breaks outperform up-breaks in **both** universes, so
diversification cancelling asset-specific continuation cannot be the cause.

### What the falsification points at instead

**The wedge does not select weakness. It selects volatility COMPRESSION.** A converging channel
narrower than 2 ATR is a quiet name, and the trigger fires on expansion out of that quiet. So the
conditioning variable is *not* the one [D253](D253-the-book-short-sides-on-crypto.md) tested:

| conditioning on | ETFs | crypto |
|---|---|---|
| **past return** (D253's anatomy) | fallen names **bounce** (+39.77%) | fallen names **keep falling** (−50.57%) |
| **wedge compression + break** (here) | down-break **rises** | down-break **rises** |

**Those are two different phenomena and the hypothesis only governs the first.** Post-compression
reversion appears to be a property of the setup rather than of the asset class, which is why it
survives a change of universe that reverses the past-return effect completely.

**So the principal's hypothesis stands where it was tested and does not extend here:**

- **Shorts — CONFIRMED.** D253 found real timing skill on crypto (98.7th percentile) where the
  identical rule had none on ETFs.
- **Breakouts — FALSIFIED.** Same sign in both universes, so the mechanism is not the one proposed.

### The cells — and why nothing succeeds

| cell | exposure | CAGR | excess Sharpe | H (Sharpe / money) | V | E | success |
|---|---:|---:|---:|---:|:--:|:--:|:--:|
| **U_long** | 12.7% | **+10.60%** | +0.668 | 73.6th / 91.3rd | yes | no (min 5) | **no** |
| **D_long** | 10.3% | **+9.47%** | +0.686 | 64.2nd / 86.0th | yes | no (min 3) | **no** |
| **D_short** | 10.3% | **−11.07%** | −0.834 | 41.8th / **8.7th** | no | no (min 3) | **no** |

**Both long cells make money and neither beats its null.** That is the cleanest demonstration in
the programme of why hurdle H exists: a randomly-timed book of identical exposure captures the
same **+32.55%** pooled buy-and-hold that the arms are riding, so the positive CAGR is exposure,
not signal. The best-of-three floor is **+1.063**, far above either.

**`D_short` sits at the 8.7th percentile on money — actively worse than random**, which the
anatomy already said it would be.

**X-1 is FALSIFIED, and so is the principal's prediction.** No cell beats its rotation null at
p95. The registered bet was that it would.

### Scoring

| | prediction | conf. | outcome |
|---|---|---|---|
| **principal** | it will at least beat the nulls | — | **FALSIFIED** — best is 73.6th on Sharpe |
| **X-1** | ≥1 cell beats its null at p95 on Sharpe | ~70% | **FALSIFIED** |
| **X-2** | the up/down spread flips sign vs ETFs | ~70% | **FALSIFIED** — the finding |
| **X-3** | hurdle E fails on every cell | ~90% | **CONFIRMED** — minimums of 5 / 3 / 3 |
| **X-4** | `D_short` posts a negative CAGR | ~80% | **CONFIRMED** (−11.07%); the *"even where it beats its null"* clause is **MOOT** — it did not |
| **X-5** | concurrency ≥30 of 34 at once | ~75% | **FALSIFIED** — 29 / 26 / 26, though sd ratios of 2.4–3.0x confirm the clustering |

**Three of my five predictions failed, and the two that carried the argument were both wrong.**
Registering them numerically is what makes that visible rather than absorbable.

### R10 and ruin

Concurrency maxima 29 / 26 / 26 of 34 against rotated maxima of 11 / 10 / 9 — **sd ratios 3.02x,
2.44x, 2.88x.** `D_short` is ruined at full per-name notional (**BTG-USD +102.4%, 2025-12-09**,
max survivable **0.98x**). The ruin measure is short-side by construction and is reported as N/A
for the two long cells.

### Stop

**CLOSED as registered.** No parameter sweep, no second arming threshold, no move to the 63-name
universe. **The anatomy's sign stands as a mechanism finding regardless of the cells**, which is
why it was registered as a separate prediction from the hurdles.
