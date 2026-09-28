"""D642 runner: the shock classifier's signal frame, Phases 3-4 (event-study curves, H1, H2, H3, H4, robustness), with
SC-A1..A8. Written after D642 (0768da5) and committed BEFORE its one run.

    python scripts/run_shock_signal.py --selftest     # SYSTEM interpreter (pyarrow); every audit fires on a broken input
    python scripts/run_shock_signal.py --dry-run      # synthetic prices on the sessions' calendar; writes nothing
    python scripts/run_shock_signal.py --run          # ONCE -> data/shock/phase3_signal.json + data/shock/trials.csv
    python scripts/run_shock_signal.py --check        # the rebuild equals the committed output

In-sample 2016-01-04 -> 2025-02-28 on SC-A6's usable sessions; nothing on or after 2025-03-01 is read (A10). The book
frame (Phase 5) is not here: it runs only past Gate 2, under its own pre-registration.

Conventions fixed here, before the run (D642 leaves them open):
- H1's one-sided p is from Student's t with G - 1 degrees of freedom, G the number of day clusters (CR1).
- SC-A2's "class - baseline" is the class-vs-rest clustered regression scaled by (1 - n_class / N): the baseline is
  all z = 4 shocks and includes the class itself; the t is the regression's.
- A shock whose curve (k = 0..60) has a missing price is kept for x and left out of the curves; both are counted.
- The dry run replaces every price and volume with a synthetic walk on the usable-session calendar and never loads a
  real price. Re-detection reads prices, so it runs only in --run and --check.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from backtest_framework.shock import model as M  # noqa: E402
from backtest_framework.validation.programme import TrialsCsv  # noqa: E402

_s = importlib.util.spec_from_file_location("build_shock_phase2", REPO / "scripts" / "build_shock_phase2.py")
assert _s is not None and _s.loader is not None
P2 = importlib.util.module_from_spec(_s)
sys.modules["build_shock_phase2"] = P2
_s.loader.exec_module(P2)

SH = REPO / "data" / "shock"
OUT = SH / "phase3_signal.json"
TRIALS = SH / "trials.csv"
SPEC = REPO / "docs" / "decisions" / "D642-PRE-REG-shock-classifier-signal-frame-h1-h4.md"
AMEND = REPO / "docs" / "internal" / "SHOCK_CLASSIFIER_AMENDMENTS.md"
TRADED = ("NQ", "ES", "CL", "GC")
USD_PER_POINT = {"NQ": 2.0, "ES": 5.0, "CL": 100.0, "GC": 10.0}  # MNQ, MES, MCL, MGC
# s.5.1 at one micro: D508's default crossing + $3 commission + one adverse tick (power_shock.py's COST, in dollars)
COST_USD = {r: 3.0 + x * t + t for r, (x, t) in {"NQ": (2.1342, 0.5), "ES": (1.1345, 1.25), "CL": (2.0312, 1.0),
                                                 "GC": (2.9335, 1.0)}.items()}
DRY_LEVEL = {"NQ": 10000.0, "ES": 3000.0, "CL": 60.0, "GC": 1500.0}
HOLD, K_MAX = 30, 60
B_BOOT, N_PERM, B_P95, SEED = 9999, 1000, 2000, 642
POWER_LABEL = {"NQ": "UNDERPOWERED", "ES": "UNDERPOWERED", "CL": "UNDERPOWERED", "GC": "powered at t=2"}
SPLIT = "2024-01-01"
ALPHA = 0.05
FAMILY, DOC = "shock classifier H1", "SHOCK_CLASSIFIER_PREREG.md"


class ShockRunError(RuntimeError):
    pass


# ============================================================================================== the audits
def check_counts(shocks: pd.DataFrame, committed: dict) -> None:
    """Lag audit (i): the shocks' z = 4 class counts must equal D641's committed counts."""
    prim = shocks[shocks["z"] == 4.0]
    got = prim.groupby(["root", "class_primary"]).size().unstack(fill_value=0).to_dict("index")
    got = {r: {k: int(v) for k, v in c.items()} for r, c in got.items()}
    if got != committed:
        raise ShockRunError(f"lag audit: the shocks do not reproduce D641's committed counts: {got}")


def classify_second(C: float, event: bool, c_hi: float, c_lo: float) -> str:
    """Lag audit (ii): a SECOND implementation of s.4.6, never calling shock.model.classify."""
    if C != C:  # NaN: fewer than two valid peers
        return "NONE"
    if C >= c_hi:
        return "INFO"
    if event and C >= 0.3:
        return "INFO"
    if (not event) and C <= c_lo:
        return "LIQ"
    return "NONE"


def check_classes(shocks: pd.DataFrame) -> None:
    for k, (hi, lo) in P2.C_PAIRS.items():
        second = [classify_second(c, bool(e), hi, lo) for c, e in zip(shocks["C"], shocks["event"])]
        bad = int(sum(a != b for a, b in zip(second, shocks[f"class_{k}"])))
        if bad:
            raise ShockRunError(f"lag audit: the second classification disagrees on {bad} shocks ({k})")


def outcome_index(i: int) -> dict[str, list[int]]:
    """The grid columns each outcome reads for a shock at column i. c_k's anchor P[b] is column i itself (t0, the
    shock bar's close, known when the shock is); every OTHER price is strictly after it."""
    return {"fill": [i + 1], "exit": [i + 1 + HOLD], "curve": list(range(i + 1, i + K_MAX + 1)),
            "stress": list(range(i + 1, i + 6))}


