# D383 RESULT — the time-series screen clears nothing, and the ten cells that "pass" are buy-and-hold

**0 of 572 defined cells clear the §4 floors on bp-per-bar. 10 clear on the primary per-trade
statistic and every one of them is a book that holds all 57 names for the whole sample: exposure
1.000, `n_eff` trades = 1, excess over buy-and-hold at matched exposure 0.00%.** §8's abandon
condition — *"nothing clears §4 on bp-per-bar"* — is **MET**. **Under R15 the decision to close is
the principal's; this record does not close the avenue.**

Pre-registration `af91504`, amended `cb864cb`; runner `scripts/run_d383_ts_structure_screen.py` —
written after both (R8). **Stage-1 screen under R14, signal hunt under R15. Admits nothing.**

**No holdout was read and none could be.** The reserved window (2024-01-01 → 2026-08-26) was cut
from the bar lists in `--prep` and never entered any cache the later stages read.

57 ETFs × **38,648 fifteen-minute mining bars**, 2018-01-02 09:30 → 2023-12-29 15:45.
Artifacts: `data/d383_observed.json`, `data/d383_nulls.json`,
`data/d383_ts_structure_screen.json`, `data/d383_neff.json`, `data/d383_span_census.json`.

---

## 1. What D383 declared, and what was computed

Written out §-by-§ before any scoring code, and checked against the implementation afterwards,
because a runner computing something *adjacent* to its own pre-registration is this programme's
most expensive recurring defect (D384).

| § | declared | computed | match |
|---|---|---|---|
| §1 | `etf_intraday_15m_panel.csv.gz` through **`run_macd_ladder.load_panel`**; 57 × 55,726 15-minute bars; MINING = first bar → 2023-12-31 = **38,648 bars/symbol, 1,497 sessions**; RESERVED = 2024-01-01 on, untouched; `[GATE]` an explicit call because `load_panel` makes none | exactly that. `load_panel` returned **57 × 55,726, 1,955 dividends matched, 0 unmatched**; `[SPLIT]` cut **17,078** reserved bars from the bar lists leaving **38,648**, last bar **2023-12-29 15:45** | ✅ |
| §2 | event = **the percentile of `x[i,t]` within that name's own trailing `x[i, t−W..t−1]`** crossing into the declared extreme decile; **no cross-sectional comparison anywhere**; long-flat, equal-weighted, per name, `lag = 1` | `pct = 100·(#{trailing < x[t]} + ½·#{trailing = x[t]}) / #{trailing finite}`, mid-rank — D382's own `100(r+0.5)/k` written for a window that excludes the ranked point. Nothing in the runner ranks one name against another | ✅ |
| §2 | W ∈ {26, 52, 130, 260, 390, 780}; holds {4, 13, 26, 78}; **26 nominated primary in advance** | all six windows, all four holds, all reported; hold 26 quoted as primary | ✅ |
| §3 | 13 declared directions + 6 undeclared × 2 tails = **25 feature-directions**; **25 × 6 × 4 = 600 cells**; the reversed book of each declared feature **reported separately** and not in the floor | 600 cells, **572 defined**; 13 × 6 × 4 = 312 reversed cells scored and reported separately, **284 defined**, none in any floor | ✅ |
| §4 | two nulls — **rotation** (each name's position series rolled within its own live window) and **matched-count random entry** (which bars a name enters on, at that name's own entry count); floor = **best-of-150 WITHIN EACH HOLD** under **one shared draw** per iteration; **never across holds** | both, 200 draws each. One offset vector and one permutation set shared by all 150 cells in a draw; each hold has its own floor and its own RNG stream. No statistic is ever compared across holds | ✅ |
| §5 | **primary = gross mean per TRADE** against the §4 floors; beside it **bp per BAR HELD**, **excess over buy-and-hold at matched exposure**, **turnover / entries per year / median hold in CALENDAR time before any performance number**, and the **shape across the six windows** | all five; §5.5 (gate 1e capturability, gate 1d′) is **NOT COMPUTED** and is reported as not-computed, which §5 permits only because nothing survived §4 | ✅ |
| §6 | `[SPLIT] [GATE] [LAG] [TS] [DIR] [BH] [POS] [X]` | all eight, plus `[SIGN]` and `[QTY]`; every one shown to **raise** on the input it exists to catch (§6 below) | ✅ |

