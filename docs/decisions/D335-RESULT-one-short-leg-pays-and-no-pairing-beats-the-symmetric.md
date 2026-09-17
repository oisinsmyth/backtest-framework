# D335 RESULT — one short leg in 46 pays its cost, and no pairing beats the best symmetric book

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D335-RESULT-one-short-leg-pays-and-no-pairing-beats-the-symmetric-book.md`. The H1 above is the full title.*

**Status:** RESULT. Pre-registered at `54d8d82`, runner at `73b785d` — both before
this file existed (R8). Run on the D333-bounded panel and the D334-rebuilt score cache.
**Date:** 2026-09-05
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted.**

---

## 1. The short side of this programme is a cost failure, stated as a measurement

Every one of the 46 dimensionless signals, symmetric at depth 2 and k=20, with the
F0 deal windows removed from the score, path-invariant lens, per trade:

| | long legs (46) | short legs (46) |
|---|--:|--:|
| PUB net per trade, **p50** | −57.8 | **−132.9** |
| PUB net per trade, **p95** | +42.4 | **−13.3** |
| legs netting > 0 under PUB | 6 | **1** |

**Under the published spread convention, with takeover targets removed, one short
leg in forty-six pays its own cost** — `close_in_range`, at **+4.9 bp per trade**,
against a p95 of −13.3. Its gross is +72.7; the other 45 are mostly gross-positive and
net-negative. Under the old per-bar median six of the top ten shorts were positive.
**PUB alone converts the short side from a signal question into a cost question.**

Q4 — *at least one short leg nets > 0* — was the against-prediction and it is
confirmed by that one leg, thinly.

## 2. The long legs, and where `hist_L` really sits

| rank | long leg | trades | PUB gross | **PUB net** | t | held ½-spread | price | premium |
|--:|---|--:|--:|--:|--:|--:|--:|--:|
| 1 | **`rsi`** | 1,901 | +129.1 | **+63.9** | +3.49 | 32.6 | $22 | +14.6 |
| 2 | **`retrace_leg`** | 2,213 | +110.0 | **+46.2** | +3.36 | 31.9 | $28 | +13.4 |
| 3 | **`hist_L`** | 1,431 | +183.4 | **+44.8** | +2.90 | **69.3** | **$11** | +27.3 |
| 4 | `id_mean` | 1,390 | +220.1 | +35.1 | +2.69 | 92.5 | $6 | +33.0 |
| 5 | `rev_21` | 1,259 | +185.6 | +24.9 | +2.38 | 80.3 | $8 | +6.5 |

Q2 and Q3 confirmed: `hist_L` and `retrace_leg` are top-3. **But the per-trade
ranking and the book disagree.** `hist_L`'s long leg has the highest gross of the three
and the highest cost — 69 bp a name in $11 stocks — and every `hist_L` pairing below
lands at **≈ 0 bp/bar** under PUB. `rsi` is first per trade and its own symmetric
book is **−2.55 bp/bar**. The leg that wins per trade is not the leg that makes a book.

`skew_63`'s short leg ranks **16 of 46** (PUB net −61.4; gross −0.7). Q1 confirmed:
retired for cause.

## 3. The nine books, and the stop condition that fires

Top-3 long × top-3 short by PUB per-leg net, as leg-wise books, both lenses, F0:

| book | PUB net/trade | **PUB bp/bar** | PUB Sharpe | maxDD | PB bp/bar | held |
|---|--:|--:|--:|--:|--:|--:|
| `rsi` / `close_in_range` | +20.76 | +11.63 | +0.387 | 15,174 | +20.80 | 19.3 |
| `rsi` / `dist_lvn` | +23.61 | +9.16 | +0.312 | 15,605 | +16.13 | 12.5 |
| **`retrace_leg` / `close_in_range`** | +17.29 | **+14.80** | **+0.428** | **11,401** | +22.51 | 20.5 |
| `retrace_leg` / `dist_lvn` | +17.56 | +12.24 | +0.362 | 14,150 | +17.62 | 13.7 |
| `hist_L` / `close_in_range` | +13.55 | +0.19 | +0.005 | 24,336 | +16.36 | 18.4 |
| `hist_L` / `dist_lvn` | +10.77 | +0.14 | +0.004 | 25,239 | +12.04 | 11.6 |
| **`retrace_leg` symmetric, F0** | +10.02 | **+18.93** | **+0.546** | 13,829 | +23.43 | 13.9 |

**Q5 falsified.** Every pairing beats the symmetric `retrace_leg` book **per trade**
(+10.0 is the lowest of the nine); **none beats it per bar** (+18.93 against a best of
+14.80). The pre-registered stop condition for *Q4 confirms and Q5 fails*: **a
positive short leg exists, but pairing it with the best long leg does not beat the best
symmetric book; the leg-wise construction is a per-trade result without a book-level
one.**

The mechanism is the one FINDINGS §10 names and nothing here measures: the pairings
hold 19–22 names a bar against the symmetric book's 14, so a per-trade edge is spread
over more slots and the book earns less per bar. The two lenses disagree, and they are
never compared on the same statistic; the *book* is the one that trades.

## 4. Q6 — the rebuilt cache changed the three books by under half a basis point

| signal | PUB bp/bar, old → new cache | score cells changed |
|---|---|--:|
| `beta_63` | −39.96 → −40.16 | 1,222,296 |
| `ivol_21` | −4.61 → −4.61 | 521,962 |
| `signed_vol` | −3.98 → −3.52 | 86 |

Confirmed. Note the inversion: a third of `beta_63`'s cells moved for 0.2 bp/bar;
86 `signed_vol` cells moved for 0.45 — a rank-boundary effect, not a magnitude one.

## 5. Predictions

| | | outcome |
|---|---|---|
| **Q1** | `skew_63`'s short leg not top-3 under F0 + PUB | **CONFIRMED** — 16 of 46 |
| **Q2** | `hist_L`'s long leg top-3 | **CONFIRMED** — 3rd, +44.8 |
| **Q3** | `retrace_leg`'s long leg top-3 | **CONFIRMED** — 2nd, +46.2 |
| **Q4** | *(against)* some short leg nets > 0 | **CONFIRMED** — one: `close_in_range`, +4.9 |
| **Q5** | *(against)* best pairing beats `retrace_leg` symmetric per bar | **FALSIFIED** — +14.80 vs +18.93 |
| **Q6** | the three rebuilt signals move < 1 bp/bar | **CONFIRMED** — 0.21 / 0.00 / 0.45 |

Five of six, and the one miss is the stop condition that decides the study.

## 6. What this establishes

1. **On this fixture, under the published spread convention and with deal targets
   removed, the short side does not pay for itself.** One leg in 46 clears its cost, at
   +4.9 bp per trade. That is a cost finding about the universe, not a signal finding,
   and it is the first time it has been stated across every signal at once.
2. **The leg-wise construction is a per-trade result, not a book.** Pairing legs adds
   per-trade edge and subtracts per-bar edge through slot count. Until FINDINGS §10's
   opportunity cost is measured, the symmetric `retrace_leg` book stands.
3. **`retrace_leg` symmetric under F0 and PUB — +18.93 bp/bar, Sharpe +0.546 — is the
   best book in the programme**, and it is the third study in a row to leave it there
   while every rival fell away.
4. **`hist_L` is a per-trade signal in names too expensive to hold.** Third-best long
   leg per trade, zero as a book. The incumbent's primary has nothing left to stand on
   at book level.
5. **`rsi`'s long leg is the strongest per trade and its book is negative** — the same
   disagreement, and the same reason.

## 7. Assertions

| | |
|---|---|
| **[K]** | score cache is the D334 rebuild: key matches with `ragged_panel.py`, npz newer than the panel builder, pre-D333 npz present |
| **[F]** | F0 mask reproduces D331: 1,719 filings applied, 2.54% of live name-bars |
| **[1]** | unfiltered, PB, D329's four arms reproduce D333's new-panel cells to **0.0e+00** |
| **[L]** | all nine pairings' ledgers equal their parents' per side, both lenses |
| **[C]** | per-leg 2c is 2 × held median half-spread, on every leg of the 46 |
| **[6]** | raises on a leg handed free money |

**Speed:** 141 s (self-test 37 s). `on_share`'s short leg has a per-bar (PB) half-spread
of exactly zero — the D302 clamp — and is costable only under PUB; recorded in the
table rather than dropped.

## 8. Files

`data/d335_legs_under_filter.json` · `scripts/run_d335_legs_under_filter.py`
