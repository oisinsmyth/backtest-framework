"""Monte Carlo null-hypothesis suite for the long-flat breakout study (D130–D133).

The question this module exists to answer is the one a reviewer asks hardest about a
trend follower run on 2015–2025 crypto: **is the strategy exploiting genuine serial
dependence in prices, or is it just harvesting a fat-tailed, strongly-drifting marginal
return distribution?** `BREAKOUT_RESULTS.md` already establishes that the absolute
returns belong to the era (D121) and that the Sharpe advantage is inside the noise
(D120). Neither of those tests the mechanism. This one does.

## The null construction (D130) — the load-bearing assumption of the whole study

Destroy the ORDERING of the bars while preserving the marginal distribution EXACTLY,
then re-run the real strategy through the real engine on the resampled path.

The strategy needs OHLC, not closes: `entry_level` is a rolling max of HIGHS and
`exit_level` a rolling min of LOWS. Shuffling closes and synthesising bars around them
would invent intrabar geometry the source data never had, and the invented geometry is
precisely what the entry and exit levels are computed from. So the resampling unit is
the **bar shape**: for every bar t after the first, the four-tuple

    (open_t / close_{t-1},  high_t / close_{t-1},  low_t / close_{t-1},  close_t / close_{t-1})

is retained as one indivisible object. A resampled path takes a permutation of those
tuples and chains them: close_t = close_{t-1} x close-ratio_t, and the same
close_{t-1} scales that bar's open, high and low. Consequences, all of them checked by
`tests/unit/test_breakout_nulls.py`:

- **Intrabar geometry survives exactly.** Every bar's o/h/l/c keep their mutual ratios,
  because they are all multiplied by the same previous close. A high stays above its
  own close by the same fraction it did in the source data. No coherence is invented.
- **The marginal distribution survives exactly**, not in expectation: the resampled
  path's multiset of bar shapes IS the source's multiset (see `block_permutation` —
  this is a permutation, never a draw with replacement).
- **Buy-and-hold is invariant.** The terminal close is `close_0 x prod(close-ratios)`,
  and a permutation does not change a product. So close-to-close buy-and-hold on a
  resampled path earns *identically* what it earned on the real path, to floating-point
  tolerance (D47). That is what makes this a controlled comparison: same drift, same
  fat tails, same total instrument return — only the sequence destroyed.

**Why permutation and not `analytics.monte_carlo.block_bootstrap_paths` (D130).** That
generator resamples overlapping blocks WITH replacement, which is the right tool for a
sampling distribution (and is what tests 3 and 4 below use). It is the wrong tool here:
with replacement, the marginal distribution is preserved only in expectation and the
buy-and-hold invariant is lost, so a shortfall on null paths could not be attributed to
ordering rather than to a re-drawn return distribution. The existing interface is not
modified; a second, differently-purposed generator is added beside it.

## The block ladder (D131)

`block_size=1` is the full shuffle: every scrap of serial dependence is gone.
As the block grows, contiguous runs of real bars survive inside each block and only the
joins between blocks are randomised, so more genuine serial structure is retained and
the null distribution should walk toward the real result. **Where it crosses is a
measurement of the time scale of the dependence the strategy trades** — directly
checkable against the measured 26–29 day median holding period.

This is D23's block-versus-shuffle argument applied to a trend follower, and **the sign
is inverted from the pairs case**. There, the shuffle was demoted because destroying
autocorrelation removed the effect a mean-reverter needs, making the null too easy to
beat. Here the same destruction is exactly the point: the shuffle is the null, and a
trend follower that still earns its result on shuffled bars has no timing edge at all.
The block ladder is the same instrument used as a ruler rather than as a null.

## What the module does NOT claim

A path built by permuting bar shapes is not a plausible price series. It has no
volatility clustering, no regimes, no calendar. That is deliberate — it is a null, and
the only property it must have is "same marginal, no ordering". Its lack of realism is
the hypothesis, not a defect.
"""

from __future__ import annotations

import math
from concurrent.futures import Executor
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Sequence

import numpy as np

from ..analytics.metrics import max_drawdown_from_returns
from ..data.bars import TimestampedBar
from ..simulator.fills import Bar
from .breakout_study import (
    BenchmarkResult,
    BreakoutStudyConfig,
    CostTier,
    Variant,
    VariantResult,
    _window_spans,
    run_benchmark,
    run_variant,
)
from .trade_diagnostics import TradeEpisode

