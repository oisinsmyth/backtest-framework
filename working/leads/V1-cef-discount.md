# V1 — the closed-end fund discount: external evidence

*Compiled 2026-09-09. Research only: no backtest was written, no fixture bar was
scored, nothing outside this file was modified. The metadata, dividend sidecar and
price columns of `data/fixtures/etf_wide_daily_raw.*` were READ to answer §2, §7 and
§8 on the actual universe rather than on a guess; those reads are flagged inline.
Every numeric claim is tagged to a source in §10. Where I could not verify something I
say so in the line itself.*

---

## 1. Verdict

**The identification half of the lead is correct and larger than suspected. NAV turns
out to be reachable without payment. And the trade still does not survive contact with
the literature or with our own cost regime.** Three things, in order of how much they
should move the decision.

**(i) The fixture is one-third closed-end funds and its mortality is essentially all
CEFs.** 172 of the 551 symbols (31.2%) are closed-end vehicles, and **21 of the 22
delistings are CEFs** — fund mergers, term-fund maturities and family
consolidations, not company failure. Our 168 US-registered CEFs are roughly **46% of
the entire US listed CEF universe** (ICI counts 364 traditional exchange-listed CEFs
at 2025-12-31). No study here has known this. Any past work on this fixture that
treated all 551 names as ETFs, read delisting as distress, or computed returns from
`close` without the dividend sidecar, is measuring something other than what it thinks.
**This correction is free and should be made regardless of what happens to V1.**

**(ii) The blocker is softer than believed — NAV is free.** Nasdaq's Fund Network
disseminates CEF NAV under pseudo-tickers that Yahoo serves free and daily
(`GAB`→`XGABX`, `ADX`→`XADEX`, `PDI`→`XPDIX`; verified empirically, and the
GAB/XGABX pair reproduces a −3.2% discount on matched timestamps). Independently,
**SEC Form N-CEN Items D.10 and D.11 give market price per share AND net asset value
per share** for every closed-end registrant, annually, free, structured, with an
EDGAR acceptance timestamp that makes the as-of-knowledge date exact — the cleanest
look-ahead-free discount observation available anywhere, from September 2018. The
flagship academic result never used daily NAV either: it used **month-end NAV from
Bloomberg**. So "no NAV" is no longer the reason to stop.

**(iii) The reason to stop is the evidence itself.** The strongest published negative
is a direct test of this exact trade and it fails: **Flynn (2004), 462 CEFs,
Jan 1985 – May 2001, sorts funds into 20 discount/premium bins and runs the hedged
trade (long the fund, short its NAV). Across all 20 bins not one alpha is
significantly positive** — the single positive point estimate is α = 0.14 with
t = 0.29, in a bin holding under one-third of one percent of observations — and those
returns already account for bid-ask spreads. The loud positive (Patro, Piccotti & Wu
2017, 18.2%/yr, Sharpe 1.92) is **gross**, ends **December 2011**, requires each fund
to have **120 months of prior history**, and its entire cost treatment is one sentence
assuming 67.8 bp spreads and "three turns a year" — while the table for the headline
model reports turnover of **5.825×**, so its own cost estimate is computed on the
*other*, lower-turnover model. Meanwhile the statistical premise is contested at the
level that matters: **Durmaz et al. (2023) reject a unit root in the discount for only
12 of 31 US CEFs, and their median-unbiased persistence estimates run to α̂ = 1.001
with an infinite upper half-life bound for 13 of 31 funds** — fund-level discounts
drift around time-varying trends, they do not revert to a fixed mean.

**And our cost regime is the worst version of this.** Measured on our own cohort: CEF
median daily dollar volume **$1.24M — 17× thinner than the rest of the fixture** —
after the fixture's own $1M liquidity screen has already removed the thinnest CEFs;
median price **$11.80**, so IBKR's per-share commission alone is **4.2 bp/side**
against ~1 bp for the rest of the universe; 12 names below the $5 floor. **And the
$1.00 per-order minimum, not the per-share rate, is the dominant term for a small
book — it binds below ~200 shares, i.e. below ~$2,100 notional at this cohort's
price.** Pontiff (1996, *QJE*) used share price itself as the proxy for arbitrage cost
and found deviations from NAV are larger for lower-priced, smaller funds: **the
mispricing exists because it is expensive to trade, and we are the marginal trader it
is expensive for.**

One further point kills the lead's own framing. The appeal was "a SLOW, LARGE move
relative to the spread." **The flagship's holding-period table says otherwise:** the
long-short mean return is 1.5% at a 1-month hold and only 2.0% cumulative at 3 months,
and beyond 3 months it is not significantly different from zero. The premium's
half-life is 8.3 months but **the tradeable abnormal return is front-loaded into month
one**, so lengthening the hold does not amortise the round trip — it just stops
paying. That is the opposite of the property the lead was recruited for.

**Recommendation: V1 should not proceed as a discount-reversion trading study.** If
the principal wants it kept open, the only version I would defend is a **Stage-0
premise check** — §9 — which is cheap, uses free N-CEN data, and would settle it.
Closing the avenue is the principal's call, not mine.

---

## 2. Which of those symbols are CEFs

**Authority.** The Nasdaq Trader symbol directories publish an explicit **ETF flag**
(`Y`/`N`) per listed symbol alongside the exchange and the official security name —
`nasdaqlisted.txt` for Nasdaq issues, `otherlisted.txt` for NYSE / NYSE Arca / NYSE
American. This is the exchange's own classification, not a vendor's inference. It is
also **current-only**, which is precisely the survivorship problem — see §3.

The head of the fixture is 40 symbols. All 40 resolve: **21 CEFs, 19 ETFs.**

| Symbol | ETF flag | Official security name | Class |
|---|---|---|---|
| AAXJ | Y | iShares MSCI All Country Asia ex Japan ETF | ETF |
| ACWI | Y | iShares MSCI ACWI ETF | ETF |
| ACWX | Y | iShares MSCI ACWI ex U.S. ETF | ETF |
| **ADX** | **N** | Adams Diversified Equity Fund Inc. | **CEF** |
| **AFT** | *absent* | Apollo Senior Floating Rate Fund Inc. | **CEF, DEAD** |
| **AGD** | **N** | abrdn Global Dynamic Dividend Fund | **CEF** |
| AGG | Y | iShares Core U.S. Aggregate Bond ETF | ETF |
| AGZ | Y | iShares Agency Bond ETF | ETF |
| **AIF** | *absent* | Apollo Tactical Income Fund Inc. | **CEF, DEAD** |
| AIVL | Y | WisdomTree U.S. AI Enhanced Value Fund | ETF |
| AMLP | Y | Alerian MLP ETF | ETF |
| **AOD** | **N** | abrdn Total Dynamic Dividend Fund | **CEF** |
| **ARDC** | **N** | Ares Dynamic Credit Allocation Fund, Inc. | **CEF** |
| **ASA** | **N** | ASA Gold and Precious Metals Limited | **CEF** (note 2) |
| ASHR | Y | Xtrackers Harvest CSI 300 China A-Shares ETF | ETF |
| **AVK** | **N** | Advent Convertible and Income Fund | **CEF** |
| **AWF** | **N** | AllianceBernstein Global High Income Fund | **CEF** |
| **AWP** | **N** | abrdn Global Premier Properties Fund | **CEF** |
| BAB | Y | Invesco Taxable Municipal Bond ETF | ETF |
| BBH | Y | VanEck Biotech ETF | ETF |
| **BBN** | **N** | BlackRock Taxable Municipal Bond Trust | **CEF** |
| **BCX** | **N** | BlackRock Resources & Commodities Strategy Trust | **CEF** |
| **BDJ** | **N** | BlackRock Enhanced Equity Dividend Trust | **CEF** |
| BFOR | Y | Barron's 400 ETF | ETF |
| **BGB** | **N** | Blackstone Strategic Credit 2027 Term Fund | **CEF** |
| **BGR** | **N** | BlackRock Energy and Resources Trust | **CEF** |
| **BGT** | **N** | BlackRock Floating Rate Income Trust | **CEF** |
| **BGY** | **N** | BlackRock Enhanced International Dividend Trust | **CEF** |
| BIL | Y | SPDR Bloomberg 1-3 Month T-Bill ETF | ETF |
| **BIT** | **N** | BlackRock Multi-Sector Income Trust | **CEF** |
| BIV | Y | Vanguard Intermediate-Term Bond ETF | ETF |
| BKF | Y | iShares MSCI BIC ETF | ETF |
| BKLN | Y | Invesco Senior Loan ETF | ETF |
| **BKT** | **N** | BlackRock Income Trust Inc. | **CEF** |
| BLV | Y | Vanguard Long-Term Bond ETF | ETF |
| **BLW** | **N** | BlackRock Limited Duration Income Trust | **CEF** |
| BND | Y | Vanguard Total Bond Market ETF | ETF |
| BNDS | Y | Infrastructure Capital Bond Income ETF | ETF |
| BNDX | Y | Vanguard Total International Bond ETF | ETF |
| **BOE** | **N** | BlackRock Enhanced Global Dividend Trust | **CEF** |

