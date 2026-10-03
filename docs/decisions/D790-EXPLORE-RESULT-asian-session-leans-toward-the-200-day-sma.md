# D790 EXPLORE RESULT: gold does not rise at the China open, the open's shape carries nothing, and the one new channel is the trend. The 09:31–15:00 session leans back toward gold's 200-day average (ρ +0.065), independent of the open and of every channel the debate measured

*2026-10-03. One run of `scripts/explore_d790_china_open_anatomy.py --run` (53 seconds), under the
[scope note](D790-EXPLORE-anatomy-of-gold-s-china-open-scope.md) committed before it (`db424000`).*
- **The follow-up was taken AFTER seeing the run:** `scripts/explore_d790_followup_trend.py` (the decomposition in §4).
  Both are disclosed.
- **Outputs:** `data/explore_d790_china_open_anatomy.json`, `data/explore_d790_followup_trend.json`.
- **This is in-sample triage** (RULES.md's correction to R14). Nothing is admitted, and nothing on or after
  2024-01-01 is read. D786's build reproduced D767 and D770 exactly.

## 1. Why gold moves at the China open: it does not rise there; the open is size, not direction

| | |
|---|---|
| mean x (09:00 → 09:30 Beijing, MGC) | **+\$0.34, t 0.58; up on 51.0%** of 1,697 sessions |
| by year | between −\$2.93 (2022) and +\$2.44 (2021), no year beyond \|t\| 1.8 |

- **What predicts the open's direction (Spearman with x; SE about 0.025):**

  | input | ρ with x | timing |
  |---|---|---|
  | the CME overnight move g | **−0.090** | before 09:00 |
  | g_US (the US afternoon) | −0.083 | before 09:00 |
  | the SGE premium's 20-day dislocation | +0.056 | before 09:00 |
  | the SGE premium's level | −0.003 | before 09:00 |
  | the change in the CNY fix (09:15) | −0.053 | inside x |
  | the AUD in the same window | **+0.295** | contemporaneous |

- **So the open is:**
  - a partial correction of the Western night's move;
  - a common China/AUD risk factor;
  - a little onshore premium pressure.
  - It is not a buying session. D765's finding stands: the open is a third to three-fifths LARGER when Shanghai
    trades, with no direction.
- **The half-hour drift across the CME day** (44 windows, \$ per MGC; the family's expected max \|t\| is about 2.8):
  - 09:00–09:30 is +\$0.33 (t 0.58);
  - **the largest drift is 10:00–10:30 Beijing, +\$1.12 (t 3.21);**
  - the SHFE lunch break, 11:30–12:30, is the most negative: −\$0.75 (t −2.44) and −\$0.64 (t −2.29);
  - 18:00 Beijing is −\$1.01 (t −2.28).
  - Only 10:00 is beyond the family's expected maximum. The lunch-break drop fits the lead hunt's "gold reverts
    where its cash venue is shut" (D772).

## 2. The open's shape: no "spike means reversal"

| feature (along x) | passive ρ (2016–19 / 2020–23) | rotation rank |
|---|---|---|
| S1 the largest one-minute move's share (the spike) | −0.012 (+0.008 / −0.026) | 0.34 |
| S2 the largest 3-minute burst | +0.029 (+0.037 / +0.019) | 0.73 |
| S3 the time of the extreme | +0.017 | 0.50 |
| S4 the retrace from the extreme at 09:30 | +0.014 | 0.40 |
| S5 path efficiency | −0.016 | 0.47 |
| S6 the first minute's share | −0.012 (+0.030 / −0.038) | 0.33 |
| **S7 the share done by 09:05** | **−0.054** (−0.032 / −0.063) | 0.958 |
| **S8 the share done in 09:20–09:30** | **+0.047** (+0.025 / +0.060) | 0.938 |
| S9, S10 volume concentration and late volume | +0.000, +0.012 | — |
| S11 relative size | +0.018 | 0.48 |

- **Continuations and reversals have the same shape.** The class medians of every shape feature are within a few
  points: the spike share is 0.37 and 0.33.
- **The only shape signal is WHEN the open's move was made:**
  - one done early (by 09:05) reverts less;
  - one made in the last ten minutes, into the entry, reverts more: passive top tercile +\$6.82 gross, +\$3.79 net.
  - Neither clears the lead bar (ranks 0.94–0.96). It is the same thing D787 found from the other side: the path
    after 09:30 tells nothing, and the push into 09:30 is the overshoot.

## 3. Against the trend: the family that sorts the fade

| feature (the open stretching away from the average when positive) | passive ρ (2016–19 / 2020–23) | rank | taker ρ |
|---|---|---|---|
| **T1s along x, vs SMA200** | **+0.064** (+0.056 / +0.063) | **0.979: LEAD** | +0.060, rank 0.978: LEAD |
| **T2s along x, vs SMA50** | **+0.070** (+0.099 / +0.052) | **0.992: LEAD** | +0.052 (0.967) |
| T3s along x, vs SMA20 | +0.057 (+0.086 / +0.040) | 0.965 | +0.044 |
| T5s RSI(14) − 50, along x | +0.046 (+0.051 / +0.046) | 0.916 | +0.031 |
| T6s the 20-day return, along x | +0.052 (+0.071 / +0.036) | 0.956 | +0.043 |
| the unsigned distances, the 250-day high | −0.014 to +0.029 | ≤ 0.72 | — |

- **The family-max null across all 20 features:**
  - passive: the best \|ρ\| 0.070 against a family p95 of 0.078, **p 0.12**;
  - taker: 0.060 against 0.073, p 0.19.
  - **No feature clears the family.** The trend features are one factor (ρ 0.43–0.83 among T1s, T2s, T3s and T6s),
    and their halves agree in sign everywhere.
- **T1s terciles, passive:** low +\$0.98, mid −\$1.41, **high +\$6.42 gross, +\$3.39 net** (t 2.71 gross).

## 4. The follow-up decomposition (taken after seeing §3): it is the SESSION, not the open

- **ρ(−distance to SMA200, y) = +0.065, with no reference to the open.** The 09:31–15:00 session leans back toward the
  200-day average. The open does not (ρ(−dist, x) = +0.007).
  - So by the debate's identity, T1s's accuracy IS this pull. The fade filter is a way of trading it on the half of
    days where it agrees with the fade.
- **The regime × the open (SMA200; passive: n, gross, net):**

  | | the open moved AWAY from the average | the open moved TOWARD it |
  |---|---|---|
  | price above SMA200 (64% of sessions) | 438, +\$3.92, +\$0.89 | 401, +\$0.70, −\$2.34 |
  | price below SMA200 | **228, +\$6.86, +\$3.83 (t 2.39)** | 261, −\$3.47, −\$6.50 |

  - **The fade pays where both forces point the same way:** the open stretched away, the fade trades back toward the
    average, and the session's pull agrees.
  - It loses where they disagree, most of all below the average.
  - Pooled, "the open moved away from SMA200" is 666 passive trades, about +\$4.9 gross and +\$1.9 net, gross t
    about 2.5.
  - **The best cell (below the average, a down-open stretching further: buy it) is one of eight looked at, post hoc.**
- **It is a new channel.** ρ(T1s, the debate's g-opposition) is −0.053; with g_US's opposition (D786's candidate 2)
  −0.037; with |x| +0.003.
  - The debate's phase 2 found that its four channels capped a composite at 0.039–0.067, and said a pass needed a
    channel independent of them. This one is independent, at 0.06–0.07.
- **The walk-forward third by T1s, passive:** 417 trades, +\$3.82 gross, +\$0.78 net.
  - Short fades +\$2.03 net (301); long fades −\$2.44 (116).
  - By year: +2.34, −3.29, −2.23, +7.22, **+14.63 (2021)**, −2.11, +2.37.
  - **T6s (the 20-day return) has the best third:** +\$5.55 gross, **+\$2.52 net, gross t 2.34**, 2021 again the
    largest year (+\$10.87).

## 5. What this gives the principal

- **The answer to "why":**
  - the China open is not a buying event. It is a large, direction-neutral repricing that partly corrects the Western
    night, moves with the AUD, and carries a little onshore premium pressure;
  - the fade's edge is the session giving that back;
  - **the one force found that predicts WHICH way the session goes is the trend:** the Asian session leans back toward
    the 200-day average.
  - A price-sensitive physical clientele (buying below the average, selling above it) is the natural account. It is
    an account, not a finding.
- **Shape is not the key.** The winners and losers of the fade look alike over 09:00–09:30, except that a push made
  late, into 09:30, reverts more.
- **The candidate a 2024+ read could test,** one frozen definition, chosen now from the in-sample:
  - the passive fade, taken only when the open moved away from the 200-day average (T1s > 0);
  - or a direction score combining the fade with the pull, which by the debate's composite arithmetic is about
    √(0.063² + 0.065²) ≈ 0.09 if the two are independent, against a passive G2 bar of about 0.10.
- **The power problem comes first:**
  - 2024-01 → 2026-09 holds about 650 sessions; at a true ρ of 0.065 the SE is about 0.039, so a one-sided test
    detects it about a third of the time;
  - the slice also sits after the SHFE auction change (2023-05-26).
  - A holdout read now is more likely wasted than informative. The forward recorder accumulating more sessions is the
    alternative.
- **Not admitted, not nominated by rule:** T1s and T2s meet the per-feature lead bar, but no feature clears the
  family-max null (p 0.12 passive). The in-sample is 2016–2023, already read for this fade many times.
