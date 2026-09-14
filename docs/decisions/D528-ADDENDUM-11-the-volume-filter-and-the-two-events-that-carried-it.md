# D528 ADDENDUM 11 — the volume filter, and the two market events that carried it

Date: 2026-09-14. Runner: `working/d528_volume_filter.py`.

**Nothing admitted (R15).** Micro universe, in sample only; reserved slice UNREAD — the principal
declined to spend it, and nothing here justifies revisiting that.

**The principal's design**, given for feedback before building: block trades when an SMA of volume
is much below an EMA of volume, over ~100 bars rather than the detection window, scale-invariant,
no warm-up, previous session's volume filling any shortfall, overnight excluded. He chose, after
feedback, to run BOTH a level and a change test, at one declared untuned cut of 1.0.

---

## 1. The one change made to the design, and why it was load-bearing

**Everything is normalised by a causal time-of-day profile first.** NQ's median 5-minute volume runs
**17,021 at 09:30 against 3,378 at 14:00 — a 14.5× swing.** A 100-bar window against a longer
average would mostly report *what time it is*: a time-of-day filter wearing a volume costume, which
is the same defect already diagnosed in the detector's own σ estimate.

It also decides whether the filter is safe to use at all. On the 717 candidates:

| | corr with price `vol_ratio` |
|---|---:|
| **time-of-day-normalised** volume | **+0.052** — independent, filter is safe |
| **raw** volume | **+0.235** — entangled, would cut the quiet-window cell that works |

**Normalising is what stops the volume filter eating the one cell that clears its control.**

Two other points from the feedback, both confirmed: the 1-minute mid fixture carries **no volume**,
so the series comes from `fut_day5m` at 5-minute resolution (100 minutes = 20 bars); and the
no-warm-up requirement is simpler than feared because **the fixture is day-session only, so there
is no overnight volume in it to exclude.** The trailing window backfills from the previous
session's same-clock bars; the profile uses only sessions strictly before the day it scores.

## 2. The filters do nothing on the pool

| cell | n | gross $ | NET fixed | NET hour | matched p5 / p95 | verdict |
|---|---:|---:|---:|---:|---|---|
| pool | 693 | −0.89 | −5.61 | −5.88 | — | — |
| LEVEL: not thin | 466 | −1.06 | −5.83 | −6.13 | −2.20 / +0.51 | inside |
| CHANGE: not falling | 291 | −0.06 | −4.77 | −5.06 | −3.13 / +1.35 | inside |
| LEVEL + CHANGE | 285 | −0.22 | −4.94 | −5.24 | −2.86 / +1.28 | inside |
| LEVEL inverted | 227 | −0.53 | −5.14 | −5.37 | −3.49 / +1.62 | inside |
| CHANGE inverted | 402 | −1.49 | −6.21 | −6.47 | −2.46 / +0.69 | inside |

Both signs of both filters are inside the control. The two measures correlate at **+0.787**, so
"both" is close to one filter, and `corr(price vol_ratio, LEVEL) = −0.117` confirms the filter is
not cutting the quiet cell.

**A cost-basis defect was found and fixed here.** The hour-spread scaling initially divided by the
root's median spread over **all 24 hours**, while D507's `COST[root]` anchor is measured **at
execution hours** — so the day session looked artificially tight (spread ×0.90) and the cost was
scaled *down*, contradicting ADDENDUM 10's finding that this cell trades wider than a random
minute. With a day-session denominator the pool reads ×1.004 and the adjustment is near-neutral
(−$0.15/trade).

## 3. On the spike cell it appears to work — and it is two market events

| cell | n | P(tgt) | gross $ | NET fixed | NET hour | matched p95 | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| spike | 130 | 8.5% | +3.66 | −1.22 | −1.50 | +3.42 | above p95 |
| spike + LEVEL | 88 | 11.4% | +5.78 | +0.92 | +0.79 | +3.50 | above p95 |
| spike + CHANGE | 58 | 13.8% | +10.68 | +5.89 | +5.74 | +5.78 | above p95 |
| **spike + LEVEL + CHANGE** | **56** | 14.3% | **+10.86** | **+6.03** | **+5.88** | +4.93 | above p95 |

The first net-positive cell in D528. **It does not survive its own concentration report.**

| | |
|---|---:|
| mean net | +$6.03 |
| **median net** | **−$9.00** |
| **t of net vs zero** | **+0.80** |
| winners | 12 of 56 |
| top 1 trade | **27.4%** of gross positive P&L |
| top 3 trades | **58.4%** |
| top 5 trades | 72.7% |
| trimmed 1% both tails | +$2.80 |
| **mean excluding the top 3** | **−$4.73** |

The three trades that carry it:

```
+$276.18  NQ  2026-03-27  13:07 ET  held 40 bars  TIMEOUT
+$211.68  NQ  2025-10-22  14:51 ET  held 40 bars  TIMEOUT
+$100.67  ES  2025-10-22  14:51 ET  held 40 bars  TIMEOUT
```

**Two of the three are the same minute on two correlated index roots**, so this is **two
independent market events**, not three. All three are 40-bar **timeouts** — they ran the full τ
and happened to close up — so they are not even the mechanism the construction claims. By root:
only NQ (+24.6) and ES (+23.0) are positive; **five of seven roots lose.**

## 4. The methodological finding, which outlives the cell

**The matched control compares MEANS, and a mean on a tail-dominated distribution is exactly where
a count-matched random draw is least informative.** A random draw from a fat-tailed pool rarely
picks the three largest, so the real cell's fat right tail clears p95 easily. The control was
technically correct and practically misleading.

**Rule to carry: a matched control on the mean needs a median or trimmed-mean companion whenever
the cell is tail-dominated.** Had that been in place, every "above p95" in §3 would have been
flagged at the point of measurement rather than by a separate concentration check. This is the
programme's existing tail-carried rule applied to the CONTROL rather than to the book.

## 5. Disposition

1. **The volume filter is not a result.** It does nothing on the pool, and its apparent effect on
   the spike cell is two market events on n = 56 at t = +0.80 with a median of −$9.00.
2. **The design was sound and the feedback loop worked.** The time-of-day normalisation was
   necessary (raw volume would have cut the working cell at corr +0.235) and the no-warm-up
   requirement was satisfied exactly as the principal specified.
3. **The precedent is explicit and this fits it:** a layer selected in-sample went from +80/trade
   to −29 out of sample (D430). This cell is that shape — roughly forty in-sample looks deep, with
   the spike profile itself selected from this same data and the volume filters layered on top.
4. **No component line, no promotion, no holdout spent.** The axis remains the principal's to close.
