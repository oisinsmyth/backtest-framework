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

---

## ICE settlement windows

Sourced for `ice_settlement_windows.csv`: the daily settlement window (the trades that set the daily settlement
price) of the five ICE contracts in BCOM, 2014-12-01 to 2025-03-01. All sources below were accessed 2026-09-27.
Local copies are in `data/raw/index_reweight/ice/`: ice.com PDFs under their own names, Wayback captures as
`wb_<timestamp>_<name>`, and secondary web pages as `secondary_*.html`. Every PDF has a `.txt` extraction beside it
(pypdf). Nothing in the CSV was filled from memory.

**CSV conventions.** Times are local clock time in `tz`. Brent and Gasoil are in Europe/London; the three softs are
in America/New_York. `effective_from` and `effective_to` are inclusive trade dates. For permanent rows, `effective_to`
is the day before the next row starts, and blank means still in force. The exception is the Gasoil pair: those
two dates are the last and first dates evidenced, not a change date (see Gasoil below). A `temporary_dst` row
overrides the permanent row on those trade dates only. It gives the first and last Monday–Friday trade dates of
the exchange's stated period. The IFEU documents start that period on a Sunday, because Sunday evening opens
Monday's trading day.

**Primary vs secondary.** Every row is primary, meaning an ICE document or a Wayback capture of one, except the
2021 spring Coffee row (a ccstrade.com repost of the ICE notice). The secondary sources listed here were used only
where no ICE copy was found.

### A. Permanent windows

