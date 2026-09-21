# D592 — The programme's α registry, trial counter and episode checks are library code with one state file, and the deposit's `results/PROGRAMME_REGISTRY.md` maps to `docs/results/` plus `data/`

**Status:** Committed
**Date:** 2026-09-21
**Category:** Testing
**Source:** The deposit's programme-level false-positive controls, written identically in
[`SETTLEMENT_FLOW_LEDGER_PREREG.md`](../internal/User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md)
§13A.8 (v1.9) and
[`OPENING_AGENT_STATE_PREREG.md`](../internal/User-Doc-Deposit/OPENING_AGENT_STATE_PREREG.md)
§12A (v1.1), with the ledger's unit tests 66–69 as the acceptance bar. Extends
[D20](D20-trialregistry-every-backtest-run-appends-config.md) (the trial registry),
[D90](D90-study-dsr-methodology.md) and [D98](D98-dsr-units-and-trial-pool.md) (DSR units
and pool semantics), [D588](D588-power-analysis-module.md) (the sibling module, and the
precedent for declining to invent a `results/` tree), and D504's `concentration_usable`
block, which `episodes.symmetric_trim` ports. Governed by
[R16](../RULES.md) on reproducing a published number and
[D78](D78-property-test-conventions.md)/[D537](D537-derandomize-does-not-mean-deterministic.md)
on property-test conventions.

## Decision

Four of the deposit's seven programme-level controls become library code, in two modules,
one state file, one rendered page and one CLI.

**1. `src/backtest_framework/validation/programme.py`** — controls 2, 3 and 4.

| Object | Signature | Units |
|---|---|---|
| `Family` | `Family(name, doc, registered_utc, slot, alpha=0.005, amendment=None, note="")` | `alpha` a probability; `slot` 1-based |
| `Registry` | `Registry(path=data/programme_registry.json)`; `.register(name, doc, *, amendment=None, registered_utc=SEALED_DATE, note="")`; `.promotion_check(name, adjusted_p) -> bool`; `.render_md(path=docs/results/PROGRAMME_REGISTRY.md, date=None)`; `.free_slots()`, `.alpha_total()`, `.get()`, `.save()` | α = 0.05 over 10 slots of 0.005 |
| `seed_registry` | `seed_registry(path) -> Registry` — idempotent | — |
| `TrialsCsv` | `TrialsCsv(path)`; `.append(row) -> dict`; `.rows()`; `.count() -> int`; `.trial_ids()`; `.columns` | rows |
| `programme_trial_count` | `(census=data/trial_registries.json, trials_csv_glob="data/**/trials.csv", repo=REPO) -> {etf_pool_distinct_configs, other_registries, trials_csv_rows, total, rule}` | counts of trials |
| `programme_dsr` | `(sr, t, skew, kurt, *, n_doc, n_programme, var_trials) -> {dsr_doc, dsr_programme}` | `sr`, `var_trials` **per-period**; `kurt` raw; outputs probabilities |
| `haircut` | `(edge, frac=0.5, vault_estimate=None) -> float` | the caller's own units, both arguments |

**2. `src/backtest_framework/validation/episodes.py`** — control 5, on daily P&L **in
dollars** with dates: `sharpe_daily_usd`, `sessions_to_half_pnl`, `symmetric_trim(usd,
frac=0.01)`, `drop_best_year(usd, dates)`, `drop_best_days(usd, frac=0.01)`,
`shared_period(a, b, dates)`, `episode_checks(usd, dates, frac=0.01)`.

**3. `scripts/programme_registry.py --render | --count | --selftest`**, and the two
artefacts `--render` writes: `data/programme_registry.json` (state) and
`docs/results/PROGRAMME_REGISTRY.md` (page), seeded with the seven families the two docs
name — LETF close flow H1, shock classifier H1, ledger H2, index H-R1, H-R2, H-R3(b),
opening H-O2 — registered 2026-09-21 in slots 1–7, with 8–10 reserved.

**The path mapping, which is the one thing the deposit could not decide for this
repository.** The deposit names `results/PROGRAMME_REGISTRY.md`. **There is no root
`results/` directory here.** It maps to:

* **`docs/results/PROGRAMME_REGISTRY.md`** — the rendered page. `docs/results/` is this
  repository's prose-results home (30-odd `*_RESULTS.md` pages).
* **`data/programme_registry.json`** — the machine-readable state. `data/` is the artefact
  home.

