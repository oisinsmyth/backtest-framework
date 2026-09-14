# D528 ADDENDUM — the causal rolling detector hits its target at exactly the sign-shuffle rate

Date: 2026-09-14. Runners: `working/d528_rolling_aligned_detector.py`,
`working/d528_rolling_diag.py`, `working/d528_stop_fill_and_null.py`.

**Nothing admitted (R15). No pre-registered statistic is changed. The reserved slice
(2026-04-11 → 2026-09-09) remains UNREAD.** This is a diagnostic addendum on the in-sample window,
and every variant in it is exploratory relative to the original pre-registration — it is recorded
as a design close-out, not as a test of a new primary.

---

## 0. What prompted it: three corrections from the principal

1. **"I don't think you understood what I meant by not trading against the drift."** The rule is:
   when the window is mean-reverting, wait for the price to be at the **low** extreme before going
   long if the drift is positive, and at the **high** extreme before going short if it is negative.
   *Never short against a positive drift and never long against a negative drift.*
2. **"The window must classify the regime as mean reverting at the time of the trade at that time
   scale ← very important."**
3. **"Given that the price reverts perfectly does this trade pay for itself? There is no point in
   making a trade, that even under perfect conditions wouldn't make money."**

All three are implemented. Each changed the construction materially, and (3) turned out to change
the **exit**, not only the entry filter.

---

## 1. Two corrections to my own earlier reporting

### 1.1 My "tailwind" label was wrong in prose and right in code

With `y = P − level` and `s = sign(y)`, the trade direction is `−s`, so the principal's rule is
exactly `s·slope < 0`. That is the cell I had labelled "tailwind" and *described* as "the level
drifts toward the price". **It drifts away.** `s = −1` with `slope > 0` is a rising level above a
price beneath it, and the gap widens.

That is why the principal's cell measured the **lower** P(return): 0.11–0.13 against 0.37–0.42.
Both numbers are real; neither was an edge:

| cell | what happens | P&L drift term `−s·slope·d` |
|---|---|---|
| `s·slope < 0` — the principal's | level recedes, a residual return is hard | **> 0, the drift pays the position** |
| `s·slope > 0` | level chases the price, the residual "returns" because the LEVEL moved | < 0, the return earns nothing |

**So `P(residual return)` was the wrong target statistic all along: it can be satisfied entirely by
the level's own motion.** It is replaced throughout by **P(price reaches a FIXED price set at
entry)**, which no level motion can manufacture.

### 1.2 A sentinel-precedence defect, which contaminated the first pass

When neither target nor stop was reached, both hit-indices held the same `1<<30` sentinel, so
`if i_s <= i_t` was **True** — recording a **timeout as a stop at the stop price** and setting the
next-entry barrier a billion bars ahead, which silently discarded every later entry in that
session. Fixed; self-test 9 reproduces the no-hit case, asserts ties go against us, and asserts the
**old** precedence fails it (a check that cannot fail is worse than none).

Effect of the fix at s=1: 2,478 → 2,540 trades, gross −0.03 → **+2.29** ticks. Every number below
is post-fix.

---

## 2. The construction

Rolling: **every bar** is a candidate, and everything read precedes it.

| element | definition |
|---|---|
| windows | `W_prev = [t−2H, t−H)`, `W_cur = [t−H, t)`, `H = 10` |
| **held level** | `W_prev`'s line extrapolated across `W_cur`'s bars — residual measured on bars the level never saw |
| classifier | crossings of the held level ≥ 2, **and** slope stability `\|b1−b2\|·H ≤ 0.5·σ_pooled`, **and** median `\|Δ\|` ≥ 4 ticks |
| trading level | `W_cur`'s line at bar `t` — **one** bar of extrapolation, not eleven |
| entry | `\|y\| ≥ 2σ` **and** `s·slope < 0` **and** `\|y\|/tick > cost` |
| target | `lvl_t`, **frozen at entry** — a resting limit |
| stop | `P_t + s·f·\|y\|`, **frozen at entry** — `f = 0.5` (D471: a stop must be ~half the target) |
| timeout | 20 bars, out at market |

