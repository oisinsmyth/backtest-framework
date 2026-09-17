# D466 RESULT — no construction clears the component standard at minimum tradable size; the figures that opened the ledger were scored at full-size costs in basis points

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D466-RESULT-no-construction-clears-the-component-standard-at-minimum-size-the-figures-that-opened-the-ledger-were-scored-at-full-size-costs-in-basis-points.md`. The H1 above is the full title.*

**Result of the pre-registered scoring in D466.** Runner `scripts/run_d466_components.py`
(`--selftest` passes; `--run` 0.0 min), artefact `data/d466_components.json`. In-sample
2016-01-04 to 2023-12-29, 2,051 ES sessions; **2024-01 onward unread; no holdout spent.**

**Under [R15](../RULES.md#r15) this record closes nothing.** It fills the ledger's tables with
the numbers the standard produces and corrects a claim I made to the principal.

---

## 0. The headline, and the correction

**The ledger opens with zero entries.** Every one of the six constructions with a committed
daily series fails C-a (net Sharpe > 0.5) at the instrument's minimum tradable size with the
declared $3 round trip.

| | active days | net Sharpe (SE) | gross Sharpe | hit | skew | σ/day | ann. net | worst day |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **K1** C1 overnight ES hold, 1 MES | 2,043 | **+0.37 (0.32)** | +0.63 | 52.5% | −0.27 | $184 (0.37%) | +$1,078 | −$1,344 |
| **K2** last-30 momentum NQ, 1 MNQ | 1,893 | **−0.01 (0.40)** | +0.66 | 46.6% | +0.54 | $68 | −$12 | −$507 |
| **K3** last-30 momentum ES, 1 MES | 1,894 | −0.29 (0.41) | +0.62 | 45.1% | +1.08 | $50 | −$230 | −$392 |
| **K4** last-30 momentum YM, 1 MYM | 1,875 | −1.12 (0.48) | +0.08 | 42.7% | +0.52 | $37 | −$657 | −$294 |
| **K5** C1 on S1 nights (subset of K1) | 177 | +0.36 (0.40) | | 55.4% | +1.91 | $64 | +$371 | −$639 |
| **K6** C1 on S2-exposure nights (subset of K1) | 204 | +0.39 (0.29) | | 52.5% | −1.21 | $48 | +$293 | −$630 |

**The correction.** On 2026-09-12 I told the principal that C1 and the NQ last-30 trade were
components at net Sharpe 0.62 and 0.42 with an equal-risk book of 0.91, and CLAUDE.md, the
memory and D466 §0 were written on those figures. They were computed in an ad-hoc shell line
in **basis points of notional at the FULL-SIZE cost** (1.1 bp per round trip = $17 on one ES;
$17 on one NQ). The standard I then pre-registered scores **dollars at minimum size with a
$3 round trip**, and on a $15k MES notional $3 is **2.0 bp** (2.9 bp in 2016, 1.4 bp in 2023),
1.8× the full-size line; on MNQ it is 1.85 bp. The reconciliation, K1 and K2:

| lens | K1 (C1) | K2 (NQ last-30) |
|---|---:|---:|
| gross, dollars at micro | +0.63 | +0.66 |
| gross, bp of notional | +0.77 | +0.68 |
| net, bp at full-size cost (**what I quoted**) | **+0.62** | **+0.42** |
| net, dollars at one full contract ($17) | +0.48 | +0.28 |
| net, bp at the micro cost (2 bp) | +0.50 | |
| **net, dollars at micro, $3 (the standard)** | **+0.37** | **−0.01** |
| net, vol-scaled to unit risk (the C4 sizing lens), micro | +0.49 | |

Two things move the number: the cost line (1.1 → 2.0 bp takes K1 from 0.62 to 0.50 in bp) and
the lens (dollars weight 2020–2023, when the index was 1.5–2× its 2016 level and C1's years were
+0.76, +1.15, −0.93, +0.98, more than bp does; K1 by year in net dollars: 2016 +0.24, 2017 +1.98,
2018 −0.81, 2019 +2.21, 2020 +0.76, 2021 +1.15, 2022 −0.93, 2023 +0.98). **Both are the
standard's choices and both are right for a $50k account that can only ever run micros: the
cost it pays is the micro cost and the P&L it is judged on is in dollars.** The figures I
quoted were the right sign and the wrong altitude of cost. The correction stands in the ledger.

**What the gross column says.** Three constructions have gross Sharpe 0.6–0.7 at micro size,
which is the signal a component is built from; **the $3 round trip is 41% of K1's gross mean
per night ($7.29 on a σ of $185) and 102% of K2's ($2.95 on $70).** The cost K1 could bear and
still clear C-a is **$1.48** per round trip; K2 $0.73; K3 $0.38. IBKR's micro line is
$0.25–0.85 commission plus ~$0.35 CME fee per side, so $3 is not conservative by much and
nothing below $2 is available to a retail account. **This is the cost-failure branch of
CLAUDE.md's first reporting group, not the signal-failure one**, and the fix for it is not a
better signal: it is a longer hold per round trip, or a larger notional per contract, and the
account's floor forbids the second.

## 1. Correlations and the admission order

```
      K1    K2    K3    K4    K5    K6
