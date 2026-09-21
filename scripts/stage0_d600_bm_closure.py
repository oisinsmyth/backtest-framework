"""D600 STAGE 0 -- the basis-momentum closure programme on the 17 commodity roots. Design committed BEFORE this file (see SPEC).

    uv run python scripts/stage0_d600_bm_closure.py --selftest   # every audit passes a clean case and RAISES on a break
    uv run python scripts/stage0_d600_bm_closure.py --run        # 2011-07 .. 2023-12-29; nothing from 2024-01-01 read

Blocks, each with its own verdict: A the maturity-specific BM(2,3) and curvature cells from a third nearby (M3); B the
de-seasonalised signal (section 6.4); C the computable half of the feature evaluation (T3); D the He-Kelly-Manela loading (M4);
E the inventory negative control on the covered roots (M5); F the second-nearby capacity table (item 7). The D564 primary is
rebuilt by D583's build_book and harnessed to D564's artifact to 1e-9 (primary, spreading cell, nine-root diagnostic) before any
new statistic. D564's N1 rotation null (purge 252, exactness guard), N2 family maximum and N3 name-randomised null for every new
cell. No cost, no construction, no closure rule. Output data/stage0_d600_bm_closure.json.
"""
from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import sys
import time
import warnings
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s); sys.modules[name] = m; s.loader.exec_module(m); return m


R83 = _load("d583", "stage0_d583_bm_quarter_end.py"); R64 = R83.R64; R55, R56, R57 = R83.R55, R83.R56, R83.R57; R61 = R64.R61; FB = R56.FB
OUT = REPO / "data" / "stage0_d600_bm_closure.json"; ART_D564 = REPO / "data" / "d564_basis_momentum.json"
FIX = REPO / "data" / "fixtures"; HKM = FIX / "hkm_factors.csv.gz"; EIA = FIX / "eia_weekly_stocks.csv"; NASS = FIX / "nass_stocks.csv"; CV = FIX / "fut_cleared_volume_cm_daily.csv.gz"
SPEC = "D600"
CM = R64.CM; ENERGY = R64.ENERGY; NON_SEASONAL = R64.NON_SEASONAL; LOOKBACK = R64.LOOKBACK; N_LEG, MIN_ELIGIBLE = R64.N_LEG, R64.MIN_ELIGIBLE; FFILL = R64.FFILL_FORMATION
PRIMARY, LONG, RESERVED_FROM = R55.PRIMARY, R55.LONG, R55.RESERVED_FROM
DS_MIN_PRIOR = 3; HORIZONS = (1, 3, 6, 12); BOOT, SEED = 2000, 600; HAC_LAG = 3; TERCILE_WINDOW, TERCILE_MIN = 120, 60; NON_OVERLAP_M = 12
EIA_KNOWN_DAYS = 7; NASS_KNOWN_UTC = "T20:00:00Z"; NC_LOW, NC_HIGH = 0.3, 0.5; SEASON_PRIOR, SEASON_MIN = 5, 3
N3_DRAWS, N3_SEED = 2000, 600; CAP_SPAN = ("2016-01-04", "2023-12-29")
INV_MAP = {"CL": ("eia", "crude_ex_spr"), "BZ": ("eia", "crude_ex_spr"), "HO": ("eia", "distillate"), "RB": ("eia", "gasoline_total"), "NG": ("eia", "natgas_working_l48"),
           "ZC": ("nass", "grain_stocks", "CORN"), "ZS": ("nass", "grain_stocks", "SOYBEANS"), "ZW": ("nass", "grain_stocks", "WHEAT"), "LE": ("nass", "cattle_on_feed", "CATTLE"), "HE": ("nass", "hogs_and_pigs", "HOGS")}
REQUIRED_OUTPUTS = ("spec", "windows", "harness", "audits", "A", "B", "C", "D", "E", "F", "nulls", "predictions", "verdicts", "timing_s")
expect_raise = R83.expect_raise


def guard_outputs(res):
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")


def spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float); ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 3:
        return np.nan
    ra = pd.Series(a[ok]).rank().to_numpy(); rb = pd.Series(b[ok]).rank().to_numpy(); return float(np.corrcoef(ra, rb)[0, 1])


def nw_t(v, lag):
    """Mean / Newey-West SE with Bartlett weights over `lag` lags; returns (mean, se, t, n)."""
    v = np.asarray(v, float); v = v[np.isfinite(v)]; n = v.size
    if n < 8:
        return np.nan, np.nan, np.nan, int(n)
    e = v - v.mean(); s = float((e * e).sum())
    for L in range(1, lag + 1):
        s += 2 * (1 - L / (lag + 1)) * float((e[L:] * e[:-L]).sum())
    se = np.sqrt(s) / n; return float(v.mean()), float(se), float(v.mean() / se) if se > 0 else np.nan, int(n)


def hac_ols(y, x, lag):
    """OLS y = a + b x with Newey-West (Bartlett, `lag`) standard error on b."""
    y = np.asarray(y, float); x = np.asarray(x, float); ok = np.isfinite(y) & np.isfinite(x); y, x = y[ok], x[ok]; n = y.size
    X = np.c_[np.ones(n), x]; beta = np.linalg.lstsq(X, y, rcond=None)[0]; u = y - X @ beta; XtX_inv = np.linalg.inv(X.T @ X)
    S = (X * u[:, None]).T @ (X * u[:, None])
    for L in range(1, lag + 1):
        G = (X[L:] * u[L:, None]).T @ (X[:-L] * u[:-L, None]); S += (1 - L / (lag + 1)) * (G + G.T)
    V = XtX_inv @ S @ XtX_inv; se = float(np.sqrt(V[1, 1])); return float(beta[1]), se, float(beta[1] / se) if se > 0 else np.nan, int(n), float(np.corrcoef(x, y)[0, 1])


def year_block_se(values, years, rng, stat=np.nanmean):
    values = np.asarray(values, float); years = np.asarray(years); uy = np.unique(years); out = []
    for _ in range(BOOT):
        pick = rng.choice(uy, uy.size, replace=True); sel = np.concatenate([np.flatnonzero(years == y) for y in pick]); out.append(stat(values[sel]))
    return float(np.nanstd(out))


# ------------------------------------------------------------------------------------------ the third nearby
def choose_nearby3(A, cols, t, day, energy, ffill):
    y, m = int(day[:4]), int(day[5:7]); thr = y * 12 + m + (3 if energy else 2)
    fin = np.isfinite(R64.formation_settles(A, t, ffill)); cand = np.flatnonzero(fin & (cols >= thr))
    if cand.size == 0:
        return None, None, None
    return int(cand[0]), (int(cand[1]) if cand.size > 1 else None), (int(cand[2]) if cand.size > 2 else None)


