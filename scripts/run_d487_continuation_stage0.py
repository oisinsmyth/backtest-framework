"""D487 stage 0 -- does intraday continuation exist in the calm years? ES and NQ one-minute RTH fixtures (D462), full sessions, 2016-2023;
the 26 fifteen-minute returns per day; variance ratio (S1), half-day continuation (S2), rest-of-day -> last-30 and first-30 -> last-30
slopes (S3), trend-day frequency (S4), next-day reversal (S5); by year, calm/stress, vol tercile. Spec committed in 554d916 BEFORE this
file. 2024+ unread (a gate raises if any row past 2023 reaches the measurement).

Nulls: N-shuffle = within each day, permute the order of the 26 returns (destroys within-day autocorrelation, keeps each day's return
set) -- valid for S2, S3, S4. S1 (the variance ratio) is INVARIANT to a within-day permutation (the day's sum does not change), so its
null is the cross-day shuffle within the group (keeps the group's 15-minute return distribution, breaks all serial dependence; recorded as
the one departure from the spec's wording). N-rotate for S5: exact rotation of the day series.

    uv run python -u scripts/run_d487_continuation_stage0.py --run
    uv run python -u scripts/run_d487_continuation_stage0.py --selftest
"""
from __future__ import annotations
import argparse, json, math, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]; FIX = REPO / "data" / "fixtures"; OUT = REPO / "data" / "d487_continuation_stage0.json"
START, END = "2016-01-04", "2023-12-29"; ROOTS = ("ES", "NQ"); NB = 26; CALM = ("2016", "2017", "2018", "2019", "2023"); STRESS = ("2020", "2022"); N_DRAWS = 1000; SEED = 487
ENDS = [f"{h:02d}:{m:02d}" for h in range(9, 16) for m in (14, 29, 44, 59) if (h, m) >= (9, 44)][:NB]     # 09:44 .. 15:59, 26 bucket ends


def day_matrix(root, lo=START, hi=END):
    b = pd.read_csv(FIX / f"fut_{root}_rth_1m.csv.gz", dtype={"day": str, "hhmm": str, "contract": str}); b = b[(b["day"] >= lo) & (b["day"] <= hi)]
    assert b["day"].max() <= "2023-12-31", "a row past 2023 reached the measurement"
    n = b.groupby("day").size(); full = n[n == 390].index; b = b[b["day"].isin(full)]
    c = b.pivot(index="day", columns="hhmm", values="close"); o = b[b["hhmm"] == "09:30"].set_index("day")["open"]; hi_ = b.groupby("day")["high"].max(); lo_ = b.groupby("day")["low"].min()
    C = c[ENDS].to_numpy(); O = o.reindex(c.index).to_numpy(); prev = np.column_stack([O, C[:, :-1]]); X = (C / prev - 1) * 1e4
    return pd.Index(c.index), X, ((hi_.reindex(c.index) - lo_.reindex(c.index)) / o.reindex(c.index) * 1e4).to_numpy()


# ------------------------------------------------------------------------------------------ statistics on a matrix of days x 26
def vr(X):
    R = X.sum(axis=1); return float(R.var(ddof=1) / (NB * X.var(ddof=1)))


def half_corr(X):
    a = X[:, :13].sum(axis=1); b = X[:, 13:].sum(axis=1); return float(np.corrcoef(a, b)[0, 1])


def slopes(X):
    f = X[:, :2].sum(axis=1); l = X[:, 24:].sum(axis=1); m = X[:, :24].sum(axis=1)
    def sl(x, y):
        x = x - x.mean(); y = y - y.mean(); b = float((x * y).sum() / (x * x).sum()); res = y - b * x; se = float(math.sqrt((res * res).sum() / (len(x) - 2) / (x * x).sum())); return b, se
    return sl(m, l), sl(f, l)


def trend_day(X):
    cs = np.cumsum(X, axis=1); path = np.column_stack([np.zeros(len(X)), cs]); rng_ = path.max(axis=1) - path.min(axis=1); ratio = np.abs(cs[:, -1]) / np.where(rng_ > 0, rng_, np.nan)
    return float(np.nanmean(ratio > 0.5)), float(np.nanmean(ratio))


