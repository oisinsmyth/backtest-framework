# D542 RESULT — two of six predictions falsified, one collapse that nearly published the opposite verdict, and a float defect that arrived with the interpreter

*Filename shortened on creation ([D540](D540-local-config-a-clone-never-receives.md)): the
path-length gate refused the full title at 89 characters. The H1 above is the full title.*

*2026-09-18. Spec committed in `26e0d70` BEFORE any code changed (R8). Nothing admitted to either
book. No holdout read: this record touches infrastructure and conventions, not a strategy.*

**Every collapse D542 pre-registered is done. Two predictions were wrong, both in the same
direction — I predicted "moves nothing" for changes whose arithmetic I had not yet measured.**

---

## The predictions, scored

| # | Prediction | Outcome |
|---|---|---|
| **P1** | Collapsing `StrategyResult.max_drawdown` and `buy_and_hold` moves **zero** stored values | **FALSIFIED** |
| **P2** | Collapsing `PositionResult.max_drawdown` moves zero; if anything moves it is ≤ `cost_bps/1e4` and becomes *less* negative | **Half confirmed, and it found something** |
| **P3** | `breakdown_study`'s percentiles become **exactly 100×** their old values | **HOLDS, departure 0.000e+00** |
| **P4** | Aligning `light_score` moves zero published null percentiles | **Confirmed analytically, not end-to-end** |
| **P5** | Where the `light_score` divergence is reachable it **deflates** rather than inflates | **CONFIRMED** |
| **P6** | The `raise` count moves **+1** | **FALSIFIED** |

### P1 — falsified, and the falsification is the more useful half

The *seed* half was right. `StrategyResult` already seeded its peak at `curve[0]`, which is what
`analytics.metrics.max_drawdown`'s `-inf` seed reduces to, so the seed alignment was a no-op.

What I had not measured when I wrote P1 is that the old bodies computed `x / peak - 1.0` while the
canonical form negated is `-((peak - x) / peak)`. **Algebraically equal, not bit-equal: on 407
curves including tie-heavy ones, 232 disagree at one ULP** (worst 1.11e-16). Every drawdown the
terrain module has ever published therefore moves in its last bit.

The same class appeared a second time in the same lane. `research/breakdown_study._max_drawdown`
computed `1.0 - nav/peak` where the canonical form is `(peak - nav)/peak` — **322 of 605 curves
disagree**, worst 1.11e-16 — while `research/breakout_nulls`' vectorised form already agreed
**bit-exactly on 603 of 603**. So there were never two arithmetics; there was one arithmetic and two
reorderings of it, and only the reorderings moved.

**The lesson is the shape of the prediction, not its content.** "This moves nothing" is a claim
about floating point, and I wrote it twice from an argument about algebra. The seed was reasoned
about and the summation order was not looked at at all.

### P2 — the real book is safe for a structural reason, and the null draws were not

`PositionResult.max_drawdown` seeded `peak = 1.0`, a peak the curve may never have reached:
`equity_curve` charges cost on bar 0 before any return, so `curve[0]` is `1.0 - charge*|position[0]|`.

