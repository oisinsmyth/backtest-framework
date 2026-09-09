# F1 — index reconstitution and forced index flows: external evidence

*Compiled 2026-09-09. Research only: nothing was run, no fixture was touched, no file outside this
one was written. Every numeric claim is tagged to a source in §10. Where I could not verify
something I say so in the line itself.*

***Provenance discipline, because the round-2 quarantine contract requires it.*** *Four PDFs —
Greenwood & Sammon in the Dec 2022 NBER and Nov 2023 HBS vintages, Tasitsiomi (arXiv 2506.21775),
and the Columbia ML paper — were **read at source**, by extracting the text of the downloaded file;
every table transcribed in §2 and §4.2 comes from those files directly. Everything marked*
`[NOT READ AT SOURCE]` *is from an abstract, a citation inside another paper, or a search summary,
and should be read at source before it is quoted in a decision record. §3 (Russell rules and the
Russell literature) and §6 (data) were researched in parallel by two agents; their URLs, HTTP status
probes and row counts I have carried through, but **their readings of papers are summaries and are
marked as such** — §3.2 and §3.4 in particular rest on citations, not on the papers themselves.*

---

## 1. Verdict

**The premise that selected this territory is inverted by the evidence, and that is the whole
result.** F1 was commissioned because index reconstitution is route (a) — a mandate-driven,
date-known, price-insensitive buyer — **"in LARGE, LIQUID, HIGH-PRICED names, which is the one
population its per-share cost model can actually trade."** The literature says the large liquid
population is exactly where the effect is dead, and the places it survives are exactly where this
programme cannot go. Four findings converge. (i) **The user's second-hand figure is real and I
found the source.** Greenwood & Sammon, *Journal of Finance* 80(2), April 2025 — the published
abstract is 7.4% in the 1990s → **0.3%** for S&P 500 additions over 2010-2020, and for deletions
large negatives in the 1990s → **+0.1%**, i.e. deletions now go *up* on average. The
"7.6% → 0.8%" version the user was quoting is the earlier NBER/HBS working-paper vintage; both are
correct, they are different revisions, and §2 gives both. (ii) **But the S&P 500 average conceals
a live sub-population, and this is the single most important thing in this brief.** In the same
paper, 2010-2020, **DIRECT** additions (from outside the S&P 1500) still average **+5.40%** and
direct deletions **−6.86%**; **MIGRATIONS** between S&P indices average **−1.82%** and **+0.06%**.
Migrations rose from ~40% to **over 80%** of changes, and they are what dragged the average to
zero — because S&P 500 tracker buying is offset by S&P MidCap tracker selling. The effect did not
disappear so much as it was *netted out by index design*. (iii) **The surviving effects are
small-cap.** The same paper's Table 8, 2010s, statistically significant: S&P SmallCap 600 direct
additions **+6.03%** (SE 0.735), SmallCap direct deletions **−12.18%** (SE 1.606), MidCap
additions **+5.67%** (SE 1.123), Russell 2000 direct additions **+3.15%** (SE 1.421). The
insignificant ones are the large-cap ones: Russell 1000 direct additions +8.53% (SE 5.114, t=1.67)
and Nasdaq 100 additions +1.98% (SE 1.140). **This is the opposite of the territory's premise.**
(iv) **Every one of those numbers is gross, measured over a window that partly precedes the
announcement, and computed on a sample that explicitly deletes the dying names.** Greenwood &
Sammon exclude firms "delisted for reasons other than an acquisition" within 100 days — which
removes about **two-thirds of all S&P 500 deletions** (Table A1: drops sample averages 34%
included) — and for the Russell they say outright that they *"do not consider deletions from the
Russell 3000 to outside the Russell 3000 universe, as these are often firms that are delisting."*
**The one population this fixture uniquely holds is the one population the literature deliberately
throws away.** That is a genuine gap, it is the only defensible thing F1 could build, and §5 and
§8 explain why the $5 floor probably closes it anyway.

**On data, the answer is yes and it is better than expected:** free, dead-inclusive S&P 500 change
history with **both announcement and effective dates** covering 2010-2026 does exist — the
`press.spglobal.com` release archive from 2012, plus PR Newswire releases enumerated through the
Wayback CDX API for 2010-2011, with Wikipedia's *Historical components* table as the skeleton. It is
a scrape of several hundred pages, not a download, and Siblis sells the same thing for ~$576/yr.
**For Russell there is no free announcement-date archive and no name lists before ~2015.** Full
detail, with the traps, in §6. Note for anyone who reaches for the obvious link: *List of S&P 500
companies* is now a **current-members-only** page and is exactly the useless kind — its revision
history is the useful part.

**Disposition I would defend: do not build a reconstitution study for the stated reason.** The
large-liquid case is dead and the surviving case is small, cheap, wide-spread and mostly outside
the fixture's floor. If anything here is pursued it should be the *direct-vs-migration* split on
S&P 500 changes, and §9 gives the one number that decides it before any runner exists.

---

## 2. The index effect and its decay

### 2.1 The decay figure, sourced

**The user's figure is supported. Here is the provenance, in three vintages of the same paper.**

| vintage | additions 1980s | 1990s | 2000s | 2010-2020 | deletions 1990s | deletions 2010-2020 |
|---|---|---|---|---|---|---|
| NBER w30748 / SSRN 4294297, **Dec 2022** | 3.4% | **7.6%** | 5.2% | **0.8%** | −16.6% | **−0.6%** |
| HBS WP 23-025, **revised Nov 2023** (abstract) | — | **7.4%** | — | **0.3%** | "large negative" | **+0.1%** |
| *Journal of Finance* **80(2), April 2025, 657-698** (published abstract) | — | **7.4%** | — | **0.3%** | "large negative" | **+0.1%** |

Read the last row carefully: the published deletion figure is **+0.1%**, positive. Deletions in
2010-2020 did not fall on average — they drifted marginally up. I read the Dec 2022 and Nov 2023
PDFs at source; the JF abstract I have from the Wiley/HBS listing, not from the published PDF
(paywalled, 403) [NOT READ AT SOURCE]. **Cite the JF version and say which vintage you are
quoting** — the two differ by 0.5pp on additions and by a sign on deletions, and a record that
mixes them will not reconcile.

Sample and universe, from the paper: **1980-2020**, S&P 500 additions and deletions, membership
list from **Siblis Research** matched to CRSP, index-tracker holdings from Thomson S12. Returns
are **market-adjusted** (stock minus CRSP value-weighted index). Three windows are reported
throughout: *announcement* (day before → day after announcement), *effective* (day before → day
after implementation), and *total* (day before announcement → day after implementation).

### 2.2 The announcement-to-effective structure, which is what decides tradability

From the Dec 2022 working paper, Table 2 (decade regressions on a constant, robust SEs). This
table is not in the same form in the Nov 2023 revision, so it is the WP vintage. Significance stamp
in backticks: `***`/`**`/`*` = 1/5/10%, `ns` = not significant.

| | 1980-89 | 1990-99 | 2000-09 | **2010-2020** | N (2010-20) |
|---|---|---|---|---|---|
| Additions — total | 3.42% `***` | 7.59% `***` | 5.21% `***` | **0.799%** (SE 0.006, t≈1.3) `ns` | 150 |
| Additions — announcement | 3.36% `***` | 5.15% `***` | 4.13% `***` | **1.05%** (SE 0.004, t≈2.6) `***` | |
| Additions — effective | 3.44% `***` | 3.68% `***` | 1.32% `***` | **0.209%** (SE 0.002, t≈1.0) `ns` | |
| Deletions — total | −4.64% `**` | −16.6% `***` | −12.3% `***` | **−0.603%** `ns` | 87 |
| Deletions — announcement | −4.71% `**` | −14.4% `***` | −10.1% `***` | **−0.2%** `ns` | |
| Deletions — effective | −4.65% `**` | −8.64% `***` | −4.34% `**` | **+0.2%** `ns` | |

**This decomposition is the kill on the naive trade and it should be quoted whenever the "index
effect" is raised.** In 2010-2020 the only statistically significant residual is the
**announcement** return, +1.05% — and the announcement window runs from the day *before* the
announcement, so capturing it requires already holding the name before S&P says anything. The
**effective** window — announcement close → day after implementation, which is the only part that
is genuinely date-known, forced, and public — is **+0.209% and insignificant**, down from +3.68%
in the 1990s. *The forced-flow leg is the leg that died.* Whatever is left lives in the
information jump, not in the flow.

### 2.3 Why it decayed — five explanations, and the one that actually carries the weight

Greenwood & Sammon test five and conclude for two:

1. **Changing composition** (size/volume/volatility of the names being added). Regression-based
   Fama-French-2001-style decomposition: accounts for only a small part. The 1990s→2010s decline
   is 6.6% raw vs 5.6% after conditioning on characteristics — "still economically large and
   statistically significant."
2. **Increased average liquidity.** Value-weighted effective spread (Holden-Jacobson off TAQ) fell
   **60bp → 6bp**, a factor of 10. But net tracker buying grew by a factor of **6-7**, so this
   nets to a small predicted decline, not the observed one; and the timing is wrong — most of the
   spread decline was mid-1990s to mid-2000s, most of the effect decline was mid-2000s to late
   2010s. Virtu implementation shortfall for institutional trades is **roughly flat** over the
   sample, which if used instead predicts an *increasing* index effect.
