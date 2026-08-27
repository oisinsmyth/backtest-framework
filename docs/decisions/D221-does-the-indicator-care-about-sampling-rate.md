# D221 — Does Impulse MACD care about the sampling rate, or only about the window?

**Status:** Pre-registered — written and committed BEFORE the runner exists
**Date:** 2026-08-27
**Category:** Validation & research integrity
**Source:** A user proposal — scale the parameters by ×4 on 15m data so the window matches
1h, and see whether the results converge. *"In the case that they don't, that comparison
could drop an edge out."*

> A result section will be appended and nothing above it edited.

## What is being tested

**Sampling invariance.** Two estimators covering the **same wall-clock window** on the same
asset over the same days:

- **A** — 1h bars, Impulse MACD default `(34, 9)`
- **B** — 15m bars, parameters scaled so the window matches

Under the null that price is a continuous process and this indicator measures a *window*,
A and B compute nearly the same statistic and should agree. **Any disagreement is
attributable to one specific thing: the intrabar path detail that only the finer sampling
sees.** That makes this a paired test with a real null rather than a parameter sweep, and it
is the same shape as D218's `I1 − C ≈ 0` — two constructions that ought to be identical,
where the delta is the finding.

Both branches are informative, which is why the study is worth running:

| outcome | what it means |
|---|---|
| **A ≈ B** | the indicator is scale-free in bars; sampling rate is a free choice and should be picked on cost grounds alone |
| **B > A** | intrabar path carries signal the hourly series discards |
| **B < A** | the finer sampling is feeding the estimator noise, and coarser bars are strictly better |

## The scaling, derived rather than assumed

×4 is the right instinct and the wrong arithmetic. Impulse MACD's lags do not scale as `4n`:

- `smma` is Wilder, `α = 1/n`, steady-state lag **`n − 1`** bars
- the signal is `sma(md, s)`, lag **`(s − 1)/2`** bars

Matching 1h's `(34, 9)` therefore needs `N − 1 = 4 × 33 = 132` and `(S − 1)/2 = 4 × 4 = 16`:

| config | bars | params | channel lag | signal lag | warm-up |
|---|---|---|---:|---:|---:|
| **A** reference | 1h | (34, 9) | 33.0h | 4.0h | 1,000 |
| **B** naive ×4 | 15m | (136, 36) | 33.8h | **4.4h** | 4,049 |
| **C** lag-matched | 15m | (133, 33) | **33.0h** | **4.0h** | 3,958 |
| **D** unmatched | 15m | (34, 9) | 8.2h | 1.0h | 1,000 |

The naive ×4 overshoots the channel by 2.3% and the **signal window by 10%**. Both B and C
are run so the matching detail is measured rather than argued — if they agree, it did not
matter; if they do not, the study has found that this indicator is sensitive to a 10%
change in its signal window, which is worth knowing on its own.

**D is included as the floor**, not as a candidate: it is the configuration the arithmetic
gate already screened at gross Sharpe −0.400 (BTC), −1.826 (XEM), −2.674 (BTG), +0.159
(ETH). It shows what running the default parameters at the wrong sampling rate costs.

## Test bed

| | |
|---|---|
| Fixture | `crypto_binance_15m_raw` — true as-traded frame (D161), no splits or dividends |
| Symbols | BTCUSDT, ETHUSDT (293,336 bars each), XEMUSDT (122,599), BTGUSDT (51,479) |
| Calendar | **shared**: `census_days` on the 15m source, and a partial UTC day is dropped at *every* frequency so that sampling rate is the only variable (D161) |
| 1h series | built by `breakout_intraday.resample` from the same 15m source — never fetched separately, so the two series cannot disagree about what happened |
| PPY | 35,040 at 15m, 8,760 at 1h — D17/D108, 365-day calendar carried down to the bar |
| Book | long-flat only — the pre-declared arm from D218 and D220, not selected here |
| Costs | `DEFAULT_TIERS` (D114): `maker_0bp`, `maker_10bp`, `maker_25bp`, `taker_40bp` |

