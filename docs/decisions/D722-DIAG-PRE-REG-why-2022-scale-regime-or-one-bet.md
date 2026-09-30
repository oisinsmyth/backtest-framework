# D722 DIAG PRE-REGISTRATION — why 2022? Is each line's 2022 dependence scale, count or regime, which measurable variable carries it, and are the lines one bet?

*2026-09-30.*
- *The principal: "Ok, lets take on the 'Why 2022' question", with their hypotheses: "expected supply shocks, stimuli
  checks across the world and project semi-conductor slow down into an actual increase in demand. Basically, nobody
  knew what was going to happen + more retail trading and volume ... Wasn't 2022 the ukraine war? So Oil prices also.
  On top of covid crazines." Then, on the drafted design: "Write this up, and for execution send out an opus agent
  for each part and I would like you to orchestrate".*
- *Numbered D722 after telling the other session (it holds D721 and takes nothing below 723).*
- ***Committed alone, before any of its runners exist.** Nothing here reads a price, a gamma value or any other value
  dated 2024-01-01 or later, on any root.*

**What this record is.** A diagnostic. It admits nothing, spends no programme slot and no vault look, and changes no
line. D716's frozen NQ F2 (slot 7) stays exactly as frozen. Every line studied here is already read in-sample, and was
**chosen because it leans on 2022** (§1): this is a study of that dependence, not a test of any line's edge.

## 0. Disclosures (before anything is built)

1. **A seal breach during the inventory for this record.** A Sonnet reader printed the header and the first data row
   of three fixtures: `fut_micro_flow_5m.csv.gz`, `fut_trade_counts.csv.gz` and `fut_spread_1m.csv.gz`. Those rows are
   dated **2025-09-11, inside the vault** (the tbbo year).
   - No value was used, kept or quoted.
   - **D722 reads none of those three fixtures.**
   - Recorded here because the breach happened in preparing this record.
2. **What was already known before this design:**
   - **D487:** intraday continuation on ES and NQ is a property of **2018 and 2022** (the two Fed-tightening years),
     not of 2020's crash. Its variance ratios are ES 1.319 (2018), 1.228 (2022) and 0.875 (2020).
   - **D711:** the unfiltered last half-hour (take everything, 15:30 → 16:00) nets **+$5.65 a MES trade in 2022 on ES
     and +$15.03 a MNQ trade on NQ.** Every other year runs −$4.8 to +$1.7.
   - **D688:** G_SUM (SPX GEX plus the carried ES book) was short on **63.6 % of 2022's sessions,** against 12.5–41.9 %
     in 2016–2023's other years.
   - **Each line's by-year table** is in its own record (§1).
   - **The 2022-05-16 0DTE era split** (OA-A12 = D652-A2) is a calendar date fixed before any of these results.
3. **The principal's hypotheses are dated, and several peak outside 2022:**

   | cause | when it peaked |
   |---|---|
   | stimulus checks | 2020 and early 2021 |
   | the retail surge | early 2021 |
   | COVID chaos | Feb–Apr 2020 |

   The design therefore tests every candidate variable **out of its own year**, against every year, not only against
   2022.

## 1. The objects (per-trade, regenerated in-sample; each reproduces its recorded known answer before any statistic)