def stats(X):
    (b_m, se_m), (b_f, se_f) = slopes(X); F, mr = trend_day(X)
    return dict(n=int(len(X)), S1_vr=vr(X), S2_half=half_corr(X), S3_rest_last=b_m, S3_rest_last_se=se_m, S3_first_last=b_f, S3_first_last_se=se_f, S4_trend_share=F, S4_mean_ratio=mr)


def shuffle_within(X, rng):
    keys = rng.random(X.shape); idx = np.argsort(keys, axis=1); return np.take_along_axis(X, idx, axis=1)


def shuffle_across(X, rng):
    flat = X.ravel().copy(); rng.shuffle(flat); return flat.reshape(X.shape)


def p95_se(x, n_boot=300, seed=5):
    r = np.random.default_rng(seed); return float(np.std([np.quantile(r.choice(x, x.size), .95) for _ in range(n_boot)], ddof=1))


def shuffle_scaled(X, rng):
    """N-x, the PRIMARY null for S1-S4: standardise each day by its own sigma, shuffle the standardised returns across every day and
    bucket in the group, rescale each day by its sigma. Keeps each day's volatility level and the group's return distribution; destroys
    within-day dependence of every kind -- lag-structured (autocorrelation) AND exchangeable (a day-common drift, which is what a trend
    day is). The within-day permutation (N-w) cannot see the exchangeable kind: a day-common component is invariant to the order of the
    buckets (proved in the selftest), so N-w is kept only as the order-only secondary."""
    s = X.std(axis=1, ddof=1, keepdims=True); s = np.where(s > 0, s, 1.0); Z = (X / s).ravel().copy(); rng.shuffle(Z); return Z.reshape(X.shape) * s


KEYS = ("S1_vr", "S2_half", "S3_rest_last", "S3_first_last", "S4_trend_share")


def _stat_vec(W):
    (bm, _), (bf, _) = slopes(W); return vr(W), half_corr(W), bm, bf, trend_day(W)[0]


def null_stats(X, rng, n=N_DRAWS):
    x = {k: np.empty(n) for k in KEYS}; w = {k: np.empty(n) for k in KEYS}
    for d in range(n):
        for k, v in zip(KEYS, _stat_vec(shuffle_scaled(X, rng))):
            x[k][d] = v
        for k, v in zip(KEYS, _stat_vec(shuffle_within(X, rng))):
            w[k][d] = v
    q = lambda v: dict(p50=float(np.median(v)), p95=float(np.quantile(v, .95)), p05=float(np.quantile(v, .05)), p99=float(np.quantile(v, .99)), p01=float(np.quantile(v, .01)), p95_se=p95_se(v))
    return {k: dict(**q(x[k]), within=q(w[k])) for k in KEYS}


def s5(R, rng_exact=True):
    a, b = R[:-1], R[1:]; c = float(np.corrcoef(a, b)[0, 1]); top = np.abs(a) >= np.quantile(np.abs(a), .9); x = np.sign(a[top]) * b[top]; m = float(x.mean()); se = float(x.std(ddof=1) / math.sqrt(x.size))
    rot = np.array([float(np.corrcoef(a, np.roll(b, k))[0, 1]) for k in range(2, len(a) - 1)]); rot_top = np.array([float((np.sign(a[top]) * np.roll(b, k)[top]).mean()) for k in range(2, len(a) - 1)])
    return dict(corr_next=c, corr_null_p05=float(np.quantile(rot, .05)), corr_null_p95=float(np.quantile(rot, .95)), after_top_decile_bp=m, after_top_decile_se=se, n_top=int(x.size), top_null_p05=float(np.quantile(rot_top, .05)), top_null_p95=float(np.quantile(rot_top, .95)))


def vol_tercile(R):
    s = pd.Series(R); v = s.rolling(21, min_periods=15).std().shift(1); q33 = v.shift(1).rolling(252, min_periods=200).quantile(1 / 3); q67 = v.shift(1).rolling(252, min_periods=200).quantile(2 / 3)
    return np.where(v.isna() | q33.isna(), np.nan, np.where(v >= q67, 1.0, np.where(v <= q33, -1.0, 0.0)))


# ------------------------------------------------------------------------------------------ run
def flag(obs, nl, k):
    return "*" if obs > nl[k]["p95"] + 2 * nl[k]["p95_se"] else ("u" if obs > nl[k]["p95"] else " ")


