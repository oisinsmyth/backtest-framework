# J3 — WHAT A VALID FIXTURE-VALIDATION COMPARISON WOULD REQUIRE

External-evidence brief. **I have no access to this programme's data and claim nothing about it.**
Everything below is either (a) primary data documentation and data files fetched and read locally,
(b) published research read at the stated depth, or (c) **my own measurement against the French
files themselves**, whose method and zero-census control are stated so it can be re-run and
disagreed with.

Written 2026-09-10. The comparison itself is a measurement and is NOT attempted here.

Excluded per brief and honoured: the death process and delisting returns, the $5 screen's mid-hold
convention, the search for a second price source, vendor data defects and ticker reuse, factor-zoo
multiple testing. French's factors appear here **only as a data series with a documented
construction** — no factor-model research.

---

## 0. BOTTOM LINE, AND MY COMMISSIONING PREMISE WAS WRONG

**WRONG PREMISE. No French daily file header declares a survivorship-free database.** The brief
says "its own file header declares it built from a survivorship-free database." I downloaded four
daily files and censused the string `surviv` (case-insensitive) in each, and in the library's own
landing page. **Zero hits in all five.** What the headers actually say, verbatim, is one line
naming the vintage of the source database:

> `This file was created by using the 202607 CRSP database.`
> — `F-F_Research_Data_Factors_daily.csv`, line 1 [MEASURED IN BRIEF]

> `This file was created using the 202607 CRSP database.  It contains`
> `value- and equal-weighted returns for size portfolios.  Each record contains returns for:`
> — `Portfolios_Formed_on_ME_daily.csv`, lines 1–2 [MEASURED IN BRIEF]

The survivorship property is **inherited from CRSP and nowhere asserted by French**. This matters
more than pedantry: the *only* documented statement about names leaving a French portfolio is a
note on the library's landing page, and it describes a convention that **changed in May 2015**
(§1.4). A validation exercise that rests on "the header says survivorship-free" rests on a
sentence that does not exist. Cite CRSP, or cite the May-2015 note, and not the header.

**THE SPECIFICATION (the thing this lane had to return).** Named series, documented construction,
enumerated adjustments:

- **Named comparator:** a **count-weighted equal-weighted aggregate over French's ME deciles 3–10**,
  built from `Portfolios_Formed_on_ME_Daily_CSV.zip` §`Average Equal Weighted Returns -- Daily`
  with monthly count weights from `Portfolios_Formed_on_ME_CSV.zip` §`Number of Firms in
  Portfolios`. Construction documented in §1; I built it and report its reference statistics in §4.6.
  Over 2010-01-04..2026-07-31 it runs **mean 0.0585%/bar, CAGR 13.25%, annvol 21.40%,
  maxDD −42.27%, AC1 −0.0633, AC2 +0.0687** [MEASURED IN BRIEF].
- **Eleven enumerated adjustments** before the two are comparable, §2, with direction and — for
  five of them — magnitude measured off French's own files.
- **The crux, answered:** the expected difference from the floor alone is dominated by **one
  effect, and it is not the mean return.** A daily-rebalanced equal-weighted aggregate carries an
  upward compounding bias that is **+6.79%/yr in the microcap decile and +0.30 to +1.28%/yr in
  every decile above it** [MEASURED IN BRIEF, §2.2]. That is a factor of ~11 across the floor. It
  is the largest floor-induced difference by an order of magnitude, it is a pure construction
  artefact, and **it is the one a "compare against French" gesture would silently attribute to
  signal.**

**THE MOST IMPORTANT NEGATIVE.** Three of the five statistics the brief proposes would **merely
produce a number** (§4.7): mean return, cross-sectional dispersion, and drawdown shape are all
design-difference-dominated and cannot distinguish a defect from a floor. The two that can catch
a broken fixture are the **bar calendar** (exact, not statistical, and it is free) and the
**lag-1/lag-2 autocorrelation pair**. And the single most decisive check requires **no external
series at all** — §4.5.

**Item 5, plainly:** there **is** a published numerical figure, and the previous round was right to
find nothing in the obvious places. Canina, Michaely, Thaler and Womack report
**ρ_ew1 = 20.22 percent** for the daily CRSP equal-weighted index, 1964–1993 (§5). But it is a
within-month 20-observation average, not a full-sample estimate, it is 33 years stale, and I could
find **no full-sample daily AC1 for an equal-weighted US aggregate anywhere**. The canonical
references (Lo–MacKinlay 1988, 1990) are **weekly**. §5 gives the confirmed absence and substitutes
my own measured 2010–2026 values.

---

## 1. WHAT EXACTLY IS IN FRENCH'S PORTFOLIOS

All quotes in this section are from raw HTML and raw CSV fetched with `curl` and de-tagged locally,
**not through a summariser**. Where I first pulled a page through WebFetch, its summariser dropped
the weighting information entirely and asserted the size-portfolio page "does not specify whether
portfolios use equal or value-weighting" — it does not specify it on that page, but the *data file*
contains both, so the summariser's framing would have sent me the wrong way. Raw bytes only below.

### 1.1 The market factor — `F-F_Research_Data_Factors_daily_CSV.zip`

Verbatim, `Data_Library/f-f_factors.html` [PRIMARY DATA DOC] [read in full]:

> R m -R f , the excess return on the market, value-weight return of all CRSP firms incorporated in
> the US and listed on the NYSE, AMEX, or NASDAQ that have a CRSP share code of 10 or 11 at the
> beginning of month t, good shares and price data at the beginning of t, and good return data for
> t minus the one-month Treasury bill rate. The one-month Treasury bill rate data through May 2024
> are from Ibbotson Associates. Starting from June 2024, the one-month Treasury bill rate is from
> ICE BofA US 1-Month Treasury Bill Index.

> Stocks: Rm-Rf includes all NYSE, AMEX, and NASDAQ firms.

And verbatim from the library landing page, which dates the definition:

> In December 2012, we revised the market return used to measure Rm-Rf in the US. It is now the
> value-weight return of all CRSP firms incorporated in the US and listed on the NYSE, AMEX, or
> NASDAQ that have (i) a CRSP share code of 10 or 11 at the beginning of month t, (ii) good shares
> and price data at the beginning of t, and (iii) good return data for t. Previously we used the
> CRSP NYSE/AMEX/NASDAQ Value-Weighted Market Index as the proxy for the market return. The set of
> firms in the new series is more consistent with the universe used to compute the other US returns.

**What this is, operationally:** NYSE + AMEX + NASDAQ; **CRSP share codes 10 and 11 only** (US
common stock — so no ADRs, no REITs-as-SHRCD-18, no closed-end funds, no units, no trusts);
US-incorporated; screened on having shares, price and return data. **Value-weighted, reconstituted
monthly** (membership is fixed "at the beginning of month t"). No price floor. No liquidity screen.
No exchange-listing-venue screen beyond the three exchanges.

File contents [MEASURED IN BRIEF]: 4 columns `Mkt-RF,SMB,HML,RF`, 26,296 daily rows,
**19260701 to 20260731**. The header's only construction statement is the T-bill sentence:

> `The Tbill return is the simple daily rate that, over the number of trading days`
> `compounds to 1-month TBill rate. …`

**The market total return is `Mkt-RF + RF`**, and there is no separate total-return column. I
verified the two have identical volatility to 4 dp and AC1 differing by 0.0001, as they must
(§4.6 table) — RF is near-constant intraday.

**There is no equal-weighted market factor.** This is the central usability fact of the whole
territory and it is why §1.2 matters.

### 1.2 The size portfolios — `Portfolios_Formed_on_ME_Daily_CSV.zip` (THE usable EW file)

Verbatim, `Data_Library/det_port_form_sz.html` [PRIMARY DATA DOC] [read in full]:

> Portfolios: ME < 0 (not used); bottom 30%, middle 40%, top 30%; quintiles; deciles.
>
> Construction: The portfolios are constructed at the end of each June using the June market equity
> and NYSE breakpoints.
>
> Stocks: The portfolios for July of year t to June of t+1 include all NYSE, AMEX, and NASDAQ
> stocks for which we have market equity data for June of t.

