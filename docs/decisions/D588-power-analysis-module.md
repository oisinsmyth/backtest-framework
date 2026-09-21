# D588 — The deposit documents' power arithmetic is one library module with a self-testing renderer, not five copies of a formula block

**Status:** Committed
**Date:** 2026-09-21
**Category:** Testing
**Source:** The five `docs/internal/User-Doc-Deposit` pre-registrations each carry
the same power block: ledger §9A (formulas, planning table, rules 1–5), §9B (the
route an underpowered participant takes instead), §13A.7 (power across the three
tracks), unit tests 51–63; `LETF_CLOSE_FLOW_PREREG.md` §6A/§6B;
`SHOCK_CLASSIFIER_PREREG.md` §7A/§7B; `INDEX_REWEIGHT_FLOW_PREREG.md` §8B.1;
`OPENING_AGENT_STATE_PREREG.md` §10. Extends D20/D21/D86 (the DSR module, whose
house style this matches) and D78/D537 (property-test conventions). The deposit
list itself was closed by the principal on 2026-09-21 (D582); this record adds no
claim about any hypothesis in it.

## Decision

`src/backtest_framework/validation/power.py` implements the pre-registered
planning arithmetic once, stdlib plus numpy, in `validation/dsr.py`'s style:
every function documents its units and the deposit section it implements, and
every guard raises rather than returning a sentinel.

**Public API** (units in the docstrings, repeated here because the units are the
point):

| Function | Returns | Units |
|---|---|---|
| `design_effect(m, rho)` | `1 + (m-1)*rho` | dimensionless |
| `n_eff(n, m, rho)` | `n / design_effect` | observations |
| `icc_from_clusters(values, cluster_ids=None)` | one-way ANOVA ICC(1,1), n0-corrected | dimensionless |
| `n_eff_from_clusters(values, cluster_ids=None)` | `n_eff` at m = mean cluster size | observations |
| `n_eff_cross_series(panel, start, min_overlap=250)` | `1/(w'Rw)` at equal weights | a count of independent instruments |
| `se_correlation(n_eff)` | `1/sqrt(n_eff)` | dimensionless |
| `se_mean(sigma, n_eff)` | `sigma/sqrt(n_eff)` | sigma's own units |
| `mde(se, t=2.0)` / `mde_80(se)` | `t*se` / `2.8*se` | se's units |
| `power_class(mde, plausible)` | `"individually_testable"` \| `"underpowered"` | — |
| `forward_evaluation_days(plausible, instruments, floor=120, cap=500)` | `ForwardPlan(n_needed, evaluation_days, route)` | observations; trading days |
| `track3_route(edge_sigma, n=300)` | `Track3Route(se, mde, route)` | multiples of sigma |
| `PowerRow` / `power_row(...)` / `validate_track_map(rows)` / `write_power_md(rows, path)` | the `POWER.md` / `TRACK_MAP.md` line and its renderer | — |

`scripts/power_table.py --spec spec.json --out POWER.md` renders a table from a
JSON list of row inputs; `--selftest` runs the six named ledger unit tests, the
ICC recovery, the cross-series parity check, and twenty-two guards each shown
raising.

Seven choices inside that are decisions rather than transcription:

1. **Two unit regimes, carried on the row.** `sigma=None` means correlation
   units; a positive `sigma` means multiples of sigma. `PowerRow.units` prints in
   the table. The docs mix "0.040 corr" and "0.05σ" in adjacent rows of one table
   and nothing in the prose stops a plausible-effect statement in one unit being
   compared with an MDE in the other.
2. **`n_eff` refuses a zero design effect.** `rho` exactly at its floor
   `-1/(m-1)` is inside the interval the brief specifies and makes the divisor 0.
   `n/0` would read on a page as infinite power, so `n_eff` raises there while
   `design_effect` still returns the 0 it is defined to return.
3. **The ICC is not clamped at zero.** A negative ANOVA ICC is a real finding;
   clamping would silently inflate the design effect and overstate power.
4. **`icc_from_clusters` accepts a grouped input form so its empty-cluster guard
   can fire.** In the flat `(values, cluster_ids)` encoding an empty cluster is
   unrepresentable — a label with no observations is a label that is not in the
   array — so a guard written against that form alone could never run, and
   CLAUDE.md is explicit that a self-test which cannot fail is worse than none.
   Passing `[[1.0, 2.0], [], [3.0, 4.0]]` is how a caller actually loses a
   cluster, and that raises.
5. **`n_eff_cross_series` is a bit-for-bit port of
   `scripts/ragged_panel.py:effective_instruments`, not an import of it.** The
   library does not import research scripts. The loop, the `min_overlap` gate and
   the zero-standard-deviation skip are reproduced unchanged, and
   `tests/unit/test_power.py` asserts the two are equal — not approximately, but
   `==` — on a synthetic ragged panel at three `min_overlap` values and two start
   offsets.
