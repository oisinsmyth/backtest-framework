# D363 — the cost lines on the two-sink fade: the spread on the entry day rather than the trailing month, the execution bounds, and cost-aware sizing

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). Nothing here is a
result and nothing here is a new signal: the ledger is D362's two-sink arm, reproduced to
1e-9, and this record changes only how it is **costed** and **sized**. **No holdout data is
read.** The quoted-spread validation (D336, the principal's pull) is on hold and this record
does not pre-empt it: every line here is an OHLC estimator and is labelled as one.
**Date:** 2026-09-06
**Area:** Cost model · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

The two-sink gated gap-up fade is +61.7 gross a trade on 3,079 trades and pays 89 bp a
round trip under PUB (39 under PB). The D361 export says where that cost sits: the edge is in
the widest-spread quintile (gross +220 on names 94 bp a side), the hold is already at its
efficient length (the P&L accrues through bar 10 and flattens), and commission and borrow
are 3 bp each. So there is nothing to cut in the hold or the small items, and a spread
ceiling removes the signal. What is left is **the estimate itself**: PUB is a 21-bar
trailing mean of the Corwin–Schultz spread, and these entries are on top-decile volume days,
when spreads compress; and **the execution**: the kernel fills at the open print and exits
at the close print, and an order in either auction does not cross the spread. This record
measures the first, bounds the second, and tests two sizing rules that use the cost.

## 1. The ledger

D362's A2 arm exactly: D361's G2 × T2 with events hitting S1 or S2 removed from the signal,
re-simulated, cap 10, hedged; 3,079 trades, +61.71 gross, asserted to 1e-9. No exit, gate,
sink or threshold changes.

## 2. The cost lines, per trade

All from the record's own Corwin–Schultz implementation (the one that builds `HALF_PUB` and
`HALF_PB`; asserted to reproduce them), at the held name; commission 2 × $0.005 a share at
the as-traded price; GC/HTB borrow as before.

| line | entry side | exit side |
|---|---|---|
| **PUB** (as D362) | 21-bar trailing mean at the entry bar | the same value |
| **PB** (as D362) | the per-bar median convention at the entry bar | the same value |
| **EW**, the entry-window line | the mean of the per-bar CS half-spread over the three bars g−1, g, g+1 (the day before the gap, the gap day, the entry day), zero-clamped as PUB clamps | the mean over the three bars around the exit bar e−1, e, e+1 |
| **EW1**, beside | the estimator's own two-day pair (g, g+1) | the pair (e−1, e) |

`2c` under each line = entry half-spread + exit half-spread + commission; net = gross − `2c`
− borrow. The by-spread-quintile table (quintiles of PUB, as the export screen cut them) is
reported under every line.

## 3. The execution bounds, per trade

The kernel's fills are the opening print (entry) and the closing print (exit at the cap). Three
points, reported and deciding nothing:

- **full crossing** — `2c` under each line (the record's convention);
- **half crossing** — one side crosses, the other is an auction print: half of `2c`;
- **auction** — neither side crosses: commission and borrow only. **Impact is not modelled**;
  in its place the record reports **participation**: the position as a share of the entry
  day's dollar volume at $10k, $25k and $50k a position, its median and its 90th
  percentile, and the share of trades under 1% at $25k. The same at the exit bar.

## 4. Sizing, two arms, weights as D362's W

- **INV** — weight ∝ 1 / `2c` under PUB, normalised to a mean weight of one: capital
  follows cheapness.
- **U** — the in-sample shape: the middle three PUB quintiles at half weight, the tightest
  and widest at full. Its null is D362's FROT on the weight: each name's weights permuted
  across its own trades, 200 draws (the per-name weight multiset kept); the statistic is
  net per unit capital under PUB.

Both arms report gross and net per unit capital under every line, the t on the weighted
mean, and the capital used; the weighted deployed base beside as D362's W.

## 5. Predictions

Q1 is load-bearing. Q5 is against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* the entry-side EW half-spread is **at least 25% below the PUB half-spread at the median** of the ledger: spreads compress on the entry days. |
| **Q2** | under the EW line the ledger **nets > 0 per trade** after commission and borrow. |
| **Q3** | the exit-side EW half-spread is within 10% of PUB at the median: the exit day is an ordinary day. |
| **Q4** | at $25k a position, the entry-day participation is under 1% for at least 90% of trades. |
| **Q5** | *(against)* the middle three PUB quintiles net > 0 under the EW line. |
| **Q6** | INV lowers net per unit capital under **both** PUB and PB relative to equal weight: the gross is in the wide names and inverse-cost sizing gives it away. |
| **Q7** | U's net per unit capital under PUB is above the p95 of 200 within-name weight permutations. |
| **Q8** | the EW1 two-day pair is zero-clamped on more than 30% of entries, and the three-bar EW on fewer than 15%: the pair is too noisy to be the line. |
| *check* | the ledger reproduces D362's A2 (3,079, +61.71) and its PUB / PB `2c` (88.77 / 38.7) to 1e-9; the runner's per-bar CS estimator averaged over 21 bars reproduces `HALF_PUB` at 300 sampled name-bars to 1e-9. |

## 6. Stop conditions

These state the construction's status; **the avenue is the principal's (R15).**

- **Q1 and Q2 hold** → on the record's own estimator the entry-day spread is materially
  below the trailing month and the fade nets positive under it; the number waits on D336
  to say whether the estimator is right at all.
- **Q1 fails** → the trailing mean is the right estimate for these days; the cost is what
  PUB says; the execution bounds are the remaining question.
- **Q7 fails** → the U shape is a description of this sample; INV and U are dropped; equal
  weight and D362's per-hit sizing stand.
- Nothing is promoted. Book: empty.

## 7. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** · **[HOLDOUT-GUARD]** | via the shared prep; every file open audited |
| **[ID]** | the ledger == D362's A2 to 1e-9; PUB and PB `2c` == D362's |
| **[CS]** | the runner's per-bar Corwin–Schultz half-spread, averaged over the record's 21-bar window, == `HALF_PUB` at 300 sampled name-bars to 1e-9; the clamp rule identical |
| **[EW]** | the entry- and exit-window values == a direct recomputation from the raw high/low on 300 sampled trades |
| **[PART]** | participation == position / (as-traded close × volume) on the entry and exit bars from the raw bars |
| **[W]** · **[PERM]** | weighted arithmetic as D362's [W]; every permutation keeps each name's weight multiset and is never the observed |
| **[6]** | [ID] on a perturbed ledger; [CS] on a perturbed window; [EW] on a perturbed high; [PERM] on a wrong multiset |

## 8. Files

`docs/decisions/D363-the-cost-lines-on-the-two-sink-fade-entry-window-spread-execution-bounds-and-cost-aware-sizing.md`
(this record) · `scripts/run_d363_cost_lines.py` (stages `--selftest`, `--perm --draws N --part
p`, `--report`) · `data/d363_perm_p*.json`, `data/d363_cost_lines.json` (to follow). Reuses
`scripts/run_d362_sink_filter.py`, `scripts/run_d361_regime_gated_short.py`, the record's
Corwin–Schultz module, `scripts/d361_export_trades.py`, `scripts/d348_prep.py`,
`scripts/d337_borrow.py`. The holdout fixture is not read; D336 is not pre-empted.
