# D583 STAGE 0 RESULT — **NOT SUPPORTED.** The reporting calendar does not order the basis-momentum book: the ten sessions into a quarter-end earn **−0.37 bp/day less than the rest (quarter-block SE 3.02, t −0.12), rank 0.47 in the 63 enumerated placements** (p05 −3.77, p50 −0.29, p95 +5.92) and 0.34 among the 44 that do not overlap; the quarter-ends rank **0.23 among the 495 four-month subsets** and sit 2.7 bp/day *below* the other eight month-ends; December is the *worst* quarter (−2.99 against +4.22 bp/day, above the other three in 4 of 12 years); ΔPRE is positive in 5 of 12 years, and both eras are inside their null. Both gates fail; M7 fails on every one of its four declared parts. The mechanism's persistence statistic (T3) moves the predicted way at 0.7 SE. Nothing follows.

*2026-09-21. Design committed in `00100c5` before the runner (R8). **Runner**
`scripts/stage0_d583_bm_quarter_end.py`, artifact `data/stage0_d583_bm_quarter_end.json`, 8 s.
**Harness first:** the rebuilt book's PRIMARY-window gross Sharpe equals D564's artifact,
+0.692157 to 1e-9, before any calendar statistic; every audit passed its clean case and raised
on its break inside the run (the harness on the series rolled one session, 0.678 against 0.692;
the calendar by a pandas groupby second path on 163 month-ends, raising on the mask shifted one
session; the placement null's zero offset and the subset {3, 6, 9, 12} each reproducing the
observed statistic; the sign in money, +10.0 bp on a synthetic PRE effect and −10.0 at rank 0.00
negated; the PRE and POST masks disjoint and distinct, raising on the same mask twice; the
declared-outputs guard). **Read:** the breadth fixture and the settlement strip for the 17
commodity roots to 2023-12-29, as D564 read them; D564's artifact for the harness. **Not read:**
any session from 2024-01-01 on. No cost, no book beyond D564's, nothing admitted (R15).*

---

## 1. The sets, as counted

