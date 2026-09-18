"""The short side of the breakout family: a regime-gated breakdown book (D169).

**THESIS LABEL (D38/D82/D117): directional and beta-loaded, like its long sibling, and
equally NOT part of this project's market-neutral thesis.** It is short or flat on a
single high-beta instrument. Its honest benchmark is not the risk-free rate and not
buy-and-hold either — it is the question "does this pay for itself in the regimes it
claims, and does it diversify the long book?", which is what the regime table and the
correlation table answer.

What this module adds on top of `breakout_study`, which it reuses unmodified for the
actual running of variants:

1. **Short variants**, with parameters NOT mirrored from the long side. Bear legs are
   faster and shorter and bear rallies are violent, so the sweep is its own
   ({10,20,30,40} x {3,5,10} against the long book's {20,30,40,55} x {5,10,20}) and is
   counted separately for multiplicity.
2. **Regime slicing**, which is the HEADLINE table rather than an appendix. A short book
   that is flat through a bull sample and profitable through 2018 and 2022 is a success;
   judging it on full-sample Sharpe would call that a failure.
3. **Correlation against the long book**, computed over the full cycle INCLUDING the
   periods either book is flat — because the diversification claim is about the combined
   equity curve, and flat periods are exactly when one book is supposed to be carrying
   the other.
4. **An exposure-matched random-SHORT-entry null**, which is the primary verdict. Any
   long-biased rule looks good in 2018; the question is whether THESE entries beat
   randomly-placed shorts of the same count and duration.

**The stop is close-based, and that is a stated limitation, not a detail (D169).** See
`ChannelStopExit`: the engine has no intrabar stop execution, so the squeeze tail is not
truncated by construction. This module measures the shortfall (`gap_through_cost`) rather
than assuming it away.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np

from ..analytics.metrics import max_drawdown_from_returns, mid_rank_percentile, sharpe
from ..data.bars import TimestampedBar
from . import breakout_study as bs

# --------------------------------------------------------------------------- variants

SHORT_N_ENTRY: tuple[int, ...] = (10, 20, 30, 40)
"""Deliberately faster than the long book's (20, 30, 40, 55). Bear legs are shorter and
steeper, so a 55-bar breakdown would mostly fire after the move was over. Different
optimal parameters from the long side is the EXPECTED finding, not a red flag."""

SHORT_N_EXIT: tuple[int, ...] = (3, 5, 10)
"""Faster than the long book's (5, 10, 20). Bear-market rallies are violent and a short
that waits for a 20-bar high to confirm has already given the move back."""

ENSEMBLE_MIN_BARS = 252
"""Warm-up before the long/short ensemble will weight anything (D181).

The weights use an EXPANDING window — every return from the start of the out-of-sample
period up to the previous bar — rather than a fixed trailing one, and this constant is only
the minimum history required before the first weight is produced. 252 is
`BreakoutStudyConfig.train_size`, an already-pinned constant.

**Why expanding rather than trailing.** The short book is regime-gated and sits flat on
~85% of bars, so it is routinely flat for an entire fixed window and has no volatility to
invert. A 63-bar window fell back to equal weight on 75% of BTC's bars — an "equal-vol"
book that was equal-CAPITAL three times out of four, which is precisely what `EnsembleResult`
says the construction exists to avoid. Any fixed window shorter than the short book's flat
spells has the same problem, and the length of those spells is not something to guess.

Choosing the window by which value produced the best combined Sharpe would be a search, and
the ensemble has no multiplicity budget. The expanding window is chosen on the stated
principle that an allocator sizes strategies by their long-run risk, not last quarter's —
especially when one of them is intermittent by design."""

SHORT_BASELINE_N_ENTRY, SHORT_BASELINE_N_EXIT = 20, 5

TIME_STOP_BARS: tuple[int, ...] = (3, 5)
"""A short not in profit within a few bars is carrying squeeze risk for nothing. Two
candidate values only, stated in the brief, and not tuned beyond them."""

SMA_GATE_WINDOW = 200

SHORT_INVERSE_VOL = {
    "type": "inverse_vol_weight",
    "target_annual_vol": 0.40,
    "vol_window": 20,
    "periods_per_year": 365.0,
    "max_weight": 1.0,
    "rebalance": "at_entry",
}
"""Same sizing brick as the long book, capped at 1.0 — which IS the per-trade position
cap the brief requires, enforced in `BreakoutStrategy.__post_init__` rather than trusted.
Note vol expands in crashes, so vol targeting automatically de-sizes as a move matures.
That is intended behaviour and is not to be "fixed"."""


STOP_FAMILIES: tuple[tuple[str, list[dict[str, Any]]], ...] = (
    ("entry_channel", [{"type": "channel_stop"}]),
    ("trail_5", [{"type": "trailing_channel_stop", "n_bars": 5}]),
    ("trail_10", [{"type": "trailing_channel_stop", "n_bars": 10}]),
    ("trail_20", [{"type": "trailing_channel_stop", "n_bars": 20}]),
    ("atr_2", [{"type": "atr_stop", "multiple": 2.0, "window": 20}]),
    ("atr_3", [{"type": "atr_stop", "multiple": 3.0, "window": 20}]),
    ("chandelier_3", [{"type": "chandelier_stop", "multiple": 3.0, "window": 20}]),
    ("swing_k2", [{"type": "swing_structure_stop", "k": 2}]),
    ("swing_k3", [{"type": "swing_structure_stop", "k": 3}]),
)
"""The stop families swept on the fixed baseline entry/exit parameters (D171).

