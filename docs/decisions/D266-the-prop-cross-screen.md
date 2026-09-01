# D266 — The R12 cross-screen to the prop track

**Status:** Screened and closed. Nothing admitted to [`BOOK_PROP.md`](../BOOK_PROP.md), which stays empty.
**Date:** 2026-09-01
**Area:** Strategy research · **prop track**

**The ledger does not move.** No cell was re-run and no book was built: every input is read from
D247's committed `intraday_shorts_summary.json`, and re-costing is arithmetic on `breakeven_bps`,
which is a cost-free statistic by construction.

---

## Why it was run

[R12](../RULES.md#r12) is binding: *"a candidate that fails one track's standards is screened against
the other's before it is closed,"* and its second corollary requires the screen to **re-cost**, not
merely re-threshold. [D264](D264-the-intraday-short-on-single-names.md) and
[D265](D265-the-entry-time-reconciliation.md) closed on the personal track, so this is the mandatory
step before that closure stands.

## What could not be screened, and it is not a cost question

**D264 and D265's single-name work is structurally unportable.** Its edge is single-name
idiosyncratic variance ([FINDINGS §2](../FINDINGS.md)), and there is no retail futures contract on
PG, LMT, PM, MO, CLF, SM, YELP or RH. **R12's escape hatch assumes the same exposure can be bought
more cheaply elsewhere; here it cannot be bought at all.**

So the screen ran on **D247's 57-ETF intraday cells**, which proxy ES/NQ/RTY/YM.

## RESULT — R12's prediction is confirmed, four cells flip, and none of them help

At **1.60 bp/side** seven of eight cells lose money. At **0.10 bp/side**:

| cell | futures net | Sharpe, ETF → futures | P2 | P1 size | **after P1 sizing** |
|---|---:|---|---|---:|---:|
| **S1_long_intra** | **+2.16%** | −0.586 → **+0.294** | **PASS** | 0.191× | **+0.413%/yr** |
| S2_long_cont | +1.10% | +0.191 → +0.320 | fail | 0.485× | **+0.535%/yr** |
| S1_long_cont | +0.91% | −0.279 → +0.056 | fail | 0.166× | +0.152%/yr |
| S1_short_intra | +0.10% | −1.550 → −0.192 | PASS | 0.098× | +0.010%/yr |

**The Sharpe is re-costed too, not only the return** — quoting D247's 1.60 bp Sharpe beside a
futures-cost return would understate the cell in one column while P1 overstates it in another.

**And none of it helps, because P1 is a sizing constraint.** Scaled until max drawdown reaches 4%,
the best cell earns **+0.535%/yr** and the best P2-compliant one **+0.413%/yr** — against
[D260](D260-the-vol-targeted-overnight-hold.md)'s already-marginal **+1.87%/yr** for the overnight
hold. This is a quarter of a candidate that was barely worth running.

**The short side contributes nothing even here:** the only surviving short cell earns **+0.010%/yr**
after sizing, with a Sharpe still negative after re-costing.

## The one thing that genuinely transfers, and it is not a return

**An intraday-flat construction holds nothing across any flatten time, so it is natively P2-compliant
at EVERY venue** — including Topstep, which [R11](../RULES.md#r11)'s amendment treats as **blocked**
for the personal book because its own sources conflict on the overnight. **The personal book can
never have that fit: 86.6% of its return is overnight timing.** If the prop track ever finds a real
intraday signal, the flatten discipline is free rather than an obstacle.

## What was NOT computed, said rather than implied

- **P4 is not calculable from these artifacts.** It needs the OPEN-equity path against a ratcheting
  barrier; every number here is closed-equity, which R11 states is materially gentler.
- **P5 and P6 are venue facts**, not properties of these cells. P6 restricts the venue to Topstep or
  MyFundedFutures.
- **The basis is real.** These are ETFs; most of the 57 have no futures contract at all, so an actual
  futures book is a **subset** with lower breadth than the 2.23 effective instruments D247 ran at.

**A pass here would have been a feasibility bound, not a result** — the same caveat D263 attached to
the COT panel. Nothing passed, so the point is moot and the closure stands.
