"""D569 Stage 0 addendum -- the soybean harvest spread: the always-on control per positioned day, the per-month
split, the placement rank, a real-time stocks-to-use rule and the COT through the window (design committed in
D569 before this ran). Diagnostic on 2011-2023 only; no pre-registration produced; nothing from 2024-01-01 on is
read on any source. Writes data/stage0_d569_soybean.json.

    uv run python -u scripts/stage0_d569_soybean_addendum.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s); sys.modules[name] = m; s.loader.exec_module(m)
    return m


R68 = _load("d568", "run_d568_corn_post_harvest_carry.py")     # the grains machinery: pairs, audits, gate, cost
R65, R64, R61, R56, R55 = R68.R65, R68.R64, R68.R61, R68.R56, R68.R55

OUT = REPO / "data" / "stage0_d569_soybean.json"
ROOT = "ZS"
COMMODITY = "Oilseed, Soybean"
WINDOW_MONTHS = (9, 10, 11)
WINDOW_FIRST, WINDOW_LAST = 9, 11
YEARS = list(range(2011, 2024))
PRIMARY, LONG, RESERVED_FROM = R55.PRIMARY, R55.LONG, R55.RESERVED_FROM
FFILL = R64.FFILL_FORMATION
SIDES_PER_WINDOW = 4
MIN_PRIOR = R68.MIN_PRIOR_NOVEMBERS      # three prior Augusts here


def su_before(w, formation, my_year):
    c = w[(w["Commodity"] == COMMODITY) & (w["ReleaseDate"] < formation) & (w["MarketYear"] == f"{my_year}/{str(my_year + 1)[-2:]}")]
    if c.empty:
        return None
    r = c.sort_values("ReleaseDate").iloc[-1]
    return {"release": r["ReleaseDate"], "flag": r["ProjEstFlag"], "su": float(r["stocks_to_use"])}


def survival_pair_series(A, cols, days, idx):
    """Object B: F/H (first delivery strictly after November, and the next listed) formed at the last session before
    September and held to November's last session, every year; daily spread return, zero elsewhere."""
    T = len(days); yB = np.zeros(T); heldB = np.zeros(T, dtype=bool); recs = []
    for y in YEARS:
        first = np.flatnonzero((idx.year == y) & (idx.month == WINDOW_FIRST)); last = np.flatnonzero((idx.year == y) & (idx.month == WINDOW_LAST))
        if first.size == 0 or last.size == 0:
            continue
        t0, t1 = first[0] - 1, last[-1]
        F0 = R64.formation_settles(A, t0, FFILL); fin = np.isfinite(F0)
        cand = np.flatnonzero(fin & (cols >= y * 12 + WINDOW_LAST + 1))
        if cand.size < 2:
            continue
        j1, j2 = int(cand[0]), int(cand[1])
        prev1, prev2 = F0[j1], F0[j2]
        for u in range(t0 + 1, t1 + 1):
            v1, v2 = A[u, j1], A[u, j2]; r1 = r2 = 0.0
            if np.isfinite(v1) and np.isfinite(prev1):
                r1 = v1 / prev1 - 1.0; prev1 = v1
            if np.isfinite(v2) and np.isfinite(prev2):
                r2 = v2 / prev2 - 1.0; prev2 = v2
            yB[u] = r1 - r2; heldB[u] = True
        recs.append({"year": y, "formation": str(days[t0]), "exit": str(days[t1]), "t1": R68.ymlabel(cols[j1]), "t2": R68.ymlabel(cols[j2]),
                     "basis0_cents": float(F0[j2] - F0[j1]), "F1": float(F0[j1])})
    return yB, heldB, recs


