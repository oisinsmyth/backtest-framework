"""D673 Stage 0 -- join the day's move once it has formed, and hold to the close.

    python scripts/stage0_d673_formed_move.py --selftest
    python scripts/stage0_d673_formed_move.py --run          # -> data/stage0_d673_formed_move.json

PRE-REGISTRATION: docs/decisions/D673-STAGE-0-DESIGN-join-the-formed-move-after-ten.md (d6aade7), committed before
this file existed. Evidence YM, RTY, ES; development NQ. In sample only; every row at or after 2025-03-01 is dropped
at load and a guard raises if one survives.

Rule: at the first of the 10:59 / 11:59 / 12:59 / 13:59 closes where sign(C - prior close) == sign(C - today's open)
!= 0, enter in that sign at the next minute's open; one trade a session; exit at the 15:59 close.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

from stage0_d669_macd_mechanism import (  # noqa: E402
    dist, drift_carry, kurt, max_dd, permute_null, qdist, sharpe, skew, sortino, strata_labels)
from stage0_d670_overnight_direction import (  # noqa: E402
    CIRCUIT, ERA_0DTE, FIXDIR, HI, LO, VAULT, GateError, arm_daily, corr_on, gross_bp, guard_window, holm, k8_daily,
    mean_t, micro_spec, roll_guard, sharpe_tpy, sign_audit, sortino_tpy)

OUT = REPO / "data" / "stage0_d673_formed_move.json"
PREREG = "d6aade7"
EVIDENCE, DEVELOPMENT = ("YM", "RTY", "ES"), ("NQ",)
ROOTS = EVIDENCE + DEVELOPMENT
FAMILY_ALPHA = 0.025
N1_DRAWS, N2_DRAWS, SEED = 10_000, 2_000, 673
EP_BURN, K_COST = 250, 2.0
M = lambda hh, mm: (hh - 9) * 60 + mm - 30                        # noqa: E731  minute index, 09:30 = 0
M0930, M0959, M1000, M1359, M1459, M1500, M1559 = M(9, 30), M(9, 59), M(10, 0), M(13, 59), M(14, 59), M(15, 0), M(15, 59)
DECISIONS = (M(10, 59), M(11, 59), M(12, 59), M(13, 59))
DECISIONS_V3 = (M0959,) + DECISIONS
ENTRY_LABEL = {M(10, 59): "11:00", M(11, 59): "12:00", M(12, 59): "13:00", M(13, 59): "14:00", M0959: "10:00"}
FILL_WINDOW = 5                                                   # a missing entry bar fills at the next open within 5 min
ND = NormalDist()


def P(*a, **k):
    print(*a, **k, flush=True)


# ------------------------------------------------------------------ data
def load_grid(root: str) -> dict:
    bars = pd.read_csv(FIXDIR / f"fut_{root}_rth_1m.csv.gz", encoding="utf-8",
                       dtype={"day": str, "hhmm": str, "contract": str})
    bars = bars[bars["day"] < VAULT]
    guard_window(bars["day"])
    bars = bars[bars["day"] >= "2015-12-01"]
    mi = bars["hhmm"].str[:2].astype(int) * 60 + bars["hhmm"].str[3:].astype(int) - (9 * 60 + 30)
    bars = bars.assign(m=mi)[(mi >= 0) & (mi <= M1559)]
    days = np.array(sorted(bars["day"].unique()))
    di = np.searchsorted(days, bars["day"].to_numpy())
    O = np.full((len(days), M1559 + 1), np.nan)
    C = np.full((len(days), M1559 + 1), np.nan)
    O[di, bars["m"].to_numpy()] = bars["open"].to_numpy(float)
    C[di, bars["m"].to_numpy()] = bars["close"].to_numpy(float)
    con = bars.groupby("day")["contract"].agg(lambda s: s.iloc[0]).reindex(days).to_numpy()
    prev_c = np.concatenate([[np.nan], C[:-1, M1559]])
    prev_con = np.concatenate([[None], con[:-1]])
    w = (days >= LO[root]) & (days <= HI)
    roll = con != prev_con
    cb = np.isin(days, list(CIRCUIT))
    miss = np.isnan(O[:, M0930]) | np.isnan(prev_c) | np.isnan(C[:, M1559])
    use = w & ~roll & ~cb & ~miss
    drops = {"sessions_in_window": int(w.sum()), "roll": int((w & roll).sum()), "circuit": int((w & cb & ~roll).sum()),
             "missing": int((w & miss & ~roll & ~cb).sum())}
    return {"days": days[use], "contract": con[use], "prev_contract": prev_con[use], "O": O[use], "C": C[use],
            "prev_c": prev_c[use], "drops": drops}


def entry_open(O: np.ndarray, i: np.ndarray, m: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The open of minute m, or of the first bar within FILL_WINDOW minutes after it."""
    px = np.full(len(i), np.nan)
    em = np.full(len(i), -1)
    for k in range(FILL_WINDOW + 1):
        mm = np.minimum(m + k, M1559)
        v = O[i, mm]
        take = np.isnan(px) & np.isfinite(v) & (m + k <= M1559)
        px[take], em[take] = v[take], mm[take]
    return px, em


