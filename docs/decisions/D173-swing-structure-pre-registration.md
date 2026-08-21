# D173 — Swing-structure rules, and a pre-registered prediction that they will not work

**Status:** PRE-REGISTERED — implementation and tests committed, **study not yet run**
**Date:** 2026-08-21
**Category:** Validation & research integrity
**Source:** Follow-on to [D171](D171-the-stop-family-sweep.md) / [D172](D172-the-short-book-deflated.md)

> **This record is written BEFORE the study runs, and is committed in that state on
> purpose.** The predictions below are falsifiable and dated by git. If they turn out
> wrong, that is a real finding and this record will say so; if they turn out right, the
> value is that they were not written afterwards. A result section will be appended, and
> nothing above it will be edited.

## What is built

Market structure — the "higher high / higher low" reading of trend — as two mechanical
bricks:

- **`SwingStructureStop(k)`** — the stop sits at the most recent CONFIRMED swing pivot
  against the trade: last swing high for a short, last swing low for a long. Ratchets like
  every other stop since D171.
- **`SwingStructureGate(k)`** — an entry gate that admits a trade only when the last two
  confirmed swings agree: higher high **and** higher low for an uptrend, lower high **and**
  lower low for a downtrend. Anything else is **ambiguous, and ambiguous vetoes**.

`k ∈ {2, 3}` only, fixed before testing.

## Two design decisions that matter more than the rules

**Pivot levels, not drawn trend lines.** A sloped line through two chosen swing lows is a
*fit*: which two points, how often to refit, what to do when a third disagrees. Those are
free parameters, and `TERRAIN_MODEL.md` already rules out "discretionary zone drawing of
any kind" for exactly this reason. A horizontal pivot level is mechanical and
reproducible; a sloped line is where discretion re-enters through the back door. So this
is structure, not trend lines, and that is a deliberate narrowing of what was asked for.

**The confirmation lag is the whole design problem.** A k-bar pivot at bar *t* cannot be
recognised until bar *t+k*, because it needs the k bars after it. An implementation that
labels pivots on the visible series without that offset reads k bars into the future — and
leaks *invisibly*, because the equity curve it produces looks entirely plausible. The
DataView would catch a crude version that indexed past the present; it cannot catch one
that computes pivots from visible bars and forgets the lag. `last_swings` never considers
a bar newer than `index - k`, and `tests/unit/test_swing_structure.py` asserts a specific
pivot is invisible at *t* and *t+k−1* and visible at *t+k*.

That lag is also why this rule is **strictly slower** than a channel stop of the same
nominal length, which is the basis of the prediction below.

## The predictions

Measured on the short book at `taker_40bp`, scored by the same every-symbol rule the long
study fixed before looking, with `SHARPE_EPS = 0.01`.

**H1 (primary, and the reason this is called a negative test).** The swing-structure stop
will **not** beat `trail_10` on both symbols — it will fail the every-symbol rule.

Two independent reasons, both measured before building:
1. **Redundancy.** Median swing spacing on this data is 7 bars at k=2 and 9 at k=3. A
   structure stop therefore places its level at roughly the distance `trail_10` already
   places its own, so it is largely the same device with extra machinery.
2. **Staleness.** The k-bar confirmation lag means the level is at least k bars old by
   construction, where `trail_10` uses the most recent bar. Slower, for the same distance.

**H2.** The structure gate will **not** improve on the SMA200 regime gate alone. The
regime gate already holds bull-market exposure to about 1%; the gate is not what is
broken. The entry rule is — it sits at the 51st percentile of its null on BTC. And every
trade-removing device this project has tested (four entry filters in the long study, three
of six stops in D171) has removed good trades along with bad.

**H3 (near-certain, stated to make the cost explicit).** Deflated Sharpe will **not** reach
0.95 on either symbol. The pool grows from 21 configurations to 25, and the incumbent best
already deflates to 0.039–0.515 (D172). Adding four configurations to a book with no
demonstrated edge lowers every DSR in it.

