# The price floor, and what a screen is actually for

[← cost index](00-index.md) · prev: [what anomalies pay](02-what-anomalies-pay.md) · next: [equal-weight bias](04-equal-weight-bias.md)

**The repo's floor is right. Its stated reason is the weaker of the two available.** Full
side-by-side at [vs repo R4](../conflicts/02-versus-repo-measurements.md).

---

## What the repo did, and why `[REPO]` — D339 / [FINDINGS §22](../../../FINDINGS.md)

The floor — **as-traded close at `t-1` ≥ `$5`** (the adjusted close times split ratios dated after
the bar; a floor on the *adjusted* close would look through future reverse splits) **AND** the dv28
pass — applied to the score **before ranking**, so the name is **REPLACED**.

Adopted on a **census run before the study**, not on an argument:

| | |
|---|---|
| books taking **more than half** their P&L below the floor | **25 of 47** |
| top trades that fail it | **35 of 47** |
| names supplying the top trade of 30 books | **nine** — VSA, TAOP, AHT, RLOC, PRMW, WATT, CYCN, KODK, DRYS |
| live name-bars the floor fails | **29.3%** |
| sub-`$5` share of the universe | **3% (2010) → 13% (2025)** |

**Three of four books improve; the fourth loses its fabricated-looking top trade.** *"The tail the
floor removes was not edge."* **Replace beats starve** — filling the vacated slot with the next
liquid name is worth **3–6 bp/bar** over dv28's hole.

## What the literature says about price screens `[EXT]` `J4`

| premise the programme carried | what `J4` measured |
|---|---|
| *"the `$5` screen is near-universal"* | **81.7% of studies impose no price filter at all**; published levels are **bimodal at `$1` and `$5`**, with **nothing above `$5` ever named** |
| *"cost in bp scales as `50/P`"* | **true of the COMMISSION, false of the SPREAD** |
| the floor is a cost lever | **relative spread is invariant to nominal price** away from the tick constraint — **11 of 12 matched tests insignificant** at the `$5`–`$20` boundary, matching NYSE commons on industry and market cap |

**The SEC states the mechanism itself:** away from the tick constraint, a price change leaves *"the
cost of transacting in the stock, for a given dollar exposure … constant."* **This programme's 33.8
bp/side names are ~7 ticks wide — nowhere near the constraint.** So both the 1992 tick-noise
justification and its modern practitioner replacement are **tick-constrained-regime arguments applied
to a population that is not tick-constrained.**

## The argument the repo should be making instead `[EXT]` `J4`

> **The `$5` screen is a SUBSTITUTE for value-weighting** — *"value-weighting … assigns only tiny
> weights to these stocks, which in turn do not need to be excluded."*
> **This programme is equal-weighted, so that substitution is unavailable: the floor does real work
> here that it does not do in the papers it was inherited from.**

**And [K5](04-equal-weight-bias.md) makes it quantitative:** the equal-weight bias's leverage on price
is **quadratic, ∝ 1/P²** — sharper than the repo's existing linear note.

## The closed form, and why it cannot be a design rule `[EXT]` `J4`

`P_min = 20000c / (g − s)`. At `$0.005`/share against a 67.6 bp round trip:

| assumed gross edge | defensible floor |
|---|---|
| 80 bp | **$8.06** |
| 75 bp | $13.51 |
| 70 bp | **$41.67** |
| ≤ 67.6 bp | **no floor works** |

**A 10 bp change in the assumed gross edge moves the floor by 5×.** And the lever is small: `$5`→`$10`
buys **10 bp** of round trip, `$5`→∞ buys **20 bp**, half of it in the first step. **The level IS
derivable from the cost model, and the derivation is too sensitive to the one input nobody knows to
serve as a design rule.**

## What the screen costs the signal `[CONFLICT D2]`

`A3`: the `$5` screen **cuts short-leg alpha 77% and the spread 68% while leaving the long leg
untouched.** `A2`: it **costs ~23% of the median premium**, and for share issuance **over half the
premium is in sub-`$5` names (1.06 → 0.48)**. **Different signals, opposite-pointing implications.
Both stand.**

## Two open questions, both cheap

1. **Does a held name falling through the floor get EJECTED or CARRIED to its delisting?** `[OPEN]`
   Settleable with no external data. **If carried, the Shumway delisting-return bias applies; if
   ejected, that is an undeclared stop-loss at `$5` truncating every trade's left tail.** Item 1 of
   [`../../README.md`](../../README.md) §"What is open".
   > `[EXT]` `H4` found **the reference implementation of the literature ejects** a held name that
   > falls through a `$5` screen on 12-month holds whose papers date the screen to formation — **and
   > says so nowhere in its prose.**
2. **No published work varies a price screen across levels** — every sensitivity in the literature is
   binary at `$5`. **The `$5`–`$10` band's contribution is unmeasured everywhere and measurable
   here.**

## The related premise that was wrong, kept because the correction is reusable

The commissioner's selection principle — *"killer 1 can ask about SIZE"* — **cannot**, because size
and per-share price come apart wherever an event requires a prior corporate state. `J2` measured
dividend **initiators at a median `$28.19` and cutters at `$28.45` — the same price.** *"Cutters are
small FIRMS whose STOCKS are not cheap, because you must have been a dividend payer to cut one."*

---

**Sources.** [`the-selection-round.md` §1.1, §1.10](../../the-selection-round.md) ·
[`the-timestamp-round.md` §1.6](../../the-timestamp-round.md) ·
[`Scan-100926/R1-99` `D2`](../../Scan-100926/R1-99-record.md) ·
repo: [FINDINGS §22](../../../FINDINGS.md), D339, D341.
