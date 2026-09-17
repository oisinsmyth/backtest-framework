# D429 — the long-only combined book at three slots, with the 2018+ window as the second-half gate

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D429-the-long-only-combined-book-at-three-slots-with-the-2018-window.md`. The H1 above is the full title.*

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. D400–D428
used, D407–D410 and D390–D399 reserved. **No holdout of any kind is read.** Daily bars.

## 1. What this is, and what it is not

**The principal's choice after D428:** the long-only arm of D428's pool, at three slots — the
sweep's peak — with the second-half gate moved from 2021–2026 to **2018–2026**.

**Said plainly:** the arm, the slot count and the window were all chosen after D428 was seen.
The primary book's pooled number **has already been observed** — D428's `LONG N3`: +4.20 / +4.52
/ +4.47 by seed, mean **+4.40 ± 1.99 (+2.2 SE)**, and its 2021–2026 window +8.28 ± 4.48. What this
study adds that has not been seen is the **2018–2026** book number and its control; the rest is a
reproduction. A gate that has already been observed to pass is not evidence; it is a floor. Both
facts go in the result whatever it says.

## 2. The construction

Everything in D428, restricted to demand zones:

```
POOL    STACK2-ANY & cell 2 & price < $38.51 & gap 3-20 & side > 0     1,416 events, 336 names
        0.338/day; mean occupancy 1.69 positions;  2018+ 764;  2021+ 528
PRIO    opposite-side prior 3-10 back, long                              165 (D428: worth nothing; kept so the object is D428's)
N       3 primary; 2, 4, 5 reported (shape)
exit    t+5 close, no stop
cost    neutral Corwin-Schultz + IBKR; NO borrow (long-only -- [COST] asserts the borrow term is identically zero)
```

`scripts/d428_pool.py` unchanged; the arm is its `long` mask.

## 3. Measured

Per trade: D422's table on pooled, 2018+, 2021–2026; the |r| ≤ 50% variant; concentration with
the top trade named and its bars read, **for the 2018+ window as well as pooled**; a per-year
table of the N=3 book's net.

The book: `sim4` (D427) at N ∈ {2, 3, 4, 5}, three seeds, with and without the priority;
`[P2]` the N=3 priority book reproduces D428's `LONG_N3` bit-identically (gross and cost
series); monthly block-bootstrap SE on pooled, 2018+ and 2021–2026 for every book.

**Control at N=3:** matched-count random pools of 1,416 drawn from **cell-2 long events** (the
control shares the arm's side, its cost model and its count; D428's drew from both sides), one
per name, no priority, 100 draws, one worker measured before the fan-out.

## 4. The bar — the N=3 long book with the priority

- **T1** pooled net bp/bar > 0 by 2 SE — **already observed at +2.2 SE; a reproduction.**
- **T2** above the p95 of the random long-pool control (D373's margin).
- **T3** **2018–2026** net > 0 by 2 SE (monthly block bootstrap on that window).

**T1 ∧ T2 ∧ T3 makes this book a candidate under the principal's standing rule** — with the
caveat of §1 attached to it in the same sentence, always. **Nothing here reads a holdout.**

## 5. Predictions (MODERATE; the pooled number is known, the window is not)

- **X-a** N=3 pooled reproduces D428 exactly: +4.40 ± 1.99.
- **X-b** 2018+ net **+5.5 to +8** with SE **2.5 to 3.5** — passes 2 SE more likely than not,
  and not by much: the 2018+ per-trade gross is +113 on 764 trades, half of the pool's history.
- **X-c** 2018+ concentration: **8 to 12 names to half the P&L** of ~230, top year ≤ 30%.
- **X-d** the random long-pool control's p95 at N=3 between **+0.5 and +2.0**; the book beats
  it by more than 2 SE.
- **X-e** the priority's delta at N=3 inside ±0.4 and inside its noise; N=2 below N=3 (cluster
  days turned away), N=4 and N=5 below N=3 (dilution) — the peak holds on the long arm.
- **X-f** the per-year table: positive in at least 11 of 17 years; 2022 or 2023 negative.

## 6. Not in scope

No holdout, no 15m, no exits, no change to pool, cut, gap window or hold, no disposition.
Twenty-ninth look by object — and the second look at this book.
