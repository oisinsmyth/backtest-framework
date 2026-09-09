# working/leads3/ — round 3, **PREPARED AND NOT COMMISSIONED**

**Prepared 2026-09-09**, while round 2's agents are still out. **No agent has been dispatched on
any lane below and no brief exists in this directory.** Round 3 is deliberately held because
**round 2's returns must extend the exclusion list before round 3 can be told what to avoid** —
that is the whole mechanism by which these rounds stay off each other's ground, and dispatching
both at once would break it.

The quarantine contract of [`../leads/README.md`](../leads/README.md) applies unchanged and is not
repeated. Under [R15](../../docs/RULES.md#r15) nothing here closes or admits anything.
**Nothing below has been measured. Every "kill number" is a number somebody would have to go and
get; not one of them has been got.**

| lane | territory | route | kind |
|---|---|---|---|
| `G1` | mutual-fund and ETF flows, forced fire-sale selling, ETF ownership share | **(a)** | signal |
| `G2` | **the death process** — cause-of-death census, and the terminal return nobody books | **(b)** | **method + signal** |
| `G3` | trading halts, LULD bands, and the re-listing resumption | **(b)** | signal |
| `G4` | 13D / 13G — the *outside* accumulator, as distinct from `F2`'s insider | **(a)** | signal |
| `G5` | **the revenue side of a long book** — fully-paid lending, cash interest, retail account rules | — | **not a signal** |
| `G6` | **documented defects in the data we already own** | — | **not a signal** |

---

## The design, and the criticism of round 2 that produced it

**Round 2's four signal lanes were all route (a).** Every one of them — index reconstitution, Form
4, earnings dates, corporate supply — asks *somebody buys or sells for a reason unrelated to
price*. [`docs/future-strategies.md §0`](../../docs/future-strategies.md) names **two** ways out of
the liquidity-compensation trap, and **the programme has never commissioned research on the second
one**: *the move is large and slow relative to the spread — then the toll is a rounding error
rather than the whole payoff.*

That omission is mine and it is not small. The record's own arithmetic for why the fade died is
**+219.8 bp gross against a 216.6 bp round trip**; route (b) is the design choice that inverts that
ratio, and no round has asked it. **`G2` and `G3` are route (b) on purpose.** A name walking to zero
over months, or one that reopens after an eight-month halt, moves in multiples of its spread —
whatever else is wrong with those lanes, *the cost wall that killed the fade is not the thing that
would kill them*, and the cost wall has been the binding constraint on nearly everything here.

**Two lanes are again not signal hunts**, for the reason round 2 recorded: round 1's three most
valuable returns were a hole in the floor methodology, a fixture defect on three committed studies,
and a withdrawn inference — **none of them a strategy**. `G5` and `G6` are commissioned in that
lane deliberately.

---

## The non-overlap audit

**File-level hit counts, case-insensitive, over `docs/`** — 486 files in `docs/decisions/`, plus
`FINDINGS.md`, `RULES.md` and the whole `research/` directory. Counted, not asserted.

| term | files | term | files | term | files |
|---|--:|---|--:|---|--:|
| fund flow | **0** | fire sale | **0** | Coval | **0** |
| outflow | **0** | ETF ownership | **0** | 13G | **0** |
| LULD | **0** | going dark | **0** | going concern | **0** |
| wash sale | **0** | pattern day / PDT | **0** | fully paid | **0** |
| stock yield enhancement | **0** | odd lot | **0** | PFOF | **0** |
| dark pool | **0** | risk parity | **0** | tracking error | **0** |
| cross-listed | **0** | Google Trends | **0** | CDS | **0** |
| 13D | 2 | 13F | 3 | institutional ownership | 1 |
| "limit up" | 2 | Chapter 11 | 1 | closing auction | 3 |

**The non-zero rows were opened and are incidental, which is why they are listed rather than
hidden.** `13D`/`13F` appear in a RESULT record's prose, in the futures-data survey and in the
prop-firm filings review — never as a variable. `closing auction` is
[D364](../../docs/decisions/D364-the-auction-participation-bound.md) measuring auction **volume**
as a participation denominator, not auction **events**. `Chapter 11` is one passing mention.

**A hit count is evidence of absence in the written record, not proof the thinking never happened.**
Anyone acting on a lane should still grep the record for its own construction before writing a
pre-registration.

---

## G1 — forced institutional flow

**The quantity.** Fund-level flows mapped onto holdings, giving a per-name *pressure* variable:
which names are held by funds currently being redeemed. Coval–Stafford fire sales, and separately
the ETF-ownership share of each name.

**Why it is not in the catalogue.** Zero hits on every term. The programme has studied the
*issuer* as marginal seller ([`future-strategies.md §1`](../../docs/future-strategies.md)) and, in
round 2, the *index* as forced buyer. **The fund as forced seller is the third leg and is absent.**

**Mechanism.** Route (a) in its purest published form: a redeemed fund sells its holdings pro rata
regardless of price, so the pressure is mandate-driven and dated.

**Data.** N-PORT (monthly portfolios, filed quarterly), 13F (quarterly, 45-day lag), fund flow
aggregates. All free from EDGAR — **and the programme already owns an EDGAR puller**
([D331](../../docs/decisions/D331-the-deal-filter.md)).

**The kill number: `n_eff`, not the return.** This is a *quarterly* variable pointed at a *daily*
book. Four independent observations a year per name, times 16 years, against a fixture that carries
**10.06 effective independent instruments over a held book** — 1,573 names is not 1,573 bets, and
the ETF universe's far worse **2.2** is what closed D251. Before anything else: compute the
effective number of independent observations a quarterly-rebalanced cross-section actually gives.
**If the honest `n_eff` is two figures, the lane is over and nothing else needs measuring.**

**The honest risk.** The 45-day 13F lag means the holdings are stale by construction, and the
published fire-sale results are on institutional-quality universes, value-weighted, in an era
before ETF ownership was what it now is.

---

## G2 — the death process

**This lane is earned, not invented.** [`FINDINGS.md §60`](../../docs/FINDINGS.md) — round 1's own
output — ends with the rule *"a status count is not a cause of death… census the instrument types
and the death causes when a fixture is built."* **That rule was written about the 551-fund ETF
fixture and has never been applied to the equity fixture**, where *dead-inclusive* is the defining
claim and the record's own build-out figure is **1,580 names, 35.7% dead**
([`FINDINGS.md`](../../docs/FINDINGS.md), from D256). The record demands this check of itself and
it has not been done.

*(A small bookkeeping note found while checking that figure, recorded rather than swallowed: the
same file quotes the panel as **1,573 names** in five other places. The seven-name difference is
almost certainly build-versus-load and is not investigated here — but **a lane auditing the death
cohort should reconcile the two counts before trusting either**.)*

**Two parts, and the first is a method check on our own most-used file.**

**(i) The cause-of-death census.** On the ETF fixture the answer was devastating: **23 of 24 dead
names were closed-end funds**, i.e. orderly term maturities and wind-ups, and *a fixture whose
deaths are fund maturities is not measuring delisting risk at all.* Nobody knows the equity
fixture's split between acquisition, failure, exchange-rule deficiency, going-private and going
dark. **`delistingDate` is in the metadata; cause is not.**

**(ii) The terminal return nobody books.**
[D256 §86](../../docs/decisions/D256-the-book-on-single-names.md) states the convention verbatim:
*"Positions are carried to the final bar and closed there."* A name that files Chapter 11 after its
last print therefore books **its last quoted move, not its loss**. In the academic fixtures this is
the classic delisting-return correction and it is not small. **Whether it flatters or penalises
this programme depends entirely on part (i)** — which is exactly why the census comes first.

**Mechanism, for the signal half.** Route **(b)**: a name walking to zero moves in multiples of its
spread. The cost wall that has killed nearly everything here is not the binding constraint on it.

**Data.** Exchange deficiency notices, Chapter 11 dockets, Form 25 and Form 15 on EDGAR, and the
provider's own `delistingDate`. The external research question is **which of these is retrievable
in bulk, point-in-time, and free**.

**The kill number.** The census itself. **If the equity fixture's deaths are overwhelmingly
acquisitions, there is no failure cohort to study** — and, separately, the `dead-inclusive` claim
in [D252](../../docs/decisions/D252-the-dead-inclusive-us-single-name-universe.md) needs amending
in writing. Either outcome is worth the work; **only one of them is a lead.**

**The honest risk.** Deal-driven death is already trodden — D330/D331/D335 built a deal filter and
found *the tape cannot separate deals from reversals*. **This lane must be scoped to failure-death
and told not to re-analyse merger pinning.** And the short side of a dying name runs straight into
borrow, which is excluded ground for good reasons.

---

## G3 — halts, LULD, and the re-listing resumption

**The quantity.** Multi-day trading halts and their resumption print; LULD limit-up/limit-down band
excursions.

**Why it is not in the catalogue, and this is the interesting part.** The programme has already met
this event **and treated it as hygiene**.
[D343](../../docs/decisions/D343-the-re-listing-clause-on-the-universe-floor.md) exists because
NBIS — the former Yandex, *first day back after an eight-month halt* — was **4.4% of D342's entire
candidate P&L with no dollar-volume percentile at entry**. The response was correct and was to
tighten the universe floor to `keep_v2`. **The event was excluded as a defect and never examined as
a phenomenon.** `LULD` has zero hits.

**Mechanism.** Route **(b)**. A halt is the one moment the price mechanism is switched off; the
resumption is a dated, scheduled reintroduction of a queue that has had days to build.

**Data.** Nasdaq and NYSE halt files, and the LULD band feed. **Retrievability point-in-time is the
first question**, not the effect size.

**The kill number: a count.** How many multi-day halt-and-resume events occur in the fixture on
names that pass `keep_v2` at resumption. D343 surfaced exactly one by accident.
**If the answer is single digits this is [D264](../../docs/decisions/D264-the-intraday-short-on-single-names.md)'s
thin-universe problem again and the lane dies on arithmetic.** D264 ran on **eight names** and said
so itself: *"eight names is thin"*. Ask for the count before anything else.

*(Correction to a committed record, made here because it was found here: the scan record's `X3`
entry calls this "forty names is D264's problem again". **D264 is eight names, not forty.** The
argument `X3` was making is unaffected; the number is wrong and is corrected on the record.)*

**The honest risk.** `keep_v2` was written specifically to exclude names with no demonstrated
liquidity, which is precisely the state a resuming name is in — **the floor and the lane are in
direct tension, and that tension is the finding if the count survives.** Whether a retail account
can even participate in a resumption auction is a real question and belongs to `F5`'s territory,
not this one.

---

## G4 — 13D / 13G, the outside accumulator

**The quantity.** Schedule 13D (activist, control intent) and 13G (passive) filings on crossing 5%.

**Why it is not in the catalogue.** Two incidental hits, neither a variable. **`F2` is out on Form
4, which is the *insider*; a 13D is an *outsider* accumulating a stake** — a different filer, a
different form, a different deadline and a different mechanism. They should not be merged.

**Mechanism.** Route (a), and the mandated disclosure is itself the dated event.

**Data.** EDGAR, free, and **the puller already exists** — this is the same argument that put `F2`
on round 2's slate, and it is the cheapest lane here by implementation distance.

**The kill number.** The count of 13D filings landing on fixture names that pass `keep_v2` on the
filing date — **and the lag**. A 13D is due within **5 business days** of crossing the threshold
since the 2024 amendment and **10 calendar days** before it. That amendment **splits the sample in
two mid-fixture**, which is a stationarity break declared in advance rather than discovered later.

**The honest risk.** The filing is old news by construction, this is among the most-published
anomalies in existence, and the equal-weighted $5-floored universe is not the one the published
results live on.

---

## G5 — the revenue side of a long book *(not a signal)*

**Why this exists.** `F5` asks what a basis point saved on execution is worth. **`G5` is its
mirror: what does the book EARN while it simply sits there?** Zero hits on `fully paid`, `stock
yield enhancement`, `wash sale`, `PDT`. The programme has studied **borrow as a cost to the short**
— excluded ground — and **has never once looked at lending income as revenue to the long.**

**The quantity.** Fully-paid securities lending income; interest on idle cash; and the account-level
rules that bound a retail book — pattern-day-trader status, Reg T versus portfolio margin, wash-sale
treatment of a high-turnover book.

**Why it could matter more than a signal.** The record's binding numbers are cost numbers: a cell
where **commission alone was 1.92 bp/side against a 1.06 bp breakeven — it lost at a zero spread**.
Revenue accruing to a held position is arithmetically identical to alpha and does not have to be
discovered.

**The kill number.** What fully-paid lending actually pays **on the names this programme would
hold**. The lendable-at-a-real-rate names are the hard-to-borrow tail, and a $5-floored liquid
universe is largely *not* that tail. **If the rate on the actual holdings rounds to zero, the
lending half is over** — and the broker takes half of what remains. The account-rules half survives
that verdict regardless, because it constrains every book here whether or not anyone has written it
down.

**The honest risk.** This produces no signal and may produce nothing but a paragraph of constraints.
**That is an acceptable outcome and is stated in advance so the lane cannot be scored as a failure
for delivering exactly what it was asked for.** Tax treatment is jurisdictional and this programme's
records do not state a jurisdiction; the lane must not assume one.

---

## G6 — documented defects in the data we already own *(not a signal)*

**Why this exists.** It is the lane that has actually paid. Round 1 returned **§59** (the best-of-N
permutation floor is blind to sign-fitting — a 16-signal pure-noise composite clears it by +1.28)
and **§60** (the "ETF fixture" is 27.2% closed-end funds and its mortality cohort is 23 of 24
CEFs). Neither was a lead. Both changed what the programme believes about files it had already
published on.

**The quantity.** Documented, citable defects in the specific data sources this programme depends
on: the provider's adjustment conventions, split and dividend handling, ticker reuse, known gaps.

**The standing evidence that this keeps happening.** Three separate incidents are already on the
record: the **15m-versus-daily corporate-action basis split** (one name sat at 5× its own prices
and no price factor can repair a spin-off), the **thirty fabricated return days** of §18 — corporate actions booked as dividends, from D333 — and
**§60**. §60's own text calls it *"the third place the programme has been caught by an unexamined
corporate-action or instrument basis."* **Three is a pattern, and nobody has gone looking on
purpose.**

**The kill number — and it is a different kind.** This lane has no premise return. **It is worth
doing only if it yields a check runnable against a file already in `data/`.** That is the bar, it
is stated in advance, and round 1's version of this cleared it twice.

**The honest risk.** It may return a list of things that are true of everyone's data and actionable
by no one. **A defect that cannot be turned into an assertion is a worry, not a finding**, and this
lane should be told that in its brief.

---

## THE EXCLUSION LIST FOR ROUND 3 — the durable part of this file

**Everything round 1 and round 2 were kept off, plus round 2's own six territories.** This is the
list that would go verbatim into every round-3 prompt.

**Carried from round 2:** credit spreads / yield curve / defensive–cyclical rotation as a regime
gate · calendar effects (turn-of-month, day-of-week, pre-FOMC drift, the even-week FOMC cycle) ·
short interest, days-to-cover, borrow fees, FINRA and FTD data · short-term reversal,
industry-relative and residual reversal, return clustering · closed-end fund discounts · lead–lag of
every kind · signal combination, ML return prediction, factor-zoo multiple testing · **options of
any kind** · inferring order flow from price action · price-level / support-resistance /
volume-profile maps · at-the-market shelf issuance · XBRL cash runway · merger-arbitrage acquirer
shorting · CFTC COT positioning · momentum, wedge breakouts, MACD, stops and targets.

**Added by round 2 itself — these six are now spent ground:** index reconstitution and forced index
flows · SEC Form 4 insider transactions · earnings announcement dates, PEAD and the announcement
premium · position sizing and portfolio construction · retail IBKR execution cost · corporate supply
events (lockups, buybacks, SEOs, spin-offs).

**Three round-3-specific exclusions with their reasons:**

1. **MERGER AND ACQUISITION DEATH IS NOT `G2`'s SUBJECT.** D330/D331/D335 built a deal filter and
   concluded *the tape cannot separate deals from reversals*. `G2` is **failure-death only** and
   must be told so, or it will re-run the deal filter under a new name.
2. **THE OVERNIGHT SESSION'S DATA AND VENUES ARE ALREADY SURVEYED.**
   [`research/futures-data/12-substitutes-and-lateral.md`](../../docs/research/futures-data/12-substitutes-and-lateral.md)
   covers Blue Ocean ATS, IBEOS, the 20:00–04:00 window, Databento and Tiingo pricing, and the SIP's
   absence in that hour. **No round-3 lane may re-survey overnight venue data.**
3. **OPTIONS REMAIN ANOTHER SESSION'S TERRITORY.** The concurrent session has since produced D406
   and D408 on options snapshots. The prohibition stands and is now broader in fact than when round
   2 was written.

---

## Recorded and deliberately NOT proposed

Kept here so a future session can see they were considered and why they were dropped, in the
tradition of the scan record's `X4`.

- **Macro releases (CPI, NFP, jobless claims) as dated events.** Genuinely uncovered — zero hits on
  `nonfarm` and `jobless`, free from BLS and FRED — and the fit looks sharp, because **every major
  release prints at 08:30 ET, inside the untraded window where this programme's edge lives.**
  **Dropped anyway:** it is a calendar effect, calendar effects are excluded, and `K1` scored 17 on
  the round-1 frame and fell hard. It is listed, not recommended.
- **Dual-class and ADR/ordinary pairs.** Same cash flow, two prices, no fundamental leg. **Dropped
  on data:** the linkage table is the whole problem and the fixture is unlikely to carry the foreign
  ordinary side.
- **The sub-$5 tail that `keep_v2` discards.** The floor is the most consequential single choice in
  the universe definition and cost in bp scales inversely with price. **Dropped as already
  reasoned** — D338, D339 and D343 are three records deep on it.
- **Deflated Sharpe, PBO and the multiple-testing literature.** It would be the natural follow-up to
  §59's sign-fitting hole, but **factor-zoo multiple testing is on the exclusion list** and the hole
  §59 found is a property of *this* floor, which is measurement work rather than reading.

---

## What this file does not claim

Nothing here is a measurement, a result, a null, a candidate or a book entry. **No lane has been
commissioned and no brief exists in this directory.** The hit counts are the only numbers in this
file that were computed rather than quoted, and they are counts of files in the written record —
**not evidence about any market.** Every kill number named above is a number somebody would have to
go and get. **Both books are unchanged; nothing is closed and nothing is admitted, which remains
the principal's call under [R15](../../docs/RULES.md#r15).**
