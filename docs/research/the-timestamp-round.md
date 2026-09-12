# The timestamp round — round 4 external evidence

**Round 4 of the lead scan.** Six territories commissioned 2026-09-09; contract, territory selection
and the exclusion list every prompt carried:
[`working/leads4/README.md`](../../working/leads4/README.md). Cross-round index:
[`README.md`](README.md).

**STATUS: COMPLETE — all six briefs in** (`H1`–`H6` in [`working/leads4/`](../../working/leads4/)).

**Round 4 was the first `3 signal + 3 method` slate**, changed from `4+2` because three rounds of
yield argued for it. **The change was correct and the margin was not close.**

---

## THE HEADLINE

**All three signal lanes died. All three method lanes returned, and two of them broke something the
programme currently believes.**

- **The fix round 3 recommended for its own look-ahead bug is itself broken.** `acceptanceDateTime`
  is timezone-inconsistent — **35 of 60 hand-checked filings are ET mislabelled as `Z`.**
- **Round 3's stated mechanism for that bug is wrong for 8-K**, and `H1` corrected it. **The bug
  survives in a different and smaller form.**
- **The reference implementation of the empirical asset-pricing literature ejects a held name that
  falls through a `$5` screen — and says so nowhere in its prose.**
- **The inherited block length of 20 is fine where the programme uses it on returns and roughly 6×
  too short where it uses it on persistent conditioners** — the direction that makes nulls easier.
- **No free second price source exists.** Measured, not inferred, across nine sources.

