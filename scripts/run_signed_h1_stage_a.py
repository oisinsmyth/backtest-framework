"""D629: the signed H1, Stage A of the settlement flow ledger on Sierra Chart's aggressor-signed window flow, over
the covered contracts only (the principal, 2026-09-26).

The specification is `docs/decisions/D629-PRE-REG-signed-h1-rebalance-and-aggressor-window-flow.md`, committed in
2b5406b before this file existed. Per root:

    S_t = α + β Q_t + γ r_t + Σ δ_k F_k,t + ε_t      (OLS, HC1)

  S_t  Sierra's Ask − Bid volume, 14:28:00–14:30:00 ET, summed over the covered held contracts C_t, minus its mean
       over t−20..t−1 on the same C_t (`ledger_power_signed_h1.abnormal`, as POWER built it);
  Q_t  q_est at τ* × the covered contracts' units share (signed);
  r_t  the held return to 14:28 (signed); F the calendar flags (D627's sets).
Gate (D629 §5–§6): β̂ > 0 and t ≥ 2 (Rubin's over A4's 50 paths on CL); the 11:50–12:20 placebo |t| < 2; the observed
t above the rotation null's p95 by more than 2 bootstrap SEs. NG takes the ladder as written; CL is underpowered, so a
CL miss is INCONCLUSIVE with its bound and a CL pass is not adopted on significance alone. Every verdict is
PROVISIONAL until the CL/NG check of Sierra's sign (after D626's read on 2026-10-10) keeps it or turns it VOID.

The estimation helpers (HC1, Rubin, the rotation, its p95 and SE, the lag audit) are D627's
(`run_h1a_stage_a.py`), and the dependent, the covered set and Q are POWER's (`ledger_power_signed_h1.py`).

    uv run python -W error::RuntimeWarning scripts/run_signed_h1_stage_a.py --selftest | --run | --check
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
SPEC = REPO / "docs" / "decisions" / "D629-PRE-REG-signed-h1-rebalance-and-aggressor-window-flow.md"
OUT = REPO / "data" / "ledger_signed_h1_stage_a.json"
DOWNLOADS = REPO / "data" / "sierra_ledger_download_record.json"
SC_DATA = Path(r"C:\SierraChart\Data")
ET = "America/New_York"
CUT, TRANSITION, SWITCH = "2025-03-01", ("2020-04-01", "2020-09-16"), "2020-09-17"
M_PATHS, MI_SEED = 50, 20260924
ROT_SEED = 629
PLAUSIBLE_BETA = 0.25
UNDERPOWERED = {"CL"}  # D629 §6, from POWER's class (deposit §9A.2)
FUNDS = {"CL": ("UCO", "SCO"), "NG": ("BOIL", "KOLD")}
REQUIRED_OUTPUTS = ("verdict", "n", "excluded", "coverage", "main", "placebo", "rotation", "readings", "beside")


class SignedH1Error(RuntimeError):
    pass


def _load(name: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


H = _load("run_h1a_stage_a")         # D627's estimation and audits
P = _load("ledger_power_signed_h1")  # POWER's dependent, coverage and Q
FLAGS = H.FLAGS


# ------------------------------------------------------------------ verdict
def verdict(root: str, beta: float, t: float, t_plc: float, t_est: float, p95: float, p95_se: float) -> str:
    if not (beta > 0 and t >= 2):
        return "INCONCLUSIVE (underpowered)" if root in UNDERPOWERED else "FAIL"
    if abs(t_plc) >= 2 or t_est <= p95:
        return "UNRESOLVED (control)"
    if t_est - p95 <= 2 * p95_se:
        return "UNRESOLVED (margin)"
    return "PASS (not adopted: underpowered)" if root in UNDERPOWERED else "PASS"


# ------------------------------------------------------------------ audits
def first_days_from_record() -> dict[str, str]:
    """The coverage audit's second source: the download record's first_utc, as an ET date."""
    rec = json.loads(DOWNLOADS.read_text(encoding="utf-8"))["contracts"]
    out = {}
    for sym, r in rec.items():
        if r.get("records", 0) > 0:
            et = pd.Timestamp(r["first_utc"], tz="UTC").tz_convert(ET)
            out[f"{sym[:2]}:20{sym[3:5]}-{'FGHJKMNQUVXZ'.index(sym[2]) + 1:02d}"] = et.strftime("%Y-%m-%d")
    return out


def audit_coverage(root: str, d: pd.DataFrame, days: list[str], first: dict[str, str]) -> None:
    """Re-derive C_t from the download record (not the panel summary) and require it to equal the design's."""
    pos = {x: i for i, x in enumerate(days)}
    for day, held, cov in zip(d["day"], d["held"], d["covered"]):
        i = pos[day]
        mine = [ym for ym in held.split(";") if i >= 20 and first.get(f"{root}:{ym}", "9999") < days[i - 20]]
        if cov.split(";") != mine:
            raise SignedH1Error(f"coverage audit: {root} {day} design {cov} != record {';'.join(mine)}")


