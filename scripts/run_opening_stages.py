"""D645 runner: the opening agent-state model's stages and tests (OPENING_AGENT_STATE_PREREG.md s.7-s.9, s.13 phases
3-5; OA-A1 .. OA-A7; O-D4 kept: three states). Written after D645 (17c2b05) and committed BEFORE its run.

    uv run python scripts/run_opening_stages.py --selftest          # the venv (scikit-learn); every audit fires
    uv run python scripts/run_opening_stages.py --dry-run           # synthetic bars on the real calendar; writes nothing
    uv run python scripts/run_opening_stages.py --run --phase 3     # ONCE: S-A -> data/opening/phase3_S-A.json + trials
    uv run python scripts/run_opening_stages.py --check --phase 3   # the rebuild equals the committed output

PHASE 3: stage S-A (the five observables + the market dummy) through the walk-forward. It gives
H-O1 at 10:00, H-O3 at every checkpoint, and S-A's H-O2 statistic at both t0 (the retention rule's reference).
PHASES 4-5 (--phase 4-5): scripts/opening_phase45.py, after A7 is resolved (D645 s.2), with OA-A8's diagnostics.

Readings fixed here, before the run (D645 leaves them to the code):
- Feature 4 is r(09:30 -> t) x d0 / sigma. At t = t0 that is |r| / sigma, as D645 s.2 writes it. At a later
  checkpoint (the state-flip models) it keeps its sign relative to the trade's d0(t0).
- "t >= 2 after Holm" is read as Holm on the two t0's two-sided HAC p-values at 0.05, with a positive difference.
  The programme's bar is the adjusted two-sided p <= 0.005 (12A.2).
- A session-market row exists when the day is usable, not excluded, and d0(t0) != 0. Every strategy (the policy and
  B1-B3) is scored on the same rows, with 0 on a no-trade day.
- A stop fill is the stop price, or the bar's open when the bar opens through it (pessimistic).
Nothing on or after 2025-03-01 is read (A10).
"""
from __future__ import annotations

import argparse
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
from scipy import stats
from sklearn.linear_model import LogisticRegression

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from backtest_framework.opening import agents as AG  # noqa: E402
from backtest_framework.opening.labels import classify  # noqa: E402
from backtest_framework.validation.frozen import assert_none_at_or_after, filter_before  # noqa: E402
from backtest_framework.validation.programme import TrialsCsv  # noqa: E402

_s = importlib.util.spec_from_file_location("opening_gate0", REPO / "scripts" / "opening_gate0.py")
assert _s is not None and _s.loader is not None
G0 = importlib.util.module_from_spec(_s)
sys.modules["opening_gate0"] = G0
_s.loader.exec_module(G0)

OD = REPO / "data" / "opening"
SPEC = REPO / "docs" / "decisions" / "D645-PRE-REG-opening-model-stages-and-tests-phases-3-5.md"
RESERVED_FROM = "2025-03-01"
ROOTS = ("ES", "NQ")
CLASSES = ("CONT", "FADE", "RANGE")  # REV merged into RANGE (O-D4); sklearn orders classes alphabetically too
CHECKPOINTS = ("09:45", "10:00", "10:30", "11:00")
TRADE_T0 = ("09:45", "10:00")
H_O1_T0 = "10:00"
TRAIN, TEST = 252, 63
C_GRID = (0.001, 0.01, 0.1, 1.0, 10.0)
N_FOLD = 5
THETA, FLIP = 0.45, 0.30
HOLD_MIN = 60
B3_LAST = "11:29"  # the break bar must close by 11:30
MAX_FEATURES = 11
SEED, N_PERM = 645, 1000
NW_LAG = 5
USD_PER_POINT = {"ES": 5.0, "NQ": 2.0}
COST_USD = {"ES": 3.0 + 1.1345 * 1.25 + 1.25, "NQ": 3.0 + 2.1342 * 0.5 + 0.5}  # D508 + $3 + one tick (OA-A5)
S_A = ("gap_atr", "loc_with", "loc_against", "r_sigma", "vol_z")
#: the (checkpoint, label t0) models every stage needs: H-O1/H-O3 at t = t0, and the state-flip exits' later checkpoints
PAIRS45 = tuple(sorted({(t, t) for t in CHECKPOINTS} | {("10:00", "09:45"), ("10:30", "09:45"), ("10:30", "10:00"),
                                                         ("11:00", "10:00")}))


class OpeningRunError(RuntimeError):
    pass


def hm(s: str) -> int:
    return int(s[:2]) * 60 + int(s[3:])


def hhmm(m: int) -> str:
    return f"{m // 60:02d}:{m % 60:02d}"


# =============================================================================================== sessions and labels
def session_table(b: pd.DataFrame, use: list[str], roots: tuple[str, ...] = ROOTS) -> dict[str, pd.DataFrame]:
    """Per market: every fixture session's RTH summary (OA-A6) plus, per checkpoint t, the 09:30 -> t window's
    price, range, bar count and volume, from bars whose START is before t (so they close by t)."""
    out = {}
    for r in roots:
        d = G0.daily_frame(b, r)
        x = b[(b["root"] == r) & (b["hhmm"] >= "09:30") & (b["hhmm"] <= "15:59")]
        for t in CHECKPOINTS:
            w = window(x, t)
            g = w.groupby("session")
            d[f"px_{t}"] = g["close"].last().reindex(d.index)
            d[f"hi_{t}"], d[f"lo_{t}"] = g["high"].max().reindex(d.index), g["low"].min().reindex(d.index)
            d[f"n_{t}"] = g.size().reindex(d.index, fill_value=0)
            d[f"vol_{t}"] = g["volume"].sum().reindex(d.index)
        d["prior_high"], d["prior_low"] = d["high"].shift(1), d["low"].shift(1)
        d["usable"] = d.index.isin(use)
        out[r] = d
    return out