Chosen to separate two questions that the entry-channel stop conflates: HOW FAR the stop
sits (atr_2 vs atr_3, both fixed at entry) and WHETHER IT FOLLOWS the trade (trail_* and
chandelier_3, which ratchet). `entry_channel` is the incumbent and the control — the wide
stop D170 measured binding once in 915 armed bars.

Seven families, one sweep, counted as its own trial series. Everything else about the
strategy is held at the baseline, so a difference between rows is attributable to the
stop and to nothing else."""


def short_config(n_entry: int, n_exit: int, time_stop: int | None = None) -> dict[str, Any]:
    """A short config with the non-optional tail discipline always present.

    There is no argument that removes the stop. `BreakoutStrategy` refuses to construct
    a short without one, so a config produced here is the only kind that runs."""
    exit_rules: list[dict[str, Any]] = [{"type": "channel_stop"}]
    if time_stop is not None:
        exit_rules.append({"type": "time_stop", "n_bars": time_stop})
    return bs.breakout_config(
        n_entry=n_entry,
        n_exit=n_exit,
        weight_source=SHORT_INVERSE_VOL,
        filters=[{"type": "trend_gate", "sma_window": SMA_GATE_WINDOW, "direction": "short"}],
        direction="short",
        exit_rules=exit_rules,
    )


def short_variants() -> list[bs.Variant]:
    """The short book's own sweep, counted separately from the long book's."""
    variants = [
        bs.Variant(
            f"short_{n_entry}_{n_exit}", "plateau",
            fixed_config=short_config(n_entry, n_exit),
        )
        for n_entry in SHORT_N_ENTRY
        for n_exit in SHORT_N_EXIT
        if n_exit <= n_entry
    ]
    variants += [
        bs.Variant(
            f"short_timestop_{n}", "exit",
            fixed_config=short_config(SHORT_BASELINE_N_ENTRY, SHORT_BASELINE_N_EXIT, time_stop=n),
        )
        for n in TIME_STOP_BARS
    ]
    # The regime gate is the short book's defining feature, so its counterfactual is a
    # variant rather than a footnote: the same rule with the gate removed.
    ungated = bs.breakout_config(
        n_entry=SHORT_BASELINE_N_ENTRY,
        n_exit=SHORT_BASELINE_N_EXIT,
        weight_source=SHORT_INVERSE_VOL,
        filters=[],
        direction="short",
        exit_rules=[{"type": "channel_stop"}],
    )
    variants.append(bs.Variant("short_no_regime_gate", "counterfactual", fixed_config=ungated))

    # The stop sweep (D171). Baseline entry/exit throughout; only the stop changes.
    for label, rules in STOP_FAMILIES:
        if label == "entry_channel":
            continue  # that IS the baseline variant, already in the list above
        variants.append(
            bs.Variant(
                f"stop_{label}", "stop",
                fixed_config=bs.breakout_config(
                    n_entry=SHORT_BASELINE_N_ENTRY,
                    n_exit=SHORT_BASELINE_N_EXIT,
                    weight_source=SHORT_INVERSE_VOL,
                    filters=[
                        {"type": "trend_gate", "sma_window": SMA_GATE_WINDOW,
                         "direction": "short"}
                    ],
                    direction="short",
                    exit_rules=rules,
                ),
            )
        )
    # The structure GATE is a separate hypothesis (H2 in D173) from the structure STOP,
    # so it gets its own variants rather than being folded into the stop sweep: the
    # baseline stop is held fixed and only the gate changes.
    for k in (2, 3):
        variants.append(
            bs.Variant(
                f"gate_swing_k{k}", "gate",
                fixed_config=bs.breakout_config(
                    n_entry=SHORT_BASELINE_N_ENTRY,
                    n_exit=SHORT_BASELINE_N_EXIT,
                    weight_source=SHORT_INVERSE_VOL,
                    filters=[
                        {"type": "trend_gate", "sma_window": SMA_GATE_WINDOW,
                         "direction": "short"},
                        {"type": "swing_structure_gate", "k": k, "direction": "short"},
                    ],
                    direction="short",
                    exit_rules=[{"type": "channel_stop"}],
                ),
            )
        )
    # The cross-book test (D178): E1 was developed and judged entirely on the LONG book.
    # It is NOT a stop — it bounds duration in a window, not loss — so on a short it must
    # ride alongside the incumbent channel stop, which is also what the baseline carries.
    # The delta against the baseline therefore prices E1 alone.
    for k in (2, 3):
        variants.append(
            bs.Variant(
                f"exit_e1_k{k}", "exit",
                fixed_config=bs.breakout_config(
                    n_entry=SHORT_BASELINE_N_ENTRY,
                    n_exit=SHORT_BASELINE_N_EXIT,
                    weight_source=SHORT_INVERSE_VOL,
                    filters=[{"type": "trend_gate", "sma_window": SMA_GATE_WINDOW,
                              "direction": "short"}],
                    direction="short",
                    exit_rules=[{"type": "channel_stop"},
                                {"type": "failed_breakout", "k": k}],
                ),
            )
        )
    return variants


SHORT_BASELINE = f"short_{SHORT_BASELINE_N_ENTRY}_{SHORT_BASELINE_N_EXIT}"


# ---------------------------------------------------------------------------- regimes


def regime_labels(
    bars: Sequence[TimestampedBar], window: int = SMA_GATE_WINDOW
) -> list[str | None]:
    """Ex-post bull / bear / chop label per bar, from the SMA(`window`) state.

    - **bull**  close above the average AND the average rising
    - **bear**  close below the average AND the average falling
    - **chop**  anything else — price and trend disagreeing

    These are EX-POST labels used only to slice results for reading. They are not
    available to the strategy and never gate a trade; the strategy's own gate is the
    simple close-vs-SMA test inside `TrendGateFilter`. Bars before the average exists
    are labelled None and excluded from every regime table rather than lumped into one.
    """
    labels: list[str | None] = [None] * len(bars)
    for i in range(window, len(bars)):
        sma_now = statistics.fmean(bars[j].bar.close for j in range(i - window, i))
        sma_prev = statistics.fmean(bars[j].bar.close for j in range(i - window - 1, i - 1))
        close = bars[i].bar.close
        rising = sma_now > sma_prev
        if close > sma_now and rising:
            labels[i] = "bull"
        elif close < sma_now and not rising:
            labels[i] = "bear"
        else:
            labels[i] = "chop"
    return labels


@dataclass(frozen=True)
class RegimeSlice:
    regime: str
    n_bars: int
    share_of_sample: float
    total_return: float
    """Compounded return of the strategy over the bars in this regime only. Not
    annualised: these are disjoint, non-contiguous stretches, and annualising a
    scattered collection of bars invents a rate that was never experienced."""
    mean_daily_return: float
    sharpe_daily: float
    exposure: float
    """Fraction of this regime's bars on which the book held a position."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "regime": self.regime,
            "n_bars": self.n_bars,
            "share_of_sample": self.share_of_sample,
            "total_return": self.total_return,
            "mean_daily_return": self.mean_daily_return,
            "sharpe_daily": self.sharpe_daily,
            "exposure": self.exposure,
        }


