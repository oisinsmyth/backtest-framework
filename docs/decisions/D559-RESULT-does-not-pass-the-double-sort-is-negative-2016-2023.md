# D559 RESULT — **DOES NOT PASS**: the momentum × term-structure double sort as published is **−0.11 gross** on 2016–2023 on the 17 commodity roots, at the 25th percentile of a rotation null whose median is +0.08; it is a two-name-a-side book that loses on its short corner, and it is the two single sorts again (ρ 0.72 / 0.80), both of which are also negative

*2026-09-19. Spec committed in `000eda0` BEFORE the runner (R8). Primary window 2016-01-04 → 2023-12-29
(2,065 sessions, 96 month-ends); long window 2011-01-03 → 2023-12-29 as the declared diagnostic; **the
2024+ slice was not read** (`df`, the curve table and the strip filtered below `2024-01-01`, asserted;
last session read **2023-12-29**). Nothing admitted (R15). Nothing closed. Runner
`scripts/run_d559_double_sort.py`, output `data/d559_double_sort.json`, 59 s (the null 12 s for 2,064
offsets × 3 cells).*

**Every audit fired on its deliberate break, the two implementations of the sort agree on all 544
positioned corner cells, and the effect is absent on the window.** Fuertes–Miffre–Rallis's rule — rank
on 12-1 momentum, terciles, then the most-backwardated third of the top tercile long and the
most-contangoed third of the bottom tercile short, held a month — puts **two names a side** on 91 of the
94 traded month-ends and returns **−0.11 gross** (SE 0.31) at 20.7% vol with a **−55% drawdown**. Its
rotation null has a *positive* median (+0.08): the rotated book keeps each root's long/short tilt (PA long
35 months, NG short 40), and that tilt alone earns more than the timing does. The single sorts rebuilt
under the identical rule are −0.07 (term structure) and −0.11 (momentum), and the double sort is
correlated 0.72 and 0.80 with them: the deposit's reading that this is "trend + carry, intersected" is
what the numbers show, and on these roots and this window neither ingredient was positive (D555's
commodity sector −0.06; D556's commodity-only carry −0.26).

**One construction fact was found on the first run and is recorded in §5:** the pre-registered
eligibility rule inherited a 20-return floor on the 1-month cell, which is a calendar filter (a
19-session month) and not a signal filter. The primary stands as pre-registered; an unfloored re-run is
reported as an unpromotable diagnostic, and it is **worse** (−0.44, rank 0.05).

---

## 1. The declared verdict

| | | |
|---|---|---|
| **PRIMARY** — cell (1) EW/published, gross Sharpe 2016–2023 | **−0.112** (SE 0.31) | N1 purged: p05 −0.415, p50 **+0.081**, **p95 +0.654**, rank **0.246** → **INSIDE, below the median** |
| cell (2) vol-scaled/published, gross | +0.109 (SE 0.34) | p05 −0.640, p50 −0.022, p95 +0.644, rank 0.614 → INSIDE |
| cell (3) dollar at minimum size, **net** | +0.156 (SE 0.29) | p05 −0.408, p50 −0.021, p95 +0.430, rank 0.782 → INSIDE |
| **N2 family**, 3 declared cells | best **+0.156** (dollar) | p50 **+0.157**, p95 +0.694, rank **0.500** → **INSIDE — the family's best is the null's median**, as in D555 and D556 |

`purge_sessions` 252; 2,064 offsets enumerated, **1,562 after the purge**; SE 0 by enumeration; the
exactness guard held on 20 offsets against the plain loop and the corner sizes were preserved at each.

| prediction | | |
|---|---|---|
| **P-1** primary > 0, above N1 p95; gross point range 0.28–0.45 | −0.112; p95 +0.654; gross − net 0.015 | **fails** on every clause |
| **P-2** Sharpe uplift over the better single sort < mean uplift in that sort's vol units | better single sort = term structure (−0.065); Sharpe uplift **−0.047**; mean-return uplift **−1.44%/yr** = −0.107 in vol units | **fails** — both uplifts are negative and the Sharpe one is the *less* negative, because the double sort's vol rose (P-3) while its mean fell |
| **P-3** double-sort ann. vol > both single sorts' | **20.7%** vs 13.5% (term structure) / 13.9% (momentum) | **holds** — concentration, 2 names a side against 6 |
| **P-4** top-1 root \|share\| of the primary's P&L > 30% | **NG 23.1%** of Σ\|root totals\| (the share of the book's total is −116%, the total being negative) | **fails** — the loss is spread: NG −0.33, CL −0.15, HE −0.10, ZW −0.09 |
| **P-5** daily ρ with each single sort > 0.4 | **0.723** (term structure), **0.800** (momentum) | **holds** |
| **P-6** the 16-root dollar book fails C-d | daily σ **$3,768** | **holds** |
| **P-7** falsifier: gates green and primary below N1 p50 | gates green (every `*_raises_on_*` true); −0.112 < +0.081 | **fires: the sort did badly on this window**; the data layer is not the reason |

