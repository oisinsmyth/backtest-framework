"""D692 DIAG -- where the oracle's winners sit, at MES (the principal: "Yes, run the oracle profile at MES"). Hindsight and
descriptive only: nothing is fitted, filtered or traded. It is the evidence the principal and I design the candidate
filters from (the principal's ruling on D690: score at MES, show the oracle first, design the filters together).

    uv run python scripts/diag_d692_oracle_profile_mes.py --run --data-root "<main checkout>/data"

THE CANDIDATES (D690's, unchanged). D688's panel, 2016-01-05 -> 2023-12-29. At t = 10:30, 11:30, 12:30, 13:30 and
14:30 on every session, with m = the last 60 minutes' move (m != 0), hold sign(m) for 60 minutes. Priced at 1 MES:
gross = sign(m) x (P(t+60) - P(t)) x $5, net = gross - $4.42. ALL candidates are profiled (no burn-in: nothing is
fitted); D690's post-burn-in totals are reproduced alongside, as a check.

THE ORACLE LABELS: WIN = net > 0; BAR = gross >= 2 x $4.42 = $8.84 (the expected-profit template's bar).

DECLARED PROFILE (for every bucket): candidates, share of all, trades a year; the WIN rate and the BAR rate, and each
one's lift over the overall rate; the mean gross and mean net per trade, with the gross mean's day-clustered t; the
share of all oracle-winner net P&L the bucket holds; and the mean net of its winners and of its losers. Buckets:
  1  gamma regime: G_SUM < 0 / >= 0; SPX GEX < 0 / >= 0; ES book < 0 / >= 0; the four SPX x ES sign cells
  2  G_SUM quintile
  3  side: long (m > 0) / short (m < 0)
  4  gamma regime (G_SUM) x side
  5  time of day: the five decision times
  6  |m| / sigma_h tercile (sigma_h = sigma_d sqrt(60/390), the last hour's move against a normal hour)
  7  today's realised volatility up to t, tercile; trailing sigma_d, tercile
  8  alignment: the last hour in the same direction as the day's move so far (prior settlement -> t), or against it
  9  year
 10  two-way: gamma regime x |m| tercile; gamma regime x today's-volatility tercile; gamma regime x time of day
Tercile and quintile edges are taken over all candidates (hindsight is allowed here; a filter would need prior-only
edges). The report counts its buckets, so nobody reads a best bucket without its multiplicity.

Reads nothing dated 2024-01-01 or later. Output data/d692_oracle_profile_mes.json: statistics only, no per-date GEX
(SqueezeMetrics, under the permission of 2026-09-28).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage0_d688_gamma_close as S  # noqa: E402  (importing defines, never runs)

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d692_oracle_profile_mes.json"
D688_JSON = REPO / "data" / "d688_gamma_close.json"
D690_JSON = REPO / "data" / "d690_oracle_filter.json"
H = 60
BURN = 250
SLOTS = ("10:30", "11:30", "12:30", "13:30", "14:30")


def P(*a, **k):
    print(*a, **k, flush=True)


def build(data_root: Path, log=P):
    """D690's candidates, rebuilt with D688's functions (D688's beta_G reproduced first)."""
    t0 = time.time()
    m581 = S.d581(data_root / "fixtures")
    I = S.load_inputs(data_root, log)
    es581 = m581.load_es(lambda *a: None)
    strip_es = I["strip"]
    refs = np.array(sorted(strip_es["ref"].unique()))
    win = [d for d in I["days"] if d >= S.IN_FROM]
    strides = [win[i::S.N_WORKERS] for i in range(S.N_WORKERS)]
    with ProcessPoolExecutor(max_workers=S.N_WORKERS, initializer=S._init, initargs=(str(I["fx"]), es581, strip_es, I["cal"], I["tcal"], refs)) as ex:
        futs = [ex.submit(S._work, (s, [])) for s in strides]
        Dfull = S.build_panel(I, log)
        outs = [f.result() for f in futs]
    prior = pd.concat([o["prior"] for o in outs]).sort_index()
    D = Dfull.join(prior[["G_ES"]], how="left")
    D = D[D.index >= S.IN_FROM]
    D["G_SUM"] = D["G_SPX"] + D["G_ES"]
    need = ["P1530", "P1600", "P1100", "P1130", "P1550", "S_prev", "sig", "V", "G_SPX", "G_ES", "A_L"] + ["P" + t.replace(":", "") for t in S.CLOCK]
    D = D[np.isfinite(D[need].to_numpy(float)).all(1)]
    S.guard_window(D.index, "D692 panel")
    days = D.index.to_numpy().astype(str)
    nd = len(days)
    sig = D["sig"].to_numpy(float); Sp = D["S_prev"].to_numpy(float)
    r = 100 * np.log(D["P1530"].to_numpy(float) / Sp); R2 = 1e4 * np.log(D["P1600"].to_numpy(float) / D["P1530"].to_numpy(float))
    f688, _ = S.gamma_regression(R2, D["G_SUM"].to_numpy(float), r, sig, D["V"].to_numpy(float), D["A_L"].to_numpy(float), null=False)
    ref = json.loads(D688_JSON.read_text(encoding="utf-8"))["gate1"]["G1"]["beta_G"]
    if f688["beta_G"] != ref:
        raise S.GateError(f"[REPRO] beta_G {f688['beta_G']!r} vs D688's {ref!r}")
    log(f"  D688 REPRODUCED on {nd} sessions ({time.time() - t0:.0f} s)")
    b = I["bars"]
    b = b[b["day"].isin(set(days))]
    close = b.pivot(index="day", columns="hhmm", values="close").reindex(days)
    op = b[b["hhmm"] == "09:30"].set_index("day")["open"].reindex(days).to_numpy(float)
    grid = [(pd.Timestamp("2000-01-01 09:30") + pd.Timedelta(minutes=5 * k)) for k in range(79)]
    PG = np.column_stack([op] + [close[(g - pd.Timedelta(minutes=1)).strftime("%H:%M")].to_numpy(float) for g in grid[1:]])
    L = np.log(PG)
    r5 = 1e4 * np.diff(L, axis=1)
    cum_rv = np.concatenate([np.full((nd, 1), np.nan), np.cumsum(r5 * r5, axis=1)], axis=1)
    step = H // 5
    js = [j for j in range(step, 79) if j % step == 0 and j + step <= 78]
    rows = []
    for slot, j in enumerate(js):
        with np.errstate(divide="ignore", invalid="ignore"):
            lrv = np.log(cum_rv[:, j] / j)
        rows.append(pd.DataFrame({"di": np.arange(nd), "slot": slot, "m": 1e4 * (L[:, j] - L[:, j - step]), "dp": PG[:, j + step] - PG[:, j],
                                  "lrv": lrv, "rt": 100 * np.log(PG[:, j] / Sp)}))
    T = pd.concat(rows, ignore_index=True)
    T = T[np.isfinite(T[["m", "dp", "lrv", "rt"]].to_numpy()).all(1) & (T["m"] != 0)].sort_values(["di", "slot"], kind="stable").reset_index(drop=True)
    T["day"] = days[T["di"].to_numpy()]
    T["G_SUM"] = D["G_SUM"].to_numpy(float)[T["di"].to_numpy()]
    T["G_SPX"] = D["G_SPX"].to_numpy(float)[T["di"].to_numpy()]
    T["G_ES"] = D["G_ES"].to_numpy(float)[T["di"].to_numpy()]
    T["sig"] = sig[T["di"].to_numpy()]
    return T, nd


def run(data_root: Path, log=P) -> int:
    t0 = time.time()
    T, nd = build(data_root, log)
    if not T["slot"].isin(range(len(SLOTS))).all():
        raise S.GateError("[SLOTS] a decision time outside 10:30 .. 14:30")
    E = S.d685()
    mes = E.cost_spec("ES", "micro")
    cost = mes["cost_rt_usd"]
    side = np.sign(T["m"].to_numpy())
    gross = side * T["dp"].to_numpy() * mes["usd_per_point"]
    net = gross - cost
    win = net > 0
    bar = gross >= 2 * cost
    di = T["di"].to_numpy()
    yrs = nd / 252.0
    n_all = len(T)
    win_rate, bar_rate = float(win.mean()), float(bar.mean())
    oracle_net_total = float(net[win].sum())
    # the check against D690 (its post-burn-in MES oracle)
    ev = di >= BURN
    d690 = json.loads(D690_JSON.read_text(encoding="utf-8"))["A_oracles"]["mes"]
    chk = {"take_all_mean_net": float(net[ev].mean()), "d690_take_all_mean_net": d690["take_all"]["mean_net"],
           "oracle_mean_net": float(net[ev & win].mean()), "d690_oracle_mean_net": d690["oracle_net_positive"]["mean_net"]}
    if not (abs(chk["take_all_mean_net"] - chk["d690_take_all_mean_net"]) < 1e-9 and abs(chk["oracle_mean_net"] - chk["d690_oracle_mean_net"]) < 1e-9):
        raise S.GateError(f"[REPRO] the candidates are not D690's: {chk}")
    log(f"  D690's MES oracle REPRODUCED (post-burn-in take-all ${chk['take_all_mean_net']:+.2f}, oracle ${chk['oracle_mean_net']:+.2f})")
    log(f"  ALL {n_all} candidates ({n_all / yrs:.0f} a year): WIN (net > 0) {win_rate:.3f}, BAR (gross >= ${2 * cost:.2f}) {bar_rate:.3f}; "
        f"mean gross ${gross.mean():+.2f}, net ${net.mean():+.2f}; winners' mean net ${net[win].mean():+.2f}, losers' ${net[~win].mean():+.2f}")

    def cell(mask):
        n = int(mask.sum())
        if n == 0:
            return {"n": 0}
        out = {"n": n, "share": n / n_all, "per_year": n / yrs, "win_rate": float(win[mask].mean()), "win_lift": float(win[mask].mean() / win_rate),
               "bar_rate": float(bar[mask].mean()), "bar_lift": float(bar[mask].mean() / bar_rate),
               "mean_gross": float(gross[mask].mean()), "mean_net": float(net[mask].mean()),
               "share_of_oracle_net": float(net[mask & win].sum() / oracle_net_total),
               "winners_mean_net": float(net[mask & win].mean()) if (mask & win).any() else None,
               "losers_mean_net": float(net[mask & ~win].mean()) if (mask & ~win).any() else None}
        if n >= 30:
            rr = sm.OLS(gross[mask], np.ones((n, 1))).fit(cov_type="cluster", cov_kwds={"groups": di[mask]})
            out["t_gross"] = float(rr.tvalues[0])
        return out

    def terc(x):
        e = np.quantile(x, [1 / 3, 2 / 3])
        return np.digitize(x, e), [float(v) for v in e]

    G, GS, GE = T["G_SUM"].to_numpy(), T["G_SPX"].to_numpy(), T["G_ES"].to_numpy()
    sh = G < 0
    sg_h = T["sig"].to_numpy() * math.sqrt(H / 390.0)
    mt, m_edges = terc(np.abs(T["m"].to_numpy()) / sg_h)
    vt, v_edges = terc(T["lrv"].to_numpy())
    st, s_edges = terc(T["sig"].to_numpy())
    q5 = np.digitize(G, np.quantile(G, [0.2, 0.4, 0.6, 0.8]))
    slot = T["slot"].to_numpy()
    align = np.sign(T["rt"].to_numpy()) == side
    yr = T["day"].str[:4].to_numpy()
    reg = {True: "short_gamma", False: "long_gamma"}
    prof = {
        "1_gamma_regime": {"G_SUM<0": cell(sh), "G_SUM>=0": cell(~sh), "SPX<0": cell(GS < 0), "SPX>=0": cell(GS >= 0), "ES<0": cell(GE < 0), "ES>=0": cell(GE >= 0),
                           "SPX<0,ES<0": cell((GS < 0) & (GE < 0)), "SPX<0,ES>=0": cell((GS < 0) & (GE >= 0)), "SPX>=0,ES<0": cell((GS >= 0) & (GE < 0)), "SPX>=0,ES>=0": cell((GS >= 0) & (GE >= 0))},
        "2_G_SUM_quintile_0_most_short": {str(q): cell(q5 == q) for q in range(5)},
        "3_side": {"long": cell(side > 0), "short": cell(side < 0)},
        "4_regime_x_side": {f"{reg[s]}_{sd}": cell((sh == s) & ((side > 0) == (sd == "long"))) for s in (True, False) for sd in ("long", "short")},
        "5_time_of_day": {SLOTS[k]: cell(slot == k) for k in range(len(SLOTS))},
        "6_abs_m_over_sigma_h_tercile": {str(k): cell(mt == k) for k in range(3)},
        "7a_today_realised_vol_tercile": {str(k): cell(vt == k) for k in range(3)},
        "7b_trailing_sigma_tercile": {str(k): cell(st == k) for k in range(3)},
        "8_alignment_with_the_days_move": {"with": cell(align), "against": cell(~align)},
        "9_year": {y: cell(yr == y) for y in sorted(set(yr))},
        "10a_regime_x_abs_m_tercile": {f"{reg[s]}_{k}": cell((sh == s) & (mt == k)) for s in (True, False) for k in range(3)},
        "10b_regime_x_today_vol_tercile": {f"{reg[s]}_{k}": cell((sh == s) & (vt == k)) for s in (True, False) for k in range(3)},
        "10c_regime_x_time": {f"{reg[s]}_{SLOTS[k]}": cell((sh == s) & (slot == k)) for s in (True, False) for k in range(len(SLOTS))},
    }
    n_buckets = sum(len(v) for v in prof.values())
    res = {"spec": "D692 DIAG (hindsight, descriptive; the MES oracle's profile)", "cost_rt_usd": cost, "bar_usd": 2 * cost,
           "all": cell(np.ones(n_all, bool)) | {"oracle_net_total": oracle_net_total}, "check_against_d690": chk,
           "edges": {"abs_m_over_sigma_h": m_edges, "log_today_rv": v_edges, "trailing_sigma_bp": s_edges},
           "profile": prof, "n_buckets": n_buckets, "timing_s": None}
    for k, v in prof.items():
        log(f"  {k}:")
        for b_, c in v.items():
            if c["n"]:
                log(f"     {b_:<22} n {c['n']:>5} ({c['per_year']:>5.0f}/yr)  WIN {c['win_rate']:.3f} (x{c['win_lift']:.2f})  BAR {c['bar_rate']:.3f} (x{c['bar_lift']:.2f})  "
                    f"gross {c['mean_gross']:+6.2f} (t {c.get('t_gross', float('nan')):+.2f})  net {c['mean_net']:+6.2f}  oracle share {c['share_of_oracle_net']:.3f}")
    log(f"  {n_buckets} buckets in all")
    res["timing_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8")
    log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']} s")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    sys.exit(run(a.data_root) if a.run else 1)