def slice_by_regime(
    returns: Sequence[float],
    labels: Sequence[str | None],
    in_market: Sequence[bool],
) -> list[RegimeSlice]:
    """`returns[i]` is the return realised over bar i; `labels` and `in_market` align to
    the same bars. All three must be the same length."""
    if not (len(returns) == len(labels) == len(in_market)):
        raise ValueError(
            f"length mismatch: {len(returns)} returns, {len(labels)} labels, "
            f"{len(in_market)} exposure flags"
        )
    labelled = sum(1 for label in labels if label is not None)
    out: list[RegimeSlice] = []
    for regime in ("bull", "bear", "chop"):
        idx = [i for i, label in enumerate(labels) if label == regime]
        if not idx:
            continue
        segment = [returns[i] for i in idx]
        compounded = 1.0
        for r in segment:
            compounded *= 1.0 + r
        out.append(
            RegimeSlice(
                regime=regime,
                n_bars=len(idx),
                share_of_sample=len(idx) / labelled if labelled else 0.0,
                total_return=compounded - 1.0,
                mean_daily_return=statistics.fmean(segment),
                sharpe_daily=(
                    statistics.fmean(segment) / statistics.stdev(segment)
                    if len(segment) > 1 and statistics.stdev(segment) > 0
                    else 0.0
                ),
                exposure=sum(1 for i in idx if in_market[i]) / len(idx),
            )
        )
    return out