Three of seven held, and they are the three about the construction's *shape* (concentration, the two
mechanisms, the size). The four that carried a magnitude or a direction from the paper failed.

## 2. Performance — net and gross, the four groups

**Cell (1), EW/published — the paper's object, 0.5 × (EW long − EW short) with equal corners:**

| | gross | net (turnover) | net incl. rolls |
|---|---:|---:|---:|
| Sharpe 2016–2023 | **−0.112** (SE 0.31) | −0.127 (SE 0.31) | −0.151 |
| ann. vol · max drawdown | 20.7% · **−54.9%** (net −56.4%) | | |
| total · hit (days) · skew · kurtosis | −19.0% · 49.4% · −0.07 · 9.0 | | |
| turnover · cost | 11.4 weight-units/yr → 30.9 bp/yr | | |
| **breakeven cost** | **−20.4 bp/side** — negative: no cost line rescues a negative gross | | |
| long window 2011–2023, gross | **−0.071** (no positions in 2011; the first 12-month cell is Dec 2011) | | |

Positioned on 2,019 of the 2,065 sessions. Eras: **2011–2015 +0.03, 2016–2019 −0.44, 2020–2023 +0.08.**
Years: 2012 +0.16, 2013 +1.05, 2014 −1.24, 2015 +0.47, **2016 −0.42, 2017 +1.68, 2018 −1.67, 2019 −0.93,
2020 +0.19, 2021 −0.72, 2022 +0.97, 2023 −0.52** — three of eight primary years positive, and two of
those (2017, 2022) are the energy-backwardation years when the long corner was HO/RB/BZ for months.

**Cell (2), vol-scaled/published:** gross **+0.109** (SE 0.34), net +0.089, net incl. rolls +0.063; vol
23.3%, **max drawdown −75.3%**, hit 49.6%, skew −0.17; turnover 18.7 weight-units/yr → 46.6 bp/yr,
breakeven +13.6 bp/side; long window +0.067. **It is not dollar-neutral:** the book's net notional
averages **21% of its gross notional**, because the 0.40/σ scale is larger on the quieter corner. That
directional residue, not the sort, is the whole of the difference between −0.11 and +0.11.

