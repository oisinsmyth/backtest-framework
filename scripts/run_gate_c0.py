"""D635 -- Gate C0 of the index-reweight model: does predicted index roll flow reach the settlement window as
aggressive flow, and how much of it (kappa)?

Spec: docs/decisions/D635-PRE-REG-gate-c0-index-roll-flow-in-the-settlement-window.md (e001171), under
INDEX_REWEIGHT_FLOW_AMENDMENTS.md IR-A1..IR-A14. POWER (b0e992a) came first; this file after both, and before its one
run.

    uv run python -W error::RuntimeWarning scripts/run_gate_c0.py --selftest   # reads no hedge-day flow
    uv run python -W error::RuntimeWarning scripts/run_gate_c0.py --run        # refuses a second run
    uv run python -W error::RuntimeWarning scripts/run_gate_c0.py --check      # rebuilds, compares byte for byte

--run REFUSES until data/index_reweight/c0_signcheck.json holds a verdict for every root (D635 §7); a root that failed
it is VOID and dropped.

THE MODEL (D635 §4): S_win = kappa_B Q_B + kappa_G Q_G + e, no intercept, OLS, SE clustered by roll month.
Separable iff |corr(Q_B, Q_G)| < 0.9 and both t >= 2; else S_win = kappa_C (Q_B + AUM_B Q_G) + e.
THE GATE (§5): C0-flow = the gate's kappa > 0 with t >= 2. C0-price = on (root, day) pairs with both legs observed, the
signed L/N spread move from t0 = W_start - 10 min to W_end, in dollars per contract, regressed (with an intercept) on
the predicted spread impact sum_legs 0.7 sigma_d sqrt(|kappa Q| / V_d) P mult: slope > 0 with t >= 2.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
IR = REPO / "data" / "index_reweight"
OUT = IR / "gate_c0.json"
SIGN = IR / "c0_signcheck.json"
SPEC = REPO / "docs" / "decisions" / "D635-PRE-REG-gate-c0-index-roll-flow-in-the-settlement-window.md"
CUT = "2025-03-01"
T_BAR, SEP_RHO, Y_IMPACT = 2.0, 0.9, 0.7
WF_TRAIN, WF_TEST = 252, 63
REQUIRED_OUTPUTS = ("verdict", "flow", "price", "separability", "walk_forward", "beside", "exclusions",
                    "sign_check", "audits", "deviations", "reads")
DEVIATIONS = [
    "D635 s.6's 'GSCI hedge days on the NYSE calendar' is not built: no NYSE holiday calendar is on disk, and the "
    "CME calendar (the primary) is the root's own settlement days. Reported as not computed.",
    "C0-price's regression carries an intercept, so its 'slope' is the usual one; D635 s.5 does not say either way.",
]


class C0Error(RuntimeError):
    pass


def _load(name: str, fn: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


D = _load("c0_design", "c0_design.py")
P = _load("power_gate_c0", "power_gate_c0.py")
G = D.G


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ------------------------------------------------------------------ fitting
def ols(X: np.ndarray, y: np.ndarray, g: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """OLS with CR1 month-clustered SE (power_gate_c0.ols_cluster); returns b, t, se. A singular design returns zeros
    (the known answer: with every Q = 0 nothing is estimated and C0-flow fails)."""
    if np.linalg.matrix_rank(X.T @ X) < X.shape[1]:
        k = X.shape[1]
        return np.zeros(k), np.zeros(k), np.full(k, np.inf)
    b, t = P.ols_cluster(X, y, g)
    with np.errstate(divide="ignore", invalid="ignore"):
        se = np.where(t != 0, b / t, np.inf)
    return b, t, se


def flow_fit(o: pd.DataFrame) -> dict[str, Any]:
    Qb, Qg = o["Q_B"].to_numpy(float), o["Q_G"].to_numpy(float)
    aum, y, g = o["aum_bn"].to_numpy(float), o["S_win"].to_numpy(float), o["month"].to_numpy()
    nz = (Qb != 0) | (Qg != 0)
    rho = float(np.corrcoef(Qb[nz], Qg[nz])[0, 1]) if nz.sum() > 2 and Qg[nz].std() > 0 else 0.0
    b2, t2, se2 = ols(np.column_stack([Qb, Qg]), y, g)
    separable = bool(abs(rho) < SEP_RHO and t2[0] >= T_BAR and t2[1] >= T_BAR)
    bc, tc, sec = ols((Qb + aum * Qg)[:, None], y, g)
    if separable:
        k, t, se, mode = float(b2[0]), float(t2[0]), float(se2[0]), "separate (kappa_B)"
    else:
        k, t, se, mode = float(bc[0]), float(tc[0]), float(sec[0]), "combined (kappa_C)"
    return {"n": int(len(o)), "months": int(o["month"].nunique()), "corr_QB_QG": round(rho, 4),
            "kappa_B": float(b2[0]), "t_B": float(t2[0]), "kappa_G_per_bn": float(b2[1]), "t_G": float(t2[1]),
            "kappa_C": float(bc[0]), "t_C": float(tc[0]), "separable": separable, "mode": mode,
            "kappa": k, "t": t, "se": se, "kappa_plus_2se": k + 2 * se if np.isfinite(se) else None,
            "pass": bool(k > 0 and t >= T_BAR)}


def q_total(o: pd.DataFrame, fit: dict[str, Any]) -> np.ndarray:
    """kappa-weighted predicted flow per observation, contracts."""
    if fit["separable"]:
        return fit["kappa_B"] * o["Q_B"].to_numpy(float) + fit["kappa_G_per_bn"] * o["Q_G"].to_numpy(float)
    return fit["kappa_C"] * (o["Q_B"].to_numpy(float) + o["aum_bn"].to_numpy(float) * o["Q_G"].to_numpy(float))


# ------------------------------------------------------------------ the dependent
def attach_flow(o: pd.DataFrame, panel: pd.DataFrame, bdays: list[str], day_map: dict[tuple[str, str], str] | None = None) -> pd.DataFrame:
    """S_win for each observation's (sym, day); `day_map` moves an observation to another day (the placebo)."""
    o = o.copy()
    o["flow_day"] = [day_map.get((m, d), None) if day_map else d for m, d in zip(o["month"], o["day"])]
    keep = {(s, d) for s, d in zip(o["sym"], o["flow_day"]) if d is not None}
    sw = D.norms(panel, bdays, keep)
    o = o.merge(sw.rename(columns={"day": "flow_day"}), on=["sym", "flow_day"], how="left")
    return o


