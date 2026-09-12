# D478 — trading the grow-right lines, in-sample: does the construction rebuilt from the oracle change what the channel's direction is worth?

*Pre-registration. Written before the runner exists (R8). Sequel to
[D477](D477-RESULT-the-ceiling-perfect-lines-pay-only-because-they-know-the-future-and-the-causal-lines-pay-nothing.md)
and [D476](D476-RESULT-the-channel-traded-is-worse-than-re-timing-its-own-trades.md). In-sample
only, by the principal's instruction: the mining panel, the same 1,573 names D476 and D477 used;
no holdout is read.*

## 1. What changed since D477

D477 found that the channel's direction, traded by holding while the channel exists, is worth
nothing in real time on D399's pivot construction (long +16.8 ± 5.5 bp gross, net −58; short
−41.9 ± 6.5), and that raising the gradient floor makes it *worse*. The principal then asked for
the causal construction to be rebuilt from the oracle's algorithm. That is `scripts/d478_causal_grow.py`
and the page "Grow Right" (artifact 6670af44): the oracle's left-to-right search with its two
hindsight leaks removed — the window grows one bar at a time, the line at bar t is the fit on
[A, t], nothing is drawn under the minimum length — every candidate window growing in parallel
with the longest survivor drawn (no chain, so no path dependence: audit [I]), and a break rule
(off here). Audits: [O] with the restart dials at their oracle values the windows are exactly
the one-bar greedy oracle's; [F] the lines up to t are unchanged when the series is cut at t;
[I] starting the walk a thousand bars later gives identical lines after max length bars; the
page and Python agree on every window on twelve names.

The principal dialled it in by eye and chose, for this test:

    split=causal grow=parallel back=9 atmax=end tol=2 mt=2 basis=wick minlen=30 maxlen=1000
    mw=5.5 maxw=55 maxoff=6.5 mintd=10 tau=1 brk=-1 bbars=1 bon=close

On the twelve page names that line draws both lines on 62% of bars (D399's `CELL_FINAL`: 28%),
128 runs, median drawn run 4–20 bars, window median 33–41 bars, width 9–28%.

## 2. The question

The same trading rule as D477, on the new lines: **in while there is a trend, out when there is
not.** A trend at bar t is both lines drawn, gradients of the same sign, both steeper than the
minimum `gmin`, read at the close of t. Enter at that close; exit at the close of the first bar
no longer in the trend, or flipped. No target, no stop, no holding cap. `gmin` swept over
{0, 10, 25, 50, 100, 200} %/yr, headline 25.

Two line sources, same run, same panel, same eligibility (keep_v2 floor), same split guard
(|log return| > 0.40 inside a trade rejects it), same Corwin–Schultz spread of the names held:

- **GROW** — the line above, from bar 0 of each name.
- **CAUSAL** — D399's `CELL_FINAL` paired construction, exactly D477's causal arm, so the two
  columns are comparable cell for cell and D477's causal numbers should reproduce.

The rule's own gradient-similarity gate is not applied (as in D477): parallelism is inside the
construction (`tau` = 1.0).

## 3. Nulls

D477 ran none because its oracle made the question empty. Here both sources are causal, so:

1. **Per-trade, within-name time rotation of the state series** (200 draws, seed 0). For each
   name the +1/−1/0 trend-state series is rolled by a random offset and re-masked to the
   eligible bars, and the same trade extractor is run on the rolled series against the real
   closes. It preserves the count and duration of trades and their name, and destroys their
   timing. Reported: the null's p50 and p95 of the mean gross bp per trade, each side, the
   headline `gmin`; the p95's bootstrap SE; a margin within 2 SE is UNRESOLVED (D373's rule).
2. **Book, D476's rotation null** (`fast_null.rotation_null`, 300 draws) on the headline
   long, short and both books, with `assert_matches_scorer` called once.

## 4. Predictions, in the runner's quantities

The principal's, verbatim: *"I predict that there won't be much of an increase on what was done
before."*

Mine, written to be checkable against `data/d478_grow_trades.json`:

- P1. GROW long at `gmin` 25: gross mean per trade between −10 and +40 bp (within 2 SE of
  D477's causal +16.8 ± 5.5); GROW short at `gmin` 25: negative. Neither side clears its
  per-trade null p95 after the 2-SE margin.
- P2. Trade count: GROW draws both lines on roughly twice as many bars as CAUSAL, so GROW's long
  trade count at `gmin` 25 exceeds CAUSAL's 28,740 — but the mean gross does not rise with it
  (P1). Median gross per trade negative on both sides (a tail-carried mean, as D477).
- P3. The monotone pattern of D477 repeats: GROW's long gross falls as `gmin` rises from 25 to
  200, because a confirmed steep channel is a late one. If it *rises* instead, that is the one
  result that would say the construction changed what the direction is worth.
- P4. CAUSAL reproduces D477 cell for cell (same code path, same panel): long +16.8, short −41.9
  at `gmin` ≤ 25.
- P5. Books: GROW long Sharpe below 0.5 and within the book null's p95; short negative.

## 5. What would change the plan

A GROW long gross above its null p95 by more than 2 SE, with a positive median, at the headline
`gmin` — or P3 inverted — would make the next step a held-out test on names this line has never
seen (the daily holdouts are spent for the *second-zone* line, not for this one: holdout
multiplicity is per line). Anything else: the construction lessons from the oracle do not move
the number, and the direction of a channel stays a property of hindsight.

## 6. Audits carried

[F] trader-side: states unchanged when every future level is deleted (D477's). [S] sign, in
money. [N] ≥ 100 trades a side at the headline. [V] the vectorised trade extractor used by the
null equals the loop extractor bit for bit on every real state series. [M] the book null's
`assert_matches_scorer`. [P] the projected wall time is stated before launch: the GROW walk is
~1 ms/bar in Python, ~5.5 M bars, run over processes.
