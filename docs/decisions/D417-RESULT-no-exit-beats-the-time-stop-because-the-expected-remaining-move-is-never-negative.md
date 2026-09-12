# D417 RESULT — no exit beats the time stop, because inside the hold the expected remaining move is never negative

**FAILS THE BAR in all three families.** Pre-registration `962c8c8` predates the runner and this
file (R8). **The ledger does not move. Nothing was admitted. No holdout was read (the principal's
standing decision). 2024+ on the 15m fixtures was not read.** D413's 180,050 / 26,024 and D414's
3,023 reproduce exactly (P1).

Cost: five seconds.

---

## 1. The bar — daily arm, pooled, primary parameters

```
                 rule     PAIRED vs fixed      SE    early   hold    bp/day   std     max loss
fixed exit     +13.21          —               —       —    5.00d   +2.64   ×1.00    -23,236
SL 1.5          +8.13    -5.08 ± 0.69       -7.4   31.9%   4.30d   +1.89   ×0.89    -22,715   T1 FAIL
TS 1.5          +7.09    -6.13 ± 0.89       -6.9   59.4%   3.81d   +1.86   ×0.81    -17,483   T1 FAIL
TP 2.0         +14.25    +1.04 ± 0.55       +1.9   20.9%   4.62d   +3.08   ×0.93    -23,236   T1 FAIL
```

**The stop costs 38% of the edge and buys an 11% reduction in standard deviation. The trailing
stop costs 46% and buys 19%. The take profit is a wash — +1 bp, just under the gate.** Nothing
improves the mean per trade, which was the gate, and the gate is the right one: the cost per round
trip is unchanged by any of these, so a lower mean is a lower coverage.

**And the stop did not cap the worst case.** The fixed exit's largest loss is −23,236 bp — a short
squeezed tenfold; the 1.5-ATR stop's is −22,715. **A stop cannot protect against a gap**, which is
where the tail lives; it only protects against the losses that arrive slowly, and §2 says those
tend to come back.

---

## 2. THE MECHANISM, in one number per family

The paired delta is zero on every trade the rule held to `t+5`, so it lives entirely on the trades
the rule exited early — and on those, two numbers say everything: what the fixed exit **would**
have delivered, and what the rule **actually** filled at.

```
                       would have (fixed)     actually filled (rule)     difference
SL 1.5   31.9% early       -463.58 bp              -479.5 bp                -16    the stop is a wash that
                                                                                   gap-fills slightly worse
TS 1.5   59.4% early       -192.83                 -203.2                   -10
TP 2.0   20.9% early       +631.01                 +636.0                    +5    the target forfeits nothing
```

**Trades that fell to the stop went on to recover, on average, 16 bp by `t+5`** — so the stop
forfeited a small positive expectation and paid gap-through fills on top. **Trades that reached
the target gave back nothing after it.** Neither rule found a state inside the hold where the
expected *remaining* move was negative, because **there isn't one**: ADDENDUM 3's marginals are
positive through bar 5 unconditionally, and this study says they stay non-negative *conditional
on being 1.5 ATR down* and *conditional on being 2 ATR up*. **Any early exit forfeits a
non-negative expectation, and a stop forfeits it while paying for the gap.**

That is the same fact D414–D416 found about entries, seen from the other end of the trade: the
path from the touch-day close has no conditional structure that timing can exploit. It rises,
on average, in every state, until it stops rising at bar 5 — **and bar 5 is where the fixed exit
already is.**

---

## 3. The rules, all of them — and the CLAUDE.md warning made concrete

