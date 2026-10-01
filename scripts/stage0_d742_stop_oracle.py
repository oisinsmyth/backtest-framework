"""D742 Stage 0, step 1: the excursion profile and a descriptive volatility-scaled stop curve for D740's floor-A NQ follow
(docs/decisions/D742-STAGE-0-PRE-REG-the-oracle-of-a-protective-stop-on-the-floored-nq-follow.md). No stop is chosen.

    uv run python scripts/stage0_d742_stop_oracle.py --selftest    # synthetic only (incl. D735's e1_tables convention)
    uv run python scripts/stage0_d742_stop_oracle.py --run         # once -> data/stage0_d742_stop_oracle.json

The trades come through D738 step 1's functions (a chunked read cut at 2023-12-29). The stop is D735's: w x sigma_rem
from the entry (sigma_rem = sigma_oc sqrt((390 - m)/390)), touched on one-minute lows/highs from the bar after the
entry, filled at the stop (or a gapped open) less one tick; else the 15:59 close. Aggregates only.
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
import stage0_d738_step3_filters as S3  # noqa: E402
import stage0_d741_macd_drawdown as D741  # noqa: E402

OUT = REPO / "data" / "stage0_d742_stop_oracle.json"
K, FLOOR_USD, A_COUNT = 1.5, 150.0, 546
NMIN, TICK = 390, 0.25
WIDTHS = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
MAE_MARKS = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0)
P = Z.P


class D742Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D742Error(msg)


# ================================================================================ the stop (D735's convention)
def stop_exit(E: float, side: float, m: int, w: float, soc: float, Op: np.ndarray, H: np.ndarray, L: np.ndarray,
              last: float, start_shift: int = 0) -> tuple[float, bool, int]:
    """One trade: entry E at minute m (watched on bars m..389; start_shift = -1 includes the entry bar: the canary).
    Returns (exit price, stopped, minute)."""
    if not math.isfinite(w):
        return last, False, NMIN - 1
    dist = w * soc * math.sqrt((NMIN - m) / NMIN)
    s0 = m + start_shift
    if side > 0:
        stop = E - dist
        hit = np.flatnonzero(L[s0:] <= stop)
        if len(hit):
            b = s0 + int(hit[0])
            return (Op[b] - TICK if Op[b] <= stop else stop - TICK), True, b
    else:
        stop = E + dist
        hit = np.flatnonzero(H[s0:] >= stop)
        if len(hit):
            b = s0 + int(hit[0])
            return (Op[b] + TICK if Op[b] >= stop else stop + TICK), True, b
    return last, False, NMIN - 1


def excursions(E: float, side: float, m: int, soc: float, H: np.ndarray, L: np.ndarray) -> dict[str, float]:
    sr = soc * math.sqrt((NMIN - m) / NMIN)
    lo, hi = np.nanmin(L[m:]), np.nanmax(H[m:])
    if side > 0:
        mae, mfe, at = max(0.0, E - lo), max(0.0, hi - E), int(m + np.nanargmin(L[m:]))
        by12 = max(0.0, E - np.nanmin(L[m:150])) if m < 150 else np.nan
    else:
        mae, mfe, at = max(0.0, hi - E), max(0.0, E - lo), int(m + np.nanargmax(H[m:]))
        by12 = max(0.0, np.nanmax(H[m:150]) - E) if m < 150 else np.nan
    return {"mae_srem": mae / sr, "mfe_srem": mfe / sr, "mae_pts": mae, "mae_minute": at, "mae_by_noon_srem": by12 / sr}


# ================================================================================ run
def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists; D742 is run once")
    t0 = time.time()
    import stage1_d711_f2_mechanism as M711
    cl = M711.cost_line("NQ")
    cost, usd = float(cl["cost"]), float(cl["usd_per_point"])
    pn = T7.panel_from_raw("NQ", S1.read_cut(S1.DATA / "fixtures" / "fut_NQ_rth_1m.csv.gz"))
    ob = T7.objects(pn)
    days = pn["days"]
    Z.no_session_after(days, "the NQ panel")
    rng = np.random.default_rng(742)
    smp = [(int(rng.integers(0, len(days))), int(rng.integers(0, len(T7.CLOCKS)))) for _ in range(40)]
    T7.lag_audit(pn, ob, smp)
    try:
        T7.lag_audit(pn, ob, smp, shift=1)
        raise D742Error("the lag canary did not fire")
    except T7.D727Error:
        pass
    bk = {k: S1.book(pn, ob, k, usd, cost) for k in S1.KS}
    S1.known_answers(bk, days, json.loads((REPO / "data" / "stage0_d727_trend_curve.json").read_text(encoding="utf-8")))
    b = bk[K]
    ti = np.flatnonzero(b["side"] != 0)
    A = pn["soc"][ti] * usd >= FLOOR_USD
    need(int(A.sum()) == A_COUNT, f"A holds {int(A.sum())} trades, D740 recorded {A_COUNT}")
    ai = ti[A]
    raw = pn["raw"]
    mins = [T7.hhmm(x) for x in range(NMIN)]

    def piv(col: str) -> np.ndarray:
        return raw.pivot(index="day", columns="hhmm", values=col).reindex(index=days, columns=mins).to_numpy(float)

    Op, H, L = piv("open"), piv("high"), piv("low")
    last = ob["close"]
    ent_m = np.array([T7.CLOCKS[int(j)] for j in b["first"][ai]])
    E = np.array([ob["Pt"][i, int(b["first"][i])] for i in ai])
    side = b["side"][ai]
    soc = pn["soc"][ai]
    # right quantity: the unstopped exit reproduces the book's gross
    g0 = np.array([side[k] * (stop_exit(E[k], side[k], ent_m[k], math.inf, soc[k], Op[i], H[i], L[i], last[i])[0] - E[k]) * usd
                   for k, i in enumerate(ai)])
    need(np.allclose(g0, b["gross"][ai], atol=1e-9), "the unstopped exit does not reproduce the follow's gross")
    net0 = g0 - cost
    win = net0 > 0
    # A. excursions
    ex = [excursions(E[k], side[k], ent_m[k], soc[k], H[i], L[i]) for k, i in enumerate(ai)]
    mae = np.array([e["mae_srem"] for e in ex])
    mfe = np.array([e["mfe_srem"] for e in ex])
    mae_min = np.array([e["mae_minute"] for e in ex])
    by12 = np.array([e["mae_by_noon_srem"] for e in ex])
    q = [0.1, 0.25, 0.5, 0.75, 0.9]
    out: dict[str, Any] = {"spec": "D742-STAGE-0-PRE-REG-the-oracle-of-a-protective-stop-on-the-floored-nq-follow.md",
                           "seal": f"nothing on or after {Z.CUT24}; aggregates only", "cost": cost, "a_trades": int(len(ai)),
                           "excursions": {
                               "mae_srem_quantiles": {"winners": dict(zip(map(str, q), np.quantile(mae[win], q).tolist())),
                                                      "losers": dict(zip(map(str, q), np.quantile(mae[~win], q).tolist()))},
                               "mfe_srem_quantiles": {"winners": dict(zip(map(str, q), np.quantile(mfe[win], q).tolist())),
                                                      "losers": dict(zip(map(str, q), np.quantile(mfe[~win], q).tolist()))},
                               "share_reaching": {str(x): {"winners": float((mae[win] >= x).mean()), "losers": float((mae[~win] >= x).mean())}
                                                  for x in MAE_MARKS},
                               "losers_worst_point_in_last_hour": float((mae_min[~win] >= 330).mean()),
                               "winners": int(win.sum()), "losers": int((~win).sum())}}
    w5 = np.argsort(net0)[: max(1, int(0.05 * len(net0)))]
    out["excursions"]["worst_5pct"] = {"n": int(len(w5)), "mean_net": float(net0[w5].mean()),
                                       "median_mae_srem": float(np.median(mae[w5])),
                                       "share_below_minus_1srem_by_noon": float(np.nanmean(by12[w5] >= 1.0)),
                                       "n_entered_before_noon": int(np.isfinite(by12[w5]).sum())}

    def daily(net_t: np.ndarray, gross_t: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        nd, gd, kd = np.zeros(len(days)), np.zeros(len(days)), np.zeros(len(days), bool)
        nd[ai], gd[ai], kd[ai] = net_t, gross_t, True
        return nd, gd, kd

    def summary(net_t: np.ndarray, gross_t: np.ndarray) -> dict[str, Any]:
        nd, gd, kd = daily(net_t, gross_t)
        rep = S3.report(nd, gd, kd, days, net_t)
        dd, cal = D741.dd_stats(net_t)
        rep.update({"calmar": cal, "worst_day": float(nd.min()), "longest_dd_sessions": D741.longest_dd(nd)})
        return rep

    # B. ceilings
    perfect = np.where(net0 < 0, -cost, net0)
    out["ceilings"] = {"perfect_exit": summary(perfect, np.where(net0 < 0, 0.0, g0)),
                       "loss_on_losing_trades": float(net0[~win].sum()),
                       "worst_20_days_sum": float(np.sort(net0)[:20].sum())}
    # C. the stop curve
    curve = {"none": dict(summary(net0, g0), stopped=0, winners_stopped=0)}
    fired = 0
    for w in WIDTHS:
        res = [stop_exit(E[k], side[k], ent_m[k], w, soc[k], Op[i], H[i], L[i], last[i]) for k, i in enumerate(ai)]
        gx = np.array([side[k] * (r[0] - E[k]) * usd for k, r in enumerate(res)])
        st = np.array([r[1] for r in res])
        if w == 1.0:
            can = [stop_exit(E[k], side[k], ent_m[k], w, soc[k], Op[i], H[i], L[i], last[i], start_shift=-1) for k, i in enumerate(ai)]
            fired = int(sum(c[0] != r[0] for c, r in zip(can, res)))
            need(fired > 0, "the early-scan canary did not change any exit")
            # sign / second implementation on stopped trades from the raw rows
            for k in [int(x) for x in rng.choice(np.flatnonzero(st), min(25, int(st.sum())), replace=False)]:
                i = ai[k]
                r = raw[raw["day"] == days[i]].set_index("hhmm").sort_index()
                dist = w * soc[k] * math.sqrt((NMIN - ent_m[k]) / NMIN)
                stop = E[k] - side[k] * dist
                rows = r.loc[T7.hhmm(ent_m[k]):]
                touch = rows[(rows["low"] <= stop)] if side[k] > 0 else rows[(rows["high"] >= stop)]
                o = float(touch["open"].iloc[0])
                want = (o - TICK if o <= stop else stop - TICK) if side[k] > 0 else (o + TICK if o >= stop else stop + TICK)
                need(math.isclose(want, res[k][0], abs_tol=1e-9), f"[STOP] {days[i]}: the raw-row stop fill differs")
                need(side[k] * (want - E[k]) < 0, "[SIGN] a stopped trade does not lose before costs")
        nx = gx - cost
        curve[str(w)] = dict(summary(nx, gx), stopped=int(st.sum()), winners_stopped=int((st & win).sum()),
                             losers_stopped=int((st & ~win).sum()))
    out["stop_curve"] = curve
    out["canary_early_scan_changed"] = fired
    out["wall_min"] = (time.time() - t0) / 60
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    P("[D742] " + "; ".join(f"w {w}: DD {c['max_dd']:.0f} Calmar {c['calmar']:.2f} mean {c['mean_net']:.2f} worst {c['worst_day']:.0f} "
                            f"stopped {c['stopped']}" for w, c in curve.items()) + f"; {out['wall_min']:.1f} min")
    return 0


# ================================================================================ selftest (synthetic only)
def selftest() -> int:
    import stage0_d735_nq_breaks_from_the_market as D735
    rng = np.random.default_rng(5)
    n = 40
    steps = rng.normal(0, 2.0, (n, NMIN))
    Cc = 1000 + np.cumsum(steps, axis=1)
    Op = np.c_[Cc[:, :1] - steps[:, :1], Cc[:, :-1]]          # each bar opens at the previous close (continuous)
    Hh = np.maximum(Op, Cc) + rng.uniform(0, 1.5, (n, NMIN))
    Ll = np.minimum(Op, Cc) - rng.uniform(0, 1.5, (n, NMIN))
    jump = rng.choice(n, 5, replace=False)
    Op[jump, 120] -= 15
    Hh[jump, 120] = np.maximum(Hh[jump, 120], Op[jump, 120])
    Ll[jump, 120] = np.minimum(Ll[jump, 120], Op[jump, 120]) - 1   # gaps through
    soc = rng.uniform(20, 60, n)
    pp = {"Op": Op, "H": Hh, "L": Ll, "C": Cc, "soc": soc}
    for w in (0.5, 1.0, math.inf):
        G = D735.e1_tables(pp, w)
        for m in (30, 60, 100, 300):
            for d in range(n):
                E = Cc[d, m - 1]
                need(math.isclose(E, Op[d, m]), "synthetic continuity")
                for sd, key in ((1.0, "up"), (-1.0, "dn")):
                    x, _, _ = stop_exit(E, sd, m, w, soc[d], Op[d], Hh[d], Ll[d], Cc[d, -1])
                    need(math.isclose(sd * (x - E) * 2.0, G[key][d, m], abs_tol=1e-9),
                         f"the stop differs from D735's e1_tables at w {w}, m {m}, day {d}, {key}")
    print("  the stop equals D735's e1_tables convention (w 0.5, 1.0, none; long and short; gapped opens)")
    # canary: only the entry bar (m - 1) touches the stop; bars from m never do
    o1, h1, l1 = np.full(NMIN, 100.0), np.full(NMIN, 101.0), np.full(NMIN, 99.0)
    l1[99] = 90.0
    x, st, _ = stop_exit(100.0, 1.0, 100, 0.2, 10.0, o1, h1, l1, 100.0)
    x2, st2, _ = stop_exit(100.0, 1.0, 100, 0.2, 10.0, o1, h1, l1, 100.0, start_shift=-1)
    need(not st and st2 and x2 != x, "the early-scan canary does not change the exit")
    print("  fires: a scan that includes the entry bar stops a trade the correct scan does not")
    e = excursions(1000.0, 1.0, 0, 30.0, np.full(NMIN, 1005.0), np.r_[np.full(10, 999.0), np.full(NMIN - 10, 990.0)])
    need(math.isclose(e["mae_pts"], 10.0) and math.isclose(e["mae_srem"], 10 / 30.0), f"MAE wrong: {e}")
    print("  MAE in points and sigma_rem units correct on a hand case")
    print("SELFTEST PASS (lag, known-answer, right-quantity, raw-row stop and sign checks run inside --run)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a_ = ap.parse_args()
    sys.exit(selftest() if a_.selftest else run() if a_.run else ap.print_help() or 2)
