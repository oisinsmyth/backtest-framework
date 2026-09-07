# D365 RESULT — the momentum buffer book clears every null and is not a size book; its median trade loses, thirteen names are half its P&L, and era 1 pays nothing

**Status:** RESULT. Pre-registered at `48410cb`, runner at `5763b1a` — both before this file
existed (R8). OHLCV only; **the holdout fixture was not read** (the file-open audit refused
the probe). `keep_v2`, F0, next-open fill, hedged, PUB primary and PB beside.
**Date:** 2026-09-07
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is a book. Nothing is promoted. The avenue is the principal's (R15).**

**Selection history, as the pre-registration required.** The primary cell came from an
eleven-combination screen on this same fixture hours earlier, and the declared grid adds
eight more. This is a **within-sample confirmation with nulls**, in the shape of D362, and
not a discovery. Cross-sectional momentum is the most published anomaly in finance; nothing
here is a claim to have found it. What is new to *this record* is the shape.

---

## 1. The verdict

**Five of eight, and the load-bearing one held.** Buying the top 5% of twelve-month momentum
and holding until a name falls out of the top 20% earns **+2.59 bp/bar net of the published
spread**, a hedged Sharpe of **0.417**, about **+6.5% a year**, on a book of 53 names turning
over 1% a day. It clears all three nulls. It is **not a size book**. And three of its four
failures are about how the money arrives, not whether it does.

| primary cell, 95/80, open fill | value |
|---|--:|
| gross | +3.37 bp/bar |
| cost (round trip 74.7 bp × 1.01% turnover) | 0.77 |
| **net PUB** | **+2.59** |
| net PB | +3.05 |
| net Sharpe | 0.417 |
| members when deployed | 53.3 |
| mean holding | 99 bars |
| trades | 1,709 |

**The nulls, and they are not close.** The observed net sits above the p95 of every one.

| null, primary cell | p50 | p95 | observed |
|---|--:|--:|--:|
| ROT, 24 rank rotations | −5.74 | −2.75 | **+2.59** |
| A′, 200 per-name time rotations | +0.78 | +1.78 | **+2.59** |
| C, 1,000 random directions | −0.03 | +2.85 | +3.44 |
| grid-max under shared offsets | −3.22 | −1.02 | +2.96 (p = 0.040) |

**One caveat on ROT, stated rather than banked.** D348's rotation wraps, so a rotated book
exits any name that climbs past the wrap point and churns at **9.9× the observed turnover**.
Cost scales with turnover, so ROT's *net* is penalised by construction — the D291 rule that a
control must share the treatment's nuisance. The comparison that is fair is gross, and the
observed clears there too: **+3.37 against a ROT gross p95 of +0.72.**

## 2. Stage 0 — the question that could have killed it, answered

The hedge is the floored universe equal-weighted, which is small-cap tilted, and momentum
winners are not small. Beta-adjustment does not fix a size tilt. So the drift was re-measured
against a **dollar-volume-decile-matched hedge** that excludes the name itself.

| top decile drift, bp per name-bar | value |
|---|--:|
| against the equal-weight universe | +3.87 |
| **against same-DV-decile peers** | **+3.97** |

**103% of it survives.** The drift is marginally *larger* against size-matched peers, not
smaller. The whole rank-band profile agrees: the two hedges differ by at most 0.06 bp in any
band, and the profile is U-shaped and top-heavy — (0,10] +0.64, then −0.74, −0.25, −0.05,
+0.78, and **+3.87 in the top decile**. Only the winners pay, and it is not a monotone
momentum gradient.

**The rival hypothesis was run as a construction, not a statistic.** The identical buffer
book, ranked on volume instead of momentum, earns **−0.99 gross** on the pre-registered
score and **−0.10** on the dollar-volume *level* (Q2's clause was written against
`dollar_vol`, which in this record's cache is a relative-volume *surprise*, so the level
control was added and reported beside it). Ranking on size earns nothing. **This is not a
size book.**

## 3. What failed, and it is the interesting half

**Q3 — the t-statistic.** The two-factor intercept is **+2.856 bp/bar**, positive and large,
but its standard error is 1.638, so **t = +1.74** (Newey-West +1.85). It misses the
pre-registered t > 2 bar. Both of Q3's other clauses held — the DV-matched hedge keeps 105%
of the net, not half. So the failure is not about size, it is about **precision**: a Sharpe
of 0.42 over twelve and a half years is a t of roughly 1.5 to 1.7 whatever way you compute
it. **The permutation nulls and the time-series t are asking different questions and they
disagree.** The nulls say the selection is doing something a random one does not. The t says
the mean is not distinguishable from zero at conventional levels. Both are true and the
record reports both rather than the flattering one.

