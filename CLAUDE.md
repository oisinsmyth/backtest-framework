# CLAUDE.md

Working notes for this repo. The research discipline lives in
[`docs/RULES.md`](docs/RULES.md); what has been measured lives in
[`docs/FINDINGS.md`](docs/FINDINGS.md); where to pick up lives in
[`PICKUP.md`](PICKUP.md). Read those first — this file is about *how to work*,
not what is true.

---

## Optimise runs and nulls for time

**A study that takes half an hour does not get iterated on.** Rotation nulls are
the bottleneck in almost every runner here, and the fix is already written:

```
scripts/fast_null.py     # bit-identical nulls, ~6x faster, threaded fan-out
```

**Use it for every new runner.** Measured on the daily fixture, 6 books × 100
sims, 16 cpus: `original serial 199.6s → fast serial 87.4s (2.28×) → fast + 6
threads 33.3s (6.00×)`. On an 18-cell study that is **32 minutes down to about
5**.

```python
from fast_null import NullContext, run_nulls, parallel_map

ctx = NullContext(panel)                      # close-to-close default
ctx.assert_matches_scorer(pos, my_scorer,     # <-- DO THIS ONCE PER STUDY
                          rf_annual=RF, borrow_annual=BORROW, ppy=PPY)
draws = run_nulls(ctx, books, n_sims=300, seed=0, ppy=PPY,
                  rf_annual=RF, borrow_annual=BORROW)
```

**`assert_matches_scorer` is not optional.** It runs your study's own scorer and
the fast one on the real book and asserts they agree *exactly*. It has already
caught a real convention mismatch: D282's overnight scorer divides `gross` and
`cost` by `nlive` separately while `RP.pooled_returns` subtracts first — a
**one-ULP** difference that would have made the overnight null incomparable to
its own study. `NullContext` takes `simple`, `mask`, `turnover` and `divide` so
both study families are covered; pick the convention, don't inherit it.

**`parallel_map` is for any independent per-item work**, not only nulls —
building books, scoring cells, per-cell diagnostics. Threads, not processes:
measured 2.28× against 2.23×, with no pickling, no per-worker panel reload and
no spawn. Anything it touches must be read-only.

### The rule that governs all of this

**Exactness, not tolerance.** A null that differs from the original by one float
is not a faster null, it is a *different* null, and every percentile in
D256–D285 becomes incomparable. Optimise only by **hoisting** identical
arithmetic out of a loop or **skipping** a quantity nothing reads. **Never
reorder a floating-point sum**, never vectorise an RNG draw sequence, and run
`--verify` after any change:

```bash
uv run python scripts/fast_null.py --verify
```

### Where the time actually went, so the next hunt starts in the right place

Measure before optimising — my first two guesses here were both wrong. What was
slow was not what it looked like:

1. **`pooled_returns` recomputed `np.expm1(...)` over the whole panel on every
   call** — the same 6.6M-element array, 300 times per book. The largest single
   cost, and invisible until profiled.
2. **`score` computes ~15 statistics; a null reads two.** The rest were computed
   and discarded 300 times.
3. **The roll touched 6.6M cells when a book is ~1% dense.**

And I predicted threads would buy almost nothing because small numpy ops hold
the GIL. **That was wrong** — numpy releases it enough, and threads matched
processes.

---

## Where to put files: `working/` then `temp/`

Two folders, and the difference between them is **time, not importance**.

| | | tracked? | the contract |
|---|---|---|---|
| [`working/`](working/) | in active use | **yes** | losing it would cost real work **right now** |
| [`temp/`](temp/) | done with | **no** — git-ignored | **could be deleted between two commands and nothing of value would be lost** |

**`temp/` is a promise to the reader**: anyone may empty it at any moment,
without asking, without reading the contents, without checking what depends on
them. **If deleting a file would cost something, it does not belong there.**

**The lifecycle is one-way: `working/` → `temp/` → gone.** When a file stops
being needed it *moves*, it does not linger. A file sitting in `working/` across
several sessions is telling you it is either finished or abandoned — promote it
to `scripts/` or drop it in `temp/`.

*(`working/` rather than "in-use" or "live": this repo already uses **live** for
open research questions — see FINDINGS §9 — and overloading it would be worse
than a slightly duller name.)*

**Neither replaces the real homes.** A runner that has run belongs in `scripts/`,
the numbers it produced in `data/`, the reasoning in `docs/decisions/`. **If a
decision record quotes a number from a file, that file is evidence and belongs
in `data/`, not in either of these.**

## The two books are the output, and almost nothing gets in

| | | |
|---|---|---|
| [`docs/BOOK.md`](docs/BOOK.md) | personal track | S1, S2 — **admitted, not promoted to capital** |
| [`docs/BOOK_PROP.md`](docs/BOOK_PROP.md) | prop track | **admitted arms: none**, and it says so on line 3 |

Both are **append-only**: an entry is amended or retired *in writing*, never
quietly edited, and every entry carries its own falsification conditions.

