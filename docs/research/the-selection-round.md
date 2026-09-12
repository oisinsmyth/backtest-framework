# The selection round — round 5 external evidence

**Round 5 of the lead scan.** Six territories prepared 2026-09-09 and commissioned 2026-09-10;
contract, selection principle and the exclusion list every prompt carried:
[`working/leads5/README.md`](../../working/leads5/README.md). Cross-round index:
[`README.md`](README.md).

**STATUS: COMPLETE — all six briefs in** (`J1`–`J6` in [`working/leads5/`](../../working/leads5/)).

**Round 5 was the first slate selected by WHAT KILLS A LANE rather than by what was untouched**, and
the first at `2 signal + 4 method`.

---

## THE HEADLINE

**The selection principle worked, was measured to be wrong on one axis, and both signal lanes died
anyway.**

- **`J1` confirmed the principle.** A stock split cannot happen in a cheap stock: `50/P` is
  **0.04–0.9 bp** on the 2024 cohort against a measured **33.8 bp/side**. **Killer 1 was genuinely
  absent. The lane died on the other four.**
- **`J2` MEASURED the principle and found it conflates two axes.** Median initiator **$28.19**,
  median cutter **$28.45** — *the same price*. **Cutters are small FIRMS whose STOCKS are not cheap,
  because you must have been a dividend payer to cut one.**
- **And both signal lanes died on the same confound, which nobody anticipated:** **the earnings
  release is absorbing dated corporate events.**

**Four method lanes returned, and one produced the first directly checkable arithmetic prediction
about the fixture that any round has made.**

