# D223 — A volume-regime gate: does trading only in loud markets pay for itself?

**Status:** Pre-registered — written and committed BEFORE the runner exists
**Date:** 2026-08-27
**Category:** Validation & research integrity
**Source:** A user proposal — *"during periods of higher than normal volume is when the
bigger moves happen... the signal should stay out of disadvantaged volatility and try to be
in advantaged volatility"* — implemented as a short EMA of volume over a long SMA of volume.

> A result section will be appended and nothing above it edited.

## What is being tested

A **regime gate**, not an entry confirmation. D220 tested whether volume at the entry bar
predicts that trade's outcome and found it does not. This is a different claim: that the
*market state* the arm is trading into is better or worse for a trend rule, and that volume
identifies it.

The parent is the arm D221 established: Impulse MACD's acceleration rung on 15m Binance bars
with `(136, 36)` — a 33-hour window — long-flat, on BTCUSDT and ETHUSDT.

## The prior, measured before the design was fixed

### Premise 1 — the volume/volatility link. **Confirmed, emphatically.**

| volume quintile | BTC mean \|ret\| | vs Q1 | ETH mean \|ret\| | vs Q1 |
|---|---:|---:|---:|---:|
| Q1 | 9.2 bp | 1.00× | 12.1 bp | 1.00× |
| Q3 | 16.9 bp | 1.83× | 22.2 bp | 1.83× |
| **Q5** | **41.3 bp** | **4.47×** | **54.3 bp** | **4.48×** |

`corr(log relative volume, |return|)` = **+0.44 / +0.46**, monotone, and the two symbols
agree to two decimals. Clark's mixture-of-distributions result holds textbook-perfectly here.
**The proposal's premise is correct and it is not marginal.**

### Premise 2 — is the move more *directional* when volume is high? **No. The reverse.**

Sharpe is invariant to a pure volatility scaling: if Q5 returns are 4.5× bigger *and* 4.5×
more volatile, the ratio is unchanged. The proposal's refinement — that the signal may become
*clearer* in high volume, not merely larger — is the argument that would break that
invariance, and it is right in principle: if loud markets mean more **informed** trading, the
permanent component grows faster than the transitory one and signal-to-noise genuinely rises.
That is Kyle rather than pure Clark, and it is testable as a property of the price series.

It does not hold here:

| quintile | BTC PE(32) | BTC PE(128) | **BTC VR(8)** | ETH PE(32) | ETH PE(128) | **ETH VR(8)** |
|---|---:|---:|---:|---:|---:|---:|
| Q1 | 0.170 | 0.103 | **1.351** | 0.180 | 0.107 | **1.331** |
| Q3 | 0.167 | 0.092 | 1.147 | 0.175 | 0.093 | 1.215 |
| Q5 | 0.163 | 0.085 | **0.671** | 0.168 | 0.086 | **0.688** |
| **Q5 − Q1** | −0.006 | **−0.017** | **−0.680** | −0.012 | **−0.020** | **−0.643** |

Path efficiency (`|sum of next n returns| / sum of |next n returns|`) is **flat to slightly
falling**. The variance ratio is decisive: **VR > 1 is trending, VR < 1 is mean-reverting**,
and it falls from **1.35 to 0.67** on both symbols. Quiet markets trend; **loud markets
revert** — consistent with liquidation cascades and news spikes that overshoot and snap back.

### The tension this study exists to resolve

The two channels **point in opposite directions**, and neither is speculative:

| channel | direction | evidence |
|---|---|---|
| **Cost.** Fees are fixed per trade; the move scales with volume | favours trading **loud** | 4.5× move, against a fixed 20 bp round trip |
| **Persistence.** A trend rule needs directional follow-through | favours trading **quiet** | VR 1.35 quiet vs 0.67 loud |

The parent arm's average trade earns **14.4 bp (BTC) / 19.9 bp (ETH) against a 20 bp
round-trip cost** at `maker_10bp` — it does not cover its own fees. So the cost channel has
real work to do. But the persistence channel says the trades that best cover their fees are
the ones a trend rule is worst at.

**Which wins is genuinely unknown, and that is the study.**

## The arms

The gate is on the **volume regime**, evaluated at the entry bar, and it decides whether the
trade is opened. It never exits early — that is a different hypothesis.

```
ratio = EMA(volume, short) / SMA(volume, long)
```

| | condition | the claim |
|---|---|---|
| **G1** | `ratio > 1` — trade only when volume is elevated | the proposal: bigger moves pay the fees |
| **G2** | `ratio < 1` — trade only when volume is quiet | the counter: VR says quiet markets trend |

