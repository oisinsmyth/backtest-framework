"""D756 Stage 0: mean-reverting days on the index micros (prop book), as pre-registered in
docs/decisions/D756-STAGE-0-PRE-REG-mean-reverting-days.md (68a96d74).

    uv run --no-sync python scripts/stage0_d756_reverting_days.py --selftest
    uv run --no-sync python scripts/stage0_d756_reverting_days.py --run      # once; writes data/stage0_d756_reverting_days.json

D727's RTH panels (ES, NQ, YM, RTY; 2016-02 -> 2023-12). Label RD: E = |C - O| / (H - L) in the bottom third of its
root-year. Prize: the 10:00 fade of the move since the open to 15:59 at one micro; Z and the break-even precision p*.
Seven pre-open predictors, walk-forward terciles (or binary), lift in the declared direction against the exact
shared-offset circular rotation of the predictor against the label; two-sided; Holm over seven. Classification only:
the fade's net per predictor cell is not computed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

DATA = REPO / "data"
SPEC = REPO / "docs" / "decisions" / "D756-STAGE-0-PRE-REG-mean-reverting-days.md"
OUT = DATA / "stage0_d756_reverting_days.json"
D727_OUT = DATA / "stage0_d727_trend_curve.json"
BREADTH = DATA / "fixtures" / "fut_breadth_hourly.csv.gz"
CAL = DATA / "fixtures" / "cme_session_calendar.csv.gz"
DIX = DATA / "raw" / "squeezemetrics" / "DIX.csv"
COSTS = DATA / "futures_costs.json"
SEAL = "2024-01-01"
ROOTS = ("ES", "NQ", "YM", "RTY")
MICRO = {"ES": "MES", "NQ": "MNQ", "YM": "MYM", "RTY": "M2K"}
KNOWN_DAYS = {"NQ": 1941, "YM": 1938, "RTY": 1557}
ON_SEGS = ["h18", "h19", "h20", "h21", "h22", "h23", "h00", "h01", "h02", "h03", "h04", "h05", "h06", "h07", "h08"]
WF, RANGE_N = 250, 20
J10 = 0                                         # D727's CLOCKS[0] = 30 minutes after 09:30 = 10:00
ALPHA, T_MIN, PRIZE_K = 0.05, 2.0, 3.0
# predictor: (kind, expected cell, opposite cell); tercile cells 0 bottom / 2 top; binary 0/1
PRED = {"P-a overnight range / mean range": ("terc", 0, 2), "P-b gap / sigma_oc": ("terc", 0, 2),
        "P-c previous E": ("terc", 0, 2), "P-d previous range / mean range": ("terc", 2, 0),
        "P-e volatility level": ("terc", 0, 2), "P-f event day": ("bin", 0, 1), "P-g GEX > 0": ("bin", 1, 0)}


class D756Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D756Error(msg)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ================================================================================ building blocks
def wf_tercile(x: np.ndarray, n: int = WF) -> np.ndarray:
    """Cell 0 / 1 / 2 against the thresholds of the previous n values (strictly before t); -1 where unknown."""
    s = pd.Series(x)
    q1 = s.shift(1).rolling(n, min_periods=n).quantile(1 / 3).to_numpy()
    q2 = s.shift(1).rolling(n, min_periods=n).quantile(2 / 3).to_numpy()
    cell = np.where(x <= q1, 0, np.where(x >= q2, 2, 1))
    return np.where(np.isfinite(x) & np.isfinite(q1) & np.isfinite(q2), cell, -1)


def wf_percentile(x: np.ndarray, n: int = WF) -> np.ndarray:
    return pd.Series(x).rolling(n + 1, min_periods=n + 1).apply(lambda w: (w[:-1] < w[-1]).mean(), raw=True).to_numpy()


def rd_label(E: np.ndarray, days: np.ndarray) -> np.ndarray:
    """RD = E in the bottom third of its calendar year (by rank; ties by order)."""
    rd = np.zeros(E.size, bool)
    yrs = np.array([d[:4] for d in days])
    for y in np.unique(yrs):
        idx = np.flatnonzero(yrs == y)
        order = idx[np.argsort(E[idx], kind="stable")]
        rd[order[: int(round(idx.size / 3))]] = True
    return rd


def lift(cells: dict, rd: dict, exp: int, opp: int, shift: int = 0) -> tuple[float, int, int, float]:
    """Pooled P(RD | expected) - P(RD | opposite) with each root's predictor rotated by shift mod its length."""
    ae = ne = ao = no = 0
    for r in cells:
        c = np.roll(cells[r], shift % cells[r].size)
        y = rd[r]
        me, mo = c == exp, c == opp
        ae += int(y[me].sum()); ne += int(me.sum()); ao += int(y[mo].sum()); no += int(mo.sum())
    pe = ae / ne if ne else float("nan")
    po = ao / no if no else float("nan")
    return pe - po, ne, no, pe


