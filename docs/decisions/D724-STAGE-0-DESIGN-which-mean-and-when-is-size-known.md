# D724 STAGE 0 DESIGN — which mean does NQ respect intraday, how early and how immediately is the day's size known, and does the size change the mean?

*2026-10-01. The principal:*
> "the question for a mean reversion is 'Where will we mean revert to' or 'Which mean will the price respect' and
> the size based question is how far in advance do you know about the size of the move and how immediate is the
> prediction? Does it affect the mean?"

- **Why this is next:** after D720/D721, the principal chose quiet-day mean reversion ("Start with one").
- **What it is:** a Stage 0 premise measurement, the map before any rule.
- **What it does not do:** choose a rule, admit anything, or spend any slice.
- **The order (R8):** this record is committed before the runner exists, and the runner before its one run.

## 0. Scope and seal

- **NQ, the day session (09:30–16:00 ET), 2016-01-04 → 2023-12-29.** Sources: `fut_NQ_rth_1m` (one-minute OHLCV),
  and `fut_opening_globex_1m` for the overnight bars.
- **The seal:** nothing dated 2024-01-01 or later is read. NQ's 2024+ last hour is D716's joint-vault look.
- **Price at t:** the close of the one-minute bar starting at t−1 (D462). The decision grid is every 5 minutes, 10:00
  → 15:30.
- **The scale:** σ_d is the mean of the prior 20 sessions' day ranges (high − low), in points. Every deviation and
  move below is in σ_d units, so years and price levels are comparable.

## 1. Q1 — which mean does the price respect?

**The candidate means, each known at t, with nothing later used:**

| | anchor |
|---|---|
| A1 | the session VWAP to t: typical price (H+L+C)/3 times volume, over the one-minute bars 09:30 → t |
| A2 | the 09:30 open |
| A3 | the prior session's 15:59 close |
| A4 | the overnight midpoint: (high + low)/2 of the Globex bars 18:00 → 09:29 |
| A5 | the running day midpoint: (high + low)/2 of 09:30 → t |
| A6 | the opening-range midpoint: (high + low)/2 of 09:30 → 09:59 |
| A7 | the prior session's full VWAP |
| A0 (the mechanical baseline) | the price 30 minutes earlier, P(t−30). Any lagged price shows some short-run reversion from noise alone, so a mean earns "respected" only by beating A0 |

**The deviation:** D_A(t) = (P_t − A_t)/σ_d.

**Two statistics per anchor and horizon h ∈ {30 min, 60 min, to the 15:59 close}:**
- **κ_A,h, the fraction of the deviation closed:** minus the slope of the forward move (P_{t+h} − P_t)/σ_d on
  D_A(t), pooled over the grid and the days, with no intercept. The t is clustered by day.
  - Reported for all deviations and for |D_A| ≥ 0.25.
  - Also split by time of day: 10:00–11:55, 12:00–13:55, 14:00–15:30.
- **M_A,h, the touch margin:**
  - the share of (day, t) with |D_A| ≥ 0.25 on which price reaches A within h;
  - minus the share on which it reaches the MIRROR level P_t + (P_t − A_t), the same distance on the other side.
  - This controls for distance and volatility exactly: a mean the price respects is reached more often than an
    equidistant level it has no reason to seek. The t is clustered by day.

**The null for κ:** the enumerated rotation of the day index of the deviation matrix against the forward-move matrix
(offsets 20 … n−20; the SE of the p95 is 0). It breaks the day's link between where the price stands and where it
goes.

## 2. Q2 — how early, and how immediately, is the size known?

**Predictors, by when they are known:**

| | predictor | known at |
|---|---|---|
| F_close | D691's M1 (D671's features + ln IV/RV20) with the two open-time features removed (the overnight range and the \|gap\|), walk-forward | the prior close |
| F_open | D691's M1 in full, as D720 used it, walk-forward | 09:30 |
| F_now(t) | the log realised variance of the 5-minute returns over the 30 minutes before t | t |
| F_rem(t) | F_open's predicted day range less the range already made by t, in σ_d units | t |

**Targets:** the day's range (D691's y), and |P_{t+h} − P_t|/σ_d for t ∈ {10:00, 11:00, 12:00, 13:00, 14:00, 15:00}
and h ∈ {30, 60, to the close}.

**Statistics, per predictor and (t, h):**
- the Spearman correlation with the target;
- F_open's partial Spearman given F_now, which is the value of the morning's knowledge once the immediate state is
  known;
- F_close against F_open on the day's range and on the first hour, which is the value of waiting for the open.

**The readings, per (t, h):**
- **IMMEDIATE:** F_now beats F_open;
- **EARLY:** F_open's partial is at least 0.05;
- **BOTH, or NEITHER,** as they fall.

## 3. Q3 — does the size change the mean?

- **The split:** κ_A,60 and M_A,60 by F_open's walk-forward tercile τ (quiet, mid, big; D720's label), and by
  F_now's tercile at t.
- **The statistic, per anchor:** Δκ_A = κ_A(quiet) − κ_A(big), against the enumerated rotation of τ over the
  sessions (the label moved, the prices fixed).
- **SIZE CHANGES THE MEAN** holds if, for at least one anchor, Δκ_A is outside its rotation's 5–95% band, or the
  best-respected anchor differs between the quiet and big terciles.

## 4. The bridge to money (reported only; nothing chosen)

- **The trade, per anchor and threshold k ∈ {0.25, 0.5, 0.75}:**
  - the first time after 10:00 that |D_A| ≥ k, go one MNQ towards A;
  - exit on the touch of A, at t+60, or at 15:59, whichever comes first;
  - one trade per anchor per day.
- **Reported:** gross and net at $4.07 a round trip, split by F_open tercile. Net and gross Sharpe and Sortino, the
  trade count, mean, median, win rate, the symmetric 1% trims, profitable years, and the largest year's share. The
  same trade toward A0 is the baseline.
- **Why:** this sizes the prize against the micro fee before any rule is designed with the principal. Choosing the
  anchor, the threshold or the tercile after seeing this table is selection, and is declared as such.

## 5. Readings for Q1 (per anchor, declared now)

| reading | condition |
|---|---|
| **RESPECTED** | κ_A,60 above its rotation's p95 **and** above A0's κ, **and** M_A,60 > 0 at a clustered t ≥ 2 |
| **WEAK** | only one of the two holds |
| **NOT RESPECTED** | neither holds |

The best-respected mean is the RESPECTED anchor with the largest κ_A,60.

## 6. Runner assertions

- **Lag:**
  - every anchor and F_now is re-derived at a sample of (day, t) by a second, minute-arithmetic implementation that
    reads only bars starting before t;
  - a canary that includes the t bar must fire;
  - F_open and F_close use D671's `forecast_audit` and `tier_audit` with their leak canaries;
  - the overnight window uses D671's `overnight_audit`.
- **Sign, in money:** a trade toward A pays when price moves toward A. A long below A that rises pays +$2 a point on
  MNQ.
- **Right quantity:** the forward move is P_{t+h} − P_t, not the move from the anchor; σ_d uses the prior 20
  sessions only.
- **The self-test** shows every audit firing on a deliberately broken input. Rotation offset 0 must equal the
  observed κ, and the mirror level must sit at the same distance as A.