def nearby_series3(tables, roots, days, me, ffill):
    """D564's nearby_series extended to a third nearby: R3 / r3d / T3 beside R1, R2, r1d, r2d; `stale` is D564's (T1 or T2),
    `stale3` adds T3. Everything D564 returns must equal D564's function bit for bit (asserted in run)."""
    n, T, K = len(roots), len(days), len(me)
    R = [np.full((n, K), np.nan) for _ in range(3)]; Tc = [np.full((n, K), -1, dtype=int) for _ in range(3)]; rd = [np.zeros((n, T)) for _ in range(3)]
    stale = np.zeros((n, K), dtype=bool); stale3 = np.zeros((n, K), dtype=bool); live = np.zeros((n, T), dtype=bool); basis = np.full((n, K), np.nan)
    for i, r in enumerate(roots):
        A, cols = tables[r]; energy = r in ENERGY; F_prev = None
        for k, t in enumerate(me):
            F = R64.formation_settles(A, t, ffill); js = choose_nearby3(A, cols, t, days[t], energy, ffill)
            if js[0] is None:
                F_prev = F; continue
            for q in range(3):
                Tc[q][i, k] = -1 if js[q] is None else js[q]
            stale[i, k] = R64.is_stale(A, t, js[0]) or R64.is_stale(A, t, js[1]); stale3[i, k] = stale[i, k] or R64.is_stale(A, t, js[2])
            if js[1] is not None:
                basis[i, k] = F[js[1]] / F[js[0]] - 1.0
            if k > 0 and Tc[0][i, k - 1] >= 0 and F_prev is not None:
                for q in range(3):
                    jj = Tc[q][i, k - 1]
                    if jj >= 0:
                        a, b = F_prev[jj], F[jj]; R[q][i, k] = b / a - 1.0 if (np.isfinite(a) and np.isfinite(b) and a > 0) else np.nan
            F_prev = F
            end = me[k + 1] if k + 1 < K else T - 1
            for q in range(3):
                j = js[q]
                if j is None:
                    continue
                prev = F[j]
                for u in range(t + 1, end + 1):
                    v = A[u, j]
                    if np.isfinite(v) and np.isfinite(prev) and prev > 0:
                        rd[q][i, u] = v / prev - 1.0
                    if np.isfinite(v):
                        prev = v
            live[i, t + 1:end + 1] = np.isfinite(F[js[0]])
    return dict(R1=R[0], R2=R[1], R3=R[2], T1=Tc[0], T2=Tc[1], T3=Tc[2], stale=stale, stale3=stale3, r1d=rd[0], r2d=rd[1], r3d=rd[2], live=live, basis=basis)


def signal_pair(Ra, Rb, stale):
    """Pi(1+Ra) - Pi(1+Rb) over the lookback; eligible where all twelve of both are finite and nothing stale."""
    n, K = Ra.shape; S = np.full((n, K), np.nan); elig = np.zeros((n, K), dtype=bool)
    for k in range(LOOKBACK - 1, K):
        wa = Ra[:, k - LOOKBACK + 1:k + 1]; wb = Rb[:, k - LOOKBACK + 1:k + 1]; ok = np.isfinite(wa).all(1) & np.isfinite(wb).all(1) & ~stale[:, k]
        S[ok, k] = np.prod(1.0 + wa[ok], axis=1) - np.prod(1.0 + wb[ok], axis=1); elig[:, k] = ok
    return S, elig


def bm23_pandas(piv, days, me, k, energy, thr_shift=0):
    """Second path for BM(2,3): the audit's own pivot, the 2nd and 3rd candidates, its own monthly returns."""
    ends = [days[m] for m in me]
    def pick(d_):
        y, m = int(d_[:4]), int(d_[5:7]); thr = y * 12 + m + (3 if energy else 2) + thr_shift
        if d_ not in piv.index:
            return None, None
        row = piv.loc[d_].dropna(); c = sorted([d for d in row.index if d >= thr]); return (c[1], c[2]) if len(c) > 2 else (None, None)
    g2 = g3 = 1.0
    for kk in range(k - LOOKBACK + 1, k + 1):
        d0, d1 = ends[kk - 1], ends[kk]; c2, c3 = pick(d0)
        if c2 is None or d1 not in piv.index:
            return None
        a2, b2, a3, b3 = piv.loc[d0, c2], piv.loc[d1, c2], piv.loc[d0, c3], piv.loc[d1, c3]
        if not all(np.isfinite(v) for v in (a2, b2, a3, b3)):
            return None
        g2 *= b2 / a2; g3 *= b3 / a3
    return g2 - g3


def audit_bm23(BM23, elig, strip, days, me, n_check=300, seed=23, thr_shift=0, pivots=None):
    rng = np.random.default_rng(seed); cells = np.argwhere(elig); pick = cells[rng.choice(len(cells), size=min(n_check, len(cells)), replace=False)]; pivots = {} if pivots is None else pivots; checked = 0
    for i, k in pick:
        r = CM[i]
        if r not in pivots:
            pivots[r] = R64.strip_pivot(strip[strip["root"] == r], days, FFILL)
        ref = bm23_pandas(pivots[r], days, me, int(k), r in ENERGY, thr_shift)
        if ref is None or not np.isclose(ref, BM23[i, k], rtol=1e-10, atol=1e-14):
            raise AssertionError(f"BM23 AUDIT: {r} {days[me[k]]}: runner {BM23[i, k]} != strip path {ref}")
        checked += 1
    return checked


# ------------------------------------------------------------------------------------------ de-seasonalisation
def deseasonalise(R1, R2, stale, me_month):
    """d = R1 - R2 per root-month; s = expanding mean of d over PRIOR month-ends of the same calendar month (>= DS_MIN_PRIOR);
    BM_ds = sum over the lookback of (d - s), eligible where all twelve d and s are finite and nothing stale."""
    n, K = R1.shape; d = R1 - R2; s = np.full((n, K), np.nan)
    for i in range(n):
        for k in range(K):
            prior = [d[i, j] for j in range(k) if me_month[j] == me_month[k] and np.isfinite(d[i, j])]
            if len(prior) >= DS_MIN_PRIOR:
                s[i, k] = float(np.mean(prior))
    e = d - s; BM = np.full((n, K), np.nan); elig = np.zeros((n, K), dtype=bool)
    for k in range(LOOKBACK - 1, K):
        w = e[:, k - LOOKBACK + 1:k + 1]; ok = np.isfinite(w).all(1) & ~stale[:, k]; BM[ok, k] = w[ok].sum(1); elig[:, k] = ok
    return BM, elig, s


def seasonal_pandas(d, me_month, shift=1):
    """Second path for s: a frame of d by month-end, groupby calendar month, expanding mean shifted `shift` observations."""
    n, K = d.shape; out = np.full((n, K), np.nan)
    for i in range(n):
        ser = pd.Series(d[i]); grp = ser.groupby(np.asarray(me_month))
        cnt = grp.transform(lambda x: x.notna().cumsum().shift(shift)); mean = grp.transform(lambda x: x.expanding().mean().shift(shift))
        out[i] = np.where(cnt >= DS_MIN_PRIOR, mean, np.nan)
    return out


def audit_seasonal(s_a, s_b):
    if not np.allclose(s_a, s_b, atol=1e-12, equal_nan=True):
        raise AssertionError(f"SEASONAL AUDIT: the numpy and pandas seasonal means disagree on {int((~np.isclose(np.nan_to_num(s_a, nan=-9), np.nan_to_num(s_b, nan=-9), atol=1e-12)).sum())} cells")


# ------------------------------------------------------------------------------------------ T3: the feature evaluation
def forward_returns(R1, h):
    n, K = R1.shape; F = np.full((n, K), np.nan)
    for k in range(K - h):
        w = R1[:, k + 1:k + 1 + h]; ok = np.isfinite(w).all(1); F[ok, k] = np.prod(1.0 + w[ok], axis=1) - 1.0
    return F


def ic_series(S, elig, F, min_n=8):
    n, K = S.shape; ic = np.full(K, np.nan)
    for k in range(K):
        ok = elig[:, k] & np.isfinite(S[:, k]) & np.isfinite(F[:, k])
        if ok.sum() >= min_n:
            ic[k] = spearman(S[ok, k], F[ok, k])
    return ic


def ic_series_pandas(S, elig, F, min_n=8):
    n, K = S.shape; ic = np.full(K, np.nan)
    for k in range(K):
        ok = elig[:, k] & np.isfinite(S[:, k]) & np.isfinite(F[:, k])
        if ok.sum() >= min_n:
            ic[k] = float(pd.DataFrame({"s": S[ok, k], "f": F[ok, k]}).corr(method="spearman").iloc[0, 1])
    return ic


def audit_ic(a, b):
    if not np.allclose(a, b, atol=1e-12, equal_nan=True):
        raise AssertionError("IC AUDIT: the numpy and pandas IC series disagree")


