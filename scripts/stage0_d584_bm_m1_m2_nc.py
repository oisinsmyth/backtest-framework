"""D584 STAGE 0 -- basis momentum's M1, M2 and the negative control. Design committed BEFORE this file (see SPEC).

    uv run python scripts/stage0_d584_bm_m1_m2_nc.py --selftest   # every audit passes a clean case and RAISES on a break
    uv run python scripts/stage0_d584_bm_m1_m2_nc.py --run        # 2011-07 .. 2023-12-29; no session from 2024-01-01 on

The D564 primary cell rebuilt by D583's build_book and harnessed to D564's artifact to 1e-9; then three mechanism tests,
each with its own verdict: M1 the per-root leg return of the 8 least liquid roots (median front-contract dollar volume)
against the 9 most liquid, against every one of the 24,310 splits; M2 the book's return in the 21 sessions after a
cross-root realised-volatility spike (80th percentile of the trailing 756 sessions), against the state shifted by every
offset within the positioned span; NC the BM signal against the COT commercials' HP and its 12-month change, and the
weekly book return against the signed commercial flow, against declared bars. No cost, no construction, no reserved read.
Output data/stage0_d584_bm_m1_m2_nc.json.
"""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s); sys.modules[name] = m; s.loader.exec_module(m); return m


R83 = _load("d583", "stage0_d583_bm_quarter_end.py"); R64 = R83.R64; R55, R56, R57 = R83.R55, R83.R56, R83.R57
R73 = _load("d573", "run_d573_hedging_pressure.py")
OUT = REPO / "data" / "stage0_d584_bm_m1_m2_nc.json"; ART_D564 = REPO / "data" / "d564_basis_momentum.json"
SPEC = "D584 (design commit 958bf07)"
CM = R64.CM; PRIMARY = R55.PRIMARY; RESERVED_FROM = R55.RESERVED_FROM
N_LOW = 8                                   # the 8 least liquid against the 9 most liquid
VOL_WIN, TRAIL, TRAIL_MIN, Q = 21, 756, 252, 80.0
LAG, LAG_ALT, OVERLAP = (1, 21), (6, 26), 42
PROFILE_BINS = [(1 + 5 * j, 5 + 5 * j) for j in range(13)]   # 1-5 .. 61-65
LOWLIQ_RATIO, LIQ_SHORT, LIQ_LONG = 0.8, 252, 756
N_REPORTS_HP, MIN_PRESENT_HP, HP_LOOKBACK = 4, 3, 12
NC_LOW, NC_HIGH = 0.3, 0.5
MIN_STATE_YEARS, MIN_TREATED_PER_YEAR = 6, 21
BOOT, SEED = 2000, 584
REQUIRED_OUTPUTS = ("spec", "windows", "harness", "audits", "sets", "M1", "M1b", "M2", "NC", "beside", "predictions", "verdicts", "timing_s")
expect_raise = R83.expect_raise; delta = R83.delta


def guard_outputs(res):
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")


def spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float); ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 3:
        return np.nan
    ra = pd.Series(a[ok]).rank().to_numpy(); rb = pd.Series(b[ok]).rank().to_numpy()
    return float(np.corrcoef(ra, rb)[0, 1])


def pearson(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float); ok = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[ok], b[ok])[0, 1]) if ok.sum() >= 3 else np.nan


def year_block_se(values, years, rng, stat=np.nanmean):
    values = np.asarray(values, float); years = np.asarray(years); uy = np.unique(years); out = []
    for _ in range(BOOT):
        pick = rng.choice(uy, uy.size, replace=True); sel = np.concatenate([np.flatnonzero(years == y) for y in pick]); out.append(stat(values[sel]))
    return float(np.nanstd(out))


# ------------------------------------------------------------------------------------------ M1: liquidity
def full_usd_per_point(roots):
    meta = json.loads(R55.META.read_text(encoding="utf-8")); return np.array([meta["specs"][r]["tick_usd_full_contract"] / meta["specs"][r]["tick_price_units"] for r in roots])


def session_dollar_volume(gfull, roots, days):
    """(n, T) front-contract session dollar volume: the fixture's hourly volumes summed x the session close x full-size USD per point."""
    vcols = [s + "_v" for s in R55.SEGS]
    df = pd.read_csv(R55.FIX, usecols=["root", "day"] + vcols, encoding="utf-8"); df = df[df["root"].isin(roots) & (df["day"] < RESERVED_FROM)]
    day_ix = {d: i for i, d in enumerate(days)}; df = df[df["day"].isin(set(day_ix))]
    vol = df[vcols].sum(axis=1, min_count=1).to_numpy(); n, T = len(roots), len(days); V = np.full((n, T), np.nan)
    ri = {r: i for i, r in enumerate(roots)}; ii = df["root"].map(ri).to_numpy(); tt = df["day"].map(day_ix).to_numpy(); V[ii, tt] = vol
    gi = [list(gfull["roots"]).index(r) for r in roots]; close = gfull["close"][gi]; upp = full_usd_per_point(roots)
    return V * close * upp[:, None]


def leg_returns(held, r1d):
    """held x r1d where positioned, NaN elsewhere."""
    return np.where(held != 0, held * r1d, np.nan)


def mu_by_root(C, cols=None):
    X = C if cols is None else C[:, cols]
    return 1e4 * np.nanmean(X, axis=1)


def mu_by_root_pandas(C, roots, days):
    """Second path: a long-format frame of positioned root-days, groupby root."""
    n, T = C.shape; ii, tt = np.nonzero(np.isfinite(C))
    df = pd.DataFrame({"root": np.asarray(roots)[ii], "session": np.asarray(days)[tt], "leg": C[ii, tt]})
    return 1e4 * df.groupby("root")["leg"].mean().reindex(list(roots)).to_numpy()


