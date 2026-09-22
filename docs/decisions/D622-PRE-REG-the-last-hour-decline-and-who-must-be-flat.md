# D622 PRE-REGISTRATION — the last-hour decline and who must be flat by the close: a mechanism test, not a momentum test

*Committed before the runner exists (R8). Stage 0 only: four predictions about the MECHANISM, all on data
already on disk. No holdout is read and none may be read until Stage 0 passes.*

## 0. Why this exists, and the standard it has to meet

The principal's objection to the continuation effect this repository keeps rediscovering is the right one:
**"price will continue to go up" names no counterparty, so it is not a strategy.** A mechanism has to identify
someone who trades *because they must* — forced by a prospectus, a risk limit or a settlement convention —
not someone who trades because they expect to profit. This record is an attempt to meet that standard for
the one window where the effect survives measurement: the last hour of the ES day session.

**Three related lines are already closed, and they constrain what is left.**

[D463](D463-RESULT-market-intraday-momentum-is-a-third-of-its-published.md) tested the *strategy* — sign of
the day's return, 15:30 → 16:00 — and found it a third of its published size and not distinguishable from
zero, with hurdle P failing at every f. That is why this record is a mechanism test.

[D530](D530-avenue-3-closed-the-leveraged-ETF-reset-flow-is-real-and.md) tested the strongest textbook
mechanism, **leveraged-ETF reset flow**, which meets the standard completely: the fund is forced by its own
prospectus, cannot decline or wait, and its size is deterministic — `A·L·(L−1)·r`, **positive for the 3x long
and the 3x inverse alike**, so they buy together after an up day. It failed its own two predictions. Flow
linear in `r` should strengthen continuation with |return-of-day|: quintile 1 → 5 read **47.20 % → 50.63 %**
with Q5 at **z 0.49**. The flow should exist only where a leveraged ETP complex trades that future: 7,489
observations, hit **50.03 %, z +0.1**. And the flow itself is confirmed real — the equity roots trade
**15.7 %–21.1 %** of session volume in the closing hour against an even share of 14.3 %. **The forced trade
arrives and carries no direction.**

That is the most useful negative available here, and it constrains the search: **D530's mechanism is
symmetric in `r` by construction, and a symmetric mechanism cannot produce direction.** If the last hour
carries direction, the participant must be asymmetric.

And [`PROP_LIQUIDATION_CASCADES.md`](../internal/User-Doc-Deposit/PROP_LIQUIDATION_CASCADES.md) is **killed
at premise check**: prop-firm funded accounts are overwhelmingly simulated (Topstep's 2025 disclosure puts
0.71 % of Express Funded participants on a live account), the firm is the counterparty to its own traders,
and forced exits under a daily loss limit therefore produce **no aggressive volume in the real book**. So the
retail-prop stop-cascade version of an asymmetric forced seller is unavailable, and this record does not use
it.

## 1. The hypothesis, with the counterparty named

> **A large decline in 14:00–15:00 ET forces same-signed selling into the 16:00 cash close from participants
> who provided the liquidity that absorbed it and must not carry the position overnight.**

The forced participant is the **intraday liquidity provider** — the market maker or short-horizon
intermediary who, by construction, buys as price falls. Absorbing a large decline leaves that participant
**long an inventory it did not choose**, against a 16:00 cash close after which index risk cannot be hedged
in the same instrument until the next session's open. Its risk policy, not its opinion, requires the position
to be reduced before the close. The flow is therefore:

- **same-signed with the decline** (long inventory is sold, pushing price further down),
- **increasing in the size of the decline** (more absorbed, more to shed),
- **asymmetric** — absorbing a *rally* leaves the provider short, which is also unwanted, but short index
  exposure into an overnight gap is the less penalised side for a participant whose book is habitually long
  gamma/short delta, and the empirical asymmetry in §4 is what the test turns on,
- **concentrated in the final minutes**, as the deadline binds.

This is not a claim that price continues. It is a claim that a *nameable* participant has an obligation whose
discharge is mechanically same-signed with the move that created it.