**One deliberate inherited choice, stated rather than buried.** `MIN_TRAILING_OBS = 20` — the
minimum trailing observations before a percentile is defined — is not in the pre-registration.
It is **D382's own `k < 20: continue`**, taken from the study D383 replaces rather than invented
here. `WARMUP = 1000` bars is likewise set by construction, not by choice: the volume-profile
sensor warms up in 183 bars and the longest window is 780.

**Two constants keep their DAILY meaning at 15 minutes, and this is a caveat, not a defect.**
`FRESH_BARS = 252` (a level older than this is stale) and `VOL_BARS = 21` are one year and one
month on daily bars; here they are ~10 sessions and ~1 session. §1's amendment says only the
*object* changes and everything else is unchanged, so the estimator modules were called exactly
as D382 called them, `rebuild_every = 1` included. **The features are the same functions; their
time constants are not the same durations.**

---

## 2. The verdict

**On the statistic §8's abandon condition names — bp per bar held — the best cell at every hold
sits AT the null's centre, not near its bar.**

```
hold   best cell (bp/bar)          bp/bar   rotation p50/p95    entry p50/p95   margin vs rotation / entry
   4   struct_trend|W260|hi       +1.4901   +1.075 / +4.828   +2.468 / +9.494      -0.06 SE / -0.59 SE
  13   struct_trend|W260|hi       +0.9417   +0.731 / +2.356   +1.024 / +3.901      +0.00 SE / -0.37 SE
  26   choch_dist|W780|hi         +0.3348   +0.543 / +2.116   +0.882 / +3.459      -0.71 SE / -0.83 SE
  78   park_vol_21|W390|lo        +0.1994   +0.390 / +1.278   +0.610 / +2.080      -0.85 SE / -0.95 SE
```

**0 of 572.** And on the primary per-trade statistic, at the three holds where that statistic is
not degenerate:

```
hold   best cell (mean/trade)     gross bp   rotation p50/p95      entry p50/p95    margin
   4   struct_trend|W260|hi         +5.98    +4.30 /   +19.31   +9.87 /   +37.98   -0.07 / -0.59 SE
  13   struct_trend|W260|hi        +12.37    +9.58 /   +30.63  +13.32 /   +50.71   -0.04 / -0.38 SE
  26   close_in_range|W26|hi       +31.55   +29.03 /   +55.01  +22.95 /   +89.93   -0.07 / -0.24 SE
```

**Cells clearing both floors on mean per trade, by hold: 4 → 0, 13 → 0, 26 → 0, 78 → 10.**

### 2a. The ten passes are buy-and-hold, and `n_eff` is what says so

Every cell that clears the pre-registered primary statistic is at hold 78, and every one of them
is the same object:

```
cell                    hold   mean bp  trades  n_eff  expo   bp/bar  grossCAGR   BH@expo   excess   median run
wick_asym|W52|lo          78   4,699.9      57      1  1.000  0.1249      7.63%     7.62%   +0.00%       37,643
lower_wick|W52|hi         78   4,695.8      57      1  1.000  0.1248      7.62%     7.62%   -0.00%       37,641
wick_asym|W26|lo          78   4,688.7      57      1  1.000  0.1246      7.62%     7.62%   -0.01%       37,642
body_frac|W26|hi          78   4,674.8      57      1  1.000  0.1242      7.60%     7.62%   -0.03%       37,646
lower_wick|W26|hi         78   4,612.9      58      1  1.000  0.1247      7.62%     7.62%   -0.00%       37,641
body_frac|W52|hi          78   4,530.9      59      1  1.000  0.1246      7.61%     7.62%   -0.01%       37,646
range_frac|W26|hi         78   4,169.1      64      1  0.999  0.1244      7.73%     7.62%   +0.11%       37,633
gap_frac|W26|lo           78   3,638.9      72      1  1.000  0.1221      7.63%     7.62%   +0.01%       37,638
lower_wick|W130|hi        78   2,946.2      89      2  1.000  0.1222      7.63%     7.62%   +0.01%       28,354
body_frac|W130|hi         78   2,862.9      84      1  1.000  0.1121      7.60%     7.62%   -0.03%       30,354
```

**57 trades on 57 names is one trade per name. The median trade runs 37,643 bars of the 37,648
available after the warm-up.** Exposure is 1.000, the gross CAGR is the panel's own +7.62%, and
`[BH]`'s excess at matched exposure is **0.00%**. The "+18.19 SE" margin over the rotation floor
is a book that is never flat being compared to a book that is never flat, rotated.

