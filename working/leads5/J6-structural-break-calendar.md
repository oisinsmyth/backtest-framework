# J6 — A STRUCTURAL-BREAK CALENDAR FOR 2010-01-04 TO 2026-08-26

**Round 5, lane J6 (data).** Quarantined under the contract in
[`../leads/README.md`](../leads/README.md); under [R15](../../docs/RULES.md#r15) nothing here closes
or admits anything. **External evidence only — I have no access to the programme's fixtures and
assert nothing about them.** Every row below is a claim about the *world*, not about the data.

**What this is for.** A structural break is a **pre-registration input**, not a nuisance. A study
spanning one of these dates must declare the sample split *in advance* or it is fitting two regimes
and reporting one. Four rounds found individual breaks by accident, each in a different lane, with
nowhere to put them. This is the place.

---

## THE CALENDAR, IN ONE TABLE

**38 dated entries across 31 Tier 1 rows** (several rows carry more than one date, which is the whole
problem with them). **Every entry names a mechanism, cites a primary document, and says which kind of
date it is.** Citations, verbatim quotes and the mechanism in full are in §2–§4 under the row id.
Data classes: **B** = daily bars, **CA** = corporate actions, **E** = EDGAR filings.

Also in §2: **BAR-12** the trading calendar — **four missing bars** (2012-10-29, 2012-10-30,
2018-12-05, 2025-01-09) and **one fewer bar every year from 2022** (Juneteenth). **BAR-12c turns that
into a direct arithmetic check on the fixture's own bar count, and it is the most actionable line in
this brief.**

| # | date | type | row | class | mechanism in one line |
|---|---|---|---|---|---|
| 0 | **2010-02-28** | EFFECTIVE | ED-5 | E | **8-K Item 5.07 added**; and **10-K/10-Q items RENUMBERED**, voting results migrating into the 8-K |
| 1 | 2010-06-10 | APPROVAL | BAR-1 s1 | B | single-stock trading pauses, **S&P 500 only** — not this universe |
| 2 | 2010-09-10 | APPROVAL | BAR-1 s2 | B | extended to Russell 1000 + listed ETPs — still not this universe |
| 3 | **2010-09-27** | EFFECTIVE | CA-1 | CA | FINRA may **refuse to process** an OTC corporate action; 10-day pre-record-date notice |
| 4 | **2011-02-28** | COMPLIANCE | BAR-2 | B | short sales restricted above the NBB once a name is −10%; **damps the downside tail** |
| 5 | **2011-06-23** | APPROVAL | BAR-1 s3 | B | pauses extended to **all remaining NMS stocks** — the stage that reaches this universe |
| 5b | 2011-04-04 / **2012-01-27** | EFFECTIVE | ED-5 | E | 8-K **Item 5.07(d)** and **Item 1.04** (mine safety) added — each a structural zero before its date |
| 5c | **2012-05-21 → 2014-05-30** | RENAME / CLOSURE | BAR-14 | B | **NYSE Amex → NYSE MKT**; **NSX ceases trading 2014-05-30** — vendor exchange-code field, not price |
| 6 | **2013-04-08** | OPERATIVE | BAR-3 | B | LULD Phase I (Tier 1 only); **MWCB switches to S&P 500 and 7/13/20%** |
| 7 | **2013-08-05 → 2014-05-12** | OPERATIVE, **ramp to full implementation** | BAR-4 | B | LULD reaches **Tier 2 — most of this universe**; ±10% bands censor daily High/Low |
| 8 | **2013-12-09** | OPERATIVE | BAR-5 | B | **odd lots enter consolidated VOLUME; O/H/L/C unchanged.** Breaks any dollar-volume screen |
| 9 | **2016-07-18** | IMPLEMENTED | BAR-6 | B | LULD reference price on quote-opens fixed → **pause rate drops sharply** in thin names |
| 10 | **2016-10-03 → 2016-10-31** | OPERATIVE, **4-week ramp** | BAR-7 | B | **Tick Size Pilot: ~1,200 small caps quoted in $0.05** |
| 11 | **2017-09-05** | OPERATIVE | CA-2 | CA | **ex-date moves from 2 business days before the record date to 1** — and **zero ex-dates on that day** |
| 12 | **2017-11-20** | IMPLEMENTED | BAR-8 | B | reopening-auction mechanics change at every primary listing exchange at once |
| 13 | **2018-09-28** | TERMINATED | BAR-7 | B | nickel quoting ends at the close, **one trading day early** |
| 14 | 2019-06-15 / 2020-06-15 / **2021-06-15** | COMPLIANCE, **by fiscal period** | ED-1 | E | Inline XBRL, phased **by filer class** — no single calendar date |
| 14b | **2017-03-21 → 2019-03-01** | RENAME | BAR-14 | B | **NYSE MKT → NYSE American**; **CHX → NYSE Chicago**; **Bats → Cboe**. Operative dates only BRACKETED |
| 15 | **2020-02-24** | ACTIVATION | BAR-9 | B | **LULD bands halved at open/close (±20%→±10%) — 14 trading days before the COVID halts** |
| 16 | **2020-03-09/12/16/18** | EVENT | BAR-10 | B | four MWCB Level 1 halts — a **15-minute hole in every name** on four days |
| 16b | **2020-03-23 → 2020-06-17** | CLOSURE | BAR-13 | B | **NYSE floor closes; Tape A closing prices come from a different auction process, collared at 10%** |
| 16c | **2020-04-21** | OPERATIVE | CA-4 | CA | Nasdaq **$0.10/10-day mandatory delisting** and **1:250-over-2-years no-compliance-period** |
| 17 | **2021-09-28** | COMPLIANCE | BAR-11 | B | OTC quotes cease for non-current issuers; **"quotes stopped" stops meaning "trading stopped"** |
| 17b | 2023-03-20 / **2023-04-13** | EFFECTIVE / COMPLIANCE | ED-6 | E | **Form 144 moves from paper to EDGAR** — the pre-2023 series is *incomplete by construction*, not low |
| 18 | 2023-02-27 / **2023-04-01** | EFFECTIVE / COMPLIANCE | ED-2 | E | 10b5-1 rule binds 5 weeks **before** the Form 4/5 checkbox exists |
| 19 | **2023-12-18** / **2024-06-15** | COMPLIANCE | ED-4 | E | **new 8-K item code 1.05** — and **not selectable in EDGAR before 2023-12-18**; **SRCs lag to 2024-06-15** |
| 19b | **2023-12-18 → 2024-12-20** | UNDOCUMENTED | ED-3b | E | **daily `form.idx` truncates `SCHEDULE 13D` to `SCHEDULE 1`** — daily and quarterly indices disagree for a year |
| 20 | **2024-02-05** | EFFECTIVE | ED-3 | E | 13D deadline → **5 business days**; 13D/G EDGAR cut-off **17:30 → 22:00 ET** |
| 21 | **2024-05-28** | OPERATIVE | CA-3 | CA | **ex-date becomes the record date** — the offset reaches zero |
| 21b | **2023-11-01 / 2024-10-07** | APPROVED | CA-4 | CA | Nasdaq reverse-split advance notice; split-into-another-deficiency no longer cures |
| 22 | **2024-09-30** | COMPLIANCE | ED-3 | E | **13G** deadlines finally bind — **8 months after 13D** |
| 23 | **2024-12-16/18/19** | COMPLIANCE | ED-3a | E | 13D/G **structured data** and the `SC 13D` → `SCHEDULE 13D` rename — **NOT a cutover; both strings needed throughout** |
| 24 | **2024-12** (month only) | RETROACTIVE | ED-7 | E | **Financial Statement Data Sets rewritten in place back to 2009 Q1** — same filenames, different data |
| 25 | **2025-01-09** | CLOSURE | BAR-12 | B + CA | missing bar; **and ex-dates DOUBLE on 2025-01-10** |
| 25b | **2025-01-15 / 2025-01-17** | APPROVED | CA-4 | CA | **NYSE and Nasdaq bar a SECOND reverse split within a year** — serial reverse splitting is foreclosed; names delist instead |
| 25c | **2025-11-03** | OPERATIVE | §6.9 | B | **MDI round-lot definition live** — the odd-lot/round-lot boundary moves for stocks above $250 (interacts with BAR-5) |
| 26 | **2026-03-18** | EFFECTIVE | ED-8 | E | **FPI directors and officers begin filing Form 4s** — a composition break, not a behavioural one |

**NOT ROWS, AND THAT IS HALF THE VALUE OF THE LANE.** §6 now carries **thirteen** entries that look
like calendar rows and are not. The ones most likely to be mistaken for breaks:

| looks like a break | actually |
|---|---|
| Reg NMS **half-penny ticks and lower access-fee caps** | **STAYED 2024-12-12, never in force** at any point in the window (§6.1) |
| **Rule 610T transaction fee pilot** | **VACATED 2020-06-16**; no pilot securities ever designated, **zero observations** (§6.5) |
| **Rule 13f-2 / Form SHO** | exempted twice, now **2028**; **zero filings exist**, censused with a control (§6.6) |
| **Rule 10c-1a / FINRA SLATE** | reporting delayed to **2028-09-28**; nothing reported or disseminated (§6.7) |
| **SEC climate disclosure** | **STAYED 2024-04-04** before any compliance date; **no data** (§6.11) |
| **Share repurchase daily tables** | vacated **before its first required filing** (§6.4) |
| **Order Competition Rule, Reg Best Execution** | **never adopted**; formally **withdrawn 2025-06-17** (§6.10) |
| **MDI competing consolidators** | **still not in effect**; its clock never started (§6.9) |
| **Nasdaq $5M MVLS delisting rule** | approved 2026-07-22, **stayed seven days later**; zero delistings (§6.12) |
| **NYSE $0.25 minimum trading price** | approved 2026-08-14 but **effective 2027-07-01** — outside the window (§6.13) |
| **Nasdaq board diversity** | the **one exception**: a real regime, **2022-08-06 → 2024-12-11** (§6.8) |

Also not breaks: the MWCB pilot becoming permanent on **2022-03-16** (thresholds unchanged — BAR-10);
Rule 605's 2026-08-01 compliance date (**25 days** before the window ends — §5); no change to trading
hours and **no overnight session ever set a closing price** (BAR-15); and seven candidates swept and
excluded on mechanism, including the Consolidated Audit Trail (§5.1).

**Two dates to EXCLUDE rather than split on:** **2015-08-24** (the SEC's own research division drops
it from every table — BAR-8) and the **2013-08-05 → 2014-05-12** LULD partial-treatment ramp (BAR-4).

**Rule 11140(b)(2) is a standing convention, not a break — and it catches stock splits.** See
CA-NOTE; it bears directly on lane J1.

---

## 0. HOW THE DATES WERE OBTAINED, AND THE THREE CONTROLS I RAN

**Every date in Tier 1 was read directly out of a primary document, not through a summariser.** The
lane brief is made of dates, so this mattered more than usual: a date obtained through a summariser
is *weaker* than a snippet, not stronger.

Method: `curl` with a project contact User-Agent
(`Backtest Framework Research research@backtest-framework.org` — no personal address was used
anywhere), raw bytes to disk, `pypdf` for PDFs, then `grep` over the extracted text by me. Search
engines were used **only to locate documents**; no date below rests on a search-result summary
unless the row says so explicitly.

**CDN / cache control (required because I harvested a parameterised endpoint).** The Nasdaq Trader
notices live at `nasdaqtrader.com/TraderNews.aspx?id=<notice>`. An HTTP 200 from a parameterised
endpoint can be a cache replaying a *different* query's result, so I censused a value that must
return nothing:

| request | result |
|---|---|
| `?id=ETU9999-99` (does not exist) | HTTP 200, but **redirected to `Trader.aspx?id=http404`**; **0** matches for `Limit Up`, `Odd Lot`, `August 5, 2013`, `December 9, 2013` |
| `?id=ERA2012-7` (distinct real notice) | returned **its own** distinct content — the *pre-delay* "Effective February 4, 2013" headline, **not** a replay of `ETU2013-25` |

**Control passes: no evidence of cache replay on that endpoint.** The second leg is the stronger
one — it shows the endpoint discriminates between ids rather than serving one cached body.

**A SECOND CENSUS-WITH-CONTROL, on the one row where a zero IS the finding.** §6.6 claims no Form SHO
filing has ever existed. EDGAR full-text search returns **0** for `forms=SHO`; the **identical query
shape** against `forms=13F-HR` and `forms=SD` each returns **10,000+**. **So the zero is a real zero,
not a broken filter or an empty parameter.**

**A THIRD, on completeness rather than on a value.** §BAR-12b's claim of *exactly four* unscheduled
closures rests on enumerating **every Nasdaq Equity Trader Alert id from 2010 to 2026** (~2,400
titles) until each year 404'd — a method validated by the fact that it **surfaced Sandy and the Carter
closure independently, before they were searched for** — cross-checked against a Federal Register
full-text search of all SEC documents in the window, which was itself validated by successfully
retrieving the Sandy language it was expected to find.

**Blocks, logged by tool and response (not by host):**

1. `curl -L` → `https://www.sec.gov/oiea/investor-alerts-bulletins/investor-alerts-circuitbreakers`
   — **HTTP 403, 510 bytes**, after a cross-host redirect to `investor.gov`. The SEC investor
   bulletin on stock-by-stock circuit breakers could not be read. I did not need it: the underlying
   release numbers came out of the LULD approval order instead.
2. `curl -L` → `https://www.sec.gov/files/rules/final/2020/34-89891.pdf` — **HTTP 404** (the
   Rule 15c2-11 adopting release is not at the `/files/rules/final/<year>/` path). Recovered from
   the Federal Register text via `govinfo.gov`.
3. `curl -L` → `https://www.sec.gov/files/rules/sro/nms/2012/34-67090.pdf` — **HTTP 404**.
   Recovered from `govinfo.gov` (77 FR 33531).
4. `curl` → `https://efts.sec.gov/LATEST/search-index?q=…` — Akamai **`Access Denied`**, unchanged by
   `Accept: application/json`, `--compressed` or a `Referer` header. **Naming the tool, not the
   host:** the refusal is against this curl client on that path; `www.sec.gov` and `govinfo.gov`
   served everything else with the same User-Agent. Consequence: the EDGAR full-text search coverage
   start could not be bracketed empirically (§8.8).
5. **A BROWSER TOOL WAS DENIED WHERE `curl` SUCCEEDED.** `mcp__Claude_Browser__navigate` to
   `nyse.com` → *"navigation to https://nyse.com was denied or failed"*, from the **permission
   system**; plain `curl` to `www.nyse.com` returned **200** throughout. **This is a tool permission
   block, not a site block** — exactly the distinction the programme's own note on logged blocks
   insists on, and the second time that note has paid off.
6. `curl` → `https://www.cadc.uscourts.gov/internet/opinions.nsf/…/19-1042-1847356.pdf` — **HTTP 404**
   with body `<title>404 Page Not Found | District of Columbia Circuit …</title>`, even though that is
   the URL the CourtListener API records as the court's own link. The **CourtListener mirror of the
   same court PDF** was used instead for the Rule 610T vacatur (§6.5).
7. `curl` → `nasdaqtrader.com/content/technicalsupport/<year>tradingcalendar.pdf` — returns a
   **42,861-byte HTML error page** for every year before 2021. 2021–2026 are real PDFs but **mark
   holidays by colour fill only, with no date labels**, so they cannot corroborate a specific date by
   text extraction. The trading calendar was therefore built from NYSE Rule 7.2 and the exchange
   alerts, not from these files.

> **`federalregister.gov` did NOT reproduce the 302-to-interstitial behaviour an earlier round
> logged.** Its **JSON API** worked normally here. Document PDFs were nonetheless taken from
> `govinfo.gov` and the important ones verified a second time against their direct `sec.gov` copies.
> **The earlier finding is not contradicted — a different endpoint was used — but it is not
> reproduced either.**

**TWO PAIRS OF PRIMARY SEC DOCUMENTS CONTRADICT EACH OTHER, and both are flagged rather than
resolved silently:**

- the Reg SHO Rule 201 **effective date** — May 10, 2010 in the adopting release, "remains March 10,
  2010" in the extension release (BAR-2);
- the **Federal Register cite for the 13D/G release** — the SEC's own footnote 4 in 89 FR 4545 gives
  *88 FR 76986*, while the govinfo PDF's running head reads **76896**. **88 FR 76896 is correct; the
  SEC footnote is a typo.**

**Neither was fatal here. Both would have been, had a citation been trusted instead of opened.**

**No page encountered contained text addressed to me or instructing me to take an action.** Nothing
was downloaded except public regulatory and exchange documents; no account, credential or form was
touched.

---

## 1. WHAT WAS ALREADY KNOWN TO THE PROGRAMME

So the calendar's incremental content is visible. From the lane brief's own list:

| already on the record | my status |
|---|---|
| Rule 10b5-1 checkbox on Forms 4/5 from 2023-04-01 | **confirmed — and the RULE took effect 2023-02-27, five weeks earlier, so the checkbox misses trades the rule already governed.** Row ED-2 |
| Schedule 13D deadline 10 calendar days → 5 business days, 2024 | **confirmed, 2024-02-05 — but Schedule 13G's deadlines did NOT move until 2024-09-30.** Row ED-3 |
| EDGAR index form-type `SC 13D` → `SCHEDULE 13D`, ~2024-12-18 | **dated from EDGAR's own announcement (Release 24.4, 2024-12-16) — AND IT IS NOT A CUTOVER. The two strings coexist through 2024 Q1–Q3 and legacy `SC 13D/A` rows still appear in 2025 Q1, so a corrected filter must match BOTH throughout. Plus a second, undocumented break: the daily index truncated the new string to `SCHEDULE 1` for a year.** Rows ED-3a, ED-3b |
| T+1 settlement, May 2024 | **confirmed 2024-05-28 — but the mechanism the programme should care about is NOT the settlement cycle, it is the ex-date convention, and there is a SECOND such break in 2017.** Rows CA-2/CA-3 |
| EDGAR acceptance cut-off extended to 22:00 ET, 2024-02-05 | **confirmed — and it is FORM-SPECIFIC to Schedules 13D/13G (Reg S-T Rule 13(a)(2) → 13(a)(4)), not a general EDGAR change. Do not generalise it.** Row ED-3 |
| Rule 605 amendments, compliance 2026-08-01 | **confirmed, and it is an extension from 2025-12-14** — row T2-1 |
| tick-size / access-fee amendments delayed to first business day of November 2027 | **confirmed — and the stronger fact is that these amendments were PARTIALLY STAYED and have NEVER taken effect at any point in the window.** §6 |
| 8-K Item 5.02(e) folding equity-award grants into an existing item code, 2006 | **pre-window (2006) — not a row for 2010-01-04 onward.** Noted and excluded |

**Everything in §2 and §3 below is new to the record as far as the brief discloses**, and the three
highest-value rows — **odd-lot trades entering consolidated volume on 2013-12-09**, the
**three-regime ex-date convention**, and **the Tick Size Pilot's two-year nickel-quoting hole in
~1,200 small caps** — are not on the brief's list at all.

**Of the eight items the programme already held, six turned out to be imprecise in a way that changes
what a filter or a split should do** — the checkbox lags its rule by five weeks; 13G lags 13D by eight
months; the 22:00 cut-off is form-specific; T+1's real mechanism is the ex-date, not settlement; the
tick-size amendments are not merely delayed but were **stayed and never in force**; and the form-type
rename **is not a cutover, so the obvious fix to a broken filter is also wrong**.

> **NONE OF THE EIGHT WAS WRONG. SIX WERE TOO COARSE TO PRE-REGISTER AGAINST.** That is the pattern
> worth carrying out of this lane: the programme's accidental finds were all *true*, and all *round*.
> A break recorded as "in 2024" or "around 2024-12-18" is a note, not a pre-registration input — and
> the difference showed up as a wrong filter, a wrong split date, and a rule that never took effect.

---

## 2. TIER 1 — DAILY US EQUITY BARS

Rows that break a series the programme holds, each with a stated mechanism. **"Which date" is
labelled on every row.**

### BAR-1 · Single-stock circuit breakers, three stages, 2010–2011
**APPROVAL dates (operative dates not established — see §8.1).**

| stage | approval | coverage |
|---|---|---|
| 1 | **2010-06-10**, Rel. 34-62252, 75 FR 34186 (2010-06-16); FINRA: 34-62251 | S&P 500 stocks |
| 2 | **2010-09-10**, Rel. 34-62884, 75 FR 56618 (2010-09-16); FINRA: 34-62883 | + Russell 1000 and specified ETPs |
| 3 | **2011-06-23**, Rel. 34-64735, 76 FR 38243 (2011-06-29) | **+ all remaining NMS stocks** |

Source: the LULD approval order recites the chain with full citations —
`https://www.sec.gov/files/rules/sro/nms/2012/34-67091.pdf` [PRIMARY DATA DOC] [read in full for
this passage]. Verbatim: *"In the third stage, the Commission approved the Exchanges' and FINRA's
proposals to add all remaining NMS stocks … to the pilot."* The same passage states the pilot *"is
currently set to expire on July 31, 2012."*

**Mechanism.** A trading pause on a large move over a short window truncates the intraday extreme,
so **daily High and Low are censored** and a zero-volume gap appears intraday. **Stage 3 is the row
that reaches this programme's universe** — stages 1–2 cover large caps only. Before stage 3 a
small-cap name's daily range was uncensored; after, it is not.

> **I did not verify this pilot's trigger threshold or pause length from a primary document** — only
> that the three stages were approved on the dates above and that the pilot was *"set to expire on
> July 31, 2012"* before LULD replaced it. The widely-repeated "10% in five minutes, five-minute
> pause" I deliberately do **not** state as established here (§8.1). **The LULD parameters in BAR-4a
> ARE established; these are not.**

### BAR-2 · Reg SHO Rule 201 short-sale price test
**COMPLIANCE date: 2011-02-28.** Adopting release 34-61595 (2010-02-24). Extension release
**34-63247** moved compliance from 2010-11-10 to 2011-02-28.

- `https://www.sec.gov/files/rules/final/2010/34-61595.pdf` [PRIMARY DATA DOC] [read in full — header]
- `https://www.sec.gov/files/rules/final/2010/34-63247.pdf` [PRIMARY DATA DOC] [read in full]
  Verbatim: *"The compliance date for both Rules has been extended from November 10, 2010 to
  February 28, 2011."*

> **TWO PRIMARY SEC DOCUMENTS DISAGREE ON THE EFFECTIVE DATE.** 34-61595 states
> *"DATES: Effective Date: May 10, 2010"*. 34-63247 states *"The effective date for Rule 201 …
> **remains March 10, 2010**."* I cannot reconcile these and I am not guessing. **It does not matter
> for a data series: the date on which the rule began to bind behaviour is the COMPLIANCE date,
> 2011-02-28**, and that one is stated identically and unambiguously. This discrepancy is itself the
> lane's warning in miniature.

**Mechanism.** Once a stock falls 10% from the prior close, short sales are permitted only at a
price above the NBB for the rest of that day and the next. So **on and after 2011-02-28 the
downside tail of an intraday move in a name already down 10% is mechanically damped**, changing
daily Low and close-to-low conditional on a large decline. Dates only — short interest and borrow
remain an excluded territory.

### BAR-3 · LULD Phase I + market-wide circuit breakers, 2013-04-08
**OPERATIVE date: 2013-04-08.** Adopted 2012-05-31. **The originally announced date was
2013-02-04 and it was delayed.**

- LULD approval: Rel. **34-67091** (2012-05-31), 77 FR 33498 —
  `https://www.sec.gov/files/rules/sro/nms/2012/34-67091.pdf` [PRIMARY DATA DOC] [read in full]
- MWCB approval: Rel. **34-67090** (2012-05-31), 77 FR 33531 —
  `https://www.govinfo.gov/content/pkg/FR-2012-06-06/pdf/2012-13652.pdf` [PRIMARY DATA DOC]
  [read in full]. Verbatim: *"will be operative on a pilot basis, beginning February 4, 2013"* —
  i.e. **the Federal Register notice states the date that did not happen.**
- That the operative date became 2013-04-08: the LULD permanent-approval order states
  *"After two amendments, the initial date of Plan operations was April 8, 2013,"* citing Rel.
  34-68953 (2013-02-20), 78 FR 13113 —
  `https://www.sec.gov/files/rules/sro/nms/2019/34-85623.pdf` [PRIMARY DATA DOC] [read in full]
- Corroborating exchange notice for the superseded date: Nasdaq `ERA2012-7`, headline
  *"Limit Up-Limit Down Plan Approved by the SEC, Effective February 4, 2013"* [PRIMARY DATA DOC]
  [read in full]

**Mechanism, LULD.** Price bands around a rolling reference price. Verbatim from the approval order:
*"Trading for an NMS Stock would exit a Limit State if, within 15 seconds of entering the Limit
State, all Limit State Quotations were executed or canceled in their entirety. If the market did not
exit a Limit State within 15 seconds, then the Primary Listing Exchange would declare a **five-minute
trading pause**, which would be applicable to all markets trading the security."* The reference price
is *"the average price of eligible reported transactions for the NMS stock over the immediately
preceding five-minute period."* **Note the asymmetry with the MWCB: a LULD pause is FIVE minutes, a
market-wide circuit-breaker halt is FIFTEEN.** **Phase I applied only
to Tier 1 NMS Stocks** (S&P 500, Russell 1000, specified ETPs) and, per the approval order, bands
ran only from 15 minutes after the open to 30 minutes before the close, with no Limit State in the
final 25 minutes. **So 2013-04-08 does NOT touch most of this programme's universe** — BAR-4 does.

**Mechanism, MWCB.** From the same date, the market-wide breaker switched reference index and
thresholds: *"(i) Replace the DJIA with the S&P 500® Index … (ii) … the 10%, 20%, and 30% market
decline trigger percentages to 7%, 13%, and 20%"*, with the 3:25 p.m. cut-off. This is the regime
under which the 2020 halts occurred (BAR-9).

### BAR-4 · LULD Phase II — Tier 2, i.e. most of this universe — 2013-08-05 to 2014-05-12
**OPERATIVE: A NINE-MONTH STAGGERED ROLLOUT, not a single date.**

- Plan design, from the approval order: *"In Phase II, the Plan would fully apply to all NMS Stocks
  beginning at 9:30 a.m. and ending at 4:00 p.m. each trading day"*, commencing *"six months after
  the initial date of the Plan or such earlier date as may be announced by the Processors with at
  least 30 days' notice."* [PRIMARY DATA DOC] [read in full]
- Actual schedule, Nasdaq `ETU2013-25`, *"Limit Up/Limit Down Phase 2 Rollout Plan"*
  [PRIMARY DATA DOC] [read in full]. Verbatim: *"On Monday, August 5, 2013, NASDAQ OMX, in
  coordination with the other primary listing markets, will begin the first stage of the Phase 2
  rollout."* The notice gives the ramp explicitly: week 1 (Aug 5) = Tier 1 band-hours change + 50
  Tier 2 names; then ~10%, ~20%, ~30% of Tier 2; **week 5 (Sept 3) = remaining ~40%.**
  Scope: *"Phase 2 will include all Tier 2 NMS securities (except rights and warrants) that are not
  in Tier 1."*

**Mechanism.** This is the date LULD censoring arrives for ordinary small- and mid-cap single
names — **the bulk of a $5-floored 1,573-name universe**. Daily High/Low become band-censored and
pause-interrupted. **Because it is a ramp, a clean single-date split does not exist here.**

> **AND THE RAMP RUNS NINE MONTHS LONGER THAN THE ROLLOUT NOTICE SUGGESTS.** The SEC's own DERA
> white paper on Amendment 10 states, twice, that **LULD was not FULLY implemented until
> 2014-05-12** — `https://www.sec.gov/files/dera_wp_the_effect_of_amendment_10_of_the_luld_plan.pdf`
> [PRIMARY DATA DOC] [read in full]. Verbatim: *"from May 12, 2014 (when the LULD Plan was fully
> implemented)"*, and in its footnote, *"Data used in this White Paper is from May 12, 2014 (when
> LULD was fully implemented) to December 31, 2016. Note that there were 549 trading days from May
> 12, 2014 until Amendment 10 was implemented on July 18, 2016."* At the August 2013 stage bands ran
> 9:30–**3:45**, not to 4:00 p.m.; full coverage came with the later amendments.
>
> **So the conservative post-date for a pre-registered LULD split is 2014-05-12, not 2013-09-09 —
> and that is the SEC's own research division's choice of start date for exactly this reason.** The
> nine months in between are a partial-treatment period and should be excluded rather than assigned
> to either regime.

