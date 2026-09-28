# Opening agent-state model: amendments beside the read-only deposit

*The spec is `docs/internal/User-Doc-Deposit/OPENING_AGENT_STATE_PREREG.md` v1.1, which stays read-only (its §0.2:
"changes are additive, versioned amendments made before code changes"). The agreed changes live here, each with its
source. Opened 2026-09-28 on the principal's word ("Open it").*

## OA-A1. The programme split applies (A10)

*Source: the programme rule A10 (the principal, 2026-09-26), and the deposit's own §12A.1, which fixes the same vault.*

- **In-sample:** 2016-01-04 → 2025-02-28 (§12A.1's 2016-01-01, starting at the first usable ES/NQ day session, D462
  G5).
- **Vault:** 2025-03-01 → 2026-09-18, scored only in the programme's joint vault run.
- **Forward:** from 2026-09-19 (Track 2 recorder; Track 3 as §12 specifies).
- Every bar, option, calendar, ETF or trade read uses `reserved_from="2025-03-01"` (§13 phase 0b, test 18).
- **Output paths follow D592's translation:** the deposit's `results/opening/` becomes `docs/results/` (pages, including
  `POWER.md` as `OPENING_AGENT_STATE_POWER.md`) and `data/opening/` (state: `trials.csv` through
  `validation.programme.TrialsCsv`, `FROZEN_VAULT.json`, `SOURCES.md`). The deposit's `results/PROGRAMME_REGISTRY.md`
  is D592's `data/programme_registry.json`, where **"opening H-O2" already holds slot 7** (registered 2026-09-21).

## OA-A2 – OA-A5. The opening rulings

*Source: the principal, 2026-09-28, answering the four questions put at the opening (OQ-A … OQ-D below).*

- **OA-A2 (prior reads, O-Q6): run as written, disclosed.** Every result states the prior reads listed under the
  opening facts (D531, D463, D581, D614, the MACD arm) and reports B1–B3 beside the policy, which the deposit already
  does (H-O2 is judged against the best baseline). The list of earlier analyses that touched the vault on ES/NQ is
  compiled from the decision records before the joint vault run.
- **OA-A3 (A7, stage S-B): Sierra Chart tick data, one contract at a time.** Sierra Chart carries the exchange's
  aggressor side (proven on HO/RB against Databento, D624: B/A match the exchange flag exactly; spread legs carry no
  side). Each ES/NQ contract is downloaded, reduced to the §4 A7 quantity per session (large-lot signed flow, with
  the prior-20-day 90th-percentile threshold), and only the reduction is kept for modelling.
  - **The disk, measured 2026-09-28.** One ES contract (ESH19) is 1.83 GB (45.9 M tick records, 2018-09-27 →
    2019-03-15), so the 74 contracts are ~150 GB raw against ~137 GB free, and the 2026-10-09 top-up needs 90 GB.
  - **No file is deleted.** Each finished file is compressed in place by NTFS (`compact /c /exe:lzx`): lossless and
    transparent, with the SHA-256 checked unchanged. ESH19 measured 3.8 : 1 (0.48 GB stored), so the pull should
    occupy ~40 GB.
  - `scripts/sierra_index_tick_download.py` does one contract at a time:
    - download;
    - the cut-short check against the third Friday;
    - hash, compress, re-hash;
    - record it in `data/opening/sierra_index_tick_record.json`;
    - stop below 95 GB free.
  - Projected at ~14–18 h, serial on Sierra's side.
  - Before A7 is admitted, Sierra's side is checked against the exchange flag on ES/NQ, as D624 did on HO/RB.
    **The known answer is the free post-vault `trades` from 2026-09-19** against the same days in Sierra.
- **OA-A4 (A6, stage S-G): Alpha Vantage 1-minute SPY and QQQ**, 2015-10 → 2026-09 (warm-up, in-sample, and the vault
  months downloaded and not read), through `scripts/fetch_opening_etf_1min.py`. The deposit names Databento equities;
  this is the substitute source, recorded in `data/opening/SOURCES.md`. Alpha Vantage prints a bar only in a minute
  with a trade, which for SPY and QQQ at 09:30 and 15:59 should be every day; Gate O0 checks it.
