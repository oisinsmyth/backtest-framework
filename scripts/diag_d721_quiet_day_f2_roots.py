"""D721 DIAG: does F2 earn on forecast-quiet days on ES, YM and RTY as it did on NQ (D720), and does the pattern follow
the root's volatility? Spec: docs/decisions/D721-DIAG-DESIGN-the-quiet-day-f2-pattern-on-other-roots.md, committed
before this file existed.

    uv run python scripts/diag_d721_quiet_day_f2_roots.py --selftest    # synthetic only
    uv run python scripts/diag_d721_quiet_day_f2_roots.py --run         # once -> data/diag_d721_quiet_day_f2.json

F2 is D711's code at 15:30, unchanged, on each root at one micro. The label is D671's realised-only size forecast M0
(walk-forward) and its walk-forward tier tau, on each root's own frame, with every cut constant lowered to 2024-01-01
through D720's `lowered_cut`. YM's and RTY's overnight range comes from fut_opening_globex_1m_ym_rty (their frames hold
day-session bars only), cut at read time. D691's M1 (with ln IV/RV20) is reported for ES and NQ. Nothing dated
2024-01-01 or later is used; no per-date SqueezeMetrics series is written.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d720_size_the_direction as Z  # noqa: E402

OUT = REPO / "data" / "diag_d721_quiet_day_f2.json"
ROOTS4 = ("ES", "NQ", "YM", "RTY")
OTHER = ("ES", "YM", "RTY")
GLOBEX_YM_RTY = "fut_opening_globex_1m_ym_rty.csv.gz"
HI, CUT24, EDGE = Z.HI, Z.CUT24, Z.EDGE


class D721Error(AssertionError):
    pass


P = Z.P


# ================================================================================ statistics
def efficiency(g: np.ndarray) -> float:
    s = float(np.abs(g).sum())
    return float(g.sum()) / s if s > 0 else float("nan")


def eff_gap(tau_tr: np.ndarray, g: np.ndarray) -> float:
    lo, hi = tau_tr < 1 / 3, tau_tr >= 2 / 3
    if not lo.any() or not hi.any():
        return float("nan")
    return efficiency(g[lo]) - efficiency(g[hi])


def spear(a: np.ndarray, b: np.ndarray) -> float:
    return float(stats.spearmanr(a, b)[0]) if len(a) > 2 else float("nan")


def rotation(tau_cal: np.ndarray, sidx: np.ndarray, g: np.ndarray, fn: Callable[[np.ndarray, np.ndarray], float]) -> dict[str, Any]:
    n = len(tau_cal)
    obs = fn(tau_cal[sidx], g)
    if not math.isclose(fn(np.roll(tau_cal, 0)[sidx], g), obs, rel_tol=0, abs_tol=1e-12):
        raise D721Error("rotation: offset 0 does not reproduce the observed statistic")
    null = np.array([fn(np.roll(tau_cal, k)[sidx], g) for k in range(EDGE, n - EDGE)])
    null = null[np.isfinite(null)]
    return {"observed": obs, "offsets": int(len(null)), "p05": float(np.quantile(null, 0.05)),
            "p50": float(np.median(null)), "p95": float(np.quantile(null, 0.95)), "p95_se": 0.0,
            "rank": float((null < obs).mean())}


def reading(rank: float) -> str:
    return "SIMILAR" if rank < 0.05 else ("OPPOSITE" if rank > 0.95 else "NOT SIMILAR")


def tercile_table(tau_tr: np.ndarray, g: np.ndarray, net: np.ndarray) -> list[dict[str, Any]]:
    out = []
    for lo, hi, nm in ((0, 1 / 3, "low (quiet)"), (1 / 3, 2 / 3, "mid"), (2 / 3, 1.01, "high (big)")):
        m = (tau_tr >= lo) & (tau_tr < hi)
        out.append({"tercile": nm, "trades": int(m.sum()),
                    "mean_gross": float(g[m].mean()) if m.any() else None,
                    "median_gross": float(np.median(g[m])) if m.any() else None,
                    "efficiency": efficiency(g[m]) if m.any() else None,
                    "mean_net": float(net[m].mean()) if m.any() else None,
                    "win_rate": float((net[m] > 0).mean()) if m.any() else None})
    return out


def book(q: np.ndarray, g: np.ndarray, net: np.ndarray, sidx: np.ndarray, cal: np.ndarray) -> dict[str, Any]:
    n = len(cal)
    daily = np.bincount(sidx, weights=q * net, minlength=n)
    gdaily = np.bincount(sidx, weights=q * g, minlength=n)
    years = np.array([s[:4] for s in cal])
    by_year = {y: float(daily[years == y].sum()) for y in np.unique(years)}
    held = q > 0
    return {"trades": int(held.sum()), "net_sharpe": Z.sharpe(daily), "net_sortino": Z.sortino(daily),
            "gross_sharpe": Z.sharpe(gdaily), "gross_sortino": Z.sortino(gdaily),
            "net_usd_a_year": float(daily.sum() / (n / 252.0)), "max_dd": Z.max_dd(daily),
            "trade_distribution_net": Z.trade_dist(net[held]), "net_by_year": by_year,
            "years_positive": int(sum(v > 0 for v in by_year.values())), "years": len(by_year)}


# ================================================================================ builds
def build_labels() -> dict[str, pd.DataFrame]:
    import stage0_d662_gamma_product as S
    import stage0_d691_iv_size as I
    C, T, M = I.C, I.T, I.M
    frames: dict[str, dict[str, Any]] = {}
    with Z.lowered_cut(I, S, T, M):
        b, use, _gd, R = M.load_bars(I.DATA, False, ROOTS4)
        Z.no_session_after(b["session"].unique(), "the bars")
        C._R = R
        T.MULT.update(M.MULT)
        tabs = R.session_table(b, use, roots=ROOTS4)
        dix = pd.read_csv(I.DATA / "raw" / "squeezemetrics" / "DIX.csv", encoding="utf-8", dtype={"date": str})
        gex = dix[dix["date"] < CUT24].set_index("date")["gex"].astype(float).sort_index()
        cal = pd.read_csv(I.FIX / "cme_session_calendar.csv.gz", encoding="utf-8", dtype={"day": str})
        glob = pd.read_csv(I.FIX / GLOBEX_YM_RTY, encoding="utf-8", dtype={"session": str, "hhmm": str},
                           usecols=["root", "session", "hhmm", "high", "low"])
        glob = glob[glob["session"] < CUT24]
        Z.no_session_after(glob["session"].unique(), "the YM/RTY overnight bars")
        for r in ROOTS4:
            d = T.root_frame(b, tabs[r], r)
            d = d[np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)].copy()
            Z.no_session_after(d.index, f"{r}'s frame")
            d["gd_spx"] = T.gex_prior(gex, d.index)
            T.gex_lag_audit(gex, d.index[:: max(1, len(d) // 40)])
            on = C.overnight(glob if r in ("YM", "RTY") else b, r)
            C.overnight_audit(on)
            crow = cal[cal["root"] == r].set_index("day")
            S_ = C.session_features(d, on, crow)
            frames[r] = {"d": d, "S": S_}
        ivs = {r: I.build_iv(r)[0] for r in ("ES", "NQ")}
        for r, iv in ivs.items():
            Z.no_session_after(iv.index, f"{r}'s IV table")
    if I.CUT != "2025-03-01" or T.RESERVED_FROM != "2025-03-01" or M.RESERVED_FROM != "2025-03-01":
        raise D721Error("the cut constants were not restored")
    labels = {}
    for r in ROOTS4:
        d, S_ = frames[r]["d"], frames[r]["S"]
        sess = S_.index.to_numpy(str)
        F0 = S_[list(C.SIZE_FEATS)].to_numpy(float)
        y = S_["y"].to_numpy(float)
        f0 = I.forecast(F0, y, I.SIGN0)
        idx = list(range(0, len(sess), max(1, len(sess) // 30)))
        C.forecast_audit(f0, F0, y, sess, idx)
        fl, _ = C.size_forecast(F0, y, leak=True)
        try:
            C.forecast_audit(fl, F0, y, sess, idx)
        except C.D671Error:
            pass
        else:
            raise D721Error(f"{r}: the forecast audit did not fire on the leaked canary")
        tau = C.tiers(f0)
        C.tier_audit(tau, f0, idx)
        try:
            C.tier_audit(C.tiers(f0, leak=True), f0, idx)
        except C.D671Error:
            pass
        else:
            raise D721Error(f"{r}: the tier audit did not fire on the leaked canary")
        lab = pd.DataFrame({"f0": f0, "tau": tau, "y": y,
                            "sig20": d["sig20"].reindex(S_.index).to_numpy(float)}, index=pd.Index(sess))
        if r in ivs:
            dz = I.design(frames[r], ivs[r])
            F1 = np.column_stack([dz["F0"], dz["ivrv"]])
            f1 = I.forecast(F1, dz["y"], I.SIGN1)
            lab["tau_m1"] = pd.Series(C.tiers(f1), index=pd.Index(dz["sess"])).reindex(lab.index).to_numpy(float)
        lab.attrs["spearman_f0_y"] = spear(f0[np.isfinite(f0) & np.isfinite(y)], y[np.isfinite(f0) & np.isfinite(y)])
        labels[r] = lab
    return labels


def build_f2() -> dict[str, dict[str, Any]]:
    import stage1_d711_f2_mechanism as M711
    d711 = json.loads((REPO / "data" / "stage1_d711_f2_mechanism.json").read_text(encoding="utf-8"))["A2"]["roots"]
    d716 = json.loads((REPO / "data" / "vault_d716_power.json").read_text(encoding="utf-8"))["known_answers"]["nq_own_window"]
    out = {}
    for r in ROOTS4:
        L = M711.load_root(r)
        X = M711.clock_frame(L, M711.ANCHOR)
        Z.no_session_after(X.index, f"{r}'s F2 frame")
        F = M711.f2_on(X)
        take = F["take"] & F["window"]
        g = X["gross"].to_numpy(float)[take]
        net = g - float(X.attrs["cost"])
        ka = {"trades": int(take.sum()), "mean_net": float(net.mean())}
        if r == "ES":
            ka["d707"] = M711.es_known_answer(X)["d707_frozen_reproduced"]
            if ka["trades"] != ka["d707"]["trades"] or not math.isclose(ka["mean_net"], ka["d707"]["mean_net"], abs_tol=1e-9):
                raise D721Error(f"ES F2's known answer is not reproduced: {ka}")
        else:
            want = d716 if r == "NQ" else d711[r]["line"]["filtered"] | {"trades": d711[r]["trades"]}
            if ka["trades"] != want["trades"] or not math.isclose(ka["mean_net"], want["mean_net"], abs_tol=1e-9):
                raise D721Error(f"{r} F2's known answer is not reproduced: {ka} against {want}")
        out[r] = {"days": X.index.to_numpy(str)[take], "g": g, "net": net, "a": X["a"].to_numpy(float)[take],
                  "cost": float(X.attrs["cost"]), "known_answer": ka}
    return out


# ================================================================================ the study
def study_root(r: str, lab: pd.DataFrame, f2: dict[str, Any], col: str = "tau") -> dict[str, Any]:
    fin = np.isfinite(lab[col].to_numpy(float))
    cal = lab.index[fin].to_numpy(str)
    cal = cal[cal <= HI]
    pos = pd.Series(np.arange(len(cal)), index=cal)
    sf = pos.reindex(f2["days"]).to_numpy(float)
    keep = np.isfinite(sf)
    sidx = sf[keep].astype(int)
    g, net, a, days = f2["g"][keep], f2["net"][keep], f2["a"][keep], f2["days"][keep]
    tau_cal = lab[col].reindex(cal).to_numpy(float)
    tau_tr = tau_cal[sidx]
    Z.join_audit(days, cal, sidx, tau_cal, tau_tr)
    res: dict[str, Any] = {"label": col, "window": [str(cal[0]), str(cal[-1])], "sessions": int(len(cal)),
                           "trades": int(keep.sum()), "trades_outside_window": int((~keep).sum())}
    res["terciles"] = tercile_table(tau_tr, g, net)
    t0 = time.time()
    res["G1_spearman_tau_gross"] = rotation(tau_cal, sidx, g, spear)
    res["G1_spearman_tau_gross"]["reading"] = reading(res["G1_spearman_tau_gross"]["rank"])
    res["efficiency_gap_low_minus_high"] = rotation(tau_cal, sidx, g, eff_gap)
    res["rotation_wall_s"] = time.time() - t0
    hi_m, lo_m = tau_tr >= 2 / 3, tau_tr < 1 / 3
    res["Hb_within"] = {"spearman_a_gross_big_days": spear(a[hi_m], g[hi_m]), "n_big": int(hi_m.sum()),
                        "spearman_a_gross_quiet_days": spear(a[lo_m], g[lo_m]), "n_quiet": int(lo_m.sum()),
                        "spearman_a_gross_all": spear(a, g)}
    res["books"] = {"F2": book(np.ones_like(g), g, net, sidx, cal),
                    "F2_quiet_only": book((tau_tr < 1 / 3).astype(float), g, net, sidx, cal)}
    return res


def run() -> int:
    t_start = time.time()
    P("[D721] labels (M0 on four roots, M1 on ES/NQ; cut at 2024-01-01) ...")
    labels = build_labels()
    P("[D721] F2 on four roots ...")
    f2 = build_f2()
    out: dict[str, Any] = {"spec": "D721-DIAG-DESIGN-the-quiet-day-f2-pattern-on-other-roots.md",
                           "seal": f"nothing on or after {CUT24}", "roots": {}}
    for r in ROOTS4:
        lab = labels[r]
        res = {"known_answer": f2[r]["known_answer"], "cost_usd": f2[r]["cost"],
               "label_spearman_f0_y_all": lab.attrs["spearman_f0_y"],
               "median_sig20_bp": float(np.nanmedian(lab["sig20"].to_numpy(float)[lab.index.to_numpy(str) <= HI])),
               "M0": study_root(r, lab, f2[r], "tau")}
        if "tau_m1" in lab:
            res["M1_reported"] = study_root(r, lab, f2[r], "tau_m1")
        out["roots"][r] = res
        P(f"[D721] {r}: M0 {res['M0']['G1_spearman_tau_gross']['reading']}")
    similar = [r for r in OTHER if out["roots"][r]["M0"]["G1_spearman_tau_gross"]["reading"] == "SIMILAR"]
    out["Ha_similar_roots"] = similar
    out["Ha_supported"] = len(similar) >= 2
    out["Hb_across_roots"] = sorted(({"root": r, "median_sig20_bp": out["roots"][r]["median_sig20_bp"],
                                      "G1_spearman": out["roots"][r]["M0"]["G1_spearman_tau_gross"]["observed"]}
                                     for r in ROOTS4), key=lambda x: -x["median_sig20_bp"])
    out["wall_min"] = (time.time() - t_start) / 60
    OUT.write_text(json.dumps(out, indent=1, default=Z._json) + "\n", encoding="utf-8", newline="\n")
    P(f"[D721] H-a supported: {out['Ha_supported']} ({similar}); wrote {OUT.name} in {out['wall_min']:.1f} min")
    return 0


# ================================================================================ self-test (synthetic only)
def selftest() -> int:
    fails: list[str] = []
    rng = np.random.default_rng(7)
    n = 800
    tau_cal = Z.pooled_terciles(rng.normal(size=n))
    sidx = np.sort(rng.choice(n, 300, replace=False))
    # gross falls with tau: the pattern -> SIMILAR; independent -> not SIMILAR (most seeds); rising -> OPPOSITE
    g_fall = 40 * (0.6 - tau_cal[sidx]) + rng.normal(0, 30, len(sidx))
    g_none = rng.normal(5, 40, len(sidx))
    g_rise = -g_fall
    if reading(rotation(tau_cal, sidx, g_fall, spear)["rank"]) != "SIMILAR":
        fails.append("a falling pattern was not SIMILAR")
    if reading(rotation(tau_cal, sidx, g_rise, spear)["rank"]) != "OPPOSITE":
        fails.append("a rising pattern was not OPPOSITE")
    if reading(rotation(tau_cal, sidx, g_none, spear)["rank"]) == "SIMILAR":
        fails.append("an independent gross read SIMILAR")
    if not (rotation(tau_cal, sidx, g_fall, eff_gap)["observed"] > 0):
        fails.append("efficiency gap sign")
    t = tercile_table(tau_cal[sidx], g_fall, g_fall - 4)
    if not (t[0]["mean_gross"] > t[2]["mean_gross"]):
        fails.append("tercile table order")
    b = book(np.ones(len(sidx)), g_fall, g_fall - 4, sidx, np.array([f"20{19 + i // 300}-01-01" for i in range(n)]))
    if b["trades"] != len(sidx):
        fails.append("book")
    if fails:
        P("SELFTEST FAILED:", fails)
        return 1
    P("SELFTEST OK: a falling pattern reads SIMILAR, a rising one OPPOSITE, an independent one not SIMILAR; the "
      "efficiency gap and tercile table have the right sign; the book runs")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.run:
        if OUT.exists():
            raise D721Error(f"{OUT.name} exists: D721 runs once")
        return run()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
