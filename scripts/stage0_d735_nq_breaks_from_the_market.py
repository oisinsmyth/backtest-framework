"""D735 Stage 0: NQ breaks from the market. Spec: docs/decisions/D735-STAGE-0-PRE-REG-nq-breaks-from-the-market.md
(with D735-A1), committed before this file existed.

    uv run python scripts/stage0_d735_nq_breaks_from_the_market.py --selftest
    uv run python scripts/stage0_d735_nq_breaks_from_the_market.py --run --data-root <checkout>/data      # once

NQ's day session (D727's days and sigma_oc; D733's OHLC panels). Legs ES / YM / RTY (D727's load_root), EQ (their
mean) and TICK (Sierra TICK-NQ, cumulated since the open). s_m = x_NQ,m - x_L,m; z_s = s / (sigma_s sqrt(m/390)).
Trigger: the first minute 10:00-14:30 with |z_s| >= k; D = sign(s); one MNQ from the bar-m0 open; E1 = a 1 sigma_rem
stop (or none) or the 15:59 close. Every (day, minute, direction, stop rule) E1 is tabulated once; trades, nulls and
matched rows index the table, and a loop implementation re-derives sampled entries. Nothing dated 2024-01-01 or later
is read.
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
import stage0_d727_trend_curve as T  # noqa: E402
import stage0_d731_flat_u as F  # noqa: E402
import stage0_d733_pullback_entry as B  # noqa: E402

OUT = REPO / "data" / "stage0_d735_nq_breaks_from_the_market.json"
NMIN, TICK, USD = 390, 0.25, 2.0
M_LO, M_HI = 30, 300                       # 10:00 .. 14:30
LEGS = ("ES", "YM", "RTY", "EQ", "TICK")
PRICE_LEGS = ("ES", "YM", "RTY")
KS = (1.5, 1.0)
STOPS = {"1s": 1.0, "none": math.inf}
PRIMARY = ("ES", 1.5, "1s")
XBINS = ((0, 0.5), (0.5, 1.0), (1.0, 1.5), (1.5, np.inf))
HOURS = (10, 11, 12, 13, 14)
CLOCKS = T.CLOCKS
EDGE = T.EDGE
TICK_COV, TICK_MIN_DAYS = 0.9, 1000
NBOOT, SEED = 2000, 735
P = Z.P


class D735Error(AssertionError):
    pass


def cell_key(leg: str, k: float, st: str) -> str:
    return f"{leg}_k{k}_{st}"


# ================================================================================ the E1 tables
def e1_tables(pp: dict[str, np.ndarray], mult: float) -> dict[str, np.ndarray]:
    """G[dir][d, m] = the gross ($, one MNQ) of an entry at bar m's open in direction dir (+1 / -1), with a stop
    mult x sigma_rem away (inf = none), exiting at the stop or the 15:59 close; plus the stopped flag. m in M_LO..M_HI
    (other columns NaN)."""
    Op, H, L, C, soc = pp["Op"], pp["H"], pp["L"], pp["C"], pp["soc"]
    n = len(Op)
    out = {k: np.full((n, NMIN), np.nan) for k in ("up", "dn")}
    stp = {k: np.zeros((n, NMIN), bool) for k in ("up", "dn")}
    last = C[:, NMIN - 1]
    for m in range(M_LO, M_HI + 1):
        entry = Op[:, m]
        if not math.isfinite(mult):
            out["up"][:, m] = (last - entry) * USD
            out["dn"][:, m] = (entry - last) * USD
            continue
        dist = mult * soc * math.sqrt((NMIN - m) / NMIN)
        op_, lo_, hi_ = Op[:, m:], L[:, m:], H[:, m:]
        # long
        stop = entry - dist
        hit = lo_ <= stop[:, None]
        anyh = hit.any(axis=1)
        fb = hit.argmax(axis=1)
        opf = op_[np.arange(n), fb]
        ex = np.where(anyh, np.where(opf <= stop, opf - TICK, stop - TICK), last)
        out["up"][:, m] = (ex - entry) * USD
        stp["up"][:, m] = anyh
        # short
        stop = entry + dist
        hit = hi_ >= stop[:, None]
        anyh = hit.any(axis=1)
        fb = hit.argmax(axis=1)
        opf = op_[np.arange(n), fb]
        ex = np.where(anyh, np.where(opf >= stop, opf + TICK, stop + TICK), last)
        out["dn"][:, m] = (entry - ex) * USD
        stp["dn"][:, m] = anyh
    return {"up": out["up"], "dn": out["dn"], "stop_up": stp["up"], "stop_dn": stp["dn"]}


def g_at(G: dict[str, np.ndarray], d: np.ndarray, m: np.ndarray, D: np.ndarray) -> np.ndarray:
    return np.where(D > 0, G["up"][d, m], G["dn"][d, m])


def stopped_at(G: dict[str, np.ndarray], d: np.ndarray, m: np.ndarray, D: np.ndarray) -> np.ndarray:
    return np.where(D > 0, G["stop_up"][d, m], G["stop_dn"][d, m])


def e1_loop(pp: dict[str, np.ndarray], d: int, m: int, D: float, mult: float) -> float:
    """Second implementation: D733's u-space exit_e1, one trade at a time."""
    u = B.uspace(pp, d, D)
    entry = u["op"][m]
    dist = mult * pp["soc"][d] * math.sqrt((NMIN - m) / NMIN) if math.isfinite(mult) else math.inf
    ex, _, _ = B.exit_e1(u, m, entry, entry - dist, m)
    return (ex - entry) * USD


# ================================================================================ legs
def minute_x(C: np.ndarray, O: np.ndarray, soc: np.ndarray) -> np.ndarray:
    """X[:, m] = (close of bar m-1 - O) / sigma for m = 1..390; column 0 = 0."""
    X = np.zeros((len(C), NMIN + 1))
    with np.errstate(invalid="ignore", divide="ignore"):
        X[:, 1:] = (C - O[:, None]) / soc[:, None]
    return X


