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

> **PRE-REGISTERED 2026-09-09 as [D404](../decisions/D404-the-cross-asset-state.md).** The runner
> does not exist and nothing has been run. **Three things the pre-registration established that
> this entry did not know:** the two fixture grids are **identical bar for bar** (4,187 dates, zero
> on either side only), so the join needs no new convention; the whole of the new code is the `raw`
> array, because `state_pack` / `block_corr` / `forward20` are reused unchanged; and **the decisive
> bar is measured, not guessed — |r| ≈ 0.15–0.16, which two of the four existing states do not
> clear.** D404 also carries the Q4 that this entry only gestured at: `data/d376_series.npz`
> already holds the 500-book matrix on the same grid, so testing the state against D389's
> unexplained factor costs almost nothing.

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

**ELEVEN LEADS.** The seven this record scanned, plus the four §9b's briefs surfaced. **The
`prior` column was added 2026-09-09 and is the only column that reflects external evidence** —
the seven axis scores are the record's own judgement as first written and are **deliberately
left unrevised**, so the scan's calibration can be audited against what the literature said
rather than quietly conformed to it.

| # | lead | NEW | DATA | COST | BRD | KILL | BASE | CEIL | **total** | prior after §9a/§9b |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **R1** | cross-asset regime state as the gate | 3 | 3 | 3 | 1 | 3 | 3 | 2 | **18** | **standing**, horizon in doubt → D404 |
| **X1** | cluster-residual reversal | 2 | 3 | 1 | 3 | 3 | 2 | 3 | **17** | **fell** — net −0.80%/mo; superseded by **X3** |
| **K1** | the calendar screen (3 declared) | 3 | 3 | 3 | 1 | 3 | 3 | 1 | **17** | **fell** — EW shrinks it; superseded by **R2** |
| **N1** | short interest / days-to-cover | 3 | 1 | 2 | 3 | 3 | 2 | 3 | **17** | **fell** — borrow fee; superseded by **N2** |
| **X3** | **industry-relative reversal, LIQUID names + low-vol screen** ⭐ | 2 | 2 | 2 | 3 | 3 | 2 | 3 | **17** | **standing — strongest of the eleven** |
| **R2** | **the even-week FOMC cycle** | 3 | 2 | 3 | 1 | 3 | 3 | 2 | **17** | **standing** |
| **N2** | **FINRA daily short-sale volume + SEC FTD crosswalk** | 3 | 2 | 2 | 3 | 3 | 2 | 2 | **17** | **standing — an INPUT, not a signal** |
| **V1** | the closed-end fund discount | 3 | 1 | 2 | 2 | 3 | 2 | 3 | **16** | **fell** — Flynn: zero significant alphas |
| **X2** | lead–lag between size cohorts | 3 | 3 | 0 | 3 | 3 | 1 | 2 | **15** | **dead** — $47m median cap |
| **X4** | **geographic lead–lag** | 3 | 1 | 1 | 3 | 3 | 2 | 2 | **15** | **standing**, weak prior — no cost test, sample ends 2013 |
| **C1** | combination of independent inputs | 2 | 3 | 1 | 3 | 1 | 1 | 2 | **13** | **ROSE to first of the unregistered** — §9a finding 2 |

**The score column did not predict the outcome, and that is worth recording against this
record's own method.** C1 scored **lowest of the seven and now ranks first**; K1 and N1 scored
17 and both fell hard. **The axis that failed was `KILL`** — C1 scored 1 there because I could
not name a cheap number that killed it, when the real situation was that I could not name its
*form*; a hurdle existed in the literature all along. **`KILL` was measuring my knowledge, not
the lead.**

**The total is a summary, not a ranking, and the order of work below differs from it.** Three
leads sit within one point of each other and the arithmetic does not separate them; what
separates them is the deferral and the cost of being wrong.

### Order of work — REVISED 2026-09-09 after the briefs

**The list below the rule is the ORIGINAL order, left standing so the revision is auditable.**

**Revised order: X3, then C1, then R1** — with R2 and N2 behind them, and X4 recorded but not
recommended.

1. **X3** — industry-relative reversal in liquid names. Two independent convergences, and its
   Stage 0 is a **count** (how many names survive a liquid-large restriction on a $5-floored
   equal-weighted fixture) that costs minutes and can end it.
2. **C1** — the 16-term OHLC composite, now that §9a finding 2 has removed the argument against
   it and §59 supplies the floor it needs. **One pre-specified form, signs declared in writing,
   no sweep.**