# ------------------------------------------------------------------------ correlation


@dataclass(frozen=True)
class EnsembleResult:
    correlation: float
    """Long-book vs short-book daily return correlation over the shared span, INCLUDING
    bars either book was flat. Excluding flat bars would measure "how do they behave when
    both happen to be trading", which is not the diversification question — the whole
    point is that the short book wakes when the long book sleeps."""
    n_bars: int
    """Bars actually SCORED — the out-of-sample span less the weighting warm-up."""
    n_warmup_bars: int
    """Leading bars dropped because no trailing window existed to weight them (D181)."""
    n_fallback_bars: int
    """Scored bars where a leg was flat for its entire history to that point, so inverse
    vol was undefined and the pair fell back to 50/50. Reported rather than hidden: if this
    is a large share of the span, the weighting is not doing what its name says. A 63-bar
    trailing window hit 75% here, which is how the scheme came to be changed (D181)."""
    mean_long_weight: float
    """Average share of the combined book carried by the LONG leg.

    Below 0.5 means the majority of the risk budget sits on the short leg — a book that is
    flat on ~85% of bars and loses money. Inverse-vol weighting reads a flat book as
    low-risk, when what it actually is, is absent. This is a known flaw in the equal-vol
    construction (D181) and it is surfaced on every result so it cannot be read past."""
    long_sharpe: float
    short_sharpe: float
    combined_sharpe: float
    """Equal VOL weight, not equal capital: the two books have very different
    volatilities, so equal capital would just be the long book with noise added. The vol
    is TRAILING, measured on a window ending at the previous bar (D44/D181) — an earlier
    version used whole-sample vol, which knew each leg's future."""
    long_max_drawdown: float
    short_max_drawdown: float
    """Carried so all three arms can be quoted on the SAME span. The drawdown comparison
    is the one D172 found disagrees with the Sharpe comparison, so leaving one arm out of
    it invites the reader to fill the gap with a number measured over a different span."""
    combined_max_drawdown: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "correlation": self.correlation,
            "n_bars": self.n_bars,
            "n_warmup_bars": self.n_warmup_bars,
            "n_fallback_bars": self.n_fallback_bars,
            "mean_long_weight": self.mean_long_weight,
            "long_sharpe": self.long_sharpe,
            "short_sharpe": self.short_sharpe,
            "combined_sharpe": self.combined_sharpe,
            "long_max_drawdown": self.long_max_drawdown,
            "short_max_drawdown": self.short_max_drawdown,
            "combined_max_drawdown": self.combined_max_drawdown,
        }


def _max_drawdown(returns: Sequence[float]) -> float:
    """Delegated to `analytics.metrics` (D542). Positive fraction, unchanged.

    This body used to be `worst = max(worst, 1.0 - nav / peak)`, which is the same
    quantity as the canonical `(peak - nav) / peak` and NOT the same float: measured on
    605 curves, 322 disagree at one ULP (worst 1.11e-16). Every number in
    `data/breakdown_study_summary.json` therefore moves in its last bit and no further —
    recorded in D542 rather than absorbed quietly, because a moved published number with
    no written reason is indistinguishable from a typo.
    """
    return max_drawdown_from_returns(returns)


class _RunningVol:
    """Welford's online variance, so an EXPANDING-window standard deviation costs O(1) per
    bar instead of O(n).

    The naive version — re-running `statistics.stdev` over a growing slice — is O(n²) and
    turns the 62-symbol universe run into hundreds of millions of operations. Welford is
    also the numerically stable formulation, which the sum-of-squares shortcut is not."""

    __slots__ = ("n", "_mean", "_m2", "_first", "_all_same")

    def __init__(self) -> None:
        self.n = 0
        self._mean = 0.0
        self._m2 = 0.0
        self._first: float | None = None
        self._all_same = True

    def add(self, x: float) -> None:
        if self._first is None:
            self._first = x
        elif x != self._first:
            self._all_same = False
        self.n += 1
        delta = x - self._mean
        self._mean += delta / self.n
        self._m2 += delta * (x - self._mean)

    @property
    def sd(self) -> float:
        # A book flat for its entire history has no volatility to invert, and floating
        # point on a constant series can leave m2 at a tiny non-zero value. The identity
        # check is exact where the arithmetic is not.
        if self._all_same or self.n < 2:
            return 0.0
        return math.sqrt(self._m2 / (self.n - 1))


