"""D744 Stage 0: the consolidation break at the European open. Spec:
docs/decisions/D744-STAGE-0-PRE-REG-the-consolidation-break-at-the-european-open.md, committed before this file existed.

    uv run python scripts/stage0_d744_european_open_break.py --selftest
    uv run python scripts/stage0_d744_european_open_break.py --run        # once -> data/stage0_d744_european_open_break.json

NQ's Globex 1-minute bars through D680's chain (D720's lowered cut, D680's CUT held at 2024-01-01; D672's C1 known
answer first). A candidate session opens its 03:00 bar strictly inside yesterday's RTH range +/- 0.25 ATR20; the first
fill of a stop at either level on the 03:00-08:29 bars is the trade (at the level or the bar's open through it), E4
trail (initial stop at the broken level, 0.25 ATR20 behind the best), flat at the 09:29 close. Gate: C1's ctier
rebuilt from rv5 and the 18:00-02:59 two-way range. One MNQ; the night cost is $3 + 1.5 x the crossing. Nothing dated
2024-01-01 or later is read; aggregates only. Run-once; a few minutes; nothing fanned out.
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
import stage0_d738_step3_filters as F3  # noqa: E402

OUT = REPO / "data" / "stage0_d744_european_open_break.json"
K_ATR = TRAIL_K = 0.25
NIGHT_FROM, LAST_ENTRY, FLAT = "03:00", "08:29", "09:29"
NIGHT_X, X2 = 1.5, 2.0
MIN_TRADES, T_BAR, ALPHA = 30, 1.28, 0.05
P = Z.P


class D744Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D744Error(msg)


def mod(h: str) -> int:
    return int(h[:2]) * 60 + int(h[3:])


# ================================================================================ the asia range
def asia_frame(x: pd.DataFrame, cut: str = NIGHT_FROM) -> pd.DataFrame:
    """Per session: high / low over 18:00 -> (cut - 1 min) and the last bar's close before `cut` in time order (the
    evening bars come first). `cut` = 03:01 is the lag canary."""
    ev = x[x["hhmm"] >= "18:00"]
    mo = x[x["hhmm"] < cut]
    mo = mo[mo["hhmm"] < "18:00"]
    both = pd.concat([ev, mo])
    g = both.groupby("session")
    out = pd.DataFrame({"a_high": g["high"].max(), "a_low": g["low"].min()})
    last_mo = mo.sort_values("hhmm").groupby("session").tail(1).set_index("session")
    last_ev = ev.sort_values("hhmm").groupby("session").tail(1).set_index("session")
    lc = last_ev["close"].reindex(out.index)
    lh = last_ev["hhmm"].reindex(out.index)
    has_mo = out.index.isin(last_mo.index)
    lc[has_mo] = last_mo["close"].reindex(out.index[has_mo]).to_numpy(float)
    lh[has_mo] = last_mo["hhmm"].reindex(out.index[has_mo]).to_numpy()
    out["a_last"], out["a_last_hhmm"], out["a_has_morning"] = lc, lh, has_mo
    return out


def asia_audit(a: pd.DataFrame) -> None:
    mo = a["a_has_morning"].to_numpy(bool)
    need(not (a.loc[mo, "a_last_hhmm"] >= NIGHT_FROM).any(), "lag: the asia range read a bar at or after 03:00")


# ================================================================================ the trade (and its loop twin)
def night_arrays(v: pd.DataFrame) -> dict[str, np.ndarray]:
    v = v[(v["hhmm"] >= NIGHT_FROM) & (v["hhmm"] <= FLAT)].sort_values("hhmm")
    return {"m": np.array([mod(h) for h in v["hhmm"]]), "o": v["open"].to_numpy(float), "h": v["high"].to_numpy(float),
            "l": v["low"].to_numpy(float), "c": v["close"].to_numpy(float)}


def night_break(bb: dict, Lh: float, Ll: float, A: float) -> dict[str, Any] | None:
    m, o, h, l = bb["m"], bb["o"], bb["h"], bb["l"]
    for i in range(len(m)):
        if m[i] > mod(LAST_ENTRY):
            return None
        for D, L in ((1, Lh), (-1, Ll)):
            stop = L + D * K_ATR * A
            if (D > 0 and h[i] >= stop) or (D < 0 and l[i] <= stop):
                return {"D": D, "i": i, "entry": float(max(stop, o[i]) if D > 0 else min(stop, o[i])), "L": L, "stop": stop}
    return None


def night_exit(bb: dict, i: int, D: int, entry: float, L: float, A: float, flat: str = FLAT) -> tuple[float, str, int]:
    m, o, h, l, c = bb["m"], bb["o"], bb["h"], bb["l"], bb["c"]
    stop, best = L, entry
    for k in range(i + 1, len(m)):
        if m[k] > mod(flat):
            break
        if (l[k] <= stop) if D > 0 else (h[k] >= stop):
            through = (o[k] <= stop) if D > 0 else (o[k] >= stop)
            return float(o[k] if through else stop), "stop", int(m[k])
        best = max(best, h[k]) if D > 0 else min(best, l[k])
        new = best - D * TRAIL_K * A
        stop = max(stop, new) if D > 0 else min(stop, new)
    j = np.flatnonzero(m <= mod(flat))
    return float(c[j[-1]]), "close", int(m[j[-1]])


def twin(X: Any, bb: dict, Lh: float, Ll: float, A: float, close_bar: int) -> tuple[dict | None, float | None]:
    """D666's own plain_break / exit_trade with the clock's constants (restored after)."""
    old = (X.LAST_ENTRY, X.CLOSE_BAR, X.TICK, X.K_ATR, X.TRAIL_K)
    try:
        X.LAST_ENTRY, X.CLOSE_BAR, X.TICK = mod(LAST_ENTRY), close_bar, 0.0
        need(X.K_ATR == K_ATR and X.TRAIL_K == TRAIL_K, "D666's K_ATR / TRAIL_K are not 0.25")
        p = X.plain_break(bb, Lh, Ll, A)
        if p is None:
            return None, None
        px, _ = X.exit_trade(bb, p["i"], p["D"], p["entry"], p["L"], A, 0.0, "E4")
        return p, px
    finally:
        X.LAST_ENTRY, X.CLOSE_BAR, X.TICK, X.K_ATR, X.TRAIL_K = old


def rising_sign() -> None:
    m = np.arange(mod("03:00"), mod("09:30"))
    p = 100.0 + 0.02 * np.arange(len(m))
    bb = {"m": m, "o": p, "h": p + 0.01, "l": p - 0.01, "c": p}
    t = night_break(bb, 100.5, 99.0, 1.0)
    need(t is not None and t["D"] == 1, "sign: a rising night does not break up")
    px, why, _ = night_exit(bb, t["i"], t["D"], t["entry"], t["L"], 1.0)
    need(why == "close" and t["D"] * (px - t["entry"]) * 2.0 > 0, "sign: the long on a rising night does not pay")
    need(-1 * (px - t["entry"]) * 2.0 < 0, "sign: a short on a rising night pays")


# ================================================================================ statistics
def decide(n: int, t: float, net_bp: float, rot_p: float, label: str | None, u_t: float, u_net: float,
           t2: float, net2: float) -> dict[str, Any]:
    c1, c2, c3, c4 = n >= MIN_TRADES, (t >= T_BAR and net_bp > 0), rot_p <= ALPHA, label == "EARNS"
    rd = "SUPPORTED" if (c1 and c2 and c3 and c4) else "LEAD" if (c1 and c2) else "NOT SUPPORTED"
    return {"1_trades": bool(c1), "2_d680_bar": bool(c2), "3_gate_rotation": bool(c3), "4_standard_EARNS": bool(c4),
            "reading": rd, "U_alone_meets_bar_LEAD": bool(u_t >= T_BAR and u_net > 0),
            "COST_FRAGILE": bool(rd == "SUPPORTED" and not (t >= T_BAR and net2 > 0))}


def book(tr: pd.DataFrame, take: np.ndarray, wdays: np.ndarray, R: Any, cost_col: str) -> dict[str, Any]:
    t = tr[take]
    pos = {s: i for i, s in enumerate(wdays)}
    net_d, gross_d, taken_d = np.zeros(len(wdays)), np.zeros(len(wdays)), np.zeros(len(wdays), bool)
    for s, nu, gu in zip(t["session"], t[f"net_usd_{cost_col}"], t["gross_usd"]):
        j = pos[s]
        net_d[j] += nu
        gross_d[j] += gu
        taken_d[j] = True
    rep = F3.report(net_d, gross_d, taken_d, wdays, t[f"net_usd_{cost_col}"].to_numpy(float))
    n = len(t)
    g = t["gross_bp"].to_numpy(float)
    tt = float(R.nw_t(g)[0]) if n >= 3 else float("nan")
    rep.update({"gross_bp": float(g.mean()) if n else None, "net_bp": float(t[f"net_bp_{cost_col}"].mean()) if n else None,
                "t_gross_hac": tt, "sd_gross_bp": float(g.std(ddof=1)) if n > 2 else None,
                "mde_gross_bp_t1.28": float(T_BAR * g.std(ddof=1) / math.sqrt(n)) if n > 2 else None,
                "calmar": float(net_d.sum() / (len(wdays) / 252) / rep["max_dd"]) if rep["max_dd"] > 0 else None,
                "worst_day": float(net_d.min()), "breakeven_cost_usd": float(t["gross_usd"].mean()) if n else None,
                "mean_gross_vs_2c": float(t["gross_usd"].mean() / (2 * t[f"cost_usd_{cost_col}"].iloc[0])) if n else None,
                "exit_reasons": t["why"].value_counts().to_dict(), "entry_hour": t["hour"].value_counts().sort_index().to_dict(),
                "long": {"n": int((t["D"] > 0).sum()), "mean_net_usd": float(t.loc[t["D"] > 0, f"net_usd_{cost_col}"].mean()) if (t["D"] > 0).any() else None},
                "short": {"n": int((t["D"] < 0).sum()), "mean_net_usd": float(t.loc[t["D"] < 0, f"net_usd_{cost_col}"].mean()) if (t["D"] < 0).any() else None}})
    if n:
        k = t[f"net_usd_{cost_col}"].idxmax()
        rep["top_trade"] = {"session": str(t.loc[k, "session"]), "D": int(t.loc[k, "D"]), "net_usd": float(t.loc[k, f"net_usd_{cost_col}"])}
    rep["_daily"] = net_d
    return rep


# ================================================================================ the run
D672_BY_YEAR = {"2018": 5.3, "2019": 0.7, "2020": 5.8, "2021": 10.0, "2022": 12.0, "2023": 4.1}  # D672 RESULT s.3
C1_TRADES_2023_CUT = 328


def c1_known_answer(tr: pd.DataFrame) -> dict[str, Any]:
    """D744-A1: V.known_answer reads D672's window to 2025-02 (387 trades), which the 2024 cut cannot reach. The known
    answer is instead D672's published per-year C1 net (s.3, fill-tick line, one decimal) for 2018-2023."""
    win = np.isfinite(tr["t671"].to_numpy(float)) & np.isfinite(tr["ctier"].to_numpy(float))
    c1 = tr[win & (tr["ctier"].to_numpy(float) < 1 / 3)]
    by = c1.groupby(c1["session"].str[:4])["net_prereg"].mean()
    got = {y: round(float(by.get(y, np.nan)), 1) for y in D672_BY_YEAR}
    need(got == D672_BY_YEAR and len(c1) == C1_TRADES_2023_CUT, f"C1 known answer: {len(c1)} trades, {got} against {D672_BY_YEAR}")
    return {"trades": int(len(c1)), "net_prereg_by_year": got}