K1  1.00  0.04  0.02  0.00  0.35  0.26
K2  0.04  1.00  0.73  0.49 -0.05 -0.01
K3  0.02  0.73  1.00  0.75 -0.06 -0.03
K4  0.00  0.49  0.75  1.00 -0.04 -0.02
```

Order by Sharpe: K6 (+0.39, fails C-a and C-c with skew −1.21), K1 (+0.37, fails C-a), K5
(+0.36, fails C-a), K2, K3, K4. Nothing enters, so C-b was never the binding condition; had K1
entered, K5 would have been refused on ρ = 0.35 and as a declared subset, and K6 on the subset
rule alone (ρ = 0.26 is under the bar — the subset rule, not the correlation, is what keeps a
gated C1 out, which is why the ledger carries it as a rule and not a number).

**The structure the layering idea rests on is confirmed:** the overnight hold and the last
half-hour on the same instrument are uncorrelated (ρ(K1, K3) = 0.02), and the three last-30
windows across ES/NQ/YM are one construction (ρ 0.49–0.75). The equal-risk book of K1 + K2 + K3,
reported because §3 declared it: net Sharpe **+0.03 (SE 0.38)**, unit weights +0.24, σ
0.11% of the account per day, worst day −0.70% (2020-02-28), max drawdown on closes −4.0%.
The layering arithmetic is correct and the components are not there at this cost.

## 2. Predictions

| | predicted | observed | |
|---|---|---|---|
| X-a K1 0.55–0.70; K2 0.35–0.50; K3 −0.05–+0.10; K4 < 0; K5/K6 0.35–0.55 | | 0.37; −0.01; −0.29; −1.12; 0.36/0.39 | **K1, K2, K3 wrong** (all by the cost line and the lens above); K4, K5, K6 right |
| X-b ρ(K1,K2) 0.05–0.15; ρ(K2,K3) 0.7–0.85; ρ(K1,K5), ρ(K1,K6) > 0.3 | | 0.04; 0.73; 0.35, 0.26 | ρ(K1,K2) just under; ρ(K2,K3) right; K5 right, **K6 wrong** (0.26) |
| X-c admits K1 and K2; book Sharpe 0.8–1.0 | | admits nothing | **wrong** |
| X-d book σ 0.5–0.7% | | no book | — |

Three of four wrong, all traceable to one act: I anchored the pre-registration on figures I
had not recomputed under the standard I was pre-registering. The predictions rule (memory
*predictions-must-be-checkable*) says each prediction is written in the runner's quantities
and computed from what the record already holds; X-a was computed in a different quantity.

## 3. What this changes in the plan D466 §5 declared

- **D467 (the extended data layer on eight roots) stands as declared.** The widening is the
  only way to find components whose gross edge per round trip is large relative to $3, and
  overnight holds on ZN/ZB/GC/CL/6E carry one round trip per night against notionals of
  $100k–$130k (ZN, ZB, 6E at full size have no micro; GC has MGC at $10/pt; CL has MCL at $100/pt
  and QM). **The cost as a fraction of σ per night is the screening number**, computed before any
  Sharpe: at micro ES it is 1.6% of σ, and a component needs gross mean/σ per night above ~3.2%
  plus that.
- **D468's book test has no components to assemble** until the ledger has entries; it runs
  when it does, unchanged.
- **The K1 finding is not filed as closed.** The gross edge is 0.63; a hold that spans two
  nights per round trip halves the cost per night and is a different construction from C1 (which
  D449 and D465 studied as one night, same contract, every night). Whether the overnight drift
  survives being held through the day session is a question C1's own tables answer directly
  (`d_end` on consecutive nights; the day session sits in between and D448 measured the
  T+0 future) — **declared here as a D469 question, not run.**
  **ADDENDUM (same day, before D468 was written):** withdrawn. The plan requires flat by the
  16:10 ET close (BOOK_PROP §C1: the 18:00 → 16:10 window is the rule's own shape), so a hold
  cannot span two sessions and no construction can amortise the round trip; the search is
  across instruments and within-session windows (D467, D468).

## 4. Corrections issued by this record

CLAUDE.md's *Two altitudes* paragraph, the memory *score-the-component-not-only-the-candidate*,
and the ledger's opening line are corrected in the same commit: the figures 0.62 / 0.42 / 0.91
were at full-size cost in bp; at the standard's cost and size they are 0.37 / −0.01 and no book.
The rule the paragraph carries (score both altitudes, every time) is unchanged and is, if
anything, better supported: the component line must be computed under the ledger's standard,
in the runner, not in a shell line, and the RESULT that omits it is incomplete.
