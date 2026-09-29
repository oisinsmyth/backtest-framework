"""The oracle filter and the accuracy assessment of a profit filter — D690.

The principal (2026-09-29): "We need a better way to filter for profits, make an oracle filter and the accuracy
assessment." Every strategy here carries an expected-profit filter (k = 2 x cost), and D689's failed: its projection
scaled with the size of the last move, and the kept trades lost. This module is the yardstick such a filter is held
to. It answers three questions, in this order:

1. WHAT IS THE PRIZE? The ORACLE FILTER takes a candidate trade if and only if its realised outcome clears the bar
   (`oracle_take`: net > 0; `oracle_take_threshold`: gross >= k x cost). It is hindsight, so it is a ceiling and
   never a strategy.
2. HOW ACCURATE MUST A FILTER BE BEFORE IT PAYS? The PARTIAL ORACLE (`partial_oracle_score`) is a forecast with a
   chosen accuracy. It takes the normal scores of the realised target and mixes in independent noise, so its
   normal-score correlation with the target is `rho` (a Gaussian copula; its Spearman correlation is about
   (6/pi) asin(rho/2), and the realised value is returned). `partial_oracle_curve` traces what a filter that keeps
   the top fraction `q` of candidates by such a forecast earns, as `rho` runs from 0 (a random filter: THE NULL the
   oracle must be read against) to 1 (the oracle).
3. HOW ACCURATE IS THIS FILTER? `assess` scores a real filter against the oracle:
   - the confusion matrix against the oracle label (precision, recall, F1, balanced accuracy);
   - the AUC of its score against that label;
   - the Spearman correlation of its score with the realised outcome (the partial-oracle curve's own axis, so the
     filter can be placed on the curve);
   - the share of the oracle's net P&L it captures;
   - and, via `calibration`, whether its projected profit is the profit that arrives (the realised-on-projected
     slope is 1 for an honest projection).

WHAT THIS MODULE IS NOT. It reads no fixture and computes no strategy return: the caller hands it per-candidate
gross and net P&L (in any money unit) and a score. It does not choose thresholds, so selection stays with the
pre-registration. Daily aggregation (Sharpe, drawdown) needs the calendar and stays with the caller.

House style follows `validation/power.py`: stdlib plus numpy, no scipy, every guard raising loudly rather than
returning a sentinel.
"""
from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np

__all__ = [
    "FilterOracleError",
    "average_ranks",
    "spearman",
    "auc",
    "normal_scores",
    "oracle_take",
    "oracle_take_threshold",
    "top_fraction",
    "confusion",
    "capture",
    "calibration",
    "partial_oracle_score",
    "partial_oracle_curve",
    "assess",
]

_ND = NormalDist()


class FilterOracleError(ValueError):
    """An input this module refuses: a length mismatch, a NaN, an out-of-range parameter."""


def _vec(x, name: str) -> np.ndarray:
    a = np.asarray(x, dtype=float)
    if a.ndim != 1:
        raise FilterOracleError(f"{name} must be one-dimensional, got shape {a.shape}")
    if a.size == 0:
        raise FilterOracleError(f"{name} is empty")
    if not np.isfinite(a).all():
        raise FilterOracleError(f"{name} contains {int((~np.isfinite(a)).sum())} non-finite value(s)")
    return a


def _mask(x, name: str) -> np.ndarray:
    a = np.asarray(x)
    if a.dtype != bool:
        raise FilterOracleError(f"{name} must be a boolean mask, got dtype {a.dtype}")
    if a.ndim != 1:
        raise FilterOracleError(f"{name} must be one-dimensional, got shape {a.shape}")
    return a


def _same_length(**arrays) -> int:
    lens = {k: len(v) for k, v in arrays.items()}
    if len(set(lens.values())) != 1:
        raise FilterOracleError(f"length mismatch: {lens}")
    return next(iter(lens.values()))


# ------------------------------------------------------------------ ranks and rank statistics
def average_ranks(x) -> np.ndarray:
    """Ranks 1..n, ties given their average rank."""
    a = _vec(x, "x")
    order = np.argsort(a, kind="mergesort")
    s = a[order]
    ranks = np.empty(a.size)
    ranks[order] = np.arange(1, a.size + 1, dtype=float)
    # average within tie groups
    start = np.flatnonzero(np.concatenate([[True], s[1:] != s[:-1]]))
    stop = np.concatenate([start[1:], [a.size]])
    for b, e in zip(start, stop):
        if e - b > 1:
            ranks[order[b:e]] = 0.5 * (b + 1 + e)
    return ranks


