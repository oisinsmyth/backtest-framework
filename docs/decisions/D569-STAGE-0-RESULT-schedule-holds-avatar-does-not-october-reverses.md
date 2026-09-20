# D569 STAGE 0 RESULT — the soybean harvest schedule **holds where corn's failed**: the short spread earns **+0.42 bp a positioned day against −1.15 always-on** (the same short *loses* every other month of the year, most in June–August), the placement rank is **0.972 exact**, and the one declared real-time stocks-to-use cut **selects** (four open windows, all positive, +0.71 % against +0.16 %); but **the avatar's two tests fail** — the curve is not inverted at formation and the commercial net short *falls* through harvest — **2012 is half the total**, and on the rule-rolled object **October reverses**

*2026-09-20. Design committed in D569 (`7b06f8f`) before this ran. Diagnostic: 2011 → 2023,
thirteen harvests; no pre-registration produced; nothing from 2024-01-01 on was read on any
source (WASDE fixture filtered first: 978 of 1,170 rows). Runner
`scripts/stage0_d569_soybean_addendum.py`, output `data/stage0_d569_soybean.json`, 25 s. Seven
audits, each proven to raise. D567's soybean table was seen and is disclosed in the design; the
gate's composition was derivable from it and is what it was derived to be (open 2016, 2021,
2022, 2023).*

**The declared rule for what follows resolves to: the schedule may be pre-registered, as seen,
with the avatar recorded as unsupported.** T1, T4 and T5 hold; T7 fails. That is the principal's
call, and this record adds three things the rule did not weigh: which object, 2012, and cost.

---

## 1. The nine tests

Object **A** is the rule-rolled first-nearby spread (delivery ≥ *m*+2: X/F in September and
October, F/H in November), short T1 / long T2, masked September → November; unmasked it is the
control. Object **B** is D567's F/H survival pair held through the window. Returns are the
*short's*: positive means the spread widened.

