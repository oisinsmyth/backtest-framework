"""D497 -- open interest against price, the four-quadrant read. Signal s = sign(dPrice) x sign(dOI) over the open interest's own
reference session, traded on the NEXT day session 10:00 -> 16:00 ET, one round trip, one micro, $3 + 1.009 ticks. Four declared
cells (ES, NQ, CL, GC), exact rotation (N1) and common-offset family maximum (N2), plus C1 (cleared volume replaces open interest)
and C2 (price only). Spec ab8b5df; fixture scripts/build_fut_open_interest.py.

    python scripts/run_d497_open_interest.py --selftest
    python scripts/run_d497_open_interest.py --run [--out data/d497_open_interest.json]
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
HOURLY = REPO / "data" / "fixtures" / "fut_sessions_hourly.csv.gz"
OI = REPO / "data" / "fixtures" / "fut_open_interest_daily.csv.gz"
SPECS = REPO / "data" / "futures_contract_specs.json"
IS = ("2016-01-04", "2023-12-29")
ROOTS = ("ES", "NQ", "CL", "GC"); MICRO = {"ES": "MES", "NQ": "MNQ", "CL": "MCL", "GC": "MGC"}
COMMISSION_RT = 3.00; CROSS_TICKS = 1.009
ENTRY, EXIT = "h09_c", "h15_c"


def load(root):
    """Per session: the day-leg move, and the open-interest / cleared-volume changes over the figure's OWN reference session."""
    T = pd.read_csv(HOURLY, usecols=["root", "day", "same_front", ENTRY, EXIT], dtype={"root": str, "day": str})
    T = T[(T["root"] == root) & T["same_front"] & (T[ENTRY] > 0) & (T[EXIT] > 0)].sort_values("day")
    T = T.set_index("day"); close = T[EXIT]
    O = pd.read_csv(OI, dtype={"root": str, "session": str, "ref_session": str})
    O = O[(O["root"] == root) & O["oi_total"].notna()].sort_values("session").set_index("session")
    j = pd.concat([T[[ENTRY, EXIT]], O[["oi_total", "cv_total", "ref_session", "staleness_sessions"]]], axis=1, join="inner")
    j = j[(j.index >= IS[0]) & (j.index <= IS[1])]
    j["ref_prev"] = j["ref_session"].shift(1); j["oi_prev"] = j["oi_total"].shift(1); j["cv_prev"] = j["cv_total"].shift(1)
    # the price change over the SAME span the open-interest change covers: close(ref) - close(ref_prev)
    j["c_ref"] = close.reindex(j["ref_session"]).to_numpy(); j["c_ref_prev"] = close.reindex(j["ref_prev"]).to_numpy()
    j["d_price"] = j["c_ref"] - j["c_ref_prev"]; j["d_oi"] = j["oi_total"] - j["oi_prev"]; j["d_cv"] = j["cv_total"] - j["cv_prev"]
    j["move"] = j[EXIT] - j[ENTRY]
    stale_repeat = int((j["ref_session"] == j["ref_prev"]).sum())
    j = j[(j["ref_session"] != j["ref_prev"]) & j["d_price"].notna() & j["d_oi"].notna() & j["move"].notna()]
    return j, stale_repeat


def usd(root, specs):
    m = specs[MICRO[root]]; return m["usd_per_point"], COMMISSION_RT + CROSS_TICKS * m["tick_usd"]


def signal(d_price, d_x):
    return np.sign(d_price) * np.sign(d_x)


def pnl_vec(s, move, u, cost):
    return np.where(s == 0, 0.0, s * move * u - np.where(s == 0, 0.0, cost))


def pnl_loop(s, move, u, cost):
    out = np.empty(len(s))
    for i in range(len(s)):
        out[i] = 0.0 if s[i] == 0 else s[i] * move[i] * u - cost
    return out


def block_se(x, sess, n_boot=2000, seed=497):
    mon = np.array([q[:7] for q in sess]); keys, inv = np.unique(mon, return_inverse=True)
    sums = np.bincount(inv, weights=x); cnts = np.bincount(inv); rng = np.random.default_rng(seed); m = np.empty(n_boot)
    for b in range(n_boot):
        p = rng.integers(0, keys.size, keys.size); m[b] = sums[p].sum() / cnts[p].sum()
    return float(m.std(ddof=1))


