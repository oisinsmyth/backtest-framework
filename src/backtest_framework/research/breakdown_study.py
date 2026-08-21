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
from datetime import datetime
from typing import Any, Mapping, Sequence

import numpy as np

from ..analytics.metrics import sharpe
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
    long_sharpe: float
    short_sharpe: float
    combined_sharpe: float
    """Equal VOL weight, not equal capital: the two books have very different
    volatilities, so equal capital would just be the long book with noise added."""
    long_max_drawdown: float
    combined_max_drawdown: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "correlation": self.correlation,
            "n_bars": self.n_bars,
            "long_sharpe": self.long_sharpe,
            "short_sharpe": self.short_sharpe,
            "combined_sharpe": self.combined_sharpe,
            "long_max_drawdown": self.long_max_drawdown,
            "combined_max_drawdown": self.combined_max_drawdown,
        }


def _max_drawdown(returns: Sequence[float]) -> float:
    peak, nav, worst = 1.0, 1.0, 0.0
    for r in returns:
        nav *= 1.0 + r
        peak = max(peak, nav)
        worst = max(worst, 1.0 - nav / peak)
    return worst


def combined_series(
    long_returns: Sequence[float], short_returns: Sequence[float]
) -> list[float]:
    """The equal-VOL-weighted combined book's return series.

    Split out from `combine_books` so the same series that produces the reported
    combined Sharpe can also be fed to the paired bootstrap — otherwise the interval
    would be computed on a differently-weighted book than the point estimate, which is
    the kind of quiet mismatch that makes an interval meaningless."""
    n = min(len(long_returns), len(short_returns))
    a, b = list(long_returns[-n:]), list(short_returns[-n:])
    sd_a = statistics.stdev(a) if len(set(a)) > 1 else 0.0
    sd_b = statistics.stdev(b) if len(set(b)) > 1 else 0.0
    if sd_a > 0 and sd_b > 0:
        wa, wb = 1.0 / sd_a, 1.0 / sd_b
        wa, wb = wa / (wa + wb), wb / (wa + wb)
    else:
        wa = wb = 0.5
    return [wa * x + wb * y for x, y in zip(a, b)]


def combine_books(
    long_returns: Sequence[float],
    short_returns: Sequence[float],
    rf_annual: float,
    periods_per_year: float,
) -> EnsembleResult:
    n = min(len(long_returns), len(short_returns))
    a, b = list(long_returns[-n:]), list(short_returns[-n:])
    sd_a = statistics.stdev(a) if len(set(a)) > 1 else 0.0
    sd_b = statistics.stdev(b) if len(set(b)) > 1 else 0.0

    if sd_a > 0 and sd_b > 0:
        correlation = float(np.corrcoef(a, b)[0, 1])
        # Equal vol weight, normalised so the pair sums to 1 and the combined book is
        # comparable in scale to each component rather than quietly levered.
        wa, wb = (1.0 / sd_a), (1.0 / sd_b)
        wa, wb = wa / (wa + wb), wb / (wa + wb)
    else:
        correlation = 0.0
        wa = wb = 0.5
    combined = [wa * x + wb * y for x, y in zip(a, b)]
    return EnsembleResult(
        correlation=correlation,
        n_bars=n,
        long_sharpe=sharpe(a, rf_annual, periods_per_year) if len(set(a)) > 1 else 0.0,
        short_sharpe=sharpe(b, rf_annual, periods_per_year) if len(set(b)) > 1 else 0.0,
        combined_sharpe=(
            sharpe(combined, rf_annual, periods_per_year) if len(set(combined)) > 1 else 0.0
        ),
        long_max_drawdown=_max_drawdown(a),
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
        percentile=float((draws < observed_sharpe).mean()),
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

def squeeze_events(episodes: Sequence[Any], atr_by_entry: Mapping[int, float]) -> dict[str, Any]:
    """Adverse excursions beyond 2 ATR against an open short — the event the tail
    discipline exists for. Counted and priced, so "the stop works" is a measurement."""
    events = []
    for e in episodes:
        atr = atr_by_entry.get(e.entry_index)
        if not atr or atr <= 0:
            continue
        # For a short, an adverse move is the position going UP: MFE on a short episode
        # is measured against entry price in the trade's favour, so the adverse side is
        # the one the diagnostics call MAE for a long. Use the raw excursion magnitude.
        adverse = abs(e.mae) * e.entry_price
        if adverse > 2.0 * atr:
            events.append({"entry_index": e.entry_index, "atr_multiples": adverse / atr,
                           "net_pnl": e.net_pnl})
    return {
        "n_squeeze_events": len(events),
        "share_of_trades": len(events) / len(episodes) if episodes else 0.0,
        "pnl_in_squeeze_trades": sum(ev["net_pnl"] for ev in events),
        "worst_atr_multiples": max((ev["atr_multiples"] for ev in events), default=0.0),
    }
