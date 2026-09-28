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

## SC-A2 – SC-A5. The opening rulings

*Source: the principal, 2026-09-27, answering the four questions put at the opening.*

- **SC-A2 (prior reads): run as written, disclosed.** The in-sample is 2016-01 → 2025-02. Every result states the
  prior reads of D528, D499 and D526, and reports the **unconditional large-move baseline** (all shocks, unclassified)
  beside each class. So the classifier is judged against what is already known about large moves on these roots,
  not against zero.
- **SC-A3 (deposit Q3): bars-only v1.** In the book frame, the INFO class exits on the time stop in place of the
  flow-flip. The flow-flip is recorded forward (Track 2) from the 2025-09 → aggressor trades and tested there.
- **SC-A4 (build):**
  - GC, SI, 6E and ZN get 08:00 → 08:59 ET one-minute bars from the on-disk archive, with the same windowed-id labelling
    (D520) and the front contract `fut_day1m` already names for that (root, day).
  - CL trades are charged the MCL micro cost line for the whole sample, flagged "before MCL listed" for 2016-01 →
    2021-06.
- **SC-A5 (deposit Q1, Q2):** as for LETF.
  - Costs: the repo's default D508 line for MNQ, MES, MCL and MGC.
  - Prop limits: D386's fourteen plans through D440's `simulate_provider`.

## SC-A6. Gate 0's coverage bar, read on usable sessions

*Source: the principal, 2026-09-27 ("Define usable, re-run"), on Gate 0's literal G1 failure (`775f215`). Written
before any price is read.*

- **A usable session** is an NYSE trading day that is not a half day (the ES calendar's early closes). CME's
  holiday sessions, when the NYSE is closed, are not trading days for the model.
  - **Archive-outage days are excluded and logged:** NYSE days on which at least four of the nine non-equity roots
    have no bar in their window. In 2016-01 → 2025-02 the rule finds 2020-02-27, 2020-02-28 and 2020-06-30, the holes
    the settlement strip also has.
  - The same usable set feeds shock detection, the time-of-day volatility, the peer betas and every test.
- **The 99% bar applies to the four TRADED markets** (NQ, ES, CL, GC), on their bars in their windows.
- **A peer needs a PRICE at each minute: its last trade no more than 5 minutes old** (forward-filled within the
  session), on at least 99% of window minutes. Its literal bar coverage is reported beside it. A thin market prints
  no bar in a minute with no trade, and the price has not moved in that minute.
- **RTY is a peer from 2017-07-10**, when the fixture begins it. Before that NQ and ES have three peers, above the
  deposit's minimum of two.

## SC-A7 (RULED 2026-09-28: the principal, "confirm SC-A7 and SC-A8"). Two readings of §3.4 that Phase 2 needed

- **EIA natural-gas storage is a diagnostic flag on CL, not part of the classifying event flag.** §3.4 marks it "CL
  (weak), diagnostic". Each CL shock carries `event_ngsr_diag` beside the event flag and it is reported, but it
  does not enter §4.6.
- **The Fed's unscheduled FOMC statements count as FOMC statements** (7 in 2019–2025 in D585's calendar), for all
  four markets.

## SC-A8 (RULED 2026-09-28, with SC-A7). A zero time-of-day scale cannot detect

- **The defect.** §4.1's σ_tod is 1.4826 × the median of |r_1m| over 60 prior sessions. In a quiet regime more than
  half of those sessions can show no change at a given minute, so the median is 0 and §4.2's threshold is 0. Any
  one-tick move is then a "shock": 39 of 3,911 ES shocks in Phase 2's first run.
- **The rule.** A minute whose σ_tod is 0 does not detect, and the count of such minutes is reported per market.
  The formula is otherwise unchanged. No forward return had been read when this was found.

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