#### BAR-4a · The band widths, numerically — read out of the Plan's own Appendix A
Because "LULD censors the range" is not a mechanism until the width is stated. From Appendix A of the
Plan as approved, clause by clause [PRIMARY DATA DOC] [read in full]:

| Reference Price | Tier 1 (S&P 500 / Russell 1000 / listed ETPs) | **Tier 2 (everything else — this universe)** |
|---|---|---|
| **> $3.00** | **5%** | **10%** |
| $0.75 to $3.00 inclusive | 20% | **20%** |
| < $0.75 | lesser of $0.15 or 75% | lesser of $0.15 or 75% |

Plus two multipliers, verbatim: *"Between 9:30 a.m. and 9:45 a.m. ET, and 3:35 p.m. and 4:00 p.m. ET
… the Price Bands shall be calculated by applying **double** the Percentage Parameters"*; and *"If a
Reopening Price does not occur within ten minutes after the beginning of a Trading Pause, the Price
Band, for the first 30 seconds following the reopening … shall be calculated by applying **triple**
the Percentage Parameters."* The Reference Price is *"based on the closing price of the NMS Stock on
the Primary Listing Exchange on the previous trading day."*

**So for this programme's universe, concretely:** a held name is Tier 2 and, being floored at $5, is
always in the `> $3.00` bucket. Its band is **±10% of the prior close**, **±20% in the first fifteen
minutes and the last twenty-five** before 2020-02-24, and **±10% throughout** after it (BAR-9). **A
daily move beyond ±10% requires the reference price to have ratcheted during the session**, which is
a constraint on the intraday path, not merely a cap on the close — so the *shape* of the daily
return distribution's tail is affected, not only its extreme value.

> **A NOTE FOR LANE J4, WHICH IS RE-EXAMINING THE FLOOR'S LEVEL.** **The band width has a
> discontinuity at $3.00: 10% above it, 20% below it.** A $5 floor sits clear of that step. **A floor
> lowered to or below $3.00 would admit names whose LULD bands are twice as wide**, so the censoring
> mechanism — and anything estimated from the daily range, including a Corwin-Schultz spread — would
> not be homogeneous across the admitted set. That is a reason to prefer a floor above $3.00 which is
> **independent of the cost argument J4 is re-examining.** External evidence only; I make no claim
> about what the programme's data shows.

### BAR-5 · Odd-lot transactions enter the consolidated tape — 2013-12-09
**OPERATIVE: 2013-12-09.** Approval: Rel. **34-70794** (2013-10-31), Eighteenth Substantive
Amendment to the Second Restatement of the CTA Plan, File No. SR-CTA-2013-05.

- `https://www.sec.gov/files/rules/sro/nms/2013/34-70794.pdf` [PRIMARY DATA DOC] [read in full]
- Operative date, Nasdaq `ETU2013-33`, *"Odd Lot Reporting to the Consolidated Tape and Revised
  Sale Conditions"* [PRIMARY DATA DOC] [read in full]. Verbatim: *"On Monday, December 9, 2013 …
  will begin publishing Odd Lot executions to the UTP SIP and Consolidated Tape System (CTS)."*

**THIS IS THE SINGLE MOST DIRECTLY RELEVANT ROW IN THE CALENDAR AND IT WAS NOT ON THE BRIEF'S
LIST.** The approval order states the asymmetry exactly, verbatim:

> *"odd-lot transactions would not be included in calculations of high and low prices and would not
> be subject to the Limit Up-Limit Down Plan"* … *"However, odd-lot transactions would be included
> in calculations of daily consolidated volume."*

And the exchange notice: *"Odd Lot Trade transactions will be included in volume statistical
calculations only."*

**Mechanism — and note which fields move and which do not.** From 2013-12-09 **reported daily
share volume steps up** while **O/H/L/C do not change at all**. Before that date odd lots were
absent from the tape entirely. Consequences that follow mechanically:

- **A dollar-volume screen is not comparable across 2013-12-09.** The programme screens on dollar
  volume. The level of the screened quantity shifts upward on that date for reasons that have
  nothing to do with liquidity.
- **The shift is not uniform across names.** Odd lots are a larger share of trades in
  **higher-priced** stocks (a 100-share round lot is a larger ticket), so the step is
  price-dependent — which is the axis `CLAUDE.md` says cost scales on, and the axis that killed
  D284.
