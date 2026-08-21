# The combined long+short book on 62 coins

**Produced:** 2026-08-21 ·
**Snapshot:** `75e1bbbfb10d70b64cb87a9ada00937e4bc00817340e9e671fc554237b847b5f` ·
**Reproduce:** `uv run python scripts/run_combined_universe.py` (offline, deterministic)

## What this is

D172 combined the two books on BTC/ETH and found the combination has a **lower Sharpe than
the long book alone** but a **smaller drawdown**. That is a two-instrument finding, and
D180 has just shown what those are worth here: E1 cleared its bar five times on BTC/ETH and
failed on sixty-two coins.

This measures the combined book across the whole D140 cross-section with **no rule
attached** — the baseline that has to exist before any rule-level combined result can be
read. Both baselines already exist and are already in their pools, so **no multiplicity is
added**; the long arm reuses `breakout_universe.baseline_variant()` directly.

**Per-symbol, not portfolio.** Each coin's own long and short series are combined into one
book. There is no cross-sectional capital allocation here and the two legs remain separate
backtests blended after the fact.

**Weights are expanding-window inverse-vol** — every return from the start of the
out-of-sample period up to the previous bar (D181/D44). The first 252 bars of
every symbol are warm-up and are excluded from every figure below, legs included, so all
three arms are quoted over the same span. A fixed window was tried first and abandoned:
the short book is flat on ~85% of bars, so a 63-bar window was entirely flat 75% of the
time and fell back to equal weight.

Reference tier `taker_40bp`; the short leg pays borrow at
10%/yr.

## Does combining beat the long book alone?

A win in the Sharpe columns means the combination scored higher. A win in the drawdown
columns means it drew down **less**. D172's BTC/ETH finding was that these two disagree.

| Cohort | Symbols | Sharpe win rate | Mean Δ Sharpe | Median Δ | DD win rate | Mean Δ max DD | Median Δ |
|---|---|---|---|---|---|---|---|
| ALL | 62 | 8% | -0.382 | -0.422 | 68% | -4.7 pp | -6.0 pp |
| collapsed | 41 | 12% | -0.302 | -0.335 | 59% | -3.7 pp | -2.4 pp |
| delisted | 2 | 0% | -0.992 | -0.992 | 50% | +17.2 pp | +17.2 pp |
| survived | 19 | 0% | -0.492 | -0.547 | 89% | -9.3 pp | -8.1 pp |

**D172's finding holds on the cross-section.** The combination scores a LOWER Sharpe than the long book alone on 92% of coins (mean Δ -0.382) while drawing down LESS on 68% (mean Δ -4.7 pp). You cannot diversify with a negative-expectancy asset; you can only spread the same losses more smoothly. The drawdown gain is real and it is bought with return.

## Is any arm worth running?

The win rates above are RELATIVE — they say whether combining helps, not whether the result
is worth having. This says the second thing, over the same post-warm-up span.

| Arm | Median total return | Mean, ex blow-ups | Mean Sharpe | Mean max DD | Profitable symbols |
|---|---|---|---|---|---|
| `long` | +123.2% | +257.3% | +0.392 | 48.1% | 51 / 62 |
| `short` | -59.4% | -47.7% | -0.478 | 67.7% | 5 / 62 |
| `combined` | +5.7% | +23.7% | +0.010 | 43.4% | 34 / 62 |

**The median is the headline and the mean is not** — a cross-section of alts has a return
distribution with a tail that eats any average. 2 symbol(s) lost more than the entire account in some arm (`LUNA1-USD`, `LUNC-USD`), so the mean column excludes them.

## The diversification claim, as a distribution

`BREAKDOWN_SHORT_STRATEGY.md` sets a ~0.2 correlation target and D172 reported the two
books clearing it on BTC and ETH. Across 62 coins it is a distribution, not a number:

| p05 | p25 | median | p75 | p95 | mean | within ±0.2 |
|---|---|---|---|---|---|---|
| -0.001 | -0.000 | +0.000 | +0.001 | +0.002 | +0.000 | 62/62 |

