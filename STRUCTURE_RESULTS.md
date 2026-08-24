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
| **Total** | **0** |

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