- Any volume-normalised quantity (turnover, Amihud-style illiquidity, volume z-scores) inherits the
  break. Any *price*-derived quantity — including a Corwin-Schultz spread estimate off OHLC — does
  **not**, because odd lots never touched high/low.
- The same notice introduced a *"Corrected Consolidated Close"* modifier usable only by the listing
  market, which **"will be eligible to set the High, Low and Last for the consolidated statistics"**
  with volume always reported as zero. That is a second, smaller change to how consolidated
  H/L/Last can be revised, from the same date.

### BAR-6 · LULD Amendment No. 10 — reference prices on quote-opens — 2016-07-18
**IMPLEMENTED 2016-07-18.** APPROVED 2016-04-21, Rel. 34-77679, 81 FR 24908 (2016-04-27).

- LULD permanent-approval order 34-85623 [PRIMARY DATA DOC] [read in full]. Verbatim:
  *"Amendment No. 10 changed the manner in which Reference Prices were determined in situations where
  a security opened for trading on a quote rather than a trade."* The order records that
  *"the number of Trading Pauses dropped significantly"* afterwards.
- Implementation date and the mechanism in full: SEC DERA white paper
  `https://www.sec.gov/files/dera_wp_the_effect_of_amendment_10_of_the_luld_plan.pdf`
  [PRIMARY DATA DOC] [read in full]. Verbatim: *"Amendment 10, which was implemented on July 18,
  2016, addresses this issue by setting a security's Reference Price to the Primary Listing
  Exchange's previous day's closing price when there is no opening transaction."* And:
  *"The implementation of Amendment 10 was associated with a dramatic decrease in the number of"*
  trading pauses.

**Mechanism, and the bug it fixed.** The DERA paper sets out the defect with a worked example: before
Amendment 10, a security that opened on a quote rather than a trade took its Reference Price from the
**midpoint of the opening quote**, so a wide opening spread could place the bands far from the
previous close — and *"The Trading Pause occurs even though the offer … is identical to the price at
which the security closed at the end of the previous trading day."* After 2016-07-18 the Reference
Price falls back to the prior close.

**Consequence.** A *level shift in the rate of trading pauses*, concentrated in **names that open on
a quote rather than a trade — i.e. thinly traded names, which is where a $5-floored small-cap
universe lives.** Any study counting halts, or using "was this name halted/paused" as a conditioner,
has a regime change at 2016-07-18. **And pre-2016-07-18 pauses are partly an artefact of wide opening
spreads rather than of price moves** — so a pause count is not a clean volatility proxy before that
date.

### BAR-7 · Tick Size Pilot — ~1,200 names quoted in nickels — 2016-10-03 to 2018-09-28
**This is not a split. It is a two-year HOLE in the middle of the window, and it applies to a
subset of names selected on criteria that overlap this programme's universe almost exactly.**

| date | what | source |
|---|---|---|
| **2015-05-06** | APPROVED, two-year pilot, Rel. **34-74892**, File 4-657 | `https://www.sec.gov/files/rules/sro/nms/2015/34-74892.pdf` [PRIMARY DATA DOC] [read in full] |
| 2015-11-13 | implementation ORDER moving start from 2016-05-06 to 2016-10-03 | recited in the 2018 exemption letter, below |
| **2016-10-03 → 2016-10-31** | PHASED ROLLOUT of pilot securities (exemption of 2016-09-13) | 2018 exemption letter [PRIMARY DATA DOC] [read in full] |
| **2018-09-28** | quoting/trading requirements TERMINATED at the close — one trading day early, instead of 2018-10-02 | `https://www.sec.gov/divisions/marketreg/mr-noaction/2018/tick-size-pilot-exemption-091018-608e.pdf` [PRIMARY DATA DOC] [read in full] |

Exemption letter, verbatim: *"end of trading on Friday, September 28, 2018, instead of at the end of
trading on Tuesday, October 2, 2018"* and *"a phased rollout of Pilot Securities starting on
October 3, 2016 and ending on October 31, 2016."* Corroborated by the SEC's own TM/DERA statement,
*"The Tick Size Pilot commenced operation on Oct. 3, 2016"*
(`https://www.sec.gov/newsroom/speeches-statements/tm-dera-statement-expiration-tick-size-pilot`)
[PRIMARY DATA DOC] [read in full].

**Selection criteria, read out of the approval order** [read in full for this passage] — market
capitalisation **$3 billion or less** (lowered by the Commission from the proposed $5bn); closing
price **≥ $2.00** on the last day of the measurement period; closing price **never below $1.50**
during it; consolidated ADV **≤ 1,000,000 shares**; measurement-period VWAP **≥ $2.00**; no IPO
within 6 months. Structure: **three Test Groups of 400 securities each**, plus a Control Group.

**Mechanism.** Test Group One quoted in **$0.05** increments; Groups Two and Three quoted *and
traded* in $0.05; Group Three additionally bore a Trade-At prohibition.

**Why this row matters more here than anywhere else in the calendar.** A universe floored at $5
as-traded with a dollar-volume screen, ~1,573 US single names, is **substantially the pilot's
eligible population** — small cap, priced above $2, under a million shares a day. For ~1,200 of
those names, for two years in the middle of the sample:

- the **minimum quoted increment was 5× wider**, so any spread estimate — including
  **Corwin-Schultz off the OHLC**, which `CLAUDE.md` mandates for held names — is measuring a
  different object in 2016-10 to 2018-09 than on either side of it;
- closing prices are quantised differently for Groups Two and Three, which traded in nickels;
- **breakeven cost in bp/side is not comparable across the pilot boundary** for an affected name.

**Three practical consequences.** (i) The affected set is a *published list*, name by name and
group by group, so this is testable rather than merely feared. (ii) The entry is a **phased rollout
over four weeks**, not a date. (iii) A study spanning 2016–2018 that reports one cost assumption
across the whole span is mixing two quoting regimes in the names most likely to be held.

### BAR-8 · LULD Amendments 12 and 13 + coordinated reopening auctions — 2017-11-20
**IMPLEMENTED 2017-11-20.** Approved 2017-01-19 (Rel. 34-79845) and 2017-04-13 (Rel. 34-80455).

Source: 34-85623 [PRIMARY DATA DOC] [read in full]. Verbatim: *"the implementation of Amendment
Nos. 12 and 13 in November 2017 modified the operation of the Plan to address issues that were
uncovered by market events on August 24, 2015"* and *"implemented these changes to their automated
reopenings on November 20, 2017."*

**Mechanism.** The price at which a paused security *reopens* is set by the primary listing
exchange's auction, and that auction's mechanics changed on this date across all primary listing
exchanges simultaneously. **Any quantity that depends on the post-pause print** — a gap, a
reopening return, a 15-minute bar containing a reopen — has a regime change.

> **AND 2015-08-24 SHOULD BE EXCLUDED OUTRIGHT, ON THE SEC'S OWN PRECEDENT.** That day's behaviour is
> what these amendments were built to fix, so it is representative of neither regime. The DERA white
> paper does exactly this, verbatim: *"Note that data from August 24, 2015 is excluded from Table 1
> and all other tables and presentations in this White Paper."* [PRIMARY DATA DOC] [read in full].
> **A primary SEC research document dropping a single date from every table is about as strong a
> precedent for excluding it as external evidence gets.**

### BAR-9 · LULD double-wide bands eliminated — 2020-02-24 — FOURTEEN TRADING DAYS BEFORE THE COVID HALTS
**ACTIVATION: 2020-02-24.** Plan amendment APPROVED **2019-04-11** (Rel. 34-85623, 84 FR 16086);
proposal filed 2018-11-05 (Rel. 34-84843, 83 FR 66464).

- Approval order [PRIMARY DATA DOC] [read in full]: the Eighteenth Amendment *"(iii) eliminate the
  doubling of the Percentage Parameters between 9:30 a.m. and 9:45 a.m.; and (iv) eliminate the
  doubling of the Percentage Parameters between 3:35 p.m. and 4:00 p.m. … for Tier 2 NMS Stocks
  with a Reference Price above $3.00."* **The order does not state an activation date.**
- Activation date from the exchange notice: Nasdaq `UTP2019-09`, *"LULD Plan Amendment 18
  (Elimination of Double-Wide Bands)"* [PRIMARY DATA DOC] [read in full]. Verbatim:
  *"Activation Date: Monday, February 24, 2020."*

**Mechanism, and the confound.** Price bands at the open and (for Tier 2 above $3.00) at the close
were **halved in width** on 2020-02-24 — **for a held name, from ±20% to ±10% in 09:30–09:45 and
15:35–16:00** (BAR-4a). Narrower bands → **more Limit States and more Trading Pauses at the open and
into the close**, in exactly the Tier 2 names this programme holds. The same
approval order explicitly anticipated this, asking for analysis of *"whether any increased Trading
Pauses and Limit States negatively impacted closing auctions in affected securities."*

> **This is a trap with the programme's name on it.** The first market-wide halt of the COVID period
> was **2020-03-09 — fourteen trading days later.** Any study that treats the March 2020 halt and
> pause counts as a pure volatility response is confounded by a band-width change that landed three
> weeks earlier. **The two effects are not separable inside 2020 with this fixture; they are
> separable only by comparing band behaviour in 2020-02-24→2020-03-06 against earlier quiet
> periods.**

### BAR-10 · The 2020 market-wide halts as a dated cluster — four Level 1 halts
**DATES: 2020-03-09, 2020-03-12, 2020-03-16, 2020-03-18.**

Source: NYSE rule filing Rel. **34-92428** (2021-07-16), File SR-NYSE-2021-40, published by the SEC
— `https://www.sec.gov/files/rules/sro/nyse/2021/34-92428.pdf` [PRIMARY DATA DOC] [read in full for
this passage]. Verbatim: *"culminating in four MWCB Level 1 halts on March 9, 12, 16, and 18,
2020."* The same filing sets out the MWCB thresholds then in force (7% / 13% / 20% of SPX from the
prior close; Level 1 and 2 halt for 15 minutes before 3:25 p.m. and not at all at or after 3:25
p.m.; Level 3 ends the day) and confirms the pilot rules ran under annual extensions to
2019-10-18, 2020-10-18 and 2021-10-18.

**The MWCB rules were made PERMANENT on 2022-03-16**, Rel. **34-94441**, File SR-NYSE-2021-40 —
`https://www.sec.gov/files/rules/sro/nyse/2022/34-94441.pdf` [PRIMARY DATA DOC] [read in full —
header]. Title: *"Notice of Filing of Amendment No. 1 and Order Granting Accelerated Approval of a
Proposed Rule Change, as Modified by Amendment No. 1 to Adopt on a Permanent Basis the Pilot Program
for Market-Wide Circuit Breakers in Rule 7.12."* **Pilot → permanent is not itself a break: the
thresholds and durations are unchanged from 2013-04-08.** It is recorded so the row is not mistaken
for one.

**Mechanism.** On each of these four days **every** name in the panel has a 15-minute hole in its
session. Volume is displaced rather than lost; the intraday path is interrupted market-wide. For a
15-minute intraday fixture these are four dates on which one bar per name is structurally unlike
every other bar in the sample. Combine with BAR-9: these four days sit **inside** the new
narrow-band regime.

### BAR-11 · Rule 15c2-11 — the OTC quote shut-off — 2021-09-28
**COMPLIANCE: 2021-09-28** (nine months after effective). ADOPTED 2020-09-16; **EFFECTIVE
2020-12-28**; a separate paragraph (b)(5)(i)(M) had a two-year compliance date (2022-12-28).

Source: the adopting release as published at 85 FR, read via
`https://www.govinfo.gov/content/pkg/FR-2020-10-27/html/2020-20980.htm` [PRIMARY DATA DOC]
[read in full for the DATES and Part II.P sections]. Verbatim: *"Effective date: December 28,
2020"*; and Part II.P: *"The Commission is providing a compliance date that is nine months after
the effective date of the amended Rule, except for … paragraph (b)(5)(i)(M) … two years after the
effective date."* The release itself uses **September 28, 2021** as that date elsewhere in its text.

**Mechanism.** From 2021-09-28 a broker-dealer may not publish quotations for a security whose
issuer information is not current and publicly available. Hundreds of OTC issuers lost public
quotations. **This touches the programme only through its dead tail** — names that left an exchange
and continued to print on OTC. After this date, **"the quotes stopped" stops being evidence that
trading stopped**; it can instead be evidence that the issuer was not current. Any delisting- or
death-related series that reads the end of a quote stream as an event date changes meaning here.
Dates only; the death process itself is an excluded territory.

### BAR-12 · THE TRADING CALENDAR — four missing bars, and one new one every year from 2022
**These are not rule changes that alter a bar. They are dates on which the bar does not exist.** A
panel built by forward-filling, or one whose bar count is assumed uniform across years, is wrong at
each of them. All four are verified from **primary exchange notices**, not news reports.

| date | day | cause | primary source |
|---|---|---|---|
| **2012-10-29** | Monday | Hurricane Sandy | Nasdaq `ETA2012-44` (dated Sunday 2012-10-28): *"NASDAQ OMX will close all U.S. equity and derivatives exchanges, as well as the NASDAQ/FINRA TRF on Monday, October 29th, due to Hurricane Sandy."* |
| **2012-10-30** | Tuesday | Hurricane Sandy | Nasdaq `ETA2012-45` (dated Monday 2012-10-29): *"…will close all U.S. equity and derivatives exchanges … on Tuesday, October 30th, due to Hurricane Sandy."* Same notice: *"expects its markets to be open as normal on Wednesday, October 31st"* |
| **2018-12-05** | Wednesday | day of mourning, George H. W. Bush | Nasdaq `ETA2018-98`: *"Nasdaq U.S. equities and options markets will be closed on Wednesday, December 5, 2018, in observance of the passing of President George H.W. Bush."* |
| **2025-01-09** | **Thursday** | day of mourning, Jimmy Carter | Nasdaq `ETA2025-1`: *"Thursday, January 9, 2025 is not a valid trade date."* |

All [PRIMARY DATA DOC] [read in full]. **Sandy closed the market on two CONSECUTIVE days** — the
only such pair in the window. Sandy is additionally confirmed from the SEC side by NYSE rule filing
Rel. **34-68137**, File SR-NYSE-2012-58 (77 FR 66894): *"On October 29 and 30, 2012 … all U.S.
equities and options markets were closed"*, and for the reopening, *"On October 31, 2012 … the
Exchange, using back-up generators, was able to open trading at its physical location."* Both days of
mourning are corroborated by Executive Orders **13852** (83 FR 62687) and **14133** (90 FR 187), each
closing federal agencies on the same date.

**THE 2018 CLOSURE MOVED EX-DATES TOO — it is not only the 2025 one.** Nasdaq `ETA2018-99`
[PRIMARY DATA DOC] [read in full]: *"Although Wednesday, December 5, 2018 is not a valid trade date,
it will be considered a valid settlement date"*, and it shifted ex-dividend dates off 12-05 onto
**2018-12-06**. **So both mourning days displace ex-dates onto the following session.**

#### BAR-12b · HOW COMPLETE THAT LIST IS, AND WHY THAT MATTERS MORE THAN THE ROWS
**The claim is "exactly four unscheduled full-day closures in the window", and it is bounded rather
than asserted.** Two independent sweeps:

1. **Every Nasdaq Equity Trader Alert from 2010 through 2026** was enumerated by id until each year
   404'd — roughly **2,400 alert titles** — and filtered for closure language. It returns **only**
   these four dates. The method demonstrably detects the events it is meant to detect: it surfaced
   Sandy and the Carter closure independently, before they were looked for.
2. **A Federal Register full-text search of all SEC documents 2010-01-01 → 2026-08-26** for
   `"markets were closed"` returns 8 hits, of which the only market-closure references are the two
   November 2012 Sandy filings plus 2013 options filings citing that same closure.

**TWO NEGATIVES THAT CATCH PEOPLE, both from primary notices:**

- **Winter Storm Stella did NOT close the market.** Nasdaq `ETA2017-51`: *"Winter Storm Stella:
  Nasdaq to Maintain Normal Market Hours for March 14-15, 2017."* [PRIMARY DATA DOC] [read in full]
- **A FEDERAL CLOSURE IS NOT A MARKET CLOSURE.** Executive Orders closed federal agencies on
  **2018-12-24** and **2024-12-24**; both were **normal (early-close) trading days**. **Do not derive
  a market holiday calendar from the federal one** — it will delete two real bars.

#### BAR-12c · AND THIS ARITHMETIC IS A DIRECT, FALSIFIABLE CHECK ON THE FIXTURE
Counting from the verified NYSE Rule 7.2 holiday set, with Juneteenth added from 2022 and New Year's
**not** observed when 1 January falls on a Saturday:

