# D329 RESULT — `skew_63` owns the short leg, specifically; `hist_L` does not own the long leg

**Status:** RESULT. Pre-registered at `16b1977`, runner at `df11bc3` — both
before this file existed (R8).
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted.**

---

## 1. At the operating point the leg-wise book beats both parents on both lenses — and every pre-registered form of that claim failed as written

Path-invariant (per trade, per-leg costed, no cap) and path-variant (the capped
book, bp/bar, D318 costing). **Never compared on the same statistic.**

| arm | k | **invariant net/trade** | t | mean/2c | rt | **variant net Sharpe** | net bp/bar | maxDD bp |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| H `hist_L` | 20 | −0.89 | −0.02 | 0.99 | 189.9 | −0.082 | −3.97 | 43,956 |
| S `skew_63` | 20 | +44.83 | +1.26 | 3.78 | 32.3 | +0.421 | +12.60 | 19,895 |
| **LW** | **20** | **+63.26** | **+1.50** | 1.94 | 120.0 | **+0.434** | **+17.49** | 28,278 |
| RV reverse | 20 | −29.63 | −0.64 | 0.49 | 102.3 | −0.062 | −2.62 | 38,445 |
| LW | 10 | +21.43 | +0.64 | 1.33 | 120.6 | +0.415 | +19.08 | 21,256 |
| LW | 40 | **+84.41** | **+1.69** | 2.20 | 121.1 | **+0.619** | **+25.88** | 22,253 |

**At k=20 and k=40, LW beats both parents on both lenses.** At **k=10 it loses
to `skew_63`** on the invariant lens (+21.43 against +31.39) — and that single
cell falsifies Q1's "every k".

**The reverse pairing is the worst arm at k=20 and k=40** on both lenses, and
it beats H by a hair at k=10 and on k=20 Sharpe (−0.062 against −0.082). That
falsifies Q6's "every k".

**I wrote the predictions too strictly and they failed on their strictness.**
The substance at the operating point held; the "every k" and "+0.10" forms did
not. Both facts are recorded; neither is softened.

## 2. The composition is exact, and the per-leg table is the mechanism in numbers

Assertion `[L]` held bit-identically in both lenses, so **every per-leg number
below is the same number in the parent and in the composite.**

| arm | leg | trades | gross | **net** | t | held half | held price | **rebalancing premium** |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| H / LW | **long** (`hist_L`) | 1,413 | +201.7 | **+97.0** | +2.97 | 52.3 | $10.8 | **+23.5** |
| H / RV | short (`hist_L`) | 1,419 | −13.2 | **−98.4** | −0.21 | 42.6 | $9.8 | **−45.9** |
| S / RV | long (`skew_63`) | 923 | +93.1 | +76.1 | +1.45 | 8.5 | $23.5 | −4.6 |
| S / LW | **short** (`skew_63`) | 1,024 | +32.0 | **+16.6** | +0.92 | 7.7 | $30.0 | −23.5 |

Three things this settles:

1. **`hist_L`'s two legs are not symmetric, and the sign of the asymmetry is the
   rebalancing premium's.** Its long leg gains +23.5 bp per trade from daily
   rebalancing; its short leg pays −45.9. The short leg's gross is −13.2 and
   after its own 85 bp round trip it nets **−98.4** — the worst leg in the
   study. **D327 §2 stands under the book's convention** (D328 §11).
2. **My magnitudes were wrong, in a way I can name.** The D328 profile put the
   premium at +78 / −85 at ranks 0–1 over a fixed 20-bar window; per *trade*
   it is +23.5 / −45.9. The profile counts a persistent name once per bar it
   sits at rank 0; the ledger counts it once per entry. **The premium
   concentrates in the persistent names.** Q5 is falsified on its thresholds
   and every leg has the predicted sign.
3. **`skew_63`'s short leg is the cheapest leg in the study** — 7.7 bp
   half-spread in $30 names — and it still pays a −23.5 premium. Cheap is not
   the same as un-bouncy. Q5's "within ±15" was wrong.

## 3. The enumeration: the short leg is SPECIFIC and the long leg is NOT

k=20, both lenses. 46 partners, less the degenerate cells.

**Direction A — `hist_L` long + X short. Where is `skew_63`?**

| lens | rank | value | p50 of 44 | p95 | next four |
|---|--:|--:|--:|--:|---|
| invariant net/trade | **1 of 44** | +63.26 | +5.47 | +54.82 | `dist_lvn` +58.95, `md` +55.39, `struct_trend` +51.54, `close_in_range` +50.48 |
| variant net Sharpe | **1 of 44** | +0.434 | +0.099 | +0.362 | `dist_lvn` +0.43, `retrace_leg` +0.37, `close_in_range` +0.30, `dist_hvn` +0.29 |

