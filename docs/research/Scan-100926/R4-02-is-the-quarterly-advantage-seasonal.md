# `D2` — Is round 3's quarterly advantage a fiscal-calendar artefact?

**Round 4, lane `D2`.** Campaign contract: [`00-SCHEMA.md`](00-SCHEMA.md). Slate:
[`R4-00-slate.md`](R4-00-slate.md). Upstream finding under test: [`R3-01`](R3-01-the-quarterly-variant-and-the-lag.md) §8.1.

**EXTERNAL LITERATURE AND PUBLIC DATA ONLY.** This lane has no access to the programme's
fixture and makes **no claim of any kind about it**. Nothing here is elevated out of
`docs/research/`. Nothing is closed and nothing is admitted.

---

## 0. THE ANSWER, AND IT IS NOT THE ONE THE LANE WAS SENT TO CONFIRM

**The seasonal-artefact hypothesis is NOT supported, and the reason is better than "no
evidence": the decisive comparison now exists and I made it.** But the hypothesis is not
refuted either, because **the single-quarter construction IS measurably contaminated by
fiscal-quarter phase — it just is not the source of its edge.** Seven findings, the
negatives first.

1. **`[MEASURED IN BRIEF]` THE SINGLE-QUARTER ADVANTAGE SURVIVES A SEASONALITY-FREE
   CONSTRUCTION WITH DATA FRESHNESS HELD CONSTANT — SO IT IS NOT A SEASONAL ARTEFACT, AND
   IT IS NOT STALENESS EITHER.** Jensen–Kelly–Pedersen ship both the trailing-four-quarter
   and the single-quarter form of net-income-to-book-equity, **both refreshed quarterly off
   the same filing**, so only the numerator window differs. On 701 matched US months,
   **α of the single-quarter form against the trailing-four-quarter form is `+0.130` %/mo
   [NW6 `+3.26`]; the reverse α is `−0.075` [`−1.54`]** — the same asymmetry Novy-Marx's
   Table A6 reports for annual-vs-quarterly (`−0.03` [`−0.23`] / `+0.42` [`3.10`]), but now
   with freshness matched. It holds in 2010–2024: `+0.102` [`+2.24`]. §5.1.
2. **BUT THE SAME MEASUREMENT SAYS THE SEASONALITY-FREE FORM GIVES UP 28% OF THE MEAN,
   SIGNIFICANTLY.** Matched 686 months: trailing-four-quarter **`0.245` %/mo [t `2.19`,
   NW6 `1.98`]** against single-quarter **`0.338` [`3.30`, NW6 `2.92`]**; the difference is
   **`+0.094` %/mo [t `2.24`, NW6 `2.55`]**. So round 3's headline is **not destroyed and
   not reproduced at magnitude** under the only seasonality-free construction. §5.1.
3. **`[MEASURED IN BRIEF]` THE CONTAMINATION IS REAL AND I MEASURED IT DIRECTLY — WITHIN
   FIRM, WHERE INDUSTRY AND FISCAL-YEAR-END ARE CONSTANT BY CONSTRUCTION.** For 613 US
   filers, the **single-quarter** gross-profitability rank shows a fiscal-quarter-phase
   R² of **`+0.0129` in excess of its own AR(1) surrogate null (14.0% of firms significant)**
   while the **trailing-four-quarter** rank shows **`−0.0682` (1.0% of firms significant,
   against a nominal 5%)**. **Paired difference `+0.0700`, Wilcoxon `p = 1.3e−38`.** The
   single-quarter construction moves a firm **1.41× as far** around the cross-section
   quarter to quarter. **In retail the paired excess is `+0.1678` and the ratio `1.55×`.** §6.3.
4. **SO THE HONEST RECONCILIATION: SEASONALITY IS NOISE IN THE SINGLE-QUARTER SORT, NOT ITS
   SIGNAL — AND THE LITERATURE SAYS THE SAME THING, IN A PASSAGE ROUND 3 HAD ONLY HALF OF.**
   Hou–Xue–Zhang report **both** forms on one sample: *"Sorting on the four-quarter-change
   in return on equity (dRoe) yields a high-minus-low average return of 0.76% per month
   (t = 5.43) at the 1-month horizon, and is slightly higher than that from sorting on Roe,
   **0.69% (t = 3.07)**."* **[read in full]** — the seasonality-controlled version is
   *stronger*, not weaker. My JKP panel independently agrees in direction: the
   four-quarter seasonal difference `niq_be_chg1` earns IR_ann `0.50` against `niq_be`'s
   `0.44`, α `+0.152` [`+2.10`]. §4.3, §5.1.
5. **THE BAR, FOR GROSS PROFITABILITY SPECIFICALLY: `[MEASURED IN BRIEF]` A
   SEASONALITY-ROBUST QUARTERLY GROSS-PROFITABILITY SORT EARNS `0.377` %/mo [t `2.25`,
   NW6 `1.98`] IN 2010–2024 AND `0.303` [`3.95`, NW6 `3.64`] OVER 890 MONTHS.** JKP's
   `gp_at` *is* a trailing-four-quarter, quarterly-refreshed gross-profitability sort — it
   had simply never been labelled as the answer to this question. §5.3.
6. **AND THE THING THAT ACTUALLY MOVES THIS FAMILY IS NOT SEASONALITY, IT IS THE DEFLATOR
   TIMING — BY MORE.** Same library, same sample: `gp_at` (current assets, Novy-Marx's
   deflator) `0.292` [t `2.92`] in 1963–2010 versus `gp_atl1` (**one-quarter-lagged**
   assets, the HXZ/OSAP deflator) **`0.163` [t `1.43`] — insignificant.** The choice round 3
   measured as costing 8–14% of the computable cross-section also costs **roughly half the
   `t`**. §5.3. **This is a bigger finding than the one I was sent for.**
