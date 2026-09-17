# D358 RESULT — the sleeve is never flat: name-level rarity does not make time-level flatness, and the hedged alpha is half its own round trip

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D358-RESULT-the-sleeve-is-never-flat-name-level-rarity-does-not-make-time-level-flatness.md`. The H1 above is the full title.*

**Status:** RESULT. Pre-registered at `cb74f1a`, runner at `e93d2d0` — both before this file
existed (R8). `keep_v2`, F0, next-open fill, hedged against the floored market, D345's kernel
with the hedged series, no slot cap, PUB primary, PB beside. Six cells, multiplicity six.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is a book. Nothing is promoted. There is no flat-by-default sleeve on these triggers.**

---

## 1. The verdict

**Four of eight, and the load-bearing one failed.** The `rev_5` 2% cell, every fresh entry
into the bottom 2% taken long at the next open and held 40 bars against the floored market,
is **−1.93 bp/bar net PUB on the deployed base** (gross +1.85, cost 3.78). It is above every
one of 100 per-name time rotations (A′ p95 −2.79) and below the p95 of the same-day
same-bucket random name (B −1.81, p50 −2.29). It nets −0.22 under PB.

**And it is deployed on 100.0% of the defined bars — as is every other cell, including
`hist_L` at 2%.** The sleeve the record set out to build is never flat.

| cap exit, deployed hedged base, bp per BAR | trades | exposure | open positions | entries/yr | gross | cost PUB | **net PUB** | net PB | net Sharpe | breakeven ½-spread |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **`rev_5` 2%** | 9,509 | **100.0%** | 120 | 762 | +1.85 | 3.78 | **−1.93** | −0.22 | −0.55 | 16.9 |
| `rev_5` 5% | 18,303 | 100.0% | 231 | 1,467 | +1.28 | 3.34 | −2.07 | −0.07 | −0.99 | 11.4 |
| `rev_5` 10% | 27,316 | 100.0% | 345 | 2,191 | +1.11 | 3.12 | −2.01 | −0.17 | −1.50 | 9.9 |
| `hist_L` 2% | 4,634 | 100.0% | 58 | 370 | +2.89 | 3.98 | −1.09 | **+0.70** | −0.20 | 27.2 |
| `hist_L` 5% | 9,732 | 100.0% | 123 | 778 | +1.54 | 3.49 | −1.96 | −0.02 | −0.57 | 14.0 |
| `hist_L` 10% | 15,889 | 100.0% | 200 | 1,271 | +1.46 | 3.20 | −1.73 | +0.10 | −0.75 | 13.4 |

The 10% cells reproduce D350's event matrices and D353's ledger (27,316 trades, +43.3806 bp)
exactly, so the per-trade numbers here are D353's on a new base.

## 2. Why it is never flat: the arithmetic the pre-registration did not do

A fresh entry into the bottom 2% of a ~1,000-name eligible universe fires **5.2 times a
bar** (16,509 events on 3,185 bars); at a 40-bar hold that stacks to 120 open positions on
the average bar and 160 at the peak. For a sleeve to be flat half the time, entries × hold
would have to be about 0.7 per bar — **five or six entries a year at this hold**, a rarity of
roughly 0.002%, which is not a signal but a handful of trades. Under the invalidation exit
the hold falls to 7 bars and the sleeve is still deployed on every bar with 30 names open.

**Name-level rarity cannot produce time-level flatness on a wide universe.** A
cross-sectional trigger says *which* names, and on 1,000 names some name always qualifies.
Flatness has to come from a time-series condition — a market-level state, an era signal —
which is exactly the allocator's job in the principal's multi-strategy book. The correct
reading of a sleeve like this one is therefore: **always on when the allocator switches it
on**, and its series tells the allocator what it earns per unit of capital while on. Q4
was written without dividing D350's event count by its bar count, and it was falsified by
that division alone.

## 3. What the alpha is, and what it costs

**Gross hedged alpha is +1.1 to +2.9 bp/bar** on 58–345 open positions: the trigger's
per-trade mean (+43 to +123 bp) spread over a 40-bar hold is +1.1 to +3.1 bp per position
per bar, and that is the whole of it. The unhedged series is +5.8 to +7.6 gross, so **about
70% of a long-only sleeve's gross is the floored market**; the hedge removes it and cuts
vol threefold, and the hedged Sharpe is *below* the unhedged on every cell (Q8 falsified)
because what the hedge removes is a premium that paid over this span. In a multi-strategy
book that is the allocator's beta to size, not the sleeve's edge.

**The cost line, stated exactly.** The pre-registration costs the deployed base "as the slot
books are": `G22.costed` charges each entry a *paired* round trip — four crossings at the
held names' median half-spread plus four commissions — which on a spread book is one leg in
and out on each side. On a hedged single name it prices **the market hedge at the single
name's spread** (D345's convention: a position's own round trip is half of it, the per-trade
`2c`). That is the primary line, as pre-registered, and it is conservative by construction.
The names' own round trip is the beside line:

| cap exit, PUB, bp per bar | gross | cost as pre-registered (4 crossings) | net | cost at the names' own round trip (2 crossings) | net |
|---|--:|--:|--:|--:|--:|
| `rev_5` 2% | +1.85 | 3.78 | −1.93 | 1.89 | −0.04 |
| `rev_5` 5% | +1.28 | 3.34 | −2.07 | 1.67 | −0.39 |
| `rev_5` 10% | +1.11 | 3.12 | −2.01 | 1.56 | −0.45 |
| `hist_L` 2% | +2.89 | 3.98 | −1.09 | 1.99 | **+0.90** |
| `hist_L` 5% | +1.54 | 3.49 | −1.96 | 1.75 | −0.21 |
| `hist_L` 10% | +1.46 | 3.20 | −1.73 | 1.60 | −0.13 |

**Even with the hedge free, the hedged alpha is at or below the names' own round trip on
five cells of six**; `hist_L` at 2% is +0.90 with the hedge free and +1.80 under PB. The
held names' PUB half-spread is 30–38 bp a side (PB 12–20): the trigger selects names that
have just fallen hard, and they are wide. That is also why the B control is close on net
and not on gross — the same-day same-bucket random name earns **less** gross (p95 +1.19
against +1.85 at 2%), less per trade (p95 +50 against +78) and a lower Sharpe, but holds
cheaper names and pays 0.8 bp/bar less to do it. Q1's null clause failed on the cost
composition of the held names, not on the signal.

## 4. The rest of the family, in one table each

**Rarity sharpens the trade and thins the book.** Q2 and Q3 held: per trade +78 > +52 > +43
(`rev_5`) and +123 > +66 > +60 (`hist_L`); entries at 2% are 35% and 29% of those at 10%.
Rarer entries are better trades, and there are enough of them to be always deployed anyway.

**Both exits.** Q6 held on every cell: invalidation has higher deployed gross (+2.4 to +4.8)
and lower net (−3 to −19), because the 7-bar `rev_5` hold turns the book over six times as
fast. Q5's "against" held — `hist_L` 2% nets +29.8 a trade under PUB on the invalidation
exit (hold 20.5 bars, median +209) — and the other five net negative.

| invalidation exit, per TRADE | n | hold | mean | median | net PUB | net PB |
|---|--:|--:|--:|--:|--:|--:|
| `rev_5` 2% / 5% / 10% | 13,604 / 30,706 / 55,226 | 7.0 / 6.8 / 6.6 | +37.5 / +30.6 / +24.2 | +115 / +107 / +96 | −45.0 / −42.9 / −43.3 | −5.4 / +1.6 / −3.7 |
| `hist_L` 2% / 5% / 10% | 4,910 / 10,693 / 18,421 | 20.5 / 20.0 / 19.5 | +110.1 / +64.6 / +53.4 | +209 / +187 / +173 | **+29.8** / −6.1 / −11.8 | +69.0 / +34.1 / +25.5 |

**Era.** Q7 held on every cell: era 2 beats era 1 on the deployed net and the 2% cells'
era-1 net is ≤ 0 (−4.59, −4.23). Per trade the split is stark — `rev_5` 2% is **−26 bp a
trade in era 1 (n 3,033) and +127 in era 2 (n 6,476)**; `hist_L` 2% +15 and +175. By year
the 2% cells are positive on the deployed net in 2020, 2022, 2025 and 2026 (`rev_5`) and
2020–2022, 2025–2026 (`hist_L`) and negative in every full year before 2020. For an
allocator with era detection this is the series to condition on: the trigger has been a
post-2019 trade.

**By `rsi` bucket of the trigger name.** The deep-oversold buckets (0–1, `rsi` ≤ 5th
percentile) are the trigger's worst ground per trade on `rev_5` (+36/+39 at 2%, −1/−24 at
5%, 0/−6 at 10%) and the neutral buckets (3–4) its best (+107/+148, +49/+91, +50/+59), as
D347 and D350 found; the sub-ledgers' deployed nets are negative in every bucket with more
than a hundred trades. No bucket makes a cell positive under PUB.

## 5. Four groups, the cap exit, per trade

| | n | mean | median | win | payoff | skew | kurt | ex-top | ex-bottom | trimmed | names to half | top-1 / 5 / 10 | years + | top trade |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| `rev_5` 2% | 9,509 | +78.4 | +46.3 | 51.4% | 1.07 | +0.8 | 16.6 | −2.6 | +147.1 | +66.0 | 13 of 1,047 | 10 / 29 / 43% | 9 of 14 | GME 2020-12-10 at $14.12, DV pct 80, +33,044 bp = 4.4% |
| `rev_5` 5% | 18,303 | +52.3 | +37.0 | 51.4% | 1.04 | +0.3 | 8.2 | −13.7 | +111.6 | +45.4 | 21 of 1,110 | 4 / 16 / 28% | 11 of 14 | CVNA 2023-05-26 at $11.74, DV pct 78, +16,512 = 1.7% |
| `rev_5` 10% | 27,316 | +43.4 | +41.8 | 51.5% | 1.02 | +0.4 | 8.4 | −18.1 | +96.9 | +35.3 | 27 of 1,130 | 3 / 12 / 23% | 10 of 14 | AAOI 2026-02-19 at $46.98, DV pct 66, +15,701 = 1.3% |
| `hist_L` 2% | 4,634 | +123.2 | +68.8 | 51.9% | 1.11 | +0.7 | 6.1 | +41.9 | +185.5 | +104.0 | 14 of 905 | 8 / 26 / 43% | 10 of 14 | GME 2021-02-10 at $51.20, DV pct 99, +18,801 = 3.3% |
| `hist_L` 5% | 9,732 | +65.6 | +43.3 | 51.3% | 1.06 | +0.4 | 7.1 | −5.2 | +127.1 | +56.2 | 15 of 1,066 | 5 / 21 / 38% | 11 of 14 | GME 2021-02-09 at $50.31, DV pct 99, +18,170 = 2.8% |
| `hist_L` 10% | 15,889 | +60.4 | +21.8 | 50.7% | 1.09 | +2.0 | 57.8 | −5.3 | +115.6 | +49.7 | 23 of 1,101 | 6 / 17 / 28% | 9 of 14 | GME 2021-01-11 at $19.94, DV pct 81, +48,240 = 5.0% |

Mean above median on every cell, the symmetric trim positive on every cell, the ex-top-1%
mean below zero on five of six: the right tail is doing more of the work as the
trigger gets rarer, and **GME in the winter of 2020–21 is the top trade of four cells** —
a real move in a liquid name (DV percentile 80–99), never above 5% of a ledger. Dead names
earn less than alive on every cell; the lower price half earns more than the upper on
every cell (D284's warning, again: the cheap names are the wide ones).

## 6. The nulls

| cap exit, 100 draws each | obs net PUB | A′ p50 / p95 | B p50 / p95 | obs gross | A′ gross p95 | B gross p95 | obs per trade | A′ p95 | B p95 | C p95 (1,000) |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `rev_5` 2% | −1.93 | −3.40 / −2.79 | −2.29 / **−1.81** | +1.85 | +0.86 | +1.19 | +78.4 | +37.5 | +50.1 | +32.6 |
| `rev_5` 5% | −2.07 | −2.89 / −2.51 | −2.20 / **−1.94** | +1.28 | +0.80 | +1.03 | +52.3 | +31.9 | +42.1 | +20.5 |
| `rev_5` 10% | −2.01 | −2.66 / −2.43 | −2.30 / −2.13 | +1.11 | +0.69 | +0.82 | +43.4 | +29.0 | +33.8 | +14.8 |
| `hist_L` 2% | −1.09 | −3.49 / −2.54 | −2.41 / −1.48 | +2.89 | +1.37 | +1.52 | +123.2 | +55.0 | +57.8 | +50.3 |
| `hist_L` 5% | −1.96 | −2.99 / −2.38 | −2.43 / −1.97 | +1.54 | +1.08 | +1.02 | +65.6 | +44.6 | +43.1 | +27.7 |
| `hist_L` 10% | −1.73 | −2.63 / −2.21 | −2.35 / −2.04 | +1.46 | +1.00 | +0.91 | +60.4 | +41.2 | +37.4 | +19.8 |

Every cell is above both nulls on gross, per trade and net Sharpe; the two `rev_5` cells
at 2% and 5% are inside B's p95 on net PUB alone, for the reason §3 gives. The nulls are
decisive on the signal (A′'s gross p95 sits 0.4–1.5 bp/bar below the observed on every cell) and
not decisive on net between the trigger and a cheaper name in its bucket. A′ and B are
100 draws, not the 200 of D353; the p95s are quoted at that width.

## 7. Predictions

| | | |
|---|---|---|
| **Q1** *(load-bearing)* | **FALSIFIED** | −1.93 net PUB; above A′ (p95 −2.79), below B (p95 −1.81) |
| Q2 | CONFIRMED | +78 > +52 > +43; +123 > +66 > +60 |
| Q3 | CONFIRMED | 762 vs 2,191 (35%); 370 vs 1,271 (29%) |
| **Q4** | **FALSIFIED** | 100.0% and 100.0%; §2 |
| Q5 *(against)* | CONFIRMED — the "against" lost | `hist_L` 2% +29.8 a trade on the invalidation exit |
| Q6 | CONFIRMED | gross higher and net PUB lower on all six |
| Q7 | CONFIRMED | era 2 > era 1 on all six; 2% era-1 nets −4.59 and −4.23 |
| **Q8** | **FALSIFIED** | unhedged gross higher on all six (yes) and net Sharpe *higher* on all six (+0.27 to +0.33 against −0.20 to −1.50) |
| *check* | held | 10% cells == D350 and D353 to 1e-9; 12 series files reload to 0.0 |

## 8. Stop conditions, executed

- **Q1 fails on the null** (below B's p95 on net PUB) → by the pre-registration the sleeve
  is the 10% cell if that clears. **`rev_5` 10% clears both nulls on net PUB (−2.01 against
  −2.43 and −2.13) and nets negative**, so the third condition applies to it: **edge above
  both nulls, the published spread eats it, breakeven half-spread 9.9 bp a side** under the
  pre-registered cost line, and it waits on D336. `hist_L` 2% is the same case with more
  room: above both nulls on every statistic, −1.09 PUB, +0.70 PB, breakeven 27.2 a side.
- **On this record's own construction there is no flat-by-default sleeve on these
  triggers**, and §2 says there cannot be one from a cross-sectional trigger at any rarity
  worth trading. The always-invested slot book remains the only construction in the record
  that pays under PUB (D344, D346, D356).
- Nothing is promoted. Book: empty.

## 9. Deviations and what the run found

- **[C] was weakened, in the code and here.** The pre-registered "mean within 2 SE of zero"
  on 1,000 iid random directions is a data assertion that fails 5% per cell by
  construction, 26% over six, and it fired on `hist_L` 10% at z = −2.4 on the first run.
  Asserted at 3 SE with every cell's z printed (this run: −1.3, +1.2, +1.1, +0.9, +0.8,
  −2.4). The rule is §7 item 24's: an assertion that fires on the seed is not a self-test.
- **The 4-crossing cost convention on a hedged single name** is D345's and the
  pre-registration inherited it by reference ("costed as the slot books are"). It stands
  as the primary line; §3 prints the 2-crossing line beside it. The verdict does not move.
- **Q8's Sharpe clause** was evaluated on the deployed net PUB Sharpe; the gross-Sharpe
  comparison goes the same way on every cell.
- **The by-bucket sub-ledgers overlap in time** and do not add up to the cell; the JSON's
  `method` field says so.
- **100 draws per control**, as pre-registered; D353 ran 200 on the 10% cell and the
  per-trade p95s agree to 0.4 bp (A′) and 2.0 bp (B).

## 10. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[G]** · **[ID]** | 72,677 == D350's stored events; 23,491 == D347's `hist_L`; 27,316 trades, +43.3806 to 1e-9 == D353; the deployed base bit-identical to a re-run of D353's code path (36 keys) |
| **[E]** | 300 events per cell satisfy ≤ p at t−1 and > p at t−2 by direct count on the raw floored score, the count equals the grid to 1e-9, and the unlagged rule fails on every sample |
| **[HX]** | hedged and unhedged deployed series equal the ledger per bar to 4e-14 on all twelve cell × exit runs, open tail excluded and contiguous |
| **[SER]** | twelve series files reload and reproduce gross, cost, net, vol, both Sharpes, bars, exposure, positions and entries to 0.0 |
| **[A′]** · **[B]** · **[C]** | every rotated event eligible, counts kept; date and bucket kept, defined-percentile pool, 99.97–100% of names changed, kept == the counted shortfall; C at 3 SE (§9) |
| **[S]** | 300 A′ trades to 0.0; +50 bp on GGAL 2013-12-27 moves one trade by +50.000 and the deployed series by 5.000 = 50 / 10 open, no other bar |
| **[6]** | [HX] raises with the market term left in and on the converse; [S] raises on the +50 bp ledger; [SER] raises on a perturbed file |

**Speed:** self-test 24 s; A′ 0.6–1.9 s a draw, B 0.5–1.9; six cells in parallel 2–6 min;
report 40 s; peak working set 726 MB per process.

## 11. What this establishes

1. **A cross-sectional trigger on a wide universe is always on.** At 2% rarity on ~1,000
   names it fires five times a bar; flatness at any tradeable rarity is impossible from the
   trigger alone and must come from a time-series gate. For a multi-strategy book that gate
   is the allocator's, and the sleeve's series is what it allocates *to*, not *when*.
2. **The hedged per-bar alpha of the best long trigger in the record is +1.9 to +2.9 bp on
   the deployed base**, equal to or below the held names' own round trip at a 40-bar hold,
   and about 30% of what the same names earn unhedged. The trigger's per-trade edge is real
   and thin per unit of capital-time; it is a beta-carrying trade.
3. **The trigger selects wide names.** A random same-day same-bucket name earns less and
   pays less; on net the two are inside each other's p95 at 2% and 5%. The cost line, not
   the signal, decides the sleeve, and D336's quoted spreads decide the cost line.
4. **The series exist** — twelve files, both exits, hedged and unhedged, positions and
   entries per bar — for an allocator to condition on era; per trade the trigger is a
   post-2019 result (−26 a trade in era 1, +127 in era 2 at 2%).

## 12. Files

`data/d358_flat_sleeve.json` · `data/d358_ctrl_{rev_5,hist_L}_{2,5,10}_p0.json` ·
`data/d358_series_{rev_5,hist_L}_{2,5,10}[_inv].npz` · `scripts/run_d358_flat_sleeve.py` ·
reuses `scripts/d345_event_book.py`, `scripts/run_d353_rev5_record.py`,
`scripts/run_d350_long_timing_screen.py`, `scripts/run_d347_long_signal_controls.py`,
`scripts/d348_prep.py`, `scripts/d322_four_group_report.py`.
