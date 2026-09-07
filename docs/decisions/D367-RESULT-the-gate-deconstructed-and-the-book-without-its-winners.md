# D367 RESULT — the nine-condition gate is one condition, and the book without its winners loses the gate

**Status:** RESULT. Pre-registration `20f3e5b`, runner `bdee444` — both committed before this record (R8).
**OHLCV only. No holdout read. Holdout reads spent: 0. Programme total: 0.**
**Date:** 2026-09-07 · **Area:** Strategy research · **personal track**

**Five of eight.** Q1, Q2, Q3, Q4, Q8 confirmed; Q5 (against) falsified by 0.01; Q6 falsified; **Q7, load-bearing,
falsified.**

---

## Headline

**Six of the nine gate conditions are exactly redundant — not approximately, identically — because they are
logically implied by the ninth.** An index at a 252-bar high is necessarily above its 200-day mean, above its
50-day mean, has positive 63- and 21-day returns, is not in a crash state, and has broad participation. The gate
that took most of a session's search is **one condition plus a ten-bar coincidence.**

**And the gate stops being demonstrable once its ten best names are removed**, while the ranking underneath it does
not. The edge is in the cross-section; the market-timing overlay is where the fragility lives.

## 1. The nine conditions alone

Scored on **timing premium** = net − the median of that gate's **own** time rotation, which holds on-share and
circular run structure fixed. On-shares run from 9.5% to 89.1%, so raw net cannot rank these.

| gate | open% | gross | net | rot p50 | **premium** | rot p95 | rank | beat | trades | condition |
|---|---|---|---|---|---|---|---|---|---|---|
| **C9** | 9.5% | +8.49 | **+6.93** | +4.02 | **+2.91** | +6.43 | 98.0% | 4 | 1,008 | index at a 252-bar high |
| C8 | 76.7% | +4.12 | +2.81 | +1.95 | +0.85 | +2.96 | 90.5% | 19 | 1,602 | breadth > 50% |
| C5 | 80.4% | +4.04 | +2.75 | +1.92 | +0.82 | +3.52 | 79.0% | 42 | 1,535 | 50-bar mean above 200-bar |
| C3 | 72.9% | +3.99 | +2.63 | +1.93 | +0.70 | +2.71 | 91.0% | 18 | 1,663 | 63-bar return > 0 |
| **C6** | 70.1% | +4.11 | **+2.67** | +1.98 | +0.69 | +2.63 | 96.0% | 8 | 1,738 | index above its 50-bar mean |
| C2 | 79.4% | +3.72 | +2.42 | +1.88 | +0.54 | +3.12 | 76.5% | 47 | 1,624 | index above its 200-bar mean |
| C7 | 64.9% | +3.91 | +2.37 | +2.01 | +0.36 | +2.48 | 89.0% | 22 | 1,833 | 21-bar return > 0 |
| C1 | 89.1% | +3.06 | +1.77 | +1.55 | +0.22 | +2.09 | 72.0% | 56 | 1,722 | NOT the crash state |
| **C4** | 80.1% | +3.00 | +1.62 | +1.69 | **−0.07** | +3.02 | **43.5%** | **113** | 1,604 | index 252-21 momentum > 0 |
| **S6** | 9.2% | +9.65 | **+8.09** | +3.93 | **+4.15** | +6.42 | **100.0%** | **0** | 988 | all nine |

**Only two singles clear their own rotation's p95: C9 and C6.** Q1 holds. C9 has much the largest premium, so Q2
holds as predicted.

**C4 is below its own rotation's median** — 113 of 200 randomly-timed C4 gates beat the real one. On its own it has
*negative* timing content.

## 2. The redundancy, which is the finding

| gate | open% | net | premium |
|---|---|---|---|
| C9 alone | 9.5% | +6.93 | +2.91 |
| C9 + C1 / C2 / C3 / C6 / C7 / C8 | 9.5% | **+6.93** | **+2.91** |
| C9 + C5 | 9.4% | +6.96 | +2.96 |
| **C9 + C4** | 9.3% | **+8.06** | **+4.14** |
| S6, all nine | 9.2% | +8.09 | +4.15 |

**Six of the eight other conditions change nothing to the last decimal.** S6's 380 open bars are a strict subset of
C9's 390. The nine-condition gate is really **C9 + C4**, and S6 beats that pair by 0.01 bp/bar — Q5 predicted the
best pair would *exceed* S6 and it falls short by that margin, which is a falsification in name and a tie in fact.

