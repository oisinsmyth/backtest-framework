# D472 RESULT — the reversal replicates in 2010–2015 cash on SPY and IWM, and still fails the in-sample family bar on every scale: eight years cannot beat the best of eight

**Result of the pre-registered checks in D472.** Runner `scripts/run_d472_reversal_checks.py`
(`--selftest` passes; `--run` 4.9 min), artefact `data/d472_reversal_checks.json`. The D467 table
was rebuilt with RTY as a ninth root (24.1 min); **the eight original roots rebuilt
bit-identically (asserted row for row against the committed file)**; RTY fails G2 and is held
back (§3). **Nothing after 2023-12-29 was read on any fixture.**

**Under [R15](../RULES.md#r15) this record closes nothing.**

---

## 0. The headline

**The declared step-3 criterion is not met: three of its four conditions hold and the first
does not.** The overnight-leg-after-a-down-leg cell fails D470's family maximum on the
standardised scales as it failed it in dollars; and the same construction, on cash SPY and IWM in
2010–2015 — a period and an instrument the family null never priced — shows the **same sign, the
same size, clears both single-cell nulls on both symbols, and is on the right side in 11 of 12
symbol-years.**

| | | |
|---|---|---|
| Step 1 — standardised family bar (ES-W2, 8 cells, exact common-offset rotation) | z **2.78** vs family p95 **3.13** (p50 2.25); gated Sharpe **+0.70** vs p95 **+0.79** (p50 +0.48) | **fails** on both scales; NQ-W2 z 2.31 vs 2.86, Sharpe +0.62 vs +0.79, fails |
| Step 2a — SPY cash 2010–2015, gap after a down gap | **+5.51 bp** vs −0.44 on the other side; diff +5.96 (SE 3.21), **1.9 SE**; N1 p95 +5.06 ✓, N2 p95 +5.09 ± 0.10 ✓; **6 of 6 years** gated > other | **holds** |
| Step 2a — IWM cash 2010–2015 | **+7.73 bp** vs −0.12; **2.0 SE**; N1 +6.83 ✓, N2 +7.13 ✓; 5 of 6 years | **holds** |
| Step 2a — SPY cash 2016–2023 (consistency) | +6.08 vs −0.46; 1.9 SE; N1/N2 ✓; 6 of 8 years | mirrors the futures |
| Step 2a — IWM cash 2016–2023 (stands in for RTY) | +7.13 vs +3.52; 0.9 SE; 7 of 8 years | same sign, weaker |
| Step 2b — RTY futures | G4 **passes** this time (0.9969 on the 16:00 print); **G2 fails** on one reverting roll | held back as declared |

## 1. Step 1, and what the family null is centred on

The standardised bars came out **above my prediction** (z p95 3.1–3.2 against 2.2–2.6; Sharpe p95
+0.79 against 0.55–0.65) and the reason is worth recording: **the rotation preserves the
unconditional drift**, so a random 45%-gate on ES-W2 is not centred on zero but on the drift
itself (z ≈ +1.5, Sharpe ≈ +0.13), and the best of eight such cells adds roughly 1.4 SE of Sharpe
noise (SE ≈ 0.35 on 2,000 days). **The p50 of the family maximum is +0.48 on the Sharpe scale**:
eight years of one instrument cannot tell a genuine +0.70 gated component from the best of eight
random gates on a drifting series. That is the honest in-sample ceiling, and it is why step 2
existed. (A difference-between-sides statistic would be centred on zero and is the natural
declaration for any future family test of a *concentration*; it is noted here and was not run,
because choosing it now would be choosing after the answer.)

## 2. Step 2 — the replication, looked at

**SPY cash, the overnight gap (16:00 close → 09:30 open) after a negative prior gap, in bp:**

| | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| after a down gap | +2.5 | +7.0 | +4.4 | +7.4 | +9.8 | +2.7 | | −2.6 | +6.9 | +9.9 | +6.0 | +25.0 | +7.3 | −1.9 | +1.7 |
| after an up gap | +1.6 | −3.5 | −0.7 | +2.5 | −1.6 | −1.1 | | −0.6 | +2.4 | +1.6 | +3.7 | −9.9 | +5.6 | −11.4 | +2.1 |

**12 of 14 years on SPY, 12 of 14 on IWM, on the right side.** The 2010–2015 gap is not a
crisis-year effect: 2012, 2013 and 2014 carry it as clearly as 2011. Medians sit beside the means
(+6.7 / +10.0 bp), symmetric trims move them by under 1 bp, and the largest nights are
2010-10-15, 2010-08-10 and 2011-08-18 — not one day's work. The size, +6 bp of a 16:00 → 09:30
gap on the S&P, is the size the futures showed: on a $17.5k MES notional +6 bp is $10.5 a night
against the $10.66 D470 measured on ES-W2.

**Two things the cash test says that D470 could not.** First, **the prior-session gate (G-A′) is
the weaker one everywhere** (+0.2 to +1.2 SE on cash; NQ-W1's +$24.92 after a down session
was the largest dollar cell in D470 and has no cash counterpart), so the construction that
replicates is specifically *overnight after overnight*. Second, D470 read the futures' gap as
"2020–2022 only" because 2016–2019 sides were equal on the 18:00 → 09:00 window; on the cash
16:00 → 09:30 window 2017, 2018 and 2019 each show the gap. The two windows differ by the
16:00–18:00 and 09:00–09:30 legs, and the year-by-year is not identical; the sign is.

## 3. RTY

G4 passed on the close-to-close of the 16:00 print (0.9969; D462's failure was the 09:30 open on
2020-03-16). G2 failed on **2020-06-14**: the Friday 2020-06-12 roll RTYM0 → RTYU0 on 160k vs
163k contracts, a Sunday session where the archive's volume front flipped back on 6,282 vs 6,354,
and forward again on Monday — a Sunday-evening artefact above the 1% volume floor (the same
shape as 2025-09-14, which the floor caught). Held back exactly as declared; IWM 2016–2023 stood
in. The table carries RTY's rows so a later record can amend G2 for Sunday sessions; nothing here
reads them.

## 4. Predictions

| | predicted | observed | |
|---|---|---|---|
| X-a family p95 z 2.2–2.6; ES-W2 clears; NQ marginal; Sharpe p95 0.55–0.65 | | z p95 3.13 / 2.86; ES-W2 **2.78 fails**; Sharpe p95 +0.79 | **wrong**: the null is centred on the drift (§1) |
| X-b SPY 2010–2015 +2 to +5 vs −1 to +1, 1.5–3 SE, larger in 2011/2015; IWM same sign, larger | | **+5.51 vs −0.44, 1.9 SE**, spread across years not concentrated in 2011/2015; IWM +7.73, 2.0 SE | size and sign right; the regime story wrong |
| X-c SPY 2016–2023 ≥ 2 SE, +3 to +6 vs −1 to +1 | | +6.08 vs −0.46, **1.9 SE** | just under 2 SE; the numbers inside the ranges |
| X-d RTY passes or fails G4 by < 0.005; RTY-W2 positive 1–2 SE | | G4 passes; **G2 fails** | wrong gate |
| X-e runner < 10 min; rebuild ≈ 22 min | | 4.9 min; 24.1 min | right |

## 5. What this leaves, stated without overstatement

- **In-sample, the pick cannot clear a best-of-eight bar on this sample, on any scale.** That is
  a statement about the sample size and the multiplicity, not about the effect; the record's
  criterion required it and it is not met.
- **Out of family, the construction "long the overnight leg after a negative overnight leg"
  replicates on SPY and IWM cash in 2010–2015 at ≈ +6 to +8 bp a night against ≈ 0 on the other
  side, clearing both single-cell nulls, and holds its sign in 24 of 28 symbol-years over
  2010–2023.** Its cash-period family was four declared cells, and the two that were predicted
  to carry it (G-B′ on the gap) did, on both symbols.
- **The pre-registered step 3 (a component record) is not triggered by this record's own
  criterion.** Whether the replication outweighs the in-sample family failure is a judgment the
  criterion did not encode, and it is the principal's, not this record's. If taken, the
  component is one declared construction (ES or NQ overnight leg after a down leg, one micro,
  $3; in-sample gated net Sharpe +0.70 / +0.62), its promotion test is the unread 2024+ slice
  (≈ 190 gated nights, SE ≈ $8 against ≈ +$10 expected, so a weak test alone), and the cash
  2024+ reserve would add ≈ 200 more gated nights at the same sign test.
- **Continuation and the prior-session condition are not supported by any of it.**

## 6. Files

Runner · `data/d472_reversal_checks.json` · rebuilt `data/fixtures/fut_sessions_hourly.csv.gz`
(nine roots; eight unchanged), `fut_sessions_rolls.csv.gz`, meta (RTY `passes: false`) · this record.