def window(x: pd.DataFrame, t: str) -> pd.DataFrame:
    """The bars a feature at checkpoint t may read: those starting from 09:30 up to t - 1 minute."""
    return x[(x["hhmm"] >= "09:30") & (x["hhmm"] <= G0.minus_one(t))]


def labels_at(d: pd.DataFrame, t0: str) -> tuple[np.ndarray, np.ndarray]:
    """(d0, label) per session under D644/OA-A6 at t0, REV merged into RANGE; excluded days carry NaN d0."""
    need = 0.9 * (hm(t0) - hm("09:30"))
    bad = d["open"].isna() | (d[f"n_{t0}"] < need) | ~d["usable"]
    d0 = np.sign(d[f"px_{t0}"] - d["open"]).to_numpy(float).copy()
    d0[bad.to_numpy()] = np.nan
    lab = classify(d0, d["open"], d["close"], d["high"], d["low"], d["ib_high"], d["ib_low"], d["prior_close"],
                   d["atr20"])
    lab = np.where(lab == "REV", "RANGE", lab).astype(object)
    return d0, lab


# =============================================================================================== features (S-A)
def features_sa(d: pd.DataFrame, t: str, d0: np.ndarray) -> pd.DataFrame:
    """The five observables at checkpoint t, direction-relative to d0 (D645 s.2). Prior-session quantities come from
    earlier rows only (ATR20, prior close/extremes, the prior-window sigma and volume statistics)."""
    gap = (d["open"] - d["prior_close"]).to_numpy(float)
    o = d["open"].to_numpy(float)
    ph, pl = d["prior_high"].to_numpy(float), d["prior_low"].to_numpy(float)
    r = (d[f"px_{t}"] / d["open"] - 1).to_numpy(float)
    sig = AG.prior_std(r)
    lv = np.log(d[f"vol_{t}"].to_numpy(float))
    lv[~np.isfinite(lv)] = np.nan
    mu = pd.Series(lv).shift(1).rolling(AG.STD_WINDOW, min_periods=AG.STD_MIN).mean().to_numpy()
    sd = AG.prior_std(lv)
    above, below = o > ph, o < pl
    return pd.DataFrame({
        "gap_atr": gap * d0 / d["atr20"].to_numpy(float),
        "loc_with": np.where(d0 > 0, above, below).astype(float),
        "loc_against": np.where(d0 > 0, below, above).astype(float),
        "r_sigma": r * d0 / sig,
        "vol_z": (lv - mu) / sd,
    }, index=d.index)


def leak_check(feature_fn: Callable[[pd.DataFrame, str], pd.DataFrame], x: pd.DataFrame, t: str,
               sessions: list[str], rng: np.random.Generator) -> None:
    """The leak canary's check (deposit test 25): corrupt one session's bars AFTER t and require that session's
    feature row to be unchanged. A feature reading any bar at or after t fails it. The checked rows must be mostly
    finite, or the comparison proves nothing."""
    base = feature_fn(x, t)
    chosen = rng.choice(sessions, size=min(8, len(sessions)), replace=False)
    if np.isfinite(base.loc[chosen].to_numpy(float)).mean() < 0.9:
        raise OpeningRunError(f"leak check at {t}: the checked rows are mostly NaN, so the check would be hollow")
    for s in chosen:
        y = x.copy()
        m = (y["session"] == s) & (y["hhmm"] >= t)
        for c in ("open", "high", "low", "close"):
            y.loc[m, c] = y.loc[m, c] * 1.37
        y.loc[m, "volume"] = y.loc[m, "volume"] * 3
        got = feature_fn(y, t)
        a, bb = base.loc[s].to_numpy(float), got.loc[s].to_numpy(float)
        if not np.allclose(a, bb, equal_nan=True):
            raise OpeningRunError(f"leak: a feature at {t} changed when bars at/after {t} of {s} changed")


def check_budget(cols: list[str]) -> None:
    if len(cols) > MAX_FEATURES:
        raise OpeningRunError(f"parameter budget: {len(cols)} features > {MAX_FEATURES} (s.7.3)")
    if any(c in ("label", "d0_label", "y") for c in cols):
        raise OpeningRunError("a label column reached the features (deposit test 2)")


# =============================================================================================== datasets
def dataset(tab: dict[str, pd.DataFrame], t: str, t0: str) -> pd.DataFrame:
    """Rows (session, market) with labels at t0 and S-A features at t (direction-relative to d0(t0))."""
    rows = []
    for r in ROOTS:
        d = tab[r]
        d0, lab = labels_at(d, t0)
        f = features_sa(d, t, d0)
        f["root"], f["session"], f["d0"], f["label"] = r, d.index, d0, lab
        f["nq"] = float(r == "NQ")
        rows.append(f)
    D = pd.concat(rows, ignore_index=True)
    D = D[np.isfinite(D["d0"]) & (D["d0"] != 0) & D["label"].notna()]
    ok = np.isfinite(D[list(S_A)].to_numpy(float)).all(axis=1)
    D = D[ok].sort_values(["session", "root"], kind="stable").reset_index(drop=True)
    return D[D["session"] >= "2016-01-04"]


