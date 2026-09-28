# D644 — the opening agent-state model's Gate O0 passes, and REV is below 8% in both markets, so it merges into RANGE by the deposit's own rule

*2026-09-28. The principal: "Open it" (the opening agent-state model), then "Confirm OA-A6". Phase 1 of
`OPENING_AGENT_STATE_PREREG.md` v1.1 (§13), under OA-A1 … OA-A6 (`docs/internal/OPENING_AGENT_STATE_AMENDMENTS.md`).
In-sample 2016-01-04 → 2025-02-28; nothing on or after 2025-03-01 was read. No forward return and no feature has been
computed. The labels read whole sessions, as §5.3 defines them, and are training targets only.*

## What was built

- **`data/fixtures/fut_opening_globex_1m.csv.gz`** (`scripts/build_fut_opening_1m.py`, 4.6 min on 6 workers at 94%;
  in the data manifest by hash):
  - ES and NQ at one minute, over each trading session's whole Globex span: the prior evening from 18:00 ET through
    16:59 ET;
  - on the session's front contract as D462 names it, with D520's windowed ids;
  - 2,440 sessions, 2015-09-01 → 2025-02-28, 3.33 M ES and 3.31 M NQ bars.
  - **Checked against D462 on 09:30–15:59:** the same 937,257 ES and 937,230 NQ bars, and every contract, close and
    volume identical.
- **`scripts/opening_gate0.py`** → `data/opening/gate0.json`, `data/opening/labels.csv` (0.8 min).
- **`src/backtest_framework/opening/labels.py`:** §5.3's rules under OA-A6, with the deposit's unit tests 1, 3 and 12
  plus ATR20's prior-only rule (`tests/unit/test_opening_labels.py`, 5 tests).
- SPY and QQQ at one minute from Alpha Vantage (OA-A4; 264 monthly slices, the vault months unread).

## Gate O0: PASS

| check | ES | NQ | bar |
|---|---:|---:|---|
| minutes 08:00–15:59 with a bar, on 2,285 usable sessions | 99.977% | 99.967% | ≥ 99% |
| SPY/QQQ 09:30 bar present | 99.96% | 99.96% | ≥ 99% |
| SPY/QQQ 15:59 bar present | 100% | 100% | ≥ 99% |
| median day's 1-min return correlation, lag 0 (lag −1 / +1) | 0.985 (−0.002 / −0.014) | 0.992 (+0.012 / +0.004) | ≥ 0.9, above ±1 |
| calendar sourced (D585, D589) | yes | yes | |

- **Usable sessions (OA-A6.9):** 2,285 NYSE days, less 18 half days.
- **Exclusions (OA-A6.8):** exactly the three circuit-breaker opens of March 2020 (03-09, 03-12, 03-16).
- **d0 = 0 (unclassified, §5.2)** at 10:00: ES 30 sessions, NQ 5. At a 0.25-point tick, ES is back at its open more
  often.
- **O0-H (S-H only):** ES options OI and settlements are there on 99.7% of usable sessions (pass). NQ is PENDING its
  fixture, from the raw pull that landed today.

## The label frequencies (§5.3, pooled in-sample)

| t0 | market | CONT | REV | FADE | RANGE | n |
|---|---|---:|---:|---:|---:|---:|
| 09:45 | ES | 16.6% | **7.6%** | 20.3% | 55.5% | 2,242 |
| 09:45 | NQ | 14.5% | **6.3%** | 21.8% | 57.5% | 2,273 |
| 10:00 | ES | 18.0% | **6.4%** | 20.1% | 55.6% | 2,252 |
| 10:00 | NQ | 15.2% | **5.6%** | 21.8% | 57.4% | 2,277 |

**REV is below 8% in both markets at both t0, so by O-D4 (read by OA-A6.7) it merges into RANGE.** The thresholds
are not tuned. By year, REV runs 3.6–9.0%; only ES 2022–2023 exceed 8% (8.8%, 9.0%), so the merge is not the
artefact of one period.

## What it means for the model

- **The classifier has three states, CONT, FADE and RANGE,** and the policy (§6.2) loses its "reverse" branch. A day
  that trends against its opening direction is a RANGE day to the model and is not traded.
- **The parameter budget stays at 11 features** (§7.3's ceiling is stated in features, not in classes), with two
  non-base classes.
- B2, the opening-reversal baseline, is untouched: §6.4's baselines are unconditioned.
- Trend days of either sign are a third or less of all days (CONT + REV ≈ 22–24%), and most days (55–57%) are RANGE.
  That is the base rate H-O1 must beat.

## Next

- Phase 2: agent pressures A1–A6 (A7 after the Sierra pull and its check against the exchange flag), their unit
  tests (deposit 4–11), and POWER (`docs/results/OPENING_AGENT_STATE_POWER.md`) before any stage runs.
- The NQ options fixture, for O0-H and S-H.
- Phase 0b's vault guard over the new inputs (deposit test 18).
