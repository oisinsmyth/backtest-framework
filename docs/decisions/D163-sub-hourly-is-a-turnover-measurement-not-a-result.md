# D163 — 15m and 30m are a turnover-and-cost measurement, not a performance result, and the walk-forward is not shrunk to make them one

**Status:** Committed
**Date:** 2026-08-19
**Category:** Validation & research integrity
**Source:** Cost-frequency frontier session

## Decision

15m and 30m appear in the frontier report in **their own section**, clearly labelled, with
**no walk-forward, no out-of-sample split, no Sharpe and no return claim**. What is
reported is trade count, median holding period in calendar terms, whipsaw rate, annualised
turnover, and fees alone as a fraction of capital per year. The 1h–1d ladder is re-run over
the *same* 60-day window so the sub-hourly rungs sit on an internally comparable curve
rather than floating alone.

Per-frequency diagnostics elsewhere in the study are likewise reported in **calendar
units** — median hold in days, whipsaw as "closed within 3 calendar days" — not in bars.

## Rationale

**Why not just shrink the windows.** yfinance serves 60 days of 15m/30m data. The study's
walk-forward is a 252-day training window; that does not fit inside 60 days. The tempting
move is to keep the *bar* counts (train = 252 bars) and call it a walk-forward — at 15m
that is a training slice of **2.6 days**. It would produce a Sharpe, a DSR, a full set of
tables, and every one of those numbers would be meaningless. This project exists to make
that kind of self-deception structurally harder, so the option is refused in writing rather
than left available.

**Why the measurement is still worth making.** Turnover is a property of the RULE and the
BAR SIZE, not of the sample's returns. Sixty days is plenty to establish that at 15m the
rule turns over ~750–790× a year, holds the median trade for five hours, whipsaws on 100%
of trades, and pays roughly 300% of capital a year in fees at the taker tier. That last
number needs no return data at all to be conclusive: there is no fee tier in this study at
which a rule paying a triple-digit percentage of capital annually in fees can be run. It
is the strongest single statement in the whole study and it comes from the section that
claims the least.

**Why calendar units throughout.** A table reporting "median 26 bars held" at 1d beside
"median 180 bars held" at 1h tells a reader nothing about what the strategy has become.
26 days versus 20 hours does. The same argument applies to the whipsaw threshold: leaving
`whipsaw_bars=3` fixed would define a whipsaw as three days at 1d and three hours at 1h,
and the resulting column would compare nothing. Bars are the engine's unit; calendar time
is the economics' unit, and the reader is being shown economics.

**What would be needed to do it properly, named rather than attempted.** Exchange APIs —
Binance and Kraken both serve complete 1m history free — would give the years of
sub-hourly data a real walk-forward needs. That is a new `DataSource` behind the existing
interface (D18), plus its own fixture, snapshot and cleaning rules for a provider whose
volume column actually works (D160). It is out of scope here, and saying so is the point
of R3.
