# D602 RESULT — **VOID on its own harness.** The covered-parity correction built from monthly-average 3-month rates does not remove the rate-differential component of FX basis momentum, it over-shoots it: the raw signal's pooled Spearman with the twelve-month change in the rate differential is **−0.514** (the bar, below −0.5, holds), and the corrected signal's is **+0.598** against a declared |ρ| < 0.3. The pre-registration said that outcome makes the trial void, not failed, and it is void: no verdict on basis momentum in FX is available from this construction. The cells are reported for the record and weigh nothing: the corrected cross-sectional book +0.06 gross (rank 0.88 in its rotation null), the raw book −0.04, and the corrected time-series form +0.48 (rank 0.996 in N1, above the family's N2 p95) — a signal 0.6-correlated with rate momentum, on a void trial. The FX 2024+ slice stays unread.

*2026-09-21. Pre-registration committed in the fixture-and-pre-registration sequence before this
runner (R8). **Runner** `scripts/run_d602_bm_fx.py`, artifact `data/d602_bm_fx.json`, 43 s.
Every audit passed its clean case and raised on its break inside the run: the CIP correction by
a pandas second path to 1e-12 (970 cells apart when the rate lag is removed); the construction's
exactness on synthetic parity settlements — BM_fx exactly zero while BM_raw is 1.6e-3, raising
at 3.2e-3 with the correction's sign flipped; the raw signal by D564's strip path on 300 cells
(raising on a negated grid); the leg membership by D557's second path on 604 cells (raising on a
swapped pair); the lag audit on 12,900 cells (raising on an unlagged book); right quantity (105
changes, raising on a daily grid); sign in money on the dollar book (4 roots, raising on the
negated and mis-lagged grids); the exactness guard on 20 offsets; the declared-outputs guard.
**Read:** the settlement strip for the six FX roots to 2023-12-29 (372,191 rows, 344,616 after
the quarterly restriction); the breadth fixture; the D601 OECD rates to 2023-12 with the one
filled cell (USD 2020-04) treated as present; D564's book for the correlation. **Not read:** any
session, settlement or rate from 2024-01-01 on.*

---

## 1. The harness, and why it failed

| statistic (pooled over 905 eligible root-months) | bar | observed |
|---|---|---|
| Spearman(BM_raw, Δ12 rate differential) | < −0.5 | **−0.514** — holds, at the bar |
| Spearman(BM_fx, Δ12 rate differential) | \|ρ\| < 0.3 | **+0.598** — **fails** |
| Spearman(BM_fx, BM_raw) | reported | +0.255 |
| BM_fx with the rate lag removed vs lag 1 | reported | +0.942 |
| USD 3-month series 2021-06 → 2023-12 | a step check | 0.09 % → 5.49 %, largest monthly step 0.64 %; no discontinuity at LIBOR's end |

The raw signal carries the rate differential's twelve-month change with the sign and roughly the
size the pre-registration derived (−0.51 against a predicted "< −0.5"). The correction removes
that and adds about twice as much of the opposite sign: the corrected signal is *more* a
rate-momentum signal than the raw one, with the sign flipped. The parity term as computed —
from the monthly-average 3-month interbank rate dated the month before, applied to 2–7-month
tenors — is not what the futures curve embeds. The curve prices the *expected* path of the two
policy rates over each contract's life; in a hiking or cutting cycle the 3-to-6-month slope of
that path is of the same order as the level difference, and the correction, which has only the
level, moves the signal by the level change while the curve had already moved by the expected
one. The pre-registration named this limitation ("BM_fx removes the spot-differential drift,
not expected-path changes") and declared the harness for exactly this case. **A construction
that would pass it needs the 3-to-6-month forward rates or an OIS curve for each currency,
daily and point-in-time, which is not on disk and not keyless.** That is a separate design if
anyone wants it; nothing here is tuned toward it.

## 2. The cells, for the record only (a void trial weighs nothing)

| cell (six roots, quarterly cycle, High2/Low2) | gross Sharpe · Sortino (SE) | net | N1 rank (p95) | LONG 2011–2023 |
|---|---|---|---|---|
| **BM_fx, EW High2/Low2** (the would-be primary) | +0.064 · +0.096 (0.36) | +0.052 | 0.880 (+0.142) | +0.008 |
| BM_raw, the paper's form on raw settlements | −0.042 · −0.063 (0.35) | −0.051 | 0.630 (+0.252) | −0.036 |
| BM_fx time-series form, 0.40/σ | **+0.483 · +0.729** (0.32) | +0.476 | **0.996** (+0.297) | +0.355 |
| N2 (primary, time-series) | best +0.483 | | p95 +0.316, rank 0.996 | |
| N3 name-randomised, the primary | | | rank 0.581 (p95 +0.524, SE 0.018) | |
| dollar High2/Low2 at minimum size (M6E, the others full) | −0.008 · −0.012 | **−0.029** at σ $851/day | | |

Eligibility: 6.00 roots at every month-end, no flat month-end, no boundary tie; 27,575 serial
rows dropped by the quarterly restriction; the D564 correlation of the published cell +0.011.
Predictions: P-1 fails (the primary inside N1), P-2 fails (the harness), P-3 VOID, P-4 holds
(eligible ≥ 5 on 100 % of month-ends), P-5 holds (PRIMARY +0.06 within 0.4 of LONG +0.01), P-6
holds (ρ +0.01 < 0.3).

**On the time-series cell.** It clears its rotation null and the family maximum on a signal that
is 0.6-correlated with the twelve-month change in the USD-minus-foreign rate differential, so
what it trades is closer to "long the currencies whose rate differential has been falling,
short those where it has risen" than to any curve imbalance. That is a rates-momentum book
wearing basis momentum's name, on a void trial, in sample, with N3 at 0.58 for the family's
primary; it is recorded so that nobody later reads it as a pass. Nothing follows from it.

## 3. What this record does not do

It does not read the FX 2024+ slice — the pre-registration reserved it for a passing primary and
there is none. It does not re-specify the correction, vary the lag, the tenor or the day count,
or try the per-contract basis with the FRBNY spot: any of those is a second pre-registration.
It does not run equity index. **Component line:** the dollar cell at minimum size is −0.029 net
at σ $851/day with ρ +0.01 to D564's commodity book — not a candidate, entered here for the
ledger's completeness only.

**Design amendment, recorded:** none; the runner is the pre-registration's.

**What the deposit's T2 now stands at.** The paper's finding that basis momentum is "present in
currencies" was to be the mechanism's cleanest test (§2.9: no storage, no producers). On the
six CME roots at the quarterly cycle the raw form is −0.04 in sample and the only construction
that clears a null is one that the harness shows to be rate momentum. Whether a properly
parity-adjusted signal exists in FX is not decided here, and cannot be from the rates on disk.
