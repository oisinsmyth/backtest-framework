"""POST HOC diagnostic, declared before it ran (D742 RESULT A1, addendum 2): the D737 agreement lead, point in time.
In-sample only (<= 2023-12-29); descriptive; nothing here is vault evidence.

    uv run python scripts/diag_d742_agreement_pit.py      # -> data/diag_d742_agreement_pit.json

PIT-1 classes D737's trades by what was known at D737's entry (floor off / already agreed / already opposed / not yet).
PIT-2 trades D737's direction only when the floored follow agrees, entering at the later trigger with D735's 1 sigma_rem
stop. D737's trades come from its own frozen functions (1,699 re-proved); D737's own trades re-priced by
stage0_d742_stop_oracle.stop_exit must equal its E1 gross.
"""
from __future__ import annotations

import json
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

OUT = REPO / "data" / "diag_d742_agreement_pit.json"
D737_MEAN = 14.869653841921307


def book(net_d: np.ndarray, taken: np.ndarray, days: np.ndarray) -> dict:
    years = np.array([d[:4] for d in days])
    dd, cal = D741.dd_stats(net_d[taken]) if taken.any() else (0.0, 0.0)
    return {"trades": int(taken.sum()), "mean_net": float(net_d[taken].mean()) if taken.any() else None,
            "median_net": float(np.median(net_d[taken])) if taken.any() else None,
            "win_rate": float((net_d[taken] > 0).mean()) if taken.any() else None, "total": float(net_d.sum()),
            "sharpe": Z.sharpe(net_d), "sortino": Z.sortino(net_d), "max_dd": dd, "calmar": cal,
            "worst_day": float(net_d.min()),
            "by_year": {y: [round(float(net_d[years == y].sum()), 2), int((taken & (years == y)).sum())] for y in np.unique(years)}}


def main() -> int:
    import stage1_d711_f2_mechanism as M711
    cl = M711.cost_line("NQ")
    cost, usd = float(cl["cost"]), float(cl["usd_per_point"])
    pnN = T7.panel_from_raw("NQ", S1.read_cut(S1.DATA / "fixtures" / "fut_NQ_rth_1m.csv.gz"))
    pnY = T7.panel_from_raw("YM", S1.read_cut(S1.DATA / "fixtures" / "fut_YM_rth_1m.csv.gz"))
    for pn in (pnN, pnY):
        Z.no_session_after(pn["days"], f"the {pn['root']} panel")
    days = pnN["days"]
    c = V737.cell(pnN, pnY)
    V737.check_known(c, cost)
    pp = c["pp"]
    if not np.allclose(pp["soc"], pnN["soc"], equal_nan=True):
        raise AssertionError("D737's sigma_oc differs from D727's")
    Op, H, L, last = pp["Op"], pp["H"], pp["L"], pp["C"][:, -1]
    # the floored follow's trigger on every day
    ob = T7.objects(pnN)
    bk = {k: S1.book(pnN, ob, k, usd, cost) for k in S1.KS}
    S1.known_answers(bk, days, json.loads((REPO / "data" / "stage0_d727_trend_curve.json").read_text(encoding="utf-8")))
    b = bk[S42.K]
    floor_on = pnN["soc"] * usd >= S42.FLOOR_USD
    trig = b["side"] != 0
    tA = np.where(trig, np.array(T7.CLOCKS)[np.clip(b["first"], 0, None)], 10_000)
    sA = b["side"]
    # D737's own trades, re-priced by the stop function (convention check)
    d = c["d"][days[c["d"]] <= V737.IN_HI]
    m0, D = c["m0"][d], c["D"][d]
    g37 = c["g"][days[c["d"]] <= V737.IN_HI]
    rep = np.array([D[k] * (S42.stop_exit(Op[i, m0[k]], D[k], int(m0[k]), 1.0, pnN["soc"][i], Op[i], H[i], L[i], last[i])[0]
                            - Op[i, m0[k]]) * usd for k, i in enumerate(d)])
    if not np.allclose(rep, g37, atol=1e-9):
        raise AssertionError(f"D737's trades re-priced by stop_exit differ ({int((~np.isclose(rep, g37, atol=1e-9)).sum())} trades)")
    net37 = g37 - cost
    # PIT-1
    fo = floor_on[d]
    known = trig[d] & (tA[d] <= m0)
    cls = np.where(~fo, "floor_off", np.where(known & (sA[d] == D), "already_agreed",
                                              np.where(known & (sA[d] == -D), "already_opposed", "not_yet")))
    pit1 = {k: {"n": int((cls == k).sum()), "mean_net": float(net37[cls == k].mean()), "total": float(net37[cls == k].sum()),
                "win_rate": float((net37[cls == k] > 0).mean())} for k in ("floor_off", "already_agreed", "already_opposed", "not_yet")}
    # PIT-2: both agree (floor on, follow triggers the same way at any clock), enter at the later trigger
    agree = fo & trig[d] & (sA[d] == D)
    ent = np.maximum(m0, np.where(trig[d], tA[d], 0))
    net2 = np.zeros(len(days))
    taken2 = np.zeros(len(days), bool)
    for k in np.flatnonzero(agree):
        i, e = d[k], int(ent[k])
        E = Op[i, e]
        x = S42.stop_exit(E, D[k], e, 1.0, pnN["soc"][i], Op[i], H[i], L[i], last[i])[0]
        net2[i], taken2[i] = D[k] * (x - E) * usd - cost, True
    later_follow = int((agree & (tA[d] > m0)).sum())
    net37d = np.zeros(len(days))
    net37d[d] = net37
    t37 = np.zeros(len(days), bool)
    t37[d] = True
    out = {"seal": f"nothing on or after {Z.CUT24}; aggregates only", "d737_trades": int(len(d)), "d737_mean_net": float(net37.mean()),
           "pit1_d737_by_state_at_entry": pit1,
           "pit2_wait_for_agreement": book(net2, taken2, days), "pit2_entries_moved_to_the_follows_later_trigger": later_follow,
           "d737_same_window": book(net37d, t37, days)}
    # POST HOC beside (added after the table above was seen): D737 with the floor alone, known at the open
    fl = np.zeros(len(days), bool)
    fl[d[fo]] = True
    out["posthoc_d737_floor_on_only"] = book(np.where(fl, net37d, 0.0), fl, days)
    out["posthoc_d737_floor_off_only"] = book(np.where(t37 & ~fl, net37d, 0.0), t37 & ~fl, days)
    a = out["pit2_wait_for_agreement"]["mean_net"] >= D737_MEAN + 10
    bb = pit1["already_agreed"]["mean_net"] - pit1["not_yet"]["mean_net"] >= 10
    out["rule"] = {"a_pit2_mean_ge_d737_plus_10": bool(a), "b_agreed_minus_not_yet_ge_10": bool(bb),
                   "lead": "SURVIVES (step 2 on the principal's word)" if a and bb else "CLOSED"}
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
