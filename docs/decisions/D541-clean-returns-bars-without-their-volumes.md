# D541 — `clean()` drops bars and hands back no volumes, and the guard against that could never fire

**Status:** Committed
**Date:** 2026-09-17
**Category:** Data integrity
**Source:** Reviewer B's inside-out audit of `src/`, filed as minor. It is not minor as an
interface and it is not live as a defect, and separating those two is what this record is for.

## The interface

`clean()` takes `volumes_by_symbol`, uses it to decide which bars to drop — `non_positive_volume`
is one of its four rules — and returns `(cleaned_bars, report)`. The caller is left holding the
volume series it passed in, now longer than the bars it belongs to and **misaligned from the first
drop onward**, with every subsequent volume attributed to the wrong bar.

That is not a hypothesis about the interface; the codebase already worked around it.
`research/breakout_universe.align_volumes` exists for exactly this and says so:

> `clean()` (D25) returns bars only — it drops bad prints and reports them, but the volume list it
> was handed is not re-indexed, so after any drop the two are misaligned by construction. That is
> an existing interface and this study does not get to change it (D111's precedent).

## The guard that could not fire

`scripts/run_breakout_study.py` raises when `len(supplied) != len(series)`, and its comment claims
a misalignment "would be a loud failure rather than a quietly shifted volume history".

**It could never fire.** `save_fixture_csv` iterated `enumerate(series)` reading `volumes[i]`, so a
longer volume series was silently cut to the bar count with its **first N entries kept** — which
preserves exactly the wrong alignment and then makes the lengths agree, before any downstream length
check runs. Demonstrated on the old writer: four volumes written against three bars read back as
`[1.0, 2.0, 3.0]`, no error anywhere.

A second symptom was surfacing elsewhere and being mislabelled. `calibrate_impact_params` raises
`"{symbol} has N volumes against M bars"`, and `FactoryRegistry.build` wrapped it as
`ConfigError: invalid cost_brick config for type 'sqrt_impact'` — this defect arriving at the user
disguised as a typo in a dict. Fixed in the same round.

## What is actually affected — measured, not inferred

Classifying by reading each call rather than by grepping for the name: **56 `clean()` call sites in
`scripts/`, of which 17 are exposed** — they pass volumes in (so the volume rule can drop) and then
use the original series. The rest are safe because they call `clean(bars)` price-only, re-index
through `align_volumes`, or raise if anything was dropped.

Exposure then depends entirely on whether the fixture a runner reads actually loses a bar:

| fixture | bars | dropped | exposed runners reading it |
|---|---:|---:|---|
| `crypto_daily_2015_2025_raw.csv.gz` | 6,991 | **0** | `run_breakout_study`, `run_breakout_nulls`, `run_crypto_pairs_study`, `run_breakdown_study` |
| `universe_daily_2015_2024_raw.csv.gz` | 143,355 | **0** | `run_gross_sweep`, `run_capacity_analysis`, `run_pairs_study{,_v2,_v3}`, `run_convention_sensitivity` |
| `etf_intraday_15m_raw.csv.gz` | 3,194,849 | **0** | `run_etf_intraday_gate` |
| `xle_xop_daily_2015_2024_raw.csv` | 5,030 | **0** | `run_first_result_v2` |
| **`crypto_binance_15m_raw.csv.gz`** | 765,408 | **658** | `run_sampling_invariance`, `run_scaling_ladder`, `run_assembled_strategy`, `run_gate_1h_replication` |

**One fixture drops anything, and it feeds four runners.** 658 bars of 765,408 is 0.086%, and the
misalignment starts at the first drop and persists to the end of each affected symbol's series.

Where it reaches: `validate()`'s `zero_volume` and `volume_spike` warning counts, and
`calibrate_impact_params`'s ADV — therefore `SqrtImpact` charges, therefore net P&L, Sharpe and
drawdown for any cell that prices impact. It does **not** reach a snapshot id for the four affected
runners, because `_hash_payload` hashes the written `bars.csv` and the writer now refuses a
mismatched series rather than writing a truncated one.

## Decision

1. **`CleaningReport` carries `kept_indices`** — the input indices that survived, per symbol — and a
   `realign(symbol, values)` helper. Additive: no signature changes and no caller breaks. A caller
   holding volumes can now realign exactly instead of re-deriving the mapping from timestamps.
2. **`save_fixture_csv` refuses a volume series whose length does not match its bars**, naming both
   counts, rather than truncating to fit. Truncation is what made the misalignment unobservable.
3. **The four affected runners are recorded here and are NOT re-run under this record.** Their
   published numbers are affected at the 0.086% level on one fixture, and moving a published figure
   is a research decision with its own pre-registration (R8) — not something an infrastructure fix
   gets to do in passing. This record is the standing note that they are known-affected.
4. **`align_volumes` stays.** It solves the same problem by re-matching on timestamps and is proven;
   `kept_indices` gives new callers a cheaper route without forcing a migration.

## What this does not settle

Whether the four affected results move materially when re-run. 658 drops in 765,408 bars is small,
and ADV is a mean over a long series, so the expected effect is far below the published precision —
but "expected" is not "measured", and this record deliberately does not claim it. Re-running them is
a separate decision.

It also does not change the 13 call sites that re-index via `align_volumes` or the 26 that clean
price-only. Those were correct before this record and are correct after it.
