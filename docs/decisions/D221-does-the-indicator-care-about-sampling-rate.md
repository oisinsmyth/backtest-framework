# D221 — Does Impulse MACD care about the sampling rate, or only about the window?

**Status:** Committed (INVARIANCE HOLDS; M6 confirmed, M1–M5 falsified)
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

---

## RESULT

*Appended after the run. Nothing above this line was edited.*

**Produced:** 2026-08-27 · **Reproduce:** `uv run python scripts/run_sampling_invariance.py`
(offline, deterministic) · Page: [`SAMPLING_RESULTS.md`](../results/SAMPLING_RESULTS.md) ·
Artifact: `data/sampling_invariance_summary.json`

### The one-sentence version

**Invariance holds on every symbol — `|Δ| ≤ 0.15` and `ρ ≥ 0.94` between 15m×4 and 1h — so
this indicator is scale-free in bars and cares only about the window; and the control proves
it, because the same indicator at the same sampling rate with an *unmatched* window
correlates at only 0.50 and loses up to 4.2 Sharpe.**

### Scoring my own predictions

| | Prediction | Outcome |
|---|---|---|
| **M1** | Invariance fails, `B < A` on the majority of symbols | **FALSIFIED.** It holds. Deltas are +0.054, +0.080, −0.103, −0.149 — noise around zero, not a direction |
| **M2** | The mechanism is `zlema` boosting high frequencies, so finer sampling injects more microstructure noise | **FALSIFIED.** No systematic degradation. Naming a mechanism did not make it real — presumably the high-frequency boost lands on a 136-bar smoothed series whose HF content is already gone |
| **M3** | B trades **more** round trips per year than A despite the matched window | **FALSIFIED.** 222 vs 226 (BTC), 228 vs 226 (ETH), 215 vs 217 (BTG), 234 vs 239 (XEM). Essentially identical, and B trades *fewer* on three of four. The whipsaw argument was wrong |
| **M4** | B is therefore worse than A net at every non-zero tier | **FALSIFIED.** B is **better** net on BTC (−0.28 vs −0.39) and ETH (−0.01 vs −0.10) |
| **M5** | C (lag-matched) lands closer to A than B does | **FALSIFIED.** B is closer on BTC and BTG, identical on ETH, C closer only on XEM. **The naive ×4 was as good as the derived lag-match**, so the arithmetic about Wilder's `n−1` was correct and did not matter |
| **M6** | D (unmatched default) is far below all three | **CONFIRMED**, emphatically |

**One of six.** The proposal was right on every point where it and I differed, and this
record should say so plainly rather than bury it in a table.

### What is actually true

**1. The window is the variable. The sampling rate is not.**

| symbol | A · 1h (34,9) | B · 15m ×4 (136,36) | Δ | ρ |
|---|---:|---:|---:|---:|
| BTCUSDT | +0.681 | +0.735 | **+0.054** | 0.95 |
| ETHUSDT | +0.733 | +0.813 | **+0.080** | 0.96 |
| XEMUSDT | −0.547 | −0.650 | **−0.103** | 0.96 |
| BTGUSDT | +0.767 | +0.617 | **−0.149** | 0.96 |

Against the control — the same indicator, the same 15m bars, the *unmatched* default window:

| symbol | D · 15m (34,9) | Δ vs 1h | ρ | RT/yr |
|---|---:|---:|---:|---:|
| BTCUSDT | −0.298 | **−0.979** | **0.50** | 946 |
| ETHUSDT | +0.224 | −0.510 | 0.50 | 939 |
| XEMUSDT | −1.939 | −1.392 | 0.58 | 990 |
| BTGUSDT | −3.416 | **−4.183** | 0.50 | 961 |

**Matched window: ρ = 0.95. Unmatched: ρ = 0.50.** The correlation is the cleanest statement
of the result — at a matched window the two estimators are measuring the same thing, and at
an unmatched one they are measuring different things while wearing the same name.

**2. The earlier screen's conclusion was a parameterisation artifact, and it was mine.**

The arithmetic gate reported gross Sharpes of −0.400, +0.159, −1.826 and −2.674 at 15m and
concluded the signal was dead at that frequency. **That conclusion was wrong.** It ran the
default `(34, 9)` on 15m bars, which is an 8-hour channel against the 1h version's 33-hour
one — a comparison between two different indicators, reported as a comparison between two
timeframes. Matching the window moves BTC from −0.298 to +0.735 on the same bars.

The screen's *cost* arithmetic stands; its *signal* conclusion does not, and nothing should
cite it.

**3. Round trips are set by the window, not the bar rate.**

~225 per year at a 33-hour window whether the decisions are taken on 15m or 1h bars, against
~950 at an 8-hour window. This is why the cost problem and the signal problem had the same
cause: the 15m default was trading four times too often *and* measuring the wrong thing, and
both were the window.

**4. Two of four symbols are positive gross, and the signal is not universal.**

BTC and ETH are positive at every matched config; XEM is negative at all of them. That is
dispersion worth reporting rather than averaging away.

### Defects and disclosures

**Nothing here is tradeable, exactly as pre-committed.** At `taker_40bp` every matched config
is deeply negative (−0.81 to −3.54). At `maker_10bp` only BTG is positive (+0.37 / +0.26) —
**and BTG is the least reliable series in the study**: 372 complete days against **179
dropped**, a 32% dropout, on a 1.4-year span. It should be read as noise, not as a signal,
and it is named here so it cannot be quoted later as the one that worked.

**The shared calendar drops real data and the amounts are unequal.** BTG loses 179 days and
XEM 132, because `clean()` removes zero-volume bars and `census_days` then rejects any UTC
day left incomplete — at *both* frequencies, which is the point (D161). BTC and ETH lose
nothing. The comparison is valid within each symbol; the spans are not equal across symbols.

**The repo's only native 1h crypto fixture is unusable, and that is a finding in its own
right.** `crypto_intraday_1h_raw` is **50.4% zero-volume bars** — the cleaner drops 17,520 of
them, leaving an irregular ~2h series wearing a 1h label. It cannot support a frequency
comparison and cannot support any volume work. The 1h arm here is resampled from the 15m
source for that reason, which also removes the provider confound: both series are built from
the same trades.

### Ledger

| block | looks |
|---|---:|
| 4 configs × 1 book, symbols as sample not hypotheses | **4** |
| inherited from D217 + D218 + D220 | 74 |
| crypto-fixture prior + structure/terrain bar on this fixture | 3,739 |
| **verdict count** | **3,817** |

**No config is promoted, so no floor is applied.** This study asked how an estimator behaves,
not whether an arm is tradeable, and a positive gross Sharpe found here gets its own
pre-registration or it gets nothing.

### What this changes

**Frequency is now a cost decision, not a signal decision.** Since the estimator is scale-free
in bars, the only reasons to prefer one sampling rate over another are execution granularity
and fees — and the fee arithmetic already says coarser is better, because round trips scale
with the window and the window is what you choose. **Anyone porting this indicator across
timeframes must scale the parameters or they are changing the hypothesis**, which is precisely
the error the earlier screen made.

**The `×4` heuristic is good enough.** The derived lag-match `(133, 33)` gave no advantage over
the naive `(136, 36)`, so the practical rule is simply to multiply the parameters by the
frequency ratio.

The open question this does *not* answer: whether a matched-window arm clears anything on a
fixture where fees are payable. That needs its own pre-registration, and on the evidence here
it needs a venue at maker rates or a coarser bar.
