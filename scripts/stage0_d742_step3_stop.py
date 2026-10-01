"""D742 step 3 (amendment A1): the principal's 1.0 sigma_rem stop on D740's floor-A NQ follow, against a random-exit null
and a paired month-block bootstrap (docs/decisions/D742-STAGE-0-PRE-REG-a-protective-stop-for-the-floored-follow.md).

    uv run python scripts/stage0_d742_step3_stop.py --selftest   # synthetic only
    uv run python scripts/stage0_d742_step3_stop.py --run        # once -> data/stage0_d742_stop_test.json

Trades and the stop come through the step-1 runner (stage0_d742_stop_oracle.stop_exit) and D738's cut read; step 1's
1.0 sigma_rem total is re-proved first. Aggregates only.
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

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d720_size_the_direction as Z  # noqa: E402
import stage0_d727_trend_curve as T7  # noqa: E402
import stage0_d738_follow_oracle as S1  # noqa: E402
import stage0_d741_macd_drawdown as D741  # noqa: E402
import stage0_d742_stop_oracle as S42  # noqa: E402

OUT = REPO / "data" / "stage0_d742_stop_test.json"
W = 1.0
KNOWN_TOTAL = 12883.847019145058          # step 1's 1.0 sigma_rem total (data/stage0_d742_stop_oracle.json)
N_DRAW = 10_000
P = Z.P


class D742Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D742Error(msg)


def row_stats(N: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Rows of chronological per-trade nets (one trade a session; flat sessions add nothing to a drawdown): max DD,
    Calmar, worst trade (= worst day)."""
    s = np.cumsum(N, axis=1)
    peak = np.maximum.accumulate(np.concatenate([np.zeros((len(N), 1)), s], axis=1), axis=1)[:, 1:]
    dd = (peak - s).max(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        cal = np.where(dd > 0, s[:, -1] / dd, np.inf)
    return dd, cal, N.min(axis=1)


def random_exits(net0: np.ndarray, exitG: list[np.ndarray], n_exit: int, cost: float, rng: np.random.Generator) -> np.ndarray:
    """N_DRAW rows: n_exit random trades each exited at a uniform random minute from its entry to 15:59."""
    n = len(net0)
    out = np.tile(net0, (N_DRAW, 1))
    picks = np.argsort(rng.random((N_DRAW, n)), axis=1)[:, :n_exit]
    for r in range(N_DRAW):
        for k in picks[r]:
            g = exitG[k]
            out[r, k] = g[rng.integers(0, len(g))] - cost
    return out


def month_bootstrap(stop_d: np.ndarray, none_d: np.ndarray, months: np.ndarray, rng: np.random.Generator) -> dict[str, Any]:
    keys = np.unique(months)
    idx = {m: np.flatnonzero(months == m) for m in keys}
    dc, dw, dd_ = np.empty(N_DRAW), np.empty(N_DRAW), np.empty(N_DRAW)
    for r in range(N_DRAW):
        sel = np.concatenate([idx[m] for m in rng.choice(keys, len(keys), replace=True)])
        a, b = stop_d[sel], none_d[sel]
        da, ca = D741.dd_stats(a)
        db, cb = D741.dd_stats(b)
        dc[r], dw[r], dd_[r] = ca - cb, a.min() - b.min(), da - db
    q = lambda x: {"p05": float(np.percentile(x, 5)), "p50": float(np.percentile(x, 50))}  # noqa: E731
    return {"P_dCalmar_gt_0": float((dc > 0).mean()), "P_dWorstDay_gt_0": float((dw > 0).mean()),
            "P_dMaxDD_lt_0": float((dd_ < 0).mean()), "dCalmar": q(dc), "dWorstDay": q(dw), "dMaxDD": q(dd_), "draws": N_DRAW,
            "months": int(len(keys))}


def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists; step 3 is run once")
    t0 = time.time()
    import stage1_d711_f2_mechanism as M711
    cl = M711.cost_line("NQ")
    cost, usd = float(cl["cost"]), float(cl["usd_per_point"])
    pn = T7.panel_from_raw("NQ", S1.read_cut(S1.DATA / "fixtures" / "fut_NQ_rth_1m.csv.gz"))
    ob = T7.objects(pn)
    days = pn["days"]
    Z.no_session_after(days, "the NQ panel")
    bk = {k: S1.book(pn, ob, k, usd, cost) for k in S1.KS}
    S1.known_answers(bk, days, json.loads((REPO / "data" / "stage0_d727_trend_curve.json").read_text(encoding="utf-8")))
    b = bk[S42.K]
    ti = np.flatnonzero(b["side"] != 0)
    A = pn["soc"][ti] * usd >= S42.FLOOR_USD
    need(int(A.sum()) == S42.A_COUNT, "A's count differs from D740's")
    ai = ti[A]
    raw = pn["raw"]
    mins = [T7.hhmm(x) for x in range(S42.NMIN)]

    def piv(col: str) -> np.ndarray:
        return raw.pivot(index="day", columns="hhmm", values=col).reindex(index=days, columns=mins).to_numpy(float)

    Op, H, L = piv("open"), piv("high"), piv("low")
    Cm = raw.pivot(index="day", columns="hhmm", values="close").reindex(index=days, columns=mins).ffill(axis=1).to_numpy(float)
    last = ob["close"]
    m = np.array([T7.CLOCKS[int(j)] for j in b["first"][ai]])
    E = np.array([ob["Pt"][i, int(b["first"][i])] for i in ai])
    side, soc = b["side"][ai], pn["soc"][ai]
    res = [S42.stop_exit(E[k], side[k], m[k], W, soc[k], Op[i], H[i], L[i], last[i]) for k, i in enumerate(ai)]
    g1 = np.array([side[k] * (r[0] - E[k]) * usd for k, r in enumerate(res)])
    stopped = np.array([r[1] for r in res])
    net1, net0 = g1 - cost, b["net"][ai]
    need(abs(net1.sum() - KNOWN_TOTAL) < 0.01, f"step 1's 1.0 sigma_rem total not reproduced ({net1.sum()})")
    n_exit = int(stopped.sum())
    # the random-exit null
    rng = np.random.default_rng(7421)
    exitG = [side[k] * (Cm[i, m[k]:] - side[k] * S42.TICK - E[k]) * usd for k, i in enumerate(ai)]
    need(all(np.isfinite(g).all() for g in exitG), "a random-exit price is missing")
    N = random_exits(net0, exitG, n_exit, cost, rng)
    dd_n, cal_n, wd_n = row_stats(N)
    dd1, cal1 = D741.dd_stats(net1)
    dd0, cal0 = D741.dd_stats(net0)
    w1, w0 = float(net1.min()), float(net0.min())
    rnd = {"R1_calmar": {"observed": cal1, "p": float((np.sum(cal_n >= cal1) + 1) / (N_DRAW + 1)),
                         "null_p50": float(np.percentile(cal_n, 50)), "null_p95": float(np.percentile(cal_n, 95))},
           "R2_worst_day": {"observed": w1, "p": float((np.sum(wd_n >= w1) + 1) / (N_DRAW + 1)),
                            "null_p50": float(np.percentile(wd_n, 50)), "null_p95": float(np.percentile(wd_n, 95))},
           "R3_max_dd": {"observed": dd1, "p": float((np.sum(dd_n <= dd1) + 1) / (N_DRAW + 1)),
                         "null_p50": float(np.percentile(dd_n, 50)), "null_p05": float(np.percentile(dd_n, 5))},
           "null_mean_net_per_trade_p50": float(np.percentile(N.mean(axis=1), 50)), "exits_per_draw": n_exit, "draws": N_DRAW}
    # the paired month bootstrap on the daily series from A's first trade
    first = days[ai[0]]
    win = days >= first
    sd, nd = np.zeros(len(days)), np.zeros(len(days))
    sd[ai], nd[ai] = net1, net0
    months = np.array([d[:7] for d in days[win]])
    boot = month_bootstrap(sd[win], nd[win], months, np.random.default_rng(7422))
    # halves by trade count
    h = len(ai) // 2
    halves = {}
    for name, sl in (("first", slice(0, h)), ("second", slice(h, None))):
        a_, c_ = D741.dd_stats(net1[sl]), D741.dd_stats(net0[sl])
        halves[name] = {"span": [str(days[ai][sl][0]), str(days[ai][sl][-1])], "calmar_stop": a_[1], "calmar_none": c_[1],
                        "max_dd_stop": a_[0], "max_dd_none": c_[0], "net_stop": float(net1[sl].sum()), "net_none": float(net0[sl].sum())}
    years = {y: float(net1[np.array([d[:4] for d in days[ai]]) == y].sum()) for y in sorted({d[:4] for d in days[ai]})}
    nby = {y: int((np.array([d[:4] for d in days[ai]]) == y).sum()) for y in years}
    import stage0_d738_step3_filters as S3
    std = S3.traded_year_standard(years, nby)
    g2 = rnd["R1_calmar"]["p"] <= 0.05 and boot["P_dCalmar_gt_0"] >= 0.90 and all(v["calmar_stop"] > v["calmar_none"] for v in halves.values())
    g3 = std.get("label") == "EARNS"
    out = {"spec": "D742-A1", "seal": f"nothing on or after {Z.CUT24}; aggregates only", "w_sigma_rem": W, "a_trades": int(len(ai)),
           "stopped": n_exit, "winners_stopped": int((stopped & (net0 > 0)).sum()),
           "stop_book": {"total": float(net1.sum()), "mean": float(net1.mean()), "max_dd": dd1, "calmar": cal1, "worst_day": w1},
           "no_stop": {"total": float(net0.sum()), "mean": float(net0.mean()), "max_dd": dd0, "calmar": cal0, "worst_day": w0},
           "random_exit_null": rnd, "bootstrap": boot, "halves": halves, "standard_with_abstention": std,
           "gate2": bool(g2), "gate3": bool(g3),
           "reading": "NOT SUPPORTED" if not g2 else "SUPPORTED" if g3 else "DRAWDOWN ONLY"}
    out["wall_min"] = (time.time() - t0) / 60
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    P(f"[D742-3] Calmar {cal1:.2f} vs none {cal0:.2f}; random-exit p {rnd['R1_calmar']['p']:.4f} (p50 {rnd['R1_calmar']['null_p50']:.2f}); "
      f"P(dCalmar>0) {boot['P_dCalmar_gt_0']:.3f}; halves {[round(v['calmar_stop'], 2) for v in halves.values()]} vs "
      f"{[round(v['calmar_none'], 2) for v in halves.values()]}; {out['reading']}; {out['wall_min']:.1f} min")
    return 0


def selftest() -> int:
    rng = np.random.default_rng(9)
    n = 300
    net0 = rng.normal(20, 150, n)
    loser = net0 < -100
    net1 = np.where(loser, -60.0, net0)                    # a stop that truncates exactly the big losers
    exitG = [rng.normal(20, 150, 50) + 4 for _ in range(n)]
    N = random_exits(net0, exitG, int(loser.sum()), 4.0, rng)
    _, cal_n, _ = row_stats(N)
    _, cal1 = D741.dd_stats(net1)
    p = (np.sum(cal_n >= cal1) + 1) / (N_DRAW + 1)
    need(p < 0.05, f"a planted loser-cutting stop is not found (p {p:.3f})")
    days = np.array([f"20{18 + i // 120:02d}-{1 + (i // 10) % 12:02d}-{1 + i % 10:02d}" for i in range(n)])
    boot = month_bootstrap(net1, net0, np.array([d[:7] for d in days]), rng)
    need(boot["P_dCalmar_gt_0"] > 0.9 and boot["P_dWorstDay_gt_0"] > 0.9, f"the bootstrap misses a planted gain: {boot}")
    netr = np.where(rng.random(n) < 0.15, net0 * 0.5, net0)  # a random partial exit
    _, calr = D741.dd_stats(netr)
    pr = (np.sum(cal_n >= calr) + 1) / (N_DRAW + 1)
    print(f"  planted loser-cutting stop: random-exit p {p:.4f}, P(dCalmar>0) {boot['P_dCalmar_gt_0']:.3f}; a random partial exit p {pr:.2f}")
    need(pr > 0.05, "a random partial exit beats the random-exit null")
    print("SELFTEST PASS (the step-1 total and the known answers are re-proved inside --run)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a_ = ap.parse_args()
    sys.exit(selftest() if a_.selftest else run() if a_.run else ap.print_help() or 2)