def load_panel() -> pd.DataFrame:
    panel = pd.read_csv(D.PANEL, encoding="utf-8", dtype={"day": str})
    panel = panel[panel["day"] < CUT].copy()
    panel["sym"] = panel["sym"].str.split("-").str[0]
    return panel


# ------------------------------------------------------------------ the price clause
def price_clause(o: pd.DataFrame, fit: dict[str, Any], panel: pd.DataFrame, prices: Any) -> dict[str, Any]:
    qt = q_total(o, fit)
    o = o.assign(qt=qt)
    pv = panel.set_index(["sym", "day"])
    vol = {s: g.set_index("day")["volume"] for s, g in panel.groupby("sym")}
    rows = []
    for (root, day), g in o.groupby(["root", "day"]):
        if set(g["role"]) != {"L", "N"}:
            continue
        L, N = g[g["role"] == "L"].iloc[0], g[g["role"] == "N"].iloc[0]
        push = N["qt"] - L["qt"]  # net predicted pressure on the spread N - L (buy N, sell L widens it)
        if push == 0:
            continue
        try:
            a, b = pv.loc[(L["sym"], day)], pv.loc[(N["sym"], day)]
        except KeyError:
            continue
        if not all(np.isfinite([a["px_t0"], a["px_end"], b["px_t0"], b["px_end"]])):
            continue
        comp = L["comp"]
        m_ = G.mult(comp)
        move = ((b["px_end"] - a["px_end"]) - (b["px_t0"] - a["px_t0"])) * m_ * np.sign(push)
        imp = 0.0
        ok = True
        for leg in (L, N):
            ym = (2000 + int(leg["sym"][3:5]), D.LETTER.index(leg["sym"][2]) + 1)
            hist = sorted(x for x in prices[comp] if x < day and ym in prices[comp][x])[-21:]
            if len(hist) < 21:
                ok = False
                break
            px = np.array([prices[comp][x][ym] for x in hist])
            if (px <= 0).any():
                ok = False
                break
            sig = float(np.std(np.diff(np.log(px)), ddof=1))
            v = vol.get(leg["sym"])
            vd = float(v[v.index < day].tail(20).mean()) if v is not None and (v.index < day).sum() >= 15 else np.nan
            if not np.isfinite(vd) or vd <= 0:
                ok = False
                break
            imp += Y_IMPACT * sig * np.sqrt(abs(leg["qt"]) / vd) * px[-1] * m_
        if ok:
            rows.append((root, day, day[:7], move, imp))
    pr = pd.DataFrame(rows, columns=["root", "day", "month", "move_usd", "impact_usd"])
    if len(pr) < 30:
        return {"pairs": int(len(pr)), "pass": False, "note": "too few pairs"}
    X = np.column_stack([np.ones(len(pr)), pr["impact_usd"].to_numpy(float)])
    b, t, se = ols(X, pr["move_usd"].to_numpy(float), pr["month"].to_numpy())
    return {"pairs": int(len(pr)), "months": int(pr["month"].nunique()), "intercept_usd": float(b[0]),
            "slope": float(b[1]), "t_slope": float(t[1]), "mean_move_usd": float(pr["move_usd"].mean()),
            "mean_impact_usd": float(pr["impact_usd"].mean()),
            "realised_over_predicted": float(pr["move_usd"].sum() / pr["impact_usd"].sum()),
            "by_root": {r: {"pairs": int(len(g)), "mean_move_usd": round(float(g["move_usd"].mean()), 2),
                            "mean_impact_usd": round(float(g["impact_usd"].mean()), 2)} for r, g in pr.groupby("root")},
            "pass": bool(b[1] > 0 and t[1] >= T_BAR)}


