# D528 ADDENDUM 14 — the `a2` test, the entry/forecast decoupling, and a stop that was inside its own entry

Date: 2026-09-15. Runners: `working/d528_a2_test.py`, `d528_decouple.py`, `d528_paired.py`.

**Nothing admitted (R15). Reserved slice NOT read.** Wide 5-minute fixture, 2010 → 2026-04-10.
Corrected chain (`slope_ok` dropped, drift alignment kept — ADDENDUM 12). Every figure
out-of-time: fitted on days < 2020-01-01, reported on days ≥ 2020-01-01.

The principal asked for both tests run **independently**, with **every design choice and every
confound enumerated explicitly and shown alongside the result**. Those enumerations live in the
two runners' docstrings (D1–D13 and C1–C5 in `d528_decouple.py`; D1–D8 and C1–C3 in
`d528_a2_test.py`) and are printed by the runners, so they travel with the numbers.

---

## 1. `a2` buys nothing, and the power lever is a third of what was projected

`a2ok` = median |bar return| over the trailing window ≥ 4 ticks. It was calibrated for 1-minute
data. Tested exactly as `slope_ok` was, so the two are comparable.

**The `a2_on` arm reproduces ADDENDUM 13 bit-for-bit** (micro, X=2.0: n 10,256, P(target) 10.0%,
gross −$1.35, net −$5.93), which validates the harness.

| universe | X | Δ candidates | ΔP(traverse) | Δgross | Δnet | Δcost |
|---|---|---:|---:|---:|---:|---:|
| micro | 2.0 | **1.27×** | **+0.0084** | +0.25 | +0.20 | +0.05 |
| micro | 3.5 | **1.34×** | **+0.0025** | +0.53 | +0.48 | +0.05 |
| all roots | 2.0 | 2.06× | +0.0087 | +1.59 | −8.01 | **+9.60** |
| all roots | 3.5 | 2.29× | +0.0046 | −1.70 | −12.49 | **+10.79** |

**ΔP(traverse) is positive in all four cells:** the windows `a2` *rejects* traverse slightly more
often than the ones it keeps. It is not neutral like `slope_ok` — it is mildly adverse. On micro,
net improves at both depths while cost moves $0.05. The forecast's own Q1 lift, fitted separately
inside each arm (D8), is unchanged or larger without `a2`: +0.0981 → +0.1030 at X=2.0 and
+0.0909 → +0.0931 at X=3.5. Whatever `a2` removes, the forecast did not want it.

**All-roots is a cost artefact, not a verdict.** Dropping `a2` there admits NG, RB, HO and the rest
of the non-micro roots: mean cost goes $14.64 → $24.24 and top-3 root share falls 24% → 12%. That
is C1/C3 firing, and it is the D493 instrument question, not the `a2` question.

**A mis-specified decision rule, disclosed.** D7 was pre-declared two-sided (`|ΔP| < 0.005`) for a
one-sided question. `a2` buying signal means Δ < 0, so the literal rule prints KEEP at X=2.0 on a
change that is *favourable*. The literal output is reported above; on the question the test was
built to answer the answer is DROP everywhere on micro.

**The projected power gain was wrong.** ~2.6× was claimed; it is **1.27–1.34× on micro**, because
the roots that have a micro already have fine ticks relative to their moves. The compounding
estimate for the power problem falls from ~28–73× to **~14–36×**, putting the deep `stop_retrace`
cells at 10,000–33,000 trades against the ~14,500 needed. The 1-minute fixture and the all-root
measurement carry nearly all of it; `a2` is not a lever.

## 2. The stop was inside its own entry in 27.5% of every published D528 trade

X = 2.0 is a **floor**, not a level, so the mean realised entry depth is **2.82σ** against a stop
fixed at G = 3.0σ. For 27.5% of micro baseline trades price is already past the stop at the fill,
and the "stop" then fires on the first bar of **favourable** movement.

| baseline split | n | win% | P(target) | P(stop) | gross $ | median bars |
|---|---:|---:|---:|---:|---:|---:|
| stop OUTSIDE (\|y\| ≤ 3σ) | 3,839 | 25.0% | 11.7% | 82.0% | −0.89 | 3 |
| **stop INSIDE (\|y\| > 3σ)** | **1,457** | 38.9% | **4.1%** | **93.4%** | −1.43 | **1** |

This is the identical defect fixed in the depth sweep two turns earlier (`G = X + 1.0`) and never
carried back into the baseline geometry. It is in every D528 per-trade cell.

**Correcting it makes the construction worse, not better, and that is the interesting part.**
Paired on identical trades, block-bootstrapped over (root, day), micro:
`fixed → relative` is **−$0.39 ± 0.33** (boot p5 −0.94, p95 +0.15), median difference **+0.00**,
and only **9.4% of pairs improve** while ~18% get worse — roughly **2 : 1 against**.

**So the buggy geometry was accidentally protective.** A 2σ+ excursion that immediately continues
does not come back, and cutting it at bar 1 beat giving it room. The published figures were
therefore mildly *optimistic* (by $0.39, inside its own error bar) rather than inflated — but they
measured a geometry nobody designed, and both conventions are now reported side by side.

## 3. The decoupling: the grace window is unresolved, frozen expectations are null, and `frozen`
   as literally specified is void

The principal's sentence bundles two changes; they were separated because run together a result
could not be attributed. (a) the **grace window** — the forecast fires at t_f, entry may occur in
[t_f, t_f+W]; with a fresh reference this is pure *selection* and changes no individual trade
(asserted, self-test [2]). (b) the **frozen reference** — level, slope and σ read from t_f.

