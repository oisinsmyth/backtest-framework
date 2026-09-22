# D622 STAGE 0 RESULT — the hour pair's specificity is established; the mechanism is UNTESTED rather than refuted, because every discriminating margin is inside two standard errors

**Pre-registration:** [`D622`](D622-PRE-REG-the-last-hour-decline-and-who-must-be-flat.md), committed alone
before this runner existed. **Runner:** `scripts/stage0_d622_close_inventory.py` ·
**artifact:** `data/stage0_d622_close_inventory.json` · 2.3 s · in-sample 2016-01-04 → 2023-12-29, 1,993 ES
sessions and eight roots of hourly bars. **No holdout was read; the 2024+ slice is untouched.**

*The filename retains "it does not revert" from the first version of this record. That claim is withdrawn in
§0 and the title above is the corrected one; the path is left alone because renaming a committed record
breaks the citation anchors that point at it.*

## 0. AMENDED — the first version called two unresolved tests failures

The principal pushed back on P8 with a specific suspicion: that its mean lived in the tail, with crashes and
genuine repricing extending it. That is correct, and checking it exposed a larger error covering three
predictions.

**What was wrong.** P4, P6 and P8 were judged on point estimates — "the third leg exceeds the first", "held
beats broke", "the mean is negative" — without applying [D373](D373-RESULT-the-winners-dip-is-the-retired-book-and-one-GME-trade.md)'s
rule that **a margin within two standard errors is UNRESOLVED**. Every one of their margins is inside 2 SE:

| | margin | SE | t | published | correct |
|---|---:|---:|---:|---|---|
| P4 leg3 − leg1, paired | +0.95 bp | 4.18 | **+0.23** | PASS | **UNRESOLVED** |
| P6 broke − held | −5.00 bp | 11.01 | **−0.45** | FAIL | **UNRESOLVED** |
| P8 overnight | −9.19 bp | 9.56 | **−0.96** | FAIL | **UNRESOLVED** |
| P8 next session | −5.24 bp | 12.04 | **−0.44** | FAIL | **UNRESOLVED** |
| P8 five sessions | −2.71 bp | 31.06 | **−0.09** | FAIL | **UNRESOLVED** |
| P8 deepest declines | −36.13 bp | 23.46 | **−1.54** | FAIL | **UNRESOLVED** |

**And the tail read confirms the principal's suspicion at the horizon that matters.** P8's overnight mean of
−9.19 bp has a **median of +1.30** — the sign flips — a symmetric 1 % trim of −5.51, and **50.5 % of
sessions revert**. Its five most negative sessions are **2020-03-13, 2020-03-06, 2020-03-11, 2020-03-05 and
2020-02-27: every one a COVID crash session.** The mean is those five days. At five sessions the median is
**+50.00 bp** against a mean of −2.71 and the trim is **+5.73** — mean and median disagree there too, and
58.2 % revert. Only the deepest-decline cell has mean, median and trim agreeing on continuation
(−36.13 / −31.15 / −31.85, 41.9 % reverting) and it is the smallest cell at n 62 and t −1.54.

**Three claims are withdrawn.** That "P8 fails"; that "the effect has no named counterparty again", which
manufactured a refutation out of a sample too small to produce one; and that the deferred signed-flow premise
check is "moot" — **it is not moot, it is now the only route that does not depend on this sample size.**

**The fix is in the runner, not only in this prose.** `resolve(margin, se)` applies the 2 SE rule and emits
`pass` / `fail` / `unresolved`, `tails()` reports the median and both-tail trims beside every mean and flags
a sign flip, and the self-test proves the rule labels rather than rubber-stamps: pass at 10 SE, fail at
−10 SE, unresolved at 1.0 SE, at 1.9 SE and on a zero SE.

## VERDICT

> **THE SPECIFICITY IS ESTABLISHED AND THE MECHANISM IS UNTESTED.** Passed **P5, P7, P9**; **UNRESOLVED
> P4, P6, P8**; failed **none**. Something is genuinely specific to this hour pair and these instruments, it
> comes with more volume than usual, and this sample cannot separate an inventory discharge from a
> repricing. The mechanism is neither supported nor refuted.

## 1. The arm, and the three predictions that pass

