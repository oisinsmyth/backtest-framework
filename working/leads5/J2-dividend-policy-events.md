# J2 — Dividend policy events: initiations, cuts and omissions, and specials, by DECLARATION date

External-evidence brief. Round 5. Written 2026-09-10.
**I have no access to the programme's data and claim nothing about it.** Every number below is
either from a cited external source (tagged by type and by how well I established it) or from a
measurement I made myself against a free public endpoint, in which case the script, the raw call
and the **negative control** are named so it can be re-run. Scripts referenced live in the
session scratchpad and are reproduced in §7.

Initiations/increases and cuts/omissions are reported **separately throughout**. They are never
pooled, never averaged together, and never share a table.

---

## 0. THE ASYMMETRY THE LANE WAS COMMISSIONED ON — MEASURED, AND IT IS NOT THERE

**The commissioning premise is directionally right and quantitatively immaterial, and that is the
first thing this brief has to say.** I harvested 4,521 dividend-policy 8-K filings from SEC EDGAR
full-text search (2010–2025), recovered the **as-traded** close before each filing, and split the
three families across price terciles of a dated market cross-section. Cuts are *not* a cheap-tail
event:

| family | n priced | p25 | **MEDIAN** | p75 | share < $5 | T1 (cheap) | T2 | T3 (rich) | 50/P at median |
|---|---|---|---|---|---|---|---|---|---|
| **INITIATIONS** | 537 | $15.44 | **$28.19** | $47.86 | **7.3%** | **7.6%** | 27.6% | 64.8% | 1.8 bp |
| **CUTS / SUSPENSIONS** | 263 | $10.00 | **$28.45** | $37.77 | **10.3%** | **12.2%** | 35.0% | 52.9% | 1.8 bp |
| **SPECIALS** | 1,586 | $13.14 | **$26.14** | $47.09 | 8.9% | 9.6% | 30.6% | 59.8% | 1.9 bp |
| *market reference* | 450 | $2.62 | *$11.00* | $29.23 | *32.2%* | *33.3%* | *33.3%* | *33.3%* | *4.5 bp* |

Tercile boundaries $5.27 / $21.12, taken from 900 randomly drawn SEC registrants priced on
randomly drawn event dates. Full method and controls in §7.

**The median firm cutting its dividend trades at $28.45. The median firm initiating one trades at
$28.19. They are the same price.** Both families are ~2.6× richer than the market cross-section,
and only 7–10% of either sits below $5 against 32.2% of the market. **Per-share commission is
1.8 bp at the median for both. Killer 1 does not kill this territory — for either leg.** The
premise that cuts live in the cheap tail while initiations sit above it is wrong as stated, and
the reason is worth stating precisely, because it separates two axes this programme has been
treating as one:

> **Firms that cut dividends ARE small, and their stocks are NOT cheap.** Cotter et al. (§2.4)
> measure cutters as smaller, riskier, lower-ROA and worse-performing than the market — the
> commissioning premise is right about *size*. But a company has to have been paying a dividend to
> cut one, and the population of dividend payers is filtered on exactly the history that keeps a
> share price in double digits. **Size and per-share price are different axes, and this territory
> is the case that pulls them apart.** A lane screened only on "are these small firms?" would have
> been closed on a cost argument that does not apply to it.

The asymmetry that *does* exist is real but small and lives in the lower half, not the middle:
the cut distribution's **p25 is $10.00 against $15.44 for initiations**, and cuts are **12.2% vs
7.6%** in the cheapest tercile — a 1.6× tilt. That is a second-order cost effect, not a lane-killer.

**Two caveats, and the first cuts against me.** (i) Survivorship: I could price only 48.3% of cut
filings against 56.5% of initiation filings, and the unpriced are disproportionately names that
died. Dead cutters are cheap cutters, so **the true cut distribution is cheaper than the table
says, by an unknown amount** — the 8-point gap in loss rate is itself the evidence. (ii) The
numbers above are as-traded only because I undid Yahoo's split adjustment; before that fix NVDA's
2012 initiation read **$0.32** and CIM Commercial's special read **$355,514** (§7.3).

**So this territory does not die of price. It dies of breadth, of decay, and of anticipation:**

- **Breadth.** Through a $5-close and $1m/day floor I count **26.2 initiations, 12.5 cuts and 63.4
  specials per year** — 0.104, 0.050 and 0.252 events per trading day. These are lower bounds
  (§7.2), but the census that is not a lower bound agrees on the order: S&P Dow Jones Indices, whose
  universe is all U.S. domestic common stocks, counted **176 dividend decreases in all of 2025 and
  132 in all of 2024** (§2.3). Against a book with ~10 effective independent instruments, the cut
  leg is a fraction of one.
- **Decay.** Amihud and Li's Table 1, read in full from the PDF: the two-day reaction to dividend
  **increases** fell from +1.17% (1962–74) to **+0.44% mean, +0.23% median (1988–2000)**; to
  **decreases** from −6.43% to **−2.63% mean, −1.77% median**. A 23 bp median against a 67.6 bp
  round trip was already dead by 2000, and that is where the published series *ends*.
- **Anticipation.** The one modern working paper on the question finds increases are *more
  anticipated* than decreases and that correcting for anticipation **explains the famous asymmetry**
  (§4.2). Anything you can forecast well enough to be positioned before the print is already in the
  price; anything you cannot, you cannot trade.
- **Replication.** The initiation drift — the only leg with a long-horizon story — was called a
  product of chance by Boehme and Sorescu (2002) and the 2014 replication that set out to rescue it
  **failed to** (§1.3).
- **And the event is mostly not a dividend event at all.** I measured the 8-K item codes on every
  filing I harvested: **62.2% of dividend initiations and 59.2% of dividend cuts are filed under
  Item 2.02, "Results of Operations and Financial Condition" — the same document as the quarterly
  earnings release, on the same timestamp** (§7.4). The share is *rising*: 41% → 72% for
  initiations and 40% → 80% for cuts between 2010 and 2024. At daily resolution these are not two
  events, they are one. **Earnings announcement dates and PEAD are on this programme's exclusion
  list, and for six events in ten this territory IS that territory.**

**Disposition I would argue for: CLOSED on the returns evidence for initiations and increases;
CLOSED on breadth for cuts and omissions; CLOSED on both for specials, where the event is
additionally documented to be predictable and the names are the illiquid ones. Separately blocked
on data: no free feed carries a usable declaration date before 2020 (§5.2). The principal closes
avenues, not me.**

---

## 1. DIVIDEND INITIATIONS

### 1.1 The canonical result, read from the primary document