**D3, the largest design decision:** every previous D528 forecast figure cut at the median of the
*candidate* population. Decoupling requires evaluating the forecast where there is no extreme, so
the composite was refitted on **3,042,356 all-bar** early-half observations, cuts −0.039 / −0.482 /
−0.846 for q = 50/25/10. These arms are comparable only to each other and to NO-FORECAST.

### 3.1 `frozen` as specified manufactures extremes rather than waiting for them

**83,792 trades against 5,296 for no filter at all — 16× more than the unconditional
construction.** A level carried 20 bars plus drift is almost always ≥2σ from price. C3 fired
exactly as pre-declared: |y|/σ rises 2.85 → 4.56 **and** delay rises 0 → 11.7 *together*, which is
the level's own extrapolation. 66–71% of its trades had the stop inside the entry. **Void**, and
recorded rather than quietly replaced. q = 50 was also dropped on C1: its coverage measured
0.80–0.86, so those cells were NO-FORECAST wearing a forecast's name.

### 3.2 `hybrid` — real trigger, frozen expectations — is the clean test of (b), and it is null

`hybrid` keeps a real fresh extreme as the trigger and reads only the target's and stop's
level/slope/σ from the forecast bar. That reads "the same mean and range **expectations** as where
forecasted last" as describing the expectations, not the trigger, and it holds the entry set
**identical** to `fresh` — same bars, same count, same cost, same root mix. So the comparison is
**paired**, which is a stronger statement than any count-matched control can make.

24 cells, block-bootstrapped over (root, day), 2,000 draws:

- the **median paired difference is exactly +0.00 in all 24 cells**
- only **23–30% of pairs are helped**
- 5 of 12 micro cells are **negative** (−1.18 to +0.88)
- the best cell, `fresh_q25_w15_relative → hybrid`, is **+$0.88 ± 0.54, boot p5 +0.01** — a margin
  of 0.01 against an SE of 0.54, selected from 24 cells

By D373's rule a margin inside 2 SE is UNRESOLVED, and this one is inside 0.02 SE of zero before
any multiplicity is charged. With the median at zero and under a third of pairs moving favourably,
whatever the mean shows is carried by a minority of pairs — the tail-carried pattern that does not
book. **Frozen expectations are null.**

### 3.3 The grace window is the most interesting negative in the set

On micro the marginal trades the window adds are *better than the base they are added to* — and
there is a clean gradient in the forecast cut, which is the first time in D528 that relaxing
anything improved a mean:

| q | base n | base gross | marginal n | marginal gross |
|---|---:|---:|---:|---:|
| 25 | 1,420 | −1.11 | +1,336 | −0.46 |
| 10 | 548 | −0.22 | +752 | **+0.65** |

But this is the **weakest** of the three statistics — the sets differ, so it is an unpaired block
bootstrap — and it does not resolve: the marginal advantage is **+$0.60 to +$1.16 with SE
1.30–2.24 and every bootstrap p5 negative** (−1.35 to −2.93). On all roots the marginal trades are
**−$13 to −$22 worse**, significantly so in 6 of 8 cells, because the window reaches into the
expensive non-micro roots.

## 4. Two defects in the runner, both disclosed and both fixed

1. **D9's implementation was not D9.** The declaration said a count-matched fire-bar control on
   identical machinery; the code bootstrapped P&L from the no-forecast pool, and a pool-size
   condition then silently dropped **every** `frozen` cell — the arms under test. It has been
   replaced with the declared construction (per session, the same number of fire bars drawn
   uniformly from that session's eligible pool), and `run()` now carries a **REQUIRED-OUTPUTS
   guard that raises** if any of the 82 declared cells is absent. Prose cannot catch a missing
   output; that guard can, and it is the standing rule this violated.
2. **Twelve of twelve stars on negative medians.** The first run starred every cell on the median
   while every median was deeply negative. "Beats the control" is empty below zero; a star is now
   reported as a margin and never as a pass.

Two fixture defects of my own, caught by the self-tests rather than shipped: tick 0.25 on a unit
random walk fails `a2ok` (2.7 ticks against a 4-tick floor), so the first fixture admitted nothing
and three checks "passed" on empty sets; and the reach test used a monotone ramp, which the drift
rule `sign(y)·slope < 0` can never admit — the same mistake ADDENDUM 13 records for the
confirmation-mode fixture. Ten self-tests now pass, including [9] which proves the stop fix is
exercised (4 of 11 inside under `fixed`, **0 of 11** under `relative`).

## 5. Disposition

1. **`a2`: DROP on micro.** It buys nothing, is mildly adverse, and is worth 1.3× not 2.6×.
2. **Frozen expectations: null.** Median paired difference zero in all 24 cells.
3. **`frozen` as literally specified: void** — it manufactures the extreme it claims to wait for.
4. **The grace window: unresolved, and the one thing here worth more power.** It is the only
   mechanism in D528 whose *marginal* trades beat its base, and the effect grows as the forecast
   cut tightens. At q=10 it has 548 base and 752 marginal trades; that is why it cannot resolve.
   It is the natural first target for the 1-minute fixture.
5. **The stop convention must be depth-relative in all future work**, and both conventions must be
   reported until the published cells are restated.
6. **No component line, no promotion.** Best micro cell in this set is `hybrid_q25_w15_relative` at
   gross +$0.11 on 2,727 out-of-time trades — the first positive gross in D528 at n > 2,500 — and
   net −$4.53 against a $4.64 round trip. Still four to five times short of cost. The axis remains
   the principal's to close.

**Outstanding for the principal:** whether the reserved slice (2026-04-11 → 2026-09-09) is
considered spent after five months of it were read in the ADDENDUM 12 defect.
