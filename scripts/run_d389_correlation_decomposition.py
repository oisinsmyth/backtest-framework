"""D389 -- where does the remaining 0.44 correlation floor come from?

    uv run python scripts/run_d389_correlation_decomposition.py --run

MECHANISM DECOMPOSITION. Scores no cell, admits nothing, reads no holdout, fetches nothing.
Pre-registration 5bd7d97 predates this file (R8).

EXTRACT the common factor, THEN identify it. Every prior attempt hypothesised a mechanism and tested
it -- D377's H1 beta (7%), H2 cohort (destroys 79% of the return), H3 price (0.0288). This one takes
the principal component of the book matrix first, so the answer is not limited to mechanisms someone
happened to think of.
"""
import argparse
import importlib.util
import json
import pathlib
import sys

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


RP = _load("rp", "ragged_panel.py")
AN = _load("an", "ragged_anomaly_scores.py")

SERIES = REPO / "data/d376_series.npz"
FIX = REPO / "data/fixtures/us_shorts_daily_raw.csv.gz"
EVJ = REPO / "data/fixtures/us_shorts_daily_raw_events.json"
OUT = REPO / "data/d389_correlation_decomposition.json"

D376 = dict(A=0.448, B=0.476, Bc=0.923)      # [SER] -- D376's committed headline, p50 pairwise rho
TOL_SER = 0.004
MIN_BOOKS_PER_BAR = 50


# ------------------------------------------------------------------ correlation, D376's own rule
def corr_masked(x, mx, y, my):
    """[MASK] -- correlate on the INTERSECTION of two defined masks. D376's rule, unchanged."""
    k = mx & my & np.isfinite(x) & np.isfinite(y)
    n = int(k.sum())
    if n < 3:
        return None, n
    a, b = x[k], y[k]
    if a.std() == 0 or b.std() == 0:
        return None, n
    return float(np.corrcoef(a, b)[0, 1]), n


def common_bars(X, M):
    """Bars defined for EVERY book in the arm. B and Bc masks are IDENTICAL across books; A' masks
    differ by at most 3 bars of 4,124, so the common set is 4,121."""
    return np.all(M, axis=0) & np.all(np.isfinite(X), axis=0)


def pair_p50(X, M, bars=None):
    """Median pairwise rho over ALL pairs, on the common mask -- one matrix product rather than a
    Python double loop. The capped-subsample version this replaced disagreed with D376's committed
    B p50 by 0.008 purely through sampling (1,770 pairs against 31,125), which [SER] caught."""
    b = common_bars(X, M) if bars is None else bars
    A = X[:, b]
    A = (A - A.mean(axis=1, keepdims=True)) / np.maximum(A.std(axis=1, keepdims=True), 1e-300)
    C = (A @ A.T) / A.shape[1]
    iu = np.triu_indices(len(A), 1)
    v = C[iu]
    v = v[np.isfinite(v)]
    return (float(np.median(v)) if len(v) else float("nan")), len(v)


def assert_FASTC(X, M, n=1500, seed=3):
    """GUARD THE REWRITE, AT THE LEVEL THE STATISTIC IS USED.

    The common-mask matrix path and D376's per-pair `corr_masked` are the SAME estimator only where
    every book shares a mask -- true for B and Bc, where equality must be exact. For A' the masks
    differ by up to 3 bars of 4,124 and the two are genuinely different estimators: individual pairs
    disagree by up to 1e-2 (measured, not assumed -- an earlier version of this guard asserted 5e-3
    on individual pairs and fired).

    The study reads the arm's MEDIAN, so that is what is guarded: the two medians over the same
    sampled pairs must agree to 2e-3. The worst per-pair gap is reported beside it."""
    rng = np.random.default_rng(seed)
    b = common_bars(X, M)
    A = X[:, b]
    A = (A - A.mean(axis=1, keepdims=True)) / np.maximum(A.std(axis=1, keepdims=True), 1e-300)
    identical = bool(np.all(M == M[0]))
    slow_v, fast_v, worst = [], [], 0.0
    for _ in range(n):
        i, j = rng.choice(len(X), 2, replace=False)
        slow, _k = corr_masked(X[i], M[i], X[j], M[j])
        fast = float(A[i] @ A[j] / A.shape[1])
        if slow is not None:
            slow_v.append(slow)
            fast_v.append(fast)
            worst = max(worst, abs(slow - fast))
    gap = abs(float(np.median(slow_v)) - float(np.median(fast_v)))
    if identical:
        assert worst < 1e-12, f"[FASTC] masks are identical but pairs differ by {worst:.3e}"
    assert gap < 2e-3, f"[FASTC] median gap {gap:.3e} between the two estimators"
    return dict(identical=identical, median_gap=gap, worst_pair=worst)


