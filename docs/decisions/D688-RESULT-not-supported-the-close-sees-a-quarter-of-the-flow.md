# D688 RESULT — NOT SUPPORTED: the dealer hedge flow predicts the close with the right sign but at about a quarter of the square-root law's size (β 0.12, t 1.2, 91st percentile of its rotation null); the long-gamma half is absent, and no book clears net

*Renumbered from D681 to D688 on 2026-09-29 before this branch (`wt/after-d674`) merged main, which holds a different D681. Commit messages and the recorded outputs in `data/` keep the old number.*

*2026-09-29. One run of `scripts/stage0_d688_gamma_close.py` (`7be544a3`), 118 s, under
[D688's pre-registration](D688-PRE-REG-the-dealer-gamma-close-on-es-spx-plus-es-books.md) (`de4a4f7e`). Output
`data/d688_gamma_close.json` (statistics only; no per-date GEX). Window: 1,989 sessions, 2016-01-05 → 2023-12-29.
No price, option, GEX or AUM row dated on or after 2024-01-01 was read. SqueezeMetrics GEX used under the permission of
2026-09-28 (credit: SqueezeMetrics).*

## The answer in one line

**Gate 1 fails and Gate 2 fails, so the verdict is NOT SUPPORTED.** It is the outcome I predicted first (§8, prediction
1).
- **The slope has the mechanism's sign:** β_G = +0.12 per bp of predicted push (NW t 1.23).
- **It does not beat its own null:** 91.3rd percentile of the 1,970-offset rotation null (p50 −0.004, p95 +0.143,
  enumerated, so the p95 has SE 0).
- **Its size rules out the pre-registered range:** the square-root table put Y at 0.5–1. The estimate is 0.12 with SE
  0.10, so Y = 0.5 sits 3.8 SE above it, and the upper 95% bound is 0.32.

The hedge flow the option books imply either does not reach the last half-hour, or reaches it at about a quarter of the
size the impact law assigns it.

## 1. The mechanics held

- **D581 reproduced exactly from its own code:** T1 c = −0.022772686672947903 (n 1,990), bit for bit.
- **The ES book was rebuilt** over 10 processes in 99 s (7.2× on 10, 72%). A serial recomputation of eight sampled
  sessions matched bit for bit.
- **Every audit passed its clean case and raised on its break:**
  - lag, a second path on 7 sessions; it raised on the same-day GEX row;
  - sign in money;
  - right quantity, twice;
  - the window guard;
  - rotation identity;
  - the prior-only π, which raised with today's return;
  - the OI keying on 12,594,319 option rows, which raised when shifted a session;
  - the declared outputs.
- **P(15:30) is identical to D581's** on all 1,989 common sessions.
- **Dropped:** 4 sessions for a missing input (3 with no ES-options book; 1 with no prior AUM, on 2016-01-04).
- **Construction details stated before the run** (runner commit):
  - Time to expiry is counted on every ES trading day. D581's ≥ 380-bar calendar drops half days and halt days, and
    timed an expiry on one as same-day.
  - 11,209 live option-rows over the window still expire on a date that is not an ES trading day (e.g. 2023-06-19).
    They are timed to the next session.
  - D581's ≥ 380-bar session rule removes the four March-2020 halt days (03-09, 03-12, 03-16, 03-18).

**The premise, before any outcome:**

| | 2016–23 |
|---|---|
| short-gamma share: SUM / SPX / ES book | 30.3% / 12.5% / 43.1% |
| corr(SPX GEX, ES book), sign agreement | +0.55, 69% |
| \|Z\| p50 / p90 / p99 | 8.2 / 24.6 / 59.1 bp |
| sd of R2 (15:30 → 16:00) | 31.7 bp |

**The ES book is short gamma far more often than SPX:** 43% of days, 78% in 2022. Adding it takes the sum's short share
from 12.5% to 30%. Under the white paper's convention (dealers long calls, short puts), ES options look more
put-heavy than SPX. Either ES dealers really are shorter, or the convention fits the futures options less well; this
record cannot separate the two.

## 2. Gate 1: the mechanism (gross)

**G1:** `R2 = a + β_G·Z_SUM + β_r·r + β_L·Z_L + β_σ·σ_d`, NW lag 5, n 1,989.

| term | β | NW t |
|---|---:|---:|
| **Z_SUM (gamma push, bp per bp)** | **+0.122** | **+1.23** |
| r (the day's move, %) | −1.96 | −0.96 |
| Z_L (LETF flow push) | +0.70 | +1.78 |
| σ_d | +0.013 | +0.47 |

Rotation null of β_G: p05 −0.135, p50 −0.004, **p95 +0.143**; observed at the **91.3rd percentile. FAIL** (t < 2,
under p95).

**G2, the placebo:** β_G at 11:00 → 11:30 is −0.057 (t −0.94). The difference, close minus 11:00, is +0.180, against a
null p50 of +0.006 and **p95 of +0.206**: the **92.5th percentile. FAIL.**

## 3. Gate 2: tradeability (net, filtered by expected profit)

- **235 MES trades** (30 a year), net +$1.91 a trade, **NW t +0.30. FAIL.** Per session, t is +0.31.
- **Every trade is a short-gamma day.** The long-gamma pass-through never projected 2 × cost, and by the last session
  the regime π was −0.058.
- **The rotation null of the book's net mean:** p50 −$5.23, p95 +$11.69, observed at the 74.8th percentile.
- **The filter trades far more than its rotations** (235 against a p50 of 23; 99.6th percentile), because only the true
  alignment gave the short-gamma π a positive sign. The profit on those trades is a single day's (§4).

## 4. The component line and the four groups (1 MES at $4.42 a round trip, unless noted; daily √252)

| book | trades/yr | net Sharpe (Sortino) | gross Sharpe (Sortino) | mean gross vs 2c | breakeven RT | hit (net) | ρ with the arm |
|---|---:|---|---|---|---:|---:|---:|
| **Gate 2, filtered, MES** | 30 | **+0.10 (+0.15)** | +0.33 (+0.53) | $6.33 vs $8.84 | $6.33 | 48.9% | +0.156 |
| unfiltered sign(Z), MES | 250 | **−1.16 (−1.65)** | +0.20 (+0.31) | $0.66 vs $8.84 | $0.66 | 42.4% | +0.058 |
| Gate 2, filtered, full ES ($19.24) | 50 | +0.14 (+0.21) | +0.30 (+0.46) | $36.56 vs $38.49 | $36.56 | 49.0% | +0.133 |
| unfiltered sign(Z), full ES | 250 | −0.39 (−0.57) | +0.20 (+0.31) | $6.59 vs $38.49 | $6.59 | 46.9% | +0.058 |

**Performance.**
- **Gate 2, MES:** net $449 over eight years; exposure 11.8% of sessions (30 minutes each); annual net vol $562;
  max drawdown $1,886.
- **Unfiltered, MES:** net −$7,425, lost money in every year, and gross is barely positive ($0.66 a trade, t 0.60).
- **The gross unfiltered signal** sits at the 91.2nd percentile of its rotation null (+0.51 bp a session; p50 −0.40,
  p95 +0.69).
- **Both lenses fail:** this is signal failure, not only cost failure.

**Trade distribution (Gate 2, MES, net per trade).**
- n 235; mean +$1.91 but **median −$1.92**; win rate 48.9%; payoff 1.10; skew +0.64; kurtosis 9.0.
- Trimming 1%: ex-top −$2.09; ex-bottom +$5.11; both tails +$1.10.
- **A mean above the median, and negative without the top 1%:** the right tail carries it.

**What the winners depend on.**
- **One trade is 134% of the net:** 2020-03-13, long, +$601. The top 5 are 375% of the net, and half of the net is
  reached in one trade.
- **By side:** longs +$785, shorts −$336.
- **By era:** 2016–21 −$35 on 109 trades; 2022–23 +$485 on 126.
- **By year:** 2020 +$655 against 2021 −$857; 5 of 8 years are profitable (2016–17 had no trades, which were still in
  the burn-in).
- **The largest adverse trades** are 2020-02-28 (−$393) and 2022-01-24 (−$348).

**Nulls:** see §2 and §3. No statistic of either book is above its rotation p95.

**The component is not entered.** Its net is +0.10 on MES, with a tail-carried mean and ρ +0.16 with the arm (the
highest of the four). It is below every ledger admission line.

## 5. Reported beside (not gated)

**The measures, on the same regression and the same rotation:**

| measure | β_G | NW t | rotation percentile |
|---|---:|---:|---:|
| SUM, square-root (primary) | +0.122 | +1.23 | 0.91 |
| SPX GEX only | +0.290 | +1.33 | 0.95 |
| ES book only, prior close | +0.160 | +1.46 | 0.94 |
| D581's ES book at 15:30 | +0.135 | +1.03 | 0.92 |
| SUM, raw −G·r ($bn) | +0.309 | +1.50 | 0.94 |
| SUM, outcome 15:50 → 16:00 (r to 15:50) | +0.104 | +1.64 | 0.93 |

**Every variant has the mechanism's sign, and none reaches t 2 or the 95th percentile.** They cluster at t 1.0–1.6 and
the 91st–95th percentiles. The SPX-only form sits at 0.95 exactly without clearing it. There is no hidden winning
variant; this is one weak effect seen through six lenses, and none of them is a pre-registered gate.

**The clock profile** (β_G, t, with r and Z built to each window's start):

| window | 09:30 | 10:00 | 10:30 | 11:00 | 11:30 | 12:00 | 12:30 | 13:00 | 13:30 | 14:00 | 14:30 | 15:00 | 15:30 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| β_G | +0.04 | −0.05 | −0.06 | −0.06 | −0.02 | +0.03 | −0.04 | +0.06 | +0.03 | −0.02 | +0.10 | +0.01 | +0.12 |
| t | +0.3 | −0.6 | −0.8 | −0.9 | −0.4 | +0.7 | −0.6 | +1.5 | +0.5 | −0.4 | +1.9 | +0.3 | +1.2 |

The morning is flat to negative; the two largest slopes are 14:30 and 15:30. **That is the shape the mechanism
predicts, but nowhere reaches t 2.** With 13 windows, a single t of 1.9 is what chance delivers.

**The regimes** (within-regime regressions, no null):

| | n | β_G | NW t | SE |
|---|---:|---:|---:|---:|
| short gamma (G_SUM < 0) | 603 | +0.548 | +1.26 | 0.43 |
| long gamma (G_SUM ≥ 0) | 1,386 | **−0.008** | **−0.04** | 0.19 |

**The pooled slope comes from the short-gamma days alone,** where it is noisy but the table's size (≈ 0.5). On the
long-gamma days, the reversal half, it is zero: Y = 0.5 is 2.7 SE away. **This decides the confirmation question
(§7).**

**By era and year.**
- **2016–21:** β +0.201, t +1.50, 93rd percentile.
- **2022–23 (the 0DTE era):** β −0.078, t −0.76, 20th percentile. The era of the largest same-day gamma shows nothing.
- **By year:** 2016 +0.12, 2017 −0.15, 2018 +0.23, 2019 +0.22 (t 2.3), 2020 +0.27, 2021 −0.14, 2022 −0.12, 2023 +0.10.
  Five of eight are positive.

## 6. Predictions (§8 of the pre-registration)

| # | prediction | outcome |
|---|---|---|
| 1 | β_G > 0 but Gate 1 fails | **Correct** (+0.12, t 1.23, 91st percentile) |
| 2 | SPX-only and sum have the same sign; ES-only weaker | **Half.** Same sign, but ES-only (t 1.46) is not weaker than the sum (1.23) |
| 3 | short-gamma β > long-gamma β | **Correct** (+0.55 against −0.01) |
| 4 | the 11:00 placebo β is at least half the close's | **Wrong.** The placebo is negative (−0.06); the effect, such as it is, is not spread through the day |
| 5 | β_r > 0 | **Wrong** (−1.96, t −0.96). With r from the prior settlement there is no continuation; D581's +0.10 was on the 14:30 → 15:30 move, a different quantity |
| 6 | 2022–23 β exceeds 2016–21 | **Wrong** (−0.08 against +0.20) |
| 7 | if Gate 1 passes, Gate 2 fails | Not applicable |

**Score: two right, one half, three wrong, one not applicable.**

## 7. What this decides, and the confirmation question

- **As a test of the pre-registered construction, the answer is no.** It needed t ≥ 2 and the 95th percentile, at a
  power the pre-registration put at t ≈ 4 for the table's size and ≈ 2 at half. The observed t 1.23 matches roughly a
  quarter of the size. **Y ≥ 0.5 is rejected at 3.8 SE.**
- **What survives is narrow:** a short-gamma continuation with β ≈ 0.5 at t 1.3 on 603 days.
- **No confirmation slice can test that.** 2024-01 → 2025-02 has one short-gamma day on SPX GEX. Even counting the ES
  book, it is mostly long gamma, the half this record found at zero.
- **So the pre-registered confirmation (the frozen rule on 2024-01 → 2025-02 plus the vault) is not triggered,** and it
  should not be run: its expected t on the half that exists in-sample is ≈ 0.
- **The ES book's 43% short share** is an unexplained premise fact worth one line in any future gamma work. A
  convention that fits SPX may not fit futures options, where dealers can hold either side.
- **Relation to earlier records.**
  - It is consistent with D581 (the ES book does not sort the close) and D662/D663 (the open).
  - It is consistent with **D665: SPX GEX carries information about the SIZE of moves, and this record finds its
    direction information at most a quarter of what the hedge-flow arithmetic implies.**
  - That matches the memory "dealer gamma predicts size, not carry", now tested on the hedge-flow construction built
    to extract direction.

**Status: NOT SUPPORTED, awaiting the principal's ruling (R15).** No 2024+ slice has been read or spent.

## CLOSED by the principal, 2026-09-29

"Close them, renumber and merge, then go after short-gamma days with volatility is controlled."
- **The line is closed under R15:** the gamma push at the close, and at any fixed clock.
- **No 2024+ slice was read or spent.**
- **Diagnosed in D683 and sized in D684.** The short-gamma continuation that D684 found post hoc is pursued as its own
  line, which does not reopen this construction.
