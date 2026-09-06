# D352 RESULT — no short event at any extreme beats random direction: the short side beats its own names because they rise, and earns nothing doing it

**Status:** RESULT. Pre-registered at `e919974`, runner at `ddedb9f` — both before this file
existed (R8). `keep_v2`, F0, next-open fill, hedged against the floored market, D345's kernel,
control A within the floored universe from the start, PUB primary, PB beside, borrow in the net.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is a book. No short trigger exists on the event lens. D354's short arm does not run.**

---

## 1. The verdict

**Two of eight; the load-bearing one falsified.** Of 139 short events — every score at the
top 2%, top 5% and top decile, and the `rsi` turn — 23 beat their own names at random
eligible times on the grid against 7 to 9 from false discovery, and four passed the gate.
Under the kernel every one of the four is above A′; two are above B; **none is above random
direction**, because none earns anything: the observed means are −11.5 to +25.6 bp a trade
against a C p95 of +11 to +30.

| kernel, short, cap exit, bp/trade | n | mean | median | t | A′ p50 / p95 | B p50 / p95 | C p95 | above A′ / B / C | net PUB + borrow |
|---|--:|--:|--:|--:|--:|--:|--:|---|--:|
| `retrace_leg`/S10 | 23,108 | −3.8 | +2.3 | −0.4 | −30.2 / −18.8 | −10.8 / −0.4 | +14.6 | yes / no / no | −68.4 |
| `on_persist`/S2 | 5,968 | +25.6 | +14.6 | 1.4 | −21.0 / +1.3 | −19.2 / +0.4 | +30.3 | yes / yes / **no** | −38.8 |
| `close_in_range`/S10 | 38,313 | −11.5 | −3.7 | −1.7 | −22.7 / −15.7 | −16.7 / −11.4 | +11.4 | yes / no / no | −77.5 |
| `wick_asym`/S2 | 20,660 | +2.6 | +6.4 | 0.3 | −17.9 / −5.8 | −18.3 / −4.2 | +17.0 | yes / yes / **no** | −63.8 |

100 draws for A′ and B, 1,000 for C.

## 2. What "beats its own names" means on the short side

A′ is centred at −18 to −30 for these members: shorting their names on random eligible
days loses 18 to 30 bp per forty bars, because the names rise. The signal's day is 11 to 47
bp better than a random day for the same name — that is the timing value — and it still
leaves the short at or near zero. **The short side's timing is real and worth less than the
names' own drift.** D349 said this with a defective control and inflated numbers (D351); this
record says it with the corrected control on 139 members at every extreme the family can
express. `on_persist` at the top 2% is the one member that is positive and above both name
controls, and its distribution disqualifies it: six names to half the P&L, the top ten names
83%, the top trade DRYS in November 2016 at $4.95 worth 13% of the total, profitable in
eight of fourteen years, era 1 −34.

**Q2 falsified.** The prediction that the short leg lives at the extreme — that `on_share`
and `skew_63` would pass at the top 2% and fail at the decile — was wrong on both: neither
passes at any shape (`on_share`/S2 p 0.18, `skew_63`/S2 p 0.22). The slot book's `on_share`
short leg at +21 to +31 a trade (D346) is not reproduced by any event on `on_share`; the
depth-2 selection with the target exit is a different object from every event shape here,
as D348 found on the long side.

**Q6 falsified in an informative direction.** A′ is below zero for 39 of the 46 S2 members;
the seven above zero are volatility and liquidity levels (`mass_imbalance` +28,
`park_vol_21` +29, `cs_spread` +24, `atr_norm` +19, `on_share` +14): the names at the top of
those rankings *fall* at random times, so a short on them carries a positive base rate —
and still none of them clears the gate.

**Q7 falsified.** The interaction with the `rsi` ranking is not most negative in the top
bucket for any survivor; for `on_persist`/S2 it is most positive there (+143 in (95, 98]).
On the short side the ranking's extreme is not systematically the worst place, unlike the
long side's fifth table; it is not systematically the best either.

## 3. Cost

No survivor nets positive after the PUB round trip and borrow under either exit (−39 to −78
per trade on the cap). Borrow is 8 bp a trade; HTB is 0.0–0.1% of trades. The breakeven
half-spread is below zero for three of four: no spread makes them pay.

## 4. Predictions

