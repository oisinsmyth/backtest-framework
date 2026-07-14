# D105 — Convention-sensitivity study: fill timing × impact calibration on the v2 configuration

**Status:** Committed
**Date:** 2026-07-14
**Category:** Validation & research integrity
**Source:** Audit remediation session (AUDIT_REPORT.md findings F3/F4 — the measurement half)

## Decision

`scripts/run_convention_sensitivity.py` → `docs/results/convention_sensitivity.md`:
the v2 configuration (cointegration selection, 1:1 hedge, identical windows and
parameters) re-run across the 2×2 of execution/calibration conventions —
{close, next-open fills} × {full-sample, train-window impact calibration} — on
the same frozen snapshot, multipliers cut to the two informative levels (0×
isolates the gross edge, where fill timing bites; 1× is the real-cost verdict).
Four prefixes in one registry; per-variant DSRs over each variant's own 1×
window trials (D98). Built-in cross-checks: the baseline cell must reproduce the
published v2 numbers (per-multiplier chaining makes shared levels byte-identical
to the 5-level sweep), and the train-cal 0× row must equal the baseline 0× row
(calibration cannot matter when costs are off).

The published v1–v3/capacity/gross artifacts are NOT rewritten: they are history
under the stated conventions, whose caveats always said so. This study prices
the conventions as its own one-variable(-pair) artifact, the same pattern as
D76's v1-alongside-v2.

## Rationale

The audit's F3 was blunt: v2's headline "+19.03% gross edge at 0×" partially
rests on entries that always catch exactly the close that triggered them, and no
sensitivity run existed anywhere. With D103 (next-open fills) and D102
(train-window calibration) in the framework, the cheapest honest response is to
measure rather than argue. The result matters in either direction: if the gross
edge survives next-open fills, the program's central "edge exists but doesn't
clear frictions" claim gains a robustness exhibit; if it collapses, the claim
weakens to "edge indistinguishable from a fill-timing artifact" — which the
writeup must then say. Numbers live in the artifact, which the writeup's
methodology section references.
