# Corporate actions booked as dividends

## The error

A US equity panel applied every dividend in its events file as a return of
`log1p(amount / close)`, with no bound. The events file recorded some corporate actions (spin-off
consideration, merger consideration, returns of value on stitched series) as cash dividends,
while the price stayed at its post-transaction level. Thirty of 35,713 dividends, 0.08%, became
return days of +9% to +356%.

Two examples: one stock closed at 10.94 and then 11.04 on its event day and was credited +356%.
Another rose 39.5% on the tape and was credited 49% more.

## How it was found

A concentration report said six names of 718 made half of one book's P&L. Nobody asked which six;
one of them carried a +356% day on a 0.9% price move. Printing the top trade's bar (open, high,
low, close, volume, return) beside any event on that bar would have shown it in one line.

## The fix and its effect

A dividend of at least 10% of the close is applied only if the price fell by at least half of
what the distribution implies (−r / (1 + r)). Otherwise it is dropped and logged. The rule
removed all thirty and kept every genuine large distribution in the panel.

With the thirty days corrected and nothing else changed, the most-cited book's edge halved, from
+14.57 to +7.15 bp per bar.

## In this framework

`DividendFlow` applies dividends exactly as given, and the validator does not cross-check a
dividend against the price move. If an events file comes from a vendor, check each large
distribution against the price before running anything on it, and name the top trades of every
result.
