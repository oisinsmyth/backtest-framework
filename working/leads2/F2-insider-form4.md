# F2 — SEC Form 4 insider transactions: external evidence

*Commissioned 2026-09-09. Research brief, not a measurement. Under the quarantine contract in
[`README.md`](README.md) this closes nothing and admits nothing.*

---

## 1. Verdict

**The data is excellent and the anomaly is probably not.** The Form 4 pull is the easiest data
acquisition this programme has ever been offered — the SEC publishes the *whole* Section 16 corpus
back to 2006Q1 as ~67 quarterly tab-delimited ZIPs of ~10–14 MB each (verified live, HTTP 200,
2010q1 through 2026q2), the issuer's **ticker travels inside the filing** (`ISSUERTRADINGSYMBOL`,
NOT NULL) so the CIK↔ticker map is point-in-time and dead-inclusive *by construction*, and the
filing date and acceptance timestamp make look-ahead a solved problem rather than a convention.
`d331_edgar_deals.py` is not even needed for the bulk history. **But the return evidence points the
wrong way for us.** The canonical magnitudes (Jeng–Metrick–Zeckhauser ~6%/yr on purchases 1975–1996;
Cohen–Malloy–Pomorski 180 bp/month equal-weight long–short 1986–2007) are pre-2008, gross of cost,
and concentrated in exactly the small/illiquid/low-priced tail our $5 floor and per-share commissions
punish. The strongest post-2010 work says the alpha lives in the window we cannot trade: **70–80% of
it dissipates between the transaction date and the next session, before disclosure**
(Ozlen–Batumoglu, unverified); a peer-reviewed 2025 study finds filing-date profits **"vanish and
even become negative when limiting the tradable dollar amount to a reasonable size," and negatively
correlated with liquidity, *before* transaction costs** (Oenschläger–Möllenhoff, FRL); and
Cziraki–Gider show **the insiders themselves** clear a median of **$464 a year** in abnormal dollar
profit. Set against that, one 2026 practitioner-journal paper claims a surviving 2011–2023 strategy —
at 10 bp/side, 12 concurrent positions, 29.3% vol and a median-revenue-$105M universe, i.e. every
knob this programme has already watched kill a lead. **My recommendation is that this is worth
exactly one Stage-0 premise measurement and not a study**, and the Stage-0 gate is not a return
number at all: it is the dead-name ticker match rate.

---

## 2. The anomaly as documented

| source | year | sample | universe | leg | magnitude | cost treatment |
|---|---|---|---|---|---|---|
| Seyhun, *JFE* [PEER-REVIEWED] | 1986 | 1975–1981 | US, all exchanges | net buy vs net sell | +4.3% / −2.2% over 300 days | none in headline; his 1998 book work says costs eat most of it |
| Rozeff & Zaman, *J. Business* [PEER-REVIEWED] | 1988 | 1973–1982 | US | outsiders mimicking | **outsider profits zero or negative at 2% round-trip cost**; insider profits ~3%/yr after 2% cost | **explicit — this is the paper's point** |
| Lakonishok & Lee, *RFS* [PEER-REVIEWED] | 2001 | 1975–1995 | NYSE/AMEX/Nasdaq | **purchases only**; sales show no predictive ability | predictability "driven by smaller firms"; commonly cited as ~4.8% strong-buy vs strong-sell year 1 (**I could not verify the 4.8% figure from a primary source**) | none |
| Jeng, Metrick & Zeckhauser, *REStat* [PEER-REVIEWED] | 2003 | 1975–1996 | US | **purchases >50 bp/month (~6%/yr); sales insignificant** | performance-evaluation method on insiders' own returns | none |
| Cohen, Malloy & Pomorski, *JF* / NBER w16454 [PEER-REVIEWED] | 2012 (WP 2010) | **1986–2007** | Thomson Reuters Section 16 (Form 4); sample tilted **to larger caps**, ~⅓ of all insider transactions | opportunistic long–short (buys − sells) | **VW 82 bp/mo (t=2.15, 9.8%/yr); EW 180 bp/mo (t=6.07, 21.6%/yr)**. Routine: VW −20 bp (t=−0.57), EW 43 bp (t=1.73) | **none** |
| Cziraki & Gider, *Rev. Finance* [PEER-REVIEWED] | 2021 (WP 2019) | **1986–2013**, ~1.3M transactions | Thomson Reuters Table 1 (Form 4) | all | mean 0.9% / **median 0.6% abnormal return over 20 days**; median trade **$129,000**; **median insider abnormal profit $464/yr** | none, but the dollar framing *is* the cost argument |
| Kang, Kim & Wang; Alldredge et al. [PEER-REVIEWED / WORKING PAPER] | 2018–19 | US | cluster vs solo purchases | cluster buys | 21-day AR **3.8% cluster vs 2.0% non-cluster**; peer-purchase-within-2-days +2.1% vs +1.2% solo (**sample periods not verified from primary**) | none |
| Schroeder & Krause, *J. Investing* [PEER-REVIEWED, practitioner journal] | 2026 | **2011–2023** (IS 2011–19, OOS 2020–23), 1.8M Form 4 filings, 9,166 companies | US, **median revenue $105M** | purchases | 17.4% CAGR vs 12.8% SPX; 5-day CAR 3.42%; **vol 29.3% vs 14.6%, maxDD −38.7%**; ≤12 concurrent positions, ~400 trades/yr | **0.1% (10 bp) on entry and exit** |
| Ozlen & Batumoglu, SSRN 5966834 [WORKING PAPER, **UNVERIFIED**] | 2025/26 | not verified | US Form 4 | all | **70–80% of total alpha dissipates between transaction date and the following trading day** — before disclosure | n/a |
| Oenschläger & Möllenhoff, *Finance Research Letters* 72(C) [PEER-REVIEWED] | 2025 | not verified (post-2010 US) | US Form 4 filings | filing-date mimicking | returns "vanish and even become negative when limiting the tradable dollar amount for each trading signal to a reasonable size"; **negatively correlated with stock liquidity** | **"even before considering transaction costs"** |
| Quantinsti blog event study [UNVERIFIED, blog] | 2026 | **2022-01-01 – 2026-06-30**; 1,345,036 rows → **7,405 issuer-day signals** (C-suite, code-P, non-10b5-1, ≥$10k) | US, Yahoo prices | purchases, **filing-date+1 entry** | **CAR +0.534% (1d, t=6.46), +1.009% (5d, t=5.05), +0.980% (21d, t=1.68, CI −0.19% to +2.15%), +1.103% (63d, t=1.19, CI includes zero)** | **none applied** |