def run():
    t0 = time.time(); print("D487 stage 0 -- does intraday continuation exist in the calm years?\n      spec committed in 554d916 BEFORE this ran; ES/NQ 1-min RTH, full sessions, 2016-2023; 2024+ unread\n      PRIMARY null N-x = scaled cross-day shuffle (keeps each day's sigma; destroys lag-structured AND day-common dependence); the spec's within-day permutation N-w is order-only and blind to a day-common drift (selftest) -- reported as [w] beside it\n      * = above N-x p95 + 2 SE, u = above N-x p95 (unresolved)")
    res = {}
    for root in ROOTS:
        days, X, hl = day_matrix(root); R = X.sum(axis=1); yrs = days.str[:4].to_numpy(); vt = vol_tercile(R); rng = np.random.default_rng(SEED); groups = {"pooled": np.ones(len(X), bool), "calm": np.isin(yrs, CALM), "stress": np.isin(yrs, STRESS)}
        for y in sorted(set(yrs)):
            groups[y] = yrs == y
        for lab, v in (("vol_high", 1.0), ("vol_mid", 0.0), ("vol_low", -1.0)):
            groups[lab] = vt == v
        out = {}; print(f"\n{root}: {len(X):,} full sessions\n  {'group':9s} {'n':>5s}  {'S1 VR':>6s} N-x p50/p95      {'S2 half':>8s} N-x p95 [w]       {'S3 rest->last':>14s} (SE)  N-x p95 [w]        {'S3 first->last':>14s} (SE)   {'S4 trend%':>9s} N-x p50/p95 [w p95]")
        for g, m in groups.items():
            if m.sum() < 60:
                continue
            st = stats(X[m]); nl = null_stats(X[m], rng); st["null"] = nl; st["flags"] = {k: flag(st[k], nl, k) for k in KEYS}; out[g] = st
            print(f"  {g:9s} {st['n']:5d}  {st['S1_vr']:6.3f}{st['flags']['S1_vr']} {nl['S1_vr']['p50']:.3f}/{nl['S1_vr']['p95']:.3f}      {st['S2_half']:+8.3f}{st['flags']['S2_half']} {nl['S2_half']['p95']:+.3f} [{nl['S2_half']['within']['p95']:+.3f}]   {st['S3_rest_last']:+14.4f}{st['flags']['S3_rest_last']} ({st['S3_rest_last_se']:.4f}) {nl['S3_rest_last']['p95']:+.4f} [{nl['S3_rest_last']['within']['p95']:+.4f}]   {st['S3_first_last']:+14.4f}{st['flags']['S3_first_last']} ({st['S3_first_last_se']:.4f})   {100*st['S4_trend_share']:8.1f}%{st['flags']['S4_trend_share']} {100*nl['S4_trend_share']['p50']:.1f}/{100*nl['S4_trend_share']['p95']:.1f} [{100*nl['S4_trend_share']['within']['p95']:.1f}]")
        s5p = s5(R); s5c = s5(R[np.isin(yrs, CALM)]); s5s = s5(R[np.isin(yrs, STRESS)])
        print(f"  S5 next-day: pooled corr {s5p['corr_next']:+.3f} (null [{s5p['corr_null_p05']:+.3f},{s5p['corr_null_p95']:+.3f}]); after top-decile |R| days E[sign*R_next] pooled {s5p['after_top_decile_bp']:+.1f} bp ({s5p['after_top_decile_se']:.1f}), calm {s5c['after_top_decile_bp']:+.1f} ({s5c['after_top_decile_se']:.1f}), stress {s5s['after_top_decile_bp']:+.1f} ({s5s['after_top_decile_se']:.1f}); rotation null pooled [{s5p['top_null_p05']:+.1f},{s5p['top_null_p95']:+.1f}]")
        res[root] = dict(sessions=int(len(X)), groups=out, S5=dict(pooled=s5p, calm=s5c, stress=s5s))
    # the decision rule
    def clears(root, g, k):
        st = res[root]["groups"][g]; return st[k] > st["null"][k]["p95"] + 2 * st["null"][k]["p95_se"]
    calm_years_es = {k: sum(clears("ES", y, k) for y in CALM if y in res["ES"]["groups"]) for k in ("S1_vr", "S4_trend_share")}
    proceed = any(clears("ES", "calm", k) and calm_years_es[k] >= 3 and clears("NQ", "calm", k) for k in ("S1_vr", "S4_trend_share"))
    res["decision"] = dict(proceed=proceed, calm_years_clearing_ES=calm_years_es, ES_calm_S1=clears("ES", "calm", "S1_vr"), ES_calm_S4=clears("ES", "calm", "S4_trend_share"), NQ_calm_S1=clears("NQ", "calm", "S1_vr"), NQ_calm_S4=clears("NQ", "calm", "S4_trend_share"))
    print(f"\nDECISION (declared rule: ES S1 or S4 above shuffle p95 + 2 SE pooled over the calm years AND in >= 3 of 5 calm years AND NQ agrees pooled): {'PROCEED' if proceed else 'CLOSE'}   calm years clearing on ES: {calm_years_es}")
    E, N = res["ES"]["groups"], res["NQ"]["groups"]
    print("\nPREDICTIONS")
    print(f"  X-a pooled ES VR 0.90-1.02 inside the null; S2 within +-0.03                        : VR {E['pooled']['S1_vr']:.3f} (null p95 {E['pooled']['null']['S1_vr']['p95']:.3f}); S2 {E['pooled']['S2_half']:+.3f}")
    print(f"  X-b calm years VR <= 1.02 and S4 inside the null every year on ES and NQ; stress VR 1.05-1.20 and S4 above p95 in 2020 and 2022 : ES calm VR " + " ".join(f"{y}:{E[y]['S1_vr']:.3f}{E[y]['flags']['S1_vr']}" for y in CALM if y in E) + "; NQ calm VR " + " ".join(f"{y}:{N[y]['S1_vr']:.3f}{N[y]['flags']['S1_vr']}" for y in CALM if y in N) + "; stress ES " + " ".join(f"{y}:VR {E[y]['S1_vr']:.3f}{E[y]['flags']['S1_vr']} S4 {100*E[y]['S4_trend_share']:.1f}%{E[y]['flags']['S4_trend_share']}" for y in STRESS if y in E))
    print(f"  X-c S3 rest->last30 positive pooled under 2 SE in calm; > 2 SE in 2020                     : calm {E['calm']['S3_rest_last']:+.4f} ({E['calm']['S3_rest_last_se']:.4f}) = {E['calm']['S3_rest_last']/E['calm']['S3_rest_last_se']:+.1f} SE; 2020 {E['2020']['S3_rest_last']:+.4f} ({E['2020']['S3_rest_last_se']:.4f}) = {E['2020']['S3_rest_last']/E['2020']['S3_rest_last_se']:+.1f} SE")
    s = res["ES"]["S5"]; print(f"  X-d S5 corr -0.06..0 pooled; after top-decile days -5..-20 bp in stress, +-5 in calm             : corr {s['pooled']['corr_next']:+.3f}; stress {s['stress']['after_top_decile_bp']:+.1f} ({s['stress']['after_top_decile_se']:.1f}); calm {s['calm']['after_top_decile_bp']:+.1f} ({s['calm']['after_top_decile_se']:.1f})")
    print(f"  X-e vol terciles: VR top > mid > low                                                       : ES {E['vol_high']['S1_vr']:.3f} / {E['vol_mid']['S1_vr']:.3f} / {E['vol_low']['S1_vr']:.3f}; NQ {N['vol_high']['S1_vr']:.3f} / {N['vol_mid']['S1_vr']:.3f} / {N['vol_low']['S1_vr']:.3f}")
    print(f"  X-f decision CLOSE; under 3 min                                                             : {'PROCEED' if proceed else 'CLOSE'}; {(time.time()-t0)/60:.1f} min")
    OUT.write_text(json.dumps(res, indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)}")


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    t0 = time.time(); rng = np.random.default_rng(1); print("== (a) the within-day shuffle keeps each day's return set and the day's sum; the variance ratio is invariant to it; the cross-day shuffle drives VR to 1 on a planted AR(1)")
    n = 1500; e = rng.normal(0, 10, (n, NB)); X = e.copy()
    for j in range(1, NB):
        X[:, j] = 0.25 * X[:, j - 1] + e[:, j]                     # planted within-day continuation
    W = shuffle_within(X, rng); assert np.allclose(np.sort(W, axis=1), np.sort(X, axis=1)) and np.allclose(W.sum(axis=1), X.sum(axis=1)) and abs(vr(W) - vr(X)) < 1e-12
    A = shuffle_across(X, rng); assert vr(X) > 1.3 and abs(vr(A) - 1) < 0.08, (vr(X), vr(A)); print(f"  ok: planted VR {vr(X):.3f}, within-day shuffle leaves it at {vr(W):.3f}, cross-day shuffle gives {vr(A):.3f}")
    print("== (b) a planted trend-day component (a day-common drift) clears N-x on every statistic and is INVISIBLE to the within-day permutation N-w; a planted AR(1) reversal sits below N-x p05 and N-w p05; white noise inside both; N-x keeps each day's sigma")
    X = e + rng.normal(0, 3, (n, 1)); nl = null_stats(X, np.random.default_rng(2), n=200); st = stats(X)
    assert all(st[k] > nl[k]["p95"] for k in KEYS), (st, nl)
    assert nl["S2_half"]["within"]["p05"] <= st["S2_half"] <= nl["S2_half"]["within"]["p95"] and nl["S4_trend_share"]["within"]["p05"] <= st["S4_trend_share"] <= nl["S4_trend_share"]["within"]["p95"], "the day-common plant must sit INSIDE the within-day null"
    Xh = e * rng.lognormal(0, 0.6, (n, 1)); Sx = shuffle_scaled(Xh, np.random.default_rng(9)); assert np.corrcoef(Sx.std(axis=1, ddof=1), Xh.std(axis=1, ddof=1))[0, 1] > 0.9 and abs(Sx.std() / Xh.std() - 1) < 0.05, "N-x keeps each day's scale (heteroskedastic days)"
    Y = e.copy()
    for j in range(1, NB):
        Y[:, j] = -0.25 * Y[:, j - 1] + e[:, j]
    sy = stats(Y); ny = null_stats(Y, np.random.default_rng(3), n=200); assert sy["S4_trend_share"] < ny["S4_trend_share"]["p05"] and sy["S1_vr"] < ny["S1_vr"]["p05"] and sy["S3_rest_last"] < ny["S3_rest_last"]["p05"], (sy, ny)      # N-w conditions on each day's sum, so it is not a yardstick for S4 in the reversal direction
    sz = stats(e); nz = null_stats(e, np.random.default_rng(4), n=200); assert all(nz[k]["p01"] <= sz[k] <= nz[k]["p99"] for k in ("S1_vr", "S4_trend_share", "S2_half")) and nz["S4_trend_share"]["within"]["p01"] <= sz["S4_trend_share"] <= nz["S4_trend_share"]["within"]["p99"], (sz, nz)
    print(f"  ok: trend-day plant VR {st['S1_vr']:.3f} > N-x p95 {nl['S1_vr']['p95']:.3f}, S4 {100*st['S4_trend_share']:.1f}% > {100*nl['S4_trend_share']['p95']:.1f}% but inside N-w [{100*nl['S4_trend_share']['within']['p05']:.1f}, {100*nl['S4_trend_share']['within']['p95']:.1f}]; reversal S4 {100*sy['S4_trend_share']:.1f}% < N-x p05 {100*ny['S4_trend_share']['p05']:.1f}%; noise inside")
    print("== (c) S5 recovers a planted next-day reversal after large days and reads ~0 on noise")
    R = rng.normal(0, 100, 3000); big = np.abs(R) > np.quantile(np.abs(R), .9); R2 = R.copy(); R2[1:] = R2[1:] - 0.3 * np.where(big[:-1], R[:-1], 0.0); s = s5(R2); z = s5(R)
    assert s["after_top_decile_bp"] < s["top_null_p05"] and z["top_null_p05"] <= z["after_top_decile_bp"] <= z["top_null_p95"], (s, z)
    print(f"  ok: planted {s['after_top_decile_bp']:+.1f} bp < null p05 {s['top_null_p05']:+.1f}; noise {z['after_top_decile_bp']:+.1f} inside")
    print("== (d) the day matrix on the real fixture: 26 buckets, the sum equals the open-to-close return to within compounding, no row past 2023")
    days, X, hl = day_matrix("ES", "2016-01-04", "2016-03-31"); assert X.shape[1] == NB and len(days) > 50 and (hl > 0).all() and days.max() < "2016-04-01"
    print(f"  ok: {len(days)} sessions, first {days[0]}, bucket ends {ENDS[0]}..{ENDS[-1]}")
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--run", action="store_true"); g.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    run() if a.run else cmd_selftest()