`H1 = r(14:00→15:00)/σ`, short 15:00 → 16:00 when `H1 ≤ −1.0` — the threshold declared in the record, not
tuned. **182 sessions, 9.1 % of the window; mean +6.83 bp; t +1.23; hit 58.8 %.** Against the **enumerated**
rotation null of the signal side rotated as a block over 1,974 offsets: observed **+6.83** against p50 +0.06
and **p95 +4.40, rank 0.9965** — clears.

**P7 — the forced trade arrives. ESTABLISHED, and it is the strongest number here.** The closing hour takes
**23.69 %** of session volume on arm days against **20.70 %** otherwise, on an even share of 15.38 %: a
difference of **+0.0299 at t +7.93**, with the medians agreeing (0.2334 against 0.2007). A hump of **1.54×**
against 1.35×, above the top of D530's unconditional 1.10×–1.48× baseline. Something does arrive.

**P9 — the deadline placebo. PASSES as a ranking, which is tail-robust.** The tested pair is the **family
maximum of all 21 usable ES hour pairs**, rank 21 of 21, at +8.88 bp against the runner-up h21→h22's +5.32,
then h12→h13 at +4.24 and h15→h16 at +3.79. The pair was a **1-of-22 selection** from FINDINGS §81's census
and it survives being priced as one.

**P5 — the cross-section. Passes its declared criterion; the evidence is weaker than three roots suggests.**

| root | | n | mean | z | hit |
|---|---|---:|---:|---:|---:|
| ES | index | 180 | +8.88 bp | +1.57 | 0.606 |
| NQ | index | 177 | +12.69 bp | +2.04 | 0.582 |
| YM | index | 171 | +7.04 bp | +1.53 | 0.556 |
| ZN · ZB · GC · CL · 6E | other | 131–247 | −0.57 · −0.00 · +0.92 · −4.01 · +0.11 | mean \|z\| **0.538** | 0.39–0.49 |

All three index roots agree in sign and the five others read nothing, which is the declared criterion and
which is exactly where D530's version died (its per-root z was NQ +0.52, RTY +0.65, ES −0.45, YM −0.54). But
**three-of-three sign agreement alone has probability 0.25 under the null**, and ES, NQ and YM are three
views of one equity complex rather than three independent instruments. The honest reading is *one marginal
observation on the index complex at z ≈ 1.5–2.0, against nothing on five unrelated roots* — suggestive of
instrument specificity, not three confirmations of it.

## 2. The three predictions the sample cannot resolve

**P8 — the reversal test.** UNRESOLVED at all four horizons, with the tail structure in §0. The direction of
the point estimates is continuation, the medians disagree with the means at two of four horizons, and no
horizon reaches 1.6 SE. **This is the test the mechanism turns on and the sample cannot run it.**

**P6 — the level.** UNRESOLVED, and its three central measures disagree in *direction*: the mean favours
sessions that held above the prior low (+9.99 against +5.00), the **median favours those that broke it**
(+8.39 against +4.26), and the symmetric trim goes back the other way (+12.21 against +8.11). A difference of
−5.00 bp against a pooled SE of 11.01. Nothing can be concluded, including the thing the first version of
this record concluded.

**P4 — the deadline binds.** UNRESOLVED. The legs read +3.07, −0.26, +4.02 bp, so the third does exceed the
first as a point comparison, but paired across the same sessions the difference is **+0.95 bp at t +0.23**
and the middle leg is negative. There is no ramp here, and no evidence against one either.

## 3. The asymmetry that motivated the record does not survive its declared threshold

This part of the first version stands. §6 of the pre-registration disclosed a median-|H1| split in which the
down side earned $5.27 a trade at t 3.04 against the up side's $1.92 at t 1.23 — the asymmetry that made an
*asymmetric* forced seller the hypothesis at all. At the **declared 1.0σ threshold**: down arm **+6.83 bp
(t +1.23)** on 182 sessions, up arm **+5.27 bp (t +1.34)** on 187. A gap of **1.56 bp with the up side
carrying the larger t**. The effect is very nearly symmetric once the threshold is declared rather than
fitted to the median, which is why it was declared in advance — and it removes the observation that pointed
at an asymmetric participant, independently of P8.

## 4. What is established, and what is open

