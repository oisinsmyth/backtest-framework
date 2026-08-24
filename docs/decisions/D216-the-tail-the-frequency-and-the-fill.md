# D216 — the tail, the frequency, and the fill: can the reversion effect ever pay?

**Status:** Pre-registered — written and committed BEFORE the runner exists
**Date:** 2026-08-24
**Category:** Validation & research integrity
**Source:** D215's one unclosed thread, pulled for completeness

> A result section will be appended and nothing above it edited.

## What is being tested

D215 established a real effect and priced it as unusable: P(reversal over 5 bars) rises
monotonically with the size of the recent move — slope +0.103 on two independent symbols,
flat on a random walk, steep on a planted one — and at 15m it is **0.24×–0.32× the cost of
capturing it**.

The thread left open was whether `p` keeps rising past the 87.5th percentile far enough to
clear a realistic cost. Pulling it turned out to require two further dimensions, because
**the break-even arithmetic is not what I said it was** when I described this as a single
thread.

## Correcting my own arithmetic first

**Break-even for a symmetric ±0.5 ATR bracket is `p* = 0.5 + round_trip / ATR`.** Computed
per cell from the committed fixtures:

| | ATR | maker 2 bp RT | 10 bp/side | taker 40 bp/side |
|---|---:|---:|---:|---:|
| 15m `BTCUSDT` | 38.3 bp | **55.22%** | impossible | impossible |
| 15m `ETHUSDT` | 51.9 bp | **53.85%** | 88.54% | impossible |
| 1d `BTC-USD` | 381.6 bp | **50.52%** | 55.24% | 70.96% |
| 1d `ETH-USD` | 527.6 bp | **50.38%** | 53.79% | 65.16% |

**Daily ATR is ten times the 15m ATR, so the identical fixed cost is ten times cheaper in
ATR terms.** The 15m top bucket already measured **50.94%** and **52.59%** — above the
*daily* maker break-even and below the *15m* one. So whether this effect can pay is a
question about bar size at least as much as about the tail, and testing the tail alone would
have answered half of it.

**And a bracketed trade's cost is not symmetric.** The take-profit is a resting limit and can
be a maker fill; the stop must cross and cannot. The round trip therefore depends on `p`
itself and break-even is a fixed point:

```
p* = (c_in + c_stop + 0.5·ATR) / (ATR + c_stop − c_tp)
```

This reduces to `0.5 + RT/ATR` when the legs are symmetric — the identity the solver is
pinned against — and is materially harsher when they are not: roughly **63.7% at 15m against
51.7% at daily** on the same fees. **Quoting a "2 bp maker round trip" for a stopped strategy
was too generous of me and this study does not repeat it.**

## Design

**Frequency.** 15m (`BTCUSDT`/`ETHUSDT`, 294k bars) and daily (`BTC-USD`/`ETH-USD`, 4,017 and
2,974 bars). Both committed fixtures.

**Move-size cutoffs.** The ladder's top bucket (87.5th percentile) plus **95th, 99th,
99.5th**. Fixed here, not searched.

**Fill convention — the dimension that decides it.**

- **taker-in**: enter at the close, always filled.
- **maker-in**: rest a limit at the close, fill only on trade-through —
  `FillAssumption.TRADE_THROUGH`, whose docstring already names the problem: *"the honest one
  for a bounce strategy — being filled only when price keeps going is precisely the adverse
  selection D9 named."*

For a reversion entry the limit fills when the move **continues**, which is the losing case
by construction. Maker is simultaneously the only tier where `p*` is reachable and the tier
that is adversely selected against this exact signal. D196 priced the same effect at
0.138–0.195 Sharpe, and measuring `p_maker` against `p_taker` is this study's second real
question.

**Lookback `M = 8` bars, both frequencies**, reused from D215 rather than re-chosen.
Bar-count matching is the only sensible reading — calendar-matching would put the daily
lookback at 768 bars.

