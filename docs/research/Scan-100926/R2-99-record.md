# Scan-100926 · Round 2 — record

**Slate:** [`R2-00-slate.md`](R2-00-slate.md) · **campaign contract:**
[`00-SCHEMA.md`](00-SCHEMA.md) · **round 1:** [`R1-99-record.md`](R1-99-record.md) ·
**previous campaign:** [`../README.md`](../README.md).

**STATUS: COMPLETE — all four lanes in.** This record was opened when three had landed and
**extended in place** when `B4` arrived, so the order things were learned in stays visible. Round 1's
record was built the same way. **`B4` is the lane that closes round 1's `D9`, and it closes it on both
horns** (§2, `B4`).

**Under [R15](../../RULES.md#r15) nothing here closes or admits anything.** Nothing in this folder is
elevated out of `docs/research/`. **Conflicts below are recorded, not adjudicated** — including the
two where a lane reached a verdict and said so, and the one where two lanes read the same paper and
disagree about what it says.

---

## 0. THE SHAPE OF THE ROUND

**The round was commissioned to pursue four threads round 1 opened. All four reported, and all four
came back with the same structural answer in different subject matter: THE CONSTRUCTION DETAIL
NOBODY'S NAME CARRIES IS THE THING THAT DECIDES THE ANSWER.**

- `B1`: the whole `A2`-vs-`A3` disagreement is **one identity**, and the term that separates them is
  measurable — *and its sign flipped in the era this programme trades.*
- `B2`: the profitability family splits in two on **whether the deflator is current or lagged
  assets**, a line no paper's title or abstract carries.
- `B3`: the session split of a characteristic premium is **published, twice, and points the other
  way from the lane's hypothesis** — and the distinction is **descriptive rather than actionable**,
  priced at `~38×`.
- `B4`: net share issuance is split-immune **if the ratio is formed inside one filing**, because
  restatement puts both periods on the same share basis — *so the split gap everyone was arguing
  about never had to be closed.*

**And the round's sharpest single line is `B4`'s.** `A2` and `A1` spent round 1 each right about a
different half of `D9`. **`B4` reports that the half they were arguing about was the wrong half.**

**And one thing round 1 could not do has been done.** `A3`'s number-one self-flagged unverified item
was that it was **refused the full text** of Blitz, Baltussen & van Vliet (2020) — *"the single most
important counter-evidence"* ([`R1-03`](R1-03-the-long-only-problem.md) line 70). **`B1` obtained the
Erasmus open-access copy and read it in full.** That is a genuine advance rather than a re-reading,
and what it found is in §1.

---

## 1. THE CENTRAL CONFLICT OF ROUND 1 — WHAT `B1` DID TO IT

**Round 1's central conflict** (`R1-99` §1): `A3` reported the long leg failing **gross**
(−0.04%/month vs the value-weighted market, Var(t) = 0.98, below the luck null); `A2` reported it
**unresolved rather than zero** (Var(t) = 1.35–1.81, signal share 0.26–0.45, against each sort's own
name-weighted universe). **`B1` was sent at the benchmark beneath both verdicts.**

### 1.1 The disagreement is one identity, and `B1` measured its middle term

```
(leg − VW market)  =  (leg − EW universe)  +  (EW universe − VW market)
```

**`B1`'s own measurement** `[MEASURED IN BRIEF]`, from Ken French's free ME-decile files, with a
**positive control** (cap-weighted deciles reproduce the CRSP VW market to **+0.0044 %/mo**, max
deviation 0.258) and a **negative control** (the non-positive market-equity bucket is empty and
flagged `−99.99` throughout). Evidence: [`data/B1_ew_vs_vw_benchmark.py`](../../../data/B1_ew_vs_vw_benchmark.py),
[`.txt`](../../../data/B1_ew_vs_vw_benchmark.txt).

| `EW universe − VW market` | 2010-01→2026-07 | post-2005 | 1963-07→2018-12 | full CRSP |
|---|---:|---:|---:|---:|
| all CRSP names | **−0.262%/mo** | −0.191 | **+0.240** (t 2.03) | +0.257 (t 2.64) |
| largest 1,573 | **−0.074** | −0.012 | **+0.167** (t 2.27) | +0.232 (t 2.89) |
| top 90% of cap | **−0.103** | −0.054 | **+0.097** (t 1.96) | +0.053 |
| ME deciles 6–10 | −0.101 | −0.048 | +0.103 (t 2.04) | +0.089 |

**THE SIGN FLIPPED IN THE ERA THIS PROGRAMME TRADES.** Every pre-2019 sample pays the
equal-weighted universe **more** than the cap-weighted market at `t ≈ 2`; every sample overlapping
this programme's window pays it **less**.

**Two further numbers from the same table that nobody commissioned and both matter.** `sd(gap)` —
the monthly volatility a mismatched benchmark **injects** into every leg series — is **1.2–2.8%/mo**.
And the name-weighted universe's **beta on the market is 1.05–1.20**, so a simple subtraction imposes
`β = 1` and **leaves a beta bet of (β − 1) inside the reported alpha**.

### 1.2 `B1`'s verdict: partial to each lane, on different statistics — recorded as `B1`'s

| | `B1`'s reading |
|---|---|
| **on the MEAN** | **`A3` survives.** The benchmark switch is worth only **+1 to +10 bp** in a screened universe. `B1` derived from Muravyev et al.'s own Table 5 that their long leg beats its own name-weighted universe by **+0.7 bp/month** (162 anomalies, 2006–2020) — landing on zero, **not** on `A2`'s +44 bp. |
| **on the STATISTIC** | **`B1` concludes `A2` wins outright.** The injected sd of 1.2–2.8%/mo predicts a long-minus-market **Var(t) of 0.76–1.19, where `A3` observed 0.98.** `B1`'s words: Var(t) = 0.98 *"is a benchmark artefact and should not be cited again as evidence of an absent signal."* |
| **on `B2`'s territory** | **undisturbed either way.** On cash-based operating profitability the two benchmarks agree to **4 bp** (+44 vs +40). |

**That middle row is a verdict, and it is recorded as `B1`'s verdict rather than adopted as this
record's.** `A3`'s reading of its own Var(t) stands on the record beside it.

### 1.3 The literature splits — and the split is predictable from who had to build a benchmark

**Papers that must CONSTRUCT a benchmark for a leg justify it at length, and land near `A2`'s
choice.** Blitz, Baltussen & van Vliet (2020) `[read in full — the copy A3 was refused]`, verbatim:

> *"A natural candidate for the neutral hedging portfolio would be the cap-weighted market portfolio.
> With that choice, however, all the results would be distorted by the size effect"*

— and they use a **50/50 Big/Small hedge** instead. DGTW justify characteristic matching explicitly;
Muravyev–Pearson–Pollet justify their variant **and test its sensitivity**.

**Papers that merely REACH for the market inherit it in silence.** Chen & Welch — the anchor for the
−0.04%/month — define it in **one table-note clause** (*"the raw Fama-French market return, computed
as Mkt − RF plus RF"*) and **never state the weighting of the legs**; the dataset's documented
default is equal-weighted. Hou–Xue–Zhang, Stambaugh–Yu–Yuan and Jensen–Kelly–Pedersen justify
**weighting**, never the **benchmark** — and the argument offered is an **aggregate-wealth** argument,
which `B1` notes has no purchase on a single absolute-return book.

### 1.4 Circularity lives in the characteristic-matched benchmark, not the universe benchmark

And **the DGTW authors say so in print**: the benchmark *"assigns no significant abnormal performance
to those investors who simply follow the same mechanical characteristic-based strategy… even if that
strategy did extremely well."* **The circularity risk named in the commissioning brief was aimed at
the wrong benchmark**, and `B1` says which one carries it.

**`DGTW` is also not constructible free for this window.** Wermers' files **end June 2012**
(breakpoints June 2010, last vintage Oct 2013) and the page's stated condition is a CRSP/Compustat
subscription. French publishes the breakpoints but **no size × BM × momentum triple sort**. A build
needs **per-name book equity** — `R1-01`'s XBRL problem, effectively unavailable before `2011q3`.

### 1.5 Absolute return is genuinely under-served, and `B1` says so plainly

**No paper asks what a cash-funded long-only single-name book should be measured against.** Sharpe
(1994), read from his own page, supplies the criterion: *"the differential return corresponds to the
payoff obtained from a unit investment in the fund, financed by a short position in the benchmark."*
**This book is financed by cash.**

**`B1`'s recommendation:** report the identity with **all three terms**; and for the programme's own
signal criterion, **subtract nothing** — a within-universe null **is** `A2`'s benchmark with a p50
and a p95 attached, **and this programme already builds it**.

---

## 2. What each lane returned

### `B2` — profitability, deep

**The family is not one candidate, and the splitter is a single line of construction nobody's name
carries: whether the deflator is CURRENT or LAGGED assets.** Under the lagged-asset deflator that
Ball et al.'s own appendix specifies, gross profitability falls to **t = 1.04–1.85** and operating
profitability to **t = 0.33–1.07**, in **two independent replications** (Hou–Xue–Zhang w23394;
Chen–Zimmermann's code). **It is an identity** — `GP/AT = (GP/AT₋₁) ÷ asset growth` — **so the
standard gross-profitability sort is partly an investment signal.**

**Cash-based operating profitability (`CbOP`) survives both conventions** (t = 3.02–3.44), both
weightings, big stocks alone, and post-2005. **It is the one survivor.** And **the reference
implementation records the ambiguity in a code comment** — `CBOperProf.py`: *"some confusion about
lagging assets or not / OP 2016 JFE seems to lag assets, but 2015 JFE does not / Yet no lag implies
results much closer to OP"* — and **ships the paper's own version as a placebo.**

**Long-only, read from the published source rather than inferred.** Ball et al.'s Table 4, CAPM alphas
per decile: `CbOP` long leg **+14 bp/mo (t = 1.95)**, short leg **−50 bp (t = −4.59)** — **77% of the
market-adjusted premium is in the short leg**, and the long leg **misses 1.96**. **Against FF3 the
same leg is +35 bp (t = 5.98).** *The benchmark moves the answer by 2.5× on the share and 3× on the
t* — **`B1`'s question arriving uninvited in `B2`'s lane.** Operating profitability's long leg is
**+7 bp (t = 0.95)**, a zero.

**Computability inverts the ranking** `[MEASURED IN BRIEF]` — SEC `frames` census, **two negative
controls, both behaved**: an invented tag returned `HTTP 404` in all eleven years **and is reported as
a 404 rather than coerced to zero**; a wrong-unit control returned 1–6 entities, proving the endpoint
unit-sensitive and alive. Evidence: [`data/B2_profitability_tag_census.json`](../../../data/B2_profitability_tag_census.json),
[`B2_profitability_tag_intersections.json`](../../../data/B2_profitability_tag_intersections.json),
scripts [`B2_tagcensus.py`](../../../data/B2_tagcensus.py), [`B2_intersect.py`](../../../data/B2_intersect.py).

| | filers | verdict |
|---|---|---|
| **`GrossProfit`** | **3,346 (2011) → 2,407 (2025)** | **STABLE. No FY2018 break.** |
| `SalesRevenueNet` | 2,085 (2015) → 1 (2019) | **DEAD** |
| `CostOfGoodsSold` | 1,296 (2017) → 2 (2019) | **DEAD** |
| `XSGA` equivalent | ~30% of filers, no single us-gaap tag | **weak** |
| `CbOP` strict intersection, six accrual terms | **171–273** | **unusable** |

**So gross profitability needs two tags and survives the collapse that killed its own components,
while `CbOP` needs twelve and deferred revenue dies exactly at FY2018.** Worse than a rename: `CbOP`
uses **Δ(DRC+DRLT)**, so that difference straddles **both** a tag change **and** an ASC 606
cumulative-effect restatement for ~1,700 industry-clustered filers. **The definition with the best
evidence is the one the data cannot deliver.**

**Also returned:** no paper in this family reports its legs' **nominal price distribution** —
confirmed by grep, zero hits in three of four sources. Gross profitability's spread **falls
monotonically in size** to 0.26 [t 1.88] in the largest quintile, large-cap Sharpe **0.27 against the
market's 0.34**. And **the quarterly variant is 2–4× stronger in three measurements and natively
point-in-time from XBRL** — the lane's largest unexploited fact, **flagged, not resolved.**

### `B3` — where the premium accrues within the day

**The lane's premise inverts. The bar is met by the first branch — named evidence — and the evidence
goes AGAINST the hypothesis.** The decomposition **has** been done for slow characteristics, **twice,
in the JFE**, and in both cases the slow premium is **intraday with a negative overnight component.**

**Lou, Polk & Skouras (2019, JFE 134:192–213)** `[PEER-REVIEWED] [read in full]`, LSE PDF, journal
header verified on page 1; 1993–2013, **value-weighted** extreme-decile long–shorts, monthly CAPM
alphas, **sub-$5 and the entire bottom NYSE size quintile excluded**:

| strategy | overnight | intraday |
|---|---:|---:|
| **`ROE` profitability** | **−0.95%** (−6.25) | **+1.42%** (5.58) |
| `BM` value | −0.10 (−0.67) | +0.48 (2.21) |
| `INV` asset growth | −0.28 (−2.10) | +0.97 (4.39) |
| `ACCRUALS` | −0.47 (−3.25) | +1.10 (4.73) |
| `ISSUE` equity issuance | −0.52 (−3.27) | +1.13 (6.13) |
| `IVOL` (low − high) | **−1.46** (−5.23) | **+2.48** (6.21) |
| `MOM` momentum | **+0.98** (3.84) | −0.02 (−0.06) |
| `CRSP` market excess | **+0.55** (3.62) | +0.38 (1.87) |

Their words: the nine non-past-return strategies *"earn their entire premia intraday"*; on issuance
and accruals, *"more than 100% of the premium occurs intraday."* **`ROE`'s intraday component is 302%
of its close-to-close total.**

**Bogousslavsky (2021, JFE 141:172–194)** corroborates independently on 1986–2015. Main text
**paywalled everywhere** `[abstract only]` — **but his Internet Appendix is posted on his own site and
`B3` read it in full.** Its Table IA.2 gives **the number a long-only book should read**: the **LONG
leg** of gross profitability earns **+0.07 bp/day overnight (t = 0.23)** against **+1.77 bp/day
intraday**. **The overnight component sits almost entirely in the SHORT legs** (+1.49 bp/night for
high issuance, +3.79 for high `IVOL`). Transcription and arithmetic:
[`data/B3_session_interval_sums.py`](../../../data/B3_session_interval_sums.py), [`.txt`](../../../data/B3_session_interval_sums.txt).

**THE RECONCILIATION, WHICH `B3` CALLS ITS MOST IMPORTANT OUTPUT AND THIS RECORD AGREES IS THE MORE
USEFUL HALF.** The **market's** return is overnight — LPS (2022) measure the quarterly intraday
`RMRF` mean at **0.000** against **0.018** overnight, 1993Q3–2019Q4. A long-only book's total return
is dominated by its **beta**; its tilt is its **alpha**. **An overnight total return plus an intraday
characteristic alpha is exactly what the literature predicts for a long-only book.** The programme's
central fact and `A2`'s surviving family were never in tension — they are statements about two
different objects, **the level and the tilt. Nothing about the overnight finding argues for or
against a characteristic book.**

**Q5 is answered DESCRIPTIVE rather than ACTIONABLE, and `B3` priced it.** Separating the sessions
needs **21 round trips a month = 1,420 bp** at this programme's own 67.6, against **37 bp** of gross
intraday long-leg alpha — **short by 38.2×**, and 10.0× on LPS's long–short. Two further sources say
the same in prose, and **NightShares' two overnight ETFs closed fourteen months after launch.** One
peer-reviewed dissent is recorded (Lachance 2023, RFE) **with its cost section unread.**

**No mechanism survives the long-hold test.** Retail-at-the-open and closing-auction flow **relabel
sessions without changing the holder's total.** Overnight inventory risk is the only one that pays
holders — and it is **characteristic-neutral** (its signature is `IVOL`/`BETA`, not `GP`) and now
measures zero. The arbitrageur-margin mechanism is **short-leg-only**, so predicts nothing for
long-only, **and the data agree.** News response is the only mechanism with demonstrated multi-month
persistence, and it keys on a news-exposure characteristic **this programme cannot compute.**

**The confirmed absence is narrower than the lane hoped, but it exists:** nobody has published the
decomposition **equal-weighted, long-only, microcap-inclusive, or past 2015**, and **no era split of
a characteristic's session location exists anywhere.** But `B3`'s own §7 constraint **binds harder
than the literature gap**: the overnight component is largest among **illiquid, small,
high-volatility** names — precisely those correlated with delisting — so a measurement on the
intraday-reachable **survivor** subset would **understate the dispersion and could get the sign
wrong.** **The `$5` floor is not the problem** (Bogousslavsky uses $5 + $100m); **weighting and
dead-inclusion are.**

### `B4` — shares outstanding, float, and the split-history gap

**`D9` CLOSES ON BOTH HORNS: the split gap CANNOT be closed from free data, AND THE SIGNAL DOES NOT
NEED IT.** Round 1 left `A2` and `A1` each right about a different half. `B4`'s answer is that the
half everyone was arguing about **was the wrong half.**

**`F1` — the same-filing ratio is split-immune by construction, and its error rate is measured.**
Accounting rules require **every period presented in one filing to be restated onto the current share
basis**, so a ratio formed from two comparative periods **inside a single filing** has the split factor
in both numerator and denominator, where it **cancels algebraically**. Evidence:
[`data/B4-same-filing-ratio-error-rate.csv`](../../../data/B4-same-filing-ratio-error-rate.csv).

| | same-filing ratio | naive cross-filing |
|---|---|---|
| **where a level restatement intervened** (n = 58) | **32.8% agreed EXACTLY**, p95 deviation **0.498%**, **ZERO of 58 showed a split-sized error** | **contaminated on 11 of 11 known split events** in the same names, **by factors 0.099 to 1,049** |

**I recomputed all four of those figures from the lane's own CSV before recording them.** 865
comparisons, n = 58 restated, **19/58 = 32.8% exact**, **0 of 58 at or above a 1.5× error**. The p95
is **0.4656% by linear interpolation and 0.49778% by nearest rank** — `B4`'s 0.498% reproduces
exactly under the nearest-rank convention, and the difference is a percentile convention, not a
discrepancy. **One precision note:** the 865 comparisons come from **92 CIKs that produced repeat
pairs, out of the 161-CIK cohort** — `B4`'s §5 states the cohort and the pair counts separately and
correctly; only its summary line compresses the two.

**The residual error is reporting-precision loss, not contamination** — Tesla 0.46%, GE 0.057% — and
**both tail outliers are one micro-cap reverse-merger shell** (Erin Energy; max deviation 33.08%,
against a signal whose own interquartile range is 0.98658–1.05200). **The restated rows are the proof:**
Tesla's level restates by **4.9883×** and NVIDIA's by **4.00493×**, Amazon's by **20.01×** and ODP's by
**0.09946×**, while the same-filing ratio moves by **0.0046, 0.0016, 0.0008 and 0.0038 in log**.

**`F2` — `A1`'s "no split history anywhere in XBRL" is contradicted, and the route still fails.**
`us-gaap:StockholdersEquityNoteStockSplitConversionRatio1` **exists**, returns correct ratios for
Apple (7, 4), NVIDIA (4, 10), Tesla (5, 3), GE (0.125), Citigroup (0.1), Chesapeake (0.005), Rite Aid
(0.05), and is carried by **2,280 distinct CIKs, 2009–2026.** **Rejected on five measured defects, not
on absence:** the date is sometimes a board-approval date, sometimes a month-long range, sometimes the
fiscal year end; **Tesla's same period carries both `val=5` and `val=3`**; **30.8% of non-unit ratios
predate the issuer's first cover page** (pre-IPO reverse splits, up-C exchange ratios — Duckhorn at
1,017,134.6); the FSDS shows **38 of 101 rows sit on a `Range=Minimum/Maximum` axis the API strips**,
so it can hand you an **authorised bound rather than an executed ratio**; and latency is **31–547
days**. **Conflict with `A1` recorded at E8, not adjudicated.**

**`F3` — the fabrication is named and confirmed against the primary document.** HP Inc's 10-K/A tagged
its cover-page count **`165228387`**, while the same document reads *"…as of November 30, 2017 was
**1,645,228,387** shares."* **A single dropped digit in a $30bn issuer.** A jump detector reads it as a
**1-for-10 reverse in November 2017 and a 10-for-1 forward in January 2018. HP never split.** Across
80 random CIKs the jump detector fired **157 times** above 20% on untagged names, and **no threshold
can separate them**: genuine annual share growth reaches **330×** while splits start at **1.5×**.
Evidence: [`data/B4-split-detector-crosstab.csv`](../../../data/B4-split-detector-crosstab.csv).
**This is the commissioning requirement discharged on its own terms** — the brief said an inferred
split is a fabricated corporate action, and `B4` produced one and named it.

**Coverage, for the record.** `dei:EntityCommonStockSharesOutstanding` ∪ a WASO fallback chain reaches
**91.0% of 6,532 `Assets`-filers**, **7.8% have nothing**, median as-of→filed lag **5 days**, and
**dead names (Sears, BBBY, SVB) are fully retained on CIK.**

**A 20% multi-class blind spot the lane was not commissioned to find.** Berkshire, Meta, Ford, Comcast,
Visa, UPS, Accenture and CME have **no non-dimensional cover-page count at all** — the count exists
only on a share-class axis the company-concept API strips. **WASO survives on 16 of those 20**, so the
recommended route also has the better coverage. **The FSDS `segments` file is the only free product
that recovers the dimensioned rows.**

**Three further hazards returned.** A **new wrong-HTTP-200 flavour**: 650 bytes, valid JSON, `units`
present, **correct unit key present, zero facts** (Expand Energy, Chubb, Ford) — *the catalogue moves
to twelve.* A **`frames` artefact that inverts a coverage number by 2×**: single-bucket 35.6% against
union-of-four-quarters 81.4%. And **the successor-entity defect defeats both vintage rules** — CIK
895126 reports the instant `2019-02-01` as **both 717,376,170 and 3,600,000**, so *"latest filed wins"*
is **wrong by 199× fourteen months before the split** (E11).

**Scale and discipline:** 1,110 requests, 138.3 MB, **zero 429/403/503**, **twelve negative controls all
clean.** Two sources not obtained and said so: Pontiff & Woodgate (urllib DNS failure on `www2.bc.edu`,
HTTP 403 on Wiley) and ASC 260-10-55-12 (login-gated, **not read**). And **a search result purporting
to be Pontiff–Woodgate fetched at 200 / 360 KB and proved to be Larrain & Urzúa on Chilean data** —
caught, flagged, correctly attributed.

---

## 3. TWO OF THIS PROGRAMME'S OWN CONTESTED FINDINGS ARE INDEPENDENTLY CORROBORATED

**`B3` returned this and it is checked against our own tables rather than taken on trust.**

**The volatility inversion is `IVOL`'s published decomposition, and the signs match ours.**
[`FINDINGS.md`](../../FINDINGS.md) §6 (D264) has low-vol names accruing **+5.56%/yr intraday** against
high-vol **−8.97%**, and overnight **+4.36%** against **+13.81%**. So **low-minus-high is positive
intraday and negative overnight** — which is **LPS's `IVOL` row exactly** (−1.46 overnight, +2.48
intraday). Corroborated a third time on beta by Hendershott, Livdan & Rösch (2020, JFE 138:635–662)
`[read in full]`: *"returns are positively related to beta overnight, whereas returns are negatively
related to beta during the trading day"*, night SML `R²` 96.2%, day 92.2%. **Three independent
measurements across 1986–2016. The internal finding is not an artefact of this programme's sample.**

**The era inversion has an analogue from the original authors.** Boyarchenko, Larsen & Whelan,
*"The Disappearing Overnight Drift"*, Liberty Street Economics, **1 July 2026**
`[OFFICIAL FED BANK BLOG, BY THE ORIGINAL AUTHORS] [read in full]`: the 02:00–03:00 ET window that
*"previously generated roughly 3.7 percent per annum has averaged close to zero since 2021"* — once
*"more than 60 percent of the contract's 5.9 percent annualized close-to-close return."* Channel
attribution: end-of-day signed-volume-imbalance **sd fell 6.5% → 2.9%**, while **VIX (20.4 → 19.4)
and the overnight volume share (15% → 16%) barely moved.** Their falsifiable prediction is quoted in
the brief. **Our own [`FINDINGS.md`](../../FINDINGS.md) §6 intraday drift goes −0.33% full sample →
+1.44% ex-2020 → +3.05% from 2021** (D247), **and an overnight component that dies is arithmetically
an intraday component that appears.** Different objects — US single names vs the E-mini, a book vs an
index — **and `B3` states that it is not claiming the same measurement.**

---

## 4. CONFLICTS — RECORDED, NOT ADJUDICATED

| | the conflict | readings |
|---|---|---|
| **E1** | **What does CFM attribute the long-leg advantage to?** | **`A3` (`R1-03` §8.1):** CFM reproduce Blitz and attribute the gap to **an SMB exposure created by the 2×3 construction**. **`B1`:** the SMB exposure appears **when the hedge is the cap-weighted SPmini — the benchmark Blitz explicitly refused**; with Blitz's own 50/50 hedge, CFM find *"no striking difference of Sharpe ratio between the long and short legs"* and an optimal short weight of **30%, not zero**. `B1` supplies the verbatim figure note and body text; `A3`'s entry is a one-line characterisation. **Both stand.** |
| **E2** | **Is `A3`'s Var(t) = 0.98 evidence of an absent signal, or an artefact of its benchmark?** | **`A3`:** Var(t) = 0.98 is below the luck null and is evidence the long leg carries no signal. **`B1`:** the mismatched benchmark injects sd 1.2–2.8%/mo, predicting Var(t) = **0.76–1.19**, so 0.98 *"is a benchmark artefact."* **Both stand; `B1`'s is a verdict recorded as `B1`'s.** |
| **E3** | **Does `CbOP` survive, or is it subsumed?** | **`B2`/Ball et al.:** `CbOP` survives both deflator conventions, both weightings, big stocks alone, post-2005 (t 3.02–3.44). **Novy-Marx & Medhat (NBER w33601, Mar 2025):** an R&D-adjusted operating profitability **subsumes `CbOP`, t 6.99 vs 0.42**, post-2000 fully — **but they change deflator, estimator AND numerator at once.** **Both sides are interested parties** (BGLN authored `CbOP`; Medhat is at Dimensional). `B2` states which it would weight and why. **Recorded unresolved.** |
| **E4** | **`P5`'s tables vs `P5`'s own prose.** | Table 3 gives gross profitability netting **0.37 at t 2.74**; the same paper's text lists the strategies achieving net excess returns significantly above zero **and gross profitability is not among them.** `B2` read both, records the tension, **did not resolve which the paper intends.** |
| **E5** | **Is "no filers" a `0` or an `HTTP 404`?** | `A1`'s census table records `CostOfGoodsSold` as **0** in the later years; `B2`'s independent census of the same tag-years records **`HTTP 404`**. Both mean no filers — **but `A1`'s brief is the one that warned against coercing a 404 to a zero.** Every other shared cell between the two censuses **matches exactly**, which makes this a replication with one encoding discrepancy. **Recorded, not adjudicated.** |
| **E6** | **Weighting: three positions, three justifications.** | `S7`: value-weighting *"accurately reflects the wealth effect experienced by investors."* `S10`: equal weighting excluding low-cap stocks is preferable. `S9`: capped value weights, *"a helpful compromise"*, worth **+8.5pp** on replication. **No resolution in the literature.** |
| **E7** | **Do long legs dominate?** | `S3` (Blitz): yes — combined long Sharpe **1.10 vs 0.69** short, 1963–2018, minus a 50/50 hedge. `S4` (CFM), reproducing it: *"the short leg should be allocated 30% of the weight, and not zero weight… the 'no-short' recommendation is not robust against such minor changes."* **Both are interested parties pointing opposite ways. Both stay.** |

| **E8** | **Is there split history in XBRL?** | **`A1`:** *"There is no split history in any XBRL product"* ([`R1-01`](R1-01-free-fundamentals.md) line 745), and every share-count signal therefore requires the corporate-actions feed as a **hard dependency** (line 885). **`B4`:** `us-gaap:StockholdersEquityNoteStockSplitConversionRatio1` **exists and is carried by 2,280 CIKs, 2009–2026**, with correct ratios for seven named issuers. **Both stand.** `B4` then rejects the route on **five measured defects**, so the two lanes' practical conclusions coincide while **their factual claims do not.** |
| **E9** | **Does the reference dataset divide or multiply by the split factor?** | **`A2`** quotes the source's own `Detailed Definition` *"read in full"*: the share count is **`shrout/cfacshr`** ([`R1-02`](R1-02-persistent-characteristics.md) line 253). **`B4`:** the shipped **code** computes **`shrout*cfacshr`**. **An inverted factor turns a 7:1 split into a 49-fold error.** This is a **documentation-versus-code disagreement in the external source**, not an error by `A2`, which quoted the documentation accurately. **Both stand.** |
| **E10** | **Does composite equity issuance need a share count?** | **`A2`** lists `CompEquIss` among *"three members that need no financial statement at all — only a split-adjusted share count"*, **while its own gloss of that same entry** says it needs *"market cap and total return"* — an internal tension inside one list. **`B4`:** Daniel & Titman (2006) **p. 1614 states it verbatim** — *"corporate actions such as splits and stock dividends leave ι unchanged"* — and Chen–Zimmermann's `CompEquIss` code takes only `[ret, mve_c]`: **no share count, no split factor.** **Recorded as a tension resolved in `B4`'s direction by a primary source, with `A2`'s entry left standing as written.** |
| **E11** | **Does "latest filed wins" reconstruct a point-in-time vintage?** | **`A1`:** `companyfacts` is **PIT-reconstructible** — every vintage stamped with accession, form and filing date, verified on six named as-of dates. **`B4`:** CIK 895126 reports the instant `2019-02-01` as **both 717,376,170 and 3,600,000**, so *"latest filed wins"* is **wrong by 199× fourteen months before the split** — the successor-entity defect **defeats both vintage rules**. This extends `A1`'s own spin-off identity defect rather than contradicting its reconstruction method. **Both stand.** |

### 4a. AND EVERY LANE RECORDS FURTHER CONFLICTS INSIDE ITS OWN BRIEF — pointers, so none is invisible

**`E1`–`E11` are the CROSS-LANE conflicts. They are not all of them.**

| lane | where | carries |
|---|---|---|
| `B1` | [§4](R2-01-the-benchmark-question.md) *"THE CONFLICT, RECONCILED ARITHMETICALLY"* and §10 | `S3` vs `S4` on whether long legs dominate; **three positions on weighting with three justifications**; a paper's prose against the campaign's own scepticism about prose |
| `B2` | [§2.4](R2-02-profitability-deep.md) *"the most recent authority says the opposite, and both sides are interested"* | the `CbOP`-subsumption contradiction (= `E3`), and `P5`'s Table 3 against `P5`'s own text (= `E4`) |
| `B3` | [`R2-03`](R2-03-where-the-premium-accrues.md) **inline at §2.3, §4.2 and §8** rather than in one section | **the same authors disagreeing with themselves** across two papers; a peer-reviewed dissent recorded **with its cost section unread**, which the brief flags as *"recorded with one side unread"* |
| `B4` | [§4.1](R2-04-shares-outstanding-and-float.md) *"The conflict with `A1`, recorded not adjudicated"* | the split-ratio tag's existence against round 1's finding (= `E8`) |

**Nothing is deleted and nothing is merged away.** Where a brief records a conflict **with one side
unread**, that asymmetry is stated rather than used to settle it.

**Round 1's conflicts `D1`–`D10` all still stand.** **`D9` — the share-count dependency failure — is
the one round 2 was sent at, and `B4` reports that both its horns fail in the same direction:** the
split gap cannot be closed from free data, **and the signal does not need it closed.** `D9` is recorded
as answered by `B4`; **under [R15](../../RULES.md#r15) only the principal closes an avenue.**

---

## 5. MY OWN WRONG PREMISES THIS ROUND, RECORDED AS MINE

1. **I compressed `A3`'s headline figure in a way that dropped its cross-section, and handed that
   compression to two agents as a premise.** [`R2-00-slate.md`](R2-00-slate.md) says *"`A3` measured
   the long leg at −0.04%/month against the value-weighted market."* **The −0.04% is the
   cross-sectional MEAN over ~170 anomalies**, and the same column gives profitability **+0.40,
   +0.26, +0.14**. **`A3`'s own brief said both things** — its line 96 labels the figure a
   cross-sectional mean, and its §7.1 names the **+0.40 best case as cash-based operating
   profitability.** So **the imprecision is mine, not `A3`'s**, and `B2` caught it by re-extracting
   the source. **Both readings of the conflict still stand.**
2. **I named the wrong benchmark as the circularity risk.** The commissioning brief warned `B1` that
   subtracting an equal-weighted universe return from an equal-weighted long leg *"may remove
   precisely the size and illiquidity exposure that generates the premium."* `B1` finds the
   circularity is **real but lives in the characteristic-matched benchmark**, where the DGTW authors
   name it themselves in print. **The warning was aimed at the wrong object.**
3. **I commissioned `B3` on a hypothesis the published literature already contradicts.** The lane was
   told that a join between the programme's overnight finding and a characteristic premium would be
   *"a join between the programme's own finding and the only family still standing."* **Two JFE
   papers had already measured the opposite.** The lane's bar was written to accept a confirmed
   absence and instead met its first branch — **which is the bar working, not the premise.**
4. **I told `B4` the source literature would not state the split-free formulation, and I was wrong
   twice over.** The brief supposed it *"will not state"* it *"because it assumes split-adjusted vendor
   data."* **Daniel & Titman (2006) state it on p. 1614 in so many words**, and Chen–Zimmermann's
   open-source code **already ships it with no share count at all.** I also framed the lane's crux as
   *"can a split be detected without a split table"* — **`B4`'s answer is that the question was the
   wrong one**, because the construction that needs no split detection was in the literature the whole
   time. **The lane answered the question I should have asked, which is the lane's credit and my
   error.**

## 6. AN OPEN QUESTION ON `B2`'s MEASUREMENT THAT `B2` DOES NOT RAISE — MINE

**`A1` established in round 1 that the `frames` endpoint returns LAST-FILED values** — that is `A1`'s
central negative, demonstrated with a 98% error 2.3 years early. **`B2`'s tag census runs on
`frames`.** A census there therefore counts filers **by their latest vintage**, so an **ASC 606
retrospective restatement** could move a filer from the old revenue tag to the new one **for a
pre-2018 period**, making the FY2018 break look **sharper and later** than it was point-in-time.
`B2` flags the **non-calendar-fiscal-year** loss and says its absolute counts are lower bounds; **it
does not flag this one.** Whether it bites is unmeasured. **Recorded as an open question, not a
defect.**

---

## 6a. WHAT LATER ROUNDS FOUND ABOUT THIS ROUND — a forward index, not a repair

| round 2 finding | what happened to it |
|---|---|
| `B1`: the whole benchmark disagreement is **one identity**, middle term measured | **Reproduced and extended three times.** Round 3's `C2` got a sharper version on free data (**+0.971 against cash, −0.322 against the CAPM, same 198 months**); `C3` hit the same finding **without being told to look for it** (`t` 3.73 / 2.08 / 0.45 across three benchmarks); `C4` hit it as a **near-miss** and said a single-benchmark measurement *"would have shipped the wrong sign."* **`B1`'s lane is the most independently confirmed of the campaign.** |
| `B2`: the **lagged deflator** collapses gross profitability to `t` 1.04–1.85 | **Scoped, then contested.** Round 3's `C1`: the collapse is **annual-only** — quarterly gives 0.51 [`t` 3.40] ([`F2`](R3-99-record.md)). Round 4's `D2`, measuring the same quarterly construction on a different library: **0.163 [`t` 1.43], insignificant, three for three** ([`G1`](R4-99-record.md)). **All three stand.** |
| `B2`: the lagged convention is *"what the source paper specifies in its own appendix"* | **Wrong, and `B2` had flagged exactly that risk** — it rested on three second-hand restatements after failing to obtain the paper. `C1` obtained the **2014 working paper**: it deflates by **CURRENT** assets ([`F3`](R3-99-record.md)). **`B2` had quoted the disconfirming code comment itself.** |
| `B2`: **`CbOP` is the one survivor** | **Round 3 and 4 pull both ways.** `C1`: `CbOP` **gains nothing** from the quarterly frequency (0.53 → 0.49) and reaches **nine CIKs** quarterly from as-filed data. `D2`: `cop_at` is **by far the strongest** measured (0.515, NW6 8.31). **So the definition with the best evidence remains the one the data cannot deliver.** |
| `B2`'s and `B4`'s reliance on a `GP`/`GPlag` **deflator placebo** | **Round 4's `D3` found it is not a clean placebo** — the two halves use different revenue fields and different financial-sector exclusions. |
| `B3`: the session distinction is **descriptive, not actionable**, priced at ~38× | **Unchallenged by any later lane.** |
| `B4`: the **same-filing ratio** is split-immune, error rate measured | **Unchallenged by any later lane.** `D9` stays closed on both horns. |
| `B4`: a **20% multi-class blind spot**, found after its bar | **Became the campaign's standing evidence that the bar is a floor** — quoted in [`00-SCHEMA.md`](00-SCHEMA.md) §2a requirement 1 and in every round-3 and round-4 prompt. |

## 7. What this record does not claim

**Nothing here was measured on this programme's fixture.** `B1`'s measurement is on Ken French's
public files, `B2`'s and `B4`'s on the SEC's public endpoints, `B3`'s is transcription plus arithmetic
on published tables. **No backtest was run, no null drawn, no candidate exists, no territory is
closed, no avenue is closed** ([R15](../../RULES.md#r15): only the principal closes an avenue).
**Both books are unchanged**, [`FINDINGS.md`](../../FINDINGS.md) and [`PICKUP.md`](../../internal/PICKUP.md)
are untouched, **and nothing in this folder is elevated out of `docs/research/`.**

**`B4`'s `F1` is a measured error rate on public filings, not a signal.** It says a construction is
**split-immune**, which is a statement about arithmetic and accounting rules. **It says nothing
whatever about whether net share issuance pays on this programme's universe**, and `B4` does not claim
otherwise. **Three of the four lanes' headline conclusions depend on benchmarks, deflators or session
boundaries that `B1`, `B2` and `B3` each show move the answer** — which is the round's own reason for
caution about all of them.

## 8. TOKEN COST OF THE ROUND

**~1.13M subagent tokens across four lanes** (B1 280k, B2 284k, B3 272k, B4 296k), against
[`00-SCHEMA.md`](00-SCHEMA.md) §2's projected **1.0–1.4M a round**. Round 1 was ~1.14M. **The schema's
arithmetic holds to within 1% across two rounds, and the per-agent depth is stable at ~250–300k.**
