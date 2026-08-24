# STRUCTURE_MODEL.md — mechanising a discretionary price-action strategy

**Status:** Pre-registration. Written and committed BEFORE any detector exists and before
any run. Recorded as D204.

Companion documents: `STRUCTURE_RESULTS.md` is the append-only results ledger and carries
the multiplicity count. This document is the spec and does not change once code starts —
an amendment gets its own dated section here and its own decision record, in the form
D144 and D198 used.

---

## What is being tested, and what is not

The object under test is a five-part discretionary day-trading strategy taught in a
YouTube course (transcript archived alongside this document). Reduced to its claims:

1. **Change of character (CHoCH).** Market structure is a sequence of confirmed swing
   highs and lows. An uptrend is higher highs and higher lows confirmed by a *break of
   structure* (a close above the prior swing high). The trend flips when price instead
   closes below the last confirmed higher low. That flip is the trigger.
2. **The flipped level.** The broken level becomes resistance where it was support, and
   price returning to it is a high-probability entry.
3. **The 61.8% Fibonacci retracement.** Price retraces the impulse leg to the "golden
   ratio" before continuing. The course attributes this to the Fibonacci sequence being
   "how the universe is coded", visible in seashells and facial symmetry.
4. **The fair value gap (FVG).** A three-bar sequence where bar 1's wick and bar 3's wick
   do not overlap leaves an imbalance; price returns to the gap's midpoint before
   continuing.
5. **RSI** as a supporting overbought/oversold filter.

The wrapper: stop beyond the swing extreme that defined the structure, target at the
opposite end of the range, claimed at 4R–8R and settled at ~5R. The stated edge is
arithmetic — at 5R a ~20% hit rate breaks even and ~30% is "highly profitable".

**What is being tested here** is whether each of these five components carries information
about forward price behaviour on BTC and ETH 15m bars, separately and in combination,
once each is written down mechanically enough that a machine can find it without a human
drawing the lines.

**What is NOT being tested** is the course's own evidence, which is worthless and is not
being replicated. Its validation method is manual TradingView bar-replay journalling, in
which the analyst draws the levels already knowing what price did next; its headline 5R
figure is a two-trade sample, one of which is invented on camera. Neither of those is a
weak study. They are not studies.

This distinction matters for how a positive result would have to be read: finding
information in a mechanised CHoCH would say nothing whatsoever about the course being
right, because the course's version is not the mechanised one.

---

## The prior, stated before the work rather than after

**It is bad, and three of the five components have already lost in a closely related
form.** The terrain programme spent 259 looks establishing that price-derived maps of
resting supply and demand carry no directional or reversal information on this data
(`TERRAIN_RESULTS.md`, D194/D200/D203). Its unifying mechanism was that inventory
accumulates below price exactly when price has been falling into it, so trading it fades a
decline — and **fading lost in every form measured**: 16 of 16 cells (D197), 16 of 16
(D199), 8 of 8 (D201), 11 years of 11 (D202).

Components 2, 3 and 4 here are all pullback-fade entries. They are entered *against* the
immediate move, into a zone defined by where price has recently been. That is the same
shape as the thing that just failed, and the prior is correspondingly poor.

Saying so now costs nothing. Saying it after the result costs credibility.

The one structural difference worth naming: the terrain sensors were *stateless maps*
read at every bar, whereas the CHoCH is an *event with a direction* and the entry is a
continuation trade in the direction of a completed flip, not a fade of an ongoing move.
Whether that difference is real is roughly the question WP3 asks about C1.

---

## Disclosures

### D1 — the S5/D196 overlap on the flipped-level component

C2 is the nearest neighbour of the S5 swing supply/demand sensor, which scored **0 of 20
cells** against its null (D196). The two are not the same object:

- S5 built **bands** from `MIN_SWINGS >= 2` repeated pivots and killed a band permanently
  on a close through it. `terrain_swing`'s docstring is explicit that the flip was
  deliberately excluded: *"The trader's 'support becomes resistance' flip is a DIFFERENT
  hypothesis and is deliberately not implemented — smuggling it in would test two ideas
  while reporting one."*
- C2 uses **one specific broken swing, precisely because it was broken**, and trades the
  flip that S5 declined to implement.

So this is the hypothesis D196 named and set aside, and the stop on S5 does not bind it.
The distinction is real but thin. **If C2 is the only surviving component, D196's 20 looks
are inherited into this programme's ledger**, because in that world the two studies are
reading the same swing structure and it would be dishonest to price only one of them.