**Reading rules unchanged, plus round 5's own:** every claim about the outside world is attributed
and tagged for **how well it was established**; **a figure from a summariser is weaker than
`[snippet only]`**; **an HTTP 200 can be wrong**, so a parameterised harvest carries a
**negative control**. `[MEASURED IN BRIEF]` means an agent measured a *public* file or endpoint.
Under [R15](../RULES.md#r15) **nothing here closes or admits anything.**

---

## 1. The findings that are not about any territory

### 1.1 MY SELECTION PRINCIPLE CONFLATES SIZE WITH PRICE, AND `J2` MEASURED IT

**Round 5's whole design rests on killer 1 — the effect lives in cheap names, where per-share
commission in bp is worst.** `J2` harvested **4,521 dividend-policy 8-Ks from EDGAR (2010–2025)** and
priced every event **as traded** `[MEASURED IN BRIEF]`:

| | median price | below $5 | cheapest tercile |
|---|--:|--:|--:|
| **initiators** | **$28.19** | 7.3% | 7.6% |
| **cutters** | **$28.45** | 10.3% | 12.2% |
| *the market* | — | *32.2%* | — |

**Per-share commission is 1.8 bp at the median for BOTH legs. Killer 1 does not apply to this
territory at all** — and my non-pooling instruction was built on the assumption that it would.

> **THE CORRECTION IS WORTH MORE THAN THE LANE. Cutters ARE small firms — but their STOCKS ARE NOT
> CHEAP, because you must have been a dividend payer to cut one. SIZE AND PER-SHARE PRICE ARE
> DIFFERENT AXES, and a screen that asks only "does it live in small firms?" would have closed this
> territory on a cost argument that does not apply to it.**

**That is a defect in the selection principle I wrote the day before, and it is mine.** Any future
killer-1 screen must ask about **price**, not about **size**, and must accept that the two come
apart wherever an event requires a prior corporate state.

### 1.2 THE EARNINGS RELEASE IS ABSORBING DATED CORPORATE EVENTS — ROUND 5's META-FINDING

**Both signal lanes died on this, independently, and neither was commissioned to look for it.**
Both measured it themselves `[MEASURED IN BRIEF]`:

```
J2, dividend policy : 62.2% of initiations and 59.2% of cuts are filed under 8-K Item 2.02 --
                      the quarterly earnings release -- in the SAME DOCUMENT on the SAME TIMESTAMP.
                      Rising from ~40% in 2010 to 72% / 80% by 2024.
J1, stock splits     : 36-68% of modern split announcements arrive inside an earnings 8-K.
                      NVIDIA's 10-for-1 was the THIRD BULLET of a record-revenue release.
```

**At daily resolution these are one event.** Earnings dates and PEAD are excluded ground, so
**roughly 60% of one territory and up to two-thirds of the other simply IS that territory** — and
the clean subsample of splits falls to **single digits per year.**

> **A "dated corporate event" territory is a shrinking asset.** Issuers increasingly bundle
> announcements into the earnings release, so the share of any such event that is *separately dated*
> declines over time — **and it declines fastest in the recent sample, which is the part a deployed
> book would trade.** This should be screened for **before** a lane is commissioned, not discovered
> by it.

### 1.3 A DIRECTLY CHECKABLE ARITHMETIC PREDICTION ABOUT THE FIXTURE

**From `J6`, and it is the first of its kind any round has produced.** Built from an external
trading calendar, read from primary exchange and SEC documents:

```
4,343 weekdays in 2010-01-04 .. 2026-08-26
 -152 scheduled holidays
= 4,187 sessions        ... if the four UNSCHEDULED closure dates are absent as rows
= 4,191 sessions        ... if they are present
```

**The four dates are 2012-10-29, 2012-10-30, 2018-12-05 and 2025-01-09. No trade occurred anywhere
in US equities on any of them.**

**This programme's own measured figure is 4,187** (recorded earlier from a fixture probe), **which
matches the no-closure-rows case exactly.** `J6` inferred "~4,190 sits on 4,191" from a rounded
figure in its prompt — **the rounding was mine; the measured number is 4,187.** So the prediction
appears already satisfied, **pending a direct check that those four dates are absent rather than
present-and-empty.** That check is two lines and has not been run.

### 1.4 ODD LOTS ENTERED CONSOLIDATED VOLUME ON 2013-12-09 — AND THE ASYMMETRY IS THE FINDING

**From `J6`, with the approval order's own statement of the mechanism.** Odd-lot trades began
appearing in **daily consolidated volume** while remaining **excluded from high, low and last sale.**

> **`V` breaks on that date. `OHLC` does not.**

**So the break hits the trailing dollar-volume screen — which is half of `keep_v2` — and it hits it
PRICE-DEPENDENTLY**, because what counts as an odd lot is a share-count threshold. **And it leaves
Corwin–Schultz untouched**, because that estimator reads the range. **A break that moves one clause
of the universe floor and not the other, and moves it differently across the price cross-section, is
exactly the kind of row this lane was commissioned to find.**

### 1.5 THE EX-DATE CONVENTION HAS THREE REGIMES, A ONE-DAY HOLE, AND A DOUBLED DAY

**From `J6`.** Not one break but three, and **the authority is not where one would look**: the SEC's
settlement-cycle releases do not set ex-dates at all — **FINRA Rule 11140 does.**

```
ex-date = record date - 2 business days   ... to 2017-09-04
        = record date - 1 business day    ... from 2017-09-05
        = record date - 0                 ... from 2024-05-28
```

And the transitions are not clean: the rule filing states **"no securities will be ex-dividend on
September 5, 2017"** — a **one-day hole** — and **2025-01-10 carries a DOUBLED ex-date day.**

**`J6` also flags, for `J1`'s territory:** Rule 11140(b)(2) sends any distribution **≥25% —
including ordinary stock splits — ex AFTER the pay date**, which inverts the usual ordering.

### 1.6 THE OBVIOUS FIX TO ROUND 3's EDGAR BUG IS ALSO WRONG

Round 3's `G4` found that a filter on `form == "SC 13D"` silently returns nothing after the string
changed to `SCHEDULE 13D`. **`J6` establishes that it is not a cutover.** Both strings **coexist
through 2024 Q1–Q3**, and legacy rows **persist into 2025 Q1**.

> **So matching the new string is ALSO wrong, and matching either string is the only correct
> filter.** A second, undocumented break compounds it: **the daily `form.idx` truncated the value to
> `SCHEDULE 1` for about a year, so the daily and quarterly indices disagree with each other.**

**The bug remains reported and unrepaired** — but the repair is now known to be harder than it
looked.

### 1.7 CORWIN–SCHULTZ FORWARD-FILLS, BY THE AUTHOR'S OWN HAND

**From `J5`, and it is the second strike against this estimator in two rounds.** `CLAUDE.md`
instructs estimating held-name spreads with Corwin–Schultz off the OHLC. **Corwin's own published
sample program flags no-trade on `PRC<0 OR VOLUME=0`, voids the high and low, then substitutes the
retained PRIOR-DAY range re-anchored to today's close.** A major reference package reproduces it.

**It is range-preserving rather than a naive fill, and the flags are emitted, so it is auditable** —
**but it is still a fabricated high and low, and the trigger set is exactly the halt / no-trade /
thin set.** Round 4 found the same estimator **understates** spreads for small illiquid names
([`the-timestamp-round.md`](the-timestamp-round.md) §1.6). **Neither finding is repaired and both are
the principal's call.**

**`J5` reported its own method failure here, which is why the finding is credible:** its
`ffill`-shaped grep **missed the block entirely, because SAS's forward-fill does not look like
pandas'.**

### 1.8 FILL THE LABEL, NEVER THE PRICE — and the zero-fill is the real fabrication

**From `J5`, a transferable rule it was not asked for.** Reading two major reference packages line by
line: both forward-fill **heavily** — industry codes, credit ratings, tickers, analyst actuals, 13F
holdings, FX rates, and one fills the **portfolio-membership label** across a multi-month hold.
**Neither fills a price or a return.** Negative control reported: the regex returns 28 hits overall,
**0 on `ret`/`prc`/`close`**, and 0 on an impossible token.

**The widespread fabrication is the ZERO-fill, not the forward-fill.** `replace ret = 0 if mi(ret)`
appears in **24 distinct files of one package — all momentum and reversal** — and the other does it
too, in a code comment, **unremarked in any prose.**

**And the vendor answers the question the lane was set, in one sentence:** *"There is no price data
from one trading day applied to the next trading day."* With it comes a full missing-data
vocabulary — price `0` when no close and no quote exist, **negative** for a bid/ask average, and four
named missing-return codes. **In that vendor's daily file a multi-day halt IS visible**: the row
exists, volume is zero, the price is negative or zero, the return is a missing code.

**Two caveats carried:** the guide came from a university mirror and **may predate a 2022/2025 tape
revision**, so every quotation needs re-checking against a current source; and one source's text
comes from **a preliminary draft whose cover asks not to be quoted** — flagged rather than acted on,
with the published version unverified, **so those quotations must not be carried into any record.**

### 1.9 A "DAILY RETURN" MAY NOT BE A ONE-DAY RETURN

**From `J5`.** That vendor's daily return **spans up to 10 trading days** before being declared
missing. One reference package carries the gap width as an explicit column and screens at 1 / 5 / 14
days, with **the only stated basis for a threshold anyone found — a frequency table left in a code
comment**: *"97.2% of non missing ret_day_dif are <=3 … 99.75% are <=10."*

**Nobody builds a union-of-all-dates grid.** Both packages build **per-name min–max grids and
left-join**; zipline forms a common grid only as a trading calendar. **This programme's construction
— grid as the union of all names' dates — has no stated convention in the literature `J5` found.**
That makes it unusual, not wrong, and worth knowing.

**On entry**, the clearest statement anywhere **excludes the IPO day** — *"data isn't available for
an asset until the end of the asset's first day."* **No source states an "exclude the first N days"
rule with a reason**; min-observation thresholds range from `1` to `72` **within a single
repository**, and one canonical paper's *"more than 17 daily observations"* never defines
"observation".

### 1.10 THE FLOOR IS THE WRONG LEVER, AND MY `50/P` FRAMING WAS HALF WRONG

**From `J4`.** I have been saying all session that cost in bp scales as `50/P`. **That is true of the
COMMISSION and false of the SPREAD.**

**Relative spread is invariant to nominal price once size is held fixed — measured at exactly the
`$5`–`$20` boundary.** Matching NYSE commons at $5–$10 and $10–$20 to same-industry, same-market-cap
controls at $20–$100: **11 of 12 tests on percentage quoted spread insignificant.** The SEC states
the mechanism itself — away from the tick constraint, a price change leaves *"the cost of transacting
in the stock, for a given dollar exposure … constant."*

> **Price bites through ONE channel: the tick constraint. This programme's 33.8 bp/side names are
> ~7 ticks wide — nowhere near it.** So the original 1992 tick-noise justification **and** its modern
> practitioner replacement are both **tick-constrained-regime arguments applied to a population that
> is not tick-constrained.**

**The closed form, and its behaviour is the finding.** `P_min = 20000c / (g − s)`. At $0.005/share
against a 67.6 bp round trip:

| gross edge | defensible floor |
|---|---|
| 80 bp | **$8.06** |
| 75 bp | $13.51 |
| 70 bp | **$41.67** |
| ≤ 67.6 bp | **no floor works** |

**A 10 bp change in assumed gross edge moves the floor by 5×.** And the lever is small: **`$5`→`$10`
buys 10 bp of round trip; `$5`→∞ buys 20 bp**, half of it in the first step. **So the level IS
derivable from the cost model, and the derivation is too sensitive to the one input nobody knows to
serve as a design rule.**

**Two more premises corrected.** **The `$5` screen is not near-universal** — **81.7% of studies
impose no price filter at all**, and published levels are bimodal at `$1` and `$5` with **nothing
above `$5` ever named**; I wrote "near-universal" into the prompt. And **the screen is a SUBSTITUTE
for value-weighting** — *"Value-weighting … assigns only tiny weights to these stocks, which in turn
do not need to be excluded."* **This programme is equal-weighted, so that substitution is
unavailable: the floor does real work here that it does not do in the papers it was inherited
from.**

**The explicit negative the bar allowed: no published work varies a price screen across levels.**
Every sensitivity result is binary at `$5`. **The `$5`–`$10` band's contribution is unmeasured in the
literature and is measurable on this fixture.**

### 1.11 THE EQUAL-WEIGHTED DAILY-REBALANCING BIAS, MEASURED ON PUBLIC FILES

**From `J3`.** The dominant difference between this programme's construction and a published
equal-weighted aggregate **is not the mean return — it is the Blume–Stambaugh daily-rebalancing
bias**, measured on public files over our own window `[MEASURED IN BRIEF]`:

```
microcap decile        : +6.79%/yr
every decile above it  : +0.30% to +1.28%/yr
```

**A factor of ~11 across the floor, one-sided — 92% of months positive — and a pure construction
artefact.** Published simulation shows **name count does not attenuate it** (7.12% at 100 names,
7.18% at 900). **This programme's books are equal-weighted, so this is a property of our own
construction and not merely of a reference series.**

**`J3` ran the negative control and proved it can fire:** the value-weighted columns, which carry no
compounding bias in theory, return **+0.0002%/month against equal-weighted's +0.5487%**, and a
sentinel census returns **0 over our window but 67,250 over the full file.**

**And it was biased negative against my own list.** Of the five statistics I proposed, **three would
merely produce a number** — mean return (there is **no monotone size gradient in this window at
all**), drawdown shape (one March-2020 event), and dispersion levels. **The two strongest checks were
not on my list**: the bar calendar, and **an internal measurement needing no external series** — the
fixture's own compounded-daily-minus-buy-and-hold equal-weighted gap, **with a pre-registrable band:
0.3–1.3%/yr if the floor binds, ~6–7%/yr if it does not.**

**A premise of mine, corrected and already recorded:** no French file header declares a
survivorship-free database — `J3` censused `surviv` across four daily files and the landing page and
found **zero hits in all five**. See [`the-timestamp-round.md`](the-timestamp-round.md) §1.5 and
[`working/leads5/README.md`](../../working/leads5/README.md). **And the error was hiding a break:
the only documented statement about names leaving a French portfolio describes a convention that
CHANGED IN MAY 2015, inside this window.**

### 1.12 RESEARCH METHOD — a hazard I created, and five kinds of wrong HTTP 200

**THE HAZARD IS MINE.** All sub-agents across all five rounds share **one scratchpad directory —
263 files.** `J6`'s verification agent reported that **its own helper script was rewritten on disk
between two calls with a different signature, by an edit it did not make.** That is a **filename
collision**, not tampering. **It was benign only because the agent noticed and said so; a collision
on a parsing helper could have silently corrupted a measurement and been reported as a finding.**
**Round 6 must require lane-unique helper filenames.**

**AND AN HTTP 200 CAN BE WRONG IN AT LEAST FIVE DISTINCT WAYS**, all now measured here:

| | what returned 200 | what it actually was |
|---|---|---|
| R4 `H1` | a parameterised census | **a CDN cache replaying another query** — fabricated two whole harvests |
| R4 `H5` | a price series for a dead ticker | **a different company's prices** — 23.4% of a 64-ticker panel |
| R5 `J3` | a paper's PDF | **a 404 handler page**, 1,651 bytes of `text/html` |
| R5 `J1` | a paging parameter | **silently ignored, replaying page 1** |
| R5 `J1` | a field named `fullCount` | **an array index** — it read as "US splits flat at ~230/yr for 27 years", which `J1` nearly published and which contradicts its entire census |

**Every one of the round-5 instances was caught by the negative-control rule added this round.**
`J1` ran **11 controls including date-additivity (55 + 49 = 104)**; `J2` ran four nonsense phrases
across 16 years plus **two positive controls** proving its counts can fire; `J6` ran three, including
a cache census and an EDGAR form census with a live control.

**The summariser rule earned its keep three more times** — a reopening date given as November 1 when
the exchange's own notice says **October 31**; a bias reported as **52%** where the paper says
**97%**; and `J6` catching **its own** error, having computed that a vacated rule produced "about five
months of data" by subtracting effective from vacated, **when the compliance date fell after the
vacatur and it produced none.** That last corroborates and sharpens round 2's `F6`.

---

## 2. `J1` — stock splits · **THE PRINCIPLE HELD; `J1` RECOMMENDS AGAINST OPENING IT AS A SIGNAL LANE**

**Killer 1 genuinely absent**: the 2024 cohort sits at $120, $175, $54, $55 post-split, and even the
small regional banks that make up much of the count split from $20–30. **`50/P` = 0.04–0.9 bp. The
lane would trade at a tenth to a thirtieth of current cost.**

**The count kills it** `[MEASURED IN BRIEF]`, censused on EDGAR full-text search with **11 controls,
all passed**:

```
distinct 8-K filers mentioning a forward-split ratio
  506 (2005)  ->  104 (2010)  ->  46 (2019)  ->  63 (2024)  ->  49 (2025)
reverse-split mentions rose 3,026 -> 5,892 over the same span
forward:reverse went from ~1:3 to ~1:59
  -- against a canonical 1976-91 sample of 5,596 forward and 76 reverse. THE COMPOSITION INVERTED.
```

**And the filer count is not the usable count**: recurring 1.05-for-1 stock dividends (two names
appear **every year**), dual-class double-counts, ADRs, and reorganisation artefacts up to
2,800-for-1. **Usable events are of order 10–25/yr**, bull-market-clustered, against ~10 effective
instruments.

**Decay**, from a 2004–2011 study extracted and read locally: the announcement window holds
(+1.86% → +1.58%), but **`CAAR(0,+30)` — the only part available once the news is public — goes
+0.93%\*\*\* → −2.46%, insignificant. 89% of the two-month window lands in three days.** The ex-date
leg tested **significant in the ⅛th-tick regime and ABSENT under decimal pricing** — the mechanism
was broker promotion funded by a widening relative spread, **and this programme's window lies
entirely inside the regime where it is absent.**

**Cost direction is wrong at the ex-date**: proportional spreads rise, percentage depth falls >30%,
and volatility and beta rise ~30% permanently. **The one robust modern fact in this territory is a
VOLATILITY fact, not a return.**

**Data**: the feed's dates are **EX-dates**, and **announcement-to-ex ranges 19 to 167 days with no
fixed offset** — my warning was right and the spread is wider than I would have guessed. A
per-company route scored **10/16 within a day, 5/16 wrong by 8–264 days**. And
**`company_tickers.json` is not dead-inclusive** — Enron and Lehman absent — **the fourth independent
confirmation of that trap.**

**`J1` corrected its own error mid-brief** on a tick-tier compliance date. **All readings of that
question are recorded unresolved in §11 rather than adjudicated here.**

## 3. `J2` — dividend policy · **`J2` FINDS THE BINDING PROBLEM IS THE EARNINGS CONFOUND, NOT COST**

Findings in §1.1 and §1.2. What remains:

**Breadth**: **0.05 cuts/day through the floor**, against a published census of **176 decreases in
all of 2025**. **Decay**: medians decayed to **+23 bp / −149 bp by 1988–2000**. **Replication**: the
initiation drift **failed replication twice**, the second attempt explicitly trying to rescue it.

**Data, and it is a direct finding about this programme's own vendor:** it carries
`declaration_date`, **but the field is empty for every row before Q4 2020** — 0 of 84 on a test name
across 1999–2019. **No free feed flags a first-ever dividend**, because that is a property of a
complete history rather than of a row. **EDGAR is the only free, dead-inclusive, declaration-accurate
source — and a CUT IS TEXTUALLY INVISIBLE there, because firms simply declare a lower number.**

**`J2` opened the filings rather than trusting its phrase match**: cut precision is **~67%**, with one
hit being *"Dividend Suspension Period"* as a **credit-agreement defined term**.

**And naming the extremes caught a real defect** — this programme's own rule, applied unprompted. An
initiation read **$0.32** and a special dividend **$355,514**, because the price source was
split-adjusted; re-fetching un-adjusted **recovers a known historical close exactly.** The
implication outruns the lane: **a `$5` floor applied to an ADJUSTED series admits cheap cutters and
excludes rich initiators — a selection effect running straight down this territory's axis.** This
programme's floor is defined on **as-traded** prices, which is the right side of that.

## 4–7. `J3`, `J4`, `J5`, `J6`

Their findings are in §1.3–§1.11, because none is about a territory. Three summary notes:

**`J3` cleared its bar** with a named series, its construction quoted verbatim, and **eleven
enumerated adjustments, five quantified** off public files.

**`J4` cleared its bar** with the explicit negative it was permitted — **no published work varies the
screen across levels** — plus the closed form and its hypersensitivity.

**`J6` cleared its bar and exceeded it**: **1,646 lines, 82 primary-document citations, and ZERO
practitioner or unverified sources used as the citation for any date.** Every Tier 1 date read with
`curl` + `pypdf` + `grep`, **no summariser in the loop.** Of **the eight breaks this programme
already held, none was wrong and SIX WERE TOO COARSE TO PRE-REGISTER AGAINST.** It also lists
**thirteen things that look like calendar rows and are not** — the tick-size amendments were
**stayed**; two named rules produced **literally zero observations**. And on 2020 its recommendation
is explicit: **three rule changes, not one shock — LULD bands halved 14 trading days before the first
halt, four market-wide halts, and the NYSE floor closing with Tape A closes struck by a different
auction collared at 10%. EXCLUDE, DO NOT SPLIT.**

Its verification sub-agents separately established that **no US equities exchange withdrew its
registration in the entire window**, that the four Direct Edge/BATS exchange identities were **never
retired**, and that **two prominent venue renames are LABEL-ONLY** — participant code and MIC
unchanged — **so whether either is a break at all depends on whether this programme's vendor keys on
the code or on the display name.**

---

## 8. Sources

Full per-source detail is in the six briefs under [`working/leads5/`](../../working/leads5/).

**`[PRIMARY DATA DOC]`, read directly — the bulk of this round.** 82 primary citations in `J6` alone:
SEC releases and Federal Register documents via govinfo PDFs, exchange certificates of formation,
FINRA Rule 11140, exchange trader notices and market-data client specifications, Nasdaq and NYSE
alert archives. Plus: EDGAR full-text search and the submissions API (`J1`, `J2`); Kenneth French's
data library files and headers (`J3`); CRSP's *Stock and Index Data Description Guide* (`J5`, from a
mirror that **may predate a 2022/2025 revision**); SEC Release 34-101070 on tick sizes (`J4`).

