"""D645 Phases 4-5 of the opening agent-state model: the agent stages under the retention rule, then H-O1 .. H-O6 and
Gate O1 on the final retained stage, with OA-A8's diagnostics at every stage. Called by
`run_opening_stages.py --run --phase 4-5` (and `--dry-run --phase 4-5`, `--check --phase 4-5`); written after OA-A8
(c1113bf) and committed BEFORE the run.

THE STAGES (s.8, D645 s.2), each a feature added to the last retained set, direction-relative (x d0):
  S-B a7_t (large-lot signed share 09:30 -> t; only if A7 passed its exchange-flag check, data/opening/a7_flag_check.json)
  S-C z1 · S-D z2 · S-E z3 · S-F z5 · S-G z6
  S-H z4 (only if O0-H passes for BOTH markets; added only if the feature count stays <= 11, else it waits for S-I)
  S-I observables + a7 (if admitted) + N + D over the retained agent pressures (plus z4 if S-H waited on the budget)
RETENTION at t0 = 10:00 (D645 s.5): OOS log loss falls >= 2% relative AND the H-O2 HAC t does not fall. S-I is kept
if its log loss is within 1% of the best agent stage evaluated, or better.

Readings fixed here, before the run (D645 leaves them to the code):
- A missing agent value (a warm-up, a CME-only session) is set to 0, the z-score's "no pressure", so every stage
  scores the SAME rows and the log losses compare like with like.
- N and D (s.4) are the mean and the standard deviation (ddof 0) of the active z_i x d0 per row; D = 0 with one agent.
- H-O4: the curve at k is D x (P[t0+k] / P[t0] - 1) x 1e4, where P[t0+k] is the close at clock t0+k. It is computed per
  traded state. A state whose mean 60-minute move is <= 0 has nothing to time: it is reported "not applicable" and is
  not a kill.
- H-O5 (agent shuffle): for each retained agent stage, its new column is reassigned across sessions within market x
  year (seed 645) and the stage refitted at 10:00. It "loses its improvement" if the shuffled log loss is no longer
  >= 2% below the previous retained stage's.
- H-O6: OLS on stacked ES/NQ rows (sorted by session) of the raw return r(09:31 -> 10:30) on z1..z6 jointly (NaN -> 0),
  HAC lag 5, with VIFs; z1 alone on r(10:30 -> 11:30); a7 at 10:30 on z2 (if A7 was admitted). All usable in-sample
  sessions, not only the OOS ones (it is validation, not prediction).
- OA-A8's AUC intervals resample sessions (day blocks) 2,000 times, seed 645.
"""
from __future__ import annotations

import json
import math
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.metrics import roc_auc_score
from statsmodels.stats.outliers_influence import variance_inflation_factor

from backtest_framework.opening.labels import atr_prior

R: Any = None  # the runner module (run_opening_stages), injected by it
AGENT_STAGES = (("S-B", "a7"), ("S-C", "z1"), ("S-D", "z2"), ("S-E", "z3"), ("S-F", "z5"), ("S-G", "z6"),
                ("S-H", "z4"))
PRESSURES = ("z1", "z2", "z3", "z4", "z5", "z6")
Z5_CAP = 5.0  # OA-A9: z5 clipped to [-5, +5] before it is multiplied by d0
RETAIN_LL = 0.02
S_I_TOL = 0.01
N_BOOT_AUC = 2000
N_BOOT_CURVE = 9999
V2_AUC = 0.55


# =============================================================================================== inputs
def load_agents(od) -> dict[str, pd.DataFrame]:
    a = pd.read_csv(od / "agents.csv", encoding="utf-8", dtype={"session": str})
    a7 = pd.read_csv(od / "a7.csv", encoding="utf-8", dtype={"session": str}) if (od / "a7.csv").exists() else None
    out = {}
    for r in R.ROOTS:
        x = a[a["root"] == r].set_index("session")[list(PRESSURES)].copy()
        x["z5"] = x["z5"].clip(-Z5_CAP, Z5_CAP)  # OA-A9 (NaN stays NaN)
        if (x["z5"].abs() > Z5_CAP).any():
            raise RuntimeError("OA-A9: z5 beyond its cap after the clip")
        if a7 is not None:
            y = a7[a7["root"] == r].set_index("session")[[f"a7_{t}" for t in R.CHECKPOINTS]]
            x = x.join(y, how="left")
        out[r] = x
    return out