MIN_BARS_FOR_NULL = 3
"""Two bars give exactly one bar shape, and a one-element multiset has exactly one
permutation — a "null" with a single possible outcome. Refused rather than returned."""

DEFAULT_BLOCK_LADDER: tuple[int, ...] = (1, 5, 20, 60)
"""The block sizes the study reports (D131). 1 = full shuffle; 60 is a little over twice
the measured median holding period, so a strategy whose edge lives entirely inside one
trade's worth of bars should be indistinguishable from the real result by then."""

DEFAULT_N_SIMS = 10_000
"""D36/D81's floor, honoured everywhere in this module including the path nulls (D132).

That was not a foregone conclusion and the arithmetic is worth recording. One path-null
simulation is a full strategy re-run over ~3,700 bars through the real engine — measured
at **101 ms on BTC-USD and 65 ms on ETH-USD** single-process — so 10,000 sims across the
16-cell grid (2 symbols x 2 tiers x 4 block sizes) is ~3.7 hours of serial compute, and a
reduction to n = 2,000 was budgeted as an explicit, costed deviation. It was not taken:
every simulation's seed is derived up front from the root seed, so the work parallelises
across processes without changing any number, and twelve workers bring the whole grid in
under an hour. Every reported p-value still carries its Monte Carlo standard error, so
the resolution bought is visible rather than implied."""

DEFAULT_ARITHMETIC_SIMS = DEFAULT_N_SIMS
"""Alias kept because tests 3 and 4 are arithmetic on existing series and would honour
D36 at any cost — naming them separately from the expensive path nulls is how the two
different compute stories stay legible in the runner's arguments."""


# ------------------------------------------------------------------- bar-shape nulls


@dataclass(frozen=True)
class BarShapes:
    """A bar series decomposed into a fixed anchor bar plus a sequence of bar shapes.

    `ratios` is (n_bars - 1, 4): columns are open, high, low, close, each divided by the
    PREVIOUS bar's close. Resampling permutes ROWS — never entries within a row, which
    is what keeps a bar's high above its own close.

    `segment_starts` are bar indices at which a new independently-permuted segment
    begins (see `bar_shapes`)."""

    first_bar: TimestampedBar
    timestamps: tuple[datetime, ...]
    ratios: np.ndarray
    segment_starts: tuple[int, ...] = ()

    @property
    def n_bars(self) -> int:
        return len(self.timestamps)

    @property
    def n_shapes(self) -> int:
        return int(self.ratios.shape[0])

    def segments(self) -> list[tuple[int, int]]:
        """[start, end) ranges over SHAPE indices, in order and covering everything."""
        edges = [0, *self.segment_starts, self.n_shapes]
        return [(a, b) for a, b in zip(edges, edges[1:])]

    def terminal_growth(self) -> float:
        """close(last) / close(first) — invariant under any permutation of the rows,
        which is the property the whole null rests on."""
        return float(np.prod(self.ratios[:, 3]))


