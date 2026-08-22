# D188 — The out-of-sample test: the portfolio on 57 ETFs

**Status:** Committed (H1 and H2 confirmed, H3 falsified — the diversification lift has the sign of the expectancy)
**Date:** 2026-08-22
**Category:** Validation & research integrity
**Source:** D183's third and last debt, and the only one that asks whether any of this is real

> Written and committed **before** the study runs, as D173, D178, D180, D182, D183, D185
> and D186 were. A result section will be appended and nothing above it edited.

## The question

D183 found the cross-sectional long portfolio at **+1.277** Sharpe against **+1.196** for a
daily-rebalanced equal-weight basket. D185 charged the rebalancing cost, D186/D187 charged
market impact, and the edge survived both at **+0.075**, with capacity around $66M.

**Every one of those numbers is one crypto cross-section over one bull-dominated decade.**

D180 is the standing lesson. E1 cleared its bar five times on BTC and ETH and then failed on
62 coins, because those two sat at the 97th and 85th percentile of the variable that decided
the outcome. Five correlated passes on a favourable sample looked exactly like evidence.

The 62-coin universe was itself the out-of-sample test **for a rule found on two coins**. It
has never been the out-of-sample test for the portfolio result, because the portfolio result
was found *on it*.

## What is run

The **same** long baseline, unchanged: 40-bar entry channel, 10-bar exit,
`breakout_universe.baseline_variant()` — the identical object the crypto universe study
runs. No refitting, no re-selection, no per-asset-class tuning.

**Four things had to change, and each is a fact about the instruments rather than a choice:**

- **`periods_per_year = 252`.** Equities do not trade weekends.
- **Volume is SHARES, declared explicitly** (D187). Getting this wrong scales impact by
  √price, which is the mistake that record exists to record.
- **Dividends are paid** — 2,285 across 53 of 57 symbols, plus 14 splits, through
  `DividendFlow` on **both** arms. This is not optional: on `SPY` alone, including them
  moves the strategy from +0.060 to +0.171 Sharpe. And omitting them would flatter the
  strategy specifically, because it is flat about half the time and collects fewer than the
  benchmark does.
- **Two crypto-specific screens are disabled.** The peg screen has no equity referent — it
  exists to exclude stablecoins, and applied verbatim it would drop 12 of 57 ETFs including
  `AGG`, `HYG` and `DIA` for being genuinely low-volatility. Dropping it **admits** the
  instruments a breakout book should find hardest, so it is the conservative direction. The
  liquidity floor compares raw volume against a USD threshold and ETF volume is in shares;
  it is also non-binding, measured rather than assumed — the thinnest name, `VYM`, trades
  $99.7M a day. `min_bars` is untouched and all 57 clear it.

**Two cost tiers, both fixed in advance:** `equity_1bp` (IBKR commission + 1 bp spread),
which is what these instruments actually cost, and `crypto_40bp`, the crypto study's own
assumption applied here as a stated handicap so the obvious question is answered rather than
left open.

**Market impact is OFF.** This asks whether the effect exists out of sample, not what it
costs at size — D186/D187 answered that for crypto. Turning it on would vary two things.

## The predictions

**H1 — the edge over the equal-weight basket is NEGATIVE at equity costs.** Predicted
**TRUE**, moderate confidence.

The crypto edge came substantially from **not being in the market when things collapsed**:
41 of 62 coins fell 90%+ and never recovered, and a book that stands aside avoids much of
that. ETFs do not do this. Over 2015–2024 these 57 mostly went up, and a strategy flat
roughly half the time gives away the compounding without avoiding a catastrophe that never
comes. `SPY` alone bears this out: the breakout book returns +54% including dividends over a
decade in which holding `SPY` returned several times that.

Against it: the benchmark here is the equal-weight **basket**, not `SPY`, and that basket
contains bond and low-volatility funds whose Sharpes are modest. The comparison may be
closer than the `SPY` figure suggests.

**H2 — drawdown still improves.** Predicted **TRUE**, high confidence.

Being flat half the time reduces drawdown mechanically, and this is the one property that
has survived every test in this project. If it fails here, the drawdown finding was a
crypto artifact too.

**H3 — the diversification lift reproduces**: the portfolio Sharpe is far above the median
single-ETF Sharpe. Predicted **TRUE**, high confidence.

This is arithmetic, not a market claim — averaging partially-independent books reduces
variance whatever they hold. D183's *actual* finding was the lift, and it should transfer to
any cross-section. If it does not, something is wrong with the aggregation rather than with
the strategy.

**What would falsify each:** H1, a positive edge. H2, drawdown at or above the basket's.
H3, a portfolio Sharpe not meaningfully above the median single name.

**Track record:** mechanism-first predictions falsified six times, confirmed five. H1
predicts a failure, and predictions of failure have been the more reliable half.

## What this cannot establish

**These 57 ETFs all survived.** Identical 2,515-bar spans, no staggered listings, no
failures. The crypto universe was deliberately built to contain the assets that died; this
one is survivorship-clean by construction — the opposite property. **A good result here
would be the easier kind**, and should be discounted accordingly.

