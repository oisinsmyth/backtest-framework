# D570 RESULT — **DOES NOT PASS**: the F/H harvest spread earns **+0.40 gross / +0.54 Sortino** on 2016–2023, the schedule is real (the always-on short **loses** at −0.80 bp a day and the rolled cousin under the mask sits at the **99.3rd percentile** of its placement null), but **the construction's own twelve-placement null puts September → November third**: the same short spread formed two months earlier — **July → September on X/F — earns +1.24**, and the rolled cousin beats the F/H pair per positioned day in sample; **the object was chosen on the seen thirteen-year table and the seen table already said otherwise on 2016–2023**; net +0.41 at one contract, skew −1.31, fails C-a and C-c, **not entered**

*2026-09-20. Spec committed in `2503321` BEFORE the runner (R8), on the principal's word, written
as seen. Primary window 2016-01-04 → 2023-12-29 (2,065 sessions, 497 positioned, 24 positioned
months, eight windows); long window 2011 → 2023 (39 months, thirteen windows) as the declared
diagnostic; **the 2024+ slice was not read on any source** (WASDE filtered first, 978 of 1,170
rows). Nothing admitted (R15). Runner `scripts/run_d570_soybean_harvest_spread.py`, output
`data/d570_soybean_harvest_spread.json`, 13 s. Seven audits and the N2-by-construction check,
each proven to raise; the current-year-median gate break is inert on this data and the json says
so.*

**Eight of ten numbered predictions held and the two that failed are the two the pass rule
stands on.** The primary is positive, its months hit 0.62, its tail is where the mechanism
said (worst month −0.64 %, σ $57 a day), the gate's four windows all paid, 2012 is not in the
primary window and without it the long table still pays 10 of 12, and cost is 16 % of gross.
But the F/H pair placed at September is not the best placement of its own construction — the
July placement on X/F is, by a wide margin — and the rule-rolled cousin, which D569 set aside
for its October roll, earns more per positioned day in sample than the pair chosen to replace
it. **Both falsifiers the pre-registration wrote for exactly this fired.**

---

## 1. The declared verdicts

| | observed | null / control | |
|---|---:|---|---|
| **PRIMARY** — B, short F / long H, Sep → Nov, gross Sharpe / Sortino 2016–2023 | **+0.397 / +0.545** (SE 0.30) | N2, twelve placements of the same construction: **third** (m7 +1.24, m8 +0.77, **m9 +0.40**); median of the other eleven −0.25 | **not best of twelve** |
| secondary — B gated on stocks-to-use (seen) | +0.680 / +1.063 (12 months) | family best; still below m7 | |
| diagnostic — A, the rolled cousin under the same mask | **+0.800 / +1.236** | N1 placement (1,562 offsets, exact): p05 −0.84, p50 −0.41, **p95 +0.654**; rank **0.993** | clears |
| control — A always on | **−0.611 / −0.829**; net −0.753 | −0.80 bp a positioned day; off-window −1.29 | the short is right only at harvest |
| per positioned day | **B +0.53 bp · A masked +0.67 bp** | | **B loses to A** |
| **verdict** | | | **DOES NOT PASS** · ledger **fails C-a, C-c** · avatar **unsupported, no claim** |

| # | prediction | value | |
|---|---|---|---|
| P-1 | B > 0; point 0.5–1.2 | **+0.40** | holds; **below the point range** |
| P-2 | months hit ≥ 0.60, median > 0; windows ≥ 0.75 | 0.62, +0.07 %; 11 of 13 | **holds** |
| P-3 | B per day > 0 and > A masked; control ≤ 0 | +0.53 vs **+0.67**; control −0.80 | **fails** on the object clause |
| P-4 | A masked N1 rank ≥ 0.90 | **0.993** | **holds** |
| P-5 | B best of twelve on both windows; placement 11 negative | third / second; m11 −0.25 | **fails** |
| P-6 | gate (seen): gated ≥ ungated on mean and hit; opens 2016, 2021, 2022, 2023 | +0.59 % vs +0.24 %; 4 of 4 vs 9 of 11 | **holds** (seen) |
| P-7 | ex-2012 mean ≥ +0.25 %, ≥ 9 of 12; 2012 ≤ 55 % | +0.28 %, 10 of 12, 50 % | **holds** |
| P-8 | worst month > −1.5 %; worst window > −0.5 % | −0.64 % (Sep 2020); −0.17 % (2014) | **holds** |
| P-9 | dollar σ positioned < $150 | **$57** | **holds** |
| P-10 | cost < 20 % of gross | **16 %** ($296 of $1,838) | **holds** |
| P-11 | falsifiers | **B not best of twelve; B per day below A**; A above N1 p50; gated hit not below ungated | two fire |

## 2. Performance — net and gross, the four groups

**B, one pair, 2016–2023:**

| | gross | net |
|---|---:|---:|
| Sharpe / Sortino, all sessions | **+0.397 / +0.545** | **+0.315 / +0.431** |
| ann. vol · total · max DD | 0.84 % · +2.75 % · −2.60 % | +2.18 % · −2.61 % |
| daily skew | **−1.52** | |
| cost | 7.1 bp a window (four sides at $3 + $6.25 on a ~$50,000 leg) | breakeven 8.6 bp/side against 1.8 modelled |
| 2011–2023 | +0.504 / +0.751 | |

**Group 2 — the 24 positioned months:** mean +0.11 %, **median +0.07 %**, hit 0.62, worst −0.64 %
(September 2020), best +0.96 % (September 2023). On 2011–2023, 39 months: mean +0.18 %, median
+0.09 %, hit 0.67. By window: 2016 +0.62 %, 2017 +0.21, 2018 −0.09, 2019 +0.23, 2020 +0.05,
2021 +0.36, 2022 +0.21, **2023 +1.17** — seven of eight, and 2023 is 42 % of the in-sample total.
The long table: 2011 +0.74, **2012 +3.47**, 2013 +0.03, 2014 −0.17, 2015 +0.08, then as above;
11 of 13, mean +0.53 %, half of it 2012.

