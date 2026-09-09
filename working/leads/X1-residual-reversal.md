# X1 — cluster-residual reversal: external evidence

External literature review. Research only — nothing run, nothing measured on our fixture.
Compiled 2026-09-09.

## 1. Verdict

**Residualising rescues the SIGNAL and relocates the COST problem — it does not solve
it.** The premise is genuinely well supported: five independent samples agree that
subtracting a group return from the past-month return multiplies GROSS reversal by
roughly **1.5× to 3.5×**, and the improvement is large, monotone and highly
significant everywhere it has been measured. But three things kill it for us. First,
**the published mechanism is not the one the lead claims.** The gain does not come
from isolating a compensated idiosyncratic component; it comes from removing raw
reversal's accidental SHORT exposure to *industry momentum* (and to PEAD). Dai,
Medhat, Novy-Marx & Rizova regress raw reversal on the three and get
`REV = 0.13 + 0.76·IRRX − 0.54·PEAD − 0.53·IMOM`, adj-R² **87%**, intercept
insignificant. Second, **the residual version is still a liquidity premium, and its
own proponents say so** — Hameed & Mian frame intra-industry reversal explicitly as
"returns to supplying liquidity" and find it earns **nothing** in names without large
order imbalances; Dai et al. adopt industry-relative reversal *precisely because* it
is a cleaner proxy for the return to liquidity provision. Third, and decisively for
us, **the one study that reports gross and net side by side for both versions on one
sample finds the residual version's cost bill grows faster than its edge**:
Novy-Marx & Velikov get gross 0.37% → 0.98%/month going from raw to industry-relative,
and net **−1.28% → −0.80%/month**. Still deeply negative, at *institutional*
effective-spread costs with no price impact and no commission. Separately, the
data-driven clustering half of the proposal has its own published negative: Chan,
Lakonishok & Swaminathan find correlation-based clusters fail out of sample, and in
small caps the out-of-sample within-cluster correlation advantage collapses to **0.02**.
Our universe is the small-cap case.

## 2. Raw vs residualised, on the same sample

The literature *does* provide this comparison, repeatedly, and it agrees. All figures
are long-short spreads in % per month unless noted; t-stats in brackets.

| Study | Sample | Universe / weighting | RAW reversal | RESIDUALISED | Ratio |
|---|---|---|---|---|---|
| Dai, Medhat, Novy-Marx & Rizova (2023) | Jan 1973 – Dec 2021 | CRSP NYSE/AMEX/NASDAQ, **value-weighted** quintiles, NYSE breaks | REV **0.31** [1.68] | IRR (− FF49 industry) **0.74** [5.40]; IRRX (also − PEAD) **1.08** [9.35] | 2.4× / 3.5× |
| Novy-Marx & Velikov (2016) | Jul 1963 – Dec 2013 | CRSP, **value-weighted** deciles | gross **0.37** [1.71]; FF4α 0.45 [2.22] | Industry-Relative gross **0.98** [5.72]; FF4α 1.05 [6.66] | 2.6× |
| Hameed & Mian (2015) | Jan 1968 – Dec 2010 | US, **equal-weighted**, $1 long / $1 short | **0.63** risk-adj | intra-industry **0.97**; with FF48 industries **1.28** | 1.5× – 2.0× |
| Da, Liu & Schaumburg (2014) | Jan 1982 – Mar 2009 | ~2,350 I/B/E/S-covered names, **>$5 price**, avg cap $2.5bn (74% of CRSP cap), **equal-weighted** deciles | **0.67** [2.53]; FF3α 0.33 [1.37]; **5Fα −0.19** [−0.85] | within-industry **1.20** [5.87] (FF3α 0.92, 5Fα 0.46); + analyst-CF residual **1.57** [9.48] (FF3α 1.34, **5Fα 0.91** [6.02]) | 1.8× / 2.3× |
| Blitz, Huij, Lansdorp & Verbeek (2013) | not verified | claims large-cap, post-1990 | — | "risk-adjusted returns **twice as large**" | 2× (claimed) |

Notes that matter more than the ratios:

- **The 5-factor column in Da et al. includes DMU, the reversal factor itself.** Raw
  reversal's alpha against it is −0.19% [−0.85]; the residual version keeps
  **+0.91% [6.02]**. So the residual signal is genuinely incremental to the published
  reversal factor, not a repackaging of it. This is the strongest positive result in
  the whole file.
