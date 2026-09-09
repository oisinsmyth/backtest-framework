# D402 RESULT — the overnight gap SURVIVES: the contamination is real, detectable, and not where the edge lives

**V1 — SURVIVES, decisively.** D280's structural claim stands. The gap IC gets **stronger** on clean
bars (−0.01746 against a committed −0.01531, **1.14×**) and is **1.8× stronger in the most liquid
quintile** than the thinnest. **The stale-open hypothesis is refuted, and by the test designed to
discriminate it.**

**Number.** Pre-registered as `D390` and **renumbered to `D402` on 2026-09-09**. `D390-D399` is reserved for the `worktree-signal-hunt-part2` branch (`fb2af62`), which master had already stepped out of once — the D163 re-cost went D389 -> D390 -> D400. I took D390 anyway, having checked `ls docs/decisions/`, which PICKUP's own warning says is insufficient and will collide. **Master takes D400 and upward.** The commit hashes below are historical and unchanged: pre-registration `6843a39`, result `c6c63f6`.

Pre-registration `6843a39` predates this file (R8). Measurement only: no cell scored, nothing
admitted, no holdout read, nothing fetched. Reuses D280's own module for fixture, signal, split and
`ic_series`.

---

## 1. `[REP]` first — this is D280's object

```
  [REP]  ALL gap IC -0.01531 (t -4.71) vs D280's -0.01531
  [REP] QUAL gap IC -0.01255 (t -3.45) vs D280's -0.01255
```

Reproduced to five decimals before any filter. **Everything below is about D280's measurement, not a
lookalike.**

---

## 2. The contamination is REAL and it is common

```
  flagged share of 2,232,440 out-of-sample bars
    S1 open == prior close        5.84%
    S2 open==high==low==close     0.51%
    S3 open at session extreme   13.16%
    S4 zero/absent volume         0.54%
    S1-S4 combined               17.58%
    S5 cheap (bottom quintile)   20.05%
    S6 thin  (bottom quintile)   19.94%
```

**Q1 predicted the exact-print signatures would flag under 2% and it is falsified by nearly ten
times.** `open == prior close` **exactly** fires on 5.84% of bars — one bar in seventeen has an
opening print bit-identical to the previous close. This is a real data property and it was worth
looking for.

**And the signatures work.** `corr(gap, intraday)`:

```
      contaminated (S1-S4): -0.1564   n   392,539
                     clean: +0.0082   n 1,838,232
        thin/cheap (S5|S6): -0.0628   n   669,569
               liquid/dear: -0.0027   n 1,561,202
```

**A stale print is corrected by the first real trade, so an artefactual gap must reverse — and the
reversal is confined almost exactly to the flagged bars: −0.1564 against +0.0082.** The detectors
detect. **Q4 held emphatically.** D280's pooled `corr(gap, body) = −0.0429` is now explained: it is
the contaminated 17.6% showing through a pooled average.

---

## 3. But the edge is not there — P1

```
universe                               cut        IC       t  vs committed       obs
    ALL     exact-print clean (not S1-S4)  -0.01599   -4.61         1.04x 1,838,232
    ALL       liquidity clean (not S5-S6)  -0.01706   -4.51         1.11x 1,562,246
    ALL                   CLEAN (neither)  -0.01746   -4.49         1.14x 1,349,269
   QUAL                   CLEAN (neither)  -0.01507   -3.75         1.20x   327,060
```

**Removing every contaminated bar makes the edge LARGER, not smaller** — 14% larger on ALL, 20% on
QUAL, on 60% of the original sample with significance intact. **The decision rule required "within
25% with sign and significance retained"; it strengthened.**

Within the signatures themselves: **S2 gives +0.01790 (t 0.65) — insignificant and wrong-signed**,
and S3 gives −0.01630, close to baseline. **S1 and S4 could not be scored**: their bars are too
scattered for a cross-sectional IC to have enough names per day. **That is a real limit of this
test** and is stated rather than glossed — the 5.84% of `open == prior close` bars are excluded by
the CLEAN cut but their own IC is unmeasured.

