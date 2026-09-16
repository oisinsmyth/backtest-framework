# D204 — the structure programme, pre-registered

**Status:** Pre-registered — written and committed BEFORE any detector exists
**Date:** 2026-08-24
**Category:** Validation & research integrity
**Source:** a YouTube day-trading course, and the condition `TERRAIN_RESULTS.md` closes with

> A result section will be appended and nothing above it edited.

## The decision

**A new research programme opens, with its own document, its own ledger and its own stop
conditions: mechanise the five components of a discretionary retail price-action strategy —
change of character, the flipped level, the 61.8% Fibonacci retracement, the fair value gap,
and RSI — and measure each separately and in combination on BTC/ETH 15m bars.**

Spec: `docs/specs/STRUCTURE_MODEL.md`. Ledger: `STRUCTURE_RESULTS.md`.

## Why this is a new programme and not a terrain refinement

`TERRAIN_RESULTS.md` closes with the condition that authorises it:

> A different data source, a different claim, or a genuinely new construction starts a new
> document and a new ledger, with this one disclosed.

`grep -rniE "fair.?value.?gap|fibonacci|retracement|change of character|choch|break of
structure|golden ratio|\bfvg\b"` over `src`, `scripts`, `docs`, `tests` and `docs/specs`
returns **zero hits**. Three of the five components do not exist here in any form.

The overlap that does exist is disclosed rather than argued away. The flipped-level
component is the hypothesis `terrain_swing`'s own docstring named and set aside:

> The trader's "support becomes resistance" flip is a DIFFERENT hypothesis and is
> deliberately not implemented — smuggling it in would test two ideas while reporting one.

So it is outside S5's stop, and the distinction — bands from repeated pivots that die on a
break, against one specific swing traded *because* it broke — is real but thin. The
pre-committed consequence: **if the flipped level is the only survivor, D196's 20 looks are
inherited into this ledger.** In that world the two studies are reading the same swing
structure and pricing only one of them would be dishonest.

## Why the prior is stated as bad, up front

Terrain spent 259 looks establishing that fading into price-derived structure loses in
every form measured — 16 of 16, 16 of 16, 8 of 8, 11 years of 11. Three of the five
components here are pullback-fade entries. That is the same shape as the thing that just
failed.

Saying so now costs nothing; saying it after the result costs credibility. The one
structural difference worth naming is that a CHoCH is a *directional event* rather than a
stateless map read at every bar, and the entry is continuation after a completed flip
rather than a fade of an ongoing move. Whether that difference is real is roughly what
WP3 asks.

## What the pre-registration fixes, before any code

1. **The five definitions, mechanically** — including the state machine's rule that only
   pivots *confirmed at or before* the evaluated index may be used. D173's lag is quoted in
   full because it is the whole risk: a detector is analytics, not a strategy, so it does
   not inherit `DataView`'s structural guard, and D181 is the record of what assuming
   otherwise cost. The property is asserted by test instead.
2. **The parameter sets and the named primary cell** — `k ∈ {2,3}` from D173,
   `k_touch ∈ {0.5,1.0}` from `terrain_nulls.TOUCH_ATR`, `HORIZON = 5`,
   `ATR_WINDOW = 1_920` on D194's calendar match. Nothing re-chosen that already exists.
3. **The three hurdles, with the percentile printed beside every delta** — D202's lesson
   that a +0.10 delta over a *wide* null's mean cleared the floor at the 67th percentile.
4. **A stop condition per work package**, including the one that can end the programme at
   analysis.
5. **Seven predictions with confidences**, four of them at high confidence that the
   component fails.

## Three design choices worth their own defence

**The wrapper is frozen across every arm.** D203 is the reason, and it is the single most
transferable finding the terrain programme produced: every refinement that changed the
*wrapper* improved the strategy against its own predecessor and left the null exactly where
the first fair test put it, while the one refinement that changed the *statistic* produced
the worst result of five. A wrapper sweep here would reproduce that pattern at the cost of
a few dozen looks, and the answer is already known.

**The Fibonacci test runs against a placebo ladder, not alone.** Testing 61.8% by itself
and finding a reaction proves nothing, because any level partway into a retracement sits
where price has recently been. So four **non-canonical ratios at matched depths** —
44.7, 55.3, 69.1, 72.4 — are fixed now, chosen to bracket the canonical ones without
coinciding with any and without being derivable from the Fibonacci sequence, φ, or a round
fraction. If 61.8 has no advantage over an arbitrary ratio at comparable depth, the
golden-ratio claim is dead and the effect belongs to *depth*. This is the cheapest decisive
test in the programme and it costs one run.

**RSI is in the study as a control, not as a fifth idea.** If a line of code from 1978
conditions outcomes as well as the three structural components, the structural components
add nothing. H6 predicts exactly that, so "the fancy components beat RSI" is a claim that
has to survive having been predicted against.

## The census requirement, restated

WP2 produces counts and nothing else, before any performance number exists. This is the
convention that has repeatedly caught defects before they became results (D197, D198, D201,
D202) — D198's census rejected a proposed rule outright once the counts showed 86% of
signals already had a second approach within 20 bars, making the "filter" a one-bar entry
delay wearing a filter's name.

Two things it produces here:

- **The funnel.** Entries surviving C1, then C1+C2, then +C3, then +C4. A four-filter
  conjunction on 15m bars plausibly leaves a handful of trades, and *"there is no sample"*
  is a real finding about a strategy sold as a repeatable daily process. Stop condition:
  under 30 entries per symbol and the stacked arm carries no verdict.
- **The friction, by arithmetic rather than experiment.** D196/D197 pin a 40 bps round trip
  at 0.49R at a 0.5-ATR stop and 0.12R at 2 ATR. Given the observed median stop width the
  required hit rate follows directly — and the course's claimed edge is precisely a hit-rate
  arithmetic argument, made with costs omitted entirely.

## What this programme is not

It is **not a replication of the course's evidence**, which is not weak evidence but
absent: its validation method is manual bar-replay journalling in which the analyst draws
the levels already knowing what price did next, and its headline 5R figure is a two-trade
sample with one trade invented on camera.

The consequence runs in both directions. A negative result here does not refute the course,
and — more importantly — **a positive result would not vindicate it**, because the
mechanised version is not the thing being taught. What is being measured is whether the
underlying claims survive being written down.
