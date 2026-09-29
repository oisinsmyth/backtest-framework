# D678 RESULT: NO MECHANISM. Going with the overnight gap at the open carries no direction on HO, RB, BZ, HG or PL. The family's gross is exactly what a random side earns on the same gap days (+0.25% of ATR, null median +0.25, rank 0.50). D677's gap lead was the exit on big days, not the gap's direction

*2026-09-29.*
- *One run of `scripts/stage0_d678_gap_open.py --run` under D678 (`7914bfde`) and D678-A1 (`ebbe30fb`); runner
  `15dabfe2`; 0.9 min.*
- *Output: `data/stage0_d678_gap_open.json`.*
- *In-sample through 2025-02-28. No vault, and no HO/RB data after 2026-09-18.*

**Inputs, gated before the run** (fixture meta `2cd82b3d`):
- `fut_opening_globex_1m_ho_rb_bz_hg_pl`, at `%.5f`;
- identity with `fut_day1m` exact on all five (789,747 / 789,772 / 762,228 / 575,232 / 579,889 bars; 0 mismatches,
  0 unmatched);
- coverage ≥ 0.887 usable in every root-year (excluded: HO 48, RB 48, BZ 95, HG 2, PL 15);
- the seal held.

## 1. Gate 1, the mechanism (family, gross, % of ATR)

| | value |
|---|---|
| statistic: the mean over 1,459 dates of each date's mean gross across the roots that gapped | **+0.25% of A (HAC t 0.40)** |
| sign-flip null (same days, a random side at each root's long share, one draw per date shared by all roots): p50 / p95 (SE) | +0.25 / +1.13 (0.012) |
| rank | **0.50** |
| without February–April 2020 | +0.25 |
| **Gate 1** | **fails:** t 0.40, below p95 |

**The statistic equals the null's median to 1e-4.** Checked: the null's own aggregation, fed the actual sides,
reproduces the statistic exactly (0.252432). The equality is a coincidence of the numbers, not a defect.

**Weighting.** Weighting each trade rather than each date gives +0.62%, still far inside the null.
- The declared statistic weights dates equally, so roots that often gap alone weigh more: HG 29% of the weight, PL 24%.
- 703 of the 1,459 dates have one root gapping; 43 have all five.

**Mechanism reading (D678-A1): NOT CONFIRMED.** Excess over each root's own null p50 is positive on 3 of 5 (binomial
p 0.50).

## 2. Per root (full size, friction counted once)

| | HO | RB | BZ | HG | PL |
|---|---|---|---|---|---|
| gap trades (a year) | 539 (62) | 478 (55) | 589 (69) | 663 (72) | 555 (60) |
| gross, bp (t) | +4.23 (1.4) | +4.53 (1.0) | −0.47 (−0.2) | −1.87 (−1.1) | +5.12 (2.0) |
| gross, % of A | +1.55 | +1.13 | −0.64 | −0.85 | +2.35 |
| **own null p50 / p95 / rank** | +0.12 / +1.69 / 0.93 | **+1.68** / +3.51 / 0.32 | −1.00 / +0.43 / 0.66 | +0.75 / +2.23 / **0.04** | +0.32 / +1.91 / **0.98** |
| excess over own p50 | +1.43 | −0.55 | +0.36 | −1.60 | +2.03 |
| cost, bp (% of A) | 7.18 (2.9) | 4.97 (1.8) | 5.69 (2.2) | 4.32 (2.8) | 10.49 (5.4) |
| net, bp (t) | −2.95 (−1.0) | −0.43 (−0.1) | −6.15 (−2.1) | −6.20 (−3.6) | −5.36 (−2.1) |
| net at +1 tick | −4.00 | −1.56 | −9.39 | −9.35 | −7.47 |
| **verdict** | NOT SUPPORTED | NOT SUPPORTED | NOT SUPPORTED | NOT SUPPORTED | NOT SUPPORTED |

**The random side earns what the gap side earns.**
- On RB a random direction on the same gap days makes +1.68% of A gross, more than going with the gap (+1.13).
- Only PL's gap side clears its own p95 (rank 0.98). HG's falls below its p5 (0.04). Both are what five draws from
  nothing look like.
