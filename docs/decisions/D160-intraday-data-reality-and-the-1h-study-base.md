# D160 — Intraday data reality: 1h is the study base, everything coarser is resampled, and the cleaner is called on prices only

**Status:** Committed
**Date:** 2026-08-19
**Category:** Data layer
**Source:** Cost-frequency frontier session ([`docs/results/breakout_intraday.md`](../results/breakout_intraday.md))

## Decision

The cost-frequency frontier fetches **1h bars over 730 days** as its single study base
(`scripts/fetch_crypto_intraday.py` → `data/fixtures/crypto_intraday_1h_raw.csv.gz`) and
resamples upward to 2h/4h/6h/12h/1d. 15m and 30m are fetched over their available 60 days
and used only as a turnover measurement (D163).

That is forced by what the provider serves, probed before anything was built:

| interval | history yfinance serves |
|---|---|
| 15m, 30m | 60 days |
| **1h** | **730 days (~17,500 bars)** |
| 4h | not served for a `max` period |
| **6h** | **not a valid yfinance interval at all** |
| 1d | full history |

`clean` is called on **prices only** — `clean(bars)`, not `clean(bars, volumes)`. The
volume column is still written to the fixture and to the snapshot in full, and the
validator still reads it.

## Rationale

**Why not fetch each frequency natively.** There is no 6h interval to fetch and no 4h over
a usable span, so a natively-fetched ladder would have holes in the middle of the range
where the interesting behaviour is. Worse, each interval would cover a *different*
calendar, and the study's entire claim is that frequency is the only variable. Resampling
from one base makes every rung span the identical 730 days by construction (D161).

**Why the cleaner is called without volumes, and why that is a finding rather than a
workaround.** `clean-v1`'s `non_positive_volume` rule drops any bar whose volume is at or
below zero. That rule is right for daily equity bars, where a zero-volume print is a bad
print. yfinance reports **Volume = 0 on roughly half of all hourly BTC/ETH bars** — 17,520
of 34,923 in the committed fixture, spread evenly across every hour of the day and every
month of the sample, on instruments that have never had a zero-volume hour. The prices in
those bars are present, OHLC-consistent, and pass every other check.

Passing volumes would therefore have deleted half the price series to a provider reporting
artifact, leaving almost no complete UTC day to resample from — silently, since the
cleaner's job is to drop bars and it would have been doing exactly its job. Calling `clean`
on prices is a supported call of the existing signature, not an edit to a shared component,
and the runner asserts that price-only cleaning drops nothing so the volume series stays
index-aligned with the bars the validator sees. The artifact then surfaces as thousands of
non-blocking `zero_volume` warnings in the snapshot metadata instead of vanishing along
with the data.

Nothing downstream consumes volume anyway: `Bar` carries none, by D111.

**What this says about the shared cleaner, which is NOT changed here.** The rule needs a
per-instrument or per-frequency policy — "zero volume is a bad print" is a claim about
daily equity bars from a provider that reports daily equity volume correctly. Making it
conditional is a framework decision affecting five other studies, and it gets its own
decision record when someone needs it, not a side effect of this one.

**The validator's other half is silent for the opposite reason.** `MOVE_WARNING_THRESHOLD`
= 25% and `MOVE_HARD_THRESHOLD` = 60% were calibrated in D74 against genuine *daily*
equity moves. An hourly BTC bar has a standard deviation of about 0.48%, so a 25% hourly
move is a fifty-sigma event: over 730 days of hourly bars the check flags nothing, and the
largest hourly move in the fixture is 5.08% on BTC and 11.90% on ETH. The gate reports
**zero hard violations and no quarantine**, which is true and uninformative. A threshold is
a statement about a distribution, and that distribution scales with the square root of the
bar's duration; carrying D74's calibration across gives 25%/√24 = 5.10% warning and
60%/√24 = 12.25% hard at 1h, which would flag ten ETH bars and still pass the series.
**The shared validator is not edited to do this** — a duration-scaled threshold is a
framework change five studies depend on and needs its own decision.
