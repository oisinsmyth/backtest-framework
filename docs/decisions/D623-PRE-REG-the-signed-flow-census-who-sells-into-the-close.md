# D623 PRE-REGISTRATION — the signed-flow census: who actually sells into the close, and is it a cascade?

*Committed before the runner exists (R8). A CENSUS: no return is scored, no strategy is built, no slice is
spent for a return-bearing construction. On the principal's word of 2026-09-22 to settle the mechanism.*

## 0. Why a census, and why now

[D622](D622-STAGE-0-RESULT-the-hour-is-specific-and-it-does-not-revert.md) established that something is
specific to 14:00 → 15:00 → 16:00 on the equity index roots — the family maximum of 21 hour pairs, absent on
five non-index roots, with a closing-hour volume share three points above normal at **t 7.93** — and could
not say what it is. Every discriminating margin came back inside two standard errors, and **four rounds of
subgroup analysis on the same 182 sessions produced no cell reaching 2 SE.** More conditioning will not help:
each round lowers the value of the next.

The principal named the counterparty and the mechanism: **retail traders, and a stop-hunting cascade**, with
the midday volume burst as the detection regime. That framing is testable, and it is testable on *flow*
rather than on *price* — which matters, because a flow census has thousands of observations per session where
a return test has one. **This is the only remaining step that adds information rather than looks.**

**What is already ruled out, so the census asks only what is open.** The
[prop-firm version is dead at premise](../internal/User-Doc-Deposit/PROP_LIQUIDATION_CASCADES.md): funded
accounts are overwhelmingly simulated, the firm is its own traders' counterparty, and those forced exits
produce no volume in the real book. [D530](D530-avenue-3-closed-the-leveraged-ETF-reset-flow-is-real-and.md)
closed leveraged-ETF reset flow, which is symmetric in the day's return and therefore cannot produce
direction. And the level-clustering a cascade implies has failed to appear twice — D622's P6 on the prior
session's low (unresolved, three central measures disagreeing) and
[D483](D483-RESULT-the-channel-is-not-the-ingredient-a-close-4pc-below-the.md) on the principal's own 140
hand-drawn lines (−2.2 bp). So the census tests the **flow signature** and nothing else.

## 1. The data already exists, which is why this costs nothing to run

`data/fixtures/fut_micro_flow_5m.csv.gz`
([D485](D485-RESULT-the-micro-crowd-is-only-half-distinct-trades-no-smaller.md)) already holds **signed
five-minute order flow from the CME `tbbo` tape using the exchange aggressor side**: 283,248 rows,
**259 sessions, 2025-09-11 → 2026-09-10**, for **ES, MES, NQ and MNQ**, carrying per bucket the buy-initiated,
sell-initiated and unsigned volume, the trade count, the small-lot volume (`lot1`, `lot_le2`), the at-bid and
at-ask counts and the aggressor agreement rate, which its gate T1 puts at **0.99999**.

**No decode is required and nothing is fetched.** The 37.3 GB tape was already paid for and read.

### 1a. D485's own reserve, which this census must not spend

D485 declared **206 sessions to 2026-06-30 as its in-sample window and left the remainder unread**. This
census therefore runs **only to 2026-06-30** and leaves 2026-07-01 → 2026-09-10 alone. That costs perhaps a
quarter of the arm sessions and is not negotiable: a reserve declared by one line is not available to another
just because the question differs.

### 1b. And D485 has already answered most of Q3 and Q4 in the unconditional case

Its title is the finding: *the micro crowd is only half distinct, **trades no smaller than the E-mini
crowd**, leaves **no flatten fingerprint**, and its excess flow clears no family bar.* So unconditionally the
micro contract carries no smaller trades and no deadline fingerprint. **Q3 and Q4 are therefore asking a
narrower question than they appear to**: not whether micro traders are distinct in general — that is answered,
and the answer is barely — but whether the small-lot share and the MES–ES gap move **on arm sessions
specifically**. That is new, and it is a much weaker prior than it would be without D485.

## 2. The slice, and the authority for reading it

The window is the reserved 2024+ slice. Two things make this admissible and both are recorded rather than
assumed:

1. **the principal's instruction of 2026-09-22** to settle the mechanism — that is the authority under R15;
2. it is read as a **non-return census in D510/D511's shape**, which read this same window for a quote and
   trade-count census and recorded it **still unspent for every return-bearing construction**.
   [D617](D617-FIXTURE-the-ES-option-signed-flow-census-from-the-tbbo-year.md) made the same declaration for
   the option tape. This record makes it a third time.

**Enforcement.** The runner asserts that no column it emits is a return, a P&L or a price change over the
scored window, and that the only price fields it reads are used to *classify sessions*, never to score one.
A declared-output guard lists the permitted column names and raises on anything else.

## 3. The arm, restated on the census window

