"""D686 (development) -- thirteen profit projections, overlays and lags on D685's month-end mechanism
(pre-registration: docs/decisions/D686-PRE-REG-thirteen-projections-overlays-and-lags-for-d685.md).

    python scripts/build_d686_es_1545.py --data-root "<main>/data"                  # system python, L1's input
    uv run python scripts/stage0_d686_month_end_variants.py --selftest
    uv run python scripts/stage0_d686_month_end_variants.py --run --data-root "<main checkout>/data"

Every variant is a (M x W) position matrix on month windows. The null rotates the SIGNAL side (the lagged drift and
everything computed from it) by k months against the TIME side (returns, sigma, volume, GEX, calendar, quarter-end,
window position), and every prior-only estimate is refit inside each rotation.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d686_month_end_variants.json"
ES1545 = REPO / "data" / "d686_es_1545.csv.gz"
D685_JSON = REPO / "data" / "d685_month_end_rebalancing.json"


def _load(name, file):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


B = _load("d685b", "stage0_d685_month_end_rebalancing.py")        # D685's base, imported unchanged

LAG = B.LAG
BURN_IN = 24
MIN_GROUP = 20
K_EP = 2.0
THRESH = 0.01
SIG_N, DV_N, DV_MIN = 20, 60, 10
SIGBAR_N, O1_CAP = 252, 3.0
HOLD = 10
L1_FIRST = "2016-01"
MONTHS_A, MONTHS_AV = 14.0, 32.5
VARIANTS = ("P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "O1", "O2", "O3", "L1", "L2")


class GateError(AssertionError):
    pass


def P(*a, **k):
    print(*a, **k, flush=True)


# ------------------------------------------------------------------ prior-only estimation
def sigma_prior(sl: np.ndarray) -> np.ndarray:
    """sigma_s per month from the prior 36 months' lagged window signals (at least 12), as D685."""
    M = sl.shape[0]
    out = np.full(M, np.nan)
    for m in range(M):
        lo = max(0, m - B.Z_PRIOR)
        if m - lo >= B.Z_MIN:
            out[m] = float(np.std(sl[lo:m].ravel(), ddof=1))
    return out


def pi_prior(g: np.ndarray, X: np.ndarray, grp: np.ndarray | None = None) -> np.ndarray:
    """Through-origin pass-through of g on X from months STRICTLY before m (M x W; NaN where not estimable).
    With grp (M x W bool), each cell gets its own group's pass-through: grp True and False are two groups."""
    fin = np.isfinite(X) & np.isfinite(g)
    Xf = np.where(fin, X, 0.0)
    gf = np.where(fin, g, 0.0)
    has = fin.any(axis=1).astype(float)
    months_before = np.concatenate([[0.0], np.cumsum(has)[:-1]])
    out = np.full(X.shape, np.nan)
    groups = [np.ones(X.shape, bool)] if grp is None else [grp, ~grp]
    for G in groups:
        num = np.concatenate([[0.0], np.cumsum((gf * Xf * G).sum(axis=1))[:-1]])
        den = np.concatenate([[0.0], np.cumsum((Xf * Xf * G).sum(axis=1))[:-1]])
        cnt = np.concatenate([[0.0], np.cumsum((fin & G).sum(axis=1))[:-1]])
        with np.errstate(invalid="ignore", divide="ignore"):
            pi_m = np.where((months_before >= BURN_IN) & (den > 0) & ((grp is None) | (cnt >= MIN_GROUP)), num / den, np.nan)
        out = np.where(G, pi_m[:, None], out)
    return out


def audit_prior_only(pi: np.ndarray, g: np.ndarray, X: np.ndarray, months) -> None:
    """The pass-through used in month m must equal one rebuilt from months strictly before m."""
    for m in months:
        want = pi_prior_loop(g, X, m)
        got = pi[m, 0]
        if not ((np.isnan(want) and np.isnan(got)) or abs(want - got) <= 1e-12 * max(1.0, abs(want))):
            raise GateError(f"[PRIOR-ONLY] month {m}: pass-through {got!r} != prior-only rebuild {want!r}")


def audit_l1_bars(bars) -> None:
    """L1's price must be strictly before 15:45:00: bar 404 (15:44-15:45) or earlier."""
    if len(bars) and int(np.max(bars)) >= 405:
        raise GateError("[L1 CAUSALITY] a 15:45 price comes from bar 405 or later")


