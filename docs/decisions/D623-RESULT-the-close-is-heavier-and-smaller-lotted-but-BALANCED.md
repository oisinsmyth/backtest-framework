# D623 RESULT — the closing hour after a decline is heavier, and smaller-lotted, and BALANCED

*Pre-registered in [D623](D623-PRE-REG-the-signed-flow-census-who-sells-into-the-close.md), committed alone
before the runner existed (R8). Runner: `scripts/census_d623_signed_close_flow.py`; artifact:
`data/census_d623_signed_close_flow.json`. **No return is scored** — the 2024+ slice stays unspent for every
return-bearing construction, as [D510](D510-RESULT-the-tick-binds-on-ZN-and-ZB-and-on-nothing-else-lane.md),
[D511](D511-RESULT-three-independent-measurements-order-the-eight-roots.md) and
[D617](D617-FIXTURE-the-ES-option-signed-flow-census-from-the-tbbo-year.md) declared for the same window.*

## The answer in one line

**The named counterparty is there, and it is not selling.** Retail-sized flow in the closing hour is
elevated after a ≥1 σ decline — on all four roots, at 2 SE on three of them — and that flow is **balanced**:
the 15:00 → 16:00 signed imbalance on arm sessions is **+0.0009 on ES at t +0.21**, with exactly **50.0 % of
arm sessions net sell-initiated**, and the census's equivalence bound **excludes** a one-sided imbalance of
the size a forced-liquidation story needs on three of four roots. Where the micro contract differs from its
mini it differs toward the **buy** side (MNQ − NQ **−0.0085 at t −2.27**), which is the retail-flow
literature's *with the body, against the extreme* pattern and the opposite of a stop cascade.

So the mechanism question closes on the pre-registration's own §6 disposition, but not in the shape §6
anticipated: **the cascade is excluded while the crowd is confirmed present.** Whoever sells the last hour on
those sessions is not visible at a lot size this fixture can resolve.

## 0. Six specification changes, every one made AFTER the first pass, and why

The first pass of the runner reported **Q3 as a pass** on a level margin with no control, and would have put
a retail signature in the record that the control does not support. That is the same failure shape as
[D618](D618-STAGE-0-RESULT-the-band-around-the-price-was-the-signal.md) §0 (a band anchored on the price) and
[D622](D622-STAGE-0-RESULT-the-hour-is-specific-and-it-does-not-revert.md) §0 (point estimates with no
standard error), so it is recorded the same way, in advance of the numbers.

| # | change | why it was forced |
|---|---|---|
| 1 | **the midday control on Q3** — the same arm-minus-non-arm comparison on 11:00–14:00 | the first pass compared the closing hour on arm sessions to the closing hour on other sessions and found +0.024 to +0.051 at t +2.4 to +4.0. The **same margin exists at midday** (+0.004 to +0.025), so the level is a property of the SESSION, not of the close. The pre-registration's own wording is a conjunction — "relative to both non-arm sessions **and** the same session's own midday baseline" — so this is the declared test applied correctly, not a new one |
| 2 | **a difference-in-differences as Q3's primary** | the conjunction of change 1: does the closing hour's small-lot share rise *more* on arm sessions than it does on other sessions |
| 3 | **the logged volume ratios, per bucket** | a *share* moves because its numerator grew or its denominator shrank, and those are opposite readings. `small_vol_ratio_log`, `vol_ratio_log` and their difference separate them. Per bucket, because midday is three hours against the close's one and an unnormalised level would carry a log(12/36) constant — the first pass printed exactly that artefact as a "fail" |
| 4 | **an equivalence bound on Q1** | Q1's declared FAILURE is that the imbalance is **symmetric**, and D373's rule can only say `unresolved`, which cannot distinguish *no effect* from *no power*. The bound is the upper 2-SE limit on the arm mean against a material effect declared as **0.5 sd of the same quantity on non-arm sessions** — sessions the claim is not about, so the benchmark is not read off the arm it judges |
| 5 | **Q4's lot legs marked VOID** | a lot is a different notional in each contract. The two pairs come out with **opposite signs** — MES − ES +0.026, MNQ − NQ **−0.206 at t −35.19** — which is the statistic measuring contract size, not trader type. That is [D485](D485-RESULT-the-micro-crowd-is-only-half-distinct-trades-no-smaller.md)'s own finding reappearing as an artefact. Only Q4's imbalance leg is interpretable |
| 6 | **the control restricted to CLASSIFIED sessions** | the first pass put the 30 sessions of the σ warm-up in the non-arm group. A session with no trailing σ is **unclassified**, not non-arm, and leaving it in made the control partly a calendar filter — the first weeks of the window. Fixing it moved MNQ's Q3 margin from t +2.16 to **+1.83**, i.e. from pass to unresolved, so it changed a verdict |

