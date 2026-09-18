# D542 — One quantity, one definition: collapsing `max_drawdown`, Sharpe and percentile

**Status:** Pre-registered
**Date:** 2026-09-18
**Category:** Research infrastructure
**Source:** Lane 6 of the two-reviewer audit (`working/REVIEW_REMEDIATION_PLAN.md` §7, items
B21–B25, B27, B28). Predictions below are committed before any code is changed (R8).

## The problem

The repository publishes **two answers to the same question** for three quantities, and the
duplication reaches committed `data/*.json` artifacts and the documents rendered from them.

- **`max_drawdown` has seven implementations.** `max_drawdown` (`analytics/metrics.py:207`) returns a **positive**
  fraction of peak; `research/terrain_strategies.py:195`, `:787`, and an undeclared seventh inside
  `buy_and_hold()` at `:464` return **negative**. Census over tracked `data/*.json`: **~1,800
  negative values in 55 files** against **~1,200 positive in 15**. The two negative *methods* also
  disagree with each other on the peak seed — `curve[0]` at `:195` against a phantom `1.0` at
  `:787` — and `:464` has no `peak > 0` guard at all.
- **Sharpe has two conventions and the gap exceeds the hurdle.** `metrics.sharpe` makes
  `rf_annual` required and says why (D49: "a default rf=0 is exactly the silent shortcut D49
  exists to kill"). Both `curve_sharpe` copies, and the inlined copy in `buy_and_hold`, have no rf
  term and no way to supply one. D228 measured the same book at **+0.792** zero-rf and **+0.566**
  at rf = 4%; **+0.793** is the published MACD headline. The gap runs **0.14–0.41** across books
  against the **+0.10** hurdle TERRAIN/STRUCTURE pass cells on.
- **`percentile` names two different statistics in two different units.**
  `research/breakdown_study.py:658` emits `(draws < observed).mean()` — strictly-below, 0–1 scale.
  `breakout_nulls.py:438`, `terrain_strategies.py:390` and `terrain_field_nulls.py:129` emit
  mid-rank with ties at half weight, 0–100 scale. Both are committed; a reader diffing
  `breakdown_study_summary.json` against `terrain_strategy_summary.json` has no way to know the
  key means two different things.

## Decision

**One arithmetic per quantity. The convention is declared in the artifact, by the generator that
wrote it.** Specifically:

1. **`max_drawdown`: `analytics.metrics.max_drawdown` is canonical** — positive fraction of peak.
   It is the only one of the seven that refuses a never-above-water curve, and the only one tied to
   an external reference (`tests/unit/test_quantstats_xgate.py:49`). The three negative sites keep
   their **display** sign, applied **once, at the emit boundary**, over a delegated call. The
   artifacts are **not rewritten**; each gains a `max_drawdown_convention` field written by its own
   generator, so the marker cannot drift from the number it describes.
2. **Sharpe: one implementation, two columns.** The zero-rf log form collapses to
   `metrics.sharpe(rets, 0.0, ppy)` and is **renamed `curve_sharpe_zero_rf`**, so the omission is
   visible at the call site rather than buried in the body. `excess_sharpe` — which already exists
   twice in `scripts/`, with rf charged on the **exposed fraction** (D228 Part 1, fact 2) — is
   promoted to `analytics/metrics.py` and emitted **beside** the zero-rf number. This implements
   D219's ruling ("both conventions are therefore reported… switching silently is forbidden"),
   which has been pre-registered and unenforced since it was written.
3. **`percentile`: mid-rank, ties at half weight, 0–100 is canonical.** It is the one with a
   stated rationale, and three of the four sites already use it. `breakdown_study.py:658` is
   re-derived onto it. This moves a published number, which is the point: the two answers already
   disagree, so one of them was already wrong.

## Predictions, committed before the runner exists

Each is written in the runner's own quantities and is checked by re-running the emitter and
diffing every pre-existing JSON key byte-for-byte.

| # | Prediction | Confidence |
|---|---|---|
| **P1** | Collapsing `StrategyResult.max_drawdown` (`:195`) and `buy_and_hold` (`:464`) onto `metrics.max_drawdown` moves **zero** stored values in `terrain_s6_summary.json`, `terrain_s6_confirm_summary.json`, `terrain_s6_exits_summary.json`. Both already seed the peak at `curve[0]`, which is what `metrics`' `-inf` seed reduces to. | High |
| **P2** | Collapsing `PositionResult.max_drawdown` (`:787`) moves **zero** stored values, because `position[0] == 0.0` in every emitter, so `curve[0] == 1.0` and the phantom seed is a no-op. **If any value moves it moves by ≤ `cost_bps/1e4` (0.004 at the 40 bp tier) and becomes strictly *less* negative** — a phantom peak can only deepen a drawdown, never shallow it. The direction is the falsifiable half. | Medium |
| **P3** | `breakdown_study`'s `percentile` values become **exactly 100× their current values** to within 1e-9 (`0.507 → 50.7…`, `0.955 → 95.5…`). Mid-rank differs from strictly-below only by the tie term, and Sharpe draws off a continuous bootstrap should tie with probability ~0. **A departure from 100× means there are ties in the draws**, which would itself be the finding — a discrete statistic where a continuous one was assumed. | High |
| **P4** | Aligning `light_score` to `metrics.sharpe` on the zero-variance branch moves **zero** published null percentiles. Measured before writing this: the two disagree **only** when the excess series is constant *and* non-zero. An all-flat rotation gives `ex ≡ 0`, `mu = 0`, and **both return `0.0`** — so the mechanism named in the review does not exist. | High |
| **P5** | Where P4's divergence *is* reachable — a rotation landing entirely on bars with zero price change, giving `ex ≡ −lf·rf − sf·borrow`, a constant **negative** — the current code scores that draw `0.0` where the correct value is `−inf`. That scores the null draw **too high**, which **deflates** the real book's percentile. The defect is **conservative, not flattering**, which is the opposite of the review's claim. | High |
| **P6** | The `raise`-guard count moves **+1** (a duplicate-key guard in `parallel_map`) and the module count moves **0**. No new module is created; `metrics.max_drawdown_from_returns` and `metrics.excess_sharpe` land in an existing one. | Medium |

P2, P3 and P5 are the ones to watch: each has a falsifiable *direction*, not just a magnitude.

## What is deliberately not done

- **The two `curve_sharpe` copies are not merged into one class.** `PositionResult.hit_rate` counts
  held bars and `StrategyResult.hit_rate` counts trades; both publish as `real_hit_rate`. Merging
  would move a published number for no stated reason.
- **The nearest-rank `q → value` copies are not re-pointed at `terrain._quantile`** (linear), and
  `_quantile` is not re-pointed at nearest-rank. The first moves every `p10/p25/p75/p90` in three
  summaries (up to 16.7% of range at p50); the second sits upstream of HVN/LVN level detection and
  would move everything terrain. They are collapsed only onto each other, which moves nothing.
- **The two paired block bootstraps are not merged.** They draw from `rng` in different orders
  (vectorised `(size, n_blocks)` per chunk against scalar `n_blocks` per sim), so a shared helper
  moves every seeded result in `breakout_study_summary.json` unless it reproduces each caller's
  draw order exactly. The gain is deduplication; the risk is a silently moved published number.
  A test asserting both produce identical index sets for matched draw counts records the shared
  contract without taking the risk.
- **`terrain_swing_decay.py`** (414 lines, imported only by its own test, zero `scripts/`
  references) is flagged, not retired. Retirement is a decision only the principal makes.
- **`data/terrain_strategy_summary.json` has no producer left in the tree** — last touched by
  `eda5d1f`, and `bh_max_drawdown` appears in no `.py` file anywhere. It cannot receive a
  generator-written convention marker. It gets a written provenance stanza naming the deleted
  runner and that commit, rather than silence.

## Claims from the review that this record falsifies

Filed here because a review claim tested is worth more than a review claim acted on.

1. **"`percentile` ×4 in two conventions that already disagree — and a null's percentile is a
   published number."** The four `q → value` implementations never reach a null bound. Every
   published p05/p50/p95 in the repository goes through `np.percentile`, uniformly. The real
   disagreement is elsewhere (`breakdown_study.py:658`) and the review did not name it.
2. **"`max_drawdown` ×6."** There are seven; the seventh is inlined in `buy_and_hold` and is the
   one that writes the `**buy and hold**` row of `STRUCTURE_RESULTS.md`.
3. **"`run_structure_pnl.py:155,161,168` writes `StrategyResult.max_drawdown` (`:195`)."** It writes
   `PositionResult.max_drawdown` (`:787`). The review had the published and the internal
   implementations the wrong way round: `:195` reaches committed JSON but **no published figure**
   (`TERRAIN_RESULTS.md` contains no drawdown at all), while `:787` reaches
   `STRUCTURE_RESULTS.md` lines 660–684.
4. **"`light_score` scores a zero-variance book `0.0` … against a memory note about degenerate
   cells beating their null."** The divergence requires a constant *non-zero* excess series; the
   degenerate case the note describes agrees exactly. Where the divergence is reachable it runs
   the other way — see P5.
5. **"paired bootstrap ×4."** Two duplicates and two distinct statistics:
   `structure_nulls.paired_bootstrap` is i.i.d. over setups (correctly unblocked, and its docstring
   says so) and `breakdown_study.random_entry_null` is not a bootstrap.
6. **"`parallel_map` drops same-key results (`fast_null.py:224`)."** The drop is at `:243`. The
   defect is real: `done` still counts to `len(items)`, so the progress line reports N while the
   returned dict holds fewer.

## What this record does not settle

Whether the rf = 4% column *changes any verdict*. It will not move a single stored number — that is
enforced, not hoped — but it puts a second number beside every headline Sharpe in the TERRAIN and
STRUCTURE programmes, and D219 already records that the correction is **not uniform across arms**
(a 50%-exposure long-flat book is charged ~0.5 × rf while its buy-and-hold baseline is charged
1 × rf, so the arm and its benchmark move by different amounts and a verdict can flip either way).
Reading those verdicts under the new column is a separate exercise with its own pre-registration.
This record only guarantees the column exists, is computed by the runner, and is labelled.