**Which leg carries the money.** The pre-2008 consensus — purchases informative, sales noise — is
well supported (Lakonishok–Lee; Jeng–Metrick–Zeckhauser; the diversification/tax/10b5-1 story).
**Cohen–Malloy–Pomorski explicitly contradict it**: they say *over half* of the improvement from the
opportunistic filter comes from **opportunistic sells outperforming routine sells**. So the correct
statement is: *unconditional* sales are noise; *sales stripped of the routine/scheduled component*
carry information. For a long-only retail book with per-share costs and borrow that distinction is
academic — but it means "sales are noise" is not a safe prior, it is a prior that survives only
without the filter.

---

## 3. Post-2010 survival and cost — the decisive section

**There is no clean, cost-honest, peer-reviewed demonstration that this survives post-2010 in a
form we could trade.** The evidence splits three ways.

**(a) The structural argument that it cannot survive at the filing date.** Ozlen & Batumoglu's
finding — 70–80% of alpha gone between transaction date and the next session, *before* the Form 4 is
public — is the single most important claim in this brief if true, because it says every
transaction-date backtest measures the value of *private* information and nothing tradeable. I could
**not** verify it: SSRN returned HTTP 403, and the one secondary write-up I reached
(tommijohnsen.substack.com) carried the 70–80% quote but **no sample period, universe, or method** —
its performance numbers were the blogger's own 5-day pilot, not the paper's. **Treat as unverified.**
Note the mechanism is independently plausible and pre-dates the paper: CMP's own footnote 15 shows
their results are insensitive to timing convention *because* median reporting lag was 3 days even
pre-SOX, and the SOX 2-day rule (effective 2002-08-29) compressed it further.

**(b) The peer-reviewed capacity/liquidity kill.** Oenschläger & Möllenhoff (*FRL* 72(C), 2025) is
the strongest published negative that is actually peer-reviewed and post-2010. Their result is
precisely the shape that has killed leads here before: the effect is real in percentage terms at
zero size, and **negative once you require a realistic dollar amount per signal, before costs**,
because it is negatively correlated with liquidity. I could only read the abstract (ScienceDirect
paywall) — **magnitudes and sample period unverified.**

**(c) The one positive.** Schroeder & Krause (*Journal of Investing*, June 2026) claim survival
2011–2023 with a genuine 2020–23 out-of-sample. **Read it sceptically.** Via the Swedroe summary:
17.4% CAGR at **29.3% annualised vol** with a −38.7% drawdown, and a claimed **Sharpe of 1.88** —
17.4/29.3 is ~0.6, so the 1.88 is not the annual Sharpe of the reported series and is either a
different frequency or a different statistic. Costs are 10 bp/side, versus the **33.8 bp/side that
D285 measured (Corwin–Schultz) on the names actually held**. The book is ≤12 concurrent positions in
a median-$105M-revenue universe. Every one of those — concentration, small caps, an assumed rather
than measured cost, a headline ratio that does not reconcile with its own vol — is a flag this
record has raised before. I could not read the paper (paywalled).

**(d) The neutral post-2010 datapoint.** The quantinsti filing-date event study (2022–2026, 7,405
C-suite code-P signals, entry at the first session strictly after `FILING_DATE`) is methodologically
the closest thing to what we would build, and its answer is: **+0.53% at 1 day and +1.01% at 5 days
with strong t-stats, and nothing you can distinguish from zero at 21 or 63 days.** It also reports
the direct lookahead measurement: transaction-date entry beats filing-date entry by **−1.721 pp at
21 sessions** [−2.007, −1.436] — i.e. **1.7 points of the 21-day "alpha" is pure lookahead**. It is a
blog, uses Yahoo prices with no point-in-time security master, and applies **no costs** — but its
author states the survivorship hazard himself: missing Yahoo histories "can correlate with distress,
delisting and extreme outcomes," possibly MNAR.

**Cost arithmetic, stated plainly.** Take the most favourable honest post-2010 number: ~1.0% gross
at 5 days. Against a measured 33.8 bp/side round trip that is **67.6 bp of cost against 100 bp of
gross** — a 1.5× coverage ratio *before* any slippage, on a signal whose 21-day CI already includes
zero, in a universe the same literature says is more profitable the *less* liquid it is. At the $5
floor, IBKR's $0.005/share tiered commission alone is **10 bp/side**, and the fixed-per-share
structure means the cheap names carrying the effect are the expensive names to trade.

**Publication decay is the background rate.** McLean & Pontiff (2016): anomaly returns fall ~58%
post-publication. Hou, Xue & Zhang (2020): 65% of anomalies fail replication. Nothing about Form 4
gives it a structural barrier — it is free, XML, instantly parsed, and has been for two decades.