### D2 — none of C1, C3, C4 exists anywhere in the repo

`grep -rniE "fair.?value.?gap|fibonacci|retracement|change of character|choch|break of
structure|golden ratio|\bfvg\b"` over `src`, `scripts`, `docs`, `tests` and `New Docs`
returns zero hits. This is a new construction, which is the condition
`TERRAIN_RESULTS.md` sets for opening a new document and a new ledger.

### D3 — nothing has been seen

Unlike D196, no cell of this programme has been run, and no number from it has been
observed. The predictions below are written blind. If that changes before the run — a
sizing measurement, a debug print that shows a result — it gets stated here in the form
D196 used, and the predictions are re-read in that light rather than quietly kept.

### D4 — a calibration note, carried forward from D199

> I predicted at HIGH confidence twice that a refinement would fail its baseline and was
> falsified both times.

Baseline-relative predictions in this document are therefore capped at **moderate**
confidence. Null-relative predictions are not affected — those have been well calibrated.

---

## The mechanical definitions

Fixed here, before the code exists, so they cannot be adjusted once a verdict is
unwelcome. This is the same requirement `terrain_nulls.py` imposed on the touch and
reversal definitions, and for the same reason.

Throughout: bars are 15m `TimestampedBar`s; `ATR` is
`terrain.rolling_mean_true_range(bars, ATR_WINDOW)` with `ATR_WINDOW = 1_920` (20 days at
96 bars/day, the calendar match D194 fixed); `HORIZON = 5` bars, inherited from
`terrain_nulls.HORIZON`, itself `breakout_study.E2_N`.

### The confirmation lag, which is where every one of these leaks if you are careless

D173 solved this once and the reasoning is quoted because it is the whole risk:

> A pivot at bar t cannot be recognised until bar t+k, because it needs the k bars after
> it. A naive implementation that labelled pivots on the visible series without that
> offset would be reading k bars into the future — and it would leak INVISIBLY, because
> the equity curve it produced would look entirely plausible.

Every state below is computed strictly from pivots **confirmed at or before** the index
being evaluated. A detector is analytics, not a strategy, so it does not inherit
`DataView`'s structural guard — D181 is the record of what assuming otherwise cost — and
the no-look-ahead property is therefore asserted directly by test.

### C1 — market structure (BOS / CHoCH)

Pivots come from `terrain_swing._is_swing_bars` / `confirmed_pivots`, unchanged, at
half-width `k`. Strict and unique: equal extremes produce no pivot.

State machine, evaluated bar by bar, using only confirmed pivots:

- **`BOS_up` at bar `t`**: `close_t` closes above the most recent confirmed swing high,
  while `trend` is `up` or `none`. Sets `trend = up`. Mirror for `BOS_down`.
- **`CHoCH_down` at bar `t`**: `trend == up` and `close_t` closes below the most recent
  confirmed **higher low** — that is, the last confirmed swing low that was itself higher
  than its predecessor and was followed by a `BOS_up`. Sets `trend = down`. Mirror for
  `CHoCH_up`.
- A CHoCH is the trigger. A BOS in an already-established trend is continuation and is
  counted but does not trigger.

Emitted per bar: `trend ∈ {up, down, none}`, `choch_index`, `choch_level` (the price of
the broken higher low / lower high), `bars_since_choch`, and `impulse_leg` =
`(start_index, start_price, end_index, end_price)` for the first leg after the CHoCH — its
start is the CHoCH extreme, its end is the first confirmed pivot of the opposite sign
after it.

### C2 — the flipped level

