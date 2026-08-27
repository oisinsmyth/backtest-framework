# D235 — Stops and targets on the recovery rule

**Status:** Pre-registered — committed BEFORE any runner exists
**Date:** 2026-08-27
**Area:** Strategy research

---

## Why this is worth running when fixed stops and targets are already measured to fail

Both are **measured destructive on the recovery rule**, and worse than on the parent:

| stop | pnl change | | target | pnl change |
|---:|---:|---|---:|---:|
| 1% | **−6.37** | | 2% | **−20.30** |
| 2% | −5.06 | | 3% | −18.34 |
| 3% | −4.72 | | 5% | −14.21 |
| 5% | −1.84 | | 8% | −11.33 |

*(unstopped total +21.71)*

**And there is a mechanism for each**, which is what makes the failures informative rather than
merely discouraging:

- **Fixed stops cut the entry dip.** The rule buys weakness by construction, so its trades draw
  down further before recovering — median **−1.62%** from entry against the parent's −1.38%, p10
  **−6.73%** against −5.10%. A stop cuts precisely the trades doing what the rule intends. *A
  dip-buyer with a stop is a contradiction.*
- **Fixed targets cap the tail.** Winners average **+7.31%** with a best of **+99.5%** — *more*
  fat-tailed than the parent's. The money is in crash rebounds, and a 2% target destroys them.

**A correction is recorded here rather than buried:** in conversation this rule was described as
mean-reverting, with the inference that its winners would be bounded and targets natural. **That
was wrong** — measured, its winners are more fat-tailed than the trend arm's. The entry is
mean-reverting; the exit is not.

**So the three variants below are chosen to avoid exactly those two failure modes**, and each is
a mechanism-derived hypothesis rather than a parameter search.

---

## The baseline

**The recovery rule**, unchanged: `position = 1 if hist_L > 0 AND md_L ≤ 0`.
**+0.746** excess Sharpe, 18.9% exposure, 6.1% vol, −10.30% max DD, 1,081 trades, 52.5% win rate,
mean hold 15.0 bars.

*Its existing exit is already a take-profit* — `md_L > 0` fires on 37.1% of exits, "sell at the
top of the channel". This study compares alternatives to an exit the rule inherited by accident,
rather than adding one where none existed.

---

## The three variants

### 1 — Breakeven stop (`BE`)

**Arms only after the trade is up X%, then exits if it falls back to entry.**

Never touches the entry dip — the thing fixed stops destroy — and only protects gains already
made. Once stopped, **stay flat until the base signal turns off and on again**; re-entering while
the level rule is still true would defeat the stop entirely.

`X ∈ {3%, 6%}`. **3% is the measured median best-gain-from-entry**, so roughly half of trades
arm; 6% is one further point. Derived from the distribution rather than chosen.

### 2 — Partial profit-taking (`PT`)

**Take half the position off at +X%, let the remainder run to the natural exit.**

Preserves the fat tail while reducing variance. `X ∈ {3%, 6%}`, same anchors for comparability.

*Declared cost:* this **reduces exposure**, so the √f penalty applies to the banked half. It must
clear that mechanical drag before it has done anything.

### 3 — Delayed target (`DT`)

**Enter below the channel as before; hold until `md_L > c` rather than `md_L > 0`.**

A hysteresis rule — the entry band and exit band differ — and the only variant expressed in the
rule's own dimensionless units, adding one parameter and no new normalisation.

`c ∈ {0.5%, 1.0%, 2.0%}`.

**Motivated by a number already in hand:** breakout bars earn **+0.062** excess Sharpe — poor,
but *positive* — so holding through the channel top costs little and may catch more of the tail.

**Seven cells in total.**

---

## The look-ahead trap, and how it is closed

D224 produced a **gross Sharpe of +4.197** from a stop that escaped an adverse move it could not
have escaped. It looked wonderful until the bug was found.

**Every exit here is close-to-close only.** A level is breached only if the *close* breaches it;
the exit takes effect on the **following** bar, consistent with `lag = 1` everywhere else. On
daily OHLC it is impossible to know whether an intrabar touch would have filled at the level or
gapped through it, so no intrabar fill is assumed anywhere.

