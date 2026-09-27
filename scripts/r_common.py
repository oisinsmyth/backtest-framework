"""D636's shared statistics for the R-stage runners: the wild cluster bootstrap by year (Webb weights, restricted
null), Holm, the yearly sign test, the calibration CI, the label-shuffle p95 with its bootstrap SE, CLAUDE.md's four
reporting groups, the component line at minimum size, and kappa/SNR from Gate C0's output.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
C0 = REPO / "data" / "index_reweight" / "gate_c0.json"
WEBB = np.array([-math.sqrt(1.5), -1.0, -math.sqrt(0.5), math.sqrt(0.5), 1.0, math.sqrt(1.5)])
BOOT, SEED = 9999, 636
ALPHA = 0.05
# the micro where one exists (Future.from_specs): scale to the micro, and its tick (D636 s.2; CLAUDE.md component line)
MICRO = {"CL": ("MCL", 0.1, 1.0), "NG": ("MNG", 0.1, 1.0), "HG": ("MHG", 0.1, 1.25), "SI": ("SIL", 0.2, 5.0),
         "GC": ("MGC", 0.1, 1.0)}
MICRO_COMMISSION = 4.0


# ------------------------------------------------------------------ kappa and the SNR
def kappa_from_c0(path: Path = C0) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"{path.name} is missing: no R stage runs before Gate C0 (R-D5, D636 s.1)")
    g = json.loads(path.read_text(encoding="utf-8"))
    f = g["flow"]
    return {"separable": bool(f["separable"]), "kappa_B": f["kappa_B"], "kappa_G_per_bn": f["kappa_G_per_bn"],
            "kappa_C": f["kappa_C"], "kappa": f["kappa"], "se": f["se"], "c0_verdict": g["verdict"]["verdict"],
            "c0_passed": g["verdict"]["verdict"] == "PASS"}


def snr(kappa: dict[str, Any], aum: tuple[float, float, float]) -> float:
    """D636 s.3: |kappa| / sqrt(se^2 + (kappa h)^2), h the AUM half-band relative to the point (IR-A5)."""
    h = (aum[2] - aum[1]) / 2 / aum[0]
    k, se = abs(kappa["kappa"]), kappa["se"]
    den = math.sqrt(se ** 2 + (k * h) ** 2)
    return k / den if den > 0 else float("inf")


# ------------------------------------------------------------------ inference
def cluster_t(y: np.ndarray, g: np.ndarray) -> float:
    """The mean's t with CR1 SE clustered by g."""
    n = len(y)
    if n < 2:
        return 0.0
    mu = y.mean()
    _, codes = np.unique(g, return_inverse=True)
    s = np.bincount(codes, weights=y - mu)
    G = len(s)
    if G < 2:
        return 0.0
    se = math.sqrt((s ** 2).sum() * G / (G - 1)) / n
    return float(mu / se) if se > 0 else 0.0


def wild_boot_p(y: np.ndarray, g: np.ndarray, seed: int = SEED, draws: int = BOOT) -> dict[str, float]:
    """One-sided (mean > 0) wild cluster bootstrap by year: Webb six-point weights, restricted null (the restricted
    residual of y = mu + e at mu = 0 is y itself)."""
    t0 = cluster_t(y, g)
    rng = np.random.default_rng(seed)
    groups = np.unique(g)
    pos = np.searchsorted(groups, g)
    hits = 0
    for _ in range(draws):
        w = rng.choice(WEBB, size=len(groups))
        hits += cluster_t(y * w[pos], g) >= t0
    return {"t": t0, "p": (hits + 1) / (draws + 1), "clusters": int(len(groups))}


def holm(ps: dict[str, float]) -> dict[str, float]:
    """Holm-adjusted p-values."""
    order = sorted(ps, key=lambda k: ps[k])
    m, out, run = len(ps), {}, 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, (m - i) * ps[k]))
        out[k] = run
    return out


def binom_p(k: int, n: int) -> float:
    """One-sided P(X >= k) for X ~ Bin(n, 1/2)."""
    return float(stats.binom.sf(k - 1, n, 0.5))