---

## 4. P3 — the discriminating test, and it runs the OTHER way

```
    $ volume quintile:      Q1        Q2        Q3        Q4        Q5
                      -0.01231  -0.01154  -0.01616  -0.01543  -0.02194
                   t     -4.93     -3.57     -4.31     -3.72     -4.62

       price quintile:  -0.01438  -0.01390  -0.01442  -0.01978  -0.01713
                   t     -5.05     -4.00     -3.72     -4.87     -4.51
```

**The gap IC is 1.8× stronger in the most liquid quintile than the thinnest** (−0.02194 against
−0.01231), and stronger in dear names than cheap ones.

**A print artefact must concentrate where prints are unreliable. This concentrates where they are
most reliable.** The two hypotheses predicted opposite gradients — §4 of the pre-registration said so
before the run — and the observed gradient is the one a real overnight repricing predicts.

**V3 is falsified, and Q3 with it — my own against-myself prediction.** I expected the liquidity
gradient to invert because D284 was killed by exactly that, and it did not.

---

## 5. Predictions scored

| | prediction | outcome |
|---|---|---|
| **Q1** | exact-print signatures flag under 2% of bars | **FALSIFIED by ~10×.** S1 alone is 5.84%, S1–S4 combined 17.58% |
| **Q2** | P1 survives within 25% | **HELD, and better** — the IC strengthens 1.14× (ALL) and 1.20× (QUAL) |
| **Q3** | **AGAINST myself: the liquidity gradient inverts** | **FALSIFIED.** It runs the other way — 1.8× stronger in the most liquid quintile |
| **Q4** | contaminated bars show materially more gap→intraday reversal | **HELD emphatically.** −0.1564 against +0.0082 |
| **Q5** | QUAL is cleaner than ALL, so the two narrow on CLEAN bars | **HELD, weakly.** The gap narrows 0.00276 → 0.00239 |
| **Q6** | **AGAINST myself: at least one assertion fires on the first run** | **FALSIFIED.** Nothing fired; the run was clean first time. Three studies running that I predicted an assertion failure, and this is the first time the prediction was wrong |

**Three of six falsified, and two of the three were aimed at myself.**

---

## 6. Assertions

```
  [REP]   ALL -0.01531, QUAL -0.01255 -- D280's committed values to five decimals
  [LAG]   lagged -0.01531 vs unlagged -0.01733, gap 2.02e-03 -- the lag is load-bearing
  [SIG]   every signature's flagged share reported; S1-S4 proved EXACT by a one-ULP unflag probe
  [SPLIT] 253 opens seen, 0 holdout paths, no unlock exists in the module
  [X]     {'REP': True, 'LAG': True, 'SIG': True} -- all raise
```

---

## 7. What this establishes, and what it explicitly does not

**Establishes:**
- **D280's structural claim survives the test it had never faced.** The overnight concentration is
  not an opening-print artefact.
- **Roughly 17.6% of out-of-sample bars carry a detectable print artefact**, with a −0.1564 gap→
  intraday reversal confined to them and none on the rest. **That is a reusable data-quality fact
  about this fixture**, independent of D280.
- **The edge is strongest where prints are most reliable** — the liquid, dear quintile.

**Does NOT establish, and this is the part that must not be lost:**
- **Nothing about tradeability.** D280's own runner already records that the IC does not survive into
  money at N=25 — *"the ascending short LOSES 11–18 bp per night overnight"* — and that *"a rank IC
  describes the WHOLE cross-section; a top-N book lives in ONE TAIL."* **That correction stands
  untouched.** This record removes a doubt about the measurement, not about the money.
- **S1 and S4's own ICs are unmeasured**, their bars being too scattered for a cross-sectional IC.

**PICKUP §1a may keep its headline.** It should gain the liquidity gradient, because *where* the
effect is strongest is new and is the opposite of what the universe's cheap tail would suggest.

---

*Result committed 2026-09-09, separately from the pre-registration, per R8. Measurement only: no cell
scored, nothing admitted, no holdout read.*
