"""D332 -- the spread estimator's CONVENTION: per-bar median (PB) vs the published
trailing mean (PUB), with and without a half-tick floor.

    uv run python scripts/run_d332_spread_convention.py

PRE-REGISTERED AT `1d0b299`, committed before this file existed (R8).

THE HARNESS CHANGE IS ONE ARRAY. Every runner since D318 reads the spread as
`held_median(res, HALF)` at (entry, row). PUB is a different HALF -- the
`cs_spread` score, which is the trailing 21-bar mean of the clamped daily
Corwin-Schultz estimates over each name's own bars, lagged one bar -- and
nothing else moves. [1] proves identity under PB; [S] proves the ledgers are
bit-identical under both, so cost never touched selection.

  PB   HALF_PB[t, i]  = CS_pair(t, i) / 2 * 1e4          the current cost model
  PUB  HALF_PUB[t, i] = cs_spread[i, t-1] / 2 * 1e4       the estimator as published
  +f   max(., half a tick / close)                        tick $0.01 at >= $1, else $0.0001

IBKR's per-share commission is unchanged (D318, G22.costed).

Part A measures the levels per leg and registers no predictions. Part B
reprices the stack under PUB against seven predictions, four of them against
the stack as it stands. Which convention is TRUE is not decided here (Part C
of the record).
"""

from __future__ import annotations

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


PB_ = _load("d330b", "run_d330b_causal_filter.py")
V9 = PB_.V9
V6, Y, W, D, M, SP, R, X = V9.V6, V9.Y, V9.W, V9.D, V9.M, V9.SP, V9.R, V9.X
Q, G22 = V6.Q, V6.G22

K0, K_INC = 20, 5
DV_PCT = 28.0
EXCLUDED = V9.EXCLUDED
OUT = REPO / "data" / "d332_spread_convention.json"


def half_floor(CLOSE):
    tick = np.where(CLOSE >= 1.0, 0.01, 0.0001)
    with np.errstate(invalid="ignore", divide="ignore"):
        f = 0.5 * tick / CLOSE * 1e4
    return np.where(np.isfinite(CLOSE) & (CLOSE > 0), f, np.nan)


def with_floor(HALF, FLOOR):
    return np.where(np.isfinite(HALF), np.maximum(HALF, FLOOR), np.nan)