Note what this page does **not** say: it does not mention share codes, and it does not mention
weighting. The share-code screen comes from the landing page's universe note; the weighting comes
from the file, which carries **both**. File structure [MEASURED IN BRIEF], 52,592 data rows in two
sections:

| line | content |
|---|---|
| 11 | `  Average Value Weighted Returns -- Daily` |
| 12 | `,<= 0,Lo 30,Med 40,Hi 30,Lo 20,Qnt 2,Qnt 3,Qnt 4,Hi 20,Lo 10,Dec 2,Dec 3,Dec 4,Dec 5,Dec 6,Dec 7,Dec 8,Dec 9,Hi 10` |
| 26311 | `  Average Equal Weighted Returns -- Daily` |
| 26312 | (same 19 columns) |
| 52610 | `Copyright 2026 Eugene F. Fama and Kenneth R. French` |

Both sections run 19260701–20260731, 26,296 rows each. **The `<= 0` column is −99.99 throughout the
2010–2026 window** — it is the negative-book-equity bucket, marked "not used". Drop it.

**The daily file contains NO firm counts and NO average firm size.** Those two sections exist only
in the **monthly** file `Portfolios_Formed_on_ME_CSV.zip`, which has six sections: VW monthly, EW
monthly, VW annual, EW annual, `Number of Firms in Portfolios`, `Average Firm Size`. This is a
hard constraint on §4's "fraction of names live over time" — see §1.5 for the daily workaround.

### 1.3 WHAT "EQUAL-WEIGHTED" MEANS HERE PRECISELY — and I established it by measurement, not by doc

French does not define it anywhere I could find. The definition that matters is whether the daily
EW series is the **cross-sectional arithmetic mean of that day's stock returns (daily rebalanced)**
or a **buy-and-hold** equal-weighted position struck at the June reconstitution. These differ by
several percent a year in microcaps and the entire comparison turns on it.

The published definition of the analogous CRSP series is unambiguous. Canina, Michaely, Thaler and
Womack, equation (1), verbatim [PEER-REVIEWED — *Journal of Finance* 53(1), 1998; author version
read in full]:

> where 𝑅𝑅_{m,τ}^d is the monthly return calculated from the daily index, 𝑅𝑅_{d,t,τ} is the CRSP daily
> index, which we calculate as (1 Σ𝑤𝑤_i⁄ )Σ_{i=1,…,n} 𝑤𝑤_i 𝑅𝑅_i, where 𝑅𝑅_i is the daily return for
> security 𝐼𝐼, for holding period 𝜏𝜏. For the EW index, 𝑤𝑤_i equals one for all securities, and for
> the VW index 𝑤𝑤_i is the market value of the firm's equity.

and their equation (2) for the monthly index is the cross-sectional mean of **monthly** (i.e.
within-month buy-and-hold) stock returns. So: **daily EW = daily rebalanced; monthly EW = monthly
rebalanced.** The gap between them is the Blume–Stambaugh/Roll rebalancing bias.

**I established that French's files behave the same way, and I established it with a control that
must return zero.** Test: for every calendar month 2010-01..2026-07, compound the daily series
within the month and subtract the monthly file's figure for the same portfolio. Theory
(Blume–Stambaugh 1983) says the **value-weighted** index has no compounding bias, so **the VW
columns must return ~0** — if my date alignment or section parsing were wrong, they would not.

[MEASURED IN BRIEF] VW columns, mean monthly difference, 199 months:

| portfolio | mean diff %/mo | annualised |
|---|---|---|
| VW Hi 10 | **+0.0002** | +0.002% |
| VW Hi 20 | +0.0006 | +0.007% |
| VW Dec 5 | +0.0033 | +0.039% |
| VW Lo 10 | +0.0089 | +0.107% |
| *worst VW cell* | +0.0089 | +0.107% |

**The control passes: every VW cell is within 0.009%/month of zero.** The EW columns, same test,
same months, same parser (§2.2) run up to **+0.5487%/month**. That is 60× the largest VW residual.
**French's daily equal-weighted series is daily-rebalanced**, and the monthly one is not. Established
by measurement against a zero-census control, which is stronger than a doc claim would have been.

### 1.4 HOW DELISTINGS ARE TREATED — and the convention changed in 2015

Verbatim, library landing page [PRIMARY DATA DOC] [read in full]. This is the only statement of the
convention anywhere in the library:

> In May 2015, we made two changes in the way we compute daily portfolio returns so the process is
> closer to the way we compute monthly portfolio returns. In daily files produced in May 2015 or
> thereafter, stocks are dropped from a portfolio immediately after their CRSP delist date; in files
> produced before May 2015, those stocks are held until the portfolio is reconstituted, at the end
> of June. Also, in daily files produced before May 2015 we exclude a stock from portfolios during
> any period in which it is missing prices for more than 10 consecutive trading days; in daily
> files produced in May 2015 and thereafter, we exclude a stock if there is no price for more than
> 200 consecutive trading days.

Two things follow, and both bear on a comparison against a fixture that **carries positions to a
dead name's final bar and closes there**:

1. The current convention is **drop immediately after the CRSP delist date**. A name's last
   included bar is its delist date, and the delisting return is inside CRSP's `DLRET`. So French's
   treatment and "carry to the final bar and close there" are **close but not identical** — French
   drops *after* the delist date, and whether the delisting return is in the last daily bar is a
   CRSP-side question I did not resolve (§8.4).
2. **Any archived French daily file downloaded before May 2015 is on the old convention** and is
   not comparable to one downloaded now. A validation run must record the download date and the
   header's CRSP vintage (`202607` in every file I pulled). French also says:

> We reconstruct the full history of returns each month when we update the portfolios.
> (Historical returns can change, for example, if CRSP revises its database.)

**So the comparator is not a fixed series.** Re-running the comparison next month can move the
French side. Pin the zip bytes; do not re-download mid-study.

### 1.5 Rebalancing frequency, breakpoints, and the one daily firm count that exists

Verbatim, landing page:

> The momentum and short term reversal portfolios are reconstituted monthly and the other research
> portfolios are reconstituted annually.
>
> Although the portfolios include all NYSE, AMEX, and NASDAQ firms with the necessary data, the
> breakpoints use only NYSE firms. Missing data are indicated by -99.99 or -999.

**NYSE-only breakpoints on a NYSE+AMEX+NASDAQ universe is the single most misread fact about these
files.** It means decile 1 is not 10% of the names — it is everything below the NYSE 10th
percentile of market cap, which in count terms is most of NASDAQ's small tail.
[MEASURED IN BRIEF] from the monthly `Number of Firms in Portfolios`, 199 months 2010-01..2026-07:

| decile | mean names | avg firm size ($m) |
|---|---|---|
| Lo 10 | **1,373.8** | **122.1** |
| Dec 2 | 442.6 | 511.1 |
| Dec 3 | 339.5 | 994.6 |
| Dec 5 | 226.3 | 2,583.2 |
| Dec 9 | 172.6 | — |
| Hi 10 | 169.0 | 125,705.8 |
| **total, 10 deciles** | **3,574.4** (min 3,193, max 4,166) | |

**Decile 1 is 38.3% of the universe by count** (min 29.1%, max 42.9%); deciles 1+2 are **50.7%**.
Equal-weighting this universe means half the weight sits in names averaging under ~$500m.

**The one daily firm count in the library.** `Portfolios_Formed_on_ME_daily.csv` has no counts, and
neither does `49_Industry_Portfolios_Daily.csv` — I checked both section lists. But
`25_Portfolios_5x5_Daily.csv` has **four** sections, and two of them are counts:

| line | section |
|---|---|
| 17 | `  Average Value Weighted Returns -- Daily` |
| 26317 | `  Average Equal Weighted Returns -- Daily` |
| 52617 | `  Number of Firms in Portfolios` |
| 78917 | `  Average Firm Size` |

