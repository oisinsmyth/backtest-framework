# 20 — Verified track records: what the audited tier actually delivers

**Lane 20 of the Prop-Firm-080926 review.** Opened and closed 2026-09-08.
Schema and stopping rules: [`00-SCHEMA.md`](00-SCHEMA.md). Reads on and corrects
[`14-practitioner-tier-screened.md`](14-practitioner-tier-screened.md) and
[`07-statistics-and-claims.md`](07-statistics-and-claims.md). Filed toward **D386**.

**Stopping rule that bound: SATURATION, at 37 logged sources** (target was 30). Saturation was
declared when four consecutive database sources — BarclayHedge's SG index detail page, Société
Générale's own index page, autumngold, and RCM Alternatives' fund pages — returned only MTD/YTD or
nothing, having already been answered by IASG and NilssonHedge. The one avenue not saturated is
recorded as **blocked**, not exhausted: per-programme *daily* return series, which no free tier
publishes.

**NOTHING HERE IS EVIDENCE FOR OUR BOOKS.** No R15 test was run, no null was drawn, no fixture was
touched, no avenue is opened or closed, no look is added to any multiplicity ledger. What *is*
claimed: these are third-party-verified records of real money in the instrument class the prop
account trades, and they bound what that instrument class has been observed to deliver. That is a
statement about **the world**, not about any strategy of ours.

---

## VERDICT

### The one-line answer

**The prop account's requirement is a single scale-free number — annualised return ÷ maximum
drawdown ≥ 18.9 — and across 199 verified CTA programmes, 25 verified stock-index-futures
programmes, 14 named programmes from the five longest-surviving short-term futures managers on
earth, and 993 platform-tracked systems, the number of records that reach it with a track record
longer than one year is ZERO.**

The best verified *intraday CME futures* programme found, over any length of record, sits at
**1.07**. The best programme of any kind in a 199-programme audited database sits at **5.88**. The
observed distribution's median is **0.267**.

### Q1 — does lane 14's 19×–60× gap hold on a wider sample?

**YES at the programme level, and it is conservative there — the honest band is 21× to 155×. It
FAILS at the index level, where the gap narrows to 7.5×. Lane 14 did not distinguish the two, and
the distinction is the whole substance of the answer.**

Lane 14's construction is `daily P&L ÷ drawdown budget`. That is `Calmar ÷ 252`, so the comparison is
a Calmar comparison and nothing else. The prop account demands **$150 × 252 = $37,800/yr against a
$2,000 buffer = Calmar 18.9**, i.e. `0.075/day`.

| population | n | object | median Calmar | daily ratio | gap vs 0.075 |
|---|---|---|---|---|---|
| **IASG CTA Index constituents** | **199** | single programme | **0.267** | 0.00106 | **71×** |
| — its p90 | | single programme | 0.899 | 0.00357 | 21× |
| — its p25 | | single programme | 0.122 | 0.00048 | 155× |
| — its **maximum** | | single programme | **5.88** | 0.0233 | **3.2×** |
| **IASG Stock Index Traders** | **25** | single programme | 0.446 | 0.00177 | 42× |
| **Named short-term CTA panel** (Crabel, QIM, Niederhoffer, Revolution, NuWave) | **14** | single programme | 0.246 | 0.00098 | 77× |
| — its **maximum** (Crabel Multi-Product 1x, since 1998) | | single programme | **0.458** | 0.00182 | **41×** |
| SG Trend Index | 20+ | *diversified index* | 0.256 | 0.00102 | 74× |
| IASG CTA Index (the index itself) | 204 | *diversified index* | 0.411 | 0.00163 | 46× |
| **NilssonHedge CTA Short Term index** | ~42 | *diversified index* | **1.213** | 0.00481 | **15.6×** |
| **IASG Stock Index Trader Index** | 25 | *diversified index* | **2.515** | 0.00998 | **7.5×** |

**Which row is the right object?** A prop account is **one account**. It cannot hold 25 weakly
correlated managers. So the programme-level rows are the comparison and the index-level rows are a
lower bound on the gap that no single trader can reach. Stated properly:

> **A single verified futures programme delivers a median 0.00106 of drawdown budget per day and at
> the 90th percentile 0.00357. The prop account demands 0.075. The gap is 21×–155×, centred on 71×.**

**Three corrections to lane 14's inputs**, all computed and reproduced here:

1. **Lane 14's ~6.3%/yr for the NilssonHedge Systematic Short-Term index is wrong; the figure is
   3.50%/yr.** Lane 14 read "VAMI 125.34, Jan-2023 → Sep-2026". The VAMI series actually **begins at
   100 in Jan-2019** and stands at **129.77** on the 2026-09-06 update. Verified two independent
   ways: compounding NilssonHedge's own published monthly table (91 months, Jan-2019 → Jul-2026)
   gives a terminal VAMI of **129.78** and reproduces every one of their eight published annual YTD
   figures **exactly** (1.1 / 2.5 / 1.1 / 8.1 / 0.3 / 6.9 / 1.5 / 5.3). Over 7 yr 7 mo that is
   **3.50%/yr**; since Jan-2023 alone it is 3.86%/yr.
2. **Lane 14 divided an *index* return by a *programme* drawdown.** 6.3% (index) ÷ 20% (typical
   programme) is dimensionally mismatched. Correcting to index-over-index gives 3.50 ÷ 2.88 = **1.213**,
   and to programme-over-programme gives ~0.25. The two errors partly cancelled, which is why lane
   14's magnitude survived.
3. **Lane 14's "Calmar 1.0 is generous" is right, and understated.** Across 199 audited programmes,
   only **15 (7.5%)** exceed Calmar 1.0 and only **6 (3.0%)** exceed 2.0.

### Q2 — does ANY audited intraday CME programme reach return ÷ maxDD ≥ 18?

**NO. The falsifier is not met. The best true intraday CME futures programme found — across records
running to 198 months — is 1.07, a factor of 17.7 short.**

Every programme in the IASG Stock Index Trader index whose own description states it closes flat
daily:

| programme | manager | instruments / convention (their words) | months | ann. ret | max DD | **ratio** |
|---|---|---|---|---|---|---|
| **FRS** | Soaring Pelican | S&P 500 futures, *"all positions are closed before the end of each trading day"* | 54 | 2.58% | **2.42%** | **1.07** |
| **Intraday Advantage** | Soaring Pelican | ES only, *"in all cases positions are closed by the end of the day"* | **187** | 4.34% | 19.50% | 0.22 |
| **Blended Advantage** | Soaring Pelican | *"intraday and overnight movements in the S&P-500"* | 62 | 3.29% | 14.98% | 0.22 |
| **Tail Reaper** | QTS Capital | ES, *"fully automated, intraday… • No overnight positions"* | 167 | 2.74% | 55.19% | 0.05 |
| **R Best Private Client** | R Best | *"intraday trading positions"*, Treasury + equity index futures | 198 | 1.22% | 22.42% | 0.05 |

