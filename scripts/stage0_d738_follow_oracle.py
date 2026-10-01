"""D738 Stage 0, step 1: the oracle of an expected-profit filter on D727's NQ follow, and a profile of where its winners
sit (docs/decisions/D738-STAGE-0-PRE-REG-the-oracle-of-an-expected-profit-filter-on-the-nq-follow.md).

    uv run python scripts/stage0_d738_follow_oracle.py --selftest      # synthetic only
    uv run python scripts/stage0_d738_follow_oracle.py --run           # once -> data/stage0_d738_follow_oracle.json

THE SEAL. NQ's 2024+ last hour is D716's joint-vault look. The NQ minute fixture is read in chunks keeping only
day <= 2023-12-29 before any row is kept; D691's frame and IV table are built under D720's `lowered_cut` (every cut
constant in that chain held at 2024-01-01) and asserted to hold no session on or after it. The output holds aggregates
only (no per-date SqueezeMetrics series). Nothing here chooses a filter (D738 s.0).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d720_size_the_direction as Z  # noqa: E402
import stage0_d727_trend_curve as T7  # noqa: E402
import stage0_d736_earn_when_trading_screen as S736  # noqa: E402
from backtest_framework.validation import filter_oracle as FO  # noqa: E402

DATA = Path("C:/Users/O/Desktop/Projects/Backtest Framework/data")  # the main checkout's fixtures (as D727's runs)
OUT = REPO / "data" / "stage0_d738_follow_oracle.json"
HI, CUT24 = Z.HI, Z.CUT24
KS = (0.5, 1.0, 1.5)
PRIMARY, POOL = 1.5, 0.5
RHOS = (0.0, 0.05, 0.10, 0.20, 0.30, 0.50, 1.0)
QS = (0.5, 0.7)
N_DRAW, SEED = 1000, 738
CALM = ("2016", "2017", "2019")
V_PANEL = ("V1_sigma_usd", "V2_abs_z", "V3_entry_clock_min", "V4_gap_with_trade", "V5_yday_with_trade",
           "V6_vol_trend_rms5_over_soc", "V7_soc_pct_252")
V_D691 = ("V8_ln_iv_rv", "V9_size_tier", "V10_gamma_prior", "V11_on_range")
P = Z.P


class D738Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D738Error(msg)


# ================================================================================ the NQ panel (cut at read time)
def read_cut(path: Path) -> pd.DataFrame:
    parts = []
    for ch in pd.read_csv(path, encoding="utf-8", dtype={"day": str, "hhmm": str, "contract": str}, chunksize=500_000):
        parts.append(ch[(ch["day"] >= T7.LO) & (ch["day"] <= HI)])
    b = pd.concat(parts, ignore_index=True)
    Z.no_session_after(b["day"].unique(), "NQ's one-minute bars")
    return b


def full_day_arrays(pn: dict[str, Any]) -> dict[str, np.ndarray]:
    """Per day in all_days: O, the last close, oc; sigma_oc (prior 20, as D727), the prior-5 RMS, and sigma_oc's
    percentile in its trailing 252 (prior days only)."""
    O, CL = pn["all_O"], pn["all_C_last"]
    oc = CL - O
    s20 = np.sqrt(pd.Series(oc * oc).shift(1).rolling(20, min_periods=20).mean().to_numpy(float))
    s5 = np.sqrt(pd.Series(oc * oc).shift(1).rolling(5, min_periods=5).mean().to_numpy(float))
    pct = pd.Series(s20).rolling(252, min_periods=252).apply(lambda w: (w[:-1] < w[-1]).mean() + 0.5 * (w[:-1] == w[-1]).mean(),
                                                            raw=True).to_numpy(float)
    return {"O": O, "CL": CL, "oc": oc, "s20": s20, "s5": s5, "pct": pct}


def book(pn: dict[str, Any], ob: dict[str, np.ndarray], k: float, usd_pt: float, cost: float,
         close: np.ndarray | None = None) -> dict[str, np.ndarray]:
    """D727's first-crossing rule, per day: side, entry clock index, entry price, gross and net (0 when flat)."""
    z = ob["z"]
    hit = np.abs(z) >= k
    first = np.where(hit.any(axis=1), hit.argmax(axis=1), -1)
    rows = np.arange(len(pn["days"]))
    j = np.clip(first, 0, None)
    side = np.where(first >= 0, np.sign(z[rows, j]), 0.0)
    entry = np.where(first >= 0, ob["Pt"][rows, j], np.nan)
    cl = ob["close"] if close is None else close
    g = np.where(side != 0, side * (cl - entry) * usd_pt, 0.0)
    net = np.where(side != 0, g - cost, 0.0)
    return {"side": side, "first": first, "entry": entry, "gross": g, "net": net, "abs_z": np.abs(z[rows, j]),
            "x": ob["x"][rows, j]}