def dataset_x(tab: dict, t: str, t0: str, ag: dict, cols: list[str], active: list[str]) -> pd.DataFrame:
    """D645 s.2's rows with the S-A features plus the stage's agent columns (x d0; NaN -> 0), and N, D if asked."""
    D = R.dataset(tab, t, t0)
    long = pd.concat({r: ag[r] for r in R.ROOTS}, names=["root", "session"])
    vals = long.reindex(pd.MultiIndex.from_arrays([D["root"], D["session"]]))
    d0 = D["d0"].to_numpy(float)

    def rel(src: str) -> np.ndarray:
        return np.nan_to_num(vals[src].to_numpy(float) * d0, nan=0.0)

    for c in cols:
        if c in R.S_A or c in ("N", "D"):
            continue
        D[c] = rel(f"a7_{t}" if c == "a7" else c)
    if "N" in cols or "D" in cols:
        Z = np.column_stack([rel(z) for z in active])
        D["N"] = Z.mean(axis=1)
        D["D"] = Z.std(axis=1)
    return D


# =============================================================================================== one stage
def run_stage(name: str, cols: list[str], active: list[str], ctx: dict) -> dict[str, Any]:
    tab, ag, cal, bars = ctx["tab"], ctx["ag"], ctx["cal"], ctx["bars"]
    oos = {}
    for t, t0 in R.PAIRS45:
        D = dataset_x(tab, t, t0, ag, cols, active)
        oos[(t, t0)] = R.walk_forward(D, cols, cal)
        R.audit_oos(oos[(t, t0)])
    res: dict[str, Any] = {"stage": name, "features": cols, "active_agents": active, "H_O2": {}}
    rep = R.classification_report(oos[(R.H_O1_T0, R.H_O1_T0)], None)
    res["logloss_10"] = rep["logloss"]
    res["accuracy_10"] = rep["accuracy"]
    res["base_logloss_10"] = rep["base_logloss"]
    Ts = {}
    for t0 in R.TRADE_T0:
        later = {t: oos[(t, t0)] for t in R.CHECKPOINTS if (t, t0) in oos and R.hm(t) > R.hm(t0)
                 and R.hm(t) <= R.hm(t0) + 1 + R.HOLD_MIN}
        T, out = R.decision_value(t0, oos[(t0, t0)], later, tab, bars)
        R.audit_right_quantity(T, out)
        res["H_O2"][t0] = out
        Ts[t0] = T
    res["_oos"], res["_T"] = oos, Ts
    res["diag"] = {t0: diagnostics(oos[(t0, t0)], Ts[t0], ctx["trades"][t0], ctx["rng_seed"]) for t0 in R.TRADE_T0}
    return res


# =============================================================================================== OA-A8 diagnostics
def trade_table(t0: str, tab: dict, bars: dict) -> pd.DataFrame:
    """Per (session, market) at t0: the CONT (d0) and FADE (-sign gap) 60-minute trades, gross and net."""
    rows = []
    for r in R.ROOTS:
        d = tab[r]
        d0, lab = R.labels_at(d, t0)
        for s, dd, lb in zip(d.index, d0, lab):
            if not (np.isfinite(dd) and dd != 0 and lb is not None) or (r, s) not in bars:
                continue
            x = d.loc[s]
            rng_ = float(x[f"hi_{t0}"] - x[f"lo_{t0}"])
            gap = float(x["open"] - x["prior_close"])
            cost = R.COST_USD[r] / R.USD_PER_POINT[r]
            row = {"root": r, "session": s, "label": lb}
            for nm, side in (("cont", int(dd)), ("fade", int(-np.sign(gap)))):
                sim = R.simulate(bars[(r, s)], R.hm(t0), side, 0.5 * rng_) if side != 0 else None
                if sim is None:
                    row[nm + "_gross"] = row[nm + "_net"] = np.nan
                    row[nm + "_stop"] = np.nan
                else:
                    e, xx, why = sim
                    g = R.pnl_bp(side, e, xx)
                    row[nm + "_gross"], row[nm + "_net"], row[nm + "_stop"] = g, g - cost / e * 1e4, float(why == "stop")
            rows.append(row)
    return pd.DataFrame(rows).set_index(["session", "root"])


