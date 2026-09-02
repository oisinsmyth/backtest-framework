"""D288 gate B -- the re-derivation, against shapes declared before any run.

    uv run python scripts/d288_gateB.py

READS `data/d288_mine.json` AND `data/d288_gateA_floor.json`. Produces no new
screen number; it decides whether the numbers that cleared the floor arrived in
the shape their own mechanism requires.

WHY THIS GATE EXISTS AND WHY IT HAD TO BE WRITTEN IN ADVANCE. Filtering on
mechanism AFTER seeing results is post-hoc rationalisation and is WORSE than
mechanical selection, because no floor can price it -- you can always find a
story for the cell that won. The shapes below are copied from the D288
pre-registration at `fa098a2`, which was committed before the screen existed.
This file adds nothing to them and may not.

A candidate is promotable only if it CLEARS THE FLOOR **and** FAILS IN NONE OF
THE WAYS ITS OWN MECHANISM FORBIDS.

EVERY MISMATCH IS REPORTED, INCLUDING FOR CANDIDATES THAT PASS. A gate that only
speaks when it fires tells you nothing about the ones it waved through.

PROMOTION, also pre-registered, also not decided here on the day:
  several clear both  -> the one whose shape was PRE-RANKED MOST SPECIFIC,
                         E > F > B > D > C > A
  none clears B, some clear A
                      -> the best on A goes forward AND THE RECORD STATES IT WENT
                         WITHOUT MECHANISM SUPPORT, which weakens whatever the
                         holdout then says
  none clears A       -> closed, and D288's stop condition applies

A1-A5 ARE NOT PROMOTABLE AT ALL. They exist to validate the screen. They are
counted in the ledger and in the floor -- D228 does not care what a cell was
built to prove -- but a calibration score winning its own calibration is not a
discovery.
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


M = _load("run_mine_neutral", "run_mine_neutral.py")

MINE = REPO / "data" / "d288_mine.json"
FLOOR = REPO / "data" / "d288_gateA_floor.json"
OUT = REPO / "data" / "d288_gateB.json"

# D286's measured band, the quantity A1 must reproduce for the screen to mean
# anything at all.
D286_N25_SPREAD_BP = 56.3
CALIBRATION_TOL_BP = 15.0
SPECIFICITY = ("E", "F", "B", "D", "C", "A")     # most specific first
QUINTILES = 5


def _peak(rec):
    """The (N, k) cell the candidate's headline is read off."""
    best = None
    for N, r in rec.items():
        k = r.get("peak_horizon")
        if k is None:
            continue
        h = r["horizons"][str(k)] if str(k) in r["horizons"] else r["horizons"][k]
        if best is None or h["spread_bp"] > best[2]["spread_bp"]:
            best = (int(N), int(k), h)
    return best


def check_A(name, rec):
    """A1 must land in D286's band. This is a check on the SCREEN, not on A1."""
    if name != "hist_L":
        return None, "not promotable (calibration)"
    r = rec.get("25") or rec.get(25)
    k = r.get("peak_horizon")
    if k is None:
        return False, "hist_L produced no reportable horizon at N=25 -- THE RUN IS VOID"
    v = (r["horizons"][str(k)] if str(k) in r["horizons"] else r["horizons"][k])
    d = abs(v["spread_bp"] - D286_N25_SPREAD_BP)
    ok = d <= CALIBRATION_TOL_BP
    return ok, (f"hist_L N=25 peak {v['spread_bp']:+.1f} bp against D286's "
                f"{D286_N25_SPREAD_BP:+.1f} (delta {d:.1f}, tol {CALIBRATION_TOL_BP:.0f})"
                + ("" if ok else " -- THE RUN IS VOID, NOT NEGATIVE"))


def check_B(name, rec):
    """An intrabar SHAPE is a one-session statement, so the effect belongs at
    short horizons. Peak at k >= 20 is a slow factor wearing a shape's name."""
    p = _peak(rec)
    if p is None:
        return False, "no reportable horizon"
    N, k, h = p
    ok = k <= 5
    return ok, (f"peak at k={k} (N={N}), {h['spread_bp']:+.1f} bp"
                + ("" if ok else "  -- predicted k<=5; k>=20 falsifies the mechanism"
                   if k >= 20 else "  -- predicted k<=5, landed in between"))


