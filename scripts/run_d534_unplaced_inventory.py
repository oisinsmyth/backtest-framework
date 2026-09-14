"""D534 -- C2 rebuilt: UNPLACED inventory is signed, and the statistic is the GROSS MEAN PER TRADE.

Spec committed in 610cb2e BEFORE this file (R8). In sample 2016-01-04..2023-12-29; the 2024+ slice is
RESERVED AND NOT READ. Nothing admitted (R15).

    python scripts/run_d534_unplaced_inventory.py --selftest
    python scripts/run_d534_unplaced_inventory.py --run       # -> data/d534_unplaced_inventory.json

The gate: price displaced materially overnight (|z| > 1 on its own trailing sd) AND cheaply (night
volume below its own trailing mean). Whoever took the other side holds it unwillingly and unwinds
when depth arrives at the open -- so the day should continue in the direction the night already
moved. PRIMARY is the CONTRAST mean(WITH) - mean(AGAINST) in per-root sigma units.
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

OUT = REPO / "data" / "d534_unplaced_inventory.json"
SPEC = "610cb2e"
OR_N = 6                                  # D531's opening range, unchanged
CAND = ["CL", "GC", "SI", "NG"]
NIGHT = [f"h{h:02d}" for h in list(range(18, 24)) + list(range(0, 9))]
TREND_N, MIN_PER = 50, 25                 # min_periods MUST be below the window
Z_MIN = 1.0                               # "materially displaced", declared in the pre-reg
HORIZONS = [6, 12, 24]                    # 30 / 60 / 120 minutes; the PRIMARY is 12
PRIMARY_H = 12
GATES = ["drift_thin", "drift"]
MIN_CELL = 200                            # a POOLED cell under this is not scored
MIN_ROOT = 25                             # a root contributes to the equal weight above this
N_DRAWS = 1000
SEED = 20260915
COST = D533.COST
MINSIZE = D533.MINSIZE


def night_state(B, root, days):
    """z = overnight log return over its own TRAILING sd, and `thin` = night volume below its own
    TRAILING mean. Both trailing statistics are SHIFTED so the current session cannot enter its own
    reference -- the return itself is known at h08, the reference must not be."""
    t = B[B.root == root].sort_values("day")
    o = t["h18_o"].to_numpy(float)
    c = t["h08_c"].to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        lr = np.where((o > 0) & (c > 0), np.log(c / o), np.nan)
    vcols = [f"{s}_v" for s in NIGHT if f"{s}_v" in t.columns]
    vol = np.nansum(t[vcols].to_numpy(float), axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        lv = np.where(vol > 0, np.log(vol), np.nan)
    s_lr = pd.Series(lr); s_lv = pd.Series(lv)
    sd = s_lr.rolling(TREND_N, min_periods=MIN_PER).std().shift(1)
    mu = s_lv.rolling(TREND_N, min_periods=MIN_PER).mean().shift(1)
    z = np.where(np.asarray(sd) > 0, lr / np.asarray(sd), np.nan)
    thin = np.asarray(s_lv < mu)
    idx = t["day"].to_numpy()
    zz = pd.Series(z, index=idx).reindex(days).to_numpy(float)
    tt = pd.Series(thin, index=idx).reindex(days).fillna(False).to_numpy(bool)
    nc = pd.Series(c, index=idx).reindex(days).to_numpy(float)
    return zz, tt, nc


def trades(A, d, ent, first, H):
    """Gross DOLLARS per session at minimum tradable size, NaN where no trade. Signed by the break."""
    O, C = A["open"], A["close"]
    g = np.full(len(d), np.nan)
    last = A["open"].shape[1] - 1
    for s in range(len(d)):
        if d[s] == 0 or ent[s] < 0:
            continue
        xb = ent[s] + H
        if xb > last:
            continue
        mv = C[s, xb] - O[s, ent[s]]
        if np.isfinite(mv):
            g[s] = d[s] * mv                      # in POINTS; scaled to dollars by the caller
    return g


def cell(g, d, z, thin, gate):
    """mean(WITH the night drift) - mean(AGAINST it) on the gated sessions. Returns None if a side
    is empty -- the caller decides whether the count clears the declared floor."""
    m = np.isfinite(g) & np.isfinite(z) & (d != 0)
    m &= np.abs(z) > Z_MIN
    if gate == "drift_thin":
        m &= thin
    sg = np.sign(z)
    w = m & (d == sg); a = m & (d == -sg)
    if w.sum() == 0 or a.sum() == 0:
        return None
    return dict(w_mean=float(g[w].mean()), a_mean=float(g[a].mean()),
                contrast=float(g[w].mean() - g[a].mean()),
                n_w=int(w.sum()), n_a=int(a.sum()))


def pooled(R, gate, H, z_of=None, thin_of=None):
    """Equal-weighted over roots in PER-ROOT SIGMA UNITS -- a dollar pool is an SI pool."""
    cs = []; nw = 0; na = 0; wm = []; am = []
    for r, st in R.items():
        z = st["z"] if z_of is None else z_of[r]
        th = st["thin"] if thin_of is None else thin_of[r]
        c = cell(st["gn"][H], st["d"], z, th, gate)
        if c is None or min(c["n_w"], c["n_a"]) < MIN_ROOT:
            continue
        cs.append(c["contrast"]); wm.append(c["w_mean"]); am.append(c["a_mean"])
        nw += c["n_w"]; na += c["n_a"]
    if not cs or nw + na < MIN_CELL:
        return None
    return dict(contrast=float(np.mean(cs)), w_mean=float(np.mean(wm)), a_mean=float(np.mean(am)),
                n_w=nw, n_a=na, roots=len(cs))


def run():
    t0 = time.time(); rng = np.random.default_rng(SEED)
    print(f"D534 -- unplaced inventory, SIGNED\n      spec {SPEC} committed BEFORE this ran; "
          f"statistic = GROSS MEAN PER TRADE in per-root sigma units; primary = the CONTRAST\n")
    G = D531.load()
    B = pd.read_csv(REPO / "data" / "fixtures" / "fut_breadth_hourly.csv.gz",
                    dtype={"root": str, "day": str})
    R = {}; align = {}
    for r in CAND:
        g = G[G.root == r]
        if not len(g):
            continue
        first, last = D531.session_span(g)
        days, A = D531.grids(g)
        d, ent, _c1, _c4, _pm = D533.features(A, first, last, OR_N)
        z, thin, nclose = night_state(B, r, days)
        upt = MINSIZE[r][1]
        gn = {}; gd = {}
        for H in HORIZONS:
            pts = trades(A, d, ent, first, H)
            usd = pts * upt
            sd = np.nanstd(usd[np.isfinite(usd)], ddof=1)
            gd[H] = usd
            gn[H] = usd / sd if sd > 0 else usd * np.nan
        # [F] PREMISE 1 -- the night must PRECEDE the scored session
        fo = A["open"][:, first]
        ok = np.isfinite(fo) & np.isfinite(nclose)
        rho = float(np.corrcoef(fo[ok], nclose[ok])[0, 1])
        gap = float(np.nanmedian(np.abs(fo[ok] - nclose[ok])))
        rngmed = float(np.nanmedian(np.nanmax(A["high"], axis=1) - np.nanmin(A["low"], axis=1)))
        align[r] = dict(rho=rho, med_gap=gap, med_session_range=rngmed)
        R[r] = dict(A=A, d=d, ent=ent, first=first, z=z, thin=thin, gn=gn, gd=gd, days=days,
                    sd={H: float(np.nanstd(gd[H][np.isfinite(gd[H])], ddof=1)) for H in HORIZONS})
        gated = np.isfinite(z) & (np.abs(z) > Z_MIN)
        print(f"  {r:<4} sessions {len(d):,}  breaks {int((d!=0).sum()):,}  "
              f"z finite {int(np.isfinite(z).sum()):,}  |z|>1 {int(gated.sum()):,} "
              f"({100*gated.mean():.0f}%)  thin {100*thin.mean():.0f}%  "
              f"both {int((gated & thin).sum()):,}")

    print(f"\n  [F] PREMISE 1 -- the night PRECEDES the session it is scored against")
    for r, v in align.items():
        print(f"    {r:<4} corr(h08 close, session first open) {v['rho']:.4f}   median gap "
              f"{v['med_gap']:.4f} against a median session range of {v['med_session_range']:.4f}")
        assert v["rho"] > 0.99, (f"[F] {r}: the night close and the session open correlate at "
                                 f"{v['rho']:.4f} -- the night is not the one preceding this session")
        assert v["med_gap"] < v["med_session_range"], f"[F] {r}: the overnight gap exceeds a session"

    res = dict(spec="D534", commit=SPEC, align=align, cost=COST, cells={}, per_root={})

    # ---- the unfiltered reference, for P-2
    ref = {}
    for H in HORIZONS:
        v = [float(np.nanmean(R[r]["gn"][H])) for r in R]
        vd = [float(np.nanmean(R[r]["gd"][H])) for r in R]
        ref[H] = dict(sigma=float(np.mean(v)), usd_per_root=dict(zip(R, vd)))
    res["unfiltered"] = ref
    print(f"\n  UNFILTERED break, gross mean per trade (the P-2 reference)")
    for H in HORIZONS:
        print(f"    H{H*5:<4} {ref[H]['sigma']:+.4f} sigma   " +
              "  ".join(f"{r} ${v:+.2f}" for r, v in ref[H]['usd_per_root'].items()))

    # ---- observed cells
    print(f"\n  THE 6 DECLARED POOLED CELLS -- equal-weighted over {list(R)}, sigma units")
    print(f"  {'gate':<11}{'H':>5}{'n WITH':>9}{'n AGST':>9}{'mean W':>9}{'mean A':>9}"
          f"{'CONTRAST':>10}{'p95':>9}{'clears':>8}")
    obs = {}
    for gate in GATES:
        for H in HORIZONS:
            c = pooled(R, gate, H)
            if c is None:
                print(f"  {gate:<11}{H*5:>5}  -- under the {MIN_CELL}-trade floor, NOT SCORED")
                continue
            obs[f"{gate}-H{H}"] = c
    assert obs, "[COVERAGE] the declared gate selected nothing -- stop here, not four screens later"
    assert f"drift_thin-H{PRIMARY_H}" in obs, "[COVERAGE] the PRIMARY cell was not scored"

    # ---- N1 / N2: rotate the night state (z, thin) as a COUPLED PAIR against the day that follows
    offs = {r: rng.integers(1, len(R[r]["d"]), size=N_DRAWS) for r in R}
    draws = {k: np.empty(N_DRAWS) for k in obs}
    for i in range(N_DRAWS):
        zo = {r: np.roll(R[r]["z"], int(offs[r][i])) for r in R}
        to = {r: np.roll(R[r]["thin"], int(offs[r][i])) for r in R}
        for k in obs:
            gate, hs = k.split("-H")
            c = pooled(R, gate, int(hs), z_of=zo, thin_of=to)
            draws[k][i] = c["contrast"] if c is not None else np.nan
    for k, c in obs.items():
        dd = draws[k]
        c["null_p50"] = float(np.nanmedian(dd)); c["null_p95"] = float(np.nanquantile(dd, 0.95))
        c["clears"] = bool(c["contrast"] > c["null_p95"])
        gate, hs = k.split("-H")
        print(f"  {gate:<11}{int(hs)*5:>5}{c['n_w']:>9,}{c['n_a']:>9,}{c['w_mean']:>+9.4f}"
              f"{c['a_mean']:>+9.4f}{c['contrast']:>+10.4f}{c['null_p95']:>+9.4f}"
              f"{('YES' if c['clears'] else 'no'):>8}")
    res["cells"] = obs

    p = obs[f"drift_thin-H{PRIMARY_H}"]
    res["primary"] = dict(key=f"drift_thin-H{PRIMARY_H}", **{k: p[k] for k in
                          ("contrast", "w_mean", "a_mean", "n_w", "n_a", "null_p50", "null_p95",
                           "clears")})
    print(f"\n  PRIMARY  drift+thin, {PRIMARY_H*5} min: contrast {p['contrast']:+.4f} sigma "
          f"(WITH {p['w_mean']:+.4f} vs AGAINST {p['a_mean']:+.4f}) against a null p50 "
          f"{p['null_p50']:+.4f} / p95 {p['null_p95']:+.4f} -> "
          f"{'CLEARS' if p['clears'] else 'INSIDE the null'}")

    keys = sorted(obs)
    L = min(len(draws[k]) for k in keys)
    M = np.nanmax(np.column_stack([draws[k][:L] - np.nanmedian(draws[k][:L]) for k in keys]), axis=1)
    best = max(keys, key=lambda k: obs[k]["contrast"])
    fp95 = float(np.nanquantile(M, 0.95))
    res["family"] = dict(n_cells=len(keys), p95=fp95, observed_max=obs[best]["contrast"],
                         argmax=best, clears=bool(obs[best]["contrast"] > fp95))
    f = res["family"]
    print(f"  N2 FAMILY over {f['n_cells']} declared cells: best {f['observed_max']:+.4f} "
          f"({f['argmax']}) against p95 {fp95:+.4f} -> {'CLEARS' if f['clears'] else 'INSIDE'}")

    # ---- predictions
    print(f"\n  PREDICTIONS")
    p2 = p["w_mean"] - ref[PRIMARY_H]["sigma"]
    d_only = obs.get(f"drift-H{PRIMARY_H}")
    p3 = (p["contrast"] - d_only["contrast"]) if d_only else float("nan")
    res["predictions"] = dict(
        P1=dict(value=p["contrast"], holds=bool(p["contrast"] > 0 and p["clears"])),
        P2=dict(value=p2, holds=bool(p2 > 0)),
        P3=dict(value=p3, holds=bool(p3 > 0)),
        P4=dict(inverted=bool(p["a_mean"] >= p["w_mean"])))
    print(f"    P-1 contrast > 0 and clears      {p['contrast']:+.4f}  -> "
          f"{'HOLDS' if res['predictions']['P1']['holds'] else 'FAILS'}")
    print(f"    P-2 WITH beats the unfiltered    {p2:+.4f}  -> "
          f"{'HOLDS' if p2 > 0 else 'FAILS'}")
    print(f"    P-3 thin gate ADDS over drift    {p3:+.4f}  -> "
          f"{'HOLDS -- an inventory story' if p3 > 0 else 'FAILS -- this is plain overnight momentum'}")
    print(f"    P-4 falsifier (AGAINST >= WITH)  -> "
          f"{'INVERTED' if res['predictions']['P4']['inverted'] else 'not inverted'}")

    res["verdict"] = dict(primary=p["clears"], family=f["clears"],
                          pass_all=bool(p["clears"] and f["clears"] and p["contrast"] > 0))
    print(f"\n  DECLARED RULE: contrast > 0, clears N1, family clears N2 -> "
          f"{'PASS' if res['verdict']['pass_all'] else 'DOES NOT PASS'}")

    res["component"] = component(R)
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"\nwrote {OUT.relative_to(REPO)} in {(time.time()-t0)/60:.1f} min")


def component(R):
    """The component line -- required whatever the verdict. The tradeable arm is WITH only, at
    minimum size, under the cost that size pays, in DOLLARS."""
    print(f"\n  COMPONENT LINE -- the WITH arm at minimum size, {PRIMARY_H*5} min, in dollars")
    print(f"  {'root':<5}{'size':<6}{'trades':>8}{'gross$':>9}{'net$':>9}{'hit':>8}{'dayS':>8}"
          f"{'netSR':>8}{'SE':>7}{'skew':>7}  C-a C-c C-d")
    K8 = D533.ledger_series(); out = {}; book = None
    for r, st in R.items():
        z, thin, d = st["z"], st["thin"], st["d"]
        m = np.isfinite(st["gd"][PRIMARY_H]) & np.isfinite(z) & (d != 0)
        m &= (np.abs(z) > Z_MIN) & thin & (d == np.sign(z))
        if m.sum() < 30:            # the gate is thin; the line is reported WITH its n, not withheld
            continue
        gs = np.where(m, np.nan_to_num(st["gd"][PRIMARY_H]), 0.0)
        ns = np.where(m, gs - COST[r], 0.0)
        S = pd.Series(ns, index=st["days"])
        sr, se = D533.sharpe(ns); gsr, _ = D533.sharpe(gs)
        sd = float(np.std(ns, ddof=1)); sk = float(pd.Series(ns).skew())
        rho = float("nan")
        if K8 is not None:
            j = pd.concat([S.rename("a"), K8.rename("b")], axis=1).dropna()
            if len(j) > 60:
                rho = float(j["a"].corr(j["b"]))
        out[r] = dict(sym=MINSIZE[r][0], trades=int(m.sum()),
                      gross_per_trade=float(np.mean(st["gd"][PRIMARY_H][m])),
                      net_per_trade=float(np.mean(st["gd"][PRIMARY_H][m] - COST[r])),
                      hit=float((st["gd"][PRIMARY_H][m] - COST[r] > 0).mean()), daily_sd=sd,
                      net_sharpe=sr, gross_sharpe=gsr, sharpe_se=se, skew=sk, rho_k8=rho,
                      C_a=bool(sr > 0.5), C_c=bool(sk >= -0.5), C_d=bool(sd <= 500.0))
        book = S if book is None else book.add(S, fill_value=0.0)
        v = out[r]
        print(f"  {r:<5}{v['sym']:<6}{v['trades']:>8,}{v['gross_per_trade']:>+9.2f}"
              f"{v['net_per_trade']:>+9.2f}{100*v['hit']:>7.1f}%{sd:>8.0f}{sr:>+8.2f}{se:>7.2f}"
              f"{sk:>+7.2f}   {'Y' if v['C_a'] else 'n'}   {'Y' if v['C_c'] else 'n'}   "
              f"{'Y' if v['C_d'] else 'n'}")
    if book is not None:
        bs, bse = D533.sharpe(book.to_numpy()); bsd = float(book.std(ddof=1))
        bsk = float(pd.Series(book.to_numpy()).skew())
        out["BOOK"] = dict(net_sharpe=bs, sharpe_se=bse, daily_sd=bsd, skew=bsk)
        print(f"  {'BOOK':<5}{'1 each':<6}{'':>8}{'':>9}{'':>9}{'':>8}{bsd:>8.0f}{bs:>+8.2f}"
              f"{bse:>7.2f}{bsk:>+7.2f}")
    return out


def selftest():
    print("== [LAG] the night state for session D is derived from row D, in a SECOND implementation")
    days = np.array(["d0", "d1", "d2", "d3", "d4", "d5"])
    n = len(days)
    B = pd.DataFrame({"root": ["X"] * n, "day": days,
                      "h18_o": [100.0, 100, 100, 100, 100, 100],
                      "h08_c": [101.0, 99, 104, 100, 97, 100]})
    for s in NIGHT:
        B[f"{s}_v"] = 1.0
    z, thin, nc = night_state(B, "X", days)
    direct = np.log(B["h08_c"].to_numpy() / B["h18_o"].to_numpy())
    assert np.allclose(nc, B["h08_c"].to_numpy()), "the night close must come from the SAME row"
    fin = np.isfinite(z)
    if fin.any():
        assert np.all(np.sign(z[fin]) == np.sign(direct[fin])), "z must carry the row's own sign"
    print(f"   ok: night close aligned row-for-row; sign of z matches log(h08_c/h18_o)")

    print("== [X] shifting the night by ONE session must BREAK the alignment check")
    fo = np.array([101.0, 99, 104, 100, 97, 100])
    good = float(np.corrcoef(fo, nc)[0, 1])
    bad = float(np.corrcoef(fo[1:], nc[:-1])[0, 1])
    assert good > 0.99, f"the aligned pair must correlate above 0.99, got {good:.4f}"
    assert bad < 0.99, f"[X] the shifted pair must FAIL the same check, got {bad:.4f}"
    print(f"   ok: aligned {good:.4f} passes, shifted-by-one {bad:.4f} fails the same threshold")

    print("== [SIGN] a book where WITH always wins must give a POSITIVE contrast, and flipping "
          "the night sign must invert it")
    m = 400
    rs = np.random.default_rng(7)
    d = rs.choice([-1.0, 1.0], size=m)
    zz = np.where(rs.random(m) < 0.5, d * 2.0, -d * 2.0)      # half WITH, half AGAINST
    g = np.where(d == np.sign(zz), +10.0, -10.0)              # WITH wins, AGAINST loses
    th = np.ones(m, bool)
    c = cell(g, d, zz, th, "drift_thin")
    assert c["contrast"] == 20.0, f"WITH +10 against AGAINST -10 must contrast +20, got {c}"
    c2 = cell(g, d, -zz, th, "drift_thin")
    assert c2["contrast"] == -20.0, f"[X] flipping the night sign must invert it, got {c2}"
    print(f"   ok: contrast {c['contrast']:+.1f}, inverted {c2['contrast']:+.1f}, "
          f"n {c['n_w']}/{c['n_a']}")

    print("== [QTY] the gate must actually BIND -- |z| <= 1 and thick nights are excluded")
    zsmall = np.full(m, 0.5)
    assert cell(g, d, zsmall, th, "drift_thin") is None, "|z| <= 1 must select nothing"
    assert cell(g, d, zz, np.zeros(m, bool), "drift_thin") is None, "thick nights must be excluded"
    assert cell(g, d, zz, np.zeros(m, bool), "drift") is not None, "the drift-only gate ignores thin"
    print(f"   ok: the threshold and the thin gate each bind, and drift-only ignores thin")

    print("== [NULL] a rotation against an UNRELATED day must centre the contrast on zero")
    gr = rs.normal(0, 10, size=m)                             # no relationship to the night at all
    cs = []
    for i in range(300):
        k = int(rs.integers(1, m))
        c = cell(gr, d, np.roll(zz, k), np.roll(th, k), "drift_thin")
        if c:
            cs.append(c["contrast"])
    med = float(np.median(cs))
    assert abs(med) < 1.0, f"an unrelated night must centre near zero, got {med:+.3f}"
    print(f"   ok: null median {med:+.3f} on a book with no night relationship")

    print("== [WARMUP] the trailing reference is SHIFTED -- a session cannot enter its own sd")
    n2 = 80
    B2 = pd.DataFrame({"root": ["X"] * n2, "day": [f"d{i:03d}" for i in range(n2)],
                       "h18_o": 100.0, "h08_c": 100.0 * np.exp(rs.normal(0, 0.01, n2))})
    for s in NIGHT:
        B2[f"{s}_v"] = 1.0
    z2, _, _ = night_state(B2, "X", B2["day"].to_numpy())
    assert not np.isfinite(z2[:MIN_PER]).any(), (
        f"the first {MIN_PER} sessions cannot have a trailing sd; got "
        f"{int(np.isfinite(z2[:MIN_PER]).sum())} finite")
    assert np.isfinite(z2[MIN_PER + 2:]).any(), "z must become finite once the window fills"
    print(f"   ok: z is NaN through the warm-up and finite after it")

    print("\nSELFTEST PASSED")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--run", action="store_true"); g.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    run() if a.run else selftest()
