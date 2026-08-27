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
