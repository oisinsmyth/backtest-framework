# D573 RESULT — **DOES NOT PASS**: hedging pressure as published earns **−0.20 gross / −0.28 Sortino** on 2016–2023, **below its time-rotation median** (rank 0.076) and at the **26th percentile of the name-randomised null**; the tilt predicted before the run is exactly what the sort is (metals long 71–97 % of month-ends, natural gas and wheat short 92–98 %) **and the tilt lost** — short the energies through 2021–22, long palladium as the one winner; every cell is negative, the de-meaned cell is worse, the dollar book is −$46,439 at σ $5,504 a day; **not entered**

*2026-09-20. Spec committed in `563eafa` BEFORE the runner (R8). Primary window 2016-01-04 →
2023-12-29 (2,065 sessions, 96 month-ends, 16 eligible at every one, legs 6/4/6 throughout, no
ties, no flat months); long window 2011 → 2023 as the declared diagnostic; **the 2024+ slice was
not read on any source** (last COT release read 2023-12-29). Nothing admitted (R15). Runner
`scripts/run_d573_hedging_pressure.py`, output `data/d573_hedging_pressure.json`, 63 s (N1
35 s over 2,064 offsets exact, N3 47 s over 2,000 draws). Six audits, each proven to raise; the
signal's second path was checked at 300 cells and **keying on the report date changed 141 of
them**, which is the look-ahead R9 forbids and the reason the audit exists.*

**Four of seven numbered predictions held, and the ones that held are the ones that describe
the construction rather than its return.** The sort is the static tilt the probe said it would
be; the long leg out-earns the short leg; the daily skew is negative; the de-meaned cell is
weaker. The ones that failed are the return (negative, not 0.2–0.5), the correlation with the
term-structure sort (0.18, not above 0.4), and the sub-book's σ. The first falsifier fired: the
primary is below its rotation null's median, so **the sort did badly on this window** — not
"inside the null", badly. No TILT verdict is available because TILT required clearing the
rotation first; what this is, in the pre-registration's words, is a portfolio that was long the
precious metals and short natural gas, wheat and the energies for eight years, and lost.

---

## 1. The declared verdicts

