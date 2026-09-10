# `B1` — THE BENCHMARK QUESTION: AGAINST WHAT SHOULD A LONG LEG BE MEASURED?

**Round 2 of `Scan-100926`.** Lane `B1` of four. Contract, inherited exclusions and the rules this
brief carries: [`00-SCHEMA.md`](00-SCHEMA.md). Slate: [`R2-00-slate.md`](R2-00-slate.md). The two
lanes whose conflict this lane was commissioned to resolve:
[`R1-02`](R1-02-persistent-characteristics.md) (`A2`) and [`R1-03`](R1-03-the-long-only-problem.md)
(`A3`).

Under [R15](../../RULES.md#r15) **nothing here closes or admits anything.** No number below was
measured on this programme's fixture. Figures restated from our own record (33.8 bp/side, 67.6 bp
round trip, ~1,573 names, ~10 effective instruments) are quoted, not recomputed. My own measurements
on public data are tagged **`[MEASURED IN BRIEF]`** and are re-runnable from
[`data/B1_ew_vs_vw_benchmark.py`](../../../data/B1_ew_vs_vw_benchmark.py) with its output at
[`data/B1_ew_vs_vw_benchmark.txt`](../../../data/B1_ew_vs_vw_benchmark.txt).

**Scope boundary.** Benchmark choice is this lane's subject. **Choosing a weighting scheme is
excluded ground** (position sizing and portfolio construction), and so is the equal-weight
rebalancing bias. Weighting appears below only where the literature's benchmark *is* defined by a
weighting scheme — which, it turns out, is nearly everywhere.

---

## 0. THE ANSWER, STATED BEFORE THE EVIDENCE

**The bar was a stated recommendation with reasoning, or an explicit finding that the literature does
not justify its benchmark choices. I reached BOTH, and they point the same way.**

> **The leg-decomposition literature splits cleanly in two. The papers that construct a benchmark
> FOR A LEG justify it explicitly, at length, and choose something close to `A2`'s
> name-weighted universe — Blitz et al. build a 50/50 Big/Small hedge precisely because "all the
> results would be distorted by the size effect" otherwise, and DGTW match on characteristics on
> purpose. The papers that SUBTRACT THE MARKET from a leg inherit it in silence. Chen & Welch, whose
> −0.04%/month anchors `A3`, define the benchmark in one clause of a table note — *"the raw
> Fama-French market return, computed as Mkt - RF plus RF"* — and nowhere state the weighting of the
> legs they subtract it from. Their dataset's documented default is equal-weighted.**

**And the arithmetic settles the conflict in a way neither lane will fully like.** The whole
disagreement is one identity:

```
(leg − VW market)  =  (leg − EW universe)  +  (EW universe − VW market)
                          [selection]           [weighting / size]
```

I measured the second term on Ken French's free data, with a positive and a negative control
`[MEASURED IN BRIEF]`. Over **2010-01 → 2026-07**, a name-weighted universe minus the CRSP
value-weighted market is **−0.262 %/mo (t = −1.32)** over all CRSP names, **−0.074 %/mo (t = −0.53)**
over the largest 1,573 names, and **−0.103 %/mo (t = −1.19)** over the top 90% of market cap. Over
1963–2018 the same term is **+0.13 to +0.24 %/mo and positive at t ≈ 2**. **The sign of the
benchmark disagreement flipped in the era this programme trades.**

Four consequences, in order of how much they change what the programme should do.

1. **`A3`'s Var(t) = 0.98 does not survive. `A3`'s mean does.** The mismatched benchmark injects a
   series with **monthly sd of 1.2 – 2.8%** into *every* leg. Feeding that into `A2`'s own numbers
   predicts a long-minus-market Var(t) of **0.76 to 1.19** where `A3` observed **0.98** (§4.3). **A
   sample Var(t) below the luck null is what a mismatched benchmark looks like, not what an absent
   signal looks like.** But the *mean* barely moves: in a screened universe the benchmark switch is
   worth **+1 to +10 bp/month**, which turns `A3`'s −4 bp into roughly **zero**, not into `A2`'s
   +44 bp.
2. **On the one signal where both lanes have a number, the benchmark is irrelevant.** Cash-based
   operating profitability: `A2` measures **+44 bp/month** long leg against its own universe;
   `A3`'s own source measures **+0.40 %/month** long-minus-VW-market for the same signal
   (Chen & Welch Table 2, verified by me from the PDF). **Two benchmarks, 4 bp apart. The
   profitability long-leg result is not a benchmark artefact in either direction.**
3. **The feared circularity is real, but it lives in DGTW, not in the universe benchmark.** DGTW say
   so themselves, in print: their measure *"assigns no significant abnormal performance to those
   investors who simply follow the same mechanical characteristic-based strategy over the entire time
   period. This is true even if that strategy did extremely well."* A universe benchmark removes the
   universe's own return — a decomposition, not a circularity — and in 2010–2026 the thing it removes
   is **negative**, so it flatters rather than hides.
4. **For an absolute-return, cash-funded book, subtracting an equity benchmark is the wrong
   operation, and the primary source says why.** Sharpe (1994): *"the differential return corresponds
   to the payoff obtained from a unit investment in the fund, financed by a short position in the
   benchmark."* This book is financed by **cash**. Its hurdle is the risk-free rate; the equity
   benchmark is a **risk control**, not a competitor, and belongs beside the number rather than
   inside it.

**The recommendation, in one line: report the identity, both terms, never one — and for the
programme's own signal criterion, the correct "benchmark" is the null distribution it already
builds, because a within-universe null IS `A2`'s benchmark with a p50 and a p95 attached.** §8.

---

## 1. SOURCES, TYPE AND HOW WELL ESTABLISHED

Every figure below is tagged in the same sentence it appears in. **No asset-manager marketing
document is used as evidence for a return anywhere in this brief.**