```
                rule    PAIRED      SE    early   hold   bp/d   std    win%     would-have   filled-at
SL 1.0         +6.33   -6.88     -7.8   49.1%   3.70   1.71   ×0.81   40.9%     -314.66     -328.7
SL 1.5         +8.13   -5.08     -7.4   31.9%   4.30   1.89   ×0.89   47.1%     -463.58     -479.5
SL 2.5        +11.01   -2.20     -4.6   12.6%   4.78   2.30   ×0.95   50.1%     -749.78     -767.2
TS 1.0         +3.03  -10.18     -9.4   85.3%   2.90   1.05   ×0.69   38.9%      -64.78      -76.7
TS 1.5         +7.09   -6.13     -6.9   59.4%   3.81   1.86   ×0.81   43.2%     -192.83     -203.2
TS 2.5        +10.02   -3.19     -5.4   23.1%   4.64   2.16   ×0.92   49.1%     -465.74     -479.5
TP 1.0        +14.10   +0.89     +1.0   50.8%   3.67   3.84   ×0.81   60.4%     +331.74     +333.5
TP 2.0        +14.25   +1.04     +1.9   20.9%   4.62   3.08   ×0.93   52.0%     +631.01     +636.0
TP 3.0        +14.03   +0.81     +2.1    8.0%   4.88   2.88   ×0.97   51.0%     +930.08     +940.2
SL+TP          +8.63   -4.58     -5.3   51.3%   3.94   2.19   ×0.83   48.3%      -37.83      -46.8
fixed         +13.21      —        —       —    5.00   2.64   ×1.00   50.9%
```

**TP 1.0 lifts the win rate from 50.9% to 60.4% and changes the mean by +0.89 bp — inside its own
noise.** That is *"a tighter exit raises the win rate while lowering the mean"* measured: nine
points of win rate for nothing. In cell 2 it is 61.9% at **−0.26 bp**.

**Every stop is monotone in its distance**: tighter is worse, at every step. **Every trailing stop
likewise**, and TS 1.0 — which exits 85% of trades early — gives up 77% of the edge for a 31%
reduction in standard deviation, the largest variance cut on the table at the largest price.

**TP 3.0 prints +2.1 SE and is shape.** It is 0.81 bp on 8% of trades, one of nine cells, and it
cannot clear (R14) — and it would be a poor thing to clear on: a target that fires on one trade in
twelve and adds four fifths of a basis point is not a rule, it is a rounding.

---

## 4. Cell 2 — the declared secondary

```
                rule    PAIRED      SE    early   bp/d   std    would-have   filled-at
fixed         +30.26      —        —       —     6.05   ×1.00
SL 1.5        +19.42  -10.84     -6.2   31.2%   4.53   ×0.91    -439.04     -473.8
TS 1.5        +17.16  -13.10     -6.0   58.6%   4.51   ×0.84    -181.52     -203.9
TP 2.0        +32.43   +2.17     +1.7   22.1%   7.06   ×0.94    +617.19     +627.0
```

**X-f was right about which family and wrong about whether it clears:** TP 2.0 is the only family
with a positive delta in cell 2, at +1.7 SE, and it does not clear. It raises bp per day from 6.05
to 7.06 by shortening the hold on the trades that hit — **edge per unit time up, edge per trade
flat, cost per trade unchanged**, which is CLAUDE.md's *"say which moved"* answered: the time
moved, the money did not.

**The stop in cell 2 forfeits 36% of the edge for a 9% cut in standard deviation**, and the
stopped trades recovered 35 bp on average after the stop — twice the pooled figure, because cell
2's bounce is stronger.

---

## 5. The 15m arm — a precision check, and it behaved like one

**The 15m sample's fixed exit is −8.89 bp** (the signal is not visible on 32 names from 2018, as
D414 said), so every early exit there is positive — cutting exposure to a losing book helps — and
none is significant (largest +1.7 SE). **That is exactly why the arm carries no gate.**

The precision question was answered on the same events, paired:

```
             15m minus daily-bar     SE     early 15m / daily    sign agrees
SL 1.5            +0.79 ± 0.47     +1.7      34.2% / 34.3%          yes
TS 1.5            -4.45 ± 1.96     -2.3      63.4% / 62.1%          yes
TP 2.0            +0.64 ± 0.55     +1.1      21.7% / 21.8%          yes
```