def confirm_at(C: np.ndarray, o0930: np.ndarray, prev_c: np.ndarray, dm: int) -> np.ndarray:
    """s_T: reads only the close of decision bar dm. NaN bar -> 0 (the rule waits)."""
    c = C[:, dm]
    a, b = np.sign(c - prev_c), np.sign(c - o0930)
    return np.where(np.isfinite(c) & (a == b) & (a != 0), a, 0.0)


def first_entry(g: dict, decisions=DECISIONS) -> pd.DataFrame:
    O, C = g["O"], g["C"]
    n = len(g["days"])
    D = np.zeros(n)
    dm = np.full(n, -1)
    for d_ in decisions:
        s = confirm_at(C, O[:, M0930], g["prev_c"], d_)
        new = (D == 0) & (s != 0)
        D[new], dm[new] = s[new], d_
    i = np.flatnonzero(D != 0)
    px, em = entry_open(O, i, dm[i] + 1)
    ok = np.isfinite(px)
    i, px, em = i[ok], px[ok], em[ok]
    t = pd.DataFrame({"i": i, "day": g["days"][i], "D": D[i], "decision_m": dm[i], "entry_m": em, "entry_px": px,
                      "exit_px": C[i, M1559], "contract": g["contract"][i], "prev_contract": g["prev_contract"][i]})
    t["entry_label"] = t["decision_m"].map(ENTRY_LABEL)
    t.attrs["no_fill"] = int((~ok).sum())
    return t


# ------------------------------------------------------------------ audits
def causal_audit(g: dict, confirm=confirm_at) -> None:
    """s_T must not move when every price after the decision bar moves."""
    for d_ in DECISIONS:
        base = confirm(g["C"], g["O"][:, M0930], g["prev_c"], d_)
        C2 = g["C"].copy()
        C2[:, d_ + 1:] *= 1.07
        if not np.array_equal(confirm(C2, g["O"][:, M0930], g["prev_c"], d_), base):
            raise GateError(f"[CAUSAL] the confirmation at minute {d_} reads a later bar")


def entry_audit(t: pd.DataFrame, O: np.ndarray) -> None:
    if not (t["entry_m"] > t["decision_m"]).all():
        raise GateError("[ENTRY] a trade entered at or before its decision bar")
    if not np.array_equal(O[t["i"].to_numpy(), t["entry_m"].to_numpy()], t["entry_px"].to_numpy()):
        raise GateError("[ENTRY] the entry price is not the open of the entry minute")
    if t["i"].duplicated().any():
        raise GateError("[ENTRY] two trades in one session")


def ep_forecast(g: np.ndarray, burn: int = EP_BURN) -> np.ndarray:
    """The expanding mean gross of EARLIER trades; NaN until `burn` exist."""
    cs = np.cumsum(g) - g
    k = np.arange(len(g))
    f = np.full(len(g), np.nan)
    ok = k >= burn
    f[ok] = cs[ok] / k[ok]
    return f