def bar_shapes(
    bars: Sequence[TimestampedBar], segment_starts: Sequence[int] = ()
) -> BarShapes:
    """Decompose a bar series into (anchor bar, bar shapes), optionally SEGMENTED.

    **Why segments exist, and why the study always uses them (D130).** The published
    result is measured over the out-of-sample span, not over the whole fixture — the
    bars before it are warm-up and training history. A permutation of the whole fixture
    would move training-era bar shapes into the out-of-sample span and vice versa, so
    each null path's OOS span would carry a *randomly re-drawn* marginal distribution
    rather than the real one. That confounds the two things the test is meant to
    separate: ordering, and the distribution being ordered.

    Splitting the shape sequence at the OOS start and permuting each part independently
    fixes it exactly. The out-of-sample span's multiset of bar shapes is then identical
    to the real one on every path, so close-to-close buy-and-hold **over the measured
    span** is invariant, not merely invariant over the whole fixture. Nothing about the
    strategy's information set changes: within the OOS span the ordering is destroyed
    completely at block size 1, which is the hypothesis under test.

    Fails loudly on the degenerate inputs a null generator must never quietly accept:
    too few bars, non-finite or non-positive prices, and a constant (or perfectly
    geometric) price path, whose every permutation is the identity — a "null
    distribution" over it would be a single point reported as if it were a
    distribution."""
    if len(bars) < MIN_BARS_FOR_NULL:
        raise ValueError(
            f"bar-shape resampling needs at least {MIN_BARS_FOR_NULL} bars, got {len(bars)} — "
            "fewer than that admits no non-trivial permutation"
        )
    prices = np.array(
        [[tb.bar.open, tb.bar.high, tb.bar.low, tb.bar.close] for tb in bars], dtype=float
    )
    if not np.all(np.isfinite(prices)):
        raise ValueError("bar series contains non-finite prices — refusing to build a null from it")
    if np.any(prices <= 0.0):
        raise ValueError(
            "bar series contains non-positive prices — bar shapes are ratios and would be "
            "undefined or sign-flipped"
        )
    ratios = prices[1:] / prices[:-1, 3][:, None]
    if np.allclose(ratios, ratios[0], rtol=0.0, atol=1e-15):
        raise ValueError(
            "every bar has the same shape (a constant or perfectly geometric price path) — "
            "every permutation reproduces the source series, so the null distribution would "
            "be a single point masquerading as a distribution"
        )
    starts = tuple(int(s) for s in segment_starts)
    if list(starts) != sorted(set(starts)):
        raise ValueError(f"segment_starts must be strictly increasing, got {starts}")
    if any(s < 1 or s >= ratios.shape[0] for s in starts):
        raise ValueError(
            f"segment_starts must lie strictly inside 1..{ratios.shape[0] - 1}, got {starts}"
        )
    return BarShapes(
        first_bar=bars[0],
        timestamps=tuple(tb.timestamp for tb in bars),
        ratios=ratios,
        segment_starts=starts,
    )


def block_permutation(n_items: int, block_size: int, rng: np.random.Generator) -> np.ndarray:
    """Indices 0..n_items-1 cut into consecutive non-overlapping blocks whose ORDER is
    permuted (D130).

    Permutation, not a draw with replacement: the returned index vector is a bijection
    onto `range(n_items)`, so applying it to the bar shapes preserves their multiset
    exactly and therefore preserves the product of close ratios exactly. A moving-block
    bootstrap with replacement would do neither, and the buy-and-hold invariant is the
    entire reason this null is a controlled comparison rather than a re-draw.

    The final block is short whenever `block_size` does not divide `n_items`; it is
    permuted along with the rest, which keeps the multiset property intact (it changes
    only WHERE the ragged block lands)."""
    if n_items < 1:
        raise ValueError(f"n_items must be positive, got {n_items}")
    if block_size < 1:
        raise ValueError(f"block_size must be at least 1, got {block_size}")
    if block_size >= n_items:
        raise ValueError(
            f"block_size={block_size} leaves only one block over {n_items} items — the "
            "'permutation' would be the identity, and a null that cannot differ from its "
            "source is not a null"
        )
    bounds = list(range(0, n_items, block_size))
    order = rng.permutation(len(bounds))
    return np.concatenate(
        [np.arange(bounds[b], min(bounds[b] + block_size, n_items)) for b in order]
    )


def resample_bars(shapes: BarShapes, seed: int, block_size: int = 1) -> list[TimestampedBar]:
    """One null path: permute the bar shapes in blocks — independently within each
    segment — and chain them from the anchor bar's close, keeping the original
    timestamps.

    `seed` is required (D34). Same seed and block size -> byte-identical path."""
    rng = np.random.default_rng(seed)
    index = np.concatenate(
        [start + block_permutation(end - start, block_size, rng) for start, end in shapes.segments()]
    )
    ratios = shapes.ratios[index]

    closes = shapes.first_bar.bar.close * np.cumprod(ratios[:, 3])
    previous = np.concatenate(([shapes.first_bar.bar.close], closes[:-1]))
    opens = previous * ratios[:, 0]
    highs = previous * ratios[:, 1]
    lows = previous * ratios[:, 2]

    path = [shapes.first_bar]
    path.extend(
        TimestampedBar(
            shapes.timestamps[i + 1],
            Bar(open=float(opens[i]), high=float(highs[i]), low=float(lows[i]), close=float(closes[i])),
        )
        for i in range(shapes.n_shapes)
    )
    return path