**First of 44 on both lenses, above the p95 of the control on both.**
`skew_63` specifically owns the short leg for `hist_L`-long.

**Direction B — X long + `skew_63` short. Where is `hist_L`?**

| lens | rank | value | p50 of 45 | p95 | the top five |
|---|--:|--:|--:|--:|---|
| invariant net/trade | **5 of 45** | +63.26 | −8.35 | +69.34 | `id_mean` +81.23, `rev_21` +74.55, `rsi` +70.24, `retrace_leg` +65.74, **`hist_L` +63.26** |
| variant net Sharpe | **14 of 45** | +0.434 | +0.360 | +0.665 | `close_in_range` +0.69, `retrace_leg` +0.68, `body_frac` +0.67, `on_minus_id` +0.64, `id_mean` +0.54 |

**Fifth per trade, fourteenth as a book.** `hist_L`'s long leg has the highest
gross per trade of any leg measured here (+201.7), and it pays **52.3 bp** a
name for it in **$10.8** stocks — the most expensive and most volatile leg in
the study. Thirteen cheaper long legs make a better *book* on top of
`skew_63`'s short leg. **The long-leg choice is not settled, and it is not
`hist_L`.**

**Q4 is falsified as written and half of it is the strongest result in the
study.** The pre-registration did not anticipate the asymmetry. The stop
condition "Q4 fails with Q1 confirmed → `hist_L`-long carries the effect and
the short partner is interchangeable" is the *mirror* of what happened: **the
short partner is the specific one.**

## 4. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | LW beats both parents: invariant every k, variant Sharpe k=20 *(load-bearing)* | **FALSIFIED** at k=10 invariant (+21.43 < +31.39). **Holds at k=20 and k=40 on both lenses** |
| **Q2** | per leg, every k: `hist_L` wins the long, `skew_63` wins the short | **FALSIFIED** at k=10 — `skew_63`'s long leg +54.0 beats `hist_L`'s +30.6 at short horizons. Holds at 20 and 40 |
| **Q3** | LW maxDD shallower than H's; Sharpe > best parent + 0.10, k=20 | **FALSIFIED** on margin — +0.013, not +0.10. MaxDD 28,278 against 43,956 as predicted. (At k=40 the margin is +0.15, which is not the pre-registered k) |
| **Q4** | `skew_63` top-3 short partner AND `hist_L` top-3 long partner; top-5 on Sharpe *(load-bearing)* | **FALSIFIED — and split.** `skew_63` is **1 of 44 on both lenses**. `hist_L` is 5 of 45 per trade and **14 of 45** on Sharpe |
| **Q5** | premium: H short < −40, H long > +40, LW short within ±15 | **FALSIFIED** on two of three thresholds — −45.9 ✓, +23.5, −23.5. Every sign as predicted; the magnitudes were the snapshot's, not the ledger's (§2.2) |
| **Q6** | RV worse than both parents, every k and on Sharpe *(against)* | **FALSIFIED** narrowly — worst arm at k=20/40 on both lenses; beats H at k=10 (−6.07 vs −10.84) and on k=20 Sharpe (−0.062 vs −0.082) |
| **Q7** | monotone tilt across legs; round trip below H's | **CONFIRMED** — 52.3 / 7.7 bp, $10.8 / $30.0, 120.0 against 189.9 |

**One of seven confirmed as written.** The stop conditions do not match what
happened, so none is invoked; §6 says what the result actually supports.

## 5. Three degenerate cells, and what they say about the cost model

`cs_spread`'s long leg and `on_share`'s and `dist_52w_high`'s short legs
select names whose held median Corwin-Schultz half-spread is **exactly zero**,
and D322's breakeven divides by it. They are recorded as degenerate, excluded
from the ranking, and counted beside every rank above. **A leg the cost model
cannot price is not a free leg** — it is D302's clamp (a left truncation of the
spread estimate) arriving as a blind spot, and any partner whose leg lands
there is unscoreable on this fixture until the spread estimator is fixed.

## 6. What this establishes, and what it does not

1. **Leg-wise composition is a real construction on this programme.** It
   composes exactly (`[L]`), and at the operating point it beats both parents
   on both lenses. That is not a stack promotion; it is a construction that
   now exists.
2. **`skew_63` owns the short leg, specifically — first of 44 on both lenses,
   above the control's p95.** That is the strongest single result here and it
   was pre-registered in the right direction.