On the **real book** this is a no-op, and for a stronger reason than the bound P2 offered. It is not
that the bar-0 term is small; it is that `position[0]` is **structurally never written** — both
constructors do `[0.0] * n` and then assign only `position[t + 1]`. So `curve[0]` is exactly `1.0`
and the two seeds coincide. Measured on `data/terrain_s6_imbalance_summary.json`: of 1,038 leaf
values, the only moves were four drawdowns at 1.11e-16 (P1's reordering) and the runtime field.

On a **null draw** it was live, and nothing in P2 anticipated this.
`terrain_field_nulls.rotation_null` rotates the position tuple, so `rotated[0]` is non-zero whenever
the book held at the rotation offset — and every such draw carried a spurious extra drawdown of
`cost_bps/1e4` from a peak it never reached. Nothing reads those drawdowns today (the field null
scores Sharpe, return and trade count), which is why this is a correction rather than a retraction.

### P3 — exact, and then the consumer nearly published the opposite verdict

`breakdown_study` published `percentile` as `(draws < observed).mean()` — strictly-below, 0–1 scale
— while three other sites published the same key mid-rank with ties at half weight on 0–100.
Collapsing onto mid-rank gave **0.507 → 50.7** and **0.955 → 95.5**, departure **0.000e+00**: no
ties, exactly as P3 said. Of 7,968 leaf values in the artifact, ten moved — those two and eight
drawdowns at ≤ 1.11e-16.

**Then the document.** `run_breakdown_study.py` rendered the value with `{:.0%}` and branched its
verdict on `>= 0.95`. The first re-run published:

> **Percentile vs the null: 5070%.** At the conventional 95% bar the strategy **beats** the null.

and replaced

> **The null verdict is SPLIT and must not be read as a pass.** ETH-USD clears the 95% bar; BTC-USD
> does not.

with *"The entry rule beats the exposure-matched null on every symbol tested … a genuine positive."*

**Nothing failed.** The producer was correct, every unit test passed, and the falsified verdict was
caught by diffing the rendered document against its predecessor, which is not a gate. It is one now:
`tests/unit/test_null_percentile_scale.py`, five gates, each verified to fire on the original defect
— the threshold literal the verdict branches on, a percentage above 100 rendered beside the word
*percentile*, the written verdict checked against the committed number, and the split reading pinned
by value. With the five consumers corrected, **the only change to `BREAKDOWN_RESULTS.md` is its
date**: the statistic changed units, the conclusion did not.

**A unit change is exactly the edit that looks safe in the producer and is wrong in the consumer.**

### P4 and P5 — the audit named a mechanism that does not exist, and the sign runs the other way

`scripts/fast_null.light_score` scored a zero-variance book `0.0` where `analytics.metrics.sharpe`
returns `sign(mu) × inf`. The review filed this against a memory note about degenerate cells beating
their null.

Measured before writing the pre-registration: **the two conventions agree whenever `mu == 0`**. An
all-flat rotation has `r == 0`, so `lf == sf == 0`, so `ex == 0` — both return `0.0`. The case the
review named is not affected at all.

The divergence needs a **constant non-zero** excess series, which needs a book that *holds* while
every held bar returns exactly zero — padded or halted bars, which these fixtures do carry. There
`ex == -lf·rf - sf·borrow`, a constant negative; the truth is `-inf` and the old branch said `0.0`.
That scores the null draw **too high**, which **deflates** the real book's percentile. **The defect
was conservative, not flattering** — the opposite of the claim it was filed under.

P4 is confirmed **analytically**, not end-to-end: no published percentile can move unless a draw hit
that constant-negative case, and confirming that by re-running the D256–D285 null family was not
done here. `assert_matches_scorer` compares with `!=` rather than a tolerance, so a real book that
ever goes degenerate now fails loudly instead of quietly inheriting either convention.

`scripts/fast_null.py` — the module CLAUDE.md says every runner must be built on — **had no test of
any kind** before this record. It has eight.

### P6 — falsified, and in the same direction as B26's

Predicted +1. Measured against the pre-registration commit `26e0d70`: the non-bare `raise` count in
`src/` went **284 → 288, a delta of +4** — three in `metrics.excess_sharpe` (length mismatch, too
few returns, unknown basis) and one in `PositionResult._check_bars`. The `parallel_map` guard I was
actually thinking of is in `scripts/`, which this count does not cover, so the one guard P6 named is
not even in the number P6 predicted.

B26 moved twice what was predicted (272 → 284, not 278); this moved four times. **Predicting a count
means counting the guards you are about to write and knowing which tree the gate measures. I
estimated, and I estimated the wrong tree.**

---

## What was found that no prediction covered

### `sum()` became compensated in CPython 3.12, and two ATR implementations diverged on it

`research/trade_diagnostics._atr` computed `sum(...) / window`;
`research/breakdown_study._atr_at` accumulated `total += ...` in a loop. Same terms, same order,
same plain (not Wilder) mean, same D44 window convention — and **380 of 13,760 probed (bars, window,
index) combinations disagree**, because **CPython 3.12 gave `sum()` Neumaier compensated summation
for floats** while a manual loop gets plain accumulation.

Neither docstring mentions it, because neither author could have: the difference arrived with the
interpreter, under code that had not changed. The compensated form is the more accurate, so the
delegation moves `worst_atr_multiples` and `median_atr_multiples` toward the true value. Measured:
on this fixture's twelve such values, **none moved** — at a 2.8% divergence rate that is chance, not
a guarantee, and it is recorded as chance.

**This is a repository-wide class.** Any optimisation replacing `sum(xs)` with a loop, or the
reverse, moves numbers. CLAUDE.md's rule against reordering a float sum now has a second edge that
nobody had written down. Pinned in `tests/unit/test_metrics.py` against the interpreter, not against
the ATR functions, so it fails if the property ever goes away.

### Two tracked `data/*.json` files are saved HTTP 429 error pages

`data/D3_wb_2018.json` and `data/D3_wb_2019.json` are 117 bytes each and contain
`<html><body><h1>429 Too Many Requests</h1>`. Nothing in the tree reads them. Found because they
would not parse during the artifact census. **A tracked JSON that does not parse should fail a
test**, and none does. Handed to the principal rather than deleted — `data/` is evidence, and
retirement is written, not quiet.

### `PositionResult`'s dead `bars` parameter could not simply be deleted

The review filed it as D48's false affordance and prescribed deletion. Deletion breaks
`tests/unit/test_terrain_field.py`, which pins the two result classes as drop-in substitutes and
calls both as `curve_sharpe_zero_rf(bars, 365.0)`; `StrategyResult` genuinely needs `bars`.

Resolved by making the parameter honest rather than absent: `_check_bars` raises when the supplied
bars could not describe this book. **A parameter that is checked is not a false affordance**, and
this is a guard the class did not have — passing the wrong book's bars was previously absorbed in
silence.

---

## The conventions, as they now stand

| quantity | canonical | where the other convention lives |
|---|---|---|
| `max_drawdown` | `analytics.metrics.max_drawdown`, **positive** fraction of peak | `research/terrain_strategies` publishes it **negative**, via one negation at the emit boundary |
| return-series drawdown | `analytics.metrics.max_drawdown_from_returns` | the vectorised hot path in `breakout_nulls`, pinned bit-exact |
| Sharpe, rf = 0 | `analytics.metrics.curve_sharpe_zero_rf` | — (three inline copies collapsed) |
| Sharpe, rf charged | `analytics.metrics.excess_sharpe`, on the **exposed fraction** | — (two `scripts/` copies collapsed) |
| null percentile | `analytics.metrics.mid_rank_percentile`, mid-rank, **0–100** | — (four sites collapsed) |

**83 tracked artifacts now carry a `max_drawdown_convention` field** stating their own sign, spliced
in textually so not one other byte moved — verified file by file against `HEAD`, zero value
mismatches, zero mixed line endings. The marker is **re-derived from the values it describes**, so
`scripts/label_drawdown_convention.py --check` fails on a marker that has drifted rather than only
on one that is absent, and the gate has a floor of 70 so it cannot pass on an empty scan.

### Two kernels, kept deliberately

`curve_sharpe_zero_rf` uses `statistics.fmean` / `statistics.stdev` (exact summation);
`metrics.sharpe` uses numpy (pairwise). **200 of 303 probed series disagree**, worst 3.7e-13
relative. Repointing the research call sites at `sharpe` would move every Sharpe in
`TERRAIN_RESULTS`, `STRUCTURE_RESULTS` and eight committed summaries for no gain. **The collapse is
one function, not one kernel**, and the two are named, measured and pinned against each other rather
than left to be discovered. The pin is an anti-tautology: if they ever agree everywhere, it fails
and this record needs amending.

---

## D219's ruling is implemented

D219 wrote *"Both conventions are therefore reported, rf = 0 and rf = 0.04, and switching silently
is forbidden"* — and stayed **Pre-registered**, propagated to no call site, for the life of the
programme. Every terrain and structure emitter now writes `excess_sharpe`, `rf_annual` and a
`sharpe_convention` string beside its `sharpe`. The ruling is a field in the file rather than a
paragraph in a record.

**It is not decorative.** On `data/terrain_s6_imbalance_summary.json` the charge lowers every cell
by 0.013 to 0.059 — D219's predicted magnitude for a partly-exposed book at rf = 4% — and one cell
changes sign: `ETH-USD|erased|stop` goes **+0.0107 → −0.0186** once the cash it holds is charged for
being cash.

**Reading the existing verdicts under the new column is not done here and is not implied.** D219
records that the correction is not uniform across arms — a 50%-exposure long-flat book is charged
~0.5 × rf while its buy-and-hold baseline is charged 1 × rf — so an arm and its benchmark move by
different amounts and a verdict can flip either way. That is a separate exercise with its own
pre-registration. This record guarantees only that the column exists, is computed by the runner, and
is labelled.

---

## Handed to the principal, not decided

1. **`src/backtest_framework/research/terrain_swing_decay.py`** — 414 lines, imported only by its
   own 573-line test, zero references anywhere in `scripts/`. Either a line naming its study, or
   retirement in writing.
2. **`data/D3_wb_2018.json` / `D3_wb_2019.json`** — the two saved error pages above.

## What this record does not settle

Whether any published verdict changes under the rf = 4% column; whether the `light_score` correction
moves a percentile in the D256–D285 null family; and whether the two paired block bootstraps should
be merged — they share their raise messages verbatim but draw from `rng` in different orders, so a
shared helper moves every seeded result in `data/breakout_study_summary.json` unless it reproduces
each caller's draw order exactly. The gain is deduplication and the risk is a silently moved
published number, so the contract is stated in both docstrings instead.
