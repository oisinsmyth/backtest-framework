# D452 — trading the grow-right lines with hysteresis and trend-side breaks, in-sample

*Pre-registration. Written before the run (R8); the runner is D451's, `scripts/run_d451_grow_trades.py`,
given this line and its own output file. Sequel to
[D451](D451-RESULT-the-grow-right-lines-trade-exactly-like-the-pivot-lines-and-both-time-their-own-trades-worse-than-chance.md).
In-sample only, by the principal's instruction: the mining panel, the same 1,573 names; no
holdout is read.*

## 1. What changed since D451

D451 found the grow-right construction traded exactly like the pivot lines (long +1.0 ± 3.2 bp,
short −44.9). The principal then diagnosed the windows as too small: it was impossible to tell a
trend's end from a gradient update. Measured on the twelve page names, 58% of shown-window deaths
were the hull lines pinching under the minimum width, 21% exceeding the maximum, 19% the gradient
gap, none a bar through a line, and half were followed within five bars by a same-direction
overlapping window. Two changes followed, both on `scripts/d451_causal_grow.py` and both pages:

1. **Hysteresis** (`surv=loose`): a window is born under the full filter set and survives under
   containment alone; it ends only on a break of the line the trader had, the survive width cap,
   or max length. Audit [H] asserts it; [XH] shows the audit rejects strict survival.
2. **Trend-side breaks** (`bside=trend`): only support can end an uptrend, only resistance a
   downtrend. 28% of loose-survival ends had been breakouts in the trend's own direction.

The principal's line for this study, chosen on the step page:

    split=causal grow=parallel back=9 atmax=end tol=2 mt=2 basis=wick minlen=30 maxlen=1000
    mw=5.5 maxw=55 maxoff=6.5 mintd=10 tau=1 brk=2 bbars=1 bon=close bside=trend
    surv=loose stol=4 smaxw=40

On the twelve page names: 79 runs, 54% of bars covered (D451's line: 128 runs, 62%), windows
at their last bar 33–122 bars, widest 25%, price at most 4% off the nearer line.

## 2. The question, unchanged

D450/D451's rule: **in while there is a trend, out when there is not** — both lines drawn,
gradients of the same sign, both steeper than `gmin`, read at the close; enter at that close, exit
at the close of the first bar no longer in it. `gmin` swept over {0, 10, 25, 50, 100, 200} %/yr,
headline 25. Two sources in one run: **GROW** (this line) and **CAUSAL** (D399's `CELL_FINAL`,
which must reproduce D451's numbers). Same panel, eligibility, split guard, spread, nulls
(within-name time rotation of the state series per trade, 200 draws; D434's book rotation null,
300 draws) and audits ([V], [XV], [F], [S], [M], [N], [SPEED]) as D451.

## 3. Predictions, in the runner's quantities

- P1. GROW long at `gmin` 25: gross mean per trade between −20 and +30 bp; short negative; neither
  side above its per-trade null p95 by 2 SE. The mechanism D450 named — a confirmed direction is
  a late one — does not depend on how long the window lives.
- P2. The trades are longer and fewer: GROW long median hold above 10 bars (D451: 6), and fewer
  than 63,340 long trades at the headline.
- P3. The gradient sweep still falls: GROW long gross at `gmin` 200 below its value at `gmin` 0.
- P4. CAUSAL reproduces D451 exactly: long +16.8, short −41.9 at `gmin` ≤ 25.
- P5. The rotation null's long p50 is again positive and above the score on both sources.

## 4. What would change the plan

A GROW long gross above its null p95 by more than 2 SE with a positive median at the headline,
or P3 inverted: a held-out test on unseen names for this line. Anything else: the window's
lifetime was not the missing ingredient either, and the next quantity to read is the channel's
level, not its direction.
