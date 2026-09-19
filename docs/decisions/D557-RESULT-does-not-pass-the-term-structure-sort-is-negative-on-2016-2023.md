# D557 RESULT — **DOES NOT PASS**: the cross-sectional term-structure sort as published is **−0.21 gross** on 2016–2023, at the **14th percentile** of a rotation null whose **median is +0.16** — a randomly re-timed copy of the same membership earns more than the sort's own timing, because the membership is mostly a fixed per-root tilt (natural gas short 66 of 96 months, palladium long 60) and the tilt is what the null keeps

*2026-09-19. Spec committed in `e3a5785` BEFORE the runner (R8). Primary window 2016-01-04 →
2023-12-29 (2,065 sessions, 96 month-ends); long window 2011-01-03 → 2023-12-29 as the declared
diagnostic; **the 2024+ slice was not read** — last session read 2023-12-29 on the breadth fixture,
the curve table and the strip, `windows.reserved_from` = 2024-01-01. Nothing admitted (R15).
Nothing closed. Runner `scripts/run_d557_xs_term_structure.py`, output
`data/d557_xs_term_structure.json`, 38 s (null enumerated in 12 s against a 98 s projection).*

**Both fixture metas carry `all_gates_pass`, every audit fired on its deliberate break, and the sort
did badly on this window.** Rank the 17 commodity roots each month by the annualised front–next
basis, long the six most backwardated, short the six most contangoed, equal weight, hold a month:
**−0.21 gross, −0.22 net** (SE 0.33) on 2016–2023, **−0.08** over 2011–2023. The vol-scaled form of
the same membership is **+0.02**; the one-contract dollar book is **+0.28 net** and, as in D556, it is
**one contract of palladium** (+$200k of a +$176k total; without it, −$24k). Three of seven
predictions held — the ones about the sort's *shape* (long leg above short leg, negative skew,
C-d failure); the four that inherited a magnitude or a mechanism claim did not, one of them (ρ with
carry timing 0.49 against a 0.5 bar) by a hair.

---

## 1. The declared verdict

| | | |
|---|---|---|
| **PRIMARY** — EW/published, gross Sharpe 2016–2023 | **−0.207** (SE 0.33) | N1 purged (252 sessions each end, 1,562 of 2,064 offsets): p05 −0.38, **p50 +0.16**, p95 +0.76, rank **0.139** → **INSIDE, below the median** |
| vol-scaled/published, gross | +0.019 (SE 0.36) | p05 −0.54, p50 +0.00, p95 +0.68, rank 0.51 |
| sort/dollar, **net** at minimum size | +0.275 (SE 0.31) | p05 −0.43, p50 +0.02, p95 +0.53, rank 0.86 |
| **N2 family**, 3 declared cells | best **+0.275** (sort/dollar) | p50 +0.19, **p95 +0.77**, rank 0.60 → **INSIDE** |

| prediction | | |
|---|---|---|
| **P-1** primary > 0, above N1 p95; gross point range 0.2–0.45 | **−0.207**, p95 +0.758 | **fails** |
| **P-2** \|ρ\| daily with CM carry timing > 0.5 | **+0.489** (monthly +0.453) | **fails**, by 0.011 — half the variance is shared, not "the same mechanism" |
| **P-3** long leg's root-month mean > short leg's | **+4.0e-4** vs **−7.5e-4** | **holds** |
| **P-4** daily skew < 0 | **−0.47** | **holds** |
| **P-5** vol-scaled within ±0.15 of EW | +0.019 vs −0.207: gap **0.226** | **fails** — the weighting *is* the difference, §3 |
| **P-6** dollar book fails C-d | σ **$4,924**/day | **holds** |
| **P-7** falsifier | gates green, primary **below N1 p50** | **fires: the sort did badly on this window**; the fixture is not the reason |

## 2. The null is the finding

The profile of null Sharpe against the offset (stored in full, `offset_profile_primary`):

| shift of the membership (sessions) | −252 … −21 (purged) | −21 … −1 (purged) | +1 … +21 (purged) | +63 … +126 | +252 … +504 | +504 … +1,032 | −504 … −252 | −1,032 … −504 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| mean null Sharpe | **+0.99** | +0.47 | −0.15 | +0.29 | −0.02 | **+0.33** | **+0.55** | −0.10 |

