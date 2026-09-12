# D497 — hurdle P on the D495 candidate: **P3 fails**

**2026-09-12.** Runner [`scripts/d497_candidate_hurdle_p.py`](../../scripts/d497_candidate_hurdle_p.py) ·
artifact [`data/d497_candidate_hurdle_p.json`](../../data/d497_candidate_hurdle_p.json).

A **completion, not a study**. It re-runs the single D495 cell that clears C-a/C-c/C-d and
computes what [`COMPONENTS_PROP.md`](../COMPONENTS_PROP.md) and [R11](../RULES.md#r11) require of
it. No search, no new grid, no new signal. Cell: `{"root": "NQ", "arm": "AGREE", "M": 5}`.

---

## 1. Why it had to exist

**D491 and D495 both reported C-a, C-c and C-d and both stopped there.** P3 — worst single day
≤ 2% of the account — had never been computed on *any* cell in this programme. R11's
2026-09-12 restatement is explicit that the relaxations did not reach it:

> P1, P2, P3 and P6 stand exactly as written. In particular P3's worst-day ≤ 2% is untouched —
> it is a daily LOSS LIMIT, enforced by the venue on the day, and no amount of
> account-replaceability softens it.

D495 stored the **best** day, for P5's haircut, and not the worst.

## 2. Result

| | | |
|---|---|---|
| C-a | net Sharpe > 0.5 | **PASS** +0.723 |
| C-b | ρ < 0.3 | **PASS** — ledger is empty, trivially satisfied |
| C-c | skew ≥ −0.5 | **PASS** −0.053 |
| C-d | daily σ ≤ $500 | **PASS** $180 |
| C-e | provenance | **PASS** — D495 pre-reg, window, cost line, two nulls |
| **P1** | sizing rule | **PASS** — post-sizing return $2,071/yr |
| **P2** | flat across the flatten | **PASS** by construction — exit 16:00 ET inside a 16:10 flatten |
| **P3** | worst day ≤ $1,000 | **FAIL** — **worst −$1,315**, 2 of 1,873 sessions beyond |
| **P4** | E[profit] > fee | **PASS** — $1,455 before breach, E[life] 177 d (0.70 yr) |
| **P5** | 30% haircut | **PASS** — best day $1,031 = 6.7% of total → haircut $0 |
| **P6** | automation | **n/a** — Topstep or MFFU only; a venue choice, not a property of the cell |

The daily distribution: worst −$1,315, p0.1 −$915, p1 −$504, p5 −$252, median $0, p95 +$314,
p99 +$547, best +$1,031. **Twenty sessions beyond −$500.**

**So the construction clears every component condition and fails hurdle P.** That is exactly
what the ledger's separation of the two altitudes is for — and it is the first time the
separation has actually bitten.

## 3. The integrated reading, which is more informative than the binary

P3 is not really a screen on the strategy. **It is a second death mechanism alongside the
trailing drawdown.**

| mechanism | E[life] | hazard |
|---|---:|---:|
| trailing 4% drawdown (D496's barrier model) | 177 d | 0.00565/day |
| P3 daily-limit breach (2/1,873 empirical) | 936 d | 0.00107/day |
| **combined** | **149 d** | **0.00672/day** |

P3 shortens the account from **177 to 149 days — a 16% reduction — with a 15% chance of a breach
in any one life.** Whether P3 stays a hard gate or becomes another hazard term is the
principal's call; P4 and P5 were relaxed on closely related grounds. **As written, it fails, and
this record says so.**

## 4. And it identifies what the stop is for

The principal raised trailing stops earlier and I assessed them on *performance*. **P3 is the
actual motivation.** A same-day loss stop caps the worst day **by construction**, which is the
only thing that can fix this: size cannot go below one micro, and D496 §1 showed that shrinking
size would *help* expected profit if it were available.

The design constraint is already measured: D471 §5 and D472 put `adverse/|move| ≈ 0.48–0.50`, so
a stop that does not destroy the edge must be **wide** — and at one MNQ a wide stop may not fit
under $1,000 at all. That is the question, not an assumption.

## 5. Checks

P3 is proven to read a **different statistic** from P5 (worst vs best day). A series is
constructed that **breaches P3 while remaining profitable overall**, so the two are proven
independent. And **C-c (skew) is proven not to bound the worst day** — a near-symmetric series
with skew +0.07 still breached — so skew is not a substitute for P3, which matters because C-c
was the only tail condition in the component standard.

One arithmetic slip fixed before the run: my first "breaches while profitable" example
(`[500, −1200, 300, −100]`) sums to −$500 and so could not demonstrate the thing it asserted.

## 6. What this does not do

- **It admits nothing** ([R15](../RULES.md#r15)). Nothing enters `COMPONENTS_PROP.md`, the vault
  or either book.
- It does not change P3. Relaxing a hurdle is the principal's authority, not mine.
- Every D495 limitation carries: in-sample only, 2024+ sealed, open-of-next-segment fills at
  the measured half-spread, no queue and no partial fills. **The worst day is an order
  statistic, so it is the figure most exposed to fill optimism** — a real fill on a gap day is
  worse, never better, so −$1,315 is itself an upper bound on the P&L and a lower bound on
  the breach.
