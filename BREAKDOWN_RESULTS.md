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

### 1. The stop is INTRABAR now — and it turns out barely to matter

Phase 2 shipped this book with a close-based stop, because `run_backtest` had no intrabar
stop execution, and said so loudly. D170 wired it: `simulator/fills.stop_fill_price` and
its D10 gap semantics now sit in the engine's bar loop, checked before the strategy is
consulted, so a stop closes a position **the moment the bar touches it** and a bar that
gaps through fills at the open rather than at a price the market never traded.

The honest result is that it changes almost nothing here, and the reason is worth more
than the fix. **The stop sits at the far side of the entry channel** — for a short
entering on an N-bar low, it is the N-bar high — which is an enormous distance from the
entry. The trailing exit channel gets there first essentially every time. See the stop
table below: the stop is armed for hundreds of bars per symbol and causes a handful of
exits, or none.

**This also corrects a Phase 2 claim.** That report said "4 of 4 stop exits filled beyond
their own stop, worst by 38.5%". That number was a measurement artifact: it inferred stop
exits by asking whether an exit price ended up beyond the stop level, which also counts
ordinary channel exits that closed past it. The engine now records which fills a stop
actually caused, and the true count is far smaller.

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
| **bear** | 818 | 22% | -6.1% | +0.007 | 30% |
| **chop** | 582 | 16% | -54.7% | -0.096 | 29% |

## Every variant at `taker_40bp`

| Variant | Total return | CAGR | Sharpe (ann.) | Max DD | Trades | Exposure |
|---|---|---|---|---|---|---|
| `short_10_3` | -68.2% | -10.6% | -0.62 | 68.2% | 51 | 10.6% |
| `short_10_5` | -78.3% | -13.9% | -0.69 | 78.5% | 47 | 14.4% |
| `short_10_10` | -61.4% | -8.9% | -0.40 | 72.3% | 35 | 18.7% |
| `short_20_3` | -66.5% | -10.2% | -0.62 | 66.5% | 38 | 8.5% |
| `short_20_5` | -71.6% | -11.6% | -0.62 | 72.4% | 35 | 11.5% |
| `short_20_10` | -57.4% | -8.0% | -0.39 | 67.1% | 26 | 14.6% |
| `short_30_3` | -52.8% | -7.1% | -0.54 | 61.0% | 27 | 6.1% |
| `short_30_5` | -59.5% | -8.5% | -0.54 | 67.6% | 25 | 8.6% |
| `short_30_10` | -60.5% | -8.7% | -0.49 | 72.4% | 21 | 10.9% |
| `short_40_3` | -49.9% | -6.6% | -0.54 | 58.6% | 25 | 5.8% |
| `short_40_5` | -54.1% | -7.4% | -0.51 | 63.3% | 23 | 7.9% |
| `short_40_10` | -53.7% | -7.3% | -0.44 | 67.7% | 19 | 10.1% |
| `short_timestop_3` | -50.0% | -6.6% | -0.42 | 58.4% | 41 | 7.7% |
| `short_timestop_5` | -56.2% | -7.8% | -0.47 | 61.3% | 38 | 8.8% |
| `short_no_regime_gate` | -92.5% | -22.5% | -0.92 | 92.5% | 61 | 19.6% |
| `stop_trail_5` | -40.6% | -5.0% | -0.34 | 52.0% | 36 | 9.5% |
| `stop_trail_10` | -58.3% | -8.2% | -0.47 | 63.4% | 35 | 10.9% |
| `stop_trail_20` | -71.5% | -11.6% | -0.62 | 72.4% | 35 | 11.5% |
| `stop_atr_2` | -63.2% | -9.3% | -0.53 | 66.3% | 35 | 11.1% |
| `stop_atr_3` | -68.3% | -10.7% | -0.59 | 70.0% | 35 | 11.4% |
| `stop_chandelier_3` | -57.8% | -8.1% | -0.53 | 57.8% | 36 | 9.3% |

## The stop sweep: which stops actually bind, and what they cost