- **Only part of Da et al.'s residual is reachable from OHLCV.** Panel C needs I/B/E/S
  analyst forecast revisions. The part we could build is Panel B, within-industry:
  **0.67 → 1.20**. Dai et al. note their own far simpler announcement adjustment
  achieves the same t-stat "without excluding two-thirds of firms."
- **Da et al. Sharpe:** monthly 0.52 residual vs 0.14 raw (raw returns); 0.53 vs 0.08
  on FF3-adjusted. The variance reduction is as big a part of the story as the mean.
- **Equal weighting inflates these numbers.** Dai et al., footnote 5: Da et al.'s
  t-stats are equal-weighted, and EW "dramatically over-weight the smallest stocks,
  where it is well known that reversals are stronger". Their own EW IRRX has t > 14.
  **We are equal-weighted.** That will flatter our gross and inflate our cost bill.
- **The mechanism.** Both Hameed & Mian and Dai et al. attribute the improvement to
  removing the *inter-industry* component, which carries Moskowitz-Grinblatt industry
  momentum. Hameed & Mian: "the primary driver of the difference in returns is the
  extraction of the inter-industry reversal component." Da et al. concede their
  industry controls "will mechanically enhance the short-term return reversal" by
  taking out industry momentum. **This is a testable premise for us** (see §8).

## 3. Is residual reversal still a liquidity premium?

**Yes. The residualisation purifies the liquidity-provision return rather than
escaping it — and that is the explicit, stated position of the people who built it.**

The strongest evidence, in order of force:

1. **Dai, Medhat, Novy-Marx & Rizova (2023) use industry-relative reversal AS their
   instrument for measuring the return to liquidity provision.** Their stated reason:
   removing PEAD and industry momentum leaves a signal "less contaminated by
   news-driven effects, so should provide a more reliable lens through which to study
   the returns to liquidity provision." The proponents of the residual construction
   treat it as the *cleaner* liquidity trade.

2. **Hameed & Mian (2015): the residual version earns nothing without order
   imbalance.** Their intra-industry strategy conditioned on large order imbalances
   earns a significant **0.7%/month** risk-adjusted; "the intra-industry reversal
   strategy applied to stocks that have low price pressure does not yield significant
   profits." They also find intra-industry reversals are stronger following aggregate
   market declines and in volatile times — the Nagel (2012) signature of constrained
   liquidity providers. Their framing: intra-industry reversals "reflect compensation
   for accommodating imbalances in order flows."

3. **Da, Liu & Schaumburg's own splits show the residual version concentrating in the
   illiquid tail of an already-large-cap universe** (Table 5, Panel D):

   | Split | Residual reversal, raw | FF3α | 5Fα (incl. reversal factor) |
   |---|---|---|---|
   | Illiquid third (Amihud) | **2.38%** | 2.23% | **1.67%** [7.39] |
   | Liquid third | **0.91%** | 0.68% | **0.29%** [1.47] |
   | Difference | 1.48% [7.05] | 1.55% [7.23] | 1.39% [5.26] |
   | Small third | 2.07% | 1.91% | 1.55% [5.86] |
   | Large third | 0.94% | 0.73% | 0.28% [1.67] |
   | High IVOL | 2.01% | 1.77% | 1.21% |
   | Low IVOL | 1.17% | 0.98% | 0.58% |

   **In the liquid third the 5-factor alpha is 0.29%/month, t = 1.47 — insignificant,
   and below their own 0.805%/month cost estimate.** Same in large caps: 0.28% [1.67].
   Their extreme deciles hold stocks with *half* the market cap of the sample average,
   higher Amihud illiquidity, higher turnover and wider spreads than the average name.

4. **Da et al.'s own time-series decomposition splits it by leg.** The LONG side
   (buying losers) loads positively and significantly on lagged detrended Amihud and
   lagged realised volatility — "these profits are more likely reflecting compensations
   for liquidity provision" (correlations 0.24 and 0.23). Only the SHORT side loads on
   sentiment (nipo, equity share; correlations 0.43 and 0.57). **The long leg is
   liquidity provision by the authors' own reading.**

