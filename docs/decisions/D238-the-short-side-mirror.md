# D238 — The short-side mirror of the recovery rule

**Status:** Pre-registered — committed BEFORE any runner exists
**Date:** 2026-08-27
**Area:** Strategy research

---

## The question

[S1](../BOOK.md#s1--the-recovery-rule) buys an ETF sitting at or below its own volatility
channel that has started to climb back out. **Does the mirror work — short at or above the
channel, exit at the bottom band or on a stall?**

This is the first short book in the programme, and it is the leading candidate for the
**second, uncorrelated arm** that both `BOOK.md` and `AITODO.md` name as the highest-value
open item. The arithmetic there is specific: required data scales as `1/delta²`, so two arms
at ρ ≈ 0 give **×√2** and cut the significance requirement from 8.6 years to **4.3**.

---

## The rule

```
    S1      position = +1  if  hist_L > 0  AND  md_L <= 0
    MIRROR  position = -1  if  hist_L < 0  AND  md_L >= 0
```

Every term is S1's, with both inequalities flipped. `md_L`, `hist_L`, the 34/9 lengths, the
log construction, `lag = 1`, the 1,000-bar warm-up and the equal-weighted book are all
unchanged. **Nothing new is fitted and nothing is swept.**

Its exits fall out of the level rule exactly as S1's do: `md_L < 0` (price fell to the channel
bottom) or `hist_L >= 0` (the fall stalled).

---

## Four asymmetries, measured before the run

**"Basically the opposite" is the hypothesis being tested, not an assumption the design may
make.** Four things are not symmetric, and three of them are quantified here so they cannot be
reported later as discoveries.

### 1. The channel itself is asymmetric — the mirror is 1.56x more exposed

Measured over 86,355 live cells on the mined 57:

| where `md_L` sits | share of bars |
|---|---:|
| **above** the channel — `md_L > 0` | **55.37%** |
| **inside** — `md_L = 0`, the dead zone | 11.69% |
| **below** the channel — `md_L < 0` | 32.95% |

The zero-lag midline sits above the smoothed high band **two thirds more often** than it sits
below the smoothed low band. That is drift, printed into the indicator's geometry. So:

| | signal density | exposure after lag |
|---|---:|---:|
| S1 long | 18.87% | **18.87%** |
| **mirror** | 29.48% | **29.46%** |

**The mirror is not exposure-matched to S1 and cannot be made so without a fitted threshold.**
No threshold is introduced. Instead the √f decomposition is reported: the extra exposure buys
`√(0.2946/0.1887) = 1.25x` on Sharpe for free, so any comparison of the two arms' Sharpes that
ignores it is wrong by 25%.

### 2. The dead zone is shared, so the two rules are not a partition

`md_L <= 0` and `md_L >= 0` **both** contain the dead zone. They are disjoint only because the
`hist_L` signs are — confirmed, **0 cells fire both** — but they overlap on the region where
the indicator is saying nothing about level at all.

| | share of that arm's held bars in the dead zone |
|---|---:|
| S1 long | 22.56% |
| mirror | 15.37% |

**Because both readings of "at the top band" are defensible, both are registered as cells**
rather than one being chosen after the fact.

### 3. Compounding — the existing return code is wrong for a short, by 9.22 points

`run_macd_ladder.portfolio_log_returns` computes `position * log_return`. That is **exact** at
`pos ∈ {0, 1}` and **wrong** at `pos = −1`: a daily-rebalanced short earns `log(1 − r_simple)`
per bar, not `−log(1 + r_simple)`. The two differ by one variance per bar and the error runs
one way — it flatters the short.

**Measured on this exact book: `−11.97%` correct against `−2.75%` naive. An overstatement of
+9.22 percentage points**, which is most of the arm's result.

The fix is a generalisation that is **exactly backward-compatible**, so nothing already
published moves:

```
    per_bar = log1p(position * expm1(return))  +  log1p(-cost)

    pos = +1  ->  log1p(expm1(r))       = r         identical to the current code
    pos =  0  ->  log1p(0)              = 0         identical to the current code
    pos = -1  ->  log1p(-expm1(r)) = log(2 - e^r)   the correct short
```

This is written fresh rather than reused, and **D212 is satisfied by naming why**: the reuse
target is defective for the case at hand. `run_exposure_dial.score`, `_excess_sharpe` and
`rotation_nulls` all inherit the defect and are re-implemented for signed books.

### 4. Financing flips sign, and borrow is a new charge

For a **long-flat** book at exposure `f`, cash `(1−f)` earns `rf`, so excess return is
`f*(r − rf)` — the current `total − f*rf`. For a **short** book the investor holds their
capital in cash earning `rf` and runs the short against it, so:

```
    return = rf - f*r        excess = -f*r        NO rf term at all
```

The general form, which reduces exactly to the current one on every long-flat book already
scored:

```
    excess = total  -  mean(max(pos, 0)) * rf  -  mean(max(-pos, 0)) * borrow
```

**Borrow is charged at a stated 1.0%/yr on short notional** — deliberately conservative for a
basket mixing liquid index ETFs with sector and commodity funds. The **breakeven borrow rate**
is reported as a diagnostic rather than swept, so the sensitivity is visible without spending
cells on it.

**One friction is named and NOT modelled:** SEC Rule 201 restricts short sales at or below the
NBBO for the remainder of the day and the following day after a 10% intraday decline — which
is disproportionately when a short signal would want to act. The arm is therefore optimistic
in exactly the conditions it most depends on.

---

## The cells — three

| | rule | reading | exposure |
|---|---|---|---:|
| **M1** | `hist_L < 0 AND md_L >= 0` | the literal mirror — "at or above the channel", matching S1's "at or below" | 29.46% |
| **M2** | `hist_L < 0 AND md_L > 0` | strictly above the top band, the dead zone excluded | 24.95% |
| **M3** | `S1 − M1` | the combined book. The two never fire together, so this needs **no weighting choice**: a net position in `{−1, 0, +1}` at 48.3% gross | — |

---

## Hurdles — and the primary is not profitability

**A short book at 29.5% exposure against ~8%/yr of drift carries roughly −14% of mechanical
drag over this span.** The mirror's measured loss is −11.97%. Profitability is therefore close
to a foregone conclusion and tells us almost nothing. The question worth asking is whether the
*timing* carries information once the drift is matched away — and a matched-count rotation
null does exactly that, because a rotated short book has the same exposure and so the same
drag.

- **W1 (carries the verdict).** **M1 beats its matched-count rotation null at the 95th
  percentile.** Same exposure, same turnover, same holding periods, wrong bars. This is the
  only hurdle separating *the short signal has skill* from *shorting a rising market loses
  money*.
- **W2.** Excess Sharpe > 0 standalone, after borrow. Reported for completeness.
- **W3.** **M3 beats S1 alone** on excess Sharpe, with a **paired block bootstrap `p05 > 0`**
  on the difference — both arms recomputed on identical resampled dates, block 21.
- **W4 (R6).** Every leg above is computed in code or the runner fails loudly. Hurdle **E** is
  reported, not waived: >=100 pooled entries and >=30 per symbol.
- **Reported, not hurdles:** the √f decomposition, arm-vs-null **percentile** (not just p95),
  the breakeven borrow rate, and the two arms' return correlation.

**The percentile of the actual against the null is reported for M1 and M2, not just the pass
or fail.** Landing *below* the null median is a materially different and more interesting
outcome than landing near it — it would mean the mirror is an **anti-signal**, and an
anti-signal is usable where a null result is not.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **V1** | **M1's excess Sharpe is negative** after borrow | **high** — measured at −0.359 raw before financing; close to arithmetic |
| **V2** | **M1 fails W1** — no short-side skill survives the drift match | **moderate** |
| **V3** | **M1 lands *below* its null's median** — an anti-signal, not a null result. Shorting strength that has turned fights momentum, which is a real effect a rotated book does not have | **moderate** |
| **V4** | **M3 does not beat S1.** Arithmetic given the measured ρ: adding an arm helps only if `SR_B > ρ*SR_A`, and `ρ*SR_A = −0.069 × 0.746 = −0.051`, while `SR_B ≈ −0.36` | **high** |
| **V5** | **M2 does not materially beat M1** — excluding the dead zone changes 15% of held bars and should not change the verdict | **moderate** |

