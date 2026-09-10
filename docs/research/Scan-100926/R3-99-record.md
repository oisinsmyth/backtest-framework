# Scan-100926 · Round 3 — record

**Slate:** [`R3-00-slate.md`](R3-00-slate.md) · **campaign contract:** [`00-SCHEMA.md`](00-SCHEMA.md) ·
**round 2:** [`R2-99-record.md`](R2-99-record.md) · **round 1:** [`R1-99-record.md`](R1-99-record.md).

**STATUS: COMPLETE — all four lanes in.**

**Under [R15](../../RULES.md#r15) nothing here closes or admits anything.** Nothing in this folder is
elevated out of `docs/research/`. **Conflicts are recorded, not adjudicated** — and this round's
central conflict is between **two of its own lanes**, both fully controlled, reaching **opposite
verdicts on the same question in the same era** (§4, `F1`).

---

## 0. THE SHAPE OF THE ROUND

**The depth mandate was added to the contract before dispatch, and it worked.**

| lane | tokens | vs the 250–300k plateau |
|---|---|---|
| `C1` quarterly variant and the lag | **368k** | **+23%** |
| `C2` how much does the answer move | **335k** | **+12%** |
| `C3` the shape of the drawdown | **334k** | **+11%** |
| `C4` is it already dead | **407k** | **+36%** |
| **round 3** | **~1.44M** | **vs ~1.13M in round 2** |

**Four of four lanes broke the plateau, and the round cost ~28% more than round 2 — above the
schema's projected 1.0–1.4M band.** That is the honest number: **the mandate bought depth and it cost
money.** What it bought is in §1–§3, and §6 records where the extra spend actually went.

**AND THE ROUND'S ORGANISING FACT IS THAT THREE LANES INDEPENDENTLY FOUND THE SAME BLIND SPOT IN THREE
DIFFERENT LITERATURES. NONE WAS TOLD THE OTHERS WERE LOOKING.**

- `C2`: **the non-standard-errors literature measures spreads, never long legs** — zero occurrences of
  *"long leg"* in one paper's appendices.
- `C3`: **no source reports a long-only tilt's drawdown.** The two that appear to are reporting a
  **market-neutralised** leg (2.2% vol, −0.02 beta) and a column headed *"% cumulative
  underperformance"*.
- `C4`: **none of the five decay papers it read in full reports long-leg decay separately**, verified
  by grep on all five.

**The programme can only hold the long leg. Three separate literatures do not report it.** That is
this round's most reusable finding and no lane was commissioned to find it.

---

## 1. THE CENTRAL CONFLICT — TWO OF THIS ROUND'S OWN LANES, OPPOSITE VERDICTS, SAME ERA

**Both lanes asked: what does an equal-weighted profitability long leg earn against its own
equal-weighted universe — the benchmark round 2's `B1` recommended?**

| | `C3` | `C4` |
|---|---|---|
| **result** | **+0.026 %/mo, IR 0.057, `t` 0.45** over 63 years; **1,235 years to reach `t` = 2**. In the programme's era the EW tilt compounds at **10.62% against the EW universe's 10.66%** — worth nothing — with a **deeper** drawdown (−38.60% vs −36.42%) | **+0.405 %/mo, `t` 3.00** post-publication 2014–2024; **+0.379, `t` 3.56** over 2010–2024 |
| **signal** | French's **operating** profitability, deflated by **book equity** | **gross** profitability, deflated by **assets** |
| **dataset** | Ken French's portfolio files | the Chen–Zimmermann public dataset |
| **cut** | deciles | quintiles |
| **controls** | positive control against **French's own annual block** (0.0333 pp over 62 years); sentinel census; a **control that FIRED** and was correctly re-stated | **13 negative + 5 positive controls**, one reproducing round 1's `A2` figure **exactly** (0.704 `t` 3.14 vs 0.70 `t` 3.14); an identity control at 1.8 × 10⁻¹⁴ |

**SAME QUESTION, SAME ERA, OPPOSITE VERDICTS, AND BOTH LANES CARRY FULL CONTROLS.** The differences
are **named, not ranked**: a different definition, a different dataset, a different cut.

**This is `C2`'s central finding happening to this campaign in real time rather than being read
about.** `C2` measured that dispersion across defensible constructions runs **68–96% of the premium
itself**, and that **the definition of the variable sits OUTSIDE the published grids** — so published
non-standard errors are a **lower bound** on what this programme hits. `F1` is the demonstration.

**Both readings stand. Nothing here selects between them.**

---

## 2. THREE CORRECTIONS TO THINGS THIS CAMPAIGN WAS CARRYING

### 2.1 Round 2's deflator collapse is an ANNUAL-frequency result

`B2`'s central negative — gross profitability's `t` falling from 3+ to **1.04–1.85** under a
lagged-asset deflator — **does not reproduce quarterly.** `C1` found Hou–Xue–Zhang measure both
frequencies **with one-quarter-lagged assets**:

| | annual | quarterly |
|---|---|---|
| gross profits / lagged assets | 0.16 **[t 1.04]** | **0.51 [t 3.40]** |
| operating profits / lagged assets | 0.20 [1.07] | **0.72 [3.35]** |
| **`CbOP`** — round 2's recommended definition | 0.53 [3.02] | **0.49 [3.02]** |

**`B2`'s finding stands as an annual result and is not contradicted — `C1` supplies the row `B2` did
not have. But the ranking inverts:** the definition round 2 recommended gains nothing from the
frequency, and the two it wrote off recover. `C1` also recovered **Novy-Marx's Table A6 in full**
(round 2 had only its prose): **the annual strategy is completely subsumed by the quarterly one**
(α −0.03, `t` −0.23) while **the quarterly earns α +0.42 [t 3.10] against the annual** — identical in
the 2012 draft and the published JFE, so the draft-versus-published check ran and passed.

### 2.2 `B2`'s attribution of the lagged deflator is wrong, and `B2` was carrying the disconfirming evidence

`B2` could not obtain Ball–Gerakos–Linnainmaa–Nikolaev's *Deflating profitability* — **four named
routes with byte counts, flagged as item 1 of its own "could not verify"** — and rested the
construction on **three second-hand restatements that agreed with each other.** `C1` obtained it and
read it in full: **it deflates by CURRENT assets, not lagged.**

> **CORRECTION, ADDED IN ROUND 4, AND IT IS MINE NOT `C1`'s.** This section originally said *"`C1`
> obtained it: the **2015 paper** deflates by CURRENT assets."* **`C1` read the 6 May 2014 Chicago
> Booth working paper**, which it tagged `[WORKING PAPER]`, cited by number, page count and URL, and
> listed **the published JFE 117(2) 2015 among the versions it could NOT verify** (its §9 item 6).
> **I collapsed the working paper into the published article in my own summary.** Round 4's `D3`
> caught it, and reports that **the published article has now failed in three consecutive rounds** —
> five routes logged with byte counts, including a Wayback **wrong-200 serving a 404 page at a `.pdf`
> URL**, with two bibliographic APIs both returning `closed`. **Everything this campaign holds from
> that paper is the 2014 working paper.** That distinction is exactly the draft-versus-published
> hazard this campaign has caught four times in other people's papers, and I made it myself in a
> record. `C1` was precise; the record was not.

**And `B2` had quoted the disconfirming evidence itself.** Its own line 183 carries the reference
implementation's code comment verbatim: *"OP 2016 JFE seems to lag assets, but 2015 JFE does not"* —
**which agrees with `C1`.** `B2` held two pieces of evidence pointing opposite ways and its headline
followed the restatements rather than the code comment it had quoted. **`B2` named the risk, the risk
materialised, and three independent restatements were wrong together.** The lane that closed it did so
by **getting the document** — the depth mandate's second requirement doing what it was written for.

### 2.3 `prevrpt` qualifies round 1's "point-in-time by construction"

`A1` established the Financial Statement Data Sets are PIT by construction — *"all numeric data is as
filed."* `C1` adds: the files carry **`prevrpt`**, which flags that a submission **was subsequently
amended**, so **a vintage file carries knowledge of its own future.** `C1` then measures it **unusable
as an amendment flag anyway** — 2.41% (2013q2) → 0.80% (2019q3) → **0.00% of 5,249 submissions
(2025q3)**. **The numeric data claim stands; one metadata column is hindsight.**

---

## 3. What each lane returned

### `C1` — the quarterly variant, and the lag

Beyond §2.1–§2.3: **five incompatible quarterly lag conventions spanning ~2.5 months, with one author
at both ends** — report-date+1 quarter in his 2013 paper, report-date+0 in his own 2023 toolkit code.
**The field's only public argument about it is a GitHub issue**, containing a retracted statistic, a
**measured 4.25% look-ahead rate**, the maintainer's note that the affected predictors *"have the
largest t-stats"*, and his reason for shipping a half-fix: *"I don't want to mess people up too much
who are already using the data."*

**Its own measurement, 839 MB of SEC as-filed data, six negative controls in both directions:** 10-Q
filing lag **p50 38–39 days, p90 45, p95 50**; HXZ's fourth month buys only **0.44–0.50pp of
coverage**. **But only 35.2% of 2025 10-Qs are accepted before 16:00 ET, with 47.9% landing in the
16:00 hour alone — so the binding constraint is the CLOCK, not the calendar.** That is round 1's
**57.5%** residual confirmed from a different direction and made worse.

**Quarterly computability is decisive: gross profitability 2,082 CIKs in 2025, operating profitability
1,066, `CbOP` NINE.** And the one-quarter-lagged deflator appears in only **3.5–5.3%** of filings —
Reg S-X gives the prior **fiscal year** end — so it needs a two-filing stitch costing **8–14% of the
cross-section.**

**Past the brief, and it is the lane's sharpest item: A SINGLE-QUARTER SORT IS AN UNADJUSTED SEASONAL
SORT.** The word *"season"* appears **zero times** in Novy-Marx 2013 (both versions) and zero times in
the 2025 retrospective; HXZ reach the point for `ROE` and **never apply it** to the gross-profitability
variant. Only a trailing-four-quarter form is seasonality-free. Also: **two quarterly placebos in one
reference repository have different missing-data semantics, one falsely documented as a line-by-line
translation.**

### `C2` — how much does the answer move

**The field measures this and it has a name: NON-STANDARD ERRORS, coined 2021.** The slate's own
overlap audit recorded **zero hits** for the term and for its lead author across all of `docs/` — and
**that zero was the most consequential gap in the campaign.** Both shapes the slate asked for exist:
**four many-analyst experiments** (including **164 teams** in the *JF*) and **six construction-grid
enumerations** (including **69,120 paths**).

**The dispersion is as wide as the premium.** Across 69,120 constructions of 68 sorting variables:
mean premium **0.28 %/mo**, non-standard error **0.19 (0.27 weighted)** — **68–96% of the premium.**
Positive in **90%** of paths, **significant in only 50%**, monotonic in 45%; for originally-significant
variables, 57%.

**Round 2's three nodes are ranked 1–3, and there are NINE MORE.** One ranked list puts **a
denominator change first** (mean |Δt| = **3.91**, largest of twelve).

> **CORRECTION, ADDED IN ROUND 4.** This record originally called that row *"the deflator… independently
> confirming `B2`"*. **It is not `B2`'s deflator.** `C2`'s own section heading is accurate — *"Corporate
> finance: Mitton's **Table 8**, average |Δt| over **65 real hypotheses**"* — but its mapping column said
> *"yes — `B2`'s deflator, ranked FIRST"*, and **I repeated that mapping.** A corporate-finance leverage
> regression's book-versus-market denominator is **not** assets-versus-lagged-assets. Round 4's `D3`
> found the right rows, in **Mitton's Table 7, the profitability column**: **`ROA`→`ROE`
> (assets→book equity) at |Δt| 12.31**, and **end-year→begin-year denominator (current→lagged) at
> 6.73**. **So the corrected evidence is STRONGER for `B2` than the figure I misattributed — 6.73, not
> 3.91 — and the 12.31 row is the assets-versus-equity node that bears on `F1`.** `C2`'s heading was
> right, its mapping over-claimed, and my summary repeated the over-claim. Second, and **absent from round 2 entirely: OUTLIER TREATMENT** (3.74; **12.86** on
quasi-random profitability ratios), where **winsorising vs trimming at the same cutoff** moves `t` by
0.99. The #1 node for profitability specifically is **dropping loss-makers**. New traps: rebalancing
frequency, **data vintage**, dividend-reinvestment timing inside the return series, level-vs-log,
stock-age filters, sort dependence. **One piece of good news: the `$5` floor is 13th of 14, worth
~2 bp/mo.**

**And it reproduced round 2's benchmark finding on free data, sharper.** The EW high-operating-
profitability long leg, 2010-01→2026-06: **+0.971 %/mo (`t` +2.46) against cash and −0.322 %/mo
(`t` −2.00) against the CAPM.** Same 198 months, same portfolio, **significant at 5% in both
directions.** `C2` names the mechanism rather than implying a result — an EW long leg over a bull
market carries β > 1, so *"against cash you are paid for the beta. Against the CAPM you are not."*
**THIS RECORD'S OWN NOTE: that is a statement about FUNDING, not a signal result**, and `C2` says so
itself, reporting the negative CAPM alpha in the same table and calling its grid *"a demonstration
that the published magnitudes reproduce on free data, not an independent estimate."*

**Five controls, four pass, and the fifth returned the WRONG ZERO and is reported.** `NC1` is a
**factor identity** — `RMW` rebuilt from the six size-OP portfolios matches the published series to
max |diff| **0.0050 pp/month over 757 months**. `NC5` predicted zero months outside its window and
**got one**: no measured number affected, **the expectation was wrong rather than the data, and the
control is what caught it.**

**Grid result:** **weighting alone** moves the full-sample tercile spread 0.224 → 0.079 and `t`
**2.37 → 0.74, straight across 1.96.** Range of means **0.167** against a midpoint of **0.163**.
**Zero sign flips in 24 cells** — `C2`'s honest negative: construction moved magnitude and
significance, not sign, **until the benchmark entered.**

**Past the brief:** **nobody reports the non-standard error of a NULL** — the one figure that exists is
a bootstrap critical value of **4.5 against a forking-paths value of ≥8.2, a 1.8× move in the critical
value**, where this programme prices sampling error to 2 SE (`CLAUDE.md:71`, verified) and prices
construction error **not at all**. **Data vintage is a dispersion no pre-registration closes** — a
third of long–short alphas lose significance on **factor vintage alone**, and one tape change
**rewrote 9.62% of monthly returns**. And **even at temperature zero, LLM-run analyses reach different
conclusions across 480 attempts** — recorded because an agent makes these choices here.

**The honest inversion is answered with objections to every remedy.** The sharpest is against
**averaging**: five mis-triaged binary nodes leave the justified region at **3%** of the multiverse.
**The only remedy with no published objection is free: name the nodes before the runner exists**,
because one paper's `t`-range grows at **1.42ⁿ** in free nodes. **That is this programme's own
[R8](../../RULES.md#r8) arriving from the outside.**

### `C3` — the shape of the drawdown

**The bar resolved in its second branch, and then the lane measured the missing number itself rather
than reporting the absence and stopping.** Absolute maximum drawdown of a long-only profitability
tilt, 1963-07→2026-07: **−52.2% value-weighted, −63.6% equal-weighted**, with the time-to-recovery
distributions the literature omits seven times out of eight.

**Seven published numbers reproduced before any new one was reported** — nobody asked for that, and it
is the right order.

**And a control FIRED and was handled correctly.** The drawdown of cumulative `RF` **must** be zero —
it was not, because **French's `RF` series has twelve negative monthly values, all pre-war.** `C3`
diagnosed it as a real data property, then **re-stated the control on the sample window**, where it
returns **exactly zero, zero episodes.** A self-test proven capable of failing. The positive control
compounds its own monthly deciles against **French's own annual block** to **0.0333 pp across 62
years**.

**The tilt decorates the drawdown rather than changing it.** Drawdown-path correlation with the market
is **0.79–0.98 for every one of the ten deciles**, and at the tilt's own worst trough **the market was
already −46.5% down.** **Full sample, the high-profitability EW decile is the worst long-only decile
in the sort bar junk:** maxDD **−63.63%** against the EW universe's −59.53%, **103 months underwater
against 43**, highest vol, highest beta (1.21), **and the smallest excess return.** Decile 5 beats the
universe by three times as much at β = 1.00. **And 0.5%/yr of cost erases the EW tilt entirely.**

**Three benchmarks, three answers, all computed:** excess of cash **`t` 3.73**; against the VW market
**`t` 2.08**; **against its own EW universe `t` 0.45.** *That is `C2`'s benchmark finding reproduced
independently, on a different construction, by a lane not told to look for it.*

**Two findings that cut the other way, recorded because they do.** The **flight to quality is real** —
the profitability factor beat the market by **+23 to +118 pp inside all six** of the market's worst
episodes, and the tilt's beta rises to **1.66** in the worst 20 market months — **but it lives
entirely in the leg unavailable to this book.** And **profitability's worst episodes are NOT value's**:
drawdown-path correlation **−0.142**.

**Past the brief:** realised drawdowns sit at only the **32nd–50th percentile of a 24-month
block-bootstrap null**; **mean drawdown is a Sharpe statistic, not a leg statistic** (corr 0.900);
concentration worsens drawdown **and** return together; and **monthly sampling understates depth by
only 2–4 pp** — which matters because this programme has daily bars and the literature does not.

### `C4` — is it already dead

**It is not dead. It never decayed — and all three reasons that is less good news than it sounds are
measured.** Gross profitability's post-publication long–short is **3× its in-sample return**, at the
**99th percentile** of 200 published predictors' decay distribution: in-sample **0.303 %/mo [t 2.39]**
— **reproducing Novy-Marx's own 0.31 [t 2.49]** — against **1.024 [t 2.65]** over 2014–2024. The same
pipeline puts the 200-predictor median post-pub ÷ in-sample ratio at **0.42**, **independently
reproducing the published 58% decline.**

1. **Two-thirds of the widening is in the SHORT leg — the side where borrow is excluded ground.**
   Against the VW market the long leg went **+0.187 → +0.179 %/mo [t 1.25]** — flat — while the short
   leg fell **−0.110 → −0.746 [t −3.52]**. **Drop 2023 and the long leg is +7.2 bp [t 0.50]; three of
   132 months carry half the total.**
2. **None of the five decay papers reports long-leg decay separately** (grep-verified on all five).
   **The 4 bp/month round 1 quoted is long–short, net-of-spread, post-publication AND post-2005 by
   construction.**
3. **Decay and era-dependence are unresolvable, and two sources say so.** `C4`'s own negative control:
   over 2013-07→2026-07, `HML` **−0.043**, `SMB` **−0.151**, `CMA` **−0.075** — **publication dates
   spanning 1981–2015, all dead in one window**, which no publication event explains. And gross
   profitability's own worst five-year blocks (1970–74, 1975–79, 2005–09) **all pre-date publication.**

**A draft-versus-published break in the field's founding decay paper** — the hazard the prompt flagged
as central to this lane, arriving exactly where predicted. Drafts (2012, 2013): **82 characteristics,
~10% out-of-sample decay explicitly "not statistically different from zero", 35% post-publication.**
Published 2016: **97, 26%, 58%.**

**Filed fund records contradict the backtests in large caps** — N-CSR filings, not factsheets, as
instructed. **QUAL −87 bp/yr over ten years, SPHQ −82, DUHP −124 since 2022 — and the indexes
themselves are −68 and −60, so it is not fees.** Only mid/small are positive (XMHQ +97, XSHQ +25) —
**and the catch only a full read would find: XMHQ's own filing discloses it tracked a DIFFERENT,
NON-QUALITY index until June 2019**, so its ten-year record is not ten years of this strategy.
Survivorship named with primary evidence — **Form 497 confirms OQAL liquidated February 2020** — and
`C4` **refuses to over-read it**, noting the issuer's entire single-factor suite went at once, **a
shelf event and not six verdicts.**

**It took the deflator past 2014 for the first time**, which round 2 could not: current-vs-lagged is
worth **+0.149 %/mo [t 1.83]** of long-leg alpha post-publication, **and the lagged convention still
gives +0.256 [t 2.23].**

**Thirteen negative and five positive controls** — including one reproducing round 1's `A2` **exactly**
(0.704 `t` 3.14 vs 0.70 `t` 3.14), a cross-lane replication across two rounds, and an identity control
at **1.8 × 10⁻¹⁴** proving the own-universe benchmark is arithmetically what it claims.

**BUT THE TWO THINGS THAT CHANGED `C4`'s ANSWER WERE NOT ON THAT LIST, AND `C4` SAYS SO IN THOSE
WORDS.** The first was **computing the long leg against two benchmarks rather than one**: against the
VW market **−0.125 [t −0.49]**, against its own EW universe **+0.405 [t 3.00]**. *"A single-benchmark
measurement here would have shipped the wrong sign, and nothing in the control table above would have
caught it — because both measurements are arithmetically correct."* The second was **testing its own
mechanism rather than filing it**: the correlation with the asset-growth anomaly's tradeable leg is
**−0.106 / −0.294**, so **the 15 bp is UNEXPLAINED, not explained.**

**Also after the bar:** French's 25 size × OP table through 2026-07 shows the profitability spread
**going to zero post-2013 in every size quintile but the largest** — **opposite** to `C4`'s own result
on the other dataset — and `C4` **resolves it on definition rather than declaring one wrong.**

---

## 4. CONFLICTS — RECORDED, NOT ADJUDICATED

| | the conflict | readings |
|---|---|---|
| **F1** | **Does an EW profitability long leg beat its own EW universe?** | **`C3`: NO** — +0.026 %/mo, `t` 0.45, 1,235 years to `t` = 2; worth nothing in the programme's era and with a deeper drawdown than the universe. **`C4`: YES** — +0.405 [t 3.00] post-publication, +0.379 [t 3.56] over 2010–2024. **Different definition, dataset and cut, all named. Both lanes fully controlled. BOTH STAND** — and this is `C2`'s finding happening to this campaign rather than being read about. |
| **F2** | **Does the lagged deflator kill gross profitability?** | **`B2` (round 2): annual, YES** — `t` falls to 1.04–1.85. **`C1`: quarterly, NO** — 0.51 [t 3.40] with one-quarter-lagged assets. **`C4`: post-2014, NO** — lagged still gives +0.256 [t 2.23]. **Not a contradiction but a scope finding: `B2`'s result is annual and pre-2014. All three stand.** |
| **F3** | **Which assets does *Deflating profitability* deflate by?** | **`B2`:** lagged, *"specifies in its own appendix"*, from **three second-hand restatements** after failing to obtain the paper by four named routes. **`C1`, having obtained it:** **CURRENT assets.** **`B2`'s own quoted code comment agrees with `C1`.** Recorded as a correction with its provenance intact, because `B2` flagged exactly this risk. |
| **F4** | **Is the FF profitability spread alive post-2013?** | **`C4` on French's 25 size × OP:** **zero in every size quintile but the largest.** **`C4` on the Chen–Zimmermann files:** alive and widening. **Same lane, two datasets, opposite answers**, which `C4` resolves **on definition** and does not rank. |
| **F5** | **How large is post-publication decay?** | **The founding paper's drafts (2012/13):** 82 characteristics, **~10% out-of-sample decay "not statistically different from zero"**, 35% post-publication. **Its 2016 publication:** 97, **26%**, **58%**. `C4` reproduces the 58% independently at 0.42. **Both versions stand on the record.** |
| **F6** | **Is it decay or is it the era?** | **The decay camp:** a publication-dated decline. **One abstract concedes:** *"partly explained by a general time trend."* **`C4`'s control:** three factors published 1981–2015 are **all dead in one window**, and gross profitability's worst five-year blocks **pre-date** publication. **Recorded unresolved; `C4` says the evidence cannot separate them.** |
| **F7** | **Menkveld's own conclusion vs its own table.** | `C2` records a paper's stated conclusion **flipping the sign of its own table's median**, and a **9% vs 53.5% swing on one winsorization choice between the draft and published versions of the paper that invented the term** — the field's #2 node biting the field's founding paper. **Both stand.** |

**Round 2's `E1`–`E11` and round 1's `D1`–`D10` all still stand.**

### 4a. AND EVERY LANE RECORDS FURTHER CONFLICTS INSIDE ITS OWN BRIEF — pointers, so none is invisible

**`F1`–`F7` are the CROSS-LANE conflicts. They are not all of them.** Each brief carries conflicts this
record does not restate, and they are listed here by location so a reader of the record knows they exist:

| lane | where | carries |
|---|---|---|
| `C1` | [§4.3](R3-01-the-quarterly-variant-and-the-lag.md) *"The conflict, recorded and not adjudicated"* | the five incompatible quarterly lag conventions, **with one author at both ends** |
| `C2` | [§9](R3-02-how-much-does-the-answer-move.md) *"CONFLICTS, RECORDED AND NOT ADJUDICATED"* | **five**, including whether data vintage changes conclusions or only adds noise; whether equal-weighting **raises or lowers** the premium; and *"sign is remarkably stable"* **against the same paper's own tables** |
| `C3` | [§10](R3-03-the-shape-of-the-drawdown.md) *"CONFLICTS, RECORDED AND NOT ADJUDICATED"* | whether the **long leg or the spread** has the worse drawdown — two sources give **opposite orderings** (−8.2% vs −3.9% one way, −10.5% vs −24.2% the other), which `C3` dissolves by showing **mean drawdown is a Sharpe statistic and neither paper says so**, while leaving both on the record |
| `C4` | [§6.4](R3-04-is-it-already-dead.md) | **its own two datasets contradicting each other** (= `F4`), resolved on definition and not ranked |

**Nothing is deleted, nothing is merged away, and where a lane supplies a mechanism that dissolves a
conflict, BOTH READINGS STILL STAND BESIDE IT.**

---

## 5. MY OWN WRONG PREMISES THIS ROUND, RECORDED AS MINE

1. **I wrote the overlap audit's zero hits as evidence the lane was clear, when the same zero was
   evidence the programme had never touched the field.** `non-standard error` **0**, `Menkveld` **0** —
   I recorded both in [`R3-00-slate.md`](R3-00-slate.md) as clearance. `C2` found a named literature,
   dated 2021, with four many-analyst experiments and six construction grids, whose **#1 ranked node is
   the one round 2 had just rediscovered the hard way.** **A zero hit count means the lane does not
   overlap. It does not mean the question is new.** Those are different facts and I conflated them.
2. **I framed round 2's deflator collapse as a property of the family, and it is a property of the
   annual frequency.** The `C1` prompt told the lane to check whether the quarterly advantage *"survives
   the deflator convention"* as though the convention were the settled part. **It was the frequency that
   was unexamined**, and `C1` found the collapse does not reproduce quarterly.
3. **I priced round 3 at ~1.1M and it cost ~1.44M.** §0. The depth mandate raised per-lane spend **11–36%**
   and took the round **above the schema's own projected band**. The band in
   [`00-SCHEMA.md`](00-SCHEMA.md) §2 was measured before the mandate existed and **§6 below updates it
   rather than leaving a stale number in the contract.**

---

## 6. WHERE THE EXTRA SPEND WENT — so the next round can be priced honestly

**The mandate's five requirements are not equally expensive, and the round shows which paid.**

| requirement | what it bought |
|---|---|
| **"the bar is a floor, not a target"** | `C3` measured the absent number instead of reporting the absence. `C4`'s two answer-changing findings both came **after** its bar. `C1`'s seasonality finding is post-bar. **This is the requirement that paid.** |
| **"read in full; chase the appendix, the repository, the code"** | `C1` **obtained the paper round 2 failed on by four routes**, correcting `F3`. `C3` independently obtained the text `A3` was refused. `C4` read **filed N-CSRs** and caught an index change a factsheet would never disclose. |
| **"one independent measurement with a negative control"** | Every lane. **`C2`'s NC5 and `C3`'s `RF` control both FIRED** — and a control that can fire is the only kind worth having. |
| **"go past the sub-questions"** | `C2`'s NSE-of-a-null; `C3`'s block-bootstrap null; `C1`'s seasonal sort; `C4`'s own-mechanism test. **None commissioned.** |
| **"what I did not open"** | `C3` 14 items, `C4` 18. **Cheap, and it is the only requirement that makes the unexplored edge visible.** |

**Revised expectation for a four-lane round under the mandate: ~1.3–1.5M**, not 1.0–1.4M.

---

## 7. What this record does not claim

**Nothing here was measured on this programme's fixture.** Every measurement is on Ken French's public
files, the Chen–Zimmermann public dataset, SEC public products, or filed fund reports — **no `$5`
floor, no trailing dollar-volume screen, no dead-name inclusion, no overnight decomposition, and not
one of this programme's own bars.** **No backtest was run, no null drawn on our data, no candidate
exists, no territory is closed, and NO AVENUE IS CLOSED** ([R15](../../RULES.md#r15): only the
principal closes an avenue).

**`C3`'s and `C4`'s results point opposite ways and neither is adopted.** The negative reading is not
a verdict and the positive reading is not a green light. **Both books are unchanged**,
[`FINDINGS.md`](../../FINDINGS.md) and [`PICKUP.md`](../../../PICKUP.md) are untouched, **and nothing
in this folder is elevated out of `docs/research/`.**
