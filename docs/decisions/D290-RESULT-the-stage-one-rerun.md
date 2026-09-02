# D290 RESULT — the stage-1 re-run, and four things the pre-registration could not have asked

**Status:** COMPLETE. Pre-registered at [`e21526f`](D290-the-stage-one-rerun.md),
amended at `fb6719b` before the runner existed. This record is separate (R8).
**Date:** 2026-09-02
**Area:** Strategy research · **personal track**

**Nothing is closed. Nothing is promoted. The holdout was not read.** Stage 1
spends nothing scarce, so the output is a ranking.

---

## The screen validated exactly

`hist_L` on the spread construction peaks at N=25, k=5, **t +2.858** against
D286's published **+2.86** — delta **0.002**. A miss would have made the run void
rather than negative. It did not miss.

## Predictions, as written

| | prediction | outcome |
|---|---|---|
| **P1** | `hist_L` reproduces D286 | **CONFIRMED**, delta 0.002 |
| **P2** | name split shrinks the top candidate ≥ 40% | **NOT CONFIRMED** — 31%. It generalises better than I predicted |
| **P3** | nothing works SHORT-ONLY | **FALSIFIED** on the letter — 7 candidates positive with min z > 0 and CV t > 0 |
| **P4** | risk terms beat rotation, fail tail-randomised | **FALSIFIED** — `ivol_21`, `beta_63`, `max_ret_21`, `rvol21`, `atr_norm` all show tail z ≥ rotation z, the *opposite* of D283/D284 |
| **P5** | something clears on spread | **CONFIRMED** — 24 of 51 survive all three nulls |
| **P6** | `close_in_range` retains ≥ 60% on CV | **CONFIRMED** — 69% |

**P4's failure is the more interesting one.** The tail tax was the programme's
standing explanation for why risk-selecting signals appear to work. On this
fixture it is not the mechanism, and D283's finding needs revisiting on its own
terms.

---

## Four things learned AFTER the pre-registered run

All post-hoc, all disclosed, all free — no holdout, nothing closed.

### 1. The ranking statistic has a blind spot, and it is the one I called honest

**Name-split CV cannot see microstructure.** An entry artifact generalises across
names perfectly well, so `lower_wick` posted **CV +6.19** on an effect that keeps
**−11%** of itself after one skipped bar. CV asks *does this hold on names I have
not seen*. It does not ask *is this real*, and D290 shipped believing it did.

### 2. The skip-a-bar test inverts the headline

Waiting one bar before entering: **32 survive, 15 collapse, 4 partial**. Every
axis-B leader collapses at its own peak — `close_in_range` **+2%**, `lower_wick`
**−11%**, `body_frac` **−14%** — and all three peaked at k=1. The candidates that
survive almost untouched are ones D290 ranked far lower: `price_log` 98%,
`dist_52w_high` 97%, `rsi` 86%, `macd_hist` 77%.

**The split is by horizon, not by axis.** A k=1 or k=2 peak does not survive
waiting a bar; a k ≥ 5 peak mostly does.

### 3. The k=1 edges are entirely OVERNIGHT, and uncapturable

The session decomposition composes exactly — overnight + intraday equals the
price return on 4,135,181 cells to **4.44e-16**.

| candidate | k=1 total | overnight | intraday |
|---|--:|--:|--:|
| `close_in_range` | +50.4 (t +15.7) | **+51.1 (t +26.5)** | **−1.2 (t −0.4)** |
| `lower_wick` | +16.8 (t +8.8) | +16.8 (t +15.1) | +0.1 |
| `wick_asym` | −19.3 (t −10.5) | −22.1 (t **−21.8**) | +2.8 |

The open→close segment carries nothing. Entering at open[t] instead of the close
that generated the signal: `close_in_range` keeps **−2%**, `lower_wick` **+1%**,
`body_frac` **−62%**.

### 4. It is NOT demonstrably bid–ask bounce — and I said it was

Bounce magnitude is proportional to the spread. Rebuilding each book inside
liquidity terciles (mean half-spread **18.2 vs 94.9 bp/side**, a **5.2×** gap), a
pure bounce edge should scale by about 5.2×.

- `close_in_range` **1.2×** · `lower_wick` **2.0×** · `body_frac` **0.8×** — nothing like it
- but `rel_vol` **3.0×**, `vol_z` **3.1×**, `dollar_vol` **4.2×** — the *volume*
  signals scale as bounce predicts

So the honest statement is narrower than the one I made: the axis-B k=1 effects
are a **real overnight close-to-open reversal**, enormous in `t`, and
**uncapturable**. The mechanism is not settled, and the scaling evidence points
away from quoted-spread bounce. The volume signals are the ones that look like it.

---

## The unified ranking

Four questions, asked in order, none of which substitutes for another:

1. **Is it real?** `min z > 0` across rotation, permutation and tail-randomised.
2. **Does it generalise?** `CV t > 0` on unseen names.
3. **Can you catch it?** open-entry `t ≥ 2` — the question the skip test *could
   not* answer, because skipping removes a real fast signal and an entry artifact
   alike.
4. **Does it pay?** effect against the **measured** round trip on names actually
   held. Reported, never used to rank — D289's amendment defers magnitude.

**TIER 1** = real, generalises **and** capturable. **TIER 2** = real and
generalises but not capturable. **TIER 3** = fails a null or the name split.

### SPREAD — dollar-neutral. 13 of 51 in tier 1

| ax | candidate | N | k | bp | CV t | min z | open bp | **open t** | kept | × bar |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| G | **price_log** | 50 | 40 | +431.7 | +3.03 | +3.64 | +400.9 | **+4.48** | 93% | **1.96** |
| A | macd_hist | 50 | 20 | +54.4 | +1.79 | +3.21 | +48.2 | +3.72 | 86% | 0.34 |
| A | rsi | 10 | 16 | +113.5 | +1.66 | +2.96 | +95.9 | +3.48 | 87% | 0.54 |
| G | dist_52w_high | 25 | 20 | +216.0 | +0.95 | +2.82 | +168.6 | +3.22 | 87% | 0.90 |
| F | on_persist | 10 | 30 | +72.1 | +0.73 | +0.42 | +80.5 | +2.98 | 99% | 0.47 |
| G | rev_5 | 50 | 5 | +22.3 | +2.13 | +1.73 | +19.5 | +2.56 | 89% | 0.09 |
| H | **choch_dist** | 5 | 40 | +738.3 | +0.96 | +1.18 | +744.9 | +2.50 | 102% | **2.43** |
| H | retrace_leg | 10 | 2 | +34.6 | +1.23 | +2.48 | +20.8 | +2.39 | 60% | 0.18 |
| G | skew_63 | 25 | 40 | +168.4 | +0.71 | +1.79 | +128.6 | +2.35 | 84% | 0.80 |
| A | macd_line | 50 | 5 | +30.7 | +1.89 | +2.46 | +20.9 | +2.32 | 71% | 0.20 |
| A | hist_L | 25 | 5 | +52.5 | +1.31 | +1.12 | +40.7 | +2.30 | 78% | 0.20 |
| G | rev_21 | 3 | 10 | +240.6 | +1.41 | +1.07 | +210.0 | +2.27 | 88% | 0.58 |
| D | dist_lvn | 25 | 10 | +39.9 | +0.14 | +1.60 | +30.5 | +2.25 | 85% | 0.22 |

**Only two clear cost**: `price_log` at 1.96× and `choch_dist` at 2.43×.

### SHORT-ONLY — the personal track's objective. **1 of 51 in tier 1**

| ax | candidate | N | k | bp | CV t | min z | open bp | open t | kept | × bar | tier |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| H | **retrace_leg** | 5 | 1 | +13.2 | +0.37 | +3.03 | +13.2 | +2.03 | 96% | **0.14** | **1** |
| B | close_in_range | 3 | 1 | +37.0 | +6.19 | +12.08 | +7.4 | +1.96 | **19%** | 0.43 | 2 |
| G | skew_63 | 3 | 5 | +116.9 | +0.29 | +1.87 | +71.7 | +1.71 | 60% | **1.13** | 2 |
| F | id_mean | 10 | 1 | +18.5 | +0.50 | +2.23 | +12.9 | +1.57 | 67% | 0.10 | 2 |
| B | lower_wick | 3 | 1 | +19.0 | +2.82 | +7.77 | +3.6 | +1.14 | 18% | 0.25 | 2 |
| B | body_frac | 3 | 1 | +18.1 | +2.26 | +7.37 | **−3.2** | −0.87 | −17% | 0.20 | 2 |

**The single tier-1 short candidate earns 0.14× its own round trip**, and that
bar excludes borrow, which this fixture cannot measure. **P3 is falsified on the
letter and stands on the substance: there is no tradeable short here.**

### LONG-ONLY — 1 of 51 in tier 1, and it barely qualifies

`close_in_range` at N=50, k=40: +244.5 bp, CV t +14.87, **min z +0.17**, 2.53×
cost. Every other candidate posts CV t of +11 to +15 and **fails the nulls** —
`mass_imbalance` −2.72, `rel_vol` −4.58, `gap_frac` −6.19.

**Fifty of fifty-one long-only books are market drift.** This table is the
clearest demonstration in the study that the nulls do work: without them, every
one of the 51 looks like a strong signal.

---

## Ledger

| | |
|---|---:|
| **holdout reads spent** | **0** |
| holdout reads, whole programme | **0** |