def simulation_seeds(seed: int, n_sims: int) -> tuple[int, ...]:
    """Per-simulation seeds derived from one root seed via `SeedSequence` (D34).

    Derived rather than `seed + i` so the streams are independent, and derived from the
    root ALONE — not from the block size or the cost tier — so the same n paths are used
    in every cell of the grid. That makes the block ladder and the two cost tiers paired
    comparisons on identical null data, and it makes any cell reproducible on its own."""
    if n_sims < 1:
        raise ValueError(f"n_sims must be positive, got {n_sims}")
    state = np.random.SeedSequence(seed).generate_state(n_sims, dtype=np.uint64)
    return tuple(int(x) for x in state)


# --------------------------------------------------------- the study's own OOS span


def study_span(bars: Sequence[TimestampedBar], study: BreakoutStudyConfig) -> tuple[int, int]:
    """(first OOS bar index, one past the last OOS bar index), taken from the study's
    OWN window derivation rather than re-computed here. `breakout_study._window_spans`
    is module-private but it is the single place the study derives spans from
    `walk_forward_windows`, and its docstring says never to re-derive them by hand — a
    second copy of that arithmetic is exactly how a null and the result it is a null
    for end up measuring different spans."""
    spans = _window_spans(bars, study)
    if not spans:
        raise ValueError("no walk-forward windows fit the series — check sizes vs series length")
    return spans[0][2], spans[-1][3]


def study_bar_shapes(
    bars: Sequence[TimestampedBar], study: BreakoutStudyConfig
) -> tuple[list[TimestampedBar], BarShapes]:
    """The (trimmed bars, segmented bar shapes) pair the study nulls run on.

    Two things happen here, both stated because both are assumptions:

    - **The series is trimmed to the last OOS bar.** `run_variant` only ever reads
      `bars[run_start:oos_end]`, so bars past the final walk-forward window are unused
      by the study — but they are NOT unused by a whole-series permutation, which would
      shuffle them into the measured span. Trimming them is a no-op for the strategy
      (pinned by a test that the real result is identical either way) and removes the
      contamination.
    - **The shapes are segmented at the first OOS bar**, so the prefix and the measured
      span are permuted independently (see `bar_shapes`)."""
    oos_start, oos_end = study_span(bars, study)
    trimmed = list(bars[:oos_end])
    return trimmed, bar_shapes(trimmed, segment_starts=(oos_start,))


# ------------------------------------------------------------------ metric machinery


@dataclass(frozen=True)
class NullSample:
    """Everything one simulated path produces. Deliberately a flat record of scalars:
    the paths themselves are not retained (16 cells x 10,000 paths x 4,000 bars would be
    gigabytes) and every reported number is derivable from these."""

    total_return: float
    sharpe_annual: float
    max_drawdown: float
    exposure: float
    n_trades: float
    benchmark_total_return: float
    benchmark_max_drawdown: float


@dataclass(frozen=True)
class MetricSpec:
    name: str
    direction: str
    """"high" = the real result is notable if it sits in the UPPER tail of the null;
    "low" = notable in the LOWER tail. Stated per metric rather than inferred, because
    the direction IS the hypothesis and a silently-chosen tail is how a two-sided
    question gets reported as a one-sided p-value."""
    label: str
    note: str


NULL_METRICS: tuple[MetricSpec, ...] = (
    MetricSpec("total_return", "high", "Total return", "at least the real total return"),
    MetricSpec("sharpe_annual", "high", "Sharpe (ann.)", "at least the real Sharpe"),
    MetricSpec("max_drawdown", "low", "Max drawdown", "a drawdown no deeper than the real one"),
    MetricSpec(
        "exposure",
        "high",
        "Exposure",
        "at least the real time in market (real trends persist, so a real path should hold longer)",
    ),
    MetricSpec(
        "n_trades",
        "low",
        "Closed trades",
        "no more round trips than the real count (persistent trends mean fewer entries and fewer whipsaws)",
    ),
)
"""The five metrics the brief asks for, each with the tail that would support the
strategy's own story. `max_drawdown` and `n_trades` are lower-tail because for those two
"better" means "smaller"; reporting them upper-tail would invert their meaning."""


@dataclass(frozen=True)
class NullDistribution:
    metric: str
    label: str
    direction: str
    real: float
    n_sims: int
    percentile: float
    p_value: float
    p_value_se: float
    null_mean: float
    null_p05: float
    null_median: float
    null_p95: float

    def to_dict(self) -> dict[str, float | str | int]:
        return {
            "metric": self.metric,
            "direction": self.direction,
            "real": self.real,
            "n_sims": self.n_sims,
            "percentile": self.percentile,
            "p_value": self.p_value,
            "p_value_se": self.p_value_se,
            "null_mean": self.null_mean,
            "null_p05": self.null_p05,
            "null_median": self.null_median,
            "null_p95": self.null_p95,
        }