**Michaely, Thaler and Womack, "Price Reactions to Dividend Initiations and Omissions:
Overreaction or Drift?"** [PEER-REVIEWED] (J. Finance 50, 573–608, 1995). I read the **NBER
Working Paper #4778, June 1994** version **in full** — it is a scanned image PDF, so I extracted
the page rasters with `pypdf` and read them visually rather than trusting any text layer or
summariser. Abstract, verbatim from the scan:

- **"short run price reactions to omissions are greater than for initiations (−7.0% vs. +3.4%
  three day return)"**
- **"when we control for the change in the magnitude of dividend yield (which is larger for
  omissions), the asymmetry shrinks or disappears, depending on the specification"** — *every
  secondary summary I encountered omitted this sentence. The famous asymmetry is a dividend-size
  effect, at least in part.*
- "In the 12 months after the announcement (excluding the event calendar month), there is a
  significant positive market-adjusted return for firms initiating dividends of **+7.5%** and a
  significant negative market-adjusted return for firms omitting dividends of **−11.0%**."
- "the post dividend omission drift is distinct from and more pronounced than that following
  earnings surprises"
- "A trading rule employing both samples (long in initiation stocks and short in omission stocks)
  earns positive returns in **22 out of 25 years**."

Sample, read from page 4 of the scan: **CRSP NYSE/AMEX, 1964–1988**, initiation defined as "the
first cash dividend payment reported on the CRSP Master File", re-institutions **excluded**,
requiring two years of prior listing. **NASDAQ is not in the sample.** For a universe of 1,573
mostly-NASDAQ US names this is a material mismatch, and the exchange restriction is not a detail:
it removes precisely the small, cheap tail.

### 1.2 The magnitude, and where inside the sample it lives