**The entire difference between a one-condition gate and the full one is ten gate-open bars and about twenty
trades, worth +1.13 bp/bar.** And the condition doing it — C4 — has no standalone timing content at all. That is
the signature of either a genuine interaction or a ten-bar coincidence, and nothing here distinguishes them.

## 3. Multiplicity — the control this record was built for

The shared-offset arm applies **one** shift to all 46 gates per draw and scores the best timing premium available
under it, pricing "the best of forty-six" rather than any single gate.

| | p50 | p95 | max | S6's premium | draws beating S6 |
|---|---|---|---|---|---|
| best-of-46 under a shared rotation | +1.22 | **+2.96** | +3.88 | **+4.15** | **0 of 200** |

**S6 clears it outright — Q4 confirmed.** No degenerate gates; all 46 had ≥50 open bars.

**But C9 alone does not.** Its premium of +2.91 sits just under the +2.96 p95. Taken as a pre-specified condition
C9 is comfortable (98th percentile of its own rotation); priced for the fact that forty-six gates were examined to
find it, it is a hair short. **The one-condition gate is cheaper in parameters and weaker in evidence, and the
difference between the two verdicts is the same ten bars.**

**Q6 failed: 20 of 36 pairs clear their own p95**, against a predicted fewer than 18. A majority of arbitrary
condition pairs beat their own rotation, which says broad trend conditions carry *some* timing value generally —
a real effect, but it also means clearing one's own rotation is a low bar here.

## 4. The book without its ten best names — Q7 falsified

**Look-ahead diagnostic, not a strategy.** The removal re-ranks the universe (1,159 names' percentiles move; the
ten names' 33 trades are replaced by 131 entries that did not previously exist).

| | gross | net | Sharpe | ann | maxDD | trades | era 1 | era 2 |
|---|---|---|---|---|---|---|---|---|
| full universe | +9.65 | +8.09 | 0.887 | +20.4% | 3,158 | 988 | +0.46 | +12.10 |
| minus the ten | +5.46 | **+3.91** | 0.478 | +9.8% | 5,071 | 995 | +0.28 | +5.87 |

| arm | p50 | p95 | rank | beat | clears? |
|---|---|---|---|---|---|
| ROT | −10.70 | −4.23 | 100.0% | 0 of 24 | YES |
| A′ | −0.35 | +1.82 | 100.0% | 0 of 200 | YES |
| **GATE-ROT** | +1.65 | **+4.47** | 85.0% | **30 of 200** | **NO** |
| C | −0.20 | +3.76 | 95.3% | 47 of 1,000 | YES |

**The trigger survives losing its ten best names; the gate does not.** Zero of 24 rank rotations and zero of 200
time rotations beat the reduced book, so momentum is still working in the remaining 505 names. But 30 of 200
randomly-timed gates beat it. It still makes money — making money and failing GATE-ROT are not opposites, because
that null keeps the trigger intact and is centred at +1.65, not zero.

**The gate's timing edge and the P&L concentration are the same phenomenon.** The real gate lost +4.18 when the ten
names went; a random gate lost only +2.45. So **43% of the gate's entire timing value was in ten names** — the gate
was not merely holding good names, it was open during the periods those ten names ran.

**Q8 confirmed exactly.** The reduced universe's own new top ten take **45% of its P&L — identical to the full
universe's 45%** — with 12 names to half the P&L against 12 before (SHOP 5.2%, PLTR 5.2%, CVNA 4.7%, IMGN 4.6%,
WDC 4.6%). **Concentration is a property of the signal, not of those names.** Remove the winners and a fresh set
concentrates identically, so it cannot be diversified away.

## 5. Two corrections to what this programme believed

**The book is invested 91.6% of bars, not 9.2%.** The gate is shut on 90.8% of bars, but it blocks *entry* only —
positions run to the 252-bar cap — so the book holds 22.5 names on average across all bars, 24.5 when invested,
with three flat stretches (longest 173 bars). Every earlier description of this construction as "flat 90% of the
time" was wrong, including in this session. **The gate rations entry occasions; it does not reduce exposure**, and
the label "exposure reduction" applied to the GATE-ROT median in D366 §4 should be read as *entry rationing*.

**The dual exit rank is dead.** S6 with exit rank 90 everywhere gives +8.11 at Sharpe 0.887 against +8.09 at 0.887
for the 80-open/90-shut split. The open-state exit rank is not a degree of freedom and can be removed.

