# D424 RESULT — on the cell that pays, every ATR exit forfeits, and the take profit is negative too

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D424-RESULT-on-the-cell-that-pays-every-ATR-exit-forfeits-and-the-target-is-now-negative-too.md`. The H1 above is the full title.*

**FAILS THE BAR on T1 and T2.** Pre-registration `05e95df` predates the runner and this file (R8).
**The ledger does not move. Nothing was admitted. No holdout was read.** Daily bars.

Cost: 457 s (15 books in 3 s; 600 control books on 8 processes).

```
[X]     D417's cell-2 TP 2.0 line reproduces before the restriction: +32.43, +2.17, 22.1%
[FILL]  every stop at or below its trigger, every target at or above (D417's assertion)
[P2]    D419's FIXED on the pool == D422's ANY-REQ book, bit for bit
[RECON] all 15 books;  [CHUNK];  [NUISANCE] control runs 4.30 / 3.83 / 4.62 == the rules'
```

---

## 1. The bar — TP 2.0 on ANY ∧ cell 2 (9,411)

```
T1  paired delta vs FIXED         -2.72 ± 2.27 bp    -1.2 SE     FAIL
T2  book net delta vs FIXED       -0.270 ± 0.420     -0.6 SE
    book net vs sampled-runs      +0.966  vs  p50 +0.664  p95 +1.312 (±0.027)   -12.9 SE   FAIL
```

---

## 2. THE GRID — D417's ten rules, each alone, on this cell

```
                PAIRED     SE    early   hold    bp/d    win    would-have   filled-at   forfeit
FIXED           +44.84     —       —     5.00   +8.97   52.4%
SL 1.0         -15.42   -4.0   47.9%    3.71   +7.93   42.2%     -290.10     -322.31    -32.21
SL 1.5          -8.56   -3.1   31.2%    4.28   +8.48   48.5%     -438.02     -465.46    -27.44
SL 2.5          -5.42   -2.7   12.5%    4.77   +8.27   51.5%     -686.71     -729.89    -43.18
TS 1.0         -28.00   -5.9   84.7%    2.90   +5.82   40.0%      -38.80      -71.85    -33.05
TS 1.5         -12.29   -3.5   58.4%    3.80   +8.56   44.7%     -176.31     -197.36    -21.04
TS 2.5          -6.40   -2.7   23.1%    4.62   +8.33   50.2%     -439.64     -467.33    -27.69
TP 1.0          -6.44   -1.7   53.1%    3.58  +10.72   62.1%     +350.56     +338.45    -12.12
TP 2.0          -2.72   -1.2   23.0%    4.58   +9.20   53.6%     +643.82     +631.99    -11.84
TP 3.0          -1.48   -1.0    8.8%    4.87   +8.90   52.6%     +943.81     +926.91    -16.90
SL+TP          -11.33   -3.2   52.5%    3.88   +8.64   49.6%      +14.47       -7.12    -21.59
```

**Ten rules, ten negative deltas, and every forfeit is negative — including the targets.** On the
base cell 2 (D417) `TP 2.0` was the one family with a positive delta (+2.17), because the trades
that reached 2 ATR gave back nothing afterwards (+9.83 forfeit). **On this cell the trades that
reach 2 ATR go on to make 12 bp more; at 3 ATR, 17 more.** D423 found 28 at 3.2 ATR on the
swing. Same law: **the forfeit scales with the distance, because on the cell that pays, the
trades that reach a level are the ones still moving.** The stop is D417's mechanism exactly —
trades cut at −1.5 ATR would have recovered 27 bp by `t+5` — and it is worse here because the
cell's losers recover more than the base cell's did (−27 forfeit against D417's −35 on cell 2 all,
but on a cell whose fixed exit is 44.84 rather than 30.26).

**The win rate is not the money.** `TP 1.0` lifts it from 52.4% to 62.1% and costs 6.44 bp a
trade; `TS 1.0` cuts it to 40.0% and costs 28. The principal asked in D413 whether the win rate
could be raised: it can, at a price, by taking profits early, and it buys nothing.

**By side:** `TP 2.0` long +0.09 (forfeit +0.36 — the long reachers stop), short −6.10 (forfeit
−29.65 — the short reachers keep going). `SL 1.5` long −9.59, short −7.31. **The long side of this
cell is the side on which a target is at least harmless; the short side is the side on which
nothing but the clock works.**

---

## 3. THE BOOK — the target holds gross and loses the turnover

```
cell-2 ANY-REQUIRED, 10 slots   gross     net     cost    util    run    early   per trade   net by seed
FIXED                          +4.889  +0.993   3.896   68.2%   5.00    0.0%    +35.85     +0.99 +1.51 +1.20
SL                             +4.114  -0.205   4.319   64.8%   4.30   30.8%    +27.30     -0.21 +0.00 -0.23
TS                             +3.913  -0.641   4.553   60.8%   3.83   58.0%    +24.63     -0.64 -0.40 -0.37
TP                             +4.991  +0.934   4.057   65.6%   4.62   21.0%    +35.15     +0.93 +1.12 +0.85
SLTP                           +4.117  -0.375   4.492   61.6%   3.92   51.2%    +26.23     -0.38 -0.04 -0.16

deltas vs FIXED               gross     NET
SL                           -0.963   -1.380 ± 0.536   -2.6 SE
TS                           -1.061   -1.705 ± 0.694   -2.5 SE
TP                           -0.121   -0.270 ± 0.420   -0.6 SE
SLTP                         -0.853   -1.427 ± 0.643   -2.2 SE

sampled-runs controls        rule net    p50      p95        margin
SL                           -0.143    +0.380   +0.958     -37 SE   worse than random exits at its turnover
TS                           -0.469    -0.120   +0.659     -35 SE   worse than random
TP                           +0.966    +0.664   +1.312     -13 SE   better than random, not by enough
```

**The stop and the trail are worse than random exits with the same turnover** — D419's finding
on the full pool, reproduced on the required one: a stop chooses *which* trades to forfeit and
chooses the ones about to recover. **The target is better than random and cannot pay its
turnover:** gross per bar +4.991 against FIXED's +4.889 at seed 419 (the swap premium is +20.8 ±
25 on 893 swaps), the extra 0.16 bp/bar of cost takes it back, and the mean over seeds is −0.27.
Utilisation falls under every rule — D423's thin-pool fact again: a freed slot on 2.25 events a
day idles.

---

## 4. Predictions — five of five

| | prediction | outcome |
|---|---|---|
| X-a | TP 2.0 −4..+3 inside 2 SE; fires 18–26%; forfeit −5..−20 | −2.72 (−1.2 SE); 23.0%; −11.84 |
| X-b | SL 1.5 −8..−18, 28–36%; TS 1.5 −10..−20, 55–65% | −8.56, 31.2%; −12.29, 58.4% |
| X-c | TP 1.0 win > 58%, delta inside 2 SE | 62.1%, −6.44 (−1.7 SE) |
| X-d | TP book gross −0.5..+0.3, util < 68.2, net inside 2 SE, above ctrl p50, below p95 | −0.121, 65.6%, −0.6 SE, +0.30 above p50, −0.35 below p95 |
| X-e | SL, TS books negative by > 2 SE | −2.6, −2.5 |

Every prediction was arithmetic on D417 and D423's forfeit scaling, and every one held. **This is
what the line looks like when it has learned its own mechanism: nothing here was a surprise, and
the study was worth running only because the principal needed the answer on this cell, not the
base one.**

---

## 5. What this leaves

1. **Seven exit constructions, none beats `t+5` with nothing** — ATR stop, trail, target and
   their combination (D417, and now on this cell), the zone as a stop (D418, D423), structure
   targets (D423), the target through the book (D419, and now on this cell).
2. **On the cell that pays, even the target forfeits.** D417's "the target forfeits nothing" was
   a property of the base cell, not of targets.
3. **The short side is where every exit hurts most and the long side is where a target is
   harmless** — consistent with D422's trade shapes (long: median above mean; short: carried by
   the tail). An exit study restricted to the long side would be a different study, and this
   record does not run it.
4. The entry rung is untouched; D422 §7 item 2 stands.

**Disposition is the principal's.**

---

## 6. R13

Twenty-fourth look by object on price levels. No new data spent.

**Evidence:** `data/d424_atr_exits_cell.json`. Runner `scripts/run_d424_atr_exits_cell.py`
(D417's walker and D419's simulator, unchanged, on the cell).