**Bulan, Subramanian and Tanlu, "On the Timing of Dividend Initiations"** [PEER-REVIEWED]
[read in full — local PDF from the author's Brandeis page]. 368 initiations, 1966–1998, firms
followed from IPO; 329 with announcement returns.

- 3-day CAR: **mean 3.81%, MEDIAN 2.24%, SD 8.63%, min −16.29%, max +53.54%.** The mean-above-
  median gap and the 8.63% SD say this is a fat right tail, not a reliable 380 bp.
- **The announcement return is *decreasing* in size: the coefficient on Log Assets is −0.0102
  (p = 0.010), robust across six specifications.** The larger the initiator, the smaller the pop.
  So even for initiations, the return that exists lives in the *smaller* names.
- Initiator characteristics: **assets mean $203m, MEDIAN $36m.** The paper's summary that
  "dividend initiators are large and stable firms" is relative to *their own post-IPO cohort*, not
  to the market. **A median initiator with $36m of assets is a microcap.** This is a direct
  correction to the commissioning premise's reasoning, though — see §0 — the *price* measurement
  does not follow the size measurement, because these firms are small in market cap without being
  cheap per share.
- Initial dividend yield: **mean 0.98%, median 0.53%.** The cash itself is tiny.
- Per-year initiation counts from the paper's Table I: 0–33 per year, **368 over 33 years ≈ 11/yr**
  on their (post-IPO, non-regulated, non-financial) construction.

### 1.3 The drift does not replicate — this is the decisive negative

**Boehme and Sorescu, "The Long-Run Performance Following Dividend Initiations and Resumptions:
Underreaction or Product of Chance?"** [PEER-REVIEWED] (J. Finance 57, 871–900, 2002)
[abstract only — I did not open the paper; the numbers below are from the SSRN/RePEc abstract and
from Chen et al.'s description of it]. 1927–1998. Post-announcement abnormal returns are
**significantly positive equal-weighted but insignificant value-weighted**, and confined to
1964–1998 with nothing before 1964. They attribute the drift to declines in Fama-French factor
loadings and call it **sample-specific chance**.

**Chen, Chou and Lee, "The long-term performance following dividend initiations and resumptions
revisited"** [PEER-REVIEWED] (J. Economics and Finance 38(4), 643–657, 2014)
[abstract only, quoted verbatim from RePEc, which I fetched directly]. This paper set out to
*rescue* the drift by removing what it believed were confounds in Boehme–Sorescu — newly-IPO'd
firms and regulated firms. It failed: **"We find no evidence that the non-robust positive price
drifts for firms, which initiate or resume cash dividends, is due to the confounding effects of
IPOs and regulated firms."**

That is a replication attempt, by authors motivated to find the effect, on a cleaner sample,
reporting the null. The +7.5% MTW initiation drift should be treated as not established.

### 1.4 What survives post-2010

Nothing I could find establishes a post-2010 initiation announcement or drift effect on a US
sample at a magnitude that clears cost. The most recent large-sample work I located that *touches*
it — **Lee and Mauck, "Dividend initiations, increases and idiosyncratic volatility"**
[PEER-REVIEWED] (J. Corporate Finance 40, 47–60, 2016), US firms 1963–2013 [**abstract/summary
only** — the SSRN PDF link returned an HTML landing page, not a PDF, so I did not open it] —
reports that firms with **higher idiosyncratic volatility** earn higher announcement abnormal
returns on initiations and increases, and that **high idiosyncratic volatility firms show the
stronger positive post-event drift**. High idio-vol is the small, wide-spread tail. Whatever
survives is concentrated in the part of the universe this programme's cost structure punishes
hardest — and note this is a *spread* problem, not the per-share commission problem of §0.

**My own count of initiations is falling steeply.** Distinct companies whose first EDGAR
initiation-language 8-K falls in each year (method and precision check in §7.2):

| 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 44 | 43 | 63 | **80** | 57 | 35 | 28 | 29 | 43 | 38 | 30 | 36 | 24 | 25 | 27 | **21** |

623 distinct initiating companies over 16 years, **38.9/yr, down ~74% from the 2013 peak.**

---

## 2. DIVIDEND CUTS AND OMISSIONS — reported separately, as instructed

### 2.1 Magnitudes, and the decay, read in full

**Amihud and Li, "The Declining Information Content of Dividend Announcements and the Effects of
Institutional Holdings"** [PEER-REVIEWED, published JFQA 2006, 637–660] — **but what I read is the
WORKING-PAPER version hosted at hofstra.edu, not the published article. [read in full: I downloaded
that PDF and extracted Table 1 locally.]** Published numbers may differ from the ones below.
CRSP, 1962–2000, two-day CAR (days 0,+1) relative to the stock's size-decile portfolio.

| period | INCREASES mean (t) | median | N | DECREASES mean (t) | median | N |
|---|---|---|---|---|---|---|
| 1962–2000 | +0.87% (31.60) | +0.58% | 14,911 | −4.58% (−24.38) | −3.68% | 1,278 |
| 1962–1974 | +1.17% (20.82) | +0.81% | 3,934 | −6.43% (−19.55) | −5.97% | 416 |
| 1975–1987 | +0.94% (23.05) | +0.65% | 7,251 | −4.29% (−15.33) | −3.55% | 548 |
| **1988–2000** | **+0.44% (8.97)** | **+0.23%** | 3,726 | **−2.63% (−7.31)** | **−1.77%** | 314 |
| 1971–1975 (peak) | +1.41% (15.92) | +0.97% | 2,147 | −6.24% (−13.54) | −5.29% | 239 |
| **1996–2000 (last)** | **+0.47% (4.65)** | **+0.23%** | 1,144 | **−2.19% (−3.59)** | **−1.49%** | 109 |

Read the medians, not the means. **By 1996–2000 the median dividend increase moved the stock
23 bp and the median decrease −149 bp.** A round trip here is ~67.6 bp plus 1.8 bp commission.
The increase leg was already under water at the median a quarter of a century ago. The decrease
leg clears it — but see §2.3 on how many there are, and note this is the *announcement-day* move,
available only to someone already positioned.

Their Table 2 is worse for a trader: the pre-announcement window (days −11 to −2), 1988–2000, is
**+0.23% (t = 2.47) for increases and −0.60% (t = 1.16, insignificant) for decreases.** There is
no established modern run-up to trade into a cut.

**Grullon, Michaely and Swaminathan (2002)**, dividend changes ≥10%, 1967–1993: increases +1.34%,
decreases −3.71% [**summariser only** — these figures come from a search-result summary; I did not
open the paper. They are consistent with Amihud–Li's full-sample −4.58%/+0.87% but I did not verify
them at source].

### 2.2 The drift after cuts is the earnings drift — the confound, answered

This is the single most important negative in the territory, and it answers the confound the brief
was told to address head-on.

**Liu, Szewczyk and Zantout, "Underreaction to Dividend Reductions and Omissions?"**
[PEER-REVIEWED] (J. Finance 63(2), 987–1020, April 2008) [**abstract only — I did not open the
paper**; the quotes below are verbatim from the RePEc abstract page, which I fetched directly
rather than taking through a search summary]. **2,337 cash dividend reduction or omission
announcements, 1927–1999.** Initially *"significant negative post-announcement long-term abnormal
returns, which last 1 year only"* — but this disappears after accounting for earnings performance
and the skewness of buy-and-hold abnormal returns, and the authors conclude there is
**"no compelling evidence of a post-dividend-reduction or post-dividend-omission price drift."**

So: MTW's −11.0% omission drift, the most-cited number in the territory, is reported by a later
JF paper to be PEAD wearing a dividend costume. **PEAD is on this programme's exclusion list.
If the cut drift is the earnings drift, this lane is re-researching excluded ground.**

The confound is not merely statistical, it is mechanical, and **I measured it: 59.2% of the cut
filings and 62.2% of the initiation filings I harvested also carry Item 2.02, "Results of
Operations and Financial Condition" — the earnings release, in the same 8-K on the same date**
(full table and the rising trend in §7.4). The very first initiation hit I inspected (GlobalSCAPE,
2015-04-30) is items `["2.02","9.01"]`. Where the dividend decision and the earnings number arrive
in one document on one timestamp, **no daily-bar study can attribute the move to the dividend**,
and any published announcement CAR is a joint effect unless its authors screened the joint filings
out. MTW and Cotter et al. discuss the issue; the Amihud–Li working paper, as far as I read it,
does not.

### 2.3 How many cuts there are — the kill number

**S&P Dow Jones Indices** [PRIMARY DATA DOC — a market-wide census, not a vendor return claim]
[**read from the raw HTML of the press release, which I fetched and grepped directly**, not
through a summariser]. Universe: U.S. domestic common stocks. Definitions quoted verbatim from the
release: *"Dividend Increases (defined as either an increase or initiation in dividend payments)"*
and *"Dividend Decreases (defined as either a decrease or suspension in dividend payments)"*.

- **2025: 2,293 issues increased. 176 issues decreased.**
- **2024: 2,450 issues increased. 132 issues decreased.**
- Q4 2025: 634 increases, 38 decreases. Q4 2024: 635 increases, 33 decreases.
- 2020, verbatim: *"the 2020 net change negative as 43 S&P 500 issues suspended their dividends at
  −$40.8 billion."*

**176 cuts per year, across the entire US market, before any floor.** That is 0.70 per trading day
including sub-$5 names, OTC-adjacent names, funds and trusts. Increases outnumber decreases 13:1.

Corroborating, on a cleaner academic construction: **Cotter, von Eije, Farooq and Muckley,
"Investor anticipation and the stock price reaction to dividend changes"** (working paper,
January 2023) [WORKING PAPER] [**read in full — I downloaded the EFMA 2023 conference PDF and
extracted it locally**]: NYSE/AMEX/NASDAQ 1967–2015, quarterly taxable cash dividends, changes
≥12.5%, **excluding utilities (SIC 4900–4949) and financials (SIC 6000–6999)**: **11,134 dividend
increases, 1,492 dividend decreases, 582 dividend omissions.** Over 49 years that is 227 increases,
**30 decreases and 12 omissions per year**. (The exclusion of financials and utilities is why this
is below the S&P count; for this programme's universe those sectors are in, so the truth is
between the two.)

**Li and Lie, "Dividend changes and catering incentives"** [PEER-REVIEWED, published JFE 2006]
[read in full — but the PDF on the author's Iowa page is the **accepted manuscript** ("accepted
21 March 2005"), not the typeset article]: **1,815 dividend decreases and 18,964 dividend
increases, 1963–2000** — 48 and 499 per year, the same 10:1 ratio.

**My own harvest** (lower bound, §7.2): distinct company-years with cut language, 2010–2025:

| 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 37 | 20 | 19 | 25 | 11 | 25 | 21 | 17 | 16 | 18 | **77** | 18 | 10 | 13 | 20 | 20 |

mean 22.9/yr. **The 2020 spike to 77 — 3.4× the surrounding years — is a positive control on the
harvest**: it reproduces the known COVID suspension wave that S&P independently records as 43
S&P 500 issues suspending. A method that could not see 2020 would not be worth reporting.

### 2.4 Where cuts live

Cotter et al., read in full: *"Dividend decreasing firms tend to be smaller (lower TA), have poorer
past returns (BHAR), higher idiosyncratic risk (IRISK), lower return on assets (ROA), lower
market-to-book ratios, higher leverage, lower cash holdings, more volatile earnings and lower
changes in the size of total assets."* Dividend increasers are the mirror image: *"larger, higher
past returns, lower idiosyncratic risk, higher ROA."*

**So the commissioning premise is confirmed on SIZE and refuted on PRICE.** Cutters are smaller,
riskier and worse-performing — and still trade at a $28.45 median (§0), because a firm has to have
been a dividend payer to cut, and dividend payers are not $3 stocks. Size and price are not the
same axis, and this territory is the case that separates them.

---

## 3. SPECIAL / ONE-OFF DIVIDENDS

### 3.1 The event has largely stopped existing, and what remains is predictable

**DeAngelo, DeAngelo and Skinner, "Special dividends and the evolution of dividend signaling"**
[PEER-REVIEWED] (JFE 57, 309–354, 2000) [**read in full — I downloaded the PDF from the USC
author page and extracted it locally**]. Abstract, verbatim:

> "(1) special dividends were once commonly paid by NYSE firms, but are now rarely paid; (2) firms
> typically paid specials almost as predictably as they paid regular dividends; (3) despite the
> dramatic overall decline in specials, the incidence of very large specials increased in recent
> years; and (4) special dividends were not displaced by stock repurchases."

The decay, in their numbers, quoted from the paper: **"During the 1940s, 61.7% of dividend-paying
NYSE firms paid at least one special, while only 4.9% did so during the first half of the 1990s.
In the single year 1950, 45.8% of dividend-paying NYSE firms paid specials, while just 1.4% of
such firms paid specials in 1995."** Among firms that paid them, specials averaged **24.3% (median
16.8%)** of total dividends. Their one countervailing finding: **large specials — at least 5% or
10% of equity value — *increased* in importance**, which is the population the FINRA ≥25% ex-date
rule in §3.2 catches.

Point (2) is the one that matters for a signal lane. **A recurring, predictable payment is not
news.** The event study (their Table 8 and the regression below), NYSE firms, mid-1962–1995:

> AR = 0.008 − 0.023·OMIT + 0.024·CHG − 0.071·OMIT×CHG
> (t: 6.16, −2.00, 1.54, −1.10)

- The intercept is the whole story: **+0.8% three-day abnormal return** on a special declaration
  with the regular dividend held constant.
- **The coefficient on the size of the special (CHG) is insignificant (t = 1.54).** The market does
  not price the amount. There is no magnitude signal to sort on.
- Verbatim: *"we observe a significantly positive average stock market reaction even when firms
  reduce special dividends (to a still-positive level)"*, and *"statistically indistinguishable
  positive average abnormal returns for increases and decreases in the special dividend."* An
  event whose sign does not depend on its content.
- Failing to pay a special after paying one the prior year produces an *"essentially zero market
  response"* — because nobody announces a non-declaration, there is no timestamp to trade.
- Where firms cut the regular *and* omitted the special (n = 25): **−1.32%**.

**My harvest independently reproduces the predictability.** Over 2010–2025 I find 3,026 special-
dividend 8-K filings across **844 distinct companies and 1,811 distinct company-years — 2.15
special-paying years per company, 3.59 filings per company.** Specials recur at the same names.
That is DeAngelo's central finding, still true 25 years later, measured on a different dataset.

### 3.2 The ex-date does behave differently, and it is a rule, not an anomaly

**FINRA Rule 11140(b)(2)** [PRIMARY DATA DOC] [the operative sentence retrieved via WebFetch of
finra.org; I did not open the full rulebook page myself, so treat the surrounding paragraphs as
unread]:

> "In respect to cash dividends or distributions, stock dividends and/or splits, and the
> distribution of warrants, which are 25 percent or greater of the value of the subject security,
> the ex-dividend date shall be the **first business day following the payable date**."

For ordinary dividends the ex-date is the business day before the record date; **for a special of
≥25% of the price the ex-date jumps to *after* the cash is paid**, with the shares trading with
due-bills attached in between. This is the single most dangerous mechanical trap in the territory:
a fixture that assumes ex-date ≈ record-date − 1 will place a large special's price drop **weeks
early**, and will do so only for the largest specials — i.e. exactly the ones with enough
magnitude to look like a signal. DeAngelo et al. document that large specials are the ones that
*survived*, so the trap and the surviving population coincide.

I could not establish a clean modern magnitude for special ex-day abnormal returns. The obvious
source — *"Ex-dividend day abnormal returns for special dividends"*, J. Economics and Finance
(2015) — was **blocked** (§8).

### 3.3 The counts, and the liquidity problem

Special-dividend 8-K filings per year from my harvest: 163, 115, **327**, 257, 191, 204, 185, 217,
216, 168, 138, 212, 163, 159, 147, 164 (2010→2025). Through a $5 + $1m/day floor: **63.4/yr**.

**The 2012 spike (327, the series maximum) is a second positive control.** Q4 2012 saw a
tax-driven wave of specials ahead of the expiry of the Bush-era dividend rate; an independent
study counts **320 special dividend announcements in October–December 2012 alone**
(*"The Impact of Special Dividend Announcements, Insider Ownership, and Tax"*, hosted on the NYU
Stern site) [WORKING PAPER — it reads as a student thesis; I read its abstract only and I am
citing it **for the count, not for its returns**, which I would not rely on].

**But specials are the illiquid family.** Of the special-dividend names above $5, the median
20-day dollar volume is **$4.07m and 29.8% trade under $1m/day** — against $12.49m/15.9% for
initiations and $19.80m/15.3% for cuts. Whatever the announcement is worth, it is worth it in the
names where a slot-limited book cannot get size on without moving the print.

---

## 4. INCREASES OF UNUSUAL SIZE

### 4.1 The literature does separate them, thinly

**Asem, "Understanding the price reaction to large dividend increases"** [PEER-REVIEWED]
(Finance Research Letters 54, 2023) [**abstract only, and via a search-result summary at that —
I did not open the paper and I did not see the numbers in situ**]. CRSP, July 1962–2018. The
reported findings: the abnormal return to large increases **"mutes on the announcement day but not
the day after"**; for increases above 100%, **61.4% of the incremental information accrues on the
day after announcement** against 30.9% for increases of at most 20%; the interpretation offered is
market uncertainty about dividend volatility.

**This is the one result in the whole territory that points at this book's stated edge (overnight),
and I am flagging it as the thing I could least establish.** It is a *share*, not a level: "61.4%
of the incremental information" says nothing about how many basis points that is, and Amihud–Li's
full-sample increase reaction is +0.87% falling to +0.44%. 61% of 44 bp is 27 bp, below the round
trip. I could not open the paper to check whether the level survives, whether the split is
computed on a lag-safe basis, or whether it holds after 2010. **If any part of J2 were to be
re-opened, this is the only sentence in the brief I would re-open it on, and it needs the actual
paper.**

Threshold conventions in the literature, for what it is worth: Grullon–Michaely–Swaminathan and
Cotter et al. use **≥12.5%** as "economically significant"; Asem uses **>100%** for "large";
Cotter et al. discard increases **>500%** as data errors.

### 4.2 Anticipation — why a bigger number is not a bigger surprise

**Cotter, von Eije, Farooq and Muckley (2023)** [WORKING PAPER] [read in full, local PDF].
Abstract, verbatim:

> "We document market anticipation of dividend changes and show that more anticipated dividend
> changes are associated with lower announcement returns... We also find that dividend increases
> are **more anticipated** than dividend decreases and that correcting for this **explains the
> well-documented asymmetry in their market reactions**."

They build a recursive multinomial logit on public data only, and it works: sorting on the
estimated probability of an increase, quintile 5 produces **3,812 increase announcements (16.12%
of that quintile's announcements)** against quintile 1's **956 (3.93%)** — a 12.19% spread,
significant at 1%.

Two consequences, in opposite directions, and both matter here:

1. **Against the lane.** The market anticipates these events, so the announcement CAR understates
   the information and *overstates* what is left to capture at the print. And the celebrated
   increase/decrease asymmetry — the reason a cut looks like the better leg — is substantially an
   anticipation artifact rather than a behavioural fact.
2. **A pre-registration trap.** Their sort is a *predictor of the event*, formed from public data.
   It is not a return predictor and the paper does not claim it is. Sorting names by "probability
   of a dividend increase" and going long is not a strategy this paper supports; the whole point is
   that the anticipated ones pay *less*.

**Also relevant, and unopened:** Andres and Hofbaur, *"Do what you did four quarters ago: Trends
and implications of quarterly dividends"*, J. Corporate Finance 43 (2017) [snippet only]. The
premise in the title is the problem: dividend decisions are largely a repeat of the same quarter a
year earlier, which is why they are forecastable and why the announcement is not news.

---

## 5. THE DATA QUESTION

### 5.1 Does a corporate-action feed distinguish a first-ever dividend from a routine one?

**No free one does, and the paid one that comes closest still does not.**

The distinction a feed *can* make is **special vs regular**, and that is not the same question.
**Polygon.io** (now redirecting to massive.com) documents `dividend_type` with values **CD** —
dividends *"paid and/or expected to be paid on consistent schedules"* — and **SC** — *"Special Cash
dividends that have been paid that are infrequent or unusual, and/or can not be expected to occur
in the future"*; plus `frequency` where **0 = one-time**; plus `declaration_date`, queryable
[the field semantics are from a search-result summary of the docs and from the vendor knowledge-base
article — **the docs page itself 404'd via its own redirect** (§8), so I have not read the schema in
situ]. **I confirmed the endpoint exists and is gated**: an unauthenticated call returns
`{"status":"ERROR","error":"API Key was not provided"}`. **I did not create an account and did not
obtain a key**, so I cannot report its coverage, its history depth, or whether it carries delisted
names.

**Nothing in any schema I found flags a first-ever dividend.** An initiation is definitionally the
*absence* of any prior dividend, which is not a property of a row — it is a property of a complete
history. To identify it you need the full dividend record for that CIK/permno back past the
company's listing, **including for names that later died**, and you need to distinguish a genuine
initiation from (a) a resumption after an omission, (b) a firm that paid dividends on another
exchange before listing, and (c) a firm whose earlier dividends predate the feed's coverage start.
MTW hit exactly problem (b) and solved it with a two-year prior-listing rule that they concede
*"excludes a substantial number of potential initiation candidates"* — i.e. the standard fix
trades a false-positive problem for a large, non-random sample loss.

### 5.2 Does a free feed carry the DECLARATION date? Measured: nominally yes, actually no.

**Alpha Vantage's `DIVIDENDS` endpoint returns exactly five fields — `ex_dividend_date`,
`declaration_date`, `record_date`, `payment_date`, `amount`.** No type flag, no frequency, no
first-ever flag. I called it with the `demo` key printed in the vendor's own documentation
(I created no account and supplied no credentials). For IBM it returns **111 rows, 1999-02-08 to
2026-08-10**. Coverage of the declaration date, by ex-date year:

| 1999–2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| **0 of 84 rows** | 1 of 4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 3/3 |

**87 of 111 rows carry `declaration_date: "None"`. The field is empty for everything before
Q4 2020.** For a fixture running 2010-01-04 to 2026-08-26, the declaration date — the *only* date
this territory is about — would be missing for roughly the first eleven of sixteen and a half
years. This is a single ticker (the demo key refuses all others, §8) and I flag that limit
explicitly, but the pattern is a coverage start, not a per-name gap.

### 5.3 What IS free, dead-inclusive and point-in-time

**SEC EDGAR is the only source that is all three, and it is unstructured.** EDGAR full-text search
(`efts.sec.gov`, 2001–present) is free, requires no key, keeps the filings of dead companies
forever, and the 8-K filing date is within four business days of the event and usually the same
day. It is what I used. Three defects, all measured:

1. **A cut is textually invisible.** A dividend cut is usually announced by declaring a *lower
   number*, not by using the word "reduce". Across seventeen cut phrasings in 2015, EDGAR returned
   1, 0, 0, 0, 0, 10, 0, 1, 0, 0, 1, 0, 32, 0, 6, 0, 0 hits — against a true count near 100–150.
   **Cuts and initiations are both defined by *comparison to the prior dividend*, which no amount of
   text search recovers. Both require the dividend time series.**
2. **EDGAR's own metadata is survivorship-biased.** `display_names` carries a ticker only for
   filers that still map to one: **36.6% of initiation filings, 40.8% of cut filings and 38.4% of
   special filings have no ticker at all.** The missing ones skew dead.
3. **A ticker without a price source is no better.** Yahoo's chart endpoint — the only free,
   key-free daily price source I could reach — returns **nothing** for Sears Holdings (SHLD) in
   2015, four years before it delisted. Free price data is not dead-inclusive.

**What would be needed:** a dividend history keyed on a permanent identifier (not ticker), complete
from before the fixture's start, covering delisted names, carrying declaration date and a
special/regular flag. That is CRSP's distribution file (codes 1212/1232/1242/1252, as MTW and Bulan
both use) or a paid equivalent such as Sharadar's ACTIONS. **I found no free substitute, and the
free candidates fail on different axes: EDGAR has the dates and the dead names but no structure,
Alpha Vantage has the structure but no declaration dates before 2020, Yahoo has the prices but not
the dead names.**

---

## 6. THE CASH IS ALREADY IN THE RETURN SERIES — WHICH PUBLISHED EFFECTS ARE WHICH

The caution is correct and it disqualifies a large fraction of this literature. Sorting it:

**(a) ANNOUNCEMENT REPRICING — not the cash, potentially tradeable in principle.** These are
revaluations on the declaration date and are *additional* to any total-return treatment of the
payment itself:
- MTW's +3.4% / −7.0% three-day reactions (§1.1).
- Amihud–Li's +0.44% / −2.63% two-day reactions, 1988–2000 (§2.1).
- Bulan's +3.81% mean / +2.24% median initiation CAR (§1.2).
- DeAngelo et al.'s +0.8% special-declaration reaction (§3.1).
- Asem's day-0 / day+1 split for large increases (§4.1).
- MTW's +7.5% / −11.0% twelve-month drifts, and Liu et al.'s finding that the cut drift is PEAD
  (§2.2).

**(b) THE CASH ITSELF — already in the return series where a corporate-events file is supplied,
and NOT a separate opportunity.** The dividend payment. A fixture computing total return already
credits it; adding a "dividend yield" signal on top would double-count it.

**(c) THE EX-DAY PRICE-DROP LITERATURE — a genuine total-return effect, but a rounding error
here, and frequently misread as (b).** The ex-day finding is that the price falls by *less* than
the dividend, so the ex-day **total** return is positive. That is not neutralised by a total-return
series — it shows up as a real positive return. But size it: a US quarterly dividend is of order
50 bp of price, and the documented shortfall is a *fraction* of the dividend, so the effect is of
order **5–15 bp on one day**, against a 67.6 bp round trip plus 1.8 bp commission. It cannot pay
for itself, which is why the practitioner literature on "dividend capture" converges on the
conclusion that *"only sufficiently high dividend yields can overcome transaction costs"*
[practitioner/summariser sources only — see §9.6]. **And it is not this territory:** ex-day is a
payment event, not a declaration event, and this lane is about declaration dates.

**(d) A MECHANICAL ARTEFACT THAT IS NEITHER — the ≥25% special ex-date rule (§3.2).** Not an
effect at all; a date convention that will manufacture a spurious one if the fixture gets it wrong.

**The clean statement: everything worth trading in this territory is in bucket (a), it is all
concentrated in one to three days around a declaration, and the modern medians in bucket (a) are
+23 bp for increases and −149 bp for cuts.**

---

## 7. MY OWN MEASUREMENTS — method, and every control

### 7.1 Sources and the negative control on each

| endpoint | what I took | negative control | result |
|---|---|---|---|
| `efts.sec.gov/LATEST/search-index` | 4,521 dividend 8-K filings, 2010–2025 | four nonsense phrases (`"zqxjkv dividend"`, `"quarterly flurb dividend"`, `"wumpus cash dividend"`, `"initial quarterly zqxjkv dividend"`) queried in the same loop, all 16 years | **0 hits, all four, all years.** The endpoint discriminates. |
| `query1.finance.yahoo.com/v8/finance/chart` | as-traded close + volume | two nonsense tickers | **HTTP 404 both** — no silent substitution of another company's data |
| same | " | `META` priced at 2010-06-01, before its 2012-05-18 IPO | **returns None**, does not fabricate a pre-listing price |
| `alphavantage.co` `DIVIDENDS` | schema + declaration-date coverage | nonsense symbol | **no discrimination possible** — the demo-key gate fires before the lookup, returning the same refusal for a real and a fake symbol. I therefore report Alpha Vantage's schema and IBM's coverage only, and claim nothing about breadth. |
| `data.sec.gov/submissions/` | 8-K item codes, SIC, entityType, exchanges | nonsense CIK `9999999999` | **HTTP 404** — no substitute filer returned |
| same | " | CIK `0000320193` must be Apple | returns tickers `['AAPL']`, exchanges `['Nasdaq']`, entityType `'operating'`, SIC 3571 |

**Positive controls, which matter as much as the negative ones here:** the cut series reproduces
the COVID suspension wave month-by-month and the special series reproduces the 2012 fiscal-cliff
wave month-by-month (§7.2). A harvest with only negative controls proves it is not returning
garbage; it does not prove it can see the thing.

**Scripts, in the session scratchpad, in the order they run:** `fts.py` (EDGAR full-text-search
client) → `harvest.py` (the event harvest, writes `events.json`) → `spot.py` (precision check,
fetches and prints real filing text) → `prices2.py` (as-traded prices, split un-adjustment,
terciles, through-floor counts) → `subs.py` (item codes, entity type, exchanges via
`data.sec.gov`). `prices.py` is the superseded split-adjusted version, kept only because §7.3 is
about the difference between the two.

### 7.2 The event harvest, and its precision — I opened the filings

Union of 17 initiation phrasings, 19 cut phrasings and `"special cash dividend"`, forms=8-K,
per year 2010–2025 (656 queries), deduped to (CIK, filing date). **These are event-*filings*, not
distinct events**; a company can appear on several dates. Distinct-company recounts are what §1.4
and §2.3 report.

**I spot-checked precision by fetching and reading the actual filing text around the match** —
six per family, randomly drawn from 2014–2023:

- **Initiations: 6/6 genuine** (Taitron, Amkor, H&E Equipment, Bruker, Enviva, Constellation
  Brands). One caveat: Enviva's hit is a slide in a later investor deck restating a declaration
  made ten weeks earlier, so **the filing date is not always the declaration date**.
- **Cuts: 4/6 genuine** (Empire State Realty, GNC, Cohu, Abercrombie). **One outright false
  positive: Consolidated Communications 2016-10-07, where "Dividend Suspension Period" is a
  defined term in a credit agreement, not a cut.** One date artefact: PG&E's hit is an investor
  slide appendix. **Cut precision ≈ 67%, with contractual boilerplate as the false-positive class.**
- **Specials: 6/6 genuine** (Coca-Cola Consolidated, ProPhase, HFF, Symetra, Aware, Viad).

Combined with the recall failure in §5.3(1), **my counts are lower bounds with ~67–100% precision,
and I am reporting them as such.** They are corroborated in level by S&P's independent census and
in shape by two **positive** controls, which I checked at monthly resolution rather than trusting
the annual totals:

- **Cut filings, 2020, by month:** Jan 1, Feb 1, **Mar 15, Apr 21, May 42**, Jun 6, Jul 2, Aug 13,
  Oct 2, Nov 8, Dec 2. The method reproduces the COVID suspension wave with the right *shape* and
  the right *timing*, not merely the right annual count.
- **Special filings, 2012, by month:** flat at 8–26 through October, then **Nov 78, Dec 89** —
  **51% of the year in its last two months**, which is the fiscal-cliff dividend-tax window. An
  independent study counts 320 special announcements in Oct–Dec 2012; I count 190 in the same
  three months, consistent with partial recall.

A harvest that could see neither of these would not be worth reporting; one that sees both, with
zero hits on four nonsense controls, is measuring the thing it claims to measure — at a level I
still would not defend, for the recall reasons above.

### 7.3 The price measurement, and the defect I caught by looking

I took the last daily close **strictly before** each filing date, and the median dollar volume over
the 20 sessions ending there.

**Yahoo's `close` is split-adjusted, and I nearly reported it as the as-traded price.** Naming the
extremes caught it: NVIDIA's 2012 initiation read **$0.32** (its 2021 4:1 and 2024 10:1 splits
divide by 40) and CIM Commercial's specials read **$355,514** (reverse splits multiply). I
re-fetched every ticker with `&events=split` and un-adjusted:

> as_traded(t) = adjusted_close(t) × ∏ splitRatio for splits after t

Three controls on the fix, all passing: **NVDA 2012-11-09 → $12.68**; **AAPL 2013-06-03 →
$449.73** (pre-7:1); **CMCT 2014-03-11 → $9.67**. The §0 table is post-fix. Dollar volume is
invariant to the adjustment and was not touched.

**This matters beyond my own numbers.** The adjustment biases in *opposite directions for the two
legs*: initiators tend to split later (adjusted price too low), cutters tend to reverse-split later
(adjusted price too high). **A $5 floor applied to an adjusted price series would admit cheap
cutters it should exclude and exclude expensive initiators it should admit** — a survivorship-
flavoured selection effect running straight through the axis this lane was commissioned to test.

**Extremes, named** (as-traded): initiations top out at **BKNG $3,741 (2024-02-22)** — the Booking
Holdings initiation S&P's Q1-2024 release names by name — and bottom at **First BanCorp PR $0.40
(2010-07-07)**. Cuts top at **Marriott $146.69 (2021-05-10)** and bottom at **Bimini Capital $0.18**.
Specials top at **TransDigm $1,410** (its recurring specials) and bottom at **ProPhase $0.11**.

### 7.4 The earnings confound, measured — and it is the largest number in this brief

The brief was told to address the earnings confound explicitly. I measured it. For every harvested
event I pulled the filing's **8-K item codes** from `data.sec.gov/submissions/CIK##########.json`
(a different host from `efts`, which had by then rate-limit-banned me — §8.6). **Item 2.02 is
"Results of Operations and Financial Condition": the earnings release.**

| family | event filings | matched to an 8-K | **ALSO carries Item 2.02** | Item 7.01 | Item 8.01 |
|---|---|---|---|---|---|
| **INITIATIONS** | 951 | 760 | **62.2%** | 30.9% | 38.9% |
| **CUTS** | 544 | 441 | **59.2%** | 36.1% | 38.8% |
| **SPECIALS** | 3,026 | 2,613 | **44.9%** | 23.4% | 48.0% |

**For roughly six out of ten dividend initiations and dividend cuts, the dividend decision and the
quarterly earnings release are the same document, filed on the same timestamp.** At daily
resolution they are one event. No amount of care in the runner separates them, because there is
nothing to separate: the company published both numbers in one press release.

**And the contamination is getting worse.** Share carrying Item 2.02, by year:

| | 2010 | 2012 | 2014 | 2016 | 2018 | 2020 | 2022 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|---|
| **INITIATIONS** | 41% | 64% | 53% | 65% | 66% | 72% | 67% | **72%** | 65% |
| **CUTS** | 40% | 47% | 69% | 62% | 62% | 59% | 50% | **80%** | 68% |
| **SPECIALS** | 38% | 24% | 45% | 44% | 44% | 48% | 53% | **58%** | 46% |

This is the finding that should decide the lane, and it points straight at the exclusion list.
**Earnings announcement dates and PEAD are excluded ground for this programme.** Liu, Szewczyk and
Zantout (§2.2) already reported that the post-cut *drift* is the earnings drift. My measurement
says the *announcement* is, for the majority of events, literally the earnings announcement.
**A dividend-declaration study on this universe would be a PEAD study wearing a dividend costume
about 60% of the time, and neither the 40% nor the 60% is separable without an announcement-time
source this programme does not have.**

### 7.5 Are these exchange-listed operating companies? Mostly, and about 40% are gone

From the same submissions data (`entityType`, `sic`, `exchanges`). **Controls: a nonsense CIK
returns HTTP 404, not another filer; CIK 0000320193 returns tickers `['AAPL']`, exchanges
`['Nasdaq']`, entityType `'operating'`, SIC 3571.**

| family | companies | entityType "operating" | fund SIC (6722/6726/6770) | REIT (6798) | on a major exchange **today** | **no exchange registration today** |
|---|---|---|---|---|---|---|
| INITIATIONS | 623 | 100.0% | 0.0% | 3.9% | 61.3% | **37.4%** |
| CUTS | 289 | 100.0% | 0.0% | **13.8%** | 57.1% | **40.8%** |
| SPECIALS | 844 | 99.8% | 0.1% | 7.1% | 50.1% | **46.3%** |

Three things follow.

1. **Fund contamination is not the problem I feared** — essentially none of these filers are
   closed-end funds or trusts by SIC or entity type, because funds do not file 8-Ks. **But cuts
   are 3.5× more REIT-heavy than initiations (13.8% vs 3.9%)**, which is largely the 2020 wave and
   is a genuine sector concentration in the cut leg. BDCs remain unchecked — see §9.11.
2. **The `exchanges` field is *current*, so "no exchange registration today" is a proxy for dead or
   deregistered — and it lands at 37–46%.** That is an *independent* corroboration of my pricing
   attrition (43.5% of initiation and 51.7% of cut filings unpriced, §0). Two unrelated methods
   agree that **roughly four in ten of these companies are no longer listed**, and the rate is
   higher for cuts than for initiations, exactly as the survivorship argument in §0 requires.
3. **Only half to three-fifths are on a major exchange today**, so the through-floor counts in §0
   are, if anything, generous about the tradeable population rather than conservative.

---

## 8. BLOCKS, LOGGED BY TOOL AND RESPONSE

1. **`curl` (Bash) → `api.nasdaq.com/api/calendar/dividends`** — **empty response body, no headers,
   no HTTP error**, on all three probes (2015-06-15, 2026-03-16, and the impossible-date control
   1899-01-02). Silent refusal; the control was equally empty, so the endpoint gave me no
   discriminating signal and I used none of it.
2. **`curl` (Bash) → `stooq.com/q/d/l/`** — **HTTP 200 carrying a JavaScript SHA-256 proof-of-work
   interstitial** (*"This site requires JavaScript to verify your browser"*), byte-identical for a
   live ticker, a delisted ticker and a nonsense ticker. Not a host block: a bot-check that a
   non-browser client cannot pass. No data obtained; no negative control possible.
3. **`WebFetch` → `link.springer.com/article/10.1007/s12197-015-9317-7`** ("Ex-dividend day
   abnormal returns for special dividends") — **HTTP 303 to `idp.springer.com/authorize`**, an
   authentication IdP. Not followed. This is why §3.2 has no modern special ex-day magnitude.
4. **`WebFetch` → `polygon.io/docs/rest/stocks/dividends/dividends`** — **HTTP 301 to
   `massive.com/docs/...`, which then returned HTTP 404.** The vendor's own redirect is broken, so
   the `dividend_type` semantics in §5.1 rest on a search-result summary and a knowledge-base
   article, not the schema page.
5. **`WebFetch` → `efmaefm.org` (two conference PDFs)** — **"unable to verify the first
   certificate"**. **Worked around**: `curl -sL` fetched both at HTTP 200 and `pypdf` extracted
   them, so §2.3 and §4.2 are read in full despite the WebFetch failure.
6. **`urllib`/`curl` → `efts.sec.gov`** — **HTTP 403 Forbidden**, first when I ran two harvests
   concurrently at ~10 req/s, and then **persistently, including on a single request**, for the
   remainder of the session. Self-inflicted rate-limit ban, not a host block, and my own fault.
   **Worked around**: the item-code and entity measurements in §7.4–7.5 were taken from
   **`data.sec.gov/submissions/`** instead, a different host that was never rate-limited, using
   the CIKs and dates already harvested. Lesson for the next harvest: EDGAR's published limit is
   10 req/s **across all its hosts combined**, and two concurrent jobs at 6–8 workers each will
   exceed it.
7. **`curl` → `alphavantage.co` with the vendor's documented `demo` key** — returns data for IBM
   and an **identical refusal for every other symbol including the nonsense control**. Not a block
   so much as a gate; **I did not create an account to get past it** and the coverage claims in
   §5.2 are therefore one-ticker claims.

**Nothing I fetched contained text addressed to me or instructing me to take any action.** The one
thing worth flagging as a category: every vendor page I touched that sells dividend data
(dividend.com, fintel, TradersPost, PageCrawl, alphaarchitect's dividend-capture piece) is a
**[SALES INSTRUMENT]** and **none of them is cited above for a return**. I used exactly one
practitioner-adjacent claim, in §6(c), and labelled it.

---

## 9. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **I did not open Boehme and Sorescu (2002).** The "product of chance" finding, the
   equal-weighted-significant/value-weighted-insignificant contrast, and the 1964 breakpoint are
   from the SSRN and RePEc abstracts and from Chen et al.'s characterisation of it. The
   *replication* (Chen, Chou and Lee 2014) I verified verbatim at RePEc, which I fetched directly —
   but that too is an abstract, not the paper.
2. **I did not open Liu, Szewczyk and Zantout (2008).** This is the load-bearing negative in §2.2 —
   the claim that the post-cut drift is entirely PEAD — and I have it only from the Wiley abstract
   and search summaries. **If one paper in this brief should be obtained in full before anything is
   decided, it is this one**, because it is what converts the cut leg from "small but real" into
   "already on the exclusion list".
3. **I did not open Asem (2023).** The "61.4% of the incremental information accrues on the day
   after" figure for >100% increases reached me through a search-result summary only, and a
   summariser is weaker than a snippet. It is a *share*, with no level attached, and it is the
   single claim in this brief that would most change the disposition if true and material. §4.1
   says so in the same sentence as the number.
4. **Grullon, Michaely and Swaminathan's +1.34% / −3.71%** is summariser-only. I report it beside
   Amihud–Li's read-in-full table rather than instead of it.
5. **No modern magnitude for special-dividend ex-day behaviour.** Springer blocked the one paper
   that addresses it directly (§8.3). §3.2 therefore establishes the *rule* (FINRA 11140(b)(2),
   primary) but not the *return*.
6. **No cost-honest treatment of any dividend-announcement strategy exists that I could find.**
   Not one of the papers above nets out spread or commission. The §6(c) statement about dividend
   capture rests on practitioner summaries and one blocked-adjacent academic paper on ex-day
   spreads; I would not defend a number from it. **The absence is itself the finding: this is one
   of the oldest literatures in finance and it has never been asked to pay a spread.**
7. **The earnings-confound measurement (§7.4) is mine, and it measures the FILING, not the
   announcement.** Item 2.02 on the same 8-K is proof the two were published together; its
   *absence* is not proof they were not, because a company can file two separate 8-Ks on the same
   day, or issue earnings by press release on the day before. **So 62.2% / 59.2% is a LOWER BOUND
   on the joint-event share.** Separately, 20–24% of my harvested filings could not be matched to
   an 8-K in the submissions feed at all (`recent` holds only the last 1,000 filings, which
   truncates prolific filers) — those are missing, not zero, and I have not checked whether the
   truncation is correlated with anything. The one published estimate I found for comparison —
   48.2% of dividend announcements within 10 days of earnings, 1981–1984 — is **summariser-only
   and forty years stale**, and I did not manage to open Aharony and Swary (1980), the paper that
   originated the separation.
8. **My event counts are lower bounds with imperfect precision**, quantified in §7.2: cut recall is
   poor enough that I would not defend the level, only the *shape* (the 2020 spike) and the
   *ordering*. The counts I would defend are S&P's, because they are a census.
9. **My price distributions are survivorship-biased upward, more for cuts than for initiations**
   (48.3% vs 56.5% priced). I cannot bound the bias. The §0 conclusion "cuts are not a cheap-tail
   event" is the *optimistic* reading of my own data, and the honest version is: **cuts are less
   cheap than the premise assumed, by enough that per-share commission is not the binding
   constraint, but I cannot tell you the true median.**
10. **I could not measure Polygon's coverage** — history depth, delisted-name inclusion, or
    declaration-date completeness — because that requires an API key and I did not create an
    account. §5.1 reports its documented *schema* and nothing about its *data*.
11. **Sector mix: measured and discharged, with one residual.** §7.5 shows essentially zero
    closed-end-fund or trust contamination (funds do not file 8-Ks, so the harvest never had the
    problem I expected) but **13.8% of cut-announcing companies are REITs against 3.9% of
    initiators** — a real sector concentration in the cut leg that I have not decomposed by era,
    and which is probably mostly 2020. **BDCs I did not check**: they file 8-Ks, they pay large and
    often special dividends, and they would sit under SIC 6726 only sometimes. If specials are ever
    revisited, that is the first screen to build.
12. **I never established a modern, cost-honest, US announcement CAR for any of the three
    families.** Every magnitude in this brief is either pre-2000 (Amihud–Li, MTW, DeAngelo, Bulan)
    or pre-2015 (Cotter et al.), and none is net of anything. **The most recent US dividend
    announcement return I could put a number on ends in 2000.** For a fixture starting in 2010,
    that means the entire returns case here is out-of-sample by a decade at best, and the one
    directional fact I do have about the intervening period — Amihud and Li's trend, and my own
    initiation counts falling 74% from their 2013 peak — points the wrong way.
