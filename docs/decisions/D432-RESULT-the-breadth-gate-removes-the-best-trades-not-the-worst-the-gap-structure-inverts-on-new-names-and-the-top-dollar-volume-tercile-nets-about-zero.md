# D432 RESULT — the breadth gate removes the best trades, not the worst; the gap structure inverts on new names; the top dollar-volume tercile of cell 2 nets about zero

**FAILS every gate: T1, T1b, T2, T3, T4.** Pre-registration `f84bf33` predates the runner and this
file (R8). **Spent data throughout; no fixture opened; `holdout2` untouched. The ledger does not
move.**

Cost: 61 s, one process.

```
[STAGE0] 2,083 / 1,783; the gate's exposure 26.6% long, 3.4% short, as declared
[GATE]   the breadth series is a causal d-4..d window and moves when the touch dates are shifted
[P2]     the union pipeline reproduces D431's short N=3 book on every seed
[ROT]    offset 0 of the enumerated rotation null equals the observed statistic
[RECON]  9 books
```

---

## 1. M1 — the mechanism had the wrong sign

```
LONG pool                    kept (breadth <= 58)        excluded (> 58)           kept - excluded
union                        n 1,528   +26.81            n 555   +95.65            -68.85 ± 39.13   (-1.8 SE)
in-sample half               n 1,040   +48.71            n 376  +166.27           -117.56 ± 41.01   (-2.9 SE)
holdout half                 n   488   -19.88            n 179   -52.68            +32.80 ± 84.55   (+0.4 SE)
holdout half 2018+           n   219   -75.20            n 133  -150.65            +75.45 ± 110.2
holdout half 2021-2026       n   149  -100.02            n  83   +11.08           -111.10 ± 129.9
SHORT pool, union            n 1,723   +71.61            n  60  +322.28           -250.66 ± 116.5
rotation null, holdout half: observed +32.80   p50 -13.86   p95 +253.76   percentile 62.8   (4,190 exact offsets)
```

**The days I called "a market falling" are the days the in-sample long arm made its money.**
The 27% of long trades on high-breadth days average **+96 on the union and +166 in-sample**,
against +27 and +49 for the rest: they are the V-bottoms — March 2020 in-sample paid, 2014 and
2015 paid, 2026 paid — and the gate that was supposed to remove the crash removed the recovery.
**The short arm's sixty high-breadth trades average +322**: shorts sold into broad weakness kept
falling. The mechanism was real and its sign was backwards for longs: breadth marks the days
with the largest moves in both directions, and on the spent names the large move after a broad
second-zone touch was up.

**On the holdout half the long arm is negative in both states** — kept −20, excluded −53, and
the kept set is −75 in 2018+ and −100 in 2021–2026 with a *median* of −55. The excluded set's
2020 is −1,846 on 13 trades and its 2026 is +1,254 on 3. The gate's +33 difference on the holdout
half is at the 63rd percentile of its own enumerated null. **No market-state gate fixes the long
arm on new names, because the long arm on new names is not a bounce that sometimes fails; it is
not a bounce.**

The gated book confirms it: gated long N=3 +1.05 ± 1.90 against ungated +2.24, gated − ungated
**−1.19 ± 0.85**. X-a, X-c and X-d were wrong in sign.

---

## 2. M2 — dollar volume: cost falls, gross rises, and the top tercile nets about zero on new names

```
cell 2 by trailing-ADV tercile   n        gross    median   cost    NET     win     trim
bottom  (< $85M)   union       12,947    +18.19    +16.9   32.32  -14.14   51.5%   +19.6
                   holdout      3,992     +7.74    +18.9   32.71  -24.97
middle             union       12,946    +28.30    +23.5   28.87   -0.57   52.6%   +28.4
                   holdout      4,421    +24.24    +24.3   29.60   -5.36
top     (> $187M)  union       12,947    +32.27    +22.9   24.43   +7.84   52.3%   +30.6
                   in-sample    8,544    +37.90    +27.7   24.22  +13.67
                   holdout      4,403    +21.34    +14.8   24.82   -3.49           (2018+ -5.08; 2021-2026 -1.94)
top-tercile 10-slot book, union: -0.316 / -0.628 / -0.645 by seed   -0.530 ± 1.345 pooled   -1.20 ± 1.99 in 2018+
```

