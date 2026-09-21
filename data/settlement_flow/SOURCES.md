# CME settlement-window sources — D586

**One entry per fact: the URL, the access date, and the sentence CME wrote.** Every quoted
sentence below was read out of the RAW response bytes cached in `data/raw/cme_settlement/`
(gitignored, unmodified, named with `fetched_at`), not out of a summary. `docs/RULES.md` and D445
forbid a summariser in a path that turns on exact wording, and this is one: the whole table is
times.

**Two fetch routes, both public, and which one was used is recorded per entry.**

| route | reaches | note |
|---|---|---|
| `curl` → `cmegroupclientsite.atlassian.net/wiki/rest/api/content/{id}` | the CME Group Client Systems Wiki (Confluence space `EPICSANDBOX`), which is where `cme-group-settlement-procedures.pdf` itself points for every asset class | anonymous, HTTP 200, returns the page body as storage XHTML with its version date |
| browser pane → `www.cmegroup.com` | the Special Executive Report HTML pages | **`curl` to cmegroup.com from this machine returns HTTP 403** with the body `"This IP address is blocked due to suspected web scraping activity"`, and `WebFetch` times out; the same 403 that `data/futures_contract_specs.json`'s `_provenance` block records. The precedent there is to read it in a browser, and that is what was done. |
| `curl` → `web.archive.org/web/…if_/…` | two SER PDFs cmegroup.com would not serve | rate-limits after a handful of requests; one capture came back as an archive.org block page and was deleted rather than parsed |

**The wrong-200 check.** Every Confluence fetch returned HTTP 200 with a matching `title` field and
the expected clock times present. The 14 cached page bodies were re-grepped for the window strings
AFTER the table was written, independently of what the browser rendered, and all 17 products'
windows matched (`data/raw/cme_settlement/confluence_*.json`).

---

## 0. The master table: where CME publishes its window times, and in which time zone

**`Daily Settlement Time Details`**, Confluence page 457085528, page version 2025-01-03.
URL `https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457085528/Daily+Settlement+Time+Details` ·
accessed 2026-09-21.

> "This topic details product settlement time ranges."

and, in the table under the heading `*Daily Settlement Time Ranges`:

| CME's row | CME's stated time | CME's stated zone |
|---|---|---|
| Livestock | 12:59:30-13:00:00 | **CT** |
| Grains/Oilseeds | 13:14:00-13:15:00 | **CT** |
| Equities | 14:59:30-15:00:00 | **CT** |
| Copper | 12:59:00-13:00:00 | **ET** |
| Silver | 13:24:00-13:25:00 | **ET** |
| Gold | 13:29:00-13:30:00 | **ET** |
| Energy Products | 14:28:00-14:30:00 | **ET** |

> "* Time range in which the relevant data is utilized to derive the daily settlement on normal
> trading days. For all Holidays in which the Trading Floors close early, these times will be
> adjusted to reflect those early closes."

**This is the first disagreement to record.** The brief's premise — "CME publishes windows in
Chicago time" — is half right. CME publishes **CME and CBOT** products (livestock, grains,
equities, FX, rates) in **Central** time and **NYMEX and COMEX** products (energy, metals) in
**Eastern**. `data/settlement_windows.csv` stores both spellings for every row and G4 asserts they
are exactly one hour apart; the `notes` column names which zone CME itself used.

The same page is what `https://www.cmegroup.com/market-data/files/cme-group-settlement-procedures.pdf`
(cached from the 2025-03-28 Wayback capture) resolves to: that PDF is one page of links, e.g.
`Energy Futures: http://www.cmegroup.com/confluence/display/EPICSANDBOX/Energy`, and the
`EPICSANDBOX` space has since moved to `cmegroupclientsite.atlassian.net`.

---

## 1. NYMEX energy — CL, NG, HO, RB — 14:28:00–14:30:00 **ET**

### 1a. The effective date