The page is rendered from the JSON and is never the source of truth: **a markdown table
cannot refuse an eleventh slot.** D588 hit the same fork for `results/<study>/POWER.md`
and declined to invent a tree inside a library function; this record makes the mapping
explicit instead of leaving it to each caller.

**The programme trial count is 83,074 today, and the rule has two clauses**, because two
kinds of evidence are counted two ways:

* **sqlite registries → distinct, de-duplicated config payloads.** The predicate is
  `scripts/run_macd_ladder.py:729-745 prior_etf_trials()` — *distinct logged config
  payload, de-duplicated across registries* — because one window re-run at a scaled cost
  multiplier is a sensitivity point, not an independent trial (D98). ETF-fixture pool:
  **45,346** (raw rows 129,286; the per-registry column sums to 97,966, about 2.2× the
  pool). Live non-pool registries, the breakout/crypto line: **37,728**, at their
  per-registry distinct-config counts, with no cross-registry de-duplication ever
  measured, so that term is an upper bound and is reported separately. The superseded
  `breakout_study` copy and the 10-row demo registry are excluded.
* **`trials.csv` → rows**, because the deposit says rows and because a row there *is* a
  configuration. **That term is 0: no `trials.csv` exists anywhere in the tree, and no
  futures runner logs a trial to any registry.** A test asserts the zero, so the day one
  appears the record stops being true out loud.

**`programme_dsr` refuses `|sr| > 1.0` per period, citing D98 by name in the message.** A
per-period Sharpe of 1.0 is 15.9 annualised on daily data; nothing here has produced one.
The refusal is the cheap form of the audit's one red finding — an annualised `sr` against
a per-period `var_trials` inflates SR₀ by √252 and forces the DSR to zero for any strategy
at all. It also refuses `n_programme < n_doc`, because the programme pool contains the
doc's own trials by construction.

**`symmetric_trim` is a port of D504's `concentration_usable` block with one
generalisation and one documented divergence.** The generalisation: `k = max(1, int(n *
frac))` replaces `max(1, len(srt) // 100)`, and the two are equal for every n from 1 to
200,000 at `frac = 0.01` (asserted exhaustively). The divergence: on a **negative** total
D504's loop returns `sessions_to_half_pnl = 1`, because a running sum clears a negative
threshold at the first session; the port returns `None`, and `sessions_to_half_pnl` raises.
D504 ran on +$25,697.0565, so its published block is unaffected.

**`shared_period`'s "same months" is an operationalisation, and the docs do not give one.**
§13A.8(5) says to flag when *"more than 40% of each model's P&L comes from the same
months"* without saying which months those are. The definition chosen: a model's **episode
months** are the fewest months, best-first, carrying half its P&L (the same 50% the rest of
the module uses); the shared months are the intersection of the two models' sets; the
shares are each model's P&L in that intersection over its total. Deterministic, no new
tuning constant, and stated rather than assumed. A model with a non-positive total has no
episode months — the flag is about shared *winners*.

**`episode_checks` returns numbers and one boolean, never a verdict.** The boolean,
`edge_positive_after_both`, is the doc's stated condition and nothing more. The symmetric
trim travels inside the same dict as the one-sided drop, so neither can be quoted alone.

## Rationale

**The R16 problem, and what was done instead of widening a tolerance.** The brief asked
the golden ledger to reproduce `data/d504_arm_full_history.json::concentration_usable`
"from the stored series if it is in the JSON, else from D504's own input path". **Neither
route is available, and checking the stored window first is what revealed it.** The JSON
publishes the block and the per-year table but **not** the daily series. And D504's
`_usable` window is not an in-sample window: `spec.usable_start` is 2016-01-04,
`spec.span` ends 2026-09-09, `usable_years` runs `['2016' … '2026']`, and
`overall_usable.n_sessions` is 2,508 — so re-deriving the series would read 2024+ fixture
rows from a slice D503 already spent. R16 clause 4 says a failing identity check is
evidence, not an inconvenience. So the golden asserts three things instead, all of them
exact and none of them reading a bar:

1. **Code identity, the strong check.** The block's *source text* is extracted from
   `scripts/d504_arm_full_history.py` by its own marker comment, `exec`'d on a synthetic
   series at n ∈ {137, 250, 2508}, and compared with `symmetric_trim` key for key and bit
   for bit. This is strictly stronger than a stored number: if either implementation moves,
   the test fails.
2. **Arithmetic identities on the published block, with `==` and no tolerance.**
   `share_ex_both_1pct == pnl_ex_both_1pct_usd / total_usd` → `23563.84450000082 /
   25697.056500001505 = 0.9169861341900946`, exact; `top1 == best_day_usd / total_usd` →
   `2657.4955 / 25697.056500001505 = 0.10341633875459022`, exact; `n_trimmed_each_side ==
   max(1, 2508 // 100) = 25`, exact.