7. **NOBODY HAS CHECKED, AND NOW THE GAP IS QUANTIFIED RATHER THAN ASSERTED.** Across Chen
   & Zimmermann's **331** signals the strings `trailing`, `year-over-year` and `same
   quarter` return **ZERO rows**; all **26** `_q` signals are `Cat.Signal = Placebo`; the
   **13** `season` hits are **all momentum/dividend return-seasonality** (excluded ground)
   and **none** concerns an accounting input. JKP's 55-page documentation mentions
   seasonality **12 times, all Heston–Sadka return seasonality, zero about the accounting
   variable** — while silently solving it in code. §4.2, §4.4.

**The precise negative I would put above all of it:** *a single-quarter sort is an
unadjusted seasonal sort* is **true as stated and does not carry the conclusion it looks
like it carries.** The contamination exists (§6.3), is concentrated in retail and
wholesale (§6.2–§6.3), and compounds with a non-December fiscal-year-end distribution that
is **3.2× more industry-dependent than chance** (§6.2) — **but in the two places anyone has
measured returns on both sides, removing the seasonality makes the signal STRONGER, not
weaker.** Round 3's headline should be marked **provisional on the deflator, not on the
season.**

---

## 1. HARD SCOPE, AND THE ONE EXCEPTION I INVOKED

This lane is about **seasonality in the accounting input being sorted on**. Calendar
effects in returns, turn-of-month, day-of-week, FOMC, holiday effects, sell-in-May,
January and **seasonal momentum** are **excluded ground inherited from the first
campaign** and I did not research them.

**Where I touched the boundary, and it is flagged rather than buried:**

- **Invoked once, for Chang–Hartzmark–Solomon–Soltes** (§4.5). I use that paper **only**
  for its documentation that seasonality in the *accounting variable* is large, persistent
  and rankable. **I do not use, cite or rely on its return result**, which is a calendar
  effect in returns and is excluded. Its Borders return figures (`2.27%` vs `−3.40%`) are
  **deliberately not carried into any finding here.**
- **Refused.** JKP's `%macro seasonality` and their `seas_*` factors, and OSAP's
  `MomSeason*` / `MomOffSeason*` / `DivSeason` families, are **Heston–Sadka return
  seasonality and seasonal momentum**. I counted them (to establish the *negative* that
  the word "season" in these libraries never means the accounting input) and **read no
  further into them**. The bug-fix entries in JKP's changelog about `seas_11_15an` are
  likewise noted as out of scope, not used.
- **Not pursued.** `Business seasonality and stock liquidity` (JFM 67, 2024) was located
  and **not opened**: its dependent variable is liquidity, and its in-scope half — a
  sales-seasonality measure — I ended up measuring myself instead (§6.2). §9 item 3.

---

## 2. SOURCES — BY TYPE, AND SEPARATELY BY HOW WELL ESTABLISHED

| # | source | type | established |
|---|---|---|---|
| `J1` | **Jensen, Kelly & Pedersen**, `GlobalFactors/accounting_chars.sas` + `char_macros.sas` + `project_macros.sas` from `bkelly-lab/ReplicationCrisis` (48,176 + 25,078 + 52,014 B, HTTP 200 `text/plain`) | [SOFTWARE DOC] — **the item `R3-01` §11 called "the most valuable unopened item on the list"** | **[read in full]** of the quarterization/TTM block (lines 262–280, 470–540) and `%combine_ann_qtr_chars` (1219–1245), quoted verbatim in §4.1 |
| `J2` | **The same project's documentation LaTeX SOURCE**, `bkelly-lab/jkp-data/documentation/documentation.tex`, 187,690 B | [PRIMARY DATA DOC] | **[read in full]** for §§ on annualized variables from quarterly data and the characteristic definition tables; all 12 `season` occurrences enumerated by me |
| `J3` | **JKP `CHANGELOG.md`** (ReplicationCrisis), 9,482 B | [PRIMARY DATA DOC] | **[read in full]** of the 2021-01-25 and 2021-03-01 entries; the `0.12 → 0.05` figure in §4.3 is transcribed by me from it |
| `J4` | **JKP's US FACTOR RETURN PANEL**, `jkp-data/documentation/sas_to_python/data/US_factors_SAS.parquet`, 1,578,145 B, magic `PAR1` — **144,620 rows, 153 characteristics, `usa`/`monthly`/`vw_cap`, 1926-01 → 2024-12** | [PRIMARY DATA] | **[read in full]**; every number in §5 is **`[MEASURED IN BRIEF]`** by me from it |
| `H1` | **Hou, Xue & Zhang**, *Replicating Anomalies*, **NBER w23394 (May 2017)**, 130 pp, 821,858 B, `nber.org`, **title line checked** | [WORKING PAPER] | **[read in full]** of the `dRoe`/seasonality passage and Appendix A.4.11; **tables did not survive extraction — see §8 item 2** |
| `C1` | **Chen & Zimmermann**, `SignalDoc.csv`, 331 rows × 29 cols, at `data/D3_SignalDoc.csv` (fetched by lane `D3` of this round; shared evidence) | [PRIMARY DATA DOC] | **[read in full]**; whole-file string censuses in §4.2 computed by me |
| `C2` | **The same project's CODE**: `Signals/pyCode/Placebos/ChangeRoA.py`, `ChangeRoE.py`, `Predictors/roaq.py` | [SOFTWARE DOC] | **[read in full]**; §4.2 records **the code contradicting its own documentation, twice** |
| `L1` | **Jegadeesh & Livnat**, *Revenue Surprises and Stock Returns* (JAE 41, 2006), the **authors' own submitted manuscript** at `pages.stern.nyu.edu/~jlivnat/`, 47 pp, 995,561 B, **title line checked** | [PEER-REVIEWED, author manuscript] | **[read in full]** of §2's expectation model; all 9 `season` occurrences enumerated |
| `S1` | **17 CFR 229.101 (Reg S-K Item 101)**, eCFR API, `text/xml`, 17,659 B | [PRIMARY REGULATORY] | **[read in full]** for the seasonality clause, quoted verbatim in §4.1 |
| `X1` | **Chang, Hartzmark, Solomon & Soltes**, *Being Surprised by the Unsurprising*, Oct 2014 draft, 57 pp, 770,925 B, `econ.yale.edu`, **title line checked** | [WORKING PAPER] | **[read in full]** of §3.2's measure construction **FOR THE IN-SCOPE HALF ONLY** — see §1 |
| `M1` | **My own SEC FSDS measurement** — 13 quarterly zips **2021q4–2024q4, 1,465,690,535 bytes**, sha1s logged; 685,444 retained facts | `[MEASURED IN BRIEF]` | scripts/results `data/D2_*`; controls in §6.1 |

**Inherited, not re-established.** `R3-01`'s transcriptions of Novy-Marx (2013) Table A6
and HXZ Table 4 (the `0.16 → 0.51` and `0.20 → 0.72` figures, and the `−0.03 [−0.23]` /
`+0.42 [3.10]` spanning pair) are **quoted from `R3-01`, not re-verified by me** — see §8
item 2 for why I could not re-verify them and §7 for what that does to the record.

**Interested parties, named.** `J1`–`J4`'s second author is at AQR. No asset-manager
publication is cited for any return here. A Dimensional insights page and an S&P Global
"Quantamental Research" note surfaced on these searches and are **[SALES INSTRUMENT]**;
neither is cited.

---

## 3. THE SUMMARISER RULE, APPLIED

Three search summarisers produced statements I did **not** carry into this brief without
independent verification, and one of them would have been a load-bearing error:

1. A summariser stated Akbas–Jiang–Koch's model *"includes quarterly seasonal dummies"*.
   **I never opened that paper** (§9 item 1) and the claim appears in this brief **only**
   as an explicitly-unverified second-hand restatement inherited from `R3-01` §8.1, which
   already flagged it as *weaker than `[snippet only]`*. **It supports no finding here.**
2. A summariser asserted *"the level of profitability is defined as trailing four-quarter
   profits, scaled by latest-quarter book equity"* **with no attribution**. I could not
   locate the source of that sentence and **it supports nothing here.** Had I trusted it,
   I would have reported that a TTM quarterly profitability level already exists in the
   literature — which §4.2's census says it does not.
3. A summariser asserted Reg S-K Item 101(c)(1)(v) requires seasonality disclosure.
   **Verified against the eCFR primary source instead** (§4.1) — and it was right, but
   the verification cost one fetch and the rule is the rule.

---

## 4. `Q1`–`Q4` — WHAT THE LITERATURE AND THE CODE ACTUALLY SAY

### 4.1 `Q2` first, because it is the cleanest: what do the standard constructions DO?

**Five constructions exist. Only one is seasonality-free, and its author's stated reason
is not seasonality.**

| construction | who | their own words | seasonality-free? |
|---|---|---|---|
| **raw single fiscal quarter** | Novy-Marx (2013) `PMU_hf`; HXZ `Gla_q`/`Ola_q`; OSAP `GPlag_q`, `roaq`; JKP `niq_at`, `niq_be` | HXZ A.4.11, **[read in full]**: *"`Gla_q`, is quarterly total revenue (Compustat quarterly item REVTQ) minus cost of goods sold (item COGSQ) divided by one-quarter-lagged total assets (item ATQ)"* | **NO** |
| **trailing four quarters** | **JKP only** | `J2`, **[read in full]**: *"In the annual data, it is calculated over one year. However, in the quarterly data, it is calculated over one quarter. **To make quarterly income and cash flows items comparable to the corresponding annual item, we take the sum of the item over the last four quarters.**"* | **YES** |
| **four-quarter (seasonal) difference** | HXZ `dRoe`; OSAP `ChangeRoA`/`ChangeRoE`; JKP `niq_at_chg1`, `niq_be_chg1`, `ocf_at_chg1` | HXZ, **[read in full]**: *"**The four-quarter-change in Roe controls for seasonality**, and likely better captures the underlying economic profitability than Roe itself."* | **YES** (but it is a *change*, not a level — §7) |
| **year-over-year ratio** | JKP `saleq_gr1` = `SALE_QTR_t / SALE_QTR_{t−12} − 1` | `J2` definition table, **[read in full]** | **YES** |
| **seasonal random walk** | Jegadeesh & Livnat (2006) for the *surprise*, adopted by JKP in 2021 | `L1`, **[read in full]**: `E(Q_{i,t}) = Q_{i,t−4} + ∂_{i,t}` | **YES** |
| **nothing at all** | Ball–Gerakos–Linnainmaa–Nikolaev; Fama–French; Novy-Marx & Medhat (2025) | `R3-01` §8.1 measured `season` = **0** in all three | n/a — annual |

**THE FINDING UNDER THIS TABLE.** **JKP's reason for the only seasonality-free
construction is COMPARABILITY ACROSS FREQUENCY, not seasonality.** The word never appears
in that context in their 55 pages. **The seasonality-freeness of the field's one clean
construction is an unintended by-product of a data-plumbing decision** — which is why
nobody reports it as the answer to this question, and why `R3-01` was right that the
literature *"never says so"*.

**AND THE CODE SAYS MORE THAN THE PROSE — this is the `R3-01` hazard, confirmed again.**
`J1`, verbatim:

```sas
%macro ttm(var); (&var + lag1(&var) + lag2(&var) + lag3(&var)) %mend;
/* Note that ttm will return missing if either of the lags are missing.
   This is the behavior we want. */
...
&var_yrl_name. = %ttm(&var_yrl.);
if (gvkey^=lag3(gvkey) or fyr^=lag3(fyr) or curcdq^=lag3(curcdq)
    or %ttm(fqtr)^=10) then &var_yrl_name. = .;
if missing(&var_yrl_name.) and fqtr=4 then
    &var_yrl_name. = &var_yrl_name.y;  * If financial quarter is 4, the ytd variable is yearly;
```

**`%ttm(fqtr)^=10` is a SEASONAL-COMPLETENESS ASSERTION that appears nowhere in the
documentation.** `1+2+3+4 = 10`: the four quarters summed must be one of each fiscal
quarter, or the TTM value is set missing. On sorted consecutive firm-quarter data this is
an effective check — though, stated precisely, **it is necessary and not logically
sufficient** (`{1,1,4,4}` and `{2,2,3,3}` also sum to 10; they cannot arise from a
contiguous cycle, but a pathological gap pattern is not formally excluded). **The
guarantee that JKP's quarterly profitability is seasonality-free lives in one SAS
conditional, not in any paper.**

`%combine_ann_qtr_chars` then determines which version ships, verbatim:

```sas
/* Substitute Annual Characteristic for Quarterly if Quarterly is more recent */
if missing(&ann_var.) or (not missing(&qtr_var.) and datadate&q_suffix. > datadate) then
    &ann_var. = &qtr_var.;
