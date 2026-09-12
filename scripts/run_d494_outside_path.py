"""D494 -- direction from outside the price path on the day session. Target: ES/NQ day leg 10:00 -> 16:00 ET (h09_c -> h15_c) in dollars
at one micro. B1 cross-instrument overnight moves (ZN ZB 6E GC CL, 18:00 -> 09:00) x {ES, NQ}; B2 index-level Robintrook sentiment (34 core
NQ members, holder-count change 16:00 t-1 -> 09:00 t) x {ES, NQ}; B3 release-day gates (CPI, Employment Situation, scheduled FOMC) on D484's
plain log-MACD sign at the 09:00 bar x {ES, NQ}. 18 cells; exact rotation (N1) and the common-offset family maximum (N2). Spec 62404c7.

    python scripts/run_d494_outside_path.py --selftest
    python scripts/run_d494_outside_path.py --run [--out data/d494_outside_path.json]
"""
from __future__ import annotations
import argparse, glob, importlib.util, json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]; FIX = REPO / "data" / "fixtures" / "fut_sessions_hourly.csv.gz"; META = REPO / "data" / "fixtures" / "fut_sessions_hourly.meta.json"
SPECS = REPO / "data" / "futures_contract_specs.json"; CAL = REPO / "data" / "macro_release_calendar.json"; RT = REPO / "data" / "raw" / "robintrack" / "popularity_export"
IS = ("2016-01-04", "2023-12-29"); TARGETS = ("ES", "NQ"); MICRO = {"ES": "MES", "NQ": "MNQ"}; PREDICTORS = ("ZN", "ZB", "6E", "GC", "CL"); COST_RT = 3.0
RT_SPAN = ("2018-05-03", "2020-08-13"); RT_OUTAGE_ENDS = ("2019-01-30", "2020-01-16"); RT_MIN_NAMES = 30; ENTRY, EXIT = "h09_c", "h15_c"


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s); sys.modules[name] = m; s.loader.exec_module(m); return m


# ------------------------------------------------------------------------------------------ data
def load_sessions():
    T = pd.read_csv(FIX, dtype={"root": str, "day": str, "prev_day": str, "contract": str, "front_prev": str}); T = T[(T["day"] >= IS[0]) & (T["day"] <= IS[1]) & T["same_front"]]
    assert T["day"].max() <= IS[1], "[D] a session after 2023-12-29 reached the runner"; return T


def day_leg(T, root):
    """Per session: entry (10:00 print), exit (16:00 print), move in points; only sessions with both prints > 0."""
    d = T[T["root"] == root].set_index("day"); e, x = d[ENTRY], d[EXIT]; ok = (e > 0) & (x > 0); return pd.DataFrame({"entry": e[ok], "exit": x[ok], "move": (x - e)[ok]})


def overnight(T, root):
    d = T[T["root"] == root].set_index("day"); o, c = d["h18_o"], d["h09_o"]; ok = (o > 0) & (c > 0); return np.log(c[ok] / o[ok]).rename(f"on_{root}")


def robintrack_series(cal):
    """Equal-weighted mean log change in users_holding across the core members: last obs <= 16:00 ET of the prior trading day -> last obs <= 09:00 ET of day t."""
    names = cal["nq_core_members_2018_05_to_2020_08"]; frames = []
    for n in names:
        d = pd.read_csv(RT / f"{n}.csv"); t = pd.to_datetime(d["timestamp"], utc=True).dt.tz_convert("US/Eastern"); d = pd.DataFrame({"t": t, "u": d["users_holding"].astype(float)}); d["date"] = d["t"].dt.strftime("%Y-%m-%d")
        pre9 = d[d["t"].dt.hour * 60 + d["t"].dt.minute <= 9 * 60].groupby("date")["u"].last().rename("u09"); pre16 = d[d["t"].dt.hour * 60 + d["t"].dt.minute <= 16 * 60].groupby("date")["u"].last().rename("u16")
        frames.append(pd.concat([pre9, pre16], axis=1).assign(name=n))
    A = pd.concat(frames).reset_index().rename(columns={"index": "date"}); A = A.sort_values(["name", "date"]); A["u16_prev"] = A.groupby("name")["u16"].shift(1)
    A["dl"] = np.log(A["u09"] / A["u16_prev"]); A.loc[~np.isfinite(A["dl"]), "dl"] = np.nan
    g = A.groupby("date")["dl"].agg(["mean", "count"]); g = g[(g.index >= RT_SPAN[0]) & (g.index <= RT_SPAN[1])]
    # outage masking: the site-wide gaps end on these dates; the first day back has a 10-day change, drop it and the day after
    mask = pd.Series(True, index=g.index)
    for e in RT_OUTAGE_ENDS:
        mask[(g.index >= e) & (g.index <= (pd.Timestamp(e) + pd.Timedelta(days=3)).strftime("%Y-%m-%d"))] = False
    dropped = int((~mask).sum() + (g["count"] < RT_MIN_NAMES).sum()); s = g[mask & (g["count"] >= RT_MIN_NAMES)]["mean"].rename("rt")
    return s, dropped