def _check_pair(
    long_returns: Sequence[float], short_returns: Sequence[float], min_bars: int
) -> None:
    """Both legs must cover the SAME bars, and there must be enough history to weight.

    The previous implementation took `min(len(a), len(b))` and sliced from the end. Today
    both books produce identical out-of-sample spans, so that was a no-op — and a silent
    one, which would have quietly misaligned dates the first time it stopped being true.
    Raising is the whole value of the check."""
    if min_bars < 2:
        raise ValueError(f"min_bars must be at least 2, got {min_bars}")
    if len(long_returns) != len(short_returns):
        raise ValueError(
            f"the two books cover different spans — long has {len(long_returns)} returns "
            f"and short has {len(short_returns)}. They must be aligned bar-for-bar before "
            "they can be combined; truncating one to fit the other would silently shift "
            "the pair out of alignment."
        )
    if len(long_returns) <= min_bars:
        raise ValueError(
            f"{len(long_returns)} returns is not enough to weight after a {min_bars}-bar "
            f"warm-up — at least {min_bars + 1} are needed. Falling back to whole-sample "
            "volatility here is what made the weights look-ahead in the first place, so "
            "this raises instead."
        )


def _inverse_vol_weights(
    long_returns: Sequence[float], short_returns: Sequence[float], min_bars: int
) -> tuple[list[tuple[float, float]], int]:
    """Per-bar inverse-volatility weights using only information available BEFORE the bar.

    At bar `t` the weights come from each leg's realized vol over `[0, t)` — everything up
    to and EXCLUDING the current bar, so the window ends at the previous bar in the sense
    D44 pins and `InverseVolatilityWeight` already applies for strategy-level sizing. The
    ensemble layer used to compute one pair of weights from the WHOLE out-of-sample series
    and apply them from the first bar, which handed the calmer leg exactly the right weight
    in advance (D181).

    Expanding rather than fixed-width: see `ENSEMBLE_MIN_BARS`. The short book is flat on
    ~85% of bars, so a fixed window short enough to be responsive is routinely all-flat and
    has no volatility to invert.

    The first `min_bars` bars are dropped rather than given a placeholder weight — equal
    weight for a warm-up year is a number nobody chose, and it would sit in the series
    looking like a measurement.

    Returns the weights for bars `min_bars..n-1` and a count of the bars that still had to
    fall back to 50/50 because a leg was flat for its entire history to that point."""
    weights: list[tuple[float, float]] = []
    fallback = 0
    vol_a, vol_b = _RunningVol(), _RunningVol()
    for t in range(min_bars):
        vol_a.add(long_returns[t])
        vol_b.add(short_returns[t])
    for t in range(min_bars, len(long_returns)):
        sd_a, sd_b = vol_a.sd, vol_b.sd  # state covers [0, t) — bar t not yet added
        if sd_a > 0.0 and sd_b > 0.0:
            # Normalised so the pair sums to 1 and the combined book is comparable in
            # scale to each component rather than quietly levered.
            wa, wb = 1.0 / sd_a, 1.0 / sd_b
            total = wa + wb
            weights.append((wa / total, wb / total))
        else:
            # A book flat for its whole history has no volatility to invert. Equal weight
            # is the only choice that does not divide by zero, and it is counted so the
            # report can say how often it happened rather than hiding it.
            fallback += 1
            weights.append((0.5, 0.5))
        vol_a.add(long_returns[t])
        vol_b.add(short_returns[t])
    return weights, fallback


def combined_series(
    long_returns: Sequence[float],
    short_returns: Sequence[float],
    min_bars: int = ENSEMBLE_MIN_BARS,
) -> list[float]:
    """The inverse-vol-weighted combined book's return series, warm-up excluded.

    Split out from `combine_books` so the same series that produces the reported
    combined Sharpe can also be fed to the paired bootstrap — otherwise the interval
    would be computed on a differently-weighted book than the point estimate, which is
    the kind of quiet mismatch that makes an interval meaningless. Both now go through
    `_inverse_vol_weights`, so they cannot drift apart."""
    _check_pair(long_returns, short_returns, min_bars)
    weights, _ = _inverse_vol_weights(long_returns, short_returns, min_bars)
    return [
        wa * long_returns[min_bars + i] + wb * short_returns[min_bars + i]
        for i, (wa, wb) in enumerate(weights)
    ]


