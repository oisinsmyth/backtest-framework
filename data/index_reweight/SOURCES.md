# BCOM index facts: sources (R-Q1, R-Q2)

Sourced for `docs/internal/User-Doc-Deposit/INDEX_REWEIGHT_FLOW_PREREG.md` (sections 3.1, 3.2; open questions
R-Q1, R-Q2). Every number in `weights/<year>.csv` and `methodology_facts.json` comes from a document listed here.
Nothing was filled from memory. Where a fact was not found, it is listed under NOT FOUND at the end.

**Access dates.** The session ran across midnight. Sources marked 2026-09-26 were fetched that day; the four
marked 2026-09-27 were fetched after midnight.

**How the tables were read.** The weight tables were not typed by hand. `parse_weights.py` (a session scratch
script, not kept) extracted every `ticker weight% weight%` triple from the fetched PDF or HTML text. The
writer then checked two things:

- **Second copies.** Where a year had a second copy (PDF and PR Newswire, or two PDFs), the two copies were
  compared and matched exactly. The one exception is noted under 2026.
- **The year-to-year chain.** Every year's printed prior-year column equals the previous year's target column,
  with zero mismatches across 2016→2026.

**Primary vs secondary.** "PRIMARY" means a Bloomberg Index Services document: a Bloomberg PDF, a Bloomberg
press page, or Bloomberg's own release distributed on PR Newswire (dateline and SOURCE: Bloomberg). A Wayback
Machine capture of a Bloomberg URL is still the Bloomberg document; the capture timestamp is given. No
secondary source was needed for any number recorded here.

**bloomberg.com is blocked for direct fetches.** The live bloomberg.com/company/press pages return HTTP 403
("Are you a robot?"), so they were not fetched directly. Their Wayback captures were used instead, and the
check was not bypassed.

---

## 1. Methodology documents (R-Q1)

| Key | Document | URL | Version / date | Accessed |
|---|---|---|---|---|
| SRC-M2026 | BCOM Methodology (current) | https://assets.bbhub.io/professional/sites/27/BCOM-Methodology-FEB-2026.pdf | FEB-2026 (target weightings as of January 2026), 100 pp. | 2026-09-26 |
| SRC-M2025 | BCOM Methodology | https://assets.bbhub.io/professional/sites/27/BCOM-Methodology-JAN-2025.pdf | JAN-2025, 99 pp. | 2026-09-26 |
| SRC-M2024 | BCOM Methodology (Wayback capture 20240612194804) | https://web.archive.org/web/20240612194804id_/https://assets.bbhub.io/professional/sites/10/BCOM-Methodology-FEB-2024_FINAL.pdf | FEB-2024, 102 pp. (live URL returns 403) | 2026-09-27 |
| SRC-M2023 | BCOM Methodology | https://assets.bbhub.io/professional/sites/10/BCOM-Methodology.pdf (byte-identical to https://data.bloomberglp.com/professional/sites/10/BCOM-Methodology.pdf) | undated file; content is the 2023 edition ("target weightings as of January 2023"), 105 pp. | 2026-09-26 |
| SRC-M2022 | BCOM Methodology | https://assets.bbhub.io/professional/sites/10/BCOM-Methodology-MAR-2022_FINAL.pdf | MAR-2022, 101 pp. | 2026-09-26 |
| SRC-M2021 | BCOM Methodology | https://assets.bbhub.io/professional/sites/27/BCOM-Methodology-Oct-2021_FINAL.pdf (text-identical tables also in the WisdomTree-hosted copy https://www.wisdomtree.eu/-/media/eu-media-files/other-documents/index/wt/index-methodology/bloomberg-commodity-total-return-index.pdf) | Oct-2021 (target weightings as of January 2021), 101 pp. | 2026-09-26 |
| SRC-M2020 | BCOM Methodology (Wayback capture 20201103204452) | https://web.archive.org/web/20201103204452id_/https://data.bloomberglp.com/professional/sites/10/BCOM-Methodology.pdf | 2020 edition ("target weightings as of January 2020"), 105 pp. | 2026-09-26 |
| SRC-M2018 | BCOM Methodology (Wayback capture 20220111214231) | https://web.archive.org/web/20220111214231id_/https://data.bloomberglp.com/indices/sites/2/2018/02/BCOM-Methodology-January-2018_FINAL-2.pdf | January 2018, 104 pp. | 2026-09-26 |
| SRC-M2017 | BCOM Methodology (Wayback capture 20220724065410) | https://web.archive.org/web/20220724065410id_/https://data.bloomberglp.com/indices/sites/2/2017/06/BCOM-Methodology-July-2017_FINAL.pdf | July 2017, 105 pp. | 2026-09-26 |
| SRC-M2016 | BCOM Methodology (Wayback capture 20220724065521) | https://web.archive.org/web/20220724065521id_/https://data.bloomberglp.com/indices/sites/2/2015/12/BCOM-Methodology-January-2016_FINAL.Updated.pdf | January 2016, 95 pp. | 2026-09-26 |

