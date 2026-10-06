# A lag audit removed 93% of an apparent edge

## The study

A cross-sectional short book screened 1,573 US equities, delisted names included, each day,
ranked the qualifying names on a score built from recent returns, and shorted the N lowest.
Its first run reported two surviving cells at annualised Sharpe +2.250 and +1.865.

## The check

The held set was derived a second time, from the score lagged one bar (`score[:, t-1]`), in a
separate implementation that never called the study's selection function. The two disagreed.

Which names qualified was correctly lagged. Which N of them were held was chosen with the
score at the close of the bar the position was about to be paid for. Because the score includes
that bar's return, the ranking picked names that had already fallen that day, and the short book
then booked the fall it had selected on.

The score was 98% correlated with its own value one bar earlier, so the error was nearly
invisible in the inputs; all of the apparent edge sat in the remaining 2%:

| | correlation |
|---|---:|
| score at t with score at t−1 | +0.9805 |
| score at t with return at t (the error) | +0.0737 |
| score at t−1 with return at t (tradeable) | −0.0103 |

| Cell | Same-day score | Lagged one bar |
|---|---:|---:|
| top 25 | +2.250 Sharpe | −0.638 Sharpe |
| top 50 | +1.865 Sharpe | −0.659 Sharpe |

Measured against a turnover-matched random control, the ranking's gross Sharpe advantage fell
from +3.218 / +3.083 / +2.719 to +0.223 / +0.203 / +0.202 across three book widths: about 93% of
the apparent edge was the error. Cells the ranking never selected were bit-identical between the
two runs, which ties the change to the selection step and nothing else.

## Where the framework stands

`DataView` makes this error impossible for a strategy run through `run_backtest`: a view never
holds bars after the current one. The study was written as vectorised array code outside the
engine, where no such guard applies. The defence there is the one that caught it: re-derive the
held set from lagged inputs with independent code and require the two to agree.