**The reading rule is unchanged**, and round 4 added one: **a figure obtained through a summariser is
WEAKER than `[snippet only]`, not stronger.** By the end of the round that rule had caught **four**
independent fabrications (§1.4). Under [R15](../RULES.md#r15) **nothing here closes or admits
anything.**

---

## 1. The findings that are not about any territory

### 1.1 THE FIX ROUND 3 RECOMMENDED IS ITSELF BROKEN — `acceptanceDateTime` HAS A MIXED TIMEZONE

**From `H1`, and it resolves an open item round 2 left.**

Round 2's `F3` flagged that the `acceptanceDateTime` timezone did not reconcile — one Apple case
checked out as UTC, an SVB February filing did not — and recommended checking ~100 filings across
both DST regimes before splitting sessions on it. **`H1` did that check. The answer is that the
field is mixed.**

```
hand-check, 60 filings vs EDGAR index pages and SGML headers:
    35 are ET mislabelled as `Z`   |   25 are genuine UTC
    -- mixed WITHIN the same day and the same filer agent

independent arbiter, 577 filings, using filingDate + the 17:30 rule:
    34.0% can only be UTC   |   5.0% can only be ET
```

**The authoritative source is the SGML `<ACCEPTANCE-DATETIME>` header, which reproduced the observed
`filingDate` on 60 of 60.**

**The consequence, stated as a bracket because the bracket is the finding:** the share of Item 4.02
filings **accepted after the 16:00 close while still carrying that day as `filingDate`** is
**between 30.7% and 65.7% — and the bracket cannot be narrowed from the JSON.**

> **A field serialised with a `Z` that is only sometimes UTC is worse than a field with no timezone
> at all**, because it invites exactly the fix round 3 recommended. **Any look-ahead rule keyed on
> `acceptanceDateTime` from the submissions JSON is unsound. Key on the SGML header.**

### 1.2 A CORRECTION TO ROUND 3, AND THE BUG SURVIVES IN A SMALLER FORM

**Round 3's [`the-plumbing-round.md`](the-plumbing-round.md) §1.1 states that the SEC moved the
EDGAR cut-off from 17:30 to 22:00 ET on 2024-02-05.** `H1` checked the primary source: **that
extension is for Schedule 13D/13G ONLY.** SEC's current filer guidance lists the same-day-after-17:30
exception forms verbatim — **Forms 3/4/5, 144, and the MEF registration forms. Form 8-K is not among
them.**

**Round 3's claim is therefore right for the form it was researching (13D/G) and wrong as the general
rule I carried into round 4's prompt.** That generalisation was mine.

**But the bug does not go away — it changes shape.** Even under the ordinary 17:30 rule, **a filing
accepted after the 16:00 market close still carries that day as `filingDate`**, so a runner entering
on `filingDate`'s close is using information that did not exist. **That is the 30.7–65.7% bracket in
§1.1.** `H1` notes the round-3 error is **in the conservative direction**, so it is not the dangerous
one — **the dangerous one is §1.1.**

**Round 3's §1.1 has been amended in place to carry this correction.**

### 1.3 A CDN CACHE THAT SILENTLY REPLAYS ANOTHER QUERY'S RESULTS

**From `H1`, and it is a new tooling hazard with a new defence.**

While censusing 8-K item codes, `H1` found **a CDN cache that ignores the `items` parameter and
silently replays a different code's results.** Its **first two harvests were entirely fabricated
numbers** — returned at HTTP 200, well-formed, plausible.

**It was caught by a negative control**: a census of `items=9.99`, a code that does not exist, which
**returned 0 in every year**. Every published count in that lane carries that control.

> **The defence generalises and costs nothing: when harvesting a parameterised endpoint, census a
> value that MUST return zero.** This programme already has a rule that a self-test which cannot
> fail is worse than none; **this is the same rule pointed at a data pull rather than at a runner.**

### 1.4 THE SUMMARISER HAZARD IS NOW A FOUR-TIME PATTERN

The rule added to every round-4 prompt — **a figure obtained through a summariser is weaker than a
snippet, not stronger** — **caught three fabrications inside the round it was added.**

| round | what the summariser produced | what was true |
|---|---|---|
| 3 · `G3` | **a fabricated table** of reversal percentages | the table does not appear in the document |
| 4 · `H4` | *"does not contain explicit price screens"* | **it does** — the paraphrase would have inverted the brief's main finding |
| 4 · `H2` | **"12.3%" and "14.6–20.6% CAAR"** attributed to a named PDF | the PDF is **an undergraduate honors thesis containing none of those numbers** |
| 4 · `H6` | — | **refused 5 of 6 PDFs outright**, which is the honest failure mode |

**Three of the four are silent failures that look like readings.** `H3` and `H6` both bypassed the
summariser entirely — `H3` parsed HTML and JATS XML locally, `H6` extracted every formula with
`pypdf` — **and those two produced the round's most reliable numbers.**

**The corollary, already noted in round 3 and now load-bearing:** WebFetch's **"corrupted PDF"
response is not a block.** The bytes land on disk and `pypdf` reads them.

### 1.5 NO FREE SECOND PRICE SOURCE EXISTS — MEASURED, NOT INFERRED

**From `H5`, whose kill condition was met.** Nine sources probed live. **On a 64-ticker panel of
known delistings spanning 2012–2025**, the best candidate returned:

```
 9.4% MATCH          -- and EVERY ONE died in 2022 or later.
                        Zero of the 2012-2021 delistings returned the right entity.
                        The retention window is ~4 years, not 16.
23.4% WRONG ENTITY   -- at HTTP 200, silently. SNDK quotes $1,764.17 for a company
                        bought at $86.50 in 2016. SHLD returns a defence-tech ETF.
67.2% HTTP 400
```

**That 23.4% is 3.5× worse than round 3's measured 6.6% ticker-reuse rate**, because the source
substitutes on **renames** as well as reuse.

**And even a working source would not have done the job: the candidates serve SPLIT-ADJUSTED OHLC,
which cannot validate a `$5` AS-TRADED floor.**

**Two things survive.**

**SEC MIDAS** — 58 quarterly files, 2012 Q2–2026 Q2, no key, no wall. **No prices** (a decile rank
only, header read verbatim from the bytes). But it carries per-ticker daily volume and is
**dead-inclusive by construction and keyed point-in-time on `(Date, Ticker)` — files are written
once and never rewritten, so ticker reuse cannot contaminate them.** Verified: SIVB, SBNY and FRC
are all present in the February 2023 file, weeks before they failed. **This is the point-in-time
roster nothing else has provided.** Two traps: **a frozen decoy URL family** that 404s after 2024 Q1,
so probing it alone yields the false conclusion that MIDAS stopped; and **a schema that is not
stable across the archive.**

**Kenneth French's daily factors** — 1926 to 2026-07-31, header reading *"created by using the 202607
CRSP database"*. **Aggregate only.** *(The "i.e. survivorship-free" gloss originally written here was
an INFERENCE from that header, not a quotation from it — round 5's `J3` censused `surviv` across four
daily files and the landing page and found **zero hits in all five**. The property is inherited from
CRSP and is nowhere asserted by French. Corrected 2026-09-10.)*