- **The positive gross D677 found in CL/NG/GC/SI's gap subset is therefore the E4 trail on high-volatility days**
  (gap days are big-move days, and a trailing stop profits from a day that runs either way). **It is not the gap's
  direction.** D677 never compared it with a random side. This test did.

## 3. Secondary: the gap vs the fresh intraday break (% of A)

| | family | HO | RB | BZ | HG | PL |
|---|---|---|---|---|---|---|
| gap | +0.25 | +1.55 | +1.13 | −0.64 | −0.85 | +2.35 |
| fresh break | −0.46 | +1.50 | +0.88 | +1.11 | +0.55 | +0.15 |
| gap − fresh (t) | +0.72 (0.9) | +0.05 | +0.25 | −1.76 | −1.40 | +2.20 (1.6) |

D677's contrast (the gap good, the fresh break bad) does not transfer either. Here the fresh breaks are about flat or
positive.

## 4. Reported

- **Long / short, gross bp:** HO −2.07 / **+12.50 (t 3.0)**; RB −4.35 / **+14.35 (2.2)**; BZ −7.68 / +8.92 (1.6);
  HG +0.13 / −4.05; PL +5.99 / +4.17.
  - Energy's short side is strong, as in D676 (short ≥ long on CL/NG/GC/SI).
  - It is a sample-period drift read (the sign-flip null keeps the long share, not the direction). Post hoc.
- **Gap size, beyond the stop by < 0.25 A / ≥ 0.25 A:** HO +0.95 / +8.66; RB +5.18 / +3.70; BZ +0.14 / −1.25;
  HG −0.81 / −2.77; PL +2.89 / +7.54. No consistent sign.
- **EIA days vs other days:** HO +4.59 / +4.12; RB −3.03 / +6.46.
- **R2's removed gap trades:** HO +9.15 (n small); RB −13.88; HG −0.05; PL +17.81.
- **Years with gross > 0, of 10:** HO 7, RB 5, BZ 5, HG 3, PL 7.
- **The four groups (net, bp):**

  | | HO | RB | BZ | HG | PL |
  |---|---|---|---|---|---|
  | median | −22.2 | −26.2 | −25.2 | −18.8 | −21.0 |
  | win | 36% | 37% | 34% | 31% | 34% |
  | payoff | 1.59 | 1.71 | 1.53 | 1.50 | 1.53 |
  | skew | 1.5 | 1.6 | 2.1 | 1.7 | 1.5 |
  | trimmed | −4.3 | −2.3 | −7.6 | −7.4 | −6.7 |
  | Sharpe net / gross (per trade, annualised) | −0.32 / +0.46 | −0.03 / +0.35 | −0.66 / −0.05 | −1.24 / −0.37 | −0.71 / +0.68 |
  | Sortino net | −0.56 | −0.06 | −1.10 | −1.95 | −1.16 |

  - 97–98% of trades end on a stop, with a median hold of 35–49 min.
- **Component line (1 full contract, daily $):**
  - net Sharpe: HO −0.44, RB −0.21, BZ −0.60, HG −1.14, PL −0.69;
  - gross: +0.23, +0.15, −0.02, −0.37, +0.67;
  - ρ with K8 ≤ 0.05; the energy roots correlate with each other (0.37–0.50); metals with anything, < 0.1;
  - the MACD arm (#2) and the NG winter spread (#3) are not rebuilt.

## 5. Predictions (§6)

| # | prediction | outcome |
|---|---|---|
| 1 | the family passes Gate 1 | **failed** (rank 0.50) |
| 2 | no root passes Gate 2 | held |
| 3 | gap − fresh > 0 on ≥ 4 of 5 | **failed** (3 of 5) |
| 4 | the gap's gross > 0 on ≥ 4 of 5 | **failed** (3 of 5) |

## 6. Routing (§7)

**NO MECHANISM. D677's lead (a) is closed.**
- The overnight gap through yesterday's day-session range does not carry direction into the day session on 23-hour
  energy and metals.
- The gross that made it look like a lead is available to a random side on the same days.
- **This is the principal's concern answered for this idea:** a gross edge that is not beyond a direction-randomised
  null is not a mechanism.