- **OA-A5 (costs at the open, O-Q5): D508's default line + one adverse tick**, as for LETF and the shock classifier
  (MES, MNQ; $3 commission), with the deposit's 2× cost robustness. The 09:30 → 10:05 spread is measured on
  post-vault sessions (free `trades`/`tbbo` from 2026-09-19) before any book result is trusted.

## OA-A6 (RULED 2026-09-28: the principal, "Confirm OA-A6", before any label was computed). The readings §5 and Gate O0 need

*The deposit fixes the label rules (§5.3) but not the prices they are read from. These are the readings, written
before the Phase 1 labels are computed. Each follows an existing repository convention where one exists.*

1. **Prices.**
   - **RTH open** is the open of the 09:30 bar.
   - **Close** is the close of the 15:59 bar (the 16:00 print, D462).
   - **Prior close** is the prior session's 15:59 close, *not* the CME settlement: the settlement differs from the
     16:00 close on most days (memory: CME index settlement is not the 16:00 close), and §4 A1 says "prior RTH
     high/low/close".
   - `gap = open − prior close`.
2. **ATR20.**
   - True range is taken on RTH daily bars: RTH high and low, and the prior RTH close.
   - It is the simple mean over the **20 sessions before** the current one, so it is known at the open. The same
     ATR20 serves the gap feature, A1 and the FADE label.
3. **IB** is the high − low of the 09:30–10:29 bars. **R** is the RTH (09:30–15:59) high − low.
4. **Price at t0** is the close of the bar ending at t0 (the 09:44 bar for t0 = 09:45).
5. **FADE's "trades through ≥ 75% of the gap towards the prior close by 16:00"**:
   - for gap > 0, the RTH low ≤ open − 0.75 × gap;
   - for gap < 0, the RTH high ≥ open + 0.75 × |gap|;
   - read over all RTH bars.
6. **Labels are per (session, t0),** because d0 depends on t0. CONT and REV can differ between 09:45 and 10:00 on a
   day whose opening direction flips. The label-frequency report is given at both, and 10:00 is H-O1's.
7. **The 8% merge rule (O-D4):**
   - frequencies are pooled over the in-sample per market;
   - a class below 8% in **either** market is merged into RANGE for **both**, because the classifier's
     coefficients are shared (§7.1).
8. **Exclusions** (logged):
   - D589's early-close sessions;
   - sessions whose 09:30 bar is missing, or with fewer than 90% of their 09:30 → t0 bars (the three March 2020
     circuit-breaker opens, D462).
9. **Gate O0's coverage** is ≥ 99% of the 480 expected minutes 08:00–15:59 ET, per market, on usable sessions (as
   SC-A6: NYSE trading days that are not half days). Its literal minute count is reported beside it.
10. **"SPY alignment verified"** means:
    - SPY's and QQQ's 09:30 and 15:59 bars are present on ≥ 99% of usable sessions;
    - Alpha Vantage's clock is US/Eastern: the median correlation of 1-minute returns with ES (SPY) and NQ (QQQ),
      09:31–15:59, is ≥ 0.9 at lag 0 and higher than at ±1 minute.

## Opening facts (2026-09-28, before any rule is applied or any price read for this model)

### The data the deposit names, against what is on disk

