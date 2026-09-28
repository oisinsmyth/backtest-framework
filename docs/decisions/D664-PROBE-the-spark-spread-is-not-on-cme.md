# D664 PROBE — the spark spread cannot be tested or traded on CME: all 121 CME electricity futures carry zero open interest and zero volume, and the main US power codes are absent from the Globex feed in every year sampled

*2026-09-28, on the principal's word ("Do the spark spread probe"). A data probe, not a study: nothing was bought and
no market data was read. Script `scripts/probe_d664_spark_power.py`; output
[`data/d664_spark_probe.json`](../../data/d664_spark_probe.json).*

## Why

`ALPHA_PROGRAMME.md` §3.2 names three processing spreads: crack, crush and spark. The crack closed in
[D653](D653-STAGE-0-RESULT-not-supported-the-deviation-is-an-era.md) and the crush in
[D656](D656-STAGE-0-RESULT-no-premium-a-real-reversion-no-trade.md). The spark spread (power less gas at a heat rate)
needs a power price. The question before any design is whether CME's power futures exist in the data and trade at all.
It is asked now because the Databento subscription lapses around 2026-10-11, and a yes would have meant a pull.

## What was found

**1. CME's own product slate** (Energy > Electricity, futures; one request in a browser, trade date 2026-09-25, final):
**121 electricity futures listed, every one marked Globex and ClearPort, and every one at zero open interest and zero
volume.** The field was checked on the same endpoint: Henry Hub natural gas 1,794,933 contracts, WTI 1,854,775.

**2. Databento's `GLBX.MDP3`**, symbology resolution only (free, no market data), four one-week windows (June 2012,
2016, 2020, 2024):

| | 2012 | 2016 | 2020 | 2024 |
|---|---|---|---|---|
| NG (control) | 3,299 instruments | 1,452 | 1,927 | 1,972 |
| CL (control) | 72 | 1,374 | 1,623 | 1,887 |
| 12 power codes: PJM Western Hub RT and DA, peak and off-peak, 1 MW and 50 MW; Northern Illinois Hub DA and RT peak; ERCOT North RT peak and 2x16; the PJM daily 800 MWh | **absent** | **absent** | **absent** | **absent** |

A parent that exists resolves to its instruments; these return "could not resolve", so there are no instrument
definitions under them in the feed in any window.

## What this decides

**The spark spread has no CME expression to backtest or trade.** US power futures trade on ICE (ICE Futures US), which
would need a different data subscription and a venue the prop book's accounts do not offer. Recommended: close the
spark spread with the other two, which leaves `ALPHA_PROGRAMME.md` §3.2's processing-spread list fully closed.
Closure is the principal's word (R15).
