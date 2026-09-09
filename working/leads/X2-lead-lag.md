# X2 — lead–lag between size cohorts: external evidence

*External literature review. RESEARCH ONLY — nothing here was computed, backtested
or verified against our fixtures. Every number below is somebody else's, on
somebody else's universe, and is tagged as such.*

Date of review: 2026-09-09.

---

## 1. Verdict

**The programme's dismissal is CORRECT, and the published literature says so in the
programme's own language.** The decisive source is peer-reviewed and recent:
Parsons, Sabbatucci & Titman (*RFS* 2020) sort the industry lead–lag effect by the
lagging firm's analyst coverage on US data 1970–2013 and find the response of a
firm's next-month return to a 100 bp lagged own-industry return falls **28 bp
(0 analysts) → 24 bp (1–4) → 14 bp (5–9) → 10 bp (10+)** — 70% weaker in the
covered names — and they state explicitly that *"alternative sorts on firm size and
trading volume give virtually identical patterns."* The same paper's one-line
summary of the whole literature is that industry lead–lag effects "are strongest
among small, thinly traded stocks with low analyst coverage". The microstructure
work is worse still for us: the canonical daily large→small lead–lag (Chordia,
Sarkar & Subrahmanyam, NY Fed SR 303) is measured from size decile 9 (mean cap
~$26bn) into size decile 0 (**mean cap ~$47 million**) — a population that sits
entirely below our $5 floor and dollar-volume window — and it is *strongest when
large-stock spreads are wide*, i.e. exactly when execution is worst. The residual
effect in scrutinised names is not literally zero (10 bp per 100 bp, **per month**),
but it is a monthly-horizon gross beta, and Novy-Marx & Velikov's cost arithmetic
(cost ≥ 1% of monthly one-sided turnover for value-weighted books, **2–3× that for
equal-weighted**) annihilates it at anything like daily turnover. Two independent
things would each be enough to close this on their own: the effect lives where we
cannot trade, and the one published net-of-cost test of lead–lag strategies puts
the kill point at **40 bp one-way** — below the 33.8 bp/side we have already
*measured* on held names (D285) and far below the ~26 bp/side a $2 name costs us.
I found **one** liquid-name variant worth a second look and it is not X2: see §6.

---

## 2. Where the effect lives

This is the decisive section. Ordered by how directly each source answers it.

### 2.1 The quantified size/coverage gradient — [PEER-REVIEWED]

**Parsons, Sabbatucci & Titman, "Geographic Lead-Lag Effects", *RFS* 33(10), 2020.**
US, 1970–2013, monthly, Compustat/CRSP + I/B/E/S coverage, value-weighted
portfolios, monthly reformation.

Panel regression of firm return on the lagged own-industry portfolio return
(coefficient = bp of next-month firm return per 100 bp of lagged industry return),
split by the *lagging* firm's analyst coverage:

| lagging firm's analyst coverage | industry lead–lag beta |
|---|---|
| 0 analysts | 28 bp |
| 1–4 analysts | 24 bp |
| 5–9 analysts | 14 bp |
| 10+ analysts | 10 bp |

Their own gloss: industry lead-lag effects are **70% weaker** among lagging firms
with 10+ analysts than among those with none, and — the sentence that matters most
for us — *"alternative sorts on firm size and trading volume give virtually
identical patterns, similar to most return anomalies, which also tend to be
strongest among the least scrutinised firms."*

Full-sample betas for reference: industry **24 bp per 100 bp, t = 11.71**; city
(geographic) **6 bp per 100 bp, t = 5.11**. Note the horizon: these are **monthly**
predictors and monthly holding periods, not day t → day t+1.

### 2.2 The population the daily effect is actually measured in — [WORKING PAPER, Fed]

**Chordia, Sarkar & Subrahmanyam, "The Microstructure of Cross-Autocorrelations",
FRBNY Staff Report 303, 2007.** ISSM (1988–92) + NYSE TAQ (1993–2002), NYSE,
size deciles formed annually on CRSP market cap.