**`[read in full]`.** O'Hara, Saar & Zhong (RAPS 2019) · Novy-Marx & Velikov on cost mitigation ·
Soebhag, Van Vliet & Verwijmeren (JBF 2024) · Hou, Xue & Zhang on screen-versus-value-weighting ·
Lipson on post-split depth · Shue & Townsend on post-split volatility · Chen & Zimmermann's Open
Source Asset Pricing code and documentation · Jensen, Kelly & Pedersen (JF 2023) code ·
Corwin's own published sample program · zipline's Pipeline engine documentation · a 2004–2011 NYSE
split study extracted locally.

**`[abstract only]` / `[snippet only]`, each flagged where used.** Kadapakkam, Krishnamurthy & Tse on
decimal-regime ex-dates · Liu, Szewczyk & Zantout (JF 2008) on post-cut drift as PEAD · Asem (2023) —
**`J2` names this as the one claim that touches this book's overnight edge, and it is unread** ·
Amihud & Li · Desai & Jain · Blume & Stambaugh — **its PDF host returned a 404 page at HTTP 200, so
its bias formula is NOT quoted** · Ball, Kothari & Shanken, flagged **unestablished** and used in no
argument.

**`[SALES INSTRUMENT]`, none used for a number.** Broker and vendor pages; dividend-focused products;
split "catalyst" material; PR Newswire releases, **explicitly refused as a primary date source by
`J6`'s sub-agents.**

