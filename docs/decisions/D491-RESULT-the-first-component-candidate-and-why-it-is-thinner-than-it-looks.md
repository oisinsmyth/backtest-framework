# D491 — RESULT: the first component candidate, and why it is thinner than it looks

**2026-09-12.** Runner [`scripts/d491_conditional_hold.py`](../../scripts/d491_conditional_hold.py) ·
artifact [`data/d491_conditional_hold.json`](../../data/d491_conditional_hold.json) ·
pre-registration [D491 PRE-REG](D491-PRE-REG-the-conditional-hold-exit-when-the-signal-flips-with-a-minimum-hold-time.md),
committed before the runner existed and amended before it existed to make B2 co-primary.
Signal code imported from D484 unchanged.

---

## 1. It passes

| | |
|---|---|
| best cell | **NQ, B1 impulse MACD, minimum hold M = 3 hours**, day session, 1 MNQ, $3 + crossing |
| net annualised Sharpe | **+0.583** |
| null family-max (2,000 rotations, the machine re-run each time) | p50 **+0.057**, p95 **+0.511** (SE 0.018) |
| margin | **+4.0 SE** of the p95 |
| **C-a** > 0.5 | **✓ +0.583** |
| **C-c** ≥ −0.5 | **✓ −0.04** |
| **C-d** ≤ $500 | **✓ $185** |
| **verdict** | **SIGNAL: YES · COMPONENT CANDIDATE: YES** |

**This is the first construction in this line to clear a pre-registered family bar and all three
computable component conditions.** Roughly twenty-five records preceded it without one.

**And it is the first to produce a real P&L series at all.** D484, D486 and D488 compared an edge
in σ units to a cost in ticks; none of them ever simulated a trade. The conditional exit makes the
**trade count an output**, which is what allowed C-a, C-c and C-d to be computed directly.

## 2. And here is why it is thinner than that table makes it look

**(a) The margin is 0.20 of one Sharpe standard error.** 1,873 sessions is ~7.4 years, so the SE
of an annualised Sharpe is **≈ 0.367**. The observed +0.583 is **1.59 SE from zero**, and the
excess over the null's p95 is **+0.072 Sharpe = 0.20 SE**. The 4.0 SE in §1 is the precision of
the *p95 estimate*, not of the observation. **The bar is met; the observation would not survive
much perturbation.**

**(b) M = 3 is the lucky draw, not a finding.** NQ B1 across the minimum-hold grid:

    M=1  +0.493     M=2  +0.428     M=3  +0.583     M=5  +0.461     mean +0.491

**The mean across M is +0.491, which does NOT clear C-a.** The substance is "NQ + impulse MACD +
day session ≈ +0.49"; the +0.583 is the maximum over four settings whose spread (0.15) is well
inside one Sharpe SE. The family null does discount that selection — that is what it is for — but
the neighbourhood is what a replication would inherit.

**(c) The conditional exit barely operates, because the closure left it no room.** Trips per
session at the best cell: **1.17**, i.e. an extra round trip on **17% of sessions**. Every session
has one forced exit at 4pm, so on 83% of sessions the construction *is* a fixed day-session hold.
**The index roots' window is six hours** — that was §8's limitation 7 and it turns out to bind
hard. The conditional mechanism is not what is being measured here; it is a garnish on it.

**(d) The signal that won is the one the principal argued against, and both our mechanisms were
wrong.** V-c broke: pooled across cells **B2 (−0.17) beats B1 (−0.24)**, confirming the
principal's counter-hypothesis on the average — yet **the best single cell is B1**. And the
reason we both gave was wrong in direction: I said B1's zero state would buy extra *exits* and the
principal said the same; in fact **B1 trades LESS (1.17 trips) than B2 (1.36)**, because a zero
makes B1 decline to **enter**. The zero state suppresses entries, not adds exits.

## 3. Predictions

