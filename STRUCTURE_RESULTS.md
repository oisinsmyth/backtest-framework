# STRUCTURE_RESULTS.md — the structure programme's ledger

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
| **Total** | **30** |

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
| `BTCUSDT` | C1 only | 3,875 | 5 | 0.321 | 1.04 | 0.41% | 0.972 | 32.9% |
| `BTCUSDT` | C1+C2+C3+C4 | 120 | 9 | 0.538 | 1.70 | 0.68% | 0.589 | 26.5% |
| `ETHUSDT` | C1 only | 3,753 | 5 | 0.316 | 1.06 | 0.56% | 0.718 | 28.6% |
| `ETHUSDT` | C1+C2+C3+C4 | 106 | 9 | 0.547 | 1.84 | 1.01% | 0.395 | 23.3% |

Frictionless, a 5R target breaks even at **16.7%** — the course's "two out of ten". The column above is the same arithmetic with costs put back.

### What the counts say

**1. The stop condition clears, so the programme continues.** `BTCUSDT` produces 120 stacked entries and `ETHUSDT` produces 106 stacked entries, both above the pre-registered floor of 30. H5 — that the stacked arm would be underpowered — is **falsified**. It was held at moderate confidence and it was wrong.

**2. The round-trip cost is roughly the whole distance to the stop.** On the C1-only arm the median stop sits at 0.41% of price on `BTCUSDT` and 0.56% of price on `ETHUSDT`, against a 40 bps round trip — so friction is 0.97R and 0.72R. This is the whole problem with running this strategy on 15m bars, and it is arithmetic rather than a result: a stop placed at the swing extreme of a 15m impulse leg is simply not far enough away to pay for crossing the spread twice.

**3. The course's central arithmetic is wrong once costs exist.** It claims a 5R target breaks even at ~20% and is "highly profitable" at 30%. Frictionless that is nearly right — the true break-even is 16.7%. At 40 bps on the stacked arm it becomes 26.5% on `BTCUSDT` and 23.3% on `ETHUSDT`, and on the C1-only arm 32.9% and 28.6%. **A 20% hit rate at 5R loses money at every cell measured here.** No backtest was needed to establish that, and none of it depends on whether the components carry information.

**4. The confluence stack's one measurable effect so far is that it enters deeper.** Median retracement moves from 0.321 to 0.538 on `BTCUSDT` and 0.316 to 0.547 on `ETHUSDT`, which widens the stop from 1.04 to 1.70 ATR and 1.06 to 1.84 ATR and roughly halves the friction. That is a real mechanical benefit and it is **not evidence of a signal** — waiting for a deeper pullback would do the same thing without any of the structure. WP4 is where the two get separated.

**5. Two filters barely filter, and one is incompatible with the rest.** C3 (the 61.8% band) admits 2,672 of 3,875 and 2,619 of 3,753 setups on its own — roughly 69% and 70% of the population, which is very little work for a filter, before anyone asks whether 0.618 is special. C5 (RSI 30/70) collapses the stacked arm to 2 and 2 entries: the textbook thresholds essentially never coincide with structural confluence. **C5 is therefore dropped as a stacked filter and kept as a continuous feature in WP4a**, which is where a 2-trade arm has nothing to say and a rank correlation still does.

**And one number that is the discretion gap itself.** `BTCUSDT`: 340 setups have all three conditions somewhere in the pullback window but only 120 have them at the same bar (35%) and `ETHUSDT`: 388 setups have all three conditions somewhere in the pullback window but only 106 have them at the same bar (27%). A trader reading the chart afterwards sees the level, the retracement and the gap all present and calls it confluence. Two thirds of the time they were not simultaneous, and which bar you would actually have entered on is a judgement call. WP6 is the audit of that; this is its first measurement.
### Sensitivity across the pre-registered grid

| symbol | k | touch | setups | stacked | median stop (ATR) | median friction (R) |
|---|---:|---:|---:|---:|---:|---:|
| `BTCUSDT` **(primary)** | 2 | 0.5 | 3,875 | 120 | 1.70 | 0.589 |
| `BTCUSDT` | 2 | 1.0 | 3,875 | 244 | 1.74 | 0.532 |
| `BTCUSDT` | 3 | 0.5 | 2,808 | 67 | 2.19 | 0.411 |
| `BTCUSDT` | 3 | 1.0 | 2,808 | 131 | 2.01 | 0.432 |
| `ETHUSDT` **(primary)** | 2 | 0.5 | 3,753 | 106 | 1.84 | 0.395 |
| `ETHUSDT` | 2 | 1.0 | 3,753 | 239 | 1.80 | 0.438 |
| `ETHUSDT` | 3 | 0.5 | 2,717 | 45 | 2.00 | 0.376 |
| `ETHUSDT` | 3 | 1.0 | 2,717 | 137 | 2.10 | 0.363 |

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

---

### Parking lot