**This is the segmentation confound §5.1 pre-registered bp-per-bar to catch, one level worse than
D382 measured it.** D382 found a nominal 40-bar hold producing 306-bar runs. Here, at hold 78,
**48 of 143 defined cells have a median run over ten times the nominal hold** and the p95 cell
runs 36,905 bars. **At the primary hold 26 the same count is 0 of 143** (median run 44.5 bars
against a nominal 26). **Hold 26 was nominated primary in advance, and it is the only hold at
which the top of the ranking is not corrupted by merging.** That the nomination was made before
the run is the reason this is reportable rather than a rescue.

**`n_eff` alongside every headline number:**

| | |
|---|---|
| **`n_eff` instruments** | **2.17 of 57** at 15 minutes (`effective_instruments`, 250-bar overlap). FINDINGS §4 puts the 57-ETF **daily** figure near 2.2 — **the saturation is a property of the universe, not of the sampling frequency**, and this is the first measurement of it at 15 minutes |
| **`n_eff` trades, the ten passes** | **1** (57 pooled trades ÷ mean concurrency 57.0) |
| **`n_eff` trades, best at hold 26** | **177** (9,733 pooled ÷ 55.0 held at once) |
| **`n_eff` trades, best own-null cell** | **912** (23,045 pooled ÷ 25.3) |
| **`n_eff` null draws** | **200** per family per hold |

R10's crowding measurement, on the primary hold: the intrabar books hold **52–55 of 57 names on
100% of bars**, and the per-symbol-rotated control reaches **57** too. **The crowding is not
selection; it is that the book is never flat.**

### 2b. Is the null decisive? Yes, and not because of the p95

R7 asks for the distribution, not the percentile. The best-of-150 floor is noisy at the short
holds — at hold 4 the rotation floor has mean +6.38 with sd 6.03, and the entry floor mean +13.38
with sd 12.60, so its p95 is not precisely estimated at 200 draws. **The verdict does not depend
on that precision, because the observed best sits at −0.07 to −0.85 SE of the floor's own centre**
— not just under the bar, but on top of the median. A tenfold increase in draws moves the bar and
not the answer.

The one place the floor's noise would matter is the ten hold-78 passes, and there the answer is
supplied by `[BH]` rather than by the null.

---

## 3. Against each cell's OWN null — reported beside the floor, never instead of it

The pre-registered statistic is the best-of-150 floor. The per-cell null (**no multiplicity
correction**, 200 draws, same two families) is carried in `data/d383_nulls.json` under `per_cell`
because it is the only way to see *where* an effect sits.

**111 of 572 cells beat their own null's p95 on mean per trade, and 91 on bp-per-bar** — against
the ~29 a 5% bar would give if nothing were there. At the primary hold, the survivors on bp-per-bar
are **one coherent family, and it is not a market-structure family:**

```
cell                       bp/bar   own rot p50/p95   own entry p50/p95   expo   excess vs BH@expo   n_eff
choch_dist|W780|hi        +0.3348   0.1467 / 0.2608   0.1344 / 0.2383    0.071        +0.93%        1,022
park_vol_21|W260|lo       +0.2802   0.1389 / 0.1787   0.1377 / 0.1800    0.443        +4.35%          912
gk_minus_cc|W52|lo        +0.2719   0.1327 / 0.1697   0.1353 / 0.1660    0.498        +4.55%          902
park_vol_21|W390|lo       +0.2666   0.1360 / 0.1766   0.1375 / 0.1799    0.420        +3.73%          921
gk_minus_cc|W130|lo       +0.2599   0.1327 / 0.1881   0.1400 / 0.1930    0.272        +2.18%        1,017
range_frac|W780|lo        +0.2063   0.1299 / 0.1554   0.1339 / 0.1491    0.721        +3.57%          355
```

**`park_vol_21`, `gk_minus_cc` and `range_frac` are the three volatility magnitudes**, and it is
the **LOW** tail of all three: *enter when this name's own trailing realised volatility is at its
own multi-week low.* It earns **+0.9% to +4.6% CAGR over buy-and-hold at matched exposure**, at
0.07–0.80 exposure, on `n_eff` 355–1,022 trades, and it survives the fully-costed net at the
longer holds (`park_vol_21|W390|h78|lo`: gross +46.4 bp, net **+37.1 bp** after a measured 5.07 bp
round trip, `n_eff` 162).