def bucket_means(S, elig, F1):
    """Per month-end: mean next-month return of the Low4, the middle, the High4 (and Low3/High3), and five rank quintiles."""
    n, K = S.shape; rows = []
    for k in range(K):
        ok = elig[:, k] & np.isfinite(S[:, k]) & np.isfinite(F1[:, k])
        if ok.sum() < MIN_ELIGIBLE:
            continue
        idx = np.flatnonzero(ok); order = idx[np.lexsort((np.array(CM)[idx], S[idx, k]))]        # ascending signal, ties by symbol (D564's rule)
        f = F1[order, k]; m = len(order); q = np.array_split(np.arange(m), 5)
        rows.append({"k": k, "low4": f[:4].mean(), "high4": f[-4:].mean(), "mid": f[4:-4].mean(), "low3": f[:3].mean(), "high3": f[-3:].mean(), **{f"q{j + 1}": f[qq].mean() for j, qq in enumerate(q)}})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------ M4: He-Kelly-Manela
def load_hkm():
    with gzip.open(HKM, "rt", encoding="utf-8") as fh:
        df = pd.read_csv(fh, encoding="utf-8")
    m = df[df["freq"] == "M"].copy(); m["period"] = m["period"].astype(int); m = m[m["period"] < int(RESERVED_FROM[:4] + RESERVED_FROM[5:7])]
    return m.set_index("period")


def monthly_book(x, days):
    s = pd.Series(x, index=pd.to_datetime(days)); mb = s.groupby(s.index.to_period("M")).sum(); return {int(p.strftime("%Y%m")): float(v) for p, v in mb.items()}


def audit_loading_sign(rng, flip=False):
    T = 150; f = rng.normal(0, 0.05, T); y = 0.5 * f + rng.normal(0, 0.02, T)
    if flip:
        y = -y
    b, se, t, n, rho = hac_ols(y, f, HAC_LAG)
    if not (b > 0 and t > 2):
        raise AssertionError(f"SIGN AUDIT (M4): beta {b:+.3f} t {t:+.2f} on a synthetic book built to load positively")
    return b, t


def tercile_state(ratio_by_period, periods):
    """At holding month m: the ratio dated m-1 against the terciles of its trailing TERCILE_WINDOW months (>= TERCILE_MIN)."""
    ser = ratio_by_period; keys = sorted(ser.index); vals = np.array([ser[k] for k in keys]); pos = {k: i for i, k in enumerate(keys)}; state = {}
    for m in periods:
        pm = int((pd.Period(str(m), "M") - 1).strftime("%Y%m"))
        if pm not in pos:
            continue
        i = pos[pm]; w = vals[max(0, i - TERCILE_WINDOW + 1):i + 1]
        if w.size < TERCILE_MIN:
            continue
        lo, hi = np.percentile(w, [100 / 3, 200 / 3]); state[m] = -1 if vals[i] <= lo else (1 if vals[i] >= hi else 0)
    return state


def state_delta(y, st):
    a = y[st == -1]; b = y[st == 1]; return float(1e4 * (a.mean() - b.mean())) if a.size and b.size else np.nan


# ------------------------------------------------------------------------------------------ M5: inventories
def load_inventories():
    eia = pd.read_csv(EIA, encoding="utf-8", dtype={"week_ending": str}) if EIA.exists() else None
    nass = pd.read_csv(NASS, encoding="utf-8", dtype={"obs_date": str, "release_datetime_utc": str}) if NASS.exists() else None
    return eia, nass


def eia_state_at(series, me_days):
    """For each month-end day: the latest week known (week_ending + EIA_KNOWN_DAYS <= day), its 52-week log change and log level, both
    de-seasonalised against the trailing SEASON_PRIOR same-week observations (>= SEASON_MIN). Returns arrays and the used rows."""
    s = series.sort_values("week_ending"); we = pd.to_datetime(s["week_ending"]).dt.date.to_numpy(); v = np.log(s["value"].to_numpy(float)); by = {d: i for i, d in enumerate(we)}
    chg = np.full(len(we), np.nan)
    for i, d in enumerate(we):
        j = by.get(d - timedelta(days=364))
        if j is not None:
            chg[i] = v[i] - v[j]
    K = len(me_days); out_c = np.full(K, np.nan); out_l = np.full(K, np.nan); used = []
    for k, day in enumerate(me_days):
        t = date.fromisoformat(day); idx = np.searchsorted(we, t - timedelta(days=EIA_KNOWN_DAYS), side="right") - 1
        if idx < 0:
            continue
        i = idx; prior_c = [chg[by[we[i] - timedelta(days=364 * j)]] for j in range(1, SEASON_PRIOR + 1) if (we[i] - timedelta(days=364 * j)) in by]
        prior_l = [v[by[we[i] - timedelta(days=364 * j)]] for j in range(1, SEASON_PRIOR + 1) if (we[i] - timedelta(days=364 * j)) in by]
        prior_c = [p for p in prior_c if np.isfinite(p)]
        if np.isfinite(chg[i]) and len(prior_c) >= SEASON_MIN:
            out_c[k] = chg[i] - float(np.mean(prior_c))
        if len(prior_l) >= SEASON_MIN:
            out_l[k] = v[i] - float(np.mean(prior_l))
        used.append({"month_end": day, "week_ending": we[i].isoformat()})
    return out_c, out_l, used


def nass_state_at(series, me_days):
    s = series.sort_values("obs_date"); od = pd.to_datetime(s["obs_date"]).dt.date.to_numpy(); rel = s["release_datetime_utc"].to_numpy(); v = np.log(s["value"].to_numpy(float)); by = {d: i for i, d in enumerate(od)}
    chg = np.full(len(od), np.nan)
    for i, d in enumerate(od):
        j = by.get(date(d.year - 1, d.month, d.day))
        if j is not None:
            chg[i] = v[i] - v[j]
    K = len(me_days); out_c = np.full(K, np.nan); out_l = np.full(K, np.nan); used = []
    for k, day in enumerate(me_days):
        cut = day + NASS_KNOWN_UTC; known = [i for i in range(len(od)) if isinstance(rel[i], str) and rel[i] <= cut]
        if not known:
            continue
        i = max(known); d = od[i]
        prior_c = [chg[by[date(d.year - j, d.month, d.day)]] for j in range(1, SEASON_PRIOR + 1) if date(d.year - j, d.month, d.day) in by]; prior_c = [p for p in prior_c if np.isfinite(p)]
        prior_l = [v[by[date(d.year - j, d.month, d.day)]] for j in range(1, SEASON_PRIOR + 1) if date(d.year - j, d.month, d.day) in by]
        if np.isfinite(chg[i]) and len(prior_c) >= SEASON_MIN:
            out_c[k] = chg[i] - float(np.mean(prior_c))
        if len(prior_l) >= SEASON_MIN:
            out_l[k] = v[i] - float(np.mean(prior_l))
        used.append({"month_end": day, "obs_date": d.isoformat(), "release": rel[i]})
    return out_c, out_l, used


def audit_known_at(used_eia, used_nass):
    for u in used_eia:
        if date.fromisoformat(u["week_ending"]) + timedelta(days=EIA_KNOWN_DAYS) > date.fromisoformat(u["month_end"]):
            raise AssertionError(f"KNOWN-AT AUDIT: EIA week {u['week_ending']} used at {u['month_end']}")
    for u in used_nass:
        if not (u["release"] <= u["month_end"] + NASS_KNOWN_UTC):
            raise AssertionError(f"KNOWN-AT AUDIT: NASS release {u['release']} used at {u['month_end']}")


def cs_rho_series(S, elig, Z, ks, min_n=5):
    out = []
    for k in ks:
        ok = elig[:, k] & np.isfinite(S[:, k]) & np.isfinite(Z[:, k]); out.append(spearman(S[ok, k], Z[ok, k]) if ok.sum() >= min_n else np.nan)
    return np.array(out)


