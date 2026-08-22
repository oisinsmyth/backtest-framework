# D192 — A zero-volume 1m bar is true, `clean-v1` cannot be told that, and the way out is a bar the market defines

**Status:** Committed (picks up D160's and D143's deferrals)
**Date:** 2026-08-22
**Category:** Data layer
**Source:** Provider probe ([`docs/results/binance_provider_probe.md`](../results/binance_provider_probe.md))

## Decision

Zero-volume 1m bars from the Binance archive are **real data and are not dropped**. The
`non_positive_volume` rule in `clean-v1` is **not edited**, and neither is `validate-v1`.

Instead this record states the finding that constrains any intraday study built on this
provider, and defers the mechanism to the pre-registration of the first such study, which
must choose its bar definition **before** it sees a return.

## The finding

D160 found yfinance reporting `Volume = 0` on roughly half of all hourly BTC/ETH bars whose
prices were present, OHLC-consistent, and on instruments that have never had a zero-volume
hour. That is a **provider defect**, and calling the cleaner on prices only was the right
response.

The zero bars here are a different thing, and the column that separates them is
`number_of_trades`. In **every sampled month, on every symbol**, the zero-volume bars and
the zero-trade bars are the same bars — exactly, not approximately:

| symbol | month | bars | zero-volume | zero-trade | both | rate |
|---|---|---:|---:|---:|---:|---:|
| `BTGUSDT` | 2022-01 | 44,640 | 25,878 | 25,878 | 25,878 | **57.97%** |
| `XEMUSDT` | 2022-09 | 43,200 | 24,486 | 24,486 | 24,486 | **56.68%** |
| `BTGUSDT` | 2022-10 | 33,660 | 15,886 | 15,886 | 15,886 | 47.20% |
| `BTCUSDT` | 2017-08 | 21,360 | 6,974 | 6,974 | 6,974 | 32.65% |
| `ETHUSDT` | 2017-08 | 21,360 | 5,806 | 5,806 | 5,806 | 27.18% |
| `BTCUSDT` | 2022-02 → 2026-07 | — | 0 | 0 | 0 | **0.000%** |

A bar that records no trades and no volume is not a bad print. It is the market saying
nothing happened in that minute. **Dropping it would delete a true observation**, which is
the opposite of the D160 case.

## Why this is the constraint that matters, and not the cleaner collision

The majors are clean from 2022 onward. The severe rates are on thin and dying listings —
and those are exactly the instruments the failure universe exists to include.

D140/D180 established that the failure universe is the only screen in this project that
ever caught anything: E1 cleared its bar five times on BTC and ETH, then lost on 57 of 62
coins, because those two sat at the 97th and 85th percentile of the variable that decided
the outcome. The final report's own summary is that every statistical control here handles
error *within* a sample and none can detect that the sample is the problem.

On a 1m time grid, **more than half the bars of a dying coin are empty**. A rule sampled on
that grid spends most of its bars looking at a price that did not move *because nothing
traded*, which is not the same fact as a price that did not move. Volatility, breakout
counts, holding periods and whipsaw rates are all computed off that grid and all inherit
the confusion.

Both ways out cost something, and the cost is the reason this is a decision rather than an
implementation detail:

- **Restrict intraday work to liquid names.** Reintroduces precisely the survivorship
  problem D180 identified. Five passes on two favourable series is the single most
  expensive mistake this project has made, and it would be re-made deliberately.
- **Move off time bars onto volume or dollar bars.** Keeps the failure universe and removes
  the empty-bar problem by construction, because a bar closes when a quantity of trading has
  happened rather than when a clock ticks. But it changes the object being measured, and no
  result would then be directly comparable to any daily result in this project.

Neither is chosen here. Choosing after seeing which one produces a better number is the
failure mode nine pre-registrations exist to prevent.

## Why the shared gate is not edited

`clean()` and `validate()` take data and nothing else. There is no per-rule disable, no rule
registry, no config object; thresholds are module constants. The only existing lever is
`allow_quarantined=True` on `SnapshotStore.load`, which is D143's override and costs a full
results section, a `gate` dict in the summary payload, and a named justification.

D160 saw this coming and said so:

> The rule needs a per-instrument or per-frequency policy — "zero volume is a bad print" is
> a claim about daily equity bars from a provider that reports daily equity volume
> correctly. Making it conditional is a framework decision affecting five other studies, and
> it gets its own decision record when someone needs it.

D143 deferred the same thing from the other direction, on the grounds that recalibrating a
cross-cutting data gate from inside a study is how gates stop meaning anything.

**This record picks up both deferrals and declines to spend them yet.** Editing
`non_positive_volume` now would change the gate for five existing studies in order to serve
a study that has not been designed, whose bar definition is undecided, and which may not use
time bars at all. The correct order is: decide the bar, then decide what a bad bar is.

What *is* settled is the criterion, so the later decision is not made from scratch: **zero
volume is droppable only where it disagrees with `number_of_trades`.** Agreement means the
bar is true. That is a testable rule, it distinguishes D160's case from this one on
measured evidence rather than on which provider produced it, and `volume_census` in
`data/binance_archive.py` computes it.

## Consequences

- Any intraday study on this provider must state its bar definition in its
  pre-registration, with the empty-bar rate of its own universe measured and reported.
- The same study must state which of the two ways out it took and what that costs, in the
  D188 style — the cost is known in advance and reporting it is not optional.
- `validate-v1`'s `zero_volume` **warning** is left alone and is now informative rather than
  noise: on this provider a warning count that diverges from the zero-trade count is a
  genuine provider defect worth looking at.
- D74's `MOVE_WARNING_THRESHOLD` / `MOVE_HARD_THRESHOLD` remain calibrated on daily equity
  moves and remain uninformative at 1m, for the reason D160 gives at length. Untouched here,
  and still open.
