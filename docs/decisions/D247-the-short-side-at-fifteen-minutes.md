# D247 — The short side of S1 and S2 at fifteen minutes

**Status:** Pre-registered — committed BEFORE the intraday panel is scored
**Date:** 2026-08-28
**Area:** Strategy research

---

## Why this exists, and what it is not

**A baseline, expected to be negative, and run because a negative baseline is where a short
programme starts.** The proposer said so explicitly and the predictions below agree.

**The reason it is worth running at all is a measurement, not a hope.** Decomposing the 57 ETFs
into overnight and intraday legs over 8.3 years, ex-dividend and split sessions excluded:

| | annualised, equal-weighted, price-only |
|---|---:|
| **overnight** (prev close → open) | **+8.59%** |
| **intraday** (open → close) | **−0.36%** |
| total | +8.19% |

Per symbol, **28 of 57 have negative intraday drift** (median +0.20%) against **6** negative
overnight (median +9.09%).

**Essentially all of the equity drift accrues overnight.** [D238](D238-the-short-side-mirror.md)
closed directional shorts because the worst bars its indicator could isolate still returned
+0.85%/yr against a breakeven borrow of −6.90%. **D238 measured close-to-close and was therefore
paying that +8.59%.** A book that is flat at every session close is exposed to **−0.36%/yr**
instead — an **8.55-point swing** — and pays no overnight borrow and no dividends over ex-dates.

**That removes D238's structural objection. It does not supply an edge**, and the cost
arithmetic below says why.

---

## The cost problem, stated before the run because it is the likely verdict

An intraday-only book does one round trip per session. S1's daily mirror held ~15 bars per
trade. For the same days of exposure that is **15× the round trips**:

```
extra turnover   f x 252 x (1 - 1/15) x 2 x 1.6bp   =   f x 7.53%/yr
drift advantage                                          f x 8.55%/yr
                                                net  =   f x +1.02%/yr
```

**Roughly nine tenths of the structural edge is consumed by the turnover required to capture
it**, and at 2 bp/side the net turns negative. **The structural advantage is real and is not by
itself a strategy.** Any positive result here has to come from signal, not from the calendar.

---

## The fixture

`etf_intraday_15m_panel` — built by `build_intraday_panel.py` from the committed as-traded
fixture, which does not load: `clean` drops bars per symbol and the lengths ranged 55,778 to
56,056. The date grid is intersected **after** cleaning and iterated to a fixed point (it
converged in one pass).

| | |
|---|---|
| **57 × 55,726 bars**, 2,156 sessions | 2018-01-02 → 2026-08-26 |
| 25.85 bars/session → **`PPY` = 6,514** | warm-up 1,000 bars = **39 sessions** |
| **live span 8.42 years** | WP0's events sidecar carried over: 1,955 dividends, 12 splits |

**The source fixture is not modified** (D24).

---

## The calendar mismatch is severe, and worse than D244's

Bar counts are frozen because the book specifies bars and D221 established the indicator is
scale-free in bar counts. **But the economic meaning is transformed, far more than on crypto:**

| | on daily bars | **at 15 minutes** |
|---|---|---|
| S1's 34-bar Impulse | ~7 weeks | **1.3 sessions** |
| S2's 252-bar regression | 1 year | **9.8 sessions** |
| S2's 63-bar age cap | one quarter | **2.4 sessions** |

**These are not the book's rules at a finer sampling. They are the same estimators at a
radically shorter horizon.** A negative result here is evidence about *those* estimators, and
says little about the daily book. **Stated now so it cannot be used later as an excuse.**

---

## Cells — a 2 × 2 × 2 factorial, eight in total

| axis | levels |
|---|---|
| rule | **S1** (`hist_L`/`md_L`) · **S2** (pivot-regression trend onset) |
| direction | **short** (the question) · **long** (the control) |
| holding | **continuous** (holds through the overnight gap) · **intraday-only** (flat at each session close) |

```
S1 short:  position = -1  if  hist_L < 0  AND  md_L >= 0        (D238's mirror)
S2 short:  DOWNTREND := g_lo < 0 AND g_hi < 0; enter at onset, exit at age 63 or state end
```

**The long cells are controls and are not candidates.** Without them a short failure cannot be
attributed: it might be direction, or it might be that 15-minute sampling breaks both rules.
**That distinction is the main thing this study can establish**, and it is why eight cells rather
than four.

---

## Borrow and financing — modelled explicitly, as requested

```
excess = total  −  mean(long fraction) × rf_per_bar  −  overnight borrow on shorts
```

