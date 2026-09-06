# D349 RESULT — every short signal beats its own names at random times, and every one still loses: the names it shorts rise

**Status:** RESULT. Pre-registered at `de389ce`, runner at `91d1b81` — both before this file
existed (R8). `keep_v2`, F0, next-open fill, hedged against the floored universe's own market,
PUB primary, PB beside, GC/HTB borrow in the net.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is a book. Nothing is promoted. The pair book has no trigger on either side under these conventions.**

---

## 1. The verdict

**Three of eight; the load-bearing one falsified.** No short signal is above all three
controls. Every one of the five is above all 100 draws of control A — its own names shorted
at random times — by 26 to 67 bp a trade, and every one still has a **negative** mean
hedged excess on the cap exit, from −1.8 (`rsi` decile) to −40.9 (`on_share`). None beats
control C: the directional claim fails because the direction is wrong on average. Two beat
control B.

| short, cap exit, bp per trade | n | observed | **control A** p50 / p95 | control B p50 / p95 | control C p95 | above A / B / C | timing = obs − A p50 |
|---|--:|--:|--:|--:|--:|---|--:|
| `on_share` | 11,102 | −40.9 | −66.6 / −48.5 | −23.7 / −12.5 | +20.5 | **yes** / no / no | **+25.6** |
| `skew_63` | 5,499 | −3.6 | −70.5 / −40.9 | −17.7 / +7.7 | +32.7 | **yes** / no / no | **+66.9** |
| `close_in_range` | 38,313 | −11.5 | −56.3 / −46.8 | −17.1 / −11.6 | +11.4 | **yes** / yes / no | **+44.9** |
| `rsi` decile | 18,467 | −1.8 | −67.0 / −54.1 | −9.4 / −3.6 | +17.3 | **yes** / yes / no | **+65.2** |
| `rsi` turn | 14,989 | −18.6 | −69.1 / −50.7 | −11.1 / −1.2 | +18.2 | **yes** / no / no | **+50.5** |

100 distinct draws for A and B, 1,000 for C.

## 2. What the controls say together

**Control A is centred at −56 to −70** (Q2 confirmed): shorting these names on random days
loses 56 to 70 bp per forty bars against the floored market. The names every short signal
touches **rise** whenever they are held — the same cohort drift D347 found under the long
signals, seen from the other side. **Against that, the signals' timing is real and large**
(Q3 confirmed, five of five): a short on the signal's day does 26 to 67 bp better than a
short on the same name on a random day. It is not enough. The cohort's rise is bigger than
the timing's recovery, so the short still loses before any cost, and the long of the same
event — the mirror — pays: +40.9 for `on_share` (t = 3.3), +18.6 for the `rsi` turn, positive
for all five (Q6 falsified). D238's verdict in the current conventions: the short signal
identifies bars on which its names underperform their own path, and those names still go up.

**What eats it is not the cost; it is the cohort.** Q4 was against and is falsified anyway:
every short nets −41 to −103 after the PUB round trip and the borrow. But the mean is
negative *before* cost. The borrow is 8 bp a trade and HTB is structurally rare here — 0.0
to 0.1% of trades, because F0 windows are removed from the score and the floor removes
sub-$5 names — so the spread (54 to 61 bp PUB per round trip) is the whole cost term, and no
spread makes a cap-exit short pay (breakeven half-spread negative on every one).

**The slot book disagrees with the event lens, again.** D346's `on_share` short leg paid
+20.7 and +30.7 a trade on the invariant lens; the decile-entry event on the same score loses
40.9. As in D348 against D347, "the two most extreme names on the day" and "any name
entering the top decile" are different selections, and the second is not what the slot book
trades. The event lens says nothing about the slot books' short legs; D348 says they clear
the time rotation.

## 3. The interaction, the splits, the hedge

**Q5 falsified, and reversed — the D347 reversal is two-sided.** For `on_share` the
interaction is most positive in the middle buckets (+52 at (25, 50]) and **−46 in the top 2%
by `rsi`**; for `skew_63` it is −107 there. A short signal on a name that is also the most
overbought by `rsi` does worst, exactly as D347's long signals did worst on the most oversold.
The pairing premise — run the signal at the extreme of the ranking — fails on both sides.

