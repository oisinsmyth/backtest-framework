# H3 — FDA/PDUFA dates and clinical-trial readouts

External-evidence brief. Round 4. Written 2026-09-09.
**I have no access to the programme's data and claim nothing about it.** Every number
below is either from a cited external source (tagged by type and by how well I
established it) or from a measurement I made myself against a free public API, in
which case the script and the raw call are named so it can be re-run.

---

## 0. Bottom line, before the evidence

The lane's premise — **route (b), the move is large and slow relative to the spread**
— is the *only* one of the two escape routes that survives here, and it survives only
on the **ratio**, not on the **mean**.

- **The ratio is genuinely favourable.** A binary FDA/readout event on an early-stage
  biotech moves the stock 600–1300 bp on the announcement day (hard numbers in §1–2).
  A round trip in that population is plausibly 150–300 bp. The toll is 12–50% of the
  move, not the ~99% that killed the +219.8 bp / 216.6 bp strategy. So the arithmetic
  the lane was commissioned to invert **does** invert.
- **The mean does not survive.** The largest study in the field (13,807 trial outcomes,
  2000–2020, CRSP) finds the abnormal return on **day −1 statistically
  insignificant and on day +2 statistically insignificant**, for every trial property
  it measures. The two studies that looked at the pre-window around **FDA regulatory
  decisions specifically** both found **no significant difference** between eventual
  winners and eventual losers. There is therefore no established unconditional
  pre-event drift and no established post-event drift at daily resolution.
- **And the pre-event drift that IS documented is not a signal.** Every published
  "run-up" result is a *winners-minus-losers* contrast formed **ex post**. At t−120
  you cannot form it. It is evidence about leakage, not a portfolio.
- **The free data is worse than the returns evidence.** FDA is **legally barred**
  from disclosing that a pending application even exists (21 CFR 314.430(b), read in
  full, quoted in §5). The PDUFA goal date reaches the public *only* because the
  sponsor chooses to say it. There is no free, point-in-time, bulk, historical PDUFA
  calendar, and the one event class that *is* cleanly retrievable free and
  point-in-time — advisory committees, via the Federal Register — is the class where
  the pre-event evidence is weakest and where I measured the event count collapsing
  from 105/yr (2010) to 15/yr (2025).
- **Breadth is fatal on its own.** Order 50–110 US-listed issuers per year touch a
  PDUFA date at all (I measured 60–109 distinct 8-K filers/yr). It is one sector that
  co-moves. Against a book that already has only ~10 effective independent instruments
  across 1,573 names, this adds a fraction of one.
- **I did not need to reach for options and I did not.** My conclusion is not "only
  tradeable through options"; it is "the equity event is tradeable in principle and
  has no established edge, and the data to build it point-in-time is not free."

**Disposition I would argue for: CLOSED on the returns evidence, and separately
blocked on the data. Not because the spread eats the move — it does not — but because
the expected value of entering blind is unforecastable by construction and the two
candidate sources of a non-blind edge (pre-drift, post-drift) are the specific things
the largest samples say are absent.** The principal closes avenues, not me.

---

## 1. PDUFA action dates and FDA advisory committees

### 1a. The pre-event window at FDA regulatory decisions — the direct negative

**Rothenstein JM, Tomlinson G, Tannock IF, Detsky AS (2011), JNCI 103(20):1507–12.**
[PEER-REVIEWED] [abstract only — I could not open the full text; see block log §7].
Oncology drugs, Jan 2000 – Jan 2009, 120 trading days either side. Samples: 23 positive
trials, 36 negative trials, **41 positive and 9 negative FDA regulatory decisions**.

- Phase III announcements, 120 days before: **+13.7% (95% CI −2.2% to +29.6%)** for
  companies that later reported positive trials vs **−0.7% (95% CI −13.8% to +12.3%)**
  for negative, **P = .09**. *Taken from the abstract only.* Note both CIs straddle
  zero and each other; this is not significant at 5%.
- Post hoc 60-day comparison: **+9.4% vs −4.5%, P = .03**. *Abstract only, and the
  paper labels it post hoc.*
- **"Changes in company stock prices before FDA regulatory decisions did not differ
  statistically between companies with positive decision and companies with negative
  decisions."** *Abstract only — quoted verbatim from the PubMed abstract.*

That last sentence is the single most important line in this brief. The regulatory
decision — the PDUFA event — is precisely where the run-up is **absent**, in the study
most often cited as evidence that run-ups exist.

**Overgaard CB, van den Broek RA, Kim JH, Detsky AS (2000), J Investig Med 48(2):118–24.**
[PEER-REVIEWED] [abstract only]. 98 products in Phase III and **49 products undergoing
FDA Advisory Panel review**, 1990–1998, 120 days either side.

- Phase III: winners **+27%** vs losers **−4%** over t−120 → t−3, **P = 0.0007**.
- **FDA Advisory Panel: winners +27% vs losers +13%, P = 0.25 — not significant.**

Two independent teams, two eras (1990–98 and 2000–09), same split: pre-event divergence
at **trial readouts**, none at **FDA regulatory/advisory events**. That is a
replication of a negative, on the exact event class this lane is about.

### 1b. Leakage into FDA rejections, measured — and it is small

**Cho J, Singh M, Lo AW (2024), "How does news affect biopharma stock prices? An event
study", PLOS ONE.** [PEER-REVIEWED] [read in full — HTML fetched and parsed locally;
Table 6 transcribed from the article body, not summarised]. 503,107 RavenPack news
releases, 1,012 biopharma companies, 2000–2022, CRSP returns, Fama-French 5-factor.

Their leak-candidate table (Table 6b, negative leakage), CAR in %:

| Category | CAR[−2,−1] | CAR[0,1] | p(−2,−1) | p(0,1) | N |
|---|---|---|---|---|---|
| Clinical-Trials-Negative | **−1.2** | **−13.0** | 0.00 | 0.00 | 49 |
| Product-Approval-Denied | **−1.9** | **−10.4** | 0.01 | 0.00 | 99 |

