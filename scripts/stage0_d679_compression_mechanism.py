"""D679: is the compression break's mechanism real? D672's compression tier on HO, RB, BZ, HG and PL (primary) and, per
D679-A1, on CL, NG, GC and SI (family 2), judged on gross.
Spec: docs/decisions/D679-PRE-REG-the-compression-break-mechanism-on-ho-rb-bz-hg-pl.md (633a7ab8; A1 7fb7e196).
Primary shares D678's fixture, gates, costs (single count, full size), R2 and exit; family 2 uses D676's fixture
(gated 0a6c033f) and D676's R2. In-sample to 2025-02-28; the vault is never read.

    uv run --with pyarrow python scripts/stage0_d679_compression_mechanism.py --selftest
    uv run --with pyarrow python scripts/stage0_d679_compression_mechanism.py --run     # once
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d678_gap_open as G  # noqa: E402

B, M, C = G.B, G.M, G.C
OUT = REPO / "data" / "stage0_d679_compression_mechanism.json"
ROOTS, COVID, FIRST, RESERVED_FROM = G.ROOTS, G.COVID, G.FIRST, G.RESERVED_FROM
ROOTS2 = ("CL", "NG", "GC", "SI")
SESS = B.SESS  # D676's CL/NG/GC/SI plus D678's five (D678 updates D676's dict on import)
N_PLACEBO, SEED, MIN_TRADES, EDGE = 1000, 679, 100, 21


class D679Error(RuntimeError):
    pass


def costs(roots: tuple[str, ...]) -> dict[str, dict[str, float]]:
    """Full size, single count: $6 + the measured d507_exec crossing (D678 s.2; D679-A1)."""
    j = json.loads((REPO / "data" / "futures_costs.json").read_text(encoding="utf-8"))
    out = {}
    for r in roots:
        f = j["roots"][r]["full"]
        com = float(f["commission_rt_usd"]["value"])
        if com != 6.0:
            raise D679Error(f"{r}: commission {com}")
        x = float(f["crossing_ticks_rt"]["d507_exec"]["value"])
        out[r] = {"symbol": f["symbol"], "line": "d507_exec", "tick": float(f["tick_points"]), "tick_usd": float(f["tick_usd"]),
                  "usd_per_point": float(f["usd_per_point"]), "crossing_ticks_rt": x, "cost_usd": com + x * float(f["tick_usd"])}
    return out


def frames2(data_root: Path) -> tuple[dict, dict]:
    """Family 2 on D676's fixture: D676's day frame, ATR, same-contract levels and R2 (flags + its audit)."""
    g = B.load_fixture(B.FIXTURE)
    cal_all = pd.read_csv(data_root / "fixtures" / "cme_session_calendar.csv.gz", encoding="utf-8", dtype={"day": str})
    fr, bars_all = {}, {}
    for r in ROOTS2:
        d, bars = B.day_frame(g, r)
        d = d[d["usable"]].copy()
        d["atr20"] = B.atr_prior(d)
        B.atr_audit(d, d["atr20"], list(range(0, len(d), max(1, len(d) // 30))))
        same = d["contract"] == d["contract"].shift(1)
        d["prior_high"] = d["high"].shift(1).where(same)
        d["prior_low"] = d["low"].shift(1).where(same)
        cal = cal_all[cal_all["root"] == r].set_index("day")
        fl = B.flags(r, d, cal)
        B.delivery_audit(fl, d, r, cal)
        d["R2"] = fl["R2_delivery"].astype(bool)
        d["eligible"] = (d.index >= FIRST) & np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)
        fr[r], bars_all[r] = d, bars
    return fr, bars_all


def features(d: pd.DataFrame, r: str) -> pd.DataFrame:
    """rv5 and the overnight two-way range as D671's session_features defines them; D671's walk-forward tiers."""
    if (d["on_last_m"].dropna() >= SESS[r]["open"]).any():
        raise D679Error(f"overnight: {r} reads a bar at or after the open")
    A = d["atr20"].astype(float)
    R = (d["high"] - d["low"]) / A
    f = pd.DataFrame(index=d.index)
    f["rv5"] = R.shift(1).rolling(5, min_periods=5).mean()
    f["on_range"] = (d["on_high"] - d["on_low"] - (d["open"] - d["close"].shift(1)).abs()) / A
    f["p_rv"] = C.tiers(f["rv5"].to_numpy(float))
    f["p_on"] = C.tiers(f["on_range"].to_numpy(float))
    comp = ((f["p_rv"] + f["p_on"]) / 2).to_numpy(float)
    f["ctier"] = C.tiers(comp)
    C.tier_audit(f["ctier"].to_numpy(float), comp, list(range(0, len(comp), max(1, len(comp) // 12))))
    C.tier_audit(f["p_on"].to_numpy(float), f["on_range"].to_numpy(float), list(range(0, len(f), max(1, len(f) // 12))))
    return f


def root_job(args: tuple) -> dict[str, Any]:
    r, d, bars, cost = args
    s = SESS[r]
    rows = []
    for sess, rec in d.iterrows():
        bb = bars.get(sess)
        if bb is None or not rec["eligible"] or rec["R2"]:
            continue
        B.flat_audit(bb, s["flat"])
        Lh, Ll, A = float(rec["prior_high"]), float(rec["prior_low"]), float(rec["atr20"])
        t = B.break_scan(bb, Lh, Ll, A, s["open"], s["last"], 0.0)
        if t is None:
            continue
        px, why, k = G.one(bb, t["i"], t["D"], t["entry"], t["L"], A, s["flat"])
        rows.append({"session": sess, "D": t["D"], "entry": t["entry"], "A_bp": A / t["entry"] * 1e4,
                     "gross": t["D"] * (px / t["entry"] - 1) * 1e4, "why": why,
                     "gap_open": bool(t["open_fill"] and int(bb["m"][t["i"]]) == s["open"]),
                     "cost_bp": cost["cost_usd"] / cost["usd_per_point"] / t["entry"] * 1e4, "tick_bp": cost["tick"] / t["entry"] * 1e4})
    return {"root": r, "rows": rows}


def delta(pct: np.ndarray, tier: np.ndarray, ok: np.ndarray) -> float:
    c1 = ok & (tier < 1 / 3)
    rest = ok & (tier >= 1 / 3)
    return float(pct[c1].mean() - pct[rest].mean())


def rot_check(actual: float, k0: float) -> None:
    if not np.isclose(actual, k0, rtol=0, atol=1e-12):
        raise D679Error(f"rotation: offset 0 gives {k0}, not the actual {actual}")


def family(roots: tuple[str, ...], fr: dict, bars_all: dict, cst: dict, R: Any, rng: np.random.Generator,
           k8: pd.Series) -> dict[str, Any]:
    feats = {r: features(fr[r], r) for r in roots}
    with ProcessPoolExecutor(max_workers=len(roots)) as pool:
        got = {o["root"]: o for o in pool.map(root_job, [(r, fr[r], bars_all[r], cst[r]) for r in roots])}
    out: dict[str, Any] = {"roots": {}}
    tr, cs, pos, okp = {}, {}, {}, {}
    for r in roots:
        t_ = pd.DataFrame(got[r]["rows"]).sort_values("session").reset_index(drop=True)
        f = feats[r]
        for c_ in ("ctier", "p_rv", "p_on"):
            t_[c_] = f[c_].reindex(t_["session"]).to_numpy(float)
        t_ = t_[np.isfinite(t_["ctier"])].reset_index(drop=True)
        t_["pct"] = t_["gross"] / t_["A_bp"] * 100
        tr[r] = t_
        s_ = f["ctier"].dropna()
        cs[r] = s_.to_numpy()
        pos[r] = pd.Series(np.arange(len(s_)), index=s_.index).reindex(t_["session"]).to_numpy()
        okp[r] = np.isfinite(pos[r])
    # ------------------------------------------------ Gate 1(a): the enumerated common-offset rotation
    act = {r: delta(tr[r]["pct"].to_numpy(float), tr[r]["ctier"].to_numpy(float), np.ones(len(tr[r]), bool)) for r in roots}
    nmin = min(len(v) for v in cs.values())
    offs = np.arange(EDGE, nmin - EDGE)
    rot = {r: np.empty(len(offs)) for r in roots}
    for r in roots:
        pct = tr[r]["pct"].to_numpy(float)
        p = pos[r][okp[r]].astype(int)
        rot_check(act[r], delta(pct[okp[r]], np.roll(cs[r], 0)[p], np.ones(len(p), bool)))
        for j, k in enumerate(offs):
            rot[r][j] = delta(pct[okp[r]], np.roll(cs[r], k)[p], np.ones(len(p), bool))
    fam_act = float(np.mean(list(act.values())))
    fam_rot = np.mean(np.vstack([rot[r] for r in roots]), axis=0)
    g1a = {"delta_pct_A": fam_act, "per_root": act, "offsets": int(len(offs)), "p50": float(np.median(fam_rot)),
           "p95": float(np.quantile(fam_rot, 0.95)), "rank": float((fam_rot < fam_act).mean())}
    c1s = pd.concat([pd.Series(tr[r].loc[tr[r]["ctier"] < 1 / 3, "pct"].to_numpy(float), index=tr[r].loc[tr[r]["ctier"] < 1 / 3, "session"].to_numpy())
                     for r in roots]).groupby(level=0).mean().sort_index()
    b_ = G.mt(c1s.to_numpy(), R)
    exd = {r: delta(tr[r]["pct"].to_numpy(float), tr[r]["ctier"].to_numpy(float), ~tr[r]["session"].between(*COVID).to_numpy()) for r in roots}
    g1 = {"a_rotation": g1a, "b_c1_gross_date_series": b_, "b_p_one_sided": float(stats.norm.sf(b_["t"])),
          "c_delta_ex_covid": float(np.mean(list(exd.values())))}
    g1["checks"] = {"a_above_rotation_p95": bool(fam_act > g1a["p95"]), "b_t_p_below_0.05": bool(g1["b_p_one_sided"] < 0.05),
                    "c_positive_ex_covid": bool(g1["c_delta_ex_covid"] > 0)}
    g1["MECHANISM"] = bool(all(g1["checks"].values()))
    out["gate1_family"] = g1
    exc = {r: float(act[r] - np.median(rot[r])) for r in roots}
    kpos = int(sum(v > 0 for v in exc.values()))
    out["mechanism_reading"] = {"excess_over_own_rotation_p50_pct_A": exc,
                                "own_rotation": {r: {"p50": float(np.median(rot[r])), "p95": float(np.quantile(rot[r], 0.95)),
                                                     "rank": float((rot[r] < act[r]).mean())} for r in roots},
                                "roots_with_excess_positive": kpos, "binomial_p_one_sided": float(stats.binom.sf(kpos - 1, len(roots), 0.5)),
                                "reading": ("CONFIRMED ACROSS ROOTS" if g1["MECHANISM"] and kpos >= (4 if len(roots) == 5 else len(roots) - 1)
                                            else "FAMILY ONLY" if g1["MECHANISM"] else "NOT CONFIRMED")}
    # ------------------------------------------------ per root
    daily, gapd, pvals = {}, {}, {}
    ladder_parts = {k: [] for k in ("C1", "C2", "C3")}
    for r in roots:
        t_, d = tr[r], fr[r]
        ct = t_["ctier"].to_numpy(float)
        c1, c2, c3 = ct < 1 / 3, (ct >= 1 / 3) & (ct < 2 / 3), ct >= 2 / 3
        ses = d.index[d["eligible"] & (d.index >= t_["session"].min())]
        years = len(ses) / 252
        gb = t_["gross"].to_numpy(float)
        net = gb - t_["cost_bp"].to_numpy(float)
        pct = t_["pct"].to_numpy(float)
        tk = t_["tick_bp"].to_numpy(float)
        exc_c = ~t_["session"].between(*COVID).to_numpy()
        n1 = G.mt(net[c1], R)
        pvals[r] = float(stats.norm.sf(n1["t"])) if n1["t"] is not None else 1.0
        yrs = t_["session"].str[:4].to_numpy()
        per_year = {y: int((c1 & (yrs == y)).sum()) for y in np.unique(yrs)}
        pools = {y: np.flatnonzero(yrs == y) for y in per_year}
        draws = np.array([net[np.concatenate([rng.choice(pools[y], per_year[y], replace=False) for y in per_year if per_year[y]])].mean()
                          for _ in range(N_PLACEBO)])
        D = t_["D"].to_numpy(int)
        for k_, msk in (("C1", c1), ("C2", c2), ("C3", c3)):
            ladder_parts[k_].append(pd.Series(pct[msk], index=t_["session"].to_numpy()[msk]))
        c1df = t_[c1]
        rec = {"trades_B0": int(len(t_)), "trades_C1": int(c1.sum()), "C1_per_year": float(c1.sum() / years),
               "window_start": str(t_["session"].min()),
               "ladder_gross_pct_A": {"C1": G.mt(pct[c1], R), "C2": G.mt(pct[c2], R), "C3": G.mt(pct[c3], R), "B0": G.mt(pct, R)},
               "ladder_gross_bp": {"C1": G.mt(gb[c1], R), "C2": G.mt(gb[c2], R), "C3": G.mt(gb[c3], R), "B0": G.mt(gb, R)},
               "gate2": {"C1_net_bp": n1, "p_one_sided": pvals[r], "net_plus1tick": float((net - 2 * tk)[c1].mean()),
                         "net_ex_covid": float(net[c1 & exc_c].mean()), "trades": int(c1.sum())},
               "placebo_within_year_net": {"C1_net": float(net[c1].mean()), "p50": float(np.median(draws)),
                                           "p95": float(np.quantile(draws, 0.95)), "rank": float((draws < net[c1].mean()).mean())},
               "each_input_alone_delta_pct_A": {"p_rv": delta(pct, t_["p_rv"].to_numpy(float), np.isfinite(t_["p_rv"].to_numpy(float))),
                                                "p_on": delta(pct, t_["p_on"].to_numpy(float), np.isfinite(t_["p_on"].to_numpy(float)))},
               "C1_long": G.mt(gb[c1 & (D > 0)], R), "C1_short": G.mt(gb[c1 & (D < 0)], R),
               "C1_by_year_gross": {y: G.mt(gb[c1 & (yrs == y)], R) for y in sorted(set(yrs))},
               "C1_gap_open_share": float(t_.loc[c1, "gap_open"].mean()), "B0_gap_open_share": float(t_["gap_open"].mean()),
               "cost_bp": float(t_["cost_bp"].mean()), "ATR_bp_median": float(t_["A_bp"].median()),
               "four_groups_C1": G.four_groups(gb[c1], net[c1], t_["cost_bp"].to_numpy(float)[c1], c1.sum() / years,
                                               t_["session"].to_numpy()[c1], D[c1])}
        rec["daily_net_C1"] = G.daily_stats(c1df, net[c1], ses, cst[r]["usd_per_point"])
        rec["daily_gross_C1"] = G.daily_stats(c1df, gb[c1], ses, cst[r]["usd_per_point"])
        daily[r] = M.daily_usd(c1df, net[c1], np.ones(int(c1.sum())), ses, cst[r]["usd_per_point"])
        gm = t_["gap_open"].to_numpy(bool)
        gapd[r] = M.daily_usd(t_[gm], net[gm], np.ones(int(gm.sum())), ses, cst[r]["usd_per_point"])
        out["roots"][r] = rec
    for r in roots:
        s = daily[r]
        kk = k8.reindex(s.index)
        ok = kk.notna()
        out["roots"][r]["component"] = {"rho_K8": float(np.corrcoef(s[ok], kk[ok])[0, 1]) if ok.sum() > 30 else None,
                                        "rho_other_roots": {o: float(s.corr(daily[o].reindex(s.index).fillna(0.0))) for o in roots if o != r},
                                        "rho_gap_open_book_same_root": float(s.corr(gapd[r])),
                                        "not_rebuilt": ["#2 the MACD day-session arm (ADMITTED)", "#3 the NG winter spread (daily P&L missing)"]}
    out["family_ladder_gross_pct_A"] = {k: G.mt(pd.concat(v).groupby(level=0).mean().to_numpy(), R) for k, v in ladder_parts.items()}
    h2 = B.T.holm(pvals) if g1["MECHANISM"] else {}
    for r in roots:
        g2 = out["roots"][r]["gate2"]
        ok = bool(g1["MECHANISM"] and h2.get(r, 1.0) < 0.05 and (g2["C1_net_bp"]["mean"] or -1) > 0 and g2["net_plus1tick"] > 0
                  and g2["trades"] >= MIN_TRADES and g2["net_ex_covid"] > 0)
        g2["holm_p"], g2["pass"] = h2.get(r), ok
        out["roots"][r]["verdict"] = "SUPPORTED" if ok else "MECHANISM ONLY" if g1["MECHANISM"] else "NOT SUPPORTED"
    out["_exc"] = exc
    return out


def build(data_root: Path) -> dict[str, Any]:
    t0 = time.time()
    g = B.load_fixture(G.FIXTURE)
    ident = G.identity_gate(g, data_root)
    if not all(v["pass"] for v in ident.values()):
        raise D679Error(f"identity gate failed: {ident}")
    fr, bars_all, cov = G.frames(g, data_root)
    del g
    R = M.S.load_v2().R
    rng = np.random.default_rng(SEED)
    b_all, use_nq, _gd, R2_ = M.load_bars(data_root, False, ("ES", "NQ"))
    C._R = R2_
    tabs = R2_.session_table(b_all, use_nq, roots=("NQ",))
    k8 = M.k8_daily(tabs["NQ"], tabs["NQ"].index[(tabs["NQ"].index >= FIRST) & (tabs["NQ"].index < RESERVED_FROM)])
    out: dict[str, Any] = {"spec": "D679 (633a7ab8) + D679-A1 (7fb7e196)", "costs": {**costs(ROOTS), **costs(ROOTS2)},
                           "data_gates": {"identity_primary": ident,
                                          "coverage_primary": {r: {k: v for k, v in c.items() if k != "unusable_list"} for r, c in cov.items()},
                                          "family2": "D676's fixture, gated 0a6c033f"}}
    prim = family(ROOTS, fr, bars_all, costs(ROOTS), R, rng, k8)
    fr2, bars2 = frames2(data_root)
    fam2 = family(ROOTS2, fr2, bars2, costs(ROOTS2), R, rng, k8)
    exc = {**prim.pop("_exc"), **fam2.pop("_exc")}
    out["primary"] = prim
    out["family2_CL_NG_GC_SI"] = fam2
    k9 = int(sum(v > 0 for v in exc.values()))
    out["all_nine_reported"] = {"roots_with_excess_positive": k9, "of": len(exc),
                                "binomial_p_one_sided": float(stats.binom.sf(k9 - 1, len(exc), 0.5)), "excess": exc}
    lad = prim["family_ladder_gross_pct_A"]
    out["predictions"] = {"1_family_delta_positive": bool(prim["gate1_family"]["a_rotation"]["delta_pct_A"] > 0),
                          "2_excess_over_own_p50_on_4_of_5": bool(prim["mechanism_reading"]["roots_with_excess_positive"] >= 4),
                          "3_no_root_passes_gate2": not any(prim["roots"][r]["gate2"]["pass"] for r in ROOTS),
                          "4_family_ladder_monotone": bool(lad["C1"]["mean"] > lad["C2"]["mean"] > lad["C3"]["mean"])}
    out["runtime_min"] = round((time.time() - t0) / 60, 2)
    return out


def selftest() -> int:
    fired = []

    def must_raise(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except (D679Error, G.D678Error, B.D676Error, C.D671Error):
            fired.append(name)
            return
        raise SystemExit(f"selftest: the {name} canary did not raise")

    rng = np.random.default_rng(9)
    v = rng.normal(size=600)
    t = C.tiers(v)
    C.tier_audit(t, v, [300, 450, 599])
    must_raise("a tier that includes its own value", lambda: C.tier_audit(C.tiers(v, leak=True), v, [300, 450, 599]))
    idx = [f"2019-{m_:02d}-{d_:02d}" for m_ in range(1, 13) for d_ in range(1, 29)][:300]
    d = pd.DataFrame({"high": 101 + rng.random(300), "low": 99 - rng.random(300), "open": 100.0, "close": 100 + rng.normal(0, .3, 300),
                      "on_high": 100.8, "on_low": 99.4, "on_last_m": G.hm("08:59"), "atr20": 2.0}, index=idx)
    features(d, "HO")
    must_raise("an overnight bar at the open", lambda: features(d.assign(on_last_m=G.hm("09:00")), "HO"))
    m = np.arange(G.hm("09:00"), G.hm("12:00"))
    down = np.linspace(105, 95, len(m))
    bd = {"m": m, "o": down, "h": down + 0.02, "l": down - 0.02, "c": down}
    px, why, k, stp = G.exit_ix(bd, 0, 1, 105.0, 104.0, 4.0, G.hm("11:59"))
    G.fill_audit(bd, k, px, why, stp)
    must_raise("a stop filled with an extra tick", lambda: G.fill_audit(bd, k, px - 0.01, why, stp))
    must_raise("a bar after the flat time", lambda: B.flat_audit(bd, G.hm("10:00")))
    ii = pd.Index(["2019-01-10", "2019-01-22"])
    dd = pd.DataFrame({"contract": ["HOG9", "HOG9"]}, index=ii)
    must_raise("a session inside the delivery buffer", lambda: G.r2_audit(pd.Series(False, index=ii), dd, "HO"))
    pct = rng.normal(size=400)
    tier = rng.random(400)
    a = delta(pct, tier, np.ones(400, bool))
    rot_check(a, delta(pct, np.roll(tier, 0), np.ones(400, bool)))
    must_raise("the rotation's offset 0 not reproducing the actual", lambda: rot_check(a, delta(pct, np.roll(tier, 1), np.ones(400, bool))))
    if set(costs(ROOTS2)) != set(ROOTS2) or any(SESS[r]["flat"] <= SESS[r]["open"] for r in ROOTS + ROOTS2):
        raise SystemExit("selftest: family 2 costs or sessions")
    print(f"selftest: {len(fired)} canaries fired: {fired}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=G.DATA)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.run:
        ap.print_help()
        return 1
    out = build(a.data_root)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    summ = {k: {"delta": out[k]["gate1_family"]["a_rotation"]["delta_pct_A"], "rank": out[k]["gate1_family"]["a_rotation"]["rank"],
                "MECHANISM": out[k]["gate1_family"]["MECHANISM"], "reading": out[k]["mechanism_reading"]["reading"],
                "verdicts": {r: v["verdict"] for r, v in out[k]["roots"].items()}} for k in ("primary", "family2_CL_NG_GC_SI")}
    print(json.dumps({**summ, "all_nine": out["all_nine_reported"], "predictions": out["predictions"], "runtime_min": out["runtime_min"]},
                     indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