def audit_mu_second_path(mu_a, mu_b):
    if not np.allclose(mu_a, mu_b, atol=1e-9, equal_nan=True):
        raise AssertionError("LEG-RETURN AUDIT: the numpy and pandas per-root means disagree")


def m1_block(mu, low_ix, n_low=N_LOW):
    """Delta_LIQ = mean mu over the low set - mean over the rest; null = every n_low-subset of the roots."""
    n = mu.size; low = np.zeros(n, bool); low[list(low_ix)] = True
    def d_of(mask):
        return float(mu[mask].mean() - mu[~mask].mean())
    obs = d_of(low); subs = list(itertools.combinations(range(n), n_low)); vals = np.empty(len(subs))
    for j, s in enumerate(subs):
        m = np.zeros(n, bool); m[list(s)] = True; vals[j] = d_of(m)
    obs_j = subs.index(tuple(sorted(low_ix))); others = np.delete(vals, obs_j)
    return {"delta_liq_bp": obs, "rank_in_splits": float((others < obs).mean()), "n_splits": int(len(subs)), "null_p05": float(np.percentile(others, 5)), "null_p50": float(np.percentile(others, 50)), "null_p95": float(np.percentile(others, 95)),
            "observed_split_reproduces": bool(np.isclose(vals[obs_j], obs))}


def audit_split_sets(low_ix, high_ix, n):
    if set(low_ix) & set(high_ix) or set(low_ix) | set(high_ix) != set(range(n)):
        raise AssertionError("RIGHT-QUANTITY AUDIT: the two root sets are not disjoint or do not cover the roots")


def audit_m1_sign(rng, flip=False):
    n, T = 17, 2000; C = rng.normal(0, 1e-3, (n, T)); low = list(range(8)); C[low] += 0.001
    if flip:
        C = -C
    b = m1_block(mu_by_root(C), low)
    if not (b["delta_liq_bp"] > 5 and b["rank_in_splits"] == 1.0):
        raise AssertionError(f"SIGN AUDIT (M1): delta {b['delta_liq_bp']:+.2f} rank {b['rank_in_splits']:.2f} on a grid built to give a positive low-liquidity delta")
    return b["delta_liq_bp"]


# ------------------------------------------------------------------------------------------ M2: the spike state
def vol_series(r1d, live):
    """Cross-root mean of the 21-session realised vol of r1d over the roots live at t, annualised."""
    n, T = r1d.shape; V = np.full((n, T), np.nan)
    for i in range(n):
        s = pd.Series(np.where(live[i], r1d[i], np.nan)); V[i] = s.rolling(VOL_WIN, min_periods=VOL_WIN).std(ddof=1).to_numpy()
    return np.sqrt(252.0) * np.nanmean(np.where(live, V, np.nan), axis=0)


def spike_state(VOL):
    """S_t = VOL_t > the 80th percentile of VOL over the trailing TRAIL sessions ending at t-1 (>= TRAIL_MIN present)."""
    T = VOL.size; S = np.zeros(T, bool)
    for t in range(T):
        w = VOL[max(0, t - TRAIL):t]; w = w[np.isfinite(w)]
        if w.size >= TRAIL_MIN and np.isfinite(VOL[t]):
            S[t] = VOL[t] > np.percentile(w, Q)
    return S


def spike_state_pandas(VOL):
    thr = pd.Series(VOL).rolling(TRAIL, min_periods=TRAIL_MIN).quantile(Q / 100.0).shift(1).to_numpy()
    return np.isfinite(thr) & np.isfinite(VOL) & (VOL > thr)


def audit_state_second_path(a, b):
    if not np.array_equal(a, b):
        raise AssertionError(f"STATE AUDIT: the two paths disagree on {int((a != b).sum())} sessions")


def treated_from(S, lag=LAG):
    """Sessions t with S[t-k] for some k in [lo, hi]; cumsum route."""
    lo, hi = lag; cs = np.r_[0, np.cumsum(S.astype(int))]; T = S.size; t = np.arange(T)
    a = np.clip(t - hi, 0, T); b = np.clip(t - lo + 1, 0, T)
    return (cs[b] - cs[a]) > 0


def treated_loop(S, lag=LAG):
    lo, hi = lag; T = S.size; out = np.zeros(T, bool)
    for k in range(lo, hi + 1):
        out[k:] |= S[:-k] if k < T else False
    return out


def m2_block(x, S, lag=LAG, overlap=OVERLAP):
    """x and S restricted to the positioned span (length V). Null = every circular shift of S."""
    V = x.size; valid = np.ones(V, bool); obs = delta(x, valid, treated_from(S, lag)); vals = np.empty(V)
    for o in range(V):
        vals[o] = delta(x, valid, treated_from(np.roll(S, o), lag))
    others = vals[1:]; offs = np.arange(1, V); non = others[np.minimum(offs, V - offs) > overlap]
    return {"delta_vol_bp": float(obs), "rank_in_shifts": float((others < obs).mean()), "n_shifts": int(others.size), "null_p05": float(np.percentile(others, 5)), "null_p50": float(np.percentile(others, 50)), "null_p95": float(np.percentile(others, 95)),
            "rank_non_overlapping": float((non < obs).mean()), "n_non_overlapping": int(non.size), "n_overlapping_named": int(others.size - non.size), "zero_shift_reproduces": bool(np.isclose(vals[0], obs)),
            "treated_sessions": int(treated_from(S, lag).sum()), "spike_sessions": int(S.sum())}


def block_se(x, treated, rng, blk=63):
    V = x.size; nb = int(np.ceil(V / blk)); starts = np.arange(0, V, blk); out = []
    for _ in range(BOOT):
        pick = rng.choice(starts, nb, replace=True); sel = np.concatenate([np.arange(s, min(s + blk, V)) for s in pick])
        a = x[sel][treated[sel]]; b = x[sel][~treated[sel]]; out.append(1e4 * (a.mean() - b.mean()) if a.size and b.size else np.nan)
    return float(np.nanstd(out))