And one thing the fixture cannot do, which is a limit and not a change: **`lot1` and `lot_le2` are volume in
small trades and are NOT split by aggressor side** (`build_fut_micro_flow.py:105` sums `size` where
`size <= 2` over all trades). The pre-registration asks for the small-lot share **of sell-initiated volume**;
that quantity does not exist in this fixture and cannot be recovered from it. Q3 therefore measures the
small-lot share of **total** volume, and on a window where Q1 finds no net selling that distinction is
load-bearing rather than pedantic.

## 1. The window, the arm, and the count reported before any comparison

| | |
|---|---|
| fixture | `data/fixtures/fut_micro_flow_5m.csv.gz` ([D485](D485-RESULT-the-micro-crowd-is-only-half-distinct-trades-no-smaller.md)) |
| read | **2025-09-11 → 2026-06-30**, 226,224 buckets, 207 sessions |
| unread | **2026-07-01 → 2026-09-10**, D485's reserve, asserted from both sides |
| closing-hour coverage | 796 of 828 (root, session) pairs carry all **12** five-minute buckets — 96.1 %; the 32 short ones are dropped by a declared rule |
| σ | trailing **60** sessions, minimum 30, lagged one session — D622's 252 does not fit a one-year window, so the convention is declared here and a quantile arm is reported beside it |
| **arm sessions** | **26** of **169** with a usable σ, at `H1 ≤ −1.0` |
| quantile arm (beside) | **24** at the worst 12 % of the window's own 14:00 → 15:00 moves; **22 in common** with the threshold arm |
| midday burst ≥ 1.25 | 52 sessions; **arm AND burst: 6** |
| unclassified, dropped | 30 (the σ warm-up) |

The 26 arm sessions: 2025-10-29, 10-30, 11-17, 12-01, 12-18, 12-31; 2026-01-15, 02-13, 02-18, 03-10, 03-18,
03-20, 03-30, 04-01, 04-07, 04-08, 05-01, 05-11, 05-18, 05-19, 05-21, 06-05, 06-10, 06-17, 06-23, 06-26.

**The signing carries no error worth naming.** The unsigned share of closing-hour volume is **exactly
0.000000** on every root — mean and maximum — and the aggressor-side agreement rate is **0.99999 to
1.00000**. Unlike D617's option tape, where the `N` share had to be measured before the conditioner could be
trusted, the futures closing hour is fully signed.

## 2. Q1 — the flow is NOT one-sided, and the bound says how firmly

The premise of every forced-seller story, and it does not hold.

| root | arm mean | t | median | symmetric trim | share net-sell | non-arm level | t |
|---|---:|---:|---:|---:|---:|---:|---:|
| ES | **+0.00092** | +0.21 | −0.00115 | +0.00089 | **0.500** | +0.00171 | +0.68 |
| MES | −0.00303 | −0.63 | −0.00404 | −0.00266 | 0.346 | −0.00304 | −1.27 |
| NQ | +0.00743 | +1.72 | +0.01077 | +0.00841 | 0.692 | +0.00607 | **+3.27** |
| MNQ | −0.00108 | −0.36 | −0.00437 | −0.00105 | 0.423 | +0.00021 | +0.14 |