| # | source | type | established |
|---|---|---|---|
| **S1** | **Daniel, Grinblatt, Titman & Wermers, *Measuring Mutual Fund Performance with Characteristic-Based Benchmarks*, JF 52(3) 1997, 1035–1058.** PDF from Wermers' own site | [PEER-REVIEWED] | **[read in part]** — the PDF is **image-only** (24 scanned TIFF pages; `pdftotext` returns **0 bytes**, `pypdf` returns 0 characters). I extracted each page's TIFF with `pypdf`, rendered it to PNG with Pillow and read pages **1039, 1041, 1042, 1043, 1047, 1056, 1057** as images. Title verified on the running head of every page read |
| **S2** | **Cremers, Petajisto & Zitzewitz, *Should Benchmark Indices Have Alpha? Revisiting Performance Evaluation*, Critical Finance Review 2, 2012/2013, 1–48.** Author-hosted copy (petajisto.net) | [PEER-REVIEWED] | **[read in full]** — text extracted locally. **Table 7's layout extraction is garbled and I quote from it only what the paper's own prose confirms** |
| **S3** | **Blitz, Baltussen & van Vliet, *When Equity Factors Drop Their Shorts*, FAJ 76(4) 2020, 73–99.** Open-access accepted manuscript from the Erasmus University repository | [PEER-REVIEWED] but **all three authors are Robeco Quantitative Investments — interested, and interested IN FAVOUR of long-only** | **[read in full]** — this is the full text `A3` was refused (`A3` §10). Table 1 and **Table A2 re-extracted with `pypdf` after the layout extraction shuffled rows** |
| **S4** | **Benaych-Georges, Bouchaud & Ciliberti, *Equity Factors: To Short Or Not To Short, That Is The Question*, arXiv 2003.10419v3, 6 Apr 2021** | [WORKING PAPER], **Capital Fund Management — interested AGAINST long-only** | **[read in full]** |
| **S5** | **Chen & Welch, *What Useful Alphas?*, arXiv 2607.06502v1, 7 Jul 2026** | [WORKING PAPER], unrefereed | **[read in relevant part]** — abstract, §2 (universe filters), Table 2 and its note, Figure 1 note, Appendix A |
| **S6** | **Muravyev, Pearson & Pollet, *Anomalies and Their Short Sale Costs*, 1 Sep 2022 draft hosted by HEC Montréal; published JF 80(6) 2025** | [WORKING PAPER] for the text read; the article is [PEER-REVIEWED] | **[read in relevant part]** — §3 benchmark construction **verbatim**, Table 5 (all three panels) re-extracted independently of `A3` and **matching `A3`'s transcription exactly**, and §4.4's benchmark-robustness claim |
| **S7** | **Hou, Xue & Zhang, *Replicating Anomalies*, RFS 33(5) 2020, 2019–2133.** Author-hosted published version (global-q.org) | [PEER-REVIEWED] | **[read in relevant part]** — §1 and §2.2 *"Reliable procedures that control for microcaps"* **verbatim** |
| **S8** | **Stambaugh, Yu & Yuan, *The short of it: Investor sentiment and anomalies*, JFE 104(2) 2012, 288–302.** Copy hosted by **AQR** — interested host, not their paper | [PEER-REVIEWED] | **[read in relevant part]** — §3.3 and eq. (1)/(2) **verbatim** |
| **S9** | **Jensen, Kelly & Pedersen, *Is There a Replication Crisis in Finance?*, NBER w28432; published JF 78(5) 2023** | [WORKING PAPER] for the bytes read | **[read in relevant part]** — the capped-value-weight justification and §III.A construction, **verbatim**. **NBER title checked against the campaign's known "NBER URL returns a different paper" failure: the running title is correct** |
| **S10** | **Chen & Zimmermann, *Open Source Cross-Sectional Asset Pricing*, FEDS 2021-037 (Federal Reserve Board)** | [WORKING PAPER] doubling as the [SOFTWARE DOC] for the dataset `A2` and `A3` both use | **[read in relevant part]** — §2.3 construction defaults and §5.2 liquidity adjustments |
| **S11** | **Sharpe, *The Sharpe Ratio*, Journal of Portfolio Management, Fall 1994.** Author's own Stanford page | [PEER-REVIEWED] | **[read in full]** — fetched and **stripped to text locally**, because an earlier summariser pass on the same page returned a paraphrase I could not use under this campaign's rules |
| **S12** | **Bessembinder, *Do Stocks Outperform Treasury Bills?*, JFE 129(3) 2018, 440–457.** The only free copy I found is hosted by a **retail-investing blog** | [PEER-REVIEWED] article; **host is uninvolved and unverified** | **[read in relevant part]** — bytes verified as the **May 2018 "Forthcoming, JFE" accepted manuscript** with the correct author and affiliation block; §1 read in full |
| **S13** | **Wermers' DGTW benchmark download page**, University of Maryland, *"Updated October 8, 2013"* | [SOFTWARE DOC] | **[read in full]** — the page's own text; **I did not download the data files** (§5) |
| **S14** | **Kenneth French's data library** | [SOFTWARE DOC] | **[index read in full; two files downloaded and used]** — `F-F_Research_Data_Factors` and `Portfolios_Formed_on_ME`, both stating they were built from the **202607 CRSP database** |
| **S15** | **Plyakha, Uppal & Vilkov, *Equal or Value Weighting? Implications for Asset-Pricing Tests*** | [WORKING PAPER] | **[abstract only, via a search summariser — weaker than `[snippet only]`]**. Its mechanism is the **equal-weight rebalancing bias**, which is **excluded ground**. Named as a boundary marker, **no figure taken** |
| **M1** | **My own measurement on `S14`'s free data** | **[MEASURED IN BRIEF]** | script, controls and output committed to `data/` |

---

## 2. SUB-QUESTION 1 — WHAT THE LEG-DECOMPOSITION LITERATURE ACTUALLY USES, AND WHETHER IT JUSTIFIES IT

**The literature divides on exactly one line: whether the author had to BUILD a benchmark for a leg,
or could reach for one that already existed.** Those who build, justify. Those who reach, do not.

### 2.1 The papers that JUSTIFY — and both choose something close to `A2`'s benchmark

**`S3` Blitz, Baltussen & van Vliet (2020) [PEER-REVIEWED, Robeco-interested] [read in full].** Their
benchmark for a leg is a **50/50 Big/Small portfolio**, not the market, and they say why in as many
words:

> *"A natural candidate for the neutral hedging portfolio would be the cap-weighted market portfolio.
> With that choice, however, all the results would be distorted by the size effect because the long
> leg is 50% long in small-cap stocks and the short leg is 50% short in small-cap stocks. To prevent
> such size distortions, using the two components of the Fama and French (2015) SMB (small minus big)
> factor, we defined the neutral hedging portfolio as 50% large-cap stocks (Big) plus 50% small-cap
> stocks (Small)."*

and again in the note to their Table 1:

> *"In Panels A and B, each leg is an equal 50/50 combination of the large-cap and small-cap portions,
> minus the market (50/50 Big/Small portfolios), to neutralize market and size tilts."*

**This is the strongest justification in the literature for benchmarking a leg against a
composition-matched universe rather than against the cap-weighted market, and it is the same argument
`A2` made.** They also acknowledge the construction's own bias — *"the standard 2×3 Fama-French
construction methodology, which gives a disproportionately high weight to small-cap stocks"* — and
test four benchmark/weighting combinations because of it (§3.2).

**`S1` DGTW (1997) [PEER-REVIEWED] [read in part].** The canonical characteristic-matched benchmark,
defined verbatim on p. 1041:

> *"The CS measure uses as a benchmark the return of a portfolio of stocks that is matched to the
> fund's holdings each quarter along the dimensions of size (market value of equity), book-to-market
> ratio, and momentum (the prior year return of the stock). … A CS measure of zero tells us that the
> performance of a fund could have been replicated, on average, by simply purchasing stocks with the
> same size, book-to-market, and momentum characteristics as the stocks that the fund held"*

with the weighting justified in footnote 14:

> *"We use NYSE-based breakpoints to determine the quintiles, and we value-weight the stocks within
> each of the 125 passive portfolios to avoid biases in computed returns from rebalancing and to
> avoid placing too much weight on extremely small stocks."*

