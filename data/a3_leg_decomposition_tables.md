# `a3_` — DERIVED EVIDENCE: the anomaly leg decompositions quoted by `R1-03`

**Lane `A3` of `Scan-100926` round 1.** Quoted by
[`docs/research/Scan-100926/R1-03-the-long-only-problem.md`](../docs/research/Scan-100926/R1-03-the-long-only-problem.md).
Promoted to `data/` because **a file a record quotes is evidence.**

**These are transcriptions of published tables, extracted locally from PDFs I downloaded and verified
as PDFs by `file`, then read with `pdftotext -layout -enc UTF-8`.** They are **not** measurements of
this programme's fixture and **not** my own computations, except §4 which is labelled as such.

**Extraction hazard recorded:** `pypdf`'s `extract_text()` **dropped the minus signs in body prose and
scrambled table row order** on the Muravyev PDF. `pdftotext -layout` recovered both correctly. Every
table below is the `-layout` extraction, and each is noted with the check that validated it.

---

## 1. Muravyev, Pearson & Pollet — *Anomaloies and Their Short Sale Costs*, draft 1 Sep 2022

**Source PDF:** `https://www.hec.ca/finance/Fichier/Pearson2022.pdf` — HTTP 200,
`application/pdf`, **770,525 bytes**, PDF 1.6, 51 pages. Published as **JF 80(6) 2025, 3639–3694**;
**the published abstract differs from this draft** — see §3.

**Universe:** CRSP common stocks matched to a Markit indicative borrow fee, **July 2006 – December
2020**, **lagged price `< $1` dropped**, **lagged market cap `< $50`mn dropped**, **562,632
stock-months**, **162 anomalies** (from Chen & Zimmermann's 202 "clear anomalies"), **equal-weighted**
decile portfolios, held from close of `t+1` to close of `t+22`.

**Abnormal return definition:** DGTW characteristic matching (size, book-to-market, prior 6-month
return) **with high-fee stocks excluded from the benchmark portfolios**. This is why every decile mean
in Table 2 is negative and is stated as such by the authors; **read the decile-vs-decile comparison,
not the level.**

### Table 2 — DGTW-abnormal %/month, all stocks, NO fee adjustment

| row | 1 (low) | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 (high) | 10−1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Average return | −0.24% | −0.10% | −0.07% | −0.07% | −0.05% | −0.05% | −0.05% | −0.06% | −0.03% | **−0.09%** | **0.15%** |
| *t* (panel adj.) | [−2.94] | [−2.44] | [−2.31] | [−2.82] | [−1.98] | [−1.94] | [−1.67] | [−1.95] | [−1.16] | **[−1.81]** | **[2.93]** |
| *t* (naive) | −13.90 | −9.25 | −7.12 | −7.79 | −4.06 | −5.96 | −5.25 | −6.22 | −2.83 | −6.62 | |
| Percentage high fee | 21.91% | 13.73% | 10.93% | 10.04% | 9.96% | 9.39% | 9.50% | 10.20% | 12.03% | **18.33%** | |
| Average fee (annual) | 2.70% | 1.58% | 1.25% | 1.16% | 1.12% | 1.08% | 1.09% | 1.14% | 1.31% | **2.03%** | |
| Average # of stocks | 243 | 239 | 244 | 247 | 250 | 240 | 237 | 238 | 239 | 236 | |

**Validated against the paper's prose**, which states the decile-1 mean (−0.24%, panel *t* 2.94,
naive 13.90), the decile-5 mean (−0.05%), the 10−1 mean (0.15%, panel *t* 2.93), the decile-1 high-fee
share (21.32% in prose vs 21.91% in the table — **prose and table disagree by 0.59 points and I
record the discrepancy rather than resolve it**), the decile-1 fee (2.70%), and the decile-2 and
decile-10 high-fee shares (13.56%/17.64% in prose vs 13.73%/18.33% in the table — **same ~0.2–0.7
point disagreement**). **The prose's and the table's high-fee shares are not identical; every other
prose figure matches the table exactly.**

### Table 3 — DGTW-abnormal %/month, EXCLUDING stocks with borrow fee `> 1%`/yr

| row | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 10−1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Average return | 0.00% | 0.01% | 0.01% | 0.00% | 0.02% | 0.00% | 0.01% | 0.00% | 0.03% | **0.04%** | **0.04%** |
| *t* (panel adj.) | [0.04] | [0.22] | [0.46] | [0.01] | [0.36] | [0.02] | [0.26] | [0.04] | [0.85] | **[0.97]** | **[0.81]** |
| Average # of stocks | 190 | 207 | 217 | 222 | 225 | 217 | 215 | 214 | 210 | 193 | |

