# N1 — short interest and days-to-cover: external evidence

*Compiled 2026-09-09. Research only: nothing was run, no fixture was touched. Every
numeric claim below is tagged to a source in §9. Where I could not verify something I say
so in the line itself.*

---

## 1. Verdict

**The predictive literature is real but the money is on the WRONG LEG for us, the borrow-fee
literature is close to fatal for the directional short use, and the free data does not reach
our fixture.** Three independent findings converge. (i) Where anyone has looked carefully at
the two legs separately, the reliable abnormal return is on the LONG side — *low* short
interest in heavily traded names — while the high-short-interest leg is "transient and of
debatable economic significance" (Boehmer-Huszar-Jordan 2010) and in Drechsler's own table
the top short-interest decile earns a raw equal-weighted **−0.06%/month**, i.e. flat, not
falling. (ii) Beneish-Lee-Nichols (2015) split nine anomalies' short legs by borrowability:
in the 85.7% of stock-dates that are *general collateral* (cheap to borrow — the only names a
retail book can actually short at scale) the short-side size-adjusted return is **−0.3% to
+0.3% per month, none significant**; the entire short-side alpha lives in the 14.3% that are
"special". Muravyev-Pearson-Pollet (JF 2025) reach the same place across 162 anomalies:
+0.14%/mo gross, **−0.01%/mo net of borrow fees**, and *"not profitable even before fees if
the high-fee observations, representing 12% of stock dates, are excluded."* (iii) Free
consolidated short interest for **exchange-listed** US names begins **June 2021** — FINRA's
free archive before that date is OTC-only — so ~11 of our 16.6 fixture years have no free
short-interest data at all, and the free per-symbol alternatives (Nasdaq) serve only
*currently listed* tickers on a rolling window, which would reintroduce precisely the
survivorship bias the fixture exists to remove. **The exclusionary use is the only version of
this lead I would still defend, and even it is weakened**: squeezes are a ~10%-of-names-per-
quarter event, the variable that actually measures squeeze risk is the *borrow fee* rather
than short interest, and the fee is not free. If N1 proceeds, it should proceed as a
June-2021-onward exclusion filter with a pre-registered acceptance that the sample is ~5
years and ~126 semi-monthly observations — not as a directional signal, and not as a claim
about the full fixture.

---

## 2. The anomaly as documented

| source | year | sample | universe | leg | magnitude | cost treatment |
|---|---|---|---|---|---|---|
| Asquith, Pathak & Ritter, *JFE* 78(2):243–276 | 2005 | 1988–2002 | NYSE/AMEX/NASDAQ, all sizes | short (high SI × low institutional ownership = "constrained") | **−215 bp/mo equal-weighted**; **−39 bp/mo value-weighted and INSIGNIFICANT** | **none**. No borrow, no spread, no commission |
| Boehmer, Huszar & Jordan, *JFE* 96(1):80–97 | 2010 | 1988–2005 | NYSE/AMEX/NASDAQ | **long** (low SI × heavily traded) | positive abnormal returns, "statistically and economically significant", *"often larger (in absolute value) than the negative returns observed for heavily shorted stocks"*; high-SI negative returns "can be transient and of debatable economic significance" | **none** stated in abstract; I did not obtain the full text to check an in-paper cost section |
| Hong, Li, Ni, Scheinkman & Yan, NBER WP 21166 | 2015 | 1988–2012, monthly rebalance | NYSE/AMEX/NASDAQ | long–short decile | **DTC 1.19%/mo EW** vs **short-interest-ratio 0.71%/mo EW**; 1-SD spread in SIR ⇒ 0.16%/mo | **none**. This is the headline DTC result and it is a gross number |
| Drechsler & Drechsler, NBER WP 20282 | 2014 | Apr 1980–Oct 2012 (SIRIO); Jan 2004–Oct 2012 (actual fees) | CRSP shrcd 10/11, **bottom 10% of size AND of price dropped** (~15% of obs) | sort on short interest / institutional ownership | decile 10 raw EW **−0.06%/mo**, FF4 alpha −1.09%; decile 1 +1.42%, alpha +0.45%; 1−10 spread 1.48% raw / 1.54% alpha (t=8.84) | fee-sorted portfolios reported gross **and** net; see §3 |
| Beneish, Lee & Nichols, *JAE* 60(2):33–57 | 2015 | Jul 2004–Dec 2013 (114 months); Table 6 Jun 2004–Nov 2013 | Markit Data Explorers ≈ 90% of CRSP market cap | short leg of nine anomalies, split by borrowability | see §3 — the split is the finding | loan fees explicitly; "several of these anomalies cease to be profitable" |
| Muravyev, Pearson & Pollet, *JF* 80(6):3639–3694 | 2025 | Markit borrow fees from **July 2006** onward; 83% of the 162 anomalies had original samples ending before 2006, so this is largely out-of-sample | US equities with Markit fee coverage | 162 anomaly long–shorts; **returns are due to the short leg** | **+0.14%/mo gross → −0.01%/mo net of borrow fees** | borrow fees, explicitly and centrally |
| "How prevalent are short squeezes?", *J. Banking & Finance* | 2025 | US and Europe | US and EU listed | n/a — base rate | market squeezes affect **9.9% of unique US stocks per quarter** (12.3% EU), "rare and short-lived" | n/a |