def known_answers(bk: dict[float, dict[str, np.ndarray]], days: np.ndarray, ref: dict[str, Any]) -> None:
    years = np.array([d[:4] for d in days])
    for k in KS:
        r = ref["roots"]["NQ"]["books"]["first_crossing"][str(k)]
        tr = bk[k]["side"] != 0
        need(int(tr.sum()) == r["trades"], f"[KNOWN] k {k}: {int(tr.sum())} trades, D727 {r['trades']}")
        mn = float((bk[k]["net"][tr]).mean())
        need(abs(mn - r["mean_net"]) < 1e-6, f"[KNOWN] k {k}: mean net {mn} != D727 {r['mean_net']}")
        for y, v in r["net_by_year"].items():
            need(abs(float(bk[k]["net"][years == y].sum()) - v) < 1e-6, f"[KNOWN] k {k} {y}: net differs from D727")


# ================================================================================ D691's frame (D720's sealed build)
def d691_frame() -> tuple[pd.DataFrame, dict[str, Any]]:
    import stage0_d662_gamma_product as S
    import stage0_d691_iv_size as I
    C, T, M = I.C, I.T, I.M
    with Z.lowered_cut(I, S, T, M):
        fr = I.frames()["NQ"]
        Z.no_session_after(fr["d"].index, "the NQ frame")
        Z.no_session_after(fr["S"].index, "the NQ features")
        iv, _ = I.build_iv("NQ")
        Z.no_session_after(iv.index, "the NQ IV table")
    need(I.CUT == "2025-03-01" and T.RESERVED_FROM == "2025-03-01", "the cut constants were not restored")
    dz = I.design(fr, iv)
    sess, F0, y, ivrv = dz["sess"], dz["F0"], dz["y"], dz["ivrv"]
    F1 = np.column_stack([F0, ivrv])
    f1 = I.forecast(F1, y, I.SIGN1)
    idx = list(range(0, len(sess), max(1, len(sess) // 30)))
    old = C.SIGN
    C.SIGN = I.SIGN1
    fired = []
    try:
        C.forecast_audit(f1, F1, y, sess, idx)
        fl, _ = C.size_forecast(F1, y, leak=True)
        try:
            C.forecast_audit(fl, F1, y, sess, idx)
        except C.D671Error:
            fired.append("forecast leak")
    finally:
        C.SIGN = old
    need("forecast leak" in fired, "D720's forecast audit did not fire on the leaked canary")
    tau = C.tiers(f1)
    C.tier_audit(tau, f1, idx)
    try:
        C.tier_audit(C.tiers(f1, leak=True), f1, idx)
    except C.D671Error:
        fired.append("tier leak")
    need("tier leak" in fired, "D720's tier audit did not fire on the leaked canary")
    S_ = fr["S"]
    tab = pd.DataFrame({"V8_ln_iv_rv": ivrv, "V9_size_tier": tau,
                        "V10_gamma_prior": fr["d"]["gd_spx"].reindex(S_.index).to_numpy(float),
                        "V11_on_range": S_["on_range"].to_numpy(float),
                        "event": S_["event"].to_numpy(float), "opex": S_["opex"].to_numpy(float)},
                       index=pd.Index(sess, name="session"))
    return tab, {"forecast_and_tier_canaries": fired, "sessions": [str(sess[0]), str(sess[-1])], "n": int(len(sess))}


def join_audit(joined: np.ndarray, tab: pd.Series, days: np.ndarray, sample: np.ndarray) -> None:
    for i in sample:
        want = tab.get(days[i], np.nan)
        got = joined[i]
        need((np.isnan(want) and np.isnan(got)) or want == got, f"[JOIN] {days[i]}: the joined value is not that session's")


# ================================================================================ the prize and the profile
def daily_stats(net: np.ndarray, gross: np.ndarray, side: np.ndarray, days: np.ndarray) -> dict[str, Any]:
    tr = side != 0
    years = np.array([d[:4] for d in days])
    by = {y: float(net[years == y].sum()) for y in np.unique(years)}
    out = {"trades": int(tr.sum()), "share": float(tr.mean()), "mean_net": float(net[tr].mean()) if tr.any() else None,
           "median_net": float(np.median(net[tr])) if tr.any() else None,
           "mean_gross": float(gross[tr].mean()) if tr.any() else None,
           "median_gross": float(np.median(gross[tr])) if tr.any() else None,
           "total_net": float(net.sum()), "net_sharpe": Z.sharpe(net), "net_sortino": Z.sortino(net),
           "gross_sharpe": Z.sharpe(gross), "gross_sortino": Z.sortino(gross), "max_dd": Z.max_dd(net),
           "net_by_year": by, "trades_by_year": {y: int((tr & (years == y)).sum()) for y in np.unique(years)}}
    if len(by) >= 3:
        st = S736.stats(by)
        out["d736"] = {k: st[k] for k in ("ex2", "ex2_per_year", "years_positive", "years_needed", "label")}
    return out


def prize(b: dict[str, np.ndarray], days: np.ndarray, cost: float, usd_pt: float, rng: np.random.Generator) -> dict[str, Any]:
    tr = b["side"] != 0
    g, n = b["gross"][tr], b["net"][tr]
    yrs = np.array([d[:4] for d in days])[tr]
    orc = FO.oracle_take(n)
    tmpl = FO.oracle_take_threshold(g, cost, 2.0)
    size = np.abs(g) >= 2 * cost
    out = {"take_all": daily_stats(b["net"], b["gross"], b["side"], days)}
    for name, take in (("oracle_net_gt_0", orc), ("oracle_gross_ge_2c", tmpl), ("size_oracle_abs_move_ge_2c", size)):
        nd = np.zeros_like(b["net"])
        nd[np.flatnonzero(tr)[take]] = n[take]
        out[name] = {"trades": int(take.sum()), "take_rate": float(take.mean()), "net": float(n[take].sum()),
                     "mean_net": float(n[take].mean()) if take.any() else None, "net_sharpe": Z.sharpe(nd),
                     "by_year": {y: {"take_rate": float(take[yrs == y].mean()), "net": float(n[take & (yrs == y)].sum())}
                                 for y in np.unique(yrs)}}
    out["by_year"] = {y: {"trades": int((yrs == y).sum()), "take_all_net": float(n[yrs == y].sum()),
                          "oracle_net": float(n[orc & (yrs == y)].sum()), "oracle_take_rate": float(orc[yrs == y].mean()),
                          "win_rate": float((n[yrs == y] > 0).mean())} for y in np.unique(yrs)}
    calm = np.isin(yrs, CALM)
    out["calm_vs_other_oracle_take_rate"] = {"calm": float(orc[calm].mean()), "other": float(orc[~calm].mean())}
    out["partial_oracle_curve"] = {str(q): FO.partial_oracle_curve(n, n, RHOS, q, N_DRAW, rng) for q in QS}
    return out


def profile_var(v: np.ndarray, net: np.ndarray, gross: np.ndarray) -> dict[str, Any]:
    ok = np.isfinite(v)
    v, net, gross = v[ok], net[ok], gross[ok]
    lab = net > 0
    out: dict[str, Any] = {"n": int(ok.sum())}
    if ok.sum() < 50 or np.ptp(v) == 0:
        out["note"] = "too few or constant"
        return out
    edges = np.quantile(v, [0.2, 0.4, 0.6, 0.8])
    q = np.searchsorted(edges, v, side="right")
    out["quintiles"] = [{"q": int(k) + 1, "lo": float(v[q == k].min()), "hi": float(v[q == k].max()), "n": int((q == k).sum()),
                         "mean_net": float(net[q == k].mean()), "mean_gross": float(gross[q == k].mean()),
                         "win_rate": float(lab[q == k].mean()), "net_total": float(net[q == k].sum())}
                        for k in range(5) if (q == k).any()]
    out["spearman_net"] = FO.spearman(v, net)
    out["spearman_gross"] = FO.spearman(v, gross)
    out["auc_oracle"] = FO.auc(v, lab) if 0 < lab.sum() < lab.size else None
    return out


def profile(b: dict[str, np.ndarray], V: dict[str, np.ndarray], days: np.ndarray) -> dict[str, Any]:
    tr = b["side"] != 0
    n, g = b["net"][tr], b["gross"][tr]
    out = {name: profile_var(v[tr], n, g) for name, v in V.items() if name not in ("event", "opex")}
    for flag in ("event", "opex"):
        f = V[flag][tr]
        out[flag] = {str(int(val)): {"n": int((f == val).sum()), "mean_net": float(n[f == val].mean()),
                                     "win_rate": float((n[f == val] > 0).mean())}
                     for val in (0.0, 1.0) if (f == val).any()}
        out[flag]["n_missing"] = int((~np.isfinite(f)).sum())
    yrs = np.array([d[:4] for d in days])[tr]
    out["vol_by_year"] = {y: {"V1_sigma_usd_mean": float(np.nanmean(V["V1_sigma_usd"][tr][yrs == y])),
                              "V7_soc_pct_mean": float(np.nanmean(V["V7_soc_pct_252"][tr][yrs == y])),
                              "net": float(n[yrs == y].sum()), "trades": int((yrs == y).sum())} for y in np.unique(yrs)}
    return out


# ================================================================================ audits on the real panel
def pit_audit(pn: dict[str, Any], fa: dict[str, np.ndarray], kept_pos: np.ndarray, sample: list[int],
              same_day: bool = False) -> None:
    """Second implementation from the raw rows: the prior session's last close (<= 15:59) and the prior-5 RMS of
    open-to-close. `same_day` reads today's close as 'yesterday': the canary."""
    raw = pn["raw"]
    by_day = {d: g for d, g in raw.groupby("day")}

    def o_c(day: str) -> tuple[float, float]:
        r = by_day[day].sort_values("hhmm")
        o = float(r.loc[r["hhmm"] == "09:30", "open"].iloc[0]) if (r["hhmm"] == "09:30").any() else float(r["close"].iloc[0])
        return o, float(r["close"].dropna().iloc[-1])

    for d in sample:
        i = int(kept_pos[d])
        prev = pn["all_days"][i if same_day else i - 1]
        need(math.isclose(o_c(prev)[1], fa["CL"][i - 1], abs_tol=1e-9), f"[PIT] prior close at {pn['all_days'][i]}")
        if i >= 5:
            win = pn["all_days"][i - 5 + (1 if same_day else 0): i + (1 if same_day else 0)]
            ocs = np.array([o_c(x)[1] - o_c(x)[0] for x in win])
            need(math.isclose(math.sqrt(float(np.mean(ocs * ocs))), fa["s5"][i], rel_tol=1e-9),
                 f"[PIT] prior-5 RMS at {pn['all_days'][i]}")


def sign_audit(pn: dict[str, Any], b: dict[str, np.ndarray], sample: list[int], usd_pt: float) -> None:
    raw = pn["raw"]
    for d in sample:
        if b["side"][d] == 0:
            continue
        r = raw[raw["day"] == pn["days"][d]].set_index("hhmm").sort_index()
        m = T7.CLOCKS[int(b["first"][d])]
        if T7.hhmm(m - 1) not in r.index or not np.isfinite(r.at[T7.hhmm(m - 1), "close"]):
            continue  # the entry is the forward-filled close; D727's lag audit skips these the same way
        entry = float(r.at[T7.hhmm(m - 1), "close"])
        close = float(r["close"].dropna().loc[:"15:59"].iloc[-1])
        g = b["side"][d] * (close - entry) * usd_pt
        need(math.isclose(g, b["gross"][d], abs_tol=1e-6), f"[SIGN] {pn['days'][d]}: gross re-priced from raw differs")
        need((g > 0) == (b["side"][d] * (close - entry) > 0), "[SIGN] a favourable move does not pay positively")


# ================================================================================ run
def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists; step 1 is run once")
    t0 = time.time()
    import stage1_d711_f2_mechanism as M711
    cl = M711.cost_line("NQ")
    cost, usd_pt = float(cl["cost"]), float(cl["usd_per_point"])
    P(f"[D738] reading NQ minutes cut at {HI} ...")
    pn = T7.panel_from_raw("NQ", read_cut(DATA / "fixtures" / "fut_NQ_rth_1m.csv.gz"))
    ob = T7.objects(pn)
    days = pn["days"]
    Z.no_session_after(days, "the NQ panel")
    rng = np.random.default_rng(SEED)
    audits: dict[str, Any] = {}
    # 1 lag
    sample = [(int(rng.integers(0, len(days))), int(rng.integers(0, len(T7.CLOCKS)))) for _ in range(40)]
    T7.lag_audit(pn, ob, sample)
    try:
        T7.lag_audit(pn, ob, sample, shift=1)
    except T7.D727Error:
        audits["lag_canary"] = "fired"
    need(audits.get("lag_canary") == "fired", "the lag canary did not fire")
    # books and 4 right quantity
    bk = {k: book(pn, ob, k, usd_pt, cost) for k in KS}
    ref = json.loads((REPO / "data" / "stage0_d727_trend_curve.json").read_text(encoding="utf-8"))
    known_answers(bk, days, ref)
    wrong = {k: book(pn, ob, k, usd_pt, cost, close=pn["C"][:, 330 - 1]) for k in KS}
    try:
        known_answers(wrong, days, ref)
    except D738Error:
        audits["right_quantity_canary"] = "fired (the 15:00 close misses D727's answers)"
    need("right_quantity_canary" in audits, "the right-quantity canary did not fire")
    # panel variables, 2 point in time
    fa = full_day_arrays(pn)
    kept_pos = np.searchsorted(pn["all_days"], days)
    need(bool((pn["all_days"][kept_pos] == days).all()), "kept days are not in all_days")
    need(np.allclose(fa["s20"][kept_pos], pn["soc"], rtol=0, atol=1e-9), "sigma_oc differs from D727's")
    sd = [int(x) for x in rng.integers(300, len(days), 30)]
    pit_audit(pn, fa, kept_pos, sd)
    try:
        pit_audit(pn, fa, kept_pos, sd, same_day=True)
    except D738Error:
        audits["pit_canary"] = "fired (today's close read as yesterday's)"
    need("pit_canary" in audits, "the point-in-time canary did not fire")
    # 3 sign
    for k in (PRIMARY, POOL):
        sign_audit(pn, bk[k], [d for d in sd + [int(x) for x in rng.integers(0, len(days), 30)]], usd_pt)
    audits["sign"] = "60 trades re-priced from raw rows per book"
    prev = kept_pos - 1
    V_base = {"V1_sigma_usd": pn["soc"] * usd_pt, "V3_entry_clock_min": None,
              "V6_vol_trend_rms5_over_soc": fa["s5"][kept_pos] / pn["soc"], "V7_soc_pct_252": fa["pct"][kept_pos]}
    gap = (pn["O"] - fa["CL"][prev]) / pn["soc"]
    yday = (fa["CL"][prev] - fa["O"][prev]) / pn["soc"]
    # D691's frame, 5 the join
    P("[D738] building D691's NQ frame and IV under the lowered cut ...")
    tab, d691_info = d691_frame()
    joined = {c: tab[c].reindex(days).to_numpy(float) for c in tab.columns}
    js = rng.integers(0, len(days), 60)
    for c in tab.columns:
        join_audit(joined[c], tab[c], days, js)
    late = tab["V9_size_tier"].reindex(days).shift(1).to_numpy(float)
    try:
        join_audit(late, tab["V9_size_tier"], days, js)
    except D738Error:
        audits["join_canary"] = "fired (one session late)"
    need("join_canary" in audits, "the join canary did not fire")
    both = np.isfinite(late) & np.isfinite(joined["V9_size_tier"])
    audits["join_canary_changed_share"] = float((late[both] != joined["V9_size_tier"][both]).mean())
    audits["d691"] = d691_info
    res: dict[str, Any] = {"spec": "D738-STAGE-0-PRE-REG-the-oracle-of-an-expected-profit-filter-on-the-nq-follow.md",
                           "seal": f"nothing on or after {CUT24}; aggregates only", "days": int(len(days)),
                           "window": [str(days[0]), str(days[-1])], "cost_usd": cost, "usd_per_point": usd_pt,
                           "audits": audits, "coverage_d691": int(np.isfinite(joined["V9_size_tier"]).sum()),
                           "books": {}}
    for k in KS:
        b = bk[k]
        P(f"[D738] k {k}: prize ...")
        entry = {"prize": prize(b, days, cost, usd_pt, rng)}
        if k in (PRIMARY, POOL):
            V = dict(V_base)
            V["V2_abs_z"] = b["abs_z"]
            V["V3_entry_clock_min"] = np.where(b["first"] >= 0, np.array(T7.CLOCKS)[np.clip(b["first"], 0, None)], np.nan).astype(float)
            V["V4_gap_with_trade"] = b["side"] * gap
            V["V5_yday_with_trade"] = b["side"] * yday
            for c in V_D691:
                V[c] = joined[c]
            V["event"], V["opex"] = joined["event"], joined["opex"]
            entry["profile"] = profile(b, V, days)
        res["books"][str(k)] = entry
    res["wall_min"] = (time.time() - t0) / 60
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    p = res["books"][str(PRIMARY)]["prize"]
    P(f"[D738] k1.5 take-all {p['take_all']['total_net']:.0f}, oracle {p['oracle_net_gt_0']['net']:.0f}; "
      f"{res['wall_min']:.1f} min")
    return 0


# ================================================================================ selftest (synthetic only)
def selftest() -> int:
    rng = np.random.default_rng(1)
    v = rng.normal(size=2000)
    net = 5 * v + rng.normal(size=2000) * 10
    pr = profile_var(v, net, net + 4)
    need(pr["spearman_net"] > 0.3 and pr["quintiles"][-1]["mean_net"] > pr["quintiles"][0]["mean_net"],
         "profile_var misses a planted monotone relation")
    pr0 = profile_var(rng.normal(size=2000), net, net + 4)
    need(abs(pr0["spearman_net"]) < 0.1, "profile_var finds a relation in noise")
    print("  profile: a planted relation is found, noise reads ~0")
    days = np.array([f"{2016 + i // 250}-01-{1 + i % 28:02d}" for i in range(2000)])
    side = np.where(rng.random(2000) < 0.5, 1.0, 0.0)
    g = np.where(side != 0, rng.normal(10, 50, 2000), 0.0)
    b = {"side": side, "gross": g, "net": np.where(side != 0, g - 4.0, 0.0)}
    pz = prize(b, days, 4.0, 2.0, rng)
    tr = side != 0
    need(abs(pz["oracle_net_gt_0"]["net"] - b["net"][tr][b["net"][tr] > 0].sum()) < 1e-9, "the oracle net is wrong")
    need(pz["oracle_net_gt_0"]["net"] >= pz["take_all"]["total_net"], "the oracle is below take-all")
    c0 = pz["partial_oracle_curve"]["0.5"]
    need(c0[-1]["mean_net_per_trade"] > c0[0]["mean_net_per_trade"], "the partial-oracle curve does not rise")
    print("  prize: the oracle is the positive trades' sum and tops take-all; the curve rises from rho 0 to 1")
    tab = pd.Series([1.0, 2.0, 3.0], index=["a", "b", "c"])
    join_audit(np.array([1.0, 2.0, 3.0]), tab, np.array(["a", "b", "c"]), np.array([0, 1, 2]))
    try:
        join_audit(np.array([np.nan, 1.0, 2.0]), tab, np.array(["a", "b", "c"]), np.array([1, 2]))
    except D738Error:
        print("  fires: the join one session late")
    else:
        raise SystemExit("SELFTEST FAILED: the join canary did not fire")
    print("SELFTEST PASS (the lag, point-in-time, sign, right-quantity and D720 forecast/tier canaries run inside --run)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else run() if a.run else ap.print_help() or 2)
