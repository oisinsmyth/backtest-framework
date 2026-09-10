# K6 — What the surviving published anomalies have in common

External-evidence brief. Round 6. Written 2026-09-10.
**I have no access to the programme's data and claim nothing about it.** Every number below is from
a cited external source, tagged by TYPE and — in the same sentence — by HOW WELL I ESTABLISHED IT.
Where a figure comes from a summariser rather than from bytes I read, it says so and is treated as
weaker, not stronger.

Scope boundary honoured: this brief never discusses t-statistic thresholds as a methodology,
deflated Sharpe, PBO, or multiple-testing correction. Replication studies are used **only** as
evidence about *which effects survive*. Two papers in the evidence base (Hou–Xue–Zhang,
Jensen–Kelly–Pedersen) are partly *about* multiple testing; I use their survival verdicts and
their size/category breakdowns and nothing else.

---

## 0. THE HEADLINE, AND IT REVERSES THE PROGRAMME'S FRAMING

The programme's six recurring killers are built around **cost**. For the surviving anomalies, cost
is **not** the binding constraint. Three things bind instead, and in this order:

| | what binds | the number |
|---|---|---|
| **1. The gross edge is gone post-2005, in the investable universe** | Post-2005, in the top 90% of market cap, the **median** published anomaly earned **7 bp/month gross**, median *t* **0.45**, median annualised Sharpe **0.11** — against **48 bp/month** in the all-stock / pre-2006 cell that matches the original papers. Roughly **85% of the published alpha required BOTH pre-2006 data AND microcaps** | Chen & Welch (2026) [WORKING PAPER] [read in full] |
| **2. What remains is mostly luck** | In that same cell the cross-sectional variance of anomaly *t*-statistics was **1.09** — luck alone produces 1.00. Signal share ≈ **0.08**. The best survivor's raw 66 bp/month shrinks to **6 bp/month** | Chen & Welch (2026) [WORKING PAPER] [read in full] |
| **3. What remains is in the SHORT leg** | Post-2005, large universe: long-leg-minus-market *t*-statistics had **mean −0.31 and variance 0.98 — below the null's 1.00**, so the shrinkage factor is zero and **every** survivor's long-minus-market return adjusts to **0.00%/month**. Top survivor raw long-minus-market returns were 0.40, 0.26, 0.35, 0.13, 0.15, 0.21, 0.14, 0.33, 0.16, −0.01 %/month — all shrink to zero | Chen & Welch (2026) [WORKING PAPER] [read in full] |

**Cost does not bind on the survivors because the survivors are low-turnover.** Novy-Marx &
Velikov's value-weighted decile strategies with **one-sided monthly turnover of 1.2–7.2%** (annual
rebalancing) paid **3–11 bp/month** in Hasbrouck effective spreads — a small fraction of a 20–80
bp/month gross spread [PEER-REVIEWED, RFS 2016; NBER w20721 working-paper text] [read in full].
At the programme's stated 33.8 bp/side the drag on a 2%/month-turnover book is **~1.4 bp/month**.
Cost is a rounding error there. It is annihilating at daily horizons (§3.4).

**So the screen this lane was asked for is not a cost screen.** It is: *low turnover, annual signal,
characteristic not event, and a short leg you cannot run.* Stated as a decision: **the survivor set
does not contain a lane this programme can trade as specified** — not because of the 33.8 bp/side,
but because the surviving gross edge sits in a short leg the programme has excluded and in
accounting fundamentals the programme does not have free. **§6 gives the honest residual — three
doors, one of which is not locked.** §5 answers the mirror question, and the answer is that survival
is close to random with respect to observable features once you condition on the post-2005 investable
universe. §9 is the screen, as a checklist.

---

## 1. SOURCES, TYPE AND HOW WELL ESTABLISHED

| # | source | type | established |
|---|---|---|---|
| S1 | Chen & Welch, *What Useful Alphas?*, arXiv 2607.06502, draft 8 Jul 2026, targeting FAJ | [WORKING PAPER] | **[read in full]** — 24pp PDF extracted locally, all tables |
| S2 | Chen & Velikov, *Zeroing In on the Expected Returns of Anomalies*, JFQA 58(3) 2023, 968–1004 (open access) | [PEER-REVIEWED] | **[read in full]** — published PDF + the 2020 FEDS 2020-039 version, both extracted |
| S3 | Novy-Marx & Velikov, *A Taxonomy of Anomalies and Their Trading Costs*, RFS 29(1) 2016; text read = NBER w20721 (Dec 2014) | [WORKING PAPER] for the text I read; the RFS version is [PEER-REVIEWED] | **[read in full]** (w20721) |
| S4 | Hou, Xue & Zhang, *Replicating Anomalies*, RFS 33(5) 2020; text read = NBER w23394 (May 2017) | [WORKING PAPER] for the text I read | **[read in full]** (w23394); the RFS abstract's 65%/82% figures are [snippet only] |
| S5 | Chen & Zimmermann, *Open Source Cross-Sectional Asset Pricing*, Critical Finance Review 11 (2022) 207–264; text read = FEDS 2021-037 | [PEER-REVIEWED] (text read is the Fed WP) | **[read in full]** |
| S6 | Jensen, Kelly & Pedersen, *Is There a Replication Crisis in Finance?*, NBER w28432 (Feb 2021); published JF 2023 | [WORKING PAPER] for the text I read | **[read in full]** — note Kelly and Pedersen are AQR; treat as interested |
| S7 | McLean & Pontiff, *Does Academic Research Destroy Stock Return Predictability?*, JF 71(1) 2016; texts read = Oct-2012 and May-2013 working drafts (82 characteristics) | [WORKING PAPER] for the text I read | **[read in full]** (drafts). The published 26%/58% figures are **[quoted verbatim inside S6, which I read in full]** |
| S8 | Chen, Lopez-Lira & Zimmermann, *Does Peer-Reviewed Research Help Predict Stock Returns?*, arXiv 2212.10317 v7, Dec 2025 | [WORKING PAPER] | **[read in full]** abstract + intro + category tables |
| S9 | Jacobs & Müller, *Anomalies across the globe*, JFE 135(1) 2020; text read = Jan-2017 draft (231 anomalies, 39 markets) | [WORKING PAPER] for the text I read | **[read in full]** abstract + intro |
| S10 | Frazzini, Israel & Moskowitz, *Trading Costs*, Aug 2018 draft | [WORKING PAPER], AQR authors — **treat as an interested cost-optimistic source** | **[read in full]** abstract + the full methodology caveats in §I |
| S11 | Blitz, Baltussen & van Vliet, *When Equity Factors Drop Their Shorts*, FAJ 76(4) 2020, open access | [PEER-REVIEWED] but all three authors are Robeco Quantitative Investments — **interested** | **[read in full]** Tables 3 and 4 |
| S12 | Stambaugh, Yu & Yuan, *The Short of It*, JFE 104(2) 2012 | [PEER-REVIEWED] | **[read in full]** abstract + hypotheses + sample |
| S13 | Patton & Weller, *What You See Is Not What You Get*, JFE 137(2) 2020 | [PEER-REVIEWED] paper; **what I read was the authors' Dec-2018 slide deck**, not the paper | **[snippet only — slides]** |
| S14 | Muravyev, Pearson & Pollet, *Anomalies and Their Short-Sale Costs*, JF 80(6) 2025, 3639–3694 | [PEER-REVIEWED] | **[abstract only]** — both Wiley and SSRN refused me (§8.1); numbers are the publisher abstract relayed by RePEc via a summariser |
| S15 | DeMiguel, Martín-Utrera, Nogales & Uppal, *A Transaction-Cost Perspective…*, RFS 33(5) 2020 | [PEER-REVIEWED] | **[snippet only]** — PDF downloaded, not read; the 6→15 figure is from a search summariser |
| S16 | Baldi-Lanfranchi, *Transaction-cost-aware Factors*, May 2024 | [WORKING PAPER] | **[abstract only]** — abstract and intro read |
| S17 | Chordia, Subrahmanyam & Tong, *Have capital market anomalies attenuated…*, JAE 58(1) 2014 | [PEER-REVIEWED] | **[abstract only]** via RePEc + WebFetch summariser |
| S18 | Dong & Yang, *Anomalies Never Disappeared: The Case of Stubborn Retail Investors*, Dec 2023 | [WORKING PAPER] | **[abstract only]** |
| S19 | Novy-Marx & Velikov, *Assaying Anomalies*, JEL (2024/25) + `github.com/velikov-mihail/AssayingAnomalies` | [SOFTWARE DOC] for what I saw | **[snippet only, and via a summariser]** — the paper itself I could not open (§8.1) |

