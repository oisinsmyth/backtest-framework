# D656 STAGE 0 DESIGN — the soybean board crush: do processors pay a premium for hedging their margin forward, and does the nearby margin revert towards next year's without becoming an era label?

*Drafted 2026-09-28 on the principal's word ("start the Crush spread Stage 0"). Committed alone, before its runner
exists (R8). **Nothing about the crush's time path has been computed.** Personal book only.*

## 0. What reopens, and what the crack taught

`ALPHA_PROGRAMME.md` §3.2 names three processing spreads (crack, crush, spark). The crack was tested in
[D653](D653-STAGE-0-RESULT-not-supported-the-deviation-is-an-era.md) and closed by the principal, every crack
variant. **The crush has never been tested**, and the principal's instruction reopens it from the list D582 closed.

D653 found three things that shape this design:

1. **A deviation from a three-year same-month norm is an era label.** The crack sat wholly below its norm in 2016
   and 2020 and wholly above it in 2022–23; one year of eight held both states. The soybean crush had its own regime
   in 2021–23: renewable-diesel demand lifted soybean oil and the margin to record levels. **So this record does not
   re-run the norm test.** Its reversion question (S2) measures the nearby margin against the same season's margin
   **one year later on the same day's curve**, a gap that adjusts to a regime as soon as the curve does.
2. **A per-year count of slopes passes for a random walk** (Kendall's bias: P(≥ 6 of 8) = 0.994 in D653). **Every
   year-count bar here carries its own simulated null.**
3. **The curve prices an expected closing, so a fixed contract carries no reversion unless the curve is biased.**
   What D653 did find, parked and later closed with the crack, was a roll-down: a fixed crack contract rose +$0.66
   a barrel per four weeks (t 2.0). **For the crush, that is the hedging mechanism itself (S1).** Crushers
   structurally sell their forward margin (the "board crush") to lock processing profit. Whoever buys it is paid a
   premium, which shows up as a fixed contract's margin rising as delivery approaches, beyond whatever the margin
   level does.

## 1. The object

**Legs**, settlements from `fut_settle_strip.csv.gz`: ZS (cents a bushel), ZM (dollars a short ton), ZL (cents a
pound). **The board crush in dollars a bushel:** `C = 0.022 × ZM + 0.11 × ZL − ZS / 100` (a bushel yields 44 lb of
meal and 11 lb of oil). **One unit** is the exchange's crush ratio, 10 ZS : 11 ZM : 9 ZL (50,000 bushels, 30
contracts).

