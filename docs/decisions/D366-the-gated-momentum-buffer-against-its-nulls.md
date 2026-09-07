# D366 — the gated momentum buffer against its nulls: does anything survive an eighty-nine-construction search?

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). **OHLCV plus the sector-ETF and
declared-sector data pulled on 2026-09-07** — the holdout fixture is not read.
**Date:** 2026-09-07
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

**THE SELECTION HISTORY IS THE HEADLINE OF THIS RECORD, NOT A FOOTNOTE.** D365's cell came from an
eleven-combination screen. Since then this session has evaluated, on this same fixture, approximately **eighty-nine
further constructions**: 10 entry gates with two exit treatments, 11 stop/trail/time exits, 14 gate-and-exit
combinations across look-ahead and expanding thresholds, 24 circuit-breaker configurations, a 7-step structural
ladder, a 6-point hold-cap sweep, an 8-point exit-rank sweep, 4 hedge instruments and 5 dispersion thresholds.
**Not one of them has been run against a null.** This record exists to find out whether the endpoint of that search
is an effect or an artefact, and its load-bearing prediction is written so that it can fail.

---

## 0. Why

D365 established a broad, slow, hysteretic long on 12-month momentum: +2.59 bp/bar net PUB at a Sharpe of 0.417,
above every null, not size, not beta. Its weaknesses were named in its own result: era 1 paid nothing, thirteen
names were half the P&L, and the two-factor intercept's t was 1.74.

The session that followed attacked those weaknesses by search, and the search worked in the sense that the numbers
improved a great deal. **That is exactly when a null is owed.** The construction below is frozen as the search left
it, and nothing about it is adjusted again in this record.

## 1. The construction, frozen

```
  score      mom_252_21 -- the 252-bar return less the most recent 21 -- floored to the declared
             universe (keep_v2), deal-filtered (F0), lagged one bar, then ranked cross-sectionally
             among that day's eligible names

  GATE, all lagged; every condition a zero threshold or a standard window except the one noted
       1  NOT the crash state: the market's 20-bar volatility below its EXPANDING 80th percentile,
          or its 63-bar return not negative        [the one quantile; expanding, min 504 observations]
       2  index above its 200-bar mean
       3  index 63-bar return > 0
       4  the index's own 252-21 momentum > 0
       5  50-bar mean above the 200-bar mean
       6  index above its 50-bar mean
       7  index 21-bar return > 0
       8  breadth: more than half of eligible names above their own 200-bar mean
       9  index at a 252-bar high

  ENTER  not held, rank > 95, gate open
  HOLD   while rank > 90
  EXIT   rank <= 90, or ineligible, or a 252-bar cap on the holding period
  BOOK   long, equal-weight over whatever qualifies
  HEDGE  short the same eligible universe DOLLAR-VOLUME WEIGHTED -- the principal's choice, and the
         tradeable one; the equal-weight version every earlier number used is not a purchasable
         portfolio and is reported beside only for continuity
  FILL   next open, both legs (D340)
```

**A parameter that does nothing, recorded rather than quietly dropped:** the exit rank *while the gate is open* is
dead code, because the gate is shut on 90.8% of bars. Setting it to 85, 80, 75, 70, 60 or 50 produces byte-identical
results. It is written as 80 above for continuity with D365 and it is not a degree of freedom.