**No vendor or sell-side material is used as evidence for a return anywhere in this brief.** S10,
S11 and S6 are author-interested and are flagged at every point of use.

---

## 2. SECTION 1 — THE REPLICATION EVIDENCE: FOUR DIFFERENT BARS, ROUTINELY CONFLATED

The literature uses one word, "survives", for four different tests. Separating them is most of the
work in this lane, because the headline replication rates (35%, 57%, 85%, ~100%) are **not in
conflict about the same question**.

| bar | what it asks | best evidence | verdict |
|---|---|---|---|
| **(a) Reproduction** | does the original paper's own number come back from the original method and data? | S5: for the **161** characteristics that were clearly significant in the originals, **98%** of reproduced long-short portfolios have \|t\|>1.96; "nearly 100% of the literature's predictability results can be reproduced" [PEER-REVIEWED] [read in full] | **passes overwhelmingly** |
| **(b) Robustness to construction** | does it survive NYSE breakpoints + value weighting, i.e. with microcaps suppressed? | S4: of **447** anomalies, **286 (64%)** insignificant at 5%; of 102 trading-frictions/liquidity variables **95 (93%)** insignificant [WORKING PAPER w23394] [read in full]. The RFS version's abstract gives **65%** and, at \|t\|>2.78, **82%** [snippet only] | **most fail** |
| **(b′) same bar, different construction choices** | ditto, with capped value weighting and a hierarchical prior | S6: replicating HXZ's own construction they get **56.9%**, not HXZ's 35%; **+8.5%** of the gap is capped value weighting alone, **+4.3%** from one breakpoint/lag choice, **+4.0%** from another; their own final rate is **84.9%** (global + empirical-Bayes), and **77.3%** after their multiple-testing handling [WORKING PAPER, AQR-affiliated] [read in full] | **most pass** |
| **(c) Out-of-sample / post-publication persistence** | does it keep working after the original sample, and after publication? | S7 drafts: out-of-sample decay **~10%, not distinguishable from zero**; post-publication decay **~35%** on 82 characteristics [WORKING PAPER] [read in full]. The published JF version's **26% out-of-sample / 58% post-publication** on 97 characteristics is quoted verbatim inside S6 [read in full]. S8: **~50% of predictability remains** post-sample, for peer-reviewed *and* for 29,000 data-mined accounting ratios alike [WORKING PAPER] [read in full] | **decays ~35–58%, does not vanish** |
| **(d) Survival net of realistic costs, in modern data** | would an investor have netted anything, post-2005, in stocks they could trade? | S2: average anomaly's expected return **4 bp/month** net, across 204 anomalies (post-publication + post-2005 + cost-mitigated); **−2 bp** if value weighting is enforced [PEER-REVIEWED] [read in full]. S1: median **7 bp/month gross** in the top-90%-of-cap universe post-2005 [WORKING PAPER] [read in full]. S14: across 162 anomalies the average long-short is **+0.14%/month before borrow fees and −0.01% after** [abstract only] | **essentially nothing survives** |

**The conflict is real and it is between (b) and (b′), not about costs.** HXZ (S4) say the
literature is microcap-driven p-hacking; JKP (S6) say the same data replicate at 77–85% and that
"criticisms of factor replicability based on arguments around stock size or liquidity are largely
groundless", reporting US empirical-Bayes replication rates of **77.3% in mega caps, 81.5% in large,
81.5% in micro, 71.4% in nano**, with the *ordering and magnitude* of cluster alphas similar across
size groups (Spearman **73%** mega vs micro) [read in full].

**Which I weight, and why.** For *this* lane I weight **S1/S2 (bar d) above both of them**, because
neither S4 nor S6 answers the question asked. S4's bar is in-sample significance under a
construction choice; S6's bar is in-sample significance under a different construction choice plus
a prior; **neither applies a single basis point of trading cost**. S6's own size-group result is
about *statistical* replicability within size bins, not about what is left after paying to trade
them. When the cost-and-era bar is applied by the same open-source data (S5 supplies the
portfolios; S1 and S2 apply the bar) the answer collapses regardless of which side of the S4/S6
dispute you take. **Both S4 and S6 stay on the record; neither is discarded.**

One further datum that cuts *against* the decay story and must be recorded: S9 finds the US is
**the only one of 39 markets** with a reliable post-publication decline — their US estimate is a
**36% post-sample and 60–65% post-publication** decline (EW and VW), while "none of the 38
international markets yields a reliable post-publication decline" [WORKING PAPER] [read in full].
Their reading is that this reflects **limits to arbitrage and the location of quant capital**, not
data mining. For a US-only programme that is the bad half of the news.

---

## 3. SECTION 2 — THE COST-HONEST SUBSET, AND WHERE EACH PAPER'S COST ASSUMPTION SITS

### 3.1 The cost-assumption ladder, and the programme's 33.8 bp/side on it

This is the part the commissioning note most needed, so it is stated exactly. The programme's
measured **33.8 bp/side on names held, ~67.6 bp round trip**, is **not pessimistic relative to the
cost-honest literature. It is almost exactly that literature's own measured number.**

