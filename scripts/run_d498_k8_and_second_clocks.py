"""D498 -- K8 (long the NQ day session after a down day) as a declared component, with three declared second-clock cells: E1 turn-of-month
long day sessions, E2 FOMC decision days long 09:30 -> 14:00, E3 the first-30 fade at 15:30. Spec committed in b463999 BEFORE this file.
Entry at the window's first bar open + tick in the trade direction, exit at the window's last bar close; one MES / one MNQ; $3. In-sample
2016-01-04 .. 2023-12-29 (the runner raises past 2023); the forward read of K8 is a separate guarded command.

    uv run python -u scripts/run_d498_k8_and_second_clocks.py --run
    uv run python -u scripts/run_d498_k8_and_second_clocks.py --forward --principals-word     # K8 on 2024-01-02 .. 2026-09-09; refuses without the flag
    uv run python -u scripts/run_d498_k8_and_second_clocks.py --selftest
"""
from __future__ import annotations
import argparse, importlib.util, json, math, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
D90 = _load("d490r", "run_d490_range_reversion.py"); D66 = D90.D66
LO, HI = "2016-01-04", "2023-12-29"; FWD_LO, FWD_HI = "2024-01-02", "2026-09-09"; ROOTS = ("NQ", "ES"); MULT = D90.MULT; TICK = D90.TICK; COST = D90.COST; ACCOUNT = D90.ACCOUNT; NBAR = D90.NBAR
B_0959, B_1359, B_1530, B_LAST = 29, 269, 360, 389; SUB = {"2016-2020": ("2016-01-04", "2020-12-31"), "2021-2023": ("2021-01-04", "2023-12-29")}
OUT = REPO / "data" / "d498_k8_second_clocks.json"; OUT_FWD = REPO / "data" / "d498_k8_forward.json"
# FOMC scheduled decision days (the second day of each meeting) from the Fed's calendars; 2020's cancelled March 17-18 meeting and the
# unscheduled decisions (2020-03-03, 2020-03-15 a Sunday, and the other 2020 notation votes) are excluded.
FOMC = ["2016-01-27", "2016-03-16", "2016-04-27", "2016-06-15", "2016-07-27", "2016-09-21", "2016-11-02", "2016-12-14",
        "2017-02-01", "2017-03-15", "2017-05-03", "2017-06-14", "2017-07-26", "2017-09-20", "2017-11-01", "2017-12-13",
        "2018-01-31", "2018-03-21", "2018-05-02", "2018-06-13", "2018-08-01", "2018-09-26", "2018-11-08", "2018-12-19",
        "2019-01-30", "2019-03-20", "2019-05-01", "2019-06-19", "2019-07-31", "2019-09-18", "2019-10-30", "2019-12-11",
        "2020-01-29", "2020-04-29", "2020-06-10", "2020-07-29", "2020-09-16", "2020-11-05", "2020-12-16",
        "2021-01-27", "2021-03-17", "2021-04-28", "2021-06-16", "2021-07-28", "2021-09-22", "2021-11-03", "2021-12-15",
        "2022-01-26", "2022-03-16", "2022-05-04", "2022-06-15", "2022-07-27", "2022-09-21", "2022-11-02", "2022-12-14",
        "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14", "2023-07-26", "2023-09-20", "2023-11-01", "2023-12-13",
        "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
        "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10",
        "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09"]
CELLS = {"K8": dict(win=(0, B_LAST), name="long the day session after a down day"), "E1": dict(win=(0, B_LAST), name="turn-of-month long day sessions"), "E2": dict(win=(0, B_1359), name="FOMC decision day long 09:30->14:00"), "E3": dict(win=(B_1530, B_LAST), name="the first-30 fade at 15:30")}


# ------------------------------------------------------------------------------------------ states and windows
def tom_mask(days):
    """Last trading day of a month and the first three of the next, on the session calendar given."""
    m = np.array([d[:7] for d in days]); out = np.zeros(len(days), bool)
    for i in range(len(days) - 1):
        if m[i + 1] != m[i]:
            out[i] = True                      # the last session of a month
            out[i + 1:i + 4] = True            # the first three sessions of the next
    return out


