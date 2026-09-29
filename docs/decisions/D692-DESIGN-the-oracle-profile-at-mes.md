# D692 DESIGN — the oracle profile at MES: where the winners of the hourly continuation sit, shown before any filter is designed

*2026-09-29. Committed with its runner (`scripts/diag_d692_oracle_profile_mes.py`), before the run. It is hindsight
and descriptive only: nothing is fitted, filtered or traded. The result follows as a separate record.*

The principal: "Yes, run the oracle profile at MES".

It follows the principal's ruling on D690:
- filters are scored on the trades actually taken (MES, $4.42 a round trip);
- the oracle's results are shown first;
- the candidate filters are designed together.

## What it shows

**The candidates:** D690's, unchanged. At 10:30–14:30 on every session, follow the last 60 minutes for the next 60,
priced at 1 MES. They cover 2016-01-05 → 2023-12-29, with no burn-in, since nothing is fitted. D690's post-burn-in
MES oracle is reproduced as a check.

**The oracle labels:** WIN is net > 0; BAR is gross ≥ $8.84 (2 × the round trip).

**For every bucket of every input a filter could use at the decision time:**
- how many candidates it holds;
- its WIN and BAR rates, each with its lift over the overall rate;
- the mean gross (with a day-clustered t) and the mean net;
- its share of all the oracle's net P&L;
- the mean net of its winners and of its losers.

**The inputs:**
- the gamma regime: SUM, SPX, the ES book, and the SPX × ES sign cells;
- the G_SUM quintile;
- the side;
- regime × side;
- the time of day;
- the size of the last hour against a normal hour;
- today's realised volatility so far, and trailing σ;
- whether the last hour agreed with the day's move;
- the year;
- three two-way tables with the gamma regime.

The bucket count is reported, so no best bucket is read without its multiplicity.