# ------------------------------------------------------------------ audits
def audit_signs(o: pd.DataFrame) -> None:
    """A long tracker's roll sells L and buys N."""
    bl, bn = o[(o["role"] == "L") & (o["Q_B"] != 0)], o[(o["role"] == "N") & (o["Q_B"] != 0)]
    if not ((bl["Q_B"] < 0).all() and (bn["Q_B"] > 0).all()):
        raise C0Error("sign audit: a BCOM roll does not sell L and buy N")


def audit_lag(o: pd.DataFrame) -> dict[str, Any]:
    """A second implementation of Q_B from the committed tracker panel and the strip, never calling c0_design's Q:
    Q_B(L, d) = -0.2 x AUM x w(d-1) / (P_L(d-1) x mult). It must agree to 1e-9 relative wherever the tracker holds
    d-1 (to det(2025))."""
    tr = pd.read_csv(D.TRACKER, encoding="utf-8", dtype={"day": str})
    w = {(d, c): float(v) for d, y, c, v in zip(tr["day"], tr["target_year"], tr["component"], tr["weight"])
         if int(y) == int(d[:4]) + 1}
    st = G.load_panel("fut_settle_strip", reserved_from=CUT, usecols=["root", "contract", "ref", "settle"]).frame
    ke = pd.read_csv(G.KE_STRIP, encoding="utf-8", dtype={"root": str, "contract": str, "ref": str})
    hole = pd.read_csv(G.HOLE_FILL, encoding="utf-8", dtype={"root": str, "contract": str, "ref": str})
    s = pd.concat([st, ke, hole[["root", "contract", "ref", "settle"]]]).drop_duplicates(["root", "contract", "ref"])
    px = {(r, c, d): float(v) for r, c, d, v in zip(s["root"], s["contract"], s["ref"], s["settle"])}
    checked = worst = 0.0
    for r in o[(o["role"] == "L") & (o["Q_B"] != 0)].itertuples():
        if (r.prev, r.comp) not in w:
            continue
        code = f"{r.root}{r.sym[2]}{int(r.sym[3:5]) % 10}"
        p = px.get((r.root, code, r.prev))
        if p is None:
            continue
        q2 = -0.2 * r.aum_bn * 1e9 * w[(r.prev, r.comp)] / (p * G.mult(r.comp))
        worst = max(worst, abs(q2 - r.Q_B) / abs(r.Q_B))
        checked += 1
    if checked < 1000 or worst > 1e-9:
        raise C0Error(f"lag audit: the second implementation of Q_B disagrees ({int(checked)} rows, worst {worst})")
    return {"rows": int(checked), "worst_rel_diff": worst}