| source | cost measure | magnitude | where 33.8 bp/side sits |
|---|---|---|---|
| S2 | **measured** effective spread: HF from TAQ/ISSM where available, else the simple average of four LF proxies — Hasbrouck Gibbs, Corwin–Schultz high–low, Abdi–Ranaldo CHL, and Fong–Holden–Trzcinka VoV. Effective spread is defined as twice the absolute log difference between trade price and quote midpoint, and they charge **half** of it per weight change [read in full] | **Average spread paid by the 204 academic anomaly implementations, post-pub & post-2005: 68 bp** (in-sample 206 bp; post-publication 85 bp). In 2014 the mean spread paid was **67 bp vs 16 bp for the average NYSE stock — 4×** | **68 bp effective = 34 bp per side. The programme's 33.8 bp/side is the same number.** Not conservative; matched |
| S3 | Hasbrouck (2009) Gibbs effective spread, explicitly "the costs faced by a **small liquidity demander**… it assumes market orders" | "Round trip transaction costs for typical **value-weighted** strategies average in excess of **50 bp**"; equal-weighted strategies "generally two to three times as high" [read in full] | programme's 67.6 bp round trip sits just above their VW average and **below** their EW multiple |
| S10 | **realised** price impact from $1.7tn of live executions by one large institutional manager, 21 markets, 19 years, executed by a **patient** limit-order algorithm | "actual trading costs to be an **order of magnitude smaller** than previous studies suggest"; they state the linear models of Korajczyk–Sadka, Lesmond–Schill–Zhou and Novy-Marx–Velikov "imply trading costs that are an order of magnitude larger" [read in full]. A median-cost figure of **6.24 bp (NYSE) / 6.16 bp (Nasdaq) per rebalance** appears in the companion literature [snippet only] | **10–50× below the programme's level — and not transferable.** See 3.2 |
| S5 | no cost model; uses **liquidity screens** as a proxy | all liquidity adjustments cost about **1/3 of the mean return**: typical 60 bp/month → ~40 bp/month, "regardless of whether the adjustment is an NYSE-only screen, a market equity screen, or the enforcement of value-weighting" [read in full] | a screen-based stand-in, roughly consistent with S2's measured 1/3 |
| S14 | **borrow fees** on the short leg | 162 anomalies: **+0.14%/month before fees, −0.01% after**; "not profitable even before fees if the high-fee observations, representing 12% of stock dates, are excluded" [abstract only] | an **additional** cost the programme has excluded as ground, which lands entirely on a leg it cannot run |
| S13 | implementation cost inferred from **mutual funds' realised** factor exposures vs paper factors | "real-world implementation costs… **eliminate returns to momentum**, **sharply reduce returns to value**, do not affect market or size" [snippet only — slides] | an independent, fund-level confirmation that high-turnover legs do not survive |

### 3.2 Why S10's optimistic number does not rescue anything here, in the authors' own words

S10 is the one serious cost-optimistic source, it is AQR-authored, and it is explicit about why its
number is small — which is also why it does not apply to a daily-bar book crossing the spread:

- the trading algorithm "breaks orders into smaller pieces", "submits a series of limit buy orders
  **below the best bid**" and "patiently waits"; the worked Microsoft example costs **4.3 bp**
  [read in full];
- their universe "**does not include extremely small and illiquid microcap or penny stocks, or
  stocks with very limited daily trading volume**" [read in full];
- and their own explanation of why TAQ-based estimates are larger: those data capture "the average
  trader, which includes informed insiders, **retail traders, liquidity demanders, and impatient
  traders, who face much higher costs than those of a patient trader**" [read in full].

**The programme as specified is the second category.** S10's figure is a statement about patient
institutional execution in liquid names, not about a retail liquidity demander; using it would be
taking a number measured on a different trader. I weight S2 and S3 for this programme and record
S10 as the dissent. (Note also that S10 is itself a source of bad news in one place: the slide
table in S13 reports, for Frazzini et al.'s own 1986–2013 sample, UMD gross **2.26%/yr** and net
**−0.77%/yr** (t = −0.14) [snippet only — slides].)

### 3.3 Which effects actually survive costs, with the numbers

**S3, value-weighted NYSE deciles, 1963–2012, Hasbrouck spreads, no cost mitigation** (gross
return / one-sided monthly turnover % / cost / net, all %/month) [read in full]:

| turnover class | anomaly | gross | TO | cost | **net** | net *t* |
|---|---|---|---|---|---|---|
| **low** | ValProf | 0.82 | 2.94 | 0.06 | **0.77** | 4.82 |
| | Investment | 0.56 | 6.40 | 0.10 | **0.46** | 3.60 |
| | Value (B/M) | 0.47 | 2.91 | 0.05 | **0.42** | 2.39 |
| | Gross profitability | 0.40 | 1.96 | 0.03 | **0.37** | 2.74 |
| | Asset growth | 0.37 | 6.37 | 0.11 | **0.26** | 1.75 |
| | Accruals | 0.27 | 5.74 | 0.09 | **0.18** | 1.43 |
| | Size | 0.33 | 1.23 | 0.04 | **0.28** | 1.44 |
| | Piotroski F | 0.20 | 7.24 | 0.11 | **0.09** | 0.45 |
| **mid** | ValMomProf | 1.43 | 26.8 | 0.43 | **0.99** | 5.18 |
| | Momentum | 1.33 | 34.5 | 0.65 | **0.68** | 2.45 |
| | ValMom | 0.93 | 28.7 | 0.41 | **0.51** | 2.67 |
| | Net issuance (M) | 0.57 | 14.4 | 0.20 | **0.37** | 2.43 |
| | PEAD (CAR3) | 0.91 | 34.7 | 0.57 | **0.34** | 2.41 |
| | Return-on-equity | 0.71 | 22.3 | 0.38 | **0.33** | 1.38 |
| | PEAD (SUE) | 0.72 | 35.1 | 0.46 | **0.26** | 1.60 |
| | Failure probability | 0.85 | 26.1 | 0.61 | **0.24** | 0.73 |
| | Idiosyncratic vol | 0.63 | 24.6 | 0.52 | **0.11** | 0.37 |
| **high** | Industry-rel. reversals (low vol) | 1.25 | 94.0 | 1.06 | **0.19** | 1.41 |
| | High-frequency combo | 1.61 | 91.0 | 1.45 | **0.16** | 1.11 |
| | Industry momentum | 0.93 | 90.1 | 1.22 | **−0.29** | −1.20 |
| | Seasonality | 0.84 | 91.1 | 1.46 | **−0.62** | −3.88 |
| | Industry-rel. reversals | 0.98 | 90.3 | 1.78 | **−0.80** | −4.73 |
| | Short-run reversals | 0.37 | 90.9 | 1.65 | **−1.28** | −6.02 |

