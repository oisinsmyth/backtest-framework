# D472 — the down-leg reversal pick tested on what the family null has not priced: a standardised family bar, SPY and IWM cash 2010–2015, and RTY

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D472-the-down-leg-reversal-pick-tested-on-what-the-family-null-has-not-priced-a-standardised-family-bar-SPY-and-IWM-cash-2010-2015-and-RTY.md`. The H1 above is the full title.*

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file.
**Reads nothing after 2023-12-29 on any fixture; the 2024+ futures slice and the 2024+ equity
reserve stay unread.** D472 taken after `ls docs/decisions` and `git log --all` on both
worktrees showed D471 used on master (the other session's spread record).

## 0. What is being tested

D470 found, against the principal's continuation hypothesis, that the overnight index drift
concentrates **after a negative overnight leg** (ES-W2 +$10.66 vs −$1.37, 2.5 SE; NQ +$13.32 vs
−$1.57, 2.1 SE; gated net Sharpe +0.70 / +0.62 at one micro and $3), clearing the exact rotation
and run-length nulls on both roots and **failing the common-offset family-maximum p95 on both**,
with the whole gap in 2020–2022. It is a pick: selected from a family of 32 cells on eight years.
The principal asked for the step-by-step fix. The fix is not a lower bar; it is **(1) the family
bar on the right scale, declared, and (2) evidence from data the family null has not priced** —
a different period and a different instrument — with the sign and size predicted first.

## 1. Step 1 — the family null on a standardised scale (an amendment to D470, declared here)

D470's family maximum was taken in **dollars per night**, so the two small, volatile cells
(G-C, G-D: a fifth of nights at σ 270–320) set the bar for a cell trading 45% of nights at σ 107.
Re-run the identical common-offset rotation over the same 8 cells per root-window with the
statistic as **(a) the z-score of the gated mean (mean / (σ/√n))** and **(b) the gated
component's net Sharpe on the root's calendar** (the ledger's quantity). Report p50, p95 (exact,
SE 0) beside the observed on both scales, for ES-W1, ES-W2, NQ-W1, NQ-W2. **The dollar scale
stays in the record; both are reported.** Passing on the standardised scale moves the cell from
*pick* to *in-sample survivor*; it does not make it a component, because the selection has
already happened.

## 2. Step 2 — the sign on data no record has read for this question

**2a. SPY and IWM cash, 2010-01-04 → 2015-12-31**, from `index_extended_15m_raw` (never read for a
conditional overnight question; D259 read the unconditional drift on it). The cash analogue of
W2 is **close (the 15:45 bar's close) → next open (09:30)**, in bp; of W1, close → next close.
Gates, read at the close before the entry: **G-B′** the prior overnight gap (into the entry day)
> 0 vs ≤ 0; **G-A′** the prior session close-to-close > 0 vs ≤ 0. Two declared cells per symbol
and window (the down sides); the up sides reported as the other side. Statistics as D470: gated
mean, other side, difference with its SE, N1 exact rotation and N2 run-length nulls on the gate,
by-year table, top nights named, symmetric 1%-trimmed means. **2016–2023 on the same two symbols
is run beside it as the consistency check** that cash mirrors the futures where both exist. No
cost model: this is a sign-and-size test, not a component.

**2b. RTY futures, 2017-07-10 → 2023-12-29**, added to the D467 builder as a ninth root (same
build, same gates; G1 1.5%, G4 vs IWM ≥ 0.99 as D462, which RTY failed at 0.9899 on the
2020-03-16 limit-down open — **if it fails again it is held back and IWM cash 2016–2023 from 2a
stands in**, declared now). If it passes: RTY-W2 after a down leg vs after an up leg, one M2K
($5/pt, $3), the same statistics and nulls as D470.

## 3. What would justify step 3 (a component pre-registration), declared now

All of: the ES-W2 down-leg cell clears the standardised family p95 on at least one of the two
scales; SPY cash 2010–2015 shows the **same sign** with the difference ≥ 1.5 SE; IWM cash
2010–2015 the same sign; and RTY (or IWM 2016–2023) the same sign. Any failure among these is
reported as such and the pick stays a pick. Step 3, if reached, is a separate record and the
2024+ read is the principal's decision.

## 4. Predictions

- **X-a** Standardised family p95 on the z scale **2.2–2.6** for every root-window; ES-W2
  down-leg z = 10.66 / (107/√904) ≈ **3.0 clears**; NQ-W2 z ≈ **2.3, marginal**; on the Sharpe
  scale the family p95 is **0.55–0.65**, ES-W2's +0.70 clears and NQ-W2's +0.62 is marginal.
  The W1 down-session cells do not clear on either scale.
- **X-b** SPY cash 2010–2015, gap after a down gap: **+2 to +5 bp** vs other side **−1 to +1 bp**,
  difference **1.5–3 SE**, larger in 2011 and 2015 than in 2012–2014 (the regime dependence
  D470 saw). IWM the same sign, larger in bp.
- **X-c** SPY cash 2016–2023 reproduces the futures: difference ≥ 2 SE, same order as ES-W2 in bp
  (≈ +5 vs −1 on a $300–450 ETF... in bp: +3 to +6 vs −1 to +1).
- **X-d** RTY passes the gates this time or fails G4 by under 0.005; RTY-W2 down-leg positive,
  difference **1–2 SE** on ~1,600 nights.
- **X-e** Runtime under 10 min for the runner; the RTY rebuild ≈ 22 min (background).

## 5. Files

This record · `scripts/run_d472_reversal_checks.py` (`--run`, `--selftest`) · `scripts/build_fut_sessions_hourly.py`
(RTY added; fixtures rebuilt bit-identically for the eight roots, asserted) · `data/d472_reversal_checks.json` · RESULT.