Low correlation is the precondition for the diversification argument, not the argument
itself — two books can be uncorrelated and still combine into something worse than the
better one, which is what the Sharpe column above measures.

## How the risk budget actually splits

Average share of the combined book carried by the LONG leg: median **0.456**, range 0.188-0.778. The long leg holds a MINORITY of the risk budget on **47 of 62** symbols.

That is a known flaw in the equal-vol construction, not a property of these coins (D181). Inverse-vol weighting reads a flat book as low-risk, when what it actually is, is absent — and the short book is regime-gated, so the less it trades the more of the risk budget it is handed. Every combined figure in this document inherits that, and it is reported here rather than left to be discovered.

**Degenerate weighting:** 1,022 of 133,120 scored bars (0.8%)
fell back to 50/50 because one leg was flat for its entire history to that point.

## Sample symbols — the 5 best and 5 worst

Ranked by Δ Sharpe against the long book alone, shown in total return so the size is
legible.

| Symbol | Status | Long return | Combined return | Δ Sharpe | Δ max DD |
|---|---|---|---|---|---|
| `USTC-USD` | collapsed | -59.7% | -16.7% | +1.154 | +4.3 pp |
| `SRM-USD` | collapsed | -70.2% | -64.1% | +0.297 | -0.7 pp |
| `AVAX-USD` | collapsed | +74.1% | +100.1% | +0.282 | -6.5 pp |
| `AXS-USD` | collapsed | -26.0% | -6.5% | +0.163 | -8.9 pp |
| `SAND-USD` | collapsed | +28.9% | +43.6% | +0.117 | +1.3 pp |
| … | | | | | |
| `ETC-USD` | collapsed | +186.5% | -21.1% | -0.738 | +8.9 pp |
| `FIL-USD` | collapsed | +265.3% | -14.4% | -0.753 | +8.2 pp |
| `BTC-USD` | survived | +4,672.4% | +197.3% | -0.761 | -8.1 pp |
| `LTC-USD` | survived | +419.7% | -40.6% | -0.852 | -5.9 pp |
| `LUNA1-USD` | delisted | +1,297.6% | -5.1% | -1.659 | +53.3 pp |

**Every admitted symbol was combined.** None had too little out-of-sample history to weight on the trailing window.

<details><summary>Every symbol</summary>