**57 correlated index funds are not 57 independent tests**, any more than 62 coins were.

**And a different asset class is not a different era.** Both samples are 2015–2024. Nothing
here tests the strategy against a period unlike the one it was built in, and that remains
the deepest untested assumption in the project.

---

# RESULT — appended 2026-08-22, after the run. Nothing above this line was edited.

**Status: H1 CONFIRMED emphatically. H2 CONFIRMED. H3 FALSIFIED — and H3's failure is the
finding.**

57 ETFs, 2,204 dates, 2016-01-05 to 2024-10-07.

| | Sharpe | Total return | Max DD |
|---|---|---|---|
| **Strategy** (equity costs) | **−0.273** | **+21.6%** | **6.1%** |
| Equal-weight basket | +0.395 | +100.5% | 33.4% |
| SPY buy & hold | +0.617 | +187.0% | 33.7% |
| *Strategy at the crypto 40 bp tier* | *−0.819* | *−0.5%* | *10.6%* |

**Edge over the basket: −0.667.** At the crypto cost tier, −1.190.

## H1 — CONFIRMED, and not narrowly

The crypto portfolio's **+0.075** edge becomes **−0.667** on an asset class the strategy was
never developed on. The book returns **+21.6%** over nine years while simply holding `SPY`
returned **+187%**.

The mechanism predicted holds: the crypto edge came substantially from **standing aside
while things collapsed** — 41 of 62 coins fell 90%+ and never recovered. ETFs do not do
that. A book flat most of the time gives away the compounding without avoiding a catastrophe
that never comes.

Turnover tells the same story from another angle: **0.4× a year**. The breakout condition
barely fires on an index fund. The strategy is not losing money by trading badly; it is
losing by not being invested.

## H2 — CONFIRMED, and it is the only thing that survives

**Max drawdown 6.1% against the basket's 33.4%** — a fifth. The drawdown property has now
survived every test in this project, including this one, and it is the only claim here that
has.

It should be read for what it is. A book invested a fraction of the time has a small
drawdown for the same reason it has a small return. At 40 bp the strategy returns **−0.5%**
with a 10.6% drawdown: nearly cash, and cash also has a small drawdown.

## H3 — FALSIFIED, and this is the part worth keeping

I predicted the diversification lift would reproduce, and called it *"arithmetic, not a
market claim — averaging partially-independent books reduces variance whatever they hold."*

| | Median single ETF | Portfolio | **Lift** |
|---|---|---|---|
| Sharpe | −0.177 | −0.273 | **−0.096** |

**The portfolio is WORSE than the median single ETF.** The lift did not merely fail to
appear; it reversed.

**And the arithmetic is exactly why.** Sharpe is `mean ÷ σ`. Averaging partially-independent
books does reduce σ — that part was right. But it divides a *mean* by that smaller σ, so:

- when the mean is **positive**, shrinking σ raises the Sharpe — the crypto case, +0.44 →
  +1.28
- when the mean is **negative**, shrinking σ makes the Sharpe **more negative** — this case,
  −0.177 → −0.273

**Diversification is a magnifier, and it has the sign of the expectancy.** It does not
create edge; it concentrates whatever sign is already there. D183 called the lift "the least
surprising result in the project, because it is arithmetic" and treated it as guaranteed. It
is arithmetic, and it is not guaranteed — it is conditional on a positive mean, which is the
entire question.

That correction applies backwards to D183's framing without changing its numbers: the crypto
lift was real, and it was real *because the crypto books had positive expectancy*, not
because averaging is free.

## What this settles

**The strategy does not transfer.** The one working idea in this project is a property of a
crypto cross-section in 2015–2025, not of breakout trading. Every number downstream of
D183 — the +0.075 edge, the 972 bp rebalancing break-even, the $66M capacity — describes
that sample and nothing wider.

**This was the easier test and it still failed.** These 57 ETFs all survived: identical
spans, no delistings, no collapses. The crypto universe was built to contain the assets that
died. A survivorship-clean sample is the *friendlier* one, and the strategy lost on it by
0.667 Sharpe.

**The project's tally is now complete and consistent.** Four entry filters, six stops, E1,
the swing stop, the within-coin ensemble, the short book — every rule-level idea failed out
of sample. The portfolio was the one thing that worked, and it worked on one asset class in
one decade.

## What it does not settle

**A different asset class is not a different era.** Both samples are 2015–2024. Nothing here
tests the strategy against a period unlike the one it was built in, and that remains the
deepest untested assumption in the project — deeper than this one, because it cannot be
fixed with data already on disk.

**And a breakout rule on index funds may simply be the wrong instrument for the idea.** A
40-bar channel breakout is a trend-following device, and 57 correlated index funds in a
decade-long bull market give it little to catch that buy-and-hold does not catch first. This
is evidence that the crypto result does not generalise. It is weaker evidence about breakout
trading in general, and it should not be quoted as the latter.