...
drop datadate datadate&q_suffix.; /* We can no longer be sure which items accounting dates refer to */
```

**So every JKP profitability characteristic is a HYBRID** — annual unless a
trailing-four-quarter quarterly value is more recent — **and JKP themselves record in a
code comment that the resulting characteristic has no well-defined as-of date.** That
matters for §5: it is why `gp_at` starts in 1950 (annual data) but is quarterly-refreshed
TTM in the modern era.

**`Q1`'s institutional anchor, primary source.** 17 CFR 229.101 Item 101(c)(1)(v),
verbatim from eCFR: *"**The extent to which the business is or may be seasonal.**"*
Seasonality is a **mandated disclosure topic** in US filings where material — so the
phenomenon is recognised as material by the regulator, and a filing-text route to
identifying seasonal firms exists.

### 4.2 `Q2`/`Q3` — the census, and a reference library contradicting itself twice

**`[MEASURED IN BRIEF]` on `C1` (331 signals, 29 columns), whole-file string census:**

| string | rows | what they are |
|---|---|---|
| `trailing` | **0** | — |
| `year-over-year` | **0** | — |
| `same quarter` | **0** | — |
| `four quarter` / `four-quarter` | 4 / 1 | `ChangeRoA`, `ChangeRoE`, `FailureProbability`, `FailureProbabilityJune`, `WW_Q` |
| `season` | **13** | `MomSeason*` (7), `MomOffSeason*` (4), `DivSeason`, `DivYieldST` — **every one a RETURN seasonality or seasonal-momentum signal. ZERO concern an accounting input.** |
| **negative control** `zzzz_not_a_string_d2` | **0** | as required |

**All 26 signals whose name ends `_q` are `Cat.Signal = Placebo`, `Predictability in OP =
indirect`, `Evidence Summary = HXZ variant`** — confirming `R3-01`'s finding independently
and extending it from four profitability rows to the whole family. **There is no
trailing-four-quarter construction anywhere in OSAP.** The only gross-profit rows are
`GP`, `GPlag`, `GPlag_q`.

**OSAP's own reported figures** (transcriptions of each original paper's headline test,
**not** OSAP's replication):

| signal | construction | `Cat.Signal` | Return | `t` | weight / quantile / sample |
|---|---|---|---|---|---|
| `GP` | annual gross profits / assets | Predictor | `0.31` | **`2.49`** | VW, quintile, 1963–2010 |
| `GPlag_q` | **single fiscal quarter** / lagged assets | **Placebo** | — | — | no statistic published |
| `roaq` | **single fiscal quarter** `ibq` / lagged `atq` | Predictor | `0.8417` | **`6.45`** | EW, decile, 1976–2005 |
| `ChangeRoA` / `ChangeRoE` | **four-quarter seasonal difference** | **Placebo** | — | — | **no statistic published** |

**THE HAZARD FIRED. OSAP'S DOCUMENTATION MISSTATES BOTH OF ITS SEASONALLY-DIFFERENCED
PROFITABILITY VARIANTS, AND THE CODE IS RIGHT.** `SignalDoc.csv`'s `Detailed Definition`
says `ChangeRoA` is *"Quarterly return on assets (**rdq/atq**) minus its value four
quarters ago"* and `ChangeRoE` is *"Quarterly return on equity (**ceqq/atq**) minus its
value four quarters ago"*. The code (`C2`, **[read in full]**) computes:

```python
# ChangeRoA.py          .otherwise(pl.col('ibq') / pl.col('atq')).alias('tempRoa')
# gen ChangeRoA = tempRoa - l12.tempRoa
# ChangeRoE.py          .otherwise(pl.col('ibq') / pl.col('ceqq')).alias('tempRoe')
# gen ChangeRoE = tempRoe - l12.tempRoe
```

`rdq` (R&D) is not the numerator — `ibq` is. And `ceqq/atq` is equity-to-assets, not ROE
— the code uses `ibq/ceqq`. **This is the third instance in this campaign of a reference
implementation's code contradicting its own prose with the code correct.**

**A second, subtler construction inconsistency inside the same library:** `roaq` (the
level) divides by **3-month-lagged** `atq` (its own header: *"Quarterly return on assets
as quarterly income (ibq) divided by 3-month lagged quarterly assets (atq)"*), while
`ChangeRoA` divides by **contemporaneous** `atq`. **So OSAP's seasonal difference is not
the seasonal difference of OSAP's level.** That is a construction node, and it belongs in
lane `D1`'s territory as much as mine.

**OSAP's own complaint, verbatim from `SignalDoc.csv`'s `Notes` on both rows:** *"HXZ do
not cite anyone for this 'replication.'"*

### 4.3 `Q3`'s sharpest answer, and it is a published number nobody has connected to this question

**`J3`, JKP's CHANGELOG, 2021-01-25, verbatim — a documented BUG FIX that consisted
precisely of switching a quarterly accounting characteristic from a NON-SEASONAL to a
SEASONAL base:**

> *"Standardized unexpected earnings (niq_su) and sales (saleq_su) is computed as the
> actual value minus the expected value… Before, the expected value was computed as the
> mean yearly change over the last 8 quarters added to **the last quarterly value**. Now
> the expected value is the same mean yearly change, but added to **the quarterly value 4
> quarters ago** consistent with Jegadeesh and Livnat (2006)."*

and, in the same entry's `__Impact__` block, **the measurement:**

> *"The standardized unexpected **sales** (saleq_su) variable went from a significant IR
> of **0.12** to an insignificant IR of **0.05**. This explains the drop in the
> replication rate. On the other hand, **niq_su increased from 0.11 to 0.19**."*

**This is a with-and-without seasonal-adjustment comparison on one library, one sample,
one construction pipeline, for a REVENUE-based quarterly characteristic — and the
revenue one LOST MORE THAN HALF ITS INFORMATION RATIO AND ITS SIGNIFICANCE when the
seasonal base was imposed.** Revenue is the numerator of gross profitability. Read the
other way round — which is how JKP read it — the `0.12` was **partly a seasonality
artefact**, and correcting it cost `0.07` of IR.

**The direction is opposite for earnings (`0.11 → 0.19`).** Both directions are on the
record; I adjudicate neither. The same split appears in my own measurement (§5.1) and in
HXZ (§4.3 below), so it is a stable feature of this literature rather than one library's
quirk.

**`L1`'s model, verbatim, which JKP adopted** — `E(Q_{i,t}) = Q_{i,t−4} + ∂_{i,t}` with
`∂` the mean of the eight most recent four-quarter differences; and they apply it to
revenue too: *"We follow a similar procedure to measure revenue surprises… we also assume
that [REV] also follows a seasonal random walk."* Their stated justification: *"Freeman
and Tse (1989) and others find that announcement date returns are more highly correlated
with forecast errors from a seasonal random walk model than with the forecast errors from
a AR(1) model."* **And their own caveat, footnote 2, verbatim:** *"it is unlikely that a
seasonal random walk model is the most appropriate model for the time series behavior of
REV for all firms. If this model is misspecified, SURGE will measure revenue surprises
with error."*

**So `Q3`'s answer is: YES, the characteristic-sorting literature does borrow the seasonal
random walk from the earnings-expectations literature — but only for SURPRISE variables,
never for a profitability LEVEL.** No source in anything I read seasonally adjusts a
profitability *level* before sorting on it. A targeted search for `X-12` / seasonal
adjustment applied to an accounting characteristic returned nothing on point.

**HXZ's passage, now read in full rather than in part.** `R3-01` §8.1 had the
interpretation sentence; **the sentence before it carries the comparison number and is
what makes it evidence:**

> *"Sorting on the four-quarter-change in return on equity (dRoe) yields a high-minus-low
> average return of 0.76% per month (t = 5.43) at the 1-month horizon, **and is slightly
> higher than that from sorting on Roe, 0.69% (t = 3.07)**. The q-factor alpha for the
> high-minus-low dRoe decile is 0.34% (t = 2.29)… We interpret the evidence as indicating
> earnings seasonality. The four-quarter-change in Roe controls for seasonality, and
> likely better captures the underlying economic profitability than Roe itself."*

**Unadjusted single-quarter level: `0.69` [`3.07`]. Seasonality-controlled: `0.76`
[`5.43`].** One sample, 1-month horizon, VW deciles, NYSE breakpoints, Jan 1967–Dec 2014.
**The authors name seasonality as the mechanism and the adjustment makes the signal
STRONGER.** That is the single most important number in the published literature for this
lane, and it points the opposite way to the artefact hypothesis.

### 4.4 `Q2`'s remaining negative — JKP's documentation never mentions the problem it solved

**`[MEASURED IN BRIEF]` on `J2` (187,690 B of LaTeX):** `season` appears **12 times**.
Enumerated: **1** is the changelog line about a bug in the `seas_*` return-seasonality
screen, and **11** are the `seas_{1_1,2_5,6_10,11_15,16_20}{an,na}` Heston–Sadka
**return**-seasonality characteristic definitions and their cluster heading.
**ZERO refer to seasonality in an accounting variable.** The library that solves the
problem, solves it silently — exactly as `R3-01` suspected, now verified on the
documentation source rather than the PDF.

### 4.5 `Q1` — how large is it, per the literature? (the bounded exception, §1)

`X1` **[read in full]**, used for the accounting variable only:

- **A named extreme case:** *"Out of Borders' 63 quarterly earnings announcements, the 14
  largest were all 4th quarter earnings."* And: *"Earnings seasonality is a persistent
  property of the firm's business."*
- **Their measure `EarnRank`:** rank a firm's 20 quarterly EPS over five years; take the
  average rank of the same fiscal quarter in years `t−4, t−8, t−12, t−16, t−20`. Median
  `11`, mean `10.85`, maximum possible `18`. **They require non-missing values for all 20
  quarters** — a severe data demand.
- **A warning that independently confirms the bug my own control caught (§6.1):** *"If
  each quarter were only ranked relative to other quarters that year, then companies with
  uniformly growing earnings would appear to have the maximum possible seasonality in the
  4th quarter."* **A growth trend masquerades as fiscal-quarter seasonality unless it is
  removed.** They handle it by ranking across 20 quarters; I handle it by de-trending
  within firm. **No source I read gives a cross-sectional magnitude for revenue, cost of
  goods or SG&A seasonality** — which is why §6.2 measures it.

---

## 5. `[MEASURED IN BRIEF]` — WHAT THE QUARTERLY ADVANTAGE DOES UNDER A SEASONALITY-FREE CONSTRUCTION

**Endpoint:** `https://raw.githubusercontent.com/bkelly-lab/jkp-data/main/documentation/sas_to_python/data/US_factors_SAS.parquet`
(HTTP 200, `1,578,145` B, magic `PAR1`). Panel: **144,620 rows, 153 characteristics,
`location=usa`, `freq=monthly`, `weighting=vw_cap`, 1926-01 → 2024-12.** Scripts
`data/D2_jkp_measure{,2,3}.py`; results `data/D2_jkp_measure{,2,3}.json`.

