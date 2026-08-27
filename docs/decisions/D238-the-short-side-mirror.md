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
- **No look-ahead:** perturb a close from bar *t* onward and assert no position at any index
  <= *t* moves.
