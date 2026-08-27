# D239 — Time-series momentum as arm two

**Status:** Pre-registered — committed BEFORE any runner exists
**Date:** 2026-08-28
**Area:** Strategy research

---

## The question

[S1](../BOOK.md#s1--the-recovery-rule) is the book's only entry, at **18.9% exposure**. Four
fifths of the capital is idle. **Is multi-asset time-series momentum the second arm?**

[D238](D238-the-short-side-mirror.md) closed the obvious candidate and left a precise target:
adding an arm improves the book's maximum attainable Sharpe **iff `SR_B > ρ · SR_A`**, with
`SR_A = +0.746`. The mirror supplied `ρ = −0.0687` and failed on return. **This candidate is
chosen for the opposite reason — it should supply the return, and the open question is ρ.**

---

## The rule

```
For each of the 57, on daily bars:

    position = 1  if  close[t] > close[t - 252]      (12-month price return > 0)
               0  otherwise
```

Long-flat, `lag = 1`, equal-weighted, same per-symbol costs, same dividend-adjusted scoring
frame, same 1,000-bar warm-up as S1 — **so both arms are scored on identical bars**, which is
what makes the paired bootstrap and the correlation meaningful. 252 is inside the existing
warm-up, so nothing is truncated and no cell starts late.

**One constant, and it is the canonical one.** 252 bars is 12 months, the value time-series
momentum has been published at since Moskowitz–Ooi–Pedersen (2012). Nothing is swept.

**The signal is computed on PRICE, the scoring on TOTAL RETURN** — D217's standing convention,
because rewriting the price to smuggle dividends into the signal would be a different rule
wearing the same name. *Note the road not taken: MOP define the signal on **excess** return
over `rf`. That variant is not tested here. Naming it now so it cannot be reached for later if
this one disappoints.*

---

## Why this candidate, stated before the result

**It is orthogonal to S1 by construction rather than by luck.** S1 buys three-week
*reversals* — oversold and turning, mean holding 15 bars. This buys twelve-month
*continuations*. They exploit opposite signs of autocorrelation at different horizons, so a
low ρ is a structural prediction, not a hope.

**It fills the hole S1 actually has.** S1's one *demonstrated* failure is T3: it lost to
buy-and-hold over the only forward window ever tested, because a 15.6%-exposed book cannot keep
pace with a melt-up. A 58%-exposed arm can.

**The fixture is already a genuine multi-asset trend universe** — 7 bond funds, 4 metals and
commodity funds, 14 country funds and 32 US equity funds. That breadth is where trend's Sharpe
comes from, and it costs no new data.

---

## Measured before the run

Exposure is a property of the signal, not of returns, so it is measured and disclosed here in
the D236/D238 house style rather than reported later as a finding.

| | instruments | exposure |
|---|---:|---:|
| **T1 — all 57** | 57 | **58.31%** |
| **T2 — non-equity subset** | 11 | 49.81% |
| *(the equity 46, for context)* | 46 | 60.34% |
| *S1, for reference* | 57 | *18.87%* |

**The non-equity subset is defined by asset class, not by performance**, and is fixed here:
`AGG, GLD, HYG, IEF, LQD, SHY, SLV, TIP, TLT, UNG, USO`. GDX and GDXJ are **equity** securities
and are classified as such despite being metals-driven — the strict reading, chosen so the
partition cannot be tuned.

**Hurdle E fails, and it is stated here rather than discovered.** Pooled entries **1,201** (≥100
✓); **minimum 7 per symbol, median 19**, against 30 required (✗). This is inherent to a slow
rule — twelve-month momentum produces a handful of independent signals per instrument per
decade — and it is the same shape of failure S1 has at 9 per symbol.

---

## Hurdles

- **P1 — carries the verdict.** **`SR_T1 > ρ · SR_S1`**, with ρ measured on the two arms' daily
  excess returns. This is exactly the condition under which *some* allocation to T1 raises the
  book's maximum attainable Sharpe, and its virtue is that **it depends on no weighting
  choice.**
- **P2 — the concrete portfolio test.** A **50/50 capital blend** of S1 and T1 beats S1 alone on
  excess Sharpe, with a **paired block bootstrap `p05 > 0`** (block 21, both arms on identical
  resampled dates). 50/50 is declared, not optimised.
- **P3 — the anti-beta control, and it is the one that matters most.** T1 must beat its
  **matched-count rotation null at p95**. *A 58%-exposed long-flat book, in a market that rose
  8.42%/yr, will post a positive Sharpe for entirely trivial reasons.* The rotation null — same
  exposure, same turnover, same holding periods, wrong bars — is the only thing separating trend
  **timing** from **being invested a lot**.
- **P4.** T1 beats buy-and-hold (+0.235) on excess Sharpe, reported beside its √f prediction.
- **E.** Reported, not waived. Already known to fail per-symbol, above.
- **R6 binds:** every leg is computed in code or the runner fails loudly.

**Reported, not hurdles.** ρ itself; the √f decomposition; the null's **money and volatility**
legs (D238's reusable audit, kept because it is what turned a suspicious clean sweep into a
defensible finding); Calmar; and — because it is the number the book's purpose actually turns
on — **deployable return**, `CAGR + rf × (1 − exposure)`, since every CAGR in this programme
credits idle cash nothing.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **Q1** | **T1 beats buy-and-hold** on excess Sharpe. A selection-free 58.31% book scores `0.235 × √0.583 = +0.179`, so this requires roughly **+31% selection quality** | **moderate-high** |
| **Q2** | **ρ with S1 lands in 0.30–0.50.** Both arms are long equity most of the time, so the structural orthogonality of horizon will be diluted by shared beta | **moderate** |
| **Q3** | **P1 passes, narrowly.** If ρ ≈ 0.45 the bar is ≈ **+0.34**, and I expect T1 in the +0.35 to +0.55 range. Genuinely close — this is the real test | **low-moderate** |
| **Q4** | **P2 FAILS.** Called in advance with the arithmetic: S1 has a very high Sharpe at *low* vol (6.09%), and a 50/50 **capital** blend with a higher-vol arm drags the combination toward the trend arm's Sharpe. At `SR_T1 = 0.45`, `σ_T1 = 13%`, `ρ = 0.45` the blend scores ≈ **+0.63 against S1's +0.746** | **moderate-high** |
| **Q5** | **T2 scores below T1 on Sharpe but at materially lower ρ**, because the non-equity subset is where the genuine diversification lives and also where the thinnest sample is | **moderate** |

**Q3 and Q4 disagreeing is the point of the study, not a contradiction.** P1 is the
*optimal-weight* condition; P2 is one fixed weighting. If they split, the finding is that
**the trend arm belongs in the book at a weight well below 50%** — which is a result, and a
more useful one than either hurdle alone.

**And a prediction about what the answer will be worth.** S1's deployable return is ~8.7%/yr.
Its Sharpe is already high and hard to improve. **The realistic case for this arm is that it
raises return and puts idle capital to work while barely moving Sharpe** — so the deployable
return column, not the Sharpe column, is where I expect the case to be made or lost.

---

## Stage 1 only

**The mined 57.** The holdout 60 and the 2025–2026 forward window are **not touched.** Under R8
nothing here reaches `BOOK.md` without its own pre-registered out-of-sample test.

---

## Ledger

| count | N |
|---|---:|
| fresh — 3 cells | **3** |
| + D238's 4, D234's 6, D235's 7, D236's 6 | 26 |
| + disclosed ETF prior | **45,829** |

---

## Reuse — D212 is binding

| need | reuse | from |
|---|---|---|
| panel, cleaning, per-symbol costs, dividend frame | `load_panel` | `run_macd_ladder.py` |
| **the signed scorer, financing, rotation null with money/vol legs** | `score`, `_excess_sharpe`, `rotation_nulls`, `signed_log_returns` | **`run_short_mirror.py`** (D238) |
| S1's book, so the comparison arm is bit-identical | `base_masks`, `hold_book` | `run_stops_targets.py` |
| the paired block bootstrap, block 21 | `paired_block_bootstrap` | `run_jerk_rung.py` |

**Written fresh:** the 252-bar signal (three lines), the asset-class partition, and the 50/50
blend. Nothing else — D238's scorer was built to be the general one and this is its first reuse.

## Verification

- Full suite green, offline, deterministic; `--report-only` re-renders **byte-for-byte**, with
  `CELL_ORDER` explicit from the start (the idempotency defect appeared in D220, D222 and D229).
- **S1 must reproduce +0.746 / 18.9% / −10.30%** in this runner. If the comparison arm moves,
  the study is void.
- **No look-ahead:** `position[t]` depends only on closes at `t−1` and `t−253`; assert that
  perturbing any close from bar *t* onward moves no position at index ≤ *t*.
- **The signal is pinned against a hand-built series** where the 252-bar sign is known by
  construction, so "12-month return > 0" is checked rather than trusted.
- **Both arms are scored on the identical bar range**, asserted, since the paired bootstrap and
  ρ are meaningless otherwise.
