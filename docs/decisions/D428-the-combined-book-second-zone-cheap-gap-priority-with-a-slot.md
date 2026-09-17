# D428 — the combined book: second zone, cheap, gap ≥ 3, opposite-side priority, no exit — with a slot sweep, both lenses

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D428-the-combined-book-second-zone-cheap-gap-priority-with-a-slot-sweep-both-lenses.md`. The H1 above is the full title.*

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. D400–D427
used, D407–D410 and D390–D399 reserved. **No holdout of any kind is read.** Daily bars.

## 1. The construction — everything this line kept, in the order a book needs it

**Entry (D413/D414):** distance-armed departure zone, entered at the touch-day close, exit at the
`t+5` close, **no stop, no target, no trail** (D417, D418, D423, D424, D425: nine exit
constructions, none beats the clock). Cell 2's three cuts as in D413.

**The pool (`scripts/d428_pool.py`, committed with this record):**
```
STACK2-ANY          the second touch, side-blind (D422)                       9,411 in cell 2
& price < $38.51    D427's fixed cheap-tercile cut (D427: +86 gross, +65 over the atlas base rate)
& gap 3-20          prior touch at least 3 sessions back (D426/D427: gap 1-2 nets nothing)
= POOL              2,649 events, 406 names, 0.633/day, mean occupancy 3.16 positions at a 5-day hold
PRIORITY            prior touch OPPOSITE side, 3-10 back (D427's L3): 303 events, refilled first
LONG arm            demand zones only: 1,416 -- reported, not primary (D427: same mean, better shape)
```
Rung 1 never (D426), rung 3+ never, no double-down, no same-side restriction, no flip, nothing
from D414–D416.

**The slot sweep — the one book parameter never touched.** Every book so far ran 10 slots; this
pool fills three. `N ∈ {2, 3, 4, 5, 7, 10}`, **primary N = 4** (occupancy/N = 0.79: near full
without structural blocking). R14: the sweep is shape, N = 4 is the bar.

## 2. Costs, declared

Neutral Corwin–Schultz (60-bar trailing median ending 2 bars before entry) + IBKR $0.0035/share,
as throughout — **plus, new here, a borrow charge on the short half**: base **1%/yr** general
collateral (≈2 bp on a 5-session hold), reported also at **10%/yr** (≈20 bp) because cheap
names are where hard-to-borrow lives and the repo has no borrow data. The primary is the 1% book;
the 10% book is a sensitivity, printed beside it.

**Corporate actions:** the daily fixture is unadjusted (D422: MTW's spinoff). No causal exclusion
exists without action data, so the primary keeps every event and a **reported** robustness drops
trades with |r| > 50% over the hold (outcome-based, hence not primary).

## 3. What is measured

**Per trade** (path-invariant, pool of 2,649): D422's full trade table — gross, median, net at
both borrow rates, win, payoff, symmetric trim, ex-top/ex-bottom — on pooled, 2018+, **2021–2026**
(the window excluding 2020, declared because the premium is 2020-onward); long/short; the
priority sub-cell; names to half the P&L, top-1/5/10 share, profitable years, the top trade
named with its bar; the |r| > 50% variant.

**The book** (D419's simulator with D421's priority ordering — D427's `sim4`, reproduced
bit-identically against D421's `simulate` on this pool first): for each N, three seeds
(419, 4190, 41900): gross, net, cost, utilisation, trades, per-trade net, same-name blocks,
full-book blocks; **with and without the priority**; the LONG arm at every N; the 10%-borrow
net. Monthly block-bootstrap SE on each book's own daily net series (mean over seeds).

**Controls at N = 4:** (i) **D422's matched-count random cell-2 pools** — 2,649 events drawn from
cell 2, one per name, no priority, 100 draws, cached-input workers, one worker's RSS printed
before the fan-out; (ii) **D421's random-priority control** — 303 events of the pool chosen at
random as the priority, 100 draws, for the priority's delta over the no-priority book.

**Assertions:** `[STAGE0]` 2,649 / 303 / 1,416 reproduce; `[P2]` `sim4` on this pool with no
priority == D421's `simulate`, and with the priority == D421's with `prio`, bit-identical; a
`[COST]` check that the borrow term is zero on every long trade and positive on every short, and
that the 1%-borrow book equals the no-borrow book on the LONG arm exactly; `[RECON]` every
book; `[CHUNK]`/`[NUISANCE]` on the controls.

## 4. The bar — the N = 4 book with the priority, 1% borrow

- **T1** mean net bp/bar over three seeds > 0 by 2 SE (monthly block bootstrap).
- **T2** above the p95 of the matched-count random-pool control (D373's margin).
- **T3** the **2021–2026** net > 0 by 2 SE (the same bootstrap on that window).

**T1 ∧ T2 ∧ T3 makes this book a candidate under the principal's standing rule** — a tradeable
indicator — **and nothing here reads a holdout**; that is a separate, explicit decision of the
principal's. Anything short of all three is not a candidate.

## 5. Predictions (arithmetic: net/bar/slot = trades per day per slot × net per trade; MODERATE)

From D427's L5-REQ (10 slots: 2,552 trades of 3,137, +83.6 gross, 33.5 cost, +3.12 net/bar):
- **X-a** the pool per trade: gross **+88 to +96**, net **+52 to +62** at 1% borrow; 2021–2026
  above pooled; the priority sub-cell above the pool's mean with an SE above 30.
- **X-b** the sweep is **monotone in N**: net/bar rises as slots fall — N=10 **+2.7 to +3.4**,
  N=4 **+5 to +7**, N=2 **+6 to +9** — while utilisation goes ~30% → ~80% → ~95% and trades
  taken fall from ~2,150 to ~1,100. Per-trade net is roughly constant across N (the refill order
  is random).
- **X-c** the priority adds **+0.2 to +0.8** bp/bar at N=4 and **≤ +0.1** at N=10, and its
  delta is **inside the random-priority null** (X-c is the study's second question).
- **X-d** the N=4 book beats its random-pool p95 by more than 2 SE (random cheap-blind pools of
  2,649 net roughly +0.5 to +1.5/bar at 4 slots).
- **X-e** 10% borrow costs **0.3 to 0.7** bp/bar at N=4; the LONG arm at N=4 nets **+3 to +5**
  at ~40% utilisation — below the full pool per bar, above it per trade.
- **X-f** the |r| > 50% variant moves the per-trade mean by **less than 5 bp**.
- **X-g** T1, T2, T3 all hold — stated at moderate confidence, because every layer here is one
  that has already been seen once on this data, and that is exactly why a holdout exists.

## 6. Not in scope

No holdout, no 15m, no change to entry, hold, cell cuts, the price cut or the gap window, no
exits, no sizing by side, no disposition. Twenty-eighth look by object.