**Why this is the right test, and why it is better than the comparison in the
literature.** `ni_be` and `niq_be` are the **same ratio** (net income over book equity)
built from the **same filings** and **both refreshed quarterly** — `%combine_ann_qtr_chars`
substitutes whichever version has the later `datadate`, four months after fiscal period
end. The only difference is **one fiscal quarter versus the sum of four**. Novy-Marx's
annual-vs-quarterly comparison confounds **three** things — freshness, rebalance frequency
and seasonality. **This one isolates the numerator window.**

### 5.1 The three-way, on matched months

US, `vw_cap`, months where **all three** series exist: **686** (1967-11 → 2024-12).

| | construction | mean %/mo | `t` | `t` NW6 | IR ann |
|---|---|---|---|---|---|
| `ni_be` | **trailing 4 quarters — seasonality-free** | `0.245` | `2.19` | `1.98` | `0.29` |
| `niq_be` | **single fiscal quarter — unadjusted** | **`0.338`** | **`3.30`** | **`2.92`** | **`0.44`** |
| `niq_be_chg1` | **4-quarter seasonal difference** | `0.248` | **`3.81`** | **`3.33`** | **`0.50`** |
| **DIFF** | `niq_be` **minus** `ni_be` | **`+0.094`** | **`2.24`** | **`2.55`** | — |

`corr(niq_be, ni_be) = 0.927`. Era splits: 1972–2010 (n=468) `0.230 [1.60]` / `0.333
[2.52]` / `0.333 [4.20]`, DIFF `+0.103 [2.08]`. **2010–2024 (n=180) `0.224 [1.15]` /
`0.298 [1.69]` / `0.112 [1.18]`, DIFF `+0.074 [1.39]` — nothing in this family is
establishable post-2010 at `vw_cap`.**

**Spanning tests, Newey-West(6):**

| | α %/mo | `t` |
|---|---|---|
| `niq_be` (single quarter) **against** `ni_be` (TTM), n=701 | **`+0.130`** | **`+3.26`** |
| `ni_be` (TTM) **against** `niq_be`, n=701 | `−0.075` | `−1.54` |
| same pair, 2010–2024, n=180 | `+0.102` / `−0.093` | `+2.24` / `−1.88` |
| `niq_be_chg1` (seasonal difference) **against** `niq_be` | `+0.152` | `+2.10` |
| `niq_be` **against** `niq_be_chg1` | `+0.163` | `+1.49` |
| `ocf_at` (TTM) **against** `ocf_at_chg1` | `+0.436` | `+3.83` |
| `ocf_at_chg1` **against** `ocf_at` | `+0.187` | `+4.12` |

**READ THIS CAREFULLY, BECAUSE IT CUTS BOTH WAYS.**

- **Against the artefact hypothesis:** the seasonality-free TTM form keeps a **positive,
  standalone** premium (`0.245 [2.19]`), and the seasonal *difference* — the construction
  HXZ say *controls for seasonality* — is the **strongest of the three** (IR `0.50`,
  α `+0.152 [+2.10]` over the unadjusted level). **Removing the seasonality does not
  remove the signal. It improves it.**
- **For the artefact hypothesis:** the single-quarter form nevertheless has **`+0.130`
  %/mo of alpha [`+3.26`] that the seasonality-free form cannot reproduce**, and the TTM
  form is **subsumed** (`−0.075 [−1.54]`). Something in the raw single quarter is priced
  that the four-quarter sum throws away.
- **What my design can and cannot separate.** With freshness matched, the residual
  difference is **(i) the seasonality of the single quarter and (ii) the recency-weighting
  of information** — the latest quarter may simply be more informative about the future
  than a four-quarter average. **This measurement cannot separate (i) from (ii) and I do
  not claim it does.** §6.3 attacks (i) directly at the characteristic level and finds it
  real but small for the median firm.
- **And the direction is not uniform:** `ocf_at` (TTM) **beats** its own seasonal
  difference by `+0.436 [+3.83]`. Cash-flow and earnings-based variables behave
  differently, as they do in JKP's changelog (§4.3) and in HXZ.

### 5.2 CONTROL 1 — IT FIRED, ON TWO OF SIX, AND IT STAYED FIRED

JKP's CHANGELOG publishes monthly OLS information ratios for six named US factors. If my
extraction is right, mine must match. **A control that cannot fail is worse than none.**

| factor | JKP published | mine, → 2024-12 | → 2020-12 | verdict |
|---|---|---|---|---|
| `saleq_su` | `0.05` | **`0.050`** | `0.054` | exact |
| `resff3_12_1` | `0.28` | `0.262` | `0.262` | close |
| `niq_su` | `0.19` | `0.159` | `0.158` | off `0.031` |
| `qmj_prof` | `0.22` | `0.174` | `0.177` | off `0.046` |
| `bidaskhl_21d` | `−0.09` | **`−0.017`** | `−0.007` | **off `0.073`** |
| `zero_trades_21d` | `+0.09` | **`−0.028`** | `−0.032` | **WRONG SIGN, off `0.118`** |

**I made a checkable prediction before reading the numbers** — that the gap was a vintage
effect, since the CHANGELOG is dated 2021-01 and this parquet runs to 2024-12, so
truncating at 2020-12 should move my figures toward the published ones. **THE PREDICTION
FAILED: the 2020-12 column is closer for only 2 of 6, and the shifts are `0.001`–`0.01`
against gaps of up to `0.118`.** I then checked whether `ret` is un-signed relative to the
`direction` column — it is not (`market_equity`, `direction = −1`, has a **positive**
`+0.178` %/mo mean, so the sign is already applied). **So the discrepancy is unexplained.**

**What I take from it, and what I do not.** The two failures are **both liquidity
characteristics**; the **accounting and momentum** ones reproduce (`saleq_su` exact to
three decimals). My §5.1/§5.3 claims rest entirely on accounting characteristics, so I
weight them as sound — **but a reader must know that two of six of this library's own
published statistics do not reproduce on its own current data, one with the sign
reversed, and that I could not account for it.** That is a vintage/construction break in a
reference library's published numbers and it is recorded, not adjudicated. §8 item 1.

**CONTROL 2** — names that must not exist returned **0 rows** each:
`ZZZ_D2_control`, `ni_be_seasonally_adjusted`, `gp_at_seasonally_adjusted`, `gpq_at`.

**CONTROL 3, RUN AFTER THE BAR WAS MET, BECAUSE §5 USES THE *SAS* BUILD AND JKP NOW SHIP A
*PYTHON* ONE.** If the two builds disagree on the characteristics I used, my numbers are
build-specific and must say so. JKP publish the comparison
(`sas_vs_py_summ_stats.parquet`, 402 characteristics × 21 columns), and I checked it
rather than assume:

- **Every one of the 21 characteristics I used has Pearson `1.000` and Spearman `≥0.9989`
  between builds, with mean differences of `0.00`–`0.17%`.** `gp_at` `1.000`/`0.9989`;
  `ni_be`, `niq_be`, `niq_be_chg1`, `niq_at` all `1.000`/`0.9999`. **§5 is build-robust.**
- Across all 402: **Pearson median `1.0000`, p05 `0.9996`; only `0.5%` fall below `0.90`**
  — two characteristics, `resff3_6_1` (`0.089`) and `resff3_12_1` (`0.148`), both residual
  momentum. **Their Spearman rank correlations are `0.9991` and their median values differ
  by `0.41%` and `1.05%`**, so the bodies and the rankings agree and only the extreme tails
  diverge (kurtosis `2.45e6` SAS versus `4.08e6` Python). **That is an outlier-handling
  difference in two variables I do not use, not a build disagreement about a
  characteristic.** **Spearman's minimum across all 402 is `0.9944`** — no characteristic's
  ranking differs materially between builds.
- **This also RULES OUT a third explanation for Control 1's failure:** `bidaskhl_21d` and
  `zero_trades_21d` have cross-build Pearson `0.991` and `1.000`, so their mismatch against
  JKP's published IRs is **not** a SAS-versus-Python build difference either.

