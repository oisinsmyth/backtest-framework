"""D698-A1's evidence, in-sample only: the per-slice Welch z's variance under the null at the vault's size (385 sessions),
by block length, the slices' correlation, and the X label's persistence. It shows why D698's registered pooled z test is
miscalibrated. Not a result.

    uv run python scripts/diag_d698_calibration.py

Writes data/diag_d698_calibration.json (statistics only). The vault is never read.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import vault_d698_busy_low_iv as V  # noqa: E402

OUT = REPO / "data" / "diag_d698_calibration.json"


def main() -> int:
    keep, sl, _ctx = V.in_sample_slices()
    axis, tab = V.session_table(keep)
    null = {k: -sl[k]["d"] for k in V.SLICES}
    out: dict = {"spec": "D698-A1 evidence (in-sample, the registered statistic under the null at the vault's size)",
                 "draws": 1500, "n_vault_sessions": V.N_VAULT}
    for blk in (1, 20, 60, 120):
        V.BLOCK = blk
        rng = np.random.default_rng(7)
        Z = np.array([[V.resample(tab, V.draw(len(axis), V.N_VAULT, rng), null)[k]["z"] for k in V.SLICES] for _ in range(1500)])
        Z = Z[np.isfinite(Z).all(axis=1)]
        c = np.corrcoef(Z.T)
        out[f"block={blk}"] = {"var_z_per_slice": dict(zip(V.SLICES, [round(float(v), 3) for v in Z.var(axis=0)])),
                               "corr_offdiag_min_max": [round(float(c[~np.eye(4, dtype=bool)].min()), 3),
                                                        round(float(c[~np.eye(4, dtype=bool)].max()), 3)],
                               "sd_of_sum_of_z": round(float(Z.sum(axis=1).std()), 3),
                               "sd_the_registered_statistic_assumes": round(float(np.sqrt(c.sum())), 3)}
    out["persistence"] = {k: {"share_x": round(float(keep[k]["x"].mean()), 3),
                              "p_x_given_previous_break_x": round(float(keep[k]["x"][1:][keep[k]["x"][:-1]].mean()), 3)}
                          for k in V.SLICES}
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