| quantity | count |
|---|---|
| weekdays in 2010-01-04 → 2026-08-26 | **4,343** |
| standard weekday holidays | **152** |
| **actual trading sessions** | **4,187** |
| **if the four unscheduled-closure dates are present as rows** | **4,191** |

> **THE PROGRAMME'S STATED BAR COUNT IS ~4,190. THAT SITS ON 4,191, NOT ON 4,187.** I hold no
> fixture and assert nothing about what is in it — **this is a prediction, not a finding.** But it is
> a cheap and decisive one: **check whether 2012-10-29, 2012-10-30, 2018-12-05 and 2025-01-09 exist
> as rows in the panel.** If they do, they are carried-forward or zero-volume fabrications, because
> **no trade occurred anywhere in the US equity market on any of those four days.**
>
> This is the lane's most actionable single line, and it is checkable today with no new data. If the
> four rows are present, then every bar-indexed window in the programme's history has been four days
> long in places where it should have been zero — and `docs/FINDINGS.md`'s block-length work is
> keyed to bar counts.

> **A SUMMARISER GOT THE SANDY REOPENING WRONG AND THE PRIMARY CAUGHT IT.** A search summary told me
> the market reopened on **November 1st**; the exchange's own notice says **Wednesday, October 31st**,
> which is also the correct weekday. **Had I taken the summary, this row would have asserted one
> missing bar too many.** This is the lane brief's summariser rule earning its keep on a date.

**AND 2025-01-09 IS NOT ONLY A MISSING BAR — IT DOUBLES THE NEXT DAY'S EX-DATES.** From the same
Nasdaq notice, verbatim:

> *"As a result of the market closure on Thursday, January 9, 2025 all stocks which would normally
> have been ex-dividend on Thursday, January 9, 2025 (with a record date of Thursday, January 9,
> 2025), shall be ex-dividend on Friday, January 10, 2025. All stocks with a record date of Friday,
> January 10, 2025, will be ex-dividend on January 10, 2025."*

**So two cohorts of ex-dates pile onto 2025-01-10**: those with record date Jan 9 and those with
record date Jan 10. **This happens precisely BECAUSE the T+1 convention sets ex-date = record date
(CA-3)** — under the pre-2024 conventions the collision would have fallen differently. The same notice
also records that **Jan 9 remained a valid SETTLEMENT date** though not a valid trade date: *"all
trades executed on Wednesday, January 8, 2025 will settle in the usual manner on Thursday, January 9,
2025."* **A doubled ex-date day is a one-line check on the corporate-actions feed.**

#### BAR-12a · Juneteenth — one fewer bar per year from 2022
**RULE CHANGE: 2021-09-30**, Rel. **34-93183**, File SR-NYSE-2021-56, **operative on filing** (the
Commission waived the 30-day operative delay). **FIRST ACTUAL CLOSURE: 2022-06-20.**

`https://www.sec.gov/files/rules/sro/nyse/2021/34-93183.pdf` [PRIMARY DATA DOC] [read in full].
Verbatim: *"The Exchange proposes to amend NYSE Rule 7.2 (Holidays) to make Juneteenth National
Independence Day a holiday of the Exchange … As a result, the Exchange will not be open for business
on Juneteenth National Independence Day, which falls on June 19 of each year."* And the observance
rule, **stated in the filing rather than inferred by me**: *"when the holiday falls on a Saturday, the
Exchange will not be open for business on the preceding Friday, and when it falls on a Sunday, the
Exchange will not be open for business on the succeeding Monday."*

**June 19, 2022 fell on a Sunday, so the first closure was Monday 2022-06-20** — which follows from
the rule as quoted, not from a guess, **and is confirmed outright** by Nasdaq `ETA2022-55`
[PRIMARY DATA DOC] [read in full]: *"Nasdaq U.S. equities and options markets will be closed on
Monday, June 20, 2022, in observance of the Juneteenth Holiday."*

> **AND THE TRAP: 2021 WAS EXPLICITLY OPEN, EVEN THOUGH THE FEDERAL OBSERVANCE WAS 2021-06-18.**
> Nasdaq `ETA2021-45`, dated 2021-06-17 [PRIMARY DATA DOC] [read in full]: *"All U.S. markets operated
> by Nasdaq will remain open on Friday, June 18, 2021 and Monday, June 21, 2021."* **A calendar that
> derives market holidays from federal ones deletes a real bar on 2021-06-18.**

Parallel filings followed from every other equities exchange (NYSE American/Arca/Chicago/National
2021-10-05; IEX 2021-11-18; Nasdaq 2021-12-03, Rel. 34-93675; MEMX 2021-12-08; LTSE 2021-12-07; Cboe
BZX/BYX/EDGX/EDGA 2021-12-22/23). Observances since: 2023-06-19 (Mon), 2024-06-19 (Wed), 2025-06-19
(Thu), 2026-06-19 (Fri) — **all five inside the window**.

**From 2022 the panel has one fewer trading day per year than 2010–2021 did.** Small in magnitude, but it means **annual bar counts are not constant across the
window**, which matters for any per-year normalisation, any block-bootstrap block length expressed in
bars, and any "bars per year" constant hard-coded in a runner. Note the holiday did **not** apply in
2021: the federal designation was 2021-06-17, two days before that year's June 19, and the NYSE rule
change came in September.

### BAR-13 · THE NYSE TRADING FLOOR CLOSES — 2020-03-23 — AND TAPE A CLOSING PRICES CHANGE PROCESS
**This is the row that touches the closing price itself, which is the field the programme trades on.**

| date | event |
|---|---|
| 2020-03-18 | CEO determination under NYSE Rule 7.1(c)(3) |
| **2020-03-23** | **floor closes; NYSE goes fully electronic** |
| **2020-05-26** | phase 1 partial reopening — **a subset of Floor brokers only** |
| **2020-06-17** | phase 2 — **DMMs return**, barred from accepting verbal bids/offers from Floor brokers |
| full reopening | **NOT ESTABLISHED** (§8.14) |

Source: Rel. **34-89086**, File SR-NYSE-2020-52 (85 FR 37746),
`https://www.sec.gov/files/rules/sro/nyse/2020/34-89086.pdf` [PRIMARY DATA DOC] [snippet only —
Background section]. Verbatim: *"On March 18, 2020, the CEO of the Exchange made a determination
under Rule 7.1(c)(3) that, beginning March 23, 2020, the Trading Floor facilities … would close and
the Exchange would move, on a temporary basis, to fully electronic trading"*; *"On May 14, 2020, the
CEO … made a determination … to reopen the Trading Floor on a limited basis on May 26, 2020 to a
subset of Floor brokers"*; *"On June 15, 2020, the CEO … to begin the second phase … by allowing
DMMs to return to on June 17, 2020."*

**MECHANISM — what actually changed about the official close.** Rel. **34-88444**, File
SR-NYSE-2020-22 (2020-03-20) [PRIMARY DATA DOC] [snippet only], whose own section heading reads
*"NYSE Trading Floor Temporarily Closes March 23, 2020"*, amended Rules 7.35A/7.35B/7.35C for a
temporary period beginning 2020-03-23 to:

- **suspend** the price and volume parameters restricting a DMM from effecting a Core Open, Trading
  Halt or Closing Auction **electronically**;
- **widen to 10%** the percentage price parameters for electronic DMM auctions;
- **suspend** the requirement to publish pre-opening indications;
- set Auction Collars for Exchange-facilitated Trading Halt Auctions after a Level 1/2 MWCB halt.

The filing states the replacement plainly: *"Because DMMs would not be physically present on the
Trading Floor, DMMs would facilitate Auctions electronically as provided for in Rules 7.35A and
7.35B"*, and *"If a DMM does not facilitate an Auction electronically … the Exchange would facilitate
the Auction pursuant to Rule 7.35C."*

> **SO FOR NYSE-LISTED (TAPE A) NAMES FROM 2020-03-23, THE OFFICIAL CLOSE STOPPED BEING A MANUAL DMM
> AUCTION** incorporating orally-represented Floor Broker interest, and became either a DMM
> **electronic** auction with parameters suspended and collars widened to 10%, or an
> **Exchange-facilitated** Rule 7.35C auction — which, unlike a DMM auction, **is** subject to
> Auction Collars (the greater of 10% or $0.15 from the Auction Reference Price). **Closing prices in
> this period are not drawn from the same generating process as before or after, and the 10% collar
> is a hard truncation on the close for names that gapped.**
>
> **This lands inside the COVID cluster and is the third confound stacked on it** — after the LULD
> band halving (BAR-9, 2020-02-24) and the four MWCB halts (BAR-10). **Anyone reading March–June
> 2020 closing prices as a pure volatility episode is reading three rule changes and one shock at
> once, and only the shock is usually named.** Note also that it is **Tape A only** — Nasdaq-listed
> names are unaffected, so the period contains a **listing-venue asymmetry** that does not exist on
> either side of it.

### BAR-14 · VENUE RENAMES AND CLOSURES — the vendor's exchange-code field, not the price
**None of these changes a single price. Each changes the STRING in a vendor's exchange-code or
primary-listing field**, and a panel that groups or filters on listing venue gets a spurious cohort
break at each.

| change | rule filing (hard date) | operative |
|---|---|---|
| **NYSE Amex → NYSE MKT LLC** | Rel. 34-67037, SR-NYSEAmex-2012-32, **2012-05-21** | bracketed **2012-05-21 → 2012-06-11** |
| **NYSE MKT → NYSE American LLC** | Rel. 34-80283, SR-NYSEMKT-2017-14, **2017-03-21** | filing says "no later than June 30, 2017" — **it slipped**; bracketed to **2017-08-02** |
| **CHX → NYSE Chicago** | Rel. 34-84517, SR-CHX-2018-04 (83 FR 55773) | **pushed into 2019** by Rel. 34-85034; bracketed **2019-02-01 → 2019-03-01** |
| **NYSE Chicago → NYSE Texas** | Rel. 34-102507, SR-NYSECHX-2025-01, **2025-02-28** | bracketed **2025-02-28 → 2025-04-08** |
| **Nasdaq BX → Nasdaq Texas, LLC** | Rel. 34-104739, SR-BX-2026-006, **2026-01-29** | bracketed **2026-01-29 → 2026-03-12** |
| **Bats BZX/BYX/EDGX/EDGA → Cboe** | Rel. 34-81962, SR-BatsBZX-2017-70, **2017-10-26** | bracketed **2017-10-26 → 2017-11-01** |
| **National Stock Exchange ceases trading** | Rel. 34-72124, SR-NSX-2014-14 | **HARD DATE 2014-05-30** — *"as of the close of business on May 30, 2014, NSX shall cease trading activity on the System"* |

All [PRIMARY DATA DOC] [snippet only].

> **WHY ONLY ONE OF THESE HAS A HARD DATE, AND WHY THAT IS THE POINT.** A rename becomes operative on
> a **state filing** — a Delaware or Texas Secretary of State certificate — **which the SRO filing does
> not date.** The NYSE MKT → NYSE American filing says the change was *"expected to be no later than
> June 30, 2017"* and **it slipped by over a month**. So the brackets above are the honest answer, and
> the operative dates are bounded, not known.
>
> **And a vendor relabels on its OWN reference-data refresh, not on the legal date anyway** — so even
> a hard legal date would not tell the programme when its field changed. **The right treatment is to
> check the fixture for when the string changed, not to assume any of these dates.**

**The consequential one for this universe is the NYSE Amex → MKT → American chain**, which relabels
the entire small-cap NYSE-listed cohort **twice** inside the window (2012 and 2017), and **Nasdaq BX →
Nasdaq Texas** in early 2026.

### BAR-15 · TRADING HOURS NEVER CHANGED, AND NO OVERNIGHT SESSION SET A CLOSING PRICE
**A negative row, established rather than assumed, because it is the row people expect to exist.**

- The core session never moved: NYSE's live hours page gives *"Core Trading Session: 9:30 a.m. to
  4:00 p.m. ET … 4:00 p.m. ET - Closing Auction"*; Nasdaq's own system-hours document gives
  *"Market hours: 9:30 a.m. – 4:00 p.m."* Both [PRIMARY DATA DOC] [read in full]. Scheduled early
  closes remain 1:00 p.m. throughout.
- **NYSE Arca's 22-hour extension was APPROVED but GATED and never commenced in the window.** Rel.
  **34-102400**, SR-NYSEARCA-2024-89 (2025-02-11) [PRIMARY DATA DOC] [snippet only]: *"the Exchange
  will not commence operation of Extended Hours Trading … unless the Equity Data Plans: (1) have
  established a mechanism to collect, consolidate, process, and disseminate quotation and transaction
  information at all times."*
- **The SIPs do not open overnight until 2026-12-06** — LULD Plan Amendment No. 27 approval
  (91 FR, 2026-08-10) [PRIMARY DATA DOC] [snippet only]: *"Overnight Protections are expected to
  commence on December 6, 2026."*
- **24X's overnight session is exempted only from 2027-01-24.**

**And the mechanical reason it could not have mattered even if it had run**, from the Arca order:
*"Trades executed and reported outside of the Core Trading Session will be reported to the
appropriate exclusive SIP with the '.T' modifier."* **`.T`-modified trades are not last-sale
eligible, so they cannot set an official closing price.** Both dates fall outside the window in any
case.

---

## 3. TIER 1 — CORPORATE ACTIONS

### CA-1 · FINRA Rule 6490, notification of company-related actions — 2010-09-27
**EFFECTIVE: 2010-09-27.** FINRA Regulatory Notice 10-38 —
`https://www.finra.org/rules-guidance/notices/10-38` [PRIMARY DATA DOC] [read in full]. Verbatim:
*"Effective Date: September 27, 2010"* and *"Effective September 27, 2010, new FINRA Rule 6490
(Processing of Company-Related Actions) codifies the requirements in SEA Rule 10b-17 for issuers …
to provide timely notice to FINRA of certain corporate actions."*

**Mechanism.** For **non-exchange-listed** equity, issuers must notify FINRA at least 10 days before
the record date of a dividend, split, reverse split or rights offering, and FINRA may **refuse to
process** a deficient action. So from this date the *completeness and timeliness* of OTC corporate
actions improves, and some actions are **blocked** rather than merely late.

**Relevance: tier-1 by data class, tier-2 by magnitude** — it binds only off-exchange names, i.e.
the programme's dead tail again, not its live universe.

### CA-2 and CA-3 · THE EX-DATE CONVENTION: THREE REGIMES, NOT ONE BREAK
**This is the corporate-actions row the programme does not have, and the T+1 entry on its record is
only the last third of it.** The SEC settlement-cycle releases **do not set ex-dates at all** — I
checked, and neither 34-80295 (T+2) nor 34-96930 (T+1) contains a single occurrence of "ex-date",
"ex-dividend" or "record date" in a rule-setting sense. The ex-date convention lives in **FINRA
Rule 11140 and the exchanges' Uniform Practice Codes**, changed by separate SRO filings.

| regime | ex-date relative to record date | from | to |
|---|---|---|---|
| T+3 | **second** business day preceding the record date | window start | 2017-09-01 |
| T+2 | **first** business day preceding the record date | **2017-09-05** | 2024-05-24 |
| T+1 | **the record date itself** | **2024-05-28** | window end |

**CA-2 — T+2, OPERATIVE 2017-09-05.** Settlement-cycle compliance date from Rel. **34-80295**
(2017-03-22) [PRIMARY DATA DOC] [read in full — header]: *"DATES: Effective date: May 30, 2017.
Compliance date: September 5, 2017."* The ex-date mechanics from Rel. **34-81446** (Nasdaq, 2017),
`https://www.sec.gov/files/rules/sro/nasdaq/2017/34-81446.pdf` [PRIMARY DATA DOC] [read in full];
the parallel FINRA filing is SR-FINRA-2017-026. That document states the **old** rule verbatim —
ex-date *"shall be the second business day preceding the record date if the record date falls on a
business day, or the third business day preceding the record date"* otherwise — and that under T+2
*"the ex-dividend date"* moves in by one business day.

> **AND A ONE-DAY HOLE, STATED IN THE RULE FILING ITSELF.** Verbatim: *"no securities will be
> ex-dividend on September 5, 2017."* The reason given: the T+3→T+2 transition made 2017-09-07 a
> *"double" settlement date*, so the SROs interpreted Rule 11140 such that *"the first record date to
> which this new ex-dividend date rationale will be applied will be Thursday, September 7, 2017."*
> **A corporate-actions feed should therefore show ZERO ex-dates on 2017-09-05. That is a
> one-line, falsifiable check on the feed — and if it shows any, the feed is not point-in-time
> correct.**

