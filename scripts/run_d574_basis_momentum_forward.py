"""D574 -- THE FORWARD READ of basis-momentum (D564) on the reserved 2024+ slice, on the principal's word
(spec 7085aac, R8). Refuses without --principals-word.

D564's frozen construction (High4/Low4 on the 12-month first-nearby minus second-nearby momentum, 17 commodity
roots, the amended five-session formation read; the as-pre-registered one-session read kept beside) is rebuilt on
the full calendar with D562's forward loader, its in-sample primary asserted equal to D564's artifact to 1e-9,
and scored on 2024-01-02 -> the fixture's last session. Cells: the D564 family (amended EW, terciles, dollar at
minimum size, time-series), the as-pre-registered EW, the declared six-root C-d sub-book, the seasonal /
non-seasonal contribution split and the non-seasonal standalone book. Nulls: N1-full (D562's: signs rotated
within each root's full span, scored on the forward window, purged 252 both ends, enumerated) and N3-forward
(name randomisation, 2,000 draws). This run SPENDS the 2024+ slice for basis-momentum on these roots.

    python scripts/run_d574_basis_momentum_forward.py --selftest
    python scripts/run_d574_basis_momentum_forward.py --run --principals-word
"""
from __future__ import annotations

import argparse
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


R64 = _load("d564", "run_d564_basis_momentum.py")     # one instance each of D561 / D557 / D556 / D555
R61, R57, R56, R55 = R64.R61, R64.R57, R64.R56, R64.R55
R62 = _load("d562", "run_d562_trend_forward_read.py")  # the forward loader (BTC weekend rule); its own D555 instance reads the same file

OUT = REPO / "data" / "d574_basis_momentum_forward.json"
ART_D564 = REPO / "data" / "d564_basis_momentum.json"
SPEC = "7085aac"
FWD_START = R62.FWD_START                                # 2024-01-02
PRIMARY, LONG, RESERVED_FROM = R55.PRIMARY, R55.LONG, R55.RESERVED_FROM
CM = R64.CM; NON_SEASONAL = R64.NON_SEASONAL; SEASONAL = [r for r in CM if r not in NON_SEASONAL]
CD_ROOTS = ["CL", "GC", "HG", "NG", "SI", "ZC"]          # D564's C-d sub-book, declared
FFILL = R64.FFILL_FORMATION
N3_DRAWS, N3_SEED = 2000, 20260921
GUARD_OFFSETS = R61.GUARD_OFFSETS
TIME_HARD_S = 900.0
REQUIRED_OUTPUTS = ["max_drawdown_convention", "spec", "commit", "instruction", "fixture_sha256", "strip_sha256", "windows", "harness", "audits",
                    "cells", "primary", "null_n1_full", "null_n2", "null_n3_forward", "split", "dollar_book", "component_line", "overlay_carry",
                    "predictions", "verdict", "spent", "timing"]


def n3_draw(member, elig, rng):
    mr = np.zeros_like(member)
    for k in range(member.shape[1]):
        nl = int((member[:, k] == 1).sum()); ns_ = int((member[:, k] == -1).sum())
        if nl + ns_ == 0:
            continue
        el = np.flatnonzero(elig[:, k]); pick = rng.choice(el, size=nl + ns_, replace=False)
        mr[pick[:nl], k] = 1; mr[pick[nl:], k] = -1
    return mr


def audit_draw_leg_counts(member, draw, elig):
    if not ((draw == 1).sum(0) == (member == 1).sum(0)).all() or not ((draw == -1).sum(0) == (member == -1).sum(0)).all() or ((draw != 0) & ~elig).any():
        raise AssertionError("N3 AUDIT: a draw changed a leg size or positioned an ineligible root")
    return int((draw != 0).sum())


def score_forward(x, xn, pos, rsimple, roots, days, w, w_days, label):
    """The four groups on the forward window for a published book: stats, months, per root, per year, worst/best day, concentration."""
    idx = pd.to_datetime(w_days); xw = x[w]
    cnt = (pos != 0).sum(0); contrib = pos * rsimple / np.where(cnt > 0, cnt, 1)[None, :]
    tot = {r: float(contrib[i][w].sum()) for i, r in enumerate(roots)}; total = sum(tot.values()); ranked = sorted(tot.items(), key=lambda kv: -kv[1])
    share = lambda k: float(sum(v for _, v in ranked[:k]) / total) if total != 0 else None
    mret = pd.Series(xw, index=idx); mret = mret.groupby(mret.index.to_period("M")).sum()
    t_min, t_max = int(np.argmin(xw)), int(np.argmax(xw))
    per_year = {y: {"sharpe": R55.sharpe(xw[[d[:4] == y for d in w_days]]), "sortino": R55.sortino(xw[[d[:4] == y for d in w_days]]), "total": float(xw[[d[:4] == y for d in w_days]].sum())}
                for y in sorted(set(d[:4] for d in w_days))}
    return {"gross": R55.stats_block(xw, w_days, label), "net": R55.stats_block(xn[w], w_days, label + " net"),
            "months": {"n": int(len(mret)), "mean": float(mret.mean()), "median": float(mret.median()), "hit": float((mret > 0).mean()), "worst": float(mret.min()), "best": float(mret.max()),
                       "by_month": {str(p): float(v) for p, v in mret.items()}},
            "per_root": {r: {"total": tot[r], "sessions_positioned": int((w & (pos[i] != 0)).sum())} for i, r in enumerate(roots)},
            "top_share": {"top1": share(1), "top2": share(2), "top5": share(5), "n_positive_roots": int(sum(1 for v in tot.values() if v > 0)), "ranked": ranked,
                          "roots_to_half": int(next((k for k in range(1, len(ranked) + 1) if sum(v for _, v in ranked[:k]) >= 0.5 * total), len(ranked))) if total > 0 else None},
            "worst_day": {"date": str(w_days[t_min]), "return": float(xw[t_min]), "largest_loser": roots[int(np.argmin(contrib[:, w][:, t_min]))]},
            "best_day": {"date": str(w_days[t_max]), "return": float(xw[t_max]), "largest_winner": roots[int(np.argmax(contrib[:, w][:, t_max]))]},
            "per_year": per_year}, contrib