## 2. The conditioner and the arm, fixed here

```
H1     = r(14:00 -> 15:00) / sigma          the prior hour's move in trailing-sigma units
LARGE  = |H1| >= 1.0                        declared threshold, one trailing sigma
arm    = SHORT the 15:00 -> 16:00 window when H1 <= -1.0
y      = 1e4 * log(P1600 / P1500)
```

`sigma` is the trailing 252-session standard deviation of the hourly move, lagged one session. The threshold
is **1.0 sigma, declared here and not tuned**; §6 discloses that the exploration which motivated this record
used a median-|H1| split instead, and the runner reports both so the difference is visible.

Controls, all measured before 15:00 so none overlaps the outcome: the overnight, 09:30 → 12:00, 12:00 → 14:00,
and — because D530's conditioner must not be able to masquerade as this one — **the whole-day move
09:30 → 15:00** entered separately. A conditioner that survives only by proxying the day's move is D463's
result again and the record must say so.

## 3. Stage 0: six predictions about the mechanism, on data already on disk

Each has a declared direction and a declared failure. **No holdout is read. Nothing is admitted.**

**P4 — the deadline binds, so the flow concentrates late.** Decompose 15:00 → 16:00 into three 20-minute
legs. Conditional on the arm, the third leg's mean must exceed the first's. *Fails* if the edge is flat or
front-loaded across the three legs, because an inventory deadline that binds at 16:00 cannot produce a
uniformly distributed effect.

**P5 — the effect is specific to the market with the 16:00 cash-close deadline.** On D467's eight hourly
roots (ES, NQ, YM, ZN, ZB, GC, CL, 6E), run the same conditioner and arm. The three equity-index roots share
the 16:00 cash close and a leveraged retail complex; the five others do not. *Passes* only if the three index
roots agree in sign **and** the five others' mean |z| is under 1.0. *Fails* on sign disagreement among the
index roots — which is exactly how D530's P2 died, when its per-root z read NQ +0.52, RTY +0.65, ES −0.45,
YM −0.54. **This is the discriminating test and it has a record of killing things.**

**P6 — the inventory is larger when the decline ran through resting liquidity.** Split the arm on whether the
14:00–15:00 decline took price below the **prior session's low**. Conditional on the arm, the broke-the-low
cell's mean must exceed the other's. *Fails* if it does not. Secondary rather than primary, because the
retail-stop version of this channel is dead on premise (§0) and what remains is the weaker claim that a
decline through a salient level absorbs more liquidity.

**The level is a level, not a trendline, and that is settled rather than assumed.** The principal proposed
keying this on a break of a retail-followed trendline. That specific question is already answered on the
principal's own 140 blind hand-drawn lines:
[D483](D483-RESULT-the-channel-is-not-the-ingredient-a-close-4pc-below-the.md) ran `dip-drawn` against the
plain dip and it earned **+45.2 against +47.4, a difference of −2.2 bp**, while the level rule came within
−1.6 of the dip. **A close 4 % below the 30-bar low earns the same with no lines at all**, which is the record
the daily channel line closed on, and [D481](D481-RESULT-the-hand-cell-trades-like-every-other-causal-channel.md)
had already found the hand cell trades like every other causal channel. So the trendline is excluded here **by
measurement, not by taste**, and P6 uses a plain prior-session low.

**P9 — THE DEADLINE PLACEBO, which holds the instrument fixed.** The mechanism is a claim about a *time of
day*: a 16:00 deadline binds. So the same conditioner-and-outcome structure, run on hour pairs where **no
deadline binds**, must not show the effect. Run `r(h−1) → r(h)` for every hour pair of the ES session and
require the 14:00 → 15:00 → 16:00 cell to stand out against the other 21 as a **family maximum**, not merely
to be positive. *Fails* if the effect is of the same size at hours with no closing constraint, because then it
is a property of hourly returns rather than of the deadline.

