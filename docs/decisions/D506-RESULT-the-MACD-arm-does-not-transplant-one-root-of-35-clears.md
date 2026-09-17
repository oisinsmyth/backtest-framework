# D506 — RESULT: the MACD arm **does not transplant**. One root of 35 clears its own null, it is the one we already had, and it fails the family bar.

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D506-RESULT-the-MACD-arm-does-not-transplant-one-root-of-35-clears-its-own-null-and-it-is-the-one-we-already-had.md`. The H1 above is the full title.*

> ## ⚠ AMENDED THE SAME DAY — §9 SUPERSEDES §1–§8
>
> **The numbers in §1–§8 were computed on a NaN-poisoned signal series and the family bar was
> read on a statistic that is not comparable across roots.** Both are fixed in **§9**, which is
> the record of this study. §1–§8 stand as written because the errors are the finding.
>
> **What changed:** two roots clear their own null (not one), the family bar **CLEARS** (not
> fails), and the decorrelated pair the book needs **exists** — ρ(HG, NQ) = +0.109.

**2026-09-13.** Runner [`scripts/d506_macd_breadth.py`](../../scripts/d506_macd_breadth.py) ·
artifact [`data/d506_macd_breadth.json`](../../data/d506_macd_breadth.json) ·
pre-registration [D506 PRE-REG](D506-PRE-REG-the-frozen-MACD-arm-across-all-36-roots-gross-first-as.md) ·
fixture [`fut_breadth_hourly`](../../data/fixtures/fut_breadth_hourly.meta.json).

**Nothing admitted** ([R15](../RULES.md#r15)). In-sample 2016-01-04 → 2023-12-29. 2024+ stays
unread on all 35 roots except NQ, and 2010–2015 stays unread.

---

## 1. The headline

| | |
|---|---|
| roots scored at the frozen spec | **28** (7 structurally inapplicable, 1 skipped) |
| **positive gross mean per trade** | **15 of 28** |
| **clearing their OWN rotation p95** | **1 — NQ** |
| **family-max** | best **+19.937** (NQ) against a family null p95 of **+20.101** → **DOES NOT CLEAR** |
| pairs of clearing roots to correlate | **none — only one root cleared** |

**The signal is positive in a majority of markets and distinguishable from noise in none of them
except the one root this programme already trades — and even there it does not survive the price
of having searched 35.**

## 2. The frozen spec, every root, gross first

| root | sess | trades | **gross tk/trade** | gross Sharpe | net tk | net Sharpe | $/trade |
|---|---:|---:|---:|---:|---:|---:|---:|
| **NQ** | 1,922 | 1,604 | **+19.937** | **+0.781** | +12.937 | +0.506 | +9.97 |
| **NG** | 1,782 | 1,458 | **+2.990** | +0.506 | +1.690 | +0.286 | +29.90 |
| **ES** | 1,929 | 1,617 | **+1.988** | +0.299 | −1.412 | −0.212 | +2.49 |
| **PL** | 1,909 | 1,532 | **+1.975** | +0.356 | +0.375 | +0.067 | +9.88 |
| **HG** | 1,901 | 1,502 | **+1.411** | +0.468 | +0.171 | +0.057 | +17.64 |
| GC | 1,904 | 1,495 | +0.795 | +0.146 | −3.205 | −0.585 | +0.79 |
| BTC | 1,387 | 1,108 | +0.770 | +0.101 | −6.230 | −0.816 | +0.38 |
| BZ | 1,732 | 1,402 | +0.613 | +0.090 | −0.687 | −0.101 | +6.13 |
| 6A | 1,949 | 1,571 | +0.531 | +0.164 | −1.069 | −0.329 | +2.65 |
| TN, ZN, ZF, UB, ZT, SI | — | — | +0.06 … +0.42 | +0.02 … +0.37 | negative | negative | — |
| **HO** | 1,753 | 1,461 | **−7.765** | −0.354 | −9.479 | −0.432 | −32.61 |
| RB, RTY, YM | — | — | −5.0 … −6.1 | −0.31 … −0.51 | negative | negative | — |
| 6E, 6S, CL, NKD, PA, 6B, 6C, 6J, ZB | — | — | −1.04 … 0.00 | negative | negative | negative | — |

**Only NG and HG are net-positive, and both fail C-d** — NG's daily σ is $1,011 and HG's $942
against a $500 cap, at full contract size with no micro. **The two roots where the fee is a small
share of a large tick are the two the account cannot hold.** That is D493's constraint arriving
from a third direction.

## 3. The null, which is the actual result

| root | observed | null p50 | null p95 | margin | clears |
|---|---:|---:|---:|---:|---|
| **NQ** | **+19.937** | +0.001 | +18.423 | **+2.2 SE** | **YES** |
| HG | +1.411 | −0.122 | +1.621 | −4.0 SE | no |
| NG | +2.990 | +0.072 | +3.388 | −6.8 SE | no |
| ZN | +0.387 | −0.025 | +0.524 | −10.0 SE | no |
| PL | +1.975 | −0.041 | +3.178 | −11.9 SE | no |
| ES | +1.988 | −0.052 | +4.010 | −14.7 SE | no |
| …all others | | | | −20 to −77 SE | no |

**FAMILY-MAX: +19.937 against +20.101. NQ clears its own null and the family does not clear
its.** The family-max null is what prices having looked at 35 roots, and NQ's margin over its
own p95 (2.2 SE) is almost exactly the width of that price.

**This is the third family in a row to fail its own family bar** — D468's 24 session windows, D499's
16 hourly cells, and now D506's 35 roots. The pattern is consistent and it is not about these
particular constructions: **a best-of-N search on ~2,000 sessions has a null p95 near the level
anything real in this programme has produced.**

## 4. Seven roots cannot run the spec at all, and that is a finding

**HE, LE, ZC, ZL, ZM, ZS, ZW — all the grains and livestock — are structurally inapplicable at
M = 5.** Their sessions end ~14:20 ET, giving an h09–h14 window. An exit decided at *t* executes
at *t+1 ≤ last*, so `M ≤ last − 1 − first` = **4**. With M = 5 no signal exit can ever execute.

**On the first run this appeared as seven roots with zero trades and NaN everywhere**, which is how
it was caught. It is not a failure of those markets and **not a result about them**: substituting
M = 4 would be a *different construction*, and doing so after seeing that M = 5 does not fit would
be fitting. **The frozen arm is not transplantable to a 6-hour session**, and that halves the
grain and livestock breadth this fixture was built to reach.

**SR3 was skipped** for under 250 qualifying sessions — its volume front hops so often (1,273 rolls
in 2,511 sessions) that the 78-bar contract-purity requirement is almost never met. Also not a
statement about SOFR, a statement about this construction's purity rule meeting a market that
rolls constantly.

## 5. Predictions

| | prediction | outcome | |
|---|---|---|---|
| **W-a** | ≥ 8 of 36 positive on gross | **HELD** | 15 of 28 scored |
| **W-b** | < 6 clear their own p95 | **HELD** | 1 |
| **W-c** | the family maximum does **not** clear | **HELD** | +19.937 vs +20.101 |
| **W-d** | NQ reproduces D495 within 10% | **BROKEN** | see §6 — and my runner checked the wrong statistic |
| **W-e** | grains/livestock not systematically better | **UNTESTABLE** | structurally inapplicable (§4) |
| **W-f** | ≥ 1 clearing pair with ρ < 0.3 | **BROKEN, vacuously** | one root cleared, so no pair exists |

## 6. Two failures of my own, and W-d is the one that matters

**The runner did not compute the statistic the pre-registration declared.** §7.1 of the pre-reg
said NQ must reproduce D495 *"to within 10% on gross mean per trade"* and must **raise** otherwise.
The runner compared **net Sharpe** (because that is what D495's artifact exposes) against an
**absolute 0.25** threshold. The observed gap — **+0.506 here against D495's +0.723** — is 30% and
breaks the prediction, but sits inside the coded threshold, **so the gate did not fire on a
prediction it was written to enforce.** That is exactly the failure mode
[`runner-must-compute-the-preregistered-statistic`] exists to prevent, and I repeated it.

**The disagreement itself is unexplained and must not be waved away.** Candidate causes, none
verified: this fixture keeps **1,922 sessions against D495's 1,873** (+2.6%, from a different
presence rule); crossing is assumed at 1.000 tick here against D495's measured 1.009; and the
front-month selection may differ at the margins. **Until it is explained, every cross-fixture
comparison in this record carries that 0.2-Sharpe uncertainty**, and the two fixtures disagree
about a root they should agree on.

**Two unit bugs in the first run**, both caught and both now asserted against:

1. `simulate` hardcodes `LAST_SEG = 21`, so the per-root window never reached the state machine —
   producing §4's seven all-NaN roots. `simulate_window` takes the last segment as a parameter and
   is **asserted bit-identical to D491's `simulate` at `last_seg = 21`**, with a shorter window
   proven to differ.
2. A cost in **ticks** was charged against prices in **price units** and converted afterwards,
   inflating it by 1/tick — **6J was billed 2,960,001 ticks a trade.** Everything now runs in
   ticks, and the self-test reproduces that exact figure as a `[X]` break.

**Gross was unaffected by bug 2**, which is the only reason the first run's gross column was
readable at all — and an accidental argument for the pre-registration's decision to lead on gross.

## 7. What this changes

- **The MACD arm does not transplant.** It is an NQ construction. 15 of 28 roots carry a positive
  gross edge and not one is separable from its own rotation null.
- **The breadth route to components 2–5 is not closed, but this construction's version of it is.**
  What was tested is *one frozen signal* on 35 underlyings. [W-f](#5-predictions) — the question
  the book actually needs — could not even be asked, because a second clearing root never appeared.
- **The two net-positive roots are both C-d failures** (NG, HG), which says the fee/σ trade-off
  runs the wrong way for the account: where the fee is small relative to the tick, the contract is
  too big for the floor.
- **Nothing is admitted.** NQ clearing its own null in-sample on a search of 35 is not a component;
  it is the arm already in the book, re-measured on a new fixture, and disagreeing with its own
  earlier measurement by 0.2 Sharpe.
- **Still unspent:** 2024+ on 34 roots, and 2010–2015 on every non-index root.

## 8. Checks

20 checks, all passing. The load-bearing ones: `simulate_window` proven bit-identical to D491's
machine at `last_seg = 21` and proven to differ at 20; `max_hold_available` proven to explain the
seven zero-trade roots; the tick/price unit confusion reproduced as a break at −2,960,001 ticks a
trade; `net = gross − cost × trips` asserted exactly with an identical trip count; the rotation
proven to preserve the signal's lag-1 autocorrelation (+0.810) where a shuffle destroys it
(−0.009); and the in-sample boundary proven to exclude both 2015 and 2024.

---

# 9. AMENDMENT, same day — two corrections, and the result changes sign

The principal asked me to explain the 1,922-vs-1,873 session disagreement of §6. Explaining it
found a defect that invalidated §1–§8, and fixing it exposed a second one in my own family
statistic. **This section is the record of D506.**

## 9a. The session gap, fully decomposed — and both figures reproduce exactly

| path | rows | kept |
|---|---:|---:|
| D467 fixture + `same_front` | 2,037 | **1,873** ← D495's published count, reproduced |
| D467 fixture, no `same_front` | 2,062 | 1,898 |
| breadth fixture + `same_front` | 2,453 | 1,890 |
| breadth fixture, no `same_front` | 2,485 | **1,922** ← §1's count, reproduced |

**+32 from not filtering `same_front`, +17 from the fixture's different row set** interacting with
the 78-bar contract-purity window. **The two fixtures agree on the underlying data exactly** —
2,062 sessions with ≥ 200 bars in h09..h15 and 1,997 with all seven closes finite, identical in
both files. **So this was never a fixture defect. It was my pipeline.**

## 9b. The real defect: keeping absent rows poisons a recursive indicator

`series_for` applies **two** filters before flattening the panel into one hourly series —
`same_front` and (by construction, since D467's builder drops them) presence. **My runner applied
neither**, and the consequence was not a 2.5% count difference:

| | sessions | **trades** | gross Sharpe | net Sharpe |
|---|---:|---:|---:|---:|
| breadth, absent rows **left in** | 1,890 | **1,573** | +0.855 | +0.579 |
| breadth, absent rows **dropped** | **1,873** | 1,957 | +1.130 | **+0.811** |
| D495 published | **1,873** | 1,904 | +1.038 | +0.723 |

**The breadth fixture keeps non-present rows and flags them; D467's builder drops them from the
file.** Those rows are mostly NaN, and **NaN propagates through the MACD's recursive EMA / ZLEMA /
SMMA filters**, so every gap suppresses the indicator downstream of itself — **1,573 trades instead
of 1,957, a 20% loss of signal with no market content whatever.**

**This is a property of the fixture I built and it will bite anything that reads it.** A flagged
row is not a dropped row, and for a recursive indicator that distinction is the whole ballgame.
Recorded in the runner's docstring and in the fixture's memory note.

The session count now reconciles **exactly** (1,873 = 1,873). A **0.088 residual** in net Sharpe
remains (+0.811 against +0.723) with identical session counts but 1,957 trades against 1,904 —
**two builders producing slightly different hourly bars for the same sessions, cause not
established.** W-d's relative gap is **12.2%** against the pre-registration's 10% bar: still
broken, and now narrowly.

## 9c. My family statistic was ill-posed

§3 read the family-max on **gross ticks per trade**. **That is not comparable across roots**: NQ's
+24.9 ticks and ZN's +0.37 sit on tick sizes three orders of magnitude apart, so a family
*maximum* in ticks is decided by whichever root has the smallest tick and says nothing about the
others. Both readings are now reported and only the second is used:

| family bar | best | family null p95 | verdict |
|---|---:|---:|---|
| gross ticks/trade — **ill posed** | +24.923 (NQ) | +17.088 | clears, *by units* |
| **gross Sharpe — scale-free** | **+1.130** (NQ) | **+1.083** | **CLEARS** |

## 9d. The corrected result

| root | gross tk/trade | gross Sharpe | own null p95 | margin | net Sharpe |
|---|---:|---:|---:|---:|---:|
| **NQ** | **+24.923** | **+1.130** | +15.285 | **+23.5 SE** | **+0.811** |
| **HG** | **+1.534** | **+0.604** | +1.431 | **+2.9 SE** | +0.115 |
| ES | +3.335 | +0.582 | +3.792 | −3.2 SE | −0.011 |
| NG | +3.041 | +0.576 | +3.825 | −8.3 SE | +0.329 |
| GC | +1.839 | +0.390 | +3.036 | −14.6 SE | −0.456 |
| …23 others | −14.2 … +1.8 | | | −10 to −110 SE | |

    positive gross:          15 of 28
    clear their OWN p95:      2 -- NQ and HG
    FAMILY-MAX (Sharpe):      CLEARS, +1.130 against +1.083
    rho(HG, NQ):              +0.109   <-- below C-b's 0.3

**W-c is BROKEN — the family clears.** **W-f is HELD — the decorrelated pair exists.** Those were
my two most important predictions and they both went the other way from §5.

## 9e. What it actually means, stated carefully

**The family clearing is not independent evidence.** It clears by **0.047 on the Sharpe scale**,
and the cell doing it is **NQ — the incumbent**, already in the book before this search began. A
search that contains its own answer clearing a best-of-N bar is the incumbent dominating the
field, not a discovery.

**HG is the genuinely new information**, and it is thin:

- **+2.9 SE over its own rotation null** on gross ticks per trade — a real, if narrow, separation.
- **ρ = +0.109 with NQ** — genuinely decorrelated, which is the property the book has been unable
  to find. Copper and the Nasdaq share no mechanism, which is the point.
- **And it is not a component.** Net Sharpe **+0.115** fails C-a's 0.5 by fourfold, and daily σ
  **$942** fails C-d's $500 at full contract size with no micro
  ([breadth fixture](../../data/fixtures/fut_breadth_hourly.meta.json)).

**So the corrected reading of D506 is: the search found one decorrelated root with a separable
gross edge that the account cannot hold.** That is a better outcome than §1–§8 reported and a
worse one than the headline "the family clears" suggests. **Nothing is admitted** ([R15](../RULES.md#r15)).

**What would change it:** HG's crossing cost is unmeasured (`bbo-1m` covers it and is not
decoded), and a micro copper contract exists at CME but was not acquired and has no committed
tick value here. Either could move HG's net; neither is in this record.
