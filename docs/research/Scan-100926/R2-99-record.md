# Scan-100926 · Round 2 — record

**Slate:** [`R2-00-slate.md`](R2-00-slate.md) · **campaign contract:**
[`00-SCHEMA.md`](00-SCHEMA.md) · **round 1:** [`R1-99-record.md`](R1-99-record.md) ·
**previous campaign:** [`../README.md`](../README.md).

**STATUS: PARTIAL — `B1`, `B2` and `B3` are in; `B4` is still running.** This record will be
**extended in place** when `B4` lands, so the order things were learned in stays visible. Round 1's
record was built the same way.

**Under [R15](../../RULES.md#r15) nothing here closes or admits anything.** Nothing in this folder is
elevated out of `docs/research/`. **Conflicts below are recorded, not adjudicated** — including the
two where a lane reached a verdict and said so, and the one where two lanes read the same paper and
disagree about what it says.

---

## 0. THE SHAPE OF THE ROUND SO FAR

**The round was commissioned to pursue four threads round 1 opened. Three have reported, and all
three came back with the same structural answer in different subject matter: THE CONSTRUCTION
DETAIL NOBODY'S NAME CARRIES IS THE THING THAT DECIDES THE ANSWER.**

- `B1`: the whole `A2`-vs-`A3` disagreement is **one identity**, and the term that separates them is
  measurable — *and its sign flipped in the era this programme trades.*
- `B2`: the profitability family splits in two on **whether the deflator is current or lagged
  assets**, a line no paper's title or abstract carries.
- `B3`: the session split of a characteristic premium is **published, twice, and points the other
  way from the lane's hypothesis** — and the distinction is **descriptive rather than actionable**,
  priced at `~38×`.

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

### `B4` — shares outstanding and float

**Still running.** This section will be written when it lands.

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

**Round 1's conflicts `D1`–`D10` all still stand.** `D9` — the share-count dependency failure — is
`B4`'s subject and is unreported.

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

## 7. What this record does not claim

**`B4` has not reported**, and §2's `B4` entry and `D9` are both empty. **Nothing here was measured
on this programme's fixture** — `B1`'s measurement is on Ken French's public files, `B2`'s on SEC
`frames`, `B3`'s is transcription plus arithmetic on published tables. **No backtest was run, no null
drawn, no candidate exists, no territory is closed, no avenue is closed** ([R15](../../RULES.md#r15):
only the principal closes an avenue). **Both books are unchanged**, [`FINDINGS.md`](../../FINDINGS.md)
and [`PICKUP.md`](../../../PICKUP.md) are untouched, **and nothing in this folder is elevated out of
`docs/research/`.**