- The lead–lag they document runs **decile 9 (average market cap ≈ $26 billion) →
  decile 0 (average market cap ≈ $47 million)**. Decile 0 is not in our universe and
  never has been.
- Order flow in **large** stocks predicts **small**-stock returns; small-stock order
  flow predicts nothing. Price discovery is in the large names; the tradeable leg is
  the small one.
- **"Cross-autocorrelation patterns in returns are strongest when large stock spreads
  are high."** The signal is loudest in exactly the states where the round trip is
  most expensive. This is the same structure that killed D284 and D285 here.

### 2.3 Hou's original industry result — [PEER-REVIEWED]

**Hou, "Industry Information Diffusion and the Lead-Lag Effect in Stock Returns",
*RFS* 20(4), 2007.** US, weekly, ~1963–2001.

- The big-firm→small-firm lead–lag is **predominantly an intra-industry phenomenon**
  — which is precisely the X2 construction, so this is the right paper.
- It is driven by **sluggish adjustment to NEGATIVE information**. That means the
  tradeable half is the **short** leg in small, thinly-traded names — a *second*
  cost wall (borrow) stacked on the first (per-share commission on low-priced names).
- More pronounced in **small, less competitive and neglected industries**.

I could not obtain the paper's own tables (SSRN 403, Oxford paywall); the above is
from the published abstract as reproduced by SSRN/RFS and as characterised by
Parsons et al. (2020) and Chinco (below).

### 2.4 The delay premium's population — [PEER-REVIEWED]

**Hou & Moskowitz, "Market Frictions, Price Delay, and the Cross-Section of Expected
Returns", *RFS* 18(3), 2005.** The delay premium is concentrated in a neglected-firm
segment described as **under 0.02% of total market capitalisation**. That is the
population in which "slow information diffusion" is priced. Not ours.

### 2.5 The strongest counter-evidence, stated fairly — [PEER-REVIEWED]

**Chordia & Swaminathan, "Trading Volume and Cross-Autocorrelations in Stock
Returns", *JF* 55(2), 2000.** CRSP NYSE/AMEX, **1963–1996**, 16 size×turnover
portfolios, Wednesday-close weekly returns.

They find high-turnover portfolios lead low-turnover portfolios **"even in the
largest size quartile"**, and report the result is **robust in the post-1980
sub-period**. This is the single strongest published statement that the effect is
not purely a microcap artefact, and it should be recorded honestly.

Why it does not rescue X2:
1. **The traded leg is the LOW-turnover portfolio.** Sorting on turnover within the
   largest size quartile does not deliver a liquid tradeable name — it deliberately
   isolates the *least* traded names at each size. Our dollar-volume window cuts on
   exactly this axis.
2. **The sample ends in 1996** — pre-decimalisation, pre-Reg NMS, pre-algorithmic
   market making, pre-ETF. Their daily first-order portfolio autocorrelations
   (e.g. 0.25 for the large/low-turnover cell) are not credible as present-day
   quantities.
3. Their own explanation for why it survives is cost: *"Why do these lead-lag
   patterns not get arbitraged away? Most likely because of the high transaction
   costs that any trading strategy designed to exploit these short-horizon patterns
   would face."* (citing Mech 1993). The authors are on the dismissal's side.

### 2.6 An out-of-sample replication attempt — [UNVERIFIED — personal research blog]

Alex Chinco's research notebook replicates Hou (2007) on June 1963–Dec 2001
(FF 12-industry) and then re-runs it on **Jan 2000–Dec 2013 with GICS
sub-industries**. Reported: the pattern persists but *"the results are similar, but
slightly less pronounced"*, peak effect at 1–2 weeks, and — notably — *"looking at
the predictive power of the really large firms (if anything) weakens the effect."*
That last line is a direct hit on the X2 premise that the *large-cap cohort* is the
right leader. This is a blog post, not peer-reviewed, and I did not verify the code
or the data; treat it as suggestive only.

---

## 3. Cost survival and break-even

### 3.1 The one direct net-of-cost lead–lag test I found — [PEER-REVIEWED, low-tier journal]