**Four things must be said about it, and each one is why it is not being reported as a finding:**

1. **It does not clear the pre-registered floor.** Not on either statistic, not at any hold. The
   floor exists because 572 cells were looked at; 111 of them beating an uncorrected p95 is what a
   correlated grid does.
2. **These three features were declared UNDECLARED in §3 and scored on both tails.** The low tail
   is the better of two, so it carries a best-of-2 on top of the best-of-150 — exactly the gate-1h
   cost §3 localised to these six features.
3. **It is a volatility-timing tilt, not a structure signal.** The rotation null holds the same
   names for the same number of bars at *random times*, so beating it means the book avoided
   high-volatility stretches. That is the low-volatility anomaly, a known and separate object, and
   it says nothing about wicks, gaps, fair-value gaps or volume nodes.
4. **The confound is not controlled.** Low realised volatility is also where the spread is
   narrowest, so the cost advantage and the return advantage have the same cause.

**No conclusion is drawn from it here and no avenue is opened by it. It is recorded because
leaving it out would be the more misleading choice.**

---

## 4. The four reporting groups, at the primary hold

### 4.1 Turnover first (D163), before any performance number

At hold 26, W = 130, per 57-name book:

```
                        events   trades  entries/yr  turnover/bar  median run   median run   exposure
                                                                       (bars)    (CALENDAR)
close_in_range|hi      208,403   11,680       2,002        0.0109         135     7.1 days      0.925
body_frac|hi           204,921   12,375       2,121        0.0115         134     7.1 days      0.946
upper_wick|lo          189,410    8,870       1,521        0.0082         142     7.9 days      0.784
park_vol_21|lo          50,578   26,022       4,461        0.0242          26     1.8 days      0.503
choch_dist|hi           21,519    8,180       1,402        0.0076          31     1.2 days      0.155
struct_trend|hi          3,461    3,089         530        0.0029          26     1.0 day       0.041
```

**Median across all 150 cells, by hold:**

```
hold   entries/yr   median run   median run    exposure   gross bp   bp/bar   net bp (IBKR only)
   4       12,347      4 bars       45 min        0.174      +0.27   0.0504        -3.29
  13        6,755     16 bars      20.5 h         0.398      +2.87   0.1001        -0.82
  26        2,639     44 bars       2.1 d         0.597      +7.14   0.1279        +3.44
  78          689    268 bars      15.0 d         0.877     +49.18   0.1268       +45.48
```

**A 4-bar hold is one hour and pays a full round trip, and at 15 minutes the intrabar features are
not signals at all — they are always-on books.** `close_in_range|hi` fires on 208,403 of 2.2M
name-bars and holds 92.5% exposure with a median run of 135 bars against a nominal 26.

### 4.2 Trade distribution — count, median, win rate, payoff, and the SYMMETRIC 1% trim

`close_in_range|W26|h26|hi`, the best cell at the primary hold:

| | |
|---|---|
| trades / `n_eff` | 9,733 / **177** |
| mean / median | **+31.55 / +20.09 bp** — mean **above** median, so the left tail is not doing the work |
| win rate / payoff | 54.8% / 1.03 |
| skew / kurtosis | +0.01 / 20.9 |
| **trim 1% from BOTH tails** | ex-top **+9.19**, ex-bottom **+53.48**, **trimmed +31.12** |
| top 1% of trades | **71.2% of P&L** |

**The symmetric trim leaves the mean where it was (+31.12 against +31.55).** Dropping only winners
takes it to +9.19 and would have frightened; the two-sided trim says the book is symmetric and
fat-tailed, which is what a 15-minute ETF book is, not a lottery ticket (D307). The same holds for
all five top cells: trimmed means +28.5 to +29.4 against untrimmed +27.3 to +31.6.

### 4.3 What the winners depend on

| | `close_in_range|W26|hi` | `upper_wick|W780|lo` |
|---|---|---|
| names to half the P&L | **15 of 57** | **13 of 57** |
| top-1 / top-5 / top-10 name share | 5.6% / 22.4% / 38.3% | 6.0% / 26.1% / 44.0% |
| the names | SMH, ITB, XLK, XHB, XLE | SMH, XME, ITB, XHB, XLE |
| profitable years | **4 of 6** | 4 of 6 |
| **price split** (low vs high half) | **+41.11 vs +21.98 bp** | **+47.98 vs +8.02 bp** |
| **top trade, named** | **OIH, entered 2020-05-11 15:45, +4,953 bp = 1.61% of P&L** | **OIH, entered 2020-05-15 14:00, +5,925 bp = 2.44% of P&L** |