def raw_net_win(sym: str, day: str) -> tuple[int, int, int]:
    """(volume, Ask − Bid, Ask + Bid) in 14:28:00–14:30:00 ET on `day`, straight from the Sierra file with pandas'
    clock arithmetic: a second implementation of the builder's integer arithmetic."""
    rec = np.dtype([("dt", "<i8"), ("o", "<f4"), ("h", "<f4"), ("l", "<f4"), ("c", "<f4"), ("n", "<u4"),
                    ("v", "<u4"), ("bv", "<u4"), ("av", "<u4")])
    lo = pd.Timestamp(f"{day} 14:28:00", tz=ET).tz_convert("UTC")
    hi = pd.Timestamp(f"{day} 14:30:00", tz=ET).tz_convert("UTC")
    origin = pd.Timestamp("1899-12-30", tz="UTC")
    a, b = (int((x - origin) / pd.Timedelta(microseconds=1)) for x in (lo, hi))
    mm = np.memmap(SC_DATA / f"{sym}-NYMEX.scid", dtype=rec, mode="r", offset=56)
    i, j = np.searchsorted(mm["dt"], [a, b])
    w = mm[i:j]
    av, bv = np.asarray(w["av"], np.int64), np.asarray(w["bv"], np.int64)
    return int(np.asarray(w["v"], np.int64).sum()), int((av - bv).sum()), int((av + bv).sum())


def audit_sign(panel: pd.DataFrame, sym: str, day: str) -> dict[str, Any]:
    """S's convention (+ = buyers = Ask volume) re-checked on one contract-day from the raw file."""
    row = panel[(panel["symbol"] == sym) & (panel["day"] == day)]
    if len(row) != 1:
        raise SignedH1Error(f"sign audit: no single panel row for {sym} {day}")
    v, net, sided = raw_net_win(sym, day)
    got = (int(row["v_win"].iloc[0]), int(row["net_win"].iloc[0]), int(row["sided_win"].iloc[0]))
    if got != (v, net, sided):
        raise SignedH1Error(f"sign audit: panel {got} != raw file {(v, net, sided)} for {sym} {day}")
    return {"symbol": sym, "day": day, "v": v, "ask_minus_bid": net, "ask_plus_bid": sided}