**Why the classifier counts crossings of a HELD level.** A least-squares level over its own bars
forces its residual to sum to zero, so it *must* be crossed — the saturation finding
(P(return) 0.9077 on a random walk). Self-test 3 measures it: a self-fitted level is crossed in
**400/400** random walks, the held level in **210/400**. A saturated crossing count would measure
arithmetic, not the market.

**Why freezing both exits matters.** The ten decile charts showed the trades were stopped out by
the level's own extrapolated slope, not by price — slope 7–10 tk/bar against σ 11–29, closing a 1σ
gap in 1–3 bars. Freezing the exits as prices removes that **structurally**, rather than filtering
it.

---

## 3. The answer to correction (3): yes, and that is why it cannot be the problem

Under perfect reversion the exit is the frozen level, so the gross gain is **exactly `|y|`**:

```
(−s)·(lvl_t − P_t) = (−s)·(−y) = s·y = |y|
```

Median `|y|` at a 2σ entry is **31.1 ticks**, against a measured round-trip crossing of 1.06–4.99
ticks. **The trade pays for itself under perfect reversion by roughly 7–30×.**

The filter therefore blocks **nothing** at the operating point — 69 trades at x=0.5, 3 at x=1.0,
1 at x=1.5, **0 at x ≥ 2.0.** It is already implied by the 2σ entry combined with the 4-tick
lattice floor. **The principal's test is correct and it is satisfied by construction here, so no
cost-side fix can rescue this trade.** It would bind on a thinner root or a shallower entry.

---

## 4. The primary result: the excess over the sign shuffle is zero at every stop width

s=1, x=2.0σ, τ=20, classifier on, drift-aligned, 35 roots, 20 shuffles, **realised** stop fill.

| stop/target | trades | P(target) | null | EXCESS | SE | p_be | NET real | NET ideal | fill gap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.25 | 2,549 | 0.2903 | 0.2886 | **+0.0017** | 0.0092 | 0.2726 | **−6.77** | +1.98 | +8.76 |
| 0.50 | 2,540 | 0.3547 | 0.3541 | **+0.0006** | 0.0097 | 0.3939 | **−7.67** | −0.23 | +7.44 |
| 0.75 | 2,530 | 0.3996 | 0.4003 | **−0.0007** | 0.0100 | 0.4805 | −7.83 | −1.99 | +5.85 |
| 1.00 | 2,518 | 0.4373 | 0.4329 | **+0.0044** | 0.0101 | 0.5454 | −7.62 | −2.58 | +5.04 |

**Every rung is inside half a standard error of its own sign shuffle.** The shuffle holds `|r|` in
place and randomises only signs, so it preserves the return distribution, the fat tails and the
volatility clustering, and destroys exactly the claim under test: that the **arrangement** of signs
after an extreme is reverting.

**On 1-minute quoted mids across 35 roots, the probability that price reaches a level before a stop
is fixed by the size distribution of the moves and their volatility clustering. The arrangement of
the signs adds nothing.**

### 4.1 Two errors would have produced a false positive, and both flattered the tightest stop

1. **The idealised stop fill.** A resting *limit* fills at its own price, so taking the target at
   `tgt` is right. A *stop* becomes a market order and fills at or beyond the stop, never better.
   Filling at exactly `stp` was worth **+8.76 ticks per trade** at f=0.25, and the tighter the stop
   the more often it applies — a monotone "excess" decay with stop width, out of nothing.
2. **The closed-form breakeven.** `f/(1+f)` says 0.20 at f=0.25; the sign shuffle says **0.2886**.
   That +8.9 pp is a property of fat-tailed, volatility-clustered paths and is present identically
   in the shuffle.

Together these turned **−6.77 into +1.98** and produced a `+0.0177` margin at f=0.25 that does not
exist. CLAUDE.md's "simulated benchmarks, never closed-form" is what caught it.

---

## 5. Neither layer of the detector carries information

Four cells at s=1, f=0.5, x=2.0 (idealised fill, so read the *contrast* not the level):

