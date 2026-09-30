"""D698-A1 follow-up, in-sample only (D696 already read these trades): is the busy / low-IV/RV cell's X-minus-rest
difference stable over time, or concentrated in some periods? The amended power check's 0 % line (the full-sample
average removed) passed 26 % of 385-session windows, against the <= 10 % the amendment requires; if the local effect
varies strongly across periods, the 0 % line is not a local null. Per slice: d by calendar year and by
non-overlapping 385-session window, and the rotation test inside each non-overlapping window at 100 % and 0 %.

    uv run python scripts/diag_d698_heterogeneity.py

Writes data/diag_d698_heterogeneity.json (statistics only). The vault is never read.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import vault_d698_busy_low_iv as V  # noqa: E402

OUT = REPO / "data" / "diag_d698_heterogeneity.json"


def main() -> int:
    keep, sl, ctx = V.in_sample_slices()
    axis, flags = V.axis_and_flags(ctx["labs"], "0000", "9999")
    out: dict = {"spec": "D698-A1 follow-up: time variation of the X-minus-rest difference (in-sample)", "by_year": {},
                 "by_window": {}}
    for k in V.SLICES:
        s, g, x = keep[k]["sessions"], keep[k]["g"], keep[k]["x"]
        yrs = np.array([v[:4] for v in s])
        out["by_year"][k] = {y: (lambda st: {"n_x": st["n_x"], "d": round(st["d"], 2)})(V.slice_stat(g[yrs == y], x[yrs == y]))
                             for y in sorted(set(yrs))}
    base = {k: V.on_axis(axis, keep[k]["sessions"], keep[k]["g"]) for k in V.SLICES}
    xs = {k: flags[k.split("_")[0]][base[k][0]] == 1.0 for k in V.SLICES}
    for w in range(len(axis) // V.N_VAULT):
        s0 = w * V.N_VAULT
        row = {"sessions": [str(axis[s0]), str(axis[s0 + V.N_VAULT - 1])]}
        for scale in (1.0, 0.0):
            f_w = {r: flags[r][s0:s0 + V.N_VAULT] for r in V.ROOTS}
            sl_w = {}
            for k in V.SLICES:
                pos, g = base[k]
                m = (pos >= s0) & (pos < s0 + V.N_VAULT)
                g_s = g + np.where(xs[k], -(1 - scale) * sl[k]["d"], 0.0)
                sl_w[k] = (pos[m] - s0, g_s[m], k.split("_")[0])
            t = V.rotation_test(f_w, sl_w)
            row[f"scale={scale:g}"] = {"verdict": t["verdict"], "p": round(t.get("p", float("nan")), 4),
                                       "T": round(t.get("T", float("nan")), 2),
                                       "d": {k: round(t["slices"][k]["d"], 2) for k in V.SLICES},
                                       "n_x": {k: t["slices"][k]["n_x"] for k in V.SLICES}}
        out["by_window"][f"w{w + 1}"] = row
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