# ------------------------------------------------------------------ data
def build(root: str, read_dependent: bool) -> dict[str, Any]:
    flow, star = H.load_flow(root)  # runs D627's lag and sign audits on the predictor panel
    days = P.business_days(root)
    d = P.design(root)
    excluded: dict[str, list[str]] = {"no_tau_star": sorted(set(flow["day"]) - set(star["day"]))}
    if root == "CL":
        excluded["a1_transition"] = sorted(star.loc[star["day"].between(*TRANSITION), "day"])
    rest = set(star["day"]) - set(excluded.get("a1_transition", [])) - set(d["day"])
    excluded["no_covered_contract_or_missing_r"] = sorted(rest)
    extra = star.set_index("day")[[f"{k}_{s}" for s in ("long", "inverse") for k in
                                   ("navdate", "sigma_q", "f_pit", "f_lo", "f_hi")]]
    d = d.join(extra, on="day")
    audit_coverage(root, d, days, first_days_from_record())
    by_tau = {t: g.set_index("day") for t, g in flow.groupby("tau")}
    plc = P.design(root, "11:30").set_index("day")
    d["Q_plc"] = plc["Q"].reindex(d["day"]).to_numpy()
    d["r_plc"] = plc["r"].reindex(d["day"]).to_numpy()
    d["covered_plc"] = plc["covered"].reindex(d["day"]).to_numpy()
    d["plc_clean"] = (by_tau["11:30"]["n_stale"].reindex(d["day"]) == 0).to_numpy()
    d["Q_1410"] = P.design(root, "14:10").set_index("day")["Q"].reindex(d["day"]).to_numpy()
    for fl in FLAGS[root]:
        if fl not in d:
            raise SignedH1Error(f"flag {fl} missing from the design")
    out: dict[str, Any] = {"d": d, "excluded": excluded, "flow": flow, "days": days}
    if not read_dependent:
        return out
    piv = P.signed_pivots(root, "in", days)
    pos = {x: i for i, x in enumerate(days)}
    cols: dict[str, list[float]] = {k: [] for k in ("S", "S_raw", "S_plc", "S_pre", "A_unsigned", "sided_win",
                                                     "v_win", "S_top", "top_share")}
    con = pd.read_csv(P.CONTRACTS, encoding="utf-8")
    con = con[con["root"] == root].set_index(["day", "tau"])
    for day, tau, cov in zip(d["day"], d["tau"], d["covered"]):
        i, c = pos[day], cov.split(";")
        now, tr = P.abnormal(piv["net_win"], days, i, c)
        cols["S"].append(now - tr)
        cols["S_raw"].append(now)
        pn, pt = P.abnormal(piv["net_plc"], days, i, c)
        cols["S_plc"].append(pn - pt)
        rn, rt = P.abnormal(piv["net_pre"], days, i, c)
        cols["S_pre"].append(rn - rt)
        vn, vt = P.abnormal(piv["v_win"], days, i, c)
        cols["A_unsigned"].append(vn - vt)
        cols["v_win"].append(vn)
        cols["sided_win"].append(P.abnormal(piv["sided_win"], days, i, c)[0])
        legs = con.loc[(day, tau)]
        sh = {ym: s for ym, s in zip(legs["ym"], legs["units_share"]) if ym in c}
        top = max(sh, key=lambda k: sh[k])
        tn, tt = P.abnormal(piv["net_win"], days, i, [top])
        cols["S_top"].append(tn - tt)
        cols["top_share"].append(sh[top])
    for k, v in cols.items():
        d[k] = v
    panel = pd.read_csv(P.SIGNED, encoding="utf-8", usecols=["root", "symbol", "day", "v_win", "net_win", "sided_win"])
    panel = panel[(panel["root"] == root) & (panel["day"] < CUT)]
    first = d.iloc[0]
    sym = f"{root}{'FGHJKMNQUVXZ'[int(first['covered'].split(';')[0][5:7]) - 1]}{first['covered'].split(';')[0][2:4]}"
    out["sign_audit"] = audit_sign(panel, sym, first["day"])
    out["d"] = d
    return out


def design_matrix(d: pd.DataFrame, root: str, q: np.ndarray, r: str = "r", extra: list[np.ndarray] | None = None
                  ) -> np.ndarray:
    cols = [np.ones(len(d)), q, d[r].to_numpy(float)] + [d[fl].to_numpy(float) for fl in FLAGS[root]]
    return np.column_stack(cols + (extra or []))


def mi_paths(root: str, d: pd.DataFrame, rng: np.random.Generator) -> list[np.ndarray]:
    """A4 as D627 (one error per fund and segment, proven days never drawn), SIGNED, times the covered share."""
    seg = H.segments(root)
    share = d["share_cov"].to_numpy(float)
    paths = []
    for _ in range(M_PATHS):
        draws: dict[tuple[str, str, str], float] = {}
        q = np.zeros(len(d))
        for side, fund in zip(("long", "inverse"), FUNDS[root]):
            f = d[f"f_est_{side}"].to_numpy(float).copy()
            for i, (nd, s) in enumerate(zip(d[f"navdate_{side}"], d[f"sigma_q_{side}"].to_numpy(float))):
                if s > 0:
                    key = (fund, *seg[(fund, nd)])
                    if key not in draws:
                        draws[key] = float(rng.normal(0.0, s))
                    f[i] = min(max(f[i] + draws[key], 0.0), 1.0)
            q = q + f * d[f"q1_{side}"].to_numpy(float)
        paths.append(q * share)
    return paths


# ------------------------------------------------------------------ the analysis
def year_dummies(d: pd.DataFrame) -> list[np.ndarray]:
    y = d["day"].str[:4].to_numpy()
    return [(y == v).astype(float) for v in np.unique(y)[1:]]