def nc_verdict(rhos, ses):
    a = np.abs(np.array(rhos, float)); s = np.array(ses, float); fin = np.isfinite(a)
    if np.any(a[fin] >= NC_HIGH):
        return "FAILS"
    if np.all(a[fin] + 2 * s[fin] < NC_LOW):
        return "HOLDS"
    return "UNRESOLVED"


# ------------------------------------------------------------------------------------------ run
def run(log=print):
    t0 = time.time(); rng = np.random.default_rng(SEED); warnings.filterwarnings("ignore", category=RuntimeWarning)
    log(f"D600 STAGE 0 -- the basis-momentum closure programme; spec {SPEC}; no session, release or observation from {RESERVED_FROM} on; no cost, no construction, no closure rule")
    days, T, me, b, b0, member_t, gfull = R83.build_book(log); x = b["x"]; K = me.size; n = len(CM); wP = R55.window_mask(days, *PRIMARY); wL = R55.window_mask(days, *LONG); dP_days, dL_days = days[wP], days[wL]
    first_session = me[b["first_me"]] + 1; valid = (np.arange(T) >= first_session) & (np.abs(b["held"]).sum(0) > 0); yr = np.array([d[:4] for d in days]); me_month = np.array([int(days[i][5:7]) for i in me])
    art = json.loads(ART_D564.read_text(encoding="utf-8")); audits = {}
    # ---- the three harnesses ----
    def audit_harness(series, ref, what):
        s = R55.sharpe(series[wP])
        if abs(s - ref) > 1e-9:
            raise AssertionError(f"HARNESS ({what}): rebuilt {s} vs artifact {ref}")
        return s
    ref_p = art["cells"]["EW High4/Low4"]["gross"]["sharpe"]; ref_s = art["spreading"]["gross"]["sharpe"]; ref_ns = art["non_seasonal_diagnostic"]["gross"]["sharpe"]
    strip = pd.read_csv(R56.STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8"); strip = strip[(strip["ref"] < RESERVED_FROM) & strip["root"].isin(CM)]
    tables = R64.strip_tables(strip, days, CM); ns3 = nearby_series3(tables, CM, days, me, FFILL); ns = b["ns"]
    for key in ("R1", "R2", "r1d", "r2d", "live", "stale"):
        if not np.array_equal(np.nan_to_num(ns3[key], nan=-7.0), np.nan_to_num(ns[key], nan=-7.0)):
            raise AssertionError(f"nearby_series3 disagrees with D564's nearby_series on {key}")
    audits["nearby3_equals_d564_on_shared_outputs"] = True
    span = np.zeros((n, T), dtype=bool)
    for i in range(n):
        ix = np.flatnonzero(ns["live"][i])
        if ix.size:
            span[i, ix[0]:ix[-1] + 1] = True
    held = b["held"]; rsimple = ns["r1d"]; rspread = ns["r1d"] - ns["r2d"]
    sh_p = audit_harness(x, ref_p, "primary"); xs = R55.book_return(held, rspread); sh_s = audit_harness(xs, ref_s, "spreading")
    ix_ns = [CM.index(r) for r in NON_SEASONAL]; mem_ns, _ = R64.membership_fixed(b["BM"][ix_ns], b["elig"][ix_ns], NON_SEASONAL, R64.N_LEG_NS, R64.MIN_ELIGIBLE_NS)
    x_ns = R55.book_return(R55.hold_from_month_ends(mem_ns.astype(float), me, T, span[ix_ns]), rsimple[ix_ns]); sh_ns = audit_harness(x_ns, ref_ns, "non-seasonal")
    audits["harness_raises"] = expect_raise(lambda: audit_harness(np.roll(x, 1), ref_p, "primary"), "the series rolled one session", log)
    harness = {"primary": {"rebuilt": float(sh_p), "artifact": float(ref_p)}, "spreading": {"rebuilt": float(sh_s), "artifact": float(ref_s)}, "non_seasonal": {"rebuilt": float(sh_ns), "artifact": float(ref_ns)}, "tolerance": 1e-9}
    log(f"  harness: primary {sh_p:+.6f}, spreading {sh_s:+.6f}, non-seasonal {sh_ns:+.6f} -- all equal D564's artifact to 1e-9")
    BM12, elig12 = b["BM"], b["elig"]
    # ---- A: the maturity cells ----
    BM23, elig23 = signal_pair(ns3["R2"], ns3["R3"], ns3["stale3"]); curv = np.where(elig12 & elig23, BM12 - BM23, np.nan); elig_c = elig12 & elig23
    piv = {}; audits["bm23_cells_checked"] = audit_bm23(BM23, elig23, strip, days, me, pivots=piv)
    audits["bm23_audit_raises"] = expect_raise(lambda: audit_bm23(BM23, elig23, strip, days, me, n_check=20, thr_shift=1, pivots=piv), "the delivery threshold shifted one month", log)
    for a_, b_, lab in ((BM12, BM23, "BM12 vs BM23"), (BM12, curv, "BM12 vs curvature"), (BM23, curv, "BM23 vs curvature")):
        ok = np.isfinite(a_) & np.isfinite(b_)
        if np.allclose(a_[ok], b_[ok]):
            raise AssertionError(f"RIGHT-QUANTITY: {lab} identical")
    audits["maturity_signals_pairwise_distinct"] = True
    # ---- B: de-seasonalised ----
    BMds, elig_ds, s_np = deseasonalise(ns["R1"], ns["R2"], ns["stale"], me_month); s_pd = seasonal_pandas(ns["R1"] - ns["R2"], me_month); audit_seasonal(s_np, s_pd); audits["seasonal_second_path"] = True
    audits["seasonal_audit_raises"] = expect_raise(lambda: audit_seasonal(s_np, seasonal_pandas(ns["R1"] - ns["R2"], me_month, shift=0)), "the seasonal mean not shifted (look-ahead)", log)
    ok = np.isfinite(BMds) & np.isfinite(BM12)
    if np.allclose(BMds[ok], BM12[ok]):
        raise AssertionError("RIGHT-QUANTITY: BM_ds equals BM")
    audits["bm_ds_distinct_from_bm"] = True
    # ---- the new cells, scored as D564 scores its cells ----
    g = dict(roots=CM, days=days, close=ns["close1"], rlog=np.where(ns["live"] & (ns["r1d"] != 0.0), np.log1p(ns["r1d"]), np.nan), dP=ns["dP1"], roll=ns["roll"], live=ns["live"], span=span, nonpositive=[])
    ones = np.ones((n, T)); cells = {}; members = {}
    for name, S_, E_ in (("BM(2,3)", BM23, elig23), ("curvature", curv, elig_c), ("BM_ds", BMds, elig_ds)):
        mem, diag = R64.membership_fixed(S_, E_, CM, N_LEG, MIN_ELIGIBLE); sh_ = R55.hold_from_month_ends(mem.astype(float), me, T, span)
        cells[name] = dict(book="published", sign_held=sh_, scale_held=ones, pos=sh_); members[name] = (mem, E_, diag)
    cells["primary on r2d"] = dict(book="published", sign_held=held, scale_held=ones, pos=held, r=ns["r2d"]); cells["primary on r1d-r2d"] = dict(book="published", sign_held=held, scale_held=ones, pos=held, r=rspread)
    results = {}
    for name, c in cells.items():
        r_ = c.get("r", rsimple); xc = R55.book_return(c["pos"], r_); results[name] = {"gross": R55.stats_block(xc[wP], dP_days, name), "gross_long": R55.stats_block(xc[wL], dL_days, name + " 2011-2023"), "positioned_names_mean": float((c["pos"][:, wP] != 0).sum(0).mean())}
        c["x"] = xc; log(f"  {name:18s} gross {results[name]['gross']['sharpe']:+.3f} / So {results[name]['gross']['sortino']:+.3f} (SE {results[name]['gross']['se']:.2f}); long {results[name]['gross_long']['sharpe']:+.3f}")
    if abs(results["primary on r1d-r2d"]["gross"]["sharpe"] - ref_s) > 1e-9:
        raise AssertionError("the spread cell did not reproduce P-7")
    # N1 for the three signal cells (the r2d / spread cells rotate the same book as the primary; their nulls are the primary's on those returns)
    live_idx = [np.flatnonzero(span[i] & wP) for i in range(n)]; null_cells = {k: dict(book="published", sign_held=np.where(wP[None, :], v["sign_held"], 0.0), scale_held=ones) for k, v in cells.items() if k in ("BM(2,3)", "curvature", "BM_ds")}
    for k in R64.GUARD_OFFSETS:
        k = k % (int(wP.sum()) - 1) or 1; p = R55.rotate_signs(null_cells["BM(2,3)"]["sign_held"], live_idx, k) * ones
        if not np.array_equal(R55.book_return(p, rsimple)[wP], R55.book_return_loop(p[:, wP], rsimple[:, wP])):
            raise AssertionError(f"exactness guard failed at offset {k}")
    audits["exactness_guard_offsets"] = len(R64.GUARD_OFFSETS); tn = time.time(); log(f"  N1 over {int(wP.sum()) - 1} offsets x 3 cells ...")
    upp_f, tick_f, comm_f, _ = R56.min_size(gfull, gfull["roots"]); ixf = [gfull["roots"].index(r) for r in CM]
    null_all, keys, null_s = R55.enumerate_null(null_cells, g, live_idx, wP, rsimple, upp_f[ixf], comm_f[ixf], tick_f[ixf], CM, log, with_sortino=True)
    ks = np.arange(1, null_all.shape[0] + 1); keep = (ks >= R55.NULL_PURGE) & (ks <= int(wP.sum()) - R55.NULL_PURGE); null = null_all[keep]
    n1 = {"offsets_enumerated": int(null_all.shape[0]), "purge_sessions": R55.NULL_PURGE, "offsets_after_purge": int(null.shape[0]), "per_cell": {}, "wall_s": round(time.time() - tn, 1)}
    obs = np.array([results[k]["gross"]["sharpe"] for k in keys])
    for j, nm in enumerate(keys):
        col = null[:, j]; n1["per_cell"][nm] = {"observed": float(obs[j]), "p05": float(np.percentile(col, 5)), "p50": float(np.percentile(col, 50)), "p95": float(np.percentile(col, 95)), "pct_rank": float((col < obs[j]).mean()), "clears_p95": bool(obs[j] > np.percentile(col, 95)),
                                                 "sortino": R55.sortino_null_block(cells[nm]["x"][wP], null_s[:, j], keep)}
    fam = null.max(1); n2 = {"family": list(keys), "observed_best": float(obs.max()), "observed_best_cell": keys[int(obs.argmax())], "p50": float(np.percentile(fam, 50)), "p95": float(np.percentile(fam, 95)), "pct_rank": float((fam < obs.max()).mean()), "clears_p95": bool(obs.max() > np.percentile(fam, 95))}
    meP = np.array([wP[min(m + 1, T - 1)] for m in me]); n3 = {}
    for nm in keys:
        mem, E_, _ = members[nm]; t3 = time.time(); v3, _ = R64.name_randomised_null(np.where(meP[None, :], mem, 0), E_, me, T, span, rsimple, wP, days, N3_DRAWS, N3_SEED); o = results[nm]["gross"]["sharpe"]; p95 = float(np.percentile(v3, 95)); se3 = R64._p95_boot_se(v3)
        n3[nm] = {"draws": N3_DRAWS, "p50": float(np.percentile(v3, 50)), "p95": p95, "p95_boot_se": se3, "pct_rank": float((v3 < o).mean()), "clears_p95": bool(o > p95), "unresolved": bool(abs(o - p95) < 2 * se3), "wall_s": round(time.time() - t3, 1)}
    for nm in keys:
        log(f"  {nm:10s} N1 rank {n1['per_cell'][nm]['pct_rank']:.3f} (p95 {n1['per_cell'][nm]['p95']:+.3f})  N3 rank {n3[nm]['pct_rank']:.3f} (p95 {n3[nm]['p95']:+.3f})")
    log(f"  N2 family best {n2['observed_best']:+.3f} ({n2['observed_best_cell']}) p95 {n2['p95']:+.3f} rank {n2['pct_rank']:.3f}")
    def sig_beside(S_, E_):
        rho = [spearman(S_[E_[:, k] & elig12[:, k], k], BM12[E_[:, k] & elig12[:, k], k]) for k in range(K) if (E_[:, k] & elig12[:, k]).sum() >= 8]; return float(np.nanmean(rho))
    A = {"cells": {k: results[k] for k in cells}, "spearman_with_bm12": {"BM(2,3)": sig_beside(BM23, elig23), "curvature": sig_beside(curv, elig_c)},
         "r2d_share_of_primary": float(cells["primary on r2d"]["x"][wP].sum() / x[wP].sum()) if x[wP].sum() != 0 else None,
         "eligible_mean": {nm: float(np.mean([members[nm][2][k]["n_eligible"] for k in range(K) if meP[k]])) for nm in keys}, "flat_month_ends": {nm: int(sum(1 for k in range(K) if meP[k] and members[nm][2][k]["flat"])) for nm in keys},
         "by_era": {nm: {f"{a_}..{b_}": R55.sharpe(cells[nm]["x"][R55.window_mask(days, a_, b_)]) for a_, b_ in R55.ERAS} for nm in keys},
         "per_root_sign_count": {nm: int(sum(1 for i in range(n) if (cells[nm]["pos"][i] * rsimple[i])[wP].sum() > 0)) for nm in keys}}
    B = {"cell": results["BM_ds"], "rho_bm_ds_vs_bm_by_root": {CM[i]: spearman(BMds[i], BM12[i]) for i in range(n)}, "rho_non_seasonal_mean": float(np.nanmean([spearman(BMds[i], BM12[i]) for i in ix_ns])), "rho_seasonal_mean": float(np.nanmean([spearman(BMds[i], BM12[i]) for i in range(n) if i not in ix_ns])),
         "eligible_mean": A["eligible_mean"]["BM_ds"], "harness_non_seasonal_reproduced": True}
    log(f"  B: rho(BM_ds, BM) non-seasonal {B['rho_non_seasonal_mean']:+.3f}, seasonal {B['rho_seasonal_mean']:+.3f}")
    # ---- C: T3 ----
    F = {h: forward_returns(ns["R1"], h) for h in HORIZONS}; ics = {h: ic_series(BM12, elig12, F[h]) for h in HORIZONS}; audit_ic(ics[1], ic_series_pandas(BM12, elig12, F[1])); audits["ic_second_path"] = True
    audits["ic_audit_raises"] = expect_raise(lambda: audit_ic(ics[1], ic_series_pandas(BM12, elig12, np.roll(F[1], 1, axis=1))), "the forward return unlagged", log)
    C = {"ic": {}}
    for h in HORIZONS:
        m_, se_, t_, n_ = nw_t(ics[h][meP | (np.arange(K) >= b["first_me"])], h - 1); C["ic"][f"h{h}"] = {"mean": m_, "nw_se": se_, "t": t_, "n": n_}
    bm_ = bucket_means(BM12, elig12, F[1]); bm_ = bm_[bm_["k"] >= b["first_me"]]; mean = bm_.drop(columns="k").mean(); C["buckets_monthly_mean_bp"] = {c: float(1e4 * v) for c, v in mean.items()}
    C["monotone_low4_mid_high4"] = bool(mean["low4"] < mean["mid"] < mean["high4"]); qs = [mean[f"q{j}"] for j in range(1, 6)]; C["quintiles_no_interior_reversal"] = bool(qs[1] <= qs[2] <= qs[3] or (qs[0] < qs[4] and spearman(range(5), qs) > 0.5))
    years = sorted({days[me[int(k)]][:4] for k in bm_["k"]}); C["by_year"] = {}
    for y in years:
        kk = [int(k) for k in bm_["k"] if days[me[k]][:4] == y]; sub = bm_[bm_["k"].isin(kk)]; C["by_year"][y] = {"ic1": float(np.nanmean(ics[1][kk])), "spread_high4_low4_bp": float(1e4 * (sub["high4"] - sub["low4"]).mean()), "n": len(kk)}
    full = {y: v for y, v in C["by_year"].items() if v["n"] >= 10}; C["years_spread_positive"] = int(sum(v["spread_high4_low4_bp"] > 0 for v in full.values())); C["years_counted"] = len(full)
    C["checklist"] = {"ic1_t_ge_3": bool(C["ic"]["h1"]["t"] >= 3.0), "ic1_t_ge_2_predicted": bool(C["ic"]["h1"]["t"] >= 2.0), "no_interior_reversal": C["monotone_low4_mid_high4"], "years_ge_60pct": bool(C["years_spread_positive"] >= 0.6 * C["years_counted"]), "decays_by_6m": bool(C["ic"]["h6"]["mean"] < C["ic"]["h1"]["mean"]), "not_built": ["CPCV", "PBO", "incremental IC vs library"]}
    log("  C: IC " + " ".join(f"h{h} {C['ic'][f'h{h}']['mean']:+.3f} (t {C['ic'][f'h{h}']['t']:+.2f})" for h in HORIZONS) + f"; buckets low4 {C['buckets_monthly_mean_bp']['low4']:+.0f} mid {C['buckets_monthly_mean_bp']['mid']:+.0f} high4 {C['buckets_monthly_mean_bp']['high4']:+.0f} bp/month; years spread positive {C['years_spread_positive']}/{C['years_counted']}; checklist {C['checklist']}")
    # ---- D: He-Kelly-Manela ----
    if HKM.exists():
        hk = load_hkm(); mb = monthly_book(x, days); periods = [p for p in sorted(mb) if p >= 201107 and p in hk.index]; y_ = np.array([mb[p] for p in periods]); f_ = hk.loc[periods, "intermediary_capital_risk_factor"].to_numpy(float); yrs_d = np.array([p // 100 for p in periods])
        audits["m4_sign_in_money"] = audit_loading_sign(rng); audits["m4_sign_audit_raises"] = expect_raise(lambda: audit_loading_sign(rng, True), "a negated synthetic book (M4)", log)
        beta, se, t, nn, rho = hac_ols(y_, f_, HAC_LAG); se_boot = year_block_se(np.arange(len(periods)), yrs_d, rng, stat=lambda idx: hac_ols(y_[idx.astype(int)], f_[idx.astype(int)], HAC_LAG)[0])
        D = {"D1_loading": {"beta": beta, "hac_se": se, "t": t, "n_months": nn, "rho": rho, "beta_year_block_se": se_boot, "first": periods[0], "last": periods[-1]}}
        blev, _, tlev, _, rlev = hac_ols(y_, hk.loc[periods, "intermediary_leverage_ratio_squared"].to_numpy(float), HAC_LAG); D["D1_on_leverage_squared"] = {"beta": blev, "t": tlev, "rho": rlev}
        for lab, lo, hi in (("2011_2015", 201107, 201512), ("2016_2023", 201601, 202312)):
            m_ = (np.array(periods) >= lo) & (np.array(periods) <= hi); bb, _, tt, nn_, rr = hac_ols(y_[m_], f_[m_], HAC_LAG); D[f"D1_{lab}"] = {"beta": bb, "t": tt, "rho": rr, "n": nn_}
        y0 = monthly_book(b0["x"], days); bb0, _, tt0, _, rr0 = hac_ols(np.array([y0.get(p, np.nan) for p in periods]), f_, HAC_LAG); D["D1_as_preregistered_ffill1"] = {"beta": bb0, "t": tt0, "rho": rr0}
        ratio = hk["intermediary_capital_ratio"]; st = tercile_state(ratio, periods); stv = np.array([st.get(p, np.nan) for p in periods]); okS = np.isfinite(stv); ys, ss = y_[okS], stv[okS].astype(int); V = ys.size
        obs2 = state_delta(ys, ss); nullv = np.array([state_delta(ys, np.roll(ss, o)) for o in range(1, V)]); offs = np.arange(1, V); non = nullv[np.minimum(offs, V - offs) > NON_OVERLAP_M]
        yrs_s = yrs_d[okS]; both = sorted({int(y) for y in yrs_s if (ss[yrs_s == y] == -1).any() and (ss[yrs_s == y] == 1).any()})
        D["D2_lagged_conditioning"] = {"delta_bottom_minus_top_bp": obs2, "rank_in_shifts": float((nullv < obs2).mean()), "n_shifts": int(nullv.size), "rank_non_overlapping": float((non < obs2).mean()), "null_p50": float(np.nanpercentile(nullv, 50)), "null_p95": float(np.nanpercentile(nullv, 95)),
                                       "months_bottom": int((ss == -1).sum()), "months_top": int((ss == 1).sum()), "years_with_both_states": both, "n_years_both": len(both)}
        st3 = {}
        for m in periods:
            pm = int((pd.Period(str(m), "M") - 3).strftime("%Y%m")); pm1 = int((pd.Period(str(pm), "M") + 1).strftime("%Y%m"))
            if pm1 in st:
                st3[m] = st[pm1]
        stv3 = np.array([st3.get(p, np.nan) for p in periods]); ok3 = np.isfinite(stv3); D["D2_lag3_beside"] = {"delta_bp": state_delta(y_[ok3], stv3[ok3].astype(int)), "n": int(ok3.sum())}
        iqr = np.array([np.subtract(*np.percentile(BM12[elig12[:, k], k], [75, 25])) if elig12[:, k].sum() >= MIN_ELIGIBLE else np.nan for k in range(K)]); kp = {int(days[me[k]][:4] + days[me[k]][5:7]): iqr[k] for k in range(K)}
        pairs = [(kp[p], ratio[p]) for p in [int((pd.Period(str(m), "M") - 1).strftime("%Y%m")) for m in periods] if p in kp and p in ratio.index and np.isfinite(kp[p])]; pa = np.array(pairs)
        rho3 = spearman(pa[:, 0], pa[:, 1]); bt = []; L = len(pa); nb = int(np.ceil(L / 12))
        for _ in range(BOOT):
            starts = rng.choice(np.arange(0, L, 12), nb, replace=True); sel = np.concatenate([np.arange(s_, min(s_ + 12, L)) for s_ in starts]); bt.append(spearman(pa[sel, 0], pa[sel, 1]))
        ann = pa[11::12]; D["D3_dispersion"] = {"spearman_iqr_vs_lagged_ratio": rho3, "block12_p05": float(np.nanpercentile(bt, 5)), "block12_p95": float(np.nanpercentile(bt, 95)), "n": L, "annual_spearman": spearman(ann[:, 0], ann[:, 1]), "n_annual": int(len(ann))}
        v_d = "SUPPORTED" if (beta > 0 and t >= 2.0) else ("NOT SUPPORTED" if (beta <= 0 or t < 1.0) else "UNRESOLVED"); D["verdict"] = v_d
        log(f"  D: loading beta {beta:+.4f} (HAC t {t:+.2f}, rho {rho:+.3f}, n {nn}) -> {v_d}; eras " + " | ".join(f"{k}: t {D[k]['t']:+.2f}" for k in ("D1_2011_2015", "D1_2016_2023")) + f"; D2 bottom-top {obs2:+.1f} bp/month rank {D['D2_lagged_conditioning']['rank_in_shifts']:.3f} (years with both states {len(both)}); D3 spearman {rho3:+.3f} [{D['D3_dispersion']['block12_p05']:+.2f}, {D['D3_dispersion']['block12_p95']:+.2f}]")
    else:
        D = {"verdict": "NOT RUN", "reason": "hkm fixture absent"}; log("  D: hkm fixture absent -- not run")
    # ---- E: inventories ----
    eia, nass = load_inventories(); me_days = [str(days[i]) for i in me]; Zc = np.full((n, K), np.nan); Zl = np.full((n, K), np.nan); used_e, used_n = [], []; covered = []
    for i, r in enumerate(CM):
        m_ = INV_MAP.get(r)
        if m_ is None:
            continue
        if m_[0] == "eia" and eia is not None:
            s_ = eia[eia["series"] == m_[1]]; c_, l_, u_ = eia_state_at(s_, me_days); Zc[i], Zl[i] = c_, l_; used_e += u_; covered.append(r)
        elif m_[0] == "nass" and nass is not None:
            s_ = nass[(nass["report"] == m_[1]) & (nass["commodity"] == m_[2])]
            if len(s_):
                c_, l_, u_ = nass_state_at(s_, me_days); Zc[i], Zl[i] = c_, l_; used_n += u_; covered.append(r)
    if covered:
        audit_known_at(used_e, used_n); audits["known_at_rows_checked"] = len(used_e) + len(used_n)
        audits["known_at_raises"] = expect_raise(lambda: audit_known_at([{**u, "week_ending": (date.fromisoformat(u["week_ending"]) + timedelta(days=7)).isoformat()} for u in used_e[:50]], []), "an EIA week claimed one week early", log) if used_e else None
        okZ = np.isfinite(Zc) & np.isfinite(Zl)
        if np.allclose(Zc[okZ], Zl[okZ]):
            raise AssertionError("RIGHT-QUANTITY: inventory change equals level")
        ks_e = np.arange(b["first_me"], K); yks = np.array([int(me_days[k][:4]) for k in ks_e]); ic_c = cs_rho_series(BM12, elig12, Zc, ks_e); ic_l = cs_rho_series(BM12, elig12, Zl, ks_e)
        pooled_c = spearman(BM12[:, ks_e][elig12[:, ks_e]], Zc[:, ks_e][elig12[:, ks_e]]); ts_c = {CM[i]: spearman(BM12[i, ks_e], Zc[i, ks_e]) for i in range(n) if CM[i] in covered}; ts_l = {CM[i]: spearman(BM12[i, ks_e], Zl[i, ks_e]) for i in range(n) if CM[i] in covered}
        rhos = [float(np.nanmean(ic_c)), pooled_c] + [v for v in ts_c.values()]; ses = [year_block_se(ic_c, yks, rng), year_block_se(np.arange(ks_e.size), yks, rng, stat=lambda idx: spearman(BM12[:, ks_e[idx.astype(int)]][elig12[:, ks_e[idx.astype(int)]]], Zc[:, ks_e[idx.astype(int)]][elig12[:, ks_e[idx.astype(int)]]]))]
        ses += [year_block_se(np.arange(ks_e.size), yks, rng, stat=lambda idx, i=i: spearman(BM12[i, ks_e[idx.astype(int)]], Zc[i, ks_e[idx.astype(int)]])) for i in range(n) if CM[i] in covered]
        E = {"covered_roots": covered, "excluded": [r for r in CM if r not in covered], "n_month_ends_with_ge5_roots": int(np.isfinite(ic_c).sum()), "change": {"mean_cs_spearman": rhos[0], "se_year_block": ses[0], "pooled_spearman": pooled_c, "pooled_se": ses[1], "per_root_ts_spearman": ts_c, "per_root_se": dict(zip(ts_c.keys(), ses[2:]))},
             "level": {"mean_cs_spearman": float(np.nanmean(ic_l)), "per_root_ts_spearman": ts_l}, "by_era": {lab: {"mean_cs_spearman_change": float(np.nanmean(ic_c[(yks >= lo) & (yks <= hi)]))} for lab, lo, hi in (("2011_2015", 2011, 2015), ("2016_2023", 2016, 2023))},
             "max_abs_rho": float(np.nanmax(np.abs(rhos))), "verdict": nc_verdict(rhos, ses)}
        log(f"  E: covered {covered}; BM vs inventory change cs-spearman {rhos[0]:+.3f} (SE {ses[0]:.3f}), pooled {pooled_c:+.3f}; per-root " + " ".join(f"{k}:{v:+.2f}" for k, v in ts_c.items()) + f"; level cs {E['level']['mean_cs_spearman']:+.3f}; max |rho| {E['max_abs_rho']:.3f} -> {E['verdict']}")
    else:
        E = {"verdict": "NOT RUN", "reason": "no inventory fixture"}; log("  E: no inventory fixture -- not run")
    # ---- F: capacity ----
    if CV.exists():
        with gzip.open(CV, "rt", encoding="utf-8") as fh:
            cv = pd.read_csv(fh, dtype={"session": str}, encoding="utf-8")
        cv = cv[(cv["session"] >= CAP_SPAN[0]) & (cv["session"] <= CAP_SPAN[1])]; sym = {}
        for r in CM:
            sr = strip[strip["root"] == r]; sym[r] = {(ref, FB.ym(c, ref)): c for c, ref in zip(sr["contract"], sr["ref"])}
        F_ = {}; day_ix = {d: i for i, d in enumerate(days)}; cvi = {(r, c): g_.set_index("session")["cleared_volume"] for (r, c), g_ in cv.groupby(["root", "contract"])}
        for i, r in enumerate(CM):
            A_, cols = tables[r]; vols = {"T1": [], "T2": []}
            for k in range(K - 1):
                dref = str(days[me[k]])
                if not (CAP_SPAN[0] <= dref <= CAP_SPAN[1]):
                    continue
                for q, Tq in (("T1", ns3["T1"]), ("T2", ns3["T2"])):
                    j = Tq[i, k]
                    if j < 0:
                        continue
                    ym_ = int(cols[j]); key = (dref, (ym_ // 12, ym_ % 12 if ym_ % 12 else 12))
                    # cols are year*12+month; recover (y, m) the way strip_tables keyed them
                    yy, mm = divmod(ym_, 12)
                    if mm == 0:
                        yy, mm = yy - 1, 12
                    c = sym[r].get((dref, (yy, mm)))
                    if c is None or (r, c) not in cvi:
                        continue
                    s_ = cvi[(r, c)]; hold = [str(d_) for d_ in days[me[k] + 1:me[k + 1] + 1]]; v_ = s_.reindex(hold).dropna().to_numpy(float); vols[q].extend(v_.tolist())
            F_[r] = {q: {"median": float(np.median(v)) if v else None, "p10": float(np.percentile(v, 10)) if v else None, "n_days": len(v), "one_contract_share_of_median": float(1 / np.median(v)) if v and np.median(v) > 0 else None} for q, v in vols.items()}
        F = {"span": list(CAP_SPAN), "by_root": F_, "note": "median and p10 daily cleared volume of the held contract over the span; the D564 dollar book holds one contract"}
        log("  F: T2 median daily cleared volume " + " ".join(f"{r}:{F_[r]['T2']['median']:.0f}" if F_[r]["T2"]["median"] else f"{r}:na" for r in CM))
    else:
        F = {"note": "cleared-volume fixture absent -- not run"}; log("  F: cleared-volume fixture absent -- not run")
    # ---- predictions and verdicts ----
    preds = {"A_bm23_positive_above_n1": n1["per_cell"]["BM(2,3)"]["clears_p95"] and obs[keys.index("BM(2,3)")] > 0, "A_curvature_positive_above_n1": n1["per_cell"]["curvature"]["clears_p95"] and obs[keys.index("curvature")] > 0, "A_family_above_n2": n2["clears_p95"],
             "A_spread_cell_reproduces_p7": True, "A_bm23_spearman_in_0.3_0.7": bool(0.3 <= A["spearman_with_bm12"]["BM(2,3)"] <= 0.7), "A_curvature_spearman_positive": bool(A["spearman_with_bm12"]["curvature"] > 0),
             "B_bm_ds_positive_above_n1": n1["per_cell"]["BM_ds"]["clears_p95"] and obs[keys.index("BM_ds")] > 0, "B_rho_non_seasonal_gt_0.8": bool(B["rho_non_seasonal_mean"] > 0.8), "B_rho_seasonal_lower": bool(B["rho_seasonal_mean"] < B["rho_non_seasonal_mean"]),
             "C_ic1_positive_t_ge_2": bool(C["ic"]["h1"]["mean"] > 0 and C["ic"]["h1"]["t"] >= 2), "C_decays_by_6m": C["checklist"]["decays_by_6m"], "D_verdict": D["verdict"], "E_verdict": E["verdict"]}
    verdicts = {"A_M3": "SUPPORTED" if (preds["A_bm23_positive_above_n1"] or preds["A_curvature_positive_above_n1"]) and preds["A_family_above_n2"] else "NOT SUPPORTED", "B_deseasonalised": "SURVIVES" if preds["B_bm_ds_positive_above_n1"] else "DOES NOT SURVIVE",
                "C_T3": C["checklist"], "D_M4": D["verdict"], "E_M5": E["verdict"]}
    log("  predictions: " + "; ".join(f"{k} {v}" for k, v in preds.items())); log(f"  STAGE 0 VERDICTS: A(M3) {verdicts['A_M3']}; B {verdicts['B_deseasonalised']}; C see checklist; D(M4) {verdicts['D_M4']}; E(M5) {verdicts['E_M5']}")
    res = {"spec": SPEC, "windows": {"long": [str(days[first_session]), str(days[-1])], "primary": list(PRIMARY), "reserved_from": RESERVED_FROM}, "harness": harness, "audits": audits, "A": A, "B": B, "C": C, "D": D, "E": E, "F": F,
           "nulls": {"n1": n1, "n2": n2, "n3": n3}, "predictions": preds, "verdicts": verdicts, "timing_s": round(time.time() - t0, 1),
           "construction": {"lookback": LOOKBACK, "n_leg": N_LEG, "min_eligible": MIN_ELIGIBLE, "ffill": FFILL, "ds_min_prior": DS_MIN_PRIOR, "horizons": HORIZONS, "hac_lag": HAC_LAG, "tercile_window": TERCILE_WINDOW, "eia_known_days": EIA_KNOWN_DAYS, "nc_bars": [NC_LOW, NC_HIGH], "season_prior": SEASON_PRIOR}}
    guard_outputs(res); audits["required_outputs_guard_raises"] = expect_raise(lambda: guard_outputs({k: v for k, v in res.items() if k != "D"}), "a missing declared output", log)
    OUT.write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8"); log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']} s")
    return res


def selftest(log=print) -> int:
    rng = np.random.default_rng(3)
    # signal_pair and the maturity distinctness on a synthetic strip-like set of monthly returns
    # 72 month-ends: the de-seasonalised signal needs three priors of every calendar month, so it is first eligible at k = 47
    n, K = 5, 72; R1 = rng.normal(0, 0.03, (n, K)); R2 = R1 + rng.normal(0, 0.01, (n, K)); R3 = R2 + rng.normal(0, 0.01, (n, K)); stale = np.zeros((n, K), bool)
    S12, e12 = signal_pair(R1, R2, stale); S23, e23 = signal_pair(R2, R3, stale); assert e12[:, LOOKBACK - 1:].all() and not e12[:, :LOOKBACK - 1].any(); assert not np.allclose(S12[e12], S23[e23]); log("  signal_pair: eligibility and distinctness on a synthetic set")
    # de-seasonalisation: a pure calendar signal is removed; second path agrees and raises without the shift
    me_month = np.array([(k % 12) + 1 for k in range(K)]); d_season = np.array([[0.05 if mm == 6 else 0.0 for mm in me_month] for _ in range(n)]); Rb = np.zeros((n, K)); Ra = d_season
    BMds, eds, s_np = deseasonalise(Ra, Rb, stale, me_month); audit_seasonal(s_np, seasonal_pandas(Ra - Rb, me_month)); assert np.nanmax(np.abs(BMds[eds])) < 1e-12, "a pure calendar signal survived de-seasonalisation"
    log("  de-seasonalisation: a pure calendar signal is removed; numpy and pandas seasonal means agree"); expect_raise(lambda: audit_seasonal(s_np, seasonal_pandas(Ra - Rb, me_month, shift=0)), "the seasonal mean not shifted (look-ahead)", log)
    # IC: numpy vs pandas; sign in money -- a signal that IS the forward return gives IC 1
    F1 = forward_returns(R1, 1); ic = ic_series(S12, e12, F1, min_n=4); audit_ic(ic, ic_series_pandas(S12, e12, F1, min_n=4)); ic_true = ic_series(F1, e12, F1, min_n=4); assert np.nanmin(ic_true) > 0.999
    log("  IC: numpy and pandas agree; a signal equal to the forward return has IC 1"); expect_raise(lambda: audit_ic(ic, ic_series_pandas(S12, e12, np.roll(F1, 1, axis=1), min_n=4)), "the forward return unlagged", log)
    # M4 sign in money and the HAC regression on a known slope
    b_, t_ = audit_loading_sign(rng); log(f"  M4 sign in money: beta {b_:+.3f} t {t_:+.1f} on a synthetic book"); expect_raise(lambda: audit_loading_sign(rng, True), "a negated synthetic book (M4)", log)
    xg = rng.normal(size=500); yg = 2.0 * xg + rng.normal(0, 0.1, 500); bb, se, tt, _, _ = hac_ols(yg, xg, 3); assert abs(bb - 2.0) < 0.05 and tt > 20
    # known-at audit
    used = [{"month_end": "2019-06-28", "week_ending": "2019-06-21"}]; audit_known_at(used, [{"month_end": "2019-06-28", "obs_date": "2019-06-01", "release": "2019-06-28T16:00:00Z"}]); log("  known-at: a week ending 2019-06-21 is usable at 2019-06-28; a NASS release at 16:00Z is usable that day")
    expect_raise(lambda: audit_known_at([{"month_end": "2019-06-28", "week_ending": "2019-06-24"}], []), "an EIA week claimed early", log); expect_raise(lambda: audit_known_at([], [{"month_end": "2019-06-28", "obs_date": "2019-06-01", "release": "2019-06-28T21:00:00Z"}]), "a NASS release after the close", log)
    # inventory state: a series with a known 52-week change and a seasonal norm
    weeks = pd.date_range("2010-01-08", "2020-12-25", freq="7D"); vals = np.exp(0.1 * np.arange(len(weeks)) / 52.0); ser = pd.DataFrame({"week_ending": weeks.strftime("%Y-%m-%d"), "value": vals}); c_, l_, u_ = eia_state_at(ser, ["2018-06-29"])
    assert abs(c_[0]) < 1e-9, f"a constant-growth series should de-seasonalise to a zero change surprise, got {c_[0]}"; assert u_[0]["week_ending"] == "2018-06-22", u_; log("  inventory state: constant growth gives a zero surprise; the latest usable week at 2018-06-29 is 2018-06-22")
    # nc verdict bars
    assert nc_verdict([0.1, -0.2], [0.03, 0.03]) == "HOLDS" and nc_verdict([0.1, 0.55], [0.03, 0.03]) == "FAILS" and nc_verdict([0.28, 0.1], [0.03, 0.03]) == "UNRESOLVED"
    # state delta and the tercile rule
    assert state_delta(np.array([1.0, 2.0, 3.0, 4.0]), np.array([-1, -1, 1, 1])) < 0
    expect_raise(lambda: guard_outputs({"spec": 1}), "missing outputs", log); log("  selftest: every audit passes its clean case and raises on its break"); return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--run", action="store_true"); a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.run:
        run()
    else:
        ap.print_help()
