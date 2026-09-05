# D345 — the event-driven book: flat by default, enter on a signal, exit on a condition

**Status:** PRE-REGISTERED. Committed **before the simulator and the runner exist** (R8).
Nothing here is a result. **This reopens Axis C** (STACK §1), closed after D310 and D317,
at the principal's decision: the construction changes from always-invested to
event-driven. The record says so here, once.
**Date:** 2026-09-06
**Area:** Construction · strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

Every D300-family book holds the two most extreme names per side at all times and
refills a slot the bar it empties. It has no flat state. D338 and D344 showed the
per-trade losses live in the weak second name and the forced refill; D295 closed the
exit work because, with `sel = rank < N_SLOTS`, a price exit beside a signal exit is
arithmetically inert — the slot refills either way. The principal's requirement: **out of
the market by default; enter when a signal fires; exit on a condition; carry no position
that has no reason to exist.** That construction makes exposure a result rather than a
constant and makes exits real decisions again. It also has one more free parameter than
the slot book, the entry threshold, and this record fixes how it is set before anything
is read.

## 1. The construction, declared

**Signal.** The floored (`keep_v2`), deal-filtered (F0) `rsi`, lagged one bar as every
score here is: the decision at bar t reads `rsi[t−1]`.

**Entry.** Long when `rsi[t−1] ≤ θ`; short when `rsi[t−1] ≥ 100 − θ`. A name already held
on that side is not re-entered. Filled at the **open** of t (D340).

**θ is calibrated on exposure and never on return.** Before any return is read, θ is
chosen on a one-point grid as the value at which the **fixed-hold** (k=40, no target)
event book has an **average of 2.0 concurrent positions per side** over the bars where
the signal is defined — the slot book's exposure, so the two constructions are
comparable. The calibration function receives no return array; the runner asserts it
cannot ([T]). θ is then frozen for every arm.