def combine_books(
    long_returns: Sequence[float],
    short_returns: Sequence[float],
    rf_annual: float,
    periods_per_year: float,
    min_bars: int = ENSEMBLE_MIN_BARS,
) -> EnsembleResult:
    """Every figure here is measured over the POST-WARM-UP span, legs included.

    Scoring the legs on the full series while the combination starts `min_bars` bars
    later would compare three books over three different periods and present the
    difference as an effect of combining them."""
    _check_pair(long_returns, short_returns, min_bars)
    weights, fallback = _inverse_vol_weights(long_returns, short_returns, min_bars)
    a = list(long_returns[min_bars:])
    b = list(short_returns[min_bars:])
    combined = [wa * x + wb * y for (wa, wb), x, y in zip(weights, a, b)]
    return EnsembleResult(
        correlation=(
            float(np.corrcoef(a, b)[0, 1])
            if len(set(a)) > 1 and len(set(b)) > 1
            else 0.0
        ),
        n_bars=len(combined),
        n_warmup_bars=min_bars,
        n_fallback_bars=fallback,
        mean_long_weight=statistics.fmean([w[0] for w in weights]) if weights else 0.5,
        long_sharpe=sharpe(a, rf_annual, periods_per_year) if len(set(a)) > 1 else 0.0,
        short_sharpe=sharpe(b, rf_annual, periods_per_year) if len(set(b)) > 1 else 0.0,
        combined_sharpe=(
            sharpe(combined, rf_annual, periods_per_year) if len(set(combined)) > 1 else 0.0
        ),
        long_max_drawdown=_max_drawdown(a),
        short_max_drawdown=_max_drawdown(b),
        combined_max_drawdown=_max_drawdown(combined),
    )


# ------------------------------------------------------- exposure-matched random null