This is a stronger control than P5 because it holds the instrument, the tick size, the participants and the
liquidity regime constant and varies only the clock. It is also **pre-specified rather than fitted**:
[FINDINGS §81](../FINDINGS.md) already measured the whole 22-pair map on this window — 09:00 **−0.040**,
10:00 **+0.034**, 15:00 **−0.018**, against 21:00 **+0.167**, 06:00 **−0.181**, 23:00 **−0.143** — so the
comparison set and its values exist before this runner does.

**And the hour pair being tested was SELECTED, which the multiplicity must price.** 14:00 → 15:00 was chosen
because §81's census found it the best product of predictability and move size on the entire clock (ρ +0.113
against a mean absolute move of $36.19, implying $4.09 against a $4.25 round trip). That is a **1-of-22**
selection and the family-maximum null in §5 is computed across all 22 pairs for exactly that reason. §81 also
supplies the other half of why this window and no other could pay at all: its fee share is **0.12**, among
the four cheapest hours on the clock, against **0.30** overnight and **0.45** at 23:00.

**P8 — THE REVERSAL TEST, and it is the sharpest discriminator in this design.** It comes from noticing what
the channel programme found in the *other* direction. D483's dip rule is a **long**: after a close 4 % below
the 30-bar low, price **reverts +47.4 ± 10.1 bp over five bars against a null p95 of +18.6**. Forced
liquidity provision and information make opposite predictions about what happens next, and this is the one
place they can be separated:

- if the last-hour decline is an **inventory discharge**, the price was pushed below fair value by a
  participant who had to sell, and it must **partially revert** — in the overnight session, the next
  morning, or over the following days;
- if it is **information**, there is nothing to revert.

*Passes* if, conditional on the arm, the subsequent overnight return and the next session's return are
**positive on average** and the reversal grows with the size of the triggering decline. *Fails* if the decline
simply persists, which would mean the last hour is repricing rather than absorbing. Measured at three
horizons — the overnight to 09:30, the next full session, and five sessions, the last matching D483's own
hold — so the two clocks can be compared directly.

**P8 is the prediction this design would be weakest without**, and it exists because the principal asked
about trendline breaks: the trendline itself is refuted, but the question led to the daily-clock reversion
result that makes intraday continuation and multi-day reversion a coherent single mechanism rather than two
contradictory findings.

**P7 — the flow is visible in volume, not only in price.** The closing hour's share of session volume must be
higher on arm days than on non-arm days, over and above D530's measured baseline hump of 1.10×–1.48×.
*Fails* if arm days show no excess. This is the premise check: if the forced trade does not arrive, the
mechanism is not operating.

**Reproduced for the record, not predictions:** the asymmetry (down versus up), the size-dependence within
the down side, and the absence of a high-volatility requirement — the three §6 measurements that motivated
this record — recomputed by the runner so the record is self-contained.

## 4. What Stage 0 cannot do, and the premise check that is deferred

The mechanism's **direct** premise — that liquidity providers are long into the close on large-decline days
and sell that inventory — requires **signed aggressor flow**, which exists on this disk only in the `tbbo`
year, 2025-09-11 → 2026-09-10, inside the reserved slice.
[D617](D617-FIXTURE-the-ES-option-signed-flow-census-from-the-tbbo-year.md) has already established that this
data is present and clean for options (unsigned share 0.000166, at-quote agreement 0.999983) and D485
established the convention on futures. **That check is deferred, not skipped**, and it is the natural second
stage: a signed-flow census on the reserved window, read as a census in D510/D511's shape with no return
scored, would test the premise without spending the slice for returns.

## 5. Bars, nulls and the power arithmetic — stated before the run

**Nulls** for any scored cell: the **enumerated** rotation null with the signal side rotated *jointly*
(conditioner, threshold state and sigma together, so the arm's own structure survives and only its pairing
with the outcome is destroyed), and the sign-flip null at 2,000 draws under seed 622. Both reported with p05,
p50, p95 and the observed rank.

**Multiplicity.** Stage 0 runs four predictions plus three reproductions, and P5 runs across eight roots. The
family maximum across the eight roots is compared against the max of the same family on each rotation draw,
which is what prices P5's cross-section.

