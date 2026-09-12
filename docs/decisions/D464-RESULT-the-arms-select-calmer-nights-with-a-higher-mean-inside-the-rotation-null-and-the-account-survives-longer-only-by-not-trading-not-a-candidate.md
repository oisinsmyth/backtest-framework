# D464 RESULT — the arms select calmer nights with a higher mean that sits inside the rotation null, and the account survives longer only by not trading: NOT a candidate

**NOT A CANDIDATE: G1 fails, G2 passes, no cell on either grid clears P4.** Spec `0391331` predates
the runner (R8). **In-sample 2016-01-04 to 2023-12-29 on ES; 2024 onward unread; no holdout.**
0.4 min. **S1's and S2's status in the personal book is untouched by this record** (spec §0).

```
2,043 same-contract 18:00 -> 16:00 ES holds (D449's table, restricted to the D462 usable window; the Monday-only 2010-2015 rows are not used)
gates = the arm's state at the close of the entry day, from the book's own code: run_activation_threshold.log_parts (S1), structure.pivots + run_uptrend_onset.rolling_fit (S2)
selftest: S2 on a sawtooth uptrend (exposure runs capped at 63); S1 on a synthetic V (off in the fall, on in the climb-out, off above); gate timing; the rotation null at offset 0; the run-length generator
```

---

## 1. The nights, gated and not

```
gate (SPY)            nights   share    mean bp   +- SE    sd     median   hit    MAE bp p50 / p99 / worst    $ p99 / worst (1 ES ct, day)        P(MAE > $1k)   P(> $2k)
all                    2,043   100%     +5.52     2.02    113     +5.99   53.8%     45 / 369 / 1,070          6,325 / 14,075 (2020-03-16)          37.6%         18.4%
S1 (recovery)            177     8.7%  +13.75     9.98    126    +11.76   56.5%     69 / 321 /   332          5,122 /  6,412 (2022-06-10)          50.8%         24.3%
S2 exposure (<= 63 bars) 204    10.0%   +9.09     4.67     94     +5.44   52.9%     49 / 321 /   552          5,411 /  7,713 (2020-09-03)          36.3%         15.2%
S2 raw state           1,129    55.3%   +4.81     2.73    109     +4.77   53.5%     40 / 395 /   997          6,238 / 13,650 (2020-03-12)          34.5%         16.6%
union S1 | S2            381    18.6%  +11.26     5.43    110     +7.23   54.6%     57 / 322 /   552
QQQ gates:  S1 +18.39 (n 152)   S2 +0.65 (n 157)        DIA gates:  S1 +14.53 (n 204)   S2 +10.27 (n 215)        S1 and S2 never on together (0 nights)

nulls on the SPY gates (mean per gated night):   S1  N1 rotation p50 +5.72 p95 +16.68 (exact)   N2 run-length gates p95 +15.38 +- 0.22     G1 fail   G2 pass (321 < 369)
                                                  S2  N1 rotation p50 +5.25 p95 +16.73           N2 p95 +13.49 +- 0.23                      G1 fail   G2 pass (321 < 369)
```