---

## 9. Blocks — tool and response, not host

`curl → papers.ssrn.com`: HTTP 403 · `curl → cnbc.com`: 403 · Cambridge and JSTOR PDFs returning
**HTML at 200** · `curl → listingcenter.nasdaq.com`: **403, `text/html`, 459 bytes** ·
`WebFetch → iextrading.com`: a JS shell with no readable alert body · `assets.ctfassets.net`: a dead
CDN returning a JSON not-found object · **Stooq: an identical bot-check page for real AND bogus
tickers — not defeated, correctly** · `efts.sec.gov`: **a self-inflicted rate-limit ban from running
two harvests at once, with the lesson recorded — EDGAR's 10 req/s is across ALL hosts, not per
host.**

**`J6` did NOT hit the federalregister.gov interstitial** that round 4 logged — the JSON API and
govinfo PDF endpoints worked throughout, **so that earlier block was route-specific, not
host-wide.**

---

## 11. CONFLICTS BETWEEN BRIEFS — RECORDED UNRESOLVED, NOT ADJUDICATED

**On the principal's instruction: where briefs disagree, ALL readings are recorded side by side and
NOTHING is ruled out on the strength of a conflict.** An agent's own preference between sources is
reported as the agent's preference, not adopted as this record's finding. **None of these is
settled, and settling them is not this record's job.**

