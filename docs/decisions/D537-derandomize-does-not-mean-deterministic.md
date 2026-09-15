# D537 — `derandomize=True` does not mean the same examples twice, and six files said it did

**Status:** Committed
**Date:** 2026-09-15
**Category:** Testing
**Source:** Portfolio repack session, out of the one-ulp gap fixed in `9a8f938`. Amends
[D78](D78-property-test-conventions.md)'s determinism claim. **[D34](D34-explicit-rng-seed-policy-every-stochastic.md)'s
requirement is unchanged** — what changes is the belief that hypothesis discharged it.

## Decision

**The claim "the suite is byte-deterministic in CI" is withdrawn from every file that makes it.**
`derandomize=True` fixes hypothesis's seed. It does not fix the *examples*, because in
hypothesis 6.156.6 the pool of constants injected into float and integer generation is harvested
from **whatever is in `sys.modules` when the test executes**
(`hypothesis/internal/conjecture/providers.py::_get_local_constants`). A full-suite run has
imported dozens more project modules by the time it reaches a given property file than a run of
that file alone, so the two draw different values from the same seed.

Three consequences are adopted as convention:

1. **A property failure must be reproduced with the whole suite**, not with its own file. A test
   that fails in `pytest -q` and passes in `pytest tests/property/test_x.py` is **not** thereby a
   flake, and must not be dismissed as one.
2. **`uv.lock` is what pins this behaviour**, not `pyproject.toml`. The dev group declares
   `hypothesis>=6.156.6` — a floor, and the floor is the very version that introduced the
   harvesting. Under [R16](../RULES.md#r16) a published number needs the build it was computed on
   named; the same now applies to a property-suite pass.
3. The six files that stated determinism are corrected in place, and D78 carries a dated amendment
   pointing here.

**No configuration remedy is proposed, because none exists.** The only determinism-adjacent field
on `hypothesis.settings` is `derandomize` itself; the environment variables are
`HYPOTHESIS_DATABASE_FILE` and three observability flags. This was checked before the record was
written rather than assumed.

## Rationale

**How it surfaced, and why it looked like the opposite of what it was.**
`test_every_gap_is_a_non_empty_band_that_price_left_behind` failed in a full run and passed on its
own. Every instinct says flake. It was not: hypothesis had generated a fair-value gap **exactly one
ulp wide** — `hi - lo` = 2.842170943040401e-14 = `ulp(lo)` at that price — so `0.5 * (lo + hi)` had
nowhere to land but an endpoint and the strict `lo < midpoint < hi` was false. A real degeneracy,
found only because the full-suite import set moved the constant pool.

**The order-dependence is therefore load-bearing in both directions.** It is why the finding looked
dismissible, and it is also why the finding was made at all: the file alone had never produced that
input in the project's lifetime. Withdrawing the determinism claim is not a downgrade of the
property suite. It is an accurate description of an exploration process that is *better* than the
one D78 described, and dangerous only while people believe the docstring.

**Why D78 was right when it was written, and what actually changed.** D78's reasoning —
*"a flaky property suite that fails only on some seeds trains people to re-run until green"* — is
still correct, and `derandomize=True` still delivers the part that matters: hypothesis does not
roll a fresh seed per run, so a green run is not a coin flip. What broke is narrower and was
invisible: a dependency added a feature that reads global interpreter state, and a claim about
byte-determinism quietly stopped being true. **Nothing in this repository could have caught it**;
it surfaced only because a genuine defect happened to sit in the gap between the two run modes.

**Six files, because the convention was copy-pasted rather than shared.** `D78:11`, plus the
docstrings of `test_breakout_invariants.py`, `test_breakout_nulls_property.py`,
`test_macd_invariants.py`, `test_simulator_invariants.py` and `test_zscore_pairs_invariants.py`.
A seventh, `test_calendar_carry_accrual_property.py`, hedged the claim and pointed at "the fixed
database-free profile in pyproject.toml / conftest" — **which does not exist and never did**. There
is no `[tool.hypothesis]` section and no registered profile anywhere in the repo. That pointer is
corrected too.

The root cause of the repetition is that every property file constructs its own
`settings(derandomize=True, max_examples=..., deadline=None)` rather than sharing one profile. A
single registered profile in `tests/conftest.py` would have made this a one-line fix instead of a
six-file one. **Not done here**: it changes how every property test is configured, which is a
behaviour change wearing a tidy-up's clothes, and it deserves its own record.

## Consequences

- `tests/property/test_structure_invariants.py` keeps its long in-file explanation. It is the
  discovery site and the only file where the mechanism is load-bearing for a specific historical
  failure; the other five get a short correction pointing here.
- `docs/internal/AUDIT_REPORT.md:97` cites "hypothesis derandomized (D78)" as a D34 compliance
  pass. **It is left exactly as it stands.** That document is a frozen audit of what was true on
  2026-07-14, and amending a dated audit to reflect a later discovery would destroy its value as a
  record of what was known when. This record is the correction; the audit is the artifact.
- The eight determinism *tests* (`test_replay_is_deterministic`,
  `test_equity_curve_hash_is_deterministic`, and their siblings) are untouched and still pass. They
  assert that the **engine** is deterministic given identical inputs, which is D34's actual
  requirement and is unaffected. The withdrawn claim was about hypothesis's input generation, not
  about the simulator.
- A future hypothesis upgrade should be read for changes to constant harvesting before it is
  locked, and the lockfile bump is the place that decision gets made.

## What this does not cover

Whether the property suite *should* be example-deterministic. There is a real argument that it
should not be — an exploration process that varies its inputs finds more, as this very episode
demonstrates — and a real argument that a CI gate should be reproducible. **This record decides
nothing about that.** It withdraws a false claim and states how to reproduce a failure. Choosing a
policy is a separate decision, and it needs the shared-profile refactor above to be implementable
at all.
