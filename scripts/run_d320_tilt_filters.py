"""D320 -- the tilt filters, and whether concentration already took the prize.

    uv run python scripts/run_d320_tilt_filters.py --selftest
    uv run python scripts/run_d320_tilt_filters.py [--draws 200]

PRE-REGISTERED AT `a14ea24`, committed before this file existed (R8).

D304's tilt study, finally run. Held names cost 26.31 bp half-spread against the
universe's 13.20 (D302), and cost is 20.90 bp/bar against gross 32.89 at the
operating point (D318). But concentration ALREADY collected part of the prize --
D300 measured N=19 -> N=2 moving held price $23.72 -> $75.95 and half-spread
26.67 -> 21.68, for free -- so the question is whether an explicit filter adds
anything ON TOP of that. Q2 enters the answer "no" as the load-bearing prediction.

FILTER SEMANTICS. `keep` is applied INSIDE the gate cut, `(rk < N_BASE) & fin &
keep`, so a filter removes names from the book rather than widening the pool to
replace them. That reproduces the baseline gate bit-identically at keep=all-True
(assertion [1]) and it is the right reading: a tilt filter says "do not hold
this", not "expand the gate". D304's own correction in FINDINGS section 10 showed
widening the pool alone is inert anyway.

THRESHOLDS ARE PER-BAR CROSS-SECTIONAL PERCENTILES of a LAGGED variable, so they
are causal, self-normalising, and exclude exactly p% of the live cross-section --
which makes the count-matched control exact by construction.

THE NULL IS A CIRCULAR TIME ROTATION of the exclusion mask, and it is the SECOND
construction tried. A name-label permutation was written first -- it preserves
each name's exclusion run-lengths exactly, which looked like the right match --
and ASSERTION [4] REJECTED IT: it churned +28.2% harder than the treatment,
indistinguishable from a per-bar re-draw's +28.4%. Names differ in liveness, so
permuting labels maps a persistent exclusion pattern onto names that are live at
other times. Matched count is not matched turnover (D279), and the check caught it
before a single cell was scored.

The rotation matches entries to +1.5%, keeps every name's own run-lengths, and
destroys only the alignment between the exclusion and when names are actually
expensive -- which is the question. Assertion [4] prints all four numbers so the
rejected construction stays visible.

COST FOLLOWS D320 section 5, which INVERTS D307 on purpose: the filter's whole
mechanism is to change what the held names cost, so a common round trip would
define the treatment effect away. Per-cell is primary; common is reported beside
it, and the gap between them decomposes selection from cost.
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
D, M, SP = W.D, W.M, W.SP
N_BASE = W.N_BASE

DEPTHS = (2, 19)
PCTS = (10.0, 25.0, 40.0)
ARMS = ("spread", "price", "dv")
WIN = 63
PER_SHARE, CROSSINGS = 0.005, 4.0
ANN, SEED = 252.0, 20260904
OUT = REPO / "data" / "d320_tilt_filters.json"

# arm -> (variable key, is a LOW value the bad one?)
BAD_LOW = {"spread": False, "price": True, "dv": True}


# ---------------------------------------------------------------- primitives
def roll_mean_T(X, w=WIN):
    """Trailing w-bar mean along TIME for each name, lagged one bar. (T,n)."""
    ok = np.isfinite(X)
    Xf = np.where(ok, X, 0.0)
    cs = np.concatenate([np.zeros((1, X.shape[1])), np.cumsum(Xf, axis=0)])
    cn = np.concatenate([np.zeros((1, X.shape[1])), np.cumsum(ok, axis=0)])
    out = np.full(X.shape, np.nan)
    j = np.arange(w, X.shape[0] + 1)
    cnt = cn[j] - cn[j - w]
    with np.errstate(invalid="ignore", divide="ignore"):
        out[j - 1] = np.where(cnt >= w / 3, (cs[j] - cs[j - w]) / np.maximum(cnt, 1),
                              np.nan)
    lag = np.full(X.shape, np.nan)
    lag[1:] = out[:-1]
    return lag


def keep_mask(v, finT, pct, bad_low):
    """Exclude the worst `pct`% of the LIVE cross-section, bar by bar.

    Causal: `v` is already lagged. A name with no estimate is never excluded --
    excluding on a missing value would make the filter a liveness proxy.
    """
    keep = np.ones(finT.shape, bool)
    if pct <= 0:
        return keep
    for t in range(finT.shape[0]):
        m = finT[t] & np.isfinite(v[t])
        if m.sum() < 20:
            continue
        x = v[t][m]
        q = np.percentile(x, pct if bad_low else 100.0 - pct)
        bad = (x <= q) if bad_low else (x >= q)
        idx = np.flatnonzero(m)[bad]
        keep[t, idx] = False
    return keep


def gate_with(A, keep):
    """W.build_gate's construction with `keep` applied INSIDE the rank cut."""
    rankT, finT = np.asarray(A["rankT"]), np.asarray(A["finT"])
    T = rankT.shape[1]
    rows, rks, off = [], [], np.zeros((2, T + 1), np.int64)
    k = 0
    for side in (0, 1):
        for t in range(T):
            rk = rankT[side, t]
            g = np.flatnonzero((rk < N_BASE) & finT[t] & keep[t])
            if g.size:
                g = g[np.argsort(rk[g], kind="stable")]
            rows.append(g.astype(np.int32))
            rks.append(rk[g].astype(np.int32))
            off[side, t] = k
            k += g.size
        off[side, T] = k
    return {"gateF": np.concatenate(rows).astype(np.int32),
            "gateR": np.concatenate(rks).astype(np.int32), "gateO": off}


