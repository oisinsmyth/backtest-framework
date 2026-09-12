# B3 — Where does a slow characteristic premium accrue within the trading day?

**Round 2, lane `B3`. External evidence only.** Campaign contract:
[`00-SCHEMA.md`](00-SCHEMA.md). Slate: [`R2-00-slate.md`](R2-00-slate.md). Nothing here is elevated
out of `docs/research/` ([R15](../../RULES.md#r15)); nothing is closed or admitted.

I have no access to the programme's private data and claim nothing about it. Internal figures quoted
in the framing (the overnight `+8.59%`/`−0.36%` split, the `86.6%` timing share, the era and
volatility inversions, the flat 1–12 month accrual, `33.8 bp`/side, `~67.6 bp` round trip,
`~41.6%` of a cohort unreachable intraday) are **quoted from the commissioning brief, never
recomputed**, and are used only to say what the external evidence bears on.

---

## 0. THE ANSWER, FIRST, BECAUSE IT INVERTS THE LANE'S PREMISE

**The bar offered two outcomes — named evidence, or a confirmed absence. It is the first, and the
evidence goes AGAINST the hypothesis.**

**The decomposition HAS been done for slow characteristics, twice, in the Journal of Financial
Economics, and in both cases the slow characteristic premium is an INTRADAY phenomenon with a
NEGATIVE overnight component.** Lou, Polk and Skouras (2019, JFE 134:192–213) decompose 14
strategies over 1993–2013 and find profitability (`ROE`) earns **−0.95%/month overnight and
+1.42%/month intraday**; value (`BM`) **−0.10% / +0.48%**; investment (`INV`, asset growth)
**−0.28% / +0.97%**; accruals **−0.47% / +1.10%**; equity issuance **−0.52% / +1.13%**. The five
strategies that DO earn their premia overnight are all past-return strategies — four momentum
variants and short-term reversal. Bogousslavsky (2021, JFE 141:172–194), on an independent
1986–2015 sample at half-hour resolution, reaches the same conclusion, and his Internet Appendix
gives the number that matters most here: **the LONG leg of gross profitability earns an overnight
alpha of +0.07 bp/day (t = 0.23) against +1.77 bp/day intraday.**

So the join this lane was commissioned to look for **does not exist in the published literature, and
its opposite does.** Two things follow, and the second is the more useful.

1. **A monthly-rebalanced characteristic premium is, on the only two samples that measure it, earned
   during the trading session.** Whatever the programme's overnight edge is, the published evidence
   says it is not a characteristic premium being collected overnight.
2. **BUT THE TWO FACTS ARE NOT IN CONFLICT, AND THE RECONCILIATION IS THIS LANE'S MOST IMPORTANT
   OUTPUT.** The literature is equally clear that the **MARKET's** return is overnight — Lou, Polk
   and Skouras (2022) measure the quarterly intraday `RMRF` mean at **0.000** against **0.018**
   overnight over 1993Q3–2019Q4. A long-only equity book's total return is dominated by its market
   exposure, not by its characteristic tilt. So **an overnight total return and an intraday
   characteristic alpha are exactly what the literature predicts for a long-only book**: the beta
   collects the overnight market premium, the tilt earns its alpha intraday. The programme's central
   fact and `A2`'s surviving family are consistent — they are simply statements about two different
   objects, the level and the tilt. **Nothing about the overnight finding argues for or against a
   characteristic book.**
3. **And the distinction is DESCRIPTIVE, not actionable, for a book that holds across both sessions
   for months** — §6. That is the lane's negative headline, and §6 prices it: separating the sessions
   costs `~38×` the alpha it would isolate.

**Two of this programme's own contested internal findings are independently corroborated by the
published literature** — §5.3 (the volatility inversion, matched almost exactly by `IVOL`'s
decomposition in LPS 2019) and §5.2 (the era inversion, matched by the original authors of the
overnight drift reporting in July 2026 that it has gone to zero since 2021). That corroboration is
worth more than the headline.

---

## 1. Q1 — IS THERE PUBLISHED EVIDENCE DECOMPOSING A CHARACTERISTIC PREMIUM?

### 1.1 Yes. Lou, Polk and Skouras (2019) — the primary source, read in full

**[PEER-REVIEWED] [read in full]** — Dong Lou, Christopher Polk, Spyros Skouras, *"A tug of war:
Overnight versus intraday expected returns"*, **Journal of Financial Economics 134 (2019) 192–213**.
Obtained as `https://personal.lse.ac.uk/polk/research/TugOfWar.pdf`, `HTTP 200`,
`1,688,485` bytes, `application/pdf`; title and journal header verified on page 1 before use;
extracted locally with `pypdf` and read.

They state their own claim of priority: *"To our knowledge, this is the first paper decomposing
firm-level returns as well as the returns to popular characteristics into their overnight and
intraday components."*

**Table 2, the whole table, verbatim from the extracted text.** Sample **1993–2013** (TAQ-constrained),
CRSP–Compustat. Value-weighted extreme-decile (or quintile) long–short portfolios, **monthly CAPM
alphas in percent** (excess returns for the `CRSP` row), `t`-statistics in parentheses, Newey–West
12 lags. **Stocks below `$5` a share and/or in the bottom NYSE size quintile are excluded.** Each
strategy is signed so that prior research would expect a positive return.

| strategy | overnight | intraday | close-to-close (sum) |
|---|---|---|---|
| `CRSP` (value-weight index excess) | **+0.55%** (3.62) | +0.38% (1.87) | +0.93% |
| `ME` size (small − large) | +0.11% (0.75) | **+0.43%** (1.85) | +0.54% |
| `BM` value (high − low) | −0.10% (−0.67) | **+0.48%** (2.21) | +0.38% |
| `MOM` momentum | **+0.98%** (3.84) | −0.02% (−0.06) | +0.96% |
| `SUE` earnings surprise | **+0.56%** (3.20) | +0.21% (0.70) | +0.77% |
| `INDMOM` industry momentum | **+1.07%** (6.47) | −0.63% (−2.03) | +0.44% |
| **`ROE` profitability (high − low)** | **−0.95%** (−6.25) | **+1.42%** (5.58) | +0.47% |
| **`INV` asset growth (low − high)** | **−0.28%** (−2.10) | **+0.97%** (4.39) | +0.69% |
| `BETA` (low − high) | −0.49% (−2.17) | +0.70% (2.40) | +0.21% |
| `IVOL` (low − high) | **−1.46%** (−5.23) | **+2.48%** (6.21) | +1.02% |
| **`ISSUE` equity issuance (low − high)** | **−0.52%** (−3.27) | **+1.13%** (6.13) | +0.61% |
| **`ACCRUALS` (low − high)** | **−0.47%** (−3.25) | **+1.10%** (4.73) | +0.63% |
| `TURNOVER` (low − high) | −0.29% (−1.98) | +0.57% (2.58) | +0.28% |
| `STR` short-term reversal | **+0.93%** (4.28) | −1.05% (−3.25) | −0.12% |

Their own summary, quoted: *"nine of the 14 strategies we study earn their entire premia intraday
(including size which is weak in our sample…). The five exceptions to this finding are all strategies
based on past returns (or their close cousin, earnings announcements)."* And on the characteristic
families specifically: *"For all strategies that earn statistically significant premia intraday (value,
profitability, investment, market beta, idiosyncratic volatility, equity issuance, discretionary
accruals, and share turnover), there is an economically and statistically significant overnight premium
that is opposite in sign… these classic asset pricing anomalies are in fact primarily intraday
anomalies."* On issuance and accruals they say *"more than 100% of the premium occurs intraday"* in
both cases.

**`ROE`'s intraday component is 302% of its close-to-close total [MEASURED IN BRIEF — arithmetic on
the table above, `1.42 / (1.42 − 0.95)`].** That is the sharpest form of the finding: a book holding
profitability close-to-close collects `+0.47%/month`; the session split says it earned `+1.42%`
during the day and gave back `−0.95%` overnight.

**Caveats that limit the transfer, stated before the transfer is attempted.** These are
**value-weighted long–short deciles** on a universe that excludes sub-`$5` stocks **and the entire
bottom NYSE size quintile**; the programme is equal-weighted, long-only, `$5`-floored and explicitly
small-to-mid. The decomposition of a long–short spread is **not** the decomposition of its long leg —
§1.3 supplies the long leg separately, and it matters.

### 1.2 Yes again, independently. Bogousslavsky (2021) — abstract verified, Internet Appendix read in full

**[PEER-REVIEWED] [abstract only for the main text; Internet Appendix read in full]** — Vincent
Bogousslavsky, *"The cross-section of intraday and overnight returns"*, **Journal of Financial
Economics 141 (2021) 172–194, DOI 10.1016/j.jfineco.2020.07.020**.

**I could not obtain the main text.** SSRN `Delivery.cfm` returned `HTTP 403` with a Cloudflare
"Just a moment…" body (5,810 bytes of HTML, not a PDF); OpenAlex reports the work `oa_status:
closed` with no repository copy. **The author's own site posts no main-text PDF** — only the
Internet Appendix. So the main text is `[abstract only]`, taken verbatim from the RePEc record:

> *"I investigate cross-sectional variation in stock returns over the trading day and overnight to
> shed light on what drives asset pricing anomalies. Margin requirements are higher overnight, and
> lending fees are typically charged only on positions held overnight. Such institutional constraints
> and overnight risk incentivize arbitrageurs who trade on mispricing to reduce their positions before
> the end of the day. Consistent with this intuition, a mispricing factor earns positive returns
> throughout the day but performs poorly at the end of the day. This pattern strengthens in the second
> half of the sample and is shared by several well-known anomalies."*

**The Internet Appendix, however, I have in full, and it carries the numbers.**
`http://bogousslavsky.github.io/files/IP_InternetAppendix.pdf`, `HTTP 200`, `369,387` bytes,
`application/pdf`, title page reads *"Internet Appendix to 'The Cross-Section of Intraday and
Overnight Returns', Vincent Bogousslavsky, July 14, 2020"*. Extracted locally and read.

**The characteristic list settles Q1 on its own.** The appendix's tables are built on: accruals
(`AC`), market beta (`BE`), log book-to-market (`BM`), **gross profitability (`GP`)**, log illiquidity
(`IL`), idiosyncratic volatility (`IV`), 12-month momentum (`MO`), **log net stock issues growth
(`NI`)**, log market capitalisation (`SI`), and the Stambaugh–Yu–Yuan mispricing score (`MIS`). Four
of those — accruals, book-to-market, gross profitability, net issuance — are **annually-rebalanced
accounting characteristics**, which is precisely the object the lane asked about.

**Method, from the table notes.** NYSE/Amex/NASDAQ common stocks, **1 Jan 1986 – 31 Dec 2015**,
NASDAQ included from 1993. Value-weighted decile portfolios on **NYSE breakpoints**, held one month.
Price `> $5` (`> $10` in Table IA.6) **and market cap `> $100m`** at the end of the previous month.
Financial firms excluded from accounting sorts. Returns from **quote midpoints**; the first intraday
interval **starts at 9:45am**, so the reported `OV` bucket runs previous close → 9:45am midquote and
contains the opening auction plus the first fifteen minutes. Newey–West, 14 lags.

**Table IA.6 — long–short decile alphas in bp, `$10` filter, quote midpoints.** `OV` as printed;
the intraday total is my own sum of his 13 printed interval alphas **[MEASURED IN BRIEF]**.

| characteristic | `OV` α | Σ intraday α | total | last half-hour (3:30) |
|---|---|---|---|---|
| Book-to-market (high − low) | **−2.69*** ** (−5.13) | +2.69 | 0.00 | +0.98*** |
| **Gross profitability (high − low)** | **−0.09** (−0.18) | **+2.30** | +2.21 | **−1.21*** ** |
| Net stock issues (low − high) | **−1.31*** ** (−3.05) | +2.92 | +1.61 | **−1.67*** ** |
| Accruals (low − high) | +0.58 (1.19) | +0.23 | +0.81 | −0.40** |
| Momentum (high − low) | **+6.36*** ** (7.60) | −1.73 | +4.63 | −0.57* |
| Size (small − large) | **−1.10*** ** (−3.15) | +2.48 | +1.38 | **+2.91*** ** |
| Illiquidity (high − low) | **−2.06*** ** (−5.51) | — | — | **+3.28*** ** |
| Idiosyncratic vol (low − high) | **−4.60*** ** (−6.96) | — | — | −1.13*** |

**The agreement with LPS across two non-overlapping-in-construction samples is the strongest thing in
this lane.** Different decade span (1986–2015 vs 1993–2013), different profitability definition
(gross profitability vs `ROE`), different price convention (quote midpoints vs first-half-hour VWAP),
different intraday resolution (13 half-hours vs one open-to-close block) — and the same answer for
every slow characteristic: **zero or negative overnight, positive intraday.** Momentum is overnight in
both. Size is last-half-hour in Bogousslavsky and intraday-but-weak in LPS.

**Accruals is the one slow characteristic that is NOT clearly intraday**, and the two papers disagree
on it: LPS report `−0.47%/month` overnight with `t = −3.25`, while Bogousslavsky's `$10` decile
alpha is `+0.58 bp/day` with `t = 1.19` — insignificant, and of the opposite sign.
**Recorded, not adjudicated.** They are different accruals definitions (discretionary vs total) on
different universes; I would weight LPS's sign for a `$5`-floored universe since its filter is closer,
but the honest statement is that accruals is unresolved between them.

### 1.3 The long leg, separately — the number a long-only book should actually read

**Internet Appendix Table IA.2** reports intraday and overnight **alphas of the long (`αL`) and short
(`αS`) legs separately**, `$5` filter, `> $100m`, quote midpoints, VW deciles, 1986–2015. This is the
single most decision-relevant table I found in this lane, because the programme is long-only.
`OV` values as printed; Σ intraday is my sum of the 13 printed interval alphas **[MEASURED IN BRIEF]**.

| leg | `OV` α (bp/day) | Σ intraday α (bp/day) | total |
|---|---|---|---|
| **Gross profitability, LONG** | **+0.07 (t = 0.23)** | **+1.77** | +1.84 |
| Gross profitability, SHORT | +0.32 (t = 1.07) | −0.89 | −0.57 |
| **Net stock issues, LONG** | **+0.09 (t = 0.29)** | **+0.68** | +0.77 |
| Net stock issues, SHORT | **+1.49 (t = 4.85)** | −2.59 | −1.10 |
| Idiosyncratic volatility, LONG | −1.27 (t = −5.05) | +2.47 | +1.20 |
| Idiosyncratic volatility, SHORT | **+3.79 (t = 7.16)** | −6.41 | −2.62 |

**Three findings, and the first is the one to carry forward.**

1. **The long leg of profitability has an overnight alpha of statistically and economically zero**
   (`+0.07 bp/day`, `t = 0.23`) and earns `+1.77 bp/day` intraday. Ninety-six percent of its alpha is
   intraday. Same for net issuance (`+0.09`, `t = 0.29`, versus `+0.68` intraday).
2. **The overnight component of these anomalies lives almost entirely in the SHORT leg.** High-issuance
   stocks earn `+1.49 bp/night` (`t = 4.85`) and high-IVOL stocks `+3.79 bp/night` (`t = 7.16`) —
   that is what makes the long–short's overnight component negative. **The long–short's negative
   overnight number is a statement about the names the programme would not hold.** This aligns with
   the inherited finding that *"what remains sits in the short leg"* — here the *session* structure
   sits in the short leg too.
3. **Consequently the mechanism Bogousslavsky proposes in his abstract — arbitrageurs unwinding before
   the close because margin is higher and lending fees are charged overnight — predicts essentially
   nothing for a long-only book that never shorts and never unwinds. And the data agree: the long
   legs' overnight alphas are zero.** §4.5.

### 1.4 Third-party confirmation of my reading, which matters because the reading is load-bearing

**[WORKING PAPER] [read in full]** — Glasserman, Krstovski, Laliberte and Mamaysky, *"Does Overnight
News Explain Overnight Returns?"*, arXiv:2507.04481v1, 6 July 2025, 43 pages; downloaded
`HTTP 200`, `1,086,346` bytes, title verified. Their literature review states independently:

> *"Lou, Polk, and Skouras (2019) … find that momentum returns are primarily earned overnight, but
> several other anomalies (including value, profitability, and investment) earn premia intraday."*

I did not take the finding from a summariser. I read LPS Table 2 in the paper, read Bogousslavsky's
appendix tables, and then found a fourth independent group restating it. **Three sources, one
conclusion.**

### 1.5 What has NOT been done — the genuine absence, narrower than the lane hoped

The absence is real but it is not the absence the lane was designed around. **Nobody has published
the decomposition:**

- **equal-weighted.** Every decomposition I found is value-weighted (LPS, Bogousslavsky, Glasserman)
  or equal-weighted only on beta-sorted portfolios (Hendershott–Livdan–Rösch). Bogousslavsky's
  appendix shows the value-weight/equal-weight gap matters in the adjacent case: Baltussen, Da and
  Soebhag's end-of-day reversal spread rises from value-weighted to **`6.38 bp/day` equal-weighted
  (`t = 17.30`)**, *"indicat[ing] a stronger reversal for smaller stocks."*
- **long-only, as a held book.** Table IA.2 gives long-leg alphas for three characteristics and
  nobody reports a long-only *portfolio return* decomposition with exposure.
- **microcap- or low-price-inclusive.** Every sample imposes `$5` plus either `> $100m` market cap or
  exclusion of the bottom NYSE size quintile. Given that the overnight components are largest among
  the illiquid, small and high-volatility names, this is exactly where the programme's universe
  differs and exactly where the literature is silent.
- **past 2015.** LPS ends 2013; Bogousslavsky ends 2015; Glasserman's characteristic-adjusted work
  runs to 2022 but on S&P 500 members only. **I found no published extension of the slow-characteristic
  decomposition into the 2016–2026 window.** I searched for one specifically and did not find it.

