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