**Intraday triggering changes fill prices by under a basis point for stops and targets, and
changes no answer.** The one significant difference is the **trailing stop, 4.45 bp *worse* at
15 minutes**: a trail updated 26 times a day is a tighter trail, and a tighter trail is whipsawed
more. X-e held on all three.

**The fixed-exit maximum loss on this arm is −5,816 bp against −23,236 on the full universe** —
the 32 survivor large caps do not contain the tail the daily arm does, which is another way of
saying what the arm cannot see.

---

## 6. Stage 0

- **P1** — every count reproduced. 111 of D414's 3,023 events lack a full five-session 15m path
  (holidays inside the hold) and are dropped, counted.
- **P2** — the primaries fire across the whole hold, not on day 1: SL 1.5 by day `21/25/22/18/14%`,
  TP 2.0 `12/21/24/23/21%`. A stop that fired 90% on day 1 would be a different object; this one
  is a stop.
- **`[FILL]`** — every stop at or below its trigger, every target at or above, in both arms and on
  the daily-bar twin. **`[SIGN]`** — a long stop losing where the fixed exit won, a target beating
  the fixed exit on a give-back path, the short mirror exactly, and **a gap through the stop filling
  at the open**, all asserted before any data was read.
- **P4** — UFS, 2010-05-05, long, entry 34.59: **stopped on day 1 at 32.09, −750 bp**, the flash
  crash; the fixed exit finished **+175**. The stop got run over by the one-day gap and the trade
  came back, which is §2 in a single name.

---

## 7. Predictions

| | prediction | outcome |
|---|---|---|
| X-a | SL fires 20–35% | correct — 31.9% |
| X-b | T1(SL) fails; std falls > 20% | **gate right, size wrong** — −7.4 SE, but std ×0.89, an 11% cut |
| X-c | T1(TS) fails | correct — −6.9 SE |
| **X-d** | **T1(TP) fails; the target clips the winners** | **gate right, mechanism wrong** — it fails at +1.9 SE, but the trades that hit the target gave back *nothing* (+631 → +636). The target is neutral, not harmful |
| X-e | 15m agrees in sign on all three | correct — 3 of 3 |
| X-f | cell 2: TP closest to clearing | correct — the only positive family, +1.7 SE, does not clear |

Five gates of five called; two mechanisms wrong in the same direction — **I overestimated how much
any exit does at all.** The stop cuts less variance than predicted and the target harms less than
predicted, because the path inside the hold has less structure than either rule assumes.

---

## 8. What four execution studies have established

| question | answer | record |
|---|---|---|
| enter before the close? | no — the intraday continuation is still running (−35 bp in cell 2) | D414 |
| enter on an intraday confirmation? | no — every pattern is a worse price than the clock it waits through | D415 |
| enter after the close, on a stall? | no — the bounce is front-loaded and the up-day is the worse price | D416 |
| exit before `t+5` on a stop, trail or target? | **no — the expected remaining move is never negative inside the hold** | **D417** |

**Entry at the touch-day close, exit at the close of `t+5`, nothing in between.** That is D413's
trade exactly as it was declared, and four studies from four sides have failed to improve on
either end of it. **The execution question on this construction is closed by measurement, not by
assumption**, and the thing execution cannot supply — a signal large enough to clear its cost on
a population that can be traded — is where the line stands.

**For the principal's judgement, the one trade-off these rules do offer:** SL 1.5 gives up 38% of
the mean for 11% less standard deviation and no protection against the gap; TS 1.0 gives up 77%
for 31%. Neither is a rule this record would carry, but the prices are printed.

**Disposition is the principal's.**

---

## 9. R13

Seventeenth look by object; fourth on execution; no new data spent.

**Evidence:** `data/d417_exits.json` — every rule, both arms, the daily-bar twin, the precision
pairing, and for every rule the fixed-exit and rule returns on the same early-exited trades.
Runner `scripts/run_d417_exits.py`: one walking function over `(events × bars)` serves both arms,
so the daily-bar rules on the 15m events are the same logic as the daily arm and not a second
implementation.
