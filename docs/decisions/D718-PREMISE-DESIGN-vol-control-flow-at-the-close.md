# D718 PREMISE DESIGN — proposal A: does ES's last 15 minutes move in the direction volatility-target funds must trade at the close?

*2026-09-30. Committed before its runner (`scripts/premise_d718_vol_control_close.py`) exists (R8).*
- **The principal:** "Ok do the cheap check please".
- **What it is:** a premise check. **No trade is scored as a result:** any trade statistic is reported only.
- **In-sample:** 2016-01-04 → 2023-12-29, ES bars only. Nothing dated 2024-01-01 or later is read. No slot.

## 1. The mechanism (proposal A of the five-agent round)

- **Who is forced to trade:** volatility-target money (insurers' variable-annuity hedges, risk-control indices, and
  volatility-scaled CTAs) holds equity exposure ∝ 1/σ̂.
- **When they trade:** when σ̂ rises they must sell, and when it falls they must buy, at or near the close.
- **Which way:** the sign comes from yesterday's change in volatility, not from today's return.
- **What was ruled out before:** D661 sized only the stress version (row 10) and rejected it on size and timing.
  **No record has tested the ordinary-day flow at the close.**

## 2. The projected flow (a fixed convention, nothing fitted)

- **The daily return:** r_d = ln(P16:00(d) / P16:00(d−1)), same contract. P16:00 is the close of the 15:59 bar. A roll
  session leaves σ̂ unchanged.
- **The volatility estimate:** σ̂²(d) = λ σ̂²(d−1) + (1 − λ) r_d², with **λ = 0.94** (the RiskMetrics convention). It
  starts from the sample variance of the first 20 sessions of the warm-up (the fixture's sessions from 2015-06-01).
- **The target weight:** w(d) = min(1, 0.10 / (σ̂(d−1) × √252)). It uses data through the previous close and is
  executed at d's close.
- **The flow:** f(d) = w(d) − w(d−1), in fractions of assets. **The funds buy when f > 0.** f = 0 (both days at the cap)
  is no flow.

## 3. The windows (ES one-minute bars, `fut_ES_rth_1m`; sessions with ≥ 380 bars; one contract)

| window | from | to | its momentum control |
|---|---|---|---|
| **close** | P15:45 (the close of the 15:44 bar) | P16:00 (the close of the 15:59 bar) | the day's move to 15:45, ln(P15:45 / P16:00(d−1)) |
| **midday placebo** | P11:45 | P12:00 | the day's move to 11:45 |

The window return is in bp. z(·) standardises over the sample.

## 4. The premise statistic and gates (fixed now)

**The regression, per window:** window return = α + β · z(f(d)) + γ · z(the momentum control) + ε. Newey–West with 5
lags. It runs on days with f ≠ 0.

| gate | passes when |
|---|---|
| **G1 exists** | β_close > 0 with NW t ≥ 2.0 |
| **G2 not chance** | β_close above the p95 of the **enumerated rotation** of the f series across days, offsets 20 … n − 20, with the returns and controls fixed (SE 0) |
| **G3 the close, not the day** | the midday β has NW t < 2.0, AND β_close > β_midday |
| **G4 today's flow, not yesterday's** | the same close regression with f(d − 1) in place of f(d) gives NW t < 2.0. f(d − 1) was already executed yesterday, so a signal there would be volatility persistence, not this flow |

**Readings:**
- **PRESENT:** G1–G4. A trade design then goes to the principal as a new record.
- **ABSENT:** G1 or G2 fails.
- **NOT THE FUNDS:** G1 and G2 pass, and G3 or G4 fails.

## 5. Reported, never gating

- **The sign trade:** sign(f) held 15:45 → 16:00 at one MES ($4.42): gross, net, NW t, trades a year, and the four
  groups.
- **The trade on the largest third of |f| only.**
- **The LETF-agreement subset** (sign(f) = the sign of the day's move to 15:45). **The up-day contrast:** among days up
  to 15:45, the window return on f < 0 days against f > 0 days, which is the discriminating cell.
- **The uncapped weight, and λ ∈ {0.90, 0.97},** read as a shape (not re-gated).
- **β by year;** the share of days with f ≠ 0 by year (the cap binds in quiet years).
- **ρ of the sign trade's daily net** with NQ F2 (slot 7; 15:30 → 16:00 on NQ, an overlapping clock). The in-sample
  series is rebuilt through `vault_d716_nq_f2`, with its known answer re-proved.
- **How the flow's sign lines up with F2** (the other session's request; D711 left "flow into the close" unresolved as
  F2's mechanism): on ES F2's and NQ F2's take days, the share where sign(f) equals F2's side, against the share on all
  days. ES F2 is rebuilt through `vault_d707_last_hour_f2`'s in-sample functions.
- **Which momentum is controlled:** the day's move from the previous close to 15:45. **This is not F2's own signal**
  (the 14:30 → 15:30 hour). A second, reported version adds z(the 14:30 → 15:30 move) as a further control, so that
  "the flow's sign" is not "the last hour's sign".

## 6. Size and power (stated now)

- About 1,900 days in the sample, fewer where f = 0.
- **The detectable β:** the 15-minute window's sd is about 12–16 bp, so a β of about 0.8–1.0 bp per sd of flow is
  detectable at t 2. The proposal's guess was about 1 bp on typical days and 3 bp on big-flow days.
- **The trade:** at an ES price of about 3,000, 1 bp ≈ $1.50 at MES. So even a PRESENT premise may not clear the $4.42
  round trip on ordinary days. That is the question for the next record.

## 7. The runner's assertions

- **Lag:** f(d) is re-derived for 40 sampled days by a plain loop over daily closes, using only data through d − 1.
  **Break:** a σ̂ that includes day d must raise.
- **Sign:** a buy-flow day with the price rising 15:45 → 16:00 scores positive.
- **Right quantity:** the midday and close windows differ, and the rotation's offset 0 equals the observed β.
- **The seal:** a 2024 row raises.
- **Synthetic:** a planted flow effect passes G1–G2, and noise fails G1 about 97.5% of the time.

**Output:** `data/premise_d718_vol_control_close.json`.
