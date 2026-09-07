# D367 — the gate deconstructed, and the book without its ten best names

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). **OHLCV only.**
**Date:** 2026-09-07 · **Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.** §5 declares the out-of-sample protocol and
**explicitly does not run it** — the principal's instruction is that the holdout is not spent yet.

---

## 0. Why

D366 found that its nine-condition gate clears its own time rotation (+8.09 against a p95 of +7.02) while a
*randomly-timed* gate of the same shape and share still earns **+4.10**. Two questions follow directly, and the
principal has asked for both:

1. **Which conditions actually time, and which only reduce exposure?** Nine conditions were added by search and
   the ladder was monotone; no individual condition has ever been tested, and no pair.
2. **Does anything remain when the ten names carrying the margin are gone?** D366's jackknife left +4.60 — the
   random gate's median — but never asked whether *that* book beats *its own* controls.

**On the 252-bar cap.** The principal has declared it a **holding-period constraint, not a fitted parameter**: a
hold approaching a year is the longest tolerable without a strong reason, and the value is kept for that reason
rather than because the sweep peaks there. D366 §6 showed the sweep is jagged and peaks at 242. Under this
declaration that is no longer an overfit concern — the cap is a constraint the strategy is *given*, not a number
the search chose — and nothing in this record tunes it. A dated amendment records this against D366.

## 1. What is deconstructed

D366's gate, frozen, is the conjunction of nine lagged conditions:

| | condition |
|---|---|
| **C1** | NOT the crash state: 20-bar volatility below its **expanding** 80th percentile, **or** the 63-bar return not negative |
| **C2** | index above its 200-bar mean |
| **C3** | index 63-bar return > 0 |
| **C4** | index's own 252-21 momentum > 0 |
| **C5** | 50-bar mean above the 200-bar mean |
| **C6** | index above its 50-bar mean |
| **C7** | index 21-bar return > 0 |
| **C8** | breadth: more than half of eligible names above their own 200-bar mean |
| **C9** | index at a 252-bar high |

**46 gates are run**: 9 singles, all 36 pairs, and the combined S6. Everything else in the construction is D366's,
unchanged — score `mom_252_21`, enter above rank 95 with the gate open, hold above rank 90, 252-bar cap,
equal-weight long, dollar-volume-weighted short of the eligible universe, next open on both legs, the hedge's own
borrow and rebalancing charged.

## 2. The statistic — and why raw net will not do

**Every gate has a different on-share**, so raw net confounds two things a gate does at once: choosing *when* to
hold, and choosing *how much* to hold at all. Only the first is a forecast. The primary statistic is therefore

> **timing premium = the gate's net − the median of that gate's OWN time rotation**

which holds on-share and run structure fixed and leaves only timing. Raw net, gross, on-share, trade count and
mean names held are reported beside it; a gate that is open 60% of bars and one open 9% are never compared on raw
net. A gate whose open bars number fewer than 50 after warm-up is reported as **degenerate** and excluded from
the maximum in Q4 — recorded, not silently dropped.

## 3. Nulls

- **GATE-ROT, per gate** — each of the 46 gates circularly shifted within its defined range, on-share and circular
  run structure preserved exactly, the trigger untouched. **200 draws.**
- **GATE-ROT, SHARED-OFFSET MAX** — the multiplicity control for this record's own search. Each draw generates
  **one** shift and applies it to **all 46 gates**, and the draw's score is the **maximum timing premium across
  them**. This prices "the best of 46 gates" rather than any one gate, per CLAUDE.md's grid-max convention.
- On the reduced universe (§4): **ROT** (24 rank shifts), **A′** (per-name time rotation within eligible bars, 200
  draws), **GATE-ROT** (200 draws), **C** (random direction, 1,000 draws).

## 4. The book without its ten best names

The ten names D366 measured as its largest contributors — **GME, AXTI, LITE, MSTR, NBIS, RNG, BGFV, SEDG, RH,
GDXU** — are removed from the **eligible universe**, not from the ledger, so every slot they held refills and the
book is rebuilt from scratch. The construction is otherwise D366's, unchanged.

**This is a look-ahead diagnostic and is labelled as one throughout.** The set was chosen by knowing which names
turned out best, so the reduced book is *not* a strategy and no version of it is proposable. The question it
answers is narrow and worth answering: **does what remains beat its own controls, or was the whole margin those ten
names?** A new top ten will exist inside the reduced universe; that is expected, and its concentration is reported
rather than treated as a defect.

## 5. The out-of-sample baseline, declared and NOT run

D366 changed what an out-of-sample test must clear. The baseline is no longer zero:

> **The baseline for any future out-of-sample read is that segment's OWN gate rotation median** — the same
> construction, gate circularly shifted within the segment, evaluated on the segment being read. In sample that
> number is **+4.10** against an observed +8.09, so the effect to be detected is roughly **+4 bp/bar, not +8**.

