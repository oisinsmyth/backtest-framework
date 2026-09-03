"""D309 -- the N=1 static book, measured against N=2.

    uv run python scripts/d309_n1_static.py

WHY. D300 and D306 both put the optimum at N=2, which is the SMALLEST width
either ever tested. An optimum on the grid boundary has never been shown to be
interior. This measures N=1 -- one long name and one short name -- through the
same four exit families, so the boundary has a point on the other side of it.

A MEASUREMENT. Nothing is searched, nothing is promoted, no record is written.

HOW. Every number comes out of `scripts/run_d306_width_exits.py`, loaded as a
module and called; not one line of its machinery is reimplemented here, and the
file itself is not touched. `contributions()` for the trimmed figures is
imported from `scripts/d307c_trimmed_nets.py` for the same reason.

TWO CHECKS, both reported:
  [1] held_per_bar must be ~2.0 at depth 1 and ~4.0 at depth 2. If depth 1 does
      not hold exactly one name per leg, the simulator does not behave at the
      boundary and nothing below is trustworthy.
  [2] the depth-2 cells recomputed here must reproduce data/d306_width_exits.json
      on gross_bp to ~1e-9. If they do not, this harness is not reproducing D306
      and the comparison is meaningless.
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


W = _load("d306", "run_d306_width_exits.py")
T7 = _load("d307c", "d307c_trimmed_nets.py")
D, SP, M = W.D, W.SP, W.M

DEPTHS = (1, 2)
OUT = REPO / "data" / "d309_n1_static.json"
D306 = REPO / "data" / "d306_width_exits.json"


def main() -> int:
    t0 = time.time()
    print(f"D309  N=1 static book vs N=2  gate={W.N_BASE} k={W.BASE_HOLD}")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    G = W.build_gate(A, verbose=False)
    r1T = np.asarray(A["r1T"])
    T = r1T.shape[0]
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    half = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    ones = np.ones(T)
    print(f"  loaded ({time.time() - t0:.0f}s)")

    ref = json.loads(D306.read_text())["cells"]
    cells = {}
    for depth in DEPTHS:
        for ut in (False, True):
            res = W.simulate(A, G, depth, ut)
            rt = W.held_rt(res, half)
            sc_ov = W.overlay_scale(res["book"])
            bars = int(res["mask"].sum())
            for ov in (False, True):
                scale = sc_ov if ov else ones
                name = ("none" if not ut else "target") + ("+overlay" if ov else "")
                key = f"N={depth}/{name}"
                st = W.stats(res, depth, scale, rt, half)
                st.update(depth=depth, exit=name)

                # --- the trimmed figures, D307c's decomposition verbatim -----
                c = T7.contributions(res, r1T, scale)
                attributed = float(c.sum()) / bars * 1e4
                resid = st["gross_bp"] - attributed   # positions still OPEN at T-1
                n = c.size
                k = max(1, n // 100)
                s = np.sort(c)
                trim_gross = float(s[k:-k].sum()) / bars * 1e4 + resid
                cost = st["cost_pos_bp"] + st["cost_overlay_bp"]
                keep = (st["entries"] - 2 * k) / st["entries"]
                cost_never = st["cost_pos_bp"] * keep + st["cost_overlay_bp"]
                st.update(trim_k=k, trim_residual_bp=resid,
                          trimmed_gross_bp=trim_gross,
                          trimmed_net_bp=trim_gross - cost,
                          never_net_bp=trim_gross - cost_never,
                          top1_bp=float(s[-k:].sum()) / bars * 1e4,
                          bottom1_bp=float(s[:k].sum()) / bars * 1e4,
                          cost_total_bp=cost)
                cells[key] = st
        print(f"  N={depth} done ({time.time() - t0:.0f}s)", flush=True)

    # ---- CHECK 1: the book holds what the depth says it holds --------------
    print("\nCHECK [1] held_per_bar")
    c1_ok = True
    c1 = {}
    for key, st in cells.items():
        want = 2.0 * st["depth"]
        got = st["held_per_bar"]
        good = abs(got - want) < 0.05 * want
        c1_ok &= good
        c1[key] = dict(held_per_bar=got, expected=want, ok=bool(good))
        print(f"    {key:<22} held/bar = {got:.6f}   expected ~{want:.1f}   "
              f"{'OK' if good else '*** FAIL ***'}")
    if not c1_ok:
        print("\n  *** LOUD FAILURE: the simulator does not hold one name per "
              "leg at depth 1. NOTHING BELOW IS TRUSTWORTHY. ***")

    # ---- CHECK 2: depth 2 must be D306's depth 2 ---------------------------
    worst, c2 = 0.0, {}
    for name in ("none", "target", "none+overlay", "target+overlay"):
        key = f"N=2/{name}"
        d = abs(cells[key]["gross_bp"] - ref[key]["gross_bp"])
        c2[key] = dict(here=cells[key]["gross_bp"], d306=ref[key]["gross_bp"],
                       abs_diff=d)
        worst = max(worst, d)
    print(f"\nCHECK [2] N=2 vs data/d306_width_exits.json, max |gross_bp| "
          f"difference = {worst:.3e} bp   "
          f"{'OK' if worst < 1e-9 else '*** FAIL -- HARNESS DOES NOT REPRODUCE D306 ***'}")
    if worst >= 1e-9:
        for key, v in c2.items():
            print(f"    {key:<22} here {v['here']:.12f}  d306 {v['d306']:.12f}")
        print("\n  STOPPING: the harness is not reproducing D306.")
        OUT.write_text(json.dumps(dict(
            purpose="D309: the N=1 static book measured against N=2.",
            check_held_per_bar=c1, check_d306_match=c2,
            check_d306_max_abs_diff=worst, ABORTED=True, cells=cells), indent=1))
        return 1

    # ---- the table ---------------------------------------------------------
    order = [f"N={d}/{n}" for n in ("none", "target", "none+overlay",
                                    "target+overlay") for d in DEPTHS]
    print("\nEIGHT CELLS  (bp per bar unless noted)")
    h = ("%-22s %8s %8s %7s %9s %6s %7s %7s %7s %7s %7s %8s %6s %8s %8s")
    print(h % ("cell", "gross", "vol", "sharpe", "maxdd", "expo", "held/b",
               "turn", "rt", "cost_p", "cost_o", "NET", "trades", "tr_mean",
               "tr_med"))
    print("-" * 152)
    for key in order:
        s = cells[key]
        print(h % (key, "%+.2f" % s["gross_bp"], "%.1f" % s["vol_bp"],
                   "%.3f" % s["sharpe"], "%.0f" % s["maxdd_bp"],
                   "%.3f" % s["exposure"], "%.3f" % s["held_per_bar"],
                   "%.4f" % s["turnover"], "%.2f" % s["round_trip"],
                   "%.2f" % s["cost_pos_bp"], "%.2f" % s["cost_overlay_bp"],
                   "%+.2f" % s["net_bp"], "%d" % s["trades"],
                   "%+.2f" % s["trade_mean_bp"], "%+.2f" % s["trade_median_bp"]))

    print("\nTRIMMED  (top and bottom 1% of trade contributions removed from "
          "P&L; cost LEFT IN PLACE)")
    h2 = "%-22s %6s %9s %9s %9s %10s %9s %11s %11s"
    print(h2 % ("cell", "k", "gross", "top1%", "bot1%", "TRIM GROSS", "cost",
                "TRIM NET", "NEVER NET"))
    print("-" * 108)
    for key in order:
        s = cells[key]
        print(h2 % (key, "%d" % s["trim_k"], "%+.2f" % s["gross_bp"],
                    "%+.2f" % s["top1_bp"], "%+.2f" % s["bottom1_bp"],
                    "%+.2f" % s["trimmed_gross_bp"], "%.2f" % s["cost_total_bp"],
                    "%+.2f" % s["trimmed_net_bp"], "%+.2f" % s["never_net_bp"]))

    print("\nN=1 MINUS N=2")
    h3 = "%-18s %10s %10s %10s %10s"
    print(h3 % ("family", "d_gross", "d_net", "d_sharpe", "d_trimnet"))
    print("-" * 62)
    deltas = {}
    for name in ("none", "target", "none+overlay", "target+overlay"):
        a, b = cells[f"N=1/{name}"], cells[f"N=2/{name}"]
        deltas[name] = dict(
            d_gross_bp=a["gross_bp"] - b["gross_bp"],
            d_net_bp=a["net_bp"] - b["net_bp"],
            d_sharpe=a["sharpe"] - b["sharpe"],
            d_trimmed_net_bp=a["trimmed_net_bp"] - b["trimmed_net_bp"])
        d = deltas[name]
        print(h3 % (name, "%+.2f" % d["d_gross_bp"], "%+.2f" % d["d_net_bp"],
                    "%+.3f" % d["d_sharpe"], "%+.2f" % d["d_trimmed_net_bp"]))

    OUT.write_text(json.dumps(dict(
        purpose="D309: the N=1 static book -- one long, one short -- measured "
                "through D306's four exit families and reported against N=2. "
                "A measurement; nothing searched, nothing promoted.",
        note="N=2 is RECOMPUTED here, not copied, and checked against "
             "data/d306_width_exits.json.",
        overlay="D297 X=12 s=0.0, applied to the return series only",
        trim="D307c's contributions(): weight 1/n_t on the trade's own leg, "
             "zero off the book mask; top and bottom 1% removed from P&L with "
             "the cost left in place.",
        check_held_per_bar=c1, check_held_per_bar_ok=bool(c1_ok),
        check_d306_match=c2, check_d306_max_abs_diff=worst,
        deltas_n1_minus_n2=deltas, cells=cells), indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
