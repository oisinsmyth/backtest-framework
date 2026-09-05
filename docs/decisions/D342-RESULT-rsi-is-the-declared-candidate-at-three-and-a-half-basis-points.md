# D342 RESULT — `rsi` is the programme's declared candidate, at three and a half basis points a bar

**Status:** RESULT. Pre-registered at `20ebdb0`, runner at `b8661e1` — both before this
file existed (R8). D333 panel, D334 cache, F0, the declared floor (replace), the open
fill, PUB primary.
**Date:** 2026-09-05
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted. Book: empty. The out-of-sample design is written and not run.**

---

## 1. The verdict, then the book

**Q1 and Q2 hold.** `rsi` symmetric at k=20, under the deal filter, the universe floor
and a next-open fill, orders the liquid gate above **all 24** rotations on gross bp/bar
(+14.72 against a null maximum of +14.64 — by a hair) and above all 24 on net Sharpe
under the published spread convention (+0.181 against a maximum of +0.149; the
matched-cost null's p95 is −0.034, so a random four-name book from the same gate does
not pay its cost and `rsi`'s ordering does). By this record's letter it is **the personal
track's declared candidate**, frozen at these parameters. The out-of-sample design is in
§6 and is not run.

**What is being declared:** +3.52 PUB bp/bar, +3.32 after GC+HTB borrow, a net Sharpe of
0.18 on a book with 308 bp/bar of volatility, eight of fourteen years net-positive,
fourteen names to half the P&L, a top trade of 5.5% that is an eighteen-bar decline in a
liquid biotech, and **−4.8 bp a trade on the invariant lens with both legs negative**.
That last number is the one to hold onto: every candidate trade, uncapped, loses money
after cost; the book earns because the slot cap takes the two most extreme of twenty-five
per side. The edge is the concentration, as D300 found it was, and it is 3.5 bp a bar.

## 2. Group 1 — identities to D341, and what was new

| `rsi` F0 k=20, floor, open fill | PB | **PUB** |
|---|--:|--:|
| gross / cost / **net** bp/bar | +14.72 / 6.19 / +8.53 | +14.72 / 11.20 / **+3.52** |
| **after GC+HTB** (0.201 bp/bar; HTB 0.2% of short bars) | +8.33 | **+3.32** |
| after house 300 | +7.34 | +2.33 |
| vol bp/bar | 307.8 | 307.8 |
| gross / net Sharpe | +0.759 / +0.440 | +0.759 / **+0.181** |
| gross t | +2.70 | +2.70 |
| annualised net | +21.5% | **+8.9%** |
| maxDD bp | 13,907 | 13,907 |
| exposure / fill / turnover | 76.1% / 100% / 0.0956 | |
| held ½-spread / price / $vol | 15.0 bp / $44 / $45.5M | 28.1 bp / $44 / $45.5M |
| 2c / mean move / ratio | 32.4 / +76.1 / 2.35× | 58.6 / +76.1 / **1.30×** |
| **breakeven ½-spread** | 37.3 = 2.48× | 37.3 = **1.33×** (Q8 ✓) |
| invariant PUB per trade: long / short / both | | **−7.9 / −1.6 / −4.8** |
| implementation-lag premium per entry, long / short | | +0.7 (t 0.08) / −7.7 (t −0.79) |

**Q5 falsified**: the short leg is the better one per trade (−1.6 against −7.9), the
reverse of D335's unfloored reading, on near-identical gross (+50.2 against +49.1). The
floor and the fill changed which leg carries. Neither carries much.

## 3. Group 2 — the trade distribution

| | |
|---|--:|
| trades | 1,215 |
| mean / **median** bp | +76.1 / **+221.3** — mean below median |
| win rate / payoff | 72.0% / 0.51 |
| hold mean / median | 10.5 / 8 bars |
| skew / kurtosis | **−1.69** / 17.2 |
| ex-top / ex-bottom / **trimmed** | +46.2 / +118.0 / **+88.3** (1.51× the 58.6 round trip) |
| top 1% / bottom 1% share of P&L | +40% / **−54%** |
| top-1% mean / bottom-1% mean | +3,065 / **−4,126** |

**The left tail does the work**, more than on any book before it: negative skew, the
bottom twelve trades larger than the top twelve, a payoff of 0.51 carried by a 72% win
rate. The twelve worst trades are MSTR 2021-01-11 (−7,725 bp, a short squeezed in the
bitcoin run), SMCI 2024-02-05 (−6,644, the same shape), FGP, TK, HTZ 2026, VSLR, FNKO
twice, RGS, EGO, SAGE, LM. **Q4 confirmed, against**: `rsi`'s and `retrace_leg`'s bottom
twelve share **two** names (EGO, TK); the two books lose on different events.

## 4. Group 3 — what the winners depend on (PUB)

| | |
|---|--:|
| names traded / **names to half** | 627 / **14** |
| top 1 / 5 / 10 name share | 6.8% / 25.2% / 41.6% |
| years net-positive / gross-positive | **8 of 14** / 12 |
| dead names' share of P&L (of trades) | 12.1% (21.8%) — dead names lose 27 a trade |
| eras, first / second half | 41.8% / 58.2% (Q6 ✓) |
| price low / mid / high | **62.0%** (+74.7 a trade) / 14.2% (−26.1) / 23.8% (−3.2) |

PUB net by year: 2013 −16 · 2014 +10 · 2015 +12 · 2016 −6 · 2017 −2 · 2018 +24 · **2019
−31** · 2020 −2 · 2021 +3 · 2022 +19 · 2023 +2 · 2024 −3 · 2025 +11 · 2026 +11. Eight of
fourteen positive; the yearly numbers are noise around +3.5. **The cheapest tercile of a
floored universe — $5 to $28 — is 62% of the P&L and the only tercile that pays its own
cost.** The floor moved the price story, it did not remove it.

### The top five, and the top trade's bars

| | side | entry | hold | P&L bp | share | biggest day r1 = raw | max div/close | as-traded | DV pct |
|---|---|---|--:|--:|--:|--:|--:|--:|--:|
| **FPRX** | short | 2020-11-13 | 18 | +5,090 | 5.5% | −12.4% | 0 | $22.43 | 0.58 |
| ACH | long | 2025-02-19 | 8 | +4,288 | 4.6% | +39.0% | 0 | $7.01 | 0.32 |
| EBS | short | 2024-07-15 | 18 | +4,115 | 4.5% | −42.0% | 0 | $10.65 | 0.48 |
| **NBIS** | long | 2024-10-21 | 1 | +4,100 | 4.4% | +5.6% | 0 | $18.94 | **NaN** |
| CHK | long | 2020-04-21 | 1 | +3,091 | 3.3% | +23.6% | 0 | $14.38 | 0.55 |

Every big day equals its raw close move to the digit; no dividend touches any hold; every
as-traded price is above $5. **Q3 fails on one clause: NBIS has no dollar-volume
percentile at entry.** 2024-10-21 is the day the former Yandex relisted as Nebius after
an eight-month halt; the trailing-63 dollar-volume mean has fewer than 21 observations,
so it is NaN, and D320's rule — *a name with no estimate is never excluded* — passed it
through the floor. The rule exists so the filter cannot become a liveness proxy; here it
let a name with no recent tape into a liquidity-floored universe. **The floor has a hole
at re-listings and the stop condition says so**: a pre-registered amendment (a name needs
its 21 observations to pass) is owed, and this trade is 4.4% of the book.

The top trade: FPRX short for eighteen bars, entered the day after Five Prime's +24.6%
day at $22.43 on 22 million shares, held through a steady decline to $15.30 with the
biggest day −12.4% at the end. Open-to-close and close-to-close agree on every bar; the
entry bar's open-to-close was −6.3% against −4.5% close-to-close, so the open fill
*helped* this one. A real trade in a liquid name.

## 5. Group 4 — the null, resolution stated

| statistic | score | p50 | p95 | max | above k of 24 |
|---|--:|--:|--:|--:|--:|
| gross bp/bar | **+14.72** | +5.64 | +11.65 | +14.64 | **24 of 24** |
| gross Sharpe | +0.759 | +0.324 | +0.643 | +0.909 | 23 of 24 |
| net Sharpe PB | +0.440 | −0.023 | +0.347 | +0.667 | 23 of 24 |
| net Sharpe PUB | **+0.181** | −0.383 | −0.034 | +0.149 | **24 of 24** |

24 of 24 distinct shifts drawn. The gross margin over the best rotation is 0.09 bp/bar;
on gross Sharpe one rotation beats the cell. "Above all 24" is the ceiling of this null
and the cell reaches it on the two statistics the record named, narrowly on one.

## 6. The out-of-sample design — written, not run

The cell, frozen: `rsi` symmetric, depth 2, k=20, D303 target at 0.9627, F0 forms and
189-bar window, the floor as declared (as-traded close ≥ $5 at t−1, dv28 pass, replace
semantics, **plus the 21-observation requirement once pre-registered**), the open fill,
PUB with GC+HTB. A fixture disjoint from this one in names or time; `us_shorts_daily_
holdout` exists and has never been read. Predictions to declare before the read: PUB net
> 0 after borrow; gross above its own rotation null's p95 with p95 > 0; symmetric trim
above the round trip; no trade above 10% of the ledger; at least 10 names to half. Any
failure retires the cell.

**Is the read worth spending?** Stated plainly, as the pre-registration requires: this is
a 0.18-Sharpe book whose annual nets are noise around +3.5 bp/bar and whose every trade
loses money uncapped. On a holdout of a few years it cannot be distinguished from zero,
and the holdout has one read. **This record recommends against spending it now**, and
names what would change the recommendation: a null with more than 24 values that the
cell still clears, and the re-listing hole closed. Both are owed before the read, not
after. The decision is the principal's.

## 7. Predictions

| | | outcome |
|---|---|---|
| **Q1** | *(load-bearing)* gross above null p95, teeth, ≥ 22 of 24 | **CONFIRMED** — 24 of 24, margin 0.09 |
| **Q2** | net Sharpe PUB above the matched-cost null's p95 | **CONFIRMED** — 24 of 24 |
| **Q3** | top five: no dividend, r1 = raw, ≥ $5, DV pct > 0.28 | **FALSIFIED** on one clause — NBIS has no DV estimate at its re-listing |
| **Q4** | *(against)* left tails share < 4 names | **CONFIRMED** — 2 (EGO, TK) |
| **Q5** | long leg per trade > short leg | **FALSIFIED** — −7.9 vs −1.6 |
| **Q6** | *(against)* no era half > 65% | **CONFIRMED** — 41.8 / 58.2 |
| **Q7** | GC+HTB < 0.5, PUB after > +3.0 | **CONFIRMED** — 0.201, +3.32 |
| **Q8** | breakeven ≥ 1.3× held PUB half-spread | **CONFIRMED** — 1.33× |
| *check* | D341's numbers for the cell reproduce | to 0.0 |

Six of eight.

## 8. Stop conditions, executed

- **Q1 and Q2 hold → `rsi` is the declared candidate; the OOS design is written (§6) and
  not run; this record recommends against spending the read now and says why.** Book:
  empty.
- **Q3 fails on liquidity → the floor has a hole**: D320's missing-estimate rule passes a
  name with no recent tape at a re-listing. Owed as a pre-registered amendment to the
  universe definition; NBIS is 4.4% of this book.
- **Q5 fails** → the leg asymmetry D335 found on the unfloored universe does not survive
  the floor and the fill; recorded, and the "long leg carries `rsi`" reading is withdrawn.

## 9. Deviations and a found defect

- **D341's [R] floor-share check could not fail.** Building this runner, the same check
  raised `KeyError` on a census key that does not exist; D341's version had fallen back to
  the value under test, so it compared the share to itself. The printed 29.2962% was right
  (D339 recorded the identical number under `floor.census_c`), and the check was vacuous.
  Fixed in `af93eef` before this runner was committed; both runners now read D339's
  `census_c` and raise on a missing key. A self-test that cannot fail is worse than none
  (CLAUDE.md), and this one was found only because a second runner tripped on the key.
- NBIS's DV percentile prints as NaN rather than a number; the runner reports it and Q3
  reads NaN as a failure of the `> 0.28` clause, which is the honest reading.

## 10. Assertions

| | |
|---|---|
| **[K]** | cache key with `ragged_panel.py`; npz newer than the builder |
| **[F0]** | 1,719 filings, 2.54% |
| **[R]** | raw factor == census factor on the full grid; floor fails 29.2962% == D339's `census_c` |
| **[F]** | 0 of 4,137,239 priced cells lack a usable open |
| **[1]** | `rsi` floor/open reproduces D341 to **0.0** on net and Sharpe under both conventions, invariant per trade, trimmed mean, both tail shares, names to half, top-5 share, years and dead share; `retrace_leg` floor/open net too |
| **[A]** | the floored `rsi` long gate rebuilt from the floored score at t−1 equals the gate on 200 of 200 sampled bars; the unlagged rebuild differs on 200 |
| **[S]** | every trade equals the open-fill recomputation to 1.1e-16; favourable excess paths pay positively on every long and short |
| **[RQ]** | same 1,215 entries under compound accumulation, 1,100 P&Ls differ; group 1 scores the summed ledger |
| **[2]** | 1,215 trades reconstruct gross to −0.23 bp; 4 open at T, no hole; rejects a ledger missing a trade |
| **[3]** | symmetric trim, k=12; rejects one deeper |
| **[N]** | rotation moves gross +14.72 → −3.75; 200 of 200 draws valid, 24 distinct shifts |
| **[B]** | borrow reconciles to 3.6e-12; `net_bp` untouched |
| **[U]** | `rsi` lies in [0.8, 100.0]; unchanged when every price is multiplied by 10 |
| **[6]** | raises on +5 bp handed |

**Speed:** 61 s including the null (3 s).

## 11. What this establishes

1. **The programme has a declared candidate for the first time, and it is +3.5 bp/bar
   after every convention it owns.** `rsi` under the deal filter, the dividend bound, the
   published spread, the universe floor, a next-open fill and borrow, above all 24
   rotations of its gate on gross and on net Sharpe. Sharpe 0.18.
2. **Every one of its trades loses money uncapped.** The book earns through the slot
   cap's selection of the two most extreme names per side. A candidate whose per-trade
   lens is negative is a statement about concentration, and about how little is left.
3. **The floor leaks at re-listings.** A name with no trailing dollar-volume estimate
   passes because a missing estimate never excludes; NBIS's relisting day is 4.4% of the
   book. The universe definition needs the 21-observation clause; pre-registered next.
4. **The two candidates lose on different names.** Two of twelve shared in the left
   tails. If either were ever traded, the other would diversify its tail.
5. **A check that cannot fail was found by writing the same check twice.** D341's [R]
   compared a number to itself for one commit. The second runner tripped on the key the
   first had silently defaulted around.

## 12. Files

`data/d342_rsi_candidate.json` · `scripts/run_d342_rsi_candidate.py` ·
`scripts/run_d341_floor_and_open_fill.py` (the [R] fix, `af93eef`)
