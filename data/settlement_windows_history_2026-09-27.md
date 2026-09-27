# CME daily settlement windows, 2012 to 2025: history for GC SI HG, ZC ZS ZW KE ZL ZM, LE HE

*Sourced 2026-09-27. A sourcing record: it gives no strategy results and does not change `data/settlement_windows.csv`.
Every row cites a document that was fetched on **2026-09-27** (the access date for every URL below), and every quote
is 15 words or fewer, copied from the fetched bytes or rendered text. The raw copies are in
`data/raw/settlement_windows/` (gitignored). File names carry the Wayback timestamp and `fetched_at`. Where a
statement is an inference and no document says it, the text marks it **INFERRED**.*

## How it was fetched (the route matters)

| route | used for | note |
|---|---|---|
| `web.archive.org` CDX plus `id_` raw captures (`curl`, UA `Mozilla/5.0 (research data fetch)`) | old `cmegroup.com/confluence/display/EPICSANDBOX/*` pages (every distinct-digest capture of Livestock, Grains, Corn, Soybeans, Wheat, Soybean Oil, Soybean Meal, KC HRW Wheat, Gold, Silver, Copper, Metals, Daily Settlement Time Details), and old CME procedure PDFs | about 230 captures. The CDX API returned "Temporarily Offline" or 504 on several calls, and those calls were retried |
| `cftc.gov/filings/orgrules/*.pdf` (`curl`) | CME/CBOT/COMEX rule certifications | HTTP 200, plain PDFs |
| Claude desktop **browser pane** on `www.cmegroup.com` | SER-6617, SER-7213 and SER-8228 notice pages. PDFs were fetched in the same origin and text-extracted in the page with pdf.js | `curl` to cmegroup.com is still blocked from this machine (D586). The PDF bytes were **not** saved. The extracted text is saved as `SER-*__*text__fetched_at_2026-09-27.txt` |
| `cmegroupclientsite.atlassian.net/wiki/rest/api/content/{id}?status=historical&version=N` | every historical version of the current Confluence pages | the page history there starts **2024-12-21** (the migration date), so it covers only 2024-12 onward |

**One side effect to disclose:** opening the SER-8228 PDF URL directly in the browser pane made the app show a
**file-save dialog**. Nothing was saved through it. The PDF was then read in-page instead.

---

## Answers to the three questions

**(a) Grains, 13:59–14:00 CT to 13:14–13:15 CT.** Yes, the move came with the 2013 hours change. **SER-6617**
(notice 2013-04-01, effective Sunday 2013-04-07 for **trade date Monday 2013-04-08**) says: *"Settlement times will
move and be based on market activity at or around 1:15 p.m."* It also says: *"Daily settlement procedures remain
unchanged."* The exact 13:14:00–13:15:00 CT window is stated in CME's grain procedure PDF as captured on 2013-05-31.
The capture of 2012-10-12 still read 13:59:00–14:00:00. So SER-6245R's window ran from 2012-06-25 **through trade
date 2013-04-05**. From 2013-04-08 the window was 13:14:00–13:15:00 CT, **blended pit and Globex**. It became
**Globex-only when the pits closed in July 2015** (CBOT Submission 15-212). The clock time never changed again
through 2025.

**(b) Livestock.** **Nothing shows a 1- or 2-minute window. The window has been 30 seconds, 12:59:30–13:00:00 CT,
since at least January 2012.** What changed was the **basis**, three times:
1. **pit-only**: the midpoint of pit trades or the last valid pit price, from at least 2012-01 to 2014-12-12;
2. **blended** pit VWAP plus Globex VWAP, from trade date **2014-12-15** (SER-7213);
3. **Globex-only**, from **July 2015** (CME Submission 15-211).

SER-8228 (trade date 2018-10-01) changed only the no-trade fallback tiers. **The window's start is inside the
requested range: 2014-12-01 to 2014-12-12 settled pit-only**, so the Globex 30 seconds did not set those settlements.