**Reading of the table.** Every equal-weighted result is large; the one value-weighted result
is 39 bp and insignificant. That gap *is* the size effect, and it is the same gap that has
killed things in this programme before (§8). The two papers that separated the legs
(Boehmer et al. 2010; Muravyev et al. 2025) disagree about which leg carries the gross
return — Boehmer says long, Muravyev says short — but they agree on the thing that matters
here: Muravyev's short leg carries the return *and then loses all of it to the borrow fee*.

**What I could not verify.** I did not obtain full texts for Asquith et al., Boehmer et al.,
or Hong et al.; those rows are from abstracts and from search-engine summaries of abstracts,
and I have not checked their t-statistics, their exact portfolio construction, or whether
they impose a price filter. Treat the magnitudes as indicative, not as audited.

---

## 3. Is it just the borrow fee?

**Largely yes for the tradeable part of the universe, and this is the strongest thing in the
file.** Two papers, from different angles, with the same conclusion.

**Beneish, Lee & Nichols (2015)** is the most directly useful because it partitions rather
than averages. They classify each stock-date from Markit Data Explorers as *Special*
(hard/expensive to borrow, DCBS > 2) or *General Collateral* (GC, cheap). **14.3% of
stock-dates are Special; 85.7% are GC.** Their Table 6, Panel A — one-month-ahead
size-adjusted returns to the short side of nine anomalies, 114 months:

| strategy | All obs | Special | **GC** |
|---|---|---|---|
| GrossProfit | −0.1% (t −0.54) | −1.5% (t −3.44) | **+0.3% (t 1.15)** |
| AssetGrowth | −0.5% (t −2.68) | −1.4% (t −3.39) | **−0.3% (t −1.38)** |
| Investment/assets | −0.6% (t −2.07) | −2.0% (t −4.40) | **−0.2% (t −0.74)** |
| NOA | −0.4% (t −1.44) | −1.7% (t −3.84) | **−0.1% (t −0.29)** |
| Accruals | −0.5% (t −3.17) | −1.6% (t −4.05) | **−0.2% (t −1.16)** |
| Payout% | −0.2% (t −1.21) | −1.0% (t −2.59) | **+0.0% (t 0.30)** |
| QuarterlyEarnings | −0.4% (t −1.40) | −2.1% (t −4.58) | **+0.2% (t 0.90)** |
| OhlsonScore | −0.4% (t −1.22) | −1.6% (t −4.09) | **+0.3% (t 0.82)** |

Every Special column entry is significant at better than 1%. **Not one GC entry is
significant, and three of the eight shown are positive.** Their own summary: *"abnormal
returns to the short-side of nine well-known market anomalies are attributable solely to
'special' stocks"*, and *"the short-side returns documented in prior studies are likely
unavailable without incurring significant borrowing costs. This reduces the attainable
profitability of strategies appearing in the literature."* They also document a **U-shaped**
relation between the short-interest ratio and specialness — both extremely high *and*
extremely low SI names are more likely to be on special — which means SI is a noisy,
non-monotone proxy for the fee.

**Muravyev, Pearson & Pollet (JF 2025)** is the broadest statement: 162 anomalies, Markit
fees from July 2006, average long–short **+0.14%/mo gross**, **−0.01%/mo net of borrow
fees**, returns due to the short leg. The killer sentence for us is not the net number but
the conditional one: *"anomalies are not profitable even before fees if the high-fee
observations, representing 12% of stock dates, are excluded."* Their 12% and BLN's 14.3% are
the same population. A retail book that cannot access the expensive-to-borrow tail — and
even where it can, must pay the fee that defines it — is left with a universe in which the
short-side effect measures zero *gross*.

**The honest counterweight — Drechsler & Drechsler (2014) argue the opposite, and I am not
going to hide it.** Sorting *on the fee itself* they find the cheap-minus-expensive-to-short
(CME) portfolio earns **1.43%/mo gross, 0.91%/mo net of fees**, FF4 alpha 1.53%; the top
decile's net return is −0.16%/mo. Their conclusion: *"high-short-fee stocks have low returns
even from the viewpoint of an investor who lends them out and earns the fees."* Three things
reconcile this with the papers above rather than contradicting them:
1. Their "net" is **the securities lender's** economics, not the short seller's. The
   sentence quoted says so explicitly. A retail short pays the fee; it does not receive it.
