"""S6 — a cumulative SIGNED inventory field over log price (D197).

Not a level set. S1 was a histogram of where volume traded and S5 was a set of discrete
bands; this is one continuous signed field with a value at every price, and that
difference is what the strategies need. D196 found that every strategy it ran read level
*prices* and never the score, which is why S5b came back bit-identical to S5 and was never
actually tested. A field has a magnitude everywhere, so a rule can rank or size on it.

## The construction, fixed by D197 before any run

For every confirmed swing pivot at bar `i`:

- a swing **low** ADDS mass, a swing **high** SUBTRACTS it, so positive net is demand and
  negative net is supply. Two zones that overlap CANCEL, which is information S5 could not
  express: a price where buyers and sellers both turned became two strong levels there and
  one ambiguous reading here.
- mass is a Gaussian in LOG price centred on the pivot extreme, `sigma = cluster_atr x
  ATR(i) / price(i)`. Log units because the fixture runs from about $200 to $150,000 and a
  fixed-dollar width means something different at each end — D187's lesson, and the same
  one that produced a -105% short in D196's first draft.
- the weight is ERA-NORMALISED: `volume(i)` over the trailing `VOL_NORM_BARS` median. Raw
  notional accumulated over a decade would make this a chart of when volume was high, not
  of where price turned.
- a parallel `gross` channel adds the magnitude regardless of sign.

## The erasure destroys, it does not mask

At every bar the body envelope of bars `t-41 .. t-2` is written to ZERO in both channels.
A zone price has recently moved through was weak or was never real, so it does not come
back when the window slides past it — only new swings rebuild it.

The two-bar exclusion is NOT a leak guard; reading bars <= t is already safe. It is what
leaves the map readable at a fresh extreme, and it sets how long a signal lives (about two
bars). Fixed at 2 and never swept: it controls the firing rate directly, and sweeping it
would be tuning the sample size until something works.

## Shrinkage, and the defect it fixes

`tilt = net / (gross + k)`, with `k` the peak per-bucket mass one era-typical swing
deposits — computed from the kernel, not chosen.

Without it the sensor fails in a specific and quiet way. A price whose only mass is kernel
spill from one nearby swing has `net ≈ gross`, so a raw `net / gross` reads ±1.0: maximum
confidence from no information at all. A deadband on the ratio does not help, because a
ratio does not shrink with evidence. D197's census measured the first version of this
constant in the wrong units (a swing's TOTAL mass rather than its per-bucket peak) and
every reading was crushed toward zero; `_shrinkage` exists so that number has one
definition and a test.

## The confirmation lag is where this leaks if you are careless

D173 again, and the reason is unchanged: a pivot at bar `i` cannot be recognised until
`i + k`, because it needs the `k` bars after it. `build_field` deposits a pivot only when
it becomes knowable, and `test_terrain_field.py` asserts that mutating every bar after `t`
leaves the field at `t` byte-identical — paired with a poison test proving that mutation
would otherwise have reached it. D181: a sensor is analytics, and the `DataView` guard
does not cover it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np

from ..data.bars import TimestampedBar
from .terrain import ATR_WINDOW, rolling_mean_true_range
from .terrain_swing import CLUSTER_ATR, SWING_K, _is_swing_bars

BUCKET_LN = 0.002
"""Grid resolution in log price, about 0.2% a bucket — roughly 3,350 buckets over the
daily crypto fixture's range. Fine enough to resolve the narrowest band the sensor can
draw (0.25 ATR) into several buckets, coarse enough that the map stays small."""

ERASE_WINDOW = 40
"""Bars in the erasure envelope. D197's value, fixed there and not swept here."""

ERASE_EXCLUDE = 2
"""Most recent bars held OUT of the envelope. See the module docstring: not a leak guard,
a control on signal lifetime, fixed at 2."""

VOL_NORM_BARS = 90
"""Trailing window for the volume normalisation. One era-typical swing is 1.0 whether it
happened in 2015 or 2024."""

SQRT_TWO_PI = math.sqrt(2.0 * math.pi)


