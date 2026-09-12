# G1 — Forced institutional flow: the fund as marginal SELLER

**External-evidence brief. Round 3, lane G1. Written 2026-09-09.**
Route **(a)** — somebody sells for a reason unrelated to price.

**Nothing here is a measurement on the programme's fixture.** I have no access to their data
and claim nothing about it. Every number below is somebody else's, on somebody else's sample,
and is tagged with how well I actually established it. Under R15 nothing here closes or admits
anything.

---

## 0. Verdict up front

**The daily/overnight version of this lane is dead twice over, and the two kills are
independent.**

1. **Cost.** The only cell in the literature that ever produced a tradeable forced-sale
   effect is *below-mean-NYSE-size stocks*, and its authors state its own breakeven
   transaction cost: **0.35% per side**. The programme's measured spread on names actually
   held is **33.8 bp/side**. That is **one basis point of margin, before commissions**, on a
   **1990–2010** sample — and in that paper's own **2001–2010** subperiod the monthly effect
   has already gone to **−0.08% (SE 0.23)**, i.e. zero. The fixture begins in 2010, *after*
   the decade in which the effect was last measurable.
2. **Observation count.** The variable cannot produce more than **four innovations a year**,
   and on free data only **27 of them exist in the entire fixture window**. After an
   autocorrelation haircut that is **~7 independent draws**. A rotation null over that object
   has **26 offsets**; its p95 cannot be resolved to within the programme's own 2-SE rule
   (D373). **The lane fails the null standard before any return is measured.** Full arithmetic
   in §5, which is the section I was asked to write and the one I would read first.

**One thread is not dead and I will not pretend it is.** A *quarterly-rebalanced, low-turnover*
version clears 33.8 bp/side comfortably on the numbers in one 2026 arXiv preprint. But that
is (i) a different product from the book the programme runs, (ii) unrefereed, single-author,
q-fin.GN, and (iii) still subject to §5's observation-count problem. See §1.4 and §6.

**The single most damaging finding is not about returns at all.** It is that the *forward*-
predictive half of this literature is not the forced-seller variable. See §1.2.

---

## 1. Coval–Stafford style fire sales, and what happened to them

### 1.1 The canonical result

**Coval & Stafford, "Asset Fire Sales (and Purchases) in Equity Markets", NBER w11357 (2005);
published *Journal of Financial Economics* 86(2), 2007.**
[PEER-REVIEWED] — **[abstract only]** (NBER landing page read; JFE full text behind
ScienceDirect, not opened).

Abstract, verbatim, from the NBER page: *"This paper examines asset fire sales, and
institutional price pressure more generally, in equity markets, using market prices of mutual
fund transactions caused by capital flows from **1980 to 2003**. Funds experiencing large
outflows (inflows) tend to decrease (increase) existing positions, which creates price pressure
in the securities held in common by these funds. Forced transactions represent a significant
cost of financial distress for mutual funds. We find that investors who trade against
constrained mutual funds earn highly significant returns for providing liquidity when few
others are willing or able. In addition, future flow-driven transactions are predictable,
creating an incentive to front-run the anticipated forced trades by funds experiencing extreme
capital flows."*

Note the sample: **1980–2003**. It ends seven years before the fixture starts. I did not open
the JFE version and therefore quote no magnitude from it.

Note also the framing the programme should hear: the authors describe the payoff as
**"returns for providing liquidity"**. That is, on its face, the same liquidity-compensation
trap `docs/future-strategies.md §0` describes — the paper's own account of its edge is that
you are the market maker. Route (a) was supposed to be the escape from that; Coval–Stafford
call the escape *by the name of the trap*.

### 1.2 Lou (2012) — read in full, and the most damaging single fact in this brief