**Two one-call items that are worth more than the lane's verdict.** The vendor's own documentation
describes **`LISTING_STATUS` with a `date=` parameter that "travels back in time"** — **a
point-in-time listing map inside the key the programme already holds**, against a survivors-only
trap now confirmed three times (rounds 2, 3, 4). Same vendor, so not independent — **but
cross-checkable against MIDAS, which is.** `H5` could not execute it (demo key gated; it registered
for nothing). And, confirmed verbatim: **intraday is `adjusted=true` by default, and
`adjusted=false` puts both fixtures on one basis** — the cheapest available fix for a mismatch this
programme has already been bitten by.

**The fallback, delivered as instructed.** The strongest single-source assertion:
**`adjusted_close / close` must be a step function changing only on recorded corporate-action
dates.** `H5` states its own ceiling up front — **internal checks catch inconsistency, never
systematic bias.**

### 1.6 THE REFERENCE IMPLEMENTATION OF THE LITERATURE EJECTS, AND SAYS SO NOWHERE

**From `H4`, and the answer splits in two, which is the finding.**

**The academic literature does not state a mid-hold rule. It states a DATE.** Read verbatim:
Jegadeesh & Titman, *"We also exclude all stocks priced below $5 at the beginning of the holding
period"* — on a six-month hold. Amihud, *"The stock price is greater than $5 at the end of year
y−1"* — on a twelve-month sample year. **Neither says what happens when a held name falls through.**
Chen & Zimmermann say it outright: *"Most papers do not provide precise explanations of these
details."* Quantified from their transcription of **212 published predictors: 144 record no filter
at all, and 20 combine a price screen with a multi-month hold** — the cell where the question bites.

**The public reference implementation of that literature EJECTS.** `filterstr = "abs(prc) > 5"` is
applied to **every stock-month**, *before* the holding-period carry-forward. A stock-month failing
the screen has no row, so no portfolio assignment, so no return — **ejected, with automatic re-entry
on recovery, on twelve-month-hold portfolios whose source papers date the screen to formation.**
**Described nowhere in the prose.** `[Code reading, not an executed test — `H4` flags this itself.]`

**Every methodology document that DOES state a convention says CARRY.** S&P: *"Current constituents
have no minimum requirement."* FTSE Russell §5.8.1 keeps an existing member below $1.00 on a 30-day
average, *"In order to reduce unnecessary turnover."* MSCI allows an existing constituent down to
2/3 of the liquidity minimum. **None ejects for a screen violation** — removal is for corporate
events only.

**A CORRECTION TO THE FRAMING I GAVE THE LANE, and it is sharper than mine.** A floor on a `t−1`
as-traded close **is not look-ahead** — the ejection is implementable. **The defect is that the
reported statistics belong to a strategy that is not the one described.**

**And it lands on this programme's reporting standard directly:** the floor **suppresses the
mean-below-median tell and pre-empts part of the bottom trim**, so **a trimmed-mean report on an
ejecting book double-counts the left-tail removal.** Direction: **long-only overstated, short-only
understated** — the floor amputates exactly the short's best trades.

**Where the `$5` came from**, read verbatim from Amihud's footnote 10: **the NYSE's 1992 minimum-tick
reduction, justified by $1/8-tick noise — a justification decimalisation killed in 2001, and nobody
restated it.**

### 1.7 THE BLOCK LENGTH IS FINE WHERE WE USE IT ON RETURNS AND TOO SHORT WHERE WE USE IT ON STATE

