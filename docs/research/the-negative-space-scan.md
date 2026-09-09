# The negative-space scan — seven leads from what the record has never looked at

**Status: RESEARCH RECORD. Not a pre-registration, not a result, and it closes nothing.**
No runner exists for anything below. No null has been run. No book is proposed. **Every
figure quoted from an existing record is attributed; the handful of new measurements are
tagged `[MEASURED HERE]` and name the probe that produced them.** Only the principal closes
a research avenue (R15); this record opens nothing either, it enumerates.

**Date:** 2026-09-09 · **Area:** signal research · **personal track**
**Holdout reads spent by this record: 0. Programme total: 1** (D371, 2026-09-07).

---

## 0. Why this record exists, and what it is NOT

The principal asked for a scan for leads across strategies, indicators, regime detectors and
"other categories", with one binding constraint: **do not overlap research already done.**

This record answers by working the *complement* rather than the frontier.
[`the-signal-hunt-part2.md`](the-signal-hunt-part2.md) enumerated candidates the **catalogue**
could not express — quantities in the same asset, on the same panel, at the same frequency.
That hunt ran to eight candidates, D391 → D397, and was **retired by the principal on
2026-09-09** ([D396](../decisions/D396-RETIREMENT-the-sign-sequence-chain.md)).

**This record asks a different question: which whole CATEGORIES has the programme never
touched at all?** Not "which score is missing from the table" but "which axis of variation has
never been in a runner". The two are different searches and they do not compete.

**One thing this record deliberately does not do.** It does not re-propose the three ideas in
[`future-strategies.md`](../future-strategies.md) — the ATM shelf issuer, cash runway from
XBRL, and the merger-arb acquirer. Those are reasoned, written down, and still owe their
premise numbers. Re-listing them here as leads would be double-counting the same thinking.
§6 says what they still owe and nothing more.

---

## 1. How non-overlap was established, so the claim is auditable

Every category below was grepped across **`docs/decisions/` (478 files), `docs/FINDINGS.md`,
`docs/STACK.md` and `scripts/`** before it was written up. The audit and its hit counts:

| category | doc hits | script hits | reading |
|---|---:|---:|---|
| seasonality / turn-of-month / day-of-week / FOMC | **0** | **0** | never computed |
| lead–lag, cross-sectional information transfer | **0** | **0** | never computed |
| yield curve, credit spread, term structure | **0** | **0** | never computed |
| short interest, put–call, insider, 13F | **0** | **0** | never fetched |
| VIX / volatility index | 0 | 1 | the 1 is a ticker in a universe list, not a study |
| HMM / regime switching / state classifier | 0 | 0 | the 9 raw `hmm` hits are a local variable `hmm` in `run_d377_hedge.py:366` |
| cross-asset gate (`TLT`/`HYG` as a *conditioner*) | 4 | 5 | **all are universe membership** — D188's ETF cross-section, D239/D240's TSMOM arms, D263's COT pairing, and fetcher symbol lists. **No study has ever gated an equity book on another asset class.** |

**And the catalogue confirms it structurally.** All 49 scores across 8 families
([signal-hunt part 2 §3](the-signal-hunt-part2.md)) plus Axis I's three sign scores are
functions of **one name's own OHLCV window**. The one exception is `beta_63`, and its market
return is built from *the panel's own equal-weighted cross-section*
(`ragged_anomaly_scores` docstring). **Not one score reads `panel.dates`, and not one score
reads any series from outside the fixture.** Those are the two holes this record works.

### 1a. What the fixtures already support — `[MEASURED HERE]`

**Probe: `scripts/probe_negative_space_census.py` → `data/negative_space_census.json`.**
Read-only, nothing scored, one pass over each fixture. **It carries the assertion that R1's
whole "no fetch needed" claim rests on — that the two fixtures share their first and last bar
— and that assertion was proved able to fail** by moving the ETF fixture's last bar one day
in a scratch wrapper, which raised. A refetch that moves either span will now break the probe
rather than silently invalidating the lead.

