# D461 — stage 0: is prop-firm FORCED FLOW visible at the flatten minutes?

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file.
**STAGE 0: NO RETURN IS READ.** Volume only, and three abandon conditions declared below before
any number is looked at.

## 1. The claim, and why it is not the order-flow lane

**Prop-firm rules FORCE positions flat at fixed clock minutes.** These are not discretionary trades
— they are mandated by terms this programme has already read from primary documents:

| venue | the rule | ET minute |
|---|---|---|
| **Topstep** | flatten at **3:10 PM CT**; the daily loss limit *"flattens open positions"* on breach | **16:10** |
| **MyFundedFutures** | the 18:00 → **16:10 ET** window `BOOK_PROP.md` is built on | **16:10** |
| **Apex** | trading day runs 6:00 PM ET → **4:59 PM ET**; the EOD threshold is *"recalculated once per trading day at 4:59:59 PM ET"* | **16:59** |

**Why this is not [lane 21](../research/Prop-Firm-080926/21-order-flow-microstructure.md), which is
closed.** That lane settled the tape-reading version on four independent measurements: the horizon
is **about one second**, the predictable move is **a fraction of one tick**, and a taker's round
turn is **1.32–1.80 ticks** — *"there is no horizon where the edge exceeds the cost."* **This is a
scheduled calendar-clock effect at a known minute**, which is the horizon this programme trades and
can pay for. **Different object, different arithmetic.**

## 2. The window, and why it is the favourable one

**16:00–17:00 ET, the hour after the cash close.** Futures trade it; it is thin; and CME halts at
17:00. **Forced flow is maximally visible against a thin tape**, which is the only reason a small
participant class could show up at all.

## 3. The statistic, and why it is a RANK

For each minute `m` in 16:00–16:59, **the share of that hour's volume falling in `m`.** Then the
**rank of the target minutes among all 60.**

> **A rank, not a threshold, because a threshold is a number I would be choosing.** The target
> minute must stand out from a distribution of **60 placebo minutes** measured the same way. This
> is the same discipline as censusing a value that must return zero.

## 4. Three controls, declared

| | destroys | keeps |
|---|---|---|
| **INSTRUMENT** — MES against ES | the prop population (accounts trade MICROS; institutions trade minis) | the minute, the hour, the era |
| **ERA** — ES 2010–2018 against ES 2019–2026 | the prop industry's scale (MES lists from **2019-05**, so the micros cannot be tested before it; ES can) | the instrument and the minute |
| **PLACEBO MINUTES** — all 60 | nothing; it is the reference distribution | |

## 5. THE CONFOUND THAT DECIDES WHICH MINUTE CAN IDENTIFY, named before the run

> **16:59 is the last minute before the 17:00 CME halt. ANY position-squaring before a daily halt
> lands there, prop or not.** Its elevation is expected for reasons that have nothing to do with
> Apex, so **16:59 is reported and CANNOT identify.**
>
> **16:10 is the clean test.** Nothing structural happens on CME at 16:10. If forced flow is
> visible anywhere, it is there.

## 6. Abandon conditions — declared before any number is read

- **A1** — **if neither target minute ranks in the TOP 5 of 60 by volume share in MES 2019–2026,
  ABANDON.** The premise is that this flow is visible; if it is not in the top 8% of minutes in the
  thinnest hour of the day, it is not visible and nothing downstream is worth building.
- **A2** — **if MES's rank is no better than ES's at the same minute, ABANDON as a prop-flow
  hypothesis.** The micro/mini split is the only instrument-level identification available.
- **A3** — **if ES 2010–2018 ranks the same as ES 2019–2026 at 16:10, ABANDON.** The effect must be
  NEW. Prop firms scaled after 2019; an anomaly as old as 2010 is something else.

**A1 ∧ A2 ∧ A3 must all survive for this to continue to stage 1.** Any one failing ends it.

## 7. Predictions

- **Q1** — **A1 FAILS and the lane ends here.** Funded accounts are a small share of even MES
  volume; most funded traders are discretionary and never hold to a flatten; and lane 13 found
  **187 of 188 calendar anomalies in index futures dead** (Carchano & Pardo). **This is the
  honest prior and I expect to be reporting a negative.**
- **Q2** — **16:59 ranks far above 16:10 regardless**, because of §5's halt confound, and that
  ranking will look like support while identifying nothing.
- **Q3** — ES 2010–2018 already shows structure in this hour, because the 16:00–17:00 window has
  always carried cash-close-related squaring.
- **Q4** — if anything survives, it is in **MES and MNQ and not in M2K or MYM**, because prop
  accounts concentrate in the two liquid micros.

## 8. Not in scope

**No return, no signal, no strategy, no cost model.** Volume shares and ranks only. **Nothing here
opens or admits anything** — under [R15](../RULES.md#r15) that is the principal's call, and a
stage-0 that clears its abandon conditions earns a stage 1, not a candidate.