**Pairs:** soybean months F, H, K, N, Q, U with meal and oil of the same letter, and **soybean X with meal and oil Z**
(the board-crush convention; products' V is unused). A pair is named by its soybean delivery.

**Contract resolution, per row:** each strip row is resolved from the code's first expiry on or after that row's own
session ([D655](D655-RESULT-no-roll-premium-the-control-earns-more.md)'s `resolve_rows`). A code resolved once files
the next decade under the old delivery.

**The principal's delivery rule:** no leg is held within ten business days of its first notice day (the last
business day of the month before its delivery month). **Every holding window ends at least ten business days before
the earliest first notice day of its legs**, asserted.

**Weekly sampling:** the last session of each ISO week on which all three roots settle. Horizon **h = 4 weeks**; the
**near pair** at t is the nearest pair whose earliest first notice day is at least h + 2 weeks after t.

**The in-sample window:** every observation whose target date is on or before **2023-12-29**, from **2011-01**
(the strip starts 2010-06; S2 needs a year-ahead pair; thirteen years). 2016–2023 is reported beside it. The loader
filters before 2024-01-01 and asserts after. **Other lines have read these roots' prices, this construction
never:** the seasonal soybean and product spreads (D567–D571), basis-momentum (D564, D574, including 2024+) and
trend and carry (D555, D556, D562, including 2024+).

## 2. S1 — the processors' premium

- **Quantity:** `Y1(t) = C_near(t + h) − C_near(t)`, the four-week change of the near pair's crush, same contracts,
  in dollars a bushel.
- **The roll-down part:** `R(t) = Y1(t) − ΔL(t)`, where `L` is the constant-tenor crush (the near pair's crush,
  re-selected every week). Y1 is what a holder earns. R is the part a curve premium explains rather than a move in
  the margin's level (2011–2023 contains the 2021–23 boom, which lifted every fixed contract with it).

| bar | declared |
|---|---|
| **S1-B1** | mean Y1 > 0, Newey–West t (4 lags) ≥ 2.0 |
| **S1-B2** | mean R > 0, Newey–West t ≥ 2.0: the premium is not the level's trend |
| **S1-B3** | the count of years with positive mean Y1 is at or above the **zero-drift null's p95**: 2,000 random walks with Y1's own weekly volatility and the same observations per year, seed 656 |
| **S1-B4** | mean Y1 > 0 in every leave-one-year-out fit (not 2021 or 2022 alone) |
| **S1-B5** | the premium per holding cycle ≥ 3 × the round trip. A long crush is rolled once per pair, about every two months, so the bar is the mean change from entering a pair to leaving it (the earliest first-notice rule) against $0.0100 a bushel (§5) |

## 3. S2 — reversion towards next year, regime-proof

- **The gap:** `G(t) = C_near(t) − C_year(t)`, where C_year is the crush of the **same pair letter one year later**
  on the same day. Both are on the same curve, same season. G says "this year's margin is above next year's" without
  any historical norm.
- **The target:** `Y2(t) = G(t + h) − G(t)`, the same two pairs.
- **The trade it implies:** short the near crush, long the year-ahead crush, when G is high.

| bar | declared |
|---|---|
| **S2-B1** | `Y2 = a + β G`: β < 0 with Newey–West t (4 lags) ≤ −2.0 |
| **S2-B2** | β below the enumerated rotation null's p05 (offsets 27 … N − 27 weeks, a 26-week purge at both ends) |
| **S2-B3** | the count of years with a negative within-year β is at or above the **random-walk null's p95** (G simulated as a random walk with its own weekly volatility, same per-year sizes, 2,000 draws, seed 656): D653's lesson |
| **S2-B4** | at least 60 % of years hold ≥ 8 weeks in each extreme tercile of G: the gap is a state, not an era |
| **S2-B5** | `|β| × median |G|` ≥ 3 × the round trip of two crush units ($0.0200 a bushel) |
| **S2-B6** | the year-ahead legs trade: over 2016–2023, from D654's open-interest fixture, each year-ahead leg's median cleared volume is ≥ 5 % of the near leg's, in the weeks it is used |

## 4. Routing

- **Each premise routes on its own.** All of its bars pass → a pre-registration of that construction for the personal
  book, **carrying an expected-profit filter** (the principal's standing rule: trade when a point-in-time projected
  gross is at least twice the round trip), put to the principal before any 2024+ price is read.
- A premise failing B1 or B2 → the recommendation is to close that premise.
- **Both failing → close the crush line.**
- Two premises is a family of two. Any pre-registration that follows states it.

## 5. Cost

From [D651](D651-RESULT-no-handoff-trough-the-night-is-one-ramp-from-the-reopen.md)'s map, 14:00–14:15 ET (the
grains settle at 14:14–14:15 ET): quoted spread 1.04 ticks on ZS ($12.50), 1.09 on ZM ($10.00), 1.31 on ZL ($6.00).
Half of it per leg, plus the declared $6.00 round trip per contract (D591): **$160.32 a side, $500.64 a round trip
for one 10 : 11 : 9 unit, $0.0100 a bushel.** The year-ahead legs quote wider than the front outrights D651
measured, so the stress line doubles the crossing: $821.28, $0.0164 a bushel.

## 6. Predictions, written before the run

1. **S1-B1 holds** (a fixed crush rises towards delivery). **S1-B2 is borderline** (t between 1.5 and 2.5): part of
   Y1 is the 2021–23 level move.
2. 2021 or 2022 is the most influential year for S1, and **S1-B4 holds** anyway.
3. **S2's β is negative** (the near margin converges towards the year-ahead one), with rotation rank ≤ 0.10.
4. **S2-B4 passes**: the gap changes state within years, unlike D653's norm deviation.
5. **S2-B6 fails for soybean oil** (the year-ahead oil contract is thin), and S2 does not route to a construction on
   that alone.
6. **At most one premise routes.**

## 7. Files

`scripts/stage0_d656_crush.py` (`--selftest`, `--run`) → `data/stage0_d656_crush.json`. The selftest must show:
- per-row resolution picks the right decade on a recycled code;
- the pairing sends November beans to December products;
- no window ends inside ten business days of a leg's first notice day;
- R equals Y1 minus the constant-tenor change exactly;
- the year-count nulls reproduce Kendall's bias on a random walk (S2) and a coin-flip on a zero-drift walk (S1);
- the rotation excludes the purged offsets;
- the holdout guard raises on a 2024 settlement.
