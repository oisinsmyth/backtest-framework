"""D614 STAGE 0 -- expiry pinning on ES from the NOON 0DTE volume ladder.

    uv run python scripts/stage0_d614_expiry_pin.py --selftest   # every audit passes a clean case and RAISES on a break
    uv run python scripts/stage0_d614_expiry_pin.py --run        # 2016-01-04 .. 2023-12-29

Pre-registration `aeceba9` predates this file (R8). Nothing admitted (R15). No session, option row
or quote from 2024-01-01 on is read.

THE PRIMARY IS THE LEVEL COEFFICIENT, NOT THE INTERACTION
---------------------------------------------------------
`stage0_d581_gamma_close.py`'s `c_only` returns `beta[2]`, which with `add_constant` prepended is
the coefficient on `F5*F2` -- the INTERACTION. D581 wanted that. A pin hypothesis is a LEVEL claim:
the close moves toward the heavy strikes whatever the prior hour did. So this runner extracts
coefficients BY NAME through `coef_named`, and `audit_column_mapping` fires if the level slot is
read at the interaction's index.

    y  = R2 = 1e4*log(P1600/P1530)                              basis points
    x1 = ON   /sigma30_bp    prior 16:00 -> 09:30
    x2 = DAY0 /sigma30_bp    09:30 -> 12:00    inside the accumulation window
    x3 = MIDE /sigma30_bp    12:00 -> 14:30    after it, before the window
    x4 = F5   /sigma30_bp    14:30 -> 15:30    D581's conditioner
    x5 = PING                the grid-only placebo, which MUST FAIL its own bar
    x6 = PIN                 <- THE PRIMARY, a level
    x7 = F5/sigma30_bp*PIN   a labelled diagnostic, never the primary

Bars: |c| above the p95 of |c| in the enumerated session-shift null, |NW t| >= 2, the family maximum
over three bands above its own p95, the PING placebo INSIDE its bar, and an ECONOMIC bar of 15 bp
per sigma below which a statistical pass is "real but not tradeable" and closes the line. Both signs
are scored separately: every cell carries its upper-tail (attraction) and lower-tail (repulsion)
rank. The variance block is DESCRIPTIVE -- its in-sample reading is not blind (see the record).

Output data/stage0_d614_expiry_pin.json.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


FIX = REPO / "data" / "fixtures"
ES_1M = FIX / "fut_ES_rth_1m.csv.gz"
OPTS = FIX / "fut_es_options_eod.csv.gz"
CUTS = FIX / "fut_es_0dte_volume_cutoffs.csv.gz"
SPECS = REPO / "data" / "futures_contract_specs.json"
ART_D581 = REPO / "data" / "stage0_d581_gamma_close.json"
TEMP = REPO / "temp" / "d614"
OUT = REPO / "data" / "stage0_d614_expiry_pin.json"

SPEC = "D614"
IN_FROM, IN_TO, RESERVED_FROM = "2016-01-04", "2023-12-29", "2024-01-01"
T_OPEN, T_NOON, T_MIDE, T_ENTRY, T_HALF, T_CLOSE = "09:30", "12:00", "14:30", "15:30", "15:45", "16:00"
MIN_BARS = 380
SIG_N, SIG_MIN = 252, 200
NW_LAG, SHIFT_MIN, BOOT, FLIP_DRAWS, SEED = 5, 10, 1000, 2000, 614
BANDS = ((None, "all"), (4.0, "4sig"), (2.0, "2sig"))        # the primary is the first: no truncation
PRIMARY_BAND = "all"
ECON_BAR_BP = 15.0                                           # bp per sigma of PIN; below this a pass is not tradeable
NEAR_K = 9                                                   # C9: the nearest nine listed strikes
COMM_RT, CROSS_TICKS = 3.00, 1.0                             # D469's line, in dollars and ticks
REQUIRED_OUTPUTS = ("spec", "windows", "sets", "audits", "premise", "blockA", "blockB", "controls",
                    "component", "beside", "predictions", "verdict", "timing_s", "construction")


def log(*a):
    print(*a, flush=True)


def expect_raise(fn, what, say=log):
    try:
        fn()
    except AssertionError as e:
        say(f"    audit RAISES on {what}: {str(e)[:78]}")
        return True
    raise AssertionError(f"audit did not raise on {what}")


def blk(obs, null):
    """Two-sided AND both one-sided tails, because the principal asked for every version scored."""
    null = np.asarray(null, float)
    null = null[np.isfinite(null)]
    if null.size == 0:
        return {"observed": float(obs), "n": 0}
    a = np.abs(null)
    return {"observed": float(obs), "n": int(null.size),
            "p05": float(np.percentile(null, 5)), "p50": float(np.percentile(null, 50)),
            "p95": float(np.percentile(null, 95)),
            "abs_p95": float(np.percentile(a, 95)),
            "rank_two_sided": float((a < abs(obs)).mean()),
            "above_abs_p95": bool(abs(obs) > np.percentile(a, 95)),
            "rank_upper": float((null < obs).mean()), "above_p95": bool(obs > np.percentile(null, 95)),
            "rank_lower": float((null > obs).mean()), "below_p05": bool(obs < np.percentile(null, 5))}


# ------------------------------------------------------------------ the regression, by NAME
def design(cols):
    names = list(cols)
    X = np.column_stack([np.asarray(cols[n], float) for n in names])
    return names, X


def audit_not_singular(cols, tol=1 - 1e-8):
    """RAISES if two columns are the same variable under different names.

    A design carrying one column twice is singular, its coefficient is arbitrary and its null explodes
    rather than failing. That happened on the first pass: the placebo cell put the grid centroid in the
    target slot while it was still a control, and the null's |c| p95 came back as 6.4e13. A number that
    large is visible; the same mistake with two merely NEAR-identical columns would not be.
    """
    names, X = design(cols)
    ok = np.isfinite(X).all(axis=1)
    if ok.sum() < 3:
        return True
    Z = X[ok]
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = Z[:, i], Z[:, j]
            if a.std() == 0 or b.std() == 0:
                continue
            r = abs(float(np.corrcoef(a, b)[0, 1]))
            if r > tol:
                raise AssertionError(f"SINGULAR DESIGN: {names[i]} and {names[j]} correlate {r:.12f}")
    return True


def fit_named(y, cols, lag=NW_LAG):
    names, X = design(cols)
    ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
    res = sm.OLS(y[ok], sm.add_constant(X[ok])).fit(cov_type="HAC", cov_kwds={"maxlags": lag})
    return {"coef": {n: float(res.params[1 + i]) for i, n in enumerate(names)},
            "t": {n: float(res.tvalues[1 + i]) for i, n in enumerate(names)}, "n": int(ok.sum())}


def coef_named(y, cols, target):
    """The scalar the nulls score: plain least squares, the coefficient read at the target's own index."""
    names, X = design(cols)
    if target not in names:
        raise AssertionError(f"coef_named: {target} is not a column ({names})")
    ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
    beta = np.linalg.lstsq(sm.add_constant(X[ok]), y[ok], rcond=None)[0]
    return float(beta[1 + names.index(target)])


def coef_at_index(y, cols, i):
    """Deliberately positional. Only the column-mapping audit uses this."""
    _, X = design(cols)
    ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
    beta = np.linalg.lstsq(sm.add_constant(X[ok]), y[ok], rcond=None)[0]
    return float(beta[1 + i])


def shift_null(y, builder, base, target="PIN", kmin=SHIFT_MIN):
    """The PRE-REGISTERED null: every circular shift of the target, the other columns held fixed.

    `builder(pin)` rebuilds the WHOLE design from a candidate target column, so a column derived from
    the target (the interaction) moves with it. Rolling the target alone while leaving `F5*PIN` built
    from the unrolled one was a bug, and it is the kind that cannot be seen in the output.

    KNOWN DEFECT, MEASURED, NOT PATCHED HERE. The target is correlated with the momentum controls
    (R^2 ~ 0.72), and a rolled copy is not, so the null's design is BETTER CONDITIONED than the
    observed one and its spread is roughly half the true standard error. That makes this null
    anti-conservative. It is reported because it is what was pre-registered; `shift_null_norm` is the
    recorded amendment, and the verdict rests on that and on the HAC t.
    """
    n = len(y)
    base = np.asarray(base, float)
    obs = coef_named(y, builder(base), target)
    if not np.isclose(coef_named(y, builder(np.roll(base, 0)), target), obs, rtol=0, atol=1e-12):
        raise AssertionError("shift null: the zero offset does not reproduce the observed coefficient")
    vals = np.empty(n - 2 * kmin + 1)
    for j, k in enumerate(range(kmin, n - kmin + 1)):
        vals[j] = coef_named(y, builder(np.roll(base, int(k))), target)
    return vals


