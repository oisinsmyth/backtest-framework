# D366 RESULT — the gated momentum buffer against its nulls: it clears them, and the gate is worth half what it looked like

**Status:** RESULT. Pre-registration `3f88292`, runner `976ecca`, refinements `2ef9c2e` — all committed before this
record (R8). **OHLCV only. No holdout read. Holdout reads spent: 0. Programme total: 0.**
**Date:** 2026-09-07 · **Area:** Strategy research · **personal track**

---

## Headline

**The construction clears every null, including the one this record was written for — and the same nulls say the
gate is worth about half of what the search made it look like, with the margin over a random gate living in ten
names out of five hundred and fifteen.**

Both halves are results. Q1 (load-bearing, for the construction) and Q7 (written against it) are *both* confirmed,
which is the outcome the pre-registration set up to be legible and is the reason it was written that way.

## 1. Performance, net and gross

| | gross | cost | **net** | vol | Sharpe | ann | maxDD | DD% | bars under | Calmar | era 1 | era 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **S6 + 252-bar cap** | +9.65 | 1.559 | **+8.09** | 145 | **0.887** | +20.4% | 3,158 | 29.4% | 1,021 | 0.645 | +0.46 | +12.10 |
| S6, uncapped | +7.62 | 1.503 | +6.12 | 143 | 0.678 | +15.4% | 4,002 | 34.0% | 278 | 0.385 | +2.15 | +8.30 |

bp/bar, PUB. Worst drawdown **2016-03-10 → 2020-03-18 → 2020-08-05**. 988 trades, 24.5 names held, gate shut
**90.8%** of bars. Cost decomposes as long round trip 1.337 + hedge borrow 0.198 + hedge rebalancing 0.024.
Per-trade round trip **96.8 bp**; mean move per trade +477.5 against it.

**The drawdown is knife-edge and this record gives two numbers rather than one.** The search's probe charged a
rounded 0.02 bp/bar for hedge rebalancing; the measured rate is 0.0237. That 0.004 bp/bar difference moves the
reported max drawdown from **3,024 to 3,158 bp** — not by accumulating, but because three recoveries that just
cleared their prior peak no longer do and their episodes merge (117 episodes become 114). Neither figure is more
true than the other; the statistic is simply unstable here at the fourth decimal place of a cost.

## 2. Trade distribution

n = 988 · mean **+477.5** · median **−28.3** · win rate 48.6% · payoff 1.77 · hold mean 72 median 48 bars ·
skew +5.3 · excess kurtosis +62.

Both-tail trims (k = 9): ex-top **+273.4**, ex-bottom **+548.2**, **symmetric +342.8**.

**The typical trade loses money.** The mean sits an order of magnitude above the median, so the *right* tail carries
this book — the mirror image of D285, where a mean below its median exposed the left tail doing the work. The
symmetric trim at +342.8 against a 96.8 bp round trip says it is not one or two trades, so Q5 passes on the honest
statistic, not the flattering one.

## 3. What the winners depend on

Names to half the P&L: **12 of 515** — Q4's prediction of ≥15 **falsified**. Top 1 / 5 / 10 name share
**11% / 30% / 45%**. Profitable years 69% of 13. Dead names 189 at +305 vs alive 799 at +518. Price split is
flat (below the $41.49 median +486, above +469), so this is not a penny-stock artefact.

**The top trade, named.** **GME, entered 2020-11-16 at $12.06, held 252 bars — exactly the cap — for +55,259 bp,
11.7% of every basis point the book made.** Its dollar volume at entry sat at the 76th percentile of that day's
eligible names, so it was not an illiquid corner of the universe. Across all its trades GME contributes +51,839 bp,
11.0% of the total.

**The jackknife — names removed from the eligible universe and the book rebuilt, so the freed slot refills:**

| dropped | gross | net | Sharpe | ann | maxDD | trades | era 2 |
|---|---|---|---|---|---|---|---|
| — | +9.65 | +8.09 | 0.887 | +20.4% | 3,158 | 988 | +12.10 |
| GME | +9.16 | +7.60 | 0.832 | +19.2% | 3,159 | 986 | +11.30 |
| + AXTI | +8.93 | +7.37 | 0.810 | +18.6% | 3,159 | 985 | +10.94 |
| + LITE | +8.74 | +7.18 | 0.791 | +18.1% | 3,162 | 984 | +10.65 |
| + MSTR, NBIS | +8.44 | +6.87 | 0.760 | +17.3% | 3,179 | 976 | +10.20 |
| + RNG, BGFV, SEDG, RH, GDXU | +6.17 | **+4.60** | 0.540 | +11.6% | 4,746 | 955 | +6.96 |

Read against §4's gate rotation, this is the sharpest thing in the record: **drop the ten best names of 515 and the
book earns +4.60, which is the random-gate median of +4.10.** The construction's entire margin over a randomly-timed
gate of the same shape is carried by ten names.

