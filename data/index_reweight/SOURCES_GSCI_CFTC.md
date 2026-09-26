# Sources: S&P GSCI (R-Q4) and CFTC CIT / Disaggregated COT (R-Q9, R-Q10)

Spec: `docs/internal/User-Doc-Deposit/INDEX_REWEIGHT_FLOW_PREREG.md` §2–5A, §16.
Every source below was fetched on **2026-09-26** (the access date for every row).
Quotes are ≤15 words. "DERIVED" marks something computed here from sourced numbers;
it is not itself a published fact. Anything not found is in the NOT FOUND list (§6),
with where I looked. Nothing here is inferred silently.

Retrieval note: spglobal.com returns HTTP 403 to curl/WebFetch (Akamai). The S&P PDFs
were read in the desktop browser pane (same-origin fetch, text extracted with pdf.js).
The methodology PDF fetched that way is **byte-identical** to the copy the principal
supplied (sha256 below), so the principal's copy is the citable file.

---

## 1. Source register

| id | document | version / date | URL | notes |
|---|---|---|---|---|
| S1 | S&P GSCI Methodology | **August 2026** (HTTP Last-Modified 2026-08-17) | https://www.spglobal.com/spdji/en/documents/methodologies/methodology-sp-gsci.pdf | supplied by the principal: `data/raw/index_reweight/methodology-sp-gsci_2026-08.pdf`, sha256 `5c42716d7da4e2c92fa5c6a689e2d6df92b9f33c6edfb9921ea8ab9b4a918fed`, 1,025,164 bytes; the online file hashed identically on 2026-09-26 |
| S2 | S&P DJI Commodity Index Mathematics Methodology | August 2025 | https://www.spglobal.com/spdji/en/documents/methodologies/methodology-commodity-index-math.pdf | linked from S1 |
| S3 | S&P Commodities Indices Policies & Practices | February 2026 | https://www.spglobal.com/spdji/en/documents/index-policies/sp-commodities-indices-policies-practices.pdf | linked from S1 |
| S4 | S&P GSCI Reference Guide (has "Appendix: Examples from the 2016 S&P GSCI Methodology") | February 2016 | https://www.spglobal.com/spdji/en/documents/methodologies/methodology-sp-gsci-quick-guide.pdf | carries 2015 and 2016 CPWs |
| S5 | S&P GSCI Methodology, **third-party mirror** (Daishin Securities ETN documents) | February 2018 | https://etn.daishin.com/e5_data/mboard/etn_product/2018/06/9_00_methodology-sp-gsci-2x-zinc.pdf | sha256 `337f4622679ca9a3bb256d5d032e1240fbc34ad77c471d990622c86c83261b81`. Not S&P-hosted. Its 2018 CPW column matches A2019 (S&P-hosted) on **24 of 24** rows, so its 2017 CPW column is used, flagged as mirror-sourced |
| A2019 | "Continued Petroleum Sector Strength as S&P DJI Announces 2019 S&P GSCI Weights" | 2018-11-01 | https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20181101-810162/810162_spgsci2019cpwindexannouncement.pdf | also mirrored at spice-indices.com (…/810162_spgsci2019cpwindexannouncement.pdf) |
| A2020 | "Energy Sector Continues To Lead as S&P DJI Announces 2020 S&P GSCI Weights" | 2019-11-07 | https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20191107-1028759/1028759_spgsci2020cpwindexannouncement.pdf | |
| A2021 | "S&P DJI Announces 2021 S&P GSCI Weights" | 2020-11-12 | https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20201112-1255559/1255559_spgsci2021cpwindexannouncement.pdf | |
| A2022 | same title, 2022 | 2021-11-11 | https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20211111-1445034/1445034_spgsci2022cpwindexannouncement.pdf | |
| A2023 | same title, 2023 | 2022-11-10 | https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20221110-1457679/1457679_spgsci2023cpwindexannouncement.pdf | |
| A2024 | same title, 2024 | 2023-11-09 | https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20231109-1467463/1467463_spgsci2024cpwindexannouncement.pdf | |
| A2025 | same title, 2025 | 2024-11-08 | https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20241108-1475176/1475176_spgsci2025cpwindexannouncement.pdf | |
| A2026a | same title, 2026 (first issue) | 2025-11-06 | https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20251106-1480756/1480756_spgsci2026cpwindexannouncement.pdf | **its 2025 RPDW column is wrong for the 8 agricultural rows** (they repeat the livestock values); see §5 |
| A2026b | same title, 2026 (re-issue) | 2025-11-12 | https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20251112-1480941/1480941_spgsci2026cpwindexannouncement.pdf | corrected 2025 RPDW column; CPW table identical to A2026a |
| P2023 | "Review of 2023 S&P GSCI Rebalancing", S&P GSCI Advisory Panel | 2022-10-13 | https://www.spglobal.com/spdji/en/documents/research/2023-sp-gsci-rebalance-advisory-panel.pdf | ISL history 2004–2023 |
| P2026 | "2026 S&P GSCI Advisory Panel" (marked "Private & Confidential", publicly hosted) | 2025-10-09 | https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20251009-1480141/1480141_2026s&pgscirebalance-advisorypanel.pdf | ISL 2025 and 2026 |
| SV25 | S&P DJI Annual Survey of Assets, as of 2025-12-31 | 2026 | https://www.spglobal.com/spdji/en/documents/index-news-and-announcements/spdji-indexed-asset-survey-2025.pdf | GSCI not broken out |
| C1 | CFTC, COT Historical Compressed | live page | https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm | |
| C2 | CFTC, About the COT Reports | live page | https://www.cftc.gov/MarketReports/CommitmentsofTraders/AbouttheCOTReports/index.htm | |
| C3 | CFTC, COT Explanatory Notes (section "Supplemental Report") | live page | https://www.cftc.gov/MarketReports/CommitmentsofTraders/ExplanatoryNotes/index.htm | |
| C4 | CFTC, Commitments of Traders landing page ("Types of Reports") | live page | https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm | |
| C5 | CFTC, current CIT report (viewable) | positions as of 2026-09-22 | https://www.cftc.gov/dea/options/deaviewcit.htm | |
| C6 | CFTC, "Commission Actions in Response to the Comprehensive Review of the COT Reporting Program" | 2006-12-05 | https://www.cftc.gov/idc/groups/public/@commitmentsoftraders/documents/file/noticeonsupplementalcotrept.pdf | sha256 `954dda0a504d38dc1f04dc868f090f4fcdb4024740283b6de079922ed5c44871` |
| C7 | CFTC, COT Historical Special Announcements | live page | https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm | |
| C8 | CFTC, COT Release Schedule | live page (2026 schedule) | https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm | |
| C9 | CFTC, Disaggregated Explanatory Notes | live page | https://www.cftc.gov/MarketReports/CommitmentsofTraders/DisaggregatedExplanatoryNotes/index.htm | |
| C10 | CFTC Public Reporting Environment (Socrata) dataset metadata | live | https://publicreporting.cftc.gov/api/views/4zgm-a668.json ; …/72hh-3qpy.json ; …/kh3c-gbw2.json | metadata only, no rows fetched |
| C11 | CFTC, Index Investment Data (IID) page and discontinuation release | 2015-11-20 | https://www.cftc.gov/MarketReports/IndexInvestmentData/index.htm ; https://www.cftc.gov/PressRoom/PressReleases/7282-15 | out of the 2016–2027 window; lead only |

