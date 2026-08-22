"""Terrain sensors: where resting supply and demand sit relative to price (D189).

Phase 3 of `New Docs/TERRAIN_MODEL.md`. The strategies detect impulse; the terrain maps the
medium. **The strategy logic does not change** — this module produces a density over price
buckets and nothing else. Fusion, per-trigger features and gates all come later, and each
depends on a sensor that has passed the null test in `terrain_nulls.py` first.

## The interface is defined here and frozen for every sensor

`TERRAIN_IMPLEMENTATION_PLAN.md` gives WP1 the job of fixing the common interface, so it
lives here rather than being rediscovered per sensor:

    sensor.density(bars, index, volumes) -> PriceDensity | None

computed strictly from data at or before `index`. `None` means **unavailable** — never an
imputed empty density, and never a silently-degenerate one. A sensor without enough history
must say so, because the fusion layer's availability mask is only meaningful if
unavailability is representable.

## Look-ahead is guarded HERE, not inherited

`DataView` (D32/D56) makes look-ahead structurally impossible for a strategy: the view is
constructed already sliced, so future bars are not merely forbidden but absent. **A sensor
is analytics, not a strategy**, and D181 is the record of what that distinction cost — the
ensemble weighted itself with whole-sample volatility for as long as it existed, inside a
project with a look-ahead guard, because the guard does not reach analytics built on
strategy output.

So `density()` takes an explicit `index` and slices internally, and
`tests/unit/test_terrain.py` asserts the property directly: perturbing any bar after `index`
must not change the density at `index`.

## Volume units are declared, never inferred

D187: the crypto fixtures report **quote-currency notional** (BTC prints ~47.5bn, which
cannot be coins) and the equity fixtures report **shares**. Reading one as the other scaled
every market-impact charge by the square root of the price for as long as it went unnoticed.

A volume-at-price profile in notional is a *dollars traded at each price* map; in shares it
is a *units traded* map. Both are defensible and they are different objects, so
`VolumeProfileSensor` takes the units as a required, validated parameter.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Any, Protocol, Sequence

from ..data.bars import TimestampedBar

VOLUME_UNITS = ("shares", "quote_notional")
"""Same two conventions `costs.calibration` pins, and for the same reason (D187)."""

LOOKBACK_DAYS = (90, 180)
"""The ONLY lookbacks this sensor may take. `TERRAIN_MODEL.md`: "sweep only {90, 180}
days". A third value is a search, and the terrain programme's multiplicity ledger counts
every combination tested."""

BUCKET_ATR = (0.25, 0.5)
"""The ONLY bucket widths, in ATR units. Fixed dollar buckets are prohibited by the spec —
a $100 bucket means something different on a $300 coin and a $90,000 one."""

ATR_WINDOW = 20
"""Bars of true range behind the bucket width. Matches `AtrStop`/`ChandelierStop`, so the
terrain and the stops measure volatility the same way rather than two ways."""


@dataclass(frozen=True)
class PriceDensity:
    """A normalised mass over contiguous price buckets, as of one bar.

    `mass` sums to 1.0 over buckets that saw any volume, so two sensors on different
    instruments and different scales are comparable before fusion — the spec's requirement
    that "sensor output is normalized to its own trailing distribution before fusion"."""

    edges: tuple[float, ...]
    """Bucket boundaries, ascending. `len(edges) == len(mass) + 1`."""
    mass: tuple[float, ...]
    bucket_width: float
    """In price units, derived from ATR at the sensor's index — carried so a consumer can
    express distances in ATR without recomputing the ATR that produced the buckets."""
    lookback: int
    bucket_atr: float
    n_bars: int
    """Bars that contributed. Below the lookback only at the very start of a series, and
    the sensor returns None rather than a thin density in that case."""
    is_stub: bool = False
    """Reserved for the honest-stub sensors the spec requires (S3 before its data exists).
    Always False for a sensor computing from real data."""

    def bucket_of(self, price: float) -> int | None:
        """Index of the bucket containing `price`, or None if outside the mapped range.

        Outside-the-range is a real answer: a price the lookback never visited has no
        density, and returning 0.0 would be indistinguishable from a visited-but-empty
        bucket."""
        if price < self.edges[0] or price > self.edges[-1]:
            return None
        idx = int((price - self.edges[0]) / self.bucket_width)
        return min(idx, len(self.mass) - 1)

    def mass_at(self, price: float) -> float | None:
        i = self.bucket_of(price)
        return None if i is None else self.mass[i]

    def centre(self, i: int) -> float:
        return (self.edges[i] + self.edges[i + 1]) / 2.0

    def levels(self, quantile: float, kind: str) -> tuple[float, ...]:
        """High- or low-volume nodes: local extrema past a density quantile.

        HVNs are consensus/inventory zones, LVNs are vacuum. "Local extremum" is strict
        against both neighbours, so a plateau produces no level rather than one level per
        bucket in it — a plateau is not a node."""
        if kind not in ("hvn", "lvn"):
            raise ValueError(f"kind must be 'hvn' or 'lvn', got {kind!r}")
        occupied = [m for m in self.mass if m > 0.0]
        if len(occupied) < 3:
            return ()
        threshold = _quantile(sorted(occupied), quantile)
        out = []
        for i in range(1, len(self.mass) - 1):
            a, b, c = self.mass[i - 1], self.mass[i], self.mass[i + 1]
            if kind == "hvn" and b > a and b > c and b >= threshold:
                out.append(self.centre(i))
            elif kind == "lvn" and b < a and b < c and b <= threshold and b > 0.0:
                out.append(self.centre(i))
        return tuple(out)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lookback": self.lookback,
            "bucket_atr": self.bucket_atr,
            "bucket_width": self.bucket_width,
            "n_bars": self.n_bars,
            "n_buckets": len(self.mass),
            "low": self.edges[0],
            "high": self.edges[-1],
            "is_stub": self.is_stub,
        }


class TerrainSensor(Protocol):
    """Every sensor answers one question: where is the mass, as of this bar?

    `density` must be computable from `bars[:index + 1]` alone. That is asserted by
    property test rather than trusted, because nothing structural enforces it here."""

    @property
    def name(self) -> str:
        """Read-only, deliberately.

        Declared as a bare `name: str` this would be a SETTABLE variable, and a frozen
        dataclass supplies a read-only attribute — so every sensor would fail the protocol
        and need a `type: ignore`. That is the same protocol-variance trap audit F20 fixed
        on `Instrument` and that `ScheduledWeightStrategy` still carries an ignore for.
        Sensors are frozen because a sensor whose parameters can change after construction
        cannot be trusted to have produced the densities attributed to it."""

    def density(
        self,
        bars: Sequence[TimestampedBar],
        index: int,
        volumes: Sequence[float] | None = None,
    ) -> PriceDensity | None: ...


def mean_true_range(bars: Sequence[TimestampedBar], start: int, end: int) -> float:
    """Mean true range over bars [start, end). Each bar's TR needs the previous close, so
    `start` must be at least 1.

    Deliberately the same arithmetic as `strategies.breakout._mean_true_range`, on bars
    rather than a DataView. Not imported from there because that module's version takes a
    `DataView` a sensor does not have, and re-deriving it would be worse than restating
    it — the two are checked against each other in the tests."""
    if start < 1:
        raise ValueError(f"true range needs a previous close, so start must be >= 1, got {start}")
    if end <= start:
        raise ValueError(f"empty ATR window [{start}, {end})")
    total = 0.0
    for j in range(start, end):
        bar, prev_close = bars[j].bar, bars[j - 1].bar.close
        total += max(bar.high - bar.low, abs(bar.high - prev_close), abs(bar.low - prev_close))
    return total / (end - start)


@dataclass(frozen=True)
class VolumeProfileSensor:
    """S1 — volume at price over a rolling lookback.

    High-volume nodes are where inventory changed hands and where impulse is expected to be
    absorbed; low-volume nodes are where it traversed quickly. This is the sensor
    `TERRAIN_MODEL.md` calls the lead one: it computes from immutable exchange data, it is
    the only sensor family adjacent to validated microstructure work, and it is expected to
    pass its null.

    **Built on DAILY bars, deviating from the spec's preference for intraday, and the
    reason is recorded in D189.** The 1h fixture reports zero volume on half its bars — the
    known yfinance defect for crypto — so a volume-at-price map built on it would be
    missing half its mass, non-randomly. Daily volume is complete across 2015-2025, eleven
    years against the intraday fixture's two, and it is the frequency the accepted
    baselines trade at, which is what the ladder's next step has to annotate. The spec
    wants intraday for sharpness, not necessity."""

    lookback_days: int
    bucket_atr: float
    volume_units: str
    name: str = "S1_volume_profile"

    def __post_init__(self) -> None:
        if self.lookback_days not in LOOKBACK_DAYS:
            raise ValueError(
                f"lookback_days must be one of {LOOKBACK_DAYS}, got {self.lookback_days}. "
                "The spec fixes this set; a third value is an unregistered search."
            )
        if self.bucket_atr not in BUCKET_ATR:
            raise ValueError(
                f"bucket_atr must be one of {BUCKET_ATR}, got {self.bucket_atr}. "
                "The spec fixes this set; a third value is an unregistered search."
            )
        if self.volume_units not in VOLUME_UNITS:
            raise ValueError(
                f"volume_units must be one of {VOLUME_UNITS}, got {self.volume_units!r}. "
                "There is no safe default: a notional column read as shares scaled every "
                "impact charge by the square root of the price once already (D187)."
            )

    def warm_up_bars(self) -> int:
        """Bars needed before the first density. The lookback itself, plus the ATR window
        that sets the bucket width, plus one for the ATR's first previous close."""
        return self.lookback_days + ATR_WINDOW + 1

    def density(
        self,
        bars: Sequence[TimestampedBar],
        index: int,
        volumes: Sequence[float] | None = None,
    ) -> PriceDensity | None:
        """Volume-at-price over `bars[index - lookback + 1 : index + 1]`.

        Everything after `index` is sliced away before any arithmetic touches it, so the
        no-look-ahead property is a fact about the code path rather than a convention."""
        if volumes is None:
            raise ValueError(
                f"{self.name} is a volume-at-price sensor and was given no volume series. "
                "A price-only profile is a different sensor, not a degraded version of "
                "this one."
            )
        if len(volumes) != len(bars):
            raise ValueError(
                f"{len(bars)} bars against {len(volumes)} volumes — a volume-at-price map "
                "needs them aligned bar-for-bar (D187's second bug was exactly this)."
            )
        if index < self.warm_up_bars() - 1 or index >= len(bars):
            return None

        start = index - self.lookback_days + 1
        window = bars[start : index + 1]
        window_volumes = volumes[start : index + 1]
        atr = mean_true_range(bars, index - ATR_WINDOW + 1, index + 1)
        if not math.isfinite(atr) or atr <= 0.0:
            return None

        width = atr * self.bucket_atr
        lows = [b.bar.low for b in window]
        highs = [b.bar.high for b in window]
        low, high = min(lows), max(highs)
        if not (high > low):
            return None
        n_buckets = max(1, int(math.ceil((high - low) / width)))
        edges = tuple(low + i * width for i in range(n_buckets + 1))

        raw = [0.0] * n_buckets
        for bar, vol in zip(window, window_volumes):
            if vol != vol or vol <= 0.0:  # NaN or no trade — contributes nothing
                continue
            # A bar's volume is spread evenly across the buckets its RANGE covers, rather
            # than dumped at its close. A daily bar is not a point: putting a whole day's
            # volume at one price would invent precision the bar does not carry, and would
            # make the profile a close-price histogram wearing a volume label.
            lo_i = max(0, int((bar.bar.low - low) / width))
            hi_i = min(n_buckets - 1, int((bar.bar.high - low) / width))
            span = hi_i - lo_i + 1
            share = vol / span
            for i in range(lo_i, hi_i + 1):
                raw[i] += share

        total = sum(raw)
        if total <= 0.0:
            return None
        return PriceDensity(
            edges=edges,
            mass=tuple(r / total for r in raw),
            bucket_width=width,
            lookback=self.lookback_days,
            bucket_atr=self.bucket_atr,
            n_bars=len(window),
        )


def _quantile(sorted_values: Sequence[float], q: float) -> float:
    """Linear-interpolated quantile of an already-sorted sequence.

    `statistics.quantiles` cuts into n groups and cannot answer an arbitrary q directly;
    this is the smaller thing actually needed."""
    if not sorted_values:
        raise ValueError("quantile of an empty sequence")
    if not 0.0 <= q <= 1.0:
        raise ValueError(f"q must be in [0, 1], got {q}")
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = q * (len(sorted_values) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = pos - lo
    return sorted_values[lo] * (1.0 - frac) + sorted_values[hi] * frac


def realized_volatility(bars: Sequence[TimestampedBar], start: int, end: int) -> float:
    """Stdev of close-to-close log returns over [start, end). Zero if degenerate."""
    if end - start < 3:
        return 0.0
    closes = [b.bar.close for b in bars[start:end]]
    rets = [math.log(b / a) for a, b in zip(closes, closes[1:]) if a > 0 and b > 0]
    if len(rets) < 2 or len(set(rets)) < 2:
        return 0.0
    return statistics.stdev(rets)
