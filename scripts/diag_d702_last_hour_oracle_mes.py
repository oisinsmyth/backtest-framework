"""D702 DIAG -- the oracle profile of the reopened ES last-hour continuation at MES (the principal: "Reopen it, that is
the whole point of this study"). Spec: docs/decisions/D702-DESIGN-the-last-hour-oracle-profile-at-mes.md (c2e519f2).
Hindsight and descriptive only: nothing is fitted, filtered or traded. It is the evidence the principal and I design the
candidate filters from.

    uv run python scripts/diag_d702_last_hour_oracle_mes.py --selftest
    uv run python scripts/diag_d702_last_hour_oracle_mes.py --run

THE CANDIDATES (D618 s.3c): at 15:30, sign(F5), F5 = ln(P15:30 / P14:30), held 15:30 -> 16:00, on D618's sessions
(ES, >= 380 bars) 2016-01-04 -> 2023-12-29. The known answer (D618 s.3c: +0.6795 points, hit 0.4929) is on every
non-roll session (1,960; a session with F5 = 0 enters as a zero); the MES candidates are the non-roll sessions with
F5 != 0 (a zero signal pays no fee). gross = sign(F5) x (P16:00 - P15:30) x $5; net = gross - $4.42.
WIN = net > 0; BAR = gross >= $8.84. Reads nothing dated 2024-01-01 or later (2024-01 -> 2025-02 is this line's
reserved confirmation slice). GEX (SqueezeMetrics) via D688's panel, no per-date series written.
Writes data/diag_d702_last_hour_oracle_mes.json.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
from backtest_framework.validation import filter_oracle as FO  # noqa: E402
import stage1_d694_coiled_break as P  # noqa: E402

D, C = P.D, P.C
DATA = D.DATA
OUT = REPO / "data" / "diag_d702_last_hour_oracle_mes.json"
COST, MES_USD, SEED = 4.42, 5.0, 702
RESERVED = "2024-01-01"
KNOWN = {"n": 1960, "mean_pts": 0.6795, "hit": 0.4929}
ERA_SPLIT = "2022-05-16"
RHOS = (0.0, 0.02, 0.05, 0.10, 0.20)


class D702Error(RuntimeError):
    pass


def _load(name: str, fn: str) -> Any:
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


# ================================================================================ the pre-entry realised volatility
def rv_today(close: pd.DataFrame, open_: pd.Series, include_1530_bar: bool = False) -> pd.Series:
    """ln sqrt(sum of squared 5-minute log returns, bp^2) from 09:30 to 15:30. The price AT t is the close of the bar
    starting t - 1 minute (D618's convention), so every bar used starts at or before 15:29. The canary extends the grid
    to 15:35, reading the bar that starts at 15:30."""
    end = pd.Timestamp("2000-01-01 15:35" if include_1530_bar else "2000-01-01 15:30")
    grid, t = [], pd.Timestamp("2000-01-01 09:35")
    while t <= end:
        grid.append((t - pd.Timedelta(minutes=1)).strftime("%H:%M"))
        t += pd.Timedelta(minutes=5)
    PG = np.column_stack([open_.to_numpy(float)] + [close[g].to_numpy(float) for g in grid])
    r5 = 1e4 * np.diff(np.log(PG), axis=1)
    with np.errstate(divide="ignore"):
        return pd.Series(np.log(np.sqrt(np.nansum(r5 * r5, axis=1))), index=close.index)


def rv_audit(close: pd.DataFrame, open_: pd.Series, got: pd.Series, days: list[str]) -> None:
    """Second implementation per day by minute arithmetic: bars whose START minute is <= 15:29 only."""
    for d in days:
        row = close.loc[d]
        pts = [float(open_.loc[d])]
        for mnt in range(9 * 60 + 34, 15 * 60 + 30, 5):
            pts.append(float(row[f"{mnt // 60:02d}:{mnt % 60:02d}"]))
        r = 1e4 * np.diff(np.log(np.array(pts)))
        want = math.log(math.sqrt(float(np.nansum(r * r))))
        if not math.isclose(want, float(got.loc[d]), rel_tol=0, abs_tol=1e-9):
            raise D702Error(f"lag: today's realised volatility at {d} reads a bar that starts at or after 15:30")


# ================================================================================ statistics
def line_stats(g: np.ndarray, take: np.ndarray, years: float, days: np.ndarray) -> dict[str, Any]:
    n = int(take.sum())
    if n < 3:
        return {"trades": n}
    gt, nt = g[take], g[take] - COST
    tpy = n / years
    sd = nt.std(ddof=1)
    dn = math.sqrt(float(np.mean(np.minimum(nt, 0) ** 2)))
    daily = np.where(take, g - COST, 0.0)
    ddn = math.sqrt(float(np.mean(np.minimum(daily, 0) ** 2)))
    eq = np.cumsum(nt)
    yrs = pd.Series(nt, index=days[take]).groupby(lambda s: s[:4]).sum()
    return {"trades": n, "trades_per_year": tpy, "mean_gross": float(gt.mean()), "mean_net": float(nt.mean()),
            "hit_gross_gt0": float((gt > 0).mean()), "win_net_gt0": float((nt > 0).mean()),
            "sharpe_per_trade": float(nt.mean() / sd * math.sqrt(tpy)) if sd > 0 else float("nan"),
            "sortino_per_trade": float(nt.mean() / dn * math.sqrt(tpy)) if dn > 0 else float("nan"),
            "sharpe_daily": float(daily.mean() / daily.std(ddof=1) * math.sqrt(252)),
            "sortino_daily": float(daily.mean() / ddn * math.sqrt(252)) if ddn > 0 else float("nan"),
            "max_drawdown_usd": float(np.max(np.maximum.accumulate(eq) - eq)),
            "years_positive": f"{int((yrs > 0).sum())} of {len(yrs)}"}


def bucket_stats(g: np.ndarray, m: np.ndarray, years: float, tot_oracle: float, n_all: int, win_all: float,
                 bar_all: float) -> dict[str, Any]:
    n = int(m.sum())
    if n < 2:
        return {"n": n}
    gg, nn = g[m], g[m] - COST
    win, bar = nn > 0, gg >= 2 * COST
    return {"n": n, "share": n / n_all, "per_year": n / years,
            "win_rate": float(win.mean()), "win_lift": float(win.mean() - win_all),
            "bar_rate": float(bar.mean()), "bar_lift": float(bar.mean() - bar_all),
            "mean_gross": float(gg.mean()), "t_gross_hac": D.nw_t(gg)[0] if n > 10 else float("nan"),
            "mean_net": float(nn.mean()), "share_of_oracle_net": float(nn[win].sum() / tot_oracle),
            "mean_net_winners": float(nn[win].mean()) if win.any() else float("nan"),
            "mean_net_losers": float(nn[~win].mean()) if (~win).any() else float("nan")}


def terciles(x: np.ndarray, k: int = 3) -> np.ndarray:
    """Bucket index 0..k-1 by hindsight quantile edges over the finite values; -1 where x is not finite."""
    fin = np.isfinite(x)
    edges = np.quantile(x[fin], np.linspace(0, 1, k + 1)[1:-1])
    return np.where(fin, np.searchsorted(edges, np.where(fin, x, 0.0), side="right"), -1)


# ================================================================================ the build
def build() -> dict[str, Any]:
    m618 = _load("m618", "stage0_d618_sharpened_ladder.py")
    S, _meta = m618.load_es()
    if (S.index >= RESERVED).any():
        raise D702Error("seal: a session on or after 2024-01-01 reached D618's frame")
    # the known answer: D618 s.3c on every non-roll session
    d = np.sign(S["F5"].to_numpy(float))
    pts = d * (S["P1600"] - S["P1530"]).to_numpy(float)
    ka = np.isfinite(pts) & ~S["roll"].to_numpy(bool)
    got = {"n": int(ka.sum()), "mean_pts": float(pts[ka].mean()), "hit": float((pts[ka] > 0).mean())}
    if got["n"] != KNOWN["n"] or abs(got["mean_pts"] - KNOWN["mean_pts"]) > 5e-5 or abs(got["hit"] - KNOWN["hit"]) > 5e-5:
        raise D702Error(f"known answer: {got} against D618 s.3c's {KNOWN}")
    cand = ka & (d != 0)
    X = S[cand].copy()
    X["gross"] = d[cand] * (X["P1600"] - X["P1530"]).to_numpy(float) * MES_USD
    X["abs_move"] = (X["P1600"] - X["P1530"]).abs() * MES_USD
    X["side"] = d[cand]
    sigF5 = S["F5"].rolling(252, min_periods=60).std().shift(1)
    X["f5z"] = (S["F5"].abs() / sigF5).reindex(X.index)
    X["align"] = np.sign(np.log(X["P1430"] / X["P0930"])) == X["side"]
    # today's realised volatility (bars) and its lag audit
    b = pd.read_csv(m618.ES_1M, dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
    b = b[(b["day"] >= m618.IN_FROM) & (b["day"] <= m618.IN_TO)]
    if (b["day"] >= RESERVED).any():
        raise D702Error("seal: a bar on or after 2024-01-01 was read")
    close = b.pivot(index="day", columns="hhmm", values="close").reindex(X.index)
    open_ = b[b["hhmm"] == "09:30"].set_index("day")["open"].reindex(X.index)
    rv = rv_today(close, open_)
    sample = list(X.index[:: max(1, len(X) // 25)])
    rv_audit(close, open_, rv, sample)
    try:
        rv_audit(close, open_, rv_today(close, open_, include_1530_bar=True), sample)
    except D702Error:
        pass
    else:
        raise D702Error("the realised-volatility lag canary did not fire")
    X["rv_today"] = rv
    # D691's forecasts (D694's audited bundle), and D691's d-bar reproduced
    lab = P.get_bundle()["ES"]["lab"]
    P.d691_reproduced(lab, "ES")
    for c in ("f1", "ivrv", "lniv"):
        X[c] = lab[c].reindex(X.index).to_numpy(float)
    # dealer gamma: D688's panel through D692's build (which reproduces D688's beta_G first)
    m692 = _load("m692", "diag_d692_oracle_profile_mes.py")
    T692, _nd = m692.build(DATA, lambda *a: None)
    gam = T692.groupby("day")[["G_SUM", "G_SPX", "G_ES"]].first()
    for c in gam.columns:
        X[c] = gam[c].reindex(X.index).to_numpy(float)
    # events
    cal = pd.read_csv(DATA / "fixtures" / "cme_session_calendar.csv.gz", encoding="utf-8", dtype={"day": str})
    cal = cal[cal["root"] == "ES"].set_index("day")
    for c in ("fomc", "cpi", "empsit", "month_end", "quarter_end"):
        X[c] = cal[c].reindex(X.index).fillna(False).astype(bool).to_numpy()
    X["opex"] = [C.third_friday(s) for s in X.index]
    X["weekday"] = pd.to_datetime(pd.Series(X.index)).dt.day_name().to_numpy()
    X["year"] = X.index.str[:4]
    X["era"] = np.where(X.index >= ERA_SPLIT, "after_2022-05-16", "before")
    return {"X": X, "known": got, "sessions_all": int(len(S))}


def profile(X: pd.DataFrame) -> dict[str, Any]:
    g = X["gross"].to_numpy(float)
    net = g - COST
    days = X.index.to_numpy(str)
    years = (pd.Timestamp(str(days[-1])) - pd.Timestamp(str(days[0]))).days / 365.25
    win_all, bar_all = float((net > 0).mean()), float((g >= 2 * COST).mean())
    tot_oracle = float(net[net > 0].sum())
    n_all = len(g)
    am = X["abs_move"].to_numpy(float)
    f5a = X["F5"].abs().to_numpy(float)
    lines = {"take_everything": line_stats(g, np.ones(n_all, bool), years, days),
             "oracle_net_gt0": line_stats(g, FO.oracle_take(net), years, days),
             "oracle_at_bar": line_stats(g, FO.oracle_take_threshold(g, COST), years, days)}
    for q in (0.2, 0.4):
        lines[f"size_only_oracle_top{int(q * 100)}"] = line_stats(g, FO.top_fraction(am, q), years, days)
        lines[f"pre_entry_size_top{int(q * 100)}_by_absF5"] = line_stats(g, FO.top_fraction(f5a, q), years, days)

    def bs(m: np.ndarray) -> dict[str, Any]:
        return bucket_stats(g, m, years, tot_oracle, n_all, win_all, bar_all)
    prof: dict[str, Any] = {}
    one = {"f5z": "absF5_over_sigma", "rv_today": "realised_vol_to_1530", "sigma30_bp": "trailing_sigma30",
           "ivrv": "ivrv", "lniv": "ln_iv"}
    for col, nm in one.items():
        tb = terciles(X[col].to_numpy(float))
        prof[nm] = {f"t{k + 1}": bs(tb == k) for k in range(3)} | {"missing": int((tb < 0).sum())}
    q5 = terciles(X["f1"].to_numpy(float), 5)
    prof["d691_M1_size_forecast"] = {f"q{k + 1}": bs(q5 == k) for k in range(5)} | {"missing": int((q5 < 0).sum())}
    gs = X["G_SUM"].to_numpy(float)
    prof["gamma"] = {"G_SUM<0": bs(gs < 0), "G_SUM>=0": bs(gs >= 0),
                     "SPX<0": bs(X["G_SPX"].to_numpy(float) < 0), "SPX>=0": bs(X["G_SPX"].to_numpy(float) >= 0),
                     "ES<0": bs(X["G_ES"].to_numpy(float) < 0), "ES>=0": bs(X["G_ES"].to_numpy(float) >= 0),
                     "missing": int((~np.isfinite(gs)).sum())}
    gq = terciles(gs, 5)
    prof["G_SUM_quintile"] = {f"q{k + 1}": bs(gq == k) for k in range(5)}
    prof["side"] = {"long": bs(X["side"].to_numpy() > 0), "short": bs(X["side"].to_numpy() < 0)}
    prof["alignment_with_0930_1430"] = {"with": bs(X["align"].to_numpy(bool)), "against": bs(~X["align"].to_numpy(bool))}
    prof["events"] = {c: {"yes": bs(X[c].to_numpy(bool)), "no": bs(~X[c].to_numpy(bool))}
                      for c in ("fomc", "cpi", "empsit", "opex", "month_end", "quarter_end")}
    prof["weekday"] = {w: bs(X["weekday"].to_numpy() == w) for w in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")}
    prof["year"] = {y: bs(X["year"].to_numpy() == y) for y in sorted(X["year"].unique())}
    prof["era"] = {e: bs(X["era"].to_numpy() == e) for e in ("before", "after_2022-05-16")}
    t_f1, t_iv, t_f5 = terciles(X["f1"].to_numpy(float)), terciles(X["ivrv"].to_numpy(float)), terciles(X["f5z"].to_numpy(float))
    side = X["side"].to_numpy()
    prof["two_way"] = {
        "M1_tercile_x_side": {f"M1t{a + 1}_{s}": bs((t_f1 == a) & (side == sv)) for a in range(3) for s, sv in (("long", 1), ("short", -1))},
        "ivrv_tercile_x_absF5_tercile": {f"iv{a + 1}_f5{b_ + 1}": bs((t_iv == a) & (t_f5 == b_)) for a in range(3) for b_ in range(3)},
        "G_SUM_sign_x_absF5_tercile": {f"{'neg' if s < 0 else 'pos'}_f5{b_ + 1}": bs(((gs < 0) if s < 0 else (gs >= 0)) & (t_f5 == b_))
                                       for s in (-1, 1) for b_ in range(3)}}
    def count(node: Any) -> int:
        if isinstance(node, dict) and "n" in node:
            return 1
        return sum(count(v) for v in node.values()) if isinstance(node, dict) else 0
    n_buckets = count(prof)
    # the accuracy curve (D690's library) with per-draw Sharpe, and each input's Spearman
    rng = np.random.default_rng(SEED)
    curve = {}
    for q in (0.2, 0.4):
        rows = FO.partial_oracle_curve(g, net, RHOS, q, 200, rng)
        rng2 = np.random.default_rng(SEED + int(q * 100))
        z = FO.normal_scores(g)
        for row in rows:
            sh = []
            for _ in range(200):
                keep = FO.top_fraction(FO._partial(z, row["rho"], rng2), q)
                x = net[keep]
                sh.append(float(x.mean() / x.std(ddof=1) * math.sqrt(keep.sum() / years)))
            row["sharpe_per_trade_mean"] = float(np.mean(sh))
        curve[f"top{int(q * 100)}"] = rows
    spear = {}
    for col in ("f5z", "rv_today", "sigma30_bp", "f1", "ivrv", "lniv", "G_SUM", "G_SPX", "G_ES"):
        x = X[col].to_numpy(float)
        ok = np.isfinite(x)
        spear[col] = {"n": int(ok.sum()), "spearman_with_gross": FO.spearman(x[ok], g[ok]),
                      "spearman_with_abs_move": FO.spearman(x[ok], am[ok])}
    return {"years": years, "candidates": n_all, "overall_win": win_all, "overall_bar": bar_all, "lines": lines,
            "profile": prof, "bucket_count": n_buckets, "accuracy_curve": curve, "input_spearman": spear}


# ================================================================================ selftest
def selftest() -> int:
    fired: list[str] = []

    def must_raise(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except D702Error:
            fired.append(name)
            return
        raise SystemExit(f"selftest: the {name} canary did not raise")
    rng = np.random.default_rng(1)
    days = [f"2019-01-{i:02d}" for i in range(1, 11)]
    cols = [f"{h:02d}:{m:02d}" for h in range(9, 16) for m in range(60) if (h, m) >= (9, 30)]
    close = pd.DataFrame(100 + np.cumsum(rng.normal(0, 0.05, (10, len(cols))), axis=1), index=days, columns=cols)
    open_ = pd.Series(100.0, index=days)
    close.loc[:, "15:34"] = close["15:34"] + 5.0  # a spike in the bar starting 15:34: only the canary reads it
    rv = rv_today(close, open_)
    rv_audit(close, open_, rv, days)
    must_raise("a realised volatility that reads the bar starting 15:30",
               lambda: rv_audit(close, open_, rv_today(close, open_, include_1530_bar=True), days))
    g = rng.normal(0, 40, 500)
    dd = np.array([f"{2016 + i // 70}-01-{1 + i % 28:02d}" for i in range(500)])
    lt = line_stats(g, np.ones(500, bool), 7.0, dd)
    lo = line_stats(g, FO.oracle_take(g - COST), 7.0, dd)
    if not (lo["mean_net"] > lt["mean_net"] and lo["win_net_gt0"] == 1.0):
        raise SystemExit("selftest: the oracle line is not the ceiling")
    tb = terciles(np.r_[np.arange(9.0), np.nan])
    if list(tb) != [0, 0, 0, 1, 1, 1, 2, 2, 2, -1]:
        raise SystemExit(f"selftest: terciles {list(tb)}")
    b = bucket_stats(g, np.r_[np.ones(250, bool), np.zeros(250, bool)], 7.0, float((g - COST)[g - COST > 0].sum()), 500, 0.4, 0.3)
    if not (b["n"] == 250 and 0 <= b["share_of_oracle_net"] <= 1):
        raise SystemExit("selftest: bucket_stats")
    print(f"selftest OK: {len(fired)} canary fired: {fired}; the rv second path agrees; the oracle line is the ceiling; "
          "terciles and bucket_stats behave. D618's known answer, D688's beta_G and D691's d-bar need the fixtures and run in --run.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.run:
        ap.print_help()
        return 1
    t0 = time.time()
    bd = build()
    res = {"spec": "D702 (c2e519f2)", "credit": "dealer gamma (GEX): SqueezeMetrics", "known_answer_d618": bd["known"],
           "sessions_in_d618_frame": bd["sessions_all"], **profile(bd["X"]), "runtime_min": round((time.time() - t0) / 60, 2)}
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    ln = res["lines"]
    print(json.dumps({k: {x: ln[k].get(x) for x in ("trades", "mean_gross", "mean_net", "win_net_gt0", "sharpe_per_trade", "sortino_per_trade")}
                      for k in ln}, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