A membership read **one to twelve months in the future** earns +0.99 — look-ahead, purged, as in
D555. But a membership **one to two years in the future** earns +0.55 and one **two to four years
stale** earns +0.33, and the surviving null's median is **+0.16** with the observed at −0.21. That
is not timing: **35% of root-months are long and 35% short, and per root the legs are nearly
constant** — NG short 66 of 96 months, ZW 70, ZC 67, HE 61; PA long 60, RB 60, BZ 60, HO 54. A
rotation by a common offset preserves each root's long/short *frequency* exactly and re-times only
the exceptions, so the null is mostly the fixed tilt "short the seasonal-contango grains and gas,
long the energies and palladium" evaluated at a random phase — and that tilt earned on 2016–2023
at most phases. The sort's own phase is among the worst 14%. This is the rule in memory: *a rotated
persistent selector keeps its state tilt; predict the null median from the cell baselines, not
zero.* The pre-registration predicted the null implicitly at zero and the runner's rank is against
the null as declared; the median is reported beside it as the record requires.

## 3. Performance — net and gross, the four groups

**EW/published (0.5 × (EW long − EW short), 12 names positioned on average of 17, dollar-neutral in
weight), 2016–2023:**

| | gross | net (turnover) | net incl. rolls |
|---|---:|---:|---:|
| Sharpe | **−0.207** (SE 0.33) | −0.219 | −0.253 |
| ann. vol · max drawdown | 12.1% · **−52.4%** (cumulative simple-return units, negative convention) | | |
| hit (days) · skew · kurtosis | 51.3% · **−0.47** · 7.6 | | |
| turnover · cost · breakeven | 5.6 weight-units/yr → 14.1 bp/yr · breakeven **−44.8 bp/side** (the gross is negative; no cost saves it) | | |

**Vol-scaled/published** (sign × 0.40/σ, risk-weighted within legs, not dollar-neutral): gross
**+0.019** (SE 0.36), net +0.003, vol 14.7%, max DD −47.7%, skew −0.33, turnover 9.9/yr → 23 bp/yr,
breakeven 2.8 bp/side; long window +0.05. **P-5's 0.23 gap is the finding about weighting:** the EW
book gives NG (σ $148 a micro but ~50% annualised vol), RB, HE and PA the same weight as gold and
copper, so the equal-weight book's return is mostly those four — three of which are its largest
losers (NG −0.164, RB −0.124, HE −0.067 of a −0.205 total). Scale them to equal risk and the sort is
flat, not negative: the *sort* carries nothing either way; the equal-weight form carries the
high-vol names' 2016–2023 path.

Eras: **2011–2015 +0.25**, 2016–2019 −0.02, 2020–2023 **−0.34**. Years: 2011 +0.74, 2012 +0.43,
2013 +0.44, 2014 −1.88, 2015 +0.98 | 2016 −0.38, 2017 +1.56, 2018 −1.47, 2019 +0.71, 2020 **−1.96**,
2021 +0.73, 2022 +0.83, 2023 −0.15 — four of eight primary years positive, and 2020 is the worst.
**Named:** March 2020 (−12.2%, the worst month) was **long RB −7.1%, BZ −5.5%, HO −3.1%** — the
backwardated energies on the way down; May 2020 (−11.1%) was **short CL −4.9%, BZ −3.0%, RB −2.6%**
— the same names, now the most contangoed after the April collapse, on the rebound. The sort was
on the wrong side of crude twice in three months because the basis lags the price. The worst
root-month is RB 2020-03 (−7.1%); the five best are all natural gas (+2.5% to +3.7%, three short,
two long), whose 53% annualised vol is the highest of the 17 (gold 14%, copper 21%).

**Group 2 — root-months (1,148 on 2016–2023, book-return units, contribution = sign × simple
return / positioned count):**

| | n | mean | median | ex-top-1% | ex-bottom-1% | trim both | win | payoff | skew |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **combined** | 1,148 | −1.79e-4 | **+1.70e-4** | −4.24e-4 | +1.91e-4 | −0.54e-4 | 51.1% | 0.90 | **−1.32** |
| **long leg** | 574 | **+3.97e-4** | +7.69e-4 | +1.75e-4 | +7.96e-4 | +5.76e-4 | 54.7% | 0.95 | −1.75 |
| **short leg** | 574 | **−7.55e-4** | −4.09e-4 | −9.88e-4 | −4.70e-4 | −7.03e-4 | 47.6% | 0.83 | −0.80 |

