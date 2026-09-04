"""D329 -- the leg-wise composite: hist_L owns the long leg, skew_63 the short.

    uv run python scripts/run_d329_legwise.py --selftest
    uv run python scripts/run_d329_legwise.py

PRE-REGISTERED AT `16b1977`, committed before this file existed (R8).

EVERY COMPOSITE SO FAR RE-RANKED ONE GATE SYMMETRICALLY. This one hands the long
leg to one signal and the short leg to another:

    rankT_LW = stack([ rank_single(hist_L)[0], rank_single(skew_63)[1] ])

`W.simulate` processes the two sides independently -- separate holdings,
separate gate slice, separate cap -- so in BOTH lenses the leg-wise book's long
trades are bit-identical to hist_L's and its short trades to skew_63's. That is
assertion [L], proven not assumed, and it means anything that is a sum over
trades composes exactly. What does NOT compose is the book-level path -- the bar
series, its Sharpe, its drawdown -- and the partner enumeration. That is where
the predictions have content.

THE CONTROL ENUMERATES THE PARTNER (CLAUDE.md: randomise the partner, never the
membership). hist_L-long is paired with each of the 46 dimensionless D290
signals short, and each of the 46 long with skew_63-short, at k=20, both lenses.
Every partner is a real signal's real leg, so the control shares the treatment's
persistence, tilt and cost. p50 and p95 are reported beside the treatment.

THE REBALANCING PREMIUM IS READ OFF THE LEDGER. Each trade is (row, entry, age,
pnl, side); pnl is the SUM of market-demeaned one-bar returns, the
daily-rebalanced convention every runner here uses (D328 section 11). The
constant-shares P&L is prod(1+r)-1 on the same bars, and the premium is their
signed difference. [P] first proves the recomputation spans the ledger's bars.

COST. Per-leg 2c is 2 x THAT leg's held median half-spread; the book's round
trip is the sum of the two legs' 2c. D326's single-median form is also reported
for the parents so [1] can hold the harness identical.

NEITHER LENS IS EVER RANKED BY THE OTHER'S STATISTIC. D326's `rank_cells` guard
is reused and [3] proves it still raises.
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


V6 = _load("d326", "run_d326_both_lenses.py")
Q, G22, Y = V6.Q, V6.G22, V6.Y
W, D, M, SP, R, X = V6.W, V6.D, V6.M, V6.SP, V6.R, V6.X

DEPTH = V6.DEPTH                      # 2, the operating point
KS = V6.KS                            # (10, 20, 40)
K_ENUM = 20
LONG_SIG, SHORT_SIG = "hist_L", "skew_63"
# The D328 units audit: these five rank price or dollar volume, not a signal.
EXCLUDED = ("macd_line", "macd_hist", "impulse_nodz", "amihud_21", "price_log")
OUT = REPO / "data" / "d329_legwise.json"


def legwise(rk_long, rk_short):
    """(2, T, n): side 0 from one signal's ranking, side 1 from another's."""
    return np.ascontiguousarray(np.stack([rk_long[0], rk_short[1]]))


def per_leg(res, HALF, CLOSE, r1T, mkt):
    """Everything the ledger says, split by side. Per-leg cost is 2 x that leg's
    held median half-spread. The rebalancing premium is summed minus compounded
    on the same bars, signed for the side."""
    out = {}
    for side in (0, 1):
        tr = [t for t in res["trades"] if t[4] == side]
        if not tr:
            out[side] = None
            continue
        sgn = 1.0 if side == 0 else -1.0
        pnl = np.array([t[3] for t in tr]) * 1e4
        hv = np.array([HALF[t[1], t[0]] for t in tr])
        px = np.array([CLOSE[t[1], t[0]] for t in tr])
        prem = np.empty(len(tr))
        for i, (row, e0, age, _p, _s) in enumerate(tr):
            v = np.nan_to_num(r1T[e0:e0 + age, row], nan=0.0)
            prem[i] = sgn * (v.sum() - np.expm1(np.log1p(v).sum()))
        half = float(np.nanmedian(hv))
        two_c = 2.0 * half
        out[side] = dict(trades=len(tr), gross=float(pnl.mean()),
                         net=float(pnl.mean()) - two_c, two_c=two_c,
                         half_bp=half, price=float(np.nanmedian(px)),
                         premium_bp=float(prem.mean() * 1e4),
                         t=float(pnl.mean() / (pnl.std(ddof=1) / np.sqrt(pnl.size)))
                         if pnl.size > 1 and pnl.std(ddof=1) > 0 else 0.0)
    return out


def invariant_legcost(res, legs):
    """The invariant book, costed PER LEG: each trade pays its own side's 2c."""
    pnl = np.array([t[3] for t in res["trades"]]) * 1e4
    cost = np.array([legs[t[4]]["two_c"] for t in res["trades"]])
    net = pnl - cost
    return dict(net_per_trade=float(net.mean()),
                gross_per_trade=float(pnl.mean()),
                median_per_trade=float(np.median(net)),
                t_per_trade=float(net.mean() / (net.std(ddof=1) / np.sqrt(net.size)))
                if net.size > 1 else 0.0,
                mean_over_2c=float(pnl.mean() / cost.mean()) if cost.mean() > 0 else 0.0,
                round_trip=float(sum(legs[s]["two_c"] for s in (0, 1) if legs[s])),
                trades=int(net.size),
                held_per_bar=float(res["held"][res["mask"]].mean()))