def _shrinkage(sigma_ln: float) -> float:
    """The pseudo-count `k`: peak per-bucket mass of one era-typical swing.

    A unit-mass Gaussian of width `sigma_ln` in log space puts `BUCKET_LN / (sigma x
    sqrt(2*pi))` into the bucket at its centre. Using that as the pseudo-count means one
    typical swing's worth of evidence halves the shrinkage, which is what "one swing is
    one unit of evidence" should mean. Derived, not chosen — there is no free parameter
    here and D197 turns on that being true."""
    return BUCKET_LN / (sigma_ln * SQRT_TWO_PI)


@dataclass(frozen=True)
class Swing:
    """One confirmed pivot, as of the bar it becomes knowable."""

    index: int
    """Bar the pivot sits ON."""
    confirmed_at: int
    """`index + k` — the first bar that may use it (D173)."""
    sign: int
    """+1 from a swing high (supply, subtracts), -1 from a swing low (demand, adds)."""
    price: float
    """The pivot EXTREME: the high for a swing high, the low for a swing low."""
    weight: float
    """Era-normalised volume. One era-typical swing is 1.0."""
    sigma_ln: float
    """Kernel width in log units, `cluster_atr x ATR(i) / price(i)`."""


@dataclass(frozen=True)
class FieldParams:
    k: int
    cluster_atr: float
    atr_window: int = ATR_WINDOW
    erase_window: int = ERASE_WINDOW
    erase_exclude: int = ERASE_EXCLUDE
    vol_norm_bars: int = VOL_NORM_BARS
    bucket_ln: float = BUCKET_LN
    erase: bool = True
    """Whether the destroy step runs at all (D201).

    False leaves the field as a pure cumulative signed map. That is NOT a legal setting for
    the boundary rule — with nothing erased, price is never outside the envelope and the
    rule never fires — but it is legal, and interesting, for the imbalance formulation,
    which reads the whole field rather than the bucket at price.

    D197's census found the erasure destroys 70% of pivots and keeps only wick extremes, an
    unintended selection doing more work than the volume weighting. This flag is what lets
    a run separate the erasure from the map, which nothing in D197-D199 could do."""

    def __post_init__(self) -> None:
        # Same enforcement, and the same reason, as SwingSupplyDemandSensor: a value
        # outside the pre-registered set is an unregistered search.
        if self.k not in SWING_K:
            raise ValueError(
                f"k must be one of {SWING_K}, got {self.k}. D173 fixed this set; a third "
                "value is an unregistered search."
            )
        if self.cluster_atr not in CLUSTER_ATR:
            raise ValueError(
                f"cluster_atr must be one of {CLUSTER_ATR}, got {self.cluster_atr}. "
                "The spec fixes this set; a third value is an unregistered search."
            )
        if self.erase and self.erase_exclude < 1:
            raise ValueError(
                f"erase_exclude={self.erase_exclude} would put the current bar inside the "
                "erasure envelope, which makes the field identically zero at every price "
                "the strategy ever reads."
            )


@dataclass(frozen=True)
class Grid:
    """The log-price axis the field lives on."""

    ln_min: float
    bucket_ln: float
    n: int

    def bucket(self, price: float) -> int:
        return int((math.log(price) - self.ln_min) / self.bucket_ln)

    def centres(self) -> np.ndarray:
        return self.ln_min + self.bucket_ln * np.arange(self.n)


def build_grid(bars: Sequence[TimestampedBar], bucket_ln: float = BUCKET_LN) -> Grid:
    """A log-price axis spanning the series with a little headroom either side."""
    lo = math.log(min(b.bar.low for b in bars)) - 0.05
    hi = math.log(max(b.bar.high for b in bars)) + 0.05
    return Grid(lo, bucket_ln, int((hi - lo) / bucket_ln) + 1)


def confirmed_swings(
    bars: Sequence[TimestampedBar], volumes: Sequence[float], params: FieldParams
) -> list[Swing]:
    """Every pivot in the series, stamped with the bar it becomes knowable on.

    Computed once and reused across all null draws — a null shuffles a swing's PRICE and
    nothing else, so the detection, the ATR and the volume normalisation are invariant."""
    if len(volumes) != len(bars):
        raise ValueError(
            f"volumes has {len(volumes)} entries for {len(bars)} bars. A misaligned volume "
            "series silently attributes one bar's activity to another (D187)."
        )
    atr = rolling_mean_true_range(bars, params.atr_window)
    out: list[Swing] = []
    for i in range(params.k, len(bars) - params.k):
        a = atr[i]
        if not (a == a) or a <= 0.0:  # NaN before warm-up, and NaN fails every comparison
            continue
        for sign in (1, -1):
            if not _is_swing_bars(bars, i, params.k, sign):
                continue
            price = bars[i].bar.high if sign > 0 else bars[i].bar.low
            if price <= 0.0:
                continue
            lo = max(0, i - params.vol_norm_bars + 1)
            scale = float(np.median(volumes[lo : i + 1]))
            if not (scale > 0.0):
                continue
            weight = float(volumes[i]) / scale
            if not (weight > 0.0):
                continue
            out.append(
                Swing(
                    index=i,
                    confirmed_at=i + params.k,
                    sign=sign,
                    price=price,
                    weight=weight,
                    sigma_ln=params.cluster_atr * a / price,
                )
            )
    return out


