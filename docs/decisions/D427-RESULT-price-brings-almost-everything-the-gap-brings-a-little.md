# D427 RESULT — price brings almost everything, the gap brings a little, long-only brings shape not money, and the stack was built in the wrong order

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D427-RESULT-price-brings-almost-everything-the-gap-brings-a-little-long-only-brings-shape-and-the-stack-order-was-wrong.md`. The H1 above is the full title.*

**A MEASUREMENT (R15): admits nothing, gated on nothing.** Declared in `44038ea` before the runner
existed (R8). **The ledger does not move. No holdout of any kind was read.** Daily bars.

Cost: 553 s — of which the first launch swapped the machine (2.7 GB of top-level imports re-executed
in each of 8 workers) and was killed; the relaunch with 0.9 GB workers took ~4 min. The lesson is in
memory; it does not touch the numbers.

```
[STAGE0] 9,411 / 7,856 / 5,137 / 921 / 3,137 / 1,416 reproduce;  L5 cut $38.51
[P2]     sim4 == D422's ANY-REQ book; == D421's simulate with the L3 priority; == D425's sim2 with ZTP
[RECON]  33 books;  [CHUNK] worker draw 0 == in-process
```

---

## 1. Each layer alone — per trade, and what its null says

```
                      n     gross   median   NET    win    trim     2018+ gross   2021-26 gross   premium vs complement, within-day null
base R2            9,411   +44.84   +25.6   +16.0  52.4%  +39.9      +44.7          +43.1
L1 gap 3-20        7,856   +48.02   +24.8   +19.1  52.3%  +42.2      +50.9          +46.4      +19.25   p50 +5.7  p95 +25.8   FAIL (-7 SE)
L2 long            5,137   +44.90   +62.4   +15.6  55.6%  +46.7      +48.6          +51.5       +0.12   p50 +4.8  p95 +15.0   FAIL
L3 opp 3-10 (sub)    921  +116.06   +57.2   +87.9  55.3%  +88.5     +120.3          +92.6      +78.95   p50 +55.7 p95 +83.3   FAIL (-3.7 SE)
L5 cheap < $38.51  3,137   +86.48   +67.0   +53.0  55.4%  +77.2     +110.9         +116.3      +62.45   p50 +25.4 p95 +41.2   PASS (+35 SE)
dropped by L1      1,555   +28.77   +31.6    +0.6  53.0%  +28.1      +14.3          +26.7
```

**L5 — price — is the layer.** +86 gross, +53 net, +116 in 2021–2026, and its premium over the
rest of the cell beats a same-day relabelling by a wide margin. Against the D392 atlas, the
long half of the cheap tercile earns **+84.65 where a random cheap long earns +19.22: +65 of
excess over the universe's own price base rate.** Cost is higher (33.5 vs 28.8) and the edge
is 2.5× the cost.

**L1 — the gap — is worth +3 per trade and does not beat its null.** The dropped gap 1–2 events
are +28.77 (net +0.56, and net-negative in the second half), so removing them lifts the rest
to +48. But 1,555 events on a fat-tailed cell make a wide null (p95 +25.8), and +19 sits inside
it. The gap filter is a reasonable thing to do and not a demonstrated selection.

**L2 — long only — brings shape and no money.** The mean is the base's (+44.90 vs +44.84;
premium +0.12). What changes is the *distribution*: median +62 against +26, win 55.6%, payoff
falling to 0.99. D422's reading holds: the long side is an ordinary distribution, the short a
lottery with the same mean — **and the cost model carries no borrow, so the short half is
overstated by whatever the borrow is.**

**L3 — the opposite-side prior at 3–10 — is largely its days.** +116 as a sub-cell, but the
within-day null of a random 921-subset of the base *on the same days* has a median premium of
+55.7: the L3 events sit on days when the whole cell paid, and the +79 premium does not beat
what those days alone give (p95 +83). Reported in D426 as a lead with wide SEs; now read.

---

## 2. The stack — and the order was wrong

```
cumulative               n     gross   median   NET    win    2018+     2021-26    null
L1                     7,856   +48.02   +24.8   +19.1  52.3%   +50.9     +46.4     FAIL
L1+L2                  4,224   +45.09   +59.6   +15.7  55.2%   +56.5     +53.8     FAIL (+0.46)
L1..L5                 1,416   +79.93   +99.0   +44.9  58.6%  +113.3    +120.3     PASS (+41.3 vs p95 +36.9, +5.4 SE)
L1..L5 & L3              165  +113.25   +95.5   +81.7  58.8%  +126.6    +144.2     (SE 45)
```

The stack ends at **+80 gross / +45 net per trade, median +99, win 58.6%, and +120 gross in
2021–2026 on 528 trades** — and every basis point of that over L1+L2 (+45) is L5. Long-only
inside the stack is again shape: the stack's median is above its mean.

**L4 — ZTP — adds nothing once the gap filter is on.** On the base +0.36 (D425); on L1 −2.21
(forfeit −15); on L1+L2 +0.61; on the stack −3.04. By subtraction, ZTP's whole positive
contribution on the base lived in the gap 1–2 events (+13 per trade there) — the events where
price had just run through the first zone and the "next live zone" above was close. Drop those
and the exit that carried information in D425 carries none.

---

## 3. The book — where the stack's order shows

```
book (cell 2, 10 slots)   gross     net    cost    util   trades  per trade   net by seed             Δ vs base
base                     +4.889  +0.993   3.896   68.2%   5,615    +35.85    +0.99 +1.51 +1.20
L1-REQ                   +4.980  +1.435   3.544   62.2%   5,121    +40.04    +1.44 +1.49 +1.58     +0.26 ± 0.50
L2-REQ                   +2.411  +0.095   2.315   39.5%   3,256    +30.49    +0.10 +0.12 +0.43     -1.02 ± 1.21
L3-PRIO                  +5.279  +1.364   3.915   68.2%   5,615    +38.72    +1.36 +1.77 +1.40     +0.27 ± 0.19  (+1.5 SE)
L4-ZTP                   +5.332  +1.310   4.022   66.0%   5,774    +38.03    +1.31 +1.84 +1.03     +0.16 ± 0.38
L5-REQ                   +5.179  +3.123   2.055   31.0%   2,552    +83.57    +3.12 +3.18 +2.99     +1.86 ± 1.00  (+1.9 SE)
C2 L1+L2                 +2.851  +0.812   2.039   35.0%   2,886    +40.68    +0.81 +0.46 +0.57     -0.62 ± 1.22
C3 +L3 priority          +2.704  +0.664   2.040   35.0%   2,886    +38.58    +0.66 +0.44 +0.47     -0.71 ± 1.23
C4 +ZTP                  +3.043  +0.974   2.069   33.3%   2,927    +42.81    +0.97 +0.78 +0.80     -0.39 ± 1.24
C5 +L5                   +2.101  +1.146   0.955   13.2%   1,155    +74.92    +1.15 +1.21 +1.15     -0.07 ± 1.14