ES's mean **flips sign against its median** and exactly half the arm sessions are net sell-initiated. The
tails are symmetric in the way a balanced book is: the three most sell-heavy arm closes are 2026-05-18
(−0.0381), 2026-03-20 (−0.0329) and 2026-04-07 (−0.0289) and the three most buy-heavy are 2025-10-30
(+0.0407), 2025-12-31 (+0.0406) and 2026-06-26 (+0.0326) — the same magnitude on both sides. The quantile
arm agrees at **−0.00124, t −0.27**. Within the session, the closing hour's imbalance minus the same
session's own midday imbalance is **−0.0015 on ES at t −0.27** and unresolved on every root.

**What the data exclude.** A material one-sided flow is 0.5 sd of the non-arm distribution, declared before
the comparison:

| root | arm mean | SE | upper 2-SE bound | material | excludes it? |
|---|---:|---:|---:|---:|:--|
| ES | +0.00092 | 0.00438 | +0.00969 | +0.01506 | **yes** |
| MES | −0.00303 | 0.00478 | +0.00653 | +0.01425 | **yes** |
| NQ | +0.00743 | 0.00431 | +0.01605 | +0.01109 | no |
| MNQ | −0.00108 | 0.00301 | +0.00494 | +0.00885 | **yes** |

Three of four roots exclude it. NQ is the exception and it is the root D622 already found carried the largest
price effect — but NQ's **non-arm** imbalance is +0.00607 at **t +3.27**, larger than its arm margin over
non-arm (+0.0035, t +0.75), so NQ's closing hour is mildly net sell-initiated *every* session and the arm
adds nothing detectable to it.

**The enumerated rotation null confirms there is nothing to place.** Rotating the arm label as a block
against the ES closing imbalance over **150** offsets: observed +0.00092, p50 **+0.00144**, p95 +0.01061
(bootstrap SE 0.00044), **rank 0.467**. The observation sits *below* the median of its own null.

## 3. Q2 — and it does not accelerate into the deadline

A cascade and an inventory deadline both predict the imbalance building through the twelve closing buckets.
It does not build on any root.

| root | slope on bucket index | t | last two minus first two | t |
|---|---:|---:|---:|---:|
| ES | −0.00050 | −0.49 | +0.00916 | +0.87 |
| MES | +0.00015 | +0.10 | +0.02074 | +1.20 |
| NQ | +0.00020 | +0.20 | +0.01318 | +1.09 |
| MNQ | +0.00035 | +0.38 | +0.02101 | **+1.94** |

Every slope is indistinguishable from zero and three of the four **flip sign on their median**. The
last-two-minus-first-two contrast is positive on all four, which is the only directional agreement in Q2, and
its largest t is +1.94 — inside 2 SE, so UNRESOLVED and not a finding. With 26 sessions there is no reading
of these numbers that supports acceleration.

## 4. Q3 — the crowd IS there: a real, replicated, direction-correct small-lot signature

This is the one place the census finds something, and it needed all three of §0's changes to be stated
honestly.

**Step 1, the raw level, which is what the first pass reported.** The ≤2-lot share of closing-hour volume,
arm minus non-arm: ES +0.02421 (t +2.39), MES +0.03841 (+2.89), NQ +0.04238 (**+3.27**), MNQ +0.02251
(+2.11). Four passes.

**Step 2, the control that voids step 1 as a deadline claim.** The *same* comparison on the midday window:
ES +0.00359 (t +0.34), MES +0.01045 (+1.14), NQ **+0.02487 (+2.06)**, MNQ +0.01070 (+1.13). Same sign on
every root and NQ's reaches 2 SE. **Arm sessions carry more small-lot volume all day**, so the closing-hour
margin is in large part a session-level characteristic.

