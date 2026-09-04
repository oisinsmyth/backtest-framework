"""D323 -- D290's shortlist, read at the width the book actually uses.

    uv run python scripts/run_d323_shortlist_at_operating_point.py --selftest
    uv run python scripts/run_d323_shortlist_at_operating_point.py [--draws 100]

PRE-REGISTERED AT `fee3b50`, committed before this file existed (R8).

Every candidate in D290 was scored at ITS OWN best cell -- N from 3 to 50, k from
1 to 40 -- and D293 chose between two of them at N=25, k=5. THE BOOK NOW RUNS AT
N_eff = 2, k = 5, AND NO CANDIDATE HAS BEEN READ THERE. Concentration selects on a
signal's RANK PROFILE, not its average: D301 measured edge per position falling
27.64 -> 11.27 bp from top-2 to top-19, so a candidate that ranks well averaged
over 25 names need not be the one that ranks well at positions 1 and 2.

HOW A SINGLE CANDIDATE IS BUILT. D295's `build_inputs` selects a 25-name gate with
the PRIMARY and then RE-RANKS inside it by the mean percentile of the PAIR -- that
composite is the confluence. A single candidate is the same construction with the
re-ranking removed: its own ordering supplies both the gate and the rank within
it, which is exactly what D293's "hist_L alone" row means.

ONLY THE GATE CHANGES PER CANDIDATE. `simulate` reads r1T, mkt, vxT and finT from
the cache and the ranking only through G, and all four are signal-independent --
so the D303 cache is built once and thirteen gates are swapped over it. The target
exit reads `vxT`, the excess vol, which is also signal-independent.

THE NULL ROTATES rankT IN TIME. That destroys the alignment between the ranking
and returns while preserving each name's score autocorrelation and each bar's gate
size exactly. A rank ROTATION WITHIN the gate (D300's null, `simulate`'s `shift`)
was rejected: `(rk + shift) % 25` admits only 24 distinct draws, so p floors at
0.04 and nothing could clear a multiplicity correction over 112 cells.

`k` IS SET BY PATCHING A MODULE GLOBAL, which is fragile, so assertion [3] checks
it BITES -- turnover must fall monotonically in k while the round trip does not
move (D296's structural finding).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


W = _load("d306", "run_d306_width_exits.py")
F = _load("d320", "run_d320_tilt_filters.py")
E, D, M, SP = W.E, W.D, W.M, W.SP
R = E.R
N_BASE = W.N_BASE

CANDS = ("price_log", "macd_hist", "rsi", "dist_52w_high", "on_persist", "rev_5",
         "choch_dist", "retrace_leg", "skew_63", "macd_line", "hist_L", "rev_21",
         "dist_lvn")
KS = (5, 10, 20, 40)
DEPTH = 2
DV_PCT = 28.0
PER_SHARE, CROSSINGS = 0.005, 4.0
ANN, SEED = 252.0, 20260904
OUT = REPO / "data" / "d323_shortlist.json"


# ---------------------------------------------------------------- primitives
def rank_single(z, base, cand, n, T):
    """(2, T, n) rank array for ONE candidate: its own order, gate and rank.

    D295's composite re-ranks the gate by a PAIR; a single candidate has no pair,
    so its position inside its own leg IS its rank. That is D293's "alone" row.
    """
    order, cnt, _ = R.ranked(z[cand], base)
    plan = R.LegPlan(order, cnt, N_BASE, T)
    bc = np.broadcast_to(plan.cols[None, :], plan.lo.shape)
    pos = np.broadcast_to(np.arange(N_BASE, dtype=np.int32)[:, None], plan.lo.shape)
    out = []
    for rows in (plan.lo, plan.hi):
        rk = np.full((n, T), n, dtype=np.int32)
        rk[rows.ravel(), bc.ravel()] = pos.ravel()
        out.append(rk)
    return np.ascontiguousarray(np.stack(out).transpose(0, 2, 1))


def gate_from(rankT, finT, keep=None):
    """W.build_gate's construction, from a SUPPLIED rankT and an optional filter."""
    T = rankT.shape[1]
    rows, rks, off = [], [], np.zeros((2, T + 1), np.int64)
    k = 0
    for side in (0, 1):
        for t in range(T):
            rk = rankT[side, t]
            m = (rk < N_BASE) & finT[t]
            if keep is not None:
                m = m & keep[t]
            g = np.flatnonzero(m)
            if g.size:
                g = g[np.argsort(rk[g], kind="stable")]
            rows.append(g.astype(np.int32))
            rks.append(rk[g].astype(np.int32))
            off[side, t] = k
            k += g.size
        off[side, T] = k
    return {"gateF": np.concatenate(rows).astype(np.int32),
            "gateR": np.concatenate(rks).astype(np.int32), "gateO": off}