5. **Dai et al.: the microcap advantage is a FIRST-DAY effect.** Reversals are much
   larger among microcaps, but "there are almost no differences across the other size
   quintiles, which together account for 97% of market capitalization," and the
   microcap spread is "primarily driven by strong first-day effects" — a ~**80 bp
   first-day** effect on illiquid low-turnover microcaps. That is bid-ask bounce and
   immediate liquidity provision. It is not harvestable by anyone paying the spread to
   get in.

**The one piece of counter-evidence, and it is real.** Novy-Marx & Velikov's Table 15
sorts strategies into lagged trading-cost terciles (conditional on size). Gross
industry-relative reversal is **1.34 / 0.88 / 1.04** across low/mid/high cost terciles —
*not* concentrated in the expensive names, and raw reversal is similarly flat
(0.66 / 0.62 / 0.51). So the residual version's gross edge is not purely a
wide-spread phenomenon. But the net returns in the same table are
**−0.17 / −1.07 / −1.99** — negative even in the cheapest tercile. The edge is not
*located* in the spread, but it is *smaller than* the spread everywhere.

**Answer: relocated, not escaped.** And where it isn't spread-concentrated, it still
doesn't clear the toll.

## 4. Cost survival and break-even

This is where every strand converges, and the numbers are brutal.

**Novy-Marx & Velikov (2016), RFS, Jul 1963 – Dec 2013, value-weighted deciles.**
Costs are Hasbrouck (2009) Gibbs-sampler **effective bid-ask spreads only** — no price
impact, no commission. The authors state plainly the measure "does not account for
price impact." So these are a **lower bound**.

| Strategy | Gross | FF4α gross | Turnover /mo | T-costs /mo | **Net** | FF4α net |
|---|---|---|---|---|---|---|
| Short-run Reversals | 0.37 [1.71] | 0.45 [2.22] | 90.87% | 1.65% | **−1.28** [−6.02] | — |
| **Industry Relative Reversals** | 0.98 [5.72] | 1.05 [6.66] | 90.28% | **1.78%** | **−0.80** [−4.73] | — |
| Ind. Rel. Rev. (**Low Volatility**) | 1.25 [9.36] | 1.17 [8.96] | 93.99% | 1.06% | **+0.19** [1.41] | 0.07 [0.57] |

Read the middle row twice. **Residualising raised gross by +0.61%/month and raised the
cost bill by +0.13%/month — and the strategy is still 80 bp/month under water.** Its
break-even requires costs at roughly **55% of a spread-only institutional estimate**.

Their verdict on the whole high-turnover class: *"Transactions costs significantly
exceed the gross spread for all but two of the anomalies we examine... accounting for
the effective bid-ask spread alone eradicates the profits."*

**With their best cost mitigation** (a 10%/50% buy/hold spread, cutting turnover from
90% to ~40%/month):

| Strategy (mitigated) | Gross | Turnover | T-costs | Net |
|---|---|---|---|---|
| Industry Relative Reversals | 0.61 [5.43] | 39.61% | 0.60% | **+0.01** [0.10] |
| Short-run Reversals | 0.38 [2.85] | 41.19% | 0.54% | **−0.17** [−1.29] |
| Ind. Rel. Rev. (Low Vol) | 0.70 [9.10] | 41.09% | 0.39% | **+0.31** [4.12] |

**Exactly zero for the plain residual version, after the best cost engineering in the
literature.** The only survivor adds a low-volatility screen — and note what that
screen does: it cuts T-costs from 1.78% to 1.06% (−40%) while cutting gross only from
1.25%... i.e. **what rescues the strategy is a cost filter, not the residualisation.**

**By size** (NMV Table 13, value-weighted, mitigated):

| Strategy | Gross Micro / Small / Large | Net Micro / Small / Large |
|---|---|---|
| Industry Relative Reversals | 1.54 / 0.89 / 0.61 | **−1.42 / −0.37 / −0.12** [−0.85] |
| Short-run Reversals | 1.05 / 0.41 / 0.18 | −1.90 / −0.84 / −0.51 |
| Ind. Rel. Rev. (Low Vol) | 0.89 / 1.17 / 0.92 | −0.86 / **+0.28** [1.96] / **+0.31** [2.73] |

**Avramov, Chordia & Goyal (2006), JF, 1962–2002, NYSE/AMEX, weekly.** The cleanest
break-even statement in the literature, and it is a negative:

- Lowest-turnover, lowest-illiquidity portfolio: contrarian profit **0.37%/week**;
  Keim-Madhavan institutional round trip for that size quintile **0.52%**. Negative.
- Highest-turnover, highest-illiquidity portfolio: profit **1.08%/week**; round trip at
  the *smallest* institutional trade size **1.15%**. Negative. At the next trade size
  up, **2.45%**.
- Proportional effective spread for that portfolio: **3.18%** (vs 0.39% for the
  low-illiquidity portfolio).
- Their conclusion: *"the potential contrarian trading profits are not attainable after
  accounting for transactions costs. The main reason is that the largest potential
  profits are obtained in the highly illiquid stocks that have high trading costs."*

**Da, Liu & Schaumburg's own cost arithmetic** is the most optimistic in the file and
worth stating precisely so it can be discounted: extreme-decile quoted spreads of 46
and 43 bp, monthly portfolio turnover of 90.2% and 90.8%, giving
`46×0.902 + 43×0.908 = 80.5 bp/month`. Against FF3α 1.34% that leaves **0.54%/month
net, t = 3.90**. But: quoted spread only, no impact, no commission; on a >$5,
$2.5bn-average-cap, analyst-covered universe; and their own *liquid* tercile
(5Fα 0.29%) and *large* tercile (0.28%) sit **below** that 80.5 bp bar.

**Hameed & Mian**: one-way proportional effective spread estimate **0.41–0.46%**
→ round trip 0.82–0.92%/month, against gross 0.97–1.28%/month. A margin of **5 to 38
bp per month** at institutional costs, on monthly turnover.

**No paper found reports net-of-cost reversal returns at a RETAIL cost level.**
Every cost estimate above is institutional: Keim-Madhavan institutional trade data,
Hasbrouck Gibbs effective spreads, or quoted spreads. I could not verify a single
study of retail-cost reversal. This is a genuine gap and it runs against us — retail
per-share costs on a low-priced universe are strictly worse than any of these.

## 5. Clustering: statistical vs industry, and cluster stability

**The literature has a direct, published negative on exactly the substitution X1
proposes, and it is the sharpest single finding in this file.**

**Chan, Lakonishok & Swaminathan (2007), Financial Analysts Journal.** CRSP,
1975–2004, split into six non-overlapping five-year blocks. Hierarchical clustering on
distance = 1 − correlation of monthly returns, **40 clusters** (chosen to roughly match
the Fama-French industry count). Correlations then measured out of sample on the
*following* five years.

| Sample | Period | Within-cluster corr | Outside-cluster corr | **Spread** |
|---|---|---|---|---|
| Large-cap | Estimation (in-sample) | 0.51 | 0.29 | 0.22 |
| Large-cap | **Testing (out-of-sample)** | 0.39 | 0.26 | **0.13** |
| Small-cap | Estimation (in-sample) | — | — | 0.15 |
| Small-cap | **Testing (out-of-sample)** | **0.18** | **0.16** | **0.02** |

Their conclusions, both of which bear directly on X1:

- *"Pseudo-industry groups formed from statistical cluster analysis of stock returns do
  not match the performance of industry classifications on an out-of-sample basis.
  Both GICS and FF industries have larger within-group correlations and sharper
  discrimination over outside-group correlations."*
- Even where clustering ties GICS (large caps), **it needs 40 categories to match what
  10 two-digit GICS sectors deliver.**
- The small-cap failure has a named cause: *"the variability in small-cap returns is
  predominantly idiosyncratic in nature, [so] the assignment of stocks to statistical
  clusters is likely to be driven by the correlations of company-specific returns"* —
  i.e. **the clustering fits noise.**

For reference, GICS's own discrimination (same paper): large caps in the same 2-digit
GICS sector correlate 0.38 vs 0.26 across sectors; within 4-digit GICS, sales-growth
correlation 0.22 vs 0.10.

**On cluster stability**, the table above *is* the measurement: within-cluster
correlation decays 0.51 → 0.39 and the discriminating spread 0.22 → 0.13 over a
five-year horizon in large caps, and 0.15 → 0.02 in small caps. **I found no published
measurement of cluster-membership turnover per rebalance** (what fraction of names
change cluster month to month). That number does not appear to exist in the
literature. It would have to be measured on our own panel.