| classifier | side | trades | P(target) | GROSS tk | NET tk | median |
|---|---|---:|---:|---:|---:|---:|
| on | **aligned (the principal's rule)** | 2,540 | 0.3547 | +2.29 | −0.23 | −10.73 |
| on | anti-aligned (control) | 1,178 | 0.3684 | +4.30 | +1.77 | −9.87 |
| off | aligned | 117,752 | 0.3586 | +1.51 | −0.90 | −4.10 |
| off | anti-aligned | 68,198 | 0.3748 | +1.79 | −0.63 | −4.08 |

**P(target) moves 2 pp across a 46× change in selectivity.** The classifier selects 2.1% of bars
and buys nothing measurable.

**The alignment rule reads slightly worse than the side it rules out** — 0.3547 against 0.3684 —
but at **0.8 SE** that difference is not real either. The defensible statement is that the
alignment rule neither helps nor hurts at this scale, not that the control is better.

### 5.1 Scale, and the principal's brainwave

Excess against the null by scale (f=0.5): **+0.0010** (s=1), −0.0103 (s=2), −0.0355 (s=3),
−0.0453 (s=5), −0.0255 (s=8). **Small scales do best and the larger ones are worse than their own
shuffle** — which is the direction the principal predicted when he said causality should break the
oracle's self-similarity. The causal construction is not scale-free; the oracle was.

---

## 6. The decay chain, step by step

| version | excess | what the previous step's excess actually was |
|---|---:|---|
| D528 oracle, A1+A2, `P(residual return)` | +0.1049 | selection on the very half being traded |
| shifted causal, `P(residual return)` | +0.0161 | 16% survived; A1-passing barely persists (0.0665→0.0811) |
| rolling causal, `P(fixed price)` | **+0.0006** | the residue was level motion satisfying the statistic |

Each step removes one named artefact and the excess falls by roughly an order of magnitude. There
is nothing left at the end of it.

---

## 7. Trade distribution, and why it is not a tail story

s=1, aligned, classifier on, f=0.5, x=2.0, idealised fill: n 2,540, mean −0.23, **median −10.73**,
win 39.0%, skew +1.16, kurt 8.71. Trimmed 1% both tails **−0.87**; ex-top −2.23; ex-bottom +1.13.
Top 1% carries **13.3%** of gross positive P&L — under the 30% threshold at which an edge is
tail-carried, so this is not a lottery book that a trim would expose. It is simply flat, and
negative once the realised fill is used.

---

## 8. Disposition

**This construction is closed: the rolling drift-aligned detector with a fitted-line level and
frozen target/stop, at s = 1–8 on the 1-minute quoted mid.** Its excess over its own sign shuffle
is zero at four stop widths spanning hitting probabilities 0.29–0.44.

**This does NOT close intraday mean reversion as an axis, and it is not mine to close** (only the
principal closes an avenue). What it closes is this detector and this exit.

### 8.1 No component line, and why

Per CLAUDE.md every construction tested for either book gets a component line. **This one does not
earn one because it is not a scored construction:** its gross per-trade mean is at or below zero
under the realised fill and its excess over the null is inside half an SE, so there is no signal to
compute a component Sharpe on. Recording a component line here would imply a candidate exists.

### 8.2 The one structural route the numbers actually point at

The fill gap is **+5.0 to +8.8 ticks per trade** — larger than any other quantity in this record,
including the whole crossing cost. **Where the money goes is the stop crossing the spread.** The
route that follows is passive on both sides: rest the entry, rest the target, and replace the stop
with a time exit so nothing crosses. That introduces adverse selection and non-fills, which are
not measured here and must not be assumed away. It is the same maker question already flagged for
C6, and it is named as an avenue, not a result.

### 8.3 What remains open and unread

- The reserved slice **2026-04-11 → 2026-09-09 is still UNREAD** and is not spent by this addendum.
- The real-vs-shuffle A1 admission comparison remains uncomputed, so D528's P4 is still
  uninterpretable.
- Slope shrinkage λ ∈ (0,1) between `half_flat` and `half_line` is still untested.