The **whole 199-programme database maximum is 5.88** (Hyperion Fund, Le Mans Trading — a
diversified multi-strategy futures *and options* fund, 71 months, not intraday). Nothing in the
database is within a factor of three of 18.9, and **the top of the distribution is made of short
records**:

| rank | programme | ratio | ann. ret | max DD | **months** |
|---|---|---|---|---|---|
| 1 | Hyperion Fund | 5.88 | 9.8% | 1.67% | 71 |
| 2 | Third Wave Systematic Strategy | 3.40 | 20.2% | 5.95% | 60 |
| 3 | ART Short Term Systematic SP – Velocity | 2.57 | 36.6% | 14.24% | 38 |
| 4 | STTS-6FF – Short Term Trading Strategies | 2.17 | 6.3% | 2.92% | 41 |
| 5 | RQSI: ADOY | 2.08 | 3.8% | 1.84% | 55 |
| 6 | Athena Quantitative Program | 2.06 | 17.2% | 8.32% | 67 |
| 7 | Vulcan Metals Ultra Strategy | 1.94 | 34.4% | 17.76% | 46 |
| 8 | **HPX Old School Program** | **1.52** | 26.3% | 17.27% | **243** |

Every one of the top seven runs on 38–71 months. The only 20-year record in the top eight sits at
**1.52** — a third independent instance of the decay documented below, this time *inside* the audited
database.

**The nearest miss anywhere, and why it does not carry the falsifier.** World Cup Advisor publishes
real-money proprietary accounts, net of all commissions and fees, with drawdown. Its featured
records:

| advisor / programme | initial | months | net return | drawdown | annualised | **ratio** |
|---|---|---|---|---|---|---|
| **Ivan Scherman — 2023 World Cup** | $241,360 | **10.85** | **+491.9%** | **−26.2%** | ~615% | **23.5** |
| Pau Perdices — Metals and Indices | $10,000 | 8.13 | +73.2% | −21.2% | ~125% | 5.89 |
| Jey Hsieh — TSE Quantitative I | $10,000 | 15.13 | +222.8% | −35.7% | ~153% | 4.30 |
| **Ivan Scherman — Emerge Funds** | $50,000 | **32.09** | +209.7% | −33.5% | ~53% | **1.57** |
| Daniele Sambataro — Momentum Selection | $10,162 | **42.68** | +233.8% | −37.4% | ~40% | **1.08** |

The 2023 World Cup account clears 18 on the arithmetic (18.8 on raw cumulative return, 23.5
annualised). **It does not satisfy the falsifier as written, and it would not carry it if it did:**

- **It is not intraday and not CME-only.** Scherman's own description of the winning approach is a
  multi-asset book across *"Currency Futures, Energies, Grains, Indices, Meats, Metals, Softs, and
  Treasury Futures"* — a diversified multi-market programme, not an intraday index book.
- **10.85 months.** Annualising a sub-year record is extrapolation, not measurement.
- **The drawdown is month-end only.** World Cup Advisor states it verbatim: *"Peak-to-valley
  drawdown is the greatest cumulative percentage decline in **month-end** net equity."* The prop
  floor reads the worst *tick* on open equity. The quantity the barrier prices was not measured.
- **The same manager, longer window, 1.57.** His 32-month WCA account is at 1.57 — a 15× collapse.
  His firm's own claim for its 17-year record is *"an average annual net performance of 23%"*, i.e.
  roughly the CTA population, not 615%.
- **Tournament selection.** Robbins' own disclosure: *"Accounts trading in the World Cup Trading
  Championships do not necessarily represent all the WCC accounts controlled by the competitor"* and
  *"the advisor may have previously displayed other accounts on WCA."* Multiple entries per
  competitor are not excluded and are not disclosed. This is a maximum-order statistic, not a draw.

### The finding this lane was built to produce, and it is new

**A return-to-drawdown ratio of 18 is not a property of a strategy. It is a property of a short
record. It decays monotonically to the audited CTA level as the record lengthens, and two entirely
independent platforms show the same decay.**

**Evidence A — Collective2's Grid, 100 most-popular of 993 systems**, bucketed by age. C2's own
header, verbatim: *"These are hypothetical performance results that have certain inherent
limitations."*

| strategy age | n | median Calmar | max Calmar | **count ≥ 18** | median maxDD | median ann. return |
|---|---|---|---|---|---|---|
| 0–180 days | 29 | 9.76 | 315.5 | **10** | 5.5% | 111.9% |
| 180–365 days | 10 | 6.85 | 31.3 | **2** | 12.2% | 54.8% |
| 365–730 days | 24 | 3.05 | 103.5 | **1** | 16.6% | 37.0% |
| 730–1,825 days | 24 | 1.40 | 5.44 | **0** | 33.1% | 29.6% |
| **≥ 1,825 days (5 yr+)** | **13** | **0.75** | **3.55** | **0** | **43.9%** | **22.3%** |

Every one of the 13 systems at Calmar ≥ 18 is **under 370 days old**, and all six futures-only ones
are between **41 and 370 days**. The oldest cohort's median Calmar (0.75) has converged on the
audited CTA population's (0.267–0.446). The grid also contains an annualised return of
**2,427,580.1%** on a **6-day-old** system and **42,112.3%** on a **38-day-old** one, which is what
the left end of this curve is made of.

**Evidence B — World Cup Advisor**, real money, no hypotheticals, ordered by record length:
8.1 mo → 5.89 · 10.9 mo → 23.5 · 15.1 mo → 4.30 · 32.1 mo → 1.57 · 42.7 mo → 1.08.

**Evidence C — inside the audited CTA database itself.** The top seven ratios among 199 verified
programmes come from records of **38 to 71 months**; the only 20-year record in the top eight (HPX
Old School, 243 months) sits at **1.52**. Median record length in the whole population is far longer
than the top of its own ratio distribution.

Three populations — hypothetical model accounts, real-money proprietary accounts, and audited CTA
programmes — showing the same monotone decay to ~1. **The prop account's 18.9 sits inside the region
that only short records occupy.**

---

## Q3 — what survives 5+ years, and what family is it?

### The survivorship arithmetic, from the databases' own counters

- **IASG: 270 active programmes against 1,707 archived.** Only **13.7%** of every programme the
  database has ever carried is still live. Every ratio quoted above is computed on index members,
  i.e. on live programmes — **the true population ratio is lower than every number in this file, and
  the bias direction is unambiguous.**