def macd_sign_at_0900(T, root, D84):
    """D484's plain log-MACD histogram on the hourly series (its own series_for), read at the 09:00 bar of each session."""
    meta = json.loads(META.read_text()); d_all = pd.read_csv(FIX); s = D84.series_for(root, d_all, meta); hist = D84.macd_hist(s["log_close"]); n_seg = len(D84.SEGMENTS)
    days = d_all[(d_all["root"] == root) & d_all["same_front"] & d_all["day"].between(s["start"], IS[1])].sort_values("day", kind="stable")["day"].to_numpy()
    idx09 = D84.SEGMENTS.index("h09"); sig = np.sign(hist.reshape(-1, n_seg)[:, idx09]); pure = s["pure"].reshape(-1, n_seg)[:, idx09]
    return pd.Series(np.where(pure, sig, np.nan), index=days).rename("macd")


# ------------------------------------------------------------------------------------------ statistics
def side_diff(x, mv, usd):
    lo, hi = np.quantile(x, [1 / 3, 2 / 3]); return float((mv[x >= hi].mean() - mv[x <= lo].mean()) * usd)


def cell_stats(x, mv, sess, usd, key):
    k = max(int(round(0.01 * len(mv))), 1); srt = np.sort(mv * usd); lo, hi = np.quantile(x, [1 / 3, 2 / 3])
    return dict(cell=key, n=int(len(mv)), spearman=float(pd.Series(x).rank().corr(pd.Series(mv).rank())), side_diff_usd=side_diff(x, mv, usd), tercile_usd=dict(bottom=float(mv[x <= lo].mean() * usd), middle=float(mv[(x > lo) & (x < hi)].mean() * usd), top=float(mv[x >= hi].mean() * usd)),
                move_sd_usd=float(mv.std(ddof=1) * usd), trim1_move_usd=float(srt[k:-k].mean()), worst_session=str(sess[int(mv.argmin())]), usd_per_point=usd, cost_rt=COST_RT)


def gate_stats(gate, sig, mv, sess, usd, key):
    """B3: signed P&L (MACD sign x move) on gated sessions minus a weekday- and year-matched non-gated control (partner weights)."""
    pnl = sig * mv * usd; g = gate.astype(bool); code = _codes(sess); K = code.max() + 1
    cg = np.bincount(code[g], minlength=K).astype(float); cc = np.bincount(code[~g], minlength=K).astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        w = np.where(cc > 0, cg / cc, 0.0)[code]; w[g] = 0.0   # each control session carries the gated count of its (weekday, year) over the control count: a partner weighting
    ctrl = float((pnl * w).sum() / w.sum()) if w.sum() > 0 else float("nan"); on = float(pnl[g].mean())
    return dict(cell=key, n_gated=int(g.sum()), n_control=int((~g).sum()), gated_mean_usd=on, control_mean_usd=ctrl, diff_usd=on - ctrl, gated_abs_move_sd=float((mv[g] * usd).std(ddof=1)), control_abs_move_sd=float((mv[~g] * usd).std(ddof=1)), gated_hit=float((pnl[g] > 0).mean()), usd_per_point=usd)


_CODE_CACHE = {}


def _codes(sess):
    key = (len(sess), str(sess[0]), str(sess[-1]))
    if key not in _CODE_CACHE:
        t = pd.to_datetime(sess); _CODE_CACHE[key] = (t.dayofweek.to_numpy() + 7 * (t.year.to_numpy() - 2000)).astype(int)
    return _CODE_CACHE[key]


def rot_null(fn, x, T):
    return np.array([fn(np.roll(x, k)) for k in range(1, T)])