**What would falsify H1**, and I would report it plainly: a structure stop that improves
annualised Sharpe by more than 0.01 against `trail_10` on **both** symbols. That is the
same bar every other candidate in this project has had to clear.

## Multiplicity, paid up front

Four new configurations (stop k∈{2,3}, gate k∈{2,3}) × 4 tiers × 2 symbols = 32 new
out-of-sample trials, taking the study from 168 to 200 and the DSR pool from 21 to 25 per
cell. Every one is registered under `breakdown-v1` and enters the pool. **A configuration
tried and learned nothing from still costs a look** — the pool is not reduced for a
variant that turns out inert, as `trail_20` already demonstrated.

This cost is worth paying only because D172 closed the deflation gap first. Run before
that, these four would have produced raw numbers with no way to price the search that
produced them.

---

# RESULT — appended 2026-08-21, after the run. Nothing above this line was edited.

**Status: H1 FALSIFIED. H2 and H3 hold.**

## H1 was wrong, and the way it was wrong is the useful part

`stop_swing_k2` beats `trail_10` on **both** symbols, clearing the every-symbol bar:

| | Δ Sharpe BTC | Δ Sharpe ETH | Verdict |
|---|---|---|---|
| `swing_k2` vs `trail_10` | **+0.100** | **+0.093** | beats it |
| `swing_k3` vs `trail_10` | +0.008 | +0.037 | does not (BTC below the 0.01 floor) |

The prediction said no structure stop would clear that bar. One did, decisively, and it is
also the first stop in this project to improve **both** symbols substantially — `trail_5`
gained +0.279 on BTC and nothing on ETH, while `swing_k2` gains +0.244 and +0.161 against
the baseline.

**Where the reasoning went wrong.** The redundancy argument compared *swing spacing* (9
bars at k=3) to *channel lookback* (10 bars) and concluded the two devices place their
levels in the same place. **Spacing ≈ lookback does not imply level ≈ level.** A swing
pivot is a LOCAL extreme; after a favourable move it sits far closer to price than the
rolling N-bar extreme, which still carries the pre-move high in its window. The adaptivity
is real and I priced it at zero.

Note the prediction *did* hold for k=3 (+0.008 on BTC is inside the noise floor) — which is
exactly the case whose spacing I reasoned from. The mechanism was right; it was applied to
the wrong parameter. Reasoning from one member of a swept set to the whole set is the
error, and it is worth naming because it looked like careful mechanism-based inference at
the time.

## H2 holds

Neither gate improves on the plain baseline across both symbols: `gate_k2` gives −0.066 /
−0.006, `gate_k3` gives +0.168 / −0.165 — opposite signs, the classic coin-flip failure.
The mechanism is visible in the trade counts, which fall from ~35 to 10–14. A second gate
is another trade-removing device, and it removed good trades along with bad, as every such
device tested in this project has.

## H3 holds, and it is what governs the reading

DSR with the pool now at 25 configurations: **BTC 0.037–0.088, ETH 0.392–0.538.** Nothing
near 0.95. And the variant DSR selects as best is still `stop_trail_5` on BTC and
`short_40_5` on ETH — **not** `swing_k2`.

So H1's falsification does not rescue the book. `swing_k2` is a genuine improvement over
`trail_10` and simultaneously the 25th configuration tried on a strategy with no
demonstrated edge. Both statements are true and the second dominates: **adopting it on
this evidence would be selecting the best of 25 looks, which is precisely what the
deflation exists to price.**

## What would make `swing_k2` believable

Not another sweep on this data. It needs to hold on instruments this study did not choose
— the crypto universe fixture already exists (D140) and contains assets that died — and
its own multiplicity would have to be counted afresh there. Until then the honest
description is: *a structure stop that beat one incumbent on two symbols, inside a book
whose deflated Sharpe is under 0.10 on one of them.*
