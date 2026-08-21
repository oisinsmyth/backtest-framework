# Per-Bar Volume Extension — Design Plan (D111 → proposed D150)

**Status: BUILT, 2026-08-21 — see [D168](decisions/D168-volume-rides-inside-the-dataview.md).**
The plan below was followed as written; the design survived contact with the code, and the
verification gates it specified are the ones that ran. Two things worth recording against
the estimates: the reflection-audit extension mattered exactly as much as predicted (the
existing Attack 5 inspected only tuples of `Bar`, so the volume tuple would have been
untested by construction), and the golden master's off-by-one risk showed up in the test
rather than the hand file — bar index t is calendar day t+1, and the first cut asserted on
calendar days, which made one assertion pass vacuously.

Originally written 2026-08-18, prompted by
[`BREAKOUT_RESULTS.md`](../BREAKOUT_RESULTS.md)'s blocked volume-confirmation filter
([D111](decisions/D111-volume-filter-blocked-on-bar-schema.md)). Unlike
[`options_extension.md`](options_extension.md), which is a deferral, this is a **design for
imminent work**: the change is small, the verification is not, and this document exists so
the verification is planned before the code is written rather than discovered afterwards.

## The decision in one paragraph

Volume becomes visible to strategy code by riding **inside `DataView`** as an aligned,
optionally-present series, constructed sliced exactly the way bars already are. `Bar` and
`TimestampedBar` are unchanged. Volume is **optional at every level** — an instrument that
has no meaningful volume (spot FX, an index, a synthetic series) simply never supplies one,
and `view.volume(i)` returns `None`. What is *not* optional is honesty about which kind of
absence you are looking at: "this instrument has no volume" and "somebody forgot to wire the
volume through" must not be the same observation, because the second one silently turns a
volume filter into a filter that rejects everything and returns a clean-looking result.

## Why this shape and not the other two

| Option | Verdict |
|---|---|
| `volume` field on `Bar` | **No.** `Bar` is constructed at ~90 sites (5 in `src`, ~85 in tests) — stop-fill logic, cost bricks, every golden master. A required field breaks all of them; an optional one is a field that is silently required in real usage but typed as though it is not. [D60](decisions/D60-timestampedbar-wraps-bar.md) already rejected adding `timestamp` to `Bar` on exactly this reasoning, and [D48](decisions/D48-no-false-affordances-enum-values-and.md) names the optional-field version as a false affordance. |
| `volume` field on `TimestampedBar` | **Does not reach the strategy.** `DataView` holds `Bar`, not `TimestampedBar` — `build_data_view` is called with `Bar` objects sliced out of `AlignedBar.bars`. Volume on `TimestampedBar` stops at the engine boundary, which is where it already is. |
| **Aligned series inside `DataView`** | **Yes.** Purely additive, every parameter optional with a default, no existing call site changes, and the look-ahead guarantee is inherited rather than re-argued. |

## Why volume was never plumbed this way before

