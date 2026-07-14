# D84 — The options extension scoping write-up: six hard problems, Lego audit, trigger conditions

**Status:** Committed (the write-up) / Deferred (the options wing itself)
**Date:** 2026-07-14
**Category:** Instruments
**Source:** Implementation session (Step 11)

## Decision

`docs/options_extension.md` is now the real scoping decision D16 promised, replacing
the Step 3 placeholder. It commits to:

- **The six hard problems** that make an options wing months-not-weeks: historical
  chain data (paid, 100–1000× the data volume — the blocker), pricing/marking
  (American + dividends → binomial, IV surface), per-contract cost bricks (with
  D65-style published-schedule X-gates), Reg-T margin formulas (why
  `margin_requirement` raises today), **expiry/assignment lifecycle** (the deepest
  engine gap: D45's inner-join alignment silently truncates the whole portfolio at
  the shortest-lived contract's expiry — finite-lived instruments are a genuinely
  new engine concept), and delta-aware risk (D57's notional-based exposure misstates
  options).
- **The Lego audit**: what bolts onto existing sockets (Instrument protocol,
  DataSource, per-class cost stacks per D13, configs per D52, snapshots per D24,
  dividend tables per D75) versus what is real engine surgery (time-varying
  instrument universe, lifecycle events, pricing layer).
- **Verification gates if ever built**, in this framework's own X/G/U/P style —
  including hand-computed Reg-T margin goldens and an expiry-day golden master.
- **Trigger conditions**: pairs writeup complete (R1) AND put-spread thesis still
  live AND data budget re-quoted and accepted. Effort estimate at trigger: 6–10
  weeks at the project's cadence. Vendor prices in the doc are labelled estimates to
  re-quote, not commitments.

Enforced against rot by a grep-test (`test_options_extension_doc_...` in
`test_instruments.py`) — the same discipline as D38/D82's labels: the stub banner
must stay gone and the load-bearing sections must stay present. The Step 11 U-gate
(stub fields, multiplier math, honest NotImplementedError, nothing else claiming to
work) has been green since Step 3 and is unchanged.

## Rationale

D16's own words: "a committed shape + written scoping rationale reads as maturity; a
half-built module reads as sprawl." The stub supplied the shape in Step 3; this
write-up supplies the rationale with enough specificity to be checkable — a reviewer
can disagree with the effort estimate or the margin-formula scope, which is exactly
what makes it a real scoping document rather than a hand-wave. One notable finding
from writing it: the expiry-lifecycle problem is *bigger* than D16's list implied
(D16 named "margin, pricing, Greeks, assignment"; the time-varying instrument
universe breaks an alignment assumption three layers down), which is the kind of
thing you only learn by scoping honestly.