def _resid(x, Z):
    return np.asarray(x, float) - Z @ np.linalg.lstsq(Z, np.asarray(x, float), rcond=None)[0]


def fw_coef(yr, xr):
    return float((xr @ yr) / (xr @ xr))


def shift_null_norm(y, ctrl_cols, base, kmin=SHIFT_MIN):
    """THE AMENDMENT. Frisch-Waugh first, then roll the RESIDUALISED target.

    Residualising on the controls and rolling what is left preserves the regressor's norm exactly,
    so the coefficient's scale is the same in the null as in the observation -- which the
    pre-registered null does not manage. The observed statistic is identical to the multiple-
    regression coefficient by Frisch-Waugh, so nothing about the estimate changes; only the null
    becomes comparable to it.
    """
    Z = sm.add_constant(np.column_stack([np.asarray(v, float) for v in ctrl_cols.values()]))
    ok = np.isfinite(y) & np.isfinite(Z).all(axis=1) & np.isfinite(base)
    Z, yy, bb = Z[ok], np.asarray(y, float)[ok], np.asarray(base, float)[ok]
    yr, xr = _resid(yy, Z), _resid(bb, Z)
    obs = fw_coef(yr, xr)
    n = xr.size
    vals = np.empty(n - 2 * kmin + 1)
    for j, k in enumerate(range(kmin, n - kmin + 1)):
        vals[j] = fw_coef(yr, np.roll(xr, int(k)))
    if not np.isclose(fw_coef(yr, np.roll(xr, 0)), obs, rtol=0, atol=1e-12):
        raise AssertionError("amended null: the zero offset does not reproduce")
    return obs, vals


def flip_null(y, ctrl_cols, base, draws=FLIP_DRAWS, seed=SEED):
    """The direction destroyed, |PIN| and its pairing with the session's own volatility kept.

    On the residualised target, so the norm is preserved exactly -- a sign flip cannot change it.
    The group is 2**n, so this is the ONE sampled null in the study; draws and seed are declared.
    """
    Z = sm.add_constant(np.column_stack([np.asarray(v, float) for v in ctrl_cols.values()]))
    ok = np.isfinite(y) & np.isfinite(Z).all(axis=1) & np.isfinite(base)
    Z, yy, bb = Z[ok], np.asarray(y, float)[ok], np.asarray(base, float)[ok]
    yr, xr = _resid(yy, Z), _resid(bb, Z)
    rng = np.random.default_rng(seed)
    out = np.empty(draws)
    for i in range(draws):
        out[i] = fw_coef(yr, rng.choice((-1.0, 1.0), size=xr.size) * xr)
    return fw_coef(yr, xr), out


def se_ladder(y, cols, target="PIN"):
    """The same coefficient under six covariance estimators.

    A result that passes |t| >= 2 under one and fails under another is ON the bar, not over it, and
    saying which estimator was pre-registered is not the same as saying the finding is robust.
    """
    names, X = design(cols)
    ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
    Xc = sm.add_constant(X[ok])
    yy = np.asarray(y, float)[ok]
    j = 1 + names.index(target)
    out = {}
    for lab, kw in (("ols_homoskedastic", {}), ("hc0_white", {"cov_type": "HC0"}),
                    ("hc3_white_leverage", {"cov_type": "HC3"}),
                    ("hac_lag1", {"cov_type": "HAC", "cov_kwds": {"maxlags": 1}}),
                    ("hac_lag5_preregistered", {"cov_type": "HAC", "cov_kwds": {"maxlags": NW_LAG}}),
                    ("hac_lag10", {"cov_type": "HAC", "cov_kwds": {"maxlags": 10}})):
        r = sm.OLS(yy, Xc).fit(**kw)
        out[lab] = {"se": float(r.bse[j]), "t": float(r.tvalues[j]), "abs_t_ge_2": bool(abs(r.tvalues[j]) >= 2.0)}
    ts = [v["abs_t_ge_2"] for v in out.values()]
    out["all_estimators_agree"] = bool(all(ts) or not any(ts))
    return out


def tail_diagnostics(y, cols, target="PIN", top=10):
    """Is the coefficient carried by a handful of sessions? A rotation null cannot see this, because
    rotating decouples the regressor from the residual it co-moves with."""
    names, X = design(cols)
    ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
    Xc = sm.add_constant(X[ok])
    yy = np.asarray(y, float)[ok]
    x = X[ok][:, names.index(target)]
    e = sm.OLS(yy, Xc).fit().resid
    idx = np.argsort(-np.abs(x))[:top]
    base = coef_named(yy, {n: X[ok][:, i] for i, n in enumerate(names)}, target)
    keep = np.ones(x.size, bool)
    keep[idx] = False
    trimmed = coef_named(yy[keep], {n: X[ok][keep, i] for i, n in enumerate(names)}, target)
    return {"kurtosis_target": float(pd.Series(x).kurtosis()), "kurtosis_y": float(pd.Series(yy).kurtosis()),
            "corr_target_sq_resid_sq": float(np.corrcoef(x ** 2, e ** 2)[0, 1]),
            "ac1_target_times_resid": float(pd.Series(x * e).autocorr(1)),
            f"share_of_sum_sq_in_top{top}": float((x[idx] ** 2).sum() / (x ** 2).sum()),
            f"mean_abs_y_in_top{top}_bp": float(np.abs(yy[idx]).mean()), "mean_abs_y_bp": float(np.abs(yy).mean()),
            "coef_full": base, f"coef_excluding_top{top}": trimmed,
            "share_of_coef_from_top10": float(1.0 - trimmed / base) if base else None}


def week_block_se(y, cols, target, weeks, rng, boot=BOOT):
    uw = np.unique(weeks)
    groups = [np.flatnonzero(weeks == w) for w in uw]
    vals = np.empty(boot)
    for i in range(boot):
        idx = np.concatenate([groups[j] for j in rng.integers(0, len(groups), len(groups))])
        vals[i] = coef_named(y[idx], {k: np.asarray(v, float)[idx] for k, v in cols.items()}, target)
    return float(np.std(vals, ddof=1))


def year_block_se(x, years, rng, boot=BOOT):
    uy = np.unique(years)
    groups = [np.flatnonzero(years == y) for y in uy]
    vals = np.empty(boot)
    for i in range(boot):
        idx = np.concatenate([groups[j] for j in rng.integers(0, len(groups), len(groups))])
        vals[i] = float(np.nanmean(x[idx]))
    return float(np.std(vals, ddof=1))


