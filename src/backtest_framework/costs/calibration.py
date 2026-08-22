"""Automated σ/ADV calibration for the SqrtImpact brick (D66, D88).

Replaces the hand-paste step from the v1/v2 scripts: σ_daily is the sample stdev of
log returns on the PROVIDER-frame closes (already split-adjusted, hence
return-continuous — D75; computing on as-traded closes would fabricate a split-day
return, the exact bug the v2 fetch script had before D75), and ADV is the mean share
volume.

D66's caveat carries forward verbatim: this is FULL-SAMPLE calibration — a mild,
documented look-ahead in cost parameters (never in the signal). Per-window,
D44-compliant estimation remains deferred work; every study artifact that uses this
function restates the caveat.
"""

from __future__ import annotations

import math
import statistics
from typing import Mapping, Sequence

from ..data.bars import TimestampedBar
from .equity_bricks import ImpactParams


VOLUME_UNITS = ("shares", "quote_notional")
"""What a fixture's volume column actually counts.

`shares` — units of the instrument, the equity convention. `SPY` reports ~68M, which at
~$474 is the ~$32bn/day it really trades.

`quote_notional` — value in the quote currency, the convention every `X-USD` crypto pair in
this project uses. `BTC-USD` reports ~47.5bn, which cannot be coins (21M will ever exist)
and is USD.

**This distinction is not cosmetic and it was got wrong once (D187).** `SqrtImpact` divides
an order QUANTITY by ADV, so the two must be in the same units. Feeding USD notional into a
field meaning shares makes the ratio off by a factor of price — impact understated ~224x on
a $96k coin and overstated ~126x on a $0.00006 one, in the same run."""


def calibrate_impact_params(
    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]],
    volumes_by_symbol: Mapping[str, Sequence[float]],
    volume_units: str = "shares",
) -> dict[str, ImpactParams]:
    if volume_units not in VOLUME_UNITS:
        raise ValueError(
            f"volume_units must be one of {VOLUME_UNITS}, got {volume_units!r}. There is no "
            "safe default here: guessing wrong scales every impact charge by the square "
            "root of the price (D187)."
        )
    params: dict[str, ImpactParams] = {}
    for symbol, series in bars_by_symbol.items():
        if len(series) < 3:
            raise ValueError(f"calibration for {symbol!r} needs at least 3 bars, got {len(series)}")
        closes = [tb.bar.close for tb in series]
        returns = [math.log(b / a) for a, b in zip(closes, closes[1:])]
        sigma = statistics.stdev(returns)
        if sigma <= 0:
            raise ValueError(f"{symbol!r} has zero return volatility — cannot calibrate impact (D48)")

        if symbol not in volumes_by_symbol:
            raise ValueError(f"no volume series for {symbol!r} — ADV must be calibrated, not defaulted (D48)")
        raw_volumes = volumes_by_symbol[symbol]
        if volume_units == "shares":
            volumes = [v for v in raw_volumes if not math.isnan(v)]
        else:
            # Quote-currency notional -> units, bar by bar. Dividing the MEAN notional by
            # a mean price would be a different (and wrong) statistic on a series whose
            # price moves by orders of magnitude, which every coin here does.
            if len(raw_volumes) != len(series):
                raise ValueError(
                    f"{symbol!r} has {len(raw_volumes)} volumes against {len(series)} bars — "
                    "converting quote notional to units needs them aligned bar-for-bar"
                )
            volumes = [
                v / tb.bar.close
                for v, tb in zip(raw_volumes, series)
                if not math.isnan(v) and tb.bar.close > 0
            ]
        if not volumes:
            raise ValueError(f"{symbol!r} has no usable volume observations")
        adv = statistics.fmean(volumes)
        if adv <= 0:
            raise ValueError(f"{symbol!r} has non-positive mean volume {adv}")

        params[symbol] = ImpactParams(sigma_daily=sigma, adv_shares=adv)
    return params