def audit_norm() -> None:
    """The norm uses days strictly before d: a spike on day d moves S_win(d) by its full size and the norm of d by 0."""
    bd = [f"2020-01-{i:02d}" for i in range(1, 31)]
    p = pd.DataFrame({"sym": "XX", "day": bd, "net": [0.0] * 29 + [100.0]})
    s = D.norms(p, bd)
    if s["S_win"].iloc[-1] != 100.0:
        raise C0Error("norm audit: the day's own flow entered its norm")


def audit_right_quantity(o: pd.DataFrame, fit: dict[str, Any]) -> None:
    raw = o["S_win"].to_numpy(float)
    if np.allclose(raw, o["net"].to_numpy(float)):
        raise C0Error("right-quantity: S_win equals the raw net (the norm was not removed)")
    lo = o[o["role"] == "L"]
    k_l = ols(np.column_stack([lo["Q_B"], lo["Q_G"]]), lo["S_win"].to_numpy(float), lo["month"].to_numpy())[0][0]
    if np.isclose(k_l, fit["kappa_B"]):
        raise C0Error("right-quantity: the gate's kappa equals the L-only fit's")


# ------------------------------------------------------------------ build
def placebo_map(o: pd.DataFrame, bdays: list[str], bd: dict[str, int]) -> dict[tuple[str, str], str]:
    """Hedge day k of month m -> the k-th of BD12..BD16 of the same month."""
    out = {}
    for m, g in o.groupby("month"):
        hedge = sorted(set(g["day"]))
        non = sorted(d for d in bdays if d[:7] == m and 12 <= bd[d] <= 16)
        for k, d in enumerate(hedge):
            if k < len(non):
                out[(m, d)] = non[k]
    return out


def walk_forward(o: pd.DataFrame, bdays: list[str], separable: bool) -> dict[str, Any]:
    days = sorted(set(o["day"]))
    idx = {d: i for i, d in enumerate(bdays)}
    preds, actual, kpath = [], [], []
    start = bdays.index(days[0]) + WF_TRAIN
    while start < len(bdays) and bdays[start] <= days[-1]:
        tr = o[(o["day"].map(idx) >= start - WF_TRAIN) & (o["day"].map(idx) < start)]
        te = o[(o["day"].map(idx) >= start) & (o["day"].map(idx) < start + WF_TEST)]
        if len(tr) > 50 and len(te):
            f = flow_fit(tr)
            if not separable:
                f["separable"] = False
            preds.extend(q_total(te, f))
            actual.extend(te["S_win"])
            kpath.append({"test_from": bdays[start], "kappa": round(f["kappa_B"] if separable else f["kappa_C"], 6)})
        start += WF_TEST
    p, a = np.array(preds), np.array(actual)
    return {"windows": len(kpath), "oos_n": int(len(a)), "oos_corr": round(float(np.corrcoef(p, a)[0, 1]), 4) if len(a) > 2 else None,
            "oos_mse": float(np.mean((a - p) ** 2)) if len(a) else None, "zero_mse": float(np.mean(a ** 2)) if len(a) else None,
            "kappa_path": kpath}