### Table 4 — DGTW-abnormal %/month, AFTER adding the borrow fee to each stock's return

| row | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 10−1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Average return | −0.01% | 0.03% | −0.03% | −0.04% | −0.02% | −0.03% | −0.02% | −0.03% | 0.00% | **−0.03%** | **−0.02%** |
| *t* (panel adj.) | [−0.10] | [0.72] | [−1.09] | [−1.66] | [−0.94] | [−1.04] | [−0.78] | [−0.98] | [−0.12] | **[−0.65]** | **[−0.49]** |

### Table 5 — RAW equal-weighted %/month (no risk adjustment, so no benchmark contamination)

| panel | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 10−1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **A: all stocks** | 0.80% | 0.92% | 0.97% | 0.95% | 0.99% | 0.98% | 0.98% | 0.98% | **1.00%** | **0.96%** | **0.16%** |
| *t* (panel adj.) | [1.43] | [1.77] | [1.92] | [1.94] | [2.01] | [2.02] | [2.04] | [2.00] | [1.98] | [1.82] | **[2.91]** |
| **B: excl. high fee** | 1.04% | 1.03% | 1.05% | 1.03% | 1.06% | 1.04% | 1.04% | 1.04% | 1.06% | **1.09%** | **0.05%** |
| *t* (panel adj.) | [1.90] | [2.02] | [2.11] | [2.11] | [2.16] | [2.15] | [2.17] | [2.13] | [2.13] | [2.10] | **[0.98]** |
| **C: net of borrow fee** | 1.03% | 1.05% | 1.01% | 0.98% | 1.02% | 1.01% | 1.01% | 1.00% | 1.03% | **1.02%** | **−0.01%** |
| *t* (panel adj.) | [1.81] | [2.02] | [1.98] | [2.00] | [2.06] | [2.06] | [2.08] | [2.04] | [2.03] | [1.91] | **[−0.04]** |

**Panel A's 10−1 of 0.16% is cross-checked in the paper's prose against Table 2's 0.15% abnormal
figure; the paper discusses the difference explicitly.**

### Table 7 — RAW %/month for the four anomalies commonly used as factors

| | Momentum D1 | D10 | 10−1 | Profitability D1 | D10 | 10−1 | Book-to-Market D1 | D10 | 10−1 | Investment D1 | D10 | 10−1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **A: all stocks** | 0.78% | 0.99% | **0.21%** | 0.54% | 1.16% | **0.62%** | 0.99% | 0.97% | **−0.02%** | 0.51% | 0.98% | **0.47%** |
| *t* | [1.00] | [1.83] | **[0.46]** | [0.83] | [2.24] | **[1.79]** | [1.94] | [1.26] | **[−0.04]** | [0.79] | [1.70] | **[2.21]** |
| % high fee | 30.83% | 21.46% | | 44.83% | 13.46% | | 21.81% | 18.22% | | 19.10% | 15.57% | |
| avg fee/yr | 3.92% | 2.83% | | 5.53% | 1.38% | | 3.12% | 2.08% | | 2.63% | 2.07% | |
| **B: excl. high fee** | 1.15% | 1.17% | **0.02%** | 1.15% | 1.25% | **0.10%** | 1.38% | 1.16% | **−0.22%** | 0.78% | 1.05% | **0.27%** |
| *t* | [1.49] | [2.25] | **[0.04]** | [1.79] | [2.48] | **[0.26]** | [2.85] | [1.52] | **[−0.47]** | [1.25] | [1.87] | **[1.29]** |
| **C: net of fee** | 1.11% | 1.10% | **−0.01%** | 1.01% | 1.20% | **0.19%** | 1.25% | 1.02% | **−0.23%** | 0.73% | 1.03% | **0.30%** |

**Note the Profitability decile-1 high-fee share: 44.83% at a 5.53%/yr fee.** Its raw return goes
from 0.54% to 1.15% when high-fee names are dropped — **the entire profitability spread in this
sample is the unprofitable-and-hard-to-borrow cohort.** **Investment is the one factor retaining a
non-trivial spread after the exclusion (+0.27%, `t` = 1.29, insignificant).**

### Table 8 — RAW %/month for two risk-based sorts

