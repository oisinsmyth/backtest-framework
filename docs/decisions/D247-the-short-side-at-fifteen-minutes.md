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

---

## RESULT

**Produced:** 2026-08-28 · `uv run python scripts/run_intraday_shorts.py` · Page:
[`INTRADAY_SHORTS_RESULTS.md`](../results/INTRADAY_SHORTS_RESULTS.md)

**57 ETFs × 55,726 bars, PPY 6,513, live 8.40 years.**

### The one-sentence version

**Every cell loses and the structural thesis is confirmed anyway: the intraday-only S1 short is
the first construction in this programme to hold bars that actually fall — −4.27%/yr against the
continuous version's +4.72% — and turnover costs five times the edge it buys.**

### The eight cells

| | long | short | excess Sharpe | CAGR | turnover/yr | borrow/yr | null pctile | breakeven bp |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S1_short_cont | — | 27.2% | −1.248 | −6.48% | 208 | 0.32% | 100.0th | −1.55 |
| **S1_short_intra** | — | 25.9% | −1.550 | −5.55% | **334** | **0.00%** | 100.0th | **0.13** |
| S2_short_cont | — | 12.4% | −0.784 | −2.44% | 27 | 0.12% | 96.3th | −7.71 |
| S2_short_intra | — | 11.9% | −1.113 | −2.51% | 87 | 0.00% | 99.6th | −1.05 |
| *S1_long_cont* | *22.6%* | — | *−0.279* | *−1.37%* | *181* | — | *99.4th* | *0.60* |
| *S1_long_intra* | *21.6%* | — | *−0.586* | *−1.98%* | *285* | — | *100.0th* | *0.86* |
| *S2_long_cont* | *12.9%* | — | ***+0.191*** | *+1.13%* | *28* | — | *81.5th* | ***4.08*** |
| *S2_long_intra* | *12.4%* | — | *−1.209* | *−1.96%* | *91* | — | ***0.0th*** | *−0.87* |
| **B&H** | 100% | — | **+0.289** | **+9.02%** | 0 | — | — | — |

**Seven of eight cells lose money**, and the eighth (+0.191) still loses to buy-and-hold's +0.289.
**Q1: 0 of 4. Q3: 0 of 4. Best-of-four floor +0.315: cleared by nothing.**

### The finding — the drift thesis is confirmed

Annualised return of the bars each short actually holds:

| held by | bars | return of those bars |
|---|---:|---:|
| all bars | 3,119,382 | +9.02% |
| S1 short, **continuous** | 847,362 | **+4.72%** |
| **S1 short, intraday-only** | 808,634 | **−4.27%** |
| S2 short, continuous | 385,404 | +9.52% |
| S2 short, intraday-only | 370,504 | +4.53% |

**An 8.99-point swing from flattening overnight, against the +8.55 predicted** from the
overnight/intraday decomposition. **P-b's mechanism is confirmed on its own terms.**

D238 closed the short side because *"the worst bars the indicator can name still return
+0.85%/yr"*. **Here they return −4.27%.** That objection is answered — by the calendar, not by
the signal.

### And the symmetry is the strongest evidence it is real

Flattening overnight **helps every short and hurts every long**:

| | continuous | intraday-only | change |
|---|---:|---:|---:|
| S1 short, held-bar return | +4.72% | **−4.27%** | **−8.99** |
| S2 short, held-bar return | +9.52% | +4.53% | −4.99 |
| *S2 long, excess Sharpe* | *+0.191* | *−1.209* | *−1.400* |
| *S2 long, null percentile* | *81.5th* | ***0.0th*** | — |

**S2's long arm goes from the 81.5th percentile of its null to the 0.0th** when the overnight
gap is removed — its entire edge was the overnight drift. That is the same fact from the other
side, and it is what makes the short result credible rather than a fluke.

### Why it still fails: costs, exactly as registered

**Only one cell of eight has a breakeven above the ~1.6 bp charged** — S2_long_cont at 4.08 bp.
The intraday S1 short breaks even at **0.13 bp**, an eighth of what it pays.

**The arithmetic in the pre-registration was right and slightly optimistic.** It projected
turnover eating nine tenths of the drift advantage; measured, at 334 turnover units per year
against a gross edge of roughly 1.1%/yr at 25.9% exposure, **costs run about five times the
gross edge.**

### The rotation nulls look paradoxical and are not

**Shorts at the 100th percentile while scoring −1.248 and −1.550.** That is not an error: a
rotated short book has the same exposure and the same drift drag, so beating it means *the
timing is better than random*. The book still loses because the direction is wrong. **D238 found
exactly this pattern on daily bars** — real skill, unmonetisable.

### Scoring — three confirmed, two split

