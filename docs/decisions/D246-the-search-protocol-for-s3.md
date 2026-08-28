# D246 — The search protocol for S3

**Status:** Pre-registered — the protocol is committed BEFORE any candidate is looked at
**Date:** 2026-08-28
**Area:** Strategy research

---

## Why a protocol record, before a single candidate

**Finding candidates has never been this programme's bottleneck. Validating them is.**

The hit rate is the argument: the short mirror, twelve-month momentum, both gradient diagonals,
the expansion cell and A2's stop all looked good in-sample and all died on a correct null or a
holdout. **Ideas are cheap here. Clean data is not**, and most of it is spent:

| | spent on |
|---|---|
| the 60-ETF instrument holdout | S1 (D237), then A0/A2/C (D242) |
| the 2013–2018 window | S1 and S2 (D243) |
| the 2025–26 forward window | S1 (D237), then S2 (D243) |
| crypto | both (D244) |

**So this record fixes the rules of the search before the search, and the single most important
one is where S3 will be validated.**

---

## The validation set, reserved now

**S3 is screened on the mined 57 and validated on [D245](D245-the-wide-universe.md)'s never-seen
cohort — the wide-universe symbols outside both the 57 and the 60.**

That cohort is **reserved for S3 from this moment** and may be used for **one** candidate. The
57 are already thoroughly spent, so screening there contaminates nothing further.

**If D245 shows the never-seen cohort behaves unlike the 57**, S3's validation is void and this
protocol restarts — a validation set has to be comparable to be a test.

---

## What S3 may not be

**Constraint 1 — not another bet on reversals beating continuations.**
[D239](D239-time-series-momentum-as-arm-two.md) established that S1 is the reversal arm and S2
the continuation arm, and [D243](D243-the-book-on-extended-history.md) confirmed it by showing
each fails in the other's era. **A third bet on the same axis is not a third arm; it is a
re-weighting of the first two.**

**Constraint 2 — not long-only directional equity.** S1 and S2 are both long-flat books on the
same universe. A third of the same shape inherits the same market factor and will correlate.

**Constraint 3 — no complement-chasing.** Three times now the interesting result has lived in
the complement of what was registered — S1 out of D234's failed cells, the exclusion reading out
of D238, the inverse anti-signal out of D239. **A candidate that is the complement or inverse of
a failed cell is not eligible under this protocol.** It may be registered separately, on its own
merits, with that provenance stated.

---

## What S3 should be

**A different return driver, where market direction cancels or is irrelevant.** The two families
that survive the constraints, both already flagged as live:

- **Cross-sectional, dollar-neutral.** Long the top of a ranking, short the bottom, matched
  notional. **Drift cancels exactly** — which is precisely what D238 proved kills a directional
  short on this universe. D238's signed scorer makes it computable; nothing before it could.
  **This family becomes far more viable on D245's universe**, where a decile is 25–50 names
  rather than 6.
- **Pairs.** `ZScorePairsStrategy` already exists with tests, and the universe holds natural
  candidates. Genuinely market-neutral. **The cost is that pair selection is a large free
  parameter**, and this protocol requires it to be fixed by a stated non-performance rule
  (cointegration over a training window, say) before any pair is scored.

---

## The rules of the search itself

- **Every candidate is declared before it is scored**, with its cells counted in the ledger.
  Post-hoc computation is permitted where it has been throughout — on the analyst's initiative,
  **disclosed, and counted** — and never presented as pre-registered.
- **A best-of-search null (D228) is mandatory** if more than one cell is screened. D240's stop
  cleared at the 99.6th percentile with no multiplicity correction and then failed out of sample
  at the 71.7th. **That must not happen twice.**
- **The correct null for the construction:** rotation for an entry rule, R7's matched-count
  overlay null for anything that modifies an existing book, and D244's lesson that a null can be
  beaten or lost **by drift structure alone** — so the conditional-return profile of the target
  universe is measured and reported *before* a null result is interpreted.
- **The bootstrap leg is never optional** (D230, R6). A point estimate that clears is not a
  result.
- **Screening stops at 8 cells.** If nothing has cleared by then, the family is closed and a
  different one is registered. **Committed here so "the last reading wasn't the right one"
  cannot be pulled later.**

---

## The bar S3 must clear

- **On the 57 (screen):** beat its matched-count null at p95, and clear `SR > ρ · SR_S2`, the
  D238 diversification condition, measured against **S2** — the entry that actually has
  out-of-sample support. **Not against S1**, whose own edge is unsupported outside its training
  era.
- **On the never-seen cohort (validation):** the same three hurdles D242 and D245 use — positive,
  beats buy-and-hold, clears its rotation null — plus a bootstrap interval, plus an
  anti-triviality floor at 25% of the screened delta.
- **Admission to `BOOK.md` requires the validation pass**, per R8. A screen pass alone earns
  nothing.

---

## Predictions about the search, not about a candidate

| | prediction | confidence |
|---|---|---|
| **S-a** | **No candidate clears both the screen and the validation.** Base rate in this programme is roughly one in eight | **moderate** |
| **S-b** | **Cross-sectional dollar-neutral screens better on D245's universe than it would on the 57**, because a decile stops being six lumpy sector funds | **moderate-high** |
| **S-c** | **If something clears, its correlation to S2 will be lower than its Sharpe is impressive** — the value of a third arm is diversification, and the honest case for it will be made on ρ, not on its own return | **moderate** |

**S-a is registered so a null result is a recorded outcome rather than a disappointment**, and so
the temptation to keep going past the 8-cell stop is priced in advance.

---

## Ledger

| count | N |
|---|---:|
| **fresh — 0.** This record is a protocol; it scores nothing | **0** |
| carried | **45,865** |

---

## Sequencing

**This protocol executes after D245**, because its validation set is defined by D245's cohort
split and because the cross-sectional family needs the breadth. **Nothing is screened until the
wide universe has been built and its never-seen cohort verified comparable.**
