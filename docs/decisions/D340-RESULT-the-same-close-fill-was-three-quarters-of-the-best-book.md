# D340 RESULT — the same-close fill was three-quarters of the best book: `retrace_leg` +18.93 → +5.14 bp/bar under a next-open fill, the incumbent −12.68 → −15.90

**Status:** RESULT. Pre-registered at `9b612b0`, simulator flag + helper + runner at
`ee976fc` — both before this file existed (R8).
D333-bounded panel, D334 cache, F0 on `retrace_leg`, PUB primary, close fill = the
convention every D300-family record used.
**Date:** 2026-09-05
**Area:** Simulator convention · cost model · every book since D300

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted. `retrace_leg` is not a candidate.**

---

## 1. The headline

Same cell, same gate, same exit rule; the only change is that a position entered at bar
t earns `close[t]/open[t] − 1` on its entry bar instead of `close[t]/close[t−1] − 1`.

| `retrace_leg` F0, k=20 | close fill (D338) | **open fill** | change |
|---|--:|--:|--:|
| gross bp/bar | +32.37 | **+18.06** | −14.31 |
| **PUB net bp/bar** | +18.93 | **+5.14** | **−13.78** |
| PB net bp/bar | +23.43 | +9.97 | −13.46 |
| PUB net Sharpe | +0.546 | **+0.173** | |
| gross t | +3.32 | +2.16 | |
| maxDD bp | 13,829 | 22,727 | |
| mean move per trade / PUB 2c | +165.1 / 2.43× | +94.0 / **1.42×** | |
| breakeven half-spread per side | 80.3 = 2.48× | 44.8 = **1.42×** | |
| PUB net after GC+HTB | +18.60 | +4.83 | |
| invariant PUB net per trade | +10.02 | **−18.27** | |
| long leg PUB net per trade | +46.23 | **−12.03** | |
| short leg PUB net per trade | −29.02 | −24.98 | |

**Seventy-three percent of the best book's published net was the overnight gap.** Under
an honest fill it nets +5 bp/bar under the published spread convention, its per-trade
lens is negative on both legs, and the long leg that carried the programme's best
per-trade number since D323 loses 12 bp a trade.

| incumbent C0, k=5 | close fill | **open fill** | change |
|---|--:|--:|--:|
| gross bp/bar | +25.36 | +21.39 | −3.97 |
| PUB net bp/bar | −12.68 | **−15.90** | **−3.21** |
| PB net bp/bar | +7.15 | +2.29 | −4.86 |
| invariant PUB net per trade | −34.48 | −43.32 | |

**Q4 falsified**: the incumbent moves by 3.2 bp/bar, not under 2. Its k=5 book turns
over 2.4× as often as `retrace_leg`'s, so a smaller premium per entry costs it nearly
as much per bar. The stop condition executes: **D318's re-costing is re-opened under the
open fill** — every net number in the stack from D300 onward is a same-close-fill number.

## 2. The implementation-lag premium, per entry

`mean(sgn · (r1T − ocT))` at the entry cell over the close-fill ledger — what the
convention credited to a position before it could have been filled:

| | n | name gap | median | t | share positive | hedge | **excess** |
|---|--:|--:|--:|--:|--:|--:|--:|
| `retrace_leg` long | 635 | **+44.8 bp** | +5.3 | +1.19 | 56% | +1.2 | +43.5 |
| `retrace_leg` short | 621 | **+27.2 bp** | −1.3 | +1.45 | 46% | −7.0 | +34.3 |
| incumbent long | 1,554 | +20.6 bp | | +2.74 | | | |
| incumbent short | 1,512 | −15.8 bp | | −1.33 | | | |