| | observed | N1 time rotation (1,562 offsets, exact) | N3 name randomisation (2,000 draws) | |
|---|---:|---|---|---|
| **PRIMARY** — EW published, gross Sharpe / Sortino | **−0.204 / −0.278** (SE 0.36) | p05 −0.23, **p50 +0.085**, p95 +0.54; rank **0.076** | p05 −0.57, p50 +0.01, p95 +0.57 (SE 0.013); rank **0.264** | **below the rotation median** |
| vol-scaled published | −0.371 / −0.500 | rank 0.091 | | |
| dollar, net | −0.065 / −0.089 | rank 0.605 (its null's median is −0.12) | | |
| de-meaned published (secondary) | −0.229 / −0.315 | rank 0.407 | rank 0.253 | |
| N2, family of four | best −0.065 (dollar) | p50 +0.25, p95 +0.62; rank 0.225 | | |
| **verdict** | | | | **DOES NOT PASS** |

| # | prediction | value | |
|---|---|---|---|
| P-1 | primary > 0; point 0.2–0.5 | **−0.20** (net −0.21) | **fails** |
| P-2 | daily ρ with the term-structure sort on 16 > 0.4 | **+0.18** (monthly +0.16); legs shared 48 % / 54 % | **fails** |
| P-3 | PL GC PA SI long ≥ 70 %; NG ZW short ≥ 70 % | PL 0.91, GC 0.97, PA 0.71, SI 0.83; NG 0.98, ZW 0.92 | **holds** |
| P-4 | de-meaned below the primary; above its N3 only if the primary is | −0.23 < −0.20; neither clears | **holds** |
| P-5 | long leg's root-month mean > short leg's | +3.0 bp vs **−6.0 bp** a root-month | **holds** — and the short leg is where the loss is |
| P-6 | daily skew ≤ 0 | −0.37 | **holds** |
| P-7 | dollar book fails C-d; sub-book σ ≤ $500 | $5,504; sub-book **$573** | **fails** on the sub-book |
| P-8 | falsifiers | **below N1 p50: the sort did badly**; not TILT (N1 not cleared); the movement does not carry it | the first fires |

## 2. Performance — net and gross, the four groups

**EW published, 2016–2023:**

| | gross | net |
|---|---:|---:|
| Sharpe / Sortino | **−0.204 / −0.278** | −0.209 / −0.284 |
| ann. vol · total · max DD | 10.3 % · −17.3 % · **−53 %** | |
| turnover · cost | 2.3 weight units a year · 5 bp a year | breakeven −90 bp/side (there is nothing to break even) |
| 2011–2023 | −0.094 / −0.127 | |
| hit · skew | 0.51 · −0.37 | |

**Group 2 — the 1,152 root-months (96 month-ends × 12 positioned):** mean −1.5 bp, median −0.9,
both trims −1.3 to +1.8 bp, win rate 0.49, payoff 0.97. **The long leg earns +3.0 bp a
root-month (median +3.0, win 0.52) and the short leg loses −6.0 (median −6.2, win 0.46).** The
long leg's distribution is left-skewed (−1.8, kurtosis 25) with its top 1 % of root-months
84 % of its total: the metals' long contribution is a few months, and the short leg's loss is
steady.

**Group 3 — who it was.** Shares of the 96 primary month-ends spent long / short:

| PL | GC | SI | PA | LE | RB | ZM | ZL | CL | HE | HO | ZC | ZS | HG | NG | ZW |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.91/0.04 | 0.97/0.01 | 0.83/0.04 | 0.71/0.29 | 0.46/0.10 | 0.54/0.11 | 0.44/0.21 | 0.28/0.31 | 0.15/0.54 | 0.21/0.44 | 0.06/0.52 | 0.11/0.42 | 0.07/0.53 | 0.24/0.53 | 0.00/0.98 | 0.02/0.92 |

By root, in book units: PA +15.4 % of NAV, NG +6.1, ZL +5.1, GC +3.6 … HE −5.8, ZM −7.6, **HO
−12.4, CL −13.8**; 7 of 16 positive. By year: 2016 −0.38, 2017 +1.39, 2018 −1.74, 2019 +0.49,
2020 +0.06, **2021 −1.68, 2022 −1.15**, 2023 +1.72. By era: 2011–15 +0.14, 2016–19 −0.06,
2020–23 −0.30. **The sort was short crude and heating oil in more than half its months and
short natural gas in all of them, through the 2021–22 energy rally**; its one large winner was
being long palladium in 2017–2019.

**Group 4 — the nulls, and what each destroys.** The time rotation keeps each root's share of
time in each leg and moves *when*; its median is +0.085, above the observed, so any placement
of this tilt through 2016–2023 did better on average than the placement hedging pressure
chose. The name randomisation keeps the legs and draws *who*; its median is +0.007, so a random
6/4/6 commodity long-short earns nothing, as it should, and hedging pressure's choice of names
sits at its 26th percentile. Neither null is decisive against a *positive* claim; both agree
there is no positive claim here.

**The dollar book, by root, before the component line:** PA **+$207,264**, ZL +$13,878, ZW
+$13,083, GC +$5,081, NG +$4,809 … ZS −$29,666, ZM −$33,110, RB −$47,877, **HO −$137,999**;
total **−$46,439** after $10,095 of cost; σ $114 (ZC) to $4,344 (PA) a contract. One palladium
contract is +$207k in a book that lost $46k: the same instrument that carried D557, D558 and
D559 on the other side of the sort, and it is the long leg's entire case. The C-d-eligible
sub-book (CL NG GC SI HG ZC): net −0.06, σ **$573**, skew −0.50 — fails all three bars together.

## 3. The component line — nothing to enter

| | dollar, 16 contracts | sub-book, 6 roots | EW published (net, return space) | de-meaned (net) |
|---|---:|---:|---:|---:|
| C-a net Sharpe / Sortino | −0.065 / −0.089 | −0.063 / −0.087 | −0.209 / −0.284 | −0.241 / −0.331 |
| C-c skew | +0.15 | −0.50 | −0.37 | −0.18 |
| C-d σ a day | $5,504 | $573 | | |
| total | −$46,439 | −$4,720 | | |
| fails | C-a, C-d | C-a, C-c, C-d | | |

ρ with entry #2 absent (the arm's daily P&L is not on disk). **Not entered.**

## 4. What the result says about the mechanism

Hedging pressure as Basu and Miffre measure it is, on these 16 roots and this window, a
fixed ordering: the hedgers of precious metals are net short every year and the hedgers of
natural gas and wheat net long every year, so the sort held the same book for eight years with
the middle four rotating. The probe knew this before the run and the record predicted it. The
theory then needs the level to be paid, and on 2016–2023 it was not: the metals the hedgers
were short of did not carry a premium for the long (gold and silver flat, platinum down,
palladium the exception), and the roots the hedgers were long of — natural gas, wheat, and the
energies in most months — paid the *long*, not the short, through 2021–22. The de-meaned cell
tests the movement instead of the level and is worse (−0.23; −0.48 on 2011–2023), so the
premium is not hiding in the changes either. The correlation with the term-structure sort is
0.18, not the 0.4 the theory of normal backwardation predicts: the two sorts share about half
their legs and disagree on the rest, and both are negative here (term structure on the same 16
roots −0.22). Basu and Miffre's sample ends in 2011; the long window's first era here (2011–15)
is +0.14 and the two since are negative.

## 5. What was not done, and where this leaves the deposit

- No ranking or holding scan, no speculators' cell, no double sort, no disaggregated cell —
  as declared. A producer-merchant cell from 2006 would be a second construction; nothing here
  suggests it would change the sign of a level that is the same in both categories.
- **The deposit's list is now scored end to end.** Trend and carry timing (closed by the
  principal, D563); the three cross-sectional sorts (all negative or inside their nulls,
  D557–D559); basis-momentum (passes only under an amendment, D564); hedging pressure
  (negative, here). What the deposit itself parks — skewness and value — remains parked.
- **The palladium contract is the recurring object.** Four of five cross-sectional books had
  one PA contract as the largest single line, on one side or the other. Any future dollar book
  on this universe should declare PA's treatment before the sort is run.
- The 2024+ slice is unread for every root here; nothing asks for it.

**Lesson, recorded:** a positioning sort on a sixteen-name commodity cross-section is a
portfolio, not a signal — the pre-registration's tilt prediction held at 71–98 % — and the name-
randomised null is the right instrument to say so; here it was not needed, because the
portfolio lost before the question of timing arose.