**From `H6`**, which derived the optimal block length in closed form, **verified it reproduces the
source paper's own published table in 5 of 6 cells**, and transcribed the reference implementation
line-for-line.

**`b = 20` is optimal for AR(1) ρ = 0.4499. And `b = 21` ⟺ ρ = 0.4718 — D106 and D229 differ by
0.022 in implied autocorrelation. They are the same number.**

**On return-side statistics the inherited 20 is 5–15× too long, and it does not matter.** The
selector returns median **1.3** for white noise and **1.5** for GARCH returns; because the bias term
is `−G/b`, over-long blocks only inflate variance — **SE noisy to 4.0% at b=20 against 1.8% at
b=4.** `H6`'s own recommendation: **a sensitivity study would return "no material difference" and it
advises against running one.** That is the "confirm the inherited choice and end there" outcome the
lane was given permission to reach, and it took it.

**On persistent-summand statistics the same 20 is ~6× too SHORT, which is the dangerous direction.**
The identical GARCH path wanting `b̂ = 1.5` for its mean wants **`b̂ = 132` for its squared mean**;
a correlation of two ρ = 0.98 conditioners wants **~157**. **Too-short blocks understate the
long-run variance — narrower intervals, easier nulls.** The selector's input is the statistic's
**influence series**, not returns.

> **OPEN, AND FLAGGED RATHER THAN ASSERTED.** This session's own regime-conditioner calibration used
> **159 blocks over ~4,187 bars ≈ 26 bars per block**, on correlations of slow-moving conditioners —
> the case `H6` says wants ~157. **If those conditioners are as persistent as they appeared, that
> probe's decisive line of |r| ≈ 0.15–0.16 is too lenient.** This has NOT been checked and is not
> claimed.

**Three more:**

**The 26-offset finding is a theorem, not an observation.** With `#G = 26`, α = 0.05 rejects only on
a strict maximum — **size exactly 1/26 = 0.0385** — and **α = 0.01 has power identically zero.**

**PER-NAME ROTATIONS DO NOT CARRY THE BIAS `CLAUDE.md` ASSERTS.** Random draws from a group, **with
the identity included** and `p = (1+b)/(1+w)`, are **exact for any `w`**. `CLAUDE.md` currently says
per-name rotations are not enumerable so *"the bias stands and only (i) or more draws touch it."*
**The fix is one character of code.** `[NOT APPLIED — amending standing guidance is the principal's
call.]`

**The selector silently breaks at ρ ≥ 0.95.** Both the Python and R implementations cap the
lag-window bandwidth at ≈70 — **a cap that is not in the source paper** — truncating the key
quantity to **29% of its true value at ρ = 0.98.** And the theorem assumes `b = o(√N)`; √4,190 =
64.7. **At ρ = 0.98 there are 42 effective observations in 4,190 bars. No block length fixes that.**

**The p95 premise holds, for the smaller reason.** At B = 200: bias **−0.026 sd** toward the centre,
sd **0.146 sd** — **variance beats bias 5.6×.** The 2-SE rule is right and ~18% more conservative
than advertised; **B ≈ 1,790 for SE = 0.05 sd.** And **~10 effective instruments across 1,573 names
is exactly ρ̄ = 0.0994** under the design-effect formula — internally consistent.

**A citation hazard:** a 1999 paper's stationary-bootstrap variance is **wrong** (sign error), and a
2004 paper's bound plus **all four of its simulation tables** are superseded.

> **THE ONE INPUT THAT DECIDES WHETHER ANY OF §1.7 BITES, AND `H6` COULD NOT GET IT.** Its own
> chief unverified item: **there is no citable modern figure for the daily autocorrelation of an
> equal-weighted US book.** Everything above is a ρ-table; **without that ρ, this programme cannot
> be placed on it.** `H6`'s two halves point in opposite directions — 20 is harmlessly too long on
> returns and dangerously too short on persistent state — so **which half applies is not a matter
> of judgement, it is a matter of one number nobody has.** It is measurable here in minutes and is
> **not measured**, because this record is research only.

### 1.8 ROUTE (b) GOT ITS FIRST CLEAN TEST, AND THE RESULT IS NOT A VERDICT ON ROUTE (b)

