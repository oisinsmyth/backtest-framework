# Index reweight flow: data inventory and gap register

Written 2026-09-26 for `INDEX_REWEIGHT_FLOW_PREREG.md` §§2, 3, 5, 8B, 12 and 16. It covers three things:

- what is on this machine for the model's data needs;
- what is missing;
- the cheapest route to each gap.

**Nothing was bought, downloaded or submitted.** Every cost below comes from a free Databento metadata call.

How this was measured:

- **Sources read:** `docs/data-available.md`, fixture `.meta.json` files, `data/futures_acquisition_manifest.json`, the job records, the Sierra download records, and a directory listing of `C:\SierraChart\Data`.
- **Method:** file names and `os.stat` sizes only. No price or trade file was opened.
- **The vault is not read:** CL/NG 2025-03-01 → 2026-09-18 is untouched. Sources and URLs for methodology facts belong in `SOURCES.md` (a separate agent writes it), not here.

---

## 1. The 15 CME roots

### 1.1 What the model needs from them

- **Drift (§4):** daily settlements of the **designated** contract under BCOM's lead-contract schedule, 2015 → present. This is often not the front month.
- **Stage R1 prices (§6):** 1-minute bars of the designated contract around each settlement window.
- **Gate C0 (§5):** `S_win` = aggressor-signed settlement-window volume minus its **trailing 20-day norm**, on monthly roll days (BD ~6–10) from 2016 to 2025-02.
  - Because of the trailing norm, C0 needs the window on **every session**, not only on roll days: about 2,386 sessions from 2015-12-01 to 2025-02-28, counting a 20-session warm-up.
- **R1 flow:** the same window on the January execution days, 10 years × 5 days.

### 1.2 Settlements

**Fixture:** `data/fixtures/fut_settle_strip.csv.gz`, with its meta.

- It holds every settlement of **every listed contract month** (`stat_type` 3, windowed ids), 2010-06-04 → **2026-09-10**.
- So the designated contract is always available, whatever BCOM's schedule turns out to be.
- It is gitignored and carried in the manifest by hash.

| root | status | rows | contracts | span |
|---|---|---:|---:|---|
| CL | ON DISK | 410,454 | 212 | 2010-06-04 → 2026-09-10 |
| NG | ON DISK | 561,197 | 282 | same |
| HO | ON DISK | 167,498 | 120 | same |
| RB | ON DISK | 168,676 | 120 | same |
| GC | ON DISK | 91,617 | 120 | same |
| SI | ON DISK | 83,521 | 120 | same |
| HG | ON DISK | 161,764 | 120 | same |
| ZC | ON DISK | 61,175 | 50 | same |
| ZS | ON DISK | 82,919 | 70 | same |
| ZW | ON DISK | 53,640 | 50 | same |
| **KE** | **MISSING** | — | — | KE is not in `ROOTS_41` (see below) |
| ZL | ON DISK | 96,708 | 80 | same |
| ZM | ON DISK | 96,063 | 80 | same |
| LE | ON DISK | 36,676 | 60 | same |
| HE | ON DISK | 47,613 | 80 | same |

**Why KE is missing.** KE is not in `ROOTS_41` (`scripts/probe_plan_cost.py`), so the `statistics` and `definition` schemas were never bought for it.

- It is also absent from every fixture: `fut_settle_strip`, `fut_day1m`, `fut_breadth_hourly` and `futures_impact_params`.
- Its window row exists in `settlement_windows.csv`.
- A KE `statistics` + `definition` pull currently **quotes $0.00** (§4.3).

**What bites when reading the strip** (from its meta and `data-available.md`):

- An exact-zero settlement is a missing marker. Drop it.
- Negative settlements are real only for CL in April 2020.
- Some holidays carry copied settlements: NG and CL on Good Fridays and holiday eves. Drop them before counting business days for BCOM's BD-n roll.
- CL and NG have no settlement on 2020-02-27 or 2020-06-30. They are filled from the EIA in `data/ledger_settle_holes_2020.csv`.
- CLK0 on 2020-04-17 is wrong in the strip.
- The strip stops at 2026-09-10. The forward recorder (Track 2) has no BCOM settlement job yet.
- CL/NG from 2025-03-01 is inside the ledger's sealed vault. Read it only through `load_panel(reserved_from="2025-03-01")`.

### 1.3 One-minute bars

**Committed fixture:** `fut_day1m.parquet`.