**Exit arms**, each with the delisting drop and a **40-bar cap** (D344's k):

| arm | rule |
|---|---|
| **A · target** | D303's rule: exit when the summed excess `cx ≥ 0.9627 · vx[t, row]` — the primary arm |
| **B · invalidation** | exit when the signal has reverted: long when `rsi[t−1] ≥ 50`, short when `rsi[t−1] ≤ 50` |
| **C · cap only** | hold to the cap |

**Sizing and the two lenses.**

- **Path-variant:** at most **N_MAX = 2** concurrent positions per side. When more
  signals fire than slots are free, the most extreme (lowest `rsi` for longs, highest for
  shorts) are taken; the rest are skipped, and a skipped signal is not queued. A fixed
  **unit of capital per position** on a base of **U = 4 units**; cash otherwise. Two
  return series are scored: **total capital** (Σ signed position returns / U, zero when
  flat — the book an account holds) and **deployed capital** (mean per side, long minus
  short, as the slot book scores — comparable to D344's cells). The two are never
  compared to each other on one statistic.
- **Path-invariant:** every signal is taken, no cap, no skip; scored **per trade** as
  every invariant lens here is.

**Costs.** PUB primary, PB beside; IBKR commission; GC+HTB borrow; D318's round trip per
crossing on the names held. Cost on total capital is `rt × entries / bars / U`.

**Null.** For each name, its entry-signal series is **circularly rotated in time within
its live bars** by a random offset, and the same simulator and exits run on the real
returns — a matched-count, matched-per-name-frequency null with a distinct book per draw
(fast_null's construction, applied to the signal). 200 draws on arm A, both lenses;
teeth on gross; the number of distinct draws stated.

## 2. The identity that makes the new kernel trustworthy

With the entry rule replaced by **"the name's rank at t is below 2 — the slot book's
depth"** and arm A with a 20-bar cap, the event simulator's **invariant** book must
reproduce D343's `rsi` v2 invariant ledger **bit-identically** — every `(row, e0, age,
side, pnl)`, and the per-side equal-weight series. The slot book's uncapped lens *is* an
event book whose signal is "ranked in the top two this bar" with no limit on how many
such positions are held at once (`simulate(slots=False)` lifts the cap on holdings, not
on the entry rank). If this identity fails, nothing else is read.

## 3. Predictions

Q1 is load-bearing. Q2 and Q8 are against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* the variant event book, arm A, PUB net Sharpe on **deployed** capital **> 0.268** (D344's k=40 slot book). No weak second name, no forced refill. |
| **Q2** | *(against)* its PUB net Sharpe on **total** capital is **below** 0.268 — idle cash costs Sharpe — and within 0.10 of it. |
| **Q3** | its mean P&L per trade exceeds the slot book's **+102 bp** (D344, k=40). |
| **Q4** | under arm A the average concurrent positions per side is **≤ 2.0** (the target shortens holds relative to the fixed-hold calibration) and the book is entirely **flat on > 10%** of signal-defined bars. |
| **Q5** | its total-capital maxDD is **below 8,423 bp** (D344, k=40). |
| **Q6** | *(the exit work reopens)* arm B beats arm A on deployed-capital PUB net Sharpe. |
| **Q7** | the invariant per-trade PUB net exceeds the slot book's invariant **−11.8** (D344, k=40): a threshold entry is a tighter cohort than rank 25. |
| **Q8** | *(against)* the invariant per-trade PUB net is **> 0**. |
| **Q9** | arm A variant gross Sharpe on deployed capital is above the rotation null's **p95** with p95 > 0. |
| **Q10** | θ calibrates inside **[15, 30]**. |
| *check* | the §2 identity holds to 0.0; the variant ledger is a subset of the invariant one. |

## 4. Stop conditions

- **Q1 fails** → the event construction does not beat the slot book on the capital it
  deploys; Axis C closes again with this record as the reason; the slot book at k=40
  stays the candidate cell.
- **Q1 and Q9 hold** → the event book becomes the construction for the candidate;
  STACK §0 and §1 are rewritten; D342's out-of-sample design is re-specified to it with
  the multiplicity stated (three exit arms and a calibrated θ, on top of D344's three).
- **Q6 holds** → D295's closure of the exit family is amended in writing: it was a
  property of the always-invested construction, not of exits.
- **Q10 fails** → θ landed outside the signal's conventional range; the calibration is
  reported and the cells run, but the record flags that "2 per side" is not a natural
  exposure for this signal.
- **The §2 identity fails** → nothing is read.
- **Nothing is promoted.** Book: empty.

## 5. Assertions — properties of code

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | cache key; F0 counts; raw factor and `keep_v2` share == D343 |
| **[ID]** | §2: gate-as-signal, arm A, cap 20, invariant lens reproduces D343's `rsi` v2 invariant ledger bit-identically — trades as a sorted set and the per-side series |
| **[T]** | the θ calibration receives no return array and raises if handed one; θ is chosen before any P&L exists |
| **[A]** | lag audit: on 200 sampled bars the invariant arm's entries at t equal the names with `rsi[t−1]` beyond θ (and not already held), rebuilt by a direct comparison on the raw floored score; the unlagged rebuild differs on most |
| **[S]** | every trade in every ledger equals `pnl_recomputed_fill` (open fill on the entry bar) to 1e-12; favourable paths pay positively |
| **[V]** | the variant ledger ⊆ the invariant ledger as `(row, e0, side)`; the variant never holds more than N_MAX per side; when it skips a signal, a more extreme one was held or taken that bar |
| **[X]** | exposure arithmetic: mean concurrent positions equals Σ`cnt`/bars; the total-capital series equals Σ signed position returns / U bar by bar; the deployed series equals mean per side |
| **[RQ]** | total-capital and deployed-capital series differ; the ledger is summed (compound accumulation on the same entries differs) |
| **[2]** | each ledger's contributions reconstruct the total-capital gross to < 1 bp up to the open tail |
| **[3]** · **[N]** · **[B]** · **[6]** | symmetric trim; the null moves the book and its distinct-draw count is stated; borrow reconciles; raises on free money |

## 6. Scope

**In:** `rsi` only; the three exit arms; N_MAX = 2, U = 4; both lenses; both conventions;
borrow; the null on arm A. **Out:** any other signal, threshold rule, N_MAX or cap; a
queued or delayed entry; intraday fills; the holdout.

## 7. Files

`docs/decisions/D345-the-event-driven-book.md` (this record) · `scripts/d345_event_book.py`
(the simulator), `scripts/run_d345_event_book.py`, `data/d345_event_book.json` (to follow).
