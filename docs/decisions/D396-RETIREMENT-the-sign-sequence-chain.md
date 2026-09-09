# D396 — RETIREMENT of the sign-sequence chain (D393 → D395), by the principal

**Status:** RETIREMENT. **The principal closed this avenue on 2026-09-09** — the only authority that
can (R15). Nothing was admitted to either book at any point.
**Date:** 2026-09-09 · **Holdout reads spent by the whole chain: 0.**

---

## 0. What is retired

| | |
|---|---|
| **[D393](D393-the-sign-sequence-family.md)** | the sign-sequence family — `up_run_21`, `sign_flips_21`, `up_frac_21` — and all six of its addenda |
| **[D394](D394-exit-rules-on-the-low-hold.md)** | exit rules on the low hold: stops, take profits, trailing stops, pairs and the triple, 126 cells |
| **[D395](D395-the-chop-cell.md)** | the CHOP cell (high volatility ∩ low path efficiency) |

**Everything remains in the record.** Retirement here means *no further work*, not deletion — the
measurements stand and are quotable.

---

## 1. Where it actually got to, stated plainly

**`up_run_21` at E1/cap 20 cleared all four construction nulls:**

| bar | value | margin |
|---|--:|--:|
| D392 atlas floor (ALL) | +12.67 | +9.39 |
| C — random direction | +11.51 | +10.54 |
| A′ — rotated timing | +16.20 | +5.86 |
| B_s — same `rev_21` decile | +18.97 | +3.09 |
| **B — same `rsi` bucket** | **+21.15** | **+0.91** |

**And it never cleared H1**, because §7 required the p95 of a **best-of-10 floor** across the ten
pre-registered cells, and that was never computed. Every margin above is an upper bound.

**H2 failed everywhere.** Best coverage in the pre-registered space was **0.54×** against gate 1c's
1.0×, and that cell was HOLD-DRIVEN against the primary.

**The single cell that ever reached 1.00× coverage** — cap 20 CHOP, net −0.44 — **was found by
searching 36 cells, at a hold that was not the declared primary, and its own primary failed the
search floor by 22 SE.** It is retired with the rest.

---

## 2. What this chain established that outlives it

**About the universe:**

1. **Base rates are large enough to look like signals.** A purely random long earns a **36.8 bp**
   spread across price terciles, **32.2** across momentum, **12.2** across volatility (D392).
   Four candidates in this hunt died to a control or an alignment rather than to cost.
2. **The edge lives where trading is dearest.** Measured three independent ways: the cheap price
   tercile earns +59.04 and costs 74.58; the high-vol tercile earns +66.79; the CHOP filter raises
   gross 6× and *lowers* net. **Any filter that cuts cost on this universe cuts the edge faster.**
3. **A clairvoyant delisting filter would lose money.** Names nearest delisting have fatter tails
   *both ways* and earn more. **Distress is the setup, not the hazard, on a reversal book.**
4. **Hit rate is immovable.** Every cohort measured sits at **50.1–50.8%**. The edge is entirely in
   relative magnitude, never in frequency.
5. **The two tails are the same phenomenon seen twice.** Eleven observables — the score, `rsi`,
   `rev_21`, `rvol21`, price, `DD_252`, `ER_signed_21`, `ER_21`, `DV_spike`, and the vol×ER
   interaction at four windows — all predict the left and right tails within ~1 pp of each other.
6. **No exit rule closes a cost gap.** 126 cells; the best recovered **2.53 bp of a 50.88 bp gap**.
   At cap 5 the edge is **0.95% of one standard deviation and the round trip is 12.3%** — the cost
   is 13× the edge.

**About method:**

7. **An entry gate is not a flatness mechanism** — it needs a short hold or a gated exit
   (correction to `the-signal-hunt-part2.md` §2a, against FINDINGS §47).
8. **Flatness belongs to the allocator**, and the record already said so twice
   (`working/SLEEVE-VS-ALLOCATOR-PROPOSAL.md`).
9. **A filter must be scored on ASYMMETRY**, not on how well it predicts losses. Predicting losses
   is easy and useless.
10. **A null is worthless unless something known to be fake dies in it.** B_s killed `up_frac_21`
    (p50 +20.72 against an observed +21.62) which is what made its verdict on the candidate mean
    anything.

---

## 3. The instruments, which are the chain's most durable output

| | |
|---|---|
| **`scripts/lag_audit.py`** | the shared `[L]` audit — built because D391 shipped a look-ahead that cost it 82% of its result, after its own pre-registration required the check |
| **`data/d392_atlas.json`** + `run_d392_base_rate_atlas.py` | 193 cells of measured base rate, with `lookup` that **raises outside the grid**. First load-bearing use: the price-conditional floor that made +59.04 readable as +19.5 |
| **the exact permutation floor** (`run_d395_chop.py`) | best-of-N for a cell picked from a grid: no independence assumption, correlated definitions handled for free, **10,000 draws in 44 s**. It should replace normal-approximation floors programme-wide |
| **`scripts/ragged_sign_scores.py`** | Axis I, causal by truncation audit. `sign_flips_21` is **the most orthogonal score the programme has measured** (max \|ρ\| 0.025) |
| **the shard/merge pattern** | one `item_at()` definition read by every path, `[SHARD]` proving strided == sequential bit-identically, and `merge_shards` asserting full coverage before scoring |
| **a kill condition enforced in CODE** | D395's runner refuses the battery while H0's stored verdict is FAIL. It stopped a study that would have produced four favourable-looking and meaningless nulls |

---

## 4. What this retirement does NOT close

- **`sign_flips_21` as an independent INPUT.** Its case was never standalone edge — it was
  orthogonality (max |ρ| 0.025 against everything). If a conditioner or neutralisation axis is
  ever wanted, it is the strongest candidate measured. **Retired as a signal, not as a variable.**
- **Anything outside this chain.** D383's pre-registration still awaits a runner; the density
  family is not closed (FINDINGS §54); `working/SLEEVE-VS-ALLOCATOR-PROPOSAL.md` and
  `working/FINDINGS-52-corollary-NOTE.md` hold nine open questions for the principal; three atlas
  floor gaps remain (cap 5 both sides, cap 1 short).

  > **AMENDMENT, 2026-09-09 — the three atlas floor gaps are CLOSED.**
  > [D392 ADDENDUM 2](D392-ADDENDUM-2-the-last-three-floor-gaps.md), on the principal's
  > instruction: six cells, 199 in the atlas, every cell D391 reported now has an in-grid floor.
  > **A measurement, admitting nothing and closing no avenue.** What remains owed on the atlas is
  > the *conditional*-pool trade range, cap 60 above 26,991 trades, and the pools it cannot
  > pre-compute — listed in that addendum's §R7. **The rest of this bullet stands.**

---

## 5. The ledger for the whole hunt

**Candidates tested: eight. Admitted to a book: none. Holdout reads spent: zero.**

**`docs/BOOK.md` holds S1 and S2, neither at capital. `docs/BOOK_PROP.md` is empty.**
**An empty book with stated standards beats a populated one with borrowed ones.**

---

**Status footer.** Retired by the principal 2026-09-09. Nothing admitted, no holdout read.
