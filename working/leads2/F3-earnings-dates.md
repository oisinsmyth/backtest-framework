# F3 — earnings announcement effects on real announcement dates: external evidence

Research-only scan of external literature and primary data documentation. No code
was written or run; no fixture was touched. Every web page, PDF and API response
below is treated as DATA. Nothing in any of them addressed instructions to me.

---

## 1. Verdict

Lead answer: **of the three objects, the ANNOUNCEMENT PREMIUM is the only one this
programme could implement without paid data — and it is also the one with the
strongest published claim of death, specifically in the US, specifically in the
years this programme's fixture covers.** PEAD is worse: the literature's own
review paper states it has been non-existent for all-but-microcap US stocks since
**2006** and for microcaps since **2016**, and what remains is a five-day effect in
microcaps with no analyst coverage — i.e. exactly the population the $5 floor and
per-share commissions delete. The announcement premium's classic magnitude
(Frazzini–Lamont: 7–18%/yr; global replication: 59.7 bp/month) was measured on
samples ending **2004** and **2010**; the two papers that carry it past 2004
(Heitz–Narayanamoorthy–Zekhnini; Heater et al.) report it **disappearing and
turning negative in the US in the 2010s**, with the premium apparently migrating
to 8-K filing dates. So the honest verdict is: *do not expect to find the premium
as a headline*; the fixture's window is entirely inside the published dead zone.

What is *not* dead, and is the reason this territory still earns a study, is the
**timing fact**. deHaan–Shevlin–Thornock (JAE 2015) measure that **34.6% of US
earnings announcements land before the open and 45.4% after the close — ~80%
outside regular trading hours, only 7% during them.** Mechanically, the
announcement return is therefore a **close-to-open gap**. That is a real
convergence with this programme's own IC decomposition (edge overnight,
wrong-signed intraday), and it is checkable here without any estimates data. And
the data question has a clean answer: **SEC EDGAR 8-K Item 2.02 gives free,
dead-inclusive, timestamped announcement dates back to August 2004** — verified
below on a delisted issuer.

Recommended framing if this is pursued: not "harvest the announcement premium"
(published as dead), but "**the announcement date is a clean, free, dead-inclusive
event label for an overnight-concentrated event**" — and the first question is
whether the programme's *own* overnight edge is concentrated on or away from those
dates. That is a conditioner question, not an anomaly-harvest question.

---

## 2. PEAD and its decay

### The strongest negative, and it is very strong

**Martineau, "Rest in Peace Post-Earnings Announcement Drift", Critical Finance
Review 11(3–4), 2022 [PEER-REVIEWED].** Sample **1984-01-01 to 2019-12-31**, US
firms in Compustat/CRSP with I/B/E/S coverage; size split at the **NYSE 20th
percentile** ("microcap" below, "all-but-microcap" above). Verbatim from the paper:

- "For large stocks, PEAD have been non-existent since 2006 but has only
  disappeared recently for microcap stocks."
- "since 2006 … analyst earnings surprises fail to positively predict
  post-announcement returns over 60 days for all-but-microcap stocks, and since
  2016 for microcap stocks."
- "PEAD is not present for the smallest 'all-but-microcap' stocks and at shorter
  horizon."
- "From 2011 … there are no pronounced price drifts following earnings
  announcements; price discovery mainly occurs at the time of announcements."
- On the random-walk (no-analyst) measure: "For all-but-microcap stocks,
  random-walk earnings surprises only predict positively returns following
  announcements prior to 1990. For microcap stocks, random-walk surprises continue
  to positively predict post-announcement returns; however, **the persistence in
  drifts does not last more than five days**."
- Responsiveness on announcement date rose: all-but-microcap and microcap prices
  are "respectively six and three times more responsive to earnings surprises on
  announcement date" in 2016–2019 than in 1984–1990.
- Pre-announcement drift weakened too, so this is not information leakage moving
  the drift earlier.

Corroborating, independent: **Christensen, Timmermann & Veliyev, "Warp speed price
moves: Jumps after earnings announcements", arXiv 2601.08962, Jan 2026 [WORKING
PAPER]** — "returns from a post-announcement trading strategy are consistent with
efficient price formation **after 2016**", using after-hours high-frequency data
("most earnings announcements are released" there).

### Where PEAD lived, when it lived

**Chordia, Goyal, Sadka, Sadka & Shivakumar, "Liquidity and the
Post-Earnings-Announcement Drift", Financial Analysts Journal 65(4), 2009
[PEER-REVIEWED].** Sample **1972–2005**. Verbatim: "A trading strategy that goes
long high-earnings-surprise stocks and short low-earnings-surprise stocks provides
a monthly value-weighted return of **0.04 percent in the most liquid stocks and
2.43 percent in the most illiquid stocks**." Headline decile-SUE strategy "earns,
on average, **90 bps per month (10 percent annually) over the 1972–2005 period**."
And on cost: "transaction costs account for **70–100 percent of the paper profits**
from a long–short strategy designed to exploit the earnings momentum anomaly."

That single sentence is the whole story for this programme: the drift is a
liquidity-tail phenomenon, it was ~60× larger in illiquid names than liquid ones,
and costs ate most of it even in the era when it existed.

**Ng, Rusticus & Verdi, "Implications of Transaction Costs for the
Post–Earnings-Announcement Drift", Journal of Accounting Research 46(3), 2008
[PEER-REVIEWED].** Same direction: profits "significantly reduced by transaction
costs", and "firms with higher transaction costs are the ones that provide the
higher abnormal returns" — i.e. the return is *paid for* by the cost.

### Surprise measures that need NO paid analyst data

This is answerable cleanly.

