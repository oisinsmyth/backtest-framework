# working/leads5/ — round 5, **COMMISSIONED**

**Prepared 2026-09-09** after round 4 was consolidated into
[`docs/research/the-timestamp-round.md`](../../docs/research/the-timestamp-round.md), and
**commissioned 2026-09-10 on the principal's instruction.** **Six agents, one lane each, running in
parallel**; briefs land here as `J1`–`J6`. The quarantine contract of
[`../leads/README.md`](../leads/README.md) applies unchanged. Cross-round index:
[`docs/research/README.md`](../../docs/research/README.md). Under [R15](../../docs/RULES.md#r15)
nothing here closes or admits anything.

| lane | territory | kind |
|---|---|---|
| `J1` | **stock splits** — the one corporate event that CANNOT happen in a cheap stock | signal |
| `J2` | dividend policy — initiations, cuts, specials | signal |
| `J3` | **validate the fixture against survivorship-free public aggregates** | data |
| `J4` | **the floor's LEVEL, now that its justification is dead** | method |
| `J5` | point-in-time panel construction conventions | method |
| `J6` | **a structural-break calendar for 2010–2026** | data |

---

## THE SELECTION PRINCIPLE CHANGED, AND THIS IS THE IMPORTANT PART OF THE FILE

**Rounds 1–4 chose territories by what was UNTOUCHED. Round 5 chooses by WHAT KILLS THEM.**

Eleven signal territories have now been researched and every one died. **They did not die of eleven
different things. They died of five**, and four of the five were visible before the lane was
commissioned:

| | the killer | where it struck |
|---|---|---|
| **1** | **the effect lives in low-priced or small names**, where per-share commission in bp is worst | `F1` down-cap · `F2` small-cap · `F3` microcaps · `G1` below-mean-size · `G2` dying names are cheap names · `G4` **$22m** average target · `H3` **39.6%** sub-$1 deficiency |
| **2** | **breadth — the count, or `n_eff`, is too small** | `G1` **26 offsets** · `G3` low double digits · `H2` **0.4 events/bar** · `H3` 20–50 names in one sector |
| **3** | **post-2010 decay** | `F1` 7.4%→0.3% · `F2` no cost-honest survival · `F3` PEAD dead since 2006 · `F6` drift gone 2003–2012 · `H1` −9.5%→−1.3% |
| **4** | **it resolves in one print, or overnight** | `F6` three of four families · `G3` one halt-cross auction · `H3` **85% lands on the day** |
| **5** | **the published effect is ex-post or contaminated** | `G1` FIT is contemporaneous, and the standard measure *"is inadvertently a direct function of a stock's actual realized return"* · `H2` filed **because** the price fell · `H3` every run-up is a winners-minus-losers contrast formed ex post |

> **KILLER 1 IS THE MOST COMMON AND THE MOST PREDICTABLE, AND I COMMISSIONED SEVEN LANES INTO IT
> ANYWAY.** Cost in basis points scales inversely with price. That is not a discovery — it is in
> `CLAUDE.md`. **A territory whose events cluster in cheap names is dead before it is written, and
> four rounds of my slates did not screen for it.**

**So `J1` is selected on exactly one criterion: it is STRUCTURALLY IMMUNE TO KILLER 1.** A company
splits its stock **because the price is high.** It is the one corporate event in the catalogue that
*cannot* occur in a cheap stock. Whether it survives killers 2–5 is the lane's job to find out —
but for the first time in five rounds, the most reliable killer is off the table by construction
rather than by hope.

**`J2` is selected the same way, more weakly:** dividend initiations and increases happen at
profitable firms, which skew higher-priced. **Cuts do not**, and the lane is told to split them.

---

## The design has moved 4+2 → 3+3 → 2+4, and the yield is why

**Four rounds, twenty-five briefs, zero strategies, eleven things the programme was wrong about —
and eight of the eleven came from non-signal lanes.** Round 4 was the sharpest instance yet:
**all three signal lanes died, all three method lanes returned, and two broke something the
programme currently believes.**

**Round 5 is 2 signal + 4 method.** This is not a retreat from looking for strategies — `J1` is the
best-targeted signal lane any round has carried. It is an allocation of effort to where the
evidence says it pays.

**And three of round 5's four method lanes were created by round 4**, which is the other durable
pattern: **method lanes generate their own successors; signal lanes do not.** `J3` exists because
`H5` found the one survivorship-free public aggregate. `J4` exists because `H4` found the `$5`
threshold's justification is dead. `J6` exists because rounds 3 and 4 kept tripping over individual
structural breaks with no calendar to put them in.

---

## The non-overlap audit

**File-level hit counts, case-insensitive, over `docs/`.** Counted, not asserted.

| term | files | term | files | term | files |
|---|--:|---|--:|---|--:|
| dividend initiation | **0** | dividend increase | **0** | dividend policy | **0** |
| holdout design | **0** | tick size pilot | **0** | Reg SCI | **0** |
| point-in-time panel | **0** | French library | **0** | benchmark the fixture | **0** |
| stock split | 1 | split announcement | 1 | special dividend | 1 |
| Kenneth French | 1 | structural break | 5 | **walk-forward** | **52** |

**Four rows were opened and two of them changed the slate:**

1. **The three split/dividend hits are all DATA HANDLING, not signal** — a fabricated-days result, a
   reverse-split 8-K link in an old survey, and round 4's own CRSP quotation. **Splits and dividend
   policy as EVENTS are genuinely untouched.**
2. **`walk-forward` returns 52 files.** Walk-forward validation is in heavy use and is spent ground.
3. **`RULES.md` ALREADY REASONS HOLDOUT DISCIPLINE AT LENGTH** — *"read at STAGE 4 or not at all"*,
   *"the scarcest asset"*, the one-read rule, and the in-sample floor as a **triage device**.
   **A holdout-design lane was on my draft slate and is CUT**, because the programme has already
   done that thinking and a brief would re-tread it.
4. **`Kenneth French` returns exactly one file — round 4's own record.** `J3` is building on a
   finding four hours old, and says so.

---

## J1 — stock splits *(signal)*

**The quantity.** Forward stock splits: the **announcement** date and the **ex-date**, treated
separately.

**Why it is chosen, and it is the whole argument.** **A split cannot happen in a cheap stock.** It
is the only event on any slate so far that is structurally immune to the killer that has taken more
lanes here than any other. High nominal price also means **the lowest possible commission in basis
points** and the tightest relative spreads in the universe.

**Mechanism, and the lane should test both.** Route (a) at the ex-date — index and fund mechanics,
and the documented retail-demand response to a lower nominal price. Route (b) at the announcement —
a management signal about expected price levels. **The lane is told the programme's own finding that
route (b) converts a cost problem into a signal problem**, so it must not treat a large move as
sufficient.

**Data.** The programme already holds a split file — **splits are in the corporate-action feed** —
so the ex-date is free and in hand. **The ANNOUNCEMENT date is the retrieval question**, and 8-K
Item 8.01 or a press release is the likely route. **The lane must not assume the existing feed's
split dates are announcement dates; they are ex-dates.**

**The kill numbers, and there are two.** **First, the count**: US forward splits per year 2010–2026
on names passing a `$5` and dollar-volume floor. **Splitting went out of fashion after 2000 and the
lane may die on arithmetic** — that is killer 2 and it is the live risk here. **Second, decay**:
this is a much-published effect, so killer 3 applies with full force.

**The honest risk.** A split is mechanically neutral, so any effect is pure behaviour or pure flow —
and the announcement is the kind of news that lands outside trading hours. **Killer 4 is in play.**

---

## J2 — dividend policy *(signal)*

**The quantity.** Dividend **initiations**, **omissions and cuts**, and **special dividends**, by
declaration date.

**Why it is not in the catalogue.** Zero hits on all three phrasings. Round 2's `F6` covered
buybacks, lockups, SEOs and spin-offs — **it did not cover dividends**, and the programme's own
corporate-action work treats dividends purely as a return component.

**Why it partially escapes killer 1, and the lane must split on this.** **Initiations and increases
happen at profitable firms and skew higher-priced. CUTS AND OMISSIONS DO NOT** — they happen at
firms in trouble, which is the cheap tail. **The lane is instructed to report the two sides
separately and never to pool them**, because pooling would hide exactly the interaction that has
killed seven lanes.

**Data.** Declaration dates are in the corporate-action feed in principle; **whether the feed
distinguishes a first-ever dividend from a routine one, and whether it carries the DECLARATION date
as against the EX-date, is the retrieval question.** Free alternatives to assess.

**The kill number.** Counts per year of initiations, cuts and specials on floor-passing names — and
the **price-tercile split of each**.

**The honest risk.** This is among the oldest studied effects in finance, so killer 3 is severe;
and the programme's fixture is **total-return where the events file is passed**, so a dividend event
is partly already in the return series.

---

## J3 — validate the fixture against survivorship-free public aggregates *(data)*

**Created by round 4's `H5` four hours ago.** It found that **Kenneth French's daily factor library
is free, runs 1926 to 2026-07-31, and its own header declares it built from a survivorship-free
database** — but that it is **aggregate only**. For a *fixture-level sanity check*, aggregate-only is
not a limitation. **It is exactly the right shape.**

**The question.** Does this programme's dead-inclusive, `$5`-floored, equal-weighted universe behave
like a published survivorship-free equal-weighted US aggregate over the same window? **If it does
not, the difference is either a real property of the floor or a defect — and nobody has ever
looked.**

**What the lane researches** — the comparison itself is a measurement and is NOT this lane's job.
**The lane's job is to establish what a valid comparison would require**: what exactly French's
portfolios contain (universe, weighting, rebalancing, delisting treatment, what "equal-weighted"
means there), what other free survivorship-free aggregates exist, and **what differences would be
EXPECTED from the floor alone** — so that an unexpected difference is interpretable rather than
just observed.

**The bar.** **It must return a like-for-like specification** — a named series, its documented
construction, and the list of adjustments needed before the two are comparable. **"Compare against
French" is not a specification; it is a gesture.**

**The honest risk.** The floor, the equal weighting and the dead-inclusion may make every difference
explainable after the fact, which is the failure mode of every benchmark comparison.

---

## J4 — the floor's LEVEL, now that its justification is dead *(method)*

**Created by round 4's `H4`.** Read verbatim from Amihud's footnote 10: **the `$5` screen's
justification is the NYSE's 1992 minimum-tick reduction and $1/8-tick noise — a justification
DECIMALISATION KILLED IN 2001, and nobody restated it.** The programme inherited a threshold whose
stated reason stopped being true twenty-five years ago.

**`H4` answered the CONVENTION question (eject or carry). This lane asks the LEVEL question**, and
they are different: `H4` asked *what happens at the boundary*, `J4` asks *where the boundary should
be.*

**Why it matters here more than in the literature.** Most published users of a `$5` screen face
**per-value** commissions, where price is nearly irrelevant to cost in basis points. **This
programme faces PER-SHARE commissions, where cost in bp is `50/P` — price is the dominant term.**
So the floor is not a nuisance filter here; **it is a cost-model parameter wearing a
data-quality costume.**

**What the lane researches.** What is documented about the *sensitivity* of cross-sectional results
to the screen's level — $1, $5, $10? Is there published work varying it? What do practitioners under
per-share commission regimes actually use, and is it written down anywhere? And: **is there a
principled way to set it from the cost model rather than from convention?**

**The bar.** **A defensible basis for choosing a level, or an explicit finding that none exists in
the literature.** A number without a basis is what the programme already has.

**The honest risk.** Raising the floor cuts the universe, which is killer 2 arriving by the back
door — the lane must state the trade-off, not just the direction.

---

## J5 — point-in-time panel construction conventions *(method)*

**Round 3's `G3` found the decisive question and could not answer it**: whether the fixture
**preserves entirely missing sessions or forward-fills them** decides whether a multi-day halt is
even *visible* — and the same property governs every ragged edge in the panel.

**The quantity.** How published work builds a dead-inclusive daily panel: **entry** (a name's first
usable bar — is the IPO day included, the first N days excluded?), **exit** (the last bar and what
is booked after it), **gaps** (missing sessions inside a name's life — halts, non-trading,
vendor gaps), and **the ragged edge** (how a panel with different start and stop dates per name is
aligned without introducing look-ahead).

**Why it is not `H4`.** `H4` was the *screen*. This is the *panel underneath it*. A screen decides
who is eligible; **panel construction decides what a bar even means when a name is not trading.**

**The bar, same as `H4`'s and for the same reason.** **A stated convention with a citation, quoted
verbatim.** If the literature leaves it implicit — which `H4` found it does for screens — **that is
the headline**, and the lane should then report what reference implementations and data vendors do
instead.

**Do NOT re-survey** delisting returns (round 3), the `$5` screen's mid-hold rule (`H4`), or vendor
data defects (`G6`).

---

## J6 — a structural-break calendar for 2010–2026 *(data)*

**Rounds 3 and 4 kept tripping over individual breaks with nowhere to put them.** Already on the
record, found incidentally: the **10b5-1 checkbox from 2023-04-01**; the **13D deadline change,
10 calendar days → 5 business days, in 2024**; the **8-K item-code string change to `SCHEDULE 13D`
around 2024-12-18**; **T+1 settlement in May 2024**; the **EDGAR 22:00 extension on 2024-02-05**;
**Rule 605 amendments with compliance 2026-08-01**; **tick-size and access-fee amendments delayed to
November 2027**; **Item 5.02(e) folding pay grants into one code in 2006**. **Each was found by
accident, by a different agent, in a different lane.**

**The quantity: one calendar.** Every US market-structure, disclosure and regulatory change between
2010-01-04 and 2026-08-26 that could plausibly break the stationarity of a daily US equity panel or
of an EDGAR-derived series — **with its exact effective date and its exact mechanism.**

**Why this is worth a lane on its own.** **A structural break is not a nuisance; it is a
pre-registration input.** A study spanning such a date **must declare the split in advance or it is
fitting two regimes and reporting one.** The programme has the discipline for this and has never had
the calendar.

**Candidates to sweep**, and the lane should find more: LULD's introduction and permanence; the
tick-size pilot (2016–2018) and its termination; Reg SCI; the Rule 605 and 606 regimes; T+1;
decimalisation-era leftovers still in the sample; short-sale rule changes **as dates only — the
short-interest territory itself is excluded**; 8-K and Schedule form changes; exchange fee-pilot
litigation; the 2020 volatility halts.

**The bar.** **A dated table with a primary citation per row, and a one-line statement of what each
break changes.** **A break with no stated mechanism is trivia.** Rank by how many of this
programme's data sources each one touches.

**The honest risk.** This could balloon into a history of US market structure. **The lane is told to
prioritise ruthlessly by whether a break touches a series this programme actually holds** — daily
US equity bars, corporate actions, and EDGAR filings.

---

## THE EXCLUSION LIST FOR ROUND 5

**Everything rounds 1–4 were kept off, plus round 4's own six territories.**

**Carried:** credit spreads / yield curve / defensive–cyclical rotation as a regime gate · calendar
effects · short interest, days-to-cover, borrow fees, FINRA and FTD data · short-term reversal,
industry-relative and residual reversal, return clustering · closed-end fund discounts · lead–lag ·
signal combination, ML return prediction, factor-zoo multiple testing, deflated Sharpe and PBO ·
**options of any kind** · inferring order flow from price action · price-level / volume-profile maps
· at-the-market shelf issuance · XBRL cash runway · merger-arbitrage and deal prediction · CFTC COT
· momentum, wedge breakouts, MACD, stops and targets · index reconstitution · SEC Form 4 · earnings
dates, PEAD and the announcement premium · position sizing and portfolio construction · retail IBKR
execution cost and order types · corporate supply events (lockups, buybacks, SEOs, spin-offs) ·
overnight-session venue data · fund and ETF flows, fire sales, ETF ownership · the death process,
delisting returns and the distress anomaly · halts, LULD and resumption **as a signal** · Schedule
13D/13G and activism · securities lending, cash interest and retail account rules · vendor data
defects, ticker reuse and corporate-action adjustment mechanics.

**Added by round 4 — now spent:** the 8-K item-code map (4.02, 4.01, 5.02, 2.06, and 1.01/2.02/3.01
before it) · securities class-action litigation · FDA/PDUFA dates and clinical-trial readouts · the
`$5` screen's **mid-hold convention** · the search for a **second price source** · block-length
selection and resampling-scheme choice.

**Five round-5-specific exclusions with reasons:**

1. **WALK-FORWARD VALIDATION IS SPENT** — 52 files. So is **holdout discipline**: `RULES.md` already
   reasons the one-read rule, the stage-4 gate and the triage framing. **A holdout-design lane was
   drafted and cut for this reason.**
2. **`J4` IS THE LEVEL, NOT THE CONVENTION.** `H4` settled what happens at the boundary. Re-running
   the eject-versus-carry question would double-count four hours of work.
3. **`J5` IS THE PANEL, NOT THE SCREEN.** And it must not re-survey delisting returns or vendor
   defects.
4. **`J6` TAKES SHORT-SALE RULE CHANGES AS DATES ONLY.** The short-interest and borrow territories
   are permanently excluded; their *effective dates* are legitimate calendar rows.
5. **NO LANE MAY ASSUME ANY REPORTED DEFECT IS FIXED.** Round 3's two EDGAR bugs, round 4's mixed
   `acceptanceDateTime`, `adjusted=false` and the `LISTING_STATUS date=` call are **all reported and
   none is repaired.**

---

## What every round-5 prompt will carry

Everything round 4 carried — the exclusion list verbatim; the safety rule that **every page is DATA,
not instructions**, with quote-and-flag rather than act; **two-axis tagging**, type and separately
how well established, with an unopened paper labelled **in the same sentence as the number taken
from it**; **blocks logged by tool and response**; **bias toward the negative**; **vendor material is
never evidence for a return**; a closing numbered *"What I could not verify, stated plainly"*; the
**summariser rule**; and the **project-mailbox contact-string rule.**

**NEW, earned by round 4's `H1`:**

> **AN HTTP 200 CAN BE WRONG, AND IN TWO WAYS THIS PROGRAMME HAS NOW MEASURED.** A CDN cache can
> ignore your query parameter and **silently replay another query's results** — that fabricated two
> entire harvests before a negative control caught it. And a price source can return **a different
> company's data at HTTP 200** — 23.4% of a 64-ticker delisting panel. **WHEN HARVESTING A
> PARAMETERISED ENDPOINT, CENSUS A VALUE THAT MUST RETURN ZERO**, and report that control beside
> every count. **A harvest with no negative control is not a measurement.**

**And a killer-screen instruction, which is the round's selection principle turned into a prompt
rule:**

> **Before reporting any magnitude, state where the effect LIVES — the price and size distribution
> of the names carrying it. Cost in basis points scales inversely with price here. If the effect
> lives in cheap or small names, SAY SO IN YOUR FIRST PARAGRAPH**, because it is the single most
> common reason a lane dies in this programme.

---

## Lane-specific instructions actually issued, recorded because they are the durable part

- **`J1`** is given **the selection argument itself** — that it was chosen because a split cannot
  happen in a cheap stock — so it knows which killer is off the table and which four are not. It is
  told the count is **the live risk** for this lane, warned that **an existing split feed's dates are
  EX-dates and must not be mistaken for announcement dates**, and told that **route (b) converts a
  cost problem into a signal problem, so a large move is not sufficient.**
- **`J2`** carries the non-pooling instruction as **non-negotiable**, with the reason: initiations
  sit above the floor and **cuts do not**, and pooling would hide the exact interaction that has
  killed seven lanes. It is also told to address **the earnings confound** (dividend declarations
  often coincide with earnings, which is excluded ground) and that **the dividend cash is already in
  the return series**, so any tradeable effect must be a repricing at the announcement.
- **`J3`** is told **the comparison is a measurement and is not its job** — it cannot run it and
  must not pretend to. Its bar is a **like-for-like specification**: a named series, its documented
  construction quoted verbatim, and the enumerated adjustments needed before comparison. It is asked
  **which statistic would actually catch a broken fixture** rather than merely produce a number, and
  to settle whether **any published figure exists for the daily autocorrelation of an equal-weighted
  US portfolio** — an absence a previous round searched for and could not fill.
- **`J4`** is told the eject-or-carry question is **settled and spent**, and that its subject is the
  **level**. It carries the framing that makes the lane worth running: under per-share commissions
  the floor **is a cost-model parameter wearing a data-quality costume**. It is asked to derive
  explicitly **the price below which a trade cannot pay** given a commission and an expected edge,
  and told that is **the most valuable part of the lane if it exists** — and to state the
  breadth cost of raising the floor rather than only the direction.
- **`J5`** is told it is **the panel, not the screen**, and that the delisting-return literature is
  known background rather than territory. The summariser rule is flagged as **acute here**, with the
  round-4 instance quoted — a summariser said a code file *"does not contain explicit price
  screens"* when it does, which would have inverted that brief. It is told the programme forbids
  forward-filling, so **a source recommending it is interesting to REPORT, not to adopt.**
- **`J6`** is given **the eight breaks already found by accident** so its incremental content is
  visible, and told to **rank ruthlessly** — *a break with no stated mechanism is trivia*, and better
  twenty rows that each name a mechanism than eighty that do not. It must distinguish
  **adopted / effective / compliance** dates and flag rules **vacated, delayed or exempted**, because
  this programme has already commissioned research premised on a rule a court vacated before it
  produced data. **Law-firm alerts may find a rule but may never be the citation for its date.**
  Excluded *territories* may still contribute **dated rule changes**, and that is stated per entry.

## What this file does not claim

**No lane has been commissioned and no brief exists here.** The hit counts are the only computed
numbers and they count files in the written record — **not evidence about any market.** Every kill
number named is a number somebody would have to go and get; **not one has been got.** **Both books
are unchanged**, nothing is closed and nothing is admitted, which remains the principal's call under
[R15](../../docs/RULES.md#r15). **Nothing here is elevated out of the research folder.**