**Pinned by test:** perturbing prices from bar *t* onward must move no position at or before *t*.

---

## Hurdles

- **P (carries the verdict).** Beat the recovery baseline on **excess Sharpe at rf = 4%, charged
  on the exposed fraction**.
- **B.** Clear a **best-of-search rotation null** over the seven cells — one offset vector per
  replication shared across cells, 1,000 replications, seed 0.
- **E.** Reported, and **known to fail**: the baseline is already at 9 entries per symbol against
  the 30 required, and no variant can raise it. Stated in advance, not waived.
- **√f decomposition per cell**, so each says whether it selected anything or merely traded less.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **V1** | **No variant beats the baseline** | **moderate-high** |
| **V2** | **`BE` does least harm of the three families** — it is the only one that neither cuts the entry dip nor caps the tail | **moderate** |
| **V3** | **`PT` loses money and falls roughly as √f on Sharpe** — it is a partial exposure cut wearing a risk-management label | **moderate-high** |
| **V4** | **`DT` is roughly neutral**, `|Δ| < 0.05` at every `c`, because breakout bars earn +0.062 — near zero either way | **moderate** |
| **V5** | **Nothing clears hurdle B** | **moderate-high** |

**V2 is the mechanism test.** If `BE` does *not* do least harm, then "stops fail because they cut
the entry dip" is the wrong explanation and the failure is something else.

---

## Stage 1 only

**Runs on the mined 57 and stops there.** The holdout is not touched, and neither is the
**2025–2026 forward window**, which D233 identifies as the resource actually worth protecting.

---

## Ledger

| count | N |
|---|---:|
| fresh — 7 cells | **7** |
| + D234's 6 | 13 |
| + D218's inherited | 75 |
| + disclosed ETF prior | **45,816** |

---

## Reuse — D212 is binding

| need | reuse | from |
|---|---|---|
| `md_L` and `hist_L` | `log_parts` | `run_activation_threshold.py` |
| rotation nulls, √f decomposition, rf-on-exposure, scoring | `rotation_nulls`, `score`, `_excess_sharpe` | `run_exposure_dial.py` |
| trade spans | `trade_spans` | `run_filter_search.py` |
| panel, costs, buy-and-hold | `load_panel`, `portfolio_log_returns` | `run_macd_ladder.py` |

**Written fresh:** the three exit overlays. They are stateful where every prior rule in this
programme was memoryless, which is the one genuinely new piece of machinery here — and the reason
the look-ahead test is not optional.

---

## STAGE 1 — SCREEN RESULT

*Appended after the run. **A screen, not a verdict.** The holdout and the 2025–2026 forward
window are untouched.*

**Produced:** 2026-08-27 · `uv run python scripts/run_stops_targets.py` · Page:
[`STOPS_TARGETS_RESULTS.md`](../../STOPS_TARGETS_RESULTS.md)

### The one-sentence version

**All seven cells beat the baseline and hurdle B cleared — and none of it is a result, because
hurdle B was the wrong control. Against a null that cuts the same number of trades short at
random bars, the best overlay sits at the 63rd percentile.**

### The cells

Baseline (recovery): **+0.746** at 18.9% exposure, +37.39% money. Buy-and-hold +0.235.

| cell | exposure | excess Sharpe | √f predicts | selection | Δ baseline | money |
|---|---:|---:|---:|---:|---:|---:|
| **BE@3%** | 17.5% | **+0.794** | +0.719 | +10% | **+0.047** | +33.22% |
| BE@6% | 18.4% | +0.747 | +0.737 | +1% | +0.001 | +34.62% |
| PT@3% | 14.7% | +0.767 | +0.659 | +16% | +0.021 | +26.07% |
| PT@6% | 16.6% | +0.748 | +0.700 | +7% | +0.002 | +29.45% |
| DT@0.5% | 20.0% | +0.764 | +0.769 | −1% | +0.018 | +39.35% |
| DT@1.0% | 21.1% | +0.772 | +0.790 | −2% | +0.025 | +40.72% |
| DT@2.0% | 22.9% | +0.781 | +0.821 | −5% | +0.035 | +42.97% |