| Measure | Needs | Verdict for this programme |
|---|---|---|
| **Analyst surprise** (actual − consensus)/price | I/B/E/S or equivalent — **paid** | Out. Martineau explicitly recommends this measure and says the random-walk substitute changes conclusions. |
| **Random-walk / seasonal-random-walk surprise**: `(EPS_{i,q} − EPS_{i,q−4}) / P_{i,q}` (Livnat–Mendenhall 2006 form, as used by Martineau) | Quarterly EPS + price only. **Free from EDGAR XBRL** (`data.sec.gov/api/xbrl/companyconcept/…/us-gaap/EarningsPerShareDiluted`) | Feasible. But Martineau: it is "a much noisier measure", it doubles the sample **almost entirely with microcaps**, and it predicts nothing for all-but-microcap stocks after 1990. |
| **SUE**: same numerator scaled by the std dev of the last 4–8 quarterly differences | Same, plus ≥2 years history | Feasible; drops young names. |
| **Price-based "surprise"**: the announcement-day return itself | Nothing but prices | Not a surprise measure — this is the tape-gap proxy the programme has already ruled out (D-record: gapped names bounce). Do not reuse. |

Coverage fact worth carrying: Martineau reports that of **593,654** Compustat
announcements with a random-walk surprise, **289,654 (49%) have no analyst
following**, and since 2000 roughly **80% of those uncovered firms are below the
NYSE 20th percentile**. Free surprise data buys you the microcap tail and
essentially nothing else.

**Net: PEAD does not transfer. The programme should not build a surprise measure.**

---

## 3. THE ANNOUNCEMENT PREMIUM (primary)

### The classic positive result

**Frazzini & Lamont, "The Earnings Announcement Premium and Trading Volume", NBER
WP 13090, May 2007 [WORKING PAPER; the underlying result is widely replicated].**

- Announcement dates from **Compustat**; "all common stocks traded in CRSP between
  January 1972 and December 2004", returns **1973–2004**, plus a **1926–1972**
  extension using fiscal-year-end only.
- Crucially **implementable**: they do not use actual dates. They forecast the
  *announcement month* two ways — (i) last year's announcement month, (ii) the
  firm's fiscal year end mapped through the historical seasonal. "It turns out
  that the results are very similar using actual announcement dates."
- Magnitude: "monthly strategies earning excess returns of **between 7% and 18% per
  year**, with Sharpe ratios larger than other popular anomalies." Fiscal-year-end
  method: **72 bp/month** over 1973–2004. Subperiods: "between **40 and 92 basis
  points a month**", significant in every 10-year block. 1926–1972: **38 bp/month**.
- **Not a small-cap effect**: "the earnings premium is not concentrated in small
  stocks. Using the fiscal year method, it appears uniformly spread across size
  classes. Using the previous year method, it is stronger in **larger** stocks." They
  caveat this is partly Compustat's poor small-firm date coverage. Note their
  portfolios are **value-weighted** in the persistence tests; the headline monthly
  premium is a long-announcers/short-non-announcers spread.
- **Timing within the event** (actual dates, above-median cap only, so not
  tradable): "a pre-announcement run-up of about **25 basis points in the 10 trading
  days prior**, then another **21 basis points earned in the three days around** the
  announcement, and finally an additional **30 basis points** earned in the days
  subsequent" — all three with t > 7. So the premium is a *month-shaped* object,
  not a three-day object.
- Persistence/cross-section: sorting on the past 4 years' own premium gives 0.44%
  vs **1.37%** per month low-vs-high quintile, a **93 bp/month** spread, persistent
  out to 4–6 years.
- Sample coverage caveat: "only **68%** of all firm-years contain the required four
  announcements" (96% by market cap); coverage rises from 50% in 1974 to 95% in 2004.

**Barber, De George, Lehavy & Trueman, "The earnings announcement premium around
the globe", Journal of Financial Economics 108(1), 2013 [PEER-REVIEWED].** ~200,000
annual announcements, ~28,000 firms, **46 countries, 1990–2009** (returns cumulated
April 1991–December 2010), **excluding the US**. Long expected-announcers /
short expected-non-announcers, **value-weighted at firm level**: **59.7 bp/month =
7.16% annualised**; with Fama–MacBeth controls for size, B/M, momentum and country
fixed effects, "**over 11% annually**". Significant in 9 of the 20 largest-sample
countries, ranging **63.4 bp (France) to 235.5 bp (UK)**. Two facts matter here:
(a) "**the bulk of the premium is realized prior to (rather than after) the
announcement day**"; (b) for *interim* (quarterly) announcements internationally
they find **no reliable premium** — only annual ones — whereas F&L find one for US
interims.

**Savor & Wilson, "Earnings Announcements and Systematic Risk" (Dec 2011 draft;
published JFE 2016) [WORKING PAPER / PEER-REVIEWED].** Weekly version: long all
announcers, short all non-announcers, "**annualized abnormal return of 20%**".
Weekly Sharpe **0.131 value-weighted, 0.330 equal-weighted** (annualised 0.94 /
**2.38**) vs 0.049 market. Persistence out to **20 years**. Early announcers
+0.24%, late announcers −0.45% abnormal.

### The strongest negative — and it lands squarely on this programme's window

**Heitz, Narayanamoorthy & Zekhnini, "The Disappearing Earnings Announcement
Premium", SSRN 3296537, working paper (2025 version) [WORKING PAPER].** From the
author-posted abstract: *"The earnings announcement premium, whereby a stock earns
abnormal returns over its earnings announcement period, has been the subject of
extensive research. **We provide the first evidence that this premium has
disappeared in the US in recent years.**"* Their mechanism: the **2004 8-K
disclosure regulation** expanded and accelerated Form 8-K reporting; the
information that used to arrive bundled at the earnings release is now preempted by
8-K filings, and **the premium appears to have shifted from earnings announcement
periods to 8-K filing periods**. They note the disappearance is US-specific — the
premium remains internationally.