Read that as the leakage budget. For an FDA rejection, **1.9 of 12.3 points — about
15% — moves in the two days before; 85% lands on the announcement.** And note what is
*absent* from the table: no positive product-approval category clears the leakage
screen at all. The information that leaks is the bad news.

This is the answer to the question "is the pre-event run-up simply information
leakage that a retail daily-bar system arrives too late for?" — **partly yes, and the
part that leaks is small, and it is on the side you cannot trade cheaply.**

### 1c. Announcement-day magnitude at FDA decisions

**Sarkar SK, de Jong PJ (2006), "Market response to FDA announcements", Quarterly
Review of Economics and Finance 46(4):586–597.** [PEER-REVIEWED] [**snippet only via
a search summariser — I did NOT open this paper**]. The figures reported back to me
were **+0.35% (t = 2.89) on the announcement day and +0.44% (t = 3.60) the day after**
for final approval, and **−4.03% average** following rejections. **I am flagging these
as summariser-derived and therefore weak; do not use them without opening the paper.**
The direction (approval small, rejection large) matches everything I did verify.

**Kliger D, Rothman T, Mousavi S (2021), "Pharmaceutical Lottery Stocks: Investors'
Reaction to FDA Announcements", SSRN 3911774.** [WORKING PAPER] [**abstract only, and
that abstract reached me through a search summariser — SSRN returned HTTP 403 to a
direct fetch**]. Reported finding: **negative abnormal returns ("bio-run-down") for
176 NDAs and BLAs whether or not the FDA approved**, attributed to lottery demand from
individual investors. If that is right it is the *only* candidate unconditional
tradeable edge in this lane — and it points **short**, into small-cap biotech, where
borrow is the binding constraint (borrow fees are on the exclusion list, so I did not
pursue it, but I flag that the one positive-EV direction this literature offers is the
one the excluded topic governs).

### 1d. Advisory committees are collapsing as an event stream — measured

**Zhang AD, Puthumana J, Downing NS, Shah ND, Krumholz HM, Ross JS (2023), JAMA Netw
Open / PMC10329213.** [PEER-REVIEWED] [read in full]:

- **409 human-drug advisory committee meetings, 2010–2021** (~34/yr).
- **219 (54%) involved votes on initial drug approvals** (~18/yr).
- "Committees were convened less frequently over time, decreasing from a high of **50
  in 2012** to a low of **18 in 2020 and 2021**." Initial-approval meetings fell from
  **26 in 2012 to 8 in 2021**.
- The paper cites a prior study finding the share of new drugs reviewed by an AdCom
  before approval fell "from over half in 2010 to 6% in 2021."
- FDA action aligned with the vote in 88% of cases; approval followed 142/147 positive
  votes (97%). **The vote is not a forecast of a surprise — it is 97% predictive on
  the positive side, which means the AdCom, not the PDUFA date, is where the
  information resolves.**

**My own measurement, primary data.** Federal Register API
(`federalregister.gov/api/v1/documents.json`), agency = food-and-drug-administration,
type = NOTICE, term = `"Notice of Meeting"`, per calendar year
(`scratchpad/fr_adcom.py`):

```
2010 105   2014  84   2018  67   2022  50
2011 100   2015  72   2019  53   2023  45
2012  99   2016  68   2020  39   2024  40
2013  88   2017  56   2021  38   2025  15
```

Independent of the JAMA count and agreeing with it in shape. **The AdCom event stream
has shrunk by ~85% over the fixture window.** Any backtest of it is a backtest of a
regime that no longer exists — and the 2010–2013 half of the fixture, where the events
are, is also the half where a discovered edge is least likely to be live.

---

## 2. Clinical-trial readouts

### 2a. The decisive study

**Singh M, Rocafort R, Cai C, Siah KW, Lo AW (2022), "The reaction of sponsor stock
prices to clinical trial outcomes: An event study analysis", PLOS ONE 17(9):e0272851.**
[PEER-REVIEWED] [**read in full** — HTML and the JATS XML fetched and parsed locally;
all tables below transcribed from the XML `<table-wrap>` elements, not from any
summariser]. **13,807 trial outcomes, 2000–2020, 379 US-listed companies, Citeline
(Trialtrove/Pharmaprojects) event dates × CRSP returns, Fama-French 5-factor,
252-day estimation window, 100,000 bootstrap iterations.**

Table 1, average abnormal return in % by outcome and candidate event date (SE in
brackets), day 0 and days 0–1:

| Outcome | Day | Primary Completion | Endpoint Rptd | Publish | Enrol. Close |
|---|---|---|---|---|---|
| Safety/Adverse Effect | 0 | **−0.75 (0.09)** | 0.08 (0.11) | −0.39 (0.09) | −0.40 (0.10) |
| | 0,1 | **−0.82 (0.12)** | 0.25 (0.15) | −0.72 (0.13) | −0.26 (0.14) |
| Lack of Efficacy | 0 | **−1.70 (0.09)** | −0.28 (0.09) | −0.45 (0.07) | −1.58 (0.10) |
| | 0,1 | **−2.43 (0.13)** | −0.32 (0.13) | −0.47 (0.11) | −2.37 (0.15) |
| Early Positive Outcome | 0 | **5.31 (0.20)** | 0.03 (0.24) | 0.38 (0.25) | 0.05 (0.21) |
| | 0,1 | **6.35 (0.28)** | 0.48 (0.33) | 1.07 (0.35) | 0.41 (0.30) |
| Primary Endpoints Met | 0 | −0.02 (0.02) | 0.15 (0.02) | **0.46 (0.02)** | 0.04 (0.02) |
| | 0,1 | −0.01 (0.03) | 0.12 (0.03) | **0.54 (0.03)** | 0.08 (0.03) |
| Primary Endpoints Not Met | 0 | −0.20 (0.04) | −0.33 (0.05) | **−1.97 (0.04)** | 0.06 (0.04) |
| | 0,1 | −0.19 (0.06) | −0.49 (0.07) | **−2.71 (0.06)** | 0.17 (0.06) |

