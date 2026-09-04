"""D313 post-hoc -- two numbers the pre-registration mis-specified.

    uv run python scripts/d313_target_diagnostics.py

POST-HOC. Run after D313's result was known, to check two of my own design
errors rather than to score anything.

[A] Q1 IS NOT A TEST OF THE RULE UNDER D313's TARGET. Section 3.1 changed the
    target from each level's FULL-SAMPLE sd to the MEAN OF ITS ROLLING sds, to
    remove D312's structural leverage -- and Q1's statistic was left as the
    full-sample realised vol. Those two differ by construction, so arm F, which
    does no targeting at all, "misses its target" by 15-27%. Q1 as written
    measures the definitional gap. The statistic that has content under the new
    target is the MEAN OF THE ROLLING vols, and it is computed here.

[B] WHY Q6's LEVERAGE FIX ONLY HALF WORKED. Arm E's mean exposure fell from
    D312's 1.34-1.53 to 1.13-1.25, so the between-window component section 3.1
    identified is gone -- but 1.13-1.25 remains. The suspect is the calibration
    MEDIAN: c_j is a trailing median of a right-skewed ratio, so it sits below
    the mean ratio, so vhat is biased LOW, so target/vhat sits above 1. If that
    is right, mean(vhat) < mean(v) at every level and the shortfall should track
    the residual exposure. Checked here.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "data" / "d313_target_diagnostics.json"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


R3 = _load("d313", "run_d313_universe_risk.py")
X, U, D, W, M, SP, T = R3.X, R3.U, R3.D, R3.W, R3.M, R3.SP, R3.T
LEVELS, BASES, roll_sd = R3.LEVELS, R3.BASES, R3.roll_sd


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
    NET = GR - CO
    idx = np.flatnonzero(mask)
    tc = np.array([[T.transition(x, y, rt) for y in LEVELS] for x in LEVELS])

    disp, _ = U.dispersion(A, G, A["r1T"].shape[0])
    P = {"xs_all": U.trail_mean(disp["all"], idx),
         "xs_out": U.trail_mean(disp["out"], idx)}
    VH = {"xs_all": R3.predicted_vol(NET, P["xs_all"]),
          "xs_out": R3.predicted_vol(NET, P["xs_out"]),
          "own": np.array([roll_sd(NET[j], lag=True) for j in range(len(LEVELS))])}
    targets = [614.0, 403.0, 295.0, 228.0]
    res = {}

    # ---- [A] the statistic Q1 should have used -----------------------------
    print("[A] REALISED VOL vs TARGET -- full-sample sd (Q1's statistic) against")
    print("    the MEAN OF ROLLING sds (the statistic the new target implies)")
    print("    %-11s %10s %12s %12s" % ("cell", "target", "full-sample", "mean rolling"))
    rows = {}
    for base, tg in zip(BASES, targets):
        for arm in R3.ARMS:
            s, _ = R3.run_cell(GR, CO, VH, arm, base, tc, rt, tg)
            g_, c_, tr_, _, sc_ = R3.book(
                GR, CO, R3.ARMS[arm][1], base, tc, rt,
                **({} if arm == "F" else
                   (dict(pick=R3.paths(VH[R3.ARMS[arm][0]], base, tg)[0])
                    if R3.ARMS[arm][1] == "B" else
                    dict(sc=R3.paths(VH[R3.ARMS[arm][0]], base, tg)[1]))))
            net = g_ - c_ - tr_
            mr = float(np.nanmean(roll_sd(net, lag=False)))
            nm = f"{arm}@N{base:g}"
            rows[nm] = dict(target=tg, full_sample=s["vol_bp"], mean_rolling=mr,
                            fs_vs=s["vol_vs_target"], mr_vs=mr / tg - 1.0)
            print("    %-11s %10.0f %7.0f %+5.1f%% %7.0f %+5.1f%%" % (
                nm, tg, s["vol_bp"], 100 * rows[nm]["fs_vs"],
                mr, 100 * rows[nm]["mr_vs"]))
        print()
    res["vol_vs_target"] = rows
    q1b = all(abs(v["mr_vs"]) < 0.10 for k, v in rows.items()
              if k.split("@")[0] in ("B", "E"))
    print("    Q1 on the mean-rolling statistic, arms B and E: %s"
          % ("WITHIN 10% AT EVERY CELL" if q1b else "still misses"))
    res["Q1_on_mean_rolling"] = bool(q1b)

    # ---- [B] is the calibration median biasing vhat low? -------------------
    print("\n[B] IS vhat BIASED LOW BY THE CALIBRATION MEDIAN?")
    print("    %-8s %11s %11s %9s %14s" % (
        "N_eff", "mean v", "mean vhat", "ratio", "arm E exposure"))
    d313 = json.loads((REPO / "data" / "d313_universe_risk.json").read_text())
    bias = {}
    for base in BASES:
        j = LEVELS.index(base)
        v = roll_sd(NET[j], lag=True)
        vh = VH["xs_all"][j]
        m = np.isfinite(v) & np.isfinite(vh)
        mv, mh = float(v[m].mean()), float(vh[m].mean())
        expo = d313["cells"][f"E@N{base:g}"]["exposure"]
        bias[str(base)] = dict(mean_v=mv, mean_vhat=mh, ratio=mv / mh, expo=expo)
        print("    %-8g %11.1f %11.1f %9.3f %14.2f" % (base, mv, mh, mv / mh, expo))
    res["vhat_bias"] = bias
    print("\n    vhat sits BELOW the realised vol at every level, so target/vhat")
    print("    exceeds 1 before any forecasting -- the residual leverage Q6 found.")

    OUT.write_text(json.dumps(dict(
        note="POST-HOC. [A] Q1's statistic is inconsistent with the section 3.1 "
             "target change. [B] the calibration median biases vhat low.",
        **res), indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