**"Lead-Lag Relationships in International Stock Markets Revisited: Are They
Exploitable?", *International Journal of Financial Research* 9(1), 2018.** Portfolios
sorted by size, analyst coverage and institutional ownership across seven major
developed markets. Abstract: abnormal returns *"quickly decline when transaction
costs are introduced and become insignificant for one-way transaction costs of more
than 40 basis points"*, and lead–lag relationships are *"probably not exploitable in
practice"*.

**Against our own measured costs:** D285 measured 33.8 bp/side (Corwin–Schultz) on
the names actually *held*; a $2 stock at one cent of spread is ~26 bp/side under our
per-share regime; and the population the effect lives in is lower-priced and wider-
spread than the names D285 held. We are at or through the published kill point
before we start, and we would be trading a *cheaper* population than the one in
which the effect is documented. I could not verify the exact universe/date range of
this paper beyond the abstract (IJFR is not a strong venue — weight accordingly),
but the 40 bp figure is the only published break-even I located and it is not close.

### 3.2 The turnover arithmetic — [PEER-REVIEWED]

**Novy-Marx & Velikov, "A Taxonomy of Anomalies and Their Trading Costs", *RFS*
2016.** Costs from Hasbrouck (2009) Gibbs-sampler effective spreads. Key results,
verbatim-in-substance:

- *"Transaction costs consequently reduce realized spreads by more than 1% of the
  monthly one-sided turnover."* i.e. 20% one-sided monthly turnover ⇒ **≥ 20 bp/month**
  of the gross spread gone.
- Round-trip costs for typical **value-weighted** strategies average **> 50 bp**.
- **"Transaction costs for equal-weighted strategies are generally two to three times
  higher"**, and such strategies are "often less profitable to implement, despite
  frequently looking stronger ignoring transaction costs." **We are equal-weighted.**
- Of every strategy studied with **> 50% one-sided monthly turnover, only two**
  generate significant net spreads (both are industry-relative reversal variants —
  see §6).
- *"Anomaly spreads are often higher for smaller stocks, [but] these stocks are
  significantly more expensive to trade."*

**Apply it to X2 as contemplated.** A day-t → day-t+1 construction with a one-day
hold is ~2,100% one-sided monthly turnover. At >1% of one-sided turnover for a
value-weighted book, that is ≥ **21% per month** in cost; at the 2–3× equal-weight
multiplier, **42–63% per month**. The published industry lead–lag beta in the
scrutinised bucket is **10 bp per 100 bp of monthly industry move**. There is no
holding period, no slot count and no cost-mitigation trick that closes a gap of
that order. Lengthening the hold to amortise the round trip runs straight into the
programme's own rule (CLAUDE.md, "Cost-cutting ≠ edge-sharpening"): the daily
cross-autocorrelation is a fast-decaying quantity, so per-bar edge falls faster than
cost coverage rises.

### 3.3 The literature's own verdict on why it persists

Chordia & Swaminathan (2000), Mech (1993, *JFE* 34(3) — cited, not read) and
Chordia/Sarkar/Subrahmanyam (2007) all converge on the same explanation for the
effect's survival: **it persists because it costs too much to trade.** An anomaly
whose published explanation for its own existence is your cost wall is not a
candidate for a retail per-share cost regime.

---

## 4. Decay since the 1990s and since 2010

I could **NOT** find a study that measures daily large-to-small cross-autocorrelation
specifically on a post-2010 US sample. That is a real gap and I state it plainly.
What exists is indirect and points one way:

- **Chordia, Subrahmanyam & Tong, *JAE* 2014** [PEER-REVIEWED] — most prominent
  equity anomalies have attenuated; average returns from a portfolio of prominent
  anomalies **roughly halved after decimalisation**, and the decline is attributed to
  hedge fund AUM, short interest and aggregate turnover. NYSE monthly value-weighted
  share turnover went from 5% (1993) to 35% (2008).
- **McLean & Pontiff, *JF* 2016** [PEER-REVIEWED] — 97 published predictors: returns
  **26% lower out-of-sample, 58% lower post-publication**. Crucially for us: the
  surviving returns are concentrated in **high idiosyncratic risk and LOW LIQUIDITY**
  stocks. The decay hits the part we could trade hardest.
