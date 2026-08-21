# D143 — The D26/D74 sanity gate is ETF-calibrated; the crypto cross-section overrides it explicitly and reports every violation

**Status:** Committed / Deferred (recalibration deferred, per R3)
**Date:** 2026-08-18
**Category:** Data layer
**Source:** Breakout universe session

## Decision

The universe snapshot is **quarantined** by the validator and is loaded anyway, via
`SnapshotStore.load(snapshot_id, allow_quarantined=True)`, in one visible place in
`scripts/run_breakout_universe.py`, with a dedicated section of the report stating:

- the total (143 hard violations across 41 of 63 symbols, plus 2,368 warnings and 25
  cleaning drops);
- that every hard violation is the same check — `unexplained_move`, a >60% single-bar move
  with no split to explain it;
- the count split **survived vs collapsed/delisted**, which is the argument;
- the ten symbols carrying the most violations.

The validator itself is **not touched**, and the thresholds are **not** recalibrated for
crypto. That is recorded here as a deferral.

## Rationale

D74 calibrated the move thresholds against observed genuine ETF data: 25–60% unexplained is
a warning, >60% is a hard quarantine, chosen so the real 2020 COVID crash days would not be
thrown away. On a broad crypto cross-section a >60% day is not a scraper artifact — ADA rose
137% on 2017-11-28 and BNB rose 62% on 2018-01-05, and those are real prints. The gate is
measuring "this is not an ETF", not "this is bad data".

**The distribution is what forces the decision.** The violations concentrate in the tokens
that collapsed — `BTG-USD`, `HT-USD`, `LUNC-USD`, `USTC-USD`, `LUNA1-USD` lead the count.
Respecting the gate mechanically would delete precisely the failed cohort and hand back the
survivorship bias the study exists to remove (D140). A gate that silently re-creates the
bias a study is measuring is worse than no gate, and the correct response is neither to
suppress it nor to obey it blindly, but to **report it in full and override it in one
place** — which is what "quarantined, not passed through" was protecting against in the
first place: *silent* passage.

The cleaner is not overridden. Its 25 drops stand, and the positivity clause of the
universe policy (D140) runs on the cleaned series precisely so genuine provider garbage —
`AAVE-USD`'s zero-priced first bar, `SHIB-USD`'s and `COMP-USD`'s part-zero series — is
still caught. What is overridden is one threshold that was calibrated on a different asset
class.

## What is deferred, and why not now (R3)

A crypto calibration of `MOVE_WARNING_THRESHOLD` / `MOVE_HARD_THRESHOLD` — or, better, a
per-asset-class threshold carried by the instrument the way D17 intended calendars to be —
is real framework work with its own verification gate: it changes what every past and
future snapshot means, and re-deriving thresholds from observed genuine data (D74's method)
requires deciding what "genuine" means for a token in freefall.

**Recalibrating a cross-cutting data gate from inside a study is how gates stop meaning
anything.** The study takes the override, names it, counts it, and leaves the gate alone.
