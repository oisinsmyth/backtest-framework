"""Pair selection with multiplicity handling (D22, D29, D85).

Gatev distance: sum of squared differences between REBASED log-price series over the
training window — the classic pairs-trading first pass. Selection RANKS all C(n,2)
candidate pairs and takes the top N (D29: never threshold p-values — testing 200
pairs at p<0.05 manufactures ~10 discoveries from pure noise). The number of pairs
tested is returned alongside the ranking so the caller logs it to the TrialRegistry:
that count is exactly what DSR deflates by later (D20/D21).

Selection reads ONLY DataViews (D22/D28's guarded accessor): it cannot see beyond
the training window it was handed, structurally (D32/D56).
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
    """C(n,2) — the multiplicity count to log with any trial that uses this selection."""


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
