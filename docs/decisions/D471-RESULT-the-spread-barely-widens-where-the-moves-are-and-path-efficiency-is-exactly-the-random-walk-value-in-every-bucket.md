# D471 — RESULT: the spread barely widens where the moves are, and path efficiency is exactly the random-walk value in every bucket

**2026-09-12.** Runner [`scripts/d471_spread_and_path_efficiency.py`](../../scripts/d471_spread_and_path_efficiency.py) ·
artifact [`data/d471_spread_and_path_efficiency.json`](../../data/d471_spread_and_path_efficiency.json)

**A MEASUREMENT, NOT A STUDY.** No signal, no entry rule, no edge, no Sharpe of any
construction. Nothing opened, closed or admitted ([R15](../RULES.md#r15)).

Two questions, both raised by [D469](D469-RESULT-the-scalping-re-cost-the-spread-is-not-what-kills-it-a-fixed-commission-against-a-tenth-sized-tick-is.md):
the spread it warned it had not conditioned, and **path efficiency**, asked by the principal.

Measured on **non-overlapping** 5- and 15-minute windows (D469 used overlapping pairs, whose
statistics share observations so an SE from them is a fiction). 23,318 windows at 15 minutes,
6,602 of them RTH.

---

## 1. The spread where the moves are — the warning was right in direction and negligible in size

D469 wrote of its own best cell: *"the top volatility quintile is exactly where fills are
worst … the conditioned rows are the most optimistic cells in the table, not the safest."*
Paying the spread **actually quoted at both ends of each window**, in the bucket being traded:

| RTH, 15 min, by trailing-move quintile | spread both ends | breakeven acc. | at D469's flat spread |
|---|---:|---:|---:|
| 1 (quietest) | 1.030 tk | 59.2% | 59.2% |
| 3 | 1.024 tk | 57.7% | 57.7% |
| **5 (busiest)** | **1.052 tk** | **54.8%** | **54.7%** |

**The correction is 0.1 pp.** The spread widens by 0.022 ticks — about 2% — from the quietest
fifth of the session to the busiest.

**The reason is structural, not luck.** ES sits at its **one-tick minimum 97.6%** of the time
(D465). The tick is a *floor* the spread cannot go below, and ES is liquid enough that even in
the busiest fifth it stays pinned there. A market whose spread is already at the exchange
minimum has nowhere to widen to.

> **WHAT THIS DOES NOT MEASURE, and it is the part that remains open.** This is the **quoted**
> spread. It says the market stays one tick wide when it is moving; it says **nothing** about
> whether an order gets filled at that quote. **Queue position, partial fills, latency and
> being run over on a fast market are not measured here and cannot be from `tbbo`** — which
> records trades and the quote at the moment of each trade, not the book or one's place in it.
> The fill risk in the busiest quintile is real; what D471 removes is the *width* worry, not
> the *fill* worry.

## 2. D469 and D471 disagreed, and the reason matters more than the numbers

D469 put the 15-minute top-quintile bar at **55.0%**; D471's all-hours table says **57.0%**.
Both are right and they measure different populations:

- **D469 required both the entry second and the exit second to carry a trade.** Overnight,
  many seconds have no trade at all, so those windows were silently dropped — which
  **activity-weights the sample toward RTH**.
- **D471 tiles every calendar block equally**, dead Asian-hours blocks included — blocks nobody
  would trade.

**Restricted to RTH, D471 gives 54.8% against D469's 55.0%.** They agree. The all-hours 57.0%
is the honest number for a rule that trades around the clock; the RTH 54.8% is the honest
number for one that does not. **A conditional mean is only defined against the population it
conditions on, and "the" mean here was two different things.**

## 3. Path efficiency: it fails, three separate ways

For a window, `eff = |net displacement| / total path length`, on the one-second grid — 1 is a
straight line, 0 a round trip. The principal's reasoning was sound: **it is the axis raw
volatility cannot see**, separating a big move you could hold from a big move that shakes you
out. It does not survive measurement.

**(a) Stage 0 — it barely forecasts itself.** On independent windows at 15 minutes (SE 0.0065):

| | ρ | in SE |
|---|---:|---:|
| trailing \|move\| → forward \|move\| | **+0.312** | 47.7 |
| trailing eff → forward eff | **+0.081** | 12.4 |
| trailing eff → forward \|move\| | **−0.073** | 11.2 |

Statistically nonzero, and it explains **0.7% of the variance** against volatility's 9.7%.
Volatility is ~4× more persistent.

**(b) Its sign is the wrong way round.** Trailing efficiency predicts *smaller* forward moves,
so conditioning on high efficiency **raises** the bar: 60.3% in the lowest quintile against
**63.3%** in the highest. A clean trend just finished is a *worse* moment to enter, not better.

**(c) It subtracts from volatility rather than adding.** Splitting the top-volatility windows:

| top-vol 15-min windows | forward \|M\| | breakeven acc. |
|---|---:|---:|
| trailing eff **below** median | **29.3 tk** | **55.9%** |
| trailing eff **above** median | 20.5 tk | 58.5% |

The better cell is high volatility with **low** efficiency — big range achieved messily. Which
is what volatility persistence *is*: churn begets churn.

## 4. The finding that explains why — ES is the random walk, to three digits

A driftless random walk of *n* steps has efficiency **exactly 1/√n** (E|net| = σ√(2n/π),
E[path] = nσ√(2/π); the ratio is √n/n). At 900 one-second steps that is **0.0333**. The
self-test confirms it by simulation: 0.0332.

**Measured ES efficiency, divided by that benchmark, in every bucket of every table:**

    all hours, by volatility     1.00 - 1.02
    all hours, by efficiency     1.01 - 1.04
    RTH only,  by volatility     0.87 - 1.03

**Every cell is the random-walk value.** In RTH it runs slightly *below* 1 — marginally
choppier than a coin, which is the signature of bid-ask bounce at one-second sampling.

So path efficiency is not a weak conditioner that better engineering could sharpen. **ES has
no trendiness at this scale to condition on**: its path-to-displacement ratio is what pure
noise produces, in quiet markets and violent ones alike.

## 5. And a constant that no conditioner moved

The adverse excursion before the winning move, as a fraction of that move — measured **on the
side that won**, because `min(long, short)` takes the gentler side whichever way price went
and that is not a trade anyone can place:

**`adverse / |move| = 0.45 to 0.50` in every cell of every table**, at both horizons, across
volatility quintiles, efficiency quintiles and the 2D cross.

**You cannot condition your way into a cleaner path.** Whatever you select on, the trade goes
about half the size of its eventual move against you first. Practically: **a stop must be
roughly half the target or it will be hit on the way to being right**, and no conditioner
tested here improves that trade-off. This is the honest answer to what the principal was
reaching for with path efficiency — the concept is the right one, and the measurement says the
quantity is invariant.

---

## 6. Checks

`--self-test` carries 24 checks. Path efficiency is verified on paths whose answer is known by
hand (straight line 1, round trip 0, out-and-two-thirds-back 0.2, sign-blind, bounded in
[0,1]) and **proven resolution-dependent**, which is why only rankings and the random-walk
*ratio* are claimed and never an efficiency level. The block machinery is checked against a
hand-built case for start/end indices, inclusive tiling, `reduceat` max/min, and path length by
cumulative sum versus a direct per-block sum. Adverse excursion is checked on a monotone rise
(zero for a long) and a dip-then-pay path (3 long, 4 short). The DBN sentinel filter is checked
to admit only the clean quote. The random-walk benchmark is checked by simulation at n = 100
and n = 900.

## 7. Three errors caught in this runner's own construction

**My blocks averaged 534 seconds of trading against a 900-second width.** The span filter
admitted anything over 0.5h, so it measured ~9-minute moves and labelled them 15-minute ones.
**The tell was arithmetic sitting there to be done:** 23,318 blocks × 900 s = 21.0M seconds
against a 12.4M-second grid. Tightened to 0.95h. (It barely moved the numbers, which is how I
found the *real* cause of the D469 gap in §2 — the fix that does not fix the discrepancy is
evidence about where the discrepancy is not.)

**I first measured adverse excursion as `min(adverse_long, adverse_short)`** — the gentler side
regardless of which way price went, which no one can trade. Corrected to the side matching the
realised move's sign; it raised the figure from ~0.40 to ~0.48.

**The self-test caught my own arithmetic.** I asserted the path `0 → 3 → 1` had efficiency 1/3;
it is 1/5. The function was right and the expectation was wrong.

## 8. What this does not do

- **It does not close or open anything.** R15. Path efficiency is measured, not ruled out as a
  research axis — this tests **one** definition on **one** grid at **two** horizons
  ([[construction-vs-axis]] is the standing error here).
- **It scores no construction**, so it enters nothing in `COMPONENTS_PROP.md` and touches
  neither book.
- **It does not measure fills**, which is now the largest unquantified cost risk at the
  15-minute horizon (§1). `mbp-10` would be the data for it and was not bought
  (`docs/data-available.md`).
- **Nothing is elevated** into `FINDINGS.md` or `RULES.md`.

---

### AMENDMENT 1, 2026-09-12 — **the grid sweep §8 asked for. My §4 benchmark was wrong by ~20%, the conclusion survives on a better instrument, and coarsening does not rescue efficiency as a conditioner**

`--grid-sweep` · artifact [`data/d471_path_efficiency_grid_sweep.json`](../../data/d471_path_efficiency_grid_sweep.json).
Grids 1 s → 300 s, windows 15 min and 60 min, RTH only, non-overlapping.

**§4's BENCHMARK WAS WRONG, AND THE 1.00 WAS LUCK.** §4 divided measured efficiency by
`1/√n`. That is the random-walk value **only for Gaussian steps**. For any iid step
distribution the truth is

    efficiency = C / sqrt(m),   C = sqrt(2/pi) * sigma_r / E|r|

and `C` is 1 *only* when `σ/E|r|` takes its Gaussian value `√(π/2)`. One-second ES steps are
nothing like Gaussian — mostly zero, occasionally one tick. **Measured `C` is 1.17–1.21 at
every grid**, so §4's benchmark ran ~20% low and its comforting "ratio = 1.00" was two errors
cancelling. **Against the correct benchmark the ratio is 0.78–0.87.**

**The conclusion survives, on an instrument that does not depend on the step shape.** The
variance ratio `Var(r_k)/(k·Var(r_1))` — 1.00 random walk, >1 trending, <1 mean-reverting:

| grid | VR, 15-min window | VR, 60-min window |
|---|---:|---:|
| 1 s | **0.82** | 0.90 |
| 5 s | 0.88 | 0.94 |
| 15 s | 0.97 | 0.95 |
| 60 s | 1.02 | 0.92 |
| 300 s | — | 0.98 |

**The one-second choppiness §4 reported is bid-ask bounce, and now it is quantified: about
18% of one-second variance is transient noise.** Past 15 seconds ES is a random walk to within
a few percent, and **no grid at either window reads above 1.02.** There is no trend structure
at any sampling rate tested — which is what §4 said, but §4 said it from a benchmark that
happened to be wrong.

**The two instruments are the same quantity, and that is now asserted rather than eyeballed:**

    efficiency / (C/sqrt(m)) = sqrt(VR) * (E|net| / sigma_net) / sqrt(2/pi)

The second factor is non-Gaussianity of the *window* return — fat tails put `E|X|/σ` below
`√(2/π)`, which is the rest of the gap between 0.82 and 1.00. A runtime gate raises if the two
sides differ by more than 1e-9. **It fired on the first run** (0.8196 against 0.7871) because
VR was computed on the whole RTH series while efficiency came from the subset of windows
passing the span/session filter — **different populations**. Both now read the steps inside the
accepted windows and the identity closes to float precision.

**AND THE PRACTICAL ANSWER: COARSENING DOES NOT RESCUE IT.** Efficiency's persistence,
trailing window to forward window, at every grid and both windows:

    -0.024  -0.007  -0.017  +0.004        (15-min window, grids 1/5/15/60 s)
    -0.094  -0.020  +0.006  +0.057  +0.006 (60-min window, grids 1/5/15/60/300 s)

**It flips sign and never exceeds 2.5 SE.** Volatility's +0.312 stands unchallenged. The best
cell for predicting the forward move is +0.088 (60 s grid, 60-min window, 2.9 SE) — 0.8% of
variance, worth perhaps 0.8 pp on the breakeven bar against volatility's 2.7 pp, before
accounting for the two conditioners overlapping.

**What is now closed and what is not.** Path efficiency as a **conditioner on ES index
futures, on grids 1–300 s at 15- and 60-minute windows**, is measured and it is not useful. That
is five grids × two windows on one instrument over one year — **not the axis**
([[construction-vs-axis]]). Untested: other instruments, grids coarser than 5 minutes, windows
longer than an hour, and efficiency defined on something other than a last-trade grid (a
volume or event clock would be the interesting variant, and `mbo` is on disk for it).

---

### AMENDMENT 2, 2026-09-12 — **the volume clock. It does not rescue path efficiency, it halves the volatility conditioner, and it lowers the breakeven bar by 1 pp for free**

`--volume-clock` · artifact [`data/d471_volume_clock.json`](../../data/d471_volume_clock.json).
93,824,356 RTH trades, 283,323,581 contracts, 258 sessions. Bars calibrated to the
**15-minute bar COUNT** (26 a session, 6,708 bars) so the A/B is fair: **V = 42,237
contracts**. Both clocks run through the identical `clock_cell`, which cannot tell which
clock it is given.

**The clock is doing real work.** A volume bar averages 15.2 min but spans **[5.8, 27.9] min**
at p10/p90 — it compresses when the market is busy and stretches when it is not.

| steps | clock | bar unit | windows | mins mean [p10,p90] | E\|M\| tk | p_be | C | corr'd | VR | kurt | **ρ\|M\|** | ρ eff |
|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 900 | volume | 47 ct | 6,082 | 15.5 [6.0, 27.9] | 27.4 | 56.2% | 1.14 | 0.93 | 0.93 | **4.3** | **+0.142** | −0.006 |
| 900 | time | 1 s | 4,023 | 15.5 [15.0, 16.4] | 28.9 | 55.9% | 1.21 | 0.83 | 0.82 | **6.5** | **+0.196** | −0.024 |
| 180 | volume | 235 ct | 6,174 | 15.2 [5.8, 27.4] | 27.2 | **56.3%** | 1.07 | 0.94 | 0.96 | **4.0** | **+0.148** | +0.003 |
| 180 | time | 5 s | 6,032 | 15.0 | 23.2 | 57.3% | 1.21 | 0.81 | 0.88 | **10.2** | **+0.267** | −0.007 |
| 60 | volume | 704 ct | 6,197 | 15.2 | 27.1 | **56.3%** | 1.06 | 0.94 | 0.96 | 4.1 | +0.137 | +0.006 |
| 60 | time | 15 s | 6,083 | 15.0 | 23.5 | 57.3% | 1.19 | 0.84 | 0.97 | 9.9 | +0.285 | −0.017 |
| 15 | volume | 2,816 ct | 6,197 | 15.2 | 27.0 | 56.3% | 1.04 | 0.94 | 0.98 | 5.1 | +0.140 | +0.005 |
| 15 | time | 60 s | 6,086 | 15.0 | 24.2 | 57.0% | 1.19 | 0.86 | 1.02 | 8.5 | +0.301 | +0.004 |

**1. CLARK (1973) IS CONFIRMED, AND IT VALIDATES THE CONSTRUCTION.** Kurtosis of the window
return is **4.0–5.1 on the volume clock against 6.5–10.2 on the wall clock** — volume-time
returns are far closer to Gaussian, which is the textbook prediction and the reason to believe
the clock is built right. The step-shape factor `C` follows it down, **1.04–1.14 against a flat
1.19–1.21**. And the volume clock's results are **grid-invariant** (E|M| 27.0–27.4, p_be
56.2–56.3%, corrected ratio 0.93–0.94 at every sub-grid) where the wall clock's wander. A
sampling scheme whose answer does not depend on its own sub-grid is the better instrument.

**2. PATH EFFICIENCY IS DEAD ON THIS CLOCK TOO, and more flatly than before.** ρ = **−0.006 to
+0.006** against the wall clock's −0.024 to +0.004, at SE ≈ 0.013. This was the most promising
untested variant named in AMENDMENT 1, and the answer is no. Path efficiency is now measured
as a conditioner on **two different clocks**, five time grids and four volume grids, at two
window lengths — it does not forecast itself on any of them.

**3. HALF THE VOLATILITY CONDITIONER WAS AN ACTIVITY FORECAST.** This is the finding.
Persistence of the absolute move falls from **+0.267…+0.301 on the wall clock to
+0.137…+0.148 on the volume clock** — roughly halved. The prediction stated in the runner's
docstring before it ran was that a volume clock would absorb volatility clustering, and it
does, by about half.

**What that means, and it is not that the conditioner is fake.** Predictability of |move| in
wall-clock time is *partly* predictability of **how much will trade**, not of how far price
moves per contract traded. Since costs are paid per **trade** and holding is measured in
**time**, the wall-clock conditioner is real and usable — D469's 54.8% stands. But its
mechanism is now decomposed: about half activity forecasting, about half genuine
movement-per-unit-activity persistence.

**4. AND A FREE PERCENTAGE POINT, WHICH IS THE PRACTICAL RESULT.** At matched bar count and
matched mean holding time (≈6,200 bars, 15.2 min against 15.0), a **volume bar captures 15%
more move**: E|M| **27.1 ticks against 23.5**, and the breakeven bar falls **57.3% → 56.3%**.

The reason is mechanical: a volume bar spends its holding time where price actually moves and
skips the dead patches, while a 15-minute bar spends 15 minutes either way. **So changing the
EXIT RULE from "hold 15 minutes" to "hold until 42,237 contracts trade" is worth about 1 pp of
breakeven accuracy at the same trade frequency** — and by D469's sensitivity table, 1 pp at
this horizon is worth roughly 1.0 of Sharpe. It needs no forecast of anything; cumulative
volume is observable in real time.

**Still no trending on either clock.** No cell of either clock reads VR above 1.02. The volume
clock does lift the fine-grid VR from 0.82 to 0.93, which says a good part of AMENDMENT 1's
"18% transient variance" was a wall-clock sampling artefact — the one-second grid oversamples
quiet stretches where the only price action is bid-ask bounce. The remainder (0.93 < 1) is
genuine bounce.

**What is NOT done.** The 1 pp is an arithmetic consequence of the sampling, measured on
2025-09→2026-09 RTH; **no rule has been scored on a volume-clock exit**, and the in-sample
window for a component is 2016–2023. A volume-clock exit also changes the trade's *timing*
distribution, which interacts with the `adverse/|move| ≈ 0.48` constant of §5 in a way not
measured here. Nothing opened, closed or admitted (R15).