def windows(sessions: list[str]) -> list[tuple[list[str], list[str]]]:
    out = []
    for i in range(0, len(sessions) - TRAIN, TEST):
        tr, te = sessions[i:i + TRAIN], sessions[i + TRAIN:i + TRAIN + TEST]
        if set(tr) & set(te):
            raise OpeningRunError("walk-forward: a training session is also a test session")
        out.append((tr, te))
    return out


def fit(X: np.ndarray, y: np.ndarray, C: float) -> LogisticRegression:
    m = LogisticRegression(C=C, max_iter=5000, tol=1e-8)
    m.fit(X, y)
    return m


def proba(m: LogisticRegression, X: np.ndarray) -> np.ndarray:
    p = np.zeros((len(X), len(CLASSES)))
    got = m.predict_proba(X)
    for j, c in enumerate(m.classes_):
        p[:, CLASSES.index(c)] = got[:, j]
    return p


def logloss(p: np.ndarray, y: np.ndarray) -> float:
    idx = np.array([CLASSES.index(v) for v in y])
    return float(-np.mean(np.log(np.clip(p[np.arange(len(y)), idx], 1e-15, 1.0))))


def walk_forward(D: pd.DataFrame, cols: list[str], cal: list[str]) -> pd.DataFrame:
    """OOS probabilities for every test-window row, the penalty chosen by blocked 5-fold CV inside each training
    window. Returns D's test rows with p_CONT, p_FADE, p_RANGE, base-rate probabilities and the chosen C."""
    check_budget(cols)
    out = []
    for tr_s, te_s in windows(cal):
        tr = D[D["session"].isin(tr_s)]
        te = D[D["session"].isin(te_s)]
        if len(te) == 0 or tr["label"].nunique() < 2:
            continue
        mu = tr[cols].mean()
        sd = tr[cols].std(ddof=0).replace(0, 1.0)
        Xtr = np.column_stack([((tr[cols] - mu) / sd).to_numpy(float), tr["nq"].to_numpy(float)])
        Xte = np.column_stack([((te[cols] - mu) / sd).to_numpy(float), te["nq"].to_numpy(float)])
        ytr = tr["label"].to_numpy()
        blocks = np.array_split(np.array(tr_s), N_FOLD)
        best, best_ll = C_GRID[0], math.inf
        for C in C_GRID:
            lls = []
            for blk in blocks:
                vm = tr["session"].isin(set(blk)).to_numpy()
                if vm.all() or not vm.any() or len(set(ytr[~vm])) < 2:
                    continue
                m = fit(Xtr[~vm], ytr[~vm], C)
                lls.append(logloss(proba(m, Xtr[vm]), ytr[vm]))
            ll = float(np.mean(lls)) if lls else math.inf
            if ll < best_ll - 1e-12:
                best, best_ll = C, ll
        m = fit(Xtr, ytr, best)
        p = proba(m, Xte)
        if not out:  # the right-quantity audit: a fit that SAW the test rows must predict them differently
            mj = fit(np.vstack([Xtr, Xte]), np.concatenate([ytr, te["label"].to_numpy()]), best)
            joint_diff = float(np.abs(proba(mj, Xte) - p).max())
        base = np.zeros((len(te), len(CLASSES)))
        for r in ROOTS:
            fr = tr.loc[tr["root"] == r, "label"].value_counts(normalize=True)
            mask = (te["root"] == r).to_numpy()
            for j, c in enumerate(CLASSES):
                base[mask, j] = fr.get(c, 0.0)
        te = te.assign(**{f"p_{c}": p[:, j] for j, c in enumerate(CLASSES)},
                       **{f"b_{c}": base[:, j] for j, c in enumerate(CLASSES)}, C=best)
        out.append(te)
    res = pd.concat(out, ignore_index=True)
    res.attrs["oos_vs_joint_maxdiff"] = joint_diff
    return res


def audit_oos(P: pd.DataFrame, tol: float = 1e-9) -> None:
    if P.attrs.get("oos_vs_joint_maxdiff", 0.0) <= tol:
        raise OpeningRunError("right quantity: the OOS predictions equal a fit that saw the test rows")