def pi_prior_loop(g, X, m) -> float:
    """Second path for the prior-only audit: explicit loop over months strictly before m."""
    num = den = 0.0
    months = 0
    for mm in range(m):
        fin = np.isfinite(X[mm]) & np.isfinite(g[mm])
        if fin.any():
            months += 1
        for j in range(X.shape[1]):
            if fin[j]:
                num += g[mm, j] * X[mm, j]
                den += X[mm, j] * X[mm, j]
    return num / den if months >= BURN_IN and den > 0 else float("nan")


# ------------------------------------------------------------------ books
def book(pos: np.ndarray, move_usd: np.ndarray, cost_rt: float, n_days: int) -> dict:
    """Net per window day (M x W), with half a round trip per contract changed; a run's exit to its last day."""
    pos = np.where(np.isfinite(pos), pos, 0.0)
    gross = pos * np.where(np.isfinite(move_usd), move_usd, 0.0)
    M, W = pos.shape
    cost = np.zeros_like(pos)
    padded = np.concatenate([np.zeros((M, 1)), pos, np.zeros((M, 1))], axis=1)
    for i in range(W + 1):
        d = np.abs(padded[:, i + 1] - padded[:, i]) * 0.5 * cost_rt
        if i < W:
            to_day = np.where(pos[:, i] != 0, i, i - 1)
        else:
            to_day = np.full(M, W - 1)
        for day in np.unique(to_day[d > 0]):
            if day < 0:
                continue
            sel = (to_day == day) & (d > 0)
            cost[sel, day] += d[sel]
    net = gross - cost
    tot, sq = float(net.sum()), float((net ** 2).sum())
    mean = tot / n_days
    var = (sq - n_days * mean * mean) / (n_days - 1)
    sh = mean / math.sqrt(var) * math.sqrt(252) if var > 0 else float("nan")
    flat = net.ravel()
    return {"sharpe": sh, "t": B.nw_mean(flat)["t"], "net_sum": tot, "gross_sum": float(gross.sum()),
            "traded": int((pos != 0).sum()), "_net": net, "_gross": gross}


