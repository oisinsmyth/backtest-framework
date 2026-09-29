"""D666 post hoc diagnostic and thread search (the principal: "a diagnostic on this, a statistical analysis of the
results, trades by year etc.. I would like you to find a thread we can pull on"). In-sample only through D666's own
sealed functions; changes no verdict. SqueezeMetrics GEX credited; output statistics only (licence-guarded).

    uv run python scripts/diag_d666.py --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"

Both constructions -- the RE-BREAK (the hypothesis) and the PLAIN break (its control) -- are rebuilt per trade with
D666's scan / plain_break / exit_trade, and each trade carries: entry clock, side, the four exits' gross, the max
favourable / adverse excursion to 60 min and to the close, the three confluences (gap, A7, TICK) and the fade veto
(D666 s.5), dealer short gamma (ES: SPX GEX prior row; NQ: own book), and the prior 20-day sigma tercile.
A  mechanics: reproduction of the committed means; fills; excursions (why the retest hurts); exit reasons.
B  statistics: by year; long/short; entry hour; weekday; vol tercile; gamma; each confluence and the count.
C  the oracle: the favourable excursion available after entry, against cost.
D  the thread search: every subset in one table, with the count of subsets and the number expected past |t| 2 by chance.
Writes data/diag_d666.json.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d662_gamma_product as S  # noqa: E402
import stage0_d663_per_root_gamma_break as T  # noqa: E402
import stage0_d666_rebreak as X  # noqa: E402

OUT = REPO / "data" / "diag_d666.json"


def excursions(bb: dict, i: int, D: int, entry: float) -> tuple[float, float, float, float]:
    m, h, l = bb["m"], bb["h"], bb["l"]
    after = np.arange(i + 1, len(m))
    after = after[m[after] <= X.CLOSE_BAR]
    if not len(after):
        return (np.nan,) * 4
    w60 = after[m[after] <= m[i] + 60]
    fav = lambda ix: float(D * ((h[ix].max() if D > 0 else l[ix].min()) / entry - 1) * 1e4) if len(ix) else np.nan  # noqa: E731
    adv = lambda ix: float(-D * ((l[ix].min() if D > 0 else h[ix].max()) / entry - 1) * 1e4) if len(ix) else np.nan  # noqa: E731
    return fav(w60), adv(w60), fav(after), adv(after)


def trades_job(args: tuple) -> list[dict]:
    r, frame, bars_r, costs = args
    COST_USD, USD_PT = costs
    out = []
    for s, d in frame.iterrows():
        bb = bars_r.get(s)
        if bb is None:
            continue
        Lh, Ll, A = float(d["prior_high"]), float(d["prior_low"]), float(d["atr20"])
        sc = X.scan(bb, Lh, Ll, A)
        e = sc if sc is not None and sc.get("i") is not None else None
        p = X.plain_break(bb, Lh, Ll, A)
        for kind, t in (("rebreak", e), ("plain", p)):
            if t is None:
                continue
            i, D, entry = t["i"], t["D"], t["entry"]
            sig_left = float(d["sig20"]) * math.sqrt(max(X.CLOSE_BAR + 1 - int(bb["m"][i]), 1) / 390)
            P_pts = entry * sig_left * float(d["m_gamma"]) / 1e4
            rec = {"construct": kind, "root": r, "session": s, "D": D, "minute": int(bb["m"][i]), "entry": entry,
                   "cost_bp": COST_USD / USD_PT / entry * 1e4, "sig20": float(d["sig20"]), "short_gamma": bool(d["m_gamma"] > 1),
                   "open": float(d["open"]), "prior_close": float(d["prior_close"]), "atr20": A,
                   "gapped_through_stop": bool((D > 0 and bb["o"][i] > t["stop"]) or (D < 0 and bb["o"][i] < t["stop"])),
                   "fill_beyond_stop_bp": float(D * (entry / t["stop"] - 1) * 1e4)}
            if kind == "rebreak":
                rec["wait_after_touch"] = int(bb["m"][i]) - int(t["tau"])
            for x in X.EXITS:
                px, why = X.exit_trade(bb, i, D, entry, t["L"], A, P_pts, x)
                rec[f"{x}_gross"] = D * (px / entry - 1) * 1e4
                rec[f"{x}_why"] = why
            rec["mfe60"], rec["mae60"], rec["mfe_close"], rec["mae_close"] = excursions(bb, i, D, entry)
            out.append(rec)
    return out


def add_confluences(tr: pd.DataFrame, data_root: Path, tabs: dict, R) -> pd.DataFrame:
    a7 = pd.read_csv(REPO / "data" / "opening" / "a7.csv", encoding="utf-8", dtype={"session": str})
    a7 = a7[a7["session"] < T.RESERVED_FROM]
    cal = sorted({s for r in R.ROOTS for s in tabs[r].index if tabs[r].loc[s, "usable"] and s >= "2016-01-04"})
    pf = {t: R.walk_forward(R.dataset(tabs, t, t), list(R.S_A), cal).set_index(["root", "session"])["p_FADE"]
          for t in X.CHECKPOINTS}
    thr = {(t, r): pf[t].xs(r, level="root").sort_index().shift(1).rolling(252, min_periods=60).quantile(0.8)
           for t in X.CHECKPOINTS for r in ("ES", "NQ")}
    with ProcessPoolExecutor(max_workers=2) as pool:
        ex = dict(pool.map(T.extract_job, [(T.SHOCK_SYMS[r]["tick"], str(T.SC_DATA / f"{T.SHOCK_SYMS[r]['tick']}.scid"))
                                           for r in ("ES", "NQ")]))
    for e_ in ex.values():
        T.assert_sealed(e_)
    parts = []
    for (kind, r), g in tr.groupby(["construct", "root"]):
        g = g.copy()
        gap = g["D"] * (g["open"] / g["prior_close"] - 1) * 100
        g["gap_al"] = gap > 0.10 * g["atr20"] / g["prior_close"] * 100
        ar = a7[a7["root"] == r].set_index("session")
        a7v = []
        for _, rec in g.iterrows():
            cps = [t for t in X.CHECKPOINTS if X.hm(t) <= rec["minute"]]
            v = ar.at[rec["session"], f"a7_{cps[-1]}"] if cps and rec["session"] in ar.index else np.nan
            a7v.append(rec["D"] * v if np.isfinite(v) else np.nan)
        g["a7_signed"] = a7v
        g["a7_al"] = g["a7_signed"] > 0
        sym = T.SHOCK_SYMS[r]["tick"]
        gt = {"tick": T.gate_f(ex[sym], "tick"), "up": {"usable": False}, "dn": {"usable": False}}
        rows = pd.DataFrame({"D": g["D"].to_numpy(), "eb": g["minute"].to_numpy()}, index=g["session"].to_numpy())
        rows = rows[~rows.index.duplicated()]
        sh = T.shocks(rows, "09:30", ex[sym], None, None, gt)
        g["tick_z"] = g["session"].map(sh["s_tick"])
        g["tick_al"] = g["tick_z"] > 0.5
        g["count"] = g[["gap_al", "a7_al", "tick_al"]].astype(int).sum(axis=1)
        veto = []
        for _, rec in g.iterrows():
            cps = [t for t in X.CHECKPOINTS if X.hm(t) <= rec["minute"]]
            v = False
            if cps:
                ser, th = pf[cps[-1]].xs(r, level="root"), thr[(cps[-1], r)]
                s_ = rec["session"]
                if s_ in ser.index and np.isfinite(th.get(s_, np.nan)):
                    v = bool(ser[s_] >= th[s_] and -np.sign(rec["open"] - rec["prior_close"]) == -rec["D"])
            veto.append(v)
        g["veto"] = veto
        parts.append(g)
    return pd.concat(parts)


def stat(x: pd.Series, R) -> dict:
    x = x.dropna().to_numpy(float)
    if len(x) < 8:
        return {"n": int(len(x))}
    t, se = R.nw_t(x)
    return {"n": int(len(x)), "mean": float(x.mean()), "t": float(t), "median": float(np.median(x)), "win": float((x > 0).mean())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    V = S.load_v2()
    R = V.R
    b, use, Gd = V.load_inputs(a.data_root, False)
    tabs = R.session_table(b, use)
    bars = R.bar_arrays(b)
    dix = pd.read_csv(a.data_root / "raw" / "squeezemetrics" / "DIX.csv", encoding="utf-8", dtype={"date": str})
    gex = dix[dix["date"] < T.RESERVED_FROM].set_index("date")["gex"].astype(float).sort_index()
    frames = {}
    for r in ("ES", "NQ"):
        d = T.root_frame(b, tabs[r], r)
        d = d[np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)].copy()
        d["gd_spx"] = T.gex_prior(gex, d.index)
        short = (d["gd_spx"] < 0) if r == "ES" else (Gd[r].reindex(d.index) < 0)
        d["m_gamma"] = np.where(short.fillna(False), 1.5, 1.0)
        frames[r] = d
    jobs = [(r, frames[r], {s: bars[(r, s)] for s in frames[r].index if (r, s) in bars}, (R.COST_USD[r], R.USD_PER_POINT[r]))
            for r in ("ES", "NQ")]
    with ProcessPoolExecutor(max_workers=2) as pool:
        tr = pd.DataFrame([x for part in pool.map(trades_job, jobs) for x in part])
    tr = add_confluences(tr, a.data_root, tabs, R)
    tr["year"] = tr["session"].str[:4]
    tr["hour"] = (tr["minute"] // 60).astype(int)
    tr["dow"] = pd.to_datetime(tr["session"]).dt.dayofweek
    tr["vol_tercile"] = tr.groupby("root")["sig20"].transform(lambda v: pd.qcut(v.rank(method="first"), 3, labels=False))
    for x in X.EXITS:
        tr[f"{x}_net"] = tr[f"{x}_gross"] - tr["cost_bp"]
    tr = tr.sort_values(["root", "construct", "session"])
    out: dict = {"spec": "post hoc diagnostic of D666 (45bae60)", "credit": "dealer gamma (GEX): SqueezeMetrics",
                 "A": {}, "B": {}, "C": {}, "D": {}}
    committed = json.loads((REPO / "data" / "stage0_d666_rebreak.json").read_text(encoding="utf-8"))["cells"]
    rep = {}
    for r in ("ES", "NQ"):
        g = tr[(tr["root"] == r) & (tr["construct"] == "rebreak")]
        for x in X.EXITS:
            rep[f"{r}_{x}"] = {"here": float(g[f"{x}_gross"].mean()), "committed": committed[f"{r}_{x}"]["gate1"]["gross_mean"]}
            if abs(rep[f"{r}_{x}"]["here"] - rep[f"{r}_{x}"]["committed"]) > 1e-9:
                raise SystemExit(f"the rebuild differs from the committed run: {r} {x} {rep[f'{r}_{x}']}")
    out["A"]["A1_reproduces_committed"] = True
    fills, exc, reasons = {}, {}, {}
    for (kind, r), g in tr.groupby(["construct", "root"]):
        key = f"{r}_{kind}"
        fills[key] = {"n": int(len(g)), "gapped_through_stop": float(g["gapped_through_stop"].mean()),
                      "fill_beyond_stop_bp_mean": float(g["fill_beyond_stop_bp"].mean()),
                      "entry_clock_median": f"{int(g['minute'].median()) // 60:02d}:{int(g['minute'].median()) % 60:02d}",
                      "wait_after_touch_median": float(g["wait_after_touch"].median()) if "wait_after_touch" in g and g["wait_after_touch"].notna().any() else None}
        exc[key] = {k: float(g[k].mean()) for k in ("mfe60", "mae60", "mfe_close", "mae_close")}
        exc[key]["mfe_minus_mae_60"] = exc[key]["mfe60"] - exc[key]["mae60"]
        exc[key]["mfe_minus_mae_close"] = exc[key]["mfe_close"] - exc[key]["mae_close"]
        reasons[key] = {x: {w: {"n": int((g[f"{x}_why"] == w).sum()), "gross_mean": float(g.loc[g[f"{x}_why"] == w, f"{x}_gross"].mean())}
                            for w in g[f"{x}_why"].unique()} for x in X.EXITS}
    out["A"]["A2_fills"] = fills
    out["A"]["A3_excursions"] = exc
    out["A"]["A4_exit_reasons"] = reasons
    # B
    by = {}
    for (kind, r), g in tr.groupby(["construct", "root"]):
        by[f"{r}_{kind}"] = {y: {"n": int(len(gy)), **{x: round(float(gy[f"{x}_gross"].mean()), 3) for x in X.EXITS},
                                 "E4_net": round(float(gy["E4_net"].mean()), 3)} for y, gy in g.groupby("year")}
    out["B"]["B1_by_year_gross"] = by
    dims = {"side": lambda g: np.where(g["D"] > 0, "long", "short"), "hour": lambda g: g["hour"].astype(str),
            "dow": lambda g: g["dow"].astype(str), "vol_tercile": lambda g: g["vol_tercile"].astype(str),
            "short_gamma": lambda g: g["short_gamma"].astype(str), "gap_al": lambda g: g["gap_al"].astype(str),
            "a7_al": lambda g: g["a7_al"].astype(str), "tick_al": lambda g: g["tick_al"].astype(str),
            "count": lambda g: g["count"].astype(str), "veto": lambda g: g["veto"].astype(str),
            "era": lambda g: np.where(g["session"] >= "2022-05-16", "post0dte", "pre0dte")}
    splits, scan = {}, []
    for (kind, r), g in tr.groupby(["construct", "root"]):
        key = f"{r}_{kind}"
        splits[key] = {}
        for dn, f in dims.items():
            lab = pd.Series(f(g), index=g.index)
            splits[key][dn] = {}
            for v, gv in g.groupby(lab):
                row = {x: stat(gv[f"{x}_gross"], R) for x in X.EXITS}
                splits[key][dn][str(v)] = row
                for x in X.EXITS:
                    s_ = row[x]
                    if s_.get("n", 0) >= 60:
                        yrs = gv.groupby("year")[f"{x}_gross"].mean()
                        scan.append({"cell": f"{key}|{dn}={v}|{x}", "n": s_["n"], "gross": s_["mean"], "t": s_["t"],
                                     "net": float(gv[f"{x}_net"].mean()), "years_positive": int((yrs > 0).sum()),
                                     "years": int(len(yrs)), "cost": float(gv["cost_bp"].mean())})
    out["B"]["B2_splits"] = splits
    # C: the favourable excursion available after entry, the most any exit could take
    out["C"] = {k: {"mfe_close_mean": v["mfe_close"], "mfe60_mean": v["mfe60"], "cost_bp": float(tr[(tr["root"] + "_" + tr["construct"]) == k]["cost_bp"].mean()),
                    "mfe_minus_mae_close": v["mfe_minus_mae_close"]} for k, v in exc.items()}
    # D: the thread search
    sc = pd.DataFrame(scan)
    n_tests = int(len(sc))
    out["D"] = {"subsets_scanned": n_tests, "expected_abs_t_over_2_by_chance": round(0.0455 * n_tests, 1),
                "observed_t_over_2": int((sc["t"] > 2).sum()), "observed_t_below_minus_2": int((sc["t"] < -2).sum()),
                "top_by_t": sc.sort_values("t", ascending=False).head(25).round(3).to_dict("records"),
                "net_positive_with_t_over_2": sc[(sc["t"] > 2) & (sc["net"] > 0)].sort_values("t", ascending=False).round(3).to_dict("records")}
    # the plain break's own numbers, per root and exit, with by-year consistency
    pl = {}
    for r in ("ES", "NQ"):
        g = tr[(tr["root"] == r) & (tr["construct"] == "plain")]
        for x in X.EXITS:
            s_ = stat(g[f"{x}_gross"], R)
            yrs = g.groupby("year")[f"{x}_gross"].mean()
            pl[f"{r}_{x}"] = {**s_, "net": float(g[f"{x}_net"].mean()), "years_positive": int((yrs > 0).sum()), "years": int(len(yrs))}
    out["D"]["plain_break_own_stats"] = pl
    T.licence_guard(out)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"A1": out["A"]["A1_reproduces_committed"], "A2": out["A"]["A2_fills"], "A3": out["A"]["A3_excursions"],
                      "D_summary": {k: out["D"][k] for k in ("subsets_scanned", "expected_abs_t_over_2_by_chance",
                                                           "observed_t_over_2", "observed_t_below_minus_2")},
                      "plain": pl}, indent=1, default=lambda v: round(v, 3)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
