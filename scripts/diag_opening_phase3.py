"""POST HOC diagnostics of D646 (the opening model's stage S-A), EXPLORATORY. The principal, 2026-09-28: "do some
diagnosis and statistical analysis of the failures and assess whether there are any improvements to be had".

    uv run python scripts/diag_opening_phase3.py --data-root DIR     # -> data/opening/diag_phase3.json

NOTHING HERE IS A TEST. It reads the same in-sample data D646 was scored on, after the verdict, so every number is
descriptive. A construction it suggests is a hypothesis for a NEW pre-registration, confirmed on data it has not
seen; it is never a re-tuned S-A. It re-runs D646's walk-forward exactly (the same code and seed) and then asks:

1. THE ORACLE CEILING: trade the TRUE label (CONT -> d0, FADE -> -sign(gap)) with D645's exits (the stop at 0.5 x the
   09:30 -> t0 range, 60-minute time stop), and with a hold to the 15:59 close and no stop. If even the oracle loses
   after cost, the classifier is not the bottleneck; the trade is.
2. THE PROBABILITIES: one-vs-rest AUC per class, the distribution of max p, how often each class crosses theta.
3. DOSE-RESPONSE: the FADE trade's 60-minute net by decile of p_FADE, and CONT's by p_CONT. A monotone rise says the
   probabilities carry tradeable ordering. No threshold is chosen.
4. FEATURES: the OOS log-loss change from dropping each S-A feature (the same walk-forward).
5. THE BASELINES: gross against net, exit reasons, by year; how much of a FADE day's gap fills inside the hour.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

REPO = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("run_opening_stages", REPO / "scripts" / "run_opening_stages.py")
assert _s is not None and _s.loader is not None
R = importlib.util.module_from_spec(_s)
sys.modules["run_opening_stages"] = R
_s.loader.exec_module(R)

OUT = REPO / "data" / "opening" / "diag_phase3.json"
T0 = "10:00"


def sim_detail(bars: dict, entry_bar: int, D: int, stop_dist: float, hold_to_close: bool = False) -> tuple | None:
    """D645's exits (or, with hold_to_close, no stop and an exit at the last RTH bar)."""
    if hold_to_close:
        m = bars["m"]
        k = np.flatnonzero(m == entry_bar)
        if len(k) == 0 or D == 0:
            return None
        return bars["c"][k[0]], bars["c"][-1], "close"
    return R.simulate(bars, entry_bar, D, stop_dist)