Two further conditions are declared here so that a later record cannot choose them after seeing anything:

- **Any out-of-sample test is run twice: on the out-of-sample segment alone, and on the combined data.** Both are
  reported; neither is chosen after the fact.
- The rotation baseline is computed **separately on each segment**, never carried over from this fixture.

**Nothing in §5 is executed by this record.** The holdout fixture is not opened, and D357's frozen read stays
unspent at the principal's instruction.

## 6. Predictions

Q1 and Q7 are load-bearing. Q5 is against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* **at least one single condition** has a net above the p95 of its **own** GATE-ROT — some individual condition genuinely times, rather than merely reducing exposure. |
| **Q2** | **C9** (index at a 252-bar high) has the **largest timing premium of the nine singles**. It added +2.53 alone as the ladder's last step, more than any other. |
| **Q3** | the combined **S6's timing premium exceeds every single condition's** — combining is worth more than its best part. |
| **Q4** | S6's timing premium is **above the p95 of the SHARED-OFFSET MAX** over all non-degenerate gates. This is the test that prices the deconstruction itself. |
| **Q5** | *(against)* **the best PAIR's timing premium exceeds S6's** — two conditions beat nine, and the other seven are decoration. |
| **Q6** | **fewer than half** of the 36 pairs have a net above their own GATE-ROT p95. If most pairs "work", the test is not discriminating. |
| **Q7** | *(load-bearing)* on the reduced universe, **net > 0 and above the p95 of ROT, A′ and GATE-ROT**. |
| **Q8** | the reduced universe's **own new top-10 share of P&L is within 10 points of the full universe's 45%** — concentration is a property of the signal, not of those ten names. |
| *check* | S6 in this runner reproduces D366 exactly: net +8.09, Sharpe 0.887, 988 trades, 24.5 names, 90.8% shut, to 1e-9 |

## 7. Stop conditions

These state status only. **The avenue is the principal's (R15); nothing here closes anything.**

- **Q1 holds and Q3 holds** → the gate has real timing content and combining earns its complexity. Report which
  conditions carry it.
- **Q1 holds and Q3 fails** → the timing is in one or two conditions and the other seven are search residue. The
  honest construction is the smaller gate, and that is a finding, not a promotion.
- **Q1 fails** → no individual condition times; the entire gate is exposure reduction, and D366's +4.10 was the
  whole story. This is a result and gets written up as one.
- **Q4 fails** → S6 is not distinguishable from the best of 46 searched gates; report the distribution, not S6.
- **Q7 fails** → the book outside its ten best names does not beat its own controls. That bears on capacity and on
  what an out-of-sample test could detect; it does not by itself make the trigger unreal, which ROT and A′ settled.
- Nothing is promoted. Book: empty.

## 8. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[ID]** | S6 here reproduces D366's stored `data/d366_gated_buffer.json` figures to 1e-9 |
| **[COND]** | each of the nine conditions equals an independent recomputation, and their conjunction equals S6 bit-for-bit; each single and pair equals the intersection of its members |
| **[SHARE]** | every rotated gate preserves its on-share **exactly** and its circular run-length multiset; no rotation returns the observed gate |
| **[SHARED]** | under the shared-offset arm, all 46 gates in one draw use the **same** shift — asserted by recomputing one draw's gates from the recorded shift |
| **[UNIV]** | the reduced universe differs from the full one in **exactly 10 columns**; those names appear in the full ledger and **never** in the reduced one; slots refill (trade count does not simply fall by their trades) |
| **[LOOK]** | the removed set is read from committed evidence (`data/d366_jackknife.json`), not retyped, and the record states it is look-ahead |
| **[DEGEN]** | any gate with fewer than 50 open bars after warm-up is flagged and excluded from Q4's maximum, and the count of such gates is reported |
| **[S]** | sign in money: +50 bp on one held name moves the book's bar by 50 / n_held and no other bar |
| **[6]** | [COND], [SHARE], [SHARED], [UNIV] and [S] each raise on a deliberately broken input |

## 9. Files

`docs/decisions/D367-the-gate-deconstructed-and-the-book-without-its-winners.md` (this record) ·
`scripts/run_d367_gate_deconstruction.py` (stages `--selftest`, `--gates --draws N --part p`,
`--reduced --null ARM --draws N`, `--report`) · `data/d367_gates.json`, `data/d367_reduced_*.json`,
`data/d367_report.json` (to follow). Reuses `scripts/d348_prep.py`, `scripts/run_d366_gated_buffer.py`,
`scripts/run_d365_momentum_buffer.py`, `scripts/run_d350_long_timing_screen.py`, `scripts/d365_export_trades.py`.
The holdout fixture is not read.
