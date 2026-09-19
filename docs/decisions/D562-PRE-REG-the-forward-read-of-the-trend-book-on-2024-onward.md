# D562 — PRE-REGISTRATION: the forward read of D555's trend book on the reserved slice, **2024-01-02 → 2026-09-09**, on the principal's instruction to settle it

**Pre-registration. Committed before the runner exists and before any session from 2024 onward is
read by any trend runner (R8).** Result in a separate file. **This record spends the futures
fixtures' 2024+ slice for the trend line.** After it, no assembled book that contains this trend
book can be confirmed on that slice (CLAUDE.md, "two altitudes", item 3). Nothing is admitted by
this record (R15); it declares what each outcome qualifies trend for and leaves admission to the
principal.

*2026-09-19. D555 scored the published 12-month book at +0.30 gross on 2016–2023, inside its null.
D561 evaluated the three sharpenings and found none moves it, and named the forward read as the
only genuinely new data on this fixture. The principal's instruction was "settle the forward
slice". This is the declaration of that read: one construction, fixed since `5ed655b`, no
parameter chosen after 2023.*

---

## 0. What is read, and what is spent

The breadth fixture, the curve table and the settlement strip all run to **2026-09-09**; AQR's
*Time Series Momentum: Factors, Monthly* runs to **2026-05**. The forward window is every session
from **2024-01-02** to the fixture's last session. Signals at the first forward month-ends use
2023 returns as their lookback, as any live book would. The runner overrides D555's
`RESERVED_FROM` filter explicitly, logs that it has done so and why, and asserts that the
in-sample primary (2016–2023) still reproduces D555's +0.3037 on the extended fixture before any
forward number is computed — extending the data must not move the past.

**Spent by this read:** the 2024+ slice for D555's construction and every variant of it (D561's
capped books, D556's cell C which contains the 12m sign, any future trend book on these roots), and
for any assembled book that includes trend. **Not spent:** the same slice for lines that do not
contain trend (memory: holdout multiplicity is per line); D556 carry A is rebuilt here only as a
*base* for the overlay statistic, and its own forward Sharpe is reported as a diagnostic, which
does spend the slice for carry timing too — declared, because the tail-sharing finding of D561 is
the one worth replicating.

## 1. The construction — D555's, unchanged

MOP's 12-month sign, EW volatility (com 60), 40 % target, month-end holds, equal average over the
36 roots, the same live spans and placeholder-row handling. Cells:

| cell | role |
|---|---|
| **12m published** | **PRIMARY** — the forward gross Sharpe with its monthly block-bootstrap SE |
| 12m dollar at minimum size | the component line: C-a / C-c / C-d, $3/$6 + one tick, rolls as two sides, 34 roots |
| 12m published, CAP = 10 | D561's declared cap, diagnostic |
| D556 cell A carry, published | rebuilt in-process; a base for the overlay statistic and a diagnostic of its own |

## 2. Nulls

**N1-full (declared):** rotate each root's held-sign series within its **full** span (2011 →
2026-09) by a common offset, score the rotated book on the forward window only, **purge 252
sessions at both ends of the full cycle**. With k ≥ 252 every rotated sign at a forward session t
is a sign computed from returns that end at least 252 sessions before t, so it carries no
look-ahead, and there are about 3,500 surviving offsets — an exact null with SE 0. Its median is
expected to be positive, as D561 S1's was (the average in-sample sign is long bonds and equities),
and the record will say so beside the observed. **N1-window (diagnostic):** the same rotation
confined to the forward window itself, purged 252 both ends, ≈ 176 offsets. Sortino beside every
Sharpe (R17). N2 is not needed: one primary cell, the rest declared diagnostic.

## 3. Statistics and predictions — in the runner's quantities

The forward window is ≈ 680 sessions. A book whose true Sharpe is +0.35 has a sampling SE near
0.6 on it; the null's sd will be near 0.9. **No prediction here is sharp, and the record says so
before the fact.** The value of the read is the sign, the shape, the harness, and the two tail
findings of D561 replicating or not.