---

## 2. R-Q4 — S&P GSCI

### 2.1 Monthly roll period and daily fractions

| fact | source | location |
|---|---|---|
| The roll runs from the **5th to the 9th business day** of every month. Quote: "roll period is from the 5th business day to the 9th business day monthly" | S1 | "Contract Roll Weights and Monthly Roll Period", PDF p.13 (printed p.12) |
| Roll-out / roll-in weights by day: **BD5 80/20, BD6 60/40, BD7 40/60, BD8 20/80, BD9 0/100**. So 20% of the position moves at each of the five settlements BD5..BD9 (φ_d = 0.2 × 5) | S1 | same table |
| The January roll (and any reweighting roll) moves into the new CPWs and normalizing constant during the regular monthly roll period | S1 | same page |
| Market disruption on a roll day: that day's weights are held, and the day's portion moves to the next contract business day with no disruption | S1 | "Adjustment of Roll Period", PDF p.13–14 (printed p.12–13) |
| An **exchange holiday** on a roll day, or a **limit price**, also triggers the adjustment: the portion rolls on the next undisrupted business day | S3 | "Market Disruption Events and Holidays During Roll Period" (TOC p.5) |
| The same 5-day schedule and weights, in the older wording: "fifth (5th) S&P GSCI Business Day of the month", 80/20 then 60/40, 40/60, 20/80, 0/100 | S5 (Feb 2018) and S4 (Feb 2016) | S5 "Calculation of the S&P GSCI" section; S4 roll-weight paragraph |
| Calendar: "The index is calculated daily based on the CME Group holiday schedule" | S1 | "Holiday Schedule", PDF p.17 (printed p.16) |
| **Conflicting calendar:** the S&P GSCI Business Day is defined "as determined by the NYSE Euronext Holiday & Hours schedule" | S3 | glossary, "S&P GSCI Business Day" (printed p.18) |

**Overlap with BCOM (the GSCI side only; BCOM's days are not verified here).** GSCI trades at the settlements of BD5–BD9. If BCOM rolls on BD6–BD10 (the spec's belief, R-Q1), the two schedules share **BD6–BD9 (4 of 5 days each)**. BD5 would be GSCI-only and BD10 BCOM-only. Caveat: each index counts business days on its own calendar, and S&P's own documents disagree on GSCI's (CME in S1, NYSE in S3). The nth business day can therefore fall on different dates for the two indices when a holiday is observed by one exchange and not the other.

### 2.2 Annual reweighting: timing, announcement, determination

