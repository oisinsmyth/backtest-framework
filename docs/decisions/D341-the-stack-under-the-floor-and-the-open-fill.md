# D341 — the stack under the floor and the open fill together: the re-costing D318 re-opened

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). Nothing here is a
result. The prediction that matters was written into STACK §6 before this record: **the
best book in the programme, honestly scored, is at or below zero.**
**Date:** 2026-09-05
**Area:** Cost model · universe · strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

Two conventions were measured on the same afternoon and never together. D339 put a
universe floor under the fixture — as-traded close ≥ $5 at t−1 and the dv28 pass, the
name replaced — and `retrace_leg` went from +18.93 to +3.14 PUB bp/bar. D340 filled
positions at the next open instead of the signal's own close and the same cell went to
+5.14. Each is a correction to a convention every D300-family number was scored under.
**Neither has been applied with the other**, so no number in the programme is yet
honest on both counts, and the two overlap: the overnight gap the fill credited was
largest in exactly the illiquid names the floor removes. The corner where both apply
is the number the programme has been trying to quote since D300.

## 1. Cells

Four signals × a 2 × 2 of conventions, both lenses, PB and PUB (PUB primary), GC+HTB
borrow as new keys:

| signal | k | filter | conventions |
|---|--:|---|---|
| `retrace_leg` symmetric (RL) | 20 | F0 | {none, floor} × {close, open} |
| incumbent C0 (N=2/target) | 5 | — | {none, floor} × {close, open} |
| `rsi` symmetric | 20 | F0 | {none, floor} × {close, open} |
| `hist_L` symmetric | 20 | F0 | {none, floor} × {close, open} |

Three of the four corners of every square already exist — none/close (D338, D333,
D339), floor/close (D339), none/open (D340 for RL and C0) — and are **reproduced to
1e-9 as identities**, not re-reported as findings. **The new corner is floor/open.** The
floor is D339's replace semantics (the universe definition); the fill is D340's flag
with `ocT`/`mkt_oc` built by the runner.

**Reported on RL floor/open:** the four groups via D322's functions, the top-five table
with as-traded price and entry-day dollar-volume percentile, the implementation-lag
premium per leg on the floored gate, a 200-draw rank-rotation null with teeth on gross
and the matched-cost net null beside it. **The null's resolution is stated**: the
number of distinct shifts drawn (at most 24) and p as "above k of 24", per D340 §5.

**Also reported, for every square:** the two marginal effects and the interaction,
`(floor/open) − [(none/close) + Δfloor + Δfill]`, in PUB bp/bar. If the gap the fill
credited lived in the names the floor removes, the interaction is positive: removing
the names removes the gap, and the fill then has less to take away.

## 2. Predictions

| | prediction |
|---|---|
| **Q1** | *(load-bearing, committed in STACK §6 before this record)* RL floor/open **PUB net ≤ 0**. |
| **Q2** | the implementation-lag premium on RL's floored long leg is **less than half** the unfloored one — below +22.4 bp per entry against D340's +44.8. The gap was the illiquid names'. |
| **Q3** | *(structural)* the interaction on RL is **positive by more than 5 bp/bar**: floor/open is above −10.6 (= 18.93 − 15.79 − 13.78) by at least 5. |
| **Q4** | the incumbent's effects are **additive within 2 bp/bar**: C0 floor/open within ±2 of −16.2 (= −12.68 − 0.34 − 3.21). Its gap was not concentrated in the floor's names. |
| **Q5** | *(against)* `rsi` floor/open **stays above zero** PUB (from +4.05 under floor/close). |
| **Q6** | `hist_L` floor/open **below −10** PUB. |
| **Q7** | RL floor/open **gross above its gross null's p95**, p95 > 0 — the ordering survives both conventions even if the net does not. |
| **Q8** | RL floor/open's top trade is **< 7%** of the ledger, at-traded price ≥ $5, dollar-volume percentile > 28. |
| *check* | the three known corners of each square reproduce D338 / D333 / D339 / D340 to 1e-9; the RL none/open corner's ledger equals D340's. |