**Both arms select nights with a higher mean and a lower tail than the average night** — S1's
nights +13.8 bp at a 56.5% hit rate, S2's +9.1 at a lower σ (94 against 113), and both gates
miss the March-2020 nights that carry the unconditional worst tail (p99 321 against 369 bp: G2
passes for both, against X-b's prediction that S1 would select the wilder nights). **And neither
is distinguishable from a random selection of the same size and persistence:** the exact
rotation of the S1 gate over the hold index puts its p95 at +16.7 bp, the S2 gate's at +16.7; a
subset of 180–200 nights drawn from a +5.5 bp drift with σ 113 has a standard error of 8–10 bp,
and the arms' means sit inside it. The QQQ-computed S2 gate is +0.65 on ES; the DIA one +10.3 —
the sign agrees, the size does not, which is what a sampling fluctuation looks like.

---

## 2. Hurdle P — the account survives by not trading

```
MFFU Rapid EOD 50K, C4 sizing (f x $50k / sigma_hat over the prior 21 traded nights, whole contracts, cap 4x static), 600-day horizon; "1ct" = one contract fixed, beyond the grid
                              ES contracts ($50/pt)                                                    MES contracts ($5/pt)
nights      f        contracts   P3 worst   days<-2%   P4 life yr   alive 600d   V         ann %      contracts   P3 worst   days<-2%   P4 life yr   alive 600d   V          ann %
all        0.2%        0.00        --          0        never funded                       0.0          0.47      -2.35%       1         0.80        100%       -209        +0.2
all        0.4%        0.00        --          0        never funded                       0.0          1.44      -4.69%       6         0.26          0%       -100 +- 9   +1.1
all        0.7%        0.00        --          0        never funded                       0.0          2.90      -8.21%      40         0.11          0%        -82 +- 14  +4.8
all        1.1%        0.15      -11.71%      27        1.05          28%     +42 +- 27    +1.6         4.82     -12.91%     147         0.08          0%       +209 +- 37  +7.7
all        1ct         1.00      -28.18%     791        0.06           0%    +352 +- 48   +28.6         1.00      -2.82%       4         0.57         11%       -146 +- 8   +2.2
S2 gate    0.7%        0.00        --          0        never funded                       0.0          0.27      -4.65%       5         0.83         27%       -209        +0.8
S2 gate    1.1%        0.01       -3.86%       1        1.17          70%    -209          0.0          0.46      -7.74%      17         0.36         23%        -43 +- 6   +1.7
S2 gate    1ct         0.10     -15.46%      78        0.04           8%    -181 +- 10    +6.6         0.10      -1.55%       0        never funded              -209        +0.6
S1 gate    1.1%        0.00        --          0        never funded                       0.0          0.23      -5.59%      13        1.84         19%       -201 +- 2   +1.4
S1 gate    1ct         0.09     -12.86%      95        0.48           0%     -42 +- 33    +8.1         0.09      -1.29%       0        1.94         73%       -209        +0.8
```

**Three things the grid says.**

1. **At whole ES contracts the account cannot hold the trade.** One ES contract's overnight σ
   is about $2,000 — the entire 4% floor — so the C4 rule sizes **zero** at every f up to 0.7%
   and 0.15 contracts on average at 1.1%. **A fixed one-contract book breaches the 2% daily
   limit on 791 of 2,043 nights and lives 0.06 years**; its `V` of +$352 is the value of a
   lottery ticket — the evaluation is passed 32% of the time and paid before the account dies —
   and it is the number that would fool a scorecard.
2. **At micro contracts the size is expressible and the return is not worth the fee.** Sizing
   that survives (f = 0.2%, half a micro on average; or one micro fixed at 0.57 years) earns
   **+0.2 to +2.2% a year of the account**; sizing that earns (f ≥ 0.7%) lives **0.08–0.11 years**.
   This is D259's scissors at a finer grain and with the instrument's true minimum size.
3. **The gates lengthen the account's life in proportion to the nights they remove, and the
   P&L falls with them.** One micro on S1's nights lives **1.94 years (73% alive at 600 days)**,
   the longest life in the study, and earns **+0.8% a year** — the evaluation target is reached
   on 2% of paths and `V` is the fee. S2 at f = 0.7% on MES: 0.83 years against 0.11
   unconditional, at +0.8% against +4.8%. **That is the ledger's own test for an abstention
   rule — "survives iff floor-touch probability falls relatively more than expected P&L; else
   it is an exposure cut with a story" — and it is an exposure cut with a story.** No cell on
   either grid reaches three years, and the ones that come closest never fund.

---

## 3. Predictions — one of six, and the misses are consistent

| | prediction | outcome |
|---|---|---|
| X-a | unconditional +3..+5 bp, σ 90–110, MAE p99 330–420, P(> $2k) 8–14% | **+5.52** (above), σ 113, p99 369 ✓, **18.4%** |
| X-b | S2 on 30–45%, +3..+6, σ 70–95, p99 250–350, G2 pass; S1 on 12–20%, +4..+9, σ 110–150, p99 400–550, G2 fail | S2 **10%** (the book's own 13.9% exposure — the 30–45% was the raw state), +9.1, σ 94 ✓, p99 321 ✓, G2 pass ✓; S1 **8.7%**, **+13.8**, σ 126 ✓, **p99 321, G2 PASS** |
| X-c | N1 p95 +2..+4; G1 fails S2, coin S1 | N1 p95 **+16.7** (a 200-night subset of a 113-σ series); G1 fails both |
| X-d | ES zero size at f ≤ 0.4%, P3 breaches, life < 0.5 yr; MES sizes 2–5, P3 passes, life 0.5–2 yr, +1..+3%/yr | ES zero at f ≤ **0.7%** ✓; MES 0.5–4.8 ct, **P3 fails above f = 0.2%**, life 0.08–0.8 yr, +0.2..+7.7% |
| X-e | S2 lengthens life 1.3–2×, S1 shortens; neither clears | S2 **7.5×** at f = 0.7% (MES), S1 **12×** at f = 1.1% — **by cutting exposure 90%**; neither clears ✓ |
| X-f | QQQ/DIA agree in sign; union ≈ S2; intersection < 5% | signs agree, **QQQ's S2 gate +0.65 vs SPY's +9.1**; union +11.3 on 19%; intersection **0** ✓ |

The N1 prediction was wrong by 5× because it was written for a gate on half the nights; the
arms are on a tenth, and a tenth of 2,043 nights of a 113-bp series has a ±8 bp standard error.

---

## 4. What this leaves — the principal's call

1. **The personal arms cannot be ported to the prop book in the only form the venue allows.**
   As gates on the session hold they pick nights that are, on the numbers, better than average —
   and not distinguishably so — and the hold underneath them is one whose single-contract σ
   equals the account's floor. Gating buys account life only by removing exposure, and the
   surviving configurations earn a fraction of a percent a year.
2. **What outlives the record:** the first hurdle-P grid at the instrument's true minimum size
   (micros), which says the same thing D463 said for a 30-minute hold — on a $50k account, an ES
   position's σ per holding period must be well under $300 to clear P3 and P4, and neither a
   quarter of an hour nor a night on the index does that at one micro or above with any return
   worth the evaluation fee. **The instrument–account pair is the binding constraint of the prop
   track**, not the candidate list.
3. **Not proposed:** a sweep of the arms' constants, a larger account plan (D379's portfolio-of-
   accounts question is a separate record and it exists), or a stop inside the untraded window
   (R11's amendment: it cannot be exited).

**Disposition is the principal's.**

---

## 5. R13

Fifty-first look by object; look #2 of the prop track on the instrument; the 2024 onward slice
unread; the personal book unchanged. **Evidence:** `data/d464_arms_as_gates.json`. Runner
`scripts/run_d464_arms_as_gates.py`.
