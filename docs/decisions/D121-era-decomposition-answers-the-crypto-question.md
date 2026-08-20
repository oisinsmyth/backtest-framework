# D121 — Every crypto backtest reports its era decomposition: annual breakdown + start-date sensitivity

**Status:** Committed
**Date:** 2026-08-18
**Category:** Validation & research integrity
**Source:** Breakout study review session

## Decision

The breakout report carries a mandatory section, *"Is this the strategy, or is it the
era?"*, built from two tables:

- **`annual_breakdown`** — per calendar year, the strategy's compounded return, the
  benchmark's, trades opened, and time in market.
- **`start_date_sensitivity`** — the identical configuration re-run on fixtures truncated
  to begin in 2015, 2018, 2020, 2021 and 2022, reporting return, CAGR, Sharpe and max
  drawdown for both strategy and benchmark at each start.

`exposure_by_year` computes time-in-market from episode **timestamps** against the OOS
calendar, not from episode bar indices — those are relative to the run series, which begins
one warm-up prefix earlier, and indexing the OOS calendar with them silently attributes
exposure to the wrong years. A test pins this.

## Rationale

A four-figure percentage return on BTC over 2015–2025 is a fact about BTC. Its price rose
426× across the out-of-sample span; any long-biased rule applied to it prints numbers with
too many digits. A report that leads with the total return, however carefully caveated, is
inviting the wrong reading — and the first version of this report did exactly that.

The two tables settle the question the total return cannot:

- **Year by year, the mechanism is unmistakable.** The strategy lost to buy-and-hold in
  every up year on both symbols, and beat it in 5 of 6 down years. Time in market tracks it
  precisely: heavily invested through bull years, nearly flat through bear ones. This is not
  return prediction; it is insurance, bought with bull-market underperformance and paid out
  in bear markets — and the whole case therefore rests on **five observations**.
- **Start date moves the answer more than any parameter does.** The strategy's CAGR on BTC
  ranges from +11% to +49% depending only on when the investor began. A result that moves
  that much on a choice the strategy does not make is describing the sample, not the rule.

Both tables also produced findings the aggregate had hidden: the Sharpe advantage does not
survive the later start dates, and ETH has a down year (2019) in which the strategy lost to
holding — which a hardcoded "beat it in every down year" sentence had asserted wrongly
before the count was computed from the data.

## Standing rule this creates

Any future study on an instrument with a strong secular trend over its sample — crypto
above all — reports the same two tables before its verdict. The cost is a few seconds of
compute; the alternative is a report whose headline number is a property of the era, quoted
as though it were a property of the strategy.