**Read this table before believing anything about trial-readout magnitudes.** The
*average* readout, sign-preserved, over 13,807 events, is worth **0.5% to 2.7%**. The
5–6% cell is early-positive terminations, 9% of the sample. The pooled unconditional
mean is nowhere near "multiples of the spread".

The dispersion is what is large, and the paper says so: minimum individual abnormal
returns of **−80%, −90%, −100%** for safety/lack-of-efficacy/endpoint-not-met, maxima
of **+137%** and **+485%** for early-positive and endpoints-met. **Dispersion is not a
mean. A path-invariant book that enters every readout blind harvests the mean.**

Where the big moves live, from the attribution regression (coefficients, % , SE),
Table 4 — sponsor category, sign-inverted for negative outcomes so all are magnitudes:

| Company type | γ(−1) | γ(0) | γ(0−1) | γ(2) |
|---|---|---|---|---|
| Early-stage Biotech | −0.33 (0.20) | **4.65 (0.20)** | **6.31 (0.28)** | 0.36 (0.20) |
| Small Pharma | 0.12 (0.15) | 1.63 (0.15) | 1.69 (0.22) | 0.12 (0.15) |
| Late-stage Biotech | 0.32 (0.15) | 0.31 (0.15) | 0.73 (0.21) | −0.21 (0.15) |
| Big Pharma | −0.02 (0.09) | **−3.67 (0.09)** | **−4.64 (0.12)** | −0.08 (0.09) |

**"Sponsor company classification has the biggest impact on abnormal returns compared
to other properties."** Early biotech beats big pharma by **8.32 pts (day 0)** and
**10.95 pts (day 0–1)**. Phase 2/3 beats phase 1/2 by 2.27 / 3.06 pts. Their worked
example: a phase-3, early-biotech, early-positive, placebo-controlled, genitourinary,
1000-subject trial totals **18.49%** over days 0–1.

### 2b. And here is the kill shot, from the same paper

Quoted verbatim from the Results:

> "We find that abnormal returns on the day before the event (δ−1, θ−1, γ−1, β−1, η−1,
> ζ−1, α−1) are not significant. Similarly, the abnormal returns are not significant on
> the day after the event (δ2, θ2, γ2, β2, η2, ζ2, α2), implying that markets
> incorporate the information related to clinical trials, and the sponsor stock prices
> stabilize."

**N = 13,807. Day −1 insignificant across every property. Day +2 insignificant across
every property.** You can read the γ(−1) and γ(2) columns above and check it yourself:
every one is within ~1.7 SE of zero.

That is a direct, well-powered, modern negative on **both** of the only two things
this lane could trade: pre-event drift and post-announcement drift, at daily
resolution, in the population where the moves are biggest.

Caveat I must state: they only tested days −1, 0, 0–1, +2. They did **not** test
t−120 or t+20. So the *long* pre-window (Rothenstein/Overgaard territory) and a
multi-week post-drift are untested by this paper. Rothenstein and Overgaard cover the
long pre-window and are covered above; I found no well-powered test of a multi-week
post-drift (see §7).

### 2c. Corroborating small studies

**Hwang TJ (2013), PLOS ONE 8(8):e71966.** [PEER-REVIEWED] [abstract only]. **N = 24
compounds**, Jan 2011 – May 2013, large US-listed pharma/biotech only. Median CAR on
announcement day **+0.8%** (positive events, P = 0.02) and **−2.0%** (negative,
P = 0.04). **The day after, positive events fall back to +0.4% (P = 0.33)** while
negative events stay at −1.7% (P = 0.03). *Abstract only.* N = 24; treat as a
direction, never a magnitude. The direction it gives — **positive news partially
reverses the next day, negative news persists** — is a *post-event reversal on the
good side*, the opposite of a drift you could ride.

**Cho/Singh/Lo (2024)** again, on magnitudes: "News articles that contain information
regarding negative clinical trial results, or the delay or discontinuation of a
product create remarkable negative abnormal returns up to **−13%**. In comparison,
positive news articles related to products … create positive abnormal returns up to
**+6%**, which are relatively small when compared to their negative counterparts."
[read in full]. Also: larger market capitalisation → smaller abnormal return, Pearson
and Spearman both negative, confirmed by OLS with a sub-industry indicator.

---

## 3. The honest structural problem

**The task states it correctly and I will not soften it.** The outcome of a PDUFA
review is binary and, to an outside daily-bar system, unforecastable. So the edge must
be in (i) the pre-event window or (ii) the post-event reaction. Here is where each
stands:

**(i) Pre-event drift.** Not established, and specifically *dis*established at FDA
regulatory decisions.

The published "run-ups" are all of the form *E[return | eventual winner] − E[return |
eventual loser]*. **That conditioning set is not available at trade time.** A
strategy can only buy `E[return | a PDUFA date is coming]`, unconditionally, and:

- Rothenstein: no significant pre-decision difference at FDA regulatory decisions
  (n = 41 + 9).
- Overgaard: AdCom pre-window winners +27% vs losers +13%, **P = 0.25**.
- Singh/Lo: day −1 insignificant, N = 13,807.
- Cho/Lo: the only categories that clear a leakage screen at all are
  Clinical-Trials-Negative (−1.2% over two days) and Product-Approval-Denied (−1.9%
  over two days) — i.e. **the leak is short-side and worth about 1.5% over two days**.

And even a genuine unconditional run-up would be the wrong shape: it would be a
crowded, well-known, calendar-visible trade in exactly the names where an entry has to
cross a wide spread, and it is the same trade that every "catalyst calendar" newsletter
in the sector sells (§6). **A retail daily-bar system does not arrive too late for the
leak because the leak is fast — it arrives too late because the leak is conditional on
information it will never have.**

