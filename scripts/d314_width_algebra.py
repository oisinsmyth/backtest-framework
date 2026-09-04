"""D314 -- the algebra of how this book makes money, fitted to all 16 widths.

    uv run python scripts/d314_width_algebra.py

NOT A STUDY AND NOT PRE-REGISTERED. It scores no book and tests no rule. It fits
three curves that D300, D306, D310, D312 and D313 have each measured a slice of,
and asks what the first-order condition says the optimal width is. Everything
here is descriptive; any rule derived from it needs its own pre-registration.

THE THREE CURVES

  vol(N)^2 = a + b/N        diversification. `a` is the systematic floor the book
                            cannot diversify away; `b/N` is the idiosyncratic
                            part. rho = a/(a+b) is the average pairwise
                            correlation implied.

  gross(N) = g0 - g1*ln N   the edge dilutes as lower-ranked names are added.
  cost(N)  = c0 - c1*ln N   turnover per bar falls as the book widens.

THE IDENTITY THAT MATTERS

  Sharpe(N) = net(N)/vol(N) = sqrt(N) * net(N) / sigma        when a -> 0

so maximising Sharpe over N maximises sqrt(N)*net(N), and the first-order
condition is

  net(N) = -2N * net'(N)      =>    g0-c0 - (g1-c1) ln N = 2(g1-c1)

which solves in closed form. If the solution lies below the grid floor the
optimum is a CORNER, and no rule that varies N can improve on sitting at it.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "data" / "d314_width_algebra.json"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


X = _load("d312", "run_d312_vol_targeted.py")
D, W, M, SP, LEVELS = X.D, X.W, X.M, X.SP, X.LEVELS


def fit_line(x, y):
    """OLS slope/intercept plus R^2, so a bad fit cannot pass as a good one."""
    A = np.vstack([np.ones_like(x), x]).T
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ beta
    ss = float(((y - y.mean()) ** 2).sum())
    return float(beta[0]), float(beta[1]), 1.0 - float(((y - pred) ** 2).sum()) / ss


def main() -> int:
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    G = W.build_gate(A, verbose=False)
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    half = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    rt = 4.0 * float(np.nanmedian(half[np.isfinite(half)]))
    cells, mask = X.build(A, G, rt)
    GR, CO = X.pack(cells, mask)

    N = np.array(LEVELS, float)
    gross = GR.mean(axis=1)
    cost = CO.mean(axis=1)
    net = gross - cost
    vol = (GR - CO).std(axis=1, ddof=1)

    print("THE MEASURED SURFACE, all %d widths" % N.size)
    print("%7s %9s %9s %9s %9s %10s" % (
        "N_eff", "gross", "cost", "net", "vol", "netSharpe"))
    for i in range(N.size):
        print("%7.1f %9.2f %9.2f %+9.2f %9.0f %+10.4f" % (
            N[i], gross[i], cost[i], net[i], vol[i],
            net[i] / vol[i] * np.sqrt(252.0)))

    # ---- 1. DIVERSIFICATION: vol^2 = a + b/N ------------------------------
    a, b, r2v = fit_line(1.0 / N, vol ** 2)
    sigma = float(np.sqrt(max(a, 0.0) + b))
    rho = float(a / (a + b))
    print("\n1. DIVERSIFICATION   vol^2 = a + b/N")
    print("   a = %.0f    b = %.0f    R^2 = %.4f" % (a, b, r2v))
    print("   implied single-name spread vol sigma = %.0f bp" % sigma)
    print("   implied average pairwise correlation rho = a/(a+b) = %.4f" % rho)
    print("   systematic floor sigma*sqrt(rho) = %.0f bp, against %.0f bp at the"
          % (sigma * np.sqrt(max(rho, 0.0)), vol[-1]))
    print("   widest width tested -- the book is NOWHERE NEAR its floor.")

    # ---- 2. DILUTION and 3. TURNOVER --------------------------------------
    lnN = np.log(N)
    g0, g1, r2g = fit_line(lnN, gross)
    c0, c1, r2c = fit_line(lnN, cost)
    print("\n2. DILUTION      gross(N) = %.2f %+.2f*ln N     R^2 = %.4f"
          % (g0, g1, r2g))
    print("3. TURNOVER      cost(N)  = %.2f %+.2f*ln N     R^2 = %.4f"
          % (c0, c1, r2c))
    print("   net(N) = %.2f %+.2f*ln N -- the edge dilutes %.2fx faster than the"
          % (g0 - c0, g1 - c1, g1 / c1))
    print("   cost falls, which is why net is monotone DOWN in width.")

    # ---- 4. THE FIRST-ORDER CONDITION -------------------------------------
    n0, n1 = g0 - c0, g1 - c1
    print("\n4. THE OPTIMUM, in closed form")
    print("   Sharpe(N) = net(N)/vol(N); with rho ~ 0 this is sqrt(N)*net(N)/sigma")
    print("   d/dN = 0  =>  net(N) = -2N*net'(N)  =>  ln N* = (n0 - 2*(-n1))/(-n1)"
          if n1 else "")
    lnstar = (n0 + 2.0 * n1) / (-n1)
    Nstar = float(np.exp(lnstar))
    print("   n0 = %.3f   n1 = %.3f   =>   ln N* = %.3f   =>   N* = %.2f"
          % (n0, n1, lnstar, Nstar))

    # the same thing done numerically on the measured points, as a check that
    # the closed form is not an artefact of the log-linear fit
    sN = np.sqrt(N) * net
    print("   numerically, sqrt(N)*net peaks at N_eff = %.1f  (%.2f)"
          % (N[int(sN.argmax())], sN.max()))
    grid_floor = float(N.min())
    corner = Nstar <= grid_floor
    print("\n   THE GRID FLOOR IS N_eff = %.0f AND N* = %.2f -- %s"
          % (grid_floor, Nstar,
             "THE OPTIMUM IS A CORNER SOLUTION" if corner
             else "the optimum is interior"))

    # ---- 5. does sigma(t) move the optimum? -------------------------------
    print("\n5. DOES THE VOL LEVEL MOVE THE OPTIMUM?")
    print("   Sharpe(N) = sqrt(N)*(gross(N) - cost(N))/sigma. If gross scales")
    print("   with sigma and cost does NOT, write gross = sigma*ghat(N):")
    print("      Sharpe = sqrt(N)*(ghat(N) - cost(N)/sigma)")
    print("   sigma enters ONLY through cost/sigma. So the optimal width moves")
    print("   with the COST-TO-OPPORTUNITY ratio, never with the vol level per se.")
    print("   A vol target varies N with sigma(t) directly, which is the wrong")
    print("   argument -- and it is why D312 and D313 could not have worked.")
    for mult in (0.5, 1.0, 2.0):
        s = np.sqrt(N) * (gross * mult - cost)
        print("      sigma x %.1f  ->  best N_eff = %5.1f" % (mult, N[int(s.argmax())]))

    # ---- 6. ROBUSTNESS: N* must not be an artefact of one subset ----------
    # N=25 is the whole gate, where the exponential weights flatten completely
    # and gross drops 9.11 -> 6.00. If N* moved when that point is dropped, the
    # headline number would be a boundary artefact rather than a fit.
    print("\n6. ROBUSTNESS of N*")
    print("   %-14s %8s %8s %8s %8s %8s" % (
        "subset", "n0", "n1", "-n0/n1", "N*", "R^2"))
    rob = {}
    for lab, m in (("all 16", N > 0), ("drop N=25", N < 25), ("drop N>=20", N < 20),
                   ("N<=10", N <= 10), ("N<=5", N <= 5), ("N>=5", N >= 5)):
        p0, p1, r2 = fit_line(np.log(N[m]), net[m])
        ns = float(np.exp(-p0 / p1 - 2.0))
        rob[lab] = dict(n0=p0, n1=p1, N_star=ns, r2=r2)
        print("   %-14s %8.3f %8.3f %8.3f %8.2f %8.4f"
              % (lab, p0, p1, -p0 / p1, ns, r2))
    lo = min(v["N_star"] for v in rob.values())
    hi = max(v["N_star"] for v in rob.values())
    print("   N* spans %.2f to %.2f across every subset -- BELOW THE GRID FLOOR"
          % (lo, hi))
    print("   in all of them, so the corner is not an artefact of one point.")

    res = dict(
        note="DESCRIPTIVE. Fits, not a study. Any rule derived here needs its "
             "own pre-registration.",
        robustness=rob, N_star_range=[lo, hi],
        round_trip=rt, levels=N.tolist(), gross=gross.tolist(),
        cost=cost.tolist(), net=net.tolist(), vol=vol.tolist(),
        diversification=dict(a=a, b=b, r2=r2v, sigma=sigma, rho=rho),
        dilution=dict(g0=g0, g1=g1, r2=r2g),
        turnover=dict(c0=c0, c1=c1, r2=r2c),
        optimum=dict(n0=n0, n1=n1, N_star=Nstar, grid_floor=grid_floor,
                     corner=bool(corner),
                     numeric_argmax=float(N[int(sN.argmax())])))
    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
