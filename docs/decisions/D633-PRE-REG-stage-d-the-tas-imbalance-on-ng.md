# D633 PRE-REGISTRATION — Stage D on NG: does the TAS imbalance improve the ledger?

*Drafted 2026-09-26, on the principal's word ("Approve the $0.29, then pre-register Stage D"). It is committed
alone, before its runner exists (R8). Stage D is the deposit's (§P5, §P6, §6), under A1–A10. It is judged against
Stage A, the last retained stage: B and C1 were not retained (D631, D632). This record fixes what the deposit leaves
open and nothing else.*

## 0. Where this comes from, and what has already been seen

- **The mechanism** (deposit line 299). Clients who buy TAS leave the liquidity providers short TAS, and the
  providers must BUY futures in the window to lock in the settlement price.
  - Q5 = + TAS_imb[t, τ], the aggressor-signed TAS volume from the session open to τ (+ = clients bought TAS).
  - **The funds' own TAS use is unknown** (G10; the filings are silent, D619). So P5 and P6 cannot be separated,
    and Q5 enters whole (deposit line 314's collapse, D4). Whether part of Q5 is the funds themselves is not tested
    here.
- **The data** (commits `8de847e` and this record's inputs):
  - trade dates ≤ 2020-02-10: Databento NGT trades with the exchange's aggressor flag (bought on the principal's
    word, $0.29);
  - from 2020-02-11: Sierra Chart's NGT files. On the HO/RB siblings, Sierra's TAS sides are the exchange flag
    (r 0.9998–0.9999, sign agreement 99.8–100%).
  - The two sources agree exactly on their overlap day, 2020-02-10, on NG itself: three contracts, volume and net.
  - Outright TAS only: a spread's sign is not a single month's.
- **Why D632 points here.** The funds' creations are large and run against P1, yet they do not appear as window
  aggressive flow (D632). They are likely blocks, EFPs or TAS at the settlement. D628's NG lead (unsigned TAS
  volume rises with the predicted rebalance, t 6.9 with year effects) is the same thread.

**Read before this record, all disclosed:**
- **The predictor side, and D624–D632 in full,** including D625/D626's TAS price premium (the sibling year; D626
  unread until 2026-10-10) and D628's unsigned TAS volume.