**Dong Lou, "A Flow-Based Explanation for Return Predictability", *Review of Financial
Studies* 25(12), 2012.** [PEER-REVIEWED] — **[read in full]** (LSE-hosted July 2012 draft,
44pp, text extracted locally; WebFetch's PDF parser failed and I extracted with `pypdf`).

Construction, verbatim from the paper:

```
FIT_{j,t} = ( Σ_i shares_{i,j,t-1} · flow_{i,t} · PSF_{i,t-1} ) / ( Σ_i shares_{i,j,t-1} )
```

where `flow_{i,t}` is the dollar flow to fund *i* in quarter *t* scaled by lagged TNA, and
`PSF` is an estimated partial-scaling factor. **Data: CDA/Spectrum quarterly holdings
1980–2006, CRSP survivorship-bias-free mutual fund database for flows.** The denominator is
*shares held by mutual funds* — note there is **no price anywhere in the ratio**, which
matters for §1.3.

**The result that kills the naive reading of this lane:**

> "the difference in equal-weighted returns between the top and bottom deciles ranked by FIT
> is **5.19% (t = 7.77) in the ranking quarter**. While the return spread is **indistinguishable
> from zero in the following year**, it is **−7.20% (t = −2.70) in years two and three
> combined**."

Read that carefully. **Realised FIT — the actual forced-flow variable, the thing this lane is
about — has no forward return over the next year.** The 5.19% is *contemporaneous*: it is the
price impact happening while you would still be discovering it. The reversal does not arrive
until **years two and three**.

The forward-predictive variable in Lou is **E[FIT]** — flow-induced trading computed from
*predicted* flows, where the prediction comes from **lagged fund performance and lagged flows**
(Lou's own §4: "lagged four-factor fund alpha"). E[FIT] earns **+2.52% (t = 3.96) in the
quarter following formation** and **+5.28% (t = 2.63) over the following year**, reversing
**−5.67% (t = −2.17) in quarters six to twelve**.

And Lou is explicit about what E[FIT] *is*: "**E[FIT] accounts for about half of the price
momentum effect**", and after controlling for E[FIT] "the coefficient on lagged stock returns
drops by **25 to 50%**".

**So the tradeable half of the flagship flow paper is a momentum proxy — and momentum is on
this round's exclusion list.** The half that is genuinely about forced selling is
contemporaneous and non-tradeable. That is not a cost problem or a decay problem; it is a
statement that the lane's forward-looking content, as this literature actually measures it,
lives in a variable the programme has already excluded.

**Transaction costs in Lou: none.** The effective bid-ask spread appears only as a *right-hand-
side* explanatory variable for the degree of partial scaling (coefficient on the
flow × spread interaction: −13.99). No strategy is ever costed. **This paper is not
cost-honest and does not claim to be.**

### 1.3 Wardlaw (2020) — the flagship measure is mechanically contaminated

**Malcolm Wardlaw, "Measuring Mutual Fund Flow Pressure as Shock to Stock Returns", *Journal
of Finance* 75(6), 3221–3243, December 2020.** [PEER-REVIEWED] — **[abstract only, verbatim]**
(obtained from RePEc; the paper itself I could not open — see §7 log).

Abstract, verbatim:

> "A large and rapidly growing literature examines the impact of misvaluation on firm policies
> by using mutual fund outflow-induced price pressure to isolate nonfundamental price
> variation. I demonstrate that **the standard approach to computing outflow-induced price
> pressure produces a measure that is inadvertently a direct function of a stock's actual
> realized return during the outflow quarter**, raising doubts about its orthogonality to
> fundamentals. **After removing these direct measurements of return, outflows generate a
> fairly negligible quarterly decline in returns, with no subsequent reversal, and many
> established results in this literature no longer hold.** I provide suggestions for future
> analysis."

This is a *Journal of Finance* paper saying that a large literature's central variable
partially measures the outcome it predicts. It has ~75 citations (Semantic Scholar, read via
API). **I want to be precise about its scope, because I did not read it:** the target is
described as the standard *outflow-induced price pressure* measure (the Edmans–Goldstein–Jiang
"MFFlow" family, scaled by dollar volume, which puts price in the denominator). **Lou's FIT as
written above has no price in it** and is therefore not the literal target — though Lou states
in a footnote that he "also use[s] lagged shares outstanding and **total trading volume** as
the denominator, and obtain[s] similar return patterns", which is the contaminated scaling.
**I could not verify from the abstract alone exactly which constructions survive.** Treat
§1.3 as: *the programme must derive its own scaling from first principles and prove it contains
no realised return, and must not inherit a published measure on trust.*

Practical consequence: any implementation must scale by a **pre-period, price-free** quantity —
lagged shares held, or lagged shares outstanding — and must **prove** by construction that no
contemporaneous price enters. Scaling by lagged market equity or by lagged dollar volume puts a
price in the denominator; using a *lagged* price is the standard fix, but it is a fix that must
be argued, not assumed.

### 1.4 The post-2010 record — this is where the lane dies on cost

**Dyakov & Verbeek, "Front-running of mutual fund fire-sales", *Journal of Banking & Finance*
37(12), 4931–4942, 2013.** [PEER-REVIEWED] — **[read in full]** (chapter 2 of Dyakov's Erasmus
doctoral thesis, repub.eur.nl, text extracted locally; the JBF version is behind ScienceDirect
and I did not open it — the thesis chapter is the same work and I read that).

Construction: for each stock, sum mutual-fund holdings by funds *forecast* to have extreme
inflows minus those forecast to have extreme outflows, **scaled by average trading volume
months t−12 to t−6**; bottom decile = "expected fire-sales"; **equal-weighted, rebalanced
monthly**, 1990–2010. Flows forecast by monthly logistic regressions on lagged flows, returns
and log TNA, using **only coefficients estimated through month t** — genuinely out-of-sample.

**Five-factor alphas during the holding month (Table 2.6, % per month):**

| cell | alpha | SE |
|---|--:|--:|
| all stocks | **−0.22** | 0.17 |
| **below mean NYSE size** | **−0.50** | 0.18 |
| above mean NYSE size | **+0.86** | 0.28 |

The headline "0.5% per month" is a **short** of expected fire-sales, and it **only exists in
the below-mean-size half**. In the above-mean-size half the same short **loses 86 bp/month** —
because, in the authors' words, "reversals in those stocks start before the front-running
algorithm can detect the price pressures". **Across all stocks the effect is statistically
zero.**

**Their own cost arithmetic, verbatim:**

> "We have to keep in mind the reported alpha of 50 basis points does not take into account the
> impact of transaction costs. Our front-running strategy is characterized with **very high
> turnover — 71.78% per month**, which implies relatively low **break-even transaction costs of
> 0.35%**. Consequently, the trading strategy may only be implementable by sophisticated
> traders who can afford to trade at low cost."

**0.35% per side against the programme's measured 33.8 bp/side is 1 bp of margin** — before
IBKR per-share commissions, and in a cell defined as *below mean NYSE size*, i.e. exactly the
low-priced names where the programme's per-share cost in bp is largest. The paper's own
conclusion is that only a low-cost professional could run it.

**And the decay, which is the part that matters most (Table 2.8, below-mean-size, % per
month):**

| month rel. to holding | 1990–2000 | 2001–2010 |
|---|--:|--:|
| −1 | −1.34 (0.27) | −1.41 (0.27) |
| **holding month** | **−0.62 (0.24)** | **−0.08 (0.23)** |
| +1 | +0.48 (0.28) | +0.45 (0.24) |

**By 2001–2010 the tradeable month is zero.** The authors dissect it at daily frequency
(Table 2.9, CAAR %, below-mean-size):

| | days 1–5 | 1–10 | 1–15 | 1–20 |
|---|--:|--:|--:|--:|
| 1990–2000 | −0.24 (0.12) | −0.38 (0.16) | −0.85 (0.31) | −0.85 (0.54) |
| **2001–2010** | −0.37 (0.15) | **−0.55 (0.22)** | −0.36 (0.40) | **−0.21 (0.64)** |

Their reading: "after 2000, **reversals among the small stocks start much earlier — around 10
trading days**... At that point, the CAAR reaches its lowest cumulative value of −0.55% and
prices start to revert."

**Put that against the programme's currency.** The best available gross move in the last decade
before the fixture opens is **55 bp, cumulative, over 10 trading days, with SE 22 bp**, and it
is gone by day 20. A round trip at 33.8 bp/side is **67.6 bp**. **The gross is 12.6 bp short of
the round trip**, on the *pre-fixture* decade, in the *only* cell that ever worked, on the
*short* side, in *below-mean-size* names. There is no version of this arithmetic that clears.

**This is the kill.** It is in the programme's own units, it comes from a peer-reviewed paper I
read in full, and it is dated 2001–2010 — a window that *ends* where the fixture begins.

### 1.5 The premise itself is contested: the seller is forced in aggregate, discretionary in the cross-section

**Huang, Ringgenberg & Zhang, "The Information in Asset Fire Sales", *Management Science*
(2022/2023).** [PEER-REVIEWED] — **[abstract only]** (INFORMS page and SMU repository listing
read; the CEIBS working-paper PDF returned HTTP 404 — see §7).

The finding, as stated in the abstract: the authors separate fire-sale trades into **expected**
trades (the manager scales the portfolio down pro rata) and **discretionary** trades (the
manager chooses which names to dump). **Discretionary trades contain fundamental information;
expected trades do not. And other traders cannot tell them apart.**

This is a direct attack on route (a)'s premise *for this lane specifically*. The fund is forced
to sell *something* — that part is genuinely price-unrelated. But **which** names it sells is a
choice, and the choice is informed. A per-name pressure variable is, by construction, a
cross-sectional variable: it is built entirely out of the part that is discretionary. So the
liquidity provider is systematically buying a blend of (harmless forced supply) and (a good
manager's informed sale), **with no way to separate them** — which the authors offer as the
explanation for why fire-sale discounts are large and persistent rather than as an anomaly.

**I did not read this paper.** I am reporting its abstract, and I flag that the numbers are not
established here. But the structural point stands on the abstract alone and it should be
weighed before any code is written.

### 1.6 One post-2010, cost-touching, US-panel treatment — and its own author's disclaimer

**Ziyao Wang, "Residual Supply and the Price of Risk Absorption", arXiv:2605.30672, 29 May
2026, q-fin.GN / econ.GN.** [WORKING PAPER — **unrefereed preprint, single author, no
affiliation stated on the arXiv page**] — **[read in full via the arXiv HTML rendering,
targeted extraction]**.

This is the closest thing I found to what §2 asked for: **a broad US panel, 2003–2024, with
transaction costs touched**. Construction (quoted from the paper): `FIT_{i,t} = Σ_f w_{f,i,t-1}
Flow_{f,t} TNA_{f,t-1}`; `ForcedSale_{i,t} = −min{FIT_{i,t}/ME_{i,t-1}, 0}`; a decayed
cumulative inventory `AbsInv_{i,t} = ρ·AbsInv_{i,t-1} + ForcedSale_{i,t}`, ρ = 0.85. Data: CRSP
mutual fund database + CRSP stocks; **"cleanest from January 2003 onward"** through November
2024. **1,022,728 stock-months, 10,338 stocks; no-microcap subsample 490,162 stock-months,
5,559 stocks.**

Forward returns to forced-sale pressure (no-microcap sample): **1m 65 bp (t = 3.32), 3m 160 bp
(t = 3.97), 6m 217 bp (t = 3.54), 12m 342 bp (t = 3.07).** Sign is **positive** — you *buy* the
fire-sold names.

**Against 67.6 bp round trip:** the **1-month horizon fails** (65 bp gross, 2.6 bp short). The
**3-month horizon clears by 2.4×**. The 6- and 12-month horizons clear comfortably.

**Cost treatment:** Appendix Table 26 only — an equal-weighted long-short portfolio with
**one-way turnover 17.2% per month** and gross **47.9 bp/month**, haircut at assumed one-way
costs of 25 / 50 / 100 bp to **44.0 / 39.7 / 31.1 bp/month**. That is turnover × one-way cost
applied once; charging both legs doubles it. At the programme's 33.8 bp/side the haircut is
**5.8 bp/month** (one leg) or **11.6** (both), leaving **~36–42 bp/month net** on the L/S. So on
this paper's own numbers the *low-turnover, monthly-rebalanced* construction **does** survive
33.8 bp/side.

**The author's own disclaimer, quoted:** the result is "**a way to locate the premium rather
than as a scalable arbitrage**". And the paper states the premium is largest "where absorption
capacity contracts, particularly affecting stocks with **narrow investor participation and
limited liquidity**" — i.e. precisely where a 33.8 bp/side average understates the true cost,
and precisely the tail the programme's $5 floor and dollar-volume screen are there to police.

**On Wardlaw:** the paper does address it — lagged (predetermined) weights, a robustness run
using holdings "at least 45 days old" (returns 50–321 bp across horizons), residualising
pressure on past returns, and pretrend controls. **Note however that its scaling is by
`ME_{i,t-1}` — lagged market equity — which puts a price in the denominator.** Lagged is the
standard fix and is probably fine; but by §1.3's rule the programme should re-derive it rather
than inherit it.

**Weight this source accordingly.** It is an unrefereed 2026 arXiv preprint in q-fin.GN by a
single author with no stated affiliation. It has not been through referees who would have
pressed on Wardlaw, on the microcap exclusion, or on the 45-day-holdings robustness. **It is
the one piece of evidence that keeps a quarterly version of this lane alive, and it is the
weakest-provenance source in this brief.** That combination should make the programme
suspicious, not encouraged.

### 1.7 Adjacent negative, for calibration

**Choi, Hoseinzade, Shin & Tehranian, "Corporate bond mutual funds and asset fire sales",
*Journal of Financial Economics* 138(2), 2020.** [PEER-REVIEWED] — **[snippet only]**
(ScienceDirect abstract page surfaced in search; not opened). Reported finding per snippet:
little evidence that bond fund redemptions drive fire-sale price pressure once time-varying
issuer-level information is controlled. **Different asset class, cited only as evidence that
the fire-sale result is fragile to controls, not as evidence about equities.**

---

## 2. Flow-induced pressure net of transaction costs on a broad US panel

**Direct answer: almost nobody has done it, and the two who touched it both landed at or below
the programme's spread.**

| source | US panel | costs subtracted? | outcome in programme's units (33.8 bp/side) |
|---|---|---|---|
| Coval–Stafford 2007 | 1980–2003 | **no** | n/a — sample predates fixture by 7 years |
| Lou 2012 [read in full] | 1980–2006 | **no** — spread is an RHS control only | n/a — forward-predictive part is a momentum proxy |
| Dyakov–Verbeek 2013 [read in full] | 1990–2010 | **breakeven stated, not subtracted** | breakeven **0.35%/side** vs 33.8 bp → **1 bp margin**; 2001–2010 gross **55 bp/10d** vs **67.6 bp** round trip → **fails** |
| Wardlaw 2020 [abstract only] | — | n/a | says the measure itself is contaminated |
| Huang–Ringgenberg–Zhang [abstract only] | — | n/a | says the cross-sectional part is informed |
| Wang 2026 arXiv [read in full, **unrefereed**] | 2003–2024 | **yes, crudely** (25/50/100 bp appendix) | 1m **fails**; 3m clears **2.4×**; L/S nets ~36–42 bp/month |

**The pattern is not subtle.** Every treatment that costs the strategy honestly finds it at or
under the wire, and the one that clears does so **only at horizons of three months and longer**
— which is to say, only by abandoning the daily book entirely and becoming a quarterly tilt.
That is route (b) smuggled into a route (a) lane: it works *because* the move is slow relative
to the spread, not because the seller is forced.

---

## 3. ETF ownership share and creation/redemption as a distinct channel

**Direct answer: there is a published result, it is at the ETF level not the stock level, and
at the stock level in a universe resembling the programme's it is a published NEGATIVE.**

### 3.1 The channel does transmit — but the magnitudes are an order below the spread

**Ben-David, Franzoni & Moussawi, "Do ETFs Increase Volatility?", *Journal of Finance* 73(6),
2018.** [PEER-REVIEWED] — **[read in full]** (Jacobs Levy Center working-paper PDF, extracted
locally). Sample **2000–2012**, day-stock and month-stock panels. Average ETF ownership per
stock rose **0.3% (2000) → 3.8% (2012)**.

Their Table 6 reversal tests, in their own worked magnitudes:

- **ETF flow channel, S&P 500, mean ETF ownership:** a **1-SD increase in ETF flows** is
  associated with next-**20-day** returns of **−0.156%**.
- **ETF mispricing channel, S&P 500, mean ETF ownership:** a **1-SD increase in mispricing** is
  associated with **−0.344% over the next trading month**.

**In the programme's units:** a round trip is 67.6 bp.
- Flow channel: **67.6 / 15.6 = 4.3 standard deviations** of ETF flow required merely to
  break even.
- Mispricing channel: **67.6 / 34.4 = 2.0 standard deviations** required merely to break even.

Neither is a strategy. Both are a *measurement of a real effect that is smaller than the toll*.

### 3.2 And in the universe that actually resembles the programme's, it is zero or wrong-signed

BFM report the **Russell 3000** cells alongside, and they are damning for this lane:

- Mispricing channel, Russell 3000: "the main effect of mispricing is **not significant**, while
  the sign on the interaction between ownership and mispricing is **actually negative**".
- Month-long reversal, Russell 3000: "the effect is **close to zero and is statistically
  insignificant**".
- Flow channel first-day impact, Russell 3000: "**contrary to our expectation, is negative**" —
  the **wrong sign**.

The authors' own summary: "the effect is stronger for S&P 500 stocks than for Russell 3000
stocks". The programme's universe — floored at $5 with a dollar-volume screen, 35.7% dead — is
**broader and smaller-cap than the Russell 3000**, i.e. further into the cell where BFM find
nothing.

**This is a published negative, in a top-three journal, on the exact axis §3 asked about.**

### 3.3 The ETF-flow return result is real but lives in the wrong instrument

**Brown, Davies & Ringgenberg, "ETF Arbitrage, Non-Fundamental Demand, and Return
Predictability", *Review of Finance* 25(4), 937–972, 2021.** [PEER-REVIEWED] — **[read in
full]** (ungated author-hosted PDF, extracted locally). Sample **2007–2016**.

Headline: long-short on ETF flows earns **1.1–2.0%/month** at the 1-month horizon,
**2.3–2.7%/quarter** at 3 months, **3.6–3.9%/half-year** at 6 months. Panel regression: decile-10
minus decile-1 ETFs, **−186 bp/month raw**, **−79 bp/month abnormal**, both p < 0.01.

**Three reasons this does not transfer to a single-name book:**

1. **The portfolio is composed of ETFs, not stocks.** You are long and short *funds*.
2. **The one-month result is driven by leveraged ETFs.** Their own decomposition: mature
   *leveraged* ETFs give **4.4–4.5%/month**; mature *unleveraged* ETFs "**do not exhibit
   predictability at a one-month horizon**" at all, and only reach 1.2%/quarter at 3 months and
   1.2–2.0% at 6 months. The headline is a leveraged-ETF phenomenon.
3. **The stock-level extension is one sentence in an Internet Appendix.** Footnote 32, verbatim
   and in full: *"Moreover, Internet Appendix Section 6 shows that our results extend to the
   individual stock level."* No magnitude, no horizon, nothing in the main text. **I could not
   verify that claim** — see §8.

**Transaction costs in BDR: none.** The only occurrence of "trading costs" in the body is the
observation that ETFs are cheaper to trade than baskets.

### 3.4 High ETF ownership makes a name MORE expensive, not less

**Israeli, Lee & Sridharan, "Is there a Dark Side to Exchange Traded Funds? An Information
Perspective", *Review of Accounting Studies* 22(3), 2017.** [PEER-REVIEWED] — **[read in
full]** (Wharton-hosted Sept 2016 draft, extracted locally). Sample **2000–2014**, firm-year
panel.

Their abstract: an increase in ETF ownership is associated with **"(1) higher trading costs
(bid-ask spreads and market liquidity); (2) an increase in stock return synchronicity; (3) a
decline in future earnings response coefficients; and (4) a decline in the number of analysts
covering the firm."**

Magnitude: **a one-SD increase in ETF ownership → a 1.7% increase in average daily bid-ask
spreads over the next year.** Note that their spread proxy is **HLSPREAD following Corwin &
Schultz (2012)** — *the same estimator the programme uses for its 33.8 bp*. So this is directly
commensurable: conditioning a book on high ETF ownership selects names whose Corwin-Schultz
spread is systematically wider.

**No return-predictability result is reported anywhere in this paper.** It is a cost-and-
information paper. Cited here as evidence that the ETF-ownership tilt moves the programme's
cost term in the **wrong direction**.

### 3.5 What ETF material is NOT evidence

I found practitioner/vendor pages on ETF-flow signals (QuantPedia and similar) while searching.
**[PRACTITIONER] / [SALES INSTRUMENT] — cited for nothing.** Per the standing rule, vendor
material is never evidence for a return. It is not even useful here as crowding evidence,
because the crowding question in this lane is about *institutional* flow data, not retail
signal blogs.

---

## 4. THE DATA QUESTION — verified against SEC primary documentation

This section is the one I would act on regardless of what happens to the signal, because two of
its findings are defects that will bite any lane touching EDGAR, not just this one.

### 4.1 Form N-PORT — cadence, lag, coverage, verified

**[PRIMARY DATA DOC] — SEC "Form N-PORT Data Sets" landing page — [read in full].**
**[PRIMARY DATA DOC] — `sec.gov/files/nport_readme.pdf`, 30pp — [read in full]** (extracted
locally with `pypdf` after WebFetch's parser failed).

Verbatim from the readme:

> "Form N-PORT is used by registered investment companies and exchange-traded funds to report
> monthly portfolio holdings other than money market funds. **Form N-PORT filings are
> disseminated quarterly.** ... **The N-PORT data sets consists of XML data submitted from
> October 2019 through current period.** ... The data will be published quarterly."

**Coverage start: October 2019.** Free, structured, tab-delimited, 30 tables.

**The tables that matter, with exact field names, from the readme:**

| table | fields | form item |
|---|---|---|
| `SUBMISSION` | `ACCESSION_NUMBER`, **`FILING_DATE`**, `SUB_TYPE`, `REPORT_DATE`, `IS_LAST_FILING` | A.3–4 |
| `FUND_REPORTED_INFO` | `SERIES_ID`, `SERIES_LEI`, **`NET_ASSETS`** (B.1.c), **`SALES_FLOW_MON1/2/3`** (B.6.a), **`REINVESTMENT_FLOW_MON1/2/3`** (B.6.b), **`REDEMPTION_FLOW_MON1/2/3`** (B.6.c) | A.2, B.1–B.6 |
| `MONTHLY_TOTAL_RETURN` | **`MONTHLY_TOTAL_RETURN1/2/3`**, `CLASS_ID` | B.5.a–b |
| `FUND_REPORTED_HOLDING` | `ISSUER_NAME`, `ISSUER_LEI`, `ISSUER_TITLE`, **`ISSUER_CUSIP`**, `BALANCE`, `UNIT`, `CURRENCY_VALUE`, **`PERCENTAGE`**, `PAYOFF_PROFILE`, `ASSET_CAT`, `ISSUER_TYPE` | C.1–C.8 |
| `IDENTIFIERS` | `IDENTIFIER_ISIN`, **`IDENTIFIER_TICKER`**, `OTHER_IDENTIFIER` | C.1.e |

**This is genuinely good news and it is the strongest positive finding in this brief.**
Item **B.6** gives, per fund series, **monthly** dollar sales, reinvestment and redemptions —
which is a *directly reported* fund flow, not one you have to back out from TNA and returns.
Item **B.5** gives monthly total returns. Item **B.1.c** gives net assets. **Per-fund monthly
flows are free.** No CRSP subscription is required for the flow half of FIT after October 2019.

**But the cadence kills the timing.** Holdings are a **quarterly** snapshot; the flows are
monthly but **batched into a quarterly filing disseminated ~60 days after quarter end**. So for
a quarter ending 31 March, filed by ~30 May: **January's flow is public 149 days after the
month it describes**, February's ~118 days, March's ~60 days. The `FILING_DATE` field is the
honest knowledge date and must be used as such.

### 4.2 The 2024 amendments would have fixed this — and they have NOT taken effect

This is a moving target and the search-result summaries are misleading about it. Verified
against SEC primary sources:

- **SEC Press Release 2024-110 (28 Aug 2024)** [PRIMARY DATA DOC] — **[read in full]**. The
  amendments require funds to "file reports on Form N-PORT on a **monthly basis within 30 days
  after the end of the month**", public "**60 days after the end of each month instead of every
  third month**". Prior regime, quoted: "file these monthly reports on a **quarterly basis
  within 60 days after quarter-end**", with only every third month public. Stated compliance:
  **17 Nov 2025**, or **18 May 2026** for fund groups under $1bn.
- **SEC final rule, 21 April 2025** (`sec.gov/rules-regulations/2025/04/s7-26-22`,
  Release IC-35538, "Delay of Effective and Compliance Dates") [PRIMARY DATA DOC] —
  **[established via SEC rule-page search result and Federal Register listing; the rule PDF
  itself I could not parse — see §7]**. **Effective date delayed from 17 Nov 2025 to 17 Nov
  2027**; compliance **17 Nov 2027** ($1bn+) and **18 May 2028** (<$1bn). The N-CEN amendments
  from the same release were *not* delayed.
- **SEC Press Release 2026-19 (18 Feb 2026)**, "SEC Proposes Amendments to Reduce Burdens in
  Reporting of Fund Portfolio Holdings" [PRIMARY DATA DOC] — **[read in full]**. Proposes to
  "provide reporting funds with an **additional 15 days** to file monthly reports" (45 days) and
  to "**reduce the publication of reports from monthly to quarterly**". Status as of today:
  **proposed, comment period closed 24 April 2026, not adopted.**

**Bottom line for the programme: as of 2026-09-09 there is no monthly public N-PORT, there has
never been one, and the SEC is actively proposing to make quarterly publication permanent.**
Anyone who plans this lane around "monthly N-PORT is coming in 2025" is planning around a rule
that was delayed to 2027–2028 and is currently proposed for repeal. **Do not build on it.**

### 4.3 Form 13F — quarterly, 45 days, structured from 2013Q2, and useless for flows

**[PRIMARY DATA DOC] — SEC "Form 13F Data Sets" page — [read in full]. Form 13F instructions
(`sec.gov/files/form13f.pdf`) — [read in full, extracted locally].**

- Structured data sets: **oldest download is 2013 Q2**; span stated as "July 2013 – May 2026".
- Deadline: **45 calendar days after quarter end**, $100m threshold in section 13(f) securities.
- Information table columns: name of issuer, title of class, **CUSIP**, **FIGI**, value, shares
  or principal amount, voting/dispositive power.
- **Confidential treatment requests** are permitted and are granted "for a period of up to one
  (1) year", after which the holdings are made public. **This is a point-in-time hazard:**
  holdings can appear in the record *retroactively*, so a naive re-read of an old quarter today
  will show positions that were not public at the time.

**13F cannot produce this lane's variable.** It gives holdings only — no TNA-by-fund, no flows —
and it is filed at the **manager** level, not the fund-series level, so a mutual fund's
investor flow is not recoverable from it. 13F is a *holdings* source, at best a substitute for
the `w_{f,i,t-1}` half, and only from 2013Q2.

### 4.4 ICI aggregates — the wrong granularity entirely

**[PRACTITIONER / trade association] — ICI weekly and monthly flow statistics — [snippet
only]** (ici.org pages surfaced in search; not opened). Weekly estimates covering ~98% of
industry assets, broken out by broad category (large/mid/small/multi cap, developed/EM, IG/HY/
government). **These are industry aggregates. There is no per-fund flow.** Since FIT is
`Σ_f w_{f,i,t-1} · Flow_{f,t}`, an aggregate flow with no fund subscript collapses the whole
cross-section to `(aggregate flow) × (ownership share of name i)` — which is not a forced-flow
signal, it is an **ownership-share signal wearing a time-series scalar**. Worth naming
explicitly because it is the failure mode a shortcut would take.

### 4.5 THE DEAD-NAME MAPPING PROBLEM — I tested it, and the programme's known burn is worse than they think

The programme already knows `company_tickers.json` is survivors-only. **I checked whether the
per-CIK submissions API is any better. It is not.** Three live fetches of
`data.sec.gov/submissions/CIK##########.json`:

| CIK | `name` returned | `tickers` | `exchanges` | `formerNames` |
|---|---|---|---|---|
| 1310067 (Sears Holdings, delisted 2018) | `SEARS HOLDINGS CORP` | **`[]`** | **`[]`** | `[]` |
| 886158 (Bed Bath & Beyond, delisted 2023) | **`20230930-DK-Butterfly-1, Inc.`** | **`[]`** | **`[]`** | `BED BATH & BEYOND INC`, **2015-03-08 → 2023-09-20** |
| 320193 (Apple, alive) | `Apple Inc.` | **`["AAPL"]`** | **`["Nasdaq"]`** | — |

**Finding, and it generalises past this lane: `tickers[]` and `exchanges[]` in the EDGAR
submissions API are populated only for currently-listed registrants. The API is survivors-only
for tickers, exactly like `company_tickers.json`.** Anyone who reaches for the submissions JSON
as the "better" alternative walks into the same bias. **This belongs in `G6` (documented
defects in data we already own) whatever happens to G1.**

Note the second row twice over: Bed Bath & Beyond's CIK **is no longer named Bed Bath &
Beyond**. A name-keyed join done today returns `20230930-DK-Butterfly-1, Inc.` — a name that
never traded. **Any name-based match against a current EDGAR name field is silently
point-in-time-wrong for restructured dead names.**

**The one genuinely point-in-time field I found is `formerNames`,** which carries dated
`from`/`to` ranges. That is a real, free, dead-inclusive, as-of-date name history. It is the
foundation any mapping should be built on.

**But the join this lane needs is CUSIP → the fixture's symbol, and I could not establish a
free path for it.** Specifically:

- `FUND_REPORTED_HOLDING.ISSUER_CUSIP` is populated for essentially all US equity holdings.
- `IDENTIFIERS.IDENTIFIER_TICKER` sits under **Item C.1.e, which is the *other identifiers*
  item** — used when the holding lacks a CUSIP. **For US-listed equities with a CUSIP the
  ticker is typically absent.** So N-PORT hands you CUSIP + issuer name and, usually, no ticker.
- **CUSIP is a licensed identifier** (CUSIP Global Services). It appears freely inside SEC
  filings, but I found **no free, authoritative, dead-inclusive, point-in-time CUSIP↔ticker
  crosswalk**.
- **FIGI is the most promising bridge** — it is openly licensed via OpenFIGI, unlike CUSIP, and
  it is a Form 13F column. **But:** it was added by the 13F amendments **effective 3 January
  2023**, and it is **"permitted but not required"** — optional. So it covers **none** of
  2010–2022, and its population rate from 2023 is **unknown to me** (I did not measure it).
  **N-PORT has no FIGI field at all** — the readme's `IDENTIFIERS` table offers only ISIN,
  ticker, and a free-text `OTHER_IDENTIFIER`.
- **ISIN** is present in `IDENTIFIERS` and a US ISIN embeds the CUSIP (`US` + 9-char CUSIP +
  check digit), so ISIN↔CUSIP is mechanical — but that solves the wrong half. It gets you
  between two identifiers you cannot map to a ticker, not to the ticker.

**Honest statement of the state of the data question:** the *flow* half is solved and free from
October 2019 (N-PORT B.5/B.6). The *holdings* half is free and quarterly from October 2019, and
free-but-unstructured (N-Q, N-CSR text) before that. **The identifier half is unsolved**, and it
is unsolved precisely on the dead names that are 35.7% of the fixture and the entire reason the
fixture exists.

### 4.6 What the free window actually is

| period | quarters | free structured fund holdings | free per-fund flows |
|---|--:|---|---|
| 2010Q1 – 2013Q1 | 13 | **none** (N-Q/N-CSR free text only) | **none** |
| 2013Q2 – 2019Q3 | 26 | 13F only (manager-level, holdings-only) | **none** |
| **2019Q4 – 2026Q2** | **27** | **N-PORT, quarterly, ~60d lag** | **N-PORT B.6, monthly, batched quarterly** |
| total fixture | **67** | — | — |

**59% of the fixture window (39 of 67 quarters) has no free per-fund flow data at all.** That is
not a gap to be papered over; it is the majority of the sample.

---

## 5. THE PREMISE NUMBER — what the honest effective observation count is

This is the section I was asked to argue, and I think it is decisive on its own.

### 5.1 The variable's ceiling

`FIT_{i,t} = Σ_f w_{f,i,t-1} · Flow_{f,t}` has two inputs, and **both are quarterly under free
data**:

- `w_{f,i,t-1}`: the ownership map. Refreshes **4×/year**, full stop — N-PORT holdings are a
  quarter-end snapshot (§4.1), and the 2024 amendments that would have made them monthly are
  delayed to 2027–2028 and proposed for repeal (§4.2).
- `Flow_{f,t}`: monthly in N-PORT item B.6, but **published in a quarterly batch**, so it
  arrives 4×/year regardless of its native frequency.

**Ceiling: 4 innovations per name per year. There is no free construction that beats it.**

### 5.2 The naive count, and why it is wrong

Fixture 2010-01-04 → 2026-08-26 = **16.65 years ≈ 4,190 trading days**, **67 quarter-ends**
(2010Q1–2026Q3), of which ~65 are usable formation dates (the first needs a lagged snapshot,
the last a forward return).

Naive multiplication against the programme's stated ~10 effective independent instruments:
**65 × 10 = 650**. **That number is wrong and I want to say why, because it is the number
somebody will reach for.**

### 5.3 Three reasons the true count is far lower

**(i) The treatment is autocorrelated, heavily.** Lou (2012, read in full) reports that FIT
"exhibits significant persistence over time: It is monotonically increasing from deciles one to
ten **in each of the eight quarters surrounding the ranking period**, and the difference in FIT
between the top and bottom deciles is **statistically significant in all eight quarters**". Fund
flows are performance-chasing and persistent — that persistence is the *entire basis* of the
E[FIT] construction. An autocorrelated treatment with quarterly AR(1) coefficient ρ gives
`N_eff,time ≈ T·(1−ρ)/(1+ρ)`. Eight quarters of significant persistence implies a high ρ. At
**ρ = 0.6**: 67 quarters → **~17**. At ρ = 0.7 → **~12**.

**(ii) The ownership map barely moves.** Lou again: "mutual funds turn over their positions
gradually". If `w_{f,i,t-1}` is near-constant across adjacent quarters, then consecutive
formation dates re-select **overlapping name sets**. The programme's ~10 effective instruments
is a property of the *return* panel; it is an upper bound here, not an estimate, because a
persistent map cannot deliver 10 fresh independent cross-sections four times a year.

**(iii) The flow vector has a dominant common component.** Cross-fund flow dispersion is
genuinely large — Dyakov & Verbeek's expected-outflow funds had median actual flow **−2.16%**
against expected-inflow funds' **+7.15%** — so the cross-section is not literally one number.
But the *dispersion* is largely a fund-performance sort, which is (i) again. The residual
idiosyncratic flow innovation is the only truly fresh randomness, and it is a fraction of the
variance.

### 5.4 The numbers

**Full fixture window, if the pre-2019 holdings were reconstructed (paid or by parsing free
text):**

| axis | count |
|---|--:|
| quarterly formation dates | 65 |
| after ρ = 0.6 autocorrelation haircut | **~17** |
| × cross-sectional instruments (generous bound, 10) | **~170** |
| × cross-sectional instruments (plausible, 3) | **~50** |

**Free-data window only (N-PORT, 2019Q4 →):**

| axis | count |
|---|--:|
| quarterly formation dates | **27** |
| after ρ = 0.6 autocorrelation haircut | **~7** |
| × cross-sectional instruments (generous bound, 10) | **~68** |
| × cross-sectional instruments (plausible, 3) | **~20** |

**The honest number for the free-data path is between 7 and 68, and I would write it as
"order 20".**

### 5.5 What that does to a daily book

The programme's book is scored in **bp/bar** over ~4,190 bars. A FIT-conditioned position held
one quarter spans **~63 bars over which the signal is constant**. The number of independent
observations is the number of **formation dates**, not bars:

- Free window: **4,190 / 7 ≈ 600×** overstatement if bars are treated as independent.
- Full window: **4,190 / 17 ≈ 250×**.

A t-statistic computed bar-wise is inflated by roughly **√600 ≈ 24×** (free) or **√250 ≈ 16×**
(full). **Any bp/bar number from this lane must be blocked at the quarter, and the block size
is 63 bars.** This is the same structural error the programme's own lag-audit rule exists to
catch, one level up: not a lookahead in the *held set*, but a lookahead in the *degrees of
freedom*.

### 5.6 Against the programme's own null standard — this is where it ends

`docs/` records the rule: **where the null's group is finite and small, enumerate it**; a time
rotation of ONE market-level series is `Td−1` offsets, **~4,000**, and at that size the sample
p95's SE is exactly 0 and a cell resolves in ~6 minutes. And **D373's rule: a margin within 2 SE
of the p95 is UNRESOLVED.**

**Here the rotatable object is a quarterly aggregate flow series.** Its rotation group is
**`T−1` = 26 offsets** on the free window, **66** on the full window. **Not 4,000. Twenty-six.**

A p95 estimated from 26 order statistics is the 25th of 26 — a single draw, with a bootstrap SE
that is a large fraction of the null distribution's own spread. **Under D373's 2-SE rule,
essentially no margin computed on the free-data window can be resolved.** It is not that the
null would be lenient; it is that the null has **no resolving power at all** at n = 26.

**The programme has already recorded four cases (R7) of a losing random control at the 100th
percentile.** At n = 26 that failure mode is not an edge case, it is the expected behaviour.

### 5.7 So: is the lane dead on the arithmetic, before any return is measured?

**On the daily framing: yes, unambiguously.** A variable with four innovations a year cannot
support a book scored in bp/bar. The 600× overstatement is not a correction to apply, it is a
statement that the instrument and the book are on different clocks.

**On the quarterly framing: not dead, but unresolvable on free data, which for this programme
amounts to the same thing.** 27 formation dates and a 26-offset rotation null cannot clear the
standard the programme has already written down for itself. To get to a resolvable count you
need the pre-2019 window, which requires either paid data (violating "free and dead-inclusive
beats paid") or parsing a decade of unstructured N-Q/N-CSR text — and even then §5.4 puts the
full-window count at ~17 independent time draws, against a rotation group of 66.

**And this arithmetic is the *second* kill, not the first.** §1.4's cost wall — 55 bp gross over
10 days against a 67.6 bp round trip, in the pre-fixture decade, in the only cell that ever
worked — closes the daily version before the observation count is even reached.

---

## 6. What would have to be true for this lane to be worth a study

Stated as falsifiable conditions rather than encouragement, so that a "no" is cheap:

1. **The horizon is a quarter, not a day.** Every cost-honest number in §2 fails at one month
   and clears at three. A one-month or shorter FIT book is refuted by Dyakov–Verbeek's
   2001–2010 subperiod and by BFM's magnitudes. **If the lane is run at all, it is a
   quarterly-rebalanced tilt, and it should be pre-registered as route (b) — "the move is slow
   relative to the spread" — not as route (a).**
2. **The scaling contains no realised return.** §1.3. Derive it; do not inherit it. Scale by
   lagged shares held or lagged shares outstanding, and assert by construction that no
   contemporaneous price enters.
3. **The variable is realised FIT, not E[FIT].** §1.2. E[FIT] is a momentum proxy by Lou's own
   accounting and momentum is excluded. But note that realised FIT is exactly the variable Lou
   finds has **no forward return over the following year** — so condition 3 and a positive
   result are in tension, and that tension is the honest description of this lane.
4. **The null is blocked at the quarter and the block size is stated.** §5.5. And the p95's
   bootstrap SE must be carried, because at n = 26 it dominates.
5. **The identifier join is solved for dead names before any return is computed.** §4.5. If
   CUSIP → fixture symbol cannot be done point-in-time and dead-inclusive, the study is
   survivorship-biased in exactly the way the fixture exists to prevent, and the result is
   uninterpretable regardless of its sign.

**Condition 5 is the cheapest to test and should be tested first.** It is a data question with a
yes/no answer, it costs no runner, and if the answer is no then conditions 1–4 never matter.

---

## 7. Blocks and failures, logged by tool and response

- `WebFetch → papers.ssrn.com/sol3/papers.cfm?abstract_id=3248750`: **HTTP 403 Forbidden.**
- `WebFetch → papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID3248750_...pdf`: **HTTP 403 Forbidden.**
- `WebFetch → onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12962`: **HTTP 403 Forbidden.**
- `WebFetch → www.researchgate.net/publication/342873878_...`: **HTTP 403 Forbidden.**
- `WebFetch → www.terry.uga.edu/directory/malcolm-wardlaw/`: **HTTP 403 Forbidden.**
  *(Wardlaw's paper was therefore established from the RePEc abstract page only, which
  returned the abstract verbatim. Four independent routes to the full text failed.)*
- `WebFetch → www.federalregister.gov/documents/2026/02/23/2026-03460/...`: **HTTP 302 redirect
  to `unblock.federalregister.gov/`**, not followed. Federal Register content was therefore
  obtained from SEC's own press release and rule pages instead.
- `WebFetch → www.ceibs.edu/files/2021-02/001-huang-sheng_jan-2020.pdf`: **HTTP 404 Not Found.**
  *(Huang–Ringgenberg–Zhang is abstract-only for that reason.)*
- `WebFetch → www.sec.gov/files/structureddata/data/form-n-port-data-sets/form-n-port-readme.pdf`:
  **HTTP 404 Not Found.** Correct URL is `www.sec.gov/files/nport_readme.pdf`.
- **`WebFetch` PDF handling failed on every PDF I fetched** — it returned "corrupted or
  improperly encoded PDF" for `nport_readme.pdf`, `formn-port.pdf`, `ic-35963.pdf`,
  `form13f.pdf`, Lou's `flows.pdf`, the Dyakov thesis, BFM, BDR and Israeli–Lee–Sridharan.
  **The files were saved to disk by the tool and I extracted every one of them locally with
  `pypdf`.** `Read` on a PDF also failed: `pdftoppm is not installed` (no poppler on this box).
  **This is a tooling note worth keeping: a WebFetch "corrupted PDF" response is not a block —
  the bytes are on disk and `pypdf` reads them.** Note also that `pypdf`'s output must be piped
  with `PYTHONIOENCODING=utf-8` (cp1252 raises `UnicodeEncodeError` on `∗`) and passed through
  `tr -d '\000'` before `grep` will treat it as text.
- **`sec.gov/files/rules/final/2025/ic-35538.pdf` (the April 2025 delay rule) I did not open.**
  Its content in §4.2 rests on the SEC rule-listing page and Federal Register listing titles
  surfaced in search, corroborated by two law-firm notes. **This is the weakest link in §4.2
  and I flag it in §8.**

**No page, PDF or search result contained text addressed to me, instructions to take an action,
claims of authority, or anything resembling an injection attempt. There is nothing to quote
under that heading.** All content was treated as data.

---

## 8. What I could not verify, stated plainly

1. **Wardlaw (2020) itself.** I read the abstract verbatim from RePEc and nothing more. Four
   routes to the full text returned HTTP 403. **I therefore cannot say which specific scalings
   survive his correction, how large "fairly negligible" is in basis points, or which
   "established results" fail.** Everything §1.3 concludes about *how to scale* is my inference
   from the abstract's wording plus Lou's construction, not something I read him say.
2. **Whether the corrected Wardlaw measure has been re-run post-2010 on equities.** Search
   surfaced claims that later papers built measures "immune to the Wardlaw-critique", but I
   opened none of them and can name no such paper with its result. **Unestablished.**
3. **Coval & Stafford's actual magnitudes.** NBER abstract only. I quote no number from it, and
   the widely-repeated figures for it are not established here.
4. **Huang, Ringgenberg & Zhang's magnitudes.** Abstract only (CEIBS PDF 404). The structural
   claim in §1.5 — discretionary trades are informed and indistinguishable — is theirs from the
   abstract; **no number in that paper is established here.**
5. **Brown–Davies–Ringgenberg's individual-stock result.** Their footnote 32 asserts it in one
   sentence and points to an Internet Appendix I did not obtain. **I do not know its magnitude,
   its horizon, its universe, or its sign at the stock level.** §3.3 should not be read as
   evidence for or against a stock-level ETF-flow signal — only that the *main paper* has none.
6. **The April 2025 N-PORT delay rule (IC-35538).** §4.2's compliance dates (17 Nov 2027 /
   18 May 2028) come from the SEC rule-listing page and search summaries corroborated by law-
   firm notes; **I did not read the rule text.** The direction of travel is triply corroborated
   (Aug 2024 adoption → Apr 2025 delay → Feb 2026 proposed rollback) and I am confident the
   *conclusion* — "monthly public N-PORT does not exist today" — is right. The **exact dates**
   should be re-verified against the rule text before anything is planned around them.
7. **Whether the Feb 2026 proposal has been adopted since April 2026.** I established it was
   proposed 18 Feb 2026 with comments closing 24 April 2026. **I found no evidence of adoption
   and no evidence of non-adoption between April 2026 and today.** Treat the current cadence as
   quarterly-public-with-60-day-lag, and re-check.
8. **FIGI population rate on Form 13F.** Established: optional, effective 3 Jan 2023. **Not
   established: what fraction of filers actually populate it, or whether it covers names that
   died between 2023 and 2026.** This is the most promising open-identifier bridge and its
   viability is entirely unmeasured.
9. **Any free, authoritative, point-in-time CUSIP↔ticker crosswalk covering dead names.** I
   looked and did not find one. **I cannot rule out that one exists.** I also did not
   investigate the CUSIP Global Services licensing position on redistributing CUSIPs extracted
   from public SEC filings — that is a question for the principal, not something I should
   opine on.
10. **Whether `formerNames` is populated densely enough to drive a name-based join.** I saw it
    populated correctly for one dead name (BBBY, with dates) and **empty for another (Sears)**.
    **Two observations. The coverage rate is unknown and the Sears result suggests it is not
    universal.**
11. **The N-PORT `IDENTIFIER_TICKER` population rate for US equity holdings.** My claim that it
    is usually absent for CUSIP-bearing US equities is **an inference from the form's item
    structure** (C.1.e is the *other identifiers* item), **not a measurement.** It is directly
    checkable against one quarterly N-PORT zip and should be checked before §4.5 is relied on.
12. **The ρ = 0.6 autocorrelation figure in §5.4.** That is **my assumption**, motivated by
    Lou's eight-quarter persistence result but **not estimated from anything**. The effective-N
    numbers scale strongly with it: ρ = 0.4 gives ~29 independent quarters on the full window
    instead of 17; ρ = 0.8 gives ~7. **The qualitative conclusion — that a 26-offset rotation
    null cannot resolve anything — does not depend on ρ**, since that count comes from the
    quarter count alone. But the ~7 and ~17 figures are soft and should be replaced by a
    measured autocorrelation of whatever flow series is actually built.
13. **The programme's "~10 effective independent instruments".** I took this from the
    commissioning brief as given and used it as an upper bound. **I did not verify it and have
    no basis to.**
14. **Everything about the programme's own data.** I have not seen the fixture, the universe
    construction, the 33.8 bp/side measurement, or any prior study. Every comparison in this
    brief that puts a literature number against 67.6 bp is **arithmetic on a number I was told**,
    not a measurement I made.
