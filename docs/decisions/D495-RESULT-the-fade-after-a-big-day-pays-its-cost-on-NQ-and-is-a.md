# D495 RESULT — the fade after a big day pays its cost on NQ and is a PICK, not a concentration: most of it is the day session's drift after any down day; the RSI(2) cells are flat

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D495-RESULT-the-fade-after-a-big-day-pays-its-cost-on-NQ-and-is-a-PICK-not-a-concentration-most-of-it-is-the-day-session-drift-after-any-down-day-the-RSI-2-cells-are-flat.md`. The H1 above is the full title.*

**Result of the pre-registered stage 0 in D495.** Runner `scripts/run_d495_daily_state_stage0.py`
(`--selftest` passes; `--run` 0.1 min), artefact `data/d495_daily_state_stage0.json`, trade files
per root and cell. ES and NQ, 1,993 full sessions each, **2016-01-04 → 2023-12-29; 2024+ unread.**

**Verdict under the declared rule: one PICK (NQ cell A long), seven closed, nothing PROCEEDS.**
The family maximum of the difference-between-sides z has p95 +2.45; the best observed cell is
+0.89, and 72% of common rotation offsets beat it.

## 0. The numbers

| one micro, 09:30 open + tick → 15:59 close | trades (share) | gross $/trade | bp (SE) | other side, bp | diff z | hit | MAE p50 / p95 / worst | net Sharpe (SE) | N1 rotation p95 | verdict |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---|
| **NQ A long** (after a top-decile DOWN day) | 110 (5.5%) | **+42.61** | +21.9 (14.5) | **+10.2** (n 761) | +0.78 | 56.4% | −152 / −641 / −1,144 | **+0.47 (0.25)** | +21.1 ✓ | **PICK** |
| NQ A short (after a top-decile UP day) | 85 (4.3%) | +23.56 | +16.8 (16.5) | +1.9 (n 976) | +0.89 | 49.4% | −118 / −542 / −854 | +0.21 (0.37) | +14.4 ✓ | closed (Sharpe) |
| ES A long | 105 | +7.57 | +9.5 (12.8) | +4.3 | +0.39 | 52.4% | −129 / −499 / −576 | +0.08 | +15.6 | closed |
| ES A short | 83 | +8.46 | +9.7 (13.7) | −1.6 | +0.81 | 49.4% | −76 / −386 / −585 | +0.09 | +11.5 | closed |
| NQ B long (RSI(2) ≤ 10) | 176 (8.8%) | +9.11 | +4.5 (10.9) | +4.9 | −0.04 | 50.6% | −135 / −656 / −1,002 | +0.09 | +16.6 | closed |
| NQ B short (RSI(2) ≥ 90) | 372 (18.7%) | −4.41 | −2.0 (4.1) | −4.9 | +0.56 | 43.3% | | −0.28 | +4.1 | closed |
| ES B long / short | 187 / 357 | +3.14 / −2.65 | +1.6 / −0.5 | +3.6 / −3.6 | −0.20 / +0.83 | | | +0.00 / −0.38 | | closed |

No cell has a day below −2% of a $50k account at one micro.

## 1. What the pick is, read honestly

**The cost is not the problem for the first time in this family.** NQ after a top-decile down day,
long the next day session: +$42.61 gross a trade against $3, hit 56%, median +$34.50, the
1%-trimmed mean +$33.72, sign positive in 6 of 8 years and in both sub-periods (+19.3 bp in
2016–2020, +25.9 in 2021–2023), net Sharpe +0.47 at one MNQ. It clears its own rotation null
(+21.1 p95). D487's −24.5 bp reproduces as a trade (+19.7 bp pooled over both sides).

**The sample is the problem, and so is what the "other side" says.** 110 trades in eight years
give a standard error of 14.5 bp on a 21.9 bp mean. And the days the state did *not* fire but the
same fade rule would have gone long — the day session after **any** down day on NQ — earned
**+10.2 bp on 761 days**. The top-decile concentration adds about 12 bp on top of that at z
+0.78, which is what the family null refuses (p95 +2.45, p50 +1.24). **Most of the pick is the
day session's drift after a down day, not a big-day effect.** ES says the same at half the size
(+9.5 against +4.3).

**The short side is not there.** After top-decile up days NQ's next session is +16.8 bp on 85
trades with a −$3.00 median and a Sharpe of +0.21; the RSI(2) shorts lose on both roots (the
index drifts up against them, −4.9 bp on the other side). **The RSI(2) longs are the
unconditional drift** (NQ +4.5 against an other side of +4.9; z −0.04).

## 2. Predictions

| | predicted | observed | |
|---|---|---|---|
| X-a A ≈ 10%; B long 8–14%, short 8–14% | | 9.8%; 8.8%, **18.7%** | shorts fire twice as often (RSI(2) ≥ 90 is common on a drifting index) |
| X-b NQ A +15–30 bp, hit 53–58%, clears N1, **z 2.0–2.8**, Sharpe 0.3–0.6; ES 0–12 inside N1 | | +19.7; 56%; cleared; **z 0.78**; +0.47; ES +9.6 inside | everything right except the z: the other side was not near zero |
| X-c B long +5–20, short −5–+5; NQ > ES; neither clears | | +4.5 / +1.6; −2.0 / −0.5; right; right | long side under the range |
| X-d MAE median −50–80 bp, p95 −180–260; none below −2% | | ≈ −60 / ≈ −250 bp on NQ; 0 | right |
| X-e NQ A long sign in ≥ 6 of 8 years and both sub-periods | | 6 of 8; both | right |
| X-f other side within ±3 bp on cell A | | **+10.2** (NQ long), +4.3 (ES long) | **wrong**, and it is the finding |

## 3. What this leaves

- **NQ cell A long is a PICK by the declared rule**: cleared its own null and the Sharpe bar,
  failed the family bar. It does not proceed to a construction record without the principal's
  word, and the honest forward test (2024+, about 70 fire days at +20 bp against a 150 bp σ per
  trade, ≈ 1.1 SE) is weak for it alone.
- **The observation the record owes, flagged as post hoc:** the "other side" of cell A — long
  NQ's day session after *any* down day — is +10.2 bp on 761 days (SE ≈ 5.5, ≈ 1.9 SE) at one
  MNQ. As a component it would trade 38% of sessions at a mean near $20 gross a trade; on the
  numbers here its net Sharpe would be in the region of 0.5. **It was not declared and is not
  scored**; it is the natural single declared cell for a next record, with the family bar then
  being its own rotation null, and 2024+ still clean for it.
- **The two cells that were declared as the reversion states are, on this data, the drift.**
  Cell B is closed on both roots; cell A's short side is closed.

## 4. Files

Runner · four trade files · the artefact · this record.