| §3 input | on disk | what it means |
|---|---|---|
| ES, NQ 1-min bars, full Globex | the `ohlcv-1m` archive, every instrument, 2010-06-06 → 2026-09-10 (raw). The committed ES/NQ fixtures are day-session only: `fut_{ES,NQ}_rth_1m` (D462, 09:30–15:59) and `fut_day1m` (09:00–15:59) | Gate O0's 08:00–16:00 coverage, the overnight high/low (A1) and A5's 08:29 → 09:25 need a new build from the raw archive with D520's windowed ids and D462's front-contract rule. Usable from 2016-01-04 (D462 G5). The three March 2020 circuit-breaker sessions (09, 12, 16) have no continuous open |
| ES, NQ trades with aggressor side | `tbbo` 2025-09-11 → 2026-09-11 only (all inside the vault), and `trades` from 2026-09-19 (free, forward). **Under the CME Standard subscription, `trades` history is served only for the last 12 months** (`fetch_ledger_free.py`'s header) | **No in-sample aggressor trades from Databento.** A7 (S-B, large-lot signed flow) cannot be built from what is on disk. See question OQ-B |
| SPY 1-min (and QQQ) | **none**: `index_extended_15m_raw` is 15-minute; no SPY/QQQ under `data/raw/alphavantage/1min/` | A6 (S-G) cannot be built from what is on disk. See question OQ-C |
| ES/NQ options OI by strike, settlements | **ES:** `fut_es_options_eod.csv.gz` (D581/D616), 25 families, 2016-01-04 → 2026-09-09, OI as of the prior close keyed on the session it is usable. **NQ:** the raw `statistics` + `definition` pull landed today (4 jobs, 42.7 GB, verified), no fixture yet | Gate O0-H (≥ 90% of days) is buildable for both. **Implied vol** is not in the fixture: D581 already has an audited Black-76 route (settlement-implied vol, rate 0, gamma at a fixed clock), with the same positioning convention as §4 A4 (dealers long calls, short puts) |
| 08:30 ET releases | D585's sourced calendar: CPI and EMPSIT are the 08:30 releases (FOMC is 14:00; EIA is 10:30/10:00) | A5 is active on CPI and payrolls days only (~24 a year), because the deposit makes the calendar shared with the shock classifier's §3.4. Other 08:30 releases (GDP, retail sales, claims, PPI) are not in it and are not added |
| Session calendar | D589 (early closes, holidays, DST, roll days) | Covers §3's exclusions. The flags (quad witching, month-end, index rebalance days) are derived from it by rule |

### Prior reads on ES/NQ at the open and in the vault (the deposit's O-Q6, and the SC-A2 precedent)

The programme has already measured things this model's baselines and agents rest on. They are listed so that each
result can be read against them, not only against zero.

- **B3 (the opening-range breakout) is D531: it does not clear on any root**, and "loses to the base rate 48 of 48"
  (its addendum). The memory of this line: intraday continuation mechanisms are flat in the 0DTE era.
- **B1 (opening momentum) is close to D463** (intraday momentum a third of its published size on ES, not
  distinguishable from zero) and to the finding that price-path momentum fails at every horizon tested on futures.
- **A4 (dealer gamma) is close to D581:** the sign of carried dealer net gamma orders nothing in the ES close. D614:
  noon-0DTE pinning is real but not tradeable.
- **The prop book's only admitted strategy, the MACD day-session arm (Entry #2), trades the same session**, and
  conditioners on it are structurally unavailable (memory). A state policy is scored as a component against it
  (CLAUDE.md), and the correlation decides whether it adds anything.
- **The vault was touched on ES/NQ by earlier lines** (the deposit's own §12A.1 says the vault is "clean for *these
  hypotheses*, not a virgin dataset"). Among others: the MACD arm was scored 2016-01-04 → 2026-09-09 (D504), D485 read
  the whole `tbbo` year of ES/NQ micro flow, D617 read ES option flow in the same year, and D614 read ES 0DTE
  pinning. The full list is built from the decision records before the vault is opened (OQ-A).

### What the deposit leaves to the owner (its §18)

- **O-Q1 (CL extension):** after the v1 verdict, as the deposit's own §2 already puts it ("not built until v1
  verdict").
- **O-Q2 (options and SPY/QQQ coverage):** answered above for options (buildable). SPY/QQQ is OQ-C.
- **O-Q3 (Track 3 automation):** needed only if the model reaches Phase 8.
- **O-Q4 (calendar):** D585, shared (above).
- **O-Q5 (costs at the open):** OQ-D.
- **O-Q6 (prior vault exposure):** OQ-A.