def load() -> dict[str, Any]:
    import stage0_d662_gamma_product as S662
    import stage0_d691_iv_size as I
    import vault_d680_nq_compression as V
    C, M, X, Tv = V.C, V.M, V.X, V.T
    old = V.CUT
    V.CUT = Z.CUT24
    try:
        with Z.lowered_cut(I, S662, I.T, I.M):
            b, use, _gd, R = M.load_bars(V.DATA, False, ("ES", "NQ"))
            dix = pd.read_csv(V.DATA / "raw" / "squeezemetrics" / "DIX.csv", encoding="utf-8", dtype={"date": str})
            gex = dix[dix["date"] < Z.CUT24].set_index("date")["gex"].astype(float).sort_index()
            tr_c1, _ = V.book(b, use, R, gex)
            ka = c1_known_answer(tr_c1)
            tabs = R.session_table(b, use, roots=("NQ",))
            d = Tv.root_frame(b, tabs["NQ"], "NQ")
            d = d[np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)].copy()
            d["gd_spx"] = np.nan
            cal = pd.read_csv(V.DATA / "fixtures" / "cme_session_calendar.csv.gz", encoding="utf-8", dtype={"day": str})
            cal = cal[(cal["root"] == "NQ") & (cal["day"] < Z.CUT24)].set_index("day")
            on = C.overnight(b, "NQ")
            Sx = C.session_features(d, on, cal)
    finally:
        V.CUT = old
    Z.no_session_after(d.index, "the NQ session frame")
    x = b[b["root"] == "NQ"][["session", "hhmm", "open", "high", "low", "close"]].copy()
    x["hhmm"] = x["hhmm"].astype(str)
    Z.no_session_after(x["session"].unique(), "NQ's Globex bars")
    return {"V": V, "C": C, "M": M, "X": X, "R": R, "d": d, "Sx": Sx, "x": x, "tr_c1": tr_c1, "c1_known": ka}