def summarise_null(
    values: Sequence[float] | np.ndarray, real: float, spec: MetricSpec
) -> NullDistribution:
    """Percentile of the real result inside the null, plus a one-sided empirical
    p-value and its Monte Carlo standard error.

    - **Percentile** is mid-rank: ties contribute a half. On a discrete statistic like
      the closed-trade count, counting ties as strictly-below would flatter whichever
      side of the comparison happened to be integer-equal.
    - **p-value** is `(1 + #{null at least as extreme}) / (n + 1)` — the add-one form,
      because an empirical p-value of exactly 0 from n draws is a statement the sample
      cannot support; the floor it reports instead is `1/(n+1)`.
    - **SE** is the binomial standard error `sqrt(p(1-p)/n)` of that estimate. It is
      the honest expression of what a reduced n bought (D132): at n = 2,000 a p of
      0.05 carries an SE of 0.005, so "p < 0.01" and "p = 0.05" are distinguishable and
      "p = 0.05" versus "p = 0.06" is not."""
    v = np.asarray(values, dtype=float)
    if v.size < 1:
        raise ValueError("cannot summarise an empty null distribution")
    if spec.direction not in ("high", "low"):
        raise ValueError(f"unknown direction {spec.direction!r} for metric {spec.name!r}")

    n = int(v.size)
    percentile = 100.0 * (float(np.sum(v < real)) + 0.5 * float(np.sum(v == real))) / n
    at_least_as_extreme = int(np.sum(v >= real) if spec.direction == "high" else np.sum(v <= real))
    p = (1.0 + at_least_as_extreme) / (n + 1.0)
    return NullDistribution(
        metric=spec.name,
        label=spec.label,
        direction=spec.direction,
        real=float(real),
        n_sims=n,
        percentile=percentile,
        p_value=p,
        p_value_se=math.sqrt(p * (1.0 - p) / n),
        null_mean=float(np.mean(v)),
        null_p05=float(np.percentile(v, 5)),
        null_median=float(np.percentile(v, 50)),
        null_p95=float(np.percentile(v, 95)),
    )


# ------------------------------------------------------------------- the path nulls


def evaluate_path(
    bars: Sequence[TimestampedBar],
    symbol: str,
    variant: Variant,
    tier: CostTier,
    study: BreakoutStudyConfig,
) -> NullSample:
    """Run the REAL strategy and the REAL benchmark on one bar series, through the same
    `run_variant` / `run_benchmark` the published study used. Nothing about the strategy,
    the cost stack, the walk-forward spans or the fill timing changes between the real
    path and a null path — only the bars do."""
    result = run_variant(bars, symbol, variant, tier, study)
    benchmark = run_benchmark(bars, symbol, tier, study)
    diagnostics = result.diagnostics
    return NullSample(
        total_return=result.total_return,
        sharpe_annual=result.sharpe_annual(study),
        max_drawdown=result.max_drawdown,
        exposure=diagnostics.exposure,
        n_trades=float(diagnostics.n_closed_trades),
        benchmark_total_return=benchmark.total_return,
        benchmark_max_drawdown=benchmark.max_drawdown,
    )


@dataclass(frozen=True)
class PathNullResult:
    symbol: str
    tier_name: str
    variant_name: str
    block_size: int
    seed: int
    real: NullSample
    samples: tuple[NullSample, ...]

    @property
    def n_sims(self) -> int:
        return len(self.samples)

    def values(self, metric: str) -> np.ndarray:
        return np.array([getattr(s, metric) for s in self.samples], dtype=float)

    def distribution(self, spec: MetricSpec) -> NullDistribution:
        return summarise_null(self.values(spec.name), getattr(self.real, spec.name), spec)

    def distributions(self) -> list[NullDistribution]:
        return [self.distribution(spec) for spec in NULL_METRICS]


def _chunk_payload(payload: tuple[Any, ...]) -> list[NullSample]:
    """Module-level so a `ProcessPoolExecutor` can pickle it. One chunk of seeds rather
    than one seed per task: the payload carries the whole bar-shape array, and paying
    that pickling cost once per worker beats paying it once per simulation."""
    shapes, symbol, variant, tier, study, block_size, seeds = payload
    return [
        evaluate_path(resample_bars(shapes, seed=s, block_size=block_size), symbol, variant, tier, study)
        for s in seeds
    ]


