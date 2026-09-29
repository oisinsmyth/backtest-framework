"""D673: the compression break on YM and RTY. Spec: docs/decisions/D673-PRE-REG-the-compression-break-on-ym-and-rty.md
(fb8c4c5e): D672's rule unchanged (D666 plain break + E4 at each root's own tick; trade only when the compression tier
< 1/3; one micro; MYM/M2K d508_exec cost). In-sample to 2025-02-28; the vault is never read. Dealer gamma (GEX,
SqueezeMetrics) enters only as a declared secondary, prior row, never output per date.

    uv run python scripts/stage0_d673_compression_ym_rty.py --selftest
    uv run python scripts/stage0_d673_compression_ym_rty.py --gates [--data-root DIR]   # data gates only, no outcome
    uv run python scripts/stage0_d673_compression_ym_rty.py --run   [--data-root DIR]   # once

Data: RTH from D462's fut_{YM,RTY}_rth_1m; overnight bars from fut_opening_globex_1m_ym_rty (build_fut_opening_1m.py
--roots YM,RTY), gated by (i) identity of its RTH bars with D462's, (ii) overnight coverage, (iii) the seal.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d671_break_construction as C  # noqa: E402

M, X, T = C.M, C.X, C.T
OUT = REPO / "data" / "stage0_d673_compression_ym_rty.json"
GLOBEX = REPO / "data" / "fixtures" / "fut_opening_globex_1m_ym_rty.csv.gz"
EVID = ("YM", "RTY")
N_PLACEBO, N_BOOT, SEED = 1000, 500, 673
MIN_C1 = 60
COVID = X.COVID


class D673Error(RuntimeError):
    pass


# ================================================================================ data and gates
def load_globex(path: Path = GLOBEX) -> pd.DataFrame:
    g = pd.read_csv(path, encoding="utf-8", dtype={"session": str, "hhmm": str},
                    usecols=["root", "session", "hhmm", "open", "high", "low", "close", "volume"])
    g = M.filter_before(g, "session", M.RESERVED_FROM)
    M.assert_none_at_or_after(g, "session", M.RESERVED_FROM)
    return g


def identity_gate(g: pd.DataFrame, rth: pd.DataFrame, r: str) -> dict[str, Any]:
    """(i) The globex fixture's 09:30-15:59 bars equal D462's RTH fixture bar for bar, in-sample."""
    a = g[(g["root"] == r) & (g["hhmm"] >= "09:30") & (g["hhmm"] <= "15:59") & (g["session"] >= M.FIRST)]
    b = rth[(rth["root"] == r) & (rth["session"] >= M.FIRST)]
    a = a.set_index(["session", "hhmm"])[["open", "high", "low", "close"]].sort_index()
    b = b.set_index(["session", "hhmm"])[["open", "high", "low", "close"]].sort_index()
    j = a.join(b, lsuffix="_g", rsuffix="_r", how="outer")
    diff = int(sum((np.abs(j[f"{c}_g"] - j[f"{c}_r"]) > 1e-6).sum() for c in ("open", "high", "low", "close")))
    out = {"rth_bars_globex": int(len(a)), "rth_bars_d462": int(len(b)), "only_globex": int(j["close_r"].isna().sum()),
           "only_d462": int(j["close_g"].isna().sum()), "price_mismatches": diff}
    out["pass"] = bool(out["only_globex"] == 0 and out["only_d462"] == 0 and diff == 0)
    return out


def coverage_gate(g: pd.DataFrame, sessions: pd.Index, r: str) -> dict[str, Any]:
    """(ii) The share of sessions with at least one overnight bar, per year (no imputation: a session without one has
    no comp and is excluded)."""
    x = g[(g["root"] == r) & ((g["hhmm"] >= "18:00") | (g["hhmm"] < "09:30"))]
    have = pd.Index(x["session"].unique())
    s = pd.Series(sessions.isin(have), index=sessions)
    return {"share": float(s.mean()), "sessions_without": int((~s).sum()),
            "by_year": {y: round(float(v), 4) for y, v in s.groupby(s.index.str[:4]).mean().items()}}


def seal_gate(g: pd.DataFrame) -> dict[str, Any]:
    """(iii) No session on or after 2025-03-01."""
    bad = int((g["session"] >= M.RESERVED_FROM).sum())
    if bad:
        raise D673Error(f"seal: {bad} rows on or after {M.RESERVED_FROM}")
    return {"rows_at_or_after_reserved": 0, "pass": True}


def load_all(data_root: Path) -> tuple[pd.DataFrame, list[str], dict, Any, pd.DataFrame]:
    b, use, Gd, R = M.load_bars(data_root, False, M.ROOTS)  # ES/NQ (opening fixture) + YM/RTY RTH (D462)
    g = load_globex()
    over = g[(g["root"].isin(EVID)) & ((g["hhmm"] >= "18:00") | (g["hhmm"] < "09:30"))]
    b2 = pd.concat([b, over[["root", "session", "hhmm", "open", "high", "low", "close", "volume"]]], ignore_index=True)
    M.assert_none_at_or_after(b2, "session", M.RESERVED_FROM)
    return b2, use, Gd, R, g


# ================================================================================ the rule and its books
def compression_tier(S_: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    p_rv, p_on = C.tiers(S_["rv5"].to_numpy(float)), C.tiers(S_["on_range"].to_numpy(float))
    comp = (p_rv + p_on) / 2
    return C.tiers(comp), p_rv, p_on


def rotation(tv_sess: pd.Series, tr: pd.DataFrame, win: np.ndarray, val: np.ndarray, c1: np.ndarray) -> dict[str, Any]:
    cs = tv_sess.dropna()
    tv = cs.to_numpy()
    pos = pd.Series(np.arange(len(cs)), index=cs.index).reindex(tr["session"]).to_numpy()
    okp = np.isfinite(pos) & win
    diffs = []
    for kk in range(21, len(tv) - 21):
        rt = np.full(len(tr), np.nan)
        rt[okp] = np.roll(tv, kk)[pos[okp].astype(int)]
        q_, r_ = okp & (rt < 1 / 3), okp & (rt >= 1 / 3)
        diffs.append(val[q_].mean() - val[r_].mean())
    diffs = np.array(diffs)
    act = float(val[c1].mean() - val[win & ~c1].mean())
    return {"c1_minus_rest": act, "p50": float(np.median(diffs)), "p95": float(np.quantile(diffs, 0.95)),
            "rank": float((diffs < act).mean()), "p_one_sided": float((diffs >= act).mean()), "offsets": int(len(diffs))}


def root_block(r: str, d: pd.DataFrame, S_: pd.DataFrame, tr: pd.DataFrame, bars: dict, costs: dict, R: Any,
               rng: np.random.Generator) -> dict[str, Any]:
    X.TICK = M.TICK_PTS[r]
    tr["cost_bp"] = costs[r]["cost_usd"] / costs[r]["usd_per_point"] / tr["entry"] * 1e4
    tr["retest"] = [C.retest(bars[(r, s)], int(i), int(D), float(L)) for s, i, D, L in zip(tr["session"], tr["i"], tr["D"], tr["L"])]
    sess = S_.index.to_numpy()
    ctier, p_rv, p_on = compression_tier(S_)
    C.tier_audit(ctier, (p_rv + p_on) / 2, list(range(0, len(sess), max(1, len(sess) // 12))))
    tr["ctier"] = pd.Series(ctier, index=sess).reindex(tr["session"]).to_numpy()
    tr["p_rv"] = pd.Series(p_rv, index=sess).reindex(tr["session"]).to_numpy()
    tr["p_on"] = pd.Series(p_on, index=sess).reindex(tr["session"]).to_numpy()
    ct = tr["ctier"].to_numpy(float)
    win = np.isfinite(ct)
    ses = d.index[d.index >= tr.loc[win, "session"].min()]
    years, usd_pt = len(ses) / 252, costs[r]["usd_per_point"]
    c1, c2, c3 = win & (ct < 1 / 3), win & (ct >= 1 / 3) & (ct < 2 / 3), win & (ct >= 2 / 3)
    bk = lambda k, col="E4_gross": C.book(tr, k, col, years, usd_pt, ses)  # noqa: E731
    gross = tr["E4_gross"].to_numpy(float)
    netv = gross - tr["cost_bp"].to_numpy(float)
    yrs = tr["session"].str[:4].to_numpy()
    # Gate 1
    rot = rotation(pd.Series(ctier, index=sess), tr, win, gross, c1)
    gm, gt, gse = M.mean_t(gross[c1], R)
    # Gate 2
    nm, nt, _ = M.mean_t(netv[c1], R)
    per_year = {yv: int((c1 & (yrs == yv)).sum()) for yv in np.unique(yrs[win])}
    pools = {yv: np.flatnonzero(win & (yrs == yv)) for yv in per_year}
    draws = np.array([netv[np.concatenate([rng.choice(pools[yv], per_year[yv], replace=False) for yv in per_year if per_year[yv]])].mean()
                      for _ in range(N_PLACEBO)])
    q95 = [np.quantile(rng.choice(draws, len(draws)), 0.95) for _ in range(N_BOOT)]
    placebo = {"c1_net": float(netv[c1].mean()), "p50": float(np.median(draws)), "p95": float(np.quantile(draws, 0.95)),
               "p95_se": float(np.std(q95, ddof=1)), "rank": float((draws < netv[c1].mean()).mean())}
    tk = M.TICK_PTS[r] / tr["entry"].to_numpy(float) * 1e4
    exc = ~tr["session"].between(*COVID).to_numpy()
    g2 = {"c1_trades": int(c1.sum()), "net_mean": nm, "net_t_hac": nt, "p_one_sided": float(stats.norm.sf(nt)) if np.isfinite(nt) else 1.0,
          "placebo": placebo, "net_plus1tick_every_fill": float((netv - 2 * tk)[c1].mean()),
          "net_ex_covid": float(netv[c1 & exc].mean())}
    # secondaries
    D = tr["D"].to_numpy(int)
    gser = pd.Series(-d["gd_spx"] / d["V20"], index=d.index)
    g_med = gser.shift(1).rolling(250, min_periods=125).median().reindex(tr["session"]).to_numpy(float)
    g_now = gser.reindex(tr["session"]).to_numpy(float)
    sec = {"S1_g_above_median": bk(c1 & (g_now > g_med)), "S1_g_below_median": bk(c1 & (g_now <= g_med)),
           "S2_ladder": {"C1": bk(c1), "C2": bk(c2), "C3": bk(c3)},
           "S3_long": bk(c1 & (D > 0)), "S3_short": bk(c1 & (D < 0)),
           "S4_p_rv_bottom": bk(win & (tr["p_rv"].to_numpy(float) < 1 / 3)), "S4_p_on_bottom": bk(win & (tr["p_on"].to_numpy(float) < 1 / 3)),
           "S5_E2": bk(c1, "E2_gross"),
           "S6_by_year": {yv: {"B0": C.book(tr, win & (yrs == yv), "E4_gross", 1.0, usd_pt, ses[ses.str.startswith(yv)]),
                               "C1": C.book(tr, c1 & (yrs == yv), "E4_gross", 1.0, usd_pt, ses[ses.str.startswith(yv)])}
                          for yv in sorted(set(yrs[win]))}}
    fg = X.four_groups(tr[c1].reset_index(drop=True), pd.Series(gross[c1]), pd.Series(netv[c1]), c1.sum() / years, R, r) if c1.sum() > 5 else {}
    return {"window_start": str(ses[0]), "sessions_in_window": int(len(ses)),
            "books": {"B0": bk(win), "C1": bk(c1), "C2": bk(c2), "C3": bk(c3)},
            "gate1": {"rotation": rot, "c1_gross_mean": gm, "c1_gross_t_hac": gt, "p_gross_one_sided": float(stats.norm.sf(gt)) if np.isfinite(gt) else 1.0},
            "gate2": g2, "secondaries": sec, "four_groups_C1": fg,
            "_daily": M.daily_usd(tr, netv, c1.astype(float), ses, usd_pt), "_c1": (tr, c1, netv, ses, usd_pt)}


# ================================================================================ build
def build(data_root: Path, gates_only: bool = False) -> dict[str, Any]:
    t0 = time.time()
    costs = M.micro_costs()
    b, use, Gd, R, g = load_all(data_root)
    C._R = R
    rth = b[b["root"].isin(EVID) & (b["hhmm"] >= "09:30") & (b["hhmm"] <= "15:59")]
    out: dict[str, Any] = {"spec": "D673 (fb8c4c5e)", "credit": "dealer gamma (GEX): SqueezeMetrics (secondary only)",
                           "data_gates": {"seal": seal_gate(g)}}
    for r in EVID:
        out["data_gates"][f"identity_{r}"] = identity_gate(g, rth, r)
    T.MULT.update(M.MULT)
    tabs = R.session_table(b, use, roots=M.ROOTS)
    for r in EVID:
        dd = T.root_frame(b, tabs[r], r)
        out["data_gates"][f"coverage_{r}"] = coverage_gate(g, dd.index, r)
    if not all(out["data_gates"][f"identity_{r}"]["pass"] for r in EVID):
        raise D673Error(f"data gate (i) failed: {out['data_gates']}")
    if gates_only:
        return out
    bars = R.bar_arrays(b)
    dix = pd.read_csv(data_root / "raw" / "squeezemetrics" / "DIX.csv", encoding="utf-8", dtype={"date": str})
    gex = dix[dix["date"] < M.RESERVED_FROM].set_index("date")["gex"].astype(float).sort_index()
    cal_all = pd.read_csv(data_root / "fixtures" / "cme_session_calendar.csv.gz", encoding="utf-8", dtype={"day": str})
    frames, sf = {}, {}
    for r in M.ROOTS:
        d = T.root_frame(b, tabs[r], r)
        d = d[np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)].copy()
        d["gd_spx"] = T.gex_prior(gex, d.index)
        T.gex_lag_audit(gex, d.index[:: max(1, len(d) // 40)])
        on = C.overnight(b, r)
        C.overnight_audit(on)
        S_ = C.session_features(d, on, cal_all[cal_all["root"] == r].set_index("day"))
        if r in EVID:  # no imputation: a session without overnight bars has no comp
            S_ = S_[np.isfinite(S_["on_range"])]
            d = d.loc[S_.index]
        frames[r], sf[r] = d, S_
    jobs = [(r, frames[r], {s: bars[(r, s)] for s in frames[r].index if (r, s) in bars}, M.TICK_PTS[r], M.SEED + M.ROOTS.index(r))
            for r in M.ROOTS]
    with ProcessPoolExecutor(max_workers=4) as pool:
        got = {o["root"]: o for o in pool.map(M.root_trades, jobs)}
    rng = np.random.default_rng(SEED)
    blocks = {}
    for r in M.ROOTS:
        tr = pd.DataFrame(got[r]["rows"]).sort_values("session").reset_index(drop=True)
        blocks[r] = root_block(r, frames[r], sf[r], tr, bars, costs, R, rng)
    # NQ must reproduce D672's C1 (the rule is unchanged); ES likewise
    ref = json.loads((REPO / "data" / "stage0_d672_compression_break.json").read_text(encoding="utf-8"))["roots"]
    for r in ("ES", "NQ"):
        tr, c1, netv, ses, _ = blocks[r]["_c1"]
        # D672's window began at D671's forecast window; compare on D672's own C1 count by year where both exist
        out.setdefault("dev_reproduction", {})[r] = {"d673_c1_net_full_tier_window": float(netv[c1].mean()),
                                                      "d672_c1_net": ref[r]["books"]["C1_compression"]["net"]}
    k8 = M.k8_daily(tabs["NQ"], frames["NQ"].index)
    out["roots"] = {}
    for r in EVID:
        blk = blocks[r]
        tr, c1, netv, ses, usd_pt = blk.pop("_c1")
        others = {o_: blocks[o_]["_daily"] for o_ in M.ROOTS if o_ != r}
        blk["component_C1"] = M.component(tr, netv, tr["E4_gross"].to_numpy(float), c1.astype(float), ses, usd_pt, k8, others)
        blk.pop("_daily")
        out["roots"][r] = blk
    # verdicts (Holm across YM and RTY)
    pa = {r: out["roots"][r]["gate1"]["rotation"]["p_one_sided"] for r in EVID}
    pb = {r: out["roots"][r]["gate1"]["p_gross_one_sided"] for r in EVID}
    ha, hb = T.holm(pa), T.holm(pb)
    passed1 = []
    for r in EVID:
        g1 = out["roots"][r]["gate1"]
        g1["checks"] = {"a_above_rotation_p95": bool(g1["rotation"]["rank"] > 0.95), "a_holm_p": ha[r],
                        "b_gross_positive_holm": bool(g1["c1_gross_mean"] > 0 and hb[r] < 0.05), "b_holm_p": hb[r]}
        if g1["checks"]["a_above_rotation_p95"] and ha[r] < 0.05 and g1["checks"]["b_gross_positive_holm"]:
            passed1.append(r)
    h2 = T.holm({r: out["roots"][r]["gate2"]["p_one_sided"] for r in passed1}) if passed1 else {}
    for r in EVID:
        g2 = out["roots"][r]["gate2"]
        ok2 = bool(r in h2 and h2[r] < 0.05 and g2["net_mean"] > 0
                   and g2["net_mean"] - g2["placebo"]["p95"] > 2 * g2["placebo"]["p95_se"]
                   and g2["net_plus1tick_every_fill"] > 0 and g2["c1_trades"] >= MIN_C1 and g2["net_ex_covid"] > 0)
        g2["checks"] = {"pass": ok2, "holm_p": h2.get(r)}
        out["roots"][r]["verdict"] = "SUPPORTED" if r in passed1 and ok2 else "MECHANISM ONLY" if r in passed1 else "NOT SUPPORTED"
    rr = out["roots"]
    full_rty = [y for y in rr["RTY"]["secondaries"]["S6_by_year"] if "2020" <= y <= "2024"]
    out["predictions"] = {
        "1_RTY_passes_gate1": "RTY" in passed1,
        "2_RTY_gate2_marginal_net_positive_t_below_2": bool(rr["RTY"]["gate2"]["net_mean"] > 0 and rr["RTY"]["gate2"]["net_t_hac"] < 2),
        "3_YM_fails_gate1a_and_C3_worst": bool(not rr["YM"]["gate1"]["checks"]["a_above_rotation_p95"]
                                               and rr["YM"]["books"]["C3"]["net"] <= min(rr["YM"]["books"]["C1"]["net"], rr["YM"]["books"]["C2"]["net"])),
        "4_RTY_S1_higher_g_better": bool(rr["RTY"]["secondaries"]["S1_g_above_median"].get("net", -99) > rr["RTY"]["secondaries"]["S1_g_below_median"].get("net", 99)),
        "5_RTY_C1_positive_4_of_full_years": bool(sum(1 for y in full_rty if rr["RTY"]["secondaries"]["S6_by_year"][y]["C1"].get("net", -1) > 0) >= 4)}
    out["runtime_min"] = round((time.time() - t0) / 60, 2)
    T.licence_guard(out)
    return out


# ================================================================================ selftest
def selftest() -> int:
    fired = []

    def must_raise(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except (D673Error, C.D671Error, T.D663Error):
            fired.append(name)
            return
        raise SystemExit(f"selftest: the {name} canary did not raise")

    rng = np.random.default_rng(5)
    v = rng.normal(size=700)
    t = C.tiers(v)
    C.tier_audit(t, v, [300, 500, 699])
    must_raise("tier with its own value", lambda: C.tier_audit(C.tiers(v, leak=True), v, [300, 500, 699]))
    b = pd.DataFrame({"root": "YM", "session": "2019-01-03", "hhmm": ["18:05", "09:29", "09:30"], "open": 1.0,
                      "high": [2.0, 3.0, 9.0], "low": [1.0, 0.5, 0.1], "close": 1.0, "volume": 1})
    C.overnight_audit(C.overnight(b, "YM"))
    must_raise("overnight reading 09:30", lambda: C.overnight_audit(C.overnight(b, "YM", include_rth=True)))
    gx = pd.Series([1.0, 2.0, 3.0], index=["2019-01-02", "2019-01-03", "2019-01-04"])
    T.gex_lag_audit(gx, pd.Index(["2019-01-03", "2019-01-04"]))
    same_day = lambda g_, s_: g_.reindex(s_)  # noqa: E731  -- the canary: the session's own row
    must_raise("GEX from the session's own row", lambda: T.gex_lag_audit(gx, pd.Index(["2019-01-03", "2019-01-04"]), same_day))
    g_ok = pd.DataFrame({"root": "YM", "session": ["2019-01-03"] * 2, "hhmm": ["09:30", "09:31"], "open": [1.0, 2.0],
                         "high": [1.0, 2.0], "low": [1.0, 2.0], "close": [1.0, 2.0], "volume": 1})
    if not identity_gate(g_ok, g_ok, "YM")["pass"]:
        raise SystemExit("selftest: the identity gate failed on identical bars")
    g_bad = g_ok.copy()
    g_bad.loc[1, "close"] = 2.5
    if identity_gate(g_bad, g_ok, "YM")["pass"]:
        raise SystemExit("selftest: the identity gate passed a mismatched bar")
    fired.append("identity gate on a mismatched bar")
    must_raise("a vault session", lambda: seal_gate(pd.DataFrame({"session": ["2025-03-03"]})))
    print(f"selftest: {len(fired)} canaries fired: {fired}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--gates", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.gates:
        out = build(a.data_root, gates_only=True)
        print(json.dumps(out["data_gates"], indent=1))
        return 0
    if not a.run:
        ap.print_help()
        return 1
    out = build(a.data_root)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"verdicts": {r: v["verdict"] for r, v in out["roots"].items()}, "predictions": out["predictions"],
                      "runtime_min": out["runtime_min"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
