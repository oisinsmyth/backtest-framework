# D430 RESULT — out of sample, the construction does not generalise across names: the base touch effect does, and every layer built on top of it vanishes

**FAILS: T1, T1b, T2, T3 all fail. The declared reading is "the construction does not generalise
across names."** Pre-registration `7dd4ff8` and its ADDENDUM `7c09e3c` predate the read. **This
was the one read of `us_shorts_daily_holdout.csv.gz` for this line (SHA-256
`7d895e13562c8e453e74b684b21f6999ced0eb8dbaa0fbd397703a83939d842c`); it is now spent.
`holdout2` was not touched. The ledger does not move. Nothing was admitted.**

Cost: 212 s from the opener's cache (the opener itself 15 s); one worker measured at 951 MB.

```
[COUNTS]  803 names; touches 92,183  cell 2 12,816  second touch & cell 2 4,726  POOL 667 (0.159/day)  priority 91
          scaled expectation ~92,000 / ~13,300 / ~4,800 / ~720 / ~85  -- every count within 10%
          the holdout's own cell-2 medians (NOT used): REV -0.02467  EFF 0.2351  DV $41.9M   vs frozen -0.02473 / 0.2367 / $44.4M
[RECON]   18 books;  [CHUNK] worker draw 0 == in-process
```

The construction, the thresholds and the sizing rule transferred exactly: the holdout's own
medians sit within 1–6% of the frozen cuts and every population count landed within 10% of the
scaled prediction. **The machinery generalised. The edge did not.**

---

## 1. The bar

```
T1   pool gross > 0 by 2 SE          -28.68 ± 31.15    -0.9 SE    FAIL
T1b  pool net > 0                    -63.99            -2.1 SE    FAIL
T2   N=2 book net > 0 by 2 SE        -3.231 ± 2.230    -1.4 SE    FAIL   (all seeds: -3.37 -3.38 -2.95)
T3   N=2 book > random long pools    p50 -1.398  p95 +0.979 (±0.136)   -31.1 SE   FAIL
per-trade null   premium -53.65 vs p95 +5.32   -52.7 SE   FAIL
```

---

## 2. THE LADDER — where it broke

```
rung                          n      gross (in-sample)     median    NET     win    trim     ex-top   ex-bot
all touches               92,183    +10.09   (+9.81)       +8.2   -22.6   50.7%   +10.5    -15.3    +35.9
cell 2                    12,816    +18.10  (+30.26)      +20.3   -10.8   52.0%   +22.1     -4.4    +44.4
second touch & cell 2      4,726     +6.21  (+44.84)       +2.8   -22.8   50.1%   +12.5    -14.9    +33.6
+ cheap                    1,448    +16.61  (+86.48)      +24.1   -18.9   52.1%   +30.6     -6.6    +53.1
+ gap 3-20                 1,217    +10.67  (+84.48)      +30.8   -24.2   52.3%   +26.2    -13.4    +49.3
long = THE POOL              667    -28.68  (+79.93)      +42.6   -64.0   52.9%    -3.7    -52.6    +17.5
the short half               550    +58.39  (+89.71)      +17.8   +24.1   51.6%   +53.8    +31.9    +83.4
```

**The base touch effect reproduced: +10.09 on 92,183 new-name touches against +9.81 in-sample.**
That is D412/D413's object — a distance-armed departure zone, touched, held five sessions — and
it is the only rung of the ladder that came through intact. **Cell 2 came through at half**
(+18 against +30). **Everything above it is gone:** the second touch, which paid +45 in-sample,
pays +6 on new names — inside 1 SE of the base rate it was supposed to double; the cheap tercile,
+86 in-sample, is +17; and the long half of the cheap second-touch pool, +80 in-sample, is
**−29 gross, −64 net**, while its short half is +58.

**The sign flip is a left tail, not a shift.** The pool's median is +42.6 — above the in-sample
median's neighbourhood — and its mean is −28.7: the trimmed mean is −3.7, removing the bottom 1%
lifts it to +17.5, and the year table has **2020 at −635 bp on 34 trades and 2022 at −354 on 40**.
Cheap longs bought at a second demand-zone touch in March 2020 and in 2022 did not bounce; they
kept falling. In-sample, 2020 was the *best* year of the long book (+13.5/bar) and 2022 a mild
negative; on new names 2020 is −16.0/bar and 2022 −15.8. **The in-sample 2020 premium was the
names, not the year.** D422 §5 said the premium "lives in seven years, one of them a regime";
this is what that sentence meant.

