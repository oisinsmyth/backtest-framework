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