def book_clustered_se(X, M, books=250, draws=200, seed=1):
    """[CLU] -- resample BOOKS, not pairs. 124,750 A' pairs come from 500 books."""
    rng = np.random.default_rng(seed)
    n = len(X)
    vals = []
    for _ in range(draws):
        pick = rng.choice(n, min(books, n), replace=True)
        pick = np.unique(pick)
        if len(pick) < 8:
            continue
        v, _ = pair_p50(X[pick], M[pick])
        if np.isfinite(v):
            vals.append(v)
    return float(np.std(vals, ddof=1)) if len(vals) > 3 else float("nan")


# ------------------------------------------------------------------------ extraction
def standardise(X, M, min_books=MIN_BOOKS_PER_BAR):
    """Books to zero mean / unit sd on their own defined bars; undefined bars become 0 and are
    excluded from the bar set. Returns (Z, bar mask)."""
    Z = np.zeros_like(X)
    for i in range(len(X)):
        k = M[i] & np.isfinite(X[i])
        if k.sum() < 30:
            continue
        v = X[i][k]
        s = v.std()
        if s > 0:
            Z[i][k] = (v - v.mean()) / s
    cover = (M & np.isfinite(X)).sum(axis=0)
    return Z, cover >= min_books


def pc1(Z, bars):
    """First principal component of the standardised book matrix, on covered bars."""
    A = Z[:, bars]
    C = A @ A.T / A.shape[1]
    w, V = np.linalg.eigh(C)
    order = np.argsort(w)[::-1]
    w, V = w[order], V[:, order]
    load = V[:, 0]
    f = load @ A
    f = (f - f.mean()) / (f.std() + 1e-300)
    share = float(w[0] / w.sum())
    return f, load, share, w


# -------------------------------------------------------------------------- drivers
def drivers(panel, T):
    """Candidate per-bar drivers, all from the panel. Each stands for a named mechanism."""
    live = panel.live
    lr = panel.log_returns
    m = AN.market_return(lr, live)[:T]
    nlive = live.sum(axis=0).astype(float)[:T]
    with np.errstate(invalid="ignore"):
        disp = np.nanstd(np.where(live, lr, np.nan), axis=0)[:T]
    d = {
        "m (equal-weight market)": m,
        "|m| (NONLINEAR market)": np.abs(m),
        "m^2 (NONLINEAR market)": m * m,
        "nlive (eligibility floor)": nlive,
        "d nlive (breadth change)": np.concatenate([[np.nan], np.diff(nlive)]),
        "cross-sectional dispersion": disp,
        "1/nlive (equal-weighting)": np.where(nlive > 0, 1.0 / np.maximum(nlive, 1), np.nan),
    }
    return {k: np.asarray(v, float) for k, v in d.items()}


def resid_on(X, M, D, bars):
    """Regress every book on the given drivers (bars where all are defined) and return residuals."""
    ok = bars & np.all(np.isfinite(D), axis=0)
    G = np.column_stack([np.ones(ok.sum())] + [d[ok] for d in D])
    Q, _ = np.linalg.qr(G)
    R = X.copy()
    for i in range(len(X)):
        k = M[i] & np.isfinite(X[i]) & ok
        if k.sum() < 60:
            R[i] = np.where(M[i], np.nan, X[i])
            continue
        sub = ok & k
        idx = np.flatnonzero(sub[ok])
        Qi = Q[idx]
        y = X[i][sub]
        R[i] = X[i].copy()
        R[i][sub] = y - Qi @ (Qi.T @ y)
    return R


