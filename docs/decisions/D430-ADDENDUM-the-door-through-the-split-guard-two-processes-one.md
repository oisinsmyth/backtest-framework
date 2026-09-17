# D430 ADDENDUM — the door through the `[SPLIT]` guard: two processes, one opener

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D430-ADDENDUM-the-door-through-the-split-guard-two-processes-one-opener.md`. The H1 above is the full title.*

**Committed before the read. The bar, the construction, the frozen thresholds and the one-read
rule of `7dd4ff8` are unchanged; only the mechanism by which the file is opened changes.**

## What happened

The first `--holdout` attempt was refused before a byte of the holdout was read:
`run_d411_signed_volume_at_price.py` installs a `sys.addaudithook` at import that raises on any
`open` of a path containing "holdout". It refused the *meta* file, the first thing
`assert_gates_passed` reads. The hook is unconditional, process-wide and un-removable; it enters
this line's chain through `run_d412` (the zone builder), which every downstream module inherits.
D411's records document no exception path; the one prior holdout read (D357) predates the hook.
`data/d430_holdout.json` was never written; the read is intact.

## The door, as approved by the principal

**Mining-side code never opens a holdout file. One separate process does, and only it.**

1. `scripts/d430_oos_loader.py` — imports only `ragged_panel`, `d339_universe_floor` and
   `run_d320_tilt_filters` (none carry the hook), requires `--spend-the-holdout`, opens
   `us_shorts_daily_holdout.csv.gz` + `_events.json` through the **same `load_panel_from` body
   the proof validated**, writes the panel arrays to `temp/d430_oos_panel.npz` (a name with no
   "holdout" in it, so the guard in the second process has nothing to refuse), and prints a
   receipt: the fixture name, its SHA-256, the panel shape, the eligibility share.
2. `scripts/run_d430_holdout.py --holdout` — the runner as proved, hook active, now reads that
   cache instead of the fixture and **refuses to run if the cache is absent**. Its artefacts are
   renamed `data/d430_oos.json` and `temp/d430_oos_inputs.npz`. Every other holdout path in that
   process stays refused. The pipeline from panel to bar is byte-for-byte the code the proof ran.

What was **not** done: no switch inside `run_d411`'s hook (that would weaken the guard for every
future runner), no `require_gates=False`, no bypass of `assert_gates_passed`.

## Still one read

The loader is the read. It runs once; the runner's `[ONE-READ]` check now keys on
`data/d430_oos.json`. A crash in the runner after the loader has run does not un-spend the file;
it is recorded as a bug against a spent read, as `7dd4ff8` §3 says.
