# D207 — two amendments to the structure pre-registration, before WP4 runs

**Status:** Committed — an amendment, written before the runs it governs
**Date:** 2026-08-24
**Category:** Validation & research integrity
**Source:** WP4/WP5 design, against `docs/specs/STRUCTURE_MODEL.md` (D204) and D206's census

`STRUCTURE_MODEL.md` states that it "does not change once code starts — an amendment gets
its own dated section here and its own decision record, in the form D144 and D198 used."
This is that record. Both amendments are written **before** the work packages they govern
produce a number, and one of them **removes a conservatism**, which is stated plainly
rather than buried.

---

## Amendment 1 — entry is a market order at the close, so D9's fill conventions do not apply

**Pre-registered:** *"Both `FillAssumption` conventions, pessimistic carries the verdict."*

**Amended to:** every arm enters at the **close of the entry bar**. The `FillAssumption`
sweep is replaced by a **cost-multiplier sensitivity** in WP5 (0.5x / 1x / 2x / 4x, D8's
harness), so the execution assumption is still swept rather than assumed.

### Why

Every condition in this programme is evaluated on the **close** — WP2's funnel, WP3's touch
statistic, `Setup.holds`. A limit order resting at a level is a different object from
"the close came within `k * ATR` of the level", and pretending otherwise would put a fill
model on top of a signal that was never defined in its terms.

The decisive reason is the ablation. **The C1-only arm has no level to rest a limit at.**
Its entry is the bar the impulse leg confirms, and there is no price to sit at. So a
limit-based design would make the base arm structurally different from every arm above it —
market entry against limit entry — and the difference between arms would no longer be *the
filters*. The whole point of `structure_setups.SetupPopulation` is that all arms share the
setups, the windows and the bands so that the filters are the only thing that varies. An
execution asymmetry at the bottom of the lattice would defeat that, and it would defeat it
invisibly, because a limit arm and a market arm both produce plausible trades.

### What this costs, stated rather than buried

**D196's adverse selection is not paid in this study.** That study measured D9's effect for
the first time in this project at **0.138–0.195 Sharpe**, 4 of 4 pairs, on a bounce
strategy — you are reliably filled on the levels price blows through and you miss some it
bounces off. A market-at-close entry does not have that problem; it has a different one,
the spread, which is what the 40 bps tier prices.

So this amendment **is not conservative-neutral**. It removes a real haircut that a
limit-entry version of this strategy would owe, and replaces it with a swept spread. Any
WP5 result must be read as "market-at-close execution", and a trader implementing the
course's actual limit-at-the-level method should subtract something in D196's range.

---

## Amendment 2 — the primary reward target is 5R, the course's own number

**Pre-registered:** *"Taken from `terrain_strategies.bounce_rr` with `TARGET_R` ... at
their existing values"* — that is, `(2.0, 3.0)`.

**Amended to:** primary `TARGET_R = 5.0`; `(2.0, 3.0)` retained as sensitivity.

### Why

The object under test is a specific claim, and the claim is arithmetic at 5R: *"two out of
ten breaks even, three out of ten is highly profitable."* D206's entire friction section is
built on 5R for that reason, and it is the number the course settles on after quoting 4R–8R.

Running the verdict at 2R and 3R would answer a question about a strategy nobody proposed.
Keeping terrain's pair as sensitivity preserves the precedent-anchored comparison, so the
change adds a value rather than replacing the set — and every value is counted in the
ledger.

The original wording was written to avoid re-choosing a parameter that already exists in
the repo. That instinct is right in general and wrong here: `bounce_rr`'s targets were
chosen for a bounce strategy on daily bars, and inheriting them would be reusing a number
because it was nearby rather than because it was the number under test.

---

## Consequence — the ablation lattice is 8 arms, not 16

D206 dropped C5 as a stacked filter on counts alone: RSI at 30/70 collapses the stacked arm
to **2 entries** on both symbols. So WP4b's lattice runs over `{C2, C3, C4}` — 2³ = 8 arms
— rather than `{C2, C3, C4, C5}` at 16.

**WP4b's multiplicity falls from 32 looks to 16.** C5 does not disappear from the study; it
is carried as a continuous feature into WP4a, where a rank correlation over 3,875 trades
still has power that a 2-trade arm does not.

---

## What is NOT amended

The statistic, the setups, the windows, the invalidation rule, the touch band, the pivot
widths, the symbols, the bars, the three hurdles, the percentile-beside-every-delta
requirement, and the stop conditions all stand exactly as D204 fixed them. **The wrapper is
still frozen across arms** — that is D203's finding and it is the constraint these
amendments are most careful not to touch: changing the target once, before any arm runs,
with the reason written down, is not the same thing as tuning an exit until a null moves.
