# D99 — Loud guards: duplicate timestamps, empty runs, grid drift, event ordering (audit F10/F11/F17/F18/F19)

**Status:** Committed
**Date:** 2026-07-14
**Category:** Data layer / Backtest engine
**Source:** Audit remediation session (AUDIT_REPORT.md findings F10, F11, F17, F18, F19)

## Decision

Five silent failure modes become loud errors or correct behaviour:

1. **Duplicate bar timestamps (F10).** `align_bars` keys bars by timestamp, so a
   duplicated bar — a real yfinance failure mode after joins/re-fetches — was
   silently collapsed last-wins, with no layer checking. Now: `align_bars` raises
   `ValueError` naming the offending timestamps (structural — nothing downstream
   can receive collapsed data), and the validator flags `duplicate_timestamp` as a
   HARD violation so the snapshot quarantines before the engine ever sees it (D26).

2. **Zero-overlap backtests (F11).** `run_backtest` on instruments sharing no
   common timestamps returned an empty equity curve whose `final_nav` equalled
   starting cash — the audit brief's "quietly-empty backtest" case, verbatim. Now
   it raises.

3. **Study grid drift (F18).** `run_pairs_study`'s warm-up slicing indexes each
   symbol's own series and assumed it matches the aligned universe's grid inside
   each window — true for every committed fixture (verified: all 57 symbols
   byte-identical timestamps) but never asserted, so a future universe with extra
   bars would silently shorten windows through the engine's inner join. Now each
   window asserts the slice's test-span timestamps equal the aligned test bars and
   that all legs share one prefix grid, and that the warm-up prefix actually fits.

4. **Dividend/split ordering within one gap (F19).** The engine scaled positions
   for splits BEFORE computing event flows over the same inter-bar gap, so a
   dividend whose ex-date preceded the split's paid on the post-split share count
   — wrong by the split ratio (latent: needs both events inside one gap, i.e.
   across a dropped bar or weekend). Now the gap is segmented at each split
   ex-date: flows before the split use pre-split shares, flows on/after it use
   post-split shares. A dividend exactly ON the split ex-date pays the post-split
   count, because its per-share amount is already post-split-frame
   (`as_declared_dividends` scales only by splits strictly after it, D75) — the
   segment boundary sits a microsecond before the split ex-date to implement
   that convention with the existing `(prev, curr]` event-flow interface.
   Carry is unchanged: its base (qty × price) is split-invariant.

5. **Cleaner volume indexing (F17).** `clean()` now bounds-guards `volumes[i]`
   the same way the validator always did — a shorter volume series was an
   IndexError mid-clean.

## Rationale

Every one of these is the same failure class the framework's Pillar 1 exists to
prevent: data or configuration problems degrading a result silently instead of
stopping it. None of them changes any committed artifact — the golden masters,
cross-engine reconciliation, and all five study runs are unaffected (no committed
fixture contains duplicates, zero-overlap inputs, grid drift, or a dividend and
split in the same gap) — which is exactly why they had to become structural
guards now, while they are still hypotheticals rather than postmortems.