**Note 1 — AFT and AIF are absent from the live exchange directory.** Both are CEFs;
both merged into MidCap Financial Investment Corp on **2024-07-22** (AFT holders
received 0.9547 MFIC shares, AIF 0.9441, plus $0.25/share cash from an Apollo
affiliate). The fixture carries both with that `delistingDate`. **The authoritative
free classifier cannot classify two of the first forty symbols, and both are CEFs.**
That is the survivorship problem in miniature on this exact universe, and it
generalises: the dead cohort is where the CEFs concentrate, which is exactly where a
current-only directory is blind.

**Note 2 — ASA is a closed-end fund but not a US-registered investment company.**
Bermuda-domiciled; it will not appear in the SEC CEF file or in N-CEN. The same holds
for the Sprott closed-end trusts in this fixture (`CEF`, `PHYS`, `PSLV`, `SPPP`) —
closed-end in economic structure, discount/premium and all, but outside the 1940-Act
filing perimeter. **Any SEC-derived list silently misses them.**

### The whole fixture, not just the head

Classifying all 551 symbols from official security names plus the fixture's own
distribution cadence (read from `etf_wide_daily_raw.meta.json`):

| | count | share |
|---|---|---|
| US-registered closed-end funds (1940 Act) | 168 | 30.5% |
| Closed-end trusts outside the 1940 Act (`CEF`, `PHYS`, `PSLV`, `SPPP`) | 4 | 0.7% |
| **Total closed-end** | **172** | **31.2%** |
| ETFs / ETNs / other | 379 | 68.8% |

For scale: ICI counts **364 traditional exchange-listed CEFs** in the whole US market
at 2025-12-31. **Our 168 registered CEFs are ~46% of that universe** — this is not a
fringe sub-sample, it is close to half the asset class.

**The mortality is almost purely closed-end.** Of the 22 delisted symbols, **21 are
CEFs**: `AFT AIF CEN DIAX FAM FEI FIF FPL GER HIE IVH JPI JPS JRO KMF MGU MUI MYD NDP
NID NTG`. The one non-CEF delisting, `ELON`, shows `max_gap_days: 2344` against 2353
bars over a 2010–2025 span — **that is a recycled ticker, not a continuous series, and
it should be looked at before it is used for anything.** The two "collapsed" names
(`UNG`, `VIXM`) are decay ETFs.

This matters beyond V1. The ICI reports the **number of listed CEFs has fallen 43%
since 2007**, and Lee-Shleifer-Thaler's original point was that price converges to NAV
at termination. **So this fixture's delisting cohort is not a distress cohort — it is
a convergence cohort, and how the fixture books terminal returns on those 21 names
determines the answer to any CEF study run on it.**

**Confidence.** The 40-symbol head table is exchange-authoritative except AFT/AIF (SEC
filings + merger release). The 551-symbol classification is **mine**. I did not
machine-join all 551 against the directory, because that means downloading and joining
a file and this was a research-only task. **The join is a ten-minute job and should be
done before any number is published off this classification** (recipe in §3). I expect
it to move the count by a handful, not by tens; the likeliest errors are
monthly-paying bond ETFs called CEFs or the reverse.

---

## 3. A free, dead-inclusive list of US CEFs

**Yes at ticker level from September 2018; only partially before that.** Three free
sources, none sufficient alone.

### (a) SEC Form N-CEN structured data — the best route

- **URL:** `https://www.sec.gov/data-research/sec-markets-data/form-n-cen-data-sets`;
  quarterly ZIPs named `[YEAR]q[QUARTER]_ncen.zip`.
- **Coverage:** every N-CEN and N-CEN/A filing on EDGAR **since September 2018**.
- **Why it identifies CEFs** — verified against the primary form
  (`https://www.sec.gov/files/formn-cen.pdf`, read directly). **Part D is
  "Additional Questions for Closed-End Management Investment Companies and Small
  Business Investment Companies"** — filing Part D *is* the closed-end flag. Item
  D.1.a requests, for common stock, "Title of class / **Exchange where listed** /
  **Ticker symbol**". Part E is the parallel ETF section (E.1.b "Ticker"), and Item
  C.3.a is a "Type of fund" checkbox for Exchange-Traded Fund. **N-CEN separates CEF
  from ETF and gives ticker and exchange, free and structured.**
- **Dead-inclusive? Yes, by stacking.** N-CEN is an annual report filed for each
  fiscal year a fund existed, and the filing stays on EDGAR forever. The union of
  2018Q4→present is every US-registered CEF that existed since ~FY2018 **including
  those since merged or liquidated**. Using only the latest quarter would be
  current-only and survivorship-biased.
- **Fields that matter for §4, §6 and §8:** **D.10 Market price per share at end of
  reporting period**, **D.11 Net asset value per share at end of reporting period**
  (both "with respect to common stock issued by the Registrant only") — i.e. **the
  discount, directly**; **D.8 management fee as a % of net assets** and **D.9 net
  annual operating expenses** — the expense ratio, free, per fund, per year, which is
  the exact input for the §6(a) reduction; and **D.2 rights offerings**, a yes/no plus
  per-offering detail, the free audit trail for §8.