**V3 and V4 are the two that matter, and they point in opposite directions for what to do
next.** If V4 holds — and it is close to certain — then **the failure is the short arm's own
expected return, not a diversification failure.** The measured correlation is already
**−0.069**, which is the ρ ≈ 0 the second-arm argument needs. **The mirror supplies the
correlation and fails to supply the return.** That is a far more specific finding than "the
short side does not work", and it says the search for arm two should keep this correlation
target and look elsewhere for the edge.

---

## Stage 1 only

**The mined 57.** The holdout 60 and the 2025–2026 forward window are **not touched**. Under
R8 nothing here can reach `BOOK.md` without its own pre-registered out-of-sample test.

---

## Ledger

| count | N |
|---|---:|
| fresh — 3 cells | **3** |
| + D234's 6, D235's 7, D236's 6 | 22 |
| + disclosed ETF prior | **45,825** |

---

## Reuse — D212 is binding

| need | reuse | from |
|---|---|---|
| panel, cleaning, per-symbol costs, dividend frame | `load_panel`, `cost_fraction` | `run_macd_ladder.py` |
| `md_L` / `hist_L`, the base masks, the lag-shifted book | `base_masks`, `hold_book` | `run_stops_targets.py` |
| drawdown, total return, Sharpe convention | `max_drawdown_of`, `total_return_of`, `sharpe_of` | `run_macd_ladder.py` |
| the paired block bootstrap, block 21 | `paired_block_bootstrap` | `run_jerk_rung.py` |

**Written fresh, and the reason is asymmetry 3 — the reuse targets are defective for signed
books:** `signed_log_returns`, `score`, `_excess_sharpe` and `rotation_nulls`. Each is pinned
by test against its long-flat counterpart, so the generalisation is **demonstrated** to be
backward-compatible rather than asserted.

## Verification

- Full suite green, offline, deterministic; `--report-only` re-renders **byte-for-byte** (the
  idempotency defect appeared in D220, D222 and D229 — `CELL_ORDER` is explicit from the
  start, never a `sort_keys` round trip).
- **Backward compatibility is a test, not a claim:** `signed_log_returns` must reproduce
  `portfolio_log_returns` **exactly** on a long-flat book, and the new `score` must reproduce
  D237's published S1 numbers on the same fixture.
- **The short compounding is pinned against a hand-computed two-bar case**, so the sign and
  the second-order term are both checked rather than trusted.
- **No look-ahead:** assert `position[t] = mask[t−1]` on every symbol and every bar of the real
  panel — the whole of what a memoryless level rule promises. The mask's own causality belongs
  to `smma`/`zlema`/`sma` and is pinned by `test_macd_ladder`.

---

## STAGE 1 — SCREEN RESULT

*Appended after the run. **A screen, not a verdict.** The holdout 60 and the 2025–2026 forward
window are untouched.*

**Produced:** 2026-08-27 · `uv run python scripts/run_short_mirror.py` · Page:
[`SHORT_MIRROR_RESULTS.md`](../results/SHORT_MIRROR_RESULTS.md)

### The one-sentence version

**The short signal has real skill and cannot be traded: it identifies bars that underperform
the market by 7.6 points a year, but those bars still go *up* — so shorting them beats a
randomly-timed short by a wide margin and still loses money.**

### The four books

Buy and hold over the span: **+0.235** excess Sharpe, +62.59%, −34.60% max drawdown, 8.42%/yr.