3. **Migrations — carries real weight.** See §2.4.
4. **Front-running / predictability — small role.** Mixed evidence. Pre-announcement CARs (Table
   4) for additions in the **(−20,−1)** window: 0.008 (1980s), 0.022 (1990s), 0.020 (2000s),
   **0.025 (2010s)** — essentially no increase in the window where front-running would show. The
   **(−100,−1)** window does rise, 6.9% → 19.3%, but the authors say this is confounded by
   selection: *"S&P 500 has become better at adding the best performing stocks."* Their own
   summary: *"which precise stocks get added are still difficult to predict."*
5. **Increased liquidity provision at the event — carries real weight.** The implied multiplier
   **M fell by a factor of ~20** for additions and more for deletions. Volume concentration on the
   effective date went from **15% → almost 30%** of the surrounding month's volume. And the
   decisive observation: index trackers now buy **7-8% of shares outstanding** on addition, yet
   *total institutional ownership barely moves* — active institutions are standing ready to sell
   into it. Their framing is Lo's adaptive markets and McLean-Pontiff post-publication decay.

### 2.4 Migrations — the mechanism, and the surviving sub-population

An S&P 500 change is a **migration** when the name moves between the S&P MidCap 400 and the
S&P 500 (example given: TRGP, dropped from MidCap and added to S&P 500 on 2022-10-06), versus a
**direct** change from outside the S&P 1500 (example: PCG added 2022-10-03). On a migration,
500-tracker buying is met by MidCap-tracker selling; MidCap passive ownership has grown to about
**6% of MidCap capitalisation**, slightly *more* than the S&P 500's own tracker share.
Migrations went from **~40% of additions in the 1990s to over 80%**.

**Table 3, Nov 2023 revision — the number that reframes this whole territory:**

| | Additions: direct | Additions: migration | Diff (SE) | Deletions: direct | Deletions: migration | Diff (SE) |
|---|---|---|---|---|---|---|
| 1995-1999 | **10.23%** | 6.65% | −3.58% (2.12%) | **−12.78%** | −0.17% | 12.61% (7.82%) |
| 2000-2009 | **8.80%** | 2.72% | −6.07% (1.34%) | **−15.71%** | −4.10% | 11.61% (6.29%) |
| **2010-2020** | **5.40%** | **−1.82%** | **−7.22% (0.99%)** | **−6.86%** | **+0.06%** | 6.92% (4.15%) |

**A caveat I am obliged to flag and could not resolve.** The table's caption says the
parenthesised figures are standard errors, but the level figures cannot be: 1995-1999 direct
additions carry (7.69%) and migrations (10.41%) while their *difference* carries (2.12%), and a
difference of two independent means cannot have a smaller SE than either component. My reading is
that the level parentheses are cross-sectional **standard deviations** and only the Diff column is
a true SE. If that reading is right, the direct-vs-migration **gap** is solidly significant in all
three periods and the *levels* have not been given usable errors. If the caption is literally
right, then +5.40% (SE 8.38%) is t=0.64 and nothing in the levels is significant. **This matters
enormously for whether §9 is worth computing, and it can only be settled by reading the published
JF table.** [NOT READ AT SOURCE — Wiley 403.]

**What is not in doubt** is the direction and the mechanism: the near-zero S&P 500 average is a
*composition* result. Over 80% of modern changes are migrations that net out by construction. The
~20% that are direct still carry a large point estimate.

### 2.5 Independent corroboration and the index provider's own admission

- **Bennett, Stulz & Wang** (NBER w27593 / SSRN 3656628, 2020), *Does Joining the S&P 500 Index
  Hurt Firms?* — sample **1997-2017**. Greenwood & Sammon credit them with first noting the
  decline. Their statement is stronger: *the positive announcement effect has disappeared and the
  long-run impact of inclusion has become negative*, alongside worse price informativeness, falling
  ROA and governance changes. [NOT READ AT SOURCE — abstract only.]
- **S&P Dow Jones Indices**, *What Happened to the Index Effect? A Look at Three Decades of S&P 500
  Adds and Drops* — the index provider's own research, sample reported as **start of 1995 to June
  2021**, concluding the index effect is in **structural decline** and attributing it partly to
  improved stock liquidity. [SALES INSTRUMENT — but self-incriminating, which is why it is worth
  citing.] [NOT READ AT SOURCE — spglobal.com returned 403 on both the PDF and the article page;
  the sample period and conclusion are from search summaries and I could not confirm S&P's own
  sub-period magnitudes. Preston & Soe (2021) is the underlying citation Greenwood & Sammon give.]
- **Petajisto** (2011, *Journal of Empirical Finance* 18(2) 270-282), *The Index Premium and Its
  Hidden Cost for Index Funds* — sample **1990-2005**; index premium measured announcement→effective;
  cost to index funds **21-28 bp/yr** for the S&P 500. Historical baseline only. [NOT READ AT SOURCE.]

---

## 3. The Russell reconstitution

### 3.1 The current rules — and two details that are commonly got wrong

Reconstitution became **semi-annual** and the rules changed materially in 2026. From the FTSE
Russell ground rules, *Russell US Equity Indexes Construction & Methodology v7.2, August 2026*
[PRIMARY DATA DOC], Rule 4.2.3: *"Reconstitution occurs on the fourth Friday in June and the second
Friday in December."* Appendix F:

| | **June** | **December** |
|---|---|---|
| Rank day | **last business day of April** | last business day of October |
| Preliminary lists released | **five weeks** before implementation | four weeks before |
| Query period | 2 weeks after preliminary | 2 weeks after preliminary |
| Implementation | **4th Friday of June**, after the close | **2nd Friday of December**, after the close |

**2026 actuals** [PRIMARY DATA DOC, LSEG]: rank **30 Apr 2026**; preliminary **22 May 2026**;
updates **29 May, 5 Jun, 12 Jun, 18 Jun**; effective after close **Fri 26 Jun 2026**, trading from
the open **Mon 29 Jun 2026**. December 2026: rank **30 Oct**, preliminary **13 Nov**, updates
**20 Nov, 27 Nov, 4 Dec**, effective after close **11 Dec 2026**.

**Two traps.** (a) The semi-annual change was announced **16 Jan 2025** specifying the second event
in **November**; a **December 2025** revision moved it to **December**. A rules table built from the
January 2025 announcement encodes the wrong month. (b) **Rank day for the June event moved from
May to the last business day of April** — an ~8-week rank-to-effective gap, against ~7 weeks under
the 2015-2025 mid-May rule and ~4 weeks before 2015. Any "predict membership at rank day" design
inherits a different gap depending on the year.

**December is not a full reconstitution**: float adjustments are applied with a 3% buffer, style
scores update only for new adds and R1000↔R2000/Microcap movers, and voting-rights research is not
re-run on existing members. Published total shares carry a **1% buffer**, so index files do not
equal true shares outstanding.

**Historical rule** [PEER-REVIEWED, JF *Replications & Corrigenda*] — Ben-David, Franzoni &
Moussawi (2019) publish a **full FTSE-Russell-supplied calendar of rank / preliminary / effective
dates 1989-2019**, which is the single most useful artefact for building a historical fixture:
annual after June 1989; effective = final business day of June until 2004, then last Friday in
June; **rank date = final trading day of May until 2015, then mid-May**. Ranking uses **total,
NON-float-adjusted** market cap; index *weights* are float-adjusted. Russell only began publishing
the ranking market-cap data in **2012**.

**Banding**, introduced **2007** [PRIMARY DATA DOC, methodology §6.10-6.11]: at the R1000/R2000
breakpoint the band is **±2.5% of cumulative R3000E market-cap percentile** (5 percentile points
wide), *not* dollars and not ranks. Critically it is asymmetric — *"Banding only applies to members
of the Russell 3000. Therefore, members of the Russell Microcap, ex-Russell 2000, are treated as
new adds and not subject to banding."* Incumbency is protected; entry is not. **Effect on
turnover**: R1000↔R2000 switchers averaged **182.4/year over 1991-2006** and **66.1/year over
2007-2020** — banding cut migration by ~64%.

**IPOs** [PRIMARY DATA DOC §4.3, §6.9]: quarterly rank on the last business day of Jan/Apr/Jul/Oct;
March and September additions announced four weeks prior, effective after the close of the **third
Friday**; June and December IPO adds fold into the semi-annual events. A new **fast-entry**
framework admits sizeable IPOs at the scheduled rebalance but requires a **fully guaranteed**
offering — variable, best-efforts and **direct listings are not eligible**. Other encodable gates:
close **≥ $1.00** on rank day, total market cap **≥ $30m**, minimum 5% float and 5% voting rights.

### 3.2 The June price pattern as documented

- **Madhavan (2003)**, *The Russell Reconstitution Effect*, *Financial Analysts Journal* 59(4)
  51-64 [PEER-REVIEWED]. Sample **1996-2002**, annual reconstitutions. **R2000 additions: temporary
  price impact 5.79%, permanent 1.41%** — the transitory component is ~4× the permanent one.
  Long-additions/short-deletions on the Russell 3000: **mean June return 14.94%**. Framed as a cost
  to index funds, with the explicit corollary that supplying immediacy then is profitable.
  **This is the number everyone quotes and it is a 1996-2002, pre-banding, pre-2015-rank-day,
  pre-2026-semi-annual sample. Every structural feature it was measured under has since changed.**
  [NOT READ AT SOURCE.]