def main():
    t_start = time.time()
    print("D569 STAGE 0 ADDENDUM -- the soybean harvest spread; design committed before this ran; 2011-2023 only; 2024+ shut on every source")
    df = R55.load_fixture()
    if (df["day"] >= RESERVED_FROM).any():
        raise AssertionError("reserved slice present")
    live_start = R55.live_start_by_rule(df); g = R55.build_grids(df, live_start)
    days = g["days"]; T = len(days); idx = pd.to_datetime(days); me = R55.month_ends(days)
    strip = pd.read_csv(R56.STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    strip = strip[(strip["ref"] < RESERVED_FROM) & (strip["root"] == ROOT)]
    A, cols = R64.strip_tables(strip, days, [ROOT])[ROOT]
    r1, r2, dP1, dP2, held, t1_idx, F1, pairs = R68.pair_series(A, cols, days, me)
    y = r1 - r2
    wL = R55.window_mask(days, *LONG); wP = R55.window_mask(days, *PRIMARY)
    mW = R68.season_mask(days, WINDOW_MONTHS) & held
    upp_all, tick_all, comm_all, size_name = R56.min_size(g, g["roots"]); i = g["roots"].index(ROOT)
    upp, tick_usd, comm_rt = float(upp_all[i]), float(tick_all[i]), float(comm_all[i])
    if size_name[i] != ROOT or abs(upp - 50.0) > 1e-9:
        raise AssertionError(f"ZS specification: {size_name[i]} {upp}")
    yB, heldB, recsB = survival_pair_series(A, cols, days, idx)

    # ---- audits (D568's, on the short spread) ----
    audits = {}
    pb = R68.pairs_pandas(strip, days, me); audits["pairs_checked"] = R68.audit_pairs(pairs, pb)
    R61._expect_raise(lambda: R68.audit_pairs(pairs, pb[1:] + pb[:1]), "pair audit on shifted formations"); audits["pair_audit_raises"] = True
    # survival for a Sep-Nov window: T1 must deliver after the session's own holding month (the rule rolls monthly here)
    mo_idx = np.array([int(d[:4]) * 12 + int(d[5:7]) for d in days])
    def audit_survival_month(t1):
        bad = [t for t in np.flatnonzero(mW) if t1[t] <= mo_idx[t]]
        if bad:
            raise AssertionError(f"SURVIVAL: T1 delivers in a holding month on {len(bad)} sessions")
        return int(mW.sum())
    audits["survival_sessions"] = audit_survival_month(t1_idx)
    R61._expect_raise(lambda: audit_survival_month(mo_idx), "survival audit on a pair delivering in the holding month")
    audits["survival_raises_on_holding_month_pair"] = True
    both = [p["both_settle_at_end"] for p in pairs if p["t1"] and p["hold_month"] < RESERVED_FROM[:7] and int(p["hold_month"][5:7]) in WINDOW_MONTHS and p["hold_month"] >= "2011-01"]
    audits["held_contract_share"] = float(np.mean(both))
    if audits["held_contract_share"] < 1.0:
        raise AssertionError("HELD-CONTRACT AUDIT")
    mW_b = R68.season_mask_pandas(days, WINDOW_MONTHS) & held; audits["lag_mask_sessions"] = R68.audit_mask(mW, mW_b, me)
    badm = mW.copy(); badm[me[[k for k, t in enumerate(me) if t + 1 < T and mW[t + 1] and not mW[t]]]] = True
    R61._expect_raise(lambda: R68.audit_mask(badm, mW_b, me), "lag audit on a formation-session mask"); audits["lag_raises"] = True
    pnl = np.where(mW, -(dP1 - dP2) * upp, 0.0)
    audits["sign_in_money_session"] = str(days[R65.audit_sign_in_money(pnl, dP1, dP2, mW, upp)])
    R61._expect_raise(lambda: R65.audit_sign_in_money(-pnl, dP1, dP2, mW, upp), "sign audit on a negated grid")
    R61._expect_raise(lambda: R65.audit_sign_in_money(np.roll(pnl, 1), dP1, dP2, mW, upp), "sign audit on a mislagged grid"); audits["sign_raises"] = True
    audits["right_quantity_changes"] = R68.audit_right_quantity(mW, days)
    R61._expect_raise(lambda: R68.audit_right_quantity(np.arange(T) % 2 == 0, days), "right-quantity on a daily grid"); audits["right_quantity_raises"] = True

    # ---- the state variable at formation (August WASDE), the gate ----
    su_tab, n_all = R68.load_su()
    su_by_year = {}; su_meta = {}
    for yv in range(2010, 2024):
        f = [p for p in pairs if p["formation"][:7] == f"{yv}-08"]
        s = su_before(su_tab, f[0]["formation"], yv) if f else None
        su_by_year[yv] = s["su"] if s else None; su_meta[yv] = s
    gate = R68.gate_decisions(su_by_year); audits["gate_windows_checked"] = R68.audit_gate(gate, R68.gate_decisions_pandas(su_by_year))
    ks_ = sorted(gate); shifted = {ks_[j]: gate[ks_[j - 1]] if j else None for j in range(len(ks_))}
    R61._expect_raise(lambda: R68.audit_gate(gate, shifted), "gate audit on shifted decisions"); audits["gate_raises"] = True
    print(f"  ZS: {T} sessions; WASDE {n_all} rows on disk, {len(su_tab)} scored; audits {audits}")
    print("  gate by year: " + " ".join(f"{yv}:{'open' if v else ('FLAT' if v is False else 'n/a')}({su_by_year[yv]:.3f})" for yv, v in gate.items() if su_by_year[yv] is not None))

    # ---- cells: the window cell, the control, object B ----
    xW = np.where(mW, -y, 0.0); xC = np.where(held, -y, 0.0); xB = np.where(heldB, -yB, 0.0)
    mret = R68.monthly_returns(xW, days, mW & wL); mretB = R68.monthly_returns(xB, days, heldB & wL)
    win = {yv: float(mret[[p.year == yv for p in mret.index]].sum()) for yv in YEARS}
    winB = {r["year"]: float(mretB[[p.year == r["year"] for p in mretB.index]].sum()) for r in recsB}
    per_mo = {m: {"mean": float(mret[mret.index.month == m].mean()), "hit_short": float((mret[mret.index.month == m] > 0).mean()), "worst": float(mret[mret.index.month == m].min()),
                  "n": int((mret.index.month == m).sum()), "share_of_total": float(mret[mret.index.month == m].sum() / mret.sum()) if mret.sum() != 0 else None} for m in WINDOW_MONTHS}
    cal = {m: float((-y)[held & wL & (idx.month == m)].mean() * 1e4) for m in range(1, 13)}
    ctrl_day = float((-y)[held & wL].mean()); win_day = float((-y)[mW & wL].mean()); off_day = float((-y)[held & wL & ~mW].mean())
    wv = np.array([win[yv] for yv in YEARS])
    T1 = {"window_bp_per_day": win_day * 1e4, "always_on_bp_per_day": ctrl_day * 1e4, "off_window_bp_per_day": off_day * 1e4,
          "holds": bool(win_day > 1.5 * ctrl_day and off_day <= 0), "ratio": win_day / ctrl_day if ctrl_day != 0 else None,
          "sharpe_window_2016_2023": R55.sharpe(xW[wP]), "sortino_window_2016_2023": R55.sortino(xW[wP]), "sharpe_window_2011_2023": R55.sharpe(xW[wL]), "sortino_window_2011_2023": R55.sortino(xW[wL]),
          "sharpe_control_2016_2023": R55.sharpe(xC[wP]), "sharpe_control_2011_2023": R55.sharpe(xC[wL]), "sortino_control_2011_2023": R55.sortino(xC[wL]),
          "window_mean_per_year": float(wv.mean()), "window_hit_short": float((wv > 0).mean()), "per_year": {str(k): v for k, v in win.items()},
          "B_per_year": {str(k): v for k, v in winB.items()}, "B_mean": float(np.mean(list(winB.values()))), "B_hit_short": float(np.mean([v > 0 for v in winB.values()])),
          "B_sharpe_2011_2023": R55.sharpe(xB[wL]), "B_sortino_2011_2023": R55.sortino(xB[wL])}
    T2 = {"per_month": per_mo, "holds": bool(all(v["hit_short"] * v["n"] >= 8 for v in per_mo.values()) and all((v["share_of_total"] or 0) <= 0.60 for v in per_mo.values()))}
    # object B beside: its per-month split and its mean without 2012 (declared as reported-beside, not a test)
    T2["B_per_month"] = {m: {"mean": float(mretB[mretB.index.month == m].mean()), "hit_short": float((mretB[mretB.index.month == m] > 0).mean()), "worst": float(mretB[mretB.index.month == m].min()),
                             "share_of_total": float(mretB[mretB.index.month == m].sum() / mretB.sum()) if mretB.sum() != 0 else None} for m in WINDOW_MONTHS}
    exB = np.array([v for k, v in winB.items() if k != 2012]); T2["B_ex_2012"] = {"mean": float(exB.mean()), "hit_short": float((exB > 0).mean()), "n": int(exB.size), "share_2012": float(winB[2012] / sum(winB.values()))}
    print("      B per month: " + "  ".join(f"m{m}: mean {v['mean']*100:+.2f}% short pays {v['hit_short']:.2f} share {v['share_of_total']:.2f}" for m, v in T2["B_per_month"].items()) + f";  B ex-2012 mean {exB.mean()*100:+.2f}% pays {(exB>0).sum()}/{exB.size}, 2012 share {T2['B_ex_2012']['share_2012']:.2f}")
    order = sorted(cal, key=lambda m: cal[m], reverse=True)
    T3 = {"bp_per_day_by_month": cal, "three_best_for_the_short": order[:3], "holds": bool(set(order[:3]) == set(WINDOW_MONTHS))}
    print(f"  T1: window {win_day*1e4:+.2f} bp/day vs always-on {ctrl_day*1e4:+.2f} (off-window {off_day*1e4:+.2f}); Sharpe window {T1['sharpe_window_2011_2023']:+.2f} control {T1['sharpe_control_2011_2023']:+.2f} (2011-23); "
          f"window/yr mean {wv.mean()*100:+.2f}% short pays {(wv>0).mean():.2f}; B mean {T1['B_mean']*100:+.2f}% hit {T1['B_hit_short']:.2f} -> {'holds' if T1['holds'] else 'FAILS'}")
    print("      per year A: " + " ".join(f"{k}:{v*100:+.2f}" for k, v in win.items()))
    print("      per year B: " + " ".join(f"{k}:{v*100:+.2f}" for k, v in winB.items()))
    print("  T2: " + "  ".join(f"m{m}: mean {v['mean']*100:+.2f}% short pays {v['hit_short']:.2f} share {v['share_of_total']:.2f}" for m, v in per_mo.items()) + f" -> {'holds' if T2['holds'] else 'FAILS'}")
    print("  T3: short spread bp/day by month " + " ".join(f"{m}:{v:+.1f}" for m, v in cal.items()) + f"; best three {order[:3]} -> {'holds' if T3['holds'] else 'FAILS'}")

    # ---- T4 placement rank on 2011-2023, exact, purged 252 ----
    live_idx = [np.flatnonzero(held & wL)]; L = int(wL.sum()); m1 = np.where(wL, mW, False).astype(float)[None, :]
    obs = R55.sharpe(xW[wL]); null = np.full(L - 1, np.nan)
    for k in range(1, L):
        mr = R55.rotate_signs(m1, live_idx, k)[0] > 0; null[k - 1] = R55.sharpe(np.where(mr, -y, 0.0)[wL])
    ks = np.arange(1, L); keep = (ks >= R55.NULL_PURGE) & (ks <= L - R55.NULL_PURGE); nk = null[keep]
    T4 = {"observed": obs, "p05": float(np.percentile(nk, 5)), "p50": float(np.percentile(nk, 50)), "p95": float(np.percentile(nk, 95)), "rank": float((nk < obs).mean()), "offsets": int(keep.sum()), "holds": bool((nk < obs).mean() >= 0.90)}
    print(f"  T4: placement rank {T4['rank']:.3f} (observed {obs:+.3f}, p50 {T4['p50']:+.3f}, p95 {T4['p95']:+.3f}, {T4['offsets']} offsets exact) -> {'holds' if T4['holds'] else 'FAILS'}")

    # ---- T5 the real-time gate ----
    dec = [yv for yv in YEARS if gate.get(yv) is not None]; opn = [yv for yv in dec if gate[yv]]
    T5 = {"decisions": {str(k): v for k, v in gate.items()}, "su": {str(k): v for k, v in su_by_year.items()}, "open": opn, "decidable": dec,
          "ungated_mean": float(np.mean([win[yv] for yv in dec])), "ungated_hit": float(np.mean([win[yv] > 0 for yv in dec])),
          "gated_mean": float(np.mean([win[yv] for yv in opn])) if opn else None, "gated_hit": float(np.mean([win[yv] > 0 for yv in opn])) if opn else None,
          "flat_mean": float(np.mean([win[yv] for yv in dec if not gate[yv]])) if any(not gate[yv] for yv in dec) else None}
    T5["holds"] = bool(opn and T5["gated_mean"] > T5["ungated_mean"] and T5["gated_hit"] >= T5["ungated_hit"])   # the short's return is +x: 'more negative spread' = larger x
    print(f"  T5: open {opn}; gated mean {(T5['gated_mean'] or 0)*100:+.2f}% hit {T5['gated_hit']} vs ungated {T5['ungated_mean']*100:+.2f}% hit {T5['ungated_hit']:.2f} over {len(dec)}; flat-years mean {(T5['flat_mean'] or 0)*100:+.2f}% -> {'holds' if T5['holds'] else 'FAILS'}")

    # ---- T6 the formation inverse (object B's August basis) ----
    bas = np.array([r["basis0_cents"] for r in recsB]); suv = np.array([su_by_year.get(r["year"], np.nan) or np.nan for r in recsB], float); retB = np.array([-winB[r["year"]] for r in recsB])   # retB in spread units (negative = widening)
    rho_sb, p_sb, _ = R68.perm_p(suv, bas); rho_br, p_br, _ = R68.perm_p(bas, retB, seed=1)
    T6 = {"spearman_su_basis": rho_sb, "p": p_sb, "spearman_basis_spreadret": rho_br, "p2": p_br, "basis_by_year": {str(r["year"]): r["basis0_cents"] for r in recsB},
          "inverted_years": [r["year"] for r in recsB if r["basis0_cents"] < 0], "holds": bool(rho_sb > 0.5 and rho_br > 0.3)}
    print(f"  T6: S/U -> August basis rho {rho_sb:+.2f} p {p_sb:.3f}; basis -> spread return rho {rho_br:+.2f} p {p_br:.3f}; inverted at formation {T6['inverted_years']} -> {'holds' if T6['holds'] else 'FAILS'}")

    # ---- T7 the COT through the window ----
    cot = pd.read_csv(R68.COT, encoding="utf-8", dtype={"code": str})
    cot = cot[(cot["symbol"] == ROOT) & (cot["family"] == "legacy") & (cot["category"] == "commercial") & (cot["report_date"] < RESERVED_FROM)].copy().sort_values("report_date")
    cot["nss"] = (cot["short"] - cot["long"]) / cot["open_interest"]
    rows = []
    for r in recsB:
        c0 = cot[cot["report_date"] < r["formation"]]; c1 = cot[cot["report_date"] < r["exit"]]
        rows.append({"year": r["year"], "nss_formation": float(c0.iloc[-1]["nss"]), "nss_end": float(c1.iloc[-1]["nss"]), "rises": bool(c1.iloc[-1]["nss"] > c0.iloc[-1]["nss"]), "spread_ret": -winB[r["year"]]})
    n_rise = sum(x["rises"] for x in rows); rho_c, p_c, _ = R68.perm_p([x["nss_end"] - x["nss_formation"] for x in rows], [x["spread_ret"] for x in rows], seed=2)
    T7 = {"rows": rows, "rises": n_rise, "of": len(rows), "mean_change": float(np.mean([x["nss_end"] - x["nss_formation"] for x in rows])), "spearman_change_spread": rho_c, "p": p_c,
          "holds": bool(n_rise >= 9 and rho_c < -0.3)}
    print(f"  T7: commercial net short rises through the window in {n_rise}/{len(rows)}; mean change {T7['mean_change']:+.3f}; Spearman(change, spread) {rho_c:+.2f} p {p_c:.3f} -> {'holds' if T7['holds'] else 'FAILS'}")

    # ---- T8 without 2012, T9 tail ----
    ex = np.array([win[yv] for yv in YEARS if yv != 2012])
    T8 = {"mean_ex_2012": float(ex.mean()), "hit_ex_2012": float((ex > 0).mean()), "n": int(ex.size), "share_2012": float(win[2012] / wv.sum()) if wv.sum() != 0 else None, "holds": bool(ex.mean() >= 0.0025 and (ex > 0).sum() >= 10)}
    T9 = {"worst_month_short": float(mret.min()), "worst_month": str(mret.idxmin()), "holds": bool(mret.min() > -0.015)}
    print(f"  T8: ex-2012 mean {ex.mean()*100:+.2f}% short pays {(ex>0).sum()}/{ex.size}; 2012 is {T8['share_2012']:.2f} of the total -> {'holds' if T8['holds'] else 'FAILS'};  T9: worst month {T9['worst_month_short']*100:+.2f}% ({T9['worst_month']}) -> {'holds' if T9['holds'] else 'FAILS'}")

    # ---- the dollar diagnostic, one ZS a leg ----
    side = comm_rt / 2.0 + 0.5 * tick_usd; cost = np.zeros(T)
    for t in range(1, T):
        if mW[t] and not mW[t - 1]:
            cost[t] += 2 * side
        if mW[t] and (t + 1 >= T or not mW[t + 1]):
            cost[t] += 2 * side
        if mW[t] and mW[t - 1] and t1_idx[t] != t1_idx[t - 1]:
            cost[t] += 4 * side
    pn = pnl - cost
    dollar = {"sigma_positioned": float(pn[mW & wL].std(ddof=1)), "net_sharpe_2016_2023": R55.sharpe(pn[wP]), "net_sortino_2016_2023": R55.sortino(pn[wP]), "gross_sharpe_2016_2023": R55.sharpe(pnl[wP]),
              "net_sharpe_2011_2023": R55.sharpe(pn[wL]), "net_sortino_2011_2023": R55.sortino(pn[wL]), "total_2011_2023": float(pn[wL].sum()), "cost_2011_2023": float(cost[wL].sum()), "skew_2016_2023": float(pd.Series(pn[wP]).skew()),
              "rolls_inside_window": int(sum(1 for t in range(1, T) if mW[t] and mW[t - 1] and t1_idx[t] != t1_idx[t - 1]))}
    print(f"  dollar (one ZS a leg, information only): sigma ${dollar['sigma_positioned']:,.0f}/positioned day; net Sh {dollar['net_sharpe_2016_2023']:+.2f} So {dollar['net_sortino_2016_2023']:+.2f} (2016-23), {dollar['net_sharpe_2011_2023']:+.2f} (2011-23); "
          f"total ${dollar['total_2011_2023']:+,.0f} cost ${dollar['cost_2011_2023']:,.0f}; rolls inside windows {dollar['rolls_inside_window']}")

    follows = ("pre-register A under the harvest mask, as seen, gate as a secondary" if (T1["holds"] and T4["holds"] and T5["holds"] and T7["holds"]) else
               "no pre-registration: T1 or T4 fails" if not (T1["holds"] and T4["holds"]) else
               "schedule may be pre-registered ungated; the state is not carried" if not T5["holds"] else
               "schedule may be pre-registered with the avatar unsupported")
    print(f"\n  WHAT FOLLOWS (declared rule): {follows}")
    res = {"design": "D569", "years": YEARS, "objects": {"A": "rule-rolled first-nearby spread (delivery >= m+2), short T1 / long T2, masked Sep-Nov; unmasked = control", "B": "F/H survival pair held Sep-Nov"},
           "B_pairs": recsB, "T1": T1, "T2": T2, "T3": T3, "T4": T4, "T5": T5, "T6": T6, "T7": T7, "T8": T8, "T9": T9, "dollar": dollar, "audits": audits, "what_follows": follows,
           "wasde": {"on_disk": n_all, "scored": int(len(su_tab)), "last_release": su_tab["ReleaseDate"].max()}, "timing": round(time.time() - t_start, 1)}
    OUT.write_text(json.dumps(R61._clean(res), indent=1), encoding="utf-8")
    print(f"  -> {OUT.relative_to(REPO)}  ({res['timing']}s)")


if __name__ == "__main__":
    main()
