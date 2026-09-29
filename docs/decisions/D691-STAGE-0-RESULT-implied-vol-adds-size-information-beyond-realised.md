# D691 STAGE 0 RESULT — SIZE INFORMATION CONFIRMED on ES and NQ: the prior close's implied-to-realised ratio cuts the out-of-sample error of D671's size forecast by 10.7 % (ES) and 9.2 % (NQ), at DM t 7.3 and 7.6, above every one of ~2,200 enumerated rotations

*2026-09-29. In-sample, 2018-01-09 → 2025-02-28; the vault was never read. The principal: "build the runner and run
it". Pre-registration [D691 STAGE 0 DESIGN](D691-STAGE-0-DESIGN-implied-vs-realised-vol-as-a-size-predictor.md)
(`7a9e4e69`), committed alone before its runner.*
- **The runner** `scripts/stage0_d691_iv_size.py` was committed before any gate or outcome (`1e9bcbf2`). The gates were
  committed before the run (`3291c610`, `data/stage0_d691_gates.json`). It ran once (`874120e1`, 12.3 min). Output:
  `data/stage0_d691_iv_size.json`, statistics only, no per-date series.
- **Dealer gamma (GEX) is SqueezeMetrics',** read to < 2025-03-01 as in D663/D671, and credited.
- **A premise check.** It admits nothing, trades nothing, and reads no break P&L.

## The answer in one line

**Gate S passes on both roots, on all three checks, decisively.** It permits a Stage 1 pre-registration on each root
and nothing more.

**What carries it is implied volatility *relative to* realised volatility, not its level.**
- `ln IV` added alone does nothing (t −0.9 and −1.4).
- About a third (ES) to a half (NQ) of the gain is the ratio's realised denominator.
- Implied volatility adds 7.5 % (ES) and 5.1 % (NQ) beyond it, at t 5.4 and 4.5.
- *This split is a post-hoc diagnostic (§4), not a registered test.*

## 1. Gate S (per root; Holm across ES and NQ)

The loss differential is d = e0² − e1², with M0 = D671's realised-only forecast and M1 = M0 + ivrv. Walk-forward, on
the same sessions.

| | ES | NQ |
|---|---:|---:|
| sessions scored | 1,774 | 1,745 |
| MSE, M0 → M1 | 0.1722 → 0.1538 | 0.1527 → 0.1386 |
| **d̄ (MSE reduction)** | **0.01847 (10.7 %)** | **0.01409 (9.2 %)** |
| (a) one-sided NW(5) HAC t; Holm p | **7.34**; 1.1e-13 | **7.64**; 2.1e-14 |
| (b) enumerated rotation of ivrv: offsets; p50 / p95 | 2,234; −0.00015 / +0.0000021 | 2,182; −0.00022 / +0.000092 |
| (b) rank of the actual d̄ | **1.000** (above every offset) | **1.000** |
| (c) d̄ without Feb–Apr 2020 | +0.01692 | +0.01326 |
| **verdict** | **SIZE INFORMATION CONFIRMED** | **SIZE INFORMATION CONFIRMED** |

**The null is decisive.**
- The rotation's median is a hair below zero: an unrelated series costs M1 a little estimation noise.
- Its p95 is at zero.
- The actual gain is two orders of magnitude beyond it.
- The rotation enumerates the whole group, so the p95's SE is exactly 0 (CLAUDE.md).

**Power, against the guess.** The pre-registration guessed a 1–2 % MSE reduction (§6). The actual gain is five to ten
times that.

## 2. Reported, never gating

**Out-of-sample Spearman with the day's ln(range/ATR20):**

| | ES | NQ |
|---|---:|---:|
| M0 | 0.471 | 0.424 |
| **M1** | **0.551** | **0.505** |
| `ln IV` alone | 0.160 | 0.103 |
| rv5 alone | 0.383 | 0.347 |

**M1's final slopes** (standardised, NNLS, the last refit), g / on_range / rv5 / abs_gap / event / opex / **ivrv**:
- ES: 0.035 / 0.071 / 0.061 / 0.080 / 0.029 / 0.008 / **0.162**;
- NQ: 0.040 / 0.061 / 0.055 / 0.079 / 0.020 / 0.004 / **0.138**.
- On both roots `ivrv` carries the largest weight in the model.