## 3. Stop conditions

- **Q1 holds** → `retrace_leg` is **retired as a book on this fixture**. D339 §7's
  out-of-sample design is withdrawn; STACK §0's "best book" becomes "none"; what
  survives, if Q7 holds, is a gross ordering with no net, recorded as such.
- **Q1 fails** (net > 0 under both conventions) → it is the first cell that survives
  every convention this programme owns. D339 §7's out-of-sample design becomes live —
  still not run; the read is the principal's — and the four-group report here is the
  candidate record.
- **Q7 fails** → the ordering itself was the gap plus the tail; D338's "the signal is
  real" and D339's "the ordering survives the floor" are both withdrawn in writing.
- **Q5 holds** (`rsi` > 0 under both) → `rsi` under the floor gets its own candidate
  record next, four groups and top trade first. It was first per trade in D335 and its
  unfloored book was negative; a floored, honestly filled `rsi` above zero would be the
  first book to *gain* from honest scoring.
- **Q3 fails** (interaction ≤ +5) → the fill's gap was not the floor's names; the two
  costs are independent and both stand in full against every future book.

## 4. Assertions — properties of code

| | |
|---|---|
| **[1]** | none/close corners reproduce D338 (RL), D333 (C0), D339 (RSI0, HL0); floor/close corners reproduce D339's RL-r, C0-r, RSI-r, HL-r; none/open corners reproduce D340's RL and C0 — all to 1e-9 on variant net and Sharpe under both conventions and invariant per trade |
| **[K]** | cache key with `ragged_panel.py`; npz newer than the builder |
| **[R]** | the raw factor equals D339's module output on the full grid; the floor share equals the census's 29.2962% to 1e-9 |
| **[E]** | the gate is fill-invariant: for every cell the floor/close and floor/open runs read the same `gateF/gateR/gateO` bitwise, and their entry sets first differ no earlier than their exit sets (D340 [E2]) |
| **[A]** | lag audit on RL floor/open's long gate: rebuilt from the floored score at t−1 by a direct stable argsort, equals the gate on 200 sampled bars; the unlagged rebuild differs on most |
| **[S]** | sign in money: every RL floor/open trade equals `pnl_recomputed_fill` — `ocT`/`mkt_oc` on the entry bar, `r1T`/`mkt` after — to 1e-12; a favourable excess path pays positively on every long and short |
| **[RQ]** | summed vs compound accumulation: same entries and exits, different P&L; group 1 scores the summed ledger |
| **[2]** | reconciliation with `contributions_fill`; gross reconstructs to < 1 bp up to the open tail; rejects a ledger missing a trade |
| **[3]** | symmetric trim; rejects an asymmetric one |
| **[N]** | rotating the rank array moves the book; the number of distinct shifts in 200 draws is reported and p is stated as "above k of that many" |
| **[B]** | borrow reconciles to 1e-9; `net_bp` untouched |
| **[F]** | fallback cells counted (D340 found zero) |
| **[6]** | [1] raises on a book handed +5 bp on 200 masked bars |

## 5. Scope

**In:** the sixteen cells, both lenses and conventions, borrow, the interaction
decomposition, the four groups and the null on RL floor/open. **Out:** any new
parameter; starve semantics (D339 settled replace); the holdout; the out-of-sample read.

## 6. Speed

32 simulations at ~1 s plus 200 null draws at ~0.1 s under the open fill; loading and
the grid build dominate. About three minutes. Background.

## 7. Files

`docs/decisions/D341-the-stack-under-the-floor-and-the-open-fill.md` (this record) ·
`scripts/run_d341_floor_and_open_fill.py`, `data/d341_floor_and_open_fill.json` (to
follow). Reuses `scripts/d339_universe_floor.py`, `scripts/d340_fill.py`, and the
helpers of `run_d338`, `run_d339`, `run_d340`.
