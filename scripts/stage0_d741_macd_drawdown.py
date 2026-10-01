"""D741 Stage 0: a 30-minute log-MACD (12/26/9) histogram agreement filter for drawdown, on D740's floor-A NQ follow
(docs/decisions/D741-STAGE-0-PRE-REG-a-macd-histogram-agreement-filter-for-drawdown-on-the-floored-nq-follow.md).

    uv run python scripts/stage0_d741_macd_drawdown.py --selftest    # synthetic only
    uv run python scripts/stage0_d741_macd_drawdown.py --run         # once -> data/stage0_d741_macd_drawdown.json

A = D727's k 1.5 follow with sigma$ >= $150 (D740; 546 trades). M = A and sign(histogram at the entry bar) = side. The
bars are NQ's day-session 30-minute bars from D738's cut read (<= 2023-12-29), chained in log price across sessions with
the roll gap removed. Judged on Calmar (net / max DD) against the exact rotation of M's mask over A's trades and a
within-year permutation. Aggregates only.
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

OUT = REPO / "data" / "stage0_d741_macd_drawdown.json"
K, FLOOR_USD, A_COUNT = 1.5, 150.0, 546
FAST, SLOW, SIG = 12, 26, 9
NBAR = 13
N_PERM, SEED = 10_000, 741
P = Z.P


class D741Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D741Error(msg)


# ================================================================================ the MACD
def chain(LB: np.ndarray, logO: np.ndarray, con: np.ndarray) -> np.ndarray:
    """LB: (days, 13) log bar closes. Continuous series: within-day diffs, the overnight step within a contract, and on a
    roll day the first bar against that day's own 09:30 open (the roll gap dropped)."""
    inc = np.zeros_like(LB)
    inc[:, 1:] = np.diff(LB, axis=1)
    same = con[1:] == con[:-1]
    inc[1:, 0] = np.where(same, LB[1:, 0] - LB[:-1, -1], LB[1:, 0] - logO[1:])
    return np.cumsum(inc.ravel())


def macd_hist(L: np.ndarray) -> np.ndarray:
    s = pd.Series(L)
    m = s.ewm(span=FAST, adjust=False).mean() - s.ewm(span=SLOW, adjust=False).mean()
    return (m - m.ewm(span=SIG, adjust=False).mean()).to_numpy(float)


def hist_loop(L: np.ndarray) -> float:
    """Second implementation: explicit recursions over the series given; returns the last histogram value."""
    af, as_, ag = 2 / (FAST + 1), 2 / (SLOW + 1), 2 / (SIG + 1)
    f = s = L[0]
    g = 0.0
    for i, x in enumerate(L):
        f = x if i == 0 else af * x + (1 - af) * f
        s = x if i == 0 else as_ * x + (1 - as_) * s
        m = f - s
        g = m if i == 0 else ag * m + (1 - ag) * g
    return float(m - g)


# ================================================================================ drawdown statistics
def dd_stats(net_seq: np.ndarray) -> tuple[float, float]:
    s = np.cumsum(net_seq)
    dd = float(np.max(np.maximum.accumulate(np.r_[0.0, s])[1:] - s))
    return dd, (float(s[-1]) / dd if dd > 0 else float("inf"))