- **Chang, Hong & Liskovich (2015)**, *RFS* 28(1) 212-246 [PEER-REVIEWED]. Sample **1996-2012**.
  RD at the 1000th rank; because both indexes are value-weighted, far more indexed money tracks the
  largest R2000 names than the smallest R1000 names, so crossing down is a demand *increase*.
  **~5% addition/deletion effect, implied demand elasticity −1.5.** [NOT READ AT SOURCE — SSRN 403;
  figures via Wei & Young's and Ben-David et al.'s direct citations.]
- **Greenwood & Sammon Table 8**, Nov 2023 revision — see §4. This is the only decade-by-decade
  Russell series I found and it is *in the same paper* as the S&P 500 result.

### 3.3 Predictability of membership ahead of rank day

Russell is **mechanical**; S&P 500 is **committee-discretionary** (the eligibility screen —
~$20bn+ minimum market cap as of 2025, ≥50% public float, positive most-recent-quarter and positive
trailing-four-quarter GAAP earnings, adequate volume, major-exchange listing — produces an
eligibility *list*, and the Index Committee then chooses). So Russell membership is far more
predictable in principle.

**Ben-David, Franzoni & Moussawi (2019)** build the best public proxy for Russell's proprietary
ranking variable (CRSP company-level, plus Compustat Securities Daily aggregated at GVKEY for
non-public share classes, plus CSHOQ where classes are closely held) and report **61 misclassified
R1000/R2000 assignments in total over 2000-2006** — a low error rate, beating CRSP-only and
Compustat-only proxies in every year. Named failure cases: multi-share-class companies and
**spin-offs**.

**Read that correctly.** It is a **pre-banding** sample; the residual errors concentrate exactly at
the cutoff where the trade would be; and since 2007 predicting the *rank* is not predicting the
*migration*, because incumbency inside a ±2.5-percentile band overrides the rank. Also: **since
2007 the preliminary list is published weeks before it trades.** Membership is not a secret to be
predicted — it is public for **five weeks** (June) or **four weeks** (December) before the event.
This is not a prediction problem.

An arXiv student paper — *Hunting Tomorrow's Leaders: Using Machine Learning to Forecast S&P 500
Additions & Removal* (Agrawal, Khalid, Tan, Xu, Columbia, arXiv 2412.12539) — claims a Random
Forest **test F1 of 0.85** on quarterly WRDS data from 2013. [WORKING PAPER, not peer-reviewed.]
**I would discard it.** An F1 of 0.85 on a problem where ~23 of ~3,000 names are added per year is
extraordinary and far more likely reflects class rebalancing or leakage than skill; the paper
reports no backtest, no costs and no out-of-sample P&L — its trading section says only that the
authors *"anticipate capturing alpha."* Noted for completeness, not as evidence.

### 3.4 The identification critique — the strongest published negative on Russell

**Wei & Young**, *Selection Bias or Treatment Effect? A Re-Examination of Russell 1000/2000 Index
Reconstitution*, **Critical Finance Review 13(1-2), 83-115** [PEER-REVIEWED]. Sample **1996-2006**
(they stop at 2006 *because banding starts in 2007*).

The finding: researchers imputed the RD assignment variable from **Russell's published June index
weights**, which are **float-adjusted** and measured a month *after* rank day — and are **not the
variable Russell assigns on** (non-float-adjusted total market cap at end of May). Their abstract:
*"lagged institutional ownership measured prior to reconstitution exhibits very similar pre-existing
differences at the 1000/2000 cutoff, and thus the results ... reflect selection bias instead of a
treatment effect."* Firms at the top of the R2000 were already significantly smaller at end-May and
had significantly more publicly available shares — **the float adjustment was doing the sorting**.
With a researcher-constructed end-of-May ranking, **no significant discontinuity in institutional
ownership** survives. A secondary result: the received wisdom that the fuzzy-RD *first stage* is
weak is wrong (Kleibergen-Paap F up to 299.96); the null second stage is left unexplained.

**Scope discipline — do not overstate this.** Wei & Young's dependent variable is **institutional
ownership**, and their targets are corporate-finance papers. They do **not** re-run Chang-Hong-
Liskovich's *price* regressions and do not claim the ~5% price effect is fake. What they establish
is that the standard apparatus is contaminated by **float-driven selection**, which is a serious
prior against price results estimated the same way — an inference, not their demonstrated result.

Companion: **Appel, Gormley & Keim**, *Identification Using Russell 1000/2000 Index Assignments*,
CFR 13(1-2) [PEER-REVIEWED] — sharp-RD estimators are biased, fuzzy-RD and IV are not; and the 2007
banding change **requires modifications to the existing methodologies**. Ben-David et al. put it
bluntly: *"The banding approach precludes the possibility of implementing a fuzzy regression
discontinuity design because it eliminates any meaningful variation around the cutoff."*
**Nearly the whole RD literature therefore stops in 2006, and any post-2006 claim borrowed from it
is out of sample.**

### 3.5 The reversal, and the volume paradox

- **Onayev & Zdorovtsov**, *Russell Reconstitution Effect Revisited* (EFMA 2007 / SSRN 960727)
  [WORKING PAPER, **UNVERIFIED — could not retrieve; TLS failure at EFMA, 403 at SSRN**]. Reported:
  the effect **weakens in more recent years**, price-pressure reversal "much smaller to nonexistent";
  **after 2002 the effect weakened**, attributed to both speculative trading and Russell's own
  methodology changes. Reported asymmetry worth remembering: **deletions are sold far ahead of,
  during and long after the event, while addition trading concentrates near the event date.**
  If this is right, the "buy in May, sell after June" reversal was already decaying by 2002-2007 —
  before banding, before the 2015 rank-day change, two decades before the current rules.
- **Chinco & Sammon**, *Excess Reconstitution-Day Volume* (SSRN 3991200, Mar 2022) [WORKING PAPER].
  Sample **2001-2020**, R1000/R2000 switchers. For every share ETFs trade on reconstitution day, an
  extra **3.15 shares** trade; ETF rebalancing alone would raise a switcher's volume 139%, actual is
  **439%**. Excess reconstitution-day volume averages **$14.5bn on that one day** across ~66 annual
  switchers. **And switcher volume does not rise at all in the two weeks before reconstitution
  day**, despite the public preliminary list. Almost all reconstitution trading occurs **in the
  closing auction**.

**The volume paradox is the point, and it cuts against the trade.** Enormous and still-growing
event volume coexists with declining price effects. Volume here is not opportunity — it is the
count of competitors, and Greenwood & Sammon's mechanism (active institutions standing ready to
sell into tracker demand) is exactly what that volume is.

---

## 4. Does anything survive post-2010? — the decisive section

**Yes — but not where this territory was pointed, and not on any number that has been netted of
costs.** The honest answer has three parts.

### 4.1 The S&P 500 average is dead, and the forced-flow leg is the deadest part

Restating §2.2 because it is the answer to the question as asked: in **2010-2020**, S&P 500
additions returned **+0.209% (insignificant)** over the announcement→effective window — the only
window that is date-known, public and mechanically forced. Deletions returned **+0.2%
(insignificant)** over the same window. **The tradeable leg of the S&P 500 index effect is gone.**
The one significant residual, the +1.05% announcement return, requires holding the name before an
announcement that the paper's own authors say is *"still difficult to predict"* because the S&P
Index Committee exercises genuine discretion.

### 4.2 What does survive: Greenwood & Sammon Table 8, Nov 2023 revision

This table is the most valuable thing in this brief. It is the *same* authors, *same* methodology,
applied to five other index families. Standard errors clustered by year; `***`/`**`/`*` = 1/5/10%.

| | R1000 add | R2000 add | MidCap add | MidCap del | SmallCap add | SmallCap del | NDX add | NDX del | All add | All del |
|---|---|---|---|---|---|---|---|---|---|---|
| 1990s | 1.011 (1.317) `ns` | 2.215 (1.238) `*` | 5.624 (1.591) `***` | −4.528 (1.777) `**` | 6.342 (1.032) `***` | −6.694 (0.640) `***` | 3.876 (3.276) `ns` | 0.171 (1.537) `ns` | 2.459 (1.275) `*` | −2.603 (0.203) `***` |
| 2000s | 16.973 (9.546) `*` | 8.284 (4.594) `*` | 8.333 (1.475) `***` | −18.252 (5.024) `***` | 7.026 (0.859) `***` | −24.589 (3.522) `***` | 2.562 (1.090) `**` | −2.622 (1.767) `ns` | 8.226 (3.876) `**` | −16.711 (2.259) `***` |
| `2010s` | 8.532 (5.114) `ns` | 3.148 (1.421) `**` | 5.665 (1.123) `***` | −1.247 (2.478) `ns` | 6.025 (0.735) `***` | −12.179 (1.606) `***` | 1.976 (1.140) `*` | 0.325 (0.678) `ns` | 4.001 (1.286) `***` | −6.443 (0.952) `***` |
| N | 456 | 7,769 | 490 | 137 | 1,203 | 322 | 317 | 257 | 10,235 | 716 |
| 00s−10s | −8.40% [0.442] | −5.10% [0.624] | −2.70% [0.162] | +17.0% [0.292] | −1.00% [0.385] | +12.4% [0.000] | −0.60% [0.707] | +2.90% [0.244] | −4.20% [0.040] | +10.3% [0.001] |

*(2010s row: coefficient, clustered SE in parentheses, significance stamp in backticks. The two
significant declines from the 2000s to the 2010s are the pooled columns and the SmallCap deletion —
every other individual decline is insignificant.)*