- It covers **front month only** (elected by highest full-day volume, from `fut_breadth_hourly`), 09:00–15:59 ET, 2010-06-07 → 2026-09-09.
- It has 36 roots. **KE is not among them.**
- The front month is **not** the BCOM designated contract on many days, so this fixture alone cannot serve R1.

**Raw per-contract bars ARE on disk:** `ohlcv-1m` ALL_SYMBOLS, `data/raw/databento/` (10 job directories), 2010-06-06 → 2026-09-10, 12.22 GB.

- This is every instrument, KE included.
- Building a designated-contract 1-minute panel from it needs a builder using D520/D521 windowed id labelling.
- **No such builder exists yet.**

Usable span per root (`fut_day5m` coverage, `data-available.md` §1):

| root | per-contract 1m on disk | front-month fixture | usable from | note |
|---|---|---|---|---|
| CL NG HO RB | yes (raw) | `fut_day1m` | 2016 (energy day session absent before 2015-06) | CL/NG vault from 2025-03-01 |
| GC SI HG | yes (raw) | `fut_day1m` | 2010/2011 | |
| ZC ZS ZW ZL ZM | yes (raw) | `fut_day1m` (58 slots, 09:30–14:20) | 2013/2014 | |
| **KE** | **yes (raw only)** | **none** | unmeasured | needs its own build |
| LE HE | yes (raw) | `fut_day1m` (55 slots) | 2016 | |

**Other derived bars:**

- `ohlcv-1s` exists for CL, NG, CLT and NGT only, 2017-05-21 → 2026-09-18. It is unsigned; D624 showed it cannot sign window flow.
- The raw archive re-downloads free only until about 2026-10-11. After that it is a paid refetch (`data-available.md` §1). It is on disk now.

### 1.4 Signed (aggressor) flow

**Sierra Chart** (`C:\SierraChart\Data`, Package 3, paid to 2027-10-24): 1-tick `.scid` files.

- AskVolume and BidVolume are Sierra's signing.
- **Known answer** (`data/sierra_aggressor_check_{ho,rb}.json`), HO/RB window 14:28–14:30 against Databento `trades`:
  - window total volume is identical;
  - B/A trades match the exchange flag exactly;
  - net-flow r is **0.877 (HO, 686 sessions) and 0.875 (RB, 694)**, with sign agreement of 80%.
- **The error source:** about 29% of window volume carries no exchange aggressor (spread-leg fills). Sierra signs it by its own rule, with no field to mark it.
- **Verdict:** this clears the principal's r ≥ 0.8 bar and **fails** the "is the exchange flag" bar (r ≥ 0.99).
- **Sierra TAS files do carry the exchange flag** (r 0.9998).

**Databento `tbbo`** (trade plus prior quote, with the exchange aggressor flag): ALL_SYMBOLS, 2025-09-11 → 2026-09-11, 37.3 GB. That covers all 15 roots, **after** the C0 span.

- **CL/NG:** this span lies inside the sealed vault.
- **Other 13 roots:** usable only as a known-answer reference for Sierra, the way HO/RB were used.

Per-root status:

| root | Sierra 1-tick on disk (file names, sizes) | Databento signed trades on disk | signed flow in C0 span (2016 → 2025-02) |
|---|---|---|---|
| CL | **89 files, 22.68 GB**, CLN15 → CLZ25. All 12 months from 2021. F/H/K/N/U/X and a few others from 2015. The 77 in-sample files in `sierra_ledger_download_record.json` all pass `cut_short`. CLM21–25 and CLZ21–25 lack their early holding months (Sierra serves ~5 months before expiry) | tbbo 2025-09-11 → (vault); `trades` 2026-09-19 → 2026-09-23 | **ON DISK (Sierra)**, pending the CL known-answer check after 2026-10-10 (AITODO). Derived window panel `data/ledger_signed_window_daily.csv.gz`: 14:28–14:30, 2017-05-22 → 2025-02-28, for the ledger's held contracts only |
| NG | **69 files, 6.01 GB**, months F/H/K/N/U/X, 2015 → 2026. 48 in-sample; 10 vault files downloaded, not to be read (`sierra_vault_download_record.json`) | same as CL | **ON DISK (Sierra)** for F/H/K/N/U/X. Same derived panel and caveat as CL |
| HO | 7 files, 0.24 GB (HOZ25, HOK26 → HOV26); TAS 12 files | `trades` 2025-09-25 → 2026-09-19 (`GLBX-20260924-SPAPH565SK`); tbbo | **MISSING** |
| RB | 7 files, 0.28 GB (RBZ25, RBK26 → RBV26); TAS 12 files | same as HO | **MISSING** |
| GC | none | tbbo 2025-09-11 → 2026-09-11 | **MISSING** |
| SI | none | tbbo | **MISSING** |
| HG | none | tbbo | **MISSING** |
| ZC | none | tbbo | **MISSING** |
| ZS | none | tbbo | **MISSING** |
| ZW | none | tbbo | **MISSING** |
| KE | none | tbbo (ALL_SYMBOLS, unverified for KE) | **MISSING** |
| ZL | none | tbbo | **MISSING** |
| ZM | none | tbbo | **MISSING** |
| LE | none | tbbo | **MISSING** |
| HE | none | tbbo | **MISSING** |

