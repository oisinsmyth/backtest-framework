"""Outcome-by-feature analysis for the at-trigger features (D167).

This is the "features, not filters" half of BREAKOUT_REVERSAL_FEATURES.md: every
feature is LOGGED on the existing accepted baseline's trades and then ranked against
trade outcomes, without a single new gate being built. Logging carries no multiplicity
cost, so nothing here enters the DSR trial pool — and nothing here can change a fill.

**Promotion is not decided here.** A feature becomes a candidate live filter only if it
shows (a) a monotonic relationship with outcomes, (b) stability across the sample, and
(c) a plateau over its own threshold. This module measures (a) and (b) and reports
them; (c) and the actual promotion are a separate later session with their own
TrialRegistry accounting. The verdict strings below are therefore "candidate" or
"no", never "adopted".

**The sample is thin and that is the headline.** The baseline trades a few dozen times
per instrument across a decade, so a quintile split leaves single-digit-to-low-teens
trades per bucket. Rank statistics on that many points are noisy enough that only a
very strong, very consistent relationship should be believed. Every table reports its
own bucket counts so the reader can see the thinness rather than infer it.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .trade_diagnostics import FEATURE_NAMES, FEATURE_UNAVAILABLE, TradeEpisode

MIN_TRADES_FOR_ANALYSIS = 20
"""Below this many trades with a value, a feature is reported as underpowered rather
than given a verdict. Not a significance threshold — a floor below which the arithmetic
is not worth printing."""

N_BUCKETS = 5
"""Quintiles, per the features doc. Kept as a named constant because the bucket count
is a stated convention, not a tuning knob to be swept."""


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    """Spearman rank correlation, ties averaged. Returns None when either series is
    constant (no ranks to correlate) or too short to mean anything.

    Rank correlation rather than Pearson because every hypothesis in the features doc
    is monotonic ("higher extension, worse outcomes"), not linear, and because a
    handful of extreme crypto trades would dominate a Pearson estimate."""
    if len(xs) != len(ys):
        raise ValueError(f"length mismatch: {len(xs)} vs {len(ys)}")
    if len(xs) < 3:
        return None
    rx, ry = _ranks(xs), _ranks(ys)
    if len(set(rx)) < 2 or len(set(ry)) < 2:
        return None
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else None


def _ranks(values: Sequence[float]) -> list[float]:
    """Average ranks, 1-based. Ties share their mean rank so a feature with repeated
    values (F4 on a two-instrument universe takes only 0, 0.5, 1) is handled honestly
    rather than by arbitrary ordering."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        shared = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = shared
        i = j + 1
    return ranks


@dataclass(frozen=True)
class Bucket:
    index: int
    n: int
    lo: float
    hi: float
    mean_mfe: float
    mean_mae: float
    win_rate: float
    whipsaw_rate: float

    def to_dict(self) -> dict[str, float | int]:
        return {
            "quintile": self.index,
            "n": self.n,
            "lo": self.lo,
            "hi": self.hi,
            "mean_mfe": self.mean_mfe,
            "mean_mae": self.mean_mae,
            "win_rate": self.win_rate,
            "whipsaw_rate": self.whipsaw_rate,
        }


@dataclass(frozen=True)
class FeatureVerdict:
    feature: str
    n_total: int
    n_available: int
    unavailable_reason: str | None
    buckets: tuple[Bucket, ...]
    rho_mfe: float | None
    """Spearman rank correlation between the raw feature value and MFE, over every
    trade where the feature is available. The headline monotonicity number."""
    rho_mae: float | None
    rho_first_half: float | None
    rho_second_half: float | None
    """The MFE correlation recomputed on the earlier and later halves of the trade
    population, split by entry time. Stability check: a relationship that flips sign
    between halves is sample noise, whatever its full-sample value."""
    verdict: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature": self.feature,
            "n_total": self.n_total,
            "n_available": self.n_available,
            "unavailable_reason": self.unavailable_reason,
            "buckets": [b.to_dict() for b in self.buckets],
            "rho_mfe": self.rho_mfe,
            "rho_mae": self.rho_mae,
            "rho_first_half": self.rho_first_half,
            "rho_second_half": self.rho_second_half,
            "verdict": self.verdict,
            "note": self.note,
        }


def _bucket(index: int, episodes: Sequence[tuple[float, TradeEpisode]], whipsaw_bars: int) -> Bucket:
    values = [v for v, _ in episodes]
    eps = [e for _, e in episodes]
    return Bucket(
        index=index,
        n=len(eps),
        lo=min(values),
        hi=max(values),
        mean_mfe=statistics.fmean(e.mfe for e in eps),
        mean_mae=statistics.fmean(e.mae for e in eps),
        win_rate=sum(1 for e in eps if e.net_pnl > 0) / len(eps),
        whipsaw_rate=sum(1 for e in eps if e.bars_held <= whipsaw_bars) / len(eps),
    )