**Sampling.** Scan every bar, take those above the cutoff, enforce **≥ M bars between
selected events** greedily. This differs from D215, which stepped blindly every M-th bar, and
the change is stated rather than absorbed: blind stepping gives ~365 samples at the 99th
percentile where spacing-based selection gives roughly eight times more, while preserving the
non-overlap that keeps the sample honest. It is a strictly better sampler for tail work and
would have been the right choice in D215 too.

## Hurdles, all required

1. `p ≥ p*` for the cell's own cost model, on **both symbols**;
2. `n ≥ 100` in the bucket — below that it is reported **underpowered** and carries no verdict;
3. `p` holds on **both chronological halves** of the sample. D213 is the reason: a mined rule
   that inverted out of sample is the default outcome, not the surprise;
4. under **maker-in**, `p_maker ≥ p*`. Maker is the only tier where `p*` is reachable, so the
   verdict has to survive the fill convention that makes it reachable.

## Predictions

- **H1** — `p` keeps rising into the 15m tail but does not reach the mixed-fill break-even
  (~63.7%). Confidence **high**.
- **H2** — maker fills are adversely selected: `p_maker` at least 3 points below `p_taker`.
  Confidence **high**.
- **H3** — the effect exists at daily but is weaker than at 15m; daily crypto is the more
  momentum-driven regime. Confidence **moderate**.
- **H4** — no cell clears all four hurdles. Confidence **moderate-high**, deliberately not
  high. The daily maker break-even of ~50.5% is genuinely close to what the 15m top bucket
  already measures, and **this is the first cell in the whole programme where the arithmetic
  does not settle the answer before the run.**
- **H5** — the 99.5th bucket is underpowered at daily and adequately powered at 15m.
  Confidence **high**.

**H4 is the one to watch**, and the reason every guard in this document exists.

## The rule if it works, committed now

If a daily maker cell clears all four hurdles, **D215's pre-committed rule applies
unchanged**: that is a positive claim, it does **not** get pursued inside this study, and it
gets its own pre-registration and its own holdout before anyone believes it.

Writing that down before the number exists is the only way it survives contact with a good
one. The motivation for looking here came from an effect found by staring at the same data,
and a discovery under those conditions is a hypothesis, not a result.

## Ledger

15m tail: 4 cutoffs × 2 symbols × 2 fills = **16**. Daily: 2 symbols × 2 fills = **4** — top
bucket only, because the tail is unmeasurable on 4,017 bars and that is reported rather than
attempted.

**20 looks**, on the reversion ledger D215's Test A opened at 4. Running total **24**. The
structure programme's 395 are not inherited: no sensor, component or level is reused.

---

## RESULT

*Appended after the run. Nothing above this line was edited.*

### Scoring my own predictions

| | prediction | outcome | |
|---|---|---|---|
| **H1** | `p` keeps rising into the 15m tail but does not reach the mixed-fill break-even | rises 52.33% → 56.66% (BTC) and 52.89% → 61.43% (ETH); verdict-tier margin −4.50% and −2.16% | **confirmed** |
| **H2** | maker fills adversely selected by ≥ 3 points | +1.46% mean, 7 of 10 cells in the predicted direction | **falsified on magnitude** |
| **H3** | the effect exists at daily but weaker | daily 40.00% and 50.00% — absent or inverted, not weaker | **falsified** |
| **H4** | no cell clears all four hurdles | 0 of 10 on the verdict tier, 2 of 10 on the optimistic bound | **falsified as written** |
| **H5** | the 99.5th bucket underpowered at daily, powered at 15m | 15m powered (n = 410, 413); the daily 99.5th was never run | **half unfalsifiable as written** |

**One clean confirmation in five.** That is a bad prediction record and it is the honest
summary of this study. Three of the four misses are informative and one is my own drafting
error: H5 asserted something about a cell the design deliberately never measured, because the
Ledger section restricts daily to the top bucket. A hypothesis that names a cell the design
excludes cannot be scored, and writing both in the same document without noticing is exactly
the kind of thing pre-registration is supposed to prevent rather than merely record.

### What is actually true

