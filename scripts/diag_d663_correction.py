"""D663 post hoc correction (after its one run; changes no verdict): two defects in the run's NQ output.
1. NQ's own-book g has NaN sessions, so every rotated slope was NaN and NQ's rotation ranks read 0.000 with NaN p50/p95.
   Recomputed here on the calendar of sessions with a finite g (the rows with NaN g were already excluded).
2. The pre-registered NQ control 'H1 with SPX GEX' was not run: the Gate F skip for the secondary shock (0f6f9e4)
   wrapped it by mistake. Run here.
The run's output (data/stage0_d663_per_root_gamma_break.json) is left as written. In-sample only, through the runner's
own sealed functions; SqueezeMetrics credited. Writes data/stage0_d663_correction.json (coefficients and statistics
only, licence-guarded).

    uv run python scripts/diag_d663_correction.py --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d662_gamma_product as S  # noqa: E402
import stage0_d663_per_root_gamma_break as T  # noqa: E402

OUT = REPO / "data" / "stage0_d663_correction.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    V = S.load_v2()
    R = V.R
    b, use, Gd = V.load_inputs(a.data_root, False)
    tabs = R.session_table(b, use)
    bars = R.bar_arrays(b)
    dix = pd.read_csv(a.data_root / "raw" / "squeezemetrics" / "DIX.csv", encoding="utf-8", dtype={"date": str})
    gex = dix[dix["date"] < T.RESERVED_FROM].set_index("date")["gex"].astype(float).sort_index()
    sy = T.SHOCK_SYMS["NQ"]
    with ProcessPoolExecutor(max_workers=1) as pool:
        ex = dict(pool.map(T.extract_job, [(sy["tick"], str(T.SC_DATA / f"{sy['tick']}.scid"))]))
    T.assert_sealed(ex[sy["tick"]])
    gt = {"tick": T.gate_f(ex[sy["tick"]], "tick"), "up": {"usable": False}, "dn": {"usable": False}}
    d = T.root_frame(b, tabs["NQ"], "NQ")
    d["gd_spx"] = T.gex_prior(gex, d.index)
    T.gex_lag_audit(gex, d.index[:: max(1, len(d) // 40)])
    d["g_spx"] = -d["gd_spx"] / d["V20"] * 100
    d["gd_own"] = Gd["NQ"].reindex(d.index) * T.MULT["NQ"] * d["prior_close"] ** 2 * 0.01
    d["g_own"] = -d["gd_own"] / d["V20"] * 100
    out = {"spec": "post hoc correction of D663's NQ output (0f6f9e4 run)", "credit": "dealer gamma (GEX): SqueezeMetrics",
           "nq_own_g_nan_sessions": int((~np.isfinite(d["g_own"])).sum()), "results": {}}
    for win, start, lab in ((S.MORNING, "09:30", "morning"), (S.MIDDAY, "12:00", "midday")):
        rows = T.breaks(d, bars, "NQ", win)
        if lab == "morning":
            T.b3_check("NQ", rows, d, bars, R)
        rows = rows.join(T.shocks(rows, start, ex[sy["tick"]], None, None, gt)).join(
            d[["g_spx", "g_own", "gd_spx", "gd_own", "sig20", "V20", "open"]])
        for gcol, gdcol in (("g_own", "gd_own"), ("g_spx", "gd_spx")):
            fin = d.index[np.isfinite(d[gcol])]
            cal, g_all = list(fin), d.loc[fin, gcol]
            rr = rows[rows.index.isin(fin)]
            out["results"][f"NQ_{lab}_H1_{gcol}"] = {"res": T.h1(rr, gcol, cal, g_all), "claim": T.size_claim(rr, gcol, gdcol, None)}
            out["results"][f"NQ_{lab}_H2_{gcol}"] = {"res": T.h2(rr, gcol, "s_tick", cal, g_all),
                                                     "claim": T.size_claim(rr, gcol, gdcol, "s_tick")}
    T.licence_guard(out)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    for k, v in out["results"].items():
        r = v["res"]
        c, t = (r["b1"], r["t"]) if "b1" in r else (r["b3"], r["t3"])
        print(f"{k:<24} coef {c:+.4f} t {t:+.2f} rank {r['rotation']['rank']:.3f} (p50 {r['rotation']['p50']:+.3f}, "
              f"p95 {r['rotation']['p95']:+.3f}) n {r['n']}")
    print("NQ own-g NaN sessions:", out["nq_own_g_nan_sessions"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