def oracle(trades: pd.DataFrame, oos_index: pd.Index) -> dict[str, Any]:
    t = trades.loc[trades.index.intersection(oos_index)]
    out = {}
    for lab, nm in (("CONT", "cont"), ("FADE", "fade")):
        v = t.loc[t["label"] == lab, nm + "_net"].to_numpy(float)
        v = v[np.isfinite(v)]
        se = v.std(ddof=1) / math.sqrt(len(v)) if len(v) > 2 else float("nan")
        out[lab] = {"n": int(len(v)), "net_mean": float(v.mean()), "t": float(v.mean() / se), "median": float(np.median(v)),
                    "win": float((v > 0).mean()),
                    "stop_share": float(np.nanmean(t.loc[t["label"] == lab, nm + "_stop"]))}
    return out


def diagnostics(P: pd.DataFrame, T: pd.DataFrame, trades: pd.DataFrame, seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    idx = pd.MultiIndex.from_arrays([P["session"], P["root"]])
    orc = oracle(trades, idx)
    y = P["label"].to_numpy()
    pr = P[[f"p_{c}" for c in R.CLASSES]].to_numpy(float)
    sess = P["session"].to_numpy()
    u, inv = np.unique(sess, return_inverse=True)
    groups = [np.flatnonzero(inv == k) for k in range(len(u))]
    auc = {}
    for j, c in enumerate(R.CLASSES):
        yy = (y == c).astype(int)
        point = float(roc_auc_score(yy, pr[:, j]))
        bs = []
        for _ in range(N_BOOT_AUC):
            pick = rng.integers(0, len(u), len(u))
            ix = np.concatenate([groups[k] for k in pick])
            if yy[ix].min() == yy[ix].max():
                continue
            bs.append(roc_auc_score(yy[ix], pr[ix, j]))
        auc[c] = {"auc": point, "ci95": [float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975))]}
    tj = trades.reindex(idx)
    dec = {}
    for c, nm in (("CONT", "cont"), ("FADE", "fade")):
        p = P[f"p_{c}"].to_numpy(float)
        q = pd.qcut(pd.Series(p).rank(method="first"), 10, labels=False).to_numpy()
        g = pd.DataFrame({"q": q, "p": p, "gross": tj[nm + "_gross"].to_numpy(float), "net": tj[nm + "_net"].to_numpy(float)})
        gg = g.groupby("q").agg(p=("p", "mean"), gross=("gross", "mean"), net=("net", "mean"), n=("p", "size"))
        dec[c] = {"deciles": gg.round(4).reset_index().to_dict("records"),
                  "spearman_p_gross": float(gg["p"].corr(gg["gross"], method="spearman"))}
    cap = {}
    tr = T[T["policy_traded"] > 0]
    for st in ("CONT", "FADE"):
        v = tr.loc[tr["state"] == st, "policy"].to_numpy(float)
        cap[st] = {"policy_traded": int(len(v)), "policy_net_per_trade": float(v.mean()) if len(v) else None,
                   "ceiling_net_per_trade": orc[st]["net_mean"],
                   "capture": float(v.mean() / orc[st]["net_mean"]) if len(v) and orc[st]["net_mean"] else None}
    return {"oracle": orc, "auc": auc, "deciles": dec, "capture": cap}


