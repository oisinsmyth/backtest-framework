# D724 STAGE 0 RESULT — NQ respects no intraday mean. Price moves AWAY from every anchor (VWAP, the open, the running midpoint, the overnight and opening-range midpoints) on quiet and big days alike. The day's size is known EARLY: at the prior close almost as well as at the open, and it predicts every later hour better than the last 30 minutes do. Size does not change the mean

*2026-10-01. The run: one run of `scripts/stage0_d724_which_mean.py` (1.3 min), with `--data-root` pointing at the
main checkout.*
- **The order:** the [design](D724-STAGE-0-DESIGN-which-mean-and-when-is-size-known.md) was committed first, and the
  runner (`8fe7325d`) before the run.
- **An earlier launch** crashed while loading bars (the worktree lacks the overnight fixture). No statistic had been
  computed and no output was written. The same code was relaunched with the data root.
- **Data:** NQ, 1,993 sessions, 2016-01-04 → 2023-12-29. Nothing dated 2024-01-01 or later was read.
- **Audits:**
  - the anchor lag audit (a second implementation by minute arithmetic, including 10 samples at 10:00) passed, and
    its canary fired;
  - the forecast audits fired on their leak canaries;
  - the self-test also shows the audit catching the 10:00 wrap-around (a naive t−31 column reads 15:59), which was
    fixed in the draft before the runner was committed.
- **Output:** `data/stage0_d724_which_mean.json`.

## 1. Q1 — which mean? None: NQ moves away from them

**κ** is the fraction of the deviation closed in 60 minutes; a negative κ means the price moves further away. **The
touch margin** is how much more often the price reaches the anchor than an equidistant mirror level, given
|D| ≥ 0.25.

| anchor | κ_60 (clustered t) | rotation p50 / p95; rank | κ to the close | touch margin (t) | reading |
|---|---|---|---:|---|---|
| A1 session VWAP | **−0.020** (−1.99) | −0.001 / +0.011; **0.008** | −0.067 | −0.011 (−1.9) | NOT RESPECTED |
| A2 the open | −0.012 (−2.33) | −0.000 / +0.007; **0.000** | −0.028 | −0.001 (−0.5) | NOT RESPECTED |
| A3 prior close | −0.006 (−1.60) | 0.033 | −0.004 | **+0.012 (+4.7)** | WEAK |
| A4 overnight midpoint | −0.012 (−2.56) | **0.000** | −0.027 | **+0.009 (+3.1)** | WEAK |
| A5 running midpoint | **−0.021** (−2.39) | **0.004** | −0.061 | −0.006 (−1.1) | NOT RESPECTED |
| A6 opening-range midpoint | −0.011 (−1.76) | 0.013 | −0.029 | +0.004 (+1.1) | NOT RESPECTED |
| A7 prior VWAP | −0.002 (−0.48) | 0.350 | +0.009 | +0.006 (+2.8) | WEAK |
| A0 the price 30 minutes ago (baseline) | −0.018 (−1.54) | 0.023 | −0.050 | **−0.036 (−4.5)** | — |

- **No anchor is RESPECTED.**
  - For the session anchors (VWAP, open, running midpoint, overnight midpoint), κ sits **below the 5th percentile**
    of the rotation.
  - The price continues away from where the day has been, most strongly in the afternoon. For VWAP, κ_60 is −0.011
    in the morning, −0.008 at midday and −0.044 in the afternoon. This is NQ's afternoon continuation seen from the
    side of the mean.
- **What is real is a level effect, not reversion.** Yesterday's close, the overnight midpoint and yesterday's VWAP
  are reached more often than equidistant mirror levels (t 4.7 / 3.1 / 2.8). But the expected move toward them is
  zero or negative. The price touches them in passing; it is not pulled back to them.
- **The 30-minute lag baseline** is reached less often than its mirror (t −4.5): momentum, at every horizon.

## 2. Q2 — how early is the size known? Early, and it lasts all day

| predictor | Spearman with the day's range | with the first hour's \|move\| |
|---|---:|---:|
| F_close (known at the prior close) | 0.475 | 0.188 |
| F_open (known at 09:30) | 0.495 | 0.207 |