**Cost.** The long leg's own round trip per trade — its own half-spread at its own entry **and** exit bars plus
commission at its own as-traded price (D363's per-trade convention). The hedge charged explicitly: **borrow at
D337's general-collateral rate (50 bp a year)** on the short notional, plus rebalancing at the measured 2.37% of
notional a bar against a stated 1 bp half-spread. PUB primary, PB beside.

## 2. Nulls

- **ROT** — D348's rank rotation, all 24 shifts: the score's ranks shifted and the book rebuilt and re-run.
- **A′** — per-name time rotation of the score within each name's **eligible** bars (D351), the book rebuilt from
  the rotated score, 200 draws.
- **GATE-ROT** — *the null this record exists for*: the gate series circularly shifted in time, its on-share and
  run structure preserved, the trigger untouched, 200 draws. Almost the entire search was spent on the gate, so if
  a random gate of the same shape earns what this one earns, the search found nothing.
- **LADDER-MAX** — the 7-step structural ladder (G4 through S6) re-run under shared offsets, so the maximum of a
  searched ladder is priced rather than the endpoint alone.
- **C** — random direction on the per-bar contribution ledger, 1,000 draws.

## 3. Predictions

Q1 is load-bearing. Q7 is against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* net PUB bp/bar **> 0 and above the p95 of ROT, A′ and C**. |
| **Q2** | above the **p95 of GATE-ROT**: the gate beats a random gate of the same shape and share. |
| **Q3** | era 2's net is above the p95 of A′ restricted to era 2. **Era 1 is not predicted to clear anything** — D365 measured its premium at a third of era 2's — and a failure there is not counted against the construction. |
| **Q4** | **at least 15 names to half the P&L.** D365's ungated book managed 13 of 709. |
| **Q5** | the symmetric 1% trimmed mean per trade **exceeds the per-trade round trip**. |
| **Q6** | above the **p95 of LADDER-MAX**. |
| **Q7** | *(against)* **GATE-ROT's p50 net is above zero** — i.e. a randomly-timed gate still pays, and the trigger rather than the gate is doing the work. |
| **Q8** | the 252-bar cap's net Sharpe exceeds the uncapped version's under the frozen hedge. |
| *check* | the construction reproduces the search's figures under the dollar-volume hedge (net +8.10 bp/bar, Sharpe 0.887, max drawdown 3,024 bp, 988 trades, 24.5 names, 90.8% shut) to 1e-9 |

## 4. Stop conditions

These state the construction's status. **The avenue is the principal's (R15).**

- **Q1 and Q2 hold** → the construction survives its own search; the next step is its own out-of-sample design,
  a separate record, which does **not** touch D357's frozen read.
- **Q2 fails while Q1 holds** → the trigger is real and **the gate is a fitted ornament**. The record says so, and
  the honest fallback is D365's committed cell, which already cleared its nulls.
- **Q1 fails** → eighty-nine constructions produced a number that a rotation reproduces, and the search is the
  finding. That is a result and it gets written up as one.
- **Q6 fails while Q1 holds** → the endpoint is not distinguishable from the best of a searched ladder; report the
  ladder, not the endpoint.
- Nothing is promoted. Book: empty.

## 5. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[ID]** | the frozen construction reproduces §3's check figures to 1e-9 |
| **[GATE]** | each of the nine conditions equals an independent recomputation; the expanding quantile is causal — perturbing a **future** bar leaves every earlier threshold unchanged |
| **[HEDGE]** | the dollar-volume-weighted hedge equals an independent recomputation; the entry bar is open-to-close on **both** legs; the equal-weight version is reported beside and the difference stated |
| **[COST]** | the per-trade round trip, the hedge borrow and the rebalance each equal an independent recomputation; the one-leg round trip is asserted to be half G22's four-crossing figure |
| **[LAG]** | the held set at t is re-derived by a second implementation that never calls the selection loop; moving the raw score at t leaves rows ≤ t and moves t+1 |
| **[CAP]** | no trade exceeds 252 bars; the uncapped variant differs on exactly the trades that would have |
| **[ROT]** · **[A′]** · **[GATE-ROT]** · **[C]** | rotations keep counts and multisets; every rotated score stays within its name's eligible bars; GATE-ROT keeps the on-share exactly and the circular run-length multiset, and is never the observed gate; C's mean within 3 SE of zero |
| **[S]** | sign in money: +50 bp on one held name moves the book's bar by 50 / n_held and no other bar |
| **[6]** | [GATE], [HEDGE], [COST], [LAG], [CAP] and [S] each raise on a deliberately broken input |

## 6. Files

`docs/decisions/D366-the-gated-momentum-buffer-against-its-nulls.md` (this record) ·
`scripts/run_d366_gated_buffer.py` (stages `--selftest`, `--null ARM --draws N --part p`, `--report`) ·
`data/d366_null_*.json`, `data/d366_gated_buffer.json` (to follow). Reuses `scripts/d348_prep.py`,
`scripts/run_d365_momentum_buffer.py`, `scripts/run_d358_flat_sleeve.py`,
`scripts/run_d348_score_rotation_null.py`, `scripts/d365_export_trades.py`, `scripts/d322_four_group_report.py`.
The holdout fixture is not read.
