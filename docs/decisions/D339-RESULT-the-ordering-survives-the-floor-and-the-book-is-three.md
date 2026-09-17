# D339 RESULT — the ordering survives the floor, the book is three basis points, and the floor is the universe from here

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D339-RESULT-the-ordering-survives-the-floor-and-the-book-is-three-basis-points.md`. The H1 above is the full title.*

**Status:** RESULT. Census and pre-registration at `45d023d`, module + runner at
`361dad6` — both before this file existed (R8). D333 panel, D334 cache,
F0 on the structure books, PUB primary, **close fill** (D340, run the same day, shows
what that convention is worth; §6).
**Date:** 2026-09-05
**Area:** Universe definition · strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted. Book: empty.**

---

## 1. The floor, and what it did to every cell

`keep = (as-traded close at t−1 ≥ $5) ∧ (dv28 pass)`; 29.30% of live name-bars fail
(price alone 7.73%, dollar volume alone 27.56%), the census's number to 0.0.

| cell | floor | fill | gross | PB net | **PUB net** | PUB Sharpe | maxDD | held ½-spread | held price | held $vol | inv. PUB/trade | top trade |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| RL0 | none | 100% | +32.37 | +23.43 | **+18.93** | +0.546 | 13,829 | 32.4 | $32 | $20.5M | +10.0 | VSA 15.9%, $0.18, DV pct 0.04 |
| **RL-r** | **replace** | 100% | +14.56 | +7.40 | **+3.14** | +0.160 | **8,406** | 27.9 | $46 | $46.5M | **−24.5** | CHK 6.8%, $69.92, 0.69 |
| RL-s | starve | 95.2% | +11.04 | +4.66 | −0.27 | −0.011 | 14,610 | 27.9 | $45 | $45.9M | −6.0 | CYCN 11.6%, $6.38, 0.43 |
| C0 | none | 100% | +25.36 | +7.15 | −12.68 | −0.332 | 13,478 | 38.8 | $71 | $40.1M | −34.5 | VSA 17.9%, $0.29, 0.04 |
| C0-r | replace | 100% | +18.93 | +4.89 | −13.02 | −0.618 | 10,105 | 32.5 | $96 | $73.6M | −23.8 | KODK 4.4% |
| C0-s | starve | 90.8% | +24.58 | +10.18 | −9.28 | −0.348 | 11,021 | 34.9 | $74 | $62.7M | −21.1 | GME 6.9% |
| RSI0 | none | 100% | +11.05 | +6.18 | −2.55 | −0.069 | 30,751 | 33.0 | $28 | $13.5M | +11.0 | PRMW 16.0%, $3.97 |
| **RSI-r** | replace | 100% | +15.17 | +10.59 | **+4.05** | +0.201 | **6,751** | 28.0 | $45 | $45.8M | −8.5 | GME 5.0% |
| HL0 | none | 100% | +5.01 | −12.33 | −26.79 | −0.535 | 50,981 | 84.5 | $9 | $6.7M | −59.2 | PRMW 34.9%, $4.06 |
| **HL-r** | replace | 100% | +9.41 | +1.22 | −11.56 | −0.334 | **19,880** | 57.3 | $23 | $35.8M | −6.6 | GME 14.4% |

**Three readings, before any prediction.**

1. **`retrace_leg` loses five-sixths of its net to the floor**: +18.93 → **+3.14** PUB,
   an 83% fall against the predicted 40%. The replacement names earn something — gross
   +14.56 against RL0's +32.37 — but the book's edge was the sub-$5 tail. Every one of
   RL0's four illiquid top trades is gone; RL-r's top trade is CHK's bankruptcy day, a
   $70 stock at the 69th percentile of dollar volume, and it is 6.8% of the ledger.
2. **The floor improves every other book it touched.** `rsi` goes from −2.55 to **+4.05**
   and its drawdown falls 4.6×; `hist_L` from −26.79 to −11.56 with the drawdown cut
   2.6× and the held half-spread from 85 to 57 bp; the incumbent is unchanged on net
   (−12.68 → −13.02, P6 confirmed against) but its top trade turns from VSA at 17.9%
   into KODK at 4.4%. **The floor removes a tail the books were selecting for, and the
   tail was not, on balance, edge.**
3. **Replace beats starve** (P9 confirmed): a vacated slot filled by the next liquid name
   is worth +3.4 bp/bar over a hole on `retrace_leg` and +6 on the incumbent's gross.
   Starve's fill is 95.2% on `retrace_leg`, 90.8% on the incumbent; the floor removes
   29% of the universe but rarely both of a side's top two.

## 2. The load-bearing prediction: the ordering survives on liquid names

Rank rotation inside the 25-name gate, 200 draws, on RL-r:

| statistic | score | p50 | p95 | max | p |
|---|--:|--:|--:|--:|--:|
| **gross bp/bar** | **+14.56** | +2.36 | **+9.25** | +10.63 | 0.0050 |
| gross Sharpe | +0.743 | +0.138 | +0.580 | +0.624 | 0.0050 |
| net Sharpe PB | +0.378 | −0.142 | +0.259 | +0.298 | 0.0050 |
| net Sharpe PUB | +0.160 | −0.531 | **−0.163** | −0.072 | 0.0050 |

**P3 confirmed.** The gross null has teeth (p95 +9.25) and RL-r is above its maximum
on every statistic. The matched-cost net null under PUB is negative at p95 — the cost
test: a random four-name book from the liquid gate does not pay 11.4 bp/bar, and
`retrace_leg`'s ordering pays it by 3. RL-s narrowly fails its own gross null (+11.04
against p95 +11.11, p = 0.09); the hole costs the ordering its significance.

## 3. The four groups on RL-r (PUB)

| group 1 | | group 2 (1,252 trades) | |
|---|--:|---|--:|
| gross / cost / **net** bp/bar | +14.56 / 11.42 / **+3.14** | mean / **median** bp | +74.9 / **+223.2** |
| vol bp/bar | 311.1 | win rate / payoff | 73.2% / 0.48 |
| gross / net Sharpe | +0.743 / +0.160 | skew / kurtosis | **−0.73** / 14.7 |
| maxDD bp | 8,406 | ex-top / ex-bottom / **trimmed** | +42.2 / +112.9 / **+80.3** |
| exposure / fill | 76.1% / 100% | top 1% / bottom 1% share | +44% / **−49%** |
| held ½-spread / price / $vol | 27.9 bp / $46 / $46.5M | | |
| 2c / mean move / ratio | 57.9 / +74.9 / **1.29×** | | |
| breakeven ½-spread | 35.9 = **1.29×** measured | | |
| after GC+HTB / house | +2.93 / +1.95 | HTB share of short bars | 0.6% |
| invariant: long / short / both | **−20.2** / −29.2 / **−24.5** per trade | | |

**P4 confirmed:** the symmetric trim, +80.3, clears the 58 bp round trip — by 1.39×.
And this is the first book in the programme whose **left tail does the work**: mean
+75 against a median +223, bottom 1% at −49% of P&L against +44% for the top, skew
negative. The floor took the right tail's penny-stock squeezes and left the losses;
what remains is a high-win-rate, low-payoff book that clears cost thinly.

Group 3: 611 names, **11** to half the P&L (from 5), top 1/5/10 share 8.5 / 32.1 /
49.6% (from 20 / 52 / 66); **7 of 14 years net-positive** (gross 12); dead names 23.8%
of P&L at +16 net a trade; the first era half is at breakeven (−0.7 a trade, 35% of
P&L), the second carries it; price terciles now cut at $30 / $71 and the cheapest is
57% of P&L at +14 net a trade on its own cost.

**The per-trade lens is negative on both legs.** The variant book's +3.14 is a
slot-selection number; every candidate trade, uncapped, loses 24.5 bp under PUB. The two
lenses are never compared on one statistic, and here they point in opposite directions
— which is the opportunity-cost hole of FINDINGS §10 with its sign shown.

## 4. Predictions

| | | outcome |
|---|---|---|
| **P1** | RL-r PUB net falls > 40% | **CONFIRMED** — −83%, +18.93 → +3.14 |
| **P2** | top-5 name share < 30%, names to half > 15 | **FALSIFIED**, narrowly — 32.1%, 11 |
| **P3** | *(load-bearing)* RL-r above the gross null's p95, p95 > 0 | **CONFIRMED** — +14.56 vs +9.25, above the max |
| **P4** | symmetric trim clears the PUB round trip | **CONFIRMED** — +80.3 vs 58.0 |
| **P5** | top trade < 5% and DV percentile > 28 | **FALSIFIED** on share — CHK 6.8%, liquid (pct 0.69) |
| **P6** | *(against)* incumbent moves < 3 bp/bar | **CONFIRMED** — −0.34 |
| **P7** | incumbent's top trade no longer VSA, < 10% | **CONFIRMED** — KODK 4.4% |
| **P8** | fill 100% replace, < 90% starve | **FALSIFIED** on starve — 95.2% |
| **P9** | *(against)* starve below replace, by less than the floor's drop | **CONFIRMED** — +3.40 vs +15.79 |
| *check* | floor share = census 29.3% | 29.2962%, to 0.0 |

Six of nine.

## 5. Stop conditions, executed — and what D340 does to them

- **P3 and P4 hold → RL-r is, by this record's letter, the programme's first liquid
  candidate, and the R8 out-of-sample design is written and not run.** It is written in
  §7. **It is also provisional**, for a reason this record could not have known when it
  was pre-registered: D340, run the same afternoon, found the same-close fill worth
  **13.8 bp/bar** of RL0's 18.93 — and RL-r is scored under that fill. Its +3.14 has an
  open-fill companion owed before the OOS design is worth running, and the honest
  expectation is that it is negative. **A candidate under a convention known to flatter
  by more than its entire net is a formal status, not an endorsement.**
- **P6 held** (against) → the incumbent was not a liquidity story; it was a PNK story
  and a fill story (D333, D340).
- **The floor becomes the declared universe for every study after this one.** The
  census justified it; §1 confirms it — the floor removes a tail three books were
  selecting for and none was earning from. A study on the unfloored universe says so and
  reports both.

## 6. Two deviations from the record's letter, both recorded by the runner

1. **Bar 0 passes the price floor.** 826 names are live on the fixture's first bar, where
   there is no prior close; the pre-registration's `RAW_CLOSE[t−1]` is undefined there
   and its [G] demands the census's 29.30% to 1e-9, which the census computes without
   failing them. Masking bar 0 would also empty bar 1's gate through the ranker's lag,
   for a reason unrelated to liquidity. The dv28 clause still applies at bar 0 (DV is NaN
   there and a missing estimate never excludes).
2. **Replace carries a double lag by construction.** The floor masks the score, and the
   ranker lags the score, so the floor effective at bar t under replace is `keep[t−1]`
   — raw price at t−2, dollar volume through t−2 — while starve applies `keep[t]`. This
   is what [A] states and asserts; it is conservative (a name must have passed the floor
   a bar earlier), and it is one reason [W] found 30 of 710 bars where the two semantics
   enter different names.

## 7. The R8 out-of-sample design, written and not run

The cell, frozen: `retrace_leg` symmetric, depth 2, k=20, D303 target at 0.9627, F0
forms and window, the floor as declared here with replace semantics, PUB, GC+HTB. **Under
the open fill** (D340), since a close fill is not a convention a real book can meet. The
fixture: one this cell has never touched — `us_shorts_daily_holdout` exists in
`data/fixtures/` and has been read zero times; whether to spend a read on it is the
principal's decision, not this record's. Predictions declared before the read: PUB net
bp/bar > 0 under the open fill; gross bp/bar above its own rotation null's p95 with p95
> 0; symmetric trim above the round trip; names to half the P&L ≥ 10; no single trade
above 10% of the ledger. Any failure retires the cell. **This design is not executed
here and this record recommends against executing it until the open-fill companion of
RL-r exists on this fixture.**

## 8. Assertions

| | |
|---|---|
| **[K]** | cache key with `ragged_panel.py`; npz newer than the builder |
| **[F]** | F0: 1,719 filings, 2.54% |
| **[R]** | raw factor equals the census's on the full grid; 1.0 on every bar for 1,070 names without splits; VSA 2025-01-30 → $0.1811 |
| **[C]** | a second implementation (per-name cumsum, per-bar percentile, never `keep_mask`) equals the floor on the full grid; perturbing every price and volume from bar t on leaves `keep[:t]` identical on 20 of 20 sampled bars (and moves `keep` after t on all 20); perturbing bar t alone leaves `keep[t]` identical on 200 of 200 |
| **[G]** | `keep = all-True` reproduces RL0 bit-identically — rank, gate, book, ledger — under replace AND starve; fill 100% / 95.2%; floor share 29.2962% == census to 0.0 |
| **[W]** | on 680 of 4,185 bars where the unfloored top-2 per side pass the floor at the semantics' own lag, replace, starve and RL0 enter the same names |
| **[A]** | RL-r's long gate rebuilt from the floored score at t−1 by a direct stable argsort equals the gate on 200 of 200 bars; the unlagged rebuild differs on 200 |
| **[S]** | every RL-r trade equals `sgn·Σ(v − mt)` to 1.4e-16; favourable paths pay positively on every long and short |
| **[RQ]** | same 1,252 entries under compound accumulation, 1,125 P&Ls differ (+74.9 vs +70.2); group 1 scores the summed ledger |
| **[1]** | RL0 reproduces D338 to 0.0; C0 reproduces D333's `C0 N=2/{PB,PUB}/new` to 0.0 |
| **[2]** | 1,252 trades reconstruct gross to −0.20 bp; 4 open at T, no hole; P&L = 1.99× contribution; rejects a ledger missing a trade |
| **[3]** | symmetric trim, k=12; rejects one deeper |
| **[N]** | rotating RL-r's rank array moves gross +14.56 → −0.77; 200 of 200 draws valid on both floored cells |
| **[B]** | borrow reconciles to 7.3e-12 on every cell; house == 300/252 to 0.0 |
| **[6]** | raises on +5 bp handed |

**Speed:** 211 s including both nulls (20 s each); self-test 189 s, of which [C] is 120.

## 9. What this establishes

1. **The fixture's illiquid tail was not edge.** Removing it improved three books and
   left the incumbent's net unchanged while replacing its top trade. A dead-inclusive
   universe with no floor hands every extreme-rank selector the same nine names; the
   floor is a universe definition from here, and the census is why.
2. **`retrace_leg` orders liquid names too** — above its null's maximum on gross — and
   **the ordering is worth 3 bp/bar under a fill convention worth 14.** With D340, the
   best book in the programme is, honestly scored, at or below zero. Its formal candidate
   status under this record's letter is recorded, and this record recommends no
   out-of-sample read until the open-fill companion exists.
3. **The first book whose left tail does the work.** Mean below median, bottom 1% larger
   than the top, negative skew, 73% win rate on a 0.48 payoff. Reporting rule 2's tell,
   seen for the first time in the direction it was written for.
4. **The two lenses disagree in sign** on RL-r: +3.14 bp/bar variant, −24.5 a trade
   invariant. FINDINGS §10's opportunity cost is not a footnote on this book; it is the
   book.
5. **Replace, not starve.** A universe definition fills the slot; a variant leaves a
   hole; the slot is worth 3 to 6 bp/bar.

## 10. Files

`data/d339_universe_floor.json` · `scripts/run_d339_universe_floor.py` ·
`scripts/d339_universe_floor.py` · the census: `scripts/d339_census.py`,
`data/d339_census.json`, `data/d339_census.txt`
