"""D652's component correlations, post hoc (D659): the runner's own component_corr, with D466's ledger series K1..K6
loaded from a checkout that holds its gitignored fixture (data/fixtures/es_c1_holds.csv.gz). The in-sample run
reported them missing because the worktree it ran in has no copy.

    uv run python scripts/diag_opening_v2_component_corr.py --ledger-root "C:/Users/O/Desktop/Projects/Backtest Framework"

The runner's daily-dollar series is not written, so each cell's per-session policy series in bp
(data/opening/v2_sessions.csv) stands in. A correlation is unchanged by a per-day scale only when the scale is
constant, so the output is labelled as the bp series. Writes data/opening/v2_component_corr.json.
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger-root", type=Path, default=REPO)
    a = ap.parse_args()
    sys.path.insert(0, str(REPO / "scripts"))
    s = importlib.util.spec_from_file_location("run_opening_v2", REPO / "scripts" / "run_opening_v2.py")
    V = importlib.util.module_from_spec(s)
    sys.modules["run_opening_v2"] = V
    s.loader.exec_module(V)

    def load_ledger(name):
        sp = importlib.util.spec_from_file_location(name, a.ledger_root / "scripts" / f"{name}.py")
        m = importlib.util.module_from_spec(sp)
        sys.modules[name] = m
        sp.loader.exec_module(m)
        return m

    V._load = load_ledger
    S = pd.read_csv(REPO / "data" / "opening" / "v2_sessions.csv", dtype={"session": str}, encoding="utf-8")
    out = {"series": "per-session policy net, bp (v2_sessions.csv)", "ledger_root": str(a.ledger_root)}
    for cell, g in S.groupby("cell"):
        out[cell] = V.component_corr(g.set_index("session")["policy"].astype(float))
    both = S.pivot(index="session", columns="cell", values="policy").dropna()
    out["V2-F_vs_V2-C"] = {"rho": round(float(both.corr().iloc[0, 1]), 4), "n_days": int(len(both))}
    (REPO / "data" / "opening" / "v2_component_corr.json").write_text(json.dumps(out, indent=1) + "\n",
                                                                      encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