3. **R1 / D404** — pre-registered and amended; the horizon curve must be reported.
4. **R2** and **N2** — both cheap, both behind the above.
5. **X4** recorded, not recommended. **X1, K1, N1, V1 superseded or fallen. X2 dead.**

### Order of work as ORIGINALLY written, kept for audit

1. ~~**R1 first.**~~ — **PRE-REGISTERED as [D404](../decisions/D404-the-cross-asset-state.md),
   2026-09-09. The runner does not exist and nothing has been run.** It needs no fetch, it is
   bar-aligned already, and **it aims at the programme's largest documented open negative** —
   D389's 98.5%-unexplained factor, whose four tested candidates were all internal. It is the only
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

## 9a. EXTERNAL EVIDENCE, 2026-09-09 — all seven briefs are in, and the ranking inverts

Seven agents researched the published literature and primary data documentation, one per lead,
in parallel. Briefs in `working/leads/`, under that directory's quarantine contract. **Every
claim below that concerns THIS programme's own data or methods was re-measured here before
being recorded; every claim about the outside world is attributed and marked as unread.**

### The three findings that are not about any lead, and are worth more than the leads

**1. A BEST-OF-N FLOOR PRICES SELECTION AND IS BLIND TO SIGN-FITTING.** `[MEASURED HERE]` —
`scripts/probe_signfit_floor.py` → `data/signfit_floor_probe.json`, closed form and a
200,000-draw simulation that agree. Signing `k` worthless signals in sample gives the composite
a null centred at `√(2/π)·√k` with sd `√(1−2/π)`, free of `k`. At `k` = 16:

```
best-of-16 |t|  -- what the D395 floor prices : p95 = 2.95
sign-fitted equal-weight composite, pure noise: p95 = 4.23
signs PRE-DECLARED in writing                 : p95 = 1.65
```

**A composite of sixteen pure-noise signals clears the selection floor by +1.28.** `CLAUDE.md`
says the exact permutation floor should replace normal-approximation floors programme-wide;
this scopes that — **it is correct for what it prices and must be EXTENDED wherever a
construction orients its own components in sample.** And pre-declaring the signs is worth a
factor of ~2 in the hurdle for no computation at all.

**2. THIS RECORD'S OWN GLOSS ON D280 WAS WRONG, AND IT INVERTS C1's RANK.** The programme's
written position was that sixteen independent useless inputs are sixteen independent sources of
noise "with no redundancy left to average away". **Orthogonality multiplies detectability by
`√k`** — 3.7–4.0× for the OHLC family at 13.5–15.8 effective inputs, against 1.69× for the nine
price scores at 2.87. **By the programme's own numbers the family it dismissed is the better
combination candidate.** C1 scored 13/21 partly on "it cannot name its own form"; it now can —
16 OHLC terms, equal-weight cross-sectional rank average, every sign declared in writing,
floored against a sign-fitting null.

**3. `etf_wide_daily_raw` IS NOT AN ETF FIXTURE, AND ITS MORTALITY COHORT IS FUND WIND-UPS.**
`[MEASURED HERE]` — `scripts/probe_etf_fixture_composition.py` →
`data/etf_fixture_composition.json`. Found by the V1 agent in passing, on a fixture **D382,
D384 and D385 have already run on**:

| | |
|---|---|
| CEF distribution signature (≥10 payments/yr **and** ≥5% yield) | **150 of 551 = 27.2%** — a deliberately strict proxy, so a **lower bound**; the brief's independent count was 172 = 31.2% |
| the mortality cohort | **23 of its 24 dead names are closed-end funds by inspection.** The single exception is `ELON`, which paid nothing |
| distributions absent from `close` | whole fixture median **3.06%/yr**; CEF cohort median **10.54%/yr** |
| terminal-wealth understatement over 16 years | **5.37×** on the CEF cohort — the brief said 3.71×, so **worse than reported** |

> **A "dead-inclusive" fixture whose deaths are CEF term maturities and mergers is not measuring
> delisting risk at all.** Its `purpose` field also reads *"US single-name equity base for
> SHORT-SIDE research"*, a copy-paste artefact this record flagged in §6.2 before knowing the
> fixture was mis-composed as well as mis-labelled.

**What is and is not at stake.** All three studies pass the events file to `load_ragged`, so
their **P&L used total return and is not affected**. What is affected is anything reading
`closes` as a price LEVEL — which is exactly the log-price axis D384 and D385 built their
density on, bled by ~10.5%/yr across a quarter of the universe. **That line is retired, so the
live stake is the fixture itself and any future study that opens it.**

### The leads, re-ranked

