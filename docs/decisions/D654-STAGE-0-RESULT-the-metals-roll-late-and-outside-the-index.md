# D654 STAGE 0 RESULT — eight roots qualify as run, but the robust core is two: gold and silver drain late, outside the index window, mostly as a roll, at a quarter of the receiving contract's volume, with a hedge leg that trades; the energies were mis-measured by my own contract rules

*Renumbered 2026-09-28 from D653: the opening model's v2 pre-registration took D652 on main while this study sat on an unmerged branch, and the three studies of that branch (the crack spread, the open-interest Stage 0, the metals roll) each moved up one. Commits before the merge cite the old number.*

*Design: [D654](D654-STAGE-0-DESIGN-when-open-interest-leaves-the-expiring-month.md) (`c651f6b`), committed alone
before the builder existed (R8). Builder and report: `scripts/build_fut_oi_expiry.py`; fixture
`data/fixtures/fut_oi_expiry_cycles.csv.gz` (gitignored, manifest by hash) and its meta; numbers
[`data/stage0_d654_oi_expiry.json`](../../data/stage0_d654_oi_expiry.json) and the disclosed diagnostic
[`data/stage0_d654_oi_expiry_diag_dcarry10.json`](../../data/stage0_d654_oi_expiry_diag_dcarry10.json). **Open
interest and cleared volume only; no price was read; the 2024+ files were never opened.***

## The answer in one line

**As run, eight roots qualify** (6C, GC, SI, HG, ZC, ZS, ZW, ZM), so the pre-registered route is a no-expiring-leg
pre-registration. But the qualifying set depends on a cycle rule the design left open. **Only gold, silver and
(barely) the Canadian dollar qualify under both rules tried**, and my contract rules mis-measured the monthly energy
roots. **The recommendation is a pre-registration scoped to GC and SI**, with 6C as a declared marginal third, put to
the principal before any price is read.

## 1. The build, and the check that it reads the right figures

8 yearly `statistics` files (2016–2023, 5.80 GiB), 8 processes, **0.4 minutes at 72 % of the pool**; 850,320
(root, contract, reference session) rows for 26 roots. The windowed id mapping (D520/D521) is imported from the
breadth builder, and a reissued id takes the label of the window containing each record (selftest).

**Known answer:** summed over contracts, CL's and GC's open interest reproduces
[D497](D497-PRE-REG-open-interest-against-price-does-the-four-quadrant.md)'s root totals
(`fut_open_interest_daily.csv.gz`) **exactly on 70 % of 1,971 sessions, within
0.1 % on 79 % (CL) and 90 % (GC)**; the worst gap is 1.5 % on CL and 9.2 % on GC (Thanksgiving 2018). CME publishes
each day's figure more than once (2018-11-23's at 09:19 Friday, Sunday and Monday), and the values change between
publications on about a fifth of (contract, day) pairs. This record keeps a figure's **last** publication; D497 keeps
the last one usable by 10:00 the next session. Taking the **first** publication instead matches D497 on 2.5 % of
sessions, so the reference-date labels are right and the residual is later revision. For a 30-day drain ratio it is
immaterial.

**G-FND passes on all 16 first-notice roots** (share of cycles with under 25 % of open interest left the day after
the declared first notice day: 1.00 on every one). The rulebook rule holds.

## 2. The table, as run

| root | cycles | half-drain d | IQR | outside share | roll share | M5 | M6 hedge | Q1–Q5 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **GC** | 39 | −5 | 3.0 | 0.74 | 0.86 | 0.247 | 0.167 | all pass |
| **SI** | 40 | −6 | 2.2 | 0.72 | 0.85 | 0.231 | 0.151 | all pass |
| HG | 40 | −8 | 2.2 | 0.67 | 0.68 | 0.126 | 0.258 | all pass |
| ZC | 32 | −8 | 3.0 | 0.66 | 0.55 | 0.133 | 0.354 | all pass |
| ZS | 39 | −7 | 2.0 | 0.68 | 0.54 | 0.123 | 0.414 | all pass |
| ZW | 40 | −10 | 3.0 | 0.56 | 0.61 | 0.106 | 0.335 | all pass |
| ZM | 39 | −9 | 2.5 | 0.62 | 0.54 | 0.102 | 0.413 | all pass |
| 6C | 32 | −3 | 0.0 | 1.00 | 1.13 | 0.387 | 0.065 | all pass |
| ZL | 39 | −9 | 3.0 | 0.63 | 0.50 | 0.096 | 0.399 | fails Q4 |
| HO / RB | 91 / 93 | −6 / −8 | 2.0 / 3.0 | 0.66 / 0.62 | 0.59 / 0.67 | 0.080 / 0.078 | 0.48 / 0.47 | fail Q4 |
| CL / NG | 26 / 58 | −4 / −8 | 1.0 / 2.0 | 0.43 / 0.37 | 0.05 / 0.36 | 0.020 / 0.085 | 0.32 / 0.59 | **mis-measured** (§3) |
| 6E 6J 6B 6A 6S | 32 each | −2 to −3 | ≤ 1.8 | 1.00 | 1.15–1.38 | 0.37–0.47 | 0.000–0.041 | fail Q5 |
| PL, PA | 31, 32 | −7, −6 | 2.0, 1.2 | 1.00 | 0.92, 0.90 | 0.46, 0.47 | 0.026, 0.003 | fail Q5 |
| ZN ZB ZF ZT UB TN | 9–24 | −3 | ≤ 1.0 | 1.00 | 0.99–1.05 | 0.39–0.65 | 0.000 or none | fail Q5 |

