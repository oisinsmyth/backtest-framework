# D677 — DIAG: why D676's root-aware break loses on CL, NG, GC and SI. The break carries a small, real piece of direction on all eight roots, but on energy and metals it is a third to a half of NQ's (relative to ATR) and the friction is about three times NQ's. The root-aware skips can only remove sessions; two removed genuinely bad ones (GC's delivery window, NG's index-roll window), and neither could create an edge that was not there

*2026-09-29.*
- *The principal: "a diagnostic and statistical review of these results and why the root aware condition didn't help? Or
  the breakout in general does not work"; "it's more of a strategy diagnostic".*
- *One run of `scripts/diag_d677_break_anatomy.py` (0.55 min). Output: `data/diag_d677_break_anatomy.json`.*
- *It uses D676's own functions unchanged and **reproduces D676's primary gross, base gross and R2/R3 removed reads to
  1e-9 before reporting anything**.*
- *In-sample, and already read by D676's single run. The vault is not read; CL/NG post-vault data stays sealed.*
- *A diagnostic: it admits nothing, and every cut below is post hoc.*

## 1. The trade, layer by layer (primary book; bp per trade, HAC t)

| | CL | NG | GC | SI |
|---|---|---|---|---|
| **A. at the level:** E4 with no fill ticks | **+3.65 (1.0)** | **+6.05 (1.4)** | **+1.64 (1.7)** | **+2.55 (1.7)** |
| B. − one tick on each fill (the rule's fill convention) | −3.12 | −7.21 | −1.20 | −5.03 |
| = D676's gross | +0.53 | −1.16 | +0.45 | −2.48 |
| C. − cost: $3 commission | −5.13 | **−10.55** | −1.88 | −1.52 |
| − measured crossing | −3.48 | −3.52 | −1.84 | −2.53 |
| − one tick of slippage | −1.71 | −3.52 | −0.63 | −2.53 |
| = D676's net | −9.79 (−2.9) | −18.74 (−4.3) | −3.91 (−4.1) | −9.05 (−5.9) |
| **single-count net** (level − commission − crossing) | −4.96 (−1.4) | −8.01 (−1.8) | −2.08 (−2.2) | −1.50 (−1.0) |
| ATR, bp (median) | 265 | 422 | 107 | 205 |
| **all friction, % of ATR** | **4.9** | **6.4** | **4.9** | **5.1** |

**Before any friction, the break makes +1.6 to +6.1 bp on every root, none with t ≥ 2.** Friction then takes 13 to
28 bp.

**The fill convention in the D668/D676 stack double-counts.** A stop that fills one tick through (B) is paying the
crossing, and C then charges the crossing and another tick.
- The single-count net takes that out and is still negative on all four, so **no verdict changes**.
- **Gate 1 is unaffected:** N1's random entries pay the same fill ticks.
- **It matters for NQ:** D668's net of +1.69 bp is understated by the same double count. Any vault pre-registration for
  NQ should state its friction once.

**The micro sizes set the cost.** MNG's notional is about $2,800, so the $3 commission alone is 10.6 bp: 2.5% of NG's
ATR before a tick is paid. NQ's cost is about 1.7% of ATR (D676 §7).

## 2. The entry: after the break, the move is close to a random walk

**Signed return from the level, same-clock drift removed** (drift is < 0.3 bp everywhere):

| | +5 min | +15 | +30 | +60 | +120 | to flat | share > 0 (all horizons) |
|---|---|---|---|---|---|---|---|
| CL | +1.3 (1.0) | +2.2 (1.2) | +0.9 | +0.3 | +0.9 | −3.3 | 0.47–0.50 |
| NG | +2.3 (1.1) | +2.3 | +1.5 | +3.8 (0.8) | +2.2 | +3.5 | 0.47–0.54 |
| GC | +1.3 (**2.9**) | +1.5 (**2.1**) | +2.1 (**2.4**) | +1.7 (1.5) | +1.6 | +1.2 | 0.46–0.52 |
| SI | +1.8 (**2.0**) | +2.2 (1.7) | +2.7 (1.8) | +1.9 | +3.0 | +1.9 | 0.46–0.51 |
- **In % of ATR:** CL −1.4 to +0.3; NG +0.9 to +1.9; GC +1.3 to +2.1; SI +1.1 to +2.1.
- **There is continuation, but at most about 2% of ATR (about zero on CL), and the median break goes nowhere:** half
  the breaks are above the level at every horizon.
- **On CL, what little there is happens inside the break bar itself.** From the break bar's close onward, the move is
  zero or negative. That part cannot be captured by a stop entry plus a tick.

**The first-passage test is the cleanest read.** The initial stop sits 0.25 A behind the level (median 0.25 A):

| | reaches +0.25 A before the stop | +0.5 A | +1 A | median MFE / MAE in 60 min (A) |
|---|---|---|---|---|
| CL | 48% | 22% | 5% | 0.16 / 0.17 |
| NG | 50% | 24% | 4% | 0.17 / 0.15 |
| GC | 51% | 29% | 8% | 0.19 / 0.17 |
| SI | 51% | 25% | 9% | 0.20 / 0.17 |
| random walk, symmetric barrier | 50% | 33% (no time limit) | 20% (no time limit) | equal |

**At the symmetric distance, the break's hit rate is the random walk's 50%.** Excursions are symmetric. The break
level is not a place where direction is decided on these roots.

## 3. The exit is not the problem

| E4 gross at the level, by exit | CL | NG | GC | SI |
|---|---|---|---|---|
| trail 0.25 A (the rule) | +3.65 | +6.05 | +1.64 | +2.55 |
| trail 0.5 A | +0.34 | +7.39 | +1.26 | +2.28 |
| trail 1 A | +2.02 | +6.37 | +1.19 | −0.25 |
| E2 (stop at the level, no trail) | −1.15 | +5.73 | +0.70 | −1.32 |
| hold to flat, no stop | −3.61 | +3.48 | +1.23 | +1.86 |

**No exit turns any root's at-level gross into more than about +7 bp**, against friction of 13–28 bp.
- The rule's 0.25 A trail is best or near-best on three roots.
- This is D630's "exits cannot rescue a thin micro edge", again.

**The payoff shape.** 88–94% of trades end on a stop (median hold 31–43 min):
- **21–29% are stopped within 15 minutes, at −14 to −61 bp:** the false breaks.
- **The 6–12% that reach the flat time earn +24 to +109 bp:** the trend days.
- **On energy and metals the trend days are too few and too small** to pay for the false breaks plus friction. On NQ
  they are not.

## 4. Where the break fires

| E4, D676 gross / at the level | CL | NG | GC | SI |
|---|---|---|---|---|
| **gap:** opens through the stop (41–47% of trades) | +2.7 / **+6.0** | +6.5 / **+14.2 (1.8)** | +2.3 / **+3.5 (2.4)** | −0.9 / **+4.3 (1.7)** |
| **fresh intraday break,** level not traded overnight (35–39%) | −1.3 / +1.6 | **−12.2 (−2.0)** / −5.3 | −2.1 / −0.9 | −4.0 / +1.1 |
| intraday, level already traded overnight (18–23%) | −0.6 / +2.5 | +0.3 / +6.8 | +1.0 / +2.2 | −3.0 / +1.7 |
| entry in the first 30 min / 30–120 / later (D676 gross) | +4.8 / −3.1 / −3.3 | +4.4 / **−12.9** / −2.7 | +0.6 / +1.4 / −2.0 | −1.8 / **−7.3 (−2.4)** / +4.9 |

- **The break that works, where anything does, is the one the overnight session already made:** the gap through the
  level.
- **A fresh intraday break of yesterday's day range fails on every root at D676's gross.**
- **The mechanism story:** these roots trade nearly 23 hours, and their information (the EIA, London metals, Asia)
  does not arrive at the CME day-session open. So yesterday's *day-session* range is not the reference the market
  trades against, as it plausibly is for the US index roots.
- Long vs short at 60 minutes, drift removed: short is higher on every root, but no t ≥ 1.6. The long/short asymmetry
  D676 reported is inside the noise.

## 5. Why the root-aware skips could not help

**A skip removes sessions.** The kept book beats the base book only by the removed trades' shortfall times their share.
It cannot add direction the break does not have.

**Removed vs kept, E4 gross on the base book:**

| | CL | NG | GC | SI |
|---|---|---|---|---|
| R2 delivery: removed − kept (t) | −3.0 (−0.6) | +0.6 (0.1) | **−5.7 (−3.1)** | −5.1 (−1.7) |
| R2 profile by business days to delivery: 0–5 / 6–10 / 11–15 / 16–20 | −6.0 / +1.8 / +5.5 / +2.6 | −20.4 / +2.9 / −12.4 / +4.0 | **−6.7 / −4.2** / +1.9 / +2.8 | −3.4 / −9.2 / +1.9 / −0.2 |
| R3 index roll: removed − kept (t) | −1.2 (−0.3) | **−16.1 (−2.8)** | +1.7 (0.9) | +5.8 (1.5) |
| R3 declared window's rank among the 17 six-day windows of the month (1 = most negative) | 11 | **1** | 13 | 15 |
| R3 years with removed < kept | 4 of 9 | 6 of 9 | 2 of 9 | 3 of 9 |
| per-trade SD, removed / kept | 86 / 101 | 113 / 112 · 104 / 115 | 26 / 30 | 51 / 55 |

**R2 works as designed on GC, and weakly on SI.**
- GC's breaks in the 10 business days before first notice lose (−6.7 and −4.2, monotone with the next buckets). That is
  when GC's active-month roll takes liquidity out of the front.
- It is the most credible read in this record: a mechanism, a monotone profile, and t −3.1.
- **It is already in the rule, and the kept book is still +0.5 bp gross.**

**R3's premise holds on NG only.**
- NG's declared window is the most negative of the 17. The neighbouring windows are negative too, and the business-day
  profile is noisy (per-day SE about 13 bp; BD 9 −45, BD 12 +27).
- Read it as about a 1-in-17 placebo on overlapping windows (p ≈ 0.06), not as a confirmed index-roll effect.
- On GC and SI the declared window is among the *better* windows (ranks 13 and 15), so the skip removed their better
  trades. The commodity-index roll is not visible in metals' day-session breaks.

**R4, the EIA, did nothing detectable:**

| | CL | NG |
|---|---|---|
| EIA day, break before the release | +1.00 (217) | −3.98 (218) |
| other days, break before 10:31 | +1.13 (870) | −2.10 (974) |
| EIA day, break after the release | −5.16 (95) | −6.28 (94) |
| other days, break after 10:31 | +2.71 (263) | −13.23 (209) |

- EIA days look like other days at the same clock. NG's late breaks fail whether or not there was a release.

**R1 is structural** (D676 §3): the levels are same-contract, so a roll session never trades.

**The skipped days are not noisier** (the SDs above are about equal), so the skips did not even buy a smaller standard
error.

**Multiplicity:** this record cuts the book about 40 ways. Two cuts at |t| ≥ 2.5 (NG R3, GC R2) is about what chance
gives. GC R2 is the one with a mechanism and a monotone profile.

## 6. Does the breakout work in general? Yes, a little, everywhere; tradeable only where it is large relative to cost

**The break vs random entry at the same clock with the same exit (N1), gross per trade:**

| | NQ* | ES* | YM | RTY | CL | NG | GC | SI |
|---|---|---|---|---|---|---|---|---|
| break − N1 p50, bp | +3.85 | +2.15 | +1.24 | +0.80 | +1.59 | +3.96 | +1.23 | +1.99 |
| N1 rank | 1.00 | 0.99 | 0.90 | 0.71 | 0.70 | 0.82 | 0.92 | 0.88 |
| cost, bp | 2.60 | 3.51 | 3.16 | 4.80 | 10.32 | 17.58 | 4.35 | 6.58 |
| **excess ÷ cost** | **1.48** | 0.61 | 0.39 | 0.17 | 0.15 | 0.23 | 0.28 | 0.30 |

*ES and NQ were D668's development roots.

**The break beats its random-entry null on 8 of 8 roots.**
- Fisher on the N1 ranks: index four p = 0.0002, energy and metals four p = 0.057, all eight p = 0.0001. This is
  descriptive: ES and NQ are spent and it was not a declared test.
- **So the breakout does carry information in general. What varies is its size:**
  - NQ's excess is about 2.6% of ATR;
  - energy and metals' are 0.6–1.2%;
  - and their friction is 4.9–6.4% of ATR against NQ's roughly 1.7–1.9%.
- **Only NQ's excess exceeds its cost.** Everywhere else the information is 15–60% of what it costs to trade.

## 7. What this says

1. **The breakout does not fail because it is meaningless.** It fails because on these roots the direction it carries
   is small (a random-walk first passage, about 1% of ATR of continuation), while micro-size friction is large (5–6%
   of ATR).
2. **The root-aware conditions were contamination filters, not signals.**
   - They could only remove bad sessions.
   - Two did remove genuinely bad ones: GC's pre-first-notice window, and NG's early-month window as a weaker lead.
   - Removing them moves the base by about 1–4 bp. The gap to breakeven is 13–28 bp.
3. **Nothing here re-opens the line under R8.** The leads, each post hoc, are:
   - **(a)** the gap-through open vs the fresh intraday break (at the level +3.5 to +14 vs −5 to +2);
   - **(b)** GC's delivery-window failure, a candidate *veto* for any GC construction;
   - **(c)** NG's early-month window;
   - **(d)** the fill-convention double count, which matters for NQ's vault pre-registration.
