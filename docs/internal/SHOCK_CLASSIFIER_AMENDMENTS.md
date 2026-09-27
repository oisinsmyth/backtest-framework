# Shock classifier: amendments beside the read-only deposit

*The spec is `docs/internal/User-Doc-Deposit/SHOCK_CLASSIFIER_PREREG.md` v1.2, which stays read-only (its §0.2:
"agreed changes are made as a versioned edit … before code changes"). The agreed changes live here, each with its
source. Opened 2026-09-27 on the principal's word ("open the shock classifier").*

## SC-A1. The programme split applies (A10)

*Source: the programme rule A10 (the principal, 2026-09-26).*

- **In-sample:** 2016-01-04 → 2025-02-28 (the deposit's "2016-01-01 to latest", cut at the vault).
- **Vault:** 2025-03-01 → 2026-09-18, scored only in the programme's joint vault run.
- **Forward:** from 2026-09-19 (Track 2 recorder; Track 3 as the deposit specifies).
- Every bar, calendar or trade read uses `reserved_from="2025-03-01"`.
- **Output paths follow D592's translation:** the deposit's `results/shock_classifier/` becomes `docs/results/`
  (pages) and `data/shock/` (state, including `trials.csv` through `validation.programme.TrialsCsv`).

## Facts established at the opening (2026-09-27), recorded before any ruling

- **The prior reads of this ground, to be disclosed in every result:**
  - **D528** (2026-09-14/15): a 1-minute spike and excursion detector on 26 roots including ES, NQ, CL and GC. Its
    reversion was "real, and 4–8× too small" for the cost. Its addenda read the wide 5-minute fixture 2010 → 2026-04
    and the 1-minute quoted mid 2025-09 → 2026-04, before the programme's vault rule existed.
  - **D499:** the hour after a large move reverts in off-hours on the index roots, worth less than a tick.
  - **D526:** the index roots trend intraday on a bounce-free mid; the rates complex mean-reverts.
  - None of the three classified moves by cross-asset confirmation or by the release calendar. The deposit's
    classifier is new; the unconditional behaviour of large moves on these roots is not.
- **Bars:** `fut_day1m.parquet` (36 roots, one minute, front by full-day volume, 2010-06 → 2026-09) holds every traded
  and peer root on a **09:00–15:59 ET template**.
  - Inside each deposit window (with w = 3's lookback and the 60-minute hold), every usable session is 100%
    covered on all twelve roots: 10th percentile 1.0, 2016-01 → 2025-02.
  - The 2.2–3.3% of sessions below 99% hold no bars in the window at all: CME holiday and half-day sessions, which
    are not trading days for the model.
  - **The gap:** GC's window opens at **08:25**, before the template. GC, SI, 6E and ZN need 08:20 → 09:00 bars, which
    the on-disk minute archive holds (free, no pull).
- **Calendar:** `data/calendar/events.csv` (D585, sourced from BLS, the Fed and EIA with URLs) carries every event §3.4
  names, 2016 → 2026: CPI 131, EMPSIT 131, FOMC 85 plus 7 unscheduled, EIA WPSR 573, EIA NGSR 574.
- **Trades with aggressor side** (the INFO flow-flip exit, §5.3): `tbbo` spans 2025-09-11 → 2026-09-11 only, so there
  are none in-sample. Buying them is outside the principal's budget, which makes this the deposit's Q3.
- **Micros:** MNQ and MES from 2019-05, **MCL from 2021-07**, MGC throughout. Before MCL's listing, CL's micro-size
  line is hypothetical.