random cell-2 pools of the same count:   base +1.237 vs p95 +0.388 (+9.4 SE)   L1 +1.500 vs +0.613 (+9.8)   C5 +1.169 vs +0.841 (+6.3)
```

**L5 alone is the best book in the record: +3.1 net per bar on every seed, at 31% utilisation,
with the lowest cost per bar (2.06) and +84 per trade.** X-e predicted +0.4 to +0.9 for it on
the reasoning that a third of the pool means a third of the book; it is three times the base,
because the trades it keeps are worth 2.3× the ones it drops and the round trips it saves are
cost. This is D422's ANY-REQ lesson a second time (gross *and* net up on fewer trades), and I
under-predicted a required book a second time.

**Long-only is the layer that starves the book.** L2-REQ nets +0.10 — the per-trade mean is
unchanged and the pool is halved, so the slots idle (39.5%). Every cumulative book after L2 is
below the base, and **C5 — the full stack — nets +1.15 at 13% utilisation, a third of L5 alone,
because L1+L2 were stacked *under* L5 and cut its pool from 2,552 trades to 1,155.** The order I
declared put the per-trade layers first and the capacity layer last; on a slot-limited book that
is backwards. **L3 as a priority is worth +0.27 ± 0.19 on the full base book and −0.09 on the
long book** — a priority acts only where there is competition for a slot.

All three controlled books beat their matched-count random pools — the base's D422 result is
now pre-declared (+9.4 SE), L1's too (+9.8), and the stack's (+6.3).

---

## 4. Predictions — the alones mostly held, the stack and the cheap book did not

| | prediction | outcome |
|---|---|---|
| X-a | L1 +47..+49, null passes, book +1.3..+1.7 | +48.02 ✓; **null FAILS** (wide at 1,555); book +1.50 ✓ |
| X-b | L2 same mean, median > 55, win > 55, null fails | +44.90, +62.4, 55.6%, fails ✓ — book +0.21, below the range |
| X-c | L3 +100..+130; priority adds 0..+0.3 | +116 ✓; +0.27 on base, −0.09 on the long book ✓ |
| X-d | ZTP on L1+L2 +1..+4; book +0.1..+0.4 | +0.61 (noise); book +0.33 ✓ |
| **X-e** | L5 +80..+90; excess over atlas +30..+40; **book +0.4..+0.9** | +86.5 ✓; **excess +65**; **book +3.12** |
| **X-f** | stack +85..+100 gross, net +50..+65, book +0.3..+0.8 | **+79.9, +44.9, book +1.17 at 13%** — per trade below, book above |
| X-g | base, L1, stack beat their random p95 | ✓ all three |

Two systematic misses, both in the same direction as before: **a requirement that keeps the
better third of the trades raises net per bar, not lowers it** (cost per bar falls faster than
gross), and **the atlas base rate is not most of the cheap tercile's edge** — it is +19 of +85.

---

## 5. What each brings, in one line each

- **Price (L5):** +42 gross per trade over the base; +65 over the universe's cheap base rate;
  the best book in the record (+3.1/bar). Everything else is second order to it.
- **Gap (L1):** +3 per trade, +0.26/bar; drops trades that pay nothing net; not separable from
  its null at this size.
- **Long-only (L2):** median +62 vs +26, win 55.6%, the same mean; as a requirement it starves
  a 10-slot book.
- **Opposite-side prior (L3):** +116 as a sub-cell but mostly its days; +0.27/bar as a
  priority on a book with competition, nothing on one without.
- **ZTP (L4):** +0.36 on the base, nothing once gap 1–2 is dropped; its D425 information lived
  there.
- **The stack, in the declared order:** +80/+45 per trade, +120 gross in 2021–2026 — and a
  book a third of what L5 alone makes, because the capacity layer went last.

**Caveats that stand:** every layer here was chosen after being seen once in D422/D426; the
stack is a forking path and its in-sample numbers flatter; 2020–2026 still carries the premium;
the cost model has no borrow; nothing has been judged out of sample. **Disposition is the
principal's.**

---

## 6. R13

Twenty-seventh look by object on price levels. No new data spent.

**Evidence:** `data/d427_layers.json`. Runner `scripts/run_d427_layers.py`; layers
`scripts/d427_layers.py`, committed with the declaration.
