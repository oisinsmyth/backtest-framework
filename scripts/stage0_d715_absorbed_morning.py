"""D715 STAGE 0 -- the absorbed morning move (proposal B). Design:
docs/decisions/D715-STAGE-0-DESIGN-the-absorbed-morning-move.md (582022f6, before this runner). The principal:
"Pre-reg, build and run a test for B please".

    uv run python scripts/stage0_d715_absorbed_morning.py --selftest
    uv run python scripts/stage0_d715_absorbed_morning.py --run --data-root "<main checkout>/data"

CANDIDATES: ES sessions >= 380 bars, 2016-01-04 .. 2023-12-29, not a roll session, one contract over the bars used
(09:30, 10:29, 10:30, 15:29, 15:59), >= 55 of the 60 first-hour minutes with signed flow for that contract.
m = ln(P10:30 / P09:30) (P09:30 = the 09:30 bar's open, P10:30 = the 10:29 bar's close); sigma60 = sd of m over the
previous 20 candidates (>= 15); z = m / sigma60; I = (sum buy - sum sell) / sum volume, 09:30-10:29; I_hat = a + b z,
OLS on the previous 250 candidates (strictly prior); R = sign(z) (I - I_hat); absorbed = R < median of the previous 250
R; breadth = >= 2 of the available NQ/RTY/YM first-hour signs agree with sign(z), >= 2 available. Trade s = sign(z),
entry the 10:30 bar's open, exit the 15:59 bar's close, one MES: gross = s (exit - entry) x $5, net = gross - $4.42.
GATES G1-G5 and the readings: the design record, s.4.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d689_short_gamma_continuation as Q   # noqa: E402  (four_groups; importing defines, never runs)

OUT = REPO / "data" / "stage0_d715_absorbed_morning.json"
LO, HI, CUT = "2016-01-04", "2023-12-29", "2024-01-01"
COST, USD = 4.42, 5.0
N_SIG, MIN_SIG, N_FIT, N_MED, MIN_FLOW = 20, 15, 250, 250, 55
ROT_MIN = 20
BARS = ("09:30", "10:29", "10:30", "15:29", "15:59")
FIRST_HOUR = [(pd.Timestamp("2000-01-01 09:30") + pd.Timedelta(minutes=k)).strftime("%H:%M") for k in range(60)]
BREADTH = ("NQ", "RTY", "YM")


class D715Error(RuntimeError):
    pass


def P(*a, **k):
    print(*a, **k, flush=True)


def seal(days, what):
    d = pd.Series(np.asarray(days)).astype(str)
    if len(d) and (d >= CUT).any():
        raise D715Error(f"[SEAL] {what}: a row dated {d[d >= CUT].min()} reached the build")


# ------------------------------------------------------------------ the walk-forward (pure; the self-test drives it)
def walk_forward(m: np.ndarray, I: np.ndarray, leak: bool = False) -> dict[str, np.ndarray]:
    """sigma60, z, (a, b), R and the absorbed flag, each from strictly earlier candidates. `leak` includes the current
    candidate in the fit (the self-test's broken book)."""
    n = len(m)
    sig = np.full(n, np.nan); z = np.full(n, np.nan); a = np.full(n, np.nan); b = np.full(n, np.nan)
    R = np.full(n, np.nan); absorbed = np.zeros(n, bool); med = np.full(n, np.nan)
    for i in range(n):
        lo = max(0, i - N_SIG)
        w = m[lo:i]
        if len(w) >= MIN_SIG:
            sig[i] = np.std(w, ddof=1)
            z[i] = m[i] / sig[i] if sig[i] > 0 else np.nan
    for i in range(n):
        hi = i + 1 if leak else i
        idx = np.arange(max(0, hi - N_FIT), hi)
        idx = idx[np.isfinite(z[idx]) & np.isfinite(I[idx])]
        if len(idx) >= N_FIT - (1 if leak else 0) and np.isfinite(z[i]) and z[i] != 0:
            X = np.column_stack([np.ones(len(idx)), z[idx]])
            coef = np.linalg.lstsq(X, I[idx], rcond=None)[0]
            a[i], b[i] = coef
            R[i] = np.sign(z[i]) * (I[i] - (a[i] + b[i] * z[i]))
    for i in range(n):
        prior = R[max(0, i - 3 * N_MED):i]
        prior = prior[np.isfinite(prior)][-N_MED:]
        if len(prior) == N_MED and np.isfinite(R[i]):
            med[i] = np.median(prior)
            absorbed[i] = R[i] < med[i]
    return {"sig": sig, "z": z, "a": a, "b": b, "R": R, "med": med, "absorbed": absorbed}


# ------------------------------------------------------------------ the build
def load(data_root: Path, log=P) -> pd.DataFrame:
    fx = data_root / "fixtures"
    sess = pd.read_csv(fx / "fut_index_sessions.csv.gz", usecols=["root", "day", "bars"], dtype={"root": str, "day": str}, encoding="utf-8")
    cal = set(sess[(sess["root"] == "ES") & (sess["bars"] >= 380) & (sess["day"] >= LO) & (sess["day"] <= HI)]["day"])
    b = pd.read_csv(fx / "fut_ES_rth_1m.csv.gz", usecols=["day", "hhmm", "contract", "open", "close"], dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
    b = b[(b["day"] >= LO) & (b["day"] <= HI)]
    seal(b["day"], "ES bars")
    nb = b.groupby("day").size()
    days = np.array(sorted(d for d in cal if nb.get(d, 0) >= 380))
    b = b[b["day"].isin(set(days))]
    kb = b[b["hhmm"].isin(BARS)].pivot(index="day", columns="hhmm", values=["open", "close", "contract"]).reindex(days)
    s = pd.read_csv(fx / "fut_ES_signed_1m.csv.gz", usecols=["day", "hhmm", "contract", "volume", "buy", "sell"], dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
    s = s[(s["day"] >= LO) & (s["day"] <= HI) & s["hhmm"].isin(FIRST_HOUR)]
    seal(s["day"], "ES signed flow")
    D = pd.DataFrame(index=days)
    D["contract"] = kb[("contract", "09:30")]
    same = np.ones(len(days), bool)
    for h in BARS:
        same &= (kb[("contract", h)] == D["contract"]).to_numpy()
    D["one_contract"] = same
    D["P0930"] = kb[("open", "09:30")]; D["P1030"] = kb[("close", "10:29")]; D["entry"] = kb[("open", "10:30")]
    D["P1530"] = kb[("close", "15:29")]; D["exit"] = kb[("close", "15:59")]
    s = s.merge(D[["contract"]].rename(columns={"contract": "sc"}), left_on="day", right_index=True)
    s = s[s["contract"] == s["sc"]]
    fl = s.groupby("day").agg(n_min=("hhmm", "size"), vol=("volume", "sum"), buy=("buy", "sum"), sell=("sell", "sum")).reindex(days)
    D["flow_minutes"] = fl["n_min"].fillna(0).astype(int)
    D["vol1h"] = fl["vol"]
    D["I"] = (fl["buy"] - fl["sell"]) / fl["vol"]
    prev = D["contract"].shift(1)
    D["roll"] = (D["contract"] != prev) & prev.notna()
    ok = D["one_contract"] & ~D["roll"] & (D["flow_minutes"] >= MIN_FLOW) & np.isfinite(D[["P0930", "P1030", "entry", "P1530", "exit", "I"]].to_numpy(float)).all(1)
    C = D[ok].copy()
    C["m"] = np.log(C["P1030"].astype(float) / C["P0930"].astype(float))
    # breadth
    for r in BREADTH:
        rb = pd.read_csv(fx / f"fut_{r}_rth_1m.csv.gz", usecols=["day", "hhmm", "contract", "open", "close"], dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
        rb = rb[(rb["day"] >= LO) & (rb["day"] <= HI) & rb["hhmm"].isin(["09:30", "10:29"])]
        seal(rb["day"], f"{r} bars")
        pv = rb.pivot(index="day", columns="hhmm", values=["open", "close", "contract"]).reindex(C.index)
        sgn = np.sign(np.log(pv[("close", "10:29")].astype(float) / pv[("open", "09:30")].astype(float)))
        sgn[pv[("contract", "09:30")] != pv[("contract", "10:29")]] = np.nan
        C[f"sgn_{r}"] = sgn.to_numpy(float)
    log(f"  candidates: {len(C)} of {len(days)} ES sessions (roll {int(D['roll'].sum())}, mixed contract {int((~D['one_contract']).sum())}, "
        f"flow < {MIN_FLOW} min {int((D['flow_minutes'] < MIN_FLOW).sum())})")
    return C, b, s


def build(C: pd.DataFrame) -> pd.DataFrame:
    wf = walk_forward(C["m"].to_numpy(float), C["I"].to_numpy(float))
    for k, v in wf.items():
        C[k] = v
    s = np.sign(C["z"].to_numpy(float))
    C["s"] = s
    sg = np.column_stack([C[f"sgn_{r}"].to_numpy(float) for r in BREADTH])
    avail = np.isfinite(sg).sum(1)
    agree = (sg == s[:, None]).sum(1)
    C["breadth"] = (avail >= 2) & (agree >= 2)
    C["move"] = (C["exit"].astype(float) - C["entry"].astype(float)) * USD
    C["g"] = s * C["move"]
    C["net"] = C["g"] - COST
    C["g_last30"] = s * (C["exit"].astype(float) - C["P1530"].astype(float)) * USD
    v = C["vol1h"].to_numpy(float)
    rel = np.full(len(C), np.nan)
    for i in range(len(C)):
        w = v[max(0, i - N_SIG):i]
        if len(w) >= MIN_SIG:
            rel[i] = v[i] / np.median(w)
    C["relvol"] = rel
    qmed = np.full(len(C), np.nan)
    for i in range(len(C)):
        w = rel[max(0, i - N_MED):i]
        w = w[np.isfinite(w)]
        if len(w) >= N_SIG:
            qmed[i] = np.median(w)
    C["quiet"] = rel < qmed
    return C


# ------------------------------------------------------------------ statistics
def nw_t(x, lags=5):
    x = np.asarray(x, float)
    if len(x) < 10:
        return float("nan")
    r = sm.OLS(x, np.ones((len(x), 1))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(r.tvalues[0])


def blk(obs, null):
    null = np.asarray(null, float)
    return {"observed": float(obs), "p50": float(np.percentile(null, 50)), "p95": float(np.percentile(null, 95)), "n_offsets": int(len(null)),
            "p95_se": 0.0, "pct_rank": float((null < obs).mean()), "above_p95": bool(obs > np.percentile(null, 95))}


def rank(x):
    return pd.Series(x).rank().to_numpy(float)


def spearman_rotation(A, g):
    ra, rg = rank(A), rank(g)
    ra = (ra - ra.mean()) / ra.std(); rg = (rg - rg.mean()) / rg.std()
    n = len(A)
    ks = np.concatenate([[0], np.arange(ROT_MIN, n - ROT_MIN + 1)])
    rho = np.array([float(np.mean(np.roll(ra, k) * rg)) for k in ks])
    return rho[0], rho[1:]


def eff(g, mask):
    x = g[mask]
    return float(x.sum() / np.abs(x).sum()) if mask.any() else float("nan")


def mask_rotation(g, take):
    n = len(g)
    ks = np.concatenate([[0], np.arange(ROT_MIN, n - ROT_MIN + 1)])
    return eff(g, take), np.array([eff(g, np.roll(take, k)) for k in ks[1:]])


def book_stats(C, mask, days_all, arm):
    x = C[mask]
    di = np.searchsorted(days_all, x.index.to_numpy())
    fg = Q.four_groups(x["g"].to_numpy(float), x["net"].to_numpy(float), di, x["s"].to_numpy(float), days_all, len(days_all), arm, COST)
    return {"trades": int(mask.sum()), "mean_gross": float(x["g"].mean()), "t_gross_nw": nw_t(x["g"]), "mean_net": float(x["net"].mean()),
            "t_net_nw": nw_t(x["net"]), "median_net": float(x["net"].median()), "win": float((x["net"] > 0).mean()), "four_groups": fg}


# ------------------------------------------------------------------ audits
def lag_audit(C, b, s, sample, log=P):
    """Second implementation: m and I re-derived from the raw rows for every candidate up to each sampled one, then
    sigma60, z, the fit, R and the absorbed flag by plain loops; never calls load/build/walk_forward."""
    bd = {d: dict(zip(zip(g["hhmm"], ["o"] * len(g)), g["open"])) | dict(zip(zip(g["hhmm"], ["c"] * len(g)), g["close"])) for d, g in b[b["hhmm"].isin(BARS)].groupby("day")}
    sd = {d: g for d, g in s.groupby("day")}
    days = list(C.index)
    mm, II = [], []
    for d in days:
        mm.append(math.log(bd[d][("10:29", "c")] / bd[d][("09:30", "o")]))
        g = sd[d]
        II.append((g["buy"].sum() - g["sell"].sum()) / g["volume"].sum())
    mm, II = np.array(mm), np.array(II)
    for i in sample:
        w = mm[max(0, i - N_SIG):i]
        sig = float(np.std(w, ddof=1))
        zi = mm[i] / sig
        zs, Is = [], []
        for j in range(i):
            wj = mm[max(0, j - N_SIG):j]
            if len(wj) >= MIN_SIG:
                zs.append(mm[j] / float(np.std(wj, ddof=1))); Is.append(II[j])
        zs, Is = np.array(zs[-N_FIT:]), np.array(Is[-N_FIT:])
        bb, aa = np.polyfit(zs, Is, 1)
        Ri = math.copysign(1.0, zi) * (II[i] - (aa + bb * zi))
        for name, ref, got in (("m", C["m"].iloc[i], mm[i]), ("I", C["I"].iloc[i], II[i]), ("z", C["z"].iloc[i], zi), ("R", C["R"].iloc[i], Ri)):
            if not math.isclose(ref, got, rel_tol=1e-7, abs_tol=1e-10):
                raise D715Error(f"[LAG] {days[i]}: {name} {ref!r} vs the raw loop's {got!r}")
    log(f"  lag audit: {len(sample)} candidates re-derived from raw rows (m, I, z, R): equal")


def sign_audit():
    for s_, move, want in ((1.0, 2.0, 10.0), (-1.0, -2.0, 10.0), (1.0, -2.0, -10.0)):
        if s_ * move * USD != want:
            raise D715Error("[SIGN] a favourable move does not pay")
    if not math.isclose((10.0 - COST), 5.58):
        raise D715Error("[SIGN] net != gross - $4.42")


# ------------------------------------------------------------------ run
def analyse(C, arm, days_all, rng):
    post_fit = np.isfinite(C["R"].to_numpy(float)) & (C["s"].to_numpy(float) != 0)
    post = post_fit & np.isfinite(C["med"].to_numpy(float))
    A_score = -C["R"].to_numpy(float)
    g = C["g"].to_numpy(float)
    rho, null = spearman_rotation(A_score[post_fit], g[post_fit])
    G1 = blk(rho, null)
    cand = C[post]
    gp = cand["g"].to_numpy(float)
    absorbed = cand["absorbed"].to_numpy(bool); breadth = cand["breadth"].to_numpy(bool)
    Bm, Am, Pm, Brm = absorbed & breadth, absorbed, ~absorbed, breadth
    books = {"B_absorbed_and_breadth": Bm, "A_absorbed": Am, "Pu_pushed": Pm, "Br_breadth": Brm, "E0_every_candidate": np.ones(len(cand), bool),
             "quiet_and_breadth": cand["quiet"].to_numpy(bool) & breadth}
    bs = {k: book_stats(cand, v, days_all, arm) for k, v in books.items()}
    e_obs, e_null = mask_rotation(gp, Bm)
    G2e = blk(e_obs, e_null)
    B = cand[Bm]
    yr = B.index.str[:4]
    by_year = B.groupby(yr)["net"].agg(["count", "sum", "mean"])
    tot = float(B["net"].sum())
    elig = by_year[by_year["count"] >= 10]
    yr_all = cand.index.str[:4]
    mu = cand.groupby(yr_all)["move"].mean()
    T = float((B["s"] * (B["move"] - mu.reindex(yr).to_numpy())).mean())
    gates = {
        "G1_mechanism": {**G1, "n": int(post_fit.sum()), "pass": bool(G1["observed"] > 0 and G1["above_p95"])},
        "G2_edge": {"mean_net": bs["B_absorbed_and_breadth"]["mean_net"], "t_net_nw": bs["B_absorbed_and_breadth"]["t_net_nw"], "efficiency": G2e,
                    "pass": bool(bs["B_absorbed_and_breadth"]["mean_net"] > 0 and bs["B_absorbed_and_breadth"]["t_net_nw"] >= 2.0 and G2e["above_p95"])},
        "G3_ingredients": {"A_gross": bs["A_absorbed"]["mean_gross"], "Pu_gross": bs["Pu_pushed"]["mean_gross"], "B_gross": bs["B_absorbed_and_breadth"]["mean_gross"],
                           "pass": bool(bs["A_absorbed"]["mean_gross"] > bs["Pu_pushed"]["mean_gross"] and bs["B_absorbed_and_breadth"]["mean_gross"] > bs["A_absorbed"]["mean_gross"])},
        "G4_not_one_episode": {"ex_2020_mean_net": float(B.loc[yr != "2020", "net"].mean()), "ex_2022_mean_net": float(B.loc[yr != "2022", "net"].mean()),
                               "largest_year_share": (float(by_year["sum"].max() / tot) if tot > 0 else None), "years_eligible": int(len(elig)),
                               "years_positive": int((elig["sum"] > 0).sum()), "by_year": {k: {"n": int(r["count"]), "net": float(r["sum"])} for k, r in by_year.iterrows()}},
        "G5_beyond_drift": {"T": T, "pass": bool(T > 0)},
    }
    g4 = gates["G4_not_one_episode"]
    g4["pass"] = bool(g4["ex_2020_mean_net"] > 0 and g4["ex_2022_mean_net"] > 0 and tot > 0 and g4["largest_year_share"] <= 0.5 and 2 * g4["years_positive"] >= g4["years_eligible"])
    p = {k: gates[k]["pass"] for k in gates}
    bg = bs["B_absorbed_and_breadth"]
    if all(p.values()):
        reading = "PASS"
    elif not p["G1_mechanism"]:
        reading = "NEITHER"
    elif p["G3_ingredients"] and bg["mean_gross"] > 0 and bg["t_gross_nw"] >= 2.0:
        reading = "MECHANISM ONLY"
    else:
        reading = "FAIL"
    # reported: breadth vs count-matched random deletion of A's trades (D714's check), size-invariant
    netA = cand["net"].to_numpy(float)[Am]
    kB = int(Bm.sum())
    draws = np.array([(lambda x: x.sum() / np.abs(x).sum())(netA[rng.choice(len(netA), kB, replace=False)]) for _ in range(20000)])
    obsB = float(cand["net"][Bm].sum() / np.abs(cand["net"][Bm]).sum())
    del_null = {"observed": obsB, "p50": float(np.median(draws)), "p95": float(np.quantile(draws, 0.95)), "rank": float((draws < obsB).mean()), "draws": 20000}
    # reported: the absorption quintiles over every post-fit candidate
    q = pd.qcut(pd.Series(A_score[post_fit]), 5, labels=False).to_numpy()
    gq = g[post_fit]
    quint = {int(k): {"n": int((q == k).sum()), "mean_gross": float(gq[q == k].mean()), "t": float(gq[q == k].mean() / (gq[q == k].std(ddof=1) / math.sqrt((q == k).sum())))} for k in range(5)}
    f2_share = float(B["g_last30"].sum() / B["g"].sum()) if B["g"].sum() != 0 else None
    ls = {sd: {"n": int((B["s"] == v).sum()), "mean_net": float(B.loc[B["s"] == v, "net"].mean())} for sd, v in (("long", 1.0), ("short", -1.0))}
    pt = pd.qcut(B["entry"].astype(float), 3, labels=False)
    price = {int(k): {"n": int((pt == k).sum()), "mean_net": float(B["net"][pt == k].mean())} for k in range(3)}
    return {"gates": gates, "reading": reading, "books": bs, "breadth_vs_random_deletion": del_null, "absorption_quintiles_gross": quint,
            "share_of_B_gross_earned_15_30_to_16_00": f2_share, "B_long_short": ls, "B_price_tercile": price,
            "counts": {"post_fit": int(post_fit.sum()), "post_median": int(post.sum()), "first_trade_day": str(cand.index[0]) if len(cand) else None,
                       "absorbed_share": float(absorbed.mean()), "breadth_share": float(breadth.mean())}}


def f2_daily(data_root):
    import importlib.util
    def _load(name, fn):
        if name in sys.modules:
            return sys.modules[name]
        sp = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
        m = importlib.util.module_from_spec(sp); sys.modules[name] = m; sp.loader.exec_module(m)
        return m
    m618 = _load("m618", "stage0_d618_sharpened_ladder.py")
    fx = Path(data_root) / "fixtures"
    m618.FIX = fx
    m618.OPTS, m618.CUTS, m618.ES_1M = fx / "fut_es_options_eod.csv.gz", fx / "fut_es_0dte_volume_cutoffs.csv.gz", fx / "fut_ES_rth_1m.csv.gz"
    m618.STRIP, m618.SESSIONS = fx / "fut_settle_strip.csv.gz", fx / "fut_index_sessions.csv.gz"
    m707 = _load("d707r", "vault_d707_last_hour_f2.py")
    X = m707.frame()
    F = m707.f2(X)
    sess = X.index.to_numpy(str)
    net = np.where(F["take"] & F["window"], X["gross"].to_numpy(float) - m707.COST, 0.0)
    ka = m707.in_sample_answer(X, F)
    if ka["trades"] != 252 or abs(ka["mean_net"] - 13.208968253968253) > 1e-9:
        raise D715Error(f"[F2] D707's known answer not reproduced: {ka}")
    return pd.Series(net[F["window"]], index=sess[F["window"]])


def run(data_root: Path, log=P) -> int:
    t0 = time.time()
    sign_audit()
    C, b, s = load(data_root, log)
    C = build(C)
    rng = np.random.default_rng(715)
    post = np.flatnonzero(np.isfinite(C["med"].to_numpy(float)))
    lag_audit(C, b, s, rng.choice(post, 40, replace=False), log)
    import stage0_d688_gamma_close as S688
    arm = S688.d685().load_arm()
    days_all = np.array(sorted(C.index))
    res = analyse(C, arm, days_all, rng)
    # rho with F2 (D707's rebuild, its known answer re-proved)
    f2 = f2_daily(data_root)
    Bm = (C["absorbed"] & C["breadth"] & np.isfinite(C["med"]) & (C["s"] != 0))
    bd = pd.Series(np.where(Bm, C["net"], 0.0), index=C.index)
    common = bd.index.intersection(f2.index)
    res["rho_B_daily_net_with_F2"] = {"rho": float(np.corrcoef(bd[common], f2[common])[0, 1]), "days": int(len(common))}
    res["spec"] = "D715 STAGE 0 (in-sample 2016-2023; one MES; the design record's gates)"
    res["design_commit"] = "582022f6"
    res["timing_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(res, indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x)) + "\n", encoding="utf-8", newline="\n")
    g, bk = res["gates"], res["books"]["B_absorbed_and_breadth"]
    log(f"  G1 rho {g['G1_mechanism']['observed']:+.4f} (p95 {g['G1_mechanism']['p95']:+.4f}, pct {g['G1_mechanism']['pct_rank']:.3f}) -> {g['G1_mechanism']['pass']}")
    log(f"  B: {bk['trades']} trades, gross ${bk['mean_gross']:+.2f} (NW t {bk['t_gross_nw']:+.2f}), net ${bk['mean_net']:+.2f} (t {bk['t_net_nw']:+.2f}); "
        f"eff pct {g['G2_edge']['efficiency']['pct_rank']:.3f}; G3 {g['G3_ingredients']['pass']} G4 {g['G4_not_one_episode']['pass']} G5 {g['G5_beyond_drift']['pass']}")
    log(f"  READING: {res['reading']}  ({res['timing_s']} s)")
    return 0


# ------------------------------------------------------------------ selftest
def selftest() -> int:
    sign_audit()
    rng = np.random.default_rng(7150)
    n = 1400
    m = rng.normal(0, 0.004, n)
    I_base = 0.02 * m / 0.004 + rng.normal(0, 0.05, n)
    wf = walk_forward(m, I_base)
    ok = np.isfinite(wf["R"])
    if not (0.45 < wf["absorbed"][np.isfinite(wf["med"])].mean() < 0.55):
        raise SystemExit("selftest: the absorbed share is not about 0.5")
    # a planted absorption effect: the outcome rises with -R
    g = np.sign(m) * 0 + (-wf["R"]) * 400 + rng.normal(0, 60, n)
    rho, null = spearman_rotation(-wf["R"][ok], g[ok])
    if not blk(rho, null)["above_p95"]:
        raise SystemExit("selftest: a planted absorption effect failed G1")
    fails = 0
    for i in range(40):
        gn = rng.normal(0, 60, n)
        r0, nl = spearman_rotation(-wf["R"][ok], gn[ok])
        fails += not blk(r0, nl)["above_p95"]
    if fails < 33:
        raise SystemExit(f"selftest: noise passed G1 {40 - fails} of 40 times")
    # the leak canary: a fit including the current candidate must differ from the prior-only one
    wl = walk_forward(m, I_base, leak=True)
    if np.allclose(wl["R"][ok], wf["R"][ok], equal_nan=True):
        raise SystemExit("selftest: the leaked fit equals the prior-only fit; the audit could not fire")
    # the rotation's offset 0 is the observed statistic
    take = rng.random(n) < 0.4
    gg = np.nan_to_num(g)
    e0, _ = mask_rotation(gg, take)
    if e0 != eff(gg, take):
        raise SystemExit("selftest: the mask rotation's offset 0 is not the observed efficiency")
    try:
        seal(["2023-12-29", "2024-01-02"], "canary")
    except D715Error:
        pass
    else:
        raise SystemExit("selftest: the seal did not fire on a 2024 row")
    print(f"SELFTEST OK: absorbed share ~0.5; planted effect passes G1; noise failed G1 {fails}/40; the leaked fit differs; the seal fires; "
          "the lag audit (raw-row loop) runs in --run")
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
