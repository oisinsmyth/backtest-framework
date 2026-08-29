# D258 — The prop track: candidates, and what reopened them

**Status:** Design record — no study registered, no cell scored
**Date:** 2026-08-29
**Area:** Strategy research

---

## Why this record exists

[R11](../RULES.md) established hurdle P and the fact that **the committed book fails P2
structurally** — it holds overnight, and 86.6% of its return is timing that accrues overnight. **No
amount of position sizing fixes that.** So the prop route needs a different strategy, and this
record fixes the candidate list and the reasoning **before** any of them is screened, so that
picking a winner later cannot be dressed up as having predicted it.

**Two goals are now tracked separately** and must not be allowed to distort each other:

| track | target | current state |
|---|---|---|
| **own capital** | ~+18%/yr with the drawdown roughly halved from −29.82% | book at 3.28x delivers the return; the drawdown is the open problem |
| **prop** | hurdle P, all six | **no candidate exists** |

---

## The fact that reopened the field

**This programme's cost wall is an EQUITY number and does not transfer.**

| | round trip | one per day |
|---|---:|---:|
| liquid ETFs | ~3.8 bp | **−8.90%/yr** |
| single names | ~10 bp | — |
| **ES futures** | **~$4–5 on ~$250k notional ≈ 0.2 bp** | **~−0.5%/yr** |

**Roughly twenty times cheaper.** That arithmetic is what excluded scalping (31–187%/yr),
[D247](D247-the-short-side-at-fifteen-minutes.md)'s intraday shorts (breakeven 0.13 bp against 1.6
charged) and most of the intraday microstructure literature
([`03-intraday-microstructure.md`](../research/shorts/03-intraday-microstructure.md), where the
three best-documented effects deliver 2.65–3.78 bp/trade against a 3.70 bp cost).

**At 0.2 bp those same effects clear their costs by an order of magnitude.** Every construction
this programme excluded on cost arithmetic must be **re-costed before it stays excluded**. That is
recorded in R11 as a standing corollary.

---

## What hurdle P demands of the return distribution

**P1 — a 4% trailing drawdown measured on OPEN equity — is the binding constraint**, and it dictates
shape rather than magnitude:

- **Positive skew is fatal.** Frequent small losses ratchet against the floor while you wait for the
  rare large win. This is exactly the profile of a short book (see [FINDINGS §1](../FINDINGS.md)).
- **Negative skew is fatal.** One large loss breaches immediately.
- **What survives is a high hit rate with low variance and tight tails** — many small wins, hard
  stops, and no position allowed to run against you even if it would have recovered.

**Both existing arms are "wait for the move" constructions and neither has this shape.**

---

## The candidates, in the order they will be examined

### C1 — the session-boundary trade

**The claim:** CME Globex runs roughly 18:00 → 17:00 ET with a one-hour maintenance break, and the
firms flatten at 16:59–17:10 ET, **at that break**. A position opened after the break and closed
before the next one therefore **never crosses a flatten point** — it is "intraday" by the venue's
own definition while spanning the entire overnight session.

**If that reading holds, the +8.59%/yr overnight drift becomes reachable inside prop rules**, which
is precisely what P2 appeared to forbid.

**This is a question about firm terms and exchange hours, not about data**, so it is checked first
and costs nothing. **It is also the candidate most likely to be wrong**, because a rule that
convenient usually has a clause attached.

**Known blocker if it survives:** we hold no futures data, and RTH-only equity bars cannot
represent a 23-hour session. C1 could not be backtested on the current fixtures even if the reading
is correct.

### C2 — intraday mean reversion with hard stops

**Shape fits P1 directly** — high hit rate, small wins, defined loss. And reversion is the single
most reproduced effect in this programme's own measurements: **+16.83%** (most beaten-down
quintile), **+18.31%** (wedge down-break), **+37.42%** (downtrend onset), **+89.74%** (forward
return after a −20% five-bar move).

**Excluded previously on ETF cost arithmetic at 5–20 round trips/day. At futures cost, 3–5 round
trips/day is affordable.** The objection was arithmetic and the arithmetic has changed.

### C3 — opening-range constructions

One trade per day, defined risk, flat by the close — **natively P2- and P3-compliant**, and the cost
is trivial at any futures commission. **Heavily mined, so the prior is poor**, but the structure is
right and it is cheap to screen.

### C4 — the sizing wrapper (a precondition, not a candidate)

Size so the 99th-percentile daily loss sits inside P3's 2%. **Not a strategy.** Any candidate needs
this bolted on before P1 is even measurable, and it should be built once and reused.

---

## What this record does NOT do

**No candidate is registered, no hurdle is claimed cleared, and no data has been looked at.** The
ledger does not move. **When one of these is screened it gets its own pre-registration** with cells
counted, and this record is what establishes that the candidate was named in advance rather than
chosen after a promising number.

## The data gap, stated plainly

**We hold no futures data.** ES ≈ SPY and NQ ≈ QQQ make the 15-minute ETF fixture a usable proxy for
C2 and C3 during regular hours, with costs re-parameterised. **C1 cannot be tested on anything we
own**, and acquiring 23-hour futures bars would be its own fetch with its own provider question.