# =============================================================================================== final-stage tests
def timing(t0: str, T: pd.DataFrame, tab: dict, bars: dict, seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    out = {}
    tr = T[T["policy_traded"] > 0]
    for st in ("CONT", "FADE"):
        s = tr[tr["state"] == st]
        curves, days = [], []
        for rec in s.itertuples(index=False):
            b = bars[(rec.root, rec.session)]
            m, c = b["m"], b["c"]
            k0 = np.flatnonzero(m == R.hm(t0) - 1)
            if len(k0) == 0:
                continue
            base = c[k0[0]]
            cv = []
            for k in range(0, 61):
                j = np.flatnonzero(m == R.hm(t0) - 1 + k)
                cv.append(rec.side * (c[j[0]] / base - 1) * 1e4 if len(j) else np.nan)
            curves.append(cv)
            days.append(rec.session)
        if len(curves) < 3:
            out[st] = {"n": len(curves), "verdict": "too few trades"}
            continue
        C = pd.DataFrame(curves).ffill(axis=1).to_numpy(float)
        mean = np.nanmean(C, axis=0)
        u, inv = np.unique(days, return_inverse=True)
        bs = []
        for _ in range(N_BOOT_CURVE):
            pick = rng.integers(0, len(u), len(u))
            ix = np.concatenate([np.flatnonzero(inv == k) for k in pick])
            bs.append(np.nanmean(C[ix], axis=0))
        bs = np.array(bs)
        c5, c60 = float(mean[5]), float(mean[60])
        verdict = ("not applicable: no positive 60-minute move" if c60 <= 0 else
                   ("PASS" if c5 <= 0.5 * c60 else "FAIL"))
        out[st] = {"n": len(curves), "mean_bp": mean.round(4).tolist(), "ci95_lo": np.quantile(bs, 0.025, axis=0).round(4).tolist(),
                   "ci95_hi": np.quantile(bs, 0.975, axis=0).round(4).tolist(), "c5": c5, "c60": c60,
                   "delay_cost_bp": c5, "verdict": verdict}
    return out


def agent_shuffle(retained: list[dict], ctx: dict) -> dict[str, Any]:
    out = {}
    tab, ag, cal = ctx["tab"], ctx["ag"], ctx["cal"]
    rng = np.random.default_rng(R.SEED)
    for k in range(1, len(retained)):
        st = retained[k]
        new = [c for c in st["features"] if c not in retained[k - 1]["features"]]
        if not new or new[0] in ("N", "D"):
            continue
        c = new[0]
        D = dataset_x(tab, R.H_O1_T0, R.H_O1_T0, ag, st["features"], st["active_agents"])
        grp = (D["root"] + "_" + D["session"].str[:4]).to_numpy()
        v = D[c].to_numpy(float).copy()
        for g in np.unique(grp):
            ix = np.flatnonzero(grp == g)
            v[ix] = v[rng.permutation(ix)]
        P = R.walk_forward(D.assign(**{c: v}), st["features"], cal)
        ll = R.logloss(P[[f"p_{x}" for x in R.CLASSES]].to_numpy(float), P["label"].to_numpy())
        prev = retained[k - 1]["logloss_10"]
        out[st["stage"]] = {"agent": c, "logloss_real": st["logloss_10"], "logloss_shuffled": ll, "logloss_prev": prev,
                            "loses_improvement": bool(ll > prev * (1 - RETAIN_LL))}
    return out


def midday_placebo(b: pd.DataFrame, use: list[str], cal: list[str]) -> dict[str, Any]:
    rows = []
    for r in R.ROOTS:
        x = b[(b["root"] == r) & (b["hhmm"] >= "09:30") & (b["hhmm"] <= "15:59")]
        g = x.groupby("session")
        d = pd.DataFrame({"rth_high": g["high"].max(), "rth_low": g["low"].min(), "close": g["close"].last()})
        d["prior_close"], d["prior_high"], d["prior_low"] = d["close"].shift(1), d["rth_high"].shift(1), d["rth_low"].shift(1)
        d["atr20"] = atr_prior(d["rth_high"].to_numpy(), d["rth_low"].to_numpy(), d["close"].to_numpy())
        p12 = x[x["hhmm"] == "11:59"].set_index("session")["close"]
        p1230 = x[x["hhmm"] == "12:29"].set_index("session")["close"]
        aft = x[x["hhmm"] >= "12:00"].groupby("session")
        ib = x[(x["hhmm"] >= "12:00") & (x["hhmm"] <= "12:59")].groupby("session")
        w = x[(x["hhmm"] >= "12:00") & (x["hhmm"] <= "12:29")].groupby("session")
        d["open"], d["px"] = p12.reindex(d.index), p1230.reindex(d.index)
        d["high"], d["low"] = aft["high"].max().reindex(d.index), aft["low"].min().reindex(d.index)
        d["ib_high"], d["ib_low"] = ib["high"].max().reindex(d.index), ib["low"].min().reindex(d.index)
        d["vol"] = w["volume"].sum().reindex(d.index)
        d0 = np.sign(d["px"] - d["open"]).to_numpy(float)
        lab = R.classify(d0, d["open"], d["close"], d["high"], d["low"], d["ib_high"], d["ib_low"], d["prior_close"], d["atr20"])
        lab = np.where(lab == "REV", "RANGE", lab).astype(object)
        rr = (d["px"] / d["open"] - 1).to_numpy(float)
        lv = np.log(d["vol"].to_numpy(float))
        mu = pd.Series(lv).shift(1).rolling(R.AG.STD_WINDOW, min_periods=R.AG.STD_MIN).mean().to_numpy()
        o = d["open"].to_numpy(float)
        f = pd.DataFrame({"gap_atr": (o - d["prior_close"].to_numpy(float)) * d0 / d["atr20"].to_numpy(float),
                          "loc_with": np.where(d0 > 0, o > d["prior_high"], o < d["prior_low"]).astype(float),
                          "loc_against": np.where(d0 > 0, o < d["prior_low"], o > d["prior_high"]).astype(float),
                          "r_sigma": rr * d0 / R.AG.prior_std(rr), "vol_z": (lv - mu) / R.AG.prior_std(lv)}, index=d.index)
        f["root"], f["session"], f["d0"], f["label"], f["nq"] = r, d.index, d0, lab, float(r == "NQ")
        rows.append(f)
    D = pd.concat(rows, ignore_index=True)
    D = D[D["session"].isin(set(use)) & np.isfinite(D["d0"]) & (D["d0"] != 0) & D["label"].notna()]
    D = D[np.isfinite(D[list(R.S_A)].to_numpy(float)).all(axis=1)].sort_values(["session", "root"], kind="stable")
    D = D[D["session"] >= "2016-01-04"].reset_index(drop=True)
    P = R.walk_forward(D, list(R.S_A), cal)
    rep = R.classification_report(P, None)
    return {k: rep[k] for k in ("n", "accuracy", "base_accuracy", "logloss", "base_logloss", "pred_share")}


def h_o6(b: pd.DataFrame, tab: dict, ag: dict, a7_ok: bool) -> dict[str, Any]:
    recs = []
    for r in R.ROOTS:
        x = b[(b["root"] == r) & b["hhmm"].isin(["09:30", "10:29", "11:29"])]
        p = x.pivot_table(index="session", columns="hhmm", values="close", aggfunc="first")
        d = tab[r]
        z = ag[r].reindex(d.index)
        f = pd.DataFrame({"root": r, "session": d.index, "usable": d["usable"].to_numpy()}, index=d.index)
        f["r_0931_1030"] = (p["10:29"] / p["09:30"] - 1).reindex(d.index) * 1e4
        f["r_1030_1130"] = (p["11:29"] / p["10:29"] - 1).reindex(d.index) * 1e4
        for c in PRESSURES:
            f[c] = z[c].to_numpy(float)
        if "a7_10:30" in z.columns:
            f["a7_1030"] = z["a7_10:30"].to_numpy(float)
        recs.append(f)
    X = pd.concat(recs, ignore_index=True)
    X = X[X["usable"] & (X["session"] >= "2016-01-04")].sort_values(["session", "root"], kind="stable")
    X = X[np.isfinite(X["r_0931_1030"]) & np.isfinite(X["r_1030_1130"])]
    Z = X[list(PRESSURES)].fillna(0.0)
    fit = sm.OLS(X["r_0931_1030"].to_numpy(float), sm.add_constant(Z.to_numpy(float))).fit(
        cov_type="HAC", cov_kwds={"maxlags": R.NW_LAG})
    tvals = dict(zip(PRESSURES, fit.tvalues[1:]))
    coefs = dict(zip(PRESSURES, fit.params[1:]))
    pvals = {k: float(stats.norm.sf(v)) for k, v in tvals.items()}  # one-sided: predicted positive
    adj = R.holm(pvals)
    vif = {c: float(variance_inflation_factor(sm.add_constant(Z.to_numpy(float)), i + 1)) for i, c in enumerate(PRESSURES)}
    f1 = sm.OLS(X["r_1030_1130"].to_numpy(float), sm.add_constant(X[["z1"]].fillna(0.0).to_numpy(float))).fit(
        cov_type="HAC", cov_kwds={"maxlags": R.NW_LAG})
    out = {"n": int(len(X)), "joint": {c: {"coef_bp_per_z": float(coefs[c]), "t": float(tvals[c]), "p_one_sided": pvals[c],
                                           "p_holm": adj[c], "vif": vif[c], "predicted_sign_ok": bool(coefs[c] > 0)}
                                       for c in PRESSURES},
           "z1_second_half": {"coef": float(f1.params[1]), "t": float(f1.tvalues[1]), "predicted": "negative"}}
    if a7_ok and "a7_1030" in X.columns:
        y = X["a7_1030"].to_numpy(float)
        ok = np.isfinite(y)
        f2 = sm.OLS(y[ok], sm.add_constant(X.loc[ok, ["z2"]].fillna(0.0).to_numpy(float))).fit(
            cov_type="HAC", cov_kwds={"maxlags": R.NW_LAG})
        out["a7_on_z2"] = {"coef": float(f2.params[1]), "t": float(f2.tvalues[1]), "predicted": "positive"}
    return out


# =============================================================================================== the phase
def build(dry: bool = False) -> tuple[dict[str, Any], list[dict]]:
    import time
    t_start = time.time()
    od = R.OD
    chk = od / "a7_flag_check.json"
    if not dry and not chk.exists():
        raise SystemExit("A7 is not resolved: data/opening/a7_flag_check.json is missing (D645 s.2)")
    a7_ok = bool(json.loads(chk.read_text(encoding="utf-8"))["pass"]) if chk.exists() else True
    o0h = o0h_status(od)
    b, use = R.load(dry)
    tab = R.session_table(b, use)
    cal = sorted({s for r in R.ROOTS for s in tab[r].index if tab[r].loc[s, "usable"] and s >= "2016-01-04"})
    ag = load_agents(od)
    if dry:  # synthetic agents (and A7) on the real sessions
        rng = np.random.default_rng(3)
        cols = list(PRESSURES) + [f"a7_{t}" for t in R.CHECKPOINTS]
        for r in R.ROOTS:
            ag[r] = pd.DataFrame(rng.normal(size=(len(ag[r]), len(cols))), index=ag[r].index, columns=cols)
    bars = R.bar_arrays(b)
    ctx = {"tab": tab, "ag": ag, "cal": cal, "bars": bars, "rng_seed": R.SEED,
           "trades": {t0: trade_table(t0, tab, bars) for t0 in R.TRADE_T0}}
    doc: dict[str, Any] = {"spec": "D645 (17c2b05), OA-A8 (c1113bf)", "a7_admitted": a7_ok, "o0h": o0h,
                           "stages": [], "dry_run": dry}
    trials: list[dict] = []
    cur = run_stage("S-A", list(R.S_A), [], ctx)
    retained = [cur]
    evaluated = [cur]
    z4_waiting = False
    for name, c in AGENT_STAGES:
        if name == "S-B" and not a7_ok:
            doc["stages"].append({"stage": name, "skipped": "A7 failed its exchange-flag check"})
            continue
        if name == "S-H":
            if not o0h["both_pass"]:
                doc["stages"].append({"stage": name, "skipped": f"O0-H: {o0h}"})
                continue
            if len(cur["features"]) + 1 > R.MAX_FEATURES:
                z4_waiting = True
                doc["stages"].append({"stage": name, "skipped": "the budget: z4 waits for S-I (s.8)"})
                continue
        cols = cur["features"] + [c]
        st = run_stage(name, cols, [x for x in cols if x in PRESSURES], ctx)
        evaluated.append(st)
        ll_ok = st["logloss_10"] <= cur["logloss_10"] * (1 - RETAIN_LL)
        t_ok = st["H_O2"]["10:00"]["t_hac"] >= cur["H_O2"]["10:00"]["t_hac"]
        st["retention"] = {"logloss_drop_rel": 1 - st["logloss_10"] / cur["logloss_10"], "logloss_ok": bool(ll_ok),
                           "t_now": st["H_O2"]["10:00"]["t_hac"], "t_prev": cur["H_O2"]["10:00"]["t_hac"],
                           "t_ok": bool(t_ok), "kept": bool(ll_ok and t_ok)}
        if ll_ok and t_ok:
            cur = st
            retained.append(st)
    # S-I
    active = [x for x in cur["features"] if x in PRESSURES] + (["z4"] if z4_waiting else [])
    final = cur
    if active:
        cols_i = list(R.S_A) + (["a7"] if "a7" in cur["features"] else []) + ["N", "D"]
        si = run_stage("S-I", cols_i, active, ctx)
        best = min(e["logloss_10"] for e in evaluated if e["stage"] != "S-A") if len(evaluated) > 1 else cur["logloss_10"]
        si["retention"] = {"best_agent_stage_logloss": best, "kept": bool(si["logloss_10"] <= best * (1 + S_I_TOL))}
        evaluated.append(si)
        if si["retention"]["kept"]:
            final = si
    for st in evaluated:
        doc["stages"].append(strip(st))
        for t0 in R.TRADE_T0:
            o = st["H_O2"][t0]
            trials.append({"trial_id": f"{st['stage']}_H-O2_{t0}", "doc": "OPENING_AGENT_STATE_PREREG.md",
                           "family": "opening H-O2", "stage": st["stage"], "t0": t0,
                           "construction": f"state policy vs best baseline ({o['best_baseline']}); features {'+'.join(st['features'])}",
                           "n_obs": o["n_sessions"], "mean_net": round(o["diff_mean_bp"], 6), "t_hac": round(o["t_hac"], 6),
                           "notes": f"policy_net={o['policy_mean_net_bp']:.6f}; reads_2024_plus={o['reads_2024_plus']}"})
    doc["retained"] = [s["stage"] for s in retained]
    doc["final_stage"] = final["stage"]
    # the final stage's tests
    P10 = final["_oos"][(R.H_O1_T0, R.H_O1_T0)]
    h1 = R.classification_report(P10, np.random.default_rng(R.SEED))
    h2 = final["H_O2"]
    adj = R.holm({t0: h2[t0]["p_two_sided"] for t0 in R.TRADE_T0})
    for t0 in R.TRADE_T0:
        h2[t0]["p_holm"] = adj[t0]
        h2[t0]["within_doc_pass"] = bool(adj[t0] < 0.05 and h2[t0]["t_hac"] > 0 and h2[t0]["policy_mean_net_bp"] > 0)
        h2[t0]["programme_bar_0005"] = bool(adj[t0] <= 0.005 and h2[t0]["t_hac"] > 0)
    h2_pass = any(h2[t0]["within_doc_pass"] for t0 in R.TRADE_T0)
    doc["final"] = {
        "H_O1": {k: v for k, v in h1.items() if k != "confusion"} | {"confusion_pred_by_label": h1["confusion"]},
        "H_O2": {t0: {k: v for k, v in h2[t0].items()} for t0 in R.TRADE_T0},
        "H_O3": {t: {k: v for k, v in R.classification_report(final["_oos"][(t, t)], None).items() if k != "confusion"}
                 for t in R.CHECKPOINTS},
        "H_O4": {t0: timing(t0, final["_T"][t0], tab, bars, R.SEED) for t0 in R.TRADE_T0},
        "H_O5_agent_shuffle": agent_shuffle(retained, ctx),
        "H_O5_midday_placebo": midday_placebo(b, use, cal),
        "H_O6": h_o6(b, tab, ag, a7_ok),
    }
    doc["gate_O1"] = bool(h1["pass"] and h2_pass)
    auc_c = final["diag"]["10:00"]["auc"]["CONT"]
    doc["v2_trigger"] = {"cont_auc": auc_c["auc"], "cont_auc_ci95": auc_c["ci95"],
                         "gate_O1_fails_on_H_O2": bool(not h2_pass),
                         "fires": bool(auc_c["auc"] >= V2_AUC and auc_c["ci95"][0] > 0.5 and not h2_pass)}
    doc["runtime_min"] = round((time.time() - t_start) / 60, 1)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for t in trials:
        t["timestamp"] = stamp
    return doc, trials


def strip(st: dict) -> dict:
    return {k: v for k, v in st.items() if not k.startswith("_")}


def o0h_status(od) -> dict[str, Any]:
    """Gate O0-H on the SAME denominator for both markets: ES's (gate0.json) is the share of the opening model's usable
    sessions, so NQ's is the builder's `O0_H_alt.opening_model_usable_sessions` (its headline `O0_H` counts every
    fut_index_sessions NQ day). Fixed 2026-09-28 before the NQ gates were computed. A missing key is None, never a pass."""
    g = json.loads((od / "gate0.json").read_text(encoding="utf-8"))
    es = bool(g["O0_H"]["ES"]["pass"])
    meta = R.REPO / "data" / "fixtures" / "fut_nq_options_eod.meta.json"
    nq, share = None, None
    if meta.exists():
        m = json.loads(meta.read_text(encoding="utf-8"))
        o = ((m.get("gates") or {}).get("O0_H_alt") or {}).get("opening_model_usable_sessions") or {}
        if "passes" in o:
            nq, share = bool(o["passes"]), o.get("share")
    return {"ES": es, "NQ": nq, "NQ_share_of_usable_sessions": share, "both_pass": bool(es and nq)}