A 20201021 Wayback capture of the 2020 file was truncated (1,048,576 bytes; pypdf could not read it) and was not used.

### 1.1 Monthly roll: days and fractions

The methodology defines two different five-day windows, and they must not be conflated:

- **Index "Roll Period" = Business Days 6 through 10 of each month.** The index shifts from WAV1 (Lead Future)
  to WAV2 (Next Future) at 20% per Business Day. Sources: SRC-M2026 §3.1 p.31, and the Glossary p.39:
  "the sixth Business Day through and including the tenth Business Day".
- **Index formulas, SRC-M2026 §3.1 p.31–32.**
  - BD1: BCOM_S = BCOM_PS·WAV1_S/WAV2_PS.
  - BD2–5: WAV1 only.
  - BD6 weights 0.8 / 0.2; BD7 0.6 / 0.4; BD8 0.4 / 0.6; BD9 0.2 / 0.8.
  - BD10 onward: WAV2 only.
  - Appendix C, Table 13 (p.42) shows the same weights on a worked January 1997 example.
- **"Hedge Roll Period" = Business Days 5 through 9 of each month.** Sources: SRC-M2026 Glossary p.38, "beginning
  with the fifth Business Day through and including the ninth", and §3.3 p.34, "(defined herein as the fifth
  through the ninth Business Days of each month)".
  - Derived arithmetic, not an outside claim: the BD6 index return (close of BD5 to close of BD6) is earned 20% on
    WAV2. A replicating book therefore moves 20% at each close of BD5 through BD9. That is the Hedge Roll Period.
- **Day counting (Business Day).** A Business Day is "any day on which the sum of the CIPs for those Index
  Commodities that are open for trading is greater than 50%". Prior-year CIPs apply up to and including the CIM
  Determination Date. Source: SRC-M2026 Glossary p.36.
  - It is a CIP-weighted calendar, not the CME calendar.
  - The same definition is printed in SRC-M2016, M2017, M2018, M2020, M2021, M2022, M2023 and M2025.
- **Unchanged 2016–2026.** "sixth through tenth Business Days" (§3.1) and "fifth through the ninth Business Days"
  (§3.3) appear in every version: SRC-M2016, M2017, M2018, M2020, M2021, M2022, M2023, M2024, M2025 and M2026.
- **Repo cross-check.** The repo says NG rolls over "the closes of BD5–9". That matches the Hedge Roll Period, and
  `clip((k−5)/5,0,1)` on BD k matches the index Roll Period weights. Note that §2.8 itself holds the contract
  calendar (Table 9a); the roll days are defined in §3.1, §3.3 and the Glossary, not in §2.8.

### 1.2 January annual rebalance: days and phasing

