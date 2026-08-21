# D174 — `swing_k2` tested on coins it was not fitted on: the stop survives, the strategy does not

**Status:** Committed
**Date:** 2026-08-21
**Category:** Validation & research integrity
**Source:** The out-of-sample test D173 named as the only thing that would make `swing_k2` believable

## Decision

`swing_k2` and `trail_10` are run **unchanged** across the D140 universe — 62 symbols
that passed a mechanical screen, built to contain the coins that failed rather than the
ones that survived. One configuration each, no per-symbol tuning (D141). The only question
asked is the one D173 left standing: does the challenger beat the incumbent, and does that
hold among coins that died?

`run_universe_study` gains an optional `variant` parameter so the short book reuses that
machinery rather than forking it. Default unchanged, so the published long-book universe
study is untouched.

## What it found

**The relative claim survives.** `swing_k2` beats `trail_10` on **43 of 62 symbols (69%)**,
median Δ Sharpe +0.049, and the win rate is above half in every survivorship cohort:
collapsed 29/41 (71%), delisted 2/2, survived 12/19 (63%). It is robust to dropping the
blown-up accounts (41/59, median +0.052).

That is the survivorship test passing, and it is the first evidence in this project that
an effect found on BTC/ETH is a property of the rule rather than of the two instruments.
It is evidence and not proof: these coins move together, so 62 symbols is far fewer than
62 independent tests.

**The strategy does not survive.** Median total return −50.5% for `swing_k2` and −56.1%
for `trail_10`; profitable on **5 of 62** and 6 of 62 respectively. `swing_k2` beats
`trail_10` on average while posting one FEWER profitable symbol — the shape of a rule that
trims the distribution's middle rather than finding winners.

Both statements are true and they must be read together: **the stop is real, the book is
not.** Nothing here changes the BTC/ETH deflated Sharpe of 0.04–0.54.

## The finding the test was not looking for

Three accounts lost more than everything — USTC −1105.7%, LUNC −167.1%, LUNA1 −149.5% —
with the stops active throughout. That is recorded separately as
[D175](D175-no-margin-call-or-liquidation-model.md), because it is a framework gap rather
than a result: the engine has no margin call, no liquidation and no borrow recall, so NAV
goes negative and the book keeps trading.

It is the most important thing this run produced, and it only became visible because the
universe contains instruments the project did not choose. That is the D140 argument
arriving in a form nobody predicted.

## Why the median leads and the mean does not

An unadjusted mean return over a cross-section containing a −1105% row is not an average
of anything. The report leads on the median, gives a mean excluding the blow-ups, and
names them. CAGR is emitted as `None` rather than `nan` where total return passes −100%,
because a `nan` in a results document is a number nobody has thought about — and the first
cut of this study did print one.

## Consequences

- The answer to "is swing structure worth pursuing" is **yes as a stop, no as a strategy**.
  It is the best stop found in this project and it improves a book with no demonstrated
  edge.
- **Adopting it still requires more than this.** The BTC/ETH evidence is best-of-25 and
  deflates to nothing; this test shows consistency, not profitability. A stop that makes a
  losing book lose less is worth having only if something else makes the book win.
- Borrow at a flat 10%/yr is generous for small-cap altcoins, where borrowing to short in
  size at the moment you want it is frequently impossible at any rate. That optimism is
  largest in the collapsed cohort, which is where the short book looks best.