def path_null(
    bars: Sequence[TimestampedBar],
    symbol: str,
    variant: Variant,
    tier: CostTier,
    study: BreakoutStudyConfig,
    seed: int,
    n_sims: int = DEFAULT_N_SIMS,
    block_size: int = 1,
    executor: Executor | None = None,
    n_chunks: int = 1,
) -> PathNullResult:
    """Tests 1 and 2: re-run the strategy on `n_sims` bar-shape-resampled paths.

    `executor` is an optional `concurrent.futures.Executor`. Parallelism cannot change a
    number here: every simulation's seed is derived up front from the root seed, so
    result i depends only on seed i and the results are re-assembled in index order.
    Determinism under seed is asserted for both the serial and the parallel path."""
    trimmed, shapes = study_bar_shapes(bars, study)
    seeds = simulation_seeds(seed, n_sims)
    real = evaluate_path(trimmed, symbol, variant, tier, study)

    if executor is None:
        samples = _chunk_payload((shapes, symbol, variant, tier, study, block_size, seeds))
    else:
        if n_chunks < 1:
            raise ValueError(f"n_chunks must be positive, got {n_chunks}")
        splits = np.array_split(np.arange(n_sims), min(n_chunks, n_sims))
        payloads = [
            (shapes, symbol, variant, tier, study, block_size, [seeds[i] for i in part])
            for part in splits
            if len(part)
        ]
        samples = [s for chunk in executor.map(_chunk_payload, payloads) for s in chunk]

    return PathNullResult(
        symbol=symbol,
        tier_name=tier.name,
        variant_name=variant.name,
        block_size=block_size,
        seed=seed,
        real=real,
        samples=tuple(samples),
    )


# ----------------------------------------------------- trade-level bootstrap (test 3)


def trade_nav_returns(result: VariantResult) -> list[float]:
    """Each trade episode's return as a NAV MULTIPLE, read off the strategy's own
    out-of-sample equity curve: `NAV(exit bar) / NAV(bar before entry) - 1`.

    Why NAV multiples and not episode cash P&L divided by something: the strategy is
    FLAT between episodes and the engine pays no interest on idle cash, so NAV is
    constant outside episodes and the per-episode multiples telescope EXACTLY into the
    reported total return. That identity is asserted in the tests, and it is what makes
    a bootstrap over these numbers a bootstrap over terminal wealth rather than over an
    approximation of it.

    The entry NAV is taken from the bar BEFORE the entry fill: the fill happens at that
    bar's open (D103), so the entry bar's close already contains part of the trade."""
    navs = [nav for _, nav in result.oos_equity]
    index_of = {timestamp: i for i, (timestamp, _) in enumerate(result.oos_equity)}
    returns = []
    for episode in result.episodes:
        entry = index_of[episode.entry_timestamp]
        if entry < 1:
            raise ValueError(
                f"episode entered at the first OOS bar ({episode.entry_timestamp.isoformat()}) — "
                "there is no flat NAV before it to measure the trade against; the warm-up prefix "
                "is supposed to make this impossible (D113)"
            )
        exit_index = index_of[episode.exit_timestamp] if episode.exit_timestamp else len(navs) - 1
        returns.append(navs[exit_index] / navs[entry - 1] - 1.0)
    return returns


@dataclass(frozen=True)
class TradeConcentration:
    n_closed: int
    n_open: int
    n_winners: int
    total_net_pnl: float
    top_pnl_shares: dict[int, float]
    """N -> share of total net cash P&L contributed by the N most profitable closed
    trades. The measure the brief asks for."""
    top_log_shares: dict[int, float]
    """N -> share of total LOG growth contributed by the N best trades. Reported beside
    the cash version because cash P&L in a compounding strategy is mechanically larger
    late in the run — a 20% trade on a 50x'd account dwarfs a 200% trade at the start —
    so a cash-share concentration number partly measures WHEN a trade happened. The log
    version is the compounding-neutral answer to the same question."""
    best_trade_return: float
    worst_trade_return: float