| lead | external verdict | disposition |
|---|---|---|
| **C1** | the gloss was backwards; a concrete hurdle exists (**4.20** sign-fitted, **1.96** pre-declared) and reproduces HLZ 3.0 / HXZ 2.78 / CGS 3.4 | **RISES to first of the unregistered leads.** One disciplined test, not a search |
| **R1** | horizon claim recorded, not adopted; two construction defects measured, one **false**, one confirmed, one new | **pre-registered as D404, amended §12a** |
| **X1** | residualising lifts gross 1.5–3.5× and net goes **−1.28 → −0.80%/mo** — still 80bp under water. Mechanism is *not* ours: raw reversal accidentally shorts industry momentum and PEAD. Clustering's own negative: out-of-sample within-minus-outside correlation spread **0.13 large-cap vs 0.02 small-cap**, and ours is the small-cap case | **falls.** The cluster step is the weakest part |
| **N1** | borrow fee close to fatal (**+0.14%/mo gross → −0.01% net** across 162 anomalies); free exchange-listed FINRA short interest **starts June 2021** (~31% of the fixture) and members **omit a security once its symbol is deleted** | **falls hard.** Better free route flagged: FINRA daily short-sale volume + SEC FTD file, which carries **CUSIP** and doubles as a symbol crosswalk |
| **K1** | location kills it before decay does — on FOMC days the CAPM *works*, α insignificant, adj-R² 64%. **Equal weighting, the thing that made K1 attractive, is what shrinks it**: 36bp VW → 25bp EW → 20bp smallest decile | **falls hard.** Keep only as a gross descriptive measurement |
| **V1** | Flynn (462 CEFs, 1985–2001) runs this exact hedged trade and finds **zero significantly positive alphas**, already net of spreads; the edge is **front-loaded into month one**, killing the "slow and large" thesis | **falls.** But its by-product is finding 3 above |
| **X2** | **the dismissal stands.** The daily large→small effect is measured into a decile averaging **$47m** cap and is strongest when large-cap spreads are widest | **confirmed dead** |

### The convergence worth noticing

**Two agents that never communicated arrived at the same construction** as the only cost-surviving
thing in the area: **industry-relative reversal in liquid names with a low-volatility screen**
(+0.31%/mo, t = 2.73, value-weighted, large-cap). X2 reached it from the lead–lag literature,
X1 from the reversal literature. **And in both accounts it is the COST FILTER doing the
rescuing, not the residualisation** — which is the same lesson this programme has now paid for
several times over. It is not a lead in this record and it would need its own pre-registration.

## 9b. FOUR LEADS THE BRIEFS SURFACED THAT THIS RECORD DID NOT CONTAIN

**These were not in the original seven.** Each came back from an agent sent to check something
else, and **two of them are better founded than the lead they were found while checking.** They
are written up here to the same anatomy as §§3–7 so they are leads on the record rather than
sentences in a brief, and they are slotted into this record's own groups rather than given a new
taxonomy.

**All four carry the same caveat and it is not a formality:** every magnitude below is quoted
from a paper measured on **someone else's universe, era and cost assumption**, and none of those
papers has been read here. **A quoted effect size is a prior, not a prediction.**

### 9b.1 R2 — the even-week FOMC cycle

**Score: NEW 3 · DATA 2 · COST 3 · BREADTH 1 · KILL 3 · BASE 3 · CEIL 2 = 17/21**

**Where it came from.** The K1 brief, sent to check the **pre-FOMC announcement drift**, reported
that Cieslak–Morse–Vissing-Jorgensen (JF 2019) is **better founded than the object it was sent to
check** — *"far more events, causal evidence, no published OOS failure I could find."*

**The quantity.** Equity returns are claimed to accrue in **even weeks** of the FOMC cycle
(week 0, 2, 4, 6 from a meeting) and not in odd weeks. **It is a phase counter on a known
calendar, not a window around an announcement.**

**Why it is not in the catalogue.** §1: no score reads `panel.dates`. And it is untouched by
K1's failure — **K1c measured a 24-hour window and this is a fortnightly phase**, so the
location argument that killed K1 (α insignificant on announcement days, beta on a schedule) does
not transfer without being re-measured.

**Why it survives K1's own killer.** K1 died partly because **equal weighting shrinks the
pre-FOMC effect** (36 bp VW → 25 EW → 20 smallest decile). **Nothing in the brief says the same
of the even-week cycle**, and that is the first thing to check rather than assume.

**BASE scores 3 and COST 3 for K1's reasons, unchanged:** a phase counter **selects no names**,
so it cannot inherit D392's 36.8 bp price-tercile base rate, and it changes only *when*.