def check_after(i: int, idx: dict[str, list[int]]) -> None:
    """Lag audit (iii): every price read for x or c_k (beyond c_k's anchor) is at a column strictly after the shock's."""
    for name, cols in idx.items():
        if not cols or min(cols) <= i:
            raise ShockRunError(f"lag audit: {name} reads a price at or before the shock bar (col {i}): {cols[:3]}")


def pnl_bp(D: int, fill: float, ex: float) -> float:
    """The trade's P&L in bp of the fill, in the trade direction D."""
    return D * (ex / fill - 1) * 1e4


def x_bp(d: int, fill: float, ex: float) -> float:
    """H1's x: the same move in the SHOCK direction d."""
    return d * (ex / fill - 1) * 1e4


def audit_money(pnl: Callable = pnl_bp, xf: Callable = x_bp, td: Callable = M.trade_direction) -> None:
    """Money: a favourable move pays long and short; x > 0 on a continuation and < 0 on a reversion, for either shock
    sign; each class's trade is paid by the move it predicts."""
    if not (pnl(1, 100.0, 101.0) > 0 and pnl(-1, 100.0, 99.0) > 0 and pnl(1, 100.0, 99.0) < 0):
        raise ShockRunError("money audit: a favourable move did not pay")
    for d, cont, rev in ((1, 101.0, 100.0), (-1, 100.0, 101.0)):
        if not (xf(d, 100.5, cont) > 0 > xf(d, 100.5, rev)):
            raise ShockRunError("money audit: x's sign convention")
        if not pnl(td("LIQ", d), 100.5, rev) > 0 or not pnl(td("INFO", d), 100.5, cont) > 0:
            raise ShockRunError("money audit: a class's trade is not paid by the move it predicts")


def check_right_quantity(x: np.ndarray, x_t0: np.ndarray, d_liq: np.ndarray, td: Callable = M.trade_direction) -> None:
    if len(x) and np.array_equal(x, x_t0):
        raise ShockRunError("right quantity: x from the t0+1 fill equals the move from the t0 close")
    D = np.array([td("LIQ", int(v)) for v in d_liq])
    if len(d_liq) and not (D != d_liq).all():
        raise ShockRunError("right quantity: a LIQ shock's shock direction equals its trade direction")


# ============================================================================================== data
def committed_counts() -> dict:
    return json.loads((SH / "phase2_counts.json").read_text(encoding="utf-8"))["per_root_class"]


def load_real(days: list[str]) -> tuple[pd.DataFrame, dict[str, np.ndarray], dict[str, np.ndarray], dict]:
    """Re-detect every shock from the D641 grids (lag audit), compare with D641's file, and return the traded grids."""
    roots = sorted(set(P2.PEERS) | {p for v in P2.PEERS.values() for p in v})
    G = P2.grids(roots, days)
    t = time.time()
    shocks, _ = P2.detect_all(days, G)
    note: dict[str, Any] = {"redetect_min": round((time.time() - t) / 60, 1)}
    check_counts(shocks, committed_counts())
    f = SH / "phase2_shocks.csv.gz"
    if f.exists():
        # byte for byte, serialised exactly as D641 wrote it (its CSV carries ~16 significant digits, so a frame read
        # back from it differs from the in-memory rebuild in the last digit; the first --run tripped on that)
        with gzip.open(f, "rt", encoding="utf-8", newline="") as h:
            disk = h.read()
        if shocks.to_csv(index=False, lineterminator="\n") != disk:
            raise ShockRunError("lag audit: the re-detected shocks differ from D641's phase2_shocks.csv.gz")
        note["equals_phase2_file_bytes"] = True
    GA = {r: G[r].to_numpy(float) for r in TRADED}
    return shocks, GA, volume_grids(days), note


def load_dry(days: list[str]) -> tuple[pd.DataFrame, dict[str, np.ndarray], dict[str, np.ndarray], dict]:
    """The shocks from D641's file (checked against its counts) and SYNTHETIC prices and volumes on the calendar."""
    shocks = pd.read_csv(SH / "phase2_shocks.csv.gz", encoding="utf-8", dtype={"day": str})
    check_counts(shocks, committed_counts())
    rng = np.random.default_rng(7)
    shape = (len(days), len(P2.MINUTES))
    GA = {r: DRY_LEVEL[r] * np.exp(np.cumsum(rng.normal(0, 3e-4, shape), axis=1)) for r in TRADED}
    V = {r: rng.lognormal(5, 1, shape) for r in TRADED}
    return shocks, GA, V, {"dry_run": "synthetic prices; re-detection skipped (it reads real prices)"}


def volume_grids(days: list[str]) -> dict[str, np.ndarray]:
    """Per traded root, the (session x minute) volume grid, for the liquidity-regime diagnostic only (s.5)."""
    f = (ds.field("day") >= P2.WARM) & (ds.field("day") < P2.RESERVED_FROM) & ds.field("root").isin(list(TRADED))
    t = ds.dataset(P2.DAY1M).to_table(columns=["root", "day", "bar", "volume", "present"], filter=f).to_pandas()
    t = t[t["present"]]
    t["hhmm"] = (pd.Timestamp("2000-01-01 09:00") + pd.to_timedelta(t["bar"], unit="m")).dt.strftime("%H:%M")
    pre = pd.read_csv(P2.PRE, encoding="utf-8", dtype={"day": str})
    pre = pre[(pre["day"] >= P2.WARM) & (pre["day"] < P2.RESERVED_FROM) & pre["front"] & (pre["root"] == "GC")]
    if (t["day"] >= P2.RESERVED_FROM).any() or (pre["day"] >= P2.RESERVED_FROM).any():
        raise ShockRunError("a sealed session reached the runner")
    out = {}
    for r in TRADED:
        a = t.loc[t["root"] == r, ["day", "hhmm", "volume"]]
        if r == "GC":
            a = pd.concat([a, pre[["day", "hhmm", "volume"]]])
        out[r] = a.pivot_table(index="day", columns="hhmm", values="volume", aggfunc="first").reindex(
            index=days, columns=P2.MINUTES).to_numpy(float)
    return out


