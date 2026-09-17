# D464 — the personal arms as gates on the session hold: S1 and S2, computed on the index ETFs, select which nights C1 holds ES; hurdle P at ES and micro granularity

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D464-the-personal-arms-as-gates-on-the-session-hold-S1-and-S2-computed-on-the-index-ETFs-select-which-nights-C1-holds-ES-hurdle-P-at-ES-and-micro-granularity.md`. The H1 above is the full title.*

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. In-sample
**2016-01-04 to 2023-12-29** on ES (the D462 usable window); **2024-01-02 onward unread**; no
holdout of any other fixture. D464 taken after `ls docs/decisions` and `git log --all` (both
worktrees) showed D463 last.

## 0. What is being tested, and what it is not

The principal asked whether the personal book's arms can be tried on the futures data for the prop
book. **They cannot be ported as they are:** S1 holds ~15 days and S2 a quarter, and the venue
permits no position across the 16:10 flatten. **What can be tested is the one form the venue
allows** — C1's session hold (18:00 Globex open → 16:00 print, D449/D451's hold table) taken
**only on the nights the arm's state is on**, the state computed on the index ETF's daily bars
exactly as the book computes it (D234/D240's own functions), the position and its path on ES.
The question is therefore: **does S1's or S2's selectivity change the hurdle-P outcome that C1
unconditional failed** (funded life 0.14 years, D440), or does the arithmetic of an overnight ES
hold on a $50k account decide regardless? It is not a test of S1 or S2 — their book status is
untouched by this record whichever way it goes.

## 1. The gates (the book's specification, the book's code)

Computed on **SPY** daily bars (`etf_wide_daily_raw`, 2010-01-04 →, the fixture family the book
was tested on), lag 1 (the state known at the close of day d−1 gates the hold entered at 18:00 on
d−1 and exited 16:00 on d — the state is decided before the entry):

- **S1 state** := `hist_L > 0 AND md_L <= 0` from `run_activation_threshold.log_parts` (Wilder
  34 / zero-lag 34 / SMA 9 on log prices; `src/backtest_framework/research/macd.smma, .zlema`),
  1,000-bar warm-up satisfied by the ETF fixture before 2016.
- **S2 state** := `UPTREND` = `g_lo > 0 AND g_hi > 0` from `run_uptrend_onset.rolling_fit` over
  confirmed swing pivots (`structure.pivots`, k = 3) in the trailing 252 bars — **the state, not
  the onset**: the book's S2 enters at onset and holds up to 63 bars or until the state ends, so
  the nights S2 is exposed are, to a close approximation, the nights the state is on within 63
  bars of an onset. The gate used is **"in an episode, ≤ 63 bars from its onset"** (S2's own
  exposure rule); the raw state is reported beside.
- **QQQ and DIA** gates are computed and reported (the book's universe is broad; ES tracks SPY).
- **Reported beside:** the union (either arm on) and the intersection (both).

## 2. The holds

`data/fixtures/es_c1_holds.csv.gz` (D449, same-contract 18:00 → 16:00 holds with `d_end`,
`d_high`, `d_low`, `mae` as fractions of entry), **restricted to 2016-01-04 → 2023-12-29** (before
2016 the archive carries mostly Mondays — D462; D449's early rows are Monday-only and are not
used). The fixed-1 sizing at ES = $50 × entry per point; MES = one tenth.

## 3. Measured

1. **Per night, gated vs ungated vs all:** count, mean and σ of `d_end` (bp), median, hit rate,
   the MAE distribution (p50/p90/p99/worst, in bp and in $ per ES contract), P(MAE > $1,000) and
   P(MAE > $2,000) at one ES contract; the same for QQQ and DIA gates, the union and the
   intersection.
2. **Nulls on the gate (two, both on `d_end`):** **N1** the exact rotation of the gate series over
   every offset (keeps the gate's persistence and count, destroys alignment; p50/p95/p99 of the
   gated mean); **N2** matched-count random gates with the gate's run-length distribution (100
   draws; the D291 lesson — a random subset that churns is not a control for a persistent gate).
3. **Hurdle P on the gated hold** (ES, MFFU Rapid EOD 50K, D440's machinery through D463's
   `sized_days` / `provider_of` with the hold's (d_low, d_high, d_end) in dollars): the C4 rule
   at f ∈ {0.2%, 0.4%, 0.7%, 1.1%} with **whole ES contracts**, and again with **whole MES
   contracts** (one tenth; the only way the account expresses fractional size — MES traded from
   2019-05, and its path is ES's path by construction); **P3** worst day and days below −2%,
   **P4** funded life in years and survival at 600 days with `V` ± SE, **P5** years with a day
   above 40% of that year's profit. Unconditional C1 on the same window, same sizing, as the
   reference row.
4. **Both lenses:** per night (bp) and per bar deployed (the hold's bp over the ~22 hours, on
   gated nights only).

## 4. The bar (one primary, R14): the S2-exposure gate on ES, in-sample

- **G1** gated mean per night > 0, above N1's p95 and N2's p95 by 2 MC-SE.
- **G2** gated MAE p99 (bp) **below** the ungated p99 — the gate selects calmer nights, not merely
  fewer.
- **P4** funded life ≥ 3 years at some declared f on the ES grid **or** the MES grid, with `V` > 0
  by 2 SE at that f, **and** P3's worst day ≥ −2% and P5 = 0 years at that f.
**Candidate for the unread slice: G1 ∧ G2 ∧ P4.** S1 is scored on the same bar and reported; the
candidate condition names S2 because its selection (calm uptrends) is the one whose mechanism
could move P4.

## 5. Predictions (MODERATE on the shape — D259/D440/D451 measured the unconditional hold — LOW on the gates)

- **X-a** unconditional C1 on 2016–2023: mean **+3 to +5 bp** per night, σ **90–110 bp**, MAE p99
  **330–420 bp**, P(MAE > $2,000 at one ES contract) **8–14%**.
- **X-b** S2 gate on: **30–45%** of nights; gated mean **+3 to +6 bp**, σ **70–95 bp** (lower —
  calm uptrends), MAE p99 **250–350 bp**; G2 passes. S1 gate on: **12–20%** of nights; gated mean
  **+4 to +9 bp** (post-selloff recoveries), σ **110–150 bp** (higher), MAE p99 **400–550 bp**;
  G2 fails for S1.
- **X-c** N1's p95 of the gated mean **+2 to +4 bp** for either gate; **G1 fails for S2** (a calm
  subset of a positive drift is not distinguishable from a rotated calm subset) and is **a coin
  for S1**.
- **X-d** hurdle P, ES contracts: the C4 rule sizes **zero** at f ≤ 0.4% (an overnight σ of
  ~$2,000 per contract on a $50k account), and at any size that trades **P3 breaches on ≥ 5% of
  nights and P4's funded life is < 0.5 years** — gated or not. MES contracts: sizing is
  expressible (2–5 micros at f = 0.4–0.7%), **P3 passes**, **P4's funded life rises to 0.5–2
  years and stays under three**, and the annual return at that size is **+1 to +3%** of the
  account — the C1 scissors at a finer grain. **X-e** S2 lengthens P4's life relative to
  unconditional by **1.3–2×** at matched f, S1 shortens it; **neither clears three years.**
- **X-f** QQQ and DIA gates agree in sign with SPY's on every statistic; the union gate behaves
  like S2's (S2 is on far more often); the intersection is on < 5% of nights.

## 6. Not in scope

S1's or S2's status in the personal book (this is not a test of the arms; their falsification
conditions are the book's); any change to the arms' constants; the 2024–2026 slice; NQ/YM
holds (D449 built ES only); any stop or intraday exit on the hold; sizing beyond the declared
grids. Fifty-first look by object; look #2 of the prop track on the instrument.

## 7. Files

This record · `scripts/run_d464_arms_as_gates.py` (`--run`, `--selftest`) ·
`data/d464_arms_as_gates.json` · RESULT.