# ------------------------------------------------------------------ prices
def load_es():
    b = pd.read_csv(ES_1M, dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
    b = b[(b["day"] >= IN_FROM) & (b["day"] <= IN_TO)]
    if b["day"].max() >= RESERVED_FROM:
        raise AssertionError("a reserved session leaked into the ES read")
    nb = b.groupby("day").size()
    close = b.pivot(index="day", columns="hhmm", values="close")
    open_ = b.pivot(index="day", columns="hhmm", values="open")
    keep = nb.reindex(close.index) >= MIN_BARS
    close, open_ = close[keep], open_[keep]
    contract = b.groupby("day")["contract"].agg(lambda s: s.value_counts().index[0]).reindex(close.index)

    def P(hhmm):     # the close of the bar ENDING at hhmm is the bar starting one minute earlier (D462)
        prev = (pd.Timestamp("2000-01-01 " + hhmm) - pd.Timedelta(minutes=1)).strftime("%H:%M")
        return close[prev]

    def rv(lo, hi):
        cols = sorted(c for c in close.columns if lo <= c <= hi)
        r = np.diff(np.log(close[cols].to_numpy()), axis=1)
        rvv = np.nansum(r * r, axis=1)
        bp = (np.pi / 2) * np.nansum(np.abs(r[:, 1:]) * np.abs(r[:, :-1]), axis=1)
        return rvv, bp, r.shape[1]

    s = pd.DataFrame({"P0930": open_[T_OPEN], "P1200": P(T_NOON), "P1430": P(T_MIDE),
                      "P1530": P(T_ENTRY), "P1545": P(T_HALF), "P1600": P(T_CLOSE)}, index=close.index)
    s["contract"] = contract
    s["R2"] = 1e4 * np.log(s["P1600"] / s["P1530"])
    s["R2a"] = 1e4 * np.log(s["P1545"] / s["P1530"])
    s["R2b"] = 1e4 * np.log(s["P1600"] / s["P1545"])
    s["F5"] = 1e4 * np.log(s["P1530"] / s["P1430"])
    s["MIDE"] = 1e4 * np.log(s["P1430"] / s["P1200"])
    s["DAY0"] = 1e4 * np.log(s["P1200"] / s["P0930"])
    s["ON"] = 1e4 * np.log(s["P0930"] / s["P1600"].shift(1))
    s["roll"] = s["contract"] != s["contract"].shift(1)
    late, bplate, nlate = rv(T_ENTRY, "15:59")
    early, bpearly, nearly = rv(T_MIDE, "14:59")
    s["RV_late"], s["RV_early"] = late, early
    s["BPV_late"], s["BPV_early"] = bplate, bpearly
    # sigma30 in BASIS POINTS, trailing 252 sessions, LAGGED one session
    s["sigma30_bp"] = s["R2"].rolling(SIG_N, min_periods=SIG_MIN).std().shift(1)
    s["sigma30_pts"] = s["sigma30_bp"] * s["P1530"] / 1e4
    s["year"] = s.index.str[:4]
    iso = pd.to_datetime(pd.Series(s.index)).dt.isocalendar()
    s["week"] = (iso["year"] * 100 + iso["week"]).to_numpy()
    s["dow"] = pd.to_datetime(pd.Series(s.index)).dt.dayofweek.to_numpy()
    return s, {"returns_per_window": int(nlate), "returns_per_window_early": int(nearly)}


def audit_prices_vs_d581(s, r81):
    """R2 and F5 must equal D581's own loader to 1e-12 on the sessions both keep."""
    es = r81.load_es(lambda *a, **k: None)
    j = s.join(es[["R2", "F5"]], how="inner", rsuffix="_81")
    if len(j) < 1500:
        raise AssertionError(f"price audit: only {len(j)} shared sessions")
    for col in ("R2", "F5"):
        d = np.abs(j[col].to_numpy() - j[col + "_81"].to_numpy())
        if np.nanmax(d) > 1e-12:
            raise AssertionError(f"price audit: {col} differs from D581 by {np.nanmax(d):.3e}")
    return int(len(j))


# ------------------------------------------------------------------ the ladder
def cache_key():
    h = hashlib.sha256()
    for p in (OPTS, CUTS, Path(__file__)):
        h.update(f"{p.name}:{p.stat().st_mtime_ns}:{p.stat().st_size}".encode())
    return h.hexdigest()[:16]


def load_ladder():
    """Per (session, strike): listed flag, noon volume and prior-close OI, for the 0DTE PM set and
    for the nearest LATER expiry. Cached on both fixtures' mtimes and this file's."""
    TEMP.mkdir(parents=True, exist_ok=True)
    cf = TEMP / f"ladder_{cache_key()}.pkl"
    if cf.exists():
        return pd.read_pickle(cf)
    d = pd.read_csv(OPTS, usecols=["session", "raw_symbol", "right", "strike", "expiry_date",
                                   "expiry_hhmm", "underlying", "oi"],
                    dtype={"session": str, "raw_symbol": str, "right": str,
                           "expiry_date": str, "expiry_hhmm": str, "underlying": str}, encoding="utf-8")
    d = d[(d["session"] >= IN_FROM) & (d["session"] <= IN_TO)]
    if d["session"].max() >= RESERVED_FROM:
        raise AssertionError("a reserved option row leaked")
    t = pd.read_csv(CUTS, dtype={"session": str, "raw_symbol": str}, encoding="utf-8")
    t = t[(t["session"] >= IN_FROM) & (t["session"] <= IN_TO)]
    t["v12"] = t["v_0000_1200"]
    t["v1530"] = t["v_0000_1200"] + t["v_1200_1530"]
    d = d.merge(t[["session", "raw_symbol", "v12", "v1530"]], on=["session", "raw_symbol"], how="left")
    d[["v12", "v1530"]] = d[["v12", "v1530"]].fillna(0.0)          # absence means zero (D613 meta)
    d["oi"] = d["oi"].fillna(0.0)
    same = d["expiry_date"].to_numpy() == d["session"].to_numpy()
    pm = d["expiry_hhmm"].to_numpy() >= T_ENTRY                     # the AM quarterly has already expired
    d["arm"] = np.where(same & pm, "zero_dte", np.where(d["expiry_date"].to_numpy() > d["session"].to_numpy(),
                                                       "later", "drop"))
    d = d[d["arm"] != "drop"]
    # the nearest later expiry per session, so the horizon-matched control moves only the horizon
    nxt = (d[d["arm"] == "later"].groupby("session")["expiry_date"].min().rename("next_exp"))
    d = d.join(nxt, on="session")
    d = d[(d["arm"] == "zero_dte") | (d["expiry_date"] == d["next_exp"])]
    g = (d.groupby(["session", "arm", "strike"], sort=True)
         .agg(v12=("v12", "sum"), v1530=("v1530", "sum"), oi=("oi", "sum"), rows=("right", "size"))
         .reset_index())
    und = (d[d["arm"] == "zero_dte"].groupby(["session", "underlying"])["v12"].sum()
           .reset_index().sort_values("v12").groupby("session").tail(1)
           .set_index("session")["underlying"].rename("dom_underlying"))
    g.to_pickle(cf)
    pd.to_pickle(und, TEMP / f"und_{cache_key()}.pkl")
    return g


def dominant_underlying():
    return pd.read_pickle(TEMP / f"und_{cache_key()}.pkl")


def centroid(k, w):
    tot = w.sum()
    if tot <= 0:
        return np.nan
    return float((k * w).sum() / tot)


def centroid_second_path(k, p1530, w):
    """Algebraically identical, a different floating-point route: p + sum((k-p)w)/sum(w)."""
    tot = w.sum()
    if tot <= 0:
        return np.nan
    return float(p1530 + ((k - p1530) * w).sum() / tot)


def audit_centroid(k, p1530, w):
    a, b = centroid(k, w), centroid_second_path(k, p1530, w)
    if not (np.isfinite(a) and np.isfinite(b) and abs(a - b) <= 1e-9 * max(1.0, abs(a))):
        raise AssertionError(f"CENTROID AUDIT: {a} vs {b}")
    return a


def centroid_broken(k, w):
    """The slip this audit is for: dividing by the count instead of the weight total."""
    return float((k * w).sum() / max(len(k), 1))


def ladder_stats(gs, p1530, sig_pts, band):
    """One session, one arm, one band -> the ladder statistics. `band` is None for no truncation."""
    k = gs["strike"].to_numpy(float)
    if band is not None and np.isfinite(sig_pts) and sig_pts > 0:
        m = np.abs(k - p1530) <= band * sig_pts
        gs, k = gs[m], k[m]
    if len(k) == 0:
        return None
    v = gs["v12"].to_numpy(float)
    oi = gs["oi"].to_numpy(float)
    out = {"nK": int(len(k)), "v_total": float(v.sum()), "oi_total": float(oi.sum()),
           "step": float(np.median(np.diff(np.sort(np.unique(k))))) if len(np.unique(k)) > 1 else np.nan}
    v1530 = gs["v1530"].to_numpy(float)
    out["K_vol"] = centroid(k, v)
    out["K_vol1530"] = centroid(k, v1530)                 # the 15:30 cutoff: DESCRIPTIVE, its reading is not blind
    out["v1530_total"] = float(v1530.sum())
    out["K_grid"] = float(k.mean())
    out["K_oi"] = centroid(k, oi)
    out["K_max"] = float(k[int(np.argmax(v))]) if v.sum() > 0 else np.nan
    sh = v / v.sum() if v.sum() > 0 else None
    if sh is not None:
        out["C"] = float((sh * sh).sum())
        out["C_norm"] = float((out["C"] - 1.0 / len(k)) / (1.0 - 1.0 / len(k))) if len(k) > 1 else np.nan
        near = np.argsort(np.abs(k - p1530))[:NEAR_K]
        vn = v[near]
        out["C9"] = float(((vn / vn.sum()) ** 2).sum()) if vn.sum() > 0 else np.nan
    else:
        out["C"] = out["C_norm"] = out["C9"] = np.nan
    return out


# ------------------------------------------------------------------ audits with breaks that fire
def audit_column_mapping():
    """A level-only panel: the NAMED level reads ~+5 and the interaction ~0. Reading the level at the
    interaction's index is the defect this fires on."""
    rng = np.random.default_rng(7)
    n = 3000
    f5 = rng.normal(0, 1, n)
    pin = rng.normal(0, 1, n)
    y = 5.0 * pin + rng.normal(0, 10, n)
    cols = {"F5": f5, "PIN": pin, "F5xPIN": f5 * pin}
    lev = coef_named(y, cols, "PIN")
    inter = coef_named(y, cols, "F5xPIN")
    if not (abs(lev - 5.0) < 0.6 and abs(inter) < 0.6):
        raise AssertionError(f"COLUMN MAPPING: level {lev:+.3f} interaction {inter:+.3f} on a level-only panel")
    return {"level": lev, "interaction": inter}


def audit_column_mapping_broken():
    """D581's positional read: index 2 of [F5, PIN, F5xPIN] is the interaction, not the level."""
    rng = np.random.default_rng(7)
    n = 3000
    f5 = rng.normal(0, 1, n)
    pin = rng.normal(0, 1, n)
    y = 5.0 * pin + rng.normal(0, 10, n)
    cols = {"F5": f5, "PIN": pin, "F5xPIN": f5 * pin}
    wrong = coef_at_index(y, cols, 2)
    if abs(wrong - 5.0) < 0.6:
        raise AssertionError("COLUMN MAPPING: the positional read happens to equal the level")
    raise AssertionError(f"COLUMN MAPPING: index 2 reads {wrong:+.3f}, not the level +5")


def audit_sign_in_money(flip=False):
    """A LEVEL effect, no interaction: the level coefficient must be positive and large."""
    rng = np.random.default_rng(11)
    n = 1500
    f5 = rng.normal(0, 1, n)
    pin = rng.normal(0, 1, n)
    y = 5.0 * pin + rng.normal(0, 15, n)
    cols = {"F5": f5, "PIN": -pin if flip else pin, "F5xPIN": f5 * pin}
    c = coef_named(y, cols, "PIN")
    if not c > 2.5:
        raise AssertionError(f"SIGN AUDIT: level {c:+.3f} on a panel built to pull positively")
    return c


def audit_trailing_no_lookahead(s):
    """The general form: rebuild sigma30 on sessions <= t and require the value at t bit-identical."""
    days = list(s.index)
    t = days[len(days) - 40]
    full = float(s.loc[t, "sigma30_bp"])
    trunc = s.loc[:t, "R2"].rolling(SIG_N, min_periods=SIG_MIN).std().shift(1).loc[t]
    if not (np.isfinite(full) and np.isfinite(trunc) and abs(full - float(trunc)) <= 0.0):
        raise AssertionError(f"LOOK-AHEAD: sigma30 at {t} is {full} on the full panel and {trunc} truncated")
    return {"session": t, "sigma30_bp": full}


def audit_trailing_broken(s):
    """The break: the shift dropped, so the session's own R2 enters its own denominator."""
    days = list(s.index)
    t = days[len(days) - 40]
    full = float(s.loc[t, "sigma30_bp"])
    nolag = s["R2"].rolling(SIG_N, min_periods=SIG_MIN).std().loc[t]
    if abs(full - float(nolag)) <= 0.0:
        raise AssertionError("LOOK-AHEAD: dropping the shift changed nothing, so the guard reads a constant")
    raise AssertionError(f"LOOK-AHEAD: unshifted sigma30 at {t} is {float(nolag):.4f} against {full:.4f}")


def audit_commensurate(dom, contract):
    """The strikes and P1530 must be quoted on the same future."""
    j = pd.DataFrame({"dom": dom, "contract": contract}).dropna()
    bad = int((j["dom"] != j["contract"]).sum())
    return {"sessions": int(len(j)), "mismatched": bad, "share": float(bad / max(len(j), 1))}


def audit_commensurate_raises(dom, contract):
    j = pd.DataFrame({"dom": dom, "contract": contract}).dropna()
    keep = j["dom"] == j["contract"]
    shifted = j["contract"].shift(1)
    still = (j.loc[keep, "dom"] == shifted.loc[keep]).mean()
    if still > 0.99:
        raise AssertionError("COMMENSURABILITY: the contract map shifted a session still agrees, so the guard is blind")
    raise AssertionError(f"COMMENSURABILITY: with the map shifted one session only {still:.3f} of kept rows agree")


def audit_right_quantity(pin, pin_later, arms_same, arms_later):
    r = float(pd.Series(pin).corr(pd.Series(pin_later)))
    if not (np.isfinite(r) and abs(r) < 0.50):
        raise AssertionError(f"RIGHT QUANTITY: treatment and the later-expiry control correlate {r:+.3f}")
    if arms_same <= 0 or arms_later <= 0:
        raise AssertionError("RIGHT QUANTITY: an arm has no rows")
    return r


def guard_outputs(res):
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")


# ------------------------------------------------------------------ run
def run():
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    log(f"D614 STAGE 0 -- expiry pinning on ES from the noon 0DTE ladder; spec {SPEC}; "
        f"nothing from {RESERVED_FROM} on is read")
    audits = {}
    audits["column_mapping"] = audit_column_mapping()
    audits["column_mapping_raises"] = expect_raise(audit_column_mapping_broken, "the level read at the interaction's index")
    audits["sign_in_money_level"] = audit_sign_in_money()
    audits["sign_audit_raises"] = expect_raise(lambda: audit_sign_in_money(True), "a negated PIN")
    r81 = _load("d581", "stage0_d581_gamma_close.py")

    s, winfo = load_es()
    audits["price_second_path_sessions"] = audit_prices_vs_d581(s, r81)
    log(f"  ES sessions {s.index.min()} .. {s.index.max()}: {len(s)}; R2 and F5 equal D581's to 1e-12 "
        f"on {audits['price_second_path_sessions']} shared sessions")
    audits["trailing_clean"] = audit_trailing_no_lookahead(s)
    audits["trailing_raises"] = expect_raise(lambda: audit_trailing_broken(s), "the sigma30 lag dropped")

    g = load_ladder()
    dom = dominant_underlying()
    comm = audit_commensurate(dom.reindex(s.index), s["contract"])
    audits["commensurability"] = comm
    audits["commensurability_raises"] = expect_raise(lambda: audit_commensurate_raises(dom.reindex(s.index), s["contract"]),
                                                     "the contract map shifted one session")
    log(f"  commensurability: {comm['mismatched']} of {comm['sessions']} sessions quote the 0DTE ladder on a "
        f"different future ({comm['share']:.3f}) -- dropped")

    # ---- per session, per band, per arm
    zero = {k: v for k, v in g[g["arm"] == "zero_dte"].groupby("session")}
    later = {k: v for k, v in g[g["arm"] == "later"].groupby("session")}
    rows = {}
    for day in s.index:
        if not np.isfinite(s.loc[day, "sigma30_bp"]) or s.loc[day, "roll"]:
            continue
        if dom.get(day) != s.loc[day, "contract"]:
            continue
        gz = zero.get(day)
        if gz is None or gz["v12"].sum() <= 0:
            continue
        p, sp = float(s.loc[day, "P1530"]), float(s.loc[day, "sigma30_pts"])
        rec = {}
        for band, tag in BANDS:
            a = ladder_stats(gz, p, sp, band)
            if a is None:
                continue
            rec[f"PIN_{tag}"] = (a["K_vol"] - p) / sp
            rec[f"PING_{tag}"] = (a["K_grid"] - p) / sp
            rec[f"PINmax_{tag}"] = (a["K_max"] - p) / sp
            rec[f"PINoi_{tag}"] = (a["K_oi"] - p) / sp
            rec[f"PIN1530_{tag}"] = (a["K_vol1530"] - p) / sp
            for q in ("nK", "C", "C_norm", "C9", "v_total", "oi_total", "step", "v1530_total"):
                rec[f"{q}_{tag}"] = a[q]
            gl = later.get(day)
            if gl is not None and gl["v12"].sum() > 0:
                b = ladder_stats(gl, p, sp, band)
                if b is not None:
                    rec[f"PINlater_{tag}"] = (b["K_vol"] - p) / sp
                    rec[f"PINlaterOI_{tag}"] = (b["K_oi"] - p) / sp
        rows[day] = rec
    L = pd.DataFrame.from_dict(rows, orient="index").sort_index()
    P = s.join(L, how="inner")
    tag = PRIMARY_BAND
    P = P[np.isfinite(P[f"PIN_{tag}"]) & np.isfinite(P["R2"]) & np.isfinite(P["ON"])]
    log(f"  panel: {len(P)} sessions with a noon ladder, a lagged sigma30, no roll and a commensurate contract")

    audits["centroid_clean"] = float(audit_centroid(zero[P.index[10]]["strike"].to_numpy(float),
                                                    float(P.loc[P.index[10], "P1530"]),
                                                    zero[P.index[10]]["v12"].to_numpy(float)))
    def _broken():
        gs = zero[P.index[10]]
        k, w = gs["strike"].to_numpy(float), gs["v12"].to_numpy(float)
        a, b = centroid(k, w), centroid_broken(k, w)
        if abs(a - b) <= 1e-9 * abs(a):
            raise AssertionError("CENTROID: dividing by the count changed nothing, so the guard is blind")
        raise AssertionError(f"CENTROID: /n gives {b:.2f} against /sum(w) {a:.2f}")
    audits["centroid_raises"] = expect_raise(_broken, "dividing by the count instead of the weight total")
    med_gap = float(np.nanmedian(np.abs(P[f"PIN_{tag}"] - P[f"PING_{tag}"]) * P["sigma30_pts"]))
    if not med_gap > 0.5:
        raise AssertionError(f"WEIGHTS BITE: median |K_vol - K_grid| is {med_gap:.3f} points; PIN is PING")
    audits["weights_bite_median_points"] = med_gap

    # ---- the columns, fixed by the pre-registration
    def controls_for(band=tag, partner="PING"):
        """The fixed control set. `partner` is the OTHER ladder statistic held alongside the target.

        For every cell the grid centroid PING is a control. For the PLACEBO cell, whose target IS
        PING, the partner becomes PIN instead -- otherwise the design carries the same column twice,
        the fit is singular and the null explodes. That bug produced a |c| p95 of 6.4e13 on the first
        pass and is the reason this argument exists.
        """
        sig = P["sigma30_bp"].to_numpy(float)
        return {"ON": P["ON"].to_numpy(float) / sig, "DAY0": P["DAY0"].to_numpy(float) / sig,
                "MIDE": P["MIDE"].to_numpy(float) / sig, "F5": P["F5"].to_numpy(float) / sig,
                "PARTNER": P[f"{partner}_{band}"].to_numpy(float)}

    def builder_for(band=tag, partner="PING"):
        """cols = controls + the candidate target + every column DERIVED from it."""
        ctl = controls_for(band, partner)
        f5s = ctl["F5"]

        def build(pin):
            pin = np.asarray(pin, float)
            return dict(ctl, PIN=pin, F5xPIN=f5s * pin)
        return build

    def cols_for(pin_name, band=tag, partner="PING"):
        return builder_for(band, partner)(P[f"{pin_name}_{band}"].to_numpy(float))

    y = P["R2"].to_numpy(float)
    weeks = P["week"].to_numpy()
    years = P["year"].to_numpy()
    audits["right_quantity_corr"] = audit_right_quantity(
        P[f"PIN_{tag}"].to_numpy(float), P.get(f"PINlater_{tag}", pd.Series(np.nan, index=P.index)).to_numpy(float),
        int(sum(len(v) for v in zero.values())), int(sum(len(v) for v in later.values())))

    def cell(pin_name, band, label, with_flip=False, partner="PING"):
        base = P[f"{pin_name}_{band}"].to_numpy(float)
        build = builder_for(band, partner)
        ctl = controls_for(band, partner)
        c = build(base)
        audit_not_singular(c)
        f = fit_named(y, c)
        obs = f["coef"]["PIN"]
        fw_obs, fw_vals = shift_null_norm(y, ctl, base)
        out = {"label": label, "coef_bp_per_sigma": obs, "nw_t": f["t"]["PIN"], "n": f["n"],
               "coef_interaction": f["coef"]["F5xPIN"], "t_interaction": f["t"]["F5xPIN"],
               "coef_F5": f["coef"]["F5"], "t_F5": f["t"]["F5"], "coef_partner": f["coef"]["PARTNER"], "partner": partner,
               "shift_null_prereg": blk(obs, shift_null(y, build, base)),
               "shift_null_amended": blk(fw_obs, fw_vals),
               "fw_coef_no_interaction": fw_obs}
        out["week_block_se"] = week_block_se(y, c, "PIN", weeks, rng)
        out["t_week_block"] = obs / out["week_block_se"] if out["week_block_se"] else None
        if with_flip:
            fo, fv = flip_null(y, ctl, base)
            out["flip_null"] = blk(fo, fv)
        out["clears_economic_bar"] = bool(abs(obs) >= ECON_BAR_BP)
        # the economic quantity the bar was MEANT to express, in the units the account pays
        out["expected_move_bp_at_mean_abs_pin"] = float(abs(obs) * float(np.nanmean(np.abs(base))))
        out["se_ladder"] = se_ladder(y, c)
        out["tail_carried"] = tail_diagnostics(y, c)
        return out

    blockB = {"primary": cell("PIN", tag, f"PIN, band {tag}", with_flip=True)}
    pp = blockB["primary"]
    log(f"  PRIMARY  c {pp['coef_bp_per_sigma']:+.3f} bp/sigma  NW t {pp['nw_t']:+.2f}  "
        f"week-block t {pp['t_week_block']:+.2f}  expected move at mean|PIN| "
        f"{pp['expected_move_bp_at_mean_abs_pin']:.2f} bp")
    log(f"           amended null: two-sided rank {pp['shift_null_amended']['rank_two_sided']:.3f} "
        f"(|c| p95 {pp['shift_null_amended']['abs_p95']:.3f}), upper {pp['shift_null_amended']['rank_upper']:.3f}, "
        f"lower {pp['shift_null_amended']['rank_lower']:.3f}")
    log(f"           pre-reg null (anti-conservative, reported): rank "
        f"{pp['shift_null_prereg']['rank_two_sided']:.3f} (|c| p95 {pp['shift_null_prereg']['abs_p95']:.3f})")
    blockB["placebo_PING"] = cell("PING", tag, "PING, the grid-only placebo", partner="PIN")
    log(f"  PLACEBO  PING c {blockB['placebo_PING']['coef_bp_per_sigma']:+.3f}  NW t "
        f"{blockB['placebo_PING']['nw_t']:+.2f}  amended rank "
        f"{blockB['placebo_PING']['shift_null_amended']['rank_two_sided']:.3f}")
    fam = {}
    for band, btag in BANDS:
        fam[btag] = cell("PIN", btag, f"PIN, band {btag}")
        log(f"  band {btag:<5} c {fam[btag]['coef_bp_per_sigma']:+.3f}  NW t {fam[btag]['nw_t']:+.2f}  "
            f"amended rank {fam[btag]['shift_null_amended']['rank_two_sided']:.3f}  n {fam[btag]['n']}")
    blockB["family_by_band"] = fam
    fmax = max(fam.values(), key=lambda v: abs(v["coef_bp_per_sigma"]))
    blockB["family_max"] = {"band": fmax["label"], "abs_coef": abs(fmax["coef_bp_per_sigma"]),
                            "above_its_abs_p95_amended": fmax["shift_null_amended"]["above_abs_p95"]}
    blockB["PINmax"] = cell("PINmax", tag, "the single heaviest strike")
    blockB["PIN1530_descriptive"] = cell("PIN1530", tag,
                                         "the 15:30 cutoff -- DESCRIPTIVE, its in-sample reading is not blind")

    controls = {"weight_matched_oi_same_strikes": cell("PINoi", tag, "OI-weighted, same 0DTE strikes")}
    if f"PINlater_{tag}" in P.columns:
        controls["horizon_matched_volume_later"] = cell("PINlater", tag, "volume-weighted, nearest LATER expiry")
    if f"PINlaterOI_{tag}" in P.columns:
        controls["both_levers_oi_later"] = cell("PINlaterOI", tag, "OI-weighted, nearest later expiry")
    for k, v in controls.items():
        log(f"  control {k[:34]:<34} c {v['coef_bp_per_sigma']:+.3f}  NW t {v['nw_t']:+.2f}  "
            f"amended rank {v['shift_null_amended']['rank_two_sided']:.3f}")

    # ---- |PIN| buckets
    ap = np.abs(P[f"PIN_{tag}"].to_numpy(float))
    qs = np.nanquantile(ap, [1 / 3, 2 / 3])
    buck = {}
    for i in range(3):
        m = (np.digitize(ap, qs) == i)
        if m.sum() > 100:
            c = {k: v[m] for k, v in cols_for("PIN").items()}
            buck[f"tercile_{i}"] = {"coef": coef_named(y[m], c, "PIN"), "n": int(m.sum()),
                                    "mean_abs_pin": float(ap[m].mean())}
    blockB["by_abs_pin_tercile"] = buck
    eras = {}
    for lab, m in (("pre_2022_05", P.index.to_numpy() < "2022-05-02"), ("post_2022_05", P.index.to_numpy() >= "2022-05-02")):
        if m.sum() > 200:
            c = {k: v[m] for k, v in cols_for("PIN").items()}
            eras[lab] = {"coef": coef_named(y[m], c, "PIN"), "n": int(m.sum()),
                         "sd_PING": float(np.nanstd(P.loc[m, f"PING_{tag}"])),
                         "mean_nK": float(np.nanmean(P.loc[m, f"nK_{tag}"]))}
    blockB["eras"] = eras

    # ---- Block A, DESCRIPTIVE
    rvr = np.log(P["RV_late"].to_numpy(float) / P["RV_early"].to_numpy(float))
    bpvr = np.log(P["BPV_late"].to_numpy(float) / P["BPV_early"].to_numpy(float))
    blockA = {"note": "DESCRIPTIVE. The in-sample reading of this block is not blind: an adversarial "
                      "review measured it before the pre-registration. No verdict is drawn from it.",
              "rvr_mean": float(np.nanmean(rvr)), "rvr_sd": float(np.nanstd(rvr)),
              "share_close_louder": float(np.nanmean(rvr > 0)),
              "bpvr_mean": float(np.nanmean(bpvr)),
              "corr_rvr_bpvr": float(pd.Series(rvr).corr(pd.Series(bpvr)))}
    for cname in ("C", "C_norm", "C9"):
        x = P[f"{cname}_{tag}"].to_numpy(float)
        ter = np.digitize(x, np.nanquantile(x, [1 / 3, 2 / 3]))
        hi, lo = rvr[ter == 2], rvr[ter == 0]
        diff = float(np.nanmean(hi) - np.nanmean(lo))
        blockA[cname] = {"tercile_diff_rvr": diff,
                         "year_block_se": year_block_se(rvr[ter == 2], years[ter == 2], rng)
                                          + year_block_se(rvr[ter == 0], years[ter == 0], rng),
                         "corr_with_sigma30": float(pd.Series(x).corr(P["sigma30_bp"].reset_index(drop=True))),
                         "corr_with_one_over_n": float(pd.Series(x).corr(1.0 / P[f"nK_{tag}"].reset_index(drop=True))),
                         "guard_sigma_ok": None, "guard_floor_ok": None}
        b = blockA[cname]
        b["guard_sigma_ok"] = bool(abs(b["corr_with_sigma30"]) <= 0.40)
        b["guard_floor_ok"] = bool(b["corr_with_one_over_n"] <= 0.60)
        log(f"  blockA {cname:<7} tercile diff RVR {diff:+.3f}  corr(sigma30) {b['corr_with_sigma30']:+.3f} "
            f"(guard {b['guard_sigma_ok']})  corr(1/n) {b['corr_with_one_over_n']:+.3f} (guard {b['guard_floor_ok']})")

    # ---- Block C, the component line
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    tick_pts = float(spec["ES"]["tick_points"])
    tick_usd = float(spec["MES"]["tick_usd"])
    pt_usd = tick_usd / tick_pts
    cost_usd = COMM_RT + CROSS_TICKS * tick_usd
    move_pts = (P["P1600"] - P["P1530"]).to_numpy(float)
    comp = {}
    for lab, sgn in (("attraction", +1.0), ("repulsion", -1.0)):
        pos = sgn * np.sign(P[f"PIN_{tag}"].to_numpy(float))
        gross = pos * move_pts * pt_usd
        net = gross - np.where(pos != 0, cost_usd, 0.0)
        tr = net[pos != 0]
        srt = np.sort(tr)
        k = max(int(0.01 * srt.size), 1)
        comp[lab] = {"n_sessions": int((pos != 0).sum()),
                     "gross_mean_usd": float(np.nanmean(gross)), "net_mean_usd": float(np.nanmean(net)),
                     "net_sd_usd": float(np.nanstd(net)),
                     "net_sharpe": float(np.nanmean(net) / np.nanstd(net) * np.sqrt(252)) if np.nanstd(net) else None,
                     "net_sortino": float(np.nanmean(net) / np.nanstd(net[net < 0]) * np.sqrt(252))
                                    if (net < 0).any() and np.nanstd(net[net < 0]) else None,
                     "gross_sharpe": float(np.nanmean(gross) / np.nanstd(gross) * np.sqrt(252)) if np.nanstd(gross) else None,
                     "hit_rate": float(np.nanmean(tr > 0)), "median_usd": float(np.nanmedian(tr)),
                     "skew": float(pd.Series(tr).skew()), "kurtosis": float(pd.Series(tr).kurtosis()),
                     "trimmed_mean_usd": float(srt[k:srt.size - k].mean()),
                     "ex_top1_mean_usd": float(srt[:srt.size - k].mean()),
                     "ex_bottom1_mean_usd": float(srt[k:].mean()),
                     "cost_usd_per_round_trip": cost_usd,
                     "breakeven_bp_per_side": float(1e4 * (cost_usd / 2) / (pt_usd * float(P["P1530"].mean()))),
                     # the three the pre-registration asks for and an earlier pass omitted
                     "exposure_share_of_sessions": float((pos != 0).mean()),
                     "exposure_minutes_per_session": 30.0,
                     "payoff_win_over_loss": (float(tr[tr > 0].mean() / abs(tr[tr < 0].mean()))
                                              if (tr > 0).any() and (tr < 0).any() else None),
                     "max_drawdown_usd": float(np.min(np.cumsum(net) - np.maximum.accumulate(np.cumsum(net)))),
                     "max_drawdown_convention": "NEGATIVE dollars from the running peak of the cumulative "
                                                "net series; not a fraction of peak, because a one-lot book "
                                                "has no equity base to divide by"}
    comp["mes_point_usd"] = pt_usd
    comp["rho_with_macd_arm"] = macd_rho(P.index, comp, y, P, pt_usd, cost_usd, tag)
    log(f"  component attraction net ${comp['attraction']['net_mean_usd']:+.2f}/session, Sharpe "
        f"{comp['attraction']['net_sharpe']}, Sortino {comp['attraction']['net_sortino']}; "
        f"rho with the MACD arm {comp['rho_with_macd_arm']}")

    beside = {"corr_PIN_PIN1530": float(pd.Series(P[f"PIN_{tag}"].to_numpy()).corr(
                  pd.Series(P[f"PIN1530_{tag}"].to_numpy()))),
              "sawtooth_sigma_by_era": {},
              "vol_to_oi_ratio_median": float(np.nanmedian(P[f"v_total_{tag}"] / P[f"oi_total_{tag}"].replace(0, np.nan))),
              "R2_halves": {"first": float(np.nanmean(P["R2a"])), "second": float(np.nanmean(P["R2b"]))},
              "largest_abs_R2": [{"session": str(P.index[i]), "R2_bp": float(y[i]),
                                  "PIN": float(P[f"PIN_{tag}"].to_numpy()[i])}
                                 for i in np.argsort(-np.abs(y))[:10]]}
    for lab, m in (("pre_2022_05", P.index.to_numpy() < "2022-05-02"), ("post_2022_05", P.index.to_numpy() >= "2022-05-02")):
        saw = 2.5 / P.loc[m, "sigma30_pts"]
        beside["sawtooth_sigma_by_era"][lab] = {"mean_half_step_in_sigma": float(np.nanmean(saw)),
                                                "sd_PING": float(np.nanstd(P.loc[m, f"PING_{tag}"])),
                                                "mean_nK": float(np.nanmean(P.loc[m, f"nK_{tag}"]))}

    pr = blockB["primary"]
    ping = blockB["placebo_PING"]
    preds = {
        "P1_primary_above_abs_p95_and_t2": bool(pr["shift_null_amended"]["above_abs_p95"] and abs(pr["nw_t"]) >= 2.0),
        # B4 as PRE-REGISTERED: the trial is void only if the placebo passes the SAME conjunction the
        # primary must (B1 rank AND B2 |t| >= 2). An earlier version of this line tested the rank alone,
        # which is stricter than the record and would have voided on a placebo failing every robust t.
        "P2_placebo_fails_its_conjunction": bool(not (ping["shift_null_amended"]["above_abs_p95"]
                                                      and abs(ping["nw_t"]) >= 2.0)),
        "P2a_placebo_clears_the_rank_bar_alone": bool(ping["shift_null_amended"]["above_abs_p95"]),
        "P3_controls_inside": bool(all(not v["shift_null_amended"]["above_abs_p95"] for v in controls.values())),
        "P5_stronger_at_small_abs_pin": bool(len(buck) == 3 and abs(buck["tercile_0"]["coef"]) > abs(buck["tercile_2"]["coef"])),
        "P6_commensurability_drop_5_to_9pct": bool(0.05 <= comm["share"] <= 0.09),
        "P7_sawtooth_larger_pre_2022": bool(beside["sawtooth_sigma_by_era"]["pre_2022_05"]["sd_PING"]
                                            > beside["sawtooth_sigma_by_era"]["post_2022_05"]["sd_PING"]),
        "economic_bar_15bp": pr["clears_economic_bar"],
    }
    if ping["shift_null_amended"]["above_abs_p95"] and abs(ping["nw_t"]) >= 2.0:
        verdict = "VOID -- the grid-only placebo clears the same bar"
    elif not preds["P1_primary_above_abs_p95_and_t2"]:
        verdict = "NOT SUPPORTED"
    elif not pr["clears_economic_bar"]:
        verdict = "REAL BUT NOT TRADEABLE -- the line closes"
    elif pr["coef_bp_per_sigma"] > 0:
        verdict = "SUPPORTED, attraction (dealers long 0DTE gamma)"
    else:
        verdict = "SUPPORTED, repulsion (dealers short 0DTE gamma)"

    sets = {"es_sessions": int(len(s)), "panel_sessions": int(len(P)),
            "sessions_dropped_roll": int(s["roll"].sum()),
            "commensurability_dropped": comm["mismatched"],
            "mean_abs_pin": float(np.nanmean(np.abs(P[f"PIN_{tag}"]))),
            "sd_pin": float(np.nanstd(P[f"PIN_{tag}"])),
            "sd_R2_bp": float(np.nanstd(y)),
            "mde_bp_per_sigma_at_t2_textbook": float(2 * np.nanstd(y) / (np.nanstd(P[f"PIN_{tag}"]) * np.sqrt(len(P)))),
            "mde_bp_per_sigma_at_t2_from_nw_se": float(2 * abs(blockB["primary"]["coef_bp_per_sigma"]
                                                               / blockB["primary"]["nw_t"]))
            if blockB["primary"]["nw_t"] else None,
            "mde_note": "the textbook figure is sd(y)/(sd(x)sqrt(n)); the fitted NW se is several times it, "
                        "because the regressor is correlated with the controls and HAC carries the "
                        "heteroskedasticity of a heavy-tailed regressor. The NW figure is the honest one.",
            "weekday_counts": {str(k): int(v) for k, v in pd.Series(P["dow"]).value_counts().sort_index().items()}}
    premise = {"corr_PIN_DAY0": float(pd.Series(P[f"PIN_{tag}"].to_numpy()).corr(pd.Series(P["DAY0"].to_numpy()))),
               "corr_PIN_F5": float(pd.Series(P[f"PIN_{tag}"].to_numpy()).corr(pd.Series(P["F5"].to_numpy()))),
               "corr_PIN_PING": float(pd.Series(P[f"PIN_{tag}"].to_numpy()).corr(pd.Series(P[f"PING_{tag}"].to_numpy()))),
               "ac1_PIN": float(pd.Series(P[f"PIN_{tag}"].to_numpy()).autocorr(1)),
               "ac1_C": float(pd.Series(P[f"C_{tag}"].to_numpy()).autocorr(1)),
               "share_noon_of_1530_volume": float(P[f"v_total_{tag}"].sum()
                                                  / max(P[f"v1530_total_{tag}"].sum(), 1.0))}
    log(f"  premise: corr(PIN, DAY0) {premise['corr_PIN_DAY0']:+.3f}, corr(PIN, F5) {premise['corr_PIN_F5']:+.3f}, "
        f"corr(PIN, PING) {premise['corr_PIN_PING']:+.3f}, ac1(PIN) {premise['ac1_PIN']:+.3f}")
    log(f"  MDE at |t|=2: textbook {sets['mde_bp_per_sigma_at_t2_textbook']:.2f}, from the fitted NW se "
        f"{sets['mde_bp_per_sigma_at_t2_from_nw_se']:.2f} bp/sigma; economic bar {ECON_BAR_BP} bp/sigma")
    log(f"  sd(PIN) {sets['sd_pin']:.3f}, mean |PIN| {sets['mean_abs_pin']:.3f} -- the economic bar was set in "
        f"bp PER SIGMA assuming sd(PIN) near 0.3, and the unbanded primary has it near 3, so the bar and the "
        f"expected move ({pp['expected_move_bp_at_mean_abs_pin']:.2f} bp) are not the same yardstick")
    sl = pp["se_ladder"]
    log("  se ladder: " + "  ".join(f"{k.split('_')[0]} t {v['t']:+.2f}" for k, v in sl.items()
                                    if isinstance(v, dict)))
    log(f"  estimators agree on |t| >= 2: {sl['all_estimators_agree']}")
    td = pp["tail_carried"]
    log(f"  tail: top-10 |PIN| sessions carry {td['share_of_sum_sq_in_top10']:.3f} of sum(PIN^2), their mean |R2| "
        f"{td['mean_abs_y_in_top10_bp']:.0f} bp against {td['mean_abs_y_bp']:.1f}; dropping them moves c from "
        f"{td['coef_full']:+.3f} to {td['coef_excluding_top10']:+.3f}")
    log(f"  predictions: " + "; ".join(f"{k} {v}" for k, v in preds.items()))
    log(f"  STAGE 0 VERDICT: {verdict}")

    res = {"spec": SPEC, "windows": {"in_sample": [IN_FROM, IN_TO], "reserved_from": RESERVED_FROM,
                                     "scored_window": [T_ENTRY, T_CLOSE], "conditioner_cutoff": T_NOON,
                                     **winfo},
           "sets": sets, "audits": audits, "premise": premise, "blockA": blockA, "blockB": blockB,
           "controls": controls, "component": comp, "beside": beside, "predictions": preds,
           "verdict": verdict, "timing_s": round(time.time() - t0, 1),
           "construction": {"primary": "the LEVEL coefficient on PIN, read by name; the interaction is a diagnostic",
                            "bands": [b for _, b in BANDS], "primary_band": PRIMARY_BAND,
                            "controls": "grid placebo, OI-weighted same strikes, volume-weighted nearest later "
                                        "expiry (horizon-matched), OI-weighted nearest later expiry",
                            "nulls": "enumerated session shift (every column but PIN held fixed); the sign-flip "
                                     f"null sampled at {FLIP_DRAWS} draws seed {SEED}, the one sampled null",
                            "economic_bar_bp_per_sigma": ECON_BAR_BP, "nw_lag": NW_LAG,
                            "later_expiry_rule": "the NEAREST expiry strictly after the session"}}
    guard_outputs(res)
    expect_raise(lambda: guard_outputs({k: v for k, v in res.items() if k != "blockB"}), "a missing declared output")
    OUT.write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)),
                   encoding="utf-8")
    log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']} s")
    return 0


