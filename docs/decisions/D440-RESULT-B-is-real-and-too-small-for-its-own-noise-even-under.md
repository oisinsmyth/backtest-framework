# D440 RESULT — B is real and too small for its own noise: even under the passive line the book is +0.65 a bar with an SE of 0.89

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D440-RESULT-B-is-real-and-too-small-for-its-own-noise-even-under-the-passive-line-the-book-is-plus-0-65-with-an-se-of-0-89.md`. The H1 above is the full title.*

**NOT A CANDIDATE: T1 and T5 pass; T2, T3 and T4 fail.** Pre-registration `ba9131f` predates the
runner and this file (R8). **In-sample; no holdout was read. Nothing is admitted.** 2.3 min.

```
[K] kernel probe;  [F] the events are D436's B (12,597);  [P2] cap-20 gross equals D438's B cell to 1e-9
```

---

## 1. The bar (cap 20)

```
T1  increment > state-matched p95 by 2 SE   +38.76 vs p95 +29.52 (±0.74)         PASS   (+20.8 over the control's p50)
T2  crossed net > 0 by 2 SE  (reported)     -0.627 ± 0.888 /bar                  FAIL
T3  passive net > 0 by 2 SE                 +0.650 ± 0.888 /bar   +0.7 SE        FAIL
T4  era-2 passive net > 0 by 2 SE           +1.055 ± 1.478 /bar   +0.7 SE        FAIL
T5  gross > time-rotation p95               +2.242 vs -0.554 (±0.044)  +64 SE    PASS
```

---

## 2. Per trade and per bar, both lines

```
                         gross    2c PUB   borrow   CROSSED net     PASSIVE cost   PASSIVE net
cap 20  per trade       +38.8     52.2      4.9      -18.3            31.7          +7.1
cap 20  per bar         +2.242    2.869 crossed  ->  -0.627 (Sharpe -0.20)   1.591 passive -> +0.650 (Sharpe +0.21)   SE 0.888
cap 40  per trade       +68.8     51.8      9.8       +7.3            36.4         +32.5
cap 40  per bar         +1.863    1.552 crossed  ->  +0.311 (Sharpe +0.13)   0.917 passive -> +0.946 (Sharpe +0.39)   SE 0.594  (+1.6 SE)
passive net by era, cap 20:  era 1 +0.245 ± 0.861   era 2 (2018-06 on) +1.055 ± 1.478
concentration, cap 20:  16 names to half the P&L;  top 1% of trades = 108% of P&L;  15 of 17 years positive
splits at cap 20 (per trade):  spread narrow gross -1.8 (passive net -27)   mid +14.3 (-17)   WIDE +106.5 (passive net +64)
                               on cadence +41.0   off +37.9;   ret20_lo +38.6   not +45.5
```

**Every number landed where D437–D439 said it would.** The signal is real by both nulls — +21 bp
per trade over a random event in the same state, +64 SE over rotated days — and the book it
makes is **+0.65 a bar under the most favourable cost line, with a bootstrap SE of 0.89**. The
daily noise of a hedged short book of ~60 positions is 1.3 bp a bar; a mean of 0.65 is not
distinguishable from zero in sixteen years, and the second half of the sample (+1.06 ± 1.48) is
no better distinguishable. At cap 40 it reaches +0.95 ± 0.59, 1.6 SE, on 18 names to half the
P&L. **The passive line does exactly what D439 said it would — it takes 2c from 52 to 32 per
trade — and it is not enough, because the object's edge is a median of +14 under a mean of +39,
carried by a top 1% that is 108% of the P&L.**

The wide spread tercile nets +64 per trade under the passive line on 3,307 trades. That is the
one corner-shaped cell in the line, and it is the cell where the passive assumption is least
safe (the widest names) and the tail is heaviest.

---

## 3. Predictions — five and a half of six

| | prediction | outcome |
|---|---|---|
| X-a | cap 20: +38.8 / −18 / +7; cap 40: +68.9 / +7 / +37 | +38.8 / −18.3 / +7.1; +68.8 / +7.3 / +32.5 ✓ |
| X-b | book cap 20: gross +2.24, crossed −0.4, passive +0.6 ± 0.6; cap 40 passive +1.0 | +2.24, −0.63, +0.65 ± 0.89; +0.95 ± 0.59 ✓ |
| X-c | T1, T5 pass | ✓ |
| X-d | era 2 passive +0.8..+1.5, near 2 SE | +1.06 ± 1.48 — in range, 0.7 SE |
| X-e | wide tercile passive +40..+60; narrow negative under both | +64; −40 / −27 ✓ |
| X-f | cadence flat; 16–20 names; top-1% ~100% | +41 / +38; 16; 108% ✓ |

This is what it looks like when the numbers are known before the study: the study confirms them.
It was worth running for one reason — to put the passive line beside the crossed one on the
object that had the best case, under a pre-registered bar — and the answer is that the line is
not enough.

---

## 4. What this leaves

1. **B is a real effect** — the volume shock in a high-priced name is followed by a continuation
   the state alone does not predict, at every horizon — **and it is not a book at any cost line
   this repo can justify.** Under the crossed line it loses; under the passive assumption it earns
   +0.65 a bar with an SE of 0.89.
2. **The holdouts stay shut for this line.** The candidate condition was declared on the passive
   line and it was not met; a holdout read would test a signal that is already established
   in-sample against nulls that test the right thing, and would not change the book's noise.
3. **What would change it is not another study on these fixtures:** a quoted-spread pull (TWS)
   to learn whether the modelled 42 bp/side on B's wide names is a cost at all — if it is a
   range, the wide tercile's +64 passive net is closer to a crossed net and the book is a
   different object; and more capital-days than sixteen years of one universe, which nothing here
   can supply.
4. **The volume line, D434–D440, ends here on my side**: an atlas with five volume axes and a
   conditional layer, one component with a real state-conditional increment, two cost lines, and
   no book. The method items (state-matched controls, the fill-alignment check, the chase
   measurement, the range-vs-quote finding) are the yield.

**Disposition is the principal's.**

---

## 5. R13

Fortieth look by object; the second forward-return look at this construction; no holdout.

**Evidence:** `data/d440_stage2_B.json`. Runner `scripts/run_d440_stage2_B.py`.
