# Cross-Sectional Signals That Predict Negative Forward Equity Returns

**Literature review — web research only. No backtests run. No repo code touched.**

Date: 2026-08-28
Scope: what the academic and practitioner literature actually establishes about short-side
cross-sectional predictability, assessed against this programme's five measured constraints.

---

## 0. Headline

**The short-side anomaly literature is almost entirely about individual stocks, and the part of it
that survives scrutiny is almost entirely about stocks we cannot trade.** Three independent,
high-quality results — Asquith/Pathak/Ritter (2005), Hou/Xue/Zhang (2020), and Muravyev/Pearson/Pollet
(2025) — each *separately* eliminate the entire short-leg premium once you restrict to
value-weighted, large-cap, cheap-to-borrow names. That is exactly our universe. This is not a
"decayed a bit" story; it is a "the effect was never in these names" story.

The honest finding of this review is that **there is essentially no stock-level short anomaly that
transfers to 57 liquid US ETFs.** The only genuinely ETF-level short-side evidence I found is:

1. **Specialized/thematic ETFs** (Ben-David, Franzoni, Kim & Moussawi, RFS 2023): −3%/yr alpha,
   −6%/yr in year one, persisting ~5 years. Real, published in a top journal, ETF-level, low
   turnover, cheap to borrow. Tiny breadth in our universe.
2. **Volatility ETPs** (VXX and family): roll yield of roughly −30%/yr. Enormous effect size,
   breadth of one name, and a documented catastrophic left tail (XIV, Feb 2018).
3. **ETF NAV mispricing reversal** (Petajisto, FAJ 2017): 14–26%/yr Carhart alpha — but *explicitly
   only after excluding diversified US equity, Treasuries and sector funds*, and it requires near-daily
   turnover. Both exclusions are fatal for us.

Everything else in this document is documented, sourced, and then killed.