def macd_rho(index, comp, y, P, pt_usd, cost_usd, tag):
    """rho of the pull book's daily dollars with the admitted MACD arm, computed HERE (D466)."""
    try:
        d504 = _load("d504_arm", "d504_arm_full_history.py")
        d484 = sys.modules["d484_offdiagonal_and_macd"]
        d503 = sys.modules["d503_forward_book"]
        d495 = sys.modules["d495_agree_confluence"]
        d491 = sys.modules["d491_conditional_hold"]
        meta = json.loads(d495.META.read_text(encoding="utf-8"))
        spec = json.loads(d484.SPECS.read_text(encoding="utf-8"))
        d_all = pd.read_csv(d495.FIX, encoding="utf-8")
        ser = d503.series_window(d504.ROOT, d_all, meta, "2010-01-01", IN_TO)
        nseg = len(d484.SEGMENTS)
        k = len(ser["log_close"]) // nseg
        gg = lambda a: np.exp(a[:k * nseg]).reshape(k, nseg)   # noqa: E731
        md = d484.impulse_macd(ser["log_high"], ser["log_low"], ser["log_close"])[1][:k * nseg]
        b1 = np.where(md == 0.0, 0.0, np.sign(d484.impulse_macd(
            ser["log_high"], ser["log_low"], ser["log_close"])[0][:k * nseg])).reshape(k, nseg)
        b2 = np.sign(d484.macd_hist(ser["log_close"])[:k * nseg]).reshape(k, nseg)
        pure = ser["pure"][:k * nseg].reshape(k, nseg)
        keep = pure[:, d491.DAY_FIRST_DECIDE:d491.LAST_SEG + 1].all(axis=1)
        days = ser["days"][:k][keep]
        if max(days) > IN_TO:
            raise AssertionError("the MACD arm reached the reserved slice")
        rows = d503.simulate_trades(gg(ser["log_open"])[keep], gg(ser["log_close"])[keep],
                                    d495.agree_signal(b1, b2)[keep], d491.DAY_FIRST_DECIDE, d504.M_HOLD,
                                    d484.COMMISSION_RT / float(spec[d504.SIZED]["tick_usd"]) + d484.CROSS_TICKS,
                                    float(spec[d504.ROOT]["tick_points"]))
        tk = np.zeros(len(days))
        for r in rows:
            tk[int(r[0])] += float(r[4])
        arm = pd.Series(tk * float(spec[d504.SIZED]["tick_usd"]), index=pd.Index(days))
        pos = np.sign(P[f"PIN_{tag}"].to_numpy(float))
        mine = pd.Series(pos * (P["P1600"] - P["P1530"]).to_numpy(float) * pt_usd - cost_usd, index=P.index)
        j = pd.concat([mine.rename("pull"), arm.rename("macd")], axis=1).dropna()
        return {"rho": float(j["pull"].corr(j["macd"])), "overlapping_sessions": int(len(j)),
                "macd_sessions": int(len(arm)), "note": "computed in this runner at MES/MNQ minimum size"}
    except Exception as e:                                    # noqa: BLE001
        return {"rho": None, "error": f"{type(e).__name__}: {e}"}


