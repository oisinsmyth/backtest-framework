# D271 — The trade-level anatomy — RECONSTRUCTED POST-HOC

**Status:** **RECONSTRUCTED POST-HOC. RUN AND CLOSED, descriptive.** **Remove the best 1% of trades
and all three surviving constructions lose money.**

> **THIS RECORD WAS WRITTEN AFTER THE RUN — 2026-09-02, from the committed scripts, the committed
> JSON, the rendered report and the commit messages. It is NOT a pre-registration and carries NO
> pre-registration claim.** [R8](../RULES.md#r8) requires the hurdles to be committed before the
> data is touched; nothing of the sort exists for D271, and no such claim may be read into this
> file. **Its Predictions section is OMITTED for exactly that reason** — a prediction that is
> written down after the answer is known is not a prediction, and back-filling one here would be
> the single worst thing this record could do. Every figure below is traceable to a named artefact;
> where a figure is not, it is listed under *What is not recoverable* rather than estimated.

**Run:** 2026-09-01 · commits `0908d70` (the study) and `234373c` (the correction)
**Record written:** 2026-09-02
**Area:** Strategy research · **personal track**
**Ledger: unmoved.** See *Ledger* below, including the tension with D264's own precedent.

---

## What this was

**A descriptive anatomy of the individual trades behind three already-measured constructions.** No
hurdle was run, no cell was scored, no rule was proposed. The docstring of
`scripts/d271_trade_anatomy.py` states the motive in one line, and it is the right one:

> *"every number reported so far has been a mean and a mean cannot distinguish a broad edge from
> one that lives in a handful of trades."*

**The three, and why these three:** they are the only things in the single-name intraday programme
that survive a properly-constructed null.

| construction | what it survived |
|---|---|
| **LOW · `S2_short_intra`** | [D264](D264-the-intraday-short-on-single-names.md) hurdle H, **both legs, 97.2th / 97.9th** |
| **HIGH · `S1_short_intra`** | D264 hurdle H, **both legs, 96.9th / 99.7th** |
| **LOW · `rel_vol` Q5** | [D270](D270-volume-structure-retest.md) M1 (monotone 5/5) and M3 (**−3.68 bp spread against a 2.56 bp best-of-15 shuffle floor**) |

**The `rel_vol` arm is an anatomy of an already-measured bucket, not a new book.** D270 measured
the mean forward move of the Q5 bucket; this shows the distribution behind that mean. D270's stop
is not reopened by it.

## What was computed, and why each earned its place

Taken from the script's own docstring, which is where the reasoning for this study lives:

| | |
|---|---|
| **P&L distribution** | the ask — reported **gross**, with the round-trip cost bar drawn on it, because gross-against-cost is the whole question |
| **skew and kurtosis** | a short *should* be negatively skewed — small wins, rare large losses. **Positive skew in a short book means the edge lives in the tail and is fragile** |
| **tail concentration** | share of total P&L from the top 5% of trades |
| **P&L by year** | [FINDINGS §6](../FINDINGS.md): measured effects in this programme are frequently one era, and this sample contains 2020 |
| **per symbol** | four names is not four independent bets; [R10](../RULES.md#r10) applies |
| **by entry bucket** | [D265](D265-the-entry-time-reconciliation.md) found EARLY entries carry S2 entirely (**+6.28 bp at 1.57× the bar, against −3.84 bp LATE**) |

**Fixture:** `single_name_intraday_15m_panel.csv.gz` — 8 survivor names, 55,004 bars, 2,117
sessions, 2018-01-02 → 2026-08-26. Trades use **the book's own exit**, flat at every session close.
**P&L is gross log return, negated for the short, in basis points.**

---

## DEFECT — the volume arm counted OVERLAPPING WINDOWS as trades, and it halved a t-statistic

**This is the most important thing in the record and it is a correction to D271's own first
reading.** Found by the principal reading the `rel_vol` distribution as *"oddly perfect"*, fixed in
`234373c`, and now carried in the script's docstring so it cannot be lost.

`score_trades` originally admitted an entry on **every** qualifying bar. Consecutive top-quintile
bars therefore produced 8-bar windows **sharing seven of their eight bars**:

| | n | mean | t |
|---|---:|---:|---:|
| **overlapping — as first reported** | **43,204** | +1.97 bp | **+5.30** |
| **non-overlapping — correct** | **13,752** | **+1.57 bp** | **+2.31** |
| *unconditional, all bars, for reference* | *216,016* | *−0.59 bp* | *−4.63* |

**43,204 "trades" from four names over 8.25 years is 1,309 per symbol per year against 252
sessions.** A book cannot open 1,300 positions in 252 sessions. **Those were overlapping
observations wearing a trade's clothes, and pooling them inflated the t-statistic from 2.31 to
5.30.** The fix: a position is held to its horizon before another may open — which is what a book
would actually do.

**And 2.31 is still not the honest figure.** The four LOW names carry only **1.87 effective
instruments** (D264), so priced for cross-correlation the t falls to **roughly 1.6** — an estimate,
labelled as one, from `234373c`.

### The second half of the same correction: the symmetry was the tell

**The percentile ratios sit at 1.04, 1.08 and 1.07 across p25/p75, p5/p95 and p1/p99 — a CONSTANT
tilt at every point in the distribution.** That is a **location shift**, not a change of shape. A
real directional edge fattens the winning tail relative to the losing one and the ratio grows
outward; this does not.

**Against the unconditional 8-bar distribution the conditioning moves the mean +2.15 bp and widens
the standard deviation from 58.8 to 77.2 bp — a 31% increase.** So:

> **High relative volume selects VOLATILITY. Direction is a side effect riding on it.**

The cost bar is 4.00 bp, so the shift delivers about half of it — consistent with D270's **0.92×**,
measured a different way and arrived at independently.

### And a third defect, fixed in the same commit

**The report's summary table was originally transcribed by hand rather than computed from the
data.** A hardcoded table drifts the moment the data does, **which is exactly what this correction
would have caused.** `scripts/d271_build_report.py` now computes it (`# Computed, not
transcribed`).

---

## THE FINDING — remove the best 1% of trades and all three lose money

Computed by `d271_build_report.py` from `data/d271_trade_anatomy.json`, post-correction:

| construction | mean | **excl. best 1%** | trades carrying 100% of the profit | share |
|---|---:|---:|---:|---:|
| **LOW · S2 short** | **+3.12 bp** | **−0.63 bp** | **12** / 1,507 | **0.80%** |
| **HIGH · S1 short** | **+5.13 bp** | **−1.57 bp** | **37** / 5,338 | **0.69%** |
| **LOW · `rel_vol` Q5** | **+1.57 bp** | **−2.37 bp** | **33** / 13,752 | **0.24%** |

**The third column is the number of trades containing one hundred percent of the net profit.**
Everything after them is, on net, giving it back. The cumulative-P&L curve overshoots 100% within
the first few percent of trades and then descends for the rest of the sample.

**Note the correction moved this row too:** pre-correction the `rel_vol` figure was *170 of 43,204
(0.39%)*; de-overlapped it is **33 of 13,752 (0.24%)**. Both are in the record because the first
was published.

---

## The full distributions, as scored

Straight from `data/d271_trade_anatomy.json`. **All P&L gross, basis points per trade.**

| | LOW · S2 short | HIGH · S1 short | LOW · `rel_vol` Q5 |
|---|---:|---:|---:|
| trades | 1,507 | 5,338 | 13,752 |
| **round-trip cost bar `2c`** | **4.00 bp** | **12.84 bp** | **4.00 bp** |
| **mean** | **+3.12** | **+5.13** | **+1.57** |
| **mean ÷ cost** | **0.78×** | **0.40×** | **0.39×** |
| median | **+0.00** | **−5.48** | **−0.00** |
| sd | 100.6 | 172.4 | 79.5 |
| hit rate | 50.0% | 47.7% | 49.8% |
| avg win / avg loss | 72.4 / 66.3 | 127.9 / 107.1 | 51.0 / 47.4 |
| payoff | 1.09 | 1.19 | 1.08 |
| **skew** | −0.07 | **+0.19** | **+1.18** |
| **kurtosis** | **10.7** | **21.2** | **24.5** |
| mean hold | 17.7 bars | 9.9 bars | 7.1 bars |
| **share of trades beating the cost bar** | **47.7%** | **43.3%** | **46.0%** |
| top 5% of trades, as share of total P&L | **386%** | **412%** | **632%** |
| p1 / p50 / p99 | −252 / +0 / +269 | −411 / −5 / +489 | −212 / −0 / +233 |

**Not one of the three has a mean that reaches its own cost bar.** 0.78×, 0.40×, 0.39×.

### What the shape means

- **Kurtosis 10.7 / 21.2 / 24.5 against a normal's 3.** Violently fat-tailed, which is why a mean
  computed over them is fragile.
- **Two of three are POSITIVELY skewed** (+0.19, +1.18). **In a short book that is the wrong
  direction:** profit arrives as rare large gains rather than as a steady harvest, and rare large
  gains are exactly what a backtest cannot promise will recur.
- **Median P&L is zero or negative in all three** — the typical trade makes nothing. Hit rates
  47.7–50.0% with payoffs 1.08–1.19: on the body of the distribution these are **coin flips with
  almost no asymmetry.**
- **Under half of trades beat the cost bar** in every construction.

### No era carries it, and no single name carries it cleanly either

| year | LOW · S2, mean bp | HIGH · S1, mean bp | `rel_vol` Q5, mean bp |
|---|---:|---:|---:|
| 2018 | **+17.23** | +11.23 | +6.17 |
| 2019 | +4.21 | +4.12 | −0.96 |
| 2020 | +4.56 | −0.47 | +6.41 |
| 2021 | +0.08 | +8.21 | +0.39 |
| 2022 | +4.88 | +1.91 | +0.14 |
| 2023 | +3.52 | +0.12 | +3.55 |
| 2024 | +0.88 | +8.90 | −2.06 |
| 2025 | **−6.11** | **+15.45** | +0.20 |
| 2026 | −1.29 | −4.06 | −0.14 |

**S2's mean per trade falls from +17.2 bp in 2018 to −6.1 in 2025. S1's is lumpy rather than
trending** — its two best years are 2025 and 2018. **Neither looks like a stable process observed
over eight years**, and FINDINGS §6's reflex applies.

**Per symbol, with R10's warning binding at the symbol level:**

| | LOW · S2 (n, mean bp) | HIGH · S1 (n, mean bp) |
|---|---|---|
| | LMT 389, **+10.08** · MO 381, +3.81 · **PG 364, −2.86** · PM 373, +1.00 | YELP 1,336, +7.60 · RH 1,351, +6.77 · CLF 1,270, +6.15 · **SM 1,381, +0.22** |

**S2 has one of four names negative and LMT doing most of the work.** Four names is not four
independent bets — **1.87 effective instruments on LOW**, 3.02 across all eight (D264).

### The entry-bucket cut reproduces D265, on trades rather than on bars

| bucket | LOW · S2 | HIGH · S1 | `rel_vol` Q5 |
|---|---:|---:|---:|
| **EARLY** (bars 1–8) | **+6.28 bp** (n 1,205) | **+7.32 bp** (n 3,217) | **+3.86 bp** (n 5,401) |
| MID (9–17) | −15.68 (n 144) | +5.73 (n 918) | +0.58 (n 4,749) |
| LATE (18+) | −3.84 (n 158) | −1.18 (n 1,203) | −0.57 (n 3,602) |

**EARLY is the best bucket in all three, LATE the worst in all three.** This is D265's result
recomputed on the trade level and it agrees to the decimal on LOW · S2 (+6.28 / −3.84). **It is
not a rule and D265 already priced what an EARLY-only book earns: +0.38%/yr.**

---

## What this overturns, and what it does not

**It does not overturn the nulls. The timing is not random, and that was measured correctly.**
D264's rotation percentiles stand at 97.2/97.9 and 96.9/99.7, and D270's monotone ordering stands.

**What the distribution adds is that beating a rotation null and having a repeatable per-trade edge
are DIFFERENT CLAIMS, and only the first is established.** [FINDINGS §3](../FINDINGS.md) —
*beating a null is not having a strategy* — is usually about exposure and structural drag. **This
is a second, independent route to the same place: a mean carried by twelve trades is not a
process.**

## Report

`docs/results/trade_anatomy.html`, built by `scripts/d271_build_report.py` from the committed JSON.
Self-contained, inline SVG, no external assets, both themes. **Republished at the same URL after
the correction**, which is why the summary table is now computed rather than transcribed.

---

## Ledger — unmoved, and the tension is disclosed rather than buried

| count | N |
|---|---:|
| fresh cells scored | **0** |
| carried | unchanged from D270's **46,209** |

**D271 moved the ledger by zero, and that is verifiable rather than asserted:**
[D272](D272-the-volume-profile-as-a-positional-input.md)'s ledger carries **46,209 "from D270"**,
skipping D271 entirely. The commit `0908d70` states *"ledger unmoved"*.

**The tension, stated plainly because it cuts against the study:** D264's own Part A anatomy **was**
counted — 23 looks — on the reasoning that *"it is a search over the same data"*. D271 is also an
anatomy over the same data. **The difference claimed is that D271 selects nothing: the three
constructions, the quintile cut and the 8-bar horizon were all fixed by D264 and D270 and are
already in the count.** That is a defensible line and it is not an obviously correct one. **The
zero as committed stands and is not restated here** — under [R13](../RULES.md#r13) this record
keeps the convention it was run under, and R13 itself is explicit that records D247–D276 are not
restated.

---

## WHAT IS NOT RECOVERABLE FROM THE ARTEFACTS

Listed so that nothing here is mistaken for a complete account:

1. **Any pre-registration.** **There was none.** No commit before `0908d70` contains a D271 design,
   hurdle set or prediction. This record cannot supply one and does not try.
2. **Hurdles and predictions.** None were declared, because the study was descriptive. **The
   Predictions section of this record is omitted, not empty.**
3. **The pre-correction `rel_vol` distribution beyond three numbers.** `data/d271_trade_anatomy.json`
   was overwritten by the corrected run. Only **n = 43,204, mean +1.97 bp, t = +5.30** and the
   *170 of 43,204 (0.39%)* concentration row survive, from `234373c` and the pre-correction report
   text. **Its skew, kurtosis, percentiles and per-year table are gone.**
4. **The t-statistics of the two short arms.** The script computes no t-statistic; only the
   `rel_vol` arm's t values were ever quoted, and those come from the commit message rather than
   from a committed artefact.
5. **The exact derivation of the "roughly 1.6" cross-correlation-adjusted t.** `234373c` gives it
   as an adjustment using LOW's 1.87 effective instruments. **It is an estimate and is labelled as
   one in both places.**
6. **The unconditional-distribution comparison** (216,016 bars, −0.59 bp, t = −4.63, sd 58.8 → 77.2,
   mean shift +2.15 bp, percentile ratios 1.04/1.08/1.07) **is not written to any file.** It exists
   only in `234373c` and in the prose of `docs/results/trade_anatomy.html`, and re-deriving it
   requires re-running the script.
