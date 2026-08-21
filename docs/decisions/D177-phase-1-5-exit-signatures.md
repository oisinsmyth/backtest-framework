# D177 — Phase 1.5's exit signatures: E1 survives, E2 was never actually built, E3 is logged only

**Status:** Committed
**Date:** 2026-08-21
**Category:** Signals & strategy interface
**Source:** Completing `BREAKOUT_REVERSAL_FEATURES.md`, whose feature half shipped in Phase 1.1 and whose exit half did not

## Decision

The three exit signatures the features doc specifies are now built to spec and reported:

- **E1 — `FailedBreakoutExit(k)`**, new. Exits when the close falls back INSIDE the channel
  the entry broke, within `k` bars. `k ∈ {2, 3}`.
- **E2 — `TimeStopExit` gains `mfe_atr`**, so it can be the rule the doc specifies rather
  than an approximation of it.
- **E3 — logged, never acted on**, per the doc's explicit instruction.

Plus the diagnostic E2's spec requires as a precondition: MFE-by-bar, and the baseline's
MFE-vs-time distribution in the report.

## The two findings from the audit, which came before any code

**E1 had never been built.** The doc calls it *"highest priority"* and names it a predicted
survivor alongside F1. Protocol §4 explicitly permits building it immediately, unlike the
entry-side features. It was simply skipped.

**E2 existed but was not E2.** `TimeStopExit`, built for the short book under D169, exits
when the position is *"not in profit"* — the current close not beyond the entry reference.
The spec is *"has not achieved MFE ≥ 1 ATR within n bars"*. A trade that spiked +1.5 ATR
and came back to flat is **exited by the built rule and retained by the specified one**.
The short book's own wording ("a short not in profit within 3–5 bars") is what got
implemented, which was right for that book and is not E2.

Rather than change the rule's meaning underneath the published short results, `mfe_atr`
defaults to `0.0` (today's behaviour) and the new keys are emitted from `config()` only
when non-default — the D166 compatibility rule, applied a fourth time.

## What the study found

**E1 works, on both symbols, and it is the first prediction in that document to hold.**

| Variant | Δ Sharpe BTC | Δ Sharpe ETH | Trades (BTC/ETH) | Decision |
|---|---|---|---|---|
| `exit_e1_k2` | +0.058 | +0.177 | 44 / 30 | **KEEP** |
| `exit_e1_k3` | +0.101 | +0.177 | 44 / 30 | **KEEP** |
| `exit_e2_n5` | −0.010 | −0.167 | 47 / 34 | DROP |
| `exit_e2_n7` | +0.005 | −0.182 | 45 / 34 | DROP |

Scored by the every-symbol rule the filter increments already use. E1 clears it at both
`k`; E2 fails at both `n`, and fails hardest on ETH.

**Why E1 differs from everything else this project has tested.** Every previous
trade-touching device — four entry filters, three of six stops — removed trades and
removed good ones along with bad. **E1 does not reduce the trade count; it raises it**
(38 → 44 on BTC, 28 → 30 on ETH). It cuts a failed trade early and the strategy re-enters
on a fresh trigger. It is a trade-*shortening* device that is also a re-entry-*enabling*
one, and that asymmetry is exactly what the doc's rationale described: *"we cannot short
it, but we must not sit in it."*

**E2's own prerequisite explains why E2 fails.** The doc requires n be validated against
the baseline's MFE-vs-time distribution first. Only **26% (BTC) and 43% (ETH)** of trades
reach 1 ATR by bar 5, and 29% / 43% by bar 7. So E2 at these thresholds cuts roughly
two-thirds of the book on BTC — including the trends that pay, since a breakout that takes
its time is not thereby a failed one. The validation the doc demanded would have predicted
this before the run.

## A counting bug the report's own arithmetic caught

The first MFE-vs-time table printed ETH at **43% by bar 5 and 39% by bar 7** — impossible,
since MFE-by-bar is monotone non-decreasing, so the rate cannot fall as the window grows.

The cause: trades that closed before bar *n* were excluded from bar *n*'s numerator via a
`len(series) >= n` guard, while sharing a denominator with bar 5. A trade that closed on
bar 6 having already reached 1 ATR *did* reach it by bar 7. Fixed to read the best
excursion available up to bar *n*, and the report now **raises** if the rate ever falls
again — the impossibility was the only reason the bug was visible at all.

## Consequences

- E1 is a **KEEP by the stated rule**, and that is not the same as adopted. It is the 25th
  through 28th configuration on this book; the DSR pool grew 24 → 28 and every long-study
  DSR moved (BTC unchanged at 0.9998, ETH 0.9786 → 0.9748). Every pre-existing variant
  metric is byte-identical across 5,568 comparisons — only the deflation moved, which is
  the correct behaviour.
- **E3 makes no claim.** Post-entry range and volume are recorded on a new
  `TradeEpisode.trajectories` field and travel in the summary JSON. Turning *"declining
  range and volume while price grinds marginally higher"* into a rule needs a definition
  the doc does not give, and inventing one to fill the gap is the unregistered search the
  rest of the document exists to prevent. Volume became loggable only with D168.
- `trajectories` is a sibling of `features` rather than an extension of it: D167 pinned
  that map as scalars-or-None, and sequences do not belong in it. Recording slopes would
  have fitted the existing schema and discarded the shape the doc asks to preserve.