**Established.** Something is specific to 14:00 → 15:00 → 16:00 on the equity index roots: it is the maximum
of 21 hour pairs on its own clock, it is absent on five non-index roots, and it comes with a closing-hour
volume share 3 percentage points higher than normal at t 7.93. The arm clears its enumerated rotation null
at rank 0.9965.

**Open.** What it is. The inventory hypothesis of §1 of the pre-registration is untested: its discriminating
prediction needs a reversal signature that 182 sessions cannot measure, and the asymmetry that motivated it
is absent at the declared threshold. Repricing on late-day information remains equally consistent with
everything above. **The effect still has no identified counterparty — but this study did not refute one, it
failed to test for one.**

**The route that does not depend on the sample size.** The deferred premise check in §4 of the
pre-registration: signed aggressor flow on the reserved `tbbo` year, read as a census in D510/D511's shape
with no return scored, asking directly whether liquidity providers are long into the close on these sessions
and sell. [D617](D617-FIXTURE-the-ES-option-signed-flow-census-from-the-tbbo-year.md) has established the
data is present and clean; D485 established the convention on futures. That is a premise test, not a price
test, so it is not hostage to 182 observations.

## 5. Is there a tradeable strategy here? No — and the reason is not the edge

Asked directly, and answered with the arithmetic rather than a judgement. Two candidates emerged from this
programme; both are scored at one MES against the $4.25 round trip the account pays.

**AMENDED 2026-09-22 (second amendment): this table first carried a Sharpe with NO SORTINO beside it, which
breaches R17, and its figures were computed in a scratchpad script rather than in the runner — the exact error
shape CLAUDE.md names after D466.** Row A is now computed by `component_line()` inside
`scripts/stage0_d622_close_inventory.py`, is a declared output (`component` in `REQUIRED_OUTPUTS`), and
annualises by the book's **own 22.8 trades a year** rather than `sqrt(252)`. The runner reproduces every
scratchpad figure — net $+9.49, t +1.06, maxDD $1,512, $1,728 total — so nothing in the disposition moves; the
Sharpe reads 0.376 rather than 0.375 on the runner's variance convention.

| | trades (per year) | net/trade | median net | t | gross Sharpe / Sortino | **net Sharpe / Sortino** | maxDD vs $2,000 | 8-year total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **A** this record's arm | 182 (22.8) | **+$9.49** | +$7.63 | +1.06 | +0.544 / +0.568 | **+0.376 / +0.403** | $1,512 (0.76×) | $1,728 |
| **B** the D618 §3d MACD cell | 342 (43) | +$3.70 | — | +1.32 | — | +0.468 / **not computed** | 0.42× | $1,265 |
| **A + B combined** | 475 (59) | +$2.67 | — | **+0.74** | — | **+0.261** / **not computed** | 0.80× | $1,269 |

**The two rows marked "not computed" are a stated debt, not an omission to be read past.** B's and the union's
P&L series were built outside any runner, so no Sortino exists for them and this record will not invent one.
B's own record ([D618](D618-STAGE-0-RESULT-the-band-around-the-price-was-the-signal.md) §3d) reports **337**
trades where this table says 342, which is a second reason to treat its row as indicative. Closing that debt
means giving the MACD cell a `component_line()` in **its** runner; until then only row A meets the ledger's
standard for a component number, and **row A does not clear the bar** — so the debt changes no disposition.

Three independent reasons, none of which is "the edge is negative":

1. **Neither clears the standard.** `COMPONENTS_PROP.md` wants net Sharpe 0.4–0.6; A is **0.376 with a
   Sortino of 0.403** — the downside deviation is *smaller* than the total, so the distribution is mildly
   favourable and the shortfall is in the mean, not in the tail — and B is 0.468. Neither t exceeds 1.4.
2. **They do not combine — they are one construction twice.** On the 49 sessions where both fire their P&L
   correlates **+0.876**, and those sessions carry the money (A earns $50.38 and B $28.49 on them, against
   $9.49 and $3.70 overall). Combining *dilutes*: Sharpe falls from 0.375 to **0.261** and the drawdown
   worsens. The five-components-at-ρ-under-0.3 plan needs independent constructions and these are not.
