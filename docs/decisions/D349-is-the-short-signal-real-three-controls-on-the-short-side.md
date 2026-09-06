# D349 — is the short signal real? D347's three controls on the short side, with borrow

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). Nothing here is a
result. Nothing here is a book: the output is which short signal, if any, has timing that
survives every control, and whether it pays after the spread and the borrow.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

D347 tested long signals and found no timing in any of them. It scored the short *mirrors*
of those long signals — all four lose — but never the programme's own short signals, the
ones the record says own or pay the short leg. The short side is where this programme's
skill has historically lived (D238: "the short signal has real skill and cannot be traded";
D329: `skew_63` owns the short leg; D346: `on_share` is the only short leg that pays at both
holds under the floor and the open fill). If the pair book the principal wants is to have a
trigger, and the long side cannot supply one, the short side is the remaining place to
look. This record measures five short signals against the same three drift-matched controls,
with the borrow the short leg actually pays.

## 1. The signals, as short events

All scores floored (`keep_v2`), deal-filtered (F0), on the warm base, lagged one bar; the
event day t is the fill day. `pct[t, i]` is the score's cross-sectional percentile among
floored live names at t−1 (average rank on ties, as D347). The leg the slot book shorts is the
**top** of the score, so the event is a fresh entry into the top decile.

| signal | short event at t | why it is here |
|---|---|---|
| **`on_share`** | `pct` enters the top decile: `pct[t] ≥ 90` and `pct[t−1] < 90` | the only short leg paying at both holds under floor + open fill (D346: +20.7 / +30.7 a trade) |
| **`skew_63`** | same | owned the short leg, specifically (D329) |
| **`close_in_range`** | same | the one short leg of 46 that paid under F0 + PUB (D335) |
| **`rsi` decile** *(reference)* | same | the ranking's own short side (D346: +3.8 at k=20) |
| **`rsi` turn** *(reference)* | `rsi[t−1] < 70` and `rsi[t−2] ≥ 70` — the cross back down | the conventional short turn |

Every event is entered at the next open. Two exits, both reported: **cap** — a fixed 40-bar
hold, the exit every control uses; and **invalidation** — `pct` crosses 50 (or `rsi` crosses
50 for the turn). Every event is taken (the invariant lens, per trade, never bp/bar).

## 2. The hedge, and the borrow

P&L per trade is `−Σ (v − m)` with **m the floored universe's own equal-weight return**;
beta-adjusted `−Σ (v − β·m)` beside it, β the name's trailing-63-bar OLS slope, lagged,
fixed at entry. **Cost** per trade: the PUB round trip (2 × the held median published
half-spread), commission, **and the borrow** at D337's rates — GC 50 bp/yr, HTB 500 when the
name is in an F0 window at entry or its as-traded close is below $5 — charged per bar held,
by `d337_borrow.borrow_per_trade_bp`. Net is reported with and without the borrow.

## 3. The three controls

| control | construction | what it removes |
|---|---|---|
| **A · per-name time rotation** | each name's short-event series rolled by a random offset within its priced bars, confined to bars where the hedge is defined (D347's `rotate_confined`) | timing: same names, same count, same holding |
| **B · same-date, same-cohort name** | each event's name replaced by a random floored live name in the same `rsi`-rank bucket that day, distinct per day and bucket | name selection within the cohort |
| **C · tail-randomised direction** | the same trades, each signed at random | the directional claim |

100 draws for A and B (full simulations), 1,000 for C. The statistic under every control is
the **mean per-trade hedged excess, cap exit**. **A signal is real only above the p95 of all
three.** Separately reported, because for a short they differ: **the timing value**
`observed − A's p50`, and **pays**: net > 0 after PUB and borrow. D347's base rates say the
high-`rsi` cohort earns −8 to −31 bp long over forty bars, so a short's control A will not
be centred at zero: a short signal can clear A and still lose, or pay and fail A.

## 4. The splits, the mirror, the interaction