**SER-4867**, `https://www.cmegroup.com/tools-information/lookups/advisories/market-regulation/SER-4867.html` ·
read in the browser pane, 2026-09-21.

> Subject: "New Settlement Procedures NYMEX WTI Crude Oil, Natural Gas, Heating Oil, and RBOB
> Futures to be Settled Based Exclusively on CME Globex Activity for the Front Six Contract Months"
>
> Notice Date: "26 May 2009" · Effective Date: "01 June 2009"
>
> "Effective June 1, 2009, the first six contract months in these products will be settled by
> Exchange staff based solely upon CME Globex activity during the closing period, from 2:28:00 to
> 2:30:00 p.m. Eastern Time."
>
> "Staff will settle the front month contract at the volume weighted average price ("VWAP") of the
> outright trades executed on CME Globex during the close, rounded to the nearest tradable tick."

### 1b. The window is still current, and the basis wording in the table

Confluence `NYMEX Crude Oil` (457218849, page version 2025-08-27):

> "NYMEX Light Sweet Crude Oil (CL) futures are settled by CME Group staff based on trading
> activity on CME Globex during the settlement period. The settlement period is defined as:
> 14:28:00 to 14:30:00 ET for the Active Month and 14:28:00 to 14:30:00 ET for calendar spreads."
>
> "Tier 1: If a trade(s) occurs on Globex between 14:28:00 and 14:30:00 ET, the active month
> settles to the volume-weighted average price (VWAP), rounded to the nearest tradable tick."

Confluence `Natural Gas` (457415061, page version 2025-08-27), identical window, plus the spot-month
exception recorded in the table's `notes`:

> "NYMEX Natural Gas (NG) futures are settled by CME Group staff based on trading activity on CME
> Globex during the settlement period. The settlement period is defined as: 14:28:00 to 14:30:00 ET"
>
> "On the day of expiration, the spot (expiring) month will settle based on the VWAP of the outright
> CME Globex trades executed between 14:00:00 and 14:30:00 ET, and the second month will settle
> based on the VWAP of the outright CME Globex trades executed between 14:28:00 and 14:30:00 ET."

Confluence `NYMEX Heating Oil` (457415161) and `NYMEX RBOB Gasoline` (457088078), both page version
2025-08-27, carry the same sentence for HO and RB:

> "The settlement period is defined as: 14:28:00 to 14:30:00 ET for the Active Month and 14:28:00 to
> 14:30:00 ET for calendar spreads."

**Verdict on the ledger's hypothesis.** `SETTLEMENT_FLOW_LEDGER_PREREG.md` §3.4 says "currently
understood to be about 14:28–14:30 ET for NG and CL; **verify and record**". **Verified, exactly, in
ET, and dated to 2009-06-01** — with the caveat that it is the *active month* window; the expiring
month on its last day uses 14:00:00–14:30:00 ET instead, which is a 30-minute window and a different
object. §7.1's "for a 14:28 window start" therefore needs no shift.

---

## 2. COMEX metals — GC, SI, HG — no dated notice found

Confluence `Gold` (457088147, page version 2026-04-15):

> "Gold futures (GC) are settled by CME Group staff based on trading activity on CME Globex during
> the settlement period. The settlement period is defined as: 13:29:00 to 13:30:00 ET for the active
> month and 13:15:00 to 13:30:00 ET for calendar spreads."

Confluence `Silver` (457415360, page version 2026-02-10) — note CME states this one in **CT**:

> "Silver futures (SI) are settled by CME Group staff based on trading activity on CME Globex during
> the settlement period. The settlement period is defined as: 12:24:00 to 12:25:00 CT for the active
> month and 12:10:00 to 12:25:00 CT for calendar spreads."

Confluence `Copper` (457415464, page version 2025-10-13):

> "Copper futures (HG) are settled by CME Group staff based on trading activity on CME Globex during
> the settlement period. The settlement period is defined as: 12:59:00 to 13:00:00 ET for the active
> month and 12:30:00 to 13:00:00 ET for calendar spreads."

