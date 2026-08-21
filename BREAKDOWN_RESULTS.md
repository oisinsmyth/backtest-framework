# The breakdown short book: does crisis alpha survive borrow?

**Produced:** 2026-08-21 ·
**Snapshot:** `a2dfbc34c975895a1a2a133e00cdc36978a14f38bea5b83e568cd64b28f28032` ·
**Reproduce:** `uv run python scripts/run_breakdown_study.py` (offline, deterministic)

> **Thesis label (D38/D82/D117).** Directional and beta-loaded, exactly like its long
> sibling, and equally **not** part of this project's market-neutral thesis. It is short
> or flat on a single high-beta instrument. Its honest benchmark is neither the risk-free
> rate nor buy-and-hold: it is "does this pay in the regimes it claims, and does it
> diversify the long book?" — which is what the regime table and the correlation table
> below are for, and why neither is an appendix.

## Read this first: three things that bound what this study can claim

### 1. The stop is CLOSE-BASED, so the squeeze tail is NOT truncated by construction

The brief makes tail discipline non-optional and says plainly that *"short expectancy is
only calculable with the squeeze tail truncated by construction"*. That standard is **not
met here, and cannot be with the current engine.**

`simulator/fills.stop_fill_price` implements correct gap-through semantics (D10) and
names `BUY_STOP` as "the exit order for a short position" — but it is a Step-2
demonstration vehicle wired only to `config/fill_model.py`, never to `run_backtest`. The
engine's order path is weight-target → quantity → fill at close or next open. There is no
intrabar stop.

So `ChannelStopExit` observes a **close** beyond the stop and exits at the **next open**.
An overnight gap goes straight through it. The study therefore MEASURES the shortfall
rather than assuming it away — see the stop-gap table. Read every short number here as
"with a stop that mostly works", not "with a bounded loss per trade".

### 2. Borrow is charged, at a stated non-zero rate

10%/yr on the short notional for the whole life of every trade
(D124's rate, D169's decision). Assuming free shorts is the single most result-corrupting
choice available to a spot-crypto short study, because the borrow accrues on ~100% of NAV
continuously while the position is open — unlike the long book, where the equivalent cost
is structurally zero.

### 3. The parameters are NOT mirrored from the long book

Sweep is (10, 20, 30, 40) x (3, 5, 10), against the long book's
(20, 30, 40, 55) x (5, 10, 20). Bear legs are faster and shorter and bear
rallies are violent. **Different optimal parameters from the long side is the expected
finding, not a red flag** — and this sweep is counted separately for multiplicity.

---

# BTC-USD

Out-of-sample **2015-09-10 to 2025-11-12** — 3,717 daily bars
across 59 walk-forward windows. Regime mix of the sample:
**bull 62% · bear 22% · chop 16%**.

## The headline table: performance by regime

A short book that is flat through a bull sample and profitable through the bears is a
SUCCESS. Judging it on full-sample Sharpe would call that a failure, which is why the
regime slice leads and the full-sample number follows it.

Regimes are ex-post SMA(200) labels — bull is price above a rising average, bear is price
below a falling one, chop is the two disagreeing. They are used only to READ the results;
the strategy's own gate is the plain close-vs-average test and it never sees these labels.

Baseline `short_20_5` at `taker_40bp`:

| Regime | Bars | Share | Return in regime | Daily Sharpe | Exposure |
|---|---|---|---|---|---|
| **bull** | 2,316 | 62% | -33.3% | -0.055 | 1% |
| **bear** | 818 | 22% | -2.3% | +0.009 | 33% |
| **chop** | 582 | 16% | -54.7% | -0.096 | 29% |

## Every variant at `taker_40bp`

