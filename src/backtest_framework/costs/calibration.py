"""σ/ADV calibration for the SqrtImpact brick.

σ_daily is the sample stdev of log returns on the provider-frame closes, which are
split-adjusted (as-traded closes would produce a spurious split-day return). ADV is the
mean volume in shares.

Calibration is full-sample: a mild look-ahead in the cost parameters, not in the signal.
Per-window estimation is not implemented; a study using this should state the caveat.
"""

from __future__ import annotations

import math
import statistics
from typing import Mapping, Sequence

from ..data.bars import TimestampedBar
from .equity_bricks import ImpactParams


VOLUME_UNITS = ("shares", "quote_notional")
"""What a fixture's volume column counts.

`shares`: units of the instrument, the equity convention. `SPY` reports ~68M, which at
~$474 is ~$32bn/day.

`quote_notional`: value in the quote currency, the convention for yfinance `X-USD` crypto
pairs. `BTC-USD` reports ~47.5bn, which must be USD (only 21M coins will ever exist).

`SqrtImpact` divides order quantity by ADV, so both must be in the same units. USD notional
read as shares puts the ratio off by a factor of price: impact understated ~224x on a $96k
coin and overstated ~126x on a $0.00006 one."""


def _is_present(volume: float | None) -> bool:
    """True when this bar has a usable volume, treating both None and NaN as a gap.

    The data layer writes a gap as NaN (`csv_fixture._to_float`); the engine layer
    (`engine/dataview.normalise_volumes`) converts NaN to None, its canonical gap.
    `math.isnan` would raise `TypeError` on None, so this check accepts both.
    """
    return volume is not None and volume == volume


def calibrate_impact_params(
    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]],
    volumes_by_symbol: Mapping[str, Sequence[float]],
    volume_units: str = "shares",
) -> dict[str, ImpactParams]:
    if volume_units not in VOLUME_UNITS:
        raise ValueError(
            f"volume_units must be one of {VOLUME_UNITS}, got {volume_units!r}. There is no "
            "safe default here: guessing wrong scales every impact charge by the square "
            "root of the price."
        )
    params: dict[str, ImpactParams] = {}
    for symbol, series in bars_by_symbol.items():
        if len(series) < 3:
            raise ValueError(f"calibration for {symbol!r} needs at least 3 bars, got {len(series)}")
        closes = [tb.bar.close for tb in series]
        returns = [math.log(b / a) for a, b in zip(closes, closes[1:])]
        sigma = statistics.stdev(returns)
        if sigma <= 0:
            raise ValueError(f"{symbol!r} has zero return volatility; cannot calibrate impact")

        if symbol not in volumes_by_symbol:
            raise ValueError(f"no volume series for {symbol!r}; ADV must be calibrated, not defaulted")
        raw_volumes = volumes_by_symbol[symbol]
        if volume_units == "shares":
            volumes = [v for v in raw_volumes if _is_present(v)]
        else:
            # Convert quote-currency notional to units bar by bar. Dividing the mean
            # notional by a mean price would be wrong for a series whose price moves by
            # orders of magnitude, as many coins do.
            if len(raw_volumes) != len(series):
                raise ValueError(
                    f"{symbol!r} has {len(raw_volumes)} volumes against {len(series)} bars; "
                    "converting quote notional to units needs them aligned bar for bar"
                )
            volumes = [
                v / tb.bar.close
                for v, tb in zip(raw_volumes, series)
                if _is_present(v) and tb.bar.close > 0
            ]
        if not volumes:
            raise ValueError(f"{symbol!r} has no usable volume observations")
        adv = statistics.fmean(volumes)
        if adv <= 0:
            raise ValueError(f"{symbol!r} has non-positive mean volume {adv}")

        params[symbol] = ImpactParams(sigma_daily=sigma, adv_shares=adv)
    return params