def spike_entries(S, gap=VOL_WIN):
    cs = np.r_[0, np.cumsum(S.astype(int))]; t = np.arange(S.size); prev = cs[t] - cs[np.clip(t - gap, 0, None)]
    return S & (prev == 0)


def lag_profile(x, S):
    ent = np.flatnonzero(spike_entries(S)); V = x.size; out = []
    for lo, hi in PROFILE_BINS:
        vals = [x[e + lo:e + hi + 1] for e in ent if e + hi < V]; out.append(float(1e4 * np.concatenate(vals).mean()) if vals else np.nan)
    return out, int(ent.size)


def audit_treated_sets(tr, un):
    if (tr & un).any() or not (tr | un).all():
        raise AssertionError("RIGHT-QUANTITY AUDIT: treated and untreated sessions are not disjoint or do not cover the span")


def audit_m2_sign(rng, flip=False):
    V = 1500; S = np.zeros(V, bool); S[rng.choice(np.arange(30, V - 30), 25, replace=False)] = True
    x = rng.normal(0, 1e-5, V); x[treated_from(S)] += 0.001
    if flip:
        x = -x
    b = m2_block(x, S)
    if not (b["delta_vol_bp"] > 5 and b["rank_in_shifts"] == 1.0):
        raise AssertionError(f"SIGN AUDIT (M2): delta {b['delta_vol_bp']:+.2f} rank {b['rank_in_shifts']:.2f} on a series built to give a positive post-spike delta")
    return b["delta_vol_bp"]


# ------------------------------------------------------------------------------------------ NC: the commercials
def audit_hp_second_path(hp, cot, roots, me_days, cells):
    vb = R73.hp_cells_pandas(cot, roots, me_days, cells, N_REPORTS_HP, MIN_PRESENT_HP); va = np.array([hp[i, k] for i, k in cells])
    if not np.allclose(va, vb, atol=1e-12, equal_nan=True):
        raise AssertionError("COT AUDIT: the numpy and pandas HP paths disagree")


def audit_corr_known_answer(v, w):
    """Known answer: rho(v, v) is 1 and rho(v, w) is near 0 for w a permutation of v; the break passes w = v."""
    v = np.asarray(v, float).ravel(); w = np.asarray(w, float).ravel(); ok = np.isfinite(v) & np.isfinite(w); v, w = v[ok], w[ok]
    if abs(spearman(v, v) - 1.0) > 1e-12 or abs(spearman(v, w)) > 0.05:
        raise AssertionError("CORRELATION AUDIT: self is not 1 or the permuted copy is not near 0")


def cross_sectional_rho(BM, Z, elig, ks, min_n=8):
    out = []
    for k in ks:
        ok = elig[:, k] & np.isfinite(BM[:, k]) & np.isfinite(Z[:, k])
        out.append(spearman(BM[ok, k], Z[ok, k]) if ok.sum() >= min_n else np.nan)
    return np.array(out)


def weekly_flow(cot, roots, days, held, x):
    """Per report week: the book's return between consecutive report dates and the signed commercial flow."""
    piv = cot.pivot_table(index="report_date", columns="symbol", values=["long", "short", "open_interest"], aggfunc="first")
    net = (piv["long"] - piv["short"]) / piv["open_interest"]; net = net.reindex(columns=roots); dates = np.asarray(net.index, dtype=str); dnet = net.diff().to_numpy()
    pos = np.searchsorted(days, dates, side="right") - 1                    # last session on or before the report date
    cx = np.r_[0.0, np.cumsum(x)]; rows = []
    for w in range(1, len(dates)):
        if pos[w - 1] < 0 or pos[w] <= pos[w - 1] or pos[w] >= len(days):
            continue
        h = held[:, pos[w]]; on = (h != 0) & np.isfinite(dnet[w])
        if on.sum() < 4:
            continue
        rows.append((str(dates[w]), float(cx[pos[w] + 1] - cx[pos[w - 1] + 1]), float((h[on] * dnet[w][on]).mean()), int(str(dates[w])[:4])))
    return pd.DataFrame(rows, columns=["report_date", "book_ret", "flow", "year"])


def weekly_price_vs_flow(cot, roots, days, r1d, first_session):
    """Diagnostic, unsigned by the book: per root, Pearson of the front's report-week return with the commercials' change in
    net/OI over the same week. The known commercials-against-price relation; it says what a signed-flow correlation inherits."""
    piv = cot.pivot_table(index="report_date", columns="symbol", values=["long", "short", "open_interest"], aggfunc="first")
    net = ((piv["long"] - piv["short"]) / piv["open_interest"]).reindex(columns=roots); dates = np.asarray(net.index, dtype=str); dnet = net.diff().to_numpy()
    pos = np.searchsorted(days, dates, side="right") - 1; cr = np.concatenate([np.zeros((len(roots), 1)), np.cumsum(np.nan_to_num(r1d), axis=1)], axis=1); out = {}
    for i, r in enumerate(roots):
        a, bb = [], []
        for w in range(1, len(dates)):
            if pos[w - 1] < first_session or pos[w] <= pos[w - 1] or pos[w] >= len(days) or not np.isfinite(dnet[w, i]):
                continue
            a.append(cr[i, pos[w] + 1] - cr[i, pos[w - 1] + 1]); bb.append(dnet[w, i])
        out[r] = pearson(a, bb) if len(a) > 50 else np.nan
    return out