**Every reversal paper that residualises uses an INDUSTRY map**, never a statistical
cluster: FF49 (Novy-Marx & Velikov; Dai et al.), FF48 and FF12 (Hameed & Mian),
I/B/E/S 11-sector (Da et al.), or FF3 factor loadings (Blitz et al.). **I found no
study implementing correlation- or PCA-cluster-residual short-term reversal on US
equities with published gross and net magnitudes.** X1's specific construction is
untested in the literature I could reach.

One mixed note: Fodor, Jorgensen & Stowe (2021, *Journal of Financial Research*) report
that using financial clusters and industry groups *together* beats either alone. That
is a combination result, not a replacement result, and I did not verify its magnitudes.

## 6. Post-2010 decay

Reversal has decayed, and it had already decayed substantially *before* 2010.

- **Da, Liu & Schaumburg**, residual reversal by decade: 1982–89 **2.10%**;
  1990–99 **1.64%**; 2000–Mar 2009 **0.99%** (5Fα 0.64%). Monotone. Their own reading:
  "consistent with the improvement of overall market liquidity and/or price efficiency."
- **Hameed & Mian**: unconditional reversal "has declined in magnitude over the past few
  decades, and is not different from zero in the recent decades." Their intra-industry
  version still earned **0.94%/month in 2000–2010** — the residual version decayed less.
- **Dai et al., over the full modern sample 1973–2021**: raw value-weighted reversal is
  **0.31%/month, t = 1.68 — insignificant.** They state their results hold
  post-decimalization (I did not extract the subperiod table).
- **Chordia, Subrahmanyam & Tong (2014)**, *J. Accounting & Economics*: anomaly returns
  **approximately halved after decimalization**, attributed to hedge fund AUM, short
  interest and aggregate turnover — i.e. exactly the stat-arb capacity channel.
- **McLean & Pontiff (2016)** and **Chen & Zimmermann**: post-publication anomaly
  returns roughly **50% smaller** than in-sample. (Reported via search summary; I did
  not open the primary sources to verify the exact decomposition.)
- **Blitz, van der Grient & Honarvar (2023)**, SSRN 4575689, *Reversing the Trend of
  Short-Term Reversal*: reported to claim the classic short-term reversal effect "has
  steadily weakened over time, to the point of now having vanished entirely in most
  regions." **UNVERIFIED** — see §9; SSRN returned HTTP 403 to WebFetch on both the
  abstract page and the PDF, so I have only a search-result summary. Worth noting *if*
  it holds: the lead author is the same David Blitz who authored the flagship
  pro-residual-reversal paper.
- **Khandani & Lo**: their contrarian-strategy simulation on daily US returns documents
  a large increase in market depth from 1995 to 2007. I did **not** verify the specific
  daily-return decay figures often quoted from this paper.

Nothing I found measures cluster-residual reversal specifically after 2010.

## 7. Where the effect lives — size, price, liquidity

Unanimous across every source: **small, illiquid, high-volatility, high-turnover, and
the very first day.**

- **Dai et al.**: reversals are much larger among microcaps; "there are almost no
  differences across the other size quintiles, which together account for 97% of market
  capitalization." The microcap excess is "primarily driven by strong first-day
  effects" — ~80 bp on the first day for illiquid low-turnover microcaps.
- **Novy-Marx & Velikov**, gross by size: industry-relative reversal 1.54 (micro) /
  0.89 (small) / 0.61 (large).
- **Da, Liu & Schaumburg**, residual reversal: small third 2.07% vs large third 0.94%;
  illiquid third 2.38% vs liquid third 0.91%; high-IVOL 2.01% vs low-IVOL 1.17%; and
  stronger among firms with sharply rising Moody's KMV EDF (distress-driven forced
  selling).
- **Avramov, Chordia & Goyal**: largest reversals in high-turnover, low-liquidity
  stocks; the extreme loser/high-turnover/high-illiquidity portfolio earns 1.08%/week
  gross against a 3.18% effective spread.

**Horizon (Q7).** Dai et al. give the cleanest structure: *higher volatility → faster,
initially stronger reversals; lower turnover → more persistent, ultimately stronger
reversals.* Concretely, for 21-day industry-relative reversal measured one month after
formation, the spread is **106 bp among below-NYSE-median-volatility stocks vs 39 bp
among high-volatility stocks** — because among high-volatility names "the reversal ends
and momentum sets in after just two weeks." So the *monthly* horizon is where the
low-volatility (tradeable) version works; the daily/weekly horizon is where the
high-volatility, microcap, first-day (untradeable) version lives.