def selftest():
    log("  selftest")
    m = audit_column_mapping()
    log(f"  column mapping: named level {m['level']:+.3f}, interaction {m['interaction']:+.3f} on a level-only panel")
    expect_raise(audit_column_mapping_broken, "the level read at the interaction's index")
    log(f"  sign in money: level {audit_sign_in_money():+.3f}")
    expect_raise(lambda: audit_sign_in_money(True), "a negated PIN")
    k = np.array([4000.0, 4005.0, 4010.0, 4015.0])
    w = np.array([1.0, 3.0, 0.0, 6.0])
    a = audit_centroid(k, 4007.0, w)
    log(f"  centroid: two routes agree at {a:.4f}")
    def _b():
        if abs(centroid(k, w) - centroid_broken(k, w)) <= 1e-9:
            raise AssertionError("CENTROID: the break changed nothing")
        raise AssertionError(f"CENTROID: /n gives {centroid_broken(k, w):.2f} against {centroid(k, w):.2f}")
    expect_raise(_b, "dividing by the count instead of the weight total")
    rng = np.random.default_rng(3)
    n = 800
    f5 = rng.normal(0, 1, n)
    pin = rng.normal(0, 1, n)
    yy = 4.0 * pin + rng.normal(0, 8, n)
    ctl = {"F5": f5, "PING": rng.normal(0, 1, n)}
    build = lambda p: dict(ctl, PIN=np.asarray(p, float), F5xPIN=f5 * np.asarray(p, float))   # noqa: E731
    b = blk(coef_named(yy, build(pin), "PIN"), shift_null(yy, build, pin, kmin=5))
    if not b["above_abs_p95"]:
        raise AssertionError(f"shift null cannot detect a planted level effect: {b}")
    log(f"  pre-reg shift null on a planted effect: c {b['observed']:+.3f}, two-sided rank "
        f"{b['rank_two_sided']:.3f}, upper {b['rank_upper']:.3f}")
    noise = rng.normal(0, 8, n)
    flat = blk(coef_named(noise, build(pin), "PIN"), shift_null(noise, build, pin, kmin=5))
    if flat["above_abs_p95"]:
        raise AssertionError(f"shift null fires on noise: {flat}")
    log(f"  pre-reg shift null on noise: two-sided rank {flat['rank_two_sided']:.3f}")
    ao, av = shift_null_norm(yy, ctl, pin, kmin=5)
    ab = blk(ao, av)
    if not ab["above_abs_p95"]:
        raise AssertionError(f"amended null cannot detect a planted level effect: {ab}")
    no, nv = shift_null_norm(noise, ctl, pin, kmin=5)
    nb = blk(no, nv)
    if nb["above_abs_p95"]:
        raise AssertionError(f"amended null fires on noise: {nb}")
    log(f"  amended (norm-preserving) null: planted rank {ab['rank_two_sided']:.3f} c {ao:+.3f}; "
        f"noise rank {nb['rank_two_sided']:.3f}")
    # the amendment's whole point: on a design whose target is CORRELATED with a control, the
    # pre-registered null's spread is too tight and the amended one is not
    corr_pin = 0.7 * ctl["F5"] + 0.7 * rng.normal(0, 1, n)
    yc = 4.0 * corr_pin + rng.normal(0, 8, n)
    pre_sd = float(np.std(shift_null(yc, lambda p: dict(ctl, PIN=np.asarray(p, float),
                                                       F5xPIN=f5 * np.asarray(p, float)), corr_pin, kmin=5)))
    _, amv = shift_null_norm(yc, ctl, corr_pin, kmin=5)
    log(f"  on a target correlated with a control: pre-reg null sd {pre_sd:.4f} vs amended "
        f"{float(np.std(amv)):.4f} -- the pre-registered one is the tighter, which is the defect")
    if not float(np.std(amv)) > pre_sd:
        raise AssertionError("the amendment did not widen the null on a correlated target, so it fixes nothing")
    fo, fv = flip_null(yy, ctl, pin, draws=200, seed=1)
    fl = blk(fo, fv)
    log(f"  flip null on the planted effect: two-sided rank {fl['rank_two_sided']:.3f}")
    audit_not_singular({"A": f5, "B": pin})
    log("  singularity guard: two distinct columns pass")
    expect_raise(lambda: audit_not_singular({"A": f5, "B": f5 * 1.0}), "one column present twice")
    expect_raise(lambda: audit_right_quantity(pin, pin, 1, 1), "a control identical to the treatment")
    expect_raise(lambda: audit_right_quantity(pin, rng.normal(0, 1, n), 0, 1), "an empty arm")
    expect_raise(lambda: guard_outputs({"spec": 1}), "missing outputs")
    log("  selftest: every audit passes its clean case and raises on its break")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else run() if a.run else 1)
