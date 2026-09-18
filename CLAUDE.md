# CLAUDE.md

*How to work here.* Rules: `docs/RULES.md` · truth: `docs/FINDINGS.md` · state:
`docs/internal/PICKUP.md`.

## Speed

Nulls dominate runtime. **Build every runner on `scripts/fast_null.py`** (~6×,
usage in its docstring) and call **`assert_matches_scorer` once per study** — it
caught a one-ULP mismatch that would have made D282's null incomparable to its
own study.

**Parallelise by default; the question is threads or processes.** Threads for
numpy + read-only fan-out (`parallel_map`, 6.00×/2.28×). **Processes for
GIL-bound pure Python** — D288 threaded two such families into 0.24 of 16 cores
at 4.9 GB WS (17 min serial → 47 threaded); 8 subprocesses over `symbols[i::N]`
→ 4 min. Stride, don't slice (bar counts vary ~10×); prove chunk == whole
bit-identically first.

**Cache costly derived arrays** in `temp/`, keyed on fixture *and* every
estimator module's mtime — else stale numbers that look fine. D288: 17 min → 20 s
across four entry points.

**Exactness, not tolerance.** Only *hoist* invariants, *skip* what nothing reads,
or *vectorise a loop into one axis-wise call* — never reorder a float sum or
vectorise an RNG draw. Guard a rewrite with equality vs the loop it replaced,
probed on a **tie-heavy** input (ties are where rewrites disagree). Sparse
`bincount` over events beats masked full-array sums. Check with
`fast_null.py --verify`. **Profile first:** every guess here has been wrong.

**Per-call cost is not scaling, and backgrounding is not a licence.** `parallel_map`
now always prints `[SPEED] sum(item time)/wall` and shouts below 70% — because
D385 ran **92 minutes at 3.28× on 6 workers (55%)** while I profiled two call
timings, called the cost inherent, and launched. The tell was one division
available at the sixth item. **Threads are right only while the work releases the
GIL; that is a property of the workload, not of the choice.** Under the floor, go
to processes over `items[i::N]`.

**Before launching anything projected over ~10 min: state the projected wall time,
do one optimisation pass, and say what you did.** `run_in_background` exists so the
agent does not block — not so the number stops mattering. It is the principal's
machine and iteration loop.

## Reporting a result

**All four groups, always.** A number without what makes it interpretable is not
a result.

1. **Performance, NET AND GROSS side by side** — plus exposure, vol, maxDD, mean
   move per trade vs `2c`, and **breakeven cost** (bp/side or borrow). Gross
   separates cost failure from signal failure: opposite fixes. CAGR without
   exposure says nothing (D279, D284). **Estimate the spread of the names HELD
   (Corwin-Schultz off the OHLC) rather than trusting a fee assumption** — D285
   missed a guessed 15 bp/side bar by 0.65 and the held names measured 33.8.
2. **Trade distribution** — count, mean, **median**, win rate, payoff, holding
   run, skew, kurtosis. Then **trim 1% from BOTH tails and report all three
   means**: ex-top, ex-bottom, and trimmed. Dropping only winners is a flag, not
   a verdict — on a two-sided fat-tailed book it always frightens (D307 called
   four cells lottery books on it; the symmetric trim was +24 to +52 bp and at
   N=19 the *losing* tail was larger, −181% against +161%). **A mean below its
   median is the tell** that the left tail is doing the work (D285: top 1% =
   196.9% of P&L, and there it was genuine).
3. **What the winners depend on** — names to reach half the P&L, top-1/5/10 name
   share, profitable years, and the split on what the universe varies: dead vs
   alive, era, and **price** (cost in bp scales inversely with price; killed
   D284).
