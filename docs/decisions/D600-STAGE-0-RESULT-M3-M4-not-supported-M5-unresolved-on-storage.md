# D600 STAGE 0 RESULT — **M3 NOT SUPPORTED; the de-seasonalised signal SURVIVES its rotation null and no other; T3 clears the paper's bar and not the protocol's; M4 NOT SUPPORTED; M5 UNRESOLVED on its letter and *against* the paper on its meaning.** BM(2,3) earns +0.37 gross at rank 0.90 in its rotation null and curvature −0.08 at 0.42; the primary scored on the second nearby earns **+0.70, as much as on the front** — the effect is not maturity-specific, it is the curve moving together. `BM_ds` earns +0.51 at rank 0.96 in N1, 0.93 in N3 and 0.94 as the family's best, with ρ 0.89–0.93 to the raw signal: **a twelve-month sum cannot carry a calendar, so de-seasonalisation changes almost nothing** and the survival is the primary's own. IC(1) +0.048 at t 2.2 (the paper's bar, not the protocol's 3.0), buckets monotone, 9 of 12 years; IC *rises* to +0.11 at twelve months. The book's monthly return loads **+0.006 (t 0.13, ρ 0.01)** on the intermediary capital risk factor, and after the capital ratio's lowest tercile it earns **81 bp/month *less*** than after its highest (rank 0.05). On the five energy roots the signal's correlation with the inventory surprise is **−0.13 to −0.48, negative on every root** — the storage state the paper says the effect is "inconsistent with" is in the signal. The metals' held contracts are the thin months (PL 25 contracts a day at the second nearby). Nothing follows; the ruling on the document is the principal's.

*2026-09-21. Design committed in `a3a3ff0` (its counts in `8d9a7a0`, a chain fault recorded
there) before the fixtures (D601) and this runner (R8). **Runner**
`scripts/stage0_d600_bm_closure.py`, artifact `data/stage0_d600_bm_closure.json`, 140 s.
**Three harnesses first:** the rebuilt primary +0.692157, the High4−Low4 spreading cell
+0.163294 and the nine-root non-seasonal diagnostic −0.091971 each equal D564's artifact to
1e-9; every audit passed its clean case and raised on its break inside the run (the harness on
the series rolled one session; the extended nearby series equal to D564's on every shared
output; BM(2,3) by a pandas second path on 300 cells to 1e-10, raising on the delivery threshold
shifted one month; the seasonal means by a pandas expanding groupby, raising on the mean not
shifted, 2,346 cells apart; the IC by `DataFrame.corr`, raising on the forward return unlagged;
sign in money on the M4 loading, +0.49 at t 17 and −0.59 negated; the known-at rule on 815 used
rows, raising on a week claimed one week early; the three maturity signals pairwise distinct;
`BM_ds ≠ BM`; the exactness guard on 20 offsets; the declared-outputs guard). **Read:** the strip
and the breadth fixture to 2023-12-29; D564's artifact; the D601 fixtures with every row filtered
on its observation and release dates. **Not read:** anything from 2024-01-01 on; the NASS
fixture, which does not yet exist (the key is not on this machine) — block E ran on the five
energy roots, as the design said it would. No cost, no book beyond D564's, nothing admitted
(R15). **No closure rule was declared and none is applied here.***

---

## A. M3 — the maturity-specific component and curvature: NOT SUPPORTED