**[UNVERIFIED — could not open the paper.]** I could not retrieve the working-paper
PDF: `www-2.rotman.utoronto.ca/.../G_ Narayanamoorthy paper.pdf` returned **HTTP
500** to WebFetch (twice), `www.ssrn.com/abstract=3296537` returned **HTTP 403** to
WebFetch, and `api.semanticscholar.org` returned **HTTP 429**. So I have the claim
and the mechanism from the authors' own posted abstract, but **not** the sample
period, the window definition, the weighting, or the subperiod table. Treat the
magnitude as unverified.

**Heater, et al., "Winning is not enough: Changing landscapes of earnings surprises
and the market reaction", Contemporary Accounting Research (2025) [PEER-REVIEWED,
BUT NUMBER UNVERIFIED].** Search snippets attribute to this literature: *"Average
earnings announcement returns have declined from **0.30% in the 1990s to −0.30% in
the 2010s**, turning negative in the past 17 years."* `onlinelibrary.wiley.com`
returned **HTTP 403** to WebFetch, so I could not verify this against the paper
itself. Flagging it as the single most decision-relevant number in this file that I
**could not verify**.

**Cohen, Dey, Lys & Sunder, "Earnings announcement premia and the limits to
arbitrage", Journal of Accounting and Economics 43(2–3), 2007 [PEER-REVIEWED].**
The earliest decay evidence: premia "persist beyond the sample period examined in
prior studies (ending in 1988), although they **decline in magnitude after 1988**";
premia are **smaller on anticipated dates than on actual dates** (which is exactly
the implementable-vs-not gap); greater voluntary disclosure → smaller premia;
arbitrage costs prevent full elimination. Reported alphas of announcer portfolios
**0.008% to 0.039% per day** [figure from a search summary, not read in the
original — treat as indicative].

### Reading the two sides together

Every strong positive US result ends by **2004** (F&L) or ~2010 (Savor–Wilson). The
global replication excludes the US and ends 2009. The two papers that look at the
US after 2004 both say it is gone. The decay mechanism proposed
(8-K preemption after the 2004 rule) is *specifically* a post-2004 story. This
programme's fixture starts **2010-01-04**. There is no published US evidence of a
live announcement premium overlapping the fixture.

---

## 4. Is the premium just volatility?

The reduction is not just plausible — it is the leading published explanation, and
the literature is split three ways.

1. **Idiosyncratic volatility (the strongest version of the reduction).**
   Barber–De George–Lehavy–Trueman find "the level of **idiosyncratic volatility
   spikes in the three days centered on the earnings announcement date**", and
   cross-country, "the premium is strongest in countries with the **greatest
   increase in idiosyncratic volatility** around the time of their firms' earnings
   announcements, suggesting that **uncertainty over the earnings information to be
   disclosed is a primary driver** of the global announcement premium." They
   instrument abnormal idiosyncratic volatility with each country's CIFAR
   disclosure score and the relation holds. This is the cleanest published
   statement that the premium *is* a volatility premium. Note the direction it
   implies: you are being paid for holding announcement-window variance.

2. **Systematic risk — argued for, and argued against.** Savor & Wilson argue yes:
   announcement betas "explain **37% of the cross-sectional variation** in average
   returns" of 40 test portfolios sorted on B/M, size, short- and long-run
   reversal; implied announcement risk premium **2.1%**; GRS cannot reject zero
   alphas. Against: Barber et al. find no international support — "we do not find
   any reliable evidence that the earnings announcement premium predicts aggregate
   earnings growth internationally … The estimated **market beta on the long-short
   portfolios of the 20 countries … is, on average, zero.** Moreover, the
   correlation in the long-short portfolio returns across countries is
   insignificantly different from zero." Frazzini & Lamont, on their own US data:
   "one type of explanation we certainly **can rule out is systematic risk as
   traditionally defined**."

3. **Attention / retail buying pressure (not risk).** Frazzini & Lamont's own
   answer: sorting on the share of the last 4 years' volume that fell in
   announcement months predicts the premium; "high premium stocks experience the
   highest levels of imputed **small investor buying**". Barber et al. fail to
   replicate this internationally — they find a **negative** relation between
   pre-announcement abnormal volume and the premium.

**Consequence for this programme's standing rule.** The best-supported
cross-sectional explanation (BDLT) says the premium *is* compensation for an
idiosyncratic-volatility spike that is scheduled and predictable. Under the house
rule, a "state" that turns out to be volatility is not a new state — so an
equal-weighted book that goes long announcers is, on the published reading, buying
scheduled idiosyncratic variance. Any study here **must** carry a
volatility-matched control, not merely a count-matched or turnover-matched one.

*Out of scope note:* the sharpest direct test of the risk interpretation (Barth &
So 2011/2016, "Risk Premiums and Non-Diversifiable Earnings Announcement Risk",
1996–2007, >45,000 announcements) runs entirely through **option-implied**
announcement volatility. That is the other team's territory and I did not pursue
it beyond noting it exists.

---

## 5. Overnight vs intraday — the convergence question

**This is the strongest positive finding in this file, and it is a structural fact
rather than an anomaly claim.**

**deHaan, Shevlin & Thornock, "Market (in)attention and the strategic scheduling
and timing of earnings announcements", Journal of Accounting and Economics 60(1),
2015 [PEER-REVIEWED].** Sample **2000–2011**, US common stocks (**CRSP shrcd 10 and
11**), announcement times triangulated from **four** sources (Compustat, I/B/E/S,
RavenPack press-release/first-article timestamps, Wall Street Horizon), retaining
only observations where **at least two sources agree**; 118,351 observations in the
timing panel (151,106 for the descriptive analysis, 120,165 in tests). Verbatim:

> "**34.6% of announcements happen immediately before U.S. market trading hours**
> (i.e., 9:30am to 4:00pm; all times Eastern), while **45.4% happen immediately
> after trading hours. Just 7% of EAs happen during trading hours**, on average.
> The remaining 13% of [announcements] …"

So **~80% of announcements are released outside RTH**, and the first price at which
the news is tradable is an **opening print**. The announcement return, for four out
of five events, is *definitionally* a close-to-open gap.