4. **Nulls: the distribution, not the percentile alone** — report **p50 and
   p95** beside the score and say whether the null is decisive. Four cases here
   of a *losing* random control at the 100th (R7). **A SAMPLE p95 IS BIASED
   TOWARD THE CENTRE, so every finite-draw null is more lenient than it looks:**
   carry the p95's bootstrap SE and record a margin within 2 SE as UNRESOLVED
   (D373's rule), and **where the null's group is finite and small — a time
   rotation of ONE market-level series is `Td-1` offsets, ~4,000 — enumerate it
   instead of sampling** (SE then exactly 0; ~6 min a cell). C2b: all four of
   D361's exact p95s came in above their published 200-draw values, and the one
   cell whose margin was thin fell from +6.4 to +0.52. Per-name rotations, B/B_c
   and C are NOT enumerable — there the bias stands and only (i) or more draws
   touch it.

**Where a path exists, both lenses.** Path-invariant (every candidate trade, no
slot cap, scored per TRADE) and path-variant (the slot-limited book, scored in
bp/bar) — **never compared on the same statistic**. Their difference is
**opportunity cost**, which nothing here has measured: `sel = rank < N_SLOTS`, so
the refill pool IS the slot count and an exit on a still-selected name re-enters
it. `docs/FINDINGS.md` §10.

## Runner assertions

All three, every runner. Patterns in `scripts/run_overnight_long.py`.

1. **Lag audit** — re-derive the held set from `score[:, t-1]` in a **second
   implementation that never calls the selection function**. Killed D279's first
   result; ~93% of its apparent edge was the bug.
2. **Sign audit, in money** — assert a favourable move pays *positively*, and a
   dividend moves long and short *oppositely*. A sign asserted in prose inverted
   D280.
3. **Right-quantity** — assert the compounded grid differs from the one you did
   *not* mean to score.

**A self-test that cannot fail is worse than none:** check the audit *raises* on
a deliberately broken book.

**A control must share the treatment's nuisance, not just its count.**
Matched-count ≠ matched-turnover (D279) ≠ matched-volatility (D284).
**A random subset is never a control for a persistent selector** — it re-draws
each bar, so it churns (D291: 2.4× the entries, up to 7×, which voided 87 cells).
Randomise the *partner*, not the *membership*.

**Cost-cutting ≠ edge-sharpening.** A longer hold lifts breakeven by amortising
one round trip; per-bar edge usually *falls*, so Sharpe can drop as cost
coverage rises. Say which moved: edge per unit exposure, or cost per trade.
**And check what the exit keys on** — D285's fired on displacement by unrelated
names, not on its own signal reverting.

## The books

`docs/BOOK.md` (personal: S1, S2; not at capital) and `docs/BOOK_PROP.md` (prop:
**one** — the MACD day-session arm, admitted 2026-09-13). Append-only — amended
or retired in writing, never quietly edited.

**Clearing a study's hurdles does not admit a strategy.** R8 needs a separate
pre-registered out-of-sample test on a fixture it has never seen; the prop book
also needs hurdle P (R11), all six. **An empty book with stated standards beats
a populated one with borrowed ones.**

### Two altitudes: candidate and component. Score BOTH, every time.

**The book is built by layering, not by finding one strategy that clears the
bar.** The prop account's geometry needs a book-level Sharpe of roughly 1.5–2;
no single construction here has come within half of that, and none has to.
Five components at net Sharpe 0.4–0.6 with pairwise correlation under 0.3 reach
it. **A standalone failure of hurdle P is therefore not a verdict on the
construction** — it is the answer to one of two questions.

On 2026-09-12 three prop-track records (D463, D464 and their predecessor C1)
were each written as "closed / not a candidate" on standalone bars without a
component line. The shell-line figures that exposed it (net Sharpe 0.62 and 0.42
at ρ 0.09, a 0.91 book) turned out to be at full-size cost in basis points; under
the ledger's standard (dollars at micro size, $3 a round trip ≈ 2 bp) they are
0.37 and −0.01 and no book (D466). **Both errors have one shape: a component
number computed outside the runner, under a cost line other than the one the
account pays.** The principal caught the first; the pre-registered standard
caught the second. Do not repeat either:

1. **Every construction tested for either book gets a component line in the
   RESULT, whether or not it clears the standalone bar:** net Sharpe on the
   in-sample window at the instrument's minimum tradable size and the cost that
   size pays (in dollars, computed by the runner), hit rate, skew, gross beside
   net, and its correlation with every component already in the ledger. The line
   is not optional and "not a candidate" without it is an incomplete record.
2. **The components ledger is `docs/COMPONENTS_PROP.md`** (append-only, like the
   books): the admission standard for a component is pre-registered there, every
   scored construction is entered with its numbers, and the assembled book is
   the object hurdle P is tested on. **A component is admitted to the ledger on
   its standard; only the assembled book is admitted to `BOOK_PROP.md`.**
3. **Choosing components after seeing their Sharpes is selection.** The assembled
   book is confirmed only on a slice no component has seen (for the futures
   fixtures, 2024-01 onward), and the ledger records the order in which
   components were added.
4. **Two constructions that share an instrument but not a clock diversify**
   (overnight vs. the last half-hour: ρ = 0.09 on ES). Two that share a clock
   and a signal do not (a gated subset of C1 is C1). Say which before adding.

## Files

**What data exists: [`docs/data-available.md`](docs/data-available.md).** Every fixture, its
span, its symbol count, and the thing that bites a study that reads it unchecked. Read it
before fetching anything — the answer is often already on disk.

| | tracked | contract |
|---|---|---|
| `working/` | yes | in use; losing it costs work now |
| `data/raw/` | no | **gitignored CACHE, not disposable** — re-fetchable, but losing it costs money or hours |
| `temp/` | no | **deletable any time, unasked, unread** |

One-way: `working/` → `temp/` → gone. Neither replaces `scripts/`, `data/`,
`docs/decisions/` — **a file a record quotes is evidence: it belongs in
`data/`.**

**`temp/` is not a cache, and the distinction is not cosmetic.** 111 GB of CME futures was
written to `temp/databento/` on 2026-09-11 and moved to `data/raw/databento/` the next day,
because `temp/README.md` promises *"if deleting a file would cost something, it does not
belong here"* — and that data is free to re-fetch only until ~2026-10-11, then $7,719.
**A raw cache goes in `data/raw/` (D191: cache the raw, commit the derived). `temp/` is for
things you would not mind losing mid-command.**

## Habits

- **>~2 min → `run_in_background: true`. Never `nohup`/`&`** — they detach, so the
  wrapper exits at once and the completion notice fires on nothing, leaving you
  polling with foreground `sleep`s that block the agent. **Never poll**; you are
  re-invoked on real exit.
- **Pre-registration committed before the runner exists; result separately** (R8).
- Write tool over long heredocs. **Backticks in `git commit -m` are command
  substitution** — they spliced a shell banner into a commit here. `\\n` inside
  `<<'EOF'` stays literal: a silent no-op `str.replace`.
