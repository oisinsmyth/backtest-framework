"""D717 STAGE 0 -- the reversed flow rule: follow first-hour moves carried by MORE aggressive flow than their size
predicts (pushed), fade those carried by less (absorbed); 10:30 open -> 15:59 close, one micro. Primary on NQ (its flow
never read before), ES reported (selected by D715: not evidence). Design:
docs/decisions/D717-STAGE-0-DESIGN-the-reversed-flow-rule.md (f979337d, with the principal's prediction added before
this runner). The principal: "pre-reg, build and run a reversed rule test"; "insampel".

    uv run python scripts/stage0_d717_reversed_flow.py --selftest
    uv run python scripts/stage0_d717_reversed_flow.py --run --data-root "<main checkout>/data"

Per root: D715's candidate rules and walk_forward, unchanged; side = +sign(z) when R >= the prior-250 median of R
(pushed: follow), -sign(z) when R < it (absorbed: fade); no breadth. Gates G1-G5 on NQ (design s.4). Output
data/stage0_d717_reversed_flow.json.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d715_absorbed_morning as D715   # noqa: E402  (walk_forward and the statistics, unchanged)
import stage0_d688_gamma_close as S688         # noqa: E402

OUT = REPO / "data" / "stage0_d717_reversed_flow.json"
D715_JSON = REPO / "data" / "stage0_d715_absorbed_morning.json"
LO, HI = D715.LO, D715.HI
BARS, FIRST_HOUR, MIN_FLOW = D715.BARS, D715.FIRST_HOUR, D715.MIN_FLOW
P = D715.P


class D717Error(RuntimeError):
    pass


def load_root(data_root: Path, root: str, log=P) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """D715's candidate rules for any root (its load(), generalised; breadth not read)."""
    fx = data_root / "fixtures"
    sess = pd.read_csv(fx / "fut_index_sessions.csv.gz", usecols=["root", "day", "bars"], dtype={"root": str, "day": str}, encoding="utf-8")
    cal = set(sess[(sess["root"] == root) & (sess["bars"] >= 380) & (sess["day"] >= LO) & (sess["day"] <= HI)]["day"])
    b = pd.read_csv(fx / f"fut_{root}_rth_1m.csv.gz", usecols=["day", "hhmm", "contract", "open", "close"], dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
    b = b[(b["day"] >= LO) & (b["day"] <= HI)]
    D715.seal(b["day"], f"{root} bars")
    nb = b.groupby("day").size()
    days = np.array(sorted(d for d in cal if nb.get(d, 0) >= 380))
    b = b[b["day"].isin(set(days))]
    kb = b[b["hhmm"].isin(BARS)].pivot(index="day", columns="hhmm", values=["open", "close", "contract"]).reindex(days)
    s = pd.read_csv(fx / f"fut_{root}_signed_1m.csv.gz", usecols=["day", "hhmm", "contract", "volume", "buy", "sell"], dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
    s = s[(s["day"] >= LO) & (s["day"] <= HI) & s["hhmm"].isin(FIRST_HOUR)].copy()
    D715.seal(s["day"], f"{root} signed flow")
    s["contract"] = s["contract"].str[:-2] + s["contract"].str[-1]          # Sierra NQH16 -> the bars' NQH6
    D = pd.DataFrame(index=days)
    D["contract"] = kb[("contract", "09:30")]
    same = np.ones(len(days), bool)
    for h in BARS:
        same &= (kb[("contract", h)] == D["contract"]).to_numpy()
    D["one_contract"] = same
    D["P0930"] = kb[("open", "09:30")]; D["P1030"] = kb[("close", "10:29")]; D["entry"] = kb[("open", "10:30")]
    D["P1530"] = kb[("close", "15:29")]; D["exit"] = kb[("close", "15:59")]
    s = s.merge(D[["contract"]].rename(columns={"contract": "sc"}), left_on="day", right_index=True)
    s = s[s["contract"] == s["sc"]]
    fl = s.groupby("day").agg(n_min=("hhmm", "size"), vol=("volume", "sum"), buy=("buy", "sum"), sell=("sell", "sum")).reindex(days)
    D["flow_minutes"] = fl["n_min"].fillna(0).astype(int)
    D["I"] = (fl["buy"] - fl["sell"]) / fl["vol"]
    prev = D["contract"].shift(1)
    D["roll"] = (D["contract"] != prev) & prev.notna()
    ok = D["one_contract"] & ~D["roll"] & (D["flow_minutes"] >= MIN_FLOW) & np.isfinite(D[["P0930", "P1030", "entry", "P1530", "exit", "I"]].to_numpy(float)).all(1)
    C = D[ok].copy()
    C["m"] = np.log(C["P1030"].astype(float) / C["P0930"].astype(float))
    log(f"  {root}: {len(C)} candidates of {len(days)} sessions (roll {int(D['roll'].sum())}, mixed {int((~D['one_contract']).sum())}, flow < {MIN_FLOW} min {int((D['flow_minutes'] < MIN_FLOW).sum())})")
    return C, b, s


def build(C: pd.DataFrame, usd: float, cost: float) -> pd.DataFrame:
    wf = D715.walk_forward(C["m"].to_numpy(float), C["I"].to_numpy(float))
    for k, v in wf.items():
        C[k] = v
    s0 = np.sign(C["z"].to_numpy(float))
    C["s_follow"] = s0
    pushed = C["R"].to_numpy(float) >= C["med"].to_numpy(float)
    C["pushed"] = pushed
    C["s"] = np.where(pushed, s0, -s0)
    C["move"] = (C["exit"].astype(float) - C["entry"].astype(float)) * usd
    C["g_follow"] = s0 * C["move"]
    C["g"] = C["s"] * C["move"]
    C["net"] = C["g"] - cost
    C["bp"] = C["s"] * np.log(C["exit"].astype(float) / C["entry"].astype(float)) * 1e4
    C["g_last30"] = C["s"] * (C["exit"].astype(float) - C["P1530"].astype(float)) * usd
    return C


def analyse(C: pd.DataFrame, root: str, usd: float, cost: float, arm, rng) -> dict:
    post_fit = np.isfinite(C["R"].to_numpy(float)) & (C["s_follow"].to_numpy(float) != 0)
    rho, null = D715.spearman_rotation(C["R"].to_numpy(float)[post_fit], C["g_follow"].to_numpy(float)[post_fit])
    G1 = D715.blk(rho, null)
    post = post_fit & np.isfinite(C["med"].to_numpy(float))
    K = C[post]
    days_all = np.array(sorted(C.index))
    pushed = K["pushed"].to_numpy(bool)
    follow = K["g_follow"].to_numpy(float)
    g = K["g"].to_numpy(float)
    # G2's null: the follow/fade choice rotated across candidates, outcomes (the follow outcome) fixed
    flip = np.where(pushed, 1.0, -1.0)
    n = len(K)
    ks = np.arange(D715.ROT_MIN, n - D715.ROT_MIN + 1)
    e_obs = float((flip * follow).sum() / np.abs(flip * follow).sum())
    if not math.isclose(e_obs, float(g.sum() / np.abs(g).sum()), rel_tol=1e-12):
        raise D717Error("[RIGHT-QUANTITY] the rotation's offset 0 is not the book's efficiency")
    e_null = np.array([float((np.roll(flip, k) * follow).sum() / np.abs(follow).sum()) for k in ks])
    G2e = D715.blk(e_obs, e_null)

    def book(mask):
        x = K[mask]
        di = np.searchsorted(days_all, x.index.to_numpy())
        fg = D715.Q.four_groups(x["g"].to_numpy(float), x["net"].to_numpy(float), di, x["s"].to_numpy(float), days_all, len(days_all), arm, cost)
        return {"trades": int(mask.sum()), "mean_gross": float(x["g"].mean()), "t_gross_nw": D715.nw_t(x["g"]), "mean_net": float(x["net"].mean()),
                "t_net_nw": D715.nw_t(x["net"]), "median_net": float(x["net"].median()), "win": float((x["net"] > 0).mean()),
                "mean_bp": float(x["bp"].mean()), "four_groups": fg}
    ones = np.ones(n, bool)
    books = {"two_sided_reversed": book(ones), "pushed_follow": book(pushed), "absorbed_fade": book(~pushed)}
    yr = K.index.str[:4]
    by_year = K.groupby(yr)["net"].agg(["count", "sum", "mean"])
    tot = float(K["net"].sum())
    elig = by_year[by_year["count"] >= 10]
    mu = K.groupby(yr)["move"].mean()
    T = float((K["s"] * (K["move"] - mu.reindex(yr).to_numpy())).mean())
    tb = books["two_sided_reversed"]
    gates = {
        "G1_mechanism": {**G1, "n": int(post_fit.sum()), "pass": bool(G1["observed"] > 0 and G1["above_p95"])},
        "G2_edge": {"mean_net": tb["mean_net"], "t_net_nw": tb["t_net_nw"], "efficiency": G2e,
                    "pass": bool(tb["mean_net"] > 0 and tb["t_net_nw"] >= 2.0 and G2e["above_p95"])},
        "G3_both_halves": {"pushed_follow_gross": books["pushed_follow"]["mean_gross"], "absorbed_fade_gross": books["absorbed_fade"]["mean_gross"],
                           "pass": bool(books["pushed_follow"]["mean_gross"] > 0 and books["absorbed_fade"]["mean_gross"] > 0)},
        "G4_not_one_episode": {"ex_2020_mean_net": float(K.loc[yr != "2020", "net"].mean()), "ex_2022_mean_net": float(K.loc[yr != "2022", "net"].mean()),
                               "largest_year_share": (float(by_year["sum"].max() / tot) if tot > 0 else None), "years_eligible": int(len(elig)),
                               "years_positive": int((elig["sum"] > 0).sum()),
                               "by_year": {k: {"n": int(r["count"]), "net": float(r["sum"]), "mean": float(r["mean"])} for k, r in by_year.iterrows()}},
        "G5_beyond_drift": {"T": T, "pass": bool(T > 0)},
    }
    g4 = gates["G4_not_one_episode"]
    g4["pass"] = bool(g4["ex_2020_mean_net"] > 0 and g4["ex_2022_mean_net"] > 0 and tot > 0 and g4["largest_year_share"] <= 0.5 and 2 * g4["years_positive"] >= g4["years_eligible"])
    p = {k: v["pass"] for k, v in gates.items()}
    if all(p.values()):
        reading = "PASS"
    elif not p["G1_mechanism"]:
        reading = "NEITHER"
    elif p["G3_both_halves"] and tb["mean_gross"] > 0 and tb["t_gross_nw"] >= 2.0:
        reading = "MECHANISM ONLY"
    else:
        reading = "FAIL"
    q = pd.qcut(pd.Series(C["R"].to_numpy(float)[post_fit]), 5, labels=False).to_numpy()
    gf = C["g_follow"].to_numpy(float)[post_fit]
    quint = {int(k): {"n": int((q == k).sum()), "mean_follow_gross": float(gf[q == k].mean())} for k in range(5)}
    ls = {sd: {"n": int((K["s"] == v).sum()), "mean_net": float(K.loc[K["s"] == v, "net"].mean())} for sd, v in (("long", 1.0), ("short", -1.0))}
    pt = pd.qcut(K["entry"].astype(float), 3, labels=False)
    return {"root": root, "usd_per_point": usd, "cost_rt": cost, "counts": {"candidates": int(len(C)), "post_fit": int(post_fit.sum()), "post_median": int(post.sum()),
            "first_trade_day": str(K.index[0]) if len(K) else None, "pushed_share": float(pushed.mean())},
            "gates": gates, "reading": reading, "books": books, "R_quintiles_follow_gross_0_most_absorbed": quint, "long_short": ls,
            "price_tercile_mean_net": {int(k): float(K["net"][pt == k].mean()) for k in range(3)},
            "share_of_gross_15_30_to_16_00": float(K["g_last30"].sum() / K["g"].sum()) if K["g"].sum() != 0 else None,
            "_daily_net": pd.Series(K["net"].to_numpy(float), index=K.index)}


def nq_f2_daily(data_root: Path) -> pd.Series:
    import vault_d716_nq_f2 as N
    N.M.FIX = Path(data_root) / "fixtures"
    bd = N.build()
    sn, Fn, net = bd["sn"], bd["Fn"], bd["net"]
    own = Fn["take"] & Fn["window"] & (sn <= N.IN_END)
    if int(own.sum()) != N.KNOWN_NQ["trades"] or abs(float(net[own].mean()) - N.KNOWN_NQ["mean_net"]) > 1e-9:
        raise D717Error("[NQ F2] D711/D716's NQ book not reproduced")
    return pd.Series(np.where(own, net, 0.0)[Fn["window"]], index=sn[Fn["window"]])


def run(data_root: Path, log=P) -> int:
    t0 = time.time()
    D715.sign_audit()
    E = S688.d685()
    arm = E.load_arm()
    rng = np.random.default_rng(717)
    out = {"spec": "D717 STAGE 0 (in-sample 2016-2023): the reversed flow rule; NQ primary, ES reported (selected by D715: not evidence)",
           "design_commit": "f979337d"}
    res = {}
    for root in ("NQ", "ES"):
        cs = E.cost_spec(root, "micro")
        C, b, s = load_root(data_root, root, log)
        C = build(C, cs["usd_per_point"], cs["cost_rt_usd"])
        post = np.flatnonzero(np.isfinite(C["med"].to_numpy(float)))
        s_aud = s.copy()
        D715.lag_audit(C, b, s_aud, rng.choice(post, 40, replace=False), log)
        if root == "ES":
            want = json.loads(D715_JSON.read_text(encoding="utf-8"))
            r_es, _ = D715.spearman_rotation(-C["R"].to_numpy(float)[np.isfinite(C["R"]) & (C["s_follow"] != 0)], C["g_follow"].to_numpy(float)[np.isfinite(C["R"]) & (C["s_follow"] != 0)])
            if len(C) != 1961 or not math.isclose(r_es, want["gates"]["G1_mechanism"]["observed"], rel_tol=1e-12):
                raise D717Error(f"[REPRO] ES does not reproduce D715: {len(C)} candidates, rho {r_es!r}")
            log(f"  ES reproduces D715: 1,961 candidates, rho(absorption) {r_es:+.6f}")
        pushed_share = C["pushed"][np.isfinite(C["med"])].mean()
        if not 0.45 < pushed_share < 0.55:
            raise D717Error(f"[RIGHT-QUANTITY] {root}: pushed share {pushed_share:.3f}")
        res[root] = analyse(C, root, cs["usd_per_point"], cs["cost_rt_usd"], arm, rng)
        g, bk = res[root]["gates"], res[root]["books"]["two_sided_reversed"]
        log(f"  {root}: G1 rho {g['G1_mechanism']['observed']:+.4f} (p95 {g['G1_mechanism']['p95']:+.4f}, pct {g['G1_mechanism']['pct_rank']:.3f}); "
            f"book {bk['trades']} trades gross ${bk['mean_gross']:+.2f} (t {bk['t_gross_nw']:+.2f}) net ${bk['mean_net']:+.2f} (t {bk['t_net_nw']:+.2f}) "
            f"{bk['mean_bp']:+.2f} bp; eff pct {g['G2_edge']['efficiency']['pct_rank']:.3f}; G3 {g['G3_both_halves']['pass']} G4 {g['G4_not_one_episode']['pass']} "
            f"G5 {g['G5_beyond_drift']['pass']} -> {res[root]['reading']}")
    # the pooled two-root book (reported), the correlations and the principal's prediction
    dn, de = res["NQ"].pop("_daily_net"), res["ES"].pop("_daily_net")
    pooled = dn.add(de, fill_value=0.0)
    out["pooled_two_root_daily"] = {"days": int(len(pooled)), "mean": float(pooled.mean()), "sharpe_daily_ann": float(pooled.mean() / pooled.std(ddof=1) * math.sqrt(252))}
    f2 = nq_f2_daily(data_root)
    cmn = dn.index.intersection(f2.index)
    allNQ = pd.Series(0.0, index=f2.index).add(dn, fill_value=0.0).reindex(f2.index)
    out["rho_NQ_daily_net_with_NQ_F2"] = {"rho": float(np.corrcoef(allNQ, f2)[0, 1]), "days": int(len(f2)), "overlap_trade_days": int(len(cmn))}
    nq, es = res["NQ"]["books"]["two_sided_reversed"], res["ES"]["books"]["two_sided_reversed"]
    out["P_principal"] = {"prediction": "NQ's reversed book beats ES's on mean gross AND mean net a trade, in dollars at one micro",
                          "NQ_gross": nq["mean_gross"], "ES_gross": es["mean_gross"], "NQ_net": nq["mean_net"], "ES_net": es["mean_net"],
                          "NQ_bp": nq["mean_bp"], "ES_bp": es["mean_bp"],
                          "held": bool(nq["mean_gross"] > es["mean_gross"] and nq["mean_net"] > es["mean_net"]),
                          "held_in_bp": bool(nq["mean_bp"] > es["mean_bp"])}
    out["roots"] = res
    out["reading_NQ_primary"] = res["NQ"]["reading"]
    out["timing_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(out, indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x)) + "\n", encoding="utf-8", newline="\n")
    log(f"  P-principal held {out['P_principal']['held']} (NQ ${nq['mean_gross']:+.2f}/${nq['mean_net']:+.2f} vs ES ${es['mean_gross']:+.2f}/${es['mean_net']:+.2f}); "
        f"rho with NQ F2 {out['rho_NQ_daily_net_with_NQ_F2']['rho']:+.3f}")
    log(f"  READING (NQ, the primary): {out['reading_NQ_primary']}  ({out['timing_s']} s)")
    return 0


def selftest() -> int:
    D715.sign_audit()
    rng = np.random.default_rng(7170)
    n = 1400
    m = rng.normal(0, 0.004, n)
    I = 0.02 * m / 0.004 + rng.normal(0, 0.05, n)
    wf = D715.walk_forward(m, I)
    ok = np.isfinite(wf["R"])
    follow = wf["R"] * 400 + rng.normal(0, 60, n)            # the reversed mechanism: pushed (high R) continues
    rho, null = D715.spearman_rotation(wf["R"][ok], follow[ok])
    if not D715.blk(rho, null)["above_p95"]:
        raise SystemExit("selftest: a planted reversed effect failed G1")
    fails = sum(not D715.blk(*D715.spearman_rotation(wf["R"][ok], rng.normal(0, 60, n)[ok]))["above_p95"] for _ in range(40))
    if fails < 33:
        raise SystemExit(f"selftest: noise passed G1 {40 - fails} of 40 times")
    s0 = np.sign(m); pushed = wf["R"] >= wf["med"]
    side = np.where(pushed, s0, -s0)
    if not np.array_equal(side[~pushed & np.isfinite(wf["med"])], -s0[~pushed & np.isfinite(wf["med"])]):
        raise SystemExit("selftest: the side does not flip exactly on the absorbed half")
    for s_, mv in ((1.0, 2.0), (-1.0, -2.0)):
        if not s_ * mv > 0:
            raise SystemExit("selftest: sign audit")
    print(f"SELFTEST OK: a planted reversed effect passes G1; noise failed G1 {fails}/40; the side flips exactly on the absorbed half; D715's audits reused")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    sys.exit(run(a.data_root) if a.run else 1)