| | | outcome |
|---|---|---|
| **Q1** | *(load-bearing)* an S2 member above A′, B and C under the kernel | **FALSIFIED** — none above C at any shape |
| **Q2** | `on_share` and `skew_63` pass at S2 and fail at S10 | **FALSIFIED** — neither passes at either |
| **Q3** | members at `p_A ≤ .05` exceed `0.05 × M_eff + 2` | **CONFIRMED** — 23 vs 7.3 / 8.8 |
| **Q4** | *(against)* a survivor nets > 0 after PUB and borrow | **FALSIFIED** — −39 to −78 |
| **Q5** | every survivor's mirror < 0 | **FALSIFIED** — two of four mirrors positive |
| **Q6** | A′ centred below zero for every S2 member | **FALSIFIED** — 39 of 46 |
| **Q7** | every survivor's interaction most negative in the top bucket | **FALSIFIED** — none |
| **Q8** | the `rsi` turn inside A′ | **CONFIRMED** — E −26.0 vs A′ p95 −23.4 |
| *check* | S10 reproduces D349's event counts | held on all five |

Two of eight.

## 5. Stop conditions, executed

- **Q1 fails → no short trigger exists on the event lens at any extreme this family can
  express.** D354 runs its long arm only; its addendum records this. The short side of any
  pair book on this universe is the ranking's own extreme or nothing.
- Nothing is promoted. Book: empty.

## 6. Deviations and what the run found

- The screen ran on six workers (528 s; 2.1 GB peak per worker) because other studies
  shared the machine; the kernel stages at 1.8 s a draw, four in parallel, 4 min each.
- Control B keeps 4.3% of `rsi`/S2's events for want of a same-day same-bucket pool (the
  declared fallback), counted; every other member replaces 99.9–100%. No eligible event
  with an undefined `rsi` percentile occurred.
- `struct_trend`/S2 has 60 events on 31 names and `rsi`/S10's top-1% share is a near-zero
  denominator; neither passed the gate and neither is read.
- The [S] secondary check (`pnl == −excess`) is at D349's 1e-9 on the nansum form; the
  open-fill recomputation is at 3.3e-16.

## 7. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** · **[F]** | via the shared prep; the grid on the short sign to 8.9e-15 |
| **[G49]** | S10 on D349's four scores and the turn equal D349's event matrices, kernel scores and counts (22,646 / 8,985 / 168,180 / 45,290 / 32,917) |
| **[E]** | 3,900 sampled events by direct count at t−1, fresh, fail unlagged |
| **[SP]** | sparse == dense rotation to 2.4e-18 and on the synthetic grid |
| **[A′]** · **[B]** | grid and kernel: counts kept, every rotated event eligible; B's replacements all eligible with a defined percentile |
| **[O]** | the oracle on `−F` clears at p = 0.001 (E +2,195 vs A′ max +46); noise below 0.05 on 1 of 20 seeds |
| **[S]** · **[SB]** | 1,798 trades to 3.3e-16, 890 risers paid negatively; borrow on 200 trades to 0.0 |
| **[M]** · **[BH]** · **[X]** | `M_eff` Li–Ji 106 / CN 136.5; BH recovers the textbook vectors; the buckets partition every survivor's trades |
| **[6]** | [S], [A′] and [O] raise on their broken inputs |

**Speed:** self-test 49 s; screen 528 s on six workers; kernel 1.8 s a draw; report 20 s.

## 8. What this establishes

1. **There is no short trigger on the event lens**, at the top 2%, 5% or 10% of any of the
   46 scores or on the `rsi` turn: the timing is real (23 of 139 beat their own names) and
   the names' rise takes all of it.
2. **The slot book's short leg is not an event.** `on_share`'s +21 to +31 a trade at depth 2
   has no counterpart at any event shape on the same score.
3. **The short side's cost is not the problem**: the means are near zero before cost.
4. **The pair book has one side.** Its short leg, if it has one, is the ranking's own
   extreme, and D354 measures what that costs.

## 9. Files

`data/d352_screen.json` · `data/d352_ctrl_*_p0.json` (four) · `data/d352_short_timing_screen.json` ·
`scripts/run_d352_short_timing_screen.py` · reuses `scripts/run_d350_long_timing_screen.py`,
`scripts/run_d349_short_signal_controls.py`, `scripts/d348_prep.py`, `scripts/d345_event_book.py`