def cell(A, G, k, HALF, CLOSE):
    """One book at k, costed per D318 with D321's [F] held-name turnover."""
    W.BASE_HOLD = k                       # patched; assertion [3] checks it bites
    res = W.simulate(A, G, DEPTH, True)
    ok = res["mask"]
    b = res["book"][ok]
    bars = b.size
    e = int(res["ent"][ok].sum())
    held = float(res["held"][ok].mean())
    if not res["trades"] or held <= 0 or bars < 100:
        return None
    hs, px = F.held_median(res, HALF), F.held_median(res, CLOSE)
    if not (np.isfinite(hs) and np.isfinite(px) and px > 0):
        return None
    rt = 4.0 * hs
    rtc = CROSSINGS * PER_SHARE / px * 1e4
    turn = e / held / bars
    g = float(b.mean()) * 1e4
    v = float(b.std(ddof=1)) * 1e4
    net = g - (rt + rtc) * turn
    eq = np.cumsum(b)
    return dict(gross_bp=g, vol_bp=v, net_bp=net, cost_bp=(rt + rtc) * turn,
                sharpe_net=net / v * np.sqrt(ANN) if v > 0 else 0.0,
                sharpe_gross=g / v * np.sqrt(ANN) if v > 0 else 0.0,
                turnover=turn, round_trip=rt, commission_rt=rtc,
                held_half_spread=hs, held_price=px, held_per_bar=held,
                fill=held / (2.0 * DEPTH),
                maxdd_bp=float(np.max(np.maximum.accumulate(eq) - eq)) * 1e4,
                entries=e, trades=len(res["trades"]), bars=bars)


def m_eff(Z):
    """Li-Ji and Cheverud-Nyholt effective test counts, as D321b established."""
    C = np.corrcoef(Z)
    ev = np.linalg.eigvalsh(C)[::-1]
    m = Z.shape[0]
    liji = float(sum((1.0 if e >= 1 else 0.0) + min(1.0, max(0.0, e - np.floor(e)))
                     for e in ev))
    nyh = float(1 + (m - 1) * (1 - np.var(ev, ddof=1) / m))
    return liji, nyh, float(np.median(C[np.triu_indices(m, 1)]))


def bh(ps, m, q=0.10):
    o = np.argsort(ps)
    hit = np.asarray(ps)[o] <= (np.arange(1, len(ps) + 1) / m) * q
    k = np.flatnonzero(hit).max() + 1 if hit.any() else 0
    rej = np.zeros(len(ps), bool)
    rej[o[:k]] = True
    return rej


