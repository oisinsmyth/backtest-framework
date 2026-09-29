# D673 — PRE-REGISTRATION: the compression break on YM and RTY, the roots that have never been read for it

*2026-09-29.*
- *The principal: "Yeah write up the pre-reg for the YM/RTY".*
- *The rule was frozen by D672's development run on ES and NQ (`31273d90` design, `c5f9d028` result):*
  - *NQ C1 made +6.93 net (t 2.40), 55 trades a year, daily Sharpe 0.97, positive in 7 of 7 full years;*
  - *ES C1 made +0.55, with its busiest third at −5.66.*
- ***Committed alone, before any YM or RTY outcome is read,** before this record's runner exists, and before D668's
  YM/RTY evidence run.*
  - *D668 will read the same roots' unconditional plain-break outcome. Nothing here is chosen after it.*

## 1. Why YM and RTY

**The compression break was found on NQ, after the fact:**
- D671's diagnostic ran 127 cuts; D672 confirmed its internal consistency on the same sample.
- ES and NQ are therefore spent for it.

**YM and RTY:**
- have never been run through the plain break, D671 or D672;
- carry the same construction at their own ticks and micro costs (D668-A1).

(The other session's D670 plans YM/RTY for a different rule, the MACD mechanism. That does not spend them for this one,
and its ρ with this line is named as missing.)

**The root stories predict opposite results, and this record writes them down now:**
- **RTY** re-prices at the cash open, as NQ does. Small caps, a thin overnight market, its own leveraged ETFs
  (TNA/TZA). Prediction: the compression break carries.
- **YM** is price-weighted over 30 names, with ES-like participants, and priced overnight. Prediction: no carry. At
  most, ES's pattern: avoiding the busy days, with nothing found on the quiet ones.

## 2. The rule (D672 §1, unchanged; nothing fitted)

1. **The break:**
   - D666's plain break: stops at yesterday's RTH high + 0.25 A and low − 0.25 A, live from 09:30, first fill of the
     day, at the stop (or the open through it) + one tick of the root's own size (YM 1.0, RTY 0.1). No entry after
     15:29.
   - A = D644's `atr20`.
   - **E4:** the initial stop at yesterday's level, then a 0.25 A trail from the best price; otherwise flat at 15:59.
2. **The compression score, known by 09:29:**
   - p_rv = the walk-forward percentile of rv5 (the mean RTH range/A over the 5 prior sessions) among the root's
     previous 250 sessions;
   - p_on = the same for the overnight two-way range, (Globex 18:00 → 09:29 high − low − |open − prior close|)/A;
   - comp = (p_rv + p_on)/2, and its tier = comp's percentile among the previous 250 comp values.
   - The functions are D671's (`session_features`, `tiers`), unchanged.
3. **Trade the break only when the tier < 1/3 (C1).** One micro.
4. **Cost:** MYM and M2K at `futures_costs.json` `d508_exec`: $3 + crossing + one tick, per trade in bp of the entry
   (D668-A1: MYM $4.30, M2K $4.26 a round trip).

## 3. Data (built before the run; no outcome read)

- **RTH:** D462's `fut_YM_rth_1m`, `fut_RTY_rth_1m` (ALL GATES PASS). Sessions through 2025-02-28.
- **Overnight:** `scripts/build_fut_opening_1m.py`, extended with `--roots`, writes `fut_opening_globex_1m_ym_rty` from
  the same CME ohlcv-1m archive and session and contract rules. Its gates, reported before the run:
  - **(i) Identity:** its 09:30–15:59 bars equal D462's RTH fixture bar for bar in-sample (as was checked for ES/NQ in
    D668-A1).
  - **(ii) Coverage:** the share of sessions with at least one overnight bar, per root and year. **Sessions with no
    overnight bar have no comp, and are excluded from every book, not imputed.** The share excluded is reported.
    RTY's early overnight market is thin.
  - **(iii)** No session on or after 2025-03-01 is written.
- **Window:** the sessions where the tier exists (250 sessions for p_rv/p_on, then 250 comp values). About 2018-01
  onward for YM and about 2019-08 onward for RTY (its fixture starts 2017-07-10). Through 2025-02-28.
- **The vault is not read.**

## 4. Statistics

**Books:**
- B0, every break in the window;
- **C1, the rule;**
- C2 and C3, the middle and busiest thirds.