---

## 4. What separates signal from noise

Ranked by strength of evidence:

1. **Transaction code.** Not a "filter" so much as the definition of the sample. Only **`P` (open
   market or private purchase)** and **`S` (open market or private sale)** are discretionary market
   trades. `A` (grant/award), `M` (option exercise), `F` (tax withholding), `G` (gift), `D`, `C`,
   `X` are compensation mechanics and carry no directional information. **A study that does not
   filter to `P` is not studying insider trading.** Nearly every headline magnitude above is
   `P`-conditioned.
2. **Opportunistic vs routine (CMP 2012).** The strongest single result: routine trades are ~55% of
   the universe and earn essentially zero (VW −20 bp/mo); the opportunistic residue carries all of
   it. **But the classification requires three consecutive prior years of same-calendar-month
   trading history per insider**, which cut CMP's own sample to ~⅓ and tilted it toward large caps
   with fewer micro-caps than CRSP. On a 43.5%-dead fixture, insiders at names that die young cannot
   accumulate the history — **the filter is a survivorship funnel**, and that is a specific,
   testable hazard, not a general worry.
3. **Cluster buys.** Multiple insiders at the same firm within a short window. Kang–Kim–Wang: 21-day
   AR 3.8% (cluster) vs 2.0% (non-cluster); Alldredge et al. (*JFR* 2019): clustered purchases
   followed by >2% abnormal return over the subsequent month, clustering greatest under low investor
   attention and high information asymmetry. Attractive for us because it is **computable from the
   pulled data with no external history** — just `(ISSUERCIK, TRANS_DATE)` counts across distinct
   `RPTOWNERCIK` — and because "low investor attention" is exactly the corner a retail book can hold.
   Sample periods unverified.
4. **Officer/director vs 10% owner.** `RPTOWNER_RELATIONSHIP` gives OFFICER / DIRECTOR /
   TENPERCENTOWNER / OTHER free. Evidence is weaker than folklore suggests: CMP find **no significant
   difference** between independent directors, senior insiders and inside directors once opportunism
   is controlled, citing Ravina & Sapienza (2010) that the executive-vs-independent-director gap is
   small. Ten-percent owners are the group most contaminated by fund mechanics.
5. **Trade size relative to holdings/salary.** Cziraki & Gider is the caution here, and it is a sharp
   one: **variables that predict percentage returns fail to predict dollar profits, because they are
   inversely related to quantities.** Insiders who trade rarely earn high *returns*; insiders who
   trade often earn large *dollars*. Their legally-imposed-discontinuity measure isolates 0.5% of
   insiders with median $2,500/yr. **The information is in the smallest trades.**

### Rule 10b5-1 and the 2023 structural break — dates, exactly

- **Rule 10b5-1 adopted August 2000.** Jagolinzer (*Management Science*, 2009) showed plans were
  *used* strategically: participants' sales followed positive and preceded negative performance,
  with larger abnormal returns than non-participating colleagues. So pre-2023, "under a plan" was
  **not** a clean noise label.
- **Final amendments (Release 33-11138, "Insider Trading Arrangements and Related Disclosures")
  effective 2023-02-27.** Mandatory cooling-off periods before trading may begin after plan adoption
  or modification, prohibitions on overlapping plans, director/officer certifications, and Item 408
  quarterly disclosure.
- **Section 16 reporting persons must comply with the amended Forms 4 and 5 for reports filed on or
  after 2023-04-01.** This is the date the **`aff10b5One` XML element / `AFF10B5ONE` checkbox**
  becomes observable. It is also when **bona fide gifts** moved from annual Form 5 to Form 4.
- **The SEC backfilled `AFF10B5ONE` into the SUBMISSION file of the 2023–2025 quarterly data sets in
  July 2025** (the `Last-Modified` on `2024q1_form345.zip` is 2025-07-22, consistent).
- **Consequence for us:** the 10b5-1 flag is available for **2023-04-01 onward only** — the last
  ~3.4 years of a 16.6-year fixture. Before that date it must be treated as *unobservable*, not
  *false*. Any runner that filters on it silently changes universe definition mid-sample. **This is a
  structural break inside our fixture and must be pre-registered as one.**
- **Post-amendment effect:** "Insider Trading After the 2022 Rule 10b5-1 Amendment" (*JAE*, 2026)
  reports that post-amendment, 10b5-1 sales are followed by **less negative** abnormal returns and
  insiders are less likely to sell under plans before earnings misses — i.e. the amendment worked,
  which means **the informativeness of the sell leg is lower after 2023 than before it**, on top of
  any decay.

---

## 5. Where the effect lives — size, price, liquidity

Every line of evidence points the same way, and it is the wrong way for us.

- **Lakonishok & Lee (2001):** predictability "driven by insiders' ability to predict returns in
  smaller firms."
- **Cohen–Malloy–Pomorski (2012):** the *opportunistic-vs-routine* distinction survives in both
  halves of the market-cap distribution — but the **magnitude** does not: **EW 180 bp/mo vs VW 82
  bp/mo**, a 2.2× gap that is the size tilt speaking. Their event-time 12-month four-leg spread is
  ~8% equal-weight against ~4% value-weight. And their own sample is *deliberately* tilted large,
  with fewer micro-caps than CRSP — so the EW/VW gap is measured on a large-tilted sample and the
  true small-cap concentration is likely worse.
- **Oenschläger & Möllenhoff (2025):** returns **negatively correlated with stock liquidity**, which
  "almost negat[es] a potentially profitable and scalable trading strategy even before considering
  transaction costs." This is the cleanest statement of the problem.