**Step 3, within the session, the share FALLS into the close** — on arm sessions as on any other: closing
minus own midday is **−0.05867 on ES at t −7.44** and −0.02235 on NQ at −3.01, with only 7.7 % of ES arm
sessions positive. Q3's own-midday leg therefore **fails**, and Q3 read as the pre-registration's conjunction
of two legs does not hold.

**Step 4, the difference-in-differences, which is what remains and what it means.** Does the closing hour's
small-lot share fall *less* on arm sessions than on other sessions?

| root | DiD on the share | t | excess small-lot growth over the book (log) | t |
|---|---:|---:|---:|---:|
| ES | +0.02062 | **+2.52** | **+0.09577** | **+3.20** |
| MES | +0.02797 | **+2.58** | **+0.11312** | **+3.02** |
| NQ | +0.01751 | **+2.26** | **+0.02700** | **+2.41** |
| MNQ | +0.01181 | +1.70 | +0.02492 | +1.83 |

**Positive on all four roots by both measures, at 2 SE on three.** The volume decomposition says what it is,
and the level is only interpretable because of change 3. On ES arm sessions the closing hour runs
**2.02× midday volume per minute** (log +0.70361, t +11.38) while small-lot volume runs **1.61×** (log
+0.47522, t +6.61), so small lots grow **20 % less** than the book (excess **−0.22839**, t −8.01): the close
is still *more* institutional than midday. On non-arm sessions that shortfall is larger, and the difference
is the DiD. So the correct statement is not "the close is retail" but **"the close is about 10 % less
institutional than it would normally be"** — e^{+0.096} on ES and e^{+0.113} on MES, e^{+0.027} and
e^{+0.025} on the NASDAQ pair.

That is a genuine signature of the principal's named counterparty. It is also, on its own, only a statement
about **presence**, because Q1 has already established that the presence is two-sided.

## 5. Q4 — and where the micro differs, it differs toward BUYING

Q4's lot legs are void (§0, change 5). The imbalance leg, paired within session:

| pair | arm sessions | t | non-arm baseline | t | difference in differences | t |
|---|---:|---:|---:|---:|---:|---:|
| MES − ES | −0.00396 | −1.11 | −0.00474 | −2.10 | +0.00079 | +0.19 |
| MNQ − NQ | **−0.00851** | **−2.27** | −0.00586 | −3.50 | −0.00265 | −0.65 |

The declared direction for Q4 was that the imbalance is **more sell-tilted in the micro**. It is **less**
sell-tilted on both pairs, on arm and non-arm sessions alike, and MNQ − NQ reaches 2 SE on arm sessions. The
difference-in-differences is unresolved on both, so the gap is a permanent property of the micro contract
rather than something the arm produces — which is the right reading, and it is the reading that makes Q4's
failure informative: **the small-contract crowd is a marginally better buyer of the closing hour than the
E-mini crowd, always, and a decline does not change that.**

## 6. Q5 — NOT TESTED

Only **6** sessions are both arm and burst, against this census's own declared floor of **12** (§3 of the
pre-registration). The margins are in the artifact — ES burst minus no-burst **−0.01453 at t −1.66**, wrong
sign, and every root unresolved — and they must not be read as evidence either way. A question asked on fewer
observations than the design declared usable has not been asked. **The midday burst's status is unchanged
from D622 §5b: an orthogonal conditioner whose own price effect never reached 2 SE, now with a flow test that
could not be run.**

## 7. Disposition against §6's declared table

§6's first branch reads: *"Q1 fails → nobody is forced out in the closing hour; the inventory and cascade
stories are both wrong and the mechanism question closes."* That is the branch the data take, and the census
reaches it by the route §6 did not name — an equivalence bound rather than a directional t, because a
symmetry claim cannot be established by failing to reject.

**What is settled.**

