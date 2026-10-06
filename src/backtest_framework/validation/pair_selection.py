"""Pair selection with multiplicity handling.

Gatev distance: the sum of squared differences between rebased log-price series over
the training window. All C(n,2) candidate pairs are ranked and the top N taken, rather
than thresholding p-values (200 pairs tested at p<0.05 yield ~10 false discoveries).
The number of pairs tested is returned with the ranking so the caller can log it to
the TrialRegistry for DSR.

Selection reads only DataViews, so it cannot see past the training window.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from ..engine.dataview import DataView


@dataclass(frozen=True)
class PairSelection:
    ranked_pairs: tuple[tuple[str, str], ...]
    """Best (lowest Gatev distance) first."""
    n_pairs_tested: int
    """C(n,2): the multiplicity count to log with any trial that uses this selection."""


def select_pairs(views: Mapping[str, DataView], top_n: int) -> PairSelection:
    symbols = sorted(views)
    if len(symbols) < 2:
        raise ValueError(f"need at least 2 instruments to form a pair, got {len(symbols)}")
    length = len(views[symbols[0]])
    if any(len(views[s]) != length for s in symbols):
        raise ValueError("all views must cover the same (aligned) window")

    # Rebased log-price matrix (T x n): each series starts at 0, so distance measures
    # divergence of paths, not difference of price levels.
    log_prices = np.array([[np.log(views[s][i].close) for s in symbols] for i in range(length)])
    rebased = log_prices - log_prices[0]

    # All-pairs SSD via the gram-matrix identity ||xi - xj||^2 = ||xi||^2 + ||xj||^2 - 2 xi.xj
    gram = rebased.T @ rebased
    norms = np.diag(gram)
    ssd = norms[:, None] + norms[None, :] - 2.0 * gram

    n = len(symbols)
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    ranked = sorted(pairs, key=lambda ij: ssd[ij[0], ij[1]])
    return PairSelection(
        ranked_pairs=tuple((symbols[i], symbols[j]) for i, j in ranked[:top_n]),
        n_pairs_tested=len(pairs),
    )