| | |
|---|---|
| `us_shorts_daily_raw` | **1,573 names, 4,137,239 rows, 2010-01-04 → 2026-08-26**, ragged, 562 delisted + 122 collapsed |
| `etf_wide_daily_raw` | **551 symbols, 2010-01-04 → 2026-08-26** — and **417 of the 551 span the entire window** |
| **the join** | **Both fixtures start and end on the same bar.** A cross-asset series can be attached to the equity book with **no fetch, no key, and no new provider.** |

**Present, full 4,187-bar history, verified individually:** `TLT` `IEF` `SHY` (curve) ·
`HYG` `JNK` `LQD` (credit) · `GLD` `SLV` (metals) · `FXE` `FXY` (FX) · `SPY` `QQQ` `IWM` `IJR`
(size) · `XLF` `XLK` `XLE` `XLU` `XLP` `XLY` (sector) · `EEM` `EFA` (geography) · `SMH` `KRE`
(industry) · `BIL` (cash).

**Absent, and this is a real limitation stated up front:** `VXX`, `VIXY` (no volatility ETP),
`UUP`, `UDN` (no dollar index), `MTUM`, `USMV` (no factor ETFs). **So implied volatility and
the dollar are out of reach without a pull.** Realised volatility is not — the programme
already computes it, and C1b found it decisive (§7e of the signal hunt).

---

## 2. The scoring frame — seven axes, drawn from the record's own kill list

**These are the seven things that have actually killed studies here.** A lead is scored 0–3
on each, /21. **The scores are my judgement, not measurements**, and the reasoning is given
under each lead so a disagreement can be located rather than asserted.

| axis | 0 | 3 |
|---|---|---|
| **NEW** — non-overlap | already covered | zero coverage, audited in §1 |
| **DATA** — what it costs to reach | paid, or blocked | **already held and bar-aligned** |
| **COST** — does the payoff escape the spread wall | denominated in the spread | slow-and-large, or adds no turnover at all |
| **BREADTH** — against `n_eff ≈ 2.2` | one series, few independent episodes | the full cross-section |
| **KILL** — one cheap Stage-0 number | no cheap kill exists | one conditional, minutes to compute |
| **BASE** — immunity to the base-rate floor | ranks a quantity carrying price units | **selects no names at all** |
| **CEIL** — what it is worth if true | a diagnostic | a new selection axis for the whole book |

**Why these seven and not others** — each is a constraint the record paid for:

1. **The cost wall is a PRICE effect.** D284's `lng10` is the only construction in the
   programme to exceed `2c` (+24.10 bp, 2.41×) and it died on a **breakeven half-spread of
   11.36 bp/side against a 15 bp floor**, holding a **$13.19 median stock with a $1.92 tenth
   percentile and 25.7% of positions under five dollars** (FINDINGS §9).
2. **A reversal edge is denominated in the spread.** On the widest two deciles of the gap-up
   fade's own trades, gross is **+219.8 bp a trade against a 216.6 bp round trip**
   (`future-strategies.md` §0). Selection, timing, exits and sizing moved the net **4 to 19 bp**.
3. **Breadth saturates.** `n_eff` = **2.23 of 57 ETFs daily**, **2.17 of 57 at 15 minutes**
   (D383) — *26× more sampling buys none* — against **10.06 over a held single-name book**
   (D285 pre-registration).