def trade_concentration(result: VariantResult, top_n: Sequence[int] = (1, 3, 5)) -> TradeConcentration:
    """How much of the result rests on how few trades.

    A trend follower's return distribution is dominated by a handful of long winners —
    that is the mechanism, not a defect. What matters for a reviewer is the magnitude:
    if the top one or two trades carry the entire result, the effective sample size of
    the whole study is one or two, whatever the bar count says."""
    episodes: list[TradeEpisode] = list(result.episodes)
    closed = [e for e in episodes if not e.is_open]
    returns = trade_nav_returns(result)
    closed_returns = [r for r, e in zip(returns, episodes) if not e.is_open]

    total = sum(e.net_pnl for e in closed)
    ranked_pnl = sorted((e.net_pnl for e in closed), reverse=True)
    logs = [math.log1p(r) for r in closed_returns]
    total_log = sum(logs)
    ranked_log = sorted(logs, reverse=True)

    def share(ranked: Sequence[float], denominator: float, n: int) -> float:
        if denominator <= 0 or not ranked:
            return float("nan")
        return sum(ranked[: min(n, len(ranked))]) / denominator

    return TradeConcentration(
        n_closed=len(closed),
        n_open=len(episodes) - len(closed),
        n_winners=sum(1 for e in closed if e.net_pnl > 0),
        total_net_pnl=total,
        top_pnl_shares={n: share(ranked_pnl, total, n) for n in top_n},
        top_log_shares={n: share(ranked_log, total_log, n) for n in top_n},
        best_trade_return=max(closed_returns) if closed_returns else float("nan"),
        worst_trade_return=min(closed_returns) if closed_returns else float("nan"),
    )


def trade_bootstrap(
    trade_returns: Sequence[float],
    seed: int,
    n_sims: int = DEFAULT_ARITHMETIC_SIMS,
) -> dict[str, float]:
    """Test 3: resample the closed trades' returns WITH replacement and compound them
    into a terminal wealth distribution.

    With replacement is correct here and permutation would be useless: a permutation of
    a set of multiplicative returns gives the same product every time (the same algebra
    that makes the test-1 null a controlled comparison), so the only informative
    resampling of trades is one that varies WHICH trades occurred. `seed` required
    (D34); n defaults to D36's 10,000 because this is arithmetic on a few dozen
    numbers."""
    r = np.asarray(trade_returns, dtype=float)
    if r.size < 2:
        raise ValueError(f"trade bootstrap needs at least 2 closed trades, got {r.size}")
    if np.any(r <= -1.0):
        raise ValueError("a trade return of -100% or worse would wipe the account — refusing to compound it")
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, r.size, size=(n_sims, r.size))
    wealth = np.prod(1.0 + r[draws], axis=1)
    actual = float(np.prod(1.0 + r))
    return {
        "n_trades": float(r.size),
        "n_sims": float(n_sims),
        "seed": float(seed),
        "actual_terminal_wealth": actual,
        "mean": float(np.mean(wealth)),
        "p05": float(np.percentile(wealth, 5)),
        "p25": float(np.percentile(wealth, 25)),
        "median": float(np.percentile(wealth, 50)),
        "p75": float(np.percentile(wealth, 75)),
        "p95": float(np.percentile(wealth, 95)),
        "prob_below_one": float(np.mean(wealth < 1.0)),
        "prob_below_actual": float(np.mean(wealth < actual)),
    }


# --------------------------------------------- paired drawdown bootstrap (test 4)


def _max_drawdown_from_returns(paths: np.ndarray) -> np.ndarray:
    """Max drawdown of each row of a (n_paths, n_returns) return matrix, as a positive
    fraction. Identical arithmetic to `analytics.metrics.max_drawdown` on the equity
    curve those returns generate — asserted in the tests rather than assumed."""
    growth = np.cumprod(1.0 + paths, axis=1)
    growth = np.concatenate([np.ones((growth.shape[0], 1)), growth], axis=1)
    peak = np.maximum.accumulate(growth, axis=1)
    return ((peak - growth) / peak).max(axis=1)