**The no-gate baseline, matched properly.** With the gate always open the exit loosens to 80, which is a different
book; matched at 90 the ungated construction earns **+1.85** (Sharpe 0.270, 40.4 names, 2,315 trades) rather than
the +1.36 first computed. The decomposition on the full universe is therefore: ungated **+1.85** → a random gate
**+4.10** → the real gate **+8.09**. Roughly a third of the gate's contribution is entry rationing that any gate of
that shape delivers; two thirds is this gate's timing.

## 6. Predictions

| | | verdict |
|---|---|---|
| **Q1** | *(load-bearing)* ≥1 single condition above the p95 of its own rotation | **CONFIRMED** — 2 of 9 (C9, C6) |
| **Q2** | C9 has the largest single timing premium | **CONFIRMED** — +2.91, next is +0.85 |
| **Q3** | S6's premium exceeds every single's | **CONFIRMED** — +4.15 vs +2.91 |
| **Q4** | S6 above the p95 of the shared-offset max | **CONFIRMED** — +4.15 vs +2.96, 0 of 200 |
| **Q5** | *(against)* the best pair exceeds S6 | **FALSIFIED by 0.01** — C4+C9 +4.14 vs +4.15; a tie in fact |
| **Q6** | fewer than half the pairs clear their own p95 | **FALSIFIED** — 20 of 36 |
| **Q7** | *(load-bearing)* reduced universe above ROT, A′ and GATE-ROT p95 | **FALSIFIED** — fails GATE-ROT, +3.91 vs +4.47 |
| **Q8** | reduced top-10 share within 10 points of 45% | **CONFIRMED** — 45%, exactly |

## 7. Assertions

All pass; `--selftest` runs in 3 s. `[ID]` reproduces D366's **stored** result to <1e-9. `[COND]` `[SHARE]`
`[SHARED]` `[UNIV]` `[LOOK]` `[DEGEN]` `[S]` hold, and `[6]` shows five of them raising on broken input.

**Two probes that were wrong and were fixed before being trusted:**

1. **The circular run-length check failed a correct rotation.** It doubled the array and grouped it, which merges
   runs across the seam and is not the circular statistic. Replaced with a proper ring version, verified against a
   hand-computed case (`[1,1,3,5]` on a ten-bar sequence) and shown invariant under all ten rolls.
2. **D366's jackknife answered a weaker question than it claimed.** It kept the full-universe percentile grid and
   only suppressed the ten names from the book; its comment that the freed slots refilled was wrong, because this
   construction has no slots — entry is unconditional on other names, so the reduced ledger was exactly the full
   one minus those trades. A real universe removal NaNs the names out of the score **before** the percentile grid
   is built. D366's +4.60 stands, read as "do not trade these ten"; D367's +3.91 is the universe answer.

## 8. Status

**Nothing promoted. Book: empty. The avenue is the principal's (R15).**

Against the pre-registration's stop conditions: **Q1 holds and Q3 holds**, so the gate has real timing content and
combining beats its best part — but §2 shows "combining" means adding exactly one further condition, on ten bars,
whose standalone timing content is negative. The pre-registration's clause for that case reads *"the honest
construction is the smaller gate."*

The open decision, stated rather than taken:

- **C9 alone** — one parameter, clears its own rotation at the 98th percentile, but sits 0.05 bp/bar under the
  best-of-46 multiplicity control.
- **S6 (≡ C9 + C4)** — clears everything including multiplicity, at the cost of a condition that does nothing alone
  and whose contribution is ten bars.

**Neither is settled by more work on this fixture.** What would settle it: the continuous relaxation of C9
(*within d% of a 252-bar high*, d = 0, 0.5, 1, 2, 5, 10) — if the premium decays smoothly the mechanism is real and
the knife-edge worry dies; if it collapses at d = 0.5% then this is the second jagged surface in this construction
after the cap sweep, and that is a pattern.

## 9. Files

`docs/decisions/D367-the-gate-deconstructed-and-the-book-without-its-winners.md` (pre-registration) ·
`scripts/run_d367_gate_deconstruction.py` · `data/d367_gates.json`, `data/d367_reduced.json`,
`data/d367_report.json`. Reuses `scripts/d348_prep.py`, `scripts/run_d366_gated_buffer.py`,
`scripts/run_d365_momentum_buffer.py`, `scripts/run_d350_long_timing_screen.py`. The holdout fixture is not read.