def nc_verdict(rhos, ses):
    a = np.abs(np.array(rhos, float)); s = np.array(ses, float)
    if np.any(a >= NC_HIGH):
        return "FAILS"
    if np.all(a < NC_LOW) and np.all(a + 2 * s < NC_LOW):
        return "HOLDS"
    return "UNRESOLVED"


# ------------------------------------------------------------------------------------------ run
def run(log=print):
    t0 = time.time(); rng = np.random.default_rng(SEED); warnings.filterwarnings("ignore", category=RuntimeWarning)   # empty-slice nanmeans on year subsets are guarded below
    log(f"D584 STAGE 0 -- basis momentum's M1, M2 and the negative control; spec {SPEC}; no session from {RESERVED_FROM} on; no cost, no construction")
    days, T, me, b, b0, member_t, gfull = R83.build_book(log); x = b["x"]; wP = R55.window_mask(days, *PRIMARY); n = len(CM)
    art = json.loads(ART_D564.read_text(encoding="utf-8")); ref = art["cells"]["EW High4/Low4"]["gross"]["sharpe"]
    def audit_harness(series):
        s = R55.sharpe(series[wP])
        if abs(s - ref) > 1e-9:
            raise AssertionError(f"HARNESS: rebuilt {s} vs artifact {ref}")
        return s
    sh = audit_harness(x); audits = {"harness_raises": expect_raise(lambda: audit_harness(np.roll(x, 1)), "the series rolled one session", log)}
    harness = {"primary_sharpe_rebuilt": float(sh), "d564_artifact": float(ref), "tolerance": 1e-9}
    log(f"  harness: PRIMARY gross Sharpe {sh:+.6f} = D564 artifact {ref:+.6f}")
    first_session = me[b["first_me"]] + 1; valid = (np.arange(T) >= first_session) & (np.abs(b["held"]).sum(0) > 0); vix = np.flatnonzero(valid)
    yr = np.array([d[:4] for d in days]); years = [str(y) for y in range(2012, 2024)]
    held, r1d = b["held"], b["ns"]["r1d"]
    sets = {"positioned_sessions": int(valid.sum()), "first_positioned_session": str(days[first_session]), "last_session": str(days[-1]), "book_bp_per_day_long": float(1e4 * x[valid].mean()), "book_bp_per_day_primary": float(1e4 * x[valid & wP].mean())}
    # ---- M1 ----
    DV = session_dollar_volume(gfull, CM, days); span_cols = np.flatnonzero(valid)
    liq = np.array([np.nanmedian(np.where(DV[i, span_cols] > 0, DV[i, span_cols], np.nan)) for i in range(n)])
    order = np.argsort(liq); low_ix = [int(i) for i in order[:N_LOW]]; high_ix = [int(i) for i in order[N_LOW:]]
    audit_split_sets(low_ix, high_ix, n); audits["right_quantity_root_sets"] = True
    audits["right_quantity_root_sets_raises"] = expect_raise(lambda: audit_split_sets(low_ix, high_ix[1:], n), "a root left out of both sets", log)
    C = leg_returns(held, r1d); C[:, ~valid] = np.nan; mu = mu_by_root(C); mu_pd = mu_by_root_pandas(C, CM, days); audit_mu_second_path(mu, mu_pd); audits["leg_return_second_path"] = True
    audits["leg_return_audit_raises"] = expect_raise(lambda: audit_mu_second_path(mu, mu_by_root_pandas(np.where(np.roll(held, 1, axis=1) != 0, np.roll(held, 1, axis=1) * r1d, np.nan), CM, days)), "held shifted one session", log)
    audits["m1_sign_in_money_delta_bp"] = audit_m1_sign(rng); audits["m1_sign_audit_raises"] = expect_raise(lambda: audit_m1_sign(rng, True), "a negated grid (M1)", log)
    M1 = m1_block(mu, low_ix)
    if not M1["observed_split_reproduces"]:
        raise AssertionError("split null: the observed split does not reproduce")
    liq_rank = pd.Series(liq).rank().to_numpy(); M1["spearman_mu_vs_liquidity_rank"] = spearman(mu, liq_rank)
    M1["roots"] = {CM[i]: {"median_dollar_volume_usd": float(liq[i]), "liquidity_rank": int(liq_rank[i]), "mu_bp_per_root_day": float(mu[i]), "se_bp": float(1e4 * np.nanstd(C[i]) / np.sqrt(np.isfinite(C[i]).sum())), "positioned_days": int(np.isfinite(C[i]).sum()), "set": "low" if i in low_ix else "high"} for i in order}
    M1["low_set"] = [CM[i] for i in low_ix]; M1["high_set"] = [CM[i] for i in high_ix]
    M1["by_era"] = {}
    for lab, lo, hi in (("2011_2015", "2011", "2015"), ("2016_2023", "2016", "2023")):
        cols = np.flatnonzero(valid & (yr >= lo) & (yr <= hi)); bl = m1_block(mu_by_root(C, cols), low_ix); M1["by_era"][lab] = {k: bl[k] for k in ("delta_liq_bp", "rank_in_splits")}
    M1["by_year"] = {}
    for y in years:
        # a root never held in a year has no leg return that year; the year's delta is over the roots each set does hold (>= 4 a side)
        cols = np.flatnonzero(valid & (yr == y)); m_y = mu_by_root(C, cols); lo_ok = np.isfinite(m_y[low_ix]); hi_ok = np.isfinite(m_y[high_ix])
        if lo_ok.sum() >= 4 and hi_ok.sum() >= 4:
            M1["by_year"][y] = {"delta_liq_bp": float(np.nanmean(m_y[low_ix]) - np.nanmean(m_y[high_ix])), "roots_low": int(lo_ok.sum()), "roots_high": int(hi_ok.sum())}
    M1["years_positive"] = int(sum(v["delta_liq_bp"] > 0 for v in M1["by_year"].values())); M1["years_counted"] = len(M1["by_year"])
    t_lo, t_hi = [int(i) for i in order[:6]], [int(i) for i in order[-6:]]; M1["terciles_delta_bp"] = float(mu[t_lo].mean() - mu[t_hi].mean())
    log("  M1 liquidity (median $/session, mu bp/root-day): " + " ".join(f"{CM[i]}:{liq[i] / 1e6:.0f}M/{mu[i]:+.1f}" for i in order))
    log(f"  M1: dLIQ {M1['delta_liq_bp']:+.2f} bp/root-day (low {M1['low_set']}), rank {M1['rank_in_splits']:.3f} in {M1['n_splits']} splits (p05 {M1['null_p05']:+.2f} p50 {M1['null_p50']:+.2f} p95 {M1['null_p95']:+.2f}); "
        f"spearman(mu, liquidity rank) {M1['spearman_mu_vs_liquidity_rank']:+.3f}; years positive {M1['years_positive']}/{M1['years_counted']}; eras " + " | ".join(f"{k}: {v['delta_liq_bp']:+.2f} rank {v['rank_in_splits']:.2f}" for k, v in M1["by_era"].items()) + f"; terciles {M1['terciles_delta_bp']:+.2f}")
    # ---- M1b: the root's own low-liquidity state, by month ----
    K = me.size; ks = np.arange(b["first_me"], K - 1); state = np.zeros((n, K), bool); cm = np.full((n, K), np.nan)
    for i in range(n):
        s = pd.Series(np.where(DV[i] > 0, DV[i], np.nan)); short = s.rolling(LIQ_SHORT, min_periods=LIQ_SHORT // 2).median().to_numpy(); long_ = s.rolling(LIQ_LONG, min_periods=LIQ_SHORT).median().to_numpy()
        for k in ks:
            t_ = me[k]; state[i, k] = np.isfinite(short[t_]) and np.isfinite(long_[t_]) and short[t_] < LOWLIQ_RATIO * long_[t_]
            seg = C[i, me[k] + 1:me[k + 1] + 1]; cm[i, k] = 1e4 * np.nanmean(seg) if np.isfinite(seg).any() else np.nan
    def m1b_delta(st):
        a = cm[st & np.isfinite(cm)]; bb = cm[~st & np.isfinite(cm)]; return float(a.mean() - bb.mean()) if a.size and bb.size else np.nan
    obs1b = m1b_delta(state); shifts = np.arange(12, K - 12); null1b = np.array([m1b_delta(np.roll(state, int(k), axis=1)) for k in shifts])
    M1b = {"delta_bp_per_root_day": obs1b, "rank_in_shifts": float((null1b < obs1b).mean()), "n_shifts": int(shifts.size), "null_p50": float(np.nanpercentile(null1b, 50)), "null_p95": float(np.nanpercentile(null1b, 95)), "low_state_root_months": int((state & np.isfinite(cm)).sum()), "root_months": int(np.isfinite(cm).sum())}
    log(f"  M1b: root's own low-liquidity months {M1b['delta_bp_per_root_day']:+.2f} bp/root-day on {M1b['low_state_root_months']} of {M1b['root_months']} root-months, rank {M1b['rank_in_shifts']:.3f} in {M1b['n_shifts']} month shifts")
    # ---- M2 ----
    VOL = vol_series(r1d, b["ns"]["live"]); S = spike_state(VOL); S_pd = spike_state_pandas(VOL); audit_state_second_path(S, S_pd); audits["state_second_path"] = True
    audits["state_audit_raises"] = expect_raise(lambda: audit_state_second_path(np.roll(S, 1), S_pd), "the state shifted one session", log)
    Sv = S[vix]; xv = x[vix]
    if not np.array_equal(treated_from(Sv), treated_loop(Sv)):
        raise AssertionError("treated mask: cumsum and loop routes disagree")
    tr = treated_from(Sv); audit_treated_sets(tr, ~tr); audits["right_quantity_treated"] = True; audits["right_quantity_treated_raises"] = expect_raise(lambda: audit_treated_sets(tr, tr), "the same mask twice", log)
    audits["m2_sign_in_money_delta_bp"] = audit_m2_sign(rng); audits["m2_sign_audit_raises"] = expect_raise(lambda: audit_m2_sign(rng, True), "a negated series (M2)", log)
    M2 = m2_block(xv, Sv)
    if not M2["zero_shift_reproduces"]:
        raise AssertionError("shift null: the zero shift does not reproduce")
    M2["se_block63"] = block_se(xv, tr, rng); M2["t"] = M2["delta_vol_bp"] / M2["se_block63"] if M2["se_block63"] else None
    prof, n_ent = lag_profile(xv, Sv); M2["lag_profile_bp"] = {f"{lo}-{hi}": v for (lo, hi), v in zip(PROFILE_BINS, prof)}; M2["spike_entries"] = n_ent
    pk = int(np.nanargmax(prof)); M2["profile_peak_bin"] = f"{PROFILE_BINS[pk][0]}-{PROFILE_BINS[pk][1]}"; M2["peak_inside_lag"] = bool(PROFILE_BINS[pk][1] <= LAG[1])
    yv = yr[vix]; M2["by_year"] = {}; M2["spike_sessions_by_year"] = {}
    for y in years:
        m = yv == y; M2["spike_sessions_by_year"][y] = int(Sv[m].sum())
        if (tr & m).sum() >= MIN_TREATED_PER_YEAR and (~tr & m).sum() > 0:
            M2["by_year"][y] = {"delta_vol_bp": float(delta(xv, m, tr)), "treated": int((tr & m).sum())}
    M2["years_with_state"] = len(M2["by_year"]); M2["years_positive"] = int(sum(v["delta_vol_bp"] > 0 for v in M2["by_year"].values()))
    M2["by_era"] = {}
    for lab, lo, hi in (("2011_2015", "2011", "2015"), ("2016_2023", "2016", "2023")):
        m = (yv >= lo) & (yv <= hi); bl = m2_block(xv[m], Sv[m]); M2["by_era"][lab] = {k: bl[k] for k in ("delta_vol_bp", "rank_in_shifts", "rank_non_overlapping", "treated_sessions")}
    M2["lag_6_26"] = {k: v for k, v in m2_block(xv, Sv, LAG_ALT).items() if k in ("delta_vol_bp", "rank_in_shifts", "rank_non_overlapping")}
    log(f"  M2: {M2['spike_sessions']} spike sessions ({n_ent} entries), {M2['treated_sessions']} treated; dVOL {M2['delta_vol_bp']:+.2f} bp/day (SE {M2['se_block63']:.2f}), rank {M2['rank_in_shifts']:.3f} in {M2['n_shifts']} shifts (p05 {M2['null_p05']:+.2f} p50 {M2['null_p50']:+.2f} p95 {M2['null_p95']:+.2f}), "
        f"non-overlapping rank {M2['rank_non_overlapping']:.3f}; profile peak {M2['profile_peak_bin']}; years with state {M2['years_with_state']}, positive {M2['years_positive']}; eras " + " | ".join(f"{k}: {v['delta_vol_bp']:+.2f} rank {v['rank_in_shifts']:.2f}" for k, v in M2["by_era"].items()) + f"; lag 6-26 {M2['lag_6_26']['delta_vol_bp']:+.2f} rank {M2['lag_6_26']['rank_in_shifts']:.2f}")
    log("    spikes by year: " + " ".join(f"{y}:{v}" for y, v in M2["spike_sessions_by_year"].items()) + "; profile " + " ".join(f"{k}:{v:+.1f}" for k, v in M2["lag_profile_bp"].items()))
    # ---- NC ----
    roots16 = [r for r in CM if r != "BZ"]; cot = R73.load_cot(roots16)
    if (cot["release_date_nominal"] >= RESERVED_FROM).any() or (cot["report_date"] >= RESERVED_FROM).any():
        raise AssertionError("COT: a reserved-slice row survived the loader")
    me_days = [str(days[i]) for i in me]; hp = R73.hp_at_month_ends(cot, roots16, me_days, N_REPORTS_HP, MIN_PRESENT_HP)
    cells = [(int(i), int(k)) for i, k in zip(rng.integers(0, len(roots16), 50), rng.integers(b["first_me"], K, 50))]; audit_hp_second_path(hp, cot, roots16, me_days, cells); audits["cot_second_path_cells"] = 50
    audits["cot_audit_raises"] = expect_raise(lambda: audit_hp_second_path(np.roll(hp, 1, axis=1), cot, roots16, me_days, cells), "HP shifted one month-end", log)
    hpf = hp[np.isfinite(hp)]; audit_corr_known_answer(hpf, rng.permutation(hpf)); audits["corr_known_answer"] = True; audits["corr_audit_raises"] = expect_raise(lambda: audit_corr_known_answer(hpf, hpf), "the copy not permuted", log)
    dhp = np.full_like(hp, np.nan); dhp[:, HP_LOOKBACK:] = hp[:, HP_LOOKBACK:] - hp[:, :-HP_LOOKBACK]
    i16 = [CM.index(r) for r in roots16]; BM16, elig16 = b["BM"][i16], b["elig"][i16]; ks_nc = np.arange(b["first_me"], K); yks = np.array([int(me_days[k][:4]) for k in ks_nc])
    r_hp = cross_sectional_rho(BM16, hp, elig16, ks_nc); r_dhp = cross_sectional_rho(BM16, dhp, elig16, ks_nc)
    NC = {"roots": roots16, "excluded_no_cot": ["BZ"], "n_month_ends": int(ks_nc.size), "hp_reports": N_REPORTS_HP,
          "NC1_bm_vs_hp": {"mean_cs_spearman": float(np.nanmean(r_hp)), "se_year_block": year_block_se(r_hp, yks, rng), "n": int(np.isfinite(r_hp).sum()), "mean_ts_spearman": float(np.nanmean([spearman(BM16[i, ks_nc], hp[i, ks_nc]) for i in range(len(roots16))]))},
          "NC1_bm_vs_dhp12": {"mean_cs_spearman": float(np.nanmean(r_dhp)), "se_year_block": year_block_se(r_dhp, yks, rng), "n": int(np.isfinite(r_dhp).sum()), "mean_ts_spearman": float(np.nanmean([spearman(BM16[i, ks_nc], dhp[i, ks_nc]) for i in range(len(roots16))]))}}
    wk = weekly_flow(cot, roots16, days, held[i16], x); wk = wk[wk["report_date"] >= str(days[first_session])].reset_index(drop=True)
    def wk_stats(ret, flow, yrs_):
        ok = np.isfinite(ret) & np.isfinite(flow); p = pearson(ret[ok], flow[ok]); s = spearman(ret[ok], flow[ok])
        def stat_p(idx):
            return pearson(ret[idx], flow[idx])
        uy = np.unique(yrs_[ok]); bt = []
        for _ in range(BOOT):
            pick = rng.choice(uy, uy.size, replace=True); sel = np.concatenate([np.flatnonzero((yrs_ == y) & ok) for y in pick]); bt.append(stat_p(sel))
        return {"pearson": p, "spearman": s, "se_year_block": float(np.nanstd(bt)), "n_weeks": int(ok.sum())}
    ret, flow, wy = wk["book_ret"].to_numpy(), wk["flow"].to_numpy(), wk["year"].to_numpy()
    NC["NC2_same_week"] = wk_stats(ret, flow, wy); NC["NC2_prior_week_flow"] = wk_stats(ret[1:], flow[:-1], wy[1:])
    NC["by_era"] = {}
    for lab, lo, hi in (("2011_2015", 2011, 2015), ("2016_2023", 2016, 2023)):
        m = (yks >= lo) & (yks <= hi); mw = (wy >= lo) & (wy <= hi)
        NC["by_era"][lab] = {"NC1_hp": float(np.nanmean(r_hp[m])), "NC1_dhp12": float(np.nanmean(r_dhp[m])), "NC2_pearson": pearson(ret[mw], flow[mw])}
    rhos = [NC["NC1_bm_vs_hp"]["mean_cs_spearman"], NC["NC1_bm_vs_dhp12"]["mean_cs_spearman"], NC["NC2_same_week"]["pearson"], NC["NC2_same_week"]["spearman"], NC["NC2_prior_week_flow"]["pearson"], NC["NC2_prior_week_flow"]["spearman"]]
    ses = [NC["NC1_bm_vs_hp"]["se_year_block"], NC["NC1_bm_vs_dhp12"]["se_year_block"], NC["NC2_same_week"]["se_year_block"], NC["NC2_same_week"]["se_year_block"], NC["NC2_prior_week_flow"]["se_year_block"], NC["NC2_prior_week_flow"]["se_year_block"]]
    NC["max_abs_rho"] = float(np.nanmax(np.abs(rhos))); NC["verdict"] = nc_verdict(rhos, ses)
    log(f"  NC: BM vs HP cs-spearman {rhos[0]:+.3f} (SE {ses[0]:.3f}), vs dHP12 {rhos[1]:+.3f} (SE {ses[1]:.3f}); weekly book vs commercial flow pearson {rhos[2]:+.3f} spearman {rhos[3]:+.3f} (SE {ses[2]:.3f}, {NC['NC2_same_week']['n_weeks']} weeks), prior-week flow {rhos[4]:+.3f}/{rhos[5]:+.3f}; max |rho| {NC['max_abs_rho']:.3f} -> {NC['verdict']}")
    # ---- beside ----
    b0x, b0h = b0["x"], b0["held"]; v0 = (np.arange(T) >= first_session) & (np.abs(b0h).sum(0) > 0); vix0 = np.flatnonzero(v0)
    held_t = R55.hold_from_month_ends(member_t.astype(float), me, T, np.abs(held).sum(0)[None, :].repeat(n, 0) > 0); xt = R55.book_return(held_t, r1d); vt = valid & (np.abs(held_t).sum(0) > 0); vixt = np.flatnonzero(vt)
    mon_ret = np.array([1e4 * x[me[k] + 1:me[k + 1] + 1].sum() for k in ks]); mon_vol = np.array([VOL[me[k]] for k in ks]); ymon = np.array([int(days[me[k]][:4]) for k in ks])
    xs = np.sort(1e4 * xv[tr]); trm = int(0.01 * xs.size)
    beside = {"m2_as_preregistered_ffill1": {k: v for k, v in m2_block(b0x[vix0], S[vix0]).items() if k in ("delta_vol_bp", "rank_in_shifts", "rank_non_overlapping")},
              "m2_terciles_cell": {k: v for k, v in m2_block(xt[vixt], S[vixt]).items() if k in ("delta_vol_bp", "rank_in_shifts", "rank_non_overlapping")},
              "contemporaneous_spearman_r_vs_vol": spearman(xv, VOL[vix]), "monthly_spearman_ret_vs_prior_month_vol": spearman(mon_ret, mon_vol), "monthly_se_year_block": year_block_se(np.arange(mon_ret.size), ymon, rng, stat=lambda idx: spearman(mon_ret[idx.astype(int)], mon_vol[idx.astype(int)])),
              "treated_mean_bp": float(xs.mean()), "treated_median_bp": float(np.median(xs)), "treated_trimmed_bp": float(xs[trm:xs.size - trm].mean()), "untreated_mean_bp": float(1e4 * xv[~tr].mean()),
              "vol_series": {"median_ann": float(np.nanmedian(VOL[vix])), "p80_ann": float(np.nanpercentile(VOL[vix], 80)), "max_ann": float(np.nanmax(VOL[vix])), "max_session": str(days[vix[int(np.nanargmax(VOL[vix]))]])}}
    pvf = weekly_price_vs_flow(cot, roots16, days, r1d[i16], first_session); beside["weekly_root_return_vs_commercial_flow"] = {"by_root": pvf, "mean": float(np.nanmean(list(pvf.values()))), "roots_negative": int(sum(v < 0 for v in pvf.values() if np.isfinite(v)))}
    log(f"  beside: commercials against price -- weekly root return vs d(net/OI), mean pearson {beside['weekly_root_return_vs_commercial_flow']['mean']:+.3f}, negative on {beside['weekly_root_return_vs_commercial_flow']['roots_negative']} of 16 roots")
    log(f"  beside: ffill=1 dVOL {beside['m2_as_preregistered_ffill1']['delta_vol_bp']:+.2f} rank {beside['m2_as_preregistered_ffill1']['rank_in_shifts']:.2f}; terciles {beside['m2_terciles_cell']['delta_vol_bp']:+.2f} rank {beside['m2_terciles_cell']['rank_in_shifts']:.2f}; "
        f"contemporaneous spearman(r, VOL) {beside['contemporaneous_spearman_r_vs_vol']:+.3f}; monthly spearman(ret, prior VOL) {beside['monthly_spearman_ret_vs_prior_month_vol']:+.3f} (SE {beside['monthly_se_year_block']:.3f}); treated mean {beside['treated_mean_bp']:+.2f} median {beside['treated_median_bp']:+.2f} trimmed {beside['treated_trimmed_bp']:+.2f} vs untreated {beside['untreated_mean_bp']:+.2f}")
    # ---- predictions and the three verdicts ----
    preds = {"M1_delta_positive_rank_ge_0.95": bool(M1["delta_liq_bp"] > 0 and M1["rank_in_splits"] >= 0.95), "M1_spearman_negative": bool(M1["spearman_mu_vs_liquidity_rank"] < 0),
             "M2_state_in_ge_6_of_12_years": bool(M2["years_with_state"] >= MIN_STATE_YEARS), "M2_delta_positive_rank_ge_0.95": bool(M2["delta_vol_bp"] > 0 and M2["rank_in_shifts"] >= 0.95), "M2_peak_inside_1_21": M2["peak_inside_lag"],
             "M2_year_share_ge_two_thirds": bool(M2["years_with_state"] > 0 and M2["years_positive"] / M2["years_with_state"] >= 2 / 3), "M2_post2016_not_weaker": bool(M2["by_era"]["2016_2023"]["delta_vol_bp"] >= M2["by_era"]["2011_2015"]["delta_vol_bp"]),
             "NC_all_abs_rho_below_0.3": bool(NC["max_abs_rho"] < NC_LOW), "NC_any_abs_rho_ge_0.5": bool(NC["max_abs_rho"] >= NC_HIGH)}
    v_m1 = "SUPPORTED" if preds["M1_delta_positive_rank_ge_0.95"] else "NOT SUPPORTED"
    if not preds["M2_state_in_ge_6_of_12_years"]:
        v_m2 = "UNRESOLVED"
    elif preds["M2_delta_positive_rank_ge_0.95"]:
        v_m2 = "SUPPORTED" if preds["M2_year_share_ge_two_thirds"] else "PARTIAL"
    else:
        v_m2 = "NOT SUPPORTED"
    verdicts = {"M1": v_m1, "M2": v_m2, "NC": NC["verdict"]}
    log("  predictions: " + "; ".join(f"{k} {v}" for k, v in preds.items())); log(f"  STAGE 0 VERDICTS: M1 {v_m1}; M2 {v_m2}; NC {NC['verdict']}")
    res = {"spec": SPEC, "windows": {"long": [str(days[first_session]), str(days[-1])], "primary": list(PRIMARY), "reserved_from": RESERVED_FROM}, "harness": harness, "audits": audits, "sets": sets, "M1": M1, "M1b": M1b, "M2": M2, "NC": NC, "beside": beside,
           "predictions": preds, "verdicts": verdicts, "timing_s": round(time.time() - t0, 1),
           "construction": {"cell": "EW High4/Low4, FFILL_FORMATION 5 (D564 primary as D574 carried it)", "n_low": N_LOW, "vol_window": VOL_WIN, "trail": TRAIL, "trail_min": TRAIL_MIN, "quantile": Q, "lag": LAG, "lag_alt": LAG_ALT, "overlap": OVERLAP, "hp_reports": N_REPORTS_HP, "nc_bars": [NC_LOW, NC_HIGH], "boot": BOOT}}
    guard_outputs(res); audits["required_outputs_guard_raises"] = expect_raise(lambda: guard_outputs({k: v for k, v in res.items() if k != "M2"}), "a missing declared output", log)
    OUT.write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8"); log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']} s")
    return res