**So an original measurement IS available to this programme, on three axes (equal weight, long-only,
post-2015) rather than on the question itself — and §7 argues it cannot be done honestly on a
dead-inclusive universe with the data described.**

---

## 2. Q2 — WHAT IS DOCUMENTED FOR THE DECOMPOSITION GENERALLY

### 2.1 The market

| source | object & sample | overnight | intraday |
|---|---|---|---|
| **LPS (2019) Table 2** `[PEER-REVIEWED] [read in full]` | VW CRSP index excess return, 1993–2013, monthly | **+0.55%/mo** (3.62) | +0.38%/mo (1.87) |
| **LPS (2022) Table I** `[WORKING PAPER] [read in full]` | `RMRF`, SPY ETF, 1993Q3–2019Q4, **quarterly means** | **+0.018** (σ 0.045) | **+0.000** (σ 0.066) |
| **Cliff, Cooper & Gulen (2008)** `[WORKING PAPER] [snippet only]` | S&P 500 individual stocks, 1993–2006, daily bp | **+2.82 to +4.76 bp** | **−2.85 to +0.22 bp** |
| **Glasserman et al. (2025)** `[WORKING PAPER] [read in full]` | S&P 500 stocks, since 2000 | difference **+2.75 bp/day ≈ 7.2%/yr** in favour of overnight | |
| **Bondarenko & Muravyev (2023)** `[PEER-REVIEWED] [snippet only]` | E-mini S&P 500 futures, tick, 2004–2018 | **the four hours around the European open account for the entire average market return, Sharpe 1.6, surviving transaction costs**; the other 20 hours are *"a noisy zero"* | |
| **Boyarchenko, Larsen & Whelan (RFS 2023; blog update 2026)** `[PEER-REVIEWED + OFFICIAL BLOG] [blog read in full]` | E-mini S&P 500, 1998–2020 | the **2:00–3:00am ET** hour alone ≈ **3.7%/yr**, *"more than 60 percent of the contract's 5.9 percent annualized close-to-close return"* | — |
| **Kelly & Clark (2011)**, J. Asset Management `[UNVERIFIED]` | index ETFs 1999–2006 | cited by Glasserman et al. as finding the same pattern; **I did not open it** | |

**A conflict to record, not adjudicate, and it is between the same authors.** LPS (2019) put the
intraday market excess return at `+0.38%/month` (`t = 1.87`, marginally positive) over 1993–2013;
LPS (2022) put the intraday quarterly `RMRF` mean at exactly **0.000** over 1993Q3–2019Q4. Those are
`~1.14%/quarter` versus `0.00%/quarter`. Both use a first-half-hour VWAP open; the 2019 paper uses
bottom-up CRSP stocks, the 2022 paper the SPDR S&P 500 ETF, and the 2022 sample adds 2014–2019.
**Either the 2014–2019 extension is strongly negative intraday, or the index-versus-bottom-up proxy
matters, or the risk-free allocation convention differs.** I did not resolve it and the brief does
not lean on either figure alone.

### 2.2 Size

LPS: `ME` is the weakest of the nine intraday strategies — `+0.43%` intraday (`t = 1.85`, which they
flag in a footnote as *"only marginally fail[ing] to achieve intraday significance"*) against
`+0.11%` overnight. Bogousslavsky is sharper: **the size premium is a last-half-hour phenomenon** —
`+2.91 bp` in the 3:30–4:00 bucket (`t = 10.65`) against `−1.10 bp` overnight, midquote `$10`; on
trade-based prices at `$5` the 3:30 bucket is `+5.19 bp` (`t = 17.65`) and the overnight α collapses to
`+0.04` (`t = 0.11`). Illiquidity behaves identically (`+3.28 bp` at 3:30, `−2.06 bp` overnight). His
abstract's own phrasing: *"size and illiquidity premia are realized in the last thirty minutes of
trading."*

### 2.3 Volatility and beta — and this is where the programme's own cross-sectional inversion shows up

- **LPS:** `IVOL` (low − high) earns **`+2.48%/month` intraday and `−1.46%/month` overnight** — *"more
  than 100% of the IVOL premium occurs intraday."* Read in the other direction: **low-volatility names
  outperform during the session; high-volatility names outperform overnight.**
- **Bogousslavsky:** `IV` (low − high) `−4.60 bp` overnight, large positive early-session alphas
  (`+1.32`, `+2.23`, `+1.00`, `+1.09` in the first four buckets). Same direction. From the long/short
  legs: the high-IVOL short leg earns **`+3.79 bp/night`**, the low-IVOL long leg **`−1.27 bp/night`**.
- **Hendershott, Livdan & Rösch (2020, JFE 138:635–662)** `[PEER-REVIEWED] [read in full]`, downloaded
  from `faculty.haas.berkeley.edu/hender/CAPMday-night.pdf`, `HTTP 200`, `1,760,635` bytes, journal
  header verified: *"Stock returns are positively related to beta overnight, whereas returns are
  negatively related to beta during the trading day."* Sample **1992–2016**, CRSP open prices. The
  24-hour security market line is flat; the night SML slopes up and the day SML slopes down, with
  `R²` of **96.2% (night)** and **92.2% (day)** for beta-sorted portfolios. High-minus-low beta earns
  **−16.3 bp/day** among size portfolios and **−13.7 bp/day** among book-to-market portfolios during
  the session; the size high-beta portfolios show a night-minus-day spread of **+27.3 bp**.

**This is a direct external corroboration of the programme's reported volatility inversion** — *"low
volatility names accruing their drift INTRADAY while high-volatility names accrued it overnight."*
That is precisely `IVOL`'s published decomposition, on US stocks 1993–2013 (LPS) and 1986–2015
(Bogousslavsky), and the beta version of it on 1992–2016 (HLR). **The internal finding is not an
artefact of the programme's sample; it is a thirty-year stylised fact with three independent
measurements.** It is also the reason to distrust any single-sample reading of the programme's own
split: the split is a function of the volatility of the names held, and the names held change.

### 2.4 One correction to a claim a search summariser made, because the lane rules require it

A WebSearch summariser told me the Lou–Polk–Skouras (2022) working paper *"The Day Destroys the Night,
Night Extends the Day"* decomposes `SMB`, `HML`, `RMW` and `CMA` into overnight and intraday
components. **It does not.** I downloaded the paper (`personal.lse.ac.uk/polk/research/LouPolkSkouras.pdf`,
`HTTP 200`, `1,417,614` bytes, April 2022 version) and read it: it decomposes the **market** return,
and then uses the smoothed past **overnight market return** as a *conditioning variable for market
betas*. The `84%` alpha reduction is a conditional-CAPM result, not a session decomposition of the
four factors. `HML` appears three times in the whole paper, twice as a control in a factor regression.
**A figure from a summariser is weaker than a snippet, and this one was a different claim entirely.**

Two further summariser slips logged: one result block said Bogousslavsky (2021) was *"published in the
Journal of Finance in 2021"* (it is the Journal of Financial Economics), and another said LPS (2019)
decomposed *"19 well-known anomaly variables"* (the paper says 14 strategies, and I counted 14 rows
in Table 2).

---

## 3. Q3 — THE MECHANISMS, AND WHETHER ANY COULD APPLY TO A POSITION HELD THREE TO SIX MONTHS

**This is the analytical heart, and the test I apply to each mechanism is explicit: does the mechanism
change the TOTAL return earned by an investor who buys once and holds for months, or does it only
relabel which session that investor's return is booked in?** A mechanism that only relabels is
descriptive. Only a mechanism that pays the *holder*, every night, for something the holder is
actually doing, can give a months-held position an overnight-tilted premium.

### 3.1 Retail order flow concentrating at the open

