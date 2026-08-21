# D184 — Two unrecorded corporate actions, an events file that is empty, and four scripts that would ignore it anyway

**Status:** Committed
**Date:** 2026-08-21
**Category:** Data layer
**Source:** A benchmark returned +102,682,123% and the number was chased rather than reported

## What happened

Computing a buy-and-hold benchmark for D183 produced an equal-weight universe return of
**+102,682,123%**. A number that absurd is a defect report, not a result.

**It came from one bar.**

```
HT-USD   2025-03-11   close 0.0000150
         2025-03-12   open 0.0000150   high 0.5455   close 0.5098
         2025-03-13   close 0.4971
```

A **+3,398,300% single-day return**, after which the price simply stays near 0.50. The
series had been sitting at ~1e-05 — a scale roughly 34,000× below where it resumes. This is
a price-scale defect in the feed, not a market move.

Neutralising that **single bar** takes the benchmark from +102,682,123% to **+70,139%** — a
factor of **1,464×** from one day, because daily rebalancing compounds it across every
subsequent bar.

**A second one is a genuine corporate action:**

```
AAVE-USD  2020-10-02   open 0.0000   low 0.0000   close 0.5166
          2020-10-03   close 53.1515
```

That is the **LEND → AAVE 100:1 token migration** of October 2020: 0.5166 × 100 = 51.66,
against an observed 53.15. A redenomination, which changes the price scale and not the
holder's wealth — exactly what a split adjustment exists to handle. The preceding bar also
carries a **zero open and zero low**, which is its own data defect.

## Three separate problems, and only one of them is what it looked like

**1. The events file is empty.** `crypto_universe_2015_2025_raw_events.json` has
`dividends` and `splits` keys covering all 63 symbols, and **every single list is `[]`.**
Neither the AAVE migration nor anything else is recorded. The corporate-actions machinery
is present, wired, and has nothing to apply.

**2. Four scripts pass an empty `CorporateActions()` rather than loading the file.**
`run_swing_universe.py`, `run_e1_universe.py`, `run_combined_universe.py` and
`run_portfolio_universe.py` all construct their snapshot with `CorporateActions()`, where
every other study in the project calls `load_events_json(EVENTS)`. Three of those four are
mine, written this session; the pattern was inherited from D174's script.

**This changed no published number**, because the file it declines to load is empty. It is
a latent defect: the first time a real event is recorded, four studies will silently ignore
it. Fixed by loading the events file in all four, which is a no-op today and correct
tomorrow.

**3. The validator would have caught both and was deliberately overridden.** D143 records
the decision to override the >60% unexplained-single-bar-move gate for the crypto universe,
on the grounds that it was calibrated on ETFs and fires hardest on the tokens that genuinely
collapsed — and that respecting it mechanically would delete the failed assets and hand back
the survivorship bias the study exists to remove.

**That reasoning is still right, and this is its cost.** The override is not free: it admits
real data defects alongside real collapses, and D143 stated the principle without ever
listing what was let through. The gate's own verdict was reported in full; what nobody did
was look at the largest admitted moves and ask which were genuine.

## The strategy results are not contaminated, and it is worth being precise about why

| | Long portfolio return that day |
|---|---|
| 2025-03-12 (HT +3,398,300%) | **+0.0127%** |
| 2020-10-03 (AAVE +10,189%) | **+0.0860%** |

Nothing. The long portfolio's largest single-day return anywhere in the sample is +33.4%,
in 2017.

**The mechanism is D103's next-open fill.** A breakout entry triggers on a bar and fills at
the *next* open, so a one-bar gap cannot be entered — the strategy arrives after the jump.
Buy-and-hold, by contrast, holds through it and captures the whole thing.

**So the defect inflates the BENCHMARK far more than the strategy**, which is an unusual
direction for a data error and worth stating plainly: had this gone unexamined, it would
have made the strategy look *worse* against an impossible benchmark, not better. AAVE-USD
is not in the strategy universe at all — the policy screened it out on data adequacy, its
zero-priced bars included — so it affects only the benchmark.

## Consequences

- **D183's benchmark section neutralises both bars** and says so. The equal-weight
  daily-rebalanced row reads +70,139% (full span) and +813.3% (conservative span).
- **The four scripts now load the events file.** No number moves; the class of silent
  failure closes.
- **D143's override is now costed, not just justified.** Its reasoning stands. What this
  adds is that an override with no follow-up inspection is a decision to accept unknown
  defects, and the follow-up — read the largest admitted moves, decide which are real — had
  never been done.
- **Neutralising a bar is not adjusting it.** The honest fix for AAVE is a 100:1 split event
  in the events file, and for HT a scale correction or a screen. Both are data-collection
  work outside this session's scope, so the benchmark states its correction inline rather
  than pretending the underlying series is clean.

## The general lesson

**An implausible number in a benchmark is worth more attention than a plausible one in a
result.** The +102,682,123% was in a throwaway comparison, computed to contextualise
something else, and it exposed an empty events file, four scripts ignoring it, and an
uninspected validator override. A benchmark that had come back at a believable +9,000% would
have been quoted and the same three defects would still be there.