# ----------------------------------------------------------------------- assertions
def assert_SER(res):
    for k, want in D376.items():
        got = res[k]["p50"]
        assert abs(got - want) < TOL_SER, f"[SER] {k} p50 {got:.4f} != D376's {want} (tol {TOL_SER})"
    return {k: res[k]["p50"] for k in D376}


def assert_FACTOR(share, rho, tol=0.12):
    """PC1's variance share must reconcile with the mean pairwise rho by an INDEPENDENT route.
    For n standardised series with one common factor, mean pairwise rho ~= (n*share - 1)/(n - 1)."""
    assert np.isfinite(share) and np.isfinite(rho), "[FACTOR] non-finite input"
    d = abs(share - rho)
    assert d < tol, f"[FACTOR] PC1 share {share:.3f} vs mean pairwise rho {rho:.3f}, gap {d:.3f}"
    return d


def assert_ALIGN(f, dr, bars):
    """The factor and the drivers must be aligned BY DATE INDEX. Probed by shifting the
    best-correlating driver one bar: a genuinely aligned pair must get WEAKER, or every
    identification below is meaningless."""
    best, name = -1.0, None
    for k, v in dr.items():
        if not np.all(np.isfinite(v[bars])):
            continue
        c = abs(float(np.corrcoef(f, v[bars])[0, 1]))
        if c > best:
            best, name = c, k
    assert name is not None, "[ALIGN] no driver was defined on every covered bar"
    c2 = abs(float(np.corrcoef(f, np.roll(dr[name], 1)[bars])[0, 1]))
    assert best > c2, f"[ALIGN] shifting {name} did not weaken it ({best:.3f} -> {c2:.3f})"
    return name, best, c2


def assert_X(f, bars):
    """Each break must move the exact SCALAR its assertion compares."""
    fired = {}
    try:                                            # [SER]: a number that is not D376's
        assert_SER({"A": {"p50": 0.30}, "B": {"p50": 0.476}, "Bc": {"p50": 0.923}})
        fired["SER"] = False
    except AssertionError:
        fired["SER"] = True
    try:                                            # [FACTOR]: a share that cannot reconcile with rho
        assert_FACTOR(0.90, 0.44)
        fired["FACTOR"] = False
    except AssertionError:
        fired["FACTOR"] = True
    try:
        # [ALIGN]: a driver that is the factor ALREADY SHIFTED. Rolling it one more RESTORES
        # alignment, so the correlation must RISE and the guard must fire.
        full = np.full(len(bars), np.nan)
        full[bars] = f
        assert_ALIGN(f, {"pre-shifted": np.roll(full, -1)}, bars)
        fired["ALIGN"] = False
    except AssertionError:
        fired["ALIGN"] = True
    bad = [k for k, v in fired.items() if not v]
    assert not bad, f"[X] these audits did NOT raise on a deliberate break: {bad}"
    return fired