def held_median(res, X):
    """Median of X over the trades actually taken, at entry."""
    v = np.array([X[e0, row] for row, e0, _a, _p, _s in res["trades"]])
    v = v[np.isfinite(v)]
    return float(np.median(v)) if v.size else np.nan


def cell(res, depth, rt_spread, rt_comm):
    ok = res["mask"]
    b = res["book"][ok]
    bars, sd = b.size, b.std(ddof=1)
    eq = np.cumsum(b)
    turn = int(res["ent"][ok].sum()) / float(depth) / 2.0 / bars
    g = float(b.mean()) * 1e4
    pos, comm = rt_spread * turn, rt_comm * turn
    net, v = g - pos - comm, float(sd) * 1e4
    return dict(gross_bp=g, vol_bp=v, cost_pos_bp=pos, cost_comm_bp=comm,
                net_bp=net, sharpe_net=net / v * np.sqrt(ANN) if v > 0 else 0.0,
                sharpe_gross=g / v * np.sqrt(ANN) if v > 0 else 0.0,
                turnover=float(turn), round_trip=rt_spread,
                breakeven_rt=rt_spread * g / (pos + comm) if pos + comm > 0 else 0.0,
                maxdd_bp=float(np.max(np.maximum.accumulate(eq) - eq)) * 1e4,
                entries=int(res["ent"][ok].sum()), trades=len(res["trades"]),
                bars=bars)


def score(A, keep, depth, HALF, CLOSE, rt_common):
    """One book: simulate, measure what it holds, cost it both ways."""
    res = W.simulate(A, gate_with(A, keep), depth, True)
    hs = held_median(res, HALF)
    px = held_median(res, CLOSE)
    rt_own = 4.0 * hs
    rtc = CROSSINGS * PER_SHARE / px * 1e4 if px > 0 else np.nan
    c = cell(res, depth, rt_own, rtc)
    c.update(held_half_spread=hs, held_price=px, commission_rt=rtc,
             net_common_bp=cell(res, depth, rt_common, rtc)["net_bp"],
             sharpe_common=cell(res, depth, rt_common, rtc)["sharpe_net"])
    return c, res


def bh(ps, q=0.10):
    o = np.argsort(ps)
    m = len(ps)
    hit = np.asarray(ps)[o] <= (np.arange(1, m + 1) / m) * q
    k = np.flatnonzero(hit).max() + 1 if hit.any() else 0
    rej = np.zeros(m, bool)
    rej[o[:k]] = True
    return rej