**Recorded because I had flagged this file as "the most alarming unexamined thing I
touched" before examining it, and on examination it is benign.** Leaving the alarm in the
record uncorrected would have been the error.

### 5.3 THE BAR, FOR GROSS PROFITABILITY — and the deflator finding that outranks it

**`gp_at` IS the seasonality-robust quarterly construction for gross profitability**
(trailing-four-quarter numerator, quarterly-refreshed, four-month lag), per §4.1. Its US
`vw_cap` long–short:

| factor | construction | era | n mo | %/mo | `t` | NW6 | IR ann | mean n stocks |
|---|---|---|---|---|---|---|---|---|
| **`gp_at`** | **GP / assets, TTM, qtr-refreshed** | full | 890 | **`0.303`** | **`3.95`** | **`3.64`** | `0.46` | 2,670 |
| `gp_at` | " | 1963–2010 | 576 | `0.292` | `2.92` | `2.81` | `0.42` | 3,137 |
| **`gp_at`** | " | **2010–2024** | 180 | **`0.377`** | **`2.25`** | **`1.98`** | `0.58` | 3,172 |
| `gp_at` | " | 2005–2024 | 240 | `0.368` | `2.63` | `2.37` | `0.59` | 3,289 |
| **`gp_atl1`** | **GP / ONE-QUARTER-LAGGED assets, TTM** | full | 878 | `0.212` | `2.47` | `2.31` | `0.29` | 2,568 |
| **`gp_atl1`** | " | **1963–2010** | 576 | **`0.163`** | **`1.43`** | **`1.42`** | `0.21` | 2,951 |
| `gp_atl1` | " | 2010–2024 | 180 | `0.312` | `1.75` | `1.41` | `0.45` | 3,109 |
| `op_at` | oper profits / assets, TTM | full | 890 | `0.308` | `4.33` | `3.94` | `0.50` | 2,789 |
| `op_atl1` | oper profits / lagged assets | 1963–2010 | 576 | `0.187` | `1.92` | `1.84` | `0.28` | 3,160 |
| `ope_be` | oper profits / book equity, TTM | full | 890 | `0.327` | `3.81` | `3.51` | `0.44` | 2,405 |
| `ope_bel1` | " / lagged equity | 1963–2010 | 576 | `0.175` | `1.83` | `1.73` | `0.26` | 2,778 |
| `cop_at` | cash-based oper prof / assets | full | 878 | `0.515` | `9.09` | `8.31` | `1.06` | 2,569 |

**THE BAR IS MET: a seasonality-robust quarterly gross-profitability sort earns `0.303`
%/mo [NW6 `3.64`] over 890 months and `0.377` [NW6 `1.98`] in the programme's own era.**
It is positive and it survives. **It is also only marginal post-2010 on the Newey-West
`t`, and every member of this family except `cop_at` falls below `t = 2` on NW6 in
2010–2024.**

**AND THE FINDING I WAS NOT SENT FOR, WHICH IS LARGER THAN THE ONE I WAS.** Holding the
library, sample, weighting and TTM construction fixed and changing **only the deflator's
timing** — current assets versus one-quarter-lagged assets:

- **1963–2010: `gp_at` `0.292 [t 2.92]` versus `gp_atl1` `0.163 [t 1.43]`. The lagged
  deflator is INSIGNIFICANT where the current one is significant.**
- The same gap appears for operating profits (`0.337 [3.72]` vs `0.187 [1.92]`) and for
  operating profits to equity (`0.317 [2.74]` vs `0.175 [1.83]`). **Three for three.**

**Novy-Marx (2013) uses the current-quarter deflator; HXZ's `Gla_q` and OSAP's `GPlag_q`
use the one-quarter-lagged one.** `R3-01` §7.4 measured that this choice costs **8–14% of
the computable cross-section** from as-filed XBRL. **It also costs roughly half the `t`.**
**I would put the deflator question in front of the principal ahead of the seasonality
question**, and it is `D1`'s node territory as much as mine.

**Caveat, stated rather than buried.** `gp_at` begins 1950-11, i.e. built from **annual**
Compustat for its early decades; the trailing-four-quarter quarterly refresh only binds
once quarterly Compustat exists. **The 2005–2024 and 2010–2024 rows are the only ones
where the construction under test is reliably operative**; the full-sample row is a hybrid
across time and should not be read as "the quarterly construction over 890 months."

---

## 6. `[MEASURED IN BRIEF]` — HOW SEASONAL IS THE SORTED INPUT, AND DOES IT REACH THE SORT?

**Endpoint:** `https://www.sec.gov/files/dera/data/financial-statement-data-sets/<q>.zip`,
**13 zips 2021q4–2024q4, 1,465,690,535 bytes**, paced 0.5 s, contact string
`research@backtest-framework.org`, sha1 of every zip in `data/D2_fsds_download.log`.
**685,444 facts retained** from 44.6M `num.txt` lines. Scripts
`data/D2_{fetch_fsds,extract,analyse,analyse4,analyse5,analyse6}.py`.

**Correctness points, each checked rather than assumed.** `segments` **must be empty** —
otherwise a row can be a **segment disaggregation** (revenue by business unit) rather than
the consolidated figure; `coreg` must be empty; `uom = USD`; flows are `qtrs='1'`, `Assets`
is `qtrs='0'`. **`prevrpt` is a HINDSIGHT column** (it flags that a submission was
*subsequently* amended) and is **recorded — 1.73% of rows — never used to filter.**
As-filed discipline: where one `(cik, tag, ddate, qtrs)` appears in several submissions the
**earliest `filed`** wins (159,068 later restatements/comparatives dropped).

### 6.1 THE CONTROLS, INCLUDING THE THREE THAT FIRED AND WHAT EACH ONE TAUGHT

| control | result |
|---|---|
| impossible FSDS quarters `2099q1`, `2021q5` | **HTTP 404 both** — as required |
| a tag that cannot exist, `ZZZZNotATagD2Control` | **0 rows** across all 13 zips |
| **`Assets` with `qtrs='1'`** — `Assets` is an **instant**, so a duration row would mean the parser is mixing instants and durations | **0 rows** — as required |
| parallel extraction efficiency | 62 s item time / 10.0 s wall on 8 processes = **6.2× (78%)**, above the 70% floor |

**THREE CONTROLS FIRED, and each one killed a statistic of mine rather than a fact about
the data. They are kept on the record because a control that can fire is the only kind
worth having.**

1. **A raw fiscal-quarter-dummy R² is not interpretable here, and `Assets` proved it.**
   First pass: Revenues median R² `0.210`, **`Assets` `0.136`** — far too high for an
   instant that should be nearly aseasonal. With ~13 quarters per firm, four dummies
   fitted to a de-trended residual absorb variance **by construction**; the pure-noise
   expectation is ≈`3/11 ≈ 0.27`, so **my Revenues figure was BELOW the null.** Discarded.
2. **A random permutation of quarter labels is an INVALID null.** True fiscal-quarter
   labels are **evenly spaced in time**; a random permutation is not, and with a serially
   correlated residual that **inflates** the null. **Tell: `Assets` came in `0.105` BELOW
   its own null**, which is impossible for a well-specified null. Discarded.
3. **A rotation of the quarter labels is DEGENERATE.** A rotation maps the mod-4 partition
   **onto itself** and merely renames the groups; R² and peak-minus-trough do not depend
   on group names. **Tell: excess was EXACTLY `0.000` for all four inputs, ratio exactly
   `1.00`.** Discarded. (Noted because the campaign rule about *enumerating* a small finite
   null group is right in general and wrong for this statistic — the group acts trivially.)

**What survived**, and `Assets` now calibrates correctly: **(S1)** a **split-half
fiscal-quarter profile correlation** — split a firm's years in half, compute the
mean de-trended fiscal-quarter profile in each, correlate them; real seasonality repeats.
**(S2)** peak-minus-trough **amplitude against an AR(1) surrogate null** (300 surrogates
per firm) which carries the firm's own persistence and no seasonality.

### 6.2 `Q1` AND `Q4` — THE MAGNITUDES THE LITERATURE DOES NOT CONTAIN

**Seasonality in the four inputs a profitability sort needs.** Firms with ≥8 quarterly
observations and all four fiscal quarters present; **fiscal Q4 derived as annual minus
nine-month YTD**, because a 10-K reports the year and not its Q4 — requiring a natively
tagged single Q4 had silently cut the Revenues sample from 5,598 firms to 583.

| input | firms | **split-half** | % > 0 | % > 0.5 | amplitude | AR(1) null | **ratio** | **% p < .05** | ρ |
|---|---|---|---|---|---|---|---|---|---|
| **Revenues** (flow) | 1,347 | **`+0.408`** | 64.4 | 44.8 | `0.174` | `0.122` | **`1.36×`** | **`23.0`** | 0.20 |
| **CostOfGoodsSold** (flow) | 790 | **`+0.395`** | 63.9 | 45.4 | `0.164` | `0.120` | `1.35×` | `23.0` | 0.17 |
| **SG&A** (flow) | 1,176 | `+0.256` | 59.0 | 38.2 | `0.200` | `0.175` | `1.23×` | `12.5` | 0.04 |
| **`Assets` (instant — NEGATIVE CONTROL)** | 6,090 | **`−0.003`** | 49.7 | 26.8 | `0.092` | `0.095` | **`0.99×`** | **`2.5`** | **0.34** |