def selftest(log=print) -> int:
    rng = np.random.default_rng(1)
    log(f"  M1 sign in money: dLIQ {audit_m1_sign(rng):+.1f} bp on a synthetic grid"); expect_raise(lambda: audit_m1_sign(rng, True), "a negated grid (M1)", log)
    expect_raise(lambda: audit_split_sets([0, 1], [1, 2], 3), "overlapping root sets", log)
    C = rng.normal(0, 1e-3, (5, 300)); C[rng.random((5, 300)) < 0.3] = np.nan; roots = list("ABCDE"); days = np.array([f"d{i}" for i in range(300)])
    audit_mu_second_path(mu_by_root(C), mu_by_root_pandas(C, roots, days)); log("  leg return: numpy and pandas paths agree on a synthetic grid")
    # a roll along time leaves every per-root mean unchanged (the first draft's break could never fire); the roots rotated one place hits what the assertion reads
    expect_raise(lambda: audit_mu_second_path(mu_by_root(C), mu_by_root_pandas(np.roll(C, 1, axis=0), roots, days)), "the roots rotated one place", log)
    VOL = np.abs(rng.normal(0.2, 0.05, 2000)) + 0.1 * (np.arange(2000) > 1500); VOL[:30] = np.nan; S = spike_state(VOL); audit_state_second_path(S, spike_state_pandas(VOL)); log(f"  spike state: two paths agree, {int(S.sum())} spike sessions of 2000")
    expect_raise(lambda: audit_state_second_path(np.roll(S, 1), spike_state_pandas(VOL)), "the state shifted one session", log)
    if not np.array_equal(treated_from(S), treated_loop(S)):
        raise AssertionError("treated mask: cumsum and loop routes disagree")
    log("  treated mask: cumsum and loop routes agree"); tr = treated_from(S); audit_treated_sets(tr, ~tr); expect_raise(lambda: audit_treated_sets(tr, tr), "the same mask twice", log)
    log(f"  M2 sign in money: dVOL {audit_m2_sign(rng):+.1f} bp on a synthetic series"); expect_raise(lambda: audit_m2_sign(rng, True), "a negated series (M2)", log)
    v = rng.normal(size=3000); audit_corr_known_answer(v, rng.permutation(v)); log("  correlation known answer: self 1, permutation near 0"); expect_raise(lambda: audit_corr_known_answer(v, v), "the copy not permuted", log)
    expect_raise(lambda: guard_outputs({"spec": 1}), "missing outputs", log)
    log("  selftest: every audit passes its clean case and raises on its break"); return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--run", action="store_true"); a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.run:
        run()
    else:
        ap.print_help()