**Q4 — era 1 pays nothing.** Era 1 is **−0.38 bp/bar** on 54,249 held name-bars; era 2 is
**+3.99** on 115,704. By year the split is stark:

| | |
|---|---|
| positive | 2014 +2.2, 2015 +1.6, 2017 +0.8, 2020 +6.8, 2021 +8.8, 2022 +9.8, 2024 +10.6, 2025 +4.8, 2026 +9.3 |
| negative | 2016 −2.5, 2018 −1.0, 2019 −2.9, 2023 −2.6 |

Everything of size is 2020 onward. The losing years are the known momentum-reversal years.
**A reader should treat this as a six-year result with a seven-year null attached, not a
thirteen-year one.**

**Q7 — nine of thirteen years positive on gross**, eight on net, against a bar of ten.

**Q8 — thirteen names are half the P&L**, of 709 that traded. The prediction was that a broad
premium would be broad, and it is not: holding 53 names at a time produced the same P&L
concentration as this record's two-name books. **Breadth of holdings is not breadth of
outcome**, and that is worth more than the prediction it broke.

## 4. Four groups, per trade

n 1,709 · mean **+334.8** · median **−141.4** · win rate 45.4% · payoff 1.71 · hold 99.4 bars
· skew +3.85 · kurtosis +35.3 · t +4.10 · mean over the round trip **3.37×**.

**The median trade loses money and the mean is strongly positive.** That is the signature of
a positively-skewed strategy: most positions are cut for being wrong and a few ride for a
year. It is the exact mirror of the warning in CLAUDE.md — a mean *below* its median means
the left tail is working; here the mean is 476 bp above its median and the right tail is.

The trims say it is not one trade:

| | |
|---|--:|
| ex-top 1% | +138.0 |
| ex-bottom 1% | +413.9 |
| symmetric 1% trim | +215.9 |

**Even with the best 1% removed the mean is +138, still 1.4× the 99.5 bp round trip.** That
is a materially more robust distribution than anything else in this record.

**Top trade: GME, entered 2020-11-09 at $11.49** (dollar-volume percentile 76), **held 305
bars, +48,938 bp = 8.6% of the P&L.** The buffer is what produced it: the name entered on
momentum in November 2020 and the 20% exit band held it through the squeeze and most of a
year. That is the construction working as designed, and it is also 8.6% of the result resting
on the most anomalous single episode in the sample.

Dead names +110.3 on 330 trades against alive +388.6 on 1,379; the cheaper half +317.1
against +352.6 — no price dependence, unlike every other book here.

## 5. The grid, and the buffer's whole point

| cell | members | turnover | hold | gross | cost | net PUB | Sharpe | %/yr |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 90 / 90 (daily refresh) | 59.5 | 5.93% | 17 | +3.84 | 4.43 | **−0.59** | −0.109 | −1.5 |
| 90 / 80 | 81.9 | 1.40% | 72 | +2.55 | 0.98 | +1.57 | 0.310 | +4.0 |
| 95 / 70 | 62.6 | 0.79% | 127 | +2.91 | 0.59 | +2.32 | 0.404 | +5.8 |
| **95 / 80 (primary)** | 53.3 | 1.01% | 99 | +3.37 | 0.77 | **+2.59** | 0.417 | +6.5 |
| 95 / 85 (grid max) | 47.9 | 1.22% | 82 | +3.93 | 0.96 | +2.96 | 0.441 | +7.5 |

**The daily-refreshed book loses and the identical signal with a buffer earns 6.5% a year.**
The difference is entirely turnover: 5.93% a day against 1.01%, so the toll falls sixfold
while the gross falls a tenth. The jitter across the boundary was noise, not information.
Q5's "against" prediction lost by a wide margin — the gap is +3.18 bp/bar against a 2.00 bar.

**The open fill cost almost nothing** (Q6): +3.43 close-to-close becomes +3.37, a loss of
1.8% of the gross, because the fill convention touches only the 1% of position-bars that are
entries. On the event books it was worth 13.8 bp/bar. **A slow book is nearly immune to the
convention that destroyed the fast ones**, which is the same arithmetic as the cost result
seen from another side.

**All three cost conventions agree here**, unlike D363's fade: held-median 0.775, entry-median
0.825, per-trade 1.000 bp/bar. The names are homogeneous, so the median is not hiding a tail.

## 6. Stop conditions, executed

- **Q1 and Q2 hold** → a broad slow long whose edge is not size and clears every null. By
  R15's criterion it is a signal. Its own out-of-sample design is a separate record and
  **does not touch D357's frozen read**, which stays reserved for the blend.
