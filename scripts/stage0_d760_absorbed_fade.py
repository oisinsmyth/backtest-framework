"""D760 Stage 0: the absorbed fade on quiet long-gamma days (prop book), as pre-registered in
docs/decisions/D760-STAGE-0-PRE-REG-flow-validated-quiet-gamma-fade.md (b0d97ef0).

    uv run --no-sync python scripts/stage0_d760_absorbed_fade.py --selftest
    uv run --no-sync python scripts/stage0_d760_absorbed_fade.py --run     # once; writes data/stage0_d760_absorbed_fade.json

Armed on D757's G and not-I days (ES, NQ, YM). Seven 30-minute windows close at 11:00 ... 14:00; a window fires when
aggressive flow in the morning's direction d is at or above theta (the 67th percentile of |f| over every usable window
of the previous 250 sessions, strictly prior) AND the window makes no progress (d * Delta <= 0). The first firing
window's close is the entry; the fade (side -d) is held to the 15:59 close, one micro. Books V (primary), A0 (the 10:30
fade on the same days), P0 (A2 alone). Gates T, G1-G5; G2 is the exact enumerated rotation of the flow across armed
days (shared offset). In-sample only (<= 2023-12-29).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d756_reverting_days as V  # noqa: E402  (read-only)
import stage0_d757_gamma_impulse as W  # noqa: E402  (read-only)
import build_fut_es_signed_1m as BF  # noqa: E402  (sierra_code only; importing never runs it)

SPEC = REPO / "docs" / "decisions" / "D760-STAGE-0-PRE-REG-flow-validated-quiet-gamma-fade.md"
OUT = REPO / "data" / "stage0_d760_absorbed_fade.json"
D757_OUT = REPO / "data" / "stage0_d757_gamma_impulse.json"
BOOKS = REPO / "data" / "d748_component_books.csv"
FX = V.DATA / "fixtures"
ROOTS = ("ES", "NQ", "YM")
NMIN = 390
M1030 = 60                                   # minute index of the bar starting 10:30
WIN_STARTS = [M1030 + 30 * k for k in range(7)]   # window k covers bars a .. a+29; it closes at t = a + 30 (11:00 .. 14:00)
WLEN, MIN_COV, LOOKBACK, QTH = 30, 25, 250, 67.0
T_MIN, MIN_TRADES = 2.0, 150
SEAL = V.SEAL


class D760Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D760Error(msg)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ================================================================================ flow
def flow_panel(flow: pd.DataFrame, days: np.ndarray, sc_con: np.ndarray) -> dict:
    """Per-day x minute buy, sell, volume and presence for rows whose contract equals the bars' contract (Sierra code)."""
    need(not (flow["day"] >= SEAL).any(), "the seal: a flow row on or after 2024-01-01")
    want = pd.Series(sc_con, index=days)
    fl = flow[flow["day"].isin(days)]
    fl = fl[fl["contract"].to_numpy(str) == want.reindex(fl["day"]).to_numpy(str)]
    mins = [BF.MINUTES[m] for m in range(NMIN)]
    out = {}
    for col in ("buy", "sell", "volume"):
        out[col] = fl.pivot(index="day", columns="hhmm", values=col).reindex(index=days, columns=mins).to_numpy(float)
    out["has"] = np.isfinite(out["volume"])
    for col in ("buy", "sell", "volume"):
        out[col] = np.nan_to_num(out[col], nan=0.0)
    return out


def windows(fp: dict, C: np.ndarray) -> dict:
    """f, coverage and Delta for the seven windows (n x 7)."""
    n = C.shape[0]
    f = np.full((n, 7), np.nan)
    cov = np.zeros((n, 7), int)
    D = np.full((n, 7), np.nan)
    Pt = np.full((n, 7), np.nan)
    for k, a in enumerate(WIN_STARTS):
        sl = slice(a, a + WLEN)
        b, s, v = fp["buy"][:, sl].sum(1), fp["sell"][:, sl].sum(1), fp["volume"][:, sl].sum(1)
        cov[:, k] = fp["has"][:, sl].sum(1)
        with np.errstate(invalid="ignore", divide="ignore"):
            f[:, k] = np.where(v > 0, (b - s) / v, np.nan)
        Pt[:, k] = C[:, a + WLEN - 1]
        D[:, k] = C[:, a + WLEN - 1] - C[:, a - 1]
    usable = (cov >= MIN_COV) & np.isfinite(f)
    return dict(f=np.where(usable, f, np.nan), cov=cov, usable=usable, D=D, Pt=Pt)