Other files in the Sierra folder, none relevant here: MES-CME (2 files plus 1 empty), YM-CBOT (1 plus 1 empty), HHU26 and HHV26, and **`UHOK26-ICEEU.scid` at 56 bytes (header only)**. An ICE Europe symbol was tried and returned no records. Whether Package 3 carries ICE Europe at all is unverified.

### 1.5 Settlement windows (D586, `data/settlement_windows.csv`)

| root | window ET | window CT | `history_status` | earliest sourced | served by `window_for` for 2016–2025? |
|---|---|---|---|---|---|
| CL NG HO RB | 14:28:00–14:30:00 (expiring month on its last day: 14:00–14:30) | 13:28–13:30 | dated_notice (SER-4867) | 2009-06-01 | **yes** |
| GC | 13:29:00–13:30:00 | 12:29–12:30 | current_only | 2026-09-21 | **no, raises** |
| SI | 13:24:00–13:25:00 | 12:24–12:25 | current_only | 2026-09-21 | **no** |
| HG | 12:59:00–13:00:00 | 11:59–12:00 | current_only | 2026-09-21 | **no** |
| ZC ZS ZW KE ZL ZM | 14:14:00–14:15:00 (a 13:59–14:00 CT window from 2012-06-25 is `record_only`, end unsourced; KE has no record row) | 13:14–13:15 | current_only | 2026-09-21 | **no** |
| LE HE | 13:59:30–14:00:00 (30 s, below 1-minute resolution) | 12:59:30–13:00:00 | current_only | 2026-09-21 | **no** |

**4 of 15 roots have a sourced window for the C0/R1 span.** The other 11 raise by design (unit test 12).

---

## 2. Non-CME components (R-Q3), used for drift only

Weights are from Bloomberg's public factsheet "Bloomberg Commodity Subindices", as of 2026-08-31 (`https://assets.bbhub.io/professional/sites/27/BCOM-Subindices.pdf`, accessed 2026-09-26). This is the current weight only. Historical lists and weights are R-Q2, handled in SOURCES.md.

| component | exchange | weight 2026-08-31 | on disk | Databento | other candidate |
|---|---|---:|---|---|---|
| Brent crude | ICE Europe (BRN) | 10.29% | **none**. Proxy: NYMEX BZ (Brent Last Day Financial, cash-settled to ICE Brent) has every month's settlement in `fut_settle_strip`, 2010 → 2026-09-10. Its month labels differ from ICE's | IFEU.IMPACT, from **2018-12-23** | BCOM ER subindex `BCOMCO` (Investing.com page exists; Yahoo `^BCOMCO5T` found by search, unverified) |
| Low sulphur gasoil | ICE Europe (G) | 4.80% | none | IFEU.IMPACT, from 2018-12-23 | BCOM subindex (TR ticker `BCOMGOT` in the factsheet) |
| Aluminium | LME | 3.41% | none | **not offered** (no LME dataset in `list_datasets`) | Westmetall free LME cash and 3-month; BCOM subindex `BCOMAL` |
| Zinc | LME | 2.26% | none | not offered | same (`BCOMZS`) |
| Nickel | LME | 1.71% | none | not offered | same; Investing.com `BCOMNI` page exists |
| Lead | LME | 0.72% | none | not offered | same (`BCOMPB`) |
| Sugar No.11 | ICE US (SB) | 2.86% | none | IFUS.IMPACT, from 2018-12-23 | `BCOMSB` |
| Coffee | ICE US (KC) | 1.97% | none | IFUS.IMPACT, from 2018-12-23 | `BCOMKC` |
| Cotton | ICE US (CT) | 1.87% | none | IFUS.IMPACT, from 2018-12-23 | `BCOMCT` |
| Cocoa | ICE US (CC) | 1.60% | none | IFUS.IMPACT, from 2018-12-23 | `BCOMCC` |
| **Total non-CME** | | **31.49%** | | | |

