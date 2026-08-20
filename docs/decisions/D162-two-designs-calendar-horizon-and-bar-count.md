# D162 — Two frequency designs — constant calendar horizon and constant bar count — which answer different questions and are never conflated

**Status:** Committed
**Date:** 2026-08-19
**Category:** Validation & research integrity
**Source:** Cost-frequency frontier session

## Decision

Every frequency runs under **both** designs, reported separately end to end:

| | Design A — constant calendar horizon | Design B — constant bar count |
|---|---|---|
| Entry / exit window | 40 days / 10 days at every frequency | 40 bars / 10 bars at every frequency |
| At 1h | 960 / 240 bars | 40 / 10 bars (= 40 h / 10 h) |
| Inverse-vol estimate window | 20 days | 20 bars |
| Question | does finer SAMPLING of the same signal help, or just add cost? | does the trend effect exist at shorter HORIZONS at all? |

The walk-forward is scaled to **equal calendar duration** at every frequency — train 252
days, test 63 days, step 63 days — so every frequency gets the same number of windows over
the same span (D161). The whipsaw threshold is likewise 3 *calendar days* everywhere
rather than 3 bars.

`periods_per_year` is set in **both** places it appears — the argument required throughout
`analytics.metrics` (D17's rule) and the field inside the `inverse_vol_weight` config
(D110) — and `assert_periods_per_year_agree` refuses to run any cell where the two
disagree.

## Rationale

**Why two designs and not one.** "Run it intraday" is two different experiments wearing
one sentence, and on this data they give opposite answers. Under Design A the trade
*count* barely changes — a 40-day breakout fires as often as it fires, whatever bar you
sample it on — so annualised turnover rises about 10% from 1d to 1h (10.5× to 11.5× on
BTC) and fees never become binding at any rung. Under Design B a 40-bar entry at 1h is a
40-HOUR breakout: turnover multiplies 18–21×, the median hold collapses from 26 days to
20 hours, and the whipsaw rate goes from 0% to 97%. Reporting a single "intraday" number
would have averaged a null result with a catastrophic one and reported the mean of two
things that are not the same quantity.

**Why the vol-estimate window scales with the design.** Under Design A a 20-BAR vol
estimate at 1h would measure twenty hours of volatility while the signal measured forty
days — so "the economic signal is identical, only sampling changes" would simply be false,
and every position would be sized off a different quantity at each rung. Scaling it with
the design keeps each design internally coherent: A is a calendar-horizon strategy
throughout, B is a bar-count strategy throughout, and neither is a hybrid nobody chose.

**Why `periods_per_year` gets a runtime assertion rather than care.** Neither layer can
see the other's copy. A study that scaled one and not the other would report a 1h Sharpe
annualised on 8,760 periods while sizing every position as though a bar were a day — and
nothing would fail, no test would notice, and the sizing would be wrong by a factor of
√24. This is the same class of bug D98 found in the DSR units, so it gets the same
treatment: an explicit, tested equality check that refuses to run rather than a convention
that has to be remembered.

**Consequence for multiplicity.** At 1d the two designs are the same configuration. That
is deliberate — it is the anchor tying this ladder to `BREAKOUT_RESULTS.md` — and the
multiplicity table reports 12 logged trials per (symbol, tier) of which **11 are distinct
configurations**, rather than double-counting the duplicate.
