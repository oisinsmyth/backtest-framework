# D380 RESULT — no exit overlay beats not cutting, and R7's control inherits the rule's trade selection

**Date:** 2026-09-08
**Pre-registration:** [D380](D380-does-the-exit-rule-beat-a-random-cut.md), committed `e6365fb`, re-scoped `571b9d3` — **both before the runner existed** (R8).
**Runner:** [`scripts/run_d380_exit_rules.py`](../../scripts/run_d380_exit_rules.py).
**Artifacts:** `data/d380_exit_rules.json`. **Mining prefix only. No holdout was read.**

---

## 0. The verdict

**Every exit overlay destroys value against simply not cutting.** The baseline holds to the 40-bar
cap and earns **+160.55** per trade; the best overlay earns **+62.43**.

| | rule | fires | hold | **mean/trade** | median | bp/bar | strict p95 | **U1** | **U2** | GATE |
|---|---|---:|---:|---:|---:|---:|---:|:--|:--|:--|
| **E0** | 40-bar cap (incumbent) | — | 39.9 | **+160.55** | +51.55 | 4.02 | — | — | — | — |
| **E1** | signal invalidation | 99.6% | 6.3 | +26.96 | **+111.05** | 4.27 | +104.64 | **FAIL** | **FAIL** | **FAIL** |
| **E2** | profit target +200 bp | 80.7% | 13.8 | +62.43 | **+271.65** | 4.51 | +31.78 | PASS | PASS | **PASS** |
| **E3** | stop −200 bp | 79.1% | 14.5 | +13.99 | −275.25 | 0.96 | +199.17 | **FAIL** | **FAIL** | **FAIL** |

**Q1 held — my prediction against my own proposal.** E1, the principled exit that keys on the name's
own signal reverting, **does not beat a random cut of the same trades.**

**Q6 falsified — E2 passes.** §2 shows why that pass means much less than it looks.

**And the finding that outlives all three verdicts is methodological: R7's strict control is not a
fixed benchmark. It inherits whichever trades the rule selects, so its difficulty varies by a factor
of fifteen across rules and U1 verdicts are NOT comparable between them.** §2.

---

## 1. What was run, and the assertion that re-scoped the study

**`[OVL]` fired on the first self-test**, before any result, and §9 of the pre-registration said what
to do: *re-scope before running*. The kernel's `("invalidation", 40)` run is **not an overlay** —
exiting at a mean 6.2 bars frees each name to take signals the 40-bar cap suppressed, giving **7,945
trades against the baseline's 3,932** from the same 10,270 events. That is a different **book**, not a
modified one. Recorded as amendment `571b9d3` before the runner produced a number.

So E1 is the invalidation **condition applied to the baseline's own trades with no re-entry**, and
`[INV]` proves it is the kernel's rule rather than a re-derivation of it: on **all 3,810 entries the
two runs share, zero mismatches**.

`[CUT]` — the re-cut of stored paths against the kernel's own per-trade P&L — came back at
**0.000e+00**, exactly as Q7 predicted, because the re-cut sums the same addends in the same order.
*(D377's analogue fired at 1e-3 and found a real specification error; that it is exact here is
evidence, not luck.)*

**`[X]` caught a second dud break of mine this session.** My first `[CUT]` break perturbed `C[0, 0]`
— but `C` is a stored **cumulative sum**, so changing an early entry leaves the endpoint the
assertion reads untouched, and the break could not fire. Replaced with a perturbation of the endpoint
and a global shift; both raise. **That is twice now** — D376's was a rescale against a scale-invariant
correlation — and the pattern is worth naming: **a deliberate break must be checked against what the
assertion actually reads, not against what it is named after.**

---

## 2. R7's control inherits the rule's trade selection — and that is the study's real finding

Look at what each rule's **own** control centres on:

| rule | fires on | **its strict control's p50** | vs the baseline's +160.55 |
|---|---|---:|---|
| **E2** target | trades that reached **+200** — the **winners** | **+11.95** | randomly truncating winners is **catastrophic** |
| **E1** invalidation | 99.6% of trades — nearly everything | +83.69 | roughly a uniform truncation |
| **E3** stop | trades that fell to **−200** — the **losers** | **+181.11** | randomly truncating losers is **better than the baseline** |

**The control's difficulty ranges from +11.95 to +181.11 — a factor of fifteen — purely because of
which trades the rule chose to touch.** A rule that fires on winners is graded against an easy
control; a rule that fires on losers is graded against one harder than doing nothing.

**So E2's PASS is close to mechanical.** Its control is "randomly truncate your biggest winners", and
the target at least guarantees roughly +200 on each of them. **E2 clears that bar and still earns
61% less per trade than not cutting at all.**

**This does not overturn R7 — it sharpens it.** R7's control correctly answers *"does the rule beat
random cutting?"* It does **not** answer *"does the rule beat not cutting?"*, and on this book those
are different questions with opposite answers. **The baseline belongs in the comparison, and the
pre-registration did not put it there.** That is a gap in this record's own design, found by its own
numbers.