The 15 CME roots carry the remaining 68.51%. That includes COMEX copper (HG) at 5.92% and KC wheat (KE) at 2.30%.

**The consequence for Gate R0 (§8).** Any year with more than 10% index weight in missing-price components is excluded from R1–R3. With nothing non-CME on disk, **every year 2016–2026 is excluded**.

- ICE alone is 25.39% and LME alone is 8.10%.
- So even full ICE coverage from Databento leaves each year at 8.1% missing: just under the 10% bar, but with a weight error bound to report.
- Databento offers nothing for **2015 → 2018-12-22**, so 2016–2018 would stay excluded on that route.

**Cheapest routes.** Each needs the owner's decision and a check of the source's terms of use.

1. **Published BCOM single-commodity excess-return subindex levels** (BCOMCO, BCOMAL, BCOMSB and so on).
   - These are exactly the `R_i(t)` of §4.1, so **no component price is needed for drift**, for LME too.
   - They would also be the Gate R0 comparison series.
   - The public factsheet gives only point-in-time 1M/3M/YTD/1Y returns.
   - Daily history appears on Investing.com (BCOMCO and BCOMNI pages confirmed by search) and possibly on Yahoo. Both are free to view; automated download may breach their terms.
   - Bloomberg's own quote pages are script-gated.
   - Using published sub-indices in place of settlements for non-CME drift is a **spec question for the owner**: §3.3 says settlements.
2. **Databento ohlcv-1d** for ICE outrights: **$24.17** for 2018-12-23 → 2026-09-26. This is a daily **close**, not the settlement. ICE settles Brent and gasoil on a 19:28–19:30 London window, so the close carries noise.
3. **LME prices:** Westmetall publishes free LME cash-settlement and 3-month prices (tables per metal; the depth of history is not stated on the page). These are not BCOM's prompt-date contracts, so they approximate. LME's own historical data is paid (LME Portal).

---

## 3. The Databento metadata calls made (free) and their results

All calls were made on 2026-09-26 with the system interpreter (`databento` 0.86.0) and the key from `~/.config/databento/key`, which was never printed. Only these call types were used:

- `metadata.list_datasets`, `metadata.get_dataset_range`, `metadata.list_schemas`, `metadata.list_publishers`;
- `symbology.resolve`;
- `metadata.get_billable_size` and `metadata.get_cost`.

**No batch job was submitted and no `get_range` was called.** End dates are exclusive. Costs are the quotes returned *today*, under whatever entitlement the account holds: the CME Standard subscription is live, and it is what makes L0 GLBX schemas $0.

### 3.1 Datasets and ranges

- `list_datasets` returns `IFEU.IMPACT`, `IFUS.IMPACT`, `IFLL.IMPACT` and `NDEX.IMPACT` among others. **There is no LME dataset.**
- `get_dataset_range`: all four ICE datasets start **2018-12-23T00:00Z** and end 2026-09-26 for every schema (`statistics`, `ohlcv-1d`, `trades`, `definition` and so on).
- `symbology.resolve(stype_in="parent", 2024-06-03 → 06-05)` resolves `BRN.FUT` (2,060 rows), `G.FUT` (959), `SB.FUT`, `KC.FUT`, `CT.FUT` and `CC.FUT`.
  - `B.FUT`, `GO.FUT` and `ULS.FUT` do not resolve (422).
  - Parent → `raw_symbol` is not supported on IFEU (422).

### 3.2 ICE quotes