- **Pinchuk, "Customer Momentum"** [WORKING PAPER, arXiv 2301.11394; dated 2018,
  posted 2023] — replicates Cohen & Frazzini's supplier–customer lead–lag on
  1978–2018 at **122 bp/month equal-weighted (106 bp value-weighted)**, then reports
  that *"in the post-discovery sample, customer momentum has a smaller magnitude and
  loses statistical significance."* Same paper: restricting to links with the smallest
  customer/supplier size ratio **cuts the magnitude by a factor of 2–4**, and adding a
  relative-size interaction term **flips the sign** — his conclusion is that customer
  momentum is *"at least partially driven by the lead-lag relationship between the
  returns of large and small stocks."* So the flagship economic-links lead–lag both
  (a) reduces to the size lead–lag and (b) has decayed post-publication.
- **Greenwood & Sammon, "The Disappearing Index Effect", NBER w30748, 2022**
  [WORKING PAPER, NBER] — the S&P 500 addition abnormal return fell from **3.4%
  (1980s)** and **7.6% (1990s)** to **0.8% over the last decade**; deletions from large
  negative abnormal returns to **−0.6% (2010–2020)** — despite indexed assets growing
  enormously. This is the cleanest available evidence that *predictable flow-driven
  effects in large liquid names have been arbitraged away* in exactly our era.
- **Parsons et al. (2020)** [PEER-REVIEWED] — geographic lead–lags "weakened somewhat
  over the last two decades", while industry momentum stayed "relatively constant".
  They attribute the industry constancy to *"high, persistent limits to arbitrage for
  small firms"* alongside "gradually more efficient pricing over time for large,
  liquid firms." Read plainly: the part that survived is the part we cannot trade.
- **Curme, Tumminello, Mantegna, Stanley & Kenett, OFR WP 15-15, 2015** [WORKING
  PAPER, US Treasury OFR] — intraday NYSE, top-100 caps, 2001–03 vs 2011–13. This
  one is **ambiguous and I will not spin it**: they report that lagged
  cross-correlations contributed significantly in 2001–03 and that auto- and lagged
  correlations play a *more* prominent role in 2011–13, with strong end-of-day
  periodicity. It is an intraday, largest-cap, physics-methodology study; it is not
  evidence about daily size-cohort lead–lag either way.

---

## 5. Is it a non-synchronous-trading artefact?

**The strongest published statement of the critique — [PEER-REVIEWED]:**
**Boudoukh, Richardson & Whitelaw, "A Tale of Three Schools: Insights on
Autocorrelations of Short-Horizon Stock Returns", *RFS* 7(3), 1994.** They argue
prior studies **seriously understate** nonsynchronous trading. Once the standard
assumptions are loosened to allow **heterogeneous nontrading probabilities and
heterogeneous betas**, the weekly autocorrelation of a small-stock portfolio
attributable to nonsynchronous trading is **as high as 0.20 — about 56% of the total
autocorrelation.** A closely related strand (Hameed 1997; Boudoukh et al.) holds that
portfolio cross-autocorrelations are largely a restatement of portfolio
autocorrelations plus contemporaneous correlations, and should vanish once own
autocorrelation is controlled for.

**Lo & MacKinlay's own numbers**, for scale: observed weekly first-order
autocorrelation of a small-firm portfolio ≈ **46%**, versus **< 9%** induced by their
nontrading model. They claimed the artefact explains only a small share; Boudoukh et
al. push that share to ~56% by relaxing the model.

**Rebuttals:**
- **Chordia & Swaminathan (2000)** [PEER-REVIEWED] — use Wednesday-close weekly
  returns and cite Foerster & Keim: a NYSE/AMEX stock goes untraded for two
  consecutive days only **2.24%** of the time and for five consecutive days **0.42%**.
  They conclude nonsynchronous trading and own autocorrelations "cannot fully explain"
  the pattern.