- **Microcap arXiv 2602.06198 [WORKING PAPER, low confidence]:** 2018–2024, **$30M–$500M market cap**,
  17,237 open-market purchases across 1,343 issuers, best cell mean CAR 6.3% — explicitly attributed
  to "slower information incorporation in illiquid markets." The effect is *most* visible exactly
  where our floor and our commissions are worst.
- **Cziraki & Gider:** median trade **$129,000**. The insider's own footprint is a median **5.08%**
  of trailing median daily dollar volume, with 23.8% of purchases exceeding 25% of ADV and 9.6%
  exceeding 100% (quantinsti). These are not liquid names.

**Nobody has published, that I could find, a breakdown by nominal share price** — which is the axis
that actually kills things here (D284). That gap is itself informative: the literature reports in
percentage abnormal return, and percentage returns are exactly the currency that hides a per-share
cost structure.

---

## 6. THE DATA

### 6a. How to pull it — and the answer is not the puller we own

**Use the SEC's structured "Insider Transactions Data Sets." It is the whole corpus in ~67 files.**

- **Landing page:** `https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets`
- **Coverage: January 2006 → current quarter**, extracted from the XML fillable portion of Forms 3,
  4 and 5. Our fixture starts 2010-01-04 — **fully covered with four years of run-up** for
  history-dependent filters.
- **URL pattern (verified live, HTTP 200):**
  `https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/{YYYY}q{Q}_form345.zip`
  — `2010q1` (13.77 MB), `2015q3` (8.91 MB), `2023q2` (10.74 MB), `2026q1` (13.87 MB) all return 200.
  **The most recent quarter is served from a different path**:
  `https://www.sec.gov/files/datastandardsinnovation/data/insider-transactions-data-sets/2026q2_form345.zip`
  (11.50 MB, 200) — the `structureddata` path 404s for `2026q2`. **A runner must try both paths.**
- **Total volume: 2010q1–2026q2 is 66 files at ~8–14 MB ≈ 700–900 MB zipped, ~66 HTTP requests.**
  At the SEC's 10 req/s ceiling this is a **sub-minute pull**, not a rate-limited crawl. The 8 req/s
  form-type crawler in `scripts/d331_edgar_deals.py` is the *wrong tool* for the history; it remains
  the right tool for a live daily tail.
- **Format:** eight tab-delimited UTF-8 text files per quarter — `SUBMISSION`, `REPORTINGOWNER`,
  `NONDERIV_TRANS`, `NONDERIV_HOLDING`, `DERIV_TRANS`, `DERIV_HOLDING`, `FOOTNOTES`,
  `OWNER_SIGNATURE` — plus a W3C tabular-data metadata file. Joined on `ACCESSION_NUMBER`.
- **Update cadence: quarterly.** Filings after 5:30pm ET on the last business day of a quarter land
  in the next release. **For anything live you need the daily route, not this one.**
- **SEC disclaimer, verbatim in substance:** the data is "as-filed," derived from registrant-provided
  information, "we cannot guarantee the accuracy," and may contain "redundancies, inconsistencies,
  and discrepancies relative to prior submissions."

**Alternative routes, and when each is right**

| route | URL | use |
|---|---|---|
| quarterly structured data sets | above | **the history. Use this.** |
| EDGAR full-index | `https://www.sec.gov/Archives/edgar/full-index/{YYYY}/QTR{n}/form.idx` (also `company.idx`, `master.idx`) | 1994Q3→present, quarter-to-date bridge; **filing-date granularity only, no transaction detail** |
| EDGAR daily-index | `https://www.sec.gov/Archives/edgar/daily-index/{YYYY}/QTR{n}/` | the live tail: today's Form 4 accessions, then fetch each `form4.xml` |
| per-filing XML | `https://www.sec.gov/Archives/edgar/data/{cik}/{accession-no-dashes}/form4.xml` | ground truth; **required if you want the acceptance timestamp or `aff10b5One` pre-July-2025** |
| filing index page/JSON | `.../{accession}-index.htm` | carries the **"Accepted" timestamp** the quarterly data sets omit |
| EDGAR full-text search | `https://www.sec.gov/edgar/search/`, API at `efts.sec.gov/LATEST/search-index?q=` | **2001-05-04→present**; **undocumented, no published schema or versioning commitment** — do not build on it |

**Rate limits / fair access [PRIMARY DATA DOC]:** SEC states a **maximum 10 requests per second**,
"carefully monitored to preserve equitable access," and requires a declared
`User-Agent: Sample Company Name AdminContact@domain.com`, plus `Accept-Encoding: gzip, deflate`.
The existing puller's 8 req/s is inside this.

### 6b. The identifier — and this is the good news

**`SUBMISSION.ISSUERTRADINGSYMBOL` — "Issuer trading symbol," VARCHAR2(10), NOT NULL.** It is
sourced from the `<issuerTradingSymbol>` element of the filing's own XML. I verified this on a live
filing: Apple's 2026-09-03 Form 4 contains `<issuerCik>0000320193</issuerCik>`,
`<issuerName>Apple Inc.</issuerName>`, `<issuerTradingSymbol>AAPL</issuerTradingSymbol>`.

**This means the CIK↔ticker mapping for Form 4 is point-in-time and dead-inclusive by construction.**
The ticker is what the issuer said its ticker was *on the day it filed*. A company that delisted in
2014 still carries its 2014 ticker in its 2014 filings, forever. **This is the same property that
made XBRL attractive elsewhere in this record, and it removes the survivorship trap without any
external mapping file.**

**Do NOT use the live mapping files for this.** For the record, what they are and why they fail here:

| file | contains | dead-name coverage |
|---|---|---|
| `https://www.sec.gov/files/company_tickers.json` | ticker ↔ CIK ↔ conformed name | **current registrants only — survivors.** SEC does not guarantee accuracy or scope |
| `https://www.sec.gov/files/company_tickers_exchange.json` | adds exchange | same limitation |
| `https://data.sec.gov/submissions/CIK##########.json` | current name, **former names**, tickers, exchanges, per-filing metadata incl. acceptance datetime | tickers/exchanges reflect *current* status; empty or stale for deregistered filers |
| `https://www.sec.gov/Archives/edgar/cik-lookup-data.txt` | **CIK ↔ entity NAME only**, historically cumulative, includes entities that no longer file | dead names present — **but no tickers**, so it cannot close the loop alone |

**The hazard the in-filing ticker does *not* remove: ticker recycling.** A ticker freed by a 2013
delisting can be reissued to an unrelated company by 2019. The join to our fixture must therefore be
**`(ticker, filing_date within the fixture's own listing interval for that name)`**, and the runner
should assert that each matched `(ticker, ISSUERCIK)` pair is unique within its matched date span —
a ticker mapping to two CIKs inside one name's life is a defect, not a merge.

### 6c. Amendments (4/A) and late filings

- `SUBMISSION.DOCUMENT_TYPE` distinguishes `4` from `4/A`; `DATE_OF_ORIG_SUB` gives the original
  filing date when the form is an amendment. **Both are in the quarterly data sets.**
- `NONDERIV_TRANS.TRANS_TIMELINESS` carries `E` = Early, `L` = **Late**, empty = on-time. **Lateness
  is a first-class field — it does not have to be inferred from date arithmetic.** (It is the filer's
  own assertion, so cross-check it against `FILING_DATE − TRANS_DATE > 2 business days`; disagreement
  is data, and worth counting before trusting either.)
- **I could not find a published, sourced statistic for the rate of 4/A amendments or the rate of
  late Form 4s post-SOX.** Practitioner sources say the 2-business-day open-market deadline is "the
  most commonly missed" Section 16 deadline and the SEC has run enforcement sweeps on it, but nobody
  put a number on it that I could verify. **This is a number the programme should simply count from
  the pulled data — it is three lines and it is our own fixture.**
- **The SEC data set is explicitly "as filed" including amendments** — so a naive load double-counts
  any transaction reported once on a `4` and again on a `4/A`.

---

## 7. The look-ahead rules, stated as rules a runner must follow

Three timestamps exist and they are not interchangeable.

| field | what it is | when it is knowable |
|---|---|---|
| `PERIOD_OF_REPORT` / `NONDERIV_TRANS.TRANS_DATE` | the date the insider traded | **NOT knowable then.** Private until the filing lands |
| `SUBMISSION.FILING_DATE` | date the filing was made | knowable **only after** the acceptance timestamp on that date |
| **acceptance timestamp** (`-index.htm` "Accepted"; `acceptanceDateTime` in `data.sec.gov/submissions/`) | the moment EDGAR accepted it | the actual public moment |

**R1 — Never key on the transaction date.** It is the single largest source of fake alpha in this
literature and it is measurable: filing-date entry underperforms transaction-date entry by
**1.721 pp at 21 sessions** (quantinsti, 2022–2026). Ozlen & Batumoglu put 70–80% of all alpha in
that window. **A study entered on `TRANS_DATE` is a study of information we do not have.**

**R2 — The acceptance timestamp, not the filing date, sets the first tradeable bar.** Verified worked
example: accession `0001140361-26-035636`, `PERIOD_OF_REPORT` 2026-09-01, `FILING_DATE` 2026-09-03,
**Accepted 2026-09-03 18:30:44 — after the close.** A runner entering at the 2026-09-03 close is
trading on a filing that was not yet public. Form 4s cluster in the late afternoon precisely because
the deadline is end-of-day.

> **The rule.** Let `t_acc` be the acceptance timestamp. The first tradeable bar is the **open of the
> first session strictly after `t_acc`**. On DAILY bars, that is: `entry_bar = filing_date + 1`
> whenever `t_acc` is at or after 16:00 ET (the majority case), and `filing_date` only if entering at
> that day's *close* and `t_acc < 16:00 ET`. **Since the quarterly data sets carry `FILING_DATE` but
> NOT the acceptance timestamp, the safe and simple rule for a bulk study is: enter at the open of
> `FILING_DATE + 1` session, unconditionally.** Any tighter rule requires pulling the acceptance
> timestamp per filing and must be justified in the pre-registration.

**R3 — Point-in-time reconstruction: a filing enters the signal state at `t_acc` and never before,
and an amendment enters at *its own* `t_acc`, not the original's.** Concretely:
- Build the event stream as `(entry_bar, issuer, payload)` and never re-sort by `TRANS_DATE`.
- **For `4/A`: do not retroactively correct the original.** As of the original's acceptance the
  market saw the original's numbers. A point-in-time book holds the original until the amendment's
  own acceptance bar, then updates from that bar forward. Restating history with the amendment is a
  look-ahead, and one that correlates with error-prone (small, distressed) filers.
- **De-duplicate forward, not backward**: an amendment supersedes for bars ≥ its acceptance; it does
  not delete the original from earlier bars.
- **Late filings (`TRANS_TIMELINESS = 'L'`) are not a data problem, they are the data.** A trade
  reported 40 days late is public 40 days late. Keying on `FILING_DATE` handles this automatically —
  which is another reason R1 matters: the late-filing subsample is exactly where transaction-date
  keying fabricates the most.

