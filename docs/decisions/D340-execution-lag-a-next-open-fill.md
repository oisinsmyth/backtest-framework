# D340 — execution lag: a next-open fill for the D300 family

**Status:** PRE-REGISTERED. Committed **before the simulator flag, the helper module and
the runner exist** (R8). Nothing here is a result.
**Date:** 2026-09-05
**Area:** Simulator convention · cost model · every book since D300

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

Every D300-family book computes its signal from the close of bar t−1, ranks on it, and
opens the position at bar t **earning `r1T[t] = close[t]/close[t−1] − 1`** — the return
from the very close the signal was computed at (`run_d306_width_exits.simulate`, mark
loop at lines 191–198; `rank_columns`, "THE LAG IS HERE AND NOWHERE ELSE", lags the
score one bar). The fill is at the signal's own close. No book can do that: the signal
needs the close to exist, and the earliest honest fill is the next open. **The
overnight gap between close[t−1] and open[t] is credited to a position that could not
have been filled before it.**

D338 showed where this matters. Three of `retrace_leg`'s five largest trades are
one-bar holds; its top trade, VSA on 2025-01-31, is credited +329.8% from a 90.55 close
to a 389.20 close, of which the open was 195.05 — the open-to-close move was +99.5% and
the rest was the gap. The convention is the whole family's, so the question is not
about one book: **how much of every net number since D300 is the overnight gap?**

## 1. The change, declared

`simulate(..., *, accumulate="sum", fill="close")`. Under `fill="open"`:

- On a position's **entry bar** t, the marked return is **`ocT[t, row] = close[t] /
  open[t] − 1`**, price only — a buyer at the open of an ex-dividend bar receives no
  dividend and a short opened there owes none — against **`mkt_oc[t]`**, the
  equal-weight open-to-close market over live names with a real open (≥ 20 names,
  mirroring `market_reference`). The hedge is established when the position is.
- Every later bar uses `r1T` and `mkt` exactly as today.
- The exit rule, the target, the slots, the gate, the `runs`/`legacy`/`shift` paths and
  the five-tuple ledger are untouched. The default `fill="close"` binds the same
  operands to the same two operations and is **bit-identical** to today.
- `A` gains two arrays built by the runner from `build_grids` — `ocT` (T, n) and
  `mkt_oc` (T,) — via `d340_fill.with_open_fill(A, panel, g)`; the D303 cache and its
  key are untouched. `fill="open"` without them raises `KeyError`; a bad value or a
  shape mismatch raises `ValueError`.
- **Fallback:** where a priced name has no usable open (NaN or ≤ 0) on its entry bar,
  `ocT = r1T` there — a fill at the prior close, counted per cell and per entry. The
  alternative, skipping the entry, would change the decisions and make the two fills
  incomparable.

`ocT` and `mkt_oc`, the two second implementations (`pnl_recomputed_fill`,
`contributions_fill` — a copy of D322's `contributions` with the entry-bar splice; the
D322 module is not edited) and the synthetic fixture live in `scripts/d340_fill.py`.

## 2. Cells

D338's `retrace_leg` cell (symmetric, depth 2, k=20, D303 target, F0) and the incumbent
C0 (N=2/target, k=5), each under `fill ∈ {close, open}`, both lenses, PB and PUB, GC+HTB
borrow. The **implementation-lag premium** per leg: `mean(sgn · (r1T − ocT)[e0, row])`
over entered names — what the same-close convention credits per entry. D338's top-five
table under both fills. A 200-draw rank-rotation null for the open-fill `retrace_leg`
cell, seeded `[W.SEED, 340]`, one simulation per draw costed under both conventions,
**teeth on the gross null** (p95 > 0 on gross bp/bar; the matched-cost net null is
reported beside it as the cost test — D338 §2's correction).

## 3. Predictions

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* the D338 cell's PUB net falls by **more than 5 bp/bar** under the open fill (from +18.93). |
| **Q2** | the long leg's implementation-lag premium is **positive** — names that broke below their swing low gap up at the next open — and larger in magnitude than the short leg's. |
| **Q3** | the top-5 trade share of the ledger falls **below 35%** (from 41.7%). |
| **Q4** | the incumbent C0 moves by **less than 2 bp/bar** on PUB net (liquid names, k=5). |
| **Q5** | the fallback covers **< 1%** of priced name-bars and **< 2%** of entries. |
| **Q6** | the open-fill `retrace_leg` cell is still **above its gross null's p95**. |
| *check* | VSA's entry-bar credit goes from +329.8% to **389.20 / 195.05 − 1 = +99.5%**; a reproduction, not a prediction. |

## 4. Stop conditions

- **Q1 holds** → the same-close fill is a measured hole in STACK §3, and **every net
  number quoted from D300 onward carries an open-fill companion** wherever it is quoted
  again. The default stays `"close"` so every published identity still reproduces; new
  studies declare which fill they score.
- **Q4 fails** → the incumbent's history was flattered by the gap too; D318's
  re-costing is re-opened under the open fill.
- **Q6 fails** → `retrace_leg`'s ordering of the gate was an overnight-gap effect, and
  D338's "the signal is real" is withdrawn.
- **Q2 fails** (premium ≤ 0 on the long leg) → the gap is not systematically in the
  book's favour and the convention's bias is noise, not a tilt; recorded as such.

## 5. Assertions — properties of code

| | |
|---|---|
| **[ID]** | (a) D303's no-exit control reproduces bit-identically with `W.BASE_HOLD` at its import default (D306 [4] restated); (b) the D338 cell reproduces `data/d338_retrace_leg_candidate.json` to 1e-9 on the close fill; (c) `simulate(A2)` with the two extra keys equals `simulate(A)` bitwise on the close fill; (d) the open fill differs on > 0 bars |
| **[V]** | `fill="x"` raises `ValueError`; `fill="open"` on the plain cache raises `KeyError`; a shape mismatch raises |
| **[E1]** | with `use_target=False` (exits by cap and delisting only) the ledgers' `(row, e0, age, side)`, `ent`, `cnt0`, `cnt1` are identical across fills, and P&L differs on exactly the trades whose entry cell has `ocT ≠ r1T` |
| **[E2]** | with the target: t* = the first bar on which the exit-event sets differ; every trade closed before t* is identical; `ent` first differs at ≥ t*; t* and the share of trades that differ are reported |
| **[G]** | synthetic: a name gaps +50% at the open and is flat open-to-close, the market gaps +1% and is flat; the close fill books long +0.49 and short +0.51 on the entry bar; the open fill books **exactly 0.0** on both (pins `mkt_oc`) |
| **[F]** | fallback < 1% of priced cells; its share of entries and of ledger P&L printed |
| **[P]** | every trade in every ledger recomputed from `(row, e0, age, side)` with `ocT`/`mkt_oc` on the entry bar and `r1T`/`mkt` after, to 1e-12, both fills; on the close fill the same function with `(r1T, mkt)` substituted reproduces the ledger |
| **[2]** | reconciliation with `contributions_fill`: the per-trade disagreement with D322's `contributions` equals `sgn · w · (ocT − r1T)[e0, row]` exactly; gross reconstructs to < 1 bp up to the open tail |
| **[L2]** | `ocT` on 3,000 sampled cells with a real open rebuilt from the raw `Bar` objects; `r1T ≠ ocT` on sampled ex-date cells |
| **[6]** | [ID](b) raises on a book handed +5 bp on 200 masked bars |

`W.BASE_HOLD` is saved and restored around [ID](a) and [G]. D306's own `--selftest`
[10] against `data/d300_width.json` is known-stale since D333 (D337 §10) and is expected
to fail on the untouched reference; [4] and the rest must pass on the edited module.

## 6. Scope

**In:** the flag, the helper, the two cells under both fills, the premium per leg, the
null on the open-fill `retrace_leg` cell. **Out:** a fill at the next *close* (a two-bar
lag; not the question); intraday fills; re-running every D300-family study — the
companion numbers are owed where a number is next quoted, not all at once; the holdout.

## 7. Files

`docs/decisions/D340-execution-lag-a-next-open-fill.md` (this record) ·
`scripts/run_d306_width_exits.py` (the flag), `scripts/d340_fill.py`,
`scripts/run_d340_open_fill.py`, `data/d340_open_fill.json` (to follow).