**Q2 confirmed, and it is worse than predicted: both of `retrace_leg`'s legs were
flattered.** Names that broke below their swing low gap *up* at the next open (the long
leg's +44.8), and names above their swing high gap *down* (the short leg's +27.2, in the
short's favour). A structure-breakdown signal computed at the close is partly a forecast
of the overnight reversal, and the same-close fill booked that forecast as if it were
tradeable. The premium is fat-tailed — a median of +5 against a mean of +45 — so it is,
like everything else about this book, a few names' gaps.

## 3. It is not only the entry bar: the two fills are different books

**Only 378 of the 1,256 close-fill trades recur under the open fill.** The exit-event
sets diverge at bar 1,002 — the first exit of any kind — because the target rule reads
the accumulated excess, the entry bar's excess differs, so the first exit fires on a
different day, a slot frees on a different day, and from there the books walk apart
([E2]). **VSA on 2025-01-31 is not held under the open fill at all**: it was rank 0 in
the long gate under both fills, but both long slots were taken — EA since 01-27 and MANH
since 01-30, a 20-bar hold that lost 1,920 bp. The +99.5% credit the pre-registration
named as its check is reproduced off the array and never enters the ledger. The
opportunity cost FINDINGS §10 names and nothing measures is doing part of this work; the
mark does the rest.

That is why **Q3 failed in the wrong direction**. Total P&L fell 43%; RXT and NKA kept
theirs (their entry bars were −5% and +2%, the gaps came later in the hold); the top-5
trade share went **41.8% → 53.6%**, names to half the P&L 5 → 4, top-10 name share
65.8% → **83.7%**, and the cheapest price tercile went from 46% of P&L to **90.6%**. The
open fill removed the gaps and left the squeezes.

## 4. The four groups on the open-fill cell (PUB)

| group 2 | close | **open** |
|---|--:|--:|
| trades | 1,256 | 1,236 |
| mean / median bp | +165.1 / +233.9 | +94.0 / +222.0 |
| win rate / payoff | 72.6% / 0.60 | 71.3% / 0.52 |
| skew / kurtosis | +8.8 / 165 | +3.8 / 81 |
| ex-top 1% / ex-bottom 1% / **trimmed** | +70.3 / +221.1 / +125.9 | **+18.2** / +155.7 / **+79.7** |
| top 1% / bottom 1% share | +58% / −33% | **+81% / −64%** |

The symmetric trim, +79.7 against a PUB round trip of 66.4, clears cost by 1.20×; drop
the twelve best trades and the mean move per trade, +18.2, is a quarter of the round
trip. Group 3: 663 names, **4** to half the P&L, 8 of 14 years net-positive (gross 9),
dead names 16.1%, both era halves still positive. The book under an honest fill is a
squeeze book with a thinner core.

## 5. The null, on the open-fill cell

| statistic | score | p50 | p95 | max | p |
|---|--:|--:|--:|--:|--:|
| gross bp/bar | **+18.06** | +4.30 | +16.16 | +16.16 | 0.0050 |
| gross Sharpe | +0.606 | +0.181 | +0.802 | +0.802 | **0.124** |
| net Sharpe PB | +0.335 | −0.101 | +0.400 | +0.400 | **0.124** |
| net Sharpe PUB | +0.173 | −0.392 | +0.108 | +0.108 | 0.0050 |

**Q6 confirmed on the pre-registered statistic** — gross bp/bar above the null's p95,
and the gross null has teeth (p95 > 0). **On the Sharpe lens the cell is inside its
null**: gross Sharpe 0.61 against a null max of 0.80, p = 0.12. The close-fill cell was
above the null's maximum on every statistic (D338); the open-fill cell is above it on
one. What survives the honest fill is a gross-return ordering with more variance than
a random rotation of the same gate.

**A limitation of the family's null, stated here for the first time:** the rotation
draws `shift ∈ {1, …, 24}`, so 200 draws are **24 distinct books** and p95 equals the
maximum whenever the top value recurs in ≥ 5% of draws. The floor on p is 1/25, not
1/201; "p = 0.0050" means "above all 24 rotations". This applies to every D300-family
null since D300, including D338's.

## 6. Predictions

| | | outcome |
|---|---|---|
| **Q1** | *(load-bearing)* PUB net falls by > 5 bp/bar | **CONFIRMED** — −13.78 (PB −13.46) |
| **Q2** | long-leg premium positive and larger than the short's | **CONFIRMED** — +44.8 vs +27.2; both legs flattered |
| **Q3** | top-5 trade share < 35% | **FALSIFIED** — 41.8% → **53.6%**; the gaps left, the squeezes stayed |
| **Q4** | incumbent moves < 2 bp/bar | **FALSIFIED** — −3.21 |
| **Q5** | fallback < 1% of cells, < 2% of entries | **CONFIRMED, vacuously** — 0 of 4,137,239 priced cells lack a usable open |
| **Q6** | open-fill cell above its gross null p95 | **CONFIRMED** on gross bp (above the max); inside the null on gross Sharpe (p 0.12) |
| *check* | VSA +329.8% → +99.5% | **reproduced** off the array; VSA is not held under the open fill (slot contention) |

Four of six. Q5 is not evidence of anything — the fixture has an open on every priced bar.

## 7. Stop conditions, executed

- **Q1 holds** → the same-close fill is a **measured hole** in STACK §3. Every net number
  quoted from D300 onward carries an open-fill companion wherever it is quoted again;
  new studies declare the fill they score. The default stays `"close"` so every published
  identity reproduces.
- **Q4 fails** → **D318's re-costing is re-opened under the open fill.** Owed as a
  pre-registered re-run of the stack's cells, not done here.
- Q6 held on the pre-registered statistic; the Sharpe reading is recorded beside it and
  D338's "the signal is real" stands only as "the gross ordering survives an honest
  fill, with more variance than its null".

## 8. Deviations from the record's letter

1. **[E1]'s wording was imprecise.** It said P&L differs "on exactly the trades whose
   entry cell has `ocT ≠ r1T`"; but `mkt_oc ≠ mkt` on every bar, so every trade differs
   (636 of 636) though only 632 entry cells differ in the name return. The runner asserts
   the exact decomposition `sgn·((ocT − r1T)[e0,row] − (mkt_oc − mkt)[e0])` to 1.9e-16
   instead, which is the statement the record meant.
2. **`V9.per_leg`'s `premium_bp` and the borrow schemes read `r1T` on the entry bar under
   both fills** (diagnostics only; the net numbers do not depend on them). Recorded in
   the JSON note.
3. The "check" (VSA's credit) is reproduced but its trade does not exist under the open
   fill; §3 explains why and the check stands as a property of the array.

## 9. Assertions

| | |
|---|---|
| **[ID]** | (a) N=19/none bit-identical to D303's no-exit control, 24,248 entries; (b) `retrace_leg` close-fill cell reproduces D338 to 0.0 — gross, net, Sharpe, invariant, both legs, PB and PUB; (b′) C0 reproduces D333's `C0 N=2/*/new` cells to 0.0; (c) `simulate(A2) == simulate(A)` bitwise on the close fill — book, `ent`, full ledger, both lenses; (d) the open fill differs on 2,954 of 4,187 bars |
| **[V]** | `ValueError` on `fill='x'`; `KeyError` on the plain cache; `ValueError` on either shape mismatch |
| **[E1]** | `use_target=False`: identical `(row, e0, age, side)`, `ent`, `cnt0`, `cnt1` on 636 trades; P&L differs by exactly the decomposition above to 1.9e-16 |
| **[E2]** | target: exit sets first differ at bar 1,002 (2013-12-26, the first exit of any kind); all trades closed before it identical; `ent` first differs at ≥ t*; 378 of 1,256 close-fill trades recur |
| **[G]** | synthetic +50% / −50% gap with a +1% market gap, flat open-to-close: close fill books +0.49 / +0.51, open fill books exactly 0.0 / 0.0 — `mkt_oc` pinned |
| **[F]** | 0 of 4,137,239 priced cells fall back |
| **[P]** | all 8 ledgers recomputed from `(row, e0, age, side)` to 4.4e-16; the close arrays miss the open-fill ledger by up to 0.559 |
| **[2]** | `contributions_fill − contributions == sgn·w·(ocT − r1T)[e0,row]` to 8.7e-17 on 1,236 trades; open-fill gross reconstructs to −0.03 bp, 4 positions open at T, no hole |
| **[L2]** | `ocT` equals `close/open − 1` rebuilt from the raw `Bar` objects on all 3,000 sampled cells (1,217 names); `r1T ≠ ocT` on all 3,000 sampled ex-date cells |
| **[N]** | 200 of 200 draws valid |
| **[6]** | [ID](b) raises on +5 bp handed on 200 masked bars |

D306's own `--selftest` on the edited module: [4] passes, [3b] passes, [10] fails at
7.53 bp against the known-stale `d300_width.json` (D337 §10; unchanged). **Speed:** 72 s
after the grid build.

## 10. What this establishes

1. **The D300 family's fill convention credited the overnight gap to every entry.** On
   `retrace_leg` that was 44.8 bp per long entry and 27.2 per short — larger than the
   published half-spread on either leg. **The cost model was missing a term bigger than
   the spread it argued about for three studies.**
2. **`retrace_leg` under an honest fill is +5 bp/bar PUB, inside its null on Sharpe,
   and negative per trade on both legs.** With D338's concentration and the census's
   floor finding, it is not a candidate on this fixture. What remains is a gross
   ordering worth +18 bp/bar against a null max of +16, in a book whose top four names
   are half its P&L.
3. **A structure-breakdown signal at the close is partly a forecast of the next open.**
   Both legs' gaps run the book's way. That is information about when the edge is
   realised, and a real book cannot be there for it.
4. **Every net number since D300 is a same-close-fill number.** The incumbent's is
   3.2 bp/bar too high; the best book's was 13.8 too high. The companions are owed where
   the numbers are next quoted, and D318's re-costing is re-opened.
5. **The family's rotation null has 24 distinct values.** A p of 0.005 is "above all 24";
   the resolution is 1/25.

## 11. Files

`data/d340_open_fill.json` · `scripts/run_d340_open_fill.py` · `scripts/d340_fill.py` ·
`scripts/run_d306_width_exits.py` (the `fill` flag)
