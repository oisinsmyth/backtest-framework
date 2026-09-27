# D641 — shock classifier Phase 2: the machinery is built and tested, and at z = 4 almost every one-minute shock moves its whole complex, so LIQ is 1–10% of shocks

*2026-09-28. The principal: "Go ahead with Phase 2". Spec: `SHOCK_CLASSIFIER_PREREG.md` v1.2 §4 and §10 Phase 2, with
SC-A1..A8 (`docs/internal/SHOCK_CLASSIFIER_AMENDMENTS.md`; A7 and A8 PROPOSED). **No forward return was read.** Every
quantity is computed from bars at or before each shock's own bar (deposit §0.7). In-sample 2016-01-04 → 2025-02-28 on
SC-A6's 2,282 usable sessions; nothing on or after 2025-03-01 is read.*

Reproduce:
- `uv run pytest tests/unit/test_shock_model.py` (the deposit's 13 tests, all claimed);
- `python scripts/build_shock_phase2.py` (4.4 min) → `data/shock/phase2_shocks.csv.gz` (every shock at z = 3, 4, 5)
  and `data/shock/phase2_counts.json`.

## What was built

`src/backtest_framework/shock/model.py` holds §4.1–§4.7 and the §5 pieces the unit tests name:
- σ_tod as a rolling 60-session median, shifted one day;
- the detector (w ∈ {1, 3}, the 60-minute cooldown, the shorter window winning);
- rolling peer β and ρ from per-day sums;
- the confirmation ratio (median over peers with |ρ| ≥ 0.3, at least two);
- the event window (release −1 → +5 minutes, inclusive);
- the classification with its event override;
- the trade direction, the stress fill, the pessimistic intra-bar exit;
- the window and roll-day eligibility, and ET → UTC.

**The deposit's 13 unit tests pass** (`tests/unit/test_shock_model.py`). Each look-ahead test shows day t's data cannot
reach day t's value, and that day t−1's can.

Prices come from `fut_day1m`'s front close, plus `fut_premarket_1m` for the gold complex before 09:00 (SC-A4). Peers
are forward-filled for at most 5 minutes within a session (SC-A6). The first run took 16.6 min, launched without the
stated projection CLAUDE.md asks for. One optimisation pass (numpy lookups, a binary-searched event window) brought it
to 4.4 min. The rewrite reproduces the first run exactly on NQ, CL and GC (every field of 33,711 rows). ES differs only
on the zero-scale minutes below.

**SC-A8 (found here):** in quiet ES regimes σ_tod can be exactly 0 (more than half the prior 60 sessions unchanged at
that minute), which made any one-tick move a "shock". 60 such ES minutes now cannot detect. That removed 37 of 3,911
ES shocks at z = 4.

## The counts (z = 4, both windows pooled, primary thresholds 0.6 / 0.2)

| | INFO | LIQ | NONE | all | per year | NONE for < 2 valid peers | event-flagged (INFO / NONE) |
|---|---:|---:|---:|---:|---:|---:|---|
| **NQ** | 3,048 (81.5%) | **85 (2.3%)** | 607 | 3,740 | 374 | 270 | 35 / 9 |
| **ES** | 3,425 (88.3%) | **51 (1.3%)** | 398 | 3,874 | 387 | 182 | 38 / 8 |
| **CL** | 3,163 (92.7%) | **40 (1.2%)** | 209 | 3,412 | 341 | 0 | 178 / 2 |
| **GC** | 2,035 (64.3%) | **304 (9.6%)** | 827 | 3,166 | 317 | 185 | 138 / 15 |
| **all four** | 11,671 | **480** | 2,041 | 14,192 | | | |

- **Shocks are two to three times as frequent as the deposit planned:** 317–387 a year per market, against its
  §7A figure of about 150.
- **The confirmation ratio sits at its "peers moved exactly by beta" value:** C has a median of 0.98 (ES), 0.99 (CL),
  1.02 (NQ) and 0.84 (GC), and an interquartile range of about 0.8–1.25 outside gold. A 4σ one-minute move in these
  markets is almost always a move of the whole complex. So INFO is nearly the unconditional set of shocks, and LIQ
  (peers did not move, no release) is rare: **480 in nine years across four markets, against the ~1,800 §7A's power
  plan assumed**.
- **Only gold has a LIQ class of any size** (304).
- **Window and sensitivity:**
  - 72–76% of shocks are one-minute moves (w = 1), the rest three-minute.
  - At z = 3 / 5 the per-market totals are 5,330–6,224 / 1,868–2,527.
  - The alternative thresholds move LIQ to 662 (0.5 / 0.3) or 336 (0.7 / 0.1). None changes the picture.
- **Shock sizes are real moves, not tick noise:** median 16 ticks (ES), 18 (CL), 20 (GC), 66 (NQ).
- **NONE for fewer than two valid peers:** mostly the index roots before RTY joins in 2017-07, when ZN's and 6J's
  |ρ| with the index is often under 0.3.

## What this means before any return is read

1. **H1 needs both classes in each market**, and LIQ has 40–85 shocks per market outside gold. §7A's power table
   assumed about 450 per market. **The POWER step (§7A, before Gate 1) will almost certainly label CL, ES and NQ
   underpowered on the LIQ side**, so their H1 verdicts would be inconclusive, not failed. Gold is the one market
   where the divergence test has two populated classes.
2. **INFO ≈ all shocks outside gold**, so SC-A2's unconditional baseline and the INFO class nearly coincide there. An
   INFO result on NQ, ES or CL is in effect a result about large moves as such, the ground D528 and D499 already
   covered.

**Phase 2's gate (all tests pass; counts reported) is met.** Phase 3 starts with the POWER step. SC-A7 and SC-A8 stand
as proposed until the principal rules.