Down-years (the floored market negative: 2015, 2018, 2022 per D347), era halves, and the
**mirror** — the long version of the same event. The interaction with the `rsi` ranking on
the short base rate (`−F` per bucket): `E[signal, bucket] − E[bucket] − E[signal] + E[all]`,
ten buckets as D347. For a short signal the pairing premise is that it does *best* in the
top buckets.

## 5. Predictions

Q1 is load-bearing. Q4 is against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* at least one of `on_share`, `skew_63`, `close_in_range` is **above the p95 of all three controls** on mean hedged excess, cap exit. |
| **Q2** | control A is centred **below zero** (p50 < 0) for every one of the five: the names short signals touch carry a negative unconditional excess. |
| **Q3** | the **timing value** `observed − A p50` is **positive** for at least two of the five. |
| **Q4** | *(against)* some short signal nets **> 0 per trade after the PUB round trip and the borrow**, under either exit. |
| **Q5** | for `on_share` and `skew_63` the interaction is **most positive in the top `rsi` bucket** (98, 100] — the pairing premise holds on the short side; D347's reversal was a long-side fact. |
| **Q6** | every mirror (the long of the same event) has mean hedged excess **< 0**. |
| **Q7** | the short excess in **down-years** exceeds the overall excess for every signal. |
| **Q8** | beta-adjusted excess is **above** equal-weight excess for every short (the names carry β > 1 and the equal-weight hedge over-credits them). |
| *check* | the kernel is D345's, unchanged, fed `(zeros, hi)`; the cap-exit trade count equals the event count minus events on names already held and events with no priced forward path. |

## 6. Stop conditions

- **Q1 holds** → the survivor is the pair book's **short** trigger; the pair design is
  rewritten short-signal-first with the long side as the hedge, and §4 says which `rsi`
  buckets it fires in profitably.
- **Q1 fails** → no short signal is real against drift-matched controls either; the pair
  book has no trigger on either side under the current conventions and waits.
- **Q3 holds and Q4 fails** → the short side has timing that cost eats — D238's verdict in
  the current conventions; the record says by how much and what breakeven spread it needs.
- Nothing is promoted. Book: empty.

## 7. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep: cache keys; F0 counts; raw factor == census; `keep_v2` share == D343 |
| **[ID]** | D345's kernel identity re-asserted on the short side: fed rank < 2 with the slot exit it reproduces the slot book's invariant **short** ledger bit-identically |
| **[E]** | 300 sampled events per signal satisfy the entry condition on the raw lagged percentile (or `rsi`) at t−1, are fresh, and fail unlagged |
| **[H]** | the floored market equals a direct mean on 200 sampled bars; β on a synthetic name recovers 2 within 0.05 |
| **[S]** | every cap-exit trade equals the open-fill recomputation against the floored market with the short sign to 1e-12; a name that **rises** against the market pays **negatively** on a short |
| **[SB]** | the borrow per trade equals `d337_borrow.borrow_per_trade_bp` recomputed independently on 200 sampled trades; HTB flags agree with F0 windows and the $5 close |
| **[A]** / **[B]** | A keeps every name's event count (< 2% lost to the hedge confinement) and no rotated trade carries a NaN; B keeps every event's date and bucket |
| **[C]** | control C's mean within 2 standard errors of zero |
| **[F]** | the short base-rate grid `−F` equals a direct per-cell recomputation on 3,000 cells |
| **[X]** | `Σ_b n_b (E_sb − E_s) = 0`; the buckets partition the events |
| **[6]** | [S] raises on a short ledger handed +50 bp; [SB] raises on borrow charged at GC where HTB applies |

## 8. Files

`docs/decisions/D349-is-the-short-signal-real-three-controls-on-the-short-side.md` (this
record) · `scripts/run_d349_short_signal_controls.py` (stages: `--selftest`, `--controls
<signal> --draws N --part p`, `--report`) · `data/d349_ctrl_*.json`,
`data/d349_short_signal_controls.json` (to follow). Reuses `scripts/d348_prep.py`,
`scripts/d345_event_book.py`, `scripts/run_d347_long_signal_controls.py`'s helpers,
`scripts/d337_borrow.py`.
