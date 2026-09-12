# H2 — securities class-action litigation: filings and resolutions

**Round 4, lane H2. External evidence only.** I have no access to the programme's fixture and claim
nothing about it. Under [R15](../../docs/RULES.md#r15) this brief closes nothing and admits nothing.

**Researched 2026-09-09.**

---

## THE HEADLINE, BECAUSE IT IS SHORT AND IT IS NEGATIVE

**The commissioning objection was right about the filing leg, and the resolution leg — the half
commissioned as "the more interesting" — is worse, not better. It is a measured null with a large
sample, published, and I read the table.**

| leg | best-evidenced dated return | source, how established |
|---|---|---|
| **filing date**, all cases | CAR[-1,1] = **-3.6%** (t large, N=3,479) | Barko/Renneboog/Zhang Table 4 Panel A, **read in full** |
| **filing date**, no recent investigation news | ABRET[0,1] = **+0.071%/day, t=0.75** (N=366) | Saha diss. Table 1.3 row 5, **read in full** |
| **post-filing**, tradeable window [2,6] | **-0.168%/day** ≈ -0.84% over 5 bars (N=1,473) | Saha diss. Table 1.3 row 1, **read in full** |
| **settlement filing** | CAR[-1,1] = **+0.001, t≈0** (N=2,052) | Barko et al. Table 4 Panel B, **read in full** |
| **final court order (the resolution)** | CAR[-1,1] = **+0.002, insignificant** (N=2,021) | Barko et al. Table 4 **Panel C — every cell insignificant**, read in full |
| **dismissal specifically** | CAR[-1,1] = **+0.002**, CAR[-20,20] = **-0.002**, both insignificant (N=1,119) | same, Panel C col (5) |

**Four things follow, and I put them first because they outrank the leads.**

1. **The filing-date effect survives the objection but is not tradeable.** Once you condition on
   *no recent public investigation news*, the filing day is **exactly zero** (+0.071%/day, t=0.75).
   The -3.6% at [-1,1] is day -1 and day 0 — the drop and the news, not the litigation.
2. **The resolution leg is a null, not an under-studied opportunity.** The commissioning premise was
   that a dismissal is "a dated removal of a known liability… mandate-driven, price-insensitive."
   The mechanism is sound and **the market does not pay it.** Barko et al. tested exactly this and
   report *"no significant upward price movements in the period surrounding the day that the final
   order is issued by the court… Strikingly, this is also the case for acquitted firms."*
3. **The one non-null on the resolution side is a wide-window artifact.** Voluntary settlements show
   +3.7% at [-20,20] — but **-0.3% at [-1,1] and +0.9% at [-5,5], both insignificant.** A result
   that is null at ±1 and ±5 and appears only at ±10 and ±20 is date imprecision, and **the authors
   say so themselves**: the settlement date "could be done with some more imprecision."
4. **The SCAC data source is currently DOWN, frozen at 2025-07-28, and its Terms of Service
   prohibit scraping and commercial use.** That is a hard blocker independent of the returns, and I
   verified it by fetching the pages. See §4.

**My recommendation: route (a) is dead on both legs. I would not spend a runner on this territory.**
The detail below is the evidence for that, plus the data findings, which are worth keeping whatever
happens to the signal — SCAC is a genuinely dead-inclusive, point-in-time-ticker litigation database
and that property is rare.

---

## 1. The filing leg, and how badly it is contaminated

### 1.1 The objection, quantified — this is the best source in the territory

**Saha, Sounak (2024), "Two Essays on Asset Prices Around Securities Class Action Lawsuits",
PhD dissertation, Old Dominion University, DOI 10.25777/8zq1-8z98.** [WORKING PAPER / dissertation]
[**read in full** — 110pp PDF pulled from ODU Digital Commons and extracted locally with `pypdf`;
110 pages, 206,131 chars]. Essay 1 is the published paper **Stivers, Sun & Saha, *Journal of
Financial Markets* 67 (2024)** [PEER-REVIEWED, **abstract only** — the ScienceDirect version is
paywalled; I read the dissertation version of the same essay in full instead, and say so here in
the same sentence as every number I take from it].

**Sample, verbatim from §4.3:** SCAC merged with daily short-sale data, **June 2009 – August 2019**;
CRSP share codes 10 and 11 on NYSE/NASDAQ/AMEX; **excludes ADRs, closed-end funds and foreign
companies**; requires Compustat data. **N = 1,473 lawsuits.** Investigation news ("IN") located in
Factiva for **56.4% (831) of cases**.

**The contamination is not marginal, it is most of the effect.** Abstract, verbatim: average
cumulative abnormal return over the 10-day pre-filing period was **"over -17% for lawsuits with a
pre-filing investigation announcement within this 10-day pre-filing window, and only about -3% for
the remaining cases."**

### 1.2 Table 1.3, which is the table that matters

**Read in full from the PDF.** Note carefully: **ABRET is an average DAILY abnormal return**, not a
cumulative one — the table header says so, and it reconciles with the -17% abstract figure
(row 3 pre-filing: -4.248%/day × 5 days ≈ -21%). Size- and book-to-market-matched-portfolio
adjusted. Panel A, full sample 08/2009–06/2019:

| lawsuit category | N | ABRET[-5,-1] | **ABRET[0,1]** | **ABRET[2,6]** |
|---|--:|--:|--:|--:|
| 1. All | 1,473 | -1.215 (-12.41) | **-0.374 (-3.95)** | **-0.168 (-3.96)** |
| 2. No investigation news at all | 642 | -0.564 (-5.05) | -0.467 (-2.80) | -0.287 (-4.53) |
| 3. IN within 5 days of filing | 243 | **-4.248 (-10.44)** | -0.689 (-2.41) | -0.228 (-1.57) |
| 4. IN 6–10 days before filing | 222 | -1.598 (-7.17) | -0.492 (-2.48) | -0.066 (-0.59) |
| 5. **IN older than 10 days** | 366 | -0.109 (-1.80) | **+0.071 (0.75)** | **+0.02 (0.38)** |

**Row 5 is the answer to the commissioning objection.** It is the only clean filing-date event in
the literature I found: the suit is filed, the market has long since digested the investigation
news, and **the filing day pays nothing (+0.071%/day, t=0.75) and the following week pays nothing
(+0.02%/day, t=0.38).** N=366 is not small. **The filing date, stripped of the news that triggered
it, is a null.**

**Row 1 is the tradeable ceiling if you ignore row 5.** Entering at the close of day +1 — the
earliest an event-driven book can act on a public filing — the [2,6] window pays **-0.168%/day ×
5 = -0.84% gross, for a SHORT.**

**Cost arithmetic, using the programme's own measured 33.8 bp/side.** Round trip 67.6 bp.
**-0.84% + 0.68% = -0.16% net.** The full-sample post-filing drift **does not clear its own
spread**, before borrow. And borrow is excluded ground, so the short leg is unavailable anyway.
**Row 2 — the "no news found" subset, which is the most favourable honest cut — pays
-0.287%/day × 5 = -1.44% gross, net -0.76% for a short.** That is the best number this leg offers
and it is short-only, on 642 events over ten years (~63/yr).

**An internal inconsistency I should flag rather than launder:** the dissertation states
"831 out of the total 1473 cases (or 56.4%) have public announcements… and the other **624** cases
do not", but 1473-831 = **642**, and Table 1.3 row 2 reports **N=642**. The "624" in the prose is a
transposition typo; the table is right. It does not affect any number above.

### 1.3 The corroborating filing-date estimate, with proper narrow windows

**Barko, Renneboog & Zhang (2023), "Corporate Fraud and the Consequences of Securities Class Action
Litigation", ECGI Finance Working Paper No. 925/2023.** [WORKING PAPER] [**read in full** — 69pp
PDF from the ECGI open repository, extracted locally; SSRN blocked, see §6]. Sample **2,910 firms,
1996–2019**; Fama-French-Carhart 4-factor, estimation window [-250,-31]; **Mahalanobis-matched
control group** (industry, log assets, past 1-yr return, market-to-book), three controls per firm.