**From `H3`.** Route (b) — *the move is large and slow relative to the spread, so the toll is a
rounding error* — was introduced in round 3 and both its lanes failed for lane-specific reasons.
`H3` is the first lane where it was tested on its own terms.

**The ratio inverts exactly as designed.** Early-biotech day 0–1 is **+631 bp**, rejections
**−1040 bp**, negative readouts **−1300 bp**, against a plausible **135–270 bp** round trip. **The
toll is 12–45% of the move, not 98.5%.**

**And the lane still dies — because that is a MAGNITUDE, not an EXPECTATION.** `H3`'s own framing,
which is the right one: **this is a signal failure, not a cost failure. Opposite fix, and cheaper
execution is not it.**

> **Route (b) does what it claims. It converts a cost problem into a signal problem — and a signal
> problem is still a problem.** That is worth knowing before the next route (b) lane is
> commissioned.

---

## 2. `H1` — the 8-K item-code map · **4.02 IS NOT ROUTE (b), AND ONLY TWO CODES SURVIVE THE COUNT**

**The census, `H1`'s own, 2010–2025, every count carrying the `items=9.99` negative control:**

| item code | filings/yr | verdict |
|---|---|---|
| **4.02** non-reliance | **103–866** | survives the count |
| **4.01** auditor change | **627–1,736** | survives the count |
| 2.06 material impairment | **54–180** | **too rare** |
| 5.02 officer/director change | **11,446–15,332** | **too common to be an event** |

**Item 4.02 is not route (b) — the move is fast and small.** −1.04% / −1.61% (3-day event and
filing), with post-filing drift of **+0.13% / +0.52% / +0.94%, all insignificant AND THE WRONG
SIGN.** The decay is visible directly: mean announcement CAR **−9.5% (1997–2000) → −1.3%
(2001–2006)**, with 2005–2006 medians of **−0.4% to −0.6% — below one side of this programme's
33.8 bp spread.**

**Sign determinability, which is the question the slate did not contain and should have.**
Structural for **2.06**, and mostly for 4.02. **4.01 and 5.02 need NLP**, because the `items` field
exposes a bare `"5.02"` **with no sub-paragraph** — and **Item 5.02(e) folded pay grants into the
same code in 2006.**

**One incidental lead, recorded and not recommended.** **Item 3.03** (material modifications to
security-holder rights), ~1,000/yr, mechanical, **carries the largest positive announcement return
in the whole item map at +2.84% — on one unreplicated cell in one working paper.**

## 3. `H2` — securities litigation · **DEAD, AND THE HALF I CALLED "MORE INTERESTING" IS THE DEADER**

**The filing leg is exactly zero once stripped of the news that triggered it.** A 2024 dissertation
(N = 1,473, 2009–2019) `[read in full, extracted locally with pypdf]`: where the law-firm
investigation news is **older than 10 days** — the only clean filing-date events — the filing day
pays **+0.071%/day (t = 0.75)** and the following week **+0.02%/day (t = 0.38)**. The tradeable
full-sample post-filing window is **−0.84% gross, short-only**, which does not clear a 67.6 bp round
trip.

**The resolution leg has a published measured null on a large sample** `[read in full from the open
PDF]`: final court order, **N = 2,021 — every single cell insignificant**, dismissals included
(CAR[−1,1] = +0.2%). The authors' words: *"this decision has no further informational value."* The
one non-null is **null at [−1,1] and [−5,5]**, a wide-window artefact the authors themselves
attribute to date imprecision.

**And it explains WHY nothing is left: the market already sorts the outcome at filing** — eventual
settlements **−5.6%** against dismissals **−1.8%**. The resolution is priced two to four years
early.

**The premise number kills it independently:** ~140–160 filings/yr against US exchange-listed
operating companies; ~170–200 resolution events/yr, ~130–160 after restriction. **At ~100 usable
events/yr that is 0.4 events per bar** — too thin to fill an equal-weighted daily book even if the
effect existed.

