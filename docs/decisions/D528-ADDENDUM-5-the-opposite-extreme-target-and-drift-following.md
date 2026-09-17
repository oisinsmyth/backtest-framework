# D528 ADDENDUM 5 — the opposite-extreme target works, drift-following stops help, and the null now makes positive gross

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D528-ADDENDUM-5-the-opposite-extreme-target-and-drift-following-stops.md`. The H1 above is the full title.*

Date: 2026-09-14. Runner: `working/d528_opposite_extreme_and_drift_stops.py`.

**Nothing admitted (R15).** Micro universe (8 roots), in sample only; the reserved slice
(2026-04-11 → 2026-09-09) remains UNREAD. Further in-sample looking on a window read repeatedly
this session. **Declared before running:** target = opposite extreme, `G = 3.0`, frozen, τ = 40,
`traverse`, 3 slots, one cell, both lenses. Everything else is a ladder and is description.

---

## 0. Two corrections to what was reported to the principal earlier in the session

### 0.1 "Your stop proposal is the stop already in place" was wrong in practice

The claim: entry at `X = 2σ`, stop at `1.5·X = 3σ` from the level, so the stop is `1σ = 0.5·|y|`
beyond the entry — the existing `f = 0.5`. Self-test 1 asserts that identity and it passes.

**It holds at the THRESHOLD and not at the realised entry.** `|y| ≥ X·σ` is tested once per bar and
the crossing bar lands well past it: **the mean entry is 2.68σ, not 2.0σ.** So `G = 3.0` sits only
0.32σ beyond the average entry — an effective `f ≈ 0.12`, far tighter than `f = 0.5`. The
`f=(G−X)/X` column in §4's ladders is computed at the threshold and is mislabelled for the same
reason: `G = 4.0` reads "f=1.00" and is really `f ≈ 0.49` on realised entries.

The same overshoot is why the two readings of "the opposite extreme" differ, and both are carried
rather than guessed:

| target | residual | mean travel | perfect payoff |
|---|---|---:|---:|
| `level` | 0 | 2.68σ | ×1.00 |
| `opposite` — far edge of the ±Xσ band | `−s·X·σ` | 4.68σ | ×1.78 |
| `reflect` — mirror of the actual entry | `−y` | 5.36σ | ×2.00 |

### 0.2 "Drift-following exits should hurt" was wrong, and the mechanism is the reverse

The prediction was that under `s·slope < 0` the level recedes, so a drift-following stop tightens a
long while its target recedes — hurting both sides. **Net improves in 8 of 9 cell × target pairs.**

Cell C net $/trade: `level` −5.16 → **−3.17**; `opposite` −2.87 → **−2.56**; `reflect` −3.66 →
**−1.66** (the best net in the file). Cell A: −6.86 → −5.61, −6.19 → −5.26, −5.93 → −5.27.

**The mechanism is that a drift-following stop triggers EARLIER, so less overshoot accumulates.**
Cell C `opposite`: hold falls 5.5 → 4.9 bars, stop share rises 76.1% → 83.5%, and payoff rises
2.38 → 2.92. More stop-outs, each one smaller. It behaves as a trailing stop that cuts losers
faster — which is the opposite of the runaway the frozen exits were introduced to fix, because the
runaway was in the TARGET receding, not in the stop tightening.

## 1. The opposite-extreme target works on the arithmetic, as predicted

Cost is fixed per round trip; the target is not. Cell C, frozen exits, path-invariant:

| target | perfect $ | cost as % of perfect | payoff | P(target) | GROSS $/tr | NET $/tr |
|---|---:|---:|---:|---:|---:|---:|
| `level` | 33.60 | 13.9% | 1.50 | 25.7% | −0.50 | −5.16 |
| **`opposite`** | 58.86 | **7.9%** | **2.38** | 16.5% | **+1.79** | **−2.87** |
| `reflect` | 67.20 | 6.9% | 2.46 | 14.7% | +1.00 | −3.66 |

**Cost share halves, payoff rises from 1.50 to 2.38, and the net loss halves.** It also aligns the
classifier with the target for the first time: `traverse` selects windows in which price crossed
the full width of the range, and the level target only asked for half of it.

**There is an interior optimum.** `reflect` is farther and *worse* — non-completion costs more than
the extra cost amortisation gains. The same ordering holds in cell A (`opposite` −6.19 vs `reflect`
−5.93 is the one exception) and cell B (−5.13 vs −4.93, also reversed), so the optimum's location
is not stable across cells.

## 2. But the declared primary is inside its null on BOTH lenses

`traverse`, `opposite`, frozen, G=3.0, τ=40, 3 slots, 20 sign-shuffled universes:

| lens | real | null p5 | p50 | p95 | reading |
|---|---:|---:|---:|---:|---|
| path-invariant gross $/trade | +1.79 | −5.45 | **+1.11** | +3.90 | inside the band |
| path-variant Sharpe gross | +0.73 | −2.20 | +0.35 | +1.12 | inside the band |
| path-variant Sharpe net | −1.17 | −4.25 | −1.19 | −0.24 | inside the band |

**THE NULL'S GROSS IS NOW POSITIVE — median +$1.11.** With this geometry a sign-shuffled universe
produces positive gross per trade, so **positive gross has stopped being evidence of anything.**
Cell C's +$1.79 barely clears the null's median. This is the same lesson as ADDENDUM 2 §4.1 in a new
place: the benchmark has to be simulated under the exact geometry, because the geometry itself
generates a number.

Cell B (`no classifier`) is **above p95** on both gross measures — invariant gross −0.46 against a
p95 of −0.91, variant Sharpe gross −2.20 against −4.26 — and inside the band on net. That is the
same cell that carries the +0.0410σ drift (ADDENDUM 2). **Both sides are negative, so the
comparison is empty** ("beats the control is empty below zero"), but the direction is consistent
for the seventh time.

## 3. One ladder rung turns positive, and it is not a finding

Cell C, `opposite`, frozen, τ=40, stop ladder:

| G | n | P(tgt) | STOP% | TO% | win% | payoff | GROSS $ | NET $ | book Sh_n | maxDD/$2,000 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2.5 | 109 | 11.0% | 84.4% | 4.6% | 18.3% | 3.10 | +1.38 | −3.28 | −1.75 | 0.18 |
| 3.0 | 109 | 16.5% | 76.1% | 7.3% | 24.8% | 2.38 | +1.79 | −2.87 | −1.17 | 0.24 |
| 3.5 | 109 | 21.1% | 69.7% | 9.2% | 29.4% | 1.98 | +1.69 | −2.97 | −0.99 | 0.34 |
| **4.0** | 109 | 26.6% | 58.7% | 14.7% | 37.6% | 1.81 | **+6.22** | **+1.57** | **+0.45** | 0.27 |
| 5.0 | 109 | 32.1% | 48.6% | 19.3% | 45.9% | 1.15 | +4.09 | −0.57 | −0.15 | 0.30 |

**Recorded as noise, for four independent reasons:**

1. It is **one rung of five in one cell of 109 trades**, and the ladder was declared description,
   not a test. It has **no null** — and §2 established that this geometry's null makes positive
   gross, so a null at G=4.0 would plausibly be positive too.
2. Its neighbours are −2.97 and −0.57. It is a **spike, not a plateau.**
3. **Cells A and B move the OPPOSITE way** with wider stops: A net −6.01 → −7.48, B −4.97 → −6.65
   across the same ladder. Cell C's direction contradicts both.
4. Six correlated stop widths on one trade population are one look.

The τ ladder is flat to mildly worse with longer τ in every cell (C: −3.14 / −2.62 / −2.87 / −3.55
at τ = 10/20/40/80), so τ = 20–40 is about right and is not a lever.

## 4. Both lenses, and the opportunity cost between them

One `resolve` feeds both scorers, so entry and exit logic cannot drift apart. Cell C is so sparse
(109 candidates over 147 sessions, 0.3% exposure at 3 slots) that **the slot cap never binds and
the two lenses agree** — 106 trades at 1 slot against 109 at 3 or unlimited. There is no
opportunity cost to measure in cell C. Cell B is the opposite: 12,865 candidates, 3.0% exposure,
and its book Sharpe (−23.75) is far worse than its per-trade number suggests, because the slot cap
forces it to hold the trades it happens to be in rather than the ones it would pick.

**A latent defect was found by self-test 5b and fixed:** `perf` derived its Sharpe denominator from
the window length, and if that implied fewer sessions than the book actually traded the denominator
was silently wrong. It now raises, and the test proves it raises.

## 5. Disposition

**Both of the principal's ideas are improvements to the construction, and neither rescues it.**

1. **The opposite-extreme target is the right target** — it halves cost as a share of the payoff and
   raises the payoff ratio from 1.50 to 2.38. Keep it. There is an interior optimum and its location
   is not stable across cells, so do not tune it.
2. **Drift-following stops help**, by cutting losers earlier and smaller. Keep them. This reverses
   the prediction in this file's own docstring.
3. **Neither closes the gap**, and the null now makes positive gross under this geometry, so the
   bar has risen rather than fallen: a candidate must beat a null that is itself positive.
4. **Still no component line** — net expectancy is negative in every declared cell.

Unchanged: the binding constraint is cost, of which $3.00 of ~$4.66 is commission; the axis is not
closed; the reserved slice is not spent.