| Symbol | Status | Long Sharpe | Short Sharpe | Combined | Δ vs long | Long DD | Combined DD | Corr |
|---|---|---|---|---|---|---|---|---|
| `USTC-USD` | collapsed | -1.27 | +0.49 | -0.11 | **+1.154** | 62% | 67% | +0.00 |
| `SRM-USD` | collapsed | -1.36 | -0.44 | -1.06 | **+0.297** | 71% | 70% | -0.00 |
| `AVAX-USD` | collapsed | +0.50 | +0.50 | +0.78 | **+0.282** | 28% | 22% | -0.00 |
| `AXS-USD` | collapsed | -0.40 | -0.06 | -0.24 | **+0.163** | 37% | 29% | -0.00 |
| `SAND-USD` | collapsed | +0.22 | +0.20 | +0.34 | **+0.117** | 39% | 40% | -0.00 |
| `REP-USD` | collapsed | -0.12 | -0.16 | -0.16 | **-0.036** | 52% | 53% | -0.00 |
| `WAVES-USD` | collapsed | +0.34 | +0.04 | +0.30 | **-0.042** | 56% | 40% | -0.00 |
| `XEM-USD` | collapsed | +0.34 | +0.07 | +0.28 | **-0.058** | 46% | 33% | -0.00 |
| `KSM-USD` | collapsed | +0.07 | -0.12 | -0.02 | **-0.089** | 38% | 24% | +0.00 |
| `CRO-USD` | survived | +1.15 | +0.08 | +1.04 | **-0.109** | 45% | 30% | -0.00 |
| `HT-USD` | collapsed | +0.51 | -0.15 | +0.38 | **-0.130** | 64% | 34% | -0.00 |
| `OMG-USD` | collapsed | +0.47 | -0.25 | +0.24 | **-0.234** | 50% | 40% | +0.00 |
| `ONT-USD` | collapsed | -0.31 | -0.54 | -0.55 | **-0.240** | 61% | 51% | -0.00 |
| `ICX-USD` | collapsed | +0.71 | -0.48 | +0.45 | **-0.257** | 39% | 22% | +0.00 |
| `SOL-USD` | survived | +0.27 | -0.27 | +0.00 | **-0.268** | 41% | 36% | +0.00 |
| `BSV-USD` | collapsed | -0.84 | -0.84 | -1.12 | **-0.281** | 80% | 75% | -0.00 |
| `XLM-USD` | survived | +0.40 | -0.33 | +0.10 | **-0.293** | 52% | 37% | +0.00 |
| `YFI-USD` | collapsed | +0.04 | -0.56 | -0.26 | **-0.297** | 50% | 48% | +0.00 |
| `TRX-USD` | survived | +0.34 | -0.79 | +0.04 | **-0.299** | 47% | 28% | +0.00 |
| `EGLD-USD` | collapsed | +0.04 | -0.46 | -0.26 | **-0.299** | 25% | 22% | +0.00 |
| `ETH-USD` | survived | +0.87 | -0.23 | +0.57 | **-0.299** | 35% | 28% | +0.00 |
| `SNT-USD` | collapsed | +0.19 | -0.67 | -0.11 | **-0.306** | 50% | 46% | +0.00 |
| `QTUM-USD` | collapsed | +0.31 | -0.57 | -0.00 | **-0.314** | 48% | 39% | +0.00 |
| `MATIC-USD` | delisted | +0.75 | -0.05 | +0.43 | **-0.325** | 41% | 22% | -0.00 |
| `ATOM-USD` | collapsed | +0.45 | -0.22 | +0.13 | **-0.327** | 31% | 38% | +0.00 |
| `SUSHI-USD` | collapsed | +0.51 | -0.31 | +0.18 | **-0.330** | 27% | 33% | +0.00 |
| `FTT-USD` | collapsed | +0.62 | -0.22 | +0.28 | **-0.335** | 62% | 42% | +0.00 |
| `THETA-USD` | collapsed | +0.81 | -0.62 | +0.46 | **-0.342** | 59% | 41% | +0.00 |
| `HBAR-USD` | survived | +1.16 | -0.06 | +0.79 | **-0.372** | 35% | 16% | -0.00 |
| `SC-USD` | collapsed | +0.54 | -0.50 | +0.14 | **-0.401** | 49% | 35% | +0.00 |
| `OKB-USD` | survived | +0.57 | -0.47 | +0.16 | **-0.415** | 48% | 34% | +0.00 |
| `BCH-USD` | survived | +0.34 | -0.68 | -0.08 | **-0.428** | 52% | 32% | +0.00 |
| `DOT-USD` | collapsed | +0.08 | -0.62 | -0.38 | **-0.457** | 36% | 38% | +0.00 |
| `DASH-USD` | collapsed | +0.30 | -0.89 | -0.17 | **-0.463** | 54% | 57% | +0.00 |
| `STEEM-USD` | collapsed | -0.01 | -0.92 | -0.48 | **-0.465** | 61% | 63% | +0.00 |
| `ZRX-USD` | collapsed | +0.50 | -0.72 | +0.04 | **-0.466** | 50% | 44% | +0.00 |
| `NEO-USD` | collapsed | +0.43 | -0.70 | -0.04 | **-0.470** | 40% | 40% | +0.00 |
| `VET-USD` | collapsed | +0.82 | -0.51 | +0.33 | **-0.483** | 37% | 35% | +0.00 |
| `MANA-USD` | collapsed | +0.66 | -0.52 | +0.17 | **-0.492** | 46% | 47% | +0.00 |
| `SNX-USD` | collapsed | +0.67 | -0.37 | +0.17 | **-0.498** | 42% | 31% | +0.00 |
| `CRV-USD` | collapsed | -0.03 | -0.83 | -0.54 | **-0.506** | 49% | 39% | -0.00 |
| `BNB-USD` | survived | +0.74 | -0.70 | +0.22 | **-0.520** | 46% | 43% | +0.00 |
| `LSK-USD` | collapsed | +0.23 | -0.78 | -0.31 | **-0.539** | 47% | 60% | +0.00 |
| `EOS-USD` | collapsed | +0.01 | -1.00 | -0.53 | **-0.541** | 44% | 58% | +0.00 |
| `XMR-USD` | survived | +0.46 | -0.87 | -0.09 | **-0.547** | 34% | 47% | +0.00 |
| `ZEC-USD` | survived | +0.81 | -0.76 | +0.25 | **-0.558** | 54% | 46% | +0.00 |
| `BAT-USD` | survived | +0.19 | -0.73 | -0.37 | **-0.558** | 56% | 49% | +0.00 |
| `MKR-USD` | survived | +0.12 | -0.82 | -0.44 | **-0.562** | 51% | 47% | +0.00 |
| `ADA-USD` | survived | +0.89 | -0.78 | +0.30 | **-0.583** | 46% | 36% | +0.00 |
| `NEAR-USD` | collapsed | +0.58 | -0.56 | -0.01 | **-0.587** | 49% | 53% | +0.00 |
| `XTZ-USD` | collapsed | +0.41 | -0.95 | -0.19 | **-0.600** | 48% | 47% | +0.00 |
| `DOGE-USD` | survived | +0.57 | -0.77 | -0.05 | **-0.618** | 66% | 51% | +0.00 |
| `XRP-USD` | survived | +0.37 | -0.92 | -0.27 | **-0.639** | 65% | 66% | +0.00 |
| `BTG-USD` | collapsed | +0.43 | -0.68 | -0.22 | **-0.644** | 54% | 56% | +0.00 |
| `LUNC-USD` | collapsed | +0.98 | +0.10 | +0.33 | **-0.648** | 52% | 70% | -0.00 |
| `LINK-USD` | survived | +0.31 | -0.68 | -0.36 | **-0.661** | 65% | 47% | +0.00 |
| `ALGO-USD` | collapsed | +0.63 | -0.77 | -0.09 | **-0.724** | 48% | 32% | +0.00 |
| `ETC-USD` | collapsed | +0.51 | -1.14 | -0.23 | **-0.738** | 43% | 52% | +0.00 |
| `FIL-USD` | collapsed | +0.56 | -0.59 | -0.19 | **-0.753** | 38% | 46% | +0.00 |
| `BTC-USD` | survived | +1.22 | -0.63 | +0.46 | **-0.761** | 43% | 35% | +0.00 |
| `LTC-USD` | survived | +0.50 | -0.89 | -0.35 | **-0.852** | 79% | 73% | +0.00 |
| `LUNA1-USD` | delisted | +2.18 | +0.03 | +0.52 | **-1.659** | 21% | 74% | -0.00 |

</details>

## Standing caveats

1. **This is not a portfolio result.** Per-symbol combination answers "does pairing this
   coin's two books help?", not "does a long/short book across 62 coins work?". The second
   needs cross-sectional capital allocation that does not exist in this framework yet.
2. **Neither leg has a demonstrated edge.** The long book's DSR sits near 1.0 only because
   its plateau is flat; the short book's is 0.04-0.538. Combining two books does not create
   an edge that neither has.
3. **No margin call, no liquidation, no borrow recall (D175).** Short accounts in this
   universe have passed -100% and kept trading.
4. **The cross-section is not independent.** These coins move together, so 62 symbols is
   far fewer than 62 independent tests.
5. **Borrow at a flat 10%/yr is generous** for small-cap alts,
   and the optimism is largest exactly where the short leg looks most attractive.