| Id | URL | Doc date | What it shows | Quote (≤15 words) |
|---|---|---|---|---|
| IFUS-2014 | https://www.ice.com/publicdocs/futures_us/exchange_notices/ExNot012714Hours.pdf | 2014-01-06 | From trade date Mon 2014-02-03: Sugar No. 11 12:53–12:55, Coffee C 13:23–13:25 (both were 13:28–13:30). Cotton is not in the list of changed windows. | "Also effective starting February 3, 2014, changes to the daily settlement window" |
| IFUS-KC2019 | https://www.ice.com/publicdocs/futures_us/exchange_notices/ICE_Futures_US_KC_ArbBlocks20181207.pdf | 2018-12-07 | Coffee C 12:23–12:25 from Mon 2019-01-07. It harmonises with IFEU Robusta. Trading hours are unchanged. | "will be from 12:23 to 12:25 pm New York time each day" |
| IFUS-SW | Wayback captures of https://www.theice.com/publicdocs/futures_us/Settlement_Window.pdf (20111212142402, 20120610055801, 20130122132558, 20140707063859, 20150619093750, 20160419081014, 20170126165226, 20181009064003, 20210517034610, 20220621203929, 20220706162212) and of https://www.ice.com/publicdocs/futures_us/Settlement_Window.pdf (20230923192023, 20231224031910, 20241231060946) | May 2011, May 2012, Oct 2012, May 2014, Apr 2015, Oct 2015, Jan 2017, Jul 2018, May 2021, Apr 2022, Jun 2022, Jan 2023, Nov 2023, Nov 2024 | Sugar 12:53–12:55 in every capture from May 2014. Coffee 13:23–13:25 from May 2014 to Jul 2018, then 12:23–12:25 from May 2021. Cotton 14:14–14:15 in every capture from May 2011. | "Coffee “C” ® Futures and Options: 13:23 to 13:25" (Jul 2018 capture) |
| IFUS-R27 | Wayback 20141223191358 and 20170420035300 of https://www.theice.com/publicdocs/rulebooks/futures_us/27_Electronic_Trading_Rules.pdf | Dec 2014, Apr 2017 | Rule 27.18(b): Coffee 1:23–1:25 PM, Cotton 2:14–2:15 PM, Sugar No. 11 12:53–12:55 PM. | "for Coffee “C” Futures and Options Contracts, 1:23 PM – 1:25 PM" |
| IFUS-R4 | Wayback 20200315115616, 20210922114733, 20220418215606 (theice.com) and 20240419062152, 20250130124142 (ice.com) of `/publicdocs/rulebooks/futures_us/4_Trading.pdf` | Mar 2020 – Jan 2025 | Rule 4.25(b): Coffee 12:23–12:25 PM, Cotton 2:14–2:15 PM, Sugar No. 11 12:53–12:55 PM in all five. | "for Coffee “C” Futures and Options Contracts, 12:23 PM – 12:25 PM" |
| IFEU-DSP-old | Wayback 20130513192315 and 20140707075617 of https://www.theice.com/publicdocs/futures/ICE_Futures_Designated_Settlement_Periods.pdf | undated (captured May 2013, Jul 2014) | Brent 19:28–19:30. LS Gasoil and legacy Gasoil 16:27–16:30. | "ICE Low Sulphur Gasoil and Options 16:27 – 16:30 10 Minutes" |
| IFEU-13/096 | https://www.ice.com/publicdocs/circulars/13096.pdf and https://www.ice.com/publicdocs/circulars/13096%20attach.pdf | 2013-06-18 | The same table (Brent 19:28–19:30; Gasoil 16:27–16:30). Its footnote says the times move with US daylight saving. | "Times may vary in line with US daylight savings times" |
| IFEU-GO-spec2013 | https://web.archive.org/web/20130530072216id_/https://www.theice.com/productguide/ProductSpec.shtml?specId=909 | captured 2013-05-30 | ICE Gasoil futures spec: a three-minute window. | "three minute settlement period from 16:27:00, London time" |
| IFEU-15/030 | https://web.archive.org/web/20150424121459id_/https://www.theice.com/publicdocs/circulars/15030_attach.pdf | 2015 (covers 08–27 Mar 2015) | DST-week table. LS Gasoil is still 16:27–16:30 GMT, and gasoil is not shifted in DST weeks. Brent is 18:28–18:30 GMT. | "ICE LS Gasoil Futures & Options 16:27-16:30 GMT" |
| IFEU-GO-page2015 | https://web.archive.org/web/20150908093209id_/https://www.theice.com/products/34361119/Low-Sulphur-Gasoil-Futures | captured 2015-09-08 | The first capture found with the two-minute LS Gasoil window. | "two minute settlement period from 16:28:00, London time" |
| IFEU-product-pages | Wayback 20140626054552 (`productguide/ProductSpec.shtml?specId=219`), 20150618154533 and 20180716201110 (`/products/219/Brent-Crude-Futures`), 20180716202103 (`/products/34361119/Low-Sulphur-Gasoil-Futures`) | 2014–2018 | Brent: two minutes from 19:28:00 London. LS Gasoil (2018): two minutes from 16:28:00. | "two minute settlement period from 19:28:00, London time" |
| IFEU-DSP | Wayback captures of https://www.theice.com/publicdocs/futures/Designated_Settlement_Periods_Volume_Thresholds.pdf (20160419015026, 20161003070619, 20161221095540, 20190918155830, 20210730060930, 20220120153931, 20220127210748, 20220629162806, 20220712180844, 20221007043718) and of the ice.com URL (20240526145949, 20250928100314) | 2016-04 to Dec 2025 | Brent 19:28–19:30 and LS Gasoil 16:28–16:30 in every capture. The legacy Gasoil line is gone by April 2016. | "ICE Brent Crude Futures and Options 19:28 – 19:30 5 Minutes" |
| IFEU-11/159 | https://www.ice.com/publicdocs/circulars/11159.pdf | 2011-12-20 | Context only (a 2011 holiday schedule). Brent was then 19:27–19:30, so it had moved to 19:28 by May 2013, before this window. | "ICE Gasoil Settlement period on Friday 30 December 2011 will be 12:27" |

### B. Temporary windows in US/UK daylight-saving mismatch weeks