**The data findings stand regardless.** The Stanford Clearinghouse is **currently down and frozen at
2025-07-28** — 13.5 months stale, **with ten version-control conflict markers rendering as page
text**; its terms **prohibit scraping**, there is no bulk download, and full case pages are
login-gated (`H2` did not register). **But it does retain dead defendants with point-in-time ticker
and exchange**, verified on a 1996 dismissed case and a later-bankrupt 2004 settled case. Resolution
dates are free on public case pages but **prefixed *"On or around"***, corroborating the
date-imprecision diagnosis exactly. **SEC AAERs carry no CIK or ticker.**

**A domain trap worth keeping, because it wastes a researcher's whole budget.** In securities
litigation *"event study"* is a **term of art for the expert-witness damages exercise** — the
`Halliburton II` price-impact calculation — **not for the empirical method of that name.** Searching
the obvious phrase returns **law-firm marketing**, not research. `H2` names this explicitly so the
next agent does not lose the same hours.

## 4. `H3` — FDA and trial calendars · **CLOSED ON RETURNS AND SEPARATELY BLOCKED ON DATA**

**The returns evidence is from the best-powered sample available** — 13,807 trial outcomes,
2000–2020 `[read in full; HTML and JATS XML parsed locally, tables transcribed, no summariser]`:
**abnormal returns on day −1 are insignificant and day +2 insignificant across every trial
property.** That kills pre-drift and post-drift at daily resolution together.

**Two independent teams, two eras, the same split: run-up at readouts, nothing at the regulatory
event.** And the framing that matters most — **every published run-up is a winners-minus-losers
contrast formed EX POST. It is not a signal.** The leak is sized: rejection CAR[−2,−1] = **−1.9%**
against CAR[0,1] = **−10.4%** — **~15% leaks, 85% lands on the day, and only the bad news leaks.**

**The data answer to the question the lane was set.** **21 CFR 314.430(b), read in full: the FDA is
legally barred from disclosing that an application exists.** **PDUFA goal dates are never published
by the FDA** — they reach the public only when the sponsor chooses. The goal is **90%, not 100%**,
and **a major amendment moves the date three months.**

**Survivorship, measured in this population:** of **134 issuers filing a PDUFA 8-K in 2014–16, only
47 (35%) map to a current SEC ticker — 65% are gone**, roughly double the fixture's dead share, and
two names **dropped from the free map instantly** on filing Form 15-12G.

**ClinicalTrials.gov's version-history endpoint is free and genuinely point-in-time** — but of 6,000
completed industry Phase 3 records, **only 43.9% carry a day-resolution primary completion date and
48.3% are month-only**, with no publish date and no ticker or CIK. **The one clean free
point-in-time stream is advisory-committee meetings** via the Federal Register (≥15 days' notice
with agenda) — **and it is collapsing: 105/yr (2010) → 40 (2024) → 15 (2025).**

**Breadth and price finish it.** 60–110 US filers/yr touch PDUFA at all; **~20–50 survive a `$5`
floor and volume screen** — *"a fraction of one additional effective instrument, not an eleventh."*
And **39.6% of the cohort has filed an 8-K containing "minimum bid price"** — sub-$1 listing
deficiency.

**One live thread, flagged as untested rather than as evidence:** one paper's prose describes CARs
continuing to fall for two weeks after negative outcomes — **plotted, but never given a coefficient
or a significance test.**

## 5–7. `H4`, `H5`, `H6`

Their findings are in §1.5, §1.6 and §1.7, because none is about a territory.

---

## 8. Sources

Full per-source detail with exact URLs and per-source tags is in the six briefs under
[`working/leads4/`](../../working/leads4/). Consolidated by strength.

**`[read in full]`, and note how many were obtained by local extraction rather than by fetching
cleanly.** Singh, Rocafort, Cai, Siah & Lo (PLOS ONE 2022) — HTML and JATS XML parsed locally ·
Cho & Lo · Saha (2024 ODU dissertation, 110pp, `pypdf`) · Barko, Renneboog & Zhang (ECGI WP
925/2023) · Jegadeesh & Titman (2001) · Amihud (2002), **including footnote 10 on the origin of the
`$5` screen** · Chen & Zimmermann's Open Source Asset Pricing documentation **and portfolio code** ·
Politis & White and the Patton–Politis–White correction · Hemerik & Goeman · Phipson & Smyth ·
Nordman · the JAMA advisory-committee study · **21 CFR 314.430(b)** and the PDUFA VII goals letter
(71pp, `pypdf`).