S3's own summary: "Most of the anomalies… with one-sided monthly turnover lower than 50% continue
to generate statistically significant net spreads, at least when designed to mitigate transaction
costs. Few of the strategies with higher turnover do", and **"only two of the strategies that have
more than 50% one-sided monthly turnover have significant net spreads"** [read in full].

**The single most useful cost-mitigation result, and its limit.** S3 finds the **buy/hold spread**
(trading hysteresis — enter at the 20th percentile, exit only at the 35th/50th) the most effective
simple mitigation. S2 tabulates exactly where it helps [read in full]:

| in-sample net return by turnover quartile | buy/hold lower bound 20 | 25 | 30 | 35 | 40 | 45 | 50 |
|---|---|---|---|---|---|---|---|
| EW quintiles, turnover Q1 | **0.39** | 0.39 | 0.38 | 0.37 | 0.36 | 0.34 | 0.33 |
| Q3 | 0.12 | 0.16 | 0.17 | **0.18** | 0.17 | 0.17 | 0.17 |
| Q4 | −0.65 | −0.51 | −0.41 | −0.34 | −0.29 | −0.24 | **−0.21** |

Hysteresis rescues high-turnover strategies **only** when combined with value weighting (VW NYSE
deciles, turnover Q4: 0.07 → 0.32 as the exit bound widens to 50). **It does nothing for
low-turnover strategies and it never turns EW Q4 positive.** This is the programme's CLAUDE.md
warning in published form: cost-cutting is not edge-sharpening — S2's optimisation raises
in-sample net returns by 51 bp/month while sacrificing only 7 bp of gross, and the post-2005
expected return is *still* 4 bp.

S16 is the modern version of the same idea (construct the factor to be cost-aware rather than
rebalancing in full), reporting net maximum squared Sharpe gains "up to a factor of 2.5", and —
critically — "TCA construction is most beneficial for **high-turnover** factors, such as momentum,
that are otherwise unprofitable net of costs" [abstract only]. Same shape: construction rescues
cost, never edge.

### 3.4 The arithmetic at the programme's own cost level

Using the programme's 33.8 bp/side, a book that replaces a fraction τ of its positions each month
pays 2·τ·33.8 bp (sell + buy), plus IBKR's 50/P per side:

| one-sided monthly turnover τ | spread drag | + commission at P = $10 | **total bp/month to clear** | published gross that clears it |
|---|---|---|---|---|
| 2% (annual rebalance) | 1.4 | +0.2 | **1.6** | easily — S3's low-turnover net column |
| 7% (S3's accruals / asset growth) | 4.7 | +0.7 | **5.4** | yes, at 1963–2012 gross levels |
| 20% (S2's typical anomaly) | 13.5 | +2.0 | **15.5** | **no** post-2005: S1's median gross is 7 bp |
| 35% (momentum) | 23.7 | +3.5 | **27.2** | **no** post-2005 |
| 90% (monthly reversal class) | 60.8 | +9.0 | **69.8** | **no** — S3 already gets −1.28%/month |
| 100% per bar, 21 bars/month | 1,420 | +210 | **1,630 (16.3%/month)** | **nothing in the literature** |

The last row is the one that matters for a daily-bar book, and it is why the surviving set is not
reachable at the programme's stated horizon without a holding period measured in months. Note
also that the commission column is where the **price** axis enters: at P = $5 the commission adds
20 bp/month at τ = 20%, at P = $50 it adds 2 bp.

---

## 4. SECTION 3 — THE STRUCTURAL FEATURES OF THE SURVIVORS (the deliverable)

Taking "survivor" at the strictest bar available — **post-2005, in a universe you could trade,
after costs** — the set is S1's and S2's, and these are its shared properties. Each is stated with
the evidence and with whether it is a screen the programme can apply.

### F1 — LOW TURNOVER, and therefore a HOLDING PERIOD OF MONTHS TO A YEAR
The strongest single regularity in the **cost** literature — and, importantly, **not** a predictor of
post-2005 net returns (see the second paragraph, which corrects a claim the working-paper version of
S2 would have supported). S3: every low-turnover survivor is **annually rebalanced**, with one-sided
monthly turnover of **1.2–7.2%** (average holding 14–80 months); every strategy with >50% one-sided
monthly turnover fails but two [read in full]. S2: across 204 anomalies, 2-sided monthly turnover of
**41%** and an average paid spread of 68 bp gives a 24 bp/month drag against a 19 bp/month post-2005
gross return — net **−5 bp** [read in full].

**The correction, and it matters.** Turnover predicts the **cost drag** — that is close to an
identity (drag ≈ turnover × spread). It does **not** predict post-2005 net returns. S2's **published**
out-of-sample test sorts anomalies on in-sample statistics and measures post-publication-and-post-2005
net returns: "**none of the predictors produces a reliable pattern in expected returns. Indeed,
turnover actually predicts net returns with the wrong sign, with high turnover implying lower net
returns**", and under value weighting "**anomalies with low in-sample turnover actually produce
negative net returns post-publication and post-2005**" [PEER-REVIEWED, JFQA 2023] [read in full].
Their published Table 3 best-quartile figures are 9.5 bp (in-sample net return), 10.5 bp (net Sharpe)
and **0.2 bp** (1/turnover) under equal weighting, and −0.5/−1.3/**−5.2** bp under value weighting,
all with standard errors of 4–7 bp [read in full]. **The earlier FEDS 2020-039 draft of the same
paper, which I also read, says instead that "only turnover seems to produce a reliable improvement"
with a top quartile of 9.7 bp. The published version supersedes it and reverses the sign. Anyone
citing the draft will get this backwards.**
**Screen: usable as a NECESSARY CONDITION ON COST, not as a predictor of edge. Holding period must
be ≥ ~3 months for the programme's 67.6 bp round trip to be amortised against a plausible 20–40
bp/month gross edge — but passing that test buys nothing about whether the edge exists.**

### F2 — A PERSISTENT CHARACTERISTIC, NOT A DATED EVENT
Every member of S1's post-2005 top ten is a **stock-level characteristic carried continuously**, not
an event with a date: cash-based operating profitability, operating profitability (R&D-adjusted),
realized-implied vol spread, off-season momentum, net external financing, seasonal momentum (16yr+),
gross profitability, R&D/market cap, net equity financing, operating leverage [read in full]. S3's
survivors are the same shape. The dated-event families in the cost-honest tables — PEAD(SUE),
PEAD(CAR3), failure probability — are the **mid-turnover** names whose net *t* falls to 1.60, 2.41
and 0.73 [read in full]. S2 is explicit about the exception class that cost mitigation **cannot**
rescue: "many of these are related to information diffusion, such as price delay or the earnings
surprise of matched large firms. Intuitively, profiting on slow information diffusion may require
trading **neglected and illiquid stocks, as well as frequent trading**" [read in full].
**Screen: usable, and it retrospectively explains eleven failed territories.** Round 1–5 chose
dated events; the survivor set contains none.

### F3 — THE SURVIVING RETURN IS IN THE SHORT LEG
The hardest finding in the brief for this programme. **S1**: post-2005, large universe, the
cross-sectional variance of long-minus-market *t*-statistics is **0.98, below the null's 1.00**, so
every survivor's shrunk long-minus-market return is **0.00%/month**; their conclusion states "Even
this required shorting — the long-only return was at most zero net of selection bias" [read in
full]. **S14**: across 162 anomalies the average long-short is +0.14%/month before borrow fees and
**−0.01%** after, and "the returns are due to the short leg" [abstract only]. **S12**: across 11
anomalies, 1965–2007, the sentiment-conditional profitability is entirely a short-leg phenomenon —
"**None of the 11 long legs exhibits a significant difference** between high- and low-sentiment
periods", with the long legs differing by **4 bp/month** [read in full].
**Counter-evidence, recorded not adjudicated — §7.2.** S11 (Robeco authors) reach the opposite
conclusion on 1963–2018 Fama–French legs: long-leg alphas over the flip-side legs are 0.70 (HML),
2.70 (WML), 0.51 (RMW), 1.19 (CMA), 0.39 (VOL) and 1.09 (All) %/month, short-leg alphas run from
≈0 to significantly negative, and a spanning test **cannot reject** that the short legs are
spanned (p = 0.87); the max-Sharpe portfolio puts **0.0%** on four of the five short legs [read in
full].
**Screen: usable as a flag, which is what the commissioning note asked for. Flag raised: the
post-2005 evidence says the survivors need the short leg; the full-sample evidence says they do
not. The disagreement is not resolved and is partly a difference in sample and in benchmark (§7.2).**

### F4 — WHERE IN THE CROSS-SECTION: SMALL AND ILLIQUID HELPS THE EDGE AND HURTS THE COST, AND THE TWO DO NOT CANCEL THE WAY ANYONE EXPECTS
- **Size.** S4: microcaps are ~3% of NYSE-Amex-Nasdaq market value but ~60% of the stock count, and
  "typically account for more than 60% of the stocks in extreme deciles"; with equal weights they
  earn **1.32%/month** and carry the largest cross-sectional dispersion in both returns and anomaly
  variables [read in full]. S1: restricting to the top 90% of market cap cuts the median anomaly
  return **by about half**, and "predictability monotonically decreases in the liquidity of the set
  of stocks being considered" [read in full].
- **But for LOW-turnover signals, size is not the cost problem.** S3's size-split table (micro /
  small / large, NYSE 20th and 50th percentiles, gross → net) [read in full]: gross profitability
  **0.74 → 0.66** in microcaps (t 2.81), value **1.02 → 0.89** (t 4.25), investment **0.98 → 0.70**,
  ValProf **1.10 → 1.00**. Their own words: "The transactions costs seem to be **immaterial for the
  low-turnover anomalies, even for the micro caps**", the exceptions being microcap size, accruals
  and F-score. For high-turnover strategies the same table is brutal: the high-frequency combo in
  microcaps goes **+1.77%/month gross (t 13.94) → −0.66% net (t −5.12)**.
- **Liquidity as a category dies hardest.** S4: **95 of 102** trading-frictions/liquidity variables
  insignificant (93%), naming Jegadeesh short-term reversal, Datar–Naik–Radcliffe turnover,
  Amihud, Acharya–Pedersen liquidity betas, Ang–Hodrick–Xing–Zhang idiosyncratic and total
  volatility, Liu zero-volume days, Corwin–Schultz spread, Bali–Cakici–Whitelaw MAX, and
  Kelly–Jiang tail risk [read in full]. **Conflict recorded:** S1's post-2005 large-cap
  category table gives "Trading / Liquidity" (N = 13) a **median 0.11%/month and 85% positive** —
  the *highest* positive share of any category [read in full]. §7.3.
- **PRICE, separately from size, as the brief required.** The literature screens on size and
  liquidity and **almost never reports the nominal price distribution of its portfolios** — see
  §8.2, this is a genuine gap and I will not fill it with inference. The one directly relevant
  measurement I did read: S5 compares liquidity adjustments and finds "**the price screen (limiting
  to stocks with share price > $5) appears to be the softest adjustment, producing the smallest
  decline in performance**", while the NYSE-only screen, the market-equity screen and value
  weighting each cost about a third of the mean return [read in full]. The weak inference that
  supports: **the sub-$5 tail contributes less to published anomaly returns than the microcap tail
  does**, so the programme's $5 floor is the cheapest of the screens it imposes. S10's universe
  also excludes "penny stocks" explicitly [read in full]. That is the whole of the price evidence I
  could establish.
**Screen: partly usable. "Does it live in microcaps?" is the WRONG question on its own — it is
fatal for high-turnover signals and nearly free for annually rebalanced ones. The right question
is the interaction: turnover × illiquidity.**

### F5 — THE DATA REQUIRED IS ACCOUNTING FUNDAMENTALS, NOT PRICES
This is the finding with the sharpest operational consequence and nobody in the commissioning note
anticipated it. S1's post-2005 top-ten survivors, classified by what you need to compute them
[my classification of S1's Table 2, which I read in full]:

| survivor | raw LS %/mo | data needed | status for this programme |
|---|---|---|---|
| Cash-based operating profitability | 0.66 | Compustat annual/quarterly | **not free** |
| Operating profitability (R&D-adj) | 0.60 | Compustat, incl. R&D line | **not free** |
| Realized-implied vol spread | 0.59 | **options** | **excluded ground** |
| Off-season momentum | 0.54 | prices only | **excluded ground** (momentum + calendar) |
| Net external financing | 0.48 | Compustat cash-flow items | **not free** |
| Seasonal momentum (16yr+) | 0.48 | prices only, **but ≥16 years of history** | **excluded ground** (calendar); and the fixture spans 16.6 years |
| Gross profitability | 0.44 | Compustat | **not free** |
| R&D over market cap | 0.41 | Compustat R&D + price | **not free** |
| Net equity financing | 0.39 | Compustat | **not free** |
| Operating leverage | 0.38 | Compustat | **not free** |

**Seven of ten need accounting fundamentals; two of the three price-only survivors are on the
exclusion list; the tenth needs options. Zero are computable from permitted free daily price and
volume data.** S1's own category table says the same thing one level up: **Profitability is the
only category with a healthy median** (mean 0.25, median 0.24 %/month, 78% positive, N = 9), while
Value/Fundamentals is **−0.02 mean, −0.04 median, 47% positive** and Momentum is **0.01 mean, 53%
positive** [read in full]. S5's independent version: of their highest-*t* predictors, "almost all
of these outstanding predictors focus on **accounting data, analyst forecasts, or stock prices**…
almost none of them come from the more exotic data categories" [read in full].
**Screen: usable, and it is close to disqualifying. A free-price-data programme is shopping in the
one aisle the survivors are not in.**

### F6 — BREADTH: THE SURVIVORS ARE BROAD SORTS, NOT CONCENTRATED BASKETS
S1 drops any signal for which more than 5% of months through 2005 have **fewer than 20 stocks in
either leg**, and in post-2005 data sets the return to zero for any month with fewer than 20 per
leg — "effectively assuming that the investor **declines to trade due to insufficient
diversification**" [read in full]. The survivors are decile or quintile sorts of a 3,000-name
universe: hundreds of names per leg. S5 also reports that pairwise correlations among 205
predictors and among their long-short portfolio returns are **close to zero**, with the bulk of
portfolio-return correlations between −0.5 and +0.5 [read in full] — so the survivors are
individually broad *and* mutually diversifying.
**Screen: usable. "≥20 names per leg in ≥95% of bars" is S1's own operational rule and is directly
transplantable.** Against the programme's stated effective breadth of ~10 independent instruments
across 1,573 names, this is a caution rather than a comfort: S1's rule is about name counts, and
the literature says nothing about effective breadth at all.

### F7 — CAPACITY IS WHERE THE LITERATURE DISAGREES MOST, AND IT IS THE ONE AXIS THAT FAVOURS A SMALL ACCOUNT
S10's central claim is capacity: costs "an order of magnitude smaller" and fund sizes "more than an
order of magnitude larger" than prior studies, with value and momentum more scalable than size
[abstract read in full]. S3's measure is explicitly "the costs faced by a **small liquidity
demander**", ignores price impact, and is described by its authors as "**conservative, because it
assumes market orders**" [read in full]. S2 likewise omits price impact and says so in its abstract.
**The implication for a retail account is the one genuinely favourable asymmetry in this brief:
the cost-honest papers charge a small trader's cost and still find nothing, so their verdicts
already apply at retail scale — but equally, a retail account suffers no capacity penalty and the
"too small to matter" defence of published anomalies is unavailable to it.** Capacity cannot
rescue a 7 bp/month gross edge.

### F8 — WHAT THE SURVIVORS ARE NOT
Recorded because absence is evidence: among the strictest-bar survivors there is **no regime gate,
no calendar effect, no short-interest signal, no reversal, no lead-lag, no index-flow effect, no
order-flow proxy**. Every one of those is either in S4's 93%-fail liquidity category, in S3's
high-turnover panel with negative net returns, or on the programme's own exclusion list already.

---

## 5. SECTION 4 — THE MIRROR QUESTION, ANSWERED HONESTLY

**Does an observable feature separate the dead from the survivors?** Partly — and the honest answer
has three layers, the last of which is the uncomfortable one.

**(i) One observable feature discriminates on COST, and — this is the correction to the obvious
answer — IT DOES NOT DISCRIMINATE ON SURVIVAL.** Turnover orders the cost outcomes cleanly (S3's
whole taxonomy is built on it, §3.3), and it must, because the drag is roughly turnover × spread.
But S2's published out-of-sample test — sort anomalies on in-sample net return, in-sample net
Sharpe, or in-sample turnover, then measure post-publication-and-post-2005 net returns — concludes
"**none of the predictors produces a reliable pattern in expected returns**", with turnover entering
**with the wrong sign**: high in-sample turnover implied *higher* post-2005 net returns, and under
value weighting low-turnover anomalies produced *negative* ones [PEER-REVIEWED] [read in full].
**So the single feature a cost-focused programme would most expect to be a survival screen is not
one.** What does still discriminate, coarsely, is **category**: liquidity/trading-frictions signals
die (S4: 95 of 102), profitability survives (S1: the only category with a healthy post-2005 median),
and **holding period / data type** (F1, F5) remain usable as feasibility filters.

**(ii) One observable feature works in the WRONG DIRECTION for this programme.** S7's central
cross-sectional result: post-publication decline is **greater** for anomaly portfolios made of
stocks that are **large, liquid, high-dividend-yield and low-idiosyncratic-risk** — the 2013 draft
narrows this to low idiosyncratic risk; the 2012 draft lists all four [both read in full]. Their
reading is costly/limited arbitrage. S18 is the modern restatement: anomaly alphas persist where
retail investors trade against them, the authors reporting value-weighted two-year alphas of
**23%** on that subset [abstract only, treat cautiously]. S1's own mechanism paragraph says the
same: small and microcap stocks "have wider bid–ask spreads, lower institutional ownership, and
less analyst coverage, **all of which allow mispricings to persist**" [read in full].
**So survival and tradeability are NEGATIVELY related through the same variable.** The effects that
keep working are the ones nobody could cheaply arbitrage, which is also why this programme cannot
cheaply arbitrage them. This is the deepest structural finding in the lane and it is not a screen
you can pass — it is a constraint you are inside.

**(iii) Within the post-2005 investable universe, survival IS close to random, and the programme
should hear this plainly.** S1's dispersion diagnostic: the cross-sectional variance of anomaly
*t*-statistics post-2005 in the top-90% universe is **1.09** against a luck-only benchmark of 1.00,
implying a signal share of **1 − 1/1.09 ≈ 0.08**; for long-minus-market returns the variance is
**0.98 < 1**, so the estimated signal share is **zero** [read in full]. S2's independent version:
"Only 9% of *t*-stats exceed 2.0 in absolute value, not far from the 5% implied by a standard
normal. Thus, the data can be largely explained by the null of no predictability, and returns in
the right tail of the distribution are **mostly due to luck**" [read in full]. And S8 removes
the most appealing remaining discriminator: **where a predictor came from barely matters** —
29,000 mechanically mined accounting ratios and the peer-reviewed literature both retain ≈50% of
predictability post-sample, and predictors the literature attributes to *risk* **decay** post-sample,
while only the theory-agnostic 20% show signs of outperformance [read in full].

**Conclusion on the mirror question — and it is the answer the brief asked me to give if it were
true.** *Ex ante*, **category** and **feasibility features** (holding period, data type, leg
structure) are real discriminators. **Turnover is not** — it discriminates the cost drag and nothing
else, and in S2's published out-of-sample test it enters with the wrong sign. **And of who survives
the post-2005 gross-edge bar in a tradeable universe, the observable features explain almost
nothing: the surviving dispersion is statistically indistinguishable from luck, and the one feature
that does predict persistence — being expensive and hard to arbitrage — is the same feature that
makes an effect untradeable here.** S2 quantifies the ceiling directly: regressing post-pub-and-
post-2005 net returns on in-sample net returns for cost-mitigated implementations gives a slope of
**0.07 (SE 0.04) — a 93% decay** — so at the 90th-percentile in-sample net return of 91 bp/month the
implied expected return is **about 6 bps per month** [read in full]. That 6 bp figure is arrived at
by a completely different route from S1's empirical-Bayes 6 bp, and the agreement is the most
robust number in this brief.
**The only dissent on record is S6**, which finds that higher in-sample alpha does predict higher
out-of-sample alpha across factors and reads that as external validity in the time series [read in
full] — but S6 applies no costs and does not isolate post-2005. **I weight S1/S2 and record S6.**

**So: yes, survival is close to random with respect to observable features, once you condition on
the post-2005 investable universe.** The features that remain usable are **feasibility filters**
(can I hold it long enough, can I compute it, can I run the leg it needs) and **one category prior**
(profitability-like accounting characteristics out-survive everything else). **Beyond those, no
screen in this literature will tell the programme which future territory will work.** That is a line
of enquiry the programme can close, and it is the most important thing in this brief.

---

## 6. SECTION 5 — IS ANYTHING IN THE SURVIVING SET REACHABLE BY A RETAIL ACCOUNT ON FREE DAILY US DATA?

**No, as specified.** The chain is short and each link is sourced:

1. The survivors require a **holding period of months** (F1). A daily-bar, overnight-edge book at
   the programme's cost level would need ~16%/month gross (§3.4). Nothing in the literature
   delivers that post-2005.
2. Their post-2005 surviving return **lives in the short leg** (F3), which the programme has ruled
   out, and borrow fees alone take the cross-anomaly average from +0.14% to −0.01%/month
   [S14, abstract only].
3. Seven of the ten strongest post-2005 survivors need **Compustat-style fundamentals** (F5); two
   of the three price-only ones are on the programme's exclusion list; one needs options.
4. Even if all of that were solved, the surviving gross edge in a tradeable universe is **7 bp/month
   median, 25 bp/month for the best category, and 6 bp/month for the very strongest anomaly after
   selection-bias adjustment** [S1, read in full].

**The honest residual — three things, and I am not forcing them.**
- **The low-turnover / annual-rebalance shape is genuinely cheap at 33.8 bp/side.** A 2%/month
  turnover book pays ~1.6 bp/month all-in (§3.4). If the programme ever acquires free annual
  fundamentals for a dead-inclusive US panel, the cost objection to a profitability-style
  characteristic sort does not apply to it. That is a **data-acquisition** question, not a signal
  question, and it is the only door in this brief that is not locked.
- **The programme's measured cost is not the outlier it was treated as.** 33.8 bp/side is S2's own
  measured 68 bp effective spread, halved. Any future lane that was rejected *because* the
  programme's costs looked unusually high was rejected on a premise that the cost-honest literature
  does not support — the literature's own anomaly portfolios pay the same.
- **The $5 floor is the cheapest screen the programme imposes**, costing less mean return than an
  NYSE-only screen, a market-equity screen, or value weighting [S5, read in full]. If a future lane
  needs to relax a screen to gain breadth, the evidence says the floor is not where the return is.

---

## 7. CONFLICTS, RECORDED NOT ADJUDICATED

**7.1 HXZ vs JKP on whether the literature replicates (S4 vs S6).** 35%/64% insignificant vs
56.9% replicating on the same construction and 84.9% on theirs; +8.5 points of the gap is capped
value weighting alone; JKP report near-equal replication rates in mega (77.3%) and micro (81.5%)
caps [both read in full]. **I weight neither for this lane** — neither applies costs, and the
cost-and-era bar (S1, S2) collapses the answer either way. Both stay on the record.

**7.2 Chen–Welch vs Blitz et al. on the short leg (S1 vs S11).** S1: post-2005, top-90% universe,
long-minus-market dispersion is *below* the luck benchmark, so long-only survivor returns shrink to
zero. S11: 1963–2018 Fama–French legs, long legs carry significant alpha and short legs are
spanned (p = 0.87). **They are not measuring the same statistic**: S1 benchmarks the long leg
against the *raw market return*; S11 regresses each leg on the *opposite legs of the other factors*
and reports Sharpe ratios of long-only legs that retain full market exposure. **They also disagree
on sample**: S1 is post-2005 only, S11 is 55 years dominated by the pre-2006 era, and neither
applies trading costs to the leg decomposition. **I weight S1 for the post-2010 question and record
S11**, noting its authors are Robeco Quantitative Investments and that its conclusion is the one a
long-only factor manager would want.

**7.3 HXZ vs Chen–Welch on the liquidity category (S4 vs S1).** 95 of 102 liquidity variables
insignificant under NYSE-breakpoint value weighting, vs "Trading / Liquidity" having the highest
positive share (85%, N = 13, median 0.11%/month) of any category post-2005 in the top-90% universe.
Different universes, different samples, different category definitions (S1 uses S5's
classification), and S1's N is 13. **I weight S4's verdict on the category and note S1's cell as an
unexplained residual** — a 13-name cell in a cross-section whose overall signal share is 0.08 is
not evidence of a live liquidity effect.

**7.4 Frazzini–Israel–Moskowitz vs Novy-Marx–Velikov / Chen–Velikov on the level of costs (S10 vs
S3, S2).** An order of magnitude apart, and both sides state why: patient institutional limit
orders in a microcap-free universe vs the effective spread faced by a small liquidity demander
assuming market orders. **For this programme I weight S3/S2**, because the programme is the trader
S10 explicitly says its number does not describe. S10 stays on the record as the reason a patient
execution study could change the 33.8 bp/side — which is excluded ground here.

**7.5 Jacobs–Müller's international null (S9) vs the whole US decay literature.** The US is the
only one of 39 markets with reliable post-publication decay. If the mechanism is arbitrage capital,
then a US-only, post-2010, cost-honest test is the single most hostile environment in the world for
a published anomaly. Recorded as bad news, not adjudicated.

**7.6 DeMiguel et al. (S15) is the only paper where net-of-cost survival goes UP**: transaction
costs raise the number of jointly significant characteristics from **6 to 15** because rebalancing
trades across characteristics cancel [snippet only, from a search summariser — I downloaded the PDF
and did not read it]. This works **only through signal combination**, which is permanently excluded
ground for this programme, so it cannot be used here. Recorded for completeness and flagged as the
weakest-established number in the brief.

---

## 8. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **Four documents were refused, logged by tool and response, not by host.**
   (a) `WebFetch` → **HTTP 403 Forbidden** on `papers.ssrn.com/sol3/papers.cfm?abstract_id=4338007`
   (Assaying Anomalies) and on `onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12365`
   (McLean–Pontiff JF 2016). (b) `curl` GET, UA `K6-research/1.0 (research@backtest-framework.org)`
   → **HTTP 403, 5,711-byte HTML body** on `papers.ssrn.com/sol3/Delivery.cfm/4266059.pdf` and
   **HTTP 403, 5,599-byte HTML** on `onlinelibrary.wiley.com/doi/pdf/10.1111/jofi.13501`
   (Muravyev et al.). (c) `curl` → **HTTP 403** on the Oxford-Man slide deck
   `oxford-man.ox.ac.uk/.../MihailVelikov_OMI_Slides.pdf`. (d) **Two HTTP 200s that were wrong:**
   `rnm.simon.rochester.edu/research/AA.pdf` and `.../MCwTC.pdf` each returned **200 with a
   19,490-byte `text/html` faculty landing page**, not a PDF — caught by `file`, not by status.
   **Consequence: every Muravyev number in this brief is [abstract only] via a summariser, and the
   Assaying Anomalies protocol — the one published artefact that is literally a screen for candidate
   signals — I could not read at all.** If one document is worth re-attempting with other access,
   it is Novy-Marx & Velikov, *Assaying Anomalies* (JEL 2024/25; SSRN 4338007).
2. **The PRICE distribution of the survivors is not established anywhere in this brief, and I could
   not establish it.** The cost-honest literature screens and reports on **size, liquidity, spread
   and turnover** — not nominal share price. The brief's "size is not price" instruction therefore
   cannot be satisfied from these sources. All I have is S5's finding that a $5 price screen costs
   the least mean return of the liquidity adjustments tested [read in full], and S10's statement
   that its universe excludes penny stocks [read in full]. **I did not find a single paper reporting
   the median or distribution of nominal share price in an anomaly's long or short leg.** Anyone who
   needs that will have to measure it.
3. **I read figures as extracted text, not as images.** S2's Figure 4 (spread distributions), S1's
   Figures 1–3 and S5's Figure 9 (performance by liquidity screen) were established from the
   surrounding prose and captions, which state the numbers I quote. I did not view the plotted
   series and cannot confirm a number that appears only in a plotted curve.
4. **A working-paper version of S2 contradicts the published version on a load-bearing result, and I
   caught it only by reading both.** FEDS 2020-039 (120 anomalies) states "only turnover seems to
   produce a reliable improvement in mean returns" with a value-weighted top quartile of 9.7 bp/month;
   JFQA 2023 (204 anomalies) states "none of the predictors produces a reliable pattern" and that
   turnover enters **with the wrong sign**, with low-turnover anomalies producing negative net returns
   under value weighting [both read in full]. **The published version governs everywhere in this
   brief.** I flag it because the draft is the freely-indexed one and its wording is the one a search
   returns.
5. **The S4 and S7 numbers I read are from working-paper versions, not the published articles.**
   S4: w23394 (447 anomalies, 286/64% insignificant) vs the RFS abstract's 452/65%/82%, which is
   [snippet only]. S7: the 2012 and 2013 drafts (82 characteristics, ~10% out-of-sample / ~35%
   post-publication) vs the published 97 characteristics and 26%/58%, which I have only as a
   **verbatim quotation inside S6** — a paper I read in full, but still a second-hand route to a
   first-hand number.
6. **Chen & Welch (S1) is an unrefereed July-2026 draft and is not independent of S2 or S5.**
   A. Y. Chen is an author of S1, S2, S5 and S8. Four of my most load-bearing findings therefore
   share one author and one dataset (openassetpricing.com). The post-2005 collapse is corroborated
   across different bars (gross-in-large-caps, net-of-spread, post-publication) but **not by an
   independent research group using independent portfolio construction**. That is the single largest
   fragility in this brief.
7. **No source I read tests the programme's actual configuration**: daily bars, dead-inclusive with
   ~35.7% dead names, equal-weighted, $5 floor plus a dollar-volume screen, 2010-01-04 onward.
   S1's universe (top 3,000 / top 90% of cap, 2006+) is *larger and more liquid* than that; S2's is
   the full CRSP cross-section including microcaps. **The programme's universe sits between S1's two
   headline cells (7 bp and 19 bp median, post-2005) and I cannot say where.** I did not interpolate
   and nobody should.
8. **Survivorship and delisting treatment in the anomaly datasets is unexamined here.** S5's
   reproduction follows original papers; none of the cost-honest papers I read discusses
   dead-name inclusion in the terms this programme uses. Whether a 35.7%-dead panel changes any of
   these verdicts is **unknown and untested**.
9. **S13 is slides, not the paper.** "Implementation costs eliminate returns to momentum and sharply
   reduce returns to value" and the FIM/NMV comparison table (UMD net −0.77%/yr in FIM's own
   1986–2013 sample) are from the authors' December 2018 presentation, which I read; I did not read
   the JFE article and the published numbers may differ.
10. **Nothing in this brief was instruction-following from a fetched document.** One downloaded PDF
   (the 2012 Frazzini–Israel–Moskowitz draft, `K6_fim_anomalies.pdf`) carries the line **"Not for
   quotation"** on its title page. I treated that as data, did not act on it as an instruction to me,
   and independently chose not to quote that draft — every FIM figure above comes from the 2018
   *Trading Costs* paper I read in full, or from S3's published description of the 2014 version, or
   is tagged [snippet only]. No other fetched page contained text addressed to the reader as an
   agent.

---

## 9. THE SCREEN, AS A CHECKLIST

What a future territory must satisfy, derived only from the survivor properties above. Questions 1–4
are ex-ante answerable from a territory description before any code is written.

| # | question | pass condition | evidence |
|---|---|---|---|
| 1 | **What is the one-sided monthly turnover?** | **< ~10%/month**, i.e. average holding ≥ 3 months. Above 50% the published survivors are essentially nil. **Necessary, not predictive** — S2's published test has turnover entering with the wrong sign on post-2005 net returns | F1; S3, S2 |
| 2 | **Is the signal a persistent characteristic or a dated event?** | characteristic. Dated events survive only at mid-turnover and their net *t* runs 0.7–2.4 | F2; S3, S2 |
| 3 | **Does the documented edge need a short leg?** | must not. If it does, the post-2005 evidence says **what is left is only in that leg** — raise the flag and stop | F3; S1, S14, S12 (vs S11) |
| 4 | **What data computes it?** | must be free daily price/volume. Seven of S1's ten survivors need Compustat; this is where the survivor set and a free-data programme fail to intersect | F5; S1, S5 |
| 5 | **Does the edge survive the interaction of turnover and illiquidity — not size alone?** | low-turnover signals are ~free even in microcaps; high-turnover signals invert in them | F4; S3 Table 13 |
| 6 | **≥ 20 names per leg in ≥ 95% of bars?** | S1's own operational rule; below it they set the return to zero | F6; S1 |
| 7 | **Is the gross edge per round trip > ~70–80 bp?** | at 33.8 bp/side plus 50/P commission. State it per round trip, never per month, so the holding period is forced into the open | §3.4 |
| 8 | **And then: is there any reason to believe this one is not luck?** | the post-2005 cross-section of ~200 published anomalies has a signal share of ~0.08 and its long-only component ~0. Anything in the right tail needs a reason beyond its own backtest | §5(iii); S1, S2, S8 |

**Question 8 is the one this lane would add to the programme's habits.** Questions 1–7 are screens
a territory can pass. Question 8 is the finding that passing them is not sufficient, and it is the
reason the answer to the commissioning question is: **the survivors do share usable features, and a
territory satisfying all of them would still most likely be luck.**