**ICE Futures U.S. (Sugar No. 11, Coffee C, Cotton No. 2), one notice per mismatch period.** Sugar No. 11's window
never moves in NY time. Every notice found says so. Cotton appears in no DST notice, and its hours and window do not
change. Coffee C's window moved to 13:23–13:25 NY in these weeks only from spring 2019. That was the first mismatch
after its permanent window was aligned with London Robusta on 2019-01-07. Before 2019 every notice found says Coffee's
window is unchanged (only Cocoa's moved).

| Period (trade dates) | Coffee C window NY | Sugar / Cotton | Source (doc date) | Quote (≤15 words) |
|---|---|---|---|---|
| 2015-03-09 – 03-27 | unchanged (13:23–13:25) | unchanged | SECONDARY https://www.comunicaffe.com/ice-notice-changes-opening-times-sugar-no-11-coffee-c-cocoa-contracts-daily-settlement-window-cocoa-contracts/ (2015-02-06 repost) | "Daily Settlement Windows, and the Daily Close of Trading (other than for Cocoa" |
| 2015-10-26 – 10-30 | unchanged | unchanged | SECONDARY https://www.comunicaffe.com/ice-announces-temporary-change-to-opening-times-for-sugar-no-11-coffee-c-and-cocoa-futures-and-option-contracts-daily-settlement/ (2015-09-15) | "Daily Settlement Window for Sugar No. 11 and Coffee “C” contracts – remain unchanged" |
| 2016-03-14 – 03-24 | unchanged | unchanged | SECONDARY https://www.comunicaffe.com/ice-announces-temporary-change-to-opening-times-for-coffee-c-contract/ (2016-02-17); 25 Mar was Good Friday | same sentence |
| 2016 autumn | NOT FOUND | — | — | — |
| 2017-03-13 – 03-24 | unchanged | unchanged | https://www.ice.com/publicdocs/futures_us/exchange_notices/NewExNotDST_Start2017.pdf (2017-02-03) | same sentence |
| 2017 autumn | NOT FOUND | — | — | — |
| 2018-03-12 – 03-23 | unchanged | unchanged | SECONDARY https://www.comunicaffe.com/ice-notice-temporary-change-to-opening-times-for-coffee-c-contract/ (2018-02-13) | same sentence |
| 2018 autumn | NOT FOUND | — | — | — |
| 2019-03-11 – 03-29 | **13:23–13:25** | unchanged | https://www.ice.com/publicdocs/futures_us/exchange_notices/ICE_Futures_US_2019DST_Start_20190114.pdf (2019-01-14) | "Coffee “C” futures and options contracts will be from 1:23 to 1:25 pm" |
| 2019-10-28 – 11-01 | **UNRESOLVED** (see conflicts) | unchanged | SECONDARY https://community.optimusfutures.com/t/notice-temporary-change-to-opening-times-for-sugar-coffee-cocoa-effective-oct-28-nov-1/3054 (2019-10-25) | "Daily Settlement Window for Sugar No. 11 and Coffee “C” contracts – remain unchanged" |
| 2020-03-09 – 03-27 | **13:23–13:25** | unchanged | https://www.ice.com/publicdocs/futures_us/exchange_notices/ICE_Futures_US_DST_Start_20190113.pdf (dated 2020-01-13 despite the file name) | as 2019 |
| 2020-10-26 – 10-30 | **13:23–13:25** | unchanged | https://www.ice.com/publicdocs/futures_us/exchange_notices/ICE_Futures_US_DST_End_2020928.pdf (2020-09-28) | as 2019 |
| 2021-03-15 – 03-26 | **13:23–13:25** | unchanged | SECONDARY https://ccstrade.com/ice-sugar-coffee-cocoa-futures-temporary-trading-hour-changes/ (2021-03-01 repost; prints "2020", a typo) | "will be from 1:23 to 1:25 pm" |
| 2021-11-01 – 11-05 | **13:23–13:25** | unchanged | https://www.ice.com/publicdocs/futures_us/exchange_notices/ICE_Futures_US_DST_End2021.pdf (2021-09-20) | as 2019 |
| 2022-03-14 – 03-25 | **13:23–13:25** | unchanged | https://www.ice.com/publicdocs/futures_us/exchange_notices/ICE_Futures_US_DST_Start_20220124.pdf (2022-01-24) | as 2019 |
| 2022-10-31 – 11-04 | **13:23–13:25** | unchanged | https://www.ice.com/publicdocs/futures_us/exchange_notices/ICE_Futures_US_DST_End_20220929.pdf (2022-09-29) | as 2019 |
| 2023-03-13 – 03-24 | **13:23–13:25** | unchanged | https://www.ice.com/publicdocs/futures_us/exchange_notices/ICE_Futures_US_DST_Start20230106.pdf (2023-01-06) | as 2019 |
| 2023-10-30 – 11-03 | **13:23–13:25** | unchanged | https://www.ice.com/publicdocs/futures_us/exchange_notices/ICE_Futures_US_DST_End20230915.pdf (2023-09-15) | as 2019 |
| 2024-03-11 – 03-28 | **13:23–13:25** | unchanged | https://www.ice.com/publicdocs/futures_us/exchange_notices/ICE_Futures_US_DST_Start2024_20240104.pdf (2024-01-04); 29 Mar was Good Friday, closed | as 2019 |
| 2024-10-28 – 11-01 | **13:23–13:25** | unchanged | https://www.ice.com/publicdocs/futures_us/exchange_notices/ICE_Futures_US_DST_End20240912.pdf (2024-09-12) | as 2019 |

Pre-range context, also fetched: https://www.ice.com/publicdocs/futures_us/exchange_notices/exnot2014DSTstart.pdf
(2014-02-14), exnot2014DST2.pdf (2014-09-19) and 10092013exnotDST2.pdf (2013-10-09) all say Coffee and Sugar are
unchanged. The next period after the range, 2025-03-10 to 03-28, is in ICE_Futures_US_DST_Start20250108.pdf
(2025-01-08): Coffee 13:23–13:25. It is outside the range and not in the CSV.

**ICE Futures Europe (Brent, Gasoil).** In mismatch weeks Brent moves to 18:28–18:30 London, which is 14:28–14:30 New
York. Its window is therefore fixed in New York time all year. LS Gasoil stays at its normal London time in every
table found. Each year's January/February circular gives both periods. The detailed table sits in a separate
"Temporary Trading Times" PDF.

| Period (trade dates) | Brent window London | Source (doc date) | Quote (≤15 words) |
|---|---|---|---|
| 2015-03-09 – 03-27 | 18:28–18:30 (table) | circular 15/030, https://web.archive.org/web/20150424122516id_/https://www.theice.com/publicdocs/circulars/15030.pdf (2015-02-18), plus its attachment https://web.archive.org/web/20150424121459id_/https://www.theice.com/publicdocs/circulars/15030_attach.pdf | "Sunday 08 March 2015 to Friday 27 March 2015 (inclusive) and Sunday 25 October 2015" |
| 2015-10-26 – 10-30 | 18:28–18:30 (period only) | circular 15/213, https://web.archive.org/web/20260910084611id_/https://www.ice.com/publicdocs/circulars/15213.pdf (2015-10-09) | "for the period of Sunday 25 October 2015 to Friday 30 October 2015 (inclusive)" |
| 2016-03-14 – 03-25 | 18:28–18:30 (table) | https://web.archive.org/web/20160411192412id_/https://www.theice.com/publicdocs/futures/Futures_Europe_TemporaryTradingHours.pdf; periods also in circular 16/019 (2016-02-25; local copy `wb_circ_16019.pdf`, from the Wayback capture 20160419020413 or 20260910082045) | "(13 March 2016 – 25 March 2016, inclusive)" |
| 2016-10-31 – 11-04 | 18:28–18:30 (table) | https://web.archive.org/web/20161003082846id_/https://www.theice.com/publicdocs/futures/Futures_Europe_TemporaryTradingHours.pdf | "(30 October 2016 – 04 November 2016, inclusive)" |
| 2017-03-13 – 03-24 | 18:28–18:30 (table) | https://web.archive.org/web/20170217174924id_/https://www.theice.com/publicdocs/futures/Futures_Europe_TemporaryTradingHours.pdf (last update Feb 2017) | "(12 March 2017 – 24 March 2017, inclusive)" |
| 2017-10-30 – 11-03 | 18:28–18:30 (period only) | circular 17/017, https://web.archive.org/web/20220123021523id_/https://www.theice.com/publicdocs/circulars/17017.pdf (2017-02-24) | "Sunday 29 October 2017 to Friday 03 November 2017 (inclusive)" |
| 2018-03-12 – 03-23 | 18:28–18:30 (period only) | circular 18/017, https://web.archive.org/web/20220119083455id_/https://www.theice.com/publicdocs/circulars/18017.pdf | "Sunday 11 March 2018 to Friday 23 March 2018 (inclusive)" |
| 2018-10-29 – 11-02 | 18:28–18:30 (table) | https://web.archive.org/web/20220119083502id_/https://www.theice.com/publicdocs/futures/Futures_Europe_TemporaryTradingHours.pdf (last update Oct 2018) | "(28 October 2018 – 02 November 2018, inclusive)" |
| 2019 spring and autumn | NOT FOUND | — | — |
| 2020-03-09 – 03-27 | 18:28–18:30 (period only) | circular 20/020, https://web.archive.org/web/20200501181459id_/https://www.theice.com/publicdocs/circulars/20020%20%28002%29.pdf (2020-02-18) | "Sunday 08 March 2020 to Friday 27 March 2020 (inclusive)" |
| 2020-10-26 – 10-30 | 18:28–18:30 (table) | https://web.archive.org/web/20201011144938id_/https://www.theice.com/publicdocs/futures/Trading_Schedule_Temporary_Trading_Hours_for_DST.pdf (last update Jun 2020) | "(25 October 2020 – 30 October 2020, inclusive)" |
| 2021 spring | NOT FOUND | — | — |
| 2021-11-01 – 11-05 | 18:28–18:30 (table) | https://www.ice.com/publicdocs/TempTradingHours2021.pdf (last update Sept 2021; June 2021 version at Wayback 20210730060730) | "(31 October 2021 – 05 November 2021, inclusive)" |
| 2022-03-14 – 03-25 | 18:28–18:30 (table) | https://web.archive.org/web/20220629153537id_/https://www.theice.com/publicdocs/futures/TempTradingHours2022.pdf (last update Jan 2022) | "(13 March 2022 – 25 March 2022, inclusive)" |
| 2022-10-31 – 11-04 | 18:28–18:30 (table) | https://web.archive.org/web/20221102171917id_/https://www.theice.com/publicdocs/futures/TempTradingHours2022.pdf | "30 Oct 22 - 04 Nov 22 (Inclusive)" |
| 2023-03-13 – 03-24 | 18:28–18:30 (table) | https://web.archive.org/web/20230331065531id_/https://www.theice.com/publicdocs/futures/IFEU_Temporary_Trading_Hours_Mar2023.pdf; periods also in circular 23/037, https://web.archive.org/web/20240502110822id_/https://www.ice.com/publicdocs/circulars/23037.pdf (2023-02-24) | "Sunday 12 March 2023 to Friday 24 March 2023 (inclusive)" |
| 2023-10-30 – 11-03 | 18:28–18:30 (table) | https://web.archive.org/web/20230921015200id_/https://www.ice.com/publicdocs/futures/IFEU_Temporary_Trading_Hours_Mar2023.pdf (July 2023 doc) | "29 Oct 23 - 03 Nov 23 (Inclusive)" |
| 2024 spring | NOT FOUND | — | — |
| 2024-10-28 – 11-01 | 18:28–18:30 (table) | https://web.archive.org/web/20241007200545id_/https://www.ice.com/publicdocs/futures/IFEU_Temporary_Trading_Hours_Mar2023.pdf (Aug 2024 doc) | "27 Oct 24 - 01 Nov 24 (Inclusive)" |

A "table" row prints Brent 18:28-18:30 GMT / 14:28-14:30 EDT outright. A "period only" row is a circular that gives the
dates and says designated settlement periods change, but whose table was not retrieved. For those rows the CSV takes
18:28–18:30 from the identical Brent entry in every table fetched. The tables come from 2014 (circular 14/011,
https://web.archive.org/web/20140707100126id_/https://www.theice.com/publicdocs/circulars/14011.pdf, 2014-02-18),
2015–2024 (above) and 2025–2026 (Wayback 20250523135609 of Trading_Schedule_Temporary_Trading_Hours_for_DST.pdf, and
the live March 2026 copy). The Brent quote common to all of them: "18:28-18:30 GMT 14:28-14:30 EDT".

### C. Conflicts between sources

1. **Coffee C, autumn 2019 (28 Oct – 1 Nov): UNRESOLVED, and the CSV has no row for it.** The only copy found is a
   broker's repost (Optimus Futures, 2019-10-25), which says the Coffee C window is "unchanged". Against it, the
   ICE notices for spring 2019 and for every period from spring 2020 move Coffee to 13:23–13:25 NY. The repost also
   omits the Cocoa window change that every ICE notice of this kind carries, so it may reuse an old template. If
   the ICE pattern held, Coffee settled 13:23–13:25 NY on 2019-10-28 to 11-01. That is an inference, not in the CSV.
2. **Gasoil 16:27–16:30 vs 16:28–16:30.** ICE's own documents in 2013–March 2015 print a three-minute window from
   16:27. Every document from September 2015 prints a two-minute window from 16:28. This is a change of unknown date,
   not two sources disagreeing (see NOT FOUND). No source shows Gasoil at 17:28–17:30, and no Gasoil window other
   than 16:27/16:28–16:30 London appears anywhere 2013–2026, apart from holiday early closes.
3. **File name vs content.** `ICE_Futures_US_DST_Start_20190113.pdf` is the notice dated January 13, 2020, covering
   March 2020. The 2019 notice is `ICE_Futures_US_2019DST_Start_20190114.pdf`.
4. **Typos inside sources.** The autumn 2020 IFUS notice says "Friday, October 301, 2020". Its footnote says an
   earlier version gave the end date as Friday, November 2. The ccstrade repost of the spring 2021 notice prints
   "March 26, 2020". Its posting date (2021-03-01) and DST dates (US March 14, BST March 28) are those of 2021.
5. **Cached IFEU document month.** The brief calls the cached IFEU table "September 2026". The cached file is titled
   June 2026 (`Designated_Settlement_Periods_2026-06.txt`). Its Brent and Gasoil windows match the brief.
6. **Brent before the range.** Circular 11/159 (Dec 2011) prints Brent's normal window as 19:27–19:30. By the
   2013-05 capture it is 19:28–19:30. The change predates 2014-12 and is not dated here.
7. A Yahoo/Reuters item returned by a search as an "October 2019" notice quotes opening times of 3:30, 4:30 and 5:00.
   Those are the 2013 opening times (10092013exnotDST2.pdf), so it was not used.

### NOT FOUND (ICE settlement windows)

The search was cut short on 2026-09-27 at the coordinator's request, because the ICE windows became documentation
only. Official settlements come from the Sierra Chart daily files.

- **The date Gasoil moved from 16:27–16:30 to 16:28–16:30.** It is bounded between 2015-03-27 (circular 15/030
  table) and 2015-09-08 (the first product-page capture showing 16:28). Where we looked:
  - Wayback captures of ICE Futures Europe circulars 14/001–15/284. About 40 of roughly 150 mid-2015 numbers are
    archived, and none of them mentions a Gasoil settlement period.
  - ice.com circulars 14/001–14/040 fetched directly.
  - Web searches.
  The direct ice.com sweep of 15/045–15/175 was not run: ice.com returned HTTP 429 (Cloudflare, Retry-After
  ~55 min) after an early 4-thread burst, the limit was honoured, and the sweep was then cancelled. Gasoil became a
  BCOM component only in 2019, so this gap predates its index relevance.
- **IFEU Brent DST tables or circulars for 2019 (both periods), spring 2021 and spring 2024.** The archived
  circulars numbered ≤60 for those years (19/008–19/035, 21/002–21/036, 24/001–24/025) hold no DST circular. The
  Wayback CDX lists no other Temporary Trading Times capture for those periods. By the structure of every other
  year, these periods would be 10–29 Mar and 27 Oct–1 Nov 2019, 14–26 Mar 2021 and 10–28 Mar 2024. That is not
  documented, so there are no CSV rows.
- **ICE's own copies of the IFUS DST notices for spring 2015, spring 2016, spring 2018, autumn 2019 and spring 2021.**
  Reposts were used instead: comunicaffe.com, optimusfutures.com and ccstrade.com.
- **IFUS DST notices for autumn 2016, autumn 2017 and autumn 2018.** There is neither an ICE copy nor a repost. They
  are pre-2019, when every notice found left Coffee and Sugar unchanged.
- Where we looked for the IFUS notices:
  - The Wayback CDX of `theice.com` and `ice.com` `/publicdocs/futures_us/exchange_notices/*` (about 1,000 URLs).
  - Web searches.
  - Guessed file names for autumn 2019. These returned only HTTP 429 and were abandoned.
- **The CFTC rule-certification filing for the 2019 Coffee window change.** It was not located in one search. The
  exchange notice and the rulebook captures are the evidence used.
- **No Wayback capture of Settlement_Window.pdf between 2018-10 and 2021-05.** Rule 4.25(b) in the 2020-03 rulebook
  capture and the 2018-12 notice cover that span.