2. Most of the CME return is on the **long** side (cheap-to-short names), which is a
   different and much cheaper trade than shorting the expensive tail.
3. They drop the bottom decile of **both** size and price (~15% of observations), so their
   surviving expensive-to-short names still average **$1.30B** market cap — a very different
   population from a $5-floor retail short book's likely candidates.

**Net answer to the decisive question:** the short-interest anomaly is not *identically* the
borrow fee, but within the borrowable, cheap-to-short 85–88% of stock-dates — which is
functionally the whole of a retail short book — the documented short-side abnormal return is
statistically indistinguishable from zero. For our purposes the distinction is academic and
the answer is: **yes, close enough to fatal for a directional short book.**

---

## 4. Post-2010 and cost survival

- **Cost survival, borrow only.** Muravyev et al.: 0.14% → −0.01%/mo. That is borrow fee
  alone, before any commission or spread.
- **Cost survival, trading costs.** Chen & Velikov (2023): mean anomaly long–short net of
  trading costs is about **−1 bp/month post-2005** under original implementations, rising to
  only ~4 bp under cost-minimising execution; the average anomaly's net expected return is
  ~8 bp/mo. Anomaly portfolios overweight stocks with roughly **4× the median NYSE spread**
  and turn over ~40% per month. Note this is a *trading-cost* study, not a borrow study —
  the two costs stack.
- **Post-publication decay.** McLean & Pontiff (2016) is the canonical reference; the figure
  usually quoted is a ~58% post-publication decline, and one search summary this session
  reported "50%". I did not open the paper. **[UNVERIFIED — exact figure]**
- **Size and price concentration — the direct hit.** Asquith-Pathak-Ritter is the clean
  statement: −215 bp EW vs −39 bp VW and insignificant. The effect is a small-stock effect.
  Drechsler's expensive-to-short decile is also the *smallest* decile in his sort. BLN's
  Special names are the constrained-supply names. Every route into the money goes through
  small, illiquid, hard-to-borrow, and (by strong implication, though none of these papers
  reports a price distribution I verified) low-priced stock. **[PARTIALLY UNVERIFIED — I
  found no paper that tabulates the short-interest effect by share PRICE bucket. That is a
  real gap and it is the exact axis our cost model is most sensitive to.]**
- **Crowding.** I found no clean, citable post-2010 decay study *specific to short interest*.
  Search summaries assert the signal has weakened and that short interest ratios have sat at
  roughly half their 2008 peak, but I could not tie that to a primary source I read.
  **[UNVERIFIED]** What is solid: short interest is among the oldest and most widely
  distributed non-price variables in existence (free, semi-monthly, since the 1970s in some
  form), it is a standard field in every commercial quant platform, and the two most recent
  serious papers on it (Muravyev 2025, Chen-Velikov 2023) both conclude the tradeable
  residual is approximately zero. The prior on crowding should be very high.

---

## 5. THE DATA

### 5a. FINRA consolidated equity short interest — the main free source

- **Landing / files:** `https://www.finra.org/finra-data/browse-catalog/equity-short-interest/files`
- **About:** `https://www.finra.org/finra-data/browse-catalog/equity-short-interest`
- **Query API (POST):** `https://api.finra.org/data/group/otcMarket/name/EquityShortInterest`
  — filter on `settlementDate`, returns CSV or JSON. XML endpoint
  `https://api.dapi.finra.org/api/EquityShortInterest/GetESI?settlementDate=31-Jul-18`.
- **Format:** CSV / JSON (XML for the legacy endpoint). Downloadable archive files by
  settlement date.
- **COVERAGE — THE BINDING CONSTRAINT.** FINRA's own note: *"Prior to June 2021, the data
  contains short interest positions in over-the-counter securities only and does not reflect
  short interest data in exchange-listed securities."* Archive files go back to 2014 but are
  **OTC-only until June 2021**. Our universe is exchange-listed single names. **Free FINRA
  short interest usable for our fixture therefore starts June 2021 — about 5.2 of 16.6 years,
  ~126 semi-monthly observations.**
