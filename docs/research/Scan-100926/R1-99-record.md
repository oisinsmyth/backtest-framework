# Scan-100926 · Round 1 — record

**Slate:** [`R1-00-slate.md`](R1-00-slate.md) · **campaign contract:**
[`00-SCHEMA.md`](00-SCHEMA.md) · **previous campaign:** [`../README.md`](../README.md).

**STATUS: COMPLETE — all four lanes in.** This record was opened when three had landed and
**extended in place** when `A1` arrived. `A1` was the lane the others depended on: `A2` stated its
prize *"needs data that lane A1 must deliver first."* **It delivers one of `A2`'s two families and
cannot deliver the other** (§2, `A1`).

**Under [R15](../../RULES.md#r15) nothing here closes or admits anything.** Nothing in this folder is
elevated out of `docs/research/`.

---

## 0. THE SHAPE OF THE ROUND

**Three lanes in, and the two that matter most disagree with each other.** `A3` reports the long leg
failing **gross**; `A2` reports it **unresolved rather than zero**, on a different benchmark, with
both sides measured. **That disagreement is the round's central result and it is recorded in §1, not
resolved.**

**And every lane found that a number this programme treated as its own weakness is the field's own
number.** Round 6 found it for **33.8 bp/side**. `A4` found it for **67% extraction precision**.
**Twice in two rounds.**

---

## 1. THE CENTRAL CONFLICT — `A2` vs `A3` ON THE LONG LEG

**Both lanes landed in the same round. Both measured. Neither is adjudicated here.**

| | `A3` — the long leg fails GROSS | `A2` — the long leg is UNRESOLVED, not zero |
|---|---|---|
| **statistic** | long-minus-**market**: mean **−0.04%/month**, mean `t` = −0.31, **Var(t) = 0.98**, below the luck null | long-minus-**each sort's own name-weighted universe**: **Var(t) = 1.35–1.81**, signal share **0.26–0.45** |
| **second dataset** | Muravyev–Pearson–Pollet `[read in full]`: long leg **−0.09%/month (t = −1.81)**; in **raw** return the top decile (0.96%) earns **less than deciles 5–9 of its own sort** | cash-based operating profitability long leg **+44 bp/month, t = 2.48** under a `$5` screen — **91% of its premium**, and it notes this agrees with Chen & Welch's own raw **+40 bp** |
| **the claim** | **fails R15's first hurdle — a positive GROSS mean — before costs are reached** | the premium exists in the long leg for the profitability family; the zero is a **benchmark artefact** |

> **THE CRUX IS THE BENCHMARK.** `A3`'s figure compares the long leg to the **value-weighted
> market**. `A2`'s objection is that an **equal-weighted** book does not compete with the
> value-weighted market — it competes with its own name-weighted universe — and that substituting
> the right benchmark moves the signal share from **0** to **0.26–0.45**.

**What is NOT in dispute.** Both read Chen & Welch; `A3` read it in full and `A2` validated its own
pipeline against its published medians (getting **53.4 / 20.3 bp** against their **48 / 19**). **So
this is not two different literatures. It is one literature and two benchmark choices**, and the
choice is now an open question with evidence on both sides.

**`A2` says explicitly that its finding is material to `A3`.** `A3` did not have `A2`'s measurement
when it wrote. **Neither brief is revised; both stand as written.**

---

## 2. What each lane returned

### `A1` — free, point-in-time, dead-inclusive fundamentals

**`A1`'s verdict in one line: the data gap IS closable, but the obvious endpoint is a silent
look-ahead and the cost is engineering rather than bandwidth.**

**The point-in-time question was TESTED, which is what the lane was set, and the answer splits the
three products apart.**

> **The `frames` endpoint is RESTATED and therefore unusable.** Kraft Heinz's FY2016 operating cash
> flow returns **2,648,000,000** carrying an accession **filed 2019-06-07**, against the
> **5,238,000,000** knowable on 2017-02-23 — **a 98% error, 2.3 years early.** Another issuer's
> 2020Q2 `Assets` return a 10-K/A value from 2022. **And `frames` rows carry no `filed` and no
> `form`, so the substitution is UNDETECTABLE.** SEC's own wording is the tell: it aggregates one
> fact per entity *"that is last filed"*.

**`companyfacts` is point-in-time RECONSTRUCTIBLE** — every vintage stamped with accession, form and
filing date — and `A1` rebuilt one issuer's balance sheet on **six named as-of dates**, getting the
right vintage each time. **The Financial Statement Data Sets are PIT by construction** (*"All numeric
data is 'as filed'"*) and are **the only product carrying an acceptance TIME.**

**A residual trap nobody warns about.** `filed` is a **date**, and **57.5% of recent 10-K/10-Q
submissions are accepted at or after 16:00 ET carrying that same day's `filed`** — up from **39.3% in
2012q2**. **For an overnight book on daily bars that is a same-session look-ahead in the majority of
cases.**

**Dead issuers are fully retained** — three named dead probes return 200 with histories to within
weeks of death, and two older failures 404 **only because they died pre-XBRL**. Every negative
control returned a genuine 404 with an XML `NoSuchKey` body. **So the binding gap is the TICKER, not
the fundamentals:** `company_tickers.json` is survivors-only for the **seventh** measured time,
`submissions.json` returns an empty `tickers` array for all three probes, and `companyfacts` reports
one dead issuer's name as **the successor shell**. The free bridge is **a union of two heuristics at
94.5–97.4%, whose false-positive rate `A1` could not measure and says so.**

**Two hard negatives.**

```
XBRL submissions   2010q1    478
                   2011q2  1,625
                   2011q3  6,980   -> small/mid names DO NOT EXIST before 2011q3, so
                                      ~21% of this programme's window is large-accelerated-only

SalesRevenueNet    2015  2,085 filers  ->  2019     1
CostOfGoodsSold    2015  1,296 filers  ->  2019     0
                   86-91% of distinct tags in any quarter are FILER-INVENTED EXTENSIONS
                                      -> a single-tag panel COLLAPSES at FY2018
```

**A new defect class for this programme, found unexpectedly.** One CIK's `Assets` at 2015-12-31 read
**23.4bn and then 3.4bn across vintages with NO restatement**, because the company became a different
company after a spin-off. **`companyfacts` shows only the current name and gives no warning; the
Financial Statement Data Sets do.** **No adjustment factor repairs a CIK whose contents changed
identity.**

**And one piece of evidence cutting AGAINST pessimism**, downloaded and read rather than taken from a
summariser. Du, Huddart & Jiang (2021) `[read in full]`, built on exactly these free products plus
the FASB calculation linkbase, find the accruals hedge pays **0.673%/month AS-FILED against
0.296%/month and insignificant on Compustat**, with four further named anomalies affected and 15 of
19 unaffected. **The as-filed data gives the STRONGER result, which is the opposite of the usual
assumption.** `A1` is explicit that this establishes the free data are **research-grade — not that
anything is profitable for this book.**

**The payoff, and a direct interaction with `A2` that matters.** Computable: **asset growth,
accruals, gross and operating profitability, investment, book-to-market, NOA growth, F-score and
distress, taxable income.** **NOT computable: net share issuance, because there is no split history
anywhere in XBRL** — and `A2` named the share-issuance family as its **cheapest non-free candidate**,
needing *"only a split-adjusted share count."*

> **OF `A2`'s TWO SURVIVING FAMILIES, `A1` UNLOCKS PROFITABILITY AND CANNOT DELIVER THE OTHER.**

Nothing segment-level and nothing needing pre-2011 small-cap fundamentals is reachable either.

### `A2` — the persistent-characteristic family

**The family is TWO families, not eight.** Post-2005 survivors reduce to **profitability** (gross,
operating, cash-based operating — annual accounting) and **external financing / share issuance**
(annual). **Book-to-market, accruals, size, Piotroski and Amihud illiquidity are negative or zero
over 2010–2024 — five of the eight canonical cost-honest low-turnover survivors do not survive this
programme's own window.**

**It measured rather than recapped** `[MEASURED IN BRIEF]`. The reference portfolio library publishes
the same **212 predictors at 1/3/6/12-month holds, under a `$5` price screen and a microcap screen,
and as daily returns** — ~380 MB pulled, and **the datasets' own long-short column reproduced exactly
from component bins, maximum discrepancy 0.0000 across 54 cells.**

**Holding-period flatness is the kill, and the flatness is a measurement.**

```
fundamentals premium by hold:  1m 18.3   3m 19.8   6m 18.2   12m 15.5   bp/month
```

**The premium accrues at a constant rate**, so a short hold takes a pro-rata slice and pays the full
round trip. **Breakeven hold for the best long-only characteristic is 3–6 months; a ten-bar hold is
short by 11×.** Established on daily data **with a positive control** that detects short-term
reversal as **11× front-loaded** and momentum as **back-loaded** — so "uniform" is a finding, not a
failure to resolve. The only concentrated piece is a **negative first day of the month** (−11 to −17
bp).

**The middle ground the slate asked about is empty: the fastest documented rebalance in the entire
331-signal census is ONE MONTH.** No cost-honest evidence exists at this programme's horizon because
nobody has published one.

**The free subset is open but empty**, with excluded separated from unavailable as instructed: 58 of
212 need only price/volume; **29 are EXCLUDED rather than unavailable, each named by clause**; 27 are
open and 21 need only daily OHLCV — **but 10 are negative over 2010–2024, only two reach t > 2, and
the best one's long leg is 2–4 bp/month against a 6.5 bp/month cost floor.** The cheapest non-free
candidate needs **only a split-adjusted share count**, but is **65% short-leg with over half its
premium in sub-`$5` names (1.06 → 0.48 under the screen).**

**Q5 answered plainly: yes, a different activity.** Daily bar survives and equal weighting survives
at a cost, but **the strategy object, the selection layer, the null and two of the four reporting
groups must be rebuilt.** **The prize is ~8 bp/month net long-only — and it needs what `A1` must
deliver first.**

**It also filled an absence with an operational substitute.** The prior campaign found **no paper
reports the nominal price distribution of any anomaly's legs**; `A2` confirmed that and instead
**measured the `$5` floor's cost at ~23% of the median premium**, finding that **the price and size
screens' ordering flips by family.**

### `A3` — the long-only problem

Its headline is in §1. Four things it added beyond what the previous campaign held:

**It read in full what round 6 had only as an abstract via a summariser**, finding the 51-page draft
on an open host and extracting every decile panel. **In the low-borrow-fee universe a long-only
account actually lives in, the whole spread collapses to +0.05%/month (t = 0.98)**, and **in the
Price category — the only input class this programme has free — the long leg is −0.12%/month
(t = −1.80)**. **It is an independent group with independent method, which repairs `K6`'s own
self-flagged largest fragility** (four load-bearing sources, one author, one dataset).

**It partly filled `K6`'s confirmed absence on price, and the finding cuts both ways.** Average share
price per leg: **long `$55.60`, short `$7.03`.** A **`$5` screen cuts the short leg's alpha 77% and
the spread 68% while leaving the long leg untouched** (+0.08% → +0.12%). **So this programme's floor
removes where the money was, not where it could have reached** — and the same paper states the
anomaly is *"not at all present in equal-weighted portfolios"*, **which is how this programme
weights.**

**The counter-evidence does not survive contact, and it recorded why rather than discarding it.** One
supportive paper charges **no trading costs**, its long-only value result exists **only in
microcaps**, its headline long-side figures are **not market-adjusted**, and **its own test cannot
reject a 50/50 split.** Separately a **long-short shop reproduced** the main pro-long-only paper and
found the optimal short weight is **30%, not zero**, tracing the long-leg advantage to a **mechanical
size exposure from the 2×3 construction.** **Five conflicts logged unadjudicated inside the brief.**

**The arithmetic nobody computes:** dropping the worst decile from an equal-weighted universe buys
**+1.7 bp/month gross — and +0.1 bp once hard-to-borrow names are out.** At a 67.6 bp round trip that
permits **2.5% of the book turning over monthly.** Labelled as the lane's own arithmetic.

**Sub-question 5 landed in excluded territory and was flagged rather than pursued**, as instructed.
The residue: the conditioning literature's long-only content is **itself a null** (long legs move 4
bp/month across sentiment regimes), and the peer-reviewed out-of-sample verdict on volatility
management is **negative**.

> **One observation recorded without a conclusion drawn from it:** Chen & Welch's own list of escapes
> from their negative result — **factor timing, ML combination, alternative data — is this
> programme's exclusion list.**

### `A4` — filing text at scale

**Text-level work is reachable; the volume question was never the constraint.** The targeted route —
phrase census → accession → `.hdr.sgml` — costs **~40,000 requests and ~0.31 GB over 2010–2026,
about 2¼ hours at 5 req/s.** The naive dissemination-feed route is **4.39 TB** (33-day HEAD sample:
136 MB/day in 2010 → 2.65 GB/day in 2023). **Three orders of magnitude apart.**

**It ran the route end to end and corroborated round 5 from a different layer** `[MEASURED IN
BRIEF]`. January 2021: 493 documents → 337 filings → `.hdr.sgml` retrieved **337/337, zero
failures** → **60.2% carry Item 2.02**, against round 5's **62.2%**. **Caveated hard: one month,
January is seasonally the worst pick, declarations are not initiations, and recall is unmeasured.**

**The real constraint is recall, not precision — and the bias has known sign.** The one paper doing
this task on 292,984 filings reports precision **12%→96% by confidence score**, and **a grep for
"recall" across all nine pages returns no match**; its corpus starts in **2022**. Round 5's statistic
is a **share**, whose bias is governed by recall — and **recall is plausibly LOWER inside earnings
releases**, because a declaration in paragraph fourteen of a nine-page release is harder to
phrase-match than a standalone one. **So round 5's 62.2% may be an underestimate.**

**Four independent error rates for extracting a typed fact from filing prose converge at 67–78%** —
and **this programme's own 67% is one of them.** **The second time in two rounds that a number
treated as our weakness is the field's own.**

**Negative findings reported as such.** A blind read of 14 phrase-family misses found **zero genuine
declarations**; the prior lane's credit-agreement-defined-term false positive turns out to be the
**second-largest class** (2 of 14, plus 4 more by the same mechanism). **No study testing filing-text
signals post-2010 net of realistic costs was found** — the best-known candidate ends in **2014**, is
short-side by construction, value-weighted, and reports no cost-netted number.

**Licensing is clean on retrieval** — 10 req/s aggregate **across machines**, a declared User-Agent
required because unclassified bots are prohibited regardless of rate, `robots.txt` restricting
nothing in `/Archives/`. **Redistribution of harvested text is unresolved, and the brief does not
treat absence of prohibition as permission.**

---

## 3. ROUTE AND HAZARD FINDINGS THAT TOUCH WORK ALREADY DONE

**Two bear on censuses the previous campaign already built.**

> **THE QUARTERLY `full-index` IS NOT POINT-IN-TIME.** SEC's own words: rebuilt weekly with
> **post-acceptance deletions applied**, and every `master.idx` from 2010Q1 to 2026Q1 carried the
> same recent `Last-Modified`. **Only the daily index and the Feed preserve what was visible on the
> day.** **Two censuses in the previous campaign were built off the quarterly index.**

> **FILINGS ACCEPTED AFTER 17:30 ET DISSEMINATE THE NEXT BUSINESS DAY**, so `filingDate` is wrong by
> a bar **in the look-ahead direction** for that population — **which is what this programme's puller
> keys on.**

**A strict improvement on the route rounds 4 and 6 used.** `-index-headers.html` **404s extend into
2014** (0/3 in 2010–13, 1/3 in 2014, 3/3 from 2015) — and **`.hdr.sgml` is the fix: 200 for 51/51
across 2010–2026, mean 921 bytes, carrying `<ACCEPTANCE-DATETIME>` and NUMERIC `<ITEMS>`**, where the
`.txt` header gives only prose item descriptions.

**The `items` parameter is ignored because it is not a parameter**, and the generalisation is nasty:
EDGAR full-text search **drops any unrecognised parameter silently** — a garbage parameter returns
**byte-identical** output — so **`locationCode` is silently ignored while `locationCodes` works. One
letter decides whether your filter applies, and the wrong spelling returns a larger, plausible, wrong
answer at HTTP 200.**

**More, from `A4`:** the **accession-number prefix is the filer agent's CIK, not the issuer's**
(paths built from it 404 with a gzipped `NoSuchKey`, **including files the same directory's
`index.json` lists as present**); **`forms=8-K` filters the root form and includes 8-K/A** (4 of
493); **no stemming** (`dividend` 2,456 vs `dividends` 2,414, **neither a superset**); a **10,000-hit
ceiling**; **`filings.recent` truncates** (7 of 18 accessions missing); and an **intermittent HTTP
500 with a 36-byte body on ~14% of requests, all clearing on retry — with an identical Elasticsearch
`took` proving a cached replay, so A REPEAT IS NOT AN INDEPENDENT CONFIRMATION.**

### THE WRONG-HTTP-200 CATALOGUE REACHES ELEVEN, AND TWO LANES COLLIDED ON THE NUMBER

Nine were on the record from the previous campaign. **`A2` and `A3` each found one and each
independently called theirs "the tenth" — recorded rather than silently renumbered.**

| | what returned 200 | what it was | found by |
|---|---|---|---|
| **10** | an NBER working-paper URL | **a genuine PDF of an ENTIRELY DIFFERENT PAPER** — catchable only by reading the title | `A3` |
| **11** | a request for a 222 MB zip | **a 2,430-byte HTML virus-scan-warning page** — caught by `file`, not status | `A2` |

---

## 4. CONFLICTS — RECORDED, NOT ADJUDICATED

**On the principal's standing instruction. All readings stand.**

| # | question | readings |
|---|---|---|
| **D1** | **does the long leg pay?** | **§1 — the round's central conflict.** `A3`: fails gross, Var(t) = 0.98 against the VW market · `A2`: Var(t) = 1.35–1.81 and signal share 0.26–0.45 against each sort's own name-weighted universe. **The benchmark is the crux** |
| **D2** | **what does the `$5` screen cost?** | `A3`: it **cuts short-leg alpha 77% and the spread 68% while leaving the long leg untouched** · `A2`: it **costs ~23% of the median premium**, and for share issuance **over half the premium is in sub-`$5` names (1.06 → 0.48)**. Different signals, opposite-pointing implications |
| **D3** | **the `acceptanceDateTime` timezone defect rate** | prior rounds: **35/60 (58%)** and **32/51 (62.7%)** · `A4`: **1/11 (9%)**, weighting the priors on sample size while confirming the defect is present · **`A1`: 37/92 (40.2%) in 2021q2 and 0/88 in 2026q2**, settled with 26 late filings whose `filed` rolled. **`A1` is the first reading to offer a MECHANISM that could reconcile the others — the defect may be ERA-DEPENDENT and may have been fixed. RECORDED AS A CANDIDATE EXPLANATION, NOT AN ADJUDICATION. All four readings stand.** |
| **D4** | **does SEC ignore `Range` headers?** | round 6: yes, flatly · `A4`: **path-dependent** — `master.idx` returns 200 with the full 32 MB **despite advertising `Accept-Ranges: bytes`**, while the feed tarball honours 206 |
| **D5** | **the 35% vs 85% replication split** | `K6` (round 6): **weights neither**, because neither applies costs · `A2`: **reaches its own view**, naming which it weights and on which specific liquidity-category cell |
| **D6** | **do the canonical low-turnover survivors survive?** | the canonical list: eight cost-honest low-turnover survivors · `A2`, measured on 2010–2024: **five of the eight are negative or zero in this programme's own window** |
| **D7** | **`A3`'s own five internal conflicts** | logged unadjudicated inside its brief — including one supportive paper whose **own test cannot reject a 50/50 split**, and a **long-short shop's reproduction** putting the optimal short weight at **30%, not zero** |
| **D8** | **one paper disagreeing with itself** | its **draft and published abstract differ in SIGN** (+0.02% → −0.01%), and **its prose disagrees with its own tables** on three high-fee shares. `A3` recorded all three readings |

| **D9** | **is `A2`'s cheapest candidate reachable?** | `A2`: the share-issuance family is the cheapest non-free candidate, needing **"only a split-adjusted share count"** · `A1`: **net share issuance is NOT computable — there is no split history anywhere in XBRL.** **Not a contradiction but a DEPENDENCY FAILURE** — the two lanes are right about different halves, and together they close that route unless a split source is found elsewhere |
| **D10** | **does as-filed data weaken a result?** | the usual assumption, and this programme's own worry: vendor-standardised data is cleaner · `A1` `[read in full]`: the accruals hedge pays **0.673%/month AS-FILED against 0.296%/month and INSIGNIFICANT on Compustat** — **the free data gives the STRONGER result on that signal**, with 4 of 19 anomalies affected and 15 unaffected |

**Two CORROBORATIONS, recorded so they are not mistaken for conflicts.** `A4`'s **60.2%** against
round 5's **62.2%** — different method, different granularity, two points apart, **with the recall
caveat meaning round 5's figure may be an underestimate rather than an overestimate.** And the
**67–78% extraction-precision convergence across four independent sources**, one of which is this
programme's own measurement.

---

## 5. What this record does not claim

- **Nothing here was measured on this programme's fixture.** `[MEASURED IN BRIEF]` means a public
  file or endpoint. Figures restated from our own record — 33.8 bp/side, the 67.6 bp round trip, the
  `$5` floor, ~10 effective instruments, 67% phrase-match precision — are quoted, not recomputed.
- **Nothing was backtested, no null was drawn, no cell was scored, no candidate exists.**
- **Nothing is repaired**, including every defect carried from the previous campaign and the two new
  route findings in §3.
- **No territory is closed, and the central question is OPEN rather than answered** — §1 is a
  disagreement, not a verdict. Closure is the principal's under [R15](../../RULES.md#r15).
- **Both books are unchanged.**