def _deposit(
    net: np.ndarray, gross: np.ndarray, grid: Grid, swing: Swing, centres: np.ndarray
) -> None:
    """Add one swing's kernel. Truncated at 3 sigma and RENORMALISED so the mass actually
    deposited is exactly `weight` — an untruncated tail would leak a few percent and make
    the shrinkage constant wrong by that much."""
    span = max(1, int(3.0 * swing.sigma_ln / grid.bucket_ln))
    c = grid.bucket(swing.price)
    lo, hi = max(0, c - span), min(grid.n - 1, c + span)
    if hi < lo:
        return
    idx = slice(lo, hi + 1)
    k = np.exp(-0.5 * ((centres[idx] - math.log(swing.price)) / swing.sigma_ln) ** 2)
    total = k.sum()
    if total <= 0.0:
        return
    k = k * (swing.weight / total)
    net[idx] += -k if swing.sign > 0 else k
    gross[idx] += k


def erasure_bounds(
    bars: Sequence[TimestampedBar], params: FieldParams
) -> tuple[np.ndarray, np.ndarray]:
    """`(lo, hi)` body envelope per bar over `t-41 .. t-2`, NaN where undefined.

    Reads only bars at or before `t - erase_exclude`, which the look-ahead test asserts
    rather than trusting this docstring."""
    n = len(bars)
    body_hi = np.array([max(b.bar.open, b.bar.close) for b in bars], dtype=float)
    body_lo = np.array([min(b.bar.open, b.bar.close) for b in bars], dtype=float)
    lo = np.full(n, np.nan)
    hi = np.full(n, np.nan)
    for t in range(n):
        z = t - params.erase_exclude
        a = max(0, z - params.erase_window + 1)
        if z < a:
            continue
        lo[t] = body_lo[a : z + 1].min()
        hi[t] = body_hi[a : z + 1].max()
    return lo, hi


@dataclass(frozen=True)
class Signal:
    """One bar on which the field is readable at the closing price."""

    index: int
    """The bar whose CLOSE fired. Entry is the next bar's open."""
    direction: int
    """+1 price broke ABOVE the envelope, -1 below."""
    price: float
    tilt: float
    gross: float
    virgin: bool
    """No mass at all at this price — the field is silent, not neutral."""


def _walk_field(
    bars: Sequence[TimestampedBar],
    swings: Sequence[Swing],
    params: FieldParams,
    grid: Grid,
    upto: int,
):
    """Deposit-then-destroy, bar by bar, yielding the state after each bar.

    One walk shared by `field_signals` and `build_field` so the two can never drift: a
    diagnostic that showed a different field from the one the strategy traded would be
    worse than no diagnostic."""
    centres = grid.centres()
    net = np.zeros(grid.n)
    gross = np.zeros(grid.n)
    lo_b, hi_b = erasure_bounds(bars, params)

    by_confirm: dict[int, list[Swing]] = {}
    for s in swings:
        by_confirm.setdefault(s.confirmed_at, []).append(s)

    for t in range(min(upto + 1, len(bars))):
        for s in by_confirm.get(t, ()):  # D173: only what is knowable now
            _deposit(net, gross, grid, s, centres)

        lo, hi = lo_b[t], hi_b[t]
        if params.erase and lo == lo:  # NaN while the envelope is undefined
            a, z = grid.bucket(lo), grid.bucket(hi)
            net[a : z + 1] = 0.0  # destroy, not mask
            gross[a : z + 1] = 0.0
        yield t, net, gross, lo, hi