6. **The cap in §13A.7(2) is applied to `evaluation_days`, not to `n_needed`.**
   The doc's prose says "if `n_needed` would exceed the cap" while its formula
   line caps the day count; the two agree on both cases in unit test 59 and
   diverge for a large instrument count. The formula line wins, because the cap is
   stated in trading days and because more instruments genuinely do shorten the
   calendar. Recorded in the docstring rather than silently chosen.
7. **`write_power_md` takes an explicit path and does not know about `results/`.**
   The docs specify `results/<study>/POWER.md`; no `results/` tree exists in this
   repository. A directory convention does not belong inside a library function,
   and inventing one here would commit the repo to a layout no record has taken.

`validation/__init__.py` is empty and re-exports nothing, so it is left alone:
`power` is imported by its full path, as `dsr` is.

## Rationale

**One implementation, because five copies of a formula block is five chances to
disagree.** The five deposit documents repeat the §9A formulas verbatim and then
each quote their own planned SEs and MDEs. Those quoted numbers are the only
cross-check that exists, and the golden ledger uses them as such: the LETF §6A
table's "~0.045σ / ~0.09σ" at n_eff 500 and "~0.026σ / ~0.05σ" at 1,500 are
asserted against the exact values alongside the doc's own rounding, so a change
that stays internally consistent but drifts from the published table still fails.

**The golden pair found something the docs do not say.** LETF §6A quotes H1's
n_eff as one cell, "~500–1,500". Against the declared 0.06σ round-trip cost the
two ends of that single range land on opposite sides of §9A.2 rule 3: at n_eff
500 the MDE is 0.0894σ and adoption by significance is **blocked**; at 1,500 it is
0.0516σ and permitted. The planning range is not a presentational detail — it
decides whether the primary cell may be adopted on its own significance test at
all. `test_case_2b_one_planned_range_straddles_the_adoption_rule` holds that.

**`adoption_by_significance_blocked` blocks in the safe direction.** It is True
unless the row is classed `individually_testable`, so a row with no
plausible-effect statement — one §13A.2 says must exist before the stage runs — is
blocked too. The cost of a wrong True is a §9B validation that was not strictly
required; the cost of a wrong False is adopting an underpowered stage on a
significance test, which is exactly what rule 3 forbids.

**`validate_track_map` names the cause, not the symptom.** It checks
`plausible_effect` before `power_class`, because a row with no statement also has
no class, and reporting the missing class first would send the reader to rule 3
when the failure is rule 2.

**2.8 is used exactly, and the true constant is recorded beside it.**
z(0.975) + z(0.80) = 2.801585218112969, but the docs pre-register 2.8 and unit
test 52 pins the value 2.8 produces (n_eff 2,500 → MDE_80 = 0.056). Substituting
the exact sum would be a 0.6% silent amendment to a pre-registration.
`Z80_TWO_SIDED` and `Z80_TWO_SIDED_EXACT` are both exported and both asserted.

**The property tests check the relations the docs reason with but never write
down** (D78 conventions, D537's amendment about example determinism): clustering
can only cost sample; the design effect is monotone in rho; MDE_80/MDE_t2 is
always 1.4, so quoting MDE_t2 as a powered number understates the required effect
by 40%; four times the sample halves the MDE, which is why §13A.7(2)'s `n_needed`
is a square; the ICC is invariant to shifting, scaling and relabelling; routing is
a step function with the boundary on the documented side.

## Consequences

- 78 tests: 53 unit (`tests/unit/test_power.py`, parametrised), 7 golden
  (`tests/golden/test_power_ledger.py`, hand arithmetic in the paired
  `.hand.txt`), 18 property (`tests/property/test_power_property.py`). Six unit
  tests carry a deposit unit-test number in the function name — 51, 52, 53, 59,
  62, 63 — so a reader goes from the doc's numbered requirement to its test
  without a search. `uv run ruff check` and `uv run mypy` are clean on all five
  files; the whole set runs in about 1.4 s.
- `scripts/power_table.py --selftest` is itself a unit test
  (`test_the_script_selftest_runs_clean`), so a change to the module cannot leave
  the script's audit stale and unnoticed.
- **Nothing here is evidence about any hypothesis.** The module computes no
  strategy return and reads no market fixture. §9A.1's own sentence — that these
  are estimates "recomputed on real data before each stage runs" — is stamped into
  every file `write_power_md` produces, and the writer refuses to emit an
  incomplete table at all.
- The deposit list is closed (D582). This module is the reusable part of it: any
  future pre-registration that states an n_eff, an SE and an MDE can compute them
  here rather than in prose, and `power_class` makes "underpowered" a value the
  runner carries rather than a sentence in a write-up.
- Not implemented, and deliberately: the §9A.2 rule 4 marginal-contribution
  regression and its VIF flag (unit test 54), and the §9B toolkit — parameter
  recovery, decision relevance, hierarchical pooling, calibration (tests 55–58).
  Those need a regression and a simulator, not planning arithmetic, and belong
  with whichever study runs them.
