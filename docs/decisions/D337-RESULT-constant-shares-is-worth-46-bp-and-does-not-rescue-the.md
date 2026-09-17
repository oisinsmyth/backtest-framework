# D337 RESULT — constant shares is worth 46 bp on the incumbent's short leg and does not rescue it; the leg-wise book does not survive sizing and borrow

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D337-RESULT-constant-shares-is-worth-46-bp-and-does-not-rescue-the-short-leg.md`. The H1 above is the full title.*

**Status:** RESULT. Pre-registered at `54d8d82`, simulator flag + borrow module + runner at
`2ef7a2c` — both before this file existed (R8). D333-bounded panel, D334-rebuilt score cache.
**Date:** 2026-09-05
**Area:** Strategy research · **personal track** · cost model

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted.**

---

## 1. The identity held, so the first half of the study is a reproduction

The pre-registration stated it before the run: with entries and exits fixed, a
constant-shares trade is the summed trade minus D329's rebalancing premium on the same
bars. Measured: **max |compound gain + premium| = 2.1e-14 bp** over all eight D333 legs
and both `S_F0` legs. Every compound P&L equals `sgn·(expm1 Σlog1p v − Σ mt)` recomputed
from the ledger to 1.1e-15 ([P]). The ledgers themselves — `(row, e0, age, side)` in
order, `cnt0/cnt1/ent/mask`, the bar series — are identical across the two accumulations
on every one of 20 cells, 38,007 trades ([E]); 35,652 P&Ls differ and nothing else does.

## 2. Q1 — the incumbent's short leg under constant shares, per trade, before borrow

| `hist_L` k=20, target exit, invariant | PB | PUB |
|---|--:|--:|
| short leg, summed (D333) | −98.61 | −180.95 |
| **short leg, compound** | **−52.76** | **−135.11** |
| gain | +45.85 | +45.85 |

**Confirmed.** Constant shares is worth 46 bp a trade on the leg — exactly the premium
D329 measured — and the leg still loses 53 to 135 bp a trade. The stop condition for
*Q1 confirms* executes: **constant shares is a sizing improvement and it is not enough;
the incumbent's short leg is a cost problem, and the incumbent stays a long-leg-only
candidate.** D335 reached the same conclusion from the other side — one short leg in 46
pays its cost — and this study says the conclusion does not depend on how the short is
sized.

## 3. Q2 and Q3 — the premium is a *selection* effect of the exit, not a duration effect

The pre-registration predicted the premium would grow with the hold: `hist_L`'s short
leg under a fixed 20-bar hold **below −60 bp**. It is **−33.78**, against −45.85 under
the target exit — **smaller at the longer hold**, and Q2 is falsified.

| `hist_L` short leg | mean age | premium |
|---|--:|--:|
| target exit | 11.3 bars | **−45.85** |
| fixed hold, k=20 | 19.9 bars | **−33.78** |

The mechanism is in the exit rule. The target fires on `cx ≥ 0.9627·u` — it closes the
positions that *moved*, and selects the high-variance paths on which a rebalanced short
pays the most. The fixed hold takes every path. **The rebalancing premium in this
programme is a property of what the target exit selects, not of how long the book
holds.** That reverses the reading in D328 §11 and D329, where it was written as a
duration effect.

Q3 falsified too, on the long leg: C0's fixed-hold premiums are **long +12.22, short
−1.91** — outside the predicted ±10 on the long side. At k=5 the long leg harvests
variance meaningfully even with no exit selecting for it.

## 4. Q4 and Q5 — the borrow stress charge

**Q4 confirmed.** Hard-to-borrow (F0 window at `e0−1`, or close at entry below $5)
covers **3.0%** of C0's short position-bars on the variant book (3.3% invariant) and
**39.0%** of `hist_L`'s (33.1%). The incumbent shorts liquid names; `hist_L` at k=20
shorts sub-$5 stock.

**Q5 confirmed, exactly.** On C0's variant book: GC+HTB costs **0.252 bp/bar**; the house
rate costs **300/252 = 1.1899 bp/bar** on every ledger-covered bar with a short, to
2.2e-16 ([F]); PB net goes **+7.15 → +6.89 (GC+HTB) → +5.96 (house)**. The arithmetic
is right, and nothing below is read against it.

Borrow per short trade, target exit, variant / invariant:

| arm | HTB share | GC+HTB bp | house bp |
|---|--:|--:|--:|
| `hist_L` (H) | 39.0% / 33.1% | 10.4 / 8.9 | 13.9 / 13.5 |
| `skew_63` (S) | 44.0% / 40.0% | — | — |
| `S_F0`, `LW_F0` short | 7.2% / 8.1% | 3.4 | 12.1 |
| C0 | 3.0% / 3.3% | 1.1 | 5.0 |

**Borrow at these rates is small beside the spread convention.** D332's PB→PUB gap on
the incumbent is 20 bp/bar; GC+HTB is a quarter of one. `skew_63` under the F0 filter
loses most of its HTB names because the filter removes them — 44% → 7%. The house 300
rate is 1.19 bp/bar on any book that is always short, whatever it holds.

## 5. Q6 — the leg-wise book under compound accumulation and borrow

| `LW_F0` k=20, target exit, PUB, per trade | summed | **compound** |
|---|--:|--:|
| spread only | −7.68 | **−11.62** |
| after GC+HTB | −9.10 | **−13.03** |
| after house | −12.6 | −16.5 |

**Falsified.** Predicted > 0; it is −13.03. And it falls *further* under compound
accumulation, because the flag applies per position, to both legs, as §1 of the
pre-registration declares: the long leg is `hist_L`'s and gives back its **+25.2 bp**
variance harvest; the short leg gains +26.9. Net, the pairing loses 4 bp a trade to the
sizing that was supposed to rescue it. The stop condition executes: **the leg-wise book
does not survive honest sizing and borrow; D329/D335's construction is per-trade only.**

*Post-hoc, derived from the per-leg table and not pre-registered:* a book that held the
long leg rebalanced and the short leg in constant shares would net **+3.29** PUB per
trade spread-only, **+1.87** after GC+HTB. An observation about a mixed convention no
runner implements, recorded so it is not rediscovered as a result.

## 6. Every leg, both accumulations, before borrow (invariant, net per trade)

`sum → compound`; PB and PUB; the premium is the difference.

| arm | exit | trades L/S | PB long | PB short | PUB long | PUB short | prem L | prem S |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| H | target | 1411/1419 | +63.9 → +38.7 | −98.6 → −52.8 | +29.3 → +4.1 | −181.0 → −135.1 | +25.2 | −45.8 |
| H | fixed | 1104/1124 | +145.3 → +90.0 | −157.4 → −123.6 | +118.0 → +62.7 | −233.6 → −199.8 | +55.3 | −33.8 |
| S | target | 923/1023 | +23.8 → +26.2 | +16.7 → +40.2 | −33.8 → −31.3 | −0.5 → +23.0 | −2.4 | −23.5 |
| S | fixed | 561/605 | −5.0 → −20.0 | +19.7 → +77.2 | −61.6 → −76.6 | −1.9 → +55.6 | +15.1 | −57.5 |
| S_F0 | target | 914/972 | +29.5 → +31.8 | −23.6 → +3.3 | −29.6 → −27.3 | −61.4 → −34.5 | −2.3 | −26.9 |
| S_F0 | fixed | 549/612 | +10.1 → −5.2 | −55.0 → +0.2 | −47.0 → −62.3 | −95.7 → −40.5 | +15.3 | −55.2 |
| C0 | target | 2447/2474 | −10.7 → −13.8 | +11.5 → +16.6 | −43.1 → −46.2 | −26.0 → −20.8 | +3.1 | −5.1 |
| C0 | fixed | 2321/2387 | −13.7 → −25.9 | +15.1 → +17.0 | −46.5 → −58.7 | −22.1 → −20.2 | +12.2 | −1.9 |

Two readings. **The sizing gain is largest exactly where the short leg is worst as a
signal**: `skew_63`'s unfiltered short under a fixed hold gains 57 bp and reaches +77 PB
— on takeover targets D331 retired. Under F0 the same leg gains 55 and reaches +0.2. And
**no PUB short leg here is positive under compound except the retired `skew_63`'s**;
`S_F0` compound is −34.5.

Whole-book net per trade, invariant, target exit — after spread → after GC+HTB → after
house:

| | PB sum | PB compound | PUB sum | PUB compound |
|---|--:|--:|--:|--:|
| H | −17.6 / −22.1 / −24.4 | −7.2 / −11.6 / −13.9 | −76.1 / −80.6 / −82.9 | −65.7 / −70.2 / −72.4 |
| S | +20.1 / +15.7 / +14.3 | +33.6 / +29.2 / +27.8 | −16.3 / −20.7 / −22.0 | −2.8 / −7.2 / −8.5 |
| S_F0 | +2.2 / +0.4 / −4.0 | +17.1 / +15.4 / +10.9 | −46.0 / −47.8 / −52.2 | −31.0 / −32.8 / −37.2 |
| LW_F0 | +28.2 / +26.8 / +23.3 | +24.3 / +22.9 / +19.4 | −7.7 / −9.1 / −12.6 | −11.6 / −13.0 / −16.5 |
| C0 | +0.4 / −0.1 / −2.0 | +1.5 / +0.9 / −1.0 | −34.5 / −35.0 / −37.0 | −33.4 / −34.0 / −35.9 |

## 7. The variant books, bp/bar (accumulation-invariant, per §1 of the pre-registration)

| book, target exit | PB net | GC+HTB | net | house | net | PUB net | PUB GC | PUB house |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| H | −4.09 | 0.892 | −4.98 | 1.187 | −5.28 | −18.77 | −19.67 | −19.96 |
| H, fixed | +9.30 | 0.915 | +8.38 | 1.184 | +8.11 | +0.97 | +0.06 | −0.21 |
| S | +7.02 | 0.979 | +6.04 | 1.184 | +5.84 | −0.58 | −1.56 | −1.77 |
| S_F0 | −10.63 | 0.325 | −10.95 | 1.183 | −11.81 | −19.32 | −19.64 | −20.50 |
| LW_F0 | −0.20 | 0.325 | −0.53 | 1.183 | −1.39 | −13.22 | −13.55 | −14.40 |
| **C0** | **+7.15** | 0.252 | +6.89 | 1.190 | +5.96 | −12.68 | −12.93 | −13.87 |

The bar series is an equal-weight mean and does not compound; a compounding *book* is
out of scope as declared. `retrace_leg` is not an arm here (D335 has it at +18.93 PUB
under F0); GC+HTB on a book of its kind would be of C0's order, 0.25–0.35 bp/bar.

## 8. Predictions

| | | outcome |
|---|---|---|
| **Q1** | *(against)* `hist_L` short < 0 under compound, both conventions, before borrow | **CONFIRMED** — −52.76 PB / −135.11 PUB |
| **Q2** | fixed-hold premium on `hist_L` short below −60 | **FALSIFIED** — −33.78; *smaller* than the target exit's −45.85 |
| **Q3** | C0 fixed-hold premiums within ±10 both legs | **FALSIFIED** — long +12.22 (short −1.91) |
| **Q4** | HTB < 15% of C0's short bars, > 25% of `hist_L`'s | **CONFIRMED** — 3.0% / 39.0% |
| **Q5** | GC+HTB < 0.5 bp/bar on C0; house exactly 1.190; PB net to < 6.0, > 0 | **CONFIRMED** — 0.252; 1.1899; +5.96 |
| **Q6** | *(load-bearing)* LW_F0 > 0 PUB per trade, compound + GC/HTB | **FALSIFIED** — −13.03 |
| *check* | compound gain = −premium exactly | 2.1e-14 bp |

Three of six. Both misses about the premium ran the same way — the premium is a
variance-selection quantity and the pre-registration modelled it as a duration quantity.

## 9. Two deviations from the record's letter, both data, neither code

1. **`S_F0` was reproduced on the unbounded panel.** `data/d331_deal_filter.json` was
   written at 01:35 and the D333 fix landed at 14:15, so D331's cells live on the
   pre-bound panel. [1] reproduces them to 0.0 under D333's `arrays_for(panel_old)`
   construction, then reports the bounded shift: **`S_F0` per trade moves −6.76 PB /
   −6.90 PUB** under the bound (`audits.s_f0_bound_shift_per_trade`). D331's numbers are
   therefore ~7 bp optimistic per trade; every `S_F0` cell in §6–§7 above is on the
   bounded panel.
2. **[F] holds on ledger-covered bars.** Positions still open at T are in `cnt1` but in
   no ledger, so "every bar with `cnt1 > 0`" is exact only up to the open tail — proven
   contiguous and ≤ 20 of 4,187 bars. Masked-mean house charge on C0 is 1.1899 against
   the flat 1.1905.

## 10. Found in passing — two owed items

- **`run_d306_width_exits --selftest` fails its own [10] on the untouched original**: the
  no-exit arm differs from `data/d300_width.json` by up to 7.53 bp. That file was
  published on the pre-D333 panel and the D303 cache now rebuilds under the bound. [4]
  (D303's no-exit control, 24,248 entries) is bit-identical, so the simulator is right
  and the reference is stale. D333's side-effects section did not list it. **Owed: re-base
  `d300_width.json` under the bounded panel in a separate note, keeping the old file
  beside it** — it is quoted by D300 and stays evidence.
- **`st[5] += math.log1p(v)` is computed in both accumulation modes.** A held-bar return
  of exactly −100% would raise; none occurs on any held bar of these 20 cells, and the
  D306 self-test's [4] passed over its full book. A guard belongs there before any
  fixture with a zero close is run; not added here because no assertion reaches it.

## 11. Assertions

| | |
|---|---|
| **[S]** | kernel sign audit: −50%/+100% long +0.5 → 0.0, short −0.5 → 0.0; −50%/−50% long −1.0 → −0.75, short +1.0 → +0.75; raises on a wrong expectation |
| **[V]** | `simulate(accumulate='x')` raises `ValueError` |
| **[E]** | ledgers `(row, e0, age, side)` identical in order across accumulations, `cnt0/cnt1/ent/mask` + bar series identical, 20 cells, 38,007 trades; 35,652 P&Ls differ |
| **[P]** | compound == `sgn·(expm1 Σlog1p v − Σ mt)` to 1.1e-15; == summed − `per_leg` premium to 8.9e-16 |
| **[1]** | `accumulate="sum"`, target exit reproduces D333's `hist_L` / `skew_63` / C0 N=2 new-panel cells, both lenses, PB + PUB, to 0.0; D331 `S_F0` to 0.0 on the unbounded panel |
| **[B]** | borrow per bar × `cnt1` == borrow per trade, summed, to 7.3e-12 bp, every cell and scheme |
| **[F]** | house `bar_bp == 300/252` to 2.2e-16 on every ledger-covered masked bar |
| **[K]** | HTB flags of 13,328 trades entered through T0 = 2093 unchanged when later filings are deleted |
| **[6]** | raises on +50 bp handed free |

`run_d326_both_lenses.LEGAL` not edited; borrow keys are reported, not ranked. `net_bp`
and `mean_over_2c` untouched on every cell (asserted equal to the borrow-free values).
**Speed:** 82 s after the gate cache; one aborted first run (`OSError 22` on
`temp/d303_cache/.../r1T.npy`) collided with D335's build of the same directory — the
three cache builds that day are bit-identical.

## 12. What this establishes

1. **The rebalancing premium is real, exactly measured, and does not decide any leg.**
   It moves the incumbent's short leg 46 bp a trade and the leg still loses 53 to 135.
   Where it is largest — 55 to 58 bp on `skew_63`'s fixed-hold short — the leg is retired
   for other reasons. With D335, the short side of this programme fails on cost under
   either sizing convention.
2. **The premium is what the target exit selects, not how long the book holds.** Longer
   holds *shrink* it. D328 §11 and D329 wrote it as a duration effect; that reading is
   withdrawn here.
3. **Borrow at declared stress rates is a quarter of a basis point per bar on the
   incumbent** and 1.2 at the house rate. It is not what decides these books; the spread
   convention is. The F0 filter removes most of the HTB cohort from any jump-detecting
   short by itself.
4. **The leg-wise book is per-trade only, for the third time** (D331, D335, D337). Under
   the published convention it is negative per trade at every sizing and borrow scheme.
5. **A mixed convention — rebalanced long, constant-shares short — is the only one that
   puts LW_F0 above zero, at +1.87 after borrow.** Post-hoc; not a result; a
   pre-registration would have to predict it.

## 13. Files

`data/d337_constant_shares_borrow.json` · `scripts/run_d337_constant_shares_borrow.py` ·
`scripts/d337_borrow.py` · `scripts/run_d306_width_exits.py` (the `accumulate` flag)
