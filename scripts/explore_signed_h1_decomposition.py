"""POST HOC, after D629's one run: how NG's signed-H1 pass decomposes. Nothing here changes a verdict.

D629's runner found NG PASS (β 0.061, t 4.21) with sign(S_t) = sign(Q_t) on only 36% of days. Q_t is the funds'
AUM x L(L-1) x r(τ) scaled, and POWER showed the window's net flow leans AGAINST the day's return. So the pass is
conditional on the return control. This script reports, on the runner's own design (`run_signed_h1_stage_a.build`):
  * the deposit's H1 as literally written: S on Q and the flags, no return control;
  * S on r and the flags alone (the market's own flow–return slope), and γ in the primary fit;
  * leave-one-year-out β and t (is the pass carried by one or two years?);
  * the primary fit on the terciles of fund AUM (the source of Q's variation at a given r).
Output: `data/ledger_signed_h1_posthoc.json`.

    uv run python -W error::RuntimeWarning scripts/explore_signed_h1_decomposition.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import run_signed_h1_stage_a as R  # noqa: E402

OUT = REPO / "data" / "ledger_signed_h1_posthoc.json"


def fit_cols(y: np.ndarray, cols: list[np.ndarray]) -> dict[str, Any]:
    X = np.column_stack([np.ones(len(y))] + cols)
    return R.H.fit(y, X)


def main() -> int:
    out: dict[str, Any] = {"note": "POST HOC, after D629's run; no verdict changes", "roots": {}}
    for root in ("CL", "NG"):
        d = R.build(root, read_dependent=True)["d"]
        y = d["S"].to_numpy(float)
        q, r = d["Q"].to_numpy(float), d["r"].to_numpy(float)
        flags = [d[f].to_numpy(float) for f in R.FLAGS[root]]
        res: dict[str, Any] = {}
        res["literal_no_return_control"] = fit_cols(y, [q] + flags)
        res["return_only"] = fit_cols(y, [r] + flags)
        X = R.design_matrix(d, root, q)
        b = np.linalg.lstsq(X, y, rcond=None)[0]
        res["primary_gamma_on_r"] = float(b[2])
        res["primary_beta_on_Q"] = float(b[1])
        years = d["day"].str[:4].to_numpy()
        res["leave_one_year_out"] = {yv: R.H.fit(y[years != yv], X[years != yv]) for yv in np.unique(years)}
        aum = (d["q1_long"].abs() + d["q1_inverse"].abs()) / np.maximum(np.abs(r), 1e-12)  # contracts per unit return
        terc = np.quantile(aum, [1 / 3, 2 / 3])
        grp = np.digitize(aum, terc)
        res["by_aum_tercile"] = {str(g): R.H.fit(y[grp == g], X[grp == g]) for g in range(3)}
        res["sign_agreement_S_Q"] = float(np.mean(np.sign(y) == np.sign(q)))
        res["sign_agreement_S_r"] = float(np.mean(np.sign(y) == np.sign(r)))
        out["roots"][root] = res
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True, default=float) + "\n", encoding="utf-8", newline="\n")
    for root, res in out["roots"].items():
        lit, ro = res["literal_no_return_control"], res["return_only"]
        print(f"{root}: literal (no r) beta {lit['beta']:.4f} t {lit['t_hc1']:.2f} | r only {ro['beta']:.1f} "
              f"t {ro['t_hc1']:.2f} | primary gamma {res['primary_gamma_on_r']:.1f} beta {res['primary_beta_on_Q']:.4f}"
              f" | sign(S)=sign(r) {res['sign_agreement_S_r']:.3f}")
        print("   leave-one-year-out:", {k: f"{v['beta']:.3f}/{v['t_hc1']:.2f}" for k, v in res["leave_one_year_out"].items()})
        print("   AUM terciles:", {k: f"{v['beta']:.3f}/{v['t_hc1']:.2f}/n{v['n']}" for k, v in res["by_aum_tercile"].items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