- **Lag:** due **"not later than 75 days after the close of the fiscal year"**
  (verified in the form's instructions), and EDGAR stamps acceptance to the second.
- **Limitation:** starts 2018-09. **Eight of the fixture's sixteen years are not
  covered at ticker level.**

### (b) SEC Closed-End Fund Information file — longer history, no tickers

- `https://www.sec.gov/data-research/sec-markets-data/closed-end-fund-information`;
  annual files at
  `.../files/investment/data/other/closed-end-fund-information/closed-end-investment-company-[YEAR].csv`.
- **Annual snapshots 2012 through 2026**, refreshed around June.
- **Verified by fetching the 2026 CSV.** Header is exactly
  `File_No,CIK,Registrant_Name,Address_1,Address_2,City,State,Zip_Code,Filing Date,Filing Type`.
  ~1,100 rows. **No ticker column, no exchange column.**
- Definition: filed both **N-8A and N-2**, "active" status; the SEC says it includes
  CEFs "that have not yet begun selling shares to the public" and those "that have
  ceased operations but have not yet terminated their registration".
- **Dead-inclusive only by stacking 2012…2026. 2010 and 2011 are not covered at all.**
- **The real defect:** ~1,100 rows is far more than the ~364 *exchange-listed* CEFs,
  because it includes non-listed interval and tender-offer funds; and it
  simultaneously **excludes** foreign-domiciled listed CEFs (ASA) and non-1940-Act
  trusts (the four Sprott vehicles). It over-covers and under-covers at once, and
  without a ticker you must join on registrant name — the kind of fuzzy join that
  silently drops the renamed funds (abrdn/Aberdeen, Nuveen/NuShares,
  AllianceBernstein/AB) that are over-represented in the dead cohort.

### (c) Nasdaq Trader symbol directories — authoritative, current-only

- `nasdaqlisted.txt` and `otherlisted.txt`, pipe-delimited, with an explicit **ETF
  `Y`/`N`** flag; definitions at
  `https://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs`.
- The cleanest free classifier that exists — **but it is a snapshot of what is listed
  today.** AFT and AIF are simply absent. **Used alone it would classify 21 of the
  fixture's 22 dead names as "unknown" and therefore drop precisely the cohort that
  carries the survivorship information.** Say this out loud in any pre-registration.

### The recipe I would use

Union of (a) 2018Q4→present stacked, for tickers and the CEF/ETF split; plus (c) for
today's listings; plus (b) 2012→2017 joined on registrant name for the early years;
with the residue — 2010–2011, foreign-domiciled funds, non-1940-Act trusts —
**hand-classified and recorded as hand-classified.** **A 100%-machine,
2010-complete, dead-inclusive free list does not exist.** Anyone who says otherwise is
selling a database.

---

## 4. NAV: where, how often, at what lag

**The blocker is real but softer than assumed. Free daily NAV exists; free
look-ahead-proof NAV exists; they are not the same source.**

### (a) Free, daily, verified — Nasdaq Fund Network NAV pseudo-tickers

Funds submit NAV to Nasdaq's Fund Network (formerly MFQS); Nasdaq disseminates it, and
Yahoo's chart endpoint serves it free under a pseudo-ticker. **Verified empirically on
2026-09-09:**

| NAV symbol | fund | type | first trade |
|---|---|---|---|
| `XGABX` | The Gabelli Equity Trust | MUTUALFUND / NAS | ≈1999-04 |
| `XADEX` | Adams Diversified Equity Fund | MUTUALFUND / NAS | ≈1999-05 |
| `XPDIX` | PIMCO Dynamic Income Fund | MUTUALFUND / NAS | ≈2012-05 (matches PDI's IPO) |

Proof it is NAV and not price — identical timestamps, `XGABX` close
`[5.82, 5.87, 5.91, 5.91, 5.91]` against `GAB` close
`[5.62, 5.66, 5.69, 5.67, 5.68]` (NYSE, instrumentType EQUITY). 5.68/5.87 − 1 =
**−3.2%**, a plausible GAB discount.

**Five caveats, all material:**

1. **No as-of-knowledge date.** Yahoo stamps one timestamp per bar at 09:30 ET *of
   that day* — before the NAV was struck. There is no field saying when the value was
   written, so **silent restatement is undetectable.** CEFs reclassify
   return-of-capital routinely at year end; NAV restatements happen. **This is a
   backfilled history, not a vintage series.**
2. **The symbol mapping is not mechanical.** `XPDIX` = X+PDI+X works; `XADXX` 404s
   (ADX is `XADEX`). Nasdaq assigns these. **No free bulk mapping file was found** —
   per-fund lookup works (cefdata.com displays it), a universe file appears to need a
   signed Nasdaq NFN access agreement.
3. **Cent quantisation.** NAV is published to the cent — only 124 distinct closes in
   504 days for `XGABX`. On a ~$5.90 NAV that is **~17 bp of resolution floor on the
   discount**, and it **scales inversely with price** — the same axis that killed
   D284. Any discount edge smaller than a few times that, on low-priced names, is
   measuring rounding.
4. **Daily depth before ~2016 is unconfirmed** — `range=max&interval=1d` silently
   returns monthly bars.
5. **Undocumented, unsupported, ToS-restricted, can break without notice.** Nasdaq's
   own symbol-directory page states NFN data is *"for internal non-commercial usage
   only unless separately licensed from Nasdaq."*

### (b) Free, authoritative, look-ahead-proof — SEC Form N-CEN

**Items D.10 and D.11 give market price per share and NAV per share at fiscal year
end**, for closed-end registrants only. Annual. Due within **75 days**. EDGAR records
acceptance to the second, so the knowability date is exact. Structured data from
September 2018.

**This is one discount observation per fund per year, and it is the only source here
whose as-of date can be proven.** Too sparse to trade. **Exactly right for a Stage-0
premise check, and for validating (a).**

### (c) Free, authoritative, coarse — SEC Form N-PORT

- **The current regime is the pre-2024 one:** quarterly filing within 60 days of
  quarter end, only the third month of each quarter public. The 2024 amendments
  (monthly, public at 60 days) were **adopted but delayed to 2027-11-17 / 2028-05-18**,
  and a Feb/Mar 2026 proposal would scale them back further. *These timing facts rest
  on law-firm secondary sources plus direct measurement of real filings, not on a
  reading of the rule text — the SEC release PDFs would not convert.*
- **Measured lag** on Adams Diversified Equity Fund (CIK 0000002230): period
  2026-06-30 filed **29 days** later; 2025-12-31 → 56 days; 2025-09-30 → 52 days.
  **The lag is fund-specific and varies quarter to quarter. Use the EDGAR acceptance
  timestamp per filing, never a constant** — assuming a flat 60 days discards a month
  of real information for prompt filers and is outright look-ahead for slow ones. Key
  on the **original** filing, not later `NPORT-P/A` amendments.
- **N-PORT does not give NAV per share.** Verified in `primary_doc.xml`: it carries
  `totAssets`, `totLiabs`, `netAssets` — **and no shares-outstanding tag.** To get
  NAV/share you must divide by a point-in-time share count, and CEF share counts move
  continuously: the same ADX filing shows `mon1Flow reinvestment = $29,120,647` on a
  $3.29bn fund — **~0.9% of net assets issued in one month via DRIP.** Add rights
  offerings, ATM issuance and buybacks — **and buybacks are run precisely because the
  discount is wide, so the share-count error is correlated with the signal.** A 1%
  share-count error is **100 bp of fabricated discount** against a cross-sectional
  dispersion of a few hundred bp. This alone could generate a result.
- **The underrated free path:** each quarterly N-PORT carries
  `monthlyTotReturn rtn1/rtn2/rtn3` — **monthly NAV total returns**, at a 29–56 day
  lag, with an exact knowability timestamp, back to **2019Q4**. But it is a *total*
  return; recovering NAV *levels* means stripping 8–12%/yr distributions and chaining,
  and chained multiplicative errors over 27 quarters will not stay small.

### (d) Paid

**Almost nothing verified — the parallel strand exhausted its search budget before
reaching pricing, and I will not guess.** Nasdaq Data Link's NFN service exists and
carries daily CEF NAV [SALES INSTRUMENT] but its price, history depth and format are
unverified. CEFConnect (Nuveen) [SALES INSTRUMENT] refused connection twice — *logged
as a WebFetch `ECONNRESET`, which may be a user-agent exclusion rather than a block*.
CEFA displays NAV and 10Y discount history sourced from Lipper/Refinitiv but bars
redistribution. **Norgate covers CEFs including a delisted universe but NAV is not
mentioned anywhere in its data-content tables — prices yes, NAV no.** Bloomberg,
LSEG/Refinitiv, FactSet, Morningstar Direct and ICE were **not reached at all**. Do
not take a number from this section.

### (e) Would monthly or quarterly NAV suffice?

**For the signal, yes — the flagship used month-end NAV.** Patro, Piccotti & Wu build
the entire strategy on **end-of-month NAV from Bloomberg** matched to CRSP prices.
Monthly NAV is not a compromise for this signal; it is what the published result
actually used.

**For a free reconstruction, no — three things break.** (1) N-PORT gives `netAssets`,
not NAV/share, and the share-count denominator is both moving and
signal-correlated. (2) N-PORT structured data starts **2019Q4** — ~27 quarters, one
regime; that cannot separate a discount effect from 2020–2022 rate and credit beta.
(3) A 29–56 day stale NAV means you are ranking on `P_t / NAV_{t−k}`, which is
**contaminated by NAV momentum** — you are partly ranking on "NAV fell recently"
rather than "the discount is wide", and those have opposite expected signs in this
literature. **That is a confound, not noise, and a matched-count control will not
remove it; the control has to hold the NAV path over the staleness window.**

**What I would actually do:** build the daily panel from the NFN pseudo-tickers, then
**validate it against N-CEN D.10/D.11 and N-PORT `rtn1/rtn2/rtn3`** — for every
fund-year check that the Yahoo NAV path reproduces the filed NAV per share, and for
every fund-quarter that it reproduces the filed monthly returns. That is a real,
computable cross-check against an independent authoritative source with a provable
as-of date, and it is the only way to catch a backfilled or silently restated series.
**Exclude funds that disagree; do not treat disagreement as noise.**

### (f) One unverified caveat that would matter

CEFs are **not** subject to the daily forward-pricing requirement that binds
redeemable open-end funds, and commenters on the 2024 N-PORT release are reported as
saying some CEFs do not calculate NAV monthly or calculate it on a significant delay.
**I could not open the release to quote it (investor.gov returned 403).** If true, a
"daily" NAV panel may contain funds whose NAV is a stale carry-forward.

---

## 5. The anomaly as documented

| Source | Year | Sample | Magnitude | Cost treatment |
|---|---|---|---|---|
| Pontiff, *JFE* 37:341–370 [PEER-REVIEWED] | 1995 | US CEFs, **1965–1985** | Funds at a **20% discount** earn **+6%** over the next 12 months vs non-discounted; attributed to premium mean-reversion, **not** to portfolio performance | None I could verify |
| Pontiff, *QJE* 111(4):1135–1151 [PEER-REVIEWED] | 1996 | US CEFs | *A negative.* Mispricing is **larger** for funds hard to replicate, paying smaller dividends, with **lower market values**, and when rates are high; ~a quarter of cross-sectional mispricing variance | The paper *is* about arbitrage cost; **uses share price itself as the cost proxy** |
| Malkiel & Xu [PEER-REVIEWED] | — | **59 US equity CEFs, weekly, Jan 1993 – Dec 2002**, equal-weighted **index** | AR(1) φ = 0.98 (half-life ≈34 weeks); AR(2) R² = 96.3%; mean discount 8%; discount predicts fund returns R² = **2.45%** | **No strategy, no costs.** Aggregating 59 funds buys the power — see §6(b) |
| **Patro, Piccotti & Wu, *J. Financial Research* 40(2):223–248** [PEER-REVIEWED] | 2017 (WP 2014) | **377 US-traded CEFs, Aug 1984 – Dec 2011**; NAV **month-end, Bloomberg**; prices CRSP; foreign-incorporated excluded. OOS **Feb 1998 – Dec 2011**; **120 months** of history required first | Monthly-rebalanced equal-weighted quintiles on modelled expected return. Q5−Q1 **17.3%/yr** (BMR) / **18.2%/yr** (RADF), Sharpe 1.86 / 1.92, five-factor alpha **17.4%**. Domestic 16.1%, foreign 18.8% | **One sentence, and it is applied to the wrong model** — see below |
| **Flynn, Vassar Econ WP57** [WORKING PAPER] | 2004 | **462 CEFs (US + Canada), Jan 1985 – May 2001**, monthly, 20 bins of 5 pp from −50% to +50% | **The hedged discount trade: ZERO significantly positive alphas across all 20 bins.** Best point estimate α = 0.14, **t = 0.29**, in a bin with **<0.33% of observations** | **Returns already account for bid-ask spreads**; Flynn notes real investors face further trading and collateral costs |
| Bradley, Brav, Goldstein & Jiang, *JFE* 95(1):1–19 [PEER-REVIEWED] | 2010 | **142 CEFs, 127 open-ending attempts, 1989–2003** | Targets at ~**20%** discounts pre-attack; attempts **cut the discount by >10 pp**, to about half; **>8 pp** below matched non-attacked funds three years later | n/a — event study |
| Kohl, SSRN 2294410 [WORKING PAPER] | 2013 | **not verified** (SSRN 403) | ">10% annually" per abstract as reported by search | **not verified** |

### Reading the flagship honestly

Patro et al. is the strongest published positive and a real peer-reviewed result. Five
things in it cut against the lead, and I verified each in the paper's own text:

1. **The cost sentence is attached to the wrong model.** The text says: *"median CEF
   bid-ask spreads during the sample period to be 0.678%, which amounts to an
   annualized transaction cost of 2% (assuming the portfolio turns over 3 times during
   the year) for the BMR strategy… transaction costs cannot be a sufficient limit to
   arbitrage to explain our large returns."* But Table V Panel A (BMR, the 17.3% model)
   shows portfolio turnover **PTO = 2.939**, while **Panel B (RADF, the headline 18.2%
   model) shows PTO = 5.825.** At the headline model's own turnover the same
   arithmetic gives **~3.9%/yr, not 2%** — and there is no borrow cost, no impact, and
   no per-name spread anywhere in the paper.
2. **It ends in 2011.** Their sub-period test finds no significant decay (18.8% vs
   17.5%) — but that is decay *within* the pre-publication sample. The paper
   circulated from 2014 and published 2017. **I found no post-publication
   out-of-sample test in the peer-reviewed record.** The one period that matters for
   us — 2012 onward, 100% of our fixture — is untested.
3. **The 120-month entry requirement is a survivorship filter with teeth.** A fund
   must have ten years of premium history before it may be traded. Funds that launched
   and died inside ten years — a large part of how CEFs actually end (§2) — never
   enter at all.
4. **The short leg does far less than the prose says.** Text: *"the long and short
   positions contributing roughly symmetrically."* **Table V Panel A: Q5 = 0.153\*\*\*
   (t = 3.543), Q1 = −0.020 (t = −0.541), Q5−Q1 = 0.173.** The long leg is 15.3 of the
   17.3 points; the short leg is 2.0 and is not distinguishable from zero. Symmetry
   holds only in five-factor alpha space (Q5 α = +10.0%, Q1 α = −7.4%), where Q1's
   market beta of 0.431 is subtracted out. **A cash-neutral book with no factor hedge
   — what this programme would run — collects the 2 points, not the 7.4.**
5. **The signal is not slow, which was the lead's whole thesis.** Their holding-period
   table: the long-short mean return is **1.5% at a 1-month hold, 2.0% cumulative at 3
   months, and not significantly different from zero beyond 3 months.** The premium's
   half-life is 8.3 months, but the *tradeable abnormal return* is front-loaded into
   month one. **Lengthening the hold to amortise the round trip does not work here.**
   This is the house's own rule — cost-cutting is not edge-sharpening — arriving from
   the literature rather than from a runner.

Their liquidity defence is one sentence ("there would have been sufficient liquidity
for this trading strategy to have been a tradable one"), supported by mean CEF dollar
volume of ~$195M annualised — i.e. **~$0.8M per name per day** — at mean market cap
~$316M. That is a capacity statement, and it is small.

---

## 6. The strongest negatives

### (a) Expenses — theoretically strong, and it **fails to replicate in US data**

This is the reduction the lead expected to be decisive. It is not, and the honest
answer points the other way.

- **Berk & Stanton (2007), *JF* 62(2):529–556** — a *calibration*, not an estimate of
  a fraction explained (fee 1%/yr, payout 2%, T = 50yr, prior ability 3.4%). It
  produces discounts "within the range observed". **Critically, the authors list what
  it cannot do and the tradeable part is on the list:** it "cannot match the
  short-term reversals documented in the literature", cannot generate the fast
  post-IPO discount decline, and cannot produce within-sector discount co-movement.
  **Even taking the rational-fee story at face value, it rationalises the *level* and
  leaves the *mean-reversion signal* unexplained.**
- **Cherkes, Sagi & Stanton (2009), *RFS* 22(1):257–297** — **725 CEFs, 1986–2004**.
  Value = NAV + capitalised liquidity benefits − capitalised fees. Second-stage
  regression R² = **0.72**; expense ratio t = −4.39, trading cost t = −3.84, payout
  t = +3.01, leverage t = +2.56. Premium at IPO ≈ underwriting cost (~5.7%), decaying
  to a mean of about **−4%**. They also report evidence *against* sentiment (Michigan
  sentiment takes the wrong sign in every significant case).
- **Gemmill & Thomas (2002), *JF* 57:2571–2594** — **158 UK CEFs, 1991–1997**,
  value-weighted mean discount **7.32%**. Expense-ratio coefficient **+2.992
  (t = 2.98)**, but **+0.263 (t = 0.29), insignificant**, once the noise-risk beta is
  dropped — collinearity-sensitive by the authors' own account.
- **The US replication fails. Flynn (2012), 458 US CEFs, 224,112 weekly discount
  observations, cross-section Jan 1991 – Dec 2000:** expense ratio **+2.627 (t = 1.01)
  for stock funds, −0.085 (t = −1.31) for bond funds — both insignificant.**
  Replication risk also insignificant. Noise-trader risk *is* priced in both — the
  opposite of the UK result. Malkiel (1977) himself concluded expenses could not
  explain the discount.
- **Ross (2002), *EFM* 8(2) — could not verify.** The publisher has elided the
  abstract everywhere and no free full text was found; one search summary asserted the
  *opposite* of the conventional reading. **Do not cite a Ross number on this file's
  say-so.**

**Verdict on (a): as a reduction of the discount *level* it is respectable; as a
reduction of the *trade* it is weak twice over.** The fee–discount relation does not
replicate in US cross-sections, and the leading rational model concedes it cannot
generate the reversals the strategy monetises. **This is the one place the lead
expected a killer and did not get one — recorded as such.**

### (b) Statistical artefact — **this is the strongest reduction, and it is verified**

**Durmaz, Kim, Lee & Sun (2023), "Trend Breaks and the Persistence of Closed-End Fund
Discounts"** — **31 US CEFs (14 core stock, 6 corporate debt, 11 general bond),
monthly, Jan 1999 – Apr 2018:**

- Plain **ADF rejects the unit root for only 12 of 31 funds (38.7%)** at 5%; RALS
  variants reach 16–18.
- Allowing **level shifts alone gives negligible power gain** (10–11 rejections even
  at 10%). Only with **two endogenous trend breaks** do you reject broadly (29 of 31).
- **Median-unbiased persistence** (i.e. Kendall/Andrews-type bias correction applied):
  **α̂ from 0.857 to 1.001** — at or above unity for some funds. **Median half-life
  8.10 months, mean 13.70, and only 18 of 31 funds have finite confidence bands** —
  **the upper half-life bound is infinite for the other 13.**
- Conclusion: discounts are nonlinearly stationary around **time-varying trends**,
  with long-swing dynamics — **not mean reversion to a fixed level.**

**This is the direct hit on the premise.** A strategy that buys "the discount is wide
relative to its mean" assumes a fixed mean the fund-level data will not support, and
the bias correction moves *against* the strategy: persistence is **higher**, not lower,
than OLS says.

**The flagship quantifies the same bias against itself.** Patro et al. report: *"Under
the null hypothesis, the mean value of the estimated β is **−0.052**"* — a pure random
walk in a sample this size produces an apparent mean-reversion coefficient of −0.052
with no mean reversion present. Their observed full-sample mean is **−0.138**. So
**~38% of the raw measured mean reversion is small-sample bias**; the economically
meaningful figure is ≈ −0.086. To their credit they subtract it before converting to
half-lives. **The procedural implication for us: any AR(1)/ADF reversion statistic on
a bounded persistent series must carry its own null-distribution bias correction, or
it will report reversion that is not there** — the same failure mode as a sample p95
read without its bootstrap SE (D373).

**Reconciling the contrast with Malkiel & Xu** (φ = 0.98, ADF *does* reject): they
aggregate 59 funds equal-weighted into an index. **Aggregation kills idiosyncratic
noise and buys statistical power, so the *index* discount looks stationary while the
*fund-level* discount — the thing you actually trade — does not.** They do not raise
Stambaugh or small-sample bias at all (checked).

**Spurious regression.** Ferson, Sarkissian & Simin (2003), *JF* 58:1393–1414 — a
persistent regressor induces spurious-regression bias in predictive regressions even
when returns are barely autocorrelated, and **data mining interacts multiplicatively
with it because persistent series are more likely to be found significant.** A
regressor with φ ≈ 0.98–1.00 is exactly their warning case. **I found no paper applying
Stambaugh (1999) or Ferson et al. specifically to the CEF discount — that is an open
gap, and it is a null this house could build.**

**Stale NAV.** Choi, Kronlund & Oh, "Sitting Bucks: Stale Pricing in Fixed Income
Funds" (*JFE* 2022) — **secondary sources only, primary not opened, treat as
unverified**: corporate and municipal bond fund NAVs are described as extremely stale,
with mis-valuations persisting up to two weeks. The implication is mechanical:
`D_t = 1 − P_t/NAV_t` with a stale `NAV_t` makes the discount a lagged-price artefact
that "reverts" as NAV catches up — **reversion you cannot trade, because the NAV move
already happened.** Cherkes et al.'s universe is **332 munis of 725 funds (46%)**, so
this contaminates roughly half the asset class. **Split munis out or the study is
uninterpretable.**

**Bid-ask bounce:** the Roll (1984) mechanism should bite hard on a low-priced, thin
universe, but **no published CEF-specific study of bounce-induced negative
autocorrelation in the discount was found. Flagged as unverified hypothesis, not
evidence.**

### (c) Event concentration — events clearly matter; **no published decomposition exists**

- **Bradley, Brav, Goldstein & Jiang (2010), *JFE* 95(1):1–19** — 142 CEFs, **127
  open-ending attempts 1989–2003**. **The base rate swings enormously: 3–4% of funds
  attacked per year in the early 1990s, rising to ~30% in 1999 and 2002**, following
  the 1992 proxy reform that cut shareholder communication costs. Targets at ~20%
  discounts; attempts cut the discount **>10 pp**, to roughly half; **>8 pp** below
  matched non-attacked funds three years later. The authors state the activist effect
  is "above and beyond" documented mean reversion — **they do not claim reversion is
  only events, and they do not decompose a discount-trading strategy's P&L into event
  and non-event components. I found no paper that does.**
- **ICI, "Closed-End Fund Activism", Apr 2025** — **[ADVOCACY / TRADE-ASSOCIATION
  LOBBYING]**, explicitly hostile to activists ("exploitation", "short-term profit
  seekers"); counts only: **~three-quarters of CEFs trade at a discount in any given
  month** (Jan 1995 – Dec 2024); **the number of listed CEFs has fallen 43% since
  2007**; **Saba, Karpus and Bulldog together held shares in half the CEF market at
  2024-12-31**, with over 75% of CEFs targeted since 2000; **44 forced tender offers
  between 2015 and June 2023.**

**So: this is an event-driven strategy wearing a mean-reversion costume until proven
otherwise.** The house rule applies directly — **name the top trade.** If the top
trades are open-endings, tenders and liquidations, this is Bradley et al.'s strategy,
not Pontiff's, and the 43% universe shrinkage since 2007 means **the delisting
handling in our fixture determines the answer** (§2: 21 of 22 delistings are CEFs).

### (d) Shortability — the short leg is the weak half and the direct evidence is thin

- **Alexander & Peterson, US CEFs, 2010–2015** (RePEc indexes it as *J. Financial
  Markets* 33:124–142, ScienceDirect serves it under an *IRFA* PII — **I could not
  resolve the discrepancy**): short sales are **30.8% of a CEF's trading volume** on
  average (30.0% discount funds, 34.5% premium funds, 30.7% even for muni CEFs);
  greater short selling precedes significant premium declines over the next five days.
  **Read that carefully: 30.8% of *volume* is FINRA daily short-volume data, which
  includes market-maker intermediation. Short volume ≠ short interest ≠ borrow
  availability.**
- **I found no published figure for CEF short interest as a percentage of shares
  outstanding, for the fraction of CEFs on hard-to-borrow lists, or for the
  distribution of borrow fees. That is a real gap and neither I nor the parallel
  strand could close it.**
- **Lamont (Acadian, May 2024)** — **[ASSET-MANAGER COMMENTARY]**, though the author
  is the principal academic authority on short-sale constraints: CEFs are "hard to
  borrow" because institutions do not typically hold them as lenders — **the float is
  retail, and retail shares are less reliably lendable.** Concrete instance: DXYZ
  (Destiny Tech100) at a ~2,000% premium on 2024-04-08 (NAV $4.84, price $105) with
  **borrow cost above 100% annualised** in mid-April 2024. One case is not a
  distribution, but it is the right shape of warning: **the funds you most want to
  short are exactly the ones where borrow is dearest.**
- **Patro et al.'s own defence is an assertion, not a demonstration:** they argue short
  constraints "cannot explain the magnitude of inefficiency" because a long-only
  version (Q5−MRKT) still yields **9.8% (BMR) / 10.7% (RADF)** annually. That is a
  claim about the alpha's source, not evidence the short leg is implementable.

### (e) Post-publication decay — **no direct estimate exists**

**McLean & Pontiff (2016)** — 82 characteristics from 68 studies, 72 replicated,
1926–2011; in-sample long-short **42.8 bp/month**, ~10% out-of-sample decay
(insignificant), **~35% post-publication decay (significant)**. **The closed-end fund
discount is not among their 82 characteristics**, so there is **no** direct
post-publication decay measurement for this anomaly. The 35% generic haircut is a
benchmark, not a measurement. Applied naively to Patro et al.'s 17.4% alpha it gives
~11.3% — still large, and still gross, still pre-2012, still long-leg-dominated.

**Doukas & Milonas (2004), *EFM* 10(2):235–266** fail to find that sentiment measured
by the change in the CEF discount is a priced systematic risk — but that attacks the
discount-as-sentiment-proxy claim, **not** the reversion trade. Sample and universe
unverified. The **Chen-Kan-Miller vs Chopra-Lee-Shleifer-Thaler (1993, *JF* 48)**
exchange is verified to exist and to be a dispute over economic and statistical
significance on nearly identical data, but **the publisher elided the abstracts and
neither full text was obtained.**

---

## 7. Liquidity, capacity and cost

### Measured on our own cohort

172 classified CEFs vs 379 others, median over bars from 2023-01-01, read from
`etf_wide_daily_raw.csv.gz`:

| | CEF cohort (n=172) | rest of fixture (n=379) |
|---|---|---|
| median daily dollar volume | **$1,240,327** | $21,670,466 |
| q25 / q10 daily dollar volume | $781,122 / $415,482 | $3,680,054 / $770,271 |
| share trading under $1M/day | **34%** | — |
| median share price | **$11.80** | (whole-window mean price median: $49.82) |
| share under $10 | **35%** | — |
| share under $5 (below the programme's floor) | **12 names** | — |

**Our CEF cohort is the liquid top of the asset class, not a representative slice.**
The fixture's own `screen_rejections` show a **$1M median-dollar-volume floor** and a
$3.00 price floor applied at screen time, so the thinnest CEFs never entered.
**External estimates put the true universe median at ~$0.4–1.0M/day** (median CEF
market cap $142.1m across 340 listed funds; annual share turnover 63.8% per Patro et
al. and ~87% (range 50–116%) per Bradley et al. → ~$420k/day; mean ~$0.89M/day). **So
the real CEF universe is thinner still than the 17× gap above.**

External price evidence agrees with ours: across 340 US-listed CEFs the median share
price is **$10.56** and **64% sit below $15**; 8.5% are already below $5. *(Source is
a single screener snapshot, LLM-extracted — re-derive before relying on it; our own
$11.80 is the number to trust.)*

### The cost stack

**IBKR US stock commissions** (verified, `interactivebrokers.com/en/pricing/commissions-stocks.php`):
**Fixed = $0.005/share, minimum $1.00 per order, maximum 1% of trade value.** Tiered:
$0.0035/share at ≤300k shares/month, minimum $0.35/order, max 1%, **plus** exchange,
clearing and pass-through fees that Fixed absorbs.

| CEF price | commission, bp/side (per-share term) |
|---|---|
| $8.27 (our cohort q25) | **6.04** |
| $11.80 (our cohort median) | **4.24** |
| $16.26 (our cohort q75) | **3.08** |

Against ~1.0 bp/side for the non-CEF cohort, **the CEF book costs roughly 4× more in
commission per unit traded, purely because CEFs are cheap per share.**

**Two traps in that table.**

1. **The $1.00 per-order minimum is probably the dominant term, and it is not a
   per-share cost.** It binds below 200 shares — **below ~$2,100 notional at our
   cohort's median price.** An equal-weighted book with $1,000 positions pays
   **100 bp/side, not 4.2.** **If any runner models IBKR cost as `0.005 × shares`, it
   understates cost by up to 20× on small tickets.** This is a live modelling risk
   for this programme, not a hypothetical.
2. **The 1% maximum is not protection.** It binds only below $0.50/share — irrelevant
   under a $5 floor. Do not model it as a cap that helps.

**Spread.** The only academic measurement is Cherkes, Sagi & Stanton (**725 CEFs,
1986–2004, Roll estimator**): mean one-way trading cost **0.49%** (muni 0.40%, taxable
FI 0.54%, domestic equity 0.51%, foreign equity 0.68%) — i.e. **~98 bp round trip** —
with CEF trade frequency "comparable to that of mid and small capitalization stocks on
the NYSE". Patro et al.'s CRSP figure is a **median 0.678% quoted spread, 1984–2011**.
**Both are largely pre-decimalisation and Roll is notoriously unstable; neither is
usable as a modern assumption.** Counter-evidence exists in direction only (Neal &
Wheatley 1998; Clarke & Shastri) that CEF spreads and adverse-selection costs are
*lower* than matched controls, because there is little private information about a
portfolio of disclosed holdings — **but no basis-point figure could be extracted from
either.**

**Per this house's standard the spread must be measured on the names HELD, off the
OHLC** — D285 missed a guessed 15 bp/side bar by 0.65 and the held names measured
33.8. Note the modern replacement for Corwin-Schultz is **EDGE** (Ardia, Guidotti &
Kroencke, *JFE* 2024), which estimates the root-mean-square effective spread from OHLC
and needs only three observations. **On a universe this thin and this low-priced the
choice of estimator will matter**, and I would expect either to come back *worse* than
the guess, not better.

### Capacity

**Externally unresolved, and both relevant papers duck it.** Patro et al. offer one
unquantified sentence and **report no transaction costs and no net-of-cost return** at
5.825× turnover. Bradley et al. report mean CEF market cap $222m, median $101m,
turnover 50–116%/yr, **average trade size 1.0–1.8 thousand shares** — and no capacity
analysis. **No paper or practitioner document reached quantifies price impact or a
capital ceiling for CEF discount arbitrage.**

Order-of-magnitude bound, as something to test rather than to believe: at ~$420k/day
universe-median volume and 10% participation, a 20-name book absorbs ~$840k/day of
trading; at ~2.3× annual turnover that is **capacity in the low tens of millions** —
and worst in exactly the smallest, cheapest, thinnest funds where Pontiff says the
signal lives.

---

## 8. The distribution trap

**This is the sharpest finding in the file and it is live in the fixture right now.**

The fixture's price columns are `open,high,low,close,volume` and nothing else.
`adjustment_frame` records that columns 1–4 are **as-traded**, with splits applied from
inline coefficients; **there is no adjusted-close column and no dividend column in the
CSV.** Distributions live in a sidecar, `etf_wide_daily_raw_events.json` →
`dividends`, as `[timestamp, amount]` pairs in the same split-adjusted frame (D75).

Measured on that sidecar over 2010-01-04 → 2026-08-26:

| | median | q25 | q75 |
|---|---|---|---|
| **CEF cohort** distribution yield %/yr | **8.22** | 7.45 | 9.38 |
| non-CEF cohort distribution yield %/yr | 2.05 | 1.16 | 3.01 |

Top of the CEF distribution: EDF 12.4%, PDI 12.4%, NCZ 11.9%, PHK 11.7%, NCV 11.7%,
PTY 11.2%, GGN 11.0%, IFN 10.9%. **This triangulates well externally** — BlackRock
reports a median distribution rate of 8.5% [SALES INSTRUMENT], AICA 9.3%
weighted-average [SALES INSTRUMENT], a neutral screener 8.48% median. Four independent
sources land in 8.2–9.3%.

### (i) The level error

**A total-return calculation that reads `close` and ignores the sidecar understates the
CEF cohort's 16.6-year terminal wealth by a factor of 3.71 — 73% of it.** For the
non-CEF cohort the same error costs ~1.4×. **The error is 4× larger on CEFs**, and it
points the wrong way for a short book: a short-side study ignoring distributions sees
CEFs falling steadily and books that as edge, when it is the fund paying its holders.

### (ii) The event error, which is worse

The level error would partly wash out of a long/short book. **The ex-date jumps will
not.** At an 8.2% yield paid monthly, the unadjusted series carries **12 downward jumps
a year averaging −71 bp each**; a quarterly payer carries 4 jumps of **−212 bp**.
Against a programme whose per-trade edges are measured against a `2c` bar, **a spurious
−71 to −212 bp on a specific name on a specific day is 10–30× the signal.** And it does
not diversify — **CEF ex-dates cluster on shared calendar dates (mid-month and
month-end), so a long book eats a coordinated hit and a short book collects one.** A
momentum or reversal signal computed on unadjusted CEF closes is, on those days,
measuring the distribution calendar. It is also lag-audit-adjacent: **the ex-date drop
is known in advance from the declaration, so a signal that sees it is trading a
calendar, not a market.**

### (iii) Return of capital — the correctness trap proper

For a *cash* distribution the tax character should be irrelevant to price adjustment —
ROC, capital gains and ordinary income all leave the fund's assets identically. **The
failure mode is a vendor whose dividend feed is built from *taxable dividend* records
rather than *cash distribution* records**, silently dropping the ROC portion and
leaving a spurious downward drift equal to the ROC yield.

The magnitude is not small. The only hard ROC numbers found — CEF Advisors, Sept 2013,
601 CEFs, trailing 12 months, **[SALES INSTRUMENT]** — report **183 of 601 (30.4%)
paid ROC**, with average ROC as a share of distributions **15.08% for bond CEFs and
54.24% for equity CEFs**. Thirteen years old and promotional; treat the level as
indicative and the ordering (equity ≫ bond) as reliable. **For an equity CEF with 54%
ROC on an 8.5% distribution, a vendor that drops ROC leaves ~4.6%/yr of residual
drift — about −52% of price level over 16 years.**

**No vendor documents ROC handling. Not one.** Norgate comes closest (four adjustment
modes; "special distributions include **capital returns**, special dividends and
spin-off distributions"; **rights issues explicitly classified as capital
reconstructions**) and Sharadar SFP is the only one that **names CEFs and delisted
funds explicitly** — but neither mentions ROC. Polygon is **split-only, no dividend
adjustment at all — disqualified for this universe.** Stooq documents nothing, which is
itself the finding. CRSP (the academic benchmark) does handle it: "nonordinary
dividends include return of capital distributions", and rights carry distribution code
**6541** with a **price factor**.

**For our provider specifically: Alpha Vantage's `TIME_SERIES_DAILY_ADJUSTED` supplies
raw OHLCV plus split and dividend events, which is what the fixture uses. Whether its
`7. dividend amount` captures the full cash distribution or only the taxable portion —
and whether it books managed-distribution ROC at all — I could not verify, and it is
the thing I would check first.** The test is cheap and decisive: take an equity CEF
with known heavy ROC, pull its 19a-1 notice and year-end 1099 breakdown from the
sponsor, and check the sidecar amount on the ex-date equals the **full** cash
distribution.

### (iv) Rights offerings — already visible in our sidecar

The `splits` map contains **`AVK → [["2024-09-20", 1.027]]`**. A 1.027 factor is not a
split — **it is the shape of a rights-offering dilution adjustment.** Advent
Convertible and Income Fund is a CEF; CEFs do dilutive rights offerings routinely; the
provider has encoded one as a split coefficient. Three further entries look like
genuine reverse splits (`AGD` and `AOD` at 0.5 on 2014-01-21, `AWP` at 0.3333 on
2026-02-09) — plausible for CEFs, which reverse-split to keep the price off the floor.

**Why this bites harder for CEFs:** a CEF rights offering is typically priced at a
discount to *NAV*, so a fund trading at a discount that issues rights below NAV is
**directly dilutive to NAV per share** — the ex-rights price drop is a corporate
action, not a return. A vendor that applies no ex-rights price factor leaves a
spurious negative jump indistinguishable from a signal. **Rights offerings are not
mentioned in the documentation of Sharadar, EODHD, Tiingo, Alpha Vantage, Polygon,
Stooq or Yahoo.** The fixture's own metadata already warns that inline split
coefficients "cover only the window the series covers" and come from the daily payload
rather than the splits endpoint. **Form N-CEN Item D.2 is a free, per-fund, per-year
audit trail of rights offerings** and would let this be checked rather than assumed.

---

## 9. Does it transfer to OUR fixture

**Bluntly: the universe transfers, the premise does not, and the cost regime is worse
here than in any published version.**

**What transfers.** The fixture genuinely contains 172 closed-end vehicles — ~46% of
the entire US listed CEF universe — spanning 2010-01-04 to 2026-08-26 with dead names
included. That is a longer and far more recent window than the flagship's out-of-sample
period, on a comparable fund count (377 there, 168 US-registered here). **If a NAV
panel were built, this fixture would be a legitimate post-2011 out-of-sample test of
Patro et al., which does not exist in the literature.** That is genuinely attractive
and worth saying.

**What does not transfer.**

1. **The premise is contested at fund level.** Durmaz et al. reject a unit root for
   only 12 of 31 funds, with median-unbiased α̂ up to 1.001 and infinite upper
   half-life bounds for 13 of 31. **Any null here must be a near-unit-root, bounded,
   trend-breaking series — not a stationary AR(1) around a fixed mean. A rotation null
   on a series whose mean itself moves will be far too lenient.**
2. **The direct test of the trade failed.** Flynn's hedged version, 462 funds,
   1985–2001, 20 bins, zero significantly positive alphas, already net of spreads.
   Patro et al.'s version is gross, pre-2012, long-leg-dominated and traded at 5.825×
   turnover with no cost model. **The gap between those two is where the whole
   question lives.**
3. **Cost.** Median CEF price $11.80 → 4.2 bp/side in commission alone, ~4× the rest
   of the universe; **the $1.00 per-order minimum binds below ~$2,100 notional and can
   make that 100 bp/side on a small book**; plus a spread on names with $1.24M/day
   median volume, after a $1M screen has already removed the thinnest. 12 names fail
   the $5 floor and 35% sit under $10. **Per-share commissions on low-priced
   instruments is exactly what killed D284 — and Pontiff (1996) says that is
   *why* the discount survives.**
4. **The hold cannot be lengthened to pay for it.** The flagship's own holding-period
   table: 1.5% at 1 month, 2.0% cumulative at 3 months, insignificant beyond.
   **The lead's central appeal — a slow, large move relative to the spread — is not
   what the data show.**
5. **The short leg.** Raw contribution 2.0 of 17.3 points, indistinguishable from
   zero; the 7.4% short alpha exists only after factor adjustment; no published borrow
   fee or short-interest distribution for CEFs exists; the one concrete data point is
   >100% annualised on the most-overpriced fund. **This programme has been here before
   (N1: the short-side alpha lives in the borrow-expensive tail a retail book cannot
   reach).**
6. **Distributions.** 8.22%/yr median, absent from the price column, 3.71× on terminal
   wealth, and 12 spurious −71 bp ex-date jumps a year clustered on shared calendar
   dates. **This must be fixed before any CEF number is computed, not after.**
7. **~46% of the CEF universe is muni/fixed-income with documented stale NAV.**
   Reversion there may be a NAV-catch-up artefact you cannot trade. **Split munis out
   or the result is uninterpretable.**

### What to do regardless of V1

Record in the fixture metadata that **172 of the 551 symbols are closed-end vehicles
and 21 of the 22 delistings are CEF corporate actions.** It costs nothing and it
changes how every past and future study on this fixture should be read. Note also that
the fixture's own `universe_rule` says `assetType == 'Stock'` while the roster is a
third CEFs and two-thirds ETFs — **the metadata does not describe what is in the
file**, which is worth resolving on its own account. And look at `ELON`: 2,344-day
max gap on 2,353 bars is a recycled ticker, not a series.

### If V1 proceeds anyway — the Stage-0 premise check

Not a backtest. **Pull N-CEN Items D.10 and D.11 for the 168 US-registered CEFs,
2018→2026** — free, structured, dead-inclusive, with an EDGAR acceptance timestamp
that makes the as-of date provable — and answer three questions before designing
anything:

1. **Does the discount have shape?** Cross-sectional dispersion, persistence, and an
   ADF/AR(1) statistic **with its own null-distribution bias subtracted** (the null
   mean is ≈ −0.05, not 0). Measure the conditioner's persistence before conditioning
   on it.
2. **Is the reversion muni-driven?** Split munis and fixed-income out. If the effect
   lives there, suspect stale NAV before writing a mechanism.
3. **Name the top trades.** If the P&L concentrates in the 21 delisted names — the
   convergence-at-termination cohort — this is Bradley et al.'s event strategy, not
   Pontiff's reversion, and it should be dispositioned as such.

If the discount has no shape at annual frequency on our own names, nothing downstream
matters and the daily-NAV plumbing never needs building. **That is the cheapest
decisive test available, and it is the only version of V1 I would defend.**

---

## 10. Sources

**Primary data documentation**

- SEC, **Form N-CEN** — `https://www.sec.gov/files/formn-cen.pdf` [PRIMARY DATA DOC].
  Read directly; source for the 75-day deadline, Part D as the closed-end section,
  Item D.1 ticker/exchange, D.2 rights offerings, D.8 management fee, D.9 net annual
  operating expenses, **D.10 market price per share, D.11 net asset value per share**,
  and Part E as the ETF section.
- SEC, Form N-CEN Data Sets —
  `https://www.sec.gov/data-research/sec-markets-data/form-n-cen-data-sets`
  [PRIMARY DATA DOC]. Quarterly `[YEAR]q[Q]_ncen.zip`, from September 2018.
- SEC, Closed-End Fund Information —
  `https://www.sec.gov/data-research/sec-markets-data/closed-end-fund-information`,
  index `https://www.sec.gov/open/datasets-closed-end-investment_company.html`
  [PRIMARY DATA DOC]. Annual files 2012–2026; 2026 CSV fetched, header verified.
- SEC, Form N-PORT Data Sets —
  `https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets`
  [PRIMARY DATA DOC]; coverage from 2019Q4. Live filing used for the lag and field
  measurements: ADX CIK 0000002230,
  `https://www.sec.gov/Archives/edgar/data/2230/000110465926088189/primary_doc.xml`.
- Nasdaq Trader symbol directories —
  `https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt`,
  `.../otherlisted.txt`, definitions
  `https://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs` [PRIMARY DATA DOC].
  Source of the ETF `Y`/`N` flag in §2.
- Nasdaq Fund Network — `https://www.nasdaq.com/solutions/data/nasdaq-fund-network`,
  operational notice `https://www.nasdaqtrader.com/TraderNews.aspx?id=DTN2025-33`,
  access agreement
  `https://www.nasdaqtrader.com/content/administrationsupport/agreementsdata/nfn_fundlist_agreement.pdf`
  [PRIMARY DATA DOC]. NAV pseudo-tickers verified via
  `https://query1.finance.yahoo.com/v8/finance/chart/XGABX?range=2y&interval=1d`
  [UNVERIFIED as a supported interface — undocumented and ToS-restricted].
- Interactive Brokers US stock commissions —
  `https://www.interactivebrokers.com/en/pricing/commissions-stocks.php`
  [PRIMARY DATA DOC].
- MidCap Financial Investment Corp merger completion release
  [SALES INSTRUMENT — issuer press release; used only for the merger date and exchange
  ratios, corroborated by the Form 425 filings at
  `https://www.sec.gov/Archives/edgar/data/1502573/`].
- Investment Company Institute, 2026 Fact Book ch.2 —
  `https://icifactbook.org/pdf/2026-factbook-ch2.pdf`, and "A Guide to Closed-End
  Funds" `https://www.ici.org/cef/background/bro_g2_ce` [PRIMARY DATA DOC — industry
  body, but these are census counts].
- ICI, "Closed-End Fund Activism", Apr 2025 —
  `https://www.ici.org/files/2025/cef-activism.pdf`
  **[ADVOCACY / TRADE-ASSOCIATION LOBBYING]** — explicitly hostile to activists; counts
  taken, framing discarded.

**Academic**

- Flynn, S., "Arbitrage in Closed-end Funds: New Evidence", Vassar Econ WP57 (2004)
  [WORKING PAPER] —
  `https://www.vassar.edu/sites/default/files/2021-07/economics-VCEWP57.pdf`.
  **The strongest negative in this file.**
- Flynn, S., "Noise-trading, Costly Arbitrage, and Asset Prices: Evidence from US
  Closed-end Funds" (2012) [WORKING PAPER] —
  `https://www.vassar.edu/sites/default/files/2021-07/economics-VCEWP71.pdf`.
- Durmaz, Kim, Lee & Sun, "Trend Breaks and the Persistence of Closed-End Fund
  Discounts", Auburn Econ WP 2023-08 [WORKING PAPER] —
  `https://cla.auburn.edu/econwp/Archives/2023/2023-08.pdf`.
- Patro, D., Piccotti, L. R. & Wu, Y. (2017), "Exploiting Closed-End Fund Discounts: A
  Systematic Examination of Alphas", *Journal of Financial Research* 40(2):223–248
  [PEER-REVIEWED]. Working-paper full text read directly:
  `https://assets.super.so/e46b77e7-ee08-445e-b43f-4ffd88ae0a0e/files/064a578b-4119-4462-b8db-cf040f35580a.pdf`
  (Dec 2016) and
  `https://www.gc.cuny.edu/sites/default/files/2021-07/Exploiting-Closed-End-Fund-Discounts_CUNY-talk.pdf`
  (Oct 2014). **All quoted figures in §5 and §6(b) are from the Dec 2016 text, checked
  against its own tables.** SSRN landing page (abstract 2468061) returned 403.
- Pontiff, J. (1995), *JFE* 37(3):341–370 [PEER-REVIEWED] —
  `https://www.sciencedirect.com/science/article/abs/pii/0304405X9400800G`. **Abstract
  not directly retrievable**; the "20% discount → +6%" figure and the 1965–1985 sample
  come from secondary summaries and Patro et al.'s characterisation. [PARTIALLY
  UNVERIFIED]
- Pontiff, J. (1996), "Costly Arbitrage: Evidence from Closed-End Funds", *QJE*
  111(4):1135–1151 [PEER-REVIEWED] —
  `https://academic.oup.com/qje/article-abstract/111/4/1135/1932203`. Abstract only.
- Berk, J. & Stanton, R. (2007), *JF* 62(2):529–556 [PEER-REVIEWED] —
  `https://faculty.haas.berkeley.edu/stanton/pdf/closed.pdf`.
- Cherkes, M., Sagi, J. & Stanton, R. (2009), *RFS* 22(1):257–297 [PEER-REVIEWED] —
  `https://faculty.haas.berkeley.edu/stanton/pdf/CEF.pdf`.
- Gemmill, G. & Thomas, D. (2002), *JF* 57:2571–2594 [PEER-REVIEWED] — Warwick WP
  `https://warwick.ac.uk/fac/soc/wbs/subjects/finance/research/wpaperseries/wp02-13.pdf`.
- Bradley, Brav, Goldstein & Jiang (2010), *JFE* 95(1):1–19 [PEER-REVIEWED] —
  `https://finance.wharton.upenn.edu/~itayg/Files/cefactivism-published.pdf`.
- Malkiel, B. & Xu, Y., "The Persistence and Predictability of Closed-End Fund
  Discounts" [PEER-REVIEWED] — `https://personal.utdallas.edu/~yexiaoxu/CFDDP.pdf`.
- Ferson, Sarkissian & Simin (2003), "Spurious Regressions in Financial Economics",
  *JF* 58:1393–1414 [PEER-REVIEWED] — NBER w9143, `https://www.nber.org/papers/w9143`.
- McLean, R. D. & Pontiff, J. (2016) [PEER-REVIEWED] —
  `https://www.fmg.ac.uk/sites/default/files/2020-08/Jeffrey-Pontiff.pdf`.
- Ardia, Guidotti & Kroencke (2024), "EDGE", *JFE* [PEER-REVIEWED] —
  `https://www.sciencedirect.com/science/article/pii/S0304405X24001399`; reference
  implementation `https://github.com/eguidotti/bidask`.
- Alexander & Peterson, "Short selling and the pricing of closed-end funds", US CEFs
  2010–2015 [PEER-REVIEWED] —
  `https://www.sciencedirect.com/science/article/abs/pii/S1386418115301191`.
  **Journal of record is ambiguous** (RePEc: *J. Financial Markets* 33:124–142;
  ScienceDirect serves an *IRFA* PII) — unresolved.
- Neal & Wheatley (1998), *J. Financial Markets* 1(1):121–149 [PEER-REVIEWED] —
  abstract only. Clarke & Shastri (RQFA) — abstract only, paywalled.
- Choi, Kronlund & Oh, "Sitting Bucks: Stale Pricing in Fixed Income Funds", *JFE*
  2022 [PEER-REVIEWED] — **primary not opened; secondary summaries only. UNVERIFIED.**
- Kohl, N. (2013), SSRN 2294410 [WORKING PAPER] — 403; **not verified**, and no
  evidence it was published in a peer-reviewed journal in the thirteen years since.
- Doukas & Milonas (2004), *EFM* 10(2):235–266 [PEER-REVIEWED] — bibliographic only.
- Chen, Kan & Miller (1993) vs Chopra, Lee, Shleifer & Thaler (1993), *JF* 48
  [PEER-REVIEWED] — dispute verified to exist; **abstracts elided by the publisher,
  full texts not obtained.**
- Ross, S. (2002), *EFM* 8(2) [PEER-REVIEWED] — **abstract elided everywhere, no free
  full text. Do not cite a Ross number on this file's authority.**

**Commercial / promotional — cited as data, labelled as sales**

- BlackRock CEF Market Insights [SALES INSTRUMENT] · AICA Q4 2025 [SALES INSTRUMENT] ·
  CEF Advisors "How to Analyze Destructive Return of Capital for CEFs", Sept 2013
  [SALES INSTRUMENT] · Nuveen daily CEF pricing [SALES INSTRUMENT] · CEFConnect
  (Nuveen) [SALES INSTRUMENT — unreachable; **logged as a WebFetch `ECONNRESET`, which
  may be a user-agent exclusion rather than a host block**] · CEFA/Lipper
  [SALES INSTRUMENT] · CEFData/CEF Advisors [SALES INSTRUMENT] · Lamont, Acadian,
  May 2024 [ASSET-MANAGER COMMENTARY] · stockanalysis.com and dividendvision.com
  screener snapshots [UNVERIFIED — single-source, LLM-extracted tables].
- Vendor adjustment documentation: Polygon/Massive KB, Norgate FAQ, Sharadar SFP docs,
  EODHD, Tiingo, Alpha Vantage, Stooq, Yahoo help, `yfinance` issue #1749, CRSP
  calculation guides [PRIMARY DATA DOC where the vendor's own docs; see §8].

**Fixture (read, not modified)**

- `data/fixtures/etf_wide_daily_raw.meta.json` — 551 symbol records, status, cohort,
  `n_dividends`, `n_bars`, `universe_rule`, `adjustment_frame`, `screen_rejections`.
- `data/fixtures/etf_wide_daily_raw_events.json` — `dividends` and `splits` sidecars.
- `data/fixtures/etf_wide_daily_raw.csv.gz` — columns
  `timestamp,symbol,open,high,low,close,volume`; §7 volume/price medians and §8
  distribution yields.

**Safety note.** No page fetched by me or by the parallel strands contained text
addressed to an AI agent or instructions to act. Two pages encountered by a parallel
strand returned **CAPTCHA challenge pages**; they were not attempted. One proxy page
carried the boilerplate string *"This page maybe requiring CAPTCHA, please make sure
you are authorized to access this page"* — recorded here as data, not acted on.
