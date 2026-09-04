"""D316 -- is the weight SHAPE worth anything at fixed N_eff? Paired, not ranked.

    uv run python scripts/d316_weight_shape_paired.py

POST-HOC AND DIAGNOSTIC. Scores no new construction and closes nothing.

D310 published both weight schemes and every width study since -- D311, D312,
D313, D314, D315 -- ran on `exp` alone. Read off the published table, `none/hard2`
posts +8.21 bp/bar net against `none/exp2`'s +4.37 at the SAME N_eff of 2, which
would make the entire width chain a study of the weaker shape.

BUT THE `hard` FAMILY IS ERRATIC WHERE `exp` IS SMOOTH. Gross by width:

    exp   24.12  22.08  19.23  17.27  15.12  12.95  10.61      monotone
    hard  27.64  18.92  18.47  17.34  12.74  10.37  11.27      not monotone

A non-monotone surface on a monotone axis is the signature of noise, so ranking
two cells off that table is exactly the mistake D315a's paired test caught: there,
a width that LOOKED 8% better on net was +0.361 bp at t = +0.12.

So the comparison is made pairwise. These books share every bar and hold
overlapping names; the difference is far better measured on the per-bar
difference than by subtracting two standalone means (D303's argument).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "data" / "d316_weight_shape_paired.json"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


X = _load("d312", "run_d312_vol_targeted.py")
R, W, D, SP, M = X.R, X.W, X.D, X.SP, X.M
WIDTHS = (2, 3, 5, 7, 10, 14, 19)
ANN = 252.0


def series(A, G, scheme, level, rt, use_target):
    r = R.simulate(A, G, scheme, level, 0.0, use_target)
    ok = r["mask"]
    gross = np.where(ok, r["book"] * 1e4, 0.0)[ok]
    return gross - np.where(ok, rt * r["turn"], 0.0)[ok]


def paired(a, b, label):
    """Paired difference AND what the test could have detected.

    A |t| under 2 is NOT evidence of no effect. `se` fixes the resolution, and
    `mde` -- the smallest true difference this test would call significant -- is
    the number that says whether a non-result means anything. Reporting t alone
    is how absence of evidence gets read as evidence of absence.
    """
    d = a - b
    se = float(d.std(ddof=1) / np.sqrt(d.size))
    m = float(d.mean())
    return dict(label=label, diff=m, se=se, t=m / se, mde=2.0 * se,
                ci_lo=m - 1.96 * se, ci_hi=m + 1.96 * se,
                corr=float(np.corrcoef(a, b)[0, 1]), win=float((d > 0).mean()))


def main() -> int:
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    G = W.build_gate(A, verbose=False)
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    half = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    rt = 4.0 * float(np.nanmedian(half[np.isfinite(half)]))

    S = {}
    for fam, ut in (("none", False), ("target", True)):
        for sch in ("hard", "exp"):
            for n in WIDTHS:
                S[(fam, sch, n)] = series(A, G, sch, n, rt, ut)
    nb = S[("none", "exp", 2)].size
    print(f"paired over {nb:,} bars, rt {rt:.1f} bp\n")

    rows = []
    print("1. HARD minus EXP at the same N_eff, `none` family")
    print("%6s %10s %10s %10s %7s %7s %19s" % (
        "N_eff", "hard net", "exp net", "diff", "t", "MDE", "95% CI"))
    print("-" * 74)
    for n in WIDTHS:
        a, b = S[("none", "hard", n)], S[("none", "exp", n)]
        r = paired(a, b, f"hard{n}-exp{n}")
        rows.append(r)
        print("%6d %+10.2f %+10.2f %+10.3f %+7.2f %7.1f  [%+7.1f, %+7.1f]" % (
            n, a.mean(), b.mean(), r["diff"], r["t"], r["mde"],
            r["ci_lo"], r["ci_hi"]))

    print("\n2. THE TARGET's contribution, paired, at each width and shape")
    print("%6s %8s %10s %7s %7s %19s" % (
        "N_eff", "scheme", "diff", "t", "MDE", "95% CI"))
    print("-" * 62)
    tg = []
    for sch in ("hard", "exp"):
        for n in WIDTHS:
            r = paired(S[("target", sch, n)], S[("none", sch, n)],
                       f"target-none/{sch}{n}")
            tg.append(r)
            print("%6d %8s %+10.3f %+7.2f %7.1f  [%+7.1f, %+7.1f]" % (
                n, sch, r["diff"], r["t"], r["mde"], r["ci_lo"], r["ci_hi"]))

    # THE POWER QUESTION, and it is the one that decides how to read section 2.
    base = S[("none", "exp", 2)].mean()
    print("\n3. WHAT COULD THIS TEST HAVE DETECTED? The book's own net is "
          "%+.2f bp/bar." % base)
    print("   %-22s %9s %9s %11s" % (
        "comparison", "MDE", "vs book", "verdict"))
    print("   " + "-" * 56)
    for r in [x for x in rows if x["label"] == "hard2-exp2"] + \
             [x for x in tg if x["label"] == "target-none/exp2"]:
        ratio = r["mde"] / abs(base)
        print("   %-22s %9.1f %8.1fx %11s" % (
            r["label"], r["mde"], ratio,
            "BLIND" if ratio > 1.0 else "usable"))
    print("\n   An MDE larger than the entire book's net means NO component that")
    print("   could exist would register. A |t| under 2 here is a statement")
    print("   about this test's resolution, NOT about the component.")

    best = max(rows, key=lambda r: r["diff"])
    print("\n  largest shape gain: %s at %+.3f bp/bar, t = %+.2f"
          % (best["label"], best["diff"], best["t"]))
    if abs(best["t"]) < 2.0:
        print("  |t| < 2 -- THE SHAPE DIFFERENCE IS NOT MEASURABLE. The width")
        print("  chain running on `exp` alone cost nothing, and the +8.21 vs")
        print("  +4.37 read off the published table is the erratic `hard`")
        print("  surface, not a better book.")
    else:
        print("  |t| >= 2 -- the shape difference IS measurable, and every width")
        print("  study since D310 ran on the weaker shape. That needs its own")
        print("  pre-registration before any of it is re-read.")

    OUT.write_text(json.dumps(dict(
        note="POST-HOC diagnostic. Paired per-bar differences; not a null and "
             "not pre-registered.",
        round_trip=rt, bars=int(nb), shape=rows, target=tg,
        best_shape=best), indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