def analyse_feature(
    episodes: Sequence[TradeEpisode], feature: str, *, whipsaw_bars: int = 3
) -> FeatureVerdict:
    """Rank `episodes` by one feature and report outcome by quintile.

    Only CLOSED episodes are used: an open trade has no realized outcome, and mixing
    unrealized excursion into an outcome table would flatter whichever bucket happens
    to contain the trade that is still running."""
    closed = [e for e in episodes if not e.is_open]
    paired: list[tuple[float, TradeEpisode]] = []
    for episode in closed:
        value = episode.features.get(feature)
        if value is not None:
            paired.append((value, episode))
    paired.sort(key=lambda pair: (pair[0], pair[1].entry_timestamp))
    reason = FEATURE_UNAVAILABLE.get(feature)

    if len(paired) < MIN_TRADES_FOR_ANALYSIS:
        note = (
            f"blocked: {reason}"
            if reason
            else f"only {len(paired)} trade(s) carry a value — below the {MIN_TRADES_FOR_ANALYSIS}-trade "
            "floor for printing rank statistics"
        )
        return FeatureVerdict(
            feature=feature,
            n_total=len(closed),
            n_available=len(paired),
            unavailable_reason=reason,
            buckets=(),
            rho_mfe=None,
            rho_mae=None,
            rho_first_half=None,
            rho_second_half=None,
            verdict="UNAVAILABLE" if reason else "UNDERPOWERED",
            note=note,
        )

    values = [v for v, _ in paired]
    mfes = [e.mfe for _, e in paired]
    maes = [e.mae for _, e in paired]

    buckets: list[Bucket] = []
    for index in range(N_BUCKETS):
        lo = len(paired) * index // N_BUCKETS
        hi = len(paired) * (index + 1) // N_BUCKETS
        if hi > lo:
            buckets.append(_bucket(index + 1, paired[lo:hi], whipsaw_bars))

    by_time = sorted(paired, key=lambda pair: pair[1].entry_timestamp)
    half = len(by_time) // 2
    rho_first = spearman([v for v, _ in by_time[:half]], [e.mfe for _, e in by_time[:half]])
    rho_second = spearman([v for v, _ in by_time[half:]], [e.mfe for _, e in by_time[half:]])

    rho = spearman(values, mfes)
    verdict, note = _verdict(rho, rho_first, rho_second, buckets)
    return FeatureVerdict(
        feature=feature,
        n_total=len(closed),
        n_available=len(paired),
        unavailable_reason=None,
        buckets=tuple(buckets),
        rho_mfe=rho,
        rho_mae=spearman(values, maes),
        rho_first_half=rho_first,
        rho_second_half=rho_second,
        verdict=verdict,
        note=note,
    )


def _verdict(
    rho: float | None,
    rho_first: float | None,
    rho_second: float | None,
    buckets: Sequence[Bucket],
) -> tuple[str, str]:
    """Three gates, all of which must hold for a feature to be called a candidate:
    a rank correlation worth looking at, the same sign in both halves of the sample,
    and quintile means that actually step in one direction.

    The thresholds are deliberately blunt and stated up front rather than searched:
    |rho| >= 0.2, sign agreement, and at least 4 of 5 quintile steps monotone. A
    feature that needs a finer threshold than this to look good has not been found by
    a decade of crypto trades."""
    if rho is None:
        return "NO", "feature is constant across the trade population — nothing to rank"
    steps = [b.mean_mfe for b in buckets]
    ups = sum(1 for a, b in zip(steps, steps[1:]) if b > a)
    downs = len(steps) - 1 - ups
    monotone = max(ups, downs) >= len(steps) - 2

    if abs(rho) < 0.2:
        return "NO", f"rank correlation with MFE is {rho:+.2f} — no usable relationship"
    if rho_first is None or rho_second is None:
        return "NO", f"rho={rho:+.2f} but the sample cannot be split for a stability check"
    if (rho_first > 0) != (rho_second > 0):
        return (
            "NO",
            f"rho={rho:+.2f} full sample but {rho_first:+.2f} then {rho_second:+.2f} across "
            "halves — the sign flips, so the relationship is sample noise",
        )
    if not monotone:
        return (
            "NO",
            f"rho={rho:+.2f} with a consistent sign, but the quintile means do not step "
            "monotonically — the relationship is not usable as a threshold",
        )
    return (
        "CANDIDATE",
        f"rho={rho:+.2f}, same sign in both halves ({rho_first:+.2f} / {rho_second:+.2f}), "
        "quintile means monotone — meets the logged-feature bar; a plateau test over its own "
        "threshold is still owed before any promotion",
    )


def analyse_all(
    episodes: Sequence[TradeEpisode], *, whipsaw_bars: int = 3
) -> dict[str, FeatureVerdict]:
    """Every feature in FEATURE_NAMES, in order. Features with no available values
    still get an entry — a blocked feature is reported as blocked, never omitted."""
    return {name: analyse_feature(episodes, name, whipsaw_bars=whipsaw_bars) for name in FEATURE_NAMES}


def summarise_features(verdicts: Mapping[str, FeatureVerdict]) -> dict[str, Any]:
    """JSON-serialisable payload for the study summary."""
    return {name: verdict.to_dict() for name, verdict in verdicts.items()}
