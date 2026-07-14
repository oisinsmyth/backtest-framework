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


def calibrate_impact_params(
    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]],
    volumes_by_symbol: Mapping[str, Sequence[float]],
) -> dict[str, ImpactParams]:
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
        volumes = [v for v in volumes_by_symbol[symbol] if not math.isnan(v)]
        if not volumes:
            raise ValueError(f"{symbol!r} has no usable volume observations")
        adv = statistics.fmean(volumes)
        if adv <= 0:
            raise ValueError(f"{symbol!r} has non-positive mean volume {adv}")

        params[symbol] = ImpactParams(sigma_daily=sigma, adv_shares=adv)
    return params