| Variant | Total return | CAGR | Sharpe (ann.) | Max DD | Trades | Exposure |
|---|---|---|---|---|---|---|
| `short_10_3` | -68.9% | -10.8% | -0.63 | 68.9% | 51 | 10.7% |
| `short_10_5` | -77.3% | -13.5% | -0.67 | 78.8% | 46 | 15.0% |
| `short_10_10` | -61.2% | -8.9% | -0.40 | 72.6% | 34 | 19.3% |
| `short_20_3` | -65.3% | -9.9% | -0.61 | 65.5% | 38 | 8.5% |
| `short_20_5` | -70.5% | -11.3% | -0.60 | 72.4% | 35 | 12.1% |
| `short_20_10` | -49.8% | -6.5% | -0.32 | 67.1% | 25 | 15.5% |
| `short_30_3` | -52.8% | -7.1% | -0.54 | 61.0% | 27 | 6.1% |
| `short_30_5` | -59.5% | -8.5% | -0.54 | 67.6% | 25 | 8.6% |
| `short_30_10` | -60.5% | -8.7% | -0.49 | 72.4% | 21 | 10.9% |
| `short_40_3` | -49.9% | -6.6% | -0.54 | 58.6% | 25 | 5.8% |
| `short_40_5` | -54.1% | -7.4% | -0.51 | 63.3% | 23 | 7.9% |
| `short_40_10` | -53.7% | -7.3% | -0.44 | 67.7% | 19 | 10.1% |
| `short_timestop_3` | -50.0% | -6.6% | -0.42 | 58.4% | 41 | 7.7% |
| `short_timestop_5` | -54.5% | -7.4% | -0.45 | 61.3% | 38 | 8.8% |
| `short_no_regime_gate` | -92.3% | -22.2% | -0.91 | 92.3% | 61 | 20.2% |

## The primary verdict: exposure-matched random SHORT entries

Any short rule shows a profit in a sample containing 2018 and 2022, because the
instrument fell. The question is whether THESE entries beat randomly-placed shorts of the
same count and the same holding-period distribution. 1,000 draws, direction
-1, exposure matched by construction.

| | Sharpe (ann.) |
|---|---|
| **Strategy (observed)** | **-0.605** |
| Random-entry null, 95th pct | -0.112 |
| Random-entry null, median | -0.614 |
| Random-entry null, 5th pct | -1.090 |

**Percentile vs the null: 51%.** At the conventional 95% bar the
strategy **does not beat** the null.

## Does it diversify the long book?

Correlation is computed over the full span **including bars either book is flat** —
excluding them would measure "how do they behave when both happen to be trading", which
is not the diversification question. The whole claim is that the short book wakes when the
long book sleeps.

| | Value |
|---|---|
| Long-vs-short daily return correlation | **+0.001** |
| Target from the brief | ≤ ~0.2 |
| Long book Sharpe (alone) | 1.20 |
| Short book Sharpe (alone) | -0.60 |
| Combined, equal VOL weight | 0.42 |
| Long book max drawdown | 43.0% |
| Combined max drawdown | 34.0% |

## What the close-based stop actually cost

Every exit that filled beyond its own stop level — the tail the stop did not truncate.

| | Value |
|---|---|
| Exits that filled beyond the stop | 2 of 2 stop exits |
| Worst single gap | 18.6% beyond the stop |
| Mean gap | 18.3% |

If this table is empty the stop was never the binding exit on this symbol — which is
information, not a clean bill of health.

---

# ETH-USD

Out-of-sample **2018-07-19 to 2025-12-17** — 2,709 daily bars
across 43 walk-forward windows. Regime mix of the sample:
**bull 50% · bear 34% · chop 16%**.

## The headline table: performance by regime

A short book that is flat through a bull sample and profitable through the bears is a
SUCCESS. Judging it on full-sample Sharpe would call that a failure, which is why the
regime slice leads and the full-sample number follows it.

Regimes are ex-post SMA(200) labels — bull is price above a rising average, bear is price
below a falling one, chop is the two disagreeing. They are used only to READ the results;
the strategy's own gate is the plain close-vs-average test and it never sees these labels.

Baseline `short_20_5` at `taker_40bp`:

| Regime | Bars | Share | Return in regime | Daily Sharpe | Exposure |
|---|---|---|---|---|---|
| **bull** | 1,351 | 50% | -16.4% | -0.065 | 1% |
| **bear** | 911 | 34% | +33.7% | +0.026 | 40% |
| **chop** | 446 | 16% | +22.6% | +0.039 | 25% |

## Every variant at `taker_40bp`

| Variant | Total return | CAGR | Sharpe (ann.) | Max DD | Trades | Exposure |
|---|---|---|---|---|---|---|
| `short_10_3` | -33.4% | -5.3% | -0.28 | 61.3% | 44 | 16.8% |
| `short_10_5` | +60.3% | +6.6% | 0.23 | 55.5% | 34 | 23.7% |
| `short_10_10` | +6.6% | +0.9% | 0.05 | 60.8% | 30 | 29.0% |
| `short_20_3` | -42.6% | -7.2% | -0.40 | 66.6% | 35 | 12.6% |
| `short_20_5` | +37.1% | +4.3% | 0.14 | 54.1% | 27 | 18.1% |
| `short_20_10` | +2.2% | +0.3% | 0.01 | 56.1% | 24 | 23.4% |
| `short_30_3` | -33.8% | -5.4% | -0.37 | 64.2% | 29 | 11.5% |
| `short_30_5` | +53.7% | +6.0% | 0.20 | 56.9% | 22 | 16.4% |
| `short_30_10` | +33.9% | +4.0% | 0.13 | 58.6% | 20 | 20.3% |
| `short_40_3` | -21.4% | -3.2% | -0.26 | 55.8% | 25 | 10.0% |
| `short_40_5` | +86.7% | +8.8% | 0.30 | 47.9% | 18 | 14.9% |
| `short_40_10` | +55.5% | +6.1% | 0.21 | 52.3% | 17 | 18.8% |
| `short_timestop_3` | +64.3% | +6.9% | 0.23 | 36.9% | 31 | 11.8% |
| `short_timestop_5` | +42.7% | +4.9% | 0.16 | 40.2% | 31 | 12.8% |
| `short_no_regime_gate` | -19.3% | -2.9% | -0.08 | 66.1% | 43 | 24.7% |

## The primary verdict: exposure-matched random SHORT entries

Any short rule shows a profit in a sample containing 2018 and 2022, because the
instrument fell. The question is whether THESE entries beat randomly-placed shorts of the
same count and the same holding-period distribution. 1,000 draws, direction
-1, exposure matched by construction.

| | Sharpe (ann.) |
|---|---|
| **Strategy (observed)** | **0.142** |
| Random-entry null, 95th pct | 0.132 |
| Random-entry null, median | -0.426 |
| Random-entry null, 5th pct | -1.047 |

**Percentile vs the null: 96%.** At the conventional 95% bar the
strategy **beats** the null.

## Does it diversify the long book?

Correlation is computed over the full span **including bars either book is flat** —
excluding them would measure "how do they behave when both happen to be trading", which
is not the diversification question. The whole claim is that the short book wakes when the
long book sleeps.

| | Value |
|---|---|
| Long-vs-short daily return correlation | **-0.001** |
| Target from the brief | ≤ ~0.2 |
| Long book Sharpe (alone) | 0.78 |
| Short book Sharpe (alone) | 0.14 |
| Combined, equal VOL weight | 0.65 |
| Long book max drawdown | 35.2% |
| Combined max drawdown | 29.5% |

## What the close-based stop actually cost

Every exit that filled beyond its own stop level — the tail the stop did not truncate.

| | Value |
|---|---|
| Exits that filled beyond the stop | 2 of 2 stop exits |
| Worst single gap | 38.5% beyond the stop |
| Mean gap | 36.8% |

If this table is empty the stop was never the binding exit on this symbol — which is
information, not a clean bill of health.

---

# Verdict

- **BTC-USD**: null percentile 51%, long/short correlation +0.00, combined Sharpe 0.42 against 1.20 long-only (max drawdown 34% against 43%).
- **ETH-USD**: null percentile 96%, long/short correlation -0.00, combined Sharpe 0.65 against 0.78 long-only (max drawdown 30% against 35%).

