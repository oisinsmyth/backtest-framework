# D354 — the pair book: a trigger hedged with a basket of the ranking's opposite extreme

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D354-the-pair-book-a-trigger-hedged-with-a-basket-of-the-opposite-extreme.md`. The H1 above is the full title.*

**Status:** PRE-REGISTERED. Committed **before the kernel or runner exists** (R8). The long
arm is fully specified here; the short arm's trigger is D352's survivor and is named in a
committed addendum to this record before the short arm runs. Nothing here is a result.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

The principal's design: a ranking signal (`rsi`) ranks the universe; a long signal fires on a
name and the book goes long it and short the ranking's most extreme opposite name; a short
signal does the reverse. The programme now has a long trigger that beats every honest control
(`rev_5` entering the bottom decile, D350/D353) and a screen for the short one (D352). Three
records have shown that the *trigger* must not be selected by the ranking's own extreme; this
record uses the ranking only to choose the hedge. The principal chose the hedge as an
**equal-weight basket of the three most extreme opposite-rank names**, and to run now under
both cost conventions.

## 1. Construction

- **Ranking:** `rsi`, floored, F0-filtered, lagged; ranked by `rank_single` and gated by
  `gate_from(rankT, finT, keep = elig)` — the 25-name gate per side, most extreme first,
  known at the close of t−1.
- **Long arm:** on a `rev_5`/E1 trigger on name i at t, go **long i** and **short the
  equal-weight basket of the three highest-`rsi` eligible names** that day, skipping i and
  any name already held on either side; if fewer than three are available the pair is not
  opened and is counted.
- **Short arm:** D352's survivor triggers a **short on j** and a **long basket of the three
  lowest-`rsi`** names, same rules.
- **Exit:** the pair closes when its trigger's exit fires — cap 40 (primary) or invalidation
  (the trigger's percentile crosses 50). If the trigger delists the pair closes; if a basket
  name delists that leg closes at its last price and the basket continues equal-weight on the
  rest (counted).
- **Slot cap:** `n_max_pairs` per arm ∈ {2, 4}; most extreme trigger first; over-cap events
  dropped and counted.
- **Marks:** every leg earns the next-open fill on its entry bar and close-to-close after;
  pair return per bar = `sgn·(v_trigger − mean(v_basket))`. **No market term:** the pair is
  self-hedged. Series: deployed (mean over open pairs) and total (Σ / U = 4 pairs). Ledger per
  pair: `(row, e0, age, pnl, side, partners)`.
- **Cost:** each leg pays its own round trip at its own held median half-spread (trigger leg
  in full, each basket leg at one third), commission per crossing, GC/HTB borrow on every
  short leg; PUB primary, PB beside; breakeven half-spread. Gross and net bp/bar, Sharpe,
  max drawdown, exposure, mean pairs, skipped share; mean and median per pair.

## 2. The nulls — both keep the membership

| null | construction | what it removes |
|---|---|---|
| **N1 · time rotation of the trigger** | each name's trigger events rolled within its eligible bars (A′); partner rule unchanged; 100 draws | the trigger's timing |
| **N2 · the random partner** | the basket drawn at random, without replacement, from the same-day opposite-side 25-name gate instead of the three most extreme; 100 draws | the choice of the extreme as the hedge — CLAUDE.md: randomise the partner, not the membership |
| **N3 · random direction** | the pair ledger's signs randomised, 1,000 | the directional claim |

Statistics under every null: PUB net bp/bar and net Sharpe on the deployed series, gross
bp/bar, mean per pair; p50, p95, max, and the fraction of draws below the observed.

## 3. Predictions — the long arm

Q1 is load-bearing. Q2 is against the design and Q3 is its test.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* the long arm at `n_max_pairs = 2`, cap exit, is above the p95 of **both** N1 and N2 on PUB net bp/bar. |
| **Q2** | *(against)* the basket leg's own P&L — short the three highest-`rsi` names — is **positive**. D349's corrected base rate says the top 2% by `rsi` earns **+11 bp** long over forty bars; the extreme partner is predicted to **cost** the pair. |
| **Q3** | N2 is centred **above** the observed: a random partner from the (90, 100] gate — base rate −8 to −12 long — is a better hedge than the three most extreme names. |
| **Q4** | the pair's per-bar vol is **below** the market-hedged trigger's on the same trades (a tighter hedge). |
| **Q5** | nets **negative under PUB** and **positive under PB** at K=2, cap exit. |
| **Q6** | the invalidation exit is worse than the cap on net bp/bar. |
| **Q7** | the pair's mean per pair is **below** the trigger's market-hedged mean per trade (D353) by more than 10 bp — the price of hedging with the extreme. |
| *check* | with the basket zeroed the pair ledger equals the event kernel's trigger ledger with a zero market, at the same cap. |

The short arm's predictions are written in the addendum with its trigger.

## 4. Stop conditions

- **Q1 holds and Q3 holds** → the pair book is real and **mis-hedged at the extreme**; the
  next record moves the basket to the (90, 98] band of the ranking and is pre-registered on
  that construction.
- **Q1 holds and Q3 fails** → the principal's design stands as constructed; the book's
  candidate record follows with both cost lines, waiting on D336.
- **Q1 fails** → the pair book is closed on this construction; the trigger's own record
  (D353) stands on its lens.
- Nothing is promoted. Book: empty.

## 5. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[ID]** | with the basket's returns zeroed, the pair kernel's trigger ledger equals `simulate_event`'s with a zero market bit-identically at the same `n_max` |
| **[L]** | the basket is re-derived from `score[:, t−1]` by a second implementation that never calls `rank_single` or `gate_from`, on 200 sampled bars, observed and rotated; the unlagged rebuild differs |
| **[S]** | a +50 bp move on the trigger name lifts a long-trigger pair by +50.0 and cuts a short-trigger pair by 50.0; the same move on one basket name moves the pair by ∓16.7 |
| **[HX]** | the deployed series equals the ledger summed per bar to 1e-12 |
| **[N1]** | every rotated trigger is eligible; counts kept; no NaN |
| **[N2]** | every random partner is in the same-day opposite-side gate, is not the trigger, is not already held; basket size preserved |
| **[C]** | N3's mean within 2 standard errors of zero |
| **[SB]** | borrow on 200 short legs equals an independent recomputation |
| **[V]** | at most `n_max_pairs` open per arm; skipped counted |
| **[6]** | [ID] raises with the market term left in; [S] raises on a pair handed +50 bp; [N2] raises on a partner drawn from outside the gate |

## 6. Files

`docs/decisions/D354-the-pair-book-a-trigger-hedged-with-a-basket-of-the-opposite.md`
(this record; the short-arm addendum to follow) · `scripts/d354_pair_book.py` (the kernel) ·
`scripts/run_d354_pair_book.py` (stages `--selftest`, `--arm long|short --null N1|N2 --draws N
--part p`, `--report`) · `data/d354_*.json` (to follow). Reuses `scripts/d348_prep.py`,
`scripts/d345_event_book.py`, `scripts/run_d323_shortlist_at_operating_point.py`
(`rank_single`, `gate_from`), `scripts/run_d329_legwise.py`, `scripts/d322_four_group_report.py`,
`scripts/d337_borrow.py`.

---

## Addendum — the short arm, 2026-09-06 (committed before any short-arm stage; none runs)

D352's Q1 failed: no short event at the top 2%, 5% or 10% of any score, nor the `rsi` turn,
is above random direction under the kernel. By D352's stop condition and this record's
§0, **the short arm has no trigger and is not run.** The long arm's eight stages ran as
pre-registered before this addendum, from the committed runner; the result reports the long
arm only and records the short side as the ranking's own extreme or nothing.
