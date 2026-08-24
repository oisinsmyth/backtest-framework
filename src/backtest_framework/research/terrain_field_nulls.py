"""S6 against matched random fields (D197 and its amendment).

## Why `pseudo_levels` does not work here

`terrain_nulls.pseudo_levels` shuffles discrete level PRICES uniformly over the span the
real levels covered. S6 has no level set — it is a continuous signed field — and its
claim is not "there are levels here" but "the mass is in the right place, with the right
sign". A null has to preserve everything except placement.

So the shuffle happens at the SWING, not at the bucket: each pivot keeps its bar index,
its sign, its weight and its kernel width, and only its `price` is redrawn. Sign balance,
magnitude distribution, deposit schedule and kernel geometry are therefore identical in
both arms by construction rather than by care, and the erasure — which is a function of
the BARS alone — is bit-identical in every draw.

That last point is why D197 makes the erasure-only control the primary comparison and not
this null. The erasure is carried identically by every draw, so no null can detect a
confound that lives in it. The null answers a narrower question: given that mass exists,
does it matter where it sits.

## Two bands, and why (the D197 amendment)

`LOCAL` — the verdict null. A pivot's price is redrawn uniformly over the high-low range
of the trailing lookback at its own bar. Era, price scale and volatility all match, so the
only randomised thing is placement within the neighbourhood.

`SPAN` — the diagnostic. `pseudo_levels`' whole-series convention, kept for comparability
with D189 and D196. Over a decade in which BTC ran 300x it scatters 2015 pivots across
2024 prices, which is a weaker test: the real arm can win merely by being in the right
neighbourhood. Reported, never a verdict.

The gap between the two separates "the right neighbourhood" from "the right place in it".
Only the second is a claim about the sensor.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Sequence

import numpy as np

from ..data.bars import TimestampedBar
from .terrain_field import FieldParams, Swing
from .terrain_strategies import PositionResult, StrategyResult

NULL_LOOKBACK = 180
"""Bars behind the local band. S5's primary lookback, reused rather than re-chosen — the
window over which "the neighbourhood" means anything is the same window the sensor's own
levels were built from."""


class ShuffleBand(Enum):
    LOCAL = "local"
    """Verdict. Redraw within the trailing lookback's high-low range at the pivot's bar."""

    SPAN = "span"
    """Diagnostic. Redraw over the span of all real pivot prices (D189's convention)."""


def _local_bounds(
    bars: Sequence[TimestampedBar], lookback: int = NULL_LOOKBACK
) -> tuple[np.ndarray, np.ndarray]:
    """Trailing high-low range per bar — the neighbourhood a pivot could have sat in."""
    n = len(bars)
    highs = np.array([b.bar.high for b in bars], dtype=float)
    lows = np.array([b.bar.low for b in bars], dtype=float)
    lo = np.empty(n)
    hi = np.empty(n)
    for t in range(n):
        a = max(0, t - lookback + 1)
        lo[t] = lows[a : t + 1].min()
        hi[t] = highs[a : t + 1].max()
    return lo, hi


def shuffled_swings(
    swings: Sequence[Swing],
    band: ShuffleBand,
    rng: np.random.Generator,
    local_lo: np.ndarray | None = None,
    local_hi: np.ndarray | None = None,
) -> list[Swing]:
    """Redraw every pivot's PRICE and change nothing else.

    `sigma_ln` travels with the swing unchanged. It is a property of the era's volatility,
    not of where the pivot happened to sit, and holding it fixed keeps the two arms
    matched on kernel width — otherwise the null would deposit differently shaped mass and
    the comparison would be measuring geometry instead of placement."""
    if band is ShuffleBand.SPAN:
        prices = [s.price for s in swings]
        if not prices:
            return list(swings)
        lo, hi = min(prices), max(prices)
        draws = rng.uniform(math.log(lo), math.log(hi), size=len(swings))
        return [
            Swing(s.index, s.confirmed_at, s.sign, float(math.exp(d)), s.weight, s.sigma_ln)
            for s, d in zip(swings, draws)
        ]

    if local_lo is None or local_hi is None:
        raise ValueError("the LOCAL band needs per-bar bounds; pass local_lo/local_hi")
    out: list[Swing] = []
    for s in swings:
        lo, hi = float(local_lo[s.index]), float(local_hi[s.index])
        if not (hi > lo > 0.0):
            out.append(s)
            continue
        d = float(rng.uniform(math.log(lo), math.log(hi)))
        out.append(
            Swing(s.index, s.confirmed_at, s.sign, math.exp(d), s.weight, s.sigma_ln)
        )
    return out


@dataclass
class FieldNullComparison:
    """One strategy, the real field against `n_sims` matched random ones."""

    real: StrategyResult
    band: ShuffleBand
    null_sharpes: list[float] = field(default_factory=list)
    null_returns: list[float] = field(default_factory=list)
    null_trades: list[int] = field(default_factory=list)

    def percentile(self, values: Sequence[float], observed: float) -> float:
        """Mid-rank percentile, matching `breakout_nulls.summarise_null`."""
        if not values:
            return 0.0
        below = sum(1 for v in values if v < observed)
        equal = sum(1 for v in values if v == observed)
        return 100.0 * (below + 0.5 * equal) / len(values)

    def to_dict(self, bars: Sequence[TimestampedBar], periods_per_year: float) -> dict:
        real_sharpe = self.real.curve_sharpe(bars, periods_per_year)
        null_mean = statistics.fmean(self.null_sharpes) if self.null_sharpes else 0.0
        return {
            "band": self.band.value,
            "n_trades_real": self.real.n_trades,
            "n_trades_null_mean": (
                statistics.fmean(self.null_trades) if self.null_trades else 0.0
            ),
            "real_sharpe": real_sharpe,
            "real_total_return": self.real.curve_total_return(bars),
            "real_max_drawdown": self.real.max_drawdown(bars),
            "real_hit_rate": self.real.hit_rate,
            "null_sharpe_mean": null_mean,
            "null_sharpe_p05": (
                float(np.percentile(self.null_sharpes, 5)) if self.null_sharpes else 0.0
            ),
            "null_sharpe_p95": (
                float(np.percentile(self.null_sharpes, 95)) if self.null_sharpes else 0.0
            ),
            "sharpe_delta": real_sharpe - null_mean,
            "sharpe_percentile": self.percentile(self.null_sharpes, real_sharpe),
            "n_sims": len(self.null_sharpes),
        }


def compare_field_to_null(
    bars: Sequence[TimestampedBar],
    swings: Sequence[Swing],
    params: FieldParams,
    run: Callable[[Sequence[Swing]], StrategyResult],
    band: ShuffleBand,
    n_sims: int,
    seed: int,
    periods_per_year: float = 365.0,
    lookback: int = NULL_LOOKBACK,
) -> FieldNullComparison:
    """Run `run(swings)` on the real pivots and on `n_sims` shuffled sets.

    `run` closes over everything except the swings — the bars, the params, the costs, the
    stop, the target — so the two arms cannot differ in any other respect. The pairing is
    enforced by the signature rather than by discipline, which is the same arrangement
    `terrain_strategies.compare_to_null` uses and for the same reason."""
    comparison = FieldNullComparison(real=run(swings), band=band)
    local_lo, local_hi = (
        _local_bounds(bars, lookback) if band is ShuffleBand.LOCAL else (None, None)
    )
    rng = np.random.default_rng(seed)
    for _ in range(n_sims):
        result = run(shuffled_swings(swings, band, rng, local_lo, local_hi))
        comparison.null_sharpes.append(result.curve_sharpe(bars, periods_per_year))
        comparison.null_returns.append(result.curve_total_return(bars))
        comparison.null_trades.append(result.n_trades)
    return comparison


def rotation_null(
    result: PositionResult,
    n_sims: int,
    rng: np.random.Generator,
) -> list[PositionResult]:
    """The realised book, rotated in time — the TIMING control D201 lacked (D202).

    Circularly rotating the position series by a random offset preserves the exposure
    distribution, the autocorrelation, the turnover and the net long tilt **exactly**, and
    destroys only the alignment with price. A rotated book therefore carries the same beta
    against the same uptrend as the real one.

    That is what makes it the right control here. Sharpe is invariant to constant leverage,
    so a book running at +0.78 net exposure cannot be separated from buy-and-hold by
    scaling arguments, and the mass-shuffle null answers a different question (placement).
    Only rotation asks: did the exposure CHANGE at the right moments?

    D201 had neither, and its best cells turned out to be one multi-year long."""
    n = len(result.position)
    out = []
    for _ in range(n_sims):
        k = int(rng.integers(1, n)) if n > 1 else 0
        rotated = result.position[k:] + result.position[:k]
        out.append(
            PositionResult(
                tuple(rotated), result.returns, result.cost_bps, result.periods_per_year
            )
        )
    return out
