"""D743 Stage 0: a skip layer for D735's NQ-against-the-market legs. Spec:
docs/decisions/D743-STAGE-0-PRE-REG-skip-busy-nights-and-release-days-on-d735.md, committed before this file existed.

    uv run python scripts/stage0_d743_skip_layer.py --selftest
    uv run python scripts/stage0_d743_skip_layer.py --run          # once -> data/stage0_d743_skip_layer.json

Cells: YM k1.0 1 sigma_rem (D737's own `cell`, its known answer) and EQ k1.5 1 sigma_rem (D735's functions, its JSON
answer), on panels from D738's `read_cut`. Vetoes: V1 NQ's busy two-way overnight (D671's on_range and walk-forward
tiers, p_on >= 2/3, through D680's Globex chain under D720's lowered cut), V2 a CPI / employment-report session, V3
either. The kept book against take-all; exact rotation of the take mask (S2 efficiency primary), Holm over six; a
within-year permutation. Nothing dated 2024-01-01 or later is read; aggregates only. Run-once, ~6-8 min serial: the
Globex load dominates and the six scorings are seconds, so nothing is fanned out.
"""
from __future__ import annotations

import argparse
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
import stage0_d720_size_the_direction as Z  # noqa: E402
import stage0_d727_trend_curve as T7  # noqa: E402
import stage0_d735_nq_breaks_from_the_market as S  # noqa: E402
import stage0_d738_follow_oracle as S1  # noqa: E402
import stage0_d738_step3_filters as F3  # noqa: E402
import stage0_d740_floor_and_htf as F40  # noqa: E402

OUT = REPO / "data" / "stage0_d743_skip_layer.json"
D735_JSON = REPO / "data" / "stage0_d735_nq_breaks_from_the_market.json"
USD = 2.0
BUSY = 2 / 3
N_PERM, SEED = 20_000, 743
CELLS = {"YM_k1.0_1s": ("YM", 1.0), "EQ_k1.5_1s": ("EQ", 1.5)}
EQ_KNOWN_TRADES = 1131
VETOES = ("V1_busy_overnight", "V2_release_day", "V3_either")
ALPHA, WY_FLAG = 0.05, 0.10
P = Z.P


class D743Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D743Error(msg)


# ================================================================================ features
def pct_loop(f: np.ndarray, i: int, n_hist: int) -> float:
    """Second implementation of D671's walk-forward percentile: the strictly earlier finite values, the last n_hist."""
    prev = [float(v) for v in f[:i] if math.isfinite(v)][-n_hist:]
    if len(prev) < n_hist or not math.isfinite(f[i]):
        return float("nan")
    return sum(1 for v in prev if v < f[i]) / len(prev)


def join_audit(feat: pd.Series, days_used: np.ndarray, days: np.ndarray, sample: list[int]) -> None:
    """The feature joined on days_used must equal a direct lookup on the trade's own day."""
    got = feat.reindex(days_used).to_numpy(float)
    for i in sample:
        direct = float(feat[days[i]]) if days[i] in feat.index else float("nan")
        same = (math.isnan(direct) and math.isnan(got[i])) or direct == got[i]
        need(same, f"join: {days[i]} reads {got[i]}, its own session {direct}")