**THE CONTROL IS TEXTBOOK-CALIBRATED.** `Assets` shows **no repeatable fiscal-quarter
profile** (`−0.003`), an amplitude **exactly at** its own null (`0.99×`), and a **2.5%**
hit rate against a nominal 5% threshold. **And it has the HIGHEST serial correlation of
the four (ρ `0.34`) while showing the LOWEST seasonality — so the statistic is not merely
picking up persistence.**

**Revenue seasonality by industry division** (median within firm):

| division | n | split-half | % > .5 | amplitude | ratio | % p < .05 |
|---|---|---|---|---|---|---|
| **G retail** | 128 | **`+0.833`** | 68.0 | `0.227` | **`1.90×`** | **`52.3`** |
| **F wholesale** | 54 | `+0.546` | 53.7 | `0.142` | `1.44×` | `22.2` |
| D manufacturing | 590 | `+0.403` | 43.2 | `0.155` | `1.38×` | `22.2` |
| E transport/utilities | 63 | `+0.303` | 46.0 | `0.248` | `1.38×` | `20.6` |
| I services | 300 | `+0.267` | 41.0 | `0.139` | `1.26×` | `15.7` |
| H finance/insurance/RE | 143 | `+0.034` | 33.6 | `0.176` | `1.18×` | `11.9` |
| B mining | 37 | **`−0.180`** | 29.7 | `0.418` | `1.05×` | `8.1` |

**AND A CORRECTION TO THE SLATE'S OWN FRAMING, WHICH IS WHAT BIASING TOWARD THE NEGATIVE
LOOKS LIKE.** The slate says *"a retailer's fiscal-Q4 revenue being four times its Q1"*.
**For the MEDIAN retailer the peak-to-trough fiscal-quarter spread is `0.227` of mean
quarterly revenue — about 23%, not 300%.** The folklore holds for a tail, not a median:
the 90th-percentile amplitude across all firms is `0.994` (a full year-mean quarter). **The
seasonality is real, repeatable and industry-concentrated; it is not, for the typical
filer, enormous.**

**`Q4` — THE FISCAL-YEAR-END DISTRIBUTION, AND IT IS NOT INDEPENDENT OF INDUSTRY.**
7,657 filers with a usable `fye`:

- **NON-DECEMBER fiscal year end: `19.41%` (1,486 of 7,657).** Month shares: Dec `80.59%`,
  Jun `4.14%`, Sep `4.05%`, Mar `2.86%`, Jan `2.06%`, Apr `1.02%`, Oct `0.99%`, Aug
  `0.97%`, Jul `1.10%`, May `0.82%`, Nov `0.74%`, Feb `0.65%`. All 12 months present.
- **Industry division × `fye` month: Cramér's V = `0.1190` (χ² = 1,084, 11×12 table).**
  **NEGATIVE CONTROL — `fye` permuted across firms, 30 draws: V = `0.0377` (p95
  `0.0497`). Observed is `3.2×` the permuted mean and far outside its p95.** The control
  fired correctly in the sense that matters: it produced a non-zero floor, and the
  observed value clears it.
- **Non-December share BY INDUSTRY, which is the channel the slate asked about:**
  **retail `43.27%`** (n=312), **wholesale `40.54%`** (n=148), construction `29.85%`
  (n=67), services `26.91%` (n=1,334), mining `25.56%` (n=313), manufacturing `22.03%`
  (n=2,587), transport/utilities `13.02%` (n=407), **finance/insurance/RE `7.77%`**
  (n=2,265).

**THE TWO CHANNELS COMPOUND, AND THEY COMPOUND IN THE SAME TWO INDUSTRIES.** Retail and
wholesale are simultaneously **the most revenue-seasonal** (split-half `0.833` / `0.546`,
amplitude ratio `1.90×` / `1.44×`) **and the most non-December** (`43.3%` / `40.5%`). So a
sort formed in a single calendar month does mix firms at different points in their own
fiscal cycles, **and the mixing is heaviest exactly where the seasonality is.** Financials,
the largest division by count, are both the least seasonal and the most uniformly
December.

### 6.3 THE DECISIVE CHARACTERISTIC-LEVEL TEST — AND A CONTROL THAT FIRED AND TAUGHT THE DESIGN

A lane with no return fixture cannot measure what a sort *earns*. It can measure whether
the two sorts are **the same sort**, and whether the single-quarter one is contaminated by
fiscal-quarter phase. At each formation quarter-end, for every firm with the data:

```
Sq  = GP(t)                              / Assets(t−1q)      SINGLE QUARTER
Ttm = GP(t)+GP(t−1)+GP(t−2)+GP(t−3)      / Assets(t−1q)      TRAILING FOUR QUARTERS
```
`GP = Revenues − CostOfGoodsSold`, both single-quarter, `segments` empty. **8,105
firm-quarters, 781 firms, 19 quarters; 14 quarters with n ≥ 150 (median n = 638).**
Sanity: median `Sq` `0.0758`, median `Ttm` `0.3063`, **ratio `4.04` — as a four-quarter sum
over the same deflator must be.**

**(a) The two constructions hold mostly the same names.**
**Spearman rank correlation `0.918`** (min `0.882`, max `0.969` across quarters).
**Top-decile overlap `0.778`; bottom-decile `0.758`** (1.00 = identical leg, 0.10 =
random). **So a seasonality-free construction keeps ~78% of the long leg.** That bounds how
much of any return difference can come from holding different names — and it is consistent
with the `corr = 0.927` between `ni_be` and `niq_be` in §5.1 on a completely different
dataset.

**(b) THE CROSS-SECTIONAL PHASE TEST FAILED ITS OWN CONTROL, and the failure is the
finding.** R² of fiscal-quarter-phase dummies on the cross-sectional rank: **single
quarter `0.03902`, trailing four quarters `0.03830` — ratio `1.02×`, essentially
identical.** I had declared that `Ttm` **must** be near zero, because a four-quarter sum
spans every phase by construction. **It is not.** The reason: **in a cross-section a firm's
fiscal-quarter phase is fixed by its fiscal-year-end month**, and `fye` is correlated with
industry (V `0.1190`, §6.2), which is correlated with the profitability level. **So the
cross-sectional statistic measures COMPOSITION, not seasonality** — and the two
constructions share the composition exactly. For scale, **industry division explains
`0.10937` / `0.12213` of the same ranks — about 3× more than fiscal-quarter phase, and
slightly MORE for the TTM construction.** A profitability sort is far more an industry bet
than a fiscal-phase bet, in **both** constructions.

**(c) THE CLEAN ISOLATION IS WITHIN FIRM — where industry and `fye` are constant by
construction, so the fiscal-quarter label can proxy for nothing but that firm's own
seasonality.** Per firm, its own cross-sectional percentile rank regressed on
fiscal-quarter dummies, calibrated against an AR(1) surrogate null (300 per firm). **613
firms with both computed:**

| | within-firm R² | AR(1) null | **excess** | **% firms p < .05** | within-firm rank sd |
|---|---|---|---|---|---|
| **single quarter** `Sq` | `0.2418` | `0.2279` | **`+0.0129`** | **`14.0%`** | **`0.0764`** |
| **trailing 4 qtr** `Ttm` **(NEG CONTROL)** | `0.1103` | `0.1736` | **`−0.0682`** | **`1.0%`** | `0.0541` |
| **paired difference** | — | — | **`+0.0700`** | — | **ratio `1.41×`** |

**Wilcoxon signed-rank on the 613 pairs: `p = 1.32e−38`.**

**THIS CONTROL BEHAVED. `Ttm` shows 1.0% of firms "significant" against a nominal 5% — it
UNDERSHOOTS chance, exactly as a construction that cannot carry seasonality should.** And
the single-quarter construction moves a firm **1.41× as far** around the cross-section from
one quarter to the next.

**By industry, and it is the same two industries again:**

| division | n | excess `Sq` | excess `Ttm` | **`Sq − Ttm`** | **sd ratio** |
|---|---|---|---|---|---|
| **G retail** | 80 | **`+0.1288`** | `−0.0304` | **`+0.1678`** | **`1.55×`** |
| **F wholesale** | 34 | `+0.1006` | `−0.0357` | **`+0.1457`** | `1.47×` |
| D manufacturing | 314 | **`−0.0200`** | `−0.0756` | `+0.0566` | `1.35×` |
| I services | 138 | `+0.0078` | `−0.0543` | `+0.0276` | `1.24×` |

**SO THE ANSWER TO "IS A SINGLE-QUARTER SORT AN UNADJUSTED SEASONAL SORT" IS: YES,
MEASURABLY, AND THE MEASUREMENT IS SMALL FOR THE MEDIAN FIRM AND LARGE FOR RETAIL AND
WHOLESALE.** The median manufacturer shows **no absolute** phase structure (`−0.0200`);
the median retailer shows a lot (`+0.1288`). **The contamination is real, it is localised,
and it is identifiable ex ante from SIC code and fiscal-year-end month** — which is the
one genuinely actionable thing in this brief.

**Limits of §6, stated plainly.** 2021q4–2024q4 only, ~10–13 quarters per firm, so the
split-half halves are ~1.5 years each and noisy. The `Sq`/`Ttm` panel is **781 firms** —
small, because it needs four consecutive quarters of **both** revenue and cost of goods
plus lagged assets, and `CostOfGoodsSold` is tagged by only 3,527 of 7,659 filers. Firms
must have all four fiscal quarters present, which selects. **These are lower bounds on
sample and upper bounds on precision; none of them is the programme's universe, which I
cannot see.**

