"""D321b -- how many INDEPENDENT tests are in a 19-point threshold sweep?

    uv run python scripts/d321b_effective_tests.py

POST-HOC, prompted by the principal declining to throw dv28 away on a BH bar
computed over nineteen nominal tests.

D321 applied BH-FDR at q = 0.10 over all nineteen thresholds, so the smallest p
had to clear 0.10/19 = 0.00526, and dv28's 0.0100 missed. That correction assumes
nineteen tests that are at least independent-ish. ADJACENT THRESHOLDS SHARE NEARLY
ALL THEIR NAMES, so they are not.

This measures the effective number of independent tests from the correlation
matrix of the nineteen books' own per-bar returns, by both standard estimators:

  Cheverud-Nyholt   M_eff = 1 + (M-1)(1 - Var(lambda)/M)
  Li-Ji             M_eff = sum over eigenvalues of  I(l>=1) + (l - floor(l))

AND THE PRECEDENT IS THE PROGRAMME'S OWN. D297 applied BH to its EIGHT
pre-registered cells and reported its 25-point fine sweep separately as a COUNT
against chance -- "4 of 25 clear p < 0.05 against 1.25 expected" -- rather than as
25 hypothesis tests. A sweep is one hypothesis measured at many correlated points.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "data" / "d321b_effective_tests.json"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


Y = _load("d321", "run_d321_dv_sweep.py")
X, W, D, M, SP = Y.X, Y.X.W, Y.X.D, Y.X.M, Y.X.SP


def main() -> int:
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
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
    DV = X.roll_mean_T(CLOSE * VOL)

    books, masks = [], []
    for p in Y.PCTS:
        r = W.simulate(A, X.gate_with(A, X.keep_mask(DV, finT, p, True)), 2, True)
        books.append(np.nan_to_num(r["book"], nan=0.0))
        masks.append(r["mask"])
    m = np.logical_and.reduce(masks)
    Z = np.array([b[m] for b in books])
    n = len(Y.PCTS)

    C = np.corrcoef(Z)
    iu = np.triu_indices(n, 1)
    ev = np.linalg.eigvalsh(C)[::-1]
    liji = float(sum((1.0 if e >= 1 else 0.0) + min(1.0, max(0.0, e - np.floor(e)))
                     for e in ev))
    nyh = float(1 + (n - 1) * (1 - np.var(ev, ddof=1) / n))

    print("D321b  how many independent tests are in the sweep?")
    print(f"  {n} thresholds over {int(m.sum()):,} common bars")
    print(f"  pairwise correlation of the threshold books: min {C[iu].min():.3f}  "
          f"median {np.median(C[iu]):.3f}  max {C[iu].max():.3f}")
    print(f"  first three eigenvalues: {ev[0]:.2f}, {ev[1]:.2f}, {ev[2]:.2f} "
          f"-- the first explains {100 * ev[0] / n:.0f}% of the variance")
    print(f"\n  EFFECTIVE INDEPENDENT TESTS   Li-Ji {liji:.1f}   "
          f"Cheverud-Nyholt {nyh:.1f}   (nominal {n})")
    print("\n  BH q=0.10 bar for the SMALLEST p, by assumed test count:")
    rows = {}
    for mm in (n, 8, int(round(nyh)), int(round(liji))):
        bar = 0.10 / mm
        rows[str(mm)] = bar
        print("    m=%2d  bar %.5f   dv28 p=0.0100 -> %s"
              % (mm, bar, "CLEARS" if 0.0100 <= bar else "misses"))

    print("\n  D297's PRECEDENT: BH over its EIGHT pre-registered cells, and its")
    print("  25-point fine sweep reported as a COUNT against chance instead --")
    print("  '4 of 25 clear p<0.05 against 1.25 expected'. D321's count is 3 of")
    print("  19 against 0.95. A sweep is ONE hypothesis at many correlated points.")

    OUT.write_text(json.dumps(dict(
        note="POST-HOC. Effective number of independent tests in D321's 19-point "
             "sweep, from the correlation of the threshold books' own returns.",
        thresholds=list(Y.PCTS), common_bars=int(m.sum()),
        corr_min=float(C[iu].min()), corr_median=float(np.median(C[iu])),
        corr_max=float(C[iu].max()), eigenvalues=[float(e) for e in ev],
        m_eff_li_ji=liji, m_eff_cheverud_nyholt=nyh,
        bh_bar_by_m=rows, dv28_p=0.0100), indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