3. **`hist_L` does not own the long leg.** Its long leg is the strongest gross
   leg measured and among the most expensive books, and thirteen cheaper legs
   pair better with `skew_63`-short. **Choosing the long leg is a fresh
   question**, and having now seen all 45, any choice I make from them is
   post-hoc. It needs its own pre-registration on a basis other than this
   table — the per-leg profile and D290's per-leg books, read for the long
   side the way this study read them for the short.
4. **The rebalancing mechanism has the right sign on every leg and the wrong
   magnitude on two of three.** D327 §2 stands under the book's convention;
   the per-trade premium is about a third of the rank-0 snapshot's because the
   snapshot over-weights persistent names.
5. **`hist_L`'s short leg is the worst leg in the study at −98.4 per trade.**
   Whatever the incumbent's future, its short leg as currently sized is not
   part of it.

## 7. What is owed

1. **The long leg, pre-registered.** Candidates from the *profile* side, not
   from §3's table: which signals have a working long end, cheap held names,
   and a positive or small premium. Then one construction, one prediction,
   against the parent and against `skew_63`-short's enumeration p95 as the bar.
2. **A constant-shares short leg** on `hist_L`, the direct sizing test of
   §2.1. Out of scope here because it changes the simulator's accumulation.
3. **The spread estimator's zero clamp** (§5), which now blocks three legs.
4. **D326's `mean/2c` for `skew_63` is 3.78 here and 4.53 there** — different
   k (this is k=20, D326's best was k=40). Not a discrepancy; noted so it is
   not read as one.

## 8. Assertions

All eight pass, and all eight are properties of the code.

| | |
|---|---|
| **[L]** | LW's long ledger is H's and its short ledger is S's, bit-identically, in both lenses; per-side counts identical; LW + RV == H + S on the bar series to 1e-12 |
| **[P]** | every H trade's summed P&L recomputed from `(row, entry, age)` on `r1T` and `mkt` reproduces the ledger to **3.3e-16** |
| **[1]** | the parents reproduce D326's k=20 cells on both lenses to **0.0e+00** |
| **[3]** | `rank_cells` raises in both directions |
| **[C]** | per-leg `2c` is 2 × that leg's held median half-spread (52.3 long, 7.7 short); paired 4× rejected; round trip 120.0 is the sum |
| **[4]** | rolling the ranking moves the variant lens by 23.76 bp/bar and the invariant by 58.4 bp/trade |
| **[R]** | RV differs from LW on both sides |
| **[6]** | the check raises on a book handed free money |

**Speed:** profiled before optimising. Eight simulations in one second; the
run is 152 s, dominated by the 26 s load and 22 s of rank arrays. No
parallelism was needed, and CLAUDE.md's "every guess here has been wrong" held
again — I was about to fan a 25-second job across eight processes.

## 9. Files

`data/d329_legwise.json` · `scripts/run_d329_legwise.py`

---

## 10. ADDENDUM, 2026-09-05 — what `skew_63`'s short leg actually shorts, and 29% of it is a takeover target pinned at the deal price

Appended after two diagnostics run on the question "where does `skew_63`'s
edge come from" (`scripts/d329_skew63_anatomy.py`,
`scripts/d329_skew63_short_leg.py`, outputs in
`data/d329_skew63_diagnostics.txt`). Not pre-registered; a diagnostic of a
result, filed as one.

### 10.1 The score is a one-day jump detector

`skew_63` is the sample skewness of the last 63 daily log returns. On 63
observations the third moment is the largest single |return|. The name it
ranks first from the short end has, at the median, a **+41.4%** single day in
its window and a worst day of **−3.6%** — quieter than the universe's −5.2%.
The name it ranks first from the long end has a **−36.2%** day. Both extremes
are "the stock that gapped last quarter."

### 10.2 The shorted names are delisting-adjacent — and they are DEALS, not collapses

| | still live 60 bars later |
|---|--:|
| rank 0 from the short end | **61%** |
| rank 1 | 75% |
| universe | 99% |

**297 of the short leg's 1,024 trades at k=20 (29%) are in a name that leaves
the tape within 60 bars.** For those, the return from entry to the last live
bar: median **+0.4%**, p25 +0.1%, p75 +1.2%. **284 of 297 (96%) end within
±5% of where they were shorted. Zero end below −30%.** Their median daily range
while held is **0.28%** against 1.61% for the survivors.

That is a cash takeover: a +40% gap on announcement, two months pinned at the
offer, delisting at the deal price. **Not one of the 297 is a collapse.**

Three consequences, in order of severity:

1. **The short earns nothing on them** — −5.6 bp per trade gross across the
   297, +14.0 on the 284 pinned ones, which is the market's drift collected by
   being short a zero-return name in a demeaned P&L. Not edge.
