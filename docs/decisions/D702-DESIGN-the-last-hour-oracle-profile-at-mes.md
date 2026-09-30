# D702 DESIGN — the oracle profile of the reopened last-hour continuation at MES: is the edge big-move-shaped, and where do the winners sit against the size forecasts?

*2026-09-30. Committed before its runner. Hindsight and descriptive only: nothing is fitted, filtered or traded. The
result follows as a separate record.*
- *The principal: "Reopen it, that is the whole point of this study"
  ([D618](D618-STAGE-0-RESULT-the-band-around-the-price-was-the-signal.md), reopened 2026-09-30).*
- *It follows the principal's rules for filters ([D690](D690-DIAG-accuracy-needed-is-small-and-the-regime-gate-is-best.md),
  [D692](D692-DIAG-the-mes-oracle-profile.md)):*
  - *score on MES at $4.42 a round trip;*
  - *show the oracle first;*
  - *design the candidate filters together.*
- *Numbered D702: D701 is the highest on every branch and in every commit subject.*

## 0. The question this answers first

**The crux.** On D689's hourly continuation, a perfect size-only oracle was worth about nothing, because that trade
has no direction per unit of size (D690 §A). D618 says the last hour is different: hit 0.4929 with a median trade of
0, so the edge is in the size of the moves. **If so, the size-only oracle should be worth something here, and a real
size forecast has something to capture. If not, no size filter can help, and the study stops at the oracle.**

## 1. The candidates (D618 §3c, unchanged)

- **The trade:** at 15:30 on every session, sign(F5), where F5 = ln(P15:30 / P14:30); held 15:30 → 16:00.
- **Prices:** D618's endpoint convention (the price at hh:mm is the close of the bar starting one minute earlier).
- **The session filter:** D618's own. ES sessions with at least 380 bars, from D618's `load_es`.
- **The window:** 2016-01-04 → 2023-12-29, about 1,960 sessions.
- **Pricing at 1 MES:** gross = sign(F5) × (P16:00 − P15:30) × $5; net = gross − $4.42.
- **The known answer:** D618's +0.6795 points a trade and hit 0.4929, reproduced before anything else.

**The oracle labels:** WIN = net > 0; BAR = gross ≥ $8.84 (2 × the round trip, the expected-profit template's bar).

## 2. The oracle lines (the ceiling and the crux)

| line | rule |
|---|---|
| take everything | every session |
| **the oracle** | realised net > 0 |
| the oracle at the bar | gross ≥ $8.84 |
| **the size-only oracle** | the top 20 % / 40 % of sessions by the realised \|P16:00 − P15:30\|, with the direction left to the rule |
| a size-only oracle on the pre-entry clock | the top 20 % / 40 % by the realised \|F5\| (known at 15:30), to show how much of the size effect is already knowable |

**Each line reports:**
- trades, and trades a year;
- mean gross, mean net, hit;
- the per-trade and daily net Sharpe with Sortino, annualised by the line's own trade count;
- max drawdown in $;
- share of years positive.

## 3. The profile (every bucket; hindsight edges over all sessions)

**Every bucket reports** (D692's columns):
- n, share, trades a year;
- the WIN and BAR rates, each with its lift;
- mean gross with its HAC t, and mean net;
- its share of all the oracle's net P&L;
- the mean net of its winners and of its losers.

| # | input (all known at 15:30) | buckets |
|---|---|---|
| 1 | \|F5\| / σ_h: the last hour against a normal hour (σ_h from D618's trailing σ) | terciles |
| 2 | today's realised volatility 09:30 → 15:30 (5-minute sum of squares) | terciles; trailing σ30 terciles |
| 3 | **D691's day-size forecast M1** (ln(range/ATR20), known before the open) | quintiles |
| 4 | **D691's ivrv = ln(IV/RV20)**, and ln IV | terciles |
| 5 | **dealer gamma** (D688's panel): G_SUM sign and quintiles; SPX GEX sign; ES book sign | as listed |
| 6 | side | long / short |
| 7 | alignment | F5 with or against the day's move 09:30 → 14:30 |
| 8 | event days | FOMC (14:00 statement), CPI and NFP, monthly opex, the last session of the month and of the quarter |
| 9 | calendar | day of week; year; before and after 2022-05-16 |
| 10 | two-way tables | M1 tercile × side; ivrv tercile × \|F5\| tercile; G_SUM sign × \|F5\| tercile |

**The bucket count is reported,** so no best bucket is read without its multiplicity.

## 4. The accuracy curve (D690's library, `backtest_framework.validation.filter_oracle`)

- **The partial-oracle curve:** forecasts of the realised gross with normal-score correlation ρ (0, 0.02, 0.05, 0.10,
  0.20), keeping the top 20 % / 40 %, over 200 draws. It shows **what Spearman a filter needs to break even at MES**
  and to reach a net Sharpe of 0.5.
- **Where each single pre-entry input from §3 sits on that curve:**
  - its Spearman with the realised gross (its accuracy for P&L);
  - its Spearman with the realised |P16:00 − P15:30| (its accuracy for size).

  Nothing is fitted. These are raw rank correlations, and they are the formation material for the filters.

## 5. Guards

- **The seal:**
  - D618's loader refuses any session ≥ 2024-01-01. **2024-01-01 → 2025-02-28 is this line's reserved
    confirmation slice**, and no file in it is opened.
  - D691's IV table and forecasts are read only for sessions < 2024-01-01.
  - GEX is read through D688's panel, SqueezeMetrics, credited. No per-date series is written.
- **Known answers:**
  - D618's +0.6795 points and hit 0.4929 on its session count;
  - D688's β_G, reproduced as D692 does;
  - D691's d̄, reproduced from the same IV table on the overlap.
- **Lag:** every §3 input is known at 15:30 or before the open. An audit recomputes today's realised volatility from
  bars that start before 15:30, and a canary that includes the 15:30 bar must raise.
- **Output:** `data/diag_d702_last_hour_oracle_mes.json`, statistics only.

## 6. What happens next

1. The RESULT shows the oracle lines, the crux, the profile and the curve.
2. **Then the principal and I design the candidate filters from it** (formation questions, the principal's choices).
3. A pre-registration follows, stating its expected holdout t on the reserved slice (§3e's power argument) before
   that slice is spent.

**Declared reading of the crux:**

| size-only oracle, top 20 % | reading |
|---|---|
| **net ≤ $0 at MES** | "a size forecast cannot help this trade either": the line stops at the oracle |
| **net > $0** | the study proceeds to filter design |