**History: NOT FETCHED.** No Special Executive Report establishing any of these three windows was
found. They are therefore `current_only` and `window_for` raises for every date before 2026-09-21.

**One dated corroboration, which is not a change date.** `SER-9637` (browser pane,
`https://www.cmegroup.com/notices/ser/2025/12/ser-9637.html`, accessed 2026-09-21):

> "Amendments to the Daily Settlement Procedure Document for the Gold Futures Contract"
> · "# SER-9637" · "Notice Date: 09 December 2025" · "Effective Date: 12 January 2026"

Its body is served only as an embedded PDF that the browser will not render as text, so **what it
changed is not sourced here.** What *is* sourced is that the window did not move across it: the
`Daily Settlement Time Details` page as it stood on **2025-01-03** already read `Gold
13:29:00-13:30:00 ET`, and the Gold procedure page as of **2026-04-15** still does.

---

## 3. CBOT grains and oilseeds — ZC, ZS, ZW, KE, ZL, ZM — 13:14:00–13:15:00 **CT**

Confluence `Grains` (457414829, page version 2026-08-20) — the page that covers all six roots:

> "CME Group staff determines the daily settlements in CBOT Corn (ZC), Wheat (ZW), Rice (ZR), Oats
> (ZO), Soybean (ZS), Soybean Meal (ZM), Soybean Oil (ZL) and KC HRW Wheat (KE) futures based on
> trading activity on CME Globex between 13:14:00 and 13:15:00 Central Time (CT), the settlement
> period."
>
> "Tier 1: The lead month settles to the volume-weighted average price (VWAP) of outright trades in
> the lead month between 13:14:00 and 13:15:00 Central Time CT, the settlement period, rounded to the
> nearest tradable tick. If the VWAP is equidistant between two ticks, then it's rounded to the tick
> that is closer to the prior-day's settlement price."
>
> "Tier 1: All months other than the designated lead month will settle based upon the VWAP of
> calendar spread transactions between 13:14:00 - 13:15:00 CT, the settlement period."
>
> "*The designated lead month in each product will roll on the 12th business day of the calendar
> month that precedes the current lead month."

Per-product pages confirm the same window independently: `Corn` (457090243, page version 2025-02-14)
— "between 13:14:00 and 13:15:00 Central Time (CT), the settlement period" — and `Kansas City Hard
Red Wheat` (457321296) — "13:14:00 - 13:15:00 CT".

**History: the CURRENT window's start is NOT FETCHED; a dated PREDECESSOR is.**

**SER S-6245R**, downloaded as raw bytes from the 2012-10-10 Wayback capture of
`http://www.cmegroup.com/rulebook/files/SER-6245R_-_CBOT_Ag_Futures_Settlements_-_06-08-2012_x3x.pdf` ·
accessed 2026-09-21:

> "S-6245 R           June 8, 2012" · "New Settlement Methodology for CBOT Agricultural Futures
> Effective June 25, 2012"
>
> "The designated lead month will be settled to the volume-weighted average price ("VWAP") of all
> outright trades executed in the pit and on Globex from 13:59:00-14:00:00 Central Time ("CT")."
>
> "Soybean Oil and Soybean Meal presently close on a month-by-month rotation that begins after 13:15
> CT. Beginning June 25, the settlement period for Soybean Oil and Soybean Meal will be
> 13:59:00-14:00:00 CT"
>
> "Expiration Procedures:  On the last trading day of an expiring contract, the settlement period for
> the expiring contract will be 12:00:00-12:01:00 CT"

It names "Corn, Wheat, Oats, Rough Rice, Soybeans, Soybean Meal and Soybean Oil" — **not KC HRW
Wheat**, which was a KCBT contract in June 2012. That is why KE carries no `record_only` row.

