# D168 — Volume reaches strategy code inside `DataView`, as one of three explicitly different states

**Status:** Committed
**Date:** 2026-08-21
**Category:** Signals & strategy interface
**Source:** Phase 1.1 follow-on session (closing D111)

## Decision

Volume becomes visible to strategy code by riding **inside `DataView`** as an aligned,
optionally-present series, constructed sliced exactly the way bars already are. `Bar` and
`TimestampedBar` are unchanged. `build_data_view`, `run_backtest` and
`walk_forward_windows` each gain one optional parameter with a default, so no existing
call site changes.

Volume has **three states**, and the accessor a consumer picks is its declaration of
which ones it can tolerate:

| State | Meaning | Behaviour |
|---|---|---|
| 1. Not applicable | The instrument has no volume in any meaningful sense — spot FX, an index level, a synthetic path. | `has_volume` is `False`, `volume(i)` returns `None`. **Silent and correct.** |
| 2. Applicable, missing on this bar | A real gap in a real series. | `volume(i)` and `require_volume(i)` return `None` for that index. **Silent; the consumer states its own policy.** |
| 3. Applicable, required, not wired | A component that needs volume is running against a view that was never given any. A configuration error. | `require_volume(i)` raises `MissingVolumeError`. **Loud.** |

This supersedes [D111](D111-volume-filter-blocked-on-bar-schema.md), which recorded the
volume-confirmation filter as blocked.

## Rationale

**Why not a field on `Bar`.** `Bar` is constructed at roughly ninety sites across the
simulator, the cost bricks and every golden master. A required field breaks all of them;
an optional one is a field that is silently required in real usage but typed as though it
is not. [D60](D60-timestampedbar-wraps-bar.md) already refused to widen `Bar` for
`timestamp` on exactly this reasoning, and [D48](D48-no-false-affordances-enum-values-and.md)
names the optional-field version as a false affordance.

**Why not a field on `TimestampedBar`.** It would not reach the strategy. `DataView`
holds `Bar` objects, so volume on `TimestampedBar` stops at the engine boundary — which
is precisely where it already was.

**Why inside `DataView`.** Purely additive, and the look-ahead guarantee is *inherited*
rather than re-argued: the volume tuple is constructed sliced, so future volumes were
never handed to the object and there is nothing for reflection, `vars()`, or a
leading-underscore poke to find. That is D32/D56's "physically cannot" property extended
to a second channel rather than a second, weaker promise.

**Why three states and not two.** This is the load-bearing part. Collapsing "no volume
exists" into "volume wasn't wired" is the trap, because a volume filter running against a
view with no volume rejects *every* entry and returns a clean-looking, entirely wrong,
entirely flat result — with no error anywhere to say so. `NaN` is worse still: every
comparison against `NaN` is `False`, so a NaN-bearing series produces the same silent
wrongness. **`NaN` is normalised to `None` once, at construction, and never enters a
view.**

**Why the strategy checks on its first call rather than at construction.** The strategy is
built before it ever sees a view, so construction-time validation would mean handing the
strategy its data — which is the exact hole this design exists to avoid. The first call
is bar 0, not bar 3,000, which satisfies the spirit of D35's "fail at factory time" as
closely as the architecture allows. The trade-off is deliberate and is recorded here
rather than left implicit.

**Which frame volume is in.** Share volume is split-sensitive: a 4-for-1 split quadruples
the share count traded. This framework runs two price frames (D75) — as-traded raw prices
for execution, split-adjusted prices for signal continuity. **Volumes align to the VIEW
frame**, because that is the frame strategies see and strategy code is volume's only
consumer. Moot for spot crypto (no splits, empty events sidecar by construction, D108),
live for any equity use, and stated up front rather than discovered later in a results
doc.

## Verification

The change is ~60 lines; the verification was the cost, and it was planned before the
code was written rather than discovered afterwards.

- **The reflection audit was extended, not assumed.** The existing cheating-strategy test
  walked `vars(view)` looking for tuples of `Bar` — a tuple of floats carrying the full
  volume series would have walked straight past it. Without that extension the structural
  mitigation would have been untested by construction.
- **The property test is the important one:** perturbing any volume after the decision bar,
  arbitrarily, cannot change a target the strategy already produced. A second data channel
  is a second way to leak the future, and the bar channel's guarantee does not extend to
  it by argument.
- **A hand-computed golden master** (`test_volume_confirmation_golden.hand.txt`) pins an
  11-bar scenario where bar 3 and bar 9 are identical in every respect the strategy cares
  about except volume — both closing far above their own 3-bar high against the same
  100-unit baseline, one printing 500 and one printing 100. Any behavioural difference
  between them is attributable to the volume rule and nothing else.
- **All existing golden masters pass untouched.** That passing suite is the *evidence* the
  change is additive, not a claim about it.

## Consequences

- `VolumeConfirmationFilter(multiple=1.5, window=20)` exists and faces the same keep/drop
  rule as the other four filters, rather than being reported as an absence.
- **Stated gap policy:** any missing volume on the trigger bar or inside the averaging
  window rejects the entry. You cannot confirm on data you do not have, and the
  conservative direction for a confirmation filter is to decline. The alternative —
  averaging whatever is present — silently varies the window length per trigger.
- Feature **F2** (trigger volume ratio) is computable for the first time (D167 recorded it
  blocked).
- The averaging baseline **ends at t−1** (D44) in both the filter and the feature: a large
  trigger bar must not inflate the very average it has to beat.
- What this unblocks beyond one filter: any liquidity-aware signal or selector, and a
  D44-compliant per-window ADV estimate available to *strategy* code rather than only to
  the cost layer.

## The honest caveat about the payoff

Recorded in `docs/volume_extension.md` before the work started, and worth repeating: the
*data* is weak for this study. Crypto daily volume from yfinance is an aggregate across
venues with inconsistent inclusion rules — a plausible relative signal and a poor absolute
one. The three filters already tested all **reduced** performance by removing trades that
were, on average, good, and the prior was that a volume filter does the same. This was
built for the framework capability and to close a written deferral honestly, not because a
result was expected.
