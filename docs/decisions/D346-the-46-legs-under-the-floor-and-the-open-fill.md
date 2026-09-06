# D346 — the 46 legs under the floor and the open fill: does any long leg survive honest scoring?

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). Nothing here is a
result.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

D335 gave every one of the 46 dimensionless signals a long-leg and a short-leg per-trade
number under the deal filter and the published spread. Six long legs were positive; one
short leg was. That table predates the universe floor (D339, D343) and the next-open fill
(D340), which between them took the best long leg from +46 to −23 a trade and turned
`rsi`'s from +64 to −11. Only four signals have been re-measured under the current
conventions and every long leg among them is negative uncapped. The principal's
question — is any long leg here anything at all, honestly scored — has not been asked of
the other 42, and the conditional-profile study planned next assumes a long signal worth
profiling. This record asks it first.

## 1. Cells

Every one of the 46 dimensionless D290 signals as a **symmetric book at depth 2**, D303
target, F0 deal windows removed, **`keep_v2`** (replace), **open fill**, at **k=20** (D335's
hold, for the comparison) and **k=40** (the current operating point). Both lenses: the
variant book (slot-capped, bp/bar, D322's costing) and the invariant ledger (every
candidate trade, per leg, per trade). PUB primary, PB beside. Per leg: trades, gross,
net, t, held half-spread, held as-traded price. Multiplicity is 46 per leg and is
reported as rank with the p50 and p95 of the 46, as D335 did. No nulls per leg; the
counts are the finding.

**Identities:** `rsi` and `retrace_leg` at k=20 reproduce D343's `RSI/v2` and `RL/v2`
cells to 1e-9 on both lenses; `rsi` at k=40 reproduces D344's.

## 2. Predictions

Q1 is load-bearing. Q3 and Q6 are against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* **fewer than 3 of 46** long legs net > 0 per trade under PUB at k=20. |
| **Q2** | none of the three event candidates' long legs — `rsi`, `retrace_leg`, `rev_5` — is positive per trade at k=20. |
| **Q3** | *(against)* at k=40 the count of positive long legs is **also below 3**: the longer hold does not rescue the invariant lens (D344 found k=40 worse per trade). |
| **Q4** | fewer than 3 of 46 short legs net > 0 per trade at k=20 (D335: one). |
| **Q5** | **fewer than 23** long legs improve per trade against D335's table — the two corrections hurt the majority of long legs. |
| **Q6** | *(against)* `rsi` symmetric is the **best variant book** of the 46 at k=20 under PUB net bp/bar, and **fewer than 5** of the 46 variant books are positive. |
| **Q7** | the median long-leg held as-traded price is above **$20** (the floor moved the books off the cheap tail; D335's top legs were at $6–$28). |
| *check* | the three identity cells reproduce to 1e-9. |

## 3. Stop conditions

- **Q1 holds** → no long leg on this fixture pays its own cost uncapped under honest
  scoring. The conditional-profile study starts from that fact, and its question becomes
  whether an *entry condition* can turn a negative uncapped leg positive — which is a
  sharper question than "which long signal is best".
- **Q1 fails** → the surviving long legs are named, their top trades printed with
  as-traded price and dollar-volume percentile (FINDINGS §18, §20), and they become the
  candidates for the profile study ahead of the three named ones.
- **Q6 fails** on the first clause → a symmetric book beats `rsi`'s under every convention
  and has never had a record; it gets one before anything is built on `rsi`.
- Nothing is promoted.

## 4. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | cache key; F0 counts; raw factor == census; `keep_v2` share == D343 |
| **[1]** | `rsi` and `retrace_leg` k=20 reproduce D343; `rsi` k=40 reproduces D344 — variant net and Sharpe, invariant per trade, both conventions, to 1e-9 |
| **[P]** | the pool is exactly D335's 46 (the five dimensional scores excluded) |
| **[C]** | per-leg `2c` is 2 × that leg's held median half-spread on every costable leg |
| **[S]** | on the `rsi` k=20 invariant ledger, every trade equals the open-fill recomputation to 1e-12 |
| **[L]** | every symmetric book's invariant ledger has both legs; a leg with a zero held half-spread under PB is recorded as degenerate, as D335 did |
| **[6]** | [1] raises on a leg handed free money |

## 5. Files

`docs/decisions/D346-the-46-legs-under-the-floor-and-the-open-fill.md` (this record) ·
`scripts/run_d346_legs_floor_open.py`, `data/d346_legs_floor_open.json` (to follow). Prior
evidence: `data/d335_legs_under_filter.json`.