**The null verdict is SPLIT and must not be read as a pass.** ETH-USD clears the 95% bar; BTC-USD does not. The long study fixed the rule for exactly this situation before looking — a filter is kept only if it improves on EVERY symbol, because one symbol out of two is a coin flip. The same discipline applies here, and by it the entry rule is not demonstrated. Reporting the winner alone would be the single most misleading thing available in this document.

**The diversification claim holds and the profitability claim does not, and those are separate findings.** Correlation against the long book comes in at or below the brief's ~0.2 target on both symbols — genuinely near zero, which is the complementary-payoff property the ensemble argument needs. But near-zero correlation cannot rescue a book that loses money: on BTC-USD, ETH-USD the equal-vol-weighted combination has a LOWER Sharpe than the long book alone. You cannot diversify with a negative-expectancy asset; you can only spread the same losses more smoothly. The one thing that does survive is drawdown: on BTC-USD, ETH-USD the combined book's worst drawdown is smaller than the long book's. That is the same shape of result the long study landed on — a drawdown-shape finding, not an alpha finding — and it should be quoted with the Sharpe cost attached, never on its own.

### Success criteria from the brief, scored

The brief named three: *strongly profitable in bear regimes; flat-to-small-loss in bull
regimes; acceptable chop bleed.* Scored here as bear return > +10%, bull return > −20%,
chop return > −10% — thresholds fixed before reading, and blunt on purpose.

| Symbol | Bear (strongly profitable?) | Bull (flat-to-small-loss?) | Chop (acceptable bleed?) |
|---|---|---|---|
| BTC-USD | -2.3% FAIL | -33.3% at 1% exposure FAIL | -54.7% FAIL |
| ETH-USD | +33.7% PASS | -16.4% at 1% exposure PASS | +22.6% PASS |

**Split again, and along the same line as the null.** ETH-USD meets all three; BTC-USD does not. The two symbols are telling different stories about the same rule, which on a two-instrument sample is the definition of an undemonstrated result rather than a partial success.

**The gate itself works on every symbol** — bull-regime exposure is at most 1%, so the book really does stand aside when the long book is working. Note that this is a separate claim from the bull CRITERION above, and the two can diverge: on a symbol where the criterion fails, it fails not because the gate let the book trade through the bull market but because the handful of trades it did allow were bad enough to lose double digits on their own. The gate is not the problem. What it gates is.
### And the stop did not do its job

**4 of 4 stop exits filled BEYOND their own stop level**, the worst by
38.5%. That is not a rounding error on the tail discipline — it is the tail
discipline failing in the only cases where it was ever the binding exit. The brief's
premise, that short expectancy becomes calculable once the squeeze tail is truncated by
construction, is not satisfied by this implementation, and every number above should be
read with that in front of it.

# Standing caveats

1. **The stop is close-based.** The squeeze tail is not truncated by construction; the
   gap table measures what that costs. Intrabar stop execution in `run_backtest` is the
   prerequisite for the brief's stated standard, and it does not exist.
2. **Borrow is a stated assumption, not a quote.** 10%/yr is mid-range for BTC/ETH spot
   margin borrow over the sample; it was neither swept nor negotiated, and hard-to-borrow
   episodes in a real crash would be worse precisely when the book is most short.
3. **No funding, no perp expression.** These are spot shorts (D108). A perpetual-futures
   implementation would pay funding, which in a falling market is often a CREDIT to
   shorts — so this is conservative in that one direction and silent about it otherwise.
4. **Live tradability is out of scope and mostly negative.** The FCA retail
   crypto-derivatives ban and the absence of retail spot margin mean this book is
   backtest-and-shadow-signals only. The one legal live expression at current capital is
   equity-index breakdown via spread betting, which is a different instrument and a
   different spec.
5. **Two instruments, both survivors.** The same selection bias the long study named as
   its largest un-deflatable problem applies here unchanged.