## 4. Nulls — the distribution, not the percentile alone

Observed **+8.09** bp/bar net.

| arm | draws | p50 | p95 | max | observed's rank | draws beating it | above p95? |
|---|---|---|---|---|---|---|---|
| **ROT** rank rotation | 24 | −11.25 | −3.48 | −0.24 | 100.0% | 0 | YES |
| **A′** per-name time rotation | 200 | −0.24 | +1.98 | +4.78 | 100.0% | 0 | YES |
| **GATE-ROT** *(the one this record exists for)* | 200 | **+4.10** | **+7.02** | **+9.25** | 99.0% | **2** | YES |
| **LADDER-MAX** | 7 | +4.62 | +7.33 | +8.09 | 85.7% | — | YES *(vacuous, see below)* |
| **C** random direction | 1,000 | −0.12 | +4.57 | +9.28 | 99.9% | 1 | YES |

**ROT and A′ are decisive.** The rank rotation's *entire* distribution is negative — its best of 24 shifts is −0.24.
The time rotation centres on zero with a p95 of +1.98 against +8.09. The trigger is real.

**GATE-ROT is the finding.** A gate carrying the same on-share and the same circular run structure, but placed at a
random point in time, earns **+4.10 bp/bar at the median**. Roughly half of what the gating appeared to buy is not
the gate's *timing* at all — it is the trigger plus the mechanical effect of being in the market only 9.2% of bars
with runs of that shape. The real gate does clear the rotation's p95 (+8.09 against +7.02), so Q2 passes; but two of
two hundred random gates beat it outright, and its maximum (+9.25) exceeds the observed. That is a pass with a thin
margin, and §3's jackknife shows what the margin is made of.

**LADDER-MAX is vacuous as a test and is recorded as such rather than counted.** S6 *is* the ladder's own maximum,
so clearing the ladder's 95th percentile is close to automatic. The informative content is the ladder's *shape*,
which is monotone: G4 +3.04 → S1 +3.44 → S2 +3.61 → S3 +4.62 → S4 +5.41 → S5 +5.56 → S6 +8.09. Every added
condition helps, and the last one — the index at a 252-bar high — helps most, adding +2.53 alone. A perfectly
monotone seven-step ladder found by search is a pattern to be suspicious of, not reassured by.

## 5. Predictions

| | | verdict |
|---|---|---|
| **Q1** | *(load-bearing)* net > 0 and above the p95 of ROT, A′ and C | **CONFIRMED** — +8.09 vs −3.48, +1.98, +4.57 |
| **Q2** | above the p95 of GATE-ROT | **CONFIRMED** — +8.09 vs +7.02, but 2 of 200 draws beat it |
| **Q3** | era 2 above the p95 of A′ restricted to era 2 | **CONFIRMED** — +12.10 vs +5.03, 0 of 200 draws beat it |
| **Q4** | ≥ 15 names to half the P&L | **FALSIFIED** — 12 of 515 |
| **Q5** | symmetric 1% trimmed mean per trade > the round trip | **CONFIRMED** — +342.8 vs 96.8 |
| **Q6** | above the p95 of LADDER-MAX | **CONFIRMED but vacuous** — the observed is the ladder's own max |
| **Q7** | *(against)* GATE-ROT's p50 above zero — a random gate still pays | **CONFIRMED** — +4.10 |
| **Q8** | the cap's Sharpe exceeds the uncapped | **CONFIRMED** — 0.887 vs 0.678 |
| *check* | reproduces the search's figures | **exact** — see §7 |

Era 1 pays **+0.46** against era 2's **+12.10**. This was pre-registered as not counting against the construction
and it does not; it is recorded because it has not changed since D365 and no gate found this session fixes it.

## 6. The cap is not a plateau — the one thing here that was not pre-registered and should have been

Q8 asked only whether the 252-bar cap beat *no* cap. It does. But the cap came from a six-point sweep inside the
same search, and the top trade held exactly 252 bars, so the obvious question is whether the cap was chosen *by*
that trade. It was not — the sweep's shape is the same with and without GME. What the finer sweep shows instead is
worse:

| cap | 63 | 126 | 189 | 210 | 231 | **242** | **252** | 262 | 273 | 294 | 315 | 378 | 504 | none |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| net | +3.51 | +5.90 | +5.95 | +6.65 | +7.20 | **+8.31** | **+8.09** | +7.10 | +6.73 | +6.75 | +5.99 | +6.19 | +6.06 | +6.12 |
| Sharpe | 0.439 | 0.683 | 0.686 | 0.798 | 0.832 | **0.922** | **0.887** | 0.735 | 0.697 | 0.703 | 0.635 | 0.686 | 0.672 | 0.678 |

**There is no plateau.** Moving the cap ten bars either side of the frozen value swings net by more than a
basis point a bar and Sharpe from 0.735 to 0.922 — a range comparable to the whole gate-rotation null. The frozen
252 is not even the local maximum; 242 is. A parameter whose neighbours disagree this much is riding noise, and the
+8.09 headline should be read as one draw from a jagged surface rather than as the value of a chosen constant.