# ------------------------------------------------------------------ data
def build(data_root: Path) -> dict:
    import pandas as pd
    D = B.load(data_root)
    days = D["days"]
    r_es, _, _, sprev_es, move_es = D["R"]["ES"]
    r_zn = D["R"]["ZN"][0]
    r_es0 = np.where(np.isfinite(r_es), r_es, 0.0)
    r_zn0 = np.where(np.isfinite(r_zn), r_zn, 0.0)
    blocks_all = B.month_blocks(days)
    bi = [i for i, b in enumerate(blocks_all) if B.FIRST_MONTH <= days[b[0]][:7] <= B.LAST_MONTH]
    blocks = [blocks_all[i] for i in bi]
    M = len(blocks)
    s = B.drift_signal(r_es0, r_zn0, blocks_all)
    T5 = np.array([b[len(b) - 5:] for b in blocks])
    T10 = np.array([b[len(b) - 10:] for b in blocks])
    # O3 hold days: the next month's first 10 trading days; the window's last month has none (would read 2024)
    H = np.full((M, HOLD), -1)
    for m, i in enumerate(bi):
        if i + 1 < len(blocks_all) and days[blocks_all[i + 1][0]] < B.CUTOFF:
            nb = blocks_all[i + 1][:HOLD]
            H[m, :len(nb)] = nb
    # sigma20 and DV60 through o-2, and S at o-2
    n = len(days)
    sig20 = np.full(n, np.nan)
    for t in range(SIG_N, n):
        sig20[t] = float(np.std(r_es0[t - SIG_N + 1:t + 1], ddof=1))
    fx = data_root / "fixtures"
    vc = [f"h{h:02d}_v" for h in range(9, 17)]
    bh = pd.read_csv(fx / "fut_breadth_hourly.csv.gz", usecols=["root", "day"] + vc)
    bh = bh[(bh.root == "ES") & (bh.day < B.CUTOFF)]
    B.guard_window(bh["day"])
    vol = bh.set_index("day")[vc].apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=1)
    vol = vol.groupby(level=0).sum(min_count=1).reindex(days).to_numpy(float)
    vol = np.where(vol > 0, vol, np.nan)
    dv60 = np.full(n, np.nan)
    for t in range(DV_N, n):
        w = vol[t - DV_N + 1:t + 1]
        if np.isfinite(w).sum() >= DV_MIN:
            dv60[t] = float(np.nanmedian(w))
    cal = pd.read_csv(fx / "cme_session_calendar.csv.gz", usecols=["root", "day", "fomc", "cpi", "empsit"])
    cal = cal[(cal.root == "ES") & (cal.day < B.CUTOFF)].set_index("day")
    B.guard_window(cal.index)
    macro = np.zeros(n, bool)
    cc = cal.reindex(days)
    for c in ("fomc", "cpi", "empsit"):
        macro |= cc[c].map(lambda v: str(v).lower() in ("true", "1", "1.0")).to_numpy(bool)
    gex = pd.read_csv(data_root / "raw" / "squeezemetrics" / "DIX.csv", usecols=["date", "gex"]).sort_values("date")
    gex = gex[gex.date < B.CUTOFF]
    gd, gv = gex["date"].to_numpy(), gex["gex"].to_numpy(float)

    def gex_before(day_idx):
        pos = np.searchsorted(gd, days[day_idx], side="left") - 1
        return np.where(pos >= 0, gv[np.clip(pos, 0, None)], np.nan)

    t2 = T5 - LAG                                                  # the o-2 index for each outcome day
    ctx = {"days": days, "M": M, "blocks": blocks, "months": [days[b[0]][:7] for b in blocks],
           "n_days": int(blocks[-1][-1] - blocks[0][0] + 1),
           "s": s, "T5": T5, "T10": T10, "H": H,
           "y5": r_es[T5] * 1e4, "mv5": move_es[T5], "sp5": sprev_es[T5],
           "y10": r_es[T10] * 1e4, "mv10": move_es[T10], "sp10": sprev_es[T10],
           "sig20_2": sig20[t2], "S_2": sprev_es[T5 - 1], "dv60_2": dv60[t2],
           "gex_1": gex_before(T5 - 1), "macro5": macro[T5],
           "qe5": np.array([[int(days[b[0]][5:7]) % 3 == 0] * 5 for b in blocks]),
           "win_pos": np.tile(np.arange(5), (M, 1)),
           "vol_cov": {str(y): int(np.isfinite(vol[[d[:4] == str(y) for d in days]]).sum()) for y in range(2010, 2024)}}
    Hm = np.where(H >= 0, H, 0)
    ctx["mvH"] = np.where(H >= 0, move_es[Hm], np.nan)
    ctx["yH"] = np.where(H >= 0, r_es[Hm] * 1e4, np.nan)
    # sigma-bar for O1: the median of sigma20 over the prior 252 trading days, at o-2
    sigbar = np.full(n, np.nan)
    for t in range(SIG_N + SIGBAR_N, n):
        sigbar[t] = float(np.nanmedian(sig20[t - SIGBAR_N:t]))
    ctx["sigbar_2"] = sigbar[t2]
    # L1: ES through 15:45 on o-1 (the held contract's settlement at o-2 as the base), ZN through its o-1 settlement
    l1 = pd.read_csv(ES1545)
    B.guard_window(l1["day"])
    audit_l1_bars(l1["bar"].to_numpy())
    ctx["es1545_sha256"] = hashlib.sha256(ES1545.read_bytes()).hexdigest()
    strip = pd.read_csv(fx / "fut_settle_strip.csv.gz")
    strip = strip[(strip.root == "ES") & (strip.ref < B.CUTOFF)]
    B.guard_window(strip["ref"])
    Sx = strip.set_index(["contract", "ref"])["settle"]
    l1 = l1.set_index("day")
    l1_months = [m for m in range(M) if ctx["months"][m] >= L1_FIRST]
    s1545 = np.full((M, 5), np.nan)
    pos_of = {d: i for i, d in enumerate(days)}
    early = 0
    for m in l1_months:
        b = blocks[m]
        start = b[0]
        for j, o in enumerate(T5[m]):
            d1 = days[o - 1]
            if d1 not in l1.index:
                continue
            row = l1.loc[d1]
            early += int(row["bar"] < 404)
            base = Sx.get((row["contract"], days[o - 2]), np.nan)
            part = math.log(row["close"]) - math.log(base) if np.isfinite(base) else np.nan
            ge = math.exp(float(np.sum(r_es0[start:o - 1])) + part)          # settlements through o-2, then to 15:45
            gb = math.exp(float(np.sum(r_zn0[start:o])))                     # ZN through its o-1 settlement
            s1545[m, j] = B.W_EQ * ge / (B.W_EQ * ge + (1 - B.W_EQ) * gb) - B.W_EQ
    ctx["s1545"] = s1545
    ctx["l1_rows"] = np.array(l1_months)
    ctx["l1_early_close_bars"] = early
    ctx["l1_n_days"] = int(blocks[-1][-1] - blocks[l1_months[0]][0] + 1)
    return ctx


