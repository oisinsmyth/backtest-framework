# D633 RESULT — Stage D on NG is NOT RETAINED: the TAS imbalance carries nothing about the window's aggressive flow, so adding it only dilutes P1

*Filename shortened 2026-09-27 to keep every tracked path within 85 characters (`tests/unit/test_public_cut.py`, D540); was `D633-RESULT-stage-d-not-retained-the-tas-imbalance-is-not-window-flow.md`. The H1 above is the full title.*

*Run once on 2026-09-26 (`scripts/run_stage_d_ng.py --run`, committed `1ed2867` after the pre-registration
`acab2bd`). Output: `data/ledger_stage_d_ng.json`, which `--check` reproduces byte for byte. The window flow is
Sierra's futures flow: PROVISIONAL like D629, subject to the NG check after 2026-10-10. The TAS imbalance is
exchange-flagged in both of its eras.*

## 1. The verdict

| clause (all 1,935 days; Stage D fits nothing) | Stage A | Stage D | rule | result |
|---|---|---|---|---|
| 1. flow: partial correlation with the window flow | 0.136 | **0.043** (×0.32) | ≥ ×1.10 | **fails** |
| 2. price: H2's t | **5.01** ($66, 1,028 trades) | 1.23 ($17, 823 trades) | D ≥ A | **fails** |
| 3. midday: the window gain against the midday gain | — | −0.093 against +0.025 | window > midday | **fails** |

**NOT RETAINED** under D633 §5. Stage D was individually testable at the plausible effect (POWER: 0.97 at γ = 0.061),
so this is evidence against the mechanism, not an inconclusive miss. The checks held:
- the known answer: with Q5 = 0, D's gate and τ\* equal Stage A's on all 1,936 days;
- Stage A's H2 here reproduced D630's exactly (n 1,028, t 5.0117).

## 2. The TAS imbalance is unrelated to the window's aggressive flow

| | partial correlation with S_win | slope γ̂ (HC1 t; NW t) | with P1 in the fit |
|---|---|---|---|
| TAS imbalance from the open to τ\* | −0.031 | −0.0064 (−0.93; −0.94) | −0.0029 (−0.44) |
| the whole imbalance, to 14:30 (a diagnostic; not tradable) | −0.047 | −0.0074 (−1.47; −1.55) | −0.0042 (−0.85) |

- Signs agree on **50.1%** of days.
- **By source:** −0.087 on Databento's era (to 2020-02-10, 665 days) and +0.014 on Sierra's (1,270 days). There is
  no relation in either, so the stitch carries nothing.
- **What it means for the mechanism** (deposit line 306: the liquidity providers who sold TAS "must buy in the
  window"). That buying does not appear as aggressive window flow, not even against the whole day's imbalance. The
  providers evidently hedge passively (resting orders filled by others), across the day, or by netting their books.
- **Why Stage D is worse, not merely no better.** The imbalance is larger than P1 (SD 2,475 against 1,692 contracts)
  and unrelated to the target. Adding it dilutes P1's signal:
  - flow correlation 0.136 → 0.043;
  - out-of-sample MSE 257.5k → 261.9k;
  - 20% of common-day directions flip, 37% of D's trades are days Stage A would not trade, and the trade falls to
    $17 gross (−$9 net).
- **D629's puzzle:** the literal slope (no return control) moves from −0.061 (t −7.98) on P1 to −0.017 (t −2.66) on
  μ_D. That is dilution by an unrelated term, not an explanation.

## 3. The trade, all days, reported beside

| | Stage A (D630) | Stage D |
|---|---|---|
| trades | 1,028 | 823 |
| mean gross / net | $66.02 / $40.02 | $16.97 / −$9.03 |
| Sharpe / Sortino, net | 1.09 / 1.75 | −0.24 / −0.35 |
| median trade | $40 | $0 |

## 4. What this means

- **D is dropped. The ledger stays at Stage A on NG** (frozen, A10).
- **Three stages have now failed the same way,** each adding observed or forecast flow that is not the window's
  aggressive flow:
  - B (D631): the gain was order-flow persistence;
  - C1 (D632): the funds' creations;
  - D: the TAS imbalance.
- **What survives is narrow and consistent.** P1 alone predicts both a small share of aggressive window flow (D629,
  6%) and a price move into the settlement that reverts afterwards (D630). Neither the funds' other flows nor the
  TAS market add to it.
- **This was the seventh test on this in-sample with this predictor** (D627–D633).