| | CAPM Beta D1 (low) | D10 (high) | 10−1 | Tail Risk Beta D1 | D10 | 10−1 |
|---|---|---|---|---|---|---|
| **A: all stocks** | 0.55% [1.77] | 1.04% [1.29] | **0.49% [0.87]** | 0.71% [2.29] | 1.19% [1.74] | **0.48% [1.09]** |
| **B: excl. high fee** | 0.69% [2.31] | 1.30% [1.61] | **0.60% [1.04]** | 0.82% [2.71] | 1.29% [1.90] | **0.48% [1.05]** |
| **C: net of fee** | 0.71% [2.31] | 1.16% [1.44] | **0.45% [0.79]** | 0.85% [2.74] | 1.27% [1.86] | **0.42% [0.95]** |

**In this 2006–2020 sample HIGH beta earned MORE raw return than low beta (1.04% vs 0.55%).**

### Table 9 — DGTW-abnormal %/month by signal category

| category | D1 (short) | D10 (long) | 10−1 | D1 high-fee | D10 high-fee |
|---|---|---|---|---|---|
| **Accounting (82)** A: all | −0.20% [−2.63] | **−0.05% [−0.75]** | 0.16% [3.06] | 21.82% | 17.20% |
| **Price (45)** A: all | −0.25% [−2.76] | **−0.12% [−1.80]** | 0.15% [1.87] | 24.11% | 18.07% |
| **Other (35)** A: all | −0.29% [−3.00] | **−0.17% [−2.98]** | 0.12% [1.04] | 18.77% | 21.51% |
| Accounting B: excl. high fee | 0.03% [0.46] | 0.08% [1.58] | 0.05% [0.99] | | |
| Price B: excl. high fee | 0.00% [−0.01] | 0.01% [0.35] | 0.02% [0.32] | | |
| Other B: excl. high fee | −0.06% [−0.74] | −0.04% [−0.79] | 0.02% [0.15] | | |
| Accounting C: net of fee | 0.01% [0.19] | 0.01% [0.22] | 0.00% [−0.01] | | |
| Price C: net of fee | −0.01% [−0.07] | −0.05% [−0.78] | −0.04% [−0.48] | | |
| Other C: net of fee | −0.07% [−0.69] | −0.12% [−2.36] | −0.06% [−0.58] | | |

### Table 10 — DGTW-abnormal %/month by anomaly subset

| subset | D1 | D10 | 10−1 |
|---|---|---|---|
| **Sample end `< 2006`** A: all | −0.23% [−2.71] | −0.11% [−2.15] | 0.12% [2.15] |
| **original `t > 5`** A: all | −0.28% [−3.33] | −0.10% [−1.56] | 0.19% [2.99] |
| **published in JF/JFE/RFS** A: all | −0.26% [−3.01] | −0.09% [−1.59] | 0.18% [2.89] |
| Sample end `< 2006` B: excl. high fee | 0.01% [0.17] | 0.02% [0.55] | 0.01% [0.22] |
| original `t > 5` B: excl. high fee | −0.02% [−0.22] | 0.05% [1.00] | 0.07% [1.18] |
| JF/JFE/RFS B: excl. high fee | −0.01% [−0.22] | 0.04% [1.18] | 0.06% [1.17] |

### NOT transcribed, and why

