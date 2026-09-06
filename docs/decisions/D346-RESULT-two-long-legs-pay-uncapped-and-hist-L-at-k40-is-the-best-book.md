# D346 RESULT — two long legs of 46 pay their cost uncapped, the corrections helped most legs and hurt the best ones, and `hist_L` at k=40 is the best book under every convention

**Status:** RESULT. Pre-registered at `0ef123b`, runner at `1ebbd05` — both before this
file existed (R8). `keep_v2`, F0, open fill, PUB primary; k=20 and k=40; multiplicity 46
per leg per k, 92 variant books in all — stated wherever a number from this table is
quoted.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted. Book: empty.**

---

## 1. The long legs, honestly scored

| PUB net per trade, invariant lens | k=20 | k=40 |
|---|--:|--:|
| long legs positive, of 46 | **2** — `hist_L` +30.9, `rev_21` +5.9 | **3** — `rev_21` +60.1, `hist_L` +43.7, `trailing_return` +29.7 |
| long-leg p50 / p95 / p05 | −46.9 / −6.2 / −117.2 | −44.8 / +21.8 / −121.5 |
| short legs positive, of 46 | **2** — `on_share` +20.7, `rsi` +3.8 | **1** — `on_share` +30.7 |
| short-leg p50 / p95 / p05 | −46.5 / −17.9 / −191.5 | −46.8 / −6.0 / −204.6 |
| median held as-traded price, long legs | **$38** (D335's top legs: $6–$28) | |

**Q1 confirmed** as written — fewer than three — and the stop condition's sentence "no
long leg pays its own cost uncapped" is **not** what the table says: two do at k=20 and
three at k=40. The record follows the table. **Q2 confirmed**: none of the three event
candidates' long legs is positive — `rsi` −11.1 on +46.1 gross, `retrace_leg` −23.1 on
+33.9, `rev_5` −19.6 on **+70.8** gross at a 45 bp half-spread (t = 3.0; the highest
gross of the three, and the most expensive names). **Q3, against, falsified**: at k=40
three long legs pay, and the two that paid at k=20 pay more — `rev_21` +5.9 → +60.1,
`hist_L` +30.9 → +43.7. The longer hold that hurt `rsi`'s invariant lens (D344) helps
these. **Q4 confirmed** on the short side: two at k=20, one at k=40; `on_share` is the
one short leg that pays at both holds.

## 2. What the corrections did to the table

**Q5 falsified, in the direction I did not expect: 29 of 46 long legs improved against
D335, median change +7.9 bp a trade.** The floor and the fill hurt the *best* legs and
helped the *rest*:

| long leg, PUB per trade | D335 (F0, close fill, no floor) | D346 k=20 (F0, `keep_v2`, open fill) |
|---|--:|--:|
| `id_mean` | +35 | **−67** |
| `rsi` | +64 | **−11** |
| `retrace_leg` | +46 | **−23** |
| `on_minus_id` | −58 | −155 |
| `rev_5` | −79 | **−20** |
| `dist_lvn` | −107 | −46 |
| `dist_52w_high` | −142 | −78 |
| `mom_252_21` | −283 | −119 |

The 95th percentile of long legs fell from +42.4 to −6.2 while the median rose from −57.8
to −46.9. **The two corrections compressed the table toward its middle**: the legs that
looked best were harvesting the sub-$5 tail and the overnight gap, and the legs that
looked worst were losing in the same tail. Remove it and the dispersion of "signal
quality" the programme has been ranking on since D290 shrinks by more than half. **Q7
confirmed**: the long legs now hold $38 names, not $6–$28.

## 3. The variant books

| PUB net bp/bar, slot-capped | k=20 | k=40 |
|---|--:|--:|
| positive, of 46 | **4** | **6** |
| best | **`rsi` +3.10** (Sharpe 0.159) | **`hist_L` +12.42** (Sharpe **0.401**) |
| next | `retrace_leg` +2.68 (0.142), `dollar_vol` +1.66, `rev_5` +1.20 | `id_mean` +9.61 (0.282), `dollar_vol` +8.47 (0.366), `rsi` +5.14 (0.268), `trailing_return` +4.16, `wick_asym` +1.34 |

**Q6, against, confirmed at k=20**: `rsi` is the best of 46 and only four are positive.
**At k=40 it is not**: `hist_L` symmetric nets **+12.42 bp/bar with a Sharpe of 0.40**,
two and a half times the candidate's, and `id_mean` and `dollar_vol` also beat it. `hist_L`
is the incumbent's primary signal — the one D338 called "a per-trade signal in names too
expensive to hold" at 69 bp a name in $11 stocks. Under the floor it holds $23 names (D339),
and at the longer hold its long leg is +43.7 a trade uncapped with the short leg
carried. **This is the maximum of 46 books at one of two holds, with no null, no top trade
named and no four groups.** It is a cell in a table, and FINDINGS §20 says what a cell in
a table is not. It gets a record before anything is built on it.

## 4. Predictions

| | | outcome |
|---|---|---|
| **Q1** | *(load-bearing)* < 3 of 46 long legs positive at k=20 | **CONFIRMED** — 2 |
| **Q2** | none of `rsi` / `retrace_leg` / `rev_5` positive | **CONFIRMED** |
| **Q3** | *(against)* < 3 positive at k=40 | **FALSIFIED** — 3 |
| **Q4** | < 3 short legs positive at k=20 | **CONFIRMED** — 2 |
| **Q5** | < 23 long legs improve vs D335 | **FALSIFIED** — 29 |
| **Q6** | *(against)* `rsi` best variant at k=20, < 5 positive | **CONFIRMED** — but `hist_L` is best at k=40 |
| **Q7** | median as-traded price of long legs > $20 | **CONFIRMED** — $38 |
| *check* | three identities | to 0.0 |

Five of seven.

## 5. Stop conditions, executed

- **Q1 holds** → the conditional-profile study starts from the table, not from the
  sentence I wrote for it: **`hist_L` and `rev_21` pay uncapped and the three event
  candidates do not.** The profile study's signals are re-chosen: `hist_L` and `rev_21`
  are the long signals to condition on `rsi` rank, and `rsi`'s own turn stays as the
  reference. `retrace_leg` and `rev_5` are out of it.
- **The Q1-fails branch applies in substance to `hist_L` and `rev_21`** even though Q1
  held: they are named here, and their top trades were not printed by this runner (it
  has no per-leg top-trade table). **Owed**: a candidate record for `hist_L` symmetric at
  k=40 under `keep_v2` and the open fill — the four groups, the top trade with as-traded
  price and dollar-volume percentile, a per-name signal-rotation null, GC+HTB — with the
  multiplicity of 92 stated. It is the best book under every convention the programme owns
  and has never been read as one.
- **Q6 first clause held at k=20** → no book beats `rsi` at the hold D335 used; at k=40
  three do, and the best is the incumbent's primary.

## 6. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | cache key; F0 counts; raw factor == census; `keep_v2` share == D343 |
| **[P]** | the pool is exactly D335's 46; the five dimensional scores excluded |
| **[1]** | `rsi` and `retrace_leg` at k=20 reproduce D343, `rsi` at k=40 reproduces D344, to **0.0** — variant net and Sharpe, invariant per trade, both conventions |
| **[C]** | per-leg `2c` is 2 × the held median half-spread on every costable leg of the 92 books |
| **[S]** | every `rsi` k=20 invariant trade equals the open-fill recomputation to 2.2e-16 |
| **[L]** | every book has both legs; three degenerate legs at each k (zero held PB half-spread) recorded, not dropped |
| **[6]** | raises on a leg handed free money |

**Speed:** 119 s for 92 books on both lenses.

## 7. What this establishes

1. **Two long legs in 46 pay their own cost uncapped under every convention the
   programme owns** — `hist_L` and `rev_21` — and three at the longer hold. The claim that
   none does is withdrawn before it was ever made a finding; the honest sentence is that
   the three signals proposed for the event book are not among them.
2. **The corrections compressed the table, not shifted it.** Twenty-nine legs improved,
   the best fell hardest, and the spread of long-leg quality the programme has ranked on
   since D290 halved. A ranking of signals measured on the unfloored, same-close universe
   was mostly a ranking of exposure to the tail.
3. **`hist_L` at k=40 is the best book in the programme by a wide margin**, +12.42 bp/bar
   and Sharpe 0.40 against the candidate's +5.14 and 0.27, on the incumbent's own primary
   signal. It is one cell of 92, unnulled, with no top trade named. It gets the next
   candidate record.
4. **The hold length is signal-specific.** k=40 hurt `rsi`'s invariant lens and helped
   `hist_L`'s and `rev_21`'s. D344's finding was about `rsi`.

## 8. Files

`data/d346_legs_floor_open.json` · `scripts/run_d346_legs_floor_open.py` · prior:
`data/d335_legs_under_filter.json`
