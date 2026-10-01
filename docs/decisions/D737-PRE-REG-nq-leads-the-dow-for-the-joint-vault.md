# D737 PRE-REGISTRATION — NQ's lead over the Dow (D735's YM k1.0 1σ_rem) for the joint vault run

*2026-10-01.*
- *The principal:*
  - *"I choose YM 1.0, it look really good" (recorded in D735 §6 before any 2024+ read);*
  - *then "Yes write it into slot 110 and freeze". This is read as programme slot 10, the slot this session had named.
    §6 says where the registry puts it.*
- *Numbered D737: the other session claimed D736 first and was told.*
- ***Committed alone, before its runner exists.** Nothing here reads a price dated 2024-01-01 or later on any root.*

## 1. The line, unchanged from D735

| item | rule (D735 §2–§3, the cell YM k1.0 1σ_rem) |
|---|---|
| objects | x_NQ,m and x_YM,m = (the close of bar m − 1 − the 09:30 open) / σ_oc, each root's own σ_oc (the RMS of the prior 20 sessions' open-to-close moves; D727's panel rules: ≥ 380 bars, roll days excluded). YM is joined to NQ's days by date |
| spread | s_m = x_NQ,m − x_YM,m; σ_s = the RMS of the prior 20 NQ sessions' s_390 (≥ 15 present); z_s,m = s_m / (σ_s √(m/390)) |
| trigger | the first minute m0 in 10:00 → 14:30 with \|z_s,m0\| ≥ **1.0**. One trade a day |
| side | D = sign(s_m0), whatever NQ's own direction |
| entry | the open of NQ's bar m0, **one MNQ** |
| stop | entry − D · σ_NQ · √((390 − m0)/390), checked from bar m0; an open through it fills at the open; one tick of slippage |
| exit | the stop or the 15:59 close |
| cost | D711's `cost_line("NQ")`, **$4.07** a round trip |

**The code is D735's own functions, imported, never re-implemented:**
- from `stage0_d735_nq_breaks_from_the_market.py`: `minute_x`, `align_rows`, `spread`, `trigger`, `e1_tables`, `g_at`
  and `timing_null`;
- from D727: `panel_from_raw`;
- from D733: `panels`;
- from D733: `nw_t`, Newey–West with 5 lags.

**The in-sample known answer (2016-01-04 → 2023-12-29):** 1,699 trades, mean net **+$14.869…** (D735's JSON, to
1e-9). It is reproduced exactly before anything else in every mode.

**The selection, disclosed.** This cell was chosen after D735 by the principal, from 20 cells. In-sample, its C2a
mean (+$14.87) cleared the family-wise p95 ($14.41), and YM was the only leg whose mechanism read (Holm 0.050). D735's
pre-registered reading was DRIFT ONLY: every cell failed the per-|x| bin leg. **A vault pass therefore confirms a
post-hoc choice.** It is evidence for this one cell, not for D735's family.

## 2. The vault window and its data

- **Scored sessions:** NQ day sessions **2024-01-01 → 2026-09-18**. That is NQ's unseen slice, the same one D716 (slot
  7) reads for NQ's last hour.
  - **The overlap is stated:** D716 scores 15:00–16:00 and this line holds from about 10:00 to the close. The two share
    sessions and the last hour.
  - **Neither changes the other's rule.** Their vault results are reported side by side, with the daily ρ between them.
- **The load:** the vault mode reads `fut_NQ_rth_1m` and `fut_YM_rth_1m` from **2023-09-01** (so σ_oc and σ_s have
  their prior 20 sessions) through 2026-09-18, and **nothing later**.
  - It refuses unless both fixtures hold a session on 2026-09-18. `--accept-end DATE` lowers that, as the principal's
    choice, and is recorded in the output.
  - The fixtures are rebuilt by D462 in the joint run (JOINT_RUN_CHECKLIST §2.2).
- **The overlap re-proof (right quantity):**
  - The vault load's trades on 2023-11-01 → 2023-12-29 must equal the in-sample run's on those days exactly: same
    days, m0, sides and gross.
  - The in-sample known answer is then re-proved from the same rebuilt fixtures, with the seal at 2023-12-29.
  - If either fails, nothing is scored.
- **Seals in every other mode:** the self-test is synthetic only. `--rehearse`, `--power` and `--freeze` read through
  D727's `load_root`, which filters to 2023-12-29, and raise on any later session.

## 3. The pass rule (fixed now, whatever the power says)

On the vault trades (sessions 2024-01-01 → 2026-09-18):

