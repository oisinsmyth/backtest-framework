# D493 — PRE-REG: the account-size lever through the lifecycle — which plan and contract size makes a measured day-session edge carryable?

**2026-09-12. Committed before the runner exists (R8).** The principal: *"we are going all in on
the prop book."* PICKUP's first next step for the prop book after the overnight closure, and D486
§3(c)'s open question: the fee is per contract, the floor is per account, and *"the constraint
that creates the cost problem is the account size itself."* **Arithmetic on committed objects,
no new measurement, nothing opened, closed or admitted (R15).** It differs from D486 in one way:
D486 priced Sharpe; this record runs the **lifecycle** — evaluation pass, funded life, payouts
against fees, the daily-loss and consistency rules — at every published plan and size.

## 1. The objects (all committed)

- **Plans:** every entry of `D386.PLANS` (`scripts/d386_full_lifecycle.py`): Apex 25/50/100/150k,
  MFFU Rapid 25/50 (EOD and intraday) /100/150k, Topstep 50k, Take Profit Trader 25/50/100/150k —
  with each plan's target, drawdown type and lock, qualifying days and threshold, consistency
  rule, payout caps, fees. **No plan parameter is edited.**
- **Engine:** `D440.simulate_provider` (D386's day-by-day loop, bit-identical to D386 on the
  Gaussian provider, gate [P1] re-asserted here), 8,000 paths, 600-day horizon (D463's setting).
- **The measured day-session series:** `data/d463_trades.csv.gz` — the last-30-minutes
  momentum trade on ES, NQ, YM (2016-01-05 → 2023-12-29, ~1,900 days each; `pnl_usd`,
  `mae_usd`, `mfe_usd`, `cost_usd` per one full contract-day). It is the only committed
  **intraday-closable** daily series with a measured MAE. NQ: +$29.5 a day gross at one full
  contract, σ $705 (D463-master called it "not distinguishable from zero" — that is the point:
  it is the edge we have, at the size that failed).
- **The other measured edge, as moments only:** D484's NQ log-MACD B2 H=5 (gross 3.849 ticks,
  σ 216.97 ticks per trade, in-sample), run as D440's **GAUSS** provider at the equivalent daily
  moments. **Declared caveat:** the MACD holds five hours from any entry hour and is not yet an
  intraday-closable construction; its lifecycle here answers the fee question only, and the
  record says so beside every number.

## 2. The grid

For each plan × instrument (ES, NQ) × contract class (micro, full) × contracts n ∈ {1, 2, 3, 5}:

- **Provider:** MEASURED (the D463 series, rolling start at every day) for the last-30 trade;
  GAUSS for the MACD moments. Dollars scale with n and the class (micro = 1/10 of the full
  contract's dollars per point, `data/futures_contract_specs.json`).
- **Cost per contract-day:** $3.00 round trip + 1.009 ticks crossing (D465/D466's lines,
  unchanged) — in dollars this is where the class enters: the same $3 is 6 ticks on MNQ and 0.6
  on NQ.
- **Reported per cell:** P(pass evaluation), expected funded life (years), P(alive at 600 days),
  V = E[payouts] − E[fees] with its SE, P3 (worst day as % of the account; days below −2%),
  P5 (years with a single day > 40% of that year's profit), net Sharpe at that fee-in-ticks and
  its monthly-block SE, and C-d (daily σ as % of the account).
- **The decision statistic:** the set of cells with **V > 2·SE and P3 worst day ≥ −2% and funded
  life ≥ 3 years** — hurdle P's computable parts, at that plan's own rules.

## 3. Predictions (checkable from the runner's quantities)

1. **No cell clears all three on the last-30 series at any plan, any size.** The edge is
   +$29.5 a day gross on one full NQ (net ≈ +$20) against σ $705: a daily Sharpe of 0.03 does
   not pass an evaluation whose target is 6% of the account inside its drawdown. P(pass) < 25%
   on every cell.
2. **The lever moves in the direction D486 says and stops short:** net Sharpe on NQ rises from
   negative at one micro to +0.3–0.5 at one full contract; the 150k plans hold one full NQ with
   P3 worst day inside −2% on fewer than half the cells (σ $2,327 a day is 1.55% of $150k, so a
   2σ day breaches).
3. **For the MACD moments at one full NQ on a 150k plan, V is positive at MFFU (the cheapest
   evaluation) and negative at Apex and TPT** — the fee structure, not the edge, orders the
   firms. This is the one row that could change what the principal buys, and it is conditional
   on a construction that does not yet exist in intraday-closable form.
4. **Micros never clear V > 0 on either series.** The fee-in-ticks is the whole story at
   micro size (D486: 70–86% of cost).

## 4. What this record does not do

It admits nothing and buys nothing. It tells the principal, in the units the firms use, whether
the prop problem is a signal problem or a size problem for the edges the programme already
holds. If prediction 1 holds and prediction 3 holds, the answer is: **a bigger account makes a
real day-session edge carryable, and the programme does not yet hold one** — which sets the
gross-per-trade target every future prop signal must meet (D494's family is scored against it).