@dataclass(frozen=True)
class RandomEntryNull:
    n_draws: int
    direction: int
    observed_sharpe: float
    null_mean: float
    null_p05: float
    null_p50: float
    null_p95: float
    percentile: float
    """Fraction of random draws the real strategy beat. THIS is the primary verdict for
    the short book: any short rule looks good through 2018, so the question is whether
    these particular entries beat randomly-placed shorts of the same count and the same
    holding periods."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_draws": self.n_draws,
            "direction": self.direction,
            "observed_sharpe": self.observed_sharpe,
            "null_mean": self.null_mean,
            "null_p05": self.null_p05,
            "null_p50": self.null_p50,
            "null_p95": self.null_p95,
            "percentile": self.percentile,
        }


def random_entry_null(
    bar_returns: Sequence[float],
    holding_periods: Sequence[int],
    observed_sharpe: float,
    *,
    direction: int,
    rf_annual: float,
    periods_per_year: float,
    n_draws: int = 1000,
    seed: int = 0,
) -> RandomEntryNull:
    """Exposure-matched random-entry null, in either direction (D169).

    `direction` is +1 for a long book and -1 for a short one — the parameter the
    breakdown addon asked the null generator to take. The draws reproduce the real
    strategy's TRADE COUNT and its HOLDING-PERIOD DISTRIBUTION exactly, placing those
    same durations at uniformly random non-overlapping start points. So the null has the
    same time in market and the same trade shape; the only thing randomised is WHEN.

    That isolates the claim under test. A short book in a sample containing 2018 and 2022
    will show a positive return whatever its entry rule, because the instrument fell; the
    null asks whether the entry rule chose better moments than chance."""
    n = len(bar_returns)
    periods = [p for p in holding_periods if p > 0]
    if not periods or n < 2:
        return RandomEntryNull(n_draws, direction, observed_sharpe, 0.0, 0.0, 0.0, 0.0, 0.0)

    rng = np.random.default_rng(seed)
    returns = np.asarray(bar_returns, dtype=float)
    draws = np.empty(n_draws, dtype=float)

    for d in range(n_draws):
        occupied = np.zeros(n, dtype=bool)
        for length in periods:
            for _attempt in range(20):
                start = int(rng.integers(0, max(n - length, 1)))
                window = slice(start, start + length)
                if not occupied[window].any():
                    occupied[window] = True
                    break
            # If 20 attempts all collided the sample is too crowded to place this
            # episode; it is dropped rather than forced, which makes the null slightly
            # LESS exposed than the strategy and therefore slightly conservative.
        path = np.where(occupied, direction * returns, 0.0)
        sd = path.std(ddof=1)
        draws[d] = (
            sharpe(list(path), rf_annual, periods_per_year) if sd > 0 else 0.0
        )

    return RandomEntryNull(
        n_draws=n_draws,
        direction=direction,
        observed_sharpe=observed_sharpe,
        null_mean=float(draws.mean()),
        null_p05=float(np.percentile(draws, 5)),
        null_p50=float(np.percentile(draws, 50)),
        null_p95=float(np.percentile(draws, 95)),
        # D542. This was `float((draws < observed_sharpe).mean())` — strictly-below, on a
        # 0-1 scale — while `breakout_nulls.summarise_null` and both terrain comparisons
        # published the same key mid-rank on a 0-100 scale. Two statistics and two units
        # under one name, in two committed artifacts, with nothing saying which was which:
        # a reader diffing this file against `terrain_strategy_summary.json` could not tell
        # that 0.955 and 95.5 are not the same number expressed differently.
        #
        # Mid-rank wins because it is the one with a stated reason (ties at half weight, so
        # a discrete statistic does not flatter whichever side is integer-equal), and
        # because three of the four sites already used it. This MOVES the published values
        # in `data/breakdown_study_summary.json`, which is the point — the two answers
        # already disagreed, so one of them was already wrong.
        percentile=mid_rank_percentile(draws.tolist(), observed_sharpe),
    )


# ------------------------------------------------------------------ stop-gap measuring


@dataclass(frozen=True)
class StopGapReport:
    """What the close-based stop actually cost, versus the stop it nominally held.

    The engine has no intrabar stop execution (D169), so a stop is observed on a CLOSE
    and filled at the NEXT OPEN. This measures the shortfall directly instead of leaving
    the brief's "tail truncated by construction" premise silently unmet."""

    n_stop_exits: int
    n_gapped: int
    """Stop exits that filled WORSE than the stop level — the tail the stop did not
    actually truncate, because the bar opened past it."""
    worst_gap_pct: float
    mean_gap_pct: float
    total_gap_cost_pct_of_nav: float
    n_armings: int = 0
    """How many bars carried a live stop. The ratio of exits to armings is the honest
    measure of whether the tail discipline BINDS or is merely present."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_stop_exits": self.n_stop_exits,
            "n_gapped": self.n_gapped,
            "n_armings": self.n_armings,
            "worst_gap_pct": self.worst_gap_pct,
            "mean_gap_pct": self.mean_gap_pct,
            "total_gap_cost_pct_of_nav": self.total_gap_cost_pct_of_nav,
        }


def measure_stop_gaps(
    stop_fills: Sequence[tuple[Any, ...]],
    n_armings: int = 0,
) -> StopGapReport:
    """Report on the exits the STOP actually caused (D170).

    Takes `BacktestResult.stop_fills`, which the engine records, rather than inferring
    stop exits from prices afterwards. The Phase 2 version of this function inferred:
    it recomputed the stop level and counted any episode whose exit price ended beyond
    it. That also catches ordinary trailing-channel exits that happened to close past
    the level, and it reported them as stops that had failed — which is how
    BREAKDOWN_RESULTS came to claim "4 of 4 stop exits gapped" when the true number of
    stop-caused exits was far smaller. Only the engine knows which fill a stop caused.

    A fill price differing from the stop price is the gap case (D10): the bar opened
    beyond the stop, so the position filled at the open and the stop did not bound the
    loss where it was set."""
    gaps: list[float] = []
    for _ts, _sid, _inst, _qty, fill_price, stop_price in stop_fills:
        if stop_price and abs(fill_price - stop_price) > 1e-9:
            gaps.append(abs(fill_price - stop_price) / stop_price)
    return StopGapReport(
        n_stop_exits=len(stop_fills),
        n_gapped=len(gaps),
        worst_gap_pct=max(gaps) if gaps else 0.0,
        mean_gap_pct=statistics.fmean(gaps) if gaps else 0.0,
        total_gap_cost_pct_of_nav=sum(gaps) if gaps else 0.0,
        n_armings=n_armings,
    )


# ------------------------------------------------------------------------- squeeze

@dataclass(frozen=True)
class SqueezeReport:
    """Adverse excursions beyond `atr_multiple` ATR against an open position — the event
    the tail discipline exists for, counted and priced rather than asserted."""

    n_trades: int
    n_squeezes: int
    share_of_trades: float
    pnl_in_squeezed_trades: float
    worst_atr_multiples: float
    median_atr_multiples: float
    stop_hit_share: float
    """Fraction of squeezed trades that ended at the stop. A squeeze the stop caught is a
    different event from one it did not."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_trades": self.n_trades,
            "n_squeezes": self.n_squeezes,
            "share_of_trades": self.share_of_trades,
            "pnl_in_squeezed_trades": self.pnl_in_squeezed_trades,
            "worst_atr_multiples": self.worst_atr_multiples,
            "median_atr_multiples": self.median_atr_multiples,
            "stop_hit_share": self.stop_hit_share,
        }