**Berkman & Truong, "Event Day 0? After-Hours Earnings Announcements", Journal of
Accounting Research 47(1), 2009 [PEER-REVIEWED].** The proportion of after-hours
announcements rose to "more than 40%"; for those, "earnings-related volume and
price changes are **not observed on the Compustat or I/B/E/S earnings announcement
date, but one trading day later**", and "daily price changes and volume are
significantly **biased** if event dates are not adjusted for after-hours
announcements." This is the lag-audit hazard for any runner built here: an
after-close announcement on date *d* pays into the *d+1* overnight gap, and a
before-open announcement on date *d* pays into the *d* overnight gap. Getting this
wrong shifts the return by a full session and will silently move it between the
overnight and intraday buckets — precisely the split the programme cares about.

**Direct overnight-decomposition evidence on earnings [thinner].** Chan & Marsh,
"Overnight Post-Earnings Announcement Drift and SEC Form 8-K Disclosures", SSRN
4765828 (2024) [WORKING PAPER — **abstract not retrieved**, `papers.ssrn.com`
returned **HTTP 403** to WebFetch]. From search summaries only: firms reporting
extreme quarterly earnings misses show pronounced overnight drift post-announcement,
attributed to unscheduled follow-on information arriving overnight in thin
liquidity. Treat as **[UNVERIFIED]**. Bogousslavsky, "The cross-section of intraday
and overnight returns", JFE 141(1), 2021, and Lou–Polk–Skouras (JFE 2019) establish
the general overnight/intraday split for anomalies but I did not find in them a
clean earnings-announcement decomposition; I checked the Lou–Polk–Skouras 2024
market-level paper directly and it contains no earnings-announcement analysis.

**Verdict on the convergence.** The match is real but it is a match of *mechanism*,
not of *result*. The literature does not say "the announcement premium is earned
overnight" in so many words; it says "80% of announcements are released outside
trading hours", which forces the same conclusion arithmetically. That is a genuine
convergence with the programme's own IC decomposition, and it is the reason to
compute anything here at all. It also predicts something checkable: the
announcement return in this fixture should show up almost entirely in the gap, with
little or nothing in the following open-to-close — and if the programme's measured
intraday component is wrong-signed, the announcement-day intraday leg should be
wrong-signed too.

---

## 6. Cost and where the effect lives

- **Cost eats it, on the literature's own numbers.** Chordia et al.: "transaction
  costs account for **70–100 percent of the paper profits**." Ng–Rusticus–Verdi:
  the higher-return firms are the higher-cost firms. Frazzini & Lamont concede
  "Frequent trading is required, thus incurring substantial trading costs" and "high
  idiosyncratic volatility around earnings announcements, which could deter traders
  who for some reason are unable to sufficiently diversify."
- **No published break-even in bp/side that I could verify.** The FAJ and JAR
  papers express cost as a fraction of profits, not as a break-even spread. I did
  not find a paper stating "the announcement premium survives up to X bp/side". If
  this is studied here, the break-even must be computed in-house — and per the house
  rule, from **Corwin–Schultz spreads of the names actually held**, not an assumed
  fee.
- **Turnover.** The announcement premium as published is a **monthly** rotation
  (F&L deliberately used monthly, not daily, portfolios *because* the premium is
  spread over a ~month-long window: −10 days run-up, +3 days event, +10 days after).
  A three-day-window implementation captures only ~21 of the ~76 bp F&L measured in
  event time — i.e. **you pay a full round trip for roughly a quarter of the effect.**
  This is the classic "cost-cutting ≠ edge-sharpening" trap: shortening the hold to
  the event window raises breakeven-per-trade but drops most of the edge.