| call | dataset | symbols (stype) | schema | span | billable | USD |
|---|---|---|---|---|---:|---:|
| A1 | IFEU.IMPACT | BRN.FUT, G.FUT (parent) | statistics | 2018-12-23 → 2026-09-26 | 338.6 GB | 7,882.84 |
| A2 | IFEU.IMPACT | same | ohlcv-1d | same | 60.5 MB | 135.33 |
| A3 | IFEU.IMPACT | same | definition | same | 13.4 GB | 99.79 |
| A4 | IFEU.IMPACT | BRN.FUT | statistics | 2019 | 21.7 GB | 504.97 |
| A5 | IFEU.IMPACT | G.FUT | statistics | 2019 | 5.26 GB | 122.56 |
| A6 | IFUS.IMPACT | SB, KC, CT, CC .FUT (parent) | statistics | 2018-12-23 → 2026-09-26 | 205.5 GB | 3,827.73 |
| A7 | IFUS.IMPACT | same | ohlcv-1d | same | 25.7 MB | 95.67 |
| A8 | IFUS.IMPACT | same | definition | same | 0.93 GB | 17.39 |
| A9–12 | IFUS.IMPACT | SB / KC / CT / CC, one each | statistics | 2019 | 6.66 / 8.80 / 4.27 / 5.14 GB | 124.14 / 163.92 / 79.55 / 95.75 |
| A13 | IFEU.IMPACT | BRN.c.0–c.11, G.c.0–c.11 (continuous = outrights only) | statistics | 2018-12-23 → 2026-09-26 | 217.0 GB | 5,051.41 |
| A14 | IFEU.IMPACT | same | **ohlcv-1d** | same | 5.66 MB | **12.64** |
| A15 | IFEU.IMPACT | BRN.c.0 | statistics | 2019 | 5.91 GB | 137.69 |
| A16 | IFUS.IMPACT | SB, KC, CT, CC .c.0–c.5 (continuous) | statistics | 2018-12-23 → 2026-09-26 | 51.1 GB | 951.66 |
| A17 | IFUS.IMPACT | same | **ohlcv-1d** | same | 3.09 MB | **11.53** |
| A18 | IFUS.IMPACT | SB.c.0 | statistics | 2019 | 0.34 GB | 6.36 |
| A19 | IFEU.IMPACT | BRN / G .c.0–c.11 | ohlcv-1m | 2018-12-23 → 2026-09-26 | 1.84 GB | 513.42 |
| A20 | IFUS.IMPACT | SB, KC, CT, CC .c.0–c.5 | ohlcv-1m | same | 0.70 GB | 327.96 |

**What the ICE quotes say:**

- ICE `statistics` is priced out: 5.9 GB for one Brent contract-year, because the schema streams intraday statistic updates.
- The cheap ICE route is **ohlcv-1d on outrights: $24.17 in total**. It gives a close, not a settlement.
- A calendar-ranked `c.N` set covers the designated months if N is wide enough. Whether c.0–c.11 and c.0–c.5 suffice depends on BCOM's schedule (R-Q1).

### 3.3 KE on GLBX (the one CME root not bought)

| call | symbols | schema | span | billable | USD |
|---|---|---|---|---:|---:|
| B1 | KE.FUT (parent) | statistics | 2010-06-06 → 2026-09-26 | 0.92 GB | **0.00** |
| B2 | KE.FUT | definition | same | 1.27 GB | **0.00** |
| B3 | KE.FUT | ohlcv-1m | same | 0.52 GB | 0.00 (already on disk inside the ALL_SYMBOLS pull) |
| B4 | KE.FUT | ohlcv-1d | same | 7.1 MB | 0.00 |

**Time-critical.** The $0 depends on the CME Standard subscription bought about 2026-09-11. Its end date is not recorded here; the 30-day refetch clock for its jobs runs to about 2026-10-11.

### 3.4 Signed flow: `trades` inside the settlement windows (C0 and R1)

Setup:

- **Symbols:** parent `.FUT` per group. This includes spreads, as the data would.
- **Windows:** the current rows of `settlement_windows.csv`, converted ET → UTC with DST.
- **Sample days:** 15 days at business day ~6–8 of a month, about one every 7 months: 2016-03-09, 2016-11-09, 2017-07-12, 2018-03-09, 2018-11-09, 2019-07-10, 2020-03-10, 2020-11-10, 2021-07-12, 2022-03-09, 2022-11-09, 2023-07-12, 2024-01-10, 2024-11-12, 2025-02-11.
- **Three quotes per day:**
  - **window**: exactly [W_start, W_end);
  - **padded**: [W_start − 30 min, W_end + 5 min), which also covers R1's t0 = W_start − 20;
  - **whole day**: 00:00–24:00 UTC. For energy, all 15 days were quoted; for the other groups, 4 of them (2016-11-09, 2019-07-10, 2022-03-09, 2024-11-12).
- **Whole span:** one parent quote per group, 2015-12-01 → 2025-03-01, as the upper bound.

**How the quotes are scaled:** the mean sample-day cost × 2,386 sessions.

- 2,386 is CL's trading sessions from 2015-12-01 to 2025-02-28 in `cme_session_calendar`, which includes the 20-session warm-up for the trailing norm.
- Grains and livestock use 2,326 sessions.
- R1 uses 50 January execution days.

