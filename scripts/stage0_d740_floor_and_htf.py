"""D740 Stage 0: a fixed volatility floor (A), agreement with the 20-day SMA's three-day direction (B), and both (C), on
D727's k 1.5 NQ follow (docs/decisions/D740-STAGE-0-PRE-REG-a-volatility-floor-and-trend-agreement.md).

    uv run python scripts/stage0_d740_floor_and_htf.py --selftest    # synthetic only
    uv run python scripts/stage0_d740_floor_and_htf.py --run         # once -> data/stage0_d740_floor_and_htf.json

The trades come through D738 step 1's functions (a chunked read cut at 2023-12-29, D727's panel and book) and are
checked against D727's recorded answers. Both filters are fixed rules: no fit, no burn-in. Nulls: the exact time
rotation of each take mask (S1 mean net, S2 mean pass-through y = gross / sigma$) and a within-year permutation.
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
import stage0_d738_follow_oracle as S1  # noqa: E402
import stage0_d738_step3_filters as S3  # noqa: E402

OUT = REPO / "data" / "stage0_d740_floor_and_htf.json"
K = 1.5
FLOOR_USD = 150.0
SMA_N, RUN = 20, 3
N_PERM, SEED = 10_000, 740
P = Z.P


class D740Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D740Error(msg)


# ================================================================================ the higher time frame
def continuous(O: np.ndarray, CL: np.ndarray, con: np.ndarray) -> np.ndarray:
    """Cumulative daily change: close-to-close within a contract; a roll day's own open-to-close (drops the roll gap)."""
    chg = np.zeros(len(CL))
    same = con[1:] == con[:-1]
    chg[1:] = np.where(same, CL[1:] - CL[:-1], CL[1:] - O[1:])
    return np.cumsum(chg)


def htf_state(c: np.ndarray, a: np.ndarray, shift: int = 0) -> np.ndarray:
    """+1 UP / -1 DOWN / 0 MIXED at session index a, from closes through a-1 (shift = 1 reads session a: the canary).
    UP iff SMA20 rose on each of a-1, a-2, a-3, i.e. c[d] > c[d-20] for d in a-1..a-3."""
    out = np.zeros(len(a))
    ok = a - RUN - SMA_N + shift >= 0
    for i in np.flatnonzero(ok):
        d = [a[i] - j + shift for j in range(1, RUN + 1)]
        diff = np.array([c[x] - c[x - SMA_N] for x in d])
        out[i] = 1.0 if (diff > 0).all() else -1.0 if (diff < 0).all() else 0.0
    out[~ok] = np.nan
    return out


def htf_audit(pn: dict[str, Any], a: np.ndarray, state: np.ndarray, sample: list[int], shift: int = 0) -> int:
    """Second implementation from the raw rows: each day's contract, 09:30 open and last close <= 15:59, re-chained over
    the 23 sessions before a. Returns how many sampled states differ (the run requires 0; the canary requires > 0)."""
    raw = pn["raw"]
    by = {d: g.sort_values("hhmm") for d, g in raw.groupby("day")}
    days = pn["all_days"]
    bad = 0
    for i in sample:
        ai = int(a[i]) + shift
        if ai - RUN - SMA_N < 1 or not np.isfinite(state[i]):
            continue
        win = range(ai - RUN - SMA_N, ai)
        o, cl, cn = {}, {}, {}
        for x in [ai - RUN - SMA_N - 1, *win]:
            r = by[days[x]]
            o[x] = float(r.loc[r["hhmm"] == "09:30", "open"].iloc[0]) if (r["hhmm"] == "09:30").any() else float(r["close"].iloc[0])
            cl[x] = float(r["close"].dropna().iloc[-1])
            cn[x] = r["contract"].value_counts().index[0]
        cc = {ai - RUN - SMA_N - 1: 0.0}
        for x in win:
            cc[x] = cc[x - 1] + (cl[x] - cl[x - 1] if cn[x] == cn[x - 1] else cl[x] - o[x])
        diff = np.array([cc[ai - j] - cc[ai - j - SMA_N] for j in range(1, RUN + 1)])
        s = 1.0 if (diff > 0).all() else -1.0 if (diff < 0).all() else 0.0
        bad += int(s != state[i])
    return bad


