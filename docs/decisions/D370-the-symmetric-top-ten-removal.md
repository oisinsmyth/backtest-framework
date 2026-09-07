# D370 — the symmetric top-ten removal: does the gate survive when every draw loses its own winners?

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
**OHLCV only. No holdout read. Holdout reads spent: 0. Programme total: 0.**
**Date:** 2026-09-07 · **Area:** Strategy research · **personal track**

---

## 0. Why — the principal's objection, and the measurement that upheld it

D367 removed the ten names that contributed most to the observed book and asked whether what remained beat its
own controls. It did not (D369: −0.311, −15.8 SE). The principal objected that the test may be mis-posed — the
gate is being asked to work in a world where the thing it identifies has been deleted.

**Measured in D369 §5, the objection largely holds:**

- the observed book drops **4.187** bp/bar when the ten go; the median rotated gate drops only **2.256**. The real
  gate is penalised **1.85×**;
- because the ten are defined by the *observed* book's P&L. They are **45.1%** of its P&L and a median **~40%** of
  a rotated book's — so the removal is nearly symmetric in share and asymmetric in level only because the observed
  book earns more, which is the thing under test.

**A set chosen from one book's outcome cannot be used to test that book against books that did not produce it.**

## 1. The fix

**Every draw loses its own top ten.**

```
  observed   the book under the real gate, with ITS OWN top ten names removed from the universe
  each draw  the book under a ROTATED gate, with THAT DRAW'S OWN top ten names removed
```

Both sides are treated identically: each loses the ten names that its own ledger made largest. The selection is
performed inside every draw, so nothing crosses between the observed book and its null.

**Removal means removal from the UNIVERSE, re-ranked** (D367's correction): the ten names are NaN-ed out of the
score *before* the percentile grid is built, so every other name's rank moves and names that never reached rank 95
now can. Suppressing them from the book while leaving the ranking intact is the weaker question and is not what
is asked here.

**And one inconsistency from D367/D369 is fixed.** There, the dollar-volume hedge still spanned the **full**
universe including the removed names. If the names cannot be traded they cannot be shorted either, so the hedge is
rebuilt on the reduced universe. **The gate's index is NOT reduced** — the market still contains those names
whether or not this book trades them, and reducing it per draw would make the gate a different object in every
draw, which is exactly what a rotation null must not do.

Everything else is D366's frozen construction under D369's convention: `mom_252_21`, enter above rank 95 with the
gate open, **single exit rank 90**, 252-bar cap (a declared holding-period constraint), equal-weight long,
dollar-volume-weighted short, next open both legs, hedge borrow and rebalancing charged, PUB primary.

## 2. Nulls

- **SYM** — the gate circularly shifted within its defined range, on-share and circular run-length multiset
  preserved, **each draw removing its own top ten**. **2,000 draws** (the per-draw cost is ~6× a D369 draw
  because the percentile grid is rebuilt inside every one; 2,000 is chosen for a p95 SE comparable to D369's, and
  the achieved SE is reported and checked in Q6).
- **ASYM** — D369's existing arm, every draw losing *the observed book's* ten, is quoted for comparison. It is not
  re-run.

Every p95 carries a **1,000-resample bootstrap standard error**, and **a margin under two SEs is reported
UNRESOLVED** — the category D369 created before seeing numbers, and which caught exactly one case there.

## 3. Predictions

Q1 is load-bearing. Q3 is against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* the observed book, minus its own ten, **clears the SYM p95 by more than 2 SE**. Under a symmetric test the gate's timing survives losing its winners. |
| **Q2** | the **SYM p50 is below the ASYM p50 of +1.562**, because every draw now loses its own tail rather than someone else's. |
| **Q3** | *(against)* **SYM reverses D369's verdict** — i.e. what failed at −15.8 SE under the asymmetric test clears under the symmetric one. If this is confirmed, D367 Q7's conclusion was an artefact of the test's construction and is retracted. |
| **Q4** | the observed book's drop (full universe → minus its own ten) is **within 2 SE of the median draw's drop** — the 1.85× asymmetry D369 measured disappears once both sides lose their own tail. |
| **Q5** | the median overlap between a draw's own top ten and the observed book's ten is **fewer than 6 names** — the sets genuinely differ, which is what makes the symmetric test different from the asymmetric one. |
| **Q6** | the SYM p95's bootstrap SE is **below 0.10 bp/bar** at 2,000 draws. If it is not, no verdict here is safe and the record says so instead of reporting one. |
| *check* | with the removed set **forced** to the observed book's ten, the runner reproduces D369's stored GATE-ROT/reduced observed value to within the hedge change, and the hedge change alone is measured and reported |

## 4. Stop conditions

Status only. **The avenue is the principal's (R15).**

- **Q1 and Q3 hold** → D367 Q7's conclusion is **retracted**: the gate's edge is not carried by ten specific
  names, and the earlier verdict was an artefact of selecting the removal set from the observed book's own P&L.
- **Q1 fails** → the verdict survives a fair test: the gate genuinely depends on extreme winners, and the
  concentration is a property of the strategy rather than of the measurement.
- **Q1 UNRESOLVED** → 2,000 draws is not enough; the record states the count needed and does not run it.
- **Q4 fails while Q1 holds** → the asymmetry has a source beyond the selection, and it is named rather than
  assumed.
- Nothing is promoted. Book: empty.

## 5. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[FAST]** | the kernel is bit-identical to D366's functions (`7ba776a`), re-asserted per run |
| **[OWN]** | every draw's removed set is derived from **that draw's own** ledger, is exactly ten names, and none of them appears in that draw's reduced book |
| **[HEDGE]** | the hedge is rebuilt on the reduced universe and equals an independent recomputation; the difference from D367/D369's full-universe hedge is measured and reported |
| **[RANK]** | removal re-ranks: the removed names carry no percentile, and more than ten names' percentiles move |
| **[SHARE]** | every rotation preserves on-share exactly and the circular run-length multiset |
| **[SE]** | every p95 carries a 1,000-resample bootstrap SE; margins are reported in SE units |
| **[PART]** | workers stride the draw index; a draw's value is independent of which worker ran it, proved against a serial run |
| **[6]** | [OWN], [HEDGE], [RANK] and [SHARE] each raise on a deliberately broken input |

## 6. Files

`docs/decisions/D370-the-symmetric-top-ten-removal.md` (this record) ·
`scripts/run_d370_symmetric_removal.py` (stages `--selftest`, `--sym --draws N --part i --nparts N`,
`--report`) · `data/d370_*.json` (to follow). Reuses `scripts/d369_fast_kernel.py`, `scripts/d348_prep.py`,
`scripts/run_d367_gate_deconstruction.py`, `scripts/run_d366_gated_buffer.py`. The holdout fixture is not read.