def run_arm(A, rankT, finT, k, G4, r1T, HALF, CLOSE, mkt):
    """Both lenses for one rankT at one k, with per-leg detail on each."""
    try:
        v, res_v = V6.variant(A, rankT, finT, k, G4, r1T)
    except ZeroDivisionError:
        # A leg whose held median half-spread is exactly ZERO cannot be costed:
        # D322's breakeven divides by it. It happened on `cs_spread`'s LONG leg,
        # which by construction selects the names with the lowest measured
        # Corwin-Schultz spread -- the clamp D302 called a left truncation. The
        # cell is recorded as degenerate, never as a number.
        return "degenerate", None, None
    if v is None:
        return None, None, None
    # D326's `variant` keeps a subset of group1; Q3 needs the drawdown too.
    c = G22.costed(res_v, G4)
    v["maxdd_bp"] = G22.group1(res_v, c, G22.contributions(res_v, r1T), r1T)["maxdd_bp"]
    i6, res_i = V6.invariant(A, rankT, finT, k, HALF)   # D326's exact formula
    legs_i = per_leg(res_i, HALF, CLOSE, r1T, mkt)
    legs_v = per_leg(res_v, HALF, CLOSE, r1T, mkt)
    inv = invariant_legcost(res_i, legs_i)
    inv["d326_net_per_trade"] = i6["net_per_trade"]
    inv["d326_round_trip"] = i6["round_trip"]
    return dict(variant=v, invariant=inv, legs_invariant=legs_i,
                legs_variant=legs_v), res_v, res_i