**The primary metric is GROSS (`maker_0bp`) Sharpe**, because the question is whether the two
estimators agree *as signals*. Costs confound that comparison — B trades on a 4× finer grid
and will pay more for the same wall-clock decisions — so net is reported beside it at every
tier and never substituted for it.

## The statistics

1. **Δ = Sharpe(B) − Sharpe(A)**, per symbol, gross. The headline.
2. **ρ**, the correlation of the two arms' return streams on the shared 1h grid. Sharpe
   agreement with low correlation would mean two different signals that happen to score
   alike, which is not invariance.
3. **Round trips per year**, per config. The mechanism behind any net-of-cost gap.
4. **Δ for C − A**, to price the naive-×4 mismatch.

## Hurdles

This study tests a null rather than hunting a survivor, so the structure differs and says so:

**I. Invariance holds** if `|Δ| ≤ 0.15` on **every** symbol **and** `ρ ≥ 0.80` on every
symbol. Both, because either alone is satisfiable by accident.

**J. The arithmetic gate still binds.** Any config whose round-trip cost at `taker_40bp`
exceeds its own mean absolute trade move is **dead on arithmetic** and carries no tradeable
verdict regardless of its gross Sharpe (D206/D216). The 15m default already failed this at
0.99× on BTC, and the gate is reported for every config.

**No config is promoted by this study under any outcome.** D219's dual verdict is not
applied and no survivor can be declared here, because the question is about an estimator's
behaviour and not about a tradeable arm. A positive gross Sharpe found here gets its own
pre-registration or it gets nothing.

## Predictions, committed before the run

| | Prediction | Confidence |
|---|---|---|
| **M1** | Invariance **fails**: `B < A` on gross Sharpe for the majority of symbols | **moderate** |
| **M2** | The mechanism is `zlema`. It is `2·EMA₁ − EMA₂`, which **boosts high frequencies**; at 4× finer sampling it amplifies proportionally more microstructure noise into the same wall-clock window | **moderate** |
| **M3** | B trades **more round trips per year** than A despite the matched window, because a finer grid whipsaws around the same zero crossings | **high** |
| **M4** | B is therefore worse than A **net** at every non-zero fee tier, by more than the gross gap | **high** |
| **M5** | C (lag-matched) lands **closer to A** than B does — the 10% signal-window overshoot is the larger of the two mismatches | **moderate** |
| **M6** | D (unmatched default) is far below all three, confirming the screen | **high** |

**What would change my mind:** M1 failing in the other direction — `B > A` by more than 0.15
gross on BTC and ETH both. That would mean intrabar path carries real signal, which is the
outcome that would justify intraday work on this indicator rather than closing it, and it is
exactly the "edge dropping out of the comparison" the proposal was reaching for.

## Ledger

| block | looks |
|---|---:|
| 4 configs × 1 book, symbols as sample not hypotheses | **4** |
| **fresh, D221 only** | **4** |
| inherited from D217 + D218 + D220 | 74 |
| crypto-fixture prior (registry distinct configs) | 3,344 |
| structure/terrain disclosed bar — **on this exact fixture** | 395 |
| **verdict count** | **3,817** |

**The ETF prior does not carry here** and the crypto prior does, per D219's amendment —
which also recorded that this relief is worth **0.09–0.20 Sharpe**, not a transformation,
because the floor is logarithmic in N. The floor is not the binding constraint in this study
anyway: no arm is promoted.

Zero-look: the arithmetic gate (a bound is not a hypothesis), the day census, the resample
report, and the four gross Sharpes already screened for config D.

## Pre-committed stops

- **The shared-calendar gate.** If the 1h series built by resampling does not contain exactly
  `complete_days × 24` bars, the run halts. `ResampleReport.check()` raises rather than warns
  for exactly this reason, and a series one bar short is a series whose comparison is void.
- **The warm-up gate.** B and C need ~4,000 bars of burn-in against A's 1,000. All four
  configs are scored on the **same wall-clock span**, the latest common start, or the
  comparison is between different samples rather than different sampling rates.
- **No parameter search.** Four configs are declared here and the grid is not extended. If B
  disagrees with A, the response is *not* to tune B until it agrees.
