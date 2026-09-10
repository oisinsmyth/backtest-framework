# `A3` — THE LONG-ONLY PROBLEM

**Round 1 of `Scan-100926`.** Lane `A3` of four. Contract, inherited exclusions and the rules this
brief carries: [`00-SCHEMA.md`](00-SCHEMA.md). Slate: [`R1-00-slate.md`](R1-00-slate.md).

Under [R15](../../RULES.md#r15) **nothing here closes or admits anything.** No number below was
measured on this programme's fixture; figures restated from our own record (33.8 bp/side, the 67.6 bp
round trip, ~1,573 names, ~10 effective instruments) are quoted, not recomputed.

---

## 0. THE VERDICT, AND IT IS THE NEGATIVE ONE

**The bar this lane was given was either a named long-only survivor with cost-honest post-2005
evidence, or an explicit well-sourced finding that long-only is where the returns are not. I reached
the second, and it is stronger than the commissioning note assumed.**

> **THE LONG LEG FAILS GROSS.** Post-2005, across ~170 published anomalies in a large-cap universe,
> the cross-sectional **mean** long-minus-market return is **−0.04% per month**, mean *t* = **−0.31**,
> and the cross-sectional variance of those *t*-statistics is **0.98 — below the luck-only 1.00**.
> Across a different 162-anomaly sample on a different statistic, the **long leg's DGTW-adjusted
> abnormal return is −0.09%/month (*t* = −1.81)** and the long leg earns **less in raw return than
> deciles 5 through 9 of the same sort**. **No transaction cost has been charged at that point.**

This matters for a specific reason. **This programme's own stated signal criterion is a positive
GROSS mean per trade above the nulls, with costs and confluences considered later.** The long-only
case does not reach the cost question. **It fails at the programme's own first hurdle, on two independent datasets, with two
different benchmarks and two different risk adjustments.**

**Three corollaries that change what future rounds should even consider.**

1. **The cost objection is not the binding one here, and neither is the $5 floor.** For the one
   anomaly whose **nominal price distribution by leg** I could establish, a **$5 price screen destroys
   77% of the short leg's alpha and leaves the long leg untouched** (+0.08% → +0.12%/month). The floor
   removes where the money was, not where the programme could have reached it. **An account that
   cannot short loses nothing to the floor — because it had nothing to lose.**
2. **The one serious body of counter-evidence does not survive contact.** Blitz et al. (2020) and
   Israel–Moskowitz (2013) both report the long legs carrying most of the premium. Israel–Moskowitz's
   **own statistical test cannot reject a 50/50 long/short split in any size group**, they **charge no
   trading costs**, and their long-only value result **exists only in microcaps**. Blitz et al.'s
   long-leg advantage was **reproduced and then mechanically attributed to an SMB exposure** by an
   independent group (§8.1). **Both readings stay on the record.**
3. **The mechanism is real, partly long-only-implementable, and not computable here.** Arbitrage
   asymmetry is supported: the most-**underpriced** quintile earns **+0.28%/month** FF3 alpha
   (*t* = 5.51) against the most-overpriced quintile's **−0.83%** (*t* = −8.07) — a genuine long-only
   alpha carrying **25%** of the spread. It requires an **11-anomaly mispricing composite built on
   fundamentals**. The **price-only** half of that same paper (IVOL) has **no long-only return at
   all**: low-IVOL's FF3 alpha is **+0.07%/month, *t* = 1.72**.

**And the honest arithmetic on "just avoid the bad names", which nobody in the literature computes
and which I computed myself (§9): dropping the worst decile from an equal-weighted universe buys
about +1.7 bp/month gross — and about 0 bp once hard-to-borrow names are already excluded.** At 67.6
bp round trip that permits **2.5% of the book turning over per month**. It is not zero. It is also
not a strategy.

---

## 1. SOURCES, TYPE AND HOW WELL ESTABLISHED

Every number below is tagged in the same sentence as the figure taken from it.

