# D632 RESULT — Stage C1 on NG is NOT RETAINED: the forecast creation flow makes the ledger WORSE on window flow, and a better forecast makes it worse still

*Run once on 2026-09-26 (`scripts/run_stage_c1_ng.py --run`, committed `3f719dc` after the pre-registration
`6ecdc22`). Output: `data/ledger_stage_c1_ng.json`, which `--check` reproduces byte for byte. §4 is POST HOC
(`scripts/explore_c1_selection_control.py` → `data/ledger_stage_c1_posthoc.json`) and never replaces it.
PROVISIONAL like D629, subject to the NG check of Sierra's sign after 2026-10-10.*

## 1. The verdict

| clause (out of sample, 1,684 days from 2018-06-20) | Stage A | Stage C1 | rule | result |
|---|---|---|---|---|
| 1. flow: partial correlation with the window flow | 0.137 | **0.094** (×0.68) | ≥ ×1.10 | **fails** |
| 2. price: H2's t | **5.08** ($68, 1,010 trades) | 4.47 ($119, 404 trades) | C1 ≥ A | **fails** |
| 3. midday: C1's gain at the window against its gain at midday | — | −0.044 against +0.012 | window > midday | **fails** |

**NOT RETAINED (inconclusive)** under D632 §5. C2 builds on Stage A. The known answer held: with a zero forecast,
C1's gate and τ\* equal Stage A's on all 1,936 days.

## 2. The creations are not in the window's aggressive flow

- **The forecast is what the deposit specifies,** and it is weak. Out-of-sample R² is 0.071 (BOIL) and 0.031
  (KOLD); against yesterday's flow as the forecast, both are 0.39.
  - BOIL's coefficients carry the deposit's expected signs in most windows: a1 < 0 in 85% and a2 < 0 in 93%
    (contrarian creations).
  - KOLD's are the reverse (a1 < 0 in 11%, a2 < 0 in 4%). That is the same contrarian behaviour, seen through an
    inverse fund.
- **Adding it LOWERS the flow correlation** (0.137 → 0.094), and the out-of-sample MSE rises (243.2k → 245.7k).
- **A much better forecast lowers it further.** The same-day variant (the deposit's regressors plus the return to τ,
  not the rule's C1) forecasts creations with R² 0.39 and 0.29, and it takes the flow correlation to **−0.022**.
  **The better the funds' creation trade is predicted, the worse the ledger fits the window's aggressive flow.**
- **What that says about the mechanism.** The creations are large (SD 2,162 contracts against P1's 1,814, D632 §0)
  and run against P1 (corr −0.68). Yet their futures trades do not appear as aggressive buying or selling in
  14:28–14:30. That fits:
  - the filings, which allow creation futures to be exchanged as blocks or EFPs at the settlement price (SOURCES §3);
  - D628's lead, where NG's TAS volume rises with the predicted rebalance;
  - D630's finding that only about 6–9% of the rebalance shows as aggressive window flow.
- **D629's puzzle is not explained by the creations.** Without the return control, the window flow's slope on
  C1's ledger is −0.054 (t −7.89), against −0.060 (t −7.88) on P1 alone. The negative sign stays.

## 3. The trade (out of sample), reported beside

| | Stage A | Stage C1 |
|---|---|---|
| trades | 1,010 | 404 (97% of them also Stage A's; no direction differs on a common day) |
| mean gross / net per trade | $68.08 / $42.08 | $119.06 / $93.06 |
| median; the mean trimmed 1% at both ends | $40; $65.3 | $70; $113.9 |
| Sharpe / Sortino, net | 1.21 / 1.95 | 1.34 / 2.44 |
| H2 t | 5.08 | 4.47 |

Netting the forecast creations against P1 shrinks |μ|, so C1's gate passes only the days with the largest
predicted flow. It trades fewer days at a higher mean, and the rule's t falls.

## 4. POST HOC: is C1's higher mean the creations, or only a stricter filter?

On the same out-of-sample days, **Stage A's own 404 largest-|I| trading days give $141 a trade (t 4.90), better
than C1's $119 (t 4.47).** C1's days overlap that set by 58%, at a median 71st percentile of Stage A's |I|. The
creation forecast adds nothing to the trade beyond selecting fewer, larger days, and it selects them worse than
Stage A's own |I| does. D630's dose-response (H3: $137 in the top |I| quintile) already carried this.

## 5. What this means

- **C1 is dropped. The ledger stays at Stage A on NG** (frozen, A10).
- **The funds' creations are real and large, but they are not window aggressive flow.** A stage that adds them to
  the ledger's prediction of window flow will fail on that clause, however good the forecast. Where the creations do
  land (TAS, EFP or blocks at the settlement) is the deposit's P5/P6 question (Stage D, TAS), and the TAS data is
  not on disk (G2, D619 §7).
- **C2 would add the ETF premium and the hedging split h** to this same creation term. §2 shows the term lowers the
  flow fit at every forecast quality tried, up to R² 0.39. C2's premium features forecast the same-day creations,
  much as the same-day variant does, so C2 is expected to fail the flow clause the same way. Its value, if any, would
  be through h: the share of creations that do reach the window. That is the question to put before pre-registering
  C2.
- A stricter |I| threshold on Stage A (§4, $141 at 404 trades) is a sizing and selection question for the book frame
  (H7). It is post hoc, and not a stage.
- This was the sixth test on this in-sample with this predictor (D627–D632).