The calendar's session count includes holiday Globex sessions, so the scaled figures are slightly conservative.

| group (symbols) | window | mean $/day, window | mean $/day, padded | mean $/day, whole day | C0 all sessions, window | C0 padded | C0 whole days (whole-span quote) | R1 50 days, window / padded |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| energy (CL NG HO RB) | 14:28–14:30 ET | 0.0597 | 0.1161 | 0.8585 | $142 | $277 | **$1,595.25** (61.2 GB) | $2.98 / $5.80 |
| GC | 13:29–13:30 | 0.0032 | 0.0086 | 0.2726 | $8 | $20 | $306.49 (11.8 GB) | $0.16 / $0.43 |
| SI | 13:24–13:25 | 0.0014 | 0.0029 | 0.0619 | $3 | $7 | $98.41 (3.8 GB) | $0.07 / $0.15 |
| HG | 12:59–13:00 | 0.0019 | 0.0042 | 0.0737 | $4 | $10 | $122.74 (4.7 GB) | $0.09 / $0.21 |
| grains (ZC ZS ZW KE ZL ZM) | 14:14–14:15 | 0.0246 | 0.0459 | 0.3213 | $57 | $107 | $626.10 (24.0 GB) | $1.23 / $2.29 |
| livestock (LE HE) | 13:59:30–14:00 | 0.0122 | 0.0213 | 0.0715 | $28 | $50 | $137.80 (5.3 GB) | $0.61 / $1.07 |
| **all 15** | | | | | **≈ $243** | **≈ $471** | **$2,886.79** | **≈ $5.14 / $9.95** |

**Notes on these quotes:**

- **Energy carries the most weight.** Its window cost ranged from $0.043 to $0.106 a day. Excluding CL and NG, which Sierra already covers, would roughly halve the energy line. That split was not quoted.
- **Tiny windows are not billed pro rata.** A 30-second livestock window bills 0.47 MB against 2.74 MB for the whole day. Treat the window figures as quotes, not as a bytes-per-second law.
- **The practical cost of window-only pulls is request count.** One streaming request is needed per (session, group) — about 14,300 in all — because a batch job takes one time range.
- A single common daily range for all 15 roots (about 12:29 → 14:35 ET) would cut that to about 2,386 requests. It was **not quoted**.
- **Databento's truth is also unsigned on spread-leg fills.** On HO/RB, about 29% of window volume has side `N`, so the exchange-flag `S_win` is itself net of that volume.
- **An earlier ledger quote, for comparison** (`data/ledger_pull_quote.json`, 2026-09-24): CL+NG whole-day `trades` 2017-05-21 → 2025-03-01 was $1,024.23 (39.3 GB). The ledger's window-only estimate was about $108 in-sample.

### 3.5 Sierra Chart route (a free download under the principal's Package 3)

**The estimate is built from the existing records, not from any new download:**

- **Measured file sizes:**
  - CL 77 in-sample files: 19.50 GB, 253 MB mean (`sierra_ledger_download_record.json`);
  - NG 48 files: 4.27 GB, 89 MB mean;
  - HO 7 files: 28–44 MB; RB 7 files: 36–53 MB.
- **Measured download speed** (memory note on Sierra quirks): serial; CL about 1–2 minutes a file, NG about 25 seconds.
- **Scaling rule:** bytes are 40 per trade record. Per-file size is scaled by each root's 2016–2023 day-session ADV (`data/futures_impact_params.json`, line `day1m_2016_2023`), at the measured 0.95–1.6 kB per ADV contract (CL 0.95, NG 1.15, HO/RB 1.6).

Estimated file sizes:

| root | ADV (contracts) | est. MB per file |
|---|---:|---:|
| HO / RB | 21.8k / 21.7k | 28–53 (measured) |
| GC | 106.1k | 106–170 |
| SI | 35.0k | 35–56 |
| HG | 29.9k | 30–48 |
| ZC | 95.6k | 96–153 |
| ZS | 61.5k | 62–98 |
| ZW | 36.9k | 37–59 |
| KE | not measured (not in the 36 roots) | — |
| ZL | 31.2k | 31–50 |
| ZM | 28.9k | 29–46 |
| LE | 17.2k | 17–27 |
| HE | 13.9k | 14–22 |

**Totals for the 13 roots without in-span files:**