def theta_series(f: np.ndarray, include_current: bool = False) -> np.ndarray:
    """67th percentile of |f| over every usable window of the previous LOOKBACK sessions (strictly prior)."""
    n = f.shape[0]
    th = np.full(n, np.nan)
    af = np.abs(f)
    for i in range(LOOKBACK, n):
        w = af[i - LOOKBACK + (1 if include_current else 0): i + (1 if include_current else 0)].ravel()
        w = w[np.isfinite(w)]
        if w.size:
            th[i] = np.percentile(w, QTH)
    return th


def fire_first(f, usable, D, d, th) -> np.ndarray:
    """Index of the first firing window (0..6), -1 if none."""
    fire = usable & (d[:, None] * f >= th[:, None]) & (d[:, None] * D <= 0)
    fire &= np.isfinite(th)[:, None]
    return np.where(fire.any(1), fire.argmax(1), -1)


def first_no_progress(D, d) -> np.ndarray:
    fire = (d[:, None] * D <= 0) & np.isfinite(D)
    return np.where(fire.any(1), fire.argmax(1), -1)


# ================================================================================ statistics
def clustered_t(x: np.ndarray, days: np.ndarray) -> float:
    """t of the trade mean with the sums of residuals clustered by session (one row per session, summing the roots)."""
    n = x.size
    if n < 3:
        return float("nan")
    e = x - x.mean()
    s = pd.Series(e).groupby(days).sum().to_numpy()
    se = math.sqrt(float((s * s).sum())) / n
    return float(x.mean() / se) if se > 0 else float("nan")


def efficiency(g: np.ndarray) -> float:
    a = np.abs(g).sum()
    return float(g.sum() / a) if a > 0 else 0.0


def dist(x: np.ndarray) -> dict:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    n = x.size
    if n < 3:
        return {"n": int(n)}
    srt = np.sort(x)
    k = int(math.floor(0.01 * n))
    w, l = x[x > 0], x[x < 0]
    sd = x.std(ddof=1)
    return {"n": int(n), "mean": float(x.mean()), "t": float(x.mean() / (sd / math.sqrt(n))), "median": float(np.median(x)),
            "win": float((x > 0).mean()), "payoff": float(w.mean() / -l.mean()) if w.size and l.size else None,
            "skew": float(pd.Series(x).skew()), "kurt": float(pd.Series(x).kurt()), "sd": float(sd),
            "mean_ex_top1": float(srt[: n - k].mean()) if k else float(x.mean()),
            "mean_ex_bottom1": float(srt[k:].mean()) if k else float(x.mean()),
            "mean_trim_both1": float(srt[k: n - k].mean()) if k else float(x.mean())}


def daily_book(tr: pd.DataFrame, cal: np.ndarray, col: str) -> pd.Series:
    return tr.groupby("day")[col].sum().reindex(cal, fill_value=0.0)


def sharpe_sortino(s: pd.Series) -> tuple[float, float]:
    x = s.to_numpy(float)
    sd = x.std(ddof=1)
    dd = math.sqrt(float(np.mean(np.minimum(x, 0) ** 2)))
    return (float(x.mean() / sd * math.sqrt(252)) if sd > 0 else float("nan"),
            float(x.mean() / dd * math.sqrt(252)) if dd > 0 else float("nan"))


