# RESULT D452 — longer windows, the same trade; the rule chops inside the window it was built to keep

*Runner `scripts/run_d451_grow_trades.py` with `--tag D452`; numbers
`data/d452_grow_trades_hysteresis.json`; log `temp/d452_full.log`; spec
[D452](D452-trading-the-grow-right-lines-with-hysteresis-in-sample.md). In-sample, the mining
panel, 1,573 names. Nothing is admitted; nothing is closed.*

## 0. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| P1 GROW long, gmin 25 | −20 to +30 bp; short negative; neither above null | **−6.6 ± 4.2**; short **−54.3 ± 5.1**; both at the 0th percentile of their null — held |
| P2 trades longer and fewer | hold median > 10 bars; n < 63,340 | hold median **7** (D451: 6) — **missed**; n = 37,784 — held |
| P3 sweep still falls | gmin 200 below gmin 0 | +9.1 → −23.1, monotone — held |
| P4 CAUSAL reproduces D451 | +16.8 / −41.9 | identical to the last digit — held |
| P5 null long p50 positive and above the score | | +58.4 vs −6.6 (GROW), +59.2 vs +16.8 (CAUSAL) — held |

## 1. The comparison, per trade, gross bp, same rule, same panel

| | GROW, hysteresis + trend-side break (this line) | GROW, D451's line | CAUSAL (D399) |
|---|---|---|---|
| both lines drawn on | 54% of bars | 57% | 28% |
| drawn runs / run median / window median | 89,051 / 8 / 35 | 160,461 / 7 / 34 | — |
| long n, gmin 25 | 37,784 | 63,340 | 28,740 |
| long gross / SE | **−6.6 / 4.2** | +1.0 / 3.2 | +16.8 / 5.5 |
| long median / trimmed / net | −98 / −26 / −80 | −30 / −13 / −68 | −125 / — / −58 |
| long win / hold | 41% / 7 | 46% / 6 | 42% / 10 |
| short gross / SE | **−54.3 / 5.1** | −44.9 / 4.0 | −41.9 / 6.5 |
| book long total / Sharpe / expo | +11.7% / 0.06 / 0.144 | +24.0% / 0.20 | +19.2% / 0.29 |
| book short total / Sharpe | −25.3% / −0.76 | −36.8% / −0.70 | −20.6% / −0.62 |
| book long null p50 / p95 | +39.3% / +42.6% | +48.4% / +53.4% | +31.1% / +34.4% |

Sweep, GROW long gross by gmin: 0 → +9.1, 10 → +0.5, 25 → −6.6, 50 → −13.7, 100 → −21.3,
200 → −23.1. Top trade CJES 2015-06-18, short, bars 977→1020, +9,729 bp, on the negative side.
Split-guard rejections 927. The walk ran 1,318 s at 10.4× on 12 processes (87%); 2,133 s in all.

## 2. Why the trades did not lengthen (P2)

The windows did what they were built to do — fewer, longer, ending only on a trend-side break or
the width cap — and the trades did not follow. On the twelve page names under this line, **a
third of the bars on which both lines are drawn are "not a trend" by the rule**: on 13% the two
gradients have opposite signs, on 20% they agree but one is under the 25%/yr floor. A drawn run
of median 14 bars carries 1.3 trades. The hysteresis keeps the window alive through a pullback;
the rule reads the pullback's re-tilted gradient, drops out, and re-enters when the slope
recovers. The window's lifetime was not the missing ingredient because the rule never used it.

## 3. Reading it

Three constructions of the channel (D399's pivots, D451's grow-right, D452's grow-right with
hysteresis) and two rules (D434's target-and-trail, the hold-while-trend of D450–D452) now give
six causal cells; every one is within noise of zero or negative on the long side, negative on the
short, and below a within-name rotation of its own trades. The direction of a channel, read at
the close, is not where the money is on this panel. What the hysteresis did buy is a window
that survives a pullback — which is exactly what a rule that reads the channel's *level* (price
against the two lines) would need, and none of these studies has read that quantity.

## 4. Audits carried

[V] extractor equality on 120,219 real trades within 1.9e-12 bp; [XV] rejects a one-bar shift;
[F] nine states on AA unchanged with future levels deleted; [S] sign in money; [M]
`assert_matches_scorer` on every book; [N] 37,784 / 29,650 at the headline. One defect, harmless:
the runner's last log line printed the output path relative to the repo and threw on the relative
path I passed, after the file was written; fixed by resolving the path.
