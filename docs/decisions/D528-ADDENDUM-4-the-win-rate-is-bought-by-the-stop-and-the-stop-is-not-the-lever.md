# D528 ADDENDUM 4 — the win rate is bought by the stop, and the stop is not the lever

Date: 2026-09-14. Runner: `working/d528_why_win_rate.py` (`--self-test`, `--run`).

**Nothing admitted (R15).** Micro universe (8 roots), in sample only; the reserved slice
(2026-04-11 → 2026-09-09) remains UNREAD. This answers a question the principal asked about
ADDENDUM 3's book — why the win rate is 36–42% and whether the stop is responsible — and adds no
new cells.

---

## 1. The win rate is chosen, not observed

The stop sits at `f = 0.5` of the target distance. For a driftless walk,

```
P(reach target before stop) = stop / (target + stop) = f / (1 + f) = 1/3
```

so **a ~33% win rate is what a 2:1 reward-to-risk geometry pays on a fair market.** Observed
P(target) is 36.7% / 37.1% / 38.5% across the three cells — slightly *better* than the geometric
value, not worse. A 33% win rate is not a defect; at a true 2:1 it breaks even.

**The closed form is a guide here, not a law**, and the self-test measures where it fails and why.
On a synthetic Gaussian walk, with the two deviations pulling opposite ways:

| f | P(target) | f/(1+f) | diff | timeouts | overshoot |
|---:|---:|---:|---:|---:|---:|
| 0.25 | 0.2598 | 0.2000 | **+0.060** | 4.9% | **2.019** |
| 0.50 | 0.3393 | 0.3333 | +0.006 | 9.5% | 1.492 |
| 1.00 | 0.3964 | 0.5000 | −0.104 | 21.1% | 1.257 |
| 2.00 | 0.4349 | 0.6667 | **−0.232** | 38.4% | 1.143 |

At a **tight** stop, overshoot inflates the effective stop distance, so the target becomes
relatively more reachable and P(target) exceeds `f/(1+f)`. At a **wide** stop, the τ=20 timeout
truncates before the far target is reached and P(target) falls below it. At f=0.5 the two roughly
cancel. The asserted invariants are therefore structural, not the closed form: **P(target) and the
timeout share rise monotonically with f, the overshoot ratio falls monotonically with f**, and at
the specified f=0.5 the observed value sits on 1/3.

## 2. So the question is the payoff, and cost takes more of it than overshoot does

Cell C (`traverse`, micro, n=109), stage by stage:

| stage | mean win | mean loss | payoff |
|---|---:|---:|---:|
| nominal geometry, target $33.60 / stop $16.80 | +$33.60 | −$16.80 | **2.00** |
| after cost, charged on **both** sides | +$28.94 | −$21.46 | **1.35** |
| after overshoot (1.510× the designed stop) | +$30.70 | −$26.59 | **1.15** |

**Cost removes 0.65 of the payoff ratio; overshoot removes a further 0.20.** The 2:1 bargain was
never 2:1 — it was 1.35:1 the moment the $4.66 round trip was charged, because cost is subtracted
from the winner *and* added to the loser: `(|y| − c) / (f·|y| + c)`.

All three cells, at the specified f=0.5:

| cell | n | TARGET / STOP / TIMEOUT | win | designed payoff | realised payoff | overshoot | effective stop |
|---|---:|---|---:|---:|---:|---:|---:|
| A as specified (`cross2`) | 1,544 | 36.7% / 58.7% / 4.6% | 38.7% | 1.28 | 0.83 | 1.648 | 0.82 of target |
| B no classifier | 12,865 | 37.1% / 58.7% / 4.2% | 35.9% | 1.11 | 0.88 | 1.727 | 0.86 of target |
| C `traverse` | 109 | 38.5% / 52.3% / 9.2% | 42.2% | 1.35 | **1.15** | 1.510 | 0.75 of target |

**A stop placed at 0.50 of the target actually risks 0.75–0.86 of it.** A stop is not a limit
order: it becomes a market order and can only fill at or beyond its price.

## 3. And no stop width fixes it — the ladder is flat in net

Cell A across an 8× range of stop widths:

| f | win% | payoff | designed payoff | overshoot | GROSS $/tr | NET $/tr |
|---:|---:|---:|---:|---:|---:|---:|
| 0.25 | 30.6% | 1.09 | 2.07 | **2.269** | −2.74 | −7.48 |
| 0.50 | 38.7% | 0.83 | 1.28 | 1.648 | −3.43 | −8.18 |
| 0.75 | 44.5% | 0.70 | 0.93 | 1.431 | −3.28 | −8.03 |
| 1.00 | 49.0% | 0.61 | 0.73 | 1.334 | −3.15 | −7.90 |
| 1.50 | 53.2% | 0.51 | 0.51 | 1.237 | −3.78 | −8.53 |
| 2.00 | 55.3% | 0.47 | 0.39 | 1.196 | −3.90 | −8.64 |

**Net moves about $1 across the whole ladder, against a loss of $7–8.** Win rate runs 30.6% → 55.3%
while payoff runs 1.09 → 0.47, and the two cancel — which is what they must do on a near-martingale.
Cell B is the same shape (net −6.19 to −7.61 across the ladder). **The stop is a dial that changes
the shape of the outcome distribution, not its mean.**

### 3.1 Two consequences worth keeping

1. **Overshoot scales inversely with stop width** (2.27× at f=0.25 → 1.20× at f=2.0), so
   tightening the stop to buy a better payoff ratio does not work: the tighter it is, the larger
   the fraction that gaps through it. This is the mechanism behind ADDENDUM 2 §4.1 — it is why the
   f=0.25 rung looked like a pass under an idealised fill and reversed under a realised one.
2. **The principal's f=0.5 is already near-optimal.** Cell C's gross peaks at +$2.25 at f=0.5
   (+$2.18 at 0.25, +$1.42 at 0.75, +$0.79 at 1.0, negative beyond). The stop was not mis-set.

## 4. One line that keeps not going away

`traverse` beats its own sign shuffle on P(target) at **all six** stop widths:

| f | 0.25 | 0.50 | 0.75 | 1.00 | 1.50 | 2.00 |
|---|---:|---:|---:|---:|---:|---:|
| C real | 0.3119 | 0.3853 | 0.4404 | 0.4862 | 0.4954 | 0.5046 |
| C null | 0.2806 | 0.3298 | 0.3872 | 0.3992 | 0.4483 | 0.4400 |
| **gap** | **+0.031** | **+0.056** | **+0.053** | **+0.087** | **+0.047** | **+0.065** |

against cells A and B, which sit on their nulls (+0.005 to +0.012 throughout). That is a sixth
independent place the same cell reads positive. **It remains n = 109 and UNRESOLVED** — six
correlated stop widths on one trade population are one look, not six — but it is consistent.

## 5. Disposition

**The answer to the question: the low win rate is the geometry, not a defect, and the stop is not
the lever.** The binding constraint is cost, which takes more of the payoff ratio than overshoot
does, and which no stop width can reach.

This adds nothing to the candidate set and changes no disposition. It does sharpen ADDENDUM 3 §6.5:
the route needs **cost** halved, and the stop is not a place to look for it.
