"""D315a post-hoc -- is the net peak at N_eff = 1.45 real, or is it noise?

    uv run python scripts/d315a_paired_net.py

POST-HOC. The pre-registration scored each width against the rank-rotation null
and against nothing else, so it can say every cell beats a scrambled ranking and
CANNOT say whether 1.45's +4.73 differs from 2.00's +4.37. Those two books share
all 3,187 bars and hold overlapping names, so their difference is far better
measured pairwise than by comparing two standalone means -- exactly D303's
paired-t argument.

TWO THINGS THIS IS NOT. It is not a null: a paired t says the two books differ,
not that either beats a control. And it is not pre-registered, so a width chosen
on it has been selected on the same data that scored it.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "data" / "d315a_paired_net.json"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


S = _load("d315a", "run_d315a_below_corner.py")
R, W, D, SP, M = S.R, S.W, S.D, S.SP, S.M


def main() -> int:
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    G = W.build_gate(A, verbose=False)
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    half = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    rt = 4.0 * float(np.nanmedian(half[np.isfinite(half)]))
    cells = {lv: S.sim(A, G, lv, rt) for lv in S.LEVELS}
    base = cells[2.0]["net"]

    print("PAIRED DIFFERENCE IN NET AGAINST N_eff = 2, per bar, %d bars"
          % base.size)
    print("%7s %9s %10s %9s %9s %8s %9s" % (
        "N_eff", "net", "diff", "sd(diff)", "t", "corr", "win rate"))
    print("-" * 70)
    out = {}
    for lv in S.LEVELS:
        if lv == 2.0:
            continue
        d = cells[lv]["net"] - base
        t = float(d.mean() / (d.std(ddof=1) / np.sqrt(d.size)))
        out[str(lv)] = dict(net=float(cells[lv]["net"].mean()),
                            diff=float(d.mean()), sd=float(d.std(ddof=1)), t=t,
                            corr=float(np.corrcoef(cells[lv]["net"], base)[0, 1]),
                            win=float((d > 0).mean()))
        r = out[str(lv)]
        print("%7.2f %+9.2f %+10.3f %9.2f %+9.2f %8.4f %8.1f%%" % (
            lv, r["net"], r["diff"], r["sd"], t, r["corr"], 100 * r["win"]))

    best = max(out, key=lambda k: out[k]["diff"])
    r = out[best]
    print("\n  the largest gain over N=2 is N_eff = %s at %+.3f bp/bar, t = %+.2f"
          % (best, r["diff"], r["t"]))
    print("  the two books correlate at %.4f, so the paired test is the right"
          % r["corr"])
    print("  one -- comparing standalone means would throw that away.")
    if abs(r["t"]) < 2.0:
        print("\n  |t| < 2: THE NET PEAK BELOW 2 IS NOT DISTINGUISHABLE FROM N=2.")
    else:
        print("\n  |t| >= 2: the difference is measurable. It is still post-hoc,")
        print("  on mined data, and selected from 7 widths -- not a result.")

    OUT.write_text(json.dumps(dict(
        note="POST-HOC, not pre-registered, not a null. Paired t of each width's "
             "per-bar net against N_eff=2.",
        round_trip=rt, bars=int(base.size), pairs=out, best=best), indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