The top trade (HSAI, +42.5% on 26.6M shares, 2025-03-04) is real and is 22% of a negative P&L
— the concentration table's "names to half" reads 1 because the total is negative and is not
meaningful there.

---

## 3. THE BOOK — negative at every slot count, on every seed, in every window

```
N   arm     gross     net    cost   util   trades  per trade   net by seed            pooled ± SE      2018+ ± SE       2021-26 ± SE
1   PRIO   +0.261  -2.295   2.555  36.2%    299     +3.59    -2.30 -1.12 -0.08    -1.16 ± 2.55    -3.77 ± 3.90    -5.67 ± 3.79
2   PRIO   -1.429  -3.365   1.936  27.1%    448    -26.29    -3.37 -3.38 -2.95    -3.23 ± 2.23    -6.32 ± 3.36    -6.93 ± 3.43
3   PRIO   -0.968  -2.399   1.431  20.4%    506    -23.65    -2.40 -2.69 -2.38    -2.49 ± 1.57    -5.03 ± 2.39    -5.31 ± 2.58
random long pools of 667 at N=2:  p50 -1.398  p95 +0.979  -- the pool is BELOW a random draw of the holdout's cell-2 longs
```

The N=2 book sits below the *median* random long pool of the same count: on new names, this
selection is worse than no selection. The 2018+ and 2021+ windows — the ones that carried
in-sample — are the worst here (−6.3, −6.9). The priority is inside its noise (+0.06), as
predicted, which is the one prediction that held.

---

## 4. Predictions — one of seven

| | prediction | outcome |
|---|---|---|
| X-a | pool 580–870 | 667 ✓ |
| X-b | ladder keeps shape, rungs 50–80% of in-sample | **shape breaks at the second touch: +6 vs +45; the pool inverts** |
| X-c | pool gross +35..+65, net 0..+30 | **−28.7 / −64.0** |
| X-d | permutation null passes | −52.7 SE |
| X-e | book +1..+3.5, ≥2 seeds positive, T3 passes | −3.2, all seeds negative, T3 fails by 31 SE |
| X-f | 2018+, 2021+ above pooled; 6–10 names to half | both far below; P&L negative |
| X-g | priority inside noise; N=1 ≥ N=2 | ✓ |

**X-c was the prediction that mattered, and the pre-registration said what its failure meant
before the file was opened:** "the construction's per-trade edge was the names it was built on,
and nothing in the twenty-nine studies before this survives that." That is the reading.

---

## 5. What this leaves

1. **The candidate is dead on new names.** Every layer that made D429 — the second touch, the
   cheap tercile, long-only, the gap, the priority — was selected on the 1,573 in-sample names
   after one look each (D427 §5 and D428 §5 said so), and on 803 unseen names their combined
   effect is a −64 net trade and a book below a random draw. The forking path did what forking
   paths do.
2. **What survives is small and old:** the base departure-zone touch effect, +10 gross on 92,183
   new-name events against +9.8 in-sample, and cell 2 at about half its in-sample size. +10 gross
   against a 29–33 bp round trip is not a trade; it is a real, weak, reproducible base rate that
   twenty studies of layering did not convert into one.
3. **The second touch was not a mechanism.** D421/D422's "second zone pays double" — the finding
   the whole second half of this line was built on — is +6 on new names. The nulls it passed
   in-sample (within-day permutation, random pools, +5.4 to +9.7 SE) were tests of *selection
   within the spent names*, and they were passed by a selection that does not transfer.
4. **The in-sample 2020 premium was name luck.** On new names, cheap longs at a second zone in
   2020 and 2022 lost −635 and −354 bp a trade. D422 and D428 flagged the concentration in those
   years; this is the realisation.
5. **`holdout2` remains unspent, and nothing in this record is a reason to open it.** The one
   question a second holdout could answer is whether the *base* effect and cell 2 hold on a third
   name set; it cannot resurrect the layers.

**Disposition is the principal's.**

---

## 6. R13

Thirtieth look by object on price levels; **the first out of sample, and the one holdout read
this line has made.** `us_shorts_daily_holdout.csv.gz` is spent for this line.

**Evidence:** `data/d430_oos.json` (counts, the ladder on three windows, the null, 18 books, the
control, the year tables). Opener `scripts/d430_oos_loader.py` (the only code that touched the
file); runner `scripts/run_d430_holdout.py` (`--proof` passed on the in-sample fixture before the
read: D413 / D422 / D429 reproduced bit-identically through the same path).