**Data.** The same FOMC date list K1 needs: `federalreserve.gov/monetarypolicy/fomccalendars.htm`
plus the per-year historical pages. **HTML only, no official CSV/JSON/iCal — it must be
scraped**, and unscheduled meetings are labelled inline (`"March 15 (unscheduled) Meeting -
2020"`, alongside `(cancelled)` and `(notation vote)`). **A phase counter that miscounts an
unscheduled meeting has the wrong phase for every subsequent week**, so the parse is
load-bearing in a way K1c's window was not.

**The premise number that kills it.** Mean forward drift of the equal-weighted floored universe
in even versus odd cycle weeks, **split 2010–2015 / 2016–2026**, with the exactly-enumerated
market-level rotation null. **And the EW-versus-VW comparison beside it**, because that is what
killed K1.

**The honest risk.** One market-level series, so BREADTH is 1 as it is for every gate here. The
paper's sample ends well before ours. And **this record has now been handed a "better founded
cousin" by an agent whose primary lead failed** — that is exactly the shape of a consolation
prize, and it should be treated with the suspicion `working/leads/README.md` requires.

### 9b.2 X3 — industry-relative reversal in LIQUID names, with a low-volatility screen ⭐ the strongest of the eleven

**Score: NEW 2 · DATA 2 · COST 2 · BREADTH 3 · KILL 3 · BASE 2 · CEIL 3 = 17/21**

**Where it came from, and why that matters.** **Two agents that never communicated converged on
it** — X1 from the reversal literature, X2 from the lead–lag literature — each naming it as the
only cost-surviving construction in its area. **Independent convergence is the strongest
positive signal this exercise produced**, and it is the reason this entry exists.

**The quantity.** Industry-relative short-term reversal, restricted to **liquid, large names**,
with a **low-volatility screen**, value-weighted. Reported at **+0.31%/mo, t = 2.73**,
net of costs, in Novy-Marx–Velikov's cost framework.

**Why NEW scores 2, stated first because it is the weakest part.** [D285](../decisions/D285-the-factor-neutral-book.md)
ran plain cross-sectional reversal on this fixture to **zero survivors across 18 cells**, and
§5.1's X1 already proposed residualising it. **What is genuinely new is neither the reversal nor
the residualisation — it is the LIQUIDITY AND VOLATILITY RESTRICTION**, and the record must say
that plainly rather than present a screened variant as a fresh idea.

> **THE FINDING INSIDE THE FINDING, AND IT IS THE WHOLE ENTRY: IN BOTH INDEPENDENT ACCOUNTS THE
> COST FILTER DOES THE RESCUING, NOT THE RESIDUALISATION.** X1's own table has industry-relative
> reversal at **−0.80%/mo net** against raw reversal's −1.28 — residualising added +0.61 gross
> and +0.13 cost and left it 80 bp under water. **What turned −0.80 into +0.31 was screening out
> the expensive names.** That is this programme's own repeated lesson arriving from outside.

**And it is therefore a test of a hypothesis this record already holds**, not a new punt: the
cost wall is a *price* effect, and a construction that removes the cheap, wide, volatile names
before ranking should survive where one that ranks them cannot.

**The premise number that kills it, and it is a COUNT before it is a return.** The published
result is **value-weighted large-cap**; this fixture is **equal-weighted and floored at $5**.
**How many names in this universe would survive a liquid-large restriction, and what is the
breadth of what remains?** If the answer is forty names, this is D264's concentration problem
again and the study is not worth writing. **That count comes first, before any design.**

**Data.** An industry map. GICS is paid. Free routes: **SEC N-PORT ETF holdings** (monthly,
Oct 2019 → Jun 2026 — *too short*), or the panel's own correlation clustering. **X1's brief
supplies the decisive number for the clustering route: out-of-sample within-minus-outside
correlation spread is 0.13 in large caps against 0.02 in small.** Since this lead is restricted
to large caps, **clustering is viable here where it was not for X1** — which is a real
difference between the two entries and the reason X3 is not simply X1 rescored.

**The honest risk.** It is a high-turnover reversal payoff, so it lives closest to the cost wall
of anything standing. And it is **somebody else's published result** — the appropriate prior is
post-publication decay, which McLean–Pontiff puts at 58%, concentrated in low-liquidity names.

### 9b.3 X4 — geographic lead–lag

**Score: NEW 3 · DATA 1 · COST 1 · BREADTH 3 · KILL 3 · BASE 2 · CEIL 2 = 15/21**

**Where it came from.** The X2 brief, sent to **confirm or refute this record's dismissal of
lead–lag**. It confirmed the dismissal — and then named the one variant that escapes the reason
for it.

