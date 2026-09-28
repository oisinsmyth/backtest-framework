"""D660's correction: is V2-F's 'failed fades lose' just optional stopping? Under a martingale the gross over ALL
eligible fades is ~0, so the timed-out mean must equal -(hit share x target gross) / (timed-out share). In-sample only
(the runner's sealed loader).

    uv run python scripts/diag_opening_v2_fade_martingale.py --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    sys.path.insert(0, str(REPO / "scripts"))
    import diag_opening_mechanics as M

    V = M.load_v2()
    R = V.R
    b, use, G = V.load_inputs(a.data_root, False)
    tab = R.session_table(b, use)
    bars = R.bar_arrays(b)
    D = V.cell_rows("V2-F", tab, b, G)
    D = pd.concat([D, V.outcomes(D, "V2-F", bars)], axis=1)
    D = D[~D["reason"].isin(["missing", "cancel"])]
    hit = D["reason"] == "target"
    g = D["gross"]
    print(f"rows {len(D)}  hit share {hit.mean():.4f}")
    print(f"gross mean all {g.mean():+.3f} bp (t {g.mean() / (g.std(ddof=1) / np.sqrt(len(g))):+.2f})")
    print(f"gross mean on target {g[hit].mean():+.3f}   timed-out {g[~hit].mean():+.3f}")
    print(f"martingale-implied timed-out mean {-(hit.mean() * g[hit].mean()) / (1 - hit.mean()):+.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