**Group 3 — by month (2011–2023, 13 each):** September **+0.27 %** (hit 0.77), October +0.05 %
(0.62), November +0.21 % (0.62). Smooth, as D569 said; and the daily book underneath is
left-skewed (−1.52): the short's losses are sharp days inside months that end positive.

**Group 4 — the nulls, and the one that decides.** The schedule is real: the always-on short
spread loses every month but September and November (by calendar month, bp a day: Jun −2.8, Jul
−3.7, Aug −2.2, **Sep +0.7**, Oct −0.4, **Nov +1.0**, Dec −1.4), and the rolled cousin under the
harvest mask is the 99.3rd percentile of 1,562 placements of that mask. **But the construction's
own null says the harvest is the wrong placement of it.** B's exact rule — a survivable pair,
short the nearer, held three months — placed at each calendar month:

| placement | months | pair (first window) | Sharpe 2016–23 | Sortino | Sharpe 2011–23 |
|---|---|---|---:|---:|---:|
| m7 | **Jul–Sep** | **X/F** | **+1.24** | **+1.97** | **+0.61** |
| m8 | Aug–Oct | X/F | +0.77 | +1.16 | +0.18 |
| **m9 (primary)** | **Sep–Nov** | **F/H** | **+0.40** | +0.54 | +0.50 |
| m11 | Nov–Jan | H/K | −0.25 | −0.34 | +0.21 |
| m5, m6, m10 | | | −0.05, −0.04, −0.06 | | |
| m1–m4, m12 | | | −0.42 to −0.67 | | |

The short X/F spread held from July — the new-crop November contract against January, formed
when the crop's size is still open — earns three times the F/H harvest spread on 2016–2023 and
is the best placement on both windows. The harvest window catches the tail of a pre-harvest
widening that starts in July. **This is corn's D568 result with the sign of the season reversed:
the declared window was late, and the construction's own placement profile said so once it was
run.** The profile was not seen before this run and is seen now, for all twelve placements.

## 3. The object — the seen table already answered

D569 recommended the F/H pair over the rolled cousin on the thirteen-year mean (+0.53 % against
+0.27 %), on smoothness across the three months, and on cost (four sides against eight). All
three were true and none was the question. The pre-registration's primary window is 2016–2023,
and on that subset of the *same seen table* the cousin led every year but 2023 (A +0.81 / +0.29
/ −0.20 / +0.43 / +0.17 / +0.50 / +0.34 / +1.17 against B +0.62 / +0.21 / −0.09 / +0.23 / +0.05
/ +0.36 / +0.21 / +1.17). The F/H pair's thirteen-year lead is 2012 (+3.47 against +1.61) and
2013 (+0.03 against −1.08), both outside the primary window. **I chose the object on the wrong
window of a table I had in front of me.** The record says so because the next pre-registration
on any root will face the same choice: when the seen table covers both objects, compare them on
the window the primary statistic is scored on, and predict that comparison.

## 4. The state variable and the avatar

The gate (seen, declared, non-promotable) did what D569 said: open 2016, 2021, 2022, 2023, four
of four, +0.59 % against +0.24 % ungated, and its cell is the family's best at +0.68 gross /
+0.61 net with skew +0.54 — the one cell here that clears C-a. It is a declared secondary, it
sits below the July placement, and its four windows are four windows. It is not carried
anywhere by this record. The COT figure is recorded (commercial net short falls through the
window in 8 of 13, seen); no avatar claim was made and none is.

## 5. The component line — fails C-a and C-c; not entered

| | one ZS short F / one ZS long H, Sep → Nov |
|---|---:|
| **C-a** net Sharpe / Sortino | **+0.413 / +0.575** (gross +0.49 / +0.69) |
| **C-c** skew | **−1.31** |
| **C-d** daily σ, positioned · all | **$57 · $29** |
| total · cost · max DD, 2016–2023 | +$1,542 · $296 · **−$1,325** |
| by window, $ | 2016 +301, 17 +88, 18 −37, 19 +76, 20 +13, 21 +176, 22 +151, 23 **+776** |
| **C-b** ρ with entry #2 | not computable; expected near zero by instrument and clock |

**Not entered.** C-a and C-c both fail; the construction is third of its own placements. The
row goes on the scored-constructions table with the gated and rolled cells beside it.

## 6. What was not done, and what this record leaves

- **The July → September X/F placement is a null cell, seen now, and not licensed.** It is the
  strongest thing on the soybean curve in this programme and it was found by the null, which is
  the null's job. Any construction on it is a new Stage 0 that starts from the twelve-placement
  profile — which is now seen for every placement, so a pre-registration on it would be as seen
  with the ZS 2024+ slice as its only test, the same position this record was in.
- **The ZS 2024+ slice is unread.** Nothing here asks for it.
- **The negative daily skew** (−1.52 in return space, −1.31 in dollars) sits under a monthly
  table that looks smooth; the ledger's C-c is on the daily series and that is where it fails.
- **The always-on control's −0.80 bp a day** is the second time (after D569) the soybean curve
  has shown the nearby strengthening through the growing season; that is the other side of the
  same mechanism, unseen as a schedule, Stage 0 material.

**Lesson, recorded:** when two candidate objects are both in the seen table, compare them on the
primary window before choosing, and run the construction's own placement null before the
schedule's — the schedule can be at the 99th percentile while the construction sits third of
twelve.
