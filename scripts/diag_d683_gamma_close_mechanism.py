"""D683 DIAG -- why did D681's dealer-gamma close fail? Post hoc, on D681's own in-sample (2016-01-05 -> 2023-12-29), no
verdict (the principal: "Do a full diagnostic, why did the mechanism fail? Did it not have enough impact?").

    uv run python scripts/diag_d683_gamma_close_mechanism.py --run --data-root "<main checkout>/data"

It rebuilds D681's panel with D681's own functions and reproduces its beta_G (+0.12248...) exactly before anything else.
Then it reads seven candidate explanations, each with the fingerprint that would support it, DECLARED HERE BEFORE THE
RUN:

A  TOO LITTLE IMPACT (underpowered). The square-root push is small against the half-hour's noise, so even the law's size
   could not show. Fingerprint: the t this sample would give at Y = 0.5 (from the actual Z, after the controls, against
   D681's residual) is below 2. If it is well above 2, the impact is missing rather than unmeasurable. Also reported:
   the hedge flow |Q| against ES's daily and closing-half-hour dollar volume, and sign(Z)*R2 against |Z| by decile.
B  CONTINUOUS HEDGING (the flow lands along the path, not at the close). Fingerprint: the first-order autocorrelation of
   the day's 5-minute returns (09:30 -> 15:30) is lower on long-gamma days and higher on short-gamma days (slope on the
   regime sign < 0), above the p95 of the enumerated day-rotation null; the day's realised variance falls with gamma.
C  THE WRONG MOVE TO HEDGE. Dealers rehedge through the day, so the imbalance at 15:30 is the RECENT move, not the move
   since the prior settlement. Fingerprint: Z built on a shorter lookback (since 09:30 / 12:00 / 14:30 / 15:00 / 15:15)
   predicts R2 better than D681's.
D  ANTICIPATED OR TEMPORARY. Fingerprint: the push shows up before 15:30 (14:30 -> 15:30 on Z built at 14:30), or the
   close's move reverses overnight (next 09:30 open against the 16:00 close) or in the next session's first half-hour.
E  A NOISY MEASURE (the ES book's convention). The ES book is short gamma on 43 % of days against SPX's 12.5 %.
   Fingerprint: the ES book's sign does not order realised variance or 5-minute autocorrelation while SPX's does, and
   the close slope differs on the days where the two books disagree.
F  THE CONTROLS ABSORB IT. r, Z_L and Z are all functions of the day's move. Fingerprint: beta_G rises materially with
   no controls, or with Z_L removed; the share of Z's variance left after the controls is small.
G  CONCENTRATION. Fingerprint: beta_G moves by more than one SE without 2020, without the top 1 % of |R2|, or across
   |Z| terciles.

Reads nothing dated 2024-01-01 or later (D681's loaders and guards). Output data/d683_gamma_close_diag.json: statistics
only, no per-date GEX (SqueezeMetrics, under the permission of 2026-09-28).
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage0_d681_gamma_close as S  # noqa: E402  (D681's committed runner; importing it defines, never runs)

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d683_gamma_close_diag.json"
D681_JSON = REPO / "data" / "d681_gamma_close.json"
LOOKBACKS = ["prior_settle", "09:30", "12:00", "14:30", "15:00", "15:15"]


def P(*a, **k):
    print(*a, **k, flush=True)


def slope_with_null(y, x, C):
    """Slope of y on x with controls C (NW t), and the enumerated rotation null of x (k = 10 .. n-10)."""
    r = S.nw_fit(y, [x] + list(C))
    ks = S.rot_ks(len(y))
    b = S.fwl_betas(y, S.rotate(x, ks), C)
    if not abs(b[0] - r.params[1]) <= 1e-9 * max(1.0, abs(r.params[1])):
        raise S.GateError("[ROTATION] batched k = 0 slope is not the regression's")
    return {"beta": float(r.params[1]), "t": float(r.tvalues[1]), "n": int(len(y)), "rotation": S.blk(b[0], b[1:])}


def run(data_root: Path, log=P) -> int:
    t0 = time.time()
    m = S.d581(data_root / "fixtures")
    I = S.load_inputs(data_root, log)
    es581 = m.load_es(lambda *a: None)
    strip_es = I["strip"]
    refs = np.array(sorted(strip_es["ref"].unique()))
    win = [d for d in I["days"] if d >= S.IN_FROM]
    strides = [win[i::S.N_WORKERS] for i in range(S.N_WORKERS)]
    with ProcessPoolExecutor(max_workers=S.N_WORKERS, initializer=S._init, initargs=(str(I["fx"]), es581, strip_es, I["cal"], I["tcal"], refs)) as ex:
        futs = [ex.submit(S._work, (s, [])) for s in strides]
        Dfull = S.build_panel(I, log)
        outs = [f.result() for f in futs]
    prior = pd.concat([o["prior"] for o in outs]).sort_index()
    log(f"  ES book rebuilt in {time.time() - t0:.0f} s")

    # ---- extra prices from the bars: 5-minute grid, 15:15, the closing half-hour's dollar volume ----
    b = I["bars"]
    b = b[b["day"].isin(set(I["days"]))]
    close = b.pivot(index="day", columns="hhmm", values="close").reindex(I["days"])
    op = b[b["hhmm"] == "09:30"].set_index("day")["open"].reindex(I["days"])
    grid = ["09:30"] + [(pd.Timestamp("2000-01-01 09:30") + pd.Timedelta(minutes=5 * k)).strftime("%H:%M") for k in range(1, 79)]

    def price(hhmm):
        if hhmm == "09:30":
            return op.to_numpy(float)
        lab = (pd.Timestamp("2000-01-01 " + hhmm) - pd.Timedelta(minutes=1)).strftime("%H:%M")
        return close[lab].to_numpy(float)

    G5 = np.column_stack([price(t) for t in grid])                       # 79 prices, 09:30 .. 16:00
    r5 = 1e4 * np.diff(np.log(G5), axis=1)                                # 78 five-minute returns, bp
    pre = r5[:, :72]                                                      # 09:30 -> 15:30
    rho1 = (pre[:, 1:] * pre[:, :-1]).sum(1) / (pre * pre).sum(1)
    rv = (r5 * r5).sum(1)
    cl = b[b["hhmm"] >= "15:30"]
    dv30 = (cl["volume"] * cl["close"] * S.MULT).groupby(cl["day"]).sum().reindex(I["days"])
    V30 = dv30.rolling(S.TRAIL).median().shift(1).to_numpy()
    X = pd.DataFrame({"rho1": rho1, "rv": rv, "V30": V30, "P1515": price("15:15")}, index=pd.Index(I["days"], name="day"))
    nxt = pd.Series(I["days"]).shift(-1).to_numpy()
    X["P0930_next"] = Dfull["P0930"].reindex(nxt).to_numpy()
    X["P1000_next"] = Dfull["P1000"].reindex(nxt).to_numpy()
    X["same_contract_next"] = (Dfull["contract"].reindex(nxt).to_numpy() == Dfull["contract"].to_numpy())

    # ---- D681's panel, exactly as the runner filters it ----
    D = Dfull.join(prior[["G_ES"]], how="left")
    D = D[D.index >= S.IN_FROM]
    D["G_SUM"] = D["G_SPX"] + D["G_ES"]
    need = ["P1530", "P1600", "P1100", "P1130", "P1550", "S_prev", "sig", "V", "G_SPX", "G_ES", "A_L"] + ["P" + t.replace(":", "") for t in S.CLOCK]
    D = D[np.isfinite(D[need].to_numpy(float)).all(1)].join(X, how="left")
    S.guard_window(D.index, "diag panel")
    n = len(D)
    days = D.index.to_numpy().astype(str)

    def pr(col):
        return D[col].to_numpy(float)

    Sp = pr("S_prev"); sig = pr("sig"); V = pr("V"); A_L = pr("A_L")
    G = pr("G_SUM"); GS = pr("G_SPX"); GE = pr("G_ES")
    r = 100 * np.log(pr("P1530") / Sp); R2 = 1e4 * np.log(pr("P1600") / pr("P1530"))
    f681, _ = S.gamma_regression(R2, G, r, sig, V, A_L, null=False)
    ref = json.loads(D681_JSON.read_text(encoding="utf-8"))["gate1"]["G1"]["beta_G"]
    if f681["beta_G"] != ref:
        raise S.GateError(f"[REPRO] beta_G {f681['beta_G']!r} vs D681's {ref!r}")
    log(f"  D681 REPRODUCED: beta_G {f681['beta_G']!r} (t {f681['t_G']:+.2f}), n {n}")
    Z = S.zpush(G, r, sig, V); ZL = S.zletf(A_L, r, sig, V)
    C = [r, ZL, sig]
    res = {"spec": "D683 DIAG of D681 (post hoc, in-sample, no verdict)", "reproduction": {"beta_G": f681["beta_G"], "t_G": f681["t_G"], "n": n, "exact": True}}

    # ---- A: too little impact? ----
    Xc = np.column_stack([np.ones(n)] + C)
    Qx, _ = np.linalg.qr(Xc)
    zt = Z - Qx @ (Qx.T @ Z)
    fit = S.nw_fit(R2, [Z] + C)
    resid_sd = float(np.sqrt(np.sum(fit.resid ** 2) / (n - 5)))
    znorm = float(np.sqrt(np.sum(zt * zt)))
    implied = {f"Y_{y}": float(y * znorm / resid_sd) for y in (1.0, 0.5, 0.25, 0.12)}
    Qd = np.abs(G * r)
    dec = np.digitize(np.abs(Z), np.quantile(np.abs(Z), np.linspace(0.1, 0.9, 9)))
    sR = np.sign(Z) * R2
    calib = {int(k): {"n": int((dec == k).sum()), "mean_absZ_bp": float(np.abs(Z)[dec == k].mean()), "mean_signZ_R2_bp": float(sR[dec == k].mean()),
                      "se_bp": float(sR[dec == k].std(ddof=1) / math.sqrt((dec == k).sum())), "pass_through": float(sR[dec == k].mean() / np.abs(Z)[dec == k].mean())} for k in range(10)}
    res["A_impact"] = {
        "share_of_Z_variance_left_after_controls": float(np.sum(zt * zt) / np.sum((Z - Z.mean()) ** 2)),
        "residual_sd_bp": resid_sd, "Z_sd_bp": float(Z.std(ddof=1)), "R2_sd_bp": float(R2.std(ddof=1)),
        "implied_ols_t_at_Y": implied, "Y_needed_for_t2": float(2 * resid_sd / znorm), "observed_ols_t": float(f681["beta_G"] * znorm / resid_sd),
        "absQ_usd_bn_quantiles": {q: float(np.quantile(Qd, float(q)) / 1e9) for q in ("0.5", "0.9", "0.99")},
        "absQ_share_of_daily_es_dollar_volume_pct": {q: float(np.quantile(Qd / V, float(q)) * 100) for q in ("0.5", "0.9", "0.99")},
        "absQ_share_of_closing_half_hour_es_dollar_volume_pct": {q: float(np.nanquantile(Qd / pr("V30"), float(q)) * 100) for q in ("0.5", "0.9", "0.99")},
        "closing_half_hour_share_of_daily_volume_median": float(np.nanmedian(pr("V30") / V)),
        "calibration_by_absZ_decile": calib}
    log(f"  A: implied OLS t at Y = 1 / 0.5 / 0.25: {implied['Y_1.0']:.2f} / {implied['Y_0.5']:.2f} / {implied['Y_0.25']:.2f}; Y for t 2 = {res['A_impact']['Y_needed_for_t2']:.3f}; "
        f"observed OLS t {res['A_impact']['observed_ols_t']:.2f}; Z variance left after controls {res['A_impact']['share_of_Z_variance_left_after_controls']:.2f}")
    log(f"     |Q| median ${res['A_impact']['absQ_usd_bn_quantiles']['0.5']:.2f}bn = {res['A_impact']['absQ_share_of_daily_es_dollar_volume_pct']['0.5']:.2f}% of ES daily $ volume, "
        f"{res['A_impact']['absQ_share_of_closing_half_hour_es_dollar_volume_pct']['0.5']:.1f}% of the closing half-hour's (p90 {res['A_impact']['absQ_share_of_closing_half_hour_es_dollar_volume_pct']['0.9']:.1f}%)")
    log("     calibration pass-through by |Z| decile: " + " ".join(f"{k}:{v['mean_absZ_bp']:.0f}bp->{v['mean_signZ_R2_bp']:+.1f}" for k, v in calib.items()))

    # ---- B: continuous hedging along the path ----
    lsig2 = np.log(sig ** 2)
    rho = pr("rho1"); lrv = np.log(pr("rv"))
    sgn = np.where(G < 0, 1.0, 0.0)                                     # 1 = short gamma
    B = {"rho1_mean_short": float(rho[sgn == 1].mean()), "rho1_mean_long": float(rho[sgn == 0].mean()),
         "rho1_on_short_gamma_dummy": slope_with_null(rho, sgn, [sig]),
         "rho1_on_G_SUM_usd_bn": slope_with_null(rho, G / 1e9, [sig]),
         "log_rv_on_short_gamma_dummy": slope_with_null(lrv, sgn, [lsig2]),
         "log_rv_on_G_SUM_usd_bn": slope_with_null(lrv, G / 1e9, [lsig2])}
    q5 = np.digitize(G, np.quantile(G, [0.2, 0.4, 0.6, 0.8]))
    B["by_G_SUM_quintile"] = {int(k): {"rho1": float(rho[q5 == k].mean()), "rv_median_bp2": float(np.median(pr("rv")[q5 == k])), "sig_median": float(np.median(sig[q5 == k]))} for k in range(5)}
    res["B_continuous_hedging"] = B
    log(f"  B: 5-min rho1 short {B['rho1_mean_short']:+.4f} long {B['rho1_mean_long']:+.4f}; rho1 on short dummy {B['rho1_on_short_gamma_dummy']['beta']:+.4f} "
        f"(t {B['rho1_on_short_gamma_dummy']['t']:+.2f}, pct {B['rho1_on_short_gamma_dummy']['rotation']['pct_rank']:.3f}); on G $bn {B['rho1_on_G_SUM_usd_bn']['beta']:+.5f} "
        f"(t {B['rho1_on_G_SUM_usd_bn']['t']:+.2f}, pct {B['rho1_on_G_SUM_usd_bn']['rotation']['pct_rank']:.3f})")
    log(f"     log RV on short dummy {B['log_rv_on_short_gamma_dummy']['beta']:+.3f} (t {B['log_rv_on_short_gamma_dummy']['t']:+.2f}, pct {B['log_rv_on_short_gamma_dummy']['rotation']['pct_rank']:.3f}); "
        f"on G $bn {B['log_rv_on_G_SUM_usd_bn']['beta']:+.4f} (t {B['log_rv_on_G_SUM_usd_bn']['t']:+.2f}, pct {B['log_rv_on_G_SUM_usd_bn']['rotation']['pct_rank']:.3f})")
    log("     by G quintile (rho1, RV median): " + " ".join(f"{k}:{v['rho1']:+.3f}/{v['rv_median_bp2']:.0f}" for k, v in B["by_G_SUM_quintile"].items()))

    # ---- C: the move to hedge ----
    Cres = {}
    for lb in LOOKBACKS:
        base = Sp if lb == "prior_settle" else pr("P" + lb.replace(":", ""))
        rl = 100 * np.log(pr("P1530") / base)
        f, _ = S.gamma_regression(R2, G, rl, sig, V, A_L)
        Cres[lb] = {"beta_G": f["beta_G"], "t_G": f["t_G"], "rotation_pct": f["rotation_null"]["pct_rank"], "beta_r": f["beta_r"], "t_r": f["t_r"], "r_sd_pct": float(rl.std(ddof=1))}
    res["C_move_to_hedge"] = Cres
    log("  C: lookback -> beta_G (t, pct): " + " | ".join(f"{k} {v['beta_G']:+.3f} ({v['t_G']:+.2f}, {v['rotation_pct']:.2f})" for k, v in Cres.items()))

    # ---- D: anticipation and reversal ----
    Dres = {}
    r1430 = 100 * np.log(pr("P1430") / Sp)
    f, _ = S.gamma_regression(1e4 * np.log(pr("P1530") / pr("P1430")), G, r1430, sig, V, A_L)
    Dres["hour_before_14_30_to_15_30_Z_at_14_30"] = {k: f[k] for k in ("beta_G", "t_G")} | {"rotation_pct": f["rotation_null"]["pct_rank"]}
    ok = pr("same_contract_next") > 0.5
    ok &= np.isfinite(pr("P0930_next")) & np.isfinite(pr("P1000_next"))
    on = 1e4 * np.log(pr("P0930_next") / pr("P1600")); nx = 1e4 * np.log(pr("P1000_next") / pr("P0930_next"))
    for lab, y in (("overnight_16_00_to_next_09_30", on), ("next_09_30_to_10_00", nx), ("close_plus_overnight", R2 + on)):
        fr = S.nw_fit(y[ok], [Z[ok], r[ok], ZL[ok], sig[ok]])
        Dres[lab] = {"beta_on_Z": float(fr.params[1]), "t": float(fr.tvalues[1]), "n": int(ok.sum())}
    res["D_anticipation_reversal"] = Dres
    log("  D: " + " | ".join(f"{k} b {v.get('beta_G', v.get('beta_on_Z')):+.3f} t {v.get('t_G', v.get('t')):+.2f}" for k, v in Dres.items()))

    # ---- E: which book's sign carries information? ----
    E = {}
    for lab, g in (("G_SPX", GS), ("G_ES", GE), ("G_SUM", G)):
        d = np.where(g < 0, 1.0, 0.0)
        E[lab] = {"short_share": float(d.mean()), "log_rv_on_short_dummy": slope_with_null(lrv, d, [lsig2]), "rho1_on_short_dummy": slope_with_null(rho, d, [sig])}
    both = np.column_stack([np.where(GS < 0, 1.0, 0.0), np.where(GE < 0, 1.0, 0.0)])
    fj = S.nw_fit(lrv, [both[:, 0], both[:, 1], lsig2])
    E["log_rv_joint"] = {"spx_short": float(fj.params[1]), "t_spx": float(fj.tvalues[1]), "es_short": float(fj.params[2]), "t_es": float(fj.tvalues[2])}
    agree = np.sign(GS) == np.sign(GE)
    for lab, msk in (("books_agree", agree), ("books_disagree", ~agree)):
        f, _ = S.gamma_regression(R2[msk], G[msk], r[msk], sig[msk], V[msk], A_L[msk], null=False)
        E[lab] = {k: f[k] for k in ("beta_G", "t_G", "n")}
    for lab, g in (("spx_only_close", GS), ("es_only_close", GE)):
        for reg, msk in (("short", g < 0), ("long", g >= 0)):
            f, _ = S.gamma_regression(R2[msk], g[msk], r[msk], sig[msk], V[msk], A_L[msk], null=False)
            E[f"{lab}_{reg}_gamma"] = {k: f[k] for k in ("beta_G", "t_G", "n")}
    res["E_measure"] = E
    log("  E: log RV on short dummy: " + " | ".join(f"{k} {E[k]['log_rv_on_short_dummy']['beta']:+.3f} (t {E[k]['log_rv_on_short_dummy']['t']:+.2f}, pct {E[k]['log_rv_on_short_dummy']['rotation']['pct_rank']:.3f})" for k in ("G_SPX", "G_ES", "G_SUM"))
        + f"; joint SPX {E['log_rv_joint']['spx_short']:+.3f} (t {E['log_rv_joint']['t_spx']:+.2f}) ES {E['log_rv_joint']['es_short']:+.3f} (t {E['log_rv_joint']['t_es']:+.2f})")
    log("     rho1 on short dummy: " + " | ".join(f"{k} {E[k]['rho1_on_short_dummy']['beta']:+.4f} (t {E[k]['rho1_on_short_dummy']['t']:+.2f}, pct {E[k]['rho1_on_short_dummy']['rotation']['pct_rank']:.3f})" for k in ("G_SPX", "G_ES", "G_SUM")))
    log("     close beta: " + " | ".join(f"{k} {v['beta_G']:+.3f} (t {v['t_G']:+.2f}, n {v['n']})" for k, v in E.items() if "beta_G" in v))

    # ---- F: the controls ----
    F = {"corr_Z_r": float(np.corrcoef(Z, r)[0, 1]), "corr_Z_ZL": float(np.corrcoef(Z, ZL)[0, 1]), "corr_r_ZL": float(np.corrcoef(r, ZL)[0, 1])}
    for lab, cols in (("no_controls", []), ("r_only", [r]), ("ZL_only", [ZL]), ("sig_only", [sig]), ("r_and_sig", [r, sig]), ("all_three", [r, ZL, sig])):
        fr = S.nw_fit(R2, [Z] + cols)
        F[lab] = {"beta_G": float(fr.params[1]), "t_G": float(fr.tvalues[1])}
    for reg, msk in (("short", G < 0), ("long", G >= 0)):
        F[f"corr_Z_ZL_{reg}_gamma"] = float(np.corrcoef(Z[msk], ZL[msk])[0, 1])
    res["F_controls"] = F
    log("  F: " + " | ".join(f"{k} {v['beta_G']:+.3f} (t {v['t_G']:+.2f})" for k, v in F.items() if isinstance(v, dict))
        + f"; corr(Z, r) {F['corr_Z_r']:+.2f} corr(Z, Z_L) {F['corr_Z_ZL']:+.2f} (short {F['corr_Z_ZL_short_gamma']:+.2f}, long {F['corr_Z_ZL_long_gamma']:+.2f})")

    # ---- G: concentration ----
    Gc = {}
    yr = np.array([d[:4] for d in days])
    top = np.abs(R2) >= np.quantile(np.abs(R2), 0.99)
    ter = np.digitize(np.abs(Z), np.quantile(np.abs(Z), [1 / 3, 2 / 3]))
    for lab, msk in (("ex_2020", yr != "2020"), ("ex_top1pct_absR2", ~top), ("ex_march_2020", ~((days >= "2020-02-20") & (days <= "2020-04-30"))),
                     ("absZ_tercile_low", ter == 0), ("absZ_tercile_mid", ter == 1), ("absZ_tercile_high", ter == 2)):
        f, _ = S.gamma_regression(R2[msk], G[msk], r[msk], sig[msk], V[msk], A_L[msk], null=False)
        Gc[lab] = {k: f[k] for k in ("beta_G", "t_G", "n")}
    for lab, msk in (("short_gamma_ex_feb_apr_2020", (G < 0) & ~((days >= "2020-02-20") & (days <= "2020-04-30"))),):
        f, _ = S.gamma_regression(R2[msk], G[msk], r[msk], sig[msk], V[msk], A_L[msk], null=False)
        Gc[lab] = {k: f[k] for k in ("beta_G", "t_G", "n")}
    res["G_concentration"] = Gc
    log("  G: " + " | ".join(f"{k} {v['beta_G']:+.3f} (t {v['t_G']:+.2f}, n {v['n']})" for k, v in Gc.items()))

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
