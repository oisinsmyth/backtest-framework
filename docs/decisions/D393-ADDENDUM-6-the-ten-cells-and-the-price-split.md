# D393 ADDENDUM 6 — all ten cells observed: **no cell covers its costs**, and the entire edge sits in the third that is most expensive to trade

**Status:** ADDENDUM 6. **DESCRIPTIVE — no null drawn, no hurdle scored, nothing admitted (R15).**
**Date:** 2026-09-08 · Runner: `scripts/run_d393_cells_and_price.py --cells --price` · Artifact:
`data/d393_cells_and_price.json` · 50 s, one process · **Holdout reads: 0.**

---

## 1. (a) The ten pre-registered cells — reported in full, NOT picked (R14's fourth amendment)

| cell | trades | gross | median | t | hold | per-bar | 2c | net | **ratio** |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| E1/cap5 | 24,777 | +4.72 | +0.88 | +1.49 | 5.0 | +0.945 | 61.48 | −56.76 | 0.08× |
| E1/cap10 | 22,855 | +10.52 | +6.78 | +2.27 | 10.0 | +1.053 | 61.40 | −50.88 | 0.17× |
| **E1/cap20** *(primary)* | 20,785 | +22.06 | +13.38 | **+3.09** | 20.0 | +1.104 | 61.19 | −39.13 | 0.36× |
| E1/cap40 | 16,951 | +17.65 | +7.87 | +1.67 | 39.9 | +0.442 | 61.04 | −43.39 | 0.29× |
| **E1/cap60** | 14,192 | **+32.82** | +23.81 | +2.33 | 59.9 | +0.548 | 60.65 | −27.83 | **0.54×** |
| E3/cap5 | 24,672 | +3.56 | +3.94 | +1.10 | 5.0 | +0.713 | 61.35 | −57.79 | 0.06× |
| E3/cap10 | 22,404 | +11.15 | +4.59 | +2.25 | 10.0 | +1.115 | 61.43 | −50.28 | 0.18× |
| E3/cap20 | 20,626 | +11.21 | +8.48 | +1.60 | 20.0 | +0.561 | 61.35 | −50.14 | 0.18× |
| E3/cap40 | 16,821 | +22.89 | +25.84 | +2.16 | 40.0 | +0.573 | 61.04 | −38.15 | 0.37× |
| E3/cap60 | 14,189 | +28.23 | +17.30 | +1.99 | 59.9 | +0.472 | 60.58 | −32.35 | 0.47× |

**Cost is ~61 bp in every cell**, confirming the arithmetic that drove this run: **cost per trade is
one round trip regardless of hold.**

> **THE BEST RATIO IN THE ENTIRE PRE-REGISTERED SPACE IS 0.54×**, against gate 1c's ≥ 1.0× and 2c's
> ≥ 1.5×. **H2 fails in all ten cells.**

**The cap profile is not monotone** — E1 runs +4.72, +10.52, +22.06, **+17.65**, +32.82. Under gate
1i an edge peak is horizon-**unresolved**; this is not even a clean peak, and cap 40 dipping below
cap 20 on both gross and t is a ragged profile rather than a horizon.

**The pre-registered primary is the best of the ten on `t`** (+3.09). That is not selection — cap 20
was fixed in §3 before any number existed — but it is exactly the configuration §7's best-of-10
floor exists to price.

### 1a. A CORRECTION TO THIS RUNNER'S OWN RENDERER, found on reading its output

The HOLD-DRIVEN check compared only **adjacent** caps, so it printed "ratio down" for E1 cap20→40
and never made the comparison that matters — **the primary against the best cell**:

> **E1 cap 20 → cap 60: ratio rises 0.36 → 0.54 while the per-bar edge FALLS 1.104 → 0.548.**
> Under [D289](D289-the-promotion-pipeline.md)'s seventh amendment that is **HOLD-DRIVEN, not
> clearing** — the improvement is bought with capital-time, not with edge.

Cap 40 dipping between them hid this from a pairwise scan. **The renderer is wrong to compare only
neighbours when the pre-registered primary is the reference**, and the fix belongs in the runner
before it is used again.

---

## 2. (b) The price-tercile split of the primary ledger — DIAGNOSTIC, not a construction

Terciles from `run_d392_base_rate_atlas.tercile_pools`, the atlas's **own** construction, so the
split and the floor are measured on the same partition. All 20,785 trades are assigned.

| band | trades | price | gross | half-spread | 2c | net | ratio | **own floor** | |
|---|--:|--:|--:|--:|--:|--:|--:|--:|---|
| **lo** | 7,023 | $17.85 | **+59.04** | 34.49 | 74.58 | **−15.54** | 0.79× | +39.54 ± 3.73 | **above** |
| mid | 6,846 | $45.09 | +18.56 | 28.50 | 59.22 | −40.66 | 0.31× | +19.84 ± 2.45 | **below** |
| hi | 6,916 | $115.19 | **−12.04** | 26.56 | 54.00 | −66.04 | −0.22× | −1.18 ± 2.23 | **below** |

> **The entire edge is in the cheapest third — which is the third that costs the most to trade.**
> The expensive tercile, where the round trip falls to 54 bp, earns **NEGATIVE gross**.

**So a price filter cannot rescue this.** Trading up the price scale to cut cost destroys the
signal: it is [D284](D284-the-overnight-long.md)'s and D285's lesson repeating on a new
construction.

**And the conditional floor is what makes the cheap band readable.** Against the *unconditional*
+12.67 floor, +59.04 would look like an enormous edge. Against its **own** +39.54 price-conditional
floor it is **+19.5** — real, but a different number entirely. **D392 exists for exactly this, and
this is its first load-bearing use.**

**Only the cheap band beats its own floor.** Mid is −1.28 below; hi is −10.86 below.

**No band is net positive. The best net anywhere in this study is −15.54 bp/trade.**

---

## 3. What this settles and what it does not

**Settles:**

1. **H2 fails everywhere in the pre-registered space** — best coverage 0.54×, and that cell is
   HOLD-DRIVEN against the primary.
2. **Price filtering is not a route to profitability here**, and the record now has the measurement
   rather than the intuition.
3. **The cap profile is ragged**, which is itself a caution about the +22.06 cell.

**Does not settle:**

1. **§7's best-of-10 floor is still uncomputed.** It can only subtract from D393's +0.91 bp binding
   margin on B.
2. **Nothing here re-opens or re-closes any of D393's four nulls** — the construction is unchanged;
   this is a report on the same ledgers.
3. **Exit rules other than a plain cap are untested**, which is [D394](D394-exit-rules-on-the-low-hold.md).

---

## 4. Assertions and hygiene

- **Terciles are the atlas's own** `tercile_pools`, so the split and the floors are the same
  partition rather than two similar ones.
- **The primary cell is simulated once** and reused by (b), so (a) and (b) cannot disagree about
  the ledger they describe.
- **[P]** the JSON was persisted before rendering.
- **Memory, as the principal asked:** build intermediates are freed after the masks are derived —
  steady state **0.33 GB**; the transient panel build peaks near 3.1 GB and was not re-measured in
  this run.
- **Holdout: 0 reads.**

---

**Status footer.** Descriptive only. Nothing admitted, nothing retired, no holdout read.
`docs/BOOK.md` holds S1 and S2, neither at capital; `docs/BOOK_PROP.md` is empty.
