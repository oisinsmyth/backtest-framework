"""D694 pre-registration aid, run before the pre-registration was written. CONDITIONER ONLY: no trade, no return and no
range outcome is read.

    uv run python scripts/diag_d694_conditioner_count.py

Counts, per root, the D691/D672 window's SESSIONS in D672's compression tiers (ctier) and the distribution of the
walk-forward ivrv percentile (p_iv) within them, so the pre-registration can fix a split that leaves both cells
populated. Sessions, not trades: a trade's existence is a price path. In-sample to 2025-02-28; the vault is never read.
Writes data/diag_d694_conditioner_count.json (statistics only). Dealer gamma (GEX): SqueezeMetrics (D691's frames).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d691_iv_size as D  # noqa: E402

C = D.C
OUT = REPO / "data" / "diag_d694_conditioner_count.json"


def main() -> int:
    fr = D.frames()
    out: dict = {"spec": "conditioner-only count before the D694 pre-registration"}
    for r in D.ROOTS:
        tab, _ = D.iv_cached(r)
        dz = D.design(fr[r], tab)
        S_ = fr[r]["S"]
        sess = dz["sess"]
        p_rv, p_on = C.tiers(S_["rv5"].to_numpy(float)), C.tiers(S_["on_range"].to_numpy(float))
        ctier = C.tiers((p_rv + p_on) / 2)
        p_iv = C.tiers(dz["ivrv"])
        w = (sess >= D.WINDOW_FROM) & np.isfinite(ctier) & np.isfinite(p_iv)
        c1 = w & (ctier < 1 / 3)
        grid = {}
        for k in range(3):
            band = w & (ctier >= k / 3) & (ctier < (k + 1) / 3)
            grid[f"c{k + 1}"] = [int((band & (p_iv < 0.5)).sum()), int((band & (p_iv >= 0.5)).sum())]
        out[r] = {
            "window_sessions": int(w.sum()), "c1_sessions": int(c1.sum()),
            "corr_ctier_p_ivrv": float(np.corrcoef(ctier[w], p_iv[w])[0, 1]),
            "p_ivrv_quantiles_in_C1": [round(float(q), 3) for q in np.quantile(p_iv[c1], [0.1, 0.25, 0.5, 0.75, 0.9])],
            "p_ivrv_quantiles_all": [round(float(q), 3) for q in np.quantile(p_iv[w], [0.1, 0.25, 0.5, 0.75, 0.9])],
            "share_C1_with_p_ivrv_ge_half": float((p_iv[c1] >= 0.5).mean()),
            "share_C1_with_p_ivrv_ge_2of3": float((p_iv[c1] >= 2 / 3).mean()),
            "grid_sessions_ctier_x_ivrv_half": grid,
            "sessions_by_year_C1_high_half": {y: int((c1 & (p_iv >= 0.5) & np.char.startswith(sess.astype(str), y)).sum())
                                              for y in map(str, range(2018, 2026))}}
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