def ep_audit(g: np.ndarray, f: np.ndarray, idx, include_own: bool = False) -> None:
    for j in idx:
        ref = g[: j + 1].mean() if include_own else g[:j].mean()
        if not np.isclose(ref, f[j], rtol=1e-12, atol=1e-12):
            raise GateError(f"[EP] forecast {j} includes an outcome it should not")


# ------------------------------------------------------------------ blocks
def book(t: pd.DataFrame, g: np.ndarray, cost_bp: np.ndarray, usd_net: np.ndarray, n_sess: int, years: float) -> dict:
    if len(g) < 3:
        return {"trades": int(len(g))}
    net = g - cost_bp
    tpy = len(g) / years
    mg, tg = mean_t(g)
    mn, tn = mean_t(net)
    return {"trades": int(len(g)), "trades_per_year": tpy, "share_of_sessions": len(g) / n_sess,
            "hours_held_mean": float(((M1559 + 1 - t["entry_m"].to_numpy()) / 60).mean()),
            "gross_mean_bp": mg, "gross_t_nw": tg, "net_mean_bp": mn, "net_t_nw": tn,
            "gross_sharpe_ann": sharpe_tpy(g, tpy), "gross_sortino_ann": sortino_tpy(g, tpy),
            "net_sharpe_ann": sharpe_tpy(net, tpy), "net_sortino_ann": sortino_tpy(net, tpy),
            "sigma_bp": float(np.std(g, ddof=1)), "max_dd_usd": max_dd(usd_net), "net_total_usd": float(usd_net.sum()),
            "mean_cost_bp": float(cost_bp.mean()), "gross_over_cost": mg / float(cost_bp.mean()),
            "breakeven_bp_per_side": mg / 2, "dist_gross_bp": dist(g), "dist_net_bp": dist(net)}


def winners(t: pd.DataFrame, g: np.ndarray, usd: np.ndarray) -> dict:
    yr = t["day"].str[:4].to_numpy()
    lng = t["D"].to_numpy() > 0
    pre = (t["day"] < ERA_0DTE).to_numpy()
    srt = np.sort(usd)[::-1]
    j = int(np.argmax(g))
    return {"by_year": {y: {"trades": int((yr == y).sum()), "gross_mean_bp": float(g[yr == y].mean()),
                            "net_usd": float(usd[yr == y].sum())} for y in sorted(set(yr))},
            "long": {"trades": int(lng.sum()), "gross_mean_bp": float(g[lng].mean()), "hit": float((g[lng] > 0).mean())},
            "short": {"trades": int((~lng).sum()), "gross_mean_bp": float(g[~lng].mean()), "hit": float((g[~lng] > 0).mean())},
            "by_entry": {lab: {"trades": int((t["entry_label"] == lab).sum()),
                               "gross_mean_bp": float(g[(t["entry_label"] == lab).to_numpy()].mean())}
                         for lab in sorted(t["entry_label"].unique())},
            "pre_0dte_gross_mean_bp": float(g[pre].mean()), "post_0dte_gross_mean_bp": float(g[~pre].mean()),
            "sessions_to_half_net": int(np.searchsorted(np.cumsum(srt), 0.5 * usd.sum()) + 1) if usd.sum() > 0 else None,
            "top_trade": {"day": str(t["day"].iloc[j]), "direction": int(t["D"].iloc[j]), "gross_bp": float(g[j])}}


def economics(t: pd.DataFrame, exit_px: np.ndarray, spec: dict):
    g = gross_bp(t["D"], t["entry_px"], exit_px)
    cost_bp = spec["cost_rt_usd"] / (t["entry_px"].to_numpy() * spec["usd_per_point"]) * 1e4
    usd_g = t["D"].to_numpy() * (exit_px - t["entry_px"].to_numpy()) * spec["usd_per_point"]
    return g, cost_bp, usd_g, usd_g - spec["cost_rt_usd"]


