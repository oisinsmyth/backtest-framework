# Reading List: Market Structure and Systematic Research

**Purpose:** build domain knowledge of *how markets actually work* — who trades, why, and
under what constraints — so that candidate alphas can be generated from mechanism rather
than mined from price.

**Organising principle:** every item here is either (a) written by someone with no
incentive to sell you a strategy, (b) primary source documentation from an exchange or
regulator, or (c) academic work that has survived replication. Nothing here has a funnel
attached.

---

## 0. The bullshit filter

Apply before reading anything not on this list.

| Test | Pass | Fail |
|---|---|---|
| **Mechanism** | Explains *who* is on the other side and what forces them to trade | Describes *what the chart does* |
| **Capacity** | States the size at which the edge degrades | Never mentions capacity |
| **Decay** | Reports when and why things stopped working | Only shows what worked |
| **Incentive** | Author trades it, or is an academic publishing failures | Author sells a course, signal service, or indicator |
| **Negative results** | Present and prominent | Absent |
| **Sample** | Multiple assets, multiple decades, out-of-sample | One asset, one regime, cherry-picked window |

The strongest single heuristic: **selling a strategy implies the strategy is worth less
than the course revenue.** Real edges are capacity-constrained, but not *that*
constrained. Treat any paid signal/indicator product as disqualified by revealed preference.

Second strongest: **primary sources have no incentive to lie to you.** Exchange rulebooks,
index methodology PDFs, CFTC documentation and regulatory filings are written by the
people who define the mechanism. They are dry, free, and the origin of most genuinely
structural edges.

---

## 1. Start here — market structure

### Larry Harris, *Trading and Exchanges: Market Microstructure for Practitioners* (2002)
**Read this first. If you read one thing on this list, read this.**

An institutional taxonomy of every category of market participant — informed traders,
dealers, block traders, hedgers, index funds, retail — what each is trying to achieve, and
which constraints force them to trade at prices they do not like. This is the "who is on
the other side" question in book form, written by a former SEC chief economist. Almost no
maths. Directly answers the problem of not being able to tell mechanism from marketing.

*Read:* the participant taxonomy chapters and the order-driven market chapters in full.
The chapters on regulation and exchange governance can be skimmed on a first pass.

### Jean-Philippe Bouchaud, Julius Bonart, Jonathan Donier, Martin Gould, *Trades, Quotes and Prices* (2018)
The rigorous empirical treatment of order books, price impact, and order flow. Written by
people running a real fund (CFM). Heavier going than Harris — this is the reference you
return to rather than read cover to cover. The square-root impact law material is the part
that changes how you think about cost and capacity.

### Joel Hasbrouck, *Empirical Market Microstructure* (2007)
The econometrics of microstructure. Read after Harris, when you want to actually estimate
the things Harris describes qualitatively.

### Foundational papers (short, worth reading properly)
- **Kyle (1985), "Continuous Auctions and Insider Trading"** — the canonical model of how
  informed trading moves prices, and why market makers widen spreads.
- **Glosten & Milgrom (1985)** — adverse selection as the origin of the bid-ask spread.
  Together with Kyle, this is why execution cost exists and why it is not a fixed fee.

These two underpin everything in the cost model. Understanding them properly is the
difference between modelling slippage and guessing at it.

---

## 2. Futures-specific

### Robert Carver, *Advanced Futures Trading Strategies* (2023)
**The highest-value single item on this list for a futures-only programme.** Carver works
through 30+ systematic futures strategies with explicit rules, position sizing, cost
treatment and honest performance attribution. Same author as *Systematic Trading*, which
is already on the shelf. He is unusually direct about which strategies do not add much and
why, which is exactly the signal that a source is honest. Effectively a pre-built baseline
library for §10.3 of `FEATURE_RESEARCH.md`.

### Core futures papers
- **Moskowitz, Ooi & Pedersen (2012), "Time Series Momentum"** — the foundational TSMOM
  result across 58 instruments and decades. Replicate this first.
- **Koijen, Moskowitz, Pedersen & Vrugt (2018), "Carry"** — carry as a unified concept
  across asset classes, not just FX. The theoretical basis for roll yield as a feature.
- **Asness, Moskowitz & Pedersen (2013), "Value and Momentum Everywhere"** — the same two
  effects appearing in eight markets simultaneously. The multi-asset, multi-decade
  evidence standard to judge other claims against.
- **Erb & Harvey (2006), "The Strategic and Tactical Value of Commodity Futures"** — where
  commodity returns actually come from, and the decomposition into spot, roll and collateral.
- **Gorton & Rouwenhorst (2006), "Facts and Fantasies about Commodity Futures"** — the title
  is the reason it is on this list.
- **Bessembinder (1992), on hedging pressure** — producers are structurally short and pay
  to be. The mechanism behind commodity risk premia.
- **Szymanowska et al. (2014), "An Anatomy of Commodity Futures Risk Premia"** — the
  systematic decomposition; useful for feature generation.

### Primary sources (free, and where the structural edges actually live)
- **CME rulebook and product specifications** — contract specs, settlement procedures,
  expiry mechanics, price limits. Tedious and essential.
- **Exchange roll and expiry calendars** — needed for the roll schedule in the research
  protocol, and a source of forced-flow features in their own right.
- **CFTC Commitments of Traders** — documentation *and* release calendar. Free weekly
  positioning data. Read the documentation before using the data; the reference-date vs
  release-date gap is a classic lookahead trap.
