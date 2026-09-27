# D638 — LETF close-flow Phase 2, NQ: bars, calendar, event flags and the data QA. Every bar the model reads is present

*2026-09-27. The principal: "Accept the estimate, transcribe the pre-2019 filings, start NQ Phase 2". Spec:
`LETF_CLOSE_FLOW_PREREG.md` v1.2 §3.3, §3.4 and §9 Phase 2 ("Data QA report: bar coverage, excluded dates"), with
LETF-A1..A5. No return of any kind was computed. Every read is cut at 2025-03-01 (A10): the four catalogued panels
through `load_panel`, the two new fixtures by the same D594 layers by hand (filter, then assert), all recorded in the
QA's `reads` block.*

Reproduce:
- `python scripts/build_fut_micro_day_volume.py` (system python, 2.4 min, 6 processes) →
  `data/fixtures/fut_micro_day_volume.csv.gz` (MNQ and MES, 2019-05-05 →);
- `python scripts/build_fut_index_anchor_bars.py` (3.2 min, 5.50× on 6 workers) →
  `data/fixtures/fut_index_anchor_bars.csv.gz` (the 09:45 and 15:59 bars of every listed ES and NQ month);
- `uv run python scripts/build_letf_phase2.py --root NQ` → `data/letf/phase2_NQ_sessions.csv.gz` and
  `data/letf/phase2_NQ_qa.json`.

Both new fixtures reuse `build_fut_index_1m.py`'s own pass (windowed ids, D520; calendar ET day; D462's front rule).

## The sessions table, 2016-01-04 → 2025-02-28

| | count |
|---|---:|
| NQ sessions (D462 fixture) | 2,362 |
| EXCLUDED: CME session on a day the NYSE was closed (no NAV, no rebalance) | 59 |
| EXCLUDED: NYSE half-day (13:00 close; §3.4) | 18 |
| **usable sessions** (= the 2,303 NYSE days less the 18 half-days) | **2,285** |

- **Bars:** every usable session has 390 bars, except the four March 2020 circuit-breaker sessions (2020-03-09, 12,
  16, 18: 376–377 bars, one 14–15 minute morning halt each). They are kept, since the halts sit outside every model
  window.
- **Coverage of what the model reads:** 100% of sessions have every bar 10:59–11:59 (H4's placebo window) and every
  bar 14:29–15:59 (the three entries and the exit).
- **The prior close, t−1** (§4.1: r = P(t, τ) / P(t−1, close) − 1, within ONE contract):
  - t−1 is the prior NYSE trading day, priced at its NYSE close: the 15:59 bar (ending 16:00), or the 12:59 bar on
    a half-day (18 sessions).
  - Today's contract throughout: the front's own bar when t−1 had the same front, and on the 36 roll days the new
    contract's own 15:59 bar from the every-month anchor bars.
  - **Missing: none.**
  - Known answer: on 2,322 non-roll days the anchor bar equals the fixture's prior 16:00 price exactly (max |diff| 0).
- **H5's next 09:45 open,** same contract: present on 99.91%. It is missing after 2020-03-06 and 2020-03-11 (the next
  sessions opened into circuit-breaker halts) and on 2025-02-28 (the next session is in the vault).
- **NQ-equivalent volume = NQ + MNQ/10** (§4.4), both front months by full-day volume. MNQ trades from 2019-05-06 and
  is zero before its listing. Its share of the NQ-equivalent grows from 2.8% (2019) to 11–18% (2020–2024) and 21.6%
  (2025).

## Event flags (§3.4: flagged, not excluded)

| flag | sessions flagged, 2016-01-04 → 2025-02-28 | source |
|---|---:|---|
| FOMC | 77 | D585/D589 calendar |
| CPI | 108 | D585/D589 |
| quad witching | 36 | D589 |
| quarter-end | 36 | D589 |
| month-end | 110 | D589 |
| Nasdaq-100 rebalance | 37 | the quarterly third Fridays (all 36 coincide with quad witching) plus the special rebalance traded at the close of 2023-07-21 (Nasdaq press release, 2023-07-07; only 1998 and 2011 before it) |
| DST transition week | 90 | D589. Every one opens at 09:30 ET, so there is no one-hour shift |

## A fact found on the way: CME's NQ settlement is not the 16:00 price

A first draft priced roll days with CME's settlement of the new contract. Measured against the 15:59 bar close of the
same contract on the same day (2,306 sessions), **the settlement equals it on 2.4% of days, and is within one tick on
7.1%**. The median gap is 4–80 ticks in every month from 2016 to 2025; p99 is 181 ticks and the maximum 427.
Settlements were dropped as a substitute; the every-month anchor bars replaced them. The measurement stays in the QA
as a fact for any study that reaches for settlements as a close.

## What follows

- **Phase 3 (model functions and the nine unit tests, §8)** can run on this table for NQ: flow, contract conversion,
  V and σ_d with their look-ahead tests, impact, activation.
- **ES waits** for the pre-2019 Direxion anchors (LETF-A5). Its Phase 2 is the same builder with `--root ES`; the
  micro and anchor fixtures already carry MES and every ES month.