3. **A fourth relation that is *not* exact, recorded rather than smoothed.**
   `1 − top1pct − bottom1pct = 0.9169861341900951` against the published
   `0.9169861341900946` — 5 ulp, three roundings against one. It is float noise at 1e-16
   and it is written down so nobody quotes it as an identity.

**Why the trial counter carries more than the deposit's own definition.** §13A.8(3) says
the counter *"sums the rows of every doc's `trials.csv`"*, which is zero today. D90's whole
argument is that a trial count cannot be reconstructed retroactively — so the counts that
*were* captured live are carried beside it, under a rule string that says exactly what each
term is and why the two are counted differently. A DSR on a shared fixture ought to see the
45,346 configurations already spent on it; a reader who wants only the deposit's literal
number reads `trials_csv_rows`.

**Why `Registry` is a state file and not an append-only book.** `docs/BOOK.md` and
`docs/COMPONENTS_PROP.md` are append-only because a retired entry must keep its text. A
registry has to answer *which slots are free* on every call, which a markdown table cannot
do. The property the append-only books protect is kept where it matters: `register`
refuses to re-register a name and refuses to move a slot, because §13A.8(2) forbids
re-allocating α retroactively for a family already evaluated, and a silent overwrite is
exactly that.

**Why the eleventh slot takes a string and not a flag.** `amendment` is the doc amendment's
text, it goes into the record and onto the page, and a whitespace-only string is refused.
An amendment offered while a slot is still free is *also* refused: the door §13A.8(2)
leaves open is for the eleventh family, not a way to skip the three reserved slots.

**Why `episode_checks` reports rather than judges.** CLAUDE.md §2 is explicit that a
one-sided trim *"is a flag, not a verdict"*, and D307 called four cells lottery books on
one before the symmetric trim came back +24 to +52 bp. D504's own published block has
`top1pct = 0.982` against `bottom1pct = −0.899` for the same reason. A function that
returned PASS on the best-1% removal alone would be the D307 mistake in library form.

**The self-test proves every raise.** CLAUDE.md: *"a self-test that cannot fail is worse
than none."* `--selftest` runs 30 checks and drives every guard onto the input it exists to
refuse — the eleventh slot, the duplicate `trial_id`, the annualised Sharpe (1.2699 = 0.08
× √252), `n_programme < n_doc`, unsorted dates, a non-finite P&L, a negative total, a
missing census — using the `expect_raise` idiom of `scripts/stage0_d581_gamma_close.py:39`.

## Consequences

* **Four of seven programme controls now exist as code.** Controls 1 (the sealed vault),
  6 (one-bar-delay robustness and the leak canary) and 7 (the consistency route's vault
  dependency) do not, and the rendered page says so in a table rather than leaving the
  omission to be inferred. Each is a property of a loader or a runner that does not exist.
* **`data/programme_registry.json` and `docs/results/PROGRAMME_REGISTRY.md` are now the
  repository's answer to `results/PROGRAMME_REGISTRY.md`.** Any doc that quotes that path
  means these two files. Re-running `--render` is idempotent and cannot move an allocated
  slot.
* **The programme trial count is a number a future runner must pass to
  `programme_dsr`, not one it may type.** It is 83,074 today and it rises the moment a
  `trials.csv` appears.
* **A future `trials.csv` must use `TRIALS_COLUMNS`**, the union of the four documents'
  schemas plus `doc` and `family`. The four share only `trial_id`, `timestamp`,
  `cost_mult`, `mean_gross`, `mean_net` and `notes`, so a pooled file without provenance
  columns could not be split back into its documents. A drifted header is refused rather
  than pooled, and the newline is pinned to `\n` (D550).
* **Nothing is admitted and nothing is scored.** No strategy return was computed, no bar
  from 2024-01-01 on was read, no fixture was opened, and no `.sqlite` was opened at all —
  the counter reads the committed census. `validation/__init__.py` stays empty.
* **Test counts:** 19 golden, 32 unit (`test_programme.py`), 26 unit (`test_episodes.py`),
  16 property — 93 in all, plus the CLI's 30 self-test checks. `uv run ruff check` and
  `uv run mypy` are clean on the five new files (the two `F601` findings ruff reports are
  pre-existing, in `scripts/stage0_d575_livestock_placements.py`, and are untouched here).