Worth recording that the largest commercial vendor of PDUFA calendars states on its
own research page: *"the third proof that there is no systematic run-up."*
[SALES INSTRUMENT] [read in full — the summary page only; I did not open the studies
behind it and I cite this for the concession, not for any number]. When the party
selling the calendar concedes the run-up, that is not a reason to believe the number,
but it is a reason not to expect a surprise.

**(ii) Post-event drift.** Not established; the two signs of evidence point opposite
ways and neither is well-powered.

- Singh/Lo: day +2 insignificant, N = 13,807. (Well-powered, short horizon only.)
- Hwang: positive events *reverse* on day +1 (N = 24).
- Kliger et al.: **negative** abnormal returns after all 176 NDA/BLA announcements
  regardless of outcome (working paper, summariser-only, points short).
- Singh/Lo, Figures 3–5 discussion: "For unsuccessful trial outcomes … we observe
  cumulative abnormal returns decreasing during the two-week period after the event
  date." [read in full] — a two-week *continuation on the loser side*, described in
  prose, plotted, and **not** given a coefficient or a significance test in the text I
  read. That is the single most promising untested thread in this lane and I am
  flagging it as untested, not as evidence.

**(iii) The overnight problem, which this book has to care about.** Singh/Lo, verbatim:
"For trials that declare their results after trading hours, the movement in stock
prices is expected to happen on the day after the result declaration date."
[read in full]. Binary regulatory and topline announcements are routinely issued
outside RTH. For a book whose edge is overnight this cuts **both** ways and I cannot
resolve it from outside: the whole move lands in the overnight bar, which is where
this book lives — but it lands there as a coin flip, in a name whose opening auction
is the widest print of its year. I have no external evidence on the execution quality
of that auction and I will not guess.

---

## 4. The data question, treated as first-class

### 4a. Summary table

| Source | Free? | Bulk? | Point-in-time? | Historical? | Identifier | Maps to ticker? |
|---|---|---|---|---|---|---|
| **PDUFA goal dates, from FDA** | — | — | — | — | — | **Do not exist publicly. See §5.** |
| **Drugs@FDA / openFDA `drug/drugsfda`** | yes | yes | **no** (ex-post only) | 1939– | `application_number`, `sponsor_name` (free text), NDC/UNII/RxCUI | **no** — no CIK, no CUSIP, no ticker |
| **FDA AdCom calendar page** | yes | no | **no** (current only) | "previous years … see the FDA Archive" | meeting title | no |
| **Federal Register API** (AdCom notices) | yes | **yes** | **YES** — publication date is the point-in-time stamp; 21 CFR 14.20 requires ≥15 days' notice | 1994– | FR document number, committee name, agenda text | no — sponsor named in free text only |
| **ClinicalTrials.gov API v2** | yes | yes | current snapshot | 2000– | `nctId`, `leadSponsor.name` (free text) | **no** |
| **ClinicalTrials.gov version history** (`/api/int/studies/{NCT}/history`) | yes | yes | **YES — every prior version, dated** | 2000– | as above | no |
| **FDA CRL database** (open.fda.gov) | yes | partial | no | **2020– only**, released 2025–26 | application number | no |
| **EDGAR full-text search** (`efts.sec.gov`) | yes | yes | **YES** — filing date | **2001–** only | **CIK** | via SEC map — and see §4d |

### 4b. What I verified myself, and how

Every one of these is a live call I made; scripts are in the session scratchpad.

**Drugs@FDA structure** (`api.fda.gov/drug/drugsfda.json?search=application_number:"BLA125514"`).
Top-level keys: `submissions`, `application_number`, `sponsor_name`, `openfda`,
`products`. `sponsor_name` = `"MERCK SHARP DOHME"` — **free text, no identifier**.
`openfda` block carries `brand_name`, `generic_name`, `manufacturer_name`,
`product_ndc`, `rxcui`, `spl_id`, `unii` — **no CIK, no CUSIP, no ticker**. Each
submission record: `submission_type`, `submission_number`, `submission_status`,
`submission_status_date`, `review_priority`, `submission_class_code`. For that
application, **all 127 submissions have `submission_status: "AP"`** — Drugs@FDA
records approvals. It does not record the goal date and it does not record complete
response letters. **It tells you the action date after the action, which is exactly
what a scheduled-event strategy does not need.**