- **Waiting for the open adds only 0.02.** The day's size is known the evening before.
- **The morning forecast predicts every later window.** F_open's Spearman with |P(t+h) − P(t)| is 0.19–0.24 at every t
  from 10:00 to 15:00, for h = 30, 60 and to the close.
- **It adds beyond the immediate state all day.** Its partial Spearman given the last 30 minutes' realised variance is
  0.16–0.21 in every cell (EARLY in all 18).
- **The immediate state catches up only after lunch.** At 13:00–14:00 over 30 and 60 minutes the last 30 minutes are
  as good or better (0.20–0.24; BOTH). In the morning they are clearly worse (0.11–0.15).
- **There is no range budget.** F_rem, the forecast range minus the range already made, correlates negatively with
  later moves (−0.15 to +0.05). A day that has already used its forecast range keeps moving, because volatility
  persists.

## 3. Q3 — does the size change the mean? No

- **κ_60 by F_open tercile:**

  | anchor | quiet | mid | big |
  |---|---:|---:|---:|
  | VWAP | −0.035 | −0.004 | −0.025 |
  | running midpoint | −0.032 | −0.007 | −0.029 |

- **Every anchor's quiet − big gap is inside its τ rotation** (ranks 0.14–0.54). The best (least negative) anchor is
  the prior VWAP in both terciles.
- **Quiet days do not revert.** On quiet days the price moves away from VWAP at least as much as on big days.
- **Split by the last 30 minutes' volatility, the same holds.** On the calmest immediate state, VWAP's κ is −0.040.

## 4. The money bridge (one MNQ, $4.07; reported only, 24 cells)

- **The trade:** the first stretch of |D| ≥ k after 10:00, toward the anchor, exiting on the touch, at +60 minutes,
  or at the close.
- **It loses on almost every cell:**
  - net Sharpe is negative for 22 of 24 cells (−0.08 to −1.57);
  - mean gross is between −$10.12 and +$1.37 on those 22.
- **Quiet days are the worst:** the quiet-tercile mean gross is negative in every cell (−$0.31 to −$75.61).
- **The two positive cells are one each from a family of 24, and are not evidence:**

  | cell | trades | gross | net Sharpe | note |
  |---|---:|---:|---:|---|
  | running midpoint, k 0.75 | 198 | +$7.21 | +0.14 | quiet −$43 |
  | the 30-minute lag, k 0.5 | 645 | +$5.45 | +0.10 | median −$3.07 |

  The lag cell is a momentum-level artefact, not reversion.

## 5. What it says

1. **Intraday mean reversion to a session mean is not a thing on NQ's day session**, on quiet days or big ones. The
   day session trends away from its means, most strongly in the afternoon. This agrees with every continuation
   result in the record: F2, the MACD arm, and D708's hourly side choice.
2. **The day's size is predictable the evening before.** It predicts every later hour, and the morning's knowledge
   stays useful even once the last 30 minutes are known. For the principal's size question: the prediction is early
   and it persists; it is not immediate and fading.
3. **Size does not pick the mean.** Quiet days are not range days on NQ: they are small-trend days.
4. **The only structure a price seeks is yesterday's levels** (close, overnight midpoint, VWAP): touched more often
   than chance, though not reverted to. As levels (targets, stops), not as means, they may be worth a look.
5. **Proposed, not decided:**
   - close quiet-day mean reversion on NQ's day session under R15, on the principal's word;
   - keep Q2's finding (early, persistent size knowledge) and Q1's level effect as structure for the next design.

## CLOSED, 2026-10-01, on the principal's word

The principal: "Close it".
- **Closed under R15:** intraday mean reversion to a session mean on NQ's day session, on quiet or big days. The
  means are VWAP, the open, and the running, overnight or opening-range midpoints, plus the prior close and prior
  VWAP as means.
- **Kept as structure:**
  - the day's size is known the evening before, and the knowledge persists all day;
  - yesterday's levels are touched beyond the mirror control, but there is no reversion to them.
