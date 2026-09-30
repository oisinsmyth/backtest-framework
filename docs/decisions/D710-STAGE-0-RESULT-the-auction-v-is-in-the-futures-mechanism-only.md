# D710 STAGE 0 RESULT — PRESENT, then MECHANISM ONLY: the dealers' auction-day V is in the Treasury futures at about two-thirds of the paper's cash size (pooled z +0.26, t 4.98, above every enumerated placebo schedule, the 2015–23 era holding its share), and the unfiltered legs gross +$17.48 (t 2.89) but net −$1.18; the paper-sized filter nets +$43.85 a trade at t 1.45, carried by the 30-year pre-auction short

*2026-09-30. One run of `scripts/stage0_d710_auction_v.py` (27 s).*
- **The order:** the [design record](D710-STAGE-0-DESIGN-treasury-auction-intraday-v.md) was committed before any
  builder or runner, and its amendment A1 (before the run) with the builders, calendars and runner, before the run.
- **The principal's rulings:** "Reopen hourly clock for C" (D499's closure, for this use), and "Fetch them" (FOMC
  2010–2015).
- **Checks:**
  - the independent lag loop reproduced all 800 events (Δ differs by 0.0 bp);
  - the post-window from 13:05 differs from one starting at 13:00 (the release jump exists and is excluded);
  - the component builders reproduced D504's arm per year and F2's 252 trades at +$13.208968 before scoring.
- **What it is:** in-sample, 2010-06-07 → 2023-12-29. No bar or price dated 2024-01-01 or later was read.
- **Outputs:** `data/stage0_d710_auction_v.json`, `data/d710_events.csv.gz`, `data/d710_trades.csv.gz`.

## The answer in one line

**The premise is PRESENT and the trade is MECHANISM ONLY.**
- Primary dealers' pre-auction concession and post-auction recovery, which the New York Fed documents in cash
  Treasuries (SR 1188), appear in the futures bars. Every premise gate passes, and all seven of the paper's free
  predictions hold.
- **The unfiltered two-leg trade pays its gross and not its full-size round trip.**
- The expected-profit book that the paper's own magnitudes select (mostly the 30-year short into the auction) nets
  +$43.85 a trade. That is t 1.45, under the declared t ≥ 2.

## 1. The premise (800 events, six tenor pairs, auction-day window move minus its ±1-week controls)

