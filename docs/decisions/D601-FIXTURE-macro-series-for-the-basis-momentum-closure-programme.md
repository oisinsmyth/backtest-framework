# D601 — FIXTURE: **the four macro fixtures for the basis-momentum closure programme** — the He–Kelly–Manela intermediary factors (monthly and quarterly, 884 rows to 2025), the EIA weekly stocks (four series, 7,375 weeks, with the release-date lag), the OECD 3-month interbank rates for seven currencies (2,206 months, one source gap filled and flagged), and the per-contract daily cleared volume of the 17 commodity roots from the `statistics` archive (852,938 rows from 2015-11); the USDA NASS stocks fixture is built by the same fetcher once the principal's key is in place; every fixture gated, sidecar-tracked, manifest-registered; nothing here reads a return

*2026-09-21. A data record, not a study. Built for the D600 closure programme (M4, M5 and the
capacity table) and for the FX pre-registration to follow (the rates). Fetcher
`scripts/fetch_macro_series.py` (stdlib + pandas; `--fetch {hkm,eia,oecd,esmis,nass,all}` into
`data/raw/`, `--build` cache → fixtures + meta, `--selftest` proving every gate raises,
`--probe-nass` for the keyed source); builder `scripts/build_fut_cleared_volume_cm.py` (system
python, `databento`; `--probe`, `--build --workers 8`, `--selftest`). Nothing here computes a
return or reads any fixture the studies score.*

## 1. What was fetched, as found on 2026-09-21

| fixture | source | key | rows | span | committed? |
|---|---|---|---|---|---|
| `hkm_factors.csv.gz` + meta | zhiguohe.net, `He_Kelly_Manela_Factors_{monthly,quarterly}_250627.csv` (He, Kelly & Manela 2017, *JFE* 126(1)) | none | 884 (664 monthly, 220 quarterly) | 1970-01 → 2025-05 monthly; 1970Q1 → 2024Q4 quarterly | **no** — the authors' terms are non-commercial use; gitignored, hashed in the manifest, raw cached |
| `eia_weekly_stocks.csv` + meta | EIA keyless bulk archives `PET.zip` (55.4 MB) and `NG.zip` (4.7 MB): `WCESTUS1` crude ex-SPR, `WGTSTUS1` total gasoline, `WDISTUS1` distillate (thousand barrels), `NW2_EPG0_SWO_R48_BCF` Lower-48 working gas (Bcf) | none | 7,375 | crude and distillate from 1982-08-20, gasoline from 1990-01-05, gas from 2010-01-01; all to 2026-09-11 | yes (public domain, 1.1 MB) |
| `oecd_ir3tib_monthly.csv` + meta | OECD SDMX `DSD_STES@DF_FINMARK` IR3TIB, monthly, USA · EA20 · GBR · JPN · AUS · CAN · CHE — the series FRED republishes as `IR3TIB01xxM156N` | none | 2,206 | 2000-01 → 2026-08 (GBP to 2026-02, JPY from 2002-04) | yes (CC BY 4.0) |
| `fut_cleared_volume_cm_daily.csv.gz` + meta | the `statistics` archive already on disk (`GLBX-20260911-SDNLQ6M99S`, stat_type 6), windowed ids as D520/D521, one row per (root, contract, CME trade date) | none | 852,938 | 2015-11-19 → 2023-12-29, all 17 roots | **no** — CME-licensed; gitignored, hashed in the manifest |
| `nass_stocks.csv` + meta | USDA NASS Quick Stats (`api_GET`, keyed) for quarterly Grain Stocks (corn, soybeans, wheat), monthly Cattle on Feed, quarterly Hogs and Pigs; release datetimes scraped from the ESMIS archive (260 · 440 · 298 releases cached under `data/raw/esmis/`) | **`NASS_API_KEY` or `~/.config/nass/key`** | — | — | **not yet built**: the key is not on this machine; the fetcher says so and skips, never prompts |

**Not fetched, and why.** FRED (`fredgraph.csv`, keyless) resets every connection from this
machine — urllib, curl and PowerShell alike, while `api.stlouisfed.org` answers 400 for want of a
key — so the rates come from the OECD source itself, which is the same series; the fixture's G4
reproduces five FRED-published values (June 2019, five currencies) to 0.01. The FRBNY H.10 spot
rates (a diagnostic only in the FX design) are not fetched: the Fed's bulk package returned an
empty body, and the FX construction is spot-free.

## 2. Four things that bite, found on the way

1. **The He–Kelly–Manela file has two rows labelled 202501 and two labelled 20251** (the second
   of each is the next period, mislabelled). Both stay in the raw cache; the fixture drops every
   row carrying a duplicated label and records them in the meta. All four are in 2025, outside
   anything a study here reads (< 2024-01). G5 counts the raw file's uniquely labelled rows.
2. **The OECD USD series has no April 2020 observation** — the one missing currency-month in
   2009–2023 across seven currencies. It is filled with the mean of March and May (0.76 %) and
   **flagged** (`filled = True`); the meta lists it; a study treats a flagged month as present
   and says so. The allowance is one filled cell (G5).
3. **EIA values are the current vintage.** The bulk archive serves revised figures; there is no
   vintage history. The fixture carries a nominal release date (Wednesday for the petroleum
   report, Thursday for gas, after the Friday week-ending) for reading; **the study's known-at
   rule is `week_ending + 7 calendar days ≤ the month-end session`**, which covers every holiday
   shift and the June-2022 two-week outage without a calendar.
4. **The `statistics` archive publishes cleared volume only from 2015-11-19** on every one of the
   17 roots (D497's fixture starts in 2016 for the same reason). The gate is on the density over
   each root's own covered span (≥ 200 sessions a year), and the first session is recorded, not
   assumed — the first draft asserted 200 sessions a year over 2010–2023 and fired on every root
   ([[assert-code-not-data]]).

## 3. Gates (in each meta; `--selftest` proves each raises on a broken panel)

| fixture | gates |
|---|---|
| HKM | G1 no duplicate (freq, period); G2 capital ratio in (0, 1); G3 ≥ 600 monthly and ≥ 200 quarterly rows; G4 quarter-end monthly vs quarterly capital ratio corr 1.0000 > 0.9; G5 monthly rows equal the raw file's uniquely labelled rows |
| EIA | G1 no duplicate (series, week); G2 every stock > 0; G3 week-ending is a Friday (100 %); G4 nominal release after the week-ending; G5 every series weekly without gaps over 2010–2023 (≥ 700 weeks) |
| OECD | G1 no duplicate (currency, period); G2 seven currencies, every month 2009-01 → 2023-12 present after the one fill; G3 rates in (−2, 25) %; G4 five FRED-published values reproduced to 0.01; G5 at most one filled cell |
| cleared volume | V1 no duplicate (root, contract, session); V2 volume ≥ 0; V3 all 17 roots; V4 Saturday-dated sessions 0.000 %; V5 ≥ 200 sessions a year over the root's own span; V6 every root covered from 2016-01-04 |
| NASS (built later) | G1 no duplicate observation; G2 every stock > 0; G3 an ESMIS release found for ≥ 95 % of observations; G4 the release after the observation date by at most 60 days |

## 4. Files

`scripts/fetch_macro_series.py`, `scripts/build_fut_cleared_volume_cm.py`; the fixtures and
`.meta.json` sidecars under `data/fixtures/`; `data/data_manifest.json` rebuilt (125 listed, 0
missing, 0 changed on verify); raw caches `data/raw/{hkm,eia,oecd,esmis}` (gitignored). The
NASS fixture, when built, joins the same record by an addendum.