def overnight_features(rng: np.random.Generator) -> dict[str, Any]:
    """NQ's on_range and p_on per session (D671's functions, D680's Globex chain, the C1-diagnostic recipe)."""
    import stage0_d662_gamma_product as S662
    import stage0_d691_iv_size as I
    import vault_d680_nq_compression as V680
    C, M, Tv = V680.C, V680.M, V680.T
    old = V680.CUT
    V680.CUT = Z.CUT24
    try:
        with Z.lowered_cut(I, S662, I.T, I.M):
            b, use, _gd, R = M.load_bars(V680.DATA, False, ("ES", "NQ"))
            tabs = R.session_table(b, use, roots=("NQ",))
            d = Tv.root_frame(b, tabs["NQ"], "NQ")
            d = d[np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)].copy()
            d["gd_spx"] = np.nan                                   # the gamma column is not used here
            cal = pd.read_csv(V680.DATA / "fixtures" / "cme_session_calendar.csv.gz", encoding="utf-8", dtype={"day": str})
            on = C.overnight(b, "NQ")
            C.overnight_audit(on)
            try:
                C.overnight_audit(C.overnight(b, "NQ", include_rth=True))
            except C.D671Error:
                pass
            else:
                raise D743Error("lag: the overnight canary (a 09:30 bar included) did not fire")
            cal = cal[(cal["root"] == "NQ") & (cal["day"] < Z.CUT24)].set_index("day")
            Sx = C.session_features(d, on, cal)
    finally:
        V680.CUT = old
    Z.no_session_after(Sx.index, "the Globex session table")
    f = Sx["on_range"].to_numpy(float)
    p_on = C.tiers(f)
    fin = np.flatnonzero(np.isfinite(p_on))
    smp = [int(v) for v in rng.choice(fin, 40, replace=False)]
    for i in smp:
        need(math.isclose(pct_loop(f, i, C.TIER_N), p_on[i], abs_tol=1e-12), f"lag: p_on at {Sx.index[i]} is not the loop's")
    C.tier_audit(p_on, f, smp)
    try:
        C.tier_audit(C.tiers(f, leak=True), f, smp)
    except C.D671Error:
        pass
    else:
        raise D743Error("lag: the leaky-tier canary did not fire")
    rel = (cal["cpi"].fillna(False).astype(bool) | cal["empsit"].fillna(False).astype(bool))
    return {"sessions": Sx.index.astype(str).to_numpy(), "p_on": pd.Series(p_on, index=Sx.index.astype(str)),
            "release": rel, "tier_n": int(C.TIER_N), "n_sessions": int(len(Sx))}


# ================================================================================ the cells
def panels() -> dict[str, dict[str, Any]]:
    out = {}
    for r in ("NQ", "YM", "ES", "RTY"):
        pn = T7.panel_from_raw(r, S1.read_cut(S1.DATA / "fixtures" / f"fut_{r}_rth_1m.csv.gz"))
        Z.no_session_after(pn["days"], f"the {r} panel")
        out[r] = pn
    return out


def cells(pn: dict[str, dict[str, Any]], cost: float) -> dict[str, dict[str, Any]]:
    import vault_d737_nq_leads_the_dow as V737
    c = V737.cell(pn["NQ"], pn["YM"])
    V737.check_known(c, cost)
    pp, XN, days, G = c["pp"], c["XN"], c["days"], c["G"]
    need(V737.STOP_MULT == 1.0 and V737.K == 1.0 and V737.LEG == "YM", "D737's cell is not YM k1.0 1 sigma_rem")
    XL = {r: S.align_rows(pn[r]["days"], S.minute_x(pn[r]["C"], pn[r]["O"], pn[r]["soc"]), days) for r in ("ES", "YM", "RTY")}
    with np.errstate(invalid="ignore"):
        xeq = (XL["ES"] + XL["YM"] + XL["RTY"]) / 3.0
    sp = S.spread(XN, xeq)
    m0, D = S.trigger(sp["Z"], sp["S"], 1.5)
    d = np.flatnonzero(m0 >= 0)
    g = S.g_at(G, d, m0[d], D[d])
    need(bool(np.isfinite(g).all()), "EQ k1.5: a trade has no E1 value")
    ka = json.loads(D735_JSON.read_text(encoding="utf-8"))["cells"]["EQ_k1.5_1s"]
    need(len(d) == EQ_KNOWN_TRADES == ka["trades"] and math.isclose(float((g - cost).mean()), ka["mean_net"], rel_tol=0, abs_tol=1e-9),
         f"EQ k1.5's known answer is not reproduced: {len(d)} / {(g - cost).mean()}")
    out = {"YM_k1.0_1s": {"d": c["d"], "m0": c["m0"][c["d"]], "D": c["D"][c["d"]], "g": c["g"]},
           "EQ_k1.5_1s": {"d": d, "m0": m0[d], "D": D[d], "g": g}}
    return {"cells": out, "pp": pp, "days": days}


