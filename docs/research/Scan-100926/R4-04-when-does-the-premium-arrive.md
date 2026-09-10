# `D4` — WHEN DOES THE PREMIUM ARRIVE? CONCENTRATION IN TIME, IN NAMES, AND THE HORIZON IT IMPLIES

**Round 4, lane `D4`.** Campaign contract: [`00-SCHEMA.md`](00-SCHEMA.md). Slate:
[`R4-00-slate.md`](R4-00-slate.md). The lane this one is downstream of is
[`R3-04`](R3-04-is-it-already-dead.md) (`C4`), with a second debt to
[`R3-03`](R3-03-the-shape-of-the-drawdown.md) (`C3`).

**EXTERNAL LITERATURE AND PUBLIC-DATA ONLY.** I have no access to the programme's fixture and
claim nothing about it. Every number I measured is on Ken French's published portfolio files or
on papers I read in full as local text — all named, all re-runnable from
[`data/D4_*`](../../../data/).

Under [R15](../../RULES.md#r15) **nothing here closes or admits anything**, nothing is elevated
into `FINDINGS.md`, `RULES.md`, the books or a decision record. Both books are unchanged. **This
lane proposes no timing rule** — regime gates and timing screens are excluded ground from the
first campaign, and §6 reports only what the literature claims.

---

## 0. THE ANSWER, STATED FIRST, AND IT GOES AGAINST THE PREMISE I WAS SENT WITH

**THE NUMBER THIS LANE WAS COMMISSIONED ON — "THREE OF 132 MONTHS CARRY HALF THE TOTAL" — IS NOT A
MEASUREMENT OF ARRIVAL. IT IS A RESTATEMENT OF THE `t`-STATISTIC. I BUILT ITS NULL AND IT SITS AT
THE NULL'S MEDIAN.**

1. **`months-to-half` is a near-deterministic function of `t` and `T`, and nothing else.**
   `[MEASURED IN BRIEF]` At **`T` = 132 months and `t` = 1.25** — `C4`'s long leg exactly — an
   **iid Gaussian with no fat tails, no skew, no clustering, no events and no regimes** produces
   `months-to-half` with **p05 = 1, median 4, p95 = 8, mean 4.16**. `C4` observed **3**. That is
   *inside* the interquartile region of pure noise. The statistic measures **how badly a mean is
   measured**, not how it arrives. §3.1, §3.2.

2. **THE DECISIVE NEGATIVE CONTROL: the CRSP value-weighted market's own equity premium reaches
   half its 1963–2013 total in 14 of 606 months — `2.31%` of them.** `C4`'s figure is
   `3/132 = 2.27%`. **The two percentages differ by four hundredths of a percentage point.**
   Nobody calls the equity premium concentrated. §3.2.

3. **On a SCALE-FREE concentration measure there is NO excess concentration anywhere — and the
   controls prove it.** The share of the sum of all *positive* months carried by the top 10% of
   positive months is **0.25–0.33 for every one of the 13 series I measured**, including the
   market excess return, `SMB` and `CMA`. Profitability long legs: 0.266 (post-pub) and 0.315
   (in-sample). Market: 0.257 and 0.261. **There is no measurable difference.** §3.4.

4. **BUT ARRIVAL *IS* CLUSTERED IN TIME, AND THAT IS THE REAL FINDING — AND IT IS THE THING
   `months-to-half` IS STRUCTURALLY BLIND TO.** `months-to-half` is an **order statistic**: it
   cannot see time at all. The statistic that can — the share of the total earned in the best
   contiguous window, against a **permutation null that preserves the marginal distribution
   exactly** — says: for the profitability long leg, **73.7% of the entire 1963–2013 total was
   earned in the 12 months 2000-10 → 2001-09 (`p` = 0.003)**, and **82.5% in the 36 months
   2000-03 → 2003-02**. For the value-weighted `Hi10−Lo10` spread the same 36 months carry
   **99.8%**. **And the same permutation test on the market's own excess return returns
   `p` = 0.60 — no clustering.** §4.

5. **THE EPISODE IS THE DOT-COM VALUATION UNWIND, NOT A RECESSION — and the literature's own
   regime story does not survive my check.** Asness–Frazzini–Pedersen document `QMJ` earning
   **0.76 %/mo in 110 NBER recession months against 0.33 in 568 expansion months** (US 1956–2012,
   read in full). On French's profitability sorts, 1963-07 → 2026-07, **recessions pay 1.3–1.7×
   expansions but the difference is `t` = 0.12 to 0.52 — not distinguishable from zero.** The
   clustered window (Mar 2000 → Feb 2003) overlaps the 2001 recession by only 8 of its 36 months.
   **And the market LOST money in that window** (it is −12.2% of the market's own total), so the
   cluster is a cross-sectional episode, not a good-times episode. §5, §4.3.

6. **THE SYMMETRIC TRIM, WHICH THIS LANE WAS ORDERED TO CARRY, CHANGES THE VERDICT — AND IT CUTS
   BOTH WAYS.** For `C4`'s own construction the symmetric 1% trim is **+16.9 bp against a raw
   +17.9** — 94% of the raw mean — while the ex-top trim alone is +14.1 and the ex-bottom +20.7.
   On my measurement of the in-sample long leg the ex-top trim is **+0.08 bp** (annihilated) and
   the symmetric trim is **+5.93 bp against a raw +6.48** — **91% of the raw mean.** **"Drop the
   top 1% and it is zero" is simultaneously true and empty.** §3.5. And the leave-one-year-out
   drop that frightened `C4` is also unremarkable: under the matched Gaussian, **28.3% of draws at
   `t` = 1.25 have a worst-LOO mean below 40% of the full mean**, and `C4`'s is exactly 40.2%.
   §3.3.

7. **THE LITERATURE REPORTS MEANS AND `t`-STATISTICS AND NEVER THE ARRIVAL PATTERN — CENSUSED ON
   SIX PAPERS READ IN FULL, WITH A CONTROL THAT FIRED TWICE.** Across Novy-Marx (2012),
   Engelberg–McLean–Pontiff (2017), Hou–Xue–Zhang (2017), McLean–Pontiff, Chen–Zimmermann (2021)
   and Ilmanen et al. (2021): **the word "drawdown" appears ZERO times in all six**; "months to
   half / half of the total" **ZERO in all six**; "best/worst month" **ZERO in five of six**;
   "fraction/percentage of months positive" **ZERO in all six once false positives are removed**;
   kurtosis **ZERO in five of six**. The founding paper of this programme's own family reports
   means, **test**-statistics and Sharpe ratios and **not one** arrival statistic. §2.

8. **SUB-QUESTION 6 IS ANSWERED AND THE SLATE'S CONJECTURE IS WRONG. The legs do not offset —
   they arrive in the SAME window.** The short leg's premium also peaks in
   **2000-03 → 2003-02, carrying 108.7% of its in-sample total (`p` = 0.004)**. So the spread
   **inherits and compounds** the long leg's clustering rather than smoothing it: the same 36
   months are 82.5% of the long leg's in-sample total and **99.8%** of the spread's. §7.

9. **A METHOD CATCH I WAS NOT LOOKING FOR, AND IT FLIPS A SIGN.** French's OP deciles use **NYSE
   breakpoints**, so `Lo 10` holds on average **967 firms** and `Hi 10` **322**. The simple mean
   of ten decile returns is therefore **NOT** the sort's equal-weighted universe. Rebuilt exactly
   from the file's own firm-count block, the EW long leg's alpha goes from **−0.0207 [`t` −0.45]
   to +0.0262 [`t` +0.45]** over 1963–2026, and from **−0.1013 [−0.87] to +0.0342 [+0.20]**
   post-2013. **The benchmark error is 13.6 bp/month post-2013 and it flips the sign.** `C4` made
   the same simple-mean assumption on a different provider's portfolios; I could not check theirs.
   §8.

10. **ON HORIZON, THE HONEST ANSWER IS WORSE THAN `(2/IR)²` SUGGESTS AND I MEASURED IT TWO OTHER
    WAYS.** `[MEASURED IN BRIEF]` For the profitability long leg against the VW market,
    1963-07 → 2026-07: `IR` 0.187, `(2/IR)²` = **114.2 years**, the horizon merely to be 95% sure
    the realised premium is positive = **77.3 years**, and — the number nobody publishes —
    **26.7% of all actual overlapping 10-year windows were negative, and 23.4% of all 20-year
    windows.** Against its own EW universe the `IR` is **0.057** and `(2/IR)²` is **1,234.6
    years**, which independently reproduces `C3`'s **1,235** on different data and a corrected
    benchmark. §9.

**The precise negative I would put above all of it:** the premium's arrival has no unusual
*distributional* concentration at all, but it has strong and significant *temporal* clustering in
a handful of cross-sectional episodes, the largest of which is a single three-year window without
which the profitability spread does not exist; and **there is no published evidence those episodes
are identifiable ex ante at a cost that could be paid** — the best-documented attempt's own
break-even trading cost is **1.8 bp per dollar traded**. §6.

---

## 1. WHAT THIS LANE WAS SENT TO CHECK, AND THE PROVENANCE OF ITS PREMISE

`C4` reported, in passing (`R3-04` §3.2), on Chen–Zimmermann's `GP` quintile portfolios,
value-weighted, price > \$5, against the CRSP VW market, 2014-01 → 2024-12:

> mean **+17.9 bp [`t` 1.25]**; **drop 2023 and it is +7.2 bp [`t` 0.50]**; drop 2020 Q1 and it is
> +10.7 bp [`t` 0.77]; **three of 132 months (2.3%) carry half the total**; median **+14.5 bp**
> below the mean of 17.9 … symmetric 1% trim **+16.9 bp**, ex-top **+14.1**, ex-bottom **+20.7**.

**I verified the provenance of the figure inside the programme's own evidence file before building
anything on it.** `data/C4_robust.py` computes `months-to-half` **twice** — once on the long–short
series (`LS_months_to_half_of_post_pub_sum`) and once on the long-minus-market series
(`LmM_months_to_half`). The published sentence is about the long leg, and the figure quoted is the
**`LmM`** one: `data/C4_robust.json` gives `GP` → `LmM_months_to_half` = `{k: 3, of_n: 132,
pct_of_months: 2.3, sum_pct_mo: 23.6}`, while the long–short value is `k = 8`. **`C4`'s sentence
quotes the right one.** `[read in full — the programme's own script and artifact]`

**That reading also hands over the thing that turned out to matter: `sum_pct_mo` = 23.6.** The
whole 132-month total is 23.6 percentage-months, against a monthly standard deviation of
`0.1787 × √132 / 1.25 = 1.64`. **Half the total is 11.8, and the largest three draws from a
`N(0.179, 1.64)` sample of 132 sum to about 12.** The statistic was going to be 3 whatever the
world did. That is where this lane started.

---

## 2. DOES ANY SOURCE REPORT THE ARRIVAL PATTERN? A CENSUS ON SIX FULL TEXTS, WITH A CONTROL THAT FIRED TWICE

**Method.** Each paper fetched as bytes, extracted locally with `pdftotext -layout`, and probed
with whitespace- and hyphen-tolerant regexes. `data/D4_census2.py`, output
`data/D4_census2.json`. **Every paper's title line was read before counting anything** — the
guessed-identifier / wrong-paper flavour of a wrong 200 is caught only that way.

### 2.1 The control fired twice, and both times the PROBE was wrong, not the paper silent

This is reported before the results because it is the reason the results can be believed.

| version | paper | `t`-statistic probe | why it returned 0 |
|---|---|---|---|
| v1 (literal substrings) | Engelberg/McLean/Pontiff | **0** | the paper writes **"standard error"** (11×) and parenthetical `t`-values, and never the phrase |
| v1 | Chen/Zimmermann | `average return` = **0** | the paper writes **"mean return"** |
| v2 (regex `\bt[-\s]*stat`) | Novy-Marx 2012 | **0** | the paper writes **"test-statistic"** 26 times and never "t-statistic"; `\b` before `t` fails inside *test*-statistic |
| v2 | Engelberg/McLean/Pontiff | **0** | as above |
| **v3 (final)** | **all six** | **28 / 12 / 29 / 30 / 166 / 12** | **all PASS** |

**A literal-string census of a `pdftotext` extraction undercounts, and the only thing that reveals
it is a must-be-positive probe.** v1 *passed* on Novy-Marx for the wrong reason — "test-statistic"
contains the substring "t-statistic". The zero-probe (`zzqqx`) returned 0 in all six papers in
every version.

### 2.2 The census, after the controls pass

`P1` Novy-Marx 2012 WP *The Other Side of Value* · `P2` Engelberg/McLean/Pontiff 2017 WP
*Anomalies and News* · `P3` Hou/Xue/Zhang NBER WP 23394 *Replicating Anomalies* · `P4`
McLean/Pontiff WP *Does Academic Research Destroy…* · `P5` Chen/Zimmermann FEDS 2021-037
*Open Source Cross-Sectional Asset Pricing* · `P6` Ilmanen et al. 2021 JOIM *How Do Factor Premia
Vary Over Time?*

| probe | P1 | P2 | P3 | P4 | P5 | P6 |
|---|---:|---:|---:|---:|---:|---:|
| **drawdown / underwater / peak-to-trough** | **0** | **0** | **0** | **0** | **0** | **0** |
| **months-to-half / half of the total** | **0** | **0** | **0** | **0** | **0** | **0** |
| **best / worst month** | **0** | **0** | **0** | **0** | **0** | 6 |
| **fraction / % / number of months positive, hit rate** | **0** | **0** | 1† | 3† | **0** | 1† |
| concentrat* | 0 | 0 | 9 | 1 | 4 | 0 |
| skewness | **0** | **0** | 32 | 0 | 16 | 2 |
| kurtosis / fat tail | **0** | **0** | **0** | **0** | **0** | 1 |
| winsorise / trim | 7 | 3 | 11 | 1 | 0 | 0 |
| recession / business cycle / NBER | 1 | 6 | 15 | 0 | 11 | 36 |
| regime | 0 | 0 | 0 | 1 | 0 | 5 |
| cluster | 0 | 11 | 2 | 8 | 0 | 0 |
| required horizon | 1 | 0 | 0 | 0 | 0 | 2 |
| **control: `t`-stat / test-stat / standard error** | 28 | 12 | 29 | 30 | 166 | 12 |
| **control: mean / average return** | 86 | 1 | 95 | 1 | 45 | 5 |
| **control: impossible token** | 0 | 0 | 0 | 0 | 0 | 0 |

**† Every one of these four hits is a false positive, inspected individually:** HXZ's is *"firm
age, `Age`, as the number of months"*; McLean–Pontiff's three are *"the number of months between
the end of the sample and publication date is 44 months"* and two table-note repetitions;
Ilmanen's is *"the 20 percent worst and best months of global equity returns"* — used to condition
**correlations between factors**, not to report a premium's arrival share. **So the honest count
for "does any of these six report the fraction of months positive" is ZERO out of six.**

Ilmanen's six "best/worst month" hits are all the same construction: `Exhibit`-level correlation
conditioning on *the market's* worst/best 20% of months. **It is a conditional-correlation
statistic, not a concentration statistic.**

### 2.3 What this means, stated plainly

**`C4`'s three-of-132 is the only number of its kind this programme has, and the reason is that
the literature does not compute the statistic.** Every one of these six papers is a canonical
reference for this exact family or for its decay, and not one reports a drawdown, a months-to-half,
a best-month share or a fraction of months positive.

**The founding paper is the starkest case.** Novy-Marx's June-2012 73-page working paper
`[WORKING PAPER]` `[read in full — 112,857 chars extracted locally]` contains **zero** occurrences
of drawdown, best/worst month, months-to-half, fraction of months, concentration, skewness,
kurtosis, regime and cluster. It reports average returns (86×), test-statistics (26×) and Sharpe
ratios. Its single long/short split, verbatim:

> *"While the joint profitability/value strategy generates almost half its profits on the long
> side (0.28 percent per month more than the sample average for the high portfolio, as opposed to
> 0.34 percent per month less for the low portfolio), its real advantages over …"*

**That is a level statement, not an arrival statement.** It is also the only leg decomposition in
the paper, and it is for the *joint* profitability/value strategy, not for gross profitability
alone.

**AND THE CENSUS IS NOT EVIDENCE THAT THE PATTERN IS ABSENT — only that it is unreported.** A
paper that never writes "drawdown" has not shown there is no drawdown. That distinction is the
whole reason §§3–9 are measurements rather than a literature note.

---

## 3. CONCENTRATION IN TIME, MEASURED, WITH THE NULL THE LITERATURE NEVER BUILDS `[MEASURED IN BRIEF]`

### 3.0 Endpoints, blocks and the sentinel hazard — proved, not assumed

**Endpoint.** `https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/` — five zip files,
fetched 2026-09-10 by `data/D4_fetch.py` (UA `D4-research/1.0 (research@backtest-framework.org)`),
all HTTP 200 `application/x-zip-compressed`, sha1 recorded in the fetch log. `[PRIMARY DATA DOC]`
`[read in full]`

**Every block is identified by its own header line, printed into `data/D4_controls.json`
(`C1_blocks_read`), and the monthly block is terminated at the first non-six-digit date key so an
annual block cannot leak in.** Files state *"This file was created using the 202607 CRSP
database."*

| file | block header read | cols | monthly rows | span | `-99.99` / `-999` |
|---|---|---:|---:|---|---:|
| `Portfolios_Formed_on_OP` | `Average Value Weight Returns -- Monthly` | 18 | 757 | 1963-07 → 2026-07 | **0** |
| `Portfolios_Formed_on_OP` | `Average Equal Weighted Returns -- Monthly` | 18 | 757 | 1963-07 → 2026-07 | **0** |
| `Portfolios_Formed_on_OP` | `Number of Firms in Portfolios` | 18 | 757 | 1963-07 → 2026-07 | **0** |
| `Portfolios_Formed_on_OP` | `Average Firm Size` | 18 | 757 | 1963-07 → 2026-07 | **0** |
| `Portfolios_Formed_on_BE-ME` | `  Value Weight Returns -- Monthly` | 19 | 1201 | 1926-07 → 2026-07 | **43** |
| `Portfolios_Formed_on_BE-ME` | `  Equal Weight Returns -- Monthly` | 19 | 1201 | 1926-07 → 2026-07 | **43** |
| `6_Portfolios_ME_OP_2x3` | `Average Value Weighted Returns -- Monthly` | 6 | 757 | 1963-07 → 2026-07 | **0** |
| `F-F_Research_Data_5_Factors_2x3` | monthly factor block | — | 757 | 1963-07 → 2026-07 | **0** |
| `F-F_Research_Data_Factors` | monthly factor block | — | 1201 | 1926-07 → 2026-07 | **0** |

**The sentinel census reproduces round 3's `43` in the book-to-market blocks exactly — and
localises it, which round 3 did not.** All 43 sit in the **`<= 0`** column (firms with negative
book equity), contiguously from **1944-11 to 1963-06**, and **there are none at all in any decile
column**: `Lo 10` missing 0, `Hi 10` missing 0. **The hazard is real in that file and it lands in
a column a decile study never reads.** *This is a refinement of the warning, not a contradiction
of it — the profitability file carries no sentinels at all, so a study that used only `Hi 10` and
`Lo 10` would have been safe by luck.*

**Controls run before any measurement** (`data/D4_controls.json`):

| control | what it asserts | result |
|---|---|---|
| `C0` | `months-to-half` of a constant 1%×132 series **must be 66**; of a one-month-carries-all series **must be 1**; of a negative-total series **must be undefined** | 66, 1, 1, `None` → **PASS** |
| `C2` | after stripping, **no retained value may equal a sentinel** and none may be < −95% or > +250% | 77,346 values checked, **0 survivors** → **PASS** |
| `C4` | **`RMW` reconstructed from the 6 ME×OP (2×3) portfolios** by French's own formula `½(SH+BH) − ½(SL+BL)` must match the published `RMW` series | 757 common months, **max abs diff 0.005 pp**, mean 0.0025 pp (the file is published to 2 dp); published mean 0.25708 vs reconstructed 0.25718 → **PASS** |
| `_E` (part 2) | the series rebuilt in a second script must match part 1's means exactly | 52 checks, **worst abs diff 0.0** → **PASS** |

**`C4` is the one that proves I read the block I meant to read.** A mis-indexed column or a
leaked annual block would not reconstruct a published factor to half a basis point.

### 3.1 The statistic's null: `months-to-half` under pure iid normality, by `t` and `T`

`data/D4_t_to_khalf.json`. Each cell: 2,000 iid Gaussian draws, sd 1, mean `t/√T`. **No fat tails,
no skew, no autocorrelation, no events.** p05/p50/p95 and mean of `months-to-half`.

| `t` | `T`=132 | `T`=151 | `T`=606 | `T`=757 |
|---|---|---|---|---|
| 0.25 | 1 / **2** / 6 (2.6) | 1 / 2 / 6 (2.7) | 1 / 4 / 11 (4.5) | 1 / 4 / 12 (5.0) |
| 0.50 | 1 / **3** / 6 (2.9) | 1 / 3 / 7 (3.1) | 1 / 5 / 12 (5.2) | 1 / 5 / 13 (5.7) |
| 0.75 | 1 / **3** / 7 (3.2) | 1 / 3 / 7 (3.4) | 1 / 5 / 13 (5.8) | 1 / 6 / 14 (6.4) |
| 1.00 | 1 / **3** / 8 (3.6) | 1 / 4 / 8 (3.8) | 1 / 6 / 14 (6.6) | 1 / 7 / 16 (7.3) |
| **1.25** | **1 / 4 / 8 (4.16)** | 1 / 4 / 9 (4.3) | 1 / 7 / 15 (7.5) | 1 / 8 / 17 (8.2) |
| 1.50 | 1 / **4** / 9 (4.5) | 1 / 5 / 9 (4.8) | 2 / 8 / 16 (8.4) | 2 / 9 / 18 (9.2) |
| 2.00 | 2 / **6** / 10 (5.6) | 2 / 6 / 11 (5.9) | 3 / 10 / 19 (10.6) | 3 / 11 / 21 (11.6) |
| 2.50 | 3 / **7** / 12 (6.9) | 3 / 7 / 12 (7.3) | 4 / 13 / 22 (13.1) | 5 / 14 / 25 (14.4) |
| 3.00 | 4 / **8** / 13 (8.2) | 4 / 9 / 14 (8.7) | 7 / 16 / 25 (15.8) | 8 / 17 / 28 (17.3) |
| 5.00 | 9 / **14** / 18 (13.6) | 9 / 15 / 20 (14.5) | 18 / 27 / 37 (27.2) | 19 / 30 / 41 (30.0) |
| 10.00 | 21 / **26** / 29 (25.5) | 23 / 28 / 32 (27.5) | 46 / 57 / 67 (56.7) | 51 / 63 / 75 (63.0) |

**Read the `t` = 1.25, `T` = 132 row against `C4`'s observed 3.** The null median is 4 and the
5th–95th range is 1 to 8. **There is no signal in the observation.**

**And read the table the other way, because that half is just as important.** At `t` = 3 over 606
months the null median is **16**. A *well-measured* premium automatically looks unconcentrated by
this statistic, and a *badly-measured* one automatically looks concentrated. **The statistic is
monotone in `t` and carries essentially no independent information.**

### 3.2 Thirteen series, two nulls, same table — and the market is the control

`data/D4_table.tsv`, `data/D4_series.json`. `k` = observed `months-to-half`; `nullG` = iid
Gaussian with **matched mean and sd**; `boot` = iid resample of the observed months, which keeps
the marginal distribution (fat tails included) and destroys only the order.

| series | window | `n` | mean | median | `t` | skew | exkurt | %pos | **`k`** | nullG p05/p50/p95 | boot p50 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| OP Hi10 VW − VW market | 2014–2024 | 132 | 0.2639 | 0.230 | 1.93 | 0.28 | −0.05 | 56.1 | **5** | 2 / **5** / 10 | 5 |
| " | 2014 → 2026-07 | 151 | 0.1999 | 0.210 | 1.51 | 0.09 | 0.00 | 55.6 | **4** | 1 / **5** / 10 | 5 |
| " | 1963–2013 | 606 | 0.0648 | 0.030 | 0.93 | 0.14 | 2.57 | 51.2 | **3** | 1 / **6** / 14 | 4 |
| " | 1963 → 2026 | 757 | 0.0918 | 0.060 | 1.49 | 0.13 | 2.15 | 52.0 | **6** | 2 / **9** / 19 | 6 |
| OP Hi10 VW − VW own universe | 2014–2024 | 132 | 0.3372 | 0.242 | 2.00 | 0.23 | 0.14 | 55.3 | **5** | 2 / **6** / 10 | 5 |
| OP Hi10−Lo10 VW spread | 2014–2024 | 132 | 0.7380 | 0.480 | 1.65 | 0.16 | −0.01 | 54.5 | **4** | 1 / **5** / 9 | 4 |
| " | 1963–2013 | 606 | 0.1922 | 0.300 | 1.16 | 0.18 | 3.02 | 53.5 | **4** | 1 / **6** / 15 | 5 |
| OP Hi10−Lo10 EW spread | 1963–2013 | 606 | 0.0443 | 0.365 | 0.28 | **−1.60** | **10.33** | 54.8 | **1** | 1 / **4** / 11 | 3 |
| `RMW` published spread | 2014–2024 | 132 | 0.3585 | 0.365 | 1.99 | 0.50 | 0.90 | 59.8 | **4** | 2 / **5** / 10 | 4 |
| " | 1963–2013 | 606 | 0.2681 | 0.235 | 2.94 | −0.46 | **12.80** | 55.9 | **10** | 7 / **15** / 25 | 10 |
| " | 1963 → 2026 | 757 | 0.2571 | 0.260 | 3.10 | −0.24 | 10.39 | 56.3 | **11** | 8 / **18** / 29 | 12 |
| BM Hi10 VW − VW market | 1963–2013 | 606 | 0.4105 | 0.200 | 3.04 | 0.57 | 3.11 | 53.6 | **10** | 7 / **16** / 26 | 11 |
| BM Hi10−Lo10 VW spread | **1926 → 2026** | **1201** | 0.4465 | **−0.010** | 2.42 | **2.33** | **20.48** | 49.9 | **6** | 6 / **17** / 29 | 7 |
| `HML` published spread | 1963–2013 | 606 | 0.3816 | 0.360 | 3.36 | 0.10 | 1.99 | 56.9 | **15** | 9 / **18** / 28 | 15 |
| **CTRL market excess `Mkt-RF`** | 2014–2024 | 132 | 0.9805 | 1.280 | 2.54 | −0.34 | 0.79 | 66.7 | **7** | 3 / **7** / 12 | 7 |
| **CTRL market excess `Mkt-RF`** | **1963–2013** | **606** | 0.5010 | 0.855 | 2.75 | −0.53 | 1.90 | 58.6 | **14** | 6 / **14** / 24 | 14 |
| " | 1963 → 2026 | 757 | 0.5992 | 1.010 | 3.70 | −0.49 | 1.71 | 59.8 | **21** | 11 / **21** / 33 | 21 |
| **CTRL `SMB`** | 1963–2013 | 606 | 0.2796 | 0.085 | 2.26 | 0.36 | 3.64 | 51.7 | **8** | 4 / **11** / 21 | 9 |
| **CTRL `CMA`** | 1963–2013 | 606 | 0.3244 | 0.185 | 3.99 | 0.26 | 1.41 | 54.3 | **18** | 12 / **21** / 32 | 18 |

**Four readings, in order of importance.**

1. **`boot p50` ≈ observed `k` in every single row.** The bootstrap keeps the marginal and throws
   away the order. **So whatever "concentration" `months-to-half` measures lives entirely in the
   marginal distribution of monthly returns, and nothing in the time ordering — which is exactly
   what an order statistic must do.**
2. **The market control lands on its own null median in all three windows (7/7, 14/14, 21/21).**
   `months-to-half` does not distinguish the equity premium from a characteristic premium.
   **The market's 1963–2013 figure is 14 of 606 = 2.31% of months, against `C4`'s 2.27%.**
3. **Where the observation IS below the Gaussian null, kurtosis explains it.** `RMW` in-sample
   10 vs null 15 (exkurt 12.8); the 100-year `BM` spread **6 vs null 17, at the null's 5th
   percentile** (exkurt 20.5, skew 2.33 — 1932–33); the EW OP spread 1 vs null 4 (exkurt 10.3).
   **These are real fat tails and they are a property of the monthly marginal, not of arrival.**
4. **And the profitability long leg — the series this lane exists for — is the one with NO excess
   at all.** Post-pub exkurt **−0.05**; observed `k` = 5 on a null median of 5. **There is nothing
   there to explain.**

**One more statement worth making because it is the opposite of the alarming one.** The 100-year
`BM Hi10−Lo10` spread has **mean +0.4465 and median −0.010**. **The median month of the
century-long value spread loses money.** That is a genuine, symmetric-by-construction statement
about a characteristic premium that no source in §2 reports.

### 3.3 Is the leave-one-year-out collapse remarkable? No — and the test that says so can fire

`C4`'s headline fragility was *drop 2023 and +17.9 becomes +7.2* — a ratio of **0.402**.

**Null (`data/D4_analyze3.py`, `B_calibration_T132`):** iid Gaussian, `T` = 132, 11 years of 12
months, 3,000 draws; the statistic is the **worst** LOO-year mean divided by the full mean.

| `t` | worst-LOO / full: p05 | p50 | p95 | **share of draws < 0.50** | **< 0.40** |
|---|---|---|---|---|---|
| 0.50 | −4.618 | 0.429 | 0.817 | **0.556** | 0.474 |
| 1.00 | −2.068 | 0.574 | 0.845 | **0.423** | 0.347 |
| **1.25** | **−1.477** | **0.629** | **0.859** | **0.357** | **0.283** |
| 1.50 | −0.843 | 0.671 | 0.870 | 0.289 | 0.222 |
| 2.00 | −0.064 | 0.742 | 0.888 | 0.166 | 0.121 |
| 3.00 | 0.589 | 0.829 | 0.915 | 0.027 | 0.015 |

**At `t` = 1.25 over 132 months, 28.3% of pure-noise draws have a worst-LOO mean below 40% of the
full mean.** `C4`'s 0.402 sits at roughly the **28th percentile of the null**. *"Drop one calendar
year and it falls to +7.2 bp"* is **a routine consequence of deleting one-eleventh of a sample
whose `t` is 1.25.**

**And the order-destroying version of the same test, run on the real series, has power.**
`data/D4_series2.json` uses a null that re-orders the *same* returns so calendar years become
random groupings — total and marginal preserved exactly:

| series | window | full mean | worst year | worst-LOO | null p05 / p50 | `p` |
|---|---|---:|---|---:|---|---:|
| OP Hi10 VW − VW market | 2014–2024 | 0.2639 | 2022 | 0.2219 | 0.151 / 0.195 | **0.94** |
| OP Hi10 VW − VW own universe | 2014–2024 | 0.3372 | 2022 | 0.3059 | 0.198 / 0.251 | **0.999** |
| OP Hi10−Lo10 VW spread | 2014–2024 | 0.7380 | 2022 | 0.5257 | 0.379 / 0.512 | 0.58 |
| `RMW` | 2014–2024 | 0.3585 | 2021 | 0.2047 | 0.208 / 0.265 | **0.043** |
| `HML` | 2014–2024 | −0.1795 | 2022 | −0.4433 | −0.458 / −0.345 | 0.071 |
| **`CMA`** | 2014–2024 | −0.0952 | 2022 | −0.3286 | −0.266 / −0.198 | **0.0035** |
| CTRL market excess | 2014–2024 | 0.9805 | 2019 | 0.8642 | 0.674 / 0.786 | 0.95 |

**The profitability long leg is LESS fragile to dropping its worst year than a random reordering
of its own months would be** (`p` = 0.94; the observed drop is −16% where the null's median drop
is −26%). **`RMW` at `p` = 0.043 and `CMA` at `p` = 0.0035 show the test is not inert.** So the
right statement is not "the long leg is fragile" but "**its fragility is exactly average for its
`t`, while `RMW`'s and `CMA`'s are not**."

### 3.4 The scale-free version, which is the one that should have been computed

`months-to-half` divides by the total, so it explodes as the total approaches zero — which is why
`OP Hi10 EW − simple-mean universe` in-sample returns a best-12-month "share" of **3.695** (369%
of the total) and a best-36-month share of **6.163**. **Those numbers are arithmetic artefacts of
a near-zero denominator and must not be reported as concentration.**

The scale-free replacement: **the share of the SUM OF POSITIVE MONTHS carried by the top 10% of
positive months.** It has a fixed denominator, is defined when the mean is negative, and is
comparable across series.

| series | window | positive months | top-3 / Σpos | **top-10% / Σpos** |
|---|---|---:|---:|---:|
| OP Hi10 VW − VW market | 2014–2024 | 74 | 0.122 | **0.266** |
| OP Hi10 VW − VW market | 1963–2013 | 310 | 0.053 | **0.315** |
| OP Hi10−Lo10 VW spread | 2014–2024 | 72 | 0.134 | **0.255** |
| OP Hi10−Lo10 VW spread | 1963–2013 | 324 | 0.056 | **0.321** |
| `RMW` | 2014–2024 | 79 | 0.153 | **0.293** |
| `RMW` | 1963–2013 | 339 | 0.064 | **0.332** |
| `HML` | 1963–2013 | 345 | 0.045 | **0.304** |
| OP Lo10 VW − VW market (short leg) | 1963–2013 | 293 | 0.047 | **0.294** |
| **CTRL market excess** | 2014–2024 | 88 | 0.120 | **0.257** |
| **CTRL market excess** | 1963–2013 | 355 | 0.035 | **0.261** |
| **CTRL `SMB`** | 1963–2013 | 313 | 0.055 | **0.300** |
| **CTRL `CMA`** | 1963–2013 | 329 | 0.042 | **0.278** |

**All 13 series, both windows, fall in 0.243–0.332. The controls are inside the same band as the
characteristic premia.** The full 26-row version is in `data/D4_series2.json`.

**So sub-question 1's distributional half is answered negatively and with controls: there is no
excess concentration of a characteristic premium in the best `k` months once the statistic is made
scale-free.** The apparent concentration in `months-to-half` is the low `t` showing through.

### 3.5 The symmetric trim, which this lane was ordered to carry

`data/D4_table.tsv`. All in %/month. `exTop` / `exBot` drop the top / bottom `⌈1%·n⌉` months;
`trimBoth` drops both; `dropBest3` / `dropWorst3` drop three months from one end.

| series | window | raw | median | exTop | exBot | **trimBoth** | dropBest3 | dropWorst3 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| OP Hi10 VW − VW market | 2014–2024 | 0.2639 | 0.230 | 0.2329 | 0.2934 | **0.2623** | 0.1756 | 0.3423 |
| OP Hi10 VW − VW market | 1963–2013 | 0.0648 | 0.030 | **0.0008** | 0.1235 | **0.0593** | 0.0304 | 0.0985 |
| OP Hi10 VW − VW market | 1963 → 2026 | 0.0918 | 0.060 | 0.0275 | 0.1512 | **0.0869** | 0.0644 | 0.1188 |
| OP Hi10−Lo10 VW spread | 1963–2013 | 0.1922 | 0.300 | 0.0392 | 0.3252 | **0.1719** | 0.1046 | 0.2726 |
| OP Hi10−Lo10 EW spread | 1963–2013 | 0.0443 | **0.365** | −0.0759 | 0.2388 | **0.1193** | −0.0233 | 0.1627 |
| `RMW` | 1963–2013 | 0.2681 | 0.235 | 0.1718 | 0.3667 | **0.2704** | 0.2127 | 0.3299 |
| `HML` | 1963–2013 | 0.3816 | 0.360 | 0.2888 | 0.4762 | **0.3835** | 0.3286 | 0.4343 |
| BM Hi10−Lo10 VW | 1926 → 2026 | 0.4465 | **−0.010** | 0.1134 | 0.6407 | **0.3062** | 0.3058 | 0.5055 |
| **CTRL market excess** | 1963–2013 | 0.5010 | **0.855** | 0.3778 | 0.6627 | **0.5399** | 0.4335 | 0.5971 |

**Three things the symmetric discipline buys.**

1. **The most alarming asymmetric figure in the whole lane is the in-sample long leg's ex-top mean
   of +0.0008 %/month — annihilated — and its symmetric trim is +0.0593 against a raw +0.0648,
   i.e. 91% of the raw mean.** Dropping only winners is a flag, not a verdict, measured on the
   field's own data.
2. **The mean-below-median tell separates the market from the characteristic premia, in the
   direction that matters.** Market excess: mean 0.501 < median 0.855 — **the left tail does the
   work**, as the programme's rule predicts for a long equity book. Profitability long leg and
   spread: mean **above** median in every window — **the right tail does the work.** The one
   exception is the EW spread in-sample (mean 0.044, median 0.365, skew −1.60, exkurt 10.33),
   where a small number of catastrophic months destroy a positive typical month.
3. **`trimBoth` ≈ raw in almost every row.** The trimmed mean is within ~10% of the raw mean for
   the long leg in all three windows, for `RMW` and for `HML`. The exception is the 100-year `BM`
   spread (0.3062 vs 0.4465, a 31% reduction) and the EW OP spread (where the trim *raises* the
   mean from 0.044 to 0.119). **A single reported figure that is alarming in one direction only is
   not a measurement, and the numbers above are what that rule is for.**

---

## 4. WHERE THE STATISTIC SHOULD HAVE BEEN LOOKING: CLUSTERING IN TIME `[MEASURED IN BRIEF]`

`months-to-half` is **order-invariant**. Permuting the months changes it not at all. **So it
cannot, even in principle, detect clustered arrival**, and the fact that the programme's only
arrival number is of that kind means the question has not yet been asked.

### 4.1 The statistic and its null

**Statistic.** The share of the series' total earned in the **best contiguous `w`-month window**.

**Null.** A **permutation** of the same months: total preserved exactly, marginal distribution
preserved exactly, time ordering destroyed. 1,000–4,000 draws. `p` = fraction of permutations
whose best window share is at least as large as the observed one. `data/D4_measure.py`
(`perm_p_rolling`), `data/D4_series2.json`.

**This null is the right one because it cannot be fooled by a low mean, a fat tail, or a skew —
all three are held fixed.**

### 4.2 The result, with the market as the control

| series | window | **best 12 months** | share of total | `p` | **best 36 months** | share | `p` |
|---|---|---|---:|---:|---|---:|---:|
| OP Hi10 VW − VW market | 1963–2013 | **2000-10 → 2001-09** | **0.737** | **0.0030** | 2000-03 → 2003-02 | 0.825 | 0.159 |
| OP Hi10 VW − VW market | 1963 → 2026 | **2000-10 → 2001-09** | **0.417** | **0.0090** | 2000-03 → 2003-02 | 0.466 | 0.252 |
| OP Hi10 VW − VW own universe | 1963–2013 | **2000-10 → 2001-09** | **0.808** | **0.0020** | 2000-04 → 2003-03 | 0.849 | 0.386 |
| OP Hi10−Lo10 VW spread | 1963–2013 | **2000-10 → 2001-09** | **0.708** | **0.0010** | **2000-03 → 2003-02** | **0.998** | **0.0030** |
| OP Hi10−Lo10 VW spread | 1963 → 2026 | 2000-10 → 2001-09 | 0.433 | **0.0010** | 2000-03 → 2003-02 | 0.610 | **0.0060** |
| OP Hi10−Lo10 EW spread | 1963–2013 | 2000-04 → 2001-03 | 2.146† | **0.0010** | 2000-03 → 2003-02 | 3.153† | **0.0030** |
| `RMW` | 1963–2013 | **2000-03 → 2001-02** | **0.303** | **0.0010** | **2000-03 → 2003-02** | **0.524** | **0.0010** |
| `RMW` | 1963 → 2026 | 2000-03 → 2001-02 | 0.253 | **0.0010** | 2000-03 → 2003-02 | 0.438 | **0.0010** |
| `HML` | 1963–2013 | **2000-03 → 2001-02** | **0.251** | **0.0002** | 2000-03 → 2003-02 | 0.326 | **0.0140** |
| **short leg** −(OP Lo10 − mkt) | 1963–2013 | **2000-10 → 2001-09** | **0.694** | **0.0030** | **2000-03 → 2003-02** | **1.087** | **0.0040** |
| BM Hi10 VW − VW market | 1963–2013 | 2000-09 → 2001-08 | 0.180 | 0.185 | 2000-09 → 2003-08 | 0.270 | 0.376 |
| OP Hi10 VW − VW market | 2014–2024 | **2021-11 → 2022-10** | **0.538** | 0.085 | 2021-10 → 2024-09 | 0.675 | 0.505 |
| OP Hi10−Lo10 VW spread | 2014–2024 | 2021-07 → 2022-06 | 0.604 | 0.094 | 2021-10 → 2024-09 | 0.783 | 0.404 |
| `RMW` | 2014–2024 | 2021-02 → 2022-01 | 0.574 | **0.044** | 2021-02 → 2024-01 | 0.840 | 0.134 |
| **CTRL market excess** | **1963–2013** | 2009-03 → 2010-02 | 0.151 | **0.601** | 2009-03 → 2012-02 | 0.246 | **0.718** |
| **CTRL market excess** | 1963 → 2026 | 2020-04 → 2021-03 | 0.115 | **0.330** | 2009-03 → 2012-02 | 0.165 | **0.903** |
| **CTRL market excess** | 2014–2024 | 2020-04 → 2021-03 | 0.404 | 0.105 | 2019-01 → 2021-12 | 0.561 | 0.592 |
| **CTRL `SMB`** | 1963–2013 | 1967-01 → 1967-12 | 0.213 | 0.365 | 1965-07 → 1968-06 | 0.406 | 0.077 |

**† Shares above 1.0 are the near-zero-denominator artefact of §3.4 and I do not read them as
percentages. Their `p`-values are still valid — the permutation null holds the same denominator.**

**Five readings.**

1. **Every characteristic premium I measured is significantly clustered in time in-sample;
   the market's own premium is not.** Characteristic `p`-values: 0.0002 to 0.009. Market:
   0.33–0.90. `SMB`: 0.077–0.365. **The clustering result survives a Bonferroni correction over
   all ~45 tests I ran** (0.05/45 = 0.0011) for `HML` (0.0002), `RMW` (0.0010) and the OP spread
   (0.0010).
2. **It is the same window for everything.** 2000-03 → 2003-02 is the best 36-month window for the
   OP VW spread, the OP EW spread, `RMW`, `HML`, the long leg and the short leg. **Value and
   profitability, long legs and short legs, all peak in one three-year episode.** *That is a
   statement about how few independent episodes the whole body of evidence rests on — and it is the
   external analogue of the programme's own "~10 independent instruments despite 1,573 names".*
3. **The mechanism is visible in the autocorrelation and it is not the market's.** Lag-1
   autocorrelation of monthly returns: OP long leg 0.125–0.145, OP spread 0.152–0.176, `RMW`
   0.148, `HML` 0.158–0.168, `CMA` 0.133 — against market excess **0.041–0.080** and **−0.161**
   post-2013. **Characteristic premia autocorrelate at ~0.15 monthly; the market does not.** *A
   caveat I will not bury: part of a monthly factor autocorrelation of this size can be stale
   prices in the small names inside the sort, which would be a microstructure artefact rather than
   clustered risk premia. I did not separate the two and nothing in §2's six papers does either.*
4. **Post-publication the clustering weakens to insignificance.** 2014–2024: the long leg's best
   12 months are 2021-11 → 2022-10 carrying 53.8% at `p` = 0.085, the spread's 60.4% at
   `p` = 0.094, `RMW`'s 57.4% at `p` = 0.044. **The episode is the 2021-22 rate shock and growth
   unwind, and with only 132 months the test cannot resolve it.**
5. **The 36-month `p`-values are often much weaker than the 12-month ones** (long leg: 0.003 at
   12 months, 0.159 at 36). With `w` = 36 in a 606-month sample there are only ~17 non-overlapping
   windows, so the permutation distribution is wide. **I weight the 12-month test.**

### 4.3 The episode test — and the control that makes it mean something

Drop the clustered window and report what is left. **Then drop the WORST window of the same length,
because a figure alarming in one direction only is not a measurement.** `data/D4_episode.json`.
Control: `n` must fall by exactly the window length — **PASS**.

**In-sample 1963-07 → 2013-12 (606 months):**

| series | full | **excl. 2000-03 → 2003-02 (36 mo)** | window's share | **MIRROR: excl. worst 36 mo** | worst window's share |
|---|---|---|---:|---|---:|
| OP Hi10 VW − VW market | 0.0648 [0.93] | **0.0121 [0.18]** | **0.825** | 0.1054 [1.52] | −0.529 |
| OP Hi10 VW − VW universe TRUE | 0.0561 [0.83] | **0.0107 [0.17]** | 0.820 | 0.0937 [1.35] | −0.572 |
| **OP Hi10−Lo10 VW spread** | 0.1922 [1.16] | **0.0004 [0.00]** | **0.998** | 0.3208 [1.99] | −0.569 |
| `RMW` | 0.2681 [2.94] | **0.1356 [1.75]** | 0.524 | 0.3583 [4.11] | −0.257 |
| `HML` | 0.3816 [3.36] | **0.2735 [2.53]** | 0.326 | 0.4693 [4.08] | −0.157 |
| **CTRL market excess** | 0.5010 [2.75] | **0.6296 [3.43]** | **−0.182** | 0.6368 [3.47] | −0.196 |

**Full 1963-07 → 2026-07 (757 months):** OP long leg 0.0918 [1.49] → **0.0514 [0.87]** excluding
the window (46.6% of total), mirror 0.1252 [2.04]; OP spread 0.2517 [1.61] → **0.1029 [0.70]**
(61.0%), mirror 0.3562 [2.31]; `RMW` 0.2571 [3.10] → **0.1518 [2.06]** (43.8%), mirror 0.3279
[4.09]; `HML` 0.2990 [2.77] → **0.2095 [2.00]** (33.3%), mirror 0.3946 [3.62]; **market 0.5992
[3.70] → 0.7058 [4.33]**.

**Post-publication 2014-01 → 2024-12 (132 months):** OP long leg 0.2639 [1.93] → **0.1343 [1.01]**
excluding 2021-11 → 2022-10 (53.8% of total), mirror excl. worst 12 months 0.3581 [2.61] (worst
window = −23.3%); excluding the best 36 months **0.118 [0.80]** (67.5%), mirror **0.385 [2.24]**
(worst 36 = only **−6.1%**).

**Four readings, and the third is the one I would put in front of a principal.**

1. **The 1963–2013 value-weighted profitability spread is 99.8% one three-year window.** Remove
   2000-03 → 2003-02 and the in-sample spread is **0.0004 %/month at `t` = 0.00**. The long leg is
   82.5% the same window and falls to 0.0121 [0.18].
2. **THE CONTROL IS THE POINT.** In that same window the **market LOST** — the window is −18.2% of
   the market's in-sample total, so excluding it *raises* the market's mean and `t`. **The
   clustered window is not "the good months"; it is a specific cross-sectional dislocation in
   which expensive unprofitable stocks fell.** A generic "good months carry everything" artefact
   would have moved the market control the other way. It did not.
3. **Symmetrically, and this is the honest version: the premium rests on few episodes in BOTH
   directions.** Dropping the worst 36 months raises the in-sample long leg from 0.065 [0.93] to
   0.105 [1.52] and the spread from 0.192 [1.16] to 0.321 [1.99]. **The episode dependence is
   two-sided in-sample (best window +82.5%, worst window −52.9%) — which is the signature of a
   low-`t` estimate, not of a lottery.**
4. **Post-publication the asymmetry is real and it is not symmetric.** The best 36 months carry
   **+67.5%** of the long leg's total while the worst 36 remove only **−6.1%** — an 11:1 ratio,
   against 1.6:1 in-sample. **For the post-2013 long leg specifically, the right tail genuinely
   does dominate**, and that is the one place where the alarming reading survives its own mirror.
   `RMW` post-pub is the same shape: best 36 = +68.8%, worst 36 = −9.0%.
5. **`RMW` and `HML` survive the episode; the OP decile spread and its long leg do not.** `RMW`
   excluding the window is still 0.1518 [2.06] over 757 months. **Whatever is robust in this
   family is in the Fama–French `2×3` construction, not in the decile long leg.**

---

## 5. IS ARRIVAL CLUSTERED AROUND IDENTIFIABLE EVENTS OR REGIMES? WHAT IS DOCUMENTED, AND MY CHECK

### 5.1 Events — the one strong documented result, and it separates the legs

**`Anomalies and News`, Engelberg, McLean & Pontiff** `[WORKING PAPER, 27 July 2017 version]`
`[read in full — 112,857 chars, extracted locally from the author's UCSD page after the fetch
returned raw PDF bytes]`. 97 anomalies, **45,975,693 firm-day observations, 1979:06 → 2013:12.**
Abstract verbatim:

> *"Using a sample of 97 stock return anomalies, we find that anomaly returns are 50% higher on
> corporate news days and are 6 times higher on earnings announcement days."*

**§2.1, the headline number worked through, verbatim:** *"the Net coefficient is 0.384, while the
Net x Earnings Announcement interaction coefficient is 2.164… for a Net value of 10 expected
returns are higher by 3.84 basis points on non-earnings announcement days, and by an additional
21.64 basis points on earnings announcement days… anomaly returns for a Net value of 10 are in
total 25.48 on earnings announcement days, which is 6.3 times higher than anomaly returns on
non-earnings announcement days."*

**§2.2 separates the legs — which three separate literatures in round 3 never did.** Verbatim,
Table 4, 1-day window:

> *"the High Net coefficient is 0.018, while the High Net x Earnings Announcement interaction
> coefficient is 0.139, showing that **long-side anomaly returns are 872% higher on earnings
> announcement days**. The news day interaction is 0.031, showing that **long-side anomaly returns
> are 272% higher on news days**."*
>
> *"the Low Net coefficient is −0.017, while the Low Net x Earnings Announcement interaction
> coefficient is −0.111, showing that **short-side anomaly returns are 753% lower on earnings
> announcement days**. The news day interaction is −0.041, showing that **short-side anomaly
> returns are 341% lower on news days**."*

**So the long leg's event concentration is slightly LARGER in proportional terms than the short
leg's (872% vs 753% on earnings days; 272% vs 341% on news days).** `Figure 1` shows the effect is
asymmetric and **does not reverse**. §2.1 also notes *"most of the information is reflected in
prices the day it is released"* — 3-day windows give smaller coefficients.

**The paper does NOT compute the share of the total anomaly return earned on those days.** `[MY
ARITHMETIC, not the paper's]` At ~4 earnings days a year out of ~252, a 6.3× multiplier implies
those 1.6% of days carry `1.6×6.3 / (1.6×6.3 + 98.4×1)` ≈ **9.3%** of the annual anomaly return —
a real concentration, but an order of magnitude away from "half the premium in three months".
**I flag this as my arithmetic on the paper's coefficient and its day count, not as a published
figure.**

**Draft-versus-published: NOT CHECKED.** This is the **July 2017 working paper**; the published
version is *The Journal of Finance* **73(5), 2018, 1971–2001**. I could not obtain the published
text (§11). **The abstract figures quoted in the RePEc/IDEAS record for the published article match
the working paper's (50% / 6 times), but I did not read the published Table 4 and therefore cannot
certify the 872%/753% split survived refereeing.** Given that one paper's headline sign flipped
between draft and print in this campaign, that is a real gap and it is listed in §11.

**A scope note the programme should read, not act on.** Earnings dates and PEAD are **excluded
ground** from the first campaign. §5.1 is reported because it is the literature's best answer to
"is arrival clustered around identifiable events", **not** as a route to a signal. The
decision-relevant content is negative: the event concentration is ~9% of the annual total, not the
bulk of it.

### 5.2 Regimes — the documented claim, and my check does not confirm it

**`Quality Minus Junk`, Asness, Frazzini & Pedersen** `[WORKING PAPER, draft of 9 October 2013]`
`[read in full — 195,593 chars]`. Table VII, Panel A, **US long sample June 1956 → December 2012,
678 months**, QMJ monthly excess returns:

| period | excess return %/mo | `t` | months |
|---|---:|---:|---:|
| **All periods** | **0.40** | 4.38 | 678 |
| **Recession** (NBER) | **0.76** | 3.48 | **110** |
| **Expansion** | **0.33** | 2.39 | **568** |
| Severe bear market (12-mo market return < −25%) | 0.07 | *(see note)* | 21 |
| Severe bull market (> +25%) | 0.42 | *(see note)* | 135 |
| Low volatility (bottom 30%) | 0.52 | — | 227 |
| High volatility (top 30%) | 0.25 | — | 227 |

*Note: the `t`-statistic columns for the severe bear/bull rows are misaligned in my local text
extraction (the extracted row gives `2.24` as the `t` on an excess return of `0.07` over 21
months, which is arithmetically impossible). **I quote the return levels and the month counts and
refuse to quote those `t`-statistics.***

The authors' own reading, verbatim: *"We find no evidence of compensation for tail risk, if
anything quality appears to hedge (as opposed being correlated to periods) of market distress"*;
and *"The strong return in extreme down markets is consistent with a flight to quality (or at
least profitability)… This mild concavity is mostly driven by the profitability subcomponent of
quality. In fact, the quadratic term is marginally significant (t-statistic of 2.0) for the
profitability factor."*

**Draft-versus-published:** published as *Quality Minus Junk*, **Review of Accounting Studies
24(1), 2019, 34–112**, with an extended sample. **I read the October-2013 draft only.** §11.

**MY INDEPENDENT CHECK, on a different construction.** `data/D4_regime.py`. NBER US contraction
months written out explicitly as `[month after the peak … trough month]` — 8 contractions,
**86 of 757 months (11.4%)** in 1963-07 → 2026-07.

| control | asserts | result |
|---|---|---|
| `C-R1` | the **VW market excess return must be clearly negative** in those months | **−0.6374 %/mo** → **PASS** |
| `C-R2` | recession + expansion months = `n` exactly | **PASS** |
| `C-R3` | **the control must be able to fail**: shift every recession +60 months and `C-R1` must break | wrong dating gives the market **+0.8991 %/mo** in "recessions" → **PASS, the control can fire** |

| series | rec. mean | rec. `t` | exp. mean | exp. `t` | **difference** | **`t`(diff)** | ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| OP Hi10 VW − VW market (long leg) | 0.1366 | 0.65 | 0.0860 | 1.34 | +0.0506 | **0.23** | 1.59 |
| OP Hi10 VW − VW universe TRUE | 0.1045 | 0.49 | 0.0791 | 1.27 | +0.0254 | **0.12** | 1.32 |
| OP Hi10−Lo10 VW (spread) | 0.3971 | 0.81 | 0.2330 | 1.41 | +0.1641 | **0.32** | 1.70 |
| OP Lo10 VW − VW market (short leg) | −0.2605 | −0.68 | −0.1470 | −1.13 | −0.1135 | **−0.28** | 1.77 |
| `RMW` | 0.3747 | 1.55 | 0.2420 | 2.74 | +0.1326 | **0.52** | 1.55 |
| `HML` | 0.2574 | 0.60 | 0.3044 | 2.80 | −0.0469 | **−0.11** | 0.85 |
| **CTRL market excess** | **−0.6374** | −0.87 | +0.7577 | 4.85 | −1.3952 | −1.87 | — |

**The sign and rough magnitude agree with AFP — profitability pays 1.3–1.8× more in recessions —
and the difference is statistically indistinguishable from zero at `t` = 0.12 to 0.52.** `HML`
goes the other way. **86 recession months is not enough to resolve a 5–16 bp/month difference,
and nothing in §2's papers says otherwise.**

**AND THE REGIME STORY IS NOT THE CLUSTERING STORY.** The window that carries the premium
(2000-03 → 2003-02, 36 months) overlaps the 2001 recession (2001-04 → 2001-11) by **8 months**.
**The episode is a valuation unwind, not a contraction** — and the two must not be conflated,
because a recession is at least dated in real time by a committee, whereas the episode is named
only in hindsight.

### 5.3 Ilmanen et al. on macro risk — the negative that matters

**`How Do Factor Premia Vary Over Time? A Century of Evidence`**, Ilmanen, Israel, Lee, Moskowitz,
Thapar `[PEER-REVIEWED — Journal of Investment Management, forthcoming; current draft January
2021]` `[read in full — 178,608 chars]`. Authors are AQR-affiliated; the finding cuts against AQR's
commercial interest, which is why I weight it. Abstract verbatim:

> *"We find little evidence for arbitrage activity influencing returns, though some novel evidence
> of overfitting biases. We identify meaningful time variation in factor risk-adjusted returns that
> appears unrelated to macroeconomic risks, supporting other theories of dynamic return premia."*

§IV.B verbatim: *"we do not find much evidence of factor premia being related to macroeconomic
shocks, but do find some variation in correlations and risk associated with macroeconomic
regimes."*

**Draft-versus-published, and the title AND author list both moved.** The SSRN working paper is
*Factor Premia and Factor Timing: A Century of Evidence* by Ilmanen, Israel, Moskowitz, Thapar
and **Wang**; the JOIM version is *How Do Factor Premia Vary Over Time?* by Ilmanen, Israel,
**Lee**, Moskowitz and Thapar. **A co-author changed between draft and print.** I read the JOIM
version only; the SSRN draft is in §12.

---

## 6. SUB-QUESTION 5 — IS THERE PUBLISHED EVIDENCE THE MONTHS ARE IDENTIFIABLE EX ANTE?

**This is reported as a conflict between two published sources and I do not adjudicate it. The
programme's first campaign permanently excluded regime gates and timing screens as a signal
territory, and nothing here is a proposal.**

### 6.1 The claim that it IS possible

**`Factor Timing`, Haddad, Kozak & Santosh** `[WORKING PAPER — NBER WP 26708, January 2020;
published as *Factor Timing*, Review of Financial Studies 33(5), 2020]` `[read in full]`. Abstract
verbatim: *"Market-neutral equity factors are strongly and robustly predictable. Exploiting this
predictability leads to substantial improvement in portfolio performance relative to static factor
investing."*

Body, verbatim: *"For the two most predictable components, the first and fourth PCs, their own
book-to-market ratios predict future monthly returns with an **out-of-sample R² around 4%**, about
four times larger than that of predicting the aggregate market return… These forecasts yield a
sizable **total out-of-sample monthly R² around 1%**."* And: *"timing expected returns provides
substantial investment gains; **a pure factor timing portfolio achieves a Sharpe ratio of
0.71**."*

**What the paper does not do: cost it.** There is no turnover figure, no break-even trading cost,
and its "out-of-sample" is a **split-half** estimation (*"estimated using only the first half of
the sample"*), not a forward test.

### 6.2 The claim that it is not usable

**Ilmanen et al., §IV.C–D** `[read in full]`, eleven timing signals, six asset classes, a century:

- *"The out-of-sample performance delivers **information ratios of 0.31**, that are orthogonal to
  the underlying static factors. Imposing economic constraints… **0.32**. Using the full in-sample
  regression coefficient estimates for the timing model generates an information ratio of
  **0.89**, which again highlights the dangers of using full sample information."*
- The in-sample upper bound lifts the portfolio Sharpe from **1.48 to 1.73**, with turnover per
  dollar levered up from 4.4 to 5.9, and **break-even cost 7.3 bp per dollar traded.**
- **Out of sample: Sharpe 1.48 → 1.51, optimal timing weight 17.4%, and "The implied break-even
  trading cost from that increase in turnover is 1.8 basis points per dollar traded. Actual
  trading costs at a reasonable size likely exceed this figure."**
- Verbatim conclusion: *"The case for adding factor timing to an already diversified multifactor
  portfolio is tenuous in practice… Accounting for increased turnover and trading costs associated
  with factor timing, the net of cost returns to timing are likely de minimis."*
- And directly on HKS, footnote 23 verbatim: *"We also examine a new timing methodology suggested
  by Haddad, Kozak, and Santosh (2019) applied to our factors and asset classes and to all of our
  timing signals. **The out-of-sample timing results are meager.**"*

### 6.3 Which I would weight, and why — recorded, not adjudicated

**Both stay on the record.** I would weight **Ilmanen et al. for any question about a tradeable
book**, for three stated reasons: (i) it reports a **break-even trading cost** and HKS reports
none; (ii) its out-of-sample is an expanding-window forward estimate while HKS's is a split-half;
(iii) it applied HKS's own method and reports the out-of-sample result as *meager*, which is a
direct test rather than a disagreement of framing. **I would weight HKS for the statistical
question** — that market-neutral factor returns are predictable in-sample by valuation spreads is
established by both papers (Ilmanen: *"Value spreads, business cycle, growth momentum, and CAPE
timing variables are the only ones that seem to improve out-of-sample performance"*).

**Asness's own framing, `[SALES INSTRUMENT — AQR Cliff's Perspective, April 2016] [snippet only]`:**
*The Siren Song of Factor Timing* (also *The Journal of Portfolio Management* 42(5), 2016)
argues factor timing on the factors' own valuations has been *"quite weak historically"* and is
*"too highly correlated to the simple value factor itself."* **I could not read the full text
and do not rely on it.**

### 6.4 The honest answer to the sub-question

**There is published evidence of statistical ex-ante predictability of factor returns (HKS, and
Ilmanen's own in-sample IR 0.89), and the only source that costs it concludes the net return is
de minimis at 1.8–2 bp per dollar traded.** For a programme measuring **33.8 bp/side** on the
names it holds, that is not a close call. **And my own §4 result says something stronger and
simpler: the clustered window is named only in hindsight — I found 2000-03 → 2003-02 by searching
every window in the sample for the maximum, which is the definition of an ex-post fit.**

---

## 7. SUB-QUESTION 6, GONE PAST: DOES CONCENTRATION DIFFER BETWEEN THE LONG LEG AND THE SPREAD?

The slate's conjecture was that a spread's arrival might be **smoother** than its long leg's
because the two legs' bad months offset. **It is wrong, and the measurement says why.**

| question | answer | evidence |
|---|---|---|
| Is the long leg more concentrated than the spread on `months-to-half`? | **No, and neither beats its own null.** Post-pub: long leg `k` = 5 on null median 5; spread `k` = 4 on null median 5. | §3.2 |
| On the scale-free measure? | **No.** Top-10%-of-positive share: long leg 0.266 / 0.315; spread 0.255 / 0.321. | §3.4 |
| Is the spread less clustered in time? | **No — it is MORE clustered.** In-sample best-36-month share: long leg **0.825**, spread **0.998**. Post-pub best-36: long leg 0.675, spread 0.783. | §4.2, §4.3 |
| Do the legs' episodes offset? | **No. THEY COINCIDE.** The short leg's premium, sign-flipped, peaks in the **same** 36 months (2000-03 → 2003-02), carrying **108.7% of its in-sample total at `p` = 0.004**, and in the same best 12 months (2000-10 → 2001-09, 69.4%, `p` = 0.003). | `data/D4_series2.json` |
| So what does a long-only book give up? | **Not smoothness — level.** The legs arrive together, so the spread inherits the long leg's clustering and adds the short leg's on top. What the long-only book gives up is the short leg's contribution in exactly the same months, which post-2013 is the larger half (`C4`: long's share of LS falls from 63% to 19%). | §4.2 + `R3-04` §3.2 |

**And the fourth instance of round 3's organising fact is confirmed for this literature too.**
Of the six papers censused in §2, **not one reports a leg-by-leg arrival statistic**; the only
leg decomposition of any arrival-like quantity anywhere in this lane's sources is
Engelberg–McLean–Pontiff's event interaction (§5.1), which is a *conditional return multiplier*,
not a concentration share. **The concentration literature is the fourth literature that reports
spreads and is silent about long legs — with the single exception of an event study that was not
looking for concentration at all.**

---

## 8. A BENCHMARK CATCH I WAS NOT SENT TO FIND, AND IT FLIPS A SIGN `[MEASURED IN BRIEF]`

**French's OP deciles use NYSE breakpoints.** From the file's own `Number of Firms in Portfolios`
block, 1963-07 → 2026-07:

| decile | first (1963-07) | last (2026-07) | min | max | **mean** | 2014-01 | 2024-12 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `Lo 10` | 178 | 1,022 | 178 (1963-07) | 2,254 (1997-07) | **967.5** | 763 | 1,050 |
| `Hi 10` | 153 | 173 | 145 (1964-07) | 589 (1987-07) | **321.6** | 221 | 179 |

**`Lo 10` holds three times as many firms as `Hi 10` on average and six times as many in 2026.**
Therefore **the simple mean of the ten decile returns is NOT the sort's equal-weighted universe**
— it over-weights the sparse deciles.

Rebuilt exactly from the file's own blocks:
`EW universe = Σ nᵈ rᵈᴱᵂ / Σ nᵈ` and `VW universe = Σ nᵈ sᵈ rᵈⱽᵂ / Σ nᵈ sᵈ` (`sᵈ` from the
`Average Firm Size` block). `data/D4_analyze3.py`, `data/D4_part3.json`.

| window | EW long − **EW universe TRUE** | EW long − simple mean | **the error itself** | VW long − **VW universe TRUE** | VW long − simple mean |
|---|---|---|---|---|---|
| post-pub 2014–2024 | **+0.0342 [`t` 0.20]** | **−0.1013 [−0.87]** | **−0.1355 [−1.57]** | +0.2494 [1.84] | +0.3372 [2.00] |
| post-pub → 2026-07 | −0.0010 [−0.01] | −0.1287 [−1.17] | −0.1276 [−1.50] | +0.1860 [1.42] | +0.2504 [1.55] |
| in-sample 1963–2013 | +0.0330 [0.56] | +0.0063 [0.12] | −0.0267 [−0.84] | +0.0561 [0.83] | +0.0603 [0.78] |
| full 1963 → 2026 | **+0.0262 [+0.45]** | **−0.0207 [−0.45]** | −0.0468 [−1.53] | +0.0820 [1.36] | +0.0982 [1.41] |

**Two sign flips.** Post-2013 the EW long leg's alpha is **−10.1 bp with the naive benchmark and
+3.4 bp with the correct one**; over the full sample **−2.1 bp versus +2.6 bp**. The error is
**13.6 bp/month post-2013**, which is larger than the quantity being measured.

**For value weighting the two benchmarks nearly agree** (VW universe TRUE − VW market = +0.0145
[`t` 1.83] post-pub, i.e. the sort's universe beats the market by 1.5 bp/month), **so the hazard is
specific to equal weighting — which is the programme's own weighting.**

**`C4` made the same assumption.** `R3-04` §3.2 defines its benchmark as *"the sort's own universe
(the simple mean of the sort's five quintile portfolios, which for an equal-count sort is its
equal-weighted universe)"*. **The conditional is the right one; what I cannot check is whether
Chen–Zimmermann's quintiles are equal-count.** If they use NYSE breakpoints — as French's do, and
as CZ does for many signals — the simple mean is not the EW universe and `C4`'s
*"+0.405 [`t` 3.00] against its own universe"* carries a benchmark error of unknown sign.
**This is flagged as a question for `C4`'s construction, not as a refutation of it.** Stated
plainly in §11.

---

## 9. SUB-QUESTION 4 — HOW LONG MUST IT BE HELD? THREE ANSWERS TO ONE QUESTION `[MEASURED IN BRIEF]`

### 9.1 What `(2/IR)²` actually answers, and what it does not

Round 3 computed `(2/IR)²`. **Written out: for an annual information ratio `IR`, `E[t]` after `T`
years is `IR·√T`, so the years until `E[t] = z` is `(z/IR)²`.** Two different questions therefore
have two different horizons:

- **years until you expect statistical significance at `t` = 2: `(2/IR)²`**
- **years until you are 95% sure the REALISED premium is positive: `(1.645/IR)²`** — which is
  `(1.645/2)² = 0.676` times the first.

**So `(2/IR)²` is ~1.5× the horizon needed merely to be confident of a positive realisation. Round
3's arithmetic is correct for the question it asks and is the stricter of the two.** Neither is a
probability statement about the realised path, which is the thing a principal needs.

### 9.2 The measurement, with two non-parametric versions

`data/D4_horizon.py`, `data/D4_horizon.json`. **Overlapping** = the actual fraction of all
overlapping `H`-month windows in the history that summed to < 0 — preserves every bit of
autocorrelation and clustering. **Bootstrap** = 20,000 draws of `H` months with replacement —
destroys clustering, keeps the marginal. Controls `C-H1`: a zero-variance positive-mean series
must give `P(neg)` = 0 (**got 0.0**); a zero-mean series must give ≈0.50 (**got 0.446**); the
overlapping count must equal `n − H + 1` (**got 281 of 281**) → **PASS**.

| series (1963-07 → 2026-07, 757 mo) | mean | `IR` | **`(2/IR)²` yrs** | **95%-sure yrs** | P(neg) 3y | 5y | **10y** | **20y** | 30y |
|---|---:|---:|---:|---:|---|---|---|---|---|
| **OP Hi10 VW − VW market** | 0.0918 | **0.187** | **114.2** | **77.3** | .364/.369 | .331/.338 | **.267**/.276 | **.234**/.201 | .055/.151 |
| OP Hi10 VW − VW universe TRUE | 0.0820 | 0.172 | 135.5 | 91.7 | .366/.380 | .344/.351 | .301/.293 | .253/.223 | .146/.174 |
| **OP Hi10 EW − EW universe TRUE** | 0.0262 | **0.057** | **1,234.6** | **835.1** | .461/.452 | .424/.445 | .458/.427 | .286/.395 | .161/.378 |
| `RMW` published spread | 0.2571 | 0.390 | 26.3 | 17.8 | .202/.240 | .145/.191 | **.096**/.108 | .000/.044 | .000/.017 |
| `HML` published spread | 0.2990 | 0.349 | 32.9 | 22.2 | .302/.275 | .244/.224 | .223/.139 | .122/.061 | .000/.028 |
| BM Hi10 VW − VW market | 0.3697 | 0.350 | 32.7 | 22.2 | .337/.276 | .322/.221 | .223/.132 | .079/.059 | .000/.029 |
| **CTRL market excess `Mkt-RF`** | 0.5992 | 0.465 | **18.5** | **12.5** | .173/.210 | .183/.150 | **.129**/.071 | .000/.021 | .000/.006 |

*Cells are `overlapping / bootstrap`.*

**Five readings.**

1. **The number a principal needs, and nobody publishes it: 26.7% of all actual overlapping
   10-year windows of the profitability long leg against the market were negative, and 23.4% of
   all 20-year windows.** The `RMW` spread's figures are 9.6% and 0.0%; the market's are 12.9% and
   0.0%.
2. **`(2/IR)²` for the EW long leg against its own EW universe is 1,234.6 years, which
   independently reproduces `C3`'s 1,235** — on a different dataset (French's deciles, not the
   programme's fixture), with a *corrected* universe benchmark (§8), and a positive mean rather
   than `C3`'s tilt. **Both arise because an EW long leg against its own EW universe has an `IR`
   of ≈0.057.** That coincidence is worth naming because it suggests the number is a property of
   the comparison, not of either dataset.
3. **Clustering roughly doubles the chance of a bad decade, and that is the gap between the two
   columns.** At `H` = 10 years: market 12.9% overlapping vs 7.1% bootstrap; `HML` 22.3% vs 13.9%;
   `BM Hi10` 22.3% vs 13.2%. **The clustering of §4 is not cosmetic — it is the difference between
   a 7% and a 13% chance of a negative decade.**
4. **At 20 and 30 years the overlapping estimate becomes unusable and I will not hide it.** With
   `H` = 360 there are 398 overlapping windows but only ~2 independent ones, which is why several
   rows read exactly **0.000**. **Those zeros are an `n_eff` artefact, not a guarantee.** The
   bootstrap is the better estimate at long horizons **and it understates, because it destroys the
   clustering that reading 3 shows matters.** The truth is above the bootstrap column.
5. **Against this, the literature.** Fama & French, *Volatility Lessons*, **Financial Analysts
   Journal 74(3), 2018, 42–53** `[PEER-REVIEWED]` `[ABSTRACT / SECONDARY ONLY — I could not obtain
   the full text, see §11]` is the published work that asks the same question with a better method
   (two bootstrap simulations, the second treating the expected premium itself as uncertain). Its
   abstract-level conclusion, quoted through the CFA Institute's own listing: *"for the 3- and
   5-year periods commonly used to evaluate asset allocations, the probabilities of negative
   realized premiums are substantial, and the probabilities are nontrivial for 10- and 20-year
   periods."* **I have NO verified numbers from it and report none.** **My §9.2 measurement is
   therefore not a check on FF; it is an independent measurement of the same quantity whose method
   (treating the sample as the population) corresponds to FF's *first* simulation only, and which
   therefore understates the uncertainty relative to their second.**

### 9.3 MSCI's hit ratio — the only place the statistic appears, and it is marketing

A search summariser reported that MSCI's *Factor Indexing Through the Decades* analyses *"the
frequency of outperformance, or hit ratio, for factor indexes relative to the MSCI World Index…
over rolling periods ranging from one to 20 years."* **I could not obtain the document** — the
`.pdf` URL returned **HTTP 200 with `Content-Type: text/html; charset=utf-8`, 433,311 bytes**, an
SPA landing page whose `<title>` is *"Factor Indexing Through the Decades | MSCI"*. **So the only
figures available to me came from a summariser, which is weaker than `[snippet only]`, and I
report NO numbers from it.** `[SALES INSTRUMENT]` `[UNVERIFIED]` **What is worth recording is the
shape of the finding: the rolling-window hit ratio — the one statistic that directly answers
"how long must it be held" — appears in vendor marketing material and in none of the six
peer-reviewed or working papers I censused.**

---

## 10. SUB-QUESTION 2 — CONCENTRATION IN NAMES: WHAT EXISTS, AND WHY I COULD NOT MEASURE IT

### 10.1 The literature reports it for the MARKET and not for a characteristic sort

**`Do Stocks Outperform Treasury Bills?`, Hendrik Bessembinder** `[PEER-REVIEWED — forthcoming
JFE; the version I read is dated May 2018]` `[read in full — 112,247 chars]`. Verbatim, §1:

> *"the approximately 25,300 companies that issued stocks appearing in the CRSP common stock
> database since 1926 are collectively responsible for lifetime shareholder wealth creation of
> nearly \$35 trillion, measured as of December 2016. However, just five firms (Exxon Mobile,
> Apple, Microsoft, General Electric, and International Business Machines) account for **10% of
> the total wealth creation**. The **90 top-performing companies, slightly more than one-third of
> 1%** of the companies that have listed common stock, collectively account for **over half of the
> wealth creation**. The **1,092 top-performing companies, slightly more than 4% of the total,
> account for all of the net wealth creation.** That is, the remaining 96% of companies … matched
> gains on one-month Treasury bills."*

Also: *"More than half of CRSP common stocks deliver negative lifetime returns"*, and on monthly
returns *"47.8% are larger than the one-month Treasury rate in the same month. In fact, less than
half of monthly CRSP common stock returns are positive."*

**A SUMMARISER CONFLICT, RECORDED.** Two search summarisers told me *"just 86 stocks have
accounted for \$16 trillion in wealth creation, half of the stock market total."* **The May-2018
text I read says 90 companies and nearly \$35 trillion total.** The 86/\$16tn figures are almost
certainly from an **earlier draft with an earlier end date**, which I did not read. **Both are on
the record; I use only the 90/\$35tn figures, because those are the ones I read.** *Twelfth
instance for the summariser tally, and it is a draft-version drift rather than an invention.*

**This is the market, not a characteristic sort.** Bessembinder sorts on *outcome*, not on a
characteristic known ex ante. **It establishes that the name distribution is extremely skewed; it
says nothing about how many names carry a profitability long leg's excess return.**

### 10.2 What the literature says instead, and it is a different statistic

Three searches returned only **segment** concentration, never name-count concentration:

- anomaly returns concentrate in **microcaps** — HXZ's census (*"With microcaps mitigated via NYSE
  breakpoints and value-weighted returns, 65% of the 452 anomalies … cannot clear the single test
  hurdle of the absolute `t`-value of 1.96"*) `[PEER-REVIEWED — RFS 33(5), 2020; I read the NBER
  WP 23394 version in full]`;
- international evidence that EW anomaly portfolios *"are dominated by microcaps with very limited
  investment capacity"* `[snippet only]`;
- anomalies deriving profitability from **distressed, hard-to-trade** stocks `[snippet only]`.

**"Which segment" is not "how many names".** A premium concentrated in microcaps can still be
spread across a thousand of them.

### 10.3 Why I did not measure it, stated rather than omitted

**Name-level concentration is not computable from any free data source I could reach.** French's
library publishes portfolio returns, firm counts and average firm size — **never constituent
returns**. Chen–Zimmermann publish portfolio returns. There is no free CRSP. **Measuring "how many
names carry half a leg's return" requires a per-name return panel, which is precisely the
commercial data this campaign works around.**

**What I can contribute instead, from the firm-count block:** the profitability `Hi 10` decile held
**145–589 firms** over its history and **179 in December 2024**; `Lo 10` held **178–2,254** and
**1,050**. **So the long leg a researcher would trade is a ~180–320 name portfolio, and the short
leg is a ~1,000 name portfolio.** *The asymmetry is a direct consequence of NYSE breakpoints and it
is the same fact that produced §8's sign flip.*

**THE GAP IS THEREFORE EXPLICIT: sub-question 2 is UNANSWERED for a characteristic sort, in the
literature and in this brief.** It is the single largest hole in this lane and §11 says so.

---

## 11. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **I could not reproduce `C4`'s three-of-132 on `C4`'s own data.** I measured French's OP
   **deciles**; `C4` measured Chen–Zimmermann's `GP` **quintiles** with a \$5 price screen. My
   closest analogue (OP `Hi 10` VW − VW market, 2014–2024) gives mean +0.2639 [`t` 1.93] and
   `months-to-half` = 5, not +0.179 [1.25] and 3. **The calibration in §3.1 is run at `C4`'s `t`
   and `T` and is therefore the right comparison, but it is a simulation at their parameters, not
   a re-measurement of their series.**
2. **Whether Chen–Zimmermann's quintile portfolios are equal-count is UNKNOWN to me**, so I cannot
   say whether `C4`'s *"simple mean of the five quintiles = its equal-weighted universe"* is
   correct for their files. §8 shows the assumption fails for French's NYSE-breakpoint deciles by
   13.6 bp/month and flips a sign. **Someone with CZ's portfolio code or firm counts should
   check.**
3. **Fama & French, *Volatility Lessons* (FAJ 74(3), 2018): NOT READ. No numbers taken.** SSRN
   returned **HTTP 403, 5,658 bytes, a Cloudflare "Just a moment…" interstitial** to my urllib
   fetcher; the AlphaArchitect write-up that reproduces its tables returned **HTTP 403 to
   WebFetch (no body) and HTTP 403, 5,780 bytes, to my urllib fetcher** — consistent with a
   user-agent exclusion rather than a substantive block. **The only content I have is an abstract
   quotation via the CFA Institute listing.** My §9.2 measurement is independent of it, not a
   check on it.
4. **The PUBLISHED version of *Anomalies and News* (JF 73(5), 2018) was not read.** I read the
   27 July 2017 working paper in full. The 50%/6× abstract figures appear unchanged in the
   published record; **the 872%/753% long/short split of Table 4 is from the working paper and I
   cannot certify it survived refereeing.**
5. **The PUBLISHED version of *Quality Minus Junk* (Review of Accounting Studies 24(1), 2019) was
   not read.** All QMJ figures in §5.2 are from the 9 October 2013 draft, US sample ending
   December 2012.
6. **The SSRN working-paper version of the Ilmanen et al. paper (*Factor Premia and Factor Timing*)
   was not read**, only the January-2021 JOIM version. The title and one co-author differ between
   them, which is exactly the situation the draft-versus-published rule exists for.
7. **I do not quote the `t`-statistics for QMJ's severe-bear and severe-bull rows.** My
   `pdftotext` extraction misaligns those two rows (it pairs an excess return of 0.07 over 21
   months with a `t` of 2.24, which is impossible). Levels and month counts only.
8. **MSCI's rolling-window hit ratios are UNVERIFIED and no figure from them is reported.** The
   `.pdf` URL served 433,311 bytes of `text/html` (an SPA shell with the right `<title>`).
9. **My regime split uses one NBER dating convention** — `[peak month + 1 … trough month]`, 86 of
   757 months. A peak-inclusive convention would add 8 months and I did not run it. **The
   conclusion (`t`(diff) = 0.12–0.52) is too far from significance for the convention to matter,
   but I did not prove that.**
10. **The monthly autocorrelation of ~0.15 in characteristic premia (§4.2) is not decomposed.** It
    could be clustered risk premia or stale prices in small constituents. **I could not separate
    them from portfolio-level monthly data, and none of the six censused papers does either.**
11. **The overlapping-window `P(negative)` figures at 20 and 30 years have an effective sample of
    ~2–3 independent observations.** The `0.000` cells are not evidence of safety. Stated in §9.2
    reading 4 and repeated here because it is the kind of number that gets quoted without its
    caveat.
12. **The §2 census is a census of WORDS, not of substance.** It establishes that these six papers
    never write "drawdown" or "months to half"; it does **not** prove none of them computes
    something equivalent under another name. The controls caught two probe defects (§2.1) and a
    third may remain. **An unreported statistic is not an absent phenomenon.**
13. **`C4`'s symmetric-trim figures (+16.9 / +14.1 / +20.7) are quoted from `R3-04` and
    `data/C4_robust.json`, not recomputed by me.** I verified the script computes what the
    sentence claims; I did not re-run it.

---

## 12. WHAT I DID NOT OPEN

Separate from §11, which is about things I tried and failed to verify. **This is the visible edge
of the unexplored.**

1. **Jensen, Kelly & Pedersen, *Is There a Replication Crisis in Finance?* (JF 2023), and the
   **jkpfactors.com** global factor dataset.** The most modern factor-return archive, free monthly
   data, 150+ countries. **It is the single best place to re-run every statistic in §3 and §4 on
   hundreds of characteristics at once, and I did not touch it.** *Highest-value omission in this
   lane.*
2. **AQR's free data library** — the *Quality Minus Junk* monthly factor file and *Century of
   Factor Premia* monthly file. Both would extend §4's clustering test to a century and to QMJ
   itself rather than French's OP proxy. Not fetched.
3. **Chen–Zimmermann's portfolio files.** `C4` used them; I used French's. **I did not fetch
   CZ's portfolio returns, so §8's benchmark question about `C4`'s construction is open rather
   than answered.**
4. **Fama & French, *Long-Horizon Returns* (RAPS 8(2), 2018)** — the companion to *Volatility
   Lessons*, about the market's convergence to lognormality. Not fetched; it is about the market,
   not characteristic premia.
5. **Bessembinder's later series** — *Extreme Stock Market Performers* Parts I–III (SSRN 3657604
   etc.) and *Long-Run Stock Market Returns: Probabilities of Big Gains and Post-Event Returns*
   (SSRN 3873010). **Part I is subtitled "Expect Some Drawdowns" and may contain the name-level
   arrival statistic sub-question 2 needs.** Identified and not opened.
6. **The published *Replicating Anomalies* (RFS 33(5), 2020).** I read the 2017 NBER working paper.
   The published version is 114 pages and the appendix tables were not examined.
7. **Engelberg, McLean & Pontiff, *Analysts and Anomalies* (SSRN 2939174)** — the companion paper,
   which per the abstract shows analyst forecasts are too high for anomaly-short stocks and too low
   for anomaly-long stocks. Relevant to why arrival clusters on news. Not opened.
8. **Lochstoer & Tetlock, *What Drives Anomaly Returns?*** (Berkeley WP, later JF) — decomposes
   anomaly returns into cash-flow and discount-rate news, which is the natural mechanism for §4's
   clustering. Not opened.
9. **Savor & Wilson on macro-announcement days**, cited inside *Anomalies and News* as the
   market-level analogue. Not opened.
10. **Keloharju, Linnainmaa & Nyberg, *Return Seasonalities*** — touches month-of-year arrival.
    **Deliberately not opened: calendar effects in returns are excluded ground from the first
    campaign** and `R4-00`'s `D2` scope block is explicit about it.
11. **The *intramonth* arrival literature.** A summariser surfaced a claim that *"the entire
    High−Low return differential was generated in the first six trading days of the month"*
    attributed to a 2026 paper on rebalancing-driven demand. **I did not locate or read it, take no
    figure from it, and note it only as an unexplored and potentially important axis — arrival
    WITHIN the month, which this lane measured only at monthly frequency.**
12. **French's daily portfolio files.** All of §3–§9 is monthly. **The clustering test at daily
    frequency, and the event-day concentration of §5.1 recomputed on published portfolios rather
    than firm-days, are both available for free and were not run.**
13. **A block bootstrap for §9.2.** I ran an iid bootstrap (destroys clustering) and overlapping
    windows (tiny `n_eff`). **A stationary block bootstrap would bridge them** — but block length
    and resampling are excluded ground from the first campaign, so I stopped at naming it.
14. **Research Affiliates' *The Incredible Shrinking Factor Return*** and the Cambridge
    Associates / GMO value-concentration notes. Vendor material, surfaced and not opened.
15. **The 25 Size × OP portfolios.** `C4` used them for the size-segment split. **I did not run
    §4's clustering test segment by segment**, which would answer whether the 2000–2003 episode is
    a small-cap or a large-cap event — **directly relevant to a programme trading small and mid
    caps.** *Second-highest-value omission.*

---

## 13. EVIDENCE FILES

All written to [`data/`](../../../data/) with the `D4_` prefix, per `CLAUDE.md`'s rule that a file
a record quotes is evidence. Raw PDFs and zips stay in session temp.

| file | what it is |
|---|---|
| `D4_fetch.py` | the fetcher: UA `D4-research/1.0 (research@backtest-framework.org)`, 0.6 s pace, logs status / size / content-type / sha1 / first 80 bytes |
| `D4_measure.py` | statistics and nulls: `k_half`, trims, max drawdown, the matched-Gaussian and bootstrap nulls, the rolling-window permutation test, Ljung–Box |
| `D4_run.py` | block readers and **all four data controls** (`C0` self-test, `C2` must-be-zero, `C3` sentinel census, `C4` `RMW` reconstruction) → `D4_controls.json` |
| `D4_defs.py` | the 13 series and 4 windows, shared so both analysis scripts measure the same objects |
| `D4_analyze.py` | the main pass → `D4_series.json`, `D4_t_to_khalf.json`, `D4_table.tsv` |
| `D4_analyze2.py` | LOO nulls, best/worst windows, scale-free shares, firm counts, **reproduction control** → `D4_series2.json` |
| `D4_analyze3.py` | the benchmark catch and the `T`=132 calibration → `D4_part3.json` |
| `D4_census.py` / `D4_census2.py` | the arrival-statistic census, v1 (control fired) and v3 (controls pass) → `D4_census.json`, `D4_census2.json` |
| `D4_horizon.py` | `(z/IR)²`, overlapping-window and bootstrap `P(negative)` → `D4_horizon.json` |
| `D4_regime.py` | the NBER split with its three controls → `D4_regime.json` |
| `D4_episode.py` | the episode test and its symmetric mirror → `D4_episode.json` |

**Every control that ran, and whether it fired:**

| control | fired? | consequence |
|---|---|---|
| `C0` `k_half` self-test on four known answers | no | — |
| `C2` no sentinel or absurd value survives (77,346 checked) | no | — |
| `C3` sentinel census | **informative**: 43 in BE-ME, all in the `<= 0` column, none in any decile | refines round 3's warning |
| `C4` `RMW` reconstructed from 6 ME×OP portfolios | no (max diff 0.005 pp) | proves the right block and columns were read |
| `_E` reproduction across scripts (52 checks) | no (worst diff 0.0) | — |
| §2 census must-be-positive | **FIRED TWICE, on four paper-probe pairs** | the census was rebuilt twice before any result was reported |
| `C-H1` horizon self-test | no | — |
| `C-R1` market must be negative in recessions | no (−0.6374) | — |
| `C-R3` deliberately wrong dating must break `C-R1` | **designed to fire and did** (+0.8991) | proves `C-R1` is capable of failing |
| §3.2 market-excess negative control on `k_half` | **FIRED against the premise**: the market lands on its own null median in all three windows and its 1963–2013 figure is 2.31% of months | the lane's headline |
| §4.2 market-excess permutation control | **discriminated**: `p` = 0.33–0.90 for the market, 0.0002–0.009 for characteristics | the lane's positive finding |
| §4.3 market control on the episode test | **discriminated**: the window is −18.2% of the market's total | the cluster is cross-sectional, not calendar |

**Blocks, logged by tool and response and never by host:**

| tool | response |
|---|---|
| `D4_fetch.py` (urllib, UA above) on `papers.ssrn.com/sol3/papers.cfm?abstract_id=3081101` | **HTTP 403**, 5,658 bytes, `text/html`, body begins `<!DOCTYPE html>…<title>Just a moment...</title>` — a Cloudflare interstitial |
| `WebFetch` on `alphaarchitect.com/2019/02/how-risky-are-the-value-and-size-premiums…` | **HTTP 403 Forbidden**, body not retrieved |
| `D4_fetch.py` on the same URL | **HTTP 403**, 5,780 bytes, `text/html` — consistent with a user-agent exclusion, not a substantive block |
| `D4_fetch.py` on `msci.com/downloads/…/factor-indexing-through-the-decades.pdf` | **HTTP 200**, 433,311 bytes, `Content-Type: text/html; charset=utf-8`, an SPA shell whose `<title>` is the right paper — **the `.pdf`-served-as-`text/html` flavour again** |
| `WebFetch` on `rady.ucsd.edu/…/ANOMALIES_NEWS.pdf` and `mysimon.rochester.edu/…/OSoV.pdf` | returned *"corrupted or improperly rendered PDF"* prose — **not blocks; the bytes landed on disk and both extracted cleanly with `pdftotext`, 112,857 and ~105,000 chars** |

---

## 14. WHAT THIS BRIEF DOES NOT CLAIM

**It does not claim a timing rule, and it does not propose one.** §6 reports a published conflict
and closes on the negative side of it; regime gates and timing screens remain excluded ground.

**It does not claim `C4` was wrong.** `C4`'s numbers reproduce from its own artifact and its
sentence quotes the right one of the two statistics its script computes. **What this lane claims is
that the statistic does not mean what it appears to mean**, and it supplies the null that says so.

**It does not claim the literature is wrong to omit arrival statistics** — only that it does omit
them, censused on six full texts with controls that fired twice before passing.

**It does not resolve sub-question 2.** Name-level concentration for a characteristic sort is
unmeasured here and, as far as four searches can establish, unpublished.

**Nothing is elevated out of `docs/research/`. Both books are unchanged. Nothing is closed and
nothing is admitted.**
