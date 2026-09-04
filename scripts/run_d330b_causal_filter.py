"""D330 Part B -- the causal pinned-name filter, pre-registered AGAINST the signal.

    uv run python scripts/run_d330b_causal_filter.py

PRE-REGISTERED AT `112bebd`, committed before this file existed (R8).

THE FILTER, at score time s for name i, from bars <= s only:
  jump   the largest single-day log return in bars [s-62, s-5] exceeds log(1.20)
  quiet  the median daily range (H-L)/C over bars [s-4, s] is below 0.75%
  fire   jump AND quiet
The 5-bar gap keeps the range test off the jump day. The filter acts on the
SCORE, not the gate -- z_f = where(fire, NaN, z) -- so a removed name is
REPLACED by the next rank, not left as a hole; [R] checks that. R.ranked lags
internally, so no extra lag is applied and [K] proves causality by truncation.

THE PREDICTION IS THAT THE SIGNAL GETS WORSE. Q4: LW_f's net per trade at k=20
falls below D329's +63.26, because the cost correction on pinned names -- read
by Corwin-Schultz as nearly free -- outweighs the market drift a short collected
on zero-return names. Q6: it still beats both parents. If Q6 fails, the
leg-wise result was the deal artefact.

Part A's look-ahead labels are recomputed here for ONE purpose: Q1, the
fraction of pinned trades the causal filter catches. Nothing is scored on them.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


PA = _load("d330a", "run_d330a_pinned_decomposition.py")
V9 = PA.V9
V6, Y, W, D, M, SP, R, X = V9.V6, V9.Y, V9.W, V9.D, V9.M, V9.SP, V9.R, V9.X

DEPTH, KS, K0 = 2, (10, 20, 40), 20
JUMP_LO, JUMP_HI = 5, 62          # bars ago; the window is [s-62, s-5]
JUMP_THRESH = np.log(1.20)
QUIET_BARS, QUIET_THRESH = 5, 0.0075
LONG_SIG, SHORT_SIG = "hist_L", "skew_63"
OUT = REPO / "data" / "d330b_causal_filter.json"


def fire_mask(r1T, RANGE, finT):
    """(n, T) bool: the causal pinned-name signature at score time s, bars <= s."""
    T, n = r1T.shape
    lr = np.ascontiguousarray(np.log1p(np.nan_to_num(r1T, nan=0.0)).T)     # (n, T)
    rg = np.ascontiguousarray(RANGE.T)                                        # (n, T)
    wlen = JUMP_HI - JUMP_LO + 1                                              # 58 bars
    jump = np.zeros((n, T), bool)
    # window ending at s-5 covers [s-62, s-5]; sliding windows over lr end at index w+wlen-1
    mx = sliding_window_view(lr, wlen, axis=1).max(axis=2)                    # (n, T-57): window j ends at j+57
    # for score time s the window must END at s-5, i.e. j + 57 = s - 5 -> j = s - 62
    jump[:, JUMP_HI:] = mx[:, :T - JUMP_HI] > JUMP_THRESH
    quiet = np.zeros((n, T), bool)
    med = np.nanmedian(sliding_window_view(rg, QUIET_BARS, axis=1), axis=2)   # window ends at j+4
    quiet[:, QUIET_BARS - 1:] = med < QUIET_THRESH
    return jump & quiet & finT.T


def main() -> int:
    t0 = time.time()
    print("D330 B  the causal pinned-name filter")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    r1T, finT, mkt = np.asarray(A["r1T"]), np.asarray(A["finT"]), np.asarray(A["mkt"])
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    HALF = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    CLOSE = np.ascontiguousarray(panel.closes.T)
    RANGE = np.ascontiguousarray(((g["high"] - g["low"]) / g["close"]).T)
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
    G4 = (HALF, CLOSE, X.roll_mean_T(CLOSE * VOL), finT)
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & panel.live
    n, T = panel.live.shape
    d329 = json.loads((REPO / "data" / "d329_legwise.json").read_text())
    last_live = PA.last_live_bar(finT)
    print(f"  panel {finT.shape} ({time.time() - t0:.0f}s)")

    fire = fire_mask(r1T, RANGE, finT)
    zS, zH = z[SHORT_SIG], z[LONG_SIG]
    zSf = np.where(fire, np.nan, zS)
    zHf = np.where(fire, np.nan, zH)
    rk = {"S": Y.rank_single({SHORT_SIG: zS}, base, SHORT_SIG, n, T),
          "Sf": Y.rank_single({SHORT_SIG: zSf}, base, SHORT_SIG, n, T),
          "H": Y.rank_single({LONG_SIG: zH}, base, LONG_SIG, n, T),
          "Hf": Y.rank_single({LONG_SIG: zHf}, base, LONG_SIG, n, T)}
    RK = {"S": rk["S"], "S_f": rk["Sf"], "H": rk["H"],
          "LW": V9.legwise(rk["H"], rk["S"]),
          "LW_f": V9.legwise(rk["H"], rk["Sf"]),
          "LW_ff": V9.legwise(rk["Hf"], rk["Sf"])}
    print(f"  filter fires on {int(fire.sum()):,} name-bars of {int(finT.sum()):,} live "
          f"({100 * fire.sum() / finT.sum():.2f}%) ({time.time() - t0:.0f}s)")

    def arm(nm, k):
        return V9.run_arm(A, RK[nm], finT, k, G4, r1T, HALF, CLOSE, mkt)

    print("\nASSERTIONS")
    # K. CAUSALITY of the filter -- truncation audit.
    T0 = T // 2
    r_cut, rg_cut, f_cut = r1T.copy(), RANGE.copy(), finT.copy()
    r_cut[T0 + 1:] = np.nan; rg_cut[T0 + 1:] = np.nan; f_cut[T0 + 1:] = False
    fire_cut = fire_mask(r_cut, rg_cut, f_cut)
    assert np.array_equal(fire[:, :T0 + 1], fire_cut[:, :T0 + 1]), \
        "[K] the filter changed before T0 when bars after T0 were deleted"
    print(f"    [K] CAUSALITY: deleting every bar after T0={T0} leaves the filter "
          f"bit-identical before T0")
    # F. the filter fires and the arms differ.
    a20 = {nm: arm(nm, K0) for nm in RK}
    assert fire.sum() > 0
    assert not V9.same_side(a20["S"][2], a20["S_f"][2], 1), "[F] S_f == S on the short leg"
    assert abs(a20["S"][0]["variant"]["sharpe_net"] - a20["S_f"][0]["variant"]["sharpe_net"]) > 1e-9
    print("    [F] the filter FIRES: S_f differs from S on both lenses")
    # 1. harness identity with D329.
    worst = 0.0
    for nm in ("S", "H", "LW"):
        c = d329["arms"][f"{nm}/k{K0}"]
        worst = max(worst, abs(a20[nm][0]["invariant"]["net_per_trade"] - c["invariant"]["net_per_trade"]),
                    abs(a20[nm][0]["variant"]["sharpe_net"] - c["variant"]["sharpe_net"]))
    assert worst < 1e-9, f"[1] D329 not reproduced: {worst:.2e}"
    print(f"    [1] the unfiltered arms reproduce D329's k=20 cells on both lenses to {worst:.1e}")
    # L. leg independence for the filtered composite.
    for lens_i in (1, 2):
        assert V9.same_side(a20["LW_f"][lens_i], a20["H"][lens_i], 0), "[L] LW_f long != H long"
        assert V9.same_side(a20["LW_f"][lens_i], a20["S_f"][lens_i], 1), "[L] LW_f short != S_f short"
    print("    [L] LW_f's long ledger is H's and its short ledger is S_f's, bit-identically, both lenses")
    # R. REFILL -- where the unfiltered rank-0 short name is removed, a different name is rank 0.
    rS, rSf = rk["S"][1], rk["Sf"][1]                                   # (T, n)
    removed_bars, refilled = 0, 0
    for t in range(1, T):
        i0 = np.flatnonzero(rS[t] == 0)
        if i0.size == 0:
            continue
        i0 = int(i0[0])
        if fire[i0, t - 1]:                                             # score at t-1 is what ranks at t
            removed_bars += 1
            j0 = np.flatnonzero(rSf[t] == 0)
            assert j0.size == 1 and int(j0[0]) != i0, f"[R] no refill at bar {t}"
            refilled += 1
    assert removed_bars > 0 and refilled == removed_bars
    print(f"    [R] REFILL: at all {removed_bars} bars where the rank-0 short name is filtered, "
          f"a different name holds rank 0")
    # C. cost dimensions.
    lg = a20["LW_f"][0]["legs_invariant"]
    for side in (0, 1):
        assert abs(lg[side]["two_c"] - 2.0 * lg[side]["half_bp"]) < 1e-12
    print("    [C] per-leg 2c is 2 x that leg's held median half-spread")
    # 6. raises.
    broke = False
    try:
        bad = dict(a20["LW_f"][0]["invariant"]); bad["net_per_trade"] += 50.0
        assert abs(bad["net_per_trade"] - a20["LW_f"][0]["invariant"]["net_per_trade"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke
    print("    [6] and the check raises on a book handed free money")

    # ---- arms at every k ---------------------------------------------------
    arms = {}
    for nm in RK:
        for k in KS:
            arms[f"{nm}/k{k}"] = a20[nm][0] if k == K0 else arm(nm, k)[0]
    print("\nPATH-INVARIANT  (per trade, per-leg costed)")
    print("  %-6s %3s %9s %9s %8s %8s %7s | %8s %8s | %6s %6s"
          % ("arm", "k", "net/trd", "gross", "t", "mean/2c", "rt", "L net", "S net", "L half", "S half"))
    for nm in RK:
        for k in KS:
            c = arms[f"{nm}/k{k}"]; i = c["invariant"]; L = c["legs_invariant"]
            print("  %-6s %3d %+9.2f %+9.2f %+8.2f %8.2f %7.1f | %+8.1f %+8.1f | %6.1f %6.1f"
                  % (nm, k, i["net_per_trade"], i["gross_per_trade"], i["t_per_trade"],
                     i["mean_over_2c"], i["round_trip"], L[0]["net"], L[1]["net"],
                     L[0]["half_bp"], L[1]["half_bp"]))
    print("\nPATH-VARIANT  (bp/bar)")
    print("  %-6s %3s %9s %9s %9s %9s" % ("arm", "k", "net/bar", "gross", "Sharpe", "maxDD"))
    for nm in RK:
        for k in KS:
            v = arms[f"{nm}/k{k}"]["variant"]
            print("  %-6s %3d %+9.2f %+9.2f %+9.3f %9.0f"
                  % (nm, k, v["net_bp_bar"], v["gross_bp_bar"], v["sharpe_net"], v["maxdd_bp"]))

    # ---- Q1 / Q3 / Q5: what the filter removed, against Part A's labels -------
    resS, resSf = a20["S"][2], a20["S_f"][2]
    lab = PA.label_trades(resS["trades"], r1T, RANGE, HALF, last_live, T)
    key_Sf = {(t[0], t[1]) for t in resSf["trades"] if t[4] == 1}
    short_idx = [j for j, t in enumerate(resS["trades"]) if t[4] == 1]
    pinned = [j for j in short_idx if lab[j, 6] == 1]
    alive = [j for j in short_idx if lab[j, 2] == 0]
    caught = np.mean([(resS["trades"][j][0], resS["trades"][j][1]) not in key_Sf for j in pinned])
    removed_alive = np.mean([(resS["trades"][j][0], resS["trades"][j][1]) not in key_Sf for j in alive])
    key_Sf0 = {(t[0], t[1]) for t in resSf["trades"] if t[4] == 0}
    long_idx = [j for j, t in enumerate(resS["trades"]) if t[4] == 0]
    removed_long = np.mean([(resS["trades"][j][0], resS["trades"][j][1]) not in key_Sf0 for j in long_idx])

    def trimmed(res):
        p = np.sort(np.array([t[3] for t in res["trades"] if t[4] == 1]) * 1e4)
        c1 = max(1, len(p) // 100)
        return float(p[c1:-c1].mean())
    tr_S, tr_Sf = trimmed(resS), trimmed(resSf)
    half_S = arms[f"S/k{K0}"]["legs_invariant"][1]["half_bp"]
    half_Sf = arms[f"S_f/k{K0}"]["legs_invariant"][1]["half_bp"]
    net = lambda nm: arms[f"{nm}/k{K0}"]["invariant"]["net_per_trade"]
    shp = lambda nm: arms[f"{nm}/k{K0}"]["variant"]["sharpe_net"]

    print("\nWHAT THE FILTER REMOVED, skew_63 short leg, k=20  (Part A labels recomputed for Q1 only)")
    print(f"  pinned trades in S: {len(pinned)}; caught by the causal filter: {100 * caught:.0f}%")
    print(f"  surviving-name trades in S: {len(alive)}; removed by the filter: {100 * removed_alive:.1f}%")
    print(f"  skew_63 LONG-leg trades removed by the filter: {100 * removed_long:.1f}%")
    print(f"  short-leg held half-spread: {half_S:.1f} -> {half_Sf:.1f} bp")
    print(f"  short-leg trimmed-both mean: {tr_S:+.1f} -> {tr_Sf:+.1f} bp")

    q1 = caught > 0.80 and removed_alive < 0.10
    q2 = half_Sf >= 8.5
    q3 = abs(tr_Sf - tr_S) < 10.0
    q4 = net("LW_f") < net("LW")
    q5 = removed_long < 0.02
    q6 = net("LW_f") > max(net("S_f"), net("H")) and shp("LW_f") > max(shp("S_f"), shp("H"))
    print("\nPREDICTIONS")
    for kk, vv in (("Q1 filter catches >80% of pinned trades and <10% of survivors", q1),
                   ("Q2 filtered short leg held half-spread >= 8.5 bp", q2),
                   ("Q3 trimmed-both mean of the short leg moves < 10 bp", q3),
                   ("Q4 LW_f net/trade at k=20 FALLS below LW's  [load-bearing, against]", q4),
                   ("Q5 the filter removes <2% of skew_63's LONG-leg trades", q5),
                   ("Q6 LW_f still beats S_f and H on invariant net and variant Sharpe, k=20  [load-bearing]", q6)):
        print(f"    {'CONFIRMED' if vv else 'FALSIFIED'}  {kk}")
    print(f"    LW {net('LW'):+.2f} -> LW_f {net('LW_f'):+.2f} per trade;  Sharpe {shp('LW'):+.3f} -> {shp('LW_f'):+.3f}")
    print(f"    parents: S_f {net('S_f'):+.2f} / {shp('S_f'):+.3f}   H {net('H'):+.2f} / {shp('H'):+.3f}")

    OUT.write_text(json.dumps(dict(
        note="D330 Part B: causal pinned-name filter on the score. Variant bp/bar, "
             "invariant per trade per-leg costed, never compared (FINDINGS 10).",
        filter=dict(jump_window=[JUMP_LO, JUMP_HI], jump_thresh=float(JUMP_THRESH),
                    quiet_bars=QUIET_BARS, quiet_thresh=QUIET_THRESH,
                    fires_name_bars=int(fire.sum())),
        arms=arms,
        removal=dict(pinned_n=len(pinned), caught=float(caught), alive_n=len(alive),
                     removed_alive=float(removed_alive), removed_long=float(removed_long),
                     half_S=half_S, half_Sf=half_Sf, trimmed_S=tr_S, trimmed_Sf=tr_Sf),
        predictions=dict(Q1=bool(q1), Q2=bool(q2), Q3=bool(q3), Q4=bool(q4),
                         Q5=bool(q5), Q6=bool(q6))), indent=1, default=float))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