4. **Base rates are large.** A purely random long earns **36.8 bp** on the price-tercile
   spread, **32.2** on momentum, **12.2** on volatility (D392's atlas). Anything ranking a
   price-carrying unit inherits that before it does anything (FINDINGS §14).
5. **Rarity in the cross-section says WHICH NAMES, never WHEN.** A fresh entry into the
   bottom 2% of ~1,000 names fires **5.2 times a bar** → **120 open positions at a 40-bar
   hold, 100% exposure, never flat** (D358 / FINDINGS §38). **Any flat-by-default
   construction must name a TIME-SERIES gate and null the gate separately.**
6. **Beating a path-shuffle null is nearly free** (the density line beat one at p = 7.2e-11
   and a rotated-density null at nothing). **The persistent-selector / time-rotation control
   is the test.**
7. **In-sample null strength does not forecast out-of-sample survival.** The momentum book
   cleared its rotation at **164 SE with 0 of 10,000 draws beating it** — and failed
   (PICKUP §0e).

---

## 3. Group R — state from OUTSIDE the fixture

### 3.1 R1 — the cross-asset regime state as the market-level gate ⭐ FIRST

**Score: NEW 3 · DATA 3 · COST 3 · BREADTH 1 · KILL 3 · BASE 3 · CEIL 2 = 18/21**

**The quantity.** Three states, each a ratio of two series the fixture already holds, each
reduced to its own trailing percentile so it carries no units:

```
credit    log(HYG / IEF)        high-yield against duration-matched governments
curve     log(IEF / SHY)        the belly against the front end
defensive log((XLU+XLP) / (XLY+XLK))   defensive against cyclical rotation
```

**Why it is not in the catalogue, precisely.** §1's audit: every one of the 52 scores is a
function of one name's own OHLCV, and the single exception (`beta_63`) builds its market
return from *the panel's own cross-section*. **The programme has never conditioned on a
series from another asset class.** Its four gates to date — the 200-day mean (D361), the
63-bar compounded return (D361), the calm-market sink (D362) and realised volatility (C1b) —
are all derived from the equity universe being traded. **A gate is only informative to the
extent it knows something the book does not, and these four know only what the book already
sees.**

**Mechanism.** Credit and the curve are the two places where a change in the discount rate
and in the price of default risk shows up *before* it shows up in equity dispersion, because
they are traded by a different set of participants with a different mandate. That is a
claim about **who is looking**, not about chart shape — and it is the only route in this
record that does not require the equity tape to have foreknowledge of itself.

**Direction declared, in advance:** widening credit (`HYG/IEF` falling) and defensive
rotation are **risk-off**; the gate **suppresses long exposure** in that state. The mirror —
a short arm gated on risk-off — is a mechanism check only, per FINDINGS §33's rule, because
this programme's short side has failed in every universe it has been measured in.

**THIS IS ALSO THE FIRST TESTABLE DRIVER OF THE PROGRAMME'S LARGEST OPEN NEGATIVE, and that
is the strongest argument for it.** [D389](../decisions/D389-RESULT-the-floor-is-ONE-factor-and-none-of-the-four-candidates-explains-it.md)
found that two unrelated books here co-move at **0.476**, that **it is ONE factor** (PC1
reproduces the pairwise rho to three decimals, 0.449 vs 0.449; PC2 is 0.006), and that **none
of the four candidates explains it** — slot mechanics 0.029, equal-weighting 0.031,
eligibility floor 0.052, shared hedge likewise. **Unattributed: 85% in A′, 98.5% in B.**
PICKUP §0d ranks this the most promising open lead in the programme and says where to look:
**"the factor lives in WHICH DAYS GET TRADED, not in the market on them."**

> **Every one of D389's four candidates was internal to the book's own machinery. A
> cross-asset state is external to all four, and "which days get traded" is exactly what a
> market-level state variable indexes.** No driver D389 could reach was of this kind. That
> makes R1 two questions in one runner, and the second is worth more than the first.

**Stage 0 — the measurement that kills it before any design.** One conditional, and it is
**C1b's lesson applied in advance rather than discovered afterwards**:

```
Q1  Does the state PERSIST?  Median episode length and the acf of the state itself.
    A conditioner with a one-bar half-life cannot gate a 40-bar hold. Measure the
    conditioner's own persistence BEFORE designing anything that conditions on it.

Q2  Does the state partition forward returns?  Equal-weighted floored-universe return
    over the next 20 bars, by state tercile, with the ERA split (FINDINGS §6: measured
    effects here are frequently one era).

Q3  THE ONE THAT DECIDES IT.  Does it survive a control for REALISED VOLATILITY?
    C1b withdrew §7d's dispersion finding on exactly this test -- "dispersion is not
    direction, but it very much is volatility", and volatility alone was decisive and
    more strongly. If the credit state is realised vol wearing a costume, it is dead,
    and that must be the pre-declared primary rather than a robustness note.
```

**The null, and it is unusually good here.** The state is **one market-level series**, so its
time rotation is a **finite group of `Td − 1` ≈ 4,000 offsets and is EXACTLY ENUMERABLE** —
sampling SE is then exactly zero, at roughly six minutes a cell. That is C2b's method
contribution, and it matters: **all four of D361's exact p95s came in ABOVE their published
200-draw values, and the one cell with a thin margin fell from +6.4 to +0.52.**

**BREADTH is why this scores 1 and not 3, and it is the honest weakness.** The gate is one
series with high autocorrelation over 4,187 bars. The number of genuinely independent regime
episodes is small — plausibly tens, not thousands — so the effective `n` judging the gate is
far below the bar count. **That must be reported as `n_eff` episodes, not as bars**, or the
precision will be overstated by an order of magnitude. It is the same error shape as D280's
"`t` on 2.2M name-bars is really `n` = 2,173 bars".

**The honest risk.** Credit and equity are both risk assets; a credit gate may simply be a
slower equity gate, which Q3 is written to catch. And **a gate cannot create an edge** — it
can only improve an existing book's Sharpe by being out at the right times. D346 measured
that half of what a searched gate buys is *being out of the market* rather than being out at
the right times (FINDINGS §46). **CEIL is 2 for that reason.**

---

## 4. Group K — the calendar

### 4.1 K1 — the calendar screen: three pre-declared hypotheses in one runner

**Score: NEW 3 · DATA 3 · COST 3 · BREADTH 1 · KILL 3 · BASE 3 · CEIL 1 = 17/21**

**Why one lead and not three.** `46 states × 138 triggers = 6,348 compounds` is the hazard
the signal hunt named at §4.6, and a calendar sweep has the same shape: date properties are
cheap to enumerate and nothing clears a best-of-many floor. **So the three hypotheses are
declared here, in writing, before the runner exists, and the floor is best-of-3 — disclosed,
not summed after the fact.**

```
K1a  TURN OF MONTH   bars [-1, +3] around the month-end boundary
K1b  DAY OF WEEK     the five weekday buckets
K1c  FOMC WINDOW     the 24h before a scheduled FOMC announcement
```

**Why it is not in the catalogue.** §1: **no score reads `panel.dates`.** The panel carries
them (`RaggedPanel.dates`, `ragged_panel.py:60`) and nothing has ever used them as anything
but an index.

**Mechanism.** K1a: 401(k) and pension inflows arrive on a payroll clock, and index funds
rebalance to a calendar — a flow that is **price-insensitive by mandate**, which is exactly
route (a) of `future-strategies.md` §0 ("somebody buys or sells for a reason unrelated to
price"). K1b is the weakest and is included because it costs nothing extra in the same
runner. K1c is the Lucca–Moench pre-announcement drift.

**BASE scores 3 — and this is the axis's real distinction.** A calendar rule **selects no
names.** It cannot tilt on the 36.8 bp price tercile, cannot tilt on momentum, cannot inherit
any of D392's base rates, because it holds the same book and changes only *when*. FINDINGS
§14's problem — a cross-sectional rank on a quantity carrying units ranks those units — is
answered by construction, not by a normalisation.

**COST scores 3 for the same reason.** K1a trades at most twelve times a year, and the
round trip amortises over a four-bar window rather than being the whole payoff.

**And it is the one honest answer to P1 that the record has never tried.** FINDINGS §38 rule
1 requires every flat-by-default construction to name a **time-series** gate, and D358 proved
a cross-sectional trigger cannot supply one at any rarity. **A calendar window IS a
time-series gate and nothing else** — it is out of the market by construction the rest of
the month.

**Stage 0.** Mean and median return of the equal-weighted floored universe inside each window
against all other bars, **split by era**, with the exactly-enumerated rotation null (as R1:
one market-level series, `Td − 1` offsets, SE zero).

**The honest risk, and it is large — CEIL is 1.** Turn-of-month is among the most heavily
documented and most heavily arbitraged effects in the literature, and it is widely reported
to have decayed. **The fixture starts 2010-01-04, which is precisely the era in which the
decay is claimed.** So the realistic outcome is a small or absent effect. **That is a reason
to spend twenty minutes on it, not a reason to skip it** — it is the cheapest measurement in
this record, it is a clean out-of-the-box test of a public claim in the exact window where
the claim is contested, and a *null* result is worth having on file because it closes a
category that would otherwise keep suggesting itself.

---

## 5. Group X — the cross-section, relative to something

### 5.1 X1 — cluster-residual reversal

**Score: NEW 2 · DATA 3 · COST 1 · BREADTH 3 · KILL 3 · BASE 2 · CEIL 3 = 17/21**

**The quantity.** Partition the 1,573 names into `k` clusters by correlation of returns over
a trailing window — **data-driven, from the panel itself, so no external sector map is needed
and nothing is fetched.** Then rank on the residual:

```
resid_5(i,t)  =  r_5(i,t)  −  r_5(cluster(i), t)
```

**Why NEW scores 2 and not 3, stated first because it is the weakest part of the claim.**
Plain cross-sectional reversal **has been run and it failed**:
[D285](../decisions/D285-the-factor-neutral-book.md), the factor-neutral book — long the
lowest `hist_L`, short the highest — returned **zero survivors across 18 cells**
(`data/d285_factor_neutral_summary.json`), and D285's own pre-registration says the prior
was *"a known effect that usually does not survive costs"*. **A residualised version is a
variation on a measured failure unless the residualisation changes the mechanism, and the
burden is on this lead to say why it does.**

**The argument that it does.** D285 went long and short the two tails of the *same* score, so
both legs carried whatever common factor the score loads on. **Residualising removes the
systematic part of the move before ranking**, and the mechanism claim is specific: *the
systematic part of a fall is not compensated, the idiosyncratic part is.* A name that fell 5%
while its cluster fell 5% has not been sold by anyone in particular; a name that fell 5%
while its cluster rose has. **That is a different selection, not a different parameter** —
and it is the FINDINGS §14 problem answered by subtraction.

**COST scores 1 and it is the binding constraint.** This is a reversal payoff, and
`future-strategies.md` §0 establishes that a reversal edge **is** the spread — +219.8 gross
against a 216.6 round trip on the fade's widest deciles. **A pre-registration must carry the
diagnostic that decides it: is the gross correlated with the held names' Corwin–Schultz
half-spread?** If it is, this is another liquidity premium wearing a costume and it dies
exactly as the fade did. That test belongs in the pre-registration, not in the post-mortem —
`future-strategies.md` §1 makes the same demand of the ATM idea and it is the right demand
here.

**Stage 0.** Two numbers, both cheap. (i) **Do the clusters exist?** Silhouette or explained
variance of the `k`-cluster partition against a random partition of the same sizes — if the
panel does not cluster, there is no residual to take. (ii) **Is the residual actually
orthogonal?** `|corr(resid_5, r_5)|` — if it is 0.9, this is `rev_5` with extra steps and
D285 already answered it.

**The honest risk.** Cluster membership is estimated and unstable, and an unstable partition
puts a name in one group this month and another the next, which manufactures turnover the
signal never asked for. **Measure the partition's own persistence at Stage 0** — the same
demand Q1 makes of R1.

### 5.2 X2 — lead–lag between size cohorts

**Score: NEW 3 · DATA 3 · COST 0 · BREADTH 3 · KILL 3 · BASE 1 · CEIL 2 = 15/21**

**The quantity.** Does the large-cap cohort's return at `t` order the small-cap cohort's
return at `t+1`, within a cluster? Zero coverage (§1).

**Why it is ranked low despite scoring well on four axes, and this is the whole entry.**
**COST is 0.** The documented lead–lag effect lives in the *slowest-adjusting*, least liquid
names — which is, to the basis point, the population the cost wall has already killed here
three separate times: D284's $1.92 tenth percentile, D338's $0.18 top trade, and FINDINGS
§22's finding that the illiquid tail was **every book's top trade and none of their edge**.
**The effect and the cost wall live in the same names.** That is not a reason it is false; it
is a reason it is unlikely to be tradeable here, and it should be said before anyone spends a
week on it rather than after.

**It is listed because the audit found it empty and the record should say so**, not because I
recommend it. **If it is run, the honest form is the one that prices the cost first** — take
the dollar-volume decile the effect is claimed to live in, price its round trip, and ask what
per-bar edge would be needed. That is a ten-minute calculation and it probably ends the idea.

---

## 6. Group N — non-price data, GATED on the principal's deferral

**The principal deferred starting on auxiliary data sources on 2026-09-07**, and that
deferral is why `future-strategies.md` exists as a note instead of a pre-registration. **Both
entries below are subject to it and neither should be built without the principal lifting it.**

### 6.1 N1 — short interest and days-to-cover

**Score: NEW 3 · DATA 1 · COST 2 · BREADTH 3 · KILL 3 · BASE 2 · CEIL 3 = 17/21**

**Why this is the strongest non-price candidate, and the argument is the record's own.**
The programme's short side has failed in every universe it has been measured in, and
**FINDINGS §39 names the reason: on the floored universe the short side has no drifting pool
— the loser decile RISES, and every short since D335 has been timing inside a pool that
rises.** FINDINGS §30 puts it identically: *every short signal beats its own names at random
times and still loses; the names it shorts rise.*

> **Days-to-cover is the direct measure of the mechanism that makes a shorted pool rise.**
> This is not a new punt. It is the one observable that would explain a failure the record
> has now documented four separate times, and it is absent from every study that documented
> it.

**Data.** FINRA publishes consolidated short interest **free, twice monthly**, and the
exchanges publish their own files. **DATA scores 1 not because it costs money but because it
is a new provider under an active deferral** — the constraint is the principal's ruling, not
the fee.

**Stage 0, and it is a count before it is a return.** (i) **Coverage on the dead names** —
this fixture is 43.5% dead (562 delisted + 122 collapsed of 1,573, `[MEASURED HERE]`), and a
short-interest source that only serves live tickers reintroduces exactly the survivorship the
fixture was built to remove. **Count the join rate on the delisted cohort before anything
else.** (ii) The bi-monthly settlement clock against a daily book — a variable that updates
twice a month cannot key a daily entry, and the honest form is a slow filter, not a trigger.
(iii) Only then: does high days-to-cover partition forward returns on the floored universe?

**The honest risk.** Short interest is the single most crowded non-price variable in
quantitative equities, it is bi-monthly with a settlement lag that must be lagged correctly or
it is look-ahead (R9's fourth appearance waiting to happen), and the high-DTC population skews
small and cheap — back into the cost wall. **COST scores 2 rather than 3 only because the
variable's most defensible use is exclusionary — a filter that removes the squeeze-prone names
from a short book — and a filter that removes expensive names improves cost by construction.**

### 6.2 V1 — the closed-end fund discount

**Score: NEW 3 · DATA 1 · COST 2 · BREADTH 2 · KILL 3 · BASE 2 · CEIL 3 = 16/21**

**The observation that prompted it — `[MEASURED HERE]`.** The first forty symbols of
`etf_wide_daily_raw` are `AAXJ ACWI ACWX ADX AFT AGD AGZ AIF AIVL AMLP AOD ARDC ASA ASHR AVK
AWF AWP …`. **`ADX`, `AFT`, `AGD`, `AIF`, `ARDC`, `AVK`, `AWF`, `AWP` are closed-end funds,
not ETFs.** The fixture appears to contain a substantial CEF sub-universe that nothing has
ever looked at, and its metadata does not distinguish them — the `purpose` field reads *"US
single-name equity base for SHORT-SIDE research"*, which is a copy-paste artefact from the
equity fixture and is itself worth correcting.

**Why the mechanism is genuinely different from everything in this record.** A closed-end
fund has a **fixed share count and no creation/redemption**, so the arbitrage that pins an
ETF to its NAV is **structurally absent**. The discount to NAV therefore wanders and
mean-reverts on a multi-month clock. **That is route (b) of `future-strategies.md` §0 —
"the move is large and slow relative to the spread" — reached by a different road**, and it
is the only lead in this record whose payoff is *not* liquidity compensation and *not* a
tape pattern.

**Stage 0, and it is a census, not a return.** **How many of the 551 are closed-end funds?**
If it is twenty, the study is not worth writing. That count is the entire gate and it comes
before any design — the same shape as `future-strategies.md` §3's *"if it is under about a
hundred, the study is not worth writing"*.

**The blocker, stated plainly.** **NAV is not in the fixture and is not on Alpha Vantage.**
Without NAV there is no discount, and a price-only version of this idea is just reversal on a
thinly-traded subset — which is D285's failure in a smaller universe. **So V1 is a real
mechanism behind a real data blocker**, and it is listed at its honest position rather than
promoted because the story is good.

---

## 7. Group C — combination

### 7.1 C1 — a low-dimensional combination of independent, individually useless inputs

**Score: NEW 2 · DATA 3 · COST 1 · BREADTH 3 · KILL 1 · BASE 1 · CEIL 2 = 13/21**

**The question, and it is a real one.** [D280](../decisions/D280-the-forecast-precheck.md)
measured that **16 OHLC derivative terms carry 13.50–15.76 EFFECTIVE inputs** — genuinely
independent — *and carry no predictive power as levels*. D280's own gloss is that this is the
mirror of D268's lesson: *"sixteen independent useless inputs are sixteen independent sources
of noise, with no redundancy left to average away."* **The untested question is whether that
gloss is right** — whether a low-dimensional combination of them carries what none carries
alone.

**Why it is ranked last, and KILL scores 1.** **There is no cheap number that kills it.**
Every other lead in this record has one; this one has a *search space*, and R13's corollary
forbids summing into a floor nothing could clear. A combination study is the 6,348-compound
hazard with a continuous parameter attached. **It could only be run as a single
pre-specified form with the count disclosed — one combination, chosen by mechanism, never
swept** — and I cannot presently name the mechanism that chooses it. **A lead that cannot
name its own form is not ready**, and that is why it is here at 13 rather than absent: the
audit found the gap, and the gap is real, but the design is not available.

---

## 8. The scored list

| # | lead | NEW | DATA | COST | BRD | KILL | BASE | CEIL | **total** |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **R1** | cross-asset regime state as the gate | 3 | 3 | 3 | 1 | 3 | 3 | 2 | **18** |
| **X1** | cluster-residual reversal | 2 | 3 | 1 | 3 | 3 | 2 | 3 | **17** |
| **K1** | the calendar screen (3 declared) | 3 | 3 | 3 | 1 | 3 | 3 | 1 | **17** |
| **N1** | short interest / days-to-cover | 3 | 1 | 2 | 3 | 3 | 2 | 3 | **17** |
| **V1** | the closed-end fund discount | 3 | 1 | 2 | 2 | 3 | 2 | 3 | **16** |
| **X2** | lead–lag between size cohorts | 3 | 3 | 0 | 3 | 3 | 1 | 2 | **15** |
| **C1** | combination of independent inputs | 2 | 3 | 1 | 3 | 1 | 1 | 2 | **13** |

**The total is a summary, not a ranking, and the order of work below differs from it.** Three
leads sit within one point of each other and the arithmetic does not separate them; what
separates them is the deferral and the cost of being wrong.

### Order of work, and why this order

1. **R1 first.** It needs no fetch, it is bar-aligned already, its null is exactly
   enumerable, and **it aims at the programme's largest documented open negative** — D389's
   98.5%-unexplained factor, whose four tested candidates were all internal. It is the only
   lead here that answers an existing question rather than opening a new one.
2. **K1 second, in the same session.** Same runner shape as R1 (a market-level time gate,
   the same enumerated rotation null), and it is the cheapest measurement in this record.
   Low ceiling, near-zero cost, and it closes a category permanently either way.
3. **X1 third**, and only after its Stage 0 shows the clusters exist and the residual is
   orthogonal. Highest ceiling of the free leads and the highest chance of dying on cost.
4. **N1 and V1 wait on the principal**, on the auxiliary-data deferral. N1 is the one I would
   argue for if the deferral is lifted, on the §39 argument.
5. **X2 and C1 are recorded, not recommended**, for the reasons in their entries.

---

## 9. What is deliberately NOT proposed, and why

| | |
|---|---|
| the three `future-strategies.md` ideas | **Already reasoned and written.** ATM shelf issuance, XBRL runway, merger-arb acquirer. All three still owe **step 2 — the premise number** — and none has been measured. Re-listing them here would double-count the same thinking. |
| a price-level / support-resistance map | **Six looks, five written closes.** TERRAIN (D189–D203, 259 looks), STRUCTURE (D173, D204–D211, 86 looks), D272/D273, the BREAKOUT family, the DENSITY line (retired 2026-09-09), and D403's wick-stack. **TERRAIN's close is a mechanism, not an absence: the map's local structure is reliably WRONG about direction.** |
| anything reading order flow from price action | **Shut in both channels on measurement, 2026-09-09.** Signed: best OHLCV recovery corr +0.374 / +0.362. Magnitude: +0.163 / +0.143. Impact-per-volume (Kyle's lambda) +0.098 / −0.022, two of four **negative**. |
| dispersion as a state | **Withdrawn by C1b** — "dispersion is not direction, but it very much is volatility", and volatility alone was decisive. |
| COT positioning | **Closed, D263** — 0 of 8 cells, at the best-powered breadth the prop track has had (3.76 effective instruments, MDE 0.21). |
| the winners' dip · the 15m structure screen | **Closed by the principal, D401.** |
| the sign-sequence family | **Retired by the principal, D396.** |
| more single-score cross-sectional crossings | **Exhausted** — D350 screened 138 long events, D352 screened 139 short. |
| D383's 111 uncorrected-p95 survivors | **Recorded and unclaimed.** D401 states that closing the avenue does not license mining them without a fresh pre-registration. Not mined here. |

---

## 10. What this record does not claim

- **No number here is new except the six tagged `[MEASURED HERE]`**, which are fixture
  census facts from a read-only probe: the two fixtures' spans and row counts, the 551/417
  symbol counts, the presence and absence lists, and the delisted/collapsed counts.
- **Nothing has been backtested. No null has been run. No hurdle has been computed.** The
  scores in §8 are my judgement against §2's frame and are labelled as such.
- **No lead here is a candidate.** Under R8 each would need a pre-registration committed
  before its runner exists, and under R15 a signal is a **positive gross mean per trade above
  its nulls** before cost is discussed at all.
- **This record closes nothing.** §9 lists what is already closed and by whom; it does not
  add to that list. Only the principal closes an avenue.
- **The negative-space method has a known blind spot and it is stated rather than hidden:**
  a category can be absent from the record because it was *considered and rejected in
  conversation* rather than because it was never thought of. §1's grep finds the second and
  cannot find the first. **Where the principal has already dismissed one of these, it should
  be struck from the list and the reason recorded**, so the next scan does not resurface it.