- **`rf` is charged on the long fraction only.** A short book's collateral earns `rf`, which
  cancels against the benchmark — D238's asymmetry 4, unchanged.
- **Borrow is charged at 1.0%/yr (D238's constant) on short positions held ACROSS A SESSION
  BOUNDARY**, prorated by the actual calendar gap — one day midweek, three over a weekend.
  **Not per bar**: charging borrow on a 15-minute intraday bar would be wrong by a factor of ~26
  and would flatter nothing, it would simply be false.
- **The intraday-only cells therefore pay no borrow at all**, which is the honest model of a
  book that is flat at every close.
- **Locate fees are NOT modelled and are named as a friction.** Neither is **SEC Rule 201**,
  which restricts short sales at or below the NBBO for the rest of the day and the next after a
  10% intraday decline — and which bites precisely when an intraday short wants to act.
- **Trading costs** are the daily book's `per_side_bps` per symbol, unchanged. **The breakeven
  cost per side is the headline diagnostic**, because that is where this lives or dies.

---

## Hurdles

- **Q1.** Excess Sharpe **> 0** for each short cell.
- **Q2 — carries the verdict.** Beats its **matched-count rotation null at p95** — same exposure,
  turnover and holding periods, wrong bars.
- **Q3.** Block bootstrap **`p05 > 0`** on the cell's own excess Sharpe (D230, R6).
- **Best-of-search null (D228) across the four short cells**, since four are screened and D240's
  stop cleared uncorrected at the 99.6th percentile and then failed out of sample at the 71.7th.

**Reported, not hurdles:** turnover, **breakeven cost per side**, exposure, deployable return,
max drawdown, hurdle E, borrow paid, and **the conditional-return profile of the target bars** —
because D244 established a null can be beaten or lost by drift structure alone, so that profile
is measured before any null result is interpreted.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **P-a** | **All four short cells fail Q1.** The proposer expects this and so do I | **high** |
| **P-b** | **The intraday-only shorts beat the continuous ones** by roughly the drift swing, adjusted for exposure. This is the measurement the record exists to make | **moderate-high** |
| **P-c** | **Costs dominate everything.** Breakeven cost per side comes in **below** the ~1.6 bp charged for at least three of the four short cells — meaning they lose before any signal question arises | **moderate-high** |
| **P-d** | **The long controls also fail Q2.** A 34-bar Impulse at 15 minutes is a 1.3-session estimator and has no reason to behave like the daily rule | **moderate** |
| **P-e** | **No short cell clears the best-of-four floor** | **high** |

**P-d is the one that decides how to read everything else.** If the longs fail too, this study
says *15-minute sampling breaks these estimators* and says nothing about the short side. If the
longs hold and only the shorts fail, that is a direction result and it is informative.

---

## Stop

**No rule is proposed and none is changed.** If everything fails, the intraday short question is
not closed — **only these two estimators at these bar counts are.** A rule designed for the
intraday horizon is a separate pre-registration, and the overnight/intraday decomposition above
is the finding that would motivate it.

---

## Ledger

| count | N |
|---|---:|
| fresh — 8 cells (4 short, 4 long controls) | **8** |
| + D245's 2, D242's 3, D241's 5, D240's 5, D239's 3, D238's 4, D234's 6, D235's 7, D236's 6 | 49 |
| + the gradient anatomy | 70 |
| + disclosed ETF prior | **45,873** |

---

## Reuse — D212 is binding

Scorers, rotation nulls, the bootstrap, `signals`/`walk` for S2, `base_masks`/`hold_book` for S1
— all committed and tested. **Written fresh: the session-boundary borrow charge, the
intraday-only flattening, and `PPY = 6,514`.**

**Timed before committing to the design**, per D226's warning about nulls on a
`(57, 56000)` panel: `load_panel` 20 s, one portfolio pass **58 ms**, pivots and the Impulse
series 0.1 s per symbol. **1,000 rotations × 8 cells ≈ 8 minutes.** No reduction in `n_sims` is
needed, and none is taken — cutting sims widens the null and makes the hurdle easier, which is
the wrong direction.

## Verification

- `--report-only` re-renders byte-for-byte; full suite green.
- **The panel is asserted rectangular** at 57 × 55,726, and the source fixture untouched.
- **Borrow is asserted to be charged only across session boundaries**, and to be exactly zero for
  every intraday-only cell.
- **The intraday-only cells are asserted flat at every session close**, on every symbol.
- **No look-ahead:** perturbing a bar from *t* onward moves no position at any index ≤ *t*.
