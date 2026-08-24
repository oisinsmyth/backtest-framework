# STRUCTURE_RESULTS.md — the structure programme's ledger

**PROGRAMME CLOSED, 2026-08-24 (D211).** The final report is below; a post-close
descriptive addendum restating every arm in Sharpe and PnL follows it (D212), taking
the ledger to **102 looks**. WP5 never ran — D210 triggered the pre-registered stop.

**Append-only.** Every work package adds a dated section; nothing above is rewritten. This
is the single results ledger `New Docs/STRUCTURE_MODEL.md` requires, and it carries the
multiplicity count that feeds the deflated Sharpe if the programme reaches WP5.

**What this programme tests:** whether the five components of a discretionary retail
day-trading strategy — change of character, the flipped level, the 61.8% Fibonacci
retracement, the fair value gap, and RSI — carry information about forward price behaviour
on BTC and ETH 15m bars, separately and in combination, once each is mechanised precisely
enough that a machine can find it without a human drawing the lines.

**Spec and pre-registration:** `New Docs/STRUCTURE_MODEL.md` (D204), committed before any
detector existed.

---

## Inherited disclosure — the terrain programme

The predecessor programme spent **259 looks** establishing that price-derived maps of
resting supply and demand carry no directional or reversal information on this data
(`TERRAIN_RESULTS.md`; S1 closed by D194, the S6 reversal line by D200, the S6 map by
D203). Its unifying mechanism was that **fading lost in every form measured** — 16 of 16
cells, 16 of 16, 8 of 8, and 11 years of 11.

Three of the five components tested here (the flipped level, the Fib retracement, the fair
value gap) are pullback-fade entries. **The prior for this programme is bad, and it is
stated here rather than after the result.**

That count is disclosed adjacent and is **not** added to this ledger — a different
construction and a different claim, per the condition `TERRAIN_RESULTS.md` closes with.
The one exception is pre-committed in Disclosure D1 of the spec: **if the flipped-level
component is the only survivor, D196's 20 looks are inherited into the total below**,
because in that world the two studies are reading the same swing structure.

---

## Multiplicity ledger — running

| Work package | looks |
|---|---:|
| WP0 pre-registration (no runs) | 0 |
| WP1 detectors (no runs) | 0 |
| WP2 census (counts only, no test) | 0 |
| WP3 components against their placebos | 24 |
| WP3 depth-matched re-reading (post-hoc) | 6 |
| WP4 feature quintiles | 12 |
| WP4 conditional on depth (post-hoc) | 10 |
| WP4 conditional on stop width (post-hoc) | 10 |
| WP4 ablation lattice | 16 |
| WP5 costed verdict | **did not run** |
| WP6 discretion audit (grid) | 8 |
| Post-close Sharpe/PnL addendum (D212) | 16 |
| **Total** | **102** |

**D213 is a separate study with its own ledger (22 looks)** — a different claim, pre-registered after this programme closed, with these 102 disclosed. Its section is
below the final report.

**D214 is a third (12 looks)** — the terrain map as a confluence gate, which overrides
D203's stop by explicit amendment and inherits both families' counts for its combined
bar: 124 + 259 + 12 = 395.

**D215 is a fourth (16 looks)** — the test of *why* it all failed. Its Test A carries a
**fresh** ledger: it deletes the structure entirely, and a test whose predicted outcome is
*this effect is generic and therefore not yours* is negative-confirming, which prior looks
do not weaken. Tests B and C inherit the 395.

Never reset. Retired and failed cells count. Budget estimated in the plan at ~118 looks
for the full programme; the estimate is not a licence and the actual count is what feeds
the deflated Sharpe.

---

## WP0 — pre-registration

**Produced:** 2026-08-24 · **Reproduce:** n/a — no runs.

`New Docs/STRUCTURE_MODEL.md` written and committed, recorded as D204. It fixes, before
any code exists: the five mechanical definitions; the confirmation-lag requirement; the
pre-registered parameter sets and the named primary cell; the three hurdles with the
percentile-beside-the-delta requirement from D202; the per-WP stop conditions; seven
pre-registered predictions with confidences; and four disclosures — the S5/D196 overlap on
the flipped level, the zero-hit grep establishing the other components as new
construction, the statement that nothing has been seen, and D199's calibration note
capping baseline-relative predictions at moderate confidence.

**Looks: 0.** Nothing was run.

## WP2 — the census, counts only

**Produced:** 2026-08-24 · **Reproduce:** `uv run python scripts/run_structure_census.py` (offline, deterministic)

No return, no Sharpe and no verdict about whether anything works appears in this section. `STRUCTURE_MODEL.md` requires the counts first, because counts have repeatedly caught defects in this project before they became results (D197, D198, D201, D202).

> **CORRECTED TWICE, 2026-08-24 — D209 then D212.** Both corrections are named here rather than shown as new numbers under an old heading.
>
> **D209** — the stop was placed at `leg.end_price`, the extreme the impulse ran TO, which for a long sits ABOVE the entry and is not a stop at all. It also reversed the direction of finding 4 below: a deeper entry is a *tighter* stop, so the confluence stack raises friction rather than halving it.
>
> **D212** — the cost convention. `cost_bps` is a PER-SIDE exchange fee, so a round trip pays twice it. This section charged it once while WP4's lattice charged it twice: two halves of one study disagreeing by a factor of two on the same tier.
>
> Superseded base-arm friction: **0.97R / 0.72R** (D209 era) and **0.48R / 0.34R** (post-D209, pre-D212). Superseded required hit rate at 5R: **32.9% / 28.6%** and **24.7% / 22.3%**. The figures below are the current ones.

### The population, at the primary cell