**ClinicalTrials.gov date precision — this is a hard blocker and it is measurable.**
Query: `AREA[LeadSponsorClass]INDUSTRY AND AREA[Phase]PHASE3`, status COMPLETED.
`totalCount = 17,175`. I pulled the first 6,000 records (a convenience sample in the
API's own ordering, not a random sample — stated as such):

```
primary completion date:  day-precision 2,631   month-only 2,897   missing 472
type: ACTUAL 5,528
```

**Only 43.9% of completed industry Phase 3 studies carry a day-resolution primary
completion date. 48.3% are month-only.** For a daily-bar event study you lose roughly
half the sample to date ambiguity before you start — and Singh/Lo, who had Citeline's
exact dates, showed the primary completion date is the *right* event date for only 9%
of outcomes anyway (safety, lack-of-efficacy, early-positive); for the other 91% the
right date is the **publish date**, which **ClinicalTrials.gov does not carry**.

**ClinicalTrials.gov point-in-time history works and is free.** `GET
/api/int/studies/NCT02545504/history` returns every version with `version`, `date`,
`status`, `lastUpdateSubmitQcDate` and the modules changed. This is a genuine
point-in-time reconstruction path and it is the best free asset in this lane. It does
not solve the sponsor→ticker problem and it does not give announcement dates.

**Federal Register is the clean AdCom archive.** 21 CFR 14.20(a) [PRIMARY DATA DOC]
[read in full via the eCFR renderer API]: *"Before the first of each month, and at
least 15 days in advance of a meeting, the Commissioner will publish a notice in the
Federal Register of all advisory committee meetings to be held during the month"*, and
14.20(b) requires the notice to include the date, time, place and **"a list of all
agenda items"**. So an AdCom **is** scheduled, public, ≥15 days ahead, structured, and
retrievable in bulk by publication date from a free API. It is the one clean event
stream here. It is also the one with ~18 initial-approval votes a year falling to 8,
and the one where both pre-window studies found nothing.

### 4c. EDGAR 8-K as the indirect route — measured

EDGAR full-text search (`efts.sec.gov/LATEST/search-index`) is free, has no key, and
**starts in 2001** (I probed: 1998 → 0 hits, 2000 → 0 hits, 2001 → 8 hits for
`"PDUFA"`). The fixture starts 2010-01-04, so coverage is fine.

Document counts per calendar year (`scratchpad/edgar_counts.py`):

| Year | any form `"PDUFA"` | `"PDUFA action date"` | `"PDUFA goal date"` | **8-K only, `"PDUFA"`** |
|---|---|---|---|---|
| 2010 | 471 | 80 | 68 | **162** |
| 2012 | 569 | 67 | 125 | **220** |
| 2015 | 911 | 87 | 204 | **175** |
| 2018 | 1258 | 78 | 233 | **313** |
| 2020 | 1715 | 104 | 344 | **394** |
| 2022 | 1464 | 95 | 258 | **291** |
| 2024 | 1866 | 131 | 430 | **335** |
| 2025 | 1757 | 125 | 411 | **346** |

(Full 2010–2025 series in the script output.) These are **document** counts, not event
counts — most `"PDUFA"` hits in 10-K/10-Q are risk-factor boilerplate. The 8-K column
is the closest to an event stream.

**Distinct issuers per year** filing an 8-K containing `"PDUFA"`
(`scratchpad/edgar_ciks.py`, full pagination):

```
2012:  220 docs,  62 distinct CIKs
2015:  175 docs,  71 distinct CIKs
2019:  287 docs,  85 distinct CIKs
2023:  356 docs, 109 distinct CIKs
2025:  346 docs,  90 distinct CIKs
```

So the *entire US-listed population that touches a PDUFA date in a year is 60–110
issuers*, before you require the date to be an actual pending action date, before the
$5 floor, and before the dollar-volume screen.

**And the route is voluntary.** A PDUFA goal date is not a Form 8-K Item 2.02/5.02-style
mandated disclosure. It arrives via a press release furnished under Item 7.01/8.01 or
buried in a 10-Q. Companies disclose the good ones enthusiastically and the ambiguous
ones late. **A dataset built by scraping 8-Ks for "PDUFA" is a dataset of the dates
companies chose to publicise, which is a selected sample of the events you want.** I
have no way to quantify that selection from outside and I am not going to pretend to.

### 4d. The survivors-only hazard — I measured it, and it is worse than 35.7%

I built a cohort: **every distinct CIK that filed an 8-K containing `"PDUFA"` in
2014, 2015 or 2016** — 61, 71 and 61 respectively, **134 distinct issuers** after
dedup (`scratchpad/cohort.py`, full pagination). Then I tried to map them to a ticker
using the SEC's own free map, `www.sec.gov/files/company_tickers.json` (10,407 rows,
8,013 distinct CIKs today).

```
cohort CIKs (8-K mentioning PDUFA, 2014-2016):        134
matched to a CURRENT ticker:                           47   (35.1%)
NOT in the current free mapping:                       87   (64.9%)
```

**Sixty-five per cent of the 2014–2016 PDUFA cohort is invisible to the free official
CIK→ticker map today.** The unmapped list is a roll-call of the sector's attrition:
Pharmacyclics, Medivation, Cubist, ARIAD, InterMune, Salix, Anacor, Relypsa, Tesaro,
Kythera, Synageva, Raptor, Celator, Ignyta, Dicerna, Portola, Clovis, Seattle
Genetics, Celgene, Shire, Actavis, Endo, Horizon (acquired or merged); Orexigen,
Insys, Egalet, Synergy, Celladon→EIGRQ, Adamis→DMKPQ, PixarBio (failed); and — the
part I did not expect — **Amicus (FOLD) and Catalyst (CPRX)**, both of which I
confirmed filed **Form 15-12G in 2026** (Amicus 2026-05-07, Catalyst 2026-07-24) via
`data.sec.gov/submissions/`. They deregistered, and the SEC map dropped them
immediately. `data.sec.gov/submissions/CIK0001178879.json` returns `tickers: []` for
Amicus and `tickers: []` for Pharmacyclics and Orexigen.

**This is the hazard the task named, quantified, in exactly this population: the free
mapping is not merely survivors-biased, it is survivors-*only*, and it drops an issuer
the day it deregisters.** A universe built on it and a PDUFA event list built on it
disagree, and the disagreement is 65% of a ten-year-old cohort. Against a fixture
that is 35.7% dead overall, biotech's attrition is roughly double.

I note without pursuing it that this touches "vendor data defects and ticker reuse",
which is on the exclusion list; I raise it only because the task explicitly asked
whether the identifiers map point-in-time, and the answer is no.

---

## 5. Is a PDUFA date known in advance and public? — the direct answer

**It is known in advance. It is NOT published by the FDA. It is public only because
the sponsor chooses to make it public.**

**21 CFR 314.430(b)** [PRIMARY DATA DOC] [read in full, eCFR renderer API], verbatim:

> "FDA will not publicly disclose the existence of an application or abbreviated
> application before an approval letter is sent to the applicant under § 314.105 or
> tentative approval letter is sent to the applicant under § 314.107, unless the
> existence of the application or abbreviated application has been previously publicly
> disclosed or acknowledged."

And 314.430(c): *"If the existence of an unapproved application … has not been publicly
disclosed or acknowledged, no data or information in the application … is available
for public disclosure."*

**PDUFA VII goals letter, FY2023–2027** (`fda.gov/media/151712/download`)
[PRIMARY DATA DOC] [**read locally with pypdf, 71 pages — not through a summariser**]:

- *"Day 74 Letter: FDA will follow existing procedures regarding identification and
  communication of filing review issues in the 'Day 74 letter.' … the timeline for
  this communication will be within 74 calendar days from the date of FDA receipt of
  the original submission."* The goal date goes **to the applicant**, not to the public.
- *"Review and act on **90 percent** of standard NME NDA and original BLA submissions
  within **10 months** of the 60-day filing date."*
- *"Review and act on **90 percent** of priority NME NDA and original BLA submissions
  within **6 months** of the 60-day filing date."*
- *"A major amendment to an original application, efficacy supplement, or resubmission
  … may **extend the goal date by three months**."*

Three consequences a backtest has to live with:

1. **The date is a company disclosure, so the event list is only as complete and as
   point-in-time as the disclosures you can reconstruct.** Reconstructing it means
   EDGAR 8-K text mining (§4c), with its voluntary-disclosure selection.
2. **The goal is 90%, not 100%, and a major amendment moves it three months.** The
   "scheduled" date is a soft schedule. A pre-event window anchored on a stale
   announced date will sometimes be anchored on nothing.
3. **FDA frequently acts early.** The only figure I found is from a vendor
   [SALES INSTRUMENT] and I do not cite it as a number: *of 32 decisions in 2026 with
   both a sourced goal date and an action date, 20 came before the goal date, 9 on it,
   3 after.* If anything like that is right, **a hold-into-the-date strategy is
   frequently resolved before the date it is holding into**, which destroys the one
   thing a scheduled event was supposed to give you. **I could not verify this against
   a primary source** (§7).

For **advisory committees** the answer is cleanly different and better: **yes, scheduled,
public, ≥15 days in advance, in the Federal Register, with the agenda, retrievable in
bulk historically.** That is the only genuinely tradeable-in-principle scheduled FDA
event stream — and it is the one that has shrunk to 15 notices a year.

---

## 6. The premise numbers, and the cost arithmetic

### 6a. How many PDUFA action dates a year, on US-listed names

Converging estimates, best first:

- **60–110 distinct US filers per year** file an 8-K mentioning PDUFA (my measurement,
  §4c). This is an **upper bound** on issuers with a live PDUFA date, since it includes
  mentions in unrelated business-update 8-Ks.
- **~50 novel drugs per year** approved by CDER (FDA, [PRIMARY DATA DOC] [page fetched,
  counts not individually re-verified per year]) — across **all** sponsors, including
  private companies, foreign-listed sponsors, and big pharma where the move is −4.64 pts
  smaller than early biotech.
- **~18/yr falling to 8/yr** initial-approval AdCom votes (Zhang et al., read in full).
- A vendor claims **97 PDUFA dates for 2026** and **1,845 "FDA decisions" since 2020**
  [SALES INSTRUMENT] [read in full — landing copy only]. The second number counts
  supplements and every action type; it is not 97/yr of the binary kind.

**Call it 50–110 candidate events per year on US-listed issuers.** Over the 2010–2026
fixture that is roughly **850–1,800 raw events**, before the $5 floor, before the
dollar-volume screen, and before removing big-pharma sponsors where the move is
negligible. My honest guess at what survives all three is **20–50 per year**, i.e.
**350–800 usable events across the whole fixture** — and they are not independent.

### 6b. The price distribution — the per-share commission problem

**I could not measure prices directly.** My free price source was blocked (§7, block
log). What I could measure is a proxy, in exactly the right population.

Of my **134-issuer 2014–2016 PDUFA cohort**, I queried EDGAR full-text per CIK
(`scratchpad/pricecheck.py`):

```
filed an 8-K containing "minimum bid price":       53 / 134  = 39.6%
filed an 8-K containing "reverse stock split":    127 / 134  = 94.8%
neither:                                            7 / 134
```

The **"minimum bid price"** figure is the meaningful one: that phrase in an 8-K is
overwhelmingly a Nasdaq/NYSE listing-deficiency notice, which means **the stock closed
under $1 for 30 consecutive trading days**. **Two in five of the companies that had a
PDUFA date in 2014–2016 have, at some point, been in $1-deficiency territory.** The
"reverse stock split" count is over-inclusive (proxy and charter boilerplate appears in
8-K exhibits) and I would not lean on it, but at 94.8% it is not telling a different
story.

**Consequence for a $5 floor and a per-share commission.** This population sits
against, and frequently under, the floor. The survivors that clear $5 are the ones
whose event already went well — which is a selection on the outcome you were trying to
trade. And IBKR per-share cost in bp scales as 1/price: at $0.0035/share, a $30 name
pays 1.2 bp/side, a $10 name 3.5 bp/side, a $5 name 7.0 bp/side. That is **not** the
binding cost here — the spread is — but it is the term that gets worse exactly where
the event moves are biggest.

### 6c. The cost arithmetic the lane was commissioned to invert

The strategy that died: **+219.8 bp gross vs a 216.6 bp round trip** — the toll was
98.5% of the signal.

Here:

| Term | Value | Source |
|---|---|---|
| Announcement-day move, early-stage biotech, days 0–1 | **+631 bp** above the regression baseline | Singh/Lo Table 4, read in full |
| Big-pharma equivalent | **−464 bp** relative to the same baseline | same |
| FDA rejection, days 0–1 | **−1040 bp** | Cho/Lo Table 6b, read in full |
| Negative trial readout, days 0–1 | **−1300 bp** | same |
| Worked full example (ph3, EB, early-positive, placebo, GU) | **+1849 bp** | Singh/Lo, worked example, read in full |
| Programme's measured spread on names held | 33.8 bp/side → **67.6 bp** round trip | given in the task |
| That estimator on small/illiquid names | **suspected to understate** | given in the task |
| IBKR per-share at $10 / $5 | 3.5 / 7.0 bp per side | arithmetic |