Windows differ and this matters: **Russell** = day before the **May rank date** → day after
implementation (~6 weeks, Madhavan's convention); **MidCap / SmallCap / Nasdaq 100** = **10 days
before the effective date** → 1 day after, because Siblis supplies no announcement dates for those
families and changes are typically announced 5 business days ahead.

**What survives, at the 5% level, in the 2010s:**

- **S&P SmallCap 600 direct additions +6.03%** (t≈8.2) and **direct deletions −12.18%** (t≈7.6).
  The SmallCap addition effect *has not declined at all* over 30 years — the authors say it
  "hasn't changed much... consistently hovering around 6%."
- **S&P MidCap 400 direct additions +5.67%** (t≈5.0). MidCap deletions have died (−1.25%, ns).
- **Russell 2000 direct additions +3.15%** (t≈2.2), N=7,769.
- **Pooled additions +4.00%** and **pooled deletions −6.44%**, both significant at 1%.

**What does not survive:** Russell 1000 direct additions (+8.53%, **t=1.67, insignificant**),
Nasdaq 100 additions (+1.98%, marginal), Nasdaq 100 deletions (~0 for 30 years), and — the whole
point of §2 — the S&P 500 average.

**The pattern is unmistakable and it is the inverse of this territory's premise: the effect
survives in small- and mid-cap names and is dead in large liquid ones.** The authors' own summary
is that effects "grew into the 2000s and shrunk thereafter, but the statistical significance is
weak" — only the pooled columns and the SmallCap deletion decline are individually significant
declines. They add one line that should be read carefully by anyone hoping predictability is the
story: because Russell is mechanical and S&P is discretionary, *"the similarity between the
time-series trends for the Russell 1000 and 2000 indices and S&P 500 [is] striking, as changes in
predictability are not likely the drivers."*

### 4.3 Four reasons not to treat §4.2 as a green light

1. **The windows partly precede the announcement, and index changes are selected on recent
   return.** MidCap/SmallCap/NDX windows start **10 trading days before the effective date**, i.e.
   about **5 days before the announcement**. A name is deleted from the SmallCap 600 *because it
   fell*. Part of −12.18% is therefore the fall that caused the deletion, not a response to forced
   selling. Greenwood & Sammon do not decompose this for these families because they lack
   announcement dates. **This is a selection confound of exactly the kind this house kills studies
   over, and it is unresolved in the published literature.**
2. **Not one number in §4.2 is net of anything.** No paper I found nets the small-cap
   reconstitution effect against realistic transaction costs on small-cap names. Madhavan frames
   cost from the index fund's side (its loss); nobody prices the arbitrageur's spread. Per D285:
   the spread of the **names held** must be estimated from their own OHLC, not assumed.
3. **The event is a closing-auction event.** Chinco & Sammon: almost all reconstitution trading is
   in the closing auction; effective-date volume is ~30% of the surrounding month. **A daily-bar
   fixture cannot see inside the print where the flow and its reversal both happen.**
4. **The one bullish claim I found is a model, not a measurement.** Tasitsiomi, *On the hidden costs
   of passive investing*, arXiv 2506.21775 (Jun 2025, v3 Oct 2025) [WORKING PAPER, not peer-
   reviewed] states that *"a trader who builds a small inventory post-announcement and provides
   liquidity at the reconstitution event can consistently earn several hundreds of basis points in
   profit... assuming minimal risk."* **This is the output of a Nash/Stackelberg game-theory model
   parameterised with price-impact assumptions, not an empirical estimate.** Its own empirical
   inputs are borrowed: the "~5.0% additions / −7.2% deletions" it cites is Arnott et al. (2023),
   and the 67bp execution cost is Li (2021). Read at source; the empirical section does not exist.

### 4.4 The practitioner evidence, deflated

- **Arnott, Brightman, Kalesnik & Wu (2023)**, *Earning Alpha by Avoiding the Index Rebalancing
  Crowd*, *Financial Analysts Journal* 79(2) 76-97 [PEER-REVIEWED — but the authors were Research
  Affiliates, which sells alternatives to cap-weighted indexing; treat the framing accordingly].
  Sample begins **October 1989** — it **pools the 1990s and 2000s, where the effect was enormous,
  with the 2010s**, which is precisely the aggregation Greenwood & Sammon's decade split exists to
  break. Headline: *in the year after a change, discretionary deletions beat additions by 22% on
  average*, and deletions outperform for at least five years. **That is a long-horizon reversal
  claim, not a forced-flow claim** — over a 1-to-5-year horizon on names sold down before removal,
  the natural reduction is *value plus long-horizon reversal in disguise*, and I found no evidence
  they control for it. Their own bottom line is far smaller than the headline: simple rules
  (trading ahead of index funds, or delaying reconstitution trades 3-12 months) add **up to 23 basis
  points a year**, and that applies to a **passive portfolio's implementation**, not to a standalone
  book. [NOT READ AT SOURCE — tandfonline and CFA Institute both 403; sample end date and any
  post-2010 sub-period breakout are **unverified**.]
- **Li (2021)**, *Should Passive Investors Actively Manage Their Trades?* (SSRN 3967799)
  [WORKING PAPER]. **56% of ETFs** track public pre-announcing indices and trade entirely at the
  reconstitution-day close; they pay **67bp** in execution cost, ~3× a comparable institutional
  trade, with a **−20bp price impact because the price reverses after the ETF's buy**. ETFs that
  spread trades over 10 days save **34bp/trade ≈ 7.3bp/year**; self-indexed ETFs that avoid
  pre-announcement save **30bp**. [NOT READ AT SOURCE — abstract and secondary citation.]
  **Note the scale: the liquidity provider's whole prize here is on the order of tens of basis
  points per event, not the percent-level numbers of the 1990s.**
- A retail backtest blog [SALES INSTRUMENT / UNVERIFIED — ravenquant.com] reports simulating entry
  on the S&P 500 effective date from **March 2000 to January 2026** across 1-6 month holds: a best
  variant with 59% win rate and +3.65% mean per addition, but total **+48.7% vs SPY's +563.7%**,
  and concludes costs, taxes and tail losses consumed the edge. Low-grade evidence; included only
  because it points the same way as everything above.

### 4.5 The plain answer

**For the S&P 500 and the Russell 1000 — the large, liquid, high-priced population this territory
was chosen for — the honest answer is no, nothing tradeable survives post-2010, and the specific
leg that died is the forced-flow leg between announcement and implementation.** That is the result
that saves the week. **For the S&P SmallCap 600, the S&P MidCap 400, and Russell 2000 direct
additions, a large and statistically significant gross effect persists through the 2010s** — but it
is measured over windows contaminated by the selection that caused the index change, has never been
netted of costs, lives in the closing auction, and sits in the price band where this programme's
per-share cost model is at its worst.

---

## 5. Deletions, and whether they separate from distress

**They have never been separated, because the modern literature deletes the distressed names
before it starts. This is the clearest gap I found and it is directly adjacent to this fixture's
one unusual property.**

**The exclusion, quoted.** Greenwood & Sammon's sample *"excludes those that are listed, acquired,
**delisted for reasons other than acquisition**, or are acquirers... within 100 days of the index
change."* And for the Russell, explicitly: *"We do not consider deletions from the Russell 3000 to
outside the Russell 3000 universe, **as these are often firms that are delisting and therefore do
not pass our sample selection criteria**."*

**How much this throws away — Table A1, the drops column:** across 1980-2020 the deletions sample
retains an average of **34%** of matched deletions. Year by year in the 2010s: 2010 **19%**, 2011
45%, 2012 29%, 2013 53%, 2014 57%, 2015 25%, 2016 25%, 2017 41%, 2018 35%, 2019 48%, 2020 63%.
By contrast additions retain **66%**. **Roughly two-thirds of S&P 500 deletions are dropped by the
filter, and the filter's dominant criterion is acquisition or non-acquisition delisting.** The
published deletion figure (+0.1% for 2010-2020) is therefore **a figure for deletions that neither
were acquired nor died**, which is a small and unusual residual population.

**Is the deletion effect larger or more persistent than the addition effect?** On the surviving
evidence: in the **S&P 500 it is not** — both are ~0 in 2010-2020. In the **S&P SmallCap 600 it is
much larger**: −12.18% in the 2010s against +6.03% for additions, and it is the only individually
significant *decline* between the 2000s and 2010s in Table 8 (from −24.59%, p=0.000). MidCap
deletions died (−1.25%, ns). So "deletions are less arbitraged" is **true in the small-cap indices
and false in the large-cap ones** — the same size pattern as §4.

**Is it separable from distress?** **No published study I found separates them post-2010, and the
best one structurally cannot, because it excludes the distressed cases by design.** Three
consequences worth stating plainly:

1. The −12.18% SmallCap deletion figure is measured on names that **did not delist within 100 days**.
   That is a point in its favour — it is not simply a bankruptcy return. But the window still starts
   10 days before the effective date and ~5 days before the announcement, so it still contains the
   decline that *caused* the deletion.
2. The historically enormous deletion numbers are visibly outlier-driven. In the Dec 2022 working
   paper's Table A2, single-name years dominate: **1985 with n=2 gives −30.39%**, **1990 with n=2
   gives −54.61%**, **1991 with n=4 gives −50.74%**. This is exactly the pattern the house rule on
   trade distributions is written for — a mean far below its median, driven by a handful of
   observations. Any deletion result must be reported with the median and both trimmed means.
3. There **is** older work distinguishing "true" deletions from inter-index transfers — a 2023
   *Journal of Banking & Finance* paper (Elsevier S0378426623001747) claims to resolve the
   asymmetric addition/deletion price-response puzzle by correcting for outliers and separating
   firms transferred into other S&P indices from true additions/deletions, finding a permanent
   price decline for true deletions. **[NOT READ AT SOURCE — ScienceDirect 403; I have neither the
   sample period, the magnitudes, nor the authors verified, and I would not cite it in a record
   without reading it.]** It is, however, the same direct-vs-migration distinction Greenwood &
   Sammon make, arrived at independently, which is mild corroboration that the distinction is real.

**The one genuinely open empirical question in this whole territory: what is the return around
index deletion for the names that actually die?** Nobody has published it, because CRSP-based event
studies routinely filter delisting returns out. A dead-inclusive fixture is the right instrument
for that question. §8 explains why the $5 floor probably takes it away again.

---

## 6. Data: historical membership changes, dead names included

**Answer: yes for the S&P family, free, dead-inclusive, with BOTH announcement and effective dates —
but it must be stitched from two sources and it is a scrape, not a download. No, for Russell:
there is no free announcement-date archive and the add/delete name lists are effectively
unavailable free before ~2015.**

### 6.1 The recommended free path for S&P 500 / 400 / 600 (2010-2026, dead-inclusive)

| segment | source | what it gives |
|---|---|---|
| **2012-01 → 2026** | `press.spglobal.com` release archive | announcement date = release date; **effective date in the body**; added and **removed** name + ticker + reason |
| **2010-01 → 2011-12** | PR Newswire permanent URLs for the same S&P releases, enumerated via the Wayback CDX API | same content; names are in the body, not the title |
| **skeleton / cross-check** | Wikipedia *Historical components of the S&P 500* | effective date + added + removed + reason; its `Refs` column links back to the S&P release that carries the announcement date |

**S&P Global press archive** [PRIMARY DATA DOC, free, no login, not bot-blocked]:

```
https://press.spglobal.com/index.php?s=2429&l=100&year=YYYY&keywords=Join&titles_only=1
```
Individual releases follow `https://press.spglobal.com/YYYY-MM-DD-Headline-With-Dashes`
(append `?asPDF=1` for a PDF rendering). **Verified end to end** on the 2014-03-14 release: release
date 2014-03-14, effective 2014-03-21 after close, full added/removed table with reasons.
**Delisted names are always present with ticker and reason** — these releases *are* the record of
names that subsequently vanished. Measured coverage by title-keyword count: **2010 → 0 releases,
2011 → 0, 2012 → 19, 2016 → 54, 2020 → 41, 2026 YTD → 38.** The oldest captures in the archive are
**January 2012**; 2012's 19 hits match that year's ~18-20 actual changes, so from 2012 the archive
is effectively complete.

**Note the trap:** `www.spglobal.com/spdji/...` — the official "Index Announcements" portal — is
**bot-blocked (HTTP 403)** and its announcement PDFs sit behind non-enumerable hashed paths
(`.../indexnews/announcements/20260813-1484396/1484396_avb54wbs.pdf`). Same content, unusable
route. Use `press.spglobal.com`.

**Filling 2010-2011** [free, verified]: pre-2012 S&P releases live permanently on PR Newswire under
generic titles ("Standard & Poor's Announces Change to U.S. Index"). Verified example:
`prnewswire.com/news-releases/standard--poors-announces-change-to-us-index-107074138.html` —
dated 2010-11-10, effective 2010-11-16 after close, Ingersoll-Rand replaces **Pactiv Corp (PTV)**,
reason acquired. Both dates and the dead name are present. Because the titles are generic,
enumerate rather than search, via the free Wayback CDX API:

```
http://web.archive.org/cdx/search/cdx?url=prnewswire.com/news-releases/standard--poors-announces*&fl=timestamp,original&collapse=urlkey&limit=2000
```
→ **87 unique** release URLs, roughly 2008-2012. Every one must be fetched because the names are
in the body.

### 6.2 Wikipedia — usable, but the page moved and the current-members page is useless

**Structural change worth knowing:** the "Selected changes" table was **split out on 2026-08-11**
into a new article. `List of S&P 500 companies` now holds **only current members** —
**as a standalone snapshot that page is exactly the useless kind this brief was told to call out:
full survivorship bias, no dead names, no change history.**

The changes table is now at **`en.wikipedia.org/wiki/Historical_components_of_the_S%26P_500`**,
columns `Effective Date | Added | Removed | Reason | Refs`. **No announcement-date column** — but
`Refs` cites the S&P release that has it, which is the join key back to §6.1. **Dead names: yes,
explicitly** (Allergan/AbbVie 2020-05-12; First Republic and SVB rows cite FDIC receivership).
Row counts: 2010:11, 2011:19, 2012:18, 2013:19, 2014:16, 2015:29, 2016:30, 2017:29, 2018:23,
2019:24, 2020:20, 2021:20, 2022:22, 2023:17, 2024:21, 2025:21, 2026 YTD:14. Pre-2007 it collapses
and is worthless. **It is a *selected* changes list and is demonstrably incomplete — 2010 shows 11
rows and 2014 shows 16 against actual turnover of ~20/year. Use it as an index into the press
releases, never as ground truth.**

**The revision-history route is the strongest free point-in-time membership source and it works.**
MediaWiki API on pageid **2676045**:
```
https://en.wikipedia.org/w/api.php?action=query&prop=revisions&pageids=2676045&rvdir=newer&rvstart=<ISO>&rvlimit=1&rvprop=ids|timestamp&format=json
https://en.wikipedia.org/w/index.php?oldid=<revid>&action=raw
```
Verified: revid **372975694** (2010-07-11) returns a full 500-row table containing Massey Energy,
El Paso, RadioShack, Sunoco, Dean Foods and Frontier — names since dead. Revisions run to 2005.
Licence CC BY-SA 4.0. **Two caveats that matter for a lag audit:** (i) that 2010 revision's own
lead says it is *"current as of the start of the trading day of April 1, 2010"* — **the table lags
the revision timestamp, sometimes by months, so revision timestamp is NOT the membership date**;
(ii) editors update around the **effective** date, never the announcement date.

### 6.3 FTSE Russell — no free announcement archive, and no names before ~2015

**LSEG does not archive prior years.** Probed directly: `ru3000-deletions-20260522.pdf` → 200,
`ru3000-additions-20250523.pdf` → 200, **`ru3000-deletions-20240524.pdf` → 404.** Only the current
and prior year survive at stable URLs. The reconstitution page also links a market-cap-range table
back to 2009 — **summary statistics only, no names, useless for membership.**
`research.ftserussell.com` index notices are free at the detail URL but the portal home and search
return **403** to automated fetching, IDs are opaque sequential integers with no date mapping, and
the notices are corrections and methodology changes, **not the recon add/delete lists**.

**The only free historical route is the Wayback Machine**, and it starts around **2015/2016**:
confirmed PDF captures for R3000 additions/deletions and Microcap 2016, final/preliminary 2017,
2018 preliminary and Microcap final, 2019, 2020, 2021, 2022 preliminary, 2023 final, plus
pre-FTSE `russell.com/documents/indexes/preliminary-list-2015-reconstitution.pdf` (verified 200,
146 KB). **2010-2014 Russell add/delete name lists are essentially not available free.**

Three further Russell caveats, stated bluntly:
- **Announcement date is inferable, not stated.** The preliminary-list posting date *is* the
  announcement, and in practice it is the Wayback capture timestamp — it is not inside the file.
- **The 2018-2023 `files/support-document/...` captures frequently archived as the Angular SPA
  landing page (`text/html`), not the PDF.** You must hunt the asset with a CDX
  `filter=mimetype:application/pdf` query. Verified failure case:
  `2019-final-russell-3000-index-deletions` returns 100 KB of HTML shell.
- **A Russell deletion is mostly a market-cap drop, not a corporate death, and the files do not
  distinguish "deleted because it shrank" from "deleted because it was acquired or delisted."**
  For §5's open question that is a fatal ambiguity in the free data.
- `WebFetch` refuses `web.archive.org`; use `curl` or the CDX API.

### 6.4 SEC EDGAR — indirect, coarse, no announcement date; an audit check only

Queried SPY's submissions (CIK 0000884394). **NPORT-P begins only ~2019** (28 filings, report dates
at quarter-ends). For **2010-2019 SPY is a unit investment trust filing N-30D / N-CSR — semi-annual
and annual schedules of investments**, i.e. two snapshots a year. Better vehicles for quarterly
2010-2019 are **IVV (iShares Trust)** and **Vanguard 500 Index Fund**, which filed N-Q quarterly
through 2019 then NPORT-P, at the cost of bundling many funds per registrant in large filings.