- **Timing.** The reweight is executed inside the January Roll Period, on the same days as the January roll:
  index BD6–10, hedge BD5–9, 20% per day. The rule is in SRC-M2026 §2.7 p.27: "CIM_last_year continues to be used
  for the calculation of WAV1 until the end of the roll period falling in the month of January".
  - Footnote 19 adds that the new CIM "is then used to calculate the WAV2 value".
  - This sentence is present in SRC-M2016, M2017, M2018, M2020, M2021, M2022, M2023, M2024, M2025 and M2026.
- **Market disruption in January.** SRC-M2026 §3.3 p.34 says rolling or rebalancing "will occur in all cases over
  five Business Days on which no Market Disruption Event exists at a rate of 20% per day". There is no doubling
  up; Table 11 on p.35 gives a worked example. The same wording is in SRC-M2016 through SRC-M2026 as listed in
  `methodology_facts.json`.
- **Press-release wording.**
  - 2026: targets "will take effect during the January 2026 Roll Period" (SRC-PR2026).
  - 2024 and 2025: "effective during the 2024 [2025] January Roll Period".
  - 2023: "Transition toward the 2023 target weights will take place during the January 2023 index roll period".
- **Derived from Table 9a (§1.4 below).** For components whose January and February Lead Futures are the same
  month, the January Roll Period moves only the CIM, not the contract. That covers NG, CL, HO, RBOB, both wheats,
  corn, the soy complex, copper, silver and all LME metals. The components with a January contract roll are Brent
  (Mar→May), Live Cattle (Feb→Apr), Lean Hogs (Feb→Apr) and Gold (Feb→Apr).

### 1.3 CIM determination date

- **Rule.** SRC-M2026 §2.1 p.10: "On the fourth Business Day of the month of January (the 'CIM Determination
  Date')". The Glossary (p.37) adds "or as otherwise determined in accordance with Section 3.3".
- **Prices used.** The Settlement Price (in USD) of the Lead Future for each Designated Contract on that date,
  called FPD_S. SRC-M2026 §2.7 p.26.
- **Formula.** ICIM = CIP·1000/FPD_S. The Adjustment Factor is WAV1(CIM_last_year, FPD_S)/1000.
  CIM_new_year = ICIM·AF, rounded to 8 decimal places, and fixed for the year. SRC-M2026 §2.7 p.26–27.
  - The CIMs can be estimated before the date from the prices of the Designated Contracts that will be January's
    Lead Futures (p.27).
- **Disruption on the determination date.** SRC-M2026 §3.3 p.35: on a limit event, the day's settlement is used;
  if the exchange fails to publish a settlement, the first prior non-disrupted Business Day's settlement is used.
- **Dates printed in each version's Table 10** ("Price on January …") and Table 8 header:

| CIM year | Printed date | Source | Note |
|---|---|---|---|
| 2016 | January 6th 2016 | SRC-M2016 | FLAG: 3rd Mon–Fri day after Jan 1 by plain weekday count |
| 2017 | January 6th 2017 | SRC-M2017 | |
| 2018 | Table 8: January 5th 2018; Table 10: January 6th 2018 | SRC-M2018 | internal conflict; Jan 6 2018 was a Saturday |
| 2019 | NOT FOUND | — | no 2019 version located; SRC-M2020 Table 8 header reads "January 7th 2019" (stale label) |
| 2020 | January 7th 2020 | SRC-M2020 | |
| 2021 | January 7th 2021 | SRC-M2021 | |
| 2022 | Table 10: January 7th 2022; Table 8 header: January 7th 2021 | SRC-M2022 | FLAG: Jan 7 2022 is the 5th Mon–Fri day after Jan 1 |
| 2023 | January 6th 2023 | SRC-M2023 | |
| 2024 | January 5th 2024 | SRC-M2024 | |
| 2025 | January 7th 2025 | SRC-M2025 | |
| 2026 | January 7th 2026 | SRC-M2026 | |

