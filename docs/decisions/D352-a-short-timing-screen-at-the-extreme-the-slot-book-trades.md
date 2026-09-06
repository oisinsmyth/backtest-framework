# D352 — a short-timing screen at the extreme the slot book trades: 139 declared short events, each scored against its own names at random eligible times

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). Nothing here is a
result. Nothing here is a book. This is a screen: it makes no claim of its own and produces
at most a shortlist of short triggers for the pair book.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

D349 tested five short signals as top-decile events — some 150 names a day — and found none
real. The slot book's short leg is the top two names of 1,573, and at that depth `on_share`'s
short leg pays +21 to +31 a trade (D346). D348 showed on the long side that the depth-2
selection and the decile event are different objects. So the short side has been tested at
the wrong extreme, and with a control D351 showed was trading the excluded tail. This record
screens every short event shape the family can express, down to the top 2%, against the
corrected control from the start.

## 1. The family, declared: 46 scores × 3 shapes + the `rsi` turn = 139

The 46 dimensionless scores of D335/D346, each floored (`keep_v2`), deal-filtered (F0), on the
warm base, lagged one bar, as a cross-sectional percentile `pct` among floored live names at
t−1 (average rank on ties; undefined below 50 finite names). Every member is a **short** event:

| shape | short event at t |
|---|---|
| **S2** | fresh entry into the top 2%: `pct[t] ≥ 98` and `pct[t−1] < 98` |
| **S5** | fresh entry into the top 5%: `pct[t] ≥ 95` and `pct[t−1] < 95` |
| **S10** | fresh entry into the top decile: `pct[t] ≥ 90` and `pct[t−1] < 90` (D349's shape) |
| **turn** | `rsi[t−1] < 70` and `rsi[t−2] ≥ 70` — the conventional short turn (`rsi` only) |

D349's five are members; S10 on them must reproduce D349's event matrices exactly.
Every event is entered short at the next open, hedged against the floored universe's
equal-weight return, held 40 bars (the cap exit), truncated at delisting, confined to bars
after the hedge is defined.

## 2. Stage 1 — the grid

`F` is D347's forward-40 hedged excess grid; the short statistic is the mean of **`−F`** over
the member's event cells, every event counted. **Control A′** rotates each name's events
within its **eligible** bars (D351's domain, the only one run here), 1,000 draws. **Control
B** replaces each event's name with a random eligible name in the same `rsi` bucket on the
same day, the pool **confined to names with a defined `rsi` percentile** (D349 §6: an
undefined percentile digitises into the top bucket, which is where short events live),
1,000 draws. Per member: `E`, the timing value `TV = E − A′ p50`, `z_A`, `p_A`, `p_B`, `TV`
per era half, event count, distinct names, overlap share, top-1% share. Multiplicity: nominal
139; `M_eff` (Li–Ji, Cheverud–Nyholt) from the members' daily mean-`−F` series; **BH at q =
0.10 on `p_A`**; the family-wise grid-max under one shared offset vector per draw, reported
beside the winner. The oracle (cells in each name's own top decile of `−F`) must clear A′ at
p < 0.001 and a matched noise series must not, before any member is read.

**The gate to stage 2:** `p_A ≤ 0.05`, `p_B ≤ 0.05`, `TV > 0` in both era halves, ≥ 2,000
events; the top five by `z_A`; if none passes, the top three, labelled fallback.

## 3. Stage 2 — the kernel, on the survivors

D345's kernel fed `(zeros, hi)` with the **raw** percentile as its score (so the invalidation
exit is `pct ≤ 50` and same-bar entries are ordered most extreme first), cap and invalidation
exits, every event taken. **Controls:** A′ (100 draws, within `elig`, the D351 assertions),
B (100, defined-percentile pool), C (1,000, random direction). **Cost:** the PUB and PB round
trips at the held median half-spread, commission, and GC/HTB borrow per trade (D337's
rates; HTB = F0 window at e0−1 or as-traded close < $5), with the breakeven half-spread.
**Mirror:** the long of the same event. **Splits:** down-years, era halves, dead/alive, price
halves. **Interaction** with the `rsi` ranking on the short base rate, buckets 0–9, events
with an undefined percentile excluded and counted. **Four groups** per trade with the top
trade named (bar, as-traded price, dollar-volume percentile).

## 4. Predictions

Q1 is load-bearing. Q4 is against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* at least one **S2** member is above the p95 of A′, B and C under the kernel. |
| **Q2** | for `on_share` and `skew_63` the S2 shape has `p_A ≤ 0.05` on the grid and the S10 shape does not: the short leg lives at the extreme the slot book trades. |
| **Q3** | the number of members at `p_A ≤ 0.05` exceeds `0.05 × M_eff + 2`. |
| **Q4** | *(against)* some survivor nets **> 0 per trade after the PUB round trip and the borrow**, under either exit. |
| **Q5** | every survivor's mirror has mean hedged excess **< 0**. |
| **Q6** | A′ is centred **below zero** for every S2 member: the names a short signal touches rise at random eligible times (D351: −22 to −41 for D349's five). |
| **Q7** | every survivor's interaction with the `rsi` ranking is **most negative in the top bucket** (98, 100]. |
| **Q8** | the `rsi` turn is inside A′'s p95. |
| *check* | S10 on `on_share`, `skew_63`, `close_in_range`, `rsi` and the turn reproduce D349's event counts (22,646 / 8,985 / 168,180 / 45,290 / 32,917). |

## 5. Stop conditions

- **Q1 holds** → the survivor with the highest `z_A` among those above all three controls is
  the pair book's **short trigger**, named in a committed addendum to D354 before its short
  arm runs.
- **Q1 fails** → no short trigger exists on the event lens at any extreme this family can
  express; D354 runs its long arm only and the short side of the pair book stays the
  ranking's own extreme.
- Nothing is promoted. Book: empty.

## 6. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** · **[F]** | via the shared prep; the grid equals a direct recomputation on 3,000 cells |
| **[G49]** | S10 on D349's four decile signals and the turn equal D349's event matrices exactly |
| **[E]** | 300 sampled events per shape satisfy the definition on the raw lagged percentile at t−1 by direct count, are fresh, and fail unlagged |
| **[SP]** | the sparse rotation gather equals the dense rotation on 20 draws × 5 members and a tie-heavy synthetic grid |
| **[A′]** | every draw keeps every name's event count; every rotated event is eligible; no NaN |
| **[B]** | date and bucket kept; the pool contains only names with a defined percentile; the name changes wherever the pool allows, the shortfall counted |
| **[O]** | the oracle on `−F` clears A′ at p < 0.001; the noise series is below 0.05 on ≤ 3 of 20 seeds |
| **[S]** | every kernel trade equals `−(open-fill hedged excess)` to 1e-12; a name that rises against the market pays negatively |
| **[SB]** | the borrow on 200 sampled trades equals an independent recomputation; HTB flags agree with the rule |
| **[M]** · **[BH]** · **[X]** | as D350 |
| **[6]** | [S] raises on a short ledger handed +50 bp; [A′] raises on a draw rotated within `finT`; [O] raises when the oracle is replaced by noise |

## 7. Files

`docs/decisions/D352-a-short-timing-screen-at-the-extreme-the-slot-book-trades.md` (this
record) · `scripts/run_d352_short_timing_screen.py` (stages `--selftest`, `--screen`,
`--kernel <member> --draws N --part p`, `--report`) · `data/d352_screen.json`,
`data/d352_ctrl_*.json`, `data/d352_short_timing_screen.json` (to follow). Reuses
`scripts/run_d350_long_timing_screen.py`, `scripts/run_d349_short_signal_controls.py`,
`scripts/d348_prep.py`, `scripts/d345_event_book.py`.
