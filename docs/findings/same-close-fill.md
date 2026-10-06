# A same-close fill credited the overnight gap

## The error

A family of daily cross-sectional books computed each signal at the close of day t−1 and opened
the position at day t earning the return from close[t−1] to close[t]. That is a fill at the
signal's own close, which no live order can get. The earliest honest fill is the next open, and
the gap between the close and the next open accrued to a position that could not yet have
existed.

## The size of it

Re-scoring the best book with an open fill (the entry bar earns close[t] / open[t] − 1, every
later bar unchanged) gave:

| | close fill | open fill |
|---|---:|---:|
| Net, bp per bar | +18.93 | +5.14 |
| Gross, bp per bar | +32.37 | +18.06 |

Net fell 73%. The gap credited per entry averaged +44.8 bp on the long leg and +27.2 bp on the
short leg, more than the half-spread on either. A signal computed at the close was partly a
forecast of the next open: names that broke below a recent low tended to gap up the next
morning, and names above a recent high to gap down.

The difference was not limited to the entry bar. Only 378 of 1,256 trades occurred under both
conventions, because a different entry return moved exits, freed slots on different days, and
let the two books drift apart.

## In this framework

`run_backtest(fill_timing="next_open")` decides orders at bar t's close and fills them at bar
t+1's open. The default, `fill_timing="close"`, fills at the signal bar's close, which is the
convention that has to be justified for any strategy whose signal uses that close. Treat the fill
timing as part of the cost model and state it with every result.