**No single trade carries the result** — the largest is 1.6–2.4% of P&L, against D373's GME trade
at 6.34%. **The price split is the live risk**: the low-priced half of entries earns two to six
times the high-priced half, and IBKR's per-share commission scales inversely with price, so the
half that earns the return is the half that pays the most in basis points. That is what killed
D284, and it would have to be answered by anything built on these cells.

The winners are the high-beta sector and thematic ETFs — SMH, XLK, ITB, XHB, XLE, XME. Together
with `n_eff` = 2.17, that is the same sentence D382 ended on: **the book is the market.**

### 4.4 Cost, measured rather than assumed

**Corwin-Schultz off the OHLC of the names actually HELD**, not a fee assumption (D285 missed a
guessed 15 bp/side bar by 0.65 and the held names measured 33.8):

| | |
|---|---|
| CS half-spread, all 2.2M name-bars | **0.82 bp** median |
| CS half-spread, names HELD at the primary hold | **0.94 bp** median |
| IBKR per side, median over names, $10M book / 57 | **1.70 bp** (1.85 bp on the held names) |
| **measured round trip** | **5.1 – 6.3 bp** on the quoted cells (12.1 bp on the worst) |
| **breakeven at the primary hold's best cell** | **15.8 bp/side** against 2.8 bp/side charged |

**Cost is not what kills this.** `close_in_range|W26|h26|hi` nets **+21.2 bp per trade** fully
costed. R15 is explicit that gross decides at the signal stage, and gross is what fails: the cell
is at its null's centre and its excess over buy-and-hold at matched exposure is **+0.77% CAGR**.

**Corwin-Schultz on 15-minute bars is a lower bound and is labelled as one.** The estimator uses a
two-bar high-low range; on a 15-minute bar that range is small, so 0.94 bp/side is almost certainly
below the true quoted half-spread. D336's quoted-spread pull is the measurement that would settle
it, and it is not available.

---

## 5. Both lenses, and where the path is

**There is no slot cap in this construction, so the two lenses are not two books.** Every candidate
event is taken; the path-invariant lens (per TRADE, no cap) and the path-variant lens (the
equal-weighted portfolio in bp/bar and CAGR) are two statistics on the same object and are never
compared to each other. Opportunity cost is not measured here and could not be: nothing is ever
displaced.

**The exposure column is what a slot cap would bite on.** At the primary hold the intrabar cells
run 0.78–0.95 exposure across 57 names — a slot-limited version would be a different study, and
one worth noting is *unregistered*.

---

## 6. Assertions — every one shown to raise

```
[SPLIT]  cut 17,078 reserved bars from the BAR LISTS; 38,648 remain, last 2023-12-29 15:45
         RAISES on: a cut that removed nothing · a reserved bar left in · arithmetic that does not close
[GATE]   assert_gates_passed accepts the panel: gate_i1, gate_i2, gate_i3, gate_i5
         RAISES on: a file with no meta beside it
[TS]     the trailing percentile equals a LITERAL x[i, t-W:t] slice on 500 probes, on five
         (feature, window) pairs including the two THREE-VALUED features (struct_trend at W26 and
         W780, fvg_signed at W130) -- ties are where a rank rewrite disagrees. An extreme at bar t
         scores EXACTLY 100 on 80 probes, which a peeking window cannot reach (it can only get to
         100(k+0.5)/(k+1)).
         RAISES on: a percentile whose window is t-W..t INCLUSIVE
[LAG]    the held set re-derived bar by bar, in pure Python, from the percentile grid, by a second
         implementation that never calls events_of, runs_from_events or either position builder
         RAISES on: a book entered one bar early
[POS]    per-event loop == difference-array grid == run kernel, rotated and not, bit-for-bit, on
         213,552 real events and on a synthetic TIE-HEAVY book
         RAISES on: a run kernel entered one bar early · a rotation that clips instead of wrapping
[SIGN]   in money: a long through the best bar pays +0.000280 and the short -0.000280; on
         EWT 2022-12-13 15:45 the dividend pays a long +1,799.01 bp and costs a short -1,799.01 bp
         RAISES on: a sign-blind scorer (one that scores |pos|)
[QTY]    the total-return grid scores this book at +25.995 bp and the price-return grid at +18.316
         RAISES on: a panel whose dividend leg is not compounded
[BH]     unit-exposure buy-and-hold, GROSS: CAGR +7.62%, Sharpe +0.285, ppy 6,454 bars/yr
         RAISES on: a panel with zero exposure
[NULL]   every observed event, and every drawn null entry, satisfies that cell's own eligibility
         mask, and the drawn entry count is matched per NAME (D347/D351)
[FN]     fast_null.light_score agrees EXACTLY with RP.score on the real book (assert_matches_scorer)
```