def build(sign: dict[str, Any]) -> dict[str, Any]:
    b = D.build()
    o, bdays, bd, prices = b["obs"], b["bdays"], b["bd"], b["prices"]
    audit_signs(o)
    audit_norm()
    lag = audit_lag(o)
    void = sorted(r for r, v in sign["roots"].items() if not v["pass"])
    missing = sorted(set(o["root"]) - set(sign["roots"]))
    if missing:
        raise C0Error(f"the sign check has no verdict for {missing} (D635 s.7)")
    panel = load_panel()
    ex: dict[str, int] = {"void_roots_rows": int(o["root"].isin(void).sum())}
    o = o[~o["root"].isin(void)]
    o = attach_flow(o, panel, bdays)
    o = o.merge(panel[["sym", "day", "net"]], on=["sym", "day"], how="left")
    ex["no_panel_row"] = int(o["net"].isna().sum())
    ex["norm_under_15_days"] = int((o["net"].notna() & o["S_win"].isna()).sum())
    o = o[o["S_win"].notna()].reset_index(drop=True)
    ex["used"] = int(len(o))
    ex["by_root_used"] = {r: int(n) for r, n in o.groupby("root").size().items()}
    fit = flow_fit(o)
    audit_right_quantity(o, fit)
    price = price_clause(o, fit, panel, prices)
    # beside
    beside: dict[str, Any] = {}
    X = np.column_stack([np.ones(len(o)), o["Q_B"], o["Q_G"]])
    bi, ti, _ = ols(X, o["S_win"].to_numpy(float), o["month"].to_numpy())
    beside["with_intercept"] = {"intercept": float(bi[0]), "kappa_B": float(bi[1]), "t_B": float(ti[1]),
                                "kappa_G_per_bn": float(bi[2]), "t_G": float(ti[2])}
    beside["per_root"] = {r: {k: round(float(v), 6) for k, v in flow_fit(g).items() if k in ("kappa_B", "t_B", "kappa_C", "t_C")}
                          for r, g in o.groupby("root") if (g["Q_B"] != 0).sum() > 20}
    beside["per_year"] = {y: {k: round(float(v), 6) for k, v in flow_fit(g).items() if k in ("kappa_C", "t_C")}
                          for y, g in o.groupby(o["month"].str[:4])}
    beside["L_only"] = {k: flow_fit(o[o["role"] == "L"])[k] for k in ("kappa_B", "t_B", "kappa_C", "t_C")}
    beside["N_only"] = {k: flow_fit(o[o["role"] == "N"])[k] for k in ("kappa_B", "t_B", "kappa_C", "t_C")}
    rp = pd.read_csv(D.RPDW, encoding="utf-8")
    rpd = {(int(y), r): float(v) for y, r, v in zip(rp["target_year"], rp["ric"], rp["rpdw_pct"])}
    for lab, off in (("gsci_rpdw_prior_year", -1), ("gsci_rpdw_next_year", 1)):
        yy = o["month"].str[:4].astype(int)
        ratio = [rpd.get((y + off, D.RIC[r]), rpd.get((y, D.RIC[r]), 1.0)) / rpd[(y, D.RIC[r])] if r in D.RIC else 1.0
                 for y, r in zip(yy, o["root"])]
        f = flow_fit(o.assign(Q_G=o["Q_G"] * np.array(ratio)))
        beside[lab] = {k: f[k] for k in ("kappa_B", "t_B", "kappa_G_per_bn", "t_G", "kappa_C", "t_C", "separable")}
    qc = np.abs(o["Q_B"] + o["aum_bn"] * o["Q_G"])
    sgn = np.sign(o["Q_B"] + o["aum_bn"] * o["Q_G"])
    nzm = qc > 0
    qq = pd.qcut(qc[nzm], 5, labels=False, duplicates="drop")
    beside["dose_response_mean_signed_S_win_by_quintile"] = [round(float((o["S_win"][nzm] * sgn[nzm])[qq == i].mean()), 2)
                                                           for i in range(int(qq.max()) + 1)]
    from scipy.stats import spearmanr
    beside["dose_response_spearman"] = round(float(spearmanr(qc[nzm], (o["S_win"] * sgn)[nzm]).statistic), 4)
    pl = attach_flow(o.drop(columns=["S_win", "norm_days"]), panel, bdays, placebo_map(o, bdays, bd)).dropna(subset=["S_win"])
    pf = flow_fit(pl)
    beside["placebo_bd12_16"] = {"n": pf["n"], "kappa": pf["kappa"], "t": pf["t"], "mode": pf["mode"],
                                 "specificity_failure": bool(pf["t"] >= T_BAR and np.sign(pf["kappa"]) == np.sign(fit["kappa"]))}
    beside["gsci_nyse_calendar"] = "not computed (DEVIATIONS[0])"
    wf = walk_forward(o, bdays, fit["separable"])
    power = json.loads((IR / "power_c0.json").read_text(encoding="utf-8"))
    if fit["pass"] and price["pass"]:
        verdict = "PASS"
    elif not fit["pass"] and power["grid"]["0.05"]["pass_rate"] < 0.8:
        verdict = "INCONCLUSIVE (underpowered)"
    else:
        verdict = "FAIL"
    doc = {"spec": "D635 (e001171), POWER b0e992a, IR-A1..IR-A14", "cut": CUT,
           "verdict": {"verdict": verdict, "C0_flow": fit["pass"], "C0_price": price["pass"], "void_roots": void,
                       "kappa_carried_forward": fit["kappa"], "mode": fit["mode"]},
           "flow": fit, "price": price,
           "separability": {"corr_QB_QG": fit["corr_QB_QG"], "separable": fit["separable"], "rule": "|corr| < 0.9 and both t >= 2"},
           "walk_forward": wf, "beside": beside, "exclusions": ex, "sign_check": sign,
           "audits": {"lag": lag, "signs": "long tracker sells L, buys N", "norm": "strictly prior days",
                      "right_quantity": "S_win != raw net; gate kappa != L-only kappa"},
           "deviations": DEVIATIONS,
           "reads": {"spec_sha256": sha256(SPEC), "panel_sha256": sha256(D.PANEL), "tracker_sha256": sha256(D.TRACKER),
                     "signcheck_sha256": sha256(SIGN), **b["reads"]}}
    miss = [k for k in REQUIRED_OUTPUTS if k not in doc]
    if miss:
        raise C0Error(f"declared outputs missing: {miss}")
    return doc