**Verdict: EDGAR gives holdings snapshots, never change events. No announcement date at all, and no
effective date finer than the snapshot interval.** Its one genuine virtue is that **dead names are
present** — they were held at the time. **Use it to verify a reconstructed series, not to build
one.** No other regulatory record of index composition exists; indices are not registered products.

### 6.5 Community datasets — convenience packagings of Wikipedia, not independent evidence

| source | coverage | ann. date | eff. date | dead names | licence |
|---|---|---|---|---|---|
| `github.com/fja05680/sp500` | 1996 → present | **no** | yes | **yes**, author states it explicitly | MIT |
| `github.com/hanshof/sp500_constituents` | 1996-01-02 → present | no | yes | present as daily snapshots | MIT |
| `github.com/epicycloids/sp500-tickers` | 1996 → | no | yes | yes (first/last date per ticker) | — |
| Robot Wealth `r-quant-recipes` | 2000 → | no | yes | yes | — |

**All four are downstream of Wikipedia** and inherit its selected-changes incompleteness and its
effective-date-only limitation. fja05680's base is Clenow's 1996-2019 file plus periodic Wikipedia
scraping. **None carries an announcement date. Treat as packaging of §6.2, not corroboration of it.**

**APIs.** Financial Modeling Prep `historical-sp500-constituent` (free tier 250 req/day) returns
date, added, removed, reason — **effective date only**, includes dead names, history quality
unverified and reported thinner than Wikipedia. EODHD `GSPC.INDX` fundamentals — historical changes
**start 2012-04-04**, carries an explicit `IsDelisted` flag, **no announcement date**, requires a
paid Fundamentals plan. **Alpha Vantage `LISTING_STATUS`** (`state=delisted`, dates from
**2010-01-01**) is **not index membership** — it is a delisting registry, and it is the right free
tool for *resolving* dead tickers and detecting ticker reuse once you have a membership series.
Nasdaq Data Link has no free constituents table.