**What ended it is not sourced.** The nearest dated notice found is **SER-6617** (browser pane,
`https://www.cmegroup.com/tools-information/lookups/advisories/market-regulation/SER-6617.html`,
accessed 2026-09-21):

> "Changes in Trading Hours for CBOT Grain and Oilseed and KCBT Markets" · Notice Date "01 April
> 2013" · Effective Date "07 April 2013"
>
> "Based on feedback from a broad cross-section of grain and oilseed market participants, effective
> Sunday, April 7 (trade date Monday, April 8), all CBOT grain and oilseed futures and options
> including all related calendar spread and inter-commodity spread options and KCBT Wheat futures and
> options trading hours will be modified."

That is a **trading-hours** notice, not a settlement-window notice. The 13:59–14:00 CT window is
therefore carried as `record_only` with its end unsourced, and the current window as `current_only`.

**A notice that was checked and does NOT bear on the window.** **SER-7395R** (browser pane,
`https://www.cmegroup.com/tools-information/lookups/advisories/ser/SER-7395R.html`, accessed
2026-09-21), Notice Date "17 June 2015", Effective Date "05 July 2015", extends Globex hours from
1:15 p.m. to 1:20 p.m. CT and adds a floor post-close for **options** — "on the trading floor a
post-close session for all grain and oilseed options will be held immediately following the market
close at 1:15 pm CT and trade until 1:20 pm CT" — leaving the futures close, and so the settlement
window, at 13:15 CT.

---

## 4. CME livestock — LE, HE — 12:59:30–13:00:00 **CT**, and only thirty seconds long

Confluence `Livestock` (457317920, page version 2026-07-15):

> "CME Group staff determines the daily settlements for Feeder Cattle (GF), Lean Hogs (HE), Live
> Cattle (LE), and Pork Cutout (PRK) futures based on trading activity on CME Globex between 12:59:30
> and 13:00:00 Central Time (CT), the settlement period."
>
> "Tier 1:  Each contract month settles to its volume-weighted average price (VWAP) of all trades
> that occur between 12:59:30 and 13:00:00 CT, the settlement period, rounded to the nearest tradable
> tick. If the VWAP is exactly in the middle of two tradable ticks, then the settlement will be the
> tradable price that is closer to the contract's prior day settlement price."

Note that livestock settles **per contract month** off its own VWAP — there is no lead-month anchor
and no spread-implied tier, unlike every other group here.

