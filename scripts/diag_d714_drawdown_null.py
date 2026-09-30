"""D714 addendum (post hoc, the principal: "Null test drawdown also?"). Descriptive; D714's verdict stands.

The same count-matched null as D714 (20,000 random |A|-subsets of NQ F2's trades B, seed 714, the same draw sequence),
each kept in time order, scored on max drawdown (lower is better), total net, and net / max drawdown (a Calmar-style
ratio). The agreement book A is ranked against it. The skipped set is ranked against random 55-trade subsets the same
way, reported. In-sample to 2023-12-29. Writes data/diag_d714_drawdown_null.json.

    uv run python scripts/diag_d714_drawdown_null.py --run
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage1_d714_nq_when_es_agrees as S  # noqa: E402

M = S.M
OUT = REPO / "data" / "diag_d714_drawdown_null.json"


def max_dd(x: np.ndarray) -> float:
    eq = np.cumsum(x)
    return float(np.max(np.maximum.accumulate(np.r_[0.0, eq])[1:] - eq))


def draws(net_b: np.ndarray, n: int, n_draw: int, seed: int) -> dict[str, np.ndarray]:
    """D714's draw sequence (the same generator calls), each subset kept in time order."""
    rng = np.random.default_rng(seed)
    dd, tot, ef = np.empty(n_draw), np.empty(n_draw), np.empty(n_draw)
    for i in range(n_draw):
        k = np.sort(rng.choice(len(net_b), n, replace=False))
        x = net_b[k]
        dd[i], tot[i], ef[i] = max_dd(x), float(x.sum()), S.efficiency(x)
    return {"dd": dd, "total": tot, "eff": ef, "calmar": tot / dd}


def rank_block(obs: dict[str, float], d: dict[str, np.ndarray]) -> dict[str, Any]:
    return {"max_drawdown": {"obs": obs["dd"], "p5": float(np.quantile(d["dd"], 0.05)), "p50": float(np.median(d["dd"])),
                             "p95": float(np.quantile(d["dd"], 0.95)),
                             "share_of_draws_with_dd_at_or_below_obs": float((d["dd"] <= obs["dd"]).mean())},
            "calmar": {"obs": obs["calmar"], "p50": float(np.median(d["calmar"])), "p95": float(np.quantile(d["calmar"], 0.95)),
                       "rank": float((d["calmar"] < obs["calmar"]).mean())},
            "total_net": {"obs": obs["total"], "p50": float(np.median(d["total"])), "p95": float(np.quantile(d["total"], 0.95)),
                          "rank": float((d["total"] < obs["total"]).mean())}}


def run() -> dict[str, Any]:
    t0 = time.time()
    Xe = M.clock_frame(M.load_root("ES"), M.ANCHOR)
    Fe = M.f2_on(Xe)
    M.es_known_answer(Xe)
    Xn = M.clock_frame(M.load_root("NQ"), M.ANCHOR)
    Fn = M.f2_on(Xn)
    sn = Xn.index.to_numpy(str)
    net = Xn["gross"].to_numpy(float) - Xn.attrs["cost"]
    es_take = pd.Series(Fe["take"] & Fe["window"], index=Xe.index)
    es_side = pd.Series(Xe["side"].to_numpy(float), index=Xe.index)
    agree = (es_take.reindex(Xn.index).fillna(False).to_numpy(bool)
             & (es_side.reindex(Xn.index).to_numpy() == Xn["side"].to_numpy(float)))
    Bm = (Fn["take"] & Fn["window"]) & (sn >= S.START)
    Am, Dm = Bm & agree, Bm & ~agree
    net_b = net[Bm]
    rec = json.loads(S.OUT.read_text(encoding="utf-8"))
    if int(Am.sum()) != rec["A_trades"] or int(Bm.sum()) != rec["B_trades"]:
        raise RuntimeError("D714's books are not reproduced")
    ef_rec, _ = S.null(net_b, int(Am.sum()), 200, S.SEED)
    d = draws(net_b, int(Am.sum()), S.N_DRAW, S.SEED)
    # the draw sequence is D714's: sorting a subset does not change its efficiency
    if not np.allclose(d["eff"][:200], ef_rec, rtol=0, atol=1e-15):
        raise RuntimeError("the draws are not D714's")
    obs = {k: v for k, v in (("dd", max_dd(net[Am])), ("total", float(net[Am].sum())))}
    obs["calmar"] = obs["total"] / obs["dd"]
    ds = draws(net_b, int(Dm.sum()), S.N_DRAW, S.SEED + 1)
    obs_d = {"dd": max_dd(net[Dm]), "total": float(net[Dm].sum())}
    obs_d["calmar"] = obs_d["total"] / obs_d["dd"]
    return {"spec": "D714 addendum, post hoc and descriptive (the principal: \"Null test drawdown also?\")",
            "B": {"trades": int(Bm.sum()), "max_drawdown": max_dd(net_b), "total": float(net_b.sum())},
            "A_agreement_vs_random_216": rank_block(obs, d),
            "skipped_vs_random_55_reported": rank_block(obs_d, ds),
            "draws": S.N_DRAW, "runtime_min": round((time.time() - t0) / 60, 2)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if not a.run:
        ap.print_help()
        return 1
    out = run()
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
