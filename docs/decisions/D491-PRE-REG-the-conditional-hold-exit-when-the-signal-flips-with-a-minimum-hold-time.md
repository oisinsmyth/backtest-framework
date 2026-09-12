# D491 — PRE-REG: the conditional hold — exit when the signal flips, with a minimum hold time

**2026-09-12, committed before the runner exists** (CLAUDE.md, [R8](../RULES.md#r8)).
Directed by the principal: *"instead lets make the hold conditional and also with a minimum hold
time."*

---

## 0. Why this is a better construction than anything before it, and why it changes the scoring

Every momentum record so far — [D484](D484-RESULT-the-log-MACD-is-a-real-signal-that-fails-only-on-cost-and-the-off-diagonal-ordering-is-confirmed.md),
[D486](D486-RESULT-cost-cutting-closes-70-percent-of-the-gap-and-stops-and-only-NQ-gets-anywhere.md),
[D488](D488-RESULT-extending-the-hold-fails-and-the-closure-accidentally-produced-the-first-net-positive-cell.md)
— imposed a **fixed** holding period and then asked whether the edge covered a fixed fee. That is
not how a MACD is traded and it has two defects:

1. **The exit ignores the signal.** A fixed-H exit sells a position the indicator still favours
   and holds one it has turned against. D488 found no H that works, which is unsurprising when H
   is chosen by the tester rather than by the market.
2. **The trade count is an input, so cost is an input.** Fixing H fixes the number of round trips,
   which fixes the bill. **A conditional exit makes the trade count an OUTPUT** — and since
   commission is 70–86% of cost (D486) and **fixed per round trip**, the number of round trips is
   the single most important quantity in the whole problem.

**The minimum hold is what makes it work rather than churn.** Without it, a signal that flickers
around zero pays the fee on every flicker. With it, the position must survive M hours before an
exit is even permitted, so the fee is paid **once per swing** instead of once per flicker.

### The scoring changes, and this is the real upgrade

A conditional exit produces an **actual traded P&L series**. So for the first time in this line,
`COMPONENTS_PROP.md`'s criteria can be computed **directly** rather than through an
edge-versus-cost proxy:

- **C-a** net annualised Sharpe of the daily P&L, at minimum size, net of cost
- **C-c** skew of the daily P&L
- **C-d** daily σ at minimum size against $500

**D484/D486/D488 could not do this.** They measured an edge in σ units and compared it to a cost
in ticks; none of them ever produced a P&L series. This does.

## 1. The construction, fixed now

**The signal is D484's, unaltered — same variants, same published parameters, no re-tuning.**
Any parameter change makes this a search and a different study.

- **B1 (CO-PRIMARY)** log **Impulse MACD**, ZLEMA/SMMA **34**, signal **9**; `md == 0` is a flat
  signal, which under a conditional exit means **it closes a position** (after the minimum hold)
  rather than merely declining to open one.
- **B2 (CO-PRIMARY)** plain log MACD histogram, **12/26/9**.

> **AMENDED before the runner existed, 2026-09-12, directed by the principal:** *"the normal
> MACD may be better as a conditional hold so test it also."* **B2 is promoted from secondary to
> co-primary.** Both already occupied the family equally (24 cells = 3 roots × 2 variants × 4 M),
> so no statistic changes — but the labelling implied a hierarchy that the principal's reasoning
> undercuts, and it is a good argument:
>
> **B1's zero state covers 14.4% of bars (D484). Under a FIXED exit that was inert. Under a
> CONDITIONAL exit every zero is an extra round trip** — the position closes, and re-opening later
> pays again. Plain MACD never reaches zero, so it holds until a genuine sign flip and pays
> fewer fees. **Since commission is 70–86% of cost, a signal that exits more often is penalised
> exactly where it hurts most.**
>
> **This cuts directly against V-c, which I wrote before hearing it.** V-c is left exactly as
> written rather than revised, and the principal's counter-hypothesis is recorded here as the
> competing prediction: **B2 beats B1, because B1's zero state buys extra round trips.** Whichever
> way it falls, one of the two was on the record first.

**The state machine, in full, so nothing about timing is left to the runner's discretion:**

```
decide at the CLOSE of segment t;  execute at the OPEN of segment t+1
elapsed = t − entry_t                      (entered at the open of entry_t+1)

EXIT  if  in a position  AND  elapsed ≥ M  AND  sign(hist)·position ≤ 0
ENTER if  flat           AND  sign(hist) ≠ 0
FORCED EXIT at the CLOSE of the last eligible segment, regardless of signal
```

**Exit is evaluated before entry within the same segment**, so a flip closes and re-opens at the
same price and pays two legs of cost. **Decision at close, execution at next open** — never at the
close just observed.

- **Minimum hold M ∈ {1, 2, 3, 5, 8} hours** on non-index roots; **{1, 2, 3, 5}** on index roots,
  whose eligible window is only 6 hours long (below).
- **No maximum hold** other than the forced session exit. That is the point of the exercise.

## 2. Data and the two constraints, fixed now

| | |
|---|---|
| fixture | `data/fixtures/fut_sessions_hourly.csv.gz`, 23 hourly segments h18…h16 |
| roots | **ES, NQ, YM, ZN, ZB, GC, CL, 6E**; RTY excluded on gate **G2**; every root's G1–G5 read and required to pass |
| window | **2016-01-04 → 2023-12-29**, each root's `usable_start` honoured. **2024+ sealed**, gate raises |
| contract | `same_front`; the whole eligible range of a session must be contract-pure or the session is skipped |

**P2** — flat by 4pm ET, so the last held segment is index **21** (h15) and the forced exit is at
its close.

**The principal's closure** — the index overnight leg is closed for the prop book, so on
**ES, NQ, YM** all activity is confined to segments **15–21** (h09–h15, the day session): a
position may open no earlier than the open of segment 16 and must be flat at the close of 21.
**Non-index roots use segments 0–21** and may hold through the overnight.

## 3. The statistics, fixed now

**Primary — the P&L series, on the roots with a committed micro spec (ES, NQ, YM only):**
per (root, variant, M), the daily P&L in dollars at **one micro**, cost
`$3.00 + 1.009 ticks` charged **per completed round trip**, and from it:

| | |
|---|---|
| **A1** | **net annualised Sharpe** — C-a's quantity |
| **A2** | skew — C-c's quantity |
| **A3** | daily σ in dollars — C-d's quantity |
| **A4** | **round trips per session** — the quantity the minimum hold exists to control, and the one that decides the bill |

**Secondary — the non-index roots** (ZN, ZB, GC, CL, 6E): **gross** P&L in ticks per session and
round trips per session, **reported without a cost line**. MGC, MCL and M6E are absent from
`data/futures_contract_specs.json`, whose own provenance records that CME returns 403 to plain
HTTP. **No micro tick value will be guessed**, so these roots cannot be scored and are carried so
that a later verified fetch can price them.

## 4. The null, fixed now

**R1 — circular rotation of the SIGNAL series**, then **the entire state machine is re-run** on
the rotated signal. Rotating the signal and re-simulating is essential: it preserves the signal's
autocorrelation (D484: lag-1 ρ = +0.886) *and* therefore preserves the **trade count**, so the
null pays a comparable bill. **A null that traded a different number of times would be comparing
two different cost structures, not two different signals.**

**2,000 draws.** Statistic: the **family maximum** net Sharpe across the 24 costable cells
(3 roots × 2 variants × 4 M values). Report p50 and p95 and carry the **bootstrap SE of the p95**;
an observed maximum within **2 SE** of the p95 is **UNRESOLVED**, not a pass.

**A family bar is used because D488's tradeable cell had no null attached to it** — §5 there
required only `gross/cost > 1.0`, which was a weakness in that record and is not repeated here.

## 5. The bars, fixed now

| verdict | requires |
|---|---|
| **SIGNAL** | the family-maximum net Sharpe exceeds R1's family-max p95 by > 2 SE |
| **COMPONENT CANDIDATE** | additionally **C-a > 0.5**, **C-c ≥ −0.5**, **C-d ≤ $500** on that cell |
| **ENTERED** | *nothing is entered off this runner.* C-b routing, C-e provenance and a separate confirmation on the sealed slice all come after, per the ledger's own standard |

## 6. Predictions

- **V-a.** The conditional exit **beats the best fixed-H cell** of D488 on NQ — gross/cost above
  1.14 — because the exit now keys on the signal. *This is the direct test of the principal's
  idea.*
- **V-b.** **Round trips per session fall steeply in M**, and the net Sharpe is **non-monotone**
  in M with an interior maximum: too small and it churns, too large and it holds through
  reversals. *If the Sharpe is monotone in M the minimum-hold idea is doing nothing.*
- **V-c.** **B1 beats B2** under a conditional exit, reversing nothing but finally giving the
  impulse zero state something to do — under a fixed H it was inert at 14.4% of bars (D484), but
  here a zero **closes a trade**.
- **V-d.** **No cell clears the family bar.** I expect V-a and V-b to hold and the null still to
  refuse, because 24 cells of a selected-in-sample construction on eight years is exactly what a
  family maximum is built to discount.
- **V-e.** **C-d is not binding** at one micro on any index root — daily σ well under $500 —
  so the failure, if it comes, is C-a's.

## 7. What would make me wrong

The family-maximum net Sharpe clearing R1's p95 by more than 2 SE **and** that cell also clearing
C-a, C-c and C-d. That would be the first component candidate this line has produced, and it
would then need C-b routing and a confirmation on the sealed slice before anything is entered.

## 8. Stated limitations, before any number exists

1. **Only ES, NQ and YM can be costed.** The largest measured MACD edges are on GC and CL
   (D484: +0.0326, +0.0337 σ) and remain unpriceable.
2. **Execution is modelled as open-of-next-segment at the measured half-spread.** No queue, no
   partial fills, no slippage on a flip — D471 §1 states plainly that fills need `mbp-10`, which
   was not bought. **Every figure is therefore an upper bound.**
3. **The volume-clock exit (D472, +10.4%) is not applied.**
4. **Hourly resolution**: a signal flip inside an hour is invisible, and the minimum hold is
   measured in whole hours.
5. **In-sample.** 2024+ is the confirmation slice and is not read.
6. **Eight roots are not eight independent draws** (ZN/ZB rates, ES/NQ/YM index).
7. **The index roots' window is only 6 hours**, so M=5 leaves almost no room for a conditional
   exit to act — at M=5 the construction is nearly a fixed-H hold, and that is a feature of the
   closure, not of the idea.