| # | question | readings, as reported |
|---|---|---|
| **C1** | **tick-size / access-fee amendments — status and date** | `H3` (R4): *delayed to the first business day of **November 2027*** · `J1` (R5): *compliance postponed to **November 2026***, given as its own mid-brief correction · `J6` (R5): the amendments were ***STAYED*, not merely delayed** — read from primary documents with no summariser |
| **C2** | **MEMX first trading day** | **2020-09-21** — MEMX's own two rule filings and its trader alerts · **2020-09-29** — an NYSE rule filing. The sub-agent preferred 09-21 as better-sourced and noted 09-29 was MEMX's first symbol *expansion*; **both readings stand here** |
| **C3** | **Bats → Cboe rename effective date** | **2017-10-16** — the BZX notice's own filing date · **2017-10-17** — the LULD Plan amendment's statement. Delaware effective date **not stated in any primary source**; bracketed 10-16 to 10-20 |
| **C4** | **NYSE Alternext → NYSE Amex** | **2009-03-18** — the exchange's own operating agreement · **2009-03-03** — the SEC's own 2012 notice. **Two primary sources disagree.** Both pre-window, so immaterial to this fixture, **recorded because the disagreement is the point** |
| **C5** | **is there a published daily autocorrelation for an equal-weighted US portfolio?** | `H6` (R4): searched and found **none citable** · `J3` (R5): found **one — ρ = 20.22%, CRSP EW index, daily, 1964–93** — and judged it a within-month 20-observation average, 33 years stale, on a universe a floor removes. **A figure exists; whether it is usable is the open question, and `J3`'s rejection is `J3`'s judgement, not a fact** |
| **C6** | **the vendor's own daily adjustment basis** | The API documentation says the daily-adjusted endpoint returns **raw as-traded OHLCV** with adjustment confined to a separate column · **the same vendor's support FAQ says it adjusts open, high, low, close and volume.** `G6` (R3) found both. **The vendor contradicts itself and neither statement has been tested against the data here** |
| **C7** | **what is wrong with Corwin–Schultz** | `H4`/round 4: it **understates** effective spreads for small, illiquid names, so 33.8 bp/side may be a **floor** · `J5`/round 5: the author's own program **fabricates the high and low** on no-trade days by re-anchoring the prior-day range. **Not necessarily contradictory — but they push the interpretation of 33.8 in different directions, and neither has been checked here** |
| **C8** | **the fixture's bar count** | **4,187** if four unscheduled-closure dates are absent as rows · **4,191** if present. This programme's recorded measurement is **4,187**; the `~4,190` `J6` reasoned from **was my rounding, not the measurement.** **Both branches stand until the four dates are checked directly** |