### Hurdle B was the wrong control, and the record says so before the numbers are read

Hurdle B as pre-registered used the **rotation null** — the construction D231 and D234 used, and
correct there. **It is wrong for an overlay**, and it cleared trivially:

> Best real **+0.047** against a rotation-null p95 of **−0.284**. *Anything not actively harmful
> clears a bar that low.*

Rotation destroys the whole book's timing, so a rotated 17.5%-exposure book scores far below the
unrotated 18.9% baseline and the delta is hugely negative by construction. **It answers "is this
book better than a randomly-timed book?" when the question is "does the trigger's timing carry
information?"**

### The right control, built because the result was not trusted

Keep the base book. Cut **the same number of trades short — 146 of 1,124, 13.0% — at random bars
inside them**, instead of at the breakeven trigger. Then the only thing varying is *when* the
overlay fires.

| | excess Sharpe |
|---|---:|
| random-exit books, p05 | +0.735 |
| random-exit books, **p50** | **+0.785** |
| random-exit books, p95 | +0.836 |
| random-exit books, best of 400 | +0.870 |
| **BE@3%, the real overlay** | **+0.794** |

> **63rd percentile. The median random-exit book scores +0.785 against the real overlay's +0.794,
> and the best random one reaches +0.870.**

**The breakeven trigger carries no information.** Cutting 13% of trades short at random does
essentially the same thing. The +0.047 is "trimming some trades helps slightly on this book", not
"this stop is smart."

**Paired bootstrap, BE@3% vs baseline:** +0.047, interval **−0.082 to +0.177** — contains zero.

### Scoring

| | prediction | outcome |
|---|---|---|
| **V1** | no variant beats the baseline | **FALSIFIED on the letter** — all seven are positive — **and right in spirit**: none is distinguishable from random exits |
| **V2** | `BE` does least harm of the three families | **MOSTLY FALSIFIED.** BE mean +0.024, DT **+0.026**, PT +0.011. DT edges it, so "stops fail because they cut the entry dip" is not the whole explanation |
| **V3** | `PT` loses money and falls roughly as √f | **SPLIT.** It loses money (+26.07% against +37.39%) ✓ but **beat** its √f prediction by +16% ✗ |
| **V4** | `DT` is roughly neutral, \|Δ\| < 0.05 | **CONFIRMED.** +0.018, +0.025, +0.035 |
| **V5** | nothing clears hurdle B | **FALSIFIED as specified** — and B was the wrong test. On the correct null, nothing clears |

**One of five clean.** The worst prediction record in the programme, and the reason is
instructive: four of the five were framed around an effect that turned out to be too small to
have a sign worth predicting.

### The correction that outlives this study

> **A rotation null is the wrong control for an overlay.** Rotation randomises the *whole book's*
> timing, which is the right question for an entry rule and the wrong one for a rule that modifies
> an existing book. The correct control **keeps the base book and randomises only the overlay's
> decisions**, matched on how many it makes.

This should have been in the pre-registration. It was not, and the error was caught only because
a clean sweep of positive results looked wrong — the same tell that caught D224's look-ahead. **A
hurdle that everything clears is not evidence; it is a broken hurdle.**

**Standing rule, proposed:** any study applying an overlay to an existing book must null the
**overlay**, matched on its decision count, not the book.

### What survives

**Nothing is promoted.** The recovery rule stands unchanged at +0.746; stops and targets add
nothing beyond what randomly trimming trades would add.

**Two things are worth keeping.** The look-ahead gate held — close-to-close exits, effective the
following bar, no intrabar fill assumed, and no cell produced anything resembling D224's +4.197.
And the overlay-null construction is now available and should be used wherever an overlay is
tested.

### Ledger

| count | N |
|---|---:|
| fresh — 7 cells | 7 |
| + D234's 6 | 13 |
| + disclosed ETF prior | **45,816** |
