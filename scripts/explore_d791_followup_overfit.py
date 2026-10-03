"""D791 follow-up 2 (looks taken AFTER seeing D791; disclosed): how much of the walk-forward ridge is overfit?

    uv run --no-sync python scripts/explore_d791_followup_overfit.py

On D791's 36-feature no-calendar ridge:
  1. per test year: the Spearman of the model with gross on its own TRAINING years against the following test year;
  2. the stability of the weights: each feature's coefficient in every fold (trained on years before 2018 ... before
     2023, and on all of 2016-2023); the share of folds whose sign matches the full fit;
  3. sensitivity to the one setting (ridge alpha 10 / 100 / 1000) and to the window (expanding against a rolling
     three-year window). These are reported, not chosen from.
Reads D791's feature cache only (in-sample 2016-2023). Writes data/explore_d791_followup_overfit.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import explore_d791_oracle_patterns as M  # noqa: E402

OUT = REPO / "data" / "explore_d791_followup_overfit.json"
CALENDAR = ("month_sin", "month_cos", "weekday", "est_clock")


def fit(Xtr: np.ndarray, gtr: np.ndarray, alpha: float) -> tuple[Ridge, np.ndarray]:
    a, _ = M.rank_scale(Xtr, Xtr[:1])
    t = (pd.Series(gtr).rank().to_numpy() / len(gtr)) - 0.5
    return Ridge(alpha=alpha).fit(a, t), a


def run_wf(X: pd.DataFrame, fs: list[str], alpha: float, rolling: int | None, cost: float) -> dict:
    yr = X["year"].to_numpy()
    A = X[fs].to_numpy(float)
    g = X["gross"].to_numpy(float)
    gp = X["gross_p"].to_numpy(float)
    filled = X["filled"].to_numpy(bool)
    pred = np.full(len(X), np.nan)
    take = np.zeros(len(X), bool)
    folds = {}
    for ty in M.TEST_YEARS:
        tr = (yr < ty) if rolling is None else ((yr < ty) & (yr >= str(int(ty) - rolling)))
        te = yr == ty
        a_tr, a_te = M.rank_scale(A[tr], A[te])
        t = (pd.Series(g[tr]).rank().to_numpy() / tr.sum()) - 0.5
        m = Ridge(alpha=alpha).fit(a_tr, t)
        ptr, pte = m.predict(a_tr), m.predict(a_te)
        pred[te] = pte
        take[te] = pte > np.quantile(ptr, 2 / 3)
        k = take & te & filled
        folds[ty] = {"train_years": f"{yr[tr].min()}-{yr[tr].max()}", "rho_train": M.spearman(ptr, g[tr]),
                     "rho_test": M.spearman(pte, g[te]), "passive_test_net": float((gp[k] - cost).mean()) if k.any() else None,
                     "passive_test_n": int(k.sum()), "coef": dict(zip(fs, map(float, m.coef_)))}
    oos = np.isin(yr, M.TEST_YEARS)
    k = take & oos & filled
    net = gp[k] - cost
    return {"oos_rho": M.spearman(pred[oos], g[oos]), "passive_n": int(k.sum()), "passive_net": float(net.mean()),
            "passive_t": M.tstat(net), "folds": folds}


def main() -> int:
    X = pd.read_csv(M.FEAT, dtype={"day": str, "year": str}, encoding="utf-8")
    with open(M.META, encoding="utf-8") as fh:
        cost = json.load(fh)["cost_p"]
    fs = [c for c in X.columns if c not in M.NON_FEATURES and c not in CALENDAR]
    g = X["gross"].to_numpy(float)
    base = run_wf(X, fs, 100.0, None, cost)
    full, a_full = fit(X[fs].to_numpy(float), g, 100.0)
    full_coef = dict(zip(fs, map(float, full.coef_)))
    stab = {}
    for f in fs:
        cs = [base["folds"][ty]["coef"][f] for ty in M.TEST_YEARS]
        stab[f] = {"full": full_coef[f], "by_fold": [round(c, 4) for c in cs],
                   "sign_agrees_with_full": f"{sum(np.sign(c) == np.sign(full_coef[f]) for c in cs)} of {len(cs)}"}
    stab = dict(sorted(stab.items(), key=lambda kv: -abs(kv[1]["full"])))
    sens = {}
    for alpha in (10.0, 100.0, 1000.0):
        for rolling in (None, 3):
            r = run_wf(X, fs, alpha, rolling, cost)
            sens[f"alpha{int(alpha)}_{'expanding' if rolling is None else 'rolling3'}"] = {
                k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k != "folds"}
    res = {"features": len(fs), "base": {k: v for k, v in base.items() if k != "folds"},
           "folds": {ty: {k: v for k, v in f.items() if k != "coef"} for ty, f in base["folds"].items()},
           "in_sample_full_fit_rho": M.spearman(full.predict(a_full), g), "coefficient_stability": stab,
           "sensitivity": sens}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    print("folds (train rho -> test rho, passive test net):")
    for ty, f in res["folds"].items():
        print(f"  {ty} trained {f['train_years']}: {f['rho_train']:+.3f} -> {f['rho_test']:+.3f} | passive "
              f"{f['passive_test_net']:+.2f} (n {f['passive_test_n']})")
    print("full-sample in-sample rho:", round(res["in_sample_full_fit_rho"], 4), "| OOS rho:", round(base["oos_rho"], 4))
    print("coefficient stability (top 12 by full-sample weight):")
    for f, s in list(stab.items())[:12]:
        print(f"  {f:28s} full {s['full']:+.4f} | folds {s['by_fold']} | sign agrees {s['sign_agrees_with_full']}")
    agree = [int(s["sign_agrees_with_full"].split()[0]) for s in stab.values()]
    print("features whose fold signs all agree:", sum(a == 6 for a in agree), "of", len(agree), "| >= 5 of 6:",
          sum(a >= 5 for a in agree))
    print("sensitivity:")
    for k, v in sens.items():
        print(f"  {k:22s} OOS rho {v['oos_rho']:+.4f} | passive n {v['passive_n']} net {v['passive_net']:+.2f} t {v['passive_t']:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
