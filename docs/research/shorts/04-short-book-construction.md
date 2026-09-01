# 04 — Short Book Construction: Financing, Risk and Whether the Short Leg Earns Its Keep

**Status:** web research, external evidence only. No backtests run. All repo-internal numbers
(costs 1.85 bp/side, drift +8.59%/yr overnight, effective breadth ≈ 2.2) are taken as given from
prior measurement and are *used* here, not re-derived.

**Date of market data:** borrow rates and interest rates quoted below were pulled 26–28 Aug 2026
and are point-in-time. Borrow fees are reset daily; treat the table as a snapshot, not a constant.

**Scope note:** this is research on market mechanics, published literature and cost arithmetic.
It is not investment advice, and the capital-allocation decision is the principal's.

---

## 0. Executive summary

Three findings, in order of how much they should change the plan.

**(1) The documented short-leg premium does not live in instruments like ours.** The literature
that says "anomaly return concentrates in the short leg" and the literature that says "anomaly
return concentrates in expensive-to-borrow names" are reporting the *same fact from two sides*.
Muravyev, Pearson & Pollet (JF 2025) close the loop: across 162 anomalies the long/short return is
+0.14%/mo gross, entirely from the short leg, −0.01%/mo after borrow fees — and **not profitable
even before fees once the high-fee 12% of stock-dates are excluded**. Our universe is 57 liquid
general-collateral ETFs borrowing at 25–65 bp. That is, by construction, the low-fee 88% where the
effect is absent. We are not "paying away" the short-leg alpha. We are trading in the part of the
market where it was never measured to exist.

**(2) Borrow is cheap for us; the expensive part is the rate haircut on short proceeds.** Real
IBKR borrow on our core names is 0.25%–0.65%/yr — a rounding error. But IBKR pays **zero interest
on the first $100,000 of short proceeds**, and only benchmark − 1.25% (currently 2.38% vs a 3.63%
benchmark) on the next tranche. Against a frictionless benchmark the short leg's structural carry
cost is **≈4.0%/yr of capital at $100k and ≈2.0%/yr at $700k**. That gradient — not borrow fees —
is the binding size constraint.

**(3) The arithmetic does not close at our breadth.** Adding a short leg doubles gross notional and
therefore doubles the turnover bill. A dollar-neutral book at $700k rebalancing monthly carries a
**≈2.9%/yr structural hurdle** before any alpha. Clearing a >10%/yr net target from that base with
an effective breadth near 2.2 requires an information coefficient of roughly 0.25–0.42, against a
realistic ceiling around 0.05 for a good equity signal. AQR's flagship Equity Market Neutral fund
— thousands of names, institutional financing — has returned **7.30%/yr since Oct 2014**.

**Verdict (full arithmetic in §7): for a $100k–$700k book in 57 co-moving liquid ETFs, the short
leg is not additive. It is a hedge we would pay roughly 2–4%/yr of capital to own, in order to
cancel a measured +8.59%/yr overnight drift.** Minimum viable capital for a dollar-neutral book at
IBKR is **$250k as a hard floor and ~$500k before the financing structure stops actively working
against you** — and clearing that floor fixes the financing, not the breadth problem.

---

## 1. Does the short leg actually add return, or is it only a hedge?

### 1.1 The case that the short leg is where the alpha is

**Stambaugh, Yu & Yuan (2012)**, "The Short of It: Investor Sentiment and Anomalies," *Journal of
Financial Economics* 104(2), 288–302. Across a broad set of cross-sectional anomalies:

- each anomaly's long/short strategy is more profitable following high sentiment;
- **the short leg of each strategy is more profitable following high sentiment**;
- sentiment has **no relation** to returns on the long legs.

The mechanism they propose is asymmetry: market-wide sentiment plus short-sale impediments means
overpricing is easier to create than underpricing, so mispricing accumulates on the short side.

- Paper: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1567616
- NBER w16898: https://www.nber.org/papers/w16898
- Full text (AQR Insight Award): https://www.aqr.com/-/media/AQR/Documents/AQR-Insight-Award/2012/The-Short-of-It.pdf

**The authors' own robustness defence.** Stambaugh, Yu & Yuan (2014), "The Long of It: Odds That
Investor Sentiment Spuriously Predicts Anomaly Returns," *JFE* 114(3), 613–619, answers the
spurious-regression critique by replacing sentiment with simulated persistent series: among 200
million simulated regressors, none supported the conclusion as strongly as actual sentiment.

- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2103302
- NBER w18231: https://www.nber.org/system/files/working_papers/w18231/w18231.pdf

So the "it's in the short leg" claim is not a statistical artifact. It survives its own robustness
tests. The rebuttal that matters is a different one.

### 1.2 The rebuttal: the alpha and the impediment are the same object

**Drechsler & Drechsler**, "The Shorting Premium and Asset Pricing Anomalies" (NBER w20282). This
is the paper the brief asked for, and it is the pivot.

- The cheap-minus-expensive-to-short (CME) portfolio earns **1.31%/mo gross, 0.78%/mo net of
  fees**, with a **1.44% four-factor alpha**.
- Short fees on the short legs of value, momentum, volatility and profitability portfolios run
  **more than triple** the market average.
- Critically: **the anomalies effectively disappear within the 80% of stocks that have low fees**,
  and are large only among high-fee stocks.
- Their interpretation: the shorting premium is arbitrageurs' compensation for concentrated risk
  borne on the short side. A larger premium means a more overpriced stock — but the premium *is*
  the compensation, not free money.

Links: https://www.nber.org/papers/w20282 ·
https://www.nber.org/system/files/working_papers/w20282/w20282.pdf ·
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2387099

**Muravyev, Pearson & Pollet (2025)**, "Anomalies and Their Short-Sale Costs," *Journal of Finance*
80(6), 3639–3694. This is the strongest and most recent statement, and it is close to dispositive.
Verbatim from the abstract:

> "Short-sale costs eliminate the abnormal returns on asset pricing anomaly portfolios. While many
> anomalies persist out-of-sample before accounting for short-sale costs, they cannot be exploited
> with long-short strategies due to stock borrow fees. Using a comprehensive sample of 162
> anomalies, the average long-short portfolio return is a significant 0.14% per month before
> short-sale costs, and the returns are due to the short leg. However, the average is −0.01% once
> returns are adjusted for borrow fees. Moreover, anomalies are not profitable even before fees if
> the high-fee observations, representing 12% of stock dates, are excluded from the analysis."

Links: https://onlinelibrary.wiley.com/doi/10.1111/jofi.13501 ·
https://ideas.repec.org/a/bla/jfinan/v80y2025i6p3639-3694.html

**The last sentence is the one that governs our decision.** It is not merely that borrow fees eat
the short-leg alpha. It is that if you restrict yourself to the 88% of the market that is cheap to
borrow, the anomalies are gone *gross of all costs*. Liquid GC ETFs are the cheapest-to-borrow
instruments in existence. We are not standing in the part of the distribution where the effect was
measured.

**Supporting mechanism — short selling is itself a risk factor.** Engelberg, Reed & Ringgenberg
(2018), "Short Selling Risk," *JF* 73(2), 755–786: lending fees are reset daily and loans can be
recalled, so a short position carries fee-escalation and recall risk. Stocks with more short
selling risk have **lower returns, less price efficiency, and less short selling**. The impediment
that creates the mispricing is the same impediment that deters the arbitrage.

- https://rady.ucsd.edu/faculty/directory/engelberg/pub/portfolios/SHORT_RISK.pdf

Related: Muravyev, Pearson & Pollet (2022), "Is There a Risk Premium in the Stock Lending Market?
Evidence from Equity Options," *JF* — https://onlinelibrary.wiley.com/doi/10.1111/jofi.13129

### 1.3 The general transaction-cost literature points the same way

- **Novy-Marx & Velikov (2016)**, "A Taxonomy of Anomalies and Their Trading Costs," *RFS* 29(1),
  104–147. Execution costs of **20–57 bp** for mid-turnover anomalies. Most anomalies with **under
  50% monthly turnover** generate significant net spreads; few above that do. The most effective
  mitigation is a **buy/hold spread** — stricter entry thresholds than exit thresholds.
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2535173 ·
  https://academic.oup.com/rfs/article/29/1/104/1844518
- **Chen & Velikov**, "Accounting for the Anomaly Zoo: A Trading Cost Perspective." Across 120
  anomalies, the average equal-weighted long/short portfolio nets **−3 bp per month
  post-publication after costs**. Optimised cost mitigation (value weighting, buy/hold spreads)
  lifts that to only **4–12 bp/mo**.
  https://jacobslevycenter.wharton.upenn.edu/wp-content/uploads/2019/09/Accounting-for-the-Anomaly-Zoo.pdf

### 1.4 The empirical record of funds that actually do this