| id | line | code path (imported, never edited) | unit, cost | known answer (asserted exactly) |
|---|---|---|---|---|
| **L1** | ES last-hour F2 (D705/D707) | `vault_d707_last_hour_f2.frame` + `f2`; trades `take & window`, sessions ≤ 2023-12-29 | 1 MES, $4.42 | 252 trades, mean net 13.208968…, the recorded take hash |
| **L2** | NQ F2, D716's book B | `vault_d716_nq_f2.build` + `masks` | 1 MNQ, $4.067121 | 271 trades, mean net 20.768672… (`FROZEN_vault_d716_nq_f2.json`) |
| **L3** | D699 V1, gamma-gated 15-minute log-MACD long | `stage0_d699_gamma_macd_long.panel`, `signals`, `states`, `trade_list` on short-gamma sessions | 1 MES, $4.418145 | 572 trades, total net 5,991.570959…, by-year table (`d699_gamma_macd_long.json`) |
| **L4** | HO F2 into the settlement window (D719; CLOSED) | `stage1_d719_commodity_settlement_f2.load` + `core` + D711's `f2_on` | 1 HO, $10.20 | 239 trades, mean net 109.210042… |
| **K1** | control: the admitted MACD arm (2020, not 2022, is its big year) | `run_d508_stretch_ranker.load_arm` (daily; one "trade" per traded session) | 1 MNQ, the arm's own cost | 1,876 sessions, $15,423 total (its own `REPRO_NET`) |
| **K2** | control and **base**: take-everything, 15:30 → 16:00, ES and NQ | D711's `load_root` + `clock_frame(L, "15:30")`, every in-window session | 1 MES / 1 MNQ | D711's `book_take_everything.by_year` (ES 1,360, NQ 1,389 trades) |