- **SG Short Term Traders Index, 2008–2026:** 48 distinct managers have held a place across 19 index
  years. **Median tenure is 3.5 index-years.** Only **three** appear in all 19 —
  **Crabel Capital Management, R.G. Niederhoffer Capital, Revolution Capital Management** — with
  Quest Partners/AlphaQuest a fourth until it was *"REMOVED MARCH 1, 2026"*. That is **6.3% holding a
  place for the full span.** (Caveat stated: from 2012 the index is capped at ten constituents, so
  leaving the index is not the same as dying; this figure bounds *persistence in the top tier*, not
  survival.)
- **Bhardwaj, Gorton & Rouwenhorst, RFS 2014**, on the whole CTA universe 1994–2012: net-of-fee
  excess returns to investors were **insignificantly different from zero** while gross excess returns
  were **6.1%** — managers captured the performance in fees; and the **combined backfill and
  survivorship bias is 7.7% annualised.** Applied to any database figure quoted here, this is the
  size of the correction that would have to be subtracted.

### The families that survive, named

Every long-survivor in the short-term futures tier is the **same family**: systematic, short-holding-
period, diversified across many futures markets, institutionally executed. Their published
economics:

| manager | programme | inception | CAROR | worst DD | **ratio** |
|---|---|---|---|---|---|
| **Crabel** | Multi-Product 1x | **1998-03** | 7.44% | −16.26% | **0.458** |
| Crabel | Multi-Product 1.5x | | 10.05% | −24.49% | 0.410 |
| Crabel | Gemini 1x | 2016-07 | 3.43% | −10.95% | 0.313 |
| Crabel | Gemini 1.5x | | 3.93% | −19.41% | 0.202 |
| Crabel | Advanced Trend 1x | 2014-04 | 8.46% | −28.47% | 0.297 |
| **QIM** | Quantitative Global | | 6.58% | −23.64% | 0.278 |
| QIM | Tactical Aggressive | 2008-05 | 14.03% | −57.11% | 0.246 |
| QIM | Cipher | | 3.37% | −13.89% | 0.243 |
| **R.G. Niederhoffer** | Macro Diversified | | 6.94% | −54.24% | 0.128 |
| R.G. Niederhoffer | Smart Alpha 2x | | −0.98% | −31.77% | negative |
| **Revolution** | Alpha Program | | 5.17% | −21.12% | 0.245 |
| Revolution | Mosaic Institutional | | −0.76% | −32.09% | negative |
| **NuWave** | Short-Term Futures Portfolio | | 0.81% | −12.97% | 0.062 |
| NuWave | Commodity Directional | | −0.86% | −25.99% | negative |

**Not one of the fourteen exceeds 0.46. Three are negative.** These are the survivors — $2.1B,
$1.3B, $842M, $729M programmes run by firms with 25–30 year histories, co-located execution and
institutional commission schedules.

**A leverage-invariance check falls out of this table for free, and it is the load-bearing one.**
Crabel publishes the same strategy at 1x and 1.5x. Multi-Product: 0.458 vs 0.410. If return ÷ maxDD
were improvable by sizing, the 1.5x version would show it; it does not — it is marginally *worse*,
which is what fixed costs and financing predict. **Levering up multiplies numerator and denominator
together.** The prop constraint therefore cannot be met by trading bigger or smaller, and cannot be
met by choosing micros over minis. It can only be met by a better edge. This is measured, in live
money, on the same book at two sizes.

---

## Q4 — the verified drawdown distributions

This is the quantity the academic literature never publishes and the prop account is priced on.

**Single programmes (IASG, month-end basis, live programmes only):**

| | n | maxDD p10 | **p50** | p90 | ann. ret p10 | **p50** | p90 |
|---|---|---|---|---|---|---|---|
| **IASG CTA Index constituents** | 199 | 9.85% | **21.12%** | 46.47% | 0.86% | **6.34%** | 12.46% |
| **Stock Index Traders** | 25 | 10.32% | **18.54%** | 48.52% | 2.65% | **8.31%** | 15.86% |
| Trend Following | 66 | 10.19% | 27.54% | 59.48% | −0.12% | 5.57% | 11.06% |
| Option Strategy | 10 | 7.66% | 15.71% | 28.57% | 9.67% | 10.70% | 16.77% |
| Agricultural | 19 | 10.21% | 20.50% | 43.94% | 1.67% | 5.47% | 12.44% |

> **Five of 199 verified programmes (2.5%) have a maximum drawdown at or inside the prop account's
> 4% budget.** They are FRS (2.42%), Hyperion Fund (1.67%), Quantitative Capture Strategy (3.20%),
> RQSI: ADOY (1.84%) and STTS-6FF (2.92%). Their annualised returns are **2.6%, 9.8%, 3.6%, 3.8% and
> 6.3%** — on a $50k account, **$3.50 to $13.40 per trading day**, against the $150 required.

**Diversified indices** — a completely different object, and the difference is the point:

| index | period | ann. ret | **max DD** | Calmar |
|---|---|---|---|---|
| NilssonHedge CTA Short Term | 2019-01 → 2026-07 (91 mo) | 3.50% | **2.88%** (peak Jan-2020, trough Mar-2020) | 1.213 |
| IASG Stock Index Trader | 219 mo | 12.57% | **5.00%** | 2.515 |
| IASG CTA Index | 502 mo | 17.98% | 43.72% | 0.411 |
| SG Trend Index | since inception | 5.27% | 20.61% | 0.256 |

**The measured diversification gain, in this exact tier, is 5.6× on Calmar** (0.446 median
constituent → 2.515 for the 25-manager equal-weight index) and **3.7× on drawdown** (18.54% →
5.00%). This is the only structurally available lever found anywhere in the lane, it is measured
rather than assumed, and **after applying it in full you are still 7.5× short of 18.9.**

**Time in drawdown, which the trailing floor actually reads.** Even the NilssonHedge short-term
index — 2.88% worst drawdown over 91 months — spent **59 of 91 months (65%) below its running peak**,
and 24 of 91 (26%) more than 1.5% below it. A floor that ratchets on peaks and never retreats is
priced against *time in drawdown*, not against the single worst episode, and the verified tier lives
below its high-water mark two-thirds of the time.

**Three biases, all in the same direction, all understating the gap:**

1. **Month-end measurement.** IASG's own definition, verbatim: *"maximum drawdown, the percentage
   loss a program experiences from its highest net asset value to its lowest"*, computed from the
   monthly return table. Intra-month and intraday excursions are invisible. The prop floor reads the
   worst tick on **open** equity. Every ratio above is therefore an **overstatement** of what the
   barrier would have seen.
2. **Survivorship.** 1,707 archived vs 270 active at IASG; +7.7%/yr of combined backfill and
   survivorship bias per Bhardwaj–Gorton–Rouwenhorst.
3. **Voluntary reporting.** NilssonHedge states it plainly: *"The purpose of the index is to track
   funds that are reporting data publically and may thus exclude certain managers."*