| # | source | type | established |
|---|---|---|---|
| **A1** | **Muravyev, Pearson & Pollet, *Anomalies and Their Short Sale Costs***. Text I read = the **1 Sep 2022 working draft**, 51 pp, hosted by HEC Montréal. Published as JF 80(6) 2025, 3639–3694 | [WORKING PAPER] for the text read; the published article is [PEER-REVIEWED] | **[read in full]** — PDF downloaded, bytes verified, extracted locally with both `pypdf` and `pdftotext -layout`; Tables 1–10 read off the layout extraction. **The published abstract I read directly from RePEc's own page bytes** (not a summariser) and it **differs from the draft** — §8.5 |
| **A2** | **Chen & Welch, *What Useful Alphas?***, arXiv **2607.06502v1**, submitted 7 Jul 2026, PDF dated 8 Jul 2026, 24 pp | [WORKING PAPER], **unrefereed, single version** — confirmed v1-only from the arXiv abstract page, with a **bogus-ID negative control returning an honest 404** (§10) | **[read in full]** — extracted locally; Tables 1–3, Figures 1–3 captions, Appendix A shrinkage algebra |
| **A3** | **Li, Sullivan & Garcia-Feijóo, *The Limits to Arbitrage and the Low-Volatility Anomaly*, Financial Analysts Journal 70(1), Jan/Feb 2014, 52–63** | [PEER-REVIEWED]. The copy I read is an **AQR-hosted reprint** of the CFA Institute article — host is an interested party, the article is not theirs | **[read in full]** — Tables 3–7 and conclusion. **This is the only source I found that reports the NOMINAL SHARE PRICE of each leg** (§5.3) |
| **A4** | **Israel & Moskowitz, *The role of shorting, firm size, and time on market anomalies*, JFE 108(2), 2013, 275–301** | [PEER-REVIEWED]. **Israel is AQR; Moskowitz is an AQR principal — interested, and its conclusion is the one a long-only factor manager wants** | **[read in full]** — published JFE version; Table 1 reconstructed from a garbled layout extraction and **verified by three accounting identities in three separate period columns** (§5.2) |
| **A5** | **Stambaugh, Yu & Yuan, *Arbitrage Asymmetry and the Idiosyncratic Volatility Puzzle*.** Text read = **NBER w18560**; published JF 70(5) 2015 | [WORKING PAPER] for the text read; published article is [PEER-REVIEWED] | **[read in full]** — §§1–5 and Table 2, **verified against four numbers quoted in the paper's own prose** |
| **A6** | **Benaych-Georges, Bouchaud & Ciliberti, *Equity Factors: To Short Or Not To Short, That Is The Question*, arXiv 2003.10419v3, 6 Apr 2021** | [WORKING PAPER], **Capital Fund Management — interested, and interested AGAINST long-only**, which makes its positive hedged-long-only number conservative-direction | **[read in full]** — 4 pp (dense); §§2–5 and Table 1 |
| **A7** | **Blitz, Baltussen & van Vliet, *When Equity Factors Drop Their Shorts*, FAJ 76(4) 2020, 73–99** | [PEER-REVIEWED] but **all three authors are Robeco Quantitative Investments — interested** | **[abstract only, plus this programme's own prior reading].** I was **refused the full text** (§10). The leg alphas I quote are **restated from `K6`'s `[read in full]` of Tables 3–4** in [`../the-reversal-round.md`](../the-reversal-round.md) §10; the three summary claims are from the **CFA Institute article page bytes I fetched myself** |
| **A8** | **Brière & Szafarz, *Factor Investing: The Rocky Road from Long-Only to Long-Short*, Amundi Working Paper WP-063-2017** | [WORKING PAPER], **Amundi — interested**. Marked "For professional investors only" | **[read in full]** — abstract, §I, and the framing of Groups 1–2. **Its content is mean-variance spanning = portfolio construction = excluded ground** (§6.2) |
| **A9** | **Green, Hand & Zhang, *The Characteristics that Provide Independent Information about Average U.S. Monthly Stock Returns*, RFS 30(12) 2017, 4389–4436** | [PEER-REVIEWED] | **[abstract only]** — and the "since 2003" figures reached me **via a search summariser**, so they are weaker than `[snippet only]`. I also found the same sentence **quoted verbatim inside `A1`'s literature review, which I read in full** |
| **A10** | **Haddad, Kozak & Santosh, *Factor Timing*, RFS 33(5) 2020, 1980–2018.** NBER w26708 PDF downloaded | [PEER-REVIEWED] article; [WORKING PAPER] for the bytes in hand | **[abstract only]** — PDF obtained, **not read**. Subject is **excluded ground** (§6.1), reported only to locate the literature |
| **A11** | **Moreira & Muir (JF 2017) vs Cederburg, O'Doherty, Wang & Yan (JFE 2020)** on volatility-managed portfolios | both [PEER-REVIEWED] | **[abstract only, via a search summariser]** — weaker than `[snippet only]`. **Excluded ground** (§6.1) |
| **A12** | **Cirulli & Walker, *Outperforming Equal Weighting*, SSRN 4669267, Dec 2023** | [WORKING PAPER] | **[UNVERIFIED]** — **SSRN refused me** (§10). Everything I have about it came through a **search summariser relaying an Alpha Architect blog post**, and the blog itself 403'd. **I report its existence and its question, not its numbers** (end of §9) |

**No asset-manager marketing document is used as evidence for a return anywhere in this brief.**
`A3`'s host, `A4`, `A6`, `A7` and `A8` are all author- or host-interested and are flagged at every
point of use. **`A6` is the one interested source whose interest runs AGAINST the conclusion it
reports**, and I say so where it is used.

---

## 2. SUB-QUESTION 1 — IS THERE POST-2005, COST-HONEST EVIDENCE FOR A LONG-ONLY ANOMALY RETURN?

**No. And the two papers that report the legs separately on post-2005 data both find the long leg
negative before any cost is charged.**

### 2.1 `A2` — long-minus-market, ~170 anomalies, post-2005, top 3,000 ∩ top 90% of market cap

`A2` is the paper that generated the figure in this lane's commissioning note, and reading it in full
**sharpens the number rather than softening it** [WORKING PAPER] [read in full]:

| statistic | value |
|---|---|
| cross-sectional **mean** long-minus-market return, ~170 anomalies | **−0.04% / month** |
| cross-sectional **SD** of those means | **0.13% / month** |
| **mean *t*-statistic** of long-minus-market | **−0.31** |
| **Var(*t*)** of long-minus-market | **0.98 — below the luck-only null of 1.00** |
| empirical-Bayes adjusted long-minus-market, shrink toward **zero** | **0.00% / month, every anomaly** |
| empirical-Bayes adjusted long-minus-market, shrink toward the **cross-sectional mean** | **−0.04% / month, every anomaly** |

**`K6` reported the shrink-to-zero target (0.00%/month). The paper carries both, and the
shrink-to-mean target is the slightly worse one.** `A2`'s own words: *"For the long legs net of the
market, Var(𝑡) was below 1, so the factor is truncated at zero either way, and the shrink-toward-mean
estimate of every long leg equals the common average of about −4 bps per month."*

And their conclusion, verbatim: *"Even this required shorting — the long-only return was at most zero
net of selection bias."*

**The best raw long-minus-market in the whole post-2005 cross-section, named.** `A2`'s Table 2 ranks
the top ten survivors by long-short return and reports each one's long-minus-market beside it. The
mapping of description to figure I verified by the **"Original Paper" column matching each signal's
known source** [read in full]:

| rank | signal | original paper | LS %/mo | **Long − Mkt %/mo** | adjusted |
|---|---|---|---|---|---|
| 1 | **Cash-based operating profitability** | Ball, Gerakos, Linnainmaa & Nikolaev (2016) | 0.66 | **+0.40** | 0.00 |
| 2 | Operating profitability (R&D adjusted) | Ball et al. (2016) | 0.60 | +0.26 | 0.00 |
| 3 | Realized-implied volatility spread | Bali & Hovakimian (2009) | 0.59 | +0.35 | 0.00 |
| 4 | Off-season momentum | Heston & Sadka (2008) | 0.54 | +0.13 | 0.00 |
| 5 | Net external financing | Bradshaw, Richardson & Sloan (2006) | 0.48 | +0.15 | 0.00 |
| 6 | Seasonal momentum (16yr+) | Heston & Sadka (2008) | 0.48 | +0.21 | 0.00 |
| 7 | Gross profitability | Novy-Marx (2013) | 0.44 | +0.14 | 0.00 |
| 8 | R&D over market cap | Chan, Lakonishok & Sougiannis (2001) | 0.41 | +0.33 | 0.00 |
| 9 | Net equity financing | Bradshaw, Richardson & Sloan (2006) | 0.39 | +0.16 | 0.00 |
| 10 | Operating leverage | Novy-Marx (2011) | 0.38 | **−0.01** | 0.00 |

**So the single strongest long-only candidate the post-2005 literature contains is cash-based
operating profitability at +0.40%/month over the market, gross, pre-shrinkage.** It is also:
**(i)** an accounting signal requiring Compustat-style fundamentals, so **not computable from this
programme's permitted data**; **(ii)** one draw from a cross-section whose dispersion is *below* the
luck benchmark, which is precisely why `A2` assigns it 0.00; and **(iii)** not charged a basis point
of cost.

**`A2`'s universe brackets this programme's more tightly than `K6` allowed.** `A2` reports median
long-short by filter: **all stocks 19 bp/month · Rank Only (N3000) 12 bp · Standard (N3000 ∩ 90%)
7 bp · Tight (N1000 ∩ 80%) 7 bp** [read in full]. This programme's ~1,573 names sit **between N1000
and N3000, and both of those cells give the same 7 bp median.** That is a narrowing of `K6` §8.7's
"I cannot say where". **The caveat stands and matters:** a `$5`-floored, dollar-volume-screened
1,573-name universe is *not* the top 1,573 by market cap, and will contain names `A2` screens out.

### 2.2 `A1` — the leg decomposition, 162 anomalies, July 2006 – December 2020, EQUAL-WEIGHTED

**This is the most valuable thing this lane recovered, because `K6` had it only as `[abstract only]`
via a summariser and the draft reports every decile.** `A1`'s universe is CRSP common stocks matched
to Markit borrow fees, **dropping lagged price below `$1` and lagged market cap below `$50`mn**,
562,632 stock-months, **equal-weighted**, DGTW characteristic-matched abnormal returns with high-fee
stocks excluded from the benchmarks [WORKING PAPER draft] [read in full].

**Table 2 — DGTW-abnormal monthly returns by decile, all stocks, no fee adjustment:**

| decile | 1 (short) | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | **10 (long)** | **10−1** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mean | **−0.24%** | −0.10 | −0.07 | −0.07 | −0.05 | −0.05 | −0.05 | −0.06 | −0.03 | **−0.09%** | **+0.15%** |
| *t* (panel) | **[−2.94]** | [−2.44] | [−2.31] | [−2.82] | [−1.98] | [−1.94] | [−1.67] | [−1.95] | [−1.16] | **[−1.81]** | **[2.93]** |
| % high-fee | 21.91% | 13.73 | 10.93 | 10.04 | 9.96 | 9.39 | 9.50 | 10.20 | 12.03 | **18.33%** | |
| avg fee/yr | 2.70% | 1.58 | 1.25 | 1.16 | 1.12 | 1.08 | 1.09 | 1.14 | 1.31 | **2.03%** | |

**Three readings, in order of how much they matter.**

**(a) The long leg's risk-adjusted abnormal return is negative, and worse than the middle of the
sort.** `A1` states it plainly: *"The average abnormal returns at the other extreme, decile ten, also
tend to be lower than the average abnormal returns of the decile three through nine portfolios."*
**The best long-only decile is decile 9 at −0.03%, indistinguishable from decile 5's −0.05%.**

**(b) The level of every decile is contaminated by benchmark construction, and the paper says so.**
All ten means are negative *because* high-fee stocks sit in all ten deciles but are excluded from the
DGTW benchmarks. **So read the decile-vs-decile comparison, not the level.** That comparison is the
one above, and it is unfavourable.

**(c) The long leg is itself a hard-to-borrow, small cohort.** Decile 10 carries **18.33%** high-fee
names at a **2.03%/yr** average fee, against **9.39–10.20%** and **~1.10%/yr** in deciles 5–8.
`A1`'s explanation: *"the decile ten portfolios tend to include smaller stocks, which also tend to
have higher borrow fees."* **The long leg is not the clean leg. It is the other end of the same
illiquid tail.**

**Table 5 — RAW equal-weighted monthly returns, which avoid the benchmark contamination entirely:**

| | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | **D10** | **10−1** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **A: all stocks** | 0.80% | 0.92 | 0.97 | 0.95 | 0.99 | 0.98 | 0.98 | 0.98 | **1.00** | **0.96%** | **+0.16%** [2.91] |
| **B: excl. high-fee** | 1.04% | 1.03 | 1.05 | 1.03 | 1.06 | 1.04 | 1.04 | 1.04 | 1.06 | **1.09%** | **+0.05%** [0.98] |
| **C: net of borrow fee** | 1.03% | 1.05 | 1.01 | 0.98 | 1.02 | 1.01 | 1.01 | 1.00 | 1.03 | **1.02%** | **−0.01%** [−0.04] |

> **In raw return, the long leg (0.96%) earns LESS than deciles 5, 6, 7, 8 and 9 of the same sort.
> The entire +0.16% spread is decile 1's 0.80% being low. There is no long-only return here at all —
> a long-only investor who bought the signal's top decile instead of the middle of the universe would
> have earned slightly less.**

**And in the borrow-free universe a long-only account actually lives in (Panel B), the whole spread
collapses to +0.05%/month, *t* = 0.98 — insignificant.** Table 3 gives the risk-adjusted version of
that same universe: decile 1 **0.00%** [0.04], **decile 10 +0.04%** [0.97], 10−1 **+0.04%** [0.81].
**Every cell insignificant.**

**Table 9 — by signal category, and this is the cell that matters most for a price-and-volume-only
programme:**

| category | D1 (short) | **D10 (long)** | 10−1 |
|---|---|---|---|
| **Accounting** (82 anomalies) | −0.20% [−2.63] | **−0.05% [−0.75]** | +0.16% [3.06] |
| **Price** (45 anomalies) | −0.25% [−2.76] | **−0.12% [−1.80]** | +0.15% [1.87] |
| **Other** (35 anomalies) | −0.29% [−3.00] | **−0.17% [−2.98]** | +0.12% [1.04] |

> **In all three categories the long leg's abnormal return is negative. In the PRICE category — the
> only input class this programme has free — the long leg is −0.12%/month with *t* = −1.80, and the
> long-short itself is only marginal at *t* = 1.87.** Excluding high-fee names, the Price category's
> long leg becomes **+0.01%** [0.35] and its spread **+0.02%** [0.32].

### 2.3 A confirmed absence inside the cost-honest literature

**Neither of the two papers that measure post-2005 net-of-spread anomaly returns reports the legs
separately net of cost.** `A2` reports long-minus-market **gross** and says so. `A1` charges **borrow
fees only** — no spread, no commission. Chen & Velikov (2023), which `K6` read in full and which is
the source of the 204-anomaly / 4 bp-net figure, reports **long-short net returns** and not legs.

> **So there is no paper anywhere in this lane's reading that reports a long-only anomaly return net
> of trading costs, post-2005. The reason the gap does not need filling is that the long leg is
> already at or below zero GROSS.** A cost charge can only move it down.

---

## 3. SUB-QUESTION 2 — WHY IS THE RETURN IN THE SHORT LEG, AND IS THE EXPLANATION EXPLOITABLE WITHOUT SHORTING?

### 3.1 The three candidate explanations, and what each is actually supported by

**(a) Short-sale constraints and borrow fees — strongly supported, and quantified.** `A1` is the
cleanest test anywhere. *"Short sale costs eliminate the abnormal profits generated by asset pricing
anomalies… Thus, short sale costs explain why these anomalies exist despite arbitrageurs' best
efforts to eliminate them"* [read in full]. Two independent cuts support it: **adjusting for borrow
fees** takes decile 1 from **−0.24% to −0.01%** and the spread from **+0.15% to −0.02%**; and
**simply excluding high-fee stocks without any fee adjustment** takes decile 1 to **0.00%** and the
spread to **+0.04%** [0.81]. **Those are two different operations reaching the same place, which is
what makes the mechanism credible rather than mechanical.** Mechanism detail: the fee is asymmetric —
the short pays the whole fee, the long **receives only part of it and only if the shares are lent**,
because intermediaries retain a cut.

**Note the boundary: WHY the return is in the short leg is this lane's subject; short interest,
days-to-cover, borrow fees and FTD data as signals are excluded ground and are not pursued.**

**(b) Arbitrage asymmetry — supported, and the asymmetry is measured at 3.4×.** `A5` is the source
[WORKING PAPER version of a peer-reviewed article] [read in full]. They build a mispricing composite
by averaging each stock's rankings on **11 anomalies**, then sort on IVOL within mispricing quintile,
1965m8–2011m1, FF3-adjusted:

| mispricing quintile | highest IVOL | … | lowest IVOL | **high − low** | **ALL (quintile's own alpha)** |
|---|---|---|---|---|---|
| **most overpriced** | −2.19 [−11.23] | | −0.42 [−3.60] | **−1.77 [−7.87]** | **−0.83% [−8.07]** |
| next | −0.91 | | −0.10 | −0.81 [−4.17] | −0.24% [−3.83] |
| middle | −0.11 | | 0.07 | −0.18 [−0.97] | −0.06% [−1.30] |
| next | −0.09 | | 0.15 | −0.25 [−1.19] | +0.18% [4.32] |
| **most underpriced** | +0.63 [4.30] | | +0.12 [1.55] | **+0.52 [2.93]** | **+0.28% [5.51]** |
| **over − under** | −2.82 | | −0.54 | −2.28 [−8.48] | **−1.10% [−7.97]** |
| **all stocks** | −1.23 [−7.44] | | +0.07 [1.72] | **−1.30 [−6.92]** | |

*(Reconstructed from a layout extraction and **verified against four numbers the paper states in
prose**: −1.77, +0.52, −0.18 and −1.30, all matching.)*

The asymmetry in the paper's own words: *"The negative highest-versus-lowest difference among the
most overpriced stocks is **3.4 times** the magnitude of the corresponding positive difference among
the most underpriced stocks."* **The direction is the predicted one: overpricing is harder to correct
than underpricing because you must short to correct it.**

**(c) Limits to arbitrage more broadly — supported but it points the wrong way for this programme.**
`A3` finds the low-volatility anomaly's alpha concentrated in low-liquidity, small and **low-priced**
names, and argues those frictions are *why* it persists [PEER-REVIEWED] [read in full]. `A1`'s
footnote 6 is the dissent worth recording: they obtain their result **for the idiosyncratic-risk
anomaly even though the literature treats idiosyncratic risk as a separate limit to arbitrage**, and
note that if it were separate *"one would expect that the net-of-fee return and the return excluding
high-fee stocks on the long-short would be positive. But they are not."*

### 3.2 The operational question: does avoiding the overpriced names from a long-only universe capture any of it?

**Partly yes, and the size of "partly" is the answer.**

**The yes.** `A5`'s **most-underpriced quintile earns +0.28%/month FF3 alpha, *t* = 5.51.** That is a
long-only number, it is significant, and it needs no short leg. It is **25% of the 1.10%/month
over-minus-under spread**; the short leg carries the other **75%**. Within that quintile the best
cell is **underpriced + highest IVOL at +0.63%/month** [4.30].

**Five reasons it does not transfer here, in descending order of force.**

1. **It is a TILT AGAINST A THREE-FACTOR BENCHMARK, not an absolute long-only return.** +0.28% is an
   alpha in `Rᵢ = a + b·MKT + c·SMB + d·HML`. **The programme trades an absolute-return book.** §4
   separates these two claims because they are routinely conflated.
2. **The conditioner needs fundamentals.** The mispricing composite is **11 anomalies** including
   accruals, net operating assets, asset growth, investment-to-assets, gross profitability and
   return-on-assets. Lane `A1` of this round is asking whether that gap is closable; **until it is,
   this is not computable here.**
3. **The price-only half of the same paper has no long-only return.** Among **all** stocks the
   high-minus-low IVOL spread is **−1.30%/month** [−6.92] — a short signal. Its long-only usable end,
   **low IVOL, earns +0.07%/month, *t* = 1.72. Insignificant.** **So the one variable in `A5` this
   programme could compute is the one with nothing in it.**
4. **Sample era.** 1965m8–2011m1. **Only ~5 of those 45 years are post-2005**, and `A2`/`A1` are the
   post-2005 readings.
5. **No trading costs are charged.**

**And the blunt arithmetic nobody in this literature performs — I did it in §9.** On `A1`'s own raw
equal-weighted deciles, **dropping the worst decile from an equal-weighted universe buys +1.7
bp/month gross, and ~0 bp if high-borrow-fee names are already excluded.**

---

## 4. SUB-QUESTION 3 — LONG-ONLY IMPLEMENTATIONS, AND THE DISTINCTION THE LANE ASKED FOR

### 4.1 The distinction, stated first because it decides everything else

**These are two different claims and the literature almost never separates them.**

| | **long-only TILT** | **absolute-return long-only BOOK** |
|---|---|---|
| the claim | a portfolio beats a stated benchmark | a portfolio earns a positive return per unit of risk, funded by cash |
| what is measured | alpha vs CAPM / FF3 / FF5, or tracking error vs an index | total or excess-of-cash return, Sharpe, drawdown |
| what carries the return | the tilt only — market exposure is the benchmark's | **market exposure plus the tilt, and the market exposure dominates** |
| examples here | `A5` (+0.28% FF3 alpha) · `A4` (CAPM alphas) · `A7` (alphas over flip-side legs) | `A6` (hedged long-only, Sharpe 0.56 **net of all costs**) |

**This programme trades the second.** `A4` is explicit about why the distinction bites: *"Because the
long-only portfolios are dominated by general stock market exposure, we also report the unconditional
market betas"* — **small-stock beta 1.26, value beta 1.27, winners beta 1.08** [read in full]. Their
long-only momentum portfolio's headline is **13.6%/yr with 21.8% volatility, Sharpe 0.62** — and its
**CAPM alpha is 5.55%/yr with residual volatility 7.60%, information ratio 0.73.** The Sharpe 0.62 is
**mostly the equity market**. Quoting the Sharpe as a long-only factor result is the conflation.

### 4.2 What the literature reports about building them

**`A7` is the canonical long-only-favourable paper and I could not open it** (§10). Its three claims,
from the **CFA Institute article-page bytes I fetched and read myself**: *"(1) most added value comes
from the long legs, (2) the long legs offer more diversification than the short legs, and (3) the
performance of the short legs is generally subsumed by that of the long legs. These results are
robust over size, time, and markets and cannot be attributed to differences in tail risk."* Plus:
*"the long legs in small caps are most attractive."* **The leg alphas** — long-minus-flip-side-legs of
**0.70 (HML), 2.70 (WML), 0.51 (RMW), 1.19 (CMA), 0.39 (VOL), 1.09 (All) %/month**, short-leg alphas
≈0 to significantly negative, spanning test on the short legs not rejected at **p = 0.87**, and
**0.0% max-Sharpe weight on four of five short legs** — are **restated from `K6`'s `[read in full]`
of its Tables 3–4**, not re-established by me. Sample **1963–2018**.

**`A6` reproduces `A7` and then dismantles the mechanism** [WORKING PAPER, CFM] [read in full]. Three
findings, and the second is the one that matters:

1. **They reproduce the correlation result** — short legs are more correlated with each other than
   long legs are — but the optimal short-leg weight comes out at **30%, not zero.** Their own words:
   *"At the very least, this means that the 'no-short' recommendation is not robust against such
   minor changes."*
2. **The long-leg advantage is mechanically an SMB exposure.** The Fama–French 2×3 building blocks are
   **50% small caps and 50% large caps**, so `(longs − market) − (market − shorts)` reduces to
   `(longs + shorts) − 2·market`, which is **correlated with SMB**. When they hedge with the SPmini —
   *"which is easily implementable as a low-cost hedge"* — the long legs look better, *"However, this
   is because the difference between the two legs is now mechanically exposed to the SMB factor."*
   **The long-leg advantage is a size exposure produced by the benchmark, not a property of the legs.**
3. **Their realistic cost-aware horse race: hedged long-only Sharpe 0.56 vs long-short Sharpe 0.98**,
   both at 6.4% realised volatility, all costs in (Table 1): LH returns+div **8.4%/yr**, trading cost
   **−2.8%**, financing **−2.0%**, no borrow cost; LS **14.2% / −4.8% / −2.6% / −0.6%**. Mean drawdown
   **−8.2% (LH)** vs **−3.9% (LS)**.

**§4.2's honest use for this programme.** `A6`'s hedged-long-only **does** net a positive Sharpe 0.56
after all costs — and it comes from a long-short shop, so the number is in the conservative direction.
But: it is a **five-factor equal-weighted combination** (signal combination is excluded ground), it is
**global** across USA-Canada/Europe/Asia/Australia not US-only, it spans **2000–2020** so it is
half pre-2006, its costs come from an **undisclosed in-house model including square-root market
impact**, it uses **a `$1`bn AUM and a 3%-per-name cap**, it turns over **~0.5% of AUM per day**, and
it is **not peer-reviewed**. **It is the best evidence in this brief that a hedged long-only book can
net something. It is not evidence that this programme's can.**

### 4.3 The documented dilution from dropping the short leg

**Four numbers, from four different samples, and they do not agree — which is itself the finding.**

| source | sample | dilution measure | figure |
|---|---|---|---|
| `A2` [read in full] | post-2005, top-90% cap | long-minus-market vs long-short, cross-sectional means | **0.08% → −0.04% /month. More than 100% of the return lost** |
| `A1` [read in full] | 2006–2020, `$1`/`$50`mn floors, EW | decile 10 abnormal vs decile 10 − decile 1 | **+0.15% → −0.09% /month. More than 100% lost** |
| `A4` [read in full] | 1926–2011, FF 2×3 | long-leg CAPM alpha ÷ long-short CAPM alpha | **size 2.05/1.42 · value 2.93/3.45 = 85% · momentum 5.55/10.48 = 53%** |
| `A6` [read in full] | 2000–2020, global, 5 factors, all costs | hedged-long-only Sharpe ÷ long-short Sharpe | **0.56 / 0.98 = 57% retained** |

**Where I would weight, and why.** For the post-2010, US-only, cost-honest question **I weight `A2`
and `A1`**, because they are the only two measured in the era and universe that bind, they use
different benchmarks (raw market return vs DGTW characteristic matching) and different anomaly sets
(170 vs 162) and **reach the same sign**. `A4` and `A6` are measured on samples dominated by the
pre-2006 era; `A4` charges no costs at all. **All four stay on the record.**

### 4.4 The excluded-ground boundary in this sub-question, flagged

`A8`'s content is **mean-variance spanning tests across groups of short-sale restrictions, plus
130/30** [WORKING PAPER, Amundi] [read in full]. **That is position sizing and portfolio
construction, which is excluded ground**, and its conclusion — *"risk-averse investors prefer freely
optimized long-only portfolios over factor-based portfolios"* — is a construction result, not a
return result. **I did not pursue it.** What it is useful for is one citation trail it preserves:
*"Blitz et al. (2014) show that, when transaction costs and strategy capacity are factored in,
long-only factors are preferable to long-short ones"* and *"Israel and Moskowitz (2013) show that…
the long legs of factor styles typically generate over 50% of total performance."* **Both are
`[UNVERIFIED]` as restated inside `A8`; the second I then established directly as `A4`, and §5.2 shows
the restatement is weaker than the paper.**

---

## 5. SUB-QUESTION 4 — IS THE SHORT-LEG CONCENTRATION GENERAL OR COHORT-SPECIFIC? (PUSHED HARD, AND THE ANSWER IS SPLIT)

**This is the sub-question the commissioning note flagged as decisive, and the answer is genuinely
two-sided. I report both halves.**

### 5.1 The half that says COHORT-SPECIFIC — and it is a cohort this programme removes

**(a) Hard-to-borrow.** `A1`'s whole paper. High-fee stocks are **12% of stock-dates**; decile 1
carries **21.91%** of them at a **2.70%/yr** fee against ~**9.4–10.2%** at ~**1.10%/yr** in the middle
deciles. **Remove the high-fee names and the short leg's abnormal return goes from −0.24% to 0.00%
and the spread from +0.15% [2.93] to +0.04% [0.81].** `A1`'s abstract: *"anomalies are not profitable
even before fees if the high-fee observations… are excluded."*

**(b) Microcaps.** `A2`'s two-by-two: **restricting to post-2005 cut median returns ~60%, restricting
to the top 90% of market cap cut them ~one-half, and together ~85%** [read in full]. `A9`: 12
characteristics were reliable independent determinants in **non-microcap** stocks 1980–2014, but
*"return predictability sharply fell in 2003 such that just two characteristics have been independent
determinants since then"*, and **outside microcaps the hedge returns have been insignificantly
different from zero since 2003** [abstract only, and the post-2003 figures reached me via a
summariser — though the same sentence appears quoted verbatim inside `A1`'s literature review, which I
read in full].

**(c) Price — §5.3, and it is the sharpest cell in the brief.**

**(d) Distress.** Named and not pursued: **the distress anomaly is excluded ground.** The relevant
literature (Avramov, Chordia, Jostova & Philipov) reports anomaly profits concentrated in
low-credit-rating names. **I did not research it; I flag that a distress-cohort explanation exists and
that this programme has ruled the territory out.**

### 5.2 The half that says NOT COHORT-SPECIFIC — `A4`, and why its abstract overstates it

`A4` is the strongest counter-evidence in the literature, it is peer-reviewed, and **reading it in
full weakens it substantially** [PEER-REVIEWED] [read in full].

**Table 1 — CAPM alphas, annualised %, `t` in parentheses.** Reconstructed from a garbled layout
extraction and **verified by the identity `long − short = spread` holding in three separate period
columns** (1926–2011: 2.05−0.65=1.40 vs 1.42 · 2.93−(−0.58)=3.51 vs 3.45 · 5.55−(−4.94)=10.49 vs
10.48; 1963–2011 and 1990–2011 likewise):

| | **long leg** | short leg | spread | **long leg 1990–2011** |
|---|---|---|---|---|
| **Size** (Small / Big / SMB) | **+2.05 (1.72)** | +0.65 (1.40) | +1.42 (1.16) | **+2.27 (1.07)** |
| **Value** (High / Low / HML) | **+2.93 (2.40)** | −0.58 (−0.87) | +3.45 (2.80) | **+2.98 (1.66)** |
| **Momentum** (Up / Down / UMD) | **+5.55 (6.74)** | −4.94 (−3.74) | +10.48 (6.13) | **+4.68 (2.71)** |

**Five things that cut `A4` down, all from its own text.**

1. **Their own statistical test cannot reject an equal split.** *"However, across all size groups, we
   cannot reject that the abnormal profits to value and momentum trading are generated equally by long
   and short positions."* **The abstract's "almost all of size, 60% of value, half of momentum" are
   point estimates that are not statistically distinguishable from 50/50.**
2. **They charge no trading costs.** *"Without having to specify a trading cost model, which is
   investor specific, we acknowledge that small stocks are more costly and more difficult to trade and
   that shorting is more costly and more constrained."* **Not a cost-honest source.**
3. **The ">100% from the long side" figures are raw-excess-of-T-bill, not market-adjusted, and they
   say so.** *"More than 100% of these return differences come from the long side… However, adjusting
   for market exposure and market returns changes the picture somewhat."* The market-adjusted value
   split is **47% long in the smallest quintile** rising to **nearly 90% in the largest**.
4. **Long-only value exists only in microcaps.** *"The value premium… is largely concentrated only
   among small stocks and is insignificant among the largest two quintiles of stocks (largest 40% of
   NYSE stocks)"*, and *"strong positive alphas for long-only value among small cap stocks and
   insignificant alphas among large caps."* Their size quintile 1 averages **`$156`mn market cap** and
   quintile 2 **`$855`mn**, and they concede *"Stocks in Quintiles 1 and 2 could face significant
   trading costs for any reasonably sized portfolio."*
5. **All three of `A4`'s anomalies are dead post-2005 in the investable universe, and its one robust
   long-only survivor is this programme's excluded ground.** `A2` Table 3 gives the post-2005,
   top-90%-of-cap long-short distribution by category. **I reconstructed it from a garbled extraction
   and validated the row assignment with an internal consistency check — the median's sign must agree
   with the share positive, and it does on all eight rows** (Intangibles median 0.00 ↔ 50% positive is
   the tightest of them). **This also independently confirms `K6`'s reading of the same table** (its
   Trading/Liquidity cell: 85%, N = 13, median 0.11%):

   | category | N | mean %/mo | median %/mo | % positive |
   |---|---|---|---|---|
   | **Momentum** | 17 | **+0.01** | +0.05 | **53** |
   | **Profitability** | 9 | **+0.25** | +0.24 | **78** |
   | **Value / Fundamentals** | 15 | **−0.02** | **−0.04** | **47** |
   | Investment / Growth | 36 | +0.09 | +0.06 | 69 |
   | Trading / Liquidity | 13 | +0.09 | +0.11 | 85 |
   | Accruals / Accounting | 18 | +0.09 | +0.06 | 72 |
   | **Intangibles** | 12 | +0.04 | **0.00** | **50** |
   | Other | 50 | +0.10 | +0.11 | 72 |
   | **All** | **170** | **+0.08** | **+0.07** | **67** |

   > **`A4`'s long-only evidence is for size, value and momentum. Post-2005 in the investable
   > universe, value's median long-short return is NEGATIVE (−0.04%/month, 47% positive) and
   > momentum's is +0.05% with 53% positive — a coin flip. `A4`'s only long-leg result significant in
   > every size quintile and every subperiod is momentum, which is excluded ground here and a coin
   > flip there.** `A2`'s own one-line reading: *"Profitability is the only category with a healthy
   > median return. Momentum, value, and intangibles-based anomalies no longer outperformed in this
   > universe."*

**And `A4`'s own recorded reversal is a warning about this whole sub-question.** Hong–Lim–Stein (2000)
and Grinblatt–Moskowitz (2004) found momentum stronger in small caps and short-leg driven; `A4` shows
that result *"seems to be unique to the 1980 to 1996 sample period"* and disappears outside it.
**Cohort findings in this literature have flipped on sample period before.**

### 5.3 PRICE, NOT SIZE — and `K6`'s confirmed absence is now PARTLY FILLED

**`K6` reported it could not find a single paper reporting the nominal share price distribution of any
anomaly's legs. I found one.** `A3`, Li, Sullivan & Garcia-Feijóo, FAJ 70(1) 2014, reports **average
share price per IVOL quintile alongside the alphas** [PEER-REVIEWED] [read in full], 1963–2010,
value-weighted, FF3-adjusted, one-month holding:

| IVOL quintile | **Table 5 — all stocks** | | **Table 6 — excluding `P < $5`** | |
|---|---|---|---|---|
| | **avg price** | alpha (t) | **avg price** | alpha (t) |
| 1 (lowest IVOL = **the long leg**) | **`$55.60`** | **+0.08 (1.87)** | **`$61.50`** | **+0.12 (2.64)** |
| 2 | `$29.20` | +0.07 (1.13) | `$35.60` | +0.07 (1.26) |
| 3 | `$19.20` | +0.09 (1.09) | `$24.50` | +0.07 (1.06) |
| 4 | `$13.50` | −0.30 (−2.35) | `$19.50` | +0.03 (0.27) |
| 5 (highest IVOL = **the short leg**) | **`$7.03`** | **−1.11 (−5.90)** | **`$14.30`** | **−0.26 (−1.82)** |
| **1 − 5** | | **+1.19 (6.04)** | | **+0.38 (2.47)** |

**Read that table and the sub-question answers itself.**

> **The long leg's average price is `$55.60`. The short leg's is `$7.03`. A single `$5` price screen
> takes the short leg's alpha from −1.11% to −0.26% a month — a 77% reduction — takes the spread from
> 1.19% to 0.38% — a 68% reduction — and leaves the long leg UNCHANGED at +0.08% → +0.12%.**

`A3`'s own conclusion, verbatim: *"the anomalous returns of value-weighted portfolios are largely
eliminated when low-priced (less than `$5`) stocks are omitted — **and are not at all present in
equal-weighted portfolios**."*

**Three further cells of `A3` that bind directly on this programme's configuration.**

1. **EQUAL WEIGHTING, which is what this programme does.** IVOL zero-cost alpha, equal-weighted:
   **1963–2010 +0.40% (1.88) · 1963–1990 +0.76% (4.24) · 1991–2010 +0.05% (0.11) · 1991–2007 −0.15%
   (−0.29)**, against value-weighted **1.19 (6.04) / 1.44 (9.39) / 1.02 (2.56) / 0.79 (1.68)**.
   **Post-1990 and equal-weighted, there is nothing.**
2. **Non-penny universe, post-1990.** *"over 1991–2010 (in unreported results), we found an
   insignificant zero-cost portfolio abnormal return of 0.24 (t-statistic = 0.80)."*
3. **Liquidity.** In the highest-liquidity tercile the alpha falls from 1.19% to **0.45%/month** — a
   ~60% reduction — and vanishes entirely under a liquidity-tercile-then-IVOL-quintile double sort.
   **A trailing dollar-volume screen does the same thing the `$5` floor does.**

**And `A1` supplies the mirror image, which stops this becoming a one-sided story.** `A1` **drops
lagged price below `$1` and market cap below `$50`mn** and says *"our results become stronger without
the penny stock filters"* — i.e. the long-short effect **weakens as the price and size floors rise.**
**Both papers agree on the direction: raise the floor, lose the effect.** This programme's floor is
`$5` — **five times `A1`'s** — **and `A1` already says `$1` makes its result weaker.**

### 5.4 The split verdict, stated as a verdict

**On the evidence I established, the short-leg concentration is BOTH.**

> **General, as a fact about the long leg:** the long leg's own return is at or below zero in **every**
> cut I read — `A2`'s −0.04%/month across 170 anomalies, `A1`'s −0.09% across 162, `A1`'s −0.05/−0.12/
> −0.17 across all three signal categories, `A3`'s +0.08% (t = 1.87) for low-volatility. **This does
> not depend on a cohort.**
>
> **Cohort-specific, as a fact about the short leg's MAGNITUDE:** the short leg's alpha is largely
> a hard-to-borrow, microcap and **sub-`$5`** phenomenon, and `A1`/`A3` both measure it away with
> screens weaker than this programme's.
>
> **Which means the commissioning note's hopeful reading — "if the short-leg return lives in names
> our `$5` floor already removes, the finding may not describe our universe" — is TRUE AND DOES NOT
> HELP.** The screens remove the short leg's return. They do not create a long leg's. **The
> programme's universe is one in which the published anomalies have no short-leg return to envy and
> no long-leg return to capture.**

**One counter-cell, recorded because it is the only one that survives the screen.** `A1` Table 7,
raw equal-weighted, **excluding high-fee stocks**: the **Investment** factor retains
**D10 − D1 = +0.27%/month (t = 1.29)**, where Momentum falls to **+0.02% (0.04)**, Profitability to
**+0.10% (0.26)** and Book-to-market to **−0.22% (−0.47)**. **It is insignificant, it is an accounting
signal needing fundamentals, and its long leg (1.05%) barely exceeds the universe's ~1.05%. But it is
not zero, and "all of it was hard-to-borrow" is therefore not universally true.**

---

## 6. SUB-QUESTION 5 — CONDITIONING RATHER THAN SELECTING: WHERE THE LITERATURE IS, AND WHERE IT LANDS

**Flagged, not pursued. Essentially all of it is excluded ground, and I am reporting the map rather
than walking it.**

### 6.1 What the literature reports, and the exclusion each answer trips

| claim | source | **where it lands** |
|---|---|---|
| Market-neutral equity factors are strongly and robustly predictable from the **book-to-market ratio of the factor portfolios**; out-of-sample monthly R² ≈ **4%**; exploiting it substantially improves performance | `A10` Haddad, Kozak & Santosh, RFS 2020 [PEER-REVIEWED article; I have the NBER PDF and did **not** read it — `[abstract only]`] | **EXCLUDED — a valuation-spread regime gate.** Also needs fundamentals. **And note it times MARKET-NEUTRAL factors, so it does not even address a long-only book's exposure** |
| Scaling exposure by inverse realised variance raises Sharpe | `A11` Moreira & Muir, JF 2017 [abstract only, via a summariser] | **EXCLUDED — a volatility regime gate** |
| **Those strategies fail out of sample**; out-of-sample versions *"generally earn lower certainty equivalent returns and Sharpe ratios than do simple investments in the original, unmanaged portfolios"*, from structural instability in the spanning regressions | `A11` Cederburg, O'Doherty, Wang & Yan, JFE 2020 [abstract only, via a summariser] | **EXCLUDED, and the peer-reviewed out-of-sample verdict is NEGATIVE** |
| Anomaly short-leg profitability is concentrated after **high investor sentiment**; *"None of the 11 long legs exhibits a significant difference between high- and low-sentiment periods"*, long legs differing by **4 bp/month** | Stambaugh, Yu & Yuan, JFE 2012 — **restated from `K6`'s `[read in full]`**; the mechanism corroborated in `A5` which I read in full | **EXCLUDED — a sentiment regime gate.** Its long-only content is the 4 bp/month non-result |

### 6.2 The one thing worth carrying out of §6

**The conditioning literature's own long-only content is a null.** `A5`'s time-series result is that
the **negative** IVOL effect among overpriced stocks strengthens after high sentiment while the
**positive** effect among underpriced stocks weakens — *"when aggregating across all stocks, the
average negative relation between IVOL and expected return… should be stronger in periods when there
is a market-wide tendency for overpricing"* [read in full]. **The timing variation is concentrated on
the side you cannot trade.** And Stambaugh–Yu–Yuan's 11 long legs move **4 bp/month** between
sentiment regimes.

> **So even if the exclusion on regime gates were lifted, the documented timing effect is a
> short-leg effect. The long legs barely move.** That is a reason to keep the exclusion, not a reason
> to revisit it.

**Consistency note worth flagging to the principal:** `A2` itself closes by naming *"Dynamic factor
timing (Haddad, Kozak, and Santosh 2020; Moreira and Muir 2017), machine-learning combinations…, and
strategies that exploit proprietary or alternative data"* as what lies **beyond** its negative result.
**Every one of those three escape routes is on this programme's exclusion list** — regime gates,
signal combination and ML return prediction, and vendor data. **The paper's own list of exits is the
programme's own list of closed doors.** That is not an argument against the exclusions; it is a
statement of where the programme has placed itself.

---

## 7. SUB-QUESTION 6 — THE LONG LEG WITH THE SHORT LEG REPLACED BY A MARKET HEDGE, OR BY CASH

**Treated as a question about documented evidence, not about choosing a construction (position sizing
and portfolio construction are excluded ground).**

### 7.1 Replaced by a MARKET HEDGE (beta ≈ 1 short index)

**This is exactly the statistic `A2` reports, and it is the central negative of this brief.**
Long-minus-market, where the market leg is *"the raw Fama-French market return, computed as Mkt – RF
plus RF"*: **cross-sectional mean −0.04%/month, SD 0.13%, mean t = −0.31, Var(t) = 0.98 < 1, every
empirical-Bayes estimate 0.00%** [read in full]. Best single case **+0.40%/month** (cash-based
operating profitability). **Gross.**

**`A6` is the only source that hedges the long leg with a real, tradeable index and charges real
costs** [WORKING PAPER, CFM — interested against this conclusion] [read in full]: **hedged long-only
Sharpe 0.56** at 6.4% volatility, 2000–2020, global, five combined factors, **8.4%/yr gross return
less 2.8% trading and 2.0% financing**, mean drawdown **−8.2%**. Against long-short's **0.98** and
**−3.9%**. **Positive, and 57% of the long-short Sharpe.** Caveats in §4.2 — the decisive ones for
here being **signal combination, global universe, half the sample pre-2006, and an undisclosed
in-house cost model.**

**And `A6` contains the one finding that reconciles the conflict**: the long leg's apparent advantage
over the short leg, when the hedge is a real large-cap index, is **mechanically an SMB exposure**
created by the Fama–French building blocks being 50% small-cap. **So "the long leg beats the market"
in `A7`'s sample is partly "small beats large".**

### 7.2 Replaced by CASH (unhedged long-only)

**Two readings and they are not in conflict — they measure different things.**

**`A4`**, 1926–2011, no costs [read in full]: long-only momentum **13.6%/yr excess of T-bills, 21.8%
vol, Sharpe 0.62**; long-only value **12.4% / 26.5% / 0.47**; long-only size **11.5% / 26.3% / 0.44**.
**Those Sharpes are mostly the equity risk premium** — betas **1.08, 1.27, 1.26** — and the authors
say so. The tilt's own contribution is the CAPM alpha: **5.55% / 2.93% / 2.05%** with information
ratios **0.73 / 0.26 / 0.19**.

**`A1`**, 2006–2020, equal-weighted, raw [read in full]: the cash-funded long leg earned **0.96%/month
against 0.99% for decile 5 and 1.00% for decile 9** in the full sample, and **1.09% against ~1.05%**
once high-fee names are excluded. **The signal's top decile is worth about 0 to 4 bp/month over the
middle of the universe, before costs.**

> **The two are the same statement at different altitudes. Unhedged long-only earns the equity risk
> premium. The anomaly contributes somewhere between −3 and +4 bp/month gross in the modern sample,
> and the question of whether that survives 67.6 bp per round trip does not need asking.**

---

## 8. CONFLICTS — RECORDED, NOT ADJUDICATED

Per the standing instruction. **All readings stand. Where I state a preference it is reported as my
preference, and nothing is discarded.**

### 8.1 `C-A3-1` — Is the surviving return in the short leg? *(this is `C12` from round 6, now with a third party)*

| reading | statistic | sample | costs |
|---|---|---|---|
| **`A2` (Chen & Welch): YES** | long leg minus **raw market return**; dispersion of *t* below the luck null | **post-2005 only**, top 3,000 ∩ top 90% cap, ~170 anomalies | **none charged** |
| **`A1` (Muravyev et al.): YES** | decile 10 **DGTW characteristic-matched** abnormal return; decile-vs-decile raw returns | **2006–2020**, `$1`/`$50`mn floors, **equal-weighted**, 162 anomalies | **borrow fees only** |
| **`A7` (Blitz et al.): NO** | each leg regressed on **the opposite legs of the other factors**; long-only leg Sharpes **retaining full market exposure** | **1963–2018**, FF 2×3, 5 factors | **none charged** |
| **`A4` (Israel & Moskowitz): NO, but cannot reject 50/50** | long-leg **CAPM alpha** and % of spread from the long side | **1926–2011**, FF 2×3 + own 25 portfolios, 3 anomalies | **none charged** |
| **`A6` (CFM): PARTLY — reproduces `A7`, weight on shorts 30% not 0%, and attributes the gap to SMB** | leg Sharpes and correlations under **two different hedge indices**; then a full cost-aware optimisation | **2000–2020**, global, 5 factors | **all costs charged** |

**`K6` recorded this as "different statistics AND different samples" and that remains exactly right.
This lane adds three things.**

1. **`A1` is a second "yes" from an independent group with independent portfolio construction**
   (Michigan State / Illinois; Markit borrow data; DGTW benchmarks) — which **repairs `K6`'s
   self-flagged largest fragility**, that its post-2005 collapse rested on four sources sharing one
   author and one dataset. **`A1` shares only the Chen–Zimmermann signal definitions, not the
   authorship or the method.**
2. **`A6` is the first source to reproduce a "no" paper and locate the mechanism of the disagreement:
   an SMB exposure created by the 2×3 construction.** That is a substantive narrowing, not a tie.
3. **`A4`'s own test cannot reject an equal long/short split**, which makes the strongest "no"
   weaker than its abstract.

**Which I would weight, and why.** For the post-2010, US-only, `$5`-floored, equal-weighted,
cost-charged question **I weight `A1` first and `A2` second.** `A1` because it is equal-weighted, its
era is 2006–2020, it reports every decile, and it charges a real cost; `A2` because it is the only
source measuring the investable-universe era directly and it reports the statistic the question asks
for. **`A7` and `A4` are measured on samples more than two-thirds pre-2006, neither charges a basis
point, and both are authored by parties whose business is long-only factor products. `A6` is the best
evidence for a hedged long-only book netting anything and comes from a party interested against that
conclusion — which is why I carry it prominently rather than discount it.** **No reading is
discarded.**

### 8.2 `C-A3-2` — `A1`'s draft versus `A1`'s published article disagree on the sign

**Caught by reading both** — the 2022 draft in full and the published abstract from RePEc's own page
bytes:

| | **draft, 1 Sep 2022** | **published, JF 80(6) 2025** |
|---|---|---|
| long-short before short-sale costs | **0.15% / month** | **0.14% / month** |
| after borrow-fee adjustment | **0.02% / month** | **−0.01% / month** |
| high-fee share | **"12% of all stocks"** | **"12% of stock dates"** |

**The sign flipped between draft and publication: +0.02% became −0.01%.** The draft is the freely
indexed one and is the text I read in full; **the published version governs, and the published
version is the more negative.** This is the **second** instance this campaign has caught of a
freely-indexed draft differing from its published article on a load-bearing number — `K6` found the
first, in Chen & Velikov, where the draft's reliable turnover predictor became "no reliable
predictor, wrong sign" on publication. **Treat every freely-indexed draft in this area as
provisional.**

**And the draft is internally inconsistent with itself on a second set of figures, which I caught by
reading both the prose and the table.** `A1`'s body text gives the decile-1, decile-2 and decile-10
high-fee shares as **21.32%, 13.56% and 17.64%**; its **Table 2, Table 4 and Table 9 all print
21.91%, 13.73% and 18.33%** — the same three numbers in three separate places, disagreeing with the
prose by 0.17 to 0.69 points. **Neither version changes any conclusion in this brief. I report the
table's figures and record that the draft's own prose disagrees with its own tables**, because it is
further reason to treat the December-2020-vintage decile tables as provisional against the published
article I could not obtain.

### 8.3 `C-A3-3` — Does the `$5`/penny cohort carry the effect, or merely some of it?

`A3`: excluding `P < $5` cuts the spread **68%** and the short leg **77%**, and equal-weighted there
is *"no anomalous return"* at all [read in full]. `A1`: already applies a **`$1`** floor and states
*"our results become stronger without the penny stock filters"*, yet still finds **+0.15%/month
[2.93]** with the `$1` floor on — so the `$1` floor does **not** kill it. **Both stand: the effect
decays with the price floor, and `$1` is not enough to kill it while `$5` plus equal weighting is
enough to kill `A3`'s.** These are different anomalies (one low-volatility, one an average of 162), so
**this is two data points on a gradient, not a contradiction.**

### 8.4 `C-A3-4` — `A4`'s abstract versus `A4`'s own test

Abstract: *"long positions make up almost all of size, 60% of value, and half of momentum profits."*
Body: *"across all size groups, we cannot reject that the abnormal profits to value and momentum
trading are generated equally by long and short positions."* **The point estimates and the hypothesis
test say different things, in the same paper, both [read in full]. I report both and weight the
test.**

### 8.5 `C-A3-5` — the `$5` floor's effect on price-distribution evidence: a CONFIRMED ABSENCE NOW PARTLY FILLED

**`K6` §8.2 recorded:** *"I did not find a single paper reporting the median or distribution of
nominal share price in an anomaly's long or short leg."* **`A3` reports exactly that, per quintile,
in two tables** (§5.3). **`K6`'s absence was real for its sources and is not general.** What remains
absent: **no paper I read reports the price distribution of a post-2005 anomaly's legs.** `A3`'s
1963–2010 is the closest, and its post-1990 cells are the closest within that. **Recorded as a
narrowed, still-open absence.**

---

## 9. MY OWN ARITHMETIC ON PUBLISHED NUMBERS — WHAT "AVOIDING THE BAD NAMES" IS WORTH

**`[MY ARITHMETIC]`, not a result from any paper.** No source I read computes this, and the
commissioning note asked for it directly. Inputs are `A1`'s Table 5 raw equal-weighted decile
returns, read in full. **Re-runnable from `A1` Table 5 alone.**

A long-only equal-weighted book over the whole universe earns the mean of the ten deciles. Excluding
the worst decile, it earns the mean of the other nine.

| universe | mean of all 10 deciles | mean of deciles 2–10 | **gain from dropping decile 1** | **breakeven one-way monthly turnover at 67.6 bp round trip** |
|---|---|---|---|---|
| **`A1` Panel A — all stocks** | 0.953% | 0.970% | **+1.7 bp/month (+0.21%/yr)** | **2.5% of the book per month** |
| same, dropping deciles 1 **and** 2 | 0.953% | 0.976% | **+2.3 bp/month (+0.28%/yr)** | 3.4% per month |
| **`A1` Panel B — high-fee names already excluded** | 1.048% | 1.049% | **+0.1 bp/month** | **~0.1% per month. Nothing.** |

**Three readings.**

1. **The honest size of the prize is 1.7 bp/month gross**, and it is **0.1 bp** in a universe that has
   already dropped the hard-to-borrow names — which a `$5` floor plus a dollar-volume screen
   substantially does. **The exclusion strategy's value is almost entirely the value of holding the
   hard-to-borrow tail and then not holding it.**
2. **The turnover budget is the binding constraint, and it is tight.** 2.5% of the book per month
   one-way. `A2`'s survivors rebalance annually at **1.2–7.2%/month one-sided**, so the *lower* half
   of that range fits and the upper half does not. **A dated-event book at this programme's horizon
   does not fit at all.**
3. **The same arithmetic on `A3`'s IVOL quintiles gives a larger number that then evaporates.**
   Dropping the top IVOL quintile from an equal-weight-across-quintiles book: all stocks
   **−0.234% → −0.015% = +21.9 bp/month**; excluding `P < $5` **+0.6 bp → +7.3 bp = +6.7 bp/month**
   (breakeven turnover 9.8%/month). **But those are VALUE-WEIGHTED quintile alphas, and `A3`'s own
   equal-weighted result for the same anomaly is +0.05% (t = 0.11) for 1991–2010 and "not at all
   present in equal-weighted portfolios".** **I report the arithmetic and then report that the paper's
   own equal-weighted measurement contradicts it. The paper wins.**

### The one thing I could not check, and it is the most relevant paper to this section

`A12` (Cirulli & Walker, *Outperforming Equal Weighting*, SSRN 4669267) asks **precisely** this
question — whether an equally weighted portfolio is improved by screening out the worst 10/20/30/40/50%
on factor scores. **SSRN refused me and the blog that summarises it 403'd** (§10). A search summariser
relayed that excluding the worst 10% (50%) by five-year Sharpe raised returns to 8.2% (9.1%).
**I am not reporting those as figures.** They are `[UNVERIFIED]`, they came through two layers of
summarisation, the screens named are **momentum and volatility** (momentum is excluded ground), and no
cost treatment was described. **If one document in this brief is worth re-attempting with other
access, it is this one, because it is the only paper I found asking this programme's exact
equal-weighted exclusion question.**

---

## 10. BLOCKS — BY TOOL AND RESPONSE, NEVER BY HOST

| tool + request | response | consequence |
|---|---|---|
| `curl` GET, UA `A3-research/1.0 (research@backtest-framework.org)` → `tandfonline.com/doi/full/10.1080/0015198X.2020.1779560` | **HTTP 403, 5,631-byte `text/html`** | `A7` is `[abstract only]`; its leg alphas are restated from `K6`'s prior reading |
| same → `tandfonline.com/doi/pdf/10.1080/0015198X.2020.1779560` | **HTTP 403, 5,628-byte `text/html`** | as above |
| same → `papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID3493305_code16198.pdf` | **HTTP 403, 5,783-byte `text/html`** | as above |
| same → `papers.ssrn.com/sol3/Delivery.cfm/4669267.pdf` | **HTTP 403, 5,711-byte `text/html`** | `A12` is `[UNVERIFIED]`; end of §9 |
| same → `alphaarchitect.com/low-priced-stocks/` | **HTTP 403, 5,506-byte `text/html`** | I could not read the blog; I found the primary paper (`A3`) by other means instead, which is the better outcome |
| same → `mysimon.rochester.edu/novy-marx/research/AA.pdf` (*Assaying Anomalies*) | **HTTP 404, 20,636-byte `text/html`** | Still unobtainable. **Worth noting the contrast: `K6` got HTTP 200 with a 19,490-byte faculty page from `rnm.simon.rochester.edu`; this host path returns an honest 404.** Same document, two hosts, one lies about status and one does not |
| same → `finance.wharton.upenn.edu/~stambaug/ShortOfIt.pdf` and `.../shortofit.pdf` | **HTTP 404, 221- and 243-byte `text/html`** | Stambaugh–Yu–Yuan (2012) not re-established; I rely on `K6`'s prior `[read in full]` and on `A5`, which I read in full and which shares the 11-anomaly composite |

**One HTTP 200 that was wrong, and it was my error not a host defect.** `curl` → 
`nber.org/system/files/working_papers/w17231/w17231.pdf` returned **HTTP 200, `application/pdf`, 
539,981 bytes, a genuine 10-page NBER working paper** — *The Land That Lean Manufacturing Forgot?
Management Practices in Transition Countries* (Bloom, Schweiger & Van Reenen). **I had guessed the
working-paper number for `A4`.** Status, content-type and `file` all passed; only reading the first
400 characters caught it. **A tenth flavour for the programme's list: correct host, correct format,
genuine document, wrong paper — catchable only by reading the title.**

**One negative control, run deliberately.** `curl` → `arxiv.org/abs/2607.99999`, an ID that must not
exist, returned **HTTP 404** with *"There is no record of an article with identifier
'2607.99999'"* — while `arxiv.org/abs/2607.06502` returned 200 with *"[Submitted on 7 Jul 2026]"* and
**a single version, v1**. **The endpoint distinguishes real from fake IDs, so `A2`'s v1-only status is
established and not an artefact.**

**One summariser caught editorialising, logged per the summariser rule.** A search summariser, asked
about long-only net-of-cost evidence, relayed Novy-Marx & Velikov's finding that *"most anomalies with
less than 50% turnover per month generate significant net spreads"* and then appended, in its own
voice: *"This suggests that low-turnover long-only strategies may be more viable than their long-short
counterparts after accounting for costs."* **The source statement is about long-SHORT net spreads. The
summariser converted it into a claim about long-only viability that no source makes.** Recorded as a
seventh caught instance for this campaign's tally.

**No page, PDF or search result contained text addressed to me or instructing me to take an action.**
Had one done so I would have quoted and flagged it rather than acted. **No accounts, no credentials,
no logins, no form submissions, no API-key registration.** The only contact string used in any
User-Agent was `research@backtest-framework.org`.

---

## 11. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **`A7` (Blitz, Baltussen & van Vliet 2020) — the single most important counter-evidence — I could
   not open.** Three separate refusals (§10). Its leg alphas in §4.2 are **restated from `K6`'s
   reading, not established by me**, and its three headline claims come from the CFA Institute
   **article page**, which is an editorial summary even though I fetched and read its bytes myself.
   **Every inference I draw against `A7` rests on `A6`'s reproduction of it, not on my own reading of
   it.** If `A6`'s reproduction is itself wrong, my §8.1 narrowing collapses.
2. **`A12` (Cirulli & Walker) is `[UNVERIFIED]` and it is the paper most directly on this
   programme's own question** — equal-weighted exclusion screening; end of §9. **I report no figure from
   it.**
3. **The text I read for `A1` is the September 2022 draft, not the 2025 Journal of Finance article.**
   Every decile figure in §2.2, §3.1, §5.1 and §9 is from the **draft**. §8.2 shows the draft and the
   published version disagree on the sign of the headline net figure, so **the decile tables may also
   have changed and I cannot know by how much.** The published abstract I read directly, and it is the
   more negative of the two.
4. **`A2` is an unrefereed single-version July-2026 draft, and it is not independent of this
   programme's other load-bearing sources.** A. Y. Chen authors `A2`, Chen & Velikov (2023), Chen &
   Zimmermann (2022) and Chen–Lopez-Lira–Zimmermann. **`A1` is the independent corroboration this
   lane adds — but `A1` uses Chen & Zimmermann's signal code, so the SIGNAL DEFINITIONS are shared
   even where the method, data and authorship are not.** The independence is partial.
5. **Three of my load-bearing tables were reconstructed from garbled layout extractions.** `A4`
   Table 1, `A5` Table 2 and `A2` Table 2 all came out column-scrambled. **I verified each by
   identity or against prose** — `A4` by `long − short = spread` holding in three period columns;
   `A5` against four numbers the paper states in prose; `A2` by each signal matching its known
   original paper. **`A4` Table 3 I could NOT verify this way and I therefore report none of its
   numbers, only the prose around it.** And `A1`'s Table 1 market-capitalisation percentiles extracted
   misaligned — the value `9.32` in that row belongs to the utilisation median per the paper's own
   prose — **so I report no market-cap distribution from `A1`.**
6. **`A9` (Green, Hand & Zhang) is `[abstract only]` and its "since 2003" figures reached me through
   a search summariser**, which under this campaign's rule is **weaker than `[snippet only]`. The
   partial mitigation is that the same sentence appears quoted verbatim inside `A1`, which I read in
   full — a second-hand route to a first-hand number, not a substitute for it.**
7. **`A10` and `A11` are `[abstract only]`, `A11` via a summariser, and both are excluded ground.**
   I downloaded the Haddad–Kozak–Santosh NBER PDF and **did not read it**. **Nothing in §6 should be
   treated as established at the level of §2–§5.** I read none of the factor-timing literature's
   tables, so I cannot say whether the 4% out-of-sample R² is long-only-relevant; I can only say the
   object timed is market-neutral factors.
8. **No source I read tests this programme's configuration.** None uses **daily bars**; all are
   monthly. None is **dead-inclusive at ~35.7%**. None combines a **`$5` as-traded floor with a
   trailing dollar-volume screen**. None reports an **overnight-only** return. And none addresses
   **~10 effective independent instruments across 1,573 names** — which is the constraint I am least
   able to speak to, because every paper here relies on diversification across 20–300 names per leg
   and `A2` explicitly declines to trade a month when either leg holds fewer than 20. **A long-only
   book with ten effective instruments has less room than any portfolio in this literature, and I
   found no evidence bearing on it.**
9. **I read figures as extracted text, never as images.** `A1`'s Figures 1–3, `A2`'s Figures 1–3,
   `A5`'s Figure 1 and `A6`'s Figures 1–8 were established from captions and surrounding prose.
   **`A6`'s Sharpe ratios 0.56 and 0.98 and its cost breakdown come from its Table 1 and its prose,
   which agree; its per-factor results exist only in plotted curves and I cannot confirm them.**
10. **The price-distribution evidence is one anomaly, one era.** §5.3 rests entirely on `A3`, whose
    sample ends in **2010** and whose anomaly is **low-volatility only**. **I found no post-2005 price
    distribution for any anomaly's legs.** Generalising `A3`'s `$55.60`-vs-`$7.03` split to the other
    161 anomalies in `A1` would be unwarranted, and `A1`'s own decile-10 fee and size pattern shows
    the cheap leg is **not** always the short one.
11. **I did not establish the borrow constraint's actual shape for this account.** Everything in §3.1
    concerns borrow fees in Markit's indicative data, 2006–2020, for institutional short sellers.
    **This programme's shorting is described as "constrained" and borrow is excluded ground; I did
    not and could not investigate what that constraint is.** The brief's conclusions do not depend on
    it, because they are about the long leg.
12. **Every table I transcribed is promoted to
    [`data/a3_leg_decomposition_tables.md`](../../../data/a3_leg_decomposition_tables.md)** with its
    source URL, byte count, PDF version, and the specific check that validated it — so any number in
    this brief can be re-checked without re-fetching, and the two tables I **refused** to transcribe
    (`A4` Table 3 and `A1` Table 1's market-cap row) are named there as refusals. **Raw PDFs are not
    promoted:** they are third-party copyrighted articles and, per the contract, raw caches stay in
    session temp.
13. **Nothing here was backtested, no null was drawn, no cell was scored, and no candidate exists.**
    §9's arithmetic is arithmetic on other people's published means — **it has no standard error, no
    null and no cost model**, and it should not be quoted as a result.
