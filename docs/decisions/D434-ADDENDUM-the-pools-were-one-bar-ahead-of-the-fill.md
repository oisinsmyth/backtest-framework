# D434 ADDENDUM — the pools were one bar ahead of the kernel's fill; shifted and re-run

**Committed before the re-run. The spec's features, pools, counts, draws and predictions are
unchanged; only the alignment between a pool and the kernel's entry changes.**

## What happened

The first run of all 132 cells completed (two halves, ~55 min). Its `cx_dn` cell read **−405 bp
for a random LONG** at n = 3,000 and `cx_up` **+471** — almost exactly one two-sigma day. That is
what a look-ahead of one bar looks like, and it was one.

`d345_event_book.simulate_event` enters an event placed at bar `t` at the **open of bar `t`**: the
entry bar's first mark is `ocT[t]` (open → close), and `r1T` is the close-to-close total return
(`run_d295.build_inputs`: `expm1(total_log_returns)`). D340 states the convention: *"every
D300-family book computes its signal from the close of bar t−1"* and fills at the next open. So
`mask[t] = True` means **signal known at close `t−1`**. The spec's features are "causal at the
close of bar `t`" — true, and one bar too late for a mask at `t`: a climax day's own move sat
inside the trade. D392's price and 12-1 momentum pools carry the same nominal misalignment and are
insensitive to it (a close-to-close price tercile barely moves within a bar; `mom_252_21` skips
the last month); volume pools built from bar `t`'s own volume and return are maximally sensitive.

The `[C]` check verified that the *features* read no bar after `t`. It did not verify that the
*mask* was aligned to the kernel's fill. That is a different property and now has its own check.

## The fix

- `volume_pools` shifts every pool one bar: **`mask[t] = feature_pool[t−1]`**, so the event at `t`
  is filled at `t`'s open on information complete at `t−1`'s close. Row 0 is empty.
- **`[F]`** fill-alignment: for every pool, `mask[t]` equals the unshifted pool at `t−1` on every
  bar, and the unshifted pool at `t` is *not* a function of the bar the kernel fills on (a check
  that fires when the shift is removed — the self-test removes it and must see `[F]` raise).
- The first run's artefacts are moved to `temp/d434_atlas_volume_{a,b}_LOOKAHEAD.json` — kept as
  evidence of the error, not as data — and both halves re-run to fresh `data/` artefacts.

## What to expect from the shift

`cx_dn` / `cx_up` lose the climax day and become a base rate of what follows a climax; `rv_x3`
likewise; the tercile pools of `rv` and `ef` move most, `uv`, `vt` and `dv` least (20- and 60-day
windows shift by one bar). The spec's predictions stand as written; X-b's sign was written for the
post-climax bars and is now testable.