def check_C(name, rec):
    """Participation is a crowd measure: it needs breadth, so the effect should
    STRENGTHEN with N. Spread at N=10 exceeding N=50 falsifies that."""
    def sp(N):
        r = rec.get(str(N)) or rec.get(N)
        k = r.get("peak_horizon")
        if k is None:
            return None
        return (r["horizons"][str(k)] if str(k) in r["horizons"]
                else r["horizons"][k])["spread_bp"]
    a, b = sp(10), sp(50)
    if a is None or b is None:
        return False, "N=10 or N=50 produced no reportable horizon"
    ok = b >= a
    return ok, (f"N=10 {a:+.1f} bp vs N=50 {b:+.1f} bp"
                + ("" if ok else "  -- predicted to strengthen with N; it weakens"))


def check_E(name, rec):
    """These select RISK, not direction, so the SHORT leg should be negative.
    Both legs positive at every horizon is the D286 signature -- the score sorts
    'rises less' from 'rises more', which is not a short."""
    neg = []
    for N, r in rec.items():
        for k, h in r["horizons"].items():
            if h["short_bp"] < 0:
                neg.append((int(N), int(k), h["short_bp"]))
    ok = bool(neg)
    if ok:
        best = min(neg, key=lambda x: x[2])
        return True, (f"short leg negative in {len(neg)} cells, most negative "
                      f"{best[2]:+.1f} bp at N={best[0]} k={best[1]}")
    return False, ("both legs positive at EVERY horizon and every N -- the D286 "
                   "signature, i.e. nothing new")


def check_F(name, rec, all_res):
    """D280 part 4 and D286 measured the two sessions OPPOSING. If the split
    carries information, `on_mean` and `id_mean` must rank with opposite sign."""
    def sp(c):
        p = _peak(all_res.get(c, {}))
        return None if p is None else p[2]["spread_bp"]
    a, b = sp("on_mean"), sp("id_mean")
    if a is None or b is None:
        return False, "on_mean or id_mean produced no reportable horizon"
    ok = (a > 0) != (b > 0)
    return ok, (f"on_mean {a:+.1f} bp, id_mean {b:+.1f} bp -- "
                + ("opposite signs, as predicted" if ok else
                   "SAME SIGN: the split carries nothing the total does not"))


def check_D(name, rec, scores, base, fwd, T):
    """The mechanism is DISTANCE, so the response should be monotone across the
    cross-section rather than living only in the two extreme buckets. Measured
    by quintile, which the screen does not produce because the screen only ever
    looks at the tails."""
    order, cnt = M.rank_columns(scores[name], base)
    p = _peak(rec)
    if p is None:
        return False, "no reportable horizon"
    _, k, _ = p
    f = fwd[k]

    means = []
    for q in range(QUINTILES):
        lo = (cnt * q) // QUINTILES
        hi = (cnt * (q + 1)) // QUINTILES
        rows, cols = [], []
        for t in np.flatnonzero(cnt >= QUINTILES * 2):
            sel = order[lo[t]:hi[t], t]
            rows.append(sel)
            cols.append(np.full(sel.size, t))
        if not rows:
            return False, "no bar carried five populated quintiles"
        s, c = M.bar_sums(f, np.concatenate(rows), np.concatenate(cols), T)
        m = c > 0
        means.append(float((s[m] / c[m]).mean() * 1e4))

    spread = means[0] - means[-1]
    if spread == 0:
        return False, "quintile 1 and quintile 5 are identical"
    middle = (means[1] - means[3]) / spread
    ok = abs(middle) < 0.60
    body = "  ".join(f"q{i+1} {v:+.1f}" for i, v in enumerate(means))
    return ok, (f"k={k}  {body}   q1-q5 {spread:+.1f} bp; middle three carry "
                f"{middle:.0%}" + ("" if ok else " -- predicted monotone across "
                                   "the cross-section, but the effect is confined "
                                   "to the extremes"))