def build_field(
    bars: Sequence[TimestampedBar],
    swings: Sequence[Swing],
    params: FieldParams,
    upto: int,
    grid: Grid | None = None,
) -> tuple[np.ndarray, np.ndarray, Grid]:
    """`(net, gross, grid)` exactly as they stand after bar `upto`.

    For tests and diagnostics. Nothing in the strategy path calls this — the strategy
    consumes `field_signals` — but a positive control has to be able to look at the map
    rather than infer it from the trades it produced."""
    grid = grid or build_grid(bars, params.bucket_ln)
    net = gross = None
    for _, net, gross, _, _ in _walk_field(bars, swings, params, grid, upto):
        pass
    if net is None or gross is None:
        return np.zeros(grid.n), np.zeros(grid.n), grid
    return net.copy(), gross.copy(), grid


def field_signals(
    bars: Sequence[TimestampedBar],
    swings: Sequence[Swing],
    params: FieldParams,
    grid: Grid | None = None,
) -> list[Signal]:
    """Every bar whose close sits outside the erasure envelope, with the field read there.

    This is the whole sensor as the strategy sees it."""
    grid = grid or build_grid(bars, params.bucket_ln)
    shrink = _shrinkage(typical_sigma(swings, params))
    out: list[Signal] = []
    for t, net, gross, lo, hi in _walk_field(bars, swings, params, grid, len(bars) - 1):
        if not (lo == lo):
            continue
        close = bars[t].bar.close
        if lo <= close <= hi:
            continue
        c = grid.bucket(close)
        if not (0 <= c < grid.n):
            continue
        g = float(gross[c])
        out.append(
            Signal(
                index=t,
                direction=1 if close > hi else -1,
                price=close,
                tilt=float(net[c]) / (g + shrink),
                gross=g,
                virgin=g <= 1e-12,
            )
        )
    return out


def typical_sigma(swings: Sequence[Swing], params: FieldParams) -> float:
    """The kernel width of an era-typical swing — the median across the series.

    D197 defines the pseudo-count from "one era-typical swing", which is ONE number, not a
    per-price lookup. A first draft here used the width of the nearest swing to each read;
    that is a different and unregistered estimator, it made the shrinkage depend on where
    price happened to be, and it was quadratic. Median, computed once.

    Invariant across null draws: shuffling moves a swing's PRICE and leaves `sigma_ln`
    alone, so the real and null arms shrink by exactly the same constant."""
    if not swings:
        return params.cluster_atr * 0.04  # ~1 ATR on this fixture; only for empty series
    return float(np.median([s.sigma_ln for s in swings]))


CONFIRM_WINDOW = 20
"""Bars a qualifying signal waits for a second, distinct approach (D198). Fixed at the
value proposed and not swept — it controls the trade count directly."""


def qualifying(signals: Sequence[Signal], threshold: float = 0.0) -> list[Signal]:
    """The signals D197's reversal rule would actually trade: not virgin, correctly
    oriented for the fade — break up into net supply, or break down into net demand."""
    out = []
    for s in signals:
        if s.virgin:
            continue
        if s.direction > 0 and s.tilt < -threshold:
            out.append(s)
        elif s.direction < 0 and s.tilt > threshold:
            out.append(s)
    return out


@dataclass(frozen=True)
class ConfirmationSplit:
    """D198's two books plus full accounting, so no signal can vanish unnoticed.

    Every qualifying signal lands in exactly one of four roles and the four sum to
    `n_qualifying`. That is asserted by test rather than trusted, because a first draft
    scanned each signal independently and put the confirming signal in BOTH books at
    once — the counts still added up, which is precisely why the count-only property test
    passed while the bookkeeping was wrong."""

    confirmed: tuple[Signal, ...]
    """The CONFIRMING signals — entries are taken on the second sighting."""
    unconfirmed: tuple[Signal, ...]
    """Aged out with no second approach. A DIAGNOSTIC, never a strategy: this is only
    knowable `window` bars later, so trading it at its own bar reads the future."""
    n_triggers: int
    """Signals that were confirmed by a later one. They set up an entry, they are not one."""
    n_absorbed: int
    """Fired while an earlier signal was still pending and did not confirm it — the same
    excursion still running. The census measured these at 61% of naive 'confirmations'."""
    n_qualifying: int

    def accounts(self) -> bool:
        return (
            len(self.confirmed) + len(self.unconfirmed) + self.n_triggers + self.n_absorbed
            == self.n_qualifying
        )