| statistic | value | gate |
|---|---|---|
| pooled mean z (full span) | **+0.259, t 4.98** (the larger of NW and week-clustered SE) | G1 yes |
| enumerated placebo schedule N1 (1,606 offsets) | p50 −0.013, p95 +0.065; **percentile 1.000** | G2 yes |
| achieved share of the transfer-adjusted cash V, full span | **0.68** (the brief's literal cash-bp bar: 0.49) | G3 yes (≥ 0.5) |
| the same, 2015–2023 (E2) | **0.69**, z +0.169, t 2.78, N1 percentile 0.998 | G4 yes |
| the 11:00-centred placebo V | −0.080, t −1.75 | G5 yes (does not fire) |
| N2, the ±1-week pseudo-events | −0.039, t −0.68 | an auction-week pattern is absent |
| N4, week-clustered sign flip | percentile 0.99999, p95 +0.084 (SE 0.0003) | decisive |

**The paper's free predictions (F1–F7) all hold:**
- the pooled z is positive;
- pre-auction is negative and post-auction positive;
- the 30-year (UB) is the largest in price bp;
- the pre-2015 era is stronger than 2015–2023;
- the 11:00 placebo is not positive;
- **the V rises with the previous same-tenor auction's primary-dealer share** (slope +0.091 z per unit, t 2.06): more
  dealer inventory, more pressure, as the paper finds.

**By pair** (Δ in price bp; t; ratio to the transfer-adjusted cash expectation):

| pair | full: Δ (t), ratio | 2010–14 | 2015–23 | pre / post leg (full) |
|---|---|---|---|---|
| 2y → ZT | +1.06 (2.26), 0.90 | +1.46 (3.19) | +0.83 (1.20) | −0.21 / +0.85 |
| 3y → ZT | +0.64 (1.35), 0.53 | +1.20 (2.87) | +0.33 (0.48) | −0.58 / +0.06 |
| **5y → ZF** | **+3.96 (3.07), 0.88** | +3.43 (1.58) | **+4.23 (2.62)** | −2.41 / +1.54 |
| 7y → ZN | +0.79 (0.54), 0.24 | +3.82 (1.33) | −0.60 (−0.36) | +0.92 / +1.71 |
| 10y → ZN | +2.91 (1.22), 0.73 | +8.14 (1.74) | +0.11 (0.04) | +0.08 / +2.99 |
| **30y → UB** | **+13.85 (2.13), 0.97** | +24.22 (1.88) | +12.01 (1.62) | **−11.90 / +1.95** |

- **The recent era is carried by the 5-year (ZF) and the 30-year (UB).** The 7- and 10-year into ZN are gone after 2015,
  consistent with the paper's finding that only 3y and 10y declined significantly.
- **The 30-year's V is almost all pre-auction:** −11.9 of its 13.85 bp. The paper puts the pre share at 71%.
- **Sensitivities hold:** shared-day 13:00 auctions included, t 5.09; March 2020 included, t 5.16; ZT from 2019 only,
  t 4.21, share 0.82.

## 2. Stage 2, the trade (full-size contracts, the d556 round trip)

| book | trades (a year) | mean gross (t) | mean net (t) | daily Sharpe net (Sortino); gross | max DD | gate |
|---|---:|---|---|---|---:|---|
| **U** (every primary leg) | 1,454 (107) | **+$17.48 (2.89)**; N1 percentile 1.000 (p95 +$3.85) | −$1.18 (−0.20) | −0.05 (−0.08); +0.77 (+1.23) | $7,615 | Gate 1 (gross) **yes** |
| **F** (projected gross ≥ 2 × round trip, from the paper's magnitudes) | 294 (22) | +$69.89 (2.28) | **+$43.85 (1.45)**; N1 percentile 0.999 (p95 +$6.31) | **+0.42 (+0.65)**; +0.67 (+1.08) | $4,308 | Gate 2 (net, t ≥ 2) **no** |

**Verdict (D666's rule): MECHANISM ONLY.**
- The always-on control, the same legs on the matched control days, grosses −$11.44 a leg (2,908 legs).
- The breakeven round trip for Book U is $17.48 a leg: 3.8 ticks on UB, 2.2 on ZF, 0.3 on ZN, 0.75 on ZT.

**Book U by leg (net a trade).**

| leg | net a trade |
|---|---:|
| **30y pre** | **+$83.04** |
| 5y pre | +$18.74 |
| 10y post | +$4.08 |
| 3y pre | +$0.42 |
| 2y post | −$0.54 |
| 5y post | −$12.32 |
| 7y post | −$12.55 |
| 2y pre | −$14.33 |
| 3y post | −$17.33 |
| 10y pre | −$28.76 |
| 7y pre | −$29.31 |

The paper's sizing named the 30-year pre-leg as the only leg worth trading in the recent era (design §8.1), and the data
agree.

**The 30-year pre-auction short alone** (the dominant leg of both books; descriptive, not a declared cell):
- 126 trades, gross +$120.29 (t 1.92), **net +$83.04 (t 1.32)**, median net +$56.50.
- 2013–14 −$4.36 (19 trades); 2015–23 +$98.56 (107 trades, t 1.40).
- **The top five trades are 84% of its net.** Without them it is +$13.89 a trade.

**The four groups for Book F** (the book the filter selects):
- **Trade distribution:** 294 trades, mean net +$43.85, **median +$9.63**, hit 52.7%, payoff 1.24, skew −0.15,
  kurtosis 7.4. Trims 1%: ex-top +$25.25, ex-bottom +$66.27, both +$47.71.
- **Dependence:**
  - 9 of 14 years profitable; 2015–2023 +$98.56 a trade (107) against 2010–14 +$12.55 (187).
  - The top 1 / 5 / 10 trades are 15% / 68% / 117% of the net.
  - The price tercile runs +$28 / −$41 / +$144.
  - Without 2020 +$57.71; without 2022 +$39.55.
- **The paper-based projection's calibration** (D690): slope +0.73, but not monotone in the middle bins. AUC against
  the oracle 0.55, Spearman with gross +0.07.

**The declared secondary,** the post-leg taken only after a concession and on high dealer share: 125 trades, gross
+$7.94, N1 percentile 0.93. Nothing.

## 3. The component line (2016-01-04 → 2023-12-29, full contracts, the d556 cost)

| book | net Sharpe (SE); Sortino | gross | hit | daily skew | daily σ | trades | ρ with #2 (arm) / #4 (F2) |
|---|---|---|---:|---:|---:|---:|---|
| U | +0.04 (0.34); +0.06 | +0.77 | 41.4% | +0.65 | $176 | 877 | +0.07 / +0.01 |
| **F** | **+0.48 (0.35); +0.76** | +0.64 | 53.7% | +0.76 | $164 | 95 | **+0.08 / +0.02** |

- **Book F sits at C-a's bar,** on the point estimate, with a Sharpe SE of 0.35.
- **It is uncorrelated with both live components.** It trades a different underlying on a different clock: the kind of
  diversifier `BOOK_PROP.md` asks for.
- **But it rests on about 12 trades a year,** and its best ten trades carry more than all of its net.

## 4. What it says

1. **The mechanism is real in the futures, with no margin of doubt in-sample.** The pooled t is 4.98, the result is above
   every enumerated placebo schedule, the 11:00 and ±1-week placebos are flat, every paper prediction holds, the
   dealer-share dose shows, and 2015–2023 keeps two-thirds of the cash magnitude.
   - **This line is new to the repo:** no earlier record read the Treasury auction clock intraday.
2. **As a trade it is thin at full size.** The average leg's move is about 0.37 of twice its round trip. Only the
   30-year pre-auction short clears its cost on average, and it is carried by a few large auctions.
3. **Book F is a plausible small, diversifying component, but not an established one.** It has a net Sharpe of about
   0.48, ρ under 0.1 with everything in the ledger, about 12 trades a year, and a t of 1.45. Confirming it on unseen
   data would need years: design §8.1 put the 30-year pre-leg's expected unseen t at 0.8–1.0.
4. **All ten programme slots are allocated,** so a pre-registration for the joint run would need an amendment that
   re-allocates α. That is the principal's call.
5. **Under R12 (design §10), the next step for MECHANISM ONLY** is a screen of the personal track (long-duration
   Treasury ETFs at about 3.8 bp a round trip) before any closure on cost. It is proposed, not started.

## PARKED, 2026-09-30, on the principal's word

The principal: "Park C while we look into E."
- **Parked, not closed.** No ETF screen, no vault line and no α re-allocation are started.
- The premise finding and Book F's in-sample line stand as recorded.

## CLOSED, 2026-09-30, on the principal's word

The principal, after a hindsight breakdown of this record's own trade table (no new data read): "Close it, not on the
size problem, but on the rarity and spikiness of the strategy."

**What the breakdown showed** (net per full contract, from `d710_trades.csv.gz`):
- **The tradeable part is the pre-auction short on two tenors, and nothing else:**
  - the 30-year into UB: +$98.56 in 2015–23 (t 1.40, median +$87.75);
  - the 5-year into ZF: +$22.61 (t 2.08).
- **Everything else loses after costs:** every post-auction long leg (−$5 to −$26), and the 2y, 7y and 10y shorts
  (the 10y into ZN is −$37, t −2.14).
- **Rarity:** a ZF + UB pre-auction book trades about 18 days a year, for +$50.89 a trade (t 1.61) and about
  $940 a year per pair of contracts.
- **Spikiness:**
  - the UB leg's years swing from +$7.9k (2019) to −$3.4k (2020);
  - without its five best trades it is +$14 a trade;
  - the per-trade sd is about $500.
- **It could not be confirmed on the unseen span:** about 48 trades in 2024–26, an expected t of about 0.8 at the full
  effect.

**Closed under R15:** the Treasury auction-day construction, as a trade for either book, including the pre-auction-only
book and any filter of it.
- **The mechanism stands as evidence:** the dealers' V is in the futures (t 4.98), with the paper's predictions and the
  dealer-share dose.
- **The calendars stay as data:** `data/calendar/treasury_auctions.csv` and `fomc_2010_2015.csv`.