def align_rows(src_days: np.ndarray, src: np.ndarray, days: np.ndarray) -> np.ndarray:
    pos = pd.Series(np.arange(len(src_days)), index=src_days)
    ix = pos.reindex(days).to_numpy(float)
    out = np.full((len(days),) + src.shape[1:], np.nan)
    ok = np.isfinite(ix)
    out[ok] = src[ix[ok].astype(int)]
    return out


def join_audit(src_days: np.ndarray, src: np.ndarray, days: np.ndarray, got: np.ndarray, sample: list[int]) -> None:
    look = {dd: i for i, dd in enumerate(src_days)}
    for r in sample:
        i = look.get(days[r])
        want = src[i] if i is not None else np.full(src.shape[1:], np.nan)
        if not np.array_equal(np.nan_to_num(want, nan=-9e9), np.nan_to_num(got[r], nan=-9e9)):
            raise D735Error(f"join: the row at {days[r]} is not that date's")


def rms_prior(v: np.ndarray, w: int = 20, minp: int = 15) -> np.ndarray:
    return np.sqrt(pd.Series(v * v).shift(1).rolling(w, min_periods=minp).mean().to_numpy(float))


def tick_leg(days: np.ndarray, cut: str = Z.CUT24) -> dict[str, Any]:
    import stage0_d663_per_root_gamma_break as G663
    old = (G663.MIN0, G663.MIN1)
    G663.MIN0, G663.MIN1 = 570, 960                       # 09:30 .. 15:59
    try:
        ex = G663.extract(str(G663.SC_DATA / "TICK-NQ.scid"), cut_et=cut)
    finally:
        G663.MIN0, G663.MIN1 = old
    sess = np.array(ex["sessions"])
    if (sess >= cut).any():
        raise D735Error("seal: a TICK session on or after 2024-01-01 was extracted")
    M = ex["M"]
    cov = np.isfinite(M[:, :M_HI]).mean(axis=1)
    Mf = pd.DataFrame(M).ffill(axis=1).fillna(0.0).to_numpy(float)
    cum = np.cumsum(Mf, axis=1)                                # cum[:, b] = sum of bars 0..b
    cum[cov < TICK_COV] = np.nan
    cumA = align_rows(sess, cum, days)
    sig = rms_prior(cumA[:, NMIN - 1])
    X = np.zeros((len(days), NMIN + 1))
    with np.errstate(invalid="ignore", divide="ignore"):
        X[:, 1:] = cumA / sig[:, None]
    X[~np.isfinite(sig)] = np.nan
    X[~np.isfinite(cumA[:, 0])] = np.nan
    return {"X": X, "sessions": sess, "M": M, "cum": cum, "cov": cov, "sig": sig, "cumA": cumA,
            "days_joined": int(np.isfinite(X[:, M_LO]).sum())}