def stats_of(s, move, sess, u, cost, label):
    g = pnl_vec(s, move, u, cost); tr = s != 0; x = g[tr]
    k = max(int(round(0.01 * len(x))), 1); srt = np.sort(x)
    return dict(cell=label, n=int(len(s)), n_traded=int(tr.sum()), mean_usd=float(x.mean()), se_usd=block_se(x, np.asarray(sess)[tr]),
                gross_usd=float((s[tr] * move[tr] * u).mean()), median=float(np.median(x)), hit=float((x > 0).mean()), trim1=float(srt[k:-k].mean()),
                worst=float(x.min()), worst_session=str(np.asarray(sess)[tr][int(x.argmin())]), cost_usd=cost, usd_per_point=u)


def quadrants(d_price, d_oi, move, u):
    out = {}
    for name, m in (("price up, OI up", (d_price > 0) & (d_oi > 0)), ("price up, OI down", (d_price > 0) & (d_oi < 0)),
                    ("price down, OI up", (d_price < 0) & (d_oi > 0)), ("price down, OI down", (d_price < 0) & (d_oi < 0))):
        out[name] = dict(n=int(m.sum()), mean_move_usd=float(move[m].mean() * u) if m.any() else None)
    return out


def rot_null(s, move, u, cost):
    T = len(s); return np.array([pnl_vec(np.roll(s, k), move, u, cost)[np.roll(s, k) != 0].mean() for k in range(1, T)])


def run(out):
    t0 = time.time(); specs = json.loads(SPECS.read_text())
    res = dict(spec="ab8b5df", window=IS, cells={}, controls={}, quadrants={}, nulls={}, audits={}, stale_repeats={})
    series = {}
    print(f"D497 -- open interest against price, {IS[0]}..{IS[1]}, one micro, $3 + 1.009 ticks\n", flush=True)
    for root in ROOTS:
        j, rep = load(root); u, cost = usd(root, specs); res["stale_repeats"][root] = rep
        dp = j["d_price"].to_numpy(); doi = j["d_oi"].to_numpy(); dcv = j["d_cv"].to_numpy(); mv = j["move"].to_numpy(); sess = j.index.to_numpy()
        s = signal(dp, doi)
        res["cells"][root] = stats_of(s, mv, sess, u, cost, root)
        res["controls"][f"{root} C1 volume"] = stats_of(signal(dp, dcv), mv, sess, u, cost, f"{root} C1")
        res["controls"][f"{root} C2 price only"] = stats_of(np.sign(dp), mv, sess, u, cost, f"{root} C2")
        res["quadrants"][root] = quadrants(dp, doi, mv, u)
        series[root] = (s, mv, u, cost, sess)
        assert np.allclose(pnl_vec(s, mv, u, cost), pnl_loop(s, mv, u, cost)), f"[M] {root}"
        c = res["cells"][root]; c1 = res["controls"][f"{root} C1 volume"]; c2 = res["controls"][f"{root} C2 price only"]
        print(f"  {root}: n {c['n']:,} ({c['n_traded']:,} traded, {rep} stale repeats)  mean {c['mean_usd']:+7.2f} +- {c['se_usd']:.2f}  gross {c['gross_usd']:+7.2f}  median {c['median']:+7.2f}  hit {c['hit']:.3f}  trim1 {c['trim1']:+7.2f}  worst {c['worst']:,.0f} ({c['worst_session']})", flush=True)
        print(f"       C1 cleared volume {c1['mean_usd']:+7.2f} +- {c1['se_usd']:.2f}   C2 price only {c2['mean_usd']:+7.2f} +- {c2['se_usd']:.2f}", flush=True)
    # nulls
    Tmin = min(len(series[r][0]) for r in ROOTS); fam = np.full(Tmin - 1, -np.inf)
    for root in ROOTS:
        s, mv, u, cost, sess = series[root]; nl = rot_null(s, mv, u, cost)
        res["nulls"][root] = dict(p50=float(np.quantile(nl, .5)), p95=float(np.quantile(nl, .95)), n=int(nl.size), observed=res["cells"][root]["mean_usd"], above_p95=bool(res["cells"][root]["mean_usd"] > np.quantile(nl, .95)))
        fam = np.maximum(fam, nl[:Tmin - 1])
        print(f"  N1 {root}: p50 {np.quantile(nl,.5):+6.2f}  p95 {np.quantile(nl,.95):+6.2f}  observed {res['cells'][root]['mean_usd']:+6.2f}  above p95 {res['nulls'][root]['above_p95']}", flush=True)
    res["nulls"]["family_max"] = dict(p50=float(np.quantile(fam, .5)), p95=float(np.quantile(fam, .95)), n_offsets=int(Tmin - 1))
    fp = res["nulls"]["family_max"]["p95"]; print(f"  N2 family max over {len(ROOTS)} roots ({Tmin-1} common offsets): p50 {np.quantile(fam,.5):+.2f}  p95 {fp:+.2f}")
    picks = []
    for root in ROOTS:
        c = res["cells"][root]; c1 = res["controls"][f"{root} C1 volume"]; c2 = res["controls"][f"{root} C2 price only"]
        ok = bool(c["mean_usd"] > 0 and res["nulls"][root]["above_p95"] and c["mean_usd"] > fp and c["mean_usd"] > c1["mean_usd"] + c1["se_usd"] and c["mean_usd"] > c2["mean_usd"] + c2["se_usd"])
        c["pick"] = ok
        if ok:
            picks.append(root)
    res["picks"] = picks; print(f"  picks: {picks or 'none'}")
    print("\n  quadrant mean day-session move, $ at one micro (descriptive):")
    for root in ROOTS:
        print(f"    {root}: " + "  ".join(f"{k} n{v['n']} {v['mean_move_usd']:+.1f}" for k, v in res["quadrants"][root].items()))
    # audits
    s, mv, u, cost, sess = series["ES"]
    res["audits"] = dict(M=True, S=bool(pnl_vec(np.array([1.0]), np.array([2.0]), 5.0, 0.0)[0] == 10.0 and pnl_vec(np.array([-1.0]), np.array([2.0]), 5.0, 0.0)[0] == -10.0),
                         X_flip_oi=bool(abs(pnl_vec(-s, mv, u, 0.0)[s != 0].mean() + pnl_vec(s, mv, u, 0.0)[s != 0].mean()) < 1e-9),
                         D_window=bool(max(sess) <= IS[1]), F_causal="every input is the fixture's usable-session row, gated by O1 (published before 10:00 ET); the entry is the 10:00 print")
    print(f"  audits: {res['audits']}")
    res["wall_min"] = round((time.time() - t0) / 60, 1); Path(out).write_text(json.dumps(res, indent=1, default=float)); print(f"\nwrote {out} in {res['wall_min']} min")