# =============================================================================================== H-O1 / H-O3
def classification_report(P: pd.DataFrame, rng: np.random.Generator | None, n_perm: int = N_PERM) -> dict[str, Any]:
    y = P["label"].to_numpy()
    p = P[[f"p_{c}" for c in CLASSES]].to_numpy(float)
    b = P[[f"b_{c}" for c in CLASSES]].to_numpy(float)
    pred = np.array(CLASSES)[p.argmax(axis=1)]
    bpred = np.array(CLASSES)[b.argmax(axis=1)]
    acc, bacc = float((pred == y).mean()), float((bpred == y).mean())
    ll, bll = logloss(p, y), logloss(b, y)
    onehot = np.array([[float(v == c) for c in CLASSES] for v in y])
    brier = float(np.mean(np.sum((p - onehot) ** 2, axis=1)))
    conf = pd.crosstab(pd.Series(y, name="label"), pd.Series(pred, name="pred")).reindex(
        index=list(CLASSES), columns=list(CLASSES), fill_value=0)
    pmax = p.max(axis=1)
    bins = np.minimum((pmax * 10).astype(int), 9)
    rel = {f"{k / 10:.1f}": {"n": int((bins == k).sum()), "pred": float(pmax[bins == k].mean()),
                             "realised": float((pred[bins == k] == y[bins == k]).mean())}
           for k in range(10) if (bins == k).any()}
    top = max(rel) if rel else None
    out: dict[str, Any] = {"n": int(len(y)), "accuracy": acc, "base_accuracy": bacc, "logloss": ll,
                           "base_logloss": bll, "brier": brier, "confusion": conf.to_dict(), "reliability": rel,
                           "calibration_flag": bool(top is not None and rel[top]["pred"] >= 0.6
                                                    and rel[top]["realised"] < 0.45),
                           "pred_share": {c: float((pred == c).mean()) for c in CLASSES}}
    if rng is not None:
        grp = (P["root"] + "_" + P["session"].str[:4]).to_numpy()
        idx = [np.flatnonzero(grp == g) for g in np.unique(grp)]
        null = np.empty(n_perm)
        for k in range(n_perm):
            yy = y.copy()
            for ix in idx:
                yy[ix] = y[rng.permutation(ix)]
            null[k] = (pred == yy).mean()
        out["perm"] = {"p": float((null >= acc).mean()), "p50": float(np.median(null)),
                       "p95": float(np.quantile(null, 0.95))}
        out["pass"] = bool(ll < bll and acc > bacc and out["perm"]["p"] < 0.05)
    return out


# =============================================================================================== trading (H-O2)
def bar_arrays(b: pd.DataFrame) -> dict[tuple[str, str], dict[str, np.ndarray]]:
    x = b[(b["hhmm"] >= "09:30") & (b["hhmm"] <= "15:59")]
    out = {}
    for (r, s), g in x.groupby(["root", "session"], sort=False):
        out[(r, s)] = {"m": np.array([hm(v) for v in g["hhmm"]]), "o": g["open"].to_numpy(float),
                       "h": g["high"].to_numpy(float), "l": g["low"].to_numpy(float),
                       "c": g["close"].to_numpy(float)}
    return out


def pnl_bp(D: int, entry: float, exit_: float) -> float:
    return D * (exit_ / entry - 1) * 1e4


def simulate(bars: dict[str, np.ndarray], entry_bar: int, D: int, stop_dist: float,
             flips: dict[int, bool] | None = None) -> tuple[float, float, str] | None:
    """(entry, exit, reason). Entry at the close of the bar starting at entry_bar; the stop at stop_dist from the
    entry (a bar opening through it fills at its open); a state-flip exit at a checkpoint close; the time stop at the
    close of the bar starting entry_bar + 60. Intra-bar: the stop first (pessimistic)."""
    m = bars["m"]
    k = np.flatnonzero(m == entry_bar)
    if len(k) == 0 or D == 0 or not np.isfinite(stop_dist) or stop_dist <= 0:
        return None
    i0 = int(k[0])
    entry = bars["c"][i0]
    stop = entry - D * stop_dist
    last = entry_bar + HOLD_MIN
    for i in range(i0 + 1, len(m)):
        if m[i] > last:
            return entry, bars["c"][i - 1], "time_gap"
        o, h, lo, c = bars["o"][i], bars["h"][i], bars["l"][i], bars["c"][i]
        if D > 0 and lo <= stop:
            return entry, (o if o <= stop else stop), "stop"
        if D < 0 and h >= stop:
            return entry, (o if o >= stop else stop), "stop"
        close_clock = m[i] + 1
        if flips and flips.get(close_clock):
            return entry, c, "flip"
        if m[i] == last:
            return entry, c, "time"
    return entry, bars["c"][-1], "session_end"


def b3_trade(bars: dict[str, np.ndarray], t0: str, hi: float, lo: float) -> tuple[float, float, str, int] | None:
    m = bars["m"]
    for i in np.flatnonzero((m >= hm(t0)) & (m <= hm(B3_LAST))):
        c = bars["c"][i]
        if c > hi or c < lo:
            D = 1 if c > hi else -1
            res = simulate(bars, int(m[i]) + 1, D, 0.5 * (hi - lo))
            return None if res is None else (*res, D)
    return None


def policy_side(p: np.ndarray, d0: float, gap: float) -> tuple[int, str]:
    """s.6.2 with REV merged: (direction, state)."""
    j = int(np.argmax(p))
    st = CLASSES[j]
    if p[j] < THETA or st == "RANGE":
        return 0, "NONE"
    if st == "CONT":
        return int(d0), st
    return int(-np.sign(gap)), st  # FADE: towards the prior close