def states(d):
    """Per session row: dir arrays (+1/-1/0) and window returns w (bp) for each cell; also the day-session R."""
    full = d["full"]; O = d["O"]; C = d["C"]; days = d["days"]; n = len(days)
    R = np.where(full, (C[:, B_LAST] / O[:, 0] - 1) * 1e4, np.nan); w14 = np.where(full, (C[:, B_1359] / O[:, 0] - 1) * 1e4, np.nan); w30 = np.where(full, (C[:, B_LAST] / O[:, B_1530] - 1) * 1e4, np.nan)
    first30 = np.where(full, np.sign(C[:, B_0959] - O[:, 0]), np.nan)
    dK8 = np.zeros(n); dK8[1:] = np.where(np.isfinite(R[:-1]) & (R[:-1] < 0), 1.0, 0.0)
    dE1 = tom_mask(days).astype(float); dE2 = np.isin(days, FOMC).astype(float); dE3 = np.where(np.isfinite(first30), -first30, 0.0)
    prev_up = np.zeros(n, bool); prev_up[1:] = np.isfinite(R[:-1]) & (R[:-1] > 0)
    return dict(R=R, w={"K8": R, "E1": R, "E2": w14, "E3": w30}, dirs={"K8": dK8, "E1": dE1, "E2": dE2, "E3": dE3}, other={"K8": prev_up, "E1": ~(dE1 > 0), "E2": ~(dE2 > 0)})


def trades(d, cell, dirs, mult, mask):
    a, b = CELLS[cell]["win"]; rows = []
    for t in np.flatnonzero(mask & (dirs != 0) & d["full"]):
        s = dirs[t]; entry = d["O"][t, a] + s * TICK; exit_ = d["C"][t, b]; pts = s * (exit_ - entry); lo = np.nanmin(d["L"][t, a:b + 1]); hi = np.nanmax(d["H"][t, a:b + 1])
        mae = (lo - entry) if s > 0 else (entry - hi); rows.append(dict(day=d["days"][t], side=int(s), entry=float(entry), exit=float(exit_), pnl_pts=float(pts), gross_usd=float(pts * mult), net_usd=float(pts * mult - COST), bp=float(pts / entry * 1e4), mae_usd=float(mae * mult)))
    return pd.DataFrame(rows)


def z_diff(x, y):
    return float((x.mean() - y.mean()) / math.sqrt(x.var(ddof=1) / x.size + y.var(ddof=1) / y.size)) if x.size >= 5 and y.size >= 5 else float("nan")


def cell_z(S, cell, mask, dirs=None):
    """The family statistic: z of (gated mean - other side) in the trade direction; for E3 (whose complement is its negative) z = mean/SE."""
    dd = S["dirs"][cell] if dirs is None else dirs; w = S["w"][cell]; ok = mask & np.isfinite(w); g = ok & (dd != 0); x = dd[g] * w[g]
    if x.size < 5:
        return float("nan"), x, None
    if cell == "E3":
        return float(x.mean() / (x.std(ddof=1) / math.sqrt(x.size))), x, None
    oth = S["other"][cell] if dirs is None else (ok & (dd == 0)); y = w[ok & oth & (dd == 0)] if cell == "K8" else w[ok & oth]
    return z_diff(x, y), x, y


def rotation_null(S, cell, mask):
    w = S["w"][cell]; idx = np.flatnonzero(mask & np.isfinite(w)); wv = w[idx]; dd = S["dirs"][cell][idx]; T = len(idx); out = np.empty(T - 2)
    for k in range(2, T):
        r = np.roll(dd, k); g = r != 0; out[k - 2] = float((r[g] * wv[g]).mean()) if g.sum() >= 5 else np.nan
    return out[np.isfinite(out)]


def family_max(SS, masks, cells=("K8", "E1", "E2", "E3")):
    T = min(int((masks[r] & np.isfinite(SS[r]["R"])).sum()) for r in ROOTS); out = np.full(T - 2, -np.inf)
    for k in range(2, T):
        best = -np.inf
        for r in ROOTS:
            S = SS[r]; mask = masks[r]
            for c in cells:
                w = S["w"][c]; idx = np.flatnonzero(mask & np.isfinite(w)); dd = np.roll(S["dirs"][c][idx], k); wv = w[idx]; g = dd != 0; x = dd[g] * wv[g]
                if x.size < 5:
                    continue
                if c == "E3":
                    z = float(x.mean() / (x.std(ddof=1) / math.sqrt(x.size)))
                else:
                    oth = np.roll(S["other"][c][idx], k); y = wv[oth & (dd == 0)] if c == "K8" else wv[oth]; z = z_diff(x, y)
                if np.isfinite(z):
                    best = max(best, z)
        out[k - 2] = best
    return out[np.isfinite(out)]