# ================================================================================ nulls
def rotation2(take: np.ndarray, net: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    n = len(take)
    s1, s2 = np.empty(n), np.empty(n)
    for o in range(n):
        m = np.roll(take, o)
        s1[o], s2[o] = net[m].mean(), y[m].mean()
    return {k: {"observed": float(s[0]), "p": float(np.mean(s >= s[0])), "null_p50": float(np.percentile(s[1:], 50)),
                "null_p95": float(np.percentile(s[1:], 95)), "offsets": n} for k, s in (("S1_mean_net", s1), ("S2_mean_y", s2))}


def within_year(take: np.ndarray, net: np.ndarray, y: np.ndarray, years: np.ndarray, rng: np.random.Generator) -> dict[str, Any]:
    s1 = np.zeros(N_PERM)
    s2 = np.zeros(N_PERM)
    kept = 0
    for yr in np.unique(years):
        idx = np.flatnonzero(years == yr)
        m = int(take[idx].sum())
        if m == 0:
            continue
        keys = rng.random((N_PERM, len(idx)))
        pick = np.argsort(keys, axis=1)[:, :m]
        s1 += net[idx][pick].sum(axis=1)
        s2 += y[idx][pick].sum(axis=1)
        kept += m
    s1, s2 = s1 / kept, s2 / kept
    o1, o2 = float(net[take].mean()), float(y[take].mean())
    return {"S1_mean_net": {"observed": o1, "p": float((np.sum(s1 >= o1) + 1) / (N_PERM + 1)), "null_p50": float(np.percentile(s1, 50)),
                            "null_p95": float(np.percentile(s1, 95))},
            "S2_mean_y": {"observed": o2, "p": float((np.sum(s2 >= o2) + 1) / (N_PERM + 1)), "null_p50": float(np.percentile(s2, 50)),
                          "null_p95": float(np.percentile(s2, 95))}, "draws": N_PERM}


# ================================================================================ run
def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists; D740 is run once")
    t0 = time.time()
    import stage1_d711_f2_mechanism as M711
    cl = M711.cost_line("NQ")
    cost, usd = float(cl["cost"]), float(cl["usd_per_point"])
    pn = T7.panel_from_raw("NQ", S1.read_cut(S1.DATA / "fixtures" / "fut_NQ_rth_1m.csv.gz"))
    ob = T7.objects(pn)
    days = pn["days"]
    Z.no_session_after(days, "the NQ panel")
    rng = np.random.default_rng(SEED)
    smp = [(int(rng.integers(0, len(days))), int(rng.integers(0, len(T7.CLOCKS)))) for _ in range(40)]
    T7.lag_audit(pn, ob, smp)
    try:
        T7.lag_audit(pn, ob, smp, shift=1)
        raise D740Error("the lag canary did not fire")
    except T7.D727Error:
        pass
    bk = {k: S1.book(pn, ob, k, usd, cost) for k in S1.KS}
    S1.known_answers(bk, days, json.loads((REPO / "data" / "stage0_d727_trend_curve.json").read_text(encoding="utf-8")))
    b = bk[K]
    # the higher time frame, on every session
    con = pn["raw"].groupby("day")["contract"].agg(lambda s: s.value_counts().index[0]).reindex(pn["all_days"]).to_numpy(str)
    c = continuous(pn["all_O"], pn["all_C_last"], con)
    a = np.searchsorted(pn["all_days"], days)
    need(bool((pn["all_days"][a] == days).all()), "kept days are not in all_days")
    state = htf_state(c, a)
    sam = [int(x) for x in rng.integers(30, len(days), 40)]
    need(htf_audit(pn, a, state, sam) == 0, "[PIT] the second implementation disagrees with the HTF state")
    canary = htf_audit(pn, a, state, sam, shift=1)  # the stored state against a re-chain that reads session t's close
    need(canary > 0, "[PIT] the canary (session t's own close) did not change any state")
    S1.sign_audit(pn, b, [int(x) for x in rng.integers(0, len(days), 40)], usd)
    # trades on the window (HTF defined)
    tr = (b["side"] != 0) & np.isfinite(state)
    ti = np.flatnonzero(tr)
    win_day = days >= days[ti[0]]
    side, net, gross = b["side"][ti], b["net"][ti], b["gross"][ti]
    sig = pn["soc"][ti] * usd
    y = gross / sig
    st = state[ti]
    years = np.array([d[:4] for d in days[ti]])
    masks = {"A_FLOOR": sig >= FLOOR_USD, "B_HTF_AGREE": side == st, "C_BOTH": (sig >= FLOOR_USD) & (side == st)}
    beside = {"against_trend": (st != 0) & (side == -st), "mixed": st == 0}
    x = gross
    e = x - x.mean()
    v = e @ e / len(x)
    for L in range(1, 6):
        v += 2 * (1 - L / 6) * (e[L:] @ e[:-L]) / len(x)
    g1 = {"mean_gross": float(x.mean()), "nw_t": float(x.mean() / math.sqrt(v / len(x)))}
    g1["holds"] = bool(g1["mean_gross"] > 0 and g1["nw_t"] >= 2)
    wd = days[win_day]

    def daily(m: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        nd, gd, kd = np.zeros(len(days)), np.zeros(len(days)), np.zeros(len(days), bool)
        sel = ti[m]
        nd[sel], gd[sel], kd[sel] = b["net"][sel], b["gross"][sel], True
        return nd[win_day], gd[win_day], kd[win_day]

    out: dict[str, Any] = {"spec": "D740-STAGE-0-PRE-REG-a-volatility-floor-and-trend-agreement.md",
                           "seal": f"nothing on or after {Z.CUT24}; aggregates only", "cost": cost, "floor_usd": FLOOR_USD,
                           "window": [str(days[ti[0]]), str(days[ti[-1]])], "window_trades": int(len(ti)),
                           "window_sessions": int(win_day.sum()), "trades_without_htf_state": int(((b["side"] != 0) & ~np.isfinite(state)).sum()),
                           "htf_state_counts_on_trades": {"UP": int((st == 1).sum()), "DOWN": int((st == -1).sum()), "MIXED": int((st == 0).sum())},
                           "pit_canary_states_changed": canary, "gate1": g1}
    nd, gd, kd = daily(np.ones(len(ti), bool))
    out["take_all"] = S3.report(nd, gd, kd, wd, net)
    out["take_all"]["mean_y"] = float(y.mean())
    ta = float(net.mean())
    out["filters"], pv = {}, {}
    for f, m in {**masks, **beside}.items():
        nd, gd, kd = daily(m)
        rep = S3.report(nd, gd, kd, wd, net[m])
        F = {"kept": int(m.sum()), "kept_share": float(m.mean()), "book": rep, "mean_y_kept": float(y[m].mean()),
             "mean_y_dropped": float(y[~m].mean()) if (~m).any() else None, "mean_net_dropped": float(net[~m].mean()) if (~m).any() else None}
        if f in masks:
            F["rotation"] = rotation2(m, net, y)
            F["within_year"] = within_year(m, net, y, years, rng)
            if f != "A_FLOOR":
                pv[f] = F["rotation"]["S1_mean_net"]["p"]
        out["filters"][f] = F
    hp = S3.holm(pv)
    for f in masks:
        F = out["filters"][f]
        p = F["rotation"]["S1_mean_net"]["p"] if f == "A_FLOOR" else hp[f]
        F["p_for_gate2"] = p
        F["p_basis"] = "raw (POST HOC, known)" if f == "A_FLOOR" else "Holm across B and C"
        g2 = F["book"]["mean_net"] > ta and p <= 0.05
        g3 = F["book"]["standard_with_abstention"].get("label") == "EARNS"
        F["gate2"], F["gate3"] = bool(g2), bool(g3)
        F["size_carried"] = bool(p <= 0.05 and F["rotation"]["S2_mean_y"]["p"] > 0.05)
        F["reading"] = ("NO MECHANISM" if not g1["holds"] else "NOT SUPPORTED" if not g2 else "SUPPORTED" if g3 else "FILTER ONLY")
    out["wall_min"] = (time.time() - t0) / 60
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    P(f"[D740] window {out['window']} {len(ti)} trades; gate1 {g1}; "
      + "; ".join(f"{f} {out['filters'][f]['reading']} n{out['filters'][f]['kept']} ${out['filters'][f]['book']['mean_net']:.2f} "
                  f"p{out['filters'][f]['p_for_gate2']:.3f}" for f in masks) + f"; {out['wall_min']:.1f} min")
    return 0


# ================================================================================ selftest (synthetic only)
def selftest() -> int:
    rng = np.random.default_rng(1)
    # roll adjustment
    O = np.array([100.0, 101, 102, 152, 153])
    CL = np.array([101.0, 102, 103, 153, 154])
    con = np.array(["H", "H", "H", "M", "M"])
    c = continuous(O, CL, con)
    need(np.allclose(np.diff(c), [1, 1, 1, 1]), f"the roll gap was not removed: {np.diff(c)}")
    print("  the roll-day adjustment removes a planted 50-point roll gap")
    # SMA identity
    cc = np.cumsum(rng.normal(size=400))
    a = np.arange(30, 400)
    s = htf_state(cc, a)
    sma = pd.Series(cc).rolling(SMA_N).mean().to_numpy()
    rose = np.diff(sma, prepend=np.nan) > 0
    fell = np.diff(sma, prepend=np.nan) < 0
    want = np.where(rose[a - 1] & rose[a - 2] & rose[a - 3], 1.0, np.where(fell[a - 1] & fell[a - 2] & fell[a - 3], -1.0, 0.0))
    need(np.array_equal(s, want), "the c_{t-1} > c_{t-21} rule is not the SMA20-rose-three-days rule")
    print("  SMA20 rose on each of the last 3 days == c[d] > c[d-20] for d = t-1..t-3 (identity holds)")
    # nulls: planted effect and a random mask
    n = 900
    years = np.repeat(np.arange(2016, 2025)[:9].astype(str), 100)
    take = rng.random(n) < 0.45
    net = rng.normal(0, 200, n) + np.where(take, 45.0, 0.0)
    y = net / 150
    r, w = rotation2(take, net, y), within_year(take, net, y, years, rng)
    need(r["S1_mean_net"]["p"] < 0.05 and w["S1_mean_net"]["p"] < 0.05, "a planted effect is not found")
    rnd = rng.random(n) < 0.45
    net0 = rng.normal(0, 200, n)
    pr = rotation2(rnd, net0, net0 / 150)["S1_mean_net"]["p"]
    pw = within_year(rnd, net0, net0 / 150, years, rng)["S1_mean_net"]["p"]
    need(0.02 < pr < 0.98 and 0.02 < pw < 0.98, f"a random mask is extreme (rotation p {pr:.2f}, within-year {pw:.2f})")
    print(f"  planted effect: rotation p {r['S1_mean_net']['p']:.3f}, within-year {w['S1_mean_net']['p']:.4f}; random mask p {pr:.2f} / {pw:.2f}")
    print("SELFTEST PASS (the lag, point-in-time, sign and known-answer checks run inside --run)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a_ = ap.parse_args()
    sys.exit(selftest() if a_.selftest else run() if a_.run else ap.print_help() or 2)
