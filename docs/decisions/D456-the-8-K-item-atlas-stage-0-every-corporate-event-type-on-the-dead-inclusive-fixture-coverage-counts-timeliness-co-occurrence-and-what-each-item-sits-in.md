# D456 — the 8-K item atlas, stage 0: every corporate-event type on the dead-inclusive fixture — coverage, counts, timeliness, co-occurrence, and what each item sits in

**Pre-registration. Committed before the parser exists (R8).** Result in a separate file. **Stage 0
reads NO forward return.** D456 taken after `ls docs/decisions` and `git log --all` showed D455 as
the last number on either branch.

## 0. Why an atlas, and why 8-K items

Three lines (the volume shock, issuance, insider purchases) each found a real per-trade effect
that lived in small, thin, beaten-down names held a quarter, and none cleared a 60–90 bp round
trip. The next line must resolve in days or move a name by more than its spread. **Corporate
events do both**, and every one is dated and item-coded on the SEC's own index: a delisting
notice (3.01), a non-reliance / restatement (4.02), an officer departure (5.02), a completed
acquisition (2.01), a material impairment (2.06), a triggering event on a debt obligation (2.04),
an earnings release (2.02). The information is not in the price path, the names include the dead,
and the filing date is point in time. **An atlas rather than a bet** because twenty item types
are a family and the D392/D434/D435 method exists for exactly this: every cell measured, the
same controls on every cell, the family priced once.

## 1. Data, declared

- **Source:** the EDGAR submissions index per CIK (`data.sec.gov/submissions/CIK##########.json`
  and its paginated history files), **already cached by D331** under `temp/edgar/submissions/`
  (3,567 documents: the recent 1,000 filings per CIK plus every history page overlapping the
  name's window `first_bar − 365 d .. last_bar`). **`temp/` is deletable:** the parser writes the
  derived event table to `data/` (committed), and if a CIK's document is missing it is re-fetched
  with D331's `Fetcher` (same project User-Agent, ≤ 8 requests/s, same cache).
- **Issuer → name** by CIK through D331's resolution, inside each CIK's window (the D444/D454
  convention); the 43 unresolved names are uncovered and counted.
- **Fields:** `form`, `filingDate`, `reportDate` (the event date the 8-K reports), `items`,
  `accessionNumber`. Forms **8-K and 8-K/A** only.
- **Only filings dated ≤ 2023-12-29 enter any stage-0 table.** Filings from 2024-01-01 to
  2026-08-26 are parsed into the table and **held unread** as the confirmation slice for a later
  stage (§6).

**Probe before this record, disclosed:** 80 cached documents were opened to learn the field
names and the item vocabulary (9.01, 2.02, 8.01, 5.02, 7.01, 1.01, 5.07, 2.03 … and legacy
single-digit codes on pre-2004 filings). No statistic on any fixture name was computed.

## 2. The cells

An **event** is one 8-K filing on one name; it enters the cell of **every item it carries**
(disclosed; the co-occurrence table shows how much this double-counts), except **9.01 (exhibits)
and 7.01 (Regulation FD)** which are not events and are excluded as cells (7.01 is reported as a
co-occurrence only). A filing with a single item other than 9.01 is a **pure** event of that
item, reported beside. **Cells = every modern item code with ≥ 300 filings 2010–2023 on eligible
names**, from: 1.01, 1.02, 1.03, 2.01, 2.02, 2.03, 2.04, 2.05, 2.06, 3.01, 3.02, 3.03, 4.01, 4.02,
5.01, 5.02, 5.03, 5.07, 5.08, 8.01. **Availability = the first fixture bar strictly after
`filingDate`.**

## 3. Measured (no forward return)

1. **Coverage.** Names with ≥ 1 8-K while live 2010–2023, by cohort / status / CIK confidence;
   8-Ks per live name-year (p10/p50/p90); the 43 unresolved.
2. **Counts.** Filings per item per year; the cells that clear 300; pure-event counts per item.
3. **Timeliness.** `filingDate − reportDate` in business days per item: p50, p90, share beyond
   the four-business-day rule.
4. **Co-occurrence.** The item × item matrix (share of filings carrying both); the share of each
   item filed the same day as a 2.02.
5. **What each item sits in — the proxy check (D454 §5's).** For each cell, the filer's tercile on
   price, volatility, momentum (D392's cells), 20-day return and dollar volume at the availability
   bar, against 1/3 each; the dead-cohort share of the cell's filers against the fixture's 36%.
6. **The tails, named:** the ten names with the most 8-Ks; the ten names with the most 3.01
   and 4.02 filings.

## 4. Abandon conditions, written before the parse

- **A1** dead-cohort coverage (≥ 1 8-K while live) **< 50%**.
- **A2** fewer than **8 cells** with ≥ 300 filings.
- **A3** timeliness median **> 6 business days** on the earnings cell (2.02) — the index dates
  are not event dates.
- Otherwise **stage 1 is the atlas with returns**, drafted separately (§6).

## 5. Predictions (MODERATE)

- **X-a** coverage: alive ≥ 95%, **dead ≥ 85%** (every listed issuer files 8-Ks; the dead file
  more in their last year); 8-Ks per live name-year median **6–10**.
- **X-b** cells clearing 300: **12–16**; 2.02 is **30–40%** of all 8-Ks and 5.02 **12–20%**; 4.02
  under **250** filings; 3.01 **300–800**; 2.06 300–600.
- **X-c** timeliness: median **1–2 business days**, beyond four days on **< 10%**, tightest on 2.02
  (earnings are filed the day of the release).
- **X-d** co-occurrence: 1.01 carries 2.03 or 9.01 on ≥ 60%; 5.02 is filed alone (pure) on ≥ 40%;
  8.01 is the catch-all (co-occurs with everything).
- **X-e** state: 3.01, 4.02, 2.04 and 2.05 filers sit in the **bottom price and momentum terciles
  on ≥ 55%** and are **dead-cohort on ≥ 60%** (3.01 ≥ 75%); 2.02 and 5.07 are flat (33 ± 5); 2.01
  filers skew to the top size tercile.
- **X-f** the names with the most 8-Ks are serial acquirers and REITs (1.01/2.03/8.01 filers);
  the most 3.01 filers are the collapsed cohort.

## 6. The stage the atlas leads to (declared here, run under its own record)

Every cell that clears 300, **long and short both scored** (the atlas does not pick a sign), the
D345 kernel at **cap 10** (two weeks — corporate events resolve in days), the **state-matched
control per cell** (same day, same price × volatility × momentum cell, no 8-K of any item within
±5 bars), the **enumerated rotation of each cell's calendar**, both cost lines. A cell **clears**
when its signed gross per trade is beyond the control's p95 on the side it favours *and* its book
is beyond the rotation's p95 — and the family is priced by requiring, in addition, that the cleared
cells **reproduce on the 2024-01 to 2026-08 slice of the same names**, parsed here and unread
until that record and the principal's word. That is the multiplicity control: selection on
2010–2023, confirmation on data no cell has seen.

## 7. Not in scope

Any forward return; any trade; any holdout; 8-K text; Forms other than 8-K. Forty-eighth look by
object; look #0 of the corporate-event line.

## 8. Files

This record · `scripts/run_d456_8k_atlas_stage0.py` (`--build`, `--run`, `--selftest`) ·
`data/d456_8k_events.csv.gz` (derived, committed; through 2026-08-26, with the 2024+ rows flagged
unread) · `data/d456_stage0.json` · RESULT.