| | prediction | outcome |
|---|---|---|
| **P-a** | all four shorts fail Q1 | **CONFIRMED** |
| **P-b** | intraday shorts beat continuous by the drift swing | **SPLIT.** On held-bar returns, decisively (−8.99 points). **On Sharpe, no** — intraday is *worse* (−1.550 vs −1.248) because turnover rose from 208 to 334 |
| **P-c** | breakeven below 1.6 bp for ≥3 of 4 shorts | **CONFIRMED**, all four |
| **P-d** | the long controls also fail Q2 | **SPLIT.** S1's longs clear their nulls at the 99.4th and 100th — while scoring −0.279 and −0.586. S2's do not |
| **P-e** | no short clears the best-of-four floor | **CONFIRMED** |

### A correction to the runner's own output

**The auto-generated reading — *"the long controls hold and the shorts do not"* — is wrong**, and
the flaw is mine: the logic counted a long control as "holding" if it merely beat its rotation
null, and S1's longs do that at **−0.279** and **−0.586** excess Sharpe. Beating a null is not
holding.

**The correct reading: 15-minute sampling breaks both estimators in both directions.** That was
declared as likely before the run — S1's 34-bar Impulse is 1.3 sessions here — and it means this
study says almost nothing about the daily book.

### What is closed and what is not

**Closed: these two estimators at these bar counts on 15-minute bars.** Nothing else.

**Explicitly NOT closed: the intraday short.** The overnight/intraday decomposition and the
−4.27% held-bar return are the strongest evidence this programme has produced that a short arm
*can* select falling bars. **What fails is the turnover, and turnover is a property of the rule,
not of the idea.** A rule designed for the intraday horizon — holding hours rather than
flipping, at a fraction of 334 turnover units — is a separate pre-registration and now has a
measured motivation.

**No rule is proposed here**, per the stop.

### Ledger

| count | N |
|---|---:|
| fresh — 8 cells | 8 |
| + D245's 2, D242's 3, D241's 5, D240's 5, D239's 3, D238's 4, D234's 6, D235's 7, D236's 6 | 49 |
| + the gradient anatomy | 70 |
| + disclosed ETF prior | **45,873** |

---

## CROSS-SCREEN at futures cost, 2026-08-29 — [R12](../RULES.md#r12)

**R12 requires a candidate closed on one track to be screened against the other's standards before
it is discarded, and D247 is the clearest case: it closed on COST arithmetic, and the prop track's
cost is roughly twenty times lower.**

D247 charged **~1.60 bp/side** on ETFs. An ES round turn is ~0.2 bp, so **~0.10 bp/side**.
Re-screened from the committed artifact, no re-run — the breakevens D247 already published are
sufficient:

| cell | turn/yr | breakeven | @1.60 bp (as run) | **@0.10 bp (futures)** | verdict |
|---|---:|---:|---:|---:|---|
| S1_long_cont | 181 | 0.603 bp | −1.80% | **+0.91%** | clears, marginal |
| **S1_long_intra** | 285 | **0.860 bp** | −2.11% | **+2.16%** | **clears materially** |
| S1_short_cont | 208 | **−1.547 bp** | −6.53% | −3.42% | **loses when FREE** |
| **S1_short_intra** | 334 | **0.130 bp** | −4.90% | **+0.10%** | clears, worth ~nothing |
| S2_long_cont | 28 | 4.081 bp | +0.69% | +1.10% | clears (already did) |
| S2_long_intra | 91 | −0.869 bp | −2.24% | −0.88% | **loses when FREE** |
| S2_short_cont | 27 | −7.712 bp | −2.52% | −2.12% | **loses when FREE** |
| S2_short_intra | 87 | −1.054 bp | −2.32% | −1.01% | **loses when FREE** |

### The shorts were never a cost problem, and this proves it

**Four of the eight cells have a NEGATIVE breakeven — they lose with completely free trading.**
Three of those four are short cells. **S2_short_cont would need to be PAID 7.7 bp per side to break
even.**

**So removing the cost wall changes nothing for the short side.** D247's shorts are closed a second
time, on stronger grounds than the first: not *"the turnover ate it"* but *"there was nothing
there."* **That is a better closure than the original, and R12's cross-screen is what produced it.**

### What does change, and what it does not license

**S1_long_intra flips sign** — breakeven 0.860 bp against a 0.10 bp charge, so its excess Sharpe
crosses from **−0.586** to positive on cost alone. That is a genuine reversal of a published cell.

**It does not reopen the study, for two reasons stated in D247 itself:**

1. **The estimator objection is untouched and was never about cost.** D247's own reading was that
   *"15-minute sampling breaks both estimators in both directions"* — S1's 34-bar Impulse is **1.3
   sessions** at this rate. A broken estimator that becomes affordable is still broken.
2. **The universe is wrong.** These are 57 ETFs. The prop track trades **three** index futures, so
   effective breadth falls from 2.2 toward 1, and `IR ~ IC x sqrt(breadth)` takes most of the gain
   straight back.

**The honest statement: the cross-screen removes ONE of D247's two objections, for the LONG cells
only, on the wrong universe.** That is a lead for [C2](../BOOK_PROP.md), not a result — and it is
recorded here so that a future study cannot present it as one.
