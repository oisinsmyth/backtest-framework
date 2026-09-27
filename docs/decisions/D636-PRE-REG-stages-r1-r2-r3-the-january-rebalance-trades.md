# D636 PRE-REGISTRATION — Stages R1, R2 and R3 of the index-reweight model: do the January rebalance flows move prices on the execution days (R1), reverse afterwards (R2), or get priced in beforehand (R3)?

*Drafted 2026-09-27 on the principal's word ("pre-register R1, R2 and R3"). It is committed alone, before any R-stage
runner or POWER step exists (R8). The spec is the deposit `INDEX_REWEIGHT_FLOW_PREREG.md` v1.3 §6–§10 under
amendments IR-A1–IR-A14. It builds on D634 (Gate R0, RESOLVED on its re-run: the tracker and ΔN) and D635 (Gate C0,
pre-registered, not yet run). One record, three stages, three verdicts; Holm applies within each stage (deposit §9).
These rules and their code are frozen for the January 2027 forward event (IR-A10).*

## 0. Where this comes from, and what has already been seen

- **The deposit's three stages:**
  - **R1, execution days:** intraday, into the settlement window on the January hedge days.
  - **R2, reversal:** the opposite way, 1, 3 and 5 days after the last hedge day.
  - **R3, pre-positioning:** from the announcement and from December, in the forecast direction.
- **The adoption rule (§8B.2):** a stage is traded only if its pooled test passes AND the yearly sign test passes
  (and, for R1, the calibration check). A pooled pass without the sign test is written up as "driven by a few years".
- **R-D5:** if Gate C0 fails, R1 runs descriptively only, and no R1 trading hypothesis can pass.
- **Seen before this record, all disclosed:**
  - D634 in full, including every year's ΔN for the 15 CME components (for example 2020 NG +92,665 contracts), which
    is R1–R3's predictor;
  - D635's design and POWER, and the non-hedge-day flow noise;
  - the settlement-window VWAP measurement, which reproduces settlements and reads no moves.
- **No January execution-day, reversal or pre-positioning return has been computed or read.** The R0
  published-return check read fund NAVs on all days, January included, as NAV-against-index errors, never as a
  return set against ΔN.
- **The in-sample events are 10** (January 2016–2025). 2026 is in the vault (IR-A1), and 2027 is forward.

## 1. The predicted January flow

- **BCOM:** ΔN_B,i(y), in contracts, from `gate_r0_rerun.json` (D634 §1.6). It is known exactly at det(y) = BD4 of
  January.
- **GSCI, per $1bn of GSCI tracking assets:**
  - ΔN_G,i(y) = 1e9 · (w_new,i − w_old,i) / (P_i · mult_i).
  - Here w_k,i = CPW_k,i · conv_i · P_i / Σ_j CPW_k,j · conv_j · P_j, evaluated at the settlements of GSCI's
    reference day. That is **BD4 of January on the CME calendar**: the day before its roll starts (the S&P 2018
    methodology gives "the last business day" before the period, SOURCES_GSCI_CFTC §2.2).
  - k is year y−1 (old) or year y (new). CPW and conv come from SOURCES_GSCI_CFTC §2.4 and Table 4.
  - **All 24 GSCI components are priced** at the reference day. The three not on disk are **inputs pending the
    principal's approval:** feeder cattle (FC) and cocoa (CC, before 2026) from Sierra Chart daily settlements, and
    LME copper from Westmetall.
  - **The fallback, if they are not approved:** the weights are computed over the 21 priced components. The missing
    three enter as a fixed share equal to their published RPDW(y−1), and their share is reported as a band.
- **The total predicted flow on execution day d (hedge BD5–BD9),** in contracts:

      Q_i,d = 0.2 · (κ̂_B · ΔN_B,i + κ̂_G · ΔN_G,i)

  κ̂ is C0's, carried forward. If C0 COMBINED the two κ, the GSCI term is κ̂_C · AUM_B(y) · ΔN_G,i. **If C0 has not
  run, no R-stage runs** (R-D5).
- **The forecast before det** (for R3): the same formulas at day t's drifted weights (the D634 re-run tracker) and
  day t's settlements, with the year-y targets once announced (§0.6: only prices known at t). GSCI's term uses the
  published CPW(y) once announced, else it is 0.

## 2. The traded universe and the costs

- **R1–R3 trade the 12 CME components with no contract roll in January:** NG, CL, HO, RB, ZC, ZS, ZM, ZL, ZW, KE, HG
  and SI (IR-A3). Their January flow is the reweight alone.
  - Live cattle, lean hogs and gold roll in January, so their flow there mixes the roll with the reweight. They are
    reported beside and never gate.