def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: D744 is run-once")
    t0 = time.time()
    rng = np.random.default_rng(744)
    rising_sign()
    L_ = load()
    V, C, M, X, R, d, Sx, x = (L_[k] for k in ("V", "C", "M", "X", "R", "d", "Sx", "x"))
    need(X.__name__.endswith("d666_rebreak"), f"X is {X.__name__}, not D666's module")
    mc = M.micro_costs()["NQ"]
    cl = V.cost_lines()
    costs = {"night": 3.0 + NIGHT_X * mc["crossing_ticks"] * mc["tick_usd"], "day": float(cl["cost_single_usd"]),
             "x2": 3.0 + X2 * mc["crossing_ticks"] * mc["tick_usd"]}
    need(costs["night"] > costs["day"] and math.isclose(costs["day"], 3.0 + mc["crossing_ticks"] * mc["tick_usd"]),
         "right quantity: the night cost is not above the day cost")
    upp = float(cl["usd_per_point"])
    # the asia range, its lag audit and canary
    a = asia_frame(x)
    asia_audit(a)
    try:
        asia_audit(asia_frame(x, cut="03:01"))
    except D744Error:
        pass
    else:
        raise D744Error("lag: the asia canary (03:00 bar included) did not fire")
    a = a.reindex(d.index)
    asia = ((a["a_high"] - a["a_low"] - (a["a_last"] - d["prior_close"]).abs()) / d["atr20"]).to_numpy(float)
    rv5 = Sx["rv5"].reindex(d.index).to_numpy(float)
    p_rv, p_as = C.tiers(rv5), C.tiers(asia)
    comp = (p_rv + p_as) / 2
    ctier = C.tiers(comp)
    for f_, t_ in ((rv5, p_rv), (asia, p_as), (comp, ctier)):
        idx = [int(i) for i in rng.choice(np.flatnonzero(np.isfinite(t_)), 40, replace=False)]
        C.tier_audit(t_, f_, idx)
        try:
            C.tier_audit(C.tiers(f_, leak=True), f_, idx)
        except C.D671Error:
            pass
        else:
            raise D744Error("lag: the leaky-tier canary did not fire")
    sess = d.index.astype(str).to_numpy()
    # the trades
    grp = {s: v for s, v in x[(x["hhmm"] >= NIGHT_FROM) & (x["hhmm"] <= FLAT)].groupby("session")}
    rows, n_out, n_no3, n_canary_diff = [], 0, 0, 0
    for k, s in enumerate(sess):
        if not math.isfinite(ctier[k]) or s not in grp:
            continue
        bb = night_arrays(grp[s])
        if len(bb["m"]) == 0 or bb["m"][0] != mod(NIGHT_FROM):
            n_no3 += 1
            continue
        rec = d.iloc[k]
        Lh, Ll, A = float(rec["prior_high"]), float(rec["prior_low"]), float(rec["atr20"])
        if not (Ll - K_ATR * A < bb["o"][0] < Lh + K_ATR * A):
            n_out += 1
            continue
        p = night_break(bb, Lh, Ll, A)
        p2, px2 = twin(X, bb, Lh, Ll, A, mod(FLAT))
        if p is None:
            need(p2 is None, f"{s}: D666's plain_break trades where the runner does not")
            continue
        px, why, mx = night_exit(bb, p["i"], p["D"], p["entry"], p["L"], A)
        need(p2 is not None and p2["i"] == p["i"] and p2["D"] == p["D"] and p2["entry"] == p["entry"] and px2 == px,
             f"{s}: the second implementation disagrees ({p2}, {px2} against {p}, {px})")
        _, pxc = twin(X, bb, Lh, Ll, A, mod(FLAT) - 1)
        n_canary_diff += int(pxc != px)
        g_bp = p["D"] * (px / p["entry"] - 1) * 1e4
        rows.append({"session": s, "D": p["D"], "entry": p["entry"], "hour": int(bb["m"][p["i"]] // 60), "why": why,
                     "gross_bp": g_bp, "gross_usd": p["D"] * (px - p["entry"]) * upp, "ctier": float(ctier[k])})
    need(n_out > 0, "right quantity: the 03:00-inside condition never binds")
    need(n_canary_diff > 0, "the 09:28-close canary agreed with every trade")
    tr = pd.DataFrame(rows)
    for nm, cu in costs.items():
        tr[f"cost_usd_{nm}"] = cu
        tr[f"net_usd_{nm}"] = tr["gross_usd"] - cu
        tr[f"net_bp_{nm}"] = tr["gross_bp"] - cu / upp / tr["entry"] * 1e4
    Z.no_session_after(tr["session"], "the D744 trades")
    wmask = np.isfinite(ctier)
    wdays = sess[wmask]
    Pm = (tr["ctier"] < 1 / 3).to_numpy()
    U = np.ones(len(tr), bool)
    need(Pm.any() and (~Pm).any() and not np.array_equal(np.roll(Pm, 1), Pm), "right quantity: the gate mask is degenerate")
    books = {nm: {cn: book(tr, m_, wdays, R, cn) for cn in costs} for nm, m_ in (("P", Pm), ("U", U), ("R", ~Pm))}
    rot = F3.rotation(Pm, tr["net_usd_night"].to_numpy(float), tr["gross_usd"].to_numpy(float))
    need(math.isclose(rot["S2_efficiency"]["observed"], float(tr.loc[Pm, "gross_usd"].sum() / tr.loc[Pm, "gross_usd"].abs().sum()), abs_tol=1e-12),
         "rotation: offset 0 is not the gated efficiency")
    bP, bU = books["P"]["night"], books["U"]["night"]
    dec = decide(int(Pm.sum()), bP["t_gross_hac"], bP["net_bp"], rot["S2_efficiency"]["p"],
                 bP["standard_with_abstention"].get("label"), bU["t_gross_hac"], bU["net_bp"],
                 books["P"]["x2"]["t_gross_hac"], books["P"]["x2"]["net_bp"])
    # overlap and the component line
    c1 = L_["tr_c1"]
    c1 = c1[np.isfinite(c1["ctier"].to_numpy(float)) & (c1["ctier"].to_numpy(float) < 1 / 3)]
    c1usd = pd.Series(c1["net"].to_numpy(float) / 1e4 * c1["level"].to_numpy(float) * upp, index=c1["session"].to_numpy())
    c1d = c1usd.groupby(level=0).sum().reindex(wdays).fillna(0.0).to_numpy()
    shared = tr[Pm].merge(c1[["session", "D"]], on="session", suffixes=("", "_c1"))
    import stage0_d727_trend_curve as T7
    import stage0_d738_follow_oracle as S1
    import stage1_d711_f2_mechanism as M711
    import vault_d737_nq_leads_the_dow as V737
    pnN = T7.panel_from_raw("NQ", S1.read_cut(S1.DATA / "fixtures" / "fut_NQ_rth_1m.csv.gz"))
    pnY = T7.panel_from_raw("YM", S1.read_cut(S1.DATA / "fixtures" / "fut_YM_rth_1m.csv.gz"))
    cy = V737.cell(pnN, pnY)
    cost737 = float(M711.cost_line("NQ")["cost"])
    V737.check_known(cy, cost737)
    d737 = pd.Series(cy["g"] - cost737, index=cy["days"][cy["d"]]).reindex(wdays).fillna(0.0).to_numpy()
    f2_, _ = Z.build_f2()
    f2d = f2_.groupby("day")["net1"].sum().reindex(wdays).fillna(0.0).to_numpy()
    pdaily = bP["_daily"]
    comp_line = {"net_sharpe": bP["net_sharpe"], "net_sortino": bP["net_sortino"], "gross_sharpe": bP["gross_sharpe"],
                 "hit_rate": bP["trade_distribution_net"].get("win_rate"), "skew": bP["trade_distribution_net"].get("skew"),
                 "rho_c1": float(np.corrcoef(pdaily, c1d)[0, 1]), "rho_d737_twin": float(np.corrcoef(pdaily, d737)[0, 1]),
                 "rho_nq_f2": float(np.corrcoef(pdaily, f2d)[0, 1]),
                 "sessions_shared_with_c1": int(len(shared)), "same_direction_share": float((shared["D"] == shared["D_c1"]).mean()) if len(shared) else None}
    for nm in books:
        for cn in books[nm]:
            books[nm][cn].pop("_daily")
    out = {"spec": "D744-STAGE-0-PRE-REG-the-consolidation-break-at-the-european-open.md", "seal": f"nothing on or after {Z.CUT24}",
           "c1_known_answer": L_["c1_known"], "costs_usd": costs, "window": [str(wdays[0]), str(wdays[-1])],
           "window_sessions": int(len(wdays)), "sessions_beyond_level_at_03": n_out, "sessions_without_03_bar": n_no3,
           "trades": {"P": int(Pm.sum()), "U": int(len(tr)), "R": int((~Pm).sum())}, "canary_close_0928_differs": n_canary_diff,
           "books": books, "rotation": rot, "decision": dec, "component_line": comp_line,
           "P_by_year_trades": tr[Pm].groupby(tr.loc[Pm, "session"].str[:4]).size().to_dict(), "wall_min": (time.time() - t0) / 60}
    OUT.write_text(json.dumps(out, indent=1, default=Z._json) + "\n", encoding="utf-8", newline="\n")
    for nm in ("P", "U", "R"):
        b_ = books[nm]["night"]
        P(f"[D744] {nm}: {b_['trades']} trades, gross {b_['gross_bp']:.2f} bp (t {b_['t_gross_hac']:.2f}), net {b_['net_bp']:.2f} bp, "
          f"${b_['total_net']:.0f}, Sharpe {b_['net_sharpe']:.2f}")
    P(f"[D744] gate rotation S2 p {rot['S2_efficiency']['p']:.3f}; {dec}; {out['wall_min']:.1f} min")
    return 0


# ================================================================================ self-test (synthetic only)
def selftest() -> int:
    fails: list[str] = []
    rng = np.random.default_rng(1)
    import stage0_d666_rebreak as X
    rising_sign()
    # 1) the loop equals D666's functions on random nights (tie-heavy prices on a quarter-point grid)
    agree, diff = 0, 0
    for _ in range(300):
        n = 390
        steps = np.round(rng.normal(0, 1.0, n) * 4) / 4
        cpx = 100 + np.cumsum(steps)
        o = np.r_[100.0, cpx[:-1]]
        h = np.maximum(o, cpx) + np.round(rng.random(n) * 4) / 4
        l = np.minimum(o, cpx) - np.round(rng.random(n) * 4) / 4
        bb = {"m": np.arange(mod("03:00"), mod("03:00") + n), "o": o, "h": h, "l": l, "c": cpx}
        A = float(rng.choice([8.0, 60.0]))
        p = night_break(bb, 102.0, 98.0, A)
        p2, px2 = twin(X, bb, 102.0, 98.0, A, mod(FLAT))
        if p is None:
            if p2 is not None:
                fails.append("plain_break trades where the loop does not")
            continue
        px, _, _ = night_exit(bb, p["i"], p["D"], p["entry"], p["L"], A)
        if p2 is None or p2["i"] != p["i"] or p2["entry"] != p["entry"] or px2 != px:
            fails.append("the loop and D666 disagree")
            break
        agree += 1
        _, pxc = twin(X, bb, 102.0, 98.0, A, mod(FLAT) - 1)
        diff += int(pxc != px)
    if agree < 50 or diff == 0:
        fails.append(f"too few agreeing trades ({agree}) or the close canary never differs ({diff})")
    if (X.LAST_ENTRY, X.CLOSE_BAR) != (15 * 60 + 29, 15 * 60 + 59):
        fails.append("D666's constants were not restored")
    # 2) the asia frame: the evening comes first, the canary includes 03:00
    rows = []
    for s in ("2020-01-02", "2020-01-03"):
        for hh, px in (("18:00", 10.0), ("23:00", 12.0), ("01:00", 9.0), ("02:59", 11.0), ("03:00", 30.0)):
            rows.append({"session": s, "hhmm": hh, "open": px, "high": px, "low": px, "close": px})
    xx = pd.DataFrame(rows)
    a = asia_frame(xx)
    if not (a["a_high"].eq(12.0).all() and a["a_low"].eq(9.0).all() and a["a_last"].eq(11.0).all()):
        fails.append(f"asia_frame: {a.to_dict()}")
    asia_audit(a)
    try:
        asia_audit(asia_frame(xx, cut="03:01"))
        fails.append("the asia canary did not raise")
    except D744Error:
        pass
    # 3) decide()
    if decide(80, 1.5, 2.0, 0.01, "EARNS", 0.5, -1.0, 1.4, 1.0)["reading"] != "SUPPORTED":
        fails.append("decide: the all-pass case")
    for args, why in (((80, 1.5, 2.0, 0.2, "EARNS", 0.5, -1, 1.4, 1.0), "rotation"), ((80, 1.5, 2.0, 0.01, "BREAK-EVEN", 0.5, -1, 1.4, 1.0), "standard")):
        if decide(*args)["reading"] != "LEAD":
            fails.append(f"decide: failing {why} is not LEAD")
    for args, why in (((20, 1.5, 2.0, 0.01, "EARNS", 0.5, -1, 1.4, 1.0), "count"), ((80, 1.0, 2.0, 0.01, "EARNS", 0.5, -1, 1.4, 1.0), "t"),
                      ((80, 1.5, -0.1, 0.01, "EARNS", 0.5, -1, 1.4, 1.0), "net")):
        if decide(*args)["reading"] != "NOT SUPPORTED":
            fails.append(f"decide: failing {why} is not NOT SUPPORTED")
    if not decide(80, 1.5, 2.0, 0.01, "EARNS", 0.5, -1, 1.4, -0.5)["COST_FRAGILE"]:
        fails.append("decide: COST-FRAGILE does not fire")
    if not decide(80, 0.5, -1.0, 0.5, None, 1.5, 0.5, 0, 0)["U_alone_meets_bar_LEAD"]:
        fails.append("decide: the U lead does not fire")
    # 4) a planted gate is caught by the rotation
    g = rng.normal(0, 50, 400)
    r = F3.rotation(g > 0, g - 4, g)
    if not r["S2_efficiency"]["p"] < 0.01:
        fails.append("the planted gate's rotation p is not small")
    try:
        need(False, "x")
        fails.append("need() did not raise")
    except D744Error:
        pass
    for m in fails:
        P(f"[SELFTEST FAIL] {m}")
    P(f"[D744] selftest: {'FAIL' if fails else 'all passed'}")
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
