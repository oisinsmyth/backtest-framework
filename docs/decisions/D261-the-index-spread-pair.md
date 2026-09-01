# D261 — The index spread, as a prop-track candidate

**Status:** Pre-registered — committed BEFORE the runner exists
**Date:** 2026-08-29
**Area:** Strategy research · **prop track** ([BOOK_PROP.md](../BOOK_PROP.md))

---

## Why a spread, and why now

**[D258](D258-the-prop-track-candidates.md)'s four candidates are exhausted, and all three that were
screened failed on SHAPE rather than on return:**

| | why it failed |
|---|---|
| **C1** session-boundary hold | positive edge; the **path** breaches a ratcheting floor |
| **C2** intraday reversion | negative edge, and **worse as conviction rises** |
| **C3** opening range | positive mean, **negative skew** — one large loss breaches |

**Hurdle P does not care what you earn. It cares how.** A 4% trailing floor on open equity punishes
both tails, and **every construction this programme knows how to build is directional.**

**Measured 2026-08-29, on the 18:00→16:10 hold, `index_extended_15m_raw`:**

| construction | ann vol | MAE p99 | **4% breach** | ann return |
|---|---:|---:|---:|---:|
| LONG SPY | 16.7% | 3.87% | 0.92% | +14.04% |
| LONG QQQ | 20.2% | 4.49% | 1.74% | +15.26% |
| **SPREAD SPY−QQQ** | **6.4%** | **2.15%** | **0.15%** | **−0.46%** |
| SPREAD SPY−DIA | 8.0% | 3.21% | 0.51% | −0.59% |

**A spread has 38% of the leg's volatility and a sixfold lower breach rate**, and its MAE p99 sits
*inside* the floor rather than on it. **In sizing terms that is roughly 4x the headroom C1 had.**

**And the drift vanishes with the volatility** — the two honest spreads return ≈0%. **So this study
is a test of one thing only: does the spread itself mean-revert enough to pay?**

---

## The trap this design must avoid, named first

**SPY−IWM returned +4.33% and QQQ−IWM +8.03% in the same measurement.** Those are **not** spread
edges — they are **tech-versus-small-cap factor bets wearing a spread's name**, and
[D251](D251-the-cross-sectional-dollar-neutral-pre-screen.md) already caught this exact failure:
*"matched notional is not matched exposure"*, with BAB at **−1.27 net beta**.

**So beta-neutrality is a HURDLE here, not an assumption**, and it is measured on the realised book
rather than asserted from the construction.

---

## Pair selection — eliminated rather than constrained

**[D246](D246-the-search-protocol-for-s3.md) requires pair selection to be fixed by a stated
non-performance rule before any pair is scored.** This design goes further and **removes the choice
entirely**:

> **The prop venue's liquid equity index contracts are ES, NQ, RTY and YM. Their proxies are SPY,
> QQQ, IWM and DIA. That is four instruments and therefore SIX pairs. ALL SIX ARE TESTED. There is
> no selection step, so there is nothing to overfit.**

**No cointegration screen, no correlation filter, no ranking.** A selection rule would be a free
parameter; testing the whole (tiny) universe is not.

## The rule — every parameter fixed here

```
spread(t)   = log P_x(t) - beta(t) * log P_y(t)
beta(t)     = OLS of x on y over the PRIOR 60 holds, clipped to [0.2, 3.0]     (R9)
z(t)        = ( spread(t) - mean_60(spread) ) / sd_60(spread)                  prior 60 only
entry       |z| > 2.0        long the spread if z < -2, short it if z > +2
exit        |z| < 0.5, or 20 holds elapsed, whichever first
execution   held over the 18:00 -> 16:10 window, FLAT at 16:10, re-entered at
            18:00 while the signal persists -- so a multi-day trade is a SEQUENCE
            of venue-compliant overnight holds
cost        0.2 bp round turn PER LEG, so 0.4 bp per spread round trip
```

**`|z| > 2.0` is the textbook default and is NOT swept.** A three-value sweep across six pairs would
be eighteen cells for a family whose known failure mode is exactly that kind of search. **One
threshold, six pairs, six cells.**

## The split

| | span |
|---|---|
| **SCREEN** | 2010-01 → 2018-12 |
| **HOLDOUT** | **2019-01 → 2026-08**, contains March 2020, carries the verdict |

Same split as [D260](D260-the-vol-targeted-overnight-hold.md), and for the same reason: **a rule
validated on a period without a stress event is not validated.**

## Hurdles — all on the HOLDOUT

- **P1 / P4.** 4% trailing drawdown on the sized spread path; expected life **> 3 years**.
- **P3.** Worst single hold **≤ 2%** of account.
- **V.** **Positive net CAGR** after two-leg futures cost.
- **NEUTRALITY — the D251 hurdle.** **|net beta of the realised book| < 0.10**, regressed on the
  equal-weighted index. A cell failing this is reported as a **directional bet**, never as a spread,
  whatever it earned.
- **NULL.** Matched-count rotation null at p95 on Sharpe AND money — same entry count, same holding
  lengths, wrong bars.
- **LADDER.** Expected profit before first breach must exceed the payout cap (26% benchmark).
- **2020 reported separately**, never pooled away.

## Predictions

| | prediction | confidence |
|---|---|---|
| **U-a** | **At least one of six pairs clears P1/P3/P4** — the shape measurement already says the floor is reachable | **~80%** |
| **U-b** | **No pair clears V and the NULL together.** Tight index spreads mean-revert over minutes, not days, and 0.4 bp per round trip on a spread whose typical excursion is tens of bp leaves little | **~60%** |
| **U-c** | **The pairs that EARN most fail NEUTRALITY** — SPY−IWM and QQQ−IWM carry the tech/small-cap tilt, and that is where the in-sample return came from | **~70%** |
| **U-d** | **SPY−QQQ and SPY−DIA are the cleanest on neutrality and the emptiest on return** | **~65%** |
| **U-e** | **2020 is the best period for the spread, not the worst** — dislocation widens spreads and mean reversion pays. This is the opposite of every directional candidate | **~55%** |

**U-c is the one that decides whether this is a spread study or a factor study in disguise**, and it
is registered so that a passing QQQ−IWM cannot later be quoted as a pairs result.

## Stop

**If no pair clears V, the NULL and NEUTRALITY together, the spread category is CLOSED for the prop
track** — no threshold sweep, no second lookback, no cross-asset pairs, no cointegration screen
added afterwards. **That would be the selection step this design deliberately removed.**

## What this cannot establish

**Equity proxies, not futures.** ES/NQ/RTY/YM spreads have their own basis behaviour, roll dates and
tick sizes that SPY/QQQ/IWM/DIA do not reproduce. **A pass is a feasibility bound.**

## Ledger

| count | N |
|---|---:|
| fresh — 6 pairs x 2 cohorts | 12 |
| + the shape measurement that motivated it: 4 legs + 4 spreads | 20 |
| + carried from D260 | 46,069 |
| **total** | **46,089** |