**Note what that footnote does: the benchmark cells are value-weighted while the portfolio being
evaluated need not be.** That mismatch is the same one at issue between `A2` and `A3`, sitting inside
the canonical characteristic-matched benchmark itself.

**`S6` Muravyev, Pearson & Pollet [WORKING PAPER draft] [read in relevant part]** justify their
variant explicitly and at length — they exclude high-fee stocks from the benchmark *"because we are
interested in identifying the impact of stock borrow fees on the portfolio returns"*, and state the
construction precisely: *"The abnormal return on stock i in month t is the difference between the
return on stock i and the average value-weighted return on the matched benchmark portfolio during the
same month."* **They then test whether it matters** — the one paper in this set that does:

> *"the close similarity between the results for raw and abnormal returns show that the results and
> conclusions are not driven by the choice to of benchmark to use to compute the abnormal returns."*

(the garbled "to of" is in the draft). §4.2 below shows that claim holds when I re-derive their long
leg against `A2`'s benchmark from their own published table.

### 2.2 The papers that INHERIT — including the one `A3`'s verdict rests on

**`S5` Chen & Welch [WORKING PAPER] [read in relevant part].** The entire definition of the benchmark
whose subtraction produces −0.04%/month is one clause in the note to Table 2:

> *"Mean Long - Mkt is the mean signal-month return of the long leg minus the raw Fama-French market
> return, computed as Mkt - RF plus RF."*