3. **Neither can ever be confirmed.** Trades for t = 2.0: A **651 (29 years)**, B **785 (18 years)**,
   combined **3,483 (59 years)**. Expected t on a two-year holdout *if the edge is entirely real*: +0.53,
   +0.66, +0.37.

And the scale settles it without statistics: **$1,728 over eight years on one MES**, about $216 a year, is
the best total this programme produced.

## 5a. Is the arm a subset of a larger family? Asked, and answered three ways — no

The arm takes 182 of 1,993 sessions. If the relation were **continuous in H1** the family would be "every
session, sized", which is 1,933 usable observations rather than 182 and would dissolve the power problem. It
is not continuous.

| decile of H1 | H1 range | n | mean y | t | the book's return |
|---:|---:|---:|---:|---:|---:|
| 1 | −13.18 … −0.93 | 194 | −5.80 | −1.07 | **+5.80** |
| 2–7 | −0.93 … +0.35 | 1,159 | −0.14 to +1.29 | \|t\| ≤ 0.64 | **≈ 0** |
| 8 | +0.35 … +0.55 | 193 | **−5.40** | **−2.02** | **−5.40** |
| 9 | +0.55 … +0.97 | 193 | +4.13 | +2.28 | +4.13 |
| 10 | +0.97 … +9.82 | 194 | +4.09 | +1.06 | +4.09 |

**The middle six deciles contribute nothing and decile 8 contradicts the pattern at t −2.02.** A linear fit
over all sessions reads `y = −0.387 + 4.683·H1` at **t +5.77**, which looks decisive — and it is a
**magnitude** relation, not a sign relation. The sign-only book, which is all one micro contract can express,
earns **+1.04 bp at t +1.16** over 1,933 sessions: **gross $1.72 against a $4.25 fee**. This is D614's wall
re-encountered in a new place — *"the regression's expected move is magnitude-weighted and lives in the tail;
a sign-only book, which is all one lot can express, realises 1.16 bp"*. The larger family exists
statistically and is not expressible at the size this account trades.

**Nor is it diversifiable across the index complex.** Each root on its own micro contract and its own fee:

| root | n (per yr) | mean | gross | fee | net | t | Sharpe (own rate) | fee share of gross |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ES / MES | 180 (22) | +8.88 bp | $13.35 | $4.25 | +$9.10 | +1.07 | +0.380 | 0.32 |
| **NQ / MNQ** | 177 (22) | **+12.69 bp** | $21.17 | **$3.50** | **+$17.67** | **+1.71** | **+0.605** | **0.17** |
| YM / MYM | 171 (21) | +7.04 bp | $9.39 | $3.50 | +$5.89 | +0.96 | +0.340 | 0.37 |

Their net P&L series correlate **0.96 to 0.99**. They are three views of one trade, so pooling *loses*: an
equal-weight book over 226 sessions reads net +$7.40 at t +1.00 and **Sharpe 0.355 — below NQ alone at
0.605** — and holding all three contracts at once gives net +$25.55 a session at t +1.40 with a maximum
drawdown of **$3,909, which is 1.95× a $50,000 account's allowance** and therefore not tradeable there.

**The one thing worth recording from this.** `NQ` is the better expression and by a clear margin: Sharpe
**0.605** is inside `COMPONENTS_PROP.md`'s 0.4–0.6 band at its top, and the reason is structural rather than
statistical — **MNQ's fee is 17 % of the gross against MES's 32 %**, which is FINDINGS §81's fee-share lever
appearing across instruments instead of across hours. It is still 22 trades a year at t 1.71, so the pooled
book needs **897 trades, 32 years**, for t = 2.0 and a two-year holdout would return an expected **+0.50**.

So the family that would rescue this cannot be found across the conditioner's range or across the index
complex, because both are the same trade. It would have to be across **deadlines or mechanisms** — genuinely
independent members — and every candidate this programme has produced has turned out to be one trade in
different clothes: ρ **+0.876** between the two conditioners on one instrument (§5), ρ **0.96–0.99** across
three instruments on one conditioner (here).

## 5b. The principal's volume-burst family, and the cascade-versus-repricing discriminator

Two further rounds of disclosed looks on the spent window, both prompted by the principal and both worth
recording because one of them produced the only orthogonal conditioner this programme has found.

