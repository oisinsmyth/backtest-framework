# D655 PRE-REGISTRATION — sell the receiving month against the month after it at the end of the gold and silver roll, and buy it back after first notice: does the forced roll leave a premium that reverts, and does an expected-profit filter make it pay?

*Renumbered 2026-09-28 from D654: the opening model's v2 pre-registration took D652 on main while this study sat on an unmerged branch, and the three studies of that branch (the crack spread, the open-interest Stage 0, the metals roll) each moved up one. Commits before the merge cite the old number.*

*Drafted 2026-09-28 on the principal's word ("Add the addendum and write the pre-registration"; and, while it was
being drafted, "I would also like a expectant profit filter as well, I think all our strategies should have one if
available or viable"). Committed alone, before its runner exists (R8). **No price of the construction has been
read.** Personal book only.*

## 0. Where this comes from

[D654](D654-STAGE-0-RESULT-the-metals-roll-late-and-outside-the-index.md) measured, on open interest alone, that the
expiring gold and silver contracts empty in the last week before first notice (half gone at d = −5 and −6). About
three quarters of that drain falls outside the index roll window (0.74, 0.72), and 85 % of it reappears in the
receiving month. On its heaviest five outside-window days the roll is a quarter of the receiving contract's volume
(0.25, 0.23; every year 2016–2023 between 0.17 and 0.37). The contract after the receiving one trades 15–17 % as
much. Its addendum (§7) fixed the scope before any price: **GC and SI primary; HG and 6C secondary; the grains
excluded.**

**The mechanism.** Holders who cannot take delivery must roll before first notice, whatever the price. Their
buying of the receiving month R, concentrated in a known week, should leave R rich against the month after it (H)
while it lasts. Once the deadline passes, no one needs to buy R, and the premium should revert. The liquidity
provider's trade is to **sell R against H at the end of the drain and buy it back after the deadline**. It never
holds the expiring month (the principal's standing rule), and neither R nor H is near its own delivery at any point
(asserted, §1).

**Read before this record, all disclosed:**
- D654 in full: open interest and cleared volume, 2016–2023.
- D651's quoted spreads at each root's settlement bucket, the cost below.
- The settlement strip's coverage for GC, SI, HG and 6C (2010-06-04 → 2026-09-10).
- **Other lines have read these roots' prices, this construction never:** the trend and carry lines (D555, D556,
  D562) and basis-momentum (D564, D574) read GC, SI and HG settlements in sample and on 2024+ as inputs to their own
  constructions. Per-line multiplicity leaves this line's slices unspent. The overlap in ingredients is the
  front–next spread level those lines signed; this construction's quantity is a six-session change of R − H around
  a first notice day, which none of them computed.

## 1. The construction

**Cycles:** exactly D654's as run, for each root:
- the expiring contract is the root's largest by open interest at d = −30;
- **R** is the later delivery with the largest open interest at d = −20;
- **H** is the delivery after R with the largest open interest at d = −20;
- the deadline D is the first notice day (GC, SI, HG: the last business day of the month before delivery; G-FND
  passed on all three) or the last trading day (6C).

Everything that selects a cycle is known by d = −19.