> **The rule, for the next overlay study:** report the rule against **both** its matched-count control
> **and** the un-overlaid baseline, and state which trades the rule selects — because the control's
> centre is a property of that selection, not of the rule's timing.

---

## 3. The median–mean trade-off, which answers the win-rate question directly

The principal asked whether exit timing could raise per-trade return **and** win rate. **It can raise
one of them.**

| | mean | median | mean − median |
|---|---:|---:|---:|
| **E0** hold to the cap | **+160.55** | +51.55 | **+109.00** |
| **E1** invalidation | +26.96 | **+111.05** | −84.09 |
| **E2** target +200 | +62.43 | **+271.65** | −209.22 |

**E1 more than doubles the typical trade (+51.55 → +111.05) and destroys 83% of the mean. E2
quintuples it and destroys 61%.** Both flip the mean **below** the median — which `CLAUDE.md` names
as the tell that the left tail is doing the work, and here it is exactly right: cutting early takes
losers off the table *and* truncates the winners the book's return actually lives in.

**So a better win rate is available, and it is not worth having.** The edge is in the right tail;
every rule that improves the middle pays for it out of the tail, at roughly two basis points of mean
per basis point of median.

---

## 4. The uncontrolled observation: cost destroys the short-hold book

The full invalidation **book** — 7,945 trades, mean hold 6.21, **reported with no control and no
verdict** per amendment `571b9d3` — is D378's front-loading warning realised:

| deployed, hedged, PUB | **gross bp/bar** | **net bp/bar** | net Sharpe | turnover | held |
|---|---:|---:|---:|---:|---:|
| **E0** baseline | +3.859 | −0.063 | −0.01 | 0.025 | 49.8 |
| **invalidation book** | **+4.639** | **−22.783** | **−2.655** | **0.161** | 15.5 |

**It earns 20% more gross per bar and is annihilated by cost**, at **6.4× the turnover**. D378
measured the edge as front-loaded and warned that a shorter hold raises the per-bar rate and the
number of round trips together. **This is the size of that trade-off: +0.78 bp/bar of gross bought
for −22.7 bp/bar of net.**

**It is not a verdict on that construction** — it has no control, and a cheaper implementation of the
same idea is not ruled out by this. It is a statement of what the naive version costs.

---

## 5. Predictions, scored

| | prediction | outcome |
|---|---|---|
| **Q1** | *against my own proposal:* **U1 fails for E1** | **HELD** — and the mechanism I gave held too: the edge decays smoothly in time, so the *state* the rule keys on adds nothing beyond the *time* it implies |
| **Q2** | E1's mean hold under 25 bars | **HELD** — 6.3 |
| **Q3** | E1 beats the **loose** control while failing the strict one | **FALSIFIED** — it fails both (+26.96 against loose p95 +107.34). It is not picking trades either |
| **Q4** | E1's mean falls below +160.55 while its bp/bar rises above +4.02 | **HELD** — +26.96 and 4.27 |
| **Q5** | the trigger fires on more than half of trades | **HELD** — 99.6% |
| **Q6** | E2 and E3 both fail their own controls | **FALSIFIED** — E3 fails, **E2 passes**, and §2 explains why the pass is weak |
| **Q7** | `[CUT]`'s deviation below 1e-12 | **HELD** — 0.000e+00 |

**Five held, two falsified.** Both falsifications are informative rather than embarrassing: Q3 was
wrong because E1 is worse than I thought, and Q6 was wrong for a reason — §2 — that the
pre-registration had no way to anticipate.

---

## 6. What this closes

**Exit timing on this construction is closed, on the evidence.** Three rules — a signal-keyed
invalidation with no free parameter, a symmetric target, a symmetric stop — and **none of them beats
holding to the cap.** The one that beats its own control still loses 61% of the mean. Combined with
[D378](D378-RESULT-the-entry-day-does-matter-and-it-survives-losing-its-best-trade.md), which found
entry timing real but worth at most half a round trip, the picture on this book's *timing* is now
complete: **the entry day carries information, the exit does not, and neither is large enough to
matter after cost.**

**Under [R15](../RULES.md#r15) closing the avenue is the principal's**, and this record does not
presume it. What it removes is the open question that D378 left.

---

## 7. What this did not settle

- **Whether a cheaper short-hold implementation works.** §4's book is the naive version at 6.4× turnover.
- **Whether an asymmetric target/stop pair does better.** Only symmetric ±200 was declared, and
  sweeping now would be a post-hoc search.
- **Whether §2's finding generalises.** The control's centre inherited trade selection *on this book*;
  the mechanism is general but the magnitude was measured once.
- **Anything out of sample.** Holdout #2 remains unspent.

---

*Result committed separately from the pre-registration, per R8. Nothing admitted to either book.*