# ------------------------------------------------------------------ one root
def root_study(root: str) -> dict:
    t0 = time.time()
    spec = micro_spec(root)
    g_ = load_grid(root)
    n_sess = len(g_["days"])
    guard_window(g_["days"])
    causal_audit(g_)
    sign_audit()
    t = first_entry(g_)
    roll_guard(t)
    entry_audit(t, g_["O"])
    years = (pd.Timestamp(HI) - pd.Timestamp(LO[root])).days / 365.25
    g, cost_bp, usd_g, usd_net = economics(t, t["exit_px"].to_numpy(), spec)
    sigma = float(np.std(g, ddof=1))
    z = ND.inv_cdf(1 - FAMILY_ALPHA / len(EVIDENCE)) + ND.inv_cdf(0.8)
    mde = z * sigma / math.sqrt(len(g))
    out = {"root": root, "role": "evidence" if root in EVIDENCE else "development", "micro": spec,
           "window": [LO[root], HI], "drops": g_["drops"], "sessions_used": n_sess, "trades": int(len(t)),
           "no_fill_within_5_min": t.attrs["no_fill"], "mde_bp_80pct_power": mde}
    P(f"[{root}] {n_sess} sessions, {len(t)} trades ({len(t) / n_sess:.0%}); sigma {sigma:.1f} bp -> MDE {mde:.2f} bp "
      f"(printed before any mean)")

    # ---- N1 and N2
    D = t["D"].to_numpy(float)
    move = gross_bp(np.ones(len(t)), t["entry_px"], t["exit_px"])
    grp = strata_labels(t["day"].to_numpy())["week"]
    rng = np.random.default_rng(SEED + ROOTS.index(root))
    dr = permute_null(D, move, grp, N1_DRAWS, rng, check=True) / len(D)
    carry = drift_carry(D, move, grp) / len(D)
    n1 = qdist(dr, rng, float(g.mean()))
    if abs(n1["mean"] - carry) > 3 * n1["sd"] / math.sqrt(N1_DRAWS):
        raise GateError(f"[PERM] {root}: draw mean {n1['mean']:.3f} vs carry {carry:.3f}")
    n1["drift_carry_exact"] = carry
    # N2: clock-matched random entries on every session
    O, C = g_["O"], g_["C"]
    allI = np.arange(n_sess)
    G_long = np.full((n_sess, len(DECISIONS)), np.nan)
    for k, d_ in enumerate(DECISIONS):
        px, _ = entry_open(O, allI, np.full(n_sess, d_ + 1))
        G_long[:, k] = gross_bp(np.ones(n_sess), px, C[:, M1559])
    p_k = np.array([(t["decision_m"] == d_).mean() for d_ in DECISIONS])
    p_long = float((D > 0).mean())
    rng2 = np.random.default_rng(SEED + 10 + ROOTS.index(root))
    n2d = np.empty(N2_DRAWS)
    for b in range(N2_DRAWS):
        si = rng2.integers(0, n_sess, len(t))
        ki = rng2.choice(len(DECISIONS), len(t), p=p_k)
        sd = np.where(rng2.random(len(t)) < p_long, 1.0, -1.0)
        n2d[b] = float(np.nanmean(sd * G_long[si, ki]))
    n2 = qdist(n2d, rng2, float(g.mean()))
    mg, tg = mean_t(g)
    ex2020 = ~t["day"].between("2020-02-01", "2020-04-30").to_numpy()
    out["primary"] = {"book": book(t, g, cost_bp, usd_net, n_sess, years), "one_sided_p": 1 - ND.cdf(tg),
                      "N1_week": n1, "N2_clock_random": n2, "gross_mean_ex_feb_apr_2020": float(g[ex2020].mean()),
                      "net_mean_plus_1_tick_each_fill": float((g - cost_bp - 2 * spec["tick_points"]
                                                               / t["entry_px"].to_numpy() * 1e4).mean()),
                      "winners": winners(t, g, usd_net)}
    out["primary"]["gate1_parts"] = {
        "above_n1_p95_by_2se": bool(mg > n1["p95"] + 2 * n1["p95_boot_se"]),
        "above_n2_p95_by_2se": bool(mg > n2["p95"] + 2 * n2["p95_boot_se"]),
        "unresolved": bool(abs(mg - n1["p95"]) <= 2 * n1["p95_boot_se"] or abs(mg - n2["p95"]) <= 2 * n2["p95_boot_se"]),
        "positive_ex_2020": bool(g[ex2020].mean() > 0)}
    P(f"[{root}] primary gross {mg:+.2f} bp (t {tg:+.2f}), net {(g - cost_bp).mean():+.2f}; N1 p50 {n1['p50']:+.2f} p95 "
      f"{n1['p95']:+.2f}; N2 p50 {n2['p50']:+.2f} p95 {n2['p95']:+.2f}; entries "
      f"{ {k: v['trades'] for k, v in out['primary']['winners']['by_entry'].items()} }")

    # ---- EP filter
    f = ep_forecast(g)
    fi = np.flatnonzero(np.isfinite(f))
    ep_audit(g, f, fi[np.linspace(0, len(fi) - 1, 10).astype(int)] if len(fi) else [])
    take = np.isfinite(f) & (f >= K_COST * cost_bp)
    out["ep_filtered"] = {"pass_rate_of_forecast": float(take.sum() / max(1, len(fi))),
                          "book": book(t[take], g[take], cost_bp[take], usd_net[take], n_sess, years)}

    # ---- variants
    have = np.isfinite(C[t["i"], M1359]) & np.isfinite(C[t["i"], M1459])
    cut = have & (t["D"].to_numpy() * (C[t["i"], M1459] - C[t["i"], M1359]) < 0) & (t["entry_m"].to_numpy() < M1500)
    o15, _ = entry_open(O, t["i"].to_numpy(), np.full(len(t), M1500))
    x1 = np.where(cut & np.isfinite(o15), o15, t["exit_px"].to_numpy())
    g1, c1, _, u1 = economics(t, x1, spec)
    d1m, d1t = mean_t(g1 - g)
    s0959 = confirm_at(C, O[:, M0930], g_["prev_c"], M0959)
    v2 = s0959[t["i"].to_numpy()] == 0
    t3 = first_entry(g_, DECISIONS_V3)
    g3, c3, _, u3 = economics(t3, t3["exit_px"].to_numpy(), spec)
    out["variants"] = {
        "V1_1500_cut": {"exits": int((cut & np.isfinite(o15)).sum()), "paired_diff_mean_bp": d1m, "paired_diff_t_nw": d1t,
                        "book": book(t, g1, c1, u1, n_sess, years)},
        "V2_arm_like_0959_unconfirmed": {"book": book(t[v2], g[v2], cost_bp[v2], usd_net[v2], n_sess, years),
                                         "rest_gross_mean_bp": float(g[~v2].mean()) if (~v2).any() else float("nan")},
        "V3_from_1000": {"book": book(t3, g3, c3, u3, n_sess, years)}}
    P(f"[{root}] V1 cut diff {d1m:+.2f} (t {d1t:+.2f}); V2 {out['variants']['V2_arm_like_0959_unconfirmed']['book'].get('gross_mean_bp', float('nan')):+.2f} "
      f"vs rest {out['variants']['V2_arm_like_0959_unconfirmed']['rest_gross_mean_bp']:+.2f}; V3 "
      f"{out['variants']['V3_from_1000']['book']['gross_mean_bp']:+.2f}")

    # ---- daily series for the component line
    days = pd.Index(g_["days"])
    daily = pd.Series(0.0, index=days)
    daily.loc[t["day"]] = usd_net
    dgross = pd.Series(0.0, index=days)
    dgross.loc[t["day"]] = usd_g
    d670 = np.sign(C[:, M0959] - g_["prev_c"])
    ok670 = np.isfinite(O[:, M1000]) & np.isfinite(C[:, M0959]) & (d670 != 0)
    r670 = pd.Series(np.where(ok670, d670 * (C[:, M1559] - O[:, M1000]) * spec["usd_per_point"] - spec["cost_rt_usd"], 0.0),
                     index=days)
    filt = pd.Series(0.0, index=days)
    filt.loc[t["day"][take]] = usd_net[take]
    out["component"] = {"net_sharpe_daily_usd": sharpe(daily), "gross_sharpe_daily_usd": sharpe(dgross),
                        "net_sortino_daily_usd": sortino(daily), "hit_rate": float((usd_net > 0).mean()),
                        "skew_daily_net": skew(daily), "kurtosis_daily_net": kurt(daily),
                        "ep_filtered_net_sharpe_daily_usd": sharpe(filt) if take.sum() > 2 else float("nan"),
                        "rho_d670_rule_same_root": float(daily.corr(r670))}
    out["wall_s"] = round(time.time() - t0, 1)
    return {"out": out, "daily": daily}