def dd_matrix(mask: np.ndarray, net: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Rows of masks over the same chronological trades: max DD, Calmar, mean net kept."""
    x = mask * net[None, :]
    s = np.cumsum(x, axis=1)
    peak = np.maximum.accumulate(np.concatenate([np.zeros((len(x), 1)), s], axis=1), axis=1)[:, 1:]
    dd = (peak - s).max(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        cal = np.where(dd > 0, s[:, -1] / dd, np.inf)
    kept = mask.sum(axis=1)
    return dd, cal, x.sum(axis=1) / np.maximum(kept, 1)


def nulls(take: np.ndarray, net: np.ndarray, years: np.ndarray, rng: np.random.Generator) -> dict[str, Any]:
    n = len(take)
    rot = np.stack([np.roll(take, o) for o in range(n)])
    wy = np.zeros((N_PERM, n), bool)
    for yr in np.unique(years):
        idx = np.flatnonzero(years == yr)
        m = int(take[idx].sum())
        if m:
            pick = np.argsort(rng.random((N_PERM, len(idx))), axis=1)[:, :m]
            wy[np.arange(N_PERM)[:, None], idx[pick]] = True
    out = {}
    for name, M in (("rotation", rot), ("within_year", wy)):
        dd, cal, mn = dd_matrix(M.astype(float), net)
        o_dd, o_cal, o_mn = (dd[0], cal[0], mn[0]) if name == "rotation" else dd_matrix(take[None, :].astype(float), net)
        o_dd, o_cal, o_mn = float(np.ravel(o_dd)[0]), float(np.ravel(o_cal)[0]), float(np.ravel(o_mn)[0])
        body = slice(1, None) if name == "rotation" else slice(None)
        out[name] = {"C1_calmar": {"observed": o_cal, "p": float(np.mean(cal >= o_cal)) if name == "rotation" else float((np.sum(cal >= o_cal) + 1) / (N_PERM + 1)),
                                   "null_p50": float(np.percentile(cal[body], 50)), "null_p95": float(np.percentile(cal[body], 95))},
                     "C2_max_dd": {"observed": o_dd, "p": float(np.mean(dd <= o_dd)) if name == "rotation" else float((np.sum(dd <= o_dd) + 1) / (N_PERM + 1)),
                                   "null_p50": float(np.percentile(dd[body], 50)), "null_p05": float(np.percentile(dd[body], 5))},
                     "S1_mean_net": {"observed": o_mn, "p": float(np.mean(mn >= o_mn)) if name == "rotation" else float((np.sum(mn >= o_mn) + 1) / (N_PERM + 1)),
                                     "null_p50": float(np.percentile(mn[body], 50)), "null_p95": float(np.percentile(mn[body], 95))},
                     "draws": int(len(M) - (1 if name == "rotation" else 0))}
    return out


def longest_dd(daily: np.ndarray) -> int:
    s = np.cumsum(daily)
    peak = np.maximum.accumulate(np.r_[0.0, s])[1:]
    under = s < peak
    best = cur = 0
    for u in under:
        cur = cur + 1 if u else 0
        best = max(best, cur)
    return int(best)


# ================================================================================ run
def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists; D741 is run once")
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
        raise D741Error("the lag canary did not fire")
    except T7.D727Error:
        pass
    bk = {k: S1.book(pn, ob, k, usd, cost) for k in S1.KS}
    S1.known_answers(bk, days, json.loads((REPO / "data" / "stage0_d727_trend_curve.json").read_text(encoding="utf-8")))
    b = bk[K]
    # 30-minute bars on every session
    raw = pn["raw"]
    mins = [T7.hhmm(m) for m in range(T7.NMIN)]
    Cp = raw.pivot(index="day", columns="hhmm", values="close").reindex(index=pn["all_days"], columns=mins)
    Cm = Cp.ffill(axis=1).to_numpy(float)
    bar_cols = [30 * (i + 1) - 1 for i in range(NBAR)]
    BC = Cm[:, bar_cols]
    need(np.isfinite(BC).all(), "a 30-minute bar close is missing")
    con = raw.groupby("day")["contract"].agg(lambda s: s.value_counts().index[0]).reindex(pn["all_days"]).to_numpy(str)
    L = chain(np.log(BC), np.log(pn["all_O"]), con)
    H = macd_hist(L)
    # A and the entry bar
    ti = np.flatnonzero(b["side"] != 0)
    sig = pn["soc"][ti] * usd
    A = sig >= FLOOR_USD
    need(int(A.sum()) == A_COUNT, f"A holds {int(A.sum())} trades, D740 recorded {A_COUNT}")
    ai = ti[A]
    a = np.searchsorted(pn["all_days"], days[ai])
    bar = np.array([T7.CLOCKS[int(j)] // 30 - 1 for j in b["first"][ai]])
    flat = a * NBAR + bar
    need(np.allclose(BC[a, bar], [ob["Pt"][i, int(b["first"][i])] for i in ai], atol=1e-9),
         "[RIGHT QUANTITY] the entry bar's close is not the follow's entry price")
    for f in [int(x) for x in rng.choice(flat, 25, replace=False)]:
        need(math.isclose(hist_loop(L[:f + 1]), H[f], rel_tol=1e-9, abs_tol=1e-12), "[PIT] the histogram is not causal")
    fired = 0
    for f in [int(x) for x in rng.choice(flat, 25, replace=False)]:
        fired += int(not math.isclose(hist_loop(L[:f + 2]), H[f], rel_tol=1e-9, abs_tol=1e-12))
    need(fired > 0, "[PIT] the next-bar canary did not change any histogram")
    S1.sign_audit(pn, b, [int(x) for x in rng.choice(ai, 30, replace=False)], usd)
    side, net, gross = b["side"][ai], b["net"][ai], b["gross"][ai]
    h = H[flat]
    M = np.sign(h) == side
    years = np.array([d[:4] for d in days[ai]])
    # Gate 1 on A
    x = gross
    e = x - x.mean()
    v = e @ e / len(x)
    for Lg in range(1, 6):
        v += 2 * (1 - Lg / 6) * (e[Lg:] @ e[:-Lg]) / len(x)
    g1 = {"mean_gross": float(x.mean()), "nw_t": float(x.mean() / math.sqrt(v / len(x)))}
    g1["holds"] = bool(g1["mean_gross"] > 0 and g1["nw_t"] >= 2)

    def book(m: np.ndarray) -> dict[str, Any]:
        nd, gd, kd = np.zeros(len(days)), np.zeros(len(days)), np.zeros(len(days), bool)
        sel = ai[m]
        nd[sel], gd[sel], kd[sel] = b["net"][sel], b["gross"][sel], True
        rep = S3.report(nd, gd, kd, days, net[m])
        dd, cal = dd_stats(net[m])
        rep.update({"calmar": cal, "max_dd_trade_seq": dd, "worst_day": float(nd.min()), "longest_dd_sessions": longest_dd(nd),
                    "mean_hist_abs": float(np.abs(h[m]).mean()) if m.any() else None})
        need(math.isclose(dd, rep["max_dd"], rel_tol=1e-9, abs_tol=1e-6), "the trade-sequence DD is not the daily DD")
        return rep

    out: dict[str, Any] = {"spec": "D741-STAGE-0-PRE-REG-a-macd-histogram-agreement-filter-for-drawdown-on-the-floored-nq-follow.md",
                           "seal": f"nothing on or after {Z.CUT24}; aggregates only", "cost": cost,
                           "a_trades": int(len(ai)), "kept": int(M.sum()), "kept_share": float(M.mean()),
                           "pit_canary_changed": fired, "gate1": g1,
                           "A": book(np.ones(len(ai), bool)), "M": book(M), "dropped": book(~M)}
    nl = nulls(M, net, years, rng)
    out["nulls"] = nl
    Arep, Mrep = out["A"], out["M"]
    g2 = Mrep["max_dd"] < Arep["max_dd"] and Mrep["calmar"] > Arep["calmar"] and nl["rotation"]["C1_calmar"]["p"] <= 0.05
    g3 = Mrep["standard_with_abstention"].get("label") == "EARNS"
    out["gate2"], out["gate3"] = bool(g2), bool(g3)
    out["reading"] = ("NO MECHANISM" if not g1["holds"] else "NOT SUPPORTED" if not g2 else "SUPPORTED" if g3 else "DRAWDOWN ONLY")
    out["wall_min"] = (time.time() - t0) / 60
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    P(f"[D741] A {len(ai)} -> M {int(M.sum())}; A DD {Arep['max_dd']:.0f} Calmar {Arep['calmar']:.2f}; M DD {Mrep['max_dd']:.0f} "
      f"Calmar {Mrep['calmar']:.2f} mean {Mrep['mean_net']:.2f}; rotation C1 p {nl['rotation']['C1_calmar']['p']:.3f}; "
      f"{out['reading']}; {out['wall_min']:.1f} min")
    return 0


# ================================================================================ selftest (synthetic only)
def selftest() -> int:
    rng = np.random.default_rng(2)
    L = np.cumsum(rng.normal(0, 0.003, 500))
    H = macd_hist(L)
    for f in (0, 1, 50, 499):
        need(math.isclose(hist_loop(L[:f + 1]), H[f], rel_tol=1e-9, abs_tol=1e-12), f"EMA/MACD differs from the loop at {f}")
    print("  the pandas MACD histogram equals the explicit recursion (causal)")
    LB = np.log(np.array([[100.0] * 13, [150.0] * 13]))
    LB[1, :] = np.log(150 + np.arange(13))
    Lc = chain(LB, np.log(np.array([100.0, 150.0])), np.array(["H", "M"]))
    need(abs(Lc[13] - Lc[12]) < 1e-12, f"the roll gap was not removed ({Lc[13] - Lc[12]})")
    print("  the roll day's first bar is chained to its own open (the 50% gap removed)")
    n = 500
    net = rng.normal(25, 200, n)
    net[200:230] -= 400                               # a cluster of losers the planted mask avoids
    years = np.repeat(np.array(["2018", "2019", "2020", "2021", "2022"]), 100)
    take = np.ones(n, bool)
    take[200:230] = False
    take[rng.choice(np.r_[0:200, 230:n], 120, replace=False)] = False
    r = nulls(take, net, years, rng)
    need(r["rotation"]["C1_calmar"]["p"] < 0.05, f"a planted drawdown cut is not found (p {r['rotation']['C1_calmar']['p']:.3f})")
    rnd = rng.random(n) < 0.7
    pr = nulls(rnd, rng.normal(25, 200, n), years, rng)["rotation"]["C1_calmar"]["p"]
    need(0.02 < pr < 0.98, f"a random mask is extreme (p {pr:.2f})")
    print(f"  planted drawdown cut: rotation p {r['rotation']['C1_calmar']['p']:.3f}; random mask p {pr:.2f}")
    print("SELFTEST PASS (lag, right-quantity, point-in-time and sign checks run inside --run)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a_ = ap.parse_args()
    sys.exit(selftest() if a_.selftest else run() if a_.run else ap.print_help() or 2)