# --------------------------------------------------------------------------- run
def run(cap=None):
    z = np.load(SERIES, allow_pickle=True)
    arms = {"A": (z["A_x"], z["A_m"]), "B": (z["B_x"], z["B_m"]), "Bc": (z["Bc_x"], z["Bc_m"])}
    T = arms["A"][0].shape[1]
    print(f"\nRUN -- D389. {', '.join(f'{k}={v[0].shape[0]}' for k, v in arms.items())} books "
          f"x {T:,} bars, from the committed D376 artifact")

    base = {}
    for k, (X, M) in arms.items():
        _fc = assert_FASTC(X, M)
        print(f"  [FASTC] {k:>2} identical masks {_fc[chr(39)]+chr(39) if False else _fc["identical"]}, median gap {_fc["median_gap"]:.2e}, worst pair {_fc["worst_pair"]:.2e}")
        r, n = pair_p50(X, M)
        base[k] = dict(p50=r, pairs=n)
        print(f"  [SER] {k:>2} p50 rho {r:+.4f} over {n:,} pairs "
              f"(D376: {D376[k]:+.3f})")
    assert_SER(base)
    print("  [SER] all three reproduce D376's committed headline")

    panel, _cleaned = RP.load_ragged(FIX, EVJ, fee_bps=0.0)
    dr = drivers(panel, T)

    out = {"base": base, "arms": {}}
    for arm in ("A", "B"):
        X, M = arms[arm]
        Z, bars = standardise(X, M)
        f, load, share, w = pc1(Z, bars)
        rho = base[arm]["p50"]
        gap = assert_FACTOR(share, rho)
        print(f"\n  [{arm}] {int(bars.sum()):,} covered bars   PC1 variance share {share:.3f} "
              f"vs pairwise rho {rho:.3f}   [FACTOR] gap {gap:.3f}")
        print(f"       PC2 {w[1]/w.sum():.3f}  PC3 {w[2]/w.sum():.3f}  "
              f"loading sign agreement {max(np.mean(load > 0), np.mean(load < 0)):.2f}")

        if arm == "A":
            nm, b1, b2 = assert_ALIGN(f, {k: v for k, v in dr.items()
                                          if np.all(np.isfinite(v[bars]))}, bars)
            print(f"  [ALIGN] best driver {nm}: |r| {b1:.3f}, shifted one bar {b2:.3f}")
            print(f"  [X]     {assert_X(f, bars)}")

        print(f"\n  IDENTIFY -- what is PC1?   ({arm} arm)")
        print(f"{'driver':>30}{'|corr| with PC1':>18}{'R^2':>8}")
        ident = {}
        for k, v in dr.items():
            ok = bars & np.isfinite(v)
            if ok.sum() < 200:
                continue
            c = float(np.corrcoef(f[np.isfinite(v[bars])], v[ok])[0, 1])
            ident[k] = c
            print(f"{k:>30}{abs(c):>18.3f}{c*c:>8.3f}")

        rank = sorted(ident, key=lambda k: -abs(ident[k]))
        print(f"\n  DECOMPOSE -- floor after removing drivers, {arm} arm")
        print(f"{'removed':>44}{'floor':>9}{'drop':>8}")
        steps = [("nothing (baseline)", [])]
        steps.append((rank[0], [rank[0]]))
        steps.append(("+ " + rank[1], rank[:2]))
        steps.append(("ALL market terms", [k for k in dr if "market" in k]))
        steps.append(("EVERYTHING", list(dr)))
        res = {}
        for label, keys in steps:
            if not keys:
                v = base[arm]["p50"]
            else:
                D = [dr[k] for k in keys]
                R = resid_on(X, M, D, bars)
                v, _ = pair_p50(R, M, bars=bars)
            res[label] = v
            print(f"{label:>44}{v:>9.4f}{v-base[arm]['p50']:>8.4f}")
        se = book_clustered_se(X, M)
        print(f"  [CLU] book-clustered SE on the baseline floor: {se:.4f}")
        out["arms"][arm] = dict(share=share, pc2=float(w[1] / w.sum()), gap=gap,
                                ident=ident, decomp=res, se=se,
                                bars=int(bars.sum()))

    OUT.write_text(json.dumps(out, indent=1))
    print(f"\n  wrote {OUT}")

    A = out["arms"]["A"]
    worst = A["decomp"]["EVERYTHING"]
    print(f"\n  M3 -- UNATTRIBUTED: after removing every driver the A' floor is {worst:.4f} "
          f"against {base['A']['p50']:.4f}")
    print(f"       attributed {base['A']['p50'] - worst:+.4f}, i.e. "
          f"{100*(base['A']['p50']-worst)/base['A']['p50']:.0f}% of the floor")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--cap", type=int, default=120)
    a = ap.parse_args()
    print("D389  where does the remaining 0.44 correlation floor come from?")
    if a.run:
        run(a.cap)
    else:
        ap.print_help()