- **By-year only (Part A's share table; their runners read 2024-01 → 2025-02, so they are not re-run):**
  - D630 and D649 (NG);
  - D648 (CL);
  - D672 C1 (NQ compression);
  - D689 (ES full size);
  - D708;
  - D717 (ES);
  - D721's F2 books on YM and RTY.

  Each is read from its committed JSON and filtered to years ≤ 2023.
- **Every per-trade row carries:** line, root, session, side (+1 long / −1 short), entry and exit minute, hold in
  minutes, entry price, dollars per point, gross dollars, cost, net dollars.
- **Where the tables live.** They are written only to `temp/d722/` (gitignored), keyed on every input's size and
  mtime, as CLAUDE.md requires. L3 is a per-date derivative of SqueezeMetrics GEX, so it is never tracked.

## 2. Part A — is 2022 bigger dollars, more trades, or better direction?

**The exact decomposition.** For line ℓ and year y, over trades i in y:

| symbol | definition |
|---|---|
| n_y | the trade count |
| m_y | the mean of \|g_i\| (the scale) |
| e_y | Σg_i / Σ\|g_i\| (the direction efficiency, D711-A1's statistic) |
| G_y | n_y · m_y · e_y (the gross), which holds exactly |

- **The reference R** is the line's other in-sample years:
  - n_R = the mean count per other year;
  - m_R = the pooled mean \|g\| over the other years;
  - e_R = the pooled efficiency over the other years.
- **The identity:** G_2022 / G_R = (n_2022/n_R) · (m_2022/m_R) · (e_2022/e_R). Each log term's share of
  ln(G_2022/G_R) is reported, and the runner asserts the identity to 1e-9 relative.
- **Where e_R ≤ 0 or e_2022 ≤ 0,** the logs are undefined. The runner reports the three ratios and the reading follows
  the efficiency test alone.
- **The same decomposition is also run for 2018,** the other tightening year.

**The efficiency test:**
- Δe = e_2022 − e_R.
- Its SE comes from a block bootstrap over ISO weeks (trades resampled by week within each side of the comparison):
  10,000 draws, seed 722.
- The rank of e_2022 among all the line's years is reported beside it.

**Scale in volatility units:**
- u_i = g_i / (usd_pp · P_entry,i · σ20_i · √(h_i / 390)).
- σ20_i is the root's standard deviation of daily close-to-close log returns over the 20 sessions before the trade's
  session: D663's `sig20` convention, lagged one session. h_i is the hold in minutes.
- **Reported:** mean u and efficiency by year, and 2022's share of Σu against its share of Σg.

**Performance tables.** Each line's by-year table carries net and gross dollars, net and gross Sharpe **and** Sortino
(R17), the count, the median and the hit rate.

**Readings per line (declared):**

| reading | when |
|---|---|
| **REGIME** | Δe / SE ≥ 2: the direction was right more often, weighted by size, in 2022 |
| **SCALE** | the m term carries ≥ ½ of the log excess **and** Δe / SE < 2 |
| **COUNT** | the n term carries ≥ ½ of the log excess |
| **MIXED** | none of the above alone; the three shares are reported |

- REGIME can co-occur with COUNT, and both are named.
- Where the logs are undefined and Δe / SE < 2, the reading is **UNRESOLVED**.

## 3. Part B — which variable, known before the trade, carries it?

**The objects:**
- **B-base:** K2 on ES and on NQ, every session: about 1,100 non-2022 sessions per root. This is the regime itself.
- **B-lines:** L1–L4, trade by trade.

**The outcome:** u_i, the volatility-normalised gross of Part A.

**The variables** (the principal's hypothesis in brackets). Every variable is measured before the trade's entry and
lagged to the prior session unless stated.

| id | variable | definition | objects |
|---|---|---|---|
| X1 | realised vol (uncertainty, scale) | ln σ20 of the line's root | all |
| X2 | implied vs realised (uncertainty: "nobody knew") | D691's ln(IV / RV20), prior settlement (`stage0_d691_iv_size.build_iv`, cache filtered < 2024-01-01) | ES and NQ objects |
| X3 | dealer gamma | 1 if G_SUM < 0 at the prior close (D688's panel) | ES and NQ objects (L3 is gated on it: reported, not read) |
| X4 | rates shock (the Fed) | ln of the 20-session sd of daily changes in ZT's front settlement (`fut_curve_front_next`, roll days excluded) | all |
| X5 | energy shock (war, oil) | ln σ20 of CL | all |
| X6 | trend regime | the variance ratio of the root's 30-minute RTH returns over the prior 60 sessions, by D487's S1 definition (`run_d487_continuation_stage0.py`); for HO, HO's own | all |
| X7 | direction (bear market) | the root's 60-session log return to the prior settlement, times the trade's side | all |
| X8 | macro event day (Fed, CPI) | 1 if the session carries FOMC, FOMC_UNSCHEDULED, CPI or EMPSIT (`data/calendar/events.csv`); HO also EIA_WPSR | all |
| X9 | stimulus checks | 1 inside the three US Economic Impact Payment windows: 35 sessions from the first deposit date of each round | all |
| X10 | retail | ln(MES day volume / ES day volume), prior session (`fut_micro_day_volume` and `fut_index_sessions`); from 2019-05 only | ES and NQ objects |
| X11 | the chip cycle | SMH's 60-session log return minus QQQ's, prior close (`etf_wide_daily_raw`) | ES and NQ objects |
| X12 | the heating-oil curve (supply) | (HO front − next settlement) / front, prior session (`fut_curve_front_next`) | L4 |

**Caveats fixed before the run:**
- **X9's dates** (the first deposits, about 2020-04-10, 2020-12-29 and 2021-03-12) are verified from an IRS or Treasury
  source, with the URL recorded, before the runner exists. A different date is an amendment committed before the run.
- **X10 is weak by D485:** micros are not a clean retail marker. No 2022 retail series exists on disk.
- **X11:** the ETF file is not adjusted for corporate actions, so any day with \|log return\| > 0.30 is treated as a
  corporate action and its return dropped.
- **The 2022-only war window** (2022-02-24 → 2022-04-29) cannot be fitted outside 2022, so it is in Part C only.

**The method for each (object, variable) cell:**
1. **Leave one year out.** For each year Y, fit u = a + b·X by OLS on the object's other years, then predict Y's mean
   û_Y.
2. **2022 is primary.** The explained fraction is φ = (û_2022 − ū_R) / (ū_2022 − ū_R), where ū_R is the mean u over
   the non-2022 years.
3. **The slope's t** comes from the fit that excludes 2022, with SEs clustered by ISO week. A Holm adjustment runs
   across each object's variables.
4. **A joint model** combines the variables that pass individually, fitted outside 2022, and the 2022 residual excess
   is reported.
5. **Every year's out-of-year prediction against its actual is reported,** so 2018 and 2020 are visible.

**Readings per cell (declared):**

| reading | when |
|---|---|
| **EXPLAINS** | Holm-adjusted p < 0.05 on b **and** φ ≥ 0.5 |
| **PARTIAL** | Holm p < 0.05 and 0.2 ≤ φ < 0.5 |
| **NO** | otherwise |

- **UNEXPLAINED (per object):** no cell EXPLAINS, and the joint model leaves ≥ ½ of 2022's excess.
- **N/A:** an object with ū_2022 ≤ ū_R has no excess to explain.

**Power, stated now:** L1, L2 and L4 each have about 180–210 non-2022 trades, so a slope needs a large effect to reach
Holm. The base (K2) carries the power, and a NO on a line is weak evidence.

## 4. Part C — event windows

**For each of L1–L4, K1 and K2,** 2022's net is split over these windows:

| id | window |
|---|---|
| C1 | X8's macro event days (and, separately, the eight 2022 FOMC days) |
| C2 | the war's first ten weeks, 2022-02-24 → 2022-04-29 |
| C3 | before and after 2022-05-16 inside 2022 |
| C4 | HO only: X12 at or above the 90th percentile of its 2016–2021 distribution (backwardation squeezes) |

- **Test:** a window's share of 2022's net is compared with the same number of 2022 trades drawn at random, 10,000
  draws, seed 722.
- **CONCENTRATED** if the window's rank is ≥ 0.95 **and** it carries ≥ 25 % of 2022's net.
- **Reference:** the same shares for C1 in every other year.
- **2022's ten largest trades per line are named:** date, side, net, and the calendar flags that day.

## 5. Part D — one bet or several?

**Data:** daily net P&L per line on common sessions, 2018-05-14 → 2023-12-29 (HO from 2018-08-01), zero on days
without a trade.

**The measures:**

| id | measure |
|---|---|
| D1 | Pearson and Spearman ρ of daily P&L for every pair, in 2022 and in the other years; also on days both lines trade |
| D2 | 2022 top-decile overlap for every pair (each line's top 10 % of its 2022 trading days by net): overlap against the hypergeometric expectation given the lines' 2022 trade days, with its p |
| D3 | each line's 2022 daily net regressed on the same session's K2 (ES) outcome: the share of 2022's net that "last-hour continuation days" account for |
| D4 | the equal-weight index book (L1 + L2 + L3, one micro each): its 2022 share, and the ratio of the sum of the lines' variances to the book's variance, 2022 against the other years |

**Reading (declared):**
- **ONE BET** if, for the pair L1–L3 **or** the pair L1–L4, ρ_2022 ≥ 0.3 **or** the D2 overlap p < 0.01.
- **SEPARATE** otherwise.
- L1–L2 (ρ 0.87, the same trade by D711) is reported, but not read.

## 6. What each outcome means (declared now)

- **REGIME, with a variable that EXPLAINS it:**
  - The edge is a property of that state.
  - D716's vault look (2025-03 → 2026-09) is in effect a bet that the state recurs, so its recorded power is an upper
    estimate.
  - D716 is not touched.
  - A regime-conditioned variant can only be pre-registered for data no model has seen, on the principal's word.
- **SCALE:**
  - The lines were no more right in 2022; the stakes were bigger.
  - D705's gate (d) then measures scale, not dependence.
  - **The method note that follows:** score year concentration in volatility units in future gates.
- **COUNT:** the filter fires more in 2022's state. That is the same question as REGIME, one level up: what made it
  fire.
- **UNEXPLAINED:** 2022 is a one-off in-sample. The ex-2022 figures already recorded are the better guide to any
  line's size.
- **ONE BET:** the lines are not diversifying components in the state that pays them. COMPONENTS_PROP's ρ figures,
  which are full-sample body statistics, overstate the book's diversification there.

## 7. The runners' assertions (each shown to raise in its `--selftest`)

1. **The seal.** Every frame and every conditioner series asserts that no session or date ≥ 2024-01-01 survives; a
   planted 2024 row must raise.
   - Loaders that parse a file carrying later rows filter them before any computation, as D707, D711 and D716
     already do.
   - No value dated 2024 or later enters any statistic.
2. **Known answers.** §1's values are reproduced exactly before any statistic, and a perturbed trade must raise.
3. **The decomposition identity** holds to 1e-9 relative, and a broken m must raise.
4. **Lag audit.** Every variable is re-derived for a sample of sessions in a second implementation, from data strictly
   before the session, and must match. A variable shifted to same-day must raise.
5. **Leave-one-year-out:**
   - on a synthetic where X carries a planted year effect, φ is about 1;
   - on a synthetic where X is noise, φ is about 0;
   - a version that leaks the held-out year must raise.
6. **Part C's and Part D's nulls:**
   - identical series give a full overlap at p ≈ 0;
   - independent series give p roughly uniform over 200 synthetic replications;
   - a window that is the whole year gives rank 1.

**Speed.** Built as CLAUDE.md requires: the bootstraps and permutations fan out from the start, and chunk == whole is
proven bit-identical in the self-test.

## 8. Predictions (mine, before any runner exists)

| # | prediction |
|---|---|
| 1 | L1 (ES F2) and L2 (NQ F2) read **REGIME**; the m term carries under half the log excess on each |
| 2 | L3 (D699) reads **COUNT** with REGIME: the n term carries ≥ ⅓ of the log excess (short-gamma days were 64 % of 2022) |
| 3 | L4 (HO) reads **SCALE**: the m term is the largest share |
| 4 | K2 reads **REGIME** on both ES and NQ |
| 5 | X4 (rates) **EXPLAINS** K2 on at least one of ES and NQ, and has the largest φ among the passing variables there |
| 6 | X9 (stimulus) and X10 (retail) EXPLAIN nothing on any object |
| 7 | X5 (energy) EXPLAINS or is PARTIAL on L4, and is NO on every index object |
| 8 | C1 (macro days) is CONCENTRATED on at least one index line |
| 9 | Part D reads **SEPARATE**: L1–L3 ρ_2022 < 0.3 and overlap p ≥ 0.01; L1–L4 likewise |
| 10 | any variable that EXPLAINS 2022 also predicts 2018 above ū_R out of year |

## 9. Execution (the principal: "send out an opus agent for each part and I would like you to orchestrate")

**Phase 0 (two Opus agents in parallel):**
- **0a:** builds `scripts/diag_d722_lines.py`, the per-trade tables of §1 with their known answers and the seal.
- **0b:** builds `scripts/diag_d722_conditioners.py`, the per-session variable panel of §3 with the lag audit, and
  verifies X9's dates.

**Phase 1 (four Opus agents in parallel), each consuming Phase 0:**

| part | runner | output |
|---|---|---|
| **A** | `scripts/diag_d722_part_a.py` | `data/diag_d722_part_a.json` |
| **B** | `scripts/diag_d722_part_b.py` | `data/diag_d722_part_b.json` |
| **C** | `scripts/diag_d722_part_c.py` | `data/diag_d722_part_c.json` |
| **D** | `scripts/diag_d722_part_d.py` | `data/diag_d722_part_d.json` |

**The rules for the agents:**
- Agents write only their own files, never stage or commit (the index is shared with another session), never edit a
  frozen or imported runner, and read nothing dated 2024-01-01 or later.
- The committed JSONs hold aggregates only: no per-date GEX-derived series.
- Each runner runs its `--selftest` before its one `--run`.

**My role (orchestration):**
- I review each runner against this record before its run.
- I commit the runners, then the results, by explicit path.
- I verify the claims the result rests on.
- I write the RESULT.

A deviation found by an agent is recorded as an amendment committed before the affected run, or disclosed in the
RESULT if found after it.

## Amendment D722-A1 (2026-10-01), after Phase 0 was built and before any Part A–D runner exists

**Phase 0 is built:**
- `scripts/diag_d722_lines.py` and `scripts/diag_d722_conditioners.py`;
- aggregates in `data/diag_d722_lines_summary.json` and `data/diag_d722_conditioners_summary.json`.

Every §1 known answer reproduced exactly, and every self-test canary raises. I checked the tables and the panel
independently: counts, means, the seal, and net = gross − cost.

**The rulings:**

1. **K1 takes a seal-preserving path.**
   - `run_d508_stretch_ranker.load_arm` passes the whole hourly fixture, through 2026, into `D504.build` before clipping.
   - Phase 0 runs the same steps, but filters the fixture to days before 2024-01-01 as it is read, before `D504.build`.
   - `D504.build` is causal. It reproduces 1,876 sessions and $15,423.41, within $1 of `REPRO_NET`, and D504's per-year
     totals to 2.3e-13.
   - **K1's rows:** one per traded session (1,708), side from a replay of D491's `simulate`, asserted identical, with 0
     on the 200 sessions that flipped. Untraded sessions are $0 in Part D.
2. **X9's third date changes.**
   - IRS IR-2021-54 and Treasury jy0063: EIP3 payments "began processing on Friday, March 12", with deposits "as early
     as this weekend".
   - So the first deposit date is 2021-03-13, and the window starts at the first session after it, **2021-03-15.**
   - The rule (35 sessions from the first deposit) is unchanged; only the approximated date is corrected. EIP1
     (2020-04-10, first session 04-13) and EIP2 (2020-12-29) were verified as stated.
   - The record's date is kept as `X9_record`: reported, but not in the Holm family.
3. **X6 horizon.**
   - §3's 30-minute returns are X6, in the family.
   - D487's own horizon was 15 minutes. It is built as `X6_15m`: reported beside X6, **not** in the Holm family.
   - The window is the 60 most recent full sessions strictly before the session.
   - **HO's X6:** the band 09:00–14:29, 11 thirty-minute buckets. A session counts as full when all 12 anchor bars are
     present.
4. **The sig20 conventions:**
   - **ES and NQ:** D663's `root_frame` exactly (the roll-day front-to-front return included), matched to 1.8e-16.
   - **HO and CL (X5):** the same contract's daily settlement log return, which is roll-free. A front-to-front series
     would carry the roll spread: up to 10 % on HO and 27 % on CL in sig20.
   - **X4:** ZT changes across a front change are excluded, as §3 says.
5. **Disclosed, no ruling needed:**
   - **Settlement windows** skip the archive dropouts (2020-02-27 and 2020-06-30 on CL, HO and ZT).
   - **Five macro events fall on no session** and flag nothing: four Good Friday releases and the Sunday FOMC of
     2020-03-15.
   - **X10** jumps after half-day holiday sessions.
   - **X3** is defined on D688's 1,993 days, of which D699 keeps 1,989.
   - **Calendar dates beyond 2023:** D688's panel, on L3's and X3's path, reads trading-day calendar dates after 2023
     to count options' days to expiry. These are exchange dates, not market values, as in D699's own run. No price,
     settlement, GEX or option value dated 2024 or later enters.
6. **What I have seen before Part B's statistics exist:**
   - each line's by-year table (§1's records);
   - each variable's per-year mean, from checking the panel.
   - **Notable from those means:**
     - X4 (rates volatility) is highest in **2022 and 2023** (ES rows −1.91 and −1.88, against −2.49 to −3.63 in
       2016–2021).
     - X5 (CL volatility) is not elevated in 2022 (−3.61, against 2020's −3.44).
   - **X9 is zero on every 2022 session by construction** (the payment windows are 2020–21). Its fitted prediction for
     2022 is therefore the baseline, and φ reflects only the slope's sign and size. Prediction 6's X9 half is close to
     vacuous, and is scored as stated.

