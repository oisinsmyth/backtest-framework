# D198 — does waiting for a second approach help, or discard the winners?

**Status:** Pre-registered — written and committed BEFORE the run
**Date:** 2026-08-24
**Category:** Signals & strategy interface
**Source:** D197's failure, and a counts-only census run before this document existed

> A result section will be appended and nothing above it edited.

## Provenance, and the discipline problem stated first

**This is a refinement proposed after seeing D197 fail.** That is discretionary search on
a hypothesis that has already been rejected once, which is the single most suspect move a
research programme can make and the exact pattern D194's permanent stop exists to
prevent. Its own document, its own bar, its own ledger, and the prior 34 looks carried.

**The honest prior is that this does not rescue S6.** D197's verdict deltas against the
local-band null were **−0.007 and −0.012** — not short of the bar, *exactly zero*. A
filter applied identically to the real arm and to every null draw is unlikely to
manufacture placement information from none. That is written here so a pass has to be
surprising rather than expected.

What makes it worth running anyway is a different claim, and it is not a rescue: **a level
approached twice may carry information a level approached once does not.** That is S5's
`tests` component, which the sensor scored on and no run in this project has ever
isolated. It has a sharp prediction attached and it can fail.

## The census, run before this document

Counts only — no returns, no Sharpe, nothing readable as a result. It rejected the
originally-proposed rule and produced the one specified below.

The proposal was: any second same-direction qualifying signal within 20 bars.

| | BTC-USD | ETH-USD |
|---|---:|---:|
| qualifying signals (D197 primary, X=0) | 492 | 410 |
| already have a second within 20 bars | **86.2%** | 86.6% |
| ...of those, second arrives on the **next bar** | **61.3%** | 64.5% |
| median gap | **1 bar** | 1 bar |

S6 fires whenever a close sits outside the erasure envelope, and during a breakout run
consecutive bars keep firing. "Seen twice" was therefore satisfied at `t+1` by the *same
excursion still happening*: the rule removes 14% of signals and delays the rest by one
bar. It is an entry delay wearing a filter's name.

**Requiring two DISTINCT approaches** — price must return inside the envelope in between —
is a filter:

| | BTC-USD | ETH-USD |
|---|---:|---:|
| confirmed within 20 bars | **67.5%** | 64.6% |
| median gap | **7 bars** | 7 bars |
| degenerate 1-bar confirmations | 0 | 0 |

That is `terrain_nulls.level_reactions`' first-bar-of-an-approach convention, already in
the project, so it costs no parameter beyond the 20-bar window.

## The rule

Everything about the sensor is D197's and **nothing is re-swept**: k=2, cluster_atr=0.5,
X=0, the primary configuration. D197 swept 16 cells and all 16 failed the null, so
re-sweeping would buy a fresh multiplicity cost for a dimension already shown not to
matter. The confirmation window is fixed at **20 bars**, the value proposed, and is not
swept either.

A qualifying signal is D197's: a fire that is not virgin and whose tilt is correctly
oriented for the fade — break up into net supply, or break down into net demand.

> Signal at `t1` is **CONFIRMED** by a later qualifying signal at `t2` in the same
> direction when `t2 - t1 <= 20` and at least one bar strictly between them closes
> **inside** the erasure envelope.

Entry is on the confirming signal, market at the open of `t2 + 1`. Stop 2 x ATR(20),
target 3R, `MAX_HOLD` 60, 40 bps round trip, full equity, one position at a time, stop
taken first when a bar covers both — all inherited from D197 unchanged.

Deterministic bookkeeping, stated so it cannot drift: signals are walked in order; a
pending same-direction signal is held for at most 20 bars; the first later signal that
satisfies the distinct-approach test emits a CONFIRMED entry and clears the pending set
for that direction; a pending signal that ages out emits to the UNCONFIRMED book.

## The three books, and which of them are real strategies

| book | tradeable? | what it is |
|---|---|---|
| **CONFIRMED** | **yes** | the new rule; carries the verdict |
| **ALL SIGNALS** | **yes** | D197's unfiltered reversal book — the baseline, already run |
| **UNCONFIRMED** | **NO** | the signals the filter rejected |

**The unconfirmed book is a diagnostic and must never be reported as a strategy.** A
signal is only known to be unconfirmed once 20 bars have passed without a partner, so
entering it at `t + 1` uses knowledge that did not exist at `t + 1`. It is deliberately
constructed with hindsight because the question it answers — *what happened to the trades
the filter threw away* — cannot be answered any other way. Any figure it produces is
labelled hindsight-classified wherever it appears.

The baseline for the verdict is therefore **ALL SIGNALS**, tradeable against tradeable.
D197 measured it on the primary configuration already: BTC **−0.437** (n=124), ETH
**−0.667** (n=106), against buy-and-hold +0.773 and +0.308, and an erasure-only control
of −0.866 and −1.166.

## The bar

All three required, on **both** symbols:

1. **CONFIRMED beats ALL SIGNALS by ≥ +0.10 Sharpe.** The claim that waiting helps,
   tradeable against tradeable.
2. **CONFIRMED beats its matched null by ≥ +0.10 Sharpe.** The local band from D197's
   amendment, 500 draws, seed 0, the erasure and the confirmation rule applied identically
   in both arms. The whole-series-span diagnostic null is **not** run: D197 showed it is
   the weaker test and that it produced a +0.284 at the 94th percentile on BTC where the
   local band read −0.007. Running it again would buy a known artifact.
3. **CONFIRMED beats buy-and-hold.**

Floor and grounding unchanged from D195, D196 and D197: D185 put the whole rebalancing
machinery at 0.025 Sharpe and D183's portfolio edge was +0.075.

**Reported alongside, not optional:** long and short legs separately (D197 found the short
leg worse in 16 of 16 cells); trade counts per book; the confirmed/unconfirmed split by
calendar year; and the UNCONFIRMED diagnostic.

## Multiplicity

2 symbols × 2 books (confirmed, unconfirmed) = 4 cells, plus 2 confirmed-vs-all
comparisons = **6 looks**, added to D197's 34. **Cumulative: 40 looks on the S6 family.**

## Predictions

**H1 — CONFIRMED fails to beat ALL SIGNALS by the floor on at least one symbol.** Predicted
**TRUE**, high confidence.

**H2 — the UNCONFIRMED diagnostic OUTPERFORMS the CONFIRMED book on at least one symbol.**
Predicted **TRUE**, moderate-to-high confidence, and this is the prediction worth watching.
A signal goes unconfirmed precisely when price went **straight back inside the range** —
which, for a trade that fades the break, is the setup working. So the filter should
preferentially discard winners. Same shape as D9's adverse selection: you are reliably
filled on the ones that keep going.

**H3 — CONFIRMED remains indistinguishable from its null, delta within ±0.10 on both
symbols.** Predicted **TRUE**, high confidence. D197's delta was exactly zero, and the
filter is applied to both arms.

**H4 — neither book beats buy-and-hold.** Predicted **TRUE**, high confidence.

**H5 — the short leg is worse than the long leg in both books on both symbols.** Predicted
**TRUE**, high confidence. D197: 16 of 16, and the confirmation rule leaves the long/short
ratio nearly unchanged (171/321 to 111/221 on BTC).

**The interesting failure mode, named in advance.** If CONFIRMED clears all three hurdles
it would be the first thing in this programme to survive a fair test, and the first
suspicion should be era selection rather than discovery: a rule that waits for price to
return to its range will fire more often in ranging markets, and this fixture contains one
long bear market in which fading breakouts works for reasons unrelated to supply and
demand. Hence the by-year split is mandatory reporting rather than a follow-up.

## Verification

- The confirmation walk gets its own look-ahead test: the pending/confirm bookkeeping must
  read no bar past the confirming signal, poisoned as in `test_terrain_field.py`.
- A property test that CONFIRMED and UNCONFIRMED **partition** the qualifying signals —
  no signal in both, none in neither.
- A test that a confirmation whose intervening bars never re-enter the envelope is
  **rejected**, which is the whole difference from the census's degenerate rule.
- The census reproduces: 67.5% / 64.6% confirmed, median gap 7 on both symbols.
- Full suite green, mypy clean, summary JSON re-renders byte-identically.

## What a pass would and would not mean

It would mean repetition carries information here — that a level approached twice is
different from a level approached once, after costs, on one asset class in one decade.

It would **not** revive S6's placement claim. D197 measured that at zero against the local
band and this run does not re-test it; a pass would say the *timing* rule works on top of
a map whose *placement* is still indistinguishable from random, which is a strange and
narrow thing to own and should be written that way rather than rounded up.

## CLARIFICATION — what the census counted, and what the rule enters, before any run

The census above reports **67.5% / 64.6% confirmed**. That is the share of qualifying
signals that *have* a distinct-approach partner within 20 bars. It is not the number of
entries, and a reader would reasonably have expected about 330 trades on BTC from it.

The pending walk this document specifies **consumes pairs**: a confirmation retires both
the trigger and the confirmer, and a signal that fires mid-excursion without confirming
anything is absorbed. Running the implemented rule:

| BTC-USD | | ETH-USD | |
|---|---:|---|---:|
| qualifying | 492 | qualifying | 410 |
| **CONFIRMED entries** | **114** | **CONFIRMED entries** | **91** |
| triggers (set up an entry, are not one) | 114 | triggers | 91 |
| absorbed (same excursion still running) | 206 | absorbed | 183 |
| **UNCONFIRMED** | **58** | **UNCONFIRMED** | **45** |

Both figures are true and they measure different things; the rule is unchanged. This is
recorded before the run rather than explained afterwards, in D144's manner.

Two consequences worth having in writing first:

- **114 entries against D197's 124** on BTC, so hurdle 1 compares books of comparable
  size rather than a large one against a small one.