def main() -> int:
    if not MINE.exists() or not FLOOR.exists():
        print(f"gate B needs {MINE.name} and {FLOOR.name}; run the screen and "
              f"gate A first.")
        return 1
    mine = json.loads(MINE.read_text())
    floor = json.loads(FLOOR.read_text())
    res = mine["results"]
    survivors = floor["survivors"]

    print(f"D288 GATE B -- the re-derivation")
    print(f"  gate A floor {floor['floor_p95']:+.1f} bp over {floor['sims']} draws; "
          f"{len(survivors)} survivor(s)")

    # A1 IS CHECKED WHETHER OR NOT IT SURVIVED. If the screen cannot reproduce a
    # known quantity, no other result from it means anything -- so this runs
    # first and can void the study on its own.
    okA, whyA = check_A("hist_L", res["hist_L"])
    print(f"\n  CALIBRATION  hist_L: {'PASS' if okA else 'FAIL'} -- {whyA}")
    if not okA:
        print(f"\n  THE SCREEN DID NOT REPRODUCE D286. The run is VOID; no gate-B "
              f"verdict below\n  is readable, and the correct next step is to find "
              f"the discrepancy, not to\n  report a mine.")

    if not survivors:
        print(f"\n  NO CANDIDATE CLEARED GATE A. D288's stop condition applies: the "
              f"mine is\n  closed -- no thirty-second candidate, no second cut of "
              f"the axes, no re-run at\n  a different N. Gate B has nothing to "
              f"re-derive.")
        OUT.write_text(json.dumps({"calibration_ok": bool(okA),
                                   "calibration": whyA, "survivors": [],
                                   "verdicts": {}, "promoted": None}, indent=1))
        return 0

    need_quintiles = [c for c in survivors if M.AXIS_OF[c] == "D"]
    scores = base = fwd = T = None
    if need_quintiles:
        panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
        live = panel.live
        g = M.P1.build_grids(panel, cleaned)
        scores, warm, _ = M.build_scores(panel, cleaned, g, live)
        base, T = warm & live, live.shape[1]
        fwd = M.forward_returns(panel, live)

    verdicts = {}
    print(f"\n  {'axis':>4s} {'candidate':16s} {'gate B':>7s}   reading")
    for c in survivors:
        ax = M.AXIS_OF[c]
        if ax == "A":
            ok, why = None, "not promotable (calibration)"
        elif ax == "B":
            ok, why = check_B(c, res[c])
        elif ax == "C":
            ok, why = check_C(c, res[c])
        elif ax == "D":
            ok, why = check_D(c, res[c], scores, base, fwd, T)
        elif ax == "E":
            ok, why = check_E(c, res[c])
        else:
            ok, why = check_F(c, res[c], res)
        verdicts[c] = {"axis": ax, "pass": ok, "reading": why}
        tag = "n/a" if ok is None else ("PASS" if ok else "FAIL")
        print(f"  {ax:>4s} {c:16s} {tag:>7s}   {why}")

    passed = [c for c in survivors if verdicts[c]["pass"] is True]
    promoted, note = None, ""
    if passed:
        promoted = min(passed, key=lambda c: SPECIFICITY.index(M.AXIS_OF[c]))
        note = (f"cleared both gates; axis {M.AXIS_OF[promoted]} carried the most "
                f"specific pre-declared shape")
    else:
        eligible = [c for c in survivors if M.AXIS_OF[c] != "A"]
        if eligible:
            promoted = max(eligible, key=lambda c: floor["observed"][c])
            note = ("NO MECHANISM SUPPORT. It cleared the floor and failed its own "
                    "pre-declared shape. Pre-registered as promotable anyway, and "
                    "the record must say so -- this materially weakens whatever "
                    "the holdout then reports.")
        else:
            note = ("the only gate-A survivors are calibration scores, which are "
                    "not promotable")

    print(f"\n{'=' * 78}")
    print(f"  PROMOTED: {promoted or 'none'}")
    if note:
        print(f"  {note}")
    print(f"\n  Under R8 a pass on the holdout is still NOT a book entry. It is one "
          f"pre-\n  registered out-of-sample result carrying its own falsification "
          f"conditions.")
    print(f"{'=' * 78}")

    OUT.write_text(json.dumps(
        {"purpose": "D288 gate B: each gate-A survivor against its own "
                    "pre-declared shape, copied from the pre-registration",
         "calibration_ok": bool(okA), "calibration": whyA,
         "specificity_rank": list(SPECIFICITY),
         "survivors": survivors, "verdicts": verdicts,
         "promoted": promoted, "note": note}, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