**The economic bar is not a Stage 0 bar.** Stage 0 asks whether the mechanism is operating, not whether it
pays. For reference, the exploration's best cell read **+$9.83 gross a trade** against a **$4.25** round trip
at one MES — and that is a *disclosed selected cell*, not a pre-registered one.

**The power arithmetic, stated now so the holdout is never spent on false hope.** At the arm's rate of about
55 trades a year and a per-trade dispersion of **$63.5**, a two-year holdout returns an expected t of **+1.62
on gross and +0.92 on net even if the effect is entirely real**; establishing the net edge at t = 2.0 needs
**519 trades, about 9.4 years**. **Therefore the holdout is gated on Stage 0**: if P5 or P7 fails, the
mechanism is not operating and the 2024+ slice is never read for it.

## 6. Disclosed looks that motivated this record

This record was written *after* the following measurements on the spent in-sample window, taken while
identifying what a gross-clearing cell in
[D618](D618-STAGE-0-RESULT-the-band-around-the-price-was-the-signal.md) was eating. They are disclosed
because a hypothesis assembled from subgroup analysis must say so:

| cell | n | gross/trade | t | hit | median |
|---|---:|---:|---:|---:|---:|
| the hour **fell** → short into the close | 888 | +$5.27 | +3.04 | 0.516 | +$1.88 |
| the hour rose → long | 1,029 | +$1.92 | +1.23 | 0.494 | $0.00 |
| **fell and the move was large** (median split) | 441 | **+$9.83** | **+3.25** | 0.540 | +$5.00 |
| fell and the move was small | 447 | +$0.78 | +0.46 | 0.492 | $0.00 |
| fell and volatility was **high** | 437 | +$4.88 | +1.68 | 0.513 | +$2.50 |
| fell and volatility was **low** | 427 | +$5.87 | +2.88 | 0.520 | +$1.25 |

The asymmetry and the size-dependence are what the mechanism predicts. The volatility result **refutes** the
vol-target variant of an asymmetric forced seller, and is why §1 names inventory rather than vol-targeting.
The cells above are a search over up/down × large/small × high/low volatility, and the best of them is
reported as the best of a search rather than as a result.

## 7. Disposition, declared in advance

- **P5 fails** (index roots disagree in sign, or the non-index roots show the same effect) → the deadline is
  not what produces the direction; the mechanism is refuted and the line closes without the holdout being
  read. This is the most likely outcome and the record says so.
- **P7 fails** → the forced trade does not arrive; the premise is false, as it was for the prop cascades.
- **P8 fails** (no reversal) → the last hour is repricing on information rather than absorbing inventory.
  That would not make the continuation unreal, but it would mean the mechanism in §1 is the wrong story for
  it, and the record must then say the effect has no named counterparty again.
- **P9 fails** (the effect is the same size at hours with no closing deadline) → the effect is a property of
  hourly returns and not of the deadline, and the mechanism is refuted with the instrument held fixed, which
  is a cleaner refutation than P5 can give.
- **All six pass** → the mechanism is operating and the deferred signed-flow premise check (§4) becomes the
  next stage, on the principal's word, as a census.
- **Some pass and some fail** → reported cell by cell with no aggregate verdict, because a mechanism test
  that is partly supported is a description and not a finding.

**The honest prior: about 10 % that all six pass**, revised down from 20 % by P8 and again by P9, both of
which are real tests rather than formalities. P9 in particular is where a 1-of-22 selection usually dies: the
hour pair was chosen as the best of the clock, so the family maximum is the bar it has to clear, and §81's
own map shows how close the runner-up hours are in correlation terms even though they are smaller in move.
P8 is the other — D483's dip result makes reversion plausible on the daily clock in
equities, but nothing here has measured it on the intraday futures clock and the two need not agree. The
asymmetry and size-dependence are already measured and are the two the mechanism most needs; P5 is the test
that killed D530's stronger mechanism; and the history of this window is that every effect in it survives its
nulls and dies on cost or cross-section.

*Runner: `scripts/stage0_d622_close_inventory.py`, written after this file is committed.*
