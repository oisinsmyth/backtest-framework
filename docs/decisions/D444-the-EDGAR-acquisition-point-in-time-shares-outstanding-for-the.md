# D444 — the EDGAR acquisition: point-in-time shares outstanding for the dead-inclusive fixture, from XBRL companyfacts

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D444-the-EDGAR-acquisition-point-in-time-shares-outstanding-for-the-dead-inclusive-fixture-from-XBRL-companyfacts.md`. The H1 above is the full title.*

**Pre-registration. Committed before the fetcher exists (R8).** Result in a separate file. **A data
acquisition plus D443's stage-0 tables re-run on it; NO forward return is read.** D444 taken after
`ls docs/decisions` and `git log --all` showed nothing above D443.

## 0. Why

D443 ended on its first abandon condition: the vendor serves none of the fixture's 562 dead
names, so the issuance object — persistent (0.44 a year out), 90% orthogonal to everything tested,
orthogonal to momentum — could only be seen on survivors. The principal asked for the source that
serves the dead: the SEC's own XBRL facts. This record acquires them, builds the same panel D443
built, re-runs D443's five tables on it unchanged, and adds the two things EDGAR has that the
vendor did not: **the filing date of every value** (retiring D443's 90-day lag assumption) and
**every later restatement of the same value** (so the point-in-time series is the first-filed one).

## 1. Sources, declared

- **CIK per symbol:** the repo's own resolution, `data/fixtures/us_shorts_daily_raw_deals.json`
  `resolution` (D331, pulled 2026-09-05): 1,530 of 1,573 names resolved — alive 997 high / 14
  low; dead 141 high / 378 low (a full-text ticker match, span-consistent) / **43 unresolved**,
  counted as uncovered here. 28 names carry a CIK *sequence* (a ticker that migrated to a new
  registrant); every CIK in the sequence is fetched and its facts are used inside its own
  `from`–`to` window only.
- **Facts:** `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json`, one request per
  CIK (~1,560), the SEC's own JSON (3–6 MB each). User-Agent is the repo's project contact
  (`d331_edgar_deals.py`'s), ≤ 8 requests/s on 4 threads, gzip-cached under
  `data/raw/edgar/companyfacts/` (git-ignored, `/data/raw/`), resumable, 404 recorded and never
  refetched, 40 consecutive failures abort. **Probe before this record, disclosed:** two documents
  (RH; AESC, a dead name) were fetched to learn the tag names and the row schema; no statistic.
- **Splits:** as D443, the `daily_adjusted` cache's split coefficients, through the same
  `visible_splits` rule (a split is adjusted only where the raw series shows it).

## 2. Extraction, declared

Tags, in preference order for the share count: **`dei:EntityCommonStockSharesOutstanding`** (the
cover-page count, dated at its own `end`, on every 10-K/10-Q), then **`us-gaap:CommonStockShares-
Outstanding`** (the balance-sheet instant at period end) where the cover count is absent. Flows,
annual only: `us-gaap:PaymentsForRepurchaseOfCommonStock`, `us-gaap:ProceedsFromIssuanceOf-
CommonStock` (FY frames; they are sparse and inconsistently tagged and are *reported*, not gated on).

**Point in time.** For each (tag, `end`) the value used is the one with the **earliest `filed`**
date — the original report, before any restatement. **Availability = the first fixture bar
strictly after `filed`.** Every later filing of the same (tag, `end`) is kept aside and counted:
the *restatement share* is the fraction of first-filed values that a later filing changed by more
than 0.1%. Values with `form` outside {10-K, 10-Q, 10-K405, 10-KSB, 10-QSB, 20-F, 40-F, 8-K} are
excluded (S-1/S-4 counts are not periodic reports).

**The panel** has D443's schema exactly (`symbol, fiscal_date = end, avail_date = filed,
t_av, so_raw, so_adj, split_factor, NS, q_jump, flag, neq4, mcap_fiscal, NIY`), so D443's
`stage0()` runs on it without a line changed; NS = ln(SO_adj / SO_adj one year earlier) matched on
`end` within [330, 400] days as in D443; `[S]` flag at ln 1.5; NIY from the annual flows over the
market cap at `end` (SO_adj × adjusted close).

## 3. Measured (no forward return)

1. **Coverage,** D443's table by cohort and status, plus by CIK-resolution confidence (high /
   low / unresolved) and by delisting year for the dead; live name-years with a fresh NS.
2. **Filing lag:** `filed − end` in days, p10/p50/p90, by form (10-K vs 10-Q) and by year — the
   number D443 assumed at 90.
3. **Restatement share** (§2), and the median |log change| where restated.
4. **D443's tables 2–5 unchanged:** shape, persistence, the proxy check on the same six axes with
   the same R², the atlas-state cross-tab, the named tails.
5. **EDGAR against the vendor on the overlap:** for name-quarters where D443's vendor panel and
   this one both carry a balance-sheet share count at the same period end, |ln(EDGAR / vendor)|:
   median and the share within 1%; and the split judgement: the share of split events the
   first-filed EDGAR series shows as visible (it is as-reported by construction, so this is a
   check of the point-in-time extraction, not of the vendor).

## 4. Abandon conditions (D443's, unchanged)

- **A1** dead-cohort coverage (≥ 1 usable NS) < 50%. — **A2** rank R² > 0.50 or any |ρ| > 0.40.
- **A3** one-year persistence < 0.10.
- None firing → a stage 1 (forward returns, state-matched control, enumerated rotation,
  persistent-selector control) is drafted as a separate record for the principal.

## 5. Predictions (MODERATE)

- **X-a** coverage: alive ≥ 92%; **dead 65–85%** — the 43 unresolved (8%) are lost, and names
  delisted before XBRL was universal (phase-in completed for fiscal periods after June 2011)
  have few or no facts; dead names delisted 2013+ ≥ 85%; overall ≥ 85%. A1 does not fire.
- **X-b** filing lag: median **38–48 days**; 10-Q p50 ≈ 40, 10-K p50 ≈ 60–75; p90 ≈ 80; fewer than
  5% beyond 90 days — D443's 90-day rule was conservative on 95% of values.
- **X-c** restatement share **5–15%** of first-filed share counts; where restated, median |log
  change| under 2%.
- **X-d** shape, now with the dead in: NS median **+0.5 to +1.5%/yr** (D443: +0.2 on survivors),
  NS > 0 on **60–68%**, net repurchase share **45–55%** (D443: 62%) — the issuers come back.
- **X-e** persistence 1y **0.35–0.50**; proxy R² **0.08–0.20**, max |ρ| < 0.30, momentum |ρ| < 0.10.
- **X-f** EDGAR vs vendor on the overlap: within 1% on **≥ 85%** of name-quarters, median |log
  ratio| < 0.3%; the first-filed EDGAR series shows **≥ 90%** of split events as visible
  (D443's vendor series: 55%).

## 6. Not in scope

Forward returns; any trade; any holdout; insider and short-interest sources. The SEC's fair-
access policy is respected exactly as D331 did. Forty-third look by object; look #1 on share
supply from a primary source.

## 7. Files

This record · `scripts/fetch_edgar_companyfacts.py` · `scripts/run_d444_edgar_issuance.py`
(`--build`, `--run`, `--selftest`; imports D443's `stage0`) · `data/d444_issuance_panel.csv.gz`,
`data/d444_issuance_panel_info.json`, `data/d444_stage0.json` · RESULT.