**Medhat & Schmeling (2022, RFS)** add a sign flip that matters: double-sorting on last
month's return and turnover, **reversal appears among LOW-turnover stocks while
HIGH-turnover stocks show short-term MOMENTUM** at the one-month horizon. Reported to
survive transaction costs and to be strongest among the largest, most liquid,
most-covered stocks. (Magnitudes not verified — search summary only.)

**I found no evidence that a weekly horizon improves the cost ratio.** The direction is
against it: weekly rebalancing multiplies turnover roughly 4× over monthly, and the
monthly strategies above already fail on cost by 80 bp/month. Avramov et al.'s weekly
results fail break-even in both the liquid and illiquid corners. Dai et al. also note
that Avramov et al.'s finding that reversals are *stronger* in high-turnover stocks at
the weekly frequency is an artifact of skipping a day, which discards exactly the
first-day effect that favours the illiquid low-turnover names.

## 8. Does it transfer to OUR universe

Bluntly: **the gross improvement should transfer; the net will not, and the clustering
step is likely to be actively harmful.**

**What transfers.** The 1.5–3.5× gross uplift from residualising is robust across five
samples, three weighting schemes, and 1963–2021. If we build X1 we should expect our
gross per-trade number to rise materially over the plain reversal that returned zero
survivors. That is real and it is worth knowing.

**What does not.**

1. **Cost, on our exact axis.** Novy-Marx & Velikov's industry-relative reversal needs
   costs at ~55% of a *spread-only, institution-executed, no-impact* estimate to break
   even. We pay IBKR retail per-share, and cost in bp scales **inversely with price**.
   Our own measured 216.6 bp round trip on the widest two deciles of a reversal
   strategy is the same order as NMV's 1.78%/month bill at 90% monthly turnover. The
   published residual version failed against the cheaper of those two.

2. **Equal weighting runs the wrong way.** Dai et al. state it directly: equal-weighted
   reversal strategies "dramatically over-weight the smallest stocks, where it is well
   known that reversals are stronger." Every headline residual-reversal t-stat above 9
   is equal-weighted. We are equal-weighted, so we will *inherit the inflated gross and
   the inflated cost bill together* — and per-share costs make our bill worse than
   proportional to the papers'.

3. **The $5 floor removes the population where the effect is strongest — but that
   population's advantage is a first-day effect.** So the floor is correct and it costs
   us little real edge; it does not rescue anything. Note also that our floor is far
   below the papers': Da et al.'s extreme deciles average **$30.90 and $38.35** per
   share, and reversal sorts select on |return|, which selects low-priced, high-vol
   names — the worst possible selection under per-share costs.

4. **The clustering step is the weakest link, and it is separable from the reversal
   question.** Chan, Lakonishok & Swaminathan's small-cap result — out-of-sample
   within-cluster correlation 0.18 vs outside-cluster 0.16, **spread 0.02** — says that
   on a small-cap panel a correlation cluster carries almost none of a name's real
   systematic variation out of sample. If that holds on our fixture, then
   `r_5(cluster(i), t)` is mostly noise, and `resid_5 = r_5 − r_5(cluster)` is
   **`r_5` plus noise**: a strictly *noisier* version of the signal that already
   returned zero survivors across 18 cells. Their diagnosis — clustering on small caps
   fits company-specific correlations — is exactly the failure mode.

5. **The mechanism claim in the lead is not the documented one, and this changes what
   to check first.** The literature's gain comes from removing raw reversal's short
   exposure to *group momentum*. Industries have documented one-month momentum
   (Moskowitz-Grinblatt); **correlation clusters are not industries and there is no
   published evidence that they carry one-month momentum.** If our clusters do not
   exhibit it, the main documented source of the improvement is simply absent.

6. **Breadth.** ~10 effective independent instruments against papers running
   value-weighted deciles over 1,000+ names. Every t-stat above is earned on breadth we
   do not have.

**Two cheap Stage-0 premise checks that decide this lead before any backtest is
written**, both computable from the existing fixture and both matching the shape of the
published failure:

- **(a) Cluster discrimination, out of sample.** Fit clusters on a trailing window;
  measure within-cluster minus outside-cluster average pairwise correlation on the
  *following, disjoint* window. If that spread is near CLS's small-cap 0.02, the
  residual is noise and X1 is dead without running it. If it is near their large-cap
  0.13, proceed.
- **(b) Cluster momentum.** Measure the one-month autocorrelation of cluster returns
  directly — the group-momentum that residualising removes. If our clusters show no
  one-month momentum, the documented mechanism for the 1.5–3.5× uplift does not apply
  and we should expect a much smaller gain than the table in §2.

**The only specification that survives costs anywhere in this literature** is
industry-relative reversal, **value-weighted**, restricted to **large caps** and to
**below-NYSE-median idiosyncratic volatility**, with a buy/hold cost-mitigation spread,
netting **+0.31%/month (t = 2.73)** over 1963–2013 at institutional spread-only costs.
That configuration differs from our universe on all four of weighting, size, volatility
screen, and cost regime. And note what it implies: **the cost filter, not the
residualisation, is what made it survive.** Given that our own binding constraint is
already the spread — gross +219.8 bp against a 216.6 bp round trip, the edge equal to
the toll to the basis point — this lead as specified attacks the numerator when the
literature says the surviving lever is the denominator.

## 9. Sources

Primary sources read in full or in substantial part are marked as such; where I relied
on a search-engine summary I say so.

- **[PEER-REVIEWED]** Da, Z., Liu, Q., Schaumburg, E. (2014). "A Closer Look at the
  Short-Term Return Reversal." *Management Science* 60(3), 658–674.
  https://academicweb.nd.edu/~zda/Reversal.pdf — full text read. Working-paper version:
  NY Fed Staff Report 513, https://www.newyorkfed.org/research/staff_reports/sr513.html
- **[PEER-REVIEWED]** Novy-Marx, R., Velikov, M. (2016). "A Taxonomy of Anomalies and
  Their Trading Costs." *Review of Financial Studies* 29(1), 104–147. NBER WP 20721,
  https://www.nber.org/system/files/working_papers/w20721/w20721.pdf — full text read.
  **The single most useful source for this lead** (Tables 3, 12, 13, 15).
- **[PEER-REVIEWED]** Hameed, A., Mian, G.M. (2015). "Industries and Stock Return
  Reversals." *JFQA* 50(1-2), 89–117.
  https://web2-bschool.nus.edu.sg/wp-content/uploads/media_rp/publications/BwXb81392625636.pdf
  — full text read.
- **[PEER-REVIEWED]** Avramov, D., Chordia, T., Goyal, A. (2006). "Liquidity and
  Autocorrelations in Individual Stock Returns." *Journal of Finance* 61(5), 2365–2394.
  https://users.nber.org/~confer/2004/mmsu04/goyal.pdf — full text read (§3.6 on costs).
- **[WORKING PAPER]** **[CONFLICT: Dimensional]** Dai, W., Medhat, M., Novy-Marx, R.,
  Rizova, S. (2023). "Reversals and the Returns to Liquidity Provision." NBER WP 30917.
  https://www.nber.org/system/files/working_papers/w30917/w30917.pdf — full text read.
  Three co-authors are Dimensional employees; Novy-Marx consults for Dimensional. NBER
  WPs are not peer-reviewed. Disclosed on the paper's own cover page.
- **[PEER-REVIEWED]** **[CONFLICT: Robeco]** Blitz, D., Huij, J., Lansdorp, S.,
  Verbeek, M. (2013). "Short-term residual reversal." *Journal of Financial Markets*
  16(3), 477–504. Abstract verified at https://repub.eur.nl/pub/40707 — **full text NOT
  obtained.** All four authors were at Robeco / Erasmus. This is the strongest positive
  claim in the file (net-of-cost profits in large caps post-1990, and an explicit
  rejection of the trading-frictions explanation) and it is the one I could least
  verify. Its magnitudes, turnover and cost assumptions are unknown to me.
- **[WORKING PAPER]** **[CONFLICT: Robeco — NOT INDEPENDENT]** Huij, J., Lansdorp, S.
  "Residual Momentum and Reversal Strategies Revisited." SSRN 2929306. Full text read.
  Confirms the 2011/2013 Blitz et al. results out of sample and across global universes
  — but **two of the four original authors wrote it, both at Robeco.** This is a
  self-replication, not independent confirmation.