def sign_audit(pp: dict[str, np.ndarray], tr: dict[str, np.ndarray], rng: np.random.Generator) -> None:
    for k in rng.choice(len(tr["d"]), 40, replace=False):
        a = S.e1_loop(pp, int(tr["d"][k]), int(tr["m0"][k]), float(tr["D"][k]), 1.0)
        need(math.isclose(a, float(tr["g"][k]), rel_tol=0, abs_tol=1e-9), f"sign: trade {k} gross {tr['g'][k]} against the loop's {a}")


def rising_panel_sign() -> None:
    n, m = 3, S.NMIN
    path = 100.0 + 0.01 * np.arange(m)
    pp = {"Op": np.tile(path, (n, 1)), "H": np.tile(path + 0.005, (n, 1)), "L": np.tile(path - 0.005, (n, 1)),
          "C": np.tile(path + 0.005, (n, 1)), "soc": np.full(n, 5.0)}
    G = S.e1_tables(pp, math.inf)
    up = float(S.g_at(G, np.array([0]), np.array([S.M_LO]), np.array([1.0]))[0])
    dn = float(S.g_at(G, np.array([0]), np.array([S.M_LO]), np.array([-1.0]))[0])
    need(up > 0 and math.isclose(dn, -up, abs_tol=1e-12), f"sign: a rising day pays long {up}, short {dn}")


# ================================================================================ statistics
def within_year(take: np.ndarray, net: np.ndarray, y: np.ndarray, g: np.ndarray, years: np.ndarray,
                rng: np.random.Generator, n_perm: int = N_PERM) -> dict[str, Any]:
    """The kept count held per year; S1 mean net, S2 efficiency, S3 mean y of a random same-count pick."""
    sn, sy, sg, sa = (np.zeros(n_perm) for _ in range(4))
    kept = 0
    for yr in np.unique(years):
        idx = np.flatnonzero(years == yr)
        m = int(take[idx].sum())
        if m == 0:
            continue
        pick = np.argsort(rng.random((n_perm, len(idx))), axis=1)[:, :m]
        sn += net[idx][pick].sum(axis=1)
        sy += y[idx][pick].sum(axis=1)
        sg += g[idx][pick].sum(axis=1)
        sa += np.abs(g[idx][pick]).sum(axis=1)
        kept += m
    null = {"S1_mean_net": sn / kept, "S2_efficiency": sg / sa, "S3_mean_y": sy / kept}
    obs = {"S1_mean_net": float(net[take].mean()), "S2_efficiency": float(g[take].sum() / np.abs(g[take]).sum()),
           "S3_mean_y": float(y[take].mean())}
    return {k: {"observed": obs[k], "p": float((np.sum(v >= obs[k]) + 1) / (n_perm + 1)),
                "null_p50": float(np.percentile(v, 50)), "null_p95": float(np.percentile(v, 95))}
            for k, v in null.items()} | {"draws": n_perm}


