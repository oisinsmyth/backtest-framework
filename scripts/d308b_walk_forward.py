"""D308b -- the shuffle null on persistence, and the walk-forward rule.

    uv run python scripts/d308b_walk_forward.py

TWO THINGS. The first is pre-registered in D308's Stage 2: the run length of the
oracle's width path is compared against that path SHUFFLED, which preserves its
level distribution and destroys only its ordering.

The second is a POST-HOC DIAGNOSTIC and is labelled as one. Stage 1 returned a
large ceiling and Stage 2 returned mean run lengths of 1.24 to 1.98 blocks, so
the pre-registered stop condition fires. But "no persistence" and "unusable" are
not the same claim, and the record should not rest on an inference where a
measurement is available:

    THE WALK-FORWARD RULE -- at each block, hold the width that was best in the
    PREVIOUS block. The simplest investable use of persistence there is, and the
    direct test of whether any exists to use.

If the width path is anti-persistent, this rule loses to the best static N, and
the ceiling above is the value of knowing 63 bars of noise in advance rather
than an opportunity.
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


T8 = _load("d308", "run_d308_width_in_time.py")
W, D, SP, M = T8.W, T8.D, T8.SP, T8.M
DEPTHS, FAMILIES, FREQS = T8.DEPTHS, T8.FAMILIES, T8.FREQS
OUT = REPO / "data" / "d308b_walk_forward.json"
SEED = 20260903


def main() -> int:
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    G = W.build_gate(A, verbose=False)
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    half = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    cells, rts, mask = T8.build(A, G, half)
    nb = int(mask.sum())
    prior = json.loads((REPO / "data" / "d308_width_in_time.json").read_text())
    rng = np.random.default_rng(SEED)
    res = {}

    print("PERSISTENCE AGAINST ITS OWN SHUFFLE  (run length in blocks)")
    print("%-16s %5s %11s %13s %10s %s" % (
        "family", "f", "observed", "shuffled p50", "ratio", "verdict"))
    print("-" * 82)
    for fam in FAMILIES:
        for f in FREQS:
            picks = prior["oracle"][fam][str(f)]["picks"]
            picks = [int(x) for x in picks]
            obs = float(T8.runs(picks).mean())
            sh = []
            for _ in range(500):
                p = list(rng.permutation(picks))
                sh.append(float(T8.runs(p).mean()))
            med = float(np.median(sh))
            ratio = obs / med
            verdict = ("ANTI-persistent" if ratio < 0.97 else
                       "persistent" if ratio > 1.03 else "indistinguishable")
            res.setdefault(fam, {}).setdefault(str(f), {})["run_obs"] = obs
            res[fam][str(f)]["run_shuffled_p50"] = med
            res[fam][str(f)]["run_ratio"] = ratio
            print("%-16s %5d %11.2f %13.2f %10.3f  %s" % (
                fam, f, obs, med, ratio, verdict))
        print()

    print("WALK-FORWARD -- hold the width that was best LAST block "
          "(post-hoc diagnostic)")
    print("%-16s %5s %11s %13s %12s %11s" % (
        "family", "f", "best static", "walk-forward", "vs static", "oracle"))
    print("-" * 82)
    for fam in FAMILIES:
        stat = {d: float(cells[(fam, d)]["net"][mask].mean()) for d in DEPTHS}
        bestN = max(stat, key=stat.get)
        for f in FREQS:
            bl = T8.blocks(mask, f)
            bn = np.array([[cells[(fam, d)]["net"][ix].sum() for d in DEPTHS]
                           for ix in bl])
            # block 0 has no predecessor: hold the best static N
            path = [bestN]
            for b in range(1, len(bl)):
                path.append(DEPTHS[int(bn[b - 1].argmax())])
            tot = sum(bn[b, DEPTHS.index(path[b])] for b in range(len(bl)))
            tc = sum(T8.transition(path[b - 1], path[b], rts[(fam, path[b])])
                     for b in range(1, len(bl)))
            wf = (tot - tc) / nb
            orc = prior["oracle"][fam][str(f)]["charged_bp"]
            res[fam][str(f)]["walk_forward_bp"] = wf
            res[fam][str(f)]["best_static_bp"] = stat[bestN]
            res[fam][str(f)]["oracle_charged_bp"] = orc
            print("%-16s %5d %11.2f %13.2f %+12.2f %11.2f" % (
                fam, f, stat[bestN], wf, wf - stat[bestN], orc))
        print()

    OUT.write_text(json.dumps(res, indent=1))
    print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