**`[PRIMARY DATA DOC]`, fetched live.** SEC EDGAR Release 24.0.2 and the current filer guidance on
same-day acceptance forms · EDGAR full-index, the submissions JSON and the SGML
`<ACCEPTANCE-DATETIME>` header · **SEC MIDAS, 58 quarterly files 2012 Q2–2026 Q2** · S&P, FTSE
Russell §5.8.1 and MSCI §3.1.2.4 index methodology documents · the FDA advisory-committee calendar
and Federal Register notices · ClinicalTrials.gov's version-history endpoint · Kenneth French's
data library header · Alpha Vantage documentation on `LISTING_STATUS` `date=` and intraday
`adjusted`.

**`[SOFTWARE DOC]`.** The `arch` package's optimal-block-length implementation and R's `np::b.star`
— **which disagree with each other and with the paper on tuning constants, and `arch` says so in its
own docstring.**

**`[abstract only]` / `[snippet only]`, each flagged where used.** Rothenstein (JNCI 2011) ·
Overgaard (2000) · Sarkar & de Jong · Kliger · the Treasury restatement-decay figures.

**`[UNVERIFIED]` and actively withdrawn.** A named PDF to which a summariser attributed "12.3%" and
"14.6–20.6% CAAR" — **it is an undergraduate honors thesis containing none of those numbers** · the
Item 3.03 **+2.84%**, one unreplicated cell in one working paper · `H1`'s **first two 8-K harvests,
which were entirely fabricated by a CDN cache** and are withdrawn in the brief.

---

## 9. Blocks — tool and response, not host

`WebFetch → papers.ssrn.com`: **HTTP 403 via Cloudflare, reproduced with curl** · `WebFetch →
cambridge.org`: HTML returned instead of PDF · `WebFetch →` publisher PDFs: **the summariser refused
5 of 6 in `H6`** · `stooq`: **three separate gates — an HTTP 200 carrying a JavaScript
proof-of-work challenge (NOT solved), then `"Access denied"` on the CSV for every symbol including
AAPL, then a consent wall (declined)** · Alpha Vantage demo key: gated, **no registration performed**
· SCAC full case pages: login-gated, **no registration performed**.

**Three entries that are NOT blocks and must not be recorded as such:** WebFetch's **"corrupted PDF"**
response (bytes land on disk, `pypdf` reads them) · **HTTP 403s that are User-Agent exclusions** ·
and the most dangerous, **HTTP 200 responses that are wrong**: a CDN cache replaying another query
(§1.3), and a price source returning **a different company's prices** (§1.5).

---

## 10. What this record does not claim

- **Nothing here was measured on this programme's fixture.** Figures restated from our own record —
  33.8 bp/side, the 67.6 bp round trip, the `$5` floor, ~4,190 bars, ~10 effective instruments,
  D106's 20 and D229's 21 — are quoted, not recomputed.
- **`[MEASURED IN BRIEF]` means an agent measured a PUBLIC file or endpoint**, named in the brief.
- **Nothing was backtested, no null was drawn, no cell was scored, no candidate exists.**
- **Nothing is repaired.** The `acceptanceDateTime` finding, the two round-3 EDGAR bugs, the
  `CLAUDE.md` per-name-rotation claim, `adjusted=false`, and the `LISTING_STATUS date=` call are all
  **reported and not acted on.** Every one is the principal's call.
- **No territory is closed.** `H3` argues for closure on returns and says explicitly that closure is
  the principal's under [R15](../RULES.md#r15).
- **Two of my own premises were wrong** and are recorded as mine: the 22:00 cut-off generalised from
  13D/G to 8-K (§1.2), and calling `H2`'s resolution leg "the more interesting half" when it is the
  deader one (§3).
- **Both books are unchanged. Nothing is elevated out of the research folder.**