def four_groups(tr: pd.DataFrame, cal: np.ndarray) -> dict:
    if tr.empty:
        return {"n": 0}
    dn, dg = daily_book(tr, cal, "net"), daily_book(tr, cal, "gross")
    sh, so = sharpe_sortino(dn)
    shg, sog = sharpe_sortino(dg)
    eq = dn.cumsum()
    yrs = tr.assign(y=tr["day"].str[:4]).groupby("y")["net"].agg(["count", "sum", "mean"])
    top = tr.sort_values("net", ascending=False)
    pos = tr.loc[tr["net"] > 0, "net"].sort_values(ascending=False)
    half = int(np.searchsorted(pos.cumsum().to_numpy(), tr["net"].sum() / 2) + 1) if tr["net"].sum() > 0 else None
    return {"trades": int(len(tr)), "net": dist(tr["net"].to_numpy()), "gross": dist(tr["gross"].to_numpy()),
            "t_clustered_net": clustered_t(tr["net"].to_numpy(float), tr["day"].to_numpy()),
            "daily_net_sharpe": sh, "daily_net_sortino": so, "daily_gross_sharpe": shg, "daily_gross_sortino": sog,
            "exposure_share_of_sessions": float((dn != 0).mean()), "max_dd_usd": float((eq.cummax() - eq).max()),
            "total_net_usd": float(tr["net"].sum()), "breakeven_cost_rt_usd": float(tr["gross"].mean()),
            "mean_cost_rt_usd": float((tr["gross"] - tr["net"]).mean()),
            "mean_abs_move_usd": float(tr["gross"].abs().mean()),
            "by_year": {y: {"n": int(r["count"]), "net": float(r["sum"]), "mean": float(r["mean"])} for y, r in yrs.iterrows()},
            "by_root": {r: dist(g["net"].to_numpy()) for r, g in tr.groupby("root")},
            "long_short": {("long" if s > 0 else "short"): dist(g["net"].to_numpy()) for s, g in tr.groupby("side")},
            "price_tercile": {str(k): dist(g["net"].to_numpy()) for k, g in tr.groupby("ptile")},
            "trades_to_half_net": half,
            "top5": top.head(5)[["day", "root", "clock", "net"]].to_dict("records"),
            "bottom5": top.tail(5)[["day", "root", "clock", "net"]].to_dict("records")}


def g4(tr: pd.DataFrame) -> dict:
    y = tr["day"].str[:4]
    tot = float(tr["net"].sum())
    ys = tr.groupby(y)["net"].agg(["count", "sum"])
    elig = ys[ys["count"] >= 10]
    out = {"ex2020": float(tr.loc[y != "2020", "net"].sum()), "ex2022": float(tr.loc[y != "2022", "net"].sum()),
           "max_year_share": float(ys["sum"].max() / tot) if tot > 0 else None,
           "years_positive": int((elig["sum"] > 0).sum()), "years_eligible": int(len(elig))}
    out["pass"] = bool(out["ex2020"] > 0 and out["ex2022"] > 0 and tot > 0 and out["max_year_share"] <= 0.5
                       and out["years_positive"] >= math.ceil(out["years_eligible"] / 2))
    return out


# ================================================================================ the rotation (G2)
def v_gross(rows: dict, shift: int = 0) -> np.ndarray:
    """Pooled gross of V with each root's flow (f, usable) shifted by `shift` mod its armed count."""
    gs = []
    for r, x in rows.items():
        n = x["f"].shape[0]
        idx = (np.arange(n) + shift) % n
        j = fire_first(x["f"][idx], x["usable"][idx], x["D"], x["d"], x["th"])
        ok = j >= 0
        gs.append(x["GW"][np.flatnonzero(ok), j[ok]])
    return np.concatenate(gs) if gs else np.array([])


def rotation(rows: dict) -> dict:
    n_min = min(x["f"].shape[0] for x in rows.values())
    obs = efficiency(v_gross(rows, 0))
    null = np.array([efficiency(v_gross(rows, k)) for k in range(1, n_min)])
    return {"observed": obs, "offsets": int(null.size), "p50": float(np.percentile(null, 50)),
            "p95": float(np.percentile(null, 95)), "rank": float((null < obs).mean()),
            "p_one_sided": float((1 + (null >= obs).sum()) / (1 + null.size))}


# ================================================================================ the lag audit (second implementation)
def _pct_linear(vals: list[float], q: float) -> float:
    s = sorted(vals)
    h = (len(s) - 1) * q / 100.0
    lo = int(math.floor(h))
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (h - lo) * (s[hi] - s[lo])


