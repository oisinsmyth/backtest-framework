# D659 — RESULT: both opening-v2 cells pass D652's kill, and the vault cannot confirm either: power at the full in-sample edge is 6.5% (fade) and 5.0% (hold), and the hold's model adds nothing to trading every day

*2026-09-28. One in-sample run of `scripts/run_opening_v2.py --run` under D652 (`e80012c`), OA-A10, OA-A11 (the EV rule
with a 1× cost margin) and OA-A12 (the break at 2022-05-16), after D645's Phase 4 run (D658), as §6 orders. 2.3 min.
Walk-forward 252/63, the C grid, blocked 5-fold CV. Last session read 2025-02-28; nothing from 2025-03-01 was read.
Output: `data/opening/v2_insample.json`, `v2_sessions.csv`, `v2_power.json`; 2 trials, family "opening V2 (D652)".*

## §6, the kill: both cells are carried

A cell is carried if **policy mean > 0 and diff > 0**. The diff is policy − always: "always" trades every eligible
row. Both are per session, net, at the micro cost.

| cell | test sessions | traded rows | policy net | gross | always | diff (HAC t) | carried |
|---|---:|---:|---:|---:|---:|---:|---|
| **V2-F**, fade at 09:45 to the prior close, 60-min time stop | 1,704 | 842 of 3,039 | **+0.40 bp** (t 0.78) | +1.02 | −2.10 | **+2.50** (3.81) | yes |
| **V2-C**, continuation from 10:30, held to the close | 1,915 | 1,259 of 3,803 | **+1.32 bp** (t 1.69) | +1.97 | +1.26 | **+0.06** (0.05) | yes |

## §7, power: the headline

§7 requires the headline to say so if PASS at s_e = 1 is below 0.5. The vault is 390 sessions, drawn as 20-session
blocks, 2,000 draws, with §8's rule (Holm across the two cells):

| edge kept | V2-F PASS | V2-C PASS |
|---|---:|---:|
| 1 (the in-sample edge, all of it) | **6.5%** | **5.0%** |
| 0.5 | 4.2% | 2.3% |
| 0.25 | 4.0% | 0.9% |
| 0 (no edge) | 2.5% | 0.7% |

**Power is 5–6.5% even if every basis point of the in-sample edge is real.** A PASS would be barely more likely
than on a zero edge. The vault's 390 sessions cannot resolve a policy mean of 0.4 or 1.3 bp at these volatilities.
§7 also notes the power is optimistic, because the blocks resample the in-sample's own regimes.

## What each cell's number is made of

### V2-F, the fade: the EV rule selects, and one year pays for it

- **The selection is real on this sample.** The null shuffles p within market × year and re-applies the EV rule
  (1,000 draws):
  - null p50 −0.97, p95 −0.45 (bootstrap SE 0.017);
  - the score is +0.40, and no draw reached it. **ABOVE, decisively.**
  - The target-hit AUC is 0.817 (0.798–0.835). That is mostly mechanical: the chance of reaching the prior close
    falls with the distance to it.
- **Trades** (842): gross mean 4.13 bp. That is below 2c (5.04 bp), i.e. the breakeven round trip is 4.13 bp.

  | | mean | median | win | skew | ex-top 1% | ex-bottom 1% | trimmed both |
  |---|---:|---:|---:|---:|---:|---:|---:|
  | net, bp | 1.61 | 10.19 | 57% | −0.83 | 0.30 | 3.47 | 2.17 |

  The mean is far below the median: the time-stop losers (551 of 842 exits) are the left tail.
- **Where it comes from:**
  - by year: **2022 nets +2,387 bp of a total +1,355**, so without 2022 the cell loses. Four of the seven
    full years are negative (2018, 2021, 2023, 2024);
  - by concentration: five sessions make half the net;
  - by market: ES +3.99 bp a trade, NQ +0.64;
  - by era: before the break +1.09, after +2.61.
- **Robustness** (policy net per session):

  | variant | policy net |
  |---|---:|
  | 2× cost | −0.22 |
  | stress entry | −1.98 (t −4.1) |
  | margin 0 | +0.35 |
  | **A4 unscaled** | **+0.35** |
  | break ±63 sessions | +0.36 / +0.41 |
  | a 1.5σ fade stop | +0.44 |

  **Scaling A4 by liquidity adds 0.05 bp.** The research's rescaling does nothing here.
