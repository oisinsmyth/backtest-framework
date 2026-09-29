"""D691 post-hoc diagnostic, NOT pre-registered and reported as such in the D691 RESULT: is M1's gain implied volatility,
or the RV20 denominator of ivrv = ln(IV / RV20)? RV20 is realised and is not in M0, so it could carry the gain alone.

    uv run python scripts/diag_d691_iv_decomposition.py

Models, each D671's walk-forward NNLS size forecast with every added term at sign +:
    M0 (D671's six features), A = M0 + (-ln RV20), B = M0 + ln IV, C = M0 + ivrv (the registered M1),
    D = M0 + ln IV + (-ln RV20).
Scored pairwise on the sessions where all five forecasts exist, with D691's Newey-West (5 lags) Diebold-Mariano t.
In-sample only (to 2025-02-28; the vault is never read). Writes data/diag_d691_iv_decomposition.json: statistics only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d691_iv_size as D  # noqa: E402

OUT = REPO / "data" / "diag_d691_iv_decomposition.json"
PAIRS = [("M0", "A_rv20"), ("M0", "B_lniv"), ("M0", "C_ivrv"), ("M0", "D_lniv_rv20"), ("A_rv20", "D_lniv_rv20"),
         ("A_rv20", "C_ivrv")]


def main() -> int:
    fr = D.frames()
    out = {"spec": "post-hoc diagnostic to D691 (not pre-registered)", "credit": "dealer gamma (GEX): SqueezeMetrics"}
    for r in D.ROOTS:
        tab, _ = D.iv_cached(r)
        dz = D.design(fr[r], tab)
        sess, F0, y = dz["sess"], dz["F0"], dz["y"]
        nlrv, lniv = -np.log(dz["rv"]), dz["lniv"]
        f = {"M0": D.forecast(F0, y, D.SIGN0),
             "A_rv20": D.forecast(np.column_stack([F0, nlrv]), y, D.SIGN1),
             "B_lniv": D.forecast(np.column_stack([F0, lniv]), y, D.SIGN1),
             "C_ivrv": D.forecast(np.column_stack([F0, dz["ivrv"]]), y, D.SIGN1),
             "D_lniv_rv20": D.forecast(np.column_stack([F0, lniv, nlrv]), y, np.append(D.SIGN0, [1.0, 1.0]))}
        e = {k: y - v for k, v in f.items()}
        ev = (sess >= D.WINDOW_FROM) & np.all([np.isfinite(v) for v in e.values()], axis=0)
        res = {"n": int(ev.sum()), "corr_ivrv_lnIV": float(np.corrcoef(dz["ivrv"][ev], lniv[ev])[0, 1]),
               "corr_ivrv_negLnRV20": float(np.corrcoef(dz["ivrv"][ev], nlrv[ev])[0, 1]),
               "corr_lnIV_negLnRV20": float(np.corrcoef(lniv[ev], nlrv[ev])[0, 1])}
        for a, b in PAIRS:
            d = e[a][ev] ** 2 - e[b][ev] ** 2
            t, _ = D.nw_t(d)
            res[f"{b} over {a}"] = {"dbar": float(d.mean()), "t_hac": t,
                                    "mse_reduction_pct": float(100 * d.mean() / np.mean(e[a][ev] ** 2))}
        # C over M0 = A over M0 + C over A on the same sessions: assert the bookkeeping
        s = res["A_rv20 over M0"]["dbar"] + res["C_ivrv over A_rv20"]["dbar"]
        if not np.isclose(s, res["C_ivrv over M0"]["dbar"], rtol=0, atol=1e-12):
            raise SystemExit("decomposition does not add up")
        out[r] = res
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