# ---------------------------------------------------------------- assertions
def assertions(A, G, V, finT, HALF, CLOSE, d306, d318):
    print("\nASSERTIONS")
    ones = np.ones(finT.shape, bool)

    # 1. THE UNFILTERED GATE IS BIT-IDENTICAL to D306's, and its book reproduces.
    Gf = gate_with(A, ones)
    for a in ("gateF", "gateR", "gateO"):
        assert np.array_equal(Gf[a], G[a]), f"[1] {a} differs at keep=all-True"
    worst = 0.0
    for d in DEPTHS:
        r = W.simulate(A, Gf, d, True)
        c = cell(r, d, W.held_rt(r, HALF), 0.0)
        ref = d306[f"N={d}/target"]
        worst = max(worst, abs(c["gross_bp"] - ref["gross_bp"]),
                    abs(c["net_bp"] - ref["net_bp"]))
    assert worst < 1e-9, f"[1] the unfiltered book differs from D306 by {worst:.2e}"
    print(f"    [1] the unfiltered gate is BIT-IDENTICAL to D306's and its book "
          f"reproduces D306's N=2 and N=19 target cells to {worst:.1e} bp")

    # 2. THE FILTER BITES, and in the declared direction.
    for arm in ARMS:
        k = keep_mask(V[arm], finT, 25.0, BAD_LOW[arm])
        rate = 1.0 - (k & finT).sum() / finT.sum()
        assert 0.20 < rate < 0.30, f"[2] {arm} excludes {rate:.1%}, not ~25%"
        r0 = W.simulate(A, gate_with(A, ones), 2, True)
        r1 = W.simulate(A, gate_with(A, k), 2, True)
        h0, h1 = held_median(r0, HALF), held_median(r1, HALF)
        p0, p1 = held_median(r0, CLOSE), held_median(r1, CLOSE)
        if arm == "spread":
            assert h1 < h0, f"[2] the spread filter RAISED held spread {h0}->{h1}"
        if arm == "price":
            assert p1 > p0, f"[2] the price floor LOWERED held price {p0}->{p1}"
        assert not np.array_equal(r0["book"], r1["book"]), f"[2] {arm} inert"
    print("    [2] every arm excludes ~25% of the live cross-section, moves its "
          "own variable in the declared direction, and changes the book")

    # 3. CAUSALITY -- the filter reads only t-1, and the audit can fail.
    raw = np.where(np.isfinite(HALF), HALF, np.nan)
    lagged = roll_mean_T(raw)
    unlag = np.full(raw.shape, np.nan)
    ok = np.isfinite(raw)
    cs = np.concatenate([np.zeros((1, raw.shape[1])), np.cumsum(np.where(ok, raw, 0.0), axis=0)])
    cn = np.concatenate([np.zeros((1, raw.shape[1])), np.cumsum(ok, axis=0)])
    j = np.arange(WIN, raw.shape[0] + 1)
    cnt = cn[j] - cn[j - WIN]
    with np.errstate(invalid="ignore"):
        unlag[j - 1] = np.where(cnt >= WIN / 3, (cs[j] - cs[j - WIN]) / np.maximum(cnt, 1), np.nan)
    m = np.isfinite(lagged) & np.isfinite(unlag)
    assert not np.array_equal(lagged[m], unlag[m]), \
        "[3] the lagged and unlagged filter variables are IDENTICAL"
    a = keep_mask(lagged, finT, 25.0, False)
    b = keep_mask(unlag, finT, 25.0, False)
    assert not np.array_equal(a, b), "[3] peeking gives the same exclusion set"
    print(f"    [3] CAUSALITY: the filter variable is lagged, and a peeking "
          f"variant moves {np.mean(a != b):.1%} of name-bars -- the audit fails "
          f"when the lag goes")

    # 4. THE NULL IS TURNOVER-MATCHED, AND D291's DEFECT IS MADE VISIBLE.
    #
    #    A NAME-LABEL PERMUTATION WAS TRIED FIRST AND THIS ASSERTION REJECTED IT:
    #    it churned +28% harder than the treatment -- indistinguishable from a
    #    per-bar re-draw -- because names differ in liveness, so permuting labels
    #    maps a persistent exclusion pattern onto names that are live at other
    #    times. Matched count is not matched turnover (D279), and the check
    #    caught it before any cell was scored.
    rng = np.random.default_rng(1)
    k = keep_mask(V["spread"], finT, 25.0, False)
    rot = np.roll(k, 211, axis=0)
    perm = k[:, rng.permutation(k.shape[1])]
    perbar = np.ones_like(k)
    for t in range(k.shape[0]):
        live = np.flatnonzero(finT[t])
        nex = int((~k[t] & finT[t]).sum())
        if nex and live.size:
            perbar[t, rng.choice(live, size=min(nex, live.size), replace=False)] = False
    e = {}
    for nm, mask in (("treatment", k), ("rotated", rot), ("permuted", perm),
                     ("per-bar", perbar)):
        r = W.simulate(A, gate_with(A, mask), 2, True)
        e[nm] = int(r["ent"][r["mask"]].sum())
    assert abs(e["rotated"] / e["treatment"] - 1.0) < 0.15, \
        f"[4] the rotation is NOT turnover-matched: {e}"
    assert e["per-bar"] > e["rotated"] * 1.10, \
        f"[4] the per-bar re-draw does not churn materially more: {e}"
    print(f"    [4] the null is turnover-matched and D291's defect is visible:")
    print(f"        entries -- treatment {e['treatment']:,}  ROTATED "
          f"{e['rotated']:,} ({e['rotated'] / e['treatment'] - 1:+.1%})  "
          f"name-permuted {e['permuted']:,} ({e['permuted'] / e['treatment'] - 1:+.1%})"
          f"  PER-BAR {e['per-bar']:,} ({e['per-bar'] / e['treatment'] - 1:+.1%})")
    print(f"        -- the rotation is used; the permutation was REJECTED by this "
          f"assertion for churning like a per-bar re-draw")

    # S. SPREAD BASIS -- held round trips must exceed the universe median.
    uni = 4.0 * float(np.nanmedian(HALF[np.isfinite(HALF)]))
    for d in DEPTHS:
        r = W.simulate(A, Gf, d, True)
        own = 4.0 * held_median(r, HALF)
        assert own > uni * 1.10, \
            f"[S] held rt at N={d} ({own:.1f}) is not above the universe " \
            f"median ({uni:.1f}) -- the basis check cannot fail"
    print(f"    [S] SPREAD BASIS: the universe median rt of {uni:.1f} is REJECTED "
          f"at both depths")

    # C. COST DIMENSIONS.
    d295 = json.loads((REPO / "data" / "d295_exits.json").read_text())
    b0 = [x for x in d295["rows"] if x["cell"] == "B0"][0]
    got = d295["round_trip_mean"] * b0["turnover"]
    assert abs(got - b0["cost_bar_mean"]) < 1e-9 * abs(b0["cost_bar_mean"])
    assert abs(got * 2.0 - b0["cost_bar_mean"]) > 1.0
    print(f"    [C] cost dimensions: rt x turn = {got:.4f} reproduces d295's; "
          f"the doubled form is rejected")

    # 6. THE SELF-TEST MUST RAISE on a broken book inside the mask.
    broke = False
    try:
        r = W.simulate(A, Gf, 2, True)
        r2 = dict(r)
        bk = r["book"].copy()
        bk[np.flatnonzero(r["mask"])[:200]] += 5e-4
        r2["book"] = bk
        c = cell(r2, 2, W.held_rt(r, HALF), 0.0)
        assert abs(c["gross_bp"] - d306["N=2/target"]["gross_bp"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[6] reproduction passed a book handed free money in the mask"
    print("    [6] and [1] raises on a book handed free money inside the mask")


# --------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()

    print("D320  the tilt filters")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    G = W.build_gate(A, verbose=False)
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

    V = {"spread": roll_mean_T(HALF),
         "price": roll_mean_T(CLOSE),
         "dv": roll_mean_T(CLOSE * VOL)}
    d306 = json.loads((REPO / "data" / "d306_width_exits.json").read_text())["cells"]
    d318 = json.loads((REPO / "data" / "d318_stack_recost.json").read_text())["cells"]
    print(f"  panel {finT.shape}, live/bar {finT.sum(1).mean():.0f} "
          f"({time.time() - t0:.0f}s)")

    assertions(A, G, V, finT, HALF, CLOSE, d306, d318)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    ones = np.ones(finT.shape, bool)
    rng = np.random.default_rng(SEED)
    res = {"cells": {}, "control": {}, "null": {}, "price_matched": {}}

    for d in DEPTHS:
        c0, r0 = score(A, ones, d, HALF, CLOSE, 0.0)
        c0["net_common_bp"] = c0["net_bp"]
        c0["sharpe_common"] = c0["sharpe_net"]
        res["control"][f"N={d}"] = c0

    print("\nTHE CELLS   (per-cell held rt primary; common = the control's rt)")
    h = "%-16s %8s %8s %8s %9s %9s %8s %8s %9s"
    print(h % ("cell", "gross", "rt", "NET", "netSHRP", "net@com", "held½s",
               "held $", "b/e rt"))
    names, ps = [], []
    for d in DEPTHS:
        k0 = res["control"][f"N={d}"]
        rtc = k0["round_trip"]
        print("\n  N=%d control: gross %+.2f  rt %.1f  NET %+.2f  netSHRP %+.3f  "
              "half %.2f  price $%.2f" % (d, k0["gross_bp"], rtc, k0["net_bp"],
                                          k0["sharpe_net"], k0["held_half_spread"],
                                          k0["held_price"]))
        print("  " + "-" * 88)
        for arm in ARMS:
            for p in PCTS:
                keep = keep_mask(V[arm], finT, p, BAD_LOW[arm])
                c, _ = score(A, keep, d, HALF, CLOSE, rtc)
                nm = f"N={d}/{arm}{p:g}"
                # the null: CIRCULAR TIME ROTATION -- each name keeps its own
                # exclusion run-lengths exactly and the book keeps its turnover
                # (assertion [4]); only the alignment with when names are
                # actually expensive is destroyed.
                nl = np.empty(a.draws)
                for i in range(a.draws):
                    pk = np.roll(keep, int(rng.integers(63, keep.shape[0] - 63)), axis=0)
                    nl[i] = score(A, pk, d, HALF, CLOSE, rtc)[0]["sharpe_net"]
                pv = float((nl >= c["sharpe_net"]).sum() + 1) / (a.draws + 1)
                c.update(depth=d, arm=arm, pct=p, p=pv,
                         null_p50=float(np.median(nl)),
                         null_p95=float(np.quantile(nl, .95)),
                         vs_control=c["sharpe_net"] - k0["sharpe_net"])
                res["cells"][nm] = c
                names.append(nm); ps.append(pv)
                print(h % (nm, "%+.2f" % c["gross_bp"], "%.1f" % c["round_trip"],
                           "%+.2f" % c["net_bp"], "%+.3f" % c["sharpe_net"],
                           "%+.2f" % c["net_common_bp"],
                           "%.2f" % c["held_half_spread"],
                           "$%.0f" % c["held_price"], "%.1f" % c["breakeven_rt"]))

    # ---- the PRICE-MATCHED control: the D284 test --------------------------
    print("\nPRICE-MATCHED CONTROLS -- the D284 test")
    print("  a filter that improves cost by holding pricier names has found the")
    print("  price level, not a filter. The price arm IS the price level, so its")
    print("  price-matched control is degenerate and is not built.")
    print("  %-16s %10s %10s %10s %10s" % (
        "cell", "held $", "matched $", "netSHRP", "matched"))
    for nm, c in list(res["cells"].items()):
        if c["arm"] == "price":
            continue
        d, tgt = c["depth"], c["held_price"]
        lo, hi, best = 0.0, 60.0, None
        for _ in range(14):
            mid = 0.5 * (lo + hi)
            cc, _ = score(A, keep_mask(V["price"], finT, mid, True), d, HALF,
                          CLOSE, res["control"][f"N={d}"]["round_trip"])
            best = cc
            if cc["held_price"] < tgt:
                lo = mid
            else:
                hi = mid
        res["price_matched"][nm] = best
        c["vs_price_matched"] = c["sharpe_net"] - best["sharpe_net"]
        print("  %-16s %10s %10s %+10.3f %+10.3f" % (
            nm, "$%.0f" % tgt, "$%.0f" % best["held_price"], c["sharpe_net"],
            best["sharpe_net"]))

    rej = bh(ps)
    res["bh"] = {n: bool(r) for n, r in zip(names, rej)}
    surv = [n for n, r in zip(names, rej) if r]
    print(f"\n  BH-FDR q=0.10 over {len(names)} cells: "
          f"{', '.join(surv) if surv else 'NONE'}")

    # ---- predictions -------------------------------------------------------
    C, K = res["cells"], res["control"]
    q1 = all(C[f"N={d}/spread{p:g}"]["held_half_spread"]
             < K[f"N={d}"]["held_half_spread"] for d in DEPTHS for p in PCTS)
    q2 = all(c["sharpe_net"] <= res["price_matched"][n]["sharpe_net"]
             or c["net_bp"] <= 0 or c["p"] > 0.05
             for n, c in C.items() if c["arm"] != "price" and c["depth"] == 2)
    q4 = all(c["gross_bp"] <= K[f"N={c['depth']}"]["gross_bp"] for c in C.values())
    def move(d, arm, p):
        return abs(C[f"N={d}/{arm}{p:g}"]["held_price"] / K[f"N={d}"]["held_price"] - 1)
    q5 = all(move(19, arm, p) > move(2, arm, p) for arm in ARMS for p in PCTS)
    res["predictions"] = dict(Q1=bool(q1), Q2=bool(q2), Q4=bool(q4), Q5=bool(q5))
    print("\nPREDICTIONS")
    for k, v in (("Q1 every spread filter cuts the held half-spread", q1),
                 ("Q2 no filter beats its price-matched control  [load-bearing]", q2),
                 ("Q4 gross falls under every filter", q4),
                 ("Q5 the filters move held price MORE at N=19 than at N=2", q5)):
        print(f"    {'CONFIRMED' if v else 'FALSIFIED'}  {k}")

    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
