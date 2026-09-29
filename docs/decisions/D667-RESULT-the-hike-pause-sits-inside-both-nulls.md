# D667 RESULT — pausing the MACD arm after NQ margin increases lifts its net Sharpe by 0.04, inside both nulls: not supported, and the arm is no more volatile after a hike than elsewhere

*Pre-registration: [D667](D667-PRE-REG-margin-hike-pause-on-the-macd-arm.md) (`161f553`), committed before the runner
existed (R8). Runner `scripts/run_d667_hike_pause_overlay.py`, one run of `--run`, repeated once only to add the drawdown-sign marker
the repository's gate requires (every number identical); numbers
[`data/d667_hike_pause_overlay.json`](../../data/d667_hike_pause_overlay.json). **A disclosed measurement on a closed
line, reopened by the principal for this overlay; it cannot admit anything. The window is 2016-01-04 → 2023-12-29;
the arm's 2024+ (spent by D503) was not read.***

## The answer in one line

**B1 and B4 pass, B2 and B3 fail: not supported.** Pausing the arm for ten sessions after each of 11 NQ margin
increases removes 106 sessions that lost $487 in total, which lifts net Sharpe from 0.724 to 0.763 (Δ **+0.040**). That
sits at the **73rd percentile of the exact rotation null** (p95 +0.137) and **below the volatility-matched null's p95**
(+0.060). Breaches are unchanged. The margin increase adds nothing a random pause or a volatility pause would not.

## 1. The arm and the events

The arm reproduced D508 exactly (1,876 sessions, $15,423 net; asserted). **11 events after merging** (12 increases):
2016-01-27, 2016-11-03, 2017-02-10, 2017-09-14, 2020-08-07, 2020-11-13, 2021-08-18, 2022-03-02, 2022-11-16, 2023-03-17
and 2023-12-20. The last event's pause runs past the window's end and is cut there, so the pause covers **106
sessions** (5.7 %). 1,263 sessions are covered by the margin history (none from 2017-11 to 2020-06).

## 2. Base against paused (one MNQ, $3.50 a round trip, all 1,876 sessions)

| | base | paused |
|---|---|---|
| net Sharpe / Sortino | 0.724 / 1.069 | **0.763 / 1.124** |
| gross Sharpe / Sortino | 1.039 / 1.557 | 1.067 / 1.594 |
| net total | $15,423 | $15,910 |
| maximum drawdown | $7,814 | $7,312 |
| worst day | −$1,315 | −$1,315 |
| round trips | 1,908 | 1,799 |
| P3a breaches a year | 0.27 (2) | 0.27 (2) |
| P3b life cost | 0.222 | 0.222 |
| skew of daily net | −0.05 | −0.13 |
| hit rate (traded sessions) | 50.6 % | 50.7 % |

**Component line:** the paused arm correlates **+0.978** with the base arm, the ledger's only component. It is the same
construction, not a new one.

## 3. The nulls

| | Δ net Sharpe | where Δ sits | bar |
|---|---|---|---|
| the hike pause | **+0.040** | | B1 pass |
| N1, exact rotation (1,262 offsets) | p05 −0.164, p50 −0.018, p95 +0.137 | 72.7th percentile | B2 FAIL |
| N2, volatility-matched (2,000 draws) | p05 −0.169, p50 −0.053, p95 +0.060 (SE 0.003) | below p95 by 6 SE | B3 FAIL, resolved |
| P3a not worse | 0.27 → 0.27 | | B4 pass |

N1's p95 (+0.137) is the smallest improvement this sample could have told from chance; the pause reached less than a
third of it. **N2's median is negative (−0.053): pausing the arm in equally volatile windows chosen by NQ's own state
costs it money**, because the arm earns more than usual there (§4).

## 4. Diagnostics

| sessions | count | mean net | SD | hit rate |
|---|---|---|---|---|
| paused (after a hike) | 106 | **−$4.59** | $158 | 50.0 % |
| elsewhere | 1,770 | +$8.99 | $182 | 50.7 % |
| N2's matched volatile windows (pooled) | 209,048 | **+$15.06** | $186 | |

- **The arm is not more volatile after a hike:** its SD on paused sessions is **0.87 ×** its SD elsewhere, although
  D657 found NQ's own variance up after increases. The arm trades one micro inside the day session and is flat
  overnight, so the market's variance does not pass through to it one for one.
- **Its mean on paused sessions is lower than elsewhere, but not distinguishably** (Welch t −0.85, 106 sessions).
- **Year by year Δ changes sign:** 2016 −0.29, 2017 +0.09, 2020 −0.19, 2021 +0.18, 2022 +0.11, 2023 +0.16. The largest
  paused session is 2022-11-30, **+$968**: a winner the pause would have skipped.
- Two events had small matched pools (4 and 11 candidate starts); the rest 40–137.

**On the principal's overfitting concern, stated as far as it goes and no further.** In windows CME dates, the arm
averages −$4.59 a session. In equally volatile windows selected from NQ's own state, it averages +$15.06. That gap is in
the direction an arm tuned to its own market's regimes would show. But 106 sessions with a t of −0.85 cannot carry it,
and this record does not claim it.

## 5. The predictions

| | prediction | outcome |
|---|---|---|
| 1 | \|Δ\| < 0.10 | held: +0.040 |
| 2 | B2 fails | held: 72.7th percentile |
| 3 | B3 fails | held: below N2's p95 |
| 4 | the arm's SD on paused sessions ≥ 1.2 × elsewhere | **FAILED**: 0.87 × |
| 5 | mean on paused sessions not distinguishable | held: t −0.85 |

## 6. What this decides

**The margin-hike pause is not supported on the admitted arm,** and D657's M3 route to the prop book ends here. The hike
filter stays what the principal recorded in D657: an input for a new component's pre-registration, where an unread
slice could confirm it. Recommended: close (principal, R15).

## 7. CLOSED by the principal, 2026-09-29

"Close after then investigate the MACD." **The margin-hike pause on the admitted arm is closed under R15,** and with it
D657's route to the prop book. The conditioner line on the arm returns to its 2026-09-13 closure. The hike filter
remains the strategy input D657 recorded.