One structural note before the candidates: **there is also a sign warning at the ETF level.** ETF short
interest is dominated by hedging and market-maker "operational shorting", not directional bearish
views, and the published evidence is that high ETF short exposure *positively* predicts subsequent
underlying-index returns — the opposite sign to the stock-level result
([Chichernea et al., *J. Financial Research*, 2026](https://onlinelibrary.wiley.com/doi/10.1111/jfir.70050?af=R);
[Evans, Moussawi, Pagano & Sedunov, "ETF Short Interest and Failures-to-Deliver"](https://jacobslevycenter.wharton.upenn.edu/wp-content/uploads/2018/08/ETF-Short-Interest-and-Failures-to-Deliver.pdf)).
Naively porting Boehmer-Jones-Zhang to ETFs would have us trading the wrong way round.

---

## 1. How each candidate is being judged

Our measured constraints, restated as arithmetic tests:

| # | Constraint | Test applied below |
|---|---|---|
| 1 | Overnight drift +8.59%/yr, intraday −0.36%/yr | Is the signal intraday-only, or dollar-neutral? A naked short pays 8.59%/yr. |
| 2 | 1.85 bp/side; one round trip/day = −8.90%/yr | What is the signal's natural rebalance frequency? Monthly ≈ −0.44%/yr; daily = dead. |
| 3 | `gross = exposure × edge` | Effect size × fraction of universe/time it applies to. Reported for every candidate. |
| 4 | Universe mean-reverts hard (beaten-down quintile +16.83%) | Does the signal reduce to "short what has fallen"? Five falsifications already. |
| 5 | Effective breadth saturates near 2.2 | Does the signal produce genuinely dispersed exposures, or one common bet? |

A sixth test the literature itself forces on us:

| 6 | **Does it survive value-weighting, large-cap restriction, and general-collateral borrow?** | This is the filter that kills nearly everything. |

---

## 2. Candidate signals

### 2.1 Short interest and days-to-cover

**Core claims.**

- Boehmer, Jones & Zhang, "Which Shorts Are Informed?", *JF* 2008
  ([SSRN 855044](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=855044)) — heavily shorted stocks
  underperform lightly shorted by **1.16% risk-adjusted over 20 trading days (~15.6%/yr)**;
  institutional non-program short sales carry the information.
- Boehmer, Huszár & Jordan, "The Good News in Short Interest", *JFE* 2010
  ([ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0304405X09002402);
  [SSRN 1405511](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1405511)) — **the long leg is
  bigger than the short leg.** Low-short-interest alphas ≈ **+1.0%/month**; high-short-interest alphas
  ≈ **−0.50%/month**. This is a *long* signal that happens to have a short tail.
- Cohen, Diether & Malloy, "Supply and Demand Shifts in the Shorting Market", *JF* 2007
  ([SSRN 672381](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=672381)) — a shorting *demand*
  shift predicts **−2.98% abnormal return next month**. Requires proprietary stock-loan data.
- Hong, Li, Ni, Scheinkman & Yan, "Days to Cover and Stock Returns"
  ([SSRN 2568768](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2568768);
  [NBER w21166](https://www.nber.org/system/files/working_papers/w21166/w21166.pdf)) — DTC
  (short interest / volume) beats raw short ratio: **1.19%/month EW vs 0.71%/month**, 1988–2012.

**The killer.** Asquith, Pathak & Ritter, "Short Interest, Institutional Ownership, and Stock
Returns", *JFE* 2005
([ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0304405X05001170);
[author PDF](https://site.warrington.ufl.edu/ritter/files/2015/04/Short-interest-institutional-ownership-and-stock-returns-2005-08.pdf)):
constrained stocks underperform by **215 bp/month equal-weighted** but only **39 bp/month
value-weighted, and insignificantly so**, 1988–2002. Their summary is blunt: equally weighted
high-short-interest portfolios underperform; **value-weighted portfolios do not.**

- **Effect size:** 15.6%/yr EW at the extreme decile; ~4.7%/yr VW and not statistically distinguishable
  from zero even in the original sample.
- **Breadth:** decile strategies, so 10% of names on the short side. Effect concentrated in the small
  and constrained tail of that decile — realistically low single-digit % of a large-cap universe.
- **Post-publication decay:** severe. See §3.3. MSCI reports the short-interest factor's return was
  *even more negative* (i.e. the strategy lost more) after December 2020
  ([MSCI](https://www.msci.com/research-and-insights/blog-post/high-short-interest-and-low-quality-hurt-small-caps-performance)).
- **Microcap/illiquid concentration:** yes, overwhelmingly. The EW/VW gap *is* the microcap effect.
- **Borrow cost:** the names with extreme short interest are precisely the names with high borrow.
  See §3.2 — this is where Muravyev et al. eliminate it.
- **Reduces to "short what has fallen"?** Partially. High short interest correlates with past losers,
  and DTC mechanically loads on stocks with falling volume and price. Not identical, but overlapping
  with something we have already falsified five times.
- **ETF-level sign flip:** documented, and it goes *against* us (see §0).

**Verdict: NOT tradeable for us.** Value-weighted evidence is insignificant, the ETF-level sign is
wrong, and the tradeable variant (Cohen-Diether-Malloy shorting demand) needs proprietary loan data
we do not have.

---

### 2.2 Securities lending fee / the shorting premium — the meta-result

This is the single most important paper in this review.

**Muravyev, Pearson & Pollet, "Anomalies and Their Short-Sale Costs", *JF* 2025**
([Wiley](https://onlinelibrary.wiley.com/doi/10.1111/jofi.13501?af=R)). 162 anomalies, July 2006 –
December 2020, using actual borrow-fee data:

| Measure | Before fees | After fees |
|---|---|---|
| Average long-short return | **+0.14%/month** (significant) | **−0.01%/month** (nil) |
| Decile-1 (short leg) abnormal return | **−0.24%/month** | **−0.02%/month** (insignificant) |
| Microcap subset | +0.36%/month | −0.05%/month |
| "Strong"/high-fee anomalies | +0.41%/month | −0.02%/month |

The mechanism: **~12% of stock-dates carry borrow fees above 1%/yr, and those 12% account for the
entire apparent anomaly premium.** Drop the high-fee observations without resorting and the average
long-short return falls to an insignificant +0.05%/month.

This is consistent with, and sharper than, Drechsler & Drechsler, "The Shorting Premium and Asset
Pricing Anomalies" ([SSRN 2387099](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2387099);
[NBER w20282](https://www.nber.org/system/files/working_papers/w20282/w20282.pdf)): **the anomalies
effectively disappear within the 80% of stocks that have low fees**, and survive only among high-fee
stocks.

Borrow-cost base rates, for calibration: D'Avolio, "The Market for Borrowing Stock", *JFE* 2002
([SSRN 305479](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=305479)) — **91% of borrowed stock
is general collateral at ~17 bp/yr**; the other 9% averages **4.30%/yr** with a fat right tail, and
specialness *decreases* with firm size and institutional ownership.

**What this means for us, stated plainly.** We trade 57 liquid US ETFs. Those are the deepest,
cheapest-to-borrow instruments in the market — the extreme opposite of the 12% of stock-dates that
carry the entire published short-side premium. **By construction, our universe sits inside the
subpopulation where the literature says the short-side anomaly does not exist.** This is not a
tradeability caveat; it is a statement that the effect is absent, not merely expensive.

**Verdict: this result does not give us a signal. It removes most of the others.**

---

### 2.3 Net share issuance and buybacks

**Core claim.** Firms that issue shares underperform; firms that retire shares outperform. Primary:
Pontiff & Woodgate, "Share Issuance and Cross-Sectional Returns", *JF* 2008
([Semantic Scholar](https://www.semanticscholar.org/paper/Share-Issuance-and-Cross%E2%80%90sectional-Returns-Pontiff-Woodgate/a49487518f8adde358fc15f79aefc2329b2cc02e));
also Daniel & Titman (2006), Fama & French, "Dissecting Anomalies" (2008)
([PDF](https://www.ivey.uwo.ca/media/3775531/dissecting_anomalies.pdf)); international replication in
McLean, Pontiff & Watanabe, *JFE* 2009
([ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0304405X09001007)).

- **Effect size:** post-1970 US, share issuance predicts the cross-section *more significantly* than
  size, book-to-market, or momentum individually. Decile spreads in the high-single-digit %/yr range.
- **Breadth:** applies to essentially the whole universe (every firm has a share count), which is
  unusual and good — most firms are in the middle, but the ranking is continuous. Annual rebalance.
- **Replication status:** **strong.** Survives Hou/Xue/Zhang's value-weighted NYSE-breakpoint gauntlet;
  it is one of the six MGMT-cluster anomalies in Stambaugh-Yuan. Replicated internationally. This is
  one of the two or three most robust anomalies in the entire literature.
- **Microcap concentration:** less than most. It is one of the survivors of value-weighting.
- **Turnover:** annual. Cost ≈ 2 round trips/yr ≈ **−0.07%/yr** at our 1.85 bp. Effectively free.
- **Reduces to "short what has fallen"?** **No.** Issuance is a corporate-action signal, orthogonal
  to price path. This is a genuine point in its favour.
- **Borrow cost:** issuers skew toward smaller, growthier, more distressed names — i.e. the expensive
  tail. Muravyev et al.'s fee adjustment applies.

**The ETF gap.** There is no ETF whose selection criterion is "companies issuing shares", and no
liquid ETF-level proxy for aggregate issuance in our 57 names. A share-count-weighted signal at the
ETF level would be a fund-flow signal, which is a different (and unstudied for this purpose) thing.

**Verdict: the best stock-level short signal in the literature, and untradeable by us for lack of an
instrument.** If this programme ever moves to single stocks, this is the first thing to build.
Flag as the top candidate *conditional on a universe change*.

---

### 2.4 Accruals (Sloan)

**Core claim.** High-accrual firms underperform. Sloan (1996).

**Post-publication status: dead.** Green, Hand & Soliman, "Going, Going, Gone? The Demise of the
Accruals Anomaly", *Management Science* 2011
([SSRN 1501020](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1501020)) — hedge returns "have
decayed in U.S. markets to the point that they are no longer positive." Richardson, Tuna & Wysocki
(2010) independently date the attenuation to **2003–2004**. Attributed to hedge-fund arbitrage.

- **Effect size now:** ~zero in the US.
- **Where the short leg came from:** small, high-accrual, low-institutional-ownership names.
- **Verdict: NOT tradeable. Decayed to nothing, and never had an ETF analogue.** Include in a
  composite (§2.7) only, and even there it now contributes noise.

---

### 2.5 Asset growth / investment (Cooper, Gulen & Schill)

**Core claim.** Top-decile asset growth underperforms bottom decile by **~13%/yr value-weighted**,
US 1968–2003 ([SSRN 1335524](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1335524);
international evidence: [Watanabe et al., *JFE* 2013](https://www.sciencedirect.com/science/article/abs/pii/S0304405X12002486)).

- **Effect size:** 13%/yr in-sample, decile spread; substantially lower post-2003.
- **Breadth:** whole universe, annual rebalance. Cost ≈ free.
- **Replication:** survives as an MGMT-cluster member in Stambaugh-Yuan and in the q-factor literature
  (it *is* the investment factor). Genuinely replicated — but note that once it became a standard
  factor (Fama-French five-factor CMA, HXZ I/A), the "anomaly" framing became a "factor" framing and
  the premium has compressed.
- **Microcap concentration:** the original result is value-weighted, so less microcap-driven than
  accruals. But O'Donovan and others document decay
  ([Understanding the Asset Growth Anomaly](https://www.ivey.uwo.ca/media/3797068/understanding-the-asset-growth-anomaly.pdf)).
- **Reduces to "short what has fallen"?** No — it is a balance-sheet signal.
- **ETF gap:** same problem. No liquid ETF sorts on asset growth. There are "quality" and "profitability"
  ETFs whose *long* side loads on low investment, but no short instrument.

**Verdict: robust at stock level, no ETF instrument, so NOT tradeable for us.**

---

### 2.6 Financial distress, O-score, Z-score

**Core claim.** Campbell, Hilscher & Szilagyi, "In Search of Distress Risk", *JF* 2008
([Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2008.01416.x);
[NBER w12362](https://www.nber.org/system/files/working_papers/w12362/w12362.pdf)) — high
failure-probability stocks earn **anomalously low returns since 1981** despite higher volatility,
higher beta, and higher value/size loadings. The "distress puzzle".

**This is the candidate this programme should reject fastest, and here is why.**

Look at the CHS failure-probability inputs: higher leverage, lower profitability, **lower market
capitalization, lower past stock returns, more volatile past returns**, lower cash, **lower price per
share**. Two of the strongest inputs are *past return* and *past volatility*. **The distress score is,
to a substantial degree, a laundered momentum-and-drawdown signal.** Shorting high-distress names is
shorting what has fallen, wearing accounting clothes. We have falsified that five times on this
universe, most recently measuring the most-beaten-down quintile at **+16.83%**.

This is not just my inference. Avramov, Chordia, Jostova & Philipov, "Anomalies and Financial
Distress", *JFE* 2013
([ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0304405X12002176);
[SSRN 1593728](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1593728)) show that price
momentum, earnings momentum, credit risk, dispersion, idiosyncratic volatility and capital
investment strategies **all derive their profitability from short positions in high-credit-risk firms
around rating downgrades.** They are, collectively, one trade: short small distressed falling stocks
in the weeks around a downgrade.

- **Effect size:** large in the raw data, entirely concentrated in a tiny, transient, junk-rated,
  hard-to-borrow subpopulation around a corporate event.
- **Breadth:** very small. Downgraded, high-credit-risk firms are a low-single-digit % of names, for a
  window of weeks. `exposure × edge` is small even before costs.
- **Microcap/illiquid:** yes, extremely.
- **Borrow cost:** highest in the market. This is the 9% special tail from D'Avolio and the 12%
  high-fee tail from Muravyev.
- **Reduces to "short what has fallen"?** **YES. Flag hard.**

**Verdict: NOT tradeable, and specifically already falsified in spirit by five of our own
measurements.** Do not spend another study on this family.

---

### 2.7 Composite mispricing scores (Stambaugh, Yu & Yuan)

**Core claims.**

- Stambaugh, Yu & Yuan, "The Short of It: Investor Sentiment and Anomalies", *JFE* 2012
  ([ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0304405X11002649);
  [SSRN 1567616](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1567616);
  [NBER w16898](https://www.nber.org/papers/w16898)). Three findings, verbatim in structure:
  (i) each anomaly is stronger following high sentiment; (ii) **the short leg of each strategy is
  more profitable following high sentiment**; (iii) **sentiment has no relation to the long legs.**
  Interpretation: short-sale impediments mean overpricing persists but underpricing does not, so
  mispricing lives on the short side.
- Stambaugh & Yuan, "Mispricing Factors", *RFS* 2017
  ([Oxford](https://academic.oup.com/rfs/article/30/4/1270/2965095);
  [SSRN 2626701](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2626701);
  [NBER w21533](https://www.nber.org/papers/w21533)). 11 anomalies averaged into two clusters:
  - **MGMT** (management-controlled): net stock issues, composite equity issues, accruals, net
    operating assets, asset growth, investment-to-assets.
  - **PERF** (performance): distress, O-score, momentum, gross profitability, return on assets.

**The most useful thing in this paper for us is the MGMT/PERF split, because it separates the two
families cleanly along our constraint 4.**

| Cluster | Contents | Reduces to "short what has fallen"? |
|---|---|---|
| MGMT | issuance, accruals, NOA, asset growth, investment | **No.** Balance-sheet / corporate action. Orthogonal to price path. |
| PERF | distress, O-score, momentum, gross profitability, ROA | **Yes, largely.** Distress and O-score load on past return and past volatility; momentum is literally past return. |

So the correct reading of the composite for this programme is: **the composite's short side is ~half a
signal we have already falsified here (PERF) and ~half a signal we have no instrument for (MGMT).**
Averaging them does not fix either problem.

- **Effect size:** the composite improves on individual anomalies and produces a better-performing
  factor model; the short-leg-concentration result is the durable contribution.
- **Breadth:** the sentiment conditioning is a *time-series* selectivity threshold. Baker-Wurgler
  sentiment is high roughly half the time by construction. So conditioning on high sentiment roughly
  halves exposure to roughly double the edge — **exactly the `gross = exposure × edge` identity in
  constraint 3. It cannot create gross return.** It can improve Sharpe if the low-sentiment periods
  are pure noise rather than pure loss, but it cannot raise gross.
- **Robustness caveat, and it is a serious one:** the sentiment-conditional result has been directly
  challenged. See "Odds that Investor Sentiment Spuriously Predicts Anomaly Returns"
  ([NBER w18231](https://www.nber.org/system/files/working_papers/w18231/w18231.pdf)) — the concern is
  that with a slow-moving, persistent conditioning variable and a handful of sentiment cycles in the
  sample, the effective number of independent observations is very small. This is the same
  low-effective-N problem our constraint 5 describes. **Treat the sentiment conditioning as one paper,
  not as replicated.**
- **Borrow cost:** applies. Muravyev et al.'s 162 anomalies include these.

**Verdict: the short-leg-concentration finding is the correct prior to hold (short-side alpha exists
in principle because shorting is constrained), but the composite is not implementable here.** Its
main value to us is diagnostic: use MGMT/PERF as a *classifier* for whether a future candidate is
price-path-derived or not.

---

### 2.8 Failures-to-deliver, hard-to-borrow, squeeze risk

- Evans, Geczy, Musto & Reed, "Failure Is an Option: Impediments to Short Selling and Options Prices",
  *RFS* 2009 — market makers choose to fail when borrow is expensive; **stocks with FTDs show negative
  abnormal returns proportional to FTD levels.** Pre-Reg-SHO data.
- Post-Reg-SHO (Rule 203/204, 2008–09), FTD levels collapsed
  ([Jain et al., *Financial Review* 2015](https://onlinelibrary.wiley.com/doi/10.1111/fire.12093)),
  so the *sample the effect was measured in no longer exists*.
- Informed short selling and FTDs
  ([ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S092753981630055X)).

**Breadth:** FTDs and threshold-list membership are a fraction of a percent of name-days, and by
construction they select the most expensive-to-borrow, most squeeze-prone names.

**Squeeze risk is not a footnote, it is the dominant term.** January 2021: GME $17 → $483 in under a
month; short sellers lost **>$6bn** year-over-year; Melvin Capital went from $12.5bn to $8bn AUM in a
single month. The relevant point for a systematic short book is that this is a **negatively skewed,
fat-left-tailed** payoff whose worst realisations are correlated *across the whole short book*
simultaneously — which annihilates the breadth assumption in any Sharpe calculation.

**Verdict: NOT tradeable. Near-zero breadth, maximal borrow cost, maximal tail risk, and the
measurement regime is gone.** Also note this reduces to "short what has fallen" in most instances.

---

### 2.9 ETF-level: specialized / thematic ETFs — **the one real candidate**

**Ben-David, Franzoni, Kim & Moussawi, "Competition for Attention in the ETF Space", *RFS* 36(3),
2023** ([Oxford](https://academic.oup.com/rfs/article-abstract/36/3/987/6655702);
[SSRN 3765063](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3765063);
[NBER w28369](https://www.nber.org/system/files/working_papers/w28369/w28369.pdf)). Sample 1993–2019.

- **Effect size: −3%/yr risk-adjusted alpha on average; ~−6%/yr immediately post-launch; persists at
  least 5 years; cumulative ~−30% risk-adjusted over the first 5 years.**
- **Mechanism:** issuers launch specialized ETFs *after* the underlying stocks have already run up and
  attracted attention. The funds hold attention-grabbing, overvalued stocks. Explicitly **not**
  explained by fees or hedging demand — it is overvaluation of the holdings at launch.
- **Breadth:** this is the binding constraint for us. Of 57 liquid US ETFs, the number that qualify as
  "specialized/thematic and recently launched" is small — plausibly 0–5, and by definition the
  most-liquid 57 skews toward broad and sector funds, which are the *control* group in this paper, not
  the treatment group. If 3 of 57 qualify at ~5% of book, `exposure × edge` ≈ 0.05 × 3% ≈ **0.15%/yr**
  on total capital. If you are willing to run the sleeve at 25% of book, ≈ **0.75%/yr**.
- **Turnover: very low.** Launch-date-triggered, hold for years. Cost is negligible: 2 round trips
  over 5 years ≈ −0.007%/yr. **This is the only candidate in the document that trivially passes
  constraint 2.**
- **Drift:** must be run dollar-neutral against a broad-market ETF, or the 8.59%/yr overnight drift
  eats twice the alpha. Dollar-neutral, drift cancels and the −3% is the clean read.
- **Borrow cost:** liquid ETFs are general collateral or close to it. Some thematic ETFs get special,
  but nothing like the distressed-microcap tail. This passes the Muravyev filter — but note the paper
  does *not* report net-of-borrow returns, so this is my inference, not their finding.
- **Reduces to "short what has fallen"?** **No — it is the opposite.** It is "short what has recently
  risen and attracted attention". Given that our universe's measured behaviour is hard mean reversion
  (beaten-down names bounce +16.83%), a short-the-recent-winner signal is *aligned* with the measured
  dynamics rather than fighting them. This is a genuine and non-obvious point in its favour.
- **Replication status:** one paper, but a top-3 journal, large sample, and the mechanism (issuers
  time launches to hot themes) is independently visible in industry data
  ([practitioner summary](https://retirementincomejournal.com/article/beware-the-specialized-etfs-research-roundup/)).
  It has not, to my knowledge, been independently replicated on a post-2019 sample. **Treat as one
  strong paper, not as replicated.**
- **Biggest failure mode for us:** breadth. Also, the 2020–2021 thematic launch wave is now in-sample
  for everyone, and the effect is well publicised — McLean-Pontiff decay (§3.3) should be assumed.

**Verdict: TRADEABLE IN PRINCIPLE, and the top candidate. Constrained entirely by how many
qualifying names exist in our 57.** Recommend the first action is simply to count them.

---

### 2.10 ETF-level: NAV premium/discount mean reversion

**Petajisto, "Inefficiencies in the Pricing of Exchange-Traded Funds", *FAJ* 2017**
([SSRN 2000336](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2000336);
[author PDF](http://www.petajisto.net/papers/etf26.pdf);
[CFA summary](https://rpc.cfainstitute.org/research/financial-analysts-journal/2017/detecting-etf-mispricing)).

- Average ETF price–NAV deviation ≈ **6 bp**, volatility of the deviation ≈ **49 bp**; typical
  mispricing band ~200 bp raw, ~100 bp after controlling for stale pricing.
- Trading strategy Carhart alpha: **14.36%/yr excluding diversified US equities and Treasuries;
  26.12%/yr also excluding sector funds.** Before transaction costs.

**Read those exclusions again.** The alpha is *defined by removing* diversified US equity, Treasuries,
and sector funds — which is a near-exact description of our 57 liquid US ETFs. The residual is
international and illiquid funds. Petajisto is telling us the effect is not in our universe.

- **Turnover:** deviations converge within ~2 days. This is a **daily-to-two-day** strategy. At 1.85
  bp/side, one round trip/day = **−8.90%/yr**; even every second day is **−4.45%/yr**. On a 6 bp
  average edge with 49 bp noise, the cost term dominates by an order of magnitude in the liquid names
  where the deviation is smallest.
- **Breadth:** the deviations that matter are in the funds with the worst arbitrage — i.e. the ones we
  do not hold.

**Verdict: NOT tradeable. Fails on universe (explicitly excluded) and on turnover (explicitly
daily).** Two independent kills.

---

### 2.11 ETF-level: volatility ETPs and roll yield

**Core claim.** A constant-maturity 1-month VIX futures position loses roughly **30%/yr** (2006–2013);
VXX and VXZ lost an average of **34 bp and 14 bp per day** respectively since their Jan-2009 launch.
Explained as a variance risk premium in equilibrium
([Eraker & Wu, *JFE* 2017](https://www.sciencedirect.com/science/article/abs/pii/S0304405X17300764);
[Gehricke & Zhang, *JFM* 2018](https://onlinelibrary.wiley.com/doi/10.1002/fut.21913);
[Husson & McCann, SLCG](https://www.slcg.com/files/research-papers/VXX%206-16-11.pdf)).

- **Effect size: the largest in this document by an order of magnitude.** −30%/yr.
- **Breadth: one.** Possibly two or three names if VXX/UVXY/VIXY are in the 57. `exposure × edge` at
  1/57 of book ≈ 0.5%/yr; at a 10% sleeve ≈ 3%/yr.
- **Turnover:** low. Hold short, roll occasionally. Passes constraint 2 easily.
- **Drift:** it is a naked short of an asset with hugely *negative* drift, so the 8.59%/yr headwind is
  irrelevant here — the instrument's own drift is −30%.
- **Reduces to "short what has fallen"?** No. It is a term-structure/carry trade.
- **Why it might kill you:** this is a short-variance carry trade with a catastrophic left tail. On
  5 Feb 2018 the inverse VIX ETN XIV lost ~96% in a day and was terminated. The −30%/yr is
  compensation for exactly that. It is also the most crowded trade of its type in existence. It is a
  **risk premium, not an anomaly**, and it will not diversify against an equity book — the tail is
  perfectly correlated with equity crashes.
- **Contango is regime-dependent:** the roll yield is negative in contango (low-vol regimes) and
  *positive* in backwardation. So the edge is conditional on a regime that is itself the thing that
  blows up.

**Verdict: real, huge, and honestly categorised as selling insurance rather than as short-side
alpha.** Tradeable, but it belongs in a separate risk bucket with explicit tail sizing, not in a
cross-sectional short book. Worth pursuing only with a pre-registered stop and position cap.

---

### 2.12 ETF-level: leveraged ETF decay

**Core claim.** Daily-rebalanced leveraged ETFs suffer volatility drag and underperform their target
multiple over long horizons.

**This is largely a folk theorem and the recent literature does not support the naive version.**
[Compounding Effects in Leveraged ETFs: Beyond the Volatility Drag Paradigm (arXiv 2504.20116)](https://arxiv.org/abs/2504.20116)
finds that with i.i.d. returns, LETFs show **positive** expected compounding effects on their target
multiple; underperformance requires **mean-reverting** underlying returns, and trending markets
*enhance* LETF returns. See also
[Beyond Volatility Decay (MDPI, JRFM 2026)](https://www.mdpi.com/1911-8074/19/1/20), which finds
standard provider methodology understates bullish LETF expected returns and overstates bearish ones.

- **Relevance to us, and it cuts both ways.** Our universe mean-reverts hard — which is exactly the
  condition under which LETF decay *is* real. So the mechanism is present here.
- **But:** the classic "short both the 3x long and the 3x inverse" trade is a short-gamma position.
  It collects decay in choppy markets and loses badly in trends, and it requires rebalancing to stay
  dollar-neutral (turnover → cost). Borrow on leveraged ETFs is frequently expensive and recall-prone.
- **Breadth:** a handful of pairs at most, and probably zero in a "57 liquid US ETFs" set that is
  likely to exclude 3x products.

**Verdict: mechanism is real given our measured mean reversion, but the trade is short-gamma with
recall risk and near-zero breadth. Low priority.**

---

### 2.13 Aggregate short interest as a market-timing signal

Rapach, Ringgenberg & Zhou, "Short Interest and Aggregate Stock Returns", *JFE* 2016
([SSRN 2474930](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2474930);
[RePEc](https://econpapers.repec.org/RePEc:eee:jfinec:v:121:y:2016:i:1:p:46-65)). Aggregate short
interest is "arguably the strongest known predictor of aggregate stock returns": **annual R² of 12.89%
in-sample and 13.24% out-of-sample**, utility gains **>300 bp/yr** for a mean-variance investor.

This is genuinely interesting *because it is a time-series signal on the index*, which is exactly the
kind of thing an ETF book can express. But:

- **The 2008 dependence is fatal to the claim.** Subsequent work reports that the entire result
  disappears if the 2008 calendar year is excluded. A predictor whose R² is carried by one crisis year
  has an effective sample size of approximately one.
- International evidence is mixed
  ([RAPS 2023](https://academic.oup.com/raps/article-pdf/13/4/691/53403664/raad007.pdf)).
- **Constraint 3 applied:** a market-timing signal that is "out of the market" some fraction of the
  time is a pure exposure reduction. It cannot create gross return; it can only improve risk-adjusted
  return if the avoided periods are genuinely negative.
- **Constraint 1 applied:** timing the *market* means fighting +8.59%/yr overnight drift whenever you
  are short or flat. The bar is very high.

**Verdict: NOT tradeable on this evidence. One paper, one crisis year. Revisit only if someone
publishes a clean post-2010 out-of-sample test.**

---

### 2.14 Meta-signal worth flagging: the overnight/intraday decomposition

Lou, Polk & Skouras, "A Tug of War: Overnight versus Intraday Expected Returns", *JFE* 134(1), 2019
([LSE PDF](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf);
[ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0304405X19300650)).

Across **14 trading strategies, profits are earned either entirely overnight or entirely intraday,
typically with opposite signs across the two components.** Momentum profits are overwhelmingly
overnight; reversal profits are intraday.

**This is directly relevant to constraint 1 and this programme should treat it as an important
methodological result rather than a signal.** It says that any candidate short signal must be
decomposed into its overnight and intraday components *before* judging it, because the aggregate
close-to-close number can be the net of two opposite-signed effects. Given that our own measurement
finds +8.59%/yr overnight and −0.36%/yr intraday, a signal whose alpha is intraday-only would sidestep
the drift headwind entirely — and the tug-of-war paper says such signals exist and are common.

**Verdict: not a candidate, but the correct lens through which to evaluate every candidate.** Any
future short study here should report the overnight/intraday split as standard.

---

## 3. Cross-cutting reasons most of the above fails

### 3.1 Microcap concentration

Hou, Xue & Zhang, "Replicating Anomalies", *RFS* 33(5), 2020
([Oxford](https://academic.oup.com/rfs/article-abstract/33/5/2019/5236964);
[NBER w23394](https://www.nber.org/system/files/working_papers/w23394/w23394.pdf);
[author PDF](https://global-q.org/uploads/1/2/2/6/122679606/houxuezhang2020rfs.pdf)). 447–452 anomalies:

- With microcaps mitigated (NYSE breakpoints + value-weighted returns), **65% cannot clear |t| > 1.96**.
- **96% of the trading-frictions category fails.**
- At a multiple-testing hurdle of |t| > 2.78, **82% fail.**

Microcaps are ~3% of total market cap but ~60% of the *number* of listed names. Equal-weighted
anomaly research is, structurally, research about 3% of the market's capital.

Chen & Welch, "What Useful Alphas?" ([arXiv 2607.06502](https://arxiv.org/pdf/2607.06502)) put a
number on the large-cap version: median anomaly ≈ **48 bp/month through 2005**, falling to
**≈7 bp/month in the top 90% of market cap after 2005** (median CAPM alpha ≈ 9 bp/month) — roughly an
**85% decline**. 7 bp/month is 0.84%/yr gross, before costs and before borrow.

### 3.2 Borrow cost eliminates the short leg (see §2.2)

Restated because it is the single most important number in this review: **the fee-adjusted decile-1
abnormal return across 162 anomalies is −0.02%/month and insignificant.** The premium lives in the
12% of stock-dates with fees above 1%/yr.

### 3.3 Post-publication decay

McLean & Pontiff, "Does Academic Research Destroy Stock Return Predictability?", *JF* 2016
([Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12365);
[SSRN 2156623](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2156623)). 97 predictors:

- **−26% out-of-sample** (pre-publication, post-sample) — the data-mining upper bound.
- **−58% post-publication.**
- The difference, **−32%**, is attributed to publication-informed arbitrage.

Every effect size quoted above should be haircut by ~58% before use, and the papers here are 10–25
years old.

Counterweight, for fairness: Chen & Zimmermann, "Open Source Cross-Sectional Asset Pricing",
*Critical Finance Review* 11(2), 2022
([SSRN 3604626](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3604626);
[openassetpricing.com](https://www.openassetpricing.com/)) reproduce **98% of 161 clearly-significant
predictors at |t| > 1.96**, with a reproduced-on-original t-stat slope of 0.88 and R² of 82%. The
findings are real; they are just small, decaying, and located in places we cannot trade. "Replicable"
and "tradeable" are different claims and the literature conflates them constantly.

### 3.4 The stock → ETF gap

This deserves to be stated as its own constraint. **Every anomaly in §2.1–§2.8 is defined on
firm-level characteristics (short interest, share count, accruals, asset growth, failure probability).
An ETF has none of these in a tradeable sense.** You cannot short "high accrual firms" with SPY, XLK
and IWM. The only ways to bridge the gap are:

1. Aggregate the characteristic to the ETF level (cap-weighted average accruals of XLK's holdings).
   This destroys nearly all the dispersion — the cross-sectional spread across 57 diversified
   portfolios is a fraction of the spread across 3,000 stocks, because averaging is exactly what
   diversification does. This interacts brutally with constraint 5: our effective breadth already
   saturates at 2.2, and characteristic-averaging pushes the cross-sectional signal dispersion toward
   zero at the same time.
2. Find ETFs whose *selection rule* is the anomaly. These exist on the long side (quality,
   profitability, buyback ETFs) but there is no liquid "short the issuers" ETF.

Zaremba, Umutlu & Maydybura, "Where have the profits gone?", *JBF* 121, 2020
([ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0378426620302284);
[SSRN 3762979](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3762979)) is the closest direct
test: they run anomalies on **64 country and 793 industry indices, 1973–2018** — i.e. on
index-level instruments, which is what we trade. They find **structural breaks and significantly
decreased profitability**, driven particularly by the disappearance of value and reversal effects,
and attribute it to improved market efficiency. **This is the paper most directly about our problem,
and its answer is negative.**

### 3.5 Breadth

Our effective breadth is ~2.2 on 57 names. The fundamental law implies IR ≈ IC × √breadth. At
breadth 2.2, an IC of 0.05 gives IR ≈ 0.074. To reach IR = 0.5 at breadth 2.2 requires IC ≈ 0.34,
which is far outside anything in this literature. **No cross-sectional signal in this document has a
plausible IC large enough to produce a usable IR at breadth 2.2.** This is arguably a more binding
constraint than any of the anomaly-specific objections, and it applies to *any* cross-sectional
approach on this universe, not just short-side ones.

---

## 4. Ranking by expected `exposure × edge`, net of costs and borrow

Assumptions: dollar-neutral (so the 8.59%/yr drift cancels), 1.85 bp/side, returns quoted on **total
capital**, not on the sleeve. Effect sizes haircut 58% per McLean-Pontiff where the anomaly is
published and old; specialized-ETF haircut 40% (published 2023, less time to decay).

| Rank | Candidate | Raw edge | Haircut edge | Plausible exposure | Turnover cost | **Net exposure × edge** | Killer |
|---|---|---|---|---|---|---|---|
| 1 | **Specialized/thematic ETF underperformance** | −3%/yr (−6% yr 1) | ~1.8%/yr | 5–25% of book (0–5 names) | ~0 | **+0.09% to +0.45%/yr** | Breadth: may be 0 qualifying names in our 57 |
| 2 | **Volatility ETP roll yield** | −30%/yr | ~30%/yr (risk premium, does not decay) | 2–10% of book, 1 name | ~0 | **+0.6% to +3%/yr** | Catastrophic left tail, perfectly correlated with equity crashes; XIV lost 96% in one day |
| 3 | **Net share issuance** (if universe ever changes) | ~8%/yr decile spread | ~3.4%/yr | 10% short leg | −0.07%/yr | **~+0.34%/yr on stocks** | No ETF instrument exists. Zero for us today. |
| 4 | Leveraged ETF decay pair | regime-dependent | unquantified | <5% | moderate | **<0.1%/yr** | Short gamma; borrow recall; likely 0 names in universe |
| 5 | Asset growth / investment | 13%/yr decile | ~5.5%/yr | 10% short leg | −0.07%/yr | **0 for us** | No ETF instrument; now a standard factor |
| 6 | Composite mispricing (MGMT half) | modest | modest | half the composite | low | **0 for us** | No ETF instrument; PERF half is already-falsified |
| 7 | ETF NAV mispricing | 14–26%/yr | n/a | ~0 in our names | **−4.5 to −8.9%/yr** | **strongly negative** | Explicitly excludes our universe; daily turnover |
| 8 | Short interest / days-to-cover | 15.6%/yr EW | ~4.7%/yr VW, insignificant | 10% | −0.44%/yr | **~0, sign uncertain** | VW insignificant; **ETF-level sign flips positive** |
| 9 | Aggregate short interest timing | R² 13% | unknown | timing only | low | **cannot create gross** | Entire result is 2008 |
| 10 | Distress / O-score / Z-score | large raw | ~0 | ~1–3% of names | high | **negative** | **Is "short what has fallen". Already falsified 5×.** |
| 11 | Accruals | historically large | **0** | 10% | low | **0** | Dead since 2003–04 |
| 12 | FTDs / hard-to-borrow / squeeze | large raw | unknown | <0.5% | extreme borrow | **negative** | Reg SHO removed the regime; tail risk |

### The two I would actually pursue

**1. Specialized / thematic ETF underperformance (Ben-David, Franzoni, Kim & Moussawi, RFS 2023).**

It is the only candidate that passes every one of our five constraints simultaneously:
drift-cancelling if run dollar-neutral; near-zero turnover so the cost constraint is irrelevant;
*aligned* with our measured mean reversion rather than fighting it (it shorts what has risen, not what
has fallen); cheap to borrow because the instruments are liquid ETFs; and defined at the ETF level so
there is no stock→ETF translation loss.

Its only weakness is breadth, and breadth is exactly what constraint 3 says determines gross return.
**The correct first step is not a backtest — it is a count.** Enumerate how many of the 57 are
narrow/thematic/recently-launched by the paper's own definition. If the answer is 0 or 1, the study is
over before it starts and we have saved ourselves the work. If it is 4–6, there is a real 0.3–0.5%/yr
sleeve to pre-register.

**2. Volatility ETP roll yield — but reclassified honestly.**

This has by far the largest measured effect and it is not decaying, because it is compensation for
bearing a real risk rather than a mispricing. But it should not go in a cross-sectional short book.
It is a single-name insurance sale whose worst outcome is simultaneous with the worst outcome of every
other equity position. Pursue it as a separately-sized, separately-stopped sleeve with a pre-registered
maximum loss, or not at all.

**Third, conditionally: net share issuance — as a trigger for a universe decision, not as a study.**
It is the most robust short-side signal in the literature (survives Hou-Xue-Zhang value-weighting, is
one of the six MGMT anomalies, replicates internationally, and does *not* reduce to "short what has
fallen"). We cannot trade it. If this programme ever considers extending beyond 57 ETFs to single
names, this is the signal that justifies the extension — and the honest framing is that the
instrument constraint, not the signal quality, is what is binding.

### What I would not spend another study on

Anything in the PERF cluster — distress, O-score, Z-score, momentum-continuation shorts, idiosyncratic
volatility shorts. Avramov et al. (2013) show these are all one trade: short small, falling,
high-credit-risk names around downgrades. That is "short what has fallen" in accounting notation, and
this programme has falsified it five times on this universe. The literature agrees with our own
measurements here; there is no tension to resolve.

---

## 5. Standing caveats on this document

- **What is replicated vs one paper.** Replicated and robust: net share issuance, asset growth,
  short-leg concentration of anomaly returns, microcap concentration (HXZ), post-publication decay
  (McLean-Pontiff), borrow-cost elimination (Muravyev/Drechsler agree). **One paper each, treat with
  caution:** the specialized-ETF result, the sentiment-conditioning result (and it has a published
  spurious-regression challenge), the aggregate-short-interest timing result (and it hinges on 2008),
  the LETF compounding results. **Definitively dead:** accruals.
- I could not extract exact table values from several PDFs (SYY 2012, Stambaugh-Yuan 2017,
  Asquith-Pathak-Ritter, Petajisto) because the fetch tool returned raw PDF streams. Numbers attributed
  to those papers above come from abstracts, publisher summaries, and secondary citations, and the
  ones that matter most to the ranking (the APR 215 bp EW / 39 bp VW split, the Petajisto 14.36% /
  26.12% exclusion-conditional alphas) should be verified against the source tables before anything is
  pre-registered on them.
- **Every effect size in §2 is gross.** None of the stock-level papers report returns net of both
  transaction costs and borrow fees except Muravyev/Pearson/Pollet and Novy-Marx/Velikov — and both of
  those report approximately zero.
- Novy-Marx & Velikov, "A Taxonomy of Anomalies and Their Trading Costs", *RFS* 29(1), 2016
  ([NBER w20721](https://www.nber.org/system/files/working_papers/w20721/w20721.pdf);
  [SSRN 2535173](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2535173)) adds the general
  turnover rule: **anomalies with one-sided monthly turnover under 50% mostly survive costs; few above
  that do.** Our 1.85 bp/side is far better than their universe's 20–57 bp, so the turnover bar is
  looser for us — but the rule's direction is the same, and it is why the two survivors in §4 are both
  near-zero-turnover strategies.

---

## Sources

- [Boehmer, Jones & Zhang — Which Shorts Are Informed? (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=855044)
- [Boehmer, Huszár & Jordan — The Good News in Short Interest (JFE 2010)](https://www.sciencedirect.com/science/article/abs/pii/S0304405X09002402)
- [Asquith, Pathak & Ritter — Short Interest, Institutional Ownership, and Stock Returns (JFE 2005)](https://www.sciencedirect.com/science/article/abs/pii/S0304405X05001170)
- [Cohen, Diether & Malloy — Supply and Demand Shifts in the Shorting Market (JF 2007)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=672381)
- [Hong, Li, Ni, Scheinkman & Yan — Days to Cover and Stock Returns](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2568768)
- [Muravyev, Pearson & Pollet — Anomalies and Their Short-Sale Costs (JF 2025)](https://onlinelibrary.wiley.com/doi/10.1111/jofi.13501?af=R)
- [Drechsler & Drechsler — The Shorting Premium and Asset Pricing Anomalies (NBER w20282)](https://www.nber.org/system/files/working_papers/w20282/w20282.pdf)
- [D'Avolio — The Market for Borrowing Stock (JFE 2002)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=305479)
- [Pontiff & Woodgate — Share Issuance and Cross-Sectional Returns (JF 2008)](https://www.semanticscholar.org/paper/Share-Issuance-and-Cross%E2%80%90sectional-Returns-Pontiff-Woodgate/a49487518f8adde358fc15f79aefc2329b2cc02e)
- [McLean, Pontiff & Watanabe — Share Issuance: International Evidence (JFE 2009)](https://www.sciencedirect.com/science/article/abs/pii/S0304405X09001007)
- [Fama & French — Dissecting Anomalies](https://www.ivey.uwo.ca/media/3775531/dissecting_anomalies.pdf)
- [Green, Hand & Soliman — Going, Going, Gone? The Demise of the Accruals Anomaly](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1501020)
- [Cooper, Gulen & Schill — The Asset Growth Effect in Stock Returns](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1335524)
- [Watanabe et al. — The Asset Growth Effect: International Equity Markets (JFE 2013)](https://www.sciencedirect.com/science/article/abs/pii/S0304405X12002486)
- [Campbell, Hilscher & Szilagyi — In Search of Distress Risk (JF 2008)](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2008.01416.x)
- [Avramov, Chordia, Jostova & Philipov — Anomalies and Financial Distress (JFE 2013)](https://www.sciencedirect.com/science/article/abs/pii/S0304405X12002176)
- [Stambaugh, Yu & Yuan — The Short of It: Investor Sentiment and Anomalies (JFE 2012)](https://www.sciencedirect.com/science/article/abs/pii/S0304405X11002649)
- [Stambaugh & Yuan — Mispricing Factors (RFS 2017)](https://academic.oup.com/rfs/article/30/4/1270/2965095)
- [Odds that Investor Sentiment Spuriously Predicts Anomaly Returns (NBER w18231)](https://www.nber.org/system/files/working_papers/w18231/w18231.pdf)
- [Evans, Geczy, Musto & Reed — Failure Is an Option (SEC copy)](https://www.sec.gov/comments/4-520/4520-6.pdf)
- [Jain et al. — Fails-to-Deliver before and after Rules 203 and 204 (Financial Review 2015)](https://onlinelibrary.wiley.com/doi/10.1111/fire.12093)
- [Ben-David, Franzoni, Kim & Moussawi — Competition for Attention in the ETF Space (RFS 2023)](https://academic.oup.com/rfs/article-abstract/36/3/987/6655702)
- [Ben-David et al. — NBER w28369 (working paper version)](https://www.nber.org/system/files/working_papers/w28369/w28369.pdf)
- [Petajisto — Inefficiencies in the Pricing of Exchange-Traded Funds (FAJ 2017)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2000336)
- [Evans, Moussawi, Pagano & Sedunov — ETF Short Interest and Failures-to-Deliver](https://jacobslevycenter.wharton.upenn.edu/wp-content/uploads/2018/08/ETF-Short-Interest-and-Failures-to-Deliver.pdf)
- [Chichernea et al. — Short Selling ETFs and Market Performance (JFR)](https://onlinelibrary.wiley.com/doi/10.1111/jfir.70050?af=R)
- [Eraker & Wu — Explaining the Negative Returns to Volatility Claims (JFE 2017)](https://www.sciencedirect.com/science/article/abs/pii/S0304405X17300764)
- [Gehricke & Zhang — Modeling VXX (J. Futures Markets 2018)](https://onlinelibrary.wiley.com/doi/10.1002/fut.21913)
- [Husson & McCann — The VXX ETN and Volatility Exposure (SLCG)](https://www.slcg.com/files/research-papers/VXX%206-16-11.pdf)
- [Compounding Effects in Leveraged ETFs: Beyond the Volatility Drag Paradigm (arXiv 2504.20116)](https://arxiv.org/abs/2504.20116)
- [Beyond Volatility Decay (JRFM 2026)](https://www.mdpi.com/1911-8074/19/1/20)
- [Rapach, Ringgenberg & Zhou — Short Interest and Aggregate Stock Returns (JFE 2016)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2474930)
- [Lou, Polk & Skouras — A Tug of War: Overnight vs Intraday Expected Returns (JFE 2019)](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf)
- [Hou, Xue & Zhang — Replicating Anomalies (RFS 2020)](https://global-q.org/uploads/1/2/2/6/122679606/houxuezhang2020rfs.pdf)
- [McLean & Pontiff — Does Academic Research Destroy Stock Return Predictability? (JF 2016)](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12365)
- [Chen & Zimmermann — Open Source Cross-Sectional Asset Pricing (CFR 2022)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3604626)
- [Chen & Welch — What Useful Alphas? (arXiv 2607.06502)](https://arxiv.org/pdf/2607.06502)
- [Novy-Marx & Velikov — A Taxonomy of Anomalies and Their Trading Costs (RFS 2016)](https://www.nber.org/system/files/working_papers/w20721/w20721.pdf)
- [Zaremba, Umutlu & Maydybura — Where Have the Profits Gone? (JBF 2020)](https://www.sciencedirect.com/science/article/abs/pii/S0378426620302284)
- [MSCI — High Short Interest and Low Quality Hurt Small Caps' Performance](https://www.msci.com/research-and-insights/blog-post/high-short-interest-and-low-quality-hurt-small-caps-performance)