def selftest():
    rng = np.random.default_rng(497); n = 800
    dp = rng.normal(size=n); doi = rng.normal(size=n); mv = rng.normal(size=n); sess = np.array([str(d)[:10] for d in pd.bdate_range("2016-01-04", periods=n)])
    s = signal(dp, doi)
    assert np.allclose(pnl_vec(s, mv, 5.0, 3.0), pnl_loop(s, mv, 5.0, 3.0)), "[M]"
    assert pnl_vec(np.array([1.0]), np.array([2.0]), 5.0, 0.0)[0] == 10.0 and pnl_vec(np.array([-1.0]), np.array([2.0]), 5.0, 0.0)[0] == -10.0, "[S]"
    assert abs(pnl_vec(-s, mv, 5.0, 0.0).mean() + pnl_vec(s, mv, 5.0, 0.0).mean()) < 1e-9, "[X]"
    nl = rot_null(s, mv, 5.0, 0.0); assert abs(np.median(nl)) < 0.2, np.median(nl)
    planted = mv + 0.8 * s; obs = pnl_vec(s, planted, 5.0, 0.0)[s != 0].mean()
    assert obs > np.quantile(rot_null(s, planted, 5.0, 0.0), .95), "a planted edge must clear its own rotation p95"
    z = signal(np.array([1.0, 0.0, -1.0]), np.array([0.0, 1.0, -1.0])); assert list(z) == [0.0, 0.0, 1.0], list(z)
    assert pnl_vec(np.array([0.0]), np.array([5.0]), 5.0, 3.0)[0] == 0.0, "a zero signal must not be charged cost"
    print("selftest OK: [M] vec==loop, [S] sign in money, [X] flip negates, rotation centred, planted edge detected, zero-signal sessions are no-trade")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--run", action="store_true"); ap.add_argument("--out", default=str(REPO / "data" / "d497_open_interest.json")); a = ap.parse_args()
    if a.selftest:
        selftest()
    if a.run:
        run(a.out)
