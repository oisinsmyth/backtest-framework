# D355 RESULT — in the slot book the target fires first: the invalidation exit lengthens the hold, cuts gross on both cells, and the target stays

**Status:** RESULT. Pre-registered at `c4cea84`, simulator edit and runner at `31e7e2f` — both
before this file existed (R8). `keep_v2`, F0, next-open fill, depth 2, k=40, PUB primary, PB
beside, GC/HTB.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted. The candidate construction keeps D303's target exit.**

---

## 1. The verdict

**Zero of seven, and the load-bearing one failed on both cells.** The invalidation exit —
leave when the name's lagged floored percentile crosses back through the median — earns
less than the target on both candidate books, and the `both` arm earns less still.

| PUB net bp/bar | target (published) | invalidation | both |
|---|--:|--:|--:|
| `rsi` k=40 | **+5.14** | +0.54 | +2.04 |
| `hist_L` k=40 | **+12.42** | +10.34 | −7.75 |

| `rsi` k=40 | target | invalidation | both |
|---|--:|--:|--:|
| gross bp/bar | 12.70 | 4.76 | 10.40 |
| PUB cost bp/bar | 7.56 | 4.22 | 8.36 |
| entries / hold (bars) | 847 / 15.0 | 474 / 27.0 | 905 / 14.1 |
| long leg bp per trade / per bar held | +39.0 / 2.55 | +61.7 / 2.28 | +50.7 / 3.54 |
| PUB net Sharpe | 0.268 | 0.030 | 0.093 |

| `hist_L` k=40 | target | invalidation | both |
|---|--:|--:|--:|
| gross bp/bar | 26.73 | 21.86 | 9.92 |
| PUB cost bp/bar | 14.31 | 11.52 | 17.67 |
| entries / hold (bars) | 771 / 16.5 | 657 / 19.4 | 999 / 12.7 |
| long leg bp per trade / per bar held | +141.5 / 8.49 | +223.9 / 10.92 | +129.4 / 10.32 |
| short leg bp per trade | +32.6 | +1.0 | +35.0 |
| PUB net Sharpe | 0.401 | 0.317 | −0.231 |

## 2. Why the event lens and the slot book disagree

On the event lens (D345, D353) the invalidation exit beat the cap because there was no
target: the cap sat through thirty bars after the reversal had paid. **In the slot book the
target is already the faster exit.** D303's rule fires when the summed excess reaches 0.96 of
the name's vol — on the first move, at a median hold of 15 bars on `rsi` — and the slot
refills. The median crossing comes later: 27 bars on `rsi`, 19 on `hist_L`. So the swap does
not shorten the hold; it lengthens it, halves the entries, and holds the position through
the part of the path the target would have banked. The long leg's mean per trade rises
(+39 to +62; +141 to +224) because each trade is longer, and its mean per bar held falls —
the opposite of Q5, which was written on the event lens's arithmetic.

**The `both` arm says the same thing from the other side.** Exiting on whichever fires first
gives the shortest holds (12.7 bars on `hist_L`) and the most entries (999), and on `hist_L`
the cost of that churn — 17.7 bp/bar — exceeds its 9.9 of gross. Q7 predicted `both` between
the other two; on `hist_L` it is below both.

**The exit is not a free lever on the slot book.** Under the target the entries are the
refills, and every exit rule that fires later than the target only delays a refill the
book wanted; every rule that fires earlier adds a round trip. D295's closure — exits are
inert on a refilled book — is amended by D345 for the event book and reinstated here for
the slot book, with the mechanism named: the target is the exit that matches the refill.

## 3. The nulls

The target arm reproduces D348: above all 200 time rotations and all 24 rank rotations on
every P&L statistic, both cells. The invalidation arm on `hist_L` is above both nulls' p95 on
PUB net (+10.34 vs A′ +3.03, rank +1.81) — a real book, worse than the target. The
invalidation arm on `rsi` is above A′'s p95 by 0.5 bp and **inside the rank rotation** (+0.54
vs p95 +5.62, 15 of 24): on `rsi` the swap takes the candidate from clearing both nulls to
clearing one.

## 4. Predictions

