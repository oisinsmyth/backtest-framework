# D354 RESULT — the basket of the ranking's opposite extreme costs the pair most of what the trigger earns, and a random gate name hedges as well

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D354-RESULT-the-basket-of-the-opposite-extreme-costs-the-pair-what-the-trigger-earns.md`. The H1 above is the full title.*

**Status:** RESULT. Pre-registered at `4c0ec69`, kernel and runner at `6e036fa`, the long-arm
data at `cd9dc24`, the short-arm addendum in the pre-registration — all before this file
existed (R8). Long arm only: D352 found no short trigger.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is a book. The pair book as designed is closed on this construction.**

---

## 1. The verdict

**Two of seven; the load-bearing one falsified.** At two pairs the long arm — `rev_5`
entering the bottom decile, hedged with a short basket of the three highest-`rsi` names that
day — loses under both cost lines and sits inside both nulls. At four pairs it nets +5.9
bp/bar under PUB, above its trigger's time rotation, and **inside the random-partner null**:
a basket drawn at random from the same-day 25-name gate does as well as the three most
extreme names. The basket leg loses 107 to 181 bp per pair whichever names fill it.

| long arm, deployed base, bp/bar | pairs | skipped | gross | **net PUB** | net PB | vol | Sharpe PUB | per pair | trigger leg | basket leg |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **K=2, cap** | 159 | 98.3% | −1.4 | **−4.9** | −4.0 | 285 | −0.28 | −55 | +126 | **−181** |
| K=2, invalidation | 883 | 97.8% | +7.8 | −11.9 | −4.8 | 307 | −0.62 | +56 | +81 | −25 |
| K=4, cap | 318 | 96.7% | +9.6 | **+5.9** | +7.2 | 222 | +0.42 | +381 | +488 | **−107** |
| K=4, invalidation | 1,770 | 95.7% | +8.5 | −10.8 | −2.9 | 235 | −0.73 | +62 | +84 | −22 |

| nulls on PUB net bp/bar | N1 time rotation p50 / p95 | above | N2 random partner p50 / p95 | above | N3 per pair p95 |
|---|--:|---|--:|---|--:|
| K=2, cap (−4.9) | −1.1 / +5.7 | no (13th pct) | −5.5 / −3.3 | no (68th) | +321 |
| K=4, cap (+5.9) | −1.3 / +2.5 | **yes** (99th) | +4.7 / +6.0 | no (94th) | +232 |

100 draws each; N3 1,000.

## 2. What the hedge costs

The trigger leg alone earns +126 per pair at K=2 and +488 at K=4 — far above the +43 of
every event, because a cap of two or four on 72,677 events admits the most extreme crash
each day a slot is free (D353 §4), and at K=4 those bounce. **The basket leg gives most of
it back: −181 and −107 per pair.** Shorting the three highest-`rsi` names on the day a
five-day crash fires costs the pair what D349's corrected base rate said it would — the
top 2% by `rsi` earns +11 bp long over forty bars — and more, because the days on which
`rev_5` fires are days the market's leaders keep leading. **The pair is also more volatile
than the market-hedged trigger** (285 against 232 bp/bar at K=2): three names are not a
market, and Q4 fails.

**Q3 failed the way that matters.** The random-partner null is centred at −5.5 (K=2) and
+4.7 (K=4), within a basis point of the extreme basket. A partner drawn at random from the
(90, 100] gate is neither better nor worse than the three most extreme names: **the choice
of partner within the ranking's top gate carries no information.** The pre-registration
predicted the extreme would be the *worse* hedge and the (90, 98] band the better one; the
data says the whole top gate hedges alike, and all of it costs.

## 3. The cost line

Each leg pays its own round trip: the trigger 55 to 75 bp PUB, each basket name 52 bp at a
third weight, commission 5, borrow 0.2 bp/bar (8 bp per pair; HTB 0%). At K=2 the pair
nets negative under **both** conventions (Q5 falsified): the basket's drag is larger than
the spread's. At K=4 it nets positive under both on 318 pairs, inside the random-partner
null.

## 4. Predictions

| | | outcome |
|---|---|---|
| **Q1** | *(load-bearing)* K=2 cap above the p95 of both N1 and N2 on PUB net | **FALSIFIED** — −4.9 vs +5.7 / −3.3 |
| **Q2** | *(against)* the basket leg's own P&L is positive | **FALSIFIED** — −181 per pair; the extreme partner costs the pair, as predicted |
| **Q3** | N2 centred above the observed | **FALSIFIED** — −5.5 vs −4.9; the top gate hedges alike |
| **Q4** | the pair's vol below the market-hedged trigger's | **FALSIFIED** — 285 vs 232 |
| **Q5** | negative under PUB, positive under PB | **FALSIFIED** — negative under both |
| **Q6** | invalidation worse than cap | **CONFIRMED** — −11.9 vs −4.9 |
| **Q7** | pair per pair more than 10 below the trigger's hedged per trade | **CONFIRMED** — −55 vs +43 |
| *check* | [ID] the pair kernel with the basket absent == the event kernel with a zero market | held bit-identically, both sides, both exits, K = 2 and 4 |

Two of seven.

## 5. Stop conditions, executed

- **Q1 fails → the pair book is closed on this construction.** The trigger's own record
  (D353) stands on its lens.
- **Q3 fails → the "move the basket to the (90, 98] band" retry is not written**: the
  random-partner null says no band of the top gate hedges better than another.
- **The short arm did not run** (addendum): D352 found no short trigger.
- Nothing is promoted. Book: empty.

## 6. Deviations and what the run found

- **N3 was drawn iid**, as pre-registered and as every prior random-direction control was.
  The runner's first version drew antithetic sign pairs so that [C]'s mean was zero by
  construction; a self-test that cannot fail is worse than none, and it was reverted before
  any stage ran. The negative control (the check fails on the unflipped ledger) is kept.
- [ID]'s "basket zeroed" is implemented as the basket *absent* — no partners drawn, no
  held-name constraint — which is the only reading under which the identity is bit-exact.
- [HX] includes still-open pairs in the per-bar rebuild (stronger than "excluded, counted").
- The K-capped trigger leg (+126 / +488 per pair) is not the invariant signal (+43): the
  cap selects the most extreme events, which D353 §4 records. The comparison in Q7 is to
  the invariant mean as pre-registered.

## 7. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[ID]** | pair ledger with the basket absent == `simulate_event` with a zero market, both sides × both exits × K ∈ {2, 4}, 6,502 trades; counts, entries and skipped equal; deployed series within 1e-15 |
| **[L]** | 400 sampled entry bars (observed and rotated): the basket == a rebuild from the raw floored `rsi` at t−1 by one stable argsort; the unlagged rebuild differs on 386 |
| **[S]** | +50 bp on the trigger: +50.000 / −50.000; on one basket name: −16.667 / +16.667 |
| **[HX]** | deployed and total series == the ledger per bar to 1.7e-18; per-pair rebuild 0.0 |
| **[N1]** · **[N2]** | eligible, counts kept, == `rotate_signals` within `elig` on the same seed; every random partner in the same-day gate, not the trigger, not held, size 3 |
| **[C]** · **[SB]** · **[V]** | N3 iid mean +11 within 2 SE (11.5) and fails on the unflipped ledger; 200 short legs to 0.0; ≤ K open on every book |
| **[6]** | [ID], [S] and [N2] raise on their broken inputs |

**Speed:** self-test 7 s; 0.15–0.30 s a simulation; eight stages of 100 draws in under a
minute each, in parallel; report 2 s; peak working set under 700 MB.

## 8. What this establishes

1. **Hedging a long trigger with the ranking's short extreme costs more than it saves**: the
   basket loses 107 to 181 bp per pair, the pair is more volatile than a market hedge, and
   at two pairs the book loses under every cost line.
2. **No band of the `rsi` top gate hedges better than another**: a random partner from the
   gate does what the three most extreme do. The ranking chooses no hedge.
3. **The pair book has one side and it is the trigger.** The long signal's record (D353)
   stands; the pair construction adds cost, vol and a losing leg to it.
4. **The kernel and its nulls are in the tree**: the pair kernel reproduces the event
   kernel bit-identically with the basket absent, and the random-partner null is the
   membership-keeping control CLAUDE.md asks for. Any retry of a pair design starts there.

## 9. Files

`data/d354_long_k{2,4}_{cap,invalidation}_{N1,N2}_p0.json` · `data/d354_pair_book.json` ·
`scripts/d354_pair_book.py` · `scripts/run_d354_pair_book.py` · the pre-registration's addendum
