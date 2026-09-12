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