Every version labels the WAV1 line "Close on 4th Business Day <year>". The two FLAG rows are not resolved by the
sources, because the Business Day definition is CIP-weighted. Verify them against settlement data before use.

The press releases confirm the rule for 2016 and 2017:

- 2016, SRC-PR2016: "The new multipliers will be calculated on the fourth business day of 2016".
- 2017, SRC-BB2017: "The new CIM will be calculated on the fourth business day of 2017".

### 1.4 Designated contract (Lead Future) schedule

SRC-M2026 §2.8, Table 9a, p.28–29 (Table 9 in earlier versions). The column is the calendar month; the value is
the Lead Future contract month. The Next Future is the next month's column; in December it is the January
column (Glossary p.38–39). The full table is in `methodology_facts.json` → `designated_contract_schedule.table`.

The table was parsed from each version's text. It is identical for all 25 BCOM rows in SRC-M2016, M2017, M2018,
M2020, M2021, M2022, M2023, M2024, M2025 and M2026. In the older versions Gas Oil, Cocoa and Lead appear in the
same table as non-index or single-commodity rows. So the calendar did not change between 2016 and 2026.

### 1.5 Holiday and market-disruption rules

- **Market Disruption Event.** SRC-M2026 §3.3 p.34 lists four cases:
  - (a) termination, suspension or material limitation of trading in a Lead or Next Future;
  - (b) a settlement at the maximum permitted price change;
  - (c) an exchange failing to publish a settlement;
  - (d) for an LME contract, a Business Day on which the LME is not open.
- **February–December.** A disruption during the Hedge Roll Period postpones that commodity's roll to the next
  non-disrupted Business Day. Other commodities are not affected. The period is extended only if the disruption
  hits the scheduled final day. SRC-M2026 §3.3 p.34.
- **January.** The rebalance always runs over five non-disrupted days (see 1.2).
- **Holidays.** There is no separate holiday rule. Holidays enter through the CIP-weighted Business Day definition
  (1.1) and through MDE case (d) for the LME.

### 1.6 Components and exchanges

SRC-M2026 §2.2, Table 2, p.13 lists the Designated Contracts and exchanges. The Glossary (p.37–39) says CBOT,
COMEX and NYMEX are "a division of the CME Group".

- **CME Group, 15 components in 2026** (Bloomberg tickers as printed in the announcements):
  - NYMEX: NG, CL, HO, XB (RBOB)
  - CBOT: C, S, SM, BO, W, KW (KC HRW wheat is printed as "CBOT")
  - COMEX: HG, GC, SI
  - CME: LC, LH
  - This matches the spec's list of 15 contracts.
- **ICE Futures Europe:** CO (Brent) and QS (Low Sulphur Gas Oil).
- **ICE Futures U.S.:** SB, KC, CC and CT.
- **LME:** LA, LX, LN and LL.
- **Copper.** BCOM uses COMEX copper prices but LME copper volume for the liquidity weight (SRC-M2026 p.13).
- **Exchange names by version.** SRC-M2016 prints "ICE" for Brent and "NYBOT" for the softs. SRC-M2018 prints
  "ICE Europe" and "ICE US". SRC-M2020 onward prints "ICE Futures Europe" and "ICE Futures U.S.". The CSVs use the
  2026 names throughout.
- **CME Globex roots.** The CSV column `ticker_root_if_known` holds the Bloomberg ticker printed in each
  announcement (NG, CL, C, S, SM, BO, W, KW, XB, LC, LH, …). CME Globex roots such as ZC, ZS, ZM, ZL, ZW, KE, RB,
  LE and HE do not appear in any fetched Bloomberg document. The mapping to them is left to the spec (§2) and is
  NOT sourced here.

**Component changes 2016–2027:**