| # | prediction | value declared | reasoning |
|---|---|---|---|
| **P-1** (primary) | forward gross Sharpe of the 12m book **> 0**; point **+0.3**; interval −0.5 … +0.9 | | the in-sample excess over the null's tilt was +0.35 on both windows |
| **P-2** | inside N1-full's p05 … p95 | | on 2.7 years nothing of this size clears an exact rotation null |
| **P-3** | Sortino ≥ Sharpe if the Sharpe is positive | | the book earns in its large days |
| **P-4** (harness) | monthly ρ with AQR TSMOM over 2024-01 … 2026-05 **≥ 0.5** | | the harness held at 0.815 in sample; it should hold out of sample |
| **P-5** (convexity) | c5 on ES long-only, forward, **≤ 0**; point −0.1; interval −0.6 … +0.2 | | the forward slice's equity selloffs (August 2024, April 2025) were sharp V-shaped reversals, where a monthly-hold trend book is caught on the wrong side; D561's +0.26 σ came from 2020 and 2022, which were sustained |
| **P-6** (tail-sharing) | c5 on carry A, forward, **< 0**, and below N1-full's p20 | | D561: −0.56 σ below all 1,562 rotations; a structural feature, so it should replicate |
| **P-7** (vehicle) | dollar book daily σ **> $500** at minimum size | | palladium, heating oil and the full-size rates contracts; the vehicle fails C-d regardless of the edge |
| **P-8** (falsifiers) | forward Sharpe **below N1-full's p05** → the effect inverted on the forward slice; **above p95** → passes the programme's standard on the forward slice, the first time for any trend cell | | |

Reported beside them: net beside gross with turnover and breakeven; the root-month distribution
with symmetric trims; per-root and per-sector contribution and the top-3 share; per-year; the
worst and best days named; the overlay statistics (c5, c10, hit, DD ratio, ρ daily and monthly,
blend Sharpe and Sortino) against ES, 60/40 and carry A, each with its N1-full null; and the same
for the CAP = 10 book as a diagnostic.

## 4. The declared disposition rule

The read settles the trend line on this fixture. Declared now, before the number:

| outcome | disposition |
|---|---|
| **A** — P-1 holds and forward c5 on ES > 0 | trend is **an overlay candidate for the personal book only** (`BOOK.md`, not at capital; the vehicle fails C-d for prop at every size measured). The ledger note is updated to say the forward read supported both the return and the shape. |
| **B** — P-1 holds and c5 on ES ≤ 0 | trend is **a return-component candidate for the personal book only, and not a hedge**: sized by vol target, never relied on for the worst days. The ledger note says the shape did not replicate. |
| **C** — P-1 fails (forward gross ≤ 0) | the published trend book **did not deliver on the forward slice**. The record recommends the trend line on this fixture be closed; under R15 the closure itself is the principal's word. |

In every outcome: **the 2024+ slice is spent for the trend line and for any assembled book that
contains it**, recorded in PICKUP and in memory; nothing enters `BOOK_PROP.md`; nothing enters the
components ledger as a component (C-d).

## 5. Runner assertions

D555's three audits on the extended grid, each proven to raise. The in-sample reproduction
(+0.3037, and D556's −0.2035) to 1e-9 as a precondition. D561's worst-day audit (numpy against
pandas) on each forward base. The exactness guard on 20 offsets against the plain loop for the
N1-full rotation scored on the forward window. `REQUIRED_OUTPUTS` guarded;
`max_drawdown_convention` first; `encoding="utf-8"` on every text-IO call. The reserved-slice
override is logged as the first line of the run and stored in the json as `reserved_slice_read`
with this record's number and the principal's instruction.

## 6. What this record does not do

No new construction, no parameter, no sub-window chosen after seeing the forward numbers. No
re-read: the runner writes one artifact, and if it is re-run it must reproduce it. No admission.
No overlay on the ledger's live arm, whose daily P&L is still not on disk. Projected wall time
under two minutes.
