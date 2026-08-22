# The cross-sectional portfolio on 57 ETFs

**Produced:** 2026-08-22 ·
**Snapshot:** `b1e9424d04ca988264a3421ad337c6dd8e69d96c2e4aa985402821a9110eb1ad` ·
**Reproduce:** `uv run python scripts/run_etf_universe.py` (offline, deterministic)

## What this is

The same long breakout baseline — 40-bar entry, 10-bar exit,
`breakout_universe.baseline_variant()` itself — run unchanged on a different asset class.
D183's portfolio result and everything built on it (D185's rebalancing cost, D186/D187's
capacity) are **one crypto cross-section over one bull-dominated decade**. D180 is the
standing lesson on what that is worth.

57 ETFs, 2,204 dates, 2016-01-05 to 2024-10-07.
`periods_per_year = 252`. The first 252 bars are
weighting warm-up and are excluded from every figure, all arms alike.

**Dividends are paid.** 2,285 of them across 53 symbols, plus 14 splits, applied through
`DividendFlow` on both the strategy and the benchmark. A price-only run would have handed
the strategy a free ~2%/yr, because it is flat about half the time and collects fewer.

## The result

| Cost tier | Strategy Sharpe | Return | Max DD | Basket Sharpe | Return | Max DD | Edge |
|---|---|---|---|---|---|---|---|
| `equity_1bp` | -0.273 | +21.6% | 6.1% | +0.395 | +100.5% | 33.4% | **-0.667** |
| `crypto_40bp` | -0.819 | -0.5% | 10.6% | +0.371 | +94.6% | 33.5% | **-1.190** |

**SPY buy & hold** over the same span: Sharpe +0.617, return
+187.0%, max drawdown 33.7%.

**The effect does not transfer.** At realistic equity costs the portfolio scores -0.273 against the equal-weight basket's +0.395 — an edge of **-0.667**. The crypto portfolio's +0.075 does not reproduce on an asset class the strategy was not developed on, which is what an out-of-sample test is for. **Drawdown still improves**, 33.4% → 6.1% (-27.4 pp) — the one property that has survived every test in this project, and it survives this one too.

Against **SPY buy & hold** (+0.617 Sharpe, +187%, 33.7% drawdown) the portfolio returns +22%. A single-asset benchmark is not the like-for-like one — the strategy is a 57-name basket — but it is the one a reader will ask about.

At the crypto study's own 40 bp the edge is **-1.190**, against -0.819 for the strategy and +0.371 for the basket. That tier is a stated handicap, not a real cost for these instruments.

## Does the diversification lift reproduce?

D183's actual finding was not that the breakout rule works on any one instrument. It was
that **holding many of them at once** lifts the book far above the median single one —
+0.44 → +1.28 on crypto. That is arithmetic, so it should reproduce anywhere the errors are
less than perfectly correlated.

| | Median single ETF | Mean single ETF | Portfolio | Lift |
|---|---|---|---|---|
| Sharpe | -0.177 | -0.259 | **-0.273** | **-0.096** |

Best single names: `XLK` +0.47, `ITB` +0.36, `QQQ` +0.31, `SMH` +0.29. Worst: `AGG` -1.09, `HYG` -1.12, `TIP` -1.34, `SHY` -3.38.

The lift is the part of the crypto result that was never in doubt — averaging
partially-independent books reduces variance whatever they hold. Whether the strategy beats
a passive basket is the separate question the table above answers.

## Standing caveats

1. **These 57 ETFs all survived.** Identical 2,515-bar spans, no staggered listings, no
   failures. The crypto universe was built to contain the assets that DIED; this one is
   survivorship-clean by construction. That is the opposite property, and it means a good
   result here would be the easier kind.
2. **Two crypto-specific screens are disabled** — the peg screen, which has no equity
   referent, and the liquidity floor, whose units do not apply (D187). Both are stated in
   `ETF_POLICY` with the measurement behind them. `min_bars` is untouched.
3. **It is a return-aggregation portfolio, not a portfolio backtest** — no shared capital
   constraint and no cost for rebalancing between symbols beyond the flat charge above
   (D183's caveat, unchanged).
4. **Market impact is OFF here.** This asks whether the effect exists out of sample, not
   what it costs at size; D186/D187 answered that for crypto. Turning it on would vary two
   things at once.
5. **57 correlated index funds are not 57 independent tests**, any more than 62 coins were.