# ------------------------------------------------------------------ run
def run() -> dict:
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=len(ROOTS)) as ex:
        res = dict(zip(ROOTS, ex.map(root_study, ROOTS)))
    k8, arm = k8_daily(), arm_daily()
    out = {"pre_registration": PREREG, "vault_from": VAULT, "roots": {r: res[r]["out"] for r in ROOTS}}
    for r in ROOTS:
        c = out["roots"][r]["component"]
        c["rho_K8"] = corr_on(res[r]["daily"], k8)
        c["rho_macd_arm"] = corr_on(res[r]["daily"], arm)
        c["rho_other_roots"] = {o: corr_on(res[r]["daily"], res[o]["daily"])["rho"] for o in ROOTS if o != r}
        c["missing"] = "the other session's plain-break book (unmerged)"
    R = out["roots"]
    g1_p = {r: R[r]["primary"]["one_sided_p"] for r in EVIDENCE}
    h1 = holm(g1_p, FAMILY_ALPHA)
    gate1 = {r: bool(h1.get(r, False) and all(R[r]["primary"]["gate1_parts"][k] for k in
                                               ("above_n1_p95_by_2se", "above_n2_p95_by_2se", "positive_ex_2020")))
             for r in EVIDENCE}
    passed = [r for r in EVIDENCE if gate1[r]]
    h2 = holm({r: 1 - ND.cdf(R[r]["primary"]["book"]["net_t_nw"]) for r in passed})
    gate2 = {r: bool(h2.get(r, False) and R[r]["primary"]["net_mean_plus_1_tick_each_fill"] > 0) for r in passed}
    verdict = {r: ("SUPPORTED" if gate2.get(r) else "MECHANISM ONLY") if gate1[r] else "NOT SUPPORTED" for r in EVIDENCE}
    out["gates"] = {"gate1": gate1, "gate1_one_sided_p": g1_p, "gate1_holm_family_alpha": FAMILY_ALPHA,
                    "gate2": gate2, "verdict": verdict}
    ent = {r: R[r]["primary"]["winners"]["by_entry"] for r in ROOTS}
    v1_better = sum(R[r]["variants"]["V1_1500_cut"]["paired_diff_mean_bp"] > 0 for r in ROOTS)
    nq = R["NQ"]
    out["predictions"] = {
        "1_NQ_positive_and_clears_N1": bool(nq["primary"]["book"]["gross_mean_bp"] > 0 and nq["primary"]["gate1_parts"]["above_n1_p95_by_2se"]),
        "2_at_most_one_evidence_root_passes": bool(sum(gate1.values()) <= 1),
        "3_YM_fails_gate1": bool(not gate1["YM"]),
        "4_over_60pct_enter_at_1100": bool(all(ent[r].get("11:00", {"trades": 0})["trades"] / R[r]["trades"] > 0.6 for r in ROOTS)),
        "5_V1_beats_primary_on_3_of_4": bool(v1_better >= 3),
        "6_NQ_V2_beats_rest": bool(nq["variants"]["V2_arm_like_0959_unconfirmed"]["book"].get("gross_mean_bp", -1e9)
                                   > nq["variants"]["V2_arm_like_0959_unconfirmed"]["rest_gross_mean_bp"]),
        "7_ES_gross_below_2bp": bool(R["ES"]["primary"]["book"]["gross_mean_bp"] < 2)}
    out["max_drawdown_convention"] = {"sign": "positive", "note": "max_dd_usd is a POSITIVE drawdown in US DOLLARS on the "
                                      "cumulative-sum P&L at one micro (peak minus trough), not a fraction of peak.",
                                      "record": "D542"}
    out["wall_min"] = round((time.time() - t0) / 60, 2)
    OUT.write_text(json.dumps(out, indent=1, default=_json), encoding="utf-8")
    P(f"gates {out['gates']}")
    P(f"predictions {out['predictions']}")
    P(f"wrote {OUT.relative_to(REPO)} in {out['wall_min']} min")
    return out


