# D631 RESULT — Stage B on NG is NOT RETAINED: its flow gain passes but is general order-flow persistence (the midday placebo gains as much), and it weakens the trade

*Run once on 2026-09-26 (`scripts/run_stage_b_ng.py --run`, committed `37f7efa` after the pre-registration
`673367c`, its amendment `7a33f36` and the POWER rerun `eea4a73`). Output: `data/ledger_stage_b_ng.json`, which
`--check` reproduces byte for byte. It is PROVISIONAL like D629, subject to the NG check of Sierra's sign after
2026-10-10.*

## 1. The verdict

| clause (out of sample, 1,684 days from 2018-06-20) | Stage A | Stage B | rule | result |
|---|---|---|---|---|
| 1. flow: partial correlation with the window flow, net of [1, r, flags] | 0.137 | **0.170** (×1.24) | ≥ ×1.10 | **passes** |
| 2. price: H2's t over each stage's trades | **5.08** ($68 a trade, 1,010 trades) | 3.90 ($51, 1,025) | B ≥ A | **fails** |

**NOT RETAINED (inconclusive)** under D631 §6. Later stages build on Stage A. The known answer held: at p = 0,
Stage B's gate and τ\* equal the panel's on all 1,936 days.

## 2. The flow gain is not the funds'

- **POWER's ceiling was broken.** Under the ledger's own prior, a perfect update could add at most 2.5%. Stage B
  added 24%. That is possible only if z carries information about the window flow that does not pass through the
  funds' Q, and so the prior's model does not account for it.
- **The midday placebo shows the same gain.** At 11:30, with z = 10:52 → 11:30 and the 11:50–12:20 flow, the update
  lifts the partial correlation from **−0.036 to +0.140**. There is no settlement at midday and no fund execution.
  The placebo reads "not retained" only because the rule needs Stage A's value above zero. **Pre-window signed flow
  predicts later signed flow at any time of day:** that is order-flow persistence, which the update step absorbs as
  if it were the funds' pre-absorption.
- The deposit's literal raw z (no residualisation on the return) gives the same: 0.165 against 0.137.
- **The parameters are unstable** (deposit §8's red flag). The fitted p swings between 0 and 0.9 across the 27
  windows at every τ (medians 0.1, 0.2 and 0.5). p = 0 is chosen in 22–33% of the windows, and λ runs up to 15.
  The full-sample fits (p 0.35, 0.5, 0.9) are not stable either.
- **The error budget moves by 1%:** the out-of-sample MSE of the window flow is 243.2k (A) against 240.7k (B).

## 3. The trade gets worse

Stage B's gate and direction change the trade on about 7% of its days: 93% of Stage B's 1,025 trades are also
Stage A's. On the out-of-sample days:

| | Stage A | Stage B |
|---|---|---|
| mean gross / net per trade | $68.08 / $42.08 | $50.84 / $24.84 |
| Sharpe / Sortino, net | 1.21 / 1.95 | 0.74 / 1.15 |
| Sharpe / Sortino, gross | 1.96 / 3.28 | 1.50 / 2.46 |
| median trade; the mean trimmed 1% both ends | $40; $65.3 | $30; $47.7 |

The update's extra information is about flow persistence, and it moves the entry time and direction away from the
days on which Stage A's price effect lives.

## 4. What this means

- **Stage B is dropped. The ledger stays at Stage A on NG** (frozen, A10).
- **POWER's premise was wrong in an instructive way.** It assumed the only thing z could tell us about the window
  is the funds' flow. The data show z also predicts the window through persistence, strongly enough to pass the flow
  clause by itself.
  - **Any later stage judged on window flow must control for this.** The placebo's gain is the benchmark: a stage's
    flow gain counts only in excess of the same update's gain at midday.
  - This is recorded for the retention rule; the rule itself is unchanged.
- **Stage I** (the large-lot split of the same measurement, §8A.5) inherits the problem unless its large lots are
  specific to the settlement. Its pre-registration must carry the midday placebo as a gating control.
- This was the fifth test on this in-sample with this predictor (D627–D631).