def lag_audit(raw_bars: pd.DataFrame, raw_flow: pd.DataFrame, days: np.ndarray, sc_con: np.ndarray, O: np.ndarray,
              th: np.ndarray, j_first: np.ndarray, entry: np.ndarray, sample: list[int]) -> None:
    """For sampled armed rows, re-derive f_w, Delta_w, theta, the first firing window and the entry from the raw rows."""
    fb = {d: g for d, g in raw_flow.groupby("day")}
    bb = {d: g.set_index("hhmm")["close"] for d, g in raw_bars.groupby("day")}
    pos = {d: i for i, d in enumerate(days)}

    def close_at(day, m):                       # the last close at or before bar m (D727's forward fill)
        s = bb[day]
        for mm in range(m, -1, -1):
            h = BF.MINUTES[mm]
            if h in s.index:
                return float(s[h])
        return float("nan")

    memo: dict = {}

    def win_f(day):
        if day in memo:
            return memo[day]
        out = []
        g = fb.get(day)
        con = sc_con[pos[day]]
        for a in WIN_STARTS:
            if g is None:
                out.append(None)
                continue
            mins = set(BF.MINUTES[a:a + WLEN])
            w = g[(g["hhmm"].isin(mins)) & (g["contract"] == con)]
            if len(w) < MIN_COV or w["volume"].sum() <= 0:
                out.append(None)
                continue
            out.append(float((w["buy"].sum() - w["sell"].sum()) / w["volume"].sum()))
        memo[day] = out
        return out

    for i in sample:
        day = days[i]
        vals = []
        for jj in range(i - LOOKBACK, i):
            vals += [abs(x) for x in win_f(days[jj]) if x is not None]
        t_loop = _pct_linear(vals, QTH)
        need(math.isclose(t_loop, th[i], rel_tol=1e-9, abs_tol=1e-12), f"lag: theta at {day} {t_loop} vs {th[i]}")
        p1030 = close_at(day, M1030 - 1)
        d = 1.0 if p1030 > O[i] else -1.0
        fw = win_f(day)
        first = -1
        for k, a in enumerate(WIN_STARTS):
            dl = close_at(day, a + WLEN - 1) - close_at(day, a - 1)
            if fw[k] is not None and d * fw[k] >= t_loop and d * dl <= 0:
                first = k
                break
        need(first == j_first[i], f"lag: first firing window at {day} {first} vs {j_first[i]}")
        if first >= 0:
            need(math.isclose(close_at(day, WIN_STARTS[first] + WLEN - 1), entry[i], rel_tol=0, abs_tol=1e-9),
                 f"lag: entry at {day}")


