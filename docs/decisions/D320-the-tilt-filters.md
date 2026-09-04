# D320 — the tilt filters, and whether concentration already took the prize

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 1. The study D304 was going to be, and why it is different now

[D300's amendment](D300-AMENDMENT-cost-basis-and-what-D304-and-D305-changed.md)
says *"D304's tilt study is the next one on the list, and D300 generates its
baseline"* — then the D304 slot was spent on `d304_two_lenses.py`, a different
question, and **the tilt arm was never run.**

The evidence for it is unusually specific:

| | |
|---|---|
| **D302** | held names' median half-spread **26.31 bp** against the universe's **13.20** |
| **D264** | IBKR commission ran **0.20 bp/side (RH) to 4.15 (CLF)** *inside one volatility stratum* — a **price** effect, not a liquidity one |
| **D318** | cost is **20.90 bp/bar against gross 32.89** at the operating point — 64% of gross |

**But the study has changed, because concentration already collected part of the
prize.** D300 measured that moving from N=19 to N=2 moved held median price
**$23.72 → $75.95** and half-spread **26.67 → 21.68 bp**, for free, as a
by-product of holding fewer names.

**So the question is no longer "do tilt filters help". It is whether an explicit
filter adds anything ON TOP of what concentration already delivered** — and the
honest prior is that it does not, which §6 enters as the load-bearing prediction.

## 2. The operating point, fixed and inherited

`N_eff = 2` on the **D300/D306 construction** — top-2 per leg, `k = 5` hold — with
the `target` exit and **no overlay** (D319 closed it at this width). Nothing on
that line is re-chosen here.

**Cost per [D318](D318-the-stack-recosted.md):** held-name round trip, plus IBKR
per-share commission on the held median price.

## 3. Three declared arms, so the best of three is priced rather than presented

| arm | construction | prior |
|---|---|---|
| **spread** | exclude names whose trailing half-spread exceeds a threshold | **weakest** — it uses the per-name Corwin–Schultz estimate D302 measured as noisy, and D312 confirmed noisy inputs make rules worse |
| **price floor** | exclude names below a price level | **highest risk of a spurious pass** — this is the shape that killed D284 |
| **dollar volume** | exclude names below a median-dollar-volume threshold | closest to a real capacity constraint, and the only one that would still matter at size |

**Three thresholds per arm, set at the 10th, 25th and 40th percentile of the
universe on that arm's own variable**, declared as percentiles rather than levels
so they do not need re-tuning per arm. **Plus the unfiltered control: 10 cells.**

**Run at `N_eff` = 2 AND at `N_eff` = 19**, because Q6 is about how much
concentration already took — that contrast is the study's second question and it
costs one extra sweep.

## 4. Two controls, and neither is optional

**A. Price-matched.** For each treatment cell, a control that excludes the same
number of names with the same persistence, chosen so its **held median price
matches the treatment's to within 5%**. **A filter that improves cost by holding
pricier names has discovered the price level, not a filter.** D284 died of exactly
this and the record says so.

**B. Persistence-matched random exclusion.** Same exclusion count, same run-length
distribution, applied at unrelated times — **not re-drawn per bar.** A per-bar
random exclusion churns where the treatment persists, which is the defect that
voided D291's veto arm (2.4× the entries, up to 7×, 87 cells).

**Assertion [4] makes that defect visible rather than merely avoided:** the
per-bar variant must be shown to produce materially more entries than the
persistent one, in the same runner.

## 5. Cost basis — and this study inverts D307's rule on purpose

**D307 established that comparing two EXIT rules requires a common round trip,
because the spread difference between them is incidental.** Here it is the
opposite: **the filter's entire mechanism is to change which names are held and
therefore what they cost.** Charging a common round trip would define the
treatment effect away.

**So per-cell held round trip is primary**, and **the price-matched control is
what keeps that honest** — it holds names at the same price and therefore faces
the same round trip, so a treatment that beats it is not merely paying less.

**Common-basis figures are reported beside every cell**, because their difference
decomposes the effect: *common* says whether the filter picks better names,
*per-cell* says whether it also pays less, and the gap between them is how much of
the result is cost rather than selection.

## 6. Statistics and predictions

**Net Sharpe primary** (FINDINGS §7), with net bp/bar, gross, held half-spread,
held price, commission and **breakeven round trip** beside it. The filters do not
change exposure — the book stays fully invested — so net bp/bar is directly
comparable across cells here.

Three predictions are against, and Q2 is load-bearing.

| | prediction |
|---|---|
| **Q1** | every filter cuts the held median half-spread at every threshold. **Mechanical — if it fails the filter is not doing what it is named** |
| **Q2** | **no filter beats its PRICE-MATCHED control on net Sharpe at any threshold, at `N_eff` = 2.** *Against — load-bearing.* Any gain is the price level, which concentration already took |
| **Q3** | **the spread arm is the weakest of the three**, because it conditions on the noisy per-name estimate. *Against that arm* |
| **Q4** | gross falls under every filter at every threshold — a filter removes opportunity |
| **Q5** | at `N_eff` = 19 the filters move held price and spread **more** than at `N_eff` = 2, because concentration has already moved them at 2. **This is the "concentration already took it" claim, measured** |
| **Q6** | commission falls proportionally **more** than spread does under the price floor, since IBKR's charge is per share and therefore purely a price effect while the spread is not |
| **Q7** | the persistence-matched random exclusion does **not** beat the unfiltered control — a sanity check on the null |
| **Q8** | the dollar-volume arm gives the smallest loss of gross per basis point of cost saved, being closest to a genuine capacity constraint |

**Q2's bar is stated in full, because I have written it carelessly three times
(D313 Q3, D315 QB2, D319 Q5):** *"beats" means beats while being profitable AND
surviving its own null.* **A cell that beats its control by losing less does not
falsify Q2.**

## 7. Stop conditions

- **Q2 confirms** → the tilt axis closes. Concentration already collected the cost
  benefit and there is nothing left on this surface. **Expected.**
- **Q2 fails** → a filter genuinely adds beyond the price level. It needs its own
  confirmation before anything else, benchmarked against the price-matched control
  and never against the unfiltered book.
- **Q1 fails** → misimplemented; nothing else is read.
- **Q7 fails** → the null is broken and no cell's p-value means anything. Report
  that and stop.

## 8. Assertions

1. **[1] Reproduction.** The unfiltered cell reproduces D306's and D318's
   `N=2/target` and `N=2/none` to floating point.
2. **[2] The filter bites.** The held set differs from the control's, and held
   median half-spread, price and dollar volume all move in the declared direction
   at every threshold.
3. **[3] The price-matched control matches** — held median price within 5% of its
   treatment — **and is a distinct book from it.** A control that is the treatment
   proves nothing.
4. **[4] THE D291 DEFECT IS MADE VISIBLE.** The persistent random exclusion and a
   per-bar re-drawn one are both constructed, and the per-bar variant must be
   shown to produce **materially more entries**. A control whose defect is only
   asserted in prose is not controlled for.
5. **[S] SPREAD BASIS.** Round trips come from the names held, are reported
   per-cell **and** common, and the check **FAILS against the universe median**.
6. **[C] Cost dimensions** against d295's 52.1893; doubled form rejected.
7. **[5] Every cell is a distinct book.**
8. **[6] The self-test raises** on a book handed free money inside the mask.

## 9. Scope

**Out:** the entry signal; the exits, beyond inheriting `target`; the gate; `k`;
width, beyond the declared 2 and 19; the overlay (D319); and any filter built from
a variable not in the three declared arms.

**This study can only close a surface or find one small effect.** It does not
change the signal, and §1 of [STACK.md](../STACK.md) is clear that the signal is
where the ceiling is. **If Q2 confirms, the entry signal — frozen since D293 —
is the whole of what remains.**

## 10. Files

`docs/decisions/D320-the-tilt-filters.md` (this record) · runner and data to
follow, in separate commits. Prior evidence: `data/d300_width.json`,
`data/d302_*.json`, `data/d306_width_exits.json`, `data/d318_stack_recost.json`.
