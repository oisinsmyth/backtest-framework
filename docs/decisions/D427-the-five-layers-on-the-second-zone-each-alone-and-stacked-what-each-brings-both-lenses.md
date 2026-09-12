# D427 — the five layers on the second zone, each alone and stacked: what each brings, both lenses

**Pre-registration. Committed before the runner exists (R8).** A **MEASUREMENT** (D280's class,
D392's form): it scores a construction's parts, proposes no rule, **admits nothing (R15), is gated
on nothing** — every layer is reported regardless of sign, which is the principal's instruction.
D400–D426 used, D407–D410 and D390–D399 reserved. **No holdout of any kind is read.** Daily bars.

## 1. The base and the layers

Base **R2** = STACK2-ANY ∧ cell 2 — the rung-2-only construction: 9,411 trades, gross +44.84,
net +16.04 (D422); ANY-REQUIRED book net +0.99/+1.51/+1.20 (D422), +1.31/+1.84/+1.03 with ZTP
(D425). The five layers are the five improvements named after D426, each an in-sample split that
has already been looked at once — so this is a measurement of what each is worth on the same data,
not evidence that any of it survives:

```
L1 GAP    the prior touch is 3-20 sessions back; drops gap 1-2 (D426: +28.77 on a -276 prior)
L2 LONG   demand zones only (D422: the long side is an ordinary distribution, the short a lottery)
L3 OPP    prior touch OPPOSITE side, 3-10 back (D426: +110/+119, n 287/634) -- a PRIORITY in the
          book; per trade it is a reported sub-cell, since a priority cannot change a per-trade mean
L4 ZTP    exit at the next live opposite-side zone, else t+5 (D425)
L5 CHEAP  entry price below the base's lower tercile, FIXED at $38.51 (D422: +86.48 gross there)
```

**Order, declared:** L1 → L1+L2 → +L3 (priority) → +L4 (exit) → +L5. Each also **alone** on the
base. `scripts/d427_layers.py`, committed with this record.

## 2. Stage 0 — counts, no outcome bar

```
                     n       2018+    2021+    names   events/day   ZTP coverage
base R2            9,411     6,100    4,261     739      2.25         60.5%
L1 alone           7,856     5,060    3,551                           59.2%
L2 alone           5,137     3,284    2,294                           61.3%
L3 sub-cell          921       593      419                           61.0%
L5 alone           3,137     1,689    1,135                           59.6%
L1+L2              4,224     2,690    1,905     657      1.01     (L3 inside: 523)
L1..L5             1,416       764      528     336      0.34     (L3 inside: 165)
```

The full stack is 15% of the base and a third of an event a day against ten slots.

## 3. What is measured, per layer and per cumulative step

**Per trade:** n, gross mean, median, SE, win rate, net (each event's own cost), payoff, the
symmetric 1% trim; on **pooled, 2018+, and 2021–2026** (the window that excludes 2020, declared
here because the premium is 2020-onward). For every *filter* layer (L1, L2, L5, and each cumulative
mask), the **within-day label permutation null** on its premium over the base's complement
(D422's null, 200 draws): does the layer select, beyond the day? L2's null is the side label
itself. L5 is additionally read against the **D392 atlas**: a random cheap-tercile long earns
+19.22 at the median on this universe with no signal — that is the base rate the cheap layer
must exceed, quoted from `data/d392_atlas.json`, not re-run. L3 is a sub-cell mean with its SE.
L4 is D425's paired delta on each population it is applied to.

**The book:** cell 2, 10 slots, three seeds, D419's scorer. Each layer alone as a *requirement*
(pool = base ∧ layer), L3 as a *priority* (pool unchanged, L3 events first — D421's priority did
nothing on a full book; this book is a third empty), L4 as the exit; then the cumulative books.
The simulator is D425's `sim2` plus D421's priority ordering, asserted bit-identical to D421's
`simulate` with a priority and no levels, and to `sim2` with levels and no priority (`[P2]`);
D422's ANY-REQ book reproduced first. Utilisation, cost/bar, per-trade net, net by seed, net
delta vs the base book (monthly block bootstrap). **Control:** D422's matched-count random cell-2
pools (100 draws, cached-input workers — D423's pattern, not D426's) for the base, for L1 alone,
and for the final stack — the three books whose counts differ most.

## 4. Predictions (arithmetic on D422/D425/D426's tables; MODERATE for the alones, LOW for the stack)

- **X-a** L1 alone gross **+47 to +49** (the weighted removal of gap 1–2 gives +48.0); its
  premium over the dropped +28.77 passes the within-day null. Book +1.3 to +1.7 at ~63% util.
- **X-b** L2 alone gross **+44 to +46** (the same mean as the base — the long side's gain is
  shape: median > +55, win > 55%), so its premium over shorts is **inside 2 SE of zero** and the
  null does *not* pass. Book +0.6 to +1.1 at ~45% util.
- **X-c** L3 sub-cell **+100 to +130** (weighted +116), SE ~25; as a priority on L1+L2 it adds
  **0 to +0.3** bp/bar, because 523 priority events on a book that is already two-thirds empty
  rarely displace anything.
- **X-d** L4 on L1+L2: paired delta **+1 to +4** (D425's long side was +2.24); book +0.1 to +0.4.
- **X-e** L5 alone gross **+80 to +90**, net +45 to +60; its permutation null passes; against the
  atlas base rate the excess is **+30 to +40** on the long half. Book +0.4 to +0.9 at ~30% util,
  cost/trade above 33.
- **X-f** the stack L1..L5 gross **+85 to +100** on 1,416 (SE ~12), net **+50 to +65** per trade;
  book **+0.3 to +0.8** net/bar at **~17% utilisation** — the highest per-trade net and the lowest
  capacity in the record. 2021–2026 above pooled at every step.
- **X-g** the stack's book beats its matched-count random pool's p95; L1 alone's does; the base's
  does (D422's +5.4 SE, now pre-declared).

X-b and X-f are the study: whether "long only" is a mean improvement or a shape improvement, and
what the stack costs in capacity for what it adds per trade.

## 5. Not in scope

No holdout, no 15m, no change to entry, hold, cost model or the cell's three cuts, no sweep on
the gap window or the price cut, no disposition. Twenty-seventh look by object.
