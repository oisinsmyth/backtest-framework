# D382 — the undercut-and-reclaim: does the RECLAIM carry information, or only the LEVEL?

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). **Nothing here is a
result.** No cell has been scored, no null has been run, no book is proposed.
**Date:** 2026-09-08 · **Area:** signal research · **personal track**

**No holdout testing. Holdout reads spent by this record: 0. Programme total: 1** (D371).
`us_shorts_daily_holdout2.csv.gz` is unspent and this record does not touch it; D357's short
candidate retains its prior claim.

**Number.** `D382` was free at the time of writing. A concurrent session is active on `master` and
took `D380` from this branch already; if `D382` collides at merge, renumber — nothing references
it yet.

**Build (R16).** Everything is computed on **today's panel: `load_ragged(..., dividend_bound=True)`**,
D333's default since 2026-09-05. No quantity is inherited from a pre-D333 record, so no
cross-build identity check is owed — and this sentence exists so that a later reader does not have
to work that out.

---

## 0. Why this record exists

**The two most independent axes this programme has measured have never been crossed.**

- **[D280](D280-the-forecast-precheck.md)**: sixteen OHLC-derivative terms carry **13.50–15.76
  effective inputs** — the intrabar axis is genuinely independent, and *as levels* it carries no
  predictive power.
- **[D268](D268-score-independence.md)**: nine price scores carry **2.87** effective inputs — the
  informative axis is largely one thing.

`scripts/ragged_structure_scores.py` computes both families **in the same file and they never
meet**: `retrace_leg` is a close-based position ratio and `choch_dist` a close-based log distance,
neither of which knows the bar's intrabar excursion; `upper_wick`, `lower_wick` and `wick_asym`
measure the excursion and have no idea where the level is.

**The undercut-and-reclaim is their product**, and it is a *two-part* condition that no
single-score percentile crossing can express — which is why D350's 138 long events and D352's 139
short events do not contain it.

---

## 1. The construction, frozen

All on the lagged, floored (`keep_v2`), deal-filtered (F0) eligible set, on bars after the hedge is
defined. Pivots from `research.structure.market_structure(bars, k=3)` — **`K = 3` is
`ragged_structure_scores.K`, taken and not chosen** — whose `StructureState` fields derive only
from bars at or before their own, with a pivot at `t−k` confirming at `t`.

**The level must be a real level, and both guards are `ragged_structure_scores`' own:**

- **fresh:** `t − last_low_index ≤ 252` (`FRESH_BARS`) — *a level older than a year is not a level*
- **a real leg:** `(last_high − last_low) > 0.5 × ATR` with both pivots fresh — the guard that
  stopped `retrace_leg` ranging over [−2295, +1207] on two-tick swings

**The event (LONG):**

```
low[t]   <  last_low        the level is taken out intrabar
close[t] >  last_low        and price closes back above it
```

**Entry: LONG at the next open** ([D340](D340-execution-lag-a-next-open-fill.md)), every event
taken, no slot cap, hedged against the floored universe's equal-weight return, truncated at
delisting. **Borrow:** none on the long; the hedge's borrow charged as D359 charged it.