| Stop | Total return | Sharpe | Max DD | Trades | Stop exits / armed bars | Bind rate | Gapped |
|---|---|---|---|---|---|---|---|
| `entry_channel` *(incumbent)* | -71.6% | -0.62 | 72.4% | 35 | 1 / 426 | 0.2% | 0 |
| `trail_5` | -40.6% | -0.34 | 52.0% | 36 | 33 / 353 | 9.3% | 0 |
| `trail_10` | -58.3% | -0.47 | 63.4% | 35 | 16 / 404 | 4.0% | 0 |
| `trail_20` | -71.5% | -0.62 | 72.4% | 35 | 1 / 426 | 0.2% | 0 |
| `atr_2` | -63.2% | -0.53 | 66.3% | 35 | 11 / 411 | 2.7% | 0 |
| `atr_3` | -68.3% | -0.59 | 70.0% | 35 | 4 / 423 | 0.9% | 0 |
| `chandelier_3` | -57.8% | -0.53 | 57.8% | 36 | 19 / 344 | 5.5% | 0 |

**Bind rate first.** A stop that never fires is not being tested — that row is the strategy without a stop, whatever else it shows. **Gapped** counts exits that filled past the level because the bar opened beyond it, which is the residue no intrabar stop can remove on daily bars.

## The primary verdict: exposure-matched random SHORT entries

Any short rule shows a profit in a sample containing 2018 and 2022, because the
instrument fell. The question is whether THESE entries beat randomly-placed shorts of the
same count and the same holding-period distribution. 1,000 draws, direction
-1, exposure matched by construction.

| | Sharpe (ann.) |
|---|---|
| **Strategy (observed)** | **-0.619** |
| Random-entry null, 95th pct | -0.108 |
| Random-entry null, median | -0.624 |
| Random-entry null, 5th pct | -1.094 |

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
| Short book Sharpe (alone) | -0.62 |
| Combined, equal VOL weight | 0.41 |
| Long book max drawdown | 43.0% |
| Combined max drawdown | 34.0% |

## What the close-based stop actually cost

Every exit that filled beyond its own stop level — the tail the stop did not truncate.

| | Value |
|---|---|
| Exits the stop actually caused | 1 |
| ...of which gapped past the stop | 0 |
| Bars carrying a live stop | 426 |
| Worst single gap | 0.0% beyond the stop |

**Read the first two rows against the third.** A stop that is armed for thousands of bars
and closes a handful of trades is *present* rather than *binding*: the trailing channel
almost always gets there first, because the stop sits at the far side of the entry
channel and that is a very long way from a breakdown entry.

These counts come from the engine's own record of which fills a stop caused (D170).
The Phase 2 version of this table inferred them, by asking whether an exit price ended
up beyond the stop level — which also catches ordinary channel exits that happened to
close past it. That inference is what produced the earlier "4 of 4 stop exits gapped"
claim, and it was wrong: most of those exits were not stop exits at all.

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
| `short_10_3` | -33.6% | -5.4% | -0.28 | 61.3% | 44 | 16.7% |
| `short_10_5` | +60.3% | +6.6% | 0.23 | 55.5% | 34 | 23.7% |
| `short_10_10` | +8.0% | +1.0% | 0.06 | 60.3% | 31 | 27.8% |
| `short_20_3` | -42.6% | -7.2% | -0.40 | 66.6% | 35 | 12.6% |
| `short_20_5` | +37.1% | +4.3% | 0.14 | 54.1% | 27 | 18.1% |
| `short_20_10` | -1.3% | -0.2% | -0.00 | 57.6% | 25 | 22.5% |
| `short_30_3` | -33.8% | -5.4% | -0.37 | 64.2% | 29 | 11.5% |
| `short_30_5` | +53.7% | +6.0% | 0.20 | 56.9% | 22 | 16.4% |
| `short_30_10` | +33.9% | +4.0% | 0.13 | 58.6% | 20 | 20.3% |
| `short_40_3` | -21.4% | -3.2% | -0.26 | 55.8% | 25 | 10.0% |
| `short_40_5` | +86.7% | +8.8% | 0.30 | 47.9% | 18 | 14.9% |
| `short_40_10` | +55.5% | +6.1% | 0.21 | 52.3% | 17 | 18.8% |
| `short_timestop_3` | +64.3% | +6.9% | 0.23 | 36.9% | 31 | 11.8% |
| `short_timestop_5` | +42.7% | +4.9% | 0.16 | 40.2% | 31 | 12.8% |
| `short_no_regime_gate` | -19.3% | -2.9% | -0.08 | 66.1% | 43 | 24.7% |
| `stop_trail_5` | +38.2% | +4.5% | 0.14 | 44.5% | 31 | 13.4% |
| `stop_trail_10` | +56.3% | +6.2% | 0.21 | 50.4% | 28 | 17.3% |
| `stop_trail_20` | +37.1% | +4.3% | 0.14 | 54.1% | 27 | 18.1% |
| `stop_atr_2` | +40.6% | +4.7% | 0.15 | 54.0% | 27 | 16.2% |
| `stop_atr_3` | +36.5% | +4.3% | 0.14 | 54.1% | 27 | 18.0% |
| `stop_chandelier_3` | +16.1% | +2.0% | 0.05 | 55.7% | 30 | 13.8% |

