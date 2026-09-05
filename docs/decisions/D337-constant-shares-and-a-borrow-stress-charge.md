# D337 — constant-shares accumulation on the short leg, and a declared borrow stress charge

**Status:** PRE-REGISTERED. Committed **before the simulator change and the runner
exist** (R8). Nothing here is a result.
**Date:** 2026-09-05
**Area:** Strategy research · **personal track** · cost model

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why, and what is already known

D328 §11 found the book's daily-rebalanced accounting pays a **rebalancing premium**:
a rebalanced long on a bouncy name harvests volatility, a rebalanced short pays it.
D329 measured it per trade — `hist_L`'s short leg **−45.8 bp**, its long leg +25.2;
`skew_63`'s short −23.5 — and named the fix: hold the short leg in constant *shares*.
Separately, no runner has ever charged **borrow** (FINDINGS §16), and D331 identified
the cohort a stress charge would target.

**One identity governs the first half of this study and is stated before it runs.**
With entries and exits held fixed, a constant-shares trade's P&L is *mechanically* the
summed P&L minus D329's premium on the same bars (`per_leg`:
`sgn·(Σv − expm1(Σ log1p v))`). So "the short leg improves by 46 bp" is not a
prediction; it is a reproduction check, and it is listed as one. **The content is where
the ledger is not already known**: the fixed-hold arm, the net sign after cost and
borrow, the hard-to-borrow share, and whether the leg-wise composite survives.

## 1. The accumulation change, declared

`run_d306_width_exits.simulate` gains a keyword-only `accumulate="sum"|"compound"`.
Each held position carries two extra slots, `Σv` and `Σ log1p v`. **The exit rule reads
the summed slot as today** (its target band was calibrated on it, D303); only the P&L
appended on close changes: `sum` → `Σ sgn(v − mt)`; `compound` →
`Σ sgn(v − mt) − sgn·(Σv − expm1(Σ log1p v))`. The ledger stays a 5-tuple. **Constant
shares on the name; the market hedge `mt` stays daily-rebalanced** — the convention
D329's premium already assumes, kept for comparability. The default reproduces today's
simulator bit-for-bit (its own D303 and `d300_width.json` identities stay green).

**Per-trade only.** The bar series `ret[side][t]` is an equal-weight mean; a compounding
*book* would need drifted weights and is **out of scope**, stated here.

## 2. The borrow charge, declared

Applied to **short** positions only, per position-bar, as bp per year / 252:

| scheme | rate | who |
|---|---|---|
| **GC + HTB** | **50 bp/yr** general collateral; **500 bp/yr** hard-to-borrow | HTB if the name is inside an F0 deal window at `e0 − 1` (D331's one-bar lag) **or** its close at entry is below **$5** |
| house | **300 bp/yr** flat | the fixture's previously declared assumption (BOOK_SINGLE_NAMES_RESULTS) |
| none | 0 | the baseline |

Per trade: `rate_i × age / 252`. Per bar: `Σ_i rate_i / (252 × cnt1[t])` over each
short position's bars — the short leg's book weight is exactly 1.0 on every bar with a
short, so a flat rate is `rate/252` bp per bar. **New keys only** — `borrow_bp`,
`net_bp_borrow`, `borrow_per_trade`, `net_per_trade_borrow`; `net_bp` and
`mean_over_2c` are untouched, because three downstream runners assert `net_bp` to
1e-9. A stress, not a model; both rates are round and stated as such.

## 3. Arms

Depth 2. `H` (`hist_L`, k=20), `S` (`skew_63`, k=20), `S_F0` (`skew_63` under the F0
deal filter), `LW_F0` (`hist_L` long / `skew_63`-F0 short), `C0` (the incumbent, k=5);
× exit {target, fixed hold `use_target=False`} × accumulate {sum, compound}; borrow
{none, GC+HTB, house} and spread {PB, PUB} applied to the same ledgers afterwards.
D333-bounded panel.

## 4. Predictions

| | prediction |
|---|---|
| **Q1** | *(load-bearing, against)* `hist_L` symmetric's **short leg still nets < 0 per trade under compound, on both conventions, before borrow** (the identity puts it near −53 PB / −135 PUB). The convention does not rescue the leg. |
| **Q2** | *(unmeasured)* under fixed hold at k=20, `hist_L`'s short-leg premium is **below −60 bp** — longer holds than the target exit gives. |
| **Q3** | *(unmeasured)* fixed-hold premiums for C0 (k=5) stay within **±10 bp** on both legs. |
| **Q4** | the HTB tier covers **< 15%** of C0's short position-bars and **> 25%** of `hist_L`'s. |
| **Q5** | GC+HTB costs C0's book **< 0.5 bp/bar**; the house rate costs exactly 300/252 = **1.190 bp/bar** and takes C0's PB net from +7.15 to below 6.0 but not below 0. |
| **Q6** | *(load-bearing)* LW_F0 at k=20 nets **> 0 per trade under PUB with compound accumulation and GC+HTB borrow**. |
| *check* | each leg's compound gain equals **−premium** from D333/D331 exactly. A reproduction, not a prediction. |

## 5. Stop conditions

- **Q1 confirms** → constant shares is a sizing improvement worth ~46 bp per trade on
  that leg and **still not enough**; the incumbent's short leg is a cost problem, and
  the incumbent stays a long-leg-only candidate.
- **Q1 fails** (short leg positive under compound) → the sizing fix rescues the leg;
  the constant-shares convention becomes a declared arm for every short leg going
  forward, and D329's "worst leg measured" is amended.
- **Q6 fails** → the leg-wise book does not survive honest sizing and borrow;
  D329/D335's construction is per-trade only.
- **Q5's exact values fail** → the borrow arithmetic is wrong; nothing is read.

## 6. Assertions — all properties of code

**[1]** `accumulate="sum"` with target exits reproduces D333's new-panel cells and
D331's `S_F0` cells to 1e-12 on both lenses. **[P]** every compound trade equals
`expm1(Σ log1p v) − Σ mt`, signed, recomputed from the ledger, AND equals summed minus
the `per_leg` premium, to 1e-12. **[E]** the `(row, e0, age, side)` sets and
`cnt0 / cnt1 / ent / mask` are identical across accumulation modes for every arm.
**[B]** borrow per bar × `cnt1`, summed, equals borrow per trade, summed, within 1e-9.
**[F]** the house scheme charges exactly 300/252 bp on every bar with `cnt1 > 0`.
**[S]** kernel sign audit on synthetic paths — −50%/+100%: long summed +0.5, compound
0.0; short −0.5, compound 0.0. −50%/−50%: long −1.0 vs −0.75; short +1.0 vs +0.75.
**[K]** HTB flags are unchanged through T0 when filings after T0 are deleted.
**[V]** `accumulate="x"` raises. **[6]** raises on a book handed free money.
`run_d326_both_lenses.LEGAL` is **not** edited; borrow keys are reported, not ranked.

## 7. Scope

**Out:** the compounding book (bar series); borrow on longs (none); rates other than
the three declared; the holdout. **In:** the five arms, both exits, both accumulations,
three borrow schemes, two conventions, per trade.

## 8. Files

`docs/decisions/D337-constant-shares-and-a-borrow-stress-charge.md` (this record) ·
`scripts/run_d306_width_exits.py` (the flag), `scripts/d337_borrow.py`,
`scripts/run_d337_constant_shares_borrow.py`, `data/d337_constant_shares_borrow.json`
(to follow).