**Evidence.** Berkman, Koch, Tuttle & Zhang, *"Paying Attention: Overnight Returns and the Hidden Cost
of Buying at the Open"*, **JFQA 47(4):715–741, 2012** `[PEER-REVIEWED] [abstract/snippet only — the
Cambridge PDF URL is gated, §8]`: attention-generating events on one day produce higher individual-investor
demand **concentrated near the next open**, creating temporary price pressure at the open, elevated
overnight returns, and **reversal during the trading day**. Aboody, Even-Tov, Lehavy & Trueman, *"Overnight
Returns and Firm-Specific Investor Sentiment"*, **JFQA 53(2):485–505, 2018** `[PEER-REVIEWED] [first
page read in full; rest skimmed]` (UCLA copy, `HTTP 200`, `265,405` bytes, journal header verified)
supports using overnight returns as a firm-specific sentiment proxy and finds *"stocks with high (low)
overnight returns underperform (outperform) over the longer term."* LPS confirm the flow pattern in
TAQ directly: **small orders (below `$5,000`) cluster near the open, large orders (above `$50,000`)
after the open and at the close** (their Fig. 3, 1993–2000).

**Does it apply to a three-to-six-month hold?** **No, for P&L; yes, for accounting.** The buyer at the
open pays the pressure and the intraday reversal takes it back. A holder who does not transact at the
open neither pays nor receives it: the pressure raises the overnight return and lowers the following
intraday return by the same amount, and the holder collects the sum. **It determines where the return
is booked, not how much there is.** This mechanism is intrinsically a one-day round trip. It is,
however, an excellent explanation of *why* the split exists at all — and therefore of why the split is
descriptive.

**One counterweight worth recording.** Glasserman et al. observe: *"This explanation becomes less
plausible when the opening price is set by European traders in S&P 500 futures, as these are less
likely to be retail investors"* — Bondarenko and Muravyev locate the market-level overnight return in
the four hours around the European open, where retail is not the marginal participant.

### 3.2 Institutional execution concentrating at the close, and the closing auction's growth

**Evidence, primary and verified.** Bogousslavsky & Muravyev, *"Who Trades at the Close? Implications
for Price Discovery and Liquidity"*, working paper 2 June 2021 (published J. Financial Markets 2023)
`[WORKING PAPER] [read in full]` — `static1.squarespace.com/.../who-trades-at-the-close_June2021.pdf`,
`HTTP 200`, `764,193` bytes, title page verified, 61 pages:

- **The auction accounted for `7.48%` of aggregate daily dollar volume in 2018, up from `3.11%` in 2010**
  — and Smith (2006) put it at `0.49%` just after NASDAQ introduced a closing auction in 2004. Growth
  is attributed by difference-in-difference to **indexing and ETFs**.
- *"Despite massive volumes, closing prices match the pre-close bid or ask prices in 68% of cases."*
  Mean absolute auction price deviation `8.1 bp`, of which the mean half-spread is `7.56 bp` and price
  impact only `0.55 bp`. Deviations *"mostly revert overnight"*; only `19%` of the last-five-minute
  return reverses next morning.
- **And a fact with era consequences: *"the increase in auction volume coincides with a decrease in
  liquidity at the open."*** §6.3.
- Incidentally, a cross-check the programme may find useful: mean closing-auction half-spread in the
  **lowest size quintile** (`$5`+, `$100m`+, 2010–2018) is **`22.19 bp`**, i.e. `~44 bp` round trip —
  in the same region as the programme's measured `33.8 bp`/side. Context only; retail execution cost
  and the `15:50` cut-off are established ground and I did not research them.

**Related, and it explains Bogousslavsky's last-half-hour column.** Baltussen, Da & Soebhag,
*"End-of-Day Reversal"*, April 2025 `[WORKING PAPER] [read in full]` (`www3.nd.edu/~zda/EOD.pdf`,
`HTTP 200`, `526,613` bytes; authors disclose Northern Trust AM and Robeco affiliations, and the paper
states the views are not necessarily those of either firm). Individual stocks reverse sharply in the
last 30 minutes; the effect is *"present in almost every 3-year rolling window"*, is stronger
equal-weighted (`6.38 bp/day`, `t = 17.30`), comes *"primarily… from positive price pressure on
intraday losers"*, and is attributed to **attention-induced retail 'buy-the-dip' purchases plus a
documented drop in new short positions before the close** — the latter because *"risk or capital
requirements tend to increase overnight."*

**Does it apply to a three-to-six-month hold?** **No, except through the rebalance price.** A
concentration of uninformed institutional volume at the close, with deviations that revert overnight,
is a transaction-timing fact. For a holder it relabels sessions; for a rebalancer it is an execution
question — and execution at the close is **established ground for this programme (the `15:50` auction
cut-off), to be cited rather than re-researched.** The only genuinely new content here for a
months-held book is the negative one: **the auction's deviations revert, so a book that transacts at
the close is not systematically harmed or helped by the auction's growth beyond the half-spread it
already measures.**

### 3.3 Overnight inventory risk — THE ONLY MECHANISM WITH A LONG-HOLD-COMPATIBLE STRUCTURE

**Evidence.** Boyarchenko, Larsen & Whelan, *"The Overnight Drift"*, **Review of Financial Studies
36(9):3502–3547, September 2023** (NY Fed Staff Report 917, Feb 2020, rev. Aug 2022)
`[PEER-REVIEWED + OFFICIAL WORKING PAPER] [staff report downloaded and title verified; blog read in
full; the RFS article itself not opened]`. The mechanism, in the authors' own July 2026 restatement:
liquidity providers absorb the residual one-sided order flow in the final hour of US trading, carry
that inventory overnight at risk in a thin market, demand a discount at the close to do so, and earn
the discount back as overseas buyers arrive at the Frankfurt and London open. In equilibrium

> `E[R_ON] = (dollar order imbalance)_t × (return variance)_t × (risk-bearing capacity)^(−1)`.

Bogousslavsky's own stated mechanism is the mirror image on the arbitrageur side: **margin requirements
are higher overnight and lending fees are charged only on positions held overnight**, so arbitrageurs
reduce positions before the close.

**Does it apply to a three-to-six-month hold?** **Structurally, yes — and this is the only mechanism
of the five for which the answer is yes.** It is a *compensation paid every night to whoever is
holding*, not a price-pressure round trip. A buy-and-hold investor is, every single night, one of the
parties bearing overnight risk, and under this mechanism is compensated for it. **That is a level
effect a months-held position genuinely collects.**

**But three things kill it as a route to a characteristic premium, and they should be stated together.**

1. **It is characteristic-NEUTRAL.** It compensates inventory and overnight risk, not profitability.
   It predicts a positive overnight return for *everything* held overnight, scaled by volatility — which
   is why its cross-sectional signature is `IVOL` and `BETA`, exactly the two characteristics whose
   overnight components are large, and **not** `GP`, `BM` or `NI`, whose long-leg overnight alphas are
   zero. Table IA.2 is the test and the mechanism fails it for slow characteristics.
2. **Glasserman et al. show it cannot be the whole story**, in their §5.4: *"Inventory management ties
   over-intra outperformance to one-day reversals from intraday to overnight returns. It does not
   explain continuation of returns separately in the intraday and overnight periods… and it is silent
   on the poor performance of intraday returns."* They separate stocks selected by the inventory-management
   signal (lowest intraday returns on day `s`) from their news-based picks and find both effects survive
   the other's removal.
3. **The authors themselves now report it has gone to zero.** §5.2.

### 3.4 News arriving outside trading hours — the one mechanism with demonstrated multi-month persistence

**Evidence.** Glasserman, Krstovski, Laliberte & Mamaysky (2025) `[WORKING PAPER] [read in full]`.
**2.4 million Thomson Reuters articles, 1996–2022, S&P 500 firms (887 names), of which approximately
two-thirds are overnight-stamped** (after the 4pm close, before the 9:30am open; weekends and holidays
count as overnight for the next trading day). Using supervised topic analysis they find that **both**
the differing *prevalence* of topics across the two periods **and** the differing *market response* to
the same topic across the two periods contribute to the over-intra gap, with the response difference
mattering more. Their characteristics-adjusted baseline puts intraday minus overnight at
**`−3.6 bp/day`** over 2001–2022 (controls follow Green, Hand & Zhang 2017, including size,
book-to-market, investment, profitability and 12-month momentum), and *"the over-intra outperformance
phenomenon is mostly eliminated once we remove our news-based picks."*

**Does it apply to a three-to-six-month hold?** **This is the one where the answer is genuinely
interesting.** Pure news *arrival* outside hours is a variance fact, not a premium — unbiased news
adds variance to the overnight bucket without adding expected return. But Glasserman et al.'s result is
not an arrival result: it is a *differential-response* result, and **their forecasts are formed from
four years of past news and predict a full year ahead**, with out-of-sample validation using a 2010
topic model applied to 2011–2022 returns. **Topic exposures are persistent at multi-year horizons.**
So this is the only mechanism in the literature whose own evidence operates on a horizon compatible
with a three-to-six-month hold.

**Three reasons it still does not help here.** (i) The conditioning variable is a **news-exposure
characteristic**, not profitability — it is a different signal, and it is `[SALES INSTRUMENT]`-free
but also `[NOT COMPUTABLE]` from the programme's permitted data, which has no news text feed.
(ii) Their universe is **S&P 500 members only**. (iii) The authors themselves disclaim tradability:
*"Because of the extreme turnover required to trade the over-intra effect, our findings fall short of
being a viable trading strategy."*

### 3.5 Arbitrageur overnight-holding costs — and the long-only asymmetry

Bogousslavsky's abstract mechanism (margin higher overnight; lending fees charged only on overnight
positions) is the one that most directly explains his last-half-hour column: the mispricing factor
*"earns positive returns throughout the day but performs poorly at the end of the day."* **Its
prediction is leg-asymmetric, and Table IA.2 confirms the asymmetry.** Arbitrageurs unwinding before
the close are overwhelmingly unwinding *shorts* — that is where the margin and the lending fee bite.
So the overnight component should sit in the short leg, and it does: `+1.49 bp/night` for high
issuance, `+3.79 bp/night` for high IVOL, against `+0.09` and `−1.27` for the long legs.

**For a long-only book that never shorts, never posts overnight margin beyond the position itself,
and never unwinds before the close, this mechanism predicts nothing.** That is a clean negative
result, and it is consistent with the long legs' zero overnight alphas. It is also the reason I would
weight Bogousslavsky's long-leg table above every long–short number in this brief for this
programme's purposes.

### 3.6 One mechanism I could not verify

A settlement-convention explanation (the `T+1` / overnight-financing channel) appears in the
literature on China's `T+1` rule and is occasionally invoked for the US. **I found no US-settlement-based
explanation I could verify in a primary source and I am not asserting one.** Listed in §8.

### 3.7 Mechanism verdict table

| mechanism | pays the months-long HOLDER? | characteristic-specific? | verdict for a 3–6 month characteristic book |
|---|---|---|---|
| Retail flow at the open | no — relabels sessions | no | **descriptive only** |
| Institutional execution / closing auction | no — relabels; matters at rebalance | no | **execution question, established ground** |
| Overnight inventory risk | **yes, structurally** | **no — it is a volatility/inventory premium** | **wrong object, and now zero (§5.2)** |
| Overnight news arrival & response | partly — persistent exposures | yes, but to a NEWS characteristic | **not computable here** |
| Arbitrageur overnight holding costs | **no — short-leg only** | yes, but in the leg not held | **predicts nothing for long-only** |

**The synthesis: not one of the five mechanisms in the literature would give a long-only,
months-held profitability book an overnight-tilted premium.** The only one that pays holders is
characteristic-neutral and now measures zero; the only one with multi-month persistence keys on news
exposure; the rest are one-day price-pressure round trips that relabel sessions without changing the
holder's total.

---

## 4. Q4 — STABILITY ACROSS ERAS AND ACROSS THE CROSS-SECTION

**The lane instructed me to treat era-dependence as the default hypothesis to be disproved. It is not
disproved. Every source that looks finds instability, and in one case the original authors have
withdrawn the magnitude of their own headline.**

### 4.1 Era instability at the market level, from the authors of the decomposition

**LPS (2022)** `[WORKING PAPER] [read in full]`, abstract verbatim: *"while the Tech boom and Covid
crash/rebound were primarily driven by overnight returns, the Global Financial Crisis was mostly an
intraday phenomenon."* In the body: *"The majority of the Covid crash and rebound comes overnight…
[the GFC] was much more of an intraday phenomenon… As far back as 1997, intraday returns were flat at
best and then became slowly negative. In contrast, the striking rise in valuations in this episode is
entirely driven by overnight returns."* **The same decomposition, on the same index, flips which session
carries the move depending on which crisis you pick.**

### 4.2 The overnight drift has gone to zero since 2021 — the single most important era finding

**[OFFICIAL BLOG OF A FEDERAL RESERVE BANK, BY THE ORIGINAL AUTHORS] [read in full]** — Nina
Boyarchenko, Lars C. Larsen and Paul Whelan, *"The Disappearing Overnight Drift"*, Liberty Street
Economics, **1 July 2026**. Fetched `HTTP 200`, `174,242` bytes, `text/html`; `<title>` verified as
*"The Disappearing Overnight Drift - Liberty Street Economics"*; stripped and read locally.

> *"Five additional years of data later, that pattern appears to have faded: the 2:00–3:00 window that
> previously generated roughly 3.7 percent per annum has averaged close to zero since 2021."*

- Original sample: S&P 500 E-mini futures **1998–2020, 5,691 trading days**; the 2:00–3:00am ET window
  was *"previously responsible for more than 60 percent of the contract's 5.9 percent annualized
  close-to-close return."*
- Post-publication sample: **January 2021 – December 2025, 1,245 trading days** — the window *"is
  flat."* *"The same pattern holds in the E-mini Nasdaq-100 (NQ) and E-mini Dow Jones (YM) contracts."*
- Channel attribution: the standard deviation of end-of-day relative signed volume (15:15–16:15 ET)
  **fell from `6.5%` to `2.9%`** — *"a compression of more than half"* — while the other two channels
  barely moved (VIX mean `20.4` → `19.4`, median `18.6` → `18.2`; overnight share of E-mini volume
  `15%` → `16%`). *"The Order-Imbalance–Overnight-Return Relationship Has Broken Down."*
- And a real-money datum: **NightShares launched NSPY and NIWM in June 2022 to capture overnight
  equity returns, citing this very inventory-risk mechanism in the prospectus; both closed fourteen
  months later**, which the authors call *"consistent with the weakened pattern over this sample
  (though ETF-specific costs likely also contributed)."*
- Their falsifiable prediction, quoted: *"if order-imbalance dispersion widens back toward its pre-2020
  range, the overnight drift should reappear in the same 2:00–3:00 window."*

**This corroborates the programme's own reported era inversion, in the same direction and over the same
break.** The programme reports a full-sample intraday drift of `−0.33%` becoming `+1.44%` excluding
2020 and `+3.05%` from 2021 onward. The NY Fed authors report the overnight component going to zero
from 2021. **An overnight component that dies is arithmetically an intraday component that appears.**
These are different objects — US single names versus S&P 500 E-mini futures, and a book versus an
index — and I am not claiming the same measurement. But **the programme's most era-suspicious internal
number has an independent, published, mechanism-attributed analogue, and the programme should stop
treating it as an anomaly of its own sample.**

### 4.3 Era instability in the characteristic decomposition itself

- **Bogousslavsky (2021), abstract verbatim** `[abstract only]`: the end-of-day mispricing pattern
  *"strengthens in the second half of the sample and is shared by several well-known anomalies."*
  So the half-hour location of the anomaly returns is itself non-stationary — and strengthening, not
  decaying, on 1986–2015.
- **LPS (2019) make time-variation their central time-series claim.** Their `TugOfWar` variable — the
  smoothed past overnight-minus-intraday spread of a strategy — *forecasts that strategy's subsequent
  close-to-close return*, positively for the overnight strategies and negatively for the intraday ones
  (*"size, book-to-market, profitability, investment, beta, idiosyncratic volatility, issuance activity,
  accruals, and turnover"*), with *"a one-standard-deviation increase in TugOfWar forecast[ing] a 1%
  higher close-to-close strategy return, or about 18% of its monthly return volatility."* **The whole
  construction presupposes that the split varies materially through time.** A paper whose main
  time-series result is that the split's variation predicts future returns is not a paper claiming a
  stable split.
- **I searched specifically for subperiod tables in LPS (2019) and found none** — no occurrence of
  "subperiod", "sub-period", "first half" or "second half" anywhere in the extracted text. **Their
  Table 2 figures are full-sample 1993–2013 only.** That is a real gap: *the headline characteristic
  decomposition has never been published split by era.*

### 4.4 One thing that IS stable, recorded because the lane asked for both directions

Baltussen, Da & Soebhag report their end-of-day reversal is *"present in almost every 3-year rolling
window"* and *"significant in various stock subsamples (small vs. large stocks; liquid vs. illiquid
stocks; high- vs. low-volatility stocks; over- vs. under-priced stocks)"*, with slope coefficients in
3-year rolling panel regressions *"almost always negative… and often significant, even in the later
years of our sample."* **So the last-half-hour reversal is stable while the overnight drift is not.**
That is evidence that "the intraday split" is not one phenomenon with one stability property — the
close behaves differently from the night.

### 4.5 Cross-sectional instability, which is the same point as §2.3

The split's sign flips across the cross-section as a matter of published record, not merely in the
programme's sample: high-beta and high-IVOL names earn overnight and lose intraday; low-beta and
low-IVOL names the reverse (LPS, Bogousslavsky, HLR). **So "is the premium overnight?" has no
sample-independent answer — it depends on the volatility of the names held, and a universe whose
volatility composition drifts will show a drifting split for that reason alone.** This is, I think,
the cleanest available explanation of why the programme's own decomposition inverts by volatility, and
it implies the era inversion could be partly a composition effect rather than a change in the world.
**I did not test that and am not asserting it.**

---

## 5. Q5 — THE OPERATIONAL CONSEQUENCE: ACTIONABLE OR DESCRIPTIVE?

### 5.1 The arithmetic identity, stated first because everything else follows from it

For a position held continuously across both sessions,
`(1 + r_overnight)(1 + r_intraday) = (1 + r_close-to-close)` — which is exactly how every paper here
constructs the decomposition (LPS (2022) print the identity; LPS (2019) *impute* the overnight return
from the intraday return and the close-to-close return). **The two components are not two returns the
holder can choose between. They are a partition of one return.** A premium that accrues overnight is
not separately capturable by a buy-and-hold position; **it is simply where the return happened.**

**So the distinction is DESCRIPTIVE for a long-hold book, and that is this lane's most important
finding.** It becomes actionable only through three specific doors, and all three are shut or closed
elsewhere.

### 5.2 Door 1 — hold in one session, be flat in the other. Priced, and it fails by ~38×

**[MEASURED IN BRIEF]** — my own arithmetic, combining Bogousslavsky's published long-leg interval
alphas with the programme's stated round-trip cost. **Every transcribed input and every sum in this
brief is re-runnable from [`data/B3_session_interval_sums.py`](../../../data/B3_session_interval_sums.py)
with its output at [`data/B3_session_interval_sums.txt`](../../../data/B3_session_interval_sums.txt)**;
the script's literals are the per-interval values as printed in Bogousslavsky's Internet Appendix
Tables IA.2, IA.6 and IA.7, so a transcription error is auditable against the appendix.

- Gross profitability's **long leg** earns **`+1.77 bp/day` intraday alpha** (sum of 13 printed
  interval alphas) and **`+0.07 bp/day` overnight**.
- Isolating the intraday component requires buying at the open and selling at the close **every trading
  day**: `21` round trips a month at the programme's stated `~67.6 bp` round trip = **`1,420 bp/month`
  of cost** against **`37 bp/month` of gross intraday alpha**. **Short by `38.2×`.** One round trip
  costs `38×` one day of the alpha it would isolate.
- The same arithmetic on LPS's long–short `ROE`: `142 bp/month` intraday against `1,420 bp/month` of
  daily round trips. **Short by `10.0×`.** (Note that this is the same order-of-ten shortfall `A2`
  reported for a ten-bar hold from an entirely different direction, which is a coincidence of scale
  and not a corroboration of anything.)

**Independent confirmation from the authors.** Glasserman et al.: *"Because of the extreme turnover
required to trade the over-intra effect, our findings fall short of being a viable trading strategy."*
HLR, on the beta version: *"implementing various BaB strategies would require significant trading in
high-beta stocks at the open and close of each day. This could significantly diminish or even eliminate
the strategies positive returns."* And the real-money datum: **NightShares' two overnight ETFs closed
fourteen months after launch.**

**A conflict to record.** Lachance, *"Night trading: Lower risk but higher returns?"*, **Review of
Financial Economics 41(4):347–363, 2023** `[PEER-REVIEWED] [abstract only, quoted verbatim from RePEc;
the Wiley full text returned `HTTP 403` behind a Cloudflare interstitial]`: *"This model identifies
one-fifth of stocks as having positive and statistically significant overnight biases. Investing
overnight in these stocks in the next year yields twice the market's return for a third of the market
beta… Implementation costs and issues are discussed."* **So one peer-reviewed source holds that a
selected overnight-only book is worthwhile**, against Glasserman et al.'s and HLR's statements that
the turnover is prohibitive. I would weight the negative side for this programme — Lachance's object
is a *selected fifth of stocks* chosen on past overnight return, which is the overnight analogue of a
past-return signal and therefore closer to momentum/reversal (excluded ground) than to a characteristic
premium; and I have not read her cost treatment. **But both readings stand and I discard neither.**

### 5.3 Door 2 — the rebalance execution price. Established ground, cited not researched

If the premium concentrates in a session, the price at which a monthly rebalance transacts matters. That
is the retail-execution-cost and `15:50`-auction-cut-off territory the exclusion list marks as
established. **I cite it and stop.** The only new input I would offer is Bogousslavsky & Muravyev's
finding that closing-auction price deviations *"mostly revert overnight"* and average `8.1 bp` of which
`7.56 bp` is half-spread and `0.55 bp` is price impact — i.e. **the auction is close to a
half-spread-only venue at the programme's size, and its deviations are not a persistent tax.**

### 5.4 Door 3 — risk rather than return

The overnight component is much less volatile than the close-to-close one. LPS: momentum's overnight
return has a `4.02%` standard deviation against `7.85%` close-to-close, giving an overnight Sharpe of
`0.77` monthly against `0.31` close-to-close (HLR restate this as an annualised `2.67`). Lachance's
abstract: *twice the market's return for a third of the market beta.* **So a session-separated position
has a genuinely better risk profile** — which is why this door keeps getting opened in the literature.
**But it is the same door as Door 1:** realising the better Sharpe requires the daily round trip that
costs `38×` the alpha. For a book that holds continuously, the sessions' variances simply add and there
is nothing to choose.

### 5.5 The honest summary of Q5

**DESCRIPTIVE, not actionable, for a book that holds across both sessions continuously for months.**
Knowing that a profitability premium accrues intraday would not change a single position, a single
weight, or a single rebalance decision in a monthly-rebalanced long-only book. It would change exactly
two things, both diagnostic rather than operational:

1. **It would tell the programme that its overnight edge is a property of its market exposure, not of
   its characteristic tilt** — §0.2. That is worth knowing because it changes what the overnight
   finding can be used to argue for. It cannot be used to argue that a characteristic book inherits it.
2. **It would make the era and volatility inversions interpretable rather than alarming** — §4.2,
   §4.5 — because the published literature shows the same inversions in the same directions.

---

## 6. Q6 — THE MEASUREMENT PROBLEMS

### 6.1 Where the boundary is drawn moves the answer, and sometimes its sign

**No two papers here draw the open-price boundary in the same place, and the differences are large.**

| source | "open" price used | what the `OV` bucket therefore contains |
|---|---|---|
| LPS (2019, 2022) | **VWAP over 9:30–10:00am** from TAQ, *"to ensure that our open prices are robust"*; observations with `< 1,000` shares in the first half hour excluded | the opening auction **plus the entire first half hour of continuous trading** |
| Bogousslavsky (2021) main tables | **quote midpoint**, first interval starting **9:45am** | the opening auction plus the first fifteen minutes |
| Bogousslavsky Table IA.7 | **first trade of the day** | the opening auction only; a separate 9:30 bucket appears |
| HLR (2020) | **CRSP open price** (sample starts 1992 for this reason) | the opening auction |
| Glasserman et al. (2025) | **CRSP open and close** | the opening auction |

**And the sensitivity is measurable from Bogousslavsky's own appendix.** Moving from quote midpoints
with a 9:45 boundary (IA.6, `$10`) to trade prices with a 9:30 boundary (IA.7, `$5`):

- the **mispricing factor's overnight alpha flips sign**, from **`+1.49 bp` (`t = 2.69`) to
  `−2.20 bp` (`t = −4.39`)**;
- the **size premium's overnight alpha** goes from **`−1.10 bp` (`t = −3.15`) to `+0.04 bp`
  (`t = 0.11`, insignificant)**, while its last-half-hour alpha rises from `+2.91` to `+5.19 bp`;
- gross profitability's overnight alpha moves from `−0.09` (insignificant) to **`−1.69 bp`
  (`t = −3.82`)** — same sign as before but now strongly significant.

Part of that is the `$5`-versus-`$10` filter and part is the price convention, and **the appendix does
not separate them.** The honest statement: **the session split of an anomaly is sensitive to the
opening-boundary convention at the same order of magnitude as the effect itself, and at least one
anomaly's overnight sign depends on the convention chosen.** Bogousslavsky's own defence is Table IA.8,
which he says shows *"the patterns in Tables 1 and 7 in the main text do not appear to be driven by
nonsynchronous trading"*, and LPS report robustness to CRSP opens, first TAQ trades and opening
midquotes — but with *"results available upon request"*, i.e. **not shown.**

### 6.2 Bid-ask bounce, and the two defences used against it

Bogousslavsky computes returns from **quote midpoints**, which removes bid-ask bounce by construction;
his trade-based table is the robustness check, not the baseline. LPS use a **volume-weighted average
price over thirty minutes** rather than a single print, explicitly *"to ensure that our open prices are
robust"*, and drop days with fewer than 1,000 shares in that window. Both papers also apply a `$5`
floor, and LPS additionally drop the bottom NYSE size quintile — which is a bid-ask-bounce defence as
much as an economic one. **The cost of those defences is that none of the published decompositions
speaks to low-priced or microcap names**, §1.5.

### 6.3 The artefact question the lane asked: is the split an artefact of where the closing and opening prices are struck?

**Four pieces of evidence, pointing in different directions. All recorded.**

1. **For the artefact reading.** Cliff, Cooper & Gulen `[snippet only — I could not open the paper,
   §8]`: the night/day effect *"is driven in part by high opening prices which subsequently decline in
   the first hour of trading."* Berkman et al. (2012) formalise exactly that: temporary retail price
   pressure at the open, reversed during the day. **If the opening print is systematically struck high,
   the overnight bucket is systematically overstated and the intraday bucket understated, with no
   economic content.**
2. **Against the artefact reading, at the market level.** Bondarenko & Muravyev locate the market's
   entire average return in the four hours around the **European open** in continuously-traded E-mini
   futures, where there is no US opening auction to be struck at all, and Boyarchenko et al. localise
   it to 2:00–3:00am ET. **A pattern in a 24-hour futures contract cannot be an artefact of the US
   opening print.**
3. **A documented non-stationarity in the open itself.** Bogousslavsky & Muravyev: *"the increase in
   auction volume coincides with a decrease in liquidity at the open."* **The quality of the very price
   every one of these decompositions depends on has deteriorated over the sample period in which the
   decomposition is measured.** That is a joint Q4–Q6 problem and I did not find anyone who addresses
   it.
4. **A corporate-action convention that is stated and systematic.** LPS: *"we assume that dividend
   adjustments, share splits, and other corporate events that could mechanically move prices take place
   overnight."* Glasserman et al.: *"Dividends are paid to the owner of the shares at the close, so we
   include them in close-to-open returns. We also assume that all stock splits and buybacks take effect
   at the close."* **So the market's entire dividend yield — on the order of 2%/yr — is assigned to the
   overnight bucket by construction in the market-level results.** Against a market-level overnight/intraday
   gap of `7.2%/yr` (Glasserman et al.) that is a material fraction, though not the whole.

   **And here is an inference of my own, marked as mine and not as any paper's claim
   [MY INFERENCE — NOT IN ANY SOURCE]:** the same convention *strengthens* the slow-characteristic
   result rather than weakening it. High-book-to-market and high-profitability firms pay higher
   dividends than their low counterparts, so assigning dividends to the overnight bucket biases
   `HML`'s and `ROE`'s **overnight** components **upward**. They still come out at `−0.10%` and
   `−0.95%` per month. **The convention works against the finding, so the finding is conservative with
   respect to it.** I have not quantified the dividend-yield differential between the legs and this is
   a direction-of-bias argument only.
5. **One fringe reading, quoted and flagged rather than weighted.** Knuteson, *"Strikingly Suspicious
   Overnight and Intraday Returns"*, arXiv:2010.01727, 4 pages `[WORKING PAPER / ADVOCACY] [read in
   full]`, argues the pattern admits no *"plausible innocuous explanation"* and advances a
   market-manipulation account. **I record its existence because the lane asked whether the split is an
   artefact and this is the literature's loudest "no"; I place no weight on its conclusion and it
   supplies no decomposition figures for any characteristic.**

---

## 7. WHAT THIS MEANS FOR THE PROGRAMME'S ABILITY TO MEASURE IT AT ALL

The lane flagged that the programme's intraday fixture covers a subset of names and **its intraday
vendor serves no delisted ticker, leaving ~41.6% of one cohort unreachable.** That interacts with this
lane's findings in a way that is worth stating plainly, because it is more binding than the literature
gap.

1. **The published samples are CRSP-based and therefore dead-inclusive.** LPS, HLR and Glasserman all
   draw from CRSP, which retains delisted names; Bogousslavsky draws from TAQ plus CRSP over 1986–2015.
   **The programme's intraday route is not dead-inclusive.** A decomposition measured on the
   intraday-reachable subset is measured on survivors.
2. **The direction of that bias is not neutral here, and §2.3 says why.** The overnight component is
   largest in magnitude among **illiquid, small, high-volatility** names — and those are precisely the
   characteristics correlated with delisting. **Dropping ~41.6% of a cohort drops disproportionately
   the names whose session split is most extreme.** So the survivor subsample would understate the
   cross-sectional dispersion of the split and could plausibly get its sign wrong for the universe as
   a whole. This is the same failure mode as the inherited lesson that a null must live in the
   tradeable universe.
3. **The `$5` floor is NOT the problem here, for once.** Bogousslavsky's main tables use a `$5` floor
   and a `$100m` market-cap floor; the programme's floor is `$5` plus a trailing dollar-volume screen.
   Those are close enough that the literature's universe is a reasonable, if larger-cap, analogue. The
   binding differences are **equal versus value weighting** and **dead-inclusion**, not the price
   floor.
4. **So the original measurement available to the programme is narrower than it looks.** Equal-weighted
   and long-only are genuinely open; post-2015 is genuinely open; **dead-inclusive is not achievable
   with the data described, and it is the axis that matters most.** A brief that reported an
   equal-weighted long-only split on survivors only would be reporting a composition effect with a
   session label on it.

---

## 8. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **Bogousslavsky (2021)'s main text.** I have the verbatim abstract (from RePEc) and the full
   Internet Appendix (the author's own posted PDF, read in full). I do **not** have the main text, so
   **Table 1 (the `$5`-filter baseline) and Table 7 are unseen by me**, and every figure I attribute to
   this paper comes from the Internet Appendix or the abstract, both labelled as such at the point of
   use. Blocks: SSRN `Delivery.cfm` → `HTTP 403`, body a 5,810-byte Cloudflare *"Just a moment…"* HTML
   page, not a PDF [tool: `curl`]. OpenAlex reports `oa_status: closed`, `any_repository_has_fulltext:
   false` for DOI `10.1016/j.jfineco.2020.07.020`. The author's own page posts no main-text PDF.
2. **The intraday sums I report for Bogousslavsky are mine, not his.** Every `Σ intraday` figure in
   §1.2, §1.3 and §5.2 is **my arithmetic sum of his 13 printed per-interval alphas**
   `[MEASURED IN BRIEF]`, re-runnable from `data/B3_session_interval_sums.py` with its output checked
   in at `data/B3_session_interval_sums.txt`. He does not print an intraday total. **A sum
   of intervals is not the same object as a compounded open-to-close return**, and it ignores any
   interval he does not print. The `OV` figures and all `t`-statistics are his, as printed.
3. **Cliff, Cooper & Gulen (2008).** The `+2.82 to +4.76 bp` night and `−2.85 to +0.22 bp` day figures
   for S&P 500 stocks are **`[snippet only]` — I did not open the paper.** Block: the free copy at
   `assets.super.so` returned `HTTP 403` with a 263-byte `application/xml` `AccessDenied` body [tool:
   `curl`]; SSRN is Cloudflare-blocked as above. **And the sample period is disputed in my own sources:**
   the snippet says 1993–2006; Glasserman et al., who cite the paper, say **1993–2003**. I did not
   resolve which is right and the figures should be treated as approximate with an uncertain end date.
4. **Berkman, Koch, Tuttle & Zhang (2012).** `[abstract/snippet only]`. Block: the Cambridge Core URL
   ending `.pdf` returned **`HTTP 200` with `content-type: text/html`** and a body beginning `<!DOC`,
   i.e. a OneTrust consent-gated landing page, not the PDF — **a fresh instance of the programme's
   "an HTTP 200 can be wrong" catalogue, caught by inspecting bytes rather than status.** I did not
   accept the consent banner (out of scope for this campaign's rules), so I have no figures from this
   paper beyond the mechanism description.
5. **Lachance (2023).** `[abstract only]`, quoted verbatim from the RePEc record. Block: Wiley
   `onlinelibrary.wiley.com/doi/full/10.1002/rfe.1180` → `HTTP 403`, 5,617-byte Cloudflare
   *"Just a moment…"* body [tool: `curl`]. **I have not read her implementation-cost treatment**, which
   is exactly the part that conflicts with §5.2, so that conflict is recorded with one side unread.
6. **Boyarchenko, Larsen & Whelan's RFS article itself.** I read their **July 2026 Liberty Street
   Economics post in full** and downloaded NY Fed Staff Report 917 (`HTTP 200`, `3,881,868` bytes,
   title page verified) but **did not read the staff report or the RFS version through.** The
   `3.7%/yr`, `5.9%` close-to-close, `>60%`, `6.5% → 2.9%`, VIX and volume-share figures are all from
   the blog post, which is by the same three authors.
7. **Kelly & Clark (2011)** in the Journal of Asset Management is `[UNVERIFIED]` — I cite it only as
   *cited by Glasserman et al.* and opened nothing.
8. **The Alpha Architect post titled "Trading Costs Wipe Out the Overnight Return Anomaly"** could not
   be retrieved and **I never identified which paper it summarises.** Blocks: WebFetch → `HTTP 403
   Forbidden`; `curl` with a browser user-agent → `HTTP 403`, 5,884-byte Cloudflare JS interstitial.
   It is a practitioner asset-manager blog and would have been `[SALES INSTRUMENT]` in any case, but
   **it may point at a cost paper I have therefore missed**, and my §5.2 conclusion would be
   strengthened or complicated by it.
9. **No era-split of the characteristic decomposition exists that I could find.** I searched
   specifically for a replication or extension of LPS (2019) or Bogousslavsky (2021) into 2016–2026 and
   for subperiod tables inside them, and found neither. **So §4's era case rests on (i) LPS (2022)'s
   market-level episode inversions, (ii) Bogousslavsky's one-sentence abstract claim that the pattern
   strengthens in the second half, (iii) LPS (2019)'s `TugOfWar` construction presupposing time
   variation, and (iv) the NY Fed futures result. None of those is a subperiod table for a
   profitability premium's session split. That table does not exist in public, and its absence is the
   one place where the lane's "confirmed absence" bar is met.**
10. **Lu, Malliaris & Qin (2023, JFE 148(3):175–200), *"Heterogeneous liquidity providers and
    night-minus-day return predictability"*, is `[UNVERIFIED]`.** It is the formal model of exactly my
    §3 question — why characteristics-sorted portfolios earn opposite-signed overnight and intraday
    returns — and **I did not open it.** The author's site linked a Google Drive file that turned out
    to be a different paper, and the SSRN abstract pages are Cloudflare-blocked. **This is the single
    most significant gap in §3**, and the mechanism verdict table should be read as provisional on it.
11. **A settlement/`T+1` explanation for the US overnight premium** is sometimes invoked and I found
    no primary source I could verify. §3.6. I assert nothing about it.
12. **I read extracted text, never images.** LPS (2022)'s Figures 4–6 (Covid, GFC, NASDAQ bubble
    cumulative overnight versus intraday lines), the Liberty Street charts, and Bogousslavsky's Figures
    IA.1–IA.6 were established **from the captions and prose only.** I quote no number that appears
    only in a plot. Where a paper's claim rests on a figure — the LPS (2022) era inversions and the
    Boyarchenko 2021–25 flatness — I have quoted the authors' words about the figure rather than read
    the figure.
13. **`[MY INFERENCE — NOT IN ANY SOURCE]` is used once**, in §6.3(4), for the argument that the
    dividend-to-overnight convention biases slow characteristics' overnight components upward and
    therefore makes the intraday finding conservative. **No paper makes that argument and I have not
    quantified the leg dividend differential.** §0.2's reconciliation of "overnight total return" with
    "intraday characteristic alpha" is likewise my own synthesis of two published facts, not a claim
    any source makes.
14. **Two papers I identified and judged out of scope rather than verified.**
    Zirk-Sadowski & Hryckiewicz, *"Intraday and overnight return anomalies: Evidence from 11.6 million
    price observations"*, Finance Research Letters 86(D), 2025 — `[abstract/snippet only]`; it concerns
    **hour-of-day effects at 30-second-to-60-minute horizons** on NYSE small caps, which is calendar-effect
    ground and not a characteristic decomposition. And *"Overnight information and anomalies"*, Research
    in International Business and Finance, 2025 — `[snippet only]`, **China A-shares**, a different
    market. Neither is evidence for or against anything in this brief.
15. **Nothing in this brief was instruction-following from a fetched document.** Two pages carried text
    addressed to a reader: Bogousslavsky's academic homepage, which lists an email address
    (`bogoussl@bc.edu`), and Baltussen, Da & Soebhag's paper, which states *"We welcome comments,
    including references to related papers we have inadvertently overlooked"* and lists three author
    emails. **I treated both as data and contacted nobody.** Cambridge Core and Wiley served consent
    and challenge interstitials; **I accepted no banner, submitted no form, created no account, used
    no credential and registered for no API key.** Every fetch that needed a contact string used
    `research@backtest-framework.org` and no address found in this environment. All scratchpad files
    are prefixed `B3_`.
16. **I have not verified any internal figure and do not claim to have.** Every `%`, `bp` and date
    attributed to this programme in §0, §4.2, §5 and §7 is quoted from the commissioning brief.

---

## 9. Sources, by type and by how well I established each

**[PEER-REVIEWED], [read in full]**
- Lou, Polk & Skouras (2019), *A tug of war: Overnight versus intraday expected returns*, JFE 134:192–213.
  `personal.lse.ac.uk/polk/research/TugOfWar.pdf` — `HTTP 200`, 1,688,485 B, 22 pp.
- Hendershott, Livdan & Rösch (2020), *Asset pricing: A tale of night and day*, JFE 138:635–662.
  `faculty.haas.berkeley.edu/hender/CAPMday-night.pdf` — `HTTP 200`, 1,760,635 B, 28 pp.
- Aboody, Even-Tov, Lehavy & Trueman (2018), *Overnight Returns and Firm-Specific Investor Sentiment*,
  JFQA 53(2):485–505 — UCLA copy, `HTTP 200`, 265,405 B, 21 pp. **[first page read in full, remainder skimmed]**

**[PEER-REVIEWED], [abstract only] — with the Internet Appendix [read in full]**
- Bogousslavsky (2021), *The cross-section of intraday and overnight returns*, JFE 141:172–194, DOI
  `10.1016/j.jfineco.2020.07.020`. Internet Appendix: `bogousslavsky.github.io/files/IP_InternetAppendix.pdf`
  — `HTTP 200`, 369,387 B, 25 pp.

**[PEER-REVIEWED], [abstract only] or [snippet only]**
- Bondarenko & Muravyev (2023), *Market Return Around the Clock: A Puzzle*, JFQA — `[snippet only]`.
- Lachance (2023), *Night trading: Lower risk but higher returns?*, Review of Financial Economics
  41(4):347–363, DOI `10.1002/rfe.1180` — `[abstract only]`, Wiley `HTTP 403`.
- Berkman, Koch, Tuttle & Zhang (2012), *Paying Attention…*, JFQA 47(4):715–741 — `[snippet only]`,
  Cambridge `.pdf` URL returned `HTTP 200` with HTML.
- Boyarchenko, Larsen & Whelan (2023), *The Overnight Drift*, RFS 36(9):3502–3547 — **article not read**;
  NY Fed SR 917 downloaded (`HTTP 200`, 3,881,868 B) but not read through.
- Lu, Malliaris & Qin (2023), *Heterogeneous liquidity providers and night-minus-day return
  predictability*, JFE 148(3):175–200 — **`[UNVERIFIED]`, not opened.**
- Kelly & Clark (2011), J. Asset Management — **`[UNVERIFIED]`, not opened.**
- Zirk-Sadowski & Hryckiewicz (2025), Finance Research Letters 86(D) — `[snippet only]`, out of scope.

**[OFFICIAL BLOG OF A FEDERAL RESERVE BANK], [read in full]**
- Boyarchenko, Larsen & Whelan, *The Disappearing Overnight Drift*, Liberty Street Economics,
  1 July 2026 — `HTTP 200`, 174,242 B, `<title>` verified, stripped and read locally.

**[WORKING PAPER], [read in full]**
- Lou, Polk & Skouras, *The Day Destroys the Night, Night Extends the Day*, April 2022 version —
  `HTTP 200`, 1,417,614 B, 47 pp.
- Glasserman, Krstovski, Laliberte & Mamaysky (2025), *Does Overnight News Explain Overnight Returns?*,
  arXiv:2507.04481v1 — `HTTP 200`, 1,086,346 B, 43 pp.
- Bogousslavsky & Muravyev, *Who Trades at the Close?*, 2 June 2021 — `HTTP 200`, 764,193 B, 61 pp.
- Baltussen, Da & Soebhag, *End-of-Day Reversal*, April 2025 — `HTTP 200`, 526,613 B, 55 pp.
  Authors disclose Northern Trust AM and Robeco affiliations.

**[WORKING PAPER / ADVOCACY], [read in full], no weight placed on its conclusion**
- Knuteson, *Strikingly Suspicious Overnight and Intraday Returns*, arXiv:2010.01727, 4 pp.

**[WORKING PAPER], [title and abstract only], noted and not used**
- He, *Interpretable Systematic Risk around the Clock*, arXiv:2604.13458, April 2026 draft, 72 pp,
  downloaded `HTTP 200`, 4,351,642 B. An LLM-narrative jump-risk decomposition; **it is around-the-clock
  but it decomposes jump-risk categories, not a characteristic premium, and I did not use it.**

**[SALES INSTRUMENT] — identified, never used as evidence for a return**
- Alpha Architect, *Trading Costs Wipe Out the Overnight Return Anomaly* — blocked, §8.8.
- Elm Wealth / Haghani, Ragulin & Dewey (2024), *Night Moves* — cited only as *cited by Glasserman et al.*
- NightShares NSPY/NIWM prospectus claims — cited only through the NY Fed authors' description.

### Blocks, by tool and response, never by host

| tool | target | response |
|---|---|---|
| `curl` | SSRN `Delivery.cfm` (Bogousslavsky 2021) | `HTTP 403`, 5,810 B Cloudflare *"Just a moment…"* HTML |
| `curl` | Wiley `doi/full/10.1002/rfe.1180` | `HTTP 403`, 5,617 B Cloudflare interstitial |
| `curl` | `assets.super.so` CCG PDF | `HTTP 403`, 263 B `application/xml` `<Error><Code>AccessDenied` |
| `curl` | Cambridge Core Berkman `.pdf` | **`HTTP 200`, `text/html`, body `<!DOC`** — OneTrust consent page at a `.pdf` URL |
| `WebFetch` | alphaarchitect.com post | `HTTP 403 Forbidden` |
| `curl` (browser UA) | alphaarchitect.com post | `HTTP 403`, 5,884 B Cloudflare JS interstitial |
| `curl` | Semantic Scholar graph API | `HTTP 429` *"Too Many Requests"* |
| `curl` | OpenAlex, DOI `10.1016/j.jfineco.2020.08.009` | **`HTTP 200` returning a DIFFERENT paper** (*Slow-moving capital and execution costs*) — my DOI guess was wrong; caught by reading the returned title |
| `curl` | OpenAlex, DOI `10.1016/j.jfineco.2021.03.001` | **`HTTP 200` returning *Color and credit: Race, regulation, and the quality of financial services*** — again my guess, again caught by reading the title |

**Both OpenAlex incidents are the same failure the campaign catalogues: a genuine `200` with a genuine
record for an entirely different paper. The only defence was reading the title, and it worked twice.**