**Academic replication packages: none usable.** Greenwood & Sammon's 1980-2020 list with both
announcement and effective dates was **licensed from Siblis Research and is not redistributed**;
same for Bennett/Stulz/Wang. Useful only as documentation that the announcement/effective
distinction is the standard.

### 6.6 Paid-but-cheap, if the free path proves too costly to build

| vendor | ann. date | eff. date | dead names | coverage | price |
|---|---|---|---|---|---|
| **Siblis Research** | **YES** | yes | yes | S&P 500 changes **1973/1980 → present** | **~$576/yr** (annual billing) |
| **Norgate Data** | no | yes | **yes** | S&P 500 to **1957**; also 100/400/600, DJIA, NDX, **Russell 1000/2000/3000 from Jul 1990** | ~$630/yr Platinum |
| **Sharadar** (Nasdaq Data Link / QuantRocket) | no | yes | yes, ~99% survivorship-free | S&P 500 constituents from **Jan 1998** | low hundreds $/yr |
| CRSP / Compustat via WRDS | no | yes | yes | 1958/1964 → | institutional only — **rule it out** |

**Siblis is the only cheap source with an explicit announcement date**, and it is the source
Greenwood & Sammon actually used — which is third-party validation rather than marketing.
[Its own site is a SALES INSTRUMENT; the validation is the NBER citation, not the site.]
**Norgate is the best price/history for point-in-time membership plus matched delisted price series
in one product, and it is the only cheap source that covers Russell at all.**

### 6.7 The blunt summary

- **Free, dead-inclusive, with announcement AND effective dates, 2010-2026, S&P family: YES** —
  `press.spglobal.com` from 2012 + PR Newswire via Wayback CDX for 2010-2011, with Wikipedia's
  historical-components table as the skeleton and the S&P release as ground truth. It is a
  multi-hundred-page scrape, not a file download.
- **Free, for Russell, with announcement dates: NO.** Names only from ~2015 via Wayback,
  announcement date only inferable from capture timestamps, and deletions do not distinguish
  shrinkage from death.
- **`List of S&P 500 companies` on its own is a current-members list and is useless here** — as is
  any vendor "constituents" endpoint that does not carry removed names. Say so and move on.

---

## 7. Adjacent forced flows

Both parts of this question resolve quickly and negatively.

**ETF creation/redemption flows.** The peer-reviewed result is **Brown, Davies & Ringgenberg**,
*ETF Arbitrage, Non-Fundamental Demand, and Return Predictability*, *Review of Finance* 25(4)
937-972 [PEER-REVIEWED]: ETF creation/redemption activity proxies non-fundamental demand shocks,
and a portfolio **short high-flow ETFs / long low-flow ETFs earns 1.1-2.0% per month**. Three
reasons this does not become an F1 lead. (i) **It is a signal on the ETF, not on the single names**
— the tradeable portfolio is a cross-section of *funds*, and this programme's ETF instrument is a
57-ETF panel whose effective independent instruments **saturate near 2.2**, so a cross-sectional
ETF long-short has ~2 degrees of freedom to work with. (ii) The mechanism is mean-reversion of a
non-fundamental demand shock, which is **short-term reversal** — already researched and already
on the exclusion list, and this programme has already established that a reversal edge is
denominated in the spread. (iii) Creation/redemption data is not free at daily frequency for a
2010-2026 history. [NOT READ AT SOURCE — abstract and journal listing only; I did not verify the
sample period or cost treatment behind the 1.1-2.0%/month figure, and a number that large with no
stated cost treatment deserves the house default of scepticism.]

**Month-end and quarter-end index-tracking flow.** This is **turn-of-month, which is explicitly on
the exclusion list** and was covered in round 1 (`working/leads/K1-calendar.md`). For completeness,
the recent framing is an *infrequent-rebalancing* mechanism: turn-of-month day returns run about
**5.2bp** above rest-of-month in regular months, **+7bp more** at the March/September close and
**+17bp more** at the June/December close (cumulative spreads 5.2 / 12.2 / 22.2bp), with larger
effects after high volatility and in recessions [*Journal of International Financial Markets,
Institutions & Money*, S1042443126000259; NOT READ AT SOURCE]. **These are index-level, directional,
single-digit-basis-point effects.** They are not cross-sectional, they are below this programme's
cost floor on any low-priced name, and they are already-researched territory. **No lead here.**

The one adjacent item worth remembering is not a trade but a fact: **Li (2021)'s 56% of ETFs
trading entirely at the reconstitution close** is why reconstitution flow is a closing-auction
phenomenon rather than a daily-bar one, and it is the same fact that makes §4.3(3) binding.

---

## 8. Does it transfer to OUR universe

**Bluntly: no, for four independent reasons, and the first one alone is sufficient.**

**1. The premise is inverted.** F1 was chosen because forced index flow happens *"in LARGE, LIQUID,
HIGH-PRICED names, which is the one population its per-share cost model can actually trade."* The
evidence says the effect in large liquid names is the part that died (S&P 500 average +0.3%;
S&P 500 announcement→effective +0.209% ns; Russell 1000 direct additions t=1.67; Nasdaq 100
additions +1.98%), and the part that survived is in the **S&P SmallCap 600, S&P MidCap 400 and
Russell 2000** — smaller, cheaper, wider-spread names. **The cost argument that justified the
territory selects against the only population where the effect is alive.**

**2. The per-share cost model reverses sign across this trade.** Cost in bp scales inversely with
price. On a $200 large cap, IBKR's per-share commission is a fraction of a basis point per side —
which is why the large-cap version would have been cheap to trade *if it still existed*. On a $6
SmallCap 600 name it is an order of magnitude worse, and the *spread* on a small-cap name being
force-sold at the close is worse again. **D285's lesson applies exactly: do not assume a spread —
Corwin-Schultz the names actually held.** Any small-cap reconstitution study that reports a gross
number without doing this is not a result.

**3. The $5 floor and the dead-inclusive property cancel each other out on the one open question.**
The fixture's genuinely unusual asset — 43.5% dead names — makes it the right instrument for the
question the literature has never answered (§5: what happens around deletion to the names that
actually die). But names being deleted from an index for distress are, disproportionately, names
approaching or below **$5**, and the floor excludes them. This is D347/D351 in mirror image: there,
a null accidentally traded the sub-$5 tail and the headline inverted when it was fixed; here, the
*published* effect may live in the sub-$5 tail that the fixture's floor removes. **Whichever way it
falls, the floor must be checked against the held names before any deletion result is believed, and
if the answer is "the effect is all in names the floor excludes", that closes it.**

**4. The instrument cannot see the event.** Reconstitution flow is a **closing-auction**
phenomenon: ~30% of the surrounding month's volume prints on the effective date, ETF rebalancing is
executed at the close, and Li (2021) measures a **−20bp price impact that reverses after the buy**.
The fixture is **daily bars** for single names; the 15-minute panel is **57 ETFs**, not single
names. **The programme has no instrument that can distinguish the impact from its reversal, because
both happen inside one closing print it observes as a single number.** Anything measured on daily
closes measures the post-reversal residual by construction.

**Two further frictions specific to this book.** Equal weighting plus a slot cap makes an event
book structurally thin: direct S&P 500 additions run at roughly **4-5 events per year**
universe-wide (about 20% of ~23 annual additions), so even at a 40-bar hold the book is near-empty
most of the time and the opportunity cost against whatever the slots would otherwise hold
(`docs/FINDINGS.md` §10) is likely to dominate the signal. And the fixture window **2010-01-04 to
2026-08-26** sits almost entirely inside the decade the literature identifies as the dead one —
there is no pre-2010 regime in the fixture to contrast against, so a fixture-internal
"has it decayed?" test cannot be run at all.

---

## 9. The premise number to compute first

**One number, one join, no runner, and it decides the territory. But note what the join costs
first:** the event list is **not** a file download. Per §6, getting S&P 500 add/delete events with
announcement dates for 2010-2026 means scraping several hundred `press.spglobal.com` releases plus
~87 PR Newswire releases via Wayback for 2010-2011 — or paying Siblis ~$576/yr for it. **A cheap
first cut exists**: the Wikipedia historical-components table gives added/removed/effective/reason
for free in one fetch, is dead-inclusive, and is *demonstrably incomplete* (11 rows in 2010 against
~20 actual changes). **That incompleteness is acceptable for the premise number and fatal for a
result** — an incomplete event list biases toward the changes editors thought notable, which is a
selection this house would not accept in a study. Use it to compute the number below; if the number
passes, buy or scrape the real list before anything else is run.

