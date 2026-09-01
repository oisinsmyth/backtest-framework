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
