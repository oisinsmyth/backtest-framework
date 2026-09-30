# D720 STAGE 0 DESIGN — size the direction we already have: does a forecast of the day's size, used to trade 0, 1 or 2 MNQ, improve the two NQ lines that carry a direction?

*2026-09-30. The principal: "Let try your idea, and push it to its edge, go with your full recommendation."*
- **The idea (this session's recommendation):** the only things that have paid here are a direction on NQ's
  afternoon (the admitted MACD arm; NQ F2) and a forecast of how far the index moves (dealer gamma, D665; IV over
  RV, D691). They have never been joined. Size each existing trade by the day's forecast size.
- **This record is committed before the runner exists.** The runner is committed before its one run; the result is
  a separate record (R8).
- **What it is:** a Stage 0 diagnostic on spent in-sample data, oracle first (the principal's rule for filters).
  It measures; it admits nothing and freezes nothing.

## 0. What the record already says, and why this is still worth one run

- **D690:** on the hourly continuation, perfect size foresight lifted full ES from −0.42 to +0.33, because that trade
  has almost no direction per unit of size. Size information scales winners and losers alike.
- **The difference here:** both lines below carry a direction. The arm grosses $11.59 a trade against a $3.50 round
  trip (efficiency well above zero), and NQ F2 nets +$20.67. If a line's gross grows with the day's size at a fixed
  efficiency, a second contract on big days earns more than its fee, and a skipped small day saves a fee it could
  not pay. Whether that holds is an empirical question D690 could not answer.
- **Known limits, stated before the run:**
  - **The arm has no unread slice** (D503 read its 2024+). Anything found on it is a measurement only
    ([[conditioners-on-the-admitted-arm-are-structurally-unavailable]]).
  - **NQ F2 already filters on realised size** (its a and b tiers). The forecast here must add to that.
  - **A dollar bar turns a relative size signal into a volatility-regime gate** (D703). The primary label is
    relative (the forecast's walk-forward percentile), and every result is reported by year.

## 1. The two lines (one MNQ each, as their own records build them)

| line | construction | window | known answer the runner must reproduce |
|---|---|---|---|
| **L1, the MACD arm** | D504's `build()`, D503's `simulate_trades()`, through D669's `load_panel()` / `trade_table()` | 2016-01-04 → 2023-12-29 | 1,908 trades, net total $15,423.414, gross $22,110.00 (D669) |
| **L2, NQ F2** | D711's code at 15:30 on NQ, through D716's `build()` | its own window to 2023-12-29 | 274 trades, mean net +$20.670105, take-session sha256 `cdd92027…` (D716) |

- **The seal.** NQ's 2024+ last hour is D716's joint-vault look. The hourly fixture is cut to sessions before
  2024-01-01 **before** D504's build runs; D716's `build()` is called in-sample only. Nothing dated 2024-01-01 or later
  is used. The arm's known answer, reproduced on the cut fixture, proves the cut changes nothing before it.
- **Cost:** each line's own runner-computed round trip at one MNQ (the arm's `cost_usd`, F2's `cost_line("NQ")`).

## 2. The size label (known by 09:30 ET on session s; both lines enter later)

- **f_s:** D691's full model M1, the walk-forward non-negative forecast of y = ln(range/ATR20) on NQ from D671's
  features (SPX gamma g, overnight range, rv5, |gap|, event day, opex) plus ln(IV/RV20). Built by D691's and D671's
  code, unchanged: `frames()`, `iv_cached()`, `design()`, `forecast()`. The bars and GEX are cut to sessions before
  2024-01-01 before any feature is computed.
- **τ_s:** f_s's walk-forward percentile among the previous 250 forecasts (D671's `tiers`). τ is finite from about
  2019; **the evaluation window is every session with finite τ, to 2023-12-29.** Both books, sized and unsized, are
  scored on the same trades in that window.
- **Audits:** D671's `forecast_audit` and `tier_audit` (both re-derive from strictly earlier sessions), each shown
  to raise on its `leak=True` canary.

## 3. What is computed

**A. The oracle (the ceiling; unknowable in advance).** The same rules as C, on two realised labels:
- A-day: the walk-forward percentile of the realised y (the forecast's own target);
- A-trade: the trade's own |window move| terciles, pooled over the window (an upper bound, not a rule).

**B. Calibration.** By τ tercile and by A-day tercile, per line: trades, mean and median gross, mean |move|,
efficiency Σg/Σ|g|, mean net per MNQ, and win rate. The reading is whether mean gross rises across terciles while
efficiency holds.

**C. The sizing rules, declared now, all reported, none chosen after the run** (q = MNQ contracts, net = q·(g − c)):

| rule | q |
|---|---|
| **R1 (primary)** | 2 when τ ≥ 2/3, else 1 |
| R2 | 0 when τ < 1/3, else 1 |
| R3 | 0 / 1 / 2 by τ tercile |
| R4 (the edge) | 3 when τ ≥ 0.9, 2 when τ ≥ 2/3, else 1 |

For each rule and the unsized book (R0: q = 1), on the daily series over every session in the window (zero on
non-trading days), √252:
- all four groups: net and gross, Sharpe and Sortino, net $ a year, max drawdown, worst day, trades, mean,
  median, win rate, skew, kurtosis, the symmetric 1% trims (ex-top, ex-bottom, both), profitable years;
- **the increments over R0:** Δ net $ a year, Δ net Sharpe, Δ Sortino, Δ max drawdown;
- the account: P3a (days beyond 2% of the account a year) at $50k and $150k (`hurdle_p.p3`).

**D. The null.** Enumerated rotation of τ across the window's sessions, offsets 20 … n − 20 (the SE of the p95 is
0). Statistic: **R1's Δ net Sharpe** (primary); R2–R4's are reported against their own rotations. p50, p95 and rank
are reported.

**E. The accuracy curve.** A partial oracle of the realised y at normal-score correlation ρ ∈ {0, 0.1, 0.2, 0.3,
0.5, 0.7, 1} (`filter_oracle.partial_oracle_score`, 200 draws, seed 720), under R1 with pooled terciles. It gives
R1's Δ net Sharpe p05/p50/p95 at each ρ, and the real forecast's Spearman with y on the window's sessions places
it on that curve.

**F. Dependence.** Δ net $ by year, the share of the total Δ from the largest year, and from 2020 and 2022; ρ of the
sized and unsized daily books between L1 and L2; and L1+L2 combined, sized and unsized.

## 4. Readings (per line, declared now)

| reading | condition |
|---|---|
| **NO CEILING** | the oracle A-day under R1 does not raise net Sharpe over R0: even perfect knowledge of the day's size does not help this line |
| **CEILING ONLY** | A-day raises it, but the forecast's R1 Δ net Sharpe is at or below its rotation p95 |
| **LEAD** | R1's Δ net Sharpe is above its rotation p95, Δ net $ is positive in all but at most one of the window's calendar years (about five, 2019–2023), and no single year carries more than half of the total Δ $ |

- **A LEAD on L1 is a measurement only:** the arm has no unread slice.
- **A LEAD on L2 can go further only one way:** a separate pre-registration on NQ F2's joint-vault slice, which
  needs a programme slot, and only on the principal's explicit, separate word. This record asks for none.
- R2–R4 inform the shape. None of them can turn a reading into a LEAD.

## 5. Runner assertions

- **Lag:**
  - the arm uses D669's `lag_audit`, an independent state machine;
  - F2 uses D711's rv, σ and right-quantity audits, which run inside `clock_frame`;
  - the label uses `forecast_audit` and `tier_audit`;
  - a trade's q is read from τ at its own session, and a second implementation joins by session date rather than by
    position.
- **Sign, in money:** a favourable move pays positively at q = 2, twice what it pays at q = 1; q = 0 pays nothing and
  costs nothing.
- **Right quantity:** R0 reproduces each line's known answer on its full window, and the sized net is not the sized
  gross.
- **The self-test** shows every audit raising on a deliberately broken input, and the rotation at offset 0 equal to
  the observed statistic.

## 6. Out of scope

- Stops and targets set from the forecast: D630 found that exits cannot rescue a thin micro edge.
- Any retuning of either line's signal.
- ES or MES: the principal trades micro, and MNQ is the vehicle (the fee is 2.4% of NQ's typical move, against 4.7%
  on MES).

## A1 (2026-09-30, before the runner is committed or run)

**What the runner's synthetic self-test showed about R1's statistic.** On a book where every day has the same
Sharpe (the move scales the P&L and its risk alike) and there is no fee, a size label that is right about the day
LOWERS R1's net Sharpe. It sat at the 1st percentile of its own rotation, because doubling the largest days adds
variance where variance is already largest. The label beats its rotation only when the fee is large against the
move (then big days carry more net per unit of risk) or when efficiency rises with size. So R1's Δ net Sharpe asks
exactly the question the account needs answered ("does sizing by the forecast raise risk-adjusted net?"). It is
not a test of "does the label know the size", and a size-informative label can fail it. Nothing in s.3 or s.4
changes.

**One line is added, reported and never gating:** Δ net $ (the sized book's total net less R0's) against the same
enumerated rotation, for R1–R4. It asks whether the label picks days with more net per contract than a random
choice of the same number of days.