def nulls(take: np.ndarray, net: np.ndarray, g: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    r = F3.rotation(take, net, g)
    r["S3_mean_y"] = F40.rotation2(take, net, y)["S2_mean_y"]
    need(math.isclose(r["S1_mean_net"]["observed"], float(net[take].mean()), abs_tol=1e-9), "rotation: offset 0 is not the kept mean")
    need(math.isclose(r["S2_efficiency"]["observed"], float(g[take].sum() / np.abs(g[take]).sum()), abs_tol=1e-12),
         "rotation: offset 0 is not the kept efficiency")
    return r


def book_line(net_t: np.ndarray, g_t: np.ndarray, d_t: np.ndarray, take: np.ndarray, wdays: np.ndarray,
              didx: np.ndarray, cost: float) -> dict[str, Any]:
    """The daily book over the window's sessions (skipped and untraded sessions are zero days)."""
    pos = {int(v): i for i, v in enumerate(didx)}
    net_d, gross_d, taken_d = np.zeros(len(wdays)), np.zeros(len(wdays)), np.zeros(len(wdays), bool)
    for k in np.flatnonzero(take):
        j = pos[int(d_t[k])]
        net_d[j] += net_t[k]
        gross_d[j] += g_t[k]
        taken_d[j] = True
    rep = F3.report(net_d, gross_d, taken_d, wdays, net_t[take])
    yrs = len(wdays) / 252.0
    rep["calmar"] = float(net_d.sum() / yrs / rep["max_dd"]) if rep["max_dd"] > 0 else None
    rep["worst_day"] = float(net_d.min())
    rep["mean_gross_vs_2c"] = float(g_t[take].mean() / (2 * cost)) if take.any() else None
    rep["breakeven_cost_per_round_trip"] = float(g_t[take].mean()) if take.any() else None
    if take.any():
        kk = np.flatnonzero(take)[int(np.argmax(net_t[take]))]
        rep["top_trade"] = {"day": str(wdays[pos[int(d_t[kk])]]), "net": float(net_t[kk])}
    rep["_daily"] = net_d
    return rep


def decide(p_holm: float, p_raw: float, skipped_total: float, kept: dict[str, Any], base: dict[str, Any],
           label: str | None, wy_p: float) -> dict[str, Any]:
    c1 = p_holm <= ALPHA
    c2 = skipped_total <= 0.0
    c3 = kept["net_sharpe"] > base["net_sharpe"] and kept["max_dd"] <= base["max_dd"]
    c4 = label == "EARNS"
    reading = "SUPPORTED" if (c1 and c2 and c3 and c4) else "LEAD" if p_raw <= ALPHA else "NOT SUPPORTED"
    return {"1_selection_holm": bool(c1), "2_skipped_do_not_earn": bool(c2), "3_sharpe_and_dd": bool(c3),
            "4_standard_EARNS": bool(c4), "reading": reading, "PICKS_YEARS": bool(wy_p > WY_FLAG)}


def mde(net: np.ndarray, take: np.ndarray) -> float | None:
    a, b = int(take.sum()), int((~take).sum())
    if a < 2 or b < 2:
        return None
    return float(2.8 * net.std(ddof=1) * math.sqrt(1 / a + 1 / b))


def oracles(net: np.ndarray, n_skip: dict[str, int]) -> dict[str, Any]:
    srt = np.sort(net)
    o1 = net[net > 0]
    return {"O1_keep_winners": {"trades": int(len(o1)), "total_net": float(o1.sum()), "mean_net": float(o1.mean())},
            "take_all": {"trades": int(len(net)), "total_net": float(net.sum()), "mean_net": float(net.mean())},
            "O2_same_size": {v: {"skipped": k, "delta_total": float(-srt[:k].sum()),
                                 "kept_mean_net": float(srt[k:].mean()) if k < len(srt) else None}
                             for v, k in n_skip.items()}}


def score(name: str, tr: dict[str, np.ndarray], feats: dict[str, Any], days: np.ndarray, soc: np.ndarray,
          cost: float, rng: np.random.Generator) -> dict[str, Any]:
    pon = feats["p_on"].reindex(days).to_numpy(float)
    rel = feats["release"].reindex(days).fillna(False).astype(bool).to_numpy()
    d_all = tr["d"]
    w = np.isfinite(pon[d_all])
    d, g = d_all[w], tr["g"][w]
    net = g - cost
    y = net / (soc[d] * USD)
    need(bool(np.isfinite(y).all()), f"{name}: sigma$ undefined on a scored trade")
    v1 = pon[d] >= BUSY
    v2 = rel[d]
    v3 = v1 | v2
    need(bool(np.array_equal(v3, np.logical_or(v1, v2))), "right quantity: V3 is not V1 or V2")
    first = int(np.flatnonzero(np.isfinite(pon))[0])
    didx = np.arange(first, len(days))
    wdays = days[didx]
    years = np.array([s[:4] for s in days[d]])
    base = book_line(net, g, d, np.ones(len(d), bool), wdays, didx, cost)
    out: dict[str, Any] = {"trades_all": int(len(d_all)), "trades_in_window": int(len(d)),
                           "dropped_burn_in": int((~w).sum()), "window": [str(wdays[0]), str(wdays[-1])],
                           "take_all": {k: v for k, v in base.items() if k != "_daily"}}
    out["oracle"] = oracles(net, {v: int(m.sum()) for v, m in zip(VETOES, (v1, v2, v3))})
    out["vetoes"] = {}
    for v, skip in zip(VETOES, (v1, v2, v3)):
        take = ~skip
        need(take.any() and skip.any(), f"{name} {v}: the veto keeps or skips everything")
        need(not np.array_equal(np.roll(take, 1), take), f"right quantity: {name} {v}'s mask is rotation-invariant")
        kept = book_line(net, g, d, take, wdays, didx, cost)
        skipped = book_line(net, g, d, skip, wdays, didx, cost)
        rot = nulls(take, net, g, y)
        wy = within_year(take, net, y, g, years, rng)
        o2 = out["oracle"]["O2_same_size"][v]["delta_total"]
        dtot = float(-net[skip].sum())
        out["vetoes"][v] = {
            "share_skipped": float(skip.mean()), "kept": {k: x for k, x in kept.items() if k != "_daily"},
            "skipped": {k: x for k, x in skipped.items() if k != "_daily"},
            "delta_total": dtot, "capture_of_O2": float(dtot / o2) if o2 > 0 else None,
            "kept_minus_skipped_mean_net": float(net[take].mean() - net[skip].mean()), "mde_mean_net": mde(net, take),
            "kept_minus_skipped_mean_y": float(y[take].mean() - y[skip].mean()),
            "rotation": rot, "within_year": wy,
            "_kept_daily": kept["_daily"], "_base_daily": base["_daily"]}
    return out


# ================================================================================ the run
def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: D743 is run-once")
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    import stage1_d711_f2_mechanism as M711
    cost = float(M711.cost_line("NQ")["cost"])
    rising_panel_sign()
    P("[D743] panels ...")
    pn = panels()
    built = cells(pn, cost)
    pp, days = built["pp"], built["days"]
    for tr in built["cells"].values():
        sign_audit(pp, tr, rng)
    P("[D743] Globex features ...")
    feats = overnight_features(rng)
    ser = feats["p_on"]
    need(all(len(s) == 10 and s[4] == "-" for s in days[:5]) and all(len(s) == 10 and s[4] == "-" for s in ser.index[:5]),
         "join: day strings are not YYYY-MM-DD on both sides")
    fin = [i for i in range(len(days)) if days[i] in ser.index and math.isfinite(ser[days[i]])]
    smp = [int(v) for v in rng.choice(fin, 50, replace=False)]
    join_audit(ser, days, days, smp)
    try:
        join_audit(ser, np.roll(days, 1), days, smp)
    except D743Error:
        pass
    else:
        raise D743Error("join: the shifted join did not fire the audit")
    P("[D743] scoring ...")
    res = {nm: score(nm, tr, feats, days, pp["soc"], cost, rng) for nm, tr in built["cells"].items()}
    ps = {f"{c}|{v}": res[c]["vetoes"][v]["rotation"]["S2_efficiency"]["p"] for c in res for v in VETOES}
    ph = F3.holm(ps)
    f2_, _ = Z.build_f2()
    f2d = f2_.groupby("day")["net1"].sum().reindex(pd.Index(days)).fillna(0.0).to_numpy()
    ym = built["cells"]["YM_k1.0_1s"]
    ym_daily = np.zeros(len(days))                     # D737's in-sample twin, take-all, every session
    np.add.at(ym_daily, ym["d"], ym["g"] - cost)
    for c in res:
        sel = (days >= res[c]["window"][0]) & (days <= res[c]["window"][1])
        for v in VETOES:
            r = res[c]["vetoes"][v]
            r["holm_p"] = ph[f"{c}|{v}"]
            lab = r["kept"]["standard_with_abstention"].get("label")
            r["decision"] = decide(r["holm_p"], r["rotation"]["S2_efficiency"]["p"], float(r["skipped"]["total_net"]),
                                   r["kept"], res[c]["take_all"], lab, r["within_year"]["S2_efficiency"]["p"])
            kd = r.pop("_kept_daily")
            r.pop("_base_daily")
            need(len(kd) == int(sel.sum()), f"{c} {v}: the kept daily book is not the window's sessions")
            td = r["kept"]["trade_distribution_net"]
            r["component_line"] = {"net_sharpe": r["kept"]["net_sharpe"], "net_sortino": r["kept"]["net_sortino"],
                                   "gross_sharpe": r["kept"]["gross_sharpe"], "hit_rate": td.get("win_rate"),
                                   "skew": td.get("skew"), "rho_nq_f2": float(np.corrcoef(kd, f2d[sel])[0, 1]),
                                   "rho_d737_twin_take_all": float(np.corrcoef(kd, ym_daily[sel])[0, 1]),
                                   "same_component_as": "D737" if c == "YM_k1.0_1s" else "D735 EQ k1.5 (D737's clock and signal family)"}
    out = {"spec": "D743-STAGE-0-PRE-REG-skip-busy-nights-and-release-days-on-d735.md", "seal": f"nothing on or after {Z.CUT24}",
           "cost": cost, "busy_threshold": BUSY, "tier_n": feats["tier_n"], "globex_sessions": feats["n_sessions"],
           "release_sessions_in_panel": int(feats["release"].reindex(days).fillna(False).astype(bool).sum()),
           "cells": res, "holm_family": ph,
           "readings": {f"{c}|{v}": res[c]["vetoes"][v]["decision"]["reading"] for c in res for v in VETOES},
           "wall_min": (time.time() - t0) / 60}
    OUT.write_text(json.dumps(out, indent=1, default=Z._json) + "\n", encoding="utf-8", newline="\n")
    for c in res:
        ta = res[c]["take_all"]
        P(f"[D743] {c}: take-all {ta['trades']} trades, ${ta['total_net']:.0f}, Sharpe {ta['net_sharpe']:.2f}")
        for v in VETOES:
            r = res[c]["vetoes"][v]
            P(f"   {v}: skip {r['share_skipped']:.2f}; kept ${r['kept']['mean_net']:.2f} vs skipped ${r['skipped']['mean_net']:.2f}; "
              f"S2 p {r['rotation']['S2_efficiency']['p']:.3f} (Holm {r['holm_p']:.3f}); wy p {r['within_year']['S2_efficiency']['p']:.3f}; "
              f"Sharpe {r['kept']['net_sharpe']:.2f}; {r['decision']['reading']}")
    P(f"[D743] {out['wall_min']:.1f} min")
    return 0


# ================================================================================ self-test (synthetic only)
def selftest() -> int:
    rng = np.random.default_rng(7)
    fails: list[str] = []

    def expect_raise(fn: Any, what: str) -> None:
        try:
            fn()
        except (D743Error, AssertionError):
            return
        fails.append(f"{what} did not raise")

    # 1) the percentile loop equals D671's tiers on a tie-heavy series, and a leaky value disagrees
    import stage0_d671_break_construction as C
    f = np.round(rng.normal(size=700), 1)
    f[rng.choice(700, 30, replace=False)] = np.nan
    t = C.tiers(f)
    for i in rng.choice(np.flatnonzero(np.isfinite(t)), 60, replace=False):
        if not math.isclose(pct_loop(f, int(i), C.TIER_N), t[i], abs_tol=1e-12):
            fails.append(f"pct_loop disagrees with tiers at {i}")
            break
    tl = C.tiers(f, leak=True)
    if np.allclose(tl[np.isfinite(t)], t[np.isfinite(t)]):
        fails.append("the leaky tiers equal the walk-forward ones (the canary cannot fire)")
    # 2) the join audit passes on the true days and raises on a shifted join
    dd = np.array([f"2020-01-{i:02d}" for i in range(1, 29)])
    feat = pd.Series(np.arange(28, dtype=float), index=dd)
    join_audit(feat, dd, dd, list(range(5, 20)))
    expect_raise(lambda: join_audit(feat, np.roll(dd, 1), dd, list(range(5, 20))), "the shifted join audit")
    # 3) the sign of a rising day
    rising_panel_sign()
    # 4) a planted veto (skip every losing trade) comes out at rotation p < 0.01; a random veto is not SUPPORTED
    n = 600
    g = rng.normal(5.0, 60.0, n)
    net = g - 4.0
    y = net / 100.0
    take = g >= 0
    r = nulls(take, net, g, y)
    if not r["S2_efficiency"]["p"] < 0.01:
        fails.append(f"the planted veto's rotation p is {r['S2_efficiency']['p']}")
    years = np.repeat([str(2016 + i) for i in range(6)], n // 6)
    wy = within_year(take, net, y, g, years, rng, 2000)
    if not wy["S2_efficiency"]["p"] < 0.01:
        fails.append("the planted veto's within-year p is not small")
    tk = rng.random(n) > 0.3
    r2 = nulls(tk, net, g, y)
    days = np.array([f"{2016 + i // 250}-{(i % 250) // 21 + 1:02d}-{i % 21 + 1:02d}" for i in range(1500)])
    didx = np.arange(1500)
    d_t = np.sort(rng.choice(1500, n, replace=False))
    kept = book_line(net, g, d_t, tk, days, didx, 4.0)
    base = book_line(net, g, d_t, np.ones(n, bool), days, didx, 4.0)
    sk = book_line(net, g, d_t, ~tk, days, didx, 4.0)
    dec = decide(r2["S2_efficiency"]["p"], r2["S2_efficiency"]["p"], sk["total_net"], kept, base,
                 kept["standard_with_abstention"].get("label"), 0.5)
    if dec["reading"] == "SUPPORTED":
        fails.append("a random veto was SUPPORTED")
    # 5) decide() itself: each condition can fail the reading
    good = {"net_sharpe": 1.0, "max_dd": 50.0}
    bad = {"net_sharpe": 0.5, "max_dd": 100.0}
    if decide(0.01, 0.01, -5.0, good, bad, "EARNS", 0.01)["reading"] != "SUPPORTED":
        fails.append("decide: the all-pass case is not SUPPORTED")
    for args, why in (((0.2, 0.01, -5.0, good, bad, "EARNS", 0.01), "Holm"), ((0.01, 0.01, 5.0, good, bad, "EARNS", 0.01), "skipped earn"),
                      ((0.01, 0.01, -5.0, {"net_sharpe": 0.4, "max_dd": 10.0}, bad, "EARNS", 0.01), "Sharpe"),
                      ((0.01, 0.01, -5.0, {"net_sharpe": 1.0, "max_dd": 150.0}, bad, "EARNS", 0.01), "drawdown"),
                      ((0.01, 0.01, -5.0, good, bad, "BREAK-EVEN", 0.01), "standard")):
        if decide(*args)["reading"] != "LEAD":
            fails.append(f"decide: failing {why} is not LEAD")
    if decide(0.5, 0.2, -5.0, good, bad, "EARNS", 0.01)["reading"] != "NOT SUPPORTED":
        fails.append("decide: raw p 0.2 is not NOT SUPPORTED")
    if not decide(0.01, 0.01, -5.0, good, bad, "EARNS", 0.2)["PICKS_YEARS"]:
        fails.append("decide: the PICKS YEARS flag does not fire")
    # 6) need() raises
    expect_raise(lambda: need(False, "x"), "need")
    for m in fails:
        P(f"[SELFTEST FAIL] {m}")
    P(f"[D743] selftest: {'FAIL' if fails else 'all passed'}")
    return 1 if fails else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.run:
        return run()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