def split_by_confirmation(
    bars: Sequence[TimestampedBar],
    signals: Sequence[Signal],
    params: FieldParams,
    window: int = CONFIRM_WINDOW,
    threshold: float = 0.0,
) -> ConfirmationSplit:
    """D198's two-approach rule, as the pending walk the document specifies.

    A signal at `t1` is CONFIRMED by a later same-direction qualifying signal at `t2` when
    `t2 - t1 <= window` AND at least one bar strictly between them closes INSIDE the
    erasure envelope. The entry is taken on `t2` — the second sighting — and both signals
    are then consumed.

    Requiring the return inside the envelope is the whole rule. Without it the census
    measured 86% of signals "confirmed", 61% of them on the very next bar, because S6
    keeps firing while one excursion is still running: that is an entry delay, not a
    second approach. This is `terrain_nulls.level_reactions`' first-bar-of-an-approach
    convention, reused rather than re-invented.

    **The unconfirmed book is a DIAGNOSTIC, not a strategy** — see `ConfirmationSplit`."""
    qual = qualifying(signals, threshold)
    lo_b, hi_b = erasure_bounds(bars, params)
    inside = [
        bool(lo_b[t] == lo_b[t] and lo_b[t] <= bars[t].bar.close <= hi_b[t])
        for t in range(len(bars))
    ]

    def returned_home(a: int, b: int) -> bool:
        return any(inside[u] for u in range(a + 1, b))

    pending: dict[int, Signal] = {}
    confirmed: list[Signal] = []
    unconfirmed: list[Signal] = []
    triggers = absorbed = 0

    for s in qual:
        held = pending.get(s.direction)
        if held is None:
            pending[s.direction] = s
            continue
        if s.index - held.index > window:  # aged out; this one starts a new wait
            unconfirmed.append(held)
            pending[s.direction] = s
            continue
        if returned_home(held.index, s.index):
            confirmed.append(s)
            triggers += 1
            del pending[s.direction]
        else:
            absorbed += 1  # same excursion still running

    unconfirmed.extend(pending.values())
    return ConfirmationSplit(
        confirmed=tuple(confirmed),
        unconfirmed=tuple(unconfirmed),
        n_triggers=triggers,
        n_absorbed=absorbed,
        n_qualifying=len(qual),
    )


def field_imbalance(
    bars: Sequence[TimestampedBar],
    swings: Sequence[Swing],
    params: FieldParams,
    grid: Grid | None = None,
) -> list[float]:
    """Demand below current price against supply above it, per bar (D201).

        D_below   = sum of POSITIVE net over buckets below the close
        S_above   = sum of NEGATIVE net (as a magnitude) over buckets above it
        imbalance = (D_below - S_above) / (D_below + S_above)        in [-1, +1]

    Positive means demand underneath dominates overhead supply; negative the reverse. NaN
    only while the field is still empty, which is the warm-up and nothing else.

    ## Why this is a different claim from the closed reversal line

    D200 closed the boundary-fade rule. That rule read the single bucket **at** the current
    price, which the erasure geometry forced: it could only speak on the ~20% of bars where
    price sat outside the envelope, and only ever about reversal at a boundary. This reads
    the **whole field on both sides** and has an answer on every bar. A map can be locally
    uninformative and still carry aggregate skew, so D197's verdict on placement does not
    settle it — though it is the same map, and that prior is not favourable.

    Note what is deliberately excluded: the bucket at the close itself contributes to
    neither sum. That is what makes the reading independent of the erasure's two-bar trick
    rather than dependent on it.

    Shares `_walk_field` with `field_signals` and `build_field`, so the field this reads is
    by construction the same field those trade."""
    grid = grid or build_grid(bars, params.bucket_ln)
    out: list[float] = []
    for t, net, _gross, _lo, _hi in _walk_field(
        bars, swings, params, grid, len(bars) - 1
    ):
        c = grid.bucket(bars[t].bar.close)
        if not (0 <= c < grid.n):
            out.append(float("nan"))
            continue
        below = net[:c]
        above = net[c + 1 :]
        demand_below = float(below[below > 0.0].sum())
        supply_above = float(-above[above < 0.0].sum())
        total = demand_below + supply_above
        out.append((demand_below - supply_above) / total if total > 0.0 else float("nan"))
    return out
