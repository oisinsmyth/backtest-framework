# D674 — the MACD arm resized: one MNQ stays the floor, so the account moves to MFFU Rapid 150k and the book's expectation moves to Sharpe 0.24

*2026-09-29.*
- *The principal, on D503 and D669–D673: "resize it, then amend". Then, choosing among the options below: "MFFU Rapid
  150k".*
- *An ANALYSIS of committed objects (as D505), not a study.* No signal is chosen or sharpened. The rule was written
  into the runner's docstring before any number was computed.
- *Runner `scripts/d674_resize_macd_arm.py` → [`data/d674_resize_macd_arm.json`](../../data/d674_resize_macd_arm.json).*

## 1. Why the size lever is the account

The arm trades **one MNQ, the smallest contract that exists**, so its dollar risk per day cannot fall. At 2025–2026
price levels that risk is a daily σ of **$389**, against $180 in sample (D503, D504).

On the admitted account, MFFU Rapid EOD 50k:
- **the $2,000 trailing drawdown is 5.1 daily σ away;**
- **the 2 % daily-loss line ($1,000) is crossed 1.90 times a year** in 2025–2026, against a bar of 1.0 (P3a). That is
  BOOK_PROP's qualification 3, now failing on the recent data.

**What D669–D673 changed is the expectation.**
- The arm's 0.72 Sharpe is the top of its family. The median neighbour is 0.24 net, and the deflated Sharpe fails.
- No portable mechanism exists (D670, D673).
- The forward read's +0.736 did not clear its own null and was carried by three sessions (D503).

**So the size decision is made at Sharpe 0.24, with 0.72 and 0 beside it.**

## 2. The declared rule and the numbers

**The rule:**
- For every plan in D386's list, at one MNQ and σ $389, compute V with D386's published-rules lifecycle model (8,000
  paths × 600 days). V is the expected dollars paid out less fees, per evaluation.
- Compute P3a on the arm's own daily net at 2 % of each account.
- **Recommend the plan that maximises V at Sharpe 0.24,** among those with P3a (2025–2026) ≤ 1.0 and V > 2 SE.

**The MFFU plans** (the programme's venue, P6):

| plan | fee | funded drawdown (σ away) | P3a 2016–26 / 2025–26 | V at 0.24 (SE) | V at 0.72 | V at 0 | P(pass) / P(paid) at 0.24 | median funded days at 0.24 |
|---|---|---|---|---|---|---|---|---|
| Rapid EOD 25k | $145 | $1,000 EOD (2.6) | 5.12 / 15.23 | +20 (8) | +102 | −5 | 30 % / 9 % | 10 |
| **Rapid EOD 50k (as admitted)** | $209 | $2,000 EOD (5.1) | 0.50 / **1.90** | +104 (14) | +402 | **+20** | 30 % / 11 % | 29 |
| Rapid 50k | $209 | $2,000 intraday (5.1) | 0.50 / 1.90 | +92 (15) | +373 | +7 | 30 % / 10 % | 27 |
| Rapid 100k | $356 | $3,000 intraday (7.7) | 0.00 / 0.00 | +44 (20) | +616 | −116 | 25 % / 9 % | 62 |
| **Rapid 150k** | **$463** | **$4,500 intraday (11.6)** | **0.00 / 0.00** | **+86 (24)** | **+1,231** | −171 | 27 % / 10 % | **127** |

**Only Rapid 100k and Rapid 150k qualify; the rule picks Rapid 150k.**

Across the full list:
- Apex loses at every size, and Take Profit Trader's 100k/150k lose, at every Sharpe.
- **Topstep 50k scores the highest V at 0.24 (+$173)**, and Take Profit Trader 25k/50k are also positive. All fail
  P3a at 1.90–15.23 a year.
- **Their V at a Sharpe of 0 is +$126, +$114 and −$24.** At zero edge, the payoff is the account structure, not the
  strategy.

## 3. What the choice buys, and what it costs

**It removes the vehicle problem D503 named:**
- **P3a goes from 1.90 a year to zero.** The $3,000 daily-loss line has never been reached by the arm.
- **The drawdown goes from 5.1 σ to 11.6 σ away.**
- **The median funded life goes from 29 days to 127 at Sharpe 0.24,** and from 34 to 163 at 0.72.

**It makes V a bet on the edge rather than on variance.**
- On 50k, V is +$20 at a Sharpe of 0: the account's convexity pays even without an edge.
- On 150k, V is −$171 at 0, +$86 at 0.24 and +$1,231 at 0.72. **The larger account pays for the edge and charges for
  its absence.** That is the right exposure for an arm whose edge is in doubt, **if it is traded at all.**

**The costs, stated plainly:**
- **The evaluation fee rises from $209 to $463.**
- **At the re-estimated edge, V is small:** +$86 ± 24 per evaluation, P(paid) 10 %. Nine accounts in ten pay nothing.
- **The funded drawdown trails intraday on the 150k plan** (EOD on the 50k). D386's model steps four times a day, so
  it prices that. **The arm's forward kurtosis of 12.1 (D503) is fatter than the model's Gaussian,** so breach risk is
  understated there and not in P3a, which reads the arm's own days.
- **The 2 % daily-loss line and the drawdown are MFFU's published figures as D386 records them.** They were not
  re-checked against MFFU's current terms here.

## 4. The ruling

**The principal chose MFFU Rapid 150k.**
- **The arm stays one MNQ**, with an unchanged spec.
- **Its account is MFFU Rapid 150k**, replacing the Rapid EOD 50k under which it was admitted.
- **Its expectation is Sharpe 0.24**, D669's neighbourhood median, **not 0.72.**
- `BOOK_PROP.md` carries the amendment, and `COMPONENTS_PROP.md` records it against entry #2.

Nothing else changes: no parameter, no filter, no conditioner.