**Q7 falsified:** four of five lose *more* in the down-years (`skew_63` −113 against −4). A
falling market does not rescue these shorts; their names' rise against the market is not a
beta.

**Q8 confirmed:** beta adjustment lifts every short (β 0.86 to 0.96 — the names carry *less*
than market beta, so the equal-weight hedge over-charges them), by 2 to 11 bp; none turns
positive on the cap exit except `skew_63` at +2.6 and `rsi` decile at +1.6, both inside their
own noise.

## 4. Predictions

| | | outcome |
|---|---|---|
| **Q1** | *(load-bearing)* `on_share`, `skew_63` or `close_in_range` above all three controls | **FALSIFIED** — none above C; all negative in mean |
| **Q2** | control A centred below zero for all five | **CONFIRMED** — −56 to −70 |
| **Q3** | timing value positive for at least two | **CONFIRMED** — five of five, +26 to +67 |
| **Q4** | *(against)* some short nets > 0 after PUB and borrow | **FALSIFIED** — −41 to −103 |
| **Q5** | `on_share`, `skew_63` interaction most positive in the top bucket | **FALSIFIED** — most negative there; argmax in the middle |
| **Q6** | every mirror < 0 | **FALSIFIED** — every mirror > 0 |
| **Q7** | down-years exceed overall for every signal | **FALSIFIED** — four of five worse |
| **Q8** | beta-adjusted above equal-weight for every short | **CONFIRMED** — β 0.86–0.96 |
| *check* | events = entries + already-held + unpriced; trades = entries − open at end | held on all five (e.g. `on_share` 22,646 = 11,216 + 11,430 + 0; 11,102 = 11,216 − 114) |

Three of eight.

## 5. Stop conditions, executed

- **Q1 fails → no short signal is real against drift-matched controls either.** The pair
  book has no trigger on either side under the current conventions and waits.
- **Q3 holds and Q4 fails → the short side has timing**, 26 to 67 bp a trade against its own
  names, **and what eats it is the cohort's rise, not the cost.** The record says so rather
  than repeating D238's "cost" reading.
- Nothing is promoted. Book: empty.

## 6. An erratum to D347, found while building this runner

`bucket_of` digitises an undefined `rsi` percentile into bucket 9. Of 2,858,599 eligible
name-bars, 961,819 have no `rsi` percentile (nearly all off the warm base), and D347's
base-rate grid and control-B pool put them in the top bucket. **D347's top-bucket long base
rate of −31 bp was those names, not high-`rsi` names**: with the pool confined to names with
a defined percentile, the (98, 100] bucket's long base rate is **+11**, and (90, 95] and
(95, 98] are −8 and −12. D347's sentence "high-`rsi` names lose it" holds for the 90th to
98th percentiles and not for the top 2%. D347's long events sat in buckets 0–2 and its
control B drew from those buckets, so its verdict is untouched; FINDINGS §28 is amended by
§30. Here, control B and every base rate are confined to defined-percentile names, and [B]
asserts it.

## 7. Deviations and what the run found

- The runner's smoke stage was killed for memory before the memoised chain existed (D348
  §6); the full stages ran under `memo_load` at about 1 GB a process.
- `close_in_range` (168,180 events) ran in four parts of 25 draws, `rsi` decile in two of 50;
  the report asserts each part's stored observed statistic against the re-simulated one.
- The [6] case for [SB] is synthetic — a GC trade's name is placed in an F0 window so the
  rule says HTB — because HTB occurs on 2 of 11,102 `on_share` trades.