def summarise(tr, cal, x, y, z, n1, label, log=print):
    g = tr["gross_usd"].to_numpy(); k = max(1, int(round(0.01 * g.size))); gs = np.sort(g); daily = tr.groupby("day")["net_usd"].sum(); ser = D66.series_on(cal, daily.index, daily.values).to_numpy(); yrs = np.array([s[:4] for s in cal])
    flips = np.random.default_rng(3).choice([-1.0, 1.0], size=(1000, ser.size)); sflip = float(np.quantile([D66.sharpe(ser * f) for f in flips], .95)); sub = {}
    for sk, (slo, shi) in SUB.items():
        m = (tr["day"] >= slo) & (tr["day"] <= shi); sub[sk] = dict(n=int(m.sum()), bp=float(tr[m]["bp"].mean()) if m.sum() else float("nan"))
    c = dict(trades=int(len(tr)), share=float(len(tr) / len(cal)), gross_mean=float(g.mean()), gross_median=float(np.median(g)), trimmed=float(gs[k:-k].mean()), bp_mean=float(x.mean()), bp_se=float(x.std(ddof=1) / math.sqrt(x.size)), net_mean=float(g.mean() - COST), hit=float((g > 0).mean()), payoff=float(g[g > 0].mean() / -g[g < 0].mean()) if (g < 0).any() and (g > 0).any() else float("nan"), skew=float(pd.Series(g).skew()),
             mae_p50=float(np.quantile(tr["mae_usd"], .5)), mae_p95=float(np.quantile(tr["mae_usd"], .05)), mae_worst=float(tr["mae_usd"].min()), days_below_2pct=int((ser < -0.02 * ACCOUNT).sum()), net_sharpe=D66.sharpe(ser), net_sharpe_se=D66.sharpe_boot(ser, cal), sharpe_flip_p95=sflip, other_bp=float(y.mean()) if y is not None else None, other_n=int(y.size) if y is not None else None, z=z,
             N1=dict(p50=float(np.median(n1)), p95=float(np.quantile(n1, .95))), by_year_bp={yv: float(tr[tr["day"].str[:4] == yv]["bp"].mean()) for yv in sorted(set(yrs)) if (tr["day"].str[:4] == yv).sum()}, by_year_sharpe={yv: D66.sharpe(ser[yrs == yv]) for yv in sorted(set(yrs))}, sub=sub, C_c=bool(pd.Series(g).skew() >= -0.5), C_d=bool(ser.std(ddof=1) <= 0.01 * ACCOUNT))
    c["clears_N1"] = c["bp_mean"] > c["N1"]["p95"]; c["_ser"] = ser
    log(f"  {label:34s} {c['trades']:4d} trades ({100*c['share']:4.1f}%)  gross ${c['gross_mean']:+6.2f} (med {c['gross_median']:+.2f}, trim {c['trimmed']:+.2f}) = {c['bp_mean']:+5.1f} bp ({c['bp_se']:.1f})  other {('%+.1f' % c['other_bp']) if c['other_bp'] is not None else '  (neg)'} bp  z {z:+.2f}  hit {100*c['hit']:.1f}%  skew {c['skew']:+.2f}  MAE p50/p95/worst {c['mae_p50']:.0f}/{c['mae_p95']:.0f}/{c['mae_worst']:.0f}  net Sharpe {c['net_sharpe']:+.2f} +- {c['net_sharpe_se']:.2f}  N1 p95 {c['N1']['p95']:+.1f} {'*' if c['clears_N1'] else ' '}  sub {sub['2016-2020']['bp']:+.1f}/{sub['2021-2023']['bp']:+.1f}")
    log(f"      by year bp: " + " ".join(f"{yv}:{v:+.0f}" for yv, v in c["by_year_bp"].items()))
    return c