| | rule | long | short | excess Sharpe | CAGR | vol | max DD | money |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **S1** | `hist>0 & md<=0` | 18.9% | — | **+0.746** | 5.43% | 6.1% | −10.30% | +37.39% |
| **M1** | `hist<0 & md>=0` | — | 29.5% | **−0.407** | −2.09% | 5.9% | −19.28% | −11.90% |
| **M2** | `hist<0 & md>0` | — | 24.9% | −0.450 | −1.96% | 4.9% | −16.93% | −11.20% |
| **M3** | S1 − M1 | 18.9% | 29.5% | +0.262 | 3.23% | 8.2% | −21.87% | +21.04% |
| **M4** | `hist<0` alone *(post-hoc)* | — | 47.8% | −0.458 | −5.43% | 13.2% | −43.95% | −28.49% |

**W1: 3 of 3. W2: 0 of 3. W3: FAILS.**

### W1 cleared everywhere — so the hurdle was audited before it was believed

All three registered cells beat their rotation null at the 99.9th–100th percentile. **Under
R7's corollary a clean sweep is a tell, not a triumph**, and there is a specific mechanism that
would produce exactly this with no skill at all:

> Sharpe is `mean / sd`. A real short book concentrates its exposure after declines, when
> volatility is high; a rotated one spreads the same exposure across calm bars too. **For a
> book whose mean is negative, a larger `sd` makes the Sharpe *less* negative.** An arm could
> therefore beat this null purely by being exposed in noisy weather.

So the same 1,000 rotations were re-scored on **money** and on **volatility**, neither of which
can be inflated that way:

| | Sharpe | null p50 | pct | **money** | **null p50** | **pct** | vol | null vol | **ratio** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **M1** | −0.407 | −0.970 | 100.0th | **−11.90%** | **−25.99%** | **100.0th** | 5.90% | 5.47% | **1.079x** |
| **M2** | −0.450 | −0.971 | 99.9th | −11.20% | −22.68% | 99.9th | 4.94% | 4.64% | 1.064x |
| **M4** | −0.458 | −0.958 | 100.0th | −28.49% | −36.92% | 99.1th | 13.23% | 8.50% | 1.556x |

**The volatility explanation is ruled out at 1.079x** — it would have needed roughly 2.4x to
account for the Sharpe gap. And M1 beats all 1,000 rotations **on money**: it loses −11.90%
where a randomly-timed short of identical exposure, turnover and holding periods loses
**−25.99%**. **The timing is real. It halves the loss.**

### The measurement that decides the reading

A rotation null can only establish that the selected bars **underperform**. A short needs bars
that **fall**. So:

| condition | bars held | annualised return of those bars |
|---|---:|---:|
| `hist>0 & md<=0` — **S1** | 16,303 | **+33.22%** |
| all live bars | 86,355 | +8.42% |
| `hist<0 & md<0` | 15,834 | +3.28% |
| `hist<0` alone — **M4** | 41,278 | +1.78% |
| `hist<0 & md>=0` — **M1** | 25,444 | **+0.85%** |

**The worst bars the indicator can name still return +0.85% a year.** That is 7.6 points below
the market and it is the wrong side of zero. An edge of that shape can never become a
profitable short — you are shorting something that rises, and paying dividends and borrow to do
it. **M1's breakeven borrow rate is −6.90%/yr: you would have to be *paid* 6.9% a year to hold
the position for it to break even.** Borrow is not what killed it, and no financing assumption
rescues it.

**`md_L >= 0` is doing real work, which the post-hoc M4 is what establishes.** Shorting on
`sign(hist)` alone selects bars returning +1.78%/yr; adding the level condition sharpens that
to **+0.85%**, roughly halving it. So this is **not** a restatement of the programme's known
one-bit finding — the level term adds short-side information the sign does not carry. It just
adds it in a direction that cannot be monetised.

*M4 was computed on the analyst's initiative after M1 cleared, because the reading turned on a
question the registration had not asked. Disclosed, and counted as a fourth look.*