- **Anderson, Eom, Hahn & Park, "Stock Return Autocorrelation is Not Spurious",
  UC Berkeley WP E05-342, 2005** [WORKING PAPER] — direct tests using **disjoint time
  intervals separated by a trade**, which mechanically eliminates the nonsynchronous
  effect. They find partial price adjustment is an important and sometimes the main
  source of autocorrelation, with "very substantial" lower bounds on its share.

**Where this leaves X2.** The artefact debate is genuinely unresolved (the honest
summary is: a large minority-to-majority share of the *small-portfolio* number is
stale-price, and a real residual of partial price adjustment survives). But the
debate is **less relevant to us than it is to the literature**, and in a way that
does not help: our $5 price floor plus dollar-volume window already excludes the
non-trading population. That excision removes the artefact **and** removes the effect
together, because both live in the same names. It is not a case where cleaning the
data leaves a tradeable residual — it is a case where the cleaning *is* the universe
filter that deletes the phenomenon.

---

## 6. Any variant that lives in liquid names

Three candidates. Only one is genuinely coverage-and-size-neutral, and it is not X2.

### 6.1 Geographic lead–lag — the only real hit

**Parsons, Sabbatucci & Titman, *RFS* 2020** [PEER-REVIEWED]. Lead–lag between
**co-headquartered firms in different sectors** (their example: Seattle's Costco and
Amazon — in 2013, zero analysts covered both). Risk-adjusted returns **5–6% per
year**, about **half** the industry lead–lag. The load-bearing claim:

> geographic lead–lags are **unrelated** to analyst coverage, market capitalisation,
> or trading volume — whereas industry lead–lag effects are 70% weaker among lagging
> firms with 10+ analysts.

Mechanism: sell-side analysts specialise by *sector*, not by *city*, so no analyst
bridges the geographic pair even when both firms are heavily covered. That is a
mechanism that predicts survival in liquid names rather than assuming it — which is
the property this programme keeps asking for.

**What is wrong with it as a lead here:**
- **Monthly, not daily.** Sorting variable and holding period are both one month;
  the beta is 6 bp per 100 bp of lagged city-portfolio return (t = 5.11). Turnover
  ~100%/month one-sided ⇒ ≥ 100 bp/month cost value-weighted, **200–300 bp/month
  equal-weighted** on Novy-Marx & Velikov's numbers. 5–6%/yr gross is ~50 bp/month.
  **It does not obviously clear our cost wall either**, and I found **no transaction-
  cost analysis in the paper.**
- **It is decaying**: the authors say geographic lead–lags "weakened somewhat over
  the last two decades" (sample ends 2013 — twelve years stale now).
- **It is not X2.** It is a geography-cluster lead–lag, not a size-cohort lead–lag.
  Filing it as a confirmation of X2 would be exactly the error in
  `construction-vs-axis.md`, in reverse.

### 6.2 Intra-industry reversals — adjacent, and the only cost-survivor in the neighbourhood

Two independent peer-reviewed pointers converge:
- **Hameed & Mian (2015)**, as characterised in Parsons et al. (2020): intra-industry
  reversals in monthly returns are *"consistently present over time, and prevalent
  across subgroups of stocks, including large and liquid stocks."* [PEER-REVIEWED —
  **but I read only the second-hand characterisation, not the paper**]
- **Novy-Marx & Velikov (2016)**: of every strategy with >50% one-sided monthly
  turnover, **exactly two** produce significant net spreads after Hasbrouck effective
  spreads — the combination of **industry momentum with industry-relative reversals**,
  and **industry-relative reversals among low-volatility stocks** — and only when
  designed with cost mitigation (buy/hold spread) in mind.

This is the strongest *cost-surviving, liquid-name, industry-conditioned* result I
found anywhere in this literature. It is a **reversal**, not a lead–lag, so it is a
different lead — but if the aim is "an industry-relative daily/monthly cross-sectional
signal that has been shown to survive realistic costs", this is the published address.

### 6.3 ETF-linked constructions — checked, and they do not deliver X2