def outcomes(sh: pd.DataFrame, GA: dict[str, np.ndarray], V: dict[str, np.ndarray], days: list[str]) -> pd.DataFrame:
    """Per shock: x (shock direction, t0+1 fill, 30-minute exit), the trade-direction P&L, the stress-fill x, the
    curve c_0..c_60 in the trade direction (the shock direction for NONE), the cost in bp and the volume ratio."""
    pos = {m: i for i, m in enumerate(P2.MINUTES)}
    dpos = {d: k for k, d in enumerate(days)}
    vmed = {r: pd.DataFrame(V[r]).rolling(60, min_periods=60).median().shift(1).to_numpy(float) for r in TRADED}
    recs, keep = [], []
    for n, s in enumerate(sh.itertuples(index=False)):
        g = GA[s.root][dpos[s.day]]
        i = pos[s.bar]
        idx = outcome_index(i)
        check_after(i, idx)
        if idx["exit"][0] >= len(g) or not (np.isfinite(g[idx["fill"][0]]) and np.isfinite(g[idx["exit"][0]])):
            continue
        cls, d = s.class_primary, int(s.d)
        D = M.trade_direction(cls, d) or d  # NONE does not trade: its curve is in the shock direction
        fill, ex = g[idx["fill"][0]], g[idx["exit"][0]]
        cv = D * (g[i:i + K_MAX + 1] / g[i] - 1) * 1e4 if i + K_MAX < len(g) else np.full(K_MAX + 1, np.nan)
        sf = M.stress_fill(g[idx["stress"]], D)
        k = dpos[s.day]
        v, vm = V[s.root][k, i], vmed[s.root][k, i]
        recs.append((x_bp(d, fill, ex), pnl_bp(D, fill, ex), x_bp(d, sf, ex), x_bp(d, g[i], ex),
                     COST_USD[s.root] / USD_PER_POINT[s.root] / fill * 1e4, fill,
                     v / vm if np.isfinite(v) and np.isfinite(vm) and vm > 0 else np.nan, cv))
        keep.append(n)
    out = sh.iloc[keep].reset_index(drop=True).copy()
    for c, col in enumerate(("x", "pnl", "x_stress", "x_t0", "cost_bp", "fill", "vol_ratio")):
        out[col] = np.array([r[c] for r in recs], dtype=float)
    out["curve"] = [r[7] for r in recs]
    out["curve_ok"] = [bool(np.all(np.isfinite(r[7]))) for r in recs]
    out.attrs["dropped_no_exit"] = int(len(sh) - len(out))
    return out


# ============================================================================================== statistics
# The system interpreter (pyarrow) has no scipy, so the four scipy functions used are written here, each checked in
# --selftest against values scipy produces: rankdata(method="average"), spearmanr, skew / kurtosis (bias=True, Fisher)
# and Student's t survival function.
def rank_avg(a: np.ndarray) -> np.ndarray:
    """Average ranks (1-based), ties sharing the mean of their positions: scipy.stats.rankdata's 'average'."""
    sorter = np.argsort(a, kind="mergesort")
    inv = np.empty(len(a), dtype=np.intp)
    inv[sorter] = np.arange(len(a))
    s = a[sorter]
    obs = np.r_[True, s[1:] != s[:-1]]
    dense = obs.cumsum()[inv]
    count = np.r_[np.nonzero(obs)[0], len(obs)]
    return 0.5 * (count[dense] + count[dense - 1] + 1)


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra, rb = rank_avg(a), rank_avg(b)
    ra, rb = ra - ra.mean(), rb - rb.mean()
    den = math.sqrt(float((ra * ra).sum() * (rb * rb).sum()))
    return float((ra * rb).sum() / den) if den > 0 else float("nan")


def skew(v: np.ndarray) -> float:
    d = v - v.mean()
    return float((d ** 3).mean() / (d ** 2).mean() ** 1.5)


def kurtosis(v: np.ndarray) -> float:
    d = v - v.mean()
    return float((d ** 4).mean() / (d ** 2).mean() ** 2 - 3.0)


def _betacf(a: float, b: float, x: float) -> float:
    """The continued fraction of the regularized incomplete beta (Lentz; Numerical Recipes 6.4)."""
    tiny, qab, qap, qam = 1e-300, a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 10001):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        de = d * c
        h *= de
        if abs(de - 1.0) < 1e-15:
            return h
    raise ShockRunError("the incomplete beta did not converge")


