"""POST HOC (after D662's one run; unpromotable): D662's control 'F on g alone' came out b 0.48, t 2.30. Is it the
break x gamma product (the break as the shock), and does it survive its own null, COVID and the years? In-sample only
(the runner's sealed loader). Writes data/diag_d662_gamma_alone.json.

    uv run python scripts/diag_d662_gamma_alone.py --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "diag_d662_gamma_alone.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    sys.path.insert(0, str(REPO / "scripts"))
    import stage0_d662_gamma_product as S

    V = S.load_v2()
    R = V.R
    b, use, Gd = V.load_inputs(a.data_root, False)
    tab = R.session_table(b, use, roots=(S.ROOT,))[S.ROOT]
    bars = R.bar_arrays(b)
    d = S.session_frame(b, tab, Gd[S.ROOT])
    out = {}
    for lab, win in (("morning", S.MORNING), ("midday", S.MIDDAY)):
        r = S.rows_for(d, bars, win, R)
        y, g = r["F"].to_numpy(float), r["g"].to_numpy(float)
        f = S.hac(y, g[:, None])
        # the purged enumerated rotation of g, slope only
        cal = list(d.index)
        T = len(cal)
        pos = pd.Index(cal).get_indexer(r.index)
        gv = d["g"].reindex(cal).to_numpy(float)
        offs = np.array([o for o in range(T) if min(o, T - o) > S.PURGE])
        Gm = gv[(pos[None, :] + offs[:, None]) % T]
        gc = Gm - Gm.mean(axis=1, keepdims=True)
        null = (gc * (y - y.mean())).sum(axis=1) / (gc ** 2).sum(axis=1)
        idx = r.index.to_series()
        q = pd.qcut(r["g"].rank(method="first"), 5, labels=False)
        by_year = {}
        for yr in sorted({s[:4] for s in r.index}):
            m = idx.str.startswith(yr).to_numpy()
            if m.sum() > 30:
                by_year[yr] = float(np.polyfit(g[m], y[m], 1)[0])
        ex = ~idx.between(*S.COVID).to_numpy()
        out[lab] = {"n": int(len(y)), "slope": float(f.params[1]), "t_hac": float(f.tvalues[1]),
                    "rotation_rank": float((null < f.params[1]).mean()), "null_p50": float(np.median(null)),
                    "null_p95": float(np.quantile(null, 0.95)),
                    "slope_ex_covid": float(np.polyfit(g[ex], y[ex], 1)[0]),
                    "t_ex_covid": float(S.hac(y[ex], g[ex][:, None]).tvalues[1]),
                    "by_year": by_year, "years_positive": int(sum(v > 0 for v in by_year.values())),
                    "F_by_g_quintile": r.groupby(q.to_numpy())["F"].mean().round(3).to_dict(),
                    "F_short_vs_long": {"short": float(y[g > 0].mean()), "long": float(y[g <= 0].mean())},
                    "g_sd": float(g.std())}
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
