# D86 — DSR: stdlib normal functions, registry-fed N and V, and the checkpoint-recovery of the paper's example

**Status:** Committed
**Date:** 2026-07-14
**Category:** Validation & research integrity
**Source:** Implementation session (Step 12)

## Decision

`validation/dsr.py` implements Bailey & López de Prado (2014): PSR, the
expected-maximum-Sharpe threshold SR0 (Euler–Mascheroni formula), DSR = PSR(SR0).
Normal CDF/inverse from the stdlib (`math.erf`, `statistics.NormalDist.inv_cdf`) —
no scipy dependency for two functions; accuracy verified against the paper's four
decimal places. `deflated_sharpe_from_trials` pulls **N (trial count) and V[{SRn}]
(variance of the named Sharpe metric) from the TrialRegistry** — the D20/D21 gate's
"not typed in" made literal — and fails loudly on any trial missing the metric,
because silently skipping one would understate N.

**How the paper's worked example was recovered (the X-gate's reproduction target):**
the paper's PDF loses its equation glyphs under text extraction, so the example's
parameter values couldn't be read directly — and memory is not a reference. But the
PLAIN prose survives, and it contains two checkpoints: "after running only N = 46
independent trials... would have been 0.9505", and "if the strategy had exhibited
Normal returns... after N = 88 independent trials" (the 95% boundary). With the
prose-stated SR (annualized 2.5, 5y daily → T=1250) and remembered skew/kurt
(−3, 10), back-solving checkpoint 1 for the one unknown gives **V[{SRn}] =
0.002000** — a clean round number — and the *independent* checkpoint 2 (different N,
different distribution assumptions) lands on exactly 0.9505 with the same V. The
system is overdetermined: one parameter, two equations, both satisfied — confirming
V and the remembered moments simultaneously. Headline reproduction: N=100 → DSR =
0.9004 (the widely-cited result), SR0 annualized 1.789. All three checkpoints are
X-gate assertions, including the N=88/89 boundary bracket.

## Rationale

Reproducing a paper's example from values one merely remembers would be
self-deception wearing an X-test's clothes; the checkpoint back-solve anchors every
number to the paper's own printed text, with an overdetermination check standing in
for the unreadable equations. Registry-fed N is the entire point of having built the
TrialRegistry first (D20: "the one component that can't be retrofitted") — Step 12
is where that Step 1 investment pays off.