Primary: `k=2`, touch band `0.5` ATR, ATR window 1,920 bars (20 days at 96/day, D194's calendar match).

| symbol | bars | CHoCH | BOS | setups | no leg | dead on arrival | in ATR warm-up |
|---|---:|---:|---:|---:|---:|---:|---:|
| `BTCUSDT` | 294,336 | 4,366 | 23,017 | 3,875 | 91 | 373 | 27 |
| `ETHUSDT` | 294,336 | 4,193 | 23,133 | 3,753 | 79 | 333 | 28 |

*Dead on arrival* is a real category rather than a rounding error: the impulse leg's end pivot needs `k` bars to confirm, and price can retrace the whole leg inside those bars. Those setups are refused, never entered at a bar where the structure was already gone.

### The funnel — how many setups survive each filter

| symbol | C1 | +C2 level | +C3 fib | +C4 gap | +C5 rsi |
|---|---:|---:|---:|---:|---:|
| `BTCUSDT` | 3,875 | 874 | 389 | 120 | 2 |
| `ETHUSDT` | 3,753 | 942 | 385 | 106 | 2 |

Each filter on its own, against the same setup population:

| symbol | C1+C2 | C1+C3 | C1+C4 | C1+C5 |
|---|---:|---:|---:|---:|
| `BTCUSDT` | 874 | 2,672 | 1,089 | 126 |
| `ETHUSDT` | 942 | 2,619 | 1,127 | 144 |

### Confluence, measured in counts

The course's claim is that the filters line up **at one price at one time**. That is a different population from each filter being satisfied somewhere during the pullback, and the gap between the two is the claim itself:

| symbol | each of C2/C3/C4 held somewhere | all three held simultaneously | ratio |
|---|---:|---:|---:|
| `BTCUSDT` | 340 | 120 | 0.35 |
| `ETHUSDT` | 388 | 106 | 0.27 |

### The stop condition

- `BTCUSDT`: **120** stacked entries against a floor of 30 — **CLEARS**.
- `ETHUSDT`: **106** stacked entries against a floor of 30 — **CLEARS**.

### The friction, by arithmetic

A 40 bps round trip against the stop widths these entries actually produce. D196/D197 already pinned the same arithmetic on daily bars at **0.49R on a 0.5-ATR stop** and **0.12R at 2 ATR**; this is that calculation on this strategy's stops, run before any backtest.

| symbol | arm | n | median wait (bars) | median retracement | median stop (ATR) | median stop (%) | median friction (R) | hit rate needed at 5R |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `BTCUSDT` | C1 only | 3,875 | 5 | 0.321 | 2.14 | 0.83% | 0.960 | 32.7% |
| `BTCUSDT` | C1+C2+C3+C4 | 120 | 9 | 0.538 | 1.39 | 0.57% | 1.412 | 40.2% |
| `ETHUSDT` | C1 only | 3,753 | 5 | 0.316 | 2.28 | 1.18% | 0.680 | 28.0% |
| `ETHUSDT` | C1+C2+C3+C4 | 106 | 9 | 0.547 | 1.47 | 0.79% | 1.011 | 33.5% |

Frictionless, a 5R target breaks even at **16.7%** — the course's "two out of ten". The column above is the same arithmetic with costs put back.

### What the counts say

**1. The stop condition clears, so the programme continues.** `BTCUSDT` produces 120 stacked entries and `ETHUSDT` produces 106 stacked entries, both above the pre-registered floor of 30. H5 — that the stacked arm would be underpowered — is **falsified**. It was held at moderate confidence and it was wrong.

**2. The round trip eats a third to a half of the risk before anything happens.** On the C1-only arm the median stop sits at 0.83% of price on `BTCUSDT` and 1.18% of price on `ETHUSDT`, against a 40 bps round trip — so friction is 0.96R and 0.68R. That is arithmetic rather than a result, and it is the structural problem with running this strategy on 15m bars: a stop placed at a 15m swing extreme is close enough that crossing the spread twice is a material fraction of the whole trade.

**3. The course's central arithmetic is wrong once costs exist.** It claims a 5R target breaks even at ~20% and is "highly profitable" at 30%. Frictionless that is nearly right — the true break-even is 16.7%. At 40 bps on the stacked arm it becomes 40.2% on `BTCUSDT` and 33.5% on `ETHUSDT`, and on the C1-only arm 32.7% and 28.0%. **A 20% hit rate at 5R loses money at every cell measured here.** No backtest was needed to establish that, and none of it depends on whether the components carry information.

**4. The confluence stack enters deeper, and that makes the arithmetic WORSE.** Median retracement moves from 0.321 to 0.538 on `BTCUSDT` and 0.316 to 0.547 on `ETHUSDT`. The stop sits at the extreme the leg came FROM, so a deeper entry is a **tighter** stop, not a wider one: 2.14 to 1.39 ATR and 2.28 to 1.47 ATR, and friction rises from 0.96R to 1.41R and 0.68R to 1.01R. So the confluence the course sells as precision is, in cost terms, a tax: it buys a better price by risking less, and the fixed spread then eats a larger share of what is left. WP4 asks whether the better price is worth the tax.

**5. Two filters barely filter, and one is incompatible with the rest.** C3 (the 61.8% band) admits 2,672 of 3,875 and 2,619 of 3,753 setups on its own — roughly 69% and 70% of the population, which is very little work for a filter, before anyone asks whether 0.618 is special. C5 (RSI 30/70) collapses the stacked arm to 2 and 2 entries: the textbook thresholds essentially never coincide with structural confluence. **C5 is therefore dropped as a stacked filter and kept as a continuous feature in WP4a**, which is where a 2-trade arm has nothing to say and a rank correlation still does.

**And one number that is the discretion gap itself.** `BTCUSDT`: 340 setups have all three conditions somewhere in the pullback window but only 120 have them at the same bar (35%) and `ETHUSDT`: 388 setups have all three conditions somewhere in the pullback window but only 106 have them at the same bar (27%). A trader reading the chart afterwards sees the level, the retracement and the gap all present and calls it confluence. Two thirds of the time they were not simultaneous, and which bar you would actually have entered on is a judgement call. WP6 is the audit of that; this is its first measurement.
### Sensitivity across the pre-registered grid

| symbol | k | touch | setups | stacked | median stop (ATR) | median friction (R) |
|---|---:|---:|---:|---:|---:|---:|
| `BTCUSDT` **(primary)** | 2 | 0.5 | 3,875 | 120 | 1.39 | 1.412 |
| `BTCUSDT` | 2 | 1.0 | 3,875 | 244 | 1.89 | 1.004 |
| `BTCUSDT` | 3 | 0.5 | 2,808 | 67 | 1.65 | 1.079 |
| `BTCUSDT` | 3 | 1.0 | 2,808 | 131 | 2.19 | 0.839 |
| `ETHUSDT` **(primary)** | 2 | 0.5 | 3,753 | 106 | 1.47 | 1.011 |
| `ETHUSDT` | 2 | 1.0 | 3,753 | 239 | 1.96 | 0.786 |
| `ETHUSDT` | 3 | 0.5 | 2,717 | 45 | 1.65 | 1.017 |
| `ETHUSDT` | 3 | 1.0 | 2,717 | 137 | 2.27 | 0.679 |

### Multiplicity

**Looks: 0.** A census is not a test. Nothing here compares anything to anything, no hypothesis is scored, and no parameter is chosen on the strength of it. The grid above is reported so that WP6's discretion audit has counts to stand on and so a cell producing nothing cannot quietly vanish from a later table.

## WP3 — each component alone, against its own matched placebo

**Produced:** 2026-08-24 · **Reproduce:** `uv run python scripts/run_structure_components.py` (offline, deterministic, seed 0)

Primary cell only: `k=2`, touch band 0.5 ATR, 500 draws. **No costs anywhere in this section** — WP3 asks whether the components carry information, and WP2 already priced the toll at 0.4-1.0R. Mixing the two would let a real signal be reported as absent because it is expensive, which D202's zero-cost diagnostic exists to prevent.

### The statistic, restated

**Touch**: the first bar of a setup's pullback window inside `k x ATR` of the level whose predecessor was outside. **Band fixed at the touch** and not revisited. **Continuation**: within 5 bars the close moves a band beyond the level *in the change of character's direction* without first moving a band beyond it against. Unresolved counts as not continued, identically in both arms.

This is `terrain_nulls`' reversal definition with one change: the direction comes from the setup rather than from the approach side. That is not cosmetic — a reversal statistic is agnostic about which way price then goes, and this one is not, because the strategy is not.

### C1 — the change of character, against a rotation null

| symbol | real Sharpe | null mean | null p95 | percentile | delta | net exposure | clears +0.10 |
|---|---:|---:|---:|---:|---:|---:|:--:|
| `BTCUSDT` | +0.124 | -0.009 | +0.533 | 66.2th | +0.133 | -0.0001 | yes |
| `ETHUSDT` | -0.068 | -0.010 | +0.532 | 43.6th | -0.057 | -0.0015 | no |

Rotation preserves the exposure distribution, the autocorrelation, the turnover and the net tilt exactly, and destroys only the alignment with price. It asks *did the exposure change at the right moments* — the one question D201 could not answer about itself.

### C2, C4, C5 — touch statistics against matched placebos

| symbol | arm | placebo | touches | P(cont) real | null mean | null p95 | percentile | delta | beats p95 |
|---|---|---|---:|---:|---:|---:|---:|---:|:--:|
| `BTCUSDT` | C2 | level drawn on the same leg | 2,780 | 44.6% | 47.0% | 48.3% | 0.4th | -0.0238 | no |
| `BTCUSDT` | C4 | same-width band, displaced | 2,228 | 56.1% | 48.0% | 49.5% | 100.0th | +0.0817 | yes |
| `BTCUSDT` | C5 | random bar of the window | 126 | 45.2% | 32.9% | 38.9% | 100.0th | +0.1236 | yes |
| `ETHUSDT` | C2 | level drawn on the same leg | 2,663 | 45.9% | 46.8% | 48.2% | 13.0th | -0.0091 | no |
| `ETHUSDT` | C4 | same-width band, displaced | 2,151 | 54.3% | 47.8% | 49.4% | 100.0th | +0.0643 | yes |
| `ETHUSDT` | C5 | random bar of the window | 144 | 54.9% | 34.2% | 40.3% | 100.0th | +0.2069 | yes |

Every delta is printed with its percentile beside it. D202's lesson 5 is the reason: a delta over a *wide* null's mean cleared that programme's +0.10 floor at the 67th percentile, and a floor without a percentile is not a hurdle.

#### The same three arms, depth-matched - and this is the verdict

The C3 ladder below came back a **strictly monotone staircase in retracement depth**. That makes depth a nuisance variable running through every other arm: a level sitting deep on its leg beats a uniformly-drawn placebo whether or not it means anything, and a shallow one loses to it. So the table above is not the verdict. This one is - *does the real arm beat a placebo at the SAME depth?*

| symbol | arm | real depth | placebo depth | P(cont) real | depth-matched expectation | delta | touches covered |
|---|---|---:|---:|---:|---:|---:|---:|
| `BTCUSDT` | C2 | 0.391 | 0.431 | 44.6% | 46.2% | -0.0159 | 2,687/2,780 |
| `BTCUSDT` | C4 | 0.626 | 0.444 | 56.1% | 55.6% | +0.0060 | 2,195/2,228 |
| `BTCUSDT` | C5 | 0.796 | 0.214 | 45.2% | 37.1% | +0.0818 | 122/126 |
| `ETHUSDT` | C2 | 0.399 | 0.434 | 45.9% | 46.3% | -0.0042 | 2,577/2,663 |
| `ETHUSDT` | C4 | 0.625 | 0.447 | 54.3% | 54.9% | -0.0062 | 2,126/2,151 |
| `ETHUSDT` | C5 | 0.745 | 0.242 | 54.9% | 39.4% | +0.1548 | 138/144 |

Real touches landing in a depth bin the placebo never reached are excluded and counted, never imputed from a neighbouring bin - an unpopulated bin means the comparison has nothing to say there, and filling it in would invent the answer at exactly the depths where the real arm is unusual.

### C3 — the golden ratio against seven other numbers

The same setups, the same legs, a different number. No draws are needed because the placebo ratios ARE the null, and D189's H2 confound — levels sitting where price has recently been — cancels exactly, since every ratio is a point on the same leg.

**`BTCUSDT`**

| ratio | kind | touches | P(continuation) |
|---:|---|---:|---:|
| 0.382 | canonical | 3,270 | 46.1% |
| 0.447 | placebo | 3,137 | 49.5% |
| 0.500 | canonical | 2,999 | 51.9% |
| 0.553 | placebo | 2,854 | 54.7% |
| 0.618 | **golden** | 2,672 | 56.9% |
| 0.691 | placebo | 2,470 | 58.7% |
| 0.724 | placebo | 2,371 | 59.1% |
| 0.786 | canonical | 2,187 | 60.5% |

**`ETHUSDT`**

| ratio | kind | touches | P(continuation) |
|---:|---|---:|---:|
| 0.382 | canonical | 3,155 | 46.3% |
| 0.447 | placebo | 3,066 | 49.9% |
| 0.500 | canonical | 2,929 | 52.0% |
| 0.553 | placebo | 2,786 | 55.4% |
| 0.618 | **golden** | 2,619 | 55.8% |
| 0.691 | placebo | 2,400 | 57.2% |
| 0.724 | placebo | 2,323 | 58.2% |
| 0.786 | canonical | 2,111 | 58.0% |

Paired bootstrap of 0.618 minus each placebo ratio, one resampled index vector applied to both arms:

| symbol | vs ratio | mean difference | 5th-95th | share of draws NOT better |
|---|---:|---:|---|---:|
| `BTCUSDT` | 0.447 | +0.0725 | [+0.0540, +0.0900] | 0.0% |
| `BTCUSDT` | 0.553 | +0.0211 | [+0.0068, +0.0350] | 0.4% |
| `BTCUSDT` | 0.691 | -0.0178 | [-0.0335, -0.0027] | 97.4% |
| `BTCUSDT` | 0.724 | -0.0227 | [-0.0405, -0.0043] | 97.6% |
| `ETHUSDT` | 0.447 | +0.0592 | [+0.0417, +0.0784] | 0.0% |
| `ETHUSDT` | 0.553 | +0.0040 | [-0.0098, +0.0187] | 29.2% |
| `ETHUSDT` | 0.691 | -0.0136 | [-0.0280, +0.0015] | 93.6% |
| `ETHUSDT` | 0.724 | -0.0238 | [-0.0421, -0.0061] | 98.8% |

### What the arms say

**C1 — the change of character.** `BTCUSDT` Sharpe +0.124 against a rotation null mean of -0.009, at the 66.2th percentile (delta +0.133) and `ETHUSDT` Sharpe -0.068 against a rotation null mean of -0.010, at the 43.6th percentile (delta -0.057). The book runs at -0.0001 and -0.0015 net exposure, so this is a timing reading and not a disguised long — the confound that made D201's best cells one multi-year long is absent here by construction.

**C2 — the flipped level**, against levels drawn uniformly over the same impulse leg. `BTCUSDT` 44.6% on 2,780 touches against a null mean of 47.0%, at the 0.4th percentile (delta -0.0238) and `ETHUSDT` 45.9% on 2,663 touches against a null mean of 46.8%, at the 13.0th percentile (delta -0.0091).

**C4 — the fair value gap**, against a band of the same width displaced within the leg. `BTCUSDT` 56.1% on 2,228 touches against a null mean of 48.0%, at the 100.0th percentile (delta +0.0817) and `ETHUSDT` 54.3% on 2,151 touches against a null mean of 47.8%, at the 100.0th percentile (delta +0.0643).

**C5 — RSI**, against a random bar of the same window. `BTCUSDT` 45.2% on 126 touches against a null mean of 32.9%, at the 100.0th percentile (delta +0.1236) and `ETHUSDT` 54.9% on 144 touches against a null mean of 34.2%, at the 100.0th percentile (delta +0.2069).

**And now the same three arms at matched depth, which is the verdict.** `BTCUSDT` C4 falls from +0.0817 against a uniform placebo to +0.0060 against one at the same depth and `ETHUSDT` C4 falls from +0.0643 against a uniform placebo to -0.0062 against one at the same depth. The real gaps sit at retracement 0.626 and 0.625 while the uniform placebo sits at 0.444 and 0.447 — so **the fair value gap's entire apparent edge was that it sits deeper on the leg.** C2 is negative either way. C5 is the only arm that survives matching, at +0.0818 and +0.1548 on 122 and 138 covered touches — a small sample, and the one component in the study that was put there as a control.
**C3 — the golden ratio, against seven other numbers on the same legs.** 0.618 ranks **4 of 8** on `BTCUSDT` (56.9% against a placebo mean of 55.5%) and 0.618 ranks **4 of 8** on `ETHUSDT` (55.8% against a placebo mean of 55.2%). The spread across all eight ratios is 0.1439 and 0.1186, against a golden-minus-placebo gap of +0.0136 and +0.0066 — so the variation *between arbitrary ratios* is larger than the advantage the golden one is supposed to have over them.


### Multiplicity

| arm | cells | looks |
|---|---|---:|
| C1 rotation null | 2 symbols | 2 |
| C2 flipped level | 2 symbols | 2 |
| C3 ratio ladder | 8 ratios x 2 symbols | 16 |
| C4 fair value gap | 2 symbols | 2 |
| C5 RSI | 2 symbols | 2 |
| depth-matched re-reading (POST-HOC) | 3 arms x 2 symbols | 6 |
| **WP3 total** | | **30** |

**The depth-matched comparison was NOT pre-registered.** It was designed after the C3 ladder came back a monotone staircase, which is post-hoc by any honest accounting, and it is counted as six further looks rather than folded into the arms it re-reads. Two things make it disclosable rather than disqualifying: it makes every verdict HARSHER, not kinder — C4 goes from a clean pass to nothing — and the confound it controls for was named in `structure_nulls.py`'s docstring before any run, as D189's H2. What was not anticipated is that the confound would turn out to explain the whole result.

The `k` and touch-band grid is NOT run here. WP3 reports the pre-registered primary cell only; the grid belongs to WP6's discretion audit, where the spread across parameterisations is the question rather than a sensitivity footnote. Running it twice would double the count for one answer.

## WP4 - what each component adds on top of the others

**Produced:** 2026-08-24 · **Reproduce:** `uv run python scripts/run_structure_marginal.py` (offline, deterministic)

Wrapper frozen in every arm: stop at the swing extreme, 5R target, channel trail after 1R, 60-bar cap. D203's finding is that refining a wrapper improves a strategy against its own predecessor and moves the null not at all, so the filters are the only thing that varies.

### (a) Feature quintiles on one trade population - the primary reading

The loosest arm (C1 only) generates the population; every component is annotated onto it as a **continuous** feature. Promotion criteria are `feature_analysis`'s, unchanged: |rho| >= 0.2, the same sign in both halves of the sample, and quintile means stepping monotonically.

| symbol | feature | n | rho(MFE) | first half | second half | verdict |
|---|---|---:|---:|---:|---:|---|
| `BTCUSDT` | fib_depth | 3,750 | +0.183 | +0.182 | +0.185 | NO |
| `BTCUSDT` | gap_distance_atr | 3,418 | -0.214 | -0.220 | -0.212 | CANDIDATE |
| `BTCUSDT` | atr_to_golden | 3,750 | -0.243 | -0.265 | -0.224 | CANDIDATE |
| `BTCUSDT` | rsi | 3,750 | -0.019 | -0.034 | -0.004 | NO |
| `BTCUSDT` | stop_atr | 3,750 | -0.307 | -0.324 | -0.293 | CANDIDATE |
| `BTCUSDT` | bars_waited | 3,750 | -0.059 | -0.020 | -0.099 | NO |
| `ETHUSDT` | fib_depth | 3,640 | +0.178 | +0.209 | +0.145 | NO |
| `ETHUSDT` | gap_distance_atr | 3,357 | -0.205 | -0.220 | -0.188 | CANDIDATE |
| `ETHUSDT` | atr_to_golden | 3,640 | -0.246 | -0.268 | -0.223 | CANDIDATE |
| `ETHUSDT` | rsi | 3,640 | -0.022 | -0.058 | +0.014 | NO |
| `ETHUSDT` | stop_atr | 3,640 | -0.301 | -0.311 | -0.289 | CANDIDATE |
| `ETHUSDT` | bars_waited | 3,640 | -0.028 | -0.031 | -0.027 | NO |

Depth quintiles on `BTCUSDT` - the gradient the ladder in WP3 predicted:

| quintile | depth range | n | mean MFE | mean MAE | win rate |
|---:|---|---:|---:|---:|---:|
| 1 | 0.000 - 0.176 | 750 | +1.0067 | -0.6576 | 25.2% |
| 2 | 0.176 - 0.265 | 750 | +1.1986 | -0.6773 | 25.7% |
| 3 | 0.265 - 0.363 | 750 | +1.3815 | -0.6954 | 24.7% |
| 4 | 0.364 - 0.492 | 750 | +1.4876 | -0.7681 | 15.9% |
| 5 | 0.492 - 0.999 | 750 | +2.3205 | -1.2025 | 13.2% |

Depth quintiles on `ETHUSDT` - the gradient the ladder in WP3 predicted:

| quintile | depth range | n | mean MFE | mean MAE | win rate |
|---:|---|---:|---:|---:|---:|
| 1 | 0.002 - 0.177 | 728 | +1.0457 | -0.6453 | 32.4% |
| 2 | 0.177 - 0.266 | 728 | +1.1749 | -0.6828 | 30.8% |
| 3 | 0.267 - 0.360 | 728 | +1.2563 | -0.7014 | 28.3% |
| 4 | 0.360 - 0.489 | 728 | +1.6680 | -0.8509 | 24.9% |
| 5 | 0.489 - 0.996 | 728 | +2.5930 | -1.2794 | 16.5% |

### (b) The same features WITHIN depth quintiles - the reading D208 forced

D208 found that retracement depth explains every apparent effect in the strategy, so *does this component add anything* now means *does it add anything at a given depth*. Trades are split into depth quintiles and each feature is ranked inside each one, holding depth roughly constant while the feature varies.

| symbol | feature | rho by depth quintile (1 shallow -> 5 deep) | max abs | signs agree |
|---|---|---|---:|:--:|
| `BTCUSDT` | gap_distance_atr | -0.15 / -0.25 / -0.14 / -0.13 / -0.02 | 0.247 | yes |
| `BTCUSDT` | atr_to_golden | -0.21 / -0.32 / -0.17 / -0.12 / -0.03 | 0.319 | yes |
| `BTCUSDT` | rsi | -0.01 / +0.00 / -0.04 / +0.04 / -0.07 | 0.074 | no |
| `BTCUSDT` | stop_atr | -0.23 / -0.35 / -0.24 / -0.22 / -0.28 | 0.350 | yes |
| `BTCUSDT` | bars_waited | -0.11 / +0.01 / -0.09 / -0.02 / +0.01 | 0.110 | no |
| `ETHUSDT` | gap_distance_atr | -0.20 / -0.20 / -0.13 / -0.12 / -0.03 | 0.199 | yes |
| `ETHUSDT` | atr_to_golden | -0.23 / -0.26 / -0.15 / -0.11 / -0.06 | 0.265 | yes |
| `ETHUSDT` | rsi | -0.05 / +0.03 / -0.10 / +0.01 / +0.02 | 0.097 | no |
| `ETHUSDT` | stop_atr | -0.25 / -0.31 / -0.21 / -0.21 / -0.31 | 0.309 | yes |
| `ETHUSDT` | bars_waited | -0.03 / -0.04 / +0.00 / -0.05 / +0.04 | 0.050 | no |

The promotion bar is |rho| >= 0.2. A feature that never reaches it inside any depth bucket is a proxy for depth and nothing more.

#### (b2) The same features within STOP-WIDTH quintiles

MFE is measured in R, and `MFE_R = excursion / risk`. So anything that varies with leg size relative to ATR inherits a correlation with it **arithmetically**, whether or not it means anything. This holds stop width roughly constant instead of depth.

| symbol | feature | rho by stop-width quintile | max abs | signs agree |
|---|---|---|---:|:--:|
| `BTCUSDT` | fib_depth | +0.01 / -0.02 / +0.03 / +0.04 / +0.07 | 0.071 | no |
| `BTCUSDT` | gap_distance_atr | +0.10 / +0.08 / -0.05 / +0.06 / -0.09 | 0.101 | no |
| `BTCUSDT` | atr_to_golden | +0.05 / +0.08 / -0.04 / +0.02 / -0.13 | 0.129 | no |
| `BTCUSDT` | rsi | -0.04 / -0.03 / -0.03 / +0.00 / -0.04 | 0.036 | no |
| `BTCUSDT` | bars_waited | -0.02 / +0.01 / -0.05 / -0.01 / -0.04 | 0.053 | no |
| `ETHUSDT` | fib_depth | +0.04 / -0.03 / +0.05 / +0.02 / +0.06 | 0.064 | no |
| `ETHUSDT` | gap_distance_atr | +0.07 / +0.06 / -0.04 / +0.05 / -0.09 | 0.091 | no |
| `ETHUSDT` | atr_to_golden | +0.03 / +0.08 / -0.07 / -0.02 / -0.13 | 0.130 | no |
| `ETHUSDT` | rsi | +0.03 / -0.07 / -0.07 / -0.02 / -0.00 | 0.073 | no |
| `ETHUSDT` | bars_waited | +0.05 / -0.04 / +0.02 / -0.05 / -0.01 | 0.052 | no |

#### Are the surviving features three things or one?

Pairwise rank correlation between the features themselves. Added after the corrected run returned three candidates whose signs and magnitudes were suspiciously alike.

**`BTCUSDT`**

| | fib_depth | gap_distance_atr | atr_to_golden | rsi | stop_atr | bars_waited |
|---|---:|---:|---:|---:|---:|---:|
| fib_depth | +1.00 | -0.55 | -0.76 | -0.07 | -0.57 | -0.11 |
| gap_distance_atr | -0.55 | +1.00 | +0.82 | -0.03 | +0.79 | +0.17 |
| atr_to_golden | -0.76 | +0.82 | +1.00 | +0.00 | +0.87 | +0.13 |
| rsi | -0.07 | -0.03 | +0.00 | +1.00 | -0.01 | -0.01 |
| stop_atr | -0.57 | +0.79 | +0.87 | -0.01 | +1.00 | +0.12 |
| bars_waited | -0.11 | +0.17 | +0.13 | -0.01 | +0.12 | +1.00 |

**`ETHUSDT`**

| | fib_depth | gap_distance_atr | atr_to_golden | rsi | stop_atr | bars_waited |
|---|---:|---:|---:|---:|---:|---:|
| fib_depth | +1.00 | -0.54 | -0.75 | -0.04 | -0.57 | -0.09 |
| gap_distance_atr | -0.54 | +1.00 | +0.83 | -0.04 | +0.80 | +0.16 |
| atr_to_golden | -0.75 | +0.83 | +1.00 | -0.02 | +0.88 | +0.11 |
| rsi | -0.04 | -0.04 | -0.02 | +1.00 | -0.03 | -0.02 |
| stop_atr | -0.57 | +0.80 | +0.88 | -0.03 | +1.00 | +0.10 |
| bars_waited | -0.09 | +0.16 | +0.11 | -0.02 | +0.10 | +1.00 |

### (c) The ablation lattice - confirmation

All 8 subsets of {C2, C3, C4}, identical wrapper, identical setups. C5 is absent by D206: RSI at 30/70 leaves 2 stacked entries on both symbols, and it is carried as a continuous feature in (a) instead. **Trade counts are printed beside every number - an arm that wins on nine trades has not won.**

| symbol | arm | trades | untradeable | hit rate | median R (40bp) | mean R, takeable only (40bp) | mean R (0bp, diagnostic) | median entry depth | stops/targets/caps |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `BTCUSDT` | C1 | 3,025 | 44% | 21.0% | -1.379 | -0.495 | +0.013 | 0.308 | 2141/137/747 |
| `BTCUSDT` | C1+C2 | 811 | 51% | 18.6% | -1.568 | -0.534 | -0.022 | 0.407 | 642/31/138 |
| `BTCUSDT` | C1+C3 | 2,329 | 71% | 15.4% | -2.025 | -0.590 | -0.000 | 0.547 | 2018/167/144 |
| `BTCUSDT` | C1+C4 | 1,006 | 44% | 22.5% | -1.342 | -0.501 | +0.098 | 0.448 | 719/54/233 |
| `BTCUSDT` | C1+C2+C3 | 368 | 70% | 10.3% | -2.007 | -0.864 | -0.160 | 0.518 | 332/16/20 |
| `BTCUSDT` | C1+C2+C4 | 248 | 50% | 16.1% | -1.561 | -0.668 | -0.021 | 0.466 | 198/13/37 |
| `BTCUSDT` | C1+C3+C4 | 573 | 66% | 17.3% | -1.817 | -0.502 | +0.142 | 0.574 | 481/49/43 |
| `BTCUSDT` | C1+C2+C3+C4 | 118 | 67% | 11.0% | -1.801 | -1.058 | -0.038 | 0.538 | 102/8/8 |
| `ETHUSDT` | C1 | 2,999 | 32% | 27.5% | -1.185 | -0.401 | +0.093 | 0.309 | 2100/160/739 |
| `ETHUSDT` | C1+C2 | 881 | 31% | 24.1% | -1.371 | -0.575 | -0.017 | 0.406 | 688/36/157 |
| `ETHUSDT` | C1+C3 | 2,308 | 54% | 20.7% | -1.709 | -0.572 | +0.043 | 0.556 | 1997/170/141 |
| `ETHUSDT` | C1+C4 | 1,038 | 31% | 26.9% | -1.212 | -0.440 | +0.074 | 0.443 | 748/50/240 |
| `ETHUSDT` | C1+C2+C3 | 368 | 52% | 16.8% | -1.737 | -0.607 | -0.039 | 0.527 | 321/22/25 |
| `ETHUSDT` | C1+C2+C4 | 254 | 30% | 21.7% | -1.463 | -0.641 | -0.149 | 0.462 | 204/4/46 |
| `ETHUSDT` | C1+C3+C4 | 551 | 49% | 22.7% | -1.598 | -0.558 | +0.125 | 0.570 | 462/42/47 |
| `ETHUSDT` | C1+C2+C3+C4 | 104 | 50% | 15.4% | -1.751 | -0.815 | -0.102 | 0.547 | 88/4/12 |

**`untradeable` is the share of trades whose 40 bps round trip costs at least their entire risk.** A stop placed at the swing extreme, entered at a shallow retracement, can sit a few basis points away, and the plain mean R for those trades runs to -100 and worse. That is correct arithmetic describing a position size nobody can take, so the median and the takeable-only mean are what the table reports and the raw mean is left in the JSON.

The zero-cost column is a **diagnostic and never a strategy** - D202's device for separating 'no information' from 'information this cost structure cannot support'.

### What the readings say

**Unconditionally, `atr_to_golden`, `gap_distance_atr`, `stop_atr` clear the promotion criteria on both symbols — and the next two paragraphs take that back.** The bar is `feature_analysis`'s, unchanged: |rho| >= 0.2, the same sign in both halves, and quintile means stepping monotonically.

| feature | `BTCUSDT` rho / verdict | `ETHUSDT` rho / verdict |
|---|---|---|
| fib_depth | +0.183 / NO | +0.178 / NO |
| gap_distance_atr | -0.214 / CANDIDATE | -0.205 / CANDIDATE |
| atr_to_golden | -0.243 / CANDIDATE | -0.246 / CANDIDATE |
| rsi | -0.019 / NO | -0.022 / NO |
| stop_atr | -0.307 / CANDIDATE | -0.301 / CANDIDATE |
| bars_waited | -0.059 / NO | -0.028 / NO |

**And the survivors are one quantity, not three.** Pairwise rank correlation between them: `BTCUSDT` gap_distance_atr~atr_to_golden +0.82, `BTCUSDT` gap_distance_atr~stop_atr +0.79, `BTCUSDT` atr_to_golden~stop_atr +0.87, `ETHUSDT` gap_distance_atr~atr_to_golden +0.83, `ETHUSDT` gap_distance_atr~stop_atr +0.80, `ETHUSDT` atr_to_golden~stop_atr +0.88. `stop_atr` is leg size relative to ATR; `atr_to_golden` is a distance to a fixed fraction of the same leg, in the same ATR units; `gap_distance_atr` is a distance to a level inside it. **MFE is measured in R, so `MFE_R = excursion / risk` correlates with leg size arithmetically** — which is what all three are reporting.

**Conditioned on depth, the largest rank correlation any component reaches in any depth bucket is** `BTCUSDT` gap_distance_atr 0.25, atr_to_golden 0.32, rsi 0.07, stop_atr 0.35, bars_waited 0.11 and `ETHUSDT` gap_distance_atr 0.20, atr_to_golden 0.26, rsi 0.10, stop_atr 0.31, bars_waited 0.05, against the promotion bar of 0.2. Signs agreeing across all five depth buckets: `BTCUSDT` gap_distance_atr, atr_to_golden, stop_atr; `ETHUSDT` gap_distance_atr, atr_to_golden, stop_atr. A component that neither clears the bar nor holds its sign inside depth buckets is carrying nothing depth does not already carry.

**And holding leg size constant instead, everything collapses.** Inside stop-width quintiles the largest rank correlation ANY feature reaches in ANY bucket is 0.13 on `BTCUSDT` and 0.13 on `ETHUSDT`, against a bar of 0.2, and not one of them holds its sign across all five buckets. Depth included. **That is the verdict: once leg size relative to ATR is held constant, no component of this strategy predicts anything.**

**The lattice shows the mechanism.** Median entry depth rises from 0.308 to 0.538 on `BTCUSDT` and 0.309 to 0.547 on `ETHUSDT` as the filters stack — they enter deeper, which is what D206's census predicted and D208 showed is the whole of it. The fully-stacked arm holds 118 and 104 trades, so it is powered enough to carry a verdict, and the verdict is that at zero cost it earns -0.038R and -0.102R a trade against the base arm's +0.013R and +0.093R — **stacking all four filters makes it worse, before costs.**

**Every arm loses at 40 bps, and most of them lose before costs too.** Median net R on the base arm is -1.379 and -1.185, with 44% and 32% of its trades untradeable outright — the round trip costs at least their whole risk. The zero-cost diagnostic on the same arm is +0.013 and +0.093 mean R, which separates 'no information' from 'information the costs ate': there was not much to eat.

### Multiplicity

| reading | cells | looks |
|---|---|---:|
| (a) feature quintiles | 6 features x 2 symbols | 12 |
| (b) conditional on depth | 5 features x 2 symbols | 10 |
| (b2) conditional on stop width | 5 features x 2 symbols | 10 |
| collinearity matrix | diagnostic, not a test | 0 |
| (c) ablation lattice | 8 arms x 2 symbols | 16 |
| **WP4 total** | | **48** |

Reading (b) was not pre-registered - D208 created the question it answers. It is counted in full rather than folded into (a), and like D208's depth-matched null it makes the verdict harsher rather than kinder.

## WP6 - the discretion audit

**Produced:** 2026-08-24 · **Reproduce:** `uv run python scripts/run_structure_audit.py` (offline, deterministic)

The course's method is discretionary: a human decides what counts as a swing, how close is close enough, which gap matters. Mechanising it replaced those judgements with parameters, and this measures how much the answer depends on them. **If the sign flips across plausible parameterisations, the strategy is a judgement call wearing a rule's clothes.**

| symbol | k | touch | setups | stacked | base zero-cost mean R | stacked zero-cost mean R | stacking helps? | max abs rho within stop quintiles |
|---|---:|---:|---:|---:|---:|---:|:--:|---:|
| `BTCUSDT` **(primary)** | 2 | 0.5 | 3,875 | 120 | +0.013 | -0.038 | no | 0.13 |
| `BTCUSDT` | 2 | 1.0 | 3,875 | 244 | +0.013 | -0.021 | no | 0.13 |
| `BTCUSDT` | 3 | 0.5 | 2,808 | 67 | +0.017 | -0.204 | no | 0.10 |
| `BTCUSDT` | 3 | 1.0 | 2,808 | 131 | +0.017 | -0.137 | no | 0.10 |
| `ETHUSDT` **(primary)** | 2 | 0.5 | 3,753 | 106 | +0.093 | -0.102 | no | 0.13 |
| `ETHUSDT` | 2 | 1.0 | 3,753 | 239 | +0.093 | +0.011 | no | 0.13 |
| `ETHUSDT` | 3 | 0.5 | 2,717 | 45 | +0.065 | -0.337 | no | 0.15 |
| `ETHUSDT` | 3 | 1.0 | 2,717 | 137 | +0.065 | -0.183 | no | 0.15 |

Per feature, the largest |rho| reached inside any stop-width quintile, across every cell of the grid:

| symbol | cell | fib_depth | gap_distance_atr | atr_to_golden | rsi | bars_waited |
|---|---|---:|---:|---:|---:|---:|
| `BTCUSDT` | k2/touch0.5 | 0.07 | 0.10 | 0.13 | 0.04 | 0.05 |
| `BTCUSDT` | k2/touch1.0 | 0.07 | 0.10 | 0.13 | 0.04 | 0.05 |
| `BTCUSDT` | k3/touch0.5 | 0.10 | 0.09 | 0.07 | 0.07 | 0.10 |
| `BTCUSDT` | k3/touch1.0 | 0.10 | 0.09 | 0.07 | 0.07 | 0.10 |
| `ETHUSDT` | k2/touch0.5 | 0.06 | 0.09 | 0.13 | 0.07 | 0.05 |
| `ETHUSDT` | k2/touch1.0 | 0.06 | 0.09 | 0.13 | 0.07 | 0.05 |
| `ETHUSDT` | k3/touch0.5 | 0.12 | 0.13 | 0.15 | 0.07 | 0.05 |
| `ETHUSDT` | k3/touch1.0 | 0.12 | 0.13 | 0.15 | 0.07 | 0.05 |

### What the audit says

**The verdict does not depend on the parameters.** Across all 8 cells of the pre-registered grid, the largest rank correlation any feature reaches inside any stop-width quintile ranges from **0.10 to 0.15**, against a promotion bar of 0.2. Not one cell produces a feature that would be promoted.

**Stacking the filters helps at zero cost in 0 of 8 cells.** It never helps.

**The base arm's zero-cost mean R ranges from +0.013 to +0.093** across the grid — indistinguishable from zero everywhere, in both signs, with no cell approaching the 27%-44% of trades that are untradeable at 40 bps. The strategy is not sensitive to its parameters because there is nothing there for a parameter to be sensitive to.

**The one honest caveat about this audit:** a verdict that is stable because the effect is zero is a weaker demonstration than a verdict that is stable while an effect is present. This grid shows that the *absence* is robust. It cannot show that a present effect would have been, because there is none to test that way.

### Multiplicity

| grid re-runs of D210's two readings | 2 symbols x 4 cells | 8 |
|---|---|---:|
| **WP6 total** | | **8** |

The primary cell is re-reported here rather than re-tested; it was already counted in WP4 and is not double-counted. The three non-primary cells per symbol are the new looks.

## FINAL REPORT — the structure programme is closed after 86 looks

**Produced:** 2026-08-24 · Recorded as D211.

### The strategy, and what it turned out to be

Five components, taught as a system: wait for a **change of character**, then enter the
pullback where a **flipped level**, the **61.8% Fibonacci retracement** and a **fair value
gap** stack up, filtered by **RSI**, with a stop past the swing extreme and a 5R target.

| | what was claimed | what it measured |
|---|---|---|
| **C1** change of character | the trigger; a trend flip you can trade | BTC Sharpe +0.124 at the **66th percentile** of its rotation null; ETH −0.068 at the 44th. Fails the both-symbols rule (D208) |
| **C2** the flipped level | support becomes resistance | **negative** against a matched placebo, on both symbols, matched or unmatched (D208) |
| **C3** the golden ratio | 0.618 is special; "how the universe is coded" | ranks **4 of 8** against seven other numbers on the same legs, and **loses to 0.691 and 0.724** in 97%+ of paired bootstrap draws (D208) |
| **C4** the fair value gap | a 3-bar imbalance price returns to | **+0.082 at the 100th percentile** — until matched on depth, where it becomes **+0.006 / −0.006** (D208) |
| **C5** RSI, the control | a supporting filter | beat all three structural components, then collapsed with them (D208/D210) |

And the unifying result: **not one of them predicts anything once leg size relative to ATR
is held constant.** Inside stop-width quintiles the largest rank correlation any feature
reaches, in any bucket, in any cell of the grid, is **0.15** against a promotion bar of 0.2
(D210, D211).

### The three findings that do not depend on any of that

**1. The course's own arithmetic fails once costs exist.** It claims a 5R target breaks even
at "two out of ten". Frictionless the true figure is 16.7%, so the claim is nearly right —
and at 40 bps it is **22.3% to 28.4%**. A 20% hit rate at 5R loses money in every cell
measured. This needed no backtest and does not depend on whether any component works
(D206/D209).

**2. Between 27% and 44% of the base arm's trades are untradeable outright.** Their 40 bps
round trip costs at least their entire risk. A stop at a 15m swing extreme is simply close
enough that crossing the spread twice is a material fraction of the whole trade (D210).

**3. The confluence is a tax, not precision.** Risk is `(1 − retracement) × |leg span|`, so
a deeper entry is a *tighter* stop. Stacking the filters moves median entry depth from 0.31
to 0.54 and raises friction from **0.48R to 0.71R**. And at **zero cost** the fully-stacked
arm earns −0.038R and −0.102R a trade against the base arm's +0.013R and +0.093R: stacking
all four filters makes the strategy worse before costs are even considered (D209/D210).

### What is closed, and what is not

**Closed:** these five components, mechanised as `STRUCTURE_MODEL.md` defines them, on
BTC/ETH 15m bars, as a source of tradeable directional signal. No further statistic, sizing
rule, exit policy or threshold will be pre-registered on them.

**Not closed:** the components themselves are reusable and several are pinned by test —
the BOS/CHoCH state machine with its D173 lag, the fair-value-gap detector, the R-unit
excursion, the depth-matched and stop-width-matched controls. Nor is this a claim about
price action as a concept, or about the course's method as practised by a human. It is a
result about **these definitions, on these bars, in this decade**.

**The one thing this study cannot tell you** is whether the discretionary version works. The
course's method is not the mechanised one, and a human drawing the lines is doing something
this programme deliberately removed. A negative here does not refute them — and, more to the
point, a positive would not have vindicated them either.

### What outlives the programme

Six things, most of them learned from defects rather than results.

1. **A guard that drops bad input converts a wrong answer into a missing one** (D205, D206,
   D209 — three times in six work packages). A mirrored state machine that produced no
   bullish legs, an `if window:` that dropped 9% of setups, and a stop on the wrong side of
   the trade that rejected 93% of them. Each was invisible to tests written over the outputs
   the component still produced.
2. **Count what a guard drops, and put the count where someone will compare it to another
   count** (D209). The stop defect surfaced because the census said 120 stacked setups and
   the lattice reported 2 trades. Not a test — two numbers that should have agreed.
3. **Mutate the module when the suite passes first time** (D205). Two of six deliberate
   mutations survived 43 green tests, one of them the pre-registered definition of a change
   of character.
4. **A scale-dependent quantity ranked across eras is an artifact generator** (D210, and
   D187 before it). MFE as a fraction of entry price made `stop_atr` a candidate at
   rho +0.56. In R units it is nothing.
5. **When several features come back with suspiciously similar verdicts, correlate them
   with each other before believing any of them** (D210). Three candidates, pairwise rank
   correlation +0.79 to +0.88 — one quantity under three names.
6. **A placebo has to be matched on the thing that actually varies** (D208). The fair value
   gap beat a uniformly-drawn band at the 100th percentile and beat a depth-matched one by
   nothing, because real gaps sit at retracement 0.63 and uniform placebos sit at 0.44.

Two disclosures kept visible: **the depth-matched null and the stop-width control were both
post-hoc**, designed after seeing a result, counted in full in the ledger, and both made the
verdict harsher rather than kinder. And **D196's adverse selection is not paid in this
study** (D207) — entry is a market order at the close, so a trader running the course's
actual limit-at-the-level method should subtract something in the 0.138–0.195 Sharpe range
that D196 measured.

### Multiplicity ledger — final

| | looks |
|---|---:|
| WP3 components against their placebos | 24 |
| WP3 depth-matched re-reading (post-hoc) | 6 |
| WP4 feature quintiles | 12 |
| WP4 conditional on depth (post-hoc) | 10 |
| WP4 conditional on stop width (post-hoc) | 10 |
| WP4 ablation lattice | 16 |
| WP6 discretion audit | 8 |
| Post-close Sharpe/PnL addendum (D212) | 16 |
| **Total on one hypothesis** | **102** |

WP0, WP1 and WP2 contribute zero: a pre-registration, a detector suite and a census are not
tests. WP5 never ran — D210 triggered the pre-registered stop.

Disclosed adjacent and separately counted: the terrain programme's **259 looks**
(`TERRAIN_RESULTS.md`). Its stop does not bind this construction, and the pre-committed
inheritance rule in D204 — if the flipped level had been the only survivor, D196's 20 looks
would join this total — did not trigger, because the flipped level did not survive either.

A different data source, a different claim, or a genuinely new construction starts a new
document and a new ledger, with this one disclosed.

---

## ADDENDUM (post-close) - every arm in Sharpe and PnL, against baselines

**Produced:** 2026-08-24 · **Reproduce:** `uv run python scripts/run_structure_pnl.py` (offline, deterministic)

**The programme is closed (D211). This is not a new test and it cannot rescue anything.** It restates arms that have already been run in two units the study never reported — annualised Sharpe and money — because *mean R per trade* is not what most people mean when they ask how a strategy did. Every look is counted in the ledger, and the rule is stated in advance: **a positive here would be a new hypothesis requiring its own pre-registration, not a result.**

**Sizing rule, which the study never had:** constant unit exposure while in a trade, flat otherwise, cost charged on every unit of exposure changed. The same `PositionResult` path D197-D202 used, reused rather than rewritten so these numbers sit on the same footing as the terrain programme's. It deliberately avoids fixed-fractional risk: on a book where a large share of trades cost at least their whole risk to trade, fixed-fractional sizing produces an equity curve that says more about the sizing rule than about the signal.

**Costs:** three tiers, all **per side**, so a round trip pays twice each (D212). Zero is the D202 diagnostic and never a strategy; 10 bps/side is roughly a real Binance spot taker fee, so the result cannot be waved away as a punitive assumption; 40 bps/side is `breakout_study`'s `taker_40bp`, the tier every other study in this repo uses. Capital 10,000 units, Sharpe annualised at 35,040 periods. Buy-and-hold pays one round trip and is shown unchanged across tiers.

### `BTCUSDT` — 8.3 years, 294,336 bars

| arm | trades | exposure | Sharpe / PnL @ zero (diagnostic) | Sharpe / PnL @ 10 bps/side | Sharpe / PnL @ 40 bps/side | max DD (40bp) |
|---|---:|---:|---:|---:|---:|---:|
| C1 | 3,025 | 32.6% | -0.10 / -2,657 | -2.15 / -9,983 | -7.98 / -10,000 | -100.0% |
| C1+C2 | 811 | 8.3% | -0.35 / -3,689 | -1.56 / -8,755 | -4.95 / -9,991 | -99.9% |
| C1+C3 | 2,329 | 16.5% | +0.27 / +6,843 | -2.15 / -9,841 | -8.79 / -10,000 | -100.0% |
| C1+C4 | 1,006 | 11.0% | +0.27 / +5,858 | -0.91 / -7,882 | -4.31 / -9,995 | -100.0% |
| C1+C2+C3 | 368 | 2.7% | -0.63 / -3,471 | -1.72 / -6,874 | -4.59 / -9,658 | -96.6% |
| C1+C2+C4 | 248 | 2.4% | -0.44 / -2,746 | -1.11 / -5,584 | -2.97 / -9,006 | -90.7% |
| C1+C3+C4 | 573 | 4.5% | +0.60 / +8,057 | -0.56 / -4,263 | -3.79 / -9,817 | -98.3% |
| C1+C2+C3+C4 | 118 | 0.9% | -0.38 / -1,368 | -0.98 / -3,184 | -2.56 / -6,648 | -67.8% |
| **buy and hold** | 1 | 100% | +0.32 / +46,000 | +0.32 / +46,000 | +0.32 / +46,000 | -77.2% |
| **cash** | 0 | 0% | +0.00 / +0 | +0.00 / +0 | +0.00 / +0 | 0.0% |

### `ETHUSDT` — 8.3 years, 294,336 bars

| arm | trades | exposure | Sharpe / PnL @ zero (diagnostic) | Sharpe / PnL @ 10 bps/side | Sharpe / PnL @ 40 bps/side | max DD (40bp) |
|---|---:|---:|---:|---:|---:|---:|
| C1 | 2,999 | 32.2% | +0.77 / +178,800 | -0.80 / -9,532 | -5.36 / -10,000 | -100.0% |
| C1+C2 | 881 | 8.8% | -0.31 / -4,179 | -1.31 / -9,001 | -4.18 / -9,995 | -100.0% |
| C1+C3 | 2,308 | 16.0% | +0.47 / +22,250 | -1.39 / -9,682 | -6.70 / -10,000 | -100.0% |
| C1+C4 | 1,038 | 11.0% | +0.51 / +19,792 | -0.46 / -6,267 | -3.28 / -9,993 | -99.9% |
| C1+C2+C3 | 368 | 2.8% | -0.07 / -595 | -0.91 / -5,497 | -3.26 / -9,508 | -95.2% |
| C1+C2+C4 | 254 | 2.5% | -0.07 / -659 | -0.63 / -4,381 | -2.21 / -8,781 | -87.8% |
| C1+C3+C4 | 551 | 4.4% | +0.65 / +11,615 | -0.28 / -2,823 | -2.95 / -9,739 | -97.6% |
| C1+C2+C3+C4 | 104 | 0.8% | -0.01 / -55 | -0.50 / -1,923 | -1.85 / -5,679 | -60.0% |
| **buy and hold** | 1 | 100% | +0.11 / +11,521 | +0.11 / +11,521 | +0.11 / +11,521 | -90.6% |
| **cash** | 0 | 0% | +0.00 / +0 | +0.00 / +0 | +0.00 / +0 | 0.0% |

### What this shows

**After costs, 0 of 16 arms make money.** None. Sharpe ranges -8.79 to -1.85 and PnL ranges -10,000 to -5,679 on 10,000 of capital.

**At zero cost, 7 of 16 make money**, with Sharpe between -0.63 and +0.77. That is the D202 diagnostic doing its job: it separates *no information* from *information this cost structure cannot support*.

**The largest of those is worth naming rather than leaving for a reader to spot.** `ETHUSDT` C1 returns +1,788% at zero cost, Sharpe +0.77 — which beats buy-and-hold. It is in the market 32% of the time and takes 2,999 round trips to do it, and it dies at the first fee tier: 10 bps a side takes it to -9,532. A book that cannot survive a tenth of a percent per side is not an edge with a cost problem; it is turnover with no edge.

**`BTCUSDT`** — buy and hold returns +460.0% at Sharpe +0.32 over the same span, against the best arm's -66.5% at -2.56 (C1+C2+C3+C4). The passive baseline is not a high bar to clear and no arm clears it.
**`ETHUSDT`** — buy and hold returns +115.2% at Sharpe +0.11 over the same span, against the best arm's -56.8% at -1.85 (C1+C2+C3+C4). The passive baseline is not a high bar to clear and no arm clears it.

**At a realistic 10 bps/side, 0 of 16 arms make money.** None. So the verdict does not rest on the 40 bps tier being generous.

**Why the costed losses are so total.** These are constant-notional books taking 104 to 3,025 round trips over 8.3 years. At 40 bps a side that is 80 bps a round trip, and the base arm's 3,000-odd trips compound to roughly 24 e-folds of fee drag — arithmetically ruinous, and exactly the same statement as D206's finding that a large share of these trades cost at least their entire risk to put on. It is not a bug and it is not a knife-edge: at a quarter of the fee the picture is the same.

**One number that matters for reading the Sharpes:** these books are in the market 1% to 33% of the time. A Sharpe computed over the whole series on a book that is mostly flat is diluted toward zero by the flat bars, so a small magnitude in the zero-cost column should not be read as *nearly* working. The PnL column is the unambiguous one.

### Multiplicity

| | cells | looks |
|---|---|---:|
| post-close Sharpe/PnL restatement | 8 arms x 2 symbols | 16 |
| **addendum total** | | **16** |

Counted in full even though no arm is under test, because a metric computed on a configuration is a look at it whatever the intent — the same rule that made D189 count three metrics across sixteen configurations as 48.

## D213 - can selection rescue it? A mined rule on a held-out seven years

**Produced:** 2026-08-24 · **Reproduce:** `uv run python scripts/run_structure_selection.py` (offline, deterministic)

Pre-registered in `docs/decisions/D213-conditional-selection-on-a-held-out-year.md` before the mining ran. Development year **2018**, chosen by trade count on both symbols before any outcome was read; every later number excludes it entirely. Mining runs on **gross** R - cost divided by a four-basis-point stop runs past 20R, so mining on net R would be a search for wide stops wearing a search for signal.

### Trades by year, and the year the rule was mined from

| year | `BTCUSDT` | `ETHUSDT` | role |
|---|---:|---:|---|
| 2018 | 385 | 351 | **development** |
| 2019 | 454 | 412 | held out |
| 2020 | 453 | 431 | held out |
| 2021 | 453 | 420 | held out |
| 2022 | 393 | 455 | held out |
| 2023 | 424 | 441 | held out |
| 2024 | 443 | 428 | held out |
| 2025 | 478 | 446 | held out |
| 2026 | 267 | 256 | held out |

### What the 2018 data said about each feature

Median split, no threshold search. A feature is kept only if the same side wins on **both** symbols and gains at least **0.10R** on each.

| feature | better side | `BTCUSDT` edge (R) | `ETHUSDT` edge (R) | sides agree | kept |
|---|---|---:|---:|:--:|:--:|
| fib_depth | below | 0.052 | 0.060 | yes | no |
| stop_atr | below | 0.044 | 0.180 | yes | no |
| rsi | split | 0.111 | 0.383 | no | no |
| bars_waited | above | 0.294 | 0.109 | yes | **KEPT** |
| hour_utc | split | 0.023 | 0.237 | no | no |
| trend_align | — | — | — | — | too thin |
| leg_bars | above | 0.222 | 0.098 | yes | no |
| vol_regime | above | 0.269 | 0.267 | yes | **KEPT** |

Survivors: **bars_waited, vol_regime**.

### The frozen rule, in sample and out

Thresholds are the development year's medians and are **not** recomputed on any holdout year - re-taking the median inside the test data is the quietest form of leakage available, because the result still looks like a holdout.

| symbol | sample | trades | kept | mean gross R (all) | mean gross R (kept) | advantage | mean net R (kept) |
|---|---|---:|---:|---:|---:|---:|---:|
| `BTCUSDT` | 2018 (in sample) | 385 | 20% | -0.017 | +0.472 | +0.489 | -0.690 |
| `BTCUSDT` | all other years (held out) | 3,365 | 26% | +0.013 | -0.115 | -0.128 | -1.850 |
| `ETHUSDT` | 2018 (in sample) | 351 | 23% | +0.036 | +0.301 | +0.265 | -2.593 |
| `ETHUSDT` | all other years (held out) | 3,289 | 27% | +0.066 | +0.050 | -0.016 | -1.476 |

### The same rule, year by year on the holdout

| symbol | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `BTCUSDT` | +0.042 | -0.035 | -0.157 | -0.012 | -0.380 | -0.105 | -0.199 | -0.074 |
| `ETHUSDT` | -0.021 | -0.038 | -0.042 | -0.089 | -0.138 | +0.189 | +0.165 | -0.272 |

Advantage in mean gross R of the filtered trades over all trades, that year.

### The feature that was never tested, tested

`trend_align` was pre-registered and then silently dropped: a median split on a +/-1 variable puts the median at one of the two values, so one side comes back empty and the thinness guard removes the feature. It disappeared from the table above without appearing as a failure - D196's H4 in a new costume, caught by checking which keys the output contains rather than trusting that eight features in means eight features out.

Split at zero instead, and run **standalone**: the mined rule was frozen before this ran and is deliberately not re-mined to include it, because re-mining after seeing the holdout is the move the whole design exists to prevent.

| symbol | sample | with the trend | against it | edge (R) |
|---|---|---:|---:|---:|
| `BTCUSDT` | 2018 (dev) | +0.001 (218) | -0.040 (167) | +0.041 |
| `BTCUSDT` | held out | +0.018 (1,970) | +0.006 (1,395) | +0.012 |
| `ETHUSDT` | 2018 (dev) | +0.116 (197) | -0.067 (154) | +0.183 |
| `ETHUSDT` | held out | +0.101 (1,947) | +0.014 (1,342) | +0.087 |

### The control that makes those numbers readable

The identical mining procedure, run 200 times on the same 2018 trades with the outcomes **shuffled within symbol** - every marginal distribution preserved, only the pairing between feature and outcome destroyed.

| | value |
|---|---:|
| draws that produced at least one survivor | 54% |
| mean survivors per draw | 0.83 |
| median in-sample advantage from pure noise | +0.071R |
| 95th percentile | +0.274R |
| largest in 200 draws | +0.410R |
| **the real rule's in-sample advantage** | **+0.377R** |

**A weakness of this control, stated rather than left for a reader to find.** The shuffle is independent per symbol, so it destroys the cross-symbol correlation real outcomes have - BTC and ETH move together. The survivor test requires both symbols to agree on which side wins, and real data gets that agreement more easily than independently-shuffled data does. So this distribution is **narrower than the true selection distribution**, and clearing its 95th percentile is an easier bar than it looks. A block shuffle preserving the cross-symbol pairing would be the right fix and is a different study.

### Verdict

**2 features survived the 2018 split: bars_waited, vol_regime.** In sample the rule gains +0.489R and +0.265R on the two symbols. H1 confirmed, as predicted at high confidence — with eight features and a low bar, something always survives.

**Out of sample it gains -0.128R and -0.016R**, against the pre-registered hurdle of +0.10R on both symbols. **It does not clear it.**

The out-of-sample advantage is -26% and -6% of the in-sample one — H2 predicted under half.

**Against the shuffled control the real in-sample advantage of +0.377R sits above the noise distribution** (95th percentile +0.274R, largest of 200 draws +0.410R). So the mining found more than a selection effect would have produced.

**H5 was void, not falsified, until the amendment.** `trend_align` never reached the table because a median split cannot divide a binary. Tested properly it gains +0.041R and +0.183R in 2018 and +0.012R and +0.087R on the held-out years — below the +0.10R bar out of sample, so the most-cited missing filter in this style is not the missing piece either.

**After costs the filtered arm returns -1.850R and -1.476R a trade out of sample.** Hurdle 4 fails, as H4 predicted at high confidence: no entry filter changes what the wrapper risks, and the toll is 0.96R on the median base-arm trade.

### Multiplicity

| | cells | looks |
|---|---|---:|
| dev-year feature splits | 8 features x 2 symbols | 16 |
| frozen rule on the holdout | 2 symbols | 2 |
| trend_align standalone (amendment) | dev + holdout x 2 symbols | 4 |
| shuffled control | a control, not a test | 0 |
| **D213 total** | | **22** |

The structure programme's 102 looks are disclosed adjacent and separately counted.

## D214 - the terrain map as a confluence gate

**Produced:** 2026-08-24 · **Reproduce:** `uv run python scripts/run_structure_terrain_gate.py` (offline, deterministic)

**This study overrides D203's stop**, deliberately and for one bounded question. The record and the reasoning are in `docs/decisions/D214-the-terrain-gate.md`, committed before this runner existed. `inverted` is the pre-registered primary because D202 measured this exact reading anti-predictive at the 2.6th percentile - the prior comes from a published result here, not from peeking at this run.

Field: D202's raw parameters (`k=2`, `cluster_atr=0.5`, no erasure) with every window calendar-matched at 96 bars/day per D194 - `atr_window` 1,920, `vol_norm_bars` 8,640. Read at the signal bar, so the bar that decides never also pays.

### A census first: does the discretisation move a gate decision?

`build_grid` spans the whole series' high and low, so the axis a reading is discretised onto knows the eventual price range. `test_terrain_field.py` knew and pinned around it — its look-ahead test passes the same grid to both arms with the comment *"same axis, or the buckets alone would differ"*. That is the right call for a signal, where the axis is a discretisation choice. A **gate** reads only the sign, so the question is whether the sign moves.

**The first version of this census was a tautology and is reported as one.** It compared the full grid against one built from the first half and returned exactly zero on both symbols — because `Grid.bucket` depends only on `ln_min`, this fixture's lowest low falls in the first half, and causal deposits put no mass above the prefix grid's top at an early bar. It could not have failed.

The potent version perturbs the axis **origin** by half a bucket, the largest misalignment the discretisation admits:

| symbol | trades | mean shift in reading | max shift | sign flips |
|---|---:|---:|---:|---:|
| `BTCUSDT` | 3,750 | 0.0748 | 1.1017 | **215** (5.73%) |
| `ETHUSDT` | 3,640 | 0.0573 | 0.9375 | **145** (3.98%) |

Reported before the verdict, in counts, because that is when a census is worth anything.

### The gate, every cell

| symbol | gate | kept | gross R (kept) | gross R (all) | advantage | gross R of REJECTED | net R @40bp | Sharpe @40bp |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `BTCUSDT` **(primary)** | inverted / zero | 52% (1,944) | -0.020 | +0.010 | -0.030 | +0.043 | -1.642 | -6.00 |
| `BTCUSDT` | inverted / median | 26% (989) | +0.025 | +0.010 | +0.015 | +0.005 | -1.602 | -3.75 |
| `BTCUSDT` | inverted / tertile | 17% (648) | -0.052 | +0.010 | -0.062 | +0.023 | -1.601 | -3.29 |
| `BTCUSDT` | aligned / zero | 48% (1,806) | +0.043 | +0.010 | +0.033 | -0.020 | -2.420 | -5.82 |
| `BTCUSDT` | aligned / median | 24% (886) | -0.038 | +0.010 | -0.048 | +0.025 | -2.776 | -4.74 |
| `BTCUSDT` | aligned / tertile | 16% (601) | -0.112 | +0.010 | -0.122 | +0.034 | -1.884 | -4.42 |
| `ETHUSDT` **(primary)** | inverted / zero | 54% (1,983) | +0.082 | +0.063 | +0.020 | +0.039 | -1.409 | -4.22 |
| `ETHUSDT` | inverted / median | 28% (1,015) | +0.079 | +0.063 | +0.017 | +0.056 | -1.537 | -2.83 |
| `ETHUSDT` | inverted / tertile | 19% (678) | +0.061 | +0.063 | -0.002 | +0.063 | -1.553 | -2.36 |
| `ETHUSDT` | aligned / zero | 46% (1,657) | +0.039 | +0.063 | -0.024 | +0.082 | -1.483 | -4.11 |
| `ETHUSDT` | aligned / median | 22% (805) | -0.001 | +0.063 | -0.064 | +0.081 | -1.588 | -3.12 |
| `ETHUSDT` | aligned / tertile | 15% (534) | +0.058 | +0.063 | -0.005 | +0.063 | -1.650 | -2.28 |

**The rejected column is not decoration.** D198's confirmation filter beat its baseline on both symbols and was worthless, because the signals it discarded scored +0.785 against the kept ones at -0.288. A filter that improves the book it keeps by throwing away the winners is not a filter.

### The control: is it placement or is it selectivity?

The identical gate applied to terrain readings **permuted among setups**. A gate keeping half the trades moves the mean whatever it selects on; this is what separates the map's placement from the gate's selectivity.

| symbol | gate | real advantage | shuffled median | shuffled p95 | shuffled max | beats p95 |
|---|---|---:|---:|---:|---:|:--:|
| `BTCUSDT` | inverted / zero | -0.030 | -0.003 | +0.042 | +0.064 | no |
| `BTCUSDT` | inverted / median | +0.015 | -0.002 | +0.064 | +0.124 | no |
| `BTCUSDT` | inverted / tertile | -0.062 | -0.002 | +0.093 | +0.178 | no |
| `BTCUSDT` | aligned / zero | +0.033 | +0.003 | +0.041 | +0.078 | no |
| `BTCUSDT` | aligned / median | -0.048 | +0.002 | +0.070 | +0.128 | no |
| `BTCUSDT` | aligned / tertile | -0.122 | -0.000 | +0.095 | +0.168 | no |
| `ETHUSDT` | inverted / zero | +0.020 | -0.005 | +0.033 | +0.053 | no |
| `ETHUSDT` | inverted / median | +0.017 | -0.008 | +0.065 | +0.098 | no |
| `ETHUSDT` | inverted / tertile | -0.002 | -0.012 | +0.089 | +0.147 | no |
| `ETHUSDT` | aligned / zero | -0.024 | +0.006 | +0.046 | +0.073 | no |
| `ETHUSDT` | aligned / median | -0.064 | +0.009 | +0.077 | +0.132 | no |
| `ETHUSDT` | aligned / tertile | -0.005 | +0.008 | +0.097 | +0.170 | no |

### The three bars

The deliverable. Each cell's observed Sharpe against three multiplicity counts, with an explicit pass/fail. The combined count is forced by `TERRAIN_RESULTS.md`: *anything that reuses these sensors inherits the count*.

| symbol | gate | Sharpe @40bp | fresh (n=12) | structure only (n=136) | combined (n=395) |
|---|---|---:|---|---|---|
| `BTCUSDT` | inverted / zero | -6.00 | need 1.27 — **fail** | need 1.69 — **fail** | need 1.83 — **fail** |
| `BTCUSDT` | inverted / median | -3.75 | need 1.27 — **fail** | need 1.69 — **fail** | need 1.83 — **fail** |
| `BTCUSDT` | inverted / tertile | -3.29 | need 1.27 — **fail** | need 1.69 — **fail** | need 1.83 — **fail** |
| `BTCUSDT` | aligned / zero | -5.82 | need 1.27 — **fail** | need 1.69 — **fail** | need 1.83 — **fail** |
| `BTCUSDT` | aligned / median | -4.74 | need 1.27 — **fail** | need 1.69 — **fail** | need 1.83 — **fail** |
| `BTCUSDT` | aligned / tertile | -4.42 | need 1.27 — **fail** | need 1.69 — **fail** | need 1.83 — **fail** |
| `ETHUSDT` | inverted / zero | -4.22 | need 1.27 — **fail** | need 1.69 — **fail** | need 1.83 — **fail** |
| `ETHUSDT` | inverted / median | -2.83 | need 1.27 — **fail** | need 1.69 — **fail** | need 1.83 — **fail** |
| `ETHUSDT` | inverted / tertile | -2.36 | need 1.27 — **fail** | need 1.69 — **fail** | need 1.83 — **fail** |
| `ETHUSDT` | aligned / zero | -4.11 | need 1.27 — **fail** | need 1.69 — **fail** | need 1.83 — **fail** |
| `ETHUSDT` | aligned / median | -3.12 | need 1.27 — **fail** | need 1.69 — **fail** | need 1.83 — **fail** |
| `ETHUSDT` | aligned / tertile | -2.28 | need 1.27 — **fail** | need 1.69 — **fail** | need 1.83 — **fail** |

### Verdict

**The primary gate (`inverted|zero`) gains -0.030R and +0.020R gross on the two symbols**, against the pre-registered +0.10R hurdle. **Hurdle 1 fails.**

Across all cells, **0 of 6 `inverted`** and **0 of 6 `aligned`** clear the gross-R hurdle. **H2 is falsified**: it predicted `inverted` would gain at least the hurdle on at least one symbol, and it does not.

The pre-registered *direction* fares better than the pre-registered *effect*. `inverted` averages -0.007R against `aligned`'s -0.038R and wins 5 of 6 paired cells — so D202's anti-signal does show up in the sign, faintly, and nowhere near the size needed to matter. That is the honest reading: the prior pointed the right way and at something far too small to trade.

**Against the shuffle control, 0 of 12 cells beat the 95th percentile of a gate applied to permuted readings.** So most of what the gate does is selectivity, not the map's placement — which is D197's finding (dead even against randomly placed mass) reappearing one level up.

**In 8 of 12 cells the trades the gate REJECTED did better than the ones it kept.** That is D198's finding repeating: a filter can improve nothing while looking like it filters, and the only way to see it is to price the discarded book beside the kept one.

**After costs the primary gate returns -1.642R and -1.409R a trade.** Hurdle 2 fails — a gate changes which trades are taken, not what the wrapper risks, and the toll is a function of the stop.

**And the three bars, which is what this study was asked to show.** Cells clearing each: **fresh** 0 of 12, **structure only** 0 of 12, **combined** 0 of 12. Nothing clears any bar, so the distinction between them never arises — the result is not one that history disqualified, it is one that was never there.

### Multiplicity

| | cells | looks |
|---|---|---:|
| gate cells | 2 directions x 3 thresholds x 2 symbols | 12 |
| gate-shuffle and rotation controls | controls, not tests | 0 |
| **D214 total** | | **12** |

Inherited for the combined bar: the structure programme's 124 and the terrain programme's 259.

## D215 - is it just mean reversion?

**Produced:** 2026-08-24 · **Reproduce:** `uv run python scripts/run_generic_reversal.py` (offline, deterministic)

Pre-registered in `docs/decisions/D215-is-it-just-mean-reversion.md` before this runner existed. The claim: the retracement-depth staircase - the only monotone relationship either programme found - is generic short-horizon reversion after a large move, and the structure contributes nothing.

**Both arms call the same function.** `structure_nulls.continue_from`, same 0.5 ATR band fixed at the bar, same horizon. Not two implementations of one rule - one function, because a second definition is a thing to drift from.

### The census that sets the lookback

| symbol | setups | M = median impulse leg | generic samples | structure touches |
|---|---:|---:|---:|---:|
| `BTCUSDT` | 3,875 | **8 bars** | 36,545 | 21,960 |
| `ETHUSDT` | 3,753 | **8 bars** | 36,512 | 21,389 |

`M` is read off the structure population, not chosen. The generic arm steps by `M` so no two samples share a lookback window - pre-registered, because overlapping windows make a **negative** look sharper than it is.

### A - the staircase with the structure deleted

**`BTCUSDT`** - every 8th bar, bucketed by move size, no change of character and no levels anywhere:

| bucket | move size (ATR) | n | P(reversal) generic | P(continuation) structure |
|---:|---|---:|---:|---:|
| 1 | 0.09 | 4,569 | 37.8% | 26.9% (175) |
| 2 | 0.28 | 4,568 | 37.1% | 28.4% (846) |
| 3 | 0.48 | 4,568 | 40.4% | 33.4% (1,485) |
| 4 | 0.72 | 4,568 | 41.5% | 36.1% (2,825) |
| 5 | 1.01 | 4,568 | 43.9% | 38.1% (3,532) |
| 6 | 1.42 | 4,568 | 48.5% | 44.7% (4,227) |
| 7 | 2.10 | 4,568 | 50.5% | 49.8% (4,841) |
| 8 | 3.96 | 4,568 | 50.9% | 51.6% (4,029) |

**`ETHUSDT`** - every 8th bar, bucketed by move size, no change of character and no levels anywhere:

| bucket | move size (ATR) | n | P(reversal) generic | P(continuation) structure |
|---:|---|---:|---:|---:|
| 1 | 0.10 | 4,564 | 37.6% | 31.3% (163) |
| 2 | 0.30 | 4,564 | 38.7% | 36.7% (711) |
| 3 | 0.51 | 4,564 | 40.1% | 31.3% (1,532) |
| 4 | 0.76 | 4,564 | 42.6% | 36.4% (2,435) |
| 5 | 1.07 | 4,564 | 44.8% | 40.5% (3,561) |
| 6 | 1.49 | 4,564 | 47.7% | 44.2% (4,094) |
| 7 | 2.18 | 4,564 | 50.0% | 48.4% (4,863) |
| 8 | 4.00 | 4,564 | 52.6% | 53.4% (4,030) |

For reference, the Fibonacci ladder this is being compared against ran `BTCUSDT` 46.1% to 60.5% and `ETHUSDT` 46.3% to 58.2% across its eight rungs.

### The verdict: matched on move size

Each structure touch scored against the generic reversal rate of its own move-size bucket. D208's precedent and its warning - there the fair value gap sat at the 100th percentile of 500 draws raw and at +0.006 depth-matched.

| symbol | touches covered | structure | matched generic | delta | within ±0.02 |
|---|---:|---:|---:|---:|:--:|
| `BTCUSDT` | 21,960 | 43.4% | 46.7% | **-0.0329** | **NO** |
| `ETHUSDT` | 21,389 | 44.1% | 47.1% | **-0.0302** | **NO** |

### B - does the slope decay with horizon?

| symbol | h=5 slope | h=20 slope | h=60 slope | decays |
|---|---:|---:|---:|:--:|
| `BTCUSDT` | +0.1029 | +0.0345 | +0.0281 | yes |
| `ETHUSDT` | +0.1029 | +0.0437 | +0.0399 | yes |

### C - the target sweep, and its counterintuitive prediction

| symbol | target | P(reach target) | mean gross R | mean net R @40bp | untradeable |
|---|---:|---:|---:|---:|---:|
| `BTCUSDT` | 1R | 42.4% | -0.007 | -2.034 | 46% |
| `BTCUSDT` | 2R | 21.3% | +0.009 | -2.017 | 46% |
| `BTCUSDT` | 5R | 4.5% | +0.010 | -2.016 | 46% |
| `ETHUSDT` | 1R | 42.7% | -0.004 | -1.510 | 33% |
| `ETHUSDT` | 2R | 21.1% | +0.020 | -1.486 | 32% |
| `ETHUSDT` | 5R | 5.1% | +0.063 | -1.443 | 32% |

### The arithmetic that makes all of it moot at this bar size

| symbol | 0.5 ATR band as share of price | 80 bp round trip | move predicted / cost |
|---|---:|---:|---:|
| `BTCUSDT` | 0.191% | 0.800% | **0.24x** |
| `ETHUSDT` | 0.259% | 0.800% | **0.32x** |

### Verdict

**The staircase survives with the structure deleted.** The generic ladder's slope is +0.1029 on `BTCUSDT` and +0.1029 on `ETHUSDT` — plain bars, bucketed by how far price just moved, with no change of character, no impulse leg, no Fibonacci level and no fair value gap anywhere in the construction. H1 confirmed.

**And matched on move size, the structure adds something.** Structure touches score 43.4% against a matched-generic 46.7% on `BTCUSDT` and 44.1% against a matched-generic 47.1% on `ETHUSDT` — deltas of -0.0329 and -0.0302, against H2's ±0.02 bar. **H2 FALSIFIED — the components carry something the raw move does not, which is the first positive finding in 395 looks and needs its own study.**

So the five components, the confluence, the golden ratio and the fair value gap reduce to **how far price just moved**. That is not a level, it is not structure, and it is not the course's mechanism — it is the oldest effect in intraday data wearing a chart pattern.

**`BTCUSDT` across horizons:** slope +0.1029 at 5 bars, +0.0345 at 20 bars, +0.0281 at 60 bars.
**`ETHUSDT` across horizons:** slope +0.1029 at 5 bars, +0.0437 at 20 bars, +0.0399 at 60 bars.

**`BTCUSDT` target sweep:** dropping from 5R to 1R lifts P(reach target) 4.5% -> 42.4% and mean gross R +0.010 -> -0.007, while mean net R goes -2.016 -> -2.034 — **worse, as H4 predicted**.
**`ETHUSDT` target sweep:** dropping from 5R to 1R lifts P(reach target) 5.1% -> 42.7% and mean gross R +0.063 -> -0.004, while mean net R goes -1.443 -> -1.510 — **worse, as H4 predicted**.

**And the arithmetic that ends it at this bar size.** The move being predicted is half an ATR, which on 15m bars is 0.191% and 0.259% of price, against an 80 bp round trip. The effect is 0.24x and 0.32x the cost of capturing it. **H5 confirmed** — a real effect, and not one you can trade at fifteen minutes. Which is the whole argument for the frequency frontier: the binding question was never which levels to draw, it is what bar size makes this move large relative to the spread.

### Multiplicity

| test | cells | looks |
|---|---|---:|
| A generic ladder + matched comparison | 2 metrics x 2 symbols | 4 |
| B slope by horizon | 3 horizons x 2 symbols | 6 |
| C target sweep | 3 targets x 2 symbols | 6 |
| **D215 total** | | **16** |

**Test A starts a fresh ledger**: it reuses no sensor, component or level, and multiplicity inflates false positives - a test whose predicted outcome is *this effect is generic and therefore not yours* is not weakened by prior looks. B and C reuse the structure machinery and inherit the 395.

## D216 - the tail, the frequency, and the fill

**Produced:** 2026-08-24 · **Reproduce:** `uv run python scripts/run_reversion_tail.py` (offline, deterministic)

Pre-registered in `docs/decisions/D216-the-tail-the-frequency-and-the-fill.md`, which also records two corrections to arithmetic I had stated earlier: daily ATR is ten times the 15m ATR so the same fixed cost is ten times cheaper in ATR terms, and a bracketed trade's cost is asymmetric because the take-profit can rest and the stop cannot - so break-even is a fixed point rather than a constant.

### Break-even, per frequency and fee tier

`p* = (c_in + c_stop + 0.5*ATR) / (ATR + c_stop - c_tp)`, which collapses to `0.5 + RT/ATR` when the legs are symmetric.

| cell | ATR | maker in/out | maker in, taker stop | taker throughout |
|---|---:|---:|---:|---:|
| `15m|BTCUSDT` | 38.2 bp | 55.23% | 63.77% | impossible |
| `15m|ETHUSDT` | 51.4 bp | 53.89% | 60.76% | impossible |
| `1d|BTC-USD` | 381.6 bp | 50.52% | 51.66% | 70.96% |
| `1d|ETH-USD` | 527.6 bp | 50.38% | 51.21% | 65.16% |

**`maker in, taker stop` carries the verdict** - you can rest an entry and a take-profit, you cannot rest a stop. `maker in/out` is an optimistic bound kept so the gap between the two is visible.

### Every cell, both fill arms

| cell | cutoff | move >= | taker n | taker p | maker n | fill rate | maker p | adverse selection |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `15m|BTCUSDT` | 87.5th | 2.72 ATR | 9,049 | 52.33% | 8,846 | 97.8% | 50.58% | **+1.75%** |
| `15m|BTCUSDT` | 95.0th | 4.39 ATR | 3,784 | 52.70% | 3,731 | 98.6% | 51.73% | **+0.97%** |
| `15m|BTCUSDT` | 99.0th | 8.19 ATR | 838 | 56.56% | 830 | 99.0% | 52.77% | **+3.79%** |
| `15m|BTCUSDT` | 99.5th | 10.19 ATR | 413 | 56.66% | 410 | 99.3% | 59.27% | **-2.61%** |
| `15m|ETHUSDT` | 87.5th | 2.79 ATR | 9,168 | 52.89% | 8,985 | 98.0% | 51.09% | **+1.81%** |
| `15m|ETHUSDT` | 95.0th | 4.40 ATR | 3,879 | 53.16% | 3,815 | 98.4% | 54.00% | **-0.84%** |
| `15m|ETHUSDT` | 99.0th | 8.04 ATR | 828 | 58.09% | 815 | 98.4% | 56.07% | **+2.02%** |
| `15m|ETHUSDT` | 99.5th | 10.02 ATR | 420 | 61.43% | 413 | 98.3% | 58.60% | **+2.83%** |
| `1d|BTC-USD` | 87.5th | 3.52 ATR | 120 | 40.00% | 118 | 98.3% | 45.76% | **-5.76%** |
| `1d|ETH-USD` | 87.5th | 3.39 ATR | 100 | 50.00% | 94 | 94.0% | 39.36% | **+10.64%** |

**Adverse selection is the rightmost column and it is the study's second finding.** A reversion entry rests a bid below a falling market and fills only when the fall continues - the losing case by construction. `FillAssumption.TRADE_THROUGH` exists for exactly this and its docstring says so.

### The verdict, each fee tier scored only on the arm it is coherent with

**A tier that assumes the entry rested must be scored on the population that actually filled by resting.** This study's first draft scored both arms against every tier and produced a pass by pairing a taker fill with maker costs — inflating `p` and deflating the cost at the same time. The pairing below is enforced in `FEES`.

| cell | cutoff | fee tier | arm | n | p | p* | margin | powered | clears | stable |
|---|---:|---|---|---:|---:|---:|---:|:--:|:--:|:--:|
| `15m|BTCUSDT` | 87.5th | maker in/out | maker | 8,846 | 50.58% | 55.23% | -4.66% | yes | no | no |
| `15m|BTCUSDT` | 87.5th | maker in, taker stop **(verdict)** | maker | 8,846 | 50.58% | 63.77% | -13.19% | yes | no | no |
| `15m|BTCUSDT` | 87.5th | taker throughout | taker | 9,049 | 52.33% | impossible | -207.03% | yes | no | no |
| `15m|BTCUSDT` | 95.0th | maker in/out | maker | 3,731 | 51.73% | 55.23% | -3.51% | yes | no | no |
| `15m|BTCUSDT` | 95.0th | maker in, taker stop **(verdict)** | maker | 3,731 | 51.73% | 63.77% | -12.04% | yes | no | no |
| `15m|BTCUSDT` | 95.0th | taker throughout | taker | 3,784 | 52.70% | impossible | -206.66% | yes | no | no |
| `15m|BTCUSDT` | 99.0th | maker in/out | maker | 830 | 52.77% | 55.23% | -2.46% | yes | no | no |
| `15m|BTCUSDT` | 99.0th | maker in, taker stop **(verdict)** | maker | 830 | 52.77% | 63.77% | -11.00% | yes | no | no |
| `15m|BTCUSDT` | 99.0th | taker throughout | taker | 838 | 56.56% | impossible | -202.80% | yes | no | no |
| `15m|BTCUSDT` | 99.5th | maker in/out | maker | 410 | 59.27% | 55.23% | +4.03% | yes | **YES** | yes |
| `15m|BTCUSDT` | 99.5th | maker in, taker stop **(verdict)** | maker | 410 | 59.27% | 63.77% | -4.50% | yes | no | no |
| `15m|BTCUSDT` | 99.5th | taker throughout | taker | 413 | 56.66% | impossible | -202.70% | yes | no | no |
| `15m|ETHUSDT` | 87.5th | maker in/out | maker | 8,985 | 51.09% | 53.89% | -2.81% | yes | no | no |
| `15m|ETHUSDT` | 87.5th | maker in, taker stop **(verdict)** | maker | 8,985 | 51.09% | 60.76% | -9.67% | yes | no | no |
| `15m|ETHUSDT` | 87.5th | taker throughout | taker | 9,168 | 52.89% | impossible | -152.72% | yes | no | no |
| `15m|ETHUSDT` | 95.0th | maker in/out | maker | 3,815 | 54.00% | 53.89% | +0.11% | yes | **YES** | no |
| `15m|ETHUSDT` | 95.0th | maker in, taker stop **(verdict)** | maker | 3,815 | 54.00% | 60.76% | -6.76% | yes | no | no |
| `15m|ETHUSDT` | 95.0th | taker throughout | taker | 3,879 | 53.16% | impossible | -152.46% | yes | no | no |
| `15m|ETHUSDT` | 99.0th | maker in/out | maker | 815 | 56.07% | 53.89% | +2.18% | yes | **YES** | no |
| `15m|ETHUSDT` | 99.0th | maker in, taker stop **(verdict)** | maker | 815 | 56.07% | 60.76% | -4.69% | yes | no | no |
| `15m|ETHUSDT` | 99.0th | taker throughout | taker | 828 | 58.09% | impossible | -147.52% | yes | no | no |
| `15m|ETHUSDT` | 99.5th | maker in/out | maker | 413 | 58.60% | 53.89% | +4.71% | yes | **YES** | yes |
| `15m|ETHUSDT` | 99.5th | maker in, taker stop **(verdict)** | maker | 413 | 58.60% | 60.76% | -2.16% | yes | no | no |
| `15m|ETHUSDT` | 99.5th | taker throughout | taker | 420 | 61.43% | impossible | -144.19% | yes | no | no |
| `1d|BTC-USD` | 87.5th | maker in/out | maker | 118 | 45.76% | 50.52% | -4.76% | yes | no | no |
| `1d|BTC-USD` | 87.5th | maker in, taker stop **(verdict)** | maker | 118 | 45.76% | 51.66% | -5.90% | yes | no | no |
| `1d|BTC-USD` | 87.5th | taker throughout | taker | 120 | 40.00% | 70.96% | -30.96% | yes | no | no |
| `1d|ETH-USD` | 87.5th | maker in/out | maker | 94 | 39.36% | 50.38% | -11.02% | **no** | no | no |
| `1d|ETH-USD` | 87.5th | maker in, taker stop **(verdict)** | maker | 94 | 39.36% | 51.21% | -11.85% | **no** | no | no |
| `1d|ETH-USD` | 87.5th | taker throughout | taker | 100 | 50.00% | 65.16% | -15.16% | yes | no | no |

### Verdict

**`15m|BTCUSDT` into the tail:** 52.33% at the 87.5th, 52.70% at the 95.0th, 56.56% at the 99.0th, 56.66% at the 99.5th — still rising.
**`15m|ETHUSDT` into the tail:** 52.89% at the 87.5th, 53.16% at the 95.0th, 58.09% at the 99.0th, 61.43% at the 99.5th — still rising.

**Adverse selection is real in direction but small.** Across all 10 cells the maker arm scores +1.46% against the taker arm on average (predicted: at least +3.00%), spanning -5.76% to +10.64%, with 7 of 10 cells in the predicted direction. **H2 falsified on magnitude** — resting a bid below a falling market does fill you when the fall continues, but at this horizon it costs about half what I predicted.


**At daily the effect is not weaker, it is absent or inverted.** `1d|BTC-USD` 40.00%, `1d|ETH-USD` 50.00% against a coin-flip 50% — 1 of 2 below it. H3 predicted a weaker-but-present reversion at daily; what is here is the opposite sign on one symbol and nothing on the other. **H3 falsified**, and in the direction that matches the standard stylised fact: reversal intraday, momentum at daily. These are the two thinnest samples in the study (n = 120, 100) and the claim is reported at that weight.
**Coherent arm/fee pairings clearing all four hurdles: 2 of 30.** They are: `15m|BTCUSDT` 99.5th under `maker in/out`, `15m|ETHUSDT` 99.5th under `maker in/out`.

**On the tier that carries the verdict — `maker in, taker stop` — 0 of 10 cells clear.** Every survivor above sits on `maker in/out`, the tier this pre-registration itself labelled *an optimistic bound*, and it is optimistic for a concrete reason: it prices the stop as a maker fill. **You cannot rest a stop.** A resting sell placed below a long's market price is immediately marketable and crosses as a taker. So the two clearing cells clear a fee model that cannot be traded.

**H4 is falsified as literally written and confirmed as it was meant.** I score it falsified, because the hurdle text said *no cell* and two cells cleared, and because scoring my own prediction on the reading most favourable to it is the failure mode this whole programme exists to avoid. What the falsification buys is one real fact: at the 99.5th percentile the effect is finally large enough to beat a 2 bp round trip on both symbols, stably across both halves. It is still not large enough to beat the 11 bp round trip you would actually pay.

**Underpowered cells (n < 100): 2 of 30**, reported with no verdict rather than with a rate computed on too few events.

### Multiplicity

| | cells | looks |
|---|---|---:|
| 15m tail | cutoffs x symbols x 2 fills | 16 |
| daily | top bucket x symbols x 2 fills | 4 |
| **D216 total** | | **20** |

On the reversion ledger D215's Test A opened at 4 - running total **24**. The structure programme's 395 are not inherited: no sensor, component or level is reused.

---

### Parking lot