**There is no sentence anywhere in the paper defending that choice, and no statement of how the legs
are weighted.** The paper is not careless about such choices in general — it devotes a full appendix
paragraph to defending its *shrinkage target* (*"It is not clear what one should shrink toward: the
cross-sectional mean or just zero. The mean is not a neutral target."*). **It applies that scepticism
to the shrinkage target and not to the benchmark.** The dataset it uses, `S10`, documents its own
default: *"our baseline portfolios follow the original papers as much as possible … as most of them
are equal-weighted"*. **So the anchor number for `A3` is, on the documented default, an
equal-weighted leg minus a value-weighted market, with the mismatch unremarked.**

**`S8` Stambaugh, Yu & Yuan (2012) [PEER-REVIEWED, AQR-hosted copy] [read in relevant part]** — the
canonical leg-decomposition paper. Legs are **value-weighted deciles**; the leg's benchmark is a
**regression**, not a subtraction:

> *"the benchmark-adjusted return is defined as the sum of aᵢ and the fitted value of εᵢ,ₜ in the
> regression Rᵢ,ₜ = aᵢ + bMKTₜ + cSMBₜ + dHMLₜ + εᵢ,ₜ"*

with the weighting given one clause: *"Our primary focus is on value-weighted returns, as they better
reflect economically significant magnitudes."* **That is an assertion about which dollar matters, not
an argument about what a leg should be compared with.**

**`S9` Jensen, Kelly & Pedersen [WORKING PAPER] [read in relevant part]** justify their *weighting*
in detail (§2.3) and dispose of the *benchmark* in half a sentence: *"Finally, we compute each
factor's β̂ᵢ via an OLS regression on a constant and the corresponding region's market portfolio."*

**`S7` Hou, Xue & Zhang [PEER-REVIEWED] [read in relevant part]** likewise justify weighting, never
the benchmark:

> *"When forming portfolios, many studies equal-weight returns. We instead focus on value-weighted
> returns. First, value-weighting accurately reflects the wealth effect experienced by investors
> (Fama 1998). Second, microcaps are influential in equal-weighted returns."*

**The finding, stated plainly: the literature's stated justifications are overwhelmingly about
WEIGHTING THE TEST PORTFOLIO, and the argument offered is an aggregate-wealth argument — which dollar
the average investor holds. That argument has no purchase on a single absolute-return book, which is
not the average dollar and does not hold the market.** §6.

---

## 3. SUB-QUESTION 2 — THE ARITHMETIC OF THE ALTERNATIVES

### 3.1 The identity, and the one property that decides everything

For a leg `L`, a benchmark `H` and a short leg `S`:

```
L − H₁  =  (L − H₂) + (H₂ − H₁)          a benchmark change is an ADDITIVE SHIFT on a leg
(L − H) − (S − H)  =  L − S              a benchmark CANCELS in a long-short spread
```

**Everything the literature argues about legs is a consequence of the second line.** A long-short
paper can be careless about its benchmark because the benchmark is not in its answer. **A leg paper
cannot.** `S3`'s own Table A2 demonstrates it empirically: swapping the hedge portfolio from
"50/50 Big+Small" to "50/50 neutral portfolios" moves the combined **long-leg Sharpe from 1.10 to
0.95** and the **short-leg from 0.69 to 0.49**, while the **long–short Sharpe is 0.86 in both
panels — identical to two decimals**. Same again in their cap-weighted panels: long 0.81 vs 0.88,
short 0.41 vs 0.32, **long–short 0.67 in both**.

### 3.2 The five alternatives, side by side

| benchmark | what it holds constant | what it gives up | what it does to a reported LONG-LEG alpha |
|---|---|---|---|
| **long − VW market** | the aggregate wealth of all equity investors; a tradeable, cheap, shortable instrument | the leg's own weighting and size composition; **imposes β = 1** | Adds the whole **weighting/size term** into the alpha. `[MEASURED IN BRIEF]`: **−0.07 to −0.26 %/mo in 2010–2026**, **+0.10 to +0.24 %/mo in 1963–2018**. Sign flips by era |
| **long − EW market** | the return of the average *name* in the whole market | the universe screen — includes microcaps the book cannot trade | Between the two above. On all CRSP names the EW/VW gap is the full **−0.262 %/mo** (2010–2026) |
| **long − its own name-weighted universe** (`A2`) | universe, screen, weighting, and **β ≈ 1 by construction** | the **entire size/illiquidity/weighting premium**, whatever its sign; is **not a tradeable instrument** | Isolates **selection only**. This is the *cleanest* estimate of what the signal adds and the *least complete* estimate of what the book earns |
| **long − risk-free** | nothing about equities; measures the return on capital deployed | all risk adjustment; every result becomes a beta bet | The honest **absolute-return** number. In 2010–2026 an EW hold of the largest 1,573 names earned **1.128 %/mo** gross of costs while the VW market delivered **1.202 %/mo** `[MEASURED IN BRIEF]` |
| **long − characteristic-matched (DGTW)** | size, book-to-market and momentum, jointly, at the name level | **the premium on the matched characteristics, by design** (§7); needs book equity for every name | Removes any part of the long-leg return that is a size/value/momentum tilt. `S6`'s D10 is **−0.09 %/mo [−1.81]** under it and **+0.7 bp/mo** under `A2`'s benchmark on the same table (§4.2) |
| *(a sixth, used by `S8`/`S9`)* **regression alpha** | estimated factor loadings rather than an imposed β = 1 | interpretability as a tradeable spread; adds estimation error | `[MEASURED IN BRIEF]`: the name-weighted universe's **β on the VW market is 1.05–1.20**. Forcing β = 1 in a rising market **understates** the benchmark: for the largest-1,573 universe over 2010–2026 the raw gap is **−0.074 %/mo** but the CAPM alpha is **−0.255 %/mo (t = −1.91)** |

### 3.3 Where the literature quantifies the gap between two benchmarks on the SAME data

**This is the most valuable class of number in the lane, so each is given with its exact scope.**

| source | what was swapped | same-data effect |
|---|---|---|
| **`S3` Table A2** [read in full] | hedge portfolio 50/50 Big+Small → 50/50 neutral, legs unchanged, 1963–2018 | combined **long-leg Sharpe 1.10 → 0.95** (−14%); short leg **0.69 → 0.49** (−29%); **long–short unchanged at 0.86** |
| **`S3` Table A2** [read in full] | 2×3 legs minus EW(Big,Small) → cap-weighted legs minus cap-weighted market | long **1.10 → 0.81**, short **0.69 → 0.41**, long–short **0.86 → 0.67** |
| **`S2` conclusion** [read in full] | Carhart/FF alpha → index-based benchmark, small-cap vs large-cap mutual funds, 1980–2005 | *"adjusting for the benchmark index has a drastic **5% per year** impact on their Carhart and Fama-French alphas, **reversing the conclusions** about how average manager skill differs between small- and large-cap funds"* |
| **`S2` Table 2** [read in full, prose-confirmed] | none — these are **passive indices** scored by a standard model | S&P 500 **+0.82 %/yr (t = 2.78)**, Russell 1000 **+0.47%**, Russell 2000 **−2.41 % (t = −3.21)**, S&P 600 **−2.59%**; long S&P 500 Growth / short Russell 2000 Growth **+5.23 %/yr (t = 4.23)**. **A no-skill portfolio can be handed ±1–2.5 %/yr of "alpha" by benchmark choice alone** |
| **`S7` §1** [read in relevant part] | NYSE breakpoints + VW → NYSE-Amex-Nasdaq breakpoints + EW, 452 anomalies, original samples | replication failure rate **65.3% → 43.1%** |
| **`S10` §1** [read in relevant part] | baseline (mostly EW, original-paper screens) → VW **or** the NYSE-20 size screen, 205 predictors | in-sample mean long-short return **about 30% lower, ≈ 20 bp/month** |
| **`S9` §1** [read in relevant part] | pure value weights → capped value weights (winsorised at the NYSE 80th percentile) | **+8.5 percentage points** on the replication rate |
| **`S1` Table II** [read in part] | CRSP VW vs CRSP EW, the two candidate market benchmarks, annual returns | **14.98% vs 19.73%/yr (1975–94)**; **16.06% vs 26.97% (1975–84)**; **13.89% vs 12.48% (1985–94)** — **the gap between the two market benchmarks reversed sign between the two decades** |
| **`M1`** `[MEASURED IN BRIEF]` | VW market → name-weighted universe, monthly | see §3.4 |

### 3.4 `M1` — the benchmark gap, measured

**Endpoints** (free, keyless, downloaded 2026-09-10, both stating they were built from the **202607
CRSP database**): `F-F_Research_Data_Factors_CSV.zip` and `Portfolios_Formed_on_ME_CSV.zip` from
Kenneth French's data library. **VW market** = `Mkt-RF + RF`. **Name-weighted universe** =
`Σᵢ nᵢ·rᵢᴱᵂ / Σᵢ nᵢ` across the ten ME deciles, from French's own "Average Equal Weighted Returns"
and "Number of Firms in Portfolios" — **exactly the construction `A2` used**, on public data.

**Controls, because a harvest without one is not a measurement.** *Positive:* cap-weighting the
deciles' **value**-weighted returns must reproduce the CRSP VW market — it does, to **+0.0044 %/mo
mean deviation, 0.258 %/mo maximum, sd 0.056 %/mo**. *Negative:* the "≤ 0 market equity" bucket must
be empty and flagged — it holds **0 firms in all 199 months** and carries French's **−99.99** missing
code throughout. Both assert in the script.

| universe (name-weighted) | mean %/mo | **minus VW mkt** | se | t | **sd of the gap** | CAPM α | t(α) | β |
|---|---|---|---|---|---|---|---|---|
| **2010-01 → 2026-07** (VW mkt 1.202 %/mo, N = 199) | | | | | | | | |
| all CRSP names (avg 3,574) | 0.941 | **−0.262** | 0.198 | −1.32 | **2.80** | −0.451 | −2.28 | 1.174 |
| largest 1,573 names | 1.128 | **−0.074** | 0.139 | −0.53 | **1.96** | −0.255 | −1.91 | 1.167 |
| top 90% of market cap | 1.099 | **−0.103** | 0.087 | −1.19 | **1.22** | −0.160 | −1.81 | 1.052 |
| ME deciles 4–10 | 1.110 | −0.092 | 0.132 | −0.70 | 1.86 | −0.257 | −2.02 | 1.152 |
| **2006-01 → 2026-07** (N = 247) | | | | | | | | |
| all CRSP names | 0.802 | **−0.191** | 0.181 | −1.06 | 2.84 | −0.360 | −2.06 | 1.198 |
| largest 1,573 names | 0.981 | **−0.012** | 0.131 | −0.09 | 2.05 | −0.178 | −1.48 | 1.195 |
| top 90% of market cap | 0.938 | **−0.054** | 0.088 | −0.61 | 1.38 | −0.133 | −1.56 | 1.093 |
| **1963-07 → 2018-12** (N = 666) | | | | | | | | |
| all CRSP names | 1.138 | **+0.240** | 0.119 | **+2.03** | 3.06 | +0.178 | 1.52 | 1.120 |
| largest 1,573 names | 1.065 | **+0.167** | 0.074 | **+2.27** | 1.90 | +0.085 | 1.23 | 1.159 |
| top 90% of market cap | 0.995 | **+0.097** | 0.050 | **+1.96** | 1.28 | +0.046 | 0.97 | 1.100 |

**Three readings.**

**(a) The size of the benchmark disagreement is comparable to, and usually larger than, the effect
being argued about.** `A3`'s headline is **−4 bp/month**. The benchmark term is **−1 to −10
bp/month** in a screened universe and **−26 bp/month** unscreened, in the same era.

**(b) It flipped sign.** Every intuition in the literature about EW-versus-VW benchmarks was formed
on samples where the gap was **positive at t ≈ 2**. Since 2006 it has been **negative and
insignificant**. **A benchmark argument inherited from a 1963–2018 sample is an argument about the
opposite sign of the same quantity.**

**(c) The screen does almost all the work.** All CRSP names → largest 1,573 shrinks the gap from
−0.262 to **−0.074**. This programme's universe is already screened. **Most of what the benchmark
debate is about is microcaps this programme cannot buy.**

**Caveats, stated where the number is.** The 1,573-name and top-90%-of-cap rows partial-include the
marginal decile at its name weight, i.e. **they assume within-decile return homogeneity**. French's
deciles use **NYSE breakpoints on the NYSE/Amex/Nasdaq universe**, which is not this programme's
`$5`-plus-dollar-volume screen; they are an analogue, not a replica. The standard errors are plain
i.i.d.; I did not Newey-West them.

---

## 4. THE CONFLICT, RECONCILED ARITHMETICALLY

### 4.1 What each lane measured

| | `A3` (via `S5`) | `A2` |
|---|---|---|
| leg weighting | not stated in the paper; **`S10`'s documented default is equal-weighted** | equal-weighted (OSAP baseline) |
| benchmark | **raw Fama-French VW market** (`Mkt-RF + RF`) | **name-weighted average of every bin of the same sort** |
| universe | top 3,000 ∩ top 90% of cap | OSAP predictor universes under four screens |
| window | post-2005 | 2010-01 → 2024-12 |
| headline | mean **−0.04 %/mo**, mean t **−0.31**, **Var(t) = 0.98** | **Var(t) = 1.35 – 1.81**, signal share **0.26 – 0.45** |

### 4.2 The mean: the benchmark switch is worth about 1–10 bp, not 48 bp

**Two independent routes, agreeing.**

**Route 1, `M1`:** post-2005, in a universe comparable to `S5`'s (top 90% of cap), the benchmark
switch is worth **+5.4 bp/month**; in a 1,573-name universe, **+1.2 bp/month**. That turns `A3`'s
**−4 bp into +1 to +2 bp**.

**Route 2, `S6`'s own table.** `S6` Table 5 Panel A gives the average raw equal-weighted return of
every decile across 162 anomalies, 2006–2020, with the number of stocks in each. **`A2`'s benchmark
is computable directly from it**, and I computed it `[MEASURED IN BRIEF]`:

| `S6` Table 5 | decile 10 | **name-weighted universe (all ten deciles)** | **D10 − universe** |
|---|---|---|---|
| Panel A, all stocks | 0.96 % | 0.9529 % | **+0.7 bp/month** |
| Panel B, excluding high-borrow-fee stocks | 1.09 % | 1.0477 % | **+4.2 bp/month** |
| Panel C, after borrow fees | 1.02 % | 1.0160 % | **+0.4 bp/month** |

**Against `A2`'s own benchmark, on an independent 162-anomaly dataset in the same era, the average
long leg beats its universe by under half a basis point a month.** The same table's
DGTW-benchmarked decile 10 is **−0.09 %/mo [−1.81]**, so the benchmark switch is worth about
**+10 bp/month here** — and it lands on **zero**, not on a premium. **I cannot attach a standard
error to the +0.7 bp: the published table gives no covariance between decile 10 and the universe.**

**Conclusion on the mean: `A2` is right that the benchmark matters, and right about the direction.
It is not large enough to convert `A3`'s cross-sectional verdict from negative to positive. It
converts it from slightly negative to indistinguishable from zero.**

### 4.3 The Var(t): the benchmark switch explains essentially all of it

`A2`'s second argument was about **volatility**, not means — that a leg minus a mismatched benchmark
carries a large common component that inflates every series' variance and drives Var(t) toward the
null. **`M1` measures that component: sd 1.22 – 2.80 %/month.**

The arithmetic, with every assumption named. `A2` reports `CBOperProf`'s long leg at **44 bp/month
with t = 2.48 over 2010-01→2024-12 (180 months)**, implying a long-minus-own-universe series with
**sd = 0.44·√180 / 2.48 = 2.38 %/month**. Adding an independent gap series of sd `g` multiplies each
series' sd by `√(1 + (g/2.38)²)` and divides every t by the same factor, so **Var(t) scales by
`1/(1 + (g/2.38)²)`**:

| `A2`'s screen and Var(t) | matching gap sd from `M1` | **predicted long-minus-VW-market Var(t)** |
|---|---|---|
| `hold1` (no screen), 1.804 | 2.80 (all CRSP names) | **0.76** |
| `price_gt5`, 1.503 | 1.96 (largest 1,573) | **0.90** |
| `price_gt5`, 1.503 | 1.22 (top 90% of cap) | **1.19** |
| `me_gt_nyse20`, 1.347 | 1.86 (ME deciles 4–10) | **0.84** |

> **`A3` observed 0.98. The predicted range is 0.76 to 1.19. The benchmark mismatch is
> quantitatively sufficient to produce `A3`'s Var(t) on its own, from `A2`'s numbers.**

**Assumptions, all of them:** the two components are treated as **independent** (they are not
exactly — a leg and its universe share names); the sd is taken from **one signal**, not the
cross-section; `A2`'s window is 2010–2024 and `A3`'s is post-2005; `A2`'s universes are OSAP's and
mine are French's ME deciles. **This is an order-of-magnitude reconciliation, not an identity.** But
it is the right order of magnitude, and it means:

> **A sample Var(t) below the luck-only null of 1.00 is the signature of a benchmark that does not
> match the portfolio. It is not evidence that the portfolios contain no signal. `A2` proposed
> exactly this mechanism and did not quantify it; §4.3 is that quantification, and it lands on
> `A3`'s observed value.**

### 4.4 The one cell where the two lanes overlap, and the benchmark does not matter there

**Cash-based operating profitability** (Ball, Gerakos, Linnainmaa & Nikolaev 2016):

- `A2`, long leg minus its own name-weighted universe, `$5` screen, 2010–2024: **+44 bp/month,
  t = 2.48**, 91% of the long-short premium.
- `S5` Table 2, rank 1, long minus the **raw VW market**, post-2005, N3000∩90%: **+0.40 %/month**
  (verified by me from the PDF; the Original-Paper column reads "Ball et al. (2016)").

**Two opposed benchmarks, two different universes, two different windows, 4 bp apart.** Whatever is
true of that signal's long leg is not a benchmark artefact. **The benchmark decides the
CROSS-SECTIONAL verdict, not this signal's.**

---

## 5. SUB-QUESTION 3 — IS A CHARACTERISTIC-MATCHED BENCHMARK CONSTRUCTIBLE FROM FREE DATA?

**Not as a download, and not for this programme's window. As a build, the size and momentum legs are
free and the book-to-market leg is the whole problem.**

**What DGTW actually requires, verbatim from `S1`'s Appendix (p. 1057) [read in part]:**

> *"Beginning in July 1972, and in each following July, we place every common stock listed on NYSE,
> AMEX, and Nasdaq into portfolios, provided these firms meet our data requirements. … We require
> that COMPUSTAT data be available for at least two years prior to the inclusion of the firm in the
> sample, and that the firm have market value data available on CRSP at the end of December and the
> end of June preceding the formation date. In addition, we require that the firm have at least six
> monthly returns available on CRSP in the 12 months preceding the formation date … The portfolios
> are all value-weighted, buy-and-hold portfolios."*

with a **sequential** triple sort — size quintiles on **NYSE-only breakpoints**, then book-to-market
within size (industry-adjusted against **50 Fama-French industries**, per Cohen–Polk), then prior
twelve-month return through end-May.

**The four inputs, priced honestly.**

| input | free? | detail |
|---|---|---|
| **The published DGTW benchmark returns and assignments** | **No, twice over** | `S13` [read in full]: the files *"cover the period 1975 to 2012 (inclusive)"*, breakpoints only *"Through June 2010"*, last vintage *"Updated October 8, 2013"* — **they end 14 years before this programme's window closes**. And the page's own condition of use is *"You must have a legal subscription to the CRSP/Compustat Merged Database"*. **I did not download the files.** *(That sentence is a licence term on a data page — quoted as data, not acted on.)* |
| **Size breakpoints** | **Yes** | `S14` publishes `ME Breakpoints` (NYSE-only), monthly, current |
| **Momentum breakpoints** | **Yes** | `S14` publishes `Prior (2-12) Return Breakpoints`; and the programme's own daily panel computes momentum for its own names directly |
| **Book-to-market per name** | **Free only via a build** | `S14` publishes `BE/ME Breakpoints` — the **cut points**, not the per-name ratios. Assigning *this programme's* names to cells needs **book equity per name, point-in-time, dead-inclusive**, which is lane `A1`'s territory (`R1-01`): possible from SEC XBRL, but **XBRL barely exists for small and mid names before 2011q3** and *"85–91% of distinct tags in any quarter are filer-invented extensions"* |
| **The 125 cell returns themselves** | **No** | `S14`'s index [read in full] publishes `25 Portfolios Formed on Size and Book-to-Market`, `25 Portfolios Formed on Size and Momentum`, `100 Portfolios Formed on Size and Book-to-Market`, and `6 Portfolios Formed on Size, Book-to-Market, Operating Profitability, Investment, and Momentum` — **but no size × book-to-market × momentum triple sort.** A DGTW grid must be assembled name by name |

**Verdict on sub-question 3: a DGTW-style benchmark is constructible from free data only from
~2011q3 forward, only after solving the XBRL book-equity problem that lane `A1` sized, and only by
assembling the 125 cells from this programme's own names — which makes the benchmark a function of
the same universe it is meant to be independent of.** §7 argues the programme should not want it
anyway.

---

## 6. SUB-QUESTION 4 — THE ABSOLUTE-RETURN CASE

**The commissioning note predicted this sub-question would be under-served by the sources. It is,
and I say so plainly: I found no paper that asks what an unlevered, cash-funded, long-only,
absolute-return single-name book should be measured against.** The leg-decomposition literature is
written by and for people with a benchmark obligation. What I did find is a **primary-source
criterion that settles it**, and one empirical result that reframes it.

### 6.1 Sharpe's own criterion: the benchmark is whatever FINANCES the position

`S11` [PEER-REVIEWED] [read in full, extracted locally]:

> *"Originally, the benchmark for the Sharpe Ratio was taken to be a riskless security. In such a
> case the differential return is equal to the excess return of the fund over a one-period riskless
> rate of interest."*

> *"Central to the usefulness of the Sharpe Ratio is the fact that a differential return represents
> the result of a zero-investment strategy. … it can be obtained by taking a long position in one
> asset (the fund) and a short position in another (the benchmark), with the funds from the latter
> used to finance the purchase of the former."*

> *"In the original applications of the ratio, where the benchmark is taken to be a one-period
> riskless asset, the differential return represents the payoff from a unit investment in the fund,
> financed by borrowing. More generally, the differential return corresponds to the payoff obtained
> from a unit investment in the fund, financed by a short position in the benchmark."*

**That is a test, not a convention.** Subtracting a benchmark asserts that the reported number is the
payoff of *long the book, short the benchmark*. **This programme is long the book and short cash.**
Reporting `book − VW market` describes a strategy the programme is not running, cannot run
(shorting is constrained ground here), and would need index futures to run. **The number that
describes what this book does is `book − RF`.**

**Where an equity benchmark still belongs: as a risk control, beside the number, not inside it.**
Sharpe is explicit that a style-matched benchmark answers a *different* question — *"The Sharpe Ratio
of the selection return can then serve as a measure of the fund's performance over and above that due
to its investment style."* **Over-and-above is the selection question. It is not the return question.**

### 6.2 The cash hurdle is not a low hurdle, and equal weighting is the construction most exposed to it

`S12` Bessembinder [PEER-REVIEWED; free copy from an unaffiliated blog host, bytes verified as the
May 2018 "Forthcoming, JFE" manuscript] [read in relevant part]:

> *"Of all monthly common stock returns contained in the CRSP database from 1926 to 2016, only 47.8%
> are larger than the one-month Treasury rate in the same month."*

> *"just 42.6% of common stocks, slightly less than three out of seven, have a buy-and-hold return
> (inclusive of reinvested dividends) that exceeds the return to holding one-month Treasury bills
> over the matched horizon. More than half of CRSP common stocks deliver negative lifetime returns.
> The single most frequent outcome (when returns are rounded to the nearest 5%) observed for
> individual common stocks over their full lifetimes is a loss of 100%."*

> *"I find that the single-stock strategy underperformed the value-weighted market over the full 90
> years in 96% of the simulations. The single-stock strategy underperformed the one-month Treasury
> bill over the 1926 to 2016 period in 73% of the simulations."*

**Read against a `35.7%`-dead, equal-weighted universe this is the most uncomfortable result in the
brief.** Equal weighting puts the most weight, per dollar, on the **median** name — and the median
name is the one that fails the T-bill hurdle. An equal-weighted book's return comes from
**rebalancing across a positively skewed cross-section**, not from holding the few names that create
the wealth. *(The mechanism by which that rebalancing generates return is the equal-weight
rebalancing bias — excluded ground, `S15`, and named here only to mark the boundary.)*

### 6.3 What the absolute-return case implies for the disputed statistic

**Under a cash hurdle, `A3`'s and `A2`'s numbers are both incomplete in the same way, and the
identity fixes both.** A long leg's contribution to an absolute-return book is

```
leg − RF  =  (leg − EW universe)  +  (EW universe − VW market)  +  (VW market − RF)
              selection: A2's number    weighting/size: M1        the equity premium
```

`A2` reports only the first term. `A3` reports the first two together. **Neither reports the third,
and for a cash-funded book the third term is most of the money.** `[MEASURED IN BRIEF]`, over
2010-01→2026-07 the third term averaged **1.202 %/mo minus RF**, and the second was **−0.074 to
−0.262 %/mo**. **A long-only book's return is dominated by a market exposure that neither lane's
statistic contains** — which is `A3`'s §7 point ("what carries the return: market exposure plus the
tilt, and the market exposure dominates") arriving from the opposite direction.

---

## 7. SUB-QUESTION 5 — IS `A2`'s BENCHMARK RIGHT, OR DOES IT BUILD IN THE ANSWER?

**Answer: it is the right comparison for the SELECTION question, it is the wrong comparison for the
RETURN question, and the specific circularity the commission feared is not present in it — it is
present in DGTW instead, and the DGTW authors say so in print.**

### 7.1 The circularity that IS documented — and it is not `A2`'s

`S1` (p. 1056) [read in part], in the authors' own words:

> *"We have discussed our characteristic-based benchmark with portfolio managers who have performed
> very well by implementing momentum and high book-to-market strategies. As one might expect, these
> individuals are not particularly enthusiastic about a benchmark that gives them no credit for
> having been insightful enough to implement such strategies. The characteristic-based selectivity
> measure assigns no significant abnormal performance to those investors who simply follow the same
> mechanical characteristic-based strategy over the entire time period. This is true even if that
> strategy did extremely well."*

**That is the circularity, stated by the people who built the benchmark, and defended as
intentional.** They formalise it: their **AS (Average Style)** measure is introduced as
*"to measure the returns earned by a fund due to that fund's tendency to hold stocks with certain
characteristics, we create an AS return measure"*, and *"The sum of the CS, CT, and AS measures
equals the total fund return."* **The characteristic premium is not
destroyed by DGTW; it is moved into a component the paper reports separately and the users of the
benchmark almost never do.**

**This has a direct consequence for `A3`'s second dataset that `A3` did not draw.** `S6` sorts 162
anomalies and benchmarks each name against a size/BM/momentum-matched cell. **For any anomaly whose
sorting variable correlates with size, book-to-market or momentum, part of the long leg's return is
removed by definition.** `S6` anticipated the objection and answered it — *"the close similarity
between the results for raw and abnormal returns show that the results and conclusions are not
driven by the choice … of benchmark"* — and §4.2 above confirms it independently: their long leg is
**+0.7 bp/month** against `A2`'s benchmark, which is characteristic-free. **The objection is valid in
principle and empirically empty here. Both halves go on the record.**

### 7.2 Why `A2`'s universe benchmark is not circular in the same way

A name-weighted universe benchmark removes **the return of the universe**, not **the return of the
characteristic**. It is a decomposition:

```
leg − universe  =  what the SIGNAL selected, given the universe and the weighting
universe − VW market  =  what the UNIVERSE and the WEIGHTING chose, given the market
```

**Neither term contains the other.** The only way `A2`'s benchmark could "build in the answer" is if
the *sorting variable were itself size or liquidity* — in which case the universe benchmark would
indeed absorb the effect being tested. **For `F-PROFIT`, `F-FINANCE` and the rest of `A2`'s census
the sorting variables are accounting characteristics, not size**, so the circularity does not bind.
**For a size, illiquidity or price-level signal it would bind completely, and that is a real
restriction on where this benchmark may be used.**

### 7.3 But the direction of the worry was backwards in this era

The commission's specific concern was that subtracting an equal-weighted universe *"removes precisely
the size and illiquidity exposure that generates the measured premium."* `[MEASURED IN BRIEF]`:
**over 2010–2026 the thing being removed is negative.** Subtracting a universe that underperformed
the market by 7–26 bp/month **adds** that much to the measured alpha. **In this era `A2`'s benchmark
is the more generous one, not the more conservative one** — and by 1–10 bp/month in a screened
universe, which is the same order as the disputed effect. On 1963–2018 data the worry would have been
correct and the sign reversed.

### 7.4 Three reasons `A2`'s benchmark is nevertheless the better of the two for this book

1. **It matches the weighting.** `S3` justified exactly this and demonstrated the cost of not doing
   it (§2.1, §3.3).
2. **It matches the beta.** `[MEASURED IN BRIEF]`: the name-weighted universe's **β on the VW market
   is 1.05–1.20**, so `leg − VW market` leaves a **+5% to +20% beta bet inside the reported alpha**.
   Against its own universe a leg's beta is ≈ 1 by construction.
3. **It is quieter.** The mismatched benchmark injects **sd 1.2–2.8 %/month** of pure noise (§4.3),
   which is the entire reason `A3`'s Var(t) came in below the luck null.

**And the one reason it is not sufficient on its own: it is not an instrument.** `A2` said so
(`R1-02` §10, item 6). You cannot buy the name-weighted universe of a sort, so `leg − universe`
answers "did the signal pick well?" and never "did the book make money?".

---

## 8. THE RECOMMENDATION

**Report the identity. Both terms. Every time. And keep the third.**

```
leg − RF  =  (leg − own name-weighted universe)   ← selection: A2's number, use it as the SIGNAL test
          +  (own universe − VW market)           ← weighting/size: −7 to −26 bp/mo in 2010-2026
          +  (VW market − RF)                     ← the equity premium the book is actually long
```

Four operational consequences.

1. **For the programme's own signal criterion — a positive gross mean per trade above its nulls —
   subtract NOTHING.** The programme's nulls already are `A2`'s benchmark. A time rotation or a
   partner randomisation *within the same eligible universe, at the same weighting, with the same
   count* holds constant exactly what the name-weighted universe holds constant, **and delivers a
   p50 and a p95 instead of a single scalar**. **A within-universe null is a strictly stronger
   instrument than a subtracted universe return, and the programme has already built it.** The
   benchmark controversy in the literature is, for this programme's first hurdle, already resolved by
   its own machinery — a fact neither `A2` nor `A3` noticed.
2. **For any headline that must be benchmark-relative, publish `leg − universe` and
   `universe − market` side by side** and never one alone. On the measured numbers, showing only the
   first would credit the strategy with **+7 to +26 bp/month** of avoided small-cap drag that the
   signal had nothing to do with.
3. **Report the absolute number against cash**, per `S11`'s financing criterion, and state the beta
   beside it. A book with **β ≈ 1.15** to the market that returns 1.13 %/mo in a market that returned
   1.20 %/mo has not beaten anything.
4. **Do not build DGTW.** It is not free for this window (§5), it requires the book-equity panel that
   `R1-01` priced, and by its authors' own statement it would **zero out any part of the return that
   comes from holding a characteristic** — which for a characteristic-premium programme is the return
   itself.

**Which reading I would weight, and why.** On the **cross-sectional verdict** I weight `A3`: the
benchmark switch moves the mean by 1–10 bp in a screened universe and lands it on zero, and `S6`'s
own table gives **+0.7 bp/month** against `A2`'s benchmark on an independent 162-anomaly sample. On
the **statistic**, I weight `A2` entirely: **Var(t) = 0.98 is a benchmark artefact and should not be
cited again as evidence of an absent signal.** On **`F-PROFIT`**, the benchmark is irrelevant — both
lanes get ~+40 bp for the same signal — so `B2`'s territory is undisturbed by this lane either way.
**Both readings stay on the record, and neither lane was wrong about what it measured.**

---

## 9. SUB-QUESTION 6 — THE SMB EXPOSURE AN EQUAL-WEIGHTED CONSTRUCTION ACQUIRES

**Documented, mechanical, and quantified — by four independent sources including one that reproduced
the effect specifically to attack a long-only conclusion.**

**The construction fact.** `S2` Table 4 Panel A [read in full]: in the Fama-French 2×3 grid, **"Small"
stocks are 13.1% of market capitalisation** but SMB weights them **+100% against −100% for Big**, and
HML equal-weights the small and large value effects even though *"the outperformance of value stocks
over growth stocks is much more pronounced among small stocks (13.21 − 4.85 = **8.36% per year**) than
large stocks (9.20 − 7.61 = **1.59% per year**)"*. `S7` [read in relevant part]: *"Microcaps represent
only 3.2% of the aggregate market capitalization but 60.7% of the number of stocks."*

**The attribution.** `S4` [WORKING PAPER, CFM — interested against long-only] [read in full]
reproduced `S3` and traced the long-leg advantage to SMB, in the note to their Figure 5:

> *"This chart shows that when (longs - market) outperforms (market - shorts), this is in large part
> explained by an SMB exposition of the difference (longs - market) - (market - shorts). … Δ roughly
> rewrites as (longs + shorts) - 2 SPmini. Given the Fama-French portfolios used in [4] are 50% small
> caps and 50% large caps, Δ is correlated to the difference between an equally-weighted index with a
> market-cap weighted index, i.e. to SMB."*

and in the text: *"the very definition of the market index — which serves as a hedge — is found to
matter quite dramatically. Using for example the SPmini index (which is easily implementable as a
low-cost hedge), we now find that the Sharpe ratio of the long legs is significantly better that that
of the short legs, as reported in [4]. However, this is because the difference between the two legs
is now mechanically exposed to the SMB factor."*

**And here is the correction to how this programme has been carrying that finding.** `R1-03` §8.1
recorded `S4` as showing that `S3`'s long-leg advantage *is* an SMB exposure. **Read in full, `S4`
says the SMB exposure appears when the hedge is the CAP-WEIGHTED SPmini — which is the benchmark
`S3` explicitly refused.** With `S3`'s own 50/50 Big+Small hedge, `S4` finds *"no striking difference
of Sharpe ratio between the long and short legs"* and an optimal short-leg weight of **30%, not
zero**. **So `S4`'s finding is: with a composition-matched benchmark the long-leg advantage largely
disappears; with a cap-weighted benchmark it reappears as SMB.** That is the same identity as §3.1,
pointing the other way, and it is the sharpest single statement of this lane's subject in the
literature.

**The scale of it, measured.** The mechanical SMB an equal-weighted construction acquires **is** the
`universe − VW market` term of `M1`: **−0.07 to −0.26 %/month over 2010–2026, +0.10 to +0.24
%/month over 1963–2018, with monthly sd 1.2–2.8% and β 1.05–1.20**. **For this programme the
exposure is unavoidable — equal weighting is the book's construction — so the question is never
whether to carry it but always whether to report it inside the alpha or beside it. It belongs
beside.**

---

## 10. CONFLICTS RECORDED, NOT ADJUDICATED

1. **`S3` vs `S4` on whether long legs dominate.** `S3`: long legs carry most of the premium
   (combined long Sharpe 1.10 vs short 0.69, 1963–2018, minus a 50/50 Big+Small hedge). `S4`,
   reproducing it: *"the short leg should be allocated 30% of the weight, and not zero weight … At
   the very least, this means that the 'no-short' recommendation is not robust against such minor
   changes."* **Both are interested parties pointing opposite ways. Both stay.**
2. **`S7` vs `S10` on weighting.** `S7`: value-weighting *"accurately reflects the wealth effect
   experienced by investors"*. `S10`, quoting `S9` in support: equal weighting excluding low-cap
   stocks is preferable. `S9`: capped value weights, *"a helpful compromise"*, worth **+8.5pp** on
   replication. **Three positions, three justifications, no resolution in the literature.**
3. **`S6`'s prose vs the campaign's own scepticism about prose.** `S6` claims benchmark-independence
   in prose; I verified it against their table and it holds (§4.2). **Recorded because the campaign's
   rule is to prefer tables, and here the table agreed.**
4. **`A2` vs `A3`.** Adjudicated in §4 and §8 — **partially for each, on different statistics**, with
   the losing reading kept in every case.

---

## 11. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **I did not re-run `A2`'s Var(t) on the OSAP portfolio data.** The decisive replication would be
   to download Chen & Zimmermann's portfolio files and recompute both Var(t)s directly. I did not:
   the files are hosted behind a drive interstitial and are large, and the reconciliation in §4.3 is
   arithmetic on `A2`'s and my own numbers, **not a replication**. **The 0.76–1.19 range is a
   prediction, not a measurement.**
2. **The sd of the long-minus-own-universe series is inferred from ONE signal** (`CBOperProf`: 44 bp
   at t = 2.48 over 180 months ⇒ 2.38 %/mo). The cross-sectional distribution of that sd is unknown
   to me, and §4.3 scales linearly in it.
3. **The +0.7 bp/month I derived from `S6` Table 5 has no standard error.** The published table does
   not give the covariance between decile 10 and the other deciles, so I cannot say whether +0.7 bp
   differs from zero.
4. **My screened universes are analogues, not replicas.** French's ME deciles use NYSE breakpoints on
   the NYSE/Amex/Nasdaq universe. The "largest 1,573" and "top 90% of cap" rows **partial-include the
   marginal decile at its name weight and therefore assume within-decile return homogeneity**. This
   programme's universe is defined by a `$5` floor and a dollar-volume screen, which is a different
   cut.
5. **Standard errors in `M1` are plain i.i.d.**, not Newey-West; monthly benchmark differences are
   close to serially uncorrelated but I did not test it.
6. **`S1` was read as images.** The Wermers-hosted DGTW PDF is a 24-page scan; `pdftotext` and
   `pypdf` both return zero characters. Every DGTW quotation above was transcribed by me from a
   rendered page image, and **transcription from an image is a weaker chain than a byte extraction**.
   I read seven of twenty-four pages; the empirical CS/CT/AS decomposition tables for funds are among
   the seventeen I did not read, so **I report DGTW's decomposition identity and not the size of its
   AS component**.
7. **`S3` Table A2's row labels were shuffled by the layout extraction** before I re-extracted the
   page with `pypdf`; the numbers quoted are from the clean `pypdf` extraction. **`S2` Table 7's
   size-decile alphas are still garbled and I quote from that table only the one value the paper's
   prose confirms** (decile 10, Carhart, +0.98%/yr, t = 2.71).
8. **I did not download the DGTW benchmark files** (`S13`), so I have not verified their contents,
   only the page's description of them. The 1975–2012 coverage and the CRSP/Compustat condition are
   the page's own statements.
9. **`S12`'s only free copy is on an unaffiliated retail-investing blog.** I verified the byte
   stream is the real May 2018 accepted manuscript (title, author, ASU affiliation, "Forthcoming,
   Journal of Financial Economics"), but **I did not obtain it from the publisher or the author**.
10. **`S15` reached me through a search summariser only, and I take no figure from it.** Its subject
    is excluded ground.
11. **Blocks and failures, by tool and response.** None. Every fetch in this lane returned HTTP 200
    with the expected content type; the one hazard encountered was **`S1` returning a genuine but
    image-only PDF where a text PDF was expected**, caught by `pdftotext` returning zero bytes and
    confirmed by `pypdf` reporting one TIFF image per page. The NBER PDF (`S9`) was title-checked
    against this campaign's known "NBER URL serves a different paper" failure and was correct.
12. **I found no source that addresses the absolute-return, cash-funded, long-only single-name case
    directly.** §6 is built from a primary-source criterion (`S11`) applied by me to this programme's
    situation, plus one empirical result (`S12`) about the cash hurdle. **That application is my
    reasoning, not a literature finding**, and it should be read as such.
