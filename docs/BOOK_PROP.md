# The Prop Book

**Admitted arms: ONE — the MACD day-session arm, admitted 2026-09-13.** See the admission at the
foot of this page. The book is **one arm**, which is not the book this page was designed around:
the layering target needs four or five low-correlation components and there is one.

> **AMENDED 2026-09-18 ([D544](decisions/D544-the-front-page-is-the-least-honest-document.md)).**
> The paragraph immediately below says "It is empty" and the heading four lines above says
> "Admitted arms: ONE". **Both were written in good faith and they have contradicted each other
> since 2026-09-13**, when the MACD day-session arm was admitted and the heading was added without
> the body being amended.
>
> **The heading is the current state. The paragraph is kept, not deleted**, because this file is
> append-only and its authority rests on that: *amended in writing, never quietly edited.* Deleting
> the sentence would have removed the only evidence that the book was ever empty, and the fact that
> it was empty for the whole of its stated-standards period is the thing the paragraph was making
> a point about.
>
> Read it as: **this book was designed around being empty, and now holds one arm — which is not
> the book it was designed around.**

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

### ~~Does it clear P4?~~ — **NO. See the amendment of 2026-09-11 at the foot of this page.**

> **The answer below is a PER-HOLD statistic and P4 was ruled on 2026-09-11 to mean the ACCOUNT'S
> LIFE** ([R11](RULES.md#r11)). **The 6.40 years is `1 / (per-hold breach rate)`. The account's life
> at the same arm and the same sizing rule is 0.14 years** —
> [D440](decisions/D440-RESULT-the-gaussian-was-worth-five-sixths-of-the-value-and-it.md).
> **Both numbers are correctly computed; only one of them is P4.** The table below is left exactly
> as it was written.

~~**Yes, at a 0.4% volatility target:**~~

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

---

## C3 — SCREENED AND CLOSED, 2026-08-29. Fails all three, and on the opposite shape to the one predicted.

**Screened on the 12-symbol diversified complex (effective breadth 3.00), not the four equity
indices C1 and C2 used.** Range = high/low of the first `k` bars; break above goes long, below goes
short; exit at the session close. **Both directions pre-specified**, since a range break is
symmetric. **Bar and shape prediction both stated before looking. Prior: ~20%.**

| OR bars | side | trades | per sym-yr | hit | mean/trade | **skew** | net futures | worst |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | long | 19,716 | 99 | 52.6% | +0.0079% | **−0.80** | +0.58% | −16.36% |
| **2** | **long** | 17,841 | 90 | **53.2%** | **+0.0118%** | **−0.51** | **+0.88%** | −14.54% |
| 4 | long | 15,182 | 76 | 53.0% | +0.0128% | −0.55 | +0.82% | −10.63% |
| 1 | short | 19,365 | 97 | 48.0% | −0.0024% | −0.14 | −0.43% | −12.67% |
| 2 | short | 17,309 | 87 | 47.9% | −0.0128% | −0.31 | −1.29% | −10.56% |
| 4 | short | 14,402 | 72 | 48.6% | +0.0038% | −0.55 | +0.13% | −11.22% |

### All three criteria fail

| | required | best measured | |
|---|---|---|---|
| `exposure x edge` net of futures cost | ≥ 3%/yr | **+0.88%** | **FAILS**, 3.4x short |
| hit rate | > 55% | **53.2%** | **FAILS** |
| worst single trade | < 2% | **−10.63%** | **FAILS by fivefold** |

### The shape prediction was wrong, and the truth is worse

**Predicted: low hit rate with POSITIVE skew** — many small losses, few large wins, which P1
punishes because losses ratchet against the floor.

**Measured: hit rate ABOVE 50% and skew NEGATIVE at −0.51 to −0.80.** Frequent small wins with rare
large losses.

**That is the worse of the two shapes for P1**, and [D258](decisions/D258-the-prop-track-candidates.md)
said so before any of this was run: *"negative skew is fatal — one large loss breaches
immediately."* **A −10.63% trade against a 4% floor breaches at any size above 0.38x**, and at that
size the return is a fraction of an already-failing +0.88%.

### Two further findings

**The long side works and the short side does not** — +0.0118% against −0.0128% at OR 2. **That
asymmetry is consistent with drift rather than signal.** A long held from break to close captures
part of the intraday drift [D250](decisions/D250-the-overnight-gap-pre-screen.md) measured at
**+3.05%/yr since 2021**; at ~15% exposure that is roughly **+0.46%/yr of the +0.97% gross**.
**About half the edge may be drift, and a matched-exposure null would be required to separate them
— which the cell does not clear the bar to justify building.**

**The era split runs opposite to D250's gap.** 2020 **loses** (−0.0533%/trade), 2010–19 is flat
(+0.0038%), and **2021–26 carries it** (+0.0286%, hit 53.9%). Different pathology, same lesson: the
edge is one era, and it is the recent one.

**By asset class**, international equity leads (+0.0355%, hit 55.4%) — **but selecting it after
seeing it is selection on the outcome**, and it is named here only so that nobody proposes it later
as though it had been predicted.

**C3 is CLOSED.**

---

## The prop candidate list is now exhausted

| | state |
|---|---|
| **C1** — session-boundary hold | closed standalone (+1.87%/yr, 20 accounts); open as a component, **but there is no partner** |
| **C2** — intraday reversion | closed — negative edge in **all seven** asset classes |
| **C3** — opening range | closed — fails all three, negative skew |
| **C4** — sizing wrapper | never a candidate. **The vol-targeting method survives and is the track's one durable output** |

**[D258](decisions/D258-the-prop-track-candidates.md) fixed four candidates in advance and all four
are now resolved.** A fifth would need a new mechanism, not a new parameter — and it would need to
clear a bar that has now rejected three constructions on **shape** rather than on return.

---

## The hurdles admit; nothing here has ever ranked — D379, 2026-09-08

**[D379](decisions/D379-the-prop-account-is-a-down-and-out-call-and-hurdle-P-has-no.md)
is a FRAMING note, not a measurement, and it reopens no candidate.** It records that a funded account
is a **down-and-out call** — component for component, with P1 as the knock-out barrier and P5 as a
constraint on the payoff path — so its value is `E[payouts | survival] × P(survival)`, **non-linear
in size with an interior optimum.** Hurdle P is six thresholds on components of that expression and
**never states the expression.** Every candidate above was screened pass/fail; **nothing in this
track has ever ordered two eligible candidates.**

**Three consequences that land on what is already written on this page:**

1. **C1's size sweep is unfinished, and the table above is why.** Its **"profit before breach"**
   column *is* `E[payout]`, measured on our own fixture — and it falls monotonically across every
   size tested (**28.20% → 1.75%**) while annual return rises monotonically (**+4.41% → +13.04%**).
   The value maximum therefore lies **at or below 0.48x, the boundary of the sweep.** The sweep
   stopped where P4 was cleared, so **the value-maximising size for C1 was never searched.**
2. **The payout ladder is the missing input, and it stops the answer being "size to zero".** This
   page already notes that 28.20% "comfortably exceeds the payout ladders these firms cap at" — so
   the payoff is **capped**, and past the ladder extra survival buys nothing. **The right size is the
   smallest that reaches the ladder with high probability, not the smallest that survives.** **No
   record here holds MyFundedFutures' ladder terms**, and §4 of D379 is not computable without them.
3. **P5 has a mechanism, and it is not venue friction.** Near the barrier the account's convexity
   inverts — variance becomes free once the option is nearly worthless — so **P3 and P5 are the
   firm's defence against a risk-shifting incentive the instrument creates.** A construction
   exploiting it would **clear P1 and P4 and be killed by P5**, which is an argument for computing
   P5 ahead of the other legs
   [D375](decisions/D375-the-hurdle-audit-the-stage-one-gates-are-sound-and-hurdle-P-is.md)
   lists as never computed.

**This amends no hurdle and loosens no threshold.** Under [R8](RULES.md#r8) each of the three needs a
pre-registration before it runs. **And the binding limit is unchanged: a valuation framework
allocates an edge, it does not supply one — the candidate list is exhausted, so there is nothing to
value.**

### The account is PURCHASABLE, so the object is a portfolio — D379 amendment, 2026-09-08

**The framing above values one account. Accounts are bought, in quantity, at a known price**, so the
full object is `V = N × [ P(pass) × E[payout | funded] − fee ]` with `N` purchasable, and
**`fee ÷ P(pass)` is the acquisition cost of one funded account** — the premium amortised over the
evaluations that fail. **This is where the "20 accounts needed for $50k" line above actually lives.**

**`P(pass)` is computable now, from machinery [D259](decisions/D259-the-extended-session-and-the-overnight-interior.md)
already built** — the same MAE-against-a-ratcheting-floor simulation, stopped at a profit target
instead of run to breach. **It is the cheapest of the open items and it is the missing half of the
ladder question above.** Owed a pre-registration like the rest.

**One measured consequence for P1, from the amendment's illustration.** At zero edge, on a
Topstep-like +3,000/−2,000 eval, a **static** floor gives the optional-stopping 40.0% while the
**trailing** floor gives **26.5%** — the ratchet costs roughly **13 points of pass rate**, and the
40% is recoverable only by betting the entire buffer on one trade. **That is this page's own P1
objection quantified from the eval side**, and it is the same convexity D379 §5 found near the
barrier: **when the edge is low, the knock-out rewards variance.**

**What it does NOT license.** The source claims pass rate is the only thing worth optimising and that
"strategies that do not work on live will work on prop firms". **Both are false**: `P(pass)` is a
function of edge, cost and the firm's geometry, and at zero edge it is pinned by optional stopping
regardless of strategy. **Prop rules can make a live-profitable strategy fail; they cannot make a
zero-edge one pass.** [R15](RULES.md#r15) is untouched — **a candidate is still screened on gross
mean per trade above its nulls, and `P(pass)` sits downstream of that.**

---

## AMENDMENT, 2026-09-11 — **C1 DOES NOT CLEAR P4, AND THE CANDIDATE LIST IS EXHAUSTED ON THE RIGHT STATISTIC**

**The principal ruled on 2026-09-11 that P4 means the ACCOUNT'S LIFE, not a per-hold breach rate
inverted** ([R11](RULES.md#r11), RULING). **This page asserted C1 clears P4 at 6.40 years. Under the
ruling it does not.** Nothing above is deleted; the §"Does it clear P4?" heading carries a pointer
to here.

**The operative numbers**, from
[D440](decisions/D440-RESULT-the-gaussian-was-worth-five-sixths-of-the-value-and-it.md),
MFFU Rapid EOD 50K, SPY, D259's own vol-targeting rule, measured path:

| daily vol, fraction of account | 0.2% | 0.4% | **0.7%** | 1.1% |
|---|---:|---:|---:|---:|
| **funded life, years** | **1.01** | 0.31 | **0.14** | 0.06 |
| `V` per evaluation | −168 | −23 | **+78** | +3 |

> **P4 needs three years. Nothing on the grid clears it, the best cell anywhere is 1.01 years, and
> that cell's `V` is negative.** Not one simulated path of 3,266 is alive at the 600-day horizon.

**And `V` itself is unresolved, not positive.** Circular block bootstrap on the hold sequence:
**0.99 / 0.72 / 0.69 SE at `b` = 1 / 20 / 60**, against a 2-SE bar. **2021–2026 alone is `+51 ± 223`.**

### What this does and does not do to C1

- **C1's REOPENING stands as written.** It was a correction to a premature closure, and applying the
  registered sizing wrapper was completing the registered test. **What has changed is that the
  reopened candidate fails the hurdle it was reopened to clear.**
- **The edge is still real and still era-stable.** +9.04%/yr overnight, +8.55% and +8.28% either
  side of 2020. **Nothing here touches [R15](RULES.md#r15)** — C1 remains a signal that pays gross.
  **What fails is the INSTRUMENT's geometry against that signal's path.**
- **It does not close C1**, and under R15 this page cannot. **C1 remains OPEN as a component**, per
  the 2026-08-29 clarification that a P4 closure closes a standalone book and not a component —
  **and there is still no partner**, C2 and C3 both having died.
- **The vol-targeting wrapper remains the track's one durable output.** D440 measured it working
  exactly as D259 said it does: on the SHUFFLED control, where there is no volatility clustering to
  exploit, vol targeting **destroys** value (654 → 344). It is an instrument for clustering, it is
  in the measured number, **and it is not enough.**

### What the track now knows that it did not

**The damage is CLUSTERING, not kurtosis.** D440's two controls separate them: a Gaussian at matched
mean and vol is worth **$770**; the same holds drawn i.i.d. — fat marginal kept, sequence destroyed —
**$654**; the historical sequence **$78**. **The fat marginal is 14–18% of the gap on all four
symbols; serial structure is the other 82–86%.**

> **So the remedy a fifth candidate needs is not a stop, a smaller size or tail insurance — those
> address the 14–18%. It is anything that reduces exposure during clustered adverse periods.**
> **`O1` in the [candidate ledger](research/Prop-Firm-080926/24-candidate-ledger-both-books.md) — a
> volatility-regime day classifier used as an ABSTENTION rule, "and it is not an edge" — is exactly
> that shape**, and this is the first quantitative reason to run it rather than a general prior that
> it ought to help.

**And the screening method itself is now on notice.** All four D258 candidates were screened on
per-trade bars — C1 on per-hold MAE and breach, C2 and C3 on *"worst single trade < 2%"*. **C2's and
C3's verdicts stand, because they died on edge sign and on skew and those are lens-invariant. The
bar was still the wrong bar.**

**Admitted arms: still none.** The statement at the top of this page is unchanged, and it is now
unchanged for a better-measured reason.

---

## C-13.1 — MARKET INTRADAY MOMENTUM, SCREENED ON ES ITSELF AND CLOSED, 2026-09-12

**The data.** The CME one-minute archive (D462): ES, NQ and YM regular-hours fixtures, front
month by measured volume, gated, **usable from 2016-01-04** — the archive lacks the index
futures' day session on most days before then (21–42% of the calendar in 2010–2012). RTY's
fixture failed the cross-check gate on the 2020-03-16 limit-down open and is not committed.

**The candidate** (lane 13's only near-miss): the sign of the day's return to 15:30 predicts the
last thirty minutes; long or short at 15:30, flat at the close. Pre-registered as
[D463](decisions/D463-market-intraday-momentum-the-last-30-minutes-on-ES-NQ-YM-RTY.md)
with the lane's five criteria, the enumerated sign-rotation and sign-randomisation nulls, futures
cost as a quote, and **hurdle P's P3, P4 and P5 computed for the first time on anything.**

| ES, 2016–2023, 1,894 trades | |
|---|---:|
| mean per trade | **+1.18 ± 0.86 bp**, median 0, hit **49.3%** |
| slope on rROD (×100) | **+1.8**, t 1.1 (published: 6.18); post-2018 +2.1 |
| exact rotation p95 / sign null p95 | +1.10 / +1.22 |
| net of $17 round trip | +0.07 bp |
| MAE inside the window, one contract | p50 $175, p99 $1,641, worst $4,000; > $1,000 on 4.4% of days |

**Hurdle P** (MFFU Rapid EOD 50K, C4 sizing on the measured path): at f = 0.2–0.4% the rule sizes
**below one whole contract** on most days; at every size that trades, **P3's worst day is −4% to
−8% (13–87 breaching days), P4's funded life is 0.07–0.20 years against three, and V is negative.**
**The size scissors the ledger described, measured: a 30-minute σ of ~$650 per contract on a
$50k account puts the floor three σ away per trade.**

**CLOSED on this window.** F1 and F3 fail; no f clears hurdle P. The 2024–2026 slice is unread.
NQ (net +0.92 bp, slope t 1.7) is reported, not selected. **What outlives the candidate:** the
hurdle-P machinery on an intraday path, and the arithmetic that any single-contract ES
construction at this per-trade σ fails P3/P4 on this account size regardless of its edge.

---

## THE PERSONAL ARMS AS GATES ON THE SESSION HOLD — TESTED ON ES AND CLOSED, 2026-09-12

The principal asked whether S1 and S2 could be tried on the futures data for this book. **They
cannot be ported as they are** (15-day and 63-day holds across the flatten); the one form the
venue allows is C1's 18:00 → 16:00 hold taken only on the nights the arm's state is on, the state
computed on SPY with the book's own functions. [D464](decisions/D464-the-personal-arms-as-gates-on-the-session-hold-S1-and-S2.md),
2,043 ES holds 2016–2023:

| nights | share | mean bp | MAE p99 bp | exact rotation p95 |
|---|---:|---:|---:|---:|
| all | 100% | +5.5 ± 2.0 | 369 | — |
| S1 on | 8.7% | +13.8 ± 10.0 | 321 | +16.7 |
| S2 exposure on | 10.0% | +9.1 ± 4.7 | 321 | +16.7 |

**Both arms pick better and calmer nights than average, and not distinguishably from a random
tenth of the nights.** Hurdle P at whole ES contracts: one contract's overnight σ (~$2,000) is the
4% floor, so the C4 rule sizes zero up to f = 0.7% and a fixed contract breaches the daily limit
on 791 of 2,043 nights. At micros the size is expressible: survivable sizing earns **+0.2 to
+2.2% a year**; the gates lengthen the account's life to at most **1.94 years, at +0.8% a year**,
by removing 90% of the exposure — the ledger's own definition of *an exposure cut with a story*.

**CLOSED.** The personal book's entries are unchanged. **The prop track's binding constraint is
the instrument–account pair** — an ES position on a $50k account needs a per-holding-period σ
well under $300 to clear P3 and P4, and neither a night nor a half-hour on the index does that
at any size worth the evaluation fee. **Admitted arms: still none.**

---

# THE ES CHAIN FOLDED IN — six records, 2026-09-11 to 2026-09-12

**C1 is now measured END TO END ON THE INSTRUMENT.** Everything below was run on ES itself, not on
the extended-hours equity proxy, once the Databento acquisition completed
(`ohlcv-1m`, 2010-06-06 → 2026-09-09; the ES subset is preserved as
`data/fixtures/es_minute_bars.parquet`, 6.8M rows).

> **C1 FAILS P4 ON THE INSTRUMENT BY ELEVENFOLD. `O1` is resolved and fails. The hold-length
> curve has no optimum, at any length from 30 minutes to 20 days. The prop candidate ledger is
> empty of unscreened entries.**

## What each record settled

| | |
|---|---|
| **[D440](decisions/D440-RESULT-the-gaussian-was-worth-five-sixths-of-the-value-and-it.md)** | D386 valued a **Gaussian** trader at `$770`/evaluation; the measured path is worth **`$78`**. **82–86% of the damage is CLUSTERING, not kurtosis.** `T1` unresolved, `T2` FAIL, `T3` unresolved. *(Already amended into this page 2026-09-11, with the R11 ruling it forced.)* |
| **[D442](decisions/D442-RESULT-O1-clears-the-ledgers-own-criterion-and-dies-inside-the.md)** | **`O1`, the last unscreened ledger entry, is resolved.** It clears the ledger's own inherited criterion (`G1`: floor-touch −59.4% against P&L −28.6%) and **dies inside an enumerated rotation null** — 70 against a rotation median of 72. **Plus an independent kill: 88 consecutive flat sessions against MFFU's 7-day inactivity rule.** Its [addendum](decisions/D442-ADDENDUM-the-two-apparent-wins-were-selection-across-four-risk.md) found two apparent wins were **selection across four risk fractions**, the premium larger than the effect |
| **[D451](decisions/D451-RESULT-the-complete-acquisition-T1-is-testable-and-the-cash.md)** | **The settlement kill-check is closed on all three regimes.** T+1 testable at last (432 pairs); the cash-futures gap **tracks the rate cycle, not the settlement rule** |
| **[D452](decisions/D452-RESULT-D440-on-the-instrument-same-verdict-and-clustering.md)** | **D440's full study, on ES.** Same verdict. **Clustering explains 94.1%** against the proxy's 82.9% — and ES's kurtosis is *higher* (18.82 vs 14.96), so **more fat tail and less damage from it** |
| **[D458](decisions/D458-RESULT-the-hold-length-curve-has-no-identifiable-optimum-and.md)** | **The hold-length curve, 30 min to 22 h.** The PATH bound is real and monotone; the VALUE curve has **no identifiable optimum** — observed argmax 507 against a null median of **917**, `p` = 0.760 |
| **[D459](decisions/D459-RESULT-beyond-22-hours-the-shape-constraints-lever-does-not.md)** | **Beyond 22 h, to 20 days.** A twentyfold change in hold length moves daily sd **1.042% → 1.065%.** `p` = 0.883 on the argmax |

## The one structural finding, because it retires a standing claim

**The prop research's shape constraint — *"THE SCISSORS CLOSE ON LONG WINDOWS, NOT ON SMALL
EDGES"* — was the single most actionable claim in that review and the last route to a fifth
candidate. It has now been tested on its own range and is NOT SUPPORTED.**

> **The argument is about PER-HOLD σ: a longer window carries more standard deviation, so one
> contract makes the `$150` day, so the contract count stays under the 4% ceiling.**
> **But the MLL ratchets DAILY and the qualifying threshold is DAILY. Nothing in the rulebook ever
> sees a hold.** Marked daily, a 20-day hold is twenty ordinary days.

**The lever is real at the frequency the strategy is described in and absent at the frequency the
account is judged at.**

**It is NOT refuted as an observation about the SEARCH** — every prop rejection in that review
really was a size rejection, and **[D463](decisions/D463-market-intraday-momentum-the-last-30-minutes-on-ES-NQ-YM-RTY.md)
measured exactly that from the other side**, at a 30-minute σ of ~`$650`/contract putting the floor
three σ away per trade. **What fails is the inference that widening the window fixes it.**

## Where C1 stands

**Closed standalone on P4, on the instrument.** Funded life **0.27 years against three** at the
`V`-maximising size, nothing on any grid clearing three years at any hold length. **The edge is
untouched** — the overnight drift is real, era-stable, and present in ES itself at
**+5.95%/yr** (D451). **R15 is untouched with it.** **What fails is the instrument's geometry
against that signal's path**, and it now fails there on the instrument rather than on a proxy.

**C1 remains OPEN as a component** under the 2026-08-29 clarification, **and there is still no
partner.**

## What the chain leaves

1. **A hold whose length is CONDITIONAL rather than a fixed calendar rule.** Every `k` in D458 and
   D459 is a clock. **A state-dependent exit is a different object and is untouched.**
2. **The `q − r` regression** (D451 §6) and the **thin-print explanation** for why the equity proxy
   *overstates* excursion (D449 amendment 2, D451 §3) — both candidates, both unmeasured.
3. **A fifth candidate still needs a NEW MECHANISM.** Nothing in the hold length, the gating, the
   instrument or the settlement rule was hiding one.

**Admitted arms: still none.**

## THE OVERNIGHT LINE CLOSED FOR THE PROP BOOK BY THE PRINCIPAL, 2026-09-12 (OPEN FOR THE PERSONAL BOOK)

**Closed by the principal, in writing, after D466–D473.** The chain: the components ledger
(D466) scored every overnight and session-window construction at minimum size and the cost that
size pays — the $3 micro round trip is ~2 bp of notional and takes 30–70% of the gross overnight
mean on ES/NQ, so no window on eight roots clears net Sharpe 0.5 (D468). The one conditioning
that concentrated the drift in-sample — the leg after a **negative** overnight leg, the
principal's continuation hypothesis reversed (D470) — cleared the single-cell nulls, failed the
family-maximum bar on every scale (D472), replicated on SPY/IWM cash 2010–2015, and **failed
its declared forward test 2024–2026 (D473: REMOVED; the drift was strong on both sides of the
gate and the cash sign reversed)**. The literature explains it: the index overnight drift was
compensation for closing order imbalances, concentrated at 2–3 a.m. ET, and has been ~zero since
2021 because the imbalances compressed (Boyarchenko–Larsen–Whelan, NY Fed, RFS 2023 and
July 2026). **What the prop book cannot carry is the cost per round trip against a drift whose
gateable structure is gone**; the unconditional drift is real and is the personal book's to
consider, at full size, where the cost is 0.34 bp.

**Spent by this line:** the 2024+ futures slice for the 18:00 → 09:00 leg on NQ and ES (both
sides), the cash 2024+ reserve on SPY and IWM (gap and close-to-close). **Unread:** 2024+ on the
day leg and full session beyond what the leg implies, every other root, the last-30 constructions.

**Closed for the prop book:** any gate, window or size on the index overnight leg at micro cost.
**Open for the personal book:** the unconditional overnight hold at full size (C1 as a personal
component; D466's ES lens net +0.48 at one ES and $17) — a separate record, under BOOK.md's
standards, if the principal takes it there.

---

## AMENDMENT, 2026-09-12 — **the standards moved, and the track now contemplates TWO accounts**

*Directed by the principal. Recorded here because this page restates hurdle P, and that
restatement is now out of date in two places.*

### P4 and P5 were relaxed — see [R11](RULES.md#r11)'s restatement of 2026-09-12

| | was | now |
|---|---|---|
| **P4** | expected account life > **3 years** | **not a hard hurdle.** Binding test: **expected profit before breach > the account's cost** (fee or reset). Account life ≥ 1 year preferred, not binding. Both reported. |
| **P5** | no single day > **40%** of trailing-year profit | **not a screen and not a hard constraint.** A **30% single-day haircut** is applied to profit for calculation purposes: `recognised = total − max(0, best_day − 0.30 × total)`. Nothing is rejected for lumpiness; it is **discounted** instead, and the discount is visible in the number. |

**P1, P2, P3 and P6 are untouched.** P3's worst-day ≤ 2% in particular is a venue-enforced daily
loss limit and no amount of account-replaceability softens it.

**The `profit before breach` column in the vol-targeting table above is now a BINDING statistic
rather than a curiosity** — it was already computed (28.20% at 0.48× average size, 14.71% at
0.71×) and it is what the amended P4 tests against the fee. **It must be recomputed on
RECOGNISED profit**, i.e. after P5's 30% single-day haircut, because **P4 and P5 now compose**:
the profit P4 tests is the profit P5 has already cut. The figures in that table are pre-haircut
and are therefore upper bounds until recomputed.

**Which closures this touches.** A closure that rested on P4 alone is reopened. **C-13.1 stays
closed**, because it failed P3 (worst day −4% to −8% against ≤ 2%) and had negative V
independently of P4; the P4 clause in its verdict is now surplus rather than load-bearing. The
overnight-leg closure stands on its own terms — K7 was removed on a **forward read**, not on P4
or P5.

### Two accounts, two books

`COMPONENTS_PROP.md`'s C-b no longer rejects a component for correlating with one already
entered; it **routes it to a vault**, from which a **second book on a second account** is built.

**The reason is the drawdown floor, not diversification for its own sake.** Each prop account
carries its **own independent 4% trailing floor**. Two correlated books on one account share a
floor and correlation is fatal. **On two accounts they do not share a floor**, so a construction
whose only defect was duplicating a risk already taken becomes viable the moment it is taken on a
separate budget.

**Hurdle P is tested PER ACCOUNT**, on that account's own assembled book. There is no combined
hurdle-P test, because there is no combined floor. **Cross-book correlation is reported in both
books and gates nothing.**

**And a second account is a second fee**, which under the amended P4 enters the arithmetic
directly: **two accounts must clear two cost bars.** A vault component earns its account only by
clearing profit-before-breach against that account's own fee.

**This page still records no admitted arm, on either account.** The vault was created empty and
no prior verdict is reversed by these changes.

---

## THE LEDGER HAS ITS FIRST ENTRY, PROVISIONAL AND PARKED — K8, 2026-09-12

**This page still admits no arm.** What changed is one level below it: [`COMPONENTS_PROP.md`](COMPONENTS_PROP.md)
entry **#1, K8 — long one MNQ from the 09:30 open plus a tick to the 15:59 close on days after the NQ
day session closed below its open** (≈ 44% of sessions, about twice a week). In-sample 2016–2023 (D498):
gross +$17.87 a trade against $3 (+11.6 bp, SE 4.0; median +$20.50), hit 57%, skew −0.02, 6 of 8 years
and both sub-periods, the other side (after up days) −3.1 bp, difference z +2.89 against the family
p95 of +2.41, **net Sharpe +0.61 (SE 0.32) at one micro**, no day below −2% of a $50k account.

**Why it is PROVISIONAL and not full.** The cell was seen as a control in D495 before D498 declared it;
that provenance is selection, and no in-sample bar cures it. The promotion rule is pre-registered in
D498 §3: a forward read of 2024-01-02 → 2026-09-09 (FULL if the forward gross mean > 0, net Sharpe > 0
and the after-down minus after-up difference has z ≥ 1; REMOVED if the net Sharpe < −0.3 or the
difference is negative; otherwise it stays PROVISIONAL).

**The principal parked it on 2026-09-12: the forward read is HELD.** The 2024+ day session is the only
unseen slice the prop line has on the futures fixtures, and the ledger confirms the *assembled book*
on that same slice. Reading it for K8 alone would make the book's later confirmation a re-read for K8,
and one component at ≈ 0.6 is not a book. So the read waits for a second component (a different
instrument or a different state; ρ < 0.3 with K8), and then K8's promotion, the second component's
promotion and hurdle P on the assembled book are read together in one pass on 2024+. K8 is not
sharpened, filtered or re-scored in-sample while it waits. ES is the same sign at half the size
(+4.9 bp, Sharpe +0.18, inside its null, ρ ≈ 0.85 with NQ) and is not a second component.

**What this page needs before its first arm:** a second ledger entry, then the one-pass forward read,
then hurdle P (all six) on the assembled book on that account's own floor.

---

## THE HOURLY CLOCK CLOSED FOR THE PROP BOOK BY THE PRINCIPAL, 2026-09-13

**Closed by the principal, in writing, after D499.** The construction tested was the principal's own
direction of 2026-09-12: a 24-hour future, a rule not limited to the off-hours but preferring them.
Stage 0 faded the hour after a top-decile hourly move on all eight gated roots, every entry hour
from 18:00 to 14:00 ET, thin against thick by volume, with an exact enumerated rotation per root
and a sixteen-cell family bar. **Fifteen of sixteen component lines are negative at one micro; the
best gross cell is +$2.46 a trade against a $3 fee; the family p95 of the z is +2.70 and the
observed maximum +1.84, which 43% of rotations reach.**

**What closes it is arithmetic, not the signal.** The fee is **14.5% of the expected hourly move on
MNQ's thin hours and 7.1% on its thick hours, against 2.4% for the whole day session**; break-even
accuracy rises to 57.2% where no cell in the family exceeds 53.1%; on ZN and ZB one crossed tick is
14–80% of an hourly move in every hour. Shortening the horizon multiplies cost against move by
three to six times, so the accuracy required passes anything this programme has measured
(FINDINGS §69, §70).

**What is real and is kept as a measurement, not a trade.** The next-hour reversal of the last hour
is genuine on the **US clock** and absent on the volume partition: pooled β −0.043 on ES, −0.037 on
YM, −0.028 on NQ over 18:00 → 08:00, outside exact rotation bands of ±0.014, flat inside the day
session; crude *continues* at +0.030. Trading it earns 1.7 ticks on ES and 4.9 on NQ, clears its own
null on both, and is net negative after the fee. The thin-book mechanism is refuted on its own
terms: low-relative-volume moves revert **less**, on seven of eight roots.

**Closed for the prop book:** any hourly-horizon construction on these eight roots at micro cost.
**Spent:** nothing — 2024+ is unread on every root under D499.
**Open:** a session-long hold on a non-index root, gated on a daily state, which the overnight
closure does not name and whose fee is 4–7% of the move rather than 14%. Not started.

---

## THE FORWARD READ IS TAKEN AND THIS PAGE STILL ADMITS NO ARM — D503, 2026-09-13

**On the principal's word**, the one-pass read this page had been waiting for was taken on
**2024-01-02 → 2026-09-09** for K8, the MACD component and the assembled two-arm book together.
**That slice is now SPENT for all three.** Full numbers in
[`COMPONENTS_PROP.md`](COMPONENTS_PROP.md) and
[D503](decisions/D503-RESULT-the-Sharpe-transferred-and-nothing-else-did-one-MNQ-has.md).

**The book was assembled and it fails hurdle P.** Net Sharpe **+0.364** — *worse than its best
arm alone at +0.736* — with **P3a at 6.96 breaches a year against a bar of 1.0**, **C-d's σ at
$534 against $500**, a worst day of **−$2,724 = 136% of the account's entire $2,000 loss budget**,
and an **empirical trailing-4% life of 31 sessions across 20 deaths**. The single admission gate
is hurdle P all six, and it fails on P3a. **No arm is admitted.**

**What the read actually established, and it is not about either signal.** Daily σ nearly doubled
on an unchanged strategy, $180 → $340, because **MNQ pays $2 an index point and NQ's level
roughly doubled** between the in-sample window and 2026. **At 2026 price levels one MNQ is too
large for a $50,000 account with a $2,000 trailing floor** — the single-arm worst day is 88% of
the whole loss budget — and **there is nothing smaller than one micro.** [D493](decisions/D493-RESULT-the-account-size-lever-fixes-the-fee-and-runs-into-the.md)
found the full contract too big for this floor; the micro is now too big as well.

**So the binding constraint on this page has changed.** It was "find an edge that survives the
fee". It is now **"find an account whose floor fits one micro at today's index level"** — a
larger account, a cheaper-per-point instrument, or a venue with a wider drawdown. That is a
question about the vehicle, not about a signal, and it is the principal's to direct.

**What is NOT closed:** the constructions. Forward gross is **+$19.68 a trade against a $3.50
cost** — the signal pays. Closing an avenue is the principal's, and nothing here closes one.

---

## TWO CLOSURES BY THE PRINCIPAL, 2026-09-13 — K8, AND THE CROSS-MARKET-INTO-THE-OPEN LINE

**K8 is CLOSED.** It was taken forward in D503 (the one-pass read of 2024-01-02 → 2026-09-09) and
did not transfer: gross **−$4.46** a trade against **+$17.87** in sample, hit 50.6% against 57%, net
Sharpe **−0.160**, the after-down minus after-up difference **+0.2 bp at z +0.02** against +2.89.
D498's own rule returned PROVISIONAL, because REMOVED needed a Sharpe below −0.3 *or* a negative
difference; the principal has closed it on the reading that a **negative gross mean** is the answer
the rule failed to name. **The ledger's entry #1 is closed, not parked.** ES K8, dismissed in sample
as "the same sign at half the size", is the arm that worked forward — which is what noise looks
like. The slice is spent; nothing may be re-read or re-scored on it.

**The cross-market-into-the-open line is CLOSED** (D494 at index level, D504 cross-sectionally).
The Asian chip channel into US semiconductors is real and semis-specific — the SMH-minus-QQQ
overnight gap loads +0.45 on Taiwan — and it clears **entirely in the opening auction**: **+25.65 bp** per unit
sigma into the relative gap at t +4.25, against **−1.65 ± 2.6 bp** into the 09:45 → 16:00 day session.
The traded primary earned +8.0 ± 8.4 bp against 11.7 bp crossed, inside its own exact rotation, with
yearly means +5 / −27 / +39 / −5; the family maximum was a **control sector with no mechanism**
(transports, +27.97 bp, hit 61%, 0.8th percentile of its own null). The prop-eligible expression
(MNQ vs MES) was net −$19.76 a trade against $6.

**Closed for the prop book:** any construction that reads a foreign market before the US open and
enters at or after that open. **What is not closed and is recorded as a measurement** (FINDINGS §71):
the gap-versus-day decomposition, which says the channel could only ever be traded **in** the gap,
needing pre-market execution and a different cost model; and the vehicle measurement that the
unconditional MNQ/MES pair's daily σ is **$128 against one MNQ's $282**, the only construction that
lowers the dollar σ without leaving the micro. **Spent:** nothing on the 15-minute fixtures.

---

# THE FIRST ARM IS ADMITTED — the MACD day-session arm, 2026-09-13

> *"Retire K8 as closed and admit the MACD into the book."* — the principal

**This page is no longer empty.** [`COMPONENTS_PROP.md`](COMPONENTS_PROP.md) entry **#1 (K8) is
retired as CLOSED** and entry **#2, the MACD day-session arm, is admitted** as the book's first
and only arm.

## The arm, specified exactly

**NQ front month by volume, traded as one MNQ. Day session only.** Decide at the close of each
hour from **h09**; execute at the next hour's open. **Enter** when the log Impulse MACD (34/9) and
the plain log MACD histogram (12/26/9) **agree in sign** (`md == 0` is a no-trade state).
**Exit** when the signal turns, after a **minimum hold of 5 hours**. **Forced flat at the close of
h15 (16:00 ET).** Cost **$3 + 1.009 ticks = $3.50** a round trip. Both indicators at published
defaults, never tuned.

## Hurdle P, all six, on 2016-01-04 → 2026-09-09 (2,508 sessions)

| | | |
|---|---|---|
| **P1** sizing rule | **+$2,582/yr** post-sizing at one MNQ | **PASS** (a number; cannot fail) |
| **P2** flat across the flatten | exit 16:00 ET, inside MFFU's 16:10 | **PASS** by construction |
| **P3a** breaches/yr ≤ 1.0 | **0.50/yr** — 5 breaches, one every 2.0 yr | **PASS** |
| **P3b** life cost ≤ 33% | **10.0%** — life 137 → 123 sessions | **PASS** |
| **P3c** worst day, reported | **−$1,761** = −7.6σ = **88% of the $2,000 budget** | reported, not a gate |
| **P4** E[profit] > fee | **$985** before breach, E[life] 96 d, against a **$209** fee | **PASS** |
| **P5** 30% single-day haircut | best day **10.3%** of total → haircut **$0** | **PASS** |
| **P6** automation when funded | **MyFundedFutures** (Topstep's overnight sources conflict) | a venue choice |

**All six clear.** That is the admission gate this page has held since it was written, and this is
the first construction to pass it.

## What the arm is worth, under the published rules rather than raw P&L

[D505](decisions/D505-your-expectation-is-a-Sharpe-1-34-strategy-and-the-real.md)
ran D386's lifecycle model at the arm's measured Sharpe and its **forced** size:

| | |
|---|---:|
| **V** — expected dollars paid out less fees, per $209 evaluation | **+$600** |
| P(pass the $3,000 evaluation) | **43.2%** |
| **P(ever being paid a cent)** | **20.4%** |
| median funded days | 94 |

**V is positive at ~2.9× the fee and the MODE of the payout distribution is zero.** Four accounts
in five return nothing. That is the honest shape of the opportunity and it is admitted with that
stated, not in spite of it.

## The four qualifications this admission carries

1. **The book is ONE ARM.** `S_book = S·√k/√(1+(k−1)ρ)`: at ρ = 0.2 five arms at +0.70 reach only
   1.16, and **at ρ = 0.3 no number of arms exceeds 1.27.** The layering target is unmet and
   **ρ matters more than count** — which makes the next four arms a search for *different
   underlyings*, not more rules on NQ (ρ was 0.70 between K8 and the ungated NQ day session, 0.85
   between NQ and ES on one construction).
2. **It is a regime construction.** 2020 + 2022 + 2025 + 2026 carry **96%** of the total.
   2016, 2017, 2019, 2023 and 2024 are flat to negative. A flat year returns **+$14** of V against
   a $209 outlay.
3. **P3a passes pooled and fails in the recent years alone** — 2.14 in 2022, 2.17 in 2025, 1.53 in
   2026 against a bar of 1.0. **C-d likewise**: $233 pooled, **$386 in 2026** against a $500 cap.
   One MNQ is now **1.10× the account's notional** against 0.18× in 2016 (D504 §4). Both margins
   are thinning with the price level, not with the signal.
4. **Every figure is an upper bound on fills** — open-of-next-segment at the measured half-spread,
   no queue, no partial fills. The worst day, which P3 reads, is the figure most exposed to that.

**Provenance.** D484 (signal, first PASS against a rotation null) · D491 (state machine) · D495
(pre-registered, the cell selected) · **D503 (the forward read of 2024-01-02 → 2026-09-09, taken
once on the principal's word under a rule declared beforehand: FULL at net Sharpe +0.736, gross
+$19.68 a trade)** · D504 (full 2016–2026 history, +35.3 SE over its rotation null) · D505
(the payout arithmetic). **That slice is spent and may never be re-read for this arm.**

---

## THE IN-PLAY CONSTRUCTION CLOSED BY THE PRINCIPAL, 2026-09-13 — AND ITS PREMISE KEPT AS A STANDING INSTRUMENT

**Closed by the principal, in writing, after D506:** conditioning a day-session signal on how active
the overnight session was, as a way of choosing *when* to trade for a better edge. On eight roots and
two signals the repo already owns, the filter bought **+0.85 points** of fee dilution (positive in 16
of 16 cells, about +0.10 of Sharpe, exactly what the premise promised) and cost **−2.09 points** of
directional accuracy (negative in 11 of 16). The primary cell, the Dow micro with the log MACD, ran
at **47.98% accuracy in play against 51.05% on the rest**, losing **$10.61 a trade gross** where the
rest made $2.10. No cell cleared the 16-cell family bar: p95 **+0.2192** against an observed maximum
of **+0.0620**, which **97.8%** of the 1,978 exact offsets beat.

**What closes the whole family rather than this version of it:** the untradeable bound. Conditioning
on the day's **realised** range, which nobody can do in advance, is **−0.0018** on the primary. There
was no prize to win even with perfect foreknowledge of the day's size, so the failure is not in the
forecast. The mechanism agrees with the two records either side of it (FINDINGS §70, §71, §72):
**by 09:30 the information is spent, and a night that moved a lot has spent more of it.**

**Stage 2, root selection, was never run** — the design made it conditional on stage 1.

### The premise is KEPT, as an instrument of the survival layer

**The principal's decision, the same day: a general activity filter is worth having even where it is
not used.** It now exists as a standing, reusable module, [`scripts/activity_filter.py`](../scripts/activity_filter.py)
(`--selftest` passes six checks), root-agnostic and causal by construction, with D506's measured
properties and both indications in its docstring.

**Its one indication.** Trading only the in-play decile cuts **P3a** — R11's breaches-per-year of the
2%-of-account daily limit — by **three to five fold**, because both prop death mechanisms are counted
in **exposure-days** and a filter that removes 90% of the sessions removes 90% of the chances to die,
even though each session it keeps is individually more dangerous:

| | P3a, all sessions | P3a, the in-play decile |
|---|---:|---:|
| ZB | **14.00 a year** | **2.71** |
| ZN | 2.00 | 0.71 |
| NQ, the long day drift | 0.57 | 0.00 |

**Reach for it when a construction fails P3a and nothing else. That is the whole indication**, and it
is a sizing decision rather than a signal one. **The arm admitted to this page today does not need
it** — the MACD day-session arm reads P3a **0.50 a year** against a bar of 1.0, and P3b 10.0% against
33%. The filter is kept for the constructions that come next, and for the day a live arm's breach
rate drifts.

**What it must never be used for:** choosing direction, or choosing which sessions carry the edge.
That is what D506 closed.

---

## THE CONDITIONER LINE ON THE ADMITTED ARM CLOSED BY THE PRINCIPAL, 2026-09-13

**Closed by the principal, in writing, after D508, D509 and D512:** conditioning the admitted MACD
day-session arm on a daily-clock state, as a way of ranking which of its sessions to take. Three
conditioners were declared and scored against the same arm, imported and reproduced exactly
(1,876 sessions, $15,423, matching D504's published per-year figures):

| conditioner | record | primary | where it sat in its own exact rotation | family |
|---|---|---:|---|---|
| \|log(P/SMA200)\|, rank statistic | D508 | Spearman +0.0089 | 43rd percentile | beaten by 58% of offsets |
| the same, economic statistic | D509 | Δ +$13.82 a session | 76.9th percentile | beaten by 40% |
| log(EMA50(range)/SMA200(range)) | D512 | Δ +$25.37 a session | 93.4th percentile | **beaten by 6.0%** |

**None clears.** The refusals tighten across the three, and the last is narrow, but a refusal at 6%
is a refusal.

**What the line established, and it is worth more than the verdict.**

1. **The arm has no unread slice on NQ** (D503), so no conditioner found on it could ever have been
   confirmed. Every one of these records states that in its §0. **A conditioner for this arm is
   structurally unavailable, whatever it measures.**
2. **The 200-day stretch ranks YEARS, not sessions.** Within a year it reverses sign: −$10.71 a
   session against a pooled +$13.82, negative in seven years of eight. Any conditioner correlated
   with "which year it is" inherits this arm's concentration in 2020 and 2022.
3. **Range expansion does NOT reverse** — within-year mean +$27.42 against a pooled +$25.37,
   positive in six years of eight. It is the only conditioner tested here that survives
   stratification, and its bottom quintile loses **gross** (−$5.27 a trade, net Sharpe −1.08). The
   arm bleeds in a compressed-range regime before costs, not through them.
4. **The apparent superiority of the 23-hour window was nine sessions** (D512's addendum). The day,
   night and 23-hour versions correlate at +0.99 and are one conditioner measured three ways.
5. **A rotation of a quintile-difference statistic subsumes a matched-persistence gate**, proven in
   D509's runner rather than asserted. Prefer a statistic whose own null contains its control.

**Closed for this arm:** any daily-clock conditioner as a ranker of its sessions. **Carried forward
on the principal's word:** the range-expansion conditioner itself, declared in advance on a root
whose 2024+ is unread, so that a confirmation exists. That is D513.

**Nothing was spent by any of the three.** 2024+ was never scored on NQ.