def run():
    t0 = time.time(); print("D498 -- K8 and three second-clock cells, intraday, one micro, $3\n      spec committed in b463999 BEFORE this ran; 2016-2023; 2024+ unread; family = max over 8 cell-roots of the difference z under a common rotation")
    SS, masks, res, sers = {}, {}, {}, {}
    for root in ROOTS:
        d = D90.load_root(root, LO, HI); assert max(d["days"]) <= HI; S = states(d); mask = d["trade"]; cal = pd.Index(d["days"][mask]); SS[root] = S; masks[root] = mask; res[root] = {}; print(f"\n{root}: {int(mask.sum())} full sessions; FOMC days in the calendar {int((S['dirs']['E2'][mask] > 0).sum())}, TOM days {int((S['dirs']['E1'][mask] > 0).sum())}")
        for cell in CELLS:
            tr = trades(d, cell, S["dirs"][cell], MULT[root], mask); z, x, y = cell_z(S, cell, mask); n1 = rotation_null(S, cell, mask); c = summarise(tr, cal, x, y, z, n1, f"{cell} {CELLS[cell]['name']}"); sers[(root, cell)] = c.pop("_ser"); res[root][cell] = c
            tr.to_csv(REPO / "data" / f"d498_trades_{root}_{cell}.csv.gz", index=False, compression="gzip")
        ung = D66.series_on(cal, d["days"][mask & d["full"]], (S["R"][mask & d["full"]] / 1e4) * d["O"][mask & d["full"], 0] * MULT[root] - COST).to_numpy(); sers[(root, "ungated")] = ung
        for cell in CELLS:
            res[root][cell]["rho_K8"] = float(np.corrcoef(sers[(root, cell)], sers[(root, "K8")])[0, 1]); res[root][cell]["rho_ungated"] = float(np.corrcoef(sers[(root, cell)], ung)[0, 1])
        print("  rho with K8 / with the ungated day session: " + "  ".join(f"{c}: {res[root][c]['rho_K8']:+.2f} / {res[root][c]['rho_ungated']:+.2f}" for c in CELLS))
    fam = family_max(SS, masks); fp95 = float(np.quantile(fam, .95)); fp50 = float(np.median(fam)); zs = {(r, c): res[r][c]["z"] for r in ROOTS for c in CELLS}; obs_k = max(zs, key=lambda k: zs[k] if np.isfinite(zs[k]) else -9); obs = zs[obs_k]
    print(f"\n  FAMILY MAX of the difference z (8 cell-roots, {fam.size} offsets): p50 {fp50:+.2f}  p95 {fp95:+.2f}  p99 {np.quantile(fam, .99):+.2f}   observed max {obs:+.2f} ({obs_k[0]} {obs_k[1]})   share of offsets >= observed {100*(fam >= obs).mean():.1f}%")
    verdict = {}
    for r in ROOTS:
        for c in CELLS:
            k = res[r][c]
            if c == "K8":
                ok = k["net_sharpe"] > 0.5 and k["C_c"] and k["C_d"]; verdict[f"{r} K8"] = "PROVISIONAL entry" if (ok and r == "NQ") else ("C-a cleared (check root)" if ok else "below C-a: recorded, not entered")
            else:
                proceed = k["clears_N1"] and k["z"] > fp95 and k["net_sharpe"] > 0.3; pick = k["clears_N1"] and k["net_sharpe"] > 0.3 and not proceed; verdict[f"{r} {c}"] = "PROCEED" if proceed else ("PICK" if pick else "closed")
    print("  VERDICTS: " + "; ".join(f"{k}: {v}" for k, v in verdict.items()))
    N = res["NQ"]; E = res["ES"]; print("\nPREDICTIONS")
    print(f"  X-a K8 NQ 45-50% of sessions, +9..+12 bp, hit 55-58%, net Sharpe +0.40..+0.60, >= 6/8 years, both subs; ES +4..+6 bp, +0.15..+0.35; rho(K8, ungated) 0.6-0.7 : NQ {100*N['K8']['share']:.0f}%, {N['K8']['bp_mean']:+.1f} bp, hit {100*N['K8']['hit']:.0f}%, Sharpe {N['K8']['net_sharpe']:+.2f} ({N['K8']['net_sharpe_se']:.2f}), years>0 {sum(v > 0 for v in N['K8']['by_year_bp'].values())}/8, subs {N['K8']['sub']['2016-2020']['bp']:+.1f}/{N['K8']['sub']['2021-2023']['bp']:+.1f}; ES {E['K8']['bp_mean']:+.1f} bp, {E['K8']['net_sharpe']:+.2f}; rho {N['K8']['rho_ungated']:+.2f}")
    print(f"  X-b E1 TOM NQ +8..+15 bp on ~48/yr, above N1, z 1.5-2.5, Sharpe +0.3..+0.5                                                        : {N['E1']['bp_mean']:+.1f} bp on {N['E1']['trades']/8:.0f}/yr, N1 {'cleared' if N['E1']['clears_N1'] else 'no'}, z {N['E1']['z']:+.2f} (family p95 {fp95:+.2f}), Sharpe {N['E1']['net_sharpe']:+.2f}; ES {E['E1']['bp_mean']:+.1f}")
    print(f"  X-c E2 FOMC to 14:00 +8..+20 bp on ~64 days, SE ~15, inside or marginal                                                          : NQ {N['E2']['bp_mean']:+.1f} ({N['E2']['bp_se']:.1f}) on {N['E2']['trades']}, N1 {'cleared' if N['E2']['clears_N1'] else 'no'}, z {N['E2']['z']:+.2f}; ES {E['E2']['bp_mean']:+.1f} ({E['E2']['bp_se']:.1f})")
    print(f"  X-d E3 fade +3..+6 bp, 2020-2022-driven, negative 2016-2017, clears N1 pooled, Sharpe +0.1..+0.4, not the family                    : NQ {N['E3']['bp_mean']:+.1f} bp, N1 {'cleared' if N['E3']['clears_N1'] else 'no'}, Sharpe {N['E3']['net_sharpe']:+.2f}, 2016/2017 {N['E3']['by_year_bp'].get('2016', float('nan')):+.0f}/{N['E3']['by_year_bp'].get('2017', float('nan')):+.0f}; ES {E['E3']['bp_mean']:+.1f}, {E['E3']['net_sharpe']:+.2f}, z {E['E3']['z']:+.2f}")
    print(f"  X-e rho(E1,K8), rho(E2,K8), rho(E3,K8) < 0.3; rho(E3, ungated) < 0.2                                                                : NQ {N['E1']['rho_K8']:+.2f} {N['E2']['rho_K8']:+.2f} {N['E3']['rho_K8']:+.2f}; E3/ungated {N['E3']['rho_ungated']:+.2f}")
    OUT.write_text(json.dumps(dict(spec="D498", results=res, family=dict(p50=fp50, p95=fp95, observed=obs, observed_cell=list(obs_k)), verdicts=verdict), indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min")


def forward(word):
    if not word:
        print("REFUSED: --forward reads the reserved 2024+ day-session slice for K8; re-run with --principals-word only on the principal's word."); return 2
    t0 = time.time(); print(f"D498 K8 -- FORWARD READ on the principal's word, {FWD_LO}..{FWD_HI}; rule: FULL if gross > 0, net Sharpe > 0, z(diff vs after-up days) >= 1; REMOVED if net Sharpe < -0.3 or diff < 0; else PROVISIONAL"); res = {}
    for root in ROOTS:
        d = D90.load_root(root, FWD_LO, FWD_HI); S = states(d); mask = d["trade"]; cal = pd.Index(d["days"][mask]); tr = trades(d, "K8", S["dirs"]["K8"], MULT[root], mask); z, x, y = cell_z(S, "K8", mask); n1 = rotation_null(S, "K8", mask)
        c = summarise(tr, cal, x, y, z, n1, f"{root} K8 forward"); c.pop("_ser"); res[root] = c; tr.to_csv(REPO / "data" / f"d498_trades_forward_{root}_K8.csv.gz", index=False, compression="gzip")
    k = res["NQ"]; v = "REMOVED" if (k["net_sharpe"] < -0.3 or k["gross_mean"] - COST < -1e9 or (k["bp_mean"] - k["other_bp"]) < 0) else ("FULL" if (k["gross_mean"] > 0 and k["net_sharpe"] > 0 and k["z"] >= 1) else "PROVISIONAL")
    print(f"\nVERDICT for K8 (NQ): {v}   (gross ${k['gross_mean']:+.2f}, net Sharpe {k['net_sharpe']:+.2f}, diff vs after-up days {k['bp_mean'] - k['other_bp']:+.1f} bp, z {k['z']:+.2f})")
    OUT_FWD.write_text(json.dumps(dict(spec="D498", forward=res, verdict=v), indent=1, default=float)); print(f"wrote {OUT_FWD.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min"); return 0


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    t0 = time.time(); print("== (a) turn-of-month days: the last session of a month and the first three of the next, on a synthetic calendar")
    days = np.array([f"2019-01-{d:02d}" for d in (28, 29, 30, 31)] + [f"2019-02-{d:02d}" for d in (1, 4, 5, 6, 7)] + [f"2019-02-{d:02d}" for d in (26, 27, 28)] + ["2019-03-01"]); m = tom_mask(days)
    assert m.tolist() == [False, False, False, True, True, True, True, False, False, False, False, True, True], m.tolist(); print("  ok")
    print("== (b) the FOMC list: 8 decision days a year except 7 in 2020, every one a weekday")
    yrs = pd.Series([f[:4] for f in FOMC]).value_counts().to_dict(); assert all(v == 8 for y, v in yrs.items() if y != "2020") and yrs["2020"] == 7 and all(pd.Timestamp(f).dayofweek < 5 for f in FOMC); print(f"  ok: {len(FOMC)} days, {sorted(yrs)[0]}..{sorted(yrs)[-1]}")
    print("== (c) E3 on a synthetic day: the first 30 minutes rise -> short at 15:30 - tick, pnl = entry - close; K8 uses yesterday's day-session sign; E2 window ends at the 13:59 close")
    n = NBAR; up = np.concatenate([np.linspace(100, 102, 30), np.full(330, 102.0), np.linspace(102, 101, 30)]); dn = np.linspace(100, 98, n); d = D90.make_d([dn, up], [np.full(n, 1.0)] * 2, None); d["days"] = np.array(["2019-03-06", "2019-03-07"]); S = states(d)
    assert S["dirs"]["E3"][1] == -1.0 and S["dirs"]["K8"][1] == 1.0 and S["dirs"]["K8"][0] == 0.0 and S["dirs"]["E2"][0] == 0.0
    t3 = trades(d, "E3", S["dirs"]["E3"], 5.0, np.array([False, True])); assert abs(t3["pnl_pts"].iat[0] - ((d["O"][1, B_1530] - TICK) - d["C"][1, B_LAST])) < 1e-9 and t3["pnl_pts"].iat[0] > 0
    t2 = trades(d, "E2", np.array([0.0, 1.0]), 5.0, np.array([False, True])); assert abs(t2["exit"].iat[0] - d["C"][1, B_1359]) < 1e-9; print(f"  ok: E3 short pnl {t3['pnl_pts'].iat[0]:+.2f} pts; K8 fires after the down day; E2 exits at the 14:00 print")
    print("== (d) a planted K8 effect clears its rotation null and the difference z; the other side partitions the calendar")
    rng = np.random.default_rng(1); R = rng.normal(0, 60, 1500); Sx = dict(R=R, w={"K8": R}, dirs={"K8": np.zeros(1500)}, other={"K8": np.zeros(1500, bool)}); Sx["dirs"]["K8"][1:] = (R[:-1] < 0).astype(float); Sx["other"]["K8"][1:] = R[:-1] > 0
    R[Sx["dirs"]["K8"] > 0] += 25.0; z, x, y = cell_z(Sx, "K8", np.ones(1500, bool)); n1 = rotation_null(Sx, "K8", np.ones(1500, bool)); assert x.mean() > np.quantile(n1, .99) and z > 4 and x.size + y.size <= 1500; print(f"  ok: planted {x.mean():+.1f} bp vs N1 p99 {np.quantile(n1, .99):+.1f}; z {z:+.2f}")
    print("== (e) the forward guard refuses without the flag")
    assert forward(False) == 2; print("  ok")
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--run", action="store_true"); g.add_argument("--forward", action="store_true"); g.add_argument("--selftest", action="store_true"); ap.add_argument("--principals-word", action="store_true"); a = ap.parse_args()
    if a.selftest:
        cmd_selftest()
    elif a.run:
        run()
    else:
        sys.exit(forward(a.principals_word))
