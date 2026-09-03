# CLAUDE.md

*How to work here.* Rules: `docs/RULES.md` · truth: `docs/FINDINGS.md` · state:
`PICKUP.md`.

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
   of a *losing* random control at the 100th (R7).

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
**none**). Append-only — amended or retired in writing, never quietly edited.

**Clearing a study's hurdles does not admit a strategy.** R8 needs a separate
pre-registered out-of-sample test on a fixture it has never seen; the prop book
also needs hurdle P (R11), all six. **An empty book with stated standards beats
a populated one with borrowed ones.**

## Files

| | tracked | contract |
|---|---|---|
| `working/` | yes | in use; losing it costs work now |
| `temp/` | no | **deletable any time, unasked, unread** |

One-way: `working/` → `temp/` → gone. Neither replaces `scripts/`, `data/`,
`docs/decisions/` — **a file a record quotes is evidence: it belongs in
`data/`.**

## Habits

- **>~2 min → `run_in_background: true`. Never `nohup`/`&`** — they detach, so the
  wrapper exits at once and the completion notice fires on nothing, leaving you
  polling with foreground `sleep`s that block the agent. **Never poll**; you are
  re-invoked on real exit.
- **Pre-registration committed before the runner exists; result separately** (R8).
- Write tool over long heredocs. **Backticks in `git commit -m` are command
  substitution** — they spliced a shell banner into a commit here. `\\n` inside
  `<<'EOF'` stays literal: a silent no-op `str.replace`.