**A result clearing its hurdles does NOT enter the book.** Under
[R8](docs/RULES.md#r8) admission needs a **pre-registered out-of-sample test on
a fixture the strategy has never seen** — a separate study, with its own record.
The prop book additionally needs [hurdle P](docs/RULES.md#r11), all six.
Nothing in D264–D285 produced a candidate, so nothing has been taken out of
sample and **D246's reserved wide-universe cohort is still unspent.**

**An empty book with stated standards is worth more than a populated one with
borrowed standards** — `BOOK_PROP.md` says that about itself, and it is the
posture to keep. Do not add an entry because a study looked good; add it because
a second, pre-registered test on untouched data agreed.

## How to report a result

**A number without the thing that makes it interpretable is not a result.** Four
groups, every time, whatever the verdict.

**1 — Performance, NET AND GROSS side by side.** Gross means zero fees, zero
borrow, zero `rf`. Report `exposure`, `CAGR`, `Sharpe`, `vol`, `maxDD`, and the
**mean move per trade against `2c`**. Without gross you cannot tell a cost
failure from a signal failure, and they need opposite fixes — D279 lost
**−0.432 GROSS**, so no cost improvement could ever have saved it. Without
exposure a CAGR is meaningless: D284's `+0.27%` was earned on **0.75% gross
exposure**, so it is a small sleeve with a large edge, not a small edge.

**Also report the breakeven cost** — half-spread in bp/side, or borrow rate —
because it is a property of the book rather than of your fee assumption. D284
cleared its cost bar at **2.41×** and still died on a breakeven half-spread of
**11.36 bp/side**.

**2 — Trade distribution, and it is where results go to die.** Trade count,
mean, **median**, win rate, payoff, holding-run length, skew, kurtosis. Then the
one that decides it:

> **Remove the best 1% of trades and re-report the mean.**

D271 had three arms at `+3.12 / +5.13 / +1.57` bp go to `−0.63 / −1.57 / −2.37`.
D285's book showed the top 1% carrying **196.9% of P&L** — the other 99% were
collectively negative. **A positive mean carried by a handful of trades is a
lottery ticket, not an edge, and the median usually says so first.**

**3 — What the winners actually depend on.** Attribute the P&L before claiming
it. At minimum: **how many names to reach half of it**, the top-1/5/10 name
share, profitable years out of years traded, and the split across whatever the
universe varies on — dead vs alive, era, and **price**, since cost in bp is
inversely proportional to price. D284 died on three columns: **$13.19 median,
$1.92 tenth percentile, 25.7% of positions under $5.**

**4 — Nulls: the distribution, never the percentile alone.** Report the null's
**p50 and p95** beside the cell's score. A percentile on its own hides
everything: D279's `S1_short|all` sat at the **100th on both legs with −0.757
Sharpe and −2.45% CAGR**, because its null was centred at **p50 −1.058**.
Anything above −0.99 cleared. Say explicitly whether the null is decisive —
[R7](docs/RULES.md#r7)'s corollary, and there are now four measured cases here
of a *losing random control* clearing at the 100th.

## Every runner needs these three assertions

Two results in this repo were destroyed by defects that care does not prevent,
so they are excluded by assertion instead. Copy the patterns from
`scripts/run_overnight_long.py`, which has all three.

1. **Lag audit.** Re-derive the held set from `score[:, t-1]` in a **second
   implementation that does not call the selection function**. A check sharing
   the code it checks cannot disagree with it. D279's first result reported two
   survivors at +2.250 Sharpe; ranked with `score[:, t-1]` instead of
   `score[:, t]` it is **−0.638**, and ~93% of the apparent edge was the bug.
2. **Sign audit, settled in money.** Assert that a name which moves the
   favourable way contributes **positively**, and that a dividend moves a long
   and a short in **opposite** directions. D280 parts 3–5 were inverted by a
   sign convention asserted in prose and never checked against a P&L.
3. **Not-the-wrong-quantity.** Assert the compounded grid differs materially
   from the one you did *not* mean to score. An overnight book silently wired to
   close-to-close returns looks entirely normal in the output.

**And a self-test that cannot fail is worse than none.** Check the negative
case: that the audit *raises* on a deliberately broken book. One of mine passed
vacuously because the synthetic score was constant over time, which makes lagged
and unlagged selections identical by construction.

**One design rule, because it cost three studies to learn:** a control must
share the treatment's **nuisance**, not just its count. Matched-count is not
matched-turnover (D279) and neither is matched-volatility (D284).

## Long-running work

- Background anything over a couple of minutes (`nohup … &`) and poll the log
  rather than blocking a foreground call.
- Commit the **pre-registration before the runner exists**, and the **result in
  a separate commit** ([R8](docs/RULES.md#r8)). This is not a style preference;
  several results in this repo were saved by it.

## Shell

Prefer the Write tool over long heredocs. Heredocs work — apostrophes,
backticks, `&&` chaining are all fine — but very long, quote-heavy commands have
failed here, and `\\n` inside a `<<'EOF'` body stays two literal characters,
which silently makes a `str.replace` match nothing.
