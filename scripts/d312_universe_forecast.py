"""D312 §0 -- is the book's vol unforecastable, or was the ESTIMATOR starved?

    uv run python scripts/d312_universe_forecast.py

POST-HOC AND PROMPTED. This was run AFTER D312's result was known, at the
principal's question: why compute the risk estimate from the held book when the
whole market is available, and names outside the top 19 are just as informative?
Nothing here is pre-registered and nothing here scores a book -- it measures the
FORECASTABILITY of a quantity, which no cell in D312 was scored on.

D312 forecast the book's vol from THE BOOK'S OWN 63-bar realised series: one
series, 63 numbers, off a two-name spread. The live universe carries ~1,019 names
a bar. Cross-sectional dispersion over all of them is three orders of magnitude
more observations of the same regime, and it costs nothing to compute.

Predictors, all causal (through t-1), against the SAME forward-63 realised book
vol D312's Q1 was scored against:

  own       the book's own trailing sd            -- D312's, the baseline
  xs_all    trailing mean of daily cross-sectional sd over ALL finite names
  xs_gate   ... restricted to the 25-per-side gate
  xs_out    ... restricted to names OUTSIDE the gate -- the principal's point
  absr_all  trailing mean of cross-sectional mean |r| -- a robust vol proxy
  mktvol    trailing sd of the market reference series

SIX PREDICTORS ARE COMPARED HERE, so a successor that adopts the best of them has
SEARCHED and must say so. The record's §9 states what a successor must carry.
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
OUT = REPO / "data" / "d312_universe_forecast.json"
WIN = 63


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


X = _load("d312", "run_d312_vol_targeted.py")
D, W, M, SP = X.D, X.W, X.M, X.SP


def dispersion(A, G, Tn):
    """Daily cross-sectional dispersion over three name sets, in bp.

    The gate is the union of both sides' rows at bar t. `outside` is every other
    finite name -- names the book never holds, and therefore a read on the regime
    that CANNOT be contaminated by the selection.
    """
    r1T, finT = A["r1T"], A["finT"]
    gF, gO = G["gateF"], G["gateO"]
    out = {k: np.full(Tn, np.nan) for k in ("all", "gate", "out", "absr")}
    n = {k: np.zeros(Tn) for k in ("all", "gate", "out")}
    for t in range(Tn):
        fin = finT[t]
        gate = np.zeros(fin.size, bool)
        for side in (0, 1):
            gate[gF[gO[side, t]:gO[side, t + 1]]] = True
        v = r1T[t]
        a = v[fin]
        if a.size > 2:
            out["all"][t] = a.std(ddof=1) * 1e4
            out["absr"][t] = np.abs(a).mean() * 1e4
        gm, om = fin & gate, fin & ~gate
        if gm.sum() > 2:
            out["gate"][t] = v[gm].std(ddof=1) * 1e4
        if om.sum() > 2:
            out["out"][t] = v[om].std(ddof=1) * 1e4
        n["all"][t], n["gate"][t], n["out"][t] = fin.sum(), gm.sum(), om.sum()
    return out, n


def trail_mean(v, idx, w=WIN):
    """Trailing mean over the scored bars, LAGGED one bar, NaN-tolerant.

    The lag is the same one D312's rule uses. A window with fewer than 30 finite
    bars returns NaN rather than a mean of whatever survived.
    """
    x = v[idx].astype(float)
    ok = np.isfinite(x).astype(float)
    xf = np.where(np.isfinite(x), x, 0.0)
    cs = np.concatenate([[0.0], np.cumsum(xf)])
    cn = np.concatenate([[0.0], np.cumsum(ok)])
    out = np.full(x.size, np.nan)
    j = np.arange(w, x.size + 1)
    cnt = cn[j] - cn[j - w]
    out[j - 1] = np.where(cnt > 30, (cs[j] - cs[j - w]) / np.maximum(cnt, 1), np.nan)
    return np.concatenate([[np.nan], out[:-1]])


def main() -> int:
    t0 = time.time()
    print("D312 stage 0  forecastability -- the book's own history vs the universe")
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
    NET = GR - CO
    idx = np.flatnonzero(mask)
    Tn = A["r1T"].shape[0]

    disp, n = dispersion(A, G, Tn)
    counts = {k: float(v[idx].mean()) for k, v in n.items()}
    print("  names per bar on the scored mask: universe %.0f, gate %.0f, "
          "outside %.0f" % (counts["all"], counts["gate"], counts["out"]))

    P = {"xs_all": trail_mean(disp["all"], idx),
         "xs_gate": trail_mean(disp["gate"], idx),
         "xs_out": trail_mean(disp["out"], idx),
         "absr_all": trail_mean(disp["absr"], idx),
         "mktvol": X.roll_sd(A["mkt"][idx] * 1e4, lag=True)}

    # THE ONE LINE THAT WOULD HAVE CAUGHT D312 BEFORE IT WAS DESIGNED: does the
    # conditioner's own level persist at the horizon it is meant to forecast?
    print("\nSTAGE 0 -- does the predictor's own level persist at 63 bars?")
    persist = {}
    for name in list(P) + ["own"]:
        p = P[name] if name != "own" else X.roll_sd(NET[X.LEVELS.index(2.0)], lag=True)
        q = p[np.isfinite(p)]
        persist[name] = float(np.corrcoef(q[:-WIN], q[WIN:])[0, 1])
        print("    %-10s lag-63 rho %+0.3f   n=%d" % (name, persist[name], q.size))

    print("\nCORRELATION with the NEXT 63 bars' realised book vol")
    print("%-10s" % "predictor" + "".join("%12s" % f"N_eff={b:g}" for b in X.BASES))
    print("-" * 58)
    fwd = {}
    for name in ["own"] + list(P):
        line, row = "%-10s" % name, {}
        for base in X.BASES:
            v = NET[X.LEVELS.index(base)]
            f = np.concatenate([X.roll_sd(v, lag=False)[WIN - 1:],
                                np.full(WIN - 1, np.nan)])
            p = X.roll_sd(v, lag=True) if name == "own" else P[name]
            m = np.isfinite(p) & np.isfinite(f)
            row[str(base)] = float(np.corrcoef(p[m], f[m])[0, 1])
            line += "%12.3f" % row[str(base)]
        fwd[name] = row
        print(line)

    print("\n  at N_eff=2 -- the width that earns -- the forecast goes from "
          "%+.3f to %+.3f" % (fwd["own"]["2.0"], fwd["xs_all"]["2.0"]))
    print("  and the ~%.0f names the book NEVER HOLDS carry it at %+.3f, "
          "better than\n  the %.0f gate names at %+.3f -- the gate is chosen on "
          "the signal, so its\n  dispersion is contaminated by the selection."
          % (counts["out"], fwd["xs_out"]["2.0"], counts["gate"],
             fwd["xs_gate"]["2.0"]))

    OUT.write_text(json.dumps(
        dict(note="POST-HOC, PROMPTED, six predictors compared -- see "
                  "D312-RESULT §0 and §9",
             window=WIN, round_trip=rt, bars=int(mask.sum()),
             names_per_bar=counts, forward_corr=fwd, persistence=persist),
        indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