| | prediction | outcome | |
|---|---|---|---|
| **V-a** | conditional beats D488's best fixed-H cell | **HELD** | NQ +0.58 |
| **V-b** | trips fall steeply in M; Sharpe non-monotone with an interior maximum | **BROKEN** | trips 1.31→1.21, barely; Sharpe −0.23/−0.25/−0.25/−0.09, no interior peak |
| **V-c** | B1 beats B2 | **BROKEN** | the principal's counter-hypothesis confirmed on the mean |
| **V-d** | no cell clears the family bar | **BROKEN** | one did |
| **V-e** | C-d not binding | **HELD** | σ $96–213, all under $500 |

**V-b breaking is the most informative.** The minimum hold — the principal's second instruction —
**did almost nothing on the index roots**, because the closure's six-hour window leaves nearly no
scope for an early exit. The idea is untested rather than refuted: it needs a window where it can
act.

## 4. The non-index roots, still uncosted

Gross ticks per session, **no cost line**, because MGC/MCL/M6E are absent from
`data/futures_contract_specs.json`:

    GC  B1 M=1   +5.22 tk/session on 2.12 trips
    CL  B2 M=1   +7.65 tk/session on 2.60 trips
    ZB  B2 M=1   +0.90            on 2.57
    ZN  B2 M=8   +0.52            on 2.14

**6E is skipped entirely** — it has no entry in the specs at all, so not even a gross figure in
ticks is expressible, and no tick size was guessed.

**These roots trade about twice as often** (2.1–2.6 trips against the index roots' 1.2), because
they have the whole 23-hour session to work in — **which is exactly where the minimum hold would
have something to do.** Costing them is the single highest-value unblock left, and it needs a
verified CME fetch through the browser.

## 5. What this does and does not license

**It does not enter anything.** §5 of the pre-registration said nothing would be entered off this
runner, and nothing is.

**But it is worth saying plainly what the ledger's own rules now imply, because that is the
principal's call and not mine:** the cell clears **C-a, C-c and C-d**; **C-e** is satisfied (a
pre-registered record, the window, the cost line, the nulls); and **C-b is trivially satisfied
because the ledger is empty** — there is nothing to correlate against. **On the standard as
written, this is eligible to become the ledger's first entry.** Given §2's four caveats I would
not enter it on this evidence alone, and the ledger's own discipline says the sealed 2024+ slice
is what promotes or removes a candidate.

**2024+ remains unread.**

## 6. Checks

19 self-test checks on the state machine, which is the whole runner. The machine is verified
against hand-computable cases: a permanently-long signal on a rising tape gives exactly one round
trip from entry to the forced exit (+20.50 ticks); cost is charged **once per round trip**; an
alternating signal **churns at 21 trips at M=1 and is suppressed to 3 at M=8**, which is the
minimum hold's entire purpose demonstrated rather than asserted; a short on a rising tape loses
**exactly** what a long gains (sign audit in money); and a zero signal **closes** a position and
does not re-open.

**The no-look-ahead check is a PAIR, and it had to be rebuilt.** The first version spiked the
open of segment 21 against a never-flipping signal — which never executes there, because it exits
at the forced close, so the check could not distinguish anything. With a signal that flips at
t=20, spiking **open-21 moves P&L from +19.50 to +1977.50** while spiking **close-20 changes it by
nothing**. That pair is what proves execution uses the next open and never the close the decision
was made on.

Scoring is checked too: a zero-mean series reads Sharpe 0, a constant series reads NaN rather
than a number, the Sharpe identity is verified against `mean/sd × √252`, and a left-skewed series
reads strongly negative so C-c has teeth.

**One crash fixed mid-run:** 6E has no `tick_points` in the committed specs, so the gross-ticks
loop divided by `None`. It is now skipped explicitly and recorded as skipped, rather than being
converted through a guessed tick size.

## 7. Where I would go next

1. **Cost GC and CL.** They trade twice as often, have the whole session to work in, and carry
   D484's two largest edges. Needs an MGC/MCL/M6E fetch from CME through the browser — plain HTTP
   403s, per the specs file's own provenance.
2. **Give the minimum hold room to act.** V-b is untested, not refuted. The non-index roots are
   where it can be tested, which makes (1) a precondition.
3. **Do not tune M.** The spread across M is inside one Sharpe SE; picking the best M is picking
   noise, and the mean across M (+0.491) is the honest level.