### Why Sharpe reads backwards here, and why the tables above are the ones to trust

M1 scores −0.407 against M4's −0.458 and looks better. **On the numbers that matter it *is*
better, but not for that reason.** Per unit of exposure M1's shorted bars return +0.85% against
M4's +1.78%, and M1 is also the *less* volatile book (5.90% at 29.5% exposure, against 13.23%
at 47.8%). For a book with a **negative** mean, lower volatility drives the Sharpe *down*. The
ranking is right and the instrument that produced it is unreliable — the same lesson D236
recorded when Sharpe could not see drawdown.

### W3 — the combined book is decisively worse than S1 alone

| | excess Sharpe |
|---|---:|
| S1 alone | **+0.746** |
| M3 combined | +0.262 |
| **delta** | **−0.484** |
| paired bootstrap | **p05 −1.043, p95 −0.028** |

**The entire 90% interval sits below zero.** Adding the short arm to S1 costs 0.484 of Sharpe
and 16 points of money, and turns a −10.30% drawdown into −21.87%.

### Scoring — three of five, and the two misses are the interesting ones

| | prediction | outcome |
|---|---|---|
| **V1** | M1's excess Sharpe is negative after borrow | **CONFIRMED**, −0.407, and the breakeven borrow of −6.90% shows financing is not the cause |
| **V2** | M1 fails W1 — no skill survives the drift match | **FALSIFIED.** 100th percentile on Sharpe *and* on money |
| **V3** | M1 lands *below* its null median — an anti-signal | **FALSIFIED, and in the opposite direction.** It lands above every draw |
| **V4** | M3 does not beat S1 | **CONFIRMED**, −0.484 with the whole interval below zero |
| **V5** | M2 does not materially beat M1 | **CONFIRMED**, −0.450 against −0.407 |

**V2 and V3 were the substantive predictions and both were wrong.** I expected shorting
strength-that-has-turned to fight momentum and land below its null. It does the opposite: the
condition selects genuinely bad bars, by a wide and robust margin. **What it does not select is
bars that fall.**

### What this changes

**The correlation the second-arm argument needs was found, and it is not the missing piece.**
`corr(S1, M1) = −0.0687` — the ρ ≈ 0 that would give ×√2 on the delta and cut the significance
requirement from 8.6 years to 4.3. **The mirror supplies the correlation and fails to supply
the return**, and W3 shows the arithmetic is not close: a −0.407 arm cannot help a +0.746 arm
at ρ ≈ 0, because adding B helps only when `SR_B > ρ·SR_A = −0.051`.

That is a far more specific finding than "the short side does not work", and it retargets the
search: **arm two needs to clear roughly −0.05 excess Sharpe at ρ ≈ 0, not merely be
uncorrelated.** Uncorrelatedness was never the binding constraint.

**And there is a constraint here that is about the asset class, not the indicator.** Over this
span, on 57 long-only US equity ETFs, the worst-conditioned bars *any* of these constructions
can isolate still return +0.85%/yr. A short arm on this universe is fighting a drift the signal
is not strong enough to overcome. **If a short arm is wanted, it needs instruments that
actually fall** — which is a fixture decision, not a rule decision.

### What survives

**Nothing is promoted. The short side is closed as a standalone arm and as an addition to S1.**
It joins trade-level stops (D235) and portfolio-level risk controls (D236): measured, mechanism
understood, shut.

**Two things are kept.** The signed-book scorer is now correct and pinned — `position *
log_return` was wrong for shorts by 9.22 points, and every future signed study inherits the
fix. And the **money-and-volatility audit of a Sharpe-based null** is reusable: it is what
turned a suspicious clean sweep into a defensible finding, and it should run on any null where
the arm's mean is negative.

### Ledger

| count | N |
|---|---:|
| fresh — 3 registered cells | 3 |
| + M4, disclosed post-hoc | **4** |
| + D234's 6, D235's 7, D236's 6 | 23 |
| + disclosed ETF prior | **45,826** |