# ================================================================================ the run
def load_root(r: str, costs: dict) -> dict:
    import stage0_d727_trend_curve as T7
    P = V.load_root_panel(T7, r)
    pn = T7.load_root(r, V.DATA)
    ob = T7.objects(pn)
    need(np.array_equal(P["days"], pn["days"]), f"{r}: the panels' days differ")
    need(max(P["days"]) < SEAL, f"the seal: {r}")
    days = P["days"]
    raw = pn["raw"]
    mins = [BF.MINUTES[m] for m in range(NMIN)]
    Op = raw.pivot(index="day", columns="hhmm", values="open").reindex(index=days, columns=mins).to_numpy(float)
    sc_con = np.array([BF.sierra_code(c, d) for c, d in zip(P["con"], days)])
    flow = pd.read_csv(FX / f"fut_{r}_signed_1m.csv.gz", dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
    flow = flow[flow["day"] < SEAL]
    fp = flow_panel(flow, days, sc_con)
    wd = windows(fp, pn["C"])
    th = theta_series(wd["f"])
    z = ob["z"][:, W.J1030]
    I = np.isfinite(z) & (np.abs(z) >= W.Z_IMP)
    G = W.gamma_cells(V.gex_prior(days))
    RD = V.rd_label(P["E"], days)
    ce = costs[r]["micro"]
    cost = float(ce["commission_rt_usd"]["value"] + ce["crossing_ticks_rt"][ce["default_line"]]["value"] * ce["tick_usd"])
    upp = float(ce["usd_per_point"])
    P1030 = ob["Pt"][:, W.J1030]
    C = ob["close"]
    d = np.sign(P1030 - P["O"])
    s = -d
    GW = s[:, None] * (C[:, None] - wd["Pt"]) * upp
    nxt = np.column_stack([Op[:, a + WLEN] for a in WIN_STARTS])
    nxt = np.where(np.isfinite(nxt), nxt, wd["Pt"])
    GWn = s[:, None] * (C[:, None] - nxt) * upp
    return dict(root=r, days=days, O=P["O"], C=C, P1030=P1030, d=d, s=s, G=G, I=I, RD=RD, th=th, cost=cost, upp=upp,
                GW=GW, GWn=GWn, sc_con=sc_con, raw=raw, flow=flow, has_any=fp["has"].any(1), **wd)


def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: run-once")
    t0 = time.time()
    costs = json.loads(V.COSTS.read_text(encoding="utf-8"))["roots"]
    d757 = json.loads(D757_OUT.read_text(encoding="utf-8"))
    roots = [r for r in ROOTS if json.loads((FX / f"fut_{r}_signed_1m.meta.json").read_text(encoding="utf-8"))["validation"]["pass"]]
    need(roots == list(ROOTS), f"a flow fixture failed its validation: {roots}")
    R = {r: load_root(r, costs) for r in roots}
    print(f"[D760] loaded {roots} in {time.time() - t0:.0f} s", flush=True)
    # 1. the known answer: D757's G and not-I cells
    for r, x in R.items():
        m = (x["G"] == 1) & ~x["I"]
        want = d757["cells"][r]["G_and_notI"]
        need(int(m.sum()) == want["n"] and math.isclose(float(x["RD"][m].mean()), want["rd_rate"], rel_tol=1e-12),
             f"known answer: {r} G and not-I {int(m.sum())} / {x['RD'][m].mean()}")
    rows, trades, a0, p0, info = {}, [], [], [], {}
    rng = np.random.default_rng(760)
    for r, x in R.items():
        armed = (x["G"] == 1) & ~x["I"] & (x["d"] != 0) & np.isfinite(x["th"])
        idx = np.flatnonzero(armed)
        j = fire_first(x["f"], x["usable"], x["D"], x["d"], x["th"])
        entry = np.where(j >= 0, x["Pt"][np.arange(len(j)), np.clip(j, 0, None)], np.nan)
        # 2. lag audit on 40 sampled armed rows (about half of them firing)
        firing = idx[j[idx] >= 0]
        quiet = idx[j[idx] < 0]
        samp = list(rng.choice(firing, size=min(20, firing.size), replace=False)) + \
            list(rng.choice(quiet, size=min(20, quiet.size), replace=False))
        lag_audit(x["raw"], x["flow"], x["days"], x["sc_con"], x["O"], x["th"], j, entry, [int(i) for i in samp])
        # 4. right quantity
        need(np.all(np.array(WIN_STARTS) >= M1030), "a window starts before 10:30")
        A0g = V.fade(x["O"], x["P1030"], x["C"], x["upp"], x["cost"])
        a0g_direct = x["s"] * (x["C"] - x["P1030"]) * x["upp"]
        need(np.allclose(A0g[0][idx], a0g_direct[idx], rtol=0, atol=1e-9), f"{r}: A0 does not reproduce D756's fade")
        rows[r] = dict(f=x["f"][idx], usable=x["usable"][idx], D=x["D"][idx], d=x["d"][idx], th=x["th"][idx], GW=x["GW"][idx])
        pt = pd.qcut(pd.Series(x["P1030"][idx]), 3, labels=False).to_numpy()
        for k, i in enumerate(idx):
            base = dict(day=x["days"][i], root=r, side=int(x["s"][i]), ptile=int(pt[k]), rd=bool(x["RD"][i]))
            g0 = float(A0g[0][i])
            a0.append(dict(base, clock="10:30", gross=g0, net=g0 - x["cost"]))
            jp = first_no_progress(x["D"][i:i + 1], x["d"][i:i + 1])[0]
            if jp >= 0:
                gp = float(x["GW"][i, jp])
                p0.append(dict(base, clock=BF.MINUTES[WIN_STARTS[jp] + WLEN], gross=gp, net=gp - x["cost"]))
            if j[i] >= 0:
                g = float(x["GW"][i, j[i]])
                gn = float(x["GWn"][i, j[i]])
                trades.append(dict(base, clock=BF.MINUTES[WIN_STARTS[j[i]] + WLEN], gross=g, net=g - x["cost"],
                                   net_next_open=gn - x["cost"]))
        info[r] = dict(armed_after_burn_in=int(idx.size), armed_all=int(((x["G"] == 1) & ~x["I"]).sum()),
                       windows_usable_share=float(x["usable"][idx].mean()), fired=int((j[idx] >= 0).sum()),
                       fire_window_share=float((x["usable"][idx] & (x["d"][idx, None] * x["f"][idx] >= x["th"][idx, None])
                                                & (x["d"][idx, None] * x["D"][idx] <= 0)).sum() / max(1, x["usable"][idx].sum())),
                       days_without_flow=int((~x["has_any"]).sum()),
                       cost=x["cost"], theta_median=float(np.nanmedian(x["th"])))
    Vt, A0t, P0t = pd.DataFrame(trades), pd.DataFrame(a0), pd.DataFrame(p0)
    # 3. sign audit in money and the rotation's offset 0
    need(math.isclose(efficiency(v_gross(rows, 0)), efficiency(Vt["gross"].to_numpy()), rel_tol=1e-12), "rotation offset 0 != observed")
    cal = np.array(sorted(set().union(*[set(x["days"][np.isfinite(x["th"])]) for x in R.values()])))
    rot = rotation(rows)
    n = len(Vt)
    Tn = n >= MIN_TRADES
    vnet = Vt["net"].to_numpy(float) if n else np.array([])
    tcl = clustered_t(vnet, Vt["day"].to_numpy()) if n else float("nan")
    G1 = bool(n and vnet.mean() > 0 and tcl >= T_MIN and np.median(vnet) >= 0)
    G2 = bool(rot["observed"] > rot["p95"])
    G3 = bool(n and vnet.mean() > A0t["net"].mean())
    g4r = g4(Vt) if n else {"pass": False}
    by_root = {r: (float(g["net"].mean()) if len(g) else None) for r, g in Vt.groupby("root")} if n else {}
    G5 = sum(1 for v in by_root.values() if v is not None and v > 0) >= 2
    if not Tn:
        reading = "NO TEST"
    elif G1 and G2 and G3 and g4r["pass"] and G5:
        reading = "PASS"
    elif not G2:
        reading = "NOTHING"
    elif G2 and not G1:
        reading = "FLOW ONLY"
    else:
        reading = "FAIL"
    # the component line
    bk = pd.read_csv(BOOKS, dtype={"session": str}, encoding="utf-8")
    dn = daily_book(Vt, cal, "net") if n else pd.Series(0.0, index=cal)
    rho = {}
    for b, g in bk.groupby("book"):
        sb = g.groupby("session")["net"].sum()
        lo, hi = max(cal.min(), sb.index.min()), min(cal.max(), sb.index.max())
        span = cal[(cal >= lo) & (cal <= hi)]
        rho[b] = float(np.corrcoef(dn.reindex(span).to_numpy(), sb.reindex(span, fill_value=0.0).to_numpy())[0, 1]) if span.size > 30 else None
    q_all = {r: float(x["RD"][(x["G"] == 1) & ~x["I"] & np.isfinite(x["th"]) & (x["d"] != 0)].mean()) for r, x in R.items()}
    res = {"record": "D760 (b0d97ef0)", "reading": reading,
           "gates": {"T": {"trades": n, "pass": Tn},
                     "G1": {"mean_net": float(vnet.mean()) if n else None, "t_clustered": tcl,
                            "median_net": float(np.median(vnet)) if n else None, "pass": G1},
                     "G2": dict(rot, **{"pass": G2}),
                     "G3": {"V_mean_net": float(vnet.mean()) if n else None, "A0_mean_net": float(A0t["net"].mean()), "pass": G3},
                     "G4": g4r, "G5": {"mean_net_by_root": by_root, "pass": bool(G5)}},
           "V": four_groups(Vt, cal), "A0": four_groups(A0t, cal), "P0": four_groups(P0t, cal),
           "V_next_open_entry": dist(Vt["net_next_open"].to_numpy()) if n else None,
           "V_entry_clocks": Vt["clock"].value_counts().sort_index().to_dict() if n else {},
           "rd_rate": {"V_days": float(Vt["rd"].mean()) if n else None, "armed_days_by_root": q_all,
                       "V_days_by_root": {r: float(g["rd"].mean()) for r, g in Vt.groupby("root")} if n else {}},
           "component_line": {"daily_net_sharpe": sharpe_sortino(dn)[0], "daily_net_sortino": sharpe_sortino(dn)[1],
                              "rho": rho, "calendar_sessions": int(cal.size)},
           "roots": info, "runner_sha256": sha(Path(__file__).resolve()), "prereg_sha256": sha(SPEC),
           "wall_s": round(time.time() - t0, 1)}
    with open(OUT, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(V._strip(res), fh, indent=1, default=str)
        fh.write("\n")
    show(res)
    return 0


def show(res: dict) -> None:
    g = res["gates"]
    print(f"[D760] {res['reading']}: trades {g['T']['trades']}; G1 mean {g['G1']['mean_net']} t_cl {g['G1']['t_clustered']} "
          f"median {g['G1']['median_net']} -> {g['G1']['pass']}")
    print(f"  G2 eff {g['G2']['observed']:.4f} vs p50 {g['G2']['p50']:.4f} p95 {g['G2']['p95']:.4f} (rank {g['G2']['rank']:.3f}, "
          f"{g['G2']['offsets']} offsets) -> {g['G2']['pass']}")
    print(f"  G3 V {g['G3']['V_mean_net']} vs A0 {g['G3']['A0_mean_net']:.2f} -> {g['G3']['pass']}; G4 {g['G4']}; G5 {g['G5']}")
    for b in ("V", "A0", "P0"):
        x = res[b]
        if x.get("trades"):
            print(f"  {b}: n {x['trades']} net {x['net']['mean']:.2f} (med {x['net']['median']:.2f}, win {x['net']['win']:.3f}, "
                  f"skew {x['net']['skew']:.2f}) gross {x['gross']['mean']:.2f}; Sharpe {x['daily_net_sharpe']:.2f} "
                  f"Sortino {x['daily_net_sortino']:.2f}")
    print(f"  RD rate on V days {res['rd_rate']['V_days']}; armed {res['rd_rate']['armed_days_by_root']}")
    print(f"  roots {res['roots']}")
    print(f"[D760] wall {res['wall_s']} s")


# ================================================================================ self-test
def selftest() -> int:
    fails = []
    rng = np.random.default_rng(1)
    # theta: strictly prior, and the broken (current-including) form must differ and be caught by the audit's compare
    f = rng.normal(0, 0.1, (300, 7))
    i = 280
    f[i] = 10.0                                  # the current session's windows are huge: including them must move theta
    f[i - LOOKBACK] = 0.0
    th, thb = theta_series(f), theta_series(f, include_current=True)
    vals = [abs(v) for v in f[i - LOOKBACK:i].ravel()]
    if not math.isclose(_pct_linear(vals, QTH), th[i], rel_tol=1e-12):
        fails.append("theta != the loop's percentile")
    try:
        need(math.isclose(_pct_linear(vals, QTH), thb[i], rel_tol=1e-9), "lag: theta")
        fails.append("a current-including theta did not raise")
    except D760Error:
        pass
    # the lag audit itself, on synthetic raw rows: passes on the true theta, raises on a current-including one
    nd = LOOKBACK + 8
    days = np.array([d.strftime("%Y-%m-%d") for d in pd.bdate_range("2016-01-04", periods=nd)])
    mins = [BF.MINUTES[m] for m in range(NMIN)]
    px = 100 + np.cumsum(rng.normal(0, 0.25, (nd, NMIN)), axis=1)
    vol = rng.integers(50, 150, (nd, NMIN))
    buy = (vol * rng.uniform(0.2, 0.8, (nd, NMIN))).astype(int)
    rb = pd.DataFrame({"day": np.repeat(days, NMIN), "hhmm": np.tile(mins, nd), "close": px.ravel()})
    rf = pd.DataFrame({"day": np.repeat(days, NMIN), "hhmm": np.tile(mins, nd), "contract": "ESH16",
                       "buy": buy.ravel(), "sell": (vol - buy).ravel(), "volume": vol.ravel()})
    sc = np.array(["ESH16"] * nd)
    Osyn = px[:, 0] - 0.1
    wd = windows(flow_panel(rf, days, sc), px)
    ths, thx = theta_series(wd["f"]), theta_series(wd["f"], include_current=True)
    dsyn = np.sign(px[:, M1030 - 1] - Osyn)
    js = fire_first(wd["f"], wd["usable"], wd["D"], dsyn, ths)
    ent = np.where(js >= 0, wd["Pt"][np.arange(nd), np.clip(js, 0, None)], np.nan)
    smp = list(range(LOOKBACK, nd))
    try:
        lag_audit(rb, rf, days, sc, Osyn, ths, js, ent, smp)
    except D760Error as e:
        fails.append(f"lag audit raised on the true theta: {e}")
    try:
        lag_audit(rb, rf, days, sc, Osyn, thx, js, ent, smp)
        fails.append("lag audit did not raise on a current-including theta")
    except D760Error:
        pass
    # fire_first
    ff = np.array([[0.2, 0.3, 0.0, 0, 0, 0, 0]])
    D = np.array([[1.0, -1.0, -1.0, 0, 0, 0, 0]])
    if fire_first(ff, np.ones_like(ff, bool), D, np.array([1.0]), np.array([0.15]))[0] != 1:
        fails.append("fire_first")
    if fire_first(-ff, np.ones_like(ff, bool), -D, np.array([-1.0]), np.array([0.15]))[0] != 1:
        fails.append("fire_first, short morning")
    # sign in money: the fade of an up morning is short; a fall to the close pays it
    g0 = V.fade(np.array([100.0]), np.array([101.0]), np.array([99.0]), 5.0, 1.0)
    if not (g0[0][0] == 10.0 and g0[1][0] == 9.0):
        fails.append("sign in money")
    # the seal
    try:
        flow_panel(pd.DataFrame({"day": ["2024-01-02"], "hhmm": ["09:30"], "contract": ["ESH24"], "buy": [1], "sell": [1],
                                 "volume": [2]}), np.array(["2023-12-29"]), np.array(["ESH24"]))
        fails.append("seal did not raise")
    except D760Error:
        pass
    # clustered t: one row per session equals the plain t (up to n/(n-1))
    x = rng.normal(1, 3, 500)
    tc = clustered_t(x, np.arange(500).astype(str))
    tp = x.mean() / (x.std(ddof=0) / math.sqrt(500))
    if not math.isclose(tc, tp, rel_tol=1e-9):
        fails.append("clustered t")
    # synthetic: planted effect passes G1 and G2; noise fails G2 about 95 %

    def synth(planted: bool, seed: int):
        r = np.random.default_rng(seed)
        n = 400
        f = r.normal(0, 0.1, (n, 7))
        D = r.normal(0, 1, (n, 7))
        d = r.choice([-1.0, 1.0], n)
        thr = np.full(n, 0.05)
        GW = r.normal(0, 50, (n, 7))
        if planted:
            fire = (d[:, None] * f >= thr[:, None]) & (d[:, None] * D <= 0)
            GW = GW + 40.0 * fire
        rows = {"X": dict(f=f, usable=np.ones_like(f, bool), D=D, d=d, th=thr, GW=GW)}
        return rows

    rows = synth(True, 5)
    g = v_gross(rows, 0)
    rot = rotation(rows)
    if not (g.mean() - 4 > 0 and g.mean() / (g.std(ddof=1) / math.sqrt(g.size)) > 2 and rot["observed"] > rot["p95"]):
        fails.append("planted effect did not pass G1/G2")
    nf = sum(1 for sd in range(100) if (lambda rt: rt["observed"] <= rt["p95"])(rotation(synth(False, 100 + sd))))
    if not (85 <= nf <= 100):
        fails.append(f"noise failed G2 {nf} / 100 (expected about 95)")
    print(f"  noise fails G2 {nf} / 100")
    for f_ in fails:
        print(f"[SELFTEST FAIL] {f_}")
    print(f"[D760] selftest: {'FAIL' if fails else 'all passed'}")
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