## The stop sweep: which stops actually bind, and what they cost

| Stop | Total return | Sharpe | Max DD | Trades | Stop exits / armed bars | Bind rate | Gapped |
|---|---|---|---|---|---|---|---|
| `entry_channel` *(incumbent)* | +37.1% | 0.14 | 54.1% | 27 | 0 / 489 | 0.0% | 0 |
| `trail_5` | +38.2% | 0.14 | 44.5% | 31 | 26 / 363 | 7.2% | 0 |
| `trail_10` | +56.3% | 0.21 | 50.4% | 28 | 11 / 468 | 2.4% | 0 |
| `trail_20` | +37.1% | 0.14 | 54.1% | 27 | 0 / 489 | 0.0% | 0 |
| `atr_2` | +40.6% | 0.15 | 54.0% | 27 | 9 / 439 | 2.1% | 0 |
| `atr_3` | +36.5% | 0.14 | 54.1% | 27 | 1 / 488 | 0.2% | 0 |
| `chandelier_3` | +16.1% | 0.05 | 55.7% | 30 | 18 / 374 | 4.8% | 0 |

**Bind rate first.** A stop that never fires is not being tested — that row is the strategy without a stop, whatever else it shows. **Gapped** counts exits that filled past the level because the bar opened beyond it, which is the residue no intrabar stop can remove on daily bars.

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
| Exits the stop actually caused | 0 |
| ...of which gapped past the stop | 0 |
| Bars carrying a live stop | 489 |
| Worst single gap | 0.0% beyond the stop |

**Read the first two rows against the third.** A stop that is armed for thousands of bars
and closes a handful of trades is *present* rather than *binding*: the trailing channel
almost always gets there first, because the stop sits at the far side of the entry
channel and that is a very long way from a breakdown entry.

These counts come from the engine's own record of which fills a stop caused (D170).
The Phase 2 version of this table inferred them, by asking whether an exit price ended
up beyond the stop level — which also catches ordinary channel exits that happened to
close past it. That inference is what produced the earlier "4 of 4 stop exits gapped"
claim, and it was wrong: most of those exits were not stop exits at all.

---

# Verdict

- **BTC-USD**: null percentile 51%, long/short correlation +0.00, combined Sharpe 0.41 against 1.20 long-only (max drawdown 34% against 43%).
- **ETH-USD**: null percentile 96%, long/short correlation -0.00, combined Sharpe 0.65 against 0.78 long-only (max drawdown 30% against 35%).

**The null verdict is SPLIT and must not be read as a pass.** ETH-USD clears the 95% bar; BTC-USD does not. The long study fixed the rule for exactly this situation before looking — a filter is kept only if it improves on EVERY symbol, because one symbol out of two is a coin flip. The same discipline applies here, and by it the entry rule is not demonstrated. Reporting the winner alone would be the single most misleading thing available in this document.

**The diversification claim holds and the profitability claim does not, and those are separate findings.** Correlation against the long book comes in at or below the brief's ~0.2 target on both symbols — genuinely near zero, which is the complementary-payoff property the ensemble argument needs. But near-zero correlation cannot rescue a book that loses money: on BTC-USD, ETH-USD the equal-vol-weighted combination has a LOWER Sharpe than the long book alone. You cannot diversify with a negative-expectancy asset; you can only spread the same losses more smoothly. The one thing that does survive is drawdown: on BTC-USD, ETH-USD the combined book's worst drawdown is smaller than the long book's. That is the same shape of result the long study landed on — a drawdown-shape finding, not an alpha finding — and it should be quoted with the Sharpe cost attached, never on its own.

### Success criteria from the brief, scored

The brief named three: *strongly profitable in bear regimes; flat-to-small-loss in bull
regimes; acceptable chop bleed.* Scored here as bear return > +10%, bull return > −20%,
chop return > −10% — thresholds fixed before reading, and blunt on purpose.

| Symbol | Bear (strongly profitable?) | Bull (flat-to-small-loss?) | Chop (acceptable bleed?) |
|---|---|---|---|
| BTC-USD | -6.1% FAIL | -33.3% at 1% exposure FAIL | -54.7% FAIL |
| ETH-USD | +33.7% PASS | -16.4% at 1% exposure PASS | +22.6% PASS |