def analyse(root: str, d: pd.DataFrame, excluded: dict[str, list[str]]) -> dict[str, Any]:
    y = d["S"].to_numpy(float)
    for other in ("S_plc", "S_raw", "A_unsigned"):
        if np.allclose(y, d[other].to_numpy(float)):
            raise SignedH1Error(f"right-quantity: S_t equals {other}")
    q = d["Q"].to_numpy(float)
    X = design_matrix(d, root, q)
    est = H.fit(y, X)
    bs, vs = [], []
    for qp in mi_paths(root, d, np.random.default_rng(MI_SEED)):
        b, v = H.hc1(y, design_matrix(d, root, qp))
        bs.append(b)
        vs.append(v)
    rubin = H.rubin(np.array(bs), np.array(vs))
    # D629 §5 (as D627): the gate reads Rubin's t on CL and the f_est HC1 t on NG; NG's Rubin is reported beside
    rub = rubin if root == "CL" else {"beta": est["beta"], "t": est["t_hc1"], "se": est["se_hc1"],
                                      "statistic": "f_est HC1", "rubin_beside": rubin}
    # C1: the time placebo, on days with a clean 11:30 row
    ok = d["plc_clean"] & d[["S_plc", "Q_plc", "r_plc"]].notna().all(axis=1)
    dp = d[ok].reset_index(drop=True)
    plc = H.fit(dp["S_plc"].to_numpy(float), design_matrix(dp, root, dp["Q_plc"].to_numpy(float), "r_plc"))
    # C2: the rotation null (A9.4), seed 629
    rr = np.random.default_rng(ROT_SEED)
    years = d["day"].str[:4].to_numpy()
    ts = H.rotation(y, X, years, rr)
    p50, p95, p95_se = H.p95_with_se(ts, rr)
    verd = verdict(root, rub["beta"], rub["t"], plc["t_hc1"], est["t_hc1"], p95, p95_se)
    readings = {}
    for rd in ("est", "pit", "lo", "hi"):
        qr = ((d[f"f_{rd}_long"] * d["q1_long"] + d[f"f_{rd}_inverse"] * d["q1_inverse"]) * d["share_cov"])
        readings[rd] = H.fit(y, design_matrix(d, root, qr.to_numpy(float)))
    beside: dict[str, Any] = {}
    yd = year_dummies(d)
    beside["year_fe"] = H.fit(y, design_matrix(d, root, q, extra=yd))
    beside["r_x_year"] = H.fit(y, design_matrix(d, root, q, extra=yd + [x * d["r"].to_numpy(float) for x in yd]))
    beside["signed_pre_window_control"] = H.fit(y, design_matrix(d, root, q, extra=[d["S_pre"].to_numpy(float)]))
    beside["largest_share_covered_contract"] = H.fit(d["S_top"].to_numpy(float),
                                                     design_matrix(d, root, q / d["share_cov"].to_numpy(float)
                                                                   * d["top_share"].to_numpy(float)))
    m1410 = d["Q_1410"].notna().to_numpy()
    beside["tau_fixed_14:10"] = H.fit(y[m1410], design_matrix(d[m1410], root, d.loc[m1410, "Q_1410"].to_numpy(float)))
    beside["by_year"] = {yv: H.fit(y[years == yv], X[years == yv]) for yv in np.unique(years)
                         if (years == yv).sum() > X.shape[1] + 10}
    if root == "CL":
        era_b = (d["day"] >= SWITCH).to_numpy()
        beside["era_a"] = H.fit(y[~era_b], X[~era_b])
        beside["era_b"] = H.fit(y[era_b], X[era_b])
    sig = (d["signal_day"] == 1).to_numpy()
    beside["signal_days"] = H.fit(y[sig], X[sig])
    beside["no_signal_days"] = H.fit(y[~sig], X[~sig])
    nroll = ((d["index_roll_close"] == 0) & (d["fund_roll"] == 0)).to_numpy()
    drop = [3 + FLAGS[root].index("index_roll_close"), 3 + FLAGS[root].index("fund_roll")]
    beside["without_roll_days"] = H.fit(y[nroll], np.delete(X, drop, axis=1)[nroll])
    full = (d["covered"] == d["held"]).to_numpy()
    if full.sum() > X.shape[1] + 10:
        beside["fully_covered_days"] = H.fit(y[full], X[full])
    se_rub = float(np.sqrt(rub["T"])) if root == "CL" else float(est["se_hc1"])
    beside["beta_against_plausible"] = {"beta": rub["beta"], "se": se_rub, "plausible": PLAUSIBLE_BETA,
                                        "upper_bound_beta_plus_2se": rub["beta"] + 2 * se_rub,
                                        "reading": "contracts of net aggressor buying in the window per contract of "
                                                   "predicted P1 in the covered contracts"}
    beside["newey_west_below_2"] = bool(est["t_nw5"] < 2)
    beside["descriptive"] = {
        "sided_share_of_window_volume": float(d["sided_win"].sum() / d["v_win"].sum()),
        "sign_agreement_S_Q": float(np.mean(np.sign(y) == np.sign(q))),
        "median_abs_S": float(np.median(np.abs(y))), "median_abs_Q": float(np.median(np.abs(q)))}
    cov = {"days": int(len(d)), "fully_covered_days": int(full.sum()),
           "share_cov_median": float(d["share_cov"].median()), "share_cov_mean": float(d["share_cov"].mean())}
    return {"verdict": verd, "provisional": "until the CL/NG check of Sierra's sign after 2026-10-10 (D629 §6)",
            "n": int(len(d)), "first": d["day"].iloc[0], "last": d["day"].iloc[-1],
            "excluded": {k: {"n": len(x), "days": x} for k, x in excluded.items()}, "coverage": cov,
            "main": {"gate": rub, "f_est": est}, "placebo": {**plc, "n_days": int(len(dp))},
            "rotation": {"p50": p50, "p95": p95, "p95_se": p95_se, "t_est": est["t_hc1"],
                         "beats": bool(est["t_hc1"] > p95), "margin": est["t_hc1"] - p95, "draws": len(ts)},
            "readings": readings, "beside": beside}