- **Brown, Davies & Ringgenberg, "ETF Arbitrage, Non-Fundamental Demand, and Return
  Predictability"** [WORKING PAPER, ~*RFS*/*JF*-track, 2020 draft]. ETF creation/
  redemption flows, **2007–2016**, monthly. A portfolio short high-flow and long
  low-flow **ETFs** earns **1–4% per month**; Sharpe 0.60 (1-month) / 0.99 (6-month)
  in the mature-ETF sample, 0.22 / 0.82 in the high-activity unleveraged sample. The
  **traded object is the ETF, not the constituents** — it is not a size-cohort
  lead–lag and would use our 551-symbol ETF fixture as the *tradeable* set, not as a
  predictor of single names.
- **Index inclusion is dead** (Greenwood & Sammon, §4): 0.8% for adds and −0.6% for
  deletes in 2010–2020, against 3.4%/7.6% in the 1980s/1990s. Any construction whose
  edge is "predictable index-driven flow into large liquid names" has already been
  competed away in precisely our sample window.
- Ben-David, Franzoni & Moussawi (2018) on ETF ownership and constituent volatility/
  reversal is real but is a *volatility/reversal* result, not a lead–lag; I did not
  verify its magnitudes directly and will not quote numbers for it.

---

## 7. Data requirements and what is free

| requirement | source | free? | catch |
|---|---|---|---|
| Industry classification (SIC) | SEC EDGAR company metadata | **free** | SIC is coarse and self-reported; not point-in-time-clean |
| Industry classification (FF 12/17/30/48/49) | Ken French data library (SIC→industry map) | **free** | static mapping; the standard academic choice |
| Industry classification (GICS) | S&P/MSCI | **paid, licensed** | what Chinco used for the 2000–2013 re-run |
| Text-based peer network (TNIC) | Hoberg–Phillips data library, Tuck/Dartmouth | **free** | **covers 1989–2021 only** — leaves ~5 years of our 2010-08-2026 fixture uncovered; annual, 10-K-derived |
| Supply-chain / customer links | Compustat Segment Customer file | **paid** | the Cohen–Frazzini / Pinchuk source |
| Supply-chain, free route | SEC 10-K Item 1 major-customer disclosure | free, needs NLP | annual, coarse; Pinchuk's linked sample is only **~11–14% of firms and ~10–15% of market cap** even in recent years — small n before you begin |
| Analyst coverage | I/B/E/S | **paid** | no free point-in-time substitute verified |
| HQ location (for the geographic variant) | Compustat | **paid** | — |
| HQ location, free route | SEC EDGAR company business address + filing history | **free** | point-in-time trail exists but must be built from filings |
| **ETF holdings** | **SEC N-PORT data sets** (sec.gov) | **FREE** | **monthly** holdings, **Oct 2019 – Jun 2026**, posted quarterly. Verified against the SEC's own data-sets page |
| ETF holdings, sponsor sites | iShares/SPDR/Invesco product pages | free | **CURRENT-DAY SNAPSHOT ONLY.** I checked the iShares IVV page: it offers `latest-holdings.csv` and **no historical archive.** A live series must be snapshotted forward from today |

**On the ETF fixture specifically:** the honest position is that free retrospective
ETF holdings exist (N-PORT, monthly, back to Oct 2019) but at a frequency an order of
magnitude coarser than our daily bars and covering only the last ~7 years of a
16.6-year fixture. Anything requiring *daily* holdings history is not free.

---

## 8. Does it transfer to OUR universe

**Bluntly: no, and the failure is structural rather than marginal.**

1. **The lagging leg is below our floor.** The daily large→small cross-autocorrelation
   is measured decile 9 → decile 0, and decile 0's *mean* market capitalisation in the
   Fed study is **$47 million**. Our $5 price floor plus dollar-volume window is
   designed to exclude exactly that. What we would be left with — the 5–9 and 10+
   analyst buckets — carries a beta of 14 and 10 bp per 100 bp, **monthly**, gross,
   in a 1970–2013 sample.
2. **We are equal-weighted, which is the expensive side of the one cost study that
   measures both.** Novy-Marx & Velikov: equal-weighted transaction costs run **2–3×**
   value-weighted, and equal-weighted books "frequently look stronger ignoring
   transaction costs." That is a description of the trap this programme has already
   walked into three times.
