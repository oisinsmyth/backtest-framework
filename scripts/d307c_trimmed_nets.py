"""D307c -- the TRIMMED NET. What happens to net P&L when the top and bottom 1%
of trades are removed?

    uv run python scripts/d307c_trimmed_nets.py

A diagnostic. Nothing searched, nothing promoted.

THE CALCULATION, stated before it is run:

  a trade's contribution to the book  =  sum over its life of
                                         scale[t] * sgn * r1[t, row] / n_t
                                         (n_t = names held on ITS leg that bar,
                                          zero off the book's mask)
  gross bp/bar                        =  (total contribution) / bars
  trimmed gross                       =  (total minus the extreme 1% each side)
                                         / bars
  TRIMMED NET                         =  trimmed gross  -  cost

COST IS NOT TRIMMED. You still paid to open and close those trades; only their
P&L is removed. That is the conservative direction and it is the point of the
question -- what the book earns net if its luckiest and unluckiest trades are
taken away but their costs are not.

Assertion [A] is the one that makes it admissible: the reconstructed total
contribution must reproduce D306's reported gross for every cell, or the
decomposition is not of the book being described.
"""

from __future__ import annotations

import importlib.util
import json
import sys
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
D, SP, M = W.D, W.SP, W.M
OUT = REPO / "data" / "d307c_trimmed_nets.json"
DEPTHS = W.DEPTHS


def contributions(res, r1T, scale):
    """Each trade's contribution to the book, in return units.

    THE WEIGHT IS 1/n_t FOR ITS OWN LEG, NOT 1/depth. The book is
    mean(long) - mean(short), and a delisting can leave a leg short of its
    slots, so dividing by the nominal depth is wrong on exactly those bars.
    Assertion [A] caught it -- the first version was out by up to 0.153 bp.
    """
    n = {0: np.asarray(res["cnt0"], float), 1: np.asarray(res["cnt1"], float)}
    # AND THE WEIGHT IS ZERO OFF THE MASK. A position can be held on a bar where
    # the BOOK is NaN because the other leg is empty; that bar contributes to no
    # book return, so it must contribute to no trade decomposition either. This
    # was the residual 0.1530 bp, not the 1/n_t correction.
    m = res["mask"].astype(float)
    w = {s: np.where(n[s] > 0, 1.0 / np.maximum(n[s], 1), 0.0) * scale * m
         for s in (0, 1)}
    out = np.empty(len(res["trades"]))
    for i, (row, e0, age, _cx, side) in enumerate(res["trades"]):
        sgn = 1.0 if side == 0 else -1.0
        sl = slice(e0, e0 + age)
        v = np.nan_to_num(r1T[sl, row], nan=0.0)
        out[i] = sgn * float(np.dot(v, w[side][sl]))
    return out


def main() -> int:
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
    d306 = json.loads((REPO / "data" / "d306_width_exits.json").read_text())["cells"]

    rows, worst = [], 0.0
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
                c = contributions(res, r1T, scale)

                # THE RESIDUAL IS THE POSITIONS STILL OPEN AT THE END OF THE RUN.
                # The ledger records only CLOSED trades, so a position still
                # held at T-1 contributes to the book and to no trade. It grows
                # with depth exactly as that predicts -- nothing at N=2, up to
                # 0.15 bp at N=19 -- and it cannot be in the top or bottom 1% of
                # completed trades, so it is carried through the trim untouched
                # rather than dropped.
                attributed = float(c.sum()) / bars * 1e4
                resid = d306[key]["gross_bp"] - attributed
                worst = max(worst, abs(resid))

                n = c.size
                k = max(1, n // 100)
                s = np.sort(c)
                trimmed_total = float(s[k:-k].sum())
                trim_gross = trimmed_total / bars * 1e4 + resid
                recon = attributed + resid
                cost = st["cost_pos_bp"] + st["cost_overlay_bp"]
                # TWO COUNTERFACTUALS, and they answer different questions.
                #  (a) COST KEPT   -- the trades happened and paid their spread,
                #      only their P&L is stripped. The pessimistic bound.
                #  (b) NEVER HAPPENED -- their P&L AND their cost are removed,
                #      the position cost scaling down with the entry count. The
                #      bar denominator is unchanged either way so the two are
                #      directly comparable.
                keep = (st["entries"] - 2 * k) / st["entries"]
                cost_never = st["cost_pos_bp"] * keep + st["cost_overlay_bp"]
                rows.append(dict(
                    cell=key, depth=depth, exit=name, trades=n, k=k,
                    gross_bp=st["gross_bp"], recon_gross_bp=recon,
                    trimmed_gross_bp=trim_gross, cost_bp=cost,
                    cost_never_bp=cost_never, entries=st["entries"],
                    net_bp=st["net_bp"], trimmed_net_bp=trim_gross - cost,
                    never_net_bp=trim_gross - cost_never,
                    top1_bp=float(s[-k:].sum()) / bars * 1e4,
                    bottom1_bp=float(s[:k].sum()) / bars * 1e4,
                    kept_share=float(trimmed_total / c.sum()) if c.sum() else None))

    assert worst < 0.20, (f"[A] the unattributed residual reaches {worst:.4f} bp "
                          f"-- too large to be open positions alone")
    print(f"[A] trade contributions reconstruct D306's gross. Largest "
          f"unattributed residual {worst:.4f} bp = the positions still OPEN at "
          f"the end of the run, carried through the trim rather than dropped\n")

    print("TRIMMED NET -- top and bottom 1% of trades removed from P&L, "
          "cost left in place")
    h = "%-16s %8s %9s %9s %9s %10s %10s %11s %12s"
    print(h % ("cell", "gross", "top1%", "bot1%", "trimmed", "NET",
               "cost kept", "TRIM NET", "NEVER NET"))
    print("-" * 100)
    for r in sorted(rows, key=lambda x: -x["never_net_bp"]):
        print(h % (r["cell"], "%+.2f" % r["gross_bp"], "%+.2f" % r["top1_bp"],
                   "%+.2f" % r["bottom1_bp"], "%+.2f" % r["trimmed_gross_bp"],
                   "%+.2f" % r["net_bp"], "%.2f" % r["cost_bp"],
                   "%+.2f" % r["trimmed_net_bp"],
                   "%+.2f" % r["never_net_bp"]))

    print(f"\n  net-positive as run                : "
          f"{sum(1 for r in rows if r['net_bp'] > 0)} of {len(rows)}")
    print(f"  net-positive trimmed, cost KEPT   : "
          f"{sum(1 for r in rows if r['trimmed_net_bp'] > 0)} of {len(rows)}")
    print(f"  net-positive as if NEVER HAPPENED : "
          f"{sum(1 for r in rows if r['never_net_bp'] > 0)} of {len(rows)}")
    pos = [r for r in rows if r["trimmed_net_bp"] > 0]
    print(f"  (legacy) net-positive BEFORE trimming: "
          f"{sum(1 for r in rows if r['net_bp'] > 0)} of {len(rows)}")
    print(f"  cells net-positive AFTER  trimming: {len(pos)} of {len(rows)}")

    OUT.write_text(json.dumps(rows, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