**Group 2 — root-months of the primary (370 in 2016–2023; a root-month is its contribution to the
book's return, so they sum to the book):**

| | n | mean | median | ex-top-1% | ex-bottom-1% | trimmed 1% both | win | payoff | skew |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **combined** | 370 | **−5.1e-4** | **−9.4e-4** | −17.2e-4 | +6.9e-4 | **−5.1e-4** | 48.1% | 1.02 | +0.18 |
| **long corner** | 185 | **+16.8e-4** | +20.5e-4 | +8.0e-4 | +27.8e-4 | +19.0e-4 | 53.0% | 1.06 | −0.38 |
| **short corner** | 185 | **−27.0e-4** | −31.7e-4 | −42.3e-4 | −14.7e-4 | −30.0e-4 | 43.2% | 0.98 | +0.64 |

The trimmed mean equals the mean: no tail is doing the work. **The long corner earned and the short corner
lost more than that** — the median short root-month is −32 bp. The short corner was natural gas 40 of 94
months, wheat 33, cattle 17, crude 16, hogs 16: the low-momentum, contangoed names, which are the
seasonally-contangoed ones (D556: NG's basic carry reads the calendar), and shorting them paid the
roll and not the price.

**Group 3 — what the P&L depends on.** Per-root totals of the primary (units of book return): PA +0.220,
HG +0.113, ZS +0.084, ZL +0.058, GC +0.048, BZ +0.037, PL +0.025, SI +0.022, HO +0.016, ZM 0.000, ZC
−0.006, LE −0.065, RB −0.072, ZW −0.090, HE −0.101, CL −0.148, **NG −0.332**. The book total is −0.190,
so "roots to reach half the P&L" is undefined and the top-1/5/10 shares of the total (−116% / −275% /
−328%) only say that the winners do not cover the losers. **Long-corner occupancy: PA 35, RB 27, HO 24,
BZ 24 of 94 month-ends; short: NG 40, ZW 33.** Boundary ties: **0** on 96 month-ends (the tie rule never
fired). Corner sizes: **2/2 on 91 month-ends, 1/1 on 3** (n_eligible = 9 → 3/3/3 → 1/1), **2 flat months**
(2017-04-28 and 2023-04-28, n_eligible 0 — §5). n_eligible ranged 0..17, median 16; 212 root-months
missing momentum and 7 missing carry (2021-05-31: the seven grain and livestock roots have no Memorial
Day session and are not live at that month-end).

**Group 4 — the nulls** are in §1. The primary's null has a positive median because the rotation keeps
each root's membership *frequency*: a book that is long palladium a third of the time and short natural
gas nearly half of it earns +0.08 on that tilt alone at a random offset (memory: *a rotated persistent
selector keeps its state tilt*). The timing subtracts from it.

## 3. The dollar book by root, then the component line

One minimum-size contract per positioned root, **16 roots** (BZ's slot untraded, as declared), $3/$6 a
round trip + one tick, a roll two sides, 2016–2023, gross $ sorted:

| root | gross $ | σ/contract/day | size |
|---|---:|---:|---|
| **PA** | **+84,855** | **4,344** | PA (full) |
| HO | +23,432 | 2,387 | HO |
| ZS | +21,362 | 761 | ZS |
| ZL | +7,602 | 511 | ZL |
| PL | +4,460 | 805 | PL |
| HG | +2,319 | 114 | MHG |
| GC | +459 | 147 | MGC |
| SI | +380 | 368 | SIL |
| ZC | −587 | 381 | ZC |
| ZM | −860 | 550 | ZM |
| CL | −2,613 | 161 | MCL |
| ZW | −5,038 | 671 | ZW |
| HE | −5,290 | 609 | HE |
| NG | −5,709 | 148 | MNG |
| LE | −12,370 | 510 | LE |
| RB | −30,110 | 1,956 | RB |

Book total **+$82,292 gross**, of which **palladium is +$84,855 (103% of the total; 41% of Σ|root|)**;
σ per contract per day runs **$114 (MHG) to $4,344 (PA)**, a 38× range. D556's finding repeats
exactly: a one-contract book across mixed sizes is a bet on whichever full-size contract carries the
largest dollar σ, and here it is the same contract. Without PA the dollar book is −$2.6k.

**C-d-eligible sub-book** (σ ≤ $500 at minimum size: CL GC HG NG SI ZC — the five micros and corn):
gross **−0.190**, net **−0.218** (SE 0.32), σ $232/day.

| component line | minsize/dollar, 16 roots |
|---|---:|
| **C-a** net Sharpe | **+0.156** (SE 0.29); gross +0.168 |
| hit · **C-c** skew | 50.7% · **−1.07** (fails ≥ −0.5) |
| **C-d** daily σ | **$3,768** (fails ≤ $500); 7.5× the cap |
| total · max DD · cost | +$76,628 net · −$130,549 · $5,665 (818 sides, 484 of them rolls) |
| ρ with the ledger's live entry | **ABSENT** — the MACD arm's per-session P&L is not on disk |

**Not entered: fails C-c and C-d, and C-a is one instrument.** The vol-scaled dollar cell is the same
object (one contract is one contract) and was not scored twice.

## 4. The single sorts, and what the double sort adds to them

Rebuilt in-process under the identical eligibility, tie rule, `ceil(n/3)` legs and n ≥ 9 gate
(json `single_sort_check`, for the orchestrator's check against the two sibling studies — **the
cross-sectional term-structure sort** and **the cross-sectional momentum sort**):

| | gross Sharpe 2016–2023 | ann. vol | max DD | 2011–2023 | ρ with the double sort |
|---|---:|---:|---:|---:|---:|
| term-structure terciles (6 long / 6 short by carry) | **−0.065172** | 13.5% | −52.5% | −0.006 | **0.723** |
| momentum terciles (6 / 6 by 12-1) | **−0.105282** | 13.9% | −39.6% | −0.039 | **0.800** |
| double sort (2 / 2) | **−0.112035** | 20.7% | −54.9% | −0.071 | 1 |

ρ between the two single sorts 0.553. Per year, term structure: 2016 +0.04, 2017 +1.86, 2018 −1.30,
2019 +0.44, 2020 −1.57, 2021 +0.72, 2022 +0.97, 2023 −0.45; momentum: −0.68, +1.40, −1.18, −0.52, +0.01,
−0.85, +1.15, −0.42. **The double sort took two negative sorts, kept their sign, raised the vol by half
and deepened the drawdown.** The deposit predicted a Sharpe "roughly the same as either single sort, at
higher concentration risk"; the first half held and the level did not.

## 5. The eligibility floor found on the first run — amendment, diagnostic, unpromotable

The pre-registration computed 12-1 momentum as `tot12 − tot1` through D555's `signal_at_month_ends`,
whose count floor is 240 returns per 12 months scaled by L/12 — **20 returns for the 1-month cell** —
and declared a name ineligible when either cell is NaN, asking for the count. **The count is 171
root-month cells in the primary window, and it is a calendar filter, not a signal filter:** the grid is
the union of all 36 roots' sessions, livestock and grains trade ~243 sessions a year against energy's
258, so most calendar months carry 19 returns for HE and LE (36 and 29 months under 20) and many for
the grains (ZC 22, ZW 17); **April 2017 and April 2023 carried 19 for every root**, which is the two
flat months. A further 41 cells are the 12-month floor itself (HE/LE at 233–239 returns through 2020–21,
and the seven roots not live on 2021-05-31).

Memory: *measure the conditioner before building on it.* The floor was declared and its consequence was
not sized. **The primary stands as pre-registered** (that is what R8 is for), and the runner re-scores
the family with the plain calendar-month sum for `tot1` — eligibility exactly "the 12-month cell is
finite" — under json `amendment_unfloored_1m`, with its own purged null:

| unfloored 1-month cell | gross Sharpe | net | N1 p50 / p95 / rank |
|---|---:|---:|---|
| EW/published | **−0.443** (SE 0.30) | −0.455 | +0.095 / +0.674 / **0.050** |
| vol-scaled/published | −0.352 | −0.368 | +0.006 / +0.629 / 0.163 |
| dollar, net | −0.019 | −0.029 | −0.017 / +0.431 / 0.476 |
| term-structure single sort | −0.162 | | ρ with the amended primary 0.778 |
| momentum single sort | −0.259 | | ρ 0.729 |

0 flat months, n_eligible 10..17 (median 17), 2/2 corners on all 96 month-ends, 92 of 1,632 membership
cells changed, ρ 0.89 with the pre-registered primary. **The artefact was hiding loss, not edge:** the
19-session months the floor emptied were months the rule would have traded and lost. Nothing in the
amended block is promotable and it enters no verdict.

## 6. What this says against the deposit's document

`PUBLISHED_STRATEGIES.md` §6 expected net 0.25–0.40 and called FMR's 21% "the least reliable number in
this document"; this record reads **−0.13 net** for the paper's object and finds the deposit's three
qualitative claims exactly: the legs are 2 names a side, the vol is 1.5× the single sorts', and the
construction is the two mechanisms intersected (ρ 0.72 / 0.80). What the document did not say and the
record adds: on a 17-root universe the *short* corner is a seasonal-carry short (NG, ZW, livestock) and
it is where the loss lives; the vol-scaled variant is a directional book in disguise (21% net notional);
and the rotation null of a persistent cross-sectional membership has a positive median, so "beats zero"
would already have been the wrong bar.

## 7. What was not done, and what is still wrong with this

- **No de-seasonalisation of carry** (as D556), and the short corner says that is where the construction
  bleeds; a seasonal-adjusted carry is a different, declared construction. **No independent (unconditional)
  double sort**, no other tercile count, no 3- or 6-month momentum.
- **The sign audit in money checked 4 roots' best days** — on 12 of the 16 dollar roots the book was flat
  on the root's largest move; `audit_sign_book` checked every cell of the scored window grid beside it.
- **The eligibility floor of §5** is the record's own defect; the amendment is reported, not adopted.
- **The null's positive median is a property of the selector, not of the window**; a name-randomised
  control (randomise which roots fill the corners, keep the counts) would separate tilt from timing and
  was not pre-registered here.
- The long-window null was not enumerated (as in D555 and D556); the long-window primary is −0.07.
- **Nothing closed.** Three of the deposit's five commodity constructions have now been scored on this
  fixture and none is positive on 2016–2023; the deposit's own recommendation — a combined continuous
  forecast (§8) rather than a filter — is the construction that has not been built.
