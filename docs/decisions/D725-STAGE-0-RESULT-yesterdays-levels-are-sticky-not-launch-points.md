# D725 STAGE 0 RESULT — NO-GO. A crossing of yesterday's close, VWAP or overnight midpoint does not continue: at 60 minutes it does no better, and slightly worse, than a crossing of a random equidistant level, and it falls back behind the level MORE often. Yesterday's levels are sticky, not launch points. Only yesterday's HIGH continues, and that is D668's spent break

*2026-10-01. The run: one run of `scripts/stage0_d725_level_crossings.py` (1.4 min, `--data-root` the main
checkout).*
- **The order:** the [pre-registration](D725-STAGE-0-PRE-REG-crossing-yesterdays-levels.md) was committed first, and
  the runner (`3aae8231`) before the run.
- **Data:** NQ, 1,993 sessions, 2016-01-04 → 2023-12-29. Nothing dated 2024-01-01 or later was read.
- **Audits:**
  - the vectorised crossings equal a plain-Python loop on 80 sampled days, and the peek canary fired;
  - the forward prices passed their audit, and the self-test shows the audit catching a wrapped index;
  - the F_close forecast and tier audits fired on their canaries.
- **Output:** `data/stage0_d725_level_crossings.json`.

## 1. P1 — continuation at 60 minutes (primary); the readings

The forward move is measured in σ_d units, t clustered by week; dollars are per MNQ.

| level | events | g_60 (t) | $ (median) | mirror's crossing $ (t) | level − mirror (t) | after drift | rotation p50 / p95; rank | Holm p | reading |
|---|---:|---|---|---|---|---|---|---:|---|
| L1 prior close | 1,105 | −0.006 (−0.63) | −$4.85 (−$2.50) | +$3.27 (+0.98) | −0.020 (−0.81) | −0.006 | +0.008 / +0.023; **0.068** | 1.0 | **NOTHING** |
| L2 prior VWAP | 945 | +0.002 (+0.16) | −$1.88 (−$1.50) | +$5.66 (+1.52) | −0.048 (−1.82) | +0.002 | +0.007 / +0.023; 0.299 | 1.0 | **NOT DISTINCT** |
| L3 overnight midpoint | 1,362 | −0.007 (−0.81) | −$1.90 (−$1.00) | +$4.91 (+1.77) | −0.033 (−1.78) | −0.007 | +0.009 / +0.023; **0.041** | 1.0 | **NOTHING** |
| *L4 prior high (reported)* | 823 | **+0.024 (+2.14)** | +$2.28 (+$3.00) | +$0.46 | +0.014 (+0.50) | +0.023 | — | — | *D668's break* |
| *L5 prior low (reported)* | 681 | −0.012 (−0.86) | −$3.50 (−$7.50) | −$2.00 | −0.045 (−1.22) | −0.010 | — | — | — |

- **None of the three primary levels continues.**
  - At 60 minutes each sits at or below its mirror. The paired differences are all negative, at t −0.8 to −1.8.
  - Two sit near the bottom of their rotation (ranks 0.068 and 0.041): a crossing of yesterday's close or of the
    overnight midpoint is, if anything, a worse continuation than a crossing of a random level at the same distance.
- **At 15 and 30 minutes the same holds.** L2 at 15 minutes is −$4.31 (t −2.20 in σ units).
- **To the close:** +$1.24 to +$3.53 per MNQ, at t ≤ 1.4, and not distinct from the mirror.

**P2, holding** (still beyond the level after 60 minutes, level against mirror):

| level | still beyond | mirror |
|---|---:|---:|
| L1 | 52.6% | 55.7% |
| L2 | 51.7% | 57.1% |
| L3 | 53.0% | 56.6% |

The price falls back behind yesterday's levels more often than behind arbitrary ones. With D724's finding (these
levels are touched more often than chance), the picture is consistent: **yesterday's levels are sticky zones that the
price returns to and crosses repeatedly.** A crossing is not a commitment.

## 2. P3 — the money (one MNQ, $4.07)

**As traded at 60 minutes:** gross −$4.85 / −$1.88 / −$1.90 for L1 / L2 / L3. Net Sharpe −0.95 / −0.62 / −0.70
(Sortino −1.21 / −0.85 / −0.96). Profitable in 1 of 8 years each.

**To the close:** gross +$1.24 / +$3.53 / +$3.39, under the $4.07 fee. Net Sharpe −0.16 / −0.03 / −0.04, with 3, 3
and 5 of 8 years positive.

**The size-only oracle (the day's REALISED range tercile, unknowable in advance),** mean gross per MNQ:

| level | 60 min: low / mid / high | to the close: low / mid / high |
|---|---|---|
| L1 | −$14.25 / −$7.40 / +$5.92 | −$21.82 / −$18.96 / **+$41.51** |
| L2 | −$22.96 / −$8.58 / +$19.34 | −$32.89 / −$14.10 / **+$45.87** |
| L3 | −$18.21 / −$0.17 / +$11.97 | −$25.39 / −$19.53 / **+$54.70** |

A ceiling exists: crossings on days that turn out big are trend days and pay.

**The evening-before forecast (F_close tercile, 2018-02 → 2023-12) does not reach it:**

| level | 60 min: low / mid / high | to the close: low / mid / high |
|---|---|---|
| L1 | −$3.00 / −$13.82 / −$7.28 | +$1.61 / −$2.06 / +$6.53 |
| L2 | −$15.29 / +$2.50 / +$6.12 | −$6.44 / **+$17.99** / +$3.66 |
| L3 | −$7.47 / +$2.69 / −$2.46 | −$7.02 / +$7.39 / +$7.44 |

- **The forecast's terciles are not ordered.** The one cell above 2 × $4.07 (L2, the mid tercile, to the close) is
  a single cell among 18 in a non-monotone pattern, and L2 itself reads NOT DISTINCT.
- **This is D720's lesson again:** a size forecast is a volatility forecast, and it does not find the trend days.

## 3. The reported reference: yesterday's high

- **Crossing above yesterday's high continues:**
  - at 60 minutes: +0.024 σ (t +2.14), +$2.28, median +$3.00;
  - to the close: +$10.68, median +$7.50; net Sharpe +0.33 (Sortino +0.46), 4 of 8 years positive, the largest year
    69% of the net.
- **It does not beat its own mirror** (+0.014, t 0.50).
- **This is D668's plain break of yesterday's range.** Its in-sample is spent, and its compressed-day subset (D680)
  is queued for the joint vault. It is recorded as a consistency check only: the break of the range continues where
  levels inside the range do not.

## 4. What it says

1. **GO is false.** No primary level reads CONTINUES, so the premise for a level-crossing rule fails.
2. **Yesterday's close, VWAP and overnight midpoint are sticky.** The price touches them more than chance (D724),
   recrosses them more than chance (P2 here), and a crossing of them continues no better than a crossing of an
   arbitrary level. **Their only edge is that they are reached, not that they are left.**
3. **Of yesterday's levels, only the edge of the range breaks** (L4, with D668). Levels inside the range do not.
4. **The evening-before size forecast does not reach the oracle's ceiling here either.** The days that pay are trend
   days, and no forecast in the record finds them in advance.
5. **Proposed, not decided:** close level-crossing continuation at yesterday's close, VWAP and overnight midpoint
   under R15, on the principal's word. Their stickiness is kept as structure: a level the price returns to is a
   candidate *target* for a trade already on, and a poor place for a stop.