# ------------------------------------------------------------------------------------------ run
def run(out):
    t0 = time.time(); specs = json.loads(SPECS.read_text()); cal = json.loads(CAL.read_text()); T = load_sessions(); D84 = _load("d484", "d484_offdiagonal_and_macd.py")
    legs = {r: day_leg(T, r) for r in TARGETS}; usd = {r: specs[MICRO[r]]["usd_per_point"] for r in TARGETS}; print(f"D494 -- sessions {T['day'].min()}..{T['day'].max()}; day legs ES {len(legs['ES'])}, NQ {len(legs['NQ'])}", flush=True)
    res = dict(spec="62404c7", window=IS, cells={}, nulls={}, audits={}, dropped={}); series = {}
    # B1
    for p in PREDICTORS:
        on = overnight(T, p)
        for r in TARGETS:
            j = pd.concat([on, legs[r]["move"]], axis=1).dropna(); x, mv, sess = j.iloc[:, 0].to_numpy(), j["move"].to_numpy(), j.index.to_numpy(); key = f"B1 {p}->{r}"
            res["cells"][key] = cell_stats(x, mv, sess, usd[r], key); series[key] = ("side", x, mv, usd[r])
    # B2
    rt, dropped = robintrack_series(cal); res["dropped"]["robintrack_sessions"] = dropped
    for r in TARGETS:
        j = pd.concat([rt, legs[r]["move"]], axis=1).dropna(); x, mv, sess = j["rt"].to_numpy(), j["move"].to_numpy(), j.index.to_numpy(); key = f"B2 RT->{r}"
        res["cells"][key] = cell_stats(x, mv, sess, usd[r], key); series[key] = ("side", x, mv, usd[r])
    # B3
    gates = {"CPI": set(cal["cpi_release_days"]), "EMPSIT": set(cal["empsit_release_days"]), "FOMC": set(cal["fomc_statement_days"])}
    for r in TARGETS:
        ms = macd_sign_at_0900(T, r, D84); j = pd.concat([ms, legs[r]["move"]], axis=1).dropna(); j = j[j["macd"] != 0]; sig, mv, sess = j["macd"].to_numpy(), j["move"].to_numpy(), j.index.to_numpy()
        for gname, gset in gates.items():
            g = np.array([d in gset for d in sess]); key = f"B3 {gname}|{r}"; res["cells"][key] = gate_stats(g, sig, mv, sess, usd[r], key); series[key] = ("gate", g, sig, mv, sess, usd[r])
    # nulls: N1 exact per cell; N2 common-offset family max of |stat| over all 18 cells
    stats = {}; Tmin = min(len(s[1]) for s in series.values()); fam = np.zeros(Tmin - 1); sub = {"B1": np.zeros(Tmin - 1), "B2": np.zeros(Tmin - 1), "B3": np.zeros(Tmin - 1)}
    for key, s in series.items():
        if s[0] == "side":
            _, x, mv, u = s; fn = lambda xx: side_diff(xx, mv, u); obs = res["cells"][key]["side_diff_usd"]
        else:
            _, g, sig, mv, sess, u = s; fn = lambda gg: gate_stats(gg, sig, mv, sess, u, key)["diff_usd"]; obs = res["cells"][key]["diff_usd"]
        nl = rot_null(fn, s[1], len(s[1])); stats[key] = nl; res["nulls"][key] = dict(p50=float(np.quantile(nl, .5)), p95=float(np.quantile(nl, .95)), p05=float(np.quantile(nl, .05)), abs_p95=float(np.quantile(np.abs(nl), .95)), n=int(nl.size), observed=obs, above_abs_p95=bool(abs(obs) > np.quantile(np.abs(nl), .95)))
        a = np.abs(nl[:Tmin - 1]); fam = np.maximum(fam, a); sub[key[:2]] = np.maximum(sub[key[:2]], a)
        print(f"  {key:16s} n {res['cells'][key].get('n', res['cells'][key].get('n_gated')):>5}  stat {obs:+8.2f}  N1 |p95| {np.quantile(np.abs(nl), .95):7.2f}  p05/p95 {np.quantile(nl, .05):+7.2f}/{np.quantile(nl, .95):+7.2f}   ({(time.time()-t0)/60:.1f} min)", flush=True)
    res["nulls"]["family_max_abs"] = dict(all18=dict(p50=float(np.quantile(fam, .5)), p95=float(np.quantile(fam, .95)), n_offsets=int(Tmin - 1)), **{k: dict(p50=float(np.quantile(v, .5)), p95=float(np.quantile(v, .95))) for k, v in sub.items()})
    fp = res["nulls"]["family_max_abs"]["all18"]["p95"]; picks = [k for k in res["cells"] if res["nulls"][k]["above_abs_p95"] and abs(res["nulls"][k]["observed"]) > fp]; res["picks"] = picks
    print(f"\n  family max |stat| over 18 cells ({Tmin-1} common offsets): p50 {res['nulls']['family_max_abs']['all18']['p50']:.2f}  p95 {fp:.2f}   sub-family p95: " + "  ".join(f"{k} {v['p95']:.2f}" for k, v in res['nulls']['family_max_abs'].items() if k != 'all18'))
    print(f"  picks: {picks or 'none'}")
    # audits
    res["audits"]["F_columns"] = dict(entry=ENTRY, exit=EXIT, predictor_end="h09_o (09:00 open) / robintrack <= 09:00 / calendar date", note="entry at the 10:00 print is the close of the 09:00 bar; every predictor is stamped at or before 09:00")
    x, mv, u = series["B1 ZN->NQ"][1:]; res["audits"]["X_flip"] = bool(abs(side_diff(-x, mv, u) + side_diff(x, mv, u)) < 1e-9)
    # [F] shifted-predictor control: the predictor from the NEXT session must sit inside its own null (it cannot know today's move)
    xs = np.roll(x, -1); obs_s = side_diff(xs, mv, u); res["audits"]["F_shifted_predictor"] = dict(observed=obs_s, inside_null=bool(abs(obs_s) <= np.quantile(np.abs(stats["B1 ZN->NQ"]), .95)))
    wd_fomc = pd.to_datetime(cal["fomc_statement_days"]).dayofweek; wd_emp = pd.to_datetime([d for d in cal["empsit_release_days"] if d >= "2016-01-08"]).dayofweek
    res["audits"]["C_calendar"] = dict(fomc_non_wednesday=[d for d, w in zip(cal["fomc_statement_days"], wd_fomc) if w != 2], empsit_non_friday=[d for d, w in zip([d for d in cal["empsit_release_days"] if d >= "2016-01-08"], wd_emp) if w != 4])
    res["audits"]["S_sign"] = bool(side_diff(np.array([0., 1., 2.]), np.array([0., 1., 2.]), 5.0) > 0); res["audits"]["D_window"] = bool(T["day"].max() <= IS[1])
    print(f"  audits: X flip {res['audits']['X_flip']}, F shifted-predictor inside null {res['audits']['F_shifted_predictor']['inside_null']}, C calendar exceptions FOMC {res['audits']['C_calendar']['fomc_non_wednesday']} EMPSIT {res['audits']['C_calendar']['empsit_non_friday']}, S {res['audits']['S_sign']}, D {res['audits']['D_window']}")
    res["wall_min"] = round((time.time() - t0) / 60, 1); Path(out).write_text(json.dumps(res, indent=1, default=float)); print(f"wrote {out} in {res['wall_min']} min")