Worth stating, because it looks like an omission and is not. Volume has been in this repo
since Step 7: fetched by `get_raw_history`, stored as a column in every fixture, carried
into snapshots, and consumed by four subsystems — the cleaner (zero-volume detection), the
validator (10× spike warnings), `calibrate_impact_params` (ADV for D3's sqrt-impact brick),
and the capacity/gross studies. It travels as a **parallel channel**,
`volumes_by_symbol: Mapping[str, Sequence[float]]`, across 13 signature sites.

That sufficed because **every one of those consumers sits on the engine side of the D32
look-ahead guard**, and legitimately holds the whole series — `calibrate_impact_params`
*wants* the full volume vector at once, not one bar at a time. None of them go through
`DataView`. The breakout study's volume filter is the first consumer on the *strategy* side
of that guard. The requirement did not exist until it did.

---

## The three states, and why two is not enough

This is the load-bearing design decision, and it is what "it just returns nulls" has to mean
in a framework whose philosophy is that absence must be loud
([D48](decisions/D48-no-false-affordances-enum-values-and.md),
[D99](decisions/D99-loud-guards-duplicates-empty-runs-event-ordering.md)).

| State | Meaning | Behaviour |
|---|---|---|
| **1. Not applicable** | The instrument has no volume in any meaningful sense — spot FX, an index level, a synthetic path. A permanent property of the world. | `view.has_volume` is `False`; `view.volume(i)` returns `None`. **Silent and correct.** |
| **2. Applicable, missing on this bar** | A real gap in a real series (the fixture loader already yields `NaN` for a blank cell). | `view.volume(i)` returns `None` for that index only. **Silent; the consumer states its own policy.** |
| **3. Applicable, required, not wired** | A component that needs volume is running against a view that was never given any. A configuration error. | **Loud.** `view.require_volume(i)` raises `MissingVolumeError` naming the instrument. |

Collapsing 1 and 3 is the trap. `NaN` is worse still — every comparison against `NaN` is
`False`, so `if volume > 1.5 * average` on a NaN-bearing series rejects every entry and
produces a plausible, wrong result with no error anywhere. **`NaN` is normalised to `None`
once, at construction, and never enters the view.**

The consumer picks its contract by picking its accessor. That is the D48 pattern applied
directly: `volume()` says "I can work without it", `require_volume()` says "I cannot".

---

## API surface

### `engine/dataview.py`

```python
class MissingVolumeError(LookAheadError):        # new
    """Raised when code that REQUIRES volume holds a view constructed without one."""

@dataclass(frozen=True)
class DataView:
    _visible_bars: tuple[Bar, ...]
    _visible_volumes: tuple[float | None, ...] | None = None   # new, defaults to absent

    @property
    def has_volume(self) -> bool: ...

    def volume(self, index: int) -> float | None: ...
    def require_volume(self, index: int) -> float | None: ...
```

- `volume` and `require_volume` resolve `index` through the **same** logic as `__getitem__`
  (absolute, with Python-style negatives, `LookAheadError` outside `[0, current_index]`).
  That resolution is factored into a private `_resolve(index)` used by all three, so a
  future change cannot make the bar accessor and the volume accessor disagree about what
  index `-3` means.
- No `mean_volume(...)` or similar helper. Aggregation embeds a policy about `None`, and
  policy belongs in the consumer, not in the guard object.
- `_visible_volumes` is `None` (absent) or a tuple of exactly `len(_visible_bars)` entries.
  Enforced in `__post_init__`.

### `engine/dataview.py` — construction

```python
def build_data_view(all_bars, up_to_index, volumes: Sequence[float] | None = None) -> DataView
```

- `len(volumes) == len(all_bars)` or a loud `ValueError` naming both lengths (D99 shape).
- Sliced to `[: up_to_index + 1]` — **the whole point**. Future volumes are never handed to
  the object, so there is nothing for reflection, `vars()`, or a leading-underscore poke to
  find. The guarantee is inherited from the existing construction, not re-argued.
- `NaN` → `None` conversion happens here, once.

### `engine/backtest.py`

```python
def run_backtest(..., volumes_by_instrument: Mapping[str, Sequence[float]] | None = None)
```

- Same shape and the same handling as the existing `view_bars_by_instrument`: build a
  `{timestamp: volume}` map per instrument, then index it by `ab.timestamp` for each aligned
  bar. A timestamp present in the aligned bars but absent from the volume map is a loud
  `ValueError`, exactly as the view-bar path already does.
- `align_bars` is **unchanged**. Volume is looked up by timestamp against the already-aligned
  series; it does not need to participate in the inner join itself.
- Instruments absent from the mapping get `None` — state 1, silently.

### `validation/walk_forward.py`

```python
def walk_forward_windows(..., volumes_by_instrument=None)
```

Optional, so fitters that want volume (a liquidity-aware selector, say) get it under the
same guard. Train views are built by the same `build_data_view` call, so the slicing
guarantee is identical.

### `strategies/breakout.py`

- `EntryFilter` gains `requires_volume: bool` (a read-only property, matching how `name` is
  declared after the F20 variance fix). Every existing filter returns `False`.
- `BreakoutStrategy.generate_targets` checks, **on its first call**, that
  `view.has_volume` holds whenever any filter declares `requires_volume` — and raises
  `MissingVolumeError` naming the instrument if not.

  *Why first call and not construction:* the strategy is built before it ever sees a view,
  so construction-time validation is impossible without handing the strategy the data —
  which is the hole this design exists to avoid. First call is bar 0, not bar 3,000, which
  satisfies the spirit of D35's "fail at factory time" as closely as the architecture allows.
  This trade-off is deliberate and should be recorded in the decision, not left implicit.

- `VolumeConfirmationFilter(multiple=1.5, window=20)`: accepts when
  `volume(t) > multiple × mean(volume over t−window … t−1)`. Uses `require_volume`.
  **Stated policy on gaps:** any `None` inside the window, or on the trigger bar, rejects
  the entry — you cannot confirm on data you do not have. Conservative, documented, tested.

---

## The trap that is not in the code: which frame is volume in?

Share volume is **split-sensitive** — a 4-for-1 split quadruples the share count traded.
This framework already runs two price frames (D75): an execution frame of as-traded raw
prices, and a view frame of split-adjusted prices for signal continuity.

**Decision: volumes align to the VIEW frame**, because that is the frame strategies see and
volume is only ever consumed by strategy code. The caller supplies volumes in the same frame
as `view_bars_by_instrument`, and the docstring says so.

This is moot for the crypto work (spot crypto has no splits, and the fixture's events sidecar
is empty by construction, D108) and live for any equity use. It is exactly the class of bug
D75 exists to prevent, so it gets stated up front and a test on a split-bearing symbol —
not discovered later in a results doc.

---

## Verification gates (house style — a step is done when its gate passes)

**DataView (U)**
- `volume()` and `__getitem__` resolve identical indices identically, including negatives.
- `volume(current_index + 1)` and `volume(-len-1)` raise `LookAheadError`.
- Absent series → `has_volume` False, `volume(i)` returns `None`, `require_volume(i)` raises.
- `NaN` in the input never appears in the view; it is `None`.
- Length mismatch between bars and volumes fails loudly, naming both lengths.

**Structural guard (I) — extends `tests/integration/test_dataview_lookahead_guard.py`**
- The existing cheating-strategy test gains volume attacks. Note its Attack 5 walks
  `vars(view).values()` looking for tuples of `Bar`; it must be extended to inspect tuples of
  floats against future volumes, or the new surface is untested by construction.
- A view built at index *i* holds exactly *i+1* volume entries — asserted directly, the same
  way `len(view._visible_bars) == 4` is asserted today.

**Property (P, seeded, D78)**
- Perturbing any volume after the decision bar — arbitrarily — cannot change a target the
  strategy already produced. This is the existing no-look-ahead property extended to the new
  channel, and it is the single most important new test.
- A filter's accept/reject decision is a pure function of visible volumes.

**Golden master (G, D39)**
- A small hand-computed scenario where a volume-gated entry is admitted on one bar and
  rejected on another, with the 20-bar average worked out in an adjacent `.hand.txt`.

**Regression (the cheap, decisive one)**
- **All 12 existing golden masters pass untouched.** Because every new parameter is optional
  with a default, no existing behaviour moves — and that passing suite is the *evidence* the
  change is additive, not a claim about it.

**Cross-engine (X, D41/D79)**
- `run_backtest` gaining a parameter is a simulator-touching change. The vectorbt
  reconciliation runs in the normal offline suite, so this re-runs automatically — the D41
  policy is already mechanised and needs no separate action.

---

## Build order

Each step is independently testable and independently revertible.

1. **`DataView` + `build_data_view` + unit tests.** No engine change; provable in isolation.
2. **Guard and property extensions.** Before any consumer exists, so the guard is written
   against the surface rather than around a use case.
3. **Engine wiring** (`run_backtest`, then `walk_forward_windows`) + alignment tests.
4. **`VolumeConfirmationFilter`** + unit tests + the golden master.
5. **Re-run the breakout study** with the filter as a fifth filter variant. Flip
   [D111](decisions/D111-volume-filter-blocked-on-bar-schema.md) from Deferred to Superseded,
   and let the filter face the same keep/drop rule as the other three.
6. **Decision record, CHANGELOG, AITODO** per R4/R5.

## Effort

| Step | Estimate |
|---|---|
| 1 — DataView + construction + unit tests | 1.5 h |
| 2 — guard + property extensions | 1.5 h |
| 3 — engine + walk-forward wiring, alignment tests | 1.5 h |
| 4 — filter + golden master (the `.hand.txt` is the slow part) | 2 h |
| 5 — study re-run, results doc, D111 disposition | 1 h |
| 6 — records and doc sync | 0.5 h |
| **Total** | **~8 h — about one week of this project's stated budget** |

## Risks

1. **Guard erosion (highest).** A new accessor is new attack surface. Mitigated structurally:
   the volume tuple is *constructed sliced*, so there is no future data in the object to
   reach — the same "physically cannot" property bars already have (D56). The reflection
   audit must be extended or this mitigation is untested.
2. **Constructor back door.** If a filter can take a volume series in its own constructor,
   the guard is decorative. Volume enters through `build_data_view` and nowhere else, and
   the `EntryFilter` protocol gives filters no way to accept one.
3. **The split frame.** See above. Live for equities, moot for crypto, tested either way.
4. **`NaN` semantics.** Handled once at construction; a test asserts `NaN` never reaches a view.
5. **Scheduling.** `engine/dataview.py` and `engine/backtest.py` are read-only to the three
   agents currently running, but all three import `run_backtest`. The change is additive and
   would not break them — but editing the engine while three agents have it open is
   avoidable risk. **Land this after they report.**

## What it unblocks beyond the one filter

- Any liquidity-aware signal or selector (volume-confirmed breakouts, volume-weighted
  z-scores, dollar-volume screens inside a walk-forward training window).
- A D44-compliant, per-window ADV estimate available to *strategy* code, not just to the cost
  layer — the cost layer's needs are already met by `impact_calibration="train_window"` (D102),
  so this is genuinely new capability rather than a duplicate path.

## The honest caveat about the payoff

Even fully built, the filter's *data* is weak for this study. Crypto daily volume from
yfinance is an aggregate across venues with inconsistent inclusion rules — a plausible
relative signal and a poor absolute one. And the three filters already tested all **reduced**
performance by removing trades that were, on average, good. The prior is that a volume filter
does the same.

Build this for the framework capability and to close a written deferral honestly. Do not
build it expecting a result.