def sign_test(per_year: pd.DataFrame, x: str, y: str, name_col: str = "comp") -> dict[str, Any]:
    """Per year, the Spearman correlation across names of x against y (only names present that year; a year with
    fewer than 4 names casts no vote). PASS when the one-sided binomial p < 0.05."""
    votes = {}
    for yr, g in per_year.groupby("year"):
        g = g.dropna(subset=[x, y])
        if g[name_col].nunique() < 4:
            continue
        votes[int(yr)] = float(stats.spearmanr(g[x], g[y]).statistic)
    n = len(votes)
    k = sum(1 for v in votes.values() if v > 0)
    p = binom_p(k, n) if n else 1.0
    return {"votes": votes, "positive": k, "cast": n, "p": p, "pass": bool(n and p < ALPHA)}


def calibration(real: np.ndarray, pred: np.ndarray, years: np.ndarray, seed: int = SEED) -> dict[str, Any]:
    """The pooled ratio of realised to predicted move, with a 90% CI from a bootstrap over years. PASS when the CI
    overlaps [0.5, 2]."""
    ratio = float(real.sum() / pred.sum()) if pred.sum() else float("nan")
    rng = np.random.default_rng(seed)
    uy = np.unique(years)
    idx = {v: np.flatnonzero(years == v) for v in uy}
    bs = []
    for _ in range(BOOT):
        ii = np.concatenate([idx[v] for v in rng.choice(uy, size=len(uy))])
        if pred[ii].sum():
            bs.append(real[ii].sum() / pred[ii].sum())
    lo, hi = (float(np.quantile(bs, 0.05)), float(np.quantile(bs, 0.95))) if bs else (float("nan"),) * 2
    return {"ratio": ratio, "ci90": [lo, hi], "pass": bool(bs and hi >= 0.5 and lo <= 2.0)}


def p95_with_se(null: np.ndarray, seed: int = SEED) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    p95 = float(np.quantile(null, 0.95))
    bs = [np.quantile(rng.choice(null, size=len(null)), 0.95) for _ in range(1000)]
    return {"p50": float(np.median(null)), "p95": p95, "p95_se": float(np.std(bs, ddof=1))}


def shuffle_verdict(obs: float, null: np.ndarray) -> dict[str, Any]:
    q = p95_with_se(null)
    margin = obs - q["p95"]
    return {**q, "observed": obs, "percentile": float((null < obs).mean()),
            "verdict": "PASS" if margin > 2 * q["p95_se"] else ("UNRESOLVED (margin)" if margin > 0 else "FAIL")}


# ------------------------------------------------------------------ reporting (CLAUDE.md's four groups)
def four_groups(trades: pd.DataFrame, gross_col: str, cost_col: str, per_year_trades: float) -> dict[str, Any]:
    """Performance net and gross (Sharpe and Sortino annualised by the book's own trade count per year), the trade
    distribution with the symmetric trims, and what the winners depend on (years, names)."""
    g = trades[gross_col].to_numpy(float)
    n_ = g - trades[cost_col].to_numpy(float)

    def ratios(x: np.ndarray) -> tuple[float, float]:
        sd = x.std(ddof=1)
        dd = np.sqrt(np.mean(np.minimum(x, 0) ** 2))
        f = math.sqrt(per_year_trades)
        return (float(x.mean() / sd * f) if sd > 0 else float("nan"),
                float(x.mean() / dd * f) if dd > 0 else float("nan"))

    def trims(x: np.ndarray) -> dict[str, float]:
        k = max(1, int(round(0.01 * len(x))))
        s = np.sort(x)
        return {"ex_top_1pct": float(s[:-k].mean()), "ex_bottom_1pct": float(s[k:].mean()),
                "trimmed_both": float(s[k:-k].mean()) if len(s) > 2 * k else float("nan")}

    sg, sog = ratios(g)
    sn, son = ratios(n_)
    wins, losses = n_[n_ > 0], n_[n_ < 0]
    by_year = trades.assign(net=n_).groupby("year")["net"]
    by_name = trades.assign(net=n_).groupby("comp")["net"].sum().sort_values(ascending=False)
    total = float(by_name.sum())
    cum = by_name.cumsum()
    return {
        "performance": {"trades": int(len(g)), "mean_gross": float(g.mean()), "mean_net": float(n_.mean()),
                        "sharpe_gross": sg, "sortino_gross": sog, "sharpe_net": sn, "sortino_net": son,
                        "breakeven_cost": float(g.mean()), "mean_move_over_cost": float(g.mean() / trades[cost_col].mean()),
                        "trades_per_year": per_year_trades},
        "distribution": {"median_net": float(np.median(n_)), "win_rate": float((n_ > 0).mean()),
                         "payoff": float(wins.mean() / -losses.mean()) if len(wins) and len(losses) else float("nan"),
                         "skew": float(stats.skew(n_)), "excess_kurtosis": float(stats.kurtosis(n_)), **trims(n_)},
        "depends": {"profitable_years": int((by_year.sum() > 0).sum()), "years": int(by_year.ngroups),
                    "by_year_mean_net": {int(k): round(float(v), 2) for k, v in by_year.mean().items()},
                    "median_year_mean_net": float(by_year.mean().median()),
                    "names_for_half_the_pnl": int((cum < total / 2).sum() + 1) if total > 0 else None,
                    "top1_top5_share": [float(by_name.iloc[:1].sum() / total), float(by_name.iloc[:5].sum() / total)]
                    if total > 0 else None},
    }