2. **They are the reason the leg looked cheap.** Corwin–Schultz estimates the
   spread from the daily range, and a pinned stock has almost none: **6.2 bp**
   on the dying names against 9.0 on the survivors. D326's unexplained 4.5×
   cost coverage, D327/D328's "cheapest names in the study," and the three
   zero-spread degenerate cells in §5 are all this. **A range-based spread
   estimator prices a pinned takeover target as nearly free to trade.**
3. **They are the names a short cannot actually be put on.** Announced deal
   targets are the most crowded shorts in the market (merger arbitrage), borrow
   is scarce and expensive, and the residual risk — a deal break — is a gap
   *up* against the short. None of that is in the cost model, which charges
   6.2 bp.

### 10.3 The edge that remains is in the survivors, and it is a two-sided lottery

The 727 trades whose name survives earn **+47.3 bp per trade gross** — a real
post-jump reversal in names that gapped +30–40% and stayed listed. But
reporting rule 2 on the whole leg:

```
mean +32.0   median +126.3   win 73%   skew -3.23   kurtosis +83.4
ex-top-1%  -19.0     ex-bottom-1%  +97.6     trimmed-both  +46.8
top 1% of trades = 159% of P&L    top 5% = 326%    bottom 1% = -203%
```

**The mean is a quarter of the median** — the tell that a tail is doing the
work, and here it is *both* tails. Ten trades make 159% of the P&L and ten
lose 203%; the bottom 1% for a short leg is the squeezes. The symmetric trim
at **+46.8** is the honest central number (CLAUDE.md: dropping only winners is
a flag, not a verdict), and it is positive — but the book will live in its
tails, and 29% of its trades are in names it cannot borrow.

### 10.4 What this does to §1–§6

- **§3's "skew_63 owns the short leg, first of 44" stands as measured** and
  is now explained: it owns it because it is the best jump detector in the
  set, and the enumeration control shares the cost model's blind spot, so the
  ranking is fair among the 44 and mis-costed for all of them.
- **§1's +63.26 per trade and 120 bp round trip are overstated** by whatever a
  borrow-cost model would charge on the 29%. Not quantified here; the record
  does not promote and this is a further reason it should not.
- **The construction finding stands** — leg ownership is real and exact —
  and the specific short leg needs a filter that a pre-registration must
  declare: *no name whose window contains a single day above +X%*, or an
  event-driven exclusion of announced deals, which this fixture cannot supply
  (its event file carries dividends and splits only).
- **`max_ret_21` carries the same signature by construction** (Spearman +0.22
  with `skew_63`, and it *is* the biggest-day score). Any short leg built on it
  inherits this.

### 10.4a AMENDMENT, 2026-09-05 — §1's +63.26 is the top of a bound

D330 B applied a causal pinned-name filter to `skew_63`'s short leg. It
caught 71% of the pinned trades and also removed 39% of the survivors, so the
filtered book is *over*-filtered and the unfiltered one is deal-contaminated.
**The honest per-trade number for LW at k=20 is between +51.05 and +63.26, and
its net Sharpe between +0.224 and +0.434.** At either end it beats both
parents, so §3's leg-ownership finding stands; §1's point estimate does not.
See [D330 RESULT](D330-RESULT-the-tape-cannot-separate-deals-from-reversals.md).

### 10.4b AMENDMENT, 2026-09-05 — `skew_63` is retired as a short; the pairing's short leg is vacant

D331 applied SEC EDGAR target-specific deal filings to the score. With the
deals removed, `skew_63`'s short leg nets **−24 to −30 per trade at the old
cost basis and −61 to −65 at the published one** (second and first EDGAR
passes); its symmetric book is −9 to −11 bp/bar.
Its +16.6, its 7.7 bp half-spread, its "first of 44" in §3, and D326's 4.53×
coverage were the pinned deal targets, entirely. **`skew_63` is retired as a
short signal.** The leg-wise *construction* stands — `[L]` and the enumeration
method are unchanged — and §3's Direction A must be re-run under the deal
filter and the published spread convention before any short partner is named
for `hist_L`-long. Under those, LW_F1 is +20.04 per trade and **−10.80
bp/bar**: a losing book whose long leg carries a losing short leg.

### 10.5 Two errors in my own diagnostics, for the record

The first anatomy script reduced a 414M-element rolling window along a 12 KB
stride and was killed at ten minutes; transposed so the window axis is
contiguous it takes one second. The second re-read `z["skew_63"]` from the
compressed archive on every loop iteration — 12,500 decompressions of a 53 MB
array — and took 690 s on a job that is otherwise instant. Both were inline
`python -c` blocks rather than scratchpad scripts, which is the habit CLAUDE.md's
"Write tool over long heredocs" exists to stop, and both ran in the foreground
past the two-minute rule. The committed scripts have neither defect.