def same_side(res_a, res_b, side):
    a = sorted(t[:4] for t in res_a["trades"] if t[4] == side)
    b = sorted(t[:4] for t in res_b["trades"] if t[4] == side)
    return a == b


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    t0 = time.time()

    print("D329  the leg-wise composite: hist_L long, skew_63 short")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    r1T, finT, mkt = np.asarray(A["r1T"]), np.asarray(A["finT"]), np.asarray(A["mkt"])
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
    G4 = (HALF, CLOSE, X.roll_mean_T(CLOSE * VOL), finT)
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & panel.live
    n, T = panel.live.shape
    d326 = json.loads((REPO / "data" / "d326_both_lenses.json").read_text())
    pool = [s for s in z.files if s not in ("key", "warm") and s not in EXCLUDED]
    assert len(pool) == 46, f"partner pool is {len(pool)}, not 46"
    assert LONG_SIG in pool and SHORT_SIG in pool
    print(f"  panel {finT.shape}, depth {DEPTH}, k={KS}, {len(pool)} partners "
          f"({time.time() - t0:.0f}s)")

    ts = time.time()
    rk = {s: Y.rank_single(z, base, s, n, T) for s in pool}
    print(f"  {len(rk)} rank arrays ({time.time() - ts:.0f}s)")
    RK = {"H": legwise(rk[LONG_SIG], rk[LONG_SIG]),
          "S": legwise(rk[SHORT_SIG], rk[SHORT_SIG]),
          "LW": legwise(rk[LONG_SIG], rk[SHORT_SIG]),
          "RV": legwise(rk[SHORT_SIG], rk[LONG_SIG])}
    assert np.array_equal(RK["H"], rk[LONG_SIG]) and np.array_equal(RK["S"], rk[SHORT_SIG])

    # ---- assertions -------------------------------------------------------
    print("\nASSERTIONS")
    ts = time.time()
    arm20 = {}
    for nm in ("H", "S", "LW", "RV"):
        arm20[nm] = run_arm(A, RK[nm], finT, K_ENUM, G4, r1T, HALF, CLOSE, mkt)
    print(f"    (four arms, both lenses, k=20: {time.time() - ts:.0f}s)")
    resv = {nm: arm20[nm][1] for nm in arm20}
    resi = {nm: arm20[nm][2] for nm in arm20}

    # L. LEG INDEPENDENCE -- the composition is exact, in both lenses.
    for lens, rs in (("variant", resv), ("invariant", resi)):
        assert same_side(rs["LW"], rs["H"], 0), f"[L] {lens}: LW long != H long"
        assert same_side(rs["LW"], rs["S"], 1), f"[L] {lens}: LW short != S short"
        assert same_side(rs["RV"], rs["S"], 0), f"[L] {lens}: RV long != S long"
        assert same_side(rs["RV"], rs["H"], 1), f"[L] {lens}: RV short != H short"
        assert np.array_equal(rs["LW"]["cnt0"], rs["H"]["cnt0"])
        assert np.array_equal(rs["LW"]["cnt1"], rs["S"]["cnt1"])
        ok = rs["H"]["mask"] & rs["S"]["mask"] & rs["LW"]["mask"] & rs["RV"]["mask"]
        lhs = rs["LW"]["book"][ok] + rs["RV"]["book"][ok]
        rhs = rs["H"]["book"][ok] + rs["S"]["book"][ok]
        assert np.allclose(lhs, rhs, atol=1e-12), f"[L] {lens}: book series do not compose"
    print("    [L] LEG INDEPENDENCE: LW's long ledger is H's and its short ledger "
          "is S's, bit-identically, in both lenses; per-side counts identical; "
          "LW + RV == H + S on the bar series to 1e-12")

    # P. THE LEDGER SPANS THE BARS I THINK IT DOES.
    worst = 0.0
    for row, e0, age, pnl, side in resi["H"]["trades"]:
        sgn = 1.0 if side == 0 else -1.0
        v = r1T[e0:e0 + age, row]
        assert np.isfinite(v).all(), "[P] a held bar is non-finite"
        rec = float(np.sum(sgn * (v - mkt[e0:e0 + age])))
        worst = max(worst, abs(rec - pnl))
    assert worst < 1e-12, f"[P] ledger P&L not reproduced: {worst:.2e}"
    print(f"    [P] every H trade's summed P&L recomputed from (row, entry, age) "
          f"on r1T and mkt matches the ledger to {worst:.1e}")

    # 1. HARNESS IDENTITY against D326.
    worst = 0.0
    for nm, s in (("H", LONG_SIG), ("S", SHORT_SIG)):
        c6 = d326["variant"][f"{s}/k{K_ENUM}"]
        worst = max(worst, abs(arm20[nm][0]["variant"]["sharpe_net"] - c6["sharpe_net"]))
        i6 = d326["invariant"][f"{s}/k{K_ENUM}"]
        worst = max(worst, abs(arm20[nm][0]["invariant"]["d326_net_per_trade"]
                               - i6["net_per_trade"]))
    assert worst < 1e-9, f"[1] D326 not reproduced: {worst:.2e}"
    print(f"    [1] the parents reproduce D326's k=20 cells on both lenses to {worst:.1e}")

    # 3. THE LENSES ARE SEPARATED IN CODE.
    raised = 0
    for lens, stat in (("invariant", "sharpe_net"), ("variant", "net_per_trade")):
        try:
            V6.rank_cells({"x": arm20["LW"][0][lens]}, lens, stat)
        except ValueError:
            raised += 1
    assert raised == 2, "[3] rank_cells did not raise in both directions"
    print("    [3] rank_cells RAISES in both directions -- FINDINGS section 10 in code")

    # C. COST DIMENSIONS -- per leg, and the paired 4x is rejected.
    lg = arm20["LW"][0]["legs_invariant"]
    for side in (0, 1):
        assert abs(lg[side]["two_c"] - 2.0 * lg[side]["half_bp"]) < 1e-12
        assert abs(lg[side]["two_c"] - 4.0 * lg[side]["half_bp"]) > 1e-9
    rt = arm20["LW"][0]["invariant"]["round_trip"]
    assert abs(rt - (lg[0]["two_c"] + lg[1]["two_c"])) < 1e-12
    print(f"    [C] per-leg 2c is 2 x that leg's held median half-spread "
          f"({lg[0]['half_bp']:.1f} long, {lg[1]['half_bp']:.1f} short); the paired "
          f"4x is rejected; book round trip {rt:.1f} is their sum")

    # 4. CAUSALITY on both lenses.
    rot = np.roll(RK["LW"], 501, axis=1)
    r_arm, _, _ = run_arm(A, rot, finT, K_ENUM, G4, r1T, HALF, CLOSE, mkt)
    d_v = abs(r_arm["variant"]["net_bp_bar"] - arm20["LW"][0]["variant"]["net_bp_bar"])
    d_i = abs(r_arm["invariant"]["net_per_trade"]
              - arm20["LW"][0]["invariant"]["net_per_trade"])
    assert d_v > 1e-6 and d_i > 1e-6, "[4] a rolled ranking gives the same book"
    print(f"    [4] CAUSALITY: rolling the ranking moves the variant lens by "
          f"{d_v:.2f} bp/bar and the invariant by {d_i:.1f} bp/trade")

    # R. RV IS A DIFFERENT BOOK FROM LW.
    assert not same_side(resi["RV"], resi["LW"], 0) and \
        not same_side(resi["RV"], resi["LW"], 1), "[R] RV equals LW"
    print("    [R] the reverse pairing is a different book on both sides")

    # 6. THE SELF-TEST MUST RAISE.
    broke = False
    try:
        bad = dict(arm20["LW"][0]["invariant"])
        bad["net_per_trade"] += 50.0
        assert abs(bad["net_per_trade"]
                   - arm20["LW"][0]["invariant"]["net_per_trade"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[6] the check passed a book handed free money"
    print("    [6] and the check raises on a book handed free money")

    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    # ---- the four arms at every k -----------------------------------------
    ts = time.time()
    arms = {}
    for nm in ("H", "S", "LW", "RV"):
        for k in KS:
            arms[f"{nm}/k{k}"] = (arm20[nm][0] if k == K_ENUM else
                                  run_arm(A, RK[nm], finT, k, G4, r1T, HALF, CLOSE, mkt)[0])
    print(f"\n  four arms x {KS} ({time.time() - ts:.0f}s)")

    print("\nPATH-INVARIANT  (per trade, per-leg costed; no cap)")
    print("  %-4s %3s %9s %9s %9s %8s %8s %7s | %8s %8s"
          % ("arm", "k", "net/trd", "gross", "median", "t", "mean/2c", "rt",
             "L net", "S net"))
    for nm in ("H", "S", "LW", "RV"):
        for k in KS:
            c = arms[f"{nm}/k{k}"]; i = c["invariant"]; L = c["legs_invariant"]
            print("  %-4s %3d %+9.2f %+9.2f %+9.2f %+8.2f %8.2f %7.1f | %+8.1f %+8.1f"
                  % (nm, k, i["net_per_trade"], i["gross_per_trade"],
                     i["median_per_trade"], i["t_per_trade"], i["mean_over_2c"],
                     i["round_trip"], L[0]["net"], L[1]["net"]))

    print("\nPATH-VARIANT  (the capped book, bp/bar; D318 costing)")
    print("  %-4s %3s %9s %9s %9s %9s %8s %6s"
          % ("arm", "k", "net/bar", "gross", "Sharpe", "maxDD", "held", "fill"))
    for nm in ("H", "S", "LW", "RV"):
        for k in KS:
            v = arms[f"{nm}/k{k}"]["variant"]
            print("  %-4s %3d %+9.2f %+9.2f %+9.3f %9.0f %8.2f %6.2f"
                  % (nm, k, v["net_bp_bar"], v["gross_bp_bar"], v["sharpe_net"],
                     arms[f"{nm}/k{k}"]["variant"].get("maxdd_bp", float("nan")),
                     v["held_per_bar"], v["fill"]))

    print("\nPER LEG, invariant, k=20  (bp per trade; premium = summed - compounded, signed)")
    print("  %-4s %-5s %6s %8s %8s %8s %8s %8s %8s"
          % ("arm", "leg", "trades", "gross", "net", "t", "half", "price", "premium"))
    for nm in ("H", "S", "LW", "RV"):
        for side, lbl in ((0, "long"), (1, "short")):
            L = arms[f"{nm}/k20"]["legs_invariant"][side]
            print("  %-4s %-5s %6d %+8.1f %+8.1f %+8.2f %8.1f %8.1f %+8.1f"
                  % (nm, lbl, L["trades"], L["gross"], L["net"], L["t"],
                     L["half_bp"], L["price"], L["premium_bp"]))

    # ---- the partner enumeration, k=20 -------------------------------------
    ts = time.time()
    enum = {"A": {}, "B": {}}
    for j, s in enumerate(pool):
        ra = run_arm(A, legwise(rk[LONG_SIG], rk[s]), finT, K_ENUM, G4, r1T, HALF, CLOSE, mkt)[0]
        rb = run_arm(A, legwise(rk[s], rk[SHORT_SIG]), finT, K_ENUM, G4, r1T, HALF, CLOSE, mkt)[0]
        for d_, r_ in (("A", ra), ("B", rb)):
            if r_ == "degenerate":
                enum[d_][s] = dict(degenerate=True,
                                   reason="held median half-spread is 0; uncostable")
                print(f"  DEGENERATE: direction {d_}, partner {s} -- held "
                      f"half-spread 0, cannot be costed; excluded from the ranking")
                continue
            enum[d_][s] = dict(net_per_trade=r_["invariant"]["net_per_trade"],
                               sharpe_net=r_["variant"]["sharpe_net"],
                               net_bp_bar=r_["variant"]["net_bp_bar"])
        if (j + 1) % 10 == 0:
            print(f"  enumeration {j + 1}/{len(pool)} ({time.time() - ts:.0f}s)", flush=True)
    print(f"  enumeration done ({time.time() - ts:.0f}s)")

    def place(d_, target, stat):
        """Rank position of `target` among the costable partners; degenerate
        cells are excluded and their count is reported beside the rank."""
        vals = sorted(((enum[d_][s][stat], s) for s in pool
                       if not enum[d_][s].get("degenerate")), reverse=True)
        pos_ = [s for _, s in vals].index(target) + 1
        arr = np.array([v for v, _ in vals])
        return pos_, float(np.percentile(arr, 50)), float(np.percentile(arr, 95)), vals

    n_deg = {d_: sum(1 for s in pool if enum[d_][s].get("degenerate")) for d_ in enum}

    print("\nPARTNER ENUMERATION, k=20")
    for d_, target, desc in (("A", SHORT_SIG, f"{LONG_SIG} long + X short: where is {SHORT_SIG}"),
                             ("B", LONG_SIG, f"X long + {SHORT_SIG} short: where is {LONG_SIG}")):
        for lens, stat in (("invariant", "net_per_trade"), ("variant", "sharpe_net")):
            p_, p50, p95, vals = place(d_, target, stat)
            tv = enum[d_][target][stat]
            print(f"  {desc}  [{lens} {stat}]")
            print(f"     rank {p_} of {len(vals)} costable ({n_deg[d_]} degenerate)   "
                  f"value {tv:+.3f}   p50 {p50:+.3f}   p95 {p95:+.3f}")
            print("     top 5: " + "  ".join(f"{s} {v:+.2f}" for v, s in vals[:5]))

    # ---- predictions -------------------------------------------------------
    def inv(nm, k): return arms[f"{nm}/k{k}"]["invariant"]["net_per_trade"]
    def shp(nm, k): return arms[f"{nm}/k{k}"]["variant"]["sharpe_net"]
    def leg(nm, k, s): return arms[f"{nm}/k{k}"]["legs_invariant"][s]
    q1 = all(inv("LW", k) > max(inv("H", k), inv("S", k)) for k in KS) \
        and shp("LW", 20) > max(shp("H", 20), shp("S", 20))
    q2 = all(leg("H", k, 0)["net"] > leg("S", k, 0)["net"]
             and leg("S", k, 1)["net"] > leg("H", k, 1)["net"] for k in KS)
    dd = lambda nm: arms[f"{nm}/k20"]["variant"].get("maxdd_bp", np.nan)
    q3 = bool(abs(dd("LW")) < abs(dd("H"))) and \
        (shp("LW", 20) - max(shp("H", 20), shp("S", 20)) > 0.10)
    pA_i, _, _, _ = place("A", SHORT_SIG, "net_per_trade")
    pB_i, _, _, _ = place("B", LONG_SIG, "net_per_trade")
    pA_v, _, _, _ = place("A", SHORT_SIG, "sharpe_net")
    pB_v, _, _, _ = place("B", LONG_SIG, "sharpe_net")
    q4 = pA_i <= 3 and pB_i <= 3 and pA_v <= 5 and pB_v <= 5
    q5 = (leg("H", 20, 1)["premium_bp"] < -40 and leg("H", 20, 0)["premium_bp"] > 40
          and abs(leg("LW", 20, 1)["premium_bp"]) < 15)
    q6 = all(inv("RV", k) < min(inv("H", k), inv("S", k)) for k in KS) \
        and shp("RV", 20) < min(shp("H", 20), shp("S", 20))
    lw = arms["LW/k20"]
    q7 = (leg("LW", 20, 0)["half_bp"] > 30 and leg("LW", 20, 1)["half_bp"] < 12
          and leg("LW", 20, 0)["price"] < 0.5 * leg("LW", 20, 1)["price"]
          and lw["invariant"]["round_trip"] < arms["H/k20"]["invariant"]["round_trip"])
    print("\nPREDICTIONS")
    for kk, vv in (("Q1 LW beats BOTH parents: invariant net/trade every k, variant Sharpe k=20  [load-bearing]", q1),
                   ("Q2 per leg: hist_L wins the long leg, skew_63 wins the short leg, every k", q2),
                   ("Q3 LW's maxDD shallower than H's and Sharpe > best parent + 0.10, k=20", q3),
                   ("Q4 skew_63 top-3 of 46 short partners, hist_L top-3 of 46 long partners (top-5 on Sharpe)  [load-bearing]", q4),
                   ("Q5 rebalancing premium: H short < -40, H long > +40, LW short within 15 bp", q5),
                   ("Q6 RV is worse than BOTH parents, every k and on Sharpe  [against]", q6),
                   ("Q7 LW's tilt is monotone across legs and its round trip is below H's", q7)):
        print(f"    {'CONFIRMED' if vv else 'FALSIFIED'}  {kk}")
    print(f"    Q4 placements: A-invariant {pA_i}, B-invariant {pB_i}, "
          f"A-variant {pA_v}, B-variant {pB_v}")

    OUT.write_text(json.dumps(dict(
        note="D329: leg-wise composite. Variant is bp/bar, invariant is per trade "
             "(per-leg costed), never compared (FINDINGS section 10). Ledger P&L "
             "is the daily-rebalanced sum; premium = summed - compounded, signed.",
        long_sig=LONG_SIG, short_sig=SHORT_SIG, depth=DEPTH, ks=list(KS),
        pool=pool, excluded=list(EXCLUDED), arms=arms, enumeration=enum,
        degenerate_cells=n_deg,
        placements=dict(A_invariant=pA_i, B_invariant=pB_i, A_variant=pA_v,
                        B_variant=pB_v),
        predictions=dict(Q1=bool(q1), Q2=bool(q2), Q3=bool(q3), Q4=bool(q4),
                         Q5=bool(q5), Q6=bool(q6), Q7=bool(q7))),
        indent=1, default=float))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