def decision_value(t0: str, P0: pd.DataFrame, later: dict[str, pd.DataFrame], tab: dict[str, pd.DataFrame],
                   bars: dict) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Per (session, market): the policy's and B1-B3's net bp. `later` maps a later checkpoint inside the hold to
    that (t, t0) model's OOS rows."""
    lk = {t: P.set_index(["session", "root"]) for t, P in later.items()}
    rows = []
    for rec in P0.itertuples(index=False):
        d = tab[rec.root].loc[rec.session]
        key = (rec.root, rec.session)
        if key not in bars:
            continue
        rng_ = float(d[f"hi_{t0}"] - d[f"lo_{t0}"])
        gap = float(d["open"] - d["prior_close"])
        p = np.array([rec.p_CONT, rec.p_FADE, rec.p_RANGE])
        D, st = policy_side(p, rec.d0, gap)
        flips = {}
        if D != 0:
            for t, L in lk.items():
                if (rec.session, rec.root) in L.index:
                    q = float(L.loc[(rec.session, rec.root), f"p_{st}"])
                    flips[hm(t)] = q < FLIP
        cost = COST_USD[rec.root] / USD_PER_POINT[rec.root]
        res: dict[str, float] = {}
        for name, side, fl in (("policy", D, flips), ("B1", int(rec.d0), None), ("B2", -int(rec.d0), None)):
            sim = simulate(bars[key], hm(t0), side, 0.5 * rng_, fl) if side != 0 else None
            if sim is None:
                res[name], res[name + "_gross"], res[name + "_traded"] = 0.0, 0.0, 0.0
            else:
                e, x, _ = sim
                g = pnl_bp(side, e, x)
                res[name], res[name + "_gross"], res[name + "_traded"] = g - cost / e * 1e4, g, 1.0
        b3 = b3_trade(bars[key], t0, float(d[f"hi_{t0}"]), float(d[f"lo_{t0}"]))
        if b3 is None:
            res["B3"], res["B3_gross"], res["B3_traded"] = 0.0, 0.0, 0.0
        else:
            e, x, _, s3 = b3
            g = pnl_bp(s3, e, x)
            res["B3"], res["B3_gross"], res["B3_traded"] = g - cost / e * 1e4, g, 1.0
        rows.append({"session": rec.session, "root": rec.root, "state": st, "side": D, **res})
    T = pd.DataFrame(rows)
    per = T.groupby("session")[["policy", "B1", "B2", "B3", "policy_gross"]].mean()
    means = {k: float(per[k].mean()) for k in ("B1", "B2", "B3")}
    best = max(means, key=means.get)
    diff = (per["policy"] - per[best]).to_numpy(float)
    t_hac, se = nw_t(diff)
    out = {"n_sessions": int(len(per)), "n_rows": int(len(T)), "traded_rows": int(T["policy_traded"].sum()),
           "policy_mean_net_bp": float(per["policy"].mean()), "policy_mean_gross_bp": float(per["policy_gross"].mean()),
           "baseline_means_net_bp": means, "best_baseline": best, "diff_mean_bp": float(diff.mean()),
           "diff_se_bp": se, "t_hac": t_hac, "p_two_sided": float(2 * stats.norm.sf(abs(t_hac))),
           "per_traded_row": describe(T.loc[T["policy_traded"] > 0, "policy"].to_numpy(float)),
           "states_traded": T.loc[T["policy_traded"] > 0, "state"].value_counts().to_dict(),
           "reads_2024_plus": bool((per.index >= "2024-01-01").any())}
    return T, out


def nw_t(x: np.ndarray, lag: int = NW_LAG) -> tuple[float, float]:
    x = np.asarray(x, dtype=float)
    n = len(x)
    e = x - x.mean()
    s = float(e @ e) / n
    for k in range(1, lag + 1):
        s += 2 * (1 - k / (lag + 1)) * float(e[k:] @ e[:-k]) / n
    se = math.sqrt(s / n)
    return (float(x.mean() / se) if se > 0 else float("nan")), se


def describe(v: np.ndarray) -> dict[str, Any]:
    v = v[np.isfinite(v)]
    if len(v) < 3:
        return {"n": int(len(v))}
    return {"n": int(len(v)), "mean": float(v.mean()), "median": float(np.median(v)), "win": float((v > 0).mean()),
            "skew": float(stats.skew(v)), "kurtosis": float(stats.kurtosis(v))}


def holm(p: dict[str, float]) -> dict[str, float]:
    keys = sorted(p, key=lambda k: p[k])
    out, run = {}, 0.0
    for i, k in enumerate(keys):
        run = max(run, min(1.0, (len(keys) - i) * p[k]))
        out[k] = run
    return out


# =============================================================================================== audits
def audit_money(side: Callable = policy_side, pnl: Callable = pnl_bp) -> None:
    if not (pnl(1, 100.0, 101.0) > 0 and pnl(-1, 100.0, 99.0) > 0 and pnl(1, 100.0, 99.0) < 0):
        raise OpeningRunError("money: a favourable move did not pay")
    if side(np.array([0.1, 0.8, 0.1]), 1.0, 5.0)[0] != -1 or side(np.array([0.1, 0.8, 0.1]), 1.0, -5.0)[0] != 1:
        raise OpeningRunError("money: FADE must trade towards the prior close (test 14)")
    if side(np.array([0.3, 0.3, 0.4]), 1.0, 5.0)[0] != 0 or side(np.array([0.44, 0.1, 0.46]), 1.0, 5.0)[0] != 0:
        raise OpeningRunError("money: RANGE or max p < theta must not trade (test 14)")
    if side(np.array([0.8, 0.1, 0.1]), -1.0, 5.0)[0] != -1:
        raise OpeningRunError("money: CONT must trade d0")


def audit_flip(sim: Callable = simulate) -> None:
    m = np.arange(hm("10:00"), hm("11:10"))
    bars = {"m": m, "o": np.full(len(m), 100.0), "h": np.full(len(m), 100.1), "l": np.full(len(m), 99.9),
            "c": np.full(len(m), 100.0)}
    res = sim(bars, hm("10:00"), 1, 5.0, {hm("10:30"): True})
    if res is None or res[2] != "flip":
        raise OpeningRunError("the state-flip exit did not fire below 0.30 (test 15)")
    res = sim(bars, hm("10:00"), 1, 5.0, {hm("10:30"): False})
    if res is None or res[2] != "time":
        raise OpeningRunError("with no flip the trade must reach its time stop")