**The midday volume burst is genuinely independent of the price move, which nothing else here is.** Defined
before looking as midday volume (11:00–14:00 ET) over its trailing 20-session median, with a declared
threshold of 1.25: **corr with H1 is +0.0015** and with |H1| only +0.230. Every previous candidate correlated
+0.876 (two conditioners, one instrument) to 0.96–0.99 (one conditioner, three instruments). Conditioning the
short arm on it roughly doubles the edge — **+12.02 bp (n 73) against +3.36 (n 109)**, with medians (+11.66
against +4.27) and trims (+13.86 against +6.78) agreeing, so it is not tail-driven — but the interaction is
**+8.66 bp at t +0.77, UNRESOLVED**, and the quintile shape is not monotone (Q2 +10.06 against Q4 +4.92,
Q5 +13.77).

**On the long side, "the opposite" loses.** Continuation after a ≥1σ rise reads +5.27 bp (t 1.34); fading the
rise is its mirror at −5.27. And the burst does not help longs (+4.52, **median −0.59**), so whatever the
burst detects acts only on the short side.

**The structural point, which matters more than any of those cells.** A volume conditioner has **no
direction**, so it can only ever be a filter or an interaction term — it can never generate its own trades.
Filters trade sample for per-trade edge: the burst cell's net rises to **+$17.12** from $9.49 while its rate
falls to **9 trades a year**, needing about 206 trades or **23 years** for t = 2.0. **An orthogonal but
directionless conditioner therefore cannot relieve a sample-size constraint — only an orthogonal DIRECTIONAL
signal can, and this programme has not produced one.**

**The cascade-versus-repricing discriminator.** A stop cascade fires into a thinning book — a large move on
light volume, high impact per contract. Informed size is the opposite. Split at the arm's own medians:

| | n | mean | t | median | trim |
|---|---:|---:|---:|---:|---:|
| high impact per contract (cascade signature) | 91 | +3.81 | +0.41 | +11.38 | +7.94 |
| low impact per contract | 91 | +9.86 | +1.63 | +2.80 | +10.16 |
| **high trigger-hour volume (size signature)** | 91 | **+12.78** | **+1.71** | +8.39 | +14.27 |
| low trigger-hour volume | 91 | +0.89 | +0.11 | +4.44 | +5.20 |

Both halves point away from the cascade: the effect is stronger on **heavy** volume at **low** impact per
contract, and on the volume half mean, median and trim all agree. Neither reaches 2 SE (−0.54 and +1.07).
**And the impact measure is partly circular** — impact per contract correlates **+0.693 with |H1|**, the
quantity that defines the arm — so the conclusion rests on the volume half, itself +0.444 correlated.

**One fact is cascade-consistent, and it is a premise observation rather than a return claim.** Volume
**builds** through the trigger hour on arm sessions: median acceleration (last 20 minutes over first 20)
**1.202**, against **0.982** on ordinary sessions. Conditioning returns on that acceleration gives t +0.39,
but the acceleration itself is a real difference in the data.

**Contamination ranking of the four conditioners**, which is the reusable part: midday burst +0.001 with H1
and +0.230 with |H1|; acceleration −0.138 and +0.156; trigger-hour burst −0.111 and +0.444; impact per
contract −0.023 and **+0.693**. The two cleanest are the principal's burst and the acceleration.

**Four rounds of subgroup analysis have now been run on this window and not one cell has reached 2 SE.** Each
round lowers the evidential value of the next. The signed-flow census that follows is the only remaining step
that adds *information* rather than looks, and it is pre-registered separately.

## 6. What is spent

The in-sample window was read for six predictions, the reproductions, the tail analysis and the viability
arithmetic. **The 2024+ slice was not read.** The holdout gate in the pre-registration opened on P5 and P7,
but with P8 unresolved there is nothing for a holdout to confirm and §5's power arithmetic says a read could
not resolve it anyway.

Every audit raised on its break: leg additivity to **3.5e-12 bp** with a one-bp slip refused and the window
being its own third leg refused; the rotation null refusing a constant outcome and refusing too few offsets;
the margin rule proven to label rather than rubber-stamp; the tail read proven to flag a mean/median sign
flip; the declared-output guard firing on a missing block.

**Nothing is admitted and no line is closed** — under R15 that is the principal's call.