def lift_loop(cells, rd, exp, opp, shift):
    ae = ne = ao = no = 0
    for r in cells:
        n = cells[r].size
        for i in range(n):
            ci = cells[r][(i - shift) % n]
            if ci == exp:
                ne += 1; ae += int(rd[r][i])
            elif ci == opp:
                no += 1; ao += int(rd[r][i])
    return ae / ne - ao / no


def rotation(cells: dict, rd: dict, exp: int, opp: int) -> dict:
    K = max(c.size for c in cells.values())
    obs, ne, no, prec = lift(cells, rd, exp, opp)
    vals = np.array([lift(cells, rd, exp, opp, k)[0] for k in range(K)])
    need(vals[0] == obs, "rotation: offset 0 is not the observed")
    fin = vals[np.isfinite(vals)]
    return {"lift": obs, "precision_expected_cell": prec, "n_expected": ne, "n_opposite": no, "offsets": int(K),
            "p_two_sided": float(np.mean(np.abs(fin) >= abs(obs))), "null_p50": float(np.percentile(fin, 50)),
            "null_p95": float(np.percentile(fin, 95)), "null_p05": float(np.percentile(fin, 5)), "_vals": vals}


def holm(ps: dict) -> dict:
    order = sorted(ps, key=lambda k: ps[k])
    out, run = {}, 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, ps[k] * (len(ps) - i)))
        out[k] = run
    return out


def fade(O, P10, C, upp, cost) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    side = -np.sign(P10 - O)
    gross = side * (C - P10) * upp
    traded = side != 0
    return np.where(traded, gross, np.nan), np.where(traded, gross - cost, np.nan), side


def stats(x: np.ndarray) -> dict:
    x = x[np.isfinite(x)]
    n = x.size
    if n < 2:
        return {"n": int(n)}
    return {"n": int(n), "mean": float(x.mean()), "t": float(x.mean() / (x.std(ddof=1) / math.sqrt(n))),
            "median": float(np.median(x)), "win": float(np.mean(x > 0)), "mean_abs": float(np.mean(np.abs(x)))}


# ================================================================================ the data
def load_root_panel(T7, root: str) -> dict:
    pn = T7.load_root(root, DATA)
    ob = T7.objects(pn)
    days = np.asarray(pn["days"], str)
    raw = pn["raw"]
    mins = [T7.hhmm(m) for m in range(T7.NMIN)]
    Hm = raw.pivot(index="day", columns="hhmm", values="high").reindex(index=days, columns=mins).to_numpy(float)
    Lm = raw.pivot(index="day", columns="hhmm", values="low").reindex(index=days, columns=mins).to_numpy(float)
    con = raw.groupby("day")["contract"].agg(lambda s: s.value_counts().index[0]).reindex(days).to_numpy(str)
    Hd, Ld = np.nanmax(Hm, axis=1), np.nanmin(Lm, axis=1)
    O, C = pn["O"], ob["close"]
    Hd, Ld = np.maximum(Hd, np.maximum(O, C)), np.minimum(Ld, np.minimum(O, C))
    rng = Hd - Ld
    with np.errstate(invalid="ignore", divide="ignore"):
        E = np.abs(C - O) / rng
    return dict(root=root, days=days, O=O, C=C, H=Hd, L=Ld, rng=rng, E=E, soc=pn["soc"], P10=ob["Pt"][:, J10], con=con)


def overnight(roots, panels) -> dict:
    cols = ["root", "day", "contract"] + [f"{s}_{x}" for s in ON_SEGS for x in "hl"]
    b = pd.read_csv(BREADTH, usecols=cols, encoding="utf-8", dtype={"day": str, "contract": str})
    b = b[b["root"].isin(roots) & (b["day"] < SEAL)]
    need(b["day"].max() < SEAL, "the seal: a breadth row on or after 2024-01-01")
    hi = b[[f"{s}_h" for s in ON_SEGS]].to_numpy(float)
    lo = b[[f"{s}_l" for s in ON_SEGS]].to_numpy(float)
    with np.errstate(all="ignore"):
        b = b.assign(on_rng=np.nanmax(hi, axis=1) - np.nanmin(lo, axis=1))
    out = {}
    for r in roots:
        g = b[b["root"] == r].set_index("day")
        P = panels[r]
        v = g["on_rng"].reindex(P["days"]).to_numpy(float)
        ct = g["contract"].reindex(P["days"]).to_numpy(object)
        same = np.array([str(a) == str(c) for a, c in zip(ct, P["con"])])
        out[r] = dict(on_rng=np.where(same, v, np.nan), mismatch=int((~same).sum()))
    return out