def audit_right_quantity(T: pd.DataFrame, out: dict[str, Any]) -> None:
    tr = T[T["policy_traded"] > 0]
    if len(tr) and np.allclose(tr["policy"], tr["policy_gross"]):
        raise OpeningRunError("right quantity: the policy's net equals its gross")
    per = T.groupby("session")[["policy", out["best_baseline"]]].mean()
    if not math.isclose(out["diff_mean_bp"], float((per["policy"] - per[out["best_baseline"]]).mean()), rel_tol=1e-9,
                        abs_tol=1e-12):
        raise OpeningRunError("right quantity: the difference is not policy minus baseline")


# =============================================================================================== build
DATA_ROOT = REPO / "data"


def load(dry: bool) -> tuple[pd.DataFrame, list[str]]:
    use, _ = G0.usable_sessions(DATA_ROOT)
    b = G0.load_bars()
    if dry:  # the real calendar and bar layout; every price and volume replaced by a synthetic walk
        rng = np.random.default_rng(7)
        b = b.sort_values(["root", "session", "et"], kind="stable").reset_index(drop=True)
        lvl = b["root"].map({"ES": 3000.0, "NQ": 10000.0}).to_numpy()
        walk = pd.Series(rng.normal(0, 4e-4, len(b))).groupby(b["root"].to_numpy()).cumsum().to_numpy()
        c = lvl * np.exp(walk)
        b["close"] = c
        starts = np.r_[True, (b["root"].to_numpy()[1:] != b["root"].to_numpy()[:-1])]
        b["open"] = np.r_[c[0], c[:-1]]
        b.loc[starts, "open"] = c[starts]
        b["high"] = np.maximum(b["open"], b["close"]) * (1 + rng.uniform(0, 2e-4, len(b)))
        b["low"] = np.minimum(b["open"], b["close"]) * (1 - rng.uniform(0, 2e-4, len(b)))
        b["volume"] = rng.integers(100, 5000, len(b))
    return b, use


def build_phase3(dry: bool = False) -> tuple[dict[str, Any], list[dict]]:
    t_start = time.time()
    audit_money()
    audit_flip()
    b, use = load(dry)
    tab = session_table(b, use)
    rng = np.random.default_rng(SEED)
    # the leak check (deposit test 25) on a full year of ES, so every prior-window statistic is defined: the raw
    # window statistics AND the standardised features must not move when one session's bars from t on move
    yr = [s for s in tab["ES"].index if "2018-07-01" <= s <= "2019-06-30"]
    x_yr = b[(b["root"] == "ES") & b["session"].isin(yr)]
    wcols = [f"{k}_{c}" for c in CHECKPOINTS for k in ("px", "hi", "lo", "n", "vol")]
    for t in CHECKPOINTS:
        def fn(xx: pd.DataFrame, t: str = t) -> pd.DataFrame:
            d = session_table(xx, use, ("ES",))["ES"]
            f = features_sa(d, t, np.ones(len(d)))
            return pd.concat([f, d[[c for c in wcols if c.endswith(t)]]], axis=1)
        leak_check(fn, x_yr, t, yr[130:], rng)
    cal = sorted({s for r in ROOTS for s in tab[r].index if tab[r].loc[s, "usable"] and s >= "2016-01-04"})
    doc: dict[str, Any] = {"spec": "D645 (17c2b05); OA-A1..A7; O-D4 kept", "stage": "S-A", "features": list(S_A),
                           "calendar": [cal[0], cal[-1], len(cal)], "windows": len(windows(cal)), "H_O3": {},
                           "H_O2": {}, "dry_run": dry}
    oos: dict[tuple[str, str], pd.DataFrame] = {}
    pairs = sorted({(t, t) for t in CHECKPOINTS} | {("10:00", "09:45"), ("10:30", "09:45"), ("10:30", "10:00"),
                                                     ("11:00", "10:00")})
    for t, t0 in pairs:
        D = dataset(tab, t, t0)
        P = walk_forward(D, list(S_A), cal)
        oos[(t, t0)] = P
        if t == t0:
            rep = classification_report(P, rng if t == H_O1_T0 else None)
            doc["H_O3"][t] = rep
    doc["H_O1"] = doc["H_O3"][H_O1_T0]
    # H-O3's argmax changes between consecutive checkpoints (same session-market)
    ch = {}
    for a, c in zip(CHECKPOINTS[:-1], CHECKPOINTS[1:]):
        A = oos[(a, a)].set_index(["session", "root"])[[f"p_{k}" for k in CLASSES]].idxmax(axis=1)
        B = oos[(c, c)].set_index(["session", "root"])[[f"p_{k}" for k in CLASSES]].idxmax(axis=1)
        j = A.to_frame("a").join(B.to_frame("b"), how="inner")
        ch[f"{a}->{c}"] = {"n": int(len(j)), "changed": float((j["a"] != j["b"]).mean())}
    doc["H_O3_argmax_changes"] = ch
    for P in oos.values():
        audit_oos(P)
    doc["oos_vs_joint_maxdiff"] = {f"{t}|{t0}": P.attrs["oos_vs_joint_maxdiff"] for (t, t0), P in oos.items()}
    bars = bar_arrays(b)
    trials: list[dict] = []
    pv = {}
    for t0 in TRADE_T0:
        later = {t: oos[(t, t0)] for t in CHECKPOINTS if (t, t0) in oos and hm(t) > hm(t0)
                 and hm(t) <= hm(t0) + 1 + HOLD_MIN}
        T, out = decision_value(t0, oos[(t0, t0)], later, tab, bars)
        audit_right_quantity(T, out)
        doc["H_O2"][t0] = out
        pv[t0] = out["p_two_sided"]
        trials.append({"trial_id": f"S-A_H-O2_{t0}", "doc": "OPENING_AGENT_STATE_PREREG.md", "family": "opening H-O2",
                       "stage": "S-A", "t0": t0, "construction": f"state policy vs best baseline ({out['best_baseline']})",
                       "n_obs": out["n_sessions"], "mean_net": round(out["diff_mean_bp"], 6),
                       "t_hac": round(out["t_hac"], 6), "notes": f"reads_2024_plus={out['reads_2024_plus']}"})
    adj = holm(pv)
    for t0 in TRADE_T0:
        o = doc["H_O2"][t0]
        o["p_holm"] = adj[t0]
        o["within_doc_pass"] = bool(adj[t0] < 0.05 and o["t_hac"] > 0 and o["policy_mean_net_bp"] > 0)
        o["programme_bar_0005"] = bool(adj[t0] <= 0.005 and o["t_hac"] > 0)
        o["power"] = "testable at t = 2; underpowered at the programme's alpha and per traded day (POWER b6f8f29)"
    h1 = doc["H_O1"]
    trials.append({"trial_id": "S-A_H-O1_10:00", "doc": "OPENING_AGENT_STATE_PREREG.md", "family": "opening H-O2",
                   "stage": "S-A", "t0": H_O1_T0, "construction": "H-O1 classification lift",
                   "n_obs": h1["n"], "notes": f"accuracy={h1['accuracy']:.6f}; base={h1['base_accuracy']:.6f}; "
                                              f"logloss={h1['logloss']:.6f}; base_logloss={h1['base_logloss']:.6f}; "
                                              f"perm_p={h1.get('perm', {}).get('p')}"})
    doc["reads"] = {"spec_sha256": hashlib.sha256(SPEC.read_bytes()).hexdigest(), "reserved_from": RESERVED_FROM,
                    "last_session_read": str(b["session"].max())}
    doc["runtime_min"] = round((time.time() - t_start) / 60, 1)
    for tr in trials:
        tr["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return doc, trials


def dump(doc: dict[str, Any]) -> str:
    def dflt(o: Any) -> Any:
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.bool_):
            return bool(o)
        raise TypeError(type(o))
    return json.dumps(doc, indent=1, sort_keys=True, default=dflt) + "\n"