# --------------------------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------------------------
def run(principals_word: bool, log=print):
    t_start = time.time()
    if not principals_word:
        log("REFUSED: --run reads the reserved 2024+ slice for basis-momentum on the 17 commodity roots; re-run with --principals-word only on the principal's word."); return 2
    instruction = "the principal, 2026-09-20: 'Pre-register the basis-momentum forward read and run it'"
    log(f"D574 -- THE FORWARD READ of basis-momentum on {FWD_START} onward, under {instruction}\n      spec {SPEC} committed BEFORE this runner (R8)")
    df = R62.load_fixture_forward(); ref = R55.load_fixture().reset_index(drop=True)
    ins = df[df["day"] < RESERVED_FROM].reset_index(drop=True)
    if len(ins) != len(ref) or not (ins[["root", "day", "close"]].to_numpy() == ref[["root", "day", "close"]].to_numpy()).all():
        raise AssertionError("the forward loader's in-sample rows differ from D555's loader")
    live_start = R55.live_start_by_rule(df); gfull = R55.build_grids(df, live_start)
    days = gfull["days"]; T = len(days); me = R55.month_ends(days); K = len(me)
    wP = R55.window_mask(days, *PRIMARY); wL = R55.window_mask(days, *LONG); wF = days >= FWD_START; wFull = days >= LONG[0]
    dP_days, dF_days = days[wP], days[wF]
    meF = np.array([days[min(m + 1, T - 1)] >= FWD_START for m in me])
    strip = pd.read_csv(R56.STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8"); strip = strip[strip["root"].isin(CM)]
    log(f"  fixture: {len(CM)} roots x {T} sessions {days[0]}..{days[-1]}; forward {dF_days[0]}..{dF_days[-1]} = {int(wF.sum())} sessions, {int(meF.sum())} positioned month-ends; "
        f"strip to {strip['ref'].max()}; weekend BTC rows dropped {df.attrs.get('rows_dropped_weekend_sessions')}")

    # ---- the construction on the full calendar ----
    t0 = time.time()
    tables = R64.strip_tables(strip, days, CM)
    ns = R64.nearby_series(tables, CM, days, me, ffill=FFILL); BM, mom, elig = R64.signals_at_month_ends(ns["R1"], ns["R2"], ns["stale"])
    ns0 = R64.nearby_series(tables, CM, days, me, ffill=1); BM0, _, elig0 = R64.signals_at_month_ends(ns0["R1"], ns0["R2"], ns0["stale"])
    n = len(CM)
    def span_of(nsx):
        sp = np.zeros((n, T), dtype=bool)
        for i in range(n):
            ix = np.flatnonzero(nsx["live"][i])
            if ix.size:
                sp[i, ix[0]:ix[-1] + 1] = True
        return sp
    span, span0 = span_of(ns), span_of(ns0)
    rlog1 = np.where(ns["live"] & (ns["r1d"] != 0.0), np.log1p(ns["r1d"]), np.nan)
    g = dict(roots=CM, days=days, close=ns["close1"], rlog=rlog1, dP=ns["dP1"], roll=ns["roll"], live=ns["live"], span=span, nonpositive=[])
    rsimple = ns["r1d"]
    member, diag = R64.membership_fixed(BM, elig, CM, R64.N_LEG, R64.MIN_ELIGIBLE); member_pd = R64.membership_fixed_pandas(BM, elig, CM, R64.N_LEG, R64.MIN_ELIGIBLE)
    member0, diag0 = R64.membership_fixed(BM0, elig0, CM, R64.N_LEG, R64.MIN_ELIGIBLE)
    sign_held = R55.hold_from_month_ends(member.astype(float), me, T, span); held0 = R55.hold_from_month_ends(member0.astype(float), me, T, span0)
    ones = np.ones((n, T))
    x_prim = R55.book_return(sign_held, rsimple); x0 = R55.book_return(held0, ns0["r1d"])
    log(f"  nearby series built in {time.time() - t0:.0f}s")

    # ---- harness: the in-sample primary reproduces D564's artifact; D556 cell A reproduces for the overlay ----
    art = json.loads(ART_D564.read_text(encoding="utf-8"))
    ref_am = art["cells"]["EW High4/Low4"]["gross"]["sharpe"]; ref_pre = art["amendment"]["as_pre_registered"]["gross_sharpe"]
    sh_am, sh_pre = R55.sharpe(x_prim[wP]), R55.sharpe(x0[wP])
    if abs(sh_am - ref_am) > 1e-9 or abs(sh_pre - ref_pre) > 1e-9:
        raise AssertionError(f"HARNESS: in-sample primary {sh_am} vs artifact {ref_am}; as-pre-registered {sh_pre} vs {ref_pre}")
    curve = pd.read_csv(R56.CURVE, dtype={"root": str, "ref": str, "front": str, "next": str}, encoding="utf-8")
    Cg = R56.carry_grid(gfull, curve); carry_me_full = R56.carry_at_month_ends(Cg, gfull["live"], me)
    s12_me, _ = R55.signal_at_month_ends(gfull["rlog"], gfull["live"], days, me, 12)
    signsA = R56.cell_signs(carry_me_full, s12_me, None)["A"]; _, posA, _, _ = R56.positions_from_signs(signsA, R55.ew_vol(gfull["rlog"], gfull["live"]), me, gfull)
    rs_full = np.where(np.isfinite(gfull["rlog"]), np.expm1(np.nan_to_num(gfull["rlog"])), 0.0); xA = R55.book_return(posA, rs_full)
    art556 = json.loads(R61.ART_D556.read_text(encoding="utf-8"))
    if abs(R55.sharpe(xA[wP]) - art556["primary"]["observed"]) > 1e-9:
        raise AssertionError("HARNESS: D556 cell A did not reproduce in sample")
    harness = {"in_sample_primary_rebuilt": sh_am, "d564_artifact": ref_am, "in_sample_as_preregistered_rebuilt": sh_pre, "d564_artifact_as_preregistered": ref_pre,
               "d556_cellA_rebuilt": R55.sharpe(xA[wP]), "d556_artifact": art556["primary"]["observed"], "tolerance": 1e-9}
    log(f"  harness: in-sample primary {sh_am:+.6f} = artifact {ref_am:+.6f}; as-pre-registered {sh_pre:+.6f} = {ref_pre:+.6f}; D556 cell A reproduces")

    # ---- audits on the full-span objects, each proven to raise ----
    audits = {}; piv = {}
    audits["bm_cells_checked_against_strip"] = R64.audit_bm_from_strip(BM, elig, strip, CM, days, me, ffill=FFILL, pivots=piv)
    R61._expect_raise(lambda: R64.audit_bm_from_strip(-BM, elig, strip, CM, days, me, n_check=20, ffill=FFILL, pivots=piv), "BM audit on a negated grid"); audits["bm_audit_raises_on_negated_grid"] = True
    audits["leg_membership_cells"] = R57.audit_leg_membership(member, member_pd, me, days)
    R61._expect_raise(lambda: R57.audit_leg_membership(R57.swap_one_pair(member), member_pd, me, days), "membership audit on a swapped pair"); audits["membership_raises_on_swapped_pair"] = True
    audits["lag_held_cells"] = R55.audit_lag(sign_held, member_pd.astype(float), me, span, T)
    unl = np.zeros_like(sign_held)
    for k, m_ix in enumerate(me):
        lo = me[k - 1] + 1 if k > 0 else 0; unl[:, lo:m_ix + 1] = member[:, k][:, None]
    unl = np.where(span, unl, 0.0)
    R61._expect_raise(lambda: R55.audit_lag(unl, member_pd.astype(float), me, span, T), "lag audit on an unlagged book"); audits["lag_raises_on_unlagged_book"] = True
    audits["right_quantity_changes"] = R55.audit_right_quantity(sign_held, me, T)
    R61._expect_raise(lambda: R55.audit_right_quantity(np.tile(np.where(np.arange(T) % 2 == 0, 1.0, -1.0), (n, 1)), me, T), "right-quantity on a daily grid"); audits["right_quantity_raises_on_daily_grid"] = True
    upp_f, tick_f, comm_f, size_f = R56.min_size(gfull, gfull["roots"]); ix_full = [gfull["roots"].index(r) for r in CM]
    upp, tick_usd, comm_rt, size_name = upp_f[ix_full], tick_f[ix_full], comm_f[ix_full], [size_f[j] for j in ix_full]
    dollar_roots = [r for r in CM if r not in R55.DOLLAR_EXCLUDED]
    sd = sign_held.astype(int); grossD_all, _, _ = R55.dollar_book(sd, g, upp, comm_rt, tick_usd, CM)
    audits["sign_in_money_roots_checked"] = R55.audit_sign_in_money(grossD_all, sd, g, upp)
    R61._expect_raise(lambda: R55.audit_sign_in_money(-grossD_all, sd, g, upp), "sign audit on a negated grid"); audits["sign_raises_on_negated_grid"] = True
    R61._expect_raise(lambda: R55.audit_sign_in_money(R55.dollar_book(sd, dict(g, dP=np.roll(g["dP"], 1, axis=1)), upp, comm_rt, tick_usd, CM)[0], sd, g, upp), "sign audit on a mislagged grid"); audits["sign_raises_on_mislagged_grid"] = True
    elig_held = elig.copy(); elig_held[:, -1] = False; audits["held_contract_share"] = float(ns["held_ok"][elig_held].mean())
    if audits["held_contract_share"] < 0.99:
        raise AssertionError("HELD-CONTRACT AUDIT")
    audits["flat_month_ends_forward_amended"] = int(sum(1 for k in range(K) if meF[k] and diag[k]["flat"])); audits["flat_month_ends_forward_as_preregistered"] = int(sum(1 for k in range(K) if meF[k] and diag0[k]["flat"]))
    log(f"  audits: {audits}")

    # ---- cells on the forward window ----
    sig = R55.ew_vol(rlog1, ns["live"])
    member_t, _ = R57.membership_at_month_ends(np.where(elig, BM, np.nan), CM); held_t = R55.hold_from_month_ends(member_t.astype(float), me, T, span)
    BM_dm = np.full_like(BM, np.nan)
    for i in range(n):
        cnt = 0; tot = 0.0
        for k in range(K):
            if elig[i, k] and np.isfinite(BM[i, k]):
                cnt += 1; tot += BM[i, k]
                if cnt >= 12:
                    BM_dm[i, k] = BM[i, k] - tot / cnt
    ts_sign_me = np.where(np.isfinite(BM_dm), np.sign(BM_dm), 0.0); ts_sign_held, ts_pos, ts_scale, _ = R56.positions_from_signs(ts_sign_me, sig, me, g)
    cbp = R55.cost_bp_per_side(g, upp, comm_rt, tick_usd)
    pub = {"EW High4/Low4 (amended)": (sign_held, rsimple, g["roll"]), "EW High4/Low4 (as pre-registered)": (held0, ns0["r1d"], ns0["roll"]),
           "EW terciles": (held_t, rsimple, g["roll"]), "time-series": (ts_pos, rsimple, g["roll"])}
    cells, series = {}, {}
    for name, (pos, rs, roll) in pub.items():
        x = R55.book_return(pos, rs); turn, rolls, tw = R55.published_cost(pos, cbp, roll); xn = x - turn
        entry, contrib = score_forward(x, xn, pos, rs, CM, days, wF, dF_days, name + " forward")
        entry["in_sample_gross_sharpe"] = R55.sharpe(x[wP]); entry["cost_ann_bp"] = float(turn[wF].sum() / (wF.sum() / 252) * 1e4)
        cells[name] = entry; series[name] = dict(x=x, xn=xn, pos=pos, contrib=contrib)
        log(f"  {name:34s} forward gross Sh {entry['gross']['sharpe']:+.3f} / So {entry['gross']['sortino']:+.3f} (SE {entry['gross']['se']:.2f})  net {entry['net']['sharpe']:+.3f}  "
            f"months n {entry['months']['n']} hit {entry['months']['hit']:.2f} worst {entry['months']['worst']*100:+.2f}%  in-sample {entry['in_sample_gross_sharpe']:+.3f}")
    # dollar books
    sF = np.where(wF[None, :], sd, 0).astype(int)
    grossD, costD, sidesD = R55.dollar_book(sF, g, upp, comm_rt, tick_usd, dollar_roots); xgD, xnD = grossD.sum(0), (grossD - costD).sum(0)
    g_cd, c_cd, _ = R55.dollar_book(sF, g, upp, comm_rt, tick_usd, CD_ROOTS); xg_cd, xn_cd = g_cd.sum(0), (g_cd - c_cd).sum(0)
    per_root_usd = {r: float((grossD[i] - costD[i])[wF].sum()) for i, r in enumerate(CM) if r in dollar_roots}
    ranked_usd = sorted(per_root_usd.items(), key=lambda kv: -abs(kv[1]))
    dollar = {"gross": R55.stats_block(xgD[wF], dF_days, "dollar forward"), "net": R55.stats_block(xnD[wF], dF_days, "dollar forward net"), "cost_total": float(costD.sum(0)[wF].sum()),
              "sides_total": int(sidesD[:, wF].sum()), "per_root_net_usd": dict(sorted(per_root_usd.items(), key=lambda kv: -kv[1])), "largest_abs_line": ranked_usd[0],
              "largest_root_share_of_total": float(max(per_root_usd.values()) / sum(per_root_usd.values())) if sum(per_root_usd.values()) != 0 else None,
              "cd_subbook": {"roots": CD_ROOTS, "gross": R55.stats_block(xg_cd[wF], dF_days, "C-d sub-book forward"), "net": R55.stats_block(xn_cd[wF], dF_days, "C-d sub-book forward net"),
                             "per_root_net_usd": {r: float((g_cd[i] - c_cd[i])[wF].sum()) for i, r in enumerate(CM) if r in CD_ROOTS}, "in_sample_net_sharpe": art["component_line"]["cd_subset_net_sharpe"]},
              "in_sample_net_sharpe": art["component_line"]["C_a_net_sharpe"]}
    log(f"  dollar (16): forward net Sh {dollar['net']['sharpe']:+.3f} So {dollar['net']['sortino']:+.3f} sigma ${dollar['net']['sd_daily']:,.0f} total ${dollar['net']['total']:+,.0f}; largest line {ranked_usd[0]}; "
        f"sub-book net Sh {dollar['cd_subbook']['net']['sharpe']:+.3f} sigma ${dollar['cd_subbook']['net']['sd_daily']:,.0f} total ${dollar['cd_subbook']['net']['total']:+,.0f}")
    log("  dollar by root: " + ", ".join(f"{r} {v:+,.0f}" for r, v in dollar["per_root_net_usd"].items()))

    # ---- the seasonal / non-seasonal split of the primary; the non-seasonal standalone ----
    prim = series["EW High4/Low4 (amended)"]; contrib = prim["contrib"]
    ix_s = [CM.index(r) for r in SEASONAL]; ix_ns = [CM.index(r) for r in NON_SEASONAL]
    xs_c = contrib[ix_s].sum(0); xns_c = contrib[ix_ns].sum(0)
    mem_ns, diag_ns = R64.membership_fixed(BM[ix_ns], elig[ix_ns], NON_SEASONAL, R64.N_LEG_NS, R64.MIN_ELIGIBLE_NS)
    x_ns = R55.book_return(R55.hold_from_month_ends(mem_ns.astype(float), me, T, span[ix_ns]), rsimple[ix_ns])
    ng = CM.index("NG"); ng_short_share = float((member[ng, meF] == -1).mean()); ng_long_share = float((member[ng, meF] == 1).mean())
    split = {"seasonal_roots": SEASONAL, "non_seasonal_roots": NON_SEASONAL,
             "seasonal_contribution": {"total": float(xs_c[wF].sum()), "sharpe": R55.sharpe(xs_c[wF]), "sortino": R55.sortino(xs_c[wF])},
             "non_seasonal_contribution": {"total": float(xns_c[wF].sum()), "sharpe": R55.sharpe(xns_c[wF]), "sortino": R55.sortino(xns_c[wF])},
             "non_seasonal_standalone_high3_low3": {"gross": R55.stats_block(x_ns[wF], dF_days, "non-seasonal forward"), "in_sample_sharpe": R55.sharpe(x_ns[wP]),
                                                    "flat_month_ends_forward": int(sum(1 for k in range(K) if meF[k] and diag_ns[k]["flat"]))},
             "ng_share_of_forward_month_ends_short": ng_short_share, "ng_share_long": ng_long_share, "ng_contribution": float(contrib[ng][wF].sum())}
    log(f"  split: seasonal contribution {split['seasonal_contribution']['total']*100:+.2f}% (Sh {split['seasonal_contribution']['sharpe']:+.2f}) vs non-seasonal {split['non_seasonal_contribution']['total']*100:+.2f}% "
        f"(Sh {split['non_seasonal_contribution']['sharpe']:+.2f}); non-seasonal standalone {split['non_seasonal_standalone_high3_low3']['gross']['sharpe']:+.3f}; NG short {ng_short_share:.2f} of month-ends, contribution {split['ng_contribution']*100:+.2f}%")

    # ---- overlay on carry A forward ----
    idxW = {q: R61.worst_days(xA[wF], R61.WORST_Q[q]) for q in R61.WORST_Q}
    ov = R61.overlay_stats(xA[wF], prim["x"][wF], idxW); ov.update({"rho_daily": float(np.corrcoef(xA[wF], prim["x"][wF])[0, 1]), "carry_A_forward_sharpe": R55.sharpe(xA[wF])})
    log(f"  overlay on carry A forward: rho {ov['rho_daily']:+.2f} c5 {ov['c5']:+.3f}; carry A forward Sharpe {ov['carry_A_forward_sharpe']:+.2f}")

    # ---- N1-full: rotate within the full span, score on the forward window ----
    live_idx_full = [np.flatnonzero(span[i] & wFull) for i in range(n)]; L_full = int(wFull.sum()); nO = L_full - 1
    sign_full = np.where(wFull[None, :], sign_held, 0.0); held_t_full = np.where(wFull[None, :], held_t, 0.0); ts_full = np.where(wFull[None, :], ts_sign_held, 0.0)
    t0 = time.time()
    for k in [kk % nO or 1 for kk in GUARD_OFFSETS]:
        p = R55.rotate_signs(sign_full, live_idx_full, k)
        if not np.array_equal(R55.book_return(p, rsimple)[wF], R55.book_return_loop(p[:, wF], rsimple[:, wF])):
            raise AssertionError(f"exactness guard failed at offset {k}")
        R55.book_return(R55.rotate_signs(held_t_full, live_idx_full, k), rsimple); R55.book_return(R55.rotate_signs(ts_full, live_idx_full, k) * ts_scale, rsimple)
        R55.dollar_book(np.sign(R55.rotate_signs(sign_full, live_idx_full, k)).astype(int), g, upp, comm_rt, tick_usd, dollar_roots)
    audits["n1_full_exactness_guard_offsets"] = len(GUARD_OFFSETS)
    k_chk = 300; rot = R55.rotate_signs(sign_full, live_idx_full, k_chk); tF = np.flatnonzero(wF)[5]; i0 = CM.index("NG"); pos_t = int(np.flatnonzero(live_idx_full[i0] == tF)[0])
    if rot[i0, tF] != sign_full[i0, live_idx_full[i0][pos_t - k_chk]]:
        raise AssertionError("rotation semantics")
    per_offset = (time.time() - t0) / len(GUARD_OFFSETS); projected = per_offset * nO
    log(f"  N1-full: {per_offset * 1e3:.1f} ms/offset -> projected {projected:.0f} s for {nO} offsets x 4 cells")
    if projected > TIME_HARD_S:
        raise AssertionError(f"projected {projected:.0f} s > {TIME_HARD_S:.0f} s")
    cnames = ["EW High4/Low4 (amended)", "EW terciles", "dollar net", "time-series"]
    null_sh = {c: np.full(nO, np.nan) for c in cnames}; null_so = {c: np.full(nO, np.nan) for c in cnames}
    for k in range(1, nO + 1):
        r_am = R55.rotate_signs(sign_full, live_idx_full, k); x1 = R55.book_return(r_am, rsimple)[wF]
        x2 = R55.book_return(R55.rotate_signs(held_t_full, live_idx_full, k), rsimple)[wF]
        x4 = R55.book_return(R55.rotate_signs(ts_full, live_idx_full, k) * ts_scale, rsimple)[wF]
        gd, cd_, _ = R55.dollar_book(np.sign(r_am).astype(int), g, upp, comm_rt, tick_usd, dollar_roots); x3 = (gd - cd_).sum(0)[wF]
        for c, xx in zip(cnames, (x1, x2, x3, x4)):
            null_sh[c][k - 1] = R55.sharpe(xx); null_so[c][k - 1] = R55.sortino(xx)
        if k % 1000 == 0:
            log(f"    offset {k}/{nO}  {time.time() - t0:.0f}s")
    ks = np.arange(1, nO + 1); keep = (ks >= R55.NULL_PURGE) & (ks <= L_full - R55.NULL_PURGE)
    obs = {"EW High4/Low4 (amended)": cells["EW High4/Low4 (amended)"]["gross"]["sharpe"], "EW terciles": cells["EW terciles"]["gross"]["sharpe"], "dollar net": dollar["net"]["sharpe"], "time-series": cells["time-series"]["gross"]["sharpe"]}
    obs_so = {"EW High4/Low4 (amended)": cells["EW High4/Low4 (amended)"]["gross"]["sortino"], "EW terciles": cells["EW terciles"]["gross"]["sortino"], "dollar net": dollar["net"]["sortino"], "time-series": cells["time-series"]["gross"]["sortino"]}
    n1 = {"offsets_enumerated": nO, "purge_sessions": R55.NULL_PURGE, "offsets_after_purge": int(keep.sum()), "span_rotated": [LONG[0], str(days[-1])], "scored_on": [str(dF_days[0]), str(dF_days[-1])], "per_cell": {},
          "offset_profile_primary": {"k": ks.tolist(), "sharpe": null_sh["EW High4/Low4 (amended)"].tolist()}}
    for c in cnames:
        col = null_sh[c][keep]; cs = null_so[c][keep]; o = obs[c]
        n1["per_cell"][c] = dict(R61._pct(col), observed=o, pct_rank=float((col < o).mean()), clears_p95=bool(o > np.percentile(col, 95)), below_p05=bool(o < np.percentile(col, 5)),
                                 sortino=dict(R61._pct(cs), observed=obs_so[c]), unpurged=dict(R61._pct(null_sh[c]), pct_rank=float((null_sh[c] < o).mean())))
    fam = np.max(np.stack([null_sh[c][keep] for c in cnames], 1), 1); best_c = max(obs, key=obs.get)
    n2 = {"observed_best": obs[best_c], "observed_best_cell": best_c, "p50": float(np.percentile(fam, 50)), "p95": float(np.percentile(fam, 95)), "pct_rank": float((fam < obs[best_c]).mean()), "clears_p95": bool(obs[best_c] > np.percentile(fam, 95))}
    primary = n1["per_cell"]["EW High4/Low4 (amended)"]
    log(f"  N1-full primary: observed {primary['observed']:+.3f} p05 {primary['p05']:+.3f} p50 {primary['p50']:+.3f} p95 {primary['p95']:+.3f} rank {primary['pct_rank']:.3f} ({keep.sum()} offsets); "
        f"dollar rank {n1['per_cell']['dollar net']['pct_rank']:.3f}; N2 best {n2['observed_best']:+.3f} ({best_c}) p95 {n2['p95']:+.3f} rank {n2['pct_rank']:.3f}")

    # ---- N3-forward: name randomisation on the forward month-ends ----
    t0 = time.time(); rng = np.random.default_rng(N3_SEED); memF = np.where(meF[None, :], member, 0)
    audits["n3_draw_cells_checked"] = audit_draw_leg_counts(memF, n3_draw(memF, elig, np.random.default_rng(1)), elig)
    bad = n3_draw(memF, elig, np.random.default_rng(1)); k0 = int(np.flatnonzero((memF == 1).sum(0) > 0)[0]); free = np.flatnonzero((bad[:, k0] == 0) & elig[:, k0]); bad[free[0], k0] = 1
    R61._expect_raise(lambda: audit_draw_leg_counts(memF, bad, elig), "N3 audit on an extra long"); audits["n3_raises_on_extra_long"] = True
    d3 = np.full(N3_DRAWS, np.nan); d3s = np.full(N3_DRAWS, np.nan)
    for d in range(N3_DRAWS):
        mr = n3_draw(memF, elig, rng); xx = R55.book_return(R55.hold_from_month_ends(mr.astype(float), me, T, span), rsimple)[wF]; d3[d] = R55.sharpe(xx); d3s[d] = R55.sortino(xx)
    o = primary["observed"]; p95_3 = float(np.percentile(d3, 95)); se3 = R64._p95_boot_se(d3)
    n3 = {"draws": N3_DRAWS, "seed": N3_SEED, "observed": o, "p05": float(np.percentile(d3, 5)), "p50": float(np.percentile(d3, 50)), "p95": p95_3, "p95_boot_se": se3, "pct_rank": float((d3 < o).mean()),
          "clears_p95": bool(o > p95_3), "margin_in_se": float((o - p95_3) / se3) if se3 > 0 else None, "unresolved": bool(abs(o - p95_3) <= 2 * se3),
          "sortino": {"observed": obs_so["EW High4/Low4 (amended)"], "p50": float(np.nanpercentile(d3s, 50)), "p95": float(np.nanpercentile(d3s, 95))}, "wall_s": round(time.time() - t0, 1)}
    log(f"  N3-forward: p50 {n3['p50']:+.3f} p95 {n3['p95']:+.3f} (SE {se3:.3f}) rank {n3['pct_rank']:.3f} margin {n3['margin_in_se']}")

    # ---- component line (recorded; nothing can enter) ----
    component = {"dollar_16": {"forward_net_sharpe": dollar["net"]["sharpe"], "forward_net_sortino": dollar["net"]["sortino"], "skew": dollar["net"]["skew"], "sigma_usd": dollar["net"]["sd_daily"], "total_usd": dollar["net"]["total"],
                               "in_sample_net_sharpe": dollar["in_sample_net_sharpe"], "in_sample_fails": art["component_line"]["fails"]},
                 "cd_subbook": {"forward_net_sharpe": dollar["cd_subbook"]["net"]["sharpe"], "forward_net_sortino": dollar["cd_subbook"]["net"]["sortino"], "skew": dollar["cd_subbook"]["net"]["skew"],
                                "sigma_usd": dollar["cd_subbook"]["net"]["sd_daily"], "total_usd": dollar["cd_subbook"]["net"]["total"], "in_sample_net_sharpe": dollar["cd_subbook"]["in_sample_net_sharpe"]},
                 "can_enter": False, "why": "the dollar book failed C-a and C-d in sample; the sub-book was a declared subset under the C-a bar; a forward number cannot promote what did not clear in sample (pre-registration §5)",
                 "rho_with_ledger_entry": "ABSENT: the MACD arm's per-session P&L is not on disk"}

    # ---- predictions and the forward verdict ----
    cA = cells["EW High4/Low4 (amended)"]; cP = cells["EW High4/Low4 (as pre-registered)"]
    preds = {
        "P-1": {"claim": "forward gross Sharpe > 0; point 0.2-0.7", "value": cA["gross"]["sharpe"], "holds": bool(cA["gross"]["sharpe"] > 0), "in_point_range": bool(0.2 <= cA["gross"]["sharpe"] <= 0.7)},
        "P-2": {"claim": "amended and as-pre-registered: 0 flat forward month-ends each, Sharpes within 0.05", "flat_amended": audits["flat_month_ends_forward_amended"], "flat_pre": audits["flat_month_ends_forward_as_preregistered"],
                "amended": cA["gross"]["sharpe"], "as_pre": cP["gross"]["sharpe"], "holds": bool(audits["flat_month_ends_forward_amended"] == 0 and audits["flat_month_ends_forward_as_preregistered"] == 0 and abs(cA["gross"]["sharpe"] - cP["gross"]["sharpe"]) <= 0.05)},
        "P-3": {"claim": "seasonal contribution > non-seasonal; non-seasonal standalone <= 0.2; NG short >= 75% of forward month-ends", "seasonal": split["seasonal_contribution"]["total"], "non_seasonal": split["non_seasonal_contribution"]["total"],
                "ns_standalone": split["non_seasonal_standalone_high3_low3"]["gross"]["sharpe"], "ng_short_share": ng_short_share,
                "holds": bool(split["seasonal_contribution"]["total"] > split["non_seasonal_contribution"]["total"] and split["non_seasonal_standalone_high3_low3"]["gross"]["sharpe"] <= 0.2 and ng_short_share >= 0.75)},
        "P-4": {"claim": "two roots reach half the forward P&L (top-2 share >= 0.5 of a positive total)", "top2": cA["top_share"]["top2"], "roots_to_half": cA["top_share"]["roots_to_half"],
                "holds": bool(cA["top_share"]["top2"] is not None and cA["top_share"]["top2"] >= 0.5 and cA["gross"]["total"] > 0)},
        "P-5": {"claim": "16-contract book fails C-d with HO or NG the largest line; sub-book sigma <= $500 and forward net within 0.5 of +0.48", "sigma": dollar["net"]["sd_daily"], "largest": ranked_usd[0][0], "sub_sigma": dollar["cd_subbook"]["net"]["sd_daily"], "sub_net": dollar["cd_subbook"]["net"]["sharpe"],
                "holds": bool(dollar["net"]["sd_daily"] > R55.C_D_SIGMA and ranked_usd[0][0] in ("HO", "NG") and dollar["cd_subbook"]["net"]["sd_daily"] <= R55.C_D_SIGMA and abs(dollar["cd_subbook"]["net"]["sharpe"] - dollar["cd_subbook"]["in_sample_net_sharpe"]) <= 0.5)},
        "P-6": {"claim": "c5 on carry A's worst 5% forward days < 0", "c5": ov["c5"], "rho": ov["rho_daily"], "holds": bool(ov["c5"] < 0)},
        "P-7": {"claim": "falsifiers", "did_not_transfer": bool(cA["gross"]["sharpe"] <= 0), "inside_both_nulls": bool(cA["gross"]["sharpe"] > 0 and not (primary["clears_p95"] and n3["clears_p95"])),
                "amendment_mattered": bool(abs(cA["gross"]["sharpe"] - cP["gross"]["sharpe"]) > 0.1), "ng_largest_loss": bool(min(cA["top_share"]["ranked"], key=lambda kv: kv[1])[0] == "NG")},
    }
    oP = cA["gross"]["sharpe"]
    verdict = ("INVERTED" if primary["below_p05"] else "DID NOT TRANSFER" if oP <= 0 else
               "TRANSFERS" if (primary["clears_p95"] and n3["clears_p95"] and n3["margin_in_se"] is not None and n3["margin_in_se"] > 2) else
               "UNRESOLVED (N3 within 2 SE)" if (primary["clears_p95"] and n3["unresolved"]) else "INSIDE")
    log("\n  predictions: " + ", ".join(f"{k} {'holds' if v.get('holds') else 'fails'}" for k, v in preds.items() if k != "P-7") + f"; P-7 {preds['P-7']}")
    log(f"  FORWARD VERDICT {verdict}")

    res = {"max_drawdown_convention": {"sign": "negative", "note": "Drawdown LEVELS are NEGATIVE: minimum of (cumulative daily return - running peak); return units for the published books, dollars for the dollar books (D542).", "record": "D542"},
           "spec": "D574", "commit": SPEC, "instruction": instruction, "fixture_sha256": R55.sha256(R55.FIX), "strip_sha256": R55.sha256(R56.STRIP),
           "windows": {"forward": [str(dF_days[0]), str(dF_days[-1])], "sessions_forward": int(wF.sum()), "positioned_month_ends_forward": int(meF.sum()), "primary_in_sample": PRIMARY, "full_span": [LONG[0], str(days[-1])]},
           "harness": harness, "audits": audits, "cells": cells, "primary": primary, "null_n1_full": n1, "null_n2": n2, "null_n3_forward": n3, "split": split, "dollar_book": dollar,
           "component_line": component, "overlay_carry": ov, "predictions": preds, "verdict": {"forward": verdict},
           "spent": {"slice": f"{FWD_START}..{days[-1]}", "for": "basis-momentum in every form of D564's family, the as-pre-registered variant, the seasonal / non-seasonal split and the C-d sub-book, on the 17 commodity roots"},
           "timing": {"wall_s": round(time.time() - t_start, 1), "n1_ms_per_offset": round(per_offset * 1e3, 1), "n3_wall_s": n3["wall_s"]}}
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")
    OUT.write_text(json.dumps(R61._clean(res), indent=1), encoding="utf-8")
    log(f"\n  -> {OUT}   ({res['timing']['wall_s']}s)")
    return 0


# --------------------------------------------------------------------------------------------
# self-test: the refusal, the rotation semantics on a synthetic span, the N3 leg-count audit
# --------------------------------------------------------------------------------------------
def selftest() -> int:
    print("D574 SELF-TEST -- no fixture read\n")
    rc = run(False, log=lambda *a: None)
    if rc != 2:
        raise AssertionError("the runner did not refuse without --principals-word")
    print("  [1] the runner REFUSES without --principals-word")
    rng = np.random.default_rng(574); n, T = 5, 900
    span = np.ones((n, T), dtype=bool); span[2, :100] = False
    sign = rng.choice([-1.0, 0.0, 1.0], size=(n, T)); rs = 0.01 * rng.standard_normal((n, T)); wF = np.arange(T) >= 700
    live_idx = [np.flatnonzero(span[i]) for i in range(n)]
    for k in (1, 7, 63, 250, 333):
        p = R55.rotate_signs(sign, live_idx, k)
        if not np.array_equal(R55.book_return(p, rs)[wF], R55.book_return_loop(p[:, wF], rs[:, wF])):
            raise AssertionError("exactness")
        tF = 705; pos_t = int(np.flatnonzero(live_idx[2] == tF)[0])
        if p[2, tF] != sign[2, live_idx[2][pos_t - k]]:
            raise AssertionError("rotation semantics")
    print("  [2] full-span rotation scored on the forward window is bit-identical to the loop; the rotated sign at t is the sign from k sessions earlier within the root's span")
    member = np.zeros((n, 12), dtype=int); member[0, :] = 1; member[1, :] = -1                  # one long, one short, three flat at every month-end
    elig = np.ones((n, 12), dtype=bool); dr = n3_draw(member, elig, rng); audit_draw_leg_counts(member, dr, elig)
    bad = dr.copy(); k0 = 0; free = np.flatnonzero((bad[:, k0] == 0) & elig[:, k0]); bad[free[0], k0] = 1
    R61._expect_raise(lambda: audit_draw_leg_counts(member, bad, elig), "N3 audit on an extra long")
    print("  [3] a name-randomised draw keeps every leg size and the audit RAISES on a draw with an extra long")
    print("\nSELF-TEST PASSED"); return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--run", action="store_true"); ap.add_argument("--principals-word", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else run(a.principals_word))