def drawdown_difference_bootstrap(
    strategy_returns: Sequence[float],
    benchmark_returns: Sequence[float],
    seed: int,
    n_sims: int = DEFAULT_ARITHMETIC_SIMS,
    block_size: int = 20,
    chunk_size: int = 500,
) -> dict[str, float]:
    """Test 4: the sampling distribution of (benchmark max DD − strategy max DD), by
    PAIRED block bootstrap (D120's pairing, D133).

    `BREAKOUT_RESULTS.md` says the drawdown reduction is the one finding it can defend —
    and a max drawdown is a single-path statistic from n = 1. This puts an interval
    around it. The pairing is the load-bearing part, exactly as in
    `sharpe_difference_bootstrap`: ONE resampled index vector is applied to BOTH return
    series, so the strong correlation between a long-flat strategy and the instrument it
    trades survives. Bootstrapping them independently would inflate the variance of the
    difference and understate the strategy's advantage for the wrong reason.

    Blocks of 20 bars, D106's pinned default. Runs in chunks because a 10,000 x 3,700
    float64 matrix is ~300 MB per series and there are several.

    **What this does and does not measure.** It answers "how often would a re-drawn
    history, built from this one's 20-bar blocks, give the strategy the shallower
    drawdown?". It does NOT test serial dependence — the resampling destroys the very
    ordering a max drawdown depends on, which is why the resampled drawdowns are not
    expected to reproduce the observed pair. The observed difference is reported beside
    the distribution rather than inside it."""
    s = np.asarray(strategy_returns, dtype=float)
    b = np.asarray(benchmark_returns, dtype=float)
    if s.size != b.size:
        raise ValueError(f"paired bootstrap needs equal lengths, got {s.size} and {b.size}")
    if s.size <= block_size:
        raise ValueError(f"need more than {block_size} observations, got {s.size}")
    if chunk_size < 1:
        raise ValueError(f"chunk_size must be positive, got {chunk_size}")

    n = s.size
    n_blocks = n // block_size + 1
    offsets = np.arange(block_size)
    rng = np.random.default_rng(seed)
    strategy_dd = np.empty(n_sims, dtype=float)
    benchmark_dd = np.empty(n_sims, dtype=float)

    done = 0
    while done < n_sims:
        size = min(chunk_size, n_sims - done)
        starts = rng.integers(0, n - block_size, size=(size, n_blocks))
        index = (starts[:, :, None] + offsets[None, None, :]).reshape(size, -1)[:, :n]
        strategy_dd[done : done + size] = _max_drawdown_from_returns(s[index])
        benchmark_dd[done : done + size] = _max_drawdown_from_returns(b[index])
        done += size

    differences = benchmark_dd - strategy_dd
    observed_strategy = float(_max_drawdown_from_returns(s[None, :])[0])
    observed_benchmark = float(_max_drawdown_from_returns(b[None, :])[0])
    probability = float(np.mean(differences > 0.0))
    return {
        "n_obs": float(n),
        "n_sims": float(n_sims),
        "block_size": float(block_size),
        "seed": float(seed),
        "observed_difference": observed_benchmark - observed_strategy,
        "observed_strategy_maxdd": observed_strategy,
        "observed_benchmark_maxdd": observed_benchmark,
        "mean_strategy_maxdd": float(np.mean(strategy_dd)),
        "mean_benchmark_maxdd": float(np.mean(benchmark_dd)),
        "mean_difference": float(np.mean(differences)),
        "p05": float(np.percentile(differences, 5)),
        "median": float(np.percentile(differences, 50)),
        "p95": float(np.percentile(differences, 95)),
        "prob_strategy_shallower": probability,
        "prob_se": math.sqrt(probability * (1.0 - probability) / n_sims),
    }


# ----------------------------------------------------------------------- convenience


def real_result(
    bars: Sequence[TimestampedBar],
    symbol: str,
    variant: Variant,
    tier: CostTier,
    study: BreakoutStudyConfig,
) -> tuple[VariantResult, BenchmarkResult]:
    """The un-resampled strategy and benchmark — the reference every null is read
    against, produced by exactly the calls `scripts/run_breakout_study.py` makes."""
    return (
        run_variant(bars, symbol, variant, tier, study),
        run_benchmark(bars, symbol, tier, study),
    )


def returns_max_drawdown(returns: Sequence[float]) -> float:
    """Max drawdown implied by a return series, as a positive fraction.

    Now `analytics.metrics.max_drawdown_from_returns` (D542) rather than a second name for
    the vectorised path. The two are BIT-IDENTICAL on 603 probed curves including
    tie-heavy ones — pinned below in `tests/unit/test_breakout_nulls.py`, exactly, not to a
    tolerance — so the vectorised form keeps the hot path (10,000 sims x 2 series) and
    this keeps the definition.
    """
    return max_drawdown_from_returns(returns)
