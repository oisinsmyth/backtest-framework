# D462 RESULT — ES, NQ and YM one-minute regular-hours fixtures pass five gates from 2016-01-04; the archive lacks the index futures' day session on most days before then; RTY is held back on one limit-down day

**A DATA BUILD (R15): admits nothing; no study, no return.** Spec `de75a63` and its ADDENDUM predate
the gate results. Build 17.9 min (26 archive files, 1.1 billion rows read in 10-million-row
chunks); gates 1 min. **Committed: `fut_ES_rth_1m.csv.gz`, `fut_NQ_rth_1m.csv.gz`,
`fut_YM_rth_1m.csv.gz` (14–17 MB each), `fut_index_sessions.csv.gz`, `fut_index_rolls.csv.gz`,
`fut_index_1m.meta.json`. NOT committed: `fut_RTY_rth_1m.csv.gz` (G4 failed as pre-registered).**

```
selftest: DST both ways; the 15:59 bar in and 16:00 out; unmapped instruments dropped; front by full-day volume; the roll row; third-Friday expiry with single-digit years
ES  1,391,074 bars  3,626 sessions  2010-06-07 .. 2026-09-09  40 contracts     usable from 2016-01-04
NQ  1,390,947 bars  3,627 sessions                                              usable from 2016-01-04
YM  1,390,274 bars  3,627 sessions                                              usable from 2016-01-04
RTY   907,580 bars  2,365 sessions  2017-07-10 .. 2026-09-09  37 contracts     usable from 2017-07-10 -- G4 FAIL, not committed
```

---

## 1. The gates

```
       G1 |r| > 1% bars (<= 40)   G2 rolls fwd/revert/multi, days-before-expiry [min,p50,max]   G3 bars p50, short (early-close-like / other)   G4 vs ETF: open-to-close, close-to-close     G5 coverage -> usable start
ES     28 on 22 named days          65 / 0 / 0   [4, 5, 5]                                        390, 128 (86 / 40 -- Sep-2010..2012 holidays, 4 March-2020 halts)   SPY 0.9957, 0.9985   PASS   2016-01-04
NQ     27                           65 / 0 / 0   [3, 4, 5]                                        390, 129 (84 / 40)                                                    QQQ 0.9974, 0.9997   PASS   2016-01-04
YM     31                           65 / 0 / 0   [4, 5, 5]                                        390, 131 (81 / 40)                                                    DIA 0.9955, 0.9990   PASS   2016-01-04
RTY    20                           36 / 0 / 0   [4, 4.5, 5]                                      390,  94 (58 / 36)                                                    IWM 0.9899, 0.9982   FAIL   2017-07-10
```

**G1.** Every listed bar sits on a named day: 2015-08-24, 2018-02-05, 2018-12-19, the March-2020
sessions, 2022-06-15 / 09-21 / 10-13 (FOMC afternoons), 2024-08-05, 2024-09-18, 2025-04-07/09.
Nothing unexplained. **G2.** 65 rolls on 16 years of ES/NQ/YM, every one forward, one per quarter,
**4–5 trading days before the third Friday** — the volume crossover falls on the Monday–Tuesday of
expiry week, later than the 7–9 days X-c predicted. **G3.** Every full day has 390 bars; the short
sessions are the early closes (210–226 bars) plus the 2010–2012 holiday Mondays the archive carries
at 120 bars and the four halted March-2020 sessions at 376–377. **G4.** The open-to-close leg is
0.9955–0.9974 on ES/NQ/YM against a 0.995 bar, and the single largest divergence on every root is
**2020-03-16**, the limit-down open (ES 4.2 points of return difference; the cash open at 09:30
was not the futures' 09:30 open). **G5 (added by the ADDENDUM).** Coverage of the equity calendar:
**21% in 2010, 27% in 2011, 42% in 2012, 82–88% in 2013–2015, ≥ 96% from 2016** — see §2.

---

## 2. The finding about the archive

**Before 2016 the archive carries the index futures' evening bars and not their day session on
most days.** On 2010-06-08, ES's front contract has 189 bars, every one between 18:00 and 20:32
ET and none in regular hours, on a day the archive holds 1,252 minute bars for ZN and 1,377 for
6E; the missing days are Tuesday–Friday almost without exception and Mondays are complete. The
symbology is not the cause (one mapping interval per contract; the definition schema agrees), and
a concurrent session's ES panel built from the same archive has the same session counts
(3,502). **This is a property of the vendor's early GLBX history for the equity index products,
and the four pre-registered gates could not see it** — G3 scored bars per present session and a
session that is absent is not short. The ADDENDUM added G5 and the usable window; **no study
reads a day before 2016-01-04** (ES, NQ, YM) or 2017-07-10 (RTY). X-a's "≈ 4,080 sessions" was
wrong by 455 for this reason, and the usable sample is eight years, not sixteen.

---

## 3. RTY, held back as pre-registered

RTY's open-to-close correlation with IWM is **0.9899** against the declared 0.99; ex 2020-03-16 it
is 0.9993, and the close-to-close leg passes at 0.9982. The cause is a market event, not a parse
error, and the gate still fails as written. **The rule was "a gate that fails stops the commit",
so the RTY bar fixture is not committed**, its rows remain in the sessions and rolls tables
(flagged `passes: false` in the meta), and D463 runs without it. A documented-event exemption
for G4 is a change to a gate after seeing its number and is left for a later record to declare.

---

## 4. Predictions — three of six

| | prediction | outcome |
|---|---|---|
| X-a | ES/NQ/YM ≈ 1.55–1.65 M rows, ≈ 4,080 sessions; RTY ≈ 0.9 M, ≈ 2,300 | **1.39 M / 3,626** (the missing early day sessions); RTY 0.91 M / 2,365 ✓ |
| X-b | G1 5–30 per root on 2015-08 / 2018-02 / 2020-03 / 2024-08, none unexplained | 20–31 ✓, none unexplained ✓ |
| X-c | 65 rolls ES/NQ/YM, 36–37 RTY, modal 7–9 days before expiry, zero reversions | 65 ✓, 36 ✓, **4–5 days**, zero ✓ |
| X-d | G3 p50 390, sub-380 = 3 early closes a year + ≤ 5 other | 390 ✓, early closes ✓, **+ 2010–12 holiday Mondays and the March-2020 halts** |
| X-e | G4 ES/SPY ≥ 0.999, NQ ≥ 0.998, YM ≥ 0.998, RTY ≥ 0.995 | **0.9957 / 0.9974 / 0.9955 / 0.9899** — every one dragged by 2020-03-16 |
| X-f | build under 40 min | 17.9 ✓ |

---

## 5. What the data layer now is

Three committed, gated one-minute regular-hours fixtures for ES, NQ and YM, 2016-01-04 to
2026-09-09, front month by measured volume, the contract on every row, no stitching; a session
table with the 09:30 open and 16:00 print per day; a roll table. **Any intraday study on these
three instruments reads a fixture, not the archive. Cross-day returns must guard the contract
column (D448's rule); the extended session, the micros and the other 37 roots are separate
builds; RTY needs a gate decision before it is used.**

**Disposition is the principal's.**

---

## 6. R13

A data build; no forward return, no candidate, no holdout. Builder
`scripts/build_fut_index_1m.py`; provenance and gate numbers in `data/fixtures/fut_index_1m.meta.json`.