- **Q3 fails on precision, not on size.** The record carries the t of 1.74 next to the
  Sharpe of 0.42 wherever this cell is quoted.
- **Q4 fails**: the result is era 2's. Anyone acting on it is betting the last six years
  resemble the next six.
- Nothing is promoted. Book: empty.

## 7. Deviations and what the run found

- **The round trip is two crossings, not four.** `G22.costed` prices a two-legged spread
  book; this book has one leg, so the round trip is `2 × half + 2 × commission` — exactly
  `V47.two_c`. [TURN] asserts the factor of two rather than silently halving.
- **`dollar_vol` is a relative-volume surprise in this cache, not a size level.** Q2 was
  scored on the pre-registered score as written and a size-*level* control was added beside
  it. Both reject the size hypothesis; the pre-registration should have named the level.
- **Two gross statistics.** The screen's is a pooled mean over held name-bars; the
  pre-registration's book return is a per-bar series. They differ by membership weighting.
  Every pre-registered target is in the pooled one, so it is the headline, and the per-bar
  series carries vol, Sharpe, maxDD and the splits.
- **A stated weakening of [C].** The pre-registration asks the check to assert both that the
  null's mean is within 3 SE of zero *and* that the observed lies outside it. The first is a
  property of the code and is asserted; the second is a property of the data — it is Q1's own
  evidence — so it is **printed loudly and not raised**, because an assertion there would make
  a negative result unobtainable rather than reportable. In a code comment and in both output
  paths. No other assertion was weakened.
- **2013 is a partial year** (−22.2) with few held name-bars; the "full year" rule is the
  screen's own, at least 500 held name-bars, which yields exactly thirteen.

## 8. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** · **[HOLDOUT-GUARD]** | via the shared prep; 257 opens audited, none under `data/fixtures`, the probe refused |
| **[ID]** | the close-to-close variant reproduces the screen exactly on both reference cells and to 8.9e-16 against its arithmetic |
| **[BUF]** · **[LAG]** | a plain scalar loop equals the vectorised hold state on every bar and name; a second derivation with no sequential state agrees on all nine cells; 25 probes plus a whole-grid probe show moving the raw score leaves rows ≤ t and moves t+1 |
| **[FILL]** | the two fills differ on exactly the 1,709 entry bars and nowhere else |
| **[TURN]** | turnover 1.006% = 1,709 / 53.344 / 3,186 from an independent count; nine statistics equal `G22.costed`'s to 0.0 |
| **[SZ]** | 300 matched pools rebuilt by direct selection to 2.1e-17; the name is never in its own pool; no eligible name-bar lacks a pool |
| **[S]** | +50 bp on BMA 2023-08-29 moves the book's bar by 0.892857 bp = 50/56 and no other bar |
| **[ROT]** · **[A′]** · **[SIZE]** · **[C]** | multisets and counts kept; 1,896,780 rotated scores all within their name's eligible bars; SIZE run as a construction; C's mean −0.59 SE from zero |
| **[6]** | [BUF], [LAG], [FILL], [SZ] and [S] each raise on a deliberately broken input |

**Speed:** self-test 9 s; ROT 0.3 s a shift, A′ 0.4 s a draw; stage 0 3 s; the cell 81 s;
report 61 s; peak working set 1.55 GB.

## 9. What this establishes

1. **The cost problem is a turnover problem, and it is solvable by arithmetic.** The same
   signal loses 1.5% a year refreshed daily and earns 6.5% behind a rank buffer. Nothing
   about the signal changed.
2. **This programme's own conventions hid it.** D300 fixed the book at two names per side for
   a spread construction and that convention propagated. A diversified premium cannot be seen
   through a two-name window, and this is the first broad book the record has ever run.
3. **It is not size, and it is not beta** — 103% survives a size-matched hedge, and ranking on
   volume earns nothing.
4. **But it is era 2's, thirteen names', and a t of 1.74.** A Sharpe of 0.42 over twelve
   years does not reach conventional significance however it is sliced, and the permutation
   nulls it clears are a different question from that one.

## 10. Files

`data/d365_stage0.json` · `data/d365_ctrl_95_80_p0.json` · `data/d365_momentum_buffer.json` ·
`scripts/run_d365_momentum_buffer.py` · reuses `scripts/d348_prep.py`,
`scripts/run_d358_flat_sleeve.py`, `scripts/run_d348_score_rotation_null.py`,
`scripts/run_d351_control_a_on_the_floor.py`, `scripts/d322_four_group_report.py`.
No auxiliary data source; the holdout fixture was not read.