**Both directions are declared**, as in D220, because testing only G1 leaves *"we should have
tried it the other way"* available after a failure, which is an escape and not a hurdle.

**Windows are whole multiples of 96 bars (one UTC day):** `(96, 960)` = 1d/10d and
`(192, 1920)` = 2d/20d.

**This is not cosmetic.** A naive `EMA(20)/SMA(200)` at 15m has **14.2% (BTC) / 11.7% (ETH) of
its variance explained by hour of day alone**, peaking at 16:00 UTC and troughing at 06:00 —
one seventh of the signal would be a *clock*, not information arrival, and crypto's session
structure could make that "work" for reasons unrelated to the hypothesis. Whole-day windows
cut it to **2.2% / 1.8%**.

**2 conditions × 2 window pairs = 4 fresh looks.** Symbols are the sample, not hypotheses.

## Hurdles

**H (selectivity), inherited from D220 and load-bearing here.** The gate must beat the
**matched-count random null** at or above the 95th percentile on **both** net Sharpe and net
total return, at `maker_10bp`.

**This hurdle matters far more here than it did on ETFs, and the reason is arithmetic.**
Because the average trade is fee-negative, removing a trade *at random* saves 20 bp and
forfeits 14.4 bp — a net gain of 5.6 bp on BTC. **Any filter will improve net PnL
mechanically.** On ETFs costs were 1.8 bp against multi-hundred-bp moves and this channel did
not exist. The random null is the only thing separating *"volume knows something"* from
*"traded less"*, and a result that clears net improvement but not the null is a **negative**.

**P (parent).** Must beat the unfiltered parent on net Sharpe *and* net total return at
`maker_10bp`.

**E (census).** ≥ 30 trades retained per symbol. The parent has ~1,842 (BTC) and ~1,891 (ETH),
so unlike D220 this will not bind — **which is the whole reason the question is answerable at
15m and was not on daily ETFs.**

## Minimum detectable effect, stated before the run

D222 established that this fixture resolves differences of roughly **0.15 Sharpe** at best —
about 11 symbol-years of correlated crypto history. With 8.3 years on two symbols the standard
error on a paired Sharpe difference is ≈ **0.11**, so the minimum detectable effect at the 95th
percentile is ≈ **0.18 Sharpe**.

**Anything smaller than that is not a finding here, however it is reported.** Stating it now
rather than discovering it in a bootstrap afterwards is the point.

## Predictions, committed before the run

| | Prediction | Confidence |
|---|---|---|
| **O1** | G1 improves **net** PnL over the unfiltered parent — and so does the random null, so this is not evidence of anything | **high** |
| **O2** | G1 **fails hurdle H**: it does not beat its matched-count random null at p95 on both metrics | **moderate-high** |
| **O3** | G1's **gross per-trade edge is lower** than the parent's, because VR says loud regimes revert. The cost saving and the signal damage partly cancel | **moderate** |
| **O4** | **G2 has the better gross per-trade edge and the worse net**, being the mirror image: quiet markets trend but their moves cannot pay a fixed 20 bp fee | **moderate** |
| **O5** | No cell clears H and P together | **moderate-high** |

**What would change my mind:** O2 failing — G1 clearing the random null at p95 on both
metrics with an effect above 0.18 Sharpe. That would mean the cost channel beats the
persistence channel by enough to be visible through the noise of this fixture, and it would be
the first tradeable result this programme has produced.

## Ledger

| block | looks |
|---|---:|
| 2 conditions × 2 window pairs | **4** |
| **fresh, D223 only** | **4** |
| inherited from D217 + D218 + D220 + D221 + D222 | 84 |
| crypto-fixture prior + structure/terrain bar on this fixture | 3,739 |
| **verdict count** | **3,827** |

**Zero-look:** the volume/volatility census, the path-efficiency and variance-ratio census
(properties of the price series, not of the arm), the diurnal-variance census, the
matched-count random null, and the unfiltered parent.

## Pre-committed stops

- **The diurnal gate.** If a chosen window pair leaves more than **5%** of the ratio's variance
  explained by hour of day, it is a clock and not a volume signal, and the cell is void.
- **The random-null gate.** A cell that improves net PnL but does not clear its matched-count
  null is reported as a **failure**, in those words, in the table.
- **No parameter search.** Four cells are declared. If G1 fails, the answer is not a third
  window pair.
- **Nothing is promoted without its own holdout.** A survivor here is a positive claim on a
  fixture this programme has already used heavily; it gets a fresh pre-registration and
  unmined data before anyone believes it (D215/D216, unchanged).