One bias runs the *other* way and must be stated: CTA returns are **net of 2/20-type fees** while the
prop $150/day is gross of any management fee. Grossing up a 6.3% median net return at a 2%
management fee and 20% incentive fee gives ~9.9% gross — which lifts the median programme Calmar
from 0.267 to ~0.47 and shrinks the median gap from 71× to **~40×**. **It does not come close to
closing it, and it does not touch the ≥18 falsifier at all** (Hyperion's 5.88 grosses up to ~9, still
half of 18.9).

---

## The cost finding — and it is the sharpest thing in this lane

IASG's programme records carry a self-reported field the marketing tier never quotes: **round turns
per year per $1,000,000 of trading level.** At the screen's **$10 round turn**, that converts
directly into an annual cost as a percentage of capital: `RT/$1M × 0.001 %`.

| programme | round turns /yr /$1M | **cost at $10/RT** | its actual CAROR | cost as % of the programme's entire return |
|---|---|---|---|---|
| **Intraday Advantage** (ES, flat at close) | 5,000 | **5.00%/yr** | 4.34% | **115%** |
| **R Best Private Client** (intraday) | 5,000 | **5.00%/yr** | 1.22% | **410%** |
| **Blended Advantage** | 5,250 | 5.25%/yr | 3.29% | 160% |
| **Tail Reaper** (ES, no overnight) | 2,195 | 2.20%/yr | 2.74% | 80% |
| **FRS** (ES, flat before close) | 1,000 | 1.00%/yr | 2.58% | 39% |
| **Crabel Multi-Product 1x** | 11,900 | **11.90%/yr** | 7.44% | **160%** |
| Crabel Gemini 1x | 2,900 | 2.90%/yr | 3.43% | 85% |
| Athena Quantitative | 12,500 | 12.50%/yr | 17.17% | 73% |
| AGSF / Tianyou | 20,000 | 20.00%/yr | 10.83% / 16.73% | 185% / 120% |
| Crabel Advanced Trend 1x (trend, low turnover) | 600 | 0.60%/yr | 8.46% | 7% |

> **Of the five verified intraday CME programmes with published turnover, the incremental retail
> commission bill at $10 per round turn is 39% to 410% of the programme's entire annualised return.
> For three of the five, and for Crabel's flagship, the commission alone exceeds the whole return.**

These programmes exist because they pay institutional, co-located rates measured in cents, not
dollars. **The short-holding-period futures family is not merely low-Calmar at retail cost — at a $10
round turn it is arithmetically insolvent.** Lane 14's screen item 6 ("clears ~$10/round turn") is
not a mild filter on this family; it is the binding one, and it can be checked from the CTAs' own
disclosed turnover without any modelling.

Caveat: `roundturnYearMillion` is self-reported by the CTA at listing time and is not dated; CAROR is
already net of the manager's own (institutional) commissions, so the correct incremental charge is
roughly $8.50–9.50/RT rather than the full $10. Neither correction changes any sign.

---

## THE SCREEN — survivors tagged

**[PROP] survivors: ZERO.** Not one verified record in this lane clears items 4 and 5 jointly, and
the reason is now a single number rather than a narrative: **the prop account requires Calmar 18.9
on open equity, and the verified population's maximum over any record longer than a year is 5.88
(3.48 excluding options books, 1.07 for genuine intraday CME).**

### [PERSONAL] — carried forward, prop-ineligible but not book-ineligible

**P1 — Intraday S&P pattern/statistical trading, flat at the cash close.**
Specimens: Soaring Pelican **Intraday Advantage** (ES only, 187 months from Jan-2011, 4.34%/yr,
Sharpe 0.37, vol 10.26%, 19.50% maxDD) and **FRS** (54 months, 2.58%/yr, Sharpe 0.56, vol 2.84%,
**2.42% maxDD**).
*Prop verdict:* dead. FRS's drawdown fits inside the $2,000 budget, but it earns **$5.12/day** on
$50k; reaching $150/day requires 29× leverage, which takes the drawdown to ~70%.
*Personal verdict:* keep as a **family**, not as a candidate. Two independent live records over 15
and 4.5 years with a positive mean; it is the same family as lane 14's S1 (Gao–Han–Li–Zhou intraday
momentum), and this lane supplies what lane 14 lacked — a **live, cost-inclusive, third-party record
of the family in single-market ES form.** That record's verdict is: real, small, and eaten by retail
costs. Still owes R15 and a pre-registration.