**CA-3 — T+1, OPERATIVE 2024-05-28.** Settlement compliance from Rel. **34-96930** (2023-02-15)
[PRIMARY DATA DOC] [read in full — header and Part VII]: *"DATES: Effective date: May 5, 2023"*,
with *"the compliance date of May 28, 2024."* Ex-date mechanics from Rel. **34-99075** (2023-12-04),
File SR-FINRA-2023-017, `https://www.sec.gov/files/rules/sro/finra/2023/34-99075.pdf`
[PRIMARY DATA DOC] [read in full]. Verbatim: *"the date designated as the 'ex-dividend date' would
be the record date if the record date falls on a business day"*, and *"The operative date of the
proposed rule change will be May 28, 2024."*

**Mechanism, and why it is not cosmetic.** The **ex-date-to-record-date offset collapses from 2
business days to 1 to 0.** Anything that joins a corporate action to a bar by *record* date, or that
assumes a fixed offset between the two, silently misaligns by one trading day at 2017-09-05 and by
another at 2024-05-28. A dividend-drop test, a split-adjustment check, a sign audit on "a dividend
moves long and short oppositely" — all of them key on which bar carries the drop. **`CLAUDE.md`
requires that dividend sign audit in every runner; its correctness depends on the regime.**

**Regime value.** **CA-2 at 2017-09-05 is the cleanest usable split in the entire window**: ~7.7
years before, ~9.0 years after. CA-3 at 2024-05-28 **clips the tail** (~2.2 years after) and cannot
support a two-regime test on its own.

### CA-4 · LISTING STANDARDS — THE RULES GOVERNING REVERSE SPLITS AND DELISTINGS CHANGED FIVE TIMES
**A reverse split IS a corporate action, and the rate at which they occur is set by exchange listing
rules — which tightened repeatedly inside this window.** For a universe that is **35.7% dead** and
**floored at $5**, this is the row that governs how names leave.

| date | type | rule | mechanism |
|---|---|---|---|
| **2020-04-21** | APPROVED + **operative stated** | Nasdaq, Rel. **34-88716**, SR-NASDAQ-2020-001 | closing bid **≤ $0.10 for 10 consecutive days → mandatory Staff Delisting Determination**; and **cumulative reverse splits of 1-for-250 or more over the prior two years → NO compliance period at all** |
| **2023-11-01** | APPROVED | Nasdaq, Rel. **34-98843**, SR-NASDAQ-2023-025 | advance MarketWatch notice + Reg FD disclosure required **before** a reverse split; Nasdaq may **halt** a split that is not timely notified |
| **2024-10-07** | APPROVED | Nasdaq, Rel. **34-101271**, SR-NASDAQ-2024-029 | a reverse split that drops the company below **another** numeric standard no longer counts as regaining bid-price compliance |
| **2025-01-15** | APPROVED (accelerated) | NYSE, Rel. **34-102201**, SR-NYSE-2024-48 | a reverse split **in the prior one year**, or **cumulative 1-for-200 over two years**, → **no compliance period**, immediate suspension and delisting |
| **2025-01-17** | APPROVED | Nasdaq, Rel. **34-102245**, SR-NASDAQ-2024-045 | **a reverse split of ANY ratio within the prior one year** → no compliance period, mandatory Delisting Determination; **and a hearing request no longer stays suspension** after a failed second 180-day period |
| **2025-12-05** | APPROVED, **operative 2026-01-19** (45 days) | Nasdaq, Rel. **34-104318**, SR-NASDAQ-2025-065 | the $0.10 rule now triggers **regardless of any existing compliance period**, and a hearing request does not stay suspension |

All [PRIMARY DATA DOC] [read in part — caption and mechanism sections].

**Verbatim, the 2020 operative statement** (the only one of the six that states one): *"The Exchange
has proposed to begin to implement the proposed rule change for companies that first receive
notification of non-compliance with the bid price requirement after the date of this approval
order."* And the 2025 Nasdaq look-back, from its notice (Rel. 34-100767): *"A company that effected a
reverse stock split of any ratio will be subject to delisting if it falls out of compliance with the
Bid Price Requirement within one year of the previous reverse stock split."*

> **THE MECHANISM IS A CHANGE IN THE RATE AND TIMING OF TWO CORPORATE-ACTION TYPES, NOT IN ANY
> PRICE.** After 2025-01-15/17, **a second reverse split within a year stops being a way to stay
> listed** — so the serial-reverse-split behaviour that was available 2010–2024 is foreclosed, and
> names that would previously have split again instead delist. **A death-process or reverse-split
> series is not stationary across January 2025**, and the direction is predictable: **fewer repeat
> reverse splits, faster delistings.** Note also that NYSE (1-for-200 / 2 years) and Nasdaq
> (1-for-250 / 2 years) use **different thresholds**, so the effect is listing-venue dependent.

**FIVE OF THE SIX ROWS GIVE ONLY AN APPROVAL DATE.** None of SR-NASDAQ-2023-025, -2024-029,
-2024-045 or SR-NYSE-2024-48 states an operative date in its approval order; the real operative dates
live in Nasdaq Listing Center notices and NYSE trader updates that were not retrieved (§8.16).
**This matters most for the 2025-01-17 one-year look-back, which is the highest-leverage rule here**
— so treat its date as an approval, not a break date.

### CA-NOTE · NOT A BREAK, BUT A STANDING TRAP: large distributions go EX AFTER the pay date
**This is a convention that held across the ENTIRE window — it is not a calendar row.** I record it
because it inverts the ordinary ex-date logic and because **it catches stock splits**, which is
exactly what sibling lane J1 is researching.

FINRA Rule 11140(b)(2), as described verbatim in Rel. 34-81446 [PRIMARY DATA DOC] [read in full]:

> *"Rule 11140(b)(2) establishes the ex-dividend date with respect to "large" distributions, e.g.,
> cash dividends or distributions, stock dividends and/or splits, and the distribution of warrants,
> which are 25% or greater of the value of the subject security. In this case, the ex-dividend date
> is the first business day following the payable date."*

**And it did NOT change under T+1.** The FINRA T+1 filing (Rel. 34-99075) shortens only the
(b)(1) timeframes; its text scopes them to distributions *"that are less than 25 percent of the
value of the subject security"* — **(b)(2) is untouched.** [PRIMARY DATA DOC] [read in full]

**Why it matters.** A 2-for-1 split is a 100% stock distribution, so it falls under (b)(2), **not**
under the (b)(1) convention that CA-2 and CA-3 changed. For any distribution ≥25%:

- the **ex-date comes AFTER the payable date**, not before the record date;
- so "the price adjusts on the ex-date, which precedes the record date" — the assumption behind an
  ordinary dividend sign audit — **is false for this class of events**;
- a due-bill period sits between record date and ex-date, during which the security trades
  *with* the distribution although the record date has passed.

**Consequence for J1.** A split study that aligns the split to the bar by the (b)(1) rule, or by a
fixed offset from the record date, will be **misaligned for every split it studies**, and the
misalignment is not a one-day shift — it is a different anchor entirely. This should be checked
against the corporate-actions feed before any split result is believed, and it is checkable today
with no new data.

---

## 4. TIER 1 — EDGAR FILINGS

**Every date below was read out of an adopting release, a Federal Register entry, an official EDGAR
announcement, or EDGAR's own index files** — not from a summariser and not from a client alert. Three
rows refine something the programme already has on its record, and **the refinements change what a
filter should do**; the rest are new.

> **THE STRONGEST EVIDENCE IN THIS SECTION IS NOT A RELEASE — IT IS THE INDEX FILES THEMSELVES
> (ED-3a, ED-3b).** A release says what was *meant* to happen; `master.idx` and `form.idx` record what
> *did*. **Where the two were compared, they disagreed** — the rename was not a cutover, and the daily
> index carried a truncated string for a year that no announcement mentions. **That gap between the
> rule and the data is the thing this section is actually for.**

### ED-1 · Inline XBRL phase-in — three dates, by filer class, 2019–2021
**ADOPTED/EFFECTIVE 2018-09-17.** COMPLIANCE is in **fiscal periods**, not calendar dates:

| filer class | compliance |
|---|---|
| large accelerated filers (US GAAP) | fiscal periods ending **on or after 2019-06-15** |
| accelerated filers (US GAAP) | fiscal periods ending **on or after 2020-06-15** |
| all other filers, incl. FPIs on IFRS | fiscal periods ending **on or after 2021-06-15** |

Rel. **33-10514** — `https://www.sec.gov/files/rules/final/2018/33-10514.pdf` [PRIMARY DATA DOC]
[read in full for DATES and the phase-in passage]. Verbatim: *"DATES: Effective date: These
amendments are effective on September 17, 2018"*, and the three-year phase-in quoted above
verbatim, clause by clause. The release adds that **domestic form filers comply beginning with their
first Form 10-Q for a fiscal period ending on or after the applicable date** — so the first iXBRL
document for a given filer is a **10-Q, not a 10-K.**

**Mechanism.** The machine-readable representation of a filing's financials changes format, and it
changes **at a different date for each filer, keyed to filer status and fiscal year-end, not to a
calendar date.** Three consequences: (i) **there is no single date on which the panel switches** —
the transition is smeared across 2019-06 to 2022-06 depending on each name's fiscal calendar;
(ii) **filer status is itself time-varying**, so a name can cross classes mid-phase-in; (iii) a
$5-floored small-cap universe is weighted toward the **third** bucket (2021-06-15), i.e. the latest
and least-documented one. **A study that treats "iXBRL available" as a date cut will mis-assign
names.**

### ED-2 · Rule 10b5-1 — the rule and the Form 4/5 checkbox are NOT the same date
**EFFECTIVE 2023-02-27** (the rule). **Forms 4 and 5 checkbox: COMPLIANCE 2023-04-01.**

Rel. **33-11138** — `https://www.sec.gov/files/rules/final/2022/33-11138.pdf` [PRIMARY DATA DOC]
[read in full for DATES and the compliance-date list]. Verbatim: *"DATES: Effective date: The final
rules are effective on February 27, 2023"*; and *"Section 16 reporting persons will be required to
comply with the amendments to Forms 4 and 5 for beneficial ownership reports filed on or after
April 1, 2023."* Issuer-side Item 408 disclosure ran on a separate track: first full fiscal period
beginning **on or after 2023-04-01**, or **2023-10-01** for smaller reporting companies.

**The programme has 2023-04-01 and that date is right. The refinement is the gap.** Between
**2023-02-27 and 2023-03-31** the substantive rule — including the cooling-off periods — was already
in force, but **no Form 4 carried the checkbox.** So:

- **the checkbox is a valid identifier of 10b5-1 trades only from 2023-04-01**, and
- **trades in that five-week gap were governed by the new rule but are unmarked**, so a count of
  "10b5-1 plan trades" that starts at the rule's effective date will read as a spurious jump on
  2023-04-01 that is purely an instrumentation artefact.
- Dates only — Form 4 as a research territory remains excluded.

### ED-3 · Schedules 13D/13G — FOUR dates, not one, and the cut-off change is form-specific
Rel. **33-11253** — `https://www.sec.gov/files/rules/final/2023/33-11253.pdf` [PRIMARY DATA DOC]
[read in full for DATES and section II.G]. Verbatim: *"DATES: Effective dates: The amendments are
effective on February 5, 2024."*

| date | type | what changes |
|---|---|---|
| **2024-02-05** | EFFECTIVE | initial **Schedule 13D** deadline shortened to **five business days** (from the prior 10-day deadline under Rule 13d-1(a)); **and** the EDGAR filing **cut-off moves from 5:30 p.m. ET to 10 p.m. ET** |
| 2023-12-18 | voluntary | filers *may* begin complying with the structured-data requirement |
| **2024-09-30** | COMPLIANCE | revised **Schedule 13G** deadlines begin to bind |
| **2024-12-18** | COMPLIANCE | **structured-data (Inline XBRL) requirement for Schedules 13D and 13G** |

Verbatim on the 13G lag: *"compliance with the revised Schedule 13G filing deadlines … will not be
required before September 30, 2024. Thus, notwithstanding the fact that the final amendments will
become effective on February 5, 2024, beneficial owners will continue to be required to comply with
the current Schedule 13G filing deadlines through September 29, 2024."* And on structured data:
*"compliance with the structured data requirement for Schedules 13D and 13G will not be required
until December 18, 2024."*

**Three refinements to what the programme has on its record:**

1. **The 22:00 ET cut-off is NOT a general EDGAR change.** The release's own comparison table
   assigns it specifically to Schedules 13D and 13G, moving them from **Regulation S-T Rule 13(a)(2)
   (5:30 p.m. ET)** to **Rule 13(a)(4) (10 p.m. ET)**. So an intraday filing-time distribution
   shifts **for these forms only** on 2024-02-05, and a filing-timestamp study must not generalise
   the change to other forms.
2. **13D and 13G moved on DIFFERENT dates** — 2024-02-05 and **2024-09-30**. The programme's record
   says "the Schedule 13D deadline shortening … in 2024", which is correct for 13D and **wrong by
   almost eight months for 13G.**
3. **The form-type string rename is now DATED from EDGAR's own announcement, and it is NOT a clean
   cutover.** See ED-3a — this is the most consequential EDGAR finding in the lane.

### ED-3a · THE `SC 13D` → `SCHEDULE 13D` RENAME: DATED, AND IT IS NOT A CUTOVER
**The programme observed the symptom. Here is the announcement, the date, and — more importantly —
the reason a corrected filter is STILL wrong.**

**The official EDGAR announcements**, both [PRIMARY DATA DOC] [read in full]:

- **Introduced 2023-12-18**, *EDGAR Release 23.4*: *"EDGAR will be updated to allow filers to
  voluntarily submit submission types Schedule 13D and Schedule 13D/A online in a structured XML
  format until December 18, 2024"* — with an identical paragraph for 13G and 13G/A.
- **Mandatory 2024-12-16**, *EDGAR Release 24.4*
  (`https://www.sec.gov/submit-filings/edgar-news-announcements/edgar-release-24-4`): *"EDGAR has
  been updated to replace the HTML and ASCII filing formats for Schedules 13D and 13G (e.g. SC 13D,
  SC 13G; respectively) and their amendments, with an XML-based filing format (e.g. SCHEDULE 13D,
  SCHEDULE 13G; respectively)."*

**And then it was checked against EDGAR's own `master.idx` files — which is EDGAR's data, not a
description of it** [PRIMARY DATA DOC] [read in full]:

| date | what the index actually contains |
|---|---|
| 2023-12-18 | **first** `SCHEDULE 13G` rows ever (2). 2023 Q4: **4** SCHEDULE vs **5,829** `SC 13*` |
| 2024 Q1–Q3 | **the two conventions COEXIST** — 226 / 116 / 168 SCHEDULE rows against 40,090 / 5,565 / 5,638 `SC 13*` |
| 2024-12-18 | last legacy row in sequence: one `SC 13D/A` |
| 2024-12-19 | **first day with zero legacy `SC 13D/G` rows** |
| 2024-12-31 **and 7 more dates in 2025 Q1** | `SC 13D/A` rows **still appear** (2025-01-07, 01-10, 02-05, 02-24 ×2, 03-17, 03-25) |

> **SO BOTH THE OLD FILTER AND THE OBVIOUS FIX ARE WRONG.** A filter on `SC 13D` silently returns
> zero after 2024-12-19. **But a filter on `SCHEDULE 13*` alone misses a full year of coexistence
> (2024 Q1–Q3) AND still misses filings in 2025 Q1.** The only correct filter over the whole window
> matches **both** strings throughout. **A one-sided correction looks like a fix and is not one.**

**All four names renamed together** — `SC 13D`, `SC 13G`, `SC 13D/A`, `SC 13G/A` — which answers the
sibling question directly. **`SC 13E3`, `SC TO-T`, `SC TO-I`, `SC 14D9` and `SC 14F1` were NOT
renamed** and still carry the `SC ` prefix, so a blanket `SC ` → `SCHEDULE ` rewrite would break
those.

### ED-3b · AND A SECOND, UNDOCUMENTED BREAK: THE DAILY INDEX TRUNCATED THE NEW STRING FOR A YEAR
**Established from the archived index files alone. No SEC announcement dates this, and I could not
find one.**

The form-type column in the **daily** `form.idx` and `company.idx` was **12 characters wide**, so the
longer new names were **silently truncated to `SCHEDULE 1`**:

| file | content |
|---|---|
| `daily-index/2023/QTR4/form.20231218.idx` | `SCHEDULE 1  Clearmind Medicine Inc.` |
| `daily-index/2024/QTR4/form.20241218.idx` | `SCHEDULE 1  AFP Integra S.A.` — **88 such rows** |
| `daily-index/2024/QTR4/form.20241220.idx` | **still truncated** — 126 rows |
| `daily-index/2024/QTR4/form.20241223.idx` | **fixed** — `SCHEDULE 13D` in a 17-char field |

**So from 2023-12-18 to 2024-12-20 the daily `form.idx` and `company.idx` carried `SCHEDULE 1`, and
the column was widened over the weekend of 2024-12-20/23.** The pipe-delimited `master.idx` was
**never** truncated, and the **quarterly** `full-index/*/form.idx` files were regenerated and show
the full names.

> **THE CONSEQUENCE IS THE ONE THAT MATTERS HERE: FOR TWELVE MONTHS, A SERIES BUILT FROM THE DAILY
> INDEX DISAGREES WITH ONE BUILT FROM THE QUARTERLY INDEX OR FROM ANY `master.idx`.** Neither is
> corrupt; they disagree about the *name of the form type*. **And because the quarterly files were
> regenerated, the disagreement is invisible to anyone who re-pulls the quarterly index today — the
> evidence of it survives only in the archived daily files.** A point-in-time reconstruction that
> uses daily indices for recency and quarterly for history will straddle it.

### ED-4 · 8-K Item 1.05 — a NEW 8-K ITEM CODE — 2023-12-18 and 2024-06-15
**EFFECTIVE 2023-09-05. COMPLIANCE: 2023-12-18 for all registrants other than smaller reporting
companies; 2024-06-15 for smaller reporting companies.** Inline XBRL tagging of Item 1.05 from
**2024-12-18.**

Rel. **33-11216** — `https://www.sec.gov/files/rules/final/2023/33-11216.pdf` [PRIMARY DATA DOC]
[read in full for DATES and section II.I]. Verbatim: *"all registrants other than smaller reporting
companies must begin complying on December 18, 2023 … smaller reporting companies are being given an
additional 180 days … before they must begin complying with Item 1.05 of Form 8-K, on June 15,
2024."* And: *"For Item 1.05 of Form 8-K and Form 6-K all registrants must begin tagging responsive
disclosure in Inline XBRL beginning on December 18, 2024."*

**Mechanism, and why it is a calendar row rather than trivia.** **The 8-K item-code vocabulary
gained a code that did not previously exist.** Round 4's lane
[`H1`](../leads4/H1-8k-item-code-map.md) researched the 8-K item-code map; this is a dated change to
that map inside the window. Specifically:

- **Item 1.05 has a zero base rate before 2023-12-18 by construction**, so any item-code frequency
  series, item-code histogram, or "share of 8-Ks by item" denominator changes on that date;
- **the smaller-reporting-company carve-out means the adoption date is SIZE-DEPENDENT** — and a
  $5-floored small-cap universe is heavily SRC, so for most of this programme's names the live date
  is **2024-06-15, not 2023-12-18**;
- the annual-report counterpart (Item 106 of Regulation S-K) begins with **fiscal years ending on or
  after 2023-12-15**, a third date.

**This row's pattern — a new item code, phased by filer size — is the one most likely to recur**, so
an item-code map should carry a "first possible date" per code rather than assuming a fixed
vocabulary.

> **AND THE RULE'S COMPLIANCE DATE IS NOT THE DATE THE CODE BECAME SELECTABLE IN EDGAR.** *EDGAR
> Release 23.4*, 2023-12-18 [PRIMARY DATA DOC] [read in full]: *"Item 1.05 will be added to the
> following forms … Forms 8-K, 8-K12B, 8-K12G3, 8-K15D5, 8-K/A, 8-K12B/A, 8-K12G3/A, and
> 8-K15D/A."* **So although the rule was EFFECTIVE 2023-09-05, Item 1.05 could not be selected in
> EDGAR at all until 2023-12-18.** For a filing-derived series the EDGAR date is the binding one.

### ED-5 · FOUR MORE 8-K ITEM CODES WERE ADDED INSIDE THIS WINDOW — and the 10-K/10-Q items were RENUMBERED
**The programme's record has only the pre-window 2006 Item 5.02(e) change. The 8-K item vocabulary
actually changed five times inside 2010-01-04 to 2026-08-26** (Item 1.05 being the fifth, ED-4). **No
8-K item code was retired or renumbered in the window** — all five changes are additions, verified
against the current Form 8-K item list on sec.gov (1.01–1.05, 2.01–2.06, 3.01–3.03, 4.01–4.02,
5.01–5.08, 6.01–6.06, 7.01, 8.01, 9.01).

| code | date | type | release | note |
|---|---|---|---|---|
| **Item 5.07** Submission of Matters to a Vote of Security Holders | **2010-02-28** | EFFECTIVE | 33-9089, *Proxy Disclosure Enhancements*, 74 FR 68334 | *"Amend Form 8–K … by adding Item 5.07."* **Zero base rate before this date** |
| **Item 5.08** Shareholder Director Nominations | 2010-11-15 nominal; **actual 2011-09-20** | see below | 33-9136, 75 FR 56668; date reset by 33-9259, 76 FR 58100 | **STAYED then its trigger VACATED — see §6.3** |
| **Item 5.07(d)** say-on-pay frequency | **2011-04-04** | EFFECTIVE + COMPLIANCE | 33-9178, 76 FR 6010 | *"DATES: Effective Date: April 4, 2011."* A new **sub-item**, not a new code |
| **Item 1.04** Mine Safety — Shutdowns and Patterns of Violations | **2012-01-27** | EFFECTIVE | 33-9164, *Mine Safety Disclosure*, 76 FR 81762 | *"DATES: Effective Date: January 27, 2012."* Also added 10-K Item 4 and 10-Q Part II Item 4 |

All [PRIMARY DATA DOC] [read in full].

> **AND THE SAME 2010-02-28 RELEASE RENUMBERED THE 10-K AND 10-Q ITEM STRUCTURE.** Verbatim from
> 33-9089: *"Amend Form 10–K … by removing Item 4 in Part I, and redesignating Items 5 through 15 as
> Items 4 through 14."* For the 10-Q, Part II Item 4 was removed and Items 5–6 became 4–5. **So
> 10-K/10-Q item numbers are not comparable across 2010-02-28**, and voting results **moved out of
> the 10-K/10-Q into the 8-K** on that date — a migration of content between form types, which is the
> kind of break that makes a form-level count look like a behavioural change. A correction followed at
> 75 FR 9100 (2010-03-01).

**Mechanism, in one line:** any 8-K item-code histogram, any "share of filings by item", and any
10-K/10-Q item-keyed extractor has a **vocabulary change** at 2010-02-28, 2012-01-27 and 2023-12-18,
and every new code has a **structural zero** before its date. Item-code map as a research territory
remains excluded; these are dated structural changes to the map.

### ED-6 · Form 144 — paper to EDGAR — 2023-04-13, and a filing-hours change at 2023-03-20
**COMPLIANCE 2023-04-13.** Release **33-11070** (*not* 33-11056), *Updating EDGAR Filing Requirements
and Form 144 Filings*, 87 FR 35393 (2022-06-10); ADOPTED 2022-06-02, **EFFECTIVE 2022-07-11**.

The release does **not** state a compliance date directly — it defines it by reference: *"the
requirement to file Form 144 electronically on EDGAR will commence six months from the date of
publication in the Federal Register of the Commission release that adopts the version of the EDGAR
Filer Manual addressing updates to Form 144."* That manual release is 33-11101 (2022-09-19), 87 FR
61977 (2022-10-13) → **2023-04-13**, stated outright in the official EDGAR announcement
(`https://www.sec.gov/oit/announcement/form-144-electronic-filing-compliance-date`): *"Affected
filers have until April 13, 2023 to transition from paper to electronic filing of Form 144."* All
[PRIMARY DATA DOC] [read in full].

**Plus, same family:** *Extending Form 144 EDGAR Filing Hours*, 88 FR 12205, **EFFECTIVE 2023-03-20**
— *"The amendments are effective on March 20, 2023."* Adds Form 144 to Reg S-T Rule 13(a)(4), so a
submission after 5:30 p.m. but by 10:00 p.m. ET gets the **same** business-day filing date.

**Mechanism.** **Form 144 volume in EDGAR steps up hard at 2023-04-13 as paper filers migrate** — the
series before that date is not low, it is *incomplete by construction*, because paper filings never
entered EDGAR at all. And the filing-date-vs-acceptance-time mapping shifts at 2023-03-20.

### ED-7 · THE FINANCIAL STATEMENT DATA SETS WERE REWRITTEN RETROACTIVELY, IN PLACE — 2024-12
**This is the worst break in the calendar for replication, and it has no day-of-month.**

Official SEC page `https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets`
[PRIMARY DATA DOC] [read in full]. Verbatim: *"In December 2024, reprocessed Financial Statement Data
Sets were posted."* The change: *"refreshed to only include the submissions and the numeric data from
the primary financial statements as rendered by the Commission"* — previously the sets also held
non-dimensional or co-registrant data — and *"a new field 'segments' has been added"* to the NUM file.

> **THE HISTORICAL QUARTERLY ZIPS BACK TO 2009 Q1 WERE REPLACED UNDER THE SAME FILENAMES.** A dataset
> pulled before December 2024 and one pulled after **are not the same data**, and **nothing in the
> file or the filename distinguishes them.** There is no version field. So a number computed from
> these sets before December 2024 cannot be reproduced from them today, and a cached copy cannot be
> identified as stale by inspection. **`CLAUDE.md` requires caches keyed on fixture and module
> mtimes; this is the same failure mode arriving from outside, and an mtime on a re-downloaded file
> will look fresh.** Dated only to the month (§8.9).

### ED-8 · FOREIGN PRIVATE ISSUER INSIDERS ENTER FORM 4 — 2026-03-18 — A COMPOSITION BREAK INSIDE THE WINDOW
**EFFECTIVE 2026-03-18.** Release **34-104903**, *Holding Foreign Insiders Accountable Act
Disclosure*, 91 FR 10320 (2026-03-03); ADOPTED 2026-02-27; underlying statute enacted 2025-12-18.
`https://www.govinfo.gov/content/pkg/FR-2026-03-03/pdf/2026-04202.pdf` [PRIMARY DATA DOC] [read in
full]. Verbatim: *"DATES: Effective date: March 18, 2026."*

Substance: extends Section 16 reporting to *"directors and officers of a foreign private issuer with
a class of equity securities registered under Section 12"* (**not** FPI 10-percent holders). Amends
Rule 3a12-3(b), Rule 16a-2 and Forms 3, 4 and 5. Corroborated by the **Ownership XML technical
specification v5.5, dated 2026-03-18**, which adds *"`<issuerForeignTradingSymbol>`,
`rptOwnerNonUSAddressFlag`, `rptOwnerNonUSStateTerritory` and `rptOwnerCountry`"* to submission types
3, 3/A, 4, 4/A, 5, 5/A. A cosmetic technical correction followed at 91 FR 32335, effective 2026-06-01.

**Mechanism.** **From 2026-03-18 an entirely new population of issuers begins generating Form 4s**, and
four new fields appear in the Form 4 XML. Any Form 4-derived count, breadth measure or cross-sectional
universe has a **composition break** — not a behavioural change — at that date. **It lands 161 calendar
days before the window closes**, so it clips the tail and cannot support a two-regime test; its value is
as a *warning against reading a level shift in Form 4 counts in 2026 as signal*. Dates only; Form 4 as a
research territory remains excluded.

---

## 5. TIER 2 — LOWER PRIORITY: REAL, DATED, BUT THE MECHANISM BARELY REACHES THIS PROGRAMME'S DATA

| row | date (type) | primary citation | what it changes | why tier 2 |
|---|---|---|---|---|
| **T2-1** Rule 605 amendments | **COMPLIANCE 2026-08-01**, extended from 2025-12-14; EFFECTIVE 2024-06-14; ADOPTED 2024-03-06 | Rel. 34-99679, 89 FR 26428; extension Rel. **34-104147**, effective 2025-10-02 — `https://www.sec.gov/files/rules/final/2025/34-104147.pdf` [PRIMARY DATA DOC] [read in full]. Verbatim: *"from December 14, 2025, to August 1, 2026"* | broker/market-centre execution-quality reports | the programme holds no 605 data, and the date is **25 days before the window ends** |
| **T2-2** Regulation SCI | EFFECTIVE 2015-02-03; **COMPLIANCE 2015-11-03** (nine months after, per the release) | Rel. 34-73639 — `https://www.sec.gov/files/rules/final/2014/34-73639.pdf` [PRIMARY DATA DOC] [read in full — DATES and compliance sections]. Verbatim: *"DATES: Effective date: February 3, 2015"*; *"a compliance date for Regulation SCI of nine months after the Effective Date"* | systems-integrity obligations on exchanges and the SIPs | **no stated mechanism that reaches a daily bar.** Plausibly reduces outage frequency; I could not name a quantity in this fixture it moves. Included only so the lane does not look like it missed it |
| **T2-3** Odd-lot **quote** dissemination under the MDI rules | **2026-04-27** (CTA SIP) | CTA Plan FAQ, `https://www.ctaplan.com/publicdocs/ctaplan/CTA_Odd_Lots_Changes_FAQ.pdf` [PRIMARY DATA DOC] [snippet only]. Verbatim: *"starting with Odd Lot Quote release on April 27, 2026"* | odd-lot **quotes** and a Best Odd Lot Order now disseminated; the FAQ states they *"are not protected … and do not affect the round lot"* quotes or the NBBO | **quotes, not trades.** The programme holds bars, not quotes. Four months before window end |
| **T2-4** EDGAR Next (filer access and account management) | EFFECTIVE **2025-03-24**; COMPLIANCE **2025-09-15**; enrolment closed **2025-12-19** | Rel. **33-11313 / 34-101209** (*not* 33-11350), 89 FR 106168 — `https://www.govinfo.gov/content/pkg/FR-2024-12-27/pdf/2024-30494.pdf` [PRIMARY DATA DOC] [read in full]. Verbatim: *"The compliance date for all other rule and form amendments … is September 15, 2025."* | filer credentials move to Login.gov; account-administrator roles; optional filer APIs | **NO public filing metadata appears to change** — nothing in the release touches the index, accession format, form type or acceptance timestamp, and an empirical check of `master.idx` daily filing counts shows **no level shift at 2025-09-15** (3,824 on 09-12; 3,276 on 09-15; 3,724 on 09-16). **A negative established by absence plus one check, so weaker than a positive date** (§8.10) |
| **T2-5** Fee-related EDGAR filings: acceptance time and filing date **diverge by design** | **2025-04-14** | Official announcement, `https://www.sec.gov/newsroom/whats-new/fee-related-edgar-filings-update` [PRIMARY DATA DOC] [read in full]. Verbatim: *"Effective April 14, 2025, fee-related filings received after 5:30 p.m. ET but before 10:00 p.m. ET will receive notifications and be accepted that same day … but will continue to receive a filing date that corresponds to the next business day."* | for fee-bearing form types, **acceptance datetime and filing date deliberately disagree** after 17:30 ET | relevant only to a **filing-timestamp** study on fee-bearing types (registration statements, not 8-K/13D). **Worth knowing that "accepted" ≠ "filed" is now by design, not error** |
| **T2-6** EDGAR stops verifying NT filing timeliness | **2016-10-31** | *Release 16.3.3 EDGAR Dissemination Feed Updates* (2016-10-06), `https://www.sec.gov/newsroom/whats-new/edgar-dissemination-feed-updates-1633` [PRIMARY DATA DOC] [read in full] | EDGAR no longer checks whether `NT 10-K`, `NT 10-Q`, `NT 20-F` etc. were submitted before the deadline | **only matters if NT filings are used as a lateness proxy.** Listed because that is a plausible future lane and the proxy changes meaning here |

### 5.1 · Swept and DELIBERATELY EXCLUDED, with the reason

**A break with no stated mechanism is trivia**, so these were checked and left out rather than
padded in. **I did not spend effort dating them, because the reason for exclusion does not depend on
the date.** Listed so that silence is not mistaken for an oversight — several were named in the lane
brief's own candidate list.