| # | test | predicted | observed | |
|---|---|---|---|---|
| **T1** control per day | window > 1.5 × always-on, off-window ≤ 0 | window **+0.42 bp** a day; always-on **−1.15**; off-window **−1.67**; window Sharpe +0.41 vs control **−0.72** (2011–23) | **holds** — the short is right only at harvest |
| **T2** per month (A) | each month ≥ 8 of 13; no month > 60 % of the total | Sep +0.15 % (10 of 13, 55 %); **Oct −0.09 % (7 of 13)**; Nov +0.21 % (8 of 13, **79 %**) | **fails** on A; on **B**: Sep +0.27 % (10), Oct +0.05 % (8), Nov +0.21 % (8), shares 50 / 9 / 40 % |
| **T3** calendar profile, always-on short, bp a day | Sep, Oct, Nov the three best | Jan −0.3, Feb −0.7, Mar −0.6, Apr −1.9, May −1.2, **Jun −2.8, Jul −3.7, Aug −2.2**, **Sep +0.7**, Oct −0.4, **Nov +1.0**, Dec −1.4; best three Nov, Sep, Jan | **fails** by 0.1 bp (October is fourth); the shape is the mechanism's — the nearby gains on the deferred all summer and gives it back at harvest |
| **T4** placement rank | ≥ 0.90 | **0.972** (observed +0.41; null p50 −0.44, p95 +0.33; 2,850 offsets, exact) | **holds** |
| **T5** real-time gate | gated mean more negative (the short's larger), hit ≥ | open 2016, 2021, 2022, 2023: **+0.71 %, 4 of 4**; ungated over the eleven decidable +0.16 %, 7 of 11; the seven flat years **−0.16 %** | **holds** — the cut selects here, where corn's did not |
| **T6** the formation inverse | S/U → August basis > +0.5; basis → spread > +0.3 | +0.44 (p 0.14); +0.24 (p 0.42); the curve is inverted at formation in **two** years (2012, 2013) | **fails** — the widening is a carry widening, not an inverse collapsing |
| **T7** COT through the window | commercial net short rises ≥ 9 of 13; Δ vs spread < −0.3 | rises **5 of 13**, mean change **−0.027**; Spearman **+0.57** (p 0.045), the *wrong* sign | **fails** — commercials *cover* into harvest, and the spread widens most when they cover least |
| **T8** without 2012 (A) | mean ≤ −0.25 % (short +0.25 %), ≥ 10 of 12 | A: +0.16 %, 8 of 12, **2012 is 46 % of the total**; B: +0.28 %, **10 of 12**, 2012 is 50 % | **fails** on A, holds on B's letter; either way 2012 is half |
| **T9** tail | worst month > −1.5 % | **−1.29 %** (October 2013) | **holds** |

Per year, the short's return, A / B: 2011 +0.18 / +0.74, **2012 +1.61 / +3.47**, 2013 −1.08 /
+0.03, 2014 −0.31 / −0.17, 2015 −0.40 / +0.08, 2016 +0.81 / +0.62, 2017 +0.29 / +0.21, 2018
−0.20 / −0.09, 2019 +0.43 / +0.23, 2020 +0.17 / +0.05, 2021 +0.50 / +0.36, 2022 +0.34 / +0.21,
2023 **+1.17 / +1.17**. A: mean +0.27 %, 9 of 13; B: mean +0.53 %, 11 of 13 (D567's table,
reproduced on the daily book).

**The dollar line, one ZS a leg, information only:** σ **$50** a positioned day; net Sharpe /
Sortino **+0.66 / +1.01** on 2016–2023 and +0.29 on 2011–2023; +$1,526 over thirteen years
against **$962 of cost** — A rolls X/F into F/H at the end of every October (eight sides a
window), and cost is **39 % of gross**. B has no roll: four sides.

## 2. What the tests say

**The schedule is real on soybeans in the way it was not on corn.** The always-on short spread
loses 1.15 bp a day and loses most in June, July and August — the nearby strengthens against
the deferred through the growing season — and earns only in September and November. That is
the shape the re-derived avatar predicts: something bids the nearby through the summer and the
harvest releases it. The placement null puts the harvest mask at the 97th percentile of every
three-month placement, exact.

**But the avatar's own two tests fail.** The curve is not inverted at the end of August except
in 2012 and 2013 (the two drought-adjacent years); the ordinary state at formation is a carry
that then widens further. And the party the avatar names does not show up as the design said:
commercial net short *falls* through harvest in 8 of 13 years, and the years it falls least are
the years the spread widens most (ρ +0.57, p 0.045 — a real relation with the opposite sign to
the one predicted). Read literally: the widening is largest when commercials are *not* covering,
i.e. when the merchant side stays short — which is the merchant-at-harvest story D567 wrote and
then rejected on the stocks-to-use sign. The two avatars are each half right and the record
cannot choose between them on thirteen observations.

**The state variable selects in real time.** One declared cut — the August stocks-to-use at or
below the median of prior Augusts — opened four windows, and all four paid, at four times the
ungated mean; the seven flat years were net losers for the short. That is the outcome corn's
gate did not produce. Its composition was derivable from the seen table before the run and the
design said so; four windows is four windows.

**Two honest weights against it.** 2012 — the drought year, where the front fell 18 % over the
window — is half the thirteen-year total on either object. Without it, A pays in 8 of 12 and B
in 10 of 12 at +0.28 %. And the object matters: the rule-rolled A, which is what a
flat-by-default runner would hold, gives back October (−0.09 %, 7 of 13) on the X/F leg and
pays a roll; the survival pair B, which is what D567 saw, is smooth across the three months
and cheaper. A pre-registration would be on B with A's always-on series as its control — an
object that exists only three months a year, whose per-day comparison is therefore against a
different pair the other nine.

## 3. What follows, and what is not licensed

Under the design's own rule the schedule may be pre-registered, as seen, avatar unsupported,
on the principal's word, with the ZS 2024+ slice (one full window and the 2023 window's
December-adjacent nothing — the 2024 and 2025 harvests, six positioned months) as the only
clean test. This record's addition is that the pre-registration, if taken, should name **B**
(F/H, formed at August's last session, held to November's last, four sides), carry the gate as
a secondary cell with its cut unchanged, predict its hit as well as its mean, and predict the
without-2012 mean, because the in-sample number is a drought.

**Not licensed:** any month outside September → November (June–August's −3 bp a day for the
short is the same mechanism from the other side and would be a *long* spread in summer — a
different construction, unseen as a schedule, Stage 0 material); any cut other than the one
declared; any use of the T7 sign as a signal.