- **The contract:** the January lead (Table 9a).
- **A (root, date) with no served settlement window is excluded** (IR-A9). This excludes KE in January 2016.
- **The cost (R-Q7 answered, the ledger's standard):** a round trip on one full-size contract costs $16 plus one
  tick (Future.from_specs; KE $12.50 a tick). Tests are scored in dollars per full-size contract.
- **The component line:** reported at the minimum tradable size, the micro where one exists (MCL, MNG, MGC, SIL,
  MHG, and the micro grains from their launch), per CLAUDE.md.

## 3. The two constructions (deposit §7)

- **A, outright.**
  - Commodity i is traded on day d when |I_i,d| ≥ 3 · RT_cost_i AND SNR ≥ 1.5, in the direction sign(Q_i,d).
  - I_i,d = 0.7 · σ_d · √(|Q_i,d| / V_d) · P · mult, with σ_d the 20-day trailing SD of daily settlement returns and
    V_d the 20-day trailing mean window volume (`window_flow_daily`), both from prior days.
  - **SNR = |κ̂| / √(se(κ̂)² + (κ̂ · h_y)²).** h_y is IR-A5's AUM half-band relative to the point. At det the flow
    is known up to these two scales, so the SNR is common to every commodity in a year: it passes a whole year or
    none of it. That is this record's reading of the deposit's "flow forecast's SNR".
- **B, market-neutral basket.**
  - Each day, the 12 are ranked by signed predicted flow share Q_i,d / V_i,d. The basket is long the top k = 3
    (predicted buys, Q > 0) and short the bottom k = 3 (predicted sells, Q < 0).
  - A day with fewer than 3 names on a side trades the names it has, never a name against its predicted sign.
  - **Weights:** inverse 20-day volatility, scaled so the long and short books have equal dollar risk (to 1%, the
    deposit's unit test 10).
  - **R1 timing:** every leg enters at the common time: 10 minutes before the EARLIEST settlement window among the
    chosen legs. Each leg exits at its own W_end.
  - The basket's daily beta to the equal-weighted return of the 12 is reported as a neutrality diagnostic.

## 4. Stage R1: the execution days

- **Days:** January BD5–BD9, 2016–2025 (the hedge days, IR-A3).
- **Entry (the ledger's fill convention, D630):**
  - t0 = W_start − 10 min is the primary. **W_start − 20 min is reported beside, and never enters Holm.**
  - The fill is the close of bar t0+1: the last trade strictly before t0 + 2 min, from the Sierra 1-tick file.
  - The exit is the last trade strictly before W_end.
- **The signal frame (gating):** the signed move in dollars per contract, (exit − fill) · sign(Q) · mult. For B,
  the weighted sum of its legs.
- **The book frame (reported):** the D630 book frame. A stop at 1.0 · |I| adverse, and an early profit if the move
  reaches |I| before W_start.
- **H-R1** (per construction):
  - the pooled mean signed gross move ≥ 1 · cost; AND
  - a **wild cluster bootstrap by year,** one-sided p < 0.05, **Holm-adjusted across A and B.** It uses Webb
    six-point weights, 9,999 draws, seed 636, and the restricted null (the mean is 0). The statistic is the mean's t
    with SE clustered by year.
- **The yearly sign test:** each year, the Spearman correlation across the traded commodities between the signed
  predicted flow share (Σ_d Q_i,d / V_i,d) and the raw price move summed over the five days. PASS when ≥ 9 of 10
  years are positive (binomial one-sided p ≈ 0.011). A year with fewer than 4 traded commodities casts no vote,
  and the bar is then recomputed for the votes cast at p < 0.05.
- **The calibration check:** the pooled ratio of realised to predicted move, Σ realised / Σ |I| over A's trades.
  Its 90% CI is a bootstrap over years (resampling years, 9,999 draws). PASS when the CI overlaps [0.5, 2].
- **Adoption of R1** requires H-R1 AND the sign test AND calibration, with C0 PASSED.

## 5. Stage R2: the reversal

- **Entry** at the settlement of BD9 (the last hedge day). The position is OPPOSITE to each commodity's total
  predicted flow, Σ_d Q_i,d.
- **Exit** at the settlement h = 1, 3 and 5 trading days later.
- **The move:** −sign(ΣQ) · (settle_{BD9+h} − settle_{BD9}) · mult, per contract.
  - If the January lead's own roll falls inside the hold, the move is measured on the sub-index (D634 §1.3),
    converted to dollars at the entry price.
- **A:** each commodity whose total-flow |I| ≥ 3 · RT_cost and SNR ≥ 1.5. **B:** the basket of §3 on the total flow
  share, entered at the BD9 settlement.
- **H-R2:** at least one of the 6 tests (3 holds × 2 constructions) has a mean ≥ 1 · cost and a Holm-adjusted wild
  cluster bootstrap p < 0.05.
- **Adoption of R2** requires H-R2 AND the yearly sign test, on the surviving hold, with the realised move reversed.
  **The calibration check is defined by the deposit for execution-day moves only.** R2's realised reversal over R1's
  predicted impact is reported, not gated.

## 6. Stage R3: pre-positioning

- **(a) Descriptive.** For each commodity, the residual return is its sub-index return minus the equal-weighted
  mean of the 12, over three periods:
  1. the announcement → 1 December;
  2. 1 December → 31 December;
  3. 1 January → the day before execution day 1 (det).
  It is correlated across commodities with the forecast flow share at each period's start, by year.
- **(b) Trading.**
  - Enter at the settlement of the first business day of December, in the direction of the forecast flow on that
    day (weights and settlements to the prior business day; §1).
  - Exit at the settlement of det(y), the day before execution day 1.
  - The move is the sub-index return times the entry price times mult, per contract.
  - **A** uses the forecast total flow's |I| ≥ 3 · RT_cost and SNR. **B** is the §3 basket on the forecast flow
    share.
- **H-R3(b):** the mean ≥ 1 · cost and a Holm-adjusted (A, B) wild cluster bootstrap p < 0.05.
- **Adoption of R3** requires H-R3(b) AND the yearly sign test on (b). Calibration is not gated, as for R2.
- **Its announcement dates** are the sourced ones (`weights/<year>.csv`). A year whose announcement falls after
  1 December has an empty period 1, and that is recorded.

## 7. Placebos, controls and reported beside

- **The date placebo:** R1's computations on January BD12–BD16, with each day k carrying hedge day k's Q. **It must
  show no effect:** a Holm-adjusted p < 0.05 with the gate's sign kills R1 (deposit §14).
- **The label shuffle:** within each year, the forecast flows are permuted across the 12 commodities, 1,000 times
  (seed 636). R1's and R3's statistics are recomputed each time. **The observed statistic must exceed the 95th
  percentile**, or the stage is killed (deposit §14).
  - The statistic is the construction's pooled mean signed move, with each permutation's own gate and directions.
  - The p95's bootstrap SE is carried, and a margin within 2 SE is recorded as UNRESOLVED (CLAUDE.md, D373).
- **Headline-only:** every test is repeated with ΔN_headline = AUM · (target(y) − target(y−1)) / (P · mult) in place
  of the drift-based ΔN. If headline-only does as well, that is recorded (§14: the drift insight adds nothing).
- **Dose-response:** the Spearman correlation between |Q| / V and the signed move, per stage.
- **Robustness (reported, deposit §8):**
  - the stress fill (worst close of bars t0+1…t0+5), and 2× cost;
  - without the grains (the least liquid group);
  - without the GSCI term, and k = 2 and 4 for B;
  - t0 = W_start − 20;
  - the median-year result beside the pooled mean (§10);
  - LE, HE and GC with their roll flow added, beside.
- **H-R4 (depth-based impact) is not run.** Order-book depth before 2025 is not on disk (the ledger's gap G5). This
  is recorded, not substituted.
- **Every trading result carries CLAUDE.md's four groups:**
  1. net and gross, with Sharpe and Sortino;
  2. the trade distribution, with the symmetric trims;
  3. the dependence on years and names;
  4. the nulls as distributions.
- **Every configuration is logged in `results/index_reweight/trials.csv`,** and the final Sharpe carries a DSR over
  the trial count (§9).

## 8. POWER (before the runner; `data/index_reweight/power_r.json`)

- **Per stage and construction,** the SE and MDE are computed from the real design (the traded set and sizes). The
  noise is the stage's own statistic on PLACEBO days: January BD12–BD16 for R1, the same holds from BD16 for R2, and
  the equivalent November windows for R3.
- **n_eff** = n / (1 + (m − 1) · ρ), with ρ the within-year correlation measured on those placebo days (§8B.1).
- **The plausible effect,** stated here before POWER runs:
  - R1: the realised move is half of the predicted |I| (the calibration's lower bound);
  - R2: a reversal of half that;
  - R3: zero, since there is no published estimate to anchor it.
- **A stage whose power is below 0.8 at its plausible effect is UNDERPOWERED.** A miss is then written as
  inconclusive, with the excluded effect size stated, as in the ledger's §9A.2.

## 9. The runners and their assertions

- **Files:** `scripts/run_stage_r1.py`, `run_stage_r2.py` and `run_stage_r3.py` (they may share `r_design.py`). Each
  has `--selftest`, `--run` (refuses a second run) and `--check`. Output goes to
  `data/index_reweight/stage_r{1,2,3}.json`, each with a `REQUIRED_OUTPUTS` guard.
- **--run REFUSES** until `gate_c0.json` exists. If C0 FAILED, R1's output is labelled descriptive and its verdict
  can only be "descriptive" (R-D5).
- **Lag audit (raises):**
  - Q at execution day d uses ΔN from det(y) settlements, and V and σ from days before d;
  - R3's forecast on day t uses settlements to t−1;
  - a second implementation rebuilds A's traded set from the stored gate inputs without calling the gate function,
    and must agree.
- **Sign audit, in money:** a predicted buy (Q > 0) whose price rises books +; R2 books the reverse; B's long and
  short books have equal risk to 1%.
- **Right-quantity:** R1's graded moves are not the placebo's, and not the W_start − 20 variant's.
- **Deposit unit tests (§13):**
  - 10 and 11: B's risk parity, and its legs exit at their own W_end;
  - 21–25: the design effect, the sign-test bars (9 of 10 gives p ≈ 0.011 and passes; 8 of 10 gives p ≈ 0.055 and
    fails), the Spearman on traded names only, the calibration CI and the three-part adoption;
  - 26–28: the 11-vote bars (9 of 11 passes at p ≈ 0.033; 8 of 11 fails), the 2027 consistency test on 2016–2025
    intervals only, and Track 3 never counting as evidence.
- **The selftest:** each audit RAISES on a deliberate break; a synthetic world carrying the effect passes and a null
  world fails. `-W error::RuntimeWarning`. Reads are cut at 2025-03-01 (IR-A1).

## 10. What this does not touch

- **No vault data:** no January 2026 event, and no 2025-03 → 2026-09 reads.
- **No 2027 publication before the freeze** (IR-A10).
- **No January return is read before each stage's one run,** except POWER's placebo days.
- **The 2027 forward event:** at the freeze these rules and runners are hashed into `FROZEN_2027.json`. Its
  consistency test (§11 v1.3) uses the 2016–2025 intervals only. January 2026 (scored at the joint vault run) and
  January 2027 (forward) add the 11th and 12th sign-test votes, in whichever order they are scored: ≥ 9 of 11, then
  ≥ 10 of 12 (IR-A1).
- **Deviations** are listed in each output and never replace a verdict.

## 11. Settled before any runner (2026-09-27, after this record's commit `1315ecf`)

*These were written while building the shared design (`scripts/r_design.py`) and the POWER step, before any R-stage
runner existed and before any execution-day, reversal or December return was read.*

- **The downloads** (the principal: "Approve the downloads"):
  - feeder cattle (`GFH16`–`GFH25`, CME) and cocoa (`CCH16`–`CCH25`, ICE US) from Sierra Chart daily settlements;
  - LME copper from Westmetall, into its own file, so the BCOM LME file Gate R0 hashed stays byte-identical.
  - **Also fetched:** gasoil's February contract (`GASG16`–`GASG25`). GSCI holds it in January, and BCOM's list held
    only March. It is the same kind of Sierra ICE daily settlement the principal approved for ICE (IR-A13).
- **GSCI's dollar weights are computed with prices in US dollars.** The components the exchanges quote in cents
  (W, KW, C, S, KC, SB, CT, LH, LC, FC) are divided by 100. S&P's printed ACRP for them is in cents under a "$"
  header, and only in dollars do they reproduce the RPDW.
  - **The known answer (raises):** each year's reference-day weights correlate with S&P's published RPDW at 0.985 to
    0.999 (2016–2025), against a bar of 0.9.
- **GSCI's reference day is BD4 of January on NG's settlement calendar**, the CME calendar of §1. GSCI's reweight
  flow is priced on the contract receiving it: the roll-in contract where GSCI rolls in January (energy), else the
  held one.
- **GSCI's January ROLL flow** (energy: it rolls G→H during BD5–BD9, and H is BCOM's lead) is predictable index flow
  on R1's traded contract. It is **not** in §1's Q, which is the deposit's reweight-only formula. It is reported
  beside, as R1 with Q plus C0's κ̂_G times GSCI's roll-in flow.
- **R3's November placebo** (§8) is 1 November BD1 → 1 December BD1, settlement to settlement. It ends where R3's own
  entry begins.
- **POWER only** (declared in `power_r_stages.py`; not the runners):
  - κ is assumed on a grid, since C0 has not run;
  - the SNR gate is taken as passed;
  - B's legs each use their own t0;
  - R3's forecast is BCOM-only.