def _json(o):
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    return float(o)


# ------------------------------------------------------------------ self-test
def _raises(fn, tag, fails):
    try:
        fn()
    except GateError:
        return
    fails.append(f"{tag}: a deliberately broken input did not raise")


def selftest() -> int:
    fails: list[str] = []
    g_ = load_grid("YM")
    guard_window(g_["days"])
    _raises(lambda: guard_window(np.array(["2025-02-28", "2025-03-03"])), "vault guard", fails)
    causal_audit(g_)
    _raises(lambda: causal_audit(g_, lambda C, o, p, d: confirm_at(C, o, p, d + 1)), "causality canary", fails)
    t = first_entry(g_)
    entry_audit(t, g_["O"])
    bad = t.copy()
    bad["entry_px"] = g_["C"][bad["i"].to_numpy(), bad["decision_m"].to_numpy()]
    _raises(lambda: entry_audit(bad, g_["O"]), "entry-at-decision-close canary", fails)
    _raises(lambda: entry_audit(pd.concat([t, t.iloc[:1]]), g_["O"]), "second-trade canary", fails)
    roll_guard(t)
    rolled = t.copy()
    rolled.loc[rolled.index[3], "prev_contract"] = "XXX"
    _raises(lambda: roll_guard(rolled), "roll canary", fails)
    sign_audit()
    _raises(lambda: sign_audit(lambda D, o, c: D * (o - c)), "sign audit", fails)
    move = gross_bp(np.ones(len(t)), t["entry_px"], t["exit_px"])
    D = t["D"].to_numpy(float)
    grp = strata_labels(t["day"].to_numpy())["week"]
    rng = np.random.default_rng(4)
    dr = permute_null(D, move, grp, 400, rng, check=True)
    if abs(dr.mean() - drift_carry(D, move, grp)) > 3 * dr.std(ddof=1) / math.sqrt(400):
        fails.append("permutation mean is not the exact carry")
    orc = np.sign(move)
    if not float(orc @ move) > np.quantile(permute_null(orc, move, grp, 400, rng), 0.95):
        fails.append("oracle direction does not beat the null")
    rnd = np.where(rng.random(len(D)) < 0.5, 1.0, -1.0)
    pct = (permute_null(rnd, move, grp, 400, rng) < float(rnd @ move)).mean()
    if not 0.02 < pct < 0.98:
        fails.append(f"random direction at the {pct:.3f} quantile")
    gg = np.random.default_rng(6).standard_normal(600)
    f = ep_forecast(gg)
    ep_audit(gg, f, [250, 400, 599])
    _raises(lambda: ep_audit(gg, f, [250, 400, 599], include_own=True), "EP canary", fails)
    P(f"YM: {len(g_['days'])} sessions, {len(t)} trades, drops {g_['drops']}, no fill {t.attrs['no_fill']}")
    P("SELFTEST " + ("PASS" if not fails else "FAIL"))
    for x in fails:
        P("  -", x)
    return 0 if not fails else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.run:
        run()
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