**The effect keeps growing all the way into the tail, on both symbols, monotonically.** That
was the open thread and it is now closed with a yes. `p` reaches **56.66%** on BTC and
**61.43%** on ETH at the 99.5th percentile of move size, on 413 and 420 spaced events.

**And it still does not pay.** The mixed-fill break-even is 63.77% (BTC) and 60.76% (ETH) and
the arm that has to clear it — the maker arm, because a taker entry at 15m is arithmetically
impossible at any tier — reaches 59.27% and 58.60%. **The gap has closed from roughly 4× to
about 4 points and it does not reach zero.**

The two cells that cleared everything cleared `maker in/out`, which prices the stop as a
maker fill. You cannot rest a stop: a sell resting below a long's market price is immediately
marketable and crosses. So those two passes are real arithmetic on an untradeable fee model,
and they are reported as the bound they are.

**At daily the sign flips.** BTC's top bucket reverts 40.00% of the time — big daily moves
*continue*. This was predicted backwards (H3 expected a weaker reversion, not a reversal of
sign) and matches the standard stylised fact of intraday reversal against daily momentum. On
n = 120 and n = 100 it is a weak claim and is written down as one.

**One anomaly, named and not pursued.** At BTC's 99.5th the maker arm scores *better* than
the taker arm (59.27% against 56.66%) — adverse selection inverted, in the one bucket that
matters most. Two readings fit: noise at n = 410, or the trade-through requirement selecting
the most extreme continuations, which then revert hardest. **Distinguishing them is a new
study, not a paragraph here**, and D215's pre-committed rule applies: a favourable surprise
found while staring at the same data is a hypothesis, not a result.

### Three defects found, and how

**1. `rate()` returned 1.0 for every cell.** `sum(1 for _, ok in rows)` with no `if ok` counts
every row. Every cell read 100.00%, every hurdle "cleared", and the reading function
announced H4 falsified and a positive found. **No test caught it.** What caught it was the
halves function, which sums bools correctly and therefore said "not stable" while the
headline said 100%. Two views of one quantity disagreed — the same tell as D209, where the
census said 120 stacked setups and the lattice reported 2.

The contributing cause is worth more than the bug: `rate` was a **closure inside `measure`**,
so it could not be imported, so it was never pinned. It is now module-level `_rate`, pinned
against a hand-counted list, and a separate test requires the headline to equal the
sample-weighted blend of the two halves — making the disagreement that exposed the bug a
permanent gate instead of a lucky glance.

**2. The verdict table paired a taker fill with maker costs.** The first draft scored *both*
arms against *every* fee tier. That takes `p` from the population that crossed the spread and
the cost from the population that rested, and it produced a pass: ETH's 99.5th taker arm at
61.43% against the 60.76% mixed-fill break-even, clearing by +0.67%. It is not a near-miss
result, it is not a result at all — you cannot pay a maker fee and cross the spread. Each
tier now declares its arm in `FEES` and only the coherent pairing is scored. **Once corrected,
that cell reads 58.60% against 60.76% and fails.**

This is the more dangerous of the two, because unlike the rate bug it produced a *plausible*
number in the direction I was hoping for.

**3. The test fixture could not test the thing it was written to test.** `_bars` padded every
synthetic bar with a 0.1% wick on both sides, so a limit resting at the previous close was
always traded through: the maker arm filled 434 of 434 events and both fill-convention tests
failed against correct code. A fixture generous enough to fill everything cannot demonstrate
selective filling. Default padding is now zero.

### Ledger

**20 looks as pre-registered**, on the reversion ledger opened by D215's Test A at 4.
**Running total 24.** The structure programme's 395 remain uninherited.

### Disposition

The thread is pulled to its end. `p` rises into the tail further than D215 could see, the
gap to a tradeable cost narrows from a factor of four to about four percentage points, and it
does not close. The daily frequency, which the arithmetic said was the most promising cell in
the study, is the one place the effect is not there at all.

**No follow-up is opened.** The BTC maker-arm anomaly is recorded above as a hypothesis with
its two candidate explanations so that a future study can start from it rather than
rediscover it.