*Half-drain d: business days before the deadline at which half the open interest of d = −30 has gone. Outside share:
of the drain, the part not on BD4–BD11 of the month (the padded index window) or a CL/NG fund-roll day. Roll share: the
receiving month's gain over the expiring month's loss. M5: the heaviest five-day outside-window roll flow over the
receiving contract's volume on those days. M6: the hedge contract's volume over the receiving contract's.*

## 3. What depends on a choice I made, stated plainly

**The cycle rule.** The design did not say which contracts count as a cycle. The builder counts one only if the
expiring month was the root's **largest by open interest at d = −30**, so that thinly held serial months (GC's
January, March, …) do not produce meaningless ratios. As a disclosed diagnostic (not a second verdict), the same
report with the test at **d = −10** qualifies only **6C, GC and SI**: by d = −10 the grains and copper are already
half drained, so they fail the "largest" test by construction (0–7 cycles). **Neither rule is neutral; the roots
that qualify under both are GC, SI and 6C.**

**The receiving rule mis-measures the monthly energies.** "Receiving = the later delivery with the largest open
interest at d = −20" picks CL's heavily held **December** contracts over the next month: CL's September 2016
expiry "rolls" into December 2016 at a roll share of 0.02, where its June expiry rolls into July at 1.04. The
same happens to some silver and grain months (SI July → December). **CL's and NG's roll shares and M5 are artefacts,
not measurements.** Prediction 3 (CL the most likely root to qualify) cannot be scored; a monthly root needs
"receiving = the next listed month", and that is a new measurement, not a patch here. HO and RB fail Q4 (M5 0.08)
under the rule as run.

## 4. The predictions

| | prediction | outcome |
|---|---|---|
| 1 | G-FND passes on metals, Treasuries, grains | **held**: 1.00 on all 16 |
| 2 | Treasuries and FX drain in the last seven days, IQR ≤ 2, roll ≥ 0.8, then fail Q5 | **held**, except 6C, which passes Q5 at 0.065 (6E 0.041) |
| 3 | CL qualifies | **not scorable**: mis-measured (§3) |
| 4 | grains and metals have outside share ≥ 0.5 | **held**: 0.56–0.74 |
| 5 | two to five roots qualify | **failed as run** (eight); three under the diagnostic rule |

## 5. What the robust core says

For **gold and silver**, the expiring month's open interest leaves **in the last week before first notice**
(half gone at d = −5 and −6). **About three quarters of the drain falls outside the index window**, because the
first notice day sits at the month's end, after BD5–9. **About 85 % of it reappears in the receiving month.** On its
heaviest five outside-window days that roll is **a quarter of the receiving contract's volume**, stable in every year
(GC 0.18–0.37, SI 0.17–0.28). The contract after the receiving one trades **15–17 % of the receiving one's volume**,
so a receiving-against-hedge spread can be held without touching the expiring month. That is the flow the
principal's rule leaves tradeable, and D635's index window does not contain it.

The grains qualify as run but sit on the Q4 bar (ZM 0.102, ZW 0.106, several years below 0.10), and they vanish
under the diagnostic rule. **6C** qualifies on a hedge leg of 0.065 against a bar of 0.05, with 30 % of its open
interest still open after the last trading day (currency futures are held to delivery).

## 6. Routing

The pre-registered route is **"three or more roots qualify: draft a no-expiring-leg pre-registration for the
principal."** Given §3, **the recommendation is to scope it to GC and SI**, with 6C declared as a marginal third and
the grains excluded, and to write it before any price is read: short the receiving contract against the hedge
contract into the outside-window drain of the last week before first notice, flat before the expiring month's first
notice day, personal book, price nulls on the construction's own placements, costs from D651's map, forward power
stated. The principal decides whether it is written.

## 7. ADDENDUM 2026-09-28 — the diagnostic is not evidence against the early drainers; the ranking the pre-registration uses

Laid out root by root for the principal, §3's diagnostic (the cycle test at d = −10) turns out to reject by
construction any root that is already half drained by then — copper and every grain hold only 43–60 % of their
d = −30 open interest at d = −10 (§2's profiles) — so their 0–7 cycles under it say nothing about their flow. The
fair comparison is the as-run numbers with the size test year by year:

| root | M5 median | years below 0.10 of 8 | roll share | reading |
|---|---:|---:|---:|---|
| GC | 0.247 | 0 (0.18–0.37) | 0.86 | core |
| SI | 0.231 | 0 (0.17–0.28) | 0.85 | core |
| HG | 0.126 | 0 (0.11–0.20) | 0.68 | candidate: clean, half gold's size |
| 6C | 0.387 | 0 (0.29–0.48) | 1.13 | marginal: hedge leg 0.065 against 0.05; 30 % held to delivery |
| ZC | 0.133 | 1 | 0.55 | outer: excluded from the pre-registration |
| ZS | 0.123 | 2 | 0.54 | excluded |
| ZW, ZM | 0.106, 0.102 | 3, 3 | 0.61, 0.54 | excluded |
| ZL, HO, RB | 0.096, 0.080, 0.078 | 6, 7, 8 | — | fail Q4 |

§6's recommendation is widened accordingly, and fixed here before any price is read: **GC and SI are the primary**,
**HG and 6C are declared secondary cells**, and the grains are excluded on their size record. The pre-registration
is [D655](D655-PRE-REG-selling-the-metals-roll-after-first-notice.md).