1. **There is no one-sided closing flow after a ≥1 σ decline.** ES's arm imbalance is +0.0009 at t +0.21 with
   exactly half the sessions net-sell, it sits below the median of its own enumerated rotation null, and a
   material one-sided imbalance is excluded on three of four roots. **The forced-seller premise — retail or
   institutional — does not hold on this window.**
2. **Nothing accelerates into the deadline.** Every slope is zero within noise; the one positive contrast
   tops out at t +1.94.
3. **The named counterparty is present and elevated.** Small-lot participation in the closing hour, measured
   against the session's own midday baseline and against other sessions, is up on all four roots and at 2 SE
   on three. It is the first direct evidence in this line of the principal's crowd in the right window.
4. **And it is not the seller.** The micro contract is *less* sell-tilted than its mini, on arm sessions at
   t −2.27. Combined with (1), the crowd is present, two-sided, and if anything leaning long — which matches
   the retail-flow literature this programme already recorded (*with the body, against only the extreme*) and
   contradicts a stop cascade.

**What the census cannot say, stated rather than implied.** It cannot identify who *does* sell: the seller
is not resolvable at a lot size this fixture carries, and `lot1`/`lot_le2` are unsigned, so even a perfect
lot-size proxy could not be conditioned on side here. It cannot connect flow to price, because no return is
scored. And with 26 arm sessions a between-session comparison is weak — which is why every finding above that
carries weight is a **within-session** comparison, and the record labels which is which.

**Multiplicity, disclosed (R13/R14).** **103** comparisons, across five questions, four roots and two lenses.
No single margin here should be read as a discovery on that look count. What carries weight is the **shape**:
Q1 near zero on every root with the bound excluding a material effect on three, Q2 at zero on every root, and
Q3's DiD positive on every root by two different measures. Agreement across four roots and two constructions
is the evidence; a t of +2.5 among 103 looks is not.

**The prior was right about the outcome and wrong about which leg would carry it.** §6's honest prior put Q1
at 65 % and Q3/Q4 at 10 %, expecting "real, one-sided and institutional". The census found the **opposite
decomposition**: the one-sidedness is absent and the small-lot signature is present. Both of the low-prior
questions produced the informative numbers, and the high-prior one produced a null with a usable bound.

## 8. Disposition of the line

**The mechanism question closes and the D622 hour keeps its specificity without an explanation.** D622
established that 14:00 → 15:00 → 16:00 is specific to the equity index roots and is the family maximum of 21
hour pairs, with the closing hour taking 23.69 % of session volume on arm days against 20.70 % (t +7.93).
This census confirms the volume (2.02× midday per minute on ES) and confirms that the extra volume is
slightly more retail than normal — and establishes that it is **balanced**, so the inventory-discharge and
stop-cascade readings of that volume are both excluded.

**No candidate, no component, no book entry.** Nothing here is scored against a return and nothing is
tradeable: D622 §5 already priced its own arm at net +$9.49 a trade on 182 trades, Sharpe 0.375 with Sortino
beside it, 29 years to confirm, and this census gives no reason to revisit that.

**The 2024+ ES slice remains unspent for every return-bearing construction**, as this record declares for the
third time after D510/D511 and D617. **D485's reserve, 2026-07-01 → 2026-09-10, is unread**, asserted from
both sides by the runner.

**What would reopen it, stated so it is not re-derived later.** Not more conditioning on this sample — four
rounds of that in D622 produced no cell at 2 SE and this census's 103 looks produced no single decisive
margin. It would take a fixture that resolves the **seller**: signed flow with trade size conditioned on
aggressor side, which means rebuilding `fut_micro_flow_5m.csv.gz` from the `tbbo` tape with a
(side × lot-bucket) cross rather than the two unsigned lot sums it carries now. That is a builder change on
data already on disk and costs no money — and it is the only remaining step on this axis that would add
information rather than another look.
