# 07 — Published statistics, aggregators and the claims tier

**Lane 07 of the Prop-Firm-080926 review.** Opened and closed 2026-09-08.
Schema and stopping rules: [`00-SCHEMA.md`](00-SCHEMA.md). Filed toward **D386**.

**Stopping rule that bound: the HARD CAP OF 20 SOURCES.** Saturation was *close* — by source 14 the
secondary tier was returning only restatements of two upstream numbers — but the cap bound first and
the lane stopped there, as §3 of the schema instructs. **Nothing here is evidence under R15.**

---

## VERDICT

**Two usable statistics exist in this entire sector. Everything else is either a dollar total with no
denominator, or a number with no methodology being recycled between parties who are paid when you
buy an evaluation.**

The two:

1. **Topstep's own 2025 performance disclosure** — four rates, each with its denominator *stated in
   the sentence*, on a named date range. This is the only firm-published statistic found that
   distinguishes per-attempt from per-person. It is the highest-value artefact in this lane.
2. **The FPFX Tech dataset** — 300,000+ accounts / 100,000 traders / 10 unnamed firms, reported by
   Finance Magnates in Sept 2024. Stated N, stated funnel, no date range, self-selected sample (it is
   FPFX's own platform tenants). Usable *with* those caveats.

**And the first one falsifies the sector's headline claim outright.** The universal "5–10% pass rate"
is contradicted by the only firm that actually publishes: Topstep's per-attempt rate is **16.8%** and
its per-person rate is **51.8%**. The aggregator most often cited for the 5–10% figure
([QuantVPS](https://www.quantvps.com/blog/prop-firm-statistics)) states "TopStep pass rate 5–10%" on
a page carrying Topstep affiliate links, while Topstep's own front page says 16.8%.

### The finding this lane was built to produce

**Topstep's published per-attempt pass rate is BELOW the zero-edge baseline, and materially so.**

| | rate | object |
|---|---|---|
| [D379](../../decisions/D379-the-prop-account-is-a-down-and-out-call-and-hurdle-P-has-no.md) §A2, zero edge, **trailing** floor, $250/trade | **26.5%** | per attempt, simulated |
| D379 §A2, zero edge, trailing, across the whole risk sweep $250→$1,000 | 26.5% – 29.4% | per attempt, simulated |
| D379 §A2, zero edge, **static** floor / all-in (`2000/5000`) | 40.0% | per attempt, simulated |
| D379 §A2, all-in **with a $10 round turn** | 25.5% | per attempt, simulated |
| **Topstep, observed, Jan–Dec 2025** | **16.8%** | **per Combine initiated** |

Topstep runs a trailing drawdown, so the like-for-like baseline is the **26.5%–29.4%** band. The
observed figure is **0.63×** the low end of that band and sits below every cell in D379's sweep.
**The population of Topstep evaluation attempts performs worse than a driftless random walk against
the same barrier.** The implied edge of the marginal evaluation buyer is not small-and-positive; it
is **negative**.

**Four candidate explanations, and this lane cannot separate them.** Naming them is the honest output:

- **(a) Costs.** D379 already measured the mechanism: a $10 round turn moves the all-in pass rate
  40.0% → 25.5%. A zero-drift walk becomes a negative-drift walk the moment it crosses the spread,
  and evaluation traders cross it many times. This is the explanation most consistent with the size
  of the gap.
- **(b) Abandonment — and this is a hole in Topstep's own denominator.** "Trading Combines
  **initiated**" includes Combines bought and abandoned, or left unresolved when the subscription
  lapses. The D379 simulation runs every path to absorption; the observed statistic does not.
  **Topstep does not disclose how an abandoned Combine is treated.** If a material share of the
  denominator never resolves, the comparison is contaminated in a known direction. This single
  undisclosed convention is the largest threat to the finding.
- **(c) Rules D379's toy does not model** — minimum trading days, the consistency rule, the daily
  loss limit. Each is an additional absorbing condition, so each pushes the observed rate down
  relative to a toy that omits it.
- **(d) Oversizing** past the sweep's $2,000 all-in point, where the floor has no room to ratchet.

**But note what survives all four.** Every one of (a)–(d) drives the implied edge to ≤ 0. The finding
that dies is *"the marginal evaluation buyer has positive edge and the barrier is the only obstacle."*
That is dead on Topstep's own published number. What (b) threatens is only the *magnitude* of the gap.

**Stage 0 consequence:** the baseline per distinct geometry that the schema calls for should be
computed **with an abandonment convention declared**, or the observed rates cannot be compared to it
at all. That is a design requirement this lane hands to Stage 0, and it was not previously stated.

### Two quantities derived from the published numbers

**1. Implied attempts per participant ≈ 4.0, and it is an upper bound.**
Topstep publishes both a per-attempt rate (16.8%) and a per-person at-least-once rate (51.8%). Under
i.i.d. attempts, `1 − (1 − 0.168)^n = 0.518` gives `n = ln(0.482)/ln(0.832) = 3.97`. Trader
heterogeneity *raises* the at-least-once probability for fixed `n` (Jensen: `(1−p)^n` is convex), so
the true mean is **≤ ~4.0**. **Independent cross-check: FPFX reports "average challenge costs $800
per account across ~3 challenges."** Two unrelated sources, same order. This is the number that
converts a pass rate into an acquisition cost, and it is exactly D379 §A2's `fee ÷ pass rate`.

**2. Topstep's per-person paid-out rate is 17.3%, not 9%.**
`51.8% × 33.3% = 17.25%` of participants who entered a Combine ever received a payout. The widely
circulated "100 traders → 17 funded → 9 paid" funnel is **arithmetically wrong**: it treats the
per-*Combine* 16.8% as if it were per-person, then multiplies by the per-person 51.8%, chaining two
rates measured on different denominators and double-counting the same funnel step. It understates
the per-person paid rate by 2×.

### The number nobody quotes

**0.71%.** Topstep's own disclosure: that is the share of Express Funded participants "called up to a
Live Funded Account." **Over 99% of Topstep "funded" accounts never touch real capital.** This figure
appears in Topstep's own footer and in essentially none of the aggregator coverage that cites the
other three rates from the same sentence. Selective quotation of a four-part disclosure is itself a
tell.

### The circular citation, stated plainly

The sector's most-repeated statistic has **no primary source anywhere**:

> **QuantVPS** attributes its 7% payout figure to **FunderPro**.
> **FunderPro's** article attributes its 7% figure to **QuantVPS (June 2025)**.
> Neither states a methodology. **QuantVPS sells VPS hosting to prop traders. FunderPro sells
> evaluations.** FunderPro's article closes with a pitch for FunderPro.

FunderPro additionally cites "The Funded Trader" (another prop firm) for **20%** of funded traders
receiving a reward — a 3× disagreement with the 7% on the same page, unreconciled, both
undisclosed. The 7% figure *does* have a real upstream origin in the FPFX dataset, but the citation
chain that popularised it does not reach it; the number is laundered, not sourced.

---

## The statistics table

**Rate types: `PASS` = completed an evaluation · `FUND` = reached a funded account · `PAID` =
received a payout.** Verdict column: **USABLE** / **WEAK** / **UNUSABLE**.

| # | statistic | which rate | denominator | who computed | methodology disclosed? | date | vs D379 baseline | verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | **16.8%** of Trading Combines initiated were completed | **PASS** | **Trading Combines initiated** (attempts) | **Topstep (firm, self)** | Partial — denominator + range stated; **abandonment convention NOT stated** | Jan–Dec 2025 | **BELOW 26.5% trailing baseline** | **USABLE** |
| 2 | **51.8%** of individual participants advanced to Funded Level at least once | **FUND** | **individual participants entering ≥1 Combine** (people) | Topstep (firm, self) | Partial, as above | Jan–Dec 2025 | n/a — different object | **USABLE** |
| 3 | **33.3%** of individual participants at Funded Level received a payout | **PAID** | **participants at Funded Level** (people, conditional) | Topstep (firm, self) | Partial, as above | Jan–Dec 2025 | n/a | **USABLE** |
| 4 | **0.71%** of Express Funded participants called up to Live Funded | *stage transition, none of the three* | Express Funded participants | Topstep (firm, self) | Partial, as above | Jan–Dec 2025 | n/a | **USABLE** |
| 5 | **17.3%** = 51.8% × 33.3% | **PAID** | participants entering ≥1 Combine | *derived here* | derived from #2, #3 | 2025 | n/a | **USABLE (derived)** |
| 6 | **≈4.0** attempts per participant (upper bound) | *implied* | — | *derived here* | derived from #1, #2 under i.i.d. | 2025 | — | **USABLE (derived, bounded)** |
| 7 | **14%** of traders passed the challenge and obtained a funded account | **FUND** | **traders** (100,000, across 10 firms) | **FPFX Tech** (platform vendor) | Partial — N and firm count stated; **no date range, firms unnamed, self-selected (own tenants)** | rep. Sep 2024 | n/a | **USABLE w/ caveats** |
| 8 | **~45%** of funded traders achieved a payout | **PAID** | **funded traders** (conditional) | FPFX Tech | Partial, as above | rep. Sep 2024 | n/a | **USABLE w/ caveats** |
| 9 | **7%** of all traders ever achieved a payout | **PAID** | **all traders in sample** | FPFX Tech | Partial, as above | rep. Sep 2024 | n/a | **USABLE w/ caveats** |
| 10 | average payout ≈ **4%** of plan size; avg challenge spend **$800 over ~3 challenges** | *economics* | FPFX sample | FPFX Tech | Partial | rep. Sep 2024 | corroborates #6 | **USABLE w/ caveats** |
| 11 | **~70%** of failures come from hitting loss limits, not missing profit targets | *failure mode* | **500,000 traders** (hoc-trade) | hoc-trade, via Velotrade | N stated; nothing else. Not traced to source | cited Jul 2026 | **consistent with the down-and-out framing** | **WEAK** |
| 12 | **<100 of 24,000** live accounts consistently profitable (**0.4%**) | *profitability, not a pass rate* | 24,000 "live" accounts at one firm | **CFTC** (sworn complaint) | Litigation pleading; not a study | filed Aug 2023 | far below any baseline | **WEAK — see note** |
| 13 | "**5–10%** of traders pass evaluations" | **PASS** (claimed) | **UNSTATED** | QuantVPS ↔ FunderPro ↔ HighStrike, circular | **NONE** | 2024–2026 | contradicted by #1 and #2 | **UNUSABLE** |
| 14 | "**7%** receive a reward" *as cited by QuantVPS/FunderPro* | **PAID** (claimed) | **UNSTATED** | circular pair | **NONE** | 2025 | — | **UNUSABLE as cited** (origin #9 is usable) |
| 15 | "**20%** of funded traders receive a reward" | **PAID** (claimed) | **UNSTATED** | The Funded Trader (a prop firm), via FunderPro | **NONE** | Mar 2025 | contradicts #14 by 3× | **UNUSABLE** |
| 16 | Apex "**15–20%** first-attempt pass rate", "**40%** with resets" | **PASS** (claimed) | **UNSTATED** — and "with resets" is almost certainly per-person, quietly compared to a per-attempt number | unattributed; appears on affiliate pages | **NONE** | 2026 | — | **UNUSABLE** |
| 17 | Earn2Trade "**verified** pass rate **10.42%**" (2024); "**8.89%**" (2025) | **PASS** (claimed) | **UNSTATED** | unattributed; **not found on Earn2Trade's own current site** | **NONE** — "verified" is a bare adjective | 2024 / 2025 | — | **UNUSABLE** |
| 18 | Take Profit Trader "**20.37%**" (Jan–Aug 2023) | **PASS** (claimed) | **UNSTATED** (per-attempt or per-person?) | unattributed | **NONE** (date range is the only disclosure) | 2023 | — | **UNUSABLE** |
| 19 | FTMO "**26%** Challenge→Verification, **60%** Verification→Funded, ~16% combined" | **PASS**/**FUND** (claimed) | **UNSTATED** | attributed to FTMO by third parties; **NOT FOUND on ftmo.com** | **NONE** | — | — | **UNUSABLE — attribution failed** |
| 20 | FTMO "**$650M+** paid in rewards", "**4.5M+** customers", "**200,000+** traders funded" | *dollar/headcount totals* | — | FTMO (firm, self) | n/a — **these are not rates** | 2026 | — | **UNUSABLE for this question** |
| 21 | FTMO "average 1-Step reward **$3,336.61**" | *average payout* | **NO N STATED** | FTMO (firm, self) | **NONE** | 2026 | — | **UNUSABLE by construction** |
| 22 | Topstep "**$1.4B+** paid out", "**7,000+** traders paid weekly" | *dollar/headcount totals* | "internal data of YTD average" | Topstep (firm, self) | minimal | 2026 | — | **UNUSABLE for this question** |
| 23 | Prop Firm Match: **$324,963,316** tracked payouts, 2025 | *dollar total* | firms that opt in | Prop Firm Match | **self-reported by firms, not independently verified; FTMO and The5ers absent** | 2025 | — | **UNUSABLE for this question — no trader denominator anywhere** |
| 24 | "**86%** failed challenges", 100,000 traders / 10 firms | **PASS** (claimed) | 100,000 traders | restatement of FPFX #7 (14% → 86%) | inherits FPFX | 2024 | — | **duplicate of #7, not independent** |
| 25 | "**93%** of **funded** prop traders never see a payout" | **PAID** (claimed) | **WRONG DENOMINATOR** | CoinGape headline | inherits FPFX | 2026 | — | **UNUSABLE — see tell #3** |
| 26 | "**80%** fail in prop trading globally" | **PASS** (claimed) | **UNSTATED** | Finance Magnates headline | **NONE** | — | — | **UNUSABLE** |
| 27 | "**45.6%** marginal-profile pass rate; **26.5%** probability of ever collecting" (Apex) | **PASS**/**PAID** (claimed) | **UNSTATED** | aggregator | **NONE — this is a simulation output presented as a measurement** | 2026 | — | **UNUSABLE — see tell #7** |

**Note on #12 (My Forex Funds):** the source is a CFTC complaint — a sworn pleading, the highest
evidentiary tier in this lane — but three things disqualify it as a sector statistic. It is an
*allegation*; **the case was dismissed in 2025 with sanctions sought against the CFTC**; and the
complaint's own theory is that this firm *actively sabotaged* traders (server-side execution
handicapping, pretextual terminations). It is an outlier by construction, not a floor for honest
firms. Lane 06 owns the litigation; it is recorded here only because the number circulates as a
pass-rate statistic and should not.

### `NOT PUBLISHED` — schema field 23, per firm

| firm | pass/payout statistic published by the firm? |
|---|---|
| **Topstep** | **YES** — four rates, dated, denominators stated. The only one. |
| **FTMO** | **NO.** Dollar and headcount totals only. No pass rate found on ftmo.com. Third-party attributions of a 26%/60% split to FTMO **could not be confirmed** and should be treated as fabricated attribution until sourced. |
| **Apex Trader Funding** | **NOT PUBLISHED** — payout dollar totals only; the "15–20%/40%" figures appear solely on affiliate pages, unattributed. |
| **MyFundedFutures** | **NOT PUBLISHED** — no pass, funded or payout rate located. |
| **Take Profit Trader** | **NOT PUBLISHED** — the "20.37%" is unattributed and undated as to source. |

---

## The claims tier — hypotheses only, never evidence

**Structural context, recorded first because it explains the rest.** Affiliate commission in this
sector is **20–30% of the evaluation fee, and the commission event is the challenge purchase — not
the trader's success.** Nobody in the content layer is paid when you get funded, and nobody loses
when you fail. Every incentive points at maximising evaluation purchases. This makes the revenue-
maximising published pass rate one that is **low enough to make passing feel like an achievement
worth preparing for, but not so low that buying looks irrational** — which is a fair description of
"5–10%, but here is how to beat it." That is the most economical explanation for why the sector
converged on an unsourced number and stayed there.

Every row below is a **hypothesis with a falsifier**, not a finding.

| claim | who benefits if you believe it | the specific number that would falsify it | status |
|---|---|---|---|
| "Only 5–10% pass — it's elite" | firms (fee justified as selective); affiliates (sets up the paid guide) | any methodology-disclosed per-attempt rate materially outside 5–10% | **ALREADY FALSIFIED** by Topstep: 16.8% per attempt, 51.8% per person |
| "Firm X has a higher pass rate, pick X" | the affiliate holding X's link | X's and Y's rates computed on the *same* denominator, same period | **untestable** — no two firms publish on a common denominator |
| "Prop firms want you to fail" | rival firms; the "we're the honest one" pitch | evaluation-fee revenue ÷ trader payouts. FTMO: $650M paid vs 4.5M customers → at a $150 mean fee, gross fees ≈ $675M, i.e. near parity | **open, and computable** — neither numerator nor denominator is published together |
| "Follow the rules and stay disciplined and you'll pass" | firms — recasts failure as a character defect rather than a geometry outcome | the zero-edge baseline. **At zero edge with a trailing floor you fail 73.5% of the time however disciplined you are** | **falsified in principle by D379 §A2** — discipline that creates no edge cannot beat 26.5% |
| "Risk 0.5% per trade to pass" | course sellers | pass rate as a function of bet size at zero edge. D379's sweep: 26.5% → 29.4% as risk *rises* $250→$1,000, and 40.0% all-in | **FALSIFIED IN SIGN** — smaller size *lowers* the zero-edge pass rate; bold play is optimal at zero edge |
| "$1.4B / $650M paid out proves your odds" | firms | that dollar figure ÷ evaluations sold | **never published together** — the denominator is the whole question |
| "Passing service / signals, $199/yr" | the seller | a pre-registered out-of-sample record on an untouched fixture (R8) | **none offered by any seller found** |
| "92% fail" / "93% never get paid" clickbait | affiliates (urgency) | the denominator | **UNUSABLE** — denominator-swapped restatements of FPFX's 7% |

**Note per the safety brief.** Every commercial page in this lane carried on-page directives —
discount codes (`APEX90`, `ALGO2026`, `FUTURES60`), "85% OFF" / "19% OFF" banners, "Limited time
only" urgency, and sign-up CTAs. **None were acted on.** No page was found to contain an instruction
addressed to an automated agent; the directives were ordinary commercial solicitation. Nothing was
signed up for, no link followed as a referral, no data entered.

---

## The recurring bullshit tells, with one example each

1. **A rate with no denominator.** "7% get paid" — of all traders, of funded traders, or per
   evaluation? Three different numbers. *Example:* QuantVPS's table, where not one of ten rows states
   a denominator.
2. **Circular citation between commercially interested parties.** *Example:* QuantVPS cites FunderPro
   for the 7%; FunderPro cites QuantVPS for the 7%. One sells hosting to prop traders, the other
   sells evaluations. No primary source exists at either end.
3. **Denominator swap on restatement.** *Example:* FPFX measured 7% of **all traders** paid.
   CoinGape's headline: "**93% of funded prop traders** never see a payout." Under FPFX's own
   numbers, 55% of *funded* traders never get paid — not 93%. The complement was computed on one
   denominator and relabelled with another.
4. **Chaining rates measured on different denominators.** *Example:* "100 traders → 17 funded → 9
   paid," built by treating Topstep's per-**Combine** 16.8% as per-person and then multiplying by the
   per-**person** 51.8%. The right per-person answer is 51.8% funded and 17.3% paid.
5. **An average with no N.** *Example:* FTMO's "average 1-Step reward $3,336.61" — a figure that
   cannot be interpreted at all without the count it averages over, and the count is what a customer
   actually wants.
6. **Cumulative dollars offered where a rate was asked for.** *Example:* "$1.4B+ paid out," "$650M+
   paid in rewards," "$325M tracked." A large numerator with the denominator withheld. Note that
   Prop Firm Match's $325M is additionally **self-reported by the firms being ranked**, with FTMO and
   The5ers absent entirely.
7. **A model output presented as a measurement.** *Example:* an aggregator's "45.6% marginal-profile
   pass rate" and "26.5% probability of ever collecting" for Apex — no data, no model disclosed,
   written in the register of an observation. (That the second figure coincides with D379's own
   simulated 26.5% is a coincidence, and a useful reminder that a plausible-looking barrier number is
   cheap to generate.)
8. **"Verified" or "Official Data" as a bare adjective.** *Example:* Earn2Trade's "verified pass rate
   of 10.42%" — no verifier named, no method, and the figure is absent from Earn2Trade's own current
   site.
9. **Precision as a proxy for provenance.** *Example:* 10.42%, 8.89%, 20.37%, $3,336.61. Topstep's
   0.71% is precise *and* sourced; the others are precise and unsourced. Two decimal places is not a
   methodology.
10. **The statistic and the discount code on the same page.** *Example:* Velotrade's "transparency
    report" carries an `ALGO2026` "20% off all challenges · Limited time only" banner above its own
    analysis of why traders don't get paid. Velotrade discloses it is a market participant; most do
    not.
11. **The aggregator contradicting the firm's own disclosure while linking to that firm.** *Example:*
    QuantVPS states "TopStep pass rate 5–10%" on a page carrying Topstep affiliate links, while
    Topstep's front page states 16.8%. The aggregator did not read the source it monetises.
12. **Selective quotation of a multi-part disclosure.** *Example:* Topstep publishes four rates in one
    sentence. The fourth — **0.71%** reaching a Live Funded Account — is almost never quoted, while
    the other three are quoted constantly.

---

## What lane 07 hands forward

- **Topstep's 16.8% is the single most useful external number in this review.** It is per-attempt, on
  a trailing geometry, and it sits below D379's zero-edge band. Stage 0 should treat it as the
  calibration target for the Topstep-like geometry.
- **Stage 0 must declare an abandonment convention** before any observed rate is compared to a
  simulated one. Confound (b) is otherwise uncontrolled, and it is the one that could move the
  headline.
- **`fee ÷ pass rate` now has both terms for one firm.** ~4.0 attempts per funded account (upper
  bound, i.i.d.), corroborated at ~3 by FPFX. This is the unpriced `BOOK_PROP` "20 accounts needed
  for $50k" line, and it is now bounded from published data.
- **Field 23 is answered for all five firms**, four of them `NOT PUBLISHED`.
- **No pass-rate statistic for MyFundedFutures exists.** Lane 01's payout-ladder task is unaffected,
  but D379 §4 will have no MFFU-specific pass rate to work with.

---

## Sources

**20 sources — the cap, which is the rule that bound.** Tier per schema §4: primary (firm T&Cs,
filings) / secondary (press, aggregators) / claims (marketing, forums). Negative results included as
mandatory entries.

| # | URL | accessed | tier | sought | yielded |
|---|---|---|---|---|---|
| 1 | https://www.topstep.com/our-program | 2026-09-08 | **primary** | field 23; any firm-published pass/payout rate | **YIELDED — the lane's central artefact.** Verbatim 2025 disclosure, four rates, denominators stated in-sentence: 16.8% per Combine initiated / 51.8% per participant / 33.3% of funded / 0.71% Express→Live. Methodology note: covers simulated *and* live environments. **Abandonment convention not stated.** |
| 2 | https://www.topstep.com/ | 2026-09-08 | **primary** | independent confirmation of #1 | **YIELDED.** Same four rates verbatim, confirming #1 is a site-wide disclosure not a one-page artefact. Plus "$1.4B+ paid out" (all-time, no denominator) and "7,000+ traders paid weekly" ("internal data of YTD average"). |
| 3 | https://ftmo.com/en/ | 2026-09-08 | **primary** | field 23 for FTMO | **YIELDED A NEGATIVE, which is the finding.** FTMO publishes **no** pass rate, funded rate or payout rate. Only "$650M+ paid in rewards", "4.5M+ customers", "140+ countries" — totals with no denominator. Directly contradicts third-party claims that FTMO publishes a 26%/60% split. |
| 4 | https://www.cftc.gov/PressRoom/PressReleases/8771-23 | 2026-09-08 | **primary** | hard numbers in the My Forex Funds action | **BLOCKED — HTTP 403 on direct fetch.** Content recovered via search index only: 135,000+ customers, $310M+ in fees, **<100 of 24,000 live accounts consistently profitable (~0.4%)**. Recorded as WEAK (allegation; case dismissed 2025; firm alleged to have sabotaged traders). Lane 06 should fetch this by another route. |
| 5 | https://www.financemagnates.com/forex/analysis/exclusive-only-7-of-300000-prop-trading-accounts-achieved-payouts/ | 2026-09-08 | secondary | a dataset with a stated N and method | **YIELDED — the second usable statistic.** FPFX Tech: 300,000+ accounts / 100,000 traders / 10 firms. 14% funded → ~45% of those paid → 7% of all traders. Avg payout ~4% of plan; avg spend $800 over ~3 challenges. **No date range; firms unnamed; sample self-selected (FPFX's own tenants).** |
| 6 | https://www.quantvps.com/blog/prop-firm-statistics | 2026-09-08 | claims | the origin of "5–10%" and "7%" | **YIELDED, as a negative about the sector.** Ten statistics, **not one with a stated denominator or methodology**. Attributes 7% to FunderPro. States "TopStep pass rate 5–10%" while carrying Topstep affiliate links — contradicted by #1/#2. Carries `FUTURES60` discount code; QuantVPS sells VPS to prop traders. |
| 7 | https://funderpro.com/blog/prop-trading-pass-rates-in-2025-what-the-data-really-shows/ | 2026-09-08 | claims | the other end of the 7% chain | **YIELDED — closes the circle.** Attributes 7% to **QuantVPS (June 2025)**, which attributes it to FunderPro. No methodology. Also cites The Funded Trader for 20% (3× disagreement, unreconciled). FunderPro is itself a prop firm; the article closes with a FunderPro pitch. |
| 8 | https://velotrade.com/reports/prop-firm-transparency | 2026-09-08 | claims (self-disclosed participant) | a methodology-disclosed rulebook study | **PARTIAL.** Method disclosed: six firms' published rules pages read, July 2026, author discloses it is a market participant — better disclosure than anything else in the tier. Rates are all restatements of FPFX #5. New: hoc-trade, **~70% of failures from loss limits not missed targets, N=500,000** (untraced). Carries `ALGO2026` "20% off all challenges" banner. |
| 9 | https://www.financemagnates.com/forex/prop-firm-match-tracked-about-325-million-in-payouts-to-traders-in-2025/ | 2026-09-08 | secondary | whether the payout tracker yields a RATE | **YIELDED A NEGATIVE.** Dollar totals only: $324,963,316 (2025); FundedNext $107.8M, FundingPips $97.1M, FundedNext Futures $46.9M. **Data "shared directly by firms", not independently verified. FTMO and The5ers absent.** No trader count, no denominator, no rate of any kind. |
| 10 | https://propfirmmatch.com/payouts | 2026-09-08 | secondary | the tracker's own methodology statement | **BLOCKED — HTTP 403.** Methodology recovered only second-hand via #9. Recorded so this is not re-attempted with WebFetch. |
| 11 | https://tradecovex.com/guides/how-many-combines-passed-express-topstep-2025 | 2026-09-08 | claims | corroboration of Topstep's 16.8% | Search-surface only. Corroborates the 16.8% figure and labels it "[Official Data]". Source of the erroneous "100 → 17 → 9" funnel (tell #4). |
| 12 | https://traderssecondbrain.com/guides/prop-firm-pass-rate | 2026-09-08 | claims | cross-firm pass rates | Search-surface. Restates Topstep's four rates; attributes an unconfirmed 26%/60% split to FTMO — **the attribution #3 falsifies.** |
| 13 | https://coinlaw.io/ftmo-statistics/ | 2026-09-08 | claims | FTMO disclosure gap | Search-surface. Headline concedes FTMO "still will not say how many traders failed"; source of the "$3,336.61 average with no N" observation. Otherwise unsourced. |
| 14 | https://coingape.com/blog/93-of-funded-prop-traders-never-see-a-payout-a-new-report-explains-why/ | 2026-09-08 | claims | the "93%" figure's provenance | **YIELDED a clean example of tell #3.** The 93% is 100−7 from FPFX, computed on *all traders* and relabelled *funded traders*. FPFX's own funded-never-paid figure is 55%. |
| 15 | https://track360.io/blog/prop-firm-affiliate-marketing-playbook-2026 | 2026-09-08 | claims (industry-facing) | the structural incentive | **YIELDED the structural context.** Affiliate commission **20–30% of the evaluation fee**, commission event is the **challenge purchase**, not trader success. Also documents self-referral fraud (affiliates buying through own links, then refunding). |
| 16 | https://fortunly.com/statistics/prop-firm-challenge-pass-rate-statistics/ | 2026-09-08 | claims | independent pass-rate data | **NOTHING NEW.** Restates 5–10%. No denominator, no methodology. Saturation signal. |
| 17 | https://thepropfirmguide.com/prop-firm-statistics/ | 2026-09-08 | claims | independent pass-rate data | **NOTHING NEW.** Restates the same 5–10% / 7% pair. Saturation signal. |
| 18 | https://damnpropfirms.com/trading-guides/prop-firm-evaluation-pass-rates-statistics-reality-check/ | 2026-09-08 | claims | independent pass-rate data | **NOTHING NEW.** Same pair, no denominators. Saturation signal. |
| 19 | https://atmosfunded.com/prop-firm-statistics/ · https://statistics.ge/prop-firm-statistics/ · https://tradeify.co/post/futures-prop-firm-statistics-2026 | 2026-09-08 | claims | independent pass-rate data | **NOTHING NEW — logged as one cluster.** Three near-identical "Prop Firm Statistics 2026" pages, two of them published by prop firms selling evaluations (Atmos, Tradeify). Recycled 5–10% / 7%. This cluster is what saturation looks like. |
| 20 | https://tradelikemaster.com/blog/how-to-pass-ftmo-challenge-2026-complete-guide ("92% Fail") · https://challengepassed.gumroad.com/l/passyourftmochallenge ($199/yr) | 2026-09-08 | claims | the paid-guide / passing-service tier | **YIELDED only as claims-tier specimens.** "92% Fail" is an unsourced clickbait denominator; the Gumroad listing sells a $199/yr FTMO-passing product with no track record offered. **Not purchased, not signed up for, no link followed as a referral.** |

**Negative results also recorded above, per schema §4:** #3 (FTMO publishes no rate — a finding, not
an absence), #4 and #10 (403-blocked, so they are not re-attempted), #9 (payout tracker yields no
rate), and #16–#19 (five consecutive sources yielding zero new facts — saturation was reached, but
the 20-source cap bound first and is the rule recorded as binding).

**Searches run that produced no new primary source, so they are not repeated:** firm-published pass
rates for Apex / MyFundedFutures / Take Profit Trader (none exist); an Earn2Trade primary for the
10.42% (not on their site); an academic or regulator-mandated pass-rate dataset (none found — the
FPFX vendor dataset is the closest thing the sector has).