Each break hits the scalar the assertion reads, not the name of something nearby: `[POS]`'s break
shifts the run start by exactly the lag; `[SIGN]`'s replaces the scorer with a sign-blind one;
`[QTY]`'s hands it a panel whose two return grids are identical.

---

## 7. The predictions, scored

| | prediction | outcome |
|---|---|---|
| **Q1** | nothing clears both floors on bp-per-bar at any hold | **CORRECT. 0 of 572**, and the best cell at every hold is within 1 SE of the floor's centre |
| **Q2** | the window sweep is **FLAT**, not humped | **WRONG.** Over 100 (direction, hold) profiles: 32 interior humps, 10 monotone-falling, 19 edge peaks, 35 flagged knife-edge, 4 incomplete. **None is flat.** The intrabar features fall monotonically in W — short windows are better — and the volatility and volume-profile features hump in the interior. The shapes are shallow but they are shapes |
| **Q3** | the shortest hold has the **best bp-per-bar** and the **worst net** | **HALF WRONG, and the wrong half is the interesting one.** Worst net: correct (median −3.29 bp at hold 4, +45.48 at hold 78). Best bp-per-bar: **wrong on the median cell** — bp/bar *rises* with hold (0.050 → 0.100 → 0.128 → 0.127). **The edge is not front-loaded at 15 minutes**, which is the opposite of D378's daily finding. It is right on the *best* cell (+1.49 at hold 4), but the null floor there is +4.83, so that is variance, not edge |
| **Q4** | entries/year at hold 4 an **order of magnitude** above the daily study's | **DEPENDS ON THE DENOMINATOR, and the prediction did not name one.** Per BOOK: 12,347/yr against D382's 2,873 = **4.3×**. Per NAME: 217 against 5.2 = **42×**, because D382's universe is **551** names and this one is 57. Correct per name, wrong per book. *A prediction has to be written in the runner's own quantities to be checkable* |
| **Q5** | at least one feature scores better in the direction NOT declared | **CORRECT, and by more than one.** On the non-degenerate holds (4/13/26), **6 of the 12 defined declared features are DIRECTION-INVERTED**: `fvg_signed`, `gap_frac`, `lower_wick`, `retrace_leg`, `upper_wick`, `wick_asym`. Three of those six are the same quantity (`upper_wick`, `lower_wick`, `wick_asym`), so it is four independent inversions. **Every one counts against its stated mechanism (gate 1h) and the ledger counts both directions** |
| **Q6** | `[TS]` and `[SPLIT]` both hold on the first run | **CORRECT** |
| **Q7** | *against myself* — if anything survives it is **axis D (volume profile)** | **WRONG.** Nothing survives the floor. The cells that beat their own uncorrected null are the **volatility magnitudes** (`park_vol_21`, `gk_minus_cc`, `range_frac`), all on the LOW tail. Axis D (`dist_hvn`, `dist_lvn`, `mass_here`, `mass_imbalance`) sits mid-table at +4.1 to +9.2 bp at the primary hold. **The D194 span census had already cleared axis D's premise** — median span 3.0, only 3.76% of contributing bars in a single bucket, so the map is a genuine volume profile at 15m and not a close-price histogram (`data/d383_span_census.json`). The premise was sound and the signal is not there |

---

## 8. Two features produced nothing, and that is a measurement

**`gap_reversal` contributed 0 of its 24 cells.** It is defined only where the bar-to-bar "gap"
exceeds 50 bp — a floor put in for daily bars, where the first run ranged over [−14338, +1880] and
was entirely denominator. At 15 minutes an adjacent-bar move of 50 bp on a liquid ETF is rare:
coverage is **1.7%**, and the trailing window then almost never holds 20 defined values.