# ================================================================================ the spread and the trigger
def spread(XN: np.ndarray, XL: np.ndarray) -> dict[str, np.ndarray]:
    S = XN - XL
    sig = rms_prior(S[:, NMIN])
    mm = np.arange(NMIN + 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        Zs = S / (sig[:, None] * np.sqrt(np.maximum(mm, 1) / NMIN)[None, :])
    return {"S": S, "sig": sig, "Z": Zs}


def trigger(Zs: np.ndarray, S: np.ndarray, k: float) -> tuple[np.ndarray, np.ndarray]:
    """(m0, D) per day; m0 = -1 if no trigger. First minute M_LO..M_HI with |z_s| >= k."""
    seg = Zs[:, M_LO:M_HI + 1]
    hit = np.isfinite(seg) & (np.abs(seg) >= k)
    first = np.where(hit.any(axis=1), hit.argmax(axis=1), -1)
    m0 = np.where(first >= 0, first + M_LO, -1)
    rows = np.arange(len(Zs))
    D = np.where(m0 >= 0, np.sign(S[rows, np.clip(m0, 0, None)]), 0.0)
    m0 = np.where(D != 0, m0, -1)
    return m0, D


def trigger_second(xn: np.ndarray, xl: np.ndarray, sig_s: float, k: float, lead: int = 0) -> tuple[int, float]:
    """Second implementation on one day's raw minute values: xn[b], xl[b] are the standardised closes of bar b
    (lead = 1 reads bar m's own close at minute m: the canary)."""
    for m in range(M_LO, M_HI + 1):
        b = m - 1 + lead
        s = xn[b] - xl[b]
        z = s / (sig_s * math.sqrt(m / NMIN))
        if math.isfinite(z) and abs(z) >= k and s != 0:
            return m, float(np.sign(s))
    return -1, 0.0


# ================================================================================ the mechanism (S1)
def fw_design(XN: np.ndarray, XL: np.ndarray) -> dict[str, np.ndarray]:
    """Per clock: x_NQ, y_NQ, e = the residual of x_L on (1, x_NQ). [day, clock] arrays."""
    nc = len(CLOCKS)
    x = np.column_stack([XN[:, m] for m in CLOCKS])
    y = XN[:, [NMIN]] - x
    xl = np.column_stack([XL[:, m] for m in CLOCKS])
    e = np.full_like(xl, np.nan)
    coef = []
    for j in range(nc):
        ok = np.isfinite(x[:, j]) & np.isfinite(xl[:, j]) & np.isfinite(y[:, j])
        A = np.column_stack([np.ones(ok.sum()), x[ok, j]])
        c = np.linalg.lstsq(A, xl[ok, j], rcond=None)[0]
        e[ok, j] = xl[ok, j] - A @ c
        coef.append((float(c[0]), float(c[1])))
    return {"x": x, "y": y, "e": e, "gamma": coef}


def fw_delta(x: np.ndarray, y: np.ndarray, e: np.ndarray, cluster_t: bool = False) -> Any:
    ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(e)
    X = np.column_stack([np.ones(ok.sum()), x[ok], e[ok]])
    c, *_ = np.linalg.lstsq(X, y[ok], rcond=None)
    if not cluster_t:
        return float(c[2])
    u = y[ok] - X @ c
    days = np.broadcast_to(np.arange(x.shape[0])[:, None], x.shape)[ok]
    XtX_inv = np.linalg.inv(X.T @ X)
    sc = X * u[:, None]
    g = np.zeros((x.shape[0], 3))
    np.add.at(g, days, sc)
    meat = g.T @ g
    V = XtX_inv @ meat @ XtX_inv
    return float(c[2]), float(c[1]), float(c[2] / math.sqrt(V[2, 2]))


def fw_null(x: np.ndarray, y: np.ndarray, e: np.ndarray) -> np.ndarray:
    n = x.shape[0]
    return np.array([fw_delta(x, y, np.roll(e, j, axis=0)) for j in range(EDGE, n - EDGE)])


def per_clock_fit(x: np.ndarray, y: np.ndarray, e: np.ndarray) -> list[tuple[float, float]]:
    out = []
    for j in range(x.shape[1]):
        ok = np.isfinite(x[:, j]) & np.isfinite(y[:, j]) & np.isfinite(e[:, j])
        X = np.column_stack([np.ones(ok.sum()), x[ok, j], e[ok, j]])
        c = np.linalg.lstsq(X, y[ok, j], rcond=None)[0]
        out.append((float(c[1]), float(c[2])))
    return out


# ================================================================================ nulls and helpers
def rot(obs: float, null: np.ndarray) -> dict[str, float]:
    a = null[np.isfinite(null)]
    return {"observed": obs, "offsets": int(len(a)), "p05": float(np.quantile(a, 0.05)), "p50": float(np.median(a)),
            "p95": float(np.quantile(a, 0.95)), "p95_se": 0.0, "rank": float((a < obs).mean()),
            "p_high": float((a >= obs).mean()), "p_low": float((a <= obs).mean())}


def holm(ps: dict[str, float]) -> dict[str, float]:
    order = sorted(ps, key=ps.get)
    out, run_ = {}, 0.0
    for i, k in enumerate(order):
        run_ = max(run_, min(1.0, ps[k] * (len(order) - i)))
        out[k] = run_
    return out


def xbin(x: np.ndarray) -> np.ndarray:
    return np.digitize(np.abs(x), [0.5, 1.0, 1.5])


def timing_null(G: dict[str, np.ndarray], d: np.ndarray, m0: np.ndarray, dir_src: np.ndarray, XN: np.ndarray,
                cost: float, offsets: np.ndarray) -> dict[str, np.ndarray]:
    """All offsets at once. dir_src[t, m] gives the moved trade's direction on target day t (sign(x_NQ) for C2a,
    sign(s) for C2b). Returns per-offset mean net, efficiency and per-bin mean net."""
    n = XN.shape[0]
    tg = (d[None, :] + offsets[:, None]) % n
    mm = np.broadcast_to(m0[None, :], tg.shape)
    Dt = np.sign(dir_src[tg, mm])
    gup, gdn = G["up"][tg, mm], G["dn"][tg, mm]
    g = np.where(Dt > 0, gup, np.where(Dt < 0, gdn, np.nan))
    ok = np.isfinite(g) & (Dt != 0)
    gz = np.where(ok, g, 0.0)
    cnt = ok.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean_net = np.where(cnt > 0, gz.sum(axis=1) / cnt - cost, np.nan)
        eff = gz.sum(axis=1) / np.abs(gz).sum(axis=1)
        xb = xbin(XN[tg, mm])
        bins = []
        for b in range(len(XBINS)):
            mb = ok & (xb == b)
            cb = mb.sum(axis=1)
            bins.append(np.where(cb > 0, np.where(mb, g, 0.0).sum(axis=1) / cb - cost, np.nan))
    return {"mean_net": mean_net, "eff": eff, "bins": np.column_stack(bins), "count": cnt}


def nw_t(x: np.ndarray) -> float:
    return B.nw_t(x)


# ================================================================================ matched rows
def matched_rows(G: dict[str, np.ndarray], XN: np.ndarray, d: np.ndarray, m0: np.ndarray, gtr: np.ndarray,
                 cost: float, rng: np.random.Generator) -> dict[str, Any]:
    n = XN.shape[0]
    ms = np.arange(M_LO, M_HI + 1, 5)
    nb = len(HOURS) * len(XBINS)
    Rs, Rc = np.zeros((n, nb)), np.zeros((n, nb))
    for m in ms:
        x = XN[:, m]
        Dd = np.sign(x)
        g = np.where(Dd > 0, G["up"][:, m], np.where(Dd < 0, G["dn"][:, m], np.nan))
        ok = np.isfinite(g) & np.isfinite(x) & (Dd != 0)
        c = (HOURS.index((570 + m) // 60) * len(XBINS)) + xbin(x)
        rr = np.flatnonzero(ok)
        np.add.at(Rs, (rr, c[ok]), g[ok] - cost)
        np.add.at(Rc, (rr, c[ok]), 1.0)
    Ts, Tc = np.zeros((n, nb)), np.zeros((n, nb))
    hr = np.array([HOURS.index((570 + m) // 60) for m in m0])
    ct = hr * len(XBINS) + xbin(XN[d, m0])
    np.add.at(Ts, (d, ct), gtr - cost)
    np.add.at(Tc, (d, ct), 1.0)

    def gain(ts: np.ndarray, tc: np.ndarray, rs: np.ndarray, rc: np.ndarray) -> float:
        ok = (tc > 0) & (rc > 0)
        if not ok.any():
            return float("nan")
        return float((tc[ok] * (ts[ok] / tc[ok] - rs[ok] / rc[ok])).sum() / tc[ok].sum())

    obs = gain(Ts.sum(0), Tc.sum(0), Rs.sum(0), Rc.sum(0))
    W = rng.multinomial(n, np.full(n, 1.0 / n), size=NBOOT).astype(float)
    bt = np.array([gain(*(w @ A for A in (Ts, Tc, Rs, Rc))) for w in W])
    se = float(np.nanstd(bt, ddof=1))
    return {"gain": obs, "se": se, "t": obs / se if se > 0 else float("nan"), "rows": int(Rc.sum()),
            "trades": int(Tc.sum())}


# ================================================================================ one cell
def score_cell(ctx: dict[str, Any], leg: str, k: float, st: str) -> dict[str, Any]:
    XN, days, n, cost = ctx["XN"], ctx["days"], ctx["n"], ctx["cost"]
    sp, G = ctx["spreads"][leg], ctx["G"][st]
    m0, D = trigger(sp["Z"], sp["S"], k)
    d = np.flatnonzero(m0 >= 0)
    m0d, Dd = m0[d], D[d]
    g = g_at(G, d, m0d, Dd)
    if not np.isfinite(g).all():
        raise D735Error(f"{leg} k{k} {st}: a trade has no E1 value")
    net = g - cost
    gfull = np.full(n, np.nan)
    gfull[d] = g
    bk, daily = F.book(np.where(np.isfinite(gfull), 1.0, 0.0), gfull, cost, days)
    offs = np.arange(EDGE, n - EDGE)
    c2a = timing_null(G, d, m0d, ctx["XN"], XN, cost, offs)
    c2b0 = timing_null(G, d, m0d, sp["S"], XN, cost, np.array([0]))
    if not math.isclose(float(c2b0["mean_net"][0]), float(net.mean()), rel_tol=0, abs_tol=1e-9):
        raise D735Error(f"{leg} k{k} {st}: C2b's offset 0 does not reproduce the observed trades")
    c2b = timing_null(G, d, m0d, sp["S"], XN, cost, offs)
    eff = float(g.sum() / np.abs(g).sum())
    xb = xbin(XN[d, m0d])
    bins = {}
    for b in range(len(XBINS)):
        mb = xb == b
        bins[b] = {"trades": int(mb.sum()), "mean_net": float(net[mb].mean()) if mb.any() else None}
        if mb.sum() >= 30:
            bins[b]["rotation"] = rot(float(net[mb].mean()), c2a["bins"][:, b])
    aligned = np.sign(XN[d, m0d]) == Dd
    counter = ~aligned
    fol = g_at(G, d[counter], m0d[counter], np.sign(XN[d[counter], m0d[counter]]))
    fol = np.where(np.isfinite(fol), fol, 0.0)                       # x_NQ = 0: the follow does not trade
    pair = g[counter] - fol
    mir = g_at(G, d, m0d, -Dd) - cost
    mr = matched_rows(G, XN, d, m0d, g, cost, np.random.default_rng(SEED))
    # oracles
    fits, gam = ctx["fits"][leg], ctx["gamma"][leg]
    clocks = np.array(CLOCKS)
    j = np.array([int(np.argmin(np.abs(clocks - m))) for m in m0d])
    xl0 = ctx["XL"][leg][d, m0d]
    x0 = XN[d, m0d]
    e0 = xl0 - (np.array([gam[i][0] for i in j]) + np.array([gam[i][1] for i in j]) * x0)
    o1 = Dd * (np.array([fits[i][0] for i in j]) * x0 + np.array([fits[i][1] for i in j]) * e0) * ctx["soc"][d] * USD
    o2 = Dd * ctx["beta727"][j] * x0 * ctx["soc"][d] * USD
    # reported exits
    Gh = ctx["G"]["half"]
    rep = {"no_stop": ctx["G"]["none"], "half_sigma_stop": Gh}
    rep_out = {nm: float((g_at(GG, d, m0d, Dd) - cost).mean()) for nm, GG in rep.items()}
    C = ctx["pp"]["C"]
    Op = ctx["pp"]["Op"]
    t60 = Dd * (C[d, np.minimum(m0d + 59, NMIN - 1)] - Op[d, m0d]) * USD - cost
    rep_out["time_60min"] = float(t60.mean())
    sig_ex = []
    for i, (dd, mm, DD) in enumerate(zip(d, m0d, Dd)):
        s_row = sp["S"][dd, mm + 1:NMIN]
        flip = np.flatnonzero(np.sign(s_row) != DD)
        if len(flip):
            mx = int(mm + 1 + flip[0])
            sig_ex.append(DD * (Op[dd, mx] - Op[dd, mm]) * USD - cost)
        else:
            sig_ex.append(DD * (C[dd, NMIN - 1] - Op[dd, mm]) * USD - cost)
    rep_out["signal_exit"] = float(np.mean(sig_ex))
    # year concentration (D729), net per trade with scale sigma_NQ x $2
    from backtest_framework.validation.concentration import year_concentration
    yc = year_concentration(days[d].astype(str), net, scale=ctx["soc"][d] * USD)
    yrs = np.array([s[:4] for s in days[d]])
    ex22 = net[yrs != "2022"]
    # SAME TRADE
    fdaily = ctx["follow_daily"]
    same = (ctx["follow_m0"][d] >= 0) & (ctx["follow_D"][d] == Dd)
    rho_f = float(np.corrcoef(daily, fdaily)[0, 1])
    hours = pd.Series([(570 + m) // 60 for m in m0d]).value_counts().sort_index()
    st_flag = stopped_at(G, d, m0d, Dd) if st == "1s" else np.zeros(len(d), bool)
    return {"leg": leg, "k": k, "stop": st, "trades": int(len(d)), "book": bk, "mean_net": float(net.mean()),
            "mean_gross": float(g.mean()), "nw_t_net": nw_t(net), "efficiency_gross": eff,
            "C2a_mean": rot(float(net.mean()), c2a["mean_net"]), "C2a_eff": rot(eff, c2a["eff"]),
            "C2b_mean": rot(float(net.mean()), c2b["mean_net"]), "C2a_by_abs_x": bins,
            "aligned": {"trades": int(aligned.sum()), "mean_net": float(net[aligned].mean()) if aligned.any() else None},
            "counter": {"trades": int(counter.sum()), "mean_net": float(net[counter].mean()) if counter.any() else None,
                        "mean_gross": float(g[counter].mean()) if counter.any() else None,
                        "C1_paired_mean": float(pair.mean()) if len(pair) else None,
                        "C1_paired_t": float(pair.mean() / (pair.std(ddof=1) / math.sqrt(len(pair)))) if len(pair) > 2 else None},
            "up_days": float(net[Dd > 0].mean()) if (Dd > 0).any() else None,
            "down_days": float(net[Dd < 0].mean()) if (Dd < 0).any() else None,
            "n_up": int((Dd > 0).sum()), "n_down": int((Dd < 0).sum()),
            "mirror_mean_net": float(mir.mean()), "matched_rows": mr,
            "O1_room_gross": float(o1.mean()), "O2_drift_budget_gross": float(o2.mean()),
            "excess_over_O2": float(g.mean() - o2.mean()),
            "reported_exits_mean_net": rep_out, "year_concentration": {"label": yc["label"],
                                                                      "max_share_usd": yc["gross"]["max_share"],
                                                                      "max_share_vol": yc["vol_units"]["max_share"]},
            "ex_2022_mean_net": float(ex22.mean()) if len(ex22) else None,
            "same_trade": {"share_same_day_side": float(same.mean()), "rho_daily_with_follow": rho_f,
                           "SAME_TRADE": bool(rho_f >= 0.7)},
            "rho_nq_f2": float(np.corrcoef(daily, ctx["f2_daily"])[0, 1]),
            "entry_hour_counts": {str(k_): int(v) for k_, v in hours.items()},
            "stopped_share": float(st_flag.mean()), "_daily": daily, "_null_mean": c2a["mean_net"],
            "_trades": (d, m0d, Dd, g)}


def readings(c: dict[str, Any], cost: float, mech: dict[str, bool], fam_p95: float) -> None:
    room = c["O1_room_gross"] >= 2 * cost
    bins_ok = [v for v in c["C2a_by_abs_x"].values() if "rotation" in v]
    above = sum(v["rotation"]["observed"] > v["rotation"]["p95"] for v in bins_ok)
    need = 3 if len(bins_ok) >= 3 else len(bins_ok)
    iii = len(bins_ok) >= 1 and above >= need
    i_ = c["mean_net"] > 0 and (c["nw_t_net"] or 0) >= 2
    ii = c["C2a_mean"]["observed"] > c["C2a_mean"]["p95"] and c["C2a_eff"]["observed"] > c["C2a_eff"]["p95"]
    mr = c["matched_rows"]
    iv = mr["gain"] >= cost and (mr["t"] or 0) >= 2
    v_ = c["counter"]["trades"] < 30 or (c["counter"]["mean_gross"] or 0) >= 0
    edge = i_ and ii and iii and iv and v_
    unres = (not edge) and i_ and ii and iii and v_ and mr["gain"] > 0 and mr["gain"] + 2 * mr["se"] >= cost
    rd = "EDGE" if edge else "UNRESOLVED" if unres else "DRIFT ONLY" if c["mean_net"] > 0 else "NOTHING"
    bk = c["book"]
    yc = c["year_concentration"]
    go = (edge and mech.get(c["leg"], False) and c["C2a_mean"]["observed"] > fam_p95 and bk["net_sharpe"] >= 0.4
          and bk["years_positive"] >= 5 and yc["max_share_usd"] is not None and yc["max_share_vol"] is not None
          and yc["max_share_usd"] < 0.5 and yc["max_share_vol"] < 0.5 and (c["ex_2022_mean_net"] or -1) > 0
          and not c["same_trade"]["SAME_TRADE"])
    c["legs_of_edge"] = {"i_mean_t": bool(i_), "ii_C2a_mean_and_eff": bool(ii), "iii_bins": f"{above}/{len(bins_ok)}",
                         "iii": bool(iii), "iv_matched": bool(iv), "v_counter": bool(v_)}
    c["NO_ROOM"] = bool(not room)
    c["reading"] = ("NO ROOM; " if not room else "") + rd
    c["GO"] = bool(go and room)


# ================================================================================ the run
def run(data_root: Path) -> int:
    t0 = time.time()
    import stage1_d711_f2_mechanism as M711
    cost = float(M711.cost_line("NQ")["cost"])
    pn = T.load_root("NQ", data_root)
    ob = T.objects(pn)
    ka = json.loads((REPO / "data" / "stage0_d727_trend_curve.json").read_text(encoding="utf-8"))["roots"]["NQ"]
    if len(pn["days"]) != ka["days"] or not math.isclose(T.beta_nw(ob["x"][:, 0], ob["y"][:, 0])["beta"],
                                                         ka["clocks"][0]["beta"], rel_tol=0, abs_tol=1e-12):
        raise D735Error("NQ's objects are not D727's")
    rng = np.random.default_rng(SEED)
    T.lag_audit(pn, ob, [(int(rng.integers(0, len(pn["days"]))), int(rng.integers(0, len(CLOCKS)))) for _ in range(30)])
    pp = B.panels(pn)
    days, n = pn["days"], len(pn["days"])
    XN = minute_x(pp["C"], pp["O"], pp["soc"])
    if not np.allclose(np.column_stack([XN[:, m] for m in CLOCKS]), ob["x"], rtol=0, atol=1e-12, equal_nan=True):
        raise D735Error("right quantity: the minute x_NQ is not D727's x at its clocks")
    P(f"[D735] NQ {n} days; legs ...")
    XL: dict[str, np.ndarray] = {}
    raws: dict[str, Any] = {}
    for r in PRICE_LEGS:
        pl = T.load_root(r, data_root)
        Xr = minute_x(pl["C"], pl["O"], pl["soc"])
        XL[r] = align_rows(pl["days"], Xr, days)
        js = [int(v) for v in rng.integers(0, n, 50)]
        join_audit(pl["days"], Xr, days, XL[r], js)
        try:
            join_audit(pl["days"], Xr, np.roll(days, 1), XL[r], js)
        except D735Error:
            pass
        else:
            raise D735Error(f"{r}: a shifted join did not fire the audit")
        raws[r] = pl
    with np.errstate(invalid="ignore"):
        XL["EQ"] = (XL["ES"] + XL["YM"] + XL["RTY"]) / 3.0
    tk = tick_leg(days)
    XL["TICK"] = tk["X"]
    legs = [lg for lg in LEGS if lg != "TICK" or tk["days_joined"] >= TICK_MIN_DAYS]
    P(f"[D735] leg days: { {lg: int(np.isfinite(XL[lg][:, M_LO]).sum()) for lg in LEGS} }")
    spreads = {lg: spread(XN, XL[lg]) for lg in legs}
    # lag audit of the trigger: a second implementation from the raw rows (and the extracted TICK minutes)
    raw_nq = pn["raw"]
    mins = [T.hhmm(m) for m in range(NMIN)]
    for lg in legs:
        m0, D = trigger(spreads[lg]["Z"], spreads[lg]["S"], 1.0)
        cand = np.flatnonzero(m0 >= 0)
        smp = rng.choice(cand, min(60, len(cand)), replace=False)
        fired = False
        for dd in smp:
            day = days[dd]
            rn = raw_nq[raw_nq["day"] == day].set_index("hhmm")["close"].reindex(mins).ffill().to_numpy(float)
            xn = (rn - pp["O"][dd]) / pp["soc"][dd]
            if lg in PRICE_LEGS or lg == "EQ":
                parts = []
                for r in (PRICE_LEGS if lg == "EQ" else (lg,)):
                    pl = raws[r]
                    i = int(np.flatnonzero(pl["days"] == day)[0])
                    rr = pl["raw"][pl["raw"]["day"] == day].set_index("hhmm")["close"].reindex(mins).ffill().to_numpy(float)
                    parts.append((rr - pl["O"][i]) / pl["soc"][i])
                xl = np.mean(parts, axis=0)
            else:
                si = int(np.flatnonzero(tk["sessions"] == day)[0])
                row = tk["M"][si]
                acc, run_v, xl = 0.0, 0.0, np.zeros(NMIN)
                for b in range(NMIN):
                    if math.isfinite(row[b]):
                        run_v = float(row[b])
                    acc += run_v
                    xl[b] = acc / tk["sig"][dd]
            # sigma_s from the prior 20 NQ days' end-of-day spread, by a loop
            prev = [spreads[lg]["S"][q, NMIN] for q in range(max(0, dd - 20), dd)]
            prev = [v for v in prev if math.isfinite(v)]
            sig_s = math.sqrt(sum(v * v for v in prev) / len(prev)) if len(prev) >= 15 else float("nan")
            if not math.isclose(sig_s, spreads[lg]["sig"][dd], rel_tol=1e-9):
                raise D735Error(f"lag: {lg} sigma_s at {day} is not the prior 20 days'")
            mm, DD = trigger_second(xn, xl, sig_s, 1.0)
            if mm != m0[dd] or DD != D[dd]:
                raise D735Error(f"lag: {lg} at {day}: the second implementation triggers at {mm}/{DD}, the runner {m0[dd]}/{D[dd]}")
            mc, Dc = trigger_second(xn, xl, sig_s, 1.0, lead=1)
            if mc != m0[dd] or Dc != D[dd]:
                fired = True
        if not fired:
            raise D735Error(f"{lg}: the one-bar-lead canary did not fire")
    P("[D735] lag audits passed; E1 tables ...")
    G = {"1s": e1_tables(pp, 1.0), "none": e1_tables(pp, math.inf), "half": e1_tables(pp, 0.5)}
    for st, mult in (("1s", 1.0), ("none", math.inf), ("half", 0.5)):
        for _ in range(40):
            dd, mm = int(rng.integers(0, n)), int(rng.integers(M_LO, M_HI + 1))
            for DD in (1.0, -1.0):
                a = e1_loop(pp, dd, mm, DD, mult)
                b = float(g_at(G[st], np.array([dd]), np.array([mm]), np.array([DD]))[0])
                if not math.isclose(a, b, rel_tol=0, abs_tol=1e-9):
                    raise D735Error(f"E1 table {st} at ({dd},{mm},{DD}): {b} against the loop's {a}")
    # the mechanism, per leg
    P("[D735] S1 ...")
    beta727 = np.array([c_["beta"] for c_ in ka["clocks"]])
    mech_out, fits, gammas = {}, {}, {}
    for lg in legs:
        fw = fw_design(XN, XL[lg])
        d_hat, b_hat, t_cl = fw_delta(fw["x"], fw["y"], fw["e"], cluster_t=True)
        null = fw_null(fw["x"], fw["y"], fw["e"])
        if not math.isclose(fw_delta(fw["x"], fw["y"], np.roll(fw["e"], 0, axis=0)), d_hat, rel_tol=0, abs_tol=1e-12):
            raise D735Error(f"{lg}: the FW null's offset 0 is not delta-hat")
        fits[lg] = per_clock_fit(fw["x"], fw["y"], fw["e"])
        gammas[lg] = fw["gamma"]
        mech_out[lg] = {"delta": d_hat, "beta": b_hat, "t_clustered": t_cl, "rotation": rot(d_hat, null),
                        "delta_by_clock": [{"t": T.hhmm(m), "beta": fits[lg][j][0], "delta": fits[lg][j][1]}
                                           for j, m in enumerate(CLOCKS)]}
    hp = holm({lg: mech_out[lg]["rotation"]["p_low"] for lg in legs})
    mech = {}
    for lg in legs:
        r = mech_out[lg]
        r["holm_p_low"] = hp[lg]
        mech[lg] = bool(r["rotation"]["p_low"] <= 0.05 and r["t_clustered"] <= -2 and hp[lg] <= 0.05)
        r["MECHANISM"] = mech[lg]
    # D727's minute follow (SAME TRADE) and NQ F2's daily (the component line)
    zN = XN / np.sqrt(np.maximum(np.arange(NMIN + 1), 1) / NMIN)[None, :]
    seg = np.abs(zN[:, M_LO:M_HI + 1]) >= 1.0
    fm0 = np.where(seg.any(axis=1), seg.argmax(axis=1) + M_LO, -1)
    fD = np.where(fm0 >= 0, np.sign(XN[np.arange(n), np.clip(fm0, 0, None)]), 0.0)
    fm0 = np.where(fD != 0, fm0, -1)
    fd = np.flatnonzero(fm0 >= 0)
    fg = np.full(n, np.nan)
    fg[fd] = g_at(G["none"], fd, fm0[fd], fD[fd])
    _, follow_daily = F.book(np.where(np.isfinite(fg), 1.0, 0.0), fg, cost, days)
    f2_, _ = Z.build_f2()
    f2_daily = f2_.groupby("day")["net1"].sum().reindex(pd.Index(days)).fillna(0.0).to_numpy()
    ctx = {"XN": XN, "XL": XL, "days": days, "n": n, "cost": cost, "spreads": spreads, "G": G, "pp": pp,
           "soc": pp["soc"], "fits": fits, "gamma": gammas, "beta727": beta727, "follow_daily": follow_daily,
           "follow_m0": fm0, "follow_D": fD, "f2_daily": f2_daily}
    P("[D735] cells ...")
    jobs = [(lg, k, st) for lg in legs for k in KS for st in STOPS]
    with ThreadPoolExecutor(max_workers=6) as ex:
        res = list(ex.map(lambda a: score_cell(ctx, *a), jobs))
    cells = {cell_key(*a): r for a, r in zip(jobs, res)}
    fam = np.nanmax(np.column_stack([c["_null_mean"] for c in cells.values()]), axis=1)
    fam_p95 = float(np.quantile(fam[np.isfinite(fam)], 0.95))
    hc = holm({k_: c["C2a_mean"]["p_high"] for k_, c in cells.items()})
    for k_, c in cells.items():
        c["holm_p"] = hc[k_]
        readings(c, cost, mech, fam_p95)
    pk = cell_key(*PRIMARY)
    pc = cells[pk]
    # the primary's MFE / MAE
    d, m0d, Dd, g = pc["_trades"]
    mfe = {}
    for h in (15, 30, 60, None):
        a_, b_ = [], []
        for dd, mm, DD in zip(d, m0d, Dd):
            last = NMIN - 1 if h is None else min(mm + h - 1, NMIN - 1)
            ent = pp["Op"][dd, mm]
            hi_, lo_ = pp["H"][dd, mm:last + 1], pp["L"][dd, mm:last + 1]
            if DD > 0:
                a_.append((hi_.max() - ent) * USD)
                b_.append((lo_.min() - ent) * USD)
            else:
                a_.append((ent - lo_.min()) * USD)
                b_.append((ent - hi_.max()) * USD)
        mfe["close" if h is None else str(h)] = {"mean_mfe": float(np.mean(a_)), "mean_mae": float(np.mean(b_))}
    pc["mfe_mae"] = mfe
    for c in cells.values():
        for kk in ("_daily", "_null_mean", "_trades"):
            c.pop(kk, None)
    any_go = [k_ for k_, c in cells.items() if c["GO"]]
    pmr = pc["matched_rows"]
    stop_axis = (pc["reading"].endswith(("NOTHING", "DRIFT ONLY")) and pmr["gain"] + 2 * pmr["se"] < 2 * cost
                 and not any(mech.values()) and not any_go)
    out = {"spec": "D735-STAGE-0-PRE-REG-nq-breaks-from-the-market.md (with D735-A1)",
           "seal": f"nothing on or after {Z.CUT24}", "days": n, "cost": cost, "legs": legs,
           "leg_days": {lg: int(np.isfinite(XL[lg][:, M_LO]).sum()) for lg in LEGS},
           "tick": {"sessions_extracted": int(len(tk["sessions"])), "coverage_median": float(np.median(tk["cov"])),
                    "days_joined": tk["days_joined"]},
           "S1_mechanism": mech_out, "family_p95": fam_p95, "cells": cells, "primary": pk,
           "primary_reading": pc["reading"], "GO_cells": any_go,
           "close_axis_proposed": bool(stop_axis), "wall_min": (time.time() - t0) / 60}
    OUT.write_text(json.dumps(out, indent=1, default=Z._json) + "\n", encoding="utf-8", newline="\n")
    P(f"[D735] primary {pk}: {pc['reading']}; MECHANISM { {lg: mech[lg] for lg in legs} }; GO cells {any_go}; "
      f"{out['wall_min']:.1f} min")
    return 0


# ================================================================================ self-test (synthetic only)
def selftest() -> int:
    fails: list[str] = []
    rng = np.random.default_rng(3)
    # 1) the FW null's size and power on simulated days (common factor + NQ's own part + the leg's own part)
    def world(nd: int, plant: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        f = np.cumsum(rng.normal(0, 0.04, (nd, NMIN)), axis=1)
        eps = rng.normal(0, 0.025, (nd, NMIN))
        i = np.zeros((nd, NMIN))
        acc = np.zeros(nd)
        for t in range(NMIN):                    # NQ's own part: momentum at rate `plant` a minute (0 = a walk)
            acc = acc * (1.0 + plant) + eps[:, t]
            i[:, t] = acc
        l = np.cumsum(rng.normal(0, 0.02, (nd, NMIN)), axis=1)
        XNs = np.zeros((nd, NMIN + 1))
        XLs = np.zeros((nd, NMIN + 1))
        XNs[:, 1:] = f + i
        XLs[:, 1:] = f + l
        return XNs, XLs, None

    fp = tp = 0
    for w in range(100):
        a, b_, _ = world(300, 0.0)
        fw = fw_design(a, b_)
        if rot(fw_delta(fw["x"], fw["y"], fw["e"]), fw_null(fw["x"], fw["y"], fw["e"]))["p_low"] <= 0.05:
            fp += 1
        a, b_, _ = world(300, 0.003)
        fw = fw_design(a, b_)
        if rot(fw_delta(fw["x"], fw["y"], fw["e"]), fw_null(fw["x"], fw["y"], fw["e"]))["p_low"] <= 0.05:
            tp += 1
    if fp > 10:
        fails.append(f"the FW null fired on {fp}/100 null worlds")
    if tp < 90:
        fails.append(f"the FW null fired on only {tp}/100 planted worlds")
    # 2) the E1 table equals the loop; a gapped stop fills at the open less a tick; sign and mirror in money
    nd = 6
    base = 100 + np.cumsum(rng.normal(0, 0.5, (nd, NMIN)), axis=1)
    C = base.copy()
    Op = np.column_stack([C[:, 0], C[:, :-1]])
    Hh, Ll = np.maximum(Op, C) + 0.25, np.minimum(Op, C) - 0.25
    pp = {"Op": Op, "H": Hh, "L": Ll, "C": C, "O": Op[:, 0].copy(), "soc": np.full(nd, 8.0)}
    pp["C"][0, :] = np.linspace(100, 130, NMIN)                       # a day that rises: a long pays
    pp["Op"][0] = np.r_[100.0, pp["C"][0, :-1]]
    pp["H"][0], pp["L"][0] = np.maximum(pp["Op"][0], pp["C"][0]) + 0.1, np.minimum(pp["Op"][0], pp["C"][0]) - 0.1
    Gt = {st: e1_tables(pp, mult) for st, mult in (("1s", 1.0), ("none", math.inf), ("h", 0.5))}
    for st, mult in (("1s", 1.0), ("none", math.inf), ("h", 0.5)):
        for dd in range(nd):
            for mm in (M_LO, 100, M_HI):
                for DD in (1.0, -1.0):
                    if not math.isclose(e1_loop(pp, dd, mm, DD, mult),
                                        float(g_at(Gt[st], np.array([dd]), np.array([mm]), np.array([DD]))[0]), abs_tol=1e-9):
                        fails.append(f"the E1 table {st} differs from the loop at ({dd},{mm},{DD})")
    gl = float(g_at(Gt["1s"], np.array([0]), np.array([M_LO]), np.array([1.0]))[0])
    gs = float(g_at(Gt["1s"], np.array([0]), np.array([M_LO]), np.array([-1.0]))[0])
    if not (gl > 0 and gs < 0):
        fails.append("sign: on a rising day the long did not pay or the mirror did not lose")
    pg = {k: v.copy() for k, v in pp.items()}
    pg["Op"][1, 50] = pg["Op"][1, 40] - 100.0                        # a gap through any stop
    pg["L"][1, 50] = pg["Op"][1, 50] - 0.1
    pg["H"][1, 50] = pg["Op"][1, 50] + 0.1
    pg["L"][1, 40:50] = np.minimum(pg["L"][1, 40:50], pg["Op"][1, 40:50])
    pg["L"][1, 40:50] = np.maximum(pg["L"][1, 40:50], pg["Op"][1, 40] - 1.0)
    Gg = e1_tables(pg, 1.0)
    want = (pg["Op"][1, 50] - TICK - pg["Op"][1, 40]) * USD
    if not math.isclose(float(Gg["up"][1, 40]), want, abs_tol=1e-9):
        fails.append("a gapped stop did not fill at the open less a tick")
    # 3) the trigger and its second implementation; the one-bar-lead canary fires
    XNs = np.zeros((40, NMIN + 1))
    XLs = np.zeros((40, NMIN + 1))
    XNs[:, 1:] = np.cumsum(rng.normal(0, 0.05, (40, NMIN)), axis=1)
    XLs[:, 1:] = np.cumsum(rng.normal(0, 0.05, (40, NMIN)), axis=1)
    sp = spread(XNs, XLs)
    m0, D = trigger(sp["Z"], sp["S"], 1.0)
    fired, checked = False, 0
    for dd in range(20, 40):
        if m0[dd] < 0 or not math.isfinite(sp["sig"][dd]):
            continue
        mm, DD = trigger_second(XNs[dd, 1:], XLs[dd, 1:], float(sp["sig"][dd]), 1.0)
        checked += 1
        if mm != m0[dd] or DD != D[dd]:
            fails.append(f"the trigger's second implementation disagrees on synthetic day {dd}")
        mc, Dc = trigger_second(XNs[dd, 1:], XLs[dd, 1:], float(sp["sig"][dd]), 1.0, lead=1)
        if mc != m0[dd] or Dc != D[dd]:
            fired = True
    if checked == 0:
        fails.append("no synthetic trigger to audit")
    if not fired:
        fails.append("the one-bar-lead canary did not fire")
    # 4) the date join and its shifted canary
    days = np.array([f"2019-{1 + i // 28:02d}-{1 + i % 28:02d}" for i in range(60)])
    src = rng.normal(0, 1, (55, 4))
    got = align_rows(days[5:], src, days)
    join_audit(days[5:], src, days, got, list(range(60)))
    try:
        join_audit(days[5:], src, np.roll(days, 1), got, list(range(10, 60)))
        fails.append("a shifted join did not fire")
    except D735Error:
        pass
    # 5) C2b at offset 0 reproduces the observed trades (the right-quantity check), C2a is a different quantity
    n6 = nd
    XN6 = np.zeros((n6, NMIN + 1))
    XN6[:, 1:] = (pp["C"] - pp["O"][:, None]) / pp["soc"][:, None]
    S6 = XN6 - XN6[::-1]
    d_ = np.arange(n6)
    m_ = np.full(n6, 120)
    D_ = np.sign(S6[d_, m_])
    keep = D_ != 0
    d_, m_, D_ = d_[keep], m_[keep], D_[keep]
    obs = float((g_at(Gt["1s"], d_, m_, D_) - 4.07).mean())
    c2b0 = timing_null(Gt["1s"], d_, m_, S6, XN6, 4.07, np.array([0]))
    if not math.isclose(float(c2b0["mean_net"][0]), obs, abs_tol=1e-9):
        fails.append("C2b's offset 0 does not reproduce the observed trades")
    if fails:
        P("SELFTEST FAILED:", fails)
        return 1
    P(f"SELFTEST OK: the FW null fires on {fp}/100 null worlds and {tp}/100 planted; the E1 tables equal the loop; a "
      "rising day pays long and loses short; a gapped stop fills at the open less a tick; the trigger's second "
      "implementation agrees and its one-bar-lead canary fires; a shifted join fires; C2b's offset 0 reproduces")
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
            raise D735Error(f"{OUT.name} exists: D735 runs once")
        return run(a.data_root)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