- **Where the effect lives — and it is not where you'd hope.**
  - PEAD: overwhelmingly **illiquid / microcap** (Chordia et al. 0.04% vs 2.43%;
    Martineau: what remains is "microcap stocks with poor information environment
    (e.g., no analysts coverage)"). Martineau cites Hou et al. (2020): microcaps are
    "only **3.2% of the aggregate market capitalization but 60.7% of the number of
    stocks**".
  - Announcement premium: the one exception — F&L find it "**not concentrated in
    small stocks**", "uniformly spread across size classes", and "stronger in larger
    stocks" under the previous-year method; Savor & Wilson agree it "is not
    restricted to small stocks". BDLT is value-weighted at firm level and still
    finds it. **This is genuinely favourable to a $5-floor universe** — it is the
    only object in this file that does not require the cheap tail. It is also the
    object claimed to be dead post-2004.
  - Price level: no paper I read reports the premium by price decile. Since this
    programme's cost in bp scales inversely with price, that split has to be
    computed in-house.

---

## 7. THE DATA

### 7a. SEC EDGAR 8-K Item 2.02 — the answer. Verified, free, dead-inclusive.

**What the rule says [PRIMARY DATA DOC — SEC Form 8-K, read from the SEC's own
form PDF].** Item 2.02(a), verbatim:

> "If a registrant, or any person acting on its behalf, makes any public
> announcement or release (including any update of an earlier announcement or
> release) disclosing material non-public information regarding the registrant's
> results of operations or financial condition for a completed quarterly or annual
> fiscal period, the registrant shall **disclose the date of the announcement or
> release**, briefly identify the announcement or release and **include the text of
> that announcement or release as an exhibit**."

General Instruction B.1: "a report is to be filed or furnished **within four
business days** after occurrence of the event." B.2: Item 2.02 information is
**furnished, not filed** (no Section 18 liability) — which is why compliance is
cheap and near-universal, but also why it is not a "filing" in the strict sense.

**The coverage holes, from the rule itself:**
- **Instruction 4: "This Item 2.02 does not apply in the case of a disclosure that
  is made in a quarterly report filed with the Commission on Form 10-Q".** A firm
  that never issues a press release and simply files its 10-Q leaves **no 8-K 2.02
  at all**. This will bite the small/quiet tail hardest — the same tail that is
  missing from Compustat's early coverage.
- **Item 2.02(b)** exempts oral/webcast-only disclosure under conditions.
- **The four-business-day window** means the acceptance timestamp is an **upper
  bound** on the release time, not the release time. In practice most issuers file
  same-day or next-day (the press release *is* the exhibit), but this must be
  measured, not assumed.

**What EDGAR actually serves [PRIMARY DATA DOC — verified live].**
`https://data.sec.gov/submissions/CIK##########.json` → `filings.recent` carries
exactly the fields needed:

```
accessionNumber, filingDate, reportDate, acceptanceDateTime,
act, form, fileNumber, filmNumber, items
```

`items` is a comma-separated string of 8-K item numbers, e.g. `"2.02,9.01"`,
`"2.02,8.01,9.01"`, `"2.02,7.01,9.01"`. So **filtering to earnings 8-Ks is a
substring test on a field EDGAR already publishes** — no document parsing needed to
get the date. `reportDate` is the event date (the release date the issuer declares
under 2.02(a)); `filingDate`/`acceptanceDateTime` is when EDGAR took it.

**Dead-name coverage — verified.** I pulled the submissions JSON for **SVB
Financial Group, CIK 0000719739**, which was delisted in 2023. Its Item 2.02 8-Ks
are all still there, e.g.:

| filingDate | reportDate | acceptanceDateTime | items |
|---|---|---|---|
| 2024-01-10 | 2024-01-09 | 2024-01-10T16:06:08.000Z | `2.02,8.01,9.01` |
| 2023-05-09 | 2023-03-31 | 2023-05-09T17:21:57.000Z | `2.02,7.01,9.01` |
| 2023-02-03 | 2023-02-03 | 2023-02-03T10:47:57.000Z | `2.02,8.01,9.01` |
| 2022-05-06 | 2022-05-02 | 2022-05-06T16:19:36.000Z | `2.02,8.01,9.01` |
| 2020-02-03 | 2020-01-30 | 2020-02-03T18:32:35.000Z | `2.02,8.01,9.01` |

EDGAR is permanent: delisting, merger, going private and bankruptcy do not remove
filings. **This is the only free source I found with genuine dead-name coverage.**

**The one real engineering cost: ticker → CIK for dead names.** SVB's JSON shows
`"tickers": []` and `"exchanges": []` — **both empty**. The `tickers` field is
populated from *current* exchange listings, so **every delisted name in the
fixture will have an empty ticker field**, and `company_tickers.json` covers
current registrants only. The JSON does carry `formerNames` (SVB: "SILICON VALLEY
BANCSHARES", 1995-04-13 → 2005-05-24), which helps name-matching but is not a
ticker map. Since the programme already owns an EDGAR puller, it presumably already
solved this; if not, it is the first thing to solve, and the mapping quality must be
audited *by dead-vs-alive*, because a mapping that silently drops dead names
re-introduces exactly the survivorship bias the fixture was built to avoid.

**Bulk access [PRIMARY DATA DOC].**
- `https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip` — all
  submissions JSONs, rebuilt nightly ~3:00 a.m. ET.
- Per-CIK: `https://data.sec.gov/submissions/CIK##########.json`; when a company
  exceeds ~1,000 filings or one year, older filings move into an array of
  additional JSON files listed under `filings.files` with their date ranges — a
  puller must follow those or it will silently truncate history for prolific filers.
- Fair access: "**Current max request rate: 10 requests/second**", and a declared
  `User-Agent` header is required. 1,573 CIKs at 10/s is a couple of minutes, or
  one bulk zip.
- Item 2.02 exists from **August 2004** (the 8-K expansion), which comfortably
  covers 2010-01-04 → 2026-08-26.

**Reliability as an earnings-date proxy — what I could and could not establish.** I
found **no** peer-reviewed study quantifying the fraction of earnings announcements
captured by Item 2.02, or the distribution of (8-K acceptance time − press release
time). Searches for such a comparison against Compustat's `RDQ` returned only
filings and vendor pages. So: **the capture fraction is UNVERIFIED and must be
measured in-house** — which is cheap, because it is a join against the fixture's
own bars. A commercial vendor (**sec-api.io [SALES INSTRUMENT]**) claims its 8-K
dataset holds "2,315,508" records from August 2004 to present and is
"survivorship-bias-free … includes every registrant that has ever furnished an Item
2.02 disclosure, regardless of whether the company is still publicly traded, has
been delisted, merged, gone private, or entered bankruptcy." That is a vendor claim
about *their* product, but it is consistent with what I verified directly on EDGAR.

### 7b. Alpha Vantage

- **`EARNINGS`** — verified live against the `demo` key on IBM. Structure:
  top-level `symbol`, `annualEarnings`, `quarterlyEarnings`. Each
  `quarterlyEarnings` entry carries **`fiscalDateEnding`, `reportedDate`,
  `reportedEPS`, `estimatedEPS`, `surprise`, `surprisePercentage`, `reportTime`** —
  so it ships an **analyst-consensus surprise for free**, and `reportTime` takes
  values **`"post-market"` / `"pre-market"`**. Earliest `fiscalDateEnding` for IBM:
  **1996-03-31**. On paper this is exactly what question 4 needs.
- **`EARNINGS_CALENDAR`** — verified live. CSV header:
  `symbol,name,reportDate,fiscalDateEnding,estimate,currency,timeOfTheDay`.
  It is **forward-looking only** (`horizon` = 3/6/12 month) and lists **currently
  listed** names. Useless for 2010–2026 history and structurally incapable of
  covering delisted tickers. Also `timeOfTheDay` was **blank on 2 of the first 3
  rows** in the live sample I pulled — the flag is present but **sparsely
  populated**.
- **Does `EARNINGS` serve delisted tickers? [UNVERIFIED].** I could not test it: the
  `demo` key is restricted to IBM, and it returned *"The demo API key is for demo
  purposes only. Please claim your free API key…"* for `SIVB`. I did not create an
  account (out of scope, and account creation is prohibited to me). What is
  documented is that Alpha Vantage has a separate **`LISTING_STATUS`** endpoint with
  `state=delisted` returning delisted symbols and delisting dates — so they *know*
  about dead names — but that does not establish that the fundamentals endpoints
  serve them. Given the programme's established finding that AV's **intraday**
  endpoint serves no delisted ticker, the prior should be **against**. **This is a
  five-minute test with a free key and should be run before any design work depends
  on AV.**

### 7c. Other free sources with dead-name coverage

I did not find a second free source with genuine dead-name coverage. Assessed and
rejected: Yahoo/`yfinance` earnings dates (a handful of recent quarters, and
delisted tickers vanish from the symbol master); Nasdaq's earnings calendar
(forward-looking, listed names only); Financial Modeling Prep's historical earnings
calendar (freemium, coverage of dead names undocumented — a vendor claim would need
testing). SEC's XBRL **Financial Statement Data Sets** and the
`companyconcept`/`companyfacts` APIs are free and dead-inclusive but date the
**10-Q/10-K filing**, not the press release — usable for a random-walk EPS surprise,
not for the announcement date. **EDGAR 8-K Item 2.02 is the route.**

### 7d. Before-open vs after-close — can it be computed?

**Yes, from EDGAR alone — with one thing to verify first.**

`acceptanceDateTime` gives a timestamp. **Timezone: I verified one case and it says
UTC.** Apple accession `0000320193-26-000013` carries
`acceptanceDateTime = "2026-05-01T10:01:00.000Z"` in the JSON, and the EDGAR filing
index page for that same accession displays `Accepted: 2026-05-01 06:01:00` — and
06:01 ET + 4h (EDT) = 10:01 UTC. So the JSON's `Z` appears to be honest.
**However**, applying the same conversion to SVB's 2023-02-03 filing
(`10:47:57.000Z`, February, EST = UTC−5) gives 05:47 ET, which is *before* EDGAR's
06:00 ET opening — so my single verification does not settle the convention across
all filings/DST. **Do not build the overnight/intraday split on this until the
timezone convention has been checked against the ET `Accepted` string on a sample of
~100 filings spanning both DST regimes.** That check is free and takes minutes.

Belt and braces: Item 2.02(a) *requires* the issuer to state "the date of the
announcement or release" in the 8-K body, and the release itself is attached as an
exhibit (usually EX-99.1) with its own dateline. So a second, independent timestamp
is available inside the document if the acceptance time proves unreliable — which
also satisfies the house rule that the lag audit be done in a second implementation
that does not call the first.

Classification rule, once the timezone is settled: acceptance before 09:30 ET →
the news is in **that day's** close-to-open gap; after 16:00 ET → **next day's**
gap; between → intraday. Berkman & Truong is the citation for why getting this wrong
biases the event study, and deHaan et al. is the citation for the expected mix
(~35 / ~45 / ~7).

Independent cross-check available: Alpha Vantage's `reportTime`
(`pre-market`/`post-market`) for the alive names, if the endpoint proves usable —
which would let the programme measure the EDGAR-derived flag's error rate against a
second source on the surviving subsample. deHaan et al. found "between **2% and
22%** of earnings announcement times are mismatched between databases", so
disagreement is expected and should be quantified rather than assumed away.

---

## 8. Does it transfer to OUR universe

Bluntly: **PEAD does not. The announcement premium is published as dead over
exactly this fixture's window. The overnight timing fact does transfer, and it is
the only thing here worth a study.**

Point by point.

- **Dates.** 2010-01-04 → 2026-08-26 sits **entirely after** every US sample that
  found a live announcement premium (F&L end 2004; Cohen et al. end ~2005;
  Savor–Wilson ~2010) and **entirely after** the date Martineau says PEAD stopped
  existing for all-but-microcap stocks (2006). There is no overlap with a positive
  published result. If a study here finds a large premium, the prior should be that
  something is wrong with the study, not that the literature is wrong.
- **The $5 floor and the dollar-volume window** delete the population where PEAD
  demonstrably lived (Chordia et al.'s illiquid decile at 2.43%/month vs 0.04% in
  the liquid one; Martineau's microcaps-without-analysts). This is the single most
  decisive transfer failure in the file. The floor is right and should not be
  moved — it just means PEAD is not available to this programme, at any cost level.
- **Per-share commissions** compound it: the surviving PEAD population is cheap
  stocks, where bp-cost is highest. Chordia et al. already found costs at 70–100% of
  profits with *institutional* cost assumptions on a value-weighted book.
- **Equal weighting** is neutral-to-favourable for the *announcement premium*
  specifically — it is the one object here that F&L and Savor–Wilson both say is not
  a small-cap effect, and BDLT find value-weighted. So if it existed, an EW book
  would harvest it. It is the decay, not the weighting, that kills it.
- **Dead-inclusive (43.5%)** is a genuine advantage and a genuine hazard. Advantage:
  EDGAR covers dead names perfectly, so the event labels are not survivorship-biased
  — unlike every vendor calendar. Hazard: the ticker→CIK map is where survivorship
  will sneak back in, since delisted issuers carry **empty ticker arrays**. Any
  runner here needs a match-rate report **split dead vs alive** before it reports a
  return.
- **The overnight edge** is the one convergence. ~80% of announcements are outside
  RTH; the announcement return is a gap; the programme has independently measured
  that its edge is a gap. That is worth one study — but note it is a convergence of
  *mechanism*, and the mechanism being shared does not mean the premium survived.
  The more useful framing is the conditioner one: **do the programme's existing
  overnight returns behave differently on announcement dates than off them?**
- **The 8-K-preemption lead.** Heitz et al.'s claim that the premium **migrated from
  earnings dates to 8-K filing dates** is, if true, directly actionable with the
  tooling the programme already owns — and it is a *different* event set (all 8-K
  items, not just 2.02). But it is a single unpublished working paper whose numbers
  I could not verify, and "the premium moved to a much larger and noisier event set"
  is exactly the sort of claim that dies on a proper null. Note it; do not build on
  it yet.
- **The volatility reduction is live and unrebutted.** BDLT's cross-country result
  says the premium tracks the announcement-window idiosyncratic-volatility spike.
  Under the house rule this is not a new state. Any study must carry a
  volatility-matched control from the start, and the control must randomise the
  *partner*, not the membership (a random subset re-drawn each bar is not a control
  for a scheduled, persistent event set — announcement dates are persistent by
  construction, which is precisely the D291 failure mode).

---

## 9. The premise number to compute first

**Stage 0, before any return is computed: the match rate.**

For each of the 1,573 names, count Item 2.02 8-Ks in EDGAR between 2010-01-04 and
2026-08-26, and report the ratio to the number of quarters the name was in the
tradeable universe. Report it **split three ways: dead vs alive, by price decile,
and by year.** If dead names match materially worse than alive ones, everything
downstream is survivorship-contaminated and the study stops there. Expected shape
if the pull is sound: close to 4/year for names in the universe, with the shortfall
concentrated in the quiet tail that discloses only via 10-Q (Item 2.02 Instruction
4). This costs one EDGAR pull and no return computation, and it is the number that
decides whether the territory is even addressable.

**Then, and only then, the premise number proper:**

> The **equal-weighted gross mean close-to-open return, in bp, on the first
> overnight gap following each Item 2.02 acceptance**, over all 1,573 names,
> 2010–2026 — reported separately for **before-open** and **after-close**
> announcements — against (a) the same names' unconditional overnight mean, and
> (b) a **volatility-matched, calendar-matched** non-announcing control.

Why this one and not the premium itself: it needs **no surprise measure, no
estimates data, no paid vendor**; it is computable from the fixture plus a free
EDGAR pull; it is the single number that tests both the announcement premium's
survival *and* the overnight convergence at once; and it is scored per event, which
keeps it path-invariant and out of the slot-cap machinery entirely at this stage.

Report it as a gross mean per trade with the null distribution beside it (p50 and
p95, and the p95's bootstrap SE), per the house standard. Two things will decide it:
the sign relative to the control, and whether the before-open and after-close
subsets agree — if they disagree, the session assignment is probably wrong, which is
exactly what Berkman & Truong warn about, and the runner's lag audit should be
built to catch that specific inversion.

Predictions to write down *before* running it, in the runner's own quantities:
1. Match rate for alive names ≥ 0.9 of expected quarters; the dead-vs-alive gap is
   the number that matters.
2. The before-open / after-close / intraday mix over the fixture should land near
   deHaan et al.'s 35 / 45 / 7 (their sample is 2000–2011; drift since is plausible,
   large divergence means the timestamp parse is wrong).
3. Given the published decay, the announcement-window gross mean vs a
   volatility-matched control should be **indistinguishable from zero** in
   2010–2026. A large positive result is a bug signal first and a finding second.

---

## 10. Sources

**Announcement premium**
- Frazzini & Lamont, *The Earnings Announcement Premium and Trading Volume*, NBER WP 13090 (2007) — https://www.nber.org/system/files/working_papers/w13090/w13090.pdf — [WORKING PAPER] (read in full)
- Barber, De George, Lehavy & Trueman, *The earnings announcement premium around the globe*, JFE 108(1) 2013 — https://webuser.bus.umich.edu/rlehavy/BDLT.pdf — [PEER-REVIEWED] (read in full)
- Savor & Wilson, *Earnings Announcements and Systematic Risk*, Dec 2011 draft — https://faculty.wharton.upenn.edu/wp-content/uploads/2012/04/Draft20111215p_edited.pdf — [WORKING PAPER] (read in full)
- Cohen, Dey, Lys & Sunder, *Earnings announcement premia and the limits to arbitrage*, JAE 43 (2007) — https://experts.arizona.edu/en/publications/earnings-announcement-premia-and-the-limits-to-arbitrage/ — [PEER-REVIEWED] (abstract only)
- Heitz, Narayanamoorthy & Zekhnini, *The Disappearing Earnings Announcement Premium*, SSRN 3296537 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3296537 — [WORKING PAPER] — **full text not retrieved** (SSRN 403; Rotman mirror HTTP 500 ×2; Semantic Scholar 429). Abstract taken from the author's own page: https://sites.google.com/view/moradzekhnini/home
- Heater et al., *Winning is not enough: Changing landscapes of earnings surprises and the market reaction*, Contemporary Accounting Research (2025) — https://onlinelibrary.wiley.com/doi/10.1111/1911-3846.13034 — [PEER-REVIEWED] — **not retrieved** (Wiley HTTP 403 to WebFetch); the "0.30% → −0.30%" figure is [UNVERIFIED]

**PEAD and its decay**
- Martineau, *Rest in Peace Post-Earnings Announcement Drift*, Critical Finance Review 11(3–4) 2022 — https://cfr.ivo-welch.org/published/papers/martineau2021rest.pdf — [PEER-REVIEWED] (read in full)
- Chordia, Goyal, Sadka, Sadka & Shivakumar, *Liquidity and the Post-Earnings-Announcement Drift*, FAJ 65(4) 2009 — https://ideas.repec.org/a/taf/ufajxx/v65y2009i4p18-32.html — [PEER-REVIEWED] (abstract verbatim; tandfonline itself returned HTTP 403)
- Ng, Rusticus & Verdi, *Implications of Transaction Costs for the Post–Earnings Announcement Drift*, JAR 46(3) 2008 — https://onlinelibrary.wiley.com/doi/10.1111/j.1475-679X.2008.00290.x — [PEER-REVIEWED] (summary only)
- Christensen, Timmermann & Veliyev, *Warp speed price moves: Jumps after earnings announcements*, arXiv 2601.08962 (Jan 2026) — https://arxiv.org/abs/2601.08962 — [WORKING PAPER] (abstract only; PDF exceeded fetch size limit)

**Timing / overnight**
- deHaan, Shevlin & Thornock, *Market (in)attention and the strategic scheduling and timing of earnings announcements*, JAE 60(1) 2015 — https://www.wallstreethorizon.com/upload/SSRN-id2545966_dehaan.pdf — [PEER-REVIEWED] (read in full; note the host is a data vendor, the paper is not)
- Berkman & Truong, *Event Day 0? After-Hours Earnings Announcements*, JAR 47(1) 2009 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=747004 — [PEER-REVIEWED] (summary only)
- Chan & Marsh, *Overnight Post-Earnings Announcement Drift and SEC Form 8-K Disclosures*, SSRN 4765828 (2024) — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4765828 — [WORKING PAPER] — **not retrieved** (SSRN HTTP 403); characterisation is [UNVERIFIED]
- Bogousslavsky, *The cross-section of intraday and overnight returns*, JFE 141(1) 2021 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2869624 — [PEER-REVIEWED] (not read; no earnings decomposition found)
- Lou, Polk & Skouras, *The Day Destroys the Night…* (July 2024) — https://personal.lse.ac.uk/loud/LouPolkSkouras.pdf — [WORKING PAPER] (read; contains **no** earnings-announcement analysis — market-level only)

**Risk / volatility reduction**
- Barth & So, *Risk Premiums and Non-Diversifiable Earnings Announcement Risk* (May 2011) — https://www.hbs.edu/faculty/Shared%20Documents/events/14/Barth.Risk_Premiums_and_Non-Diversifiable_Earnings.pdf — [WORKING PAPER] — **options-based; out of scope, noted only**
- *Earnings announcement premium and return volatility: Is it consistent with risk-return trade-off?*, Pacific-Basin Finance Journal (2023) — https://www.sciencedirect.com/science/article/abs/pii/S0927538X23000951 — [PEER-REVIEWED] (title/abstract snippet only; ScienceDirect HTTP 403)

**Primary data documentation**
- SEC, *Form 8-K* (General Instruction B; Item 2.02 and its Instructions) — https://www.sec.gov/files/form8-k.pdf — [PRIMARY DATA DOC] (read verbatim)
- SEC, *EDGAR Application Programming Interfaces* (submissions JSON, bulk `submissions.zip`, nightly ~3 a.m. ET) — https://www.sec.gov/search-filings/edgar-application-programming-interfaces — [PRIMARY DATA DOC]
- SEC, *Accessing EDGAR Data* — "Current max request rate: 10 requests/second", User-Agent required — https://www.sec.gov/os/accessing-edgar-data — [PRIMARY DATA DOC]
- Live verification, delisted issuer: https://data.sec.gov/submissions/CIK0000719739.json (SVB Financial Group) — [PRIMARY DATA DOC]
- Live verification, timezone: https://data.sec.gov/submissions/CIK0000320193.json vs https://www.sec.gov/Archives/edgar/data/320193/000032019326000013/0000320193-26-000013-index.htm — [PRIMARY DATA DOC]
- Alpha Vantage `EARNINGS` live response (demo key, IBM) — https://www.alphavantage.co/query?function=EARNINGS&symbol=IBM&apikey=demo — [PRIMARY DATA DOC]
- Alpha Vantage `EARNINGS_CALENDAR` live response — https://www.alphavantage.co/query?function=EARNINGS_CALENDAR&horizon=3month&apikey=demo — [PRIMARY DATA DOC]
- Alpha Vantage API documentation — https://www.alphavantage.co/documentation/ — [PRIMARY DATA DOC] (earnings sections did not render to the fetcher)

**Vendor / commercial (label: sales instruments)**
- sec-api.io, *Earnings Results — Form 8-K, Item 2.02 (2004–Present)* — https://sec-api.io/datasets/earnings-results-form-8-k-item-2-02 — [SALES INSTRUMENT] (its survivorship-free claim is consistent with what I verified on EDGAR directly, but is a vendor claim about a paid product)
- Quantpedia, *Earnings Announcement Premium* — https://quantpedia.com/strategies/earnings-announcement-premium — [SALES INSTRUMENT] (not relied on)
- Alpha Architect, *Introducing the Global Earnings Announcement Premium* — https://alphaarchitect.com/introducing-the-global-earnings-announcement-premium/ — [SALES INSTRUMENT] (not relied on; summarises BDLT, which I read directly)
- Macroption, *Alpha Vantage Delisted Stocks* — https://www.macroption.com/alpha-vantage-delisted-stocks/ — [UNVERIFIED THIRD-PARTY BLOG] (covers `LISTING_STATUS` only; says nothing about fundamentals for delisted names)

**Blocks encountered (tool + response, per the house rule)**
- WebFetch → `papers.ssrn.com` and `www.ssrn.com`: HTTP 403 (three separate papers)
- WebFetch → `onlinelibrary.wiley.com`: HTTP 403
- WebFetch → `www.sciencedirect.com`: HTTP 403
- WebFetch → `www.tandfonline.com`: HTTP 403
- WebFetch → `www-2.rotman.utoronto.ca` PDF: HTTP 500, twice
- WebFetch → `api.semanticscholar.org/graph/v1/paper/search`: HTTP 429
- WebFetch → `arxiv.org/pdf/2601.08962`: exceeded the 10 MB fetch limit (abstract page worked)
- Alpha Vantage `demo` key: serves IBM only; returns an "claim your free API key" notice for any other symbol, so delisted-ticker coverage of `EARNINGS` could not be tested
- Several publisher PDFs did not parse through WebFetch's converter; where the PDF was saved locally I extracted the text with `pypdf` and read it directly (Frazzini–Lamont, Martineau, Barber et al., Savor–Wilson, deHaan et al., SEC Form 8-K, Barth & So, Lou–Polk–Skouras).