**R4 — The 10b5-1 flag does not exist before 2023-04-01.** Any filter on `AFF10B5ONE` / `aff10b5One`
must be written as a three-state variable (`true` / `false` / `unobservable`), and a study that uses
it must either restrict to 2023-04-01→2026-08-26 or pre-register how the unobservable era is
handled. **Silently treating pre-2023 as `false` changes the universe at a known date and will look
like a regime change.**

**R5 — Filter to `TRANS_CODE` in `{P}` (or `{P,S}`) explicitly, and assert the codes you excluded.**
`A`, `M`, `F`, `G`, `D`, `C`, `X`, `I`, `J` are compensation and administrative mechanics. Assert the
count dropped by each code and print it — a code-set that silently changes between runs is the same
class of defect as a fixture that changes basis.

---

## 8. Crowding and decay

**This is one of the most publicly consumed datasets in equities.** Free retail surfaces:
OpenInsider, SecForm4, Finviz, TipRanks, Quiver Quantitative, InsiderMonkey, MarketBeat. Paid
institutional feeds: **VerityData / InsiderScore** (states its clients are "hedge funds, long-only
asset managers, multi-manager platforms, and quant or quantamental firms") [SALES INSTRUMENT],
**2iQ Research** (founded 2002, >60,000 stocks, "top hedge funds to quantitative portfolio
managers") [SALES INSTRUMENT], **The Washington Service**, plus Bloomberg, FactSet and Refinitiv
carriage. **Everything in this brief that a vendor published, I have labelled as a sales instrument,
and I have used none of it as evidence.**

**The best crowding evidence is the ETF graveyard, because it is a live, cost-bearing test.**
- **Direxion Large Cap Insider Sentiment (INSD)** and siblings: liquidated 2013, the Trust citing
  "low level of assets and their inability to attract sufficient investment assets."
- **Guggenheim → Invesco Insider Sentiment ETF (NFO)**, tracking the Sabrient/Nasdaq US Insider
  Sentiment Index, ~$79–88M AUM, **liquidated: last creation 2020-02-07, trading ceased 2020-02-14**,
  in Invesco's 42-fund, $1.13bn closure round.
- **Direxion All Cap Insider Sentiment (KNOW)**: I could **not** confirm its current status either
  way — unverified.

Three publicly-traded, fully-costed implementations of "buy what insiders buy" existed and are gone.
That is not proof the signal died, and asset-gathering failure is not the same as performance
failure — Invesco's closure was explicitly a post-acquisition redundancy cull. **But it is the only
evidence in this brief from a vehicle that actually paid spreads.**

**Did publicity kill it?** I found no study that isolates *this* anomaly's post-publication decay.
The background rates apply — McLean & Pontiff's ~58% and Hou–Xue–Zhang's 65% replication failure —
and Form 4 has no structural barrier to arbitrage: free, XML, machine-parsed within seconds of
acceptance, for twenty-three years. **A master's thesis (Aalto) reportedly replicates CMP on
2008–2024 and finds alphas down ~60–70%, from ~1.2–1.6%/mo to ~0.3–0.4%/mo, with signs intact. I
attempted the PDF twice and got HTTP 403 both times — I could not verify a single number of it and
it is a master's thesis. Cite it to nobody.** If it is right, it is exactly the McLean–Pontiff rate,
and 30–40 bp/month gross does not clear 67.6 bp round-trip on a monthly-turnover book.

---

## 9. Does it transfer to OUR universe — bluntly

**Probably not, and the reasons are specific rather than atmospheric.**

1. **The effect is strongest where our floor cuts.** Every source that breaks it down says small,
   illiquid, and (by implication of price/size correlation) cheap. Our $5 floor plus a dollar-volume
   window removes precisely the microcap tail the arXiv working paper measures at 6.3% CAR. What
   remains is the half of the distribution where CMP measured **82 bp/mo value-weight, not 180
   equal-weight**.
2. **Per-share commissions bite hardest on the survivors of that cut.** A $5.50 name at
   $0.005/share is ~9 bp/side in commission alone before spread. D285's measured 33.8 bp/side on
   actually-held names is the number to plan against, not a 10 bp assumption. Round trip ~67.6 bp
   against a best-case honest 5-day gross of ~100 bp.
3. **Equal weighting is the one genuine fit.** CMP's EW result is 2.2× their VW result and the whole
   literature's effect is size-decreasing. This programme is equal-weighted by construction. That
   argues the *right* version of this test here is EW and small — which collides head-on with (1)
   and (2). **The construction that would work is the one the cost regime forbids.**
4. **The opportunistic/routine filter is a survivorship funnel on a 43.5%-dead fixture.** It needs
   three prior years of per-insider trading history. Names that die young cannot supply it. CMP's own
   sample shrank to ⅓ and tilted large. **On our fixture this filter would silently select survivors
   — the exact bias the fixture exists to remove.** Cluster-buy and code-`P` filters have no such
   requirement and should be preferred.
5. **The 2023-04-01 10b5-1 checkbox is a structural break inside our sample** — 3.4 years of a
   16.6-year window observe a variable the other 13.2 do not, and the *JAE* 2026 evidence says the
   underlying informativeness changed at that date too. Both lenses (path-invariant per-trade and the
   slot-limited book) need a pre/post split, not a pooled number.
6. **Event density is the unknown that decides feasibility.** ~1.8M Form 4 filings across 9,166
   companies over 2011–2023 is ~138k filings/yr; ~24–25% of insider trades are buys (Cziraki–Gider)
   and code-`P` is a subset of those. Restricted to 1,573 names this may or may not fill a slot book.
   **Nobody can tell you this from the literature — it is a count on our own data.**
7. **What is genuinely, unusually good here:** the look-ahead is solved by construction rather than
   convention, the dead-name identity problem is solved by the in-filing ticker, and the entire
   16.6-year history is a ~15-minute download. **If a premise number is going to be cheap to compute,
   it is this one.** That is an argument for measuring it, not for believing it.

---

## 10. The premise number to compute first

**Stage 0 gate, before any return is computed — the dead-name match rate.**

> Load `SUBMISSION` for 2010q1–2026q3. Join `ISSUERTRADINGSYMBOL` to the fixture's 1,573 names,
> restricted to each name's own listing interval. Report: **(i) the fraction of the 684 dead names
> that appear at least once, against the fraction of the 889 live names**; (ii) any ticker matching
> two distinct `ISSUERCIK`s inside one name's life. **If the dead-name hit rate is materially below
> the live-name hit rate, stop — the identity is broken and every downstream number is
> survivorship**, exactly as D347/D351 were. This is a pure counting exercise on a ~900 MB download
> and it costs nothing.

**Then, and only then, the premise number:**

> **The gross mean forward return per code-`P` open-market purchase event, entered at the OPEN of the
> `FILING_DATE + 1` session, held 1 / 5 / 21 / 63 bars, on the fixture's own eligible bars
> (`$5` floor + dollar-volume window), reported per TRADE (path-invariant) — split dead vs alive and
> by price bucket — against a time rotation of the event dates within the same eligibility mask.**

Report it under the house standard: gross **and** net side by side; mean **and median** (a mean below
its median means the tail is doing the work); the symmetric 1% trim on both tails; the number of
names to reach half the P&L; and the null's **p50 and p95** with the p95's bootstrap SE. Because the
rotated object here is a **per-name** event stream, the null group is not enumerable — the p95 bias
stands and only more draws touch it.

**The pass/fail this brief predicts.** The literature's honest post-2010 number is **+1.0% at 5 days
gross, with the 21-day CI containing zero, before costs, in a universe more liquid-averse than ours.**
Against a 67.6 bp round trip the 5-day cell has ~1.5× coverage and the 21-day cell has none. **A
result at 21 or 63 bars that clears the null decisively would contradict the best post-2010 evidence
I found and should be treated as a bug hunt first.** A 1–5 bar result that clears gross is the
expected outcome and settles nothing until net, price-split and slot-book lenses are on it.

---

## 11. Sources

**Primary SEC documentation**
- [PRIMARY DATA DOC] Insider Transactions Data Sets — https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets
- [PRIMARY DATA DOC] Insider Transactions Data Sets readme (table/field definitions, trans-code and timeliness lists) — https://www.sec.gov/files/insider_transactions_readme.pdf
- [PRIMARY DATA DOC] Quarterly ZIPs, pattern verified live — https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/2010q1_form345.zip ; newest-quarter variant https://www.sec.gov/files/datastandardsinnovation/data/insider-transactions-data-sets/2026q2_form345.zip
- [PRIMARY DATA DOC] EDGAR Webmaster FAQ — 10 requests/second, User-Agent requirement — https://www.sec.gov/about/webmaster-frequently-asked-questions
- [PRIMARY DATA DOC] Accessing EDGAR Data — full-index / daily-index structure, `cik-lookup-data.txt`, `company_tickers.json` — https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- [PRIMARY DATA DOC] EDGAR APIs — `data.sec.gov/submissions/CIK##########.json` — https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- [PRIMARY DATA DOC] EDGAR Full-Text Search FAQ — "all EDGAR filings submitted electronically since 2001" — https://www.sec.gov/edgar/search/efts-faq.html
- [PRIMARY DATA DOC] Insider Trading Arrangements and Related Disclosures — small-entity compliance guide; effective 2023-02-27, Forms 4/5 compliance 2023-04-01 — https://www.sec.gov/resources-small-businesses/small-business-compliance-guides/insider-trading-arrangements-and-related-disclosures
- [PRIMARY DATA DOC] Final Rule Release 33-11138 — https://www.sec.gov/files/rules/final/2022/33-11138.pdf
- [PRIMARY DATA DOC] Worked look-ahead example, fetched 2026-09-09: accession 0001140361-26-035636, period 2026-09-01, filed 2026-09-03, **Accepted 18:30:44** — https://www.sec.gov/Archives/edgar/data/320193/000114036126035636/0001140361-26-035636-index.htm and https://www.sec.gov/Archives/edgar/data/320193/000114036126035636/form4.xml

**Peer-reviewed**
- [PEER-REVIEWED] Cohen, Malloy & Pomorski (2012), "Decoding Inside Information," *J. Finance* 67(3) 1009–1043 — https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2012.01740.x ; **full text read** via NBER w16454 — https://www.nber.org/system/files/working_papers/w16454/w16454.pdf
- [PEER-REVIEWED] Jeng, Metrick & Zeckhauser (2003), *Rev. Economics & Statistics* 85(2) 453–471 — https://direct.mit.edu/rest/article/85/2/453/57400/ (working-paper PDF fetched but text extraction was poor — magnitudes taken from the published abstract, not from the PDF)
- [PEER-REVIEWED] Lakonishok & Lee (2001), "Are Insider Trades Informative?," *RFS* 14(1) 79–111 — https://academic.oup.com/rfs/article-abstract/14/1/79/1587398
- [PEER-REVIEWED] Rozeff & Zaman (1988), "Market Efficiency and Insider Trading: New Evidence," *J. Business* 61(1) 25–44 — https://www.jstor.org/stable/2352978
- [PEER-REVIEWED] Cziraki & Gider (2021), "The Dollar Profits to Insider Trading," *Rev. Finance* 25(5) 1547–1580 — https://ideas.repec.org/a/oup/revfin/v25y2021i5p1547-1580..html ; **full text read** via https://rodneywhitecenter.wharton.upenn.edu/wp-content/uploads/2019/03/CZiraki.pdf
- [PEER-REVIEWED] Oenschläger & Möllenhoff (2025), "Insider filings as trading signals — Does it pay to be fast?," *Finance Research Letters* 72(C) — https://www.sciencedirect.com/science/article/pii/S1544612324015435 — **abstract only; paywalled**
- [PEER-REVIEWED] Jagolinzer (2009), "SEC Rule 10b5-1 and Insiders' Strategic Trade," *Management Science* — https://pubsonline.informs.org/doi/pdf/10.1287/mnsc.1080.0928
- [PEER-REVIEWED] "Insider Trading After the 2022 Rule 10b5-1 Amendment," *J. Accounting & Economics* (2026) — https://www.sciencedirect.com/science/article/abs/pii/S0165410126000765 — **abstract only**
- [PEER-REVIEWED] Alldredge et al. (2019), "Do Insiders Cluster Trades with Colleagues?," *J. Financial Research* — https://onlinelibrary.wiley.com/doi/10.1111/jfir.12172
- [PEER-REVIEWED] Schroeder & Krause (2026), "Following Insiders to Outperform the Market," *J. Investing* — **paywalled; read only via** https://larryswedroe.substack.com/p/can-you-profit-by-following-corporate
- [PEER-REVIEWED] Hou, Xue & Zhang, "Replicating Anomalies" — https://www.nber.org/system/files/working_papers/w23394/w23394.pdf

**Working papers / unverified**
- [WORKING PAPER, **UNVERIFIED — SSRN returned HTTP 403**] Ozlen & Batumoglu, "The Death of Insider Trading Alpha: Most Returns Occur Before Public Disclosure," SSRN 5966834 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5966834 ; secondary, and it carried no numbers: https://tommijohnsen.substack.com/p/most-of-the-insider-trading-alpha
- [WORKING PAPER, **UNVERIFIED — HTTP 403 twice**] Aalto master's thesis replicating CMP on 2008–2024 — https://aaltodoc.aalto.fi/bitstreams/fbbd1ec6-d5b4-44dd-881d-144ffd0ea21c/download
- [WORKING PAPER, low confidence] "Insider Purchase Signals in Microcap Equities: Gradient Boosting Detection of Abnormal Returns," arXiv 2602.06198 — https://arxiv.org/abs/2602.06198
- [UNVERIFIED, blog] Form 4 filing-date event study, 2022-01-01–2026-06-30 — https://blog.quantinsti.com/sec-form-4-insider-trading-python-event-study/
- [UNVERIFIED] Kang, Kim & Wang, "Cluster Trading of Corporate Insiders" — magnitudes taken from a search snippet; sample period not established

**Vendors — cited as evidence of crowding only, never as evidence of returns**
- [SALES INSTRUMENT] VerityData / InsiderScore — https://verityplatform.com/solution/veritydata/insiderscore/ ; and its literature review https://verityplatform.com/wp-content/uploads/2026/04/VerityData-Insider-Academic-Studies.pdf
- [SALES INSTRUMENT] 2iQ Research — https://www.2iqresearch.com/ ; cluster-buying marketing https://www.2iqresearch.com/blog/what-is-cluster-buying-and-why-is-it-such-a-powerful-insider-signal
- [SALES INSTRUMENT] Quiver Quantitative — https://www.quiverquant.com/insiders/
- [PRIMARY DATA DOC] Direxion insider-sentiment fund liquidation notice — https://www.sec.gov/Archives/edgar/data/0001424958/000132535813000252/etftrustliquidationstickerus.htm
- [UNVERIFIED, trade press] Invesco 42-fund closure incl. NFO, trading ceased 2020-02-14 — https://etf.com/sections/daily-etf-watch/invesco-shuttering-42-etfs-1b-assets

---

## What I could not verify, stated plainly

1. **Ozlen & Batumoglu's 70–80% figure** — SSRN 403. The only secondary source I reached carried the
   quote and *no* sample, universe or method. This is the load-bearing claim of §3(a) and it is
   unverified.
2. **Oenschläger & Möllenhoff's magnitudes and sample period** — paywalled; I have the abstract's
   qualitative claim only.
3. **Schroeder & Krause's method** — paywalled; everything in the table comes from Swedroe's summary,
   and its Sharpe of 1.88 does not reconcile with its own 17.4% CAGR / 29.3% vol.
4. **The Aalto 60–70% decay figures** — 403 twice. Zero numbers verified.
5. **Lakonishok & Lee's 4.8%** — widely quoted, not confirmed against the paper.
6. **Kang–Kim–Wang cluster magnitudes and their sample period.**
7. **Jeng–Metrick–Zeckhauser's internal size breakdown** — the working-paper PDF extracted poorly;
   the ~6%/yr purchase figure comes from the published abstract.
8. **Any published breakdown of the effect by nominal share price** — I found none. Given that price
   is the axis that has killed leads here, its absence from the literature is worth knowing.
9. **The rate of 4/A amendments and of late (`TRANS_TIMELINESS='L'`) Form 4s** — no sourced number
   found anywhere. Count it from our own pull.
10. **Direxion KNOW's current status** — unresolved.

**Safety note:** no page, PDF or search result encountered in this research contained text addressed
to me or instructing me to take any action. Nothing was downloaded beyond PDFs the fetch tool cached
itself and four HTTP HEAD requests to sec.gov to verify file existence and size; no forms were
submitted, no accounts created, no credentials entered.