# ------------------------------------------------------------------ the variants
def signal_side(ctx):
    s = ctx["s"]
    return {"sl5": s[ctx["T5"] - LAG], "sl10": s[ctx["T10"] - LAG], "s1545": ctx["s1545"]}


def rotate(sig, k, l1_rows):
    out = {"sl5": np.roll(sig["sl5"], k, axis=0), "sl10": np.roll(sig["sl10"], k, axis=0)}
    M1 = len(l1_rows)
    k1 = 0 if k == 0 else 2 + ((k - 2) % (M1 - 3))
    s1 = sig["s1545"].copy()
    s1[l1_rows] = np.roll(sig["s1545"][l1_rows], k1, axis=0)
    out["s1545"] = s1
    return out


def run_all(ctx, sig, rt, usd_pt, keep=False) -> dict:
    sl5 = sig["sl5"]
    sgn = -np.sign(sl5)
    sig_s = sigma_prior(sl5)
    z = sl5 / sig_s[:, None]
    az = np.abs(z)
    g = sgn * ctx["y5"]
    notional = usd_pt * ctx["sp5"]                                 # $ per 1.0 of return, at entry
    mv5 = ctx["mv5"] * usd_pt
    two_c = K_EP * rt

    def usd(G_bp):
        return G_bp / 1e4 * notional

    X1 = ctx["sig20_2"] * np.sqrt(np.abs(sl5) * ctx["S_2"] / ctx["dv60_2"])
    thr = np.abs(sl5) >= THRESH
    short = np.isfinite(ctx["gex_1"]) & (ctx["gex_1"] < 0)
    has_g = np.isfinite(ctx["gex_1"])
    Gp = {}
    pi0 = pi_prior(g, az)
    Gp["P0"] = pi0 * az
    pi1 = pi_prior(g, X1)
    Gp["P1"] = pi1 * X1
    Gp["P2"] = pi_prior(g, az, ctx["qe5"]) * az
    X3 = np.where(thr, az, np.nan)
    G3 = pi_prior(g, X3) * X3
    Gp["P3"] = G3
    X4 = np.where(has_g, az, np.nan)
    Gp["P4"] = pi_prior(g, X4, short) * X4
    pi5 = np.full(az.shape, np.nan)
    for j in range(5):
        Xj = np.where(ctx["win_pos"] == j, az, np.nan)
        pj = pi_prior(g, Xj)
        pi5 = np.where(ctx["win_pos"] == j, pj, pi5)
    Gp["P5"] = pi5 * az

    def ratio(grp):
        a = pi_prior(g, np.where(grp, X1, np.nan))
        b = pi_prior(g, np.where(~grp, X1, np.nan))
        cnt_ok = np.isfinite(a) & np.isfinite(b) & (b > 0)
        r = np.where(cnt_ok, np.clip(a / np.where(cnt_ok, b, 1.0), 0.0, 5.0), 1.0)
        return np.where(grp, r, 1.0)
    X6 = X1 * ratio(ctx["qe5"]) * ratio(thr) * ratio(short & has_g)
    Gp["P6"] = pi_prior(g, X6) * X6
    usd_parts = []
    for p in ("P1", "P2", "P3", "P4", "P5"):
        u = usd(Gp[p])
        if p == "P3":
            u = np.where(thr, u, 0.0)
        usd_parts.append(u)
    stack = np.stack(usd_parts)
    with np.errstate(invalid="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)          # an all-NaN day has no projection: no trade
        G7usd = np.nanmean(np.where(np.isfinite(stack), stack, np.nan), axis=0)

    res = {}
    for p in ("P0", "P1", "P2", "P3", "P4", "P5", "P6"):
        Gu = usd(Gp[p])
        pos = np.where(np.isfinite(Gu) & (Gu >= two_c) & (Gp[p] > 0), sgn, 0.0)
        res[p] = book(pos, mv5, rt, ctx["n_days"])
    pos = np.where(np.isfinite(G7usd) & (G7usd >= two_c), sgn, 0.0)
    res["P7"] = book(pos, mv5, rt, ctx["n_days"])
    size = np.where(np.isfinite(ctx["sigbar_2"] / ctx["sig20_2"]),
                    np.minimum(O1_CAP, ctx["sigbar_2"] / ctx["sig20_2"]), 1.0)
    res["O1"] = book(sgn * size, mv5, rt, ctx["n_days"])
    res["O2"] = book(np.where(ctx["macro5"], 0.0, sgn), mv5, rt, ctx["n_days"])
    hold_pos = np.where(np.isfinite(ctx["mvH"]), sgn[:, -1:], 0.0)
    res["O3"] = book(np.concatenate([sgn, hold_pos], axis=1),
                     np.concatenate([mv5, ctx["mvH"] * usd_pt], axis=1), rt, ctx["n_days"])
    r1 = ctx["l1_rows"]
    s1 = sig["s1545"][r1]
    res["L1"] = book(np.where(np.isfinite(s1), -np.sign(s1), 0.0), mv5[r1], rt, ctx["l1_n_days"])
    res["L2"] = book(-np.sign(sig["sl10"]), ctx["mv10"] * usd_pt, rt, ctx["n_days"])
    res["_base"] = book(sgn, mv5, rt, ctx["n_days"])
    res["_base_L1window"] = book(sgn[r1], mv5[r1], rt, ctx["l1_n_days"])
    if keep:
        res["_aux"] = {"g": g, "az": az, "z": z, "X1": X1, "pi0": pi0, "sig_s": sig_s}
    else:
        for v in res.values():
            v.pop("_net", None)
            v.pop("_gross", None)
    return res


# ------------------------------------------------------------------ self-test
def do_self_test() -> int:
    rng = np.random.default_rng(678)
    M, W = 60, 5
    g = rng.standard_normal((M, W))
    X = np.abs(rng.standard_normal((M, W)))
    pv = pi_prior(g, X)
    audit_prior_only(pv, g, X, (24, 30, 59))
    # a leaking pass-through: month m's estimate includes month m itself
    num = np.cumsum((g * X).sum(axis=1))
    den = np.cumsum((X * X).sum(axis=1))
    leak = np.where(np.arange(M) >= BURN_IN - 1, num / den, np.nan)[:, None] * np.ones((1, W))
    try:
        audit_prior_only(leak, g, X, (30, 59))
        raise SystemExit("prior-only audit FAILED to fire on a pass-through that includes month m")
    except GateError:
        pass
    P("  prior-only pass-through equals its explicit loop; one that includes month m is caught")
    pos = np.array([[0, 1, 1, 0, -1]], float)
    mv = np.ones((1, 5))
    b = book(pos, mv, 2.0, 5)
    exp_cost = 0.5 * 2 * (1 + 1 + 1 + 1)                           # in at 1, out at 3, in at 4 (short), out at end
    if abs((b["gross_sum"] - b["net_sum"]) - exp_cost) > 1e-12:
        raise SystemExit(f"book cost wrong: {b['gross_sum'] - b['net_sum']} vs {exp_cost}")
    P("  book charges half a round trip per contract changed, exits included")
    B.audit_sign(B.book_position)
    P("  sign audit (D685's) holds")
    B.guard_window(["2023-12-29"])
    try:
        B.guard_window(["2024-01-02"])
        raise SystemExit("window guard FAILED to fire")
    except GateError:
        pass
    except B.GateError:
        pass
    P("  window guard fires on a 2024 row")
    audit_l1_bars(np.array([400, 404]))
    try:
        audit_l1_bars(np.array([404, 405]))
        raise SystemExit("L1 causality audit FAILED to fire on bar 405")
    except GateError:
        pass
    P("  L1 causality audit fires on bar 405")
    P("SELF-TEST PASSED")
    return 0


# ------------------------------------------------------------------ run
def do_run(data_root: Path) -> int:
    t0 = time.perf_counter()
    ctx = build(data_root)
    M = ctx["M"]
    P(f"built: {M} months, {len(ctx['l1_rows'])} L1 months, n_days {ctx['n_days']} (L1 {ctx['l1_n_days']}); "
      f"ES day-volume days by year {ctx['vol_cov']}; L1 early-close bars {ctx['l1_early_close_bars']} "
      f"({time.perf_counter() - t0:.1f}s)")
    mes, es = B.cost_spec("ES", "micro"), B.cost_spec("ES", "full")
    sig = signal_side(ctx)
    obs = run_all(ctx, sig, mes["cost_rt_usd"], mes["usd_per_point"], keep=True)

    # reproduction of D685 and the prior-only audit on the real data
    d685 = json.loads(D685_JSON.read_text(encoding="utf-8"))
    aux = obs["_aux"]
    base_gross_bp = float(np.mean(aux["g"]))
    if base_gross_bp != d685["B2"]["value"]:
        raise GateError(f"[REPRO] base gross {base_gross_bp!r} != D685's {d685['B2']['value']!r}")
    hz = np.isfinite(aux["sig_s"])
    b1 = B.nw_slope(aux["z"][hz].ravel(), ctx["y5"][hz].ravel())
    if b1["beta"] != d685["B1"]["beta"]:
        raise GateError(f"[REPRO] B1 {b1['beta']!r} != D685's {d685['B1']['beta']!r}")
    audit_prior_only(aux["pi0"], aux["g"], aux["az"], (30, 80, M - 1))
    P(f"reproduced D685: base gross {base_gross_bp:+.4f} bp, B1 {b1['beta']:+.4f}; prior-only audit passes")

    ks = [0] + list(range(2, M - 1))
    draws = {v: [] for v in VARIANTS}
    for k in ks[1:]:
        r = run_all(ctx, rotate(sig, k, ctx["l1_rows"]), mes["cost_rt_usd"], mes["usd_per_point"])
        for v in VARIANTS:
            draws[v].append(r[v]["sharpe"])
    r0 = run_all(ctx, rotate(sig, 0, ctx["l1_rows"]), mes["cost_rt_usd"], mes["usd_per_point"])
    for v in VARIANTS:
        if r0[v]["sharpe"] != obs[v]["sharpe"]:
            raise GateError(f"[NULL] rotation k=0 does not reproduce {v}")
    t_null = time.perf_counter() - t0
    fam = np.nanmax(np.array([draws[v] for v in VARIANTS]), axis=0)

    months_win = {v: (len(ctx["l1_rows"]) if v == "L1" else M) for v in VARIANTS}
    table = {}
    for v in VARIANTS:
        d = np.array(draws[v], float)
        o = obs[v]
        own = B.band(o["sharpe"], d[np.isfinite(d)])
        dpass = bool(o["sharpe"] > own["p95"] and o["t"] >= 2.0 and o["traded"] >= 60)
        table[v] = {"sharpe": o["sharpe"], "t": o["t"], "traded": o["traded"], "net_sum": o["net_sum"],
                    "gross_sum": o["gross_sum"], "own_null": own, "D_PASS": dpass,
                    "t_expected_2024_slice": o["t"] * math.sqrt(MONTHS_A / months_win[v]),
                    "t_expected_slice_plus_vault": o["t"] * math.sqrt(MONTHS_AV / months_win[v])}
    best = max(VARIANTS, key=lambda v: obs[v]["sharpe"])
    fam_band = B.band(obs[best]["sharpe"], fam)
    for v in VARIANTS:
        table[v]["beats_family_p95"] = bool(obs[v]["sharpe"] > fam_band["p95"])

    # full ES beside, observed only
    es_obs = run_all(ctx, sig, es["cost_rt_usd"], es["usd_per_point"])
    for v in VARIANTS:
        table[v]["ES_full"] = {"sharpe": es_obs[v]["sharpe"], "t": es_obs[v]["t"], "net_sum": es_obs[v]["net_sum"]}

    # the fade question (P1)
    years = np.array([[int(m[:4])] * 5 for m in ctx["months"]])
    F = ctx["sig20_2"] * np.sqrt(ctx["S_2"] / ctx["dv60_2"])
    fy, ry = {}, {}
    for y in range(2010, 2024):
        sel = (years == y) & np.isfinite(F) & np.isfinite(aux["az"])
        if sel.sum() >= 10:
            fy[y] = float(np.mean(F[sel]))
            ry[y] = float(np.sum(aux["g"][sel]) / np.sum(aux["az"][sel]))
    yy = sorted(fy)
    def ranks(a):
        o_ = np.argsort(np.argsort(a))
        return o_.astype(float)
    rho = float(np.corrcoef(ranks(np.array([fy[y] for y in yy])), ranks(np.array([ry[y] for y in yy])))[0, 1]) if len(yy) > 3 else float("nan")
    f_1315 = np.mean([fy[y] for y in yy if 2013 <= y <= 2015]) if any(2013 <= y <= 2015 for y in yy) else float("nan")
    f_2023 = np.mean([fy[y] for y in yy if 2020 <= y <= 2023])
    fade = {"F_by_year": fy, "realised_gross_per_unit_absz_by_year": ry, "spearman": rho,
            "F_2013_15": float(f_1315), "F_2020_23": float(f_2023),
            "P1_explains_the_fade": bool(rho >= 0.5 and f_2023 < f_1315)}

    # four groups for the best variant and every D-PASS variant; correlation with the MACD arm
    arm = B.load_arm()
    groups = {}
    for v in sorted({best} | {v for v in VARIANTS if table[v]["D_PASS"]}):
        o = obs[v]
        net, gross = o["_net"], o["_gross"]
        traded = (np.abs(gross) > 0) | (net != 0)
        rows_months = ctx["months"] if v != "L1" else [ctx["months"][i] for i in ctx["l1_rows"]]
        per_year = {}
        for i, m in enumerate(rows_months):
            per_year[m[:4]] = per_year.get(m[:4], 0.0) + float(net[i].sum())
        # daily net on the grid for the correlation with the arm
        idx = ctx["T5"] if v not in ("L2", "O3", "L1") else (ctx["T10"] if v == "L2" else ctx["T5"][ctx["l1_rows"]] if v == "L1"
                                                             else np.concatenate([ctx["T5"], ctx["H"]], axis=1))
        daily = np.zeros(len(ctx["days"]))
        ok = idx >= 0
        np.add.at(daily, idx[ok], net[ok])
        pos_of = {d: i for i, d in enumerate(ctx["days"])}
        x = np.array([daily[pos_of[d]] if d in pos_of else 0.0 for d in arm["days"]])
        groups[v] = {"per_traded_day_net": B.dist(net[traded]) if traded.sum() > 3 else None,
                     "per_traded_day_gross": B.dist(gross[traded]) if traded.sum() > 3 else None,
                     "per_year_net": per_year, "profitable_years": int(sum(val > 0 for val in per_year.values())),
                     "max_dd": B.max_dd(net.ravel()), "sortino_daily": None,
                     "corr_with_macd_arm": float(np.corrcoef(x, arm["net"])[0, 1]) if x.std() > 0 else float("nan")}
        # Sortino on the full daily series
        dd = daily[(np.arange(len(daily)) >= ctx["blocks"][0][0]) & (np.arange(len(daily)) <= ctx["blocks"][-1][-1])]
        groups[v]["sortino_daily"] = B.sortino(dd)

    base = {"all": {k: obs["_base"][k] for k in ("sharpe", "t", "traded", "net_sum", "gross_sum")},
            "L1_window": {k: obs["_base_L1window"][k] for k in ("sharpe", "t", "traded", "net_sum", "gross_sum")}}

    # predictions (s.5)
    ov = {v: obs[v]["sharpe"] for v in ("O1", "O2", "O3")}
    dp = [v for v in VARIANTS if table[v]["D_PASS"]]
    pr = {"1_no_variant_clears_family": not any(table[v]["beats_family_p95"] for v in VARIANTS),
          "2_F_falls_but_spearman_below_0.5": bool(f_2023 < f_1315 and rho < 0.5),
          "3_O1_best_overlay": bool(max(ov, key=ov.get) == "O1"),
          "4_O3_raises_sharpe": bool(obs["O3"]["sharpe"] > obs["_base"]["sharpe"]),
          "5_L1_beats_base_on_its_window": bool(obs["L1"]["sharpe"] > obs["_base_L1window"]["sharpe"]),
          "6_P6_at_least_P7": bool(obs["P6"]["sharpe"] >= obs["P7"]["sharpe"]),
          "7_every_DPASS_unconfirmable_alone": all(table[v]["t_expected_2024_slice"] < 1.5 for v in dp)}

    # report
    P(f"\n=== 13 variants (MES; daily net Sharpe; own null over {len(ks) - 1} offsets; null {t_null:.0f}s) ===")
    P(f"  base: Sharpe {base['all']['sharpe']:+.3f} t {base['all']['t']:+.2f}; on L1's window {base['L1_window']['sharpe']:+.3f}")
    P(f"  {'v':<3} {'Sharpe':>7} {'p50':>7} {'p95':>7} {'pct':>6} {'t':>6} {'traded':>6} {'net$':>8} {'D-PASS':>6} "
      f"{'fam':>4} {'tA':>5} {'tA+V':>5} {'ES Sh':>6}")
    for v in VARIANTS:
        x = table[v]
        P(f"  {v:<3} {x['sharpe']:+7.3f} {x['own_null']['p50']:+7.3f} {x['own_null']['p95']:+7.3f} "
          f"{x['own_null']['pct']:6.3f} {x['t']:+6.2f} {x['traded']:6d} {x['net_sum']:8.0f} "
          f"{'YES' if x['D_PASS'] else 'no':>6} {'Y' if x['beats_family_p95'] else '.':>4} "
          f"{x['t_expected_2024_slice']:5.2f} {x['t_expected_slice_plus_vault']:5.2f} {x['ES_full']['sharpe']:+6.3f}")
    P(f"  best {best}: Sharpe {obs[best]['sharpe']:+.3f}; best-of-13 null p50 {fam_band['p50']:+.3f} "
      f"p95 {fam_band['p95']:+.3f}; pct {fam_band['pct']:.3f}")
    P(f"\n=== The fade (P1) ===  Spearman {rho:+.2f}; F 2013-15 {f_1315:.3e} -> 2020-23 {f_2023:.3e}; "
      f"explains the fade: {fade['P1_explains_the_fade']}")
    P("  " + "  ".join(f"{y}: F {fy[y]:.2e} edge {ry[y]:+.2f}" for y in yy))
    P("\n=== Four groups ===")
    for v, gdat in groups.items():
        n_ = gdat["per_traded_day_net"]
        P(f"  {v}: corr arm {gdat['corr_with_macd_arm']:+.3f}; Sortino {gdat['sortino_daily']:+.3f}; maxDD ${gdat['max_dd']:,.0f}; "
          f"profitable years {gdat['profitable_years']}/{len(gdat['per_year_net'])}; per-day net mean {n_['mean']:+.2f} "
          f"median {n_['median']:+.2f} win {n_['win_rate']:.3f} ex-top {n_['mean_ex_top_1pc']:+.2f} "
          f"ex-bottom {n_['mean_ex_bottom_1pc']:+.2f} trimmed {n_['mean_trimmed_1pc_both']:+.2f}")
        P("     per year: " + " ".join(f"{y}:{val:+.0f}" for y, val in gdat["per_year_net"].items()))
    P("\n=== Predictions (D686 s.5) ===")
    for k_, v_ in pr.items():
        P(f"  {k_:<38} {'HELD' if v_ else 'BROKEN'}")
    out = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "pre_registration": "docs/decisions/D686-PRE-REG-thirteen-projections-overlays-and-lags-for-d685.md",
           "development_not_evidence": True, "es1545_sha256": ctx["es1545_sha256"],
           "l1_early_close_bars": ctx["l1_early_close_bars"], "es_day_volume_days_by_year": ctx["vol_cov"],
           "costs": {"MES": mes, "ES": es}, "base": base, "variants": table, "best": best, "family_null": fam_band,
           "fade": fade, "four_groups": groups, "predictions": pr, "offsets": len(ks) - 1,
           "wall_seconds": time.perf_counter() - t0}
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    P(f"\nwrote {OUT.relative_to(REPO)} ({time.perf_counter() - t0:.0f}s)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    if a.selftest:
        return do_self_test()
    if a.run:
        do_self_test()
        return do_run(a.data_root)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