**Two notes on how to read this table.** First, **a conflict is not a reason to discard either
side** — several of these are two primary sources disagreeing, which is a fact about the record
rather than an error by an agent. Second, **where an agent stated a preference it is preserved as a
preference**; the strongest methodological claim available (`J6` read every Tier 1 date from a
primary document with no summariser in the loop) **is evidence about that agent's method, not a
ruling on the others.**

---

## 10. What this record does not claim

- **Nothing here was measured on this programme's fixture.** `[MEASURED IN BRIEF]` means a public
  file or endpoint. Figures restated from our own record — 33.8 bp/side, the 67.6 bp round trip,
  `keep_v2`'s clauses, 4,187 bars, ~10 effective instruments — are quoted, not recomputed.
- **Nothing was backtested, no null was drawn, no cell was scored, no candidate exists.**
- **Nothing is repaired.** The `SC 13D` filter, the `acceptanceDateTime` timezone, the two
  Corwin–Schultz findings, `adjusted=false`, the `LISTING_STATUS date=` call, and the four-date bar
  check are **all reported and none acted on.**
- **No territory is closed.** `J1` recommends against opening as a signal lane; **closure remains the
  principal's under [R15](../RULES.md#r15).**
- **FIVE of my own premises were wrong this round** and are recorded as mine: the killer-1 screen
  conflating size with price (§1.1); `50/P` applied to the spread as well as the commission (§1.10);
  the `$5` screen described as near-universal (§1.10); the French survivorship-free declaration
  (§1.11); and **the shared scratchpad that let two agents overwrite each other's code (§1.12).**
- **Both books are unchanged. Nothing is elevated out of the research folder.**