**Table 1's market-capitalisation percentile row extracted MISALIGNED.** The value `9.32` printed in
that row belongs to **utilisation's median** per the paper's own prose (*"The mean of utilization is
21.50% compared to a median of 9.32%"*). **No market-cap distribution from this paper is quoted
anywhere, by the record or here.** Prose-confirmed Table 1 figures only: mean borrow fee **1.67%/yr**;
fee percentiles **0.25% (1st), 0.38% (50th), 3% (90th), 30% (99th)**; **high-fee defined as fee
`> 1%`/yr, ≈ 12% of observations**; utilisation mean **21.50%**, median **9.32%**, 90th **50.71%**,
99th **90.09%**.

**Table 6** (five specific anomalies: IPO, share issuance, idiosyncratic risk, skewness, turnover
volatility) extracted with its column headers interleaved; the numbers are legible but the
decile-1/10−1 pairing could not be validated by an identity, so the record quotes only the paper's
prose about it.

---

## 2. Li, Sullivan & Garcia-Feijóo — *The Limits to Arbitrage and the Low-Volatility Anomaly*, FAJ 70(1) 2014

**Source PDF:** `https://images.aqr.com/-/media/AQR/Documents/Insights/Journal-Article/The-Limits-to-Arbitrage-and-the-Low-Volatility-Anomaly.pdf`
— HTTP 200, `application/pdf`, **254,416 bytes**, PDF 1.6. **An AQR-hosted reprint of a CFA Institute
peer-reviewed article — the host is an interested party, the article is not theirs.**

**Sample:** July 1963 – December 2010, US. Alphas are **Fama–French-adjusted**, one-month holding,
**value-weighted unless stated**.

### Tables 5 and 6 — alpha AND AVERAGE SHARE PRICE by IVOL quintile

**This is the only table in either lane's reading that reports the NOMINAL SHARE PRICE of an
anomaly's legs.**

| IVOL rank | **Table 5: all stocks** alpha | avg price | avg NonZEROR | avg Amihud | avg DVOL `$`mn | **Table 6: excl. `P < $5`** alpha | avg price | avg NonZEROR | avg Amihud | avg DVOL `$`mn |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 (lowest IVOL) | **+0.08% [1.87]** | **`$55.6`** | 78.0% | 0.37 | 256.7 | **+0.12% [2.64]** | **`$61.5`** | 80.0% | 0.33 | 272.1 |
| 2 | +0.07% [1.13] | `$29.2` | 82.7% | 0.75 | 178.9 | +0.07% [1.26] | `$35.6` | 84.2% | 0.57 | 214.0 |
| 3 | +0.09% [1.09] | `$19.2` | 82.2% | 1.60 | 121.4 | +0.07% [1.06] | `$24.5` | 84.5% | 0.88 | 165.3 |
| 4 | −0.30% [−2.35] | `$13.5` | 80.7% | 3.99 | 79.8 | +0.03% [0.27] | `$19.5` | 84.8% | 1.30 | 135.2 |
| 5 (highest IVOL) | **−1.11% [−5.90]** | **`$7.03`** | 77.3% | 27.36 | 40.0 | **−0.26% [−1.82]** | **`$14.3`** | 85.4% | 2.58 | 111.1 |
| **1 − 5** | **+1.19% [6.04]** | | | | | **+0.38% [2.47]** | | | | |

**Validated against the paper's prose**, which states the `$7.03` highest-volatility average price
verbatim, the 1.19% → 0.38% decline on excluding penny stocks verbatim, and the 1.19% zero-cost alpha
in three separate places.

### Table 4 — zero-cost quintile alpha %/month, equal- versus value-weighted

| risk measure | period | **Equal Weighted** | **Value Weighted** |
|---|---|---|---|
| **IVOL** | 1963–2010 | **+0.40% [1.88]** | +1.19% [6.04] |
| | 1963–1990 | +0.76% [4.24] | +1.44% [9.39] |
| | **1991–2010** | **+0.05% [0.11]** | +1.02% [2.56] |
| | **1991–2007** | **−0.15% [−0.29]** | +0.79% [1.68] |
| **IVOL36** | 1963–2010 | +0.38% [1.82] | +0.82% [4.56] |
| | 1963–1990 | +0.57% [2.89] | +1.04% [6.07] |
| | 1991–2010 | +0.30% [0.80] | +0.70% [2.34] |
| | 1991–2007 | +0.25% [0.61] | +0.62% [1.81] |

**The BETA block of Table 4 extracted with its `t`-statistics interleaved and could not be validated
by an identity, so it is not transcribed.** Prose-confirmed for BETA: the strategy is *"not profitable
at all, on average, when using BETA as the measure of risk."*

### Further prose-confirmed figures

- **1991–2010, non-penny universe (unreported in their tables):** zero-cost alpha **0.24%/month,
  `t` = 0.80.**
- **Highest-liquidity tercile (DVOL):** the value-weighted quintile spread falls to **+0.45%/month**,
  *"decline by about 60% — that is, alpha declines from 1.19% a month to 0.45% a month."*
- **Liquidity-tercile-then-IVOL-quintile double sort:** *"no anomalous returns are found — and alpha
  is the same for both high-IVOL and low-IVOL stocks."*
- **Conclusion, verbatim:** *"the anomalous returns of value-weighted portfolios are largely
  eliminated when low-priced (less than `$5`) stocks are omitted — and are not at all present in
  equal-weighted portfolios."*

---

## 3. Muravyev et al. — the DRAFT versus the PUBLISHED abstract

**Published abstract read directly from RePEc's page bytes** —
`https://ideas.repec.org/a/bla/jfinan/v80y2025i6p3639-3694.html`, HTTP 200, `text/html`, 33,075 bytes,
text extracted locally. **Not a summariser.**

| | **draft, 1 Sep 2022** | **published, JF 80(6) 2025** |
|---|---|---|
| long-short before short-sale costs | **0.15% / month** | **0.14% / month** |
| after borrow-fee adjustment | **0.02% / month** | **−0.01% / month** |
| high-fee share description | *"12% of all stocks"* | *"12% of stock dates"* |
| *"the returns are due to the short leg"* | implied in body | **stated in the abstract** |

**The sign flipped between draft and publication. The published version is the more negative and it
governs.** Every decile figure in §1 above is from the **draft**, and the published tables may also
have moved.

---

## 4. Chen & Welch — *What Useful Alphas?*, arXiv 2607.06502v1

**Source PDF:** `https://arxiv.org/pdf/2607.06502` — HTTP 200, `application/pdf`, **427,439 bytes**,
PDF 1.7, 24 pages. **Abstract page confirms a single version, v1, submitted 7 Jul 2026.**
**Negative control run:** `https://arxiv.org/abs/2607.99999` → **HTTP 404, *"There is no record of an
article with identifier '2607.99999'"***, so the endpoint distinguishes real from fabricated IDs.

### Table 2 last two rows — the cross-section of ~170 anomalies, post-2005, Standard (N3000, 90%)

| | Long − Short | **Long − Mkt** | Adjusted LS | **Adjusted Long − Mkt** |
|---|---|---|---|---|
| **Mean, all 170 anomalies** | **0.08%** | **−0.04%** | 0.01% | **0.00%** |
| **SD, all 170 anomalies** | 0.18% | **0.13%** | 0.02% | 0.00% |

**Mean `t`-statistic of long-minus-market: −0.31. Var(`t`) = 0.98, below the luck-only 1.00, so the
empirical-Bayes shrinkage factor is truncated at zero.** Shrinking toward the cross-sectional mean
instead of zero gives **−4 bp/month for every long leg** — stated in the paper's prose.

### Table 2 top ten — validated by the "Original Paper" column matching each signal's known source

| rank | signal | original paper | LS %/mo | **Long − Mkt %/mo** |
|---|---|---|---|---|
| 1 | Cash-based operating profitability | Ball et al. (2016) | 0.66 | **+0.40** |
| 2 | Operating profitability (R&D adj) | Ball et al. (2016) | 0.60 | +0.26 |
| 3 | Realized-implied volatility spread | Bali & Hovakimian (2009) | 0.59 | +0.35 |
| 4 | Off-season momentum | Heston & Sadka (2008) | 0.54 | +0.13 |
| 5 | Net external financing | Bradshaw, Richardson & Sloan (2006) | 0.48 | +0.15 |
| 6 | Seasonal momentum (16yr+) | Heston & Sadka (2008) | 0.48 | +0.21 |
| 7 | Gross profitability | Novy-Marx (2013) | 0.44 | +0.14 |
| 8 | R&D over market cap | Chan, Lakonishok & Sougiannis (2001) | 0.41 | +0.33 |
| 9 | Net equity financing | Bradshaw, Richardson & Sloan (2006) | 0.39 | +0.16 |
| 10 | Operating leverage | Novy-Marx (2011) | 0.38 | **−0.01** |

### Table 3 — by category, post-2005, Standard universe

**Row assignment validated by an internal consistency check: the median's sign must agree with the
share positive, and it does on all eight rows.** Intangibles (median 0.00 ↔ 50% positive) is the
tightest.

| category | N | mean %/mo | median %/mo | 25th | 75th | % positive |
|---|---|---|---|---|---|---|
| Momentum | 17 | +0.01 | +0.05 | −0.16 | 0.09 | 53 |
| **Profitability** | 9 | **+0.25** | **+0.24** | 0.09 | 0.44 | **78** |
| **Value / Fundamentals** | 15 | **−0.02** | **−0.04** | −0.11 | 0.10 | **47** |
| Investment / Growth | 36 | +0.09 | +0.06 | −0.02 | 0.18 | 69 |
| Trading / Liquidity | 13 | +0.09 | +0.11 | 0.03 | 0.13 | 85 |
| Accruals / Accounting | 18 | +0.09 | +0.06 | −0.02 | 0.19 | 72 |
| Intangibles | 12 | +0.04 | **0.00** | −0.02 | 0.07 | **50** |
| Other | 50 | +0.10 | +0.11 | −0.03 | 0.18 | 72 |
| **All** | **170** | **+0.08** | **+0.07** | −0.04 | 0.18 | **67** |

### Table 1 — median long-short %/month post-2005 by universe filter (prose-confirmed)

| filter | median LS |
|---|---|
| all stocks (original) | **19 bp** |
| Rank Only (N3000) | **12 bp** |
| **Standard (N3000 ∩ 90%)** | **7 bp** |
| **Tight (N1000 ∩ 80%)** | **7 bp** |

**Prose-confirmed for the Standard filter:** interquartile range **−4 to +18 bp/month**, median
`t` **0.45**, median annualised Sharpe **0.11**, median CAPM alpha **9 bp/month**, median alpha
`t` **0.64**, **67% of anomalies positive** (80% in the all-stock universe, 68% in Tight).

---

## 5. Stambaugh, Yu & Yuan — *Arbitrage Asymmetry and the Idiosyncratic Volatility Puzzle*, NBER w18560

**Source PDF:** `https://www.nber.org/system/files/working_papers/w18560/w18560.pdf` — HTTP 200,
`application/pdf`, **181,567 bytes**. Published **JF 70(5) 2015**; **the bytes read are the working
paper.**

**Sample:** 1965m8 – 2011m1. **Mispricing measure:** the average of each stock's rankings on **11
anomalies** that survive a Fama–French three-factor adjustment. Returns are **benchmark-adjusted** as
the intercept `a` in `Rᵢ,ₜ = a + b·MKTₜ + c·SMBₜ + d·HMLₜ + εᵢ,ₜ`; `t`-statistics use White (1980)
standard errors. **Dependent sort: mispricing quintile first, then IVOL quintile within it.**

### Table 2 — %/month

| mispricing quintile | Highest IVOL | Next 20% | Next 20% | Next 20% | Lowest IVOL | **Highest − Lowest** | **All stocks** |
|---|---|---|---|---|---|---|---|
| **Most overpriced (top 20%)** | −2.19 [−11.23] | −1.27 [−8.29] | −0.88 [−6.26] | −0.81 [−5.40] | −0.42 [−3.60] | **−1.77 [−7.87]** | **−0.83 [−8.07]** |
| Next 20% | −0.91 [−5.82] | −0.44 [−3.18] | −0.24 [−2.32] | −0.22 [−2.28] | −0.10 [−0.98] | −0.81 [−4.17] | −0.24 [−3.83] |
| Middle 20% | −0.11 [−0.72] | 0.05 [0.42] | 0.05 [0.52] | −0.22 [−2.29] | 0.07 [0.79] | −0.18 [−0.97] | −0.06 [−1.30] |
| Next 20% | −0.09 [−0.54] | 0.07 [0.67] | 0.29 [3.19] | 0.22 [2.73] | 0.15 [1.91] | −0.25 [−1.19] | 0.18 [4.32] |
| **Most underpriced (bottom 20%)** | 0.63 [4.30] | 0.66 [5.55] | 0.38 [3.88] | 0.29 [3.50] | 0.12 [1.55] | **0.52 [2.93]** | **0.28 [5.51]** |
| **Most over − most under** | −2.82 [−11.66] | −1.93 [−9.48] | −1.27 [−6.69] | −1.10 [−5.98] | −0.54 [−3.56] | −2.28 [−8.48] | **−1.10 [−7.97]** |
| **All stocks** | −1.23 [−7.44] | −0.40 [−3.90] | 0.03 [0.54] | 0.03 [0.64] | **0.07 [1.72]** | **−1.30 [−6.92]** | |

**Validated against four figures the paper states in prose: −1.77 (`t` −7.87), +0.52 (`t` 2.93),
−0.18 (`t` −0.97) and −1.30 (`t` −6.92). All match.** The paper also states the asymmetry ratio:
the overpriced high-minus-low effect is **3.4×** the underpriced one.

**The two cells the record leans on:** the **most-underpriced quintile's own alpha is +0.28%/month
(`t` = 5.51)** — a long-only number — and among **all** stocks the **lowest-IVOL quintile's alpha is
+0.07%/month (`t` = 1.72)**, which is the price-only long-only end and is insignificant.

---

## 6. Israel & Moskowitz — *The role of shorting, firm size, and time on market anomalies*, JFE 108(2) 2013

**Source PDF:** `https://gritcap.com/enoalroa/2020/10/Israel-and-Moskowitz-The-role-of-shorting-firm-size-and-time-on-market-anomalies-2012.pdf`
— HTTP 200, `application/pdf`, **2,539,837 bytes**, PDF 1.7, 18 pages. **The published JFE typeset
version** (journal header, volume, page range and DOI block all present). **Israel is AQR; Moskowitz
is an AQR principal.**

**Sample:** July 1926 (January 1927 for momentum) – December 2011. Fama–French 2×3 portfolios.
**Alphas are CAPM alphas, annualised %, betas re-estimated within each subperiod. NO TRADING COSTS ARE
CHARGED ANYWHERE IN THE PAPER**, by the authors' own statement.

### Table 1 — CAPM alphas (`t`-statistics in parentheses)

**Reconstructed from a garbled layout extraction and validated by the identity `long − short =
spread` holding in THREE separate period columns** (see the check block below).

| | 1926–2011 | 1926–1962 | 1963–2011 | 1926–1949 | 1950–1969 | 1970–1989 | **1990–2011** |
|---|---|---|---|---|---|---|---|
| **Small** (size long leg) | **2.05 (1.72)** | 0.70 (0.33) | 3.08 (2.30) | 3.12 (1.01) | 1.72 (1.03) | 2.62 (1.29) | **2.27 (1.07)** |
| Big (size short leg) | 0.65 (1.40) | −0.01 (−0.01) | 1.19 (2.49) | 0.26 (0.25) | 0.77 (1.66) | 1.72 (3.41) | 0.90 (0.96) |
| SMB | 1.42 (1.16) | 0.71 (0.37) | 1.92 (1.29) | 2.86 (1.02) | 0.99 (0.59) | 0.90 (0.42) | 1.39 (0.56) |
| **High** (value long leg) | **2.93 (2.40)** | 0.73 (0.33) | 4.72 (4.21) | 2.71 (0.86) | 2.67 (1.72) | 5.91 (3.50) | **2.98 (1.66)** |
| Low (value short leg) | −0.58 (−0.87) | 0.05 (0.05) | −1.07 (−1.27) | 1.21 (0.80) | −0.40 (−0.41) | −2.23 (−1.82) | −1.04 (−0.75) |
| HML | 3.45 (2.80) | 0.68 (0.33) | 5.74 (4.14) | 1.50 (0.51) | 3.04 (1.82) | 8.10 (4.10) | 3.95 (1.67) |
| **Up** (momentum long leg) | **5.55 (6.74)** | 5.79 (4.34) | 5.45 (5.16) | 6.69 (3.36) | 5.43 (4.32) | 5.08 (3.55) | **4.68 (2.71)** |
| Down (momentum short leg) | −4.94 (−3.74) | −6.44 (−2.89) | −3.76 (−2.43) | −3.61 (−1.14) | −4.83 (−3.28) | −4.39 (−2.03) | −4.19 (−1.54) |
| UMD | 10.48 (6.13) | 12.23 (4.49) | 9.21 (4.35) | 10.29 (2.61) | 10.26 (5.21) | 9.47 (3.32) | 8.87 (2.38) |

**The validating identities.** `long − short` against the printed spread, in three columns:

| | 1926–2011 | 1963–2011 | 1990–2011 |
|---|---|---|---|
| SMB: Small − Big | 2.05 − 0.65 = **1.40** vs printed **1.42** | 3.08 − 1.19 = **1.89** vs **1.92** | 2.27 − 0.90 = **1.37** vs **1.39** |
| HML: High − Low | 2.93 + 0.58 = **3.51** vs **3.45** | 4.72 + 1.07 = **5.79** vs **5.74** | 2.98 + 1.04 = **4.02** vs **3.95** |
| UMD: Up − Down | 5.55 + 4.94 = **10.49** vs **10.48** | 5.45 + 3.76 = **9.21** vs **9.21** | 4.68 + 4.19 = **8.87** vs **8.87** |

**Nine identities, all within rounding and within the paper's stated re-estimation of betas per
subperiod. The reconstruction is sound.**

### Table 3 — NOT transcribed

**Table 3 (long/short contribution across size quintiles) extracted with its row labels and numeric
rows irrecoverably interleaved; the spread-minus-leg identity does NOT hold on any candidate
assignment I tried, so I transcribe none of it.** The record quotes only the paper's prose about it:

- value 5−1 raw spread **11.22%/yr in the smallest quintile, 3.70% in the largest**;
- *"Among the smallest stocks, the long side of value contributes only **47%** to total profits, but
  among the largest stocks the contribution of long positions is nearly **90%**"*;
- *"The long side contributes **71%** of profits among small cap momentum and only **38%** among large
  cap momentum"*;
- *"Long-only momentum is strongest among the smallest stocks and weakest among the largest stocks,
  though it is statistically and economically significant in each"*;
- *"strong positive alphas for long-only value among small cap stocks and insignificant alphas among
  large caps"*, with the difference **4.31%/yr (`t` = 1.97)** between smallest and largest quintiles.

### Prose-confirmed statements the record leans on

- **Long-only portfolio figures, 1926–2011, in excess of T-bills:** momentum **13.6%/yr, 21.8% SD,
  Sharpe 0.62, beta 1.08**; value **12.4%, 26.5%, 0.47, beta 1.27**; size **11.5%, 26.3%, 0.44,
  beta 1.26**. Information ratios **0.73 / 0.26 / 0.19**.
- **No trading costs:** *"Without having to specify a trading cost model, which is investor specific,
  we acknowledge that small stocks are more costly and more difficult to trade and that shorting is
  more costly and more constrained."*
- **Their own test cannot reject an equal split:** *"However, across all size groups, we cannot reject
  that the abnormal profits to value and momentum trading are generated equally by long and short
  positions."*
- **Value is a microcap effect:** *"The value premium… is largely concentrated only among small stocks
  and is insignificant among the largest two quintiles of stocks (largest 40% of NYSE stocks)."*
- **Size quintile average market caps:** quintile 1 **`$156`mn**, quintile 2 **`$855`mn**, and
  *"Stocks in Quintiles 1 and 2 could face significant trading costs for any reasonably sized
  portfolio."*
- **The `>100%` long-side figures are not market-adjusted, and they say so:** *"More than 100% of
  these return differences come from the long side… However, adjusting for market exposure and market
  returns changes the picture somewhat."*

---

## 7. Benaych-Georges, Bouchaud & Ciliberti — *Equity Factors: To Short Or Not To Short*, arXiv 2003.10419v3

**Source PDF:** `https://arxiv.org/pdf/2003.10419` — HTTP 200, `application/pdf`, **493,507 bytes**,
PDF 1.5, 4 pages (dense two-column). **Capital Fund Management — a long-short shop, so its positive
hedged-long-only number runs AGAINST its own interest.**

**Setup:** five ranked predictors (Low Volatility, Momentum, Returns Over Assets, Small Minus Big,
Value Earnings), **global** pool (USA-Canada, Europe, Asia, Australia) weighted by available
liquidity, **2000–2020**, signals smoothed with a 150-day EMA, **`$1`bn AUM**, max 3% per name,
costs = linear spread + broker fees + square-root market impact from in-house estimates, plus
financing and in-house hard-to-borrow fees. **LH** = long-only optimisation hedged against a tradeable
index (S&P 500, EURO STOXX 50, TOPIX, ASX 200, TSX 60). **LS** = same signals, same cost control,
volatility-matched to LH.

### Table 1 — all figures % per year of `$1`bn AUM, both at 6.4% realised volatility

| | **Sharpe** | **mean drawdown** | returns + div. | trading cost | financing cost | short borrow cost |
|---|---|---|---|---|---|---|
| **LH (hedged long-only)** | **0.56** | **−8.2%** | 8.4% | −2.8% | −2.0% | n/a |
| **LS (long-short)** | **0.98** | **−3.9%** | 14.2% | −4.8% | −2.6% | −0.6% |

**Turnover:** LH ≈ **0.5% of AUM per day**; LS ≈ **2% of gross market value per day**.

### The two prose findings the record leans on

- **The reproduction, and its limit:** they reproduce Blitz et al.'s leg-correlation result but the
  max-Sharpe allocation puts **30% on the short legs, not 0%** — *"At the very least, this means that
  the 'no-short' recommendation is not robust against such minor changes."*
- **The mechanism of the disagreement:** the Fama–French 2×3 portfolios are **50% small caps and 50%
  large caps**, so `(longs − market) − (market − shorts)` reduces to `(longs + shorts) − 2·market`,
  which is correlated with SMB. Hedging with the SPmini makes the long legs look better — *"However,
  this is because the difference between the two legs is now mechanically exposed to the SMB factor."*
- **Per-factor Sharpes and correlations exist only in plotted figures (Figs. 4, 6, 7, 8) and are NOT
  transcribed.** Table 1 and the prose agree on the 0.56/0.98 headline.

---

## 8. What is NOT in this file

- **No figure here is measured on this programme's fixture.** Nothing was backtested, no null was
  drawn, no cell was scored.
- **`A7` (Blitz, Baltussen & van Vliet 2020) has no section here, because I could not obtain it.**
  Three refusals logged in the record's §10. Its leg alphas appear in the record restated from `K6`'s
  prior reading and are **not** re-established.
- **Raw PDFs are NOT promoted.** They are third-party copyrighted articles and, per the contract, raw
  caches stay in session temp. Every one is re-fetchable from the URL, byte count and PDF version
  recorded above.
- **The record's §9 arithmetic is not in this file.** It is computed from §1's Table 5 alone and is
  re-runnable from it: the mean of the ten decile returns against the mean of deciles 2–10.
