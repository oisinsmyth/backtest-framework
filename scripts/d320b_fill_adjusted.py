"""D320b -- the filters shrink the book, and that changes both the cost and the claim.

    uv run python scripts/d320b_fill_adjusted.py

POST-HOC, prompted by D320's own held-per-bar diagnostic. It re-costs D320's cells
and reinterprets them; it runs no new construction.

TWO THINGS THE MAIN RUNNER GOT WRONG, both from the same fact.

D306's simulator weights each held name 1/n_t within its leg -- `ret[side][t] =
mean(buf[:k])`, and its own comment says "NOT 1/depth". So a book that cannot fill
its slots is NOT partly in cash: it is a FULLY INVESTED, NARROWER book.

  1. THE COST IS UNDERSTATED. `turn = entries / depth / 2 / bars` divides by the
     NOMINAL slot count. The fraction of the book actually traded divides by the
     names actually HELD, so cost is understated by exactly 1/fill.

  2. AND THE CLAIM IS WRONG. A filter that leaves a 19-slot book holding 14.3
     names is not a tilt result -- it is D300's width axis arriving through the
     back door, which is precisely the confound D305 identified and named:
     "every arm that blocks re-entry also shrinks the book ... its positive net is
     bought by holding half as much."

D320's two BH survivors run at 74% and 57% of slots, and its best net Sharpe cell
runs at 38%.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "data" / "d320b_fill_adjusted.json"
ANN = 252.0


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


X = _load("d320", "run_d320_tilt_filters.py")
W, D, M, SP = X.W, X.D, X.M, X.SP


def main() -> int:
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
    V = {"spread": X.roll_mean_T(HALF), "price": X.roll_mean_T(CLOSE),
         "dv": X.roll_mean_T(CLOSE * VOL)}
    ones = np.ones(finT.shape, bool)
    d320 = json.loads((REPO / "data" / "d320_tilt_filters.json").read_text())

    print("D320b  fill-adjusted -- the filters shrink the book")
    print("  weight is 1/n_t, so a book that cannot fill its slots is a NARROWER")
    print("  book at full notional, not a book partly in cash.\n")
    h = "%-16s %8s %7s %9s %9s %9s %9s %9s"
    print(h % ("cell", "held/bar", "fill", "gross", "NET pub", "NET adj",
               "SHRP pub", "SHRP adj"))
    print("-" * 82)
    out = {}
    for depth in (2, 19):
        cells = [("control", None, None)] + [
            (arm, p, None) for arm in X.ARMS for p in X.PCTS]
        for arm, p, _ in cells:
            keep = ones if arm == "control" else \
                X.keep_mask(V[arm], finT, p, X.BAD_LOW[arm])
            res = W.simulate(A, X.gate_with(A, keep), depth, True)
            ok = res["mask"]
            held = float(res["held"][ok].mean())
            fill = held / (2.0 * depth)
            hs = X.held_median(res, HALF)
            px = X.held_median(res, CLOSE)
            rt = 4.0 * hs
            rtc = X.CROSSINGS * X.PER_SHARE / px * 1e4
            c = X.cell(res, depth, rt, rtc)
            # THE FIX: divide by the names actually held, not the nominal slots
            turn_adj = c["turnover"] / fill
            net_adj = c["gross_bp"] - (rt + rtc) * turn_adj
            nm = "N=%d/%s" % (depth, "control" if arm == "control"
                              else f"{arm}{p:g}")
            out[nm] = dict(held_per_bar=held, fill=fill, gross=c["gross_bp"],
                           net_pub=c["net_bp"], net_adj=net_adj,
                           sharpe_pub=c["sharpe_net"],
                           sharpe_adj=net_adj / c["vol_bp"] * np.sqrt(ANN),
                           turnover_pub=c["turnover"], turnover_adj=turn_adj,
                           round_trip=rt, held_half_spread=hs, held_price=px)
            r = out[nm]
            print(h % (nm, "%.2f" % held, "%.0f%%" % (100 * fill),
                       "%+.2f" % r["gross"], "%+.2f" % r["net_pub"],
                       "%+.2f" % r["net_adj"], "%+.3f" % r["sharpe_pub"],
                       "%+.3f" % r["sharpe_adj"]))
        print("-" * 82)

    print("\nWHAT SURVIVES THE FIX")
    k2 = out["N=2/control"]
    best = max((v for k, v in out.items() if k.startswith("N=2/")
                and k != "N=2/control"), key=lambda v: v["sharpe_adj"])
    print("  N=2 control        net %+.2f  netSHRP %+.3f  fill %.0f%%"
          % (k2["net_adj"], k2["sharpe_adj"], 100 * k2["fill"]))
    for k, v in out.items():
        if k.startswith("N=2/") and v["sharpe_adj"] > k2["sharpe_adj"]:
            print("  %-18s net %+.2f  netSHRP %+.3f  fill %.0f%%  BEATS control"
                  % (k, v["net_adj"], v["sharpe_adj"], 100 * v["fill"]))
    print("\n  D320's BH survivors and best cell, fill-adjusted:")
    for k in ("N=19/price25", "N=19/price40", "N=19/spread40"):
        v = out[k]
        print("  %-18s fill %3.0f%%   netSHRP %+.3f -> %+.3f   net %+.2f -> %+.2f"
              % (k, 100 * v["fill"], v["sharpe_pub"], v["sharpe_adj"],
                 v["net_pub"], v["net_adj"]))
    print("\n  and the fill-adjusted books, compared to the STATIC width that")
    print("  holds the same number of names -- the D305 confound made explicit:")
    for k in ("N=19/spread40", "N=19/price40"):
        v = out[k]
        print("    %-16s holds %.1f names, i.e. about N_eff = %.0f per leg"
              % (k, v["held_per_bar"], v["held_per_bar"] / 2))

    OUT.write_text(json.dumps(dict(
        note="POST-HOC. Turnover re-derived on names actually held rather than "
             "nominal slots, because D306's simulator weights 1/n_t. A filter "
             "that shrinks the book is D300's width axis, not a tilt result.",
        cells=out), indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
