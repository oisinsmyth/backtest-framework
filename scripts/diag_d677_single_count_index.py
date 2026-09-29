"""D677 s.1 applied to the index roots: D668's plain break and D672's compression tier with the friction counted ONCE.

The D668/D671/D672/D676 stack fills every stop one tick through inside the gross and then charges $3 + the measured
crossing + one more tick. Single count = the trade at the level (no fill ticks) - $3 - the measured crossing. This
reproduces D668's gross and D672's C1 net to 1e-9 before reporting. In-sample, already read; the vault is not read.
Dealer gamma (GEX): SqueezeMetrics -- read only because D672's evaluation window is defined through D671's size
forecast; nothing per-date is written.

    uv run python scripts/diag_d677_single_count_index.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d671_break_construction as C  # noqa: E402

M, X, T = C.M, C.X, C.T
DATA = Path("C:/Users/O/Desktop/Projects/Backtest Framework/data")
OUT = REPO / "data" / "diag_d677_single_count_index.json"


def main() -> int:
    t0 = time.time()
    costs = M.micro_costs()
    b, use, Gd, R = M.load_bars(DATA, False, M.ROOTS)
    C._R = R
    T.MULT.update(M.MULT)
    tabs = R.session_table(b, use, roots=M.ROOTS)
    bars = R.bar_arrays(b)
    dix = pd.read_csv(DATA / "raw" / "squeezemetrics" / "DIX.csv", encoding="utf-8", dtype={"date": str})
    gex = dix[dix["date"] < M.RESERVED_FROM].set_index("date")["gex"].astype(float).sort_index()
    cal_all = pd.read_csv(DATA / "fixtures" / "cme_session_calendar.csv.gz", encoding="utf-8", dtype={"day": str})
    j668 = json.loads((REPO / "data" / "stage0_d668_break_predictor.json").read_text(encoding="utf-8"))["roots"]
    j672 = json.loads((REPO / "data" / "stage0_d672_compression_break.json").read_text(encoding="utf-8"))["roots"]
    out = {"spec": "D677 s.1 on D668 / D672 (single-count friction)", "credit": "dealer gamma (GEX): SqueezeMetrics", "roots": {}}
    for r in M.ROOTS:
        tick, c = M.TICK_PTS[r], costs[r]
        d = T.root_frame(b, tabs[r], r)
        d = d[np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)].copy()
        d["gd_spx"] = T.gex_prior(gex, d.index)
        rows = []
        for s, rec in d.iterrows():
            bb = bars.get((r, s))
            if bb is None:
                continue
            Lh, Ll, A = float(rec["prior_high"]), float(rec["prior_low"]), float(rec["atr20"])
            X.TICK = tick
            p = X.plain_break(bb, Lh, Ll, A)
            if p is None:
                continue
            px, _ = X.exit_trade(bb, p["i"], p["D"], p["entry"], p["L"], A, 0.0, "E4")
            X.TICK = 0.0
            p0 = X.plain_break(bb, Lh, Ll, A)
            if p0 is None or p0["i"] != p["i"] or p0["D"] != p["D"]:
                raise SystemExit(f"{r} {s}: the break moved when the fill tick was removed")
            px0, _ = X.exit_trade(bb, p0["i"], p0["D"], p0["entry"], p0["L"], A, 0.0, "E4")
            rows.append({"session": s, "D": p["D"], "entry": p["entry"], "level": p0["entry"],
                         "E4_gross": p["D"] * (px / p["entry"] - 1) * 1e4, "E4_level": p0["D"] * (px0 / p0["entry"] - 1) * 1e4})
        X.TICK = tick
        tr = pd.DataFrame(rows).sort_values("session").reset_index(drop=True)
        g, g0 = tr["E4_gross"].to_numpy(float), tr["E4_level"].to_numpy(float)
        cost = c["cost_usd"] / c["usd_per_point"] / tr["entry"].to_numpy(float) * 1e4
        single = g0 - (3.0 + c["crossing_ticks"] * c["tick_usd"]) / c["usd_per_point"] / tr["level"].to_numpy(float) * 1e4
        if abs(g.mean() - j668[r]["gate1"]["gross_mean"]) > 1e-9:
            raise SystemExit(f"{r}: does not reproduce D668's gross ({g.mean()} vs {j668[r]['gate1']['gross_mean']})")
        res = {"trades": int(len(tr)), "D668_gross": M.mean_t(g, R)[:2], "at_level_gross": M.mean_t(g0, R)[:2],
               "fill_tick_drag": float(g.mean() - g0.mean()), "D668_net": M.mean_t(g - cost, R)[:2],
               "single_count_net": M.mean_t(single, R)[:2], "correction": float(single.mean() - (g - cost).mean())}
        # D672's compression tier C1 on the same trades (development roots only)
        if r in C.ROOTS:
            on = C.overnight(b, r)
            S_ = C.session_features(d, on, cal_all[cal_all["root"] == r].set_index("day"))
            sess = S_.index.to_numpy()
            comp = (C.tiers(S_["rv5"].to_numpy(float)) + C.tiers(S_["on_range"].to_numpy(float))) / 2
            ct = pd.Series(C.tiers(comp), index=sess).reindex(tr["session"]).to_numpy()
            f671, _ = C.size_forecast(S_[list(C.SIZE_FEATS)].to_numpy(float), S_["y"].to_numpy(float))
            t671 = pd.Series(C.tiers(f671), index=sess).reindex(tr["session"]).to_numpy()
            win = np.isfinite(t671) & np.isfinite(ct)
            c1 = win & (ct < 1 / 3)
            want = j672[r]["books"]["C1_compression"]["net"] if "books" in j672[r] else None
            here = float((g - cost)[c1].mean())
            if want is not None and abs(here - want) > 1e-9:
                raise SystemExit(f"{r}: does not reproduce D672's C1 net ({here} vs {want})")
            res["D672_C1"] = {"trades": int(c1.sum()), "D672_net": M.mean_t((g - cost)[c1], R)[:2],
                              "single_count_net": M.mean_t(single[c1], R)[:2], "reproduced": want is not None}
        out["roots"][r] = res
        print(r, json.dumps(res, default=float), flush=True)
    out["runtime_min"] = round((time.time() - t0) / 60, 2)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