def stats_of(v: np.ndarray) -> dict:
    v = np.asarray(v, dtype=float)
    v = v[np.isfinite(v)]
    if len(v) < 3:
        return {"n": int(len(v))}
    se = v.std(ddof=1) / np.sqrt(len(v))
    return {"n": int(len(v)), "mean": float(v.mean()), "se": float(se), "t": float(v.mean() / se), "median": float(np.median(v)),
            "win": float((v > 0).mean())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    R.DATA_ROOT = a.data_root
    b, use = R.load(False)
    tab = R.session_table(b, use)
    cal = sorted({s for r in R.ROOTS for s in tab[r].index if tab[r].loc[s, "usable"] and s >= "2016-01-04"})
    D = R.dataset(tab, T0, T0)
    P = R.walk_forward(D, list(R.S_A), cal)
    bars = R.bar_arrays(b)
    out: dict = {"POST_HOC": "exploratory diagnostics of D646; nothing here is a test or a selection", "t0": T0}

    # ---- 2. the probabilities
    y = P["label"].to_numpy()
    pr = P[[f"p_{c}" for c in R.CLASSES]].to_numpy(float)
    out["auc_one_vs_rest"] = {c: float(roc_auc_score((y == c).astype(int), pr[:, j])) for j, c in enumerate(R.CLASSES)}
    out["max_p_quantiles"] = {q: float(np.quantile(pr.max(axis=1), q)) for q in (0.5, 0.9, 0.99)}
    out["share_crossing_theta"] = {c: float((pr[:, j] >= R.THETA).mean()) for j, c in enumerate(R.CLASSES)}
    out["label_share_oos"] = {c: float((y == c).mean()) for c in R.CLASSES}

    # ---- trade outcomes per row: oracle, dose-response and baselines
    rows = []
    for rec in P.itertuples(index=False):
        key = (rec.root, rec.session)
        if key not in bars:
            continue
        d = tab[rec.root].loc[rec.session]
        rng_ = float(d[f"hi_{T0}"] - d[f"lo_{T0}"])
        gap = float(d["open"] - d["prior_close"])
        cost = R.COST_USD[rec.root] / R.USD_PER_POINT[rec.root]
        row = {"root": rec.root, "session": rec.session, "label": rec.label, "d0": rec.d0, "gap_atr": gap / float(d["atr20"]),
               "p_CONT": rec.p_CONT, "p_FADE": rec.p_FADE}
        for name, side in (("cont", int(rec.d0)), ("fade", int(-np.sign(gap))), ("b2", -int(rec.d0))):
            for hold in (False, True):
                sim = sim_detail(bars[key], R.hm(T0), side, 0.5 * rng_, hold) if side != 0 else None
                tag = f"{name}_{'close' if hold else 'd645'}"
                if sim is None:
                    row[tag + "_net"] = row[tag + "_gross"] = np.nan
                    row[tag + "_why"] = "none"
                else:
                    e, x, why = sim
                    g = R.pnl_bp(side, e, x)
                    row[tag + "_gross"], row[tag + "_net"], row[tag + "_why"] = g, g - cost / e * 1e4, why
        # how much of the gap fills within the hour and by the close (FADE days)
        m, c = bars[key]["m"], bars[key]["c"]
        pc, op = float(d["prior_close"]), float(d["open"])
        within = (m > R.hm(T0)) & (m <= R.hm(T0) + R.HOLD_MIN)
        if gap != 0:
            toward = -np.sign(gap)
            ext = (toward * (c[within] - op)).max() if within.any() else np.nan
            ext_day = (toward * (c[m >= R.hm("09:30")] - op)).max()
            row["fill_frac_hour"] = float(ext / abs(gap)) if np.isfinite(ext) else np.nan
            row["fill_frac_day"] = float(ext_day / abs(gap))
        rows.append(row)
    T = pd.DataFrame(rows)

    # ---- 1. the oracle ceiling (true labels)
    orc = {}
    for lab, name in (("CONT", "cont"), ("FADE", "fade")):
        s = T[T["label"] == lab]
        orc[lab] = {"d645_exits_net": stats_of(s[f"{name}_d645_net"]), "d645_exits_gross": stats_of(s[f"{name}_d645_gross"]),
                    "exit_reasons": s[f"{name}_d645_why"].value_counts(normalize=True).round(3).to_dict(),
                    "hold_to_close_net": stats_of(s[f"{name}_close_net"])}
    out["oracle"] = orc
    fd = T[T["label"] == "FADE"]
    out["fade_days_fill"] = {"median_frac_within_hour": float(fd["fill_frac_hour"].median()),
                             "share_reaching_75pct_within_hour": float((fd["fill_frac_hour"] >= 0.75).mean()),
                             "median_frac_by_close": float(fd["fill_frac_day"].median())}

    # ---- 3. dose-response by probability decile (no threshold chosen)
    def by_decile(col: str, trade: str) -> list:
        q = pd.qcut(T[col].rank(method="first"), 10, labels=False)
        g = T.assign(q=q).groupby("q")
        return [{"decile": int(k), "p_mean": float(v[col].mean()), "n": int(len(v)),
                 "net_mean": float(v[trade].mean()), "gross_mean": float(v[trade.replace('_net', '_gross')].mean())}
                for k, v in g]
    out["dose_fade"] = by_decile("p_FADE", "fade_d645_net")
    out["dose_cont"] = by_decile("p_CONT", "cont_d645_net")
    for k in ("dose_fade", "dose_cont"):
        pm = np.array([r["p_mean"] for r in out[k]])
        nm = np.array([r["gross_mean"] for r in out[k]])
        out[k + "_spearman_gross"] = float(pd.Series(pm).corr(pd.Series(nm), method="spearman"))

    # ---- 5. the unconditioned trades gross vs net (B1 = cont on every row, B2 = its reverse)
    out["unconditioned"] = {
        "B1_follow_d0": {"gross": stats_of(T["cont_d645_gross"]), "net": stats_of(T["cont_d645_net"]),
                          "exits": T["cont_d645_why"].value_counts(normalize=True).round(3).to_dict(),
                          "gross_by_year": T.groupby(T["session"].str[:4])["cont_d645_gross"].mean().round(2).to_dict(),
                          "hold_to_close_gross": stats_of(T["cont_close_gross"])},
        "B2_fade_d0": {"gross": stats_of(T["b2_d645_gross"]), "net": stats_of(T["b2_d645_net"]),
                        "hold_to_close_gross": stats_of(T["b2_close_gross"])},
        "FADE_the_gap_every_day": {"gross": stats_of(T["fade_d645_gross"]),
                                   "big_gap_only_gross": stats_of(T.loc[T["gap_atr"].abs() >= 0.25, "fade_d645_gross"]),
                                   "big_gap_hold_to_close_gross": stats_of(T.loc[T["gap_atr"].abs() >= 0.25, "fade_close_gross"])},
        "cost_bp_mean": float((T["cont_d645_gross"] - T["cont_d645_net"]).mean()),
    }

    # ---- 4. drop-one-feature (the same walk-forward)
    full = R.logloss(pr, y)
    drop = {}
    for f in R.S_A:
        cols = [c for c in R.S_A if c != f]
        Pd = R.walk_forward(D, cols, cal)
        drop[f] = float(R.logloss(Pd[[f"p_{c}" for c in R.CLASSES]].to_numpy(float), Pd["label"].to_numpy()) - full)
    out["logloss_full"] = full
    out["logloss_increase_when_dropped"] = drop
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("auc_one_vs_rest", "share_crossing_theta", "oracle", "fade_days_fill",
                                          "dose_fade_spearman_gross", "dose_cont_spearman_gross",
                                          "logloss_increase_when_dropped")}, indent=1, default=float))
    print(json.dumps(out["unconditioned"], indent=1, default=float))
    print("dose FADE:", [(r["decile"], round(r["p_mean"], 3), round(r["gross_mean"], 2)) for r in out["dose_fade"]])
    print("dose CONT:", [(r["decile"], round(r["p_mean"], 3), round(r["gross_mean"], 2)) for r in out["dose_cont"]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