`choch_level` from C1. Feature: signed distance from `close_t` to `choch_level` in ATR
units. A "touch" uses `terrain_nulls`' definition unchanged — `|close_t − L| <= k_touch ·
ATR_t` with the previous bar outside the band, so a price sitting inside the band for a
week is one touch and not thirty.

**Broken is dead, permanently**: a close beyond the level in the pre-break direction
invalidates it and it does not return. Same convention as S5, stated explicitly so the two
studies are comparable.

### C3 — the Fibonacci retracement

Over C1's `impulse_leg`:

```
retracement = (leg_end − price) / (leg_end − leg_start)
```

signed so that 0.0 is the leg's extreme and 1.0 is its origin, in both directions. The
feature logged is the **continuous depth**, not a boolean. A "61.8% touch" is
`|retracement − 0.618| · |leg_end − leg_start| <= k_touch · ATR_t`, so the tolerance is
the same band C2 uses rather than a second free parameter.

**The 61.8 claim is only testable against a placebo ladder.** Testing 61.8 alone and
finding a reaction proves nothing, because *any* level partway into a retracement sits
where price has recently been. WP3 therefore measures 61.8 against:

- the other canonical ratios — **38.2, 50.0, 78.6** — and
- **non-canonical ratios at matched depths — 44.7, 55.3, 69.1, 72.4** — chosen now, before
  any run, to bracket the canonical ones without coinciding with any of them and without
  being derivable from the Fibonacci sequence, φ, or any round fraction.

If 61.8 has no advantage over an arbitrary ratio sitting at a comparable depth in the same
leg, the golden-ratio claim is dead and whatever effect exists belongs to *depth*, which
is a different and much more boring hypothesis.

### C4 — the fair value gap

Fully mechanical; this is the one component the course states precisely enough to
implement without interpretation.

- **Bullish FVG** at `t`: `low_t > high_{t−2}`. Gap is `(high_{t−2}, low_t)`.
- **Bearish FVG** at `t`: `high_t < low_{t−2}`. Gap is `(high_t, low_{t−2})`.
- Midpoint is `(lo + hi) / 2` — the 50% level the course trades.
- A gap is **filled, and dead**, when price trades through its far edge.

Only gaps formed **inside the impulse leg** identified by C1 are eligible, which is what
the course means by "if it aligns with my other general analysis". Gaps elsewhere are
counted in the census and not traded.

### C5 — RSI, the control

RSI(14) with Wilder smoothing, thresholds at the textbook 30/70. Not swept.

This is in the study as the **cheap control**, not as a fifth idea. If a plain oscillator
conditions outcomes as well as the three structural components, then the structural
components add nothing over a line of code from 1978, and that is the finding.

### The wrapper — frozen, and deliberately not a variable

Entry at the level; stop at the far side of the swing extreme that defined the structure;
target at a fixed R multiple; trailing stop once 1R in profit. Taken from
`terrain_strategies.bounce_rr` with `TARGET_R`, `TRAIL_AFTER_R`, `TRAIL_LOOKBACK` and
`MAX_HOLD` at their existing values.

**The wrapper is held constant across every arm of this study.** D202/D203 is the record
of why:

> Every refinement that changed the **wrapper** — entry timing, exits, stops, thresholds —
> improved the strategy against its own predecessor and left the null comparison exactly
> where the first fair test put it. The one refinement that changed the **statistic**
> (D202) fixed every defect named in its diagnosis and produced the **worst** result.

A wrapper sweep here would generate exactly that pattern again and it is already known.

---

## The pre-registered parameter sets

A value outside these sets is an unregistered search and the ledger counts every
combination tested.

| Parameter | Set | Source |
|---|---|---|
| Pivot half-width `k` | `{2, 3}` | D173's set, reused not re-chosen |
| Touch band `k_touch` | `{0.5, 1.0}` ATR | `terrain_nulls.TOUCH_ATR` |
| Fib tolerance | = one touch band | not a free parameter |
| Canonical ratios | `{38.2, 50.0, 61.8, 78.6}` | the course |
| Placebo ratios | `{44.7, 55.3, 69.1, 72.4}` | fixed here |
| RSI | 14 / 30 / 70 | textbook, not swept |
| `HORIZON` | 5 bars | `terrain_nulls.HORIZON` |
| `ATR_WINDOW` | 1,920 bars | D194's calendar match |
| Cost | 40 bps taker | `breakout_study` `taker_40bp` |
| `periods_per_year` | 35,040 | 96 bars/day × 365 |
| Symbols | `BTCUSDT`, `ETHUSDT` | matches every prior study |
| Bars | 15m, `crypto_binance_15m_raw.csv.gz` | committed fixture |

**The primary cell, named now:**
`BTCUSDT + ETHUSDT · 15m · k=2 · k_touch=0.5 · 40 bps · pessimistic fill`.
Everything else in this document is sensitivity and is labelled as such in the ledger.

---

## The hurdles

All required, on **both** symbols, for any component or arm to be called a survivor:

1. Beat its **matched placebo null** by ≥ **+0.10** Sharpe.
2. Beat the **rotation null** by ≥ +0.10 Sharpe.
3. Beat **buy-and-hold**.

**Every delta is reported with the null percentile beside it.** D202's lesson 5 is the
reason and it is a limitation this project found in its own method:

> A +0.10 delta over a null *mean* is not a hurdle when the null is wide — D201's
> statistic cleared it at the 67th percentile.

A delta that clears +0.10 while sitting below the null's p95 has not cleared anything.

---

## The work packages and their stop conditions

| WP | What it does | Stop condition |
|---|---|---|
| WP0 | this document, the ledger, D204 | — |
| WP1 | the five detectors + look-ahead / planted / false-positive tests | a failing no-look-ahead or random-walk test blocks everything downstream |
| WP2 | **the census — counts only, before any performance number** | fully-stacked arm yielding **< 30 entries per symbol** is reported as underpowered and carries no verdict; only WP4a proceeds |
| WP3 | each component alone against its own matched null, no costs | none — a component may be individually null and still marginally useful |
| WP4 | marginal contribution: feature quintiles (primary) + ablation lattice (confirmation) | **no component clearing the promotion criteria ends the programme here** as a reportable negative; WP5 does not run |
| WP5 | costed, both fill conventions, three hurdles, deflated Sharpe | — |
| WP6 | the discretion audit and the final report | — |

**WP2 exists because counts have repeatedly caught defects before they became results**
(D197, D198, D201, D202). D198's census rejected a proposed rule outright — 86% of signals
already had a second approach within 20 bars, so the "filter" was a one-bar entry delay
wearing a filter's name. A four-filter stack on 15m bars plausibly leaves a handful of
trades, and *"there is no sample"* is a legitimate and important finding about a strategy
sold as a repeatable daily process.

WP2 also computes, **before any backtest**, what the friction actually is. D196/D197 pin a
40 bps round trip at **0.49R at a 0.5-ATR stop** and **0.12R at 2 ATR**. Given the observed
median stop width the required hit rate follows by arithmetic, and it may end the study
without an experiment.

---

## Pre-registered predictions

Confidence is stated per D199's convention. Null-relative predictions at full confidence;
baseline-relative capped at moderate per Disclosure D4.

- **H1 — C1 (CHoCH) fails its rotation null on both symbols.** Confidence: **moderate.**
  This is the component with the best claim to being something other than a fade, and the
  rotation null is a hard control. Lower confidence than the rest because the mechanism —
  a directional event rather than a stateless map — is genuinely outside what terrain
  tested.
- **H2 — C3 (Fib 61.8) shows no advantage over the matched non-canonical placebo ratios.**
  Confidence: **high.** There is no mechanism by which 44.7% and 61.8% differ other than
  the number of people watching, and the depth confound explains any effect either shows.
- **H3 — C4 (FVG) fails against its displaced-band placebo.** Confidence: **high.**
- **H4 — C2 (flipped level) fails, consistent with D196.** Confidence: **high.**
- **H5 — the fully-stacked arm is underpowered**, i.e. fewer than 30 entries per symbol.
  Confidence: **moderate.** Four conjunctive filters on ~300k bars could go either way and
  the census is the point.
- **H6 — C5 (RSI) conditions outcomes at least as well as the best structural component.**
  Confidence: **moderate.** Stated so that "the fancy components beat RSI" is a claim that
  had to survive being predicted against.
- **H7 — the verdict is stable across `k ∈ {2,3}` and `k_touch ∈ {0.5,1.0}`.** Confidence:
  **low.** If it is not stable, the strategy is a judgement call wearing a rule's clothes,
  which is the most interesting outcome available and is what WP6 is for.

---

## Cross-cutting rules

- **`STRUCTURE_RESULTS.md` is the single ledger.** Append-only, dated sections, nothing
  above rewritten.
- **The multiplicity ledger never resets.** Retired and failed cells count. Terrain's 259
  is disclosed adjacent and counted separately, except for the D196 inheritance rule in
  Disclosure D1.
- **No scope additions mid-WP.** New ideas go to a parking-lot section of the ledger for
  triage between work packages.
- **A census before the document, and counts only.** Every WP that produces a verdict
  reports its counts first, in its own section, before any performance number appears.
- **Session hygiene.** Each session starts by reading this document and the current
  ledger, and ends by updating the ledger and the WP checklist.

## WP checklist

- [x] WP0 — pre-registration (this document, the ledger, D204)
- [x] WP1 — detectors and their tests (D205)
- [ ] WP2 — the census
- [ ] WP3 — components against their nulls
- [ ] WP4 — marginal contribution
- [ ] WP5 — costed verdict
- [ ] WP6 — discretion audit and final report
