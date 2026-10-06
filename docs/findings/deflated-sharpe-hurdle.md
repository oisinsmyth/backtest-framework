# The deflated-Sharpe hurdle rises with the trial count

The best of many backtests looks good partly by luck. The expected maximum Sharpe of N
zero-edge trials (Bailey and López de Prado, 2014) is the floor a selected result has to clear,
and it rises with N. The trial registry exists so that N is a logged count rather than a
recollection.

## The case

A study ran a ladder of MACD rules on 57 ETFs, live from 2016-07-26 to 2024-12-30. Its best
cell, a long-or-flat signal-line rule, had an annualised Sharpe of 0.4957. The variance of
per-period Sharpe across the trials was 9.07e-5.

The study itself spent 42 configurations. Counted that way the floor is 0.3340 and the cell
clears it comfortably. The project's trial registries, across every study run before it, held
45,783 trials. Counted that way the floor is 0.6377 and the cell fails.

| Trials counted | Floor (annualised) | Best cell 0.4957 |
|---:|---:|---|
| 42 | 0.3340 | clears |
| 1,085 | 0.49568 | clears |
| 1,086 | 0.49572 | fails |
| 45,783 | 0.6377 | fails |

The result stops clearing at 1,086 trials. The cell cleared six of the seven checks it was
scored against; the trial count alone decided the seventh.

## What this shows

- The verdict depends on which trials are counted, and that has to be decided before looking at
  the result.
- A trial count cannot be reconstructed afterwards. `TrialRegistry` logs each trial as it runs
  and is append-only.

The floors above are `validation.dsr.expected_max_sharpe(n, 9.07e-5) × √252`.
