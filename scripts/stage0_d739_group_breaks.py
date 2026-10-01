"""D739 Stage 0: does D735's mechanism transfer? A root's move that its group does not share, on metals, energy, rates,
FX and grains. Spec: docs/decisions/D739-STAGE-0-PRE-REG-does-breaking-from-the-group-transfer.md, committed before
this file existed.

    uv run --with pyarrow python scripts/stage0_d739_group_breaks.py --selftest
    uv run --with pyarrow python scripts/stage0_d739_group_breaks.py --run --data-root <checkout>/data      # once

D737's rule unchanged (k 1.0, a 1 sigma_rem stop, exit at the window's close), with the window length L and the trigger
window as parameters. D735's functions are used where they are already generic (rms_prior, align_rows, join_audit,
timing_null, g_at, stopped_at, rot, holm, xbin, fw_delta, fw_null, per_clock_fit); the L-parameterised versions here are
proven equal to D735's at L = 390 in the self-test. fut_day1m bar b = minute 09:00 + b ET. Nothing dated 2024-01-01 or
later is read.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d720_size_the_direction as Z  # noqa: E402
import stage0_d731_flat_u as F  # noqa: E402
import stage0_d733_pullback_entry as B  # noqa: E402
import stage0_d735_nq_breaks_from_the_market as S  # noqa: E402

OUT = REPO / "data" / "stage0_d739_group_breaks.json"
LO, HI = "2016-01-04", "2023-12-29"
# group: (roots, first fixture bar of the window, L)
GROUPS = {"METALS": (("GC", "SI", "HG", "PL", "PA"), 0, 240),
          "ENERGY": (("CL", "BZ", "HO", "RB"), 0, 330),
          "RATES": (("ZT", "ZF", "ZN", "TN", "ZB", "UB"), 0, 360),
          "FX": (("6A", "6B", "6C", "6E", "6J", "6S"), 0, 360),
          "GRAINS": (("ZC", "ZW", "ZS", "ZM", "ZL"), 30, 290)}
MICROS = ("GC", "SI", "HG", "CL", "6E")
K, STOP_MULT, MLO, TAIL, MIN_SHARE = 1.0, 1.0, 30, 90, 0.90
NBOOT, SEED = 2000, 739
EDGE = S.EDGE
P = Z.P


class D739Error(AssertionError):
    pass


# ================================================================================ L-parameterised versions of D735's
def minute_x(C: np.ndarray, O: np.ndarray, soc: np.ndarray) -> np.ndarray:
    L = C.shape[1]
    X = np.zeros((len(C), L + 1))
    with np.errstate(invalid="ignore", divide="ignore"):
        X[:, 1:] = (C - O[:, None]) / soc[:, None]
    return X


def spread(X: np.ndarray, XL: np.ndarray, L: int) -> dict[str, np.ndarray]:
    Sp = X - XL
    sig = S.rms_prior(Sp[:, L])
    mm = np.arange(L + 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        Zs = Sp / (sig[:, None] * np.sqrt(np.maximum(mm, 1) / L)[None, :])
    return {"S": Sp, "sig": sig, "Z": Zs}


def trigger(Zs: np.ndarray, Sp: np.ndarray, k: float, mlo: int, mhi: int) -> tuple[np.ndarray, np.ndarray]:
    seg = Zs[:, mlo:mhi + 1]
    hit = np.isfinite(seg) & (np.abs(seg) >= k)
    first = np.where(hit.any(axis=1), hit.argmax(axis=1), -1)
    m0 = np.where(first >= 0, first + mlo, -1)
    rows = np.arange(len(Zs))
    D = np.where(m0 >= 0, np.sign(Sp[rows, np.clip(m0, 0, None)]), 0.0)
    return np.where(D != 0, m0, -1), D


def e1_tables(pp: dict[str, np.ndarray], mult: float, mlo: int, mhi: int, tick: float, usd: float) -> dict[str, np.ndarray]:
    Op, H, Lw, C, soc = pp["Op"], pp["H"], pp["L"], pp["C"], pp["soc"]
    n, L = Op.shape
    out = {k: np.full((n, L), np.nan) for k in ("up", "dn")}
    stp = {k: np.zeros((n, L), bool) for k in ("up", "dn")}
    last = C[:, L - 1]
    for m in range(mlo, mhi + 1):
        entry = Op[:, m]
        if not math.isfinite(mult):
            out["up"][:, m] = (last - entry) * usd
            out["dn"][:, m] = (entry - last) * usd
            continue
        dist = mult * soc * math.sqrt((L - m) / L)
        op_, lo_, hi_ = Op[:, m:], Lw[:, m:], H[:, m:]
        stop = entry - dist
        hit = lo_ <= stop[:, None]
        anyh = hit.any(axis=1)
        opf = op_[np.arange(n), hit.argmax(axis=1)]
        ex = np.where(anyh, np.where(opf <= stop, opf - tick, stop - tick), last)
        out["up"][:, m] = (ex - entry) * usd
        stp["up"][:, m] = anyh
        stop = entry + dist
        hit = hi_ >= stop[:, None]
        anyh = hit.any(axis=1)
        opf = op_[np.arange(n), hit.argmax(axis=1)]
        ex = np.where(anyh, np.where(opf >= stop, opf + tick, stop + tick), last)
        out["dn"][:, m] = (entry - ex) * usd
        stp["dn"][:, m] = anyh
    return {"up": out["up"], "dn": out["dn"], "stop_up": stp["up"], "stop_dn": stp["dn"]}


def clocks_for(L: int) -> list[int]:
    return list(range(30, L - 29, 30))


def fw_design(X: np.ndarray, XL: np.ndarray, L: int, clocks: list[int] | None = None) -> dict[str, Any]:
    cl = clocks_for(L) if clocks is None else list(clocks)
    x = np.column_stack([X[:, m] for m in cl])
    y = X[:, [L]] - x
    xl = np.column_stack([XL[:, m] for m in cl])
    e = np.full_like(xl, np.nan)
    coef = []
    for j in range(len(cl)):
        ok = np.isfinite(x[:, j]) & np.isfinite(xl[:, j]) & np.isfinite(y[:, j])
        A = np.column_stack([np.ones(ok.sum()), x[ok, j]])
        c = np.linalg.lstsq(A, xl[ok, j], rcond=None)[0]
        e[ok, j] = xl[ok, j] - A @ c
        coef.append((float(c[0]), float(c[1])))
    return {"x": x, "y": y, "e": e, "gamma": coef, "clocks": cl}


def matched_rows(G: dict[str, np.ndarray], X: np.ndarray, d: np.ndarray, m0: np.ndarray, gtr: np.ndarray, cost: float,
                 mlo: int, mhi: int, rng: np.random.Generator) -> dict[str, Any]:
    n = X.shape[0]
    nh = mhi // 60 + 1
    nb = nh * len(S.XBINS)
    Rs, Rc = np.zeros((n, nb)), np.zeros((n, nb))
    for m in range(mlo, mhi + 1, 5):
        x = X[:, m]
        Dd = np.sign(x)
        g = np.where(Dd > 0, G["up"][:, m], np.where(Dd < 0, G["dn"][:, m], np.nan))
        ok = np.isfinite(g) & np.isfinite(x) & (Dd != 0)
        c = (m // 60) * len(S.XBINS) + S.xbin(x)
        rr = np.flatnonzero(ok)
        np.add.at(Rs, (rr, c[ok]), g[ok] - cost)
        np.add.at(Rc, (rr, c[ok]), 1.0)
    Ts, Tc = np.zeros((n, nb)), np.zeros((n, nb))
    ct = (m0 // 60) * len(S.XBINS) + S.xbin(X[d, m0])
    np.add.at(Ts, (d, ct), gtr - cost)
    np.add.at(Tc, (d, ct), 1.0)

    def gain(ts, tc, rs, rc):
        ok = (tc > 0) & (rc > 0)
        return float((tc[ok] * (ts[ok] / tc[ok] - rs[ok] / rc[ok])).sum() / tc[ok].sum()) if ok.any() else float("nan")

    obs = gain(Ts.sum(0), Tc.sum(0), Rs.sum(0), Rc.sum(0))
    W = rng.multinomial(n, np.full(n, 1.0 / n), size=NBOOT).astype(float)
    A = [W @ M for M in (Ts, Tc, Rs, Rc)]
    bt = np.array([gain(A[0][i], A[1][i], A[2][i], A[3][i]) for i in range(NBOOT)])
    se = float(np.nanstd(bt, ddof=1))
    return {"gain": obs, "se": se, "t": obs / se if se > 0 else float("nan"), "rows": int(Rc.sum()), "trades": int(Tc.sum())}


# ================================================================================ data
def cost_line(root: str) -> dict[str, Any]:
    j = json.loads((REPO / "data" / "futures_costs.json").read_text(encoding="utf-8"))["roots"][root]
    size = "micro" if "micro" in j else "full"
    e = j[size]
    cr = e["crossing_ticks_rt"]
    line = "d508_exec" if "d508_exec" in cr else "d556_one_tick"
    rt = float(e["commission_rt_usd"]["value"]) + float(cr[line]["value"]) * float(e["tick_usd"])
    return {"symbol": e["symbol"], "size": size, "usd_per_point": float(e["usd_per_point"]), "tick": float(e["tick_points"]),
            "tick_usd": float(e["tick_usd"]), "crossing_line": line, "round_trip_usd": rt}


def load_group(data_root: Path, roots: tuple[str, ...]) -> pd.DataFrame:
    import pyarrow.parquet as pq
    t = pq.read_table(data_root / "fixtures" / "fut_day1m.parquet",
                      filters=[("root", "in", list(roots)), ("day", ">=", LO), ("day", "<=", HI)],
                      columns=["root", "day", "bar", "open", "high", "low", "close", "same_front", "present"])
    d = t.to_pandas()
    if len(d) and str(d["day"].max()) > HI:
        raise D739Error("seal: a row after 2023-12-29 was read")
    Z.no_session_after(d["day"].unique(), "fut_day1m")
    return d


def root_panel(raw: pd.DataFrame, root: str, a: int, L: int) -> dict[str, Any]:
    x = raw[raw["root"] == root]
    flags = x.groupby("day").agg(sf=("same_front", "all"), pr=("present", "all"))
    w = x[(x["bar"] >= a) & (x["bar"] < a + L)]
    cnt = w.groupby("day")["close"].count()
    good = flags.index[flags["sf"] & flags["pr"]]
    good = np.array(sorted(set(good) & set(cnt.index[cnt >= MIN_SHARE * L])))
    w = w[w["day"].isin(good)]
    piv = {c: w.pivot(index="day", columns="bar", values=c).reindex(index=good, columns=range(a, a + L)).to_numpy(float)
           for c in ("open", "high", "low", "close")}
    Cp = piv["close"]
    C = pd.DataFrame(Cp).ffill(axis=1).bfill(axis=1).to_numpy(float)
    prevc = np.column_stack([C[:, 0], C[:, :-1]])
    Op = np.where(np.isfinite(piv["open"]), piv["open"], prevc)
    H = np.where(np.isfinite(piv["high"]), piv["high"], np.maximum(Op, C))
    Lw = np.where(np.isfinite(piv["low"]), piv["low"], np.minimum(Op, C))
    O = Op[:, 0]
    oc = C[:, -1] - O
    soc = np.sqrt(pd.Series(oc * oc).shift(1).rolling(20, min_periods=20).mean().to_numpy(float))
    keep = np.isfinite(soc) & (soc > 0)
    return {"root": root, "days": good[keep], "Op": Op[keep], "H": H[keep], "L": Lw[keep], "C": C[keep], "O": O[keep],
            "soc": soc[keep], "all_days": good, "all_O": O, "all_last": C[:, -1], "raw": w}


# ================================================================================ one root
def score_root(ctx: dict[str, Any], g: str, root: str) -> dict[str, Any]:
    roots, a, L = GROUPS[g]
    mhi = L - TAIL
    pn = ctx["panels"][root]
    days, n = pn["days"], len(pn["days"])
    cl = cost_line(root)
    cost, usd = cl["round_trip_usd"], cl["usd_per_point"]
    X = minute_x(pn["C"], pn["O"], pn["soc"])
    legs = []
    for q in roots:
        if q == root:
            continue
        pq = ctx["panels"][q]
        Xq = minute_x(pq["C"], pq["O"], pq["soc"])
        al = S.align_rows(pq["days"], Xq, days)
        js = [int(v) for v in np.random.default_rng(SEED).integers(0, n, 40)]
        S.join_audit(pq["days"], Xq, days, al, js)
        try:
            S.join_audit(pq["days"], Xq, np.roll(days, 1), al, js)
        except S.D735Error:
            pass
        else:
            raise D739Error(f"{root}/{q}: a shifted join did not fire")
        legs.append(al)
    XL = np.mean(legs, axis=0)                                   # NaN where any member is missing
    sp = spread(X, XL, L)
    m0, D = trigger(sp["Z"], sp["S"], K, MLO, mhi)
    pp = {"Op": pn["Op"], "H": pn["H"], "L": pn["L"], "C": pn["C"], "soc": pn["soc"]}
    G = e1_tables(pp, STOP_MULT, MLO, mhi, cl["tick"], usd)
    d = np.flatnonzero(m0 >= 0)
    m0d, Dd = m0[d], D[d]
    gr = S.g_at(G, d, m0d, Dd)
    if not np.isfinite(gr).all():
        raise D739Error(f"{root}: a trade has no E1 value")
    # lag audit: a second implementation from the raw rows (bars <= m0 - 1), with a one-bar-lead canary
    rng = np.random.default_rng(SEED)
    smp = rng.choice(d, min(40, len(d)), replace=False) if len(d) else []
    fired = False
    for dd in smp:
        day = days[dd]

        def xs(q: str, lead: int) -> np.ndarray:
            pq = ctx["panels"][q]
            i = int(np.flatnonzero(pq["days"] == day)[0])
            r = pq["raw"][pq["raw"]["day"] == day].set_index("bar")["close"].reindex(range(a, a + L))
            c = r.ffill().bfill().to_numpy(float)
            return (c - pq["O"][i]) / pq["soc"][i]
        xr = xs(root, 0)
        xg = np.mean([xs(q, 0) for q in roots if q != root], axis=0)
        prev = [sp["S"][qq, L] for qq in range(max(0, dd - 20), dd)]
        prev = [v for v in prev if math.isfinite(v)]
        sig = math.sqrt(sum(v * v for v in prev) / len(prev)) if len(prev) >= 15 else float("nan")
        if not math.isclose(sig, sp["sig"][dd], rel_tol=1e-9):
            raise D739Error(f"lag: {root} sigma_s at {day} is not the prior 20 days'")
        for lead in (0, 1):
            mm, DD = -1, 0.0
            for m in range(MLO, mhi + 1):
                b = min(m - 1 + lead, L - 1)
                s = xr[b] - xg[b]
                z = s / (sig * math.sqrt(m / L))
                if math.isfinite(z) and abs(z) >= K and s != 0:
                    mm, DD = m, float(np.sign(s))
                    break
            if lead == 0 and (mm != m0[dd] or DD != D[dd]):
                raise D739Error(f"lag: {root} at {day}: second implementation {mm}/{DD}, runner {m0[dd]}/{D[dd]}")
            if lead == 1 and (mm != m0[dd] or DD != D[dd]):
                fired = True
    if len(d) and not fired:
        raise D739Error(f"{root}: the one-bar-lead canary did not fire")
    net = gr - cost
    gfull = np.full(n, np.nan)
    gfull[d] = gr
    bk, daily = F.book(np.where(np.isfinite(gfull), 1.0, 0.0), gfull, cost, days)
    offs = np.arange(EDGE, n - EDGE)
    c2a = S.timing_null(G, d, m0d, X, X, cost, offs)
    c2b0 = S.timing_null(G, d, m0d, sp["S"], X, cost, np.array([0]))
    if len(d) and not math.isclose(float(c2b0["mean_net"][0]), float(net.mean()), rel_tol=0, abs_tol=1e-9):
        raise D739Error(f"{root}: C2b's offset 0 does not reproduce the trades")
    c2b = S.timing_null(G, d, m0d, sp["S"], X, cost, offs)
    eff = float(gr.sum() / np.abs(gr).sum()) if len(d) else float("nan")
    # mechanism
    fw = fw_design(X, XL, L)
    dl, bt, tcl = S.fw_delta(fw["x"], fw["y"], fw["e"], cluster_t=True)
    null = S.fw_null(fw["x"], fw["y"], fw["e"])
    if not math.isclose(S.fw_delta(fw["x"], fw["y"], np.roll(fw["e"], 0, axis=0)), dl, rel_tol=0, abs_tol=1e-12):
        raise D739Error(f"{root}: the FW null's offset 0 is not delta-hat")
    fits = S.per_clock_fit(fw["x"], fw["y"], fw["e"])
    clk = np.array(fw["clocks"])
    j = np.array([int(np.argmin(np.abs(clk - m))) for m in m0d], int)
    x0, xl0 = X[d, m0d], XL[d, m0d]
    gam = fw["gamma"]
    e0 = xl0 - (np.array([gam[i][0] for i in j]) + np.array([gam[i][1] for i in j]) * x0)
    o1 = Dd * (np.array([fits[i][0] for i in j]) * x0 + np.array([fits[i][1] for i in j]) * e0) * pn["soc"][d] * usd
    beta_own = []
    for jj in range(len(clk)):
        ok = np.isfinite(fw["x"][:, jj]) & np.isfinite(fw["y"][:, jj])
        xc = fw["x"][ok, jj] - fw["x"][ok, jj].mean()
        beta_own.append(float((xc * (fw["y"][ok, jj] - fw["y"][ok, jj].mean())).sum() / (xc * xc).sum()))
    o2 = Dd * np.array(beta_own)[j] * x0 * pn["soc"][d] * usd
    aligned = np.sign(x0) == Dd
    ctr = ~aligned
    fol = S.g_at(G, d[ctr], m0d[ctr], np.sign(x0[ctr]))
    fol = np.where(np.isfinite(fol), fol, 0.0)
    pair = gr[ctr] - fol
    mr = matched_rows(G, X, d, m0d, gr, cost, MLO, mhi, np.random.default_rng(SEED)) if len(d) else None
    from backtest_framework.validation.concentration import year_concentration
    yc = year_concentration(days[d].astype(str), net, scale=pn["soc"][d] * usd) if len(d) else None
    yrs = pd.Series(bk["net_by_year"])
    ex2 = float(yrs.sort_values().iloc[:-2].sum()) if len(yrs) > 2 else float("nan")
    bins = {}
    xb = S.xbin(x0)
    for b in range(len(S.XBINS)):
        mb = xb == b
        bins[b] = {"trades": int(mb.sum()), "mean_net": float(net[mb].mean()) if mb.any() else None}
    res = {"group": g, "root": root, "contract": cl, "days": int(n), "leg_days": int(np.isfinite(XL[:, MLO]).sum()),
           "trades": int(len(d)), "in_market_share": float(len(d) / n), "mean_net": float(net.mean()) if len(d) else None,
           "mean_gross": float(gr.mean()) if len(d) else None, "gross_over_cost": float(gr.mean() / cost) if len(d) else None,
           "nw_t_net": B.nw_t(net) if len(d) >= 10 else None, "efficiency_gross": eff, "book": bk,
           "C2a_mean": S.rot(float(net.mean()), c2a["mean_net"]), "C2a_eff": S.rot(eff, c2a["eff"]),
           "C2b_mean": S.rot(float(net.mean()), c2b["mean_net"]), "by_abs_x": bins,
           "S1": {"delta": dl, "beta": bt, "t_clustered": tcl, "rotation": S.rot(dl, null),
                  "delta_by_clock": [{"m": int(c), "beta": f[0], "delta": f[1]} for c, f in zip(clk, fits)]},
           "O1_room_gross": float(o1.mean()) if len(d) else None, "O2_drift_budget_gross": float(o2.mean()) if len(d) else None,
           "aligned": {"trades": int(aligned.sum()), "mean_net": float(net[aligned].mean()) if aligned.any() else None},
           "counter": {"trades": int(ctr.sum()), "mean_gross": float(gr[ctr].mean()) if ctr.any() else None,
                       "C1_paired_mean": float(pair.mean()) if len(pair) else None,
                       "C1_paired_t": float(pair.mean() / (pair.std(ddof=1) / math.sqrt(len(pair)))) if len(pair) > 2 else None},
           "mirror_mean_net": float((S.g_at(G, d, m0d, -Dd) - cost).mean()) if len(d) else None,
           "matched_rows": mr, "stopped_share": float(S.stopped_at(G, d, m0d, Dd).mean()) if len(d) else None,
           "year_concentration": None if yc is None else {"label": yc["label"], "max_share_usd": yc["gross"]["max_share"],
                                                          "max_share_vol": yc["vol_units"]["max_share"]},
           "net_ex_two_best_years": ex2, "years_positive": bk["years_positive"],
           "entry_window_hour_counts": {str(k_): int(v) for k_, v in pd.Series(m0d // 60).value_counts().sort_index().items()},
           "_daily": pd.Series(daily, index=days), "_null": c2a["mean_net"]}
    return res


def readings(r: dict[str, Any], mech: bool, fam_p95: float) -> None:
    cost = r["contract"]["round_trip_usd"]
    room = (r["O1_room_gross"] or -1e9) >= 2 * cost
    mr = r["matched_rows"] or {"gain": float("nan"), "t": float("nan")}
    ctr_ok = r["counter"]["trades"] < 30 or (r["counter"]["mean_gross"] or 0) >= 0
    tr = (mech and room and (r["mean_net"] or -1) > 0 and (r["nw_t_net"] or 0) >= 2
          and r["C2a_mean"]["observed"] > r["C2a_mean"]["p95"] and r["C2a_eff"]["observed"] > r["C2a_eff"]["p95"]
          and mr["gain"] >= cost and (mr["t"] or 0) >= 2 and ctr_ok)
    yc = r["year_concentration"] or {}
    go = (tr and r["C2a_mean"]["observed"] > fam_p95 and r["root"] in MICROS and r["book"]["net_sharpe"] >= 0.4
          and r["years_positive"] >= 5 and (yc.get("max_share_usd") or 1) < 0.5 and (yc.get("max_share_vol") or 1) < 0.5
          and (r["net_ex_two_best_years"] or -1) > 0)
    rd = "TRANSFERS" if tr else ("DRIFT ONLY" if (r["mean_net"] or -1) > 0 else "NOTHING")
    r["NO_ROOM"] = bool(not room)
    r["MECHANISM"] = bool(mech)
    r["reading"] = ("NO ROOM; " if not room else "") + rd
    r["GO"] = bool(go)


# ================================================================================ the run
def run(data_root: Path) -> int:
    t0 = time.time()
    panels: dict[str, Any] = {}
    for g, (roots, a, L) in GROUPS.items():
        raw = load_group(data_root, roots)
        for r in roots:
            panels[r] = root_panel(raw, r, a, L)
        P(f"[D739] {g}: days { {r: len(panels[r]['days']) for r in roots} }")
    ctx = {"panels": panels}
    jobs = [(g, r) for g, (roots, _, _) in GROUPS.items() for r in roots]
    with ThreadPoolExecutor(max_workers=6) as ex:
        res = dict(zip([r for _, r in jobs], ex.map(lambda a_: score_root(ctx, *a_), jobs)))
    P("[D739] roots scored; nulls ...")
    hp = holm({r: v["S1"]["rotation"]["p_low"] for r, v in res.items()})
    mech = {r: bool(v["S1"]["delta"] < 0 and v["S1"]["rotation"]["p_low"] <= 0.05 and v["S1"]["t_clustered"] <= -2
                    and hp[r] <= 0.05) for r, v in res.items()}
    nmin = min(len(v["_null"]) for v in res.values())
    fam = np.nanmax(np.column_stack([v["_null"][:nmin] for v in res.values()]), axis=1)
    fam_p95 = float(np.nanquantile(fam, 0.95))
    hc = holm({r: v["C2a_mean"]["p_high"] for r, v in res.items()})
    for r, v in res.items():
        v["S1"]["holm_p_low"] = hp[r]
        v["C2a_holm_p"] = hc[r]
        readings(v, mech[r], fam_p95)
    # the component line: daily rho with NQ F2 and D735's YM k1.0 (by date)
    f2_, _ = Z.build_f2()
    f2_d = f2_.groupby("day")["net1"].sum()
    import vault_d737_nq_leads_the_dow as V
    c37 = V.in_sample(data_root)
    cst37 = V.cost()
    ym_d = pd.Series(c37["g"] - cst37, index=c37["days"][c37["d"]])
    for r, v in res.items():
        dly = v.pop("_daily")
        v.pop("_null")
        cal = dly.index.union(f2_d.index).union(ym_d.index)
        a_ = dly.reindex(cal).fillna(0.0)
        v["rho_nq_f2"] = float(np.corrcoef(a_, f2_d.reindex(cal).fillna(0.0))[0, 1])
        v["rho_d737_ym"] = float(np.corrcoef(a_, ym_d.reindex(cal).fillna(0.0))[0, 1])
    groups = {g: {"roots": list(roots), "mechanism": [r for r in roots if res[r]["MECHANISM"]],
                  "transfers": [r for r in roots if res[r]["reading"].endswith("TRANSFERS")],
                  "go": [r for r in roots if res[r]["GO"]],
                  "delta_signs_negative": int(sum(res[r]["S1"]["delta"] < 0 for r in roots))}
              for g, (roots, _, _) in GROUPS.items()}
    any_mech = any(mech.values())
    out = {"spec": "D739-STAGE-0-PRE-REG-does-breaking-from-the-group-transfer.md", "seal": f"nothing after {HI}",
           "family_p95": fam_p95, "groups": groups, "roots": res, "MECHANISM_anywhere": bool(any_mech),
           "GO_roots": [r for r in res if res[r]["GO"]],
           "close_proposed": bool(not any_mech), "wall_min": (time.time() - t0) / 60}
    OUT.write_text(json.dumps(out, indent=1, default=Z._json) + "\n", encoding="utf-8", newline="\n")
    P(f"[D739] mechanism: { {g: v['mechanism'] for g, v in groups.items()} }; transfers "
      f"{ {g: v['transfers'] for g, v in groups.items()} }; GO {out['GO_roots']}; {out['wall_min']:.1f} min")
    return 0


def holm(ps: dict[str, float]) -> dict[str, float]:
    return S.holm(ps)


# ================================================================================ self-test (synthetic only)
def selftest() -> int:
    fails: list[str] = []
    rng = np.random.default_rng(5)
    nd, L = 60, S.NMIN
    C = 100 + np.cumsum(rng.normal(0, 0.3, (nd, L)), axis=1)
    Op = np.column_stack([C[:, 0], C[:, :-1]])
    pp = {"Op": Op, "H": np.maximum(Op, C) + 0.25, "L": np.minimum(Op, C) - 0.25, "C": C, "O": Op[:, 0].copy(),
          "soc": np.abs(rng.normal(3, 0.5, nd))}
    # 1) the L-parameterised functions equal D735's at L = 390, trigger window 30..300, tick 0.25, $2
    for mult in (1.0, math.inf):
        a = e1_tables(pp, mult, S.M_LO, S.M_HI, S.TICK, S.USD)
        b = S.e1_tables(pp, mult)
        for k in ("up", "dn", "stop_up", "stop_dn"):
            if not np.array_equal(np.nan_to_num(a[k], nan=-7.0), np.nan_to_num(b[k], nan=-7.0)):
                fails.append(f"e1_tables {k} (mult {mult}) differs from D735's")
    X = minute_x(C, pp["O"], pp["soc"])
    if not np.array_equal(X, S.minute_x(C, pp["O"], pp["soc"])):
        fails.append("minute_x differs from D735's")
    C2 = 100 + np.cumsum(rng.normal(0, 0.3, (nd, L)), axis=1)
    XL = minute_x(C2, C2[:, 0], np.full(nd, 3.0))
    s1, s2 = spread(X, XL, L), S.spread(X, XL)
    if not all(np.array_equal(np.nan_to_num(s1[k], nan=-7.0), np.nan_to_num(s2[k], nan=-7.0)) for k in ("S", "sig", "Z")):
        fails.append("spread differs from D735's")
    t1, t2 = trigger(s1["Z"], s1["S"], 1.0, S.M_LO, S.M_HI), S.trigger(s2["Z"], s2["S"], 1.0)
    if not (np.array_equal(t1[0], t2[0]) and np.array_equal(t1[1], t2[1])):
        fails.append("trigger differs from D735's")
    fw1 = fw_design(X, XL, L, clocks=list(S.CLOCKS))   # D735 pooled 30..330; D739 declares 30..L-30
    fw2 = S.fw_design(X, XL)
    if not (fw1["clocks"] == list(S.CLOCKS) and np.allclose(fw1["e"], fw2["e"], equal_nan=True, rtol=0, atol=1e-12)):
        fails.append("fw_design differs from D735's at L = 390")
    # 2) a shorter window works: sign in money, the trigger window bounds
    Ls, mhi = 240, 150
    Cs = np.tile(np.linspace(100, 112, Ls), (4, 1))
    Ops = np.column_stack([Cs[:, 0], Cs[:, :-1]])
    pps = {"Op": Ops, "H": np.maximum(Ops, Cs) + 0.05, "L": np.minimum(Ops, Cs) - 0.05, "C": Cs, "soc": np.full(4, 5.0)}
    Gs = e1_tables(pps, 1.0, MLO, mhi, 0.1, 10.0)
    if not (Gs["up"][0, MLO] > 0 and Gs["dn"][0, MLO] < 0):
        fails.append("sign: a rising day did not pay long / lose short on a 240-bar window")
    if np.isfinite(Gs["up"][0, mhi + 1]) or not np.isfinite(Gs["up"][0, mhi]):
        fails.append("the E1 table is not bounded to the trigger window")
    # 3) a gapped stop fills at the open less a tick
    pg = {k: v.copy() for k, v in pps.items()}
    pg["Op"][1, 60] = pg["Op"][1, 40] - 50.0
    pg["L"][1, 60], pg["H"][1, 60] = pg["Op"][1, 60] - 0.05, pg["Op"][1, 60] + 0.05
    Gg = e1_tables(pg, 1.0, MLO, mhi, 0.1, 10.0)
    want = (pg["Op"][1, 60] - 0.1 - pg["Op"][1, 40]) * 10.0
    if not math.isclose(float(Gg["up"][1, 40]), want, abs_tol=1e-9):
        fails.append("a gapped stop did not fill at the open less a tick")
    # 4) the cost line follows the file's rule
    c = cost_line("GC")
    if not (c["symbol"] == "MGC" and c["crossing_line"] == "d508_exec"
            and math.isclose(c["round_trip_usd"], 3.0 + 2.9334505021406643 * 1.0, rel_tol=1e-9)):
        fails.append(f"the GC cost line is not $3 + d508_exec x $1: {c}")
    if cost_line("ZN")["size"] != "full" or cost_line("ZN")["crossing_line"] != "d556_one_tick":
        fails.append("ZN's cost line is not the full contract on the one-tick default")
    if fails:
        P("SELFTEST FAILED:", fails)
        return 1
    P("SELFTEST OK: at L = 390 the E1 tables, minute_x, spread, trigger and the FW design equal D735's exactly; on a "
      "240-bar window a rising day pays long and loses short and the table is bounded to the trigger window; a gapped "
      "stop fills at the open less a tick; the cost lines follow futures_costs.json's rule")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.run:
        if OUT.exists():
            raise D739Error(f"{OUT.name} exists: D739 runs once")
        return run(a.data_root)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