def spearman(a, b) -> float:
    """Spearman's rank correlation (Pearson's on average ranks)."""
    x, y = _vec(a, "a"), _vec(b, "b")
    _same_length(a=x, b=y)
    if x.size < 3:
        raise FilterOracleError("spearman needs at least 3 observations")
    rx, ry = average_ranks(x), average_ranks(y)
    rx -= rx.mean()
    ry -= ry.mean()
    den = math.sqrt(float(rx @ rx) * float(ry @ ry))
    if den == 0:
        raise FilterOracleError("spearman is undefined for a constant input")
    return float(rx @ ry) / den


def auc(score, label) -> float:
    """The area under the ROC curve of `score` for the boolean `label` (Mann-Whitney U / (n1 n0); ties count half)."""
    s = _vec(score, "score")
    lab = _mask(label, "label")
    _same_length(score=s, label=lab)
    n1, n0 = int(lab.sum()), int((~lab).sum())
    if n1 == 0 or n0 == 0:
        raise FilterOracleError(f"auc needs both classes, got {n1} positive and {n0} negative")
    r = average_ranks(s)
    return float((r[lab].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def normal_scores(x) -> np.ndarray:
    """The van der Waerden normal scores: inv_cdf(rank / (n + 1)), average ranks for ties."""
    r = average_ranks(x)
    n = r.size
    return np.array([_ND.inv_cdf(v / (n + 1.0)) for v in r])


# ------------------------------------------------------------------ the oracle and the filters
def oracle_take(net) -> np.ndarray:
    """THE ORACLE FILTER: take a candidate if and only if its realised NET is positive. Hindsight; a ceiling."""
    return _vec(net, "net") > 0


def oracle_take_threshold(gross, cost: float, k: float = 2.0) -> np.ndarray:
    """The oracle at the expected-profit template's bar: take iff the realised GROSS >= k x cost."""
    g = _vec(gross, "gross")
    if not (math.isfinite(cost) and cost >= 0):
        raise FilterOracleError(f"cost must be finite and >= 0, got {cost!r}")
    if not (math.isfinite(k) and k >= 0):
        raise FilterOracleError(f"k must be finite and >= 0, got {k!r}")
    return g >= k * cost


def top_fraction(score, q: float) -> np.ndarray:
    """Keep the top `q` of candidates by score: exactly round(q n) of them (at least one); ties broken by position."""
    s = _vec(score, "score")
    if not (0 < q <= 1):
        raise FilterOracleError(f"q must be in (0, 1], got {q!r}")
    k = max(1, int(round(q * s.size)))
    keep = np.zeros(s.size, dtype=bool)
    keep[np.argsort(-s, kind="mergesort")[:k]] = True
    return keep


# ------------------------------------------------------------------ the accuracy assessment
def confusion(take, label) -> dict:
    """The filter's decisions against the oracle's: counts, precision, recall, F1, accuracy, balanced accuracy."""
    t, lab = _mask(take, "take"), _mask(label, "label")
    _same_length(take=t, label=lab)
    tp = int((t & lab).sum()); fp = int((t & ~lab).sum()); fn = int((~t & lab).sum()); tn = int((~t & ~lab).sum())
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if (tp and prec + rec > 0) else float("nan")
    spec = tn / (tn + fp) if tn + fp else float("nan")
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": prec, "recall": rec, "f1": f1,
            "accuracy": (tp + tn) / t.size, "balanced_accuracy": 0.5 * (rec + spec) if (tp + fn and tn + fp) else float("nan"),
            "base_rate": float(lab.mean()), "take_rate": float(t.mean())}


def capture(net, take) -> dict:
    """The filter's realised net against the oracle's (the ceiling) and against taking everything (no filter)."""
    n = _vec(net, "net")
    t = _mask(take, "take")
    _same_length(net=n, take=t)
    oracle = float(n[n > 0].sum())
    got = float(n[t].sum())
    return {"filter_net": got, "oracle_net": oracle, "take_all_net": float(n.sum()), "trades": int(t.sum()),
            "mean_net_per_trade": float(n[t].mean()) if t.any() else float("nan"),
            "capture_of_oracle": got / oracle if oracle > 0 else float("nan")}


def calibration(projected, realized, n_bins: int = 10) -> dict:
    """Is the projected profit the profit that arrives? Realised means by projected-quantile bin, and the OLS slope and
    intercept of realised on projected (an honest projection has slope 1 and intercept 0)."""
    p, r = _vec(projected, "projected"), _vec(realized, "realized")
    _same_length(projected=p, realized=r)
    if n_bins < 2 or p.size < 2 * n_bins:
        raise FilterOracleError(f"calibration needs n_bins >= 2 and at least 2 per bin, got n_bins {n_bins}, n {p.size}")
    edges = np.quantile(p, np.linspace(0, 1, n_bins + 1)[1:-1])
    b = np.searchsorted(edges, p, side="right")
    bins = [{"bin": int(k), "n": int((b == k).sum()), "mean_projected": float(p[b == k].mean()), "mean_realized": float(r[b == k].mean())}
            for k in range(n_bins) if (b == k).any()]
    pc = p - p.mean()
    vp = float(pc @ pc)
    if vp == 0:
        raise FilterOracleError("calibration is undefined for a constant projection")
    slope = float(pc @ (r - r.mean())) / vp
    return {"bins": bins, "slope": slope, "intercept": float(r.mean() - slope * p.mean())}


def partial_oracle_score(target, rho: float, rng: np.random.Generator) -> np.ndarray:
    """A forecast of `target` with normal-score correlation `rho`: rho z + sqrt(1 - rho^2) e, z the normal scores of the
    target and e independent standard normal. rho = 1 is the oracle's ranking; rho = 0 is a random filter."""
    return _partial(normal_scores(target), rho, rng)


def _partial(z: np.ndarray, rho: float, rng: np.random.Generator) -> np.ndarray:
    if not (0.0 <= rho <= 1.0):
        raise FilterOracleError(f"rho must be in [0, 1], got {rho!r}")
    return rho * z + math.sqrt(1.0 - rho * rho) * rng.standard_normal(z.size)


def partial_oracle_curve(target, net, rhos, q: float, n_draw: int, rng: np.random.Generator) -> list[dict]:
    """For each rho: keep the top `q` of candidates by a partial-oracle forecast of `target`; over `n_draw` draws report
    the kept trades' mean net per trade (mean, p05, p95), their total, their precision against the oracle label, and
    the forecast's realised Spearman correlation with the target (mean). rho = 0 is the null."""
    t, n = _vec(target, "target"), _vec(net, "net")
    _same_length(target=t, net=n)
    if n_draw < 1:
        raise FilterOracleError(f"n_draw must be >= 1, got {n_draw!r}")
    lab = n > 0
    z = normal_scores(t)                                   # hoisted: the same for every draw
    out = []
    for rho in rhos:
        means, totals, precs, sps = [], [], [], []
        for _ in range(n_draw):
            s = _partial(z, float(rho), rng)
            keep = top_fraction(s, q)
            means.append(float(n[keep].mean())); totals.append(float(n[keep].sum()))
            precs.append(float(lab[keep].mean())); sps.append(spearman(s, t))
        means_a = np.array(means)
        out.append({"rho": float(rho), "q": float(q), "n_draw": int(n_draw), "mean_net_per_trade": float(means_a.mean()),
                    "p05": float(np.percentile(means_a, 5)), "p95": float(np.percentile(means_a, 95)),
                    "total_net_mean": float(np.mean(totals)), "precision_mean": float(np.mean(precs)),
                    "realised_spearman_mean": float(np.mean(sps))})
    return out


def assess(score, take, gross, net) -> dict:
    """The accuracy assessment of one real filter, against the oracle filter (net > 0)."""
    s, g, n = _vec(score, "score"), _vec(gross, "gross"), _vec(net, "net")
    t = _mask(take, "take")
    _same_length(score=s, take=t, gross=g, net=n)
    lab = n > 0
    return {"confusion_vs_oracle": confusion(t, lab), "auc_vs_oracle_label": auc(s, lab) if 0 < lab.sum() < lab.size else float("nan"),
            "spearman_score_vs_gross": spearman(s, g) if np.ptp(s) > 0 else float("nan"), "capture": capture(n, t)}