**This is the cleanest lever in the line and it is worth eight basis points.** Cost falls
monotonically with dollar volume (32 → 29 → 24) *and* gross rises with it (18 → 28 → 32) — the
opposite of the price-cut story, where the edge sat in the cheap names and the cost with it. The
top tercile of cell 2 — the largest, most liquid, least layered object this line has — **nets
+7.8 on the union, +13.7 on the spent names and −3.5 on the new ones**, inside ±5 in every holdout
window, with a 10-slot book at −0.5 ± 1.3. X-e was right in every particular, which is what a
prediction that is arithmetic on cost looks like; it also describes an object with no edge to
speak of.

---

## 3. M3 — the gap structure was the names

```
second touch & cell 2     gap 3-5              gap 6-10             gap 11-20
in-sample half            +56.66 (n 1,480)     +61.02 (n 2,094)     +38.68 (n 4,282)
holdout half               -6.79 (n   708)     -20.45 (n 1,111)      +7.67 (n 2,091)
```

D426's finding — the second zone that pays is the one that arrives after the first trade
resolved — is +61 on the spent names and **−20 on the new ones**; the ordering inverts (11–20 is
the only positive bucket on the holdout). X-f predicted +15 to +40; the sign was wrong.

---

## 4. Predictions — one of six

| | prediction | outcome |
|---|---|---|
| X-a | excluded long trades are the bad ones; T2, T3 pass | **the excluded are the best trades in-sample (+166); holdout +33 at the 63rd percentile** |
| X-b | T1 fails, T1b a coin | T1 fails; T1b fails outright (−56) |
| X-c | short arm unchanged through the gate | excluded shorts **+322** |
| X-d | gated long book above ungated | **below by 1.19 ± 0.85** |
| **X-e** | cost monotone in DV; top tercile −5..+10 union, ±15 holdout; book ±1 | **all as stated** |
| X-f | holdout 6–10 +15..+40 | **−20; the ordering inverts** |

The mechanism prediction was written with conviction and the stage-0 fact that motivated it —
27% of long trades on high-breadth days, concentrated in the losing years — was true and
pointed the wrong way: those days were where the *winning* years were made too. I predicted the
story and did not compute, from the spent data that was sitting there, which sign the excluded
set had. It was computable in ten seconds before the pre-registration. Memory updated.

---

## 5. What this leaves

1. **No mechanism tested here improves the construction on new names.** The breadth gate
   inverts the in-sample premium and does nothing on the holdout; the gap structure inverts on
   the holdout; the dollar-volume lever produces the line's most liquid object at a net of
   about zero.
2. **The long arm on new names is negative in every state, every window, and at the median
   (−55 in 2018+).** It is not a bounce that fails in crashes; it is not a bounce.
3. **What holds across 2,376 names is the base touch (+12), cell 2 (+26 union / +18 holdout),
   and cell 2's top-DV tercile at +21 gross / −3.5 net on new names.** That is the whole
   transferable content of thirty-two studies, and none of it clears its cost.
4. **The short arm's high-breadth trades (+322 on 60) are the one number here with a
   mechanism that read the right way** — and sixty trades on spent data, three of them
   apiece on the holdout's crash days, is a note, not a study.
5. **`holdout2` is untouched and nothing in this record is a reason to open it.**

**Disposition is the principal's.**

---

## 6. R13

Thirty-second look by object on price levels; spent data. No new data spent.

**Evidence:** `data/d432_mechanisms.json`. Runner `scripts/run_d432_mechanisms.py`.