### AMENDMENT, 2026-09-07 — the cap is a declared constraint, not a fitted parameter

**The principal has ruled that the 252-bar cap stays as it is, and why: a hold approaching a full year is already
at the limit of what is comfortable, and lengthening it would need a strong reason that does not exist.**

This changes how §6 should be read. The jagged sweep was written up as evidence that the cap is riding noise, and
that reading holds *only* if the cap is claimed to be an optimum. It is not. Under this declaration the cap is a
**constraint the strategy is given** — the longest tolerable holding period — and the fact that 242 scores higher
is irrelevant rather than awkward, because 242 was never a candidate on its own merits and would not have been
adopted had it won by more. What §6 still establishes, and what remains worth carrying, is that **the +8.09
headline is one draw from a jagged surface**: it is a fair number for the declared constraint, not evidence that
252 bars is a discovered horizon.

No number in this record changes. D367 does not tune the cap.

## 7. Assertions

All pass; `--selftest` runs in 3 s. Building `[ID]` as an *exact* identity rather than an approximate one exposed
two defects in the search's own probe, both recorded rather than smoothed over:

- **The probe hedged entry bars on the wrong leg** — it filled the long leg at the next open but held the hedge
  close-to-close on the same bar, a leg mismatch worth 2.41 bp/bar on entry bars. The frozen construction hedges
  open-to-close on both legs as pre-registered. `[ID]` reproduces the probe's arithmetic exactly (net +8.098,
  Sharpe 0.8875, maxDD 3023.7, 988 trades, 24.53 names, 90.79% shut) so the identity is a bit-level fact.
- **The rounded rebalance charge**, whose effect on the drawdown is §1's knife-edge.

A third question the identity settled: eligibility already carries a finite return, so whether NaN-return names sit
in the hedge's weight denominator is a distinction without a difference — asserted across the whole grid, which is
what leaves the entry-bar leg as the only real difference from the probe.

`[GATE]` `[HEDGE]` `[COST]` `[LAG]` `[CAP]` `[S]` `[ROT]` `[A′]` `[GATE-ROT]` `[C]` all hold, and `[6]` shows eight
of them raising on deliberately broken input.

**Two probes that proved nothing and were replaced, recorded because a self-test that cannot fail is worse than
none:**

1. The first causality probe multiplied one already-high volatility observation by 100 and asserted the expanding
   80th percentile moved. It did not, correctly — scaling a value already above the threshold leaves its *rank*
   alone. Replaced by one that overwrites **every** bar from 2022-04-04 onward and asserts all 3,085 earlier
   thresholds are bit-identical while all 1,102 later ones move.
2. The first jackknife passed a grid of zeros as its return grid, so every name scored +0, the "top ten" were the
   first ten alphabetically, and the ex-GME column never dropped GME — the two columns matched exactly and that
   was nearly read as evidence the cap was robust to it. Now asserts the ledger carries non-zero P&L and that
   dropping GME changes the eligibility grid.

## 8. Status

**The avenue is the principal's (R15). Nothing here closes anything and nothing is promoted. Book: empty.**

Against the pre-registration's own stop conditions: **Q1 and Q2 both hold, so by §4 of the pre-registration the
construction survives its own search**, and the named next step is a separate pre-registered out-of-sample design
that does **not** touch D357's frozen holdout read.

Three facts belong beside that verdict, and they are the reason this record does not read as a clean pass:

1. **Half the gating is shape, not timing** — a randomly-placed gate of the same on-share earns +4.10 of the +8.09.
2. **The margin over that random gate is ten names.** Drop the top ten of 515 and the book returns +4.60, the
   random gate's median. Q4 was falsified in the same direction.
3. **The cap is riding a jagged surface**, and the frozen value is not its local maximum.

None of the three is a reason the trigger is unreal — ROT and A′ settle that, decisively and in the construction's
favour. They bear on how much of the *elaboration* survives, and on what an out-of-sample test would need to be
powered to detect.

## 9. Files

`docs/decisions/D366-the-gated-momentum-buffer-against-its-nulls.md` (pre-registration) ·
`scripts/run_d366_gated_buffer.py` (stages `--selftest`, `--null ARM --draws N --part p`, `--jackknife`,
`--report`) · `data/d366_null_{ROT,APRIME,GATEROT,LADDER,C}_p0.json` · `data/d366_gated_buffer.json` ·
`data/d366_jackknife.json`. Reuses `scripts/d348_prep.py`, `scripts/run_d365_momentum_buffer.py`,
`scripts/run_d358_flat_sleeve.py`, `scripts/run_d350_long_timing_screen.py`, `scripts/d365_export_trades.py`.
The holdout fixture is not read; `[HOLDOUT-GUARD]` audits 261 file opens per process and refuses the probe.