def dump(doc: dict[str, Any]) -> str:
    return json.dumps(doc, indent=1, sort_keys=True, default=float) + "\n"


# ------------------------------------------------------------------ selftest
def selftest() -> int:
    """Reads NO hedge-day flow. The noise is the POWER pool (non-hedge days); the audits raise on breaks."""
    b = D.build()
    o = b["obs"]
    audit_signs(o)
    broken = o.copy()
    broken.loc[broken["role"] == "L", "Q_B"] *= -1
    try:
        audit_signs(broken[broken["Q_B"] != 0])
        raise AssertionError("the sign audit did not fire")
    except C0Error:
        pass
    audit_norm()
    lag = audit_lag(o)
    bad = o.copy()
    bad["Q_B"] = bad["Q_B"] * 1.0001
    try:
        audit_lag(bad)
        raise AssertionError("the lag audit did not fire")
    except C0Error:
        pass
    # synthetic worlds on the POWER noise pool
    panel = load_panel()
    nonhedge = {d for d in b["bdays"] if 12 <= b["bd"][d] <= 16}
    keep = {(s, d) for s, d in zip(panel["sym"], panel["day"]) if d in nonhedge}
    sw = D.norms(panel, b["bdays"], keep).dropna(subset=["S_win"])
    rng = np.random.default_rng(635)
    noise = rng.choice(sw["S_win"].to_numpy(float), size=len(o))
    for kappa, want in ((0.10, True), (0.0, False)):
        y = kappa * (o["Q_B"] + o["aum_bn"] * o["Q_G"]).to_numpy(float) + noise
        f = flow_fit(o.assign(S_win=y))
        if f["pass"] != want:
            raise AssertionError(f"synthetic kappa {kappa}: pass {f['pass']}, want {want} ({f['kappa']}, t {f['t']})")
        if kappa and abs(f["kappa"] - kappa) > 2 * f["se"] and abs(f["kappa_C"] - kappa) > 0.01:
            raise AssertionError(f"synthetic kappa 0.10 recovered as {f['kappa']} (se {f['se']})")
    zero = flow_fit(o.assign(Q_B=0.0, Q_G=0.0, S_win=noise))
    if zero["pass"] or zero["kappa"] != 0.0:
        raise AssertionError("the all-zero-Q known answer did not fail")
    try:
        audit_right_quantity(o.assign(S_win=noise, net=noise), {"kappa_B": 0.1})
        raise AssertionError("the right-quantity audit did not fire")
    except C0Error:
        pass
    print(f"selftest OK: sign, lag ({lag['rows']} rows), norm and right-quantity audits fire on breaks; synthetic "
          "kappa 0.10 passes and is recovered; kappa 0 and all-zero Q fail")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not SIGN.exists():
        raise SystemExit(f"{SIGN.name} is missing: run check_c0_sierra_sign.py for every root first (D635 s.7)")
    sign = json.loads(SIGN.read_text(encoding="utf-8"))
    if a.run:
        if OUT.exists():
            raise SystemExit(f"{OUT.name} exists: Gate C0 runs once")
        doc = build(sign)
        OUT.write_text(dump(doc), encoding="utf-8", newline="\n")
        v, f, p = doc["verdict"], doc["flow"], doc["price"]
        print(f"GATE C0: {v['verdict']}  ({f['mode']}: kappa {f['kappa']:.5f}, t {f['t']:.2f}; price slope "
              f"{p.get('slope')}, t {p.get('t_slope')})")
        return 0
    if a.check:
        if dump(build(sign)) != OUT.read_text(encoding="utf-8"):
            raise SystemExit("CHECK FAILED: the rebuild differs from gate_c0.json")
        print("check OK: byte for byte")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
