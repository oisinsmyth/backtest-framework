# D454 — insider open-market purchases, stage 0: the SEC Form 3/4/5 bulk data on the dead-inclusive fixture — coverage, shape, timeliness, and what the buys sit in

**Pre-registration. Committed before the fetcher exists (R8).** Result in a separate file. **Stage 0
reads NO forward return.** D454 taken after `ls docs/decisions` and `git log --all` showed D453 as
the last number on either branch.

## 0. Why

The issuance line (D443–D453) was parked as real and unbookable: a persistent characteristic held
six months gives a few dozen independent observations in thirteen years. Insider buying is the
opposite shape — a dated filing, public within two business days, an *event* the D345 kernel and
the three declared controls handle as they stand. It carries information the price path cannot
(who inside the firm is putting money in), it is demand in the literal sense, and the literature's
effect on open-market purchases is large enough to survive this repo's cost lines (clustered and
opportunistic purchases in small firms: on the order of 1–2% a month over a quarter; sales weak).
**A stage 0 because the data has never been touched here** and the order is fixed: coverage,
shape, timeliness, proxy — then, separately, the event study.

## 1. Data, declared

**Probe before this record, disclosed:** one quarter (2015q1) was downloaded to learn the archive's
files and field names; the quarters 2006q1, 2010q1, 2015q1 and 2023q4 were HEAD-checked (200,
8–17 MB each) and 2026q2 (404). No statistic was computed.

- **Source:** the SEC's *Insider Transactions Data Sets*, one zip per calendar quarter,
  `https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/{yyyy}q{n}_form345.zip`,
  **2006q1 through 2026q1** (81 files, ~1 GB), fetched with the repo's project User-Agent, ≤ 2
  requests/s, cached under `data/raw/edgar/form345/` (git-ignored). Three tables are parsed:
  `SUBMISSION` (accession, `FILING_DATE`, `DOCUMENT_TYPE`, `ISSUERCIK`, `ISSUERTRADINGSYMBOL`),
  `REPORTINGOWNER` (accession, `RPTOWNERCIK`, `RPTOWNER_RELATIONSHIP`), `NONDERIV_TRANS`
  (accession, `TRANS_DATE`, `TRANS_FORM_TYPE`, `TRANS_CODE`, `TRANS_SHARES`, `TRANS_PRICEPERSHARE`,
  `TRANS_ACQUIRED_DISP_CD`, `SECURITY_TITLE`, `DIRECT_INDIRECT_OWNERSHIP`).
- **Issuer → fixture name:** by `ISSUERCIK` through D331's resolution (every CIK in a name's
  sequence, inside its own window); a filing whose CIK is unmapped but whose `ISSUERTRADINGSYMBOL`
  is a fixture symbol on a bar the name is live is counted separately as a *ticker match* and
  reported, not used, until stage 1 decides.
- **Only filings dated ≤ 2023-12-29 enter any stage-0 table**; 2024q1–2026q1 are fetched and held
  unread as the later slice (the same convention as D446's sample end).

## 2. The event, declared

An **insider open-market purchase filing** = a Form 4 submission (`DOCUMENT_TYPE` 4 or 4/A) with at
least one non-derivative transaction with `TRANS_CODE = P` and `TRANS_ACQUIRED_DISP_CD = A`,
`TRANS_SHARES > 0`, `TRANS_PRICEPERSHARE > 0`, on a security whose title contains *common*,
*ordinary* or *class A/B/C* and does not contain *preferred*, *warrant*, *option*, *note*,
*debenture* or *right* (a *common unit* is kept). Aggregated per (issuer, filing date):
**value** = Σ shares × price, **owners** = distinct `RPTOWNERCIK`, **role** = the set of
relationships (Director / Officer / TenPercentOwner / Other), **direct** share. The mirror,
**sales** (`S` and `D`), is built the same way for comparison only.
**Availability = the first fixture bar strictly after `FILING_DATE`.**

## 3. Measured (no forward return)

1. **Coverage.** Names with ≥ 1 purchase filing 2010–2023, by cohort / status, by CIK-resolution
   confidence, and dead names by delisting year; name-years with ≥ 1 purchase; the ticker-match
   count. Sales coverage beside.
2. **Shape.** Purchase filings per year; value p10/p50/p90; owners per filing; **clusters** (≥ 2
   distinct owners buying in the same name within 5 trading days); role mix; the purchase-to-sale
   ratio by year and its 2020 and 2022 spikes if present.
3. **Timeliness.** `FILING_DATE − TRANS_DATE` in business days: p50, p90, share > 2 (the statutory
   deadline), by year.
4. **Routine vs opportunistic** (Cohen–Malloy–Pomorski): a purchase is *routine* when the same
   owner bought the same name in the same calendar month in each of the two preceding years;
   the routine share, overall and by role.
5. **What the buys sit in — the proxy check.** At each purchase's availability bar, the name's
   tercile on the six tested axes (12-1 momentum, 20-day return, log price, log market cap, 60-day
   volatility, dollar volume — D392's cells where they exist, else the bar's cross-sectional
   terciles) against the eligible base rate of one third each; and the name's **issuance decile**
   (D444's panel, the latest fresh NS) against the base rate of one tenth. The same for sales.
6. **The tails, named:** the ten largest purchase filings by value and the ten largest clusters.

## 4. Abandon conditions, written before the fetch

- **A1** dead-cohort coverage (≥ 1 purchase filing while live) **< 50%**.
- **A2** fewer than **2,000** purchase filings on fixture names 2010–2023 (an event study at 2 SE
  needs the count; the literature gives ~1 per firm-year).
- **A3** timeliness median **> 5 business days** — the filing is not an event on this data.
- Otherwise a stage-1 event study is drafted separately (kernel entry at the availability bar,
  a declared hold, C1 state-matched names, C2 enumerated rotation of the event calendar, C3 a
  name-preserving time shuffle; both cost lines; one primary bar).

## 5. Predictions (MODERATE; literature and fixture shape, no data)

- **X-a** coverage: alive ≥ 85%, **dead ≥ 60%**, overall ≥ 75%; ~45–60% of live name-years carry a
  purchase; ticker-only matches < 5% of filings.
- **X-b** purchase filings 2010–2023 on the fixture: **12,000–35,000**; median value $25–60k, p90
  $0.5–1.5M; owners per filing median 1; clusters 12–25% of purchases; officers + directors
  ≥ 85% of filers; sales outnumber purchases 3–6 : 1, with the ratio falling toward 1 in 2020 Q1
  and 2022.
- **X-c** timeliness: median **1–2 business days**, > 2 on 10–20%, improving by year.
- **X-d** routine share **8–20%**, higher for officers than directors.
- **X-e** purchases sit in the **bottom tercile of 20-day return on ≥ 45%** and of 12-1 momentum on
  ≥ 40% (contrarian buying), in the small and cheap terciles (≥ 40% each); sales the mirror
  (top terciles). Purchases in the top issuance decile 8–15% and in the bottom decile 12–20%:
  insiders buy where the firm repurchases, mildly.
- **X-f** the ten largest purchases by value are 10% owners and controlling holders, not
  officers; the largest clusters are 2008–2009 and March 2020.

## 6. Not in scope

Any forward return; any trade; any holdout; derivative transactions; Forms 3 and 5 as events;
the 2024–2026 slice. Forty-sixth look by object; look #1 on insider demand.

## 7. Files

This record · `scripts/fetch_sec_form345.py` · `scripts/run_d454_insider_stage0.py` (`--build`,
`--run`, `--selftest`) · `data/d454_insider_events.csv.gz` (derived, committed) · `data/d454_stage0.json` · RESULT.