# =============================================================================================== selftest
def selftest() -> int:
    fired = []

    def must_raise(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except OpeningRunError:
            fired.append(name)
            return
        raise AssertionError(f"the {name} audit did not fire")

    audit_money()
    must_raise("money-fade", lambda: audit_money(side=lambda p, d0, gap: (int(np.sign(gap)), "FADE")))
    must_raise("money-pnl", lambda: audit_money(pnl=lambda D, e, x: -D * (x / e - 1)))
    audit_flip()
    must_raise("flip", lambda: audit_flip(lambda *a, **k: (100.0, 100.0, "time")))
    must_raise("budget", lambda: check_budget([f"f{i}" for i in range(12)]))
    must_raise("label-in-features", lambda: check_budget(["gap_atr", "label"]))
    must_raise("walk-forward-overlap", lambda: windows_broken())
    fake = pd.DataFrame({"x": [1]})
    fake.attrs["oos_vs_joint_maxdiff"] = 0.0
    must_raise("oos-equals-joint-fit", lambda: audit_oos(fake))
    # the leak canary on a synthetic session table
    rng = np.random.default_rng(1)
    sess = [f"2019-01-{d:02d}" for d in range(2, 32)]
    rows = []
    for s in sess:
        for m in range(hm("09:30"), hm("16:00")):
            c = 100 + rng.normal()
            rows.append((s, hhmm(m), c, c + 0.5, c - 0.5, c, 100))
    x = pd.DataFrame(rows, columns=["session", "hhmm", "open", "high", "low", "close", "volume"])

    def clean(xx: pd.DataFrame, t: str) -> pd.DataFrame:
        w = window(xx, t)
        return w.groupby("session")["close"].last().to_frame("px")

    def canary(xx: pd.DataFrame, t: str) -> pd.DataFrame:  # reads the bar STARTING at t: one minute too late
        return xx[xx["hhmm"] <= t].groupby("session")["close"].last().to_frame("px")

    leak_check(clean, x, "10:00", sess, rng)
    must_raise("leak-canary", lambda: leak_check(canary, x, "10:00", sess, rng))
    # the right-quantity audit fires on a policy whose net equals its gross, and on a reversed difference
    T = pd.DataFrame({"session": ["a", "b"], "policy": [1.0, 2.0], "policy_gross": [1.0, 2.0], "policy_traded": [1, 1],
                      "B1": [0.5, 0.5]})
    must_raise("net-equals-gross", lambda: audit_right_quantity(T, {"best_baseline": "B1", "diff_mean_bp": 1.0}))
    T2 = T.assign(policy_gross=[1.5, 2.5])
    audit_right_quantity(T2, {"best_baseline": "B1", "diff_mean_bp": 1.0})
    must_raise("reversed-difference", lambda: audit_right_quantity(T2, {"best_baseline": "B1", "diff_mean_bp": -1.0}))
    # NW t on a known series; Holm
    t_, se_ = nw_t(np.array([1.0, -1.0] * 50 + [0.0]))
    assert abs(t_) < 1e-9
    assert holm({"a": 0.01, "b": 0.04}) == {"a": 0.02, "b": 0.04}
    # the simulator: a long stopped out at the stop; a bar opening through it fills at its open
    m = np.arange(hm("10:00"), hm("10:05"))
    bars = {"m": m, "o": np.array([100, 100, 94, 100, 100.0]), "h": np.full(5, 100.5), "l": np.array([99.5, 99.5, 93, 99, 99]),
            "c": np.array([100, 100, 94, 100, 100.0])}
    e, xit, why = simulate(bars, hm("10:00"), 1, 5.0)
    assert why == "stop" and xit == 94.0, (why, xit)
    print(f"selftest: {len(fired)} audits fire on broken inputs ({', '.join(fired)}); the simulator and statistics check out")
    return 0


def windows_broken() -> None:
    s = [f"d{i:04d}" for i in range(400)]
    tr, te = s[:252], s[251:314]
    if set(tr) & set(te):
        raise OpeningRunError("walk-forward: a training session is also a test session")


def phase45(a: argparse.Namespace) -> int:
    """Phases 4-5 (scripts/opening_phase45.py), under D645 and OA-A8."""
    s = importlib.util.spec_from_file_location("opening_phase45", REPO / "scripts" / "opening_phase45.py")
    assert s is not None and s.loader is not None
    P45 = importlib.util.module_from_spec(s)
    sys.modules["opening_phase45"] = P45
    s.loader.exec_module(P45)
    P45.R = sys.modules[__name__]
    out = OD / "phase45.json"
    if a.dry_run:
        doc, trials = P45.build(dry=True)
        dump(doc)
        print(f"DRY RUN phase 4-5 (synthetic bars and agents): every path ran; {len(trials)} trials; retained "
              f"{doc['retained']}; final {doc['final_stage']}; gate O1 {doc['gate_O1']}; {doc['runtime_min']} min; "
              "nothing written")
        return 0
    if a.run:
        if out.exists():
            raise SystemExit("phases 4-5 run once (D645): phase45.json exists")
        doc, trials = P45.build()
        out.write_text(dump(doc), encoding="utf-8", newline="\n")
        log = TrialsCsv(OD / "trials.csv")
        for t in trials:
            log.append(t)
        print(f"wrote {out.name} and {len(trials)} trials in {doc['runtime_min']} min; final {doc['final_stage']}; "
              f"gate O1 {doc['gate_O1']}; v2 trigger {doc['v2_trigger']['fires']}")
        return 0
    doc, _ = P45.build()
    old = json.loads(out.read_text(encoding="utf-8"))
    doc["runtime_min"] = old["runtime_min"]
    if dump(doc) != out.read_text(encoding="utf-8"):
        raise SystemExit("CHECK FAILED: the phase 4-5 rebuild differs from the committed output")
    print("CHECK: the phase 4-5 rebuild equals the committed output")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--run", action="store_true")
    g.add_argument("--check", action="store_true")
    ap.add_argument("--phase", default="3")
    ap.add_argument("--data-root", type=Path, default=REPO / "data",
                    help="where the gitignored inputs (SPY's daily file, D589) live; a worktree passes the main checkout's")
    a = ap.parse_args()
    global DATA_ROOT
    DATA_ROOT = a.data_root
    if a.selftest:
        return selftest()
    if a.phase == "4-5":
        return phase45(a)
    if a.phase != "3":
        raise SystemExit("--phase is 3 or 4-5")
    out = OD / "phase3_S-A.json"
    trials_path = OD / "trials.csv"
    if a.dry_run:
        doc, trials = build_phase3(dry=True)
        dump(doc)
        print(f"DRY RUN (synthetic bars): every path ran; {len(trials)} trials; H-O1 pass={doc['H_O1'].get('pass')}; "
              f"H-O2 t={ {k: round(v['t_hac'], 2) for k, v in doc['H_O2'].items()} }; {doc['runtime_min']} min; "
              "nothing written")
        return 0
    if a.run:
        if out.exists() or trials_path.exists():
            raise SystemExit("phase 3 runs once (D645): its output or trials already exist")
        doc, trials = build_phase3()
        out.write_text(dump(doc), encoding="utf-8", newline="\n")
        log = TrialsCsv(trials_path)
        for t in trials:
            log.append(t)
        print(f"wrote {out.name} and {trials_path.name} ({len(trials)} trials) in {doc['runtime_min']} min")
        return 0
    doc, _ = build_phase3()
    old = json.loads(out.read_text(encoding="utf-8"))
    doc["runtime_min"] = old["runtime_min"]
    if dump(doc) != out.read_text(encoding="utf-8"):
        raise SystemExit("CHECK FAILED: the rebuild differs from the committed output")
    print("CHECK: the rebuild equals the committed output")
    return 0


if __name__ == "__main__":
    sys.exit(main())