**AQR Equity Market Neutral Fund (QMNIX)** — a live, investable, fee-paying instance of the exact
strategy, run by a firm with institutional financing and thousands of names of breadth. As of
31 Jul 2026 (https://funds.aqr.com/funds/alternatives/aqr-equity-market-neutral-fund/qmnix):

| Metric | Value |
|---|---|
| Inception | 7 Oct 2014 |
| **Annualised since inception** | **7.30%** |
| 10-year annualised | 6.27% |
| 5-year annualised | 18.57% |
| 3-year annualised | 17.73% |
| 1-year | 5.82% |
| YTD through Jul 2026 | **−5.92%** |

The fee table is the more useful artifact, because it is a *direct measurement of what carrying a
short book costs*:

| Component | % |
|---|---|
| Management fee | 1.10 |
| **Dividends on short sales / interest expense** | **4.69** |
| All other expenses | 0.21 |
| Acquired fund fees | 0.03 |
| **Gross expense ratio** | **6.03** |
| Adjusted expense ratio (ex short-carry) | 1.34 |

**Read this carefully — 4.69% is not all real economic cost.** The bulk is dividend expense on
shorts, which is an accounting artifact: you pay the dividend, but the short's price drops by the
dividend, so it is offset in the capital return. The genuinely lost portion is borrow fees plus the
financing spread. But the figure does establish the shape: for a real EMN book, **short-side
carrying items are ~3.5x the management fee**, and the fund's headline 7.30%/yr is reported after
all of it.

Note also the dispersion: 5-year 18.57% but since-inception 7.30% means the 2015–2020 stretch was
badly negative. Equity market neutral has long, deep barren periods. Any plan that assumes a smooth
absolute-return stream from this strategy family is not supported by the record.

### 1.5 Verdict on question 1

The short leg *has historically* carried the anomaly return. It has done so **specifically in
expensive-to-borrow, hard-to-arbitrage names**, and the premium is compensation for the risk of
holding them. In cheap-to-borrow instruments the effect is not detectable even before costs. For a
book restricted to liquid GC ETFs, **the short leg should be modelled as a hedge with a carrying
cost, not as a source of return.**

---

## 2. Borrow mechanics and real costs for a small account

### 2.1 How stock loan works

A short seller must borrow the security to deliver it (Reg SHO locate requirement). The borrower
posts cash collateral, typically ~102% of market value, marked daily. The lender invests that cash
and rebates part of the interest back to the borrower. The **rebate rate** is the borrower's return
on collateral; the **borrow fee** is the shortfall from the risk-free rate.

- **General collateral (GC):** securities with ample supply. Fee is small and the rebate is close
  to the market rate. IBKR's own framing: GC stocks are highly liquid and readily available, but a
  GC name *can become* hard-to-borrow when conditions change.
- **Specials:** limited lendable inventory against high demand. Fee rises, and in extremis the
  rebate goes negative.

IBKR reference material: https://www.interactivebrokers.com/en/pricing/short-sale-cost.php ·
https://www.interactivebrokers.com/en/trading/securities-financing.php ·
https://www.interactivebrokers.com/en/trading/short-securities-availability.php

### 2.2 What we would actually pay — measured, on our universe

Pulled 28 Aug 2026, 13:33 EDT, from ChartExchange, which mirrors the IBKR availability file
(refreshed every 15 minutes):

| ETF | Borrow fee (annualised) | Shares available | Source |
|---|---|---|---|
| SPY | **0.25%** | 6,000,000 | https://chartexchange.com/symbol/nyse-spy/borrow-fee/ |
| QQQ | **0.25%** | 10,000,000 | https://chartexchange.com/symbol/nasdaq-qqq/borrow-fee/ |
| XLF | **0.41%** | 8,300,000 | https://chartexchange.com/symbol/nyse-xlf/borrow-fee/ |
| IWM | **0.64%** | 1,500,000 | https://chartexchange.com/symbol/nyse-iwm/borrow-fee/ |
| XBI | **1.56%** | 1,500,000 | https://chartexchange.com/symbol/nyse-xbi/borrow-fee/ |
| XOP | **1.62%** | 550,000 | https://chartexchange.com/symbol/nyse-xop/borrow-fee/ |

Independent confirmation for SPY at 0.25% with 6.0M shares:
https://companiesmarketcap.com/spdr-sp-500-etf/cost-to-borrow/

**Shape of the distribution.** Mega-cap broad-index ETFs sit at 25 bp. Large sector SPDRs at
40–65 bp. Thinner, more heavily-shorted thematic/sector ETFs (XBI, XOP) at ~1.6%. A 57-name liquid
ETF universe weighted toward the broad and large-sector end should blend to roughly **0.35–0.50%/yr**.
Extending to ~500 US-listed ETFs would pull the tail up materially — the thin end of the ETF
universe includes names at several percent — so **universe extension is not free on the short side.**

**Retail markup, quantified.** State Street reports SPY's volume-weighted average lending fee — what
the *lender* receives wholesale — at **12 bp/yr**, on 14% utilisation, for a 1.6 bp return on
lendable assets (https://www.ssga.com/us/en/intermediary/insights/unlocking-the-securities-lending-potential-of-spy).
IBKR charges us 25 bp. **We pay roughly 2x the wholesale rate on GC ETFs**; the ~13 bp difference is
intermediation spread. This is not a bad deal by retail standards, and it is not the problem.

**Capacity is a non-issue at our size.** The thinnest name above, XOP at 550,000 shares (~$70M+
notional), against a maximum single-name short of ~$12k in a $700k book equal-weighted across 57
names. We are three to four orders of magnitude inside available supply. **Borrow availability does
not constrain us. It is worth stating plainly so it stops being a worry.**

### 2.3 The short rebate — this is where the real money goes

This is the most important mechanical finding in the document and it is specific to small accounts.

IBKR pays interest on cash held as short-sale collateral, but on a **tiered schedule applied to the
short-proceeds balance**, and with an eligibility gate on account NAV.

IBKR's own wording: **"There will be no interest paid on the first USD 100,000."** And on NAV:
accounts with NAV of USD 100,000 or more are paid at the full eligible rate; **accounts below USD
100,000 receive interest at rates proportional to account size** — an account with USD 50,000 NAV
earns half the rate. (https://www.interactivebrokers.com/en/pricing/short-sale-cost.php ·
https://www.interactivebrokers.com/en/accounts/fees/interestPaid_Example2.php)

The tier table, as published by LYNX (an IBKR introducing broker that republishes IBKR's schedule),
USD, benchmark **3.630%** as of 26 Aug 2026 —
https://www.lynxbroker.com/info/ibkr-credit-rates/ :

| Short-proceeds balance (USD) | Rate paid | Formula |
|---|---|---|
| 0 – 100,000 | **0.000%** | — |
| 100,000.01 – 1,000,000 | **2.380%** | BM − 1.25% |
| 1,000,000.01 – 3,000,000 | 3.130% | BM − 0.50% |
| 3,000,000.01+ | 3.380% | BM − 0.25% |

For comparison, ordinary **cash** credit interest is BM − 0.50% = **3.130%** above a $10,000
balance. So short-sale collateral is paid *worse* than idle cash until you clear $1M of short
proceeds.

**Blended rate actually received on short proceeds, dollar-neutral book (short notional = equity):**

| Capital | Short proceeds | Blended rate received | Haircut vs 3.63% benchmark |
|---|---|---|---|
| $100k | $100k | **0.00%** | −3.63% |
| $150k | $150k | 0.79% | −2.84% |
| $250k | $250k | 1.43% | −2.20% |
| $500k | $500k | 1.90% | −1.73% |
| $700k | $700k | **2.04%** | **−1.59%** |
| $1.0M | $1.0M | 2.14% | −1.49% |
| $3.0M | $3.0M | 2.88% | −0.75% |

**At 4%-ish policy rates this is the dominant cost of the short leg, and it is five to fifteen
times larger than the borrow fee.** The brief was right that the rate environment "materially
changes the arithmetic" — it does, and at our size it changes it against us, because the entire
benefit is withheld on the first $100k.

### 2.4 Recall risk

Lenders may recall at any time, forcing an involuntary close-out. Quantified:

- For **easily borrowed stocks, forced recalls occur roughly once in eight years** (Schultz, "What
  Makes Short Selling Risky: Other Short Sellers" —
  https://www.acem.sjtu.edu.cn/sffs/2020/pdf/paper8.pdf).
- For stocks with **utilisation above 50%**, recall occurs on **1.852% of stock-days** — roughly
  once every 54 trading days.
- After recall, the mean (median) time before the short can be re-established is **23 (9) trading
  days**.
- Recall days show **more than twice** the stock's mean trading volume and elevated intraday
  volatility.
- Optimal-stopping models of shorting under margin and recall frictions find a **~17% loss in
  value** versus a frictionless benchmark under conservative parameters
  (https://arxiv.org/abs/1903.11804).

**Implication for us: near-zero risk.** Our ETFs sit at very low utilisation with millions of
shares available. Recall risk is a hard-to-borrow phenomenon and we are not in that regime. The
23-day re-establishment lag would be genuinely destructive to a systematic book — it silently turns
a full-notional strategy into a partially-invested one — but it is not a risk we are running.

### 2.5 Margin requirements and the gross-exposure ceiling

**Reg T / FINRA Rule 4210** (https://www.finra.org/rules-guidance/rulebooks/finra-rules/4210 ·
https://www.finra.org/rules-guidance/key-topics/margin-accounts):

- Initial margin on a short sale: **150% of market value** — 100% from the short proceeds
  themselves plus **50% deposited**.
- Initial margin on a long: **50%**.
- Maintenance: **25%** of market value long; **30% or $5/share, whichever is greater**, short.

**The gross-exposure algebra.** Under Reg T, equity required = 0.5 × (long + short) = 0.5 × gross.
So with equity `E`, **maximum gross is 2E**. A dollar-neutral book therefore runs at most
**1.0x per side** (L = S = E, gross = 2E) under Reg T. That is the ceiling, and it means the
"leverage" often assumed for market-neutral strategies is simply unavailable in a Reg T account.

**Portfolio margin** relaxes this via a risk-based model, but has a hard capital gate:

- **$110,000 to initiate, $100,000 to maintain** at IBKR. Below $100,000 the account is subject to
  a **margin surcharge that progressively transitions it back toward Reg T levels** as equity
  declines.
- FINRA/industry standard elsewhere is $125,000 initial (e.g. Schwab —
  https://www.schwab.com/margin/portfolio-margin).
- Reg T caps overnight leverage at 2:1; **portfolio margin can reach 6.67:1 or more**.
- IBKR applies concentration add-ons: **full margin required for ETF concentrations ≥ 5%**.
  (https://www.interactivebrokers.com/en/trading/margin-stocks.php ·
  https://en.wikipedia.org/wiki/Portfolio_margin)

**This is the second hard threshold at ~$100–110k**, and it coincides with the short-rebate
threshold. Below it: no portfolio margin, gross capped at 2x, and zero interest on short proceeds.
The two constraints stack at the same number, which is why the minimum-viable-capital answer in §6
is as sharp as it is.

**One favourable note on the balance sheet.** For a dollar-neutral book with L = S = E, cash after
buying the longs is exactly zero. There is **no margin loan and no debit interest**. The financing
cost is entirely the opportunity cost of the withheld rebate, which is what §2.3 measures. This is
cleaner than it is often assumed to be — the problem is the withheld rebate, not a borrowing charge.

---

## 3. Crowding and squeeze risk

### 3.1 Metrics

- **Short interest ratio / days to cover (DTC)** = short interest ÷ average daily volume. Hong, Li,
  Ni, Scheinkman & Yan, "Days to Cover and Stock Returns" (NBER w21166,
  https://www.nber.org/system/files/working_papers/w21166/w21166.pdf) frame DTC as the cost of
  exiting a crowded trade: arbitrageurs demand a premium for high-DTC names.
- **Utilisation** = shares on loan ÷ lendable supply. The cleanest direct crowding measure, and the
  variable that governs recall risk (§2.4).
- **Borrow fee level and fee volatility** — the market's own price of crowding, and the input to
  Engelberg/Reed/Ringgenberg's short-selling-risk measure.

Evidence on direction: internationally, **DTC and utilisation are among the most robust short-sale
measures for predicting future returns**, and in large samples heavy shorting is normally a
*bearish* signal — short sellers are informed. Rapach, Ringgenberg & Zhou (2016), "Short Interest
and Aggregate Stock Returns," *JFE* 121(1), 46–65, find aggregate short interest is **arguably the
strongest known predictor of aggregate stock returns**, with annual in-sample and out-of-sample R²
of **12.89% and 13.24%**, and utility gains above **300 bp/yr** for a mean-variance investor
(https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2474930).

So crowding is normally informative and normally profitable. The tail is the problem.

### 3.2 January 2021, quantified

- The **Goldman Sachs Highest Short Interest basket** (50 most-shorted Russell 3000 names above
  $1bn market cap) rose **+52.1% YTD through 27 Jan 2021**.
- Over three months, the most-shorted stocks rose **+98%** — Goldman called it the **most extreme
  short squeeze in 25 years**, versus **+72%** during the 1999–2000 tech bubble. Trailing 5-, 10-
  and 21-day returns were **the largest on record**.
  (https://www.cnbc.com/2021/01/31/goldman-sachs-says-this-is-the-biggest-short-squeeze-in-25-years-with-shorted-stocks-up-98percent.html)
- **Hedge fund gross leverage fell 7.5% in a single day and 10% over the week of 25 Jan — the
  largest active deleveraging since February 2009.**
- Fund-level: Melvin Capital **−53% in January**, −49% over Q1; Maplelane **−45% in January**,
  −39.5% Q1; D1 Capital **−20% in January**; Light Street −20% Q1; White Square closed its main
  fund. GameStop short interest reached **~140% of float**; shorts lost roughly **$10bn**.
  (https://en.wikipedia.org/wiki/GameStop_short_squeeze)

**The lesson, stated mechanically rather than narratively.** Almost none of the damage came from
the short thesis being wrong. It came from three things compounding: (a) unbounded single-name
convexity on the short side; (b) margin calls forcing covering into a bid-less tape; and (c) the
deleveraging in (b) being *industry-wide and simultaneous*, so that every position in every book
became correlated for a week regardless of its own fundamentals. A dollar-neutral book does not
protect you from (c) — the systematic deleveraging hits your longs and shorts in the same direction.

### 3.3 How practitioners cap single-name short risk

Standard controls, in rough order of how universally they are applied: hard per-name notional caps
(commonly 0.5–2% of NAV on the short side, tighter than on longs); caps expressed as a multiple of
average daily volume or as a share of *days to cover*, so the position can be exited inside normal
liquidity; utilisation and borrow-fee screens that exclude names above a threshold; automatic
downsizing when borrow fee rises; and gross-exposure de-risking triggers keyed to realised
portfolio volatility.

### 3.4 Why this section largely does not apply to us — the strongest point in favour of ETF shorts

**An ETF cannot be squeezed the way a single name can, because its share supply is elastic.**
Authorised Participants create new ETF shares on demand by delivering the underlying basket. If ETF
price rises above NAV, the AP arbitrage creates supply and closes the gap. ETF short interest can
and does exceed 100% of shares outstanding without pathology, because a share can be lent more than
once.

> "The creation and redemption mechanism is the primary reason why it is nearly impossible to
> engineer a short squeeze for an ETF."
> — ORTEX, https://public.ortex.com/why-its-nearly-impossible-to-squeeze-etfs/

Background: https://www.schwabassetmanagement.com/content/understanding-etf-creation-and-redemption-mechanism ·
Evans et al. on operational shorting in ETFs,
https://jacobslevycenter.wharton.upenn.edu/wp-content/uploads/2018/08/ETF-Short-Interest-and-Failures-to-Deliver.pdf

**Consequence: for our universe, the two classic short-book killers — squeeze and recall — are both
near-absent.** This is a genuine, material advantage of the ETF universe over single-name shorts and
it should be stated as such. It does not, however, create return. It removes a tail risk from a
strategy whose central problem (§7) is that it has no measurable edge to begin with.

---

## 4. Construction choices that matter

### 4.1 Dollar- vs beta- vs sector-neutral

| Approach | What it buys | What it costs |
|---|---|---|
| **Dollar-neutral** (Σlong $ = Σshort $) | Exact, estimation-free cancellation. No parameters, no lookback, nothing to misfit. **For us: cancels the +8.59%/yr overnight drift exactly.** | Does **not** guarantee beta neutrality — residual beta equals the net of underlying betas. A book long high-beta and short low-beta is dollar-neutral and market-directional. |
| **Beta-neutral** (Σwᵢβᵢ = 0) | Removes market directionality, which dollar neutrality does not. | Introduces **estimation risk**: betas are noisy, unstable, and break in regime changes. You trade a known exact cancellation for an estimated approximate one. See "Betas and the myth of market neutrality," https://www.sciencedirect.com/science/article/abs/pii/S0169207015001533 |
| **Sector-neutral** | Removes the largest common factor after market. Practitioners pair longs and shorts within sector/factor/country to isolate stock selection. | On a 57-ETF universe of *sector* ETFs, sector neutrality is close to self-defeating — it constrains away the very axis the universe is built on. It also cuts already-scarce breadth further. |

Practitioner framing: https://caia.org/blog/2024/03/17/demystifying-equity-market-neutral-investing ·
https://www.simplify.us/blog/demystifying-equity-market-neutral-investing

**Assessment against our constraints.** Dollar neutrality is the right choice *if* we neutralise at
all: it is exact, parameter-free, and directly cancels the drift we have measured. Beta neutrality
adds estimation risk for a benefit that dollar-neutrality on a broad-ETF universe largely already
delivers (ETF betas cluster near 1). Sector neutrality is inapplicable. **But note the trap: our
measured effective breadth of ~2.2 means the book is already close to being a small number of
factor bets. Adding neutrality constraints to a 2.2-bet book removes bets, it does not add
robustness.**

### 4.2 Rebalancing frequency versus cost — the table that decides it

Our measurement: **1.85 bp/side**, so 3.70 bp per round trip per unit notional. Confirming the
stated figure: (1 − 0.000370)^252 = 0.9110 → **−8.90%/yr** for one daily round trip on 1x notional. ✓

**A dollar-neutral book runs 2x gross, so the same schedule costs twice as much:**
(1 − 0.000740)^252 = 0.8298 → **−17.02%/yr**.

| Rebalance frequency | Rebalances/yr | Cost, 1x gross (long-only) | **Cost, 2x gross (dollar-neutral)** |
|---|---|---|---|
| Daily | 252 | −8.90% | **−17.02%** |
| Weekly | 52 | −1.91% | **−3.78%** |
| Six-weekly | 8.7 | −0.32% | **−0.64%** |
| Monthly | 12 | −0.44% | **−0.88%** |
| Quarterly | 4 | −0.15% | **−0.30%** |

(Assumes 100% turnover at each rebalance — a worst case. Real books turn over a fraction of the
book each period, so treat these as upper bounds.)

**What real market-neutral books do, and why.** The spectrum is genuinely wide: statistical
arbitrage books rebalance every 5–15 minutes; traditional quant market-neutral funds run
substantially lower turnover and target longer-horizon factor alpha; one quantitative fund
determined its **optimal interval to be six weeks**, based on proprietary market-impact models
(https://thehedgefundjournal.com/campbell-quantitative-equities/ ·
https://www.morningstar.com/funds/market-neutral-funds-watch-these-fast-growing-quantitative-equity-strategies).

The reason for that spread is simple and it is the Novy-Marx/Velikov result: **the signal's decay
horizon must be longer than the cost of trading it.** Their finding that anomalies below **50%
monthly turnover** survive costs while few above it do is the practical rule. Books that rebalance
in minutes have per-trade costs measured in fractions of a basis point and signals that decay in
minutes. We have neither.

**Direct implication: daily rebalancing is disqualified for a dollar-neutral book at our cost
level.** −17%/yr is not a hurdle any realistic ETF cross-sectional signal clears. The habitable
region is **monthly to quarterly (−0.30% to −0.88%/yr)**, with weekly (−3.78%) already demanding a
signal strong enough that its existence would be surprising. Novy-Marx & Velikov's **buy/hold
spread** — requiring a stronger score to open a position than to keep it — is the single most
effective mitigation available and should be assumed in any design.

### 4.3 Position sizing and the asymmetry

A short's loss is unbounded; its gain is capped at 100%. Three consequences:

1. **Positions grow as they lose.** A short that doubles becomes twice the book weight it was sized
   at, and does so precisely when it is hurting. Longs do the opposite — they shrink as they lose,
   self-limiting. A short book therefore requires *active* re-sizing to hold target weights, which
   means turnover that a long book gets for free. That turnover is a real cost at 1.85 bp/side.
2. **Rebalancing a short book is systematically the wrong-way trade.** Holding constant weights
   means selling more of what has fallen and buying back what has risen — momentum-negative by
   construction.
3. **For ETFs, the asymmetry is much milder than for single names.** A diversified sector ETF does
   not go up 10x; the creation/redemption mechanism (§3.4) removes the squeeze channel entirely.
   The unbounded-loss argument is a strong reason to avoid *single-name* shorts and a weak one
   against *ETF* shorts.

---

## 5. Does this work at our size?

### 5.1 Fixed costs — a smaller problem than expected

- **Borrow minimums:** none at IBKR for GC names, and availability exceeds our need by 3–4 orders
  of magnitude (§2.2). **Not a constraint.**
- **Commissions:** already measured at 1.85 bp/side and included throughout.
- **Data:** liquid US ETF EOD/intraday data is inexpensive; not a threshold cost at $100k+.
- **Margin:** genuinely constraining below $110k (§2.5) — no portfolio margin, gross capped at 2x.
- **Short rebate:** the binding one. Zero on the first $100k regardless of account size, and
  further pro-rated down if NAV itself is under $100k.

**The honest conclusion is that the small-account problem is not the fixed costs anyone worries
about. It is a single pricing tier.**

### 5.2 Structural drag by capital level

Dollar-neutral, L = S = E, blended ETF borrow 0.40%, monthly rebalance, benchmark 3.63%:

| Capital | Rebate haircut vs 3.63% | Borrow fee | Turnover (monthly, 2x gross) | **Total annual hurdle** |
|---|---|---|---|---|
| $75k (NAV < 100k) | −3.63% | −0.40% | −0.88% | **−4.91%** |
| $100k | −3.63% | −0.40% | −0.88% | **−4.91%** |
| $250k | −2.20% | −0.40% | −0.88% | **−3.48%** |
| $500k | −1.73% | −0.40% | −0.88% | **−3.01%** |
| $700k | −1.59% | −0.40% | −0.88% | **−2.87%** |
| $3M | −0.75% | −0.40% | −0.88% | **−2.03%** |

The hurdle falls by roughly **2 percentage points** between $100k and $700k, and then only another
0.8 points all the way to $3M. **The curve is steep exactly across our capital range and flat
above it.**

### 5.3 Minimum viable capital

- **Below $100k: not viable.** No portfolio margin, gross capped at 2x, and short proceeds earn
  *nothing* — the short leg costs the full risk-free rate plus borrow, ~4.0%/yr of capital, before
  a single trade. You are paying 4% to run a hedge.
- **$100k–$250k: viable mechanically, poor economically.** Portfolio margin becomes reachable at
  $110k. But the first $100k of short proceeds still earns zero, so at $150k the blended rebate is
  0.79% and the hurdle is ~4.1%.
- **$250k: the hard floor.** Blended rebate 1.43%, hurdle ~3.5%. This is the point at which the
  financing structure stops being actively punitive.
- **$500k+: the sensible floor.** Hurdle ~3.0% and falling slowly. Above this, further capital
  improves the arithmetic only marginally — the remaining problem is breadth, not size.

**Answer: $250k is the hard minimum, $500k is the number I would actually use.** And note what
that means: clearing the floor fixes the *financing*. It does not fix §6.

### 5.4 The prop-firm routing note

The stated goal routes returns through prop-firm payouts. This deserves a flag, because the two
halves of the plan are structurally in tension:

- Payout splits across major firms as of Aug 2026 run **80–100%**, most settling at **90/10**, with
  headline 100% rates applying only to a first tranche (e.g. first $25k at Apex, first $10k at
  Topstep) before reverting to 90/10.
  (https://thortradecopier.com/blog/how-prop-firm-payouts-work · https://damnpropfirms.com/prop-firm-rules/)
- The prop-firm universe is overwhelmingly **futures**, not cash equities/ETFs. A cash short with
  stock-loan mechanics is not the instrument these programmes are built around.
- Rules include trailing drawdown, daily loss limits, consistency rules capping the best day, and
  minimum trading days (Apex 5, Topstep 5 winning days of $150+, Bulenox 10).
- **Critically: many firms force flat at the close.** FundedSeat closes every position at 4:59pm ET
  — no overnight, no weekends. Some firms (e.g. Elite Trader Funding) offer overnight-capable
  account types.
  (https://elitetraderfunding.app/blog/swing-trading-prop-firms-which-allow-overnight-holds-2026)

**The tension:** our measured edge is **+8.59%/yr overnight and −0.36% intraday**. Essentially all
of the drift is an overnight phenomenon. A prop programme that forces flat at the close removes the
entire source of return. Any prop route must be filtered for overnight-hold permission first, and
that filter is doing more work than the payout split.

---

## 6. The breadth constraint, which dominates everything above

Grinold's fundamental law: **IR = IC × √BR**, where BR is the number of *independent* bets per year
(https://analystprep.com/study-notes/cfa-level-2/state-and-interpret-the-fundamental-law-of-active-portfolio-management-including-its-component-terms-transfer-coefficient-information-coefficient-breadth-and-active-risk-aggressiveness/ ·
https://www.sciencedirect.com/science/article/pii/S0927539817300543).

Our measurement: **effective independent instruments saturate near 2.2 regardless of headcount.**
That is the whole ballgame, and it is worth being explicit about why. Adding ETFs 58 through 500
raises headcount but not breadth, because they co-move. A "diversified" ETF book is not diversified.

With BR ≈ 2.2 independent bets per rebalance and monthly rebalancing, annual breadth ≈ 26.4, so
√BR ≈ 5.14. Required IC to hit a given information ratio:

| Target | Required IR | Required IC at BR = 26.4/yr |
|---|---|---|
| 10% net at 6% vol | 1.67 (net) → 2.15 gross after the 2.87% hurdle | **0.42** |
| 10% net at 10% vol | 1.00 (net) → 1.29 gross | **0.25** |
| 6% net at 6% vol | 1.00 (net) → 1.48 gross | **0.29** |

A strong, genuine equity cross-sectional signal has an IC around **0.03–0.05**. At IC = 0.05 and
BR = 26.4, IR = 0.26 — at a 6% vol target that is **1.5%/yr of gross alpha, against a 2.87%/yr
hurdle.** The book loses money on expectation.

To reach IC ≈ 0.25–0.42 would require forecasting skill roughly **five to eight times** anything
documented in the literature. And note the direction of the error: **`gross = exposure × edge`, and
selectivity cannot create gross return.** Raising exposure raises the turnover bill and the borrow
bill proportionally; it does not raise the edge. There is no configuration of the book that escapes
this, because the constraint is in the universe, not the implementation.

---

## 7. Verdict

**Is the short leg additive for a book of our size and universe, or is it a hedge we would be
paying for?**

**It is a hedge we would be paying for. The arithmetic:**

At $700k, dollar-neutral, monthly rebalance, blended ETF borrow 0.40%:

```
  Short-proceeds rebate received            +2.04%   (blended: $0 on first $100k, 2.38% on $600k)
  Rebate haircut vs 3.63% benchmark         −1.59%   (the real financing cost of the short leg)
  Borrow fees on short notional             −0.40%
  Incremental turnover from doubling gross  −0.44%   (2x gross vs 1x, monthly, 100% turnover)
  ─────────────────────────────────────────────────
  Cost of carrying the short leg            −2.43%/yr of capital

  Expected gross alpha from the short leg    ~0.00%/yr
```

The zero on the last line is not pessimism, it is the literature. Muravyev, Pearson & Pollet find
that across 162 anomalies the entire long/short premium comes from the short leg — **and vanishes
entirely once the high-borrow-fee 12% of stock-dates are excluded, before any costs.** Drechsler &
Drechsler find the anomalies "effectively disappear within the 80% of stocks that have low fees."
Our 57 liquid ETFs, borrowing at 25–65 bp against a wholesale rate of 12 bp, are the definitional
low-fee case. **We would be shorting precisely the instruments in which the short-leg premium has
been measured not to exist.**

What we would get for that −2.43%/yr is real but narrow: exact cancellation of the +8.59%/yr
overnight drift, near-immunity to squeeze (creation/redemption elasticity) and to recall (utilisation
far below the 50% threshold where recalls run at 1.852% of stock-days). That is a well-behaved,
low-tail-risk hedge. **It is a hedge that cancels a positive drift, at a cost of 2.4%/yr, in
exchange for access to a relative-value edge that our own measured breadth of 2.2 cannot support.**

**Three specific conclusions:**

1. **Do not build a dollar-neutral ETF book expecting the short leg to contribute return.** Build
   it only if the objective is explicitly drift-cancellation and the ~2.4%/yr (at $700k) is
   accepted as the price of that. At $100k the price is ~4.9%/yr and I would not pay it.
2. **Minimum viable capital for a dollar-neutral book at IBKR is $250k hard / $500k sensible** —
   set by the short-proceeds rebate tier ($0 on the first $100k) and the portfolio-margin gate
   ($110k initiate / $100k maintain), which stack at the same threshold.
3. **The binding constraint is breadth, not cost, and more capital does not fix it.** At BR ≈ 2.2
   the required IC to hit a >10%/yr net target is 0.25–0.42 against a realistic ceiling near 0.05.
   Every remaining lever — universe extension to 500 ETFs, higher gross, better execution — moves
   cost or exposure. None of them moves breadth. **If the >10%/yr target is firm, the honest next
   step is to look for a source of independent bets, not a better signal on these 57 instruments.**

For calibration on what "good" looks like in this strategy family: AQR's Equity Market Neutral fund
— thousands of names, institutional financing, decades of research — has compounded at **7.30%/yr
since 2014**, with a −5.92% drawdown year-to-date in 2026.

---

## Sources

**Academic — short leg and anomalies**
- Stambaugh, Yu & Yuan (2012), "The Short of It: Investor Sentiment and Anomalies," *JFE* 104(2), 288–302 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1567616 · https://www.nber.org/papers/w16898 · https://www.aqr.com/-/media/AQR/Documents/AQR-Insight-Award/2012/The-Short-of-It.pdf
- Stambaugh, Yu & Yuan (2014), "The Long of It: Odds That Investor Sentiment Spuriously Predicts Anomaly Returns," *JFE* 114(3), 613–619 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2103302 · https://www.nber.org/system/files/working_papers/w18231/w18231.pdf
- Drechsler & Drechsler, "The Shorting Premium and Asset Pricing Anomalies," NBER w20282 — https://www.nber.org/papers/w20282 · https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2387099
- Muravyev, Pearson & Pollet (2025), "Anomalies and Their Short-Sale Costs," *JF* 80(6), 3639–3694 — https://onlinelibrary.wiley.com/doi/10.1111/jofi.13501 · https://ideas.repec.org/a/bla/jfinan/v80y2025i6p3639-3694.html
- Engelberg, Reed & Ringgenberg (2018), "Short Selling Risk," *JF* 73(2), 755–786 — https://rady.ucsd.edu/faculty/directory/engelberg/pub/portfolios/SHORT_RISK.pdf
- Muravyev, Pearson & Pollet (2022), "Is There a Risk Premium in the Stock Lending Market?" *JF* — https://onlinelibrary.wiley.com/doi/10.1111/jofi.13129
- Rapach, Ringgenberg & Zhou (2016), "Short Interest and Aggregate Stock Returns," *JFE* 121(1), 46–65 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2474930
- Hong, Li, Ni, Scheinkman & Yan, "Days to Cover and Stock Returns," NBER w21166 — https://www.nber.org/system/files/working_papers/w21166/w21166.pdf
- Schultz, "What Makes Short Selling Risky: Other Short Sellers" — https://www.acem.sjtu.edu.cn/sffs/2020/pdf/paper8.pdf
- "Short Selling with Margin Risk and Recall Risk" — https://arxiv.org/abs/1903.11804

**Academic — trading costs**
- Novy-Marx & Velikov (2016), "A Taxonomy of Anomalies and Their Trading Costs," *RFS* 29(1), 104–147 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2535173 · https://www.nber.org/system/files/working_papers/w20721/w20721.pdf
- Chen & Velikov, "Accounting for the Anomaly Zoo: A Trading Cost Perspective" — https://jacobslevycenter.wharton.upenn.edu/wp-content/uploads/2019/09/Accounting-for-the-Anomaly-Zoo.pdf
- Grinold's fundamental law — https://www.sciencedirect.com/science/article/pii/S0927539817300543

**Broker and regulator documentation**
- IBKR Short Sale Cost — https://www.interactivebrokers.com/en/pricing/short-sale-cost.php
- IBKR Interest Paid on Short Sale Proceeds — https://www.interactivebrokers.com/en/accounts/fees/interestPaid_Example2.php
- IBKR Stock Margin Requirements — https://www.interactivebrokers.com/en/trading/margin-stocks.php
- IBKR Short-Securities Availability (SLB) — https://www.interactivebrokers.com/en/trading/short-securities-availability.php
- LYNX (IBKR introducing broker), republished IBKR rate schedule, 26 Aug 2026 — https://www.lynxbroker.com/info/ibkr-credit-rates/
- FINRA Rule 4210 — https://www.finra.org/rules-guidance/rulebooks/finra-rules/4210
- FINRA margin accounts key topics — https://www.finra.org/rules-guidance/key-topics/margin-accounts
- Schwab portfolio margin — https://www.schwab.com/margin/portfolio-margin

**Market data (point-in-time, 28 Aug 2026)**
- ChartExchange borrow fees (mirrors IBKR availability file): SPY https://chartexchange.com/symbol/nyse-spy/borrow-fee/ · QQQ https://chartexchange.com/symbol/nasdaq-qqq/borrow-fee/ · XLF https://chartexchange.com/symbol/nyse-xlf/borrow-fee/ · IWM https://chartexchange.com/symbol/nyse-iwm/borrow-fee/ · XBI https://chartexchange.com/symbol/nyse-xbi/borrow-fee/ · XOP https://chartexchange.com/symbol/nyse-xop/borrow-fee/
- CompaniesMarketCap SPY cost to borrow — https://companiesmarketcap.com/spdr-sp-500-etf/cost-to-borrow/
- State Street, "Unlocking the securities lending potential of SPY" — https://www.ssga.com/us/en/intermediary/insights/unlocking-the-securities-lending-potential-of-spy
- AQR Equity Market Neutral Fund (QMNIX) — https://funds.aqr.com/funds/alternatives/aqr-equity-market-neutral-fund/qmnix

**Practitioner sources (named as such)**
- ORTEX on ETF squeeze impossibility — https://public.ortex.com/why-its-nearly-impossible-to-squeeze-etfs/
- Schwab Asset Management on ETF creation/redemption — https://www.schwabassetmanagement.com/content/understanding-etf-creation-and-redemption-mechanism
- Evans et al., ETF short interest and failures-to-deliver — https://jacobslevycenter.wharton.upenn.edu/wp-content/uploads/2018/08/ETF-Short-Interest-and-Failures-to-Deliver.pdf
- CAIA, "Demystifying Equity Market Neutral Investing" — https://caia.org/blog/2024/03/17/demystifying-equity-market-neutral-investing
- Morningstar on market-neutral fund turnover — https://www.morningstar.com/funds/market-neutral-funds-watch-these-fast-growing-quantitative-equity-strategies
- The Hedge Fund Journal, Campbell Quantitative Equities (six-week rebalance interval) — https://thehedgefundjournal.com/campbell-quantitative-equities/
- CNBC on the GS Highest Short Interest basket, Jan 2021 — https://www.cnbc.com/2021/01/31/goldman-sachs-says-this-is-the-biggest-short-squeeze-in-25-years-with-shorted-stocks-up-98percent.html
- GameStop short squeeze, fund-level losses — https://en.wikipedia.org/wiki/GameStop_short_squeeze
- Prop firm payout structures 2026 — https://thortradecopier.com/blog/how-prop-firm-payouts-work · https://damnpropfirms.com/prop-firm-rules/ · https://elitetraderfunding.app/blog/swing-trading-prop-firms-which-allow-overnight-holds-2026