- **Designated contracts:** BCOM holds about 5–7 designated months per root per year (to be confirmed by R-Q1). Over 2015-H2 → 2025-02 that is roughly 46–65 contracts per root.
- **Files:** about **600–850**, central ~725.
- **Disk:** about **25–55 GB**.
- **Wall time:** about **4–8 hours** of serial downloading, with one downloader only (memory note).
- **Money:** $0 marginal.
- **CL and NG** need nothing new if BCOM's designated months are within the files already held (NG is F/H/K/N/U/X; CL is F/H/K/N/U/X from 2015 and all months from 2021). Check this against R-Q1.

**Unknowns to probe before relying on this route:**

1. **Sierra's historical depth before 2020 on non-energy roots.** Sierra had **no NG TAS before 2020-02-10** ("historical data file not available"). CL/NG outrights did reach 2015. Probe one early file per exchange group (for example GCG16, ZCH16, LEG16) before a bulk queue.
2. **Whether Package 3 serves COMEX and CBOT ag symbols.** CBOT (YM) and CME (MES) files exist; no COMEX file has been tried.
3. **The signing rule.** It is Sierra's own for about 29% of HO/RB window volume (r 0.875). Each new root needs its own known answer against the tbbo year (2025-09-11 → 2026-09-11 is on disk for all 15 roots). **For CL/NG that year is vault**, so their check waits for the post-vault trades after 2026-10-10, as AITODO plans.

### 3.6 Priced options, side by side

| need | route | cost | coverage | caveat |
|---|---|---|---|---|
| C0 signed window flow, 13 roots | Sierra 1-tick | $0; ~725 files, 25–55 GB, 4–8 h | ~5 months before each expiry | Sierra signing r ≈ 0.875 (HO/RB); depth before 2020 unverified |
| same | Databento `trades`, exact windows | **≈ $243** (all 15; ≈ $170 without CL/NG, unquoted split) | exchange flag | ~14,300 requests |
| same | Databento `trades`, padded windows | ≈ $471 | as above, plus R1 entry path | same |
| same | Databento `trades`, whole days | $2,886.79 (all 15, one quote per group) | full days | 99.6 GB billable |
| R1 January execution days only | Databento window / padded | ≈ $5.14 / $9.95 | 2016–2025, 50 days | needs the window history first |
| KE settlements plus definitions | Databento GLBX | **$0.00** now | 2010 → | the subscription's end date |
| ICE settlements proxy | Databento ohlcv-1d, outrights | **$24.17** | 2018-12-23 → | a close, not a settlement; nothing before 2018-12-23 |
| ICE true settlements | Databento statistics, outrights | $6,003 (5,051.41 + 951.66) | 2018-12-23 → | not viable |
| non-CME drift, all years | BCOM ER subindex levels (web) | free to view | index history | terms of use; owner's spec decision (§3.3 says settlements) |
| LME | Westmetall (free) / LME Portal (paid) | free / paid | cash and 3-month | not BCOM's prompt dates |

---

## 4. Gap register

In the style of the `docs/internal/AITODO.md` DATA GAPS REGISTER. The ids are local to this model (IR-).

