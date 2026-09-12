# RESULT D481 — the hand cell trades like every other causal channel: +12 bp gross long, below its own rotation null, and worse as the trend steepens

*Runner `scripts/run_d478_grow_trades.py --source hand`; numbers `data/d481_hand_trades.json`
(the first column is keyed "GROW" in the file and the null/book log lines — it is the hand cell);
log `temp/d481_full.log`; spec [D481](D481-trading-the-hand-cell-in-sample.md). In-sample, the
mining panel, 1,573 names. Nothing is admitted; nothing is closed — only the principal closes.*

## 0. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| P1 HAND long, gmin 25 | −20 to +30 bp; short negative; neither above its null | **+12.3 ± 3.4**; short **−38.7 ± 4.3**; both at the 0th percentile of their null — held |
| P2 coverage and count | both lines on > 40% of bars; more longs than 28,740 | 41%; 53,382 — held |
| P3 the sweep falls | gmin 200 below gmin 0 | +12.3 → +8.0 → −2.2 → −8.2 — held |
| P4 CAUSAL reproduces | +16.8 / −41.9 | identical — held |
| P5 null long p50 above the score | | +45.7 vs +12.3 — held |

## 1. Per trade, gross bp, same rule, same panel

| | HAND (D480's cell) | HYST (D479) | GROW (D478) | CAUSAL (D399) |
|---|---|---|---|---|
| both lines drawn on | 41% | 54% | 57% | 28% |
| long n, gmin 25 | 53,382 | 37,784 | 63,340 | 28,740 |
| long gross / SE | **+12.3 / 3.4** | −6.6 / 4.2 | +1.0 / 3.2 | +16.8 / 5.5 |
| long median / trimmed / net | −97 / +4.7 / −60 | −98 / −26 / −80 | −30 / −13 / −68 | −125 / — / −58 |
| long win / hold | 43% / 8 | 41% / 7 | 46% / 6 | 42% / 10 |
| short gross / SE | **−38.7 / 4.3** | −54.3 / 5.1 | −44.9 / 4.0 | −41.9 / 6.5 |
| null long p50 / p95 | +45.7 / +52.2 | +58.4 / +65.2 | +36.8 / +41.5 | +59.2 / +68.3 |
| book long total / Sharpe / expo | +27.1% / 0.27 / 0.166 | +11.7% / 0.06 | +24.0% / 0.20 | +19.2% / 0.29 |
| book long null p50 | +46.3% | +39.3% | +48.4% | +31.1% |
| book short total / Sharpe | −27.8% / −0.71 | −25.3% / −0.76 | −36.8% / −0.70 | −20.6% / −0.62 |

The rows at gmin 0 / 10 / 25 are identical because the cell carries D399's gradient floor
(δ = 1e-3/bar ≈ 29%/yr) inside the construction. Split-guard rejections 996. Spread of the
names held ~72 bp round trip; the long side is five spreads short of covering it.

## 2. Distribution and concentration (long, gmin 25)

Mean +12.3, median −97, trimmed +4.7: the mean is carried by the right tail, and the tail is
more spread than before — 20 names to half the P&L (D478: 2), top name 4%, top ten 28%, 10 of 17
years profitable. Top trade CVNA, long from 2020-06-04, bars 780→824, +7,822 bp.

## 3. Reading it

- **A construction that draws the principal's lines trades no differently.** The hand cell is
  the only construction that reproduces the eye's gradient (sign 92 / 87%, D480); under the
  same rule it earns +12 bp gross against a spread of 72, and a random re-timing of its own
  trades earns +46. That is the fifth causal cell, on four constructions and two rules, with the
  same shape: near zero gross long, negative short, below its rotation null, and falling as the
  gradient floor rises.
- **The steepness pattern held again**: +12.3 → −8.2 across the sweep. The cell confirms *five
  bars earlier* than the eye (D480's lag −5), so "late confirmation" is not the whole mechanism;
  a channel's slope read at the close carries no forward information on this panel however
  early it is read.
- **What changed is the tail, not the centre.** Half the long P&L now needs 20 names instead of 2,
  which is the drawing being better; the median trade is still −97 bp.

## 4. What this leaves

The direction of a channel is closed as an entry on this panel by any reading short of the
principal's word. What none of the five cells has read is the channel's **level** — where the
close sits between the two lines — which the hand cell's 4% margin makes a defined quantity for
the first time, and which is where the only reproducible daily effect found in this programme
(the +10 bp touch effect of D412–D433) lived.

## 5. Audits carried

[V] extractor equality on 146,572 real trades within 1.9e-12 bp; [XV] rejects a one-bar shift;
[F] nine states on AA unchanged with future levels deleted; [S] sign in money; [M]
`assert_matches_scorer` on every book; [N] 53,382 / 40,380 at the headline. [SPEED]: the hand
cell ran 317 s wall at 2.23× on 12 workers (19%) — the 200 longest histories took 270 s, the
per-name cost rising with history length — five minutes in all, so it was not re-engineered;
whole run 1,190 s.
