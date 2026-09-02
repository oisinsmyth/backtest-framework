# CLAUDE.md

*How to work here.* Discipline: [`docs/RULES.md`](docs/RULES.md). What is true:
[`docs/FINDINGS.md`](docs/FINDINGS.md). Where to pick up: [`PICKUP.md`](PICKUP.md).

## Speed

Nulls are the bottleneck. **Build every runner on `scripts/fast_null.py`** (~6×;
usage in its docstring) and call **`assert_matches_scorer` once per study** — it
already caught a one-ULP convention mismatch that would have made D282's null
incomparable to its own study. `parallel_map` threads any read-only per-item
work, not just nulls.

**Exactness, not tolerance.** Optimise only by *hoisting* identical arithmetic
out of a loop or *skipping* what nothing reads — never reorder a float sum or
vectorise an RNG draw. Verify with `fast_null.py --verify`. **Profile first:**
both my guesses were wrong.

## Reporting a result

**A number without the thing that makes it interpretable is not a result.** Four
groups, every time, whatever the verdict.

1. **Performance, NET AND GROSS side by side** — plus `exposure`, `vol`,
   `maxDD`, mean move per trade vs `2c`, and the **breakeven cost** (bp/side or
   borrow rate). Gross separates a cost failure from a signal failure; they need
   opposite fixes. A CAGR without exposure says nothing (D279, D284).
2. **Trade distribution** — count, mean, **median**, win rate, payoff, holding
   run, skew, kurtosis. Then: **remove the best 1% and re-report the mean.** A
   positive mean carried by a handful of trades is a lottery ticket, and the
   median usually says so first (D271, D285: top 1% carried 196.9% of P&L).
3. **What the winners depend on** — names to reach half the P&L, top-1/5/10 name
   share, profitable years, and the split across what the universe varies on:
   dead vs alive, era, and **price** (cost in bp is inversely proportional to
   price; D284 died on it).
4. **Nulls: the distribution, never the percentile alone.** Report **p50 and
   p95** beside the score, and say whether the null is decisive. Four cases here
   of a *losing random control* clearing at the 100th ([R7](docs/RULES.md#r7)).

## Every runner needs these assertions

Copy from `scripts/run_overnight_long.py`, which has all three.

1. **Lag audit** — re-derive the held set from `score[:, t-1]` in a **second
   implementation that does not call the selection function**. D279's first
   result died here; ~93% of its apparent edge was the bug.
2. **Sign audit, settled in money** — assert a favourable move contributes
   *positively*, and that a dividend moves a long and a short *oppositely*. A
   sign asserted in prose inverted D280.
3. **Not-the-wrong-quantity** — assert the compounded grid differs from the one
   you did *not* mean to score.

**A self-test that cannot fail is worse than none** — check that the audit
*raises* on a deliberately broken book.

**A control must share the treatment's nuisance, not just its count.**
Matched-count ≠ matched-turnover (D279) ≠ matched-volatility (D284).

## The books

[`docs/BOOK.md`](docs/BOOK.md) (personal: S1, S2, not promoted to capital) and
[`docs/BOOK_PROP.md`](docs/BOOK_PROP.md) (prop: **none**). Append-only — amended
or retired in writing, never quietly edited.

**Clearing a study's hurdles does not admit a strategy.** [R8](docs/RULES.md#r8)
requires a separate pre-registered out-of-sample test on a fixture it has never
seen; the prop book also needs [hurdle P](docs/RULES.md#r11), all six. **An
empty book with stated standards beats a populated one with borrowed ones.**

## Files

| | tracked? | contract |
|---|---|---|
| [`working/`](working/) | yes | in active use; losing it costs real work now |
| [`temp/`](temp/) | no | **deletable at any moment, unasked, without reading it** |

One-way: `working/` → `temp/` → gone. Neither replaces `scripts/`, `data/` or
`docs/decisions/` — **if a record quotes a number from a file, that file is
evidence and belongs in `data/`.**

## Working habits

- Background anything over a couple of minutes (`nohup … &`) and poll the log.
- **Commit the pre-registration before the runner exists; the result separately**
  ([R8](docs/RULES.md#r8)). Several results here were saved by it.
- Prefer the Write tool to long heredocs — quote-heavy ones have failed, and
  `\\n` inside `<<'EOF'` stays two literal characters, silently making a
  `str.replace` match nothing.