3. **The horizon is wrong for the cost regime.** Everything worth trading in this
   literature is a monthly-horizon quantity. The *daily* quantity (day t → day t+1) is
   the one most contaminated by the stale-price critique (§5) and the one whose
   turnover multiplies the cost by ~20×.
4. **The tradeable half is the short side of illiquid names.** Hou (2007): the
   lead–lag is driven by sluggish adjustment to **negative** information. Borrow on
   small, low-priced, thinly-traded names is a second cost wall we have not even
   priced here.
5. **The signal is loudest when execution is worst.** The Fed study's finding that
   cross-autocorrelation peaks when large-cap spreads are wide means the strongest
   signal days are the worst fill days — a correlation between edge and cost that
   makes gross-to-net degradation worse than a flat-cost assumption would show.
6. **Post-2010 evidence is absent, and every adjacent measurement points down.**
   Halved anomaly returns post-decimalisation; 58% post-publication decay concentrated
   in low-liquidity names; customer momentum losing significance post-discovery; the
   index effect down from 7.6% to 0.8%.

**What is honestly NOT settled.** No published paper I found measures daily
large-cohort → small-cohort cross-autocorrelation on a **2010–2026 US sample with a
$5 price floor**. So "the documented effect lives in the illiquid tail" is settled;
"there is literally nothing at t+1 in the $5+ population" is an inference from the
size/coverage gradient plus the decay evidence, not a direct measurement. Given the
cost arithmetic in §3.2 — a gap of two orders of magnitude, not a close call — I do
not think that gap is worth a week of runner time to close. If the principal wants
the axis kept open (per `construction-vs-axis.md`, only the principal closes an
avenue), the cheapest honest probe is **not** X2 as framed but §6.2:
industry-relative reversal in liquid names, which is the one construction in this
literature with a published net-of-cost survival.

---

## 9. Sources

**[PEER-REVIEWED]**
- Parsons, Sabbatucci & Titman, "Geographic Lead-Lag Effects", *Review of Financial
  Studies* 33(10), 2020 — https://academic.oup.com/rfs/article-abstract/33/10/4721/5682420
  (full working-paper text read at https://www.aeaweb.org/conference/2020/preliminary/paper/SfTyaRaf)
- Hou, "Industry Information Diffusion and the Lead-lag Effect in Stock Returns",
  *RFS* 20(4), 2007 — https://academic.oup.com/rfs/article-abstract/20/4/1113/1615954
  (abstract only; full text paywalled — **numbers here are second-hand**)
- Hou & Moskowitz, "Market Frictions, Price Delay, and the Cross-Section of Expected
  Returns", *RFS* 18(3), 2005 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=408161
  (abstract only)
- Chordia & Swaminathan, "Trading Volume and Cross-Autocorrelations in Stock Returns",
  *Journal of Finance* 55(2), 2000 — https://www.cis.upenn.edu/~mkearns/finread/Chordia_lead_lag.pdf
  (full text read)
- Boudoukh, Richardson & Whitelaw, "A Tale of Three Schools: Insights on
  Autocorrelations of Short-Horizon Stock Returns", *RFS* 7(3), 1994, pp. 539–573 —
  https://pages.stern.nyu.edu/~rwhitela/research.html (abstract/secondary only;
  **the 0.20 / 56% figures are second-hand and I did not read the paper's tables**)
- Lo & MacKinlay, "An Econometric Analysis of Nonsynchronous Trading", NBER w2960 /
  *Journal of Econometrics*, 1990 — https://www.nber.org/papers/w2960
- Novy-Marx & Velikov, "A Taxonomy of Anomalies and Their Trading Costs", *RFS*, 2016 —
  https://mysimon.rochester.edu/novy-marx/research/ToAatTC.pdf (full text read)
- McLean & Pontiff, "Does Academic Research Destroy Stock Return Predictability?",
  *Journal of Finance* 71(1), 2016 — https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12365
- Chordia, Subrahmanyam & Tong, "Have capital market anomalies attenuated in the
  recent era of high liquidity and trading activity?", *Journal of Accounting and
  Economics*, 2014 — https://www.sciencedirect.com/science/article/abs/pii/S0165410114000275
  (abstract only)
- Cohen & Frazzini, "Economic Links and Predictable Returns", *Journal of Finance*,
  2008 — https://pages.stern.nyu.edu/~afrazzin/pdf/Economic%20Links%20and%20Predictable%20Returns%20-%20Cohen%20and%20Frazzini.pdf
  (**fetch failed — connection refused; numbers here come from Pinchuk's replication,
  not from the original**)
- Mech, "Portfolio return autocorrelation", *JFE* 34(3), 1993, pp. 307–344 —
  **cited by Chordia & Swaminathan as the transaction-cost explanation; NOT READ**
- Hameed & Mian, intra-industry reversals, 2015 — **NOT READ**; characterised only via
  Parsons et al. (2020) footnote
- "Lead-Lag Relationships in International Stock Markets Revisited: Are They
  Exploitable?", *International Journal of Financial Research* 9(1), 2018 —
  https://ideas.repec.org/a/jfr/ijfr11/v9y2018i1p8-30.html (abstract only; **low-tier
  venue — the 40 bp break-even is the only published break-even I found and it is
  weakly sourced**)