| gate | condition |
|---|---|
| G0 | ≥ 100 trades. Otherwise **UNRESOLVED** (expected: about 560) |
| G1 | mean net > 0 **and** one-sided Newey–West (5 lags, trade order) t ≥ **1.645** |
| G2 | mean net above the **p95 of the timing null C2a**: D735 §5's null, run on the vault sessions only. Each trade's entry minute and stop rule are moved to vault day d + j, for j = 20 … n_v − 20 (enumerated), and entered in that day's sign(x_NQ,m0). This keeps the vault's own drift and asks that the entry beat it |

- **PASS = G0 ∧ G1 ∧ G2.**
- **FAIL:** mean net ≤ 0.
- **UNRESOLVED:** otherwise. The mean is positive, but G1 or G2 fails.
- **A FAIL or UNRESOLVED is not re-tuned:** k, the stop, the clock window and the leg are not changed after the look.
- **What a PASS means, written now:** the cell is a confirmed candidate component on one look of about 2¾ years.
  - It goes to the components ledger's standard, and to hurdle P with the assembled book, through `BOOK_PROP.md`'s
    written process.
  - **A PASS admits nothing by itself.**

## 4. Reported beside, never gating

**The four groups:**
- net and gross, Sharpe and Sortino (daily, 0 on days without a trade);
- max drawdown and P3a at $50k and $150k;
- the trade distribution with the symmetric 1% trims;
- by year: 2024, 2025 and 2026 to 09-18;
- D729's year concentration in $ and in volatility units.

**Further lines:**
- t against 1.2816 (the programme's usual vault bar, D716/D680) and 2.576, for comparison only;
- the efficiency Σg/Σ|g| against C2a's p95;
- C2b (the moved schedule in that day's sign(s));
- the counter subset and its paired C1;
- the mirror;
- the matched-row gain, with the day-block bootstrap SE (2,000 draws, seed 737);
- the entry-hour table;
- the stopped share;
- MFE/MAE at +15 / +30 / +60 minutes and the close.

**The mechanism and ρ:**
- **the mechanism on the vault sessions,** D735 §4's δ for YM, with its rolled-e null over the vault days;
- **ρ with D716's vault NQ F2,** daily: read from D716's vault output if it exists when this runs, else named missing.

## 5. Power (computed in-sample before the freeze; it changes nothing in §3)

The runner's `--power` mode writes `data/vault_d737_power.json`. It is in-sample only.
- **G1 power:** resample the in-sample trades in 20-trade blocks to the expected vault count, with the edge shifted to
  100 / 75 / 50 / 25 / 0% of in-sample (in σ_oc units). Each is priced at two σ levels: the in-sample mean σ_oc and
  2023's mean σ_oc. 4,000 draws, seed 737.
- **G1 ∧ G2 at the observed edge:** run the full gate (G0–G2, C2a enumerated inside the window) on moving windows of
  the in-sample sessions as long as the vault (step 20 sessions). The pass rate is reported with the number of
  independent windows (about 3).

**Already estimated in chat** (scratch, in-sample, at 2023's σ): G1 alone passes about 68% at 100% of the edge, 41% at
75%, 20% at 50% and 1% at 0%.

## 6. Programme slot, the freeze, the order

- **Programme registration:** one family, "NQ leads the Dow (D735 YM k1.0)", α 0.005, registered at the freeze with
  `Registry.register`.
  - **The registry gives the lowest free slot.** Slots 1 and 2 were released on 2026-09-30 and 10 is free, so it lands
    in **slot 1**.
  - The α and the rule are the same in any slot. The principal's "slot 10" is honoured as one programme slot, and the
    number is the registry's.
- **The freeze:** `data/FROZEN_vault_d737_nq_leads_the_dow.json`, written once by `--freeze` after `--rehearse` and
  `--power`. It holds LF-pinned sha256 values of:
  - the runner;
  - this record, D735's pre-registration and result;
  - every repo module the runner imports (discovered statically and recursively, as D723's freeze does; the modules
    actually imported must be a subset);
  - the parameters, the known answer, the rehearsal's and power files' bytes, the slot and the principal's words.
- **`--vault --principals-word "..."` (the joint run only), in order:**
  1. verify the freeze (any drift refuses);
  2. refuse a second opening (the output exists);
  3. re-prove the in-sample known answer;
  4. load to 2026-09-18 and run the overlap re-proof;
  5. score;
  6. write `data/vault_d737_nq_leads_the_dow.json`.
- **When it runs:** after the D462 rebuild, which comes after D626's 10-10 read (JOINT_RUN_CHECKLIST, the principal's
  "Yes to all 3"). Its position among the joint run's lines does not matter, because it reads only NQ and YM bars.