The mean sits below the median on every line: the left tail is doing the work, and it is in the
long leg (skew −1.75 — the backwardated energies on the way down in 2020). The long leg earns
(P-3), the short leg loses on every statistic: **the contango leg was short natural gas, wheat, corn
and hogs through 2016–2023, and those rallied.** Backwardation paid; contango did not punish.

**Group 3 — what the book depends on.** The total is negative (−0.205), so "roots to reach half the
P&L" has no answer and the share figures are relative to a loss: the largest single contributor is
**PA +0.143** (long 60 months; its own Sharpe +0.83), then HG +0.043, GC +0.040, ZL +0.036, PL
+0.031; the losers NG **−0.164**, RB −0.124, CL −0.078, HE −0.067, LE −0.048, BZ −0.047. Nine of 17
roots positive. **Eligibility:** 17 eligible on 95 of 96 primary month-ends (6/5/6), **10 on
2021-05-31** (the CBOT grains and the livestock carry no session that day; 4/2/4); over 2011–2023
also 12 on 2014-12-31 (4/4/4). **0 boundary ties, 0 flat months.**

**Group 4 — nulls** in §1 and §2: SE 0 by enumeration, purge 252, 1,562 surviving offsets.

## 4. The dollar book decomposed, then the component line

One minimum-size contract per positioned root, **16 traded** (BZ ranked, its slot untraded), 2016–2023,
net dollars by root, sorted:

| PA | HO | ZW | PL | ZM | GC | ZL | ZC | ZS | HG | CL | NG | SI | HE | LE | RB |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **+199,872** | +39,765 | +12,676 | +10,050 | +6,992 | +6,863 | +6,456 | +5,083 | +5,022 | +3,002 | −2,750 | −5,523 | −6,512 | −8,384 | −27,824 | **−68,421** |

Total **+$176,366**; the top contributor is **113% of it** (without palladium, **−$23,506**); per-contract
daily σ runs **$114 (MHG) to $4,344 (PA)** — a 38× range inside one "equal-weight" leg. Cost $12,380
(1,927 sides, 1,574 of them rolls). The sign of the dollar book is the sign of palladium's 2016–2023
path at full size, exactly D556's finding on the same contract.

| | sort/dollar (16 roots) | C-d sub-book (CL NG GC SI HG ZC) |
|---|---:|---:|
| **C-a** net Sharpe | **+0.275** (SE 0.31); gross +0.295 | **+0.003**; gross +0.036 |
| hit · **C-c** skew | 52.4% · **−1.03** | · σ **$475** |
| **C-d** daily σ · max DD | **$4,924** · −$187,380 | total +$163 over 8 years |
| ρ with the ledger's live entry | **ABSENT** — the MACD arm's per-session P&L is not on disk | |

**Not entered: fails C-a (0.28 < 0.5), C-c and C-d, and the C-a figure is one instrument.** The
vol-scaled dollar cell is not a fourth cell: `sign(sign × 0.40/σ)` is the membership, the same object.

## 5. Comparability with carry timing

D556's cell A rebuilt in-process on the 17 commodities only: **−0.257** on 2016–2023 (D556's own
CM sector figure −0.26), +0.15 on 2011–2023. ρ with the sort **+0.489 daily, +0.453 monthly**; the
vol-scaled sort against carry timing +0.458. The deposit's "treat as one mechanism for correlation
purposes" is half right: the two share the sign of the basis on the roots whose basis rarely
changes sign, and differ on the ten middle-ranked names timing holds and the sort leaves flat.

## 6. What was not done, and what is still wrong with this

- **No de-seasonalisation**, as declared. NG (mean month-end carry −0.235) and HE (−0.198) are in
  the contango leg by calendar, not by inventory; the theory-of-storage claim the deposit cites is
  about the *deviation* of the basis from its seasonal, and this record scored the raw basis as
  the deposit's §4 states it. A seasonal-adjusted basis is a different, declared construction.
- **The null's median is +0.16, not zero, and the pre-registration did not predict it.** §2 says
  why; the rank is against the null as declared. A name-randomised null (memory: run it too) would
  separate the tilt from the phase and was not declared here.
- **The EW cell is weight-neutral and risk-concentrated**; the vol-scaled cell is risk-balanced and
  weight-long-or-short. Neither is the paper's exact object (FMR use equal weights on a larger
  cross-section where one name's vol matters less); at 17 names the choice moves the Sharpe by 0.23.
- **The long-window null was not enumerated**, as in D555 and D556; it is a 40-second read.
- Two sibling studies — the cross-sectional momentum sort and the double sort — are separate records.