**[WORKING PAPER]**
- Chordia, Sarkar & Subrahmanyam, "The Microstructure of Cross-Autocorrelations",
  FRBNY Staff Report 303, Sept 2007 — https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr303.pdf
  (full text read)
- Anderson, Eom, Hahn & Park, "Stock Return Autocorrelation is Not Spurious",
  UC Berkeley WP E05-342, 2005 — https://escholarship.org/content/qt9s35b82c/qt9s35b82c.pdf
  (abstract read)
- Greenwood & Sammon, "The Disappearing Index Effect", NBER w30748, 2022 —
  https://www.nber.org/papers/w30748 (abstract/secondary)
- Pinchuk, "Customer Momentum", arXiv:2301.11394 (dated Dec 2018) —
  https://arxiv.org/pdf/2301.11394 (full text read)
- Brown, Davies & Ringgenberg, "ETF Arbitrage, Non-Fundamental Demand, and Return
  Predictability", 2020 draft — https://ssrn.com/abstract=2872414 (full text read)
- Curme, Tumminello, Mantegna, Stanley & Kenett, "How Lead-Lag Correlations Affect
  the Intraday Pattern of Collective Stock Dynamics", OFR WP 15-15, 2015 —
  https://www.stern.nyu.edu/sites/default/files/assets/documents/OFRwp-2015-15_Lead-Lag-Correlations.pdf
  (abstract/intro read; **ambiguous, do not cite as decay evidence**)

**[PRIMARY DATA DOC]**
- SEC, Form N-PORT data sets — https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets
  (free; monthly fund/ETF holdings, Oct 2019 – Jun 2026, posted quarterly)
- iShares Core S&P 500 ETF product page —
  https://www.ishares.com/us/products/239726/ishares-core-sp-500-etf
  (current-day holdings CSV only; no historical archive offered)
- Hoberg–Phillips Data Library, TNIC industry classifications —
  https://hobergphillips.tuck.dartmouth.edu/industryclass.htm (free; 1989–2021)

**[UNVERIFIED]**
- Alex Chinco, "Intra-Industry Lead-Lag Effect" (personal research blog) —
  https://alexchinco.com/intra-industry-lead-lag-effect/ — replication of Hou (2007)
  and a 2000–2013 GICS re-run. Not peer-reviewed; code and data not checked.

**[SALES INSTRUMENT]** — noted, not relied on
- AQR, "Economic Links and Predictable Returns" —
  https://www.aqr.com/Insights/Research/Journal-Article/Economic-Links-and-Predictable-Returns
  (asset manager hosting a co-authored journal article; Frazzini is an AQR principal)

**Nothing in any of the pages I read contained text addressed to me or instructing me
to act.** No files were submitted, no forms filled, no accounts created. PDFs were
cached by the fetch tool and text-extracted locally for reading only.