| # | information | stage / test | status | cheapest route and cost |
|---|---|---|---|---|
| IR-G1 | non-CME component prices, **2015 → 2018-12-22**: Brent, gasoil, 4 ICE softs, 4 LME metals (31.49% of 2026 weight) | **Gate R0**, drift §4, net-flow §4.5 | **MISSING**. Every year is excluded under R0's 10% rule | BCOM single-commodity ER subindex levels (free web, terms to check; needs the owner's ruling that published `R_i` may stand in for settlements). Brent partly proxied by NYMEX BZ (on disk). Databento has nothing before 2018-12-23 |
| IR-G2 | ICE component prices, 2018-12-23 → present | R0, drift | **MISSING, priced** | Databento ohlcv-1d outrights **$24.17** (close, not settlement); statistics ≈ $6,003 (not viable) |
| IR-G3 | LME aluminium, zinc, nickel and lead at BCOM's prompt dates | R0, drift | **MISSING** (8.10% weight; not on Databento) | BCOM ER subindex levels (as IR-G1); Westmetall free cash and 3-month (approximate); LME Portal (paid) |
| IR-G4 | KE settlements and definitions (the designated contract, roll calendar) | drift, C0, R1 for KE | **MISSING, $0 now** | Databento GLBX `statistics` + `definition`, KE.FUT, 2010-06-06 → 2026-09-26: 0.92 + 1.27 GB, **$0.00** while the CME Standard subscription lasts. **Time-critical** |
| IR-G5 | designated-contract 1-minute bars (not the front month), 15 roots | R1, R2, C0 price slope | **ON DISK (raw), no fixture** | Build from `ohlcv-1m` ALL_SYMBOLS on disk with windowed ids (D520/D521). $0. KE has no fixture at all |
| IR-G6 | aggressor-signed settlement-window volume, **13 roots** (HO RB GC SI HG ZC ZS ZW KE ZL ZM LE HE), 2015-12 → 2025-02, every session (20-day trailing norm) | **Gate C0**, R1 flow | **MISSING** | (a) Sierra: $0, ~725 files, 25–55 GB, 4–8 h, signing r ≈ 0.875; (b) Databento `trades` in windows: **≈ $243** exact, ≈ $471 padded, $2,887 whole days |
| IR-G7 | aggressor-signed window flow, CL and NG | C0, R1 | **ON DISK (Sierra)**, known answer pending | CL/NG check against post-vault trades after 2026-10-10 (r < 0.8 voids that root). Confirm BCOM's designated CL/NG months are within the files held (R-Q1) |
| IR-G8 | settlement-window times with effective dates before 2026-09-21: GC SI HG, 6 grains, LE HE (11 roots) | **Gate C0**, R1 timing, unit test 12 | **MISSING**. `window_for` raises | Source CME SERs and market notices (free; shared with the ledger's R-Q5). Livestock's 30-second window cannot be resolved on 1-minute bars |
| IR-G9 | BCOM designated-contract schedule, roll BD and daily fractions, CIM determination dates, 2015–2027 | drift, C0's `Q_roll`, R1's φ_d | **TO SOURCE** (R-Q1; SOURCES.md) | BCOM methodology PDFs (public). Not a data purchase |
| IR-G10 | published sub-index or component returns for the 5 bp/month test | **Gate R0** | **MISSING** (only the latest monthly factsheet was seen) | BCOM ER subindex daily levels (as IR-G1), or archived monthly factsheets. S&P GSCI single-commodity indices use a different roll, so they are not a match |
| IR-G11 | exchange-flag known answer for Sierra's signing on each non-energy root | validates the IR-G6 (a) route | **ON DISK** (tbbo 2025-09-11 → 2026-09-11, all instruments) | $0. Extend `check_sierra_aggressor.py` per root. The CL/NG part of tbbo is vault and unusable |
| IR-G12 | resting depth at t0 for H-R4 (§5A.4) | H-R4 | **MISSING** outside 2026-08-11 → 09-10 (MBO for CL and GC only among the 15) | R-Q11; the ledger quoted CL+NG MBO windows at ≈ $916 in-sample. Out of scope here |
| IR-G13 | forward recording of all BCOM component settlements (Track 2) | Track 2, the 2027 event | **NOT RUNNING**. `recorder/jobs.json` has no BCOM job | Add a recorder job. The ICE and LME sources are the same open question as IR-G1 to IR-G3 |

### 4.1 The top blockers

**Gate R0:**

1. **Non-CME prices (IR-G1 to IR-G3).** They are 31.5% of weight and nothing is on disk. Databento's ICE history starts 2018-12-23 and there is no LME at all, so every year fails the 10% rule until a route is chosen. The cheapest full fix is published BCOM sub-index levels, which needs an owner ruling.
2. **Methodology facts (IR-G9) and the published comparison series (IR-G10).** Without the designated-month schedule and the CIM dates, `R_i(t)` cannot be reconstructed. Without a published series, R0's 5 bp test has nothing to compare against.
3. **KE (IR-G4).** It is the only CME root with no settlements on disk. The fix costs $0 today but is time-critical: it depends on the subscription.

**Gate C0:**

1. **Signed window flow for 13 of 15 roots (IR-G6).** It is absent across the whole 2016 → 2025-02 span. The choice is Sierra (free, hours, signing r ≈ 0.875) or Databento (≈ $243–471 for windows).
2. **Settlement-window history (IR-G8).** 11 of 15 roots have no sourced window before 2026-09-21, and `window_for` raises by design. So `S_win` cannot even be defined for metals, grains and livestock.
3. **Signing validity (IR-G7, IR-G11).** Sierra's signing of spread-leg volume is its own rule, not the exchange flag. CL/NG await their known answer after 2026-10-10. Each other root needs one against the tbbo year before its flow is trusted. Sierra's history before 2020 for non-energy roots is also unverified.