def run() -> dict[str, Any]:
    ins = (P.FLOW, P.CONTRACTS, P.SIGNED, P.SIGNED_SUM, P.CAL, P.PANEL, H.FSHARE, DOWNLOADS)
    out: dict[str, Any] = {"spec": {"record": SPEC.name, "sha256": hashlib.sha256(SPEC.read_bytes()).hexdigest()},
                           "inputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ins},
                           "cut": CUT, "deviations": [], "roots": {}}
    for root in ("CL", "NG"):
        b = build(root, read_dependent=True)
        r = analyse(root, b["d"], b["excluded"])
        r["sign_audit"] = b["sign_audit"]
        missing = [k for k in REQUIRED_OUTPUTS if k not in r]
        if missing:
            raise SignedH1Error(f"{root}: REQUIRED_OUTPUTS missing {missing}")
        out["roots"][root] = r
    return out


# ------------------------------------------------------------------ selftest (no in-sample signed row)
def selftest() -> int:
    assert verdict("NG", -0.1, 3.0, 0.0, 3.0, 1.5, 0.1) == "FAIL"
    assert verdict("CL", 0.3, 1.9, 0.0, 1.9, 1.5, 0.1) == "INCONCLUSIVE (underpowered)"
    assert verdict("NG", 0.3, 3.0, 2.5, 3.0, 1.5, 0.1) == "UNRESOLVED (control)"
    assert verdict("NG", 0.3, 3.0, 0.5, 1.4, 1.5, 0.1) == "UNRESOLVED (control)"
    assert verdict("NG", 0.3, 3.0, 0.5, 1.6, 1.5, 0.1) == "UNRESOLVED (margin)"
    assert verdict("NG", 0.3, 3.0, 0.5, 3.0, 1.5, 0.1) == "PASS"
    assert verdict("CL", 0.3, 3.0, 0.5, 3.0, 1.5, 0.1) == "PASS (not adopted: underpowered)"
    print("  verdict ladder: as D629 §6, NG and CL rows")
    # the raw-file recompute on a PRE-SAMPLE contract-day (NGN16, 2016-05-02) against the panel
    panel = pd.read_csv(P.SIGNED, encoding="utf-8", usecols=["root", "symbol", "day", "v_win", "net_win", "sided_win"])
    panel = panel[panel["day"] < P.FIRST_IN]
    if (panel["day"] >= P.FIRST_IN).any():
        raise SignedH1Error("an in-sample signed row is in memory in the selftest")
    audit_sign(panel, "NGN16", "2016-05-02")
    flipped = panel.assign(net_win=-panel["net_win"])
    try:
        audit_sign(flipped, "NGN16", "2016-05-02")
    except SignedH1Error:
        print("  sign audit: panel == raw file on a pre-sample day, and RAISES on a flipped sign")
    else:
        raise SignedH1Error("the sign audit did not fire on a flipped sign")
    for root in ("CL", "NG"):
        b = build(root, read_dependent=False)
        d = b["d"]
        # coverage audit: a contract that is held but not covered, let in, must raise
        first = first_days_from_record()
        audit_coverage(root, d, b["days"], first)
        bad = d.copy()
        k = int(np.flatnonzero((bad["covered"] != bad["held"]).to_numpy())[0]) if root == "CL" else 0
        bad.loc[k, "covered"] = bad.loc[k, "held"] if root == "CL" else bad.loc[k, "covered"] + ";2099-01"
        try:
            audit_coverage(root, bad, b["days"], first)
        except SignedH1Error:
            pass
        else:
            raise SignedH1Error(f"{root}: the coverage audit did not fire on an uncovered contract let in")
        print(f"  {root}: coverage audit agrees with the download record, and RAISES on an uncovered contract")
        # the lag and sign audits on the predictor panel, broken one input at a time
        base = b["flow"]
        breaks = {"a NAV dated its own day": lambda f: f.assign(navdate_long=f["day"].where(f.index == f.index[0],
                                                                                          f["navdate_long"])),
                  "q_est off q1 x f_est": lambda f: f.assign(q_est=f["q_est"] * 1.001),
                  "a flipped q1 sign": lambda f: f.assign(q1_inverse=-f["q1_inverse"])}
        for what, brk in breaks.items():
            try:
                H.audit_flow(brk(base.copy()))
            except H.H1aError:
                continue
            raise SignedH1Error(f"the audit did not fire on {what}")
        print(f"  {root}: D627's lag and sign audits RAISE on each of {len(breaks)} breaks")
        # injected effects on the real design with POWER's pre-sample noise
        ps = P.presample(root)
        rng = np.random.default_rng(7)
        V = d["V"].to_numpy(float)
        noise = lambda: V * P.P._block(ps["_resid"], len(d), rng)  # noqa: E731
        big = 3.0 if root in UNDERPOWERED else 0.5  # CL's power at 0.5 is 0.51 (POWER); 3.0 makes a pass near-certain
        res = {}
        for beta in (big, 0.0):
            syn = d.copy()
            syn["S"] = beta * syn["Q"].to_numpy(float) + noise()
            syn["S_raw"] = syn["S"] + 10 * V
            syn["S_plc"], syn["S_pre"], syn["A_unsigned"], syn["S_top"] = noise(), noise(), noise(), noise()
            syn["sided_win"], syn["v_win"], syn["top_share"] = V, V, syn["share_cov"]
            r = analyse(root, syn, b["excluded"])
            missing = [k for k in REQUIRED_OUTPUTS if k not in r]
            if missing:
                raise SignedH1Error(f"{root}: synthetic analyse is missing {missing}")
            res[beta] = r["verdict"]
        if not res[big].startswith("PASS") or res[0.0].startswith("PASS"):
            raise SignedH1Error(f"{root}: selftest verdicts {res}")
        print(f"  {root}: analyse() end to end on synthetic data: beta {big} -> {res[big]}; beta 0 -> {res[0.0]} "
              f"(n {len(d)})")
    print("selftest: every check passes on its known answer and raises on its break")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.run and OUT.exists():
        raise SignedH1Error(f"{OUT.name} exists: the signed H1 has been run once (D629). Use --check to recompute.")
    res = run()
    text = json.dumps(res, indent=1, sort_keys=True, default=float) + "\n"
    if a.check:
        if OUT.read_text(encoding="utf-8") != text:
            raise SignedH1Error(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    for root, r in res["roots"].items():
        m = r["main"]
        print(f"{root}: {r['verdict']}  n {r['n']}  gate beta {m['gate']['beta']:.4f} t {m['gate']['t']:.2f} | "
              f"f_est t {m['f_est']['t_hc1']:.2f} NW {m['f_est']['t_nw5']:.2f} | placebo t {r['placebo']['t_hc1']:.2f} | "
              f"rotation p50 {r['rotation']['p50']:.2f} p95 {r['rotation']['p95']:.2f} ± {r['rotation']['p95_se']:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