def gex_prior(days: np.ndarray) -> np.ndarray:
    g = pd.read_csv(DIX, usecols=["date", "gex"], dtype={"date": str}, encoding="utf-8")
    g = g[g["date"] < SEAL].sort_values("date")
    need(g["date"].max() < SEAL, "the seal: a DIX row on or after 2024-01-01")
    dd = g["date"].to_numpy(str)
    vv = g["gex"].to_numpy(float)
    ix = np.searchsorted(dd, days, side="left") - 1                     # the last date strictly before t
    return np.where(ix >= 0, vv[np.clip(ix, 0, None)], np.nan)


def events(root: str, days: np.ndarray) -> np.ndarray:
    c = pd.read_csv(CAL, usecols=["root", "day", "fomc", "cpi", "empsit"], encoding="utf-8", dtype={"day": str})
    c = c[(c["root"] == root) & (c["day"] < SEAL)].set_index("day")
    f = c[["fomc", "cpi", "empsit"]].fillna(False).astype(bool).any(axis=1)
    return f.reindex(days).fillna(False).to_numpy(bool)


def predictors(P: dict, on: dict, gex: np.ndarray, ev: np.ndarray) -> dict:
    rng = P["rng"]
    mean_rng = pd.Series(rng).shift(1).rolling(RANGE_N, min_periods=RANGE_N).mean().to_numpy()
    prevC = np.r_[np.nan, P["C"][:-1]]
    with np.errstate(invalid="ignore", divide="ignore"):
        raw = {"P-a overnight range / mean range": on["on_rng"] / mean_rng,
               "P-b gap / sigma_oc": np.abs(P["O"] - prevC) / P["soc"],
               "P-c previous E": np.r_[np.nan, P["E"][:-1]],
               "P-d previous range / mean range": np.r_[np.nan, rng[:-1]] / mean_rng,
               "P-e volatility level": wf_percentile(P["soc"])}
    cells = {k: wf_tercile(v) for k, v in raw.items()}
    cells["P-f event day"] = ev.astype(int)
    cells["P-g GEX > 0"] = np.where(np.isfinite(gex), (gex > 0).astype(int), -1)
    return dict(raw=raw, cells=cells, mean_rng=mean_rng)