Identical to D622's, on the same clock, with the threshold declared there: `H1 = r(14:00→15:00)/σ`, and an
**arm session** is one with `H1 ≤ −1.0`. On the **206 sessions to 2026-06-30** (§1a) that is expected to be
roughly **15–20 sessions**, which would be hopeless for a return test and is ample for a flow test: each arm
session contributes twelve five-minute buckets in the 15:00–16:00 window and thousands of trades.

`σ` is the trailing standard deviation of the hourly move. Because the census window is only a year, the
runner computes it from the fixture's own bucket returns and **reports the count of arm sessions before any
comparison**; if fewer than 12 qualify the census reports that and stops rather than straining.

## 4. The five questions, each with a declared direction and a declared failure

**Q1 — IS THE CLOSING FLOW ONE-SIDED?** The premise of every forced-seller story. On arm sessions, the
15:00–16:00 signed imbalance `(sell − buy) / (sell + buy)` must be **positive** — net sell-initiated — and
larger than on non-arm sessions. *Fails* if the imbalance is symmetric, which would mean nobody is being
forced out in that window and both the inventory and cascade stories are wrong.

**Q2 — DOES IT ACCELERATE INTO THE DEADLINE?** A cascade and an inventory deadline both predict the imbalance
**building** across the twelve buckets of the closing hour, strongest in the last two. Measured as the slope
of imbalance on bucket index, and the last-two-buckets minus first-two contrast. *Fails* if the imbalance is
flat or front-loaded.

**Q3 — IS IT SMALL LOTS?** This is the principal's counterparty, tested directly. `lot1` and `lot_le2` give
volume in one-lot and ≤2-lot trades. If retail stops are firing, the **small-lot share of sell-initiated
volume must rise** during the trigger hour and the closing hour on arm sessions, relative to both non-arm
sessions and the same session's own midday baseline. *Fails* if the small-lot share is flat or falls — which
would mean the selling is institutional, and the named counterparty is wrong even if the mechanism is right.
**D485's caveat is respected:** it established that the *micro contract* is not a retail identifier; lot size
*within* a contract is a different and better proxy, and the census reports both so the two are not conflated.

**Q4 — MES AGAINST ES.** If the forced sellers are retail, the imbalance and the small-lot effect should be
**more extreme in MES than in ES**. *Fails* if MES and ES behave alike, which would put the flow in the
institutional contract. Reported for NQ/MNQ too, since D622's cross-section found NQ the largest effect.

**Q5 — THE DETECTION REGIME.** The principal's midday volume burst, defined exactly as in D622 §5b (midday
volume over its trailing 20-session median, threshold 1.25). On arm sessions, does a midday burst predict a
**larger** closing imbalance? *Fails* if burst and non-burst sessions have the same imbalance — which would
mean the burst detects nothing about who is positioned, and its apparent price effect was noise.

**Every comparison is judged by D373's rule**: a margin inside two standard errors is **UNRESOLVED**, not a
pass and not a fail. The runner emits that as a category. Medians and both-tail trims are reported beside
every mean, and the sessions carrying each tail are named (D322). Those two disciplines are in this record
because their absence is what D622 had to be amended for.

## 5. What the census cannot do

It cannot establish that the *price* effect is caused by the flow it measures — that needs returns, and no
return is scored here. It cannot identify a retail participant directly; lot size is a proxy with an
unmeasured error rate, and the census says so rather than treating small lots as retail. And a year of data
gives ~20–25 arm sessions, so a *between-session* comparison is weak even where the *within-session* flow
comparison is strong; the runner reports both and labels which is which.

## 6. Disposition, declared in advance

- **Q1 fails** → nobody is forced out in the closing hour; the inventory and cascade stories are both wrong
  and the mechanism question closes.
- **Q1 and Q2 pass, Q3 and Q4 fail** → something is forced out and it is **institutional, not retail**. The
  mechanism survives and the principal's named counterparty does not, which is a specific and useful result.
- **Q3 and Q4 pass** → the counterparty is small-lot, concentrated in the micro contract, and the retail
  cascade has its first direct evidence. That would justify a pre-registered return test on a slice not yet
  read — which does not exist for this window, so it would justify **buying new data**, and the record would
  say so rather than reusing this one.
- **Everything unresolved** → the census is reported and the mechanism stays unidentified. Given ~20–25 arm
  sessions this is a live possibility and is not a failure of the design.

**The honest prior.** Q1 at about 65 % — a closing-hour sell imbalance after a decline is close to mechanical.
Q2 at 50 %. **Q3 and Q4 at about 10 %**, revised down from 20 % once D485's title was read properly (§1b): it
already found the micro crowd's trades are **no smaller** than the E-mini crowd's and that it leaves **no
flatten fingerprint**, so the conditional version has to overturn an established unconditional null. Add
D622 §5b's discriminator pointing to heavy volume at low impact per contract — size trading rather than stops
— and **the most likely single outcome by some distance is that the flow is real, one-sided and
institutional.** Q5 at about 30 %, since the burst's price effect never reached 2 SE and may have nothing
behind it.

*Runner: `scripts/census_d623_signed_close_flow.py`, written after this file is committed.*