[MEASURED IN BRIEF] That count section is **genuinely daily, not annually stamped**: the total
across the 25 cells changes on **2,166 of 4,168** consecutive-day pairs in 2010–2026, with changes
in all twelve calendar months. So a free daily point-in-time name count does exist, on a
**book-equity-screened** subset (mean 3,230.7 concurrent names vs 3,574.4 in the unscreened monthly
ME file — the BE screen costs ~340 names).

### 1.6 The industry portfolios — `49_Industry_Portfolios_daily_CSV.zip`

Header verbatim [MEASURED IN BRIEF]:

> `This file was created using the 202607 CRSP database.`
> `It contains value- and equal-weighted returns for 49 industry portfolios.`
>
> `The portfolios are constructed at the end of June.`
>
> `Missing data are indicated by -99.99 or -999.`

Two sections (VW daily, EW daily), 49 columns each, 26,296 rows each, 19260701–20260731. No counts.
Useful for exactly one thing here: it is the **only free daily cross-sectional panel** in the
library, so it is the only way to get a daily cross-sectional dispersion series out of French
(§4.4).

### 1.7 The 5×5 portfolios — `25_Portfolios_5x5_Daily_CSV.zip`

Header verbatim [MEASURED IN BRIEF]:

> `This file was created by using the 202607 CRSP database.`
> `It contains value-weighted returns for the intersections of  5 ME portfolios`
> `and  5 BE/ME portfolios.`
>
> `The portfolios are constructed at the end of June.  ME is market cap at the end`
> `of June.  BE/ME is book equity at the last fiscal year end of the prior calendar`
> `year divided by ME at the end of December of the prior year.`
>
> `Missing data are indicated by -99.99 or -999.`
>
> `The break points use Compustat firms plus the firms hand-collected from the`
> `Moodys Industrial, Transportation, Utilities, and Financials Manuals.`
>
> `The  portfolios  use Compustat firms plus the firms hand-collected from the`
> `Moodys Industrial, Transportation, Utilities, and Financials Manuals.`

**Note the header says "value-weighted returns" and the file contains an equal-weighted section
anyway.** The header is stale with respect to its own contents. A second reason not to trust these
headers as construction documentation. The BE/ME requirement makes this the **narrowest** universe
of the four files; use it for the daily count series (§1.5) and not for return comparison.

### 1.8 Which files are usable, one line each

| file | usable for | not usable for |
|---|---|---|
| `F-F_Research_Data_Factors_daily` | the **VW market total return** (`Mkt-RF + RF`), as an exact external anchor | anything equal-weighted |
| `Portfolios_Formed_on_ME_Daily` | **the comparison.** EW and VW daily, 10 deciles + 3 groups + 5 quintiles, 1926–2026 | firm counts; liquidity or price screens |
| `Portfolios_Formed_on_ME` (monthly) | the **count weights** and average firm size needed to aggregate deciles | daily anything |
| `25_Portfolios_5x5_Daily` | the **daily point-in-time name count** | return comparison (BE-screened universe) |
| `49_Industry_Portfolios_daily` | **daily cross-sectional dispersion** | name counts |
| `ME_Breakpoints` | the NYSE ME percentile ladder, monthly, every 5th percentile | anything price-based |

---

## 2. THE ADJUSTMENTS A LIKE-FOR-LIKE COMPARISON WOULD NEED

Eleven. Five are quantified off French's own files; two are quantified from the literature; four are
directional only and I say so.

### 2.1 Adjustment 1 — THE SIZE TILT THE FLOOR INDUCES (direction: large, and it is not the mean)

A $5 as-traded close floor plus a trailing dollar-volume screen removes the bottom of the
distribution. French's decile 1 averages $122m and is 38.3% of the count. **A floored universe
cannot be compared to any French aggregate that includes decile 1**, and that rules out
`Lo 30`, `Lo 20`, `Lo 10` and any count-weighted all-decile aggregate. The comparator must start at
decile 2 or 3. §4.6 gives all four variants.

**What the floor does NOT do much of:** change the mean. [MEASURED IN BRIEF] EW decile CAGRs
2010–2026 are 13.70 (Lo 10), 11.50, 14.01, 12.38, 13.18, 12.77, 12.17, 13.95, 12.67, 13.61 (Hi 10).
There is **no monotone size gradient in this window at all** — decile 1 is mid-pack and decile 2 is
the worst. So "mean return looks similar" is **not** evidence the floor is working, and "mean return
differs" is not evidence it is broken. §4.7.

### 2.2 Adjustment 2 — THE DAILY-REBALANCING (BID-ASK BOUNCE) BIAS. THIS IS THE CRUX.

This is the answer to "what differences should be expected from the floor alone".

**The mechanism** [PEER-REVIEWED] Blume and Stambaugh, *JFE* 12, 1983, 387–404, read at
[snippet only] — the PDF is a logged block, §7 — and via CMTW's account of it [read in full]:
using quoted closing prices imparts an upward bias to individual computed returns; a **rebalanced**
portfolio return inherits it, a **buy-and-hold** one largely does not. In their sample the average
daily rebalanced-minus-buy-and-hold difference is **0.056 percent per day for the smallest decile
and 0.001 percent per day for the largest — over fifty times as great** [snippet only, via search
result text; the number appears in their Section 4 discussion]. They conclude a bid-ask bias
accounts for roughly **one half** of the measured size effect.

**The magnitude, 1964–1993** [PEER-REVIEWED] Canina, Michaely, Thaler & Womack, *JF* 53(1), 1998
[read in full], abstract verbatim:

> The differences between the monthly returns compounded from the daily tapes and the monthly CRSP
> equal-weighted indices is almost 0.43 percent per month, or 6 percent per year. This difference
> amounts to one-third of the average monthly return, and is large enough to reverse the conclusions
> of a paper using the daily tape to compute the return on the benchmark portfolio.

And crucially, verbatim, on whether a narrower universe escapes it:

> The difference (on an annual basis) is 6.51 percent for the 10-stock portfolio, 7.12 percent for
> the 100-stock portfolio, 7.23 percent for the 300-stock portfolio, 7.19 percent for the 600-stock
> portfolio, and 7.18 percent for the 900- stock portfolio. These results indicate that (1) a
> significant bias exists even for a portfolio of ten stocks, and (2) the bias has the same
> magnitude for all the portfolios we check.

**So name count does not attenuate it. A 1,573-name universe gets the same bias as a 900-name one.**
The thing that attenuates it is the **spread of the names held**, which is what the floor changes.

**The magnitude in the programme's own window, which nobody has published** [MEASURED IN BRIEF].
Same test as §1.3, EW columns, 199 months 2010-01..2026-07, monthly-compounded-from-daily minus
monthly-file:

| portfolio | mean diff %/mo | **annualised** | max month | frac > 0 |
|---|---|---|---|---|
| **EW Lo 10** | **+0.5487** | **+6.79%** | +4.81 | 92.0% |
| EW Lo 20 | +0.4304 | +5.29% | +3.92 | 92.0% |
| EW Lo 30 | +0.3829 | +4.69% | +3.75 | 91.5% |
| EW Dec 2 | +0.0779 | +0.94% | +1.56 | 60.3% |
| EW Dec 3 | +0.1061 | **+1.28%** | +2.61 | 63.8% |
| EW Dec 4 | +0.0474 | +0.57% | +1.44 | 59.3% |
| EW Dec 5 | +0.0593 | +0.71% | +1.59 | 67.8% |
| EW Dec 6 | +0.0508 | +0.61% | +1.74 | 63.8% |
| EW Dec 7 | +0.0550 | +0.66% | +1.48 | 67.3% |
| EW Dec 8 | +0.0758 | +0.91% | +3.16 | 68.8% |
| EW Dec 9 | +0.0253 | +0.30% | +0.85 | 65.8% |
| **EW Hi 10** | **+0.0246** | **+0.30%** | +0.66 | 63.3% |

Three readings, and they are the heart of this brief:

1. **The bias is alive in 2010–2026, and in microcaps it is LARGER than CMTW's 1964–93 all-stock
   figure** — 6.79%/yr against 6.04%/yr. Tighter modern spreads did not kill it, because the
   decile-1 universe got smaller-cap, not just cheaper to trade.
2. **Above the floor it collapses to +0.30 to +1.28%/yr** — a factor of ~5 to ~23 versus decile 1.
   **This is the expected difference from the floor alone, and it is the dominant one.**
3. **It is one-sided and near-deterministic**, not noise: 92.0% of months positive in decile 1. A
   null will not absorb it. It is an accounting identity of how you average, not a return.

**The consequence for the comparison.** If the programme's aggregate is a daily cross-sectional
mean of its floored names (daily rebalanced) and it is compared to French EW `Lo 30` (which is
also daily rebalanced but includes decile 1), the floored side should come in roughly
**4%/yr lower in compounded terms from this effect alone** (Lo 30's +4.69%/yr against a
deciles-3–10 aggregate's ~+0.6%/yr), with nothing wrong on either side.
Compare against deciles 3–10 and that collapses to ~0. **This single adjustment is the difference
between a comparison and a gesture.**

### 2.3 Adjustment 3 — THE DOLLAR-VOLUME SCREEN HAS NO FRENCH COUNTERPART. Directional only.

French publishes portfolios formed on ME, BE/ME, operating profitability, investment, variance,
residual variance, net share issues, accruals, beta, E/P, CF/P, dividend yield, momentum and
reversal. **There is no turnover-, volume-, dollar-volume- or spread-sorted portfolio in the
library.** So a trailing dollar-volume screen **cannot be matched** on the French side. It can only
be bounded: the screen is positively correlated with size, so it pushes the comparator further up
the decile ladder than the price floor alone does. That is why §4.6 reports deciles 2–10, 3–10 and
4–10 rather than picking one — **the right comparator is a bracket, not a series.**

Supporting, for why the screen matters at all and is not just a size proxy [snippet only, via
search result summary — I did **not** read these and flag them as unverified depth]: Horowitz,
Loughran and Savin (2000) report the small-firm effect vanishing once sub-$5m-market-cap names are
removed; Crain (2011) and Bryan (2014) locate it in the smallest ~5% of firms. I cite these as
*direction*, not magnitude, and they should not be quoted from this brief.

### 2.4 Adjustment 4 — SHARE-CODE AND EXCHANGE SCOPE

French is **SHRCD 10 or 11, US-incorporated, NYSE/AMEX/NASDAQ**. A vendor daily endpoint returning
US single names is very unlikely to match that: it will typically include ADRs, REITs, units,
tracking stocks, and names on exchanges outside the three. Every such inclusion is a universe
difference that shows up in the aggregate and has nothing to do with the fixture being broken.

For contrast, the other major free library draws the line differently — JKP's `common` flag is
**SHRCD 10, 11 *or* 12** (§3.2). Even the two leading academic libraries disagree on the share-code
set. **This adjustment must be stated as a count, not assumed away:** the comparison needs the
programme's own count of names excluded by an SHRCD-10/11-equivalent screen.

### 2.5 Adjustment 5 — ANNUAL RECONSTITUTION vs A CONTINUOUSLY ELIGIBLE UNIVERSE

French's size portfolios are fixed from **end of June to end of June** — "constructed at the end of
each June using the June market equity and NYSE breakpoints" — with names leaving on delist and
**nothing entering until the next June**. A universe screened on a *trailing* dollar-volume window
and an as-traded price floor is re-evaluated continuously (or at whatever cadence the screen runs).

[MEASURED IN BRIEF] the size of this effect, from the 5×5 daily count series, by portfolio year
(July t → June t+1), 2010–2025 full years:

| portfolio year | start | end | net shrinkage |
|---|---|---|---|
| 2010 | 3,680 | 3,388 | 7.93% |
| 2013 | 3,327 | 3,144 | 5.50% |
| 2020 | 3,125 | 2,994 | 4.19% |
| 2025 | 3,079 | 2,868 | 6.85% |
| **mean, 16 full years** | | | **5.91%** |

So a French portfolio **shrinks ~5.9% over its year and then snaps back each July**. An aggregate
built on it has a sawtooth in its effective N that a continuously-screened universe does not. At
daily frequency this is second-order for returns; it is **first-order for any comparison of name
counts or of "fraction live"**, §4.3.

### 2.6 Adjustment 6 — POINT-IN-TIME COUNT vs UNION-OVER-TIME COUNT

"~1,573 names, ~35.7% dead" over a ragged 16.6-year panel is almost certainly a **union over
time**, not a concurrent count. French's 3,574.4 is a **concurrent monthly** count. These are
different quantities by a large factor and **must not be compared directly.** I cannot tell from
the brief which 1,573 is, and this is the adjustment most likely to produce a spurious "the fixture
is too small" or "the fixture is too big" conclusion.

For scale, if one takes French's 5.91%/yr net shrinkage as an attrition rate and compounds it
independently over 16.6 years, implied survival is **36.4%** — i.e. ~64% of a 2010 cohort gone,
against the fixture's stated 35.7% dead. **I state that contrast and decline to interpret it**,
because (a) French's shrinkage includes loss of Compustat book-equity coverage, not only death,
(b) the 5×5 universe is BE-screened, and (c) a $5-plus-dollar-volume screen selects names with a
materially different hazard. The honest conclusion is that **the two "dead fraction" numbers are
not the same statistic** and a comparison on them would be uninterpretable. §4.3.

### 2.7 Adjustment 7 — THE RETURN DEFINITION AND CORPORATE-ACTION BASIS

French's returns are CRSP total returns: dividends in, splits adjusted, delisting return applied.
A vendor endpoint returning **raw as-traded OHLCV with adjustment confined to a separate
adjusted-close column** is a different object. The aggregate must be built from a total-return
series or it will run below French by approximately the dividend yield (~1.5–2%/yr on a US
aggregate in this window) **with nothing wrong**. And the library flags a relevant change in its
own basis, verbatim:

> One important change to note is that in the Legacy (FIZ) format, monthly returns are month to
> month holding period returns with dividends reinvested at month-end. In the new Flat File Format
> (CIZ), monthly returns are compounded daily returns with dividends reinvested on their ex-dates.

> CRSP's Stock and Indexes Legacy Format (FIZ) files were discontinued after the December 2024 data
> release. Beginning with the January 2025 data release, we use the new Stock and Indexes Flat File
> Format 2.0 (CIZ) files to generate US research returns.

**The daily files I pulled are CIZ-era (created from the 202607 CRSP database).** Dividends are
reinvested **on ex-date**. A fixture reinvesting at month-end, or not at all, differs.

### 2.8 Adjustment 8 — THE $5 FLOOR IS ON PRICE; FRENCH SORTS ON MARKET EQUITY

There is **no price-sorted portfolio in the library and no price screen in any construction note.**
Price and market cap are correlated but not the same: a $3 stock with 400m shares is a $1.2bn
company and a $40 stock with 3m shares is a $120m company. **A decile-based comparator is a proxy
for a price floor, not a match to it.** This is an irreducible mismatch and it is the main reason
§4.7 concludes the *level* comparisons are weak. The `ME_Breakpoints` file gives the NYSE ME
percentile ladder (every 5th percentile, monthly, 1925-12 onward, "divided by 1000000") and lets you
locate a given market cap on the ladder — it does **not** let you locate a given price.

### 2.9 Adjustment 9 — THE WINDOW AND THE CALENDAR

[MEASURED IN BRIEF] French's daily files end **20260731**. The fixture runs to 2026-08-26. The
overlap is **2010-01-04 .. 2026-07-31 = 4,169 bars** against the fixture's stated ~4,190 to
2026-08-26; the ~21-bar gap is exactly August's trading days to the 26th, so the two calendars are
consistent at the endpoint. Per-year bar counts, which are an **exact** check:

| 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 |
|---|---|---|---|---|---|---|---|---|
| 252 | 252 | **250** | 252 | 252 | 252 | 252 | **251** | **251** |

| 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 (to 7/31) |
|---|---|---|---|---|---|---|---|
| 252 | **253** | 252 | **251** | **250** | 252 | **250** | 145 |

The non-252 years are the whole point: 2012 is 250 (the two-day Sandy closure), 2025 is 250, 2020 is
253. **Any fixture year that does not match this row has a calendar defect, full stop, no statistics
required.** §4.1.

### 2.10 Adjustment 10 — THE COMPARATOR IS NOT A FIXED SERIES

Per §1.4: French reconstructs the full history every month. Two runs a month apart are two
different comparators. **Pin the zip and record the header's CRSP vintage** (`202607` here). Also
note the library's own warning that a December 2023 Fama–French paper estimates the effect of
process and CRSP-data changes on average SMB and HML — i.e. the maintainers themselves treat the
series as revisable.

### 2.11 Adjustment 11 — THE `-99.99` SENTINEL

"Missing data are indicated by -99.99 or -999." A naive mean over a French column that includes the
sentinel is catastrophically wrong, and the `<= 0` column is sentinel throughout the modern window.
[MEASURED IN BRIEF] my zero-census: **0** sentinel cells in the 49 EW industry daily file over
2010–2026 (204,281 cells), and **67,250** over the full 1926–2026 file — so the test can fire and
did not. Run that census on any French column before using it.

---

## 3. OTHER FREE SURVIVORSHIP-FREE AGGREGATES

Stated honestly, including the ones that do not help.

### 3.1 Kenneth French Data Library — the only one that is actually fit for this

Coverage 1926-07-01 to 2026-07-31 daily; **free, no account, no registration**; `curl` with a plain
UA works (4 zips fetched, HTTP 200, §7). **Equal-weighted daily series published** for size
portfolios, 5×5, and 49 industries. Survivorship-free status: **documented by inheritance from CRSP,
NOT asserted in the files** (§0). Construction documented at the level quoted in §1 — which is thin,
and thinner than this territory assumed.

### 3.2 Global Factor Data (Jensen, Kelly, Pedersen) — jkpfactors.com

[PRIMARY DATA DOC] `Documentation.pdf`, 55 pp, fetched and scanned [read in full for the relevant
sections]. Coverage 93 countries, 153 characteristics (406 in the full set), daily factor returns
available. Free "for academic research and personal non-commercial use"; **stock-level data needs a
WRDS account with CRSP and Compustat** — so the stock-level panel is *not* free.

Why it does **not** substitute for French here, verbatim from the documentation:

> For each tercile, we compute its "capped value weight" return, meaning that we weight stocks by
> their market equity, winsorized at the NYSE 80 th percentile. This construc- tion ensures that
> tiny stocks have tiny weights and any one mega stock does not dominate a portfolio, seeking to
> create tradable, yet balanced, portfolios.

**Capped value weight, not equal weight.** I censused `surviv` in the whole document: **0 hits** —
same absence as French. And `\bew\b`: **0 hits**. The only equal-weighting is across factors within
a theme:

> To compute a cluster (theme) return, we first sign factors according to the original reference,
> then we equal-weight the returns of factors within a specific cluster.

What it **is** good for, and it is genuinely useful to this territory — **a second, independently
documented statement of the screens**, which is exactly what §2.4 needs:

> Suggested screens: – To restrict the sample to one observation per security× month, use obs
> main=1. – To restrict the sample to common stocks, use common=1. – To restrict the sample to
> prominent exchanges, use exch main=1. – To restrict the sample to primary listing × month, use
> primary sec=1.

> common Indicator for common stocks. If CRSP is the source, common is one if the SHRCD variable is
> 10, 11 or 12.

> exch main Indicator for ordinary exchanges. If CRSP is the source, main exchanges are those with
> crsp exchcd 1, 2 and 3.

> size grp This groups each firm into one of five categories: Mega, large, small, micro and nano
> cap. The groups are non-overlapping and the breakpoints are based on the market equity of NYSE
> stocks by the end of each month. In particular, Mega caps are stocks with a market cap above the
> 80th percentile of NYSE stocks, large caps are all remaining stocks above the 50th percentile,
> small caps are above the 20th percentile, micro caps above the 1st percentile and nano caps are
> the remaining stocks.

And its delisting convention, verbatim, which is a useful cross-check on §1.4:

> Return RET* We use RET. In case of delisting, we calculate as (1+RET)*(1+DLRET)-1

**Note the share-code disagreement with French (10/11/12 vs 10/11) and that JKP's breakpoints are
monthly where French's are annual.** Two libraries, two universes. Neither is wrong; they are not
interchangeable.

### 3.3 AQR Data Library

[UNVERIFIED depth — I read the library's "About" page description via search result text only,
not the page itself]. Free, no account. Monthly for most series, **daily for some** (the US BAB
equity factor among them). Each dataset is tied to a specific published paper, so construction is
documented *by reference to the paper* rather than in a data dictionary. **Value-weighted or
signal-weighted throughout as far as I could establish; I found no equal-weighted US aggregate.**
Survivorship-free status: not separately documented; inherited from CRSP/XpressFeed by assertion.
**I did not verify this and it should not be relied on from this brief.**

### 3.4 Open Source Asset Pricing (Chen & Zimmermann)

**Monthly only.** Rules it out for a daily-bar fixture check. Noted so the next round does not
re-walk it.

### 3.5 Hou–Xue–Zhang q-factor library (global-q.org)

Free, daily factors published, CRSP/Compustat-derived, construction in the published papers.
**Value-weighted.** No equal-weighted aggregate. Same shape of problem as AQR. [UNVERIFIED — I did
not fetch it this round.]

### 3.6 Index total-return series

- **Wilshire 5000 Total Market (FRED, free, daily)** — float-cap-weighted, not equal-weighted. A
  *chained real-time index* is free of survivorship bias **by construction** (the level is a live
  chain, not a re-selected backtest), but that property is not "documented survivorship-free
  status"; it is a different property and a weaker one for this purpose, because index membership
  rules are the index provider's and are not CRSP's.
- **S&P 500 Equal Weight** — genuinely equal-weighted and quarterly rebalanced, but it is **500
  large caps**, which is the wrong end of the distribution entirely, the index itself is licensed,
  and the free proxy (an ETF's price history from 2003) is a fund, not an index. **Rejected.**
- **S&P 500 / NASDAQ Composite levels on FRED** — price only, no dividends. Rejected.
- **CRSP cap-based indexes** — the right shape, but licensed; free index levels where published are
  for the investable (Vanguard-tracked) index family, not the research deciles.

### 3.7 Summary table

| source | coverage | freq | cost | EW available? | survivorship documented? |
|---|---|---|---|---|---|
| **French data library** | 1926-07→2026-07 | **daily** | **free, no account** | **yes** | **no — inherited from CRSP, not asserted** |
| JKP Global Factor Data | 1926→, 93 countries | daily | free (stock-level: WRDS) | **no** (capped value weight) | **no — 0 hits for `surviv`** |
| AQR Data Library | varies by paper | mostly monthly, some daily | free | not found | no |
| Open Source Asset Pricing | 1926→ | **monthly** | free | n/a | n/a |
| HXZ q-factors | 1967→ | daily | free | no | no |
| Wilshire 5000 (FRED) | 1970→ | daily | free | no (float-cap) | by construction, not documented |
| S&P 500 Equal Weight | 1990→ | daily | licensed | yes, but 500 large caps | by construction |
| CRSP research files | 1925→ | daily | **paid (WRDS)** | buildable | **yes, and asserted** |

**The honest conclusion: French is the only free source that publishes a documented, daily,
equal-weighted, dead-inclusive US aggregate. There is no second opinion available at zero cost.**
That is a real weakness of the whole exercise and it should be stated in any record that uses it:
a disagreement with French cannot be adjudicated against a third series.

---

## 4. WHAT IS THE RIGHT STATISTIC TO COMPARE?

Ranked by what would actually catch a broken fixture. The useless ones are named as useless.

### 4.1 RANK 1 — THE BAR CALENDAR. Exact, free, and not a statistic.

Compare the fixture's set of bar dates to French's, year by year, then date by date on any year
that disagrees. The reference row is in §2.9. This catches: a holiday calendar error, a
duplicated bar, a missing half-day, a timezone-shifted date, an off-by-one at a year boundary. It
is **deterministic** — there is no null, no p-value, no SE — and it is the check most likely to
fire on a real defect, because calendar bugs are the commonest kind and the hardest to see in a
return series. **Do this first and do not proceed until it passes.** It costs one set intersection.

### 4.2 RANK 2 — AUTOCORRELATION, AS THE (AC1, AC2) PAIR

This is the most diagnostic *statistic*, for a reason specific to the failure mode that matters:
**a stale or forward-filled bar shows up in AC1 and in almost nothing else.** A fixture that
carries a price through a non-trading day, or that forward-fills a halted name, manufactures
positive AC1 at the portfolio level (the non-synchronous-trading mechanism) while leaving the mean
and the volatility roughly intact.

[MEASURED IN BRIEF] the reference values, 2010-01-04..2026-07-31, n=4,169, iid SE ≈ 0.0155:

| series | AC1 | AC2 | AC3 | AC5 |
|---|---|---|---|---|
| **Mkt (VW total return)** | **−0.1030** | +0.0676 | −0.0437 | −0.0009 |
| EW Lo 10 (microcaps) | **+0.0978** | +0.1337 | +0.0309 | +0.0175 |
| EW Dec 2 | −0.0721 | +0.0712 | −0.0309 | −0.0019 |
| EW Dec 5 | −0.0599 | +0.0666 | −0.0380 | +0.0045 |
| EW Hi 10 | −0.0976 | +0.0773 | −0.0429 | −0.0037 |
| **EW deciles 3–10 (cnt-wtd)** | **−0.0633** | **+0.0687** | −0.0403 | −0.0025 |
| VW deciles 3–10 (cnt-wtd) | −0.0717 | +0.0646 | −0.0386 | +0.0030 |
| SMB | −0.0377 | +0.0060 | −0.0111 | −0.0017 |
| HML | +0.0369 | −0.0132 | −0.0507 | +0.0169 |

**The sign flip at the floor is the whole diagnostic.** Decile 1 is the **only** portfolio in the
file with positive AC1 (+0.0978, 6.3 iid SEs from zero). Every decile above it is **negative**, in a
tight band from −0.034 to −0.098. So:

- **A floored, dollar-volume-screened EW universe should have AC1 in roughly −0.03 to −0.08.**
- **If it comes back positive, that is either the floor failing to bind or stale bars.** Those are
  the two hypotheses worth separating, and they are separable: stale bars also inflate AC2 (decile 1
  has AC2 = +0.1337 against ~+0.068 for everything else), whereas a floor that merely binds
  loosely moves AC1 without that AC2 signature. **Hence the pair, not AC1 alone.**
- AC2 is remarkably stable at **+0.06 to +0.08 across every VW and EW decile and the market**. That
  stability is what makes it a usable control: a fixture whose AC2 is far off +0.07 has something
  wrong that is not a size tilt.

Caveat, and it is a real one: AC1 is a **weak** discriminant on the aggregate. The count-weighted
all-decile EW aggregate has AC1 = −0.0170 versus −0.0633 for deciles 3–10 — a gap of only 0.046,
about 3 iid SEs. Decile 1 is 38% of the count and still only moves aggregate AC1 by 0.046. **So
AC1 will catch gross staleness and will not catch a subtle floor mis-specification.** Do not
oversell it.

### 4.3 RANK 3 — THE DAILY LIVE-NAME COUNT, as a shape not a level

**The level is uninterpretable** (§2.6: union-over-time vs point-in-time; and the floor changes the
count by construction). **The shape is interpretable.** French's daily 5×5 count series (§1.5) has a
documented sawtooth: monotone decline within each July–June year at **~5.91%** (§2.5), then a jump
each July. A continuously screened universe should show a *different* shape — no July jump — but it
should show **the same delisting-driven downward pressure between re-screens**, and the daily count
should never rise on a day when no re-screen ran. **That last clause is the check**: a fixture whose
live-name count rises on an arbitrary Tuesday has a name entering the panel that should not be
there. That is a defect, and it is visible in the count series alone.

**What I will not propose:** comparing 35.7% dead to French's implied ~64%. §2.6 — not the same
statistic, and the comparison would be uninterpretable.

### 4.4 RANK 4 — CROSS-SECTIONAL DISPERSION. Available, but weak.

It is constructible for free at daily frequency from French, and this appears not to be widely
known: the **cross-sectional SD across the 49 EW industry returns each day** is a genuine daily
dispersion series off the same CRSP universe. [MEASURED IN BRIEF], 2010-01-04..2026-07-31:

> mean **1.0134%**, median 0.9198%, p5 0.5574%, p95 1.7245%, max 12.5332%, **AC1 of the dispersion
> series +0.4390**

The high AC1 (+0.44) is the useful part — dispersion is strongly persistent, so a fixture whose
dispersion series is *not* persistent has a problem. But as a **level** comparison it is poor: 49
industry aggregates have far lower dispersion than 1,573 single names, and the gap is a design
difference of unknown size. **Use the autocorrelation of dispersion, not its level.**

### 4.5 THE CHECK THAT NEEDS NO EXTERNAL SERIES AT ALL — and it is the most decisive

This falls out of §2.2 and it is the most useful thing in this brief.

**Compute, inside the fixture, the difference between (a) the monthly return obtained by compounding
the daily equal-weighted cross-sectional mean and (b) the equal-weighted mean of the names'
within-month buy-and-hold returns.** That difference is the Blume–Stambaugh rebalancing bias of the
names *actually held*. It requires no French file, no universe matching, none of the eleven
adjustments in §2 — it is internal to the fixture.

**And it has a pre-registrable expectation**, from §2.2: French's floored-equivalent deciles give
**+0.30 to +1.28%/yr**, and the unfloored microcap decile gives **+6.79%/yr**.

- A fixture landing in the **0.3–1.3%/yr** band has a floor that is binding on the spread.
- A fixture landing near **6–7%/yr** is holding microcap-spread names regardless of what the $5
  floor nominally does — which is precisely the thing the territory wanted to know and could not
  get from a mean-return comparison.

It is one-sided (92% of months positive in the microcap case), so it is **near-deterministic rather
than statistical** — no null needed, which for a programme that carries ~10 effective independent
instruments across 1,573 names is worth a great deal. **This is the comparison I would run first
after the calendar.**

### 4.6 THE COMPARATOR SERIES, BUILT, WITH ITS REFERENCE STATISTICS

[MEASURED IN BRIEF] 2010-01-04..2026-07-31, n=4,169 bars. `mean%` is per bar; `CAGR%` is
geometric annualised; count weights from the monthly `Number of Firms` section, held across each
month's days.

| series | mean% | CAGR% | annvol% | maxDD% | corr Mkt | AC1 | AC2 |
|---|---|---|---|---|---|---|---|
| Mkt (VW total return) | 0.0591 | 14.26 | 17.69 | −34.22 | 1.00 | −0.1030 | +0.0676 |
| EW deciles 1–10 (cnt-wtd) | 0.0569 | 13.07 | 20.19 | −41.37 | 0.89 | −0.0170 | +0.0936 |
| EW deciles 2–10 (cnt-wtd) | 0.0579 | 12.94 | 22.01 | −43.04 | 0.92 | −0.0665 | +0.0706 |
| **EW deciles 3–10 (cnt-wtd)** | **0.0585** | **13.25** | **21.40** | **−42.27** | **0.93** | **−0.0633** | **+0.0687** |
| EW deciles 4–10 (cnt-wtd) | 0.0572 | 13.03 | 20.75 | −41.08 | 0.94 | −0.0608 | +0.0680 |
| VW deciles 3–10 (cnt-wtd) | 0.0576 | 13.16 | 20.66 | −39.95 | 0.95 | −0.0717 | +0.0646 |
| EW Lo 10 | 0.0583 | 13.70 | 19.16 | −52.31 | 0.76 | +0.0978 | +0.1337 |
| EW Hi 10 | 0.0566 | 13.61 | 17.31 | −36.22 | 0.98 | −0.0976 | +0.0773 |

**Read the bracket, not the line.** Deciles 2–10, 3–10 and 4–10 span CAGR 12.94–13.25%, annvol
20.75–22.01%, maxDD −41.08 to −43.04%, AC1 −0.0608 to −0.0665. **That spread is the irreducible
uncertainty in the comparator from not being able to match the price floor and the dollar-volume
screen (§2.3, §2.8).** Any fixture difference inside that bracket is **not a finding**. This is the
number that makes the comparison honest, and it is the number a "compare against French" gesture
omits.

Note also: **corr with the market is 0.92–0.94 for every candidate comparator.** If the fixture's
aggregate does not correlate ~0.9+ with `Mkt-RF + RF`, that is a defect and not a design
difference. It is a cheap, high-power check and I would put it third, after the calendar and §4.5.

### 4.7 WHICH COMPARISONS WOULD MERELY PRODUCE A NUMBER. Say it plainly.

- **Mean return / CAGR: uninterpretable.** §2.1 — there is **no monotone size gradient in this
  window**. EW decile CAGRs run 11.50 to 14.01 in no order, and the whole decile 2–10 bracket spans
  only 12.94–13.25. The between-design spread and the within-bracket spread are the same size.
  A mean-return comparison cannot distinguish a defect from a floor. **Do not run it as a test; report
  it as context.**
- **Volatility: weak.** The bracket is 20.75–22.01% annualised against a market at 17.69%, and the
  fixture's own N and screen move it within that range. Only a gross miss (say below 15% or above
  30%) would mean anything.
- **Drawdown shape: uninterpretable as a test.** maxDD across candidate comparators spans −39.95 to
  −43.04%, and all of them are the same March 2020 event. One observation of one event. There is no
  statistic here, and a match or a miss would be luck. **Do not dress this up as a comparison.**
- **Cross-sectional dispersion levels: uninterpretable.** §4.4 — 49 aggregates vs 1,573 names.
- **The dead fraction: uninterpretable.** §2.6.

So of the five statistics the territory proposed, **one is diagnostic (autocorrelation), one is
mis-specified as a level but usable as a shape (live-name count), and three would produce numbers
and not evidence.** The two strongest checks available are not in that list at all: the **calendar**
(§4.1) and the **internal rebalancing-bias measurement** (§4.5).

---

## 5. IS THERE A PUBLISHED FIGURE FOR THE DAILY AUTOCORRELATION OF AN EQUAL-WEIGHTED US EQUITY PORTFOLIO?

**Yes, one, and it is weaker than it sounds. And a full-sample figure: confirmed absent.**

### 5.1 The figure that exists

[PEER-REVIEWED] Canina, Michaely, Thaler & Womack, "Caveat Compounder: A Warning about Using the
Daily CRSP Equal-Weighted Index to Compute Long-Run Excess Returns", *Journal of Finance* 53(1),
1998, 403–416. Author version read in full. Verbatim, from the body text on p. 9:

> It is interesting to compare the relative effect of the portfolio positive autocorrelation to the
> average negative autocorrelation of the individual securities on 𝐷𝐷𝐷𝐷𝐷𝐷𝐷𝐷. **The mean portfolio
> autocorrelation is 20.22 percent, and the mean securities' autocorrelation is −6.255 percent.**

The object, stated exactly, from p. 7–8:

> the first-, second-, and third-order average autocorrelations, respectively. Each security's
> autocorrelation for month 𝑡𝑡 is calculated from daily returns and averaged cross-sectionally.
> […] We also calculate the first-, second-, and third-order autocorrelations of the equal-weighted
> portfolio, 𝜌𝜌_{ew1}, 𝜌𝜌_{ew2}. 𝜌𝜌_{ew3}. Consistent with prior literature, the first-order portfolio
> autocorrelation is, on average, positive. The second- and third-order autocorrelations are
> negative, but much smaller.

and the estimation window, from footnote 5:

> As there are 21 trading days in most months, we use 20 observations to compute the first-order
> autocorrelation, 19 to compute the second, and 18 to compute the third (missing observations are
> excluded).

**So: ρ_ew1 = +0.2022, CRSP equal-weighted index, DAILY returns, sample 1964–1993 (360 months),
estimated within each calendar month from ~20 observations and averaged across months.** The
individual-security counterpart is **−0.0625**.

**Four reasons to discount it heavily before using it as an expectation:**

1. **It is not a full-sample AC1.** It is the mean of 360 twenty-observation estimates. A
   twenty-observation AC1 carries a small-sample downward bias of order −1/(T−1) ≈ −0.05, so the
   full-sample value it proxies is plausibly **higher** than 20.22%, not lower. The statistic is
   also not the same estimator as a 4,169-observation AC1 and should not be compared to one.
2. **It is 1964–1993.** The mechanism is non-synchronous trading and bid-ask bounce, and both have
   shrunk enormously. [snippet only, via search result text — I did **not** read the paper]
   Chordia, Roll and Subrahmanyam (*JFE* 87, 2008, "Liquidity and Market Efficiency") report that
   first-order daily autocorrelations **declined across tick-size regimes, particularly for smaller
   firms**, as the minimum tick fell. So the 1964–93 figure is an upper bound on a modern one by a
   margin nobody has published.
3. **The index is the full CRSP EW index — it includes decile 1.** Per §4.2 decile 1 is the only
   portfolio with positive AC1 in the modern window, so the 1964–93 positive figure is consistent
   with a modern **negative** figure for a floored universe, and the published number is therefore
   **not** an expectation for this programme. Using it as one would be a mistake.
4. **I could not read the table.** The figure is from the body text, which is the stronger source
   anyway; but Tables V and VI in the version I obtained are **images with no extractable text**
   (§8.2), so I could not confirm the standard deviation or the extreme values alongside the mean.

### 5.2 The absence, stated plainly

**I found no published full-sample daily lag-1 autocorrelation for an equal-weighted US equity
aggregate.** Specifically:

- **Lo and MacKinlay (1988)**, *RFS* 1, 41–66, the canonical reference, is **weekly**, not daily.
  Corroborated in a third-party description [UNVERIFIED, snippet only]: they reject the random walk
  for "the CRSP NYSE Value-Weighted and CRSP NYSE Equal-Weighted index for a sample of **weekly**
  data from September 6, 1962, to December 26, 1985."
- **Lo and MacKinlay (1990)**, *RFS* 3, 175–205, is the reference CMTW cite for **individual
  security** daily autocorrelations, and CMTW's own text says their −6.255% is "similar in magnitude
  to that reported by Lo and MacKinlay (1990)". So the published daily figure in that literature is
  for **single names**, not for the EW portfolio.
- **Ortiz, Contreras and Villena (2018)**, arXiv:1510.03926, which on its title looked like exactly
  the paper — read in full via `pypdf` — analyses the CRSP VW and EW indexes 1950–2013 but uses
  **variance-ratio tests on weekly rolling windows**, and reports **no daily AC1 number**. Their
  daily work is a **simulation** of two- and six-asset portfolios, not an estimate on the index.
- **Campbell, Lo and MacKinlay (1997)** Table 2.4 is the remaining candidate. Third-party
  descriptions say it reports first-order autocorrelations for daily, weekly and monthly VW and EW
  CRSP indexes, 1962–1994, and that they are "positive and often significantly different from
  zero". **I could not obtain the numbers** (§8.1). **I flag this as the one place a published
  full-sample daily figure plausibly exists, and as unverified.** If the next round wants it, it is
  a library request for one page of a textbook, not a web search — the searches do not surface it
  and I burned two on it.

**So: the previous round's finding stands, with one amendment.** There is no published full-sample
daily EW autocorrelation that I could verify. There **is** one published daily-frequency figure
(+0.2022, within-month, 1964–93) and it is the wrong vintage, the wrong estimator and the wrong
universe to serve as this programme's expectation.

### 5.3 What to use instead

The values in §4.2, measured off the primary files over the programme's own window: **−0.0633 for
the count-weighted EW deciles 3–10, −0.1030 for the VW market, +0.0978 for the unfloored microcap
decile.** These are not published figures and should not be cited as such — they are my measurement
and the script is at §6 — but they are the right window, the right estimator and the right
universe, which the published figure is not on any of the three.

---

## 6. REPRODUCING THE MEASUREMENTS

Five zips + two HTML pages + two PDFs, all fetched 2026-09-10 with
`curl -A "backtest-framework-research/1.0 (research@backtest-framework.org)"`. Every file header
quoted above came from the bytes on disk, not from a summariser.

| file | bytes | HTTP |
|---|---|---|
| `F-F_Research_Data_Factors_daily_CSV.zip` | 178,044 | 200 |
| `Portfolios_Formed_on_ME_Daily_CSV.zip` | 1,565,760 | 200 |
| `Portfolios_Formed_on_ME_CSV.zip` | 200,578 | 200 |
| `25_Portfolios_5x5_Daily_CSV.zip` | 4,035,370 | 200 |
| `49_Industry_Portfolios_daily_CSV.zip` | 4,186,243 | 200 |
| `ME_Breakpoints_CSV.zip` | 81,038 | 200 |
| `data_library.html` | 245,739 | 200 |
| `f-f_factors.html` / `det_port_form_sz.html` | 16,999 / 12,444 | 200 |
| Caveat Compounder (Cornell eCommons) | 881,416 | 200 |
| JKP `Documentation.pdf` | 644,240 | 200 |

Scripts (scratchpad, not committed — **if any number here is to be quoted in a record, the scripts
and the pinned zips belong in `data/`, per the file contract**):
`meas.py` (§4.2 autocorrelations), `diff.py` (§1.3 zero-census control + §2.2 bias table + §1.5
counts), `meas2.py` (§2.11 sentinel census, §4.4 dispersion, §4.6 drawdowns, §2.9 calendar),
`meas3.py` (§2.5 attrition), `ref.py` (§4.6 comparator construction).

**The control to re-run first:** the VW compounding-difference census of §1.3. It must return
≤0.01%/month on every VW column. If it does not, the date alignment between the daily and monthly
files is wrong and every EW number in §2.2 is wrong with it. And the sentinel census of §2.11 must
return 0 for 2010–2026 and 67,250 for the full file — **the second half is the part that proves the
census can fire at all.**

---

## 7. BLOCKS, BY TOOL AND RESPONSE

1. **`curl` → `www-2.rotman.utoronto.ca` (and `www-2.` variant), Blume & Stambaugh 1983 PDF.**
   **HTTP 200, 1,651 bytes, `content_type: text/html`** — body is
   `<title>404Handler</title>` with a JS redirect to `apps.rotman.utoronto.ca/404handler/`.
   **This is an HTTP 200 that is wrong**, exactly the failure mode the shared rules warn about: a
   200 with a content-type and a size that only a byte inspection catches. I treated it as a block.
   Consequence: **Blume & Stambaugh (1983) is [snippet only] in this brief**, via CMTW's direct
   quotation of it and via search-result text. Its bias *formula* is not quoted here because I could
   not read it, and §2.2 rests on CMTW and on my own measurement instead.
2. **`WebFetch` → `arxiv.org/pdf/1510.03926`.** Returned "I cannot find… The document appears to
   contain compressed/encoded data and images rather than readable text". **Not a block** — the
   bytes landed in the tool-results cache and `pypdf` read all 46 pages and 70,553 characters
   cleanly. §5.2's finding on that paper comes from the local read, not the summariser.
3. **`WebFetch` → French `f-f_factors.html` and `det_port_form_sz.html`.** HTTP 200 and answered,
   but the summariser **omitted the weighting information** and stated of the size-portfolio page
   "The page does not specify whether portfolios use equal or value-weighting" and "does not address
   share codes". Both pages were then fetched raw. **Logged because it is the failure the shared
   rules predict:** the summary was not false, but it was the wrong shape for construction
   documentation, and acting on it would have cost the EW series entirely.
4. **`pypdf` → Caveat Compounder, pages 14–20.** Extracted 11–24 characters per page: **Tables I–VI
   are images.** Body text extracted fine. §5.1's figure is body text; the table values are not
   available from this copy.
5. **No block on:** `mba.tuck.dartmouth.edu` (10 fetches), `ecommons.cornell.edu`,
   `jkpfactors.s3.amazonaws.com`, `arxiv.org`.

---

## 8. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **Campbell, Lo and MacKinlay (1997) Table 2.4.** This is the most likely home of a published
   full-sample **daily** AC1 for the CRSP equal-weighted index (1962–1994). I could not obtain the
   numbers — two searches returned only third-party descriptions ("positive and often significantly
   different from zero", p. 68) and no values. **If item 5 is worth closing properly, this is a
   one-page textbook lookup, not a search.** Everything in §5.2 is conditional on this.
2. **Blume & Stambaugh's bias formula and their Table 3 magnitudes.** [snippet only]. The
   0.056%/day vs 0.001%/day contrast is quoted here from search-result text and is corroborated in
   direction by my own §2.2 measurement, but **I did not read the paper** and the per-stock bias
   expression (which I believe is of order one quarter of the squared proportional spread) is
   **not** asserted in this brief. Do not quote a formula from here.
3. **Whether French's last daily bar for a delisting name includes the CRSP delisting return.**
   §1.4 establishes names are "dropped from a portfolio immediately after their CRSP delist date"
   but not whether `DLRET` is compounded into the final daily observation. JKP's documentation shows
   their own convention is `(1+RET)*(1+DLRET)-1`; French states no convention. **This matters
   specifically because the fixture closes positions on a dead name's final bar**, so the two final
   bars may differ by the delisting return. Unresolved. (The death process itself is excluded ground
   and I did not pursue it; this is a French-construction gap, not a death-process question.)
4. **Whether French's daily EW portfolio return uses that day's surviving members only, or the
   June-set members with missing names excluded.** §1.3 establishes it is a daily cross-sectional
   mean (daily rebalanced) by measurement. It does **not** establish the denominator on a day when
   a member has no price. The "no price for more than 200 consecutive trading days" exclusion rule
   implies names with shorter gaps are retained — but with what return on the gap days, I do not
   know. This is a real gap for a fixture that must decide the same question.
5. **AQR and HXZ libraries.** §3.3 and §3.5 are [UNVERIFIED] — I read neither this round, and
   the statements that neither publishes an equal-weighted US aggregate are my inference from their
   documented methods as described in search results, not from their data dictionaries. **Do not
   treat §3.3/§3.5 as established.** Given §3.7's conclusion (French is the only free EW source)
   rests partly on these, that conclusion is the weakest claim in this brief.
6. **The attrition contrast in §2.6.** French's implied ~64% 16.6-year attrition against the
   fixture's stated 35.7% dead. I measured the French side and I am confident in it as a
   *measurement of the BE-screened 5×5 universe's net within-year shrinkage*. I am **not** confident
   it is the same quantity as "35.7% dead", and I say in §2.6 that a comparison on it would be
   uninterpretable. The contrast is in this brief as a flag, not a finding.
7. **The literature on price filters** (Horowitz–Loughran–Savin 2000, Crain 2011, Bryan 2014),
   §2.3. [snippet only], from one search-result summary, **not read**. Direction only. The specific
   claim "removing sub-$5m-market-cap names makes the small firm effect vanish" is a paraphrase of
   a paraphrase and should be re-established before it is relied on.
8. **Whether the programme's 1,573 is a concurrent or a union-over-time count.** §2.6. The whole
   name-count arm of §4.3 depends on which it is, and I cannot see the data. The comparison needs
   the concurrent daily count; French supplies its own (§1.5).
9. **Nothing in this brief is a claim about the programme's data.** Every measured number above is
   a measurement of French's published files or of a published paper. I have not seen the fixture
   and the comparison remains unrun.