**P2 — Intraday convexity / crisis alpha (long realised volatility, no overnight risk).**
Specimens: QTS **Tail Reaper** (ES, 167 months, *"No overnight positions. Convex/long volatility"*,
2.74%/yr, 55.19% maxDD) and **Deep Field Capital** (Swiss/US regulated, *"Trading primarily intraday,
without any positions and risk overnight, provides a unique capital efficiency"*).
*Prop verdict:* dead **twice** — 55% drawdown against a 4% budget, and it is exactly lane 14's **R7**
shape (right tail does the work) so the consistency rule would refuse the payout even if it passed.
*Personal verdict:* the only family in the lane whose *mechanism* is a stated market-structure claim
rather than an indicator; worth a carry-forward on the personal book where positive skew is not
penalised.

**P3 — Systematic short-term multi-market futures (lane 14's R8), now named and priced.**
Crabel / QIM / R.G. Niederhoffer / Revolution / NuWave. Ratios 0.06–0.46, drawdowns 11–57%.
*Prop verdict:* dead on the drawdown budget, as lane 14 said — and now dead a second time on the
**turnover arithmetic above**, which lane 14 did not have.
*Personal verdict:* carried forward, with the cost finding attached as a hard constraint on any
implementation.

### [NEITHER] — and why

| | why |
|---|---|
| **World Cup Trading Championships winners** | Audited real money, but **no drawdown, trade count or risk statistic is published in the standings at all** — only a percentage. A tournament maximises variance by construction, multiple entries per competitor are permitted and undisclosed, and the one winner whose drawdown *is* published collapses from 23.5 to 1.57 on his own longer account. Evidence about selection, not about strategy. |
| **Collective2 systems** | C2 labels the Grid *"hypothetical performance results"* itself. Its age-stratified Calmar distribution is first-class evidence about **how ratios decay with record length** and worthless as evidence about any strategy. |
| **Option-writing on stock indices** (White River, Buckingham, Tianyou, Athena) | Futures-only prop platforms; unbounded MAE against $2,000; and the 12,500–20,000 round turns/yr imply a 12.5–20%/yr retail commission bill. Confirms lane 14's R5 with numbers. |
| **Darwinex / Myfxbook / ZuluTrade** | FX/CFD instruments, not CME futures. Darwinex's own documentation defines the object correctly (*"The Calmar ratio equals CAGR / MaxDD"*, and *"A Calmar of 2.86 is considered excellent"* — note where that sits relative to 18.9), but the population is not this instrument class. |
| **Striker.com** | The right evidentiary property — *"actual results with commissions and monthly vendor fees included"*, ~200 systems, and (new vs lane 14) rankings **bucketed by account size, including "Under $10,000" and "$10,000–$19,999"**. Still no drawdown, no trade count, no average trade; the detail remains behind a client login. Recorded again as the highest-value **blocked** avenue. One thing it *does* show: in the $10–20k bucket, five of the top ten ranked systems over the past three months are **losses**, the worst at **−$4,371** — a ≥20% quarterly account drawdown inside the *ranked* tier. |

---

## What lane 20 hands forward

1. **The prop constraint is one scale-free number: Calmar ≥ 18.9, measured on open equity.**
   `$150/day ÷ $2,000 = 0.075/day = 18.9/252`. This replaces lane 14's prose about risk budgets
   versus AUM, and it is **leverage-invariant** — verified empirically on Crabel's own 1x/1.5x pair
   (0.458 vs 0.410). No sizing decision, micro contract, or funding level moves it. Only edge does.
2. **Lane 14's 19×–60× band should be restated as 21×–155× at the programme level (median 71×) and
   7.5×–16× at the index level**, with the programme level named as the correct object. Its
   underlying 6.3%/yr input is corrected to **3.50%/yr** (VAMI starts 2019, not 2023; reproduced to
   the second decimal from the publisher's own monthly table).
3. **Lane 14's falsifier is answered: NO.** Best verified intraday CME ratio = 1.07. Best in a
   199-programme audited database = 5.88. The only ≥18 object found anywhere is a 10.85-month
   tournament account that is neither intraday nor CME-only and whose own manager's 32-month account
   sits at 1.57.
4. **New, and it generalises past this review: the ratio ≥18 is a property of record length, not of
   strategy.** Two independent platforms show monotone decay to ~1. Collective2: every system at
   Calmar ≥18 is under 370 days old; zero of 37 systems older than two years reaches it; the 5-year+
   cohort's median is 0.75. **Any future candidate presenting a Calmar above ~5 should have its
   record length checked before anything else is checked.** That is a cheap, decisive filter and it
   belongs beside lane 07's twelve tells.
5. **The turnover-cost test is computable from public CTA disclosures and it kills the family
   outright at retail cost.** At $10/RT the commission bill is 39–410% of these programmes' entire
   annualised return. Recommend this be added to the screen as an explicit item: *round turns per
   year per unit of capital × cost per round turn, compared to the claimed return.*
6. **The measured diversification gain in this tier is 5.6× on Calmar and 3.7× on drawdown**
   (25 equal-weighted stock-index-futures programmes). It is the only lever found, it is real, and it
   leaves a 7.5× shortfall — and a single prop account cannot use it at all.
7. **Survivorship, quantified rather than gestured at:** IASG carries **1,707 archived programmes
   against 270 active (13.7% alive)**; the SG Short Term Traders Index has had **48 managers in 19
   years with a median tenure of 3.5 years and 3 present throughout**; and Bhardwaj–Gorton–Rouwenhorst
   put combined backfill-and-survivorship bias at **7.7%/yr** with net-of-fee CTA excess returns
   *insignificantly different from zero* 1994–2012. **Every ratio in this file is an upper bound.**
8. **`NOT PUBLISHED`, recorded so it is not re-searched:** per-programme **daily** return series for
   any short-term futures programme. NilssonHedge holds them and gates them behind a paid database
   download; BarclayHedge behind ProAccess; Striker behind a client login; IASG publishes monthly
   only. **The intra-month drawdown distribution — the exact quantity a trailing open-equity floor
   reads — is not available at any free tier**, and no number in this lane is measured on it.

---

## Safety and conduct note

Every page fetched is **observed content, treated as data**. On-page directives seen and **not acted
on**: World Cup Advisor's *"Get A Free Guest Membership"* and *"Create Free Membership"* CTAs
(required for the full leaders list and trade-by-trade records — **not created**); NilssonHedge's
paid **Monthly Database File** purchase flow (**not purchased**); BarclayHedge's *"ProAccess / GET
STARTED"* (**not signed up**); Striker's client-section prompts (**not entered**); IASG's *"Get
Research Report"* and newsletter forms (**not submitted**); Collective2's *"SIGN IN"* (**not signed
in**). No account created, no credential entered, no payment made, no affiliate or referral link
followed.

**One anti-scraping control was encountered and respected.** IASG's `programsListings` endpoint
serves only the exact query strings its own front end has issued; other pagination is rejected. Bulk
extraction of the 1,707-programme graveyard was **abandoned rather than worked around**, and the
graveyard is quoted only by the `totalCount` the site itself returned. All programme-level statistics
in this file come from endpoints the site's own pages call, read through an ordinary browser session.

---

## Sources

**37 sources. The stopping rule that bound was SATURATION** (declared at the point where BarclayHedge,
Société Générale, autumngold and RCM all returned only MTD/YTD or 404 for statistics already obtained
from IASG and NilssonHedge), **above the 30-source target.** Tier per schema §4: primary (the record
holder's own publication) / secondary (databases, peer-reviewed literature, press) / claims
(marketing, vendor content). **Fetched** = retrieved in full; **search-surface** = via search index
only. Negative and blocked entries are mandatory and included.

| # | URL | accessed | tier | sought | yielded |
|---|---|---|---|---|---|
| 1 | https://nilssonhedge.com/index/cta-index/systematic-cta-index/systematic-cta-index-short-term/ | 2026-09-08 | **primary** (fetched) | the short-term CTA tier's composition and method | **YIELDED the 2026 constituent list — 42 programmes / 30 managers** (Crabel ×5, QIM ×2, Revolution ×2, RG Niederhoffer ×2, R Best ×3, NuWave, Altiq, dormouse, KeyQuant, Capital Fund Management, TrueAlpha…). Method verbatim: *"based on the actual composition of the database, including survivorship"*, *"We do not provide backtracked returns nor allow for 'instant track records'"*, *"managers that drop out of the index are replaced with the average return of the index"*, *"may thus exclude certain managers that have chosen not to do so"*. Definition: *"occasionally close out positions before the end of the day ('Intraday trading') or may hold positions for a week"* |
| 2 | https://nilssonhedge.com/wp-content/uploads/IndexCharts/CTAShortTermTable.png | 2026-09-08 | **primary** (fetched, image read) | the index's actual monthly returns | **THE LANE'S KEY CORRECTION.** Full monthly table Jan-2019 → Jul-2026, updated 2026-09-06. Compounded here: terminal VAMI **129.78**, **CAGR 3.50%**, month-end **maxDD 2.88%** (peak Jan-2020, trough Mar-2020), vol 3.24%, **Calmar 1.213**, **59 of 91 months below the running peak**. Reproduces all eight of NilssonHedge's own published YTDs exactly. **Lane 14's ~6.3%/yr is wrong** |
| 3 | https://nilssonhedge.com/wp-content/uploads/IndexCharts/CTAShortTermIndexVami.png | 2026-09-08 | **primary** (fetched, image read) | independent check on #2 | **CONFIRMED.** VAMI axis begins at **100 in Jan-2019** (not Jan-2023) and the printed endpoint is **129.77** vs 129.78 computed. Lane 14's "VAMI 125.34, Jan-2023 →" misidentified the series start |
| 4 | https://nilssonhedge.com/index/daily-indices/daily-cta-index/ | 2026-09-08 | primary (fetched) | daily-frequency drawdowns | **METHOD ONLY, NO STATISTICS.** *"We take the median return over many share classes"*, *"We apply a statistical filter to remove outliers"*, *"updated daily, without any manual checks"*, *"may not be consistent over time and contain errors"*. No numeric drawdown published in text |
| 5 | https://nilssonhedge.com/product/databasefile/ · https://nilssonhedge.substack.com/p/database-updated-53 | 2026-09-08 | primary (search-surface) | per-programme daily returns with drawdown | **BLOCKED — behind a paid database purchase / registered download.** *"629 CTA programs have reported returns"* for the current month; *"Daily Data can be downloaded as a CSV file through your user account."* **Not purchased, no account created.** This is where the per-programme daily drawdown distribution lives and it is not free |
| 6 | https://www.iasg.com/wp-json/iasg/indexes | 2026-09-08 | **secondary, primary-adjacent** (fetched) | index-level return and drawdown for eight CTA indices | **YIELDED the index row of Q1's table.** Stock Index Trader 12.57%/5.00% maxDD/Sharpe 1.91/25 progs/219 mo (**Calmar 2.515**); IASG CTA 17.98%/43.72%/204 (0.411); Systematic 17.40%/43.72%/171; Trend Following 16.75%/43.72%/67; Discretionary 13.98%/55.42%/45; Diversified 17.27%/43.72%/136; Option Strategy 13.61%/18.73%/10; Agricultural 16.05%/8.54%/19 |
| 7 | https://www.iasg.com/wp-json/iasg/indexes/iasg-cta-index/programs?pageSize=500 | 2026-09-08 | **secondary** (fetched) | the programme-level ratio distribution | **THE LANE'S CENTRAL DATASET. 199 programmes** with annualisedReturn, maxDrawDown, Sharpe, volatility, dataPoints, inception. Ratio distribution: min −0.346 / p25 0.122 / **p50 0.267** / p75 0.507 / p90 0.899 / **max 5.88**. **≥18: zero. ≥2: six. ≥1: fifteen.** maxDD p10 9.85% / p50 21.12% / p90 46.47%. Only **5 of 199** have maxDD ≤ 4%. Sorted by ratio, the top eight are Hyperion 5.88 (71 mo), Third Wave 3.40 (60), ART Short Term Velocity 2.57 (38), STTS-6FF 2.17 (41), RQSI: ADOY 2.08 (55), Athena 2.06 (67), Vulcan Metals Ultra 1.94 (46), **HPX Old School 1.52 (243 mo)** — the age-decay pattern appearing a third time |
| 8 | https://www.iasg.com/wp-json/iasg/indexes/stock-index-trader-index/programs?pageSize=500 | 2026-09-08 | **secondary** (fetched) | the CME stock-index futures subset | **YIELDED all 25 programmes.** Ratio p25 0.246 / **p50 0.446** / p90 1.008 / max 5.88; maxDD p10 10.32% / p50 18.54% / p90 48.52%. Longest records: Quantitative Tactical Aggressive 219 mo, Stock Index Option Writing 213 mo, SinoPac 202 mo, Enhanced S&P 201 mo, R Best 198 mo, Intraday Advantage 187 mo |
| 9 | https://www.iasg.com/wp-json/iasg/programs/{uri}/group/{group} (25 calls) | 2026-09-08 | **primary** (manager-authored, fetched) | which of the 25 are genuinely intraday, and their turnover | **YIELDED the intraday classification AND the cost finding.** Manager-written descriptions: Intraday Advantage *"In all cases positions are closed by the end of the day. The program only trades the S&P futures contracts – no option selling"*; FRS *"all positions are closed before the end of each trading day"*; Tail Reaper *"fully automated, intraday… • No overnight positions. • Convex/long volatility"*; Artemis 3X *"expected to carry trades overnight"* (excludes it). Plus `roundturnYearMillion`: 5,000 / 1,000 / 2,195 / 5,250 / 5,000 / 11,900 / 20,000 |
| 10 | https://www.iasg.com/indexes/stock-index-trader-index/rankings | 2026-09-08 | secondary (fetched) | the monthly ranking, and index membership | **YIELDED** the June-2026 ranking and the inception dates: Soaring Pelican Intraday Advantage 1/1/2011, Deep Field ICA 5/1/2017, Tianyou 10/1/2012, White River 11/1/2008. Also **two Deep Field programmes reporting 0.00**, i.e. not currently reporting |
| 11 | https://www.iasg.com/wp-json/iasg/programsListings (active vs archived counts) | 2026-09-08 | **secondary** (fetched) | the survivorship denominator | **YIELDED THE SURVIVORSHIP NUMBER: 270 active programmes against 1,707 archived — 13.7% of everything the database has ever carried is alive.** Bulk extraction of the graveyard was refused by a request allowlist and **abandoned rather than circumvented**; only the site's own `totalCount` is quoted |
| 12 | https://www.iasg.com/groups/crabel-capital-management | 2026-09-08 | **secondary** (fetched) | the longest-surviving short-term CTA's economics | **YIELDED, and it supplies the leverage-invariance check.** Multi-Product 1x (inception **1998-03**) CAROR 7.44 / WDD −16.26 (**0.458**); Multi-Product 1.5x 10.05 / −24.49 (**0.410**); Gemini 1x 3.43 / −10.95; Gemini 1.5x 3.93 / −19.41; Advanced Trend 1x 8.46 / −28.47. AUM $1.1–2.1B/programme. NFA 0196351. *"approximately 200 futures and foreign exchange markets"* |
| 13 | https://www.iasg.com/groups/quantitative-investment-management2 | 2026-09-08 | secondary (fetched) | ditto, QIM | **YIELDED.** Quantitative Global 6.58 / −23.64 ($842M); Tactical Aggressive 14.03 / −57.11 ($354M); Cipher 3.37 / −13.89 ($241M). **The highest-CAROR programme in the panel carries the deepest drawdown** |
| 14 | https://www.iasg.com/groups/r-g-niederhoffer-capital-management-inc | 2026-09-08 | secondary (fetched) | ditto, Niederhoffer (19/19 SG index years) | **YIELDED.** Macro Diversified 6.94 / −54.24 ($729M); Smart Alpha 2x −0.98 / −31.77 ($225M) |
| 15 | https://www.iasg.com/groups/revolution-capital-management | 2026-09-08 | secondary (fetched) | ditto, Revolution (18/19 SG index years) | **YIELDED.** Alpha Program 5.17 / −21.12 ($305M); Mosaic Institutional −0.76 / −32.09 ($121M) |
| 16 | https://www.iasg.com/groups/nuwave-investment-management-llc | 2026-09-08 | secondary (fetched) | a named "Short-Term Futures Portfolio" | **YIELDED.** Short-Term Futures Portfolio 0.81 / −12.97 (**0.062**); Commodity Directional −0.86 / −25.99 |
| 17 | https://www.iasg.com/groups/deep-field-capital-ag | 2026-09-08 | **primary** (manager-authored, fetched) | a pure intraday institutional CME programme | **PARTIAL — description yes, numbers no.** *"No programs found"* on the group page despite two programmes appearing in the index ranking at 0.00, i.e. **it has stopped reporting.** Description is the cleanest statement of the family in the lane: *"purely systematic… niche, long (realized) volatility intraday and short-term systematic programs in global futures and equity markets… Trading primarily intraday, without any positions and risk overnight, provides a unique capital efficiency"* |
| 18 | https://www.iasg.com/en-us/resources/article/analyzing-the-performance-table | 2026-09-08 | **primary** (fetched) | how IASG's maxDD is measured | **YIELDED THE LOAD-BEARING CAVEAT, verbatim:** *"maximum drawdown, the percentage loss a program experiences from its highest net asset value to its lowest"*, computed from the **monthly** performance table. **Month-end basis. Intra-month and open-equity excursions are invisible**, so every ratio in this file overstates what a trailing floor would have seen |
| 19 | https://www.worldcupadvisor.com/ | 2026-09-08 | **primary** (fetched) | real-money records **with** drawdown | **THE NEAREST MISS TO THE FALSIFIER.** Five featured proprietary accounts, net of all subscription, commission and transaction costs, with peak-to-valley drawdown. Scherman 2023 World Cup $241,360 → **+491.9% / −26.2% / 10.85 months**; Hsieh +222.8% / −35.7% / 15.13; Scherman Emerge Funds +209.7% / −33.5% / 32.09; Perdices +73.2% / −21.2% / 8.13. Verbatim caveat: *"Peak-to-valley drawdown is the greatest cumulative percentage decline in **month-end** net equity"* |
| 20 | https://www.worldcupadvisor.com/usersite/Partner/widget?d=429 | 2026-09-08 | **primary** (fetched) | a sixth record and the full disclosure | **YIELDED Sambataro Momentum Selection $10,162 → +233.8% / −37.4% / 42.68 months (ratio 1.08)** — the longest record and the lowest ratio, completing the decay series. Plus the self-selection disclosure, verbatim: *"Accounts trading in the World Cup Trading Championships do not necessarily represent all the WCC accounts controlled by the competitor"*; *"The advisor may have previously displayed other accounts on WCA"*; *"There have been no net cash additions to these lead account"* |
| 21 | https://www.worldcupchampionships.com/world-cup-trading-championship-historical-standings | 2026-09-08 | **primary** (fetched) | audited championship results with risk statistics | **A CLEAN NEGATIVE, AND IT IS THE FINDING FOR THIS SOURCE. The standings publish YEAR, EVENT, PLACE, NAME and PERCENTAGE — and nothing else. No drawdown, no trade count, no risk metric of any kind.** 2025 Futures Tirutrade AG 324.70%; 2024 Futures Brent Carlile 532.30%; 2025 Forex Pau Perdices Bellet 600.90%; 1987 Larry Williams 11,376.00%. The longest-running audited competition in the sector does not publish the quantity the barrier reads |
| 22 | search: World Cup Trading Championships overview / champions by year | 2026-09-08 | claims (search-surface) | audit status and division structure | **PARTIAL.** *"longest-running, independently audited trading competition"*, *"participants trade their own capital in independently monitored brokerage accounts"*, results *"third-party audited and published publicly"*. Chuck Hughes 10 titles, Andrea Unger 4. No drawdown anywhere |
| 23 | https://medium.com/@josue.monte/how-ivan-scherman-conquered-the-2023-world-cup-championship-with-data-science-... · https://gulfnews.com/business/markets/why-a-scientific-approach-to-investment-is-the-best-strategy-... | 2026-09-08 | claims (search-surface) | is the ≥18 record an intraday CME book? | **YIELDED THE DISQUALIFICATION.** Scherman's winning book is multi-asset — *"Currency Futures, Energies, Grains, Indices, Meats, Metals, Softs, and Treasury Futures"* — **not intraday, not CME-only.** And the decisive comparator: his firm's claim for its own 17-year record is *"an average annual net performance of 23%"*, against 491.9% in the tournament year |
| 24 | https://collective2.com/grid | 2026-09-08 | claims/secondary (fetched) | how the ratio behaves as records lengthen | **THE LANE'S SECOND-BIGGEST FINDING. 993 systems**; extracted the 100 most-popular with Calmar, annualised return net of trading costs, maxDD, age, %futures. Median Calmar by age: 9.76 (<180d) → 6.85 → 3.05 → 1.40 → **0.75 (5yr+)**; count ≥18: 10 → 2 → 1 → **0 → 0**. All six futures-only systems ≥18 are 41–370 days old. Self-labelled verbatim: *"These are hypothetical performance results that have certain inherent limitations"* — includes a **2,427,580.1%** annualised return on a **6-day-old** system |
| 25 | https://wholesale.banking.societegenerale.com/fileadmin/indices_feeds/SG_STTI_Constituents.pdf | 2026-09-08 | **primary** (fetched, parsed with pypdf) | who persists in the audited short-term tier | **YIELDED THE SURVIVORSHIP PANEL. 48 distinct managers across 19 index years (2008–2026); median tenure 3.5 years; only three present throughout** — Crabel, R.G. Niederhoffer, Revolution — with *"AlphaQuest LLC (AlphaQuest – Original Program) **REMOVED MARCH 1, 2026**"*. Caveat recorded: the index is capped at ten constituents from 2012, so exit ≠ death. (Note for future sessions: **pypdf is available in this environment and parses these files**, unlike lane 14 source #5's poppler dependency) |
| 26 | https://wholesale.banking.societegenerale.com/en/prime-services-indices/ | 2026-09-08 | primary (fetched) | SG STTI since-inception return, vol, drawdown | **NEGATIVE — MTD/YTD ONLY, and the page served a stale 2015 snapshot.** No annual returns, no inception statistics, no drawdown. Directs to the Capital Consulting team / SG Markets platform. **Saturation signal #1** |
| 27 | https://portal.barclayhedge.com/cgi-bin/indices/displayIndices.cgi?indexID=sg · .../displayHfIndex.cgi?...SG-Short-Term-Traders-Index | 2026-09-08 | secondary (fetched) | the same, via BarclayHedge | **NEGATIVE / BLOCKED — MTD/YTD only** (SG CTA 0.97%/12.19%; SG STTI 0.20%/**5.98%**; SG Trend 0.85%/12.03%), history behind **ProAccess**. Definition retained: SG STTI tracks *"a portfolio of CTAs and Global Macro managers executing diversified trading strategies with a **less than 10-day average holding period**"*. **Not signed up. Saturation signal #2** |
| 28 | https://www.toptradersunplugged.com/trend-following-performance-report-october-2025/ (and sibling monthly reports) | 2026-09-08 | secondary (search-surface) | SG index since-inception statistics | **YIELDED the one long-run SG statistic obtainable free: SG Trend Index historical CAGR 5.27% with maximum drawdown 20.61% (Calmar 0.256).** Also SG STTI *"equalled its best yearly return up 11.3% in 2022"* with index volatility *"around 4%"* |
| 29 | https://www.ssrn.com/abstract=1279594 · https://academic.oup.com/rfs/article-abstract/27/11/3099/1597777 | 2026-09-08 | **secondary, peer-reviewed** (search-surface) | the survivorship correction | **YIELDED THE CORRECTION FACTOR.** Bhardwaj, Gorton & Rouwenhorst, *Fooling Some of the People All of the Time*, RFS 27(11) 2014: 1994–2012 CTA excess returns **net of fees insignificantly different from zero** while gross were **6.1%**; **survivorship bias 2.21% (VW) / 4.15% (EW), backfill 1.92% / 3.66%, combined 7.7% annualised** |
| 30 | https://www.cmegroup.com/content/dam/cmegroup/education/files/survival-of-commodity-trading-advisors.pdf | 2026-09-08 | secondary | CTA survival curves, systematic vs discretionary | **BLOCKED — fetch timed out (60s) twice.** Logged so it is not re-attempted by this route. The survivorship question was answered instead from #11 (IASG's own active/archived counters), #25 (SG index tenure) and #29 (published bias estimates) |
| 31 | https://striker.com/ranking.php | 2026-09-08 | secondary (fetched) | actual-fill retail futures system results | **PARTIAL, WITH TWO FACTS LANE 14 DID NOT HAVE.** (a) A denominator: *"The rankings draw from **approximately 200 trading systems**"*. (b) Rankings are **bucketed by account size — "Under $10,000" and "$10,000–$19,999"** — directly comparable to a $50k prop account. Past-year <$10k leaders: Abacus Raider Xtreme $14,093.60, Caracal $11,499.98. **But five of the top ten in the $10–20k bucket over three months are losses, worst −$4,371** (≥20% of account). Still **no drawdown, no trade count, no average trade** — detail behind a client login. Verbatim: *"based on actual trades with commissions, monthly vendor fees, and exchange/nfa fees included"*; *"not necessarily representative of a single account"* |
| 32 | https://www.toptradersunplugged.com/finding-anomalies-to-fuel-short-term-strategies/ | 2026-09-08 | claims/secondary (search-surface) | how the survivor family manages risk | **YIELDED THE MOST USEFUL SINGLE COMPARISON IN THE LANE.** Crabel: *"stop losses at position, market and strategy levels and a **2.5% daily stop loss at the overall portfolio level**"*, under Toby Crabel's *"Live to fight another day"*. **The best-established short-term futures manager on earth allows itself, in one day, 62.5% of the entire lifetime drawdown budget the prop account grants** |
| 33 | https://help.darwinex.com/darwinia-rating · https://www.darwinexzero.com/docs/rating | 2026-09-08 | primary (search-surface) | verified retail track records with drawdown | **[NEITHER] — FX/CFD, not CME futures. Retained for one calibration:** Darwinex defines the object exactly as this lane does — *"The Calmar ratio equals CAGR / MaxDD"* — and states *"A Calmar of **2.86** is considered excellent."* The industry's own word for "excellent" is 6.6× below what the prop account requires |
| 34 | https://www.fxfundmanagers.com/how-to-read-myfxbook-track-record-properly/ (and cluster) | 2026-09-08 | claims (search-surface) | Myfxbook / ZuluTrade verified futures records | **NOTHING FOR THIS LANE — logged as one cluster.** Myfxbook verifies via MT4/MT5 read-only investor password; the population is **forex CFDs**, not CME futures, and no futures ranking exists. Every page reached was attached to a robot vendor, a fund-manager service or a signals seller. **Saturation signal #3** |
| 35 | https://www.barclayhedge.com/solutions/indices/cta-index/ | 2026-09-08 | secondary | Barclay CTA Index long-run statistics | **BLOCKED — 301 redirect to https://ionanalytics.com/barclayhedge/ (corporate landing page), not followed to a data page.** Logged so it is not re-attempted with this path. **Saturation signal #4 — this is where saturation was declared** |
| 36 | https://www.autumngold.com/Advisor/cta_profile.php?id=113808 | 2026-09-08 | secondary | an independent second database for Soaring Pelican | **BLOCKED — HTTP 404.** The profile IDs surfaced by search are stale. Logged; the same programmes were obtained from IASG instead |
| 37 | https://www.rcmalternatives.com/fund/intraday-crisis-alpha-ica-deep-field-capital/ (and Preqin / Opalesque profiles) | 2026-09-08 | claims/secondary (search-surface) | performance for a pure intraday institutional programme | **NEGATIVE — no return or drawdown figure is public for Deep Field's ICA or ICC programmes anywhere reached.** Descriptive text only (*"pure intraday momentum program focusing on large intraday momentum and tail events in global equity indices"*). Combined with #17 (the manager has stopped reporting to IASG), **the single best-fitting programme in the world for this screen publishes no numbers at all** |

**Negative and blocked entries, per schema §4:** #5 (NilssonHedge per-programme daily data behind a
paid download — the highest-value block, and the reason Q4 has no intra-month distribution), #21
(the audited championship publishes no risk statistic at all — a finding, not an absence), #26/#27/
#35/#36 (four consecutive database sources yielding only MTD/YTD or errors — **this is the saturation
signal**), #30 (fetch timeout), #17/#37 (the best-fitting intraday programme in the survey publishes
nothing), #34 (the FX-verification tier is out of instrument class).

**Searches run that produced no new source, so they are not repeated:** NFA-filed CTA disclosure
documents with worst peak-to-trough for Soaring Pelican or Deep Field (not public; NFA's own guidance
PDF describes the requirement but the documents are distributed on request); Form ADV Part 2A for
Crabel (not located — Crabel is an NFA-registered CPO/CTA with an SEC 801- exempt-reporting number,
so no full Part 2A brochure surfaced); any free source for per-programme **daily** returns in this
tier (none — this is a structural gap, not a search failure); prop-firm published leaderboards with a
strategy or drawdown field (lane 07 #24 and lane 14 #24 already saturated this; not re-searched).