**Table 4 Panel A, CARs around case filing (read in full):**

| window | all (N=3,479) | **control (N=9,765)** | vol. settle (828) | ord. settle (760) | **dismissed (1,675)** |
|---|--:|--:|--:|--:|--:|
| CAR[-1,1] | -0.036*** | **-0.001 (ns)** | -0.056*** | -0.053*** | **-0.018*** |
| CAR[-5,5] | -0.083*** | -0.001 (ns) | -0.132*** | -0.098*** | -0.051*** |
| CAR[-20,20] | -0.123*** | +0.006* | -0.206*** | -0.146*** | -0.072*** |

**Two things worth taking from this.** First, **the matched control group is flat (-0.1%, ns) at
[-1,1]** — so the filing-date drop is the event, not a selection artifact. That is a well-built
control and I credit it. Second, **the market already sorts the outcome at the filing date**:
eventual settlements -5.6%, eventual dismissals -1.8%, difference strongly significant. **That is
the single most damaging fact for the resolution leg** — if the market prices the eventual outcome
at filing, there is nothing left to pay at resolution. Which is exactly what Panel C shows.

**The widely-quoted "12.3%" is CAR[-20,20]** — a 41-day window, half of it before the event. It is
not a tradeable number and it should not be quoted as one.

### 1.4 A figure circulating in search results that I could not find in its cited source

Search summarisers repeatedly attributed **"a 12.3% abnormal return drop"** and **"14.6–20.6%
negative CAAR for firms that pay damages vs 7.2% for dismissed"** to
`stern.nyu.edu/…/con_043276.pdf`. **I downloaded that PDF and read it: it is Merenstein (2006), an
undergraduate honors thesis** [UNVERIFIED as evidence — undergraduate thesis, not peer-reviewed]
**and it contains none of those numbers** (grep for `12.3`, `14.6`, `20.6` returns nothing). The
figures are actually Barko et al.'s, above. **This is the second time in this programme's rounds
that a summariser has attached numbers to a document that does not contain them.** Treat the
undergraduate thesis as worthless for a return and treat search-summary attributions as unreliable.