**d̄ by year** (all positive on both roots; 2025 is two months):

| | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ES | .0092 | .0274 | .0237 | .0359 | **.0025** | .0135 | .0134 | .0404 |
| NQ | .0134 | .0188 | .0193 | .0231 | **.0010** | .0095 | .0103 | .0323 |

- **2022 is nearly flat on both roots.** A plausible reading, not measured here: realised and implied volatility stayed
  high together that year, so the ratio had least to say.
- **Before and after 2022-05-16 (the daily-expiry era):**
  - ES 0.0223 → 0.0125;
  - NQ 0.0170 → 0.0096.
  - The gain roughly halves in the daily-expiry era and stays positive.

**Without g** (M1 against M0, SPX gamma removed from both):
- ES d̄ 0.0178 (t 7.15);
- NQ d̄ 0.0128 (t 7.08).
- Both are slightly *smaller* than with g.

**The secondary target, ln(|open → close| / ATR20):**
- ES d̄ 0.0247 (t 4.62, n 1,762);
- NQ d̄ 0.0218 (t 4.36, n 1,741).
- The information reaches the day's net move as well as its range.

**Coverage and sanity:**
- IV coverage on the scored window: ES 99.7 %, NQ 98.0 %.
- corr(IV, RV20) = 0.81 on both.
- The median IV by year stands out in 2020 and 2022 (§3).

## 3. Data gates (committed before the run, `3291c610`)

| gate | ES | NQ |
|---|---|---|
| G1 coverage (IV table, window) | 100 % | 98.4 % (29 sessions with no bracketing call/put pair, 2018–2024) |
| G2 price → IV → price, worst relative error | 3.9e-14 | 2.5e-14 |
| G3 point-in-time second path, 30 sessions each, to 1e-10 | passed | passed |
| G3 canary: an IV built on the session's own settle | **fired** | — |
| G4 seal (no session ≥ 2025-03-01) | held | held |
| G5 median IV, 2017 / 2020 / 2022 | 0.067 / 0.198 / 0.227 | 0.101 / 0.255 / 0.293 |

## 4. Post-hoc diagnostic: implied volatility, or the realised denominator? (NOT pre-registered)

**Why it was needed.** `ivrv = ln IV − ln RV20`. RV20 (close-to-close) is realised and is not in M0, so the gain could
belong to it alone. The rotation null rotates the ratio as a unit and cannot separate the two.
- **The script** is `scripts/diag_d691_iv_decomposition.py`, run after the verdict, and its output is
  `data/diag_d691_iv_decomposition.json`.
- **Same forecast, same sessions, every added term at sign +.**
- **An assertion** checks that the parts add up to the registered d̄. Its model C reproduces §1 exactly.

| MSE reduction (DM t) | ES | NQ |
|---|---:|---:|
| A = M0 + (−ln RV20), over M0 | 3.5 % (2.72) | 4.4 % (3.74) |
| B = M0 + ln IV, over M0 | −0.1 % (−0.88) | −0.1 % (−1.35) |
| C = M0 + ivrv (the registered M1), over M0 | 10.7 % (7.34) | 9.2 % (7.64) |
| D = M0 + ln IV + (−ln RV20), over M0 | 10.7 % (7.46) | 9.2 % (7.53) |
| **C over A: IV beyond the realised denominator** | **7.5 % (5.36)** | **5.1 % (4.46)** |
| D over A | 7.5 % (5.62) | 5.1 % (5.18) |

**Correlations on the scored sessions:**
- corr(ln IV, −ln RV20) = −0.79 on both roots;
- corr(ivrv, ln IV) = 0.21 (ES), 0.09 (NQ);
- corr(ivrv, −ln RV20) = 0.44 (ES), 0.56 (NQ).

**Reading:**
1. **IV's level is volatility's level (0.79 with RV20), and the target is already normalised by ATR20.** `ln IV` alone
   therefore has nothing left to say. That is why prediction 3 failed, and why B is zero.