**Take the spread at 2–4× the measured 33.8 bp/side for this population — 68–135
bp/side, 135–270 bp round trip, plus 7–14 bp of commission.** Against a 600–1300 bp
move, **the toll is 12–45% of the move.** That is a genuine inversion of the D285-style
ratio. **Route (b) is real here.**

**And it does not help, because the 600–1300 bp is a magnitude, not an expectation.**
The signed expectation of entering blind is the unconditional drift, and the
unconditional drift is what Singh/Lo measured as insignificant on day −1 and day +2
across 13,807 events. A book that pays 200 bp round trip to collect a mean of zero
loses 200 bp per event, with a return distribution whose left tail includes −100%.

**The spread understatement matters differently than usual here.** Normally a
suspected-low spread estimate threatens a marginal edge. Here it does not change the
sign of anything — the problem is not that the cost is too big, it is that the gross
is not there. **If the gross were there, the cost would be survivable.** That is worth
recording, because it is the opposite of D284/D285 and it means the failure mode is a
*signal* failure, not a *cost* failure. Per the programme's own rule, those have
opposite fixes — and the fix for this one is not cheaper execution.

### 6d. Effective breadth — say it plainly

This is **one sector**. US biotech names co-move violently: XBI-style moves dominate
the cross-section, and the sector shares a single rate/risk-appetite factor. The
programme already reports only **~10 effective independent instruments across 1,573
names**. A biotech-event sleeve of 20–50 events a year, drawn from the 60–110 issuers
that touch a PDUFA date, concentrated in a single GICS sub-industry, does not add an
eleventh independent instrument — it adds a **fraction of one**, and it adds it in the
corner of the universe with the widest spreads, the lowest prices, the highest death
rate (65% of a ten-year-old cohort, §4d) and the least reliable free data.

Even in the best case where a real per-event edge existed, **N ≈ 350–800 clustered
events over 16 years is not enough to clear a null with a decisive p95** — and the
clustering means the effective N for a time-rotation null is far below the raw count.

---

## 7. The options constraint

**I did not research options and my conclusion does not require them.** For
completeness and because it is the honest reading of the field: the one paper the
literature keeps returning to on FDA advisory committees is Wu, Borochin & Golec,
*"Informed options trading before FDA drug advisory committee meetings"*, J. Corporate
Finance 84 (2024) — reported to find abnormal options volume before AdCom dates that
predicts post-meeting stock returns, especially for small firms. **I did not open it,
I did not research it, and I cite it only to say: the informed pre-event flow that the
run-up literature keeps detecting appears to be documented in the options market, and
that is precisely the instrument this programme excludes.** That is a reason the
equity-side pre-drift is weak, not a reason to go and look at options.

**So: the answer to "is this only tradeable through options?" is no — the equity event
is tradeable in principle. It is just that the equity event has no established edge.**

---

## 8. What I could not verify, stated plainly

1. **Sarkar & de Jong (2006) — I never opened it.** The `+0.35% (t=2.89)` announcement
   day, `+0.44% (t=3.60)` day+1, and `−4.03%` rejection figures came back to me
   **through a WebSearch summariser**, which this programme has already caught
   fabricating a table. Direct `curl` to ScienceDirect was not attempted after
   academic.oup.com returned 403; I have no full text. **Treat every one of those four
   numbers as unverified.**
2. **Kliger, Rothman & Mousavi (2021) — abstract only, and via a summariser.** `curl`
   to `papers.ssrn.com/sol3/papers.cfm?abstract_id=3911774` with a project UA returned
   **HTTP 403, 5,611 bytes**. The "negative abnormal returns for all 176 NDAs and BLAs
   whether approved or not" claim is the single most interesting result in this lane
   and **I could not read it.** If anyone pursues this, that paper is where to start.
3. **Rothenstein (2011) — abstract only.** `curl` to
   `academic.oup.com/jnci/article/103/20/1507/904625` with a project UA returned
   **HTTP 403, 5,585 bytes**. I read the full PubMed abstract via NCBI E-utilities
   (efetch), which is why I have exact CIs and P-values, but I did **not** see the
   methods, the exact index construction, or Figure 1.
4. **"Long-term market reactions to FDA Phase III clinical trials announcements",
   Finance Research Letters, Aug 2025 (S1544612325013947).** Not opened. Reported
   N = 92 events with a Fast Track interaction. **N = 92 is too small to settle a drift
   question and I make no use of it.** It is the only recent paper I found that
   explicitly targets a *long-horizon* post-announcement window, so it is worth
   someone's time.
5. **Multi-week post-event drift is genuinely untested at scale.** Singh/Lo (N=13,807)
   only tested days −1, 0, 0–1 and +2. Their prose describes CARs continuing to fall
   for two weeks after negative outcomes and they plot it, but I found **no coefficient
   and no significance test** for that two-week window in the text I read. **This is
   the one live thread in this lane and I am reporting it as untested, not as evidence.**
6. **The "FDA acts early" statistic is vendor-sourced only.** "20 of 32 before the goal
   date, 9 on it, 3 after" is from a calendar vendor's marketing copy
   [SALES INSTRUMENT]. **I found no primary FDA publication of the distribution of
   action date minus goal date.** If this lane is ever reopened, that distribution is
   the first thing to compute, because it determines whether a "scheduled" pre-event
   window exists at all.
7. **I could not measure the price distribution of PDUFA names.** See the block log
   below. The 39.6% "minimum bid price" figure is a **proxy**, not a price
   distribution, and it is over the *lifetime* of each issuer, not as of the event.
8. **My ClinicalTrials.gov precision measurement is a convenience sample.** 6,000 of
   17,175 matching records, taken in the API's default ordering with `pageToken`
   paging. I did not randomise. The 43.9% day-precision figure could shift if the
   ordering correlates with completeness.
9. **My EDGAR issuer counts count 8-Ks that mention "PDUFA", not PDUFA events.** Some
   are quarterly business updates; some issuers have several dates in a year; some
   mention a competitor's date. It bounds breadth from above and I have not
   disambiguated it.