**The programme currently holds none of this.** A search of `data/`, `scripts/` and `docs/` for
index-membership artefacts returns only incidental mentions of "Russell" in the futures-data and
COT research notes — **there is no constituent file, no membership table and no event list in the
repository.** So the true cost of the first measurement is the scrape, not the join.



> **How many index-change events land on symbols that are in the fixture, inside 2010-01-04 to
> 2026-08-26, split by (a) index family, (b) direct vs migration, and (c) addition vs deletion —
> and what is the price distribution of those names on the day before the event?**

This is a Stage-0 premise check in the sense the memory file means: the "conditioner" here is not a
persistent state whose autocorrelation must be measured, it is an **event**, so the premise number
is the **event count intersected with the tradeable universe**, plus the price distribution that
decides whether the cost model can touch it.

**The thresholds to pre-register before looking:**

1. **Direct S&P 500 additions ∩ fixture.** The universe-wide ceiling is ~4-5/year × 16.6 years
   ≈ **76 events**, before any intersection. If the fixture contains fewer than ~40, **stop** — at
   that N a +5.40% mean with the cross-sectional dispersion Table 3 implies cannot be separated from
   zero in this sample regardless of how large the true effect is, and a null will be
   uninformative. **This is a power calculation that costs one join and can be done today.**
2. **Price distribution of the SmallCap 600 / MidCap 400 / Russell 2000 event names.** If the
   median pre-event price is under ~$15, the per-share commission plus a Corwin-Schultz spread
   estimated **off the held names' own OHLC** will very likely exceed the gross effect, and the
   answer is the same one this programme has reached repeatedly: the edge is denominated in the
   spread. **Compute the breakeven in bp/side against the measured spread, not an assumed one.**
3. **The deletion-and-death overlap.** Of the fixture's dead names, how many were removed from a
   major index before dying, and what fraction of those were **above $5 at the time of removal**?
   This is the only number that tells you whether the fixture can answer the question the
   literature has never answered, or whether the floor has already removed the sample.

**What would have to be true for this to proceed**, stated now so it cannot be moved later: N ≥ ~40
usable events in a single family, median event-name price high enough that the measured spread is a
small fraction of a +5% gross point estimate, and a design that separates the pre-announcement
window from the announcement→effective window — because §2.2 shows the second one is where the
forced flow lives and it is the one that died.

**A caution on the null, per the house rule.** The natural control is a matched-count random draw
of non-event names — and that is *"never a control for a persistent selector"* and, worse here,
never a control for a **selected** one. Index changes are chosen on size, recent return and
liquidity; an addition is a name that went up and a deletion is a name that fell. The control must
share those nuisances, i.e. **matched on trailing return, size and turnover**, not on count. With
~40-80 events and a market-level annual calendar, a time rotation has very few distinct offsets and
should be **enumerated rather than sampled** (D361/D373).

---

## 10. Sources

**Primary evidence — read at source (PDF text extracted from the downloaded file):**

- [PEER-REVIEWED / WORKING PAPER, three vintages] Greenwood, R. & Sammon, M., *The Disappearing
  Index Effect*.
  - Published: *Journal of Finance* **80(2), April 2025, 657-698**, DOI 10.1111/jofi.13410 —
    https://onlinelibrary.wiley.com/doi/10.1111/jofi.13410 *(abstract only; Wiley returned 403)*
  - HBS Working Paper 23-025, **revised November 2023** —
    https://www.hbs.edu/ris/Publication%20Files/23-025_563e45c6-df92-4d9c-ae05-608d4d0acab1.pdf
    **[READ AT SOURCE — Tables 3 and 8, §3.1-3.4 and the abstract in §2.1 come from this file]**
  - NBER Working Paper w30748, **December 2022** —
    https://www.nber.org/system/files/working_papers/w30748/w30748.pdf ; mirror
    https://www.ivey.uwo.ca/media/m2kh5j5y/the-disappearing-index-effect.pdf
    **[READ AT SOURCE — Table 2, Table 4, Tables A1/A2 and the five explanations come from this file]**
  - SSRN listing: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4294297
- [WORKING PAPER, **not peer-reviewed** — a game-theory model, not an empirical study]
  Tasitsiomi, I., *On the Hidden Costs of Passive Investing*, arXiv 2506.21775 (v3, 20 Oct 2025) —
  https://arxiv.org/pdf/2506.21775 **[READ AT SOURCE]**
- [WORKING PAPER, **student paper, not peer-reviewed — I recommend discarding it**] Agrawal, V.,
  Khalid, E., Tan, T. & Xu, D., *Hunting Tomorrow's Leaders: Using Machine Learning to Forecast
  S&P 500 Additions & Removal*, Columbia University, arXiv 2412.12539 —
  https://arxiv.org/pdf/2412.12539 **[READ AT SOURCE]**

**Primary data documentation — FTSE Russell / LSEG:**

- [PRIMARY DATA DOC] *Russell US Equity Indexes, Construction & Methodology*, **v7.2, August 2026** —
  https://www.lseg.com/content/dam/ftse-russell/en_us/documents/ground-rules/russell-us-indexes-construction-and-methodology.pdf
- [PRIMARY DATA DOC] Russell Reconstitution calendar page (June and December 2026 dates) —
  https://www.lseg.com/en/ftse-russell/russell-reconstitution
- [PRIMARY DATA DOC] *FTSE Russell Begins June 2026 Semi-Annual Reconstitution* —
  https://www.lseg.com/en/media-centre/press-releases/ftse-russell/2026/ftse-russell-begins-june-2026-semi-annual-russell-us-indexes-reconstitution
- [PRIMARY DATA DOC] *June 2026 reconstitution: summary of changes* —
  https://www.lseg.com/content/dam/ftse-russell/en_us/documents/other/2026-russell-us-indexes-reconstitution-summary.pdf
- [PRIMARY DATA DOC] Semi-annual announcement, **16 Jan 2025** (says **November**) —
  https://lseg.com/en/media-centre/press-releases/ftse-russell/2025/russell-us-indexes-move-to-semi-annual-reconstitution
- [PRIMARY DATA DOC] Semi-annual, **updated December 2025** (moves it to **December**) —
  https://lseg.com/en/ftse-russell/research/russell-us-indexes-move-to-semi-annual-reconstitution

**Peer-reviewed:**

- [PEER-REVIEWED] Madhavan, A. (2003), *The Russell Reconstitution Effect*, *Financial Analysts
  Journal* 59(4) 51-64 — https://www.tandfonline.com/doi/abs/10.2469/faj.v59.n4.2545 ;
  full text mirror https://www.hillsdaleinv.com/uploads/The_Russell_Reconstitution_Effect,_Ananth_Madhaven,_Financial_Analysts_Journal,_JulyAugust_2003,_Pages_51-64.pdf
  [NOT READ AT SOURCE]
- [PEER-REVIEWED] Chang, Y.-C., Hong, H. & Liskovich, I. (2015), *Regression Discontinuity and the
  Price Effects of Stock Market Indexing*, *Review of Financial Studies* 28(1) 212-246 —
  https://academic.oup.com/rfs/article-abstract/28/1/212/1680962 ; NBER w19290
  https://www.nber.org/papers/w19290 [NOT READ AT SOURCE — SSRN 403]
- [PEER-REVIEWED — **the strongest published negative on the Russell identification**] Wei, W. &
  Young, A., *Selection Bias or Treatment Effect? A Re-Examination of Russell 1000/2000 Index
  Reconstitution*, *Critical Finance Review* 13(1-2) 83-115 —
  https://cfr.ivo-welch.org/published/papers/wei2020selection.pdf ;
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2780660 ; replication files https://osf.io/gku6j
- [PEER-REVIEWED] Appel, I., Gormley, T. & Keim, D., *Identification Using Russell 1000/2000 Index
  Assignments: A Discussion of Methodologies*, *Critical Finance Review* 13(1-2) —
  https://cfr.ivo-welch.org/published/papers/appel2020identification.pdf
- [PEER-REVIEWED, JF *Replications & Corrigenda*] Ben-David, I., Franzoni, F. & Moussawi, R. (2019),
  *A Note to "Do ETFs Increase Volatility?": An Improved Method to Predict Assignment of Stocks into
  Russell Indexes* — https://afajof.org/wp-content/uploads/20191016-Note-for-JF.pdf
  **(Appendix A: full rank / preliminary / reconstitution date calendar 1989-2019)**
- [PEER-REVIEWED — **author commercial interest**: Research Affiliates sells alternatives to
  cap-weighted indexing] Arnott, R., Brightman, C., Kalesnik, V. & Wu, L. (2023), *Earning Alpha by
  Avoiding the Index Rebalancing Crowd*, *Financial Analysts Journal* 79(2) 76-97 —
  https://www.tandfonline.com/doi/full/10.1080/0015198X.2023.2173506 ; summary
  https://rpc.cfainstitute.org/research/financial-analysts-journal/2023/earning-alpha-by-avoiding-the-index-rebalancing-crowd
  [NOT READ AT SOURCE — both 403; **sample end date and post-2010 breakout unverified**]