def selftest():
    rng = np.random.default_rng(4); x = rng.normal(size=500); mv = rng.normal(size=500); assert abs(side_diff(-x, mv, 5.0) + side_diff(x, mv, 5.0)) < 1e-9
    nl = rot_null(lambda xx: side_diff(xx, mv, 5.0), x, 500); assert abs(np.median(nl)) < 0.5; planted = 0.4 * x + rng.normal(size=500); assert side_diff(x, planted, 5.0) > np.quantile(np.abs(nl), .95)
    sess = np.array([str(d)[:10] for d in pd.bdate_range("2016-01-04", periods=500)]); g = np.zeros(500, bool); g[::20] = True; sig = np.sign(rng.normal(size=500)); gs = gate_stats(g, sig, mv, sess, 5.0, "t")
    assert gs["n_gated"] == 25 and np.isfinite(gs["control_mean_usd"]); mv2 = mv.copy(); mv2[g] += 3 * sig[g]; gs2 = gate_stats(g, sig, mv2, sess, 5.0, "t"); assert gs2["diff_usd"] > gs["diff_usd"] + 10, "a planted gated edge must raise the gated-minus-control difference"
    print("selftest OK: [X] flip negates, rotation centred, planted side effect detected, gate control is finite and a planted gated edge is detected")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--run", action="store_true"); ap.add_argument("--out", default=str(REPO / "data" / "d494_outside_path.json")); a = ap.parse_args()
    if a.selftest:
        selftest()
    if a.run:
        run(a.out)
