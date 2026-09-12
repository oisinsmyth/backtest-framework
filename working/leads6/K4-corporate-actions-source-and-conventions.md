# K4 — Corporate actions: the SOURCE question, and the CONVENTIONS above the arithmetic

External-evidence brief. Round 6. Written 2026-09-10.
**I have no access to the programme's data and claim nothing about it.** Every number below is
either from a cited external source — tagged by TYPE and separately by HOW WELL I ESTABLISHED IT,
with the establishment tag in the same sentence as the number — or from a live probe I made myself,
in which case the exact call and the **negative control** are named in §9 so it can be re-run.

**Scope honoured.** The adjustment *arithmetic* (round 3's `G6`) is treated as known background.
This brief is about **the series, its identifiers, its dates and its type codes** — what the file
*is*, not how you multiply prices with it.

---

## 0. THE ANSWER TO THE BAR, FIRST

**No free, dead-inclusive, point-in-time source for US equity splits and distributions exists.** I
probed eight candidates live on named dead issuers. Every one failed, and **three failed in the
specific way that is worse than failing**: they returned **HTTP 200 with a different company's
data**.

| candidate | dead-name probe | result |
|---|---|---|
| Yahoo `v8/finance/chart` `events=div,split` | `TWTR` | **HTTP 404**, `"No data found, symbol may be delisted"` |
| `api.nasdaq.com/.../dividends` | `SHLDQ`, `BBBYQ`, `SIVBQ`, `SVB` | **HTTP 000 on all four** — no response, no bytes |
| Nasdaq Trader Daily List files | direct file paths | **302 → 404 handler**; site retired. Product is **PAID** |
| NYSE Corporate Actions | product page | **PAID** ("Purchase Now") |
| DTCC T+1 Dividend Processing FAQ | PDF | **404** (curl *and* WebFetch), 108 KB HTML handler body |
| stockanalysis.com | `BBBY` → **404**; `SHLD` → **200, Global X Defense Tech ETF** |
| dividendhistory.org | `BBBY` → **200, correct**; `SHLD` → **200, Global X Defense Tech ETF**; `SIVB` → 404 |
| stocksplithistory.com | `SHLD` → **200, two issuers blended in one document** |
| EODHD | `AAPL` demo → 200; `SHLD` → **403 plan gate** |
| Alpha Vantage | `IBM` demo → 200; `BBBY`/`SHLD` → **200 with a registration prompt as the body** |
| Polygon / Massive | **API key required; unprobed → counted as FAILURE** |

**What *does* exist free and dead-inclusive is SEC EDGAR, and it is CIK-keyed, which is the one
thing none of the others are.** But EDGAR cannot supply the field a backtest actually needs. That
is §2, and it is the central structural finding of this lane:

> **Rule 10b-17(b)(1) enumerates the fields an issuer must notify — declaration date, record date,
> payment-or-delivery date, amount, rate, fractional settlement, conditions, transfer agent — and
> the EX-DATE IS NOT AMONG THEM.** The ex-date is *designated* by the exchange or by FINRA's UPC
> Committee under Rule 11140(a), not declared by the issuer. **So the only free dead-inclusive
> source structurally cannot carry the only date the price file joins on.** A second corporate-action
> source is not merely unavailable here — for the ex-date it is unavailable *in principle* from
> issuer documents.

---

## 1. THE SOURCE QUESTION — every probe, and what came back

All probes made 2026-09-10 with `User-Agent: backtest-framework-research/1.0
(research@backtest-framework.org)` (SEC calls used the SEC-required contact form of the same
mailbox). **No account was created, no key was registered, no form was submitted.**

### 1.1 The probe set, and an honesty correction to it

The commissioning note named Sears Holdings, Bed Bath & Beyond, Twitter and SVB Financial as probes.
**Three of the four never paid a common cash dividend** (Sears, Twitter, SVB Financial). So their
*absence from a dividend source is correct behaviour, not a coverage gap*, and I do not score it as
one. Only **BBBY** is a valid dividend probe. **Sears is the valid *distribution* probe** — it had
the Lands' End and Sears Hometown separations and the Sears Canada rights offering — and Sears is
where the sources failed hardest.

### 1.2 Yahoo — 404s the dead, and says so [MEASURED IN BRIEF]

```
GET query1.finance.yahoo.com/v8/finance/chart/TWTR?...&events=div%2Csplit
→ HTTP 404, 108 bytes
{"chart":{"result":null,"error":{"code":"Not Found","description":"No data found, symbol may be delisted"}}}
```
Clean, honest failure. This is the *good* kind: the source tells you it has nothing. Confirms round
4's `H5` result for prices extends to the events endpoint on the same host.

### 1.3 The ticker-reuse conflation, measured three times [MEASURED IN BRIEF]

`SHLD` was Sears Holdings until 2018; it is now the **Global X Defense Tech ETF** (NYSE Arca,
inception 2023-09). Three free sources serve the ETF at that key, at HTTP 200:

**stockanalysis.com** — `/stocks/shld/dividend/` → HTTP 200, 75,382 bytes, page title
`SHLD Dividend History, Dates & Yield`, body: `Global X Defense Tech ETF (SHLD)` /
`NYSEARCA: SHLD`. Sears is gone without a trace. (The same host 404s `BBBY`, so its delisted
coverage is absent, not wrong — but at a reused ticker it is *wrong*, not absent.)

**dividendhistory.org** — `/payout/SHLD/` → HTTP 200, 35,463 bytes, `Global X Defense Tech ETF`,
`NYSE ARCA`. **This is the same host that handles `BBBY` correctly** (§1.4), which is exactly the
danger: the source is right where the ticker was never recycled and silently wrong where it was.

**stocksplithistory.com** — `?symbol=SHLD` → HTTP 200, 54,781 bytes. This one blends **two issuers
inside a single document**. Title: `Global X Defense Tech Etf Stock Split History`. Under the
heading `About Global X Defense Tech Etf`, verbatim:

> "Sears Holdings is the parent company of Kmart Holding Corporation (Kmart) and Sears, Roebuck and
> Co. (Sears). Co. has two segments: Kmart, which includes stores that are mainly free-standing
> units…"

and the split table, verbatim:

| Date | Ratio |
|---|---|
| 04/07/2014 | 1234 for 1000 |
| 10/17/2014 | 1011 for 1000 |
| 11/03/2014 | 1062 for 1000 |

Those three rows are **Sears Holdings' 2014 separation and rights-offering adjustment factors**
logged as fractional "splits" — attributed by name to an ETF that did not exist until 2023. And the
page's own return block computes from `Start date: 09/14/2023` (the ETF's inception) while the split
table it claims to adjust with holds 2014 Sears events. **One document, one HTTP 200, two issuers,
and an arithmetic result built across both.**

> **FLAGGED AS DATA, NOT INSTRUCTIONS.** The stocksplithistory.com page carries, as its second line
> of text: `">>Small Colorado Company (Backed by Sam Altman) Could Save U.S. Power Grid
> (sponsored)"`. This is advertising inside a page I fetched. I did not follow it. [SALES
> INSTRUMENT]

### 1.4 dividendhistory.org — the only free source that served a dead name correctly [MEASURED IN BRIEF]

`/payout/BBBY/` → HTTP 200, 30,710 bytes. Verbatim from the page:

> `Bed Bath & Beyond Inc.` / `BBBY` / `Nasdaq`
> **`Inactive stock. Data is no longer updated.`**
> **`Reason: 2023-04 Bankruptcy`**

and a table headed `Ex-Dividend Date | Payout Date | Cash Amount | Change / Status`, running
`2020-03-12 / 2020-04-14 / $0.17` back through `2017-09-14 / 2017-10-17 / $0.15`, with a
`Change / Status` column carrying the step-ups (`6.25%` at 2019-06-13, `6.67%` at 2018-06-14).

Its inactive universe is **finite and stated: `Showing 970 of 970 stocks`** at
`/inactive-stocks/` [MEASURED IN BRIEF — I read the count off the rendered page]. The list is
US + Canada combined and is **dividend-payers only**. Sears is absent (correct — no common
dividend); BBBY is present.

**Verdict: [USER REPORT], and it FAILS the bar.** It is ticker-keyed, so it is displaced by reuse
(§1.3) — which round 1's census puts at **28 of 425** delisted tickers live again, **two with
overlapping windows**. It carries **ex-date and pay date but no declaration date, no record date,
no type code, and no splits at all**. 970 names over two countries cannot cover a ~562-name dead
cohort's distributions. And I cannot establish its provenance, its vintage, or whether any row was
ever revised. **It is a hand-check tool for one name, not a second source.**
Negative control: `/payout/ZZZZQQFAKE/` → **HTTP 404, 18,737 bytes** — same byte count as the `SIVB`
404, so the handler is uniform and the 404 is real. [MEASURED IN BRIEF]

### 1.5 The exchange files: the right data, and it is for sale