```
gap_reversal events, lo/hi:  W26 0/0 · W52 0/0 · W130 1/1 · W260 1/2 · W390 1/2 · W780 6/42
```

**`struct_trend` lost its longest window** — 24 and 18 events at W780, below the 50-event minimum —
because a three-valued score crosses its own trailing decile less and less often as the window
grows (22,702 events at W26 falling to 24 at W780). Both are properties of transplanting a daily
estimator to a 15-minute bar, and both are reported rather than papered over. 600 − 24 − 4 = **572
defined cells**, which is the denominator every headline here uses.

---

## 9. What this does and does not settle

**It settles**, on this fixture and this construction:

- **The time-series version of the market-structure screen carries no signal at 15 minutes** on the
  statistic §8 named. D382 closed the cross-sectional version on the daily panel; this is the other
  cell of that 2×2, and §0's point that D382's failure said *nothing* about this one was right —
  it is a genuinely new test and it comes back the same way.
- **The per-trade mean is unusable at hold 78 for dense features**, and the record now has the
  number: 48 of 143 cells with a median run over 10× the nominal hold, against 0 of 143 at hold 26.
  **A screen that quotes mean-per-trade without bp-per-bar beside it will report buy-and-hold as a
  discovery.** D383 pre-registered the companion; without it, this study's headline would have been
  "10 of 600 cells clear both nulls at up to +18 SE".
- **`n_eff` = 2.17 of 57 at 15 minutes.** FINDINGS §4's ~2.2 saturation is a property of the ETF
  universe and **not** of the sampling frequency. Sampling 26× more often buys no breadth.

**It does not settle**, and these are stated as untested rather than as remaining questions:

- **Level- or threshold-based selection.** The event is a decile *crossing*; a rule that says "enter
  whenever the percentile is below 10" rather than "when it crosses below 10" is a different book
  and was not run.
- **The short side.** Every cell here is long-flat. Six of the twelve defined declared features
  score better in the direction they did not declare (§7, Q5), which is a fact about the *long*
  reading of those features and not a short study.
- **A slot-limited book.** No cap, so no opportunity cost and no path lens in the sense
  `FINDINGS §10` means.
- **The low-volatility tilt of §3**, which beat its own null but not the floor, and which is a
  different hypothesis from the one D383 tested.
- **Gate 1e (capturability) and gate 1d′ (correlation to S1/S2)** — §5.5 makes both conditional on
  something surviving §4. Nothing did. **NOT COMPUTED**, and recorded as such rather than omitted.

**§8's abandon condition is MET:** *"Nothing clears §4 on bp-per-bar → the features carry nothing at
this frequency either, and the family is closed on both constructions. Write it as the close; do not
sweep more windows."* No further windows were swept and none will be.

**Under [R15](../RULES.md#r15), a research avenue is closed by the principal and never by a record.
This record reports what the construction showed and what it did not test. It does not close the
axis, and it admits nothing to either book.**

---

## 10. Cost of the run, and the machine

| | |
|---|---|
| `--prep` (load, split, cache) | 1 process, **1.93 GB peak**, ~3 min |
| `--features` (19 grids) | **4 processes over `symbols[i::4]`**, 268 s, 0.29 GB each. Serial was 13 min: the volume-profile sensor and the structure state machine are GIL-bound pure Python, so processes, not threads (D288) |
| `--events` (114 percentile grids) | 191 s, **0.50 GB**. One grid alive at a time — the 600-cell grid is never materialised |
| `--observed` (912 cells) | 326 s, **0.34 GB** |
| `--nulls` (200 draws × 2 families × 4 holds) | **1,343 s**, **1.05 GB**, `parallel_map` over the four holds at **3.15× on 4 workers = 79% efficiency** |
| **peak working set, any process** | **1.93 GB** |

**The null kernel is the reason this fits.** Rotating a book's **circular runs** instead of rolling
2.2M cells and rescanning them took a cell-draw from **26.1 ms to 5.6 ms**, and `[POS]` proves the
two agree element for element — unrotated and rotated, on a tie-heavy book — before a draw is taken.
Without it the null stage is over five hours. A first version cached the shared permutation pool per
feature-window and reached **2.84 GB**; dropping that cache and moving the event and run arrays to
int32 brought the same computation to **1.05 GB**.

*Every cache in `temp/` is keyed on the fixture's mtime **and** every estimator module's mtime, and
`load_mined` refuses a stale one rather than returning numbers that look fine.*
