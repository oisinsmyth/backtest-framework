# D205 — the structure detectors, and the mutation pass that found their tests were weak

**Status:** Committed
**Date:** 2026-08-24
**Category:** Signals & strategy interface
**Source:** WP1 of `docs/specs/STRUCTURE_MODEL.md` (D204)

## The decision

**`research/structure.py` implements the five components as five independent detectors —
no strategy, no costs, no thresholds — each a single causal forward pass, with the
confirmation lag applied where it belongs and asserted by test rather than by docstring.**

A module that fused them would make the question the programme exists to answer
unanswerable, so `market_structure`, `retracement`, `fair_value_gaps` and `rsi` are
separate entry points and WP4 composes them.

## Three choices inside the detectors

**No thresholds.** `retracement` returns a continuous depth, not "is it at 61.8".
`fair_value_gaps` returns every gap, including the ones that are obviously noise. Whether
0.618 is special is WP3's question, and a detector that pre-filtered to 0.618 would have
answered it by assumption. Likewise the course's "if it aligns with my other general
analysis" is precisely the discretion being removed, so it is not implemented.

**One detector has no lag, and says so.** A pivot at `t` is not knowable until `t + k`, but
a fair value gap at `t` is defined by bars `t-2`, `t-1` and `t`, all closed. Giving it a lag
it does not have would be as wrong as omitting one it does.

**The impulse leg's start is captured at the change of character, not when its end
confirms.** By the time the end pivot arrives, `last_high` / `last_low` may have moved on
to newer pivots; reading them then measures the leg from the wrong extreme and every
retracement built on it is quietly wrong. The failure mode is a plausible number, not an
exception — which is the whole family of bug this module is arranged against.

## The part worth recording: two mutations survived 43 green tests

The unit tests passed on the first run. For a look-ahead gate that is exactly when to
distrust them, so the module was deliberately broken six ways and the suite re-run.

| # | mutation | caught? |
|---|---|---|
| 1 | consume pivots one bar early (`confirmed_at = index + k - 1`) — the D173 leak itself | yes, 3 tests |
| 2 | read the leg's start when its end confirms rather than at the CHoCH | yes |
| 3 | fill a gap on the close rather than the bar's range | yes, 2 tests |
| 4 | `>` becomes `>=` in the gap definition | yes |
| 5 | **drop the higher-low requirement — fire the CHoCH off the last swing low** | **NO** |
| 6 | **mirror sign error: read the wrong extreme as a bullish leg's start** | **NO** |

**Mutation 5 is the definition `STRUCTURE_MODEL.md` fixed.** The spec requires a close
below the last confirmed *higher low*; the common shortcut is a close below the last
confirmed low, full stop. They differ whenever a leg prints a pivot low beneath its
predecessor without ever closing below it — the shortcut then fires a change of character
off a structure that never rose. Forty-three tests could not tell the two apart, so the
pre-registered definition was, in practice, untested.

The fix is a planted pattern built to separate them: a swing low at 100 that is *lower*
than the higher low at 101, and a bar closing at 100.5 between the two. The spec fires and
records 101 as the flipped level; the shortcut does nothing. Its mirror, reflected through
a horizontal price axis with high and low swapped, does the same job for the bullish
branch — a mirrored fixture being the cheapest test of a mirrored state machine.

**Mutation 6 survived for a subtler reason, and it is the more useful finding.** The
degeneracy guard refuses a leg whose start is on the wrong side of its end, so the sign
error did not produce *wrong* legs — it silently produced *no* bullish legs. The test
asserted the sign of every leg it found, which a starved branch satisfies vacuously. The
fix asserts both endpoints against the pivot set and requires **each direction to be
populated**: a branch that never produces a leg is broken, not strict.

That generalises past this module. **An invariant asserted only over the outputs a
component produces cannot see a component that has stopped producing them.** Guards that
drop bad cases convert wrong answers into missing ones, and a test written in terms of the
surviving cases will pass either way. It is the same shape as D196's H4 — every S5b
strategy read level prices and never the score, so all ten cells came back bit-identical to
S5 and the sensor was never tested at all — reached from the opposite direction.

## The gate

`tests/unit/test_structure.py` (45) and `tests/property/test_structure_invariants.py` (10):
the look-ahead property per detector at fixed indices and then quantified over paths and
index with hypothesis; pivots pinned against `terrain_swing.confirmed_pivots` rather than
trusted to agree; planted patterns for each component; the two mirror fixtures; and the
false-positive checks the geometry actually licenses.

Those last are deliberately **not** "the detector must find nothing in noise". These are
geometric detectors and they will find shapes in a random walk — that is a fact about
geometry, not a bug, and a test asserting otherwise would be theatre. What is asserted is
that they find nothing where geometry forbids it: a monotone series has no change of
character, and a flat series has no pivots at all under D173's strict-and-unique tie rule.
Whether the shapes found in noise differ from those found in real data is WP3's question,
measured against a null.

1,098 tests green (55 new), mypy `--strict` clean on the new module.

## What this does NOT establish

That any of it means anything. WP1 delivers detectors that find what they say they find,
when they say they can know it. Every question about whether those findings carry
information is downstream, and the census in WP2 comes before any of it.