**The quantity.** Firms headquartered in the same city but operating in **different sectors**
lead one another, at a reported **5–6%/yr**.

**Why it escapes what killed X2.** X2 died because the effect lives in $47m-cap names, inside
the cost wall. **The geographic effect is explicitly reported as unrelated to size, trading
volume and analyst coverage** — the mechanism offered is that analysts specialise by *sector*,
so information crossing sector lines within a city is slow regardless of how large the firms
are. **That is a different mechanism, not a different parameter**, which is the only thing that
reopens a dismissed axis under R13.

**Data.** Headquarters location per name, **including delisted names**. SEC EDGAR carries a
business address on filings and is free, but assembling a point-in-time HQ for 1,573 names of
which 43.5% are dead is real work — **and HQ moves**, so a current address applied historically
is a look-ahead. **This sits behind the principal's auxiliary-data deferral.**

**The premise number that kills it.** A **count**: how many cities carry enough names, in
enough different sectors, to form a pair at all on this universe? If the answer is three cities,
the study is not worth writing.

**The honest risk, and DATA and COST both score 1 for it.** The result is **monthly**, its
sample **ends 2013**, and **the paper carries no cost test**. A 5–6%/yr gross effect with no
cost treatment, in an era we cannot observe, is a weak prior — this is a lead worth recording
and not one worth taking first.

### 9b.4 N2 — FINRA daily short-sale volume, with the SEC FTD file as the crosswalk

**Score: NEW 3 · DATA 2 · COST 2 · BREADTH 3 · KILL 3 · BASE 2 · CEIL 2 = 17/21**

**Where it came from.** The N1 brief, after establishing that **short interest itself is not
reachable on this fixture** — free exchange-listed FINRA short interest starts **June 2021**
(~31% of the fixture) and members **omit a security once its symbol is deleted**, so the
terminal observation of every dying name is missing by rule.

**The quantity.** **Daily** short-sale volume as a share of total volume — a flow, not a stock.
FINRA publishes it consolidated from **2018-08** and per-venue back to **2009**, at a **one-day
lag**, point-in-time.

**Why this is the better route, and it is a coverage argument rather than a signal argument.**
Short interest is a **twice-monthly stock with a seven-business-day publication lag** — it cannot
key a daily entry and it is missing exactly where this fixture is dense. Daily short-sale volume
is **point-in-time, daily, and published the next day.** **N1's three killers were coverage,
lag and delisted-name loss; this addresses all three.**

**And the crosswalk is the part worth recording separately.** The **SEC failures-to-deliver
file runs from 2004 and carries CUSIP**, where the FINRA files carry **symbol only**. That makes
the FTD file usable as a **symbol-to-CUSIP crosswalk for delisted names** — which is the
programme's standing ticker-reuse hazard (*a delisted ticker can be reassigned to a different
company*) answered by a free primary source. **That is useful independently of whether any short
signal works.**

**CEIL is 2 and the entry says why: this is an INPUT, not a signal.** Nothing here proposes a
strategy. It proposes a variable the programme could hold, of a kind it has never had.

**The premise number that kills it.** The **join rate on the delisted cohort** — the exact test
N1 failed. Using the FTD crosswalk, what fraction of the fixture's 684 dead names can be matched
to short-sale volume records covering their final year? **If the dead cannot be joined, this
reintroduces the survivorship bias the fixture exists to remove**, and it dies where N1 died.

**The honest risk.** Short-sale volume is **not short interest** — a high short-volume share can
mean market-making inventory rather than directional conviction, and the literature on its
predictive content is thinner than on short interest. And it is a **new provider under the
deferral.**

---

### What the briefs could not establish, carried rather than smoothed over

Five of the seven hit paywalls or 403s on at least one load-bearing source — SSRN, ScienceDirect
and Oxford blocked repeatedly. **Named gaps:** exact per-variable OOS R² in Goyal–Welch (R1);
five calendar papers read at abstract level only, including a 2026 paper directly on
data-mining artefacts (K1); Blitz et al. 2013, the one paper claiming net-of-cost reversal
survival, unobtainable and Robeco-authored with a replication by two of its own authors (X1);
Hou's and Boudoukh's own tables (X2). **Every figure from those is tagged `[UNVERIFIED]` in the
briefs and none is relied on above.**

**And the standing suspicion held.** R1's brief was the one that read most confidently, and its
two headline construction claims were **the ones that did not survive measurement** — the
alleged 2–5%/yr drift was −0.92%/yr and ran the opposite way. `working/leads/README.md`'s rule
was written before that was known and it paid for itself immediately.

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
