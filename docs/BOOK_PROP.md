# The Prop Book

**Admitted arms: none.**

This file is the prop track's counterpart to [BOOK.md](BOOK.md). It is empty, and saying so plainly
is the point — an empty book with stated standards is more useful than a populated one with
borrowed ones.

**Admission requires [hurdle P](RULES.md#r11), all six.** The personal book's arms do not clear it
and cannot be made to.

---

## Why the personal book cannot be ported

| | personal book | hurdle P |
|---|---:|---:|
| max drawdown at deployed size | **−29.82%** | **≤ 4% trailing, on OPEN equity** |
| overnight exposure | **required** — 86.6% of the return is overnight timing | venue-specific; forecloses it at most firms |
| instrument | ETFs | futures |

**P1 is failed by roughly sevenfold and P2 structurally.** No amount of position sizing fixes P2 —
the edge *is* the overnight hold. This is not a sizing problem, it is a different strategy.

---

## The standards, restated

From [R11](RULES.md#r11) and its amendment. **P2 is venue-specific and was corrected the day it was
written:**

- **MyFundedFutures** permits a position opened at the **18:00 ET Globex open** to be held to the
  **16:10 ET** New York close — a ~22-hour hold spanning the entire overnight session — **and
  permits automation at the funded stage.** It is the only venue clearing both P2 and P6.
- **Topstep** permits automation but its own sources conflict on the overnight, so it is treated as
  blocked.
- **Apex** and **Take Profit Trader** ban automation at the funded stage, failing P6 outright.

**So the venue is effectively decided: MyFundedFutures, or nothing.**

---

## Candidates

Fixed in [D258](decisions/D258-the-prop-track-candidates.md) **before any was screened**, so that a
later winner cannot be dressed up as having been predicted.

| | candidate | state |
|---|---|---|
| **C1** | the session-boundary trade — hold the 18:00→16:10 window and collect the overnight drift | **rule question answered favourably; the path measurement is running** |
| **C2** | intraday mean reversion with hard stops | not screened. Shape fits P1; the cost objection that excluded it is removed |
| **C3** | opening-range constructions | not screened. Natively P2/P3-compliant, heavily mined |
| **C4** | the sizing wrapper | a precondition, not a candidate. Build once, reuse |

---

## What P1 demands of the return distribution

**A 4% trailing drawdown on OPEN equity dictates shape, not magnitude:**

- **Positive skew is fatal** — frequent small losses ratchet against the floor while you wait for the
  rare large win. This is the profile of a short book ([FINDINGS §1](FINDINGS.md)).
- **Negative skew is fatal** — one large loss breaches immediately.
- **What survives is a high hit rate with low variance and tight tails.**

**Both personal arms are "wait for the move" constructions. Neither has this shape.**

---

## The open risk nobody has measured

**A 22-hour futures hold is 22 hours of OPEN-equity exposure against a ratcheting floor**, and
**20:00–04:00 ET cannot be exited** — a gap through that window cannot be stopped out of.

**The +8.59%/yr overnight figure is a cash-equity close-to-open GAP with no interior.** Futures trade
that period continuously, so the drift may be identical while the *path* — which is exactly what P1
measures — is entirely different. **That measurement is in progress and it is C1's gate.**

---

## Data

**We hold no futures data**, and free intraday CME data does not meaningfully exist
([`docs/alpha_vantage_api.md`](alpha_vantage_api.md) — Alpha Vantage serves no futures at all; its
commodity endpoints are daily macro series and `FX_INTRADAY` silently ignores `month`).

The nearest proxy is an **extended-hours equity fixture** — `TIME_SERIES_INTRADAY` with
`extended_hours=true` gives ~64 bars/session covering **04:00–19:45 ET**, which is 16 of the 23
futures hours, leaving only the Asian session uncovered. **That fetch is running.**

Options for real futures data are recorded in
[D259](decisions/) when acquired; none is free.

---

## C1 — SCREENED AND CLOSED, 2026-08-29

[D259](decisions/D259-the-extended-session-and-the-overnight-interior.md) measured the path. **C1
fails hurdle P4 by roughly sixteenfold and cannot be sized out of it profitably.**

### The edge is real and era-stable — that is not the problem

Overnight total **+9.04%/yr**, reproducing D247's +8.59% in shape, and **stable across eras**:
**+8.55%** (2010–19) / +18.91% (2020) / **+8.28%** (2021–26). **Unlike the intraday leg, which is a
2020 artefact, the overnight drift holds up.**

Decomposed: post-market **+1.70%**, untraded 20:00–04:00 **+5.88%**, pre-market **+1.27%**, regular
hours +3.12%.

### The path is the problem

| era | holds | MAE p99 | worst | **4% breach @1x** | @2x | @3x |
|---|---:|---:|---:|---:|---:|---:|
| ALL | 12,985 | 3.98% | **13.85%** | **2.07%** | 16.47% | 34.73% |
| 2010–2019 | 7,758 | 3.48% | 13.85% | 1.06% | 11.34% | 26.46% |
| **2020** | 792 | **7.05%** | 11.29% | **11.36%** | 35.10% | 56.57% |
| **2021–2026** | 4,435 | 3.90% | 6.87% | **2.19%** | 22.10% | 45.30% |

**P4 requires an expected time-to-breach above 3 years — a breach rate under 0.132%:**

| | breach | expected life | verdict |
|---|---:|---:|---|
| **1x** | 2.07% | **48 sessions, 0.19 yr** | **FAILS by 16x** |
| 2x | 16.47% | 6 sessions | FAILS by 125x |
| 3x | 34.73% | 3 sessions | FAILS by 263x |

**The typical hold is quiet — median MAE 0.55% — and the tail is not.** The 99th percentile sits
*exactly* on the 4% floor.

### Why sizing down does not rescue it

Clearing P4 needs the 99.87th percentile of MAE inside the floor, which puts the notional near
**0.5x**. At 0.5x the arm captures roughly **4.5%/yr of account value** — and **2020 would still
have breached at 11.36% even at 1x**, so a single such month ends the account regardless.

**This is `exposure x edge` ([FINDINGS §1a](FINDINGS.md)) arriving from the drawdown side.** The
size that survives the constraint earns too little to matter, and the size that earns enough does
not survive.

### The unstoppable half

**In the March 2020 cluster roughly half of each drawdown was delivered by the gap before the
market opened** — IWM 2020-03-12 lost 5.07% of an 11.29% MAE in the untraded window.

**R11's amendment claimed "a gap cannot be stopped out of" and D259 shows that is right in mechanism
and small in magnitude** — only **3.72%** of 1x first-breaches occur in the untraded window, and the
gap alone breaches on **0.10%** of holds at 1x. **Three caveats all make that a lower bound**: the
untraded window contributes one observation per hold, the pre-market is counted exitable and barely
is, and it is quiet by construction in this fixture.

**Worst hold in sixteen years: QQQ 2010-05-06, the Flash Crash, 14.03% trailing drawdown** — a
regular-hours event a stop could in principle have caught.

### What C1 leaves behind

**The overnight drift is real, era-stable and reachable at MyFundedFutures.** What defeats it is
P1's ratcheting floor measured on open equity, not the edge. **Any future prop candidate must be
screened on MAE before its returns are computed** — D259's method is the reusable part.

**Next: [C2](decisions/D258-the-prop-track-candidates.md), whose shape fits P1 by design** — high
hit rate, tight tails — and whose cost objection R12's cross-screen has already removed.

---

## C1 — REOPENED, 2026-08-29. The closure above tested only STATIC sizing, and that was my error.

**[D258](decisions/D258-the-prop-track-candidates.md) named C4, the sizing wrapper, as a
PRECONDITION** — *"Any candidate needs this bolted on before P1 is even measurable."* **C1 was
closed without it.** The verdict above measured a constant notional against a ratcheting floor,
which is the one sizing scheme guaranteed to be wrong when the tail is regime-driven.

### Vol-targeted sizing, matched on average exposure

Size `k = target_vol / trailing_vol`, the volatility estimate taken over the **prior 21 holds only**
(R9), capped. Compared against static sizing **at the same average exposure** — the only fair
comparison:

| avg size | **breach, vol-targeted** | *breach, static* | ratio | ann return | **profit before breach** |
|---:|---:|---:|---:|---:|---:|
| 0.48x | **0.06%** | *0.13%* | 0.47x | +4.41% | **28.20%** *(vs 18.75%)* |
| 0.71x | **0.18%** | *0.55%* | **0.32x** | +6.61% | **14.71%** *(vs 6.74%)* |
| 0.95x | **0.57%** | *1.75%* | **0.33x** | +8.79% | **6.08%** *(vs 2.82%)* |
| 1.42x | 2.95% | *6.66%* | 0.44x | +13.04% | 1.75% *(vs 1.11%)* |

**A threefold reduction in breach rate at matched exposure, and roughly double the expected profit
before breach.**

### And it removes the regime dependence entirely

| era | static 1x | **vol-targeted** | avg size it chose |
|---|---:|---:|---:|
| 2010–2019 | 1.07% | **0.22%** | 0.79x |
| **2020** | **11.36%** | **0.13%** | **0.50x** |
| 2021–2026 | 2.19% | **0.11%** | 0.63x |

**2020's breach rate falls by a factor of 87, and the three eras converge to 0.11–0.22%.** The tail
was regime-driven; sizing to volatility removes the regime. **This is D236's finding read against
the right criterion** — those six controls "reduced drawdown without improving risk-adjusted
return", which is exactly what a drawdown constraint wants.

### Does it clear P4?

**Yes, at a 0.4% volatility target:**

| scheme | avg size | breach | **expected life** | ann return | profit before breach |
|---|---:|---:|---:|---:|---:|
| **voltgt 0.4%, cap 4x** | **0.48x** | **0.06%** | **6.40 years** | **+4.41%** | **28.20%** |
| voltgt 0.6% | 0.71x | 0.18% | 2.33 years | +6.61% | 14.71% |
| *static 1x (the closure above)* | *1.00x* | *2.09%* | *0.19 years* | *+13.10%* | *2.49%* |

**P4 needs an expected life above 3 years. The 0.4% target gives 6.40.**

**And the number that matters most for a funded account: expected profit before breach is 28.20% of
account value** — on a $150k MFF account, roughly **$42,000**, which comfortably exceeds the payout
ladders these firms cap at. **The account earns its full ladder well before it dies.**

### What this is, and what it is not

**It is a correction to a premature closure**, not a rescue of a dead candidate. The distinction
matters and rests on one fact: **D258 named the sizing wrapper as a precondition before C1 was ever
screened.** Applying it is completing the registered test, not searching for a variant that passes.

**Five caveats, all real:**

1. **The vol target was chosen after seeing the breach data.** 0.4% is not pre-registered and a
   proper study must fix it in advance or sweep it and pay the multiplicity.
2. **In-sample throughout.** No holdout has been spent on this.
3. **The path is measured on EQUITY extended-hours bars, not futures.** 16 of 23 hours, and the
   futures path may differ.
4. **+4.41%/yr is gross of the firm's own costs** — evaluation fees, data, and the payout split.
5. **2020 is one event.** A single observation carrying an 87x improvement is a thin basis, however
   good the mechanism sounds.

**C1 moves from CLOSED to OPEN, pending a pre-registration that fixes the vol target in advance and
reserves a holdout.**

---

## C2 — SCREENED AND CLOSED, 2026-08-29. The direction is wrong.

**Pre-screen, D250 discipline: the bar was stated before looking** — `exposure x edge` net of
futures cost ≥ 3%/yr, hit rate > 55%, worst trade < 2%. **Prior stated at ~30%.**

Buy a within-session decline from the running session high, exit after `h` bars or at the close.
367,944 candidate bars, 16,748 sessions, SPY/QQQ/IWM/DIA, RTH only.

| threshold | horizon | setups | hit rate | **mean/trade** | net at futures cost |
|---:|---:|---:|---:|---:|---:|
| 0.30% | 4 | 182,871 | 51.4% | **−0.0017%** | −10.30% |
| 0.50% | 4 | 120,375 | 50.6% | **−0.0049%** | −12.53% |
| 0.75% | 4 | 74,386 | 49.3% | **−0.0102%** | −13.70% |
| 1.00% | 4 | 47,331 | 49.0% | **−0.0089%** | −7.76% |
| 1.50% | 8 | 19,364 | 48.3% | +0.0066% | **+1.34%** |

### All three criteria fail

| | required | measured | |
|---|---|---|---|
| `exposure x edge` net of futures cost | ≥ 3%/yr | **+1.34%** best cell | **FAILS** |
| hit rate | > 55% | **51.7%** best | **FAILS** |
| worst single trade | < 2% | **−4.56% to −6.52%** | **FAILS** |

**And the hit rate DECLINES as the threshold tightens** — 50.7% at 0.30% down to **48.7%** at 1.50%.
**The deeper the decline, the worse the odds of a bounce**, which is the exact opposite of the shape
P1 requires and the exact opposite of the premise.

### The finding is bigger than the cell

**Nineteen of twenty cells have a NEGATIVE mean return. Buying an intraday decline loses.**

> **The reversion this universe shows at DAILY horizons does not exist at INTRADAY horizons.
> Within a session, weakness CONTINUES.**

That is a clean split and it reconciles two bodies of evidence this programme had never put side by
side: **+16.83%, +18.31%, +37.42% and +89.74% after daily-horizon weakness**, against a negative
edge at every intraday threshold here. **Horizon, not direction, is what separates them.**

**The inverse is not a candidate either**, and it is worth saying so before anyone reaches for it
(D246 C3 forbids it in any case): the per-trade edge is roughly **0.5 bp**, so shorting it nets
**0.3 bp** after a 0.2 bp futures round turn — about **+0.34%/yr**. There is nothing on either side.

### One methodological caveat, stated

**The setups overlap** — every qualifying bar is counted, so consecutive bars share horizon. That
inflates the annualised magnitudes in both directions. **It does not touch the two decisive facts**:
the per-trade mean is negative and the hit rate is at or below 51.7%. **No annualisation turns a
negative edge positive.**

### What this does to C1

**C1 stays closed.** The √k component argument needed a second uncorrelated arm, and C2 was the
candidate. **With C2 dead, `k` remains 1 and C1's standalone figure stands at +1.87%/yr and twenty
accounts.**

**Remaining: C3 (opening-range), and C4 which was never a candidate.** The prop track has one
untested idea left.

### C2 — the two rescues tested, 2026-08-29. Neither works, and one leaves something behind.

**Asked whether book-level sizing or multi-symbol deployment saves C2.**

**Sizing does not, and for a different reason than C1's.** C1 had a **positive** edge too large for
the constraint, so sizing traded return for survival. **C2's edge is negative**, and `w x negative`
is negative for every `w`. **A confidence scalar is the right instinct and the gradient is
inverted**: hit rate falls **50.7% → 48.7%** and mean/trade worsens **−0.0017% → −0.0102%** as the
signal strengthens. **Sizing up on conviction makes it worse.**

**Multi-symbol does not either, because the edge is negative in EVERY asset class.** Re-run across
55 symbols of the 57-ETF 15m fixture, grouped into the classes a futures book actually spans:

| asset class | symbols | setups | mean/trade | hit rate |
|---|---:|---:|---:|---:|
| energy | 5 | 126,233 | −0.0034% | 50.0% |
| international equity | 14 | 110,381 | −0.0039% | 49.2% |
| sector | 20 | 340,415 | −0.0041% | 49.8% |
| equity index | 5 | 57,000 | −0.0078% | 49.7% |
| metals | 4 | 74,054 | −0.0089% | 49.8% |
| **rates** | 5 | 8,684 | **−0.0154%** | **48.5%** |

**Seven of seven negative, hit rates 48.5–50.0%.** A handful of single names print positive
(EWH +0.0095%, FXI +0.0056%) at ~50% hit rates — **that is noise, and selecting them would be
selection on the outcome.**

**Breadth multiplies whatever edge you have. C2's is negative everywhere, so more breadth buys a
more reliable loss.**

### What the multi-symbol question DID establish, and it outlives C2

**Effective breadth of the daily P&L series:**

| book | symbols | **effective** |
|---|---:|---:|
| 4 equity indices *(what C2 was screened on)* | 4 | **1.17** |
| **diversified futures complex** *(indices + energy + metals + rates + international)* | 12 | **3.00** |
| all 55 ETFs | 55 | 2.35 |

**A futures-complex book has 2.6x the breadth of an equity-index book — worth `sqrt(2.6) = 1.6x` on
IR for any candidate with a positive edge.** And note the third row: **55 symbols give LESS breadth
than 12**, the same saturation [FINDINGS §4](FINDINGS.md) measured on ETFs — adding correlated
sector names subtracts.

**This corrects how the prop track has been screening.** C1 and C2 were both measured on four
near-identical equity indices at effective breadth **1.17**. **Every future candidate should be
screened on the diversified complex**, and the `sqrt(k)` argument that C1 needs a partner for is
worth 1.6x before any second arm is even found.

**C2 remains CLOSED.** Neither rescue applies to a negative edge.
