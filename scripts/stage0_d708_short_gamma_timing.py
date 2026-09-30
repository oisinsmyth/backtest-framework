"""D708 STAGE 0 -- does the hourly continuation on ES-book short-gamma days choose its side, or only ride the drift?
In-sample, D688's panel (2016-01-05 -> 2023-12-29). The design record is
docs/decisions/D708-STAGE-0-DESIGN-does-the-short-gamma-hourly-continuation-choose-its-side.md (committed 9b6b10f8,
before this runner existed). The principal's ruling (2026-09-30): "Timing term as the gate".

    uv run python scripts/stage0_d708_short_gamma_timing.py --selftest
    uv run python scripts/stage0_d708_short_gamma_timing.py --run --data-root "<main checkout>/data"

THE OBJECT (D689's declared primary, unchanged): at t = 10:30 .. 14:30 on D689's 5-minute grid, m = log P(t) -
log P(t-60) (bp), side s = sign(m) (m = 0 dropped), held 60 minutes; f = log P(t+60) - log P(t); the gross in dollars
is s * (P(t+60) - P(t)) * usd_per_point. The last exit is 15:30 (D707's F2 trades 15:30 -> 16:00; never overlapped).

THE POPULATION: P_ES = sessions with G_ES < 0 (D688's ES options book at the prior settlement). Its parts:
P_ES∩SUM (G_SUM < 0) and P_ES\\SUM (G_SUM >= 0). The contrast: G_ES >= 0.

THE TIMING TERM: mu(y, t) = the mean dollar move over EVERY decision row of the population at clock t in calendar
year y (both sides, m = 0 included); tau = s * (x - mu(y, t)) with x = (P(t+60) - P(t)) * usd_per_point at MES;
T = mean(tau) over the population's trades, day-clustered t. Long leg = mean tau over s = +1, short leg = over s = -1.

GATES (fixed in the design): G1 T > 0, clustered t >= 2.0, above the p95 of N1 (the enumerated day rotation of each
day's side schedule over P_ES days); G2 both legs > 0; G3 the same-day-rv-stratified difference of tau (bp; each
population demeaned by its own mu) between G_ES < 0 and G_ES >= 0 rows > 0 and above the p95 of N2 (the enumerated
day-level G_ES label rotation, tau held fixed); G4 T > 0 ex 2020-02-20 -> 04-30, ex 2022, and in at least half the
years with >= 20 trades; G5 T > 0 on P_ES\\SUM.

READINGS: SIGNAL (G1-G5), DRIFT CARRIER (raw mean(s*x) > 0 at t >= 2 but G1 or G2 fails), NOT GAMMA (G1, G2 pass;
G3 fails), EPISODIC (G1-G3 pass; G4 fails), POPULATION MISMATCH (G1-G4 pass; G5 fails), NEITHER otherwise.

Output data/d708_short_gamma_timing.json: statistics only, no per-date GEX (SqueezeMetrics permission, 2026-09-28).
Nothing dated 2024-01-01 or later is read (D688's panel guard); D706's conditioner-only counts are reused for power.
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
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage0_d688_gamma_close as S  # noqa: E402  (D688's committed runner; importing defines, never runs)
import stage0_d689_short_gamma_continuation as Q  # noqa: E402  (D689's committed runner; importing defines, never runs)

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d708_short_gamma_timing.json"
D689_JSON = REPO / "data" / "d689_short_gamma_continuation.json"
D692_JSON = REPO / "data" / "d692_oracle_profile_mes.json"
D706_JSON = REPO / "data" / "d706_vault_short_gamma_count.json"
H = 60
STEP = H // 5
JS = [j for j in range(STEP, 79) if j % STEP == 0 and j + STEP <= 78]      # grid columns of 10:30 .. 14:30
CLOCKS = ["10:30", "11:30", "12:30", "13:30", "14:30"]
T_BAR = 2.0
MIN_YEAR_TRADES = 20
N_AUDIT = 40


class GateError(RuntimeError):
    pass


def P(*a, **k):
    print(*a, **k, flush=True)


# ------------------------------------------------------------------ the timing statistic (pure; the self-test drives it)
def drift(x, di, ci, yr_day, pop_day):
    """mu[(y, c)] = mean of x over every finite row on a population day at clock c in year y (both sides, m = 0 in)."""
    ok = np.isfinite(x) & pop_day[di]
    mu = {}
    for y in np.unique(yr_day):
        for c in range(len(CLOCKS)):
            sel = ok & (yr_day[di] == y) & (ci == c)
            if sel.any():
                mu[(y, c)] = float(x[sel].mean())
    return mu


def drift_pooled(x, di, ci, pop_day):
    ok = np.isfinite(x) & pop_day[di]
    return {c: float(x[ok & (ci == c)].mean()) for c in range(len(CLOCKS)) if (ok & (ci == c)).any()}


def tau_of(s, x, di, ci, yr_day, mu):
    m = np.array([mu.get((yr_day[d], c), np.nan) for d, c in zip(di, ci)])
    return s * (x - m)


def tau_pooled_of(s, x, ci, mup):
    return s * (x - np.array([mup.get(c, np.nan) for c in ci]))


def cl_mean(y, groups):
    """Day-clustered mean and t (as D689's `mt`)."""
    if len(y) < 10:
        return {"n": int(len(y)), "mean": float(np.mean(y)) if len(y) else None}
    r = sm.OLS(y, np.ones((len(y), 1))).fit(cov_type="cluster", cov_kwds={"groups": groups})
    naive = float(y.mean() / (y.std(ddof=1) / math.sqrt(len(y)))) if y.std(ddof=1) > 0 else float("nan")
    return {"n": int(len(y)), "mean": float(r.params[0]), "t": float(r.tvalues[0]), "t_naive": naive, "median": float(np.median(y))}


def schedule_matrices(s, x_dm, di, ci, pop_days):
    """Day x clock matrices over the population's days in date order: S (side, 0 where no trade), X (x - mu, NaN
    where no finite outcome). pop_days holds panel day INDICES (ints), the same kind as di."""
    if not np.issubdtype(np.asarray(pop_days).dtype, np.integer):
        raise GateError("[SCHEDULE] pop_days must be panel day indices")
    pos = {d: i for i, d in enumerate(pop_days)}
    n = len(pop_days)
    Sm = np.zeros((n, len(CLOCKS)))
    Xm = np.full((n, len(CLOCKS)), np.nan)
    for sv, xv, d, c in zip(s, x_dm, di, ci):
        if d in pos:
            Sm[pos[d], c] = sv
            Xm[pos[d], c] = xv
    return Sm, Xm


def rotation_T(Sm, Xm, ks):
    """T under each rotation k: day i's outcomes paired with day (i - k)'s side schedule (D688's `rotate` convention).
    Column 0 is k = 0, the observed T."""
    n = Sm.shape[0]
    out = np.empty(len(ks))
    fin = np.isfinite(Xm)
    X0 = np.where(fin, Xm, 0.0)
    for j, k in enumerate(ks):
        Sk = Sm[(np.arange(n) - k) % n]
        valid = (Sk != 0) & fin
        out[j] = (Sk * X0)[valid].sum() / valid.sum()
    return out


# ------------------------------------------------------------------ audits
def lag_audit(bars_by_day, days, PG, s, di, ci, sample, log=P):
    """Second implementation: m, side and the dollar move re-derived from the raw 1-minute bars by dict lookup, never
    from the grid. P(t) is the close of the minute before t; P(09:30) is the 09:30 open."""
    for i in sample:
        d, c = days[di[i]], ci[i]
        rows = bars_by_day[d]
        t = pd.Timestamp("2000-01-01 " + CLOCKS[c])
        def px(ts):
            if ts.strftime("%H:%M") == "09:30":
                return rows["open"]["09:30"]
            return rows["close"][(ts - pd.Timedelta(minutes=1)).strftime("%H:%M")]
        p0, p1, p2 = px(t - pd.Timedelta(minutes=H)), px(t), px(t + pd.Timedelta(minutes=H))
        side = float(np.sign(math.log(p1) - math.log(p0)))
        if side != s[i]:
            raise GateError(f"[LAG] {d} {CLOCKS[c]}: side {s[i]} vs the bar loop's {side}")
        j = JS[c]
        if not (p1 == PG[di[i], j] and p2 == PG[di[i], j + STEP]):
            raise GateError(f"[LAG] {d} {CLOCKS[c]}: grid prices {PG[di[i], j]}, {PG[di[i], j + STEP]} vs the bar loop's {p1}, {p2}")
    log(f"  lag audit: {len(sample)} decisions re-derived from raw 1-minute bars: equal")


def sign_audit(usd_per_point):
    up = 10.0
    if not (np.sign(1.0) * up * usd_per_point > 0 and np.sign(-1.0) * up * usd_per_point < 0):
        raise GateError("[SIGN] a favourable move does not pay the long and cost the short")
    mu = {("2019", 0): 7.0}
    if tau_of(np.array([1.0, -1.0]), np.array([7.0, 7.0]), np.array([0, 0]), np.array([0, 0]), np.array(["2019"]), mu).tolist() != [0.0, 0.0]:
        raise GateError("[SIGN] a trade whose outcome equals the drift does not score zero")


# ------------------------------------------------------------------ the self-test
def selftest() -> int:
    rng = np.random.default_rng(708)
    nd, nc = 900, 5
    yr_day = np.array([str(2016 + d // 113) for d in range(nd)])
    pop_day = np.ones(nd, bool)
    di =np.repeat(np.arange(nd), nc)
    ci = np.tile(np.arange(nc), nd)

    def run_case(drift_usd, timing_usd):
        m = rng.standard_normal(nd * nc)
        s = np.sign(m)
        x = drift_usd + timing_usd * s + 60.0 * rng.standard_normal(nd * nc)
        mu = drift(x, di, ci, yr_day, pop_day)
        tau = tau_of(s, x, di, ci, yr_day, mu)
        Sm, Xm = schedule_matrices(s, x - np.array([mu[(yr_day[d], c)] for d, c in zip(di, ci)]), di, ci, np.arange(nd))
        ks = S.rot_ks(nd)
        rot = rotation_T(Sm, Xm, ks)
        if not np.isclose(rot[0], tau.mean(), rtol=1e-12, atol=1e-12):
            raise GateError(f"[SELFTEST] N1's k = 0 column {rot[0]!r} != T {tau.mean()!r}")
        c = cl_mean(tau, di)
        raw = cl_mean(s * x, di)
        g1 = c["mean"] > 0 and c["t"] >= T_BAR and S.blk(rot[0], rot[1:])["above_p95"]
        return g1, raw

    g1, _ = run_case(drift_usd=0.0, timing_usd=8.0)
    if not g1:
        raise GateError("[SELFTEST] a planted timing effect failed G1")
    g1, raw = run_case(drift_usd=10.0, timing_usd=0.0)
    if g1:
        raise GateError("[SELFTEST] a pure drift passed G1")
    # a pure drift with more long than short signals must pass the raw mean: tilt the sides
    m = rng.standard_normal(nd * nc) + 0.6
    s = np.sign(m)
    x = 10.0 + 60.0 * rng.standard_normal(nd * nc)
    mu = drift(x, di, ci, yr_day, pop_day)
    tau = tau_of(s, x, di, ci, yr_day, mu)
    raw = cl_mean(s * x, di)
    if not (raw["mean"] > 0 and raw["t"] >= T_BAR):
        raise GateError(f"[SELFTEST] a long-tilted pure drift did not pass the raw mean ({raw})")
    if cl_mean(tau, di)["t"] >= T_BAR:
        raise GateError("[SELFTEST] a long-tilted pure drift passed the timing term")
    # the lag audit must raise on a book whose side is taken one hour late
    PG = np.exp(np.cumsum(0.001 * rng.standard_normal((3, 79)), axis=1)) * 3000.0
    PG[:, 0] = PG[:, 0]
    grid = [(pd.Timestamp("2000-01-01 09:30") + pd.Timedelta(minutes=5 * k)) for k in range(79)]
    bars = {}
    for d in range(3):
        close = {(g - pd.Timedelta(minutes=1)).strftime("%H:%M"): PG[d, k] for k, g in enumerate(grid) if k > 0}
        bars[f"s{d}"] = {"open": {"09:30": PG[d, 0]}, "close": close}
    sdays = np.array(["s0", "s1", "s2"])
    di3 = np.repeat(np.arange(3), 5)
    ci3 = np.tile(np.arange(5), 3)
    good = np.array([np.sign(math.log(PG[d, JS[c]]) - math.log(PG[d, JS[c] - STEP])) for d, c in zip(di3, ci3)])
    lag_audit(bars, sdays, PG, good, di3, ci3, range(15), log=lambda *a: None)
    late = np.array([np.sign(math.log(PG[d, JS[c] + STEP]) - math.log(PG[d, JS[c]])) for d, c in zip(di3, ci3)])
    try:
        lag_audit(bars, sdays, PG, late, di3, ci3, range(15), log=lambda *a: None)
    except GateError:
        pass
    else:
        raise GateError("[SELFTEST] the lag audit did not fire on a side taken one hour late")
    sign_audit(5.0)
    P("SELFTEST OK: planted timing passes G1; pure drift fails G1; a long-tilted drift passes the raw mean and fails the "
      "timing term; the lag audit fires on a late side; the sign audit holds")
    return 0


# ------------------------------------------------------------------ run
def run(data_root: Path, log=P) -> int:
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
    S.guard_window(D.index, "D708 panel")
    days = D.index.to_numpy().astype(str)
    nd = len(days)
    sig = D["sig"].to_numpy(float)
    G_SUM = D["G_SUM"].to_numpy(float)
    G_ES = D["G_ES"].to_numpy(float)
    G_SPX = D["G_SPX"].to_numpy(float)
    r = 100 * np.log(D["P1530"].to_numpy(float) / D["S_prev"].to_numpy(float))
    R2 = 1e4 * np.log(D["P1600"].to_numpy(float) / D["P1530"].to_numpy(float))
    f688, _ = S.gamma_regression(R2, G_SUM, r, sig, D["V"].to_numpy(float), D["A_L"].to_numpy(float), null=False)
    ref = json.loads(Q.D688_JSON.read_text(encoding="utf-8"))["gate1"]["G1"]["beta_G"]
    if f688["beta_G"] != ref:
        raise GateError(f"[REPRO] beta_G {f688['beta_G']!r} vs D688's {ref!r}")
    log(f"  D688 REPRODUCED: beta_G {f688['beta_G']!r} on {nd} sessions ({time.time() - t0:.0f} s)")

    # ---- D689's 5-minute grid ----
    b = I["bars"]
    b = b[b["day"].isin(set(days))]
    S.guard_window(b["day"].unique(), "D708 bars")
    close = b.pivot(index="day", columns="hhmm", values="close").reindex(days)
    op = b[b["hhmm"] == "09:30"].set_index("day")["open"].reindex(days).to_numpy(float)
    grid = [(pd.Timestamp("2000-01-01 09:30") + pd.Timedelta(minutes=5 * k)) for k in range(79)]
    PG = np.column_stack([op] + [close[(g - pd.Timedelta(minutes=1)).strftime("%H:%M")].to_numpy(float) for g in grid[1:]])
    L = np.log(PG)
    r5 = 1e4 * np.diff(L, axis=1)
    cum_rv = np.concatenate([np.full((nd, 1), np.nan), np.cumsum(r5 * r5, axis=1)], axis=1)
    if [grid[j].strftime("%H:%M") for j in JS] != CLOCKS:
        raise GateError(f"[CLOCK] grid columns {JS} are not {CLOCKS}")
    E = S.d685()
    mes, esf = E.cost_spec("ES", "micro"), E.cost_spec("ES", "full")
    arm = E.load_arm()
    rows = []
    for c, j in enumerate(JS):
        with np.errstate(divide="ignore", invalid="ignore"):
            lrv = np.log(cum_rv[:, j] / j)
        rows.append(pd.DataFrame({"di": np.arange(nd), "ci": c, "m": 1e4 * (L[:, j] - L[:, j - STEP]), "f": 1e4 * (L[:, j + STEP] - L[:, j]),
                                  "dp": PG[:, j + STEP] - PG[:, j], "P": PG[:, j], "lrv": lrv}))
    A = pd.concat(rows, ignore_index=True)
    A = A[np.isfinite(A[["m", "f", "dp", "P"]].to_numpy()).all(1)].reset_index(drop=True)      # every decision row (m = 0 kept for mu)
    di_a = A["di"].to_numpy(); ci_a = A["ci"].to_numpy(); m_a = A["m"].to_numpy(); f_a = A["f"].to_numpy(); dp_a = A["dp"].to_numpy()
    x_a = dp_a * mes["usd_per_point"]                  # dollar move at MES
    yr_day = np.array([d[:4] for d in days])
    in_crash = (days >= Q.CRASH[0]) & (days <= Q.CRASH[1])
    es_short = G_ES < 0
    sum_short = G_SUM < 0
    pops = {"P_ES": es_short, "P_ES_and_SUM": es_short & sum_short, "P_ES_not_SUM": es_short & ~sum_short, "long_gamma_ES": ~es_short}

    # ---- the reproduction guards (D689 primary; D692's cells) ----
    tr = (m_a != 0) & np.isfinite(A["lrv"].to_numpy())       # D689's trade rows (it required a finite lrv)
    s_a = np.sign(m_a)
    g689 = (s_a * x_a)[tr & sum_short[di_a]]
    rep = cl_mean(g689, di_a[tr & sum_short[di_a]])
    d689 = json.loads(D689_JSON.read_text(encoding="utf-8"))["cells"]["h60_k0.0"]["C_concentration"]["all"]
    if not (rep["n"] == d689["n"] and rep["mean"] == d689["mean_gross_mes_usd"] and rep["t"] == d689["t"]):
        raise GateError(f"[REPRO] D689 primary: n {rep['n']} mean {rep['mean']!r} t {rep['t']!r} vs {d689}")
    prof = json.loads(D692_JSON.read_text(encoding="utf-8"))["profile"]["1_gamma_regime"]
    for lab, mask in (("ES<0", es_short), ("SPX>=0,ES<0", (G_SPX >= 0) & es_short)):
        g = (s_a * x_a)[tr & mask[di_a]]
        if not (len(g) == prof[lab]["n"] and np.isclose(g.mean(), prof[lab]["mean_gross"], rtol=1e-12, atol=0)):
            raise GateError(f"[REPRO] D692 {lab}: n {len(g)} mean {g.mean()!r} vs n {prof[lab]['n']} mean {prof[lab]['mean_gross']!r}")
    log(f"  D689 REPRODUCED: n {rep['n']}, +${rep['mean']:.4f}, t {rep['t']:.4f}; D692's ES<0 and SPX>=0,ES<0 cells reproduced")

    # ---- audits ----
    sign_audit(mes["usd_per_point"])
    bars_by_day = {}
    samp_days = set()
    rng = np.random.default_rng(708)
    sample = rng.choice(np.flatnonzero(tr), N_AUDIT, replace=False)
    for i in sample:
        samp_days.add(days[di_a[i]])
    bb = b[b["day"].isin(samp_days)]
    for d, g in bb.groupby("day"):
        bars_by_day[d] = {"open": dict(zip(g["hhmm"], g["open"])), "close": dict(zip(g["hhmm"], g["close"]))}
    lag_audit(bars_by_day, days, PG, s_a, di_a, ci_a, sample, log)

    res = {"spec": "D708 STAGE 0 (in-sample; the timing term over the per-year clock-matched drift, on ES-book short-gamma days)",
           "design_commit": "9b6b10f8", "reproduction": {"beta_G": f688["beta_G"], "d689_primary": rep, "sessions": nd},
           "costs": {"mes": mes, "es_full": esf}, "populations": {}}

    # ---- per population: drift, tau, T, legs, raw, pooled ----
    tau_bp_all = np.full(len(A), np.nan)                 # for G3: each population demeaned by its own mu (bp)
    TAU = {}
    for name, pday in pops.items():
        mu = drift(x_a, di_a, ci_a, yr_day, pday)
        mup = drift_pooled(x_a, di_a, ci_a, pday)
        mu_bp = drift(f_a, di_a, ci_a, yr_day, pday)
        sel = tr & pday[di_a]
        s, x, di, ci = s_a[sel], x_a[sel], di_a[sel], ci_a[sel]
        tau = tau_of(s, x, di, ci, yr_day, mu)
        tau_p = tau_pooled_of(s, x, ci, mup)
        tau_bp = tau_of(s, f_a[sel], di, ci, yr_day, mu_bp)
        if name in ("P_ES", "long_gamma_ES"):
            tau_bp_all[np.flatnonzero(sel)] = tau_bp
        TAU[name] = {"tau": tau, "s": s, "x": x, "di": di, "ci": ci, "mu": mu}
        C = {"days": int(pday.sum()), "trades": int(sel.sum()), "trades_per_day": float(sel.sum() / max(1, pday.sum()))}
        C["T_usd_mes"] = cl_mean(tau, di)
        C["T_bp"] = cl_mean(tau_bp, di)
        C["T_pooled_drift_usd_mes"] = cl_mean(tau_p, di)
        C["raw_mean_s_x_usd_mes"] = cl_mean(s * x, di)
        C["long_leg_excess_usd_mes"] = cl_mean(tau[s > 0], di[s > 0])
        C["short_leg_excess_usd_mes"] = cl_mean(tau[s < 0], di[s < 0])
        C["long_leg_raw_usd_mes"] = float((x[s > 0]).mean())
        C["short_leg_raw_usd_mes"] = float((-x[s < 0]).mean())
        C["share_long"] = float((s > 0).mean())
        C["drift_by_clock_pooled_usd_mes"] = {CLOCKS[c]: v for c, v in mup.items()}
        C["drift_share_of_raw"] = float(1 - C["T_usd_mes"]["mean"] / C["raw_mean_s_x_usd_mes"]["mean"]) if C["raw_mean_s_x_usd_mes"]["mean"] else None
        yr = yr_day[di]
        cr = in_crash[di]
        C["by_year_T_usd_mes"] = {y: cl_mean(tau[yr == y], di[yr == y]) for y in sorted(set(yr))}
        C["T_ex_crash"] = cl_mean(tau[~cr], di[~cr])
        C["T_ex_2022"] = cl_mean(tau[yr != "2022"], di[yr != "2022"])
        C["by_clock_T_usd_mes"] = {CLOCKS[c]: cl_mean(tau[ci == c], di[ci == c]) for c in range(len(CLOCKS))}
        res["populations"][name] = C
        log(f"  {name}: {C['days']} days, {C['trades']} trades; T ${C['T_usd_mes']['mean']:+.2f} (t {C['T_usd_mes'].get('t', float('nan')):+.2f}); "
            f"raw ${C['raw_mean_s_x_usd_mes']['mean']:+.2f} (t {C['raw_mean_s_x_usd_mes'].get('t', float('nan')):+.2f}); "
            f"legs long ${C['long_leg_excess_usd_mes']['mean']:+.2f} short ${C['short_leg_excess_usd_mes']['mean']:+.2f}; pooled-drift T ${C['T_pooled_drift_usd_mes']['mean']:+.2f}")

    # ---- right-quantity ----
    PE = TAU["P_ES"]
    if np.isclose(PE["tau"].mean(), (PE["s"] * PE["x"]).mean()):
        raise GateError("[RIGHT-QUANTITY] T equals the raw mean: the drift was not subtracted")
    mup_es = drift_pooled(x_a, di_a, ci_a, pops["P_ES"])
    if all(np.isclose(PE["mu"][(y, c)], mup_es[c]) for (y, c) in PE["mu"]):
        raise GateError("[RIGHT-QUANTITY] the per-year drift equals the pooled drift")

    # ---- N1: the enumerated day rotation of the side schedule over P_ES days ----
    pdays = np.flatnonzero(pops["P_ES"])
    x_dm = PE["tau"] * PE["s"]                             # x - mu, since s is +/-1
    Sm, Xm = schedule_matrices(PE["s"], x_dm, PE["di"], PE["ci"], pdays)
    ks1 = S.rot_ks(len(pdays))
    rot = rotation_T(Sm, Xm, ks1)
    if not np.isclose(rot[0], PE["tau"].mean(), rtol=1e-12, atol=1e-12):
        raise GateError(f"[RIGHT-QUANTITY] N1's k = 0 column {rot[0]!r} != T {PE['tau'].mean()!r}")
    n1 = S.blk(rot[0], rot[1:])
    res["N1_day_rotation_T_usd_mes"] = n1
    log(f"  N1: T ${n1['observed']:+.3f} vs rotation p50 ${n1['p50']:+.3f} p95 ${n1['p95']:+.3f} (pct {n1['pct_rank']:.3f}, {n1['n_offsets']} offsets)")

    # ---- N2 / G3: the gamma contrast on tau (bp), same-day rv strata, G_ES label rotated ----
    ok3 = np.isfinite(tau_bp_all) & tr
    lrv3 = A["lrv"].to_numpy()[ok3]
    q_rv = np.minimum((pd.Series(lrv3).rank(pct=True).to_numpy() * Q.N_STRATA).astype(int), Q.N_STRATA - 1)
    v = Q.stratified_diff(tau_bp_all[ok3], q_rv, di_a[ok3], es_short.astype(float), S.rot_ks(nd))
    n2 = S.blk(v[0], v[1:])
    res["G3_stratified_tau_short_minus_long_bp"] = n2
    log(f"  G3: stratified tau short - long {n2['observed']:+.3f} bp vs label rotation p50 {n2['p50']:+.3f} p95 {n2['p95']:+.3f} (pct {n2['pct_rank']:.3f})")

    # ---- the books (E as proposed, and the always-long control on the same windows), P_ES ----
    sel = tr & pops["P_ES"][di_a]
    books = {}
    for lab, cs in (("mes", mes), ("es_full", esf)):
        gr = s_a[sel] * dp_a[sel] * cs["usd_per_point"]
        books[f"E_{lab}"] = Q.four_groups(gr, gr - cs["cost_rt_usd"], di_a[sel], s_a[sel], days, nd, arm, cs["cost_rt_usd"])
        gl = dp_a[sel] * cs["usd_per_point"]
        books[f"always_long_{lab}"] = Q.four_groups(gl, gl - cs["cost_rt_usd"], di_a[sel], np.ones(sel.sum()), days, nd, arm, cs["cost_rt_usd"])
    res["books_P_ES"] = books
    # the price question: by year, gross $ and bp, the round trip in bp at that year's price, fee share of gross
    yr = yr_day[di_a[sel]]
    Pm = A["P"].to_numpy()[sel]
    gbp = (s_a * f_a)[sel]
    gus = (s_a * x_a)[sel]
    res["price_question_by_year"] = {y: {"trades": int((yr == y).sum()), "gross_usd_mes": float(gus[yr == y].mean()), "gross_bp": float(gbp[yr == y].mean()),
                                         "mean_price": float(Pm[yr == y].mean()), "cost_bp_mes": float(mes["cost_rt_usd"] / (mes["usd_per_point"] * Pm[yr == y].mean()) * 1e4),
                                         "fee_share_of_gross": float(mes["cost_rt_usd"] / gus[yr == y].mean()) if gus[yr == y].mean() != 0 else None}
                                     for y in sorted(set(yr))}
    res["rho_with_d707_f2"] = "not computed: D707's runner exposes no in-sample daily series without its vault path; the clocks are adjacent (15:30) and never overlap"
    for bl, bv in books.items():
        if "net" in bv:
            log(f"  book {bl}: {bv['trades_per_year']:.0f}/yr net Sharpe {bv['net']['sharpe_daily']:+.2f} Sortino {bv['net']['sortino_daily']:+.2f}; "
                f"gross {bv['gross']['sharpe_daily']:+.2f}/{bv['gross']['sortino_daily']:+.2f}; mean net ${bv['net']['mean_per_trade_usd']:+.2f}; rho arm {bv.get('rho_with_macd_arm', float('nan')):+.3f}")

    # ---- the gates ----
    Cp = res["populations"]["P_ES"]
    T = Cp["T_usd_mes"]
    g1 = bool(T["mean"] > 0 and T["t"] >= T_BAR and n1["above_p95"])
    g2 = bool(Cp["long_leg_excess_usd_mes"]["mean"] > 0 and Cp["short_leg_excess_usd_mes"]["mean"] > 0)
    g3 = bool(n2["observed"] > 0 and n2["above_p95"])
    elig = {y: v for y, v in Cp["by_year_T_usd_mes"].items() if v["n"] >= MIN_YEAR_TRADES}
    pos = sum(1 for v in elig.values() if v["mean"] > 0)
    g4 = bool(Cp["T_ex_crash"]["mean"] > 0 and Cp["T_ex_2022"]["mean"] > 0 and 2 * pos >= len(elig))
    g5 = bool(res["populations"]["P_ES_not_SUM"]["T_usd_mes"]["mean"] > 0)
    raw = Cp["raw_mean_s_x_usd_mes"]
    raw_ok = bool(raw["mean"] > 0 and raw["t"] >= T_BAR)
    if g1 and g2 and g3 and g4 and g5:
        reading = "SIGNAL: GO for a joint-vault pre-registration"
    elif raw_ok and not (g1 and g2):
        reading = "DRIFT CARRIER"
    elif g1 and g2 and not g3:
        reading = "NOT GAMMA"
    elif g1 and g2 and g3 and not g4:
        reading = "EPISODIC"
    elif g1 and g2 and g3 and g4 and not g5:
        reading = "POPULATION MISMATCH"
    else:
        reading = "NEITHER"
    res["gates"] = {"G1_timing": g1, "G2_both_legs": g2, "G3_gamma_contrast": g3, "G4_not_one_episode": g4, "G4_years": {"eligible": len(elig), "positive": pos},
                    "G5_unmeasured_part": g5, "raw_mean_passes": raw_ok, "reading": reading}
    log(f"  GATES: G1 {g1} G2 {g2} G3 {g3} G4 {g4} ({pos}/{len(elig)} years) G5 {g5}; raw {raw_ok} -> {reading}")

    # ---- power for the joint run (D706's conditioner-only counts reused) ----
    cnt = json.loads(D706_JSON.read_text(encoding="utf-8"))["slices"]
    n_unseen = cnt["vault_2025_03_2026_09"]["short_gamma_sessions"]["G_ES"] + cnt["clean_2024_01_2025_02"]["short_gamma_sessions"]["G_ES"]
    tau_x = PE["tau"][~in_crash[PE["di"]]]
    snr = Cp["T_ex_crash"]["mean"] / tau_x.std(ddof=1)
    shrink = T["t"] / T["t_naive"]
    n_tr = n_unseen * Cp["trades_per_day"]
    pw = {}
    for frac in (1.0, 0.5):
        et = frac * snr * math.sqrt(n_tr) * shrink
        pw[f"{int(frac * 100)}pct"] = {"expected_t": float(et), "pass_prob_one_sided_5pct": float(1 - norm.cdf(1.645 - et))}
    res["power_joint_run"] = {"unseen_es_book_short_sessions": int(n_unseen), "trades_per_day": Cp["trades_per_day"], "expected_trades": float(n_tr),
                              "snr_ex_crash": float(snr), "cluster_shrink": float(shrink), **pw}
    log(f"  POWER: {n_unseen} unseen ES-book-short sessions x {Cp['trades_per_day']:.2f} = {n_tr:.0f} trades; SNR {snr:.4f}; "
        f"expected t {pw['100pct']['expected_t']:.2f} (pass {pw['100pct']['pass_prob_one_sided_5pct']:.2f}) / {pw['50pct']['expected_t']:.2f} (pass {pw['50pct']['pass_prob_one_sided_5pct']:.2f})")

    res["timing_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8")
    log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']} s")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    sys.exit(run(a.data_root) if a.run else 1)