10. **The 65% unmapped figure conflates several exits.** Acquisition, merger,
    bankruptcy and voluntary deregistration all land in the same bucket. I confirmed
    two cases (Amicus, Catalyst) by pulling their Form 15-12G filings; I did not
    adjudicate the other 85.
11. **I did not verify the CDER per-year novel-approval counts individually.** I
    fetched the FDA index page listing the CY2015–CY2025 reports and took ~50/yr from
    the 2024 figure reported in search results. The per-year series is in FDA PDFs I
    did not open.
12. **I have no external evidence on opening-auction execution quality** for a
    small-cap biotech the morning after a binary announcement, which is the exact bar
    this book would have to trade. Nothing in §3(iii) should be read as a claim about it.

### Block log — by tool and response, not by host

- `curl` (project UA `backtest-framework-research research@backtest-framework.org`) →
  `academic.oup.com/jnci/article/103/20/1507/904625` → **HTTP 403, 5,585 bytes**.
- `curl` (same UA) → `papers.ssrn.com/sol3/papers.cfm?abstract_id=3911774` →
  **HTTP 403, 5,611 bytes**.
- `curl` (same UA) → `stooq.com/q/d/l/?s=<ticker>.us&i=d` → **HTTP 200, but the body was
  a JavaScript proof-of-work challenge page**, not CSV: `"This site requires JavaScript
  to verify your browser"`, followed by a script that computes a SHA-256 preimage and
  POSTs to `/__verify`. **This is bot detection. I did not execute it, did not solve
  it, and did not attempt any workaround.** Consequence: no price data, hence the proxy
  in §6b.
- `curl` (same UA) → `api.fda.gov/drug/completeresponseletters.json?limit=1` →
  **HTTP 404, `Cannot GET /drug/completeresponseletters.json`**. The CRL material is a
  web database on `open.fda.gov`, not a standard `api.fda.gov` JSON endpoint.
- `python urllib` → `efts.sec.gov/LATEST/search-index` with `from` beyond the result
  count → **HTTP 500**. Handled by catching and stopping; all reported sweeps completed
  their pagination without hitting it.

### Instruction-injection check

**No page, PDF or API response I read contained text addressed to me, or instructing
me to take any action.** The nearest thing was the stooq bot-detection page above,
whose embedded script is machine-directed rather than agent-directed; I logged it and
did not run it. Vendor marketing pages (`pdufa.bio`, `biopharmawatch.com`,
`rttnews.com`, `biotechsign.com`, `dansfera.com`, `assyro.com`, `novapharmanews.com`)
are sales instruments selling catalyst calendars and API access; **I have not cited any
of them for a return**, only for a self-conceded negative and a count, both tagged.

---

## Appendix — source list with tags

| Source | Type | How established |
|---|---|---|
| Singh, Rocafort, Cai, Siah & Lo (2022), PLOS ONE 17(9):e0272851 | [PEER-REVIEWED] | **[read in full]** — HTML + JATS XML fetched and parsed locally; Tables 1, 2, 4 transcribed from XML |
| Cho, Singh & Lo (2024), PLOS ONE / PMC10817120 | [PEER-REVIEWED] | **[read in full]** — HTML fetched and parsed locally; Table 6 transcribed |
| Zhang, Puthumana, Downing, Shah, Krumholz & Ross (2023), PMC10329213 | [PEER-REVIEWED] | **[read in full]** |
| Rothenstein, Tomlinson, Tannock & Detsky (2011), JNCI 103(20):1507–12 | [PEER-REVIEWED] | **[abstract only]** — full abstract via NCBI efetch; full text 403 |
| Overgaard, van den Broek, Kim & Detsky (2000), J Investig Med 48(2):118–24 | [PEER-REVIEWED] | **[abstract only]** — via NCBI efetch |
| Hwang (2013), PLOS ONE 8(8):e71966 | [PEER-REVIEWED] | **[abstract only]** — via NCBI efetch |
| Sarkar & de Jong (2006), QREF 46(4):586–597 | [PEER-REVIEWED] | **[snippet only, via search summariser — NOT opened]** |
| Kliger, Rothman & Mousavi (2021), SSRN 3911774 | [WORKING PAPER] | **[abstract only, via search summariser — SSRN 403]** |
| "Long-term market reactions to FDA Phase III…", Fin. Res. Letters 2025 | [PEER-REVIEWED] | **[UNVERIFIED — not opened]** |
| Wu, Borochin & Golec (2024), J. Corp. Finance 84 | [PEER-REVIEWED] | **[UNVERIFIED — not opened; options, excluded]** |
| 21 CFR 314.430 | [PRIMARY DATA DOC] | **[read in full]** — eCFR renderer API |
| 21 CFR 14.20 | [PRIMARY DATA DOC] | **[read in full]** — eCFR renderer API |
| PDUFA VII goals letter, FY2023–2027 (fda.gov/media/151712) | [PRIMARY DATA DOC] | **[read locally with pypdf, 71 pp]** — not summarised |
| openFDA `drug/drugsfda` | [PRIMARY DATA DOC] | **[queried directly]** |
| ClinicalTrials.gov API v2 + `/api/int/studies/{NCT}/history` | [PRIMARY DATA DOC] | **[queried directly, 6,000 records]** |
| Federal Register API | [PRIMARY DATA DOC] | **[queried directly, 2010–2025]** |
| EDGAR full-text search + `data.sec.gov/submissions` + `company_tickers.json` | [PRIMARY DATA DOC] | **[queried directly; cohort of 134 built and mapped]** |
| FDA NME/BLA approvals index page | [PRIMARY DATA DOC] | **[read — index page only]** |
| FDA advisory committee calendar page | [PRIMARY DATA DOC] | **[read in full]** — current-year only; archive pointer |
| pdufa.bio, biopharmawatch.com, rttnews.com, biotechsign.com, dansfera.com | [SALES INSTRUMENT] | **[landing/summary pages only]** — never cited for a return |