---

## 7. PAST THE SUB-QUESTIONS — THE ADJACENT QUESTIONS THE SLATE DID NOT ASK

**Stated explicitly per the depth mandate: everything in §7 is beyond what `D2` was
commissioned to find.**

### 7.1 "SEASONALITY-FREE" AND "SEASONALLY ADJUSTED" ARE NOT THE SAME THING, AND THE SLATE'S DECISION RULE CONFLATES THEM

The slate's decisive question offers a dichotomy: if the trailing-four-quarter form
performs like the annual one, *"the advantage was the seasonality"*; if it keeps the
advantage, *"the advantage is the freshness of the data."* **Neither branch is what
happened, and the dichotomy is not exhaustive.** There are **three** distinguishable
constructions, not two:

1. **The single-quarter level** — fresh, unadjusted, seasonal.
2. **The trailing-four-quarter level** — fresh, seasonality-free, but it **also discards
   the recency-weighting** of the latest quarter. It is not "the single quarter,
   seasonally adjusted"; it is a four-quarter average.
3. **The four-quarter difference** — fresh, seasonality-controlled, but it is a **change**
   signal and not a level at all. HXZ say so: it *"likely better captures the underlying
   economic profitability than Roe itself"* — a different economic claim, not a cleaned
   version of the same one.

**No construction anywhere in this literature is "the single-quarter LEVEL with its own
seasonality removed."** That object — a single fiscal quarter divided by that firm's own
historical seasonal factor for that quarter — **does not exist in any source I read, in
any code I read, or in any of OSAP's 331 signals.** It is the construction that would
actually separate seasonality from recency, and **it has never been built.** That is a
sharper "nobody has checked" than the one the lane was sent to establish, and it is
buildable from the quantities in §6.

### 7.2 THE SINGLE-QUARTER FORM'S EXTRA TURNOVER IS NOT FREE, AND I CAN BOUND IT

§6.3 measures that the single-quarter rank has **1.41× the within-firm quarter-to-quarter
volatility** of the TTM rank (`0.0764` vs `0.0541` in percentile units). **A sort whose
ranks move 41% more moves more names across any decile boundary**, which is turnover that
the TTM construction does not pay. `R3-01` §8.2 records Novy-Marx's own statement that the
quarterly strategy turns over ~4× the annual one. **The present measurement says part of
that excess turnover is being paid to chase fiscal-quarter phase** — in retail, where the
sd ratio is `1.55×`, most of it. **This lane computes no net number and has no fixture**;
the point is only that **the cost side and the contamination side are the same
phenomenon**, and a trailing-four-quarter construction reduces both at once. That is a
different argument for the TTM form than the seasonality one, and it is stronger.

### 7.3 A THIRD INSTANCE OF CODE-VERSUS-PROSE, AND A FOURTH THING IT IMPLIES

§4.2 records OSAP's documentation misstating both `ChangeRoA` and `ChangeRoE`. **The
implication nobody has drawn: every second-hand restatement of HXZ's seasonally-differenced
profitability variants that was taken from `SignalDoc.csv` rather than from the code is
wrong.** And because `roaq` uses **lagged** assets while `ChangeRoA` uses
**contemporaneous** assets, **OSAP's seasonal difference is not the difference of OSAP's
level** — so the library cannot be used for a with/without seasonal-adjustment comparison
even though it appears to contain both sides. **That is why §5 uses JKP and not OSAP**, and
it is worth saying because the opposite choice would have looked equally reasonable.

### 7.4 FISCAL Q4 IS LARGELY ABSENT FROM AS-FILED XBRL AS A SINGLE QUARTER

`[MEASURED IN BRIEF]`, and discovered by accident when a sample collapsed. Requiring a
**natively tagged** single-quarter (`qtrs=1`) fiscal-Q4 revenue row cut the usable sample
from **5,598 firms to 583**, because a 10-K reports the **year**, not its fourth quarter.
Deriving Q4 as **annual (`qtrs=4`) minus nine-month YTD (`qtrs=3`)** recovered
**3,081 Revenues, 2,545 CostOfGoodsSold and 3,597 SG&A** firm-quarters that are otherwise
invisible. **No source I read states this**, and `R3-01`'s computability census (its
finding 7) measured tag presence without separating the Q4 case. **Any as-filed quarterly
profitability panel that does not derive Q4 is missing one quarter in four for most
filers, and is missing it non-randomly** — which would itself induce a fiscal-phase
selection, i.e. manufacture the very artefact this lane was sent to look for.

### 7.5 THE SEASONALITY-FREE CONSTRUCTION HAS NO PUBLISHED ANNUAL COUNTERPART, SO THE CLEANEST COMPARISON IS STILL IMPOSSIBLE

JKP compute characteristics *"for annual and quarterly accounting data separately"* and
then **keep whichever is more recent** (§4.1). The two halves exist inside their pipeline;
**only the hybrid ships.** So even in the one library with a seasonality-free quarterly
construction, **there is no annual-only `gp_at` to compare it against** — which is why §5.3
reports a level and not a quarterly-minus-annual difference, and why `R3-01` §11 item 9 was
right to note there is *"no annual-only counterpart in their library."* **Reproducing both
halves requires WRDS Compustat access, which this lane does not have and which is the
single thing that would close this question properly.**

---

## 8. CONFLICTS, RECORDED AND NOT ADJUDICATED

1. **JKP's published information ratios versus JKP's own current data.** Two of six do not
   reproduce (`bidaskhl_21d` `−0.09` vs `−0.017`; `zero_trades_21d` `+0.09` vs `−0.028`,
   **sign reversed**); four do, to within `0.05`, one exactly. My vintage explanation was
   tested and **failed**. **I would weight my own recomputation for the accounting
   characteristics** (the class that reproduces, including an exact match) **and weight
   JKP's published figure for the liquidity ones**, because their construction is the part
   I have not read. **Both stay on the record.**
2. **Direction of the seasonality effect: earnings versus sales.** JKP's changelog has
   imposing a seasonal base **halving** the sales signal (`0.12 → 0.05`) and **raising** the
   earnings one (`0.11 → 0.19`). HXZ have the seasonality-controlled ROE **stronger**
   (`0.69 [3.07] → 0.76 [5.43]`). My own panel has the seasonal difference stronger for
   net income (`niq_be_chg1` over `niq_be`, α `+0.152 [+2.10]`) and **weaker** for cash
   flow (`ocf_at` over `ocf_at_chg1`, α `+0.436 [+3.83]`). **Four measurements, three
   directions. I would weight HXZ's**, because it is the only one that is a like-for-like
   level-versus-adjusted-level comparison on one sample with the authors' own attribution —
   **but the sales result is the one that bears on gross profitability's numerator, and it
   points the other way.** Nothing here resolves it.
3. **`R3-01`'s table transcriptions, which I could not re-verify.** I obtained HXZ
   w23394 and read its prose in full, but **the tables did not survive PDF extraction with
   row labels attached**, so I could **not** independently check the `0.16 [1.04] → 0.51
   [3.40]` and `0.20 [1.07] → 0.72 [3.35]` cells, nor Novy-Marx's Table A6 (whose source
   mirror I did not fetch at all). **They stand as `R3-01` recorded them, inherited and
   unverified by me.** I found nothing inconsistent with them; I found nothing confirming
   them either. This is a gap in the chain between round 3's headline and this lane's test
   of it, and it should be closed by someone with the published RFS version.
4. **`R3-01`'s and my own readings of HXZ agree and extend each other.** `R3-01` had the
   interpretation sentence; I add the preceding sentence with `Roe`'s own `0.69 [3.07]`.
   **No conflict — a completion**, recorded so the provenance of the added number is clear.

---

## 9. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **Whether the single-quarter form's `+0.130` %/mo [`+3.26`] alpha over the
   trailing-four-quarter form is SEASONALITY or RECENCY.** My design holds freshness
   constant, which removes staleness as an explanation, but the residual difference is
   jointly (i) the single quarter's seasonality and (ii) the informational value of the
   most recent quarter over a four-quarter average. **§7.1 names the construction that
   would separate them and establishes that nobody has built it.** This is the central
   unresolved thing in the brief.
2. **Why two of JKP's six published information ratios do not reproduce**, one with the
   sign reversed. **Three explanations tested and all three ruled out:** a sample-end
   vintage effect (the 2020-12 truncation is closer for only 2 of 6, by `0.001`–`0.01`
   against gaps up to `0.118`); an unapplied `direction` sign (`market_equity`, direction
   `−1`, has a **positive** mean, so the sign is already applied); and a SAS-versus-Python
   build difference (cross-build Pearson `0.991` and `1.000` for the two failing factors,
   §5.2 Control 3). **I did not read their liquidity-characteristic construction, which is
   the remaining candidate.** §8 item 1.
3. **HXZ's and Novy-Marx's table cells**, for the reason in §8 item 3. The `t`-statistics
   at the centre of round 3's headline remain transcribed-once, by one lane.
4. **Whether §6's magnitudes hold before 2021.** My FSDS window is 2021q4–2024q4 — 13
   quarters, chosen for as-filed XBRL coverage. Revenue seasonality, the fiscal-year-end
   distribution and the phase contamination could all have been larger in the 1970s–2000s
   sample where the published results were estimated. **I measured the present and inferred
   nothing about the past.**