**Split again, and along the same line as the null.** ETH-USD meets all three; BTC-USD does not. The two symbols are telling different stories about the same rule, which on a two-instrument sample is the definition of an undemonstrated result rather than a partial success.

**The gate itself works on every symbol** — bull-regime exposure is at most 1%, so the book really does stand aside when the long book is working. Note that this is a separate claim from the bull CRITERION above, and the two can diverge: on a symbol where the criterion fails, it fails not because the gate let the book trade through the bull market but because the handful of trades it did allow were bad enough to lose double digits on their own. The gate is not the problem. What it gates is.
### The stop sweep, scored

Same rule the long study fixed before looking: keep only what improves on EVERY symbol,
because one out of two is a coin flip. Δ is against the incumbent `entry_channel` stop at
`taker_40bp`; `INERT` means the variant produced results identical to the incumbent, so it is
not a distinct configuration at all.

| Stop | Δ Sharpe BTC-USD | Δ Sharpe ETH-USD | Stop exits | Decision |
|---|---|---|---|---|
| `trail_5` | +0.279 | -0.002 | 59 | DROP |
| `trail_10` | +0.144 | +0.068 | 27 | **KEEP** |
| `trail_20` | +0.002 | +0.000 | 1 | INERT |
| `atr_2` | +0.092 | +0.013 | 20 | **KEEP** |
| `atr_3` | +0.034 | -0.002 | 5 | DROP |
| `chandelier_3` | +0.092 | -0.096 | 37 | DROP |

**2 of the swept stops improve risk-adjusted return on every symbol by more than 0.01 Sharpe**, and the strongest by worst-case improvement is `trail_10` (+0.07 on its weaker symbol, 27 stop exits). **But binding more is not uniformly better.** The rank correlation between how often a stop binds and how much it helps is BTC-USD +0.94, ETH-USD -0.43 — positive on BTC-USD, negative on ETH-USD. On the symbol where it is negative, the stops that fire most (`trail_5`, `chandelier_3`) are cutting winning trades short rather than truncating losers. That is the same failure mode the long study found in its entry filters: a device that removes trades removes good ones too.

**Three things this does not mean.**

First, **less bad is not good.** The best BTC row is still a large loss at a negative
Sharpe; a tighter stop shrinks the damage, it does not create an edge. The entry rule is
what failed its null, and no stop repairs an entry.

Second, **this is a fresh trial series and it is not free.** Six stop configurations on
two symbols across four tiers were evaluated here on top of an already-swept strategy.
One of them (`trail_20`) turned out to be inert — for a short entering on a 20-bar low, a
20-bar trailing high IS the entry channel — so the effective count is five. These trials
are NOT yet in the deflated-Sharpe accounting (see the gap noted below), and picking the
best row of five after the fact is exactly the selection this project's machinery exists
to penalise.

Third, **the sweep was run at fixed entry/exit parameters.** A stop interacts with the
exit channel it sits beside, and re-optimising both together would be a much larger
multiplicity bill for a book that has not yet shown an entry edge.
### What the stop actually did

The stop was armed for **915 bars** and caused **1 exit(s)**
(BTC-USD 1 exit(s) from 426 armed bars · ETH-USD 0 exit(s) from 489 armed bars). **None of them gapped** — each filled at its stop price, which is the intrabar machinery doing exactly what it exists to do.

**Read those two numbers against each other.** A stop armed for hundreds of bars that
closes a handful of trades is *present* rather than *binding*: it sits at the far side of
the entry channel, which is a very long way from a breakdown entry, so the trailing exit
gets there first almost every time. The brief's premise — that short expectancy becomes
calculable once the squeeze tail is truncated — is now satisfied mechanically, and turns
out not to be the thing that was limiting this book.

# Standing caveats

1. **The stop is intrabar (D170) but almost never binds.** The mechanism is correct —
   touched stops fill at the stop, gapped ones at the open — but the level sits at the
   far side of the entry channel, so the trailing exit closes nearly every position
   first. A risk control that never binds has not been shown to work on this sample, only
   to be unneeded on it. A tighter stop (ATR-based, say) is a different strategy and
   would need its own sweep and its own multiplicity accounting.
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
6. **No TrialRegistry rows and no deflated Sharpe — a real gap, not an omission by
   design.** The brief for this book asks for both. The long study has them; this one
   does not, and the stop sweep has just added a fresh trial series on top. Every Sharpe
   here is therefore RAW, undeflated, and should be read as an upper bound. Closing this
   is the first thing to do before any stop family is adopted.
