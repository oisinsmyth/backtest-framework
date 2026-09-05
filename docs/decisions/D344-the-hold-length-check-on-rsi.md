# D344 — the hold-length check on `rsi`: does a longer hold cut cost faster than it dilutes the ordering?

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). Nothing here is a
result. Three cells, declared here; nothing else is swept.
**Date:** 2026-09-05
**Area:** Cost model · strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

The candidate grosses +14.4 bp/bar and pays 11.3 of it in cost under the published
convention. Cost per bar is the held round trip times turnover, and turnover in this
construction is one over the hold (D296: `1/k` at every depth). The hold is the one cost
lever the programme owns that needs no new data and no new fixture. D323 found `rsi`
peaks at k=10 on net Sharpe *unfloored, same-close fill, per-bar spread*; D335 chose k=20
for every leg; nobody has looked under the floor, the open fill and the published spread,
where cost is twice as heavy and the arithmetic may favour the longer hold.

## 1. Cells

`rsi` symmetric · depth 2 · D303 target · F0 · `keep_v2` · open fill · PUB primary, PB
beside · GC+HTB · both lenses, at **k ∈ {10, 20, 40}**. k=20 is D343's `rsi` v2 cell and
is held as an identity. **No other parameter moves.** Each cell gets a 200-draw rotation
null with its resolution stated; multiplicity is three and is reported as such.

## 2. Predictions

Q1 is load-bearing and against D323's unfloored ranking. Q7 is against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* PUB net at **k=40 exceeds** PUB net at k=20 (+3.10): cost falls faster than the ordering dilutes. |
| **Q2** | PUB net at k=10 is **below** k=20's — the shorter hold pays twice the cost for less than twice the gross. |
| **Q3** | *(mechanism)* turnover on names held scales as 1/k within **15%**: `turn(10)/turn(20)` and `turn(20)/turn(40)` both in [1.7, 2.3]. |
| **Q4** | gross bp/bar **falls monotonically** with k — the ordering dilutes over a longer hold. |
| **Q5** | the held PUB round trip moves by **less than 35%** across the three k — k is a turnover axis, not a population axis (D323 [3], where it moved 33%). |
| **Q6** | every one of the three cells is **above its gross null's p95** with p95 > 0. |
| **Q7** | *(against)* k=40's PUB net Sharpe exceeds k=20's (+0.159). |
| **Q8** | no cell's top trade exceeds **7%** of its ledger. |
| *check* | k=20 reproduces D343's `rsi` v2 cell to 1e-9. |

## 3. Stop conditions

- **Q1 and Q6 hold at k=40** → the candidate cell moves to k=40 **as a declared choice
  made after seeing three cells**; the multiplicity is written into D342's out-of-sample
  design, which is what protects the choice; the record quotes k=40's numbers beside
  k=20's and never alone.
- **Q1 fails** → k=20 stays; the hold is not a cost lever on this book and the record
  says why (the ordering decays faster than cost falls).
- **Q6 fails at any k** → that k is out regardless of net.
- **Q3 fails** → turnover is not 1/k here and D296's arithmetic is re-examined before
  anything is read.
- **Nothing is promoted.** A k chosen from three cells is a parameter, not a validation.

## 4. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | cache key; F0 counts; raw factor and `keep_v2` share == D343 |
| **[1]** | k=20 reproduces D343's `rsi` v2 cell to 1e-9 — net and Sharpe under both conventions, invariant per trade |
| **[T]** | `W.BASE_HOLD` bites: `ent` totals differ across k and every ledger's max age equals its k |
| **[A]** | lag audit on the k=40 gate (the gate is k-invariant: assert the three cells read one gate bitwise) |
| **[S]** | every k=40 trade equals `pnl_recomputed_fill` to 1e-12; favourable paths pay positively |
| **[RQ]** | compound accumulation at k=40: same entries, different P&L |
| **[2]** · **[3]** · **[N]** · **[B]** · **[6]** | as D343 |

## 5. Files

`docs/decisions/D344-the-hold-length-check-on-rsi.md` (this record) ·
`scripts/run_d344_hold_length.py`, `data/d344_hold_length.json` (to follow).