For each, per trade at 1 micro: trades a year, gross and net, HAC t, win rate, P(hold), $ a year, daily Sharpe and
Sortino, maximum drawdown.

**Gate 1, the MECHANISM (gross, per root, Holm across YM and RTY):**
- **(a)** C1's mean gross − the rest's mean gross, against an **enumerated rotation of the comp tier across sessions**
  (offsets 21 … n − 21; exact, so SE 0). It must rank above the rotation's p95, and the one-sided rank p is
  Holm-adjusted across the two roots.
- **(b)** C1's mean gross > 0, one-sided HAC t, Holm across the two roots.

**Gate 2, TRADEABILITY (net, on a root that passed Gate 1, Holm across the roots at Gate 2):**
- C1's mean net > 0, one-sided HAC t;
- C1's mean net above the p95 of 1,000 within-year random subsets of B0 of C1's count (seed 673), by more than 2
  bootstrap SE;
- C1's net still > 0 at +1 extra tick on every fill;
- at least 60 C1 trades;
- C1's net > 0 without February–April 2020.

**Verdicts, per root:**
- SUPPORTED (both gates);
- MECHANISM ONLY (Gate 1 only);
- NOT SUPPORTED.

Each is stated with its power (§6).

**The four groups and the component line** for C1:
- daily $ Sharpe at one micro;
- ρ with the rebuilt K8;
- ρ with NQ's D672 C1 book (in-sample, where the windows overlap);
- ρ between YM's and RTY's C1.

**Declared secondaries** (reported, never gated):
- **(S1)** within C1, dealer g above versus below its walk-forward median, predicted + (D672 NQ: +12.70 vs +2.08);
- **(S2)** the ladder C1 > C2 > C3;
- **(S3)** long and short separately;
- **(S4)** each input alone (p_rv, p_on);
- **(S5)** the E2 exit;
- **(S6)** by year.

## 5. Predictions (from the root stories, written now)

1. **RTY passes Gate 1.** C1 − rest > 0 above the rotation's p95, and C1 gross > 0.
2. **RTY's Gate 2 is marginal:** the M2K cost is about 4.3–6.1 bp. Predicted: C1 net positive, but t < 2.
3. **YM fails Gate 1 on (a).** C1 is not better than the rest by more than the rotation's p95. The busiest third is its
   worst (ES's pattern).
4. **(S1) holds on RTY.** Within C1, higher dealer g is better.
5. **RTY's C1 is positive in at least 4 of its full years** (2020–2024).

## 6. Power (from D667/D672, before any YM/RTY read)

Per-trade σ is taken as ES's 35 bp for YM and NQ's 45 bp for RTY (assumptions, not reads).

| | C1 trades (≈ 55/yr) | MDE of C1 net (80%, α 0.025) | MDE of C1 − rest | power at NQ's effect (C1 − rest +7.2) |
|---|---:|---:|---:|---:|
| YM, 2018-01 → 2025-02 | ≈ 390 | ≈ 5.0 bp | ≈ 6.1 bp | ≈ 0.90 |
| RTY, 2019-08 → 2025-02 | ≈ 300 | ≈ 7.3 bp | ≈ 8.9 bp | ≈ 0.62 |

**So:**
- YM can detect an NQ-sized effect if one exists; a null there is informative.
- RTY has roughly 60% power at NQ's size, so a Gate-1 miss there is weak evidence, and is stated as such.

## 7. Seals and order of work

**Seals:**
- The vault (2025-03-01 → 2026-09-18) is not read on any root.
- CL/NG post-vault data is sealed until D626's read on 2026-10-10.
- SqueezeMetrics: the prior row only, never output per date (the licence guard), and credited.

**Order of work:**
1. This record, committed alone.
2. The overnight fixture for YM/RTY, with gates (i)–(iii), committed.
3. `scripts/stage0_d673_compression_ym_rty.py`:
   - D672's functions;
   - lag audits for the tier, the overnight window and the GEX row date;
   - a selftest in which each audit raises on a broken input;
   - run once.
4. A RESULT record.

**Routing:**
- **SUPPORTED on RTY:** the compression break becomes a component candidate for the ledger (its standard in
  `COMPONENTS_PROP.md`), with the vault's joint run on all four roots as its confirmation. Anything built on GEX
  informs only the principal's own trading.
- **NOT SUPPORTED on both:** the thread is recorded as NQ-specific or spurious. NQ's in-sample result then stands only
  until the vault reads it.