**History: NOT FETCHED.** `current_only`. The December-2014 move off a pit-only settlement is
described in the secondary literature (the CFTC's pit-closure paper) but **no CME notice stating the
window was located**, and a secondary source is not a source for a time.

---

## 5. CME equity index — ES, NQ — 14:59:30–15:00:00 CT, and the one change the brief predicted

### 5a. The effective date, and the superseded window verbatim

**SER-8591**, downloaded as raw bytes from the 2024-12-20 Wayback capture of
`https://www.cmegroup.com/notices/ser/2020/09/SER-8591.pdf` · accessed 2026-09-21.

> "DATE: September 22, 2020" · "SER#:  8591" · "SUBJECT: Amendments to the Daily Settlement Procedure
> Documents for Certain CME and CBOT Equity Products"
>
> "Effective Sunday, October 25, 2020 for trade date Monday, October 26, 2020, and pending all
> relevant CFTC regulatory review periods, Chicago Mercantile Exchange Inc. ("CME") and The Board of
> Trade of the City of Chicago, Inc. ("CBOT") (collectively, the "Exchanges") will amend the Daily
> Settlement Procedure Documents relating to certain CME and CBOT futures and options on futures
> contracts"
>
> "Specifically, the Exchanges are implementing amendments to change the daily settlement price
> determination period of the Contracts from 3:15 p.m. Central Time (CT) to 3:00 p.m. CT. The
> amendments will synchronize settlement times of the Contracts with the related cash equity market."

Its Exhibit A names, among others, "E-mini S&P 500 Futures", "Micro E-mini S&P 500 Index Futures",
"E-mini Nasdaq-100 Futures" and "Micro E-mini Nasdaq-100 Index Futures" — which is also the source
for MES and MNQ inheriting their parents' rows.

Its Exhibit B is a blackline, and that is where the **superseded** window's exact text comes from
(additions underlined, deletions struck through; the deleted text is the first of each pair):

> "Tier 1: The volume-weighted average price ("VWAP") of all trades executed in the full-sized futures
> contract on the trading floor and in the E-mini futures contract executed on CME Globex will be
> calculated for the designated lead month contract from 15:14:30 – 15:15:00 14:59:30 to 15:00:00
> Central Time ("CT"), the settlement period.  A multiplier of 5 will be applied to the quantities
> traded in the full-sized contract to reflect the 5 to 1 relationship between the full-sized and the
> E-mini contracts.  The combined VWAP for the designated lead month will be rounded to the nearest
> .10 index point."

**The start of that superseded period is not given anywhere in SER-8591**, so its row is
`record_only`: the window is recorded, its end (2020-10-23, the last trade date before the change)
is sourced, and `window_for` never returns it.

### 5b. The current wording

Confluence `E-Mini Standard and Poors 500 Futures` (457418067, page version 2026-08-20):

> "The volume-weighted average price ("VWAP") of all trades executed on CME Globex between 14:59:30
> and 15:00:00 CT, the settlement period, in the E-mini S&P futures will be calculated for the
> designated lead month and rounded to the nearest .25 index point."
>
> "If no trades in the lead month occur between 14:59:30 and 15:00:00 CT, then the contract month
> settles to the midpoint of the Bid/Ask between 14:59:30 to 15:00:00 CT, the settlement period."
>
> "Daily settlement of the Micro E-mini S&P futures (MES) and E-Nano S&P 500 (NES) are equal to the
> daily settlement price of the E-Mini S&P 500 futures (ES)."

Confluence `Nasdaq-100` (457222172, page version 2026-08-20):

> "Tier 1:   If the lead month contract trades on Globex between 14:59:30 and 15:00:00 Central Time
> (CT), the settlement period, then the lead month settles to the volume-weighted average price
> (VWAP) of the trade(s) during this period."
>
> "Tier 2:   If no trades in the lead month occur on Globex between 14:59:30 and 15:00:00 CT, then the
> contract month settles to the midpoint of the Bid/Ask between 14:59:30 and 15:00:00 CT, the
> settlement period."
>
> "Daily settlement of the Micro contracts are equal to the settlement price of their associated Mini
> contracts."

Note the ES rounding is stated as **.25 index point** on the current page and **.10** in the
superseded blackline; both are transcribed into the `basis` column of their own row rather than
harmonised.

---

## 6. Raw cache

`data/raw/cme_settlement/` (gitignored; a clone receives none of it):

| file | route | bytes |
|---|---|---:|
| `cme-group-settlement-procedures__wayback20250328085721__fetched_at_2026-09-21.pdf` | Wayback | 78,911 |
| `SER-8591__wayback20241220125115__fetched_at_2026-09-21.pdf` | Wayback | 108,884 |
| `SER-6245R-CBOT-Ag-Futures-Settlements__wayback20121010220311__fetched_at_2026-09-21.pdf` | Wayback | 83,298 |
| `confluence_{457085528,457088078,457088147,457090243,457218849,457222172,457317920,457321296,457414829,457415061,457415161,457415360,457415464,457418067}_*__fetched_at_2026-09-21T1930Z.json` | Confluence REST | 9,202–24,367 each |

The SER HTML pages (SER-4867, SER-6617, SER-7395R, SER-9637) were read through the browser pane and
are **not** in the cache: the pane returns rendered text, not response bytes, and writing a
transcription into a file named like a raw capture would make it look like something it is not. The
quotes above are that rendered text, and each carries its URL so it can be re-read.