def component_line(trades: pd.DataFrame, gross_col: str, per_year_trades: float) -> dict[str, Any]:
    """Net at the minimum tradable size: the micro where one exists (scale and tick), else the full contract at its
    own cost."""
    net = []
    for r in trades.itertuples():
        root = r.root
        if root in MICRO:
            _, scale, tick = MICRO[root]
            net.append(getattr(r, gross_col) * scale - (MICRO_COMMISSION + tick))
        else:
            net.append(getattr(r, gross_col) - r.cost_usd)
    x = np.array(net)
    sd = x.std(ddof=1)
    return {"mean_net": float(x.mean()), "hit_rate": float((x > 0).mean()), "skew": float(stats.skew(x)),
            "sharpe_net": float(x.mean() / sd * math.sqrt(per_year_trades)) if sd > 0 else float("nan"),
            "micros": {k: v[0] for k, v in MICRO.items()}, "micro_cost": f"${MICRO_COMMISSION:.0f} + one micro tick"}


def adoption(pooled: bool, sign: bool, calib: bool | None) -> bool:
    """Deposit s.8B.2 (unit test 25): pooled AND sign test AND (for R1) calibration."""
    return bool(pooled and sign and (calib if calib is not None else True))


def design_effect(n: int, m: float, rho: float) -> float:
    """Deposit unit test 21: n_eff = n / (1 + (m - 1) rho)."""
    return n / (1 + (m - 1) * rho)


def consistency_2027(value: float, interval: tuple[float, float], track1_years: list[int]) -> bool:
    """Deposit s.11 v1.3 (unit test 27): the forward event must fall within the Track 1 interval with the same sign.
    The interval must come from 2016-2025 only."""
    if any(y < 2016 or y > 2025 for y in track1_years):
        raise ValueError("the consistency interval must be computed from 2016-2025 only")
    return bool(interval[0] <= value <= interval[1] and np.sign(value) == np.sign(sum(interval) / 2))


def track3_counts_as_evidence(_: Any) -> bool:
    """Deposit unit test 28: Track 3 (live-small) January trades are never independent efficacy evidence."""
    return False


def unit_tests() -> list[str]:
    done = []
    assert abs(binom_p(9, 10) - 0.0107) < 1e-3 and binom_p(9, 10) < ALPHA and binom_p(8, 10) > ALPHA
    assert abs(binom_p(8, 10) - 0.0547) < 1e-3
    done.append("22")
    assert binom_p(9, 11) < ALPHA and abs(binom_p(9, 11) - 0.0327) < 1e-3 and binom_p(8, 11) > ALPHA
    done.append("26")
    assert abs(design_effect(750, 75, 0.5) - 750 / 38) < 1e-9
    done.append("21")
    df = pd.DataFrame({"year": [2016] * 5, "comp": list("abcde"), "x": [1, 2, 3, 4, np.nan], "y": [1, 2, 3, 4, 9]})
    assert sign_test(df, "x", "y")["votes"][2016] == 1.0  # the untraded name (x missing) is left out
    done.append("23")
    c = calibration(np.array([1.0, 1.1, 0.9] * 4), np.array([1.0] * 12), np.repeat(np.arange(4), 3))
    assert c["pass"] and not calibration(np.array([5.0] * 12), np.ones(12), np.repeat(np.arange(4), 3))["pass"]
    done.append("24")
    assert adoption(True, True, True) and not adoption(True, False, True) and not adoption(True, True, False)
    done.append("25")
    try:
        consistency_2027(0.1, (0.0, 0.2), [2016, 2026])
        raise AssertionError("test 27 did not fire")
    except ValueError:
        pass
    done.append("27")
    assert not track3_counts_as_evidence(object())
    done.append("28")
    h = holm({"A": 0.01, "B": 0.04})
    assert h["A"] == 0.02 and h["B"] == 0.04
    return done