5. **Whether the `781`-firm `Sq`/`Ttm` panel is representative.** It requires
   `CostOfGoodsSold` to be tagged (3,527 of 7,659 filers) **and** four consecutive
   quarters **and** all four fiscal quarters present. I did not characterise how that
   selection differs from the full filer population on size, price or industry. **Per the
   campaign's "size is not price" rule I should report the price distribution of the names
   carrying this effect and I cannot: FSDS carries no prices**, and I had no permitted
   price source for a cross-sectional match.
6. **Whether JKP's `%ttm(fqtr)^=10` guard is sufficient in practice**, as opposed to
   necessary. I established that `{1,1,4,4}` and `{2,2,3,3}` also sum to 10 and argued they
   cannot arise from contiguous sorted data; **I did not run the code** and so did not
   confirm it empirically.
7. **Whether OSAP's `SignalDoc.csv` errors on `ChangeRoA`/`ChangeRoE` are known upstream.**
   I read the code and the documentation; I did **not** check the repository's issues or
   commits, so I cannot say whether this is already filed.
8. **The claim that Akbas–Jiang–Koch use quarterly seasonal dummies.** Still
   second-hand, still unverified, and still supporting nothing. §3 item 1.

---

## 10. WHAT I DID NOT OPEN

**Separate from §9 per the depth mandate. Documents I identified, judged relevant or
plausibly relevant, and did not read.**

1. **Akbas, Jiang & Koch, *The Trend in Firm Profitability and the Cross Section of Stock
   Returns*, The Accounting Review 92(5), 2017** (DOI `10.2308/ACCR-51708`, SSRN 2538867).
   **NOT OBTAINED, after seven distinct routes** — recorded by **tool and response** per the
   campaign rule, never by host: Semantic Scholar Graph API → HTTP 200, `openAccessPdf`
   **`status: CLOSED`**, `url: ""`; Unpaywall (contact string
   `research@backtest-framework.org`) → HTTP 200, `is_oa: false`, `oa_locations: []`,
   `has_repository_copy: false`; OpenAlex → HTTP 200, `primary_location.pdf_url: null`, no
   OA location; `papers.ssrn.com` via urllib → **HTTP 403 Cloudflare interstitial**
   (`<title>Just a moment...</title>`, a bot challenge — **not bypassed, per the standing
   rule**); `core.ac.uk` → **HTTP 403, same Cloudflare interstitial**; `docplayer.net`
   mirror → **DNS `getaddrinfo` failure via both WebFetch (`ENOTFOUND`) and urllib**, i.e.
   the host does not resolve in this environment; **the author's own site**
   (`sites.google.com/site/chaojiang7`) → HTTP 200, fetched and parsed, and **its only
   non-SSRN file link is his CV** (Google Drive `1G8Ykx9bB6uHwbSG6h_z24nbm6pWeZGx3`),
   confirmed by reading the surrounding markup; KU ScholarWorks DSpace REST API → HTTP 200
   `application/hal+json` with no matching item. **It remains the source that most directly
   bears on §4.3 and it is still the first thing a follow-up should get.** A shadow-library
   copy was visible in search results and **deliberately not used.**
2. **The published RFS 33(5) 2020 version of Hou–Xue–Zhang**, and **Novy-Marx (2013)
   Table A6 in any form.** I read the NBER working paper's prose; I fetched neither the
   published HXZ nor the Novy-Marx mirror `R3-01` used. §8 item 3.
3. **`Business seasonality and stock liquidity`, Journal of Financial Markets 67 (2024)**
   (`S1386418123000678`). Located, **not opened** — ScienceDirect, and its dependent
   variable is liquidity. **Its in-scope half is a firm-level sales-seasonality measure
   (reportedly: the five highest of the past 20 quarters falling in the same fiscal
   quarter), which I measured myself instead (§6.2) rather than trust a summariser for.**
   A lane wanting a published cross-sectional magnitude for sales seasonality should get it.
4. **Foster (1977), Griffin (1977), Brown & Rozeff (1979), Bernard & Thomas (1989/1990),
   Freeman & Tse (1989), Lorek** — the seasonal-ARIMA / seasonal-random-walk time-series
   literature on quarterly accounting data. **Not opened.** `L1` cites Freeman & Tse and
   Foster–Olsen–Shevlin and I took the chain from `L1`'s own text. **This is the body of
   work that would give `Q1` its canonical magnitudes and autocorrelation structure, and
   it is the largest unexplored area adjacent to this lane.** Much of it is
   PEAD-adjacent, which is excluded ground for its *return* results but **not** for its
   characterisation of the input's time-series properties.
5. **Balakrishnan, Bartov & Faurel (2010), JAE** — cited by **both** OSAP (for `roaq`,
   `ChangeRoA`, `ChangeRoE`) and JKP (for `niq_at`) as the source of quarterly ROA.
   **Not opened**, for the same reason `R3-01` gave: it is a post-loss/announcement-drift
   paper. **But it is now the named origin of BOTH the level and the seasonal-difference
   variants in two reference libraries**, which is a stronger reason to open it than
   `R3-01` had.
6. **`bkelly-lab/jkp-data/src/jkp/data/aux_functions.py`** (375,719 B) — the **Python port**
   of the SAS characteristic construction. I read the **SAS** original in full and the
   documentation LaTeX; I did **not** diff the Python against it. Given that this repo
   ships a whole `documentation/sas_to_python/` comparison directory including
   `lms_comparison.parquet` and `sas_vs_py_summ_stats.parquet`, **the two ports are known
   to differ and the size of the difference is sitting in a file I downloaded and did not
   analyse.**
7. ~~`D2_sas_vs_py_summ_stats.parquet`~~ — **NO LONGER ON THIS LIST. I opened it after the
   bar was met and it became Control 3 (§5.2).** It is kept here, struck through rather than
   deleted, because the sequence is the point: I first listed it as *"the most alarming
   unexamined thing I touched"* on the strength of one Pearson correlation of `0.089`, and
   on examination **the alarm was false** — ranks agree at Spearman `≥0.9944` across all
   402 characteristics and all 21 I used agree at Pearson `1.000`. **An unopened file
   produced a scarier claim than the opened one supported**, which is the argument for the
   depth mandate in miniature.
8. **`documentation/is_there_a_replication_crisis_in_finance_JF.pdf`** (1,447,872 B, the
   **published Journal of Finance version**) and `documentation/compustat_correction/` —
   both present in the repo I harvested, neither opened. The Compustat-correction
   directory is a documented data-defect correction with its own statistics parquet.
9. **JKP's `%QUARTERIZE` macro body.** I read its call site and the TTM block around it;
   I did not locate and read the macro that converts year-to-date items to quarters.
   **It is upstream of every number in §5** for any firm whose quarterly items are
   YTD-only.
10. **FSDS `pre.txt` and `tag.txt`** (99.5 MB and 20.8 MB per zip). I used `sub.txt` and
    `num.txt` only. `pre.txt` carries statement and line ordering, which would let a build
    distinguish an income-statement `GrossProfit` from one tagged elsewhere — the same item
    `R3-01` §11 left unopened.
11. **Every FSDS quarter outside 2021q4–2024q4.** Thirteen zips of roughly seventy.
12. **Filing text.** Reg S-K Item 101(c)(1)(v) makes seasonality a **mandated disclosure
    topic** (§4.1), so `10-K` Item 1 text is a direct, primary route to identifying which
    firms call themselves seasonal — and a far better instrument than my SIC proxy in
    §6.2–§6.3. **I did not fetch a single filing.** This is the cheapest high-value
    follow-up available from this brief.
13. **`jkpfactors.com`'s own download interface.** I took the factor panel from the GitHub
    repository instead. I do not know whether the site offers characteristic-level data or
    an annual-only variant that would close §7.5.

---

## 11. WHAT THIS BRIEF DOES NOT CLAIM

**Nothing here is elevated out of `docs/research/`.** Both books are unchanged; nothing is
closed and nothing is admitted. **No claim of any kind is made about the programme's
fixture, which this lane cannot see** — every return figure in §5 is JKP's US `vw_cap`
long–short on their universe, not this programme's, and §5.1's 2010–2024 `t`-statistics are
below 2 throughout.

**I do not claim round 3's headline is wrong.** I claim the seasonal-artefact hypothesis
that would have killed it is **not supported by the two places anyone has measured both
sides**, that the contamination it names is **real but small for the median firm and
concentrated in retail and wholesale**, and that **the construction choice that actually
moves this family by more is the deflator's timing** (§5.3). **Round 3's headline should be
marked provisional on the deflator, not on the season** — and that reframing, not a
verdict, is this lane's result.

**I do not claim to have resolved seasonality versus recency** (§9 item 1). The
construction that would — a single fiscal quarter divided by that firm's own seasonal
factor — **does not exist in any source, code base or signal library I examined**, and
saying so is §7.1's finding rather than a gap in it.

Every literature figure is transcribed from a document named and graded in §2. Every
measurement is marked **`[MEASURED IN BRIEF]`**, names its endpoint, **carries at least one
negative control that could fire — and five of them did, four of which killed a statistic
of mine rather than a fact about the world**: the raw fiscal-quarter R², the permutation
null, the rotation null (§6.1), and the whole cross-sectional phase design (§6.3b), which
is what forced the within-firm test that became the lane's decisive measurement. **The
fifth — JKP's own published information ratios, §5.2 — fired and is still unexplained.**
Everything is reproducible from the scripts and JSON in `data/` prefixed `D2_`.