| | |
|---|---|
| positioned sessions | 3,225, 2011-07-01 → 2023-12-29 |
| quarter-ends | 50, of which **13** are year-ends (the design wrote 12: 2011-12 through 2023-12 is thirteen; T2's per-year count uses the 12 full years 2012–2023 as declared) |
| other month-ends | 100 |
| PRE sessions (10 × 50) | 500 |
| POST sessions (5 × 49 within the window) | 245 |
| book, gross bp/day | +2.66 on the LONG window; +3.09 on PRIMARY 2016–2023 |

## 2. The tests against their predictions

| # | predicted | observed | verdict |
|---|---|---|---|
| **T1** | ΔPRE > 0, rank ≥ 0.95 of 63; profile peaks inside PRE | **ΔPRE −0.37 bp/day**, SE 3.02, t −0.12; **rank 0.468** (p05 −3.77, p50 −0.29, p95 +5.92); non-overlapping rank 0.341 of 44; profile peak at session **−28**, outside PRE | **fails** |
| **T1b** | ΔQ > 0, rank ≥ 0.95 of 495 | **ΔQ −2.72 bp/day, rank 0.229** (p50 −0.01, p95 +6.29); the quarter-ends sit *below* the other month-ends | **fails** |
| **T2** | December > Mar/Jun/Sep pooled; ≥ 8 of 12 years | December PRE **−2.99** against **+4.22** bp/day; December above in **4 of 12** | **fails, inverted** |
| **T3** | corr(d_m, d_{m+1}) across roots higher after quarter-end months | +0.039 after quarter-end months, −0.007 after others; difference **+0.045, SE 0.066** (year-block) | direction as predicted, 0.7 SE; no gate |
| **T4** | ≥ 8 of 12 years ΔPRE > 0; post-2016 not weaker | **5 of 12**; 2011–2015 ΔPRE −1.52 (rank 0.35, 18 quarters), 2016–2023 +0.27 (rank 0.50, 32 quarters) | fails the count; "not weaker" holds only because both are zero |
| **T5** | reported | ΔPOST **−7.84** bp/day; ΔPRE without the settlement session +1.26; ΔPRE at the other month-ends **+3.49** | diagnostic |

**Decision rule:** T1 inside its null and T1b inside its null → **NOT SUPPORTED**, on both gates,
with the ordering (T2) inverted and the year count (T4) at chance. The pre-registered variant
(`ffill = 1`) gives ΔPRE +0.17 at rank 0.63; the terciles cell +0.07 at rank 0.58. There is no
cell, window or variant in which the reporting calendar is visible.

## 3. What the profile showed

The pooled quarter-end profile (mean gross bp/day by session relative to the quarter-end
settlement, 50 events) has no shape at the reporting date. The ten PRE sessions sum to +23 bp
against +51 bp for the same ten sessions at the other month-ends. The quarter-end session itself
is **−10.3 bp** pooled and **−38.8 bp** in December; the five POST sessions sum to −23 bp
pooled. The peak of the 46-session profile is at −28, a session with no meaning in the
mechanism.

**December is a turn-of-the-year effect with the wrong sign for M7.** Its PRE ten sum to −30
bp; its POST five sum to **+65 bp** (+40.5, +17.0, +24.6, +11.6 on the first four sessions of
January). The book earns its December in the first week of January, after the snapshot, when
the mechanism says balance sheets re-expand and disturbances dissipate faster. That is a
month-end / new-year regularity on the commodity curve, unpromotable here (the line's forward
slice is spent, D574) and parked as a fact, not a lead.

**The year-by-year ΔPRE is two-sided and large:** 2014 −20.4, 2015 +16.7, 2017 −10.7, 2022 +10.8
bp/day, on a book that averages +2.66; the quarter-block SE of 3.02 says the 50-event mean is
not resolvable below about ±6 bp/day. **Ten of the 500 PRE sessions are ±170 bp or larger**, and
four of the ten are 2020-03-18 to 2020-03-25 (+200, −244, −170, +192); the PRE mean is +2.35,
its median +4.22, its symmetric 1 % trim +2.56, ex-top +0.48 and ex-bottom +4.42 — a two-sided
tail, no single-side dependence, and the mean *below* the median by 1.9 bp says the left tail
is the slightly heavier one.

**The best four-month subsets are not the reporting months.** The top five of the 495 all
contain October and November (`{5, 6, 10, 11}` +11.7 bp/day, `{2, 5, 10, 11}` +9.0, …). That
is an unpre-registered, post-hoc reading and is recorded only so no one later mistakes it for
a discovery: it is the maximum of 495 draws whose p95 is +6.3.

## 4. What this says about the mechanism

`BASIS_MOMENTUM.md` §4.2 predicts that the regulatory snapshot lowers the arbitrage loop's gain
into the reporting date, that disturbances then persist longer, and that basis momentum is
stronger around those dates, year-end most. The book shows none of it: not the window, not the
month set, not the ordering, not the year count. The one statistic that moved the predicted way
is the persistence of the monthly curve disturbance across roots (T3, +0.045, SE 0.066), and that
is a 0.7 SE difference on 50 against 100 months, consistent with nothing.

Two readings are open and this record cannot separate them. Either the loop-gain story is wrong
for these 17 roots, or the reporting calendar is the wrong instrument for it (the G-SIB and
leverage-ratio snapshots bind the largest dealers' *repo and derivatives* books, and the
commodity futures curve may clear through capital that is not so measured). M4 — the He–Kelly–
Manela capital ratio, the canonical series the deposit ranks first — would separate them, and it
is a fetch and a separate design if anyone wants the answer; with the line's forward slice spent
there is no construction that could use it, so this record does not recommend it.

**Kills on the deposit's own terms:** the mechanism's second-ranked derivative fails on a seen
book with an exact null and every audit raising. Together with D564 (the book itself, +0.69
gross PRIMARY, inside its rotation null once purged) and D574, basis momentum on these roots is a
weak positive book whose named mechanism does not show in its calendar.

## 5. What this record did not do

It did not run M1–M5 (§5 of the design); did not build the equity-index financing rate or the
calendar-spread liquidity measure; did not pre-register any calendar construction; did not
read the funding or option fixtures; did not read any session from 2024-01-01 on. No cost was
applied and no component line is due: the book scored is D564's, whose ledger line stands.

**Design amendment, recorded:** the year-end count is 13, not 12 (§1); no statistic depended on
the figure.

**Memory:** none new. The D578 (era, years, level path) and D580 (window sized to the profile,
overlapping placements named) lessons were carried and did their work: the non-overlapping rank
and the session profile are what show the window empty rather than merely unlucky.