| Target year | Count | Change | Source |
|---|---|---|---|
| 2016–2018 | 22 | none ("No new commodities will be added or removed") | SRC-PR2016, SRC-BB2017, SRC-BB2018 |
| 2019 | 23 | Low Sulphur Gas Oil (QS) added; its 2018 weight is printed as 0.0000000% | SRC-BB2019, SRC-TW2019 |
| 2020–2022 | 23 | 2021 and 2022 state no additions or deletions. The 2020 release does not say so, but lists the same 23 tickers. | SRC-PR2020, SRC-PR2021, SRC-PR2022 |
| 2023 | 24 | Lead (LL) added, "the 24th exchange-traded contract" | SRC-PR2023 |
| 2024–2025 | 24 | none; Lead retained | SRC-PR2024, SRC-PR2025 |
| 2026 | 25 | Cocoa (CC) reintroduced | SRC-PR2026 |

---

## 2. Annual target weights (R-Q2)

One row per target year. Every row's weights are in `weights/<year>.csv`. "Sum" is the sum of the published
per-component target weights.

Tracking AUM is written exactly as qualified in the release: `>100` means "over $100bn", and `~85` means
"approximately $85 billion". A parser must handle the `>` and `~` prefixes.

| Target year | Announced | Tracking AUM (USD bn) | Weight-table source (CSV `source_url`) | Other copies checked | Sum of targets |
|---|---|---|---|---|---|
| 2016 | 2015-10-29 | not stated | SRC-PR2016 | — (its 2016 column matches SRC-TW2017's prior column) | 100.000001 |
| 2017 | 2016-10-20 | not stated | SRC-TW2017 | SRC-BB2017 (text only; table is an image) | 100.000000 |
| 2018 | 2017-10-23 | not stated | SRC-TW2018 | SRC-BB2018 (text); SRC-TW2018web p.10 (2017 & 2018 "CIP" columns) | 99.999999 |
| 2019 | 2018-10-31 | ~85 | SRC-TW2019 | SRC-BB2019 (text) | 100.000001 |
| 2020 | 2019-10-30 | not stated | SRC-TW2020 | SRC-PR2020: identical | 99.999997 |
| 2021 | 2020-10-29 | not stated | SRC-TW2021 | SRC-PR2021: identical; SRC-TW2021sum p.6 | 100.000000 |
| 2022 | 2021-11-09 | >100 | SRC-PR2022 | its 2022 column = SRC-PR2023's prior column | 100.000000 |
| 2023 | 2022-10-27 | >110 | SRC-PR2023 | SRC-TW2023 (PDF dated November 30, 2022): identical | 100.000000 |
| 2024 | 2023-11-02 | 105.5 | SRC-TW2024 | SRC-PR2024: identical | 99.999998 |
| 2025 | 2024-10-31 | 102 | SRC-TW2025 | SRC-PR2025: identical | 99.999996 |
| 2026 | 2025-10-30 | 108.8 | SRC-TW2026 | SRC-PR2026 and SRC-BB2026: identical except Cocoa's prior (below) | 100.000001 |
| 2027 | not yet published | — | — | — | — |

**Spec §3.1 "verified example" for 2026: confirmed** from SRC-TW2026, SRC-PR2026 and SRC-BB2026:

- natural gas 7.7783690% → 7.1979390%
- WTI 6.9660050% → 6.6398440%
- energy group 29.4354750%
- AUM "(estimated AUM $108.8B)"

### 2.1 Per-year source list

| Key | URL | Doc date | Accessed | Quote (≤15 words) |
|---|---|---|---|---|
| SRC-PR2016 | https://www.prnewswire.com/news-releases/2016-target-weights-for-the-bloomberg-commodity-index-announced-300169215.html | Oct. 29, 2015 | 2026-09-26 | "There will be no new commodities added or removed" |
| SRC-TW2017 | https://data.bloomberglp.com/indices/sites/2/2016/10/BCOM-Target-Weights_2016-2017.pdf via https://web.archive.org/web/20230604181935id_/ (same URL) | undated; columns 2017 Weight / 2016 Weight | 2026-09-27 | — |
| SRC-BB2017 | https://web.archive.org/web/20171029043913id_/https://www.bloomberg.com/company/announcements/2017-target-weights-for-the-bloomberg-commodity-index-announced/ | October 20, 2016 | 2026-09-26 | "The new CIM will be calculated on the fourth business day of 2017" |
| SRC-TW2018 | https://data.bloomberglp.com/professional/sites/10/2018-BCOM-Target-Weights11.pdf | undated (PDF metadata created 2017-10-23 per WebFetch); columns 2018 / 2017 | 2026-09-26 | — |
| SRC-TW2018web | https://data.bloomberglp.com/professional/sites/10/2018-BCOM-Target-Weights-Website-FINAL.pdf | 2018 target weights deck | 2026-09-26 | "No constituent changes (22 commodities constituents / 20 commodities)" |
| SRC-BB2018 | https://web.archive.org/web/20171216094004id_/https://www.bloomberg.com/company/announcements/bcom-2018-target-weights-announced/ | October 23, 2017 | 2026-09-26 | "The 2018 target weights will be effective January 2018." |
| SRC-TW2019 | https://data.bloomberglp.com/professional/sites/10/BCOM-2019-Target-Weights.pdf | undated; columns 2019 / 2018 | 2026-09-26 | — |
| SRC-BB2019 | https://web.archive.org/web/20231120194021id_/https://www.bloomberg.com/company/press/bloomberg-commodity-index-bcom-2019-target-weights-announced/ | October 31, 2018 | 2026-09-26 | "tracked by approximately $85 billion in assets" |
| SRC-TW2020 | https://data.bloomberglp.com/professional/sites/10/BCOM-2020-Target-Weights.pdf | undated (metadata 2019-10-30 per WebFetch); columns 2020 / 2019 | 2026-09-26 | — |
| SRC-PR2020 | https://www.prnewswire.com/news-releases/bloomberg-commodity-index-2020-target-weights-announced-300948642.html | Oct. 30, 2019 | 2026-09-26 | "the 2020 target weights become effective January 2020" |
| SRC-TW2021 | https://assets.bbhub.io/professional/sites/10/BCOM-2021-Target-Weightsv5.pdf | undated; columns 2021 / 2020 | 2026-09-26 | — |
| SRC-TW2021sum | https://assets.bbhub.io/professional/sites/10/BCOM-2021-Target-Weight-Summaryv3.pdf | 29 October 2020 | 2026-09-26 | "No new constituent changes; 23 constituents" |
| SRC-PR2021 | https://www.prnewswire.com/news-releases/bloomberg-commodity-index-2021-target-weights-announced-301163435.html | Oct. 29, 2020 | 2026-09-26 | "There will be no commodity additions or deletions to BCOM in 2021." |
| SRC-PR2022 | https://www.prnewswire.com/news-releases/bloomberg-commodity-index-2022-target-weights-announced-301420460.html | Nov. 9, 2021 | 2026-09-26 | "Assets tracking the benchmark are now over $100bn" |
| SRC-PR2023 | https://www.prnewswire.com/news-releases/bloomberg-commodity-index-2023-target-weights-announced-301661824.html | Oct. 27, 2022 | 2026-09-26 | "with an estimated AUM of over $110B" |
| SRC-TW2023 | https://assets.bbhub.io/professional/sites/10/BCOM-2023-Target-Weights.pdf | November 30, 2022 | 2026-09-26 | — |
| SRC-PR2024 | https://www.prnewswire.com/news-releases/bloomberg-commodity-index-2024-target-weights-announced-301976390.html | Nov. 2, 2023 | 2026-09-26 | "(estimated AUM $105.5B)" |
| SRC-TW2024 | https://assets.bbhub.io/professional/sites/10/BCOM-2024-Target-Weights.pdf | November 2, 2023 | 2026-09-27 | — |
| SRC-PR2025 | https://www.prnewswire.com/news-releases/bloomberg-commodity-index-2025-target-weights-announced-302290528.html | Oct. 31, 2024 | 2026-09-26 | "(estimated AUM $102B)" |
| SRC-TW2025 | https://assets.bbhub.io/professional/sites/27/BCOM-2025-Target-Weights.pdf | October 31, 2024 | 2026-09-26 | — |
| SRC-PR2026 | https://www.prnewswire.com/news-releases/bloomberg-commodity-index-2026-target-weights-announced-302600263.html | Oct. 30, 2025 | 2026-09-26 | "(estimated AUM $108.8B)" |
| SRC-TW2026 | https://assets.bbhub.io/professional/sites/27/BCOM-2026-Target-Weights.pdf | October 30, 2025 | 2026-09-26 | — |
| SRC-BB2026 | https://web.archive.org/web/20251031071306id_/https://www.bloomberg.com/company/press/bloomberg-commodity-index-2026-target-weights-announced/ | October 30, 2025 | 2026-09-26 | "will take effect during the January 2026 Roll Period" |

Secondary pages were seen in search results only and were not used for any number. They were marketscreener.com
(2017) and the morningstar and yahoo reposts of 2026.

### 2.2 Conflicts between sources and versions

1. **The spec's execution days.** Spec §3.2 believes the January rebalance runs over the 6th–10th business day.
   That is the index Roll Period. The methodology's Hedge Roll Period, where a replicating book trades, is
   Business Days 5–9 (see 1.1).
2. **The 2023 announcement date.** The PR Newswire release is dated 2022-10-27. The bbhub 2023 PDF is dated
   November 30, 2022, with identical numbers. The CSV uses 2022-10-27.
3. **Cocoa's 2026 prior weight.** SRC-TW2026 prints "-" and SRC-PR2026 prints 0.0000000%. The CSV leaves it blank.
   Similar 0.0000000% priors are kept as printed: QS in 2019 (for 2018) and LL in 2023 (for 2022).
4. **CIM date labels inside methodology versions** disagree for 2018, 2019 and 2022, and two printed dates fail a
   plain weekday count (2016, 2022). See 1.3.
5. **The Calculation Period.** SRC-M2026 footnote 10 says it is "typically the third or fourth calendar quarter".
   The Glossary (p.37) says "the sixth month of the year preceding". This affects only how the weights are built,
   not the flow model.

---

## NOT FOUND

- **Tracking-AUM estimate for 2016, 2017, 2018, 2020 and 2021.** None is printed in any of those announcements.
  Looked in SRC-PR2016, SRC-BB2017, SRC-BB2018, SRC-PR2020, SRC-PR2021, SRC-TW2021sum, and the 2018 deck
  SRC-TW2018web.
- **2027 target weights.** Not published as of 2026-09-27. A web search for "Bloomberg Commodity Index 2027 Target
  Weights" (2026-09-27) returned only the 2026 release, and `BCOM-2027-Target-Weights.pdf` returns 403 at bbhub.
  Expected around late October 2026.
- **The 2019 CIM Determination Date as printed by Bloomberg.** No methodology version in force during 2019 was
  located. Looked at the Wayback CDX indexes of data.bloomberglp.com/indices/*,
  data.bloomberglp.com/professional/sites/10/* and assets.bbhub.io/professional/sites/*. The rule (4th Business
  Day) is unchanged in the 2018 and 2020 versions.
- **The live bloomberg.com press pages.** They return HTTP 403 with a bot check, so Wayback captures were used.
  The 2016 capture (20160228100117) returned navigation only, so SRC-PR2016 was used for 2016.
- **CME Globex root codes for the Bloomberg tickers.** They are not in any Bloomberg document fetched.
- **The 2017 table as HTML text.** In SRC-BB2017 the table is an image; SRC-TW2017 supplies the numbers.