- **Fields (full data dictionary, verified from FINRA's own metadata PDF):**
  `issueSymbolIdentifier`, `settlementDate`, `issueName`, `marketCategoryCode`,
  `marketCategoryDescription`, `currentShortShareNumber`, `previousShortShareNumber`,
  `changePercent`, `percentageChangefromPreviousShort`, `averageShortShareNumber`,
  `daysToCoverNumber`, `updateDatetime`.
- **IDENTIFIER: SYMBOL ONLY. THERE IS NO CUSIP.** The only other identifying field is
  `issueName`, truncated to ~30 characters. See §6 rule 4.
- **Days-to-cover is provided but CENSORED.** FINRA's definition: short interest / average
  daily share volume; **"1.00 will be displayed for any values equal or less than 1"** and
  the observed cap in FINRA's own sample output is **999.99**; **"N/A will be displayed if
  the days to cover is Zero (i.e., Average Daily Share Volume is Zero)."** So DTC is floored
  at 1, capped at ~1000, and undefined for zero-volume names. Any runner must recompute DTC
  from `currentShortShareNumber / averageShortShareNumber` rather than trust the field, and
  must handle `averageShortShareNumber = 0` (FINRA translates NULL volume to zero).
- **`averageShortShareNumber` definition:** *"Total Volume or Adjusted Volume in case of
  splits / Total trade days between (previous settlement date + 1) to (current settlement
  date)."* It is FINRA's own ADV over the cycle — it will not equal our fixture's ADV, and it
  is split-adjusted on FINRA's basis, not ours. Given `fixtures-disagree-on-corporate-action-basis`,
  this is a live hazard: use it only for the ratio, never mixed with our own volume series.
- **Rate limits / terms:** the automation guide states FINRA *"neither limits nor guides
  firms on how to access the data programmatically"* and gives curl/Postman examples. I found
  **no published rate limit** for this dataset. **[UNVERIFIED — absence of a documented limit
  is not a guarantee of no limit.]** There is a discrepancy in FINRA's own pages about the
  interactive grid depth: one page says "five rolling years", another says "one rolling
  year". The downloadable archive is the thing to use either way.

### 5b. Settlement date vs publication date — the exact rule

- **Reporting settlement dates:** twice monthly — the settlement date corresponding to the
  **15th of each month** and the **last business day of the month**, adjusted when those fall
  on a non-settlement day. FINRA publishes the exact list each calendar year at
  `https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest`.
- **Member reporting deadline:** *"All short interest positions must be reported by 6 p.m.
  Eastern Time on the second business day after the reporting settlement date."*
- **PUBLICATION:** *"the short interest data is compiled for each security and provided for
  publication on the 7th business day after the reporting settlement date."*
- **Worked example from FINRA's own 2025 schedule:** settlement **Friday 14 Nov** → due
  **Tuesday 18 Nov, 6pm** → **publication Tuesday 25 Nov**. That is a **7-business-day /
  11-calendar-day** gap between the date the data is *about* and the date it exists.
- I found **no** statement that the May-2024 move to T+1 settlement changed this rule.
  FINRA's current schedule page carries no T+1 note. **[UNVERIFIED — I could not confirm
  either way; a runner should read the settlement-date list FINRA publishes per year rather
  than deriving dates from a rule of thumb, which sidesteps the question entirely.]**

### 5c. Frequency, and the pending change

- **Current:** twice monthly, under FINRA Rule 4560.
- **PENDING RULE CHANGE — SR-FINRA-2026-012**, filed with the SEC 1 May 2026, Federal
  Register notice 18 May 2026. FINRA proposes to (i) require **weekly** rather than
  bi-monthly reporting, (ii) cut the turnaround from two business days to **one**, so that
  short interest would be **published weekly, five business days after the settlement date**;
  (iii) capture positions arising from customer securities-loan/arranged-financing
  obligations that are currently outside the definition; and (iv) adopt new Rule 4321
  requiring monthly reporting of daily fail-to-deliver allocations (regulatory use, **not**
  publicly disseminated). **As of 2026-09-09 this is proposed, not effective** — FINRA states
  it *"will announce the effective date of the proposed rule change in a Regulatory Notice."*
  A study built now would sit across a cadence break if this is adopted mid-sample.
- **SEC Rule 13f-2 / Form SHO** (monthly manager-level short positions, published by the SEC
  in aggregated form) is **not going to help**: adopted Oct 2023, compliance deferred twice,
  most recently on 3 Dec 2025 to **2 January 2028**, first filings due **14 February 2028**.

### 5d. DELISTED NAMES — the decisive question

**Answer: a qualified YES on the archive structure, but a hard NO on the last observation of
every dying name, and a hard NO for the free per-symbol routes.**

1. **The FINRA archive is point-in-time and therefore does NOT survivorship-bias by
   construction.** Files and API results are keyed on `settlementDate` and return the full
   cross-section of symbols that reported on that date. A name that traded in 2022 and
   delisted in 2024 is present in the 2022 files. This is the right shape for a
   dead-inclusive fixture.

