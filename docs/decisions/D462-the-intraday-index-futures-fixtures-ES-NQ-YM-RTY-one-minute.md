# D462 — the intraday index-futures fixtures: ES, NQ, YM, RTY at one minute, regular hours, front month by volume, from the CME archive, with the four acceptance gates

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D462-the-intraday-index-futures-fixtures-ES-NQ-YM-RTY-one-minute-regular-hours-front-by-volume-from-the-CME-archive-with-the-four-acceptance-gates.md`. The H1 above is the full title.*

**Pre-registration of a DATA-LAYER build. Committed before the builder exists (R8).** Result in a
separate file. **No study, no return, no candidate: fixtures and their gates only.** D462 taken
after `ls docs/decisions` and `git log --all` (both worktrees) showed D461 as the highest number.

## 0. Why

The prop track's three named candidates are closed on the right statistic (BOOK_PROP, 2026-09-11
amendment); the acquisition is complete and verified (129 files, 111 GB, 2010-06-06 → 2026-09-09,
now at `data/raw/databento/`, git-ignored); and the candidate the research lane rated the only
near-miss with a real mechanism — **market intraday momentum, the last 30 minutes** (lane 13,
C-13.1) — needs exactly one thing nobody publishes: **the path inside the window on one-minute
bars, on the futures themselves.** Every prior ES study here (D448–D451) built its own panel from
the raw archive for one question. This record builds the reusable fixtures once, gated, so that
the candidate's record (next) and any later one read a committed fixture and not 111 GB.

## 1. Source and scope, declared

- **Source:** `data/raw/databento/*/glbx-mdp3-*.ohlcv-1m.dbn.zst` — 26 files, the GLBX.MDP3
  one-minute OHLCV for every CME symbol, read with the system interpreter's `databento` (as D448/D449).
- **Roots:** **ES, NQ, YM** from 2010-06-06 and **RTY** from its CME listing (2017-07; the archive
  has no CME Russell outright before that — `ER2` had left for ICE in 2008). Outrights only:
  symbols matching `^(ES|NQ|YM|RTY)[FGHJKMNQUVXZ]\d{1,2}$`; no spreads, no micros (MES/MNQ are a
  separate fixture if ever needed).
- **Clock:** `ts_event` converted to US/Eastern with DST; a bar's timestamp is its **start**.
  **Regular hours = bars 09:30 through 15:59** inclusive (390 bars; the 15:59 bar's close is the
  16:00 print, D448's convention). Nothing else is kept in the fixture; the extended session was
  the subject of D448/D449 and is not this record's.
- **Front month per (root, day) = the outright with the highest total volume over the FULL day**
  (all sessions), measured, not a calendar rule — D448's definition. Every bar in the fixture is
  the front contract's; the contract is a column, so a study can drop any pair of days whose
  contracts differ. **No stitching, no back-adjustment**: an intraday return takes both endpoints
  from the same contract on the same day by construction, and a cross-day return is the study's
  responsibility to guard (as D448 did).

## 2. Outputs

- `data/fixtures/fut_{ROOT}_rth_1m.csv.gz` per root: `day, hhmm, contract, open, high, low,
  close, volume` (prices in points; `PX = 1e-9` from the DBN fixed-point). ≈ 1.6 M rows for ES,
  NQ, YM; ≈ 0.9 M for RTY; **committed** (the repo's fixtures are csv.gz; ~20–30 MB each).
- `data/fixtures/fut_index_sessions.csv.gz`: one row per (root, day): `contract, bars, p0930
  (open of the 09:30 bar), p1600 (close of the 15:59 bar), rth_volume, day_volume, roll (the
  contract changed from the previous session)`.
- `data/fixtures/fut_index_rolls.csv.gz`: every front-month change with the day, the two
  contracts, and the two contracts' volumes on that day.
- `data/fixtures/fut_index_1m.meta.json`: provenance (files read, rows in, rows kept per root),
  the gate results, and the anomaly list.

## 3. The four acceptance gates (the purchase proposal's §12, mandatory before any study reads this)

- **G1 — no unexplained bar.** Every one-minute close-to-close move with |r| > **1.0%** on ES, NQ,
  YM or > **1.5%** on RTY is **listed with its day and minute**; the list must be short (declared:
  **≤ 40 bars per root over the whole span**) and every bar on it must fall on a day the record
  can name (2015-08-24, 2018-02-05, the March-2020 sessions, 2022-01-24, 2024-08-05 …). A move
  that is not on such a day is investigated before the fixture is committed. (The 2010-05-06
  flash crash predates the archive.)
- **G2 — rolls at volume crossover, never reverting.** Per root, every front-month change is
  forward in the contract cycle (H → M → U → Z → H…), there is **exactly one** change per
  quarterly cycle, no change reverts, and the change falls in the **expiry week or the two weeks
  before it** (the quarterly third Friday); the day-count distribution of "days before expiry"
  is printed.
- **G3 — session coverage.** Bars per regular-hours day: **p50 = 390**, days below 380 are listed
  and must be **early-close days** (the day after Thanksgiving, Christmas Eve, July 3 — 210 bars)
  or documented outages; no other systematic hole (every `hhmm` from 09:30 to 15:59 present on
  ≥ 99% of full days).
- **G4 — independent cross-check.** Against the repo's own equity 15-minute fixture
  (`index_extended_15m_raw`: SPY, QQQ, DIA, IWM): on matched days, the correlation of
  **open-to-close** (09:30 open → 16:00 close) returns **≥ 0.995** for ES/SPY, NQ/QQQ, YM/DIA, and
  ≥ 0.99 for RTY/IWM; and of **close-to-close** on same-contract day pairs ≥ 0.99. D448 measured
  ES/SPY RTH at 0.9996; a fixture that does not reproduce that is wrong, not different.

**A gate that fails stops the commit.** The RESULT reports every gate's number whether it passed
or not.

## 4. Predictions (LOW stakes — a data build — but written so the build is checkable)

- **X-a** rows kept: ES ≈ 1.55–1.65 M, NQ and YM the same, RTY ≈ 0.85–0.95 M; ≈ 4,080 sessions
  for ES/NQ/YM and ≈ 2,300 for RTY.
- **X-b** G1 lists **5–30** bars per root, concentrated in 2015-08, 2018-02, 2020-03 and 2024-08;
  none unexplained.
- **X-c** G2: **65 rolls** on ES/NQ/YM (16.3 years × 4), **36–37** on RTY; the modal roll is
  **7–9 trading days before expiry**; zero reversions.
- **X-d** G3: p50 = 390; the sub-380 list is 3 early closes a year (≈ 48) plus **≤ 5** other days.
- **X-e** G4: ES/SPY open-to-close ≥ 0.999; NQ/QQQ ≥ 0.998; YM/DIA ≥ 0.998; RTY/IWM ≥ 0.995.
- **X-f** build time under 40 minutes on the 26 files, reading each in 10-million-row chunks.

## 5. Not in scope

Any study; the extended session; micros; the other 37 roots; stitching or adjustment of any kind
(the stitcher `futures_continuous.py` exists for cross-day studies and is not invoked here).

## 6. Files

This record · `scripts/build_fut_index_1m.py` (`--build`, `--gates`, `--selftest`) · the fixtures
in §2 · RESULT.

---

## ADDENDUM, 2026-09-12, after the build and before any fixture is committed — a fifth gate, a usable window, and RTY held back

**What the build found that the four gates could not see.** ES, NQ and YM have **3,626 sessions
against ~4,080 trading days**: 555 days are absent, almost all Tuesday–Friday, almost all before
2016 (coverage 21% in 2010, 27% in 2011, 42% in 2012, 82–88% in 2013–2015, ≥ 97.6% from 2016). On
the absent days the archive carries the contract's **evening bars only** (2010-06-08: 189 ES bars,
all 18:00–20:32 ET, zero in regular hours) while Treasuries and currencies carry full days — the
early GLBX history lacks the index futures' day session on most days, which is a property of the
vendor's reconstruction, not of the parse (mappings are one interval per contract; the definition
schema agrees). **G3 counted bars per *present* session and so could not see a missing session**
— the gate was mis-specified, and the 4,080-session prediction (X-a) was wrong by 450.

**G5, added:** sessions against the equity fixture's calendar, per year; **usable start** = the
first year from which every later year has ≥ 97% of the calendar's days as full sessions. The
fixtures keep every bar the archive has; `fut_index_1m.meta.json` declares the usable window
and **no study reads a day before it.** Expected: ES/NQ/YM from **2016-01-04**, RTY from its listing.

**RTY's G4 fails as written** (open-to-close correlation with IWM 0.9899 against a 0.99 bar; the
close-to-close leg passes at 0.9982). The whole shortfall is **2020-03-16**, the limit-down open
(ES's own worst day on the same test is that day, at 4.2 points of difference); excluding it the
correlation is 0.9993. **The gate stands as pre-registered: the RTY bar fixture is not committed**,
and D463 runs on ES, NQ and YM. A documented-event exemption for G4 would be a spec change made
after seeing the number, and it is not made.