| cell (EW High4/Low4 on ≤ 17 roots, scored on the nearby return) | gross Sharpe · Sortino (SE) | N1 rank (p95) | N3 rank (p95) | LONG 2011–2023 |
|---|---|---|---|---|
| **BM(2,3)** = Π(1+R2) − Π(1+R3) | **+0.374 · +0.521** (0.34) | **0.903** (+0.430) | 0.858 (+0.570) | +0.294 |
| **curvature** = BM(1,2) − BM(2,3) | **−0.079 · −0.111** (0.33) | 0.418 (+0.425) | 0.410 (+0.570) | +0.123 |
| the primary scored on **r2d** (the second nearby's return) | **+0.703 · +1.010** (0.30) | — | — | +0.585 |
| the primary scored on **r1d − r2d** (the calendar spread) | +0.163 · +0.225 (0.31) — D564's P-7 to 1e-9 | — | — | +0.234 |
| N2, family of three | best +0.511 (`BM_ds`) | p95 +0.532, **rank 0.940** | | |

Predicted: BM(2,3) > 0 above N1 p95 (**fails**, inside at 0.90); curvature > 0 above N1 p95
(**fails**, negative); the family above N2 p95 (**fails**, 0.94). Spearman with BM(1,2) at the
month-end: BM(2,3) **0.53** (inside the predicted 0.3–0.7), curvature **0.66** (predicted
positive). Eligible roots 17.0 a month, no flat month-ends; per-root positive P&L 13 of 17 for
BM(2,3), 9 of 17 for curvature. Eras: BM(2,3) +0.12 / +0.33 / +0.42 (2011–15, 2016–19, 2020–23);
curvature +0.50 / −0.13 / −0.04.

**What the r2d line says.** The second nearby's daily return, under D564's own membership,
earns +0.70 against the front's +0.69, and its share of the primary's P&L is 94 %. The paper's
"maturity-specific component that varies across the curve" is not visible at this resolution:
whatever BM(1,2) selects, the front and the second nearby move together in the holding month,
and the calendar-spread cell that would carry a maturity-specific premium is +0.16. BM(2,3) —
the same construction one pair out — is a weaker, correlated copy (ρ 0.53) inside its null.

## B. De-seasonalisation: the signal SURVIVES its rotation null, and the reason is arithmetic

`BM_ds` (the twelve-month sum of the curve increment less its expanding calendar-month mean,
three priors required): **+0.511 · Sortino +0.725** (SE 0.30), **N1 rank 0.958** (p95 +0.460,
clears), N3 rank 0.926 (p95 +0.578, inside), N2 rank 0.940 (inside); LONG +0.441; eras +0.30 /
+0.31 / +0.67; 14 of 17 roots positive. ρ(BM_ds, BM) at the month-end: **0.886 on the nine
non-seasonal roots and 0.929 on the eight seasonal ones** — the predicted ordering (seasonal
lower) **fails**; CL 0.50, NG 0.71 and RB 0.74 are the only roots below 0.9, and they are
energies, not the grains.

The design's falsifier ("inside the null → the in-sample pass was the calendar") does not fire,
and the reason is in the construction, not the data: **a sum over twelve consecutive months of a
fixed calendar-month effect is a constant** (every calendar month appears once), so
de-seasonalising the monthly increment can only shift each root's signal by that root's mean
annual curve drift and by the expanding estimate's slow motion. The document's §6.4 concern —
"a naive slope-change measure picks up the calendar rather than an imbalance" — is real for a
one-month or three-month measure and void for the twelve-month one the paper publishes. The
survival is the primary's own survival under D564's amendment, restated on a signal that is
0.9-correlated with it; it is not new evidence.

## C. T3 — the computable half of the feature evaluation

| statistic | value | the paper's bar | `FEATURE_RESEARCH.md` §11 |
|---|---|---|---|
| IC(1) cross-sectional Spearman, mean over 150 month-ends, NW t | **+0.048, t 2.17** | > 0, t ≥ 2: **holds** | t ≥ 3.0: **fails** |
| IC(3) · IC(6) · IC(12) | +0.061 (t 2.14) · **+0.102 (t 2.88)** · +0.112 (t 2.68) | "decays by six months": **fails — it rises** | — |
| buckets, mean next-month return (bp): Low4 · middle 9 · High4 | **−51 · +31 · +71**; quintiles −51, +31, +19, +68, +62 | monotone Low→mid→High: **holds** | no interior reversal: holds (Q2–Q4 wobble +31/+19/+68) |
| per-year High4−Low4 spread positive | **9 of 12** (2012 −195, 2019 −59, 2020 −215 bp/month; 2022 +628) | — | ≥ 60 %: **holds** |
| turnover | D564's 4.2 weight-units a year | — | breakeven reported in D564 |
| CPCV · PBO · incremental IC vs a library | not built | — | not claimed |

The IC that rises with the horizon is the signature of a slow signal on a slow premium: BM
ranks the roots by twelve months of curve drift, and the ranking predicts the next twelve
months' nearby return better than the next one's. That is consistent with the D564 book's
low turnover and inconsistent with a disturbance that dissipates as intermediaries absorb it.

## D. M4 — dealer balance-sheet stress (He–Kelly–Manela): NOT SUPPORTED

| # | statistic | predicted | observed |
|---|---|---|---|
| **D1 (confirmatory)** | OLS of the book's calendar-month gross return on the intermediary capital risk factor, same month; HAC(3) t; 150 months 2011-07 → 2023-12 | **β > 0, t ≥ 2.0** | **β +0.0061, t +0.13, ρ +0.013**; year-block SE of β 0.035 — **NOT SUPPORTED** |
| D1 by era | | | 2011–2015 β −0.072 (t −1.13); 2016–2023 β +0.036 (t +0.61) |
| D1 on the leverage-ratio-squared factor · on the as-pre-registered book | | | β −2.5e-5 (t −1.20, ρ −0.12) · β −0.0005 (t −0.02) |
| D2 (diagnostic) | the ratio dated *m−1* in its bottom tercile of the trailing 120 months vs its top → the month-*m* book return; null = every shift of the state | bottom > top | **−80.8 bp/month**, **rank 0.047** of 149 shifts (non-overlapping 0.056); 42 bottom and 64 top months; **years with both states: 2** (2020, 2022); lag 3: +4.7 bp |
| D3 (diagnostic) | Spearman of the cross-sectional IQR of BM with the ratio dated *m−1* | negative | **−0.056**, 12-month block 90 % interval [−0.35, +0.29]; annual +0.08 on 12 points |

The book does not load on intermediary capital — not in the pooled sample, not in either era,
not on the alternative factor, not on the as-pre-registered book. The one number that moves is
D2, and it moves the wrong way: after the capital ratio's lowest tercile the book earned 81
bp/month less than after its highest, near the bottom of its shift null, on the two years that
hold both states. The dispersion of the signal does not track the ratio. **The mechanism's
canonical instrument, the one the deposit ranked first, reads nothing.** With D583 (the
calendar), D584 (depth, volatility) and this, every free instrument of intermediary capacity
has now been read on this book and none orders it; what remains of the loop-gain story is M6's
non-decay, which any undecayed signal shows.

## E. M5 — the inventory negative control: UNRESOLVED on its letter, and the reading is against the paper

Coverage: **the five energy roots** (BZ and CL on crude ex-SPR, HO on distillate, RB on
gasoline, NG on Lower-48 working gas; EIA, known-at rule `week + 7 days ≤ session`, audited on
815 used rows). The five NASS roots wait on the principal's key; the metals and ZL/ZM have no free
history. 120 month-ends with all five present.

| statistic | bar | observed (SE) |
|---|---|---|
| mean cross-sectional Spearman of BM with the de-seasonalised 52-week inventory change, 5 roots | \|ρ\| < 0.3 holds; ≥ 0.5 fails | **−0.132** (0.099); 2011–2015 **−0.43**, 2016–2023 −0.06 |
| pooled over root-months | | **−0.248** (0.088) |
| per-root time-series Spearman | | BZ −0.25 (0.16) · **CL −0.34** (0.15) · HO −0.11 (0.21) · NG −0.17 (0.24) · **RB −0.48** (0.11) |
| the same on the de-seasonalised level | reported | cross-sectional −0.05; per root BZ −0.39, CL −0.18, HO −0.24, NG −0.43, RB −0.39 |

**Verdict on the letter: UNRESOLVED** (the largest |ρ| is 0.483, between the 0.3 bar and the 0.5
kill). **On the meaning:** the sign is negative on every root, on the change and on the level,
pooled and cross-sectionally, and −0.43 cross-sectionally in the first era. High basis momentum
— twelve months of the front rising against the second, backwardation building — goes with
inventories falling against their seasonal norm. That is the theory of storage, written in the
signal. The paper's finding that basis momentum is "inconsistent with explanations based on
storage, inventory and hedging pressure" is, on the energy roots here, not what the data show;
D584 found the hedging-pressure half inside its bar (−0.15) and this finds the storage half
outside it. **The control is a limit on the energy roots only** — the seven roots without a
series say nothing either way — and it would become a verdict if the NASS roots, when fetched,
read the same sign.

## F. Capacity at the second nearby (item 7), 2016–2023

| root | T1 median · p10 daily cleared volume | T2 median · p10 | one contract as a share of T2's median |
|---|---|---|---|
| CL | 295,175 · 142,994 | 101,537 · 64,796 | 0.001 % |
| NG · ZC · ZS | 97,905 · 148,372 · 100,352 | 42,772 · 89,538 · 49,636 | 0.002 % |
| RB · HO · ZW · ZL · ZM · BZ · LE · HE | 16,000–59,000 | 12,700–30,300 | 0.003–0.008 % |
| **GC** | **2,689 · 416** | **3,742 · 113** | 0.03 % |
| **PA** | 1,405 · **0** | 1,599 · **0** | 0.06 % |
| **HG** | 820 · 253 | 836 · 134 | 0.12 % |
| **SI** | 547 · 78 | 444 · 22 | 0.23 % |
| **PL** | **20 · 0** | **25 · 1** | **4 %** |

Capacity is not a constraint on the twelve liquid roots at any size the personal path could
reach. **The table's real content is the metals.** The construction's "first listed delivery ≥
*m*+2" lands COMEX gold, silver, copper, platinum and palladium on their *inactive* calendar
months — the exchange lists every month but the market trades the even months of gold, the
Mar/May/Jul/Sep/Dec cycle of silver and copper, the Jan/Apr/Jul/Oct of platinum — so the held
contracts print tens to hundreds of lots a day and on a tenth of days nothing at all. D564's
staleness rule (three unchanged settlements) caught the worst of it; it did not catch a
contract that settles by formula every day and trades twenty lots. A construction that rolled
the metals on their active months would be a different, declared construction; on this line it
cannot be tested, and the figure is recorded so that the D564 metals legs are read for what they
were.

## G. The five verdicts, and what each would need

| block | verdict | what a follow-up would need |
|---|---|---|
| A · M3 | NOT SUPPORTED | nothing — the curve moves together at this resolution |
| B · de-seasonalised | SURVIVES N1 (0.958), inside N3 and N2; ρ 0.9 with BM | nothing — arithmetic, not evidence |
| C · T3 | the paper's bar (IC > 0, t ≥ 2) holds; the protocol's (t ≥ 3) does not; monotone; 9 of 12 years; IC rises with horizon | a fresh slice, which this line does not have on commodities |
| D · M4 | NOT SUPPORTED | nothing — the canonical instrument reads zero |
| E · M5 | UNRESOLVED on its letter; storage in the signal on every energy root | the NASS fixture (the principal's key) to read the sign on five more roots |
| F · capacity | a table | the metals' active-month construction, if anyone ever wanted the metals |

**Not run:** T1 (unrunnable), T2 on equity index (excluded), the vol multiplier, buffering,
ranking-period variants, the instrumentation builds — as the design said. **T2 on FX is its own
pre-registration.** No session, release or observation from 2024-01-01 was read.

**Design amendments, recorded:** (i) block E ran on five roots, not ten, because the NASS key
was not on this machine at run time; the design declared this fallback; (ii) the cleared-volume
fixture starts 2015-11-19, so the capacity table's span is the design's 2016–2023 exactly, with
no earlier read.

**Memory:** two lessons worth a file — *a twelve-month sum cannot carry a calendar* (the
de-seasonalisation of an annual-lookback signal is a per-root constant, so "does it survive
de-seasonalisation" is answered by arithmetic before any run), and *the listed delivery is not
the traded one on COMEX* (a delivery-month rule lands the metals on inactive months; check the
held contract's volume before scoring a metals leg). The others are already on file.
