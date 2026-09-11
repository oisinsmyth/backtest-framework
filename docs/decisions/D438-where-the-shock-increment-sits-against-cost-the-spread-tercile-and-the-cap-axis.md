# D438 — where the shock's increment sits against cost: the spread tercile and the cap axis, on A and B

**A MEASUREMENT** (D392/D434's class). **Scores no strategy, proposes no rule, admits nothing (R15).
Committed before the runner exists (R8).** In-sample on the mining fixture; no holdout. D400–D437
used, D407–D410 and D390–D399 reserved.

## 1. Why, and what is dropped

D437 found the volume shock adds +10 (A: `mom_hi` long) and +22 (B: `price_hi` short) bp per trade
over a random event in the same state, at +10 SE and +22 SE against the declared nulls — and that
the names it fires in cost 52–75 bp to trade under the kernel's own PUB convention, so no
component nets positive. **C and D are dropped here because they showed no increment (+3, 0); that
is a subtraction of components that measured nothing, disclosed as post-hoc.** The question is
whether the increment is concentrated somewhere the spread is not.

## 2. Two axes, one kernel

The D345 kernel through `run_d359` (the D435 / D437 path), cap exit, next-open fill, hedged;
costs from `trade_block` (2c PUB primary, PB beside; borrow on B).

**Axis 1 — the spread tercile of the names held.** Each event's cached PUB half-spread at `t−1`
(`P["HALF"]["PUB"]`, known before the fill); tercile cuts on each component's own events, fixed and
printed. For each (component, tercile): gross, 2c, net per trade; the **state-matched control**
(100 draws of random non-shock cells from the same state, same daily count, *restricted to the same
spread tercile* — so the control shares the nuisance); the increment and its p95.

**Axis 2 — the cap.** Caps 5, 10, 20, 40, 60 for A and B, all events: gross, 2c (fixed per
trade), net per trade; deployed gross, 2c cost and net per bar; the state-matched control at each
cap (100 draws); the increment by cap — **does the shock's extra accrue in the first five days or
across sixty.**

**Assertions:** `[K]` the kernel probe; `[P2]` cap 20, all events, reproduces D437's per-trade
gross for A and B to 1e-9; `[T]` the three spread terciles partition each component's events;
`[F]` the events are D436's masks (counts equal).

**Cost:** ~2,000 kernel runs (600 for axis 1, 1,000 for axis 2, plus the observed cells); at
0.2–0.6 s a run ≈ 12–15 min, one process.

## 3. The corner condition, declared

A cell (component × spread tercile, or component × cap) is a **corner** if its **net PUB per trade
> 0 by 2 SE** *and* its **increment over the state-matched control exceeds the control's p95**.
A corner is what stage 2 would be pre-registered on. No corner → the shock's increment lives
where the spread is, and the construction's only remaining lever is execution.

## 4. Predictions (LOW–MODERATE; D432's DV lever and D437's costs are the priors)

- **X-a** spread terciles: 2c PUB ≈ **25–35 / 45–60 / 90–130** bp (narrow / mid / wide); gross
  *rises* with spread (wider = smaller, more volatile, more edge — the zone line's pattern):
  A ≈ +20 / +35 / +55, B ≈ +25 / +40 / +55.
- **X-b** the increment over state is roughly **flat across terciles** (A +8 to +14 in each,
  B +15 to +30) — the timer's information is not a spread effect.
- **X-c** **no spread-tercile corner**: the narrow tercile nets **−10 to +5** under PUB in A and
  **−5 to +10** in B; B's narrow tercile is the only cell with a chance.
- **X-d** the cap axis: the increment **accrues** — A +4 / +7 / +10 / +13 / +14 and B +10 / +16
  / +22 / +28 / +30 at caps 5 / 10 / 20 / 40 / 60 (a plateau by 40); gross per trade rises
  with cap (D392's floors do); 2c is fixed, so **net per trade improves with cap**.
- **X-e** at cap 60: A gross **+55 to +70** vs 2c ~62 → net PUB inside ±15; B gross **+65 to
  +85** vs ~57 → **net PUB +5 to +25, > 2 SE — the one predicted corner**, at the price of a
  60-bar hold and the concentration that comes with it (reported: names to half the P&L,
  top-1% share, by year).
- **X-f** deployed net per bar is negative at every cap for A and turns positive for B at 40–60.

X-e is the study: whether a longer hold amortises the spread faster than the increment fades.

## 5. Not in scope

Any holdout; C and D; any new state or feature; execution. Thirty-eighth look by object; a
measurement on spent data.
