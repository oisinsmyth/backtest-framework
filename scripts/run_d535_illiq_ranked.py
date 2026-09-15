"""D535 -- displacement per unit volume, ranked CONTINUOUSLY, with five guards against averaging.

Spec committed in bbaa99f BEFORE this file (R8). In sample 2016-01-04..2023-12-29; the 2024+ slice is
RESERVED AND NOT READ. Nothing admitted (R15).

    python scripts/run_d535_illiq_ranked.py --selftest
    python scripts/run_d535_illiq_ranked.py --run        # -> data/d535_illiq_ranked.json

x = log|overnight return| - log(night volume), deviated from its TRAILING mean and ranked by its
TRAILING percentile -- every rank here is causal, which D533's and D534's whole-sample buckets were
not. G1 four-way decomposition, G2 per-root sign count, G3 decile profile, G4 mean+trim+median,
G5 era split. P-5: if the G1 sub-cells disagree in sign the pooled contrast is UNINTERPRETABLE.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s); sys.modules[name] = m; s.loader.exec_module(m)
    return m


D531 = _load("d531e", "run_d531_orb_session_native.py")
D533 = _load("d533e", "run_d533_story_conditions.py")

OUT = REPO / "data" / "d535_illiq_ranked.json"
SPEC = "bbaa99f"
OR_N = 6
PRIMARY = ["CL", "GC", "SI", "NG"]
CONFIRM = ["HG", "HO", "RB", "ZN", "6E", "ZC"]
NIGHT = [f"h{h:02d}" for h in list(range(18, 24)) + list(range(0, 9))]
DEV_N, DEV_MIN = 50, 25                   # trailing mean of x
RANK_N, RANK_MIN = 250, 120               # trailing percentile window
SD_N, SD_MIN = 250, 100                   # trailing sd of the unfiltered break P&L
HORIZONS = [6, 12, 24]
PRIMARY_H = 12
BUCKETS = {"decile": 0.90, "tercile": 2 / 3}
MIN_CELL, MIN_ROOT = 200, 25
ERA = "2020-01-01"
N_DRAWS = 1000
SEED = 20260915
# minimum tradable size: USD per point. The four primary roots come from D533; the confirmation set
# is from data/futures_contract_specs.json, micro where one exists and the full contract otherwise.
UPT = {"CL": 100.0, "GC": 10.0, "SI": 1000.0, "NG": 1000.0,
       "HG": 2500.0, "HO": 42000.0, "RB": 42000.0, "ZN": 1000.0, "6E": 12500.0, "ZC": 50.0}
COST = dict(D533.COST, HG=5.0, HO=10.0, RB=10.0, ZN=6.0, **{"6E": 5.0}, ZC=10.0)


def trailing_pct(v, n=RANK_N, mn=RANK_MIN):
    """Fraction of the PREVIOUS n observations strictly below this one. The current value is never
    part of its own reference window -- that is the causality fix this record is named for."""
    out = np.full(len(v), np.nan)
    for i in range(len(v)):
        lo = max(0, i - n)
        w = v[lo:i]
        w = w[np.isfinite(w)]
        if len(w) >= mn and np.isfinite(v[i]):
            out[i] = float((w < v[i]).mean())
    return out


def _edge(t, suffix, last=False):
    """The FIRST (or last) populated night hour for each session -- a root's night begins when ITS
    market opens, not at h18. Corn reopens at 19:00 CT, so h18_o is populated on 6% of ZC sessions
    and hard-coding h18 silently emptied the whole root."""
    cols = [f"{s}_{suffix}" for s in NIGHT if f"{s}_{suffix}" in t.columns]
    M = t[cols].to_numpy(float)
    if last:
        M = M[:, ::-1]
    fin = np.isfinite(M)
    idx = np.argmax(fin, axis=1)
    out = M[np.arange(len(M)), idx]
    return np.where(fin.any(axis=1), out, np.nan)


def night_state(B, root, days):
    """x = log|overnight return| - log(night volume), its trailing deviation, and its trailing rank."""
    t = B[B.root == root].sort_values("day")
    o = _edge(t, "o"); c = _edge(t, "c", last=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        lr = np.where((o > 0) & (c > 0), np.log(c / o), np.nan)
    vcols = [f"{s}_v" for s in NIGHT if f"{s}_v" in t.columns]
    vol = np.nansum(t[vcols].to_numpy(float), axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        x = np.where((vol > 0) & np.isfinite(lr) & (lr != 0),
                     np.log(np.abs(lr)) - np.log(vol), np.nan)
    dev = (pd.Series(x) - pd.Series(x).rolling(DEV_N, min_periods=DEV_MIN).mean().shift(1)).to_numpy()
    pct = trailing_pct(dev)
    idx = t["day"].to_numpy()
    R = lambda a, f=np.nan: pd.Series(a, index=idx).reindex(days).to_numpy(float)
    return R(pct), np.sign(R(lr)), R(c)


def norm_pnl(A, d, ent, H, upt):
    """Gross dollars per session at minimum size, then divided by the root's OWN TRAILING sd of the
    unfiltered break P&L -- trailing, so one volatility era cannot dominate the pooled mean (G5)."""
    O, C = A["open"], A["close"]
    last = A["open"].shape[1] - 1
    usd = np.full(len(d), np.nan)
    for s in range(len(d)):
        if d[s] == 0 or ent[s] < 0:
            continue
        xb = ent[s] + H
        if xb > last:
            continue
        mv = C[s, xb] - O[s, ent[s]]
        if np.isfinite(mv):
            usd[s] = d[s] * mv * upt
    sd = pd.Series(usd).rolling(SD_N, min_periods=SD_MIN).std().shift(1).to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        gn = np.where(np.isfinite(sd) & (sd > 0), usd / sd, np.nan)
    return usd, gn


def stats(v):
    """G4: the mean is the pass statistic; the trim and the median are declared beside it."""
    v = np.asarray(v, float); v = v[np.isfinite(v)]
    if len(v) == 0:
        return dict(n=0, mean=np.nan, trim=np.nan, median=np.nan)
    s = np.sort(v); k = max(1, int(round(0.01 * len(s))))
    tr = s[k:-k] if len(s) > 2 * k else s
    return dict(n=int(len(v)), mean=float(v.mean()), trim=float(tr.mean()),
                median=float(np.median(v)))


def cell(gn, d, pct, sg, thr, era=None, light=False):
    """WITH/AGAINST above a rank threshold, plus the G1 four-way decomposition.

    `light` computes the MEANS ONLY -- no sort for the trim, no G1. A null draw needs nothing else,
    and the sorts were 6 of every 8 stats() calls in the loop."""
    m = np.isfinite(gn) & np.isfinite(pct) & (d != 0) & np.isfinite(sg) & (sg != 0) & (pct >= thr)
    if era is not None:
        m &= era
    w = m & (d == sg); a = m & (d == -sg)
    nw, na = int(w.sum()), int(a.sum())
    if nw == 0 or na == 0:
        return None
    if light:
        return dict(w=dict(n=nw, mean=float(gn[w].mean())),
                    a=dict(n=na, mean=float(gn[a].mean())),
                    contrast=float(gn[w].mean() - gn[a].mean()), contrast_trim=np.nan,
                    n_w=nw, n_a=na, g1=None)
    W, A = stats(gn[w]), stats(gn[a])
    out = dict(w=W, a=A, contrast=W["mean"] - A["mean"], contrast_trim=W["trim"] - A["trim"],
               n_w=W["n"], n_a=A["n"])
    out["g1"] = {}
    for nm, sv, dv in (("up-up", 1, 1), ("dn-dn", -1, -1), ("up-dn", 1, -1), ("dn-up", -1, 1)):
        k = m & (sg == sv) & (d == dv)
        out["g1"][nm] = stats(gn[k]) if k.sum() else dict(n=0, mean=np.nan)
    return out


def pooled(R, roots, thr, H, pct_of=None, sg_of=None, era=None, weighted=False, light=False):
    cs, ts, ws, as_, nw, na, per = [], [], [], [], 0, 0, {}
    for r in roots:
        st = R[r]
        p = st["pct"] if pct_of is None else pct_of[r]
        s = st["sg"] if sg_of is None else sg_of[r]
        c = cell(st["gn"][H], st["d"], p, s, thr, era=era, light=light)
        if c is None or min(c["n_w"], c["n_a"]) < MIN_ROOT:
            continue
        per[r] = c
        cs.append(c["contrast"]); ts.append(c["contrast_trim"])
        ws.append(c["w"]["mean"]); as_.append(c["a"]["mean"])
        nw += c["n_w"]; na += c["n_a"]
    if not cs or nw + na < MIN_CELL:
        return None
    wgt = np.array([per[r]["n_w"] + per[r]["n_a"] for r in per], float) if weighted else None
    avg = (lambda v: float(np.average(v, weights=wgt))) if weighted else (lambda v: float(np.mean(v)))
    return dict(contrast=avg(cs), contrast_trim=avg(ts), w_mean=avg(ws), a_mean=avg(as_),
                n_w=nw, n_a=na, roots=len(cs), per_root=per,
                sign_pos=int(sum(1 for v in cs if v > 0)), sign_n=len(cs))


def run():
    t0 = time.time(); rng = np.random.default_rng(SEED)
    print(f"D535 -- displacement per unit volume, RANKED\n      spec {SPEC} committed BEFORE this "
          f"ran; every rank is a TRAILING quantile; primary = top-decile CONTRAST\n")
    G = D531.load()
    B = pd.read_csv(REPO / "data" / "fixtures" / "fut_breadth_hourly.csv.gz",
                    dtype={"root": str, "day": str})
    R = {}; align = {}
    for r in PRIMARY + CONFIRM:
        g = G[G.root == r]
        if not len(g):
            print(f"  {r:<4} NOT IN THE FIXTURE -- skipped")
            continue
        first, last = D531.session_span(g)
        days, A = D531.grids(g)
        d, ent, _a, _b, _c = D533.features(A, first, last, OR_N)
        pct, sg, nclose = night_state(B, r, days)
        gd = {}; gn = {}
        for H in HORIZONS:
            gd[H], gn[H] = norm_pnl(A, d, ent, H, UPT[r])
        fo = A["open"][:, first]
        ok = np.isfinite(fo) & np.isfinite(nclose)
        rho = float(np.corrcoef(fo[ok], nclose[ok])[0, 1]) if ok.sum() > 10 else np.nan
        align[r] = dict(rho=rho, n=int(ok.sum()))
        era = np.array([str(x) >= ERA for x in days])
        R[r] = dict(A=A, d=d, ent=ent, pct=pct, sg=sg, gd=gd, gn=gn, days=days, era=era)
        top = np.isfinite(pct) & (pct >= BUCKETS["decile"])
        print(f"  {r:<4} sessions {len(d):,}  breaks {int((d!=0).sum()):,}  pct finite "
              f"{int(np.isfinite(pct).sum()):,}  top decile {int(top.sum()):,}  "
              f"align rho {rho:.4f}")
        assert rho > 0.99, f"[F] {r}: night close vs session open correlate at {rho:.4f}"
        assert top.sum() > 0, f"[COVERAGE] {r}: the top decile is empty"

    res = dict(spec="D535", commit=SPEC, align=align, cost=COST, upt=UPT)
    prim_roots = [r for r in PRIMARY if r in R]
    all_roots = [r for r in PRIMARY + CONFIRM if r in R]

    # ---------- the 6 declared cells, on the primary four
    print(f"\n  THE 6 DECLARED POOLED CELLS -- equal-weighted over {prim_roots}, sigma units")
    print(f"  {'bucket':<9}{'H':>5}{'n WITH':>8}{'n AGST':>8}{'mean W':>9}{'mean A':>9}"
          f"{'CONTRAST':>10}{'trim':>9}{'p95':>9}{'clears':>8}")
    obs = {}
    for bname, thr in BUCKETS.items():
        for H in HORIZONS:
            c = pooled(R, prim_roots, thr, H)
            if c is None:
                print(f"  {bname:<9}{H*5:>5}   under the {MIN_CELL}-trade floor, NOT SCORED")
                continue
            obs[f"{bname}-H{H}"] = c
    assert f"decile-H{PRIMARY_H}" in obs, "[COVERAGE] the PRIMARY cell was not scored"

    offs = {r: rng.integers(1, len(R[r]["d"]), size=N_DRAWS) for r in R}
    draws = {k: np.empty(N_DRAWS) for k in obs}
    dec_draws = np.empty(N_DRAWS)
    DECS = [round(0.1 * i, 2) for i in range(10)]
    for i in range(N_DRAWS):
        po = {r: np.roll(R[r]["pct"], int(offs[r][i])) for r in R}
        so = {r: np.roll(R[r]["sg"], int(offs[r][i])) for r in R}
        for k in obs:
            b, hs = k.rsplit("-H", 1)
            c = pooled(R, prim_roots, BUCKETS[b], int(hs), pct_of=po, sg_of=so, light=True)
            draws[k][i] = c["contrast"] if c is not None else np.nan
        prof = []
        for lo in DECS:
            c = pooled(R, prim_roots, lo, PRIMARY_H, pct_of=po, sg_of=so, light=True)
            prof.append(c["contrast"] if c is not None else np.nan)
        dec_draws[i] = spearman(np.arange(10.0), np.array(prof))

    for k, c in obs.items():
        dd = draws[k]
        c["null_p50"] = float(np.nanmedian(dd)); c["null_p95"] = float(np.nanquantile(dd, 0.95))
        c["clears"] = bool(c["contrast"] > c["null_p95"])
        b, hs = k.rsplit("-H", 1)
        print(f"  {b:<9}{int(hs)*5:>5}{c['n_w']:>8,}{c['n_a']:>8,}{c['w_mean']:>+9.4f}"
              f"{c['a_mean']:>+9.4f}{c['contrast']:>+10.4f}{c['contrast_trim']:>+9.4f}"
              f"{c['null_p95']:>+9.4f}{('YES' if c['clears'] else 'no'):>8}")
    res["cells"] = {k: {kk: vv for kk, vv in v.items() if kk != "per_root"} for k, v in obs.items()}

    p = obs[f"decile-H{PRIMARY_H}"]
    res["primary"] = {k: v for k, v in p.items() if k != "per_root"}
    print(f"\n  PRIMARY  top decile, {PRIMARY_H*5} min: contrast {p['contrast']:+.4f} sigma "
          f"(WITH {p['w_mean']:+.4f} vs AGAINST {p['a_mean']:+.4f}) against null p50 "
          f"{p['null_p50']:+.4f} / p95 {p['null_p95']:+.4f} -> "
          f"{'CLEARS' if p['clears'] else 'INSIDE the null'}")

    keys = sorted(obs)
    M = np.nanmax(np.column_stack([draws[k] - np.nanmedian(draws[k]) for k in keys]), axis=1)
    best = max(keys, key=lambda k: obs[k]["contrast"])
    fp95 = float(np.nanquantile(M, 0.95))
    res["family"] = dict(n_cells=len(keys), p95=fp95, observed_max=obs[best]["contrast"],
                         argmax=best, clears=bool(obs[best]["contrast"] > fp95))
    f = res["family"]
    print(f"  N2 FAMILY over {f['n_cells']} declared cells: best {f['observed_max']:+.4f} "
          f"({f['argmax']}) against p95 {fp95:+.4f} -> {'CLEARS' if f['clears'] else 'INSIDE'}")

    # ---------- G1: the four-way decomposition, and P-5
    print(f"\n  G1 -- the four cells the WITH/AGAINST average is made of (primary cell)")
    print(f"  {'night-break':<13}{'n':>7}{'mean':>10}{'median':>10}   what it is")
    WHAT = {"up-up": "short covering", "dn-dn": "long liquidation",
            "up-dn": "fading an up night", "dn-up": "fading a down night"}
    g1 = {}
    for nm in ("up-up", "dn-dn", "up-dn", "dn-up"):
        vals, ns = [], 0
        for r in prim_roots:
            c = p["per_root"].get(r)
            if c and c["g1"][nm]["n"] >= 10:
                vals.append(c["g1"][nm]["mean"]); ns += c["g1"][nm]["n"]
        g1[nm] = dict(mean=float(np.mean(vals)) if vals else np.nan, n=ns, roots=len(vals))
        md = np.nanmedian([p["per_root"][r]["g1"][nm].get("median", np.nan)
                           for r in prim_roots if r in p["per_root"]])
        print(f"  {nm:<13}{ns:>7,}{g1[nm]['mean']:>+10.4f}{md:>+10.4f}   {WHAT[nm]}")
    res["g1"] = g1
    wsigns = [np.sign(g1[k]["mean"]) for k in ("up-up", "dn-dn")]
    asigns = [np.sign(g1[k]["mean"]) for k in ("up-dn", "dn-up")]
    p5_ok = bool(len(set(wsigns)) == 1 and len(set(asigns)) == 1)
    res["P5_interpretable"] = p5_ok
    print(f"  P-5: the two WITH cells {'AGREE' if len(set(wsigns))==1 else 'DISAGREE'} in sign and "
          f"the two AGAINST cells {'AGREE' if len(set(asigns))==1 else 'DISAGREE'} -> "
          f"{'interpretable' if p5_ok else 'POOLED CONTRAST IS UNINTERPRETABLE'}")

    # ---------- G2: per-root, ten markets
    print(f"\n  G2 -- per-root contrast, top decile, {PRIMARY_H*5} min, over TEN roots")
    wide = pooled(R, all_roots, BUCKETS["decile"], PRIMARY_H)
    print(f"  {'root':<6}{'n W':>7}{'n A':>7}{'contrast':>11}{'trim':>10}")
    pr = {}
    for r in all_roots:
        c = wide["per_root"].get(r) if wide else None
        if not c:
            print(f"  {r:<6}   under the per-root floor")
            continue
        pr[r] = dict(contrast=c["contrast"], trim=c["contrast_trim"], n_w=c["n_w"], n_a=c["n_a"])
        print(f"  {r:<6}{c['n_w']:>7,}{c['n_a']:>7,}{c['contrast']:>+11.4f}"
              f"{c['contrast_trim']:>+10.4f}")
    npos = sum(1 for v in pr.values() if v["contrast"] > 0)
    res["per_root_wide"] = pr
    res["sign_count"] = dict(positive=npos, total=len(pr))
    print(f"  SIGN COUNT: {npos} of {len(pr)} roots positive  (P-3 bar is 8 of 10)")

    # ---------- G3: the decile profile
    print(f"\n  G3 -- the decile profile, {PRIMARY_H*5} min, primary roots (NOT one bucket)")
    print(f"  {'pct >=':<8}{'n W':>7}{'n A':>7}{'contrast':>11}{'trim':>10}")
    prof = []
    for lo in DECS:
        c = pooled(R, prim_roots, lo, PRIMARY_H)
        prof.append(c["contrast"] if c else np.nan)
        if c:
            print(f"  {lo:<8.1f}{c['n_w']:>7,}{c['n_a']:>7,}{c['contrast']:>+11.4f}"
                  f"{c['contrast_trim']:>+10.4f}")
    rho_d = spearman(np.arange(10.0), np.array(prof))
    p95_d = float(np.nanquantile(dec_draws, 0.95))
    res["monotone"] = dict(spearman=rho_d, p95=p95_d, clears=bool(rho_d > p95_d), profile=prof)
    print(f"  P-2 monotone: Spearman(decile, contrast) {rho_d:+.3f} against N3 p95 {p95_d:+.3f} -> "
          f"{'CLEARS' if rho_d > p95_d else 'INSIDE'}")

    # ---------- G5: era
    print(f"\n  G5 -- the primary cell by era")
    eras = {}
    for nm, sel in (("2016-2019", False), ("2020-2023", True)):
        e = {r: (R[r]["era"] == sel) for r in prim_roots}
        c = pooled(R, prim_roots, BUCKETS["decile"], PRIMARY_H, era=None) if False else None
        cc = pooled_era(R, prim_roots, BUCKETS["decile"], PRIMARY_H, e)
        eras[nm] = cc
        if cc:
            print(f"    {nm}  n {cc['n_w']:,}/{cc['n_a']:,}  contrast {cc['contrast']:+.4f}  "
                  f"trim {cc['contrast_trim']:+.4f}")
        else:
            print(f"    {nm}  under the floor")
    res["eras"] = eras

    res["predictions"] = dict(
        P1=dict(value=p["contrast"], holds=bool(p["contrast"] > 0 and p["clears"])),
        P2=dict(value=rho_d, holds=bool(rho_d > p95_d)),
        P3=dict(positive=npos, total=len(pr), holds=bool(npos >= 8)),
        P4=dict(inverted=bool(p["contrast"] <= 0)),
        P5=dict(interpretable=p5_ok))
    res["verdict"] = dict(primary=p["clears"], family=f["clears"],
                          pass_all=bool(p["clears"] and f["clears"] and p["contrast"] > 0 and p5_ok))
    print(f"\n  DECLARED RULE: contrast > 0, clears N1, family clears N2 (and P-5 interpretable) -> "
          f"{'PASS' if res['verdict']['pass_all'] else 'DOES NOT PASS'}")
    res["component"] = component(R, prim_roots)
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"\nwrote {OUT.relative_to(REPO)} in {(time.time()-t0)/60:.1f} min")


def pooled_era(R, roots, thr, H, eras):
    cs, ts, nw, na = [], [], 0, 0
    for r in roots:
        st = R[r]
        c = cell(st["gn"][H], st["d"], st["pct"], st["sg"], thr, era=eras[r])
        if c is None or min(c["n_w"], c["n_a"]) < MIN_ROOT:
            continue
        cs.append(c["contrast"]); ts.append(c["contrast_trim"]); nw += c["n_w"]; na += c["n_a"]
    if not cs:
        return None
    return dict(contrast=float(np.mean(cs)), contrast_trim=float(np.mean(ts)), n_w=nw, n_a=na,
                roots=len(cs))


def spearman(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 4:
        return float("nan")
    ra = pd.Series(a[ok]).rank().to_numpy(); rb = pd.Series(b[ok]).rank().to_numpy()
    return float(np.corrcoef(ra, rb)[0, 1])


def component(R, roots):
    """The WITH arm at minimum size. THE DUTY CYCLE IS READ BEFORE ANY SHARPE -- D534's line failed
    on 7 trades a year and no Sharpe at that count means anything."""
    print(f"\n  COMPONENT LINE -- the WITH arm, top decile, {PRIMARY_H*5} min, in dollars")
    print(f"  {'root':<5}{'size':<6}{'trades':>8}{'per yr':>8}{'gross$':>9}{'net$':>9}{'hit':>8}"
          f"{'dayS':>8}{'netSR':>8}{'SE':>7}{'skew':>7}  C-a C-c C-d")
    K8 = D533.ledger_series(); out = {}; book = None
    for r in roots:
        st = R[r]
        m = (np.isfinite(st["gd"][PRIMARY_H]) & np.isfinite(st["pct"]) & (st["d"] != 0)
             & (st["pct"] >= BUCKETS["decile"]) & (st["sg"] != 0) & (st["d"] == st["sg"]))
        if m.sum() < 30:
            continue
        yrs = len(set(str(x)[:4] for x in st["days"]))
        gs = np.where(m, np.nan_to_num(st["gd"][PRIMARY_H]), 0.0)
        ns = np.where(m, gs - COST[r], 0.0)
        S = pd.Series(ns, index=st["days"])
        sr, se = D533.sharpe(ns); sd = float(np.std(ns, ddof=1))
        sk = float(pd.Series(ns).skew())
        rho = float("nan")
        if K8 is not None:
            j = pd.concat([S.rename("a"), K8.rename("b")], axis=1).dropna()
            if len(j) > 60:
                rho = float(j["a"].corr(j["b"]))
        out[r] = dict(trades=int(m.sum()), per_year=float(m.sum() / yrs),
                      gross_per_trade=float(np.mean(st["gd"][PRIMARY_H][m])),
                      net_per_trade=float(np.mean(st["gd"][PRIMARY_H][m] - COST[r])),
                      hit=float((st["gd"][PRIMARY_H][m] - COST[r] > 0).mean()), daily_sd=sd,
                      net_sharpe=sr, sharpe_se=se, skew=sk, rho_k8=rho,
                      C_a=bool(sr > 0.5), C_c=bool(sk >= -0.5), C_d=bool(sd <= 500.0))
        book = S if book is None else book.add(S, fill_value=0.0)
        v = out[r]
        print(f"  {r:<5}{'':<6}{v['trades']:>8,}{v['per_year']:>8.0f}{v['gross_per_trade']:>+9.2f}"
              f"{v['net_per_trade']:>+9.2f}{100*v['hit']:>7.1f}%{sd:>8.0f}{sr:>+8.2f}{se:>7.2f}"
              f"{sk:>+7.2f}   {'Y' if v['C_a'] else 'n'}   {'Y' if v['C_c'] else 'n'}   "
              f"{'Y' if v['C_d'] else 'n'}")
    if book is not None:
        bs, bse = D533.sharpe(book.to_numpy())
        out["BOOK"] = dict(net_sharpe=bs, sharpe_se=bse, daily_sd=float(book.std(ddof=1)))
        print(f"  {'BOOK':<5}{'1 each':<6}{'':>8}{'':>8}{'':>9}{'':>9}{'':>8}"
              f"{out['BOOK']['daily_sd']:>8.0f}{bs:>+8.2f}{bse:>7.2f}")
    return out


def selftest():
    rs = np.random.default_rng(11)
    print("== [X] the trailing rank EXCLUDES the current value from its own window")
    v = np.arange(400.0)
    p = trailing_pct(v)
    assert not np.isfinite(p[:RANK_MIN]).any(), "the warm-up must be NaN"
    assert np.all(p[RANK_MIN:] == 1.0), "a strictly rising series must rank 1.0 against its past"
    big = v.copy(); big[300] = 1e9
    assert trailing_pct(big)[300] == 1.0 and trailing_pct(big)[301] < 1.0, \
        "[X] a spike must rank high on its own day and push the NEXT day down -- not the reverse"
    print(f"   ok: warm-up NaN, rising series ranks 1.0, a spike does not rank ITSELF via the future")

    print("== [LAG] a whole-sample quantile would LEAK; the trailing one must differ from it")
    y = rs.normal(size=400); y[350:] += 6.0          # a regime shift late in the sample
    tp = trailing_pct(y)
    whole = pd.Series(y).rank(pct=True).to_numpy()
    early = np.isfinite(tp) & (np.arange(400) < 340)
    assert np.nanmean(tp[early]) > np.nanmean(whole[early]) + 0.05, (
        "a late regime shift must depress the WHOLE-SAMPLE rank of early sessions but not the "
        "trailing rank -- if these agree the causality fix is not doing anything")
    print(f"   ok: trailing mean rank {np.nanmean(tp[early]):.3f} vs whole-sample "
          f"{np.nanmean(whole[early]):.3f} on the pre-shift era")

    print("== [SIGN] WITH wins -> positive contrast; flipping the night sign inverts it")
    m = 600
    d = rs.choice([-1.0, 1.0], size=m)
    sg = np.where(rs.random(m) < 0.5, d, -d)
    gn = np.where(d == sg, +2.0, -2.0)
    pct = np.ones(m)
    c = cell(gn, d, pct, sg, 0.9)
    assert abs(c["contrast"] - 4.0) < 1e-9, f"expected +4, got {c['contrast']}"
    c2 = cell(gn, d, pct, -sg, 0.9)
    assert abs(c2["contrast"] + 4.0) < 1e-9, f"[X] flipping must invert, got {c2['contrast']}"
    print(f"   ok: {c['contrast']:+.1f} / inverted {c2['contrast']:+.1f}")

    print("== [G1] the four-way decomposition must SUM back to the pooled means")
    nw = c["g1"]["up-up"]["n"] + c["g1"]["dn-dn"]["n"]
    na = c["g1"]["up-dn"]["n"] + c["g1"]["dn-up"]["n"]
    assert nw == c["n_w"] and na == c["n_a"], f"G1 must partition WITH/AGAINST, {nw}/{na}"
    print(f"   ok: G1 partitions {nw} WITH and {na} AGAINST exactly")

    print("== [G4] a planted TAIL must move the mean and leave the trimmed mean alone")
    base = np.zeros(1000) + 1.0
    s0 = stats(base)
    base[0] = 1e6
    s1 = stats(base)
    assert s1["mean"] > 100, "the mean must absorb the tail"
    assert abs(s1["trim"] - 1.0) < 1e-9, f"the trim must reject it, got {s1['trim']}"
    print(f"   ok: mean {s0['mean']:.2f} -> {s1['mean']:.1f}, trim stays {s1['trim']:.2f}")

    print("== [G3] a MONOTONE planted effect must be recovered by the decile profile")
    prof = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
    assert abs(spearman(np.arange(10.0), prof) - 1.0) < 1e-9, "a perfect ramp must read +1"
    assert abs(spearman(np.arange(10.0), prof[::-1]) + 1.0) < 1e-9, "reversed must read -1"
    print(f"   ok: ramp +1.000, reversed -1.000")

    print("== [EDGE] the night's open is the root's OWN first populated hour, not h18")
    n3 = 4
    t3 = pd.DataFrame({"root": ["Z"] * n3, "day": [f"d{i}" for i in range(n3)]})
    for s in NIGHT:
        t3[f"{s}_o"] = np.nan; t3[f"{s}_c"] = np.nan
    t3.loc[:, "h20_o"] = 10.0                       # a grain: nothing before h20
    t3.loc[:, "h08_c"] = 11.0
    t3.loc[2, "h08_c"] = np.nan; t3.loc[2, "h07_c"] = 12.0   # a session missing its last hour
    o3 = _edge(t3, "o"); c3 = _edge(t3, "c", last=True)
    assert np.all(o3 == 10.0), f"the open must come from h20 when h18/h19 are empty, got {o3}"
    assert c3[0] == 11.0 and c3[2] == 12.0, f"the close must fall back to h07, got {c3}"
    t3.loc[:, "h18_o"] = 9.0
    assert np.all(_edge(t3, "o") == 9.0), "[X] when h18 IS populated it must win over h20"
    print(f"   ok: opens {o3[:1]} from h20, close falls back to h07, and h18 wins when present")

    print("== [QTY] the bucket threshold must BIND")
    assert cell(gn, d, np.zeros(m), sg, 0.9) is None, "pct 0 must select nothing at the decile"
    assert cell(gn, d, np.full(m, 0.7), sg, 2 / 3) is not None, "0.7 must pass the tercile"
    print(f"   ok: the decile and tercile thresholds each bind")

    print("\nSELFTEST PASSED")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--run", action="store_true"); g.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    run() if a.run else selftest()