| swept | why it is not a row |
|---|---|
| **Consolidated Audit Trail** (Rule 613 and the CAT NMS Plan, phased reporting from 2018) | CAT is a **regulator-only** repository. Nothing it changed is visible in a daily bar, a corporate action, or an EDGAR filing. **No mechanism.** Named in the brief; excluded on mechanism, not on effort |
| **Regulation Best Interest** | broker–customer conduct standard. No mechanism reaching any series held |
| **Rule 15c3-5 (market access)** | broker pre-trade risk controls. Plausibly reduces erroneous prints, but **I can name no quantity in this fixture it moves**, so it stays out |
| **Retail Liquidity Programs** (NYSE and others, from 2012) | sub-penny price improvement on retail order flow. Affects *execution* quality, not the consolidated O/H/L/C this programme holds |
| **Decimalisation** (2001) | **pre-window** |
| **8-K Item 5.02(e)** folding equity-award grants into an existing item code (2006) | **pre-window.** On the programme's known list, but it is four years before 2010-01-04 and therefore constant across the entire sample |
| **Exchange fee *schedule* changes** (routine, continuous) | these happen monthly at every venue and are not datable as a panel-level break. The one fee *pilot* that would have been a row never ran — §6 |

---

## 6. ADOPTED BUT NEVER IN FORCE — THE ROWS THAT ARE **NOT** BREAKS

**This section exists because the programme has already commissioned research premised on a
disclosure rule a court vacated before it produced any data.** Each of these looks like a calendar
row and is not one.

**6.1 · Reg NMS minimum pricing increments and access fee caps (Rel. 34-101070) — ADOPTED
2024-09-18, EFFECTIVE 2024-12-09, AND NEVER IN FORCE AT ANY POINT IN THIS WINDOW.**

- Adopting release `https://www.sec.gov/files/rules/final/2024/34-101070.pdf` [PRIMARY DATA DOC]
  [read in full — DATES and Part VI]. Verbatim: *"DATES: Effective Date: December 9, 2024"*, with
  compliance *"Rules 600(b)(89)(i)(F) and 612: The first business day of November 2025"*,
  *"Rule 610: The first business day of November 2025"*, and odd-lot information *"the first
  business day of May 2026."*
- Then: exemptive relief to **November 2026** (Rel. 34-104172, 2025-10-31, 90 FR 51418), announced
  at `https://www.sec.gov/newsroom/press-releases/2025-130-...` [PRIMARY DATA DOC] [read in full].
  That press release also records *"the Commission's **partial stay** of the effect of the
  amendments to Rules 600(b)(89)(i)(F), 610(c) and 612 upon the completion of judicial review"* and
  a **D.C. Circuit denial of a petition for review**.
- Then: further extension to **the first business day of November 2027**, Rel. **34-105656**
  (2026-06-11), per the Chairman's statement of 2026-06-11
  (`https://www.sec.gov/newsroom/speeches-statements/atkins-statement-minimum-pricing-increments-access-fee-caps-061126`)
  [PRIMARY DATA DOC] [read in full]. Verbatim: *"Today, the Commission further extended the
  temporary exemptive relief … until the first business day of November 2027."*

**So: the $0.005 tick and the $0.001 access-fee cap are NOT a break in 2024, 2025 or 2026.** The
programme's record has the November-2027 delay; the stronger fact is the **partial stay pending
judicial review**, which means the amendments never bound even between the effective date and the
first exemption. **Nothing in this fixture changes on 2024-12-09.**

**6.2 · And from the same statement, a live negative:** on **2026-06-11** the Commission
*"proposed to rescind Rule 611 of Regulation NMS, known as the trade-through rule"* (Rel.
34-105655), plus Rule 610(e)'s locked/crossed provisions. **PROPOSED, not adopted.** Not a row.
Flagged because it is the kind of thing that will read, in a year's time, as though it had happened.

**6.3 · 8-K Item 5.08 / Rule 14a-11 — ADOPTED, STAYED, THEN THE TRIGGER VACATED.**
Nominal **EFFECTIVE 2010-11-15** (Rel. 33-9136, *Facilitating Shareholder Director Nominations*, 75 FR
56668). Then:

- **STAYED by Commission order 2010-10-04** (Rel. 33-9149/34-63031/IC-29456,
  `https://www.sec.gov/files/rules/other/2010/33-9149.pdf`) — *"the Commission has determined to
  exercise its discretion to stay Rule 14a-11 and related amendments."*
- **Rule 14a-11 VACATED by the D.C. Circuit on 2011-07-22.**
- The Form 8-K amendment itself then took effect **2011-09-20** (Rel. 33-9259, 76 FR 58100): *"the
  amendments to … § 249.308, published on September 16, 2010 (75 FR 56668), is September 20, 2011.
  Section 240.14a-11 was vacated."*

All [PRIMARY DATA DOC] [read in full]. **So Item 5.08 exists in Form 8-K from 2011-09-20 but the rule
that would have triggered it is dead — expect it to be essentially unused.** A non-zero count would
be more surprising than a zero one, and a "new item code therefore new disclosure" inference fails
here.

**6.4 · Share Repurchase Disclosure Modernization — ADOPTED, EFFECTIVE, VACATED BEFORE ITS FIRST
REQUIRED FILING.** ADOPTED **2023-05-03**, Rel. **34-97424** / IC-34906, File S7-21-21; **EFFECTIVE
2023-07-31**; **VACATED by the Fifth Circuit, applicable 2023-12-19**.

- Adopting release `https://www.sec.gov/files/rules/final/2023/34-97424.pdf` [PRIMARY DATA DOC]
  [read in part]. *"DATES: This final rule is effective on July 31, 2023."* **Compliance** was
  *"the first filing that covers the first full fiscal quarter that begins on or after October 1,
  2023"* (FPIs 2024-04-01; listed closed-end funds 2024-01-01).
- Vacatur, stated in the SEC's **own** conforming release Rel. **34-99778** / IC-35157,
  `https://www.sec.gov/files/rules/final/2024/34-99778.pdf` [PRIMARY DATA DOC] [read in full]:
  *"On December 19, 2023, the U.S. Court of Appeals for the Fifth Circuit vacated the Repurchase
  Rule."* and *"The Federal court's vacatur of the rule amendments was applicable as of December 19,
  2023."*

> **CORRECTION TO MY OWN EARLIER READING OF THIS ROW: IT PRODUCED EFFECTIVELY NO DATA AT ALL.** I
> first recorded it as "about five months of data" on the strength of the effective and vacatur
> dates. **That was wrong, and the compliance date is why.** The first *required* daily-repurchase
> table for a December-fiscal-year issuer would have appeared in its FY2023 Form 10-K, filed in
> 2024 — **after** the 2023-12-19 vacatur. **The rule was effective for 141 days and never reached a
> single mandatory filing.** Any daily repurchase data in this window is voluntary or early, not
> required, and therefore a self-selected sample.
>
> **The lesson is the lane's own thesis in miniature: effective-minus-vacated is NOT the data
> window. Compliance-minus-vacated is, and here it is empty.** Reading two dates off a release and
> subtracting them produced a plausible, specific, wrong answer.

**6.5 · Rule 610T, the TRANSACTION FEE PILOT — ADOPTED, STAYED, VACATED, AND IT NEVER PRODUCED A
SINGLE OBSERVATION.** ADOPTED **2018-12-19** (Rel. 34-84875, 84 FR 5202); **EFFECTIVE 2019-04-22**;
**STAYED IN PART 2019-03-28**; **VACATED 2020-06-16**.

- Stay: Rel. **34-85447**, Admin. Proc. 3-19124 [PRIMARY DATA DOC] [read in full] — *"ORDER ISSUING
  STAY"*. It stayed the Pilot and post-Pilot periods **in their entirety**, and stayed pre-Pilot data
  *reporting and public disclosure*; only exchanges' internal **compilation** survived.
- Pre-Pilot dates: Rel. **34-85906** [PRIMARY DATA DOC] [read in full] — *"1. July 1, 2019 as the
  pre-Pilot period's commencement date, and 2. December 31, 2019 as the pre-Pilot period's
  termination date"*, and *"these exchanges will not be required to transmit order routing data to
  the Commission, or to publicly post Exchange Transaction Fee Summaries."*
- **VACATED** — *New York Stock Exchange LLC v. SEC*, No. 19-1042 (consol.), **962 F.3d 541** (D.C.
  Cir.) [PRIMARY DATA DOC] [read in part]: *"Argued October 11, 2019 Decided June 16, 2020"* and
  *"We grant the petitions for review and vacate Rule 610T and the Pilot Program."* Ground: the SEC
  *"acted without delegated authority."*

> **NO LIST OF PILOT SECURITIES WAS EVER DESIGNATED, NO FEE OR REBATE TREATMENT WAS EVER APPLIED, AND
> NO ORDER-ROUTING DATASET OR FEE SUMMARY WAS EVER TRANSMITTED OR POSTED.** Exchanges compiled
> pre-Pilot data for their own files, 2019-07-01 → 2019-12-31, and that is all that ever existed.
> **The lane brief asked for "exchange fee pilots and the litigation that vacated them": this is it,
> and the answer is that it is a non-row.**

**6.6 · Rule 13f-2 / FORM SHO — ADOPTED, EXEMPTED TWICE, REMANDED, AND ZERO FILINGS EXIST.**
ADOPTED **2023-10-13** (Rel. 34-98738, 88 FR 75100); **EFFECTIVE 2024-01-02**; original **COMPLIANCE
2025-01-02**; now exempted to **2028-01-02**.

- Exemption #1, Rel. **34-102380** [PRIMARY DATA DOC] [read in full]: *"a temporary exemption from
  compliance with Rule 13f-2 and Form SHO reporting effective February 7, 2025, and ending January 2,
  2026"* — granted **one week before the first Form SHO was due** (2025-02-14).
- Litigation: *Nat'l Ass'n of Private Fund Managers, MFA, AIMA v. SEC*, No. 23-60626 (5th Cir.)
  [PRIMARY DATA DOC] [read in part]: *"FILED August 25, 2025"*, *"we GRANT the petition for review in
  part and REMAND the Securities Lending Rule and the Short Sale Rule."* **Remand WITHOUT vacatur**,
  for failure to quantify the two rules' *cumulative* economic impact — so both rules legally remain
  on the books.
- Exemption #2, Rel. **34-104303** (2025-12-03) [PRIMARY DATA DOC] [read in full]: relief *"effective
  January 2, 2026, and ending January 2, 2028."* **The first Form SHO now covers a January 2028
  period.**

> **AND THIS ONE WAS CENSUSED, WITH A CONTROL.** EDGAR full-text search returns **0 filings** for
> `forms=SHO`. **Control: the identical query shape against `13F-HR` and `SD` each returns 10,000+.**
> So the zero is a real zero, not a broken query — which is exactly the check the lane brief demands
> of a parameterised endpoint, applied to the one row where a zero is the whole finding.
>
> **Short interest and borrow remain a permanently excluded territory. The point of this row is
> narrower and it is a warning: there is no Form SHO data, there never has been, and there will be
> none before 2028.** Any proposal premised on it is premised on a rule that has been exempted twice.

**6.7 · Rule 10c-1a / FINRA SLATE — securities-lending reporting had NOT begun.** ADOPTED
2023-10-13 (Rel. 34-98737); EFFECTIVE 2024-01-02; original reporting date 2026-01-02 and
dissemination 2026-04-02; **delayed to 2026-09-28 / 2027-03-29 (2025-07-28), then to 2028-09-28 /
2029-03-29** (Rel. 34-104303). FINRA's SLATE Rule 6500 Series **was** approved 2025-01-02 (Rel.
34-102093) — **but it carries no live reporting obligation.** [PRIMARY DATA DOC] [read in full].
**Nothing was reported or disseminated on or before 2026-08-26.**

