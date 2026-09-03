"""D307 -- risk work on D306's candidate cells. A diagnostic, not a study.

    uv run python scripts/d307_risk_on_candidates.py

Nothing is searched and nothing is promoted. Every construction is already
decided; this measures what D306 reported at cell level but never broke down:
era, name concentration, drawdown behaviour, the lottery check, and the
sensitivity of each cell's net to the one number it rests on.

FOUR CANDIDATES, and why each is here:
  N=2  / target        best NET in the grid (+15.25)
  N=3  / target        best Sharpe among net-positive full-exposure cells
  N=5  / none+overlay  best net among the overlay cells (+4.59)
  N=7  / none+overlay  best SHARPE in the grid (+0.868)

AND THE SENSITIVITY THAT MATTERS MOST. Each cell's net uses the round trip of the
names IT holds. At N=2 the no-exit book measures 86.7 bp and the target book 73.2
-- a 16% gap at the same depth, from the exit rule alone. If that gap is noise
rather than signal, the target's cost advantage evaporates. Section 5 prices it.
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
D, SP, M = W.D, W.SP, W.M
OUT = REPO / "data" / "d307_risk.json"
ANN = 252.0

CANDIDATES = (("N=2/target", 2, True, False),
              ("N=3/target", 3, True, False),
              ("N=5/none+overlay", 5, False, True),
              ("N=7/none+overlay", 7, False, True))


def underwater(eq):
    """Longest run of bars below a prior peak, and the share of bars under."""
    pk = np.maximum.accumulate(eq)
    under = eq < pk - 1e-15
    best = cur = 0
    for u in under:
        cur = cur + 1 if u else 0
        best = max(best, cur)
    return int(best), float(under.mean())


def risk(res, scale, years, half, rt):
    ok = res["mask"]
    b = res["book"][ok] * scale[ok]
    eq = np.cumsum(b)
    pnl = np.array([x[3] for x in res["trades"]])
    byname = {}
    for x in res["trades"]:
        byname[x[0]] = byname.get(x[0], 0.0) + x[3]
    v = np.sort(np.array(list(byname.values())))[::-1]
    tot = float(v.sum())
    yr = years[ok]
    ys = {int(u): float(b[yr == u].mean()) * 1e4 for u in np.unique(yr)}
    ex = np.sort(pnl)[:-max(1, pnl.size // 100)]
    roll = []
    for s in range(0, b.size - 252, 63):
        w = b[s:s + 252]
        if w.std(ddof=1) > 0:
            roll.append(float(w.mean() / w.std(ddof=1) * np.sqrt(ANN)))
    lw, us = underwater(eq)
    return dict(
        bars=int(b.size), gross_bp=float(b.mean()) * 1e4,
        sharpe=float(b.mean() / b.std(ddof=1) * np.sqrt(ANN)),
        maxdd_bp=float(np.max(np.maximum.accumulate(eq) - eq)) * 1e4,
        longest_underwater_bars=lw, share_underwater=us,
        worst_bar_bp=float(b.min()) * 1e4, best_bar_bp=float(b.max()) * 1e4,
        worst5_bp=[float(x) * 1e4 for x in np.sort(b)[:5]],
        skew=float(((b - b.mean()) ** 3).mean() / b.std() ** 3),
        kurt=float(((b - b.mean()) ** 4).mean() / b.std() ** 4),
        trades=int(pnl.size),
        trade_mean_bp=float(pnl.mean()) * 1e4,
        trade_mean_ex_top1_bp=float(ex.mean()) * 1e4,
        top1_share_of_pnl=float(v[0] / tot),
        top5_share_of_pnl=float(v[:5].sum() / tot),
        top10_share_of_pnl=float(v[:10].sum() / tot),
        names=len(byname),
        names_to_half=int(np.searchsorted(np.cumsum(v), 0.5 * tot) + 1),
        years=len(ys), years_profitable=sum(1 for x in ys.values() if x > 0),
        by_year=ys, worst_year_bp=min(ys.values()), best_year_bp=max(ys.values()),
        rolling252_sharpe_min=float(min(roll)) if roll else None,
        rolling252_sharpe_med=float(np.median(roll)) if roll else None,
        rolling252_sharpe_max=float(max(roll)) if roll else None,
        rolling_windows_negative=int(sum(1 for x in roll if x < 0)),
        rolling_windows=len(roll))


def main() -> int:
    t0 = time.time()
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    G = W.build_gate(A, verbose=False)
    T = A["r1T"].shape[0]
    years = np.arange(T) // 252
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    half = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    ones = np.ones(T)
    print(f"D307  risk on D306's candidates  (loaded {time.time() - t0:.0f}s)\n")

    out = {}
    for name, depth, ut, ov in CANDIDATES:
        r = W.simulate(A, G, depth, ut)
        rt = W.held_rt(r, half)
        sc = W.overlay_scale(r["book"]) if ov else ones
        out[name] = risk(r, sc, years, half, rt)
        out[name]["round_trip"] = rt
        out[name]["net_bp"] = W.stats(r, depth, sc, rt, half)["net_bp"]

    print("DRAWDOWN AND PATH")
    h = "%-18s %9s %9s %10s %12s %8s %10s %10s"
    print(h % ("cell", "net", "sharpe", "maxdd", "longest_uw", "%under", "worst_bar",
               "best_bar"))
    print("-" * 92)
    for k, v in out.items():
        print(h % (k, "%+.2f" % v["net_bp"], "%+.3f" % v["sharpe"],
                   "%,.0f".replace(",", "") % v["maxdd_bp"],
                   "%d bars" % v["longest_underwater_bars"],
                   "%.0f%%" % (100 * v["share_underwater"]),
                   "%+.0f" % v["worst_bar_bp"], "%+.0f" % v["best_bar_bp"]))

    print("\nCONCENTRATION -- what the winners depend on")
    h2 = "%-18s %8s %10s %9s %9s %10s %14s"
    print(h2 % ("cell", "names", "to_half", "top1%", "top5%", "top10%",
                "trade_ex_top1"))
    print("-" * 92)
    for k, v in out.items():
        print(h2 % (k, v["names"], v["names_to_half"],
                    "%.1f%%" % (100 * v["top1_share_of_pnl"]),
                    "%.1f%%" % (100 * v["top5_share_of_pnl"]),
                    "%.1f%%" % (100 * v["top10_share_of_pnl"]),
                    "%+.1f bp" % v["trade_mean_ex_top1_bp"]))

    print("\nERA -- mean bp/bar by 252-bar year")
    yrs = sorted({y for v in out.values() for y in v["by_year"]})
    print("%-18s " % "cell" + " ".join("%7d" % y for y in yrs) + "   prof")
    print("-" * (19 + 8 * len(yrs) + 8))
    for k, v in out.items():
        row = " ".join("%+7.1f" % v["by_year"].get(y, float("nan")) for y in yrs)
        print("%-18s %s   %d/%d" % (k, row, v["years_profitable"], v["years"]))

    print("\nROLLING 252-BAR SHARPE (63-bar step)")
    for k, v in out.items():
        print("  %-18s min %+6.2f  median %+6.2f  max %+6.2f   negative in "
              "%d of %d windows" % (k, v["rolling252_sharpe_min"],
                                    v["rolling252_sharpe_med"],
                                    v["rolling252_sharpe_max"],
                                    v["rolling_windows_negative"],
                                    v["rolling_windows"]))

    # 5. THE ROUND-TRIP SENSITIVITY. Each cell's net rests on the spread of the
    #    names it holds, and D306 measured 73.2 for N=2/target against 86.7 for
    #    N=2/none -- a 16% gap at the same depth from the exit rule alone.
    print("\nROUND-TRIP SENSITIVITY -- net if the cell were charged the OTHER "
          "book's round trip")
    r2t = W.simulate(A, G, 2, True)
    r2n = W.simulate(A, G, 2, False)
    rt_t, rt_n = W.held_rt(r2t, half), W.held_rt(r2n, half)
    st = W.stats(r2t, 2, ones, rt_t, half)
    sn = W.stats(r2n, 2, ones, rt_n, half)
    alt = W.stats(r2t, 2, ones, rt_n, half)
    print(f"  N=2/target  own rt {rt_t:.1f} -> net {st['net_bp']:+.2f}")
    print(f"  N=2/none    own rt {rt_n:.1f} -> net {sn['net_bp']:+.2f}")
    print(f"  N=2/target charged the NO-EXIT book's rt {rt_n:.1f} -> net "
          f"{alt['net_bp']:+.2f}")
    print(f"  so the target's advantage over no-exit is "
          f"{st['net_bp'] - sn['net_bp']:+.2f} on own spreads and "
          f"{alt['net_bp'] - sn['net_bp']:+.2f} on a common one")
    out["rt_sensitivity"] = dict(
        rt_target=rt_t, rt_none=rt_n, net_target_own=st["net_bp"],
        net_none_own=sn["net_bp"], net_target_common_rt=alt["net_bp"])

    OUT.write_text(json.dumps(out, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
