"""POST HOC diagnostic (the principal, 2026-10-01: "see how often it agrees / wants to trade at the same time as the
similar strategy that is in the vault"): floor A + the 1.0 sigma_rem stop (D740/D742) against D737 (D735's YM k1.0
1 sigma_rem cell, programme slot 1), in-sample only (<= 2023-12-29). Descriptive; it tests nothing and changes no reading.

    uv run python scripts/diag_d742_overlap_d737.py        # -> data/diag_d742_overlap_d737.json

D737's trades are rebuilt with its own frozen functions (cell, check_known: 1,699 trades and D735's mean net to 1e-9);
both panels come from D738's chunked read cut at 2023-12-29. Nothing of D737's is edited or run in any vault mode.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d720_size_the_direction as Z  # noqa: E402
import stage0_d727_trend_curve as T7  # noqa: E402
import stage0_d738_follow_oracle as S1  # noqa: E402
import stage0_d741_macd_drawdown as D741  # noqa: E402
import stage0_d742_stop_oracle as S42  # noqa: E402
import vault_d737_nq_leads_the_dow as V737  # noqa: E402

OUT = REPO / "data" / "diag_d742_overlap_d737.json"


def stats(daily: np.ndarray) -> dict[str, float]:
    dd, cal = D741.dd_stats(daily)
    return {"total": float(daily.sum()), "sharpe": Z.sharpe(daily), "sortino": Z.sortino(daily), "max_dd": dd,
            "calmar": cal, "worst_day": float(daily.min()), "days_traded": int((daily != 0).sum())}


def main() -> int:
    import stage1_d711_f2_mechanism as M711
    cl = M711.cost_line("NQ")
    cost, usd = float(cl["cost"]), float(cl["usd_per_point"])
    pnN = T7.panel_from_raw("NQ", S1.read_cut(S1.DATA / "fixtures" / "fut_NQ_rth_1m.csv.gz"))
    pnY = T7.panel_from_raw("YM", S1.read_cut(S1.DATA / "fixtures" / "fut_YM_rth_1m.csv.gz"))
    for pn in (pnN, pnY):
        Z.no_session_after(pn["days"], f"the {pn['root']} panel")
    days = pnN["days"]
    # D737, by its own functions
    c = V737.cell(pnN, pnY)
    got = V737.check_known(c, cost)
    d37 = c["d"][days[c["d"]] <= V737.IN_HI]
    sel = days[c["d"]] <= V737.IN_HI
    net37 = np.zeros(len(days))
    side37 = np.zeros(len(days))
    min37 = np.full(len(days), -1)
    net37[d37], side37[d37], min37[d37] = c["g"][sel] - cost, c["D"][d37], c["m0"][d37]
    # floor A + the 1.0 sigma_rem stop (D742's step-1 total re-proved)
    ob = T7.objects(pnN)
    bk = {k: S1.book(pnN, ob, k, usd, cost) for k in S1.KS}
    S1.known_answers(bk, days, json.loads((REPO / "data" / "stage0_d727_trend_curve.json").read_text(encoding="utf-8")))
    b = bk[S42.K]
    ti = np.flatnonzero(b["side"] != 0)
    ai = ti[pnN["soc"][ti] * usd >= S42.FLOOR_USD]
    if len(ai) != S42.A_COUNT:
        raise AssertionError("A's count differs from D740's")
    raw = pnN["raw"]
    mins = [T7.hhmm(x) for x in range(S42.NMIN)]
    piv = {col: raw.pivot(index="day", columns="hhmm", values=col).reindex(index=days, columns=mins).to_numpy(float)
           for col in ("open", "high", "low")}
    mA = np.array([T7.CLOCKS[int(j)] for j in b["first"][ai]])
    E = np.array([ob["Pt"][i, int(b["first"][i])] for i in ai])
    sA = b["side"][ai]
    res = [S42.stop_exit(E[k], sA[k], mA[k], 1.0, pnN["soc"][i], piv["open"][i], piv["high"][i], piv["low"][i], ob["close"][i])
           for k, i in enumerate(ai)]
    netA_t = np.array([sA[k] * (r[0] - E[k]) * usd for k, r in enumerate(res)]) - cost
    if not math.isclose(netA_t.sum(), 12883.847019145058, abs_tol=0.01):
        raise AssertionError("D742's 1.0 sigma_rem total is not reproduced")
    netA = np.zeros(len(days))
    sideA = np.zeros(len(days))
    minA = np.full(len(days), -1)
    netA[ai], sideA[ai], minA[ai] = netA_t, sA, mA
    # overlap
    a_on, v_on = sideA != 0, side37 != 0
    both = a_on & v_on
    same = both & (sideA == side37)
    opp = both & (sideA == -side37)
    win = days >= days[ai[0]]                         # A's own window (it abstains before 2018)
    first_A = both & (minA < min37)
    out = {
        "seal": f"nothing on or after {Z.CUT24}; aggregates only", "d737_known_answer": got,
        "A_trades": int(a_on.sum()), "d737_trades": int(v_on.sum()), "d737_trades_in_A_window": int((v_on & win).sum()),
        "shared_days": int(both.sum()), "share_of_A_days_D737_also_trades": float(both.sum() / a_on.sum()),
        "share_of_D737_days_in_A_window_A_also_trades": float(both.sum() / (v_on & win).sum()),
        "same_direction_on_shared_days": float(same.sum() / both.sum()), "opposite_direction_days": int(opp.sum()),
        "entry_timing_on_shared_days": {
            "A_first": float(first_A.sum() / both.sum()), "D737_first": float((both & (min37 < minA)).sum() / both.sum()),
            "same_minute": float((both & (min37 == minA)).sum() / both.sum()),
            "median_A_minus_D737_minutes": float(np.median((minA - min37)[both])),
            "within_30_minutes": float((np.abs(minA - min37)[both] <= 30).sum() / both.sum())},
        "daily_net_correlation": {"all_sessions_in_A_window": float(np.corrcoef(netA[win], net37[win])[0, 1]),
                                  "shared_days_only": float(np.corrcoef(netA[both], net37[both])[0, 1])},
        "A_net_on_D737_days": {"same_direction": float(netA[same].sum()), "opposite": float(netA[opp].sum()),
                               "D737_flat": float(netA[a_on & ~v_on].sum()), "n_D737_flat": int((a_on & ~v_on).sum()),
                               "mean_same": float(netA[same].mean()) if same.any() else None,
                               "mean_D737_flat": float(netA[a_on & ~v_on].mean()) if (a_on & ~v_on).any() else None},
        "D737_net_on_A_days": {"same_direction": float(net37[same].sum()), "opposite": float(net37[opp].sum()),
                               "A_flat_in_A_window": float(net37[v_on & ~a_on & win].sum()),
                               "n_A_flat_in_A_window": int((v_on & ~a_on & win).sum())},
        "books_in_A_window": {"A_stop": stats(netA[win]), "D737": stats(net37[win]), "A_stop_plus_D737": stats(netA[win] + net37[win])},
    }
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
