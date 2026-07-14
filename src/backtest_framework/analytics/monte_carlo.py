"""Seeded block-bootstrap Monte Carlo (D34, D36, D81).

Block bootstrap, not returns-shuffle: D23 demoted the shuffle because it destroys the
autocorrelation a mean-reversion strategy trades — resampling contiguous blocks
preserves local dependence. This is the same tool Step 12's validation science
reuses.

`seed` is a REQUIRED argument (D34): "deterministic simulator" means nothing for
reproducibility if the analytics layer is silently nondeterministic. Same seed →
byte-identical percentile table; the seed belongs in the TrialRegistry row of any
trial whose reported numbers came from this. Default n_sims is 10,000 (D36:
simulations are cheap; n=500 was an arbitrary number).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

DEFAULT_N_SIMS = 10_000
DEFAULT_BLOCK_SIZE = 20
DEFAULT_PERCENTILES = (5, 25, 50, 75, 95)


@dataclass(frozen=True)
class BootstrapPercentiles:
    n_sims: int
    block_size: int
    seed: int
    terminal_return: dict[int, float]
    max_drawdown: dict[int, float]


def block_bootstrap_paths(
    returns: Sequence[float],
    seed: int,
    n_sims: int = DEFAULT_N_SIMS,
    block_size: int = DEFAULT_BLOCK_SIZE,
) -> np.ndarray:
    """The resampled return paths themselves, shape (n_sims, len(returns)) — exposed
    (D87) so Step 12's shuffle-vs-block demonstration can measure autocorrelation on
    the paths, and Step-12-style nulls can reuse the generator. Contiguous blocks
    preserve local dependence; that is the entire point vs a shuffle (D23)."""
    r = np.asarray(returns, dtype=float)
    n = r.size
    if n < block_size:
        raise ValueError(f"need at least block_size={block_size} returns, got {n}")
    rng = np.random.default_rng(seed)

    n_blocks = -(-n // block_size)  # ceil
    starts = rng.integers(0, n - block_size + 1, size=(n_sims, n_blocks))
    # Assemble each simulated path from contiguous blocks, trimmed to length n.
    block_offsets = np.arange(block_size)
    indices = (starts[:, :, None] + block_offsets[None, None, :]).reshape(n_sims, -1)[:, :n]
    return r[indices]  # (n_sims, n)


def block_bootstrap_percentiles(
    returns: Sequence[float],
    seed: int,
    n_sims: int = DEFAULT_N_SIMS,
    block_size: int = DEFAULT_BLOCK_SIZE,
    percentiles: Sequence[int] = DEFAULT_PERCENTILES,
) -> BootstrapPercentiles:
    paths = block_bootstrap_paths(returns, seed=seed, n_sims=n_sims, block_size=block_size)

    growth = np.cumprod(1.0 + paths, axis=1)
    terminal = growth[:, -1] - 1.0
    running_peak = np.maximum.accumulate(growth, axis=1)
    drawdowns = ((running_peak - growth) / running_peak).max(axis=1)

    return BootstrapPercentiles(
        n_sims=n_sims,
        block_size=block_size,
        seed=seed,
        terminal_return={int(p): float(np.percentile(terminal, p)) for p in percentiles},
        max_drawdown={int(p): float(np.percentile(drawdowns, p)) for p in percentiles},
    )