| | | outcome |
|---|---|---|
| **Q1** | *(load-bearing)* invalidation PUB net > target's on both cells | **FALSIFIED** — +0.54 vs +5.14; +10.34 vs +12.42 |
| **Q2** | invalidation above both nulls on both cells | **FALSIFIED** — `rsi` inside the rank rotation |
| **Q3** | entries at least double | **FALSIFIED** — 0.56× and 0.85× |
| **Q4** | gross rises by more than cost rises | **FALSIFIED** — both fall; and as written Q4 restates Q1 (cost = gross − net) |
| **Q5** | long leg per trade falls, per bar held rises | **FALSIFIED** — the reverse on both cells |
| **Q6** | *(against)* PUB net Sharpe rises | **FALSIFIED** — falls on both |
| **Q7** | `both` sits between | **FALSIFIED** — below both on `hist_L` |
| *check* | target == D346 to 0.0; the two implementations of the exit agree | held — 0.0 on both cells; 3,537 and 2,334 trades bit-identical |

Zero of seven.

## 5. Stop conditions, executed

- **Q1 fails → the target stays.** D357 reads the declared construction (or the blend, D356);
  the invalidation exit is not carried anywhere.
- Nothing is promoted. Book: empty.

## 6. Deviations and what the run found

- **The identity between the two implementations of the exit holds on every ledger, count
  and entry, with one insertion-order difference traced and asserted rather than hidden.**
  The ranker masks `score[t−1]` with `base[t]`; the prep's lagged grid masks with
  `base[t−1]`. On bar 1000 and on 6–9 later name-bars per cell a gate member has an
  undefined percentile; the exit never reads those cells, but the kernel sorts NaN last
  while the gate sorts by rank, so two same-bar entrants swap insertion order on 3–4 (side,
  bar) pairs and the per-side mean moves by ≤ 8 ULP on five bars of `rsi`. The runner
  asserts the exact set of such bars, that every one is a base-switch bar, and that with
  only those keys repaired the identity is bit-for-bit including the book.
- **Q4 was a tautology as written** (cost is gross minus net, so "gross rises by more than
  cost rises" is Q1 restated); the runner prints both terms and the record says so.
- The percentile grid rebuild under the rotation cost 0.5 s a draw, not the 4 s the plan
  estimated; twelve stages ran at 1.5–2.0 s a draw, 12 processes, 10.4 GB total.
- The simulator's own gate cache (`temp/d306_cache`) rebuilt once because its key hashes the
  file's mtime; the shared prep did not.

## 7. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[ID0]** | the target arm == D346's two cells to 0.0 on 23 statistics; `invalidation=None` == the keyword absent; D348's stored observed blocks reproduced to 0.0 |
| **[IDX]** | slot simulator with `invalidation=PCT`, no target, invariant lens == D345's kernel `exit="invalidation"` fed `rank < 2`: ledger, counts, entries bit-identical on both cells; the insertion-order residual bounded and asserted (§6) |
| **[X0]** | the `both` arm's age ≤ the target's and ≤ the invalidation's on every matched entry, == the minimum on the triple intersection |
| **[PC]** | observed grid == cached `PCT` == an independent rebuild; rotated grids == rebuild on 3 draws |
| **[A]** · **[N]** · **[5]** | counts and multisets kept; offsets non-zero; vectorised == loop |
| **[L]** | gate audit on observed and rotated books; the exit re-derived from `(row, e0, side)` on 300 trades per arm and lens; the unlagged grid moves 222–239 of 300 |
| **[S]** | sign in money on the invalidation ledgers, both lenses, observed and rotated |
| **[6]** | [ID0] raises on a perturbed grid; [IDX] raises with the target left on; [L] raises on the unlagged score |
| **[P]** | every part's stored observed equals the re-simulated to 0.0 |

**Speed:** self-test 50 s; 1.5–2.0 s a draw; twelve 100-draw stages in parallel in about 4
minutes; report 141 s including six sets of 24 rank rotations.

## 8. What this establishes

1. **The target exit is the right exit for the slot book**, because it is the exit that
   matches the refill: it fires on the first move and hands the slot to the next name.
2. **A signal-invalidation exit lengthens the slot book's hold** and gives back gross on
   both candidate cells; it is a real book on `hist_L` and a weaker one on `rsi`.
3. **The event lens's exit finding does not transfer to the slot book**, for a stated
   mechanism. The two constructions disagree about exits the way they disagree about
   selection (D348, D352): neither speaks for the other.
4. **The slot simulator now has a signal exit**, additive and proven, for any later
   construction that has no target.

## 9. Files

`data/d355_ctrl_{rsi,hist_L}_40_{target,invalidation,both}_p{0,1}.json` (twelve) ·
`data/d355_exit_swap.json` · `scripts/run_d355_exit_swap.py` · `scripts/run_d306_width_exits.py`
(the keyword)