| fact | source | location |
|---|---|---|
| New CPWs "are implemented during the January roll period" | S2 | "Calculation of the Contract Production Weights", PDF p.8 (printed p.7) |
| Effective day in each announcement: 2019-01-08, 2020-01-08, 2021-01-08, **2022-01-07**, **2023-01-09**, 2024-01-08, 2025-01-08, 2026-01-08. Each is the first day of the January roll | A2019–A2026b | page 1, paragraph 2 of each |
| DERIVED check: each of those dates is the 5th weekday of January after skipping Jan 1 and the observed holiday (Jan 2 2023). This is consistent with BD5 | — | — |
| Announcement timing: "Annual Weights: First week of November", annual | S3 | "Announcements" table (TOC p.4) |
| Actual announcement dates: 2018-11-01 (2019), 2019-11-07 (2020), 2020-11-12 (2021), 2021-11-11 (2022), 2022-11-10 (2023), 2023-11-09 (2024), 2024-11-08 (2025), 2025-11-06 and re-issued 2025-11-12 (2026) | A2019–A2026b | dateline, page 1 |
| Several are **later than the first week of November** (Nov 9–12 in 2020–2023 and 2025's re-issue), so S3's timing is a guideline, not the observed date | — | DERIVED from the rows above |
| An advisory-panel pro-forma precedes each announcement by about a month: P2023 is dated 2022-10-13, P2026 2025-10-09 | P2023, P2026 | cover pages |
| Rebalancing announcements "are made two days prior to the rebalancing date" | S1 | "Announcements", PDF p.17 (printed p.16) |
| Volume window for the CPWs: annual calculation period = September of the previous year to August of the current year | S1 | "Contract Volume and Liquidity Requirements", PDF p.6 (printed p.5) |
| Quarterly TVM review on the last business day of the January quarterly cycle | S1 | PDF p.10 (printed p.9) |
| **No price-based "multiplier determination date" exists for GSCI.** CPWs are fixed quantities published in November. Only the **normalizing constant** is set from prices: it "calculates on the reference day prior to the reconstitution period" and is applied during the roll | S2 | "Calculation of the Normalizing Constant", PDF p.7 (printed p.6) |
| Older and more explicit: NC_new "is calculated on the last S&P GSCI Business Day of the previous S&P GSCI Period", from first-nearby DCRPs, with NC_new = NC_old × TDWR and TDWR = Σ CPW_new·DCRP / Σ CPW_old·DCRP | S5 | "Calculation of the Normalizing Constant" |
| DERIVED: the new period starts on the first day of the January roll (BD5), so the NC reference day is **BD4 of January**. This is GSCI's analogue of BCOM's CIM determination date (spec §3.2). S1/S2 do not name the business day, so treat it as unconfirmed | — | — |
| Reweighting-period total dollar weight: TDW_d = (NC_new/NC_old)·Σ CPW1·CRW1·DCRP1 + Σ CPW2·CRW2·DCRP2, with CPW2 the new CPW on the roll-in contract | S2 | "Total Dollar Weight Calculation During Any Reweighting Period", PDF p.7 (printed p.6) |
| DERIVED, for §4.4 stacking: contracts held per $ of GSCI-tracking notional ∝ CPW_c/(NC·I·size_c), so the January flow per unit AUM is ∝ CPW_new/NC_new − CPW_old/NC_old, moved 20% per day on BD5–BD9. This also applies to commodities that do not change contract in January (then CPW1 and CPW2 sit on the same expiry) | — | from S2's formula |
| FPI futures series (CME S&P GSCI futures) update NCs "annually on the 12th business day in January" | S1 | "S&P GSCI FPI Series Calculation", PDF p.15 (printed p.14). A different index; do not confuse with the GSCI roll |

### 2.3 Designated contract schedule (contract held at each month's start)

Source: S1 Appendix A Table 1, PDF p.22 (printed p.21), "starting with January 2026". The same letters appear for every commodity in **S4 (2016)** and **S5 (2018)**, so the schedule has not changed across 2016–2026. A letter change between month m and m+1 means that commodity rolls in month m (on BD5–9).

| fac. | commodity | RIC | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | rolls/yr (DERIVED) | roll months |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CBT | Chicago Wheat | W | H | H | K | K | N | N | U | U | Z | Z | Z | H | 5 | Feb Apr Jun Aug Nov |
| KBT | Kansas Wheat | KW | H | H | K | K | N | N | U | U | Z | Z | Z | H | 5 | Feb Apr Jun Aug Nov |
| CBT | Corn | C | H | H | K | K | N | N | U | U | Z | Z | Z | H | 5 | Feb Apr Jun Aug Nov |
| CBT | Soybeans | S | H | H | K | K | N | N | X | X | X | X | F | F | 5 | Feb Apr Jun Oct Dec |
| ICE-US | Coffee | KC | H | H | K | K | N | N | U | U | Z | Z | Z | H | 5 | Feb Apr Jun Aug Nov |
| ICE-US | Sugar | SB | H | H | K | K | N | N | V | V | V | H | H | H | 4 | Feb Apr Jun Sep |
| ICE-US | Cocoa | CC | H | H | K | K | N | N | U | U | Z | Z | Z | H | 5 | Feb Apr Jun Aug Nov |
| ICE-US | Cotton | CT | H | H | K | K | N | N | Z | Z | Z | Z | Z | H | 4 | Feb Apr Jun Nov |
| CME | Lean Hogs | LH | G | J | J | M | M | N | Q | V | V | Z | Z | G | 7 | Jan Mar May Jun Jul Sep Nov |
| CME | Live Cattle | LC | G | J | J | M | M | Q | Q | V | V | Z | Z | G | 6 | Jan Mar May Jul Sep Nov |
| CME | Feeder Cattle | FC | H | H | J | K | Q | Q | Q | U | V | X | F | F | 8 | Feb Mar Apr Jul Aug Sep Oct Dec |
| NYM / ICE | WTI Crude Oil | CL | G | H | J | K | M | N | Q | U | V | X | Z | F | 12 | every month |
| NYM | Heating Oil | HO | G | H | J | K | M | N | Q | U | V | X | Z | F | 12 | every month |
| NYM | RBOB Gasoline | RB | G | H | J | K | M | N | Q | U | V | X | Z | F | 12 | every month |
| ICE-UK | Brent Crude Oil | LCO | H | J | K | M | N | Q | U | V | X | Z | F | G | 12 | every month |
| ICE-UK | Gasoil | LGO | G | H | J | K | M | N | Q | U | V | X | Z | F | 12 | every month |
| NYM / ICE | Natural Gas | NG | G | H | J | K | M | N | Q | U | V | X | Z | F | 12 | every month |
| LME | Aluminum / Copper / Nickel / Lead / Zinc | MAL MCU MNI MPB MZN | G | H | J | K | M | N | Q | U | V | X | Z | F | 12 | every month |
| CMX | Gold | GC | G | J | J | M | M | Q | Q | Z | Z | Z | Z | G | 5 | Jan Mar May Jul Nov |
| CMX | Silver | SI | H | H | K | K | N | N | U | U | Z | Z | Z | H | 5 | Feb Apr Jun Aug Nov |

Components: **24 contracts** in all years 2016–2026 (every announcement says "no new contracts added to or removed"). Contract sizes (S1 Table 4, printed p.23): W/KW/C/S 5,000 bu; KC 37,500 lb; SB 112,000 lb; CC 10 MT; CT 50,000 lb; LH/LC 40,000 lb; FC 50,000 lb; CL/LCO 1,000 bbl; HO/RB 42,000 gal; LGO 100 MT; NG 10,000 MMBtu; MAL/MCU/MPB/MZN 25 MT; MNI 6 MT; GC 100 oz; SI 5,000 oz.

**Relevance to the spec's traded list (§2), DERIVED:** GSCI holds CL, NG, HO, RB, GC, SI, ZC (C), ZS (S), ZW (W), KE (KW), LE (LC) and HE (LH). It holds **no soybean oil (ZL), no soybean meal (ZM) and no COMEX copper (HG)**; GSCI copper is LME. So κ_G adds nothing to ZL, ZM or HG. In January, only CL, HO, RB, NG, LH, LC, GC and the LME/ICE-UK legs change contract. For W, KW, C, S, SI and the softs, the January reweight is a quantity change within the same expiry. Spec §5 counts about 12 calibration events a year per contract. For GSCI that holds only for energy and LME; the grains, softs, precious metals and livestock roll 4–8 times a year (table above).

### 2.4 Per-year Contract Production Weights, 2015–2026

CPWs are the index's fixed quantities (units per the WPQ conversion; see S1 Table 4). Sources by year:

- 2015 and 2016: S4 Table 1.
- 2017: S5 Table 1, "2017 CPW" (mirror).
- 2018: A2019 Table 3, equal to S5's "2018 CPW".
- 2019: A2019 and A2020.
- 2020: A2020 and A2021.
- 2021: A2021 and A2022.
- 2022: A2022 and A2023.
- 2023: A2023 and A2024 (and P2023's pro-forma).
- 2024: A2024 and A2025.
- 2025: A2025, A2026b and S1.
- 2026: A2026b and S1.

Every year that appears in two sources was checked row-by-row, and the two sources agree. **2027: not published** (due in November 2026).

| RIC | 2015 | 2016 | 2017 (S5 mirror) | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| W | 19929.26 | 20181.8 | 19593.74 | 18577.02 | 18541.59 | 18073.64 | 18633.54 | 19458.43 | 19263.74 | 19982.69 | 18940.32 | 18572.64 |
| KW | 4559.198 | 4731.456 | 5539.8 | 6791.687 | 7560.385 | 8461.355 | 8576.191 | 7915.366 | 8365.251 | 7751.352 | 8978.328 | 9661.873 |
| C | 32907.26 | 33563.3 | 35028.78 | 36718.35 | 37987.17 | 40020.53 | 42509.52 | 43170.92 | 43970.54 | 44787.06 | 45400.45 | 45442.70 |
| S | 8828.723 | 8986.094 | 9317.775 | 9939.278 | 10359.80 | 10902.82 | 11728.36 | 12270.07 | 12491.57 | 12724.26 | 12999.81 | 12960.77 |
| KC | 18179.15 | 18477.47 | 18863.52 | 19130.13 | 19303.73 | 19713.30 | 19857.99 | 20672.35 | 21127.24 | 22077.66 | 22909.76 | 23676.96 |
| SB | 347147 | 350467.6 | 356948.3 | 371030.6 | 381821.3 | 382988.4 | 383784.3 | 390154.8 | 391575.0 | 393391.2 | 397190.2 | 390626.6 |
| CC | 4.277231 | 4.49828 | 4.482378 | 4.499853 | 4.515547 | 4.651853 | 4.808290 | 5.013083 | 5.170340 | 5.303011 | 5.530011 | 5.599180 |
| CT | 55144.32 | 55730.3 | 56919.26 | 58443.26 | 56367.84 | 54366.53 | 54372.00 | 54201.50 | 54332.83 | 55831.68 | 55873.44 | 55309.73 |
| LH | 84970.17 | 87671.93 | 89422.62 | 89508.52 | 90398.53 | 91607.36 | 92812.84 | 94540.48 | 96620.79 | 111483.7 | 130487.7 | 156066.1 |
| LC | 92895.69 | 92186.84 | 94811.31 | 95985.02 | 97906.06 | 104808.8 | 109554.8 | 110644.1 | 110633.0 | 110944.0 | 114369.8 | 109278.2 |
| FC | 16537 | 21383.2 | 22425.74 | 24819.72 | 27486.73 | 27994.45 | 26933.66 | 29541.00 | 31753.94 | 35136.87 | 38776.70 | 39937.41 |
| CL | 10354.9 | 11568.56 | 12637.76 | 13241.68 | 13354.41 | 13539.79 | 13284.94 | 12392.85 | 12079.15 | 11252.59 | 11300.89 | 11300.20 |
| HO | 82958.12 | 78754.85 | 71069.42 | 64895.68 | 69816.19 | 67232.46 | 75118.71 | 70902.91 | 75458.02 | 74629.31 | 70482.35 | 70531.64 |
| RB | 86115.54 | 84209.46 | 78841 | 76651.74 | 74548.34 | 81545.36 | 76060.08 | 85545.41 | 82553.26 | 78382.22 | 72252.20 | 68570.98 |
| LCO | 9618.998 | 9256.426 | 8679.141 | 8574.135 | 8616.139 | 8684.505 | 8939.108 | 10024.82 | 10693.69 | 11345.07 | 11026.17 | 11087.07 |
| LGO | 341.2737 | 294.9689 | 286.6551 | 263.1475 | 289.0299 | 304.6870 | 332.5306 | 342.1020 | 319.4099 | 311.2954 | 327.9326 | 335.8560 |
| NG | 31092.93 | 31615.91 | 32577.49 | 33432.15 | 34674.30 | 35495.32 | 36243.22 | 37653.94 | 39421.14 | 42118.17 | 43851.52 | 45901.50 |
| MAL | 45.816 | 47.09 | 48.692 | 52.096 | 58.178 | 61.248 | 63.580 | 65.892 | 67.890 | 69.000 | 70.180 | 71.532 |
| MCU | 18.66 | 19.1 | 19.68 | 20.44 | 21.30 | 22.0732 | 22.7648 | 23.580 | 23.840 | 24.280 | 24.500 | 24.8744 |
| MNI | 1.442 ‡ | 1.516 ‡ | 1.658 | 1.784 | 1.870 | 1.944 | 1.996 | 2.016 | 2.0938 | 2.1628 | 2.2812 | 2.572 |
| MPB | 9.17 ‡ | 9.484 ‡ | 9.894 | 10.322 | 10.48 | 10.549 | 10.8496 | 11.02 | 11.22 | 11.64 | 11.84 | 11.96 |
| MZN | 12.08 | 12.38 | 12.58 | 12.86 | 13.22 | 13.34 | 13.60 | 13.44 | 13.52 | 13.58 | 13.54 | 13.34 |
| GC | 79.41235 | 81.79151 | 85.00658 | 89.70059 | 93.04427 | 95.93784 | 99.92453 | 102.3680 | 103.7183 | 103.2039 | 102.5609 | 102.2394 |
| SI | 716.9617 | 752.9706 | 787.0504 | 794.1235 | 825.6313 | 842.9927 | 855.2100 | 887.3607 | 879.0015 | 841.7066 | 818.5581 | 823.0592 |

‡ **S4 labels these two rows the other way round.** It prints "Lead MPB 1.442 / 1.516, ACRP 13711.2083" and "Nickel MNI 9.17 / 9.484, ACRP 1885.9583", and its WPA table swaps the two the same way. Here they are assigned by the ACRP (a 13.7k $/t price is nickel's) and by continuity with 2017 (MNI 1.658, MPB 9.894). The assignment is DERIVED, not printed.

### 2.5 Per-year reference percentage dollar weights (RPDW) as announced

The RPDW is S&P's "target weight". The RPDW for year y uses the ACRP of that year's annual calculation period (Sep y−2 to Aug y−1), so it is priced about 4–16 months before the January roll. DERIVED check: S1's 2026 RPDW column reproduces to 2 dp on all 24 rows as CPW_2026 × ACRP_2025 / Σ, once the grain, soft and livestock ACRPs are read in **US cents**. S1's "2025 RPDW" column does not reproduce from 2025 ACRP (max error 2.44 pp). It is the value "as reported in November 2024", per A2026b's footnote 2 (see §5).

| RIC | 2016 (S4) | 2018 (A2019) | 2019 (A2019) | 2020 (A2021) | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|
| W | 3.53 | 3.029 | 2.769 | 2.851221 | 3.736564 | 3.639760 | 3.306645 | 3.174613 | 2.501533 | 2.375319 |
| KW | 0.88 | 1.121 | 1.147 | 1.254001 | 1.483037 | 1.398139 | 1.503575 | 1.449073 | 1.258336 | 1.241523 |
| C | 4.23 | 4.978 | 4.361 | 4.903934 | 5.749474 | 6.541656 | 5.657621 | 6.000747 | 4.558413 | 4.671894 |
| S | 2.95 | 3.662 | 3.143 | 3.105988 | 3.965832 | 4.643469 | 3.604751 | 3.966024 | 3.506659 | 3.102528 |
| KC | 0.94 | 1.012 | 0.722 | 0.649999 | 0.835443 | 0.832721 | 0.934687 | 0.854073 | 1.035835 | 1.849040 |
| SB | 1.59 | 2.487 | 1.543 | 1.520088 | 1.801799 | 1.812634 | 1.450679 | 1.888286 | 1.987869 | 1.715561 |
| CC | 0.45 | 0.365 | 0.318 | 0.341941 | 0.450256 | 0.355547 | 0.254636 | 0.334909 | 0.819801 | 1.178418 |
| CT | 1.19 | 1.593 | 1.406 | 1.260390 | 1.271920 | 1.256305 | 1.266387 | 1.015329 | 1.026018 | 0.877353 |
| LH | 2.30 | 2.216 | 1.907 | 2.053462 | 2.133796 | 2.356771 | 1.826483 | 2.104899 | 2.473356 | 3.310959 |
| LC | 4.79 | 4.062 | 3.479 | 3.896490 | 4.460746 | 3.759203 | 2.980578 | 4.001349 | 4.672884 | 5.202291 |
| FC | 1.55 | 1.252 | 1.268 | 1.301341 | 1.395279 | 1.246002 | 1.049662 | 1.623837 | 2.156991 | 2.677597 |
| CL | 23.04 | 24.70 | 26.42 | 25.30759 | 21.78450 | 20.34080 | 21.82859 | 19.30865 | 20.25712 | 17.78920 |
| HO | 5.21 | 3.876 | 4.449 | 4.272602 | 4.084293 | 3.501924 | 4.623547 | 4.812206 | 4.223675 | 3.686760 |
| RB | 5.31 | 4.584 | 4.484 | 4.531476 | 3.702687 | 4.335321 | 4.595460 | 4.385415 | 3.901648 | 3.290147 |
| LCO | 20.43 | 16.89 | 18.61 | 18.40825 | 16.10039 | 17.18794 | 19.93998 | 20.72882 | 20.72664 | 18.22456 |
| LGO | 5.82 | 4.634 | 5.556 | 5.950752 | 5.454422 | 4.780995 | 5.760029 | 5.729368 | 5.908821 | 5.220289 |
| NG | 3.24 | 3.898 | 3.110 | 3.239388 | 2.802775 | 3.330280 | 4.717792 | 3.465948 | 2.393480 | 3.571871 |
| MAL | 2.88 | 3.628 | 3.887 | 3.690645 | 4.017302 | 4.183039 | 3.803466 | 3.499207 | 3.762849 | 4.278730 |
| MCU | 3.85 | 4.428 | 4.446 | 4.356173 | 4.965467 | 5.798651 | 4.348250 | 4.486681 | 4.954048 | 5.474302 |
| MNI | 0.70 ‡ | 0.685 | 0.764 | 0.802422 | 1.031943 | 0.997634 | 0.983167 | 1.129734 | 0.902610 | 0.932302 |
| MPB | 0.60 ‡ | 0.867 | 0.782 | 0.677841 | 0.769226 | 0.656632 | 0.490274 | 0.539522 | 0.570813 | 0.556615 |
| MZN | 0.88 | 1.304 | 1.282 | 1.122147 | 1.129564 | 1.076274 | 0.951244 | 0.827314 | 0.815317 | 0.885345 |
| GC | 3.24 | 4.209 | 3.725 | 4.082334 | 6.271471 | 5.325982 | 3.735652 | 4.251695 | 5.104469 | 7.242292 |
| SI | 0.41 | 0.520 | 0.420 | 0.419519 | 0.601817 | 0.642327 | 0.386843 | 0.422301 | 0.480814 | 0.645104 |

- The 2021–2026 columns use the most precise printing: the "new-year" column of each year's own announcement, which equals the "prior-year" column of the next announcement.
- 2017 as announced: NOT FOUND (§6).
- 2025 and 2026 appear in both A2026b and S1 at 2 dp. The 2 dp column sums are 100.00 (2025) and 100.01 (2026).

### 2.6 Assets tracking the GSCI

- **No S&P-published estimate of GSCI-tracking AUM was found.** SV25 lumps GSCI into "Multi-Asset & Alternatives" (footnote 7).
- What S&P does publish is the **Investment Support Level (ISL)**. It is the "targeted amount of investment … based on the estimated aggregate outstanding level of investment in S&P GSCI-related investments" (S3 glossary). S3 adds that it "generally will not reflect the actual levels of such investment". P2023 p.9 and P2026 p.10 both say: "Not an accurate estimate of commodity investment space."
- ISL by index year (US$ bn), P2023 p.10: 2004 30; 2005 40; 2006 70; 2007 110; 2008 150; 2009 200; 2010 170; 2011 190; 2012 230; 2013 230; 2014 240; 2015 220; **2016 180; 2017 160; 2018 200; 2019 250; 2020 230; 2021 210; 2022 230; 2023 310**. P2026 p.11 gives **2025 310** and **2026 320**. **2024: NOT FOUND.**
- Use: at most an upper-bound scale anchor. The spec fits κ_G on flow, so an AUM number is not needed for §4.4. Do not enter the ISL as `AUM_G`.

---

## 3. R-Q9 — CFTC Supplemental (Commodity Index Traders, CIT)

| fact | source | location / quote |
|---|---|---|
| Covers **13** agricultural contracts, futures-and-options combined | C4 ("Types of Reports"), C10 (dataset 4zgm-a668 description) | "includes 13 select agricultural commodity contracts for combined futures and options" |
| The 13 markets as of the 2026-09-22 report, with CFTC codes: **WHEAT-SRW CBOT 001602; WHEAT-HRW CBOT 001612; CORN CBOT 002602; SOYBEANS CBOT 005602; SOYBEAN OIL CBOT 007601; SOYBEAN MEAL CBOT 026603; COTTON NO. 2 ICE US 033661; LEAN HOGS CME 054642; LIVE CATTLE CME 057642; FEEDER CATTLE CME 061641; COCOA ICE US 073732; SUGAR NO. 11 ICE US 080732; COFFEE C ICE US 083731** | C5 | report header: "Supplemental Report - Option and Futures Combined Positions as of September 22, 2026" |
| Original list, **12 markets**: corn, soybeans, wheat and soybean oil on CBOT; wheat on KCBOT; cotton no. 2, coffee C, sugar no. 11 and cocoa on NYBOT; live cattle, lean hogs and feeder cattle on CME | C6 | §III (p.~11 of the notice): "the following 12 agricultural commodity futures and options" |
| First report **2007-01-05**, positions as of 2007-01-02, with weekly 2006 data published alongside; two-year pilot | C6 | §I items 2–4 and §III |
| **Change:** CBT soybean meal was added **2013-04-05** (12 → 13) | C7 | "CBT Soybean Meal has been added to the Commitment of Traders Index Supplement" |
| Reclassification: in July 2018 staff moved some traders out of, and others into, the index category. The positions were small but noticeable in aggregate, and only the CIT report was affected | C7 | entry dated 2018-07-25 |
| Index Traders are drawn from both the noncommercial and commercial categories (the commercial side includes swap dealers hedging OTC index exposure). Some traders are misassigned both ways | C3 | "Supplemental Report" section |
| History: compressed files from **January 2006**; "to 2006 for the Supplemental report" | C1; C2 | C1 CIT section; C2 paragraph 6 |
| Release: **Friday 3:30 p.m. Eastern**, data as of the previous **Tuesday**. Federal holidays can delay release by a day or two | C2; C8 | C8: "released at 3:30 p.m. Eastern time"; the 2026 schedule marks delayed dates, namely **Mon 2026-01-05**, Mon 2026-06-22, Mon 2026-07-06, Mon 2026-11-16, Mon 2026-11-30 and Mon 2026-12-28 |
| HEAD check: `deacit.txt` and the 2025 history zips carry Last-Modified Fri 2026-09-25 19:27 GMT (15:27 EDT) | curl HEAD | consistent with 15:30 ET |
| **URL patterns (confirmed by HEAD, not downloaded):** yearly history `https://www.cftc.gov/files/dea/history/dea_cit_txt_{YYYY}.zip` (text) and `…/dea_cit_xls_{YYYY}.zip` (Excel), 2006…2026; bundle `…/dea_cit_txt_2006_2016.zip` (916,800 B) and `…/dea_cit_xls_2006_2016.zip` (1,239,980 B); current week `https://www.cftc.gov/dea/newcot/deacit.txt`; viewable `https://www.cftc.gov/dea/options/deaviewcit.htm`; API `https://publicreporting.cftc.gov/resource/4zgm-a668.json` (dataset "Supplemental - CIT") | C1, C4, C10 | `dea_cit_txt_2025.zip` returned 200, application/zip, 92,893 B |
| API columns (metadata only): `cit_positions_long_all`, `cit_positions_short_all`, `change_cit_long_all`, `change_cit_short_all`, `pct_oi_cit_long_all`, `traders_cit_long_all`, and the rest; the non-index categories carry a `_nocit` suffix. Variable dictionary: https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalViewable/cotvariablescitsupplement.html | C10 | 60 columns |

**Relevance (DERIVED):**
- Of the spec's traded list, the CIT covers ZW (001602), KE (001612), ZC, ZS, ZL, ZM, LE and HE. It does not cover CL, NG, HO, RB, GC, SI or HG. §5A.2 is therefore ag and livestock only, which matches the spec.
- ZM enters the CIT only from 2013-04-05. §5A.2 fits on ZM must start there.

---

## 4. R-Q10 — report variants

| report | futures-only | futures-and-options combined | source |
|---|---|---|---|
| **CIT Supplemental** | **does not exist** | **the only variant** | C2 ("published for Futures-and-Options-Combined"), C3 ("Based on … futures-and-options combined"), C4, C5 header |
| **Disaggregated** (swap dealer series) | exists: API `72hh-3qpy`; history `fut_disagg_txt_{YYYY}.zip` / `fut_disagg_xls_{YYYY}.zip`, bundle `fut_disagg_txt_hist_2006_2016.zip`; current `https://www.cftc.gov/dea/newcot/f_disagg.txt` | exists: API `kh3c-gbw2`; history `com_disagg_txt_{YYYY}.zip` / `com_disagg_xls_{YYYY}.zip`, bundle `com_disagg_txt_hist_2006_2016.zip`; current `https://www.cftc.gov/dea/newcot/c_disagg.txt` | C1, C4, C9, C10 (HEAD 200 on `fut_disagg_txt_2025.zip` and `com_disagg_txt_2025.zip`) |
| Legacy | from 1986 (`deacot{YYYY}.zip`) | from March 1995 (`deahistfo{YYYY}.zip`) | C1, C2 |

- Swap dealer definition: an entity that "deals primarily in swaps for a commodity" and uses futures to hedge those swaps (C9). API columns: `swap_positions_long_all`, `swap__positions_short_all` (double underscore, as the provider spells it), `swap__positions_spread_all`, and the change, percent and trader-count columns (C10).
- Disaggregated publication began **2009-09-04**, all physical markets from 2009-12-04 (C9). History back to **2006-06-13** was released on 2009-10-20. It is **backcast using recent classifications**, so its accuracy "diminishes … further back in time" (C9, "Historical Data").
- DERIVED consequence for R-Q10: the CIT has only a combined form. A like-for-like §5A.3 cross-check (R-D12, "fits agree on the shared overlap") therefore argues for the **combined** Disaggregated swap-dealer series. That is the variant this repository deliberately does *not* hold (§7). Pre-register the choice; this document does not make it.
- Lead outside the window: the CFTC **Index Investment Data** report gave index notional and futures-equivalents per US market, including energy and metals, above $0.5 bn. It was quarterly from September 2009, monthly from July 2010, and **discontinued with October 2015 data** (final release 2015-11-25) (C11). It does not reach 2016+.

---

## 5. Contradictions and cautions found

1. **GSCI calendar:** S1 says "based on the CME Group holiday schedule", while S3 defines the business day by the NYSE Euronext schedule. The two can differ on days one exchange closes and the other does not. A candidate is 2025-01-09, the day after BD5 = 2025-01-08 (A2025), when the NYSE is understood to have closed for a national day of mourning. **That closure is not sourced in this document; verify it.** How S&P counted the day is NOT FOUND.
2. **Exchange attribution inside S&P's own documents:** A2026a/b say gold is "traded on ICE US" and A2021 says "traded on CME Globex", but S1 Table 1 lists gold as **CMX**. CL and NG are listed "NYM / ICE".
3. **A2026a (2025-11-06) is wrong** in its 2025 RPDW column for W, KW, C, S, KC, SB, CC and CT: it repeats the livestock values 4.672884 / 2.156991 / 2.473356. A2026b (2025-11-12) corrects them. Use A2026b.
4. **S1 footnote (2) vs its data:** the "2025 RPDW" column says it uses the 2025 ACRP, but it is the November-2024 value (A2026b fn. 2). DERIVED: it does not reproduce from 2025 CPW × 2025 ACRP (max error 2.44 pp), while the 2026 column reproduces exactly.
5. **ACRP units:** S1's Table 1 heads the column "ACRP ($)", but grain, soft and livestock values are **US cents** (corn 439.90, wheat 547.23). S5 and P2023 print dollars (S5: corn 3.6148; P2023: wheat 8.6867).
6. **S4 (2016) swaps the Lead/Nickel labels** in Tables 1 and 3 (§2.4 ‡).
7. **Announcement date vs S3's "first week of November":** the actual dates run Nov 1–12 (§2.2).
8. **Spec §5 "about 12 calibration events a year per contract"** holds for GSCI energy only. GSCI grains, softs and precious metals roll 4–5 times a year, livestock 6–8 (§2.3).
9. **Spec §4.3 CIM determination date:** GSCI has no multiplier determination. Its only price-dependent reset is the NC, on the reference day before the January roll (S2; S5 says the last business day of the prior period) (§2.2).
10. **Repo tracker vs disk:** `docs/internal/DEPOSIT_INFRASTRUCTURE_TRACKER.md` line 158 says "CIT supplement and COT ✓ raw". **No CIT data is on disk** (§7), and no script in `scripts/` fetches it.

---

## 6. NOT FOUND

| item | where I looked |
|---|---|
| **2027 GSCI CPWs** | not yet published (due in November 2026); S1 has only 2025/2026 |
| 2016 and 2017 **announcement dates**; the Nov-2016 (2017 weights) and Nov-2017 (2018 weights) announcement PDFs; the 2017 RPDW as announced | spglobal.com announcement paths (only 2019–2026 located), web search, spice-indices.com (only 2019 found); etfstrategy.com's 2018 article is secondary and its page did not return the text on fetch. S5's "2017 PDW" column uses 2017 ACRP and is not the as-announced value |
| 2016–2018 **effective (first roll) dates** stated by S&P | S4 and S5 give none; A2019+ give theirs |
| An S&P estimate of **assets tracking the GSCI** (any year) | S1, S3, P2023, P2026, SV25 (GSCI not broken out). Only the ISL exists, and S&P disclaims it as an AUM estimate |
| **ISL for 2024** | P2023 (ends 2023), P2026 (gives 2025, 2026) |
| The **named business day** of the GSCI NC calculation in the current documents | S1, S2 (say only "reference day prior to the reconstitution period") |
| How S&P treated **2025-01-09** in the January 2025 roll (whether the NYSE closure applied is itself unverified here) | S1, S3; no S&P holiday calendar fetched |
| The date the CIT's KC wheat moved from "KCBOT" to "CBOT WHEAT-HRW" (same code 001612 today) | C6 (KCBOT in 2006), C5 (CBOT now), C7 (no entry found) |
| Any CIT market **removed** since 2007 | C7 shows only the 2013 addition; the current list (C5) is a superset of the 2006 list (C6) |
| **BCOM** roll days (6–10) | not checked, by instruction |

---

## 7. CFTC data already on disk (read from metadata; no price data read)

- `data/fixtures/cftc_cot_raw.csv.gz`, with `.meta.json` built 2026-09-20T10:52:29Z. Shape is tidy, one row per (report_date, symbol, family, category).
  - **Rows:** 274,473. **Span:** 1986-01-15 → 2026-09-15. **Symbols:** 34.
  - **Families:** legacy 133,398, disaggregated 84,515, tff 56,560.
  - **Columns:** `report_date, release_date_nominal, symbol, code, family, contract_name, open_interest, traders_total, category, long, short, spread`. Disaggregated categories are `producer_merchant, swap_dealer, managed_money, other_reportable, nonreportable`.
  - **Variant: futures-only only.** The Socrata datasets are 6dca-aqww, 72hh-3qpy and gpe5-46if. Per the meta, "Combined futures-and-options datasets exist and are deliberately NOT used". `docs/cftc_cot.md` explains why.
  - **Release convention:** Friday 15:30 ET; `release_date_nominal` is empty before 1993.
  - **Traded-list roots present:** CL, NG, HO, RB, GC, SI, HG, ZC, ZS, ZW (SRW 001602), ZL, ZM, LE, HE.
  - **Absent:** **KE / WHEAT-HRW 001612**, FC, and all ICE softs.
  - **CL starts only 2009-07-28** in both families (code 067411). The other roots have disaggregated rows from 2006-06-13; that is the CFTC's backcast history (§4).
- `data/raw/cftc/{legacy,disaggregated,tff}/` hold 34 JSON.gz files each (~21 MB total, gitignored), the raw cache of the same pulls.
- `docs/data-available.md` §"Positioning" describes `cftc_cot_raw` only. There is **no CIT/Supplemental fixture, raw cache or fetcher** (`scripts/` grep for supplemental / 4zgm / CIT: nothing).