**Nasdaq Daily List** [VENDOR OFFICIAL DOC — spec read in full, product page read in full]. This is
the authoritative file and its own product page says so: it *"Provides notification of cash
dividends, stock dividends and stock splits to Nasdaq securities"*, with *"historical corporate
action data dating back to 1999"*. Access is by **"a secured FTP interface"** and a **"secured
website interface"**; the spec's path strings read
`IPAddress\Trader\DailyList\Dividends\dimmddyyyy` with the note *"The actual IP Address is only
provided when the requisite documents have been completed and the user ID/password has been
assigned."* It is **priced** — Nasdaq filed a fee reconfiguration for the Daily List in 2024
[PRIMARY DATA DOC, Federal Register — title read, document not opened]. Direct file paths under
`nasdaqtrader.com/dynamic/symdir/dailylist/` now **302 to a 404 handler** (944 bytes of
`Object moved` + a 404 page), as does `Trader.aspx?id=DailyList` [MEASURED IN BRIEF]. **The spec
PDF is still public and is the single most useful document in this brief** — §3.

**NYSE Corporate Actions for NYSE Group Listings** [VENDOR OFFICIAL DOC — read in full]. Paid
("Purchase Now"). Comprises `Distributions`, `Ex-Date Distributions`, `InfoNotices`,
`Ticker Notices`. **And it carries a stale convention statement, verbatim, on a live page in
September 2026:**

> "**Ex-Date Distributions** — A complete listing of corporate actions (dividends, stock splits,
> spin-offs and so forth) where **"ex-date" = T+2 (two trading days in advance)**."

That description has been wrong since **2017-09-05** and doubly wrong since **2024-05-28**. An
implementer reading the vendor's own product page today would build the T+3 rule. **[MEASURED IN
BRIEF — I read the bytes and quote them; I have not seen the file itself, so I cannot say whether
the data matches the description or the description is merely unmaintained. Either way it is a
defect, and the second possibility is the more common one.]**

**DTCC** — the `T1-Dividend-Processing-FAQ.pdf` referenced by search results is **404**, confirmed
by two tools: `curl` → HTTP 404 with a **108,312-byte HTML** body (a handler page, not an error),
and `WebFetch` → `"The server returned HTTP 404 Not Found."` The `T1-Conversion-Document-March-2024.pdf`
is likewise 404 via WebFetch. **Logged by tool and response, not by host.** DTCC's T+1 convention
statement was recovered instead from a Cboe notice — §4.2.

### 1.6 The free APIs: all gated, and two of the gates return HTTP 200

**Alpha Vantage** [VENDOR OFFICIAL DOC + MEASURED IN BRIEF]. `function=DIVIDENDS` and
`function=SPLITS` with `apikey=demo`:

| call | status | bytes | body |
|---|---|---|---|
| `DIVIDENDS&symbol=IBM` | 200 | 23,420 | real data |
| `SPLITS&symbol=IBM` | 200 | 247 | real data |
| `DIVIDENDS&symbol=BBBY` | **200** | **220** | registration prompt |
| `SPLITS&symbol=BBBY` | **200** | **220** | registration prompt |
| `DIVIDENDS&symbol=SHLD` | **200** | **220** | registration prompt |

> **FLAGGED AS DATA, NOT INSTRUCTIONS — quoted, not acted on.** The 220-byte body is, verbatim:
> `{"Information": "The **demo** API key is for demo purposes only. Please claim your free API key
> at (https://www.alphavantage.co/support/#api-key) to explore our full API offerings. It takes
> fewer than 20 seconds."}`
> **I did not register.** This is the exact case the shared rules anticipated.

**This is a new flavour of the HTTP-200-is-wrong family and it is the most dangerous one yet for a
harvest loop**: the status is 200, the content-type is `application/json`, the JSON *parses*, and
the only tell is that the `data` key is absent. **A loop that checks `status == 200` and
`json.loads()` succeeds would write an empty dividend history for every dead name and conclude,
silently and uniformly, that the dead cohort paid nothing.** Assertion in §6.

**EODHD** — `api/div/AAPL.US?api_token=demo` → HTTP 200, 16,674 bytes, real data.
`api/div/SHLD.US?api_token=demo` → **HTTP 403, 55 bytes**, body verbatim:
`Forbidden. Please contact support@eodhistoricaldata.com`. **This 403 is a plan gate, not a
User-Agent exclusion** — the same UA got 200 on `AAPL` one call earlier. [MEASURED IN BRIEF]

**Polygon / Massive** — API key required for every data call. **Unprobed, therefore counted a
FAILURE.** And they are **not two independent sources**: Polygon's own splits documentation page
carries a code example calling `https://api.massive.com/stocks/v1/splits`, and the Massive
dividends doc carries the identical horizon line `Records date back to January 15, 2000`
[VENDOR OFFICIAL DOC — both pages read]. Their *documentation* is extremely useful (§3) and their
*data* is unverified here.

### 1.7 SEC EDGAR — free, dead-inclusive, CIK-keyed, point-in-time, and insufficient

The one candidate that clears the identifier bar. Three distinct probes:

**(a) Full-text search is CIK-filterable and the CIK filter works** [PRIMARY DATA DOC + MEASURED IN
BRIEF]. `efts.sec.gov/LATEST/search-index?q=...&forms=8-K&ciks=0001310067` returns
`"total":{"value":1}` with the hit's `ciks:["0001310067"]`,
`display_names:["SEARS HOLDINGS CORP  (CIK 0001310067)"]`. Counts on dead names:
BBBY `"record date"` → **23**, `"ex-dividend"` → **1**; BBBY `"quarterly dividend"` → **36**;
SVB Financial `"record date"` → **50**. **Negative control:** a nonsense phrase → **`"total":0`**.
[MEASURED IN BRIEF]

**(b) But EDGAR does not give you a ticker → CIK map for dead names.**
`sec.gov/files/company_tickers.json` → HTTP 200, 796,513 bytes, **10,407 rows, 10,407 distinct
tickers, and it contains NONE of `SIVB`, `SIVBQ`, `BBBY`, `BBBYQ`, `TWTR`, `SHLD`, `SHLDQ`.** The
file is **survivor-only**. And `data.sec.gov/submissions/CIK…json` reports `tickers: []` and
`exchanges: []` for **all four** dead probes. [MEASURED IN BRIEF]
Two further identifier facts fell out of the same probe:
- **The issuer NAME moves too.** CIK 0000886158 is now `"20230930-DK-Butterfly-1, Inc."` with
  `formerNames: ["BED BATH & BEYOND INC"]`; CIK 0000895126 (Chesapeake) is now
  `"EXPAND ENERGY CORPORATION"`.
- **Where EDGAR *does* show a dead ticker, it shows the TERMINAL one.** FTS display names render
  `SVB FINANCIAL GROUP  (SIVBQ)` — the post-bankruptcy OTC symbol, **not the `SIVB` under which the
  name traded in a 2010–2023 panel.**

**(c) XBRL company-concept facts are dead-inclusive and structured** [PRIMARY DATA DOC + MEASURED
IN BRIEF]. `data.sec.gov/api/xbrl/companyconcept/CIK…/us-gaap/…`:

| CIK / name | tag | result |
|---|---|---|
| 0000886158 BBBY | `CommonStockDividendsPerShareDeclared` | **200, 101 facts** |
| 0000719739 SVB | same | **404** |
| 0001045810 NVDA | `StockholdersEquityNoteStockSplitConversionRatio1` | **200, 7 facts** |
| 0000895126 Chesapeake→Expand | same | **200, 2 facts**, `val: 0.005`, `end: 2020-04-14` |
| 0000886158 BBBY / 0001310067 Sears | same | **404** (neither split — correct) |

So the **amount** and the **ratio** are recoverable free, for dead names, keyed on CIK, with a
`filed` timestamp that makes them genuinely point-in-time. **The DATES are not.** BBBY's facts are
fiscal-period aggregates (`start: 2016-02-28, end: 2016-05-28, val: 0.125`). NVDA's 10-for-1 is
tagged `start: 2024-05-01, end: 2024-05-31, val: 10` — **a calendar month, and the actual ex-date
(2024-06-10) falls outside it.** NVDA's 2021 4-for-1 appears with two different `end` values
(`2021-06-03` and `2021-07-19`) and **neither is its ex-date (2021-07-20)**. The same fact repeats
across four filings with different `fy`/`fp`, so the series is not one-row-per-event.

**Verdict: a RATIO and AMOUNT cross-check, never a date source.** Which is still worth having —
§6.8, §6.9.

---

## 2. WHY NO ISSUER-SOURCED FEED CAN CARRY THE EX-DATE — from the rule text

**17 CFR § 240.10b-17, "Untimely announcements of record dates"** [PRIMARY DATA DOC, eCFR API,
version 2026-01-01 — read in full]. Paragraph (b)(1) lists what notice must contain. Verbatim, the
whole enumeration:

> "(i) Title of the security to which the declaration relates;
> (ii) Date of declaration;
> (iii) Date of record for determining holders entitled to receive the dividend or other
> distribution or to participate in the stock or reverse split;
> (iv) Date of payment or distribution or, in the case of a stock or reverse split or rights or
> other subscription offering, the date of delivery;
> (v) For a dividend or other distribution including a stock or reverse split or rights or other
> subscription offering: (a) In cash, the amount of cash to be paid or distributed per share,
> except if exact per share cash distributions cannot be given because of existing conversion
> rights … then **a reasonable approximation of the per share distribution may be provided** so
> long as the actual per share distribution is subsequently provided on the record date,
> (b) In the same security, the amount of the security outstanding immediately prior to and
> immediately following the dividend or distribution and the rate of the dividend or distribution,
> (c) In any other security of the same issuer, the amount to be paid or distributed and the rate …,
> (d) In any security of another issuer, the name of the issuer and title of that security, the
> amount to be paid or distributed, and the rate … and if that security is a right or a warrant,
> the subscription price,
> (e) In any other property … the identity of the property and **its value and basis for assigning
> that value**;
> (vi) Method of settlement of fractional interests;
> (vii) Details of any condition which must be satisfied or Government approval which must be
> secured to enable payment of distribution; and in
> (viii) The case of stock or reverse split in addition to the aforementioned information;
> (a) The name and address of the transfer or exchange agent"

and the timing: notice *"no later than 10 days prior to the record date involved"*.

**Declaration, record, pay-or-delivery. No ex-date.** And the FINRA UPC FAQ confirms where it comes
from instead — verbatim [PRIMARY DATA DOC, FINRA, read in full]:

> "**2. What is an "ex-dividend date"?** The date on or after which a security begins trading
> without the dividend (cash or stock) included in the contract price. Please refer to FINRA Rule
> 11140 to see how an ex-dividend date is set."

**Consequence for this programme.** Any cross-check built on issuer filings can verify **amount,
ratio, record date and pay date** and can *derive a predicted* ex-date from the 11140 arithmetic —
but it can never *observe* one. **The ex-date is the one field that has no free second source at
all**, and therefore the one field where a single-source discipline (§6) has to do all the work.

---

## 3. THE CONVENTION QUESTION — which date does a feed key on, and is the ex-date computed or published

### 3.1 The exchange's own file — Nasdaq Daily List spec