**The trade, per cycle:** **short 1 R, long 1 H at the settlement of d = −1; close both at the settlement of
d = +5** (business days of the root's own calendar relative to D). Fills are at settlement, the convention every
settlement-strip study here uses, and the cost line charges a crossing on every leg regardless.

- Gross P&L, dollars: `−(R₊₅ − R₋₁) × M + (H₊₅ − H₋₁) × M`, with M the multiplier (GC 100 oz, SI 5,000 oz, HG
  25,000 lb, 6C CAD 100,000).
- **In basis points of R's notional at entry:** gross $ / (R₋₁ × M) × 10⁴. That is the unit the pooled primary is
  scored in.
- **Asserted on every cycle:** R's and H's own deadlines are at least ten business days after d = +5, and all four
  settlements exist.

**Cost, per cycle** (four crossings at D651's quoted half-spread in the settlement bucket, plus the declared $6.00
round trip on each of two contracts, D591):

| root | bucket (ET) | quoted spread | round trip, base | stress (2 × crossing) |
|---|---|---:|---:|---:|
| GC | 13:15 | 3.54 ticks × $10 | **$82.77** | $153.53 |
| SI | 13:15 | 3.55 ticks × $25 | **$189.50** | $366.99 |
| HG | 13:00 | 2.08 ticks × $12.50 | **$64.02** | $116.04 |
| 6C | 14:45 | 1.14 ticks × $5 | **$23.40** | $34.80 |

D651's quotes are the front outright in 2025–26. The deferred R and H quote wider, and a listed spread quotes
tighter; the base is the declared line, the stress is reported beside it. Net = gross − base.

**The in-sample window:** every cycle whose d = +5 settlement is on or before **2023-12-29**. The strip is filtered
before 2024-01-01 at the loader and asserted after (`frozen.filter_before`, `assert_none_at_or_after`).

## 2. The expected-profit filter (the principal's standing request)

**The size predictor, known before entry:** `x = (the expiring month's open-interest decline from d = −30 to
d = −2) × (R's gain over the same days ÷ that decline, clipped to [0, 1]) ÷ R's summed cleared volume over d = −6 …
−2`. This is the cycle's own roll flow as a share of the receiving contract's trade, D654's quantity through the
last figure published before entry (d = −2's open interest is published the evening of d = −2).

**The pass-through, from earlier cycles only:** `b` = the no-intercept least-squares slope of gross bp on x, over
every earlier in-sample cycle **of the same root**. The first eight cycles of each root form the burn-in and are not
traded by the filtered book.

**The rule:** trade the cycle if **b > 0 and b × x ≥ 2 × (base cost in bp at entry)**. D649's multiple of two, fixed
here.

The filtered book is scored beside the unfiltered one (§4). It is **promotable only if the unfiltered mechanism
bars B2 and B3 pass**, because a filter on no mechanism selects noise. It needs **at least 15 traded cycles**, or its
verdict is UNRESOLVED.

## 3. The nulls and the control

- **Placement null (the construction's own).** The same entry–exit pattern shifted by k business days for every k
  from −60 to +40 with |k| > 10, on the same R and H per cycle, skipping any placement where a leg lacks a settlement
  or where R or H would be within ten business days of its own deadline. **Enumerated**, so the p95 has SE 0. The
  statistic is the pooled mean gross bp; the full offset profile is stored.
- **Negative control: the same trade at month-ends with no roll.** GC, SI and HG list serial months that carry
  almost no open interest (GC's F, H, K, N, U, X; SI's and HG's F, G, J, M, Q, V, X). At each serial month's first
  notice day there is no forced roll. The control places the same trade there: R_c is the largest delivery at
  d = −20 later than the serial month, H_c the next largest after it, same offsets. It shares the month-end calendar
  and the contracts' nature and lacks only the flow. For 6C, the control is the last-trading-day rule applied in the
  non-quarterly months.

## 4. The bar

**Primary: GC and SI pooled, unfiltered, net bp per cycle.**

- **B1** mean net > 0, Newey–West t (one lag, cycles in time order) ≥ 2.0.
- **B2** mean gross above the enumerated placement null's p95.
- **B3** mean gross minus the serial-month control's mean gross > 0, Welch t ≥ 2.0.
- **B4** the count of calendar years with positive mean gross is at or above the placement null's p95 of the same
  count (a year count carries its own null, since a random placement's year count is not "half").
- **B5** median gross > 0, and the mean with one cycle trimmed from each tail > 0: not a one-cycle book.

**Filtered book:** net mean > 0 with t ≥ 2.0 on its traded cycles, ≥ 15 of them, and net per traded cycle above the
unfiltered net. Promotable only with B2 and B3.

**Routing.**
- **All of B1–B5** → the unfiltered construction is a candidate for the personal book.
- **B2, B3, B5 but not B1** (the premium is real, the average trade does not clear cost) → the filtered book decides.
  If it passes, the filtered construction is the candidate.
- **B2 or B3 fails** → the forced roll leaves no reverting premium in these spreads, and the recommendation is to close
  the delivery line.

A candidate is not admitted. Its forward read is on 2024-01-01 → 2025-02-28 (outside the vault) and in the joint
vault run, each on the principal's word after a freeze, with the power stated first.

**Secondary cells, HG and 6C:** the same statistics, reported cell by cell. Neither is promotable unless the primary
passes.

## 5. What is reported

**All four groups** (CLAUDE.md):
1. **Performance, net and gross:** Sharpe and Sortino of the daily book at one spread per root, exposure, volatility,
   max drawdown, mean move per trade against 2 × cost, breakeven cost.
2. **Trade distribution:** count, mean, median, hit rate, payoff, skew, kurtosis, and the ex-top, ex-bottom and
   symmetric trimmed means.
3. **What the winners depend on:** the GC/SI split, years, and the five largest cycles named.
4. **The nulls as distributions:** p50 and p95 beside the score.

**Beside those:**
- **The mechanism check, predicted positive, not gating:** the mean change of R − H in bp from d = −10 to d = −1. The
  roll should push R up against H during the drain. If the reversion pays and the drain shows no push, the story is
  wrong.
- Exits at d = +1, +3 and +10.
- The filter's traded share and its b path.
- **The component line:** net Sharpe at one spread, hit rate, skew, gross beside net, and the correlation with the
  admitted MACD arm's daily series.

**POWER, first, before the runner scores anything:** the runner's `--power` mode reads only the placement offsets
(|k| > 10, never the event window). It reports the standard deviation of the six-session R − H change in bp, the MDE
at t = 2 for the in-sample cycle count, and the power of the forward windows: 2024-01 → 2025-02 holds roughly seven
GC and six SI cycles, and about fifteen more with the vault. It gates nothing.

## 6. Predictions, written before any price

1. **The mechanism sign holds on both roots:** R richens against H from d = −10 to d = −1.
2. **The gross is small:** a few basis points a cycle, positive on the pool.
3. **B1 fails:** silver's cost (15–25 bp of notional a round trip) is larger than the premium, and gold's is about
   the size of it.
4. **The control sits inside its placement null:** month-ends without a roll pay nothing.
5. **The filter trades fewer than half the cycles** and almost none of silver's.
6. **Whatever there is, gold carries it.**

## 7. Files

`scripts/run_d655_metals_roll.py` (`--selftest`, `--power`, `--run`) → `data/d655_metals_roll.json`. The selftest
must show:
- the cycle selection reproduces D654's cycle count and its R and H for GC and SI;
- the P&L sign is right in money: R falling against H pays the short-R, long-H position;
- the no-delivery assertion raises when R's deadline is inside the window;
- the filter's b uses only earlier cycles (a future cycle injected into the fit raises);
- the placement null excludes |k| ≤ 10;
- the holdout guard raises on a 2024 settlement.