def betainc(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lb = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(lb) * _betacf(a, b, x) / a
    return 1.0 - math.exp(lb) * _betacf(b, a, 1.0 - x) / b


def t_sf(t: float, df: float) -> float:
    """P(T > t) for Student's t with df degrees of freedom."""
    tail = 0.5 * betainc(df / 2.0, 0.5, df / (df + t * t))
    return tail if t >= 0 else 1.0 - tail


def cluster_ols(x: np.ndarray, ind: np.ndarray, day: np.ndarray) -> dict[str, float]:
    """OLS of x on [1, ind] with CR1 day-clustered SE; one-sided p (coef > 0) from t with G - 1 df."""
    X = np.column_stack([np.ones(len(x)), ind.astype(float)])
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ X.T @ x
    e = x - X @ beta
    _, inv = np.unique(day, return_inverse=True)
    G = int(inv.max()) + 1
    sc = np.column_stack([np.bincount(inv, weights=X[:, j] * e, minlength=G) for j in range(2)])
    meat = sc.T @ sc
    n = len(x)
    Vc = xtx_inv @ meat @ xtx_inv * G / (G - 1) * (n - 1) / (n - 2)
    se = math.sqrt(Vc[1, 1])
    t = float(beta[1] / se)
    return {"coef_bp": float(beta[1]), "se_bp": se, "t": t, "p_one_sided": t_sf(t, G - 1), "clusters": G}


def cluster_ols_loop(x: np.ndarray, ind: np.ndarray, day: np.ndarray) -> float:
    """The clustered SE by an explicit per-day loop (a check on the bincount rewrite)."""
    X = np.column_stack([np.ones(len(x)), ind.astype(float)])
    xtx_inv = np.linalg.inv(X.T @ X)
    e = x - X @ (xtx_inv @ X.T @ x)
    meat = np.zeros((2, 2))
    groups = pd.Series(np.arange(len(x))).groupby(day).indices
    for ix in groups.values():
        s = X[ix].T @ e[ix]
        meat += np.outer(s, s)
    G, n = len(groups), len(x)
    return math.sqrt((xtx_inv @ meat @ xtx_inv * G / (G - 1) * (n - 1) / (n - 2))[1, 1])


class DayBoot:
    """Day-block bootstrap: B resamples of the session days with replacement; a mean is a ratio of weighted day sums."""

    def __init__(self, day: np.ndarray, rng: np.random.Generator, B: int = B_BOOT):
        self.uniq, self.inv = np.unique(day, return_inverse=True)
        D = len(self.uniq)
        self.W = np.stack([np.bincount(rng.integers(0, D, D), minlength=D) for _ in range(B)]).astype(np.float64)

    def means(self, vals: np.ndarray, mask: np.ndarray) -> np.ndarray:
        v, inv, D = vals[mask], self.inv[mask], len(self.uniq)
        N = self.W @ np.bincount(inv, minlength=D).astype(float)
        if v.ndim == 1:
            return (self.W @ np.bincount(inv, weights=v, minlength=D)) / N
        S = np.stack([np.bincount(inv, weights=v[:, j], minlength=D) for j in range(v.shape[1])], axis=1)
        return (self.W @ S) / N[:, None]


def spearman_boot(C: np.ndarray, x: np.ndarray, day: np.ndarray, rng: np.random.Generator) -> dict[str, Any]:
    """Spearman rho(C, x) with a day-block-bootstrap 95% CI."""
    rho = spearman(C, x)
    order = np.argsort(day, kind="stable")
    C, x, day = C[order], x[order], day[order]
    _, starts, lens = np.unique(day, return_index=True, return_counts=True)
    G = len(starts)
    bs = np.empty(B_BOOT)
    for b in range(B_BOOT):
        pick = rng.integers(0, G, G)
        L = lens[pick]
        idx = np.repeat(starts[pick] - np.cumsum(L) + L, L) + np.arange(L.sum())
        bs[b] = spearman(C[idx], x[idx])
    return {"n": int(len(x)), "spearman": rho, "ci95": [float(np.nanquantile(bs, 0.025)), float(np.nanquantile(bs, 0.975))]}


def dist(v: np.ndarray) -> dict[str, Any]:
    v = v[np.isfinite(v)]
    if len(v) < 3:
        return {"n": int(len(v))}
    lo, hi = np.quantile(v, [0.01, 0.99])
    return {"n": int(len(v)), "mean": float(v.mean()), "median": float(np.median(v)), "win": float((v > 0).mean()),
            "skew": skew(v), "kurtosis": kurtosis(v), "mean_ex_top1": float(v[v <= hi].mean()),
            "mean_ex_bottom1": float(v[v >= lo].mean()), "mean_trimmed_both": float(v[(v >= lo) & (v <= hi)].mean())}


def holm(p: dict[str, float]) -> dict[str, float]:
    keys = sorted(p, key=lambda k: p[k])
    m, out, run = len(keys), {}, 0.0
    for i, k in enumerate(keys):
        run = max(run, min(1.0, (m - i) * p[k]))
        out[k] = run
    return out


def h1_frame(sub: pd.DataFrame, cls_col: str, xcol: str) -> dict[str, Any]:
    ab = sub[sub[cls_col].isin(["INFO", "LIQ"])]
    ni, nl = int((ab[cls_col] == "INFO").sum()), int((ab[cls_col] == "LIQ").sum())
    if ni < 3 or nl < 3:
        return {"n_info": ni, "n_liq": nl, "note": "fewer than 3 in a class"}
    cd = cluster_ols(ab[xcol].to_numpy(float), (ab[cls_col] == "INFO").to_numpy(), ab["day"].to_numpy())
    return {"delta_bp": cd.pop("coef_bp"), **cd, "n_info": ni, "n_liq": nl,
            "mean_info_x_bp": float(ab.loc[ab[cls_col] == "INFO", xcol].mean()),
            "mean_liq_x_bp": float(ab.loc[ab[cls_col] == "LIQ", xcol].mean()),
            "reads_2024_plus": bool((ab["day"] >= SPLIT).any())}


def h3_verdict(obs: float, p95: float, se: float) -> str:
    m = obs - p95
    return "PASS" if m > 2 * se else ("FAIL" if m < -2 * se else "UNRESOLVED")


# ============================================================================================== build
def build(dry: bool = False) -> tuple[dict[str, Any], list[dict]]:
    t_start = time.time()
    days = P2.usable_sessions()
    sh, GA, V, note = load_dry(days) if dry else load_real(days)
    if (sh["day"] >= P2.RESERVED_FROM).any():
        raise ShockRunError("a sealed shock reached the runner")
    check_classes(sh)
    audit_money()
    o = outcomes(sh, GA, V, days)
    prim = o[o["z"] == 4.0].reset_index(drop=True)
    check_right_quantity(prim["x"].to_numpy(), prim["x_t0"].to_numpy(),
                         prim.loc[prim["class_primary"] == "LIQ", "d"].to_numpy(int))
    rng = np.random.default_rng(SEED)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    doc: dict[str, Any] = {"spec": "D642 (0768da5) with SC-A1..A8; D641; POWER 2f6a2b3", "cost_usd_one_micro": COST_USD,
                           "dropped_no_exit_all_z": o.attrs["dropped_no_exit"],
                           "curves_left_out_missing_price_z4": int((~prim["curve_ok"]).sum()),
                           "n_z4_after_drops": {r: {k: int(v) for k, v in c.items()} for r, c in prim.groupby(
                               ["root", "class_primary"]).size().unstack(fill_value=0).to_dict("index").items()},
                           "reads": note, "instruments": {}}
    trials: list[dict] = []
    p_h1 = {}
    for r in TRADED:
        a = prim[prim["root"] == r].reset_index(drop=True)
        day = a["day"].to_numpy()
        cls = a["class_primary"].to_numpy()
        xs = a["x"].to_numpy(float)
        boot = DayBoot(day, rng)
        # --- event-study curves (produced first)
        cm = a["curve_ok"].to_numpy()
        CV = np.stack([c if ok else np.zeros(K_MAX + 1) for c, ok in zip(a["curve"], cm)])
        curves = {}
        for c in ("INFO", "LIQ", "NONE", "ALL"):
            m = cm & (np.ones(len(a), bool) if c == "ALL" else cls == c)
            if m.sum() < 3:
                curves[c] = {"n": int(m.sum())}
                continue
            bd = boot.means(CV, m)
            curves[c] = {"n": int(m.sum()), "mean_bp": CV[m].mean(axis=0).tolist(),
                         "ci95_lo": np.quantile(bd, 0.025, axis=0).tolist(), "ci95_hi": np.quantile(bd, 0.975, axis=0).tolist(),
                         "direction": "trade" if c in ("INFO", "LIQ") else "shock (NONE does not trade; ALL mixes)"}
        # --- H1
        h1 = h1_frame(a, "class_primary", "x")
        p_h1[r] = h1["p_one_sided"]
        vs_base = {}
        for c in ("INFO", "LIQ"):
            ind = cls == c
            cr = cluster_ols(xs, ind, day)
            vs_base[c] = {"class_minus_baseline_bp": cr["coef_bp"] * (1 - ind.mean()), "class_minus_rest_bp": cr["coef_bp"],
                          "t": cr["t"], "n_class": int(ind.sum()), "n_baseline": int(len(xs))}
        h1.update({"power": POWER_LABEL[r], "vs_baseline_SC_A2": vs_base, "baseline_mean_x_bp": float(xs.mean()),
                   "n_liq_2024_plus": int(((cls == "LIQ") & (day >= SPLIT)).sum())})
        # --- H2 (every class reported; the gate reads the H1-passing instruments)
        h2 = {}
        for c in ("INFO", "LIQ"):
            if "mean_bp" not in curves[c]:
                h2[c] = {"note": "fewer than 3 shocks with a full curve"}
                continue
            cv = np.array(curves[c]["mean_bp"])
            ks = int(np.argmax(cv))
            h2[c] = {"k_star": ks, "c_k_star_bp": float(cv[ks]), "c_5_bp": float(cv[5]),
                     "pass": bool(ks > 5 and cv[ks] > 0 and cv[5] <= 0.5 * cv[ks]),
                     "delay_cost": {"captured_from_t0_bp": float(cv[ks]), "captured_from_t0_plus_5_bp": float(cv[ks] - cv[5])}}
        # --- H3: INFO/LIQ labels permuted within calendar year
        ab = (cls == "INFO") | (cls == "LIQ")
        lab, yr, xv = (cls[ab] == "INFO"), a.loc[ab, "day"].str[:4].to_numpy(), xs[ab]
        obs = float(xv[lab].mean() - xv[~lab].mean())
        yidx = [np.where(yr == y)[0] for y in np.unique(yr)]
        perm = np.empty(N_PERM)
        for p in range(N_PERM):
            L = lab.copy()
            for ix in yidx:
                L[ix] = rng.permutation(lab[ix])
            perm[p] = xv[L].mean() - xv[~L].mean()
        p95 = float(np.quantile(perm, 0.95))
        se95 = float(np.std([np.quantile(rng.choice(perm, N_PERM), 0.95) for _ in range(B_P95)], ddof=1))
        h3 = {"observed_bp": obs, "p50_bp": float(np.median(perm)), "p95_bp": p95, "se_of_p95_bp": se95,
              "margin_bp": obs - p95, "rank": float((perm < obs).mean()), "verdict": h3_verdict(obs, p95, se95)}
        # --- H4 per instrument (pooled below)
        h4: dict[str, Any] = {c: spearman_boot(a.loc[cls == c, "C"].to_numpy(float), xs[cls == c], day[cls == c], rng)
                              for c in ("INFO", "LIQ") if (cls == c).sum() >= 5}
        h4["pass"] = bool(all(h4.get(c, {}).get("spearman", -1.0) > 0 for c in ("INFO", "LIQ")))
        # --- distributions per class: the trade direction for INFO/LIQ, gross and net, bp and $ at one micro
        groups = {}
        for c in ("INFO", "LIQ", "NONE", "ALL"):
            m = np.ones(len(a), bool) if c == "ALL" else cls == c
            y = a.loc[m, "pnl"].to_numpy(float) if c in ("INFO", "LIQ") else xs[m]
            cb, fl, dd = a.loc[m, "cost_bp"].to_numpy(float), a.loc[m, "fill"].to_numpy(float), day[m]
            usd = y / 1e4 * fl * USD_PER_POINT[r]
            groups[c] = {"direction": "trade" if c in ("INFO", "LIQ") else "shock (not traded)",
                         "gross_bp": dist(y), "net_bp": dist(y - cb), "net_2x_bp": dist(y - 2 * cb),
                         "gross_usd": dist(usd), "net_usd": dist(usd - COST_USD[r]),
                         "mean_cost_bp": float(cb.mean()) if m.any() else None,
                         "mean_gross_bp_2016_2023": float(y[dd < SPLIT].mean()) if (dd < SPLIT).any() else None,
                         "mean_gross_bp_2024_plus": float(y[dd >= SPLIT].mean()) if (dd >= SPLIT).any() else None,
                         "by_year": {str(yy): {"n": int(len(g)), "mean_gross_bp": float(g.mean())}
                                     for yy, g in pd.Series(y, index=pd.Index(dd).str[:4]).groupby(level=0)}}
            if c in ("INFO", "LIQ"):
                for mult in (1, 2):
                    trials.append(trial(f"{r}_{c}_signal_net_cost{mult}x", r, c, 4.0, "1+3", 0.6, 0.2, "time30", "t0+1",
                                        mult, "none", int(m.sum()), float(y.mean()), float((y - mult * cb).mean()), None,
                                        bool((dd >= SPLIT).any()), "sensitivity: the class's signal-frame return net of cost"))
        doc["instruments"][r] = {"curves": curves, "H1": h1, "H2": h2, "H3": h3, "H4": h4, "groups": groups}
    # H4 pooled across the four instruments, blocks by day
    pooled: dict[str, Any] = {}
    for c in ("INFO", "LIQ"):
        q = prim[prim["class_primary"] == c]
        pooled[c] = spearman_boot(q["C"].to_numpy(float), q["x"].to_numpy(float), q["day"].to_numpy(), rng)
    pooled["pass"] = bool(all(pooled[c]["spearman"] > 0 for c in ("INFO", "LIQ")))
    doc["H4_pooled"] = pooled
    adj = holm(p_h1)
    for r in TRADED:
        h = doc["instruments"][r]["H1"]
        h["p_holm"] = adj[r]
        h["signs_ok"] = bool(h["mean_info_x_bp"] > 0 and h["mean_liq_x_bp"] < 0)
        h["pass"] = bool(adj[r] < ALPHA and h["t"] >= 2 and h["signs_ok"])
        h["verdict"] = "PASS" if h["pass"] else ("INCONCLUSIVE (underpowered, s.7A)" if POWER_LABEL[r] == "UNDERPOWERED" else "FAIL")
        trials.insert(TRADED.index(r), trial(f"{r}_H1_primary", r, "INFO-LIQ", 4.0, "1+3", 0.6, 0.2, "time30", "t0+1", 0,
                                             "none", h["n_info"] + h["n_liq"], h["delta_bp"], None, h["t"],
                                             h["reads_2024_plus"], f"PRIMARY H1 (one of four); p_holm={adj[r]:.6g}"))
    doc["robustness"] = robustness(o, trials)
    g1 = [r for r in TRADED if doc["instruments"][r]["H1"]["pass"]
          and any(v.get("pass") for v in doc["instruments"][r]["H2"].values())]
    g2 = [r for r in g1 if doc["instruments"][r]["H3"]["verdict"] == "PASS"]
    doc["gates"] = {"gate1_instruments": g1, "gate1": bool(g1), "gate2_instruments": g2, "gate2": bool(g2),
                    "verdict": ("GATE 1 FAILED: STOP -> write-up" if not g1 else
                                "GATE 2 FAILED: STOP -> write-up" if not g2 else "GATES 1-2 PASSED: Phase 5 (book frame) follows"),
                    "inconclusive_for_power": [r for r in TRADED if doc["instruments"][r]["H1"]["verdict"].startswith("INCONCLUSIVE")]}
    doc["reads"]["spec_sha256"] = hashlib.sha256(SPEC.read_bytes()).hexdigest()
    doc["reads"]["amendments_sha256"] = hashlib.sha256(AMEND.read_bytes()).hexdigest()
    doc["n_trials"] = len(trials)
    doc["dry_run"] = dry
    doc["runtime_min"] = round((time.time() - t_start) / 60, 1)
    for t in trials:
        t["timestamp"] = stamp
    return doc, trials


def robustness(o: pd.DataFrame, trials: list[dict]) -> dict[str, Any]:
    """D642 s.5: H1's divergence under each variant, per instrument (reported, never re-selected; each a trial row)."""
    out: dict[str, Any] = {}
    for r in TRADED:
        a = o[o["root"] == r]
        p = a[a["z"] == 4.0]
        ev = p["event"].astype(bool)
        v: dict[str, tuple] = {  # name -> (frame, class column, x column, z, w, c_hi, c_lo, fill, event filter)
            "stress_fill": (p, "class_primary", "x_stress", 4.0, "1+3", 0.6, 0.2, "stress t0+1..t0+5", "none"),
            "z3": (a[a["z"] == 3.0], "class_primary", "x", 3.0, "1+3", 0.6, 0.2, "t0+1", "none"),
            "z5": (a[a["z"] == 5.0], "class_primary", "x", 5.0, "1+3", 0.6, 0.2, "t0+1", "none"),
            "w1": (p[p["w"] == 1], "class_primary", "x", 4.0, "1", 0.6, 0.2, "t0+1", "none"),
            "w3": (p[p["w"] == 3], "class_primary", "x", 4.0, "3", 0.6, 0.2, "t0+1", "none"),
            "c_0.5_0.3": (p, "class_alt_0.5_0.3", "x", 4.0, "1+3", 0.5, 0.3, "t0+1", "none"),
            "c_0.7_0.1": (p, "class_alt_0.7_0.1", "x", 4.0, "1+3", 0.7, 0.1, "t0+1", "none"),
            "without_event_shocks": (p[~ev], "class_primary", "x", 4.0, "1+3", 0.6, 0.2, "t0+1", "exclude events"),
            "event_shocks_only": (p[ev], "class_primary", "x", 4.0, "1+3", 0.6, 0.2, "t0+1", "events only"),
            "split_2016_2023": (p[p["day"] < SPLIT], "class_primary", "x", 4.0, "1+3", 0.6, 0.2, "t0+1", "none"),
            "split_2024_plus": (p[p["day"] >= SPLIT], "class_primary", "x", 4.0, "1+3", 0.6, 0.2, "t0+1", "none"),
        }
        if r == "CL":
            v["without_ngsr_diag"] = (p[~p["event_ngsr_diag"].astype(bool)], "class_primary", "x", 4.0, "1+3", 0.6, 0.2,
                                      "t0+1", "exclude NGSR diagnostic")
        for y in sorted(p["day"].str[:4].unique()):
            v[f"year_{y}"] = (p[p["day"].str[:4] == y], "class_primary", "x", 4.0, "1+3", 0.6, 0.2, "t0+1", "none")
        ok = p["vol_ratio"].notna()
        terc = pd.qcut(p.loc[ok, "vol_ratio"], 3, labels=["low", "mid", "high"])
        for t in ("low", "mid", "high"):
            v[f"liquidity_{t}"] = (p[ok][terc == t], "class_primary", "x", 4.0, "1+3", 0.6, 0.2, "t0+1", "none")
        rr: dict[str, Any] = {}
        for name, (fr, cc, xc, z, w, chi, clo, fill, evf) in v.items():
            res = h1_frame(fr, cc, xc)
            rr[name] = res
            if "delta_bp" in res:
                trials.append(trial(f"{r}_H1_{name}", r, "INFO-LIQ", z, w, chi, clo, "time30", fill, 0, evf,
                                    res["n_info"] + res["n_liq"], res["delta_bp"], None, res["t"], res["reads_2024_plus"],
                                    f"sensitivity {name}"))
        rr["liquidity_tercile_vol_ratio_missing"] = int((~ok).sum())
        rr["flow_profile"] = "not computable in v1: bars only (SC-A3)"
        out[r] = rr
    return out


def trial(tid: str, r: str, cls: str, z: float, w: str, chi: float, clo: float, exit_type: str, fill: str, cm: float,
          ev: str, n: int, gross: float, net: float | None, t: float | None, reads24: bool, notes: str) -> dict:
    return {"trial_id": tid, "doc": DOC, "family": FAMILY, "instrument": r, "class": cls, "z": z, "w": w, "c_hi": chi,
            "c_lo": clo, "exit_type": exit_type, "fill_model": fill, "cost_mult": cm, "event_filter": ev, "n_trades": n,
            "mean_gross": round(gross, 6), "mean_net": None if net is None else round(net, 6),
            "t_clustered": None if t is None else round(t, 6), "notes": f"{notes}; reads_2024_plus={reads24}"}


def _json_default(o: Any) -> Any:
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    raise TypeError(type(o))


def dump(doc: dict[str, Any]) -> str:
    return json.dumps(doc, indent=1, sort_keys=True, default=_json_default) + "\n"


# ============================================================================================== selftest
def selftest() -> int:
    """Each audit passes on the real code and RAISES on a deliberately broken input."""
    fired = []

    def must_raise(name: str, f: Callable) -> None:
        try:
            f()
        except ShockRunError:
            fired.append(name)
            return
        raise AssertionError(f"the {name} audit did not fire on a broken input")

    # lag (i): counts
    fake = pd.DataFrame({"root": ["GC", "GC"], "z": [4.0, 4.0], "class_primary": ["INFO", "LIQ"]})
    check_counts(fake, {"GC": {"INFO": 1, "LIQ": 1}})
    must_raise("counts", lambda: check_counts(fake.assign(class_primary=["INFO", "INFO"]), {"GC": {"INFO": 1, "LIQ": 1}}))
    # lag (ii): the second classification agrees with the model's, and fires on a tampered class
    for C, e in ((0.6, False), (0.35, True), (0.1, True), (0.2, False), (float("nan"), False), (0.5, False),
                 (0.25, True), (0.3, True), (0.29, True), (-0.4, False), (0.7, True), (0.1, False)):
        for hi, lo in P2.C_PAIRS.values():
            assert classify_second(C, e, hi, lo) == M.classify(C, e, hi, lo), (C, e, hi, lo)
    ok = pd.DataFrame({"C": [0.7, 0.1], "event": [False, False]})
    for k, (hi, lo) in P2.C_PAIRS.items():
        ok[f"class_{k}"] = [M.classify(c, False, hi, lo) for c in ok["C"]]
    check_classes(ok)
    must_raise("classes", lambda: check_classes(ok.assign(class_primary=["LIQ", "LIQ"])))
    # lag (iii): the indexer, and a broken one that reads the shock bar
    check_after(100, outcome_index(100))
    must_raise("after", lambda: check_after(100, {**outcome_index(100), "fill": [100]}))
    # money
    audit_money()
    must_raise("money-pnl", lambda: audit_money(pnl=lambda D, f, e: -D * (e / f - 1)))
    must_raise("money-x", lambda: audit_money(xf=lambda d, f, e: (e / f - 1)))
    must_raise("money-direction", lambda: audit_money(td=lambda c, d: d))
    # right quantity
    check_right_quantity(np.array([1.0, 2.0]), np.array([1.5, 2.0]), np.array([1, -1]))
    must_raise("rq-fill", lambda: check_right_quantity(np.array([1.0]), np.array([1.0]), np.array([1])))
    must_raise("rq-direction", lambda: check_right_quantity(np.array([1.0]), np.array([2.0]), np.array([1, -1]),
                                                           td=lambda c, d: d))
    # the scipy stand-ins against scipy 1.18's own values on a tie-heavy input (the venv, 2026-09-28)
    ta = np.array([3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7, 9, 3, 2, 3, 8, 4], float)
    tb = np.array([2, 7, 1, 8, 2, 8, 1, 8, 2, 8, 4, 5, 9, 0, 4, 5, 2, 3, 5, 3], float)
    assert rank_avg(ta).tolist() == [6.5, 1.5, 9.5, 1.5, 12.0, 19.0, 3.5, 14.0, 12.0, 6.5, 12.0, 16.5, 19.0, 15.0, 19.0,
                                     6.5, 3.5, 6.5, 16.5, 9.5]
    assert math.isclose(spearman(ta, tb), 0.19073187020980284, rel_tol=1e-12)
    assert math.isclose(skew(ta), 0.2781041038870394, rel_tol=1e-12)
    assert math.isclose(kurtosis(ta), -1.1984523941774117, rel_tol=1e-12)
    for t, df, want in ((2.0, 10, 0.03669401738537018), (2.5, 1500, 0.006262701445054912), (-1.3, 50, 0.9002189322360733),
                        (0.0, 5, 0.5), (8.0, 900, 1.90789689831632e-15), (1.0, 1, 0.25000000000000006)):
        assert math.isclose(t_sf(t, df), want, rel_tol=1e-9), (t, df, t_sf(t, df), want)
    # the statistics
    rng = np.random.default_rng(1)
    x = np.r_[rng.normal(2, 5, 300), rng.normal(-2, 5, 100)].round(1)  # rounded: ties
    info = np.r_[np.ones(300, bool), np.zeros(100, bool)]
    day = np.r_[np.arange(300) // 3, np.arange(100) // 2].astype(str)
    cd = cluster_ols(x, info, day)
    assert math.isclose(cd["coef_bp"], x[info].mean() - x[~info].mean(), rel_tol=1e-12) and cd["t"] > 2
    assert math.isclose(cd["se_bp"], cluster_ols_loop(x, info, day), rel_tol=1e-12)
    b = DayBoot(day, np.random.default_rng(2), B=400)
    bm = b.means(x, np.ones(len(x), bool))
    assert abs(bm.mean() - x.mean()) < 0.2 and bm.std() > 0
    assert np.allclose(b.means(np.column_stack([x, 2 * x]), np.ones(len(x), bool))[:, 1], 2 * bm)
    assert holm({"a": 0.01, "b": 0.04, "c": 0.03}) == {"a": 0.03, "c": 0.06, "b": 0.06}
    assert h3_verdict(1.0, 0.5, 0.1) == "PASS" and h3_verdict(0.55, 0.5, 0.1) == "UNRESOLVED"
    assert h3_verdict(0.1, 0.5, 0.1) == "FAIL"
    # the vectorised block expansion equals the per-day concatenation
    order = np.argsort(day, kind="stable")
    _, starts, lens = np.unique(day[order], return_index=True, return_counts=True)
    pick = np.random.default_rng(3).integers(0, len(starts), len(starts))
    L = lens[pick]
    fast = np.repeat(starts[pick] - np.cumsum(L) + L, L) + np.arange(L.sum())
    slow = np.concatenate([np.arange(starts[k], starts[k] + lens[k]) for k in pick])
    assert np.array_equal(fast, slow)
    print(f"selftest: {len(fired)} audits fire on broken inputs ({', '.join(fired)}); the statistics check out")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--run", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.dry_run:
        doc, trials = build(dry=True)
        dump(doc)
        ids = [t["trial_id"] for t in trials]
        assert len(ids) == len(set(ids)), "duplicate trial ids"
        print(f"DRY RUN (synthetic prices): every path ran; {len(trials)} trials; gates {doc['gates']['verdict']!r} "
              f"(meaningless on synthetic prices); {doc['runtime_min']} min. Nothing written.")
        return 0
    if a.run:
        if OUT.exists() or TRIALS.exists():
            raise SystemExit("the signal frame runs once (D642): its output or trials already exist")
        doc, trials = build()
        OUT.write_text(dump(doc), encoding="utf-8", newline="\n")
        log = TrialsCsv(TRIALS)
        for t in trials:
            log.append(t)
        print(json.dumps(doc["gates"], indent=1))
        print(f"wrote {OUT.name} and {TRIALS.name} ({len(trials)} trials) in {doc['runtime_min']} min")
        return 0
    doc, _ = build()
    committed = OUT.read_text(encoding="utf-8")
    old = json.loads(committed)
    doc["runtime_min"] = old["runtime_min"]
    doc["reads"]["redetect_min"] = old["reads"].get("redetect_min")
    if dump(doc) != committed:
        raise SystemExit("CHECK FAILED: the rebuild differs from the committed output")
    print("CHECK: the rebuild equals the committed output")
    return 0


if __name__ == "__main__":
    sys.exit(main())