- **The TAS imbalance panel** (`build_tas_imbalance_panel.py`, Stage D's own input): its known answer, and its scale
  in POWER:
  - SD 2,475 contracts at τ\*, against P1's 1,692;
  - corr(P1, TAS_imb) −0.17;
  - TAS traded on 99.9% of days.
- No window flow or price was read for this record beyond D627–D632's published results.
- **This is the seventh test on this in-sample with this predictor** (D627–D633).

## 1. Sample

- NG, the 1,936 days with a defined τ\*, 2017-06-20 → 2025-02-28.
- **Stage D has no fitted parameter** (deposit §6), so every day is out of sample. It is scored on all of them. The
  only estimated quantity, Q5's variance (§2), uses prior days only.
- **Inputs:**
  - the P1 panel;
  - `data/ledger_tas_imbalance_daily.csv.gz`;
  - D629's signed window panel (the window and midday flows);
  - the calendar flags;
  - D630's minute bars.

## 2. The Stage D ledger at each τ ∈ {13:50, 14:00, 14:10} (and 11:30 for the midday control)

    μ_D(τ) = P1(τ) + Q5(τ),       Q5(τ) = Σ_{held months} TAS_imb(τ)           (contracts: one TAS = one futures)
    σ²_D(τ) = σ_Q(τ)² + Var_{t−20..t−1}[ Σ_{held} (TAS_imb(14:30) − TAS_imb(τ)) ]

- TAS_imb(τ) is the outright TAS net from 18:00 ET the evening before to τ, in the held months. A held month with
  no TAS trade traded 0.
- **The variance term** is the unseen part of the day's TAS imbalance, from τ to W_end: its sample variance over
  the 20 prior days, summed over the held months. Nothing from day t is used.
- With Q5 ≡ 0 and its variance 0, the ledger is Stage A exactly: the known answer (§7).

## 3. Stage D's own trades

§7.2's gate on D's quantities:
- |I| = 0.7 σ_d √(|μ_D| / V_d) P_held ≥ 3 × RT_cost, and SNR = |μ_D| / σ_D ≥ 1.5;
- τ\*_D is the earliest pass, else 14:10;
- the direction is sign(μ_D), in `traded_ym` at τ\*_D;
- the fill and exit are D630's.

## 4. The retention rule, on all 1,936 days

Stage D is **RETAINED** if:
1. **flow:** the partial correlation of μ_D(τ\*_D) with the window flow S_win, net of [1, r to 14:28, flags], is
   ≥ 1.10 × Stage A's, with Stage A's > 0 (deposit line 417; A8's reading);
2. **price:** H2's t over D's traded days is not below Stage A's H2 t (D630: 5.01);
3. **the midday control (D631's lesson, as in D632):** D's gain at the window, ρ_D − ρ_A, exceeds its gain at
   midday. The midday gain uses the ledger at 11:30 (P1 + TAS_imb to 11:30) against the 11:50–12:20 flow, net of
   [1, r to 11:30, flags], on days with a clean 11:30 row. It separates the providers' settlement hedge from TAS
   imbalance simply tracking the day's order flow.

## 5. The verdict

| outcome | condition | consequence |
|---|---|---|
| **RETAINED** | 1, 2 and 3 | D joins the ledger. It is frozen (A10), and later stages build on A + D |
| **UNRESOLVED (midday)** | 1 and 2, not 3 | the TAS gain is not specific to the settlement. Written up and put to the principal |
| **NOT RETAINED** | 1 or 2 fails | later stages build on Stage A. At the plausible effect Stage D is individually testable (§8), so a miss there is evidence against, with the band reported |
| **VOID** | the NG check of Sierra's futures sign after 2026-10-10 gives r < 0.8 | S_win is Sierra's futures flow; the verdict stands as recorded but may not be used. TAS_imb itself does not depend on that check |

## 6. Reported beside, never gating

- **TAS_imb on its own:** its partial correlation with S_win, the controls as clause 1. Also its slope in
  contracts of window flow per contract of TAS imbalance (γ̂), with its HC1 and Newey-West t.
- **The mechanism diagnostic** (NOT tradable: it uses TAS to 14:30): the same with TAS_imb to 14:30.
- **By source:** Databento's era (to 2020-02-10) and Sierra's (from 2020-02-11), clause 1's two correlations each.
  The stitch must not carry the result.
- The fixed-14:10 variant. D629's literal regression (no return control) with μ_D. The sign agreement of S_win and
  TAS_imb.
- **H2** on all days, CLAUDE.md's four groups: gross and net, Sharpe and Sortino, the distribution with the trimmed
  means, and the traded-day overlap. For D beside Stage A.
- **The error budget:** the MSE of S_win on each stage's predictor.

## 7. The runner and its assertions

- **File:** `scripts/run_stage_d_ng.py`, with `--selftest`, `--run` (refuses a second run) and `--check`.
  **Output:** `data/ledger_stage_d_ng.json`, with a `REQUIRED_OUTPUTS` guard.
- **Known answer (raises):** with Q5 ≡ 0 and its variance 0, D's gate equals the panel's at every τ and τ\*_D equals
  τ\*_A, exactly, on all 1,936 days.
- **Lag audit (raises):**
  - the spans are nested: cumulative TAS volume to 13:50 ≤ to 14:00 ≤ to 14:10 ≤ to 14:30, on every row;
  - Q5's variance uses trade dates strictly before t;
  - D627's `audit_flow`.
- **Sign audit:** clients buying TAS (+ TAS_imb) raises μ_D; D630's money audit.
- **Source audit:** no (trade date, month) comes from both sources.
- **Selftest** (no window flow or price):
  - a synthetic world where the window flow carries a share of the TAS imbalance must be RETAINED;
  - one where it tracks P1 alone must not be;
  - each audit RAISES on a deliberate break.
- `-W error::RuntimeWarning`.

## 8. POWER (`data/ledger_power_stage_d.json`)

The window flow = 0.061 × P1 + γ × TAS_imb + pre-sample noise; the midday flow is noise.

| γ (window aggressive contracts per TAS contract) | 0 (the null) | 0.03 | 0.061 (P1's own share, D629) | 0.12 | 0.25 |
|---|---|---|---|---|---|
| retained on clauses 1 and 3 | **3.5%** | 64.5% | **97%** | 92.5% | 33% |
| the median ratio | 0.33 | 1.46 | 3.09 | 7.82 | −19.7 |

- **The size is sound (3.5%).** Power at P1's own share is 0.97: individually testable.
- **The ratio rule breaks at very large γ.** When the TAS term dominates, Stage A's partial correlation turns
  negative (corr(P1, TAS_imb) = −0.17) and clause 1's "Stage A > 0" fails. Stage A's real partial correlation is
  +0.14 (D629, D631), which rules that world out, but the flaw is recorded.
- Clause 2 is not simulated.

## 9. What this does not touch

- No vault data. The vault's NG TAS files are on disk and unread (A10).
- No CL.
- No price move or window flow is read before the runner's one run.
- **Deviations** are listed in the output and never replace a verdict.