2. **BUT the final cycle before a symbol is deleted is MISSING BY RULE.** From FINRA's own
   May-2026 SEC filing, §C "Short Interest Reporting for Securities with Deleted Symbols":

   > *"Currently, if a security no longer is assigned a security symbol as of a designated
   > short interest reporting settlement date, members do not include that security in their
   > reported short interest data (due to the absence of a valid symbol on the date that
   > short interest is assessed)."*

   FINRA is *proposing* to fix this ("members must report their gross short positions in the
   security as of the last settlement date for which a symbol was in effect") — proposed,
   not in force. **For our 43.5%-dead fixture this is a systematic, non-random hole located
   at exactly the event we care about most.** A name whose symbol is deleted between
   settlement dates simply vanishes from the file; a `bfill`/`ffill` join would silently
   carry a stale short interest through the terminal window, and a dropna would delete the
   dying names — i.e. it would re-create the survivorship bias in the *time series* even
   though the *cross-section* is clean.

3. **The free per-symbol routes ARE survivorship-biased and must not be used.** Nasdaq's
   free access is a per-security query on nasdaqtrader.com / nasdaq.com covering *"a rolling
   12 months"* for *currently listed* symbols; the bulk comma-delimited file is a **paid SFTP
   subscription**. Querying by ticker against a live-symbol endpoint returns nothing for a
   delisted name — joining that to our fixture would reintroduce exactly the bias the fixture
   was built to remove. **Use snapshot archives keyed on date, never per-symbol lookups.**

4. **NYSE.** I could not locate a free bulk historical NYSE short interest file. NYSE
   publishes consolidated short interest reports as periodic documents/press releases and
   sells data products. Since June 2021 the FINRA consolidated file supersedes the need.
   **[UNVERIFIED — I did not exhaustively search NYSE's data-products catalogue.]**

5. **TICKER REUSE is unmitigable with this file.** The file carries **symbol + truncated
   issue name and nothing else** — no CUSIP, no CIK, no permno. A ticker freed by a
   delisting can be reassigned within months. Any join to our fixture must be validated on
   both symbol *and* an independent check (issue-name similarity, listing-date interval, or
   a symbol→CUSIP crosswalk built from the SEC FTD file, which *does* carry CUSIP — see §7).

---

## 6. The look-ahead traps — rules a runner must follow

1. **Rank on the PUBLICATION date, never the settlement date.** The data does not exist
   until the 7th business day after the settlement date it describes. A signal derived from
   the 14 Nov settlement file may first be read on a bar dated **25 Nov or later**. Using the
   settlement date as the as-of date buys an 11-calendar-day forward look on every
   observation, for the whole sample.
2. **Take the publication date from FINRA's published schedule, not from a computed
   "+7 business days".** Holidays, the T+1 transition, and FINRA's own adjustments make the
   arithmetic unreliable. Hard-code the settlement→publication map from FINRA's per-year
   tables and **assert** that every joined observation's publication date is strictly less
   than the bar date. A second implementation that re-derives the held set from the
   publication-keyed panel without calling the join function is the lag audit this programme
   already requires (`run_overnight_long.py` pattern 1).
3. **Assert the assertion fires.** Shift the publication date one bar *earlier* on a
   deliberately broken panel and confirm the lag audit raises. Per
   `break-what-the-assertion-reads`, break the *date comparison*, not the variable's name.
4. **Join on symbol AND a listing-interval check.** No CUSIP exists in the FINRA file.
   Require that the fixture's symbol was alive on the file's settlement date; reject any
   match where the fixture's listing interval does not contain the settlement date. Log the
   rejected count — if it is not small, the ticker-reuse problem is live.
5. **Never forward-fill through a symbol deletion.** The last cycle before deletion is absent
   by rule (§5d.2). Treat a symbol that disappears from a settlement file as *missing*, not
   as *unchanged*. Explicitly test both handlings and report the difference: if the result
   moves, the result is about the missing-data rule, not about short interest.
6. **Recompute days-to-cover; do not use `daysToCoverNumber`.** It is floored at 1.00, capped
   at 999.99 and N/A at zero volume. A censored variable will silently compress the top decile
   — the exact decile the study is about.
7. **Do not mix FINRA's `averageShortShareNumber` with our own volume series.** Different
   corporate-action basis. Use FINRA's numerator over FINRA's denominator, or ours over ours,
   and say which.
8. **Pre-register the sample as June 2021 onward** and report `n_eff` in semi-monthly
   observations, not in bars. ~126 observations is the honest N for anything using
   exchange-listed free data, and a null must be built on that N, not on the bar count.
9. **Do not assume the cadence is constant.** If SR-FINRA-2026-012 is adopted mid-sample the
   frequency changes from semi-monthly to weekly. Assert the observed inter-settlement gap
   distribution matches the declared cadence.

---

## 7. FTDs and Reg SHO as an alternative

**This is the better free dataset for our fixture, and it was not the lead.**

**SEC fails-to-deliver data** — `https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data`

- **Coverage: February 2004 → present** (files listed through Aug 2026). This *does* span our
  whole 2010-01-04 → 2026-08-26 fixture.
- **Format:** pipe-delimited text inside ZIP, one file per half-month, containing **daily**
  records.
- **Fields:** Settlement Date | **CUSIP** | Symbol | Quantity (fails) | Description | Price
  (previous day's close). **It carries CUSIP**, which makes it the natural source for a
  symbol→CUSIP crosswalk to defuse the ticker-reuse problem in §6.4.
- **Release lag:** first half of a month published at month-end; second half around the 15th
  of the following month. So the lag is comparable to short interest — same publication-date
  discipline applies.
- **Point-in-time:** files are keyed on settlement date, so delisted names are retained.
- **SEC's own caveat, which must be quoted in any record that uses it:** *"fails-to-deliver
  can occur for a number of reasons on both long and short sales. Therefore, fails-to-deliver
  are not necessarily the result of short selling, and are not evidence of abusive short
  selling or 'naked' short selling."* Also: fails are **cumulative outstanding**, not a daily
  flow — *"a cumulative number of all fails outstanding until that day, plus new fails that
  occur that day, less fails that settle that day."*

**Predictive content — weak and contested.** Fotak, Raman & Yadav (*JFE* 114(3):493–516,
2014), 1,492 NYSE stocks over 42 months 2005–2008, find FTDs *improve* liquidity and pricing
efficiency and *reduce* return volatility — i.e. the opposite of the folk story. Boulton &
Braga-Alves report that returns are typically **positive** just before periods of increased
naked shorting that produce persistent fails and **remain positive for several weeks
afterwards** — which, read against our lead, is the wrong sign for a short book and the
*right* sign for an exclusion filter. Devos et al. (2010) and Lecce et al. (2012, ASX) find
negative abnormal returns under specific conditions. **There is no consensus and no clean US
long-short magnitude I could cite.** **[The Boulton & Braga-Alves and Devos/Lecce lines are
from search summaries; I did not read those papers. UNVERIFIED.]**

**Reg SHO threshold lists** are published daily and free by Nasdaq, NYSE, Cboe and FINRA
(OTC), but each venue publishes only its own listings and I found no consolidated free
historical archive with a stated start date. Boulton & Braga-Alves argue threshold-list
stocks tend to be *overpriced*, again the wrong direction for a short book.

**FINRA daily short-sale VOLUME files** — a third free dataset, and the one with the best
fixture coverage:
`https://cdn.finra.org/equity/regsho/daily/CNMSshvol{YYYYMMDD}.txt`
(catalogue: `https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data/daily-short-sale-volume-files`).
Daily, symbol-level short volume / total volume, posted by 6pm ET the same trade date — so a
**one-day** publication lag rather than eleven. **Consolidated NMS files start 2018-08-01**;
before that, per-venue files (FNSQ/FNYX/FORF etc.) exist back to 2009 and would have to be
summed across a venue set that changes over time. This measures short-selling **flow**, not
the **stock** of short interest, so it is not a days-to-cover substitute — but it is daily,
point-in-time, free, and reaches much further back than the consolidated short-interest file.
**If the programme wants a first non-price variable, this is the cheapest one to test.**

---

## 8. Does it transfer to OUR universe — bluntly

**No, not as a directional signal, and only marginally as the exclusion filter it was
proposed for. Five reasons, in descending severity.**

1. **The data does not reach the fixture.** Free exchange-listed short interest starts **June
   2021**. Our fixture is 2010-01-04 to 2026-08-26. That is ~31% of the fixture, and the
   available slice is the *post-crowding, post-publication* era in which every cost study
   says the residual is zero. Any result would be a 5-year, ~126-observation result, and D373's
   rule on finite-draw nulls plus the small N makes decisiveness very hard to reach. This is
   a data-availability verdict, not an opinion about the anomaly.

2. **The dead names lose their last observation.** 43.5% of the fixture delists or collapses.
   FINRA's own filing says a security with a deleted symbol is simply omitted from the report
   — and FINRA is only now proposing to fix that. The terminal window of every dying name,
   which is where a squeeze-exclusion filter would earn its keep, is the window with no data.
   This is not a bias we can bound; it is a hole located on the treatment.

3. **The price floor removes the effect.** The literature's money is equal-weighted and
   small: −215 bp/mo EW vs −39 bp/mo VW and insignificant (Asquith et al.). We are
   equal-weighted, which sounds favourable — but the EW premium is generated by the microcap
   and sub-$5 tail that our $5 floor and dollar-volume window exclude by design, and that
   Drechsler explicitly removes (bottom 10% of size *and* price) before his results even
   start. Per-share IBKR costs make that tail untradeable anyway: at 26 bp/side for a $2
   stock, the cost wall arrives before the signal does. This is the same wall that killed
   D284, and per `construction-vs-axis` I note the failure would be of *this* construction on
   *this* universe — not of the axis.

4. **The borrow leg is where the money is and we cannot get it.** BLN: all short-side alpha
   in the 14.3% Special. Muravyev: no gross profit at all once the 12% high-fee stock-dates
   are excluded. A retail book is structurally in the other 86–88%, where the measured
   short-side return is zero *before* costs. The programme's short side has failed because
   its pool rises; the literature's answer is that the pool that *falls* is the pool you
   cannot borrow.

5. **The exclusionary use is the survivor, and it is thin.** The argument for it is genuinely
   better than a fresh punt — it targets a documented, measured failure. But: (a) squeezes
   are rare, ~9.9% of unique US stocks per quarter, so a filter keyed on squeeze-proneness
   removes a lot of book to avoid an uncommon event, and the trade only pays if the avoided
   losses are very fat-tailed — which is testable in our own data *before* buying any
   external variable; (b) short interest is a **non-monotone** proxy for the fee (BLN's
   U-shape: both extreme-high and extreme-low SI names are more often special), so a
   high-DTC exclusion is a blunt instrument for the mechanism; (c) the variable that
   *directly* measures the squeeze mechanism is the borrow fee / utilisation, and there is no
   free historical source for it. IBKR's Short Stock Availability Tool exposes current
   availability and per-symbol "historical indicative borrow rates" as CSV, but it is
   account-gated and per-symbol — **I could not establish that a bulk historical fee panel is
   obtainable free. [UNVERIFIED]**

**What I would actually do with this, if anything.** Per `stage-0-premise-check`, before
buying any of this: measure, in our own fixture, the persistence and magnitude of the
programme's stated failure — how much of the short side's loss is concentrated in names with
large positive terminal moves, and what fraction of book those names are. If that
concentration is not large, no exclusion filter of any construction can pay, and N1 dies for
free. If it *is* large, the cheapest external test is **FINRA daily short-sale volume**
(free, daily, one-day lag, point-in-time, 2018-08 consolidated / 2009 per-venue) rather than
short interest — and the FTD file (2004→, carries CUSIP) as the crosswalk that makes any
symbol join safe. Per `signal-criterion-and-avenue-closure` this is a note on constructions
and data availability; **only the principal closes the axis.**

---

## 9. Sources

**Anomaly literature**
- Asquith, Pathak & Ritter, "Short interest, institutional ownership, and stock returns", *JFE* 78(2):243–276, 2005 — https://www.sciencedirect.com/science/article/abs/pii/S0304405X05001170 · free draft https://site.warrington.ufl.edu/ritter/files/2015/04/Short-interest-institutional-ownership-and-stock-returns-2005-08.pdf **[PEER-REVIEWED]** *(abstract/summary only — full text not read)*
- Boehmer, Huszar & Jordan, "The good news in short interest", *JFE* 96(1):80–97, 2010 — https://econpapers.repec.org/article/eeejfinec/v_3a96_3ay_3a2010_3ai_3a1_3ap_3a80-97.htm **[PEER-REVIEWED]** *(abstract only)*
- Hong, Li, Ni, Scheinkman & Yan, "Days to Cover and Stock Returns", NBER WP 21166, 2015 — https://www.nber.org/papers/w21166 · PDF https://www.nber.org/system/files/working_papers/w21166/w21166.pdf **[WORKING PAPER]** *(abstract/summary only)*
- Drechsler & Drechsler, "The Shorting Premium and Asset Pricing Anomalies", NBER WP 20282, 2014 — https://www.nber.org/system/files/working_papers/w20282/w20282.pdf **[WORKING PAPER]** *(full text read; Tables 2, 8 and §2 quoted)*
- Beneish, Lee & Nichols, "In short supply: Short-sellers and stock returns", *JAE* 60(2):33–57, 2015 — https://accounting.wharton.upenn.edu/wp-content/uploads/2015/04/BeneishLeeNichols.pdf **[PEER-REVIEWED]** *(full working-paper text read; Table 6 Panel A transcribed)*
- Muravyev, Pearson & Pollet, "Anomalies and Their Short-Sale Costs", *Journal of Finance* 80(6):3639–3694, 2025 — https://onlinelibrary.wiley.com/doi/10.1111/jofi.13501 · SSRN https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4266059 **[PEER-REVIEWED]** *(paywalled — abstract and search summaries only; the 0.14%/−0.01% and 12% figures were consistent across three independent summaries but I did not read the paper)*
- Engelberg, Reed & Ringgenberg, "Short-Selling Risk", *Journal of Finance* 73(2):755–786, 2018 — https://rady.ucsd.edu/faculty/directory/engelberg/pub/portfolios/SHORT_RISK.pdf **[PEER-REVIEWED]** *(abstract only)*
- Chen & Velikov, "Zeroing in on the Expected Returns of Anomalies" — https://www.ssrn.com/abstract=3073681 **[PEER-REVIEWED / WORKING PAPER]** *(summary only)*
- McLean & Pontiff (2016) post-publication decay — **[UNVERIFIED — not opened this session]**
- "How prevalent are short squeezes? Evidence from the US and Europe", *J. Banking & Finance*, 2025 — https://www.sciencedirect.com/science/article/pii/S0378426625000561 **[PEER-REVIEWED]** *(abstract only)*
- Fotak, Raman & Yadav, "Fails-to-deliver, short selling, and market quality", *JFE* 114(3):493–516, 2014 — https://www.ssrn.com/abstract=1573163 **[PEER-REVIEWED]** *(abstract only)*
- Boulton & Braga-Alves, "Naked Short Selling and Market Returns" — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1373813 **[WORKING PAPER / UNVERIFIED — search summary only]**

**Primary data and regulatory documents**
- FINRA, Equity Short Interest files — https://www.finra.org/finra-data/browse-catalog/equity-short-interest/files **[PRIMARY DATA DOC]**
- FINRA, About Equity Short Interest (settlement/publication rule) — https://www.finra.org/finra-data/browse-catalog/equity-short-interest **[PRIMARY DATA DOC]**
- FINRA, Short Interest Reporting deadlines and per-year settlement/due/publication tables — https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest **[PRIMARY DATA DOC]**
- FINRA, Equity Short Interest Data File Download & API metadata (full data dictionary; confirms symbol-only, DTC censoring) — https://www.finra.org/sites/default/files/Equity_Short_Interest_Data_File_Download_API.pdf **[PRIMARY DATA DOC]** *(read in full)*
- FINRA, SR-FINRA-2026-012 (weekly reporting; §C deleted symbols) — https://www.finra.org/sites/default/files/2026-05/SR-FINRA-2026-012.pdf · Federal Register notice 2026-05-18 https://www.federalregister.gov/documents/2026/05/18/2026-09864/ **[PRIMARY DATA DOC]** *(read in full; §C quoted verbatim)*
- FINRA, Daily Short Sale Volume Files — https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data/daily-short-sale-volume-files **[PRIMARY DATA DOC]**
- SEC, Fails-to-Deliver Data — https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data **[PRIMARY DATA DOC]**
- SEC, Rule 13f-2 / Form SHO compliance extension to Jan 2028 (Crenshaw statement, 2025-12-03) — https://www.sec.gov/newsroom/speeches-statements/crenshaw-statement-extension-compliance-dates-120325 **[PRIMARY DATA DOC]**
- Nasdaq Trader, Short Interest (rolling 12 months free per issue; bulk file = paid SFTP) — https://www.nasdaqtrader.com/Trader.aspx?id=ShortInterest **[PRIMARY DATA DOC]**
- Interactive Brokers, Short-Securities Availability — https://www.interactivebrokers.com/en/trading/short-securities-availability.php **[SALES INSTRUMENT / broker product page]** *(bulk historical fee panel availability UNVERIFIED)*

**Labelled sales instruments — cited nowhere above as evidence, listed for completeness**
- Alpha Architect, "The Good News in Short Interest" — https://alphaarchitect.com/the-good-news-in-short-interest/ **[SALES INSTRUMENT]**
- Quantpedia short interest strategy pages — https://quantpedia.com/strategies/short-interest-effect-long-short-version **[SALES INSTRUMENT]**
- IHS Markit, "US Short Squeeze Model" and "Short Interest, Crowding and Liquidity Crises" — vendor whitepapers **[SALES INSTRUMENT]**
- Apify / QuantQuote short-interest scrapers and APIs — **[SALES INSTRUMENT]**

**Safety note.** Nothing encountered during this research contained text addressed to me or
instructing me to act. All pages were read as data. No files were downloaded to the project,
no forms submitted, no accounts created. Three source PDFs were fetched into the session's
own tool-results cache by the fetch tool and read there.