# ---------------------------------------------------------------- assertions
def assertions(A, z, base, finT, HALF, CLOSE, n, T, d293, d306):
    print("\nASSERTIONS")

    # 1. THE INCUMBENT reproduces D306's N=2/target -- the cache and the
    #    simulator are the ones the published stack was scored on.
    W.BASE_HOLD = 5
    G0 = W.build_gate(A, verbose=False)
    r = W.simulate(A, G0, DEPTH, True)
    gg = float(r["book"][r["mask"]].mean()) * 1e4
    d = abs(gg - d306["N=2/target"]["gross_bp"])
    assert d < 1e-9, f"[1] the incumbent differs from D306 by {d:.2e} bp"

    # 1b. A SINGLE CANDIDATE'S GATE must be a real gate: 25 per side where the
    #     cross-section allows, and DIFFERENT from the composite's.
    rk = rank_single(z, base, "hist_L", n, T)
    Gh = gate_from(rk, finT)
    assert not np.array_equal(Gh["gateF"], G0["gateF"]), \
        "[1b] hist_L alone produces the composite's gate -- the re-ranking is " \
        "not being removed"
    sz = np.diff(Gh["gateO"][0])
    assert sz.max() == N_BASE, f"[1b] the gate never reaches {N_BASE}: {sz.max()}"
    print(f"    [1] the incumbent reproduces D306's N=2/target to {d:.1e} bp, and "
          f"a single candidate's gate is a real {N_BASE}-name gate DISTINCT from "
          f"the composite's")

    # 2. CAUSALITY -- rankT is lagged (R.ranked lags), and the null's rotation
    #    must move the book. R9 has fired three times here, twice on hist_L.
    rot = np.roll(rk, 501, axis=1)
    Gr = gate_from(rot, finT)
    assert not np.array_equal(Gr["gateF"], Gh["gateF"]), "[2] rotation is inert"
    c0 = cell(A, Gh, 5, HALF, CLOSE)
    c1 = cell(A, Gr, 5, HALF, CLOSE)
    assert abs(c0["gross_bp"] - c1["gross_bp"]) > 1e-9, "[2] same book"
    print(f"    [2] CAUSALITY: rotating rankT moves the book "
          f"({c0['gross_bp']:+.2f} -> {c1['gross_bp']:+.2f} bp gross)")

    # 3. k BITES -- the module global is patched, so this must be checked.
    #    Turnover falls in k; the round trip does NOT move (D296).
    ts, rts = [], []
    for k in KS:
        c = cell(A, Gh, k, HALF, CLOSE)
        ts.append(c["turnover"])
        rts.append(c["round_trip"])
    assert all(a > b for a, b in zip(ts, ts[1:])), f"[3] turnover not falling: {ts}"
    assert max(rts) / min(rts) - 1 < 0.25, f"[3] the round trip moved with k: {rts}"
    print(f"    [3] k BITES: turnover {ts[0]:.4f} -> {ts[-1]:.4f} across k="
          f"{KS[0]}..{KS[-1]} while the round trip moves only "
          f"{100 * (max(rts) / min(rts) - 1):.1f}% (D296)")

    # F. FILL -- turnover on the names HELD, and the nominal form is rejected.
    c = cell(A, Gh, 5, HALF, CLOSE)
    nom = c["entries"] / DEPTH / 2.0 / c["bars"]
    assert abs(c["turnover"] / nom - 1.0 / c["fill"]) < 1e-9, "[F] not turn/fill"
    assert c["turnover"] > nom or c["fill"] >= 0.999, \
        "[F] the held form does not exceed the nominal one"
    print(f"    [F] FILL: the book fills {c['fill']:.0%} and held turnover is "
          f"{c['turnover'] / nom:.3f}x the nominal form")

    # S. SPREAD BASIS.
    uni = 4.0 * float(np.nanmedian(HALF[np.isfinite(HALF)]))
    assert c["round_trip"] > uni * 1.10, "[S] the basis check cannot fail"
    print(f"    [S] SPREAD BASIS: held rt {c['round_trip']:.1f} rejects the "
          f"universe median {uni:.1f}")

    # C. COST DIMENSIONS.
    d295 = json.loads((REPO / "data" / "d295_exits.json").read_text())
    b0 = [x for x in d295["rows"] if x["cell"] == "B0"][0]
    got = d295["round_trip_mean"] * b0["turnover"]
    assert abs(got - b0["cost_bar_mean"]) < 1e-9 * abs(b0["cost_bar_mean"])
    assert abs(got * 2.0 - b0["cost_bar_mean"]) > 1.0
    print(f"    [C] cost dimensions: rt x turn = {got:.4f} reproduces d295's; "
          f"the doubled form is rejected")

    # 5. THE SELF-TEST MUST RAISE.
    broke = False
    try:
        r2 = W.simulate(A, G0, DEPTH, True)
        bk = r2["book"].copy()
        bk[np.flatnonzero(r2["mask"])[:200]] += 5e-4
        assert abs(float(bk[r2["mask"]].mean()) * 1e4
                   - d306["N=2/target"]["gross_bp"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[5] reproduction passed a book handed free money in the mask"
    print("    [5] and [1] raises on a book handed free money inside the mask")
    W.BASE_HOLD = 5


# --------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=100)
    a = ap.parse_args()
    t0 = time.time()

    print("D323  the shortlist at the operating point")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    HALF = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    CLOSE = np.ascontiguousarray(panel.closes.T)
    VOL = np.full(CLOSE.shape, np.nan)
    sym = {s: i for i, s in enumerate(panel.symbols)}
    pos = {d: i for i, d in enumerate(panel.dates)}
    for s, bars in cleaned.items():
        i = sym.get(s)
        if i is None:
            continue
        for st in bars:
            t = pos.get(st.timestamp[:10])
            if t is not None:
                VOL[t, i] = st.bar.volume
    finT = np.asarray(A["finT"])
    n, T = panel.live.shape
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & panel.live
    d293 = json.loads((REPO / "data" / "d293_candidate.json").read_text())
    d306 = json.loads((REPO / "data" / "d306_width_exits.json").read_text())["cells"]
    keep28 = F.keep_mask(F.roll_mean_T(CLOSE * VOL), finT, DV_PCT, True)
    print(f"  panel {n} x {T}, {len(CANDS)} candidates "
          f"({time.time() - t0:.0f}s)")

    assertions(A, z, base, finT, HALF, CLOSE, n, T, d293, d306)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    rng = np.random.default_rng(SEED)
    res = {"cells": {}, "dropped": [], "incumbent": {}}

    # the incumbent, at every k, on the composite gate
    G0 = W.build_gate(A, verbose=False)
    for k in KS:
        for dv in (False, True):
            Gc = G0 if not dv else gate_from(np.asarray(A["rankT"]), finT, keep28)
            c = cell(A, Gc, k, HALF, CLOSE)
            res["incumbent"][f"k{k}/dv{int(dv)}"] = c

    ranks = {}
    for cand in CANDS:
        try:
            ranks[cand] = rank_single(z, base, cand, n, T)
        except Exception as ex:                       # dropped and NAMED
            res["dropped"].append({"candidate": cand, "reason": repr(ex)})
            print(f"  DROPPED {cand}: {ex!r}")

    print(f"\nTHE CELLS   (N_eff=2, per-cell held rt + commission, [F] turnover)")
    h = "%-15s %3s %3s %8s %8s %8s %9s %8s %7s %8s"
    print(h % ("candidate", "k", "dv", "gross", "cost", "NET", "netSHRP",
               "half", "fill", "p"))
    print("-" * 88)
    names, ps, series = [], [], []
    for cand in CANDS:
        if cand not in ranks:
            continue
        for dv in (False, True):
            G = gate_from(ranks[cand], finT, keep28 if dv else None)
            for k in KS:
                c = cell(A, G, k, HALF, CLOSE)
                if c is None:
                    res["dropped"].append(
                        {"candidate": cand, "k": k, "dv": dv,
                         "reason": "no usable book at this cell"})
                    continue
                nl = np.empty(a.draws)
                for i in range(a.draws):
                    sh = int(rng.integers(126, T - 126))
                    Gn = gate_from(np.roll(ranks[cand], sh, axis=1), finT,
                                   keep28 if dv else None)
                    cn = cell(A, Gn, k, HALF, CLOSE)
                    nl[i] = cn["sharpe_net"] if cn else np.nan
                nl = nl[np.isfinite(nl)]
                p = float((nl >= c["sharpe_net"]).sum() + 1) / (nl.size + 1)
                nm = f"{cand}/k{k}/dv{int(dv)}"
                c.update(candidate=cand, k=k, dv=dv, p=p,
                         null_p50=float(np.median(nl)),
                         null_p95=float(np.quantile(nl, .95)),
                         null_draws=int(nl.size))
                res["cells"][nm] = c
                names.append(nm); ps.append(p)
                print(h % (cand, k, "Y" if dv else "n", "%+.2f" % c["gross_bp"],
                           "%.2f" % c["cost_bp"], "%+.2f" % c["net_bp"],
                           "%+.3f" % c["sharpe_net"],
                           "%.2f" % c["held_half_spread"],
                           "%.0f%%" % (100 * c["fill"]), "%.4f" % p))

    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    print(f"  {len(names)} cells scored, {len(res['dropped'])} dropped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