**(c) Metals.** **The clock windows held from at least October 2012 through 2025:** GC 13:29–13:30 ET, SI 13:24–13:25
ET and HG 12:59–13:00 ET. The 2015 pit closure changed **HG's basis** from pit plus Globex to Globex-only (COMEX
Submission 15-214). GC and SI were already described as Globex-only in 2012–2015. Nothing in 2016, 2019 or 2020
moved an active-month window. The Confluence page edits (2017-10, 2018-08, 2019-10, 2020-01) and SER-9185 (2023,
called "administrative, non-substantive" for GC SI HG) all keep the same windows. **One conflicting document** is
recorded below: the master table's 2015-08-13 version gave "12:58:00-13:00:00 ET" for all three metals.

---

## Pit-closure date: a conflict that does not move any window

| source | says |
|---|---|
| CBOT 15-212 / COMEX 15-214 (2015-06-08), CME 15-211 (2015-06-12), certifications on cftc.gov | revised procedures *"effective on Monday, July 6, 2015"*; contracts *"will no longer trade via open outcry beginning July 6, 2015"* |
| CME/CBOT/COMEX 40.6(a) filings of 2015-06-10 ([CME](https://www.cftc.gov/filings/orgrules/rule061115cmedcm001.pdf), [CBOT](https://www.cftc.gov/filings/orgrules/rule061115cbotdcm002.pdf), [COMEX](https://www.cftc.gov/filings/orgrules/rule061115comexdcm001.pdf)) | open outcry futures close *"after the close of open outcry trading on July 2, 2015"* |
| [CME press release, 2015-06-23](https://www.cmegroup.com/media-room/press-releases/2015/6/23/cme_group_delaysclosureofopenoutcryfuturestradinginchicagoandnew.html) (browser pane) | the last day *"is now expected to take place on Monday, July 6"* |
| [CFTC OCE paper (Gousgounis and Onur)](https://www.cftc.gov/sites/default/files/idc/groups/public/@economicanalysis/documents/file/oce_effectofpitclosure.pdf), secondary | *"On July 6th 2015, floor trading ceased"* (a footnote marker is fused into the year in the PDF text); pits closed as of *"July 7th 2015"* |

**My read (INFERRED):** trade date **2015-07-06** was the last pit day for grains, livestock and COMEX metals
futures, so the **first Globex-only settlement was 2015-07-06 or 2015-07-07**. The filings name July 6. The delay
notice and CFTC OCE imply pits still traded on July 6. No CME notice that settles this for settlement purposes was
found. The **clock window is the same on both sides of this date**, so only a pit-versus-Globex basis flag depends
on it.

---

## GC: COMEX Gold (active month)

| window | tz | basis | effective_from | effective_to | source | doc date | quote (≤15 words) |
|---|---|---|---|---|---|---|---|
| 13:29:00–13:30:00 | ET | VWAP of **Globex** trades, active month | ≤ 2012-10-16 (earliest dated capture; no start notice found) | 2015-07-05 | [daily-settlement-procedure-gold-futures.pdf, Wayback 2012-10-16](https://web.archive.org/web/20121016212123/http://www.cmegroup.com/trading/metals/files/daily-settlement-procedure-gold-futures.pdf) | capture 2012-10-16 | "based on CME Globex activity between 13:29:00 and 13:30:00 Eastern Time (ET)" |
| same | ET | same | — | — | [same PDF, Wayback 2015-04-19](https://web.archive.org/web/20150419162440/http://www.cmegroup.com/trading/metals/files/daily-settlement-procedure-gold-futures.pdf) | capture 2015-04-19 | "If a trade(s) occurs on Globex between 13:29:00 and 13:30:00 ET" |
| 13:29:00–13:30:00 | ET | Globex-only; spreads Globex-only (the blackline deletes the floor wording) | 2015-07-06 | — (still current) | [COMEX Submission 15-214, cftc.gov](https://www.cftc.gov/filings/orgrules/rule060815comexdcm001.pdf) | 2015-06-08 | "based exclusively on activity on CME Globex" |
| 13:29:00–13:30:00 | ET | Globex; from 2017 the spreads use ≥25 lots, 13:15–13:30 ET | — | — | Confluence Gold captures [2015-08-16](https://web.archive.org/web/20150816191525/http://www.cmegroup.com:80/confluence/display/EPICSANDBOX/Gold) … [2024-05-20](https://web.archive.org/web/20240520125040/https://www.cmegroup.com/confluence/display/EPICSANDBOX/Gold) (37 captures, all with this window) | page versions Jul 2015 to Apr 2024 | "between 13:29:00 and 13:30:00 Eastern Time (ET), the settlement period" |
| 13:29:00–13:30:00 | ET | unchanged ("administrative, non-substantive") | 2023-08-30 | — | [COMEX 23-170 Exhibit A, cftc.gov](https://www.cftc.gov/filings/orgrules/rules0815235374.pdf) | 2023-08-15 | "The settlement period is defined as: 13:29:00 to 13:30:00 ET" |
| 13:29:00–13:30:00 | ET | Globex | — | — | [Confluence 457088147 v1–v6](https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457088147/Gold) (2024-12-21 … 2025-09-26) | page versions | "13:29:00 to 13:30:00 ET for the active month" |
| **12:58:00–13:00:00** (CONFLICT) | ET | master table row only | — | — | [Daily Settlement Time Details, Wayback 2015-09-07](https://web.archive.org/web/20150907124144/http://www.cmegroup.com/confluence/display/EPICSANDBOX/Daily+Settlement+Time+Details) | page version 2015-08-13 | "Gold 12:58:00-13:00:00 ET" |

- **Conflict 1 (master table).** The 2015-08-13 version of *Daily Settlement Time Details* lists Gold, Silver,
  Copper **and** Platinum all as 12:58:00–13:00:00 ET. The Gold product page captured the same month says 13:29–13:30.
  So does the COMEX 15-214 blackline, which took effect six weeks earlier. The next table version (2015-09-08) lists
  13:29:00–13:30:00. **My read: this was a transcription error in the table.** No notice moved the window.
- **Conflict 2 (basis before July 2015).** The 15-214 blackline strikes *"by incorporating both Floor-based and
  Globex-"* from the Gold and Silver daily procedures. That implies the pre-July-2015 text was blended. The
  published Gold PDF (2012-10 and 2015-04 captures) and the master procedures PDF (2012-01 to 2015-02) both say the
  active month settles on **Globex** trades only. UNRESOLVED; the clock window is the same either way.
- **NOT FOUND:** any notice that *set* 13:29–13:30 ET (looked in: SER search, CFTC filings of June 2015 and August
  2023, Wayback captures back to 2012-01). Also no GC document before 2012-10-16 states the time. The 2012-01 master
  PDF says only *"during the defined settlement time period"*.
- **Read for 2015-01 → 2025-02:** **the current window was in force for the whole period.** The basis was Globex
  VWAP throughout (with the Conflict 2 caveat for the months before July 2015).

## SI: COMEX Silver (active month)

| window | tz | basis | effective_from | effective_to | source | doc date | quote (≤15 words) |
|---|---|---|---|---|---|---|---|
| 13:24:00–13:25:00 | ET (= 12:24–12:25 CT) | VWAP of Globex trades, active month | ≤ 2012-10-17 | 2015-07-05 | [daily-settlement-procedure-silver-futures.pdf, Wayback 2012-10-17](https://web.archive.org/web/20121017003702/http://www.cmegroup.com/trading/metals/files/daily-settlement-procedure-silver-futures.pdf) | capture 2012-10-17 | "based on CME Globex activity between 13:24:00 and 13:25:00 Eastern Time (ET)" |
| same | ET | same | — | — | [same, Wayback 2015-04-19](https://web.archive.org/web/20150419184942/http://www.cmegroup.com/trading/metals/files/daily-settlement-procedure-silver-futures.pdf) | capture 2015-04-19 | "If a trade occurs on Globex between 13:24:00 and 13:25:00 ET" |
| 13:24:00–13:25:00 | ET | Globex-only | 2015-07-06 | — (current) | [COMEX Submission 15-214](https://www.cftc.gov/filings/orgrules/rule060815comexdcm001.pdf) | 2015-06-08 | "based on trading activity on CME Globex between 13:24:00 and 13:25:00 Eastern" |
| 13:24:00–13:25:00 | ET | Globex; spreads ≥25 lots, 13:10–13:25 ET from 2017 | — | — | Confluence Silver captures [2015-10-09](https://web.archive.org/web/20151009022221/http://www.cmegroup.com:80/confluence/display/EPICSANDBOX/Silver) … [2022-06-25](https://web.archive.org/web/20220625164632/https://www.cmegroup.com/confluence/display/EPICSANDBOX/Silver) (19 captures) | Jul 2015 to 2022 | "between 13:24:00 and 13:25:00 Eastern Time (ET), the settlement period" |
| 13:24:00–13:25:00 | ET | unchanged | 2023-08-30 | — | [COMEX 23-170 Exhibit A](https://www.cftc.gov/filings/orgrules/rules0815235374.pdf) | 2023-08-15 | "The settlement period is defined as: 13:24:00 to 13:25:00 ET" |
| 13:24:00–13:25:00 | ET | Globex | — | — | [Confluence 457415360 v1–v5](https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457415360/Silver) (2024-12-21 … 2025-10-13) | page versions | "13:24:00 to 13:25:00 ET for the active month" |
| **12:58:00–13:00:00** (CONFLICT) | ET | master table only | — | — | [Daily Settlement Time Details, Wayback 2015-09-07](https://web.archive.org/web/20150907124144/http://www.cmegroup.com/confluence/display/EPICSANDBOX/Daily+Settlement+Time+Details) | 2015-08-13 | "Silver 12:58:00-13:00:00 ET" |

- The time zone varies by document. **Every historical version (2012–2025-10) states Silver in ET.** D586 records
  that the current product page states 12:24–12:25 **CT**. That is the same instant, and the switch falls after
  2025-10-13, outside the range.
- **NOT FOUND:** a notice setting 13:24–13:25 ET; any SI source before 2012-10-17 that gives the time. Conflicts 1
  and 2 are as for GC.
- **Read for 2015-01 → 2025-02:** **current window in force throughout.**

## HG: COMEX Copper (active month)

| window | tz | basis | effective_from | effective_to | source | doc date | quote (≤15 words) |
|---|---|---|---|---|---|---|---|
| 12:59:00–13:00:00 | ET | **VWAP of Globex and COMEX floor** trades (blended) | ≤ 2012-10-23 | 2015-07-05 (INFERRED; see pit-closure note) | [daily-settlement-procedure-copper-futures.pdf, Wayback 2012-10-23](https://web.archive.org/web/20121023040530/http://www.cmegroup.com/trading/metals/files/daily-settlement-procedure-copper-futures.pdf) | capture 2012-10-23 | "trades executed on Globex and the COMEX floor between 12:59:00 and 13:00:00 ET" |
| (blended, time not stated) | — | blended | — | — | [cme-group-settlement-procedures.pdf, Wayback 2015-02-26](https://web.archive.org/web/20150226065615/http://www.cmegroup.com:80/market-data/files/cme-group-settlement-procedures.pdf) | capture 2015-02-26 | "VWAP of all trades occurring on Globex and in the pit during the closing range" |
| 12:59:00–13:00:00 | ET | **Globex-only** | 2015-07-06 | — (current) | [COMEX Submission 15-214](https://www.cftc.gov/filings/orgrules/rule060815comexdcm001.pdf) (blackline strikes the floor wording; the window is unchanged) | 2015-06-08 | "based on trading activity on CME Globex between 12:59:00 and 13:00:00 Eastern" |
| 12:59:00–13:00:00 | ET | Globex; spreads 12:30–13:00 ET | — | — | Confluence Copper captures [2015-09-09](https://web.archive.org/web/20150909012044/http://www.cmegroup.com/confluence/display/EPICSANDBOX/Copper) … [2022-12-24](https://web.archive.org/web/20221224193041/https://www.cmegroup.com/confluence/display/EPICSANDBOX/Copper) (11 readable captures) | page versions Jul 2015 to Aug 2018 | "based on trading activity on CME Globex between 12:59:00 and 13:00:00 Eastern Time" |
| 12:59:00–13:00:00 | ET | unchanged | 2023-08-30 | — | [COMEX 23-170 Exhibit A](https://www.cftc.gov/filings/orgrules/rules0815235374.pdf) | 2023-08-15 | "The settlement period is defined as: 12:59:00 to 13:00:00 ET" |
| 12:59:00–13:00:00 | ET | Globex | — | — | [Confluence 457415464 v1–v3](https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457415464/Copper) (2024-12-21 … 2025-10-13) | page versions | "12:59:00 to 13:00:00 ET for the active month" |
| **12:58:00–13:00:00** (CONFLICT) | ET | master table only | — | — | [Daily Settlement Time Details, Wayback 2015-09-07](https://web.archive.org/web/20150907124144/http://www.cmegroup.com/confluence/display/EPICSANDBOX/Daily+Settlement+Time+Details) | 2015-08-13 | "Copper 12:58:00-13:00:00 ET" |

- **NOT FOUND:** a notice that set 12:59–13:00 ET or introduced the blended VWAP. There are no copper PDF captures
  between 2012-10-23 and July 2015. The 12:59–13:00 window over that gap comes from the unstruck window text in the
  15-214 blackline, which describes the pre-change document.
- **Read for 2015-01 → 2025-02:** **same clock window throughout.** The basis was **pit plus Globex until the pit
  closure** (last pit day 2015-07-06, INFERRED) and **Globex-only after**. A Globex-only reconstruction of HG
  settlement before 2015-07 will not match the published settle exactly.

---

## ZC ZS ZW ZL ZM: CBOT grains and oilseeds (lead month; deferred months off spread VWAP in the same window)

| window | tz | basis | effective_from | effective_to | source | doc date | quote (≤15 words) |
|---|---|---|---|---|---|---|---|
| ZC ZS ZM ZL: Pit Committee "preponderance" in the closing range; ZW: 13:14:00–13:15:00 Globex VWAP | CT | pit committee (ZC ZS ZM ZL); Globex VWAP (ZW) | ≤ 2012-01-05 | 2012-06-22 | [cme-group-settlement-procedures.pdf, Wayback 2012-01-05](https://web.archive.org/web/20120105155731/http://www.cmegroup.com:80/market-data/files/CME_Group_Settlement_Procedures.pdf) | capture 2012-01-05 | "Wheat, Rice and Oats futures settle to the VWAP of trades on Globex" |
| 13:59:00–14:00:00 | CT | VWAP of pit **and** Globex outright trades | **2012-06-25** | **2013-04-05** (last trade date before SER-6617) | [SER S-6245R](https://www.cmegroup.com/rulebook/files/SER-6245R_-_CBOT_Ag_Futures_Settlements_-_06-08-2012_x3x.pdf) (cached from Wayback in `data/raw/cme_settlement/`, D586) | 2012-06-08 | "executed in the pit and on Globex from 13:59:00- 14:00:00 Central Time" |
| same | CT | same | — | — | [daily-grains-settlement-procedure.pdf, Wayback 2012-10-12](https://web.archive.org/web/20121012155814/http://www.cmegroup.com/trading/agricultural/files/daily-grains-settlement-procedure.pdf) | capture 2012-10-12 | "incorporating both Floor-based and Globex-based trading activity between 13:59:00 and 14:00:00 Central Time" |
| **13:14:00–13:15:00** | CT | blended pit and Globex, "procedures remain unchanged" | **2013-04-08** (trade date) | **2015-07-05 or 07-06** (see pit-closure note) | [SER-6617 notice page](https://www.cmegroup.com/tools-information/lookups/advisories/market-regulation/SER-6617.html) → [PDF](https://www.cmegroup.com/rulebook/files/ser_6617_cbot_grain_oilseed_hours_2013_final.pdf) (browser pane; text in `SER-6617__pdfjs-text__…txt`) | 2013-04-01 | "Settlement times will move and be based on market activity at or around 1:15 p.m." |
| 13:14:00–13:15:00 | CT | blended pit and Globex | — | — | [daily-grains-settlement-procedure.pdf, Wayback 2013-05-31](https://web.archive.org/web/20130531064343/http://www.cmegroup.com/trading/agricultural/files/daily-grains-settlement-procedure.pdf); also 2013-07-02 and 2014-07-18 captures | captures 2013-05-31 to 2014-07-18 | "incorporating both Floor-based and Globex-based trading activity between 13:14:00 and 13:15:00 Central Time" |
| 13:14:00–13:15:00 | CT | blended (Corn page) | — | — | [Confluence Corn, Wayback 2015-07-03](https://web.archive.org/web/20150703223044/http://www.cmegroup.com:80/confluence/display/EPICSANDBOX/Corn) (page version 2015-02-12) | 2015-02-12 | "incorporating both Floor-based and CME Globex-based trading activity" |
| **13:14:00–13:15:00** | CT | **Globex-only**; deferreds from spread VWAP in the same window | **2015-07-06/07** | — (current) | [CBOT Submission 15-212](https://www.cftc.gov/filings/orgrules/rule060815cbotdcm001.pdf) | 2015-06-08 | "determined based exclusively on activity on CME Globex" |
| 13:14:00–13:15:00 (Globex trading extended to 13:20) | CT | Globex | trade date 2015-07-06 | — | [CBOT Submission 15-204](https://www.cftc.gov/filings/orgrules/rule061115cbotdcm001.pdf) | 2015-06-09 | "not impact or influence the 1:14-1:15 p.m. CT settlement window" |
| 13:14:00–13:15:00 | CT | Globex | — | — | Confluence Grains captures [2015-07-04](https://web.archive.org/web/20150704205716/http://www.cmegroup.com:80/confluence/display/EPICSANDBOX/Grains) (version 2015-07-02) … [2024-05-24](https://web.archive.org/web/20240524043818/https://www.cmegroup.com/confluence/display/EPICSANDBOX/Grains) (20 readable); Corn, Soybeans, Wheat, Soybean Oil, Soybean Meal product pages 2015-08 … 2023-12 | 2015-07-02 to 2023-12-18 | "based on trading activity on CME Globex between 13:14:00 and 13:15:00 Central Time (CT)" |
| 13:14:00–13:15:00 | CT | Globex | — | — | [Confluence 457414829 v1–v2](https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457414829/Grains) (2024-12-21, 2024-12-24); master table 457085528 v1–v3 | page versions | "between 13:14:00 and 13:15:00 Central Time (CT), the settlement period" |

- **ZL and ZM before 2012-06-25** closed on a rotation after 13:15 CT (SER-6245R, recorded in D586). This is
  outside the requested range.
- **D586 correction.** SER-6617 is effective **Sunday 2013-04-07 for trade date Monday 2013-04-08**. The CSV note's
  "07 April 2013" is the calendar date and D586's prose "2013-04-08" is the trade date. Both are right. Also, SER-6617
  does state the settlement move. It does not give the exact seconds; the 2013-05-31 procedure PDF does.
- **NOT FOUND:** a CME notice that states the exact string "13:14:00–13:15:00" with an effective date. SER-6617
  says "at or around 1:15 p.m.", and the procedure PDF gives the seconds but no date. I looked in: SER-6617 (HTML and
  PDF), Wayback captures of the grain procedure PDF, and CME settlement procedure PDF captures from 2012-01 to 2015-09.
- **Read for 2015-01 → 2025-02:** **the current clock window was in force for the whole period.** The basis was
  **pit plus Globex until the July 2015 pit closure**, then Globex-only.

## KE: KC HRW Wheat

| window | tz | basis | effective_from | effective_to | source | doc date | quote (≤15 words) |
|---|---|---|---|---|---|---|---|
| (KCBT's own procedure) | — | — | — | before 2013-07 | NOT FOUND | — | — |
| trading hours only: close moved to 1:15 p.m. CT | CT | — | 2013-04-08 | — | [SER-6617](https://www.cmegroup.com/tools-information/lookups/advisories/market-regulation/SER-6617.html) lists "KCBT Wheat Futures & Options" | 2013-04-01 | "all CBOT grain and oilseed futures … and KCBT Wheat futures and options" (elided) |
| 13:14:00–13:15:00 | CT | blended floor and Globex, in the CBOT procedure | ≤ 2013-07-02 (first capture naming KE; the 2013-05-31 capture does not) | 2015-07-05/06 | [daily-grains-settlement-procedure.pdf, Wayback 2013-07-02](https://web.archive.org/web/20130702074705/http://www.cmegroup.com:80/trading/agricultural/files/daily-grains-settlement-procedure.pdf); 2014-07-18 capture names "KC HRW Wheat (KE)" | captures | "Soybean Oil (ZL) and KCBT Wheat (KE) futures by incorporating both Floor-based" |
| 13:14:00–13:15:00 | CT | Globex-only | 2015-07-06/07 | — (current) | [CBOT Submission 15-212](https://www.cftc.gov/filings/orgrules/rule060815cbotdcm001.pdf) names "KC HRW Wheat" | 2015-06-08 | "CBOT KC HRW Wheat Futures Final Settlement" (listed document) |
| 13:14:00–13:15:00 | CT | Globex | — | — | [Confluence KC HRW Wheat, Wayback 2015-09-06](https://web.archive.org/web/20150906132648/http://www.cmegroup.com/confluence/display/EPICSANDBOX/Kansas+City+Hard+Red+Wheat) … 2023-10-02 (8 captures) | 2015-07-15 to 2018-08-02 versions | "Kansas City Hard Red Wheat (KE) futures on trading activity on CME Globex" |

- **NOT FOUND:** the date KE entered the CBOT settlement procedure (bracketed between the 2013-05-31 and 2013-07-02
  captures), and KCBT's window before that. This is outside the requested range.
- **Read for 2015-01 → 2025-02:** **current window throughout.** The basis was blended until July 2015.

---

## LE HE: CME Live Cattle and Lean Hogs (each contract month settles to its own VWAP)

| window | tz | basis | effective_from | effective_to | source | doc date | quote (≤15 words) |
|---|---|---|---|---|---|---|---|
| 12:59:30–13:00:00 | CT | **pit-only**: midpoint of pit trades or the last valid pit price | ≤ 2012-01-05 | **2014-12-12** (last trade date before SER-7213) | [cme-group-settlement-procedures.pdf, Wayback 2012-01-05](https://web.archive.org/web/20120105155731/http://www.cmegroup.com:80/market-data/files/CME_Group_Settlement_Procedures.pdf); identical text in the 2012-10, 2013-05, 2014-01 and [2014-09-28](https://web.archive.org/web/20140928160811/http://www.cmegroup.com:80/market-data/files/cme-group-settlement-procedures.pdf) captures | captures 2012-01 to 2014-09 | "settled to the midpoint of the trades or the last valid price in the pit" |
| (context) | — | the last floor-only benchmark | — | — | [Quick Facts on Settlements, October 2014](https://web.archive.org/web/20210922054544/https://www.cmegroup.com/trading/agricultural/files/settlement-price-fact-sheet.pdf) | Oct 2014 | "After our CME livestock products transition to a blended settlement process in December 2014" |
| **12:59:30–13:00:00** | CT | **blended**: pit VWAP and Globex VWAP combined, volume-weighted | **2014-12-15** (trade date) | 2015-07-05/06 | [SER-7213](https://www.cmegroup.com/tools-information/lookups/advisories/market-regulation/SER-7213.html) (browser pane; text in `SER-7213__browser-pane-text__…txt`) | notice 2014-10-27 | "The two VWAPs will be combined to produce a single VWAP settlement price" |
| **12:59:30–13:00:00** | CT | **Globex-only** | **2015-07-06/07** | — (current) | [CME Submission 15-211](https://www.cftc.gov/filings/orgrules/rule061215cmedcm002.pdf) (blackline deletes the floor wording; window unchanged) | 2015-06-12 | "will be determined based exclusively on activity on CME Globex" |
| 12:59:30–13:00:00 | CT | Globex | — | — | Confluence Livestock captures [2015-09-06](https://web.archive.org/web/20150906194954/http://www.cmegroup.com/confluence/display/EPICSANDBOX/Livestock) (version 2015-07-15) … [2023-12-11](https://web.archive.org/web/20231211055112/https://www.cmegroup.com/confluence/display/EPICSANDBOX/Livestock) (23 of 30 captures readable; the other 7, from 2022-05 to 2023-08, are page shells with no procedure text); master table 2015-08 … 2024-02 | 2015-07-15 onward | "based on trading activity on CME Globex between 12:59:30 and 13:00:00 Central Time (CT)" |
| 12:59:30–13:00:00 | CT | Globex; fallback tiers changed (last trade validated vs bid/ask; net change validated) | 2018-10-01 (trade date) | — | [SER-8228](https://www.cmegroup.com/notices/ser/2018/09/SER-8228.html) → [PDF](https://www.cmegroup.com/content/dam/cmegroup/notices/ser/2018/09/SER-8228.pdf) (text in `SER-8228__pdfjs-text__…txt`) | 2018-09-11 | "The methodologies will be exactly the same with the exception of the settlement time windows." |
| 12:59:30–13:00:00 | CT | Globex | — | — | [Confluence 457317920 v1–v3](https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457317920/Livestock) (2024-12-21 … 2025-12-12); master table 457085528 v1–v3 | page versions | "between 12:59:30 and 13:00:00 Central Time (CT), the settlement period" |

- **NOT FOUND:** any 1-minute or 2-minute livestock daily window in 2012–2025. I looked in every capture above and
  in SER-7213, SER-8228, 15-211 and the current page history. The only 90-second window is the **expiring**
  contract's 11:58:30–12:00:00 CT, which is a different object.
- **NOT FOUND:** the notice that first set 12:59:30–13:00:00 for the pit close, before 2012-01.
- Later, outside the range: Confluence Livestock v4 (2026-07-15), plus CME Globex notices of July 2026 about
  "Livestock Market Enhancements". These were not read, because they fall after 2025-03-01.
- **Read for 2015-01 → 2025-02:** **the same 30-second clock window for the whole period.** The basis was
  **blended pit plus Globex from 2014-12-15 to the July 2015 pit closure**, then Globex-only. **The requested start,
  2014-12-01 to 2014-12-12, was pit-only** (the midpoint or last valid pit price, not a VWAP). A Globex-trade study
  of those two weeks is not scoring the settlement object.

---

## Summary

| root | clock window (every period 2014-12 to 2025-02) | basis changes inside 2014-12-01 → 2025-03-01 | current window in force all of 2015-01 → 2025-02? |
|---|---|---|---|
| GC | 13:29:00–13:30:00 ET | none on a window; Globex basis (Conflict 2 caveat before 2015-07) | **yes** |
| SI | 13:24:00–13:25:00 ET | as GC | **yes** |
| HG | 12:59:00–13:00:00 ET | pit plus Globex to 2015-07-05/06, then Globex | **yes** (clock); basis differs before July 2015 |
| ZC ZS ZW ZL ZM | 13:14:00–13:15:00 CT | pit plus Globex to 2015-07-05/06, then Globex | **yes** (clock); basis differs before July 2015 |
| KE | 13:14:00–13:15:00 CT | as grains | **yes** (clock) |
| LE HE | 12:59:30–13:00:00 CT | pit-only to 2014-12-12; blended 2014-12-15 → 2015-07-05/06; then Globex; tiers amended 2018-10-01 | **yes** (clock); basis differs before July 2015 |

## Every file saved (`data/raw/settlement_windows/`, gitignored)

- `cme-group-settlement-procedures__wayback{20120105155731,20121010131134,20130522063951,20140124061734,20140928160811,20150226065615,20150906112746}__…pdf`
- `daily-grains-settlement-procedure__wayback{20121012155814,20130531064343,20130702074705,20140718082853}__…pdf`, `CBOT-VWAP-Settlement-FAQ__wayback20120901164413__…pdf`
- `daily-settlement-procedure-{gold,silver}-futures__wayback{2012…,20150419…}__…pdf`, `daily-settlement-procedure-copper-futures__wayback20121023040530__…pdf`
- `settlement-price-fact-sheet__wayback20210922054544__…pdf`, `globex-notice-20141124__wayback20191019041855__…html` (no livestock content)
- `wayback_EPICSANDBOX_{Livestock,Grains,Corn,Soybeans,Wheat,Soybean-Oil,Soybean-Meal,Kansas-City-Hard-Red-Wheat,Gold,Silver,Copper,Metals,Daily-Settlement-Time-Details}__<ts>__…html` (about 230)
- `cftc_rule060815cbotdcm001` (15-212), `cftc_rule060815comexdcm001` (15-214), `cftc_rule061215cmedcm002` (15-211), `cftc_rule061115{cbotdcm001 (15-204), cbotdcm002, cmedcm001, comexdcm001}`, `cftc_rules081523537{3,4}` (23-170), `cftc_PitClosurePaper_livestock`, `cftc_oce_effectofpitclosure` (all `__fetched_at_2026-09-27.pdf`)
- `confluence_{457317920_livestock,457414829_grains,457088147_gold,457415360_silver,457415464_copper,457085528_daily-settlement-time-details}_v{N}__fetched_at_2026-09-27.json`
- `SER-6617__pdfjs-text__…txt`, `SER-7213__browser-pane-text__…txt`, `SER-8228__pdfjs-text__…txt`