2. **The realised denominator alone is worth 3.5–4.4 %.** It is about a third of ES's gain and a half of NQ's. RV20 is
   a close-to-close measure and the target is range over ATR20, so −ln RV20 carries mean reversion in the ratio of the
   two realised measures. This part is **not** implied-volatility information.
3. **Given RV20, implied volatility adds 7.5 % (ES) and 5.1 % (NQ)** at t 5.4 and 4.5. That is the part only the
   options market knows. D, which frees the two coefficients, does no better than the fixed ratio C.
4. **Unlike §1, this split has no rotation null.** Rotating `ln IV` with RV20 held fixed is the control that breaks only
   the claimed ingredient. Stage 1 should carry it.

## 5. Predictions (§7 of the design)

| # | prediction | outcome |
|---|---|---|
| 1 | M1 beats M0 on ES (Gate S passes) | **held** |
| 2 | the gain on NQ is smaller than on ES | **held** (d̄ 0.0141 < 0.0185; 9.2 % < 10.7 %) |
| 3 | `ln IV` alone beats rv5 alone in Spearman, both roots | **failed** (0.160 vs 0.383; 0.103 vs 0.347). IV's level is volatility's level (§4.1). |
| 4 | M1's final slope on `ivrv` is positive, both roots | **held** (0.162, 0.138; the largest slope in the model) |
| 5 | the gain is larger without g (IV and gamma overlap) | **failed** (0.0178 < 0.0185; 0.0128 < 0.0141). They are complementary: IV does not stand in for dealer gamma. |

## 6. What this is not

**Not a trade.** The four reporting groups (performance, trade distribution, what the winners depend on, nulls on
P&L) have no object here. They belong to Stage 1.
- **Component line:** none; there is no construction.
- **Size the prize before Stage 1:** a 10 % cut in the squared error of *log* range is not yet a number of dollars. D671
  already showed that a better size forecast pointed the wrong way for the plain break on NQ.

**Not a confirmation.** This is in-sample development on the window D671 had already read (the target and M0). Only
the feature is new.

## 7. Deviations (none replaces a verdict)

1. **G2** used the runner's own price → IV → price check on the bracketing options of 10 sampled sessions a root, not
   D581's `audit_iv_roundtrip`.
2. **G3's second path is independent only in the forward's date rule.** It takes the strip's last settle strictly before
   T by its own lookup. It shares the option selection (`candidates`) and the strike interpolation (`atm_iv_session`)
   with the first. The canary tests the date rule, which is the one a lag would break.
3. **Implementation choices beyond the text:**
   - the nearest qualifying expiry is sought within 15 sessions, else NaN;
   - strikes within 5 % of F;
   - the underlying is that of the nearest expiry.
4. **The timing** was measured on 3 offsets, not 50: 0.37 s an offset, projected at 1.2 min a root. The rotation took
   5.0 and 5.2 min, because another session's job was running on the machine. The whole run took 12.3 min, inside the
   declared 15.
5. **The rotation's offsets run 21 … n − 22.** The range's upper bound is exclusive, so offset n − 21 is omitted.
6. **D665's break |follow-through| secondary target was not computed.** The open → close target was.
7. **The first `--run` crashed after the rotation,** at a numpy string `min()`, before anything was printed or written.
   No outcome was seen. The one-line fix is `874120e1`, and the run-once guard is on the output file, which did not
   yet exist.

## 8. Routing (the design's §8)

**CONFIRMED on both roots permits a Stage 1 pre-registration on each, on the principal's word.** It would test the plain
break (D668's E4, friction once, D668-A2) split by the declared "coiled" hypothesis: breaks on days with a low
realised range but a high implied-to-realised ratio carry.

What Stage 1 must carry from this record:
- **the RV20-only control** (§4): the coiled split scored with `ln IV` rotated and RV20 held fixed, so that the realised
  denominator cannot pass for implied information;
- **on NQ, the overlap with D680:** the compression break, frozen in slot 9. A filter on NQ's break refines D680 and is
  confirmed only by D680's vault look;
- **on ES, the lack of an unread index slice** to confirm on.