def squeeze_events(
    episodes: Sequence[Any],
    bars: Sequence[TimestampedBar],
    stop_fills: Sequence[tuple[Any, ...]] = (),
    *,
    direction: int = -1,
    atr_multiple: float = 2.0,
    atr_window: int = 20,
) -> SqueezeReport:
    """Adverse excursions beyond `atr_multiple` ATR against an open position (D176).

    **Which excursion is "adverse" depends on the trade's direction, and getting that
    backwards is silent.** `trade_diagnostics` measures excursions in PRICE terms, not
    trade terms: `mfe` is `max(high)/entry - 1` and `mae` is `min(low)/entry - 1`,
    written for the long-flat book it was built for (D112). For a LONG the adverse side
    is therefore `mae`; **for a SHORT it is `mfe`** — a short is hurt when price rises.

    The first version of this function used `abs(mae)` for the short book, which is the
    FAVOURABLE side, and would have reported profitable excursions as squeezes. It was
    never called, so nothing was published from it; it is corrected here rather than
    quietly rewritten, because the comment above it had reasoned its way confidently to
    the wrong answer."""
    trades = [e for e in episodes if not e.is_open]
    stop_bars = {t[0] for t in stop_fills}
    multiples, squeezed = [], []
    for e in trades:
        atr = _atr_at(bars, e.entry_index, atr_window)
        if atr is None or atr <= 0.0:
            continue
        adverse_fraction = e.mfe if direction < 0 else -e.mae
        if adverse_fraction <= 0:
            continue
        adverse = adverse_fraction * e.entry_price
        m = adverse / atr
        multiples.append(m)
        if m > atr_multiple:
            squeezed.append((e, m))

    caught = sum(1 for e, _ in squeezed if e.exit_timestamp in stop_bars)
    return SqueezeReport(
        n_trades=len(trades),
        n_squeezes=len(squeezed),
        share_of_trades=len(squeezed) / len(trades) if trades else 0.0,
        pnl_in_squeezed_trades=sum(e.net_pnl for e, _ in squeezed),
        worst_atr_multiples=max((m for _e, m in squeezed), default=0.0),
        median_atr_multiples=statistics.median(multiples) if multiples else 0.0,
        stop_hit_share=caught / len(squeezed) if squeezed else 0.0,
    )


def _atr_at(bars: Sequence[TimestampedBar], index: int, window: int) -> float | None:
    """Mean true range over the `window` bars ENDING AT index-1 (D44), so the entry bar's
    own range does not set the yardstick its excursion is measured against."""
    start = index - window
    if start < 1 or index > len(bars):
        return None
    total = 0.0
    for j in range(start, index):
        bar, prev_close = bars[j].bar, bars[j - 1].bar.close
        total += max(bar.high - bar.low, abs(bar.high - prev_close), abs(bar.low - prev_close))
    return total / window


def correlation_by_window(
    long_returns: Sequence[float],
    short_returns: Sequence[float],
    window_bounds: Sequence[tuple[int, int]],
) -> list[dict[str, Any]]:
    """Long-vs-short return correlation computed PER WALK-FORWARD WINDOW (D176).

    The brief asks for this and the first cut of the study reported the full-sample figure
    only. They answer different questions: a full-sample correlation near zero is
    consistent with the two books being strongly correlated in some regimes and strongly
    anti-correlated in others, which is exactly the case that would break the
    diversification argument at the moment it is needed.

    `window_bounds` are (start, end) indices into the OOS return series. Windows where
    either series is constant — which for a short book means it never traded in that
    window — return None rather than a fabricated zero: "no correlation measurable" and
    "correlation is zero" are different findings."""
    out: list[dict[str, Any]] = []
    for i, (start, end) in enumerate(window_bounds):
        a = list(long_returns[start:end])
        b = list(short_returns[start:end])
        n = min(len(a), len(b))
        a, b = a[:n], b[:n]
        rho: float | None = None
        if n >= 3 and len(set(a)) > 1 and len(set(b)) > 1:
            rho = float(np.corrcoef(a, b)[0, 1])
        out.append({
            "window": i,
            "n_bars": n,
            "correlation": rho,
            "short_active": bool(len(set(b)) > 1),
        })
    return out