- **[PEER-REVIEWED]** Chan, L.K.C., Lakonishok, J., Swaminathan, B. (2007). "Industry
  Classifications and Return Comovement." *Financial Analysts Journal* 63(6).
  https://www.lsvasset.com/pdf/research-papers/industry_FAJ.pdf — full text read
  (Table 6 and conclusion). Hosted by LSV Asset Management (the authors' firm), but the
  paper is peer-reviewed FAJ.
- **[PEER-REVIEWED]** Nagel, S. (2012). "Evaporating Liquidity." *RFS* 25(7), 2005–2039.
  https://www.nber.org/papers/w17653 — **abstract/summary only, full text not read.**
  Cited for the framing that reversal returns proxy the return to liquidity provision
  and are strongly predictable by VIX.
- **[PEER-REVIEWED]** Chordia, T., Subrahmanyam, A., Tong, Q. (2014). "Have Capital
  Market Anomalies Attenuated in the Recent Era of High Liquidity and Trading
  Activity?" *J. Accounting & Economics* 58, 41–58.
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2029057 — **search summary only.**
- **[PEER-REVIEWED]** Medhat, M., Schmeling, M. (2022). "Short-Term Momentum." *RFS*
  35(3). https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3795253 — **search summary
  only.** Note Medhat is at Dimensional.
- **[PEER-REVIEWED]** Fodor, A., Jorgensen, R.D., Stowe, J.D. (2021). "Financial
  clusters, industry groups, and stock return correlations." *Journal of Financial
  Research*. https://onlinelibrary.wiley.com/doi/abs/10.1111/jfir.12236 — **search
  summary only**; magnitudes unverified.
- **[WORKING PAPER]** **[CONFLICT: Robeco]** **[UNVERIFIED]** Blitz, D., van der Grient,
  B., Honarvar, I. "Reversing the Trend of Short-Term Reversal." SSRN 4575689.
  **Could not verify.** WebFetch returned **HTTP 403 Forbidden** on both
  `papers.ssrn.com/sol3/papers.cfm?abstract_id=4575689` and the
  `Delivery.cfm` PDF URL. The claim that reversal "has vanished entirely in most
  regions" comes from a search-engine summary only and should not be cited as
  established until the paper is read.
- **[PEER-REVIEWED]** McLean, R.D., Pontiff, J. (2016). "Does Academic Research Destroy
  Stock Return Predictability?" *Journal of Finance* — **search summary only**; the
  commonly quoted ~50% post-publication decay was not verified against the primary text.
- **[WORKING PAPER]** Khandani, A., Lo, A. "What Happened to the Quants in August 2007?"
  http://web.mit.edu/~alo/www/Papers/august07b_2.pdf — **search summary only.** The
  frequently quoted decay of daily contrarian returns from the mid-1990s to 2007 was
  **not** verified; do not cite a number from it without reading it.

### What I could not verify

1. **Blitz et al. (2013) full text** — the paper making the strongest pro-X1 claim.
   EFMA mirror failed with a TLS error ("unable to verify the first certificate");
   SSRN and ScienceDirect are paywalled/403. Its magnitudes, turnover assumptions and
   cost model are unknown to me. Given that it is the lone source claiming net-of-cost
   survival and is practitioner-authored, **this gap matters and should be closed
   before X1 is costed.**
2. **Any retail-cost analysis of reversal.** None found. Every cost figure in this file
   is institutional.
3. **Any study of correlation/PCA-cluster-residual short-term reversal on US equities**
   with published gross and net magnitudes. None found — X1's exact construction
   appears untested.
4. **Published cluster-membership turnover per rebalance.** None found. Only CLS's
   five-year out-of-sample correlation decay speaks to stability.
5. **Post-2010 subperiod numbers for the residual version.** Hameed & Mian stop at 2010;
   Da et al. at 2009; NMV at 2013; Dai et al. run to 2021 but I did not extract their
   post-decimalization subperiod table.

### Safety note

No web page, PDF or search result encountered during this review contained text
addressed to the agent, instructions to act, or attempts to alter the task. All content
was treated as data. Two sources were blocked rather than fetched — SSRN returned HTTP
403 to WebFetch on two URLs, and the EFMA host failed TLS certificate verification;
these are recorded above as tool-level failures, not as evidence.
