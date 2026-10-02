"""D762 Stage 0: does the cash close reverse? (prop book), as pre-registered in
docs/decisions/D762-STAGE-0-PRE-REG-does-the-cash-close-reverse.md (02a6afce).

    uv run --no-sync python scripts/stage0_d762_cash_close.py --selftest
    uv run --no-sync python scripts/stage0_d762_cash_close.py --run      # once; writes data/stage0_d762_cash_close.json

ES, NQ, YM, RTY, 2016-01-04 -> 2023-12-29. x = P16:00 - P15:50 (the close's pressure), y = P16:10 - P16:00 (the
response), P_t the close of the bar starting t-1 (D727). Day-session prices from D727's panels (fut_{root}_rth_1m);
post-close prices from fut_index_close_1m (D762's fixture). C1 size; C2 Spearman rho(x, y) against the exact rotation of
y (one-sided p05, Holm over the roots); C3 against the 15:00 and 12:00 placebos (paired day bootstrap, 2 SE); C4 the
walk-forward top-third |x| fade's gross against the cost. In-sample only.
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
from scipy.stats import rankdata

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d756_reverting_days as V  # noqa: E402  (wf_tercile, holm, costs path, _strip)
import stage0_d760_absorbed_fade as R  # noqa: E402  (dist, four_groups, sharpe_sortino, daily_book: reporting only)

SPEC = REPO / "docs" / "decisions" / "D762-STAGE-0-PRE-REG-does-the-cash-close-reverse.md"
OUT = REPO / "data" / "stage0_d762_cash_close.json"
FX = V.DATA / "fixtures"
CLOSE_FX = FX / "fut_index_close_1m.csv.gz"
CLOSE_META = FX / "fut_index_close_1m.meta.json"
BOOKS = REPO / "data" / "d748_component_books.csv"
ROOTS = ("ES", "NQ", "YM", "RTY")
SEAL = V.SEAL
NMIN = 390
POST = [f"16:{m:02d}" for m in range(15)]                     # bar starts 16:00 .. 16:14
# minute index m of the bar starting 09:30 + m; P_t = close of the bar starting t-1
IX = {"15:50": 379, "16:00": 389, "15:30": 359, "14:50": 319, "15:00": 329, "15:10": 339, "11:50": 139, "12:00": 149, "12:10": 159}
NEED_BARS = ("15:49", "15:59", "11:49", "11:59")
B_BOOT, SEED, ALPHA, T_MIN = 2000, 762, 0.05, 2.0
RUSSELL = {"2016-06-24", "2017-06-23", "2018-06-22", "2019-06-28", "2020-06-26", "2021-06-25", "2022-06-24", "2023-06-23"}


class D762Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D762Error(msg)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def seal_check(df: pd.DataFrame, what: str) -> None:
    need(not (df["day"] >= SEAL).any(), f"the seal: a {what} row on or after 2024-01-01")


def hhmm(m: int) -> str:
    t = 9 * 60 + 30 + m
    return f"{t // 60:02d}:{t % 60:02d}"


# ================================================================================ statistics
def spearman(x: np.ndarray, y: np.ndarray) -> float:
    rx, ry = rankdata(x), rankdata(y)
    rx, ry = rx - rx.mean(), ry - ry.mean()
    return float((rx * ry).sum() / math.sqrt((rx * rx).sum() * (ry * ry).sum()))


def rotation(x: np.ndarray, y: np.ndarray) -> dict:
    """Exact enumerated rotation of y across sessions (offsets 1 .. n-1); ranks are rotation-invariant."""
    rx, ry = rankdata(x), rankdata(y)
    rx, ry = rx - rx.mean(), ry - ry.mean()
    den = math.sqrt((rx * rx).sum() * (ry * ry).sum())
    obs = float((rx * ry).sum() / den)
    n = x.size
    null = np.array([float((rx * np.roll(ry, k)).sum() / den) for k in range(1, n)])
    return {"rho": obs, "offset0": float((rx * np.roll(ry, 0)).sum() / den), "offsets": int(null.size),
            "p05": float(np.percentile(null, 5)), "p50": float(np.percentile(null, 50)), "p95": float(np.percentile(null, 95)),
            "p_one_sided": float((1 + (null <= obs).sum()) / (1 + null.size))}


def ols_nw(x: np.ndarray, y: np.ndarray, lags: int = 5) -> dict:
    X = np.column_stack([np.ones_like(x), x])
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ b
    n = len(y)
    XtXi = np.linalg.inv(X.T @ X)
    S = (X * e[:, None]).T @ (X * e[:, None])
    for L in range(1, lags + 1):
        w = 1 - L / (lags + 1)
        G = (X[L:] * e[L:, None]).T @ (X[:-L] * e[:-L, None])
        S += w * (G + G.T)
    V_ = XtXi @ S @ XtXi
    return {"slope": float(b[1]), "t_nw": float(b[1] / math.sqrt(V_[1, 1]))}


def boot_diff(x, y, xp, yp, seed: int) -> dict:
    """Paired day bootstrap of rho(x, y) - rho(xp, yp)."""
    rng = np.random.default_rng(seed)
    n = x.size
    d = np.empty(B_BOOT)
    for b in range(B_BOOT):
        i = rng.integers(0, n, n)
        d[b] = spearman(x[i], y[i]) - spearman(xp[i], yp[i])
    obs = spearman(x, y) - spearman(xp, yp)
    se = float(d.std(ddof=1))
    verdict = "pass" if obs < -2 * se else ("fail" if obs > 2 * se else "unresolved")
    return {"margin": obs, "se": se, "verdict": verdict}


def c3_verdict(vs: list[str]) -> str:
    if all(v == "pass" for v in vs):
        return "pass"
    if any(v == "fail" for v in vs):
        return "fail"
    return "unresolved"


def reading(c2: bool, c3: str | None, c4: bool | None) -> str:
    if not c2:
        return "NO REVERSAL"
    if c3 == "fail":
        return "GENERIC"
    if c3 == "unresolved":
        return "UNRESOLVED"
    return "PREMISE HOLDS" if c4 else "NO PRIZE"


# ================================================================================ data
def third_friday(y: int, m: int) -> str:
    d = pd.Timestamp(year=y, month=m, day=1)
    d += pd.Timedelta(days=(4 - d.weekday()) % 7 + 14)
    return d.strftime("%Y-%m-%d")


def build_root(r: str, close: pd.DataFrame, costs: dict) -> dict:
    import stage0_d727_trend_curve as T7
    pn = T7.load_root(r, V.DATA)
    days = np.asarray(pn["days"], str)
    need(max(days) < SEAL, f"the seal: {r}'s panel")
    raw = pn["raw"]
    seal_check(raw, f"{r} rth")
    con = raw.groupby("day")["contract"].agg(lambda s: s.value_counts().index[0]).reindex(days).to_numpy(str)
    present = raw.groupby("day")["hhmm"].agg(set).reindex(days)
    has_need = np.array([all(h in s for h in NEED_BARS) for s in present])
    c = close[close["root"] == r]
    seal_check(c, f"{r} close")
    c = c[c["day"].isin(days)]
    want = pd.Series(con, index=days)
    c = c[c["contract"].to_numpy(str) == want.reindex(c["day"]).to_numpy(str)]
    pc = c.pivot(index="day", columns="hhmm", values="close").reindex(index=days, columns=POST).to_numpy(float)
    has_post = np.isfinite(pc[:, 5:10]).any(1)
    C = pn["C"]
    P = {k: C[:, i] for k, i in IX.items()}
    post = np.column_stack([P["16:00"], pc])                  # col 0 = P16:00, col k = close of bar 16:(k-1)
    post = pd.DataFrame(post).ffill(axis=1).to_numpy(float)
    P["16:05"], P["16:10"], P["16:15"] = post[:, 5], post[:, 10], post[:, 15]
    ok = has_need & has_post & np.isfinite(P["16:10"])
    ce = costs[r]["micro"]
    cost = float(ce["commission_rt_usd"]["value"] + ce["crossing_ticks_rt"][ce["default_line"]]["value"] * ce["tick_usd"])
    q = {k: v[ok] for k, v in P.items()}
    x = q["16:00"] - q["15:50"]
    y = q["16:10"] - q["16:00"]
    out = dict(root=r, days=days[ok], x=x, y=y, x30=q["16:00"] - q["15:30"], oc=q["16:00"] - pn["O"][ok],
               y5=q["16:05"] - q["16:00"], y15=q["16:15"] - q["16:00"],
               xp15=q["15:00"] - q["14:50"], yp15=q["15:10"] - q["15:00"],
               xp12=q["12:00"] - q["11:50"], yp12=q["12:10"] - q["12:00"],
               p16=q["16:00"], upp=float(ce["usd_per_point"]), cost=cost, tick_usd=float(ce["tick_usd"]),
               n_panel=int(days.size), n_dropped_need=int((~has_need).sum()), n_dropped_post=int((has_need & ~has_post).sum()),
               raw=raw, close_raw=c, con=con[ok])
    out["top"] = V.wf_tercile(np.abs(x)) == 2
    return out


# ================================================================================ the lag audit (second implementation)
def _pct_linear(vals, q: float) -> float:
    s = sorted(vals)
    h = (len(s) - 1) * q
    lo = int(math.floor(h))
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (h - lo) * (s[hi] - s[lo])


def lag_audit(raw: pd.DataFrame, close_raw: pd.DataFrame, days, con, x, y, xp12, yp12, top, sample, include_current=False):
    rb = {d: g.set_index("hhmm")["close"] for d, g in raw.groupby("day")}
    cb = {d: g.set_index("hhmm")["close"] for d, g in close_raw.groupby("day")}

    def p_at(day, t):                                         # close of the bar starting t-1, forward-filled
        mins = [hhmm(m) for m in range(NMIN)] + POST
        tt = (pd.Timestamp(f"2000-01-01 {t}") - pd.Timedelta(minutes=1)).strftime("%H:%M")
        k = mins.index(tt)
        for h in reversed(mins[: k + 1]):
            if h >= "16:00":
                s = cb.get(day)
                if s is not None and h in s.index:
                    return float(s[h])
            else:
                s = rb[day]
                if h in s.index:
                    return float(s[h])
        return float("nan")

    ax = {}
    for i in sample:
        d = days[i]
        for nm, got, (a, b) in (("x", x, ("15:50", "16:00")), ("y", y, ("16:00", "16:10")),
                                ("xp12", xp12, ("11:50", "12:00")), ("yp12", yp12, ("12:00", "12:10"))):
            v = p_at(d, b) - p_at(d, a)
            need(math.isclose(v, got[i], rel_tol=0, abs_tol=1e-6), f"lag: {nm} at {d}: {v} vs {got[i]}")
        lo = i - V.WF + (1 if include_current else 0)
        hi = i + (1 if include_current else 0)
        vals = []
        for j in range(lo, hi):
            if j not in ax:
                ax[j] = abs(p_at(days[j], "16:00") - p_at(days[j], "15:50"))
            vals.append(ax[j])
        q2 = _pct_linear(vals, 2 / 3)
        need(bool(abs(x[i]) >= q2) == bool(top[i]), f"lag: the top-third flag at {d}")


# ================================================================================ the run
def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: run-once")
    t0 = time.time()
    meta = json.loads(CLOSE_META.read_text(encoding="utf-8"))
    roots = [r for r in ROOTS if meta["validation"][r]["pass"]]
    costs = json.loads(V.COSTS.read_text(encoding="utf-8"))["roots"]
    close = pd.read_csv(CLOSE_FX, dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
    seal_check(close, "close fixture")
    D = {r: build_root(r, close, costs) for r in roots}
    print(f"[D762] loaded {roots} in {time.time() - t0:.0f} s", flush=True)
    rng = np.random.default_rng(SEED)
    res_roots, ps = {}, {}
    bk = pd.read_csv(BOOKS, dtype={"session": str}, encoding="utf-8")
    for r, d in D.items():
        n = d["x"].size
        samp = [int(i) for i in rng.choice(np.arange(V.WF, n), size=40, replace=False)]
        lag_audit(d["raw"], d["close_raw"], d["days"], d["con"], d["x"], d["y"], d["xp12"], d["yp12"], d["top"], samp)
        rot = rotation(d["x"], d["y"])
        need(math.isclose(rot["offset0"], rot["rho"], rel_tol=1e-12) and math.isclose(rot["rho"], spearman(d["x"], d["y"]), rel_tol=1e-12),
             "rotation offset 0 != observed")
        ps[r] = rot["p_one_sided"]
        # C1 size
        c1 = {"sd_y_usd": float(np.std(d["y"] * d["upp"], ddof=1)), "mean_abs_y_usd": float(np.mean(np.abs(d["y"])) * d["upp"]),
              "sd_x_usd": float(np.std(d["x"] * d["upp"], ddof=1)), "mean_abs_x_usd": float(np.mean(np.abs(d["x"])) * d["upp"]),
              "cost_usd": d["cost"], "share_y_zero": float((d["y"] == 0).mean())}
        # C3 placebos
        c3 = {"15:00": boot_diff(d["x"], d["y"], d["xp15"], d["yp15"], SEED + 1),
              "12:00": boot_diff(d["x"], d["y"], d["xp12"], d["yp12"], SEED + 2)}
        pl = {"15:00": spearman(d["xp15"], d["yp15"]), "12:00": spearman(d["xp12"], d["yp12"])}
        # C4 the fade on the walk-forward top third of |x|
        side = -np.sign(d["x"])
        tk = d["top"] & (side != 0)
        g = side[tk] * d["y"][tk] * d["upp"]
        tr = pd.DataFrame({"day": d["days"][tk], "root": r, "side": side[tk].astype(int), "clock": "16:00",
                           "ptile": pd.qcut(pd.Series(d["p16"][tk]), 3, labels=False).to_numpy(), "gross": g,
                           "net": g - d["cost"]})
        gs = R.dist(g)
        c4 = bool(tk.sum() >= 3 and gs["mean"] >= d["cost"] and gs["t"] >= T_MIN)
        cal = d["days"][V.WF:]
        fg = R.four_groups(tr, cal)
        dn = R.daily_book(tr, cal, "net")
        rho_b = {}
        for b, gb in bk.groupby("book"):
            sb = gb.groupby("session")["net"].sum()
            lo, hi = max(min(cal), min(sb.index)), min(max(cal), max(sb.index))
            span = cal[(cal >= lo) & (cal <= hi)]
            rho_b[b] = float(np.corrcoef(dn.reindex(span).to_numpy(), sb.reindex(span, fill_value=0.0).to_numpy())[0, 1]) if span.size > 30 else None
        # reported: heavy-auction days
        dd = pd.to_datetime(pd.Series(d["days"]))
        qfri = {third_friday(y_, m_) for y_ in range(2016, 2024) for m_ in (3, 6, 9, 12)}
        ym = dd.dt.strftime("%Y-%m")
        mend = (ym != ym.shift(-1)).to_numpy()
        groups = {"quarterly_expiry_friday": np.isin(d["days"], list(qfri)), "month_end": mend,
                  "russell_recon": np.isin(d["days"], list(RUSSELL))}
        heavy = {}
        for k, m in groups.items():
            rest = ~m
            fm = tk & m
            heavy[k] = {"n": int(m.sum()), "rho": spearman(d["x"][m], d["y"][m]) if m.sum() > 5 else None,
                        "rho_rest": spearman(d["x"][rest], d["y"][rest]),
                        "mean_abs_x_usd": float(np.mean(np.abs(d["x"][m])) * d["upp"]) if m.sum() else None,
                        "fade_all_days_gross": R.dist((side * d["y"] * d["upp"])[m & (side != 0)]),
                        "fade_top_third_gross": R.dist((side * d["y"] * d["upp"])[fm])}
        res_roots[r] = {
            "n": int(n), "panel_sessions": d["n_panel"], "dropped_missing_bars": d["n_dropped_need"], "dropped_no_post_bar": d["n_dropped_post"],
            "C1": c1, "C2": dict(rot, **ols_nw(d["x"], d["y"])), "C3": {"margins": c3, "placebo_rho": pl,
                                                                        "verdict": c3_verdict([v["verdict"] for v in c3.values()])},
            "C4": {"trades": int(tk.sum()), "gross": gs, "pass": c4, "net_plus_one_tick": R.dist(tr["net"].to_numpy() - d["tick_usd"]),
                   "four_groups": fg, "rho_books": rho_b},
            "reported": {"rho_x30_y": spearman(d["x30"], d["y"]), "rho_oc_y": spearman(d["oc"], d["y"]),
                         "rho_x_y5": spearman(d["x"], d["y5"]), "rho_x_y15": spearman(d["x"], d["y15"]),
                         "rho_x_y_by_year": {yr: spearman(d["x"][ym.str[:4].to_numpy() == yr], d["y"][ym.str[:4].to_numpy() == yr])
                                             for yr in sorted(set(ym.str[:4]))},
                         "heavy_auction_days": heavy}}
    adj = V.holm(ps)
    for r in res_roots:
        x = res_roots[r]
        c2 = bool(x["C2"]["rho"] < 0 and x["C2"]["rho"] < x["C2"]["p05"] and adj[r] < ALPHA)
        x["C2"]["holm_p"] = adj[r]
        x["C2"]["pass"] = c2
        x["reading"] = reading(c2, x["C3"]["verdict"], x["C4"]["pass"])
    res = {"record": "D762 (02a6afce)", "roots": res_roots, "readings": {r: x["reading"] for r, x in res_roots.items()},
           "fixture_validation": meta["validation"], "runner_sha256": sha(Path(__file__).resolve()), "prereg_sha256": sha(SPEC),
           "wall_s": round(time.time() - t0, 1)}
    with open(OUT, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(V._strip(res), fh, indent=1, default=str)
        fh.write("\n")
    show(res)
    return 0


def show(res: dict) -> None:
    for r, x in res["roots"].items():
        c1, c2, c3, c4 = x["C1"], x["C2"], x["C3"], x["C4"]
        print(f"[D762] {r}: {x['reading']}  n {x['n']}")
        print(f"  C1 sd y ${c1['sd_y_usd']:.2f}, mean|y| ${c1['mean_abs_y_usd']:.2f}; sd x ${c1['sd_x_usd']:.2f}; cost ${c1['cost_usd']:.2f}; y=0 {c1['share_y_zero']:.3f}")
        print(f"  C2 rho {c2['rho']:+.4f} (p05 {c2['p05']:+.4f}, p50 {c2['p50']:+.4f}, p95 {c2['p95']:+.4f}); p {c2['p_one_sided']:.4f}, "
              f"Holm {c2['holm_p']:.4f}; slope {c2['slope']:+.4f} (NW t {c2['t_nw']:+.2f}) -> {c2['pass']}")
        print(f"  C3 placebo rho {c3['placebo_rho']}; margins {c3['margins']} -> {c3['verdict']}")
        g = c4["gross"]
        print(f"  C4 n {c4['trades']}: gross {g.get('mean', float('nan')):+.2f} (t {g.get('t', float('nan')):.2f}, med {g.get('median', float('nan')):+.2f}) "
              f"vs cost {c1['cost_usd']:.2f} -> {c4['pass']}; net Sharpe {c4['four_groups'].get('daily_net_sharpe')}")
        rep = x["reported"]
        print(f"  reported rho x30 {rep['rho_x30_y']:+.4f}, oc {rep['rho_oc_y']:+.4f}, y5 {rep['rho_x_y5']:+.4f}, y15 {rep['rho_x_y15']:+.4f}")
        print(f"  heavy {{k: (v['n'], v['rho']) for k, v in rep['heavy_auction_days'].items()}}".replace("{k: (v['n'], v['rho']) for k, v in rep['heavy_auction_days'].items()}",
              str({k: (v["n"], None if v["rho"] is None else round(v["rho"], 3)) for k, v in rep["heavy_auction_days"].items()})))
    print(f"[D762] wall {res['wall_s']} s")


# ================================================================================ self-test
def selftest() -> int:
    fails = []
    rng = np.random.default_rng(3)
    # the rotation: offset 0 equals rho, and the exact null has n - 1 offsets
    x, y = rng.normal(size=300), rng.normal(size=300)
    rt = rotation(x, y)
    if rt["offsets"] != 299 or not math.isclose(rt["rho"], spearman(x, y), rel_tol=1e-12):
        fails.append("rotation")
    # readings and C3 verdicts
    if reading(False, None, None) != "NO REVERSAL" or reading(True, "fail", True) != "GENERIC" or \
            reading(True, "unresolved", True) != "UNRESOLVED" or reading(True, "pass", False) != "NO PRIZE" or \
            reading(True, "pass", True) != "PREMISE HOLDS":
        fails.append("reading")
    if c3_verdict(["pass", "pass"]) != "pass" or c3_verdict(["pass", "fail"]) != "fail" or c3_verdict(["pass", "unresolved"]) != "unresolved":
        fails.append("c3_verdict")
    # sign in money: fading an up-close pays when the price falls after 16:00
    xx, yy = np.array([2.0]), np.array([-1.0])
    if float(-np.sign(xx)[0] * yy[0] * 5.0) != 5.0:
        fails.append("sign in money")
    # the seal
    try:
        seal_check(pd.DataFrame({"day": ["2024-01-02"]}), "test")
        fails.append("seal did not raise")
    except D762Error:
        pass
    # synthetic: a planted close reversal passes C2 and C3; noise fails C2 about 95 %
    n = 1500
    xs = rng.normal(0, 1, n)
    ys = -0.25 * xs + rng.normal(0, 1, n)
    xp, yp = rng.normal(0, 1, n), rng.normal(0, 1, n)
    rp = rotation(xs, ys)
    bd = boot_diff(xs, ys, xp, yp, 1)
    if not (rp["rho"] < rp["p05"] and bd["verdict"] == "pass"):
        fails.append("planted reversal did not pass C2 and C3")
    nf = 0
    for s in range(100):
        r2 = np.random.default_rng(1000 + s)
        a, b = r2.normal(size=400), r2.normal(size=400)
        rr = rotation(a, b)
        nf += int(not (rr["rho"] < rr["p05"]))
    print(f"  noise fails C2 {nf} / 100")
    if not 88 <= nf <= 100:
        fails.append(f"noise fails C2 {nf}/100")
    # the lag audit itself on synthetic raw rows: passes on the true flag, raises on a current-including window
    nd = V.WF + 80
    days = np.array([d.strftime("%Y-%m-%d") for d in pd.bdate_range("2016-01-04", periods=nd)])
    mins = [hhmm(m) for m in range(NMIN)]
    px = 100 + np.cumsum(rng.normal(0, 0.25, (nd, NMIN)), axis=1)
    # plant |x| so session WF flips: its true window {10, 166 x 0, 83 x 2} has q2 = 2 (|x| = 1 is not top); a window that
    # includes it {166 x 0, 1, 83 x 2} has q2 = 1 (top)
    plant = np.r_[10.0, np.zeros(166), np.full(83, 2.0), 1.0]
    px[: plant.size, IX["15:50"]] = px[: plant.size, IX["16:00"]] - plant
    pp = px[:, -1:] + np.cumsum(rng.normal(0, 0.25, (nd, len(POST))), axis=1)
    raw = pd.DataFrame({"day": np.repeat(days, NMIN), "hhmm": np.tile(mins, nd), "close": px.ravel()})
    craw = pd.DataFrame({"day": np.repeat(days, len(POST)), "hhmm": np.tile(POST, nd), "close": pp.ravel()})
    X = px[:, IX["16:00"]] - px[:, IX["15:50"]]
    Y = pp[:, 9] - px[:, IX["16:00"]]
    XP = px[:, IX["12:00"]] - px[:, IX["11:50"]]
    YP = px[:, IX["12:10"]] - px[:, IX["12:00"]]
    TOP = V.wf_tercile(np.abs(X)) == 2
    smp = list(range(V.WF, V.WF + 8))
    try:
        lag_audit(raw, craw, days, None, X, Y, XP, YP, TOP, smp)
    except D762Error as e:
        fails.append(f"lag audit raised on the truth: {e}")
    # a session whose flag a current-including window flips; the audit run that way must raise on it
    flip = [k for k in range(V.WF, nd)
            if bool(abs(X[k]) >= _pct_linear(list(np.abs(X[k - V.WF + 1:k + 1])), 2 / 3)) != bool(TOP[k])]
    if not flip:
        fails.append("no session flips under a current-including window (the break cannot be shown)")
    else:
        try:
            lag_audit(raw, craw, days, None, X, Y, XP, YP, TOP, [flip[0]], include_current=True)
            fails.append("lag audit did not raise on a current-including tercile")
        except D762Error:
            pass
    for f in fails:
        print(f"[SELFTEST FAIL] {f}")
    print(f"[D762] selftest: {'FAIL' if fails else 'all passed'}")
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