[VENDOR OFFICIAL DOC, `nasdaqtrader.com/content/technicalSupport/specifications/dataproducts/dlspec_1130prior.pdf`,
HTTP 200, 234,653 bytes, 22 pages, extracted with `pypdf` — **read in full**. Page footers read
`Updated: November 1, 2011` and `Updated: May 30, 2012`, so this is the vintage spec, not today's.]

**It keys on nothing permanent.** Record layout, verbatim:

> `Daily List Date | Market Category | Issue Symbol | Company Name | Declaration Date | Amount |
> Payment Freq | X-Date | Record Date | Payment Date | NOTES for Each Dividend | Dividend Type Id |
> Stock Amount | Cash Amount | CUSIP | QualDiv | Index | Rights Basis Notes | Rights Exercise Price
> Amount | Rights Expiration Date | Net Amount`

`Issue Symbol` is *"The symbol of the issue experiencing the dividend."* `CUSIP` is available only
in the licensed variant and is *"the CUSIP effective on the date the NASDAQ Dividend Daily List is
published"* — i.e. **point-in-time, and it changes across corporate actions**. There is no permanent
issuer id in the file at all.

**It carries all four dates, and keys the RECORD on the announcement day.** `Daily List Date` is
*"The date and time the NASDAQ Daily List was distributed"*; the four event dates are separate
fields. So the exchange's file is an **announcement stream**, not an event table: one row is
*"what we published on day D"*, and the event it describes sits in the future.

**The ex-date is PUBLISHED, and it is the authority — and the spec says explicitly that the AMOUNT
and the ADJUSTMENT FACTOR can disagree.** This is the single most load-bearing paragraph I found.
Verbatim, `Stock Amount`:

> "When applicable, a numeric factor relating the ratio of the stock dividend. For Example: The
> factor for a 2/1 stock split would be 2 · The factor for a 2/1 reverse split would be .5 · The
> factor for a 3/2 stock split would be 1.5 · The factor for a stock dividend of 10% would be 1.10.
>
> **The factors reflect the amount that NASDAQ adjusted the stock price by on the X-Date. In cases
> where the Factor values differ from the Amount values, the factor will always take precedence.**
> This occurs frequently with ADS and ADR issues types; where NASDAQ is occasionally obligated to
> adjust on X-Date based on an approximate value. Other cases can result from truncation or
> rounding, but the factor will always reflect the field the stock price is adjusted by. **Also,
> please note that entries without an X-Date do not get adjusted, even though a factor may be
> provided.**"

Three separate assertable facts in one paragraph:
1. **The factor, not the stated amount, is what the price series was adjusted by.** They are
   different quantities and the exchange says so.
2. **A row can carry a factor and NO X-Date, and that row must NOT be applied.** A loader that
   iterates rows and applies every non-null factor will corrupt the series.
3. The ADR/ADS case is an **approximation**, consistent with 10b-17(b)(1)(v)(a)'s approximation
   clause.

**The announcement can be cancelled.** The Next-Day X-Date list carries `CancelOrder`:
*"This field will indicate if open orders should be cancelled. Allowed Values: Y – Yes, N – No"* —
and `New TSO`: *"The resulting Total Shares Outstanding (TSO) value due to the Stock Dividend or
Stock Split occurring for this issue."*

**`Amount` is not a number.** Verbatim: *"The amount of a dividend. The following codes are used:
apx = approximate · ann = annual · cdn = Canadian · ext = extra · fnl = final · inc = Increase ·
SA = semiannual · stk = stock div · spl = special"*. The numeric value lives in `Cash Amount` /
`Stock Amount`; `Amount` is a free-ish field that can hold a code. **And `Cash Amount` is GROSS:**
*"In instances where a NASDAQ-listed issue has declared a dividend that is subject to certain taxes
and fees and there is a GROSS amount and a NET amount, this field will represent the GROSS amount"*,
with a separate `Net Amount` that *"will be blank"* if there is only a gross.

**And the dates inside a future-effective row are AS OF THE PUBLICATION DAY, not the event day.**
From the equities section, verbatim:

> "From this point on, all data is as of the NASDAQ Daily List Date - not the Effective date. For a
> future effective NASDAQ Daily List entry, these fields will be the CURRENT Day not the future
> Effective Date. For instance, **for a Symbol Change due to a stock split, the following data
> fields will be the current information not the next day's resulting information that is based on
> the stock split.**"

### 3.2 The vendor layer — three feeds, three different keys, and one that is a cadence label

**Polygon / Massive dividends** [VENDOR OFFICIAL DOC — page read in full]. Keys on `ticker`;
*"The sort column defaults to 'ticker' if not specified"*. `Records date back to January 15, 2000`.
Fields and their verbatim descriptions:

| field | verbatim |
|---|---|
| `ex_dividend_date` | "Date when the stock begins trading without the dividend value" |
| `record_date` | "Date when shareholders must be on record to be eligible for the dividend payment" |
| `pay_date` | "Date when the dividend payment is distributed to shareholders" |
| `declaration_date` | "Date when the company officially announced the dividend" |
| `cash_amount` | "Original dividend amount per share in the specified currency" |
| `split_adjusted_cash_amount` | "Dividend amount adjusted for stock splits that occurred after the dividend was paid, expressed on a current share basis" |
| `historical_adjustment_factor` | "Cumulative adjustment factor used to offset dividend effects on historical prices. To adjust a historical price for dividends: for a price on date D, find the first dividend whose `ex_dividend_date` is after date D and multiply the price by that dividend's `historical_adjustment_factor`." |
| `frequency` | "How many times per year this dividend is **expected** to occur… depending on the issuer's declared **or inferred** payout cadence" |
| `distribution_type` | "Classification describing the nature of this dividend's **recurrence pattern**: recurring … special … supplemental … irregular … unknown (cannot be classified from available data)" |

**Two things matter here.** First, **`distribution_type` classifies CADENCE, NOT ECONOMICS.** There
is no code for return-of-capital, stock dividend, spin-off or rights. A consumer of this endpoint
cannot distinguish a $3.00 ordinary dividend from a $3.00 return of capital, and the doc says so by
omission and says `frequency` is *inferred* by the vendor in so many words. Second, **every single
response attribute is marked `optional`** — including `ex_dividend_date`, `record_date`, `pay_date`
and `cash_amount`. Nulls in the join key are the documented norm.

**Polygon / Massive splits** [VENDOR OFFICIAL DOC — read in full]. `Records date back to October 25,
1978` — **a different horizon from the dividends endpoint in the same product**. Sorts on
`execution_date.desc`. Verbatim:

> "`execution_date`: Date when the stock split takes effect. **The adjustment is applied overnight.
> On the prior trading day, the post-market session is the last session that shows pre-split prices.
> On the execution date, all trading is already adjusted for the split. This includes the pre-market
> session.**"

and `split_from` = *"Denominator of the split ratio (old shares)"*, `split_to` = *"Numerator of the
split ratio (new shares)"*. **Note what is absent: no record date, no pay date, no declaration date,
no type.** §4.1 is why that matters.

**Alpha Vantage** [VENDOR OFFICIAL DOC + MEASURED IN BRIEF]. `DIVIDENDS` carries
`ex_dividend_date`, `declaration_date`, `record_date`, `payment_date`, `amount`. `SPLITS` carries
**only** `effective_date` and `split_factor`. Live `IBM` response:

```
{"ex_dividend_date": "2026-08-10", "declaration_date": "2026-07-22",
 "record_date": "2026-08-10", "payment_date": "2026-09-10", "amount": "1.69"}
{"ex_dividend_date": "2026-05-08", ... "record_date": "2026-05-08", ...}
```

**`ex_dividend_date == record_date` in both rows.** That is the post-2024-05-28 regime, observed
live in a vendor feed, and it is the cleanest available demonstration that the ex-date in these
feeds is the **published** one rather than a stale computation from the record date.

**EODHD** [VENDOR OFFICIAL DOC + MEASURED IN BRIEF]. Live `AAPL` demo row:
```
{"date":"1987-05-11","declarationDate":"1987-04-22","recordDate":"1987-05-15",
 "paymentDate":"1987-06-15","period":null,"value":0.00054,"unadjustedValue":0.12096,"currency":"USD"}
```
The primary `date` is the **ex-date**; `value` is **split-adjusted**, `unadjustedValue` is as-paid.
Ratio here is 224× — Apple's cumulative split factor since 1987. **A feed that carries both and a
consumer that picks the wrong one is off by the whole split history**, and the field that *looks*
like the amount (`value`) is the adjusted one.

### 3.3 Direct answers to the lane's convention questions

**Which date does a corporate-action feed key on?** *Three different answers.* The exchange file keys
the **row** on the publication day (`Daily List Date`) and carries all four event dates as payload.
A vendor dividend endpoint keys/sorts on **ticker**, with the ex-date as a filterable attribute. A
vendor split endpoint keys on **`execution_date`** and carries **no other date at all**. There is no
shared convention, and the split and dividend series of the *same vendor* do not even share a
horizon (1978 vs 2000).

**Is the ex-date stored as the vendor computed it or as the exchange published it?** **As published,
for the ex-date.** Nasdaq's own spec grounds the factor in *"the amount that NASDAQ adjusted the
stock price by on the X-Date"*; Alpha Vantage's live `IBM` rows show `ex == record` rather than
`record − 1`, which a stale computation would have produced. **But the AMOUNTS and the TYPE LABELS
are vendor-computed and the vendors say so**: `split_adjusted_cash_amount` and `value` are derived,
`frequency` is *"inferred"*, `distribution_type` is *"cannot be classified from available data"* at
the bottom of its enum, and Nasdaq warns that its own `Amount` and its own factor disagree *"in
cases where the Factor values differ from the Amount values"*. **The date is observed; the economics
are modelled.** That is the asymmetry to carry.

---

## 4. THE 25% INVERSION, AND THE THREE REGIMES

### 4.1 Rule 11140(b)(2), from the rule text, and what it does to a join

**FINRA Rule 11140** [PRIMARY DATA DOC, finra.org, HTTP 200, 89,384 bytes — **read in full**],
current text, verbatim:

> "**(b) Normal Ex-Dividend, Ex-Warrants Dates**
> (1) In respect to cash dividends or distributions, or stock dividends, and the issuance or
> distribution of warrants, which are **less than 25 percent** of the value of the subject security,
> if the definitive information is received sufficiently in advance of the record date, the date
> designated as the "ex-dividend date" shall be **the record date** if the record date falls on a
> business day, or the **first business day preceding** the record date if the record date falls on
> a day designated by the Committee as a non-delivery date.
> (2) In respect to cash dividends or distributions, stock dividends and/or splits, and the
> distribution of warrants, which are **25 percent or greater** of the value of the subject
> security, the ex-dividend date shall be **the first business day following the payable date**.
> (3) In respect to stock dividends and/or splits relating to American Depository Receipts (ADRs)
> and foreign securities, the ex-dividend or ex-warrants date shall be **designated by the
> Committee**."

and the amendment trail, verbatim:
`Amended by SR-FINRA-2023-017 eff. May 28, 2024.` ·
`Amended by SR-FINRA-2016-047 eff. Sept. 5, 2017.` ·
`Amended by SR-FINRA-2017-026 eff. Aug. 17, 2017.` ·
`Amended by SR-FINRA-2010-030 eff. Dec. 15, 2010.`

**Round 5's `J6` is confirmed on the authority question: this is FINRA 11140, and the regime dates
are 2017-09-05 and 2024-05-28.** Note the fourth amendment — **`eff. Dec. 15, 2010`** — which falls
*inside* the programme's window (2010-01-04 onward). I did not establish what it changed. §10.1.

**Three things the rule says that a naive implementation gets wrong:**

1. **An ordinary forward split goes EX AFTER the PAY date.** A 2-for-1 split is a 100% stock
   dividend, hence ≥25%, hence (b)(2). **The ex-date follows the payable date rather than preceding
   the record date.** Any validator written as `assert ex_date <= record_date` will fire on every
   split in the file.
2. **(b)(1) has a non-delivery-date branch.** If the record date falls on a day the Committee
   designated a non-delivery date, the ex-date shifts an extra business day earlier. A pure
   `ex == record` rule will be off by one on those.
3. **(b)(3) hands ADRs and foreign securities to Committee discretion.** For those there is *no
   formula at all*, which matches the Nasdaq spec's note that ADS/ADR factors are set on *"an
   approximate value"*.

**The primary confirmation, on a named event** [PRIMARY DATA DOC, EDGAR 8-K exhibit, CIK 0001045810,
accession 0001045810-24-000113, `q1fy25pr.htm` — **read in full**]. NVIDIA's 10-for-1, verbatim:

> "Each record holder of common stock as of the close of market on **Thursday, June 6, 2024**, will
> receive nine additional shares of common stock, to be distributed after the close of market on
> **Friday, June 7, 2024**. Trading is expected to commence on a split-adjusted basis at market open
> on **Monday, June 10, 2024**."

So: record **06-06**, pay/distribution **06-07**, ex **06-10** = first business day after payable.
**Exactly 11140(b)(2).** And the ex-date is **two business days AFTER** the record date.

**The same press release, two paragraphs later, on the cash dividend:**

> "will be paid on Friday, June 28, 2024, to all shareholders of record on **Tuesday, June 11,
> 2024**."

Record 06-11, and under (b)(1) in the T+1 regime the ex-date is **06-11** — the record date itself.
**One issuer, one document, one month: `ex − record = +2` for the split and `ex − record = 0` for
the dividend.** There is no single offset that fits both, and both are in the same file.

**And the bear trap in that same document:** its own bullet headline reads
**"Ten-for-one forward stock split effective June 7, 2024"**. **The issuer calls 06-07 "effective";
the market adjusts on 06-10.** A split file whose date field was populated from issuer language is
**one business day early** relative to the price file. Polygon's `execution_date` is documented as
the market-adjustment date (*"On the execution date, all trading is already adjusted"*), not the
issuer's "effective" date — but the two words sit one business day apart and nothing in the field
name tells you which you have.

**What it means for joining a split file to a price file on date.** Four things:
- **You cannot audit the date against the rule**, because the rule's input is the *pay* date and
  **Polygon's and Alpha Vantage's split records do not contain a pay date.** The only checkable
  version of 11140(b)(2) on these feeds is a *price-based* one: the gap must appear on
  `execution_date`, not on `record_date ± k`.
- **The ratio and the price gap are not the same number for a ≥25% distribution that is not a pure
  split.** §5.
- **The sign of `ex − record` is not a constant**, so it cannot be used as a sanity filter.
- **A 24.9% stock dividend and a 25.1% one land on opposite sides of the pay date.** The threshold is
  on *value*, which is not in the file, so **you cannot predict from the file which branch applied** —
  you can only observe which one the dates are consistent with.

### 4.2 The two regime transitions, from primary SRO documents

**2017-09-05 (T+3 → T+2).** [PRIMARY DATA DOC, SEC Release 34-81446 / SR-NASDAQ-2017-084, 9 pages,
HTTP 200, 133,882 bytes — **read in full**.] The filing gives the transition mapping as a table.
Verbatim:

> "During the implementation of the T+2 settlement cycle, the "regular" ex-dividend dates will be as
> follows:
> Record Date 9/1/2017 Ex date 8/30/2017
> Record Date 9/5/2017 Ex date 8/31/2017
> Record Date 9/6/2017 Ex date 9/1/2017
> Record Date 9/7/2017 Ex date 9/6/2017 [fn: September 4, 2017 is Labor Day and not a business day.]"

and, on the cause and on the large-distribution branch:

> "the September 5, 2017 industry-wide transition date from T+3 to T+2 will result in **September 7,
> 2017 being a "double" settlement date** for trades that occur on September 1, 2017 (under T+3 …)
> and trades that occur on September 5, 2017 (under T+2) … In order to avoid confusion about the
> proper settlement date and to coordinate with other SROs, Nasdaq and the other SROs have agreed
> that **no securities will be ex-dividend on September 5, 2017.**"

> "In order to ensure that no securities will be ex-dividend on September 5, 2017 for purposes of
> "large" distributions, Nasdaq similarly proposes to interpret Rule 11140(b) so that, **if an issuer
> sets September 1, 2017 as the payment date for a large distribution, the ex-dividend date would be
> September 6, 2017, not September 5, 2017.**"

The same filing also quotes the **pre-2017 text** verbatim, which pins the T+3 regime:
*"the date designated as the "ex-dividend date" shall be the **second business day preceding the
record date** if the record date falls on a business day, or the **third business day preceding**
the record date if the record date falls on a day designated by Nasdaq Regulation as a non-delivery
date."*

**2024-05-28 (T+2 → T+1).** [PRIMARY DATA DOC, Cboe notice `C2024051400`, HTTP 200, 138,860 bytes —
**read in full**; extracted with `pypdf` after WebFetch returned its "corrupted PDF" message, which
per the shared rules is **not a block** and was not one here.] Verbatim, the whole operative passage:

> "The Cboe U.S. Equities Exchanges will also shorten the period for which transactions in stocks
> are ex-dividend or ex-rights. **Currently, the Cboe U.S. Equities Exchanges commence ex-dividend
> trading one trading day before the record date** for a dividend or other distribution. **Upon
> implementation of the new settlement cycle, ex-dividend trading will take place on the same date
> as the record date.**
>
> As a result of the transition to a T+1 settlement cycle effective May 28, 2024, **the settlement
> date for trades that occur on both May 24, 2024, and May 28, 2024, will be May 29, 2024.**
>
> The Cboe U.S. Equities Exchanges and other self-regulatory organizations have agreed with DTCC
> that **no securities will become ex-dividend on May 28, 2024.**"

And the FINRA side, verbatim [PRIMARY DATA DOC, SR-FINRA-2023-017, 58 pages, HTTP 200, 2,112,808
bytes — **the Rule 11140 pages read in full, the rest skimmed for 11140 mentions**]:

> "FINRA is proposing to shorten the timeframes in Rule 11140(b)(1) by one business day. As such,
> the date designated as the "ex-dividend date" would be the record date if the record date falls on
> a business day, or the first business day preceding the record date if the record date falls on a
> day designated by the Committee as a non-delivery date."

with the compliance date stated as: *"The effective date of final Exchange Act Rules changes is May
5, 2023, and the **compliance date is May 28, 2024**."*

**The resulting three-regime table, each cell from a primary document:**

| regime | dates | (b)(1) rule | authority |
|---|---|---|---|
| T+3 | window open → **2017-09-04** | ex = record **− 2** bd (− 3 if record is a non-delivery date) | pre-2017 11140(b)(1), quoted in 34-81446 |
| T+2 | **2017-09-05** → **2024-05-27** | ex = record **− 1** bd (− 2 if non-delivery) | SR-FINRA-2016-047 eff. 2017-09-05 |
| T+1 | **2024-05-28** → now | ex = **record** (− 1 if non-delivery) | SR-FINRA-2023-017 eff. 2024-05-28 |

throughout which **(b)(2) never changed**: ex = first business day after payable.

### 4.3 A CORRECTION to round 5's `J6`, recorded as a conflict and not adjudicated

Round 5's `J6` is reported to have found *"a ONE-DAY HOLE where no security went ex-dividend, and a
DOUBLED ex-date day"*. **My primary documents say something different, and I report both.**

- **There are TWO declared holes, not one.** `no securities will be ex-dividend on September 5,
  2017` (SR-NASDAQ-2017-084) **and** `no securities will become ex-dividend on May 28, 2024` (Cboe
  C2024051400). Both are SRO-declared, in the imperative, in primary filings.
- **The doubled day in both primaries is a doubled SETTLEMENT date, not a doubled EX-DATE.**
  2017-09-07 (*"a 'double' settlement date"*) and 2024-05-29 (*"the settlement date for trades that
  occur on both May 24, 2024, and May 28, 2024, will be May 29, 2024"*). **I found no primary
  document declaring, or describing, a doubled ex-dividend date at either transition.** Both
  transition mappings I recovered are injective: `{9/1→8/30, 9/5→8/31, 9/6→9/1, 9/7→9/6}` has no
  repeated target, and the 2024 mapping likewise empties 05-28 rather than doubling anything.
- **The two holes have different causes, which is itself worth carrying.** 2017-09-05 was *declared*
  and required an explicit override for the (b)(2) branch (pay 09-01 → ex 09-06). 2024-05-28 was
  declared too, but the 2024 filings carry no transition table, so the mapping around it is not
  pinned by a primary document I read — §10.3.

**Which I would weight:** the primary SRO filings, because they are the instruments that set the
behaviour and both use the exact word "settlement" for the doubling. **But I cannot see `J6`'s
working, and a doubled ex-date is a perfectly plausible *empirical* observation in a data file even
where no rule declares one** — it is what you would get if a vendor applied the old offset to
record dates straddling the boundary. Those are not the same claim, and the second would be a
vendor defect rather than a convention. **Not adjudicated.** §6.4 is the assertion that settles it
on the programme's own file in one line, and it is the cheapest item in §6.

---

## 5. THE CLASSES THAT BREAK A TWO-FIELD SCHEMA

Taking the exchange's own taxonomy as the yardstick, because it is primary and it is published.
**Nasdaq Daily List `Dividend Type Id`, verbatim, the complete enum:**

> "XC - Cash Dividend · CS - Cash and Stock Dividend or Split · XR - Ex-Rights · XW - Ex-Warrants ·
> RS - Reverse Split · SO - Spin Off · CP - Stock Div. payable in another Company · XS - Stock
> Dividend or Split · XX - Other"

**Nine codes.** A schema of `(split_ratio, dividend_amount)` has **two slots and no type field**,
so it must collapse nine classes onto two. Below: what each class needs, and what is lost. The
right-hand column is the part that cannot be recovered from the file afterwards at any price.

| class | exchange code | what a feed must carry | what `(ratio, amount)` cannot express |
|---|---|---|---|
| **Ordinary split / reverse split** | `XS`, `RS` | ratio, ex-date, **pay date** (the (b)(2) input), `New TSO` | The pay date — so 11140(b)(2) becomes unauditable (§4.1). **And `CS`: a cash-and-stock event needs BOTH slots at once on ONE date**, which a two-field row can hold only if the loader knows not to treat them as separate events. |
| **Stock dividend (<25%)** | `XS` | ratio as a factor (`1.10` for 10%), ex-date | Indistinguishable from a 1.10-for-1 split in the ratio slot, yet it is **(b)(1)**, so its ex-date precedes the record date while a ≥25% one follows the pay date. **Same slot, opposite date algebra.** |
| **Cash dividend** | `XC` | amount, currency, **gross vs net**, ex/record/pay/declaration | `Net Amount` vs gross `Cash Amount`. **A foreign-withholding event books at gross and pays at net**; one field books one of them and silently mis-states total return by the withholding. |
| **Special / supplemental dividend** | `XC` + `Amount: spl/ext` | a flag that it is non-recurring | Nothing in a bare amount says a $3.00 row is a one-off. Polygon's answer is `distribution_type`, which is **a cadence label, not an economic one**. A recurrence model fed specials will forecast them. |
| **Return of capital** | `XC` (+ `QualDiv`) | **tax character** | **This is the worst case and it is invisible.** ROC is economically a *partial liquidation*: it reduces basis and is not income. In a two-field schema it is byte-identical to an ordinary dividend of the same size. `QualDiv` (`Y`/`N`/`U`/`NULL`) is the exchange's only handle and **`U` means "Issuer has made no affirmation"** — so even the primary file is often silent. |
| **Spin-off** | `SO`, `CP` | **the identity and title of the OTHER issuer**, the share ratio, the value basis | 10b-17(b)(1)(v)(d) requires *"the name of the issuer and title of that security, the amount to be paid or distributed, and the rate"*. **A scalar factor carries none of it.** Measured: Alpha Vantage books the IBM/Kyndryl spin-off as `{"effective_date": "2021-11-04", "split_factor": "1.0460"}` [MEASURED IN BRIEF]. From IBM's own 8-K, verbatim: *"Record date for distribution of Kyndryl shares will be **October 25, 2021**"*, *"The distribution is expected to occur after close of market on **November 3, 2021**"*, *"each holder of IBM common stock will receive **one share of Kyndryl common stock for every five shares of IBM** common stock held"* [PRIMARY DATA DOC, CIK 0000051143, accession 0001104659-21-125064 — read in full]. **`1.0460` is a price ratio derived from Kyndryl's market value. The 1-for-5 share ratio, the name "Kyndryl", and the 80.1%/19.9% retention are all unrecoverable.** And the feed's date (**11-04**) is **pay + 1**, **8 business days after the record date** — so (b)(1)'s `record − 1` does not hold for this class either. |
| **Rights offering** | `XR` | `Rights Basis Notes`, `Rights Exercise Price Amount`, `Rights Expiration Date` | **Three fields, none of which is a ratio or an amount.** A rights offering's price effect depends on the subscription price and the basis; a scalar factor is a *consequence*, not the event. This is where Sears' 2014 `1011 for 1000` and `1062 for 1000` rows came from (§1.3) — the event compressed to its own side-effect. |
| **Warrant distribution** | `XW` | subscription price, expiry | Same as rights. |
| **Share-class consolidation / reclassification** | `XX`, + symbol-change records | **the old and new identifiers**, and the conversion ratio *per class* | A two-field schema has one row per (ticker, date) and **no place for "class B became class A at 1:1 and the ticker changed"**. The Daily List handles this in a *different file section* (symbol/name changes), not in the dividend file at all — so **a consumer of only the dividend/split file never sees it.** |
| **Conditional or cancelled distribution** | any, + `CancelOrder` | a cancel/amend mechanism and an as-of | 10b-17(b)(1)(vii) requires *"Details of any condition which must be satisfied"*; IBM's own 8-K says *"The distribution is subject to certain conditions described in the registration statement on Form 10"*. **An event table with no revision history cannot represent an announcement that was later cancelled**, nor tell you what you would have believed on an earlier date. |
| **Fractional settlement** | any split/reverse | 10b-17(b)(1)(vi) *"Method of settlement of fractional interests"* | A reverse split pays **cash in lieu** of fractions. That is a **cash flow on the ex-date that is not a dividend and not a price adjustment.** At a 1-for-200 reverse split it can be the majority of a small position's value. No slot for it. |
| **ADR / foreign** | (b)(3) | a flag, plus the note that the factor is approximate | Nasdaq: the factor may be *"based on an approximate value"* and *"the factor will always take precedence"*. **So for this class the feed's own amount field is known-wrong and the file says so.** |

**The two structural losses, stated once.** (i) **There is no type field**, so nine economically
distinct events are read as two, and the three that change *total return* rather than *price*
(return of capital, gross-vs-net withholding, cash-in-lieu) are unreachable. (ii) **There is no
second identifier and no revision history**, so a class consolidation, a symbol change and a
cancelled announcement are all invisible to a consumer of the events file alone.

---

## 6. WHAT COULD BE ASSERTED — every convention and defect above, turned into a check

Each numbered item is phrased as the brief demands: **"assert X about the data"**. Items marked
**[WORRY]** are defects I could not reduce to an assertion and are labelled as worries, not
findings, per the rule.

**On the ex-date regimes (§4.2) — these are the cheap, high-value ones.**

1. **Assert that every (b)(1)-class event in the file satisfies the regime's own offset**: for each
   row with both an ex-date and a record date and `|factor − 1| < 0.25`, assert
   `ex == busday(record, −2)` when `ex < 2017-09-05`, `ex == busday(record, −1)` when
   `2017-09-05 ≤ ex < 2024-05-28`, and `ex == record` thereafter — **with an allowance of one extra
   business day earlier** for the non-delivery-date branch, and **only** that direction. Report the
   violation *count per regime*: a file built on one offset will show near-zero violations in one
   regime and near-100% in the others, which is a far sharper signature than a global rate.
2. **Assert the two holes are empty.** Assert **zero** events in the file have
   `ex_date == 2017-09-05`, and **zero** have `ex_date == 2024-05-28`. This is two lines and it is
   the strongest available single test of whether the file's ex-dates are *published* or
   *recomputed* — a recomputed column **cannot** produce those holes, and a published one cannot
   avoid them.
3. **Assert the (b)(2) override at the 2017 boundary**: assert no event with
   `pay_date == 2017-09-01` and `|factor − 1| ≥ 0.25` carries `ex_date == 2017-09-05`; the primary
   says it must be `2017-09-06`.
4. **Assert the doubled-day question rather than arguing it.** Assert the per-day event count has no
   outlier at the transitions: compute `n_events` by ex-date over `2017-08-25…2017-09-15` and
   `2024-05-17…2024-06-07` and assert each day's count is within the surrounding month's range.
   **This is the one-line test that settles §4.3 on the programme's own file**: a genuine doubled
   ex-date day shows as a count spike adjacent to a zero, and its absence would confirm the primaries.

**On the 25% inversion (§4.1).**

5. **Assert that splits sit on the opposite side of the record date from dividends.** For every row
   with `|factor − 1| ≥ 0.25` **and** a populated record date, assert `ex_date > record_date`. Then
   assert the complement: for `|factor − 1| < 0.25` dividend rows, `ex_date ≤ record_date`. **Two
   assertions, opposite signs, and a validator written with one sign will fail loudly instead of
   passing quietly.**
6. **Assert no `assert ex <= record` exists anywhere in the codebase.** A grep-level assertion: this
   is the specific naive check that (b)(2) invalidates, and a reverse 1-for-10 split satisfies
   `|factor − 1| ≥ 0.25` too, so it is not a rare branch.
7. **[WORRY, not a finding] — the issuer-"effective" vs market-"ex" one-day gap (§4.1).** I cannot
   turn this into a self-contained assertion, because deciding which of the two a field holds needs
   the price series, and the *price-based* version of the check is adjustment arithmetic, which this
   lane is scoped out of. **The honest form is a worry with a named probe:** NVDA's 10-for-1 has
   issuer-"effective" **2024-06-07** and market-ex **2024-06-10**, one business day apart, both in
   the issuer's own 8-K. **Assert `split_date == 2024-06-10` for NVDA's 10-for-1, as a single
   hard-coded fixture row.** One known answer, from a primary document, that distinguishes the two
   conventions in one line. (If it reads 06-07, every split in the file is a business day early.)

**On the amount/factor distinction (§3.1) — the exchange's own warning.**

8. **Assert no row carries an adjustment factor with a null ex-date.** Nasdaq, verbatim: *"entries
   without an X-Date do not get adjusted, even though a factor may be provided."* Assert
   `n_rows(factor != 1 AND ex_date IS NULL) == 0`, and if non-zero, assert the loader **skips** them
   rather than applying them.
9. **Assert gross-vs-net.** Assert every cash row's amount matches the **gross** convention by
   cross-checking the fiscal-period sum against SEC XBRL
   `CommonStockDividendsPerShareDeclared` (free, CIK-keyed, dead-inclusive, §1.7c): for each
   (CIK, fiscal period) where the tag exists, assert
   `sum(feed amounts with ex_date in period) == xbrl_val` to the cent. **Deduplicate the XBRL side
   on `(start, end, val)` and take the earliest `filed`** — the same fact repeats across four
   filings. A net-of-withholding feed will come in systematically *low* and only on the names that
   withhold, which is a signature, not noise.
10. **Assert split ratios against XBRL.** For each (CIK, fiscal year) where
    `StockholdersEquityNoteStockSplitConversionRatio1` exists, assert
    `prod(feed factors in year) == prod(xbrl ratios in year)`. **Assert on the RATIO only and never
    on the XBRL date** — NVDA's 10-for-1 is tagged to the month `2024-05-01…2024-05-31` and the real
    ex-date is outside it.

**On identifiers (§1.3, §1.7b) — the failure that is worse than no source.**

11. **Assert every corporate-action row resolves to a permanent identifier, and that the identifier's
    validity window contains the event date.** Assert `n_rows WHERE ticker IS the only key == 0`
    before any join. The measured base rate this must survive: **28 of 425** delisted tickers are
    live again, **two with overlapping windows**.
12. **Assert a dead ticker's corporate actions do not post-date its last bar.** For every name, assert
    `max(action ex_date) <= last_bar_date + k` for a small stated `k`. **This catches the exact
    stocksplithistory.com/dividendhistory.org failure mode mechanically** — the Global X ETF's 2024-26
    dividends attached to a Sears row would violate it by years.
13. **Assert the converse, which is the subtler direction.** For every name, assert
    `min(action ex_date) >= first_bar_date − k`. Sears' **2014** split rows attached to an ETF that
    began trading **2023-09-14** is a violation of *this* one, not of §6.12. **Both directions or
    neither** — the measured conflation produced one of each.
14. **Assert the ticker→identifier crosswalk is not survivor-only.** Assert the crosswalk contains
    every dead name in the panel. Measured control: `sec.gov/files/company_tickers.json` has
    **10,407 rows and 0 of `SIVB`/`SIVBQ`/`BBBY`/`BBBYQ`/`TWTR`/`SHLD`/`SHLDQ`** — so if the
    crosswalk was built from that file it is survivor-only by construction, and **asserting its row
    count against the panel's dead count is a one-line detector.**
15. **Assert that where a dead name's ticker is recorded, it is the IN-PANEL ticker and not the
    terminal one.** Measured: EDGAR renders SVB Financial as `SIVBQ`, its post-bankruptcy OTC
    symbol, not the `SIVB` it traded under. Assert any ticker field carries the symbol in force **on
    the event date**, and assert no in-panel ticker ends in a bankruptcy `Q` suffix before its
    delisting date.

**On universe membership, which is where this lane touches the programme's floor.**

16. **Assert the floor is evaluated on the SAME basis the action file adjusts.** The floor is
    `$5 AS-TRADED close`; a split factor applied to the close moves a name across `$5`. Assert that
    the series the floor is read from is the **unadjusted** one, and assert the count of
    floor-crossings **on action ex-dates** is not elevated relative to non-action dates. A reverse
    split is the acute case: it multiplies the as-traded price and **admits names to the universe**
    — which is a membership event, not a return event, and the two have different nulls.
17. **Assert the dollar-volume screen's denominator moved with the numerator.** A split changes share
    count and price together; dollar volume should be invariant. Assert
    `dollar_volume(ex_date) / dollar_volume(ex_date − 1)` has no systematic jump at split ex-dates.
    **This is the assertion that catches a factor applied to price but not to volume**, which is a
    pure membership error with no return signature at all.

**On the harvest loop, if one is ever written against a public endpoint.**

18. **Assert on CONTENT, never on status.** Measured: Alpha Vantage returns **HTTP 200,
    `application/json`, 220 bytes, valid JSON, no `data` key** for every gated symbol. Assert the
    expected key is present and the record count is > 0 **before** writing a row, and assert the
    response length exceeds a floor. Otherwise a dead cohort is written as uniformly
    dividend-free — the single most plausible silent failure in this whole lane.
19. **Assert a value that must return zero.** Controls that worked here and are reusable:
    `dividendhistory.org/payout/ZZZZQQFAKE/` → **404, 18,737 bytes, byte-identical to a real miss**;
    EDGAR FTS on a nonsense phrase → **`"total": 0`**. Assert both on every run of a harvest, and
    assert the nonsense-ticker byte count **equals** the known-miss byte count — a handler that
    starts answering nonsense tickers with content has changed underneath you.
20. **Assert the source is one source.** Assert any "second source" reconciliation does not compare a
    feed against itself. Measured: **Polygon's own splits documentation calls
    `https://api.massive.com/stocks/v1/splits`**, and the two sites publish the identical horizon
    line. Assert the two endpoints' *disagreement rate is non-zero* before trusting an agreement.
21. **Assert series horizons separately.** Measured in one product: splits *"Records date back to
    October 25, 1978"*, dividends *"Records date back to January 15, 2000"*. Assert each series'
    earliest event against its **documented** start, not against the other series'. A dividend file
    that is empty before 2000 is **correct behaviour being mistaken for a defect**, and vice versa.

**Worries I could not reduce to assertions, labelled as such.**

22. **[WORRY] Return of capital is invisible in a two-field schema and I know of no free check.**
    `QualDiv == 'U'` (*"Issuer has made no affirmation"*) is an allowed value in the exchange's own
    primary file, so **even the authoritative source is frequently silent**. The only assertion I
    can construct is a *detector, not a validator*: assert that no single name's annual cash
    distributions exceed some multiple of its earnings, which flags ROC candidates for hand
    inspection and proves nothing. **Recording it as an unresolved worry is the honest move.**
23. **[WORRY] Cash-in-lieu of fractional interests is a real cash flow with no field.** 10b-17
    requires the *method* be disclosed; no feed I saw carries the *amount*. On a 1-for-200 reverse
    split it can dominate a small position. **No assertion available from the events file alone.**
24. **[WORRY] The NYSE product page documents its ex-date file as `T+2`, two regimes stale.** I can
    assert the *data* (items 1–4) but I cannot assert a *document*. The generalisable worry is that
    **vendor convention prose is not evidence of vendor convention**, and the only defence is items
    1–4 run against the bytes.
25. **[WORRY] No revision history means the file is not point-in-time.** The exchange's own feed has
    `CancelOrder` and publishes future-effective rows whose payload is *"as of the NASDAQ Daily List
    Date - not the Effective date"*. An events table with one row per event **cannot** answer "what
    did I believe on date D", and **no assertion on a single snapshot can detect that it is a
    snapshot.** The only fix is keeping dated snapshots, which is a collection decision, not a check.

---

## 7. WHAT I WOULD WEIGHT, WHERE SOURCES DISAGREE

Recorded, not adjudicated, per the standing instruction.

1. **Round 5 `J6` vs the SRO filings, on the hole and the doubled day.** §4.3. I weight the
   primaries (two declared holes; the doubling is of *settlement*), but `J6` may be reporting an
   empirical observation in a data file, which is a different and compatible claim. **§6.4 settles
   it in one line on the programme's own data and costs nothing.**
2. **NYSE's product page (`"ex-date" = T+2`) vs FINRA 11140 and the Cboe notice.** I weight the rule
   and the SRO notice absolutely — the rule *is* the behaviour. But **I do not discard the NYSE
   page**, because if its file genuinely still computes `T+2` that is a live vendor defect, and I
   cannot tell from outside which it is.
3. **`Amount` vs `Stock Amount`/`Cash Amount` inside Nasdaq's own file.** Nasdaq adjudicates this
   itself and I follow it: *"the factor will always take precedence"*.
4. **stocksplithistory.com vs everything.** Its Sears/Global X page is internally contradictory, so
   it is not a party to a disagreement — it is a measured defect. I would not use it for anything.

---

## 8. WHAT THIS CHANGES ABOUT THE PROGRAMME'S POSITION

Stated as implications, claiming nothing about the programme's data.

- **The second-source question is closed for the ex-date and only partly open for the rest.** Amount
  and ratio have a free, dead-inclusive, CIK-keyed cross-check in SEC XBRL (§6.9, §6.10). **The
  ex-date has none and cannot, because no issuer document contains it** (§2). So the ex-date must be
  defended by **internal consistency against a published rule** — which is exactly what §6.1–§6.5
  are, and which is available today at the cost of a few dozen lines.
- **The regime assertions are the highest-value items in this brief per line of code.** §6.1 and §6.2
  between them distinguish a *published* ex-date column from a *recomputed* one, pin which of three
  offsets the file was built on, and do it **without any second source at all**. A file that passes
  §6.2's two holes is being told the ex-date by someone who knows; a file that fails them is
  computing it.
- **A corporate-action error is a universe-membership error, and §6.16–§6.17 are the only assertions
  here that touch that.** The floor is on as-traded prices, a reverse split multiplies as-traded
  prices, and **an erroneous reverse-split factor admits names to the universe** with no return-side
  tell. That direction seems to me the least-covered one.
- **Sign conventions cannot be asserted with one inequality.** §6.5's two opposite assertions are
  required. The programme's own history — a sign asserted in prose inverting a result — suggests the
  failure mode is already familiar.
- **The "dead-inclusive" framing needs one refinement.** Three of four named probes never paid a
  dividend, so **the dead cohort's exposure here is to DISTRIBUTIONS and SPLITS, not to ordinary
  dividends** — and distributions are precisely the class the two-field schema handles worst (§5)
  and where every free source failed worst (§1.3).

---

## 9. HOW TO RE-RUN EVERY PROBE

All probes 2026-09-10. UA `backtest-framework-research/1.0 (research@backtest-framework.org)`;
SEC calls `backtest-framework-research research@backtest-framework.org`. **No account created, no
key registered, no form submitted, no credential entered.**

### 9.1 The calls

```
# Dead-name source probes
curl -A "$UA" "https://query1.finance.yahoo.com/v8/finance/chart/TWTR?period1=1262304000&period2=1767225600&interval=1d&events=div%2Csplit"
curl -A "$UA" "https://api.nasdaq.com/api/quote/SHLDQ/dividends?assetclass=stocks"     # HTTP 000
curl -A "$UA" "https://stockanalysis.com/stocks/bbby/dividend/"                         # 404
curl -A "$UA" "https://stockanalysis.com/stocks/shld/dividend/"                         # 200, WRONG ISSUER
curl -A "$UA" "https://dividendhistory.org/payout/BBBY/"                                # 200, correct
curl -A "$UA" "https://dividendhistory.org/payout/SHLD/"                                # 200, WRONG ISSUER
curl -A "$UA" "https://dividendhistory.org/payout/SIVB/"                                # 404
curl -A "$UA" "https://dividendhistory.org/payout/ZZZZQQFAKE/"                          # NEGATIVE CONTROL: 404, 18737 B
curl -A "$UA" "https://dividendhistory.org/inactive-stocks/"                            # "Showing 970 of 970"
curl -A "$UA" "https://www.stocksplithistory.com/?symbol=SHLD"                          # 200, TWO ISSUERS
curl -A "$UA" "https://eodhd.com/api/div/AAPL.US?api_token=demo&fmt=json"               # 200
curl -A "$UA" "https://eodhd.com/api/div/SHLD.US?api_token=demo&fmt=json"               # 403 plan gate
curl -A "$UA" "https://www.alphavantage.co/query?function=DIVIDENDS&symbol=IBM&apikey=demo"
curl -A "$UA" "https://www.alphavantage.co/query?function=DIVIDENDS&symbol=BBBY&apikey=demo"  # 200/220 B, NO DATA KEY
curl -A "$UA" "https://www.alphavantage.co/query?function=SPLITS&symbol=IBM&apikey=demo"

# SEC, CIK-keyed
curl -A "$SECUA" "https://data.sec.gov/submissions/CIK0001310067.json"   # also 0000886158 0000719739 0001418091
curl -A "$SECUA" "https://www.sec.gov/files/company_tickers.json"        # 10407 rows, 0 dead probes
curl -A "$SECUA" "https://efts.sec.gov/LATEST/search-index?q=%22ex-dividend%22&forms=8-K&ciks=0001310067"
curl -A "$SECUA" "https://efts.sec.gov/LATEST/search-index?q=%22zzqqxxfake+phrase+nobody%22&forms=8-K"  # CONTROL: total 0
curl -A "$SECUA" "https://data.sec.gov/api/xbrl/companyconcept/CIK0000886158/us-gaap/CommonStockDividendsPerShareDeclared.json"
curl -A "$SECUA" "https://data.sec.gov/api/xbrl/companyconcept/CIK0000895126/us-gaap/StockholdersEquityNoteStockSplitConversionRatio1.json"

# Primary convention documents (all HTTP 200)
curl -A "$UA" "https://www.finra.org/rules-guidance/rulebooks/finra-rules/11140"
curl -A "$UA" --compressed "https://www.ecfr.gov/api/versioner/v1/full/2026-01-01/title-17.xml?section=240.10b-17"   # needs Accept-Encoding or 406
curl -A "$UA" "https://www.sec.gov/files/rules/sro/nasdaq/2017/34-81446.pdf"
curl -A "$UA" "https://cdn.cboe.com/resources/release_notes/2024/Cboe-Equities-to-Transition-to-T-1-Clearing-and-Settlement.pdf"
curl -A "$UA" "https://www.finra.org/sites/default/files/2023-11/SR-FINRA-2023-017.pdf"
curl -A "$UA" "https://www.nasdaqtrader.com/content/technicalSupport/specifications/dataproducts/dlspec_1130prior.pdf"
curl -A "$UA" "https://www.nyse.com/market-data/corporate-actions/corporate-actions-for-nyse-group-listings"
curl -A "$UA" "https://www.finra.org/filing-reporting/market-transparency-reporting/uniform-practice-code-upc/faq"

# Primary event documents
.../Archives/edgar/data/1045810/000104581024000113/q1fy25pr.htm          # NVDA 10-for-1
.../Archives/edgar/data/51143/000110465921125064/tm2128856d3_ex99-1.htm  # IBM/Kyndryl record + distribution dates
```

### 9.2 Blocks and non-blocks, logged by TOOL AND RESPONSE

| tool | target | response | reading |
|---|---|---|---|
| `curl` | `api.nasdaq.com/api/quote/{SHLDQ,BBBYQ,SIVBQ,SVB}/dividends` | **HTTP 000, 0 bytes, all four**, >120 s total | no response at all; **not** a 403, **not** a UA exclusion, **no output file written** |
| `curl` | `nasdaqtrader.com/dynamic/symdir/dailylist/*` | **302**, 944 B `Object moved` → `/Trader.aspx?id=http404` | site retired |
| `curl` | `eodhd.com/api/div/SHLD.US` | **403**, 55 B, `Forbidden. Please contact support@…` | **plan gate, NOT a UA exclusion** — same UA got 200 on `AAPL` one call earlier |
| `curl` + `WebFetch` | `dtcc.com/.../T1-Dividend-Processing-FAQ.pdf` | **404** both; curl body is **108,312 B of HTML** | genuine 404 served with a large handler page |
| `WebFetch` | Cboe T+1 PDF | *"corrupted or encoded PDF with primarily unreadable binary content"* | **NOT A BLOCK.** Bytes landed; `pypdf` read all of it |
| `curl` | `ecfr.gov/api/.../title-17.xml` | **406**, `"This endpoint requires response compression"` | fixed by `--compressed` |
| `curl` | `crsp.org/products/documentation/distribution-codes` | **HTTP 200, 972,198 B of *Morningstar Market Indexes* marketing** | a documentation URL serving unrelated content at 200 |
| `curl` | `crsp.org/wp-content/uploads/guides/CRSP_US_Stock_…pdf` | **404**, 190,807 B HTML | |
| `curl` | `terpconnect.umd.edu/…/data_defs_061899.pdf` | 200, 2,523,136 B, **`pypdf` → `Stream has ended unexpectedly`** | truncated download; **not retried** |
| `curl` | `data.nasdaq.com/databases/SFA/documentation` | 200, 6,663 B, `"You need to enable JavaScript"` | JS shell, no content |
| `curl` | `tiingo.com/documentation/end-of-day` | 200, 20,263 B, no extractable text | JS shell |
| `curl` | `polygon.io/docs/rest/stocks/tickers/ticker-events` | **404**, 317,930 B | path guess, wrong |

### 9.3 Raw bytes, and a handling note

Every response above is on disk in the session scratchpad, prefixed `K4_` per the lane-unique
filename rule:
`…/268972c6-b281-4926-b9db-c5611e52a2c6/scratchpad/K4_*` — including
`K4_nasdaq_dlspec.pdf` (234,653 B) and its extraction `K4_dlspec.txt`, `K4_finra_11140.html`,
`K4_p_nasdaq_34_81446` (the 2017 transition table), `K4_p_cboe_t1.pdf` (the 2024 hole),
`K4_ecfr.xml` (10b-17), `K4_nvda.htm`, `K4_ibm_rec.htm`, `K4_p_ssh_shld` (the two-issuer page),
`K4_p_dh_bbby`, `K4_company_tickers.json`, and the helper `K4_txt.py`.

**Handling note, flagged rather than decided:** the scratchpad is session-temp. **Four of those files
are quoted verbatim as load-bearing evidence in this brief** — the Nasdaq Daily List spec PDF, SEC
Release 34-81446, the Cboe notice `C2024051400`, and the eCFR 10b-17 extract. Under the house rule
that *a file a record quotes is evidence and belongs in `data/`*, **those four should be promoted out
of temp.** I have not moved them: promoting files into `data/` is not mine to decide, and the
decision should be visible rather than incidental. **All four are re-fetchable from the URLs in §9.1
and all four returned HTTP 200.**

---

## 10. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **What the 2010-12-15 amendment to Rule 11140 (SR-FINRA-2010-030) changed.** It is in the
   amendment trail on the rule page and **it falls inside the programme's window** (which opens
   2010-01-04). I read the trail but not the filing. **If it touched (b)(1) or (b)(2), there is a
   FOURTH regime boundary eleven days before the window's first bar**, and §6.1's three-regime
   assertion would be incomplete. **This is the single most important unfinished item in the brief**
   and it is one document away.
2. **Whether any free source serves a dead name's SPLITS at all.** I found one free source that
   serves a dead name's **dividends** (dividendhistory.org, BBBY) and **none** that serves a dead
   name's splits or distributions correctly. I did not probe every possible free endpoint, so this is
   "not found", not "does not exist" — though combined with round 4's `H5` on prices I would not
   expect a different answer.
3. **The 2024-05-28 transition mapping of record dates to ex-dates.** The **hole** at 2024-05-28 is
   pinned by a primary exchange notice, verbatim. The **full mapping** around it (what ex-date record
   dates 05-24, 05-28, 05-29 received) I have only from a **search-result summariser**, and **per the
   summariser rule I do not treat that as established** and have not quoted it as a finding. The
   2017 equivalent *is* pinned, from the Nasdaq filing's own table.
4. **Whether round 5's `J6` doubled ex-date is a rule artefact, a data artefact, or an error.** §4.3.
   I could not see `J6`'s working and I found no primary declaring a doubled ex-date at either
   transition. **Recorded as a conflict, not adjudicated.**
5. **Whether Polygon/Massive, EODHD, or any keyed vendor actually serves dead names' actions.** Every
   such call needs a key; I did not register. **Per the bar, that is a FAILURE, not a candidate**,
   and I am not recommending any of them. Their *documentation* I read and quote; their *data* I have
   not seen.
6. **Whether the NYSE `Ex-Date Distributions` file matches its own `T+2` description or the
   description is merely unmaintained.** The file is paid; I read only the product page. **Both
   possibilities are live** and I cannot distinguish them from outside.
7. **Whether today's Nasdaq Daily List spec still reads as the one I quote.** The PDF I read is
   footered `Updated: November 1, 2011` / `May 30, 2012` and its filename (`dlspec_1130prior.pdf`)
   says it is a superseded version. **Field semantics may have changed since.** I did not locate the
   current spec.
8. **The CRSP distribution-code taxonomy.** I wanted it as a third, independent yardstick for §5.
   The documentation URL **serves Morningstar marketing at HTTP 200**, the guide PDF 404s, and a
   university mirror of the 1999 definitions downloaded truncated (`pypdf` → `Stream has ended
   unexpectedly`). **§5 therefore rests on Nasdaq's nine-code enum and Rule 10b-17's field list —
   both primary, both read in full — and NOT on CRSP.** The search-result characterisation of the
   4-digit scheme is **[UNVERIFIED]** and I have not used it.
9. **Whether `dividendhistory.org`'s 970 inactive names were ever revised, and where its data comes
   from.** No provenance statement, no vintage, no change log. Its BBBY page agreed with BBBY's own
   8-K dividend cadence on the rows I spot-checked, which is one name.
10. **The exact count of Nasdaq `Dividend Type Id` values in use today.** I have the **documented**
    enum of nine from the spec. **I have never seen a row of the actual file**, so I cannot say which
    codes appear, at what frequency, or whether `XX - Other` is rare or common. **If `XX` is common,
    §5's table understates the problem.**
11. **Any claim about the programme's own corporate-events file.** I have not seen it. Every
    assertion in §6 is a check I believe is *constructible* from the conventions established here;
    **none is a report of a defect found in their data**, and §6.7's NVDA fixture row is the only one
    whose expected value I have pinned to a primary document.