## 8. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[ID]** | fed rank < 2 on the short side with the slot exit, the kernel reproduces the slot book's invariant short ledger bit-identically: 1,995 trades |
| **[E]** | 300 sampled events per signal satisfy the entry condition on the raw lagged percentile (or `rsi`) at t−1, are fresh, and fail unlagged on 300 of 300 |
| **[H]** | the floored market equals a direct mean on 200 sampled bars; a synthetic name recovers β = 2 |
| **[S]** | every trade equals `−(open-fill hedged excess)` to 3.3e-16; 5,656 risers pay negatively and 5,446 fallers positively on `on_share`'s 11,102; every trade has side 1 |
| **[SB]** | the borrow on 200 sampled trades equals an independent recomputation to 0.0; HTB flags agree with the F0 window and the $5 close |
| **[A]** | control A keeps every name's event count except 280 of 22,646 (1.24%) lost to the hedge confinement; no rotated trade carries a NaN |
| **[B]** | control B keeps every event's date and bucket, changes its name, and draws only names with a defined percentile |
| **[C]** | control C's mean within 2 standard errors of zero |
| **[F]** | the short base-rate grid `−F` equals a direct per-cell recomputation on 3,000 cells to 1e-14 |
| **[X]** | `Σ_b n_b (E_sb − E_s) = 0`; the buckets partition the events |
| **[6]** | [S] raises on a short ledger handed +50 bp; [SB] raises on a borrow charged at GC where the rule says HTB |

**Speed:** self-test 5 s under the memoised chain (55 s before it); 2.9 s a draw on
`on_share` and the `rsi` turn, 5.7 s on `close_in_range`; eight processes at once; report 38 s.

## 9. What this establishes

1. **No short signal is real against drift-matched controls.** Five of five lose on average
   before cost; none beats the random-direction control.
2. **The short side has timing and the cohort takes it back.** Every short signal beats its
   own names at random times by 26 to 67 bp; its names rise 56 to 70 bp at random times.
   The long of every short event pays.
3. **The extreme of the `rsi` ranking is where a signal does worst on both sides.** D347's
   interaction reversal is not a long-side fact.
4. **The event lens and the slot lens disagree on the short leg as they did on the long**
   (D348). The decile-entry event is not the depth-2 selection, and neither record speaks
   for the other.
5. **D347's top-bucket base rate was an artefact** of undefined percentiles digitised into
   bucket 9; the top 2% by `rsi` earns +11 long, not −31.

## 10. Files

`data/d349_ctrl_*.json` (nine part files) · `data/d349_short_signal_controls.json` ·
`scripts/run_d349_short_signal_controls.py` · reuses `scripts/d348_prep.py`,
`scripts/d345_event_book.py`, `scripts/run_d347_long_signal_controls.py`, `scripts/d337_borrow.py`

---

## Amendment — D351, 2026-09-06: the verdict stands; the timing values are withdrawn

This record's control A used D347's `rotate_confined` and carries its defect: 8–12% of the
rotated events landed off the floor, on bars where a short loses +251 to +319 bp per forty
bars. D351 reproduced the stored draws to 0.0 and rotated within the floored universe (A′):

| short, cap, bp/trade | observed | A as run p50 | **A′** p50 / p95 | above A′ | timing as stated → **timing′** |
|---|--:|--:|--:|---|--:|
| `on_share` | −40.9 | −66.6 | **−41.4 / −22.3** | no | +25.6 → **+0.4** |
| `skew_63` | −3.6 | −70.5 | −33.1 / −0.3 | no | +66.9 → +29.5 |
| `close_in_range` | −11.5 | −56.3 | −22.7 / −16.4 | yes | +44.9 → +11.2 |
| `rsi` decile | −1.8 | −67.0 | −35.2 / −23.9 | yes | +65.2 → +33.4 |
| `rsi` turn | −18.6 | −69.1 | −37.0 / −20.3 | yes | +50.5 → +18.4 |

**Withdrawn:** §1's "every one beats control A by 26 to 67 bp", §2's "the timing is real
and large", §5's second stop condition as stated, and §9 item 2. `on_share`'s timing is
zero; two of five are inside A′. **Stands:** Q1's failure and the verdict — every short is
negative in mean before cost and none beats control C; the mirrors pay; the interaction
reversal on the short side (§3, no rotation involved); the borrow finding; the erratum on
bucket 9 (§6). The names these shorts touch rise 22 to 41 bp at random eligible times, not
56 to 70. See D351's result and FINDINGS §32.
