# D628 — Option D's diagnosis: correcting the life cycle does not rescue the window line, NG's TAS link is too weak for the vault, and the settlement ledger STOPS with the vault unread

*2026-09-25. EXPLORATORY, on the in-sample D627 already spent. It admits nothing and changes no verdict: D627 FAILS
on both roots. The vault rule was committed in `ee4d59e` BEFORE this was run. The script is
`scripts/explore_h1a_lifecycle.py`, and its output `data/ledger_h1a_exploratory.json` reproduces byte for byte
under `--check`.*

## 1. Why this was run

D627 failed with negative slopes, and its dependent drifted: A_t was positive on 74–77% of days
([D627-RESULT](D627-RESULT-h1a-fails-with-negative-slopes-on-both-roots.md) §4.2). The principal chose to diagnose
before deciding (option D). The rule fixed beforehand:
- a line qualifies for the vault only if β > 0 and its vault power is ≥ 0.80 at HALF its exploratory effect;
- the vault has n = 390 business days;
- at that size the rule needs an exploratory t of about 12.7, with year fixed effects.

## 2. The correction

Each held contract on day t is compared with the previous 6 delivery months of the same root. Each of those is
taken on the day it stood at the same number of business days to its own expiry. All such days are earlier than t.

| | D627: days with A > 0 | corrected: days with A\* > 0 | median today/norm |
|---|---|---|---|
| CL | 77% | 64% | 1.19 |
| NG | 74% | 55% | 1.07 |

The drift is mostly removed for NG and halved for CL. The CL remainder is consistent with volume growing across
contracts over time, for example in era B's deferred months. It was not investigated further.

## 3. The lines, refitted (HC1 t; year fixed effects; NW in brackets)

| root | line | β (year FE) | t (year FE) | pooled t | rotation p95 | vault power at ½ effect |
|---|---|---|---|---|---|---|
| CL | window | −0.96 | −3.97 (−3.51) | −2.52 | 3.55 | 0 (β < 0) |
| CL | TAS | −1.78 | −3.71 (−3.39) | −3.52 | 3.28 | 0 (β < 0) |
| CL | window placebo | −0.86 | −2.03 (−1.94) | | | |
| NG | window | −0.11 | −2.30 (−1.69) | −0.52 | 2.98 | 0 (β < 0) |
| **NG** | **TAS** | **+1.28** | **+6.92 (+5.45)** | **+9.34** | **6.93** | **0.34** |
| NG | window placebo | −0.02 | −0.27 (−0.26) | | | |

## 4. What it shows

- **The negative window slope is not the drift artefact on CL.** It survives the correction (t −3.97), and the
  corrected placebo carries it too (t −2.03). On CL, larger predicted rebalances go with LESS abnormal volume both
  at 14:28 and at midday. It is a day-level association, not a settlement-window flow.
- **On NG, the correction flattens the window line** (pooled t −0.52). The fund rebalance leaves no visible
  footprint in NG's window volume.
- **NG's TAS volume does move with predicted rebalance size,** and it is the strongest line anywhere in the study:
  - β +1.28 (year FE), t 6.9, NW 5.45;
  - the placebo on NG is flat;
  - but the rotation null's p95 is 6.93, so the year-FE t sits exactly at the rotation bar. Much of the link is
    serial structure the rotation keeps, not day-by-day alignment;
  - at half its effect over 390 vault days, the power is 0.34. It does not qualify.
- **CL's TAS goes the wrong way** (t −3.7).

## 5. The decision (the rule's outcome)

**No line qualifies. The settlement flow ledger STOPS, as the deposit prescribes after a Gate 1 failure, and goes to
its write-up. The vault (2025-03-01 → 2026-09-18) stays unread.**

What stays true and reusable:
- Stage A's inputs:
  - the calendar;
  - the window-volume panel (window volume that is exact to the 1-minute fixture);
  - the P1 panel on Gate 0b's proven holdings;
  - the §7.2 gate;
  - the power harness and the A9 control, which is calibrated;
  - the ETF-premium bias check (the close is within about 1 bp of the mid).
- **The lead worth carrying:** NG's TAS volume rises with the leveraged funds' predicted rebalance. It is consistent
  with the funds executing at the settlement price through TAS rather than in the window. It is POST HOC and
  under-powered for the vault. Only data recorded forward, which the deposit's recorder (Phase 0) is built for,
  could test it.
- **D626** (the TAS price sign, read on 2026-10-10) is independent of this record and is unaffected.

## 6. Lessons, saved to memory

- An "abnormal" dependent on a rolling futures position inherits the contract's life cycle. Check its mean on the
  pre-sample, built exactly as the runner builds it
  (memory: `an-abnormal-volume-dependent-on-a-rolling-contract-drifts`).
- A day shuffle of an autocorrelated regressor is anti-conservative. Calibrate every control's size in the power
  simulation before the pre-registration (memory: `a-rotation-null-of-a-correlated-regressor-is-anti-conservative`).
