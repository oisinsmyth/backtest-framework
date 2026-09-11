# RESULT D451 — the grow-right lines trade exactly like the pivot lines, and both time their own trades worse than chance

*Runner `scripts/run_d451_grow_trades.py`; numbers `data/d451_grow_trades.json`; log
`temp/d451_full.log`; spec [D451](D451-trading-the-grow-right-lines-in-sample.md). In-sample,
the mining panel, 1,573 names. Nothing is admitted; nothing is closed — only the principal
closes an avenue.*

## 0. The prediction, and the answer

The principal, before the run: *"I predict that there won't be much of an increase on what was
done before."* Correct. Cell for cell:

| | GROW (D451's lines) | CAUSAL (D399's, D450's arm) |
|---|---|---|
| both lines drawn on | **57%** of bars | 28% |
| long, gmin 25: n | 63,340 | 28,740 |
| long, gmin 25: gross / ±SE | **+1.0 ± 3.2 bp** | +16.8 ± 5.5 |
| long: median / trimmed / net | −30 / −13 / −68 | −125 / — / −58 |
| long: win / hold | 46% / 6 bars | 42% / 10 |
| short, gmin 25: gross / ±SE | **−44.9 ± 4.0** | −41.9 ± 6.5 |
| short: median / net | −107 / −123 | −222 / −126 |
| book long: total / Sharpe / expo | +24.0% / 0.20 / 0.176 | +19.2% / 0.29 / 0.115 |
| book short: total / Sharpe | −36.8% / −0.70 | −20.6% / −0.62 |

The rebuilt construction draws lines on twice as many bars and produces twice as many trades,
and the mean gross per trade does not move: +1 bp long, −45 short, both within two SE of the
pivot construction's cells. CAUSAL reproduced D450 to the last digit (P4). Split-guard
rejections 1,267 (GROW's shorter, denser trades put more of them across a halving).

## 1. The sweep repeats D450's pattern (P3)

GROW long gross by minimum gradient, %/yr: 0 → +9.9, 10 → +5.2, 25 → +1.0, 50 → −2.5,
100 → −4.5, 200 → −11.2 (SE 3–5). Monotone down again. The steeper the confirmed channel, the
later it is; the construction did not change that because it is a property of confirmation,
not of the estimator. The short side is flat around −45 to −26 across the sweep.

## 2. Both sources time their own trades worse than chance

The within-name time rotation of the trend-state series (200 draws; the same trades, same
durations, same names, random bars, re-masked to the eligible universe):

| gmin 25 | score | null p50 | null p95 (SE) | score's percentile |
|---|---|---|---|---|
| GROW long | +1.0 bp | +36.8 | +41.5 (0.5) | 0.0 |
| CAUSAL long | +16.8 | +59.2 | +68.3 (0.6) | 0.0 |
| GROW short | −44.9 | −23.5 | −17.9 (0.5) | 0.0 |
| CAUSAL short | −41.9 | −24.5 | −14.6 (0.6) | 0.0 |

The null's p50 is *positive* on the long side and *less negative* on the short side than the
actual trades: holding the same names for the same durations on random bars earns more than
holding them while the channel says "trend". That is D434's finding again ("the channel traded
is worse than re-timing its own trades"), now on two constructions and the simplest rule. The
books say the same: GROW long +24.0% against a rotation p50 of +48.4% (Sharpe 0.20 vs null p95
0.63); GROW both −20.8% against p50 +15.8%.

## 3. What the winners depend on, and the top trade

GROW long at the headline: 1,405 names, 2 names to half the (small) P&L, top-1 name 49% of it,
10 of 17 years profitable; a tail-carried mean, as the trimmed mean −13 and the median −30 say.
Top trade: **ANV, short entered 2013-01-02, bars 754→859, +12,752 bp** — a 105-bar short on a
collapsing name, on the side whose total is negative. Nothing here is a strategy.

## 4. Reading it

The oracle's algorithm, made causal and dialled in by the principal's eye, is a better
*drawing* — twice the coverage, windows that are the oracle's own windows minus hindsight
(D451's audits [O], [F], [I]) — and an identical *trade*. Two constructions, two rules
(D434's target-and-trail, D450/D451's hold-while-trend), four causal cells, all within noise of
zero gross on the long side and negative on the short, all below their own rotation null. The
direction of a channel is a property of hindsight (memory `oracle-lines-leak-through-their-
existence`); improving the lines improves the picture, not the number.

What this does not test: anything other than the channel's *direction*. The D399 second-zone
work found a +10 bp touch effect that reproduced three times; a channel's *level* — where price
is inside it — is a different quantity from its slope, and this study did not read it.

## 5. Audits carried

[V] the vectorised trade extractor used by the null returned the same (entry, exit, side) list
as D450's loop on all 166,170 real trades, gross within 1.9e-12 bp; [XV] it rejects a one-bar
shift. [F] nine states on AA unchanged with every future level deleted. [S] the largest up-bar
inside a long trade (+3,987 bp) contributes with the right sign. [M] `assert_matches_scorer` on
every scored book. [N] 63,340 / 49,981 trades at the headline. [SPEED] the grow walk ran 709 s
wall at 9.57× on 12 processes (80%); whole run 1,333 s. The first launch, detached through
PowerShell, never spawned a worker — multiprocessing on Windows needs valid console handles —
and sat 15 minutes with an empty log; the runner now writes every worker failure to a file.