- **The UNCONFIRMED diagnostic is thin — 58 and 45 trades.** H2's test is correspondingly
  weak, and a difference there will need to be large before it means anything. Stated now
  so a null result on H2 is not later read as evidence that waiting is harmless.

The confirmed entries spread evenly across the fixture — BTC 7 to 19 a year for eleven
years, ETH 1 to 15 — which is some reassurance against the era-selection failure mode
named above, though the by-year P&L split is still mandatory reporting.

---

## RESULT — appended after the run; nothing above this line edited

**0 of 2 symbols clear all three hurdles.** But hurdle 1 passed on both, and the
diagnostic answered the real question emphatically.

| | BTC-USD | ETH-USD |
|---|---:|---:|
| CONFIRMED | **−0.288** (n=67) | **−0.183** (n=54) |
| ALL SIGNALS (D197 baseline) | −0.437 (n=124) | −0.667 (n=106) |
| **vs ALL** | **+0.149** ✓ | **+0.484** ✓ |
| vs local-band null | **−0.156** ✗ (21st pct) | +0.090 ✗ (60th pct) |
| buy-and-hold | +0.773 ✗ | +0.308 ✗ |
| *UNCONFIRMED (hindsight diagnostic)* | *+0.785 (n=42)* | *+0.310 (n=30)* |

### H1 — FALSIFIED

Predicted at high confidence that CONFIRMED would fail to beat ALL SIGNALS on at least one
symbol. It beats it on **both**, by +0.149 and +0.484, clearing the floor. **Waiting for a
second distinct approach does improve the strategy.**

The mechanism is entry price, not selectivity. ALL SIGNALS enters at the *first* qualifying
signal of an excursion; CONFIRMED enters at the second approach, after price has already
run further against the eventual fade — a better price to sell into a rally or buy into a
decline. That is worth about +0.15 to +0.48 Sharpe here.

This is the second document running in which I predicted a refinement would fail to beat
its own baseline and it did not.

### H2 — CONFIRMED, and it is the run's finding

The signals the filter **discards** are far better than the ones it keeps:

| | CONFIRMED | UNCONFIRMED *(hindsight)* | gap |
|---|---:|---:|---:|
| BTC Sharpe | −0.288 | **+0.785** | **1.073** |
| BTC hit rate | 28.4% | **57.1%** | |
| ETH Sharpe | −0.183 | **+0.310** | **0.493** |
| ETH hit rate | 29.6% | **43.3%** | |

A signal goes unconfirmed precisely when price went **straight back inside the range** —
which, for a trade that fades the break, is the setup working. So the rule systematically
keeps the excursions that kept running and throws away the ones that reverted. Waiting
costs about a full Sharpe point on BTC and half of one on ETH.

Both effects are real and they point opposite ways: waiting buys a better entry price and
sells the winners to get it. Here the second dominates.

**The unconfirmed book is not a strategy and its numbers are not an edge.** Membership is
only knowable 20 bars after the fact. It measures what the filter threw away; that is all.

### H3 — falsified on BTC, and in the unhelpful direction

Predicted CONFIRMED would sit within ±0.10 of its null on both symbols. ETH does (+0.090).
BTC does not — but at **−0.156, the 21st percentile**, the real map is *worse* than
randomly placed mass put through the same confirmation rule. The prediction that the
filter would not manufacture placement information is confirmed with room to spare; the
specific band was wrong on the pessimistic side. The null also trades half as often
(34 against 67).

### H4 — CONFIRMED

Neither book beats buy-and-hold, and not narrowly: −1.060 and −0.491 short of it.

### H5 — CONFIRMED

The short leg is worse than the long leg in every book on both symbols. CONFIRMED on BTC:
longs +0.105, shorts −0.502. ETH: longs +0.202, shorts −0.490. Even inside the positive
unconfirmed diagnostic the ordering holds (BTC longs +0.742, shorts +0.351).

### Era selection did not materialise

The named failure mode was that a rule waiting for price to come home would concentrate in
ranging markets. Confirmed entries spread evenly — BTC 3 to 9 a year across eleven years,
best 2023 (+0.43 summed net), worst 2021 (−0.43); ETH 1 to 9, best 2022 (+0.79), worst
2025 (−0.73). No era carries the result. It failed on its merits.

### Ledger

**D198: 6 looks. Cumulative on the S6 family: 40.**

### What this leaves

S6's placement claim is not revived and this run did not test it. What it establishes is
narrower and more useful: **for this fade rule, the trades worth having resolve quickly**,
and any filter that waits for confirmation sells them off.

That has a tradeable analogue this run did not test. If the winners are the excursions that
revert fast, the lever is the **holding period**, not the entry filter: `MAX_HOLD` is 60
bars and the unconfirmed set resolves inside 20. Shortening the hold, or exiting on
re-entry into the envelope, is a rule that needs no hindsight. It is a different
hypothesis with a different bar and it belongs in its own pre-registration, not in this
result section.