- **S&P GSCI and Bloomberg Commodity Index methodology documents** — the roll windows are
  published in advance, and the flow is large and price-insensitive. This is what a
  structural edge looks like when it is documented rather than sold.

---

## 3. Cross-sectional equity research

### Richard Grinold & Ronald Kahn, *Active Portfolio Management* (2nd ed.)
The theoretical spine of the whole approach: information coefficient, breadth, the
Fundamental Law, forecasting as scaled and shrunk raw signals, and the separation of alpha
from risk from portfolio construction. Dense and worth the effort. Chapters on forecasting
and the Fundamental Law are the core; the empirical chapters have dated.

### Qian, Hua & Sorensen, *Quantitative Equity Portfolio Management* (2007)
The practitioner complement to Grinold & Kahn. Explicit on factor construction, IC
analysis, neutralisation and the mechanics of turning forecasts into portfolios. Closest
published thing to the workflow in `FEATURE_RESEARCH.md`.

### Core cross-sectional papers
- **Jegadeesh & Titman (1993)** — cross-sectional momentum, the original.
- **Fama & French (1993, 2015)** — the factor framework everything is residualised against.
- **Bernard & Thomas (1989)** — post-earnings announcement drift; the cleanest example of
  slow information diffusion.
- **Gatev, Goetzmann & Rouwenhorst (2006)** — pairs trading, the distance approach. Read
  as the baseline your cointegration/Kalman work improves on.
- **Novy-Marx (2013), "The Other Side of Value"** — gross profitability; a good example of
  a feature justified by mechanism rather than data mining.

---

## 4. Methodology, overfitting, and the replication crisis

This section is the intellectual core of the portfolio narrative. It is also the best
available inoculation against internet nonsense.

- **Marcos López de Prado, *Advances in Financial Machine Learning* (2018)** — already on
  the list. Read chapters on labelling (triple barrier), sample uniqueness, purged
  cross-validation and backtest overfitting first. The rest is more variable in quality.
- **Bailey & López de Prado (2014), "The Deflated Sharpe Ratio"** — how to discount a
  Sharpe for the number of trials that produced it. Implement it; do not just cite it.
- **Harvey, Liu & Zhu (2016), "…and the Cross-Section of Expected Returns"** — 300+
  published factors, and the argument that a t-stat of 2 is nowhere near sufficient.
  The reason the admission threshold in the protocol is 3.0.
- **Harvey & Liu (2015), "Backtesting"** — practical multiple-testing adjustment for
  strategy evaluation.
- **Arnott, Harvey & Markowitz (2019), "A Backtesting Protocol in the Era of Machine
  Learning"** — short, checklist-shaped, directly applicable.
- **McLean & Pontiff (2016), "Does Academic Research Destroy Stock Return Predictability?"**
  — published anomalies decay by roughly a third to a half post-publication. Essential
  calibration for how long any edge lasts.
- **Bailey, Borwein, López de Prado & Zhu (2014), "Pseudo-Mathematics and Financial
  Charlatanism"** — the mathematics of why backtest overfitting is nearly inevitable
  without explicit accounting. Also the most useful thing to read when evaluating someone
  else's claimed track record.

---

## 5. Execution and cost

- **Almgren & Chriss (2000), "Optimal Execution of Portfolio Transactions"** — the
  foundational impact-vs-timing-risk trade-off.
- **Kissell, *The Science of Algorithmic Trading and Portfolio Management*** — practitioner
  reference on implementation shortfall and cost modelling.
- **Frazzini, Israel & Moskowitz (2018), "Trading Costs"** — real costs from a large fund's
  actual execution data, which is far more credible than modelled estimates.
- **Bouchaud et al. on the square-root impact law** — impact scales roughly with the square
  root of participation. This is the single most important fact for capacity estimation.

---

## 6. Practitioner sources without a funnel

- **AQR research library** — published papers, including ones documenting their own
  strategies' weak periods.
- **CFM (Capital Fund Management) research** — Bouchaud's group; microstructure and impact.
- **Kaiko research** — crypto market structure, if that remains relevant.
- **Robert Carver's blog** — honest, detailed, futures-focused. He does sell books, which is
  a different thing from selling signals.
- **Exchange and clearing house publications** — margin methodology, settlement mechanics.

**Treat with caution:** aggregator blogs and forums. Not worthless, but the signal-to-noise
ratio requires the §0 filter on every individual post.

---

## 7. Suggested order

**Phase 1 — mechanism (the current gap)**
1. Harris, *Trading and Exchanges* — participant and order-driven market chapters
2. Carver, *Advanced Futures Trading Strategies*
3. CME product specs + CFTC COT documentation for the traded universe
4. Moskowitz/Ooi/Pedersen TSMOM, Koijen et al. Carry

**Phase 2 — method**
5. Grinold & Kahn — Fundamental Law and forecasting chapters
6. Harvey, Liu & Zhu; Bailey & López de Prado Deflated Sharpe
7. López de Prado — labelling and cross-validation chapters
8. McLean & Pontiff

**Phase 3 — depth**
9. Bouchaud et al., *Trades, Quotes and Prices*
10. Kyle; Glosten & Milgrom
11. Almgren & Chriss; Frazzini/Israel/Moskowitz
12. Qian/Hua/Sorensen

Interleave with implementation. Each Phase 1 item should produce at least one
pre-registered feature; each Phase 2 item should produce a change to the evaluation harness.
Reading that does not change the repo is entertainment.