- **Component line** (1 micro, dollars, computed by the runner):
  - net Sharpe **0.22**, Sortino 0.29; gross Sharpe 0.64, Sortino 0.87;
  - hit rate 57%, per-trade skew −0.99;
  - $1.27 a day, maxDD $3,372, vol $1,459 a year;
  - in the market on 38% of sessions, 47 min a trade.

### V2-C, the hold to the close: the money is in holding, not in the model

- **The model's selection is worse than chance.** The same null gives p50 **+1.48** and p95 +2.38 (SE 0.041), and
  62% of random selections beat the policy's +1.32. **BELOW.** The AUC is 0.542 (0.519–0.565), and the diff over
  trading every day is +0.06 bp (t 0.05).
- **What earns is the always-on hold itself:** +1.26 bp a row across 3,803 rows. It is tail-carried: median +0.41,
  the top 1% of rows is 252% of the sum, and without it the mean is −1.94.
- **The policy's trades** (1,259): gross mean 5.98 bp, above 2c (3.95).

  | | mean | median | win | skew | ex-top 1% | ex-bottom 1% | trimmed both |
  |---|---:|---:|---:|---:|---:|---:|---:|
  | net, bp | 4.01 | 8.19 | 55% | +0.14 | 1.13 | 6.52 | 3.64 |

  The top 1% of trades is 72% of the net. The top trade is NQ on 2022-11-30: long, +427 bp, held to the close.
- **Where it comes from:**
  - by year: 2018 and 2021 negative, **2024 is +2,155 of +5,043**;
  - by concentration: nine sessions make half the net;
  - by market: NQ +4.72 bp a trade, ES +2.36;
  - by era: after the break +4.76, before +2.31.
- **Robustness:**

  | variant | policy net | diff |
  |---|---:|---:|
  | margin 0 | | −0.17 |
  | A4 unscaled | | −0.02 |
  | 2× cost | +0.67 | |
  | stress | −0.69 | |
  | no stop | +1.37 | |
- **Component line** (1 micro, dollars, computed by the runner):
  - net Sharpe **0.62**, Sortino 0.94; gross Sharpe 0.87, Sortino 1.35;
  - hit rate 55%, per-trade skew +0.27;
  - $7.72 a day, maxDD $3,582, vol $3,157 a year;
  - in the market on 47% of sessions, 310 min a trade.

  It reads like a component, but the component is the always-on hold, not v2's model.

### Correlations with the ledger

The runner reported these missing: D466's fixture is gitignored and absent from the worktree.
`scripts/diag_opening_v2_component_corr.py` computed them post hoc with the runner's own `component_corr`, loading
the ledger from the main checkout. The series is per-session bp, because the runner does not write its dollar series.
Output: `data/opening/v2_component_corr.json`.

| | K1 | K2 | K3 | K4 | K5 | K6 |
|---|---:|---:|---:|---:|---:|---:|
| V2-F | −0.04 | 0.06 | 0.06 | 0.02 | −0.05 | −0.01 |
| V2-C | 0.06 | 0.10 | 0.08 | 0.10 | 0.05 | 0.01 |

- V2-F against V2-C: ρ −0.11 (1,704 days).
- The prop book's MACD arm has no daily series on disk, so it is not computed.

## What it means

1. **By the letter, both cells are carried**, and D652 sends them to the vault.
2. **Neither look can confirm anything.** At 5–6.5% power, a FAIL says nothing about the cell, and a PASS is little
   more likely than on a zero edge. Spending the look costs a single read of the vault for almost no information.
3. **V2-F** is one year (2022) and dies at twice the cost.
4. **V2-C's model adds nothing** (diff +0.06, null BELOW, AUC 0.54). If the vault passed it, it would be confirming
   "hold continuation from 10:30 to the close". That was not a pre-registered cell, and in-sample it is tail-carried.
5. The research's two specific ideas did not carry the result:
   - A4 scaled by liquidity: unscaled A4 gives the same numbers;
   - the 0DTE break: the ±63-session moves barely change anything.

## Recommendation, for the principal

- **Close v2 without spending its vault look,** and do not take slot 9.
- **Or freeze it and queue it for the joint run knowing the power is 5–6.5%.**
- D652 §7: the look is spent only on the principal's word, whatever the power.
- The freeze (`FROZEN_v2.json`) and the slot-9 registration wait for that word.
- **Not a construction here:** the always-on 10:30 → close continuation, +1.26 bp a row in-sample, is a separate
  question. It would need its own pre-registration on data it has not been chosen on. The 2024+ futures slice is
  spent for trend (memory), so the only fresh sample is the vault.