The thesis is useful for one thing only — **its literature review names primary sources** [all
**snippet only**, read via the thesis's own prose, not opened by me]: Romano (1991) reports
**no significant abnormal returns at dismissal or settlement dates**; **Ferris & Pritchard (2001)**
find **"no effect on the day when investors learn the outcome of a motion to dismiss"**;
Griffin et al. (2004) report -4.1% at the filing date and -16.6% at the class end date.
**I did not open Ferris & Pritchard or Romano.** I flag that in the same sentence. Their conclusions
happen to agree with Barko et al.'s Panel C, which I did read, so the load is not on them.

---

## 2. THE RESOLUTION LEG — the null, in full

This was commissioned as the more interesting half. **It has been tested, on 2,021 final orders,
and it is empty.**

**Barko, Renneboog & Zhang (2023), Table 4 Panels B and C — read in full from the ECGI PDF.**

**Panel B, CARs around the settlement filing (N=2,052 all; 507 voluntary; 408 ordered; 1,119
dismissed):**

| window | all | voluntary settle | ordered settle | dismissed |
|---|--:|--:|--:|--:|
| **CAR[-1,1]** | **+0.001 (ns)** | **-0.003 (ns)** | +0.003 (ns) | +0.002 (ns) |
| CAR[-5,5] | +0.003 (ns) | +0.009 (ns) | +0.001 (ns) | +0.001 (ns) |
| CAR[-10,10] | +0.007 (ns) | **+0.026\*\*\*** | -0.011 (ns) | +0.004 (ns) |
| CAR[-20,20] | +0.006 (ns) | **+0.037\*\*\*** | -0.015 (ns) | -0.002 (ns) |

**Panel C, CARs around the FINAL ORDER (N=2,021 all; 1,119 dismissed):**

| window | all | voluntary | ordered | **dismissed** |
|---|--:|--:|--:|--:|
| CAR[-1,1] | +0.002 (ns) | +0.001 (ns) | 0.000 (ns) | **+0.002 (ns)** |
| CAR[-1,3] | 0.000 (ns) | -0.001 (ns) | -0.001 (ns) | +0.002 (ns) |
| CAR[-5,5] | +0.002 (ns) | +0.002 (ns) | +0.002 (ns) | +0.001 (ns) |
| CAR[-10,10] | +0.005 (ns) | +0.008 (ns) | +0.003 (ns) | +0.004 (ns) |
| CAR[-20,20] | 0.000 (ns) | +0.002 (ns) | 0.000 (ns) | **-0.002 (ns)** |

**Every cell in Panel C is statistically insignificant.** The authors' own words: *"Panel C reports
CARs around the final court order about settlement fund and closing the case. We find that this
decision has no further informational value."* And on the settlement filing: *"Around the former
date, we do not find any significant CARs which indicates that this event bears little
information."*

### 2.1 The one apparent exception, and why I do not believe it is tradeable

**Voluntary settlements: +2.6% at [-10,10] and +3.7% at [-20,20], both significant at 1%.** The
authors give it a sensible story — shareholders learn the firm will stop contesting, uncertainty
resolves.

**Three reasons to discount it, and I am biased toward the negative here deliberately.**

1. **It is null at [-1,1] (-0.3%) and null at [-5,5] (+0.9%).** A dated event that pays nothing in
   the three days around the date and 3.7% in the forty-one days around it is **not a dated event.**
   The authors attribute the width to date imprecision or market inattention — I attribute it to
   date imprecision, and §4.3 shows SCAC's own resolution dates are labelled *"On or around"*.
2. **Half the window is before the event.** The tradeable half is at most [0,20]. If the drift were
   symmetric that is ~+1.85% over 20 bars; net of 67.6 bp round trip, **~+1.17%, or ~6 bp/bar.**
   The paper does not report [0,20], so **that split is my arithmetic on an assumption of symmetry,
   which the paper does not support.** It is a guess, labelled as one.
3. **N=507 over 24 years ≈ 21 events/year.** Even if real, that is not a book.

### 2.2 The long-run result, and why it is probably someone else's anomaly

Barko et al. also run a long-horizon study: 4-factor monthly, window **[-1,+36] months** around
filing, chosen because "the average length of the court procedure amounts to about 3 years." They
report risk-adjusted returns declining **from -22% short-run to -53% after three years**, with
**no reversal for settlements and continued decline for dismissed firms**; footnote 22 says the
dismissed-vs-settled CAR[-1,36] difference is **not statistically significant** and the result
survives 1/99 and 5/95 winsorisation.

**I would not build on this, for two reasons.**

- **A -53% three-year abnormal return on a Carhart 4-factor model is very close to what a distress
  and low-profitability exposure produces on its own.** There is no profitability or investment
  factor in the model. **THE DEATH PROCESS, DELISTING RETURNS AND THE DISTRESS ANOMALY are on the
  exclusion list** — a defendant sliding toward delisting is explicitly not this territory's
  subject, and this result looks like it is mostly that.
- It is a **short** thesis, and borrow is excluded ground.

**It is, however, the best evidence for the premise number in §5** — because it says the typical
defendant is down roughly half, risk-adjusted, by the time its case resolves.

---

## 3. Adjacent dated events — a paragraph each, as commissioned

**Motion-to-dismiss rulings.** The only direct evidence I located is **Ferris & Pritchard (2001)**,
**[snippet only, read through Merenstein's literature review — I did not open the paper]**: no
effect on the day investors learn the MTD outcome. This is consistent with Barko et al.'s Panel C
null on final orders, which I did read. **A caution on searching this topic: in securities
litigation, "event study" almost always means the expert-witness damages exercise used to prove
price impact under *Halliburton II*, not an asset-pricing study.** Every search I ran on
"MTD ruling event study" returned law-firm client alerts about the former. **Those are
[SALES INSTRUMENT] and are not evidence for a return.** Separately, the MTD ruling has a genuine
attraction the resolution date lacks — it is a *court-calendar* event with a real information
content (survival vs death of the claim) — but I found no return study of it and Cornerstone's data
show why sample size would be a problem: see below.

**Class certification.** I found **no return-based study of the class-certification date at all.**
Searches returned only law-firm commentary on *Halliburton II* and price-impact rebuttal. What I do
have is Cornerstone's settlement-stage data [PRACTITIONER, read in full from the 2024 settlements
PDF]: of 10b-5 settlements 2015–2024, **N=64 settled before the MTD was filed, 113 after filing but
before ruling, 227 after the MTD ruling but before a class-certification motion, 144 after a
class-certification motion was filed.** Median settlements rise monotonically across those stages
($3.4M → $6.7M → $7.0M → $19.7M). **Read as an event calendar this says the certification stage is
reached by a minority of cases** — a few dozen a year — which caps any study of it.

**SEC enforcement: AAERs and litigation releases.** Verified live, see §4.4. As a *return* series
the historical citation is **Feroz, Park & Pastena (1991)** [**snippet only**, via Merenstein]:
mean excess return of **-7.5%** on days [-1,0] when the market learns of an SEC enforcement action,
against -12.9% at the earlier corrective disclosure — i.e. **the same contamination structure as
the class-action filing leg, one step removed.** A 1991 paper on 1980s data is not evidence for
2010-2026. **The disqualifying problem is not the return, it is the population** — see §4.4: the
overwhelming majority of AAER and litigation-release respondents are individual accountants,
officers and private-scheme promoters, not listed issuers, and neither series carries a security
identifier.

---

## 4. THE DATA QUESTION — treated as a first-class deliverable

Everything in this section was verified by fetching the actual pages with `curl` and parsing the
raw HTML locally. I did **not** register for any account, and the full case pages and the Advanced
Search form are behind a login I did not cross.

### 4.1 Stanford SCAC — status, and it is bad news

**[PRIMARY DATA DOC], pages fetched 2026-09-09, HTTP 200.** A banner appears on every page:

> "The Stanford Securities Class Action Clearinghouse (SCAC) is currently under construction and is
> temporarily unavailable as it undergoes updates and improvements. The Clearinghouse is expected to
> return as part of the Stanford Rock Center for Corporate Governance in **Winter 2026**. During
> this period, **updates and new filings will not be available.**"

**Three observations, all verified.**

- **The database is frozen at 2025-07-28.** The most recent filing on the public list is Lockheed
  Martin, 07/28/2025. As of today (2026-09-09) that is **13.5 months stale**, and the promised
  "Winter 2026" return is already overdue.
- **The site is visibly broken mid-restructure.** The raw HTML of the home page contains **10
  version-control conflict markers** (`|||||||  .r976`, `=======`, `>>>>>>> .r979`) rendering as
  page text, with two different "Featured Report" blocks spliced together. That is a site being
  edited in place, not a stable source.
- **The footer reads "© 2026"**, so the site is being served and maintained — it is not abandoned,
  just frozen.

**This alone makes SCAC unusable as the spine of a 2010-2026 fixture without a second source for
the last 13 months.**

### 4.2 What SCAC exposes for free, field by field

**Filings list** (`filings.html`, `list-mode.html`) — **6,879 total filings**, banner-confirmed and
matching the About page. Columns, verified from the rendered rows:

| field | example | note |
|---|---|---|
| Filing Name | `Regional Health Properties, Inc.` | issuer, or issuer `:` security for funds/crypto |
| Filing Date | `07/11/2025` | |
| District Court | `N.D. Georgia` | |
| **Exchange** | `NASDAQ`, `New York SE`, **`OTC-BB`**, `Open-end Fund`, `N/A` | **at filing** |
| **Ticker** | `RHEP`, `LMT`, `N/A` | **at filing** |

**The Exchange and Ticker fields are recorded as of the filing date and are NOT survivorship-
scrubbed** — the public list carries `OTC-BB` tickers and `N/A` for non-listed defendants. **This is
the single most valuable property of the source for this programme** and it is the direct answer to
the commissioned hazard about survivors-only ticker maps.

**Case page** (`filings-case.html?id=N`, server-rendered, sequential integer ids). Public,
un-authenticated fields:

- **Case Status**: `ONGOING` / `DISMISSED` / `SETTLED`
- **A RESOLUTION DATE with a basis label** — this is the key finding, see §4.3
- Current/last presiding judge
- Filing date
- A long narrative case summary (allegations, class period, often the exact percentage price drop
  and closing price on the corrective-disclosure day)

**Gated behind login** (I did not cross it): the *Company & Securities Info* tab (so **no ticker on
the case page itself** — ticker only appears in the list view), *First Identified Complaint*,
*Reference Complaint*, *Related District Court Filings*, and the **Advanced Search form**. The
gating text reads: *"Please Log In or Sign Up for a free account to access restricted features of
the Clearinghouse website, including the Advanced Search form and the full case pages."* **I did not
act on it.** It is ordinary site UI, not an injection attempt, but I record it because the shared
rules require it.

**Key Statistics page** (`stats.html`), verified, 1996 to YTD:

| quantity | value |
|---|--:|
| Total filings | **6,879** |
| Number of filings **settled** | **3,004** |
| Number of filings **dismissed** | **3,306** |
| Number of filings still ongoing | **535** |
| Total $ of all settlements | $119,351,176,861 |
| Total defendants (individuals + companies) | 53,195 |

3,004 + 3,306 + 535 = 6,845, leaving **34 unaccounted** (other dispositions). **91.7% of all filings
since 1996 have reached a resolution, and dismissals outnumber settlements 3,306 to 3,004 — 52.4% of
resolved cases are dismissed.** That is a genuinely large, genuinely resolved population.

### 4.3 The resolution date, and its quality — the thing that decides the lane

The public case page carries a line of the form:

> `Case Status: SETTLED — On or around 07/24/2006 (Date of order of final judgment)`

**I sampled five case ids to recover the label vocabulary.** Observed bases:

| basis label | example | date quality |
|---|---|---|
| `Date of order of final judgment` | id=103000, settled 07/24/2006 | **good** — a real docket event |
| `Court's order of dismissal` | id=104100, dismissed 10/16/2009 | **good** |
| `Notice of voluntarily dismissal` | id=106800, dismissed 01/29/2019 | good, but a non-event economically |
| `Other` | id=100500, dismissed 03/05/1998 | **poor — not a court-order date** |
| `Date of last review` | id=108612, ONGOING | **not a resolution at all** |

**Two things follow.** First, **the date basis varies and the label tells you which**, so a runner
could filter to the two good labels — that is a real mitigation and I credit it. Second, **the
prefix is literally "On or around"**. SCAC does not claim day precision. **That corroborates the
§2.1 diagnosis exactly**: Barko et al.'s settlement effect appears only at ±10 and ±20 days because
the dates behind it are approximate. **A daily-bar event study on approximate dates cannot recover a
one-day effect, and there is no one-day effect to recover.**

### 4.4 The other free sources, and what each identifier actually is

| source | fetched | live? | fields | identifier | verdict |
|---|---|---|---|---|---|
| **SCAC filings list** | HTTP 200 | **frozen 2025-07-28** | name, filing date, court, exchange, **ticker** | **ticker + exchange, point-in-time at filing** | best identifier in the territory; **but see ToS below** |
| **SCAC case page** | HTTP 200 | frozen | status, **resolution date + basis**, judge, narrative | **none** (ticker is gated) | resolution dates are here and free |
| **SEC AAERs** | HTTP 200 | **current to 2026-09-03** | date, respondents, release no. | **free-text respondent name only** | see below |
| **SEC litigation releases** | HTTP 200 | **current to 2026-09-09** | date, respondents, release no., links to complaint/final judgment | **free-text respondent name only** | see below |
| **CourtListener / RECAP bulk** | HTTP 200 | current | dockets, parties, docket entries; **free CSV bulk on S3, no account** | docket + party name | see below |
| **PACER** | **not accessed** | — | — | — | **I did not register, as instructed** |

**SEC AAERs.** `sec.gov/enforcement-litigation/accounting-auditing-enforcement-releases`, fetched
with a project contact in the User-Agent per SEC fair access. Paginated, **100 rows/page × 34 pages
(`?page=0`…`?page=33`)**, latest AAER-4599 (2026-09-03), page 33 reaching AAER-1311 and dates into
1997. **Current, unlike SCAC — that is a genuine advantage.** But: **the respondents on page 0 are
Paul Frenkiel, Steven W. Hurd CPA, Jason Jianxun Tang CPA, Adrian D. Beamish CPA, Jai Sondhi,
George John Drazenovic CPA, Francis Decker CPA** — **individual accountants and officers**, with
only *L&L Energy, Inc.* and *Key Tronic Corporation* being issuers. Worse, **L&L Energy appears
twice, both times as "Order Granting Extension of Time"** — procedural orders consume release
numbers. **There is no CIK and no ticker.** The count of distinct, dated, *issuer-level* AAER events
is a small fraction of the ~105/year the release numbering implies.

**SEC litigation releases.** Filterable by year (1995–2026) and month. Same shape: date, free-text
respondents, `LR-` number, links to the complaint and final judgment. Page 0 respondents on
2026-09-09: *Justin Chen, Francisco Javier Sarabia, Institutional Shareholder Services Inc., Parker
Terrill Austin, Omar Dario Chavez, Trijya Vakil and Neeraj Visen.* **Overwhelmingly individuals and
private offering-fraud schemes.** No security identifier. **Mapping either SEC series to a
point-in-time ticker requires fuzzy name matching against a historical issuer table — which is
exactly the survivors-only hazard the lane was warned about, re-introduced at the join.**

**CourtListener / RECAP.** Free bulk CSV of dockets, parties and docket entries, streamed to a
public S3 bucket, **no account required** (`com-courtlistener-storage.s3-us-west-2.amazonaws.com`,
prefix `bulk-data/`), with a published schema dump. This is the only genuinely bulk-downloadable
free primary source in the territory, and it is the one that could in principle date an
MTD ruling to the day. **Its disqualifying property is that RECAP coverage is crowd-sourced** — a
docket is in RECAP only because some user fetched it from PACER — so **coverage is incomplete and
non-random**, correlated with case prominence. No ticker, no CIK.

### 4.5 The Terms of Service problem, which I rate as decisive

SCAC's own FAQ, item 7, verbatim from `about-the-scac.html`:

> "We do provide Excel spreadsheets to **academic researchers** who would like to use the underlying
> SCAC data for **non-commercial** empirical research and/or analysis. Data is provided pursuant to a
> **Non-Disclosure Agreement**. Use of the data is subject to the Terms of Service, which prohibits,
> among other things, **use of the data for commercial purposes**, unauthorized reproduction of data,
> as well as **use of scraping tools or webcrawlers to access, process and/or index the data.**"

**There is no public bulk download.** The public filings list is capped at recent filings; I tested
`filings.html?year=2015` and the year parameter is **ignored** (byte-identical response, 89,145
bytes). The by-year navigation and Advanced Search are login-gated. **Retrieving all 6,879 records
would require either the NDA route — academic, non-commercial, which this programme is not — or
scraping, which the ToS prohibits.** I made ~10 manual page fetches for schema verification, which
is ordinary browsing; a systematic retrieval is a different act and I am flagging it rather than
doing it.

**Coverage scope, from the methodology section (read in full):** federal court only, filings on or
after 1996-01-01; **state-court cases are excluded unless there is a parallel federal action; SEC
enforcement proceedings are not tracked.** One "filing" = all related complaints against the same
defendant set consolidated into a single record — **so the unit is the case, not the complaint**,
which is the right unit for an event study and avoids double-counting.

### 4.6 Dead and delisted defendants — VERIFIED, and the answer is yes

**This was the commissioned question and it resolves positively.** Two case pages fetched at random
ids:

- **id=100500 — Network Express, Inc.**, filed 1996-10-07, `DISMISSED — On or around 03/05/1998`.
  A 1994-IPO ISDN vendor, long gone. Full narrative retained, including the class-period price path
  ($7-8 → $19-5/8).
- **id=103000 — Whitehall Jewellers, Inc.**, filed 2004-02-12, `SETTLED — On or around 07/24/2006
  (Date of order of final judgment)`. Bankrupt in 2008. Full record retained, including
  *"shares of Whitehall fell 7.6%, or $0.75 per share, to close at $9.04"*.

**A litigation database necessarily keeps dead defendants, and SCAC does.** Combined with §4.2's
point-in-time ticker and exchange, **SCAC is structurally dead-inclusive in exactly the way the
commissioning note hoped.** That property is real and it survives everything else in this brief.
**It is the one thing here worth keeping.**

---

## 5. THE PREMISE NUMBERS

### 5.1 Filings per year — built in layers, each layer sourced

**Layer 1 — SCAC raw federal filings, all defendant types.** Extracted from the `cld_filing_year`
data array embedded in the raw HTML of `charts.html` — **the site's own chart data, not a
summariser**, cross-checked against the `list-mode.html` heat map:

| 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025† |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 175 | 188 | 151 | 165 | 168 | 208 | 271 | **411** | **402** | **402** | 317 | 212 | 197 | 213 | 222 | 129 |

† 2025 is partial, to 2025-07-28. **2010-2024 sum = 3,702; mean 246.8/yr.**

**Layer 2 — remove M&A merger-objection suits, which are not fraud events and are adjacent to
excluded ground.** The 2017-2019 spike is almost entirely them. **Cornerstone Research,
"Securities Class Action Filings — 2025 Year in Review", Appendix 3** [PRACTITIONER — Cornerstone is
a litigation-economics consultancy that sells expert testimony, so treat its commentary as a sales
instrument; **the counts are jointly produced with SCAC and Stanford Securities Litigation Analytics
and I read the appendix in full from the PDF**]. Case status as of 2026-01-16, federal only:

| filing year | **M&A filings** | non-M&A: dismissed | settled | remanded | continuing | trial | **non-M&A total** |
|--:|--:|--:|--:|--:|--:|--:|--:|
| 2014 | 12 | 66 | 87 | 2 | 1 | 0 | **156** |
| 2015 | 34 | 96 | 71 | 4 | 0 | 1 | **172** |
| 2016 | 84 | 93 | 85 | 6 | 2 | 2 | **188** |
| 2017 | **198** | 115 | 93 | 4 | 1 | 0 | **213** |
| 2018 | **182** | 128 | 86 | 0 | 5 | 1 | **220** |
| 2019 | **160** | 125 | 110 | 0 | 7 | 0 | **242** |
| 2020 | 99 | 132 | 76 | 0 | 10 | 0 | **218** |
| 2021 | 18 | 106 | 73 | 1 | 13 | 0 | **193** |
| 2022 | 7 | 95 | 48 | 0 | 47 | 0 | **190** |
| 2023 | 6 | 95 | 42 | 1 | 67 | 0 | **205** |
| 2024 | 5 | 78 | 13 | 0 | 126 | 0 | **217** |
| 2025 | 6 | 20 | 0 | 0 | 177 | 0 | **197** |
| **avg 2014-24** | **73** | **103** | **71** | **2** | **25** | **0** | **~201** |

**Non-M&A federal filings run ~190-240/yr, averaging ~201.** Cornerstone's headline "core filings"
(federal + state, excluding M&A) were **220 in 2024** and **~223 in 2025** [these two from a search
summary of the press release, **not read in the PDF** — the appendix numbers above are the ones I
read]. The appendix does not cover 2010-2013, but SCAC totals there (175/188/151/165) are already
low, so M&A cannot have been large; ~160-190/yr is the reasonable read.

**Layer 3 — restrict to US exchange-listed operating companies.** SCAC's list demonstrably includes
open-end mutual funds (`RMJAX`, `WATFX`), crypto issuers with `N/A` tickers, and ADRs. The best
empirical haircut available is **Saha's**: **1,473 filings over June 2009 – August 2019** surviving
CRSP shrcd 10/11 on NYSE/NASDAQ/AMEX with ADRs, closed-end funds and foreign companies excluded
— **≈144/yr**, against Cornerstone's ~200/yr non-M&A over the overlapping years. **That is a ~70-75%
survival rate**, and it is if anything conservative because Saha additionally required Compustat and
short-sale data.

**→ THE PREMISE NUMBER: approximately 140-160 federal securities class actions per year are filed
against US exchange-listed operating companies, giving roughly 2,300-2,700 over 2010-01 to 2026-08.**

### 5.2 How many resolve inside the window

From Appendix 3's status column, **as of January 2026**, the non-M&A cohorts are resolved at:
2014-2021 **93-99%**; 2022 **75%** (143/190); 2023 **67%** (138/205); 2024 **42%** (91/217);
2025 **10%** (20/197).

**Cornerstone Appendix 4, "Status by Year — Core Federal Filings"** (read in full) gives the timing
directly, as percentages of each cohort:

| cohort | resolved within 1 yr | within 2 yrs | within 3 yrs |
|--:|--:|--:|--:|
| 2010 | 13.2% | 42.6% | 61.8% |
| 2013 | 19.7% | 55.3% | **75.0%** |
| 2016 | 16.0% | 46.8% | 66.5% |
| 2019 | 14.5% | 45.5% | 68.6% |
| 2022 | 13.2% | 31.6% | 62.6% |
| 2023 | 10.2% | 46.8% | 67.3% |

**The structure of that table matters more than the totals: settlements in year one are essentially
zero — 0.0% to 1.5% across every cohort 1997-2025.** Year-one resolutions are almost entirely
dismissals (9.6%-19.1%). **Settlements concentrate in years 2 and 3.** Median filing-to-dismissal
is therefore **~1.5-2 years** (derived from this table, not taken from a summariser; my five SCAC
case probes gave 1.4, 1.45, 1.6, 0.2 and 2.4 years, consistent). **Median filing-to-settlement is
3.2 years in 2024 and 3.7 years in 2023** — **Cornerstone, "Securities Class Action Settlements —
2024 Review and Analysis", read in full from the PDF**, which also gives the distribution for
2015-2023: <2yr N=135, 2-3yr N=224, 3-4yr N=173, 4-5yr N=96, >5yr N=108 (total 736).

**→ Of ~2,400 filings 2010-2026 on exchange-listed operating companies, roughly 1,800-2,000 have a
resolution date inside a window ending 2026-08-26.** Annual event flow: **~82-88 approved
settlements per year** (Cornerstone: 736 over 2015-2023, 83 in 2023, **88 in 2024**) and
**~95-130 dismissals per year**, i.e. **~170-200 resolution events/year before any price screen**,
falling to **~130-160/year** after the exchange-listed operating-company restriction.

### 5.3 The harder number — how many pass a $5 close and dollar-volume floor AT RESOLUTION

**No source I found measures this. What follows is a bounded estimate and I label every input.**

**Starting point is more favourable than the commissioning note assumed.** Cornerstone 2025
Year in Review, read in full: **median predisclosure market capitalisation for Section 10(b) filings
2021-2025 was $2.0 billion**, and the median class-period-end price drop was 15-22%. **Defendants
are typically mid-caps at filing, not micro-caps** — most would clear a $5 floor on the filing date
comfortably. *(Caveat: this median is over filings for which DDL could be estimated; filings without
usable market data are excluded, which biases the figure upward.)*

**The attrition happens during the 3.2-3.7 years to resolution, and there is a primary measurement
of its hard tail.** Cornerstone 2024 settlements report, read in full:

> "Issuers that have been **delisted from a major exchange and/or declared bankruptcy prior to
> settlement** are generally associated with lower settlement amounts. **The proportion of
> settlements with such issuers increased from 6% in 2023 to 16% in 2024.**"

**6-16% of settling defendants are already delisted or bankrupt at the settlement date.** That is a
**floor**, not the answer — it counts only total failure, not the much larger set that is still
listed but trading under $5 or below a dollar-volume threshold. Corroborating the softer attrition:
Barko et al.'s 4-factor CAR runs from -22% to **-53% over [-1,+36] months**, i.e. **the typical
defendant is down roughly half, risk-adjusted, by the time its case resolves** (with the §2.2 caveat
that this measurement is probably contaminated by the distress anomaly).

**→ MY ESTIMATE: 25-40% of resolution events fail a $5-close plus dollar-volume screen at the
resolution date, leaving roughly 80-120 usable resolution events per year, or ~1,300-1,900 over
2010-2026. The 6-16% delisted/bankrupt figure is primary and measured; the rest of that haircut is
my inference from the market-cap distribution and the three-year decline, and nothing I found
measures it directly.**

### 5.4 The density problem, which is separate from the returns

**~100 usable resolution events per year over ~252 bars is 0.4 events per bar.** With a 20-bar hold
that is **~8 names held on average**. Under the programme's slot-limited book that is an extremely
concentrated, high-variance path, and under the path-invariant lens the per-trade sample is ~1,600
trades over 16 years. **Even if the resolution effect were not a null, the event stream is too thin
to fill an equal-weighted daily book**, and the two lenses would be measuring very different things
(`docs/FINDINGS.md` §10). The filing leg is denser (~145/yr) but is the contaminated one.

---

## 6. Blocks, by tool and response

| tool | target | response |
|---|---|---|
| `curl` (browser UA) | `papers.ssrn.com/sol3/papers.cfm?abstract_id=4521118` | **HTTP 403**, body = Cloudflare interstitial `<title>Just a moment...</title>` |
| `curl` (browser UA) | `papers.ssrn.com/sol3/Delivery.cfm/4521118.pdf` | **HTTP 403**, same Cloudflare interstitial |
| `WebFetch` | same SSRN abstract URL | **"The server returned HTTP 403 Forbidden."** |
| `curl` | Cambridge Core PDF, Gande & Lewis JFQA 2009 | **HTTP 200 but `content_type: text/html`** — a challenge page, not the PDF |

**The SSRN block cost nothing** — the same paper is open at ECGI
(`ecgi.global/sites/default/files/working_papers/documents/corporatefraudandtheconsequencesof.pdf`,
HTTP 200, 1,308,765 bytes) and I read it in full there. **The Cambridge block did cost me**: Gande &
Lewis (2009) remains **[abstract only, via search summary]** and I have not verified its numbers.
Its claim — that shareholders partially anticipate suits from industry peers' filings, so filing-date
studies understate losses — points the same direction as Saha's and does not carry any load here.

**No page I fetched contained text addressed to me or instructing me to take an action.** The only
imperative text encountered was ordinary site UI — SCAC's *"Please Log In or Sign Up…"* gating
notice and its sign-up form — which I did not act on, per instruction and per the ToS in §4.5.

---

## 7. What I could not verify, stated plainly

1. **Ferris & Pritchard (2001) — "no effect on the day investors learn the MTD outcome."** I did not
   open this paper. I read the claim in Merenstein's (2006) undergraduate literature review only. I
   probed the Michigan Law repository at four article ids and hit the wrong archive (2003-2009
   working papers, not the 2001 Olin series). **The MTD leg therefore rests on a snippet**, though
   it agrees with Barko et al.'s Panel C, which I did read.
2. **Romano (1991), Griffin/Grundfest/Perino (2004), Feroz/Park/Pastena (1991), Bohn & Choi (1996),
   Bhagat et al. (1994).** All **snippet only**, all read through the same undergraduate thesis's
   literature review. None was opened. **I would not put weight on any number attributed to them
   here** — including Feroz et al.'s -7.5% SEC-enforcement figure in §3.
3. **Gande & Lewis (2009, JFQA).** **Abstract only, via a search summary** — Cambridge Core returned
   a challenge page. I did not verify any figure from it.
4. **Stivers, Sun & Saha (2024), *Journal of Financial Markets* 67.** I read the **dissertation
   version** in full, not the published article. The published version may differ in sample or
   tables. Every number I quote is from the dissertation PDF.
5. **The [0,20] half of Barko et al.'s voluntary-settlement +3.7%.** The paper reports only
   symmetric windows. **My ~+1.85% post-event figure is arithmetic on an unsupported symmetry
   assumption**, not a reported result.
6. **The share of resolution-date defendants failing a $5 close plus dollar-volume screen.** **No
   source measures this.** The 6-16% delisted-or-bankrupt-at-settlement figure is primary and real;
   the 25-40% total haircut in §5.3 is **my estimate** from the market-cap distribution and the
   three-year decline.
7. **Filings 2010-2013 split between M&A and non-M&A.** Cornerstone's Appendix 3 begins at 2014.
   My ~160-190/yr for those years is inferred from SCAC totals being low, not measured.
8. **Cornerstone's 2024 and 2025 "core filings" headline counts (220, ~223).** Taken from a **search
   summary of a press release**, not read in the report PDF. The Appendix 3 and Appendix 4 numbers
   *were* read in full and should be preferred wherever they conflict.
9. **Whether SCAC's frozen state is temporary.** The banner says "Winter 2026" and it is now
   September 2026. I cannot tell whether the archive returns, whether the 13.5-month gap gets
   backfilled, or whether the free tier survives the move to the Rock Center.
10. **The full SCAC field schema.** The *Company & Securities Info*, *First Identified Complaint* and
    *Related District Court Filings* tabs and the Advanced Search form are login-gated and **I did
    not register**. There may be structured resolution fields, settlement amounts, or CIKs behind
    that login that I have not seen. **Settlement amounts in particular I never located on any free
    public page** — only the aggregate $119.4bn total.
11. **The distribution of SCAC resolution-date basis labels.** I sampled **five** case ids. I do not
    know what fraction of the 6,344 resolved cases carry a good label (`Date of order of final
    judgment`, `Court's order of dismissal`) versus a useless one (`Other`). **This ratio is the
    single most decision-relevant unknown left in the data question**, and establishing it would
    require the systematic retrieval that §4.5's ToS prohibits.
12. **RECAP/CourtListener docket coverage for securities cases.** I verified free bulk CSV exists on
    S3 with no account. I did **not** download it, measure its coverage of the ~6,879 SCAC cases, or
    check whether MTD-ruling docket entries are reliably present and reliably dated.
13. **AAER and litigation-release issuer share.** My "overwhelmingly individuals" conclusion is from
    reading **page 0 of each listing** (100 AAER rows, ~25 litigation-release rows). I did not count
    the issuer share across all 34 AAER pages or across years.