**6.8 · Nasdaq BOARD DIVERSITY — the one row here that DID produce data, with a hard stop.**
**APPROVED 2021-08-06** (Rel. 34-92590); **Rule 5606 OPERATIVE 2022-08-06** (*"Proposed Rule 5606
would become operative one year after Commission approval"*); **VACATED 2024-12-11** — *Alliance for
Fair Board Recruitment v. SEC*, No. 21-60626 (5th Cir., **en banc**) [PRIMARY DATA DOC] [read in
part]: *"FILED December 11, 2024"*, *"we GRANT the consolidated petitions for review and VACATE SEC's
order approving Nasdaq's Board Diversity Proposal."*

> **This one is different from every other row in §6: it ran for about 28 months and produced roughly
> the 2022, 2023 and 2024 proxy seasons of board-diversity matrices, then stopped dead.** A series
> built on it has a genuine start **and** a genuine end, both for legal reasons — **so it is a real
> regime, bounded 2022-08-06 → 2024-12-11, and neither endpoint is a behavioural change.**

**6.9 · Market Data Infrastructure — the core regime is STILL not in effect, but ONE PIECE WENT
LIVE.** ADOPTED 2020-12-09 (Rel. 34-90610); **EFFECTIVE 2021-06-08**; the competing-consolidator /
decentralized-consolidation / exclusive-SIP-retirement regime **was not in effect at 2026-08-26 and
nothing has started its clock** — compliance was never calendar-dated, being keyed to a plan-amendment
approval that never issued. The SEC says so itself in Rel. 34-101070 [PRIMARY DATA DOC] [read in
part]: *"Because the MDI Rules are not yet implemented, NMS stock quotation information that is
included in SIP data is provided in round lots, as defined in exchange rules"*, and *"competing
consolidators, which are not yet in operation."*

> **BUT THE ROUND-LOT DEFINITION DID GO LIVE, ON 2025-11-03**, per Rel. **34-104172** (2025-10-31)
> [PRIMARY DATA DOC] [read in full]: *"the implementation of the round lot definition as set forth in
> Rule 600(b)(93) … is required to be completed on the first business day of November 2025, i.e.,
> November 3, 2025."*
>
> **AND THAT INTERACTS DIRECTLY WITH BAR-5.** A round lot is no longer 100 shares for every stock —
> it is tiered by price, so for stocks above $250 the round lot is smaller. **"Odd lot" is defined as
> less than a round lot**, and odd lots have been in consolidated volume since 2013-12-09 (BAR-5).
> **So on 2025-11-03 the boundary between "odd lot" and "round lot" moved for high-priced names**,
> which shifts what the `I` modifier marks. It does **not** change total volume — every trade is still
> reported — but it changes the odd-lot/round-lot **split** of it, and therefore any series that
> conditions on that flag. Rule 610(d) (fees determinable at execution) became operative the first
> business day of **February 2026**.

**6.10 · NEVER ADOPTED AT ALL — the Order Competition Rule and Regulation Best Execution.**
**Both were PROPOSED ONLY and FORMALLY WITHDRAWN as of 2025-06-17.** Rel. **33-11377** /
34-103247 [PRIMARY DATA DOC] [read in part]: *"ACTION: Notice of withdrawal of proposed rules"* and
*"The Commission does not intend to issue final rules with respect to these proposals."* The
withdrawal names them: 88 FR 128 (2023-01-03) = **Order Competition Rule** (proposed Rule 615);
88 FR 5440 (2023-01-27) = **Regulation Best Execution**. **Volume-Based Exchange Transaction Pricing
for NMS Stocks** (88 FR 76282) was withdrawn in the same instrument and was also never adopted.

> **Neither ever had a compliance date, produced data, or changed any behaviour. A study premised on
> either is premised on a proposal.**

**6.11 · Other adopted-then-killed disclosure rules, in brief** — all [PRIMARY DATA DOC] [read in
part]:

| rule | outcome | data? |
|---|---|---|
| **SEC climate disclosure** (33-11275), ADOPTED 2024-03-06, EFFECTIVE 2024-05-28 | **STAYED 2024-04-04** (Rel. 33-11280); defence **withdrawn 2025-03-27**; petitions held in **abeyance 2025-09-12**; **rescission only PROPOSED 2026-05-29** (33-11421) | **NONE.** The stay preceded any compliance date. **As of 2026-08-26 it is still nominally in the CFR, stayed** |
| **Resource extraction** (Rule 13q-1) | 2012 rule **VACATED 2013-07-02**; 2016 rule **CRA-disapproved 2017-02-14**; 2020 rule EFFECTIVE 2021-03-16, first Form SD ~2024-09-30 | 2012 and 2016 versions: **zero filings**. 2020 version: filings from 2024, **not verified** (§8.17) |
| **Conflict minerals** (Rule 13p-1 / Form SD) | EFFECTIVE 2012-11-13, first reports 2014-05-31; **partially unconstitutional 2014-04-14** (*NAM v. SEC*, 748 F.3d 359) — **only** the compelled "not been found to be 'DRC conflict free'" descriptor fell | **YES, continuously from 2014-05-31.** The regime survived |
| **Pay ratio** (33-9877) | EFFECTIVE 2015-10-19, COMPLIANCE first FY beginning on/after 2017-01-01 | **NOT killed.** No vacatur or stay found. Data from 2018 proxies |
| **Clawback / Rule 10D-1** (33-11126) | EFFECTIVE 2023-01-27; listing standards required effective no later than 2023-11-28 | **NOT killed.** Produced data |

**The last two are listed precisely because they are negatives** — they are the two most commonly
assumed to have been struck down, and neither was.

**6.12 · AND ONE THAT WAS APPROVED INSIDE THE WINDOW AND STAYED SEVEN DAYS LATER.** Nasdaq's **$5M
MVLS continued-listing requirement** (Rel. **34-105971**, SR-NASDAQ-2026-004) was **APPROVED
2026-07-22** — MVLS below $5m for 30 consecutive business days → **immediate Staff Delisting
Determination, no cure period** — and **STAYED 2026-07-29** by operation of Rule of Practice 431(e)
when Cemtrex, Inc. and the Small Public Company Coalition filed notices of intention to petition for
review. Deputy Secretary letter [PRIMARY DATA DOC] [read in full]: *"In accordance with Rule 431(e),
the July 22, 2026, order is stayed until the Commission orders otherwise."*

> **SO IT PRODUCED ZERO DELISTINGS IN THE WINDOW. Anyone modelling a Nasdaq delisting-rate break at
> 2026-07-22 would be modelling a rule that was stayed seven days later** — and this is the newest
> instance of the exact pattern the lane exists to catch. **Whether the stay was still in force at
> 2026-08-26 is NOT established** (§8.15); if the Commission lifted it in August 2026 the operative
> date moves into the window.

**6.13 · And the largest pending delisting break lands just AFTER the window.** NYSE's **$0.25
Minimum Trading Price** (Rel. **34-106133**, SR-NYSE-2025-43) was **APPROVED 2026-08-14** — *"if a
security's closing price per share is less than $0.25 … on any trading day, the Exchange shall
immediately suspend trading and commence delisting proceedings"* — but **EFFECTIVE 2027-07-01**:
*"Amendment No. 2 extends the effective date of the proposed rule to July 1, 2027."* [PRIMARY DATA
DOC] [read in part]. **Outside the window, and therefore not a row — but it is the single largest
delisting-rate change now scheduled, and any future extension of this fixture past mid-2027 must
carry it.**

---

## 7. WHICH ROWS ACTUALLY SPLIT THIS WINDOW, AND WHICH MERELY CLIP AN EDGE OF IT

The window is **2010-01-04 to 2026-08-26**, ~4,190 bars, ~16.6 years. A break is only useful as a
pre-registered split if **both** sides carry enough bars to be scored. Taking ~3 years a side as the
crude floor:

### Splits that give two usable regimes

| date | row | years before / after | what it splits |
|---|---|---|---|
| **2013-08-05 → 2014-05-12** | BAR-4 LULD Tier 2 | 3.6 / 12.3 | daily High/Low censoring arrives for the held universe. **Not a date — a NINE-MONTH ramp.** Use **2014-05-12** as the post-date, on the SEC DERA paper's own precedent, and **exclude the ramp** |
| **2013-12-09** | BAR-5 odd lots | 3.9 / 12.7 | **reported daily VOLUME only.** O/H/L/C unaffected. The cleanest *mechanically isolated* break in the calendar |
| **2017-09-05** | CA-2 ex-date T+2 | 7.7 / 9.0 | **the most balanced split in the window.** Corporate actions only |
| **2020-02-24 / 2020-03** | BAR-9 + BAR-10 + BAR-13 | 10.1 / 6.5 | LULD band width, the halt cluster, **and the NYSE floor closure. THREE rule changes and one shock, all inside five weeks** |
| **2025-01-15/17** | CA-4 listing standards | 15.0 / 1.6 | **tail clip**, but the reverse-split/delisting rate changes direction here. Listed among splits because it is the only corporate-action *rate* break in the calendar |
| **2021-09-28** | BAR-11 Rule 15c2-11 | 11.7 / 4.9 | OTC quote availability. Usable by span, but touches **only the dead tail** |

### Splits that merely clip an edge, and cannot carry a two-regime test alone

| date | row | the clip |
|---|---|---|
| 2011-02-28 | BAR-2 Reg SHO 201 | only **1.2 years** before it. Front-edge clip |
| 2010-06/09, 2011-06 | BAR-1 single-stock CBs | 0.4–1.5 years before. Front-edge clip, **and the dates are approvals, not go-lives** |
| 2024-05-28 | CA-3 ex-date T+1 | only **2.2 years** after. Tail clip |
| 2026-03-18 | ED-8 FPI Form 4s | **161 days** after. Tail clip — a warning, not a split |
| 2026-08-01 | T2-1 Rule 605 | **25 days** after. Not a split in any sense |
| 2026-04-27 | T2-3 odd-lot quotes | 4 months after. Not a split |
| 2012-10-29/30, 2018-12-05, 2025-01-09, Juneteenth | BAR-12 | **missing bars, not regimes.** Handle by excluding the date, not by splitting on it |

### And a whole class that is neither: rows that are FILTER-CORRECTNESS problems, not splits

**ED-3a, ED-3b, ED-5, ED-6, ED-7 and ED-8 should not be pre-registered as sample splits at all.**
They do not divide the window into regimes to be compared; they determine **whether a series is
being extracted correctly in the first place**:

- **ED-3a / ED-3b** — a 13D/13G filter must match **both** form-type strings across the whole window,
  and a daily-index-derived series disagrees with a quarterly-index-derived one for twelve months.
- **ED-5** — a new 8-K item code has a **structural zero** before its date; that is not a low base
  rate to be modelled, it is an absence to be excluded.
- **ED-6** — Form 144 before 2023-04-13 is **incomplete by construction**, because paper filings
  never entered EDGAR.
- **ED-7** — the Financial Statement Data Sets **were rewritten retroactively under the same
  filenames**, so a pre-2024-12 number is not reproducible from today's files.
- **ED-8** — a Form 4 count rising in 2026 is a **new population**, not new behaviour.

**Treating any of these as a regime split would be the wrong response.** The right response is to fix
the extraction and, where the earlier data does not exist, to **start the series later** rather than
model a zero.

### And one row that is neither — it is a hole

**BAR-7, the Tick Size Pilot (2016-10-03 → 2018-09-28), does not split the window. It excises a
two-year block from the middle of it, for a named subset of ~1,200 securities.** That makes it the
awkward one to pre-register: the correct handling is **three regimes per affected name** (pre-pilot,
pilot, post-pilot) and **two for everything else** — which is a per-name, not a per-date,
declaration. It is also the row whose treatment population overlaps this programme's universe most
closely, so it is the one least safe to ignore.

### The practical upshot

**If only one split is to be pre-registered, 2013-12-09 and 2017-09-05 are the two strongest
candidates**, for opposite reasons: the first is *mechanically isolated* (volume moves, prices do
not), the second is *temporally balanced* (7.7 / 9.0).

**2020 IS THE MOST DANGEROUS PERIOD IN THE CALENDAR, AND IT IS WORSE THAN IT LOOKED AT THE START OF
THIS LANE.** Not because any single break is large, but because **three rule changes land within five
weeks of a famous shock**, and the shock is the only one usually named:

| date | what | whose names |
|---|---|---|
| 2020-02-24 | LULD bands **halved** at open and close | all Tier 2 — i.e. this universe |
| 2020-03-09/12/16/18 | four MWCB halts | every name |
| 2020-03-23 | **NYSE floor closes; Tape A closes struck by a different auction, collared at 10%** | **NYSE-listed only** |

**The last one introduces a listing-venue asymmetry that exists on neither side of 2020.** So a
2020 result that differs between NYSE- and Nasdaq-listed names has a mechanical explanation before it
has a behavioural one. **The honest treatment of 2020-02-24 → 2020-06-17 is exclusion, not a split** —
the effects are not separable inside this fixture.

**And before any of that: run BAR-12c.** If the four unscheduled-closure dates are present as rows,
the bar index is wrong in four places and every split date above is being applied to a slightly
different panel than intended. **That check costs one query and gates the rest.**

---

## 8. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **The OPERATIVE dates of the three single-stock circuit breaker stages, AND that pilot's trigger
   threshold and pause length (BAR-1).** I have the approval dates from a primary source. I do
   **not** have the dates the pauses began operating, which were later than approval and were
   themselves phased; nor did I verify the "10% in five minutes / five-minute pause" parameters from
   any primary document. The one SEC page that would have given the stage-1 go-live returned
   **HTTP 403** (§0, block 1). **BAR-1's dates are approvals and must not be used as break dates
   without further work.**
2. **WHICH amendment extended LULD bands from 9:30–3:45 to 9:30–4:00, and on what date (BAR-4).** I
   now have the endpoint — the SEC DERA paper puts **full implementation at 2014-05-12** — but **not
   the individual amendment dates inside the 2013-08-05 → 2014-05-12 ramp.** So I can bound the ramp
   but not describe its interior, and a study needing per-name treatment status inside those nine
   months cannot get it from this brief.
3. **The per-name Tick Size Pilot group assignments (BAR-7).** The lists were published by the
   primary listing exchanges and by FINRA. I did not retrieve them. **Without them the pilot is a
   date range, not a treatment indicator**, and the date range is the weaker object.
4. **The magnitude of the 2013-12-09 odd-lot volume step.** I established the mechanism and the
   direction from primary documents. I have **no** external estimate of how large the step is, in
   aggregate or by price decile. This is measurable from the programme's own data and is not
   something I can supply.
5. **The Reg SHO Rule 201 effective date**, on which two primary SEC releases disagree (BAR-2).
   Unresolved and flagged rather than papered over.
6. **WHY seven `SC 13D/A` filings still appear in 2025 Q1** after the mandatory 2024-12-18 date
   (ED-3a). The *EDGAR Release 24.4* announcement hints at it — *"Certain Schedule 13D amendments may
   continue to be filed in HTML, see EDGAR Filer Manual for more details"*, consistent with the
   combined 13D-plus-Schedule-TO carve-out in Rel. 33-11253 — but **the Filer Manual chapter was not
   opened to confirm that this explains these specific seven.** The *existence* of the stragglers is
   established from the index files; only the *reason* is not.
7. **The exact date EDGAR widened the form-type column in the daily `form.idx` / `company.idx`
   (ED-3b).** Bracketed to **2024-12-20 (still truncated) → 2024-12-23 (fixed)** from the archived
   files themselves. **No official announcement dating it could be found**, so the intervening
   weekend cannot be resolved. The break itself is solid; its closing date is a two-day bracket.
8. **The launch date of the current EDGAR full-text search system.** Its *coverage* is established
   from sec.gov — *"the full text of all EDGAR filings submitted electronically since 2001"* — but
   the launch date is **absent from all 194 entries of the official EDGAR News & Announcements
   archive**, and no SEC press release or Federal Register notice for it could be found. Only
   third-party claims exist, and they are not cited here. **Logged block, by tool and response:**
   `curl` to `https://efts.sec.gov/LATEST/search-index?q=…` with the project User-Agent returns an
   Akamai **`Access Denied`**, unchanged by `Accept: application/json`, `--compressed`, or a
   `Referer` header — so the earliest indexed filing could not be bracketed empirically either.
   Naming the tool and not the host: the refusal is against this curl client on that path;
   `www.sec.gov` and `govinfo.gov` served everything else with the same User-Agent.
9. **The day of the month in December 2024 on which the Financial Statement Data Sets were
   reprocessed (ED-7).** The official page gives the month only, and the ZIPs carry no version
   field, so **pre- and post-reprocessing vintages cannot be told apart by inspection.** This is the
   single least satisfying row in the calendar: the break is large, retroactive, and undated to
   better than a month.
10. **Whether EDGAR Next changed any public filing metadata (T2-4).** Nothing in the adopting release
    does, and daily filing counts show no level shift at 2025-09-15 — but that is **a negative from
    absence in one document plus one empirical check**, not an affirmative statement that public
    metadata is unchanged.
11. **Item 5.02(e)'s 2006 history beyond Federal Register metadata.** Dated to 69 FR 15594
    (2004-03-25), with the effective date set to 2004-08-23 by a correction at 69 FR 48370 — **from
    the FR index, not from reading the release PDFs.** Out of window regardless.
12. **FIRST-TRADING DATES FOR EVERY NEW EXCHANGE IN THE WINDOW.** SEC **registration** orders are
    solid — IEX **2016-06-17** (Rel. 34-78101), LTSE **2019-05-10** (34-85828), MEMX **2020-05-04**
    (34-88806), MIAX Pearl equities rules **2020-08-20** (34-89563), 24X **2024-11-27** (34-101777),
    Green Impact Exchange 2025-04-17, TXSE **2025-09-30** (34-104146). **The dates these venues
    actually began trading equities are NOT established** for IEX, LTSE, MEMX, NYSE National's
    relaunch, or Green Impact Exchange; MIAX Pearl's 2020-09-25 and TXSE's 2026-07-02/17 are
    *"anticipated"* in forward-looking statements, not confirmations. **Registration is not
    operation**, and for a vendor's exchange-code field only operation matters.
13. **NSX's 2015 resumption and 2017 final cessation**, the SEC order approving the NYSE/ICE
    acquisition of NSX, **NYSE National's 2018 relaunch date**, and **CBOE Stock Exchange (CBSX)'s
    closure date.** Only NSX's **2014-05-30** cessation is hard. Not reached.
14. **The date the NYSE trading floor FULLY reopened (BAR-13).** As late as **2022-04** the Rule
    7.35A/7.35C relief was still expressed as ending *"on the earlier of a full reopening of the
    Trading Floor facilities to DMMs or after the Exchange closes on July 31, 2022"* (Rel. 34-94619).
    **So the end of the altered-closing-price regime is not dated**, only its phased reopening
    (2020-05-26, 2020-06-17). **Treat the post-2020-06-17 period as partially treated.**
15. **Whether the SEC lifted the stay on Nasdaq's $5M MVLS rule (§6.12) before 2026-08-26.** The SRO
    index lists no later Commission order, but **no affirmative primary document confirms the stay
    remained in force** on that date. **If it was lifted in August 2026, that rule's operative date
    moves inside the window — verify before using it.**
16. **OPERATIVE dates for five of the six listing-standard rows in CA-4.** Only SR-NASDAQ-2020-001
    states one. SR-NASDAQ-2023-025, -2024-029, -2024-045 and SR-NYSE-2024-48 give **approval dates
    only**; the real operative dates live in Nasdaq Listing Center notices and NYSE trader updates
    that were not retrieved. **This matters most for the 2025-01-17 one-year reverse-split look-back,
    the highest-leverage rule in that row.**
17. **Whether any Form SD resource-extraction disclosures were actually filed** under the 2020 rule
    from 2024-09-30 (§6.11); **the exchanges' actual Rule 10D-1 clawback listing-standard effective
    date** (commonly cited as 2023-10-02 — only the SEC's outer bound of 2023-11-28 was verified); and
    **whether MDI odd-lot information went live on the first business day of May 2026.** Rel. 34-104172
    conspicuously does *not* exempt the odd-lot requirements, which is strong negative evidence that
    they did go live, **but no primary document confirms it. Treat 2026-05-01 as inferred.**
18. **Two court dates rest on secondary records:** the D.C. Circuit's **2025-10-14** denial of the
    Reg NMS tick-size petition (*Cboe Global Markets v. SEC*, No. 24-1350) is taken from **the SEC's
    own order**, not the opinion; and *NAM v. SEC*, 800 F.3d 518 (2015-08-18) from a citation record.
19. **Listing-standard changes at NYSE Arca, Cboe BZX and IEX** were not searched — scope was NYSE,
    NYSE American and Nasdaq only.
20. **NO ROW STATES A MAGNITUDE.** Every mechanism here is established; **not one break is
    quantified** — not the odd-lot volume step, not the change in pause rates, not the spread widening
    under the tick pilot, not the reverse-split rate change. That is the correct division of labour
    (magnitudes live in the programme's data, not in mine), but it means **no row in this calendar can
    tell you whether a break is large enough to matter.** Each is a reason to pre-register a split,
    **not evidence that the split will move a number.**
21. **AND THE ONE THING THIS BRIEF ASSERTS ABOUT THE PROGRAMME'S OWN DATA IS A PREDICTION, NOT A
    FINDING.** BAR-12c's arithmetic (4,187 sessions, or 4,191 with the closure rows) is computed from
    an externally verified holiday calendar. **I hold no fixture and have checked nothing against
    one.** If the bar count disagrees, the holiday calendar above is the thing to re-derive first —
    not the fixture.
