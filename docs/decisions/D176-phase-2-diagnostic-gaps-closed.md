# D176 — Phase 2's two missing diagnostics, and the direction bug hiding in the dead one

**Status:** Committed
**Date:** 2026-08-21
**Category:** Diagnostics & reporting
**Source:** Auditing `BREAKDOWN_SHORT_STRATEGY.md`'s diagnostics list against what Phase 2 actually shipped

## Decision

Two required diagnostics that Phase 2 did not deliver are now built, wired and reported:

1. **Squeeze events** — adverse excursions beyond 2 ATR against an open short, with the
   share of trades, the P&L carried by those trades, and how many of them the stop caught.
2. **Per-window long/short correlation** — the brief asks for correlation "per window" and
   the study reported the full-sample figure only.

## Why they were missing, which differs between the two

**The squeeze diagnostic existed and was never called.** `squeeze_events()` sat in
`breakdown_study.py` as dead code from the Phase 2 session. Nothing imported it, no report
rendered it, and the requirement looked satisfied because the function was there. That is
the worst shape a gap can take: a reviewer scanning for the capability finds it.

**And the dead code was wrong.** It computed the adverse excursion as `abs(mae)`. Excursions
are measured in PRICE terms (D112): `mfe = max(high)/entry − 1`, `mae = min(low)/entry − 1`,
written for the long-flat book the module was built for. A short is hurt when price
**rises**, so its adverse side is **MFE**, not MAE. The original would have counted the
short book's *profitable* moves as squeezes and reported them as evidence the tail
discipline was needed.

Worth recording that the code carried a comment reasoning its way to the wrong answer —
"MFE on a short episode is measured against entry price in the trade's favour, so the
adverse side is the one the diagnostics call MAE". Confident, specific, and backwards. It
was caught only because wiring it up meant reading it again. **Dead code is not neutral: it
is unreviewed code wearing the appearance of a delivered requirement.**

**The correlation gap was a plain omission** — full-sample computed, per-window not.

## What they found

**Squeezes are real and the stop does not catch them.** 6 of 35 BTC trades (17%) ran more
than 2 ATR against the position while open, worst 3.70 ATR, carrying −39,015 of P&L between
them — and **0% of them ended at the stop**. The trailing exit or the channel got there
first every time. That is a direct measurement of the thing D169/D170/D171 kept circling:
the stop is present and it is not what closes the dangerous trades.

**Per-window correlation holds.** 15 of 59 windows are measurable — the short book sat out
the other 44 entirely, which is the regime gate working — and none exceeds ±0.2, with a
median of −0.004 and a range of −0.042 to +0.019. So the near-zero full-sample figure is
**not** an artefact of opposite-signed regimes cancelling, which was the specific failure
mode the per-window view exists to expose. The diversification property is genuine; it
remains attached to a book that loses money.

## Conventions pinned

- **A window the short book sat out has no correlation**, and is reported as unmeasurable
  rather than as zero. "Uncorrelated" and "not present" are different claims, and 44 of 59
  windows fall in the second category — collapsing them to 0.0 would have produced a
  reassuring median from windows where one book did not exist.
- **Squeeze direction is an explicit parameter**, not inferred, so the MFE/MAE question has
  to be answered at every call site rather than assumed once.
- Open episodes are excluded: an unrealised excursion is not a squeeze the book survived.

## Consequences

- Phase 2's diagnostics list is now delivered in full, with one exception recorded rather
  than closed: the brief's "time-to-stop distribution compared against the long side"
  remains unbuilt, and is not worth building while the stop closes 0% of squeezes.
- Funding-context tagging stays correctly absent — F5 has no data plumbing (D167).
- The tests added here assert the direction convention directly: a 30% rise against a short
  is a squeeze, the same episode read as a long is not, and a 40% favourable collapse never
  counts. That is the specific bug this record exists to prevent recurring.