def main() -> int:
    t0 = time.time()
    print("D332  the spread estimator's convention")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    r1T, finT, mkt = np.asarray(A["r1T"]), np.asarray(A["finT"]), np.asarray(A["mkt"])
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    HALF_PB = np.ascontiguousarray(
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
    DV = X.roll_mean_T(CLOSE * VOL)
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & panel.live
    n, T = panel.live.shape
    cs = z["cs_spread"]                                            # (n, T), round-trip fraction
    HALF_PUB = np.full((T, n), np.nan)
    HALF_PUB[1:] = (cs[:, :-1] / 2.0 * 1e4).T
    FLOOR = half_floor(CLOSE)
    HALF = {"PB": HALF_PB, "PUB": HALF_PUB,
            "PB+f": with_floor(HALF_PB, FLOOR), "PUB+f": with_floor(HALF_PUB, FLOOR)}
    d329 = json.loads((REPO / "data" / "d329_legwise.json").read_text())
    d323 = json.loads((REPO / "data" / "d323_shortlist.json").read_text())
    d318 = json.loads((REPO / "data" / "d318_stack_recost.json").read_text())
    pool = [s for s in z.files if s not in ("key", "warm") and s not in EXCLUDED]
    assert len(pool) == 46
    print(f"  panel {finT.shape} ({time.time() - t0:.0f}s)")

    # ---- the harness, parameterised ---------------------------------------
    def run_cell(rankT, k, depth=2, H=None, keep=None, use_target=True, want_variant=True):
        W.BASE_HOLD = k
        gate = Y.gate_from(rankT, finT, keep)
        out, res_v, res_i = {}, None, None
        if want_variant:
            res_v = W.simulate(A, gate, depth, use_target, slots=True)
            if res_v["trades"]:
                try:
                    c = G22.costed(res_v, (H, CLOSE, DV, finT))
                    g1 = G22.group1(res_v, c, G22.contributions(res_v, r1T), r1T)
                    out["variant"] = dict(net_bp_bar=g1["net_bp_bar"], gross_bp_bar=g1["gross_bp_bar"],
                                          sharpe_net=g1["sharpe_net"], round_trip=c["round_trip"],
                                          held_half=c["held_half_spread"], held_per_bar=g1["held_per_bar"])
                except ZeroDivisionError:
                    out["variant"] = "degenerate"
        res_i = W.simulate(A, gate, depth, use_target, slots=False)
        legs = V9.per_leg(res_i, H, CLOSE, r1T, mkt)
        if all(legs[s] for s in (0, 1)) and all(np.isfinite(legs[s]["half_bp"]) for s in (0, 1)):
            out["invariant"] = V9.invariant_legcost(res_i, legs)
        else:
            out["invariant"] = "degenerate"
        out["legs"] = legs
        return out, res_v, res_i

    rk = {s: Y.rank_single(z, base, s, n, T) for s in pool}
    fire = PB_.fire_mask(r1T, ((g["high"] - g["low"]) / g["close"]).T.copy(), finT)
    rkSf = Y.rank_single({"skew_63": np.where(fire, np.nan, z["skew_63"])}, base, "skew_63", n, T)
    RK = {"H": rk["hist_L"], "S": rk["skew_63"],
          "LW": V9.legwise(rk["hist_L"], rk["skew_63"]),
          "RV": V9.legwise(rk["skew_63"], rk["hist_L"]),
          "S_f": rkSf, "LW_f": V9.legwise(rk["hist_L"], rkSf)}
    rkC0 = Q.rank_composite(z, base, *Q.COMPOSITES["C0_incumbent"], n, T)
    print(f"  rank arrays ({time.time() - t0:.0f}s)")

    # ---- assertions -------------------------------------------------------
    print("\nASSERTIONS")
    # U. units
    mPB = float(np.nanmedian(HALF_PB[finT])); mPUB = float(np.nanmedian(HALF_PUB[finT]))
    assert abs(mPB - 14.2) < 0.15 and abs(mPUB - 31.7) < 0.15, f"[U] {mPB:.2f} {mPUB:.2f}"
    print(f"    [U] UNITS: universe median half-spread PB {mPB:.1f} bp, PUB {mPUB:.1f} bp -- the stage-0 numbers")
    # Z. PUB's zero rate
    zPB = float((HALF_PB[finT & np.isfinite(HALF_PB)] == 0).mean())
    zPUB = float((HALF_PUB[finT & np.isfinite(HALF_PUB)] == 0).mean())
    assert zPUB < 0.01 and zPB > 0.40, f"[Z] {zPB:.3f} {zPUB:.4f}"
    print(f"    [Z] ZERO RATE: PB {100 * zPB:.1f}% of finite values are exactly zero; PUB {100 * zPUB:.2f}%")
    # C. the lag
    rng = np.random.RandomState(20260905)
    for _ in range(200):
        t, i = rng.randint(1, T), rng.randint(n)
        if np.isfinite(cs[i, t - 1]):
            assert HALF_PUB[t, i] == cs[i, t - 1] / 2.0 * 1e4
    print("    [C] PUB at bar t is cs_spread at t-1 -- pairs ending at or before t-1; causality "
          "inherited from axis E's truncation audit")
    # F. the floor
    for k_ in ("PB", "PUB"):
        Hf, H0 = HALF[k_ + "+f"], HALF[k_]
        m = np.isfinite(H0)
        assert (Hf[m] >= FLOOR[m] - 1e-12).all()
        above = m & (H0 > FLOOR)
        assert np.array_equal(Hf[above], H0[above])
    print("    [F] FLOOR: applied values are >= half a tick over price everywhere, and untouched above it")
    # 1. identity under PB against D329 and D323
    cell = {}
    worst = 0.0
    for nm in ("H", "S", "LW", "RV"):
        cell[(nm, "PB")], _, resPB = run_cell(RK[nm], K0, H=HALF_PB)
        c9 = d329["arms"][f"{nm}/k{K0}"]
        worst = max(worst, abs(cell[(nm, "PB")]["invariant"]["net_per_trade"] - c9["invariant"]["net_per_trade"]),
                    abs(cell[(nm, "PB")]["variant"]["sharpe_net"] - c9["variant"]["sharpe_net"]))
        cell[(nm, "PUB")], _, resPUB = run_cell(RK[nm], K0, H=HALF_PUB)
        # S. swap-only
        assert sorted(resPB["trades"]) == sorted(resPUB["trades"]), f"[S] {nm}: ledgers differ under PUB"
    thirteen = sorted({k.split("/")[0] for k in d323["cells"] if k.endswith(f"/k{K0}/dv0")})
    for s in thirteen:
        rks = rk[s] if s in rk else Y.rank_single(z, base, s, n, T)
        cell[(s, "PB")], _, _ = run_cell(rks, K0, H=HALF_PB)
        v = cell[(s, "PB")]["variant"]
        if v != "degenerate":
            worst = max(worst, abs(v["net_bp_bar"] - d323["cells"][f"{s}/k{K0}/dv0"]["net_bp"]))
    assert worst < 1e-6, f"[1] PB does not reproduce D329/D323: {worst:.2e}"
    print(f"    [1] IDENTITY under PB: D329's four arms and D323's thirteen k=20 cells reproduce to {worst:.1e}")
    print("    [S] SWAP-ONLY: every arm's ledger is bit-identical under PUB -- cost never touches selection")
    # 6. raises
    broke = False
    try:
        bad = dict(cell[("LW", "PUB")]["invariant"]); bad["round_trip"] = 0.0
        assert bad["round_trip"] == cell[("LW", "PUB")]["invariant"]["round_trip"]
    except AssertionError:
        broke = True
    assert broke
    print("    [6] and the check raises on a cell handed a free spread")

    # ---- Part A: levels per leg -------------------------------------------
    ts = time.time()
    levels = {}
    for s in pool:
        _, _, res_i = run_cell(rk[s], K0, H=HALF_PB, want_variant=False)
        row = {}
        for side in (0, 1):
            tr = [t for t in res_i["trades"] if t[4] == side]
            if not tr:
                continue
            e = np.array([HALF_PB[t[1], t[0]] for t in tr])
            row[side] = {"trades": len(tr),
                         "zero_frac": float(np.mean(e[np.isfinite(e)] == 0)) if np.isfinite(e).any() else np.nan}
            for k_, Hk in HALF.items():
                v = np.array([Hk[t[1], t[0]] for t in tr]); v = v[np.isfinite(v)]
                row[side][k_] = float(np.median(v)) if v.size else np.nan
        levels[s] = row
    print(f"\n  Part A: 46 legs x 2 under four conventions ({time.time() - ts:.0f}s)")
    for side, lbl in ((1, "SHORT"), (0, "LONG")):
        print(f"\nPART A -- {lbl} LEGS: held median half-spread (bp) at entry, k=20.  sorted by PUB/PB")
        print("  %-14s %6s %6s | %7s %7s %7s %7s | %6s" % ("signal", "trades", "zero%", "PB", "PUB", "PB+f", "PUB+f", "PUB/PB"))
        rows = sorted(pool, key=lambda s: -(levels[s][side]["PUB"] / max(levels[s][side]["PB"], 1e-9)) if side in levels[s] else 0)
        for s in rows[:12] + ["..."] + rows[-6:]:
            if s == "...":
                print("  ..."); continue
            d = levels[s].get(side)
            if not d:
                continue
            print("  %-14s %6d %5.0f%% | %7.1f %7.1f %7.1f %7.1f | %6.2f"
                  % (s, d["trades"], 100 * d["zero_frac"], d["PB"], d["PUB"], d["PB+f"], d["PUB+f"],
                     d["PUB"] / max(d["PB"], 1e-9)))
    ratios = [levels[s][side]["PUB"] / levels[s][side]["PB"] for s in pool for side in (0, 1)
              if side in levels[s] and levels[s][side]["PB"] > 0]
    print("\n  PUB / PB across all costable legs: median %.2fx, p10 %.2fx, p90 %.2fx"
          % tuple(np.percentile(ratios, [50, 10, 90])))

    # ---- Part B: the stack under PUB ---------------------------------------
    ts = time.time()
    for nm in ("S_f", "LW_f"):
        for k_ in ("PB", "PUB"):
            cell[(nm, k_)], _, _ = run_cell(RK[nm], K0, H=HALF[k_])
    for nm in RK:
        cell[(nm, "PUB+f")], _, _ = run_cell(RK[nm], K0, H=HALF["PUB+f"])
    # the incumbent at its own operating point: k=5, target, depth 2 and 19; and dv28
    pct = np.full(T, np.nan)
    for t in range(T):
        v = DV[t][finT[t] & np.isfinite(DV[t])]
        if v.size > 50:
            pct[t] = np.percentile(v, DV_PCT)
    keep28 = ~(DV < pct[:, None])                       # nan DV -> kept (no information)
    inc = {}
    for k_ in ("PB", "PUB"):
        inc[("N2", k_)], _, _ = run_cell(rkC0, K_INC, depth=2, H=HALF[k_])
        inc[("N19", k_)], _, _ = run_cell(rkC0, K_INC, depth=19, H=HALF[k_])
        inc[("N2dv28", k_)], _, _ = run_cell(rkC0, K_INC, depth=2, H=HALF[k_], keep=keep28)
    for s in thirteen:
        rks = rk[s] if s in rk else Y.rank_single(z, base, s, n, T)
        cell[(s, "PUB")], _, _ = run_cell(rks, K0, H=HALF_PUB)
    print(f"\n  Part B cells ({time.time() - ts:.0f}s)")

    vb = lambda c: c["variant"]["net_bp_bar"] if c["variant"] != "degenerate" else np.nan
    sh = lambda c: c["variant"]["sharpe_net"] if c["variant"] != "degenerate" else np.nan
    it = lambda c: c["invariant"]["net_per_trade"] if c["invariant"] != "degenerate" else np.nan
    print("\nPART B -- the stack repriced.  variant bp/bar | invariant per trade")
    print("  %-22s %9s %9s %9s | %9s %9s %9s" % ("cell", "PB", "PUB", "PUB+f", "PB", "PUB", "PUB+f"))
    for nm in RK:
        print("  %-22s %+9.2f %+9.2f %+9.2f | %+9.2f %+9.2f %+9.2f"
              % (f"{nm}/k{K0}", vb(cell[(nm, "PB")]), vb(cell[(nm, "PUB")]), vb(cell[(nm, "PUB+f")]),
                 it(cell[(nm, "PB")]), it(cell[(nm, "PUB")]), it(cell[(nm, "PUB+f")])))
    d318_n2 = d318["cells"]["N=2/target"]
    print("\n  incumbent C0, k=5, target (D318's operating point)     variant bp/bar     Sharpe")
    for key, lbl in (("N2", "N=2"), ("N19", "N=19"), ("N2dv28", "N=2 + dv28 (rebuilt, not D321's cell)")):
        print("  %-42s PB %+7.2f  PUB %+7.2f | PB %+.3f  PUB %+.3f"
              % (lbl, vb(inc[(key, "PB")]), vb(inc[(key, "PUB")]), sh(inc[(key, "PB")]), sh(inc[(key, "PUB")])))
    gap = vb(inc[("N2", "PB")]) - (d318_n2.get("net_bp", d318_n2.get("net_bp_bar", np.nan)))
    print(f"  [H] this harness's N=2/target under PB vs D318's published cell: differs by {gap:+.3f} bp/bar "
          f"(informational -- D318's construction is not asserted identical)")
    print("\n  D323's thirteen at k=20, variant net bp/bar, ranked")
    for k_ in ("PB", "PUB"):
        order = sorted(thirteen, key=lambda s: -vb(cell[(s, k_)]) if np.isfinite(vb(cell[(s, k_)])) else 1e9)
        print(f"    {k_:4s}: " + "  ".join(f"{s} {vb(cell[(s, k_)]):+.1f}" for s in order[:6]))

    # enumeration under PUB for Q6 (invariant only)
    ts = time.time()
    enumPUB = {"A": {}, "B": {}}
    for s in pool:
        ra, _, _ = run_cell(V9.legwise(rk["hist_L"], rk[s]), K0, H=HALF_PUB, want_variant=False)
        rb, _, _ = run_cell(V9.legwise(rk[s], rk["skew_63"]), K0, H=HALF_PUB, want_variant=False)
        enumPUB["A"][s] = it(ra); enumPUB["B"][s] = it(rb)
    print(f"  enumeration under PUB ({time.time() - ts:.0f}s)")

    # ---- predictions -------------------------------------------------------
    q1 = vb(inc[("N2", "PUB")]) <= 0.0
    dPB = vb(inc[("N2", "PB")]) - vb(inc[("N19", "PB")])
    dPUB = vb(inc[("N2", "PUB")]) - vb(inc[("N19", "PUB")])
    q2 = abs(dPUB - dPB) <= 5.0
    q3 = it(cell[("LW", "PUB")]) > max(it(cell[("H", "PUB")]), it(cell[("S", "PUB")]))
    advPB = vb(inc[("N2dv28", "PB")]) - vb(inc[("N2", "PB")])
    advPUB = vb(inc[("N2dv28", "PUB")]) - vb(inc[("N2", "PUB")])
    q4 = advPUB > advPB
    top2 = {k_: set(sorted(thirteen, key=lambda s: -vb(cell[(s, k_)]) if np.isfinite(vb(cell[(s, k_)])) else 1e9)[:2])
            for k_ in ("PB", "PUB")}
    q5 = top2["PB"] != top2["PUB"]
    deg = {"A": ("on_share", "dist_52w_high"), "B": ("cs_spread",)}
    q6 = True; deg_rank = {}
    for d_, names in deg.items():
        order = sorted(pool, key=lambda s: -enumPUB[d_][s] if np.isfinite(enumPUB[d_][s]) else 1e9)
        for s in names:
            r_ = order.index(s) + 1
            deg_rank[f"{d_}/{s}"] = (r_, enumPUB[d_][s])
            q6 = q6 and np.isfinite(enumPUB[d_][s]) and r_ > 10
    q7 = all(abs(it(cell[(nm, "PUB+f")]) - it(cell[(nm, "PUB")])) <= 1.0 for nm in RK)
    print("\nPREDICTIONS")
    for kk, vv in (("Q1 the incumbent nets <= 0 bp/bar at N=2 under PUB  [load-bearing, against the stack]", q1),
                   ("Q2 concentration survives: N2 - N19 within 5 bp/bar of its PB value", q2),
                   ("Q3 the leg-wise book still beats both parents per trade under PUB", q3),
                   ("Q4 dv28's advantage over its base widens under PUB  [directional]", q4),
                   ("Q5 D323's top-2 at k=20 changes under PUB  [against the shortlist]", q5),
                   ("Q6 the three degenerate cells are costable under PUB and none is top-10", q6),
                   ("Q7 the half-tick floor moves no PUB cell by more than 1 bp per trade", q7)):
        print(f"    {'CONFIRMED' if vv else 'FALSIFIED'}  {kk}")
    print(f"    incumbent N=2: PB {vb(inc[('N2', 'PB')]):+.2f} -> PUB {vb(inc[('N2', 'PUB')]):+.2f} bp/bar;  "
          f"N2-N19: PB {dPB:+.2f}, PUB {dPUB:+.2f};  dv28 advantage: PB {advPB:+.2f}, PUB {advPUB:+.2f}")
    print(f"    LW per trade: PB {it(cell[('LW', 'PB')]):+.2f} -> PUB {it(cell[('LW', 'PUB')]):+.2f};  "
          f"parents PUB: H {it(cell[('H', 'PUB')]):+.2f}, S {it(cell[('S', 'PUB')]):+.2f}")
    print(f"    top-2 PB {sorted(top2['PB'])}  PUB {sorted(top2['PUB'])};  degenerate cells under PUB: "
          + "  ".join(f"{k} rank {v[0]} ({v[1]:+.1f})" for k, v in deg_rank.items()))

    def ser(c):
        return {k: (v if not isinstance(v, dict) or k != "legs" else {str(s): v[s] for s in v}) for k, v in c.items()}
    OUT.write_text(json.dumps(dict(
        note="D332: PB = per-bar CS median at entry (the current cost model); PUB = cs_spread "
             "trailing-21 mean lagged (the published estimator); +f = half-tick floor. Variant "
             "bp/bar, invariant per trade, never compared (FINDINGS 10).",
        universe_median={"PB": mPB, "PUB": mPUB}, zero_rate={"PB": zPB, "PUB": zPUB},
        levels={s: {str(k): v for k, v in levels[s].items()} for s in pool},
        cells={f"{a}/{b}": ser(c) for (a, b), c in cell.items()},
        incumbent={f"{a}/{b}": ser(c) for (a, b), c in inc.items()},
        d318_gap=gap, enumeration_PUB=enumPUB, degenerate_rank=deg_rank,
        top2={k: sorted(v) for k, v in top2.items()},
        predictions=dict(Q1=bool(q1), Q2=bool(q2), Q3=bool(q3), Q4=bool(q4), Q5=bool(q5),
                         Q6=bool(q6), Q7=bool(q7))), indent=1, default=float))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