In-sample looks disclosed and not priced, per D289's amendment: 51 fresh, plus
the post-hoc skip, entry, tercile and independence probes. **No primitive has
touched the holdout**, so all 51 remain holdout-eligible.

## Known limits of this study

- **`on%` is computed at k=1 for every candidate**, including those peaking at
  k=40, where it is not a meaningful decomposition of the peak cell.
- **The tight liquidity tercile is degenerate** — 0.3 bp/side, because
  Corwin–Schultz clamps negative estimates to zero. The 355× wide/tight ratio is
  unusable; wide/mid at 5.2× is the benchmark used throughout.
- **Borrow is absent from every short cost bar.** The fixture cannot measure it.
- **`price_log` leans on one era** — +239 / **+1156** / +436 across
  pre-2020 / 2020 / post-2020 — and it is the score that required an as-traded
  reconstruction after a fixture-level look-ahead was found. It is simultaneously
  the best-ranked candidate and the least trustworthy.
- **No independence gate was pre-registered.** Measured after the fact: the top
  14 by spread CV carry **4.79 effective inputs**, and the momentum family sits at
  ρ 0.5–0.84.

## What this hands to stage 2

Not a promotion — a shortlist and a warning. The spread book has thirteen real,
capturable candidates of which two clear cost. The short book has one, at 0.14×.
And the study's own ranking statistic needed three post-hoc tests to become
trustworthy, which is the finding most worth carrying into the next
pre-registration.

---

# ADDENDUM 2 — gates 1g, 1h and 1i applied retroactively

Stage 1 spends nothing scarce, so applying new gates to an already-burnt fixture
costs nothing and invalidates nothing. **The holdout remains unread.** These are
retroactive applications, not a re-run — and they do NOT make D290 a
pre-registered test of these gates. The gates bind from the next study.

## 1g — turnover: two candidates are not signals

**6 static tilts** under 5% turnover per bar, `price_log` the extreme at **1.9%
and a 51-bar holding run**. It never says *when* to do anything.

**12 with one-sided delisting exposure**, and the volatility family is severe:

| candidate | dead in LONG | dead in SHORT |
|---|--:|--:|
| `vol_ratio` | **66.6%** | 28.6% |
| `rvol21` | **66.4%** | 41.7% |
| `atr_norm` | **65.8%** | 42.1% |
| `ivol_21` | **64.9%** | 42.1% |
| `max_ret_21` | **63.2%** | 41.7% |

**Same frozen-tape mechanism as AVNS.** Lowest ATR does not mean a calm stock, it
means a tape that has stopped — a takeover or a halt — which is a delisting. The
low-volatility end of every ranking is structurally full of about-to-die names.

## 1h — the direction D290 never scored

51 candidates × 50 draws × 3 nulls × both directions, **21 minutes**. **11
reversed candidates clear all three nulls; 5 are capturable.**

**The miss: `wick_asym`.** D290 put it at tier 3 (−18.2 bp, t −1.79, min z −8.96).

| direction | N | k | bp | t | min z | open t |
|---|--:|--:|--:|--:|--:|--:|
| forward | 25 | 30 | −18.2 | −1.80 | −8.96 | +0.36 |
| **reversed** | 25 | 1 | **+19.3** | **+10.51** | **+5.07** | **−1.77** |

Reversed it is the second-strongest thing in the study by evidence. **Gate 1h
found it and gate 1e disqualified it** — open-entry t −1.77, 115% overnight, the
same uncapturable close-to-open effect as `close_in_range`. The two gates working
as intended.

## 1i — and where the peak sits demotes two of the five

| construction | corner (N=50, k=40) | edge | interior |
|---|---|---|---|
| long | **51 of 51**, 1 passes nulls | — | — |
| short | — | **0 of 6 pass** | 19 of 45 |
| spread | 1 of 1 | 7 of 13 | 16 of 37 |

Tier 1 across both directions is **5 candidates** — but `range_frac` and `rvol21`
sit at the **corner** with min z of only **+0.32 and +0.42**, and `rvol21` is one
of 1g's 66%-dead-leg candidates. **`fvg_signed` is the only genuinely interior
tier-1 candidate in the study**, at +32.8 bp and 0.21× cost.

## The conclusion does not move

The short book — the objective — still has nothing tradeable. The one candidate
clearing cost is `choch_dist` at 2.41×, on CV t +0.96 and 25.7% coverage, with
its peak at max k and therefore **horizon-unresolved**.

**And a reproducibility defect, found while optimising and fixed prospectively:**
`run_stage1_rerun.py:370` seeds with `SEED + hash(c) % 100000`, and Python
randomises `hash()` per process. **D290's z-values are valid but cannot be
regenerated.** `d290_direction_nulls.py` uses `zlib.crc32` instead.
