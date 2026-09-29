# D673 RESULT — NOT SUPPORTED on YM and on RTY: the compression break does not transfer. On RTY the compressed third is the WORST of the three (−8.07 bp net, t −2.70); on YM it is no better than the rest. The NQ result stands only as an NQ-specific, in-sample finding

*2026-09-29.*
- *One completed run of `scripts/stage0_d673_compression_ym_rty.py` under D673 (`fb8c4c5e`), 1.2 min.*
- *Data gates passed before any outcome (`febb7ff9`):*
  - *(i) identity of the new overnight fixture's RTH bars with D462's is exact (YM 906,639 bars, RTY 756,413);*
  - *(ii) overnight coverage is 100% every year on both roots;*
  - *(iii) no vault row.*
- *Output: `data/stage0_d673_compression_ym_rty.json`. Dealer gamma (GEX): SqueezeMetrics, a secondary only.*

**Disclosure.**
- The first `--run` crashed in its output step (a `KeyError`: YM's daily series was trimmed before RTY's correlation
  used it). That was after computing, but before writing or printing anything. No outcome was seen.
- The fix, committed before the completed run, moves one line and changes nothing else.
- The run also reproduces D672's development C1 exactly: ES +0.5535, NQ +6.9339.

## 1. The books (1 micro, net of MYM/M2K `d508_exec`)

| | YM (2018-01 →) | RTY (2019-08 →) |
|---|---|---|
| B0, every break | gross +1.17, net −1.64 (t −1.51), 162/yr, Sharpe −0.56 | gross −0.26, net −4.81 (t −2.85), 165/yr, Sharpe −1.15 |
| **C1, compressed third** | **gross +0.76, net −2.03 (t −1.05)**, 58/yr, P(hold) 0.60 | **gross −3.55, net −8.07 (t −2.70)**, 56/yr, P(hold) 0.55 |
| C2, middle | gross +2.22, net −0.57 | gross +5.22, net +0.63 |
| C3, busiest | gross +0.59, net −2.26 | gross −2.38, net −6.94 |

## 2. The gates (Holm across YM and RTY)

| | YM | RTY |
|---|---|---|
| **Gate 1a:** C1 − rest (gross) against the enumerated rotation, p50 / p95 / rank | −0.63 against +0.04 / +3.81 / 0.39 | **−4.97** against +0.01 / +6.17 / 0.08 |
| **Gate 1b:** C1 gross, HAC t (Holm p) | +0.76, t 0.40 (0.69) | −3.55, t −1.19 (0.88) |
| **Gate 2:** C1 net; placebo p50 / p95 / rank | −2.03; −1.67 / +0.75 / 0.40 | −8.07; −4.91 / −0.80 / 0.10 |
| **Verdict** | **NOT SUPPORTED** | **NOT SUPPORTED** |

**Power, as registered:** about 0.90 on YM and 0.62 on RTY at NQ's effect.
- YM's null is informative.
- RTY's estimate is not a near-miss: it has the wrong sign, and its point estimate (−5.0 bp relative to the rest)
  sits well below zero.

## 3. Predictions (§5)

| # | prediction | outcome |
|---|---|---|
| 1 | RTY passes Gate 1 | **failed:** the compressed third is RTY's worst |
| 2 | RTY's Gate 2 marginal, net positive | **failed:** net −8.07 |
| 3 | YM fails 1a, with C3 its worst | **held:** fails 1a; C3 −2.26 is its worst |
| 4 | RTY: higher dealer g is better within C1 | **held:** −3.43 vs −10.74 |
| 5 | RTY's C1 positive in ≥ 4 of its full years | **failed:** positive in 1 of 5 (2022) |

**The root stories got RTY wrong.** "RTY re-prices at the cash open like NQ" did not produce NQ's behaviour. RTY's
whole break is negative before costs (B0 gross −0.26). The small-cap index gives back its breaks, compressed or not.

## 4. Secondaries (reported only)

**Each input alone,** as the tier (bottom third, gross; net in brackets):

| | recent range (p_rv) | overnight range (p_on) |
|---|---|---|
| YM | −0.28 (−3.08) | +3.28 (+0.46) |
| RTY | −4.71 (−9.35) | +4.94 (+0.38) |
| *ES, D672* | *about 0* | *+4.79 (+1.71)* |
| *NQ, D672* | *+7.87* | *+7.34* |

- **Across all four roots, the quiet-OVERNIGHT half points the same way** (positive gross on every root).
- **The quiet-RECENT-DAYS half helped only NQ**, and hurts RTY.
- The composite rule inherited the recent-range half's failure.
- This is a post hoc observation across four roots. It is recorded here and **not promoted**.

**Other secondaries:**
- **Dealer g within C1:** above its median is better on both roots (YM −0.10 vs −3.37; RTY −3.43 vs −10.74). This is
  the same direction as NQ and ES (D665's size effect), but neither side is profitable.
- **Long / short:** YM −1.51 / −2.85; RTY −5.59 / −11.16.
- **The E2 exit:** YM −1.23; RTY −7.72.
- **By year:**
  - YM's C1 is positive in 2018 and 2022 only;
  - RTY's C1 is positive in 2019 (partial) and 2022.

**The component line (C1, daily $ at 1 micro):**
- YM Sharpe −0.45 (ρ K8 +0.04);
- RTY −1.33 (ρ K8 −0.07).

## 5. Routing (D673 §7)

**NOT SUPPORTED on both evidence roots:**
- **The compression break is recorded as NQ-specific or spurious.** NQ's in-sample +6.93 (D672) was found and checked
  on the same sample, and it failed to transfer to the two roots that could confirm it.
- **It stands only until the vault reads NQ,** with about 30% power per D667. It is not a ledger candidate.

**What survives as a direction, not a result:**
- The overnight-quiet half is consistent in sign across ES, YM and RTY, and on NQ.
- A successor built on it alone would need a fresh pre-registration and a sample none of these reads has touched. The
  energy and metals roots (CL, NG, SI) have never been run through this construction.