**Exit:** cap ∈ {5, 10, 20, 40, 60} **reported in full and not picked** (R14's fourth amendment).
**Primary is cap 20**, declared now as the midpoint of the grid, before any number is seen.

**Direction declared LONG (gate 1h).** The mechanism is a **stop-run**: price takes out the
obvious level, finds no supply, and closes back inside. A result in the opposite direction is
reported **DIRECTION-INVERTED** and counts against the mechanism even if the number is good.

**The undercut DEPTH is not swept.** The primary event is *any* undercut — a parameter-free
definition. A depth profile (0.1, 0.25, 0.5 ATR) is **owed and explicitly NOT run here**, so this
record's multiplicity stays at the cap grid. Adding it later is a new look and is priced then.

**The short mirror** — `high[t] > last_high` and `close[t] < last_high` — is computed and
**reported as a mechanism check only, never as a candidate**, per FINDINGS §33 rule 1: *the short
side of this universe has no event trigger.* Confirming that rule is worth more than quietly
re-testing it.

---

## 2. Stage 0 — run first, read before any null, and it can stop the record

**Four things, and two of them can end it:**

1. **The exposure arithmetic, computed BEFORE it is predicted** (§38 rule 2): entries per bar ×
   hold = open positions. D358 measured a bottom-2% cross-sectional trigger at **5.2 entries a
   bar → 120 open positions at a 40-bar hold → 100% exposure**. **If this fires at a comparable
   rate it is not a flat-by-default sleeve either**, and the record says so rather than implying
   otherwise.
2. **THE POOL'S OWN DRIFT — §52's rule applied before the fact.** What does a name that undercuts
   a fresh pivot low earn over the horizon **regardless of whether it reclaims**? *Before crediting
   a selector, measure what a random member of the same pool on the same day earns.* This number
   is the one `B_r` is built to test against, and if the reclaimers and the whole pool earn the
   same thing the record stops at §2 with that finding.
3. **The split sizes** — reclaim vs no-reclaim counts per year. A control needs a population.
4. **The four groups, with the top trade NAMED and its bar printed** (D322: a concentration report
   is not finished until the top trade is named). Count, mean, **median**, win rate, payoff,
   holding run, skew, kurtosis; the 1% trim from **both** tails with all three means; names to half
   the P&L as a **share**; top-1/5/10 name share; profitable years; and the splits on
   dead-vs-alive, era and **price**.

**Stage 0 scores no cell and admits nothing.**

---

## 3. The nulls — and the third one is the reason this record exists

Every null's events must satisfy **the observed events' eligibility mask** (D351), asserted per
draw batch. Every reported p95 carries its **bootstrap SE**, and a margin within **2 SE** is
recorded **UNRESOLVED**, never passed (D369). **None of these is a finite group**, so C2b's
enumeration remedy does not apply and the SE must be carried — stated so its absence is a decision
rather than an oversight.

| | null | draws | asks |
|---|---|--:|---|
| **A′** | each name's events rotated in time within its **eligible** bars | 2,000 | is the *timing* real? |
| **B** | each event's name replaced by a random eligible name in the same `rsi` bucket that day | 1,000 | is it the *name*? |
| **B_r** | **the same-pivot population that undercut and closed BELOW** | 2,000 | **does the RECLAIM carry information, or only the LEVEL?** |
| **C** | random direction on the per-trade ledger | 2,000 | is it better than a coin? |

**`B_r` is load-bearing and it does not exist in the programme's control library.** A′, B and C
all ask whether *these names at these times* beat some re-drawn alternative. **None of them holds
the level fixed.** `B_r` draws from names at a *fresh pivot undercut on the same bar* whose close
finished **below** the level instead of above it — same pool, same day, same structure, opposite
outcome.

**If the book is not above `B_r`'s p95, the pattern is `choch_dist` re-expressed and the record
closes.** That is the single most likely way this produces a false positive, and it is the same
failure mode §52 found in the winners' dip: **a selector that is a rounding error on the pool it
selects from.**

---

## 4. The hurdles — each names its PARTNER (D289's sixth amendment)

| | hurdle | partner |
|---|---|---|
| **H1** | **Signal (R15).** Gross mean per trade > 0 and above the p95 of A′, B, **B_r** and C, against the **best-of-5 floor** over the cap grid | **H2** |
| **H2** | **Size (1c′).** Gross mean per trade ≥ **1.0×** the measured round trip, **beside the per-bar edge on the deployed base at the same hold**; a cell clearing the ratio while its per-bar edge falls versus a shorter cap is **HOLD-DRIVEN**, not clearing | **H1** |
| **H3** | **THE RECLAIM (new, and the record's reason).** Above `B_r`'s p95 by more than 2 SE | — *(stands alone by design)* |
| **H4** | **Breadth (H4′).** `names_to_half_share` ≥ the **p05 of A′** on this study's own draws | — |
| **H5** | **Capturability (1e).** Open-entry t ≥ 2.0 **and** retention ≥ 50% | each other |
| **H6** | **Cost, reported not gating.** Net PB and PUB; the held names' **measured** Corwin–Schultz half-spread; breakeven half-spread; turnover, holding run, dead share (1g) | — |
| **H7** | **Independence (1d′).** ρ to S1, S2 and the retired S6/C9 against the p95 of the pair distribution in this candidate's own pool — **and a paired difference of means on matched bars beside it**, because ρ is blind to level and failing 1d′ alone is a **REPLACEMENT** question, not a rejection | **the paired means test** |

**Both lenses, never on the same statistic** (FINDINGS §10): path-invariant per-trade and
path-variant deployed bp/bar, reported separately.

---

## 5. Predictions

Committed before the runner exists, in the runner's own quantities. **Q3 is load-bearing; Q1 and
Q6 are against.**

| | prediction |
|---|---|
| **Q1** | *(against)* **exposure ≥ 90%** on the primary cell — this is **not** a flat-by-default sleeve. D358's arithmetic on ~700 eligible names says a structural event fires many times a bar, and rarity in the cross-section cannot make flatness in time |
| **Q2** | the trade count is between **5,000 and 60,000** on the primary cell. A count outside that means the event definition is not what I think it is, and the record checks the definition before reading any P&L |
| **Q3** | *(load-bearing)* the book's gross mean per trade is **above `B_r`'s p95** — the reclaim carries information beyond the level |
| **Q4** | `mean > median > 0` on the primary cell, **at a stated cap** — the stop-run mechanism should produce many small wins rather than a lottery ledger. *(Read at a fixed hold: D373's segmentation diagnostic showed this chain is confounded with holding period across constructions.)* |
| **Q5** | the top trade is **≤ 10%** of the ledger. D371's was 30% and D366's GME 11.7% |
| **Q6** | *(against)* the **short mirror fails** its own controls, confirming FINDINGS §33 rule 1 rather than reopening it |
| **Q7** | H7's ρ to S1 and S2 is **below 0.3** — different universe, different construction |

---

## 6. The search cost, stated

**Multiplicity 5** — the cap grid — and H1 is measured against a **best-of-5 floor**, the maximum
over the five caps **within each draw**, as D367 and D373 built theirs.

**Under [R13](../RULES.md#r13), what carries.** D350's 138 and D352's 139 events **do not carry**:
this event is not expressible in that family (it is a two-part intrabar-plus-level condition and
that screen ranged over single-score percentile crossings), so it did not shape this search. **What
does carry is one look**: `docs/research/the-signal-hunt-part2.md` §4.4 named this candidate before
any of it was scored, and that record's eight-candidate enumeration is disclosed as the space this
was drawn from. **Disclosed, not summed into a floor no measurement could clear** (R13's corollary).

**In-sample looks are bookkeeping, not a bar** (R14's first amendment). This record spends no
holdout read.

---

## 7. Assertions the runner must carry

- **[L] Lag audit** — the held set re-derived from the event mask at `t−1` in a **second
  implementation that never calls the selection function**. ~93% of D279's apparent edge was this
  bug, and it entered one layer *above* the function everything was watching.
- **[PIV] The level is causal** — `last_low` at bar `t` derives only from bars ≤ `t−k`. Asserted by
  a second path: recompute the pivot from a panel truncated at `t` and require the same level. **A
  level that moves when the future is deleted is a look-ahead and must fail the run.**
- **[S] Sign audit, in money** — a favourable move pays **positively** on the long; +50 bp on one
  name moves exactly one trade by +50.000 and no other bar. A sign asserted in prose inverted D280.
- **[E]** every null event satisfies the observed events' eligibility mask (D351), per draw batch.
- **[Br]** `B_r` draws **only** from same-bar fresh-pivot undercuts that closed **below** the
  level, and **never** an observed event; pool membership asserted per draw, and the pool's size
  reported per bar.
- **[N]** each null's centre is reported against the pool's own base rate from §2; a null centred
  far from it fails the run rather than earning a mechanism.
- **[P]** the result JSON is **persisted before it is rendered** (D371 lost its evidence to a
  `KeyError` in a print loop).
- **[X]** the self-test **RAISES** on (a) the event's reclaim condition inverted, (b) a `B_r` draw
  taken from a bar with no undercut, and (c) a pivot level read one bar early. **A self-test that
  cannot fail is worse than none.**

---

## 8. What would make me abandon this

- **H3 fails — the book is inside `B_r`** → the level is the signal and the reclaim is decoration.
  **Record it and stop.** Do not sweep undercut depth looking for a version that clears: that is
  the search that produced D366's gate, which cleared 164 standard errors and then failed out of
  sample.
- **Stage 0's pool drift explains the whole per-trade mean** → §52's rule closes it before any null
  is run, and the record stops at §2.
- **The direction inverts** → DIRECTION-INVERTED, recorded as counting against the mechanism.
- **Any hurdle needs a holdout read to settle** → **do not spend it.**

---

**Status footer.** No runner exists. No cell has been scored. `docs/BOOK.md` holds S1 and S2,
neither at capital; `docs/BOOK_PROP.md` is empty. Nothing in this record is a result, and **only
the principal closes a research avenue (R15).**