- [PEER-REVIEWED] Petajisto, A. (2011), *The Index Premium and Its Hidden Cost for Index Funds*,
  *Journal of Empirical Finance* 18(2) 270-282 —
  https://www.petajisto.net/papers/petajisto%202011%20jef%20-%20hidden%20cost%20for%20index%20funds.pdf
  [NOT READ AT SOURCE]
- [PEER-REVIEWED] Brown, D., Davies, S. & Ringgenberg, M., *ETF Arbitrage, Non-Fundamental Demand,
  and Return Predictability*, *Review of Finance* 25(4) 937-972 —
  https://academic.oup.com/rof/article/25/4/937/5919085 [NOT READ AT SOURCE]
- [PEER-REVIEWED, **unverified**] *Additions to and deletions from the S&P 500 index: A resolution to
  the asymmetric price response puzzle*, *Journal of Banking & Finance* (2023) —
  https://www.sciencedirect.com/science/article/abs/pii/S0378426623001747
  [NOT READ AT SOURCE — 403; authors, sample and magnitudes all unverified]
- [PEER-REVIEWED, **unverified**] *Infrequent rebalancing, risk deferral, and equity returns at the
  turn of the month*, S1042443126000259 —
  https://www.sciencedirect.com/science/article/abs/pii/S1042443126000259 [NOT READ AT SOURCE]

**Working papers:**

- [WORKING PAPER] Bennett, B., Stulz, R. & Wang, Z. (2020), *Does Joining the S&P 500 Index Hurt
  Firms?*, NBER w27593 — https://www.nber.org/system/files/working_papers/w27593/w27593.pdf ;
  SSRN 3656628 [NOT READ AT SOURCE]
- [WORKING PAPER] Chinco, A. & Sammon, M. (2022), *Excess Reconstitution-Day Volume* —
  https://www.alexchinco.com/excess-reconstitution-day-volume.pdf ; SSRN 3991200
  [NOT READ AT SOURCE]
- [WORKING PAPER] Li, S. (2021), *Should Passive Investors Actively Manage Their Trades?*,
  SSRN 3967799 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3967799 [NOT READ AT SOURCE]
- [WORKING PAPER, **UNVERIFIED — could not retrieve**] Onayev, Z. & Zdorovtsov, V. (2007),
  *Russell Reconstitution Effect Revisited*, SSRN 960727 —
  https://www.efmaefm.org/0efmameetings/EFMA%20ANNUAL%20MEETINGS/2007-Austria/papers/0693.pdf
  *(TLS failure at EFMA, 403 at SSRN — every figure attributed to it in §3.5 is second-hand)*
- [WORKING PAPER] Madhavan, A., Ribando, J. & Udevbulu, N. (2022), *Demystifying Index Rebalancing:
  An Analysis of the Costs of Liquidity Provision*, *Journal of Portfolio Management* 48(6)
  [NOT READ AT SOURCE]
- [WORKING PAPER] Micheli, A. & Neuman, E. (2020), *Evidence of Crowding on Russell 3000
  Reconstitution Events*, arXiv 2006.07456 [NOT READ AT SOURCE]

**Data sources (§6) — all verified reachable unless marked:**

- [PRIMARY DATA DOC] S&P Global press-release archive — https://press.spglobal.com/ ;
  query form `https://press.spglobal.com/index.php?s=2429&l=100&year=YYYY&keywords=Join&titles_only=1` ;
  verified example release
  https://press.spglobal.com/2014-03-14-Biogen-Idec-Set-to-Join-the-S-P-100-Keurig-Green-Mountain-to-Join-the-S-P-500-Changes-to-the-S-P-MidCap-400-and-the-S-P-SmallCap-600 ;
  RSS (current items only) `https://press.spglobal.com/index.php?s=2429&pagetemplate=rss`
- [PRIMARY DATA DOC] PR Newswire, S&P 2010 index change (verified: both dates + dead name) —
  https://www.prnewswire.com/news-releases/standard--poors-announces-change-to-us-index-107074138.html ;
  enumerate via Wayback CDX
  `http://web.archive.org/cdx/search/cdx?url=prnewswire.com/news-releases/standard--poors-announces*&fl=timestamp,original&collapse=urlkey&limit=2000`
- [PRIMARY DATA DOC] Wikipedia, *Historical components of the S&P 500* (pageid 83943699, created
  2026-08-11) — https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_500
- [**USELESS ON ITS OWN — current members only, full survivorship bias**] Wikipedia, *List of S&P
  500 companies* (pageid 2676045) — https://en.wikipedia.org/wiki/List_of_S%26P_500_companies
  *(its **revision history** via the MediaWiki API is the useful part; verified revid 372975694,
  2010-07-11, returns dead names)*
- [PRIMARY DATA DOC] LSEG Russell 3000 deletions/additions, current and prior year only —
  https://www.lseg.com/content/dam/ftse-russell/en_us/documents/other/ru3000-deletions-20250523.pdf
  *(2024 equivalent returns 404 — LSEG does not archive)*
- [PRIMARY DATA DOC] SEC EDGAR, SPY submissions —
  https://data.sec.gov/submissions/CIK0000884394.json *(holdings snapshots only, no change events,
  no announcement date; NPORT-P from ~2019, N-30D semi-annual before)*
- [open source, MIT] https://github.com/fja05680/sp500 · https://github.com/hanshof/sp500_constituents
  · https://github.com/epicycloids/sp500-tickers · https://robotwealth.com/how-to-get-historical-spx-constituents-data-for-free/
  *(all downstream of Wikipedia; none carries an announcement date)*
- [API docs] FMP https://site.financialmodelingprep.com/developer/docs/stable/historical-sp-500 ·
  EODHD https://eodhd.com/financial-apis-blog/sp-500-historical-constituents-data ·
  Alpha Vantage `LISTING_STATUS` https://www.alphavantage.co/documentation/ *(a delisting registry,
  not index membership — the right tool for resolving dead tickers)*
- [SALES INSTRUMENT — but the source Greenwood & Sammon actually licensed, which is real
  third-party validation] Siblis Research historical component changes —
  https://siblisresearch.com/data/historical-component-changes/ *(~$576/yr; the only cheap source
  with an explicit **announcement date**)*
- [SALES INSTRUMENT] Norgate Data — https://norgatedata.com/ *(~$630/yr; point-in-time membership
  plus matched delisted price series; the only cheap source covering Russell)* ·
  Sharadar — https://sharadar.com/prices · https://data.nasdaq.com/databases/SEP

**Sales instruments — cited only where self-incriminating or for context:**

- [SALES INSTRUMENT] S&P Dow Jones Indices, *What Happened to the Index Effect? A Look at Three
  Decades of S&P 500 Adds and Drops* —
  https://www.spglobal.com/spdji/en/research/article/what-happened-to-the-index-effect-a-look-at-three-decades-of-sp-500-adds-and-drops
  *(403 on both article and PDF; sample "start of 1995 to June 2021" and the "structural decline"
  conclusion are from search summaries, not read)*
- [SALES INSTRUMENT] FTSE Russell / LSEG reconstitution marketing: ~$12.2tn benchmarked (30 Jun
  2025); $217.2bn traded at the June 2025 reconstitution close; 2026 R1000/R2000 breakpoint $5.7bn.
  *The AUM footnote concedes it excludes assets not reported to third parties and substitutes stale
  prior-period figures — treat with suspicion.*
- [SALES INSTRUMENT] Alpha Architect, *Markets Becoming More Efficient: The Disappearing Index
  Effect* — https://alphaarchitect.com/disappearing-index-effect/ *(403; a research-summary blog run
  by an asset manager)*
- [SALES INSTRUMENT / UNVERIFIED] ravenquant.com, *S&P 500 Index Addition Strategy: Is There an
  Edge?* — a retail backtest, March 2000 to January 2026, concluding costs consumed the edge.
- [SALES INSTRUMENT / UNVERIFIED] etftrends.com, *Retail Revival Fuels Comeback of S&P 500 Index
  Inclusion Effect* — **403, could not read.** Search summary claims 2025 additions (Block,
  Coinbase, DoorDash) outperformed equal-weight S&P 500 by 7.4pp on announcement day and 12pp in
  the three preceding months, with no continuation after the reshuffle. **N=3 named high-profile
  crypto/tech names in one year, no method, no costs, no source paper identified. This is the
  only "comeback" claim I found and I would not carry it into a record.**

---

## Safety note

**No web page, PDF or search result encountered during this research contained text addressed to me
or attempting to instruct me.** Every source was treated as data. No files were downloaded on
instruction from a page, no forms were submitted, no accounts created.

One item worth recording rather than acting on: the Wayback CDX index for FTSE Russell contains
user-submitted prank URLs with joke text spliced into the path
(`russell-3000-index-additions-2021%20Stfu%20with%20your%20fud`,
`russell-microcap-deletions-2021%20GameStop%20removed%20from%20the%20Russell%20Microcap%20index,%20very%20bullish`).
**That is URL noise submitted by members of the public into an archive index, not instructions and
not data** — it is flagged here only because anything enumerating Russell files through CDX will
encounter it and must filter it out.

Several publisher domains (Wiley, ScienceDirect, tandfonline, **`www.spglobal.com/spdji`**, CFA
Institute, alphaarchitect, etftrends, `research.ftserussell.com` search) returned **HTTP 403** to an
automated fetch, and `WebFetch` refuses `web.archive.org` outright. Per the memory rule: those are
**tool-level user-agent exclusions**, not blocks on the programme and not evidence of anything about
the content. Where a 403 prevented reading a source, the line says `[NOT READ AT SOURCE]`.