# ================================================================================ the run
def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: run-once")
    t0 = time.time()
    import stage0_d727_trend_curve as T7
    d727 = json.loads(D727_OUT.read_text(encoding="utf-8"))["roots"]
    costs = json.loads(COSTS.read_text(encoding="utf-8"))["roots"]
    PN = {r: load_root_panel(T7, r) for r in ROOTS}
    for r, n in KNOWN_DAYS.items():
        need(len(PN[r]["days"]) == n == d727[r]["days"], f"known answer: {r} {len(PN[r]['days'])} days")
    for r in ROOTS:
        need(max(PN[r]["days"]) < SEAL, f"the seal: {r}")
        E = PN[r]["E"]
        need(np.nanmin(E) >= 0 and np.nanmax(E) <= 1 + 1e-12, f"{r}: E outside [0, 1]")
    ON = overnight(ROOTS, PN)
    CELLS, RD, RAW, UNIT = {}, {}, {}, {}
    for r in ROOTS:
        P = PN[r]
        rd = rd_label(P["E"], P["days"])
        yrs = np.array([d[:4] for d in P["days"]])
        for y in np.unique(yrs):
            m = yrs == y
            need(abs(rd[m].mean() - 1 / 3) <= 1 / m.sum() + 1e-9, f"{r} {y}: RD share {rd[m].mean()}")
        pr = predictors(P, ON[r], gex_prior(P["days"]), events(r, P["days"]))
        CELLS[r], RD[r], RAW[r] = pr["cells"], rd, pr
        ce = costs[r]["micro"]
        UNIT[r] = dict(upp=float(ce["usd_per_point"]), cost=float(ce["commission_rt_usd"]["value"]
                       + ce["crossing_ticks_rt"][ce["default_line"]]["value"] * ce["tick_usd"]))

    # the lag audit: a second implementation from the raw arrays, with its canary
    rng_ = np.random.default_rng(756)
    canary = 0
    for _ in range(40):
        r = ROOTS[int(rng_.integers(0, 4))]
        P = PN[r]
        t = int(rng_.integers(RANGE_N + 2, P["days"].size))
        mr = float(np.mean(P["rng"][t - RANGE_N:t]))
        want = {"P-c previous E": P["E"][t - 1], "P-d previous range / mean range": P["rng"][t - 1] / mr,
                "P-b gap / sigma_oc": abs(P["O"][t] - P["C"][t - 1]) / P["soc"][t]}
        for k, v in want.items():
            got = RAW[r]["raw"][k][t]
            need((not np.isfinite(v) and not np.isfinite(got)) or math.isclose(got, v, rel_tol=1e-12), f"lag audit {r} {t} {k}: {got} vs {v}")
        if P["rng"][t] / mr != RAW[r]["raw"]["P-d previous range / mean range"][t]:
            canary += 1
    need(canary > 0, "the lag canary (day t's own range) never disagreed")

    # the prize
    rows = {}
    for r in ROOTS:
        P = PN[r]
        g, nt, side = fade(P["O"], P["P10"], P["C"], UNIT[r]["upp"], UNIT[r]["cost"])
        rows[r] = dict(net=nt, gross=g)
    net_rd = np.concatenate([rows[r]["net"][RD[r]] for r in ROOTS])
    net_no = np.concatenate([rows[r]["net"][~RD[r]] for r in ROOTS])
    cost_rd = np.concatenate([np.full(int(RD[r].sum()), UNIT[r]["cost"]) for r in ROOTS])
    s_rd, s_no = stats(net_rd), stats(net_no)
    s_all = stats(np.concatenate([rows[r]["net"] for r in ROOTS]))
    Z = bool(s_rd["mean"] > 0 and s_rd["t"] >= T_MIN and s_rd["mean_abs"] >= PRIZE_K * float(cost_rd.mean()))
    mu1, mu0 = s_rd["mean"], s_no["mean"]
    pstar = (-mu0 / (mu1 - mu0)) if (mu1 > 0 > mu0) else (0.0 if mu0 >= 0 else None)

    # the predictors
    res_p, ps = {}, {}
    for name, (kind, exp, opp) in PRED.items():
        cells = {r: CELLS[r][name] for r in ROOTS}
        rot = rotation(cells, RD, exp, opp)
        ks = list(range(0, rot["offsets"], max(1, rot["offsets"] // 50)))[:50]
        for k in ks:
            need(math.isclose(lift_loop(cells, RD, exp, opp, k), rot["_vals"][k], rel_tol=1e-12, abs_tol=1e-15),
                 f"{name}: rotation vector != loop at {k}")
        per_root = {}
        for r in ROOTS:
            c, y = cells[r], RD[r]
            per_root[r] = {f"cell_{v}": {"n": int((c == v).sum()), "rd_rate": float(y[c == v].mean()) if (c == v).any() else None}
                           for v in sorted(set(c.tolist()) - {-1})}
            per_root[r]["lift"] = lift({r: c}, {r: y}, exp, opp)[0]
        res_p[name] = {**{k: v for k, v in rot.items() if not k.startswith("_")}, "per_root": per_root,
                       "expected_cell": exp, "opposite_cell": opp}
        ps[name] = rot["p_two_sided"]
    ph = holm(ps)
    verdicts = {}
    for name in PRED:
        x = res_p[name]
        x["p_holm"] = ph[name]
        passes = ph[name] <= ALPHA and x["lift"] > 0
        if not passes:
            verdicts[name] = "NOT PREDICTABLE" if x["lift"] > 0 or ph[name] > ALPHA else "WRONG SIGN"
        elif pstar is not None and x["precision_expected_cell"] >= pstar:
            verdicts[name] = "PREDICTABLE AND WORTH IT"
        else:
            verdicts[name] = "RECOGNISABLE, NOT WORTH IT"
    if not Z:
        reading = "NO PRIZE"
    elif any(v == "PREDICTABLE AND WORTH IT" for v in verdicts.values()):
        reading = "PREDICTABLE AND WORTH IT: " + ", ".join(k for k, v in verdicts.items() if v == "PREDICTABLE AND WORTH IT")
    elif any(v == "RECOGNISABLE, NOT WORTH IT" for v in verdicts.values()):
        reading = "RECOGNISABLE, NOT WORTH IT: " + ", ".join(k for k, v in verdicts.items() if v == "RECOGNISABLE, NOT WORTH IT")
    else:
        reading = "NOT PREDICTABLE"

    res = {"record": "D756 (68a96d74)", "reading": reading, "Z_prize_holds": Z, "p_star": pstar,
           "prize": {"RD_days": s_rd, "other_days": s_no, "all_days": s_all, "mean_cost_on_RD": float(cost_rd.mean()),
                     "per_root": {r: {"RD": stats(rows[r]["net"][RD[r]]), "other": stats(rows[r]["net"][~RD[r]])} for r in ROOTS}},
           "predictors": res_p, "verdicts": verdicts,
           "sessions": {r: int(PN[r]["days"].size) for r in ROOTS},
           "windows": {r: [str(PN[r]["days"][0]), str(PN[r]["days"][-1])] for r in ROOTS},
           "overnight_contract_mismatch": {r: ON[r]["mismatch"] for r in ROOTS}, "units": UNIT,
           "runner_sha256": sha(Path(__file__).resolve()), "prereg_sha256": sha(SPEC), "wall_s": round(time.time() - t0, 1)}
    with open(OUT, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(_strip(res), fh, indent=1)
        fh.write("\n")
    show(res)
    return 0


def _strip(x: Any) -> Any:
    if isinstance(x, dict):
        return {str(k): _strip(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_strip(v) for v in x]
    if isinstance(x, (np.floating, float)):
        return None if not math.isfinite(float(x)) else float(x)
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def show(res: dict) -> None:
    p = res["prize"]
    print(f"[D756] {res['reading']}")
    print(f"  prize: RD {p['RD_days']}  other {p['other_days']}  all {p['all_days']}  Z {res['Z_prize_holds']}  p* {res['p_star']}")
    for k, v in res["predictors"].items():
        print(f"  {k:36s} lift {v['lift']:+.4f} prec {v['precision_expected_cell']:.3f} p {v['p_two_sided']:.4f} "
              f"holm {v['p_holm']:.4f} null p05/p50/p95 {v['null_p05']:+.4f}/{v['null_p50']:+.4f}/{v['null_p95']:+.4f} "
              f"-> {res['verdicts'][k]}  per-root {({r: round(x['lift'], 3) for r, x in v['per_root'].items()})}")
    print(f"  overnight contract mismatches {res['overnight_contract_mismatch']}; wall {res['wall_s']} s")


# ================================================================================ self-test
def selftest() -> int:
    fails = []
    rng = np.random.default_rng(7561)
    # the label: a third per year, E in [0, 1]
    days = np.array([f"{y}-{m:02d}-{d:02d}" for y in (2018, 2019) for m in range(1, 13) for d in (3, 10, 17, 24)])
    E = rng.random(days.size)
    rd = rd_label(E, days)
    for y in ("2018", "2019"):
        m = np.array([d[:4] == y for d in days])
        if abs(rd[m].mean() - 1 / 3) > 1 / m.sum():
            fails.append(f"label share {rd[m].mean()}")
    # walk-forward terciles use only the past
    x = rng.normal(size=600)
    c1 = wf_tercile(x)
    x2 = x.copy()
    x2[400:] += 100.0                                     # change the future
    if not np.array_equal(c1[:400], wf_tercile(x2)[:400]):
        fails.append("wf_tercile reads the future")
    # sign in money: a short fade after a rise pays when the close is below P10
    g, n_, s = fade(np.array([100.0]), np.array([105.0]), np.array([101.0]), 2.0, 4.0)
    if not (s[0] == -1 and math.isclose(g[0], 8.0) and math.isclose(n_[0], 4.0)):
        fails.append(f"sign in money: {g} {n_} {s}")
    # the rotation: offset 0, a planted predictor equal to the label, vector == loop
    lab = {"A": rng.random(700) < 1 / 3, "B": rng.random(500) < 1 / 3}
    planted = {k: np.where(v, 0, 2) for k, v in lab.items()}
    r = rotation(planted, lab, 0, 2)
    if not r["p_two_sided"] < 0.01:
        fails.append(f"planted predictor p {r['p_two_sided']}")
    noise = {k: rng.integers(-1, 3, v.size) for k, v in lab.items()}
    for k in range(0, 700, 37):
        if not math.isclose(lift(noise, lab, 0, 2, k)[0], lift_loop(noise, lab, 0, 2, k), rel_tol=1e-12, abs_tol=1e-15):
            fails.append("rotation vector != loop")
            break
    if holm({"a": 0.01, "b": 0.04}) != {"a": 0.02, "b": 0.04}:
        fails.append("holm")
    try:
        need(False, "x")
        fails.append("need() did not raise")
    except D756Error:
        pass
    for f in fails:
        print(f"[SELFTEST FAIL] {f}")
    print(f"[D756] selftest: {'FAIL' if fails else 'all passed'}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    return selftest() if a.selftest else run()


if __name__ == "__main__":
    sys.exit(main())
