"""D701 DIAG -- do D700's 5- and 15-minute channel onsets and D699's V1 carry the same information on short-gamma
days? (The principal, 2026-09-30: "Measure the overlap between the 5- and 15-minute channels and V1's entries
first".) Design: docs/decisions/D701-DIAG-DESIGN-do-the-channel-and-v1-carry-the-same-information.md, committed
before this runner.

    uv run python scripts/diag_d701_channel_v1_overlap.py --selftest
    uv run python scripts/diag_d701_channel_v1_overlap.py --run --data-root "<main checkout>/data"

In-sample, 2016-01-05 -> 2023-12-29, on the short-gamma days D699 and D700 both trade; nothing on or after 2024-01-01
is read. Both objects are REPRODUCED through their own runners' functions, unchanged, and guarded against their
published numbers exactly (V1: 572 trades, mean net +$10.47477440436403; the channel's +60-minute mean excess on
short-gamma days: 5m +$4.408950821115721, 15m +$6.764175105858219).

DECLARED MEASUREMENTS
  A  coincidence against time-matched base rates: V1 holding at each channel onset's fill (up and down onsets);
     the up channel held at V1's deciding close (5m, 15m); phi between V1's state and the up channel's state at every
     15-minute close 09:45 .. 15:45
  B  the channel's up and down onsets split by V1's state at the fill: +60-minute signed gross, drift control,
     excess and its day-clustered t, hit (D700's measure exactly)
  C  V1's trades split by whether an up channel holds at V1's deciding close (5m, 15m): count, mean net and gross,
     median, hit, D699's drift excess and its day-clustered t
DECLARED READING per clock: SAME INFORMATION if the up-onset excess with V1 flat is under a third of the up-onset
pooled excess with |t| < 1, and V1's trades without a channel keep >= 2/3 of V1's mean gross; INDEPENDENT if the
up-onset excess with V1 flat keeps >= 2/3 of the pooled; CONDITIONER CANDIDATE if V1's trades with the channel's
agreement earn >= $4.42 a trade more net than those without; else MIXED.

Output data/d701_channel_v1_overlap.json: statistics only, no per-date GEX (SqueezeMetrics, under the permission of
2026-09-28).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d688_gamma_close as S                 # noqa: E402  (importing defines, never runs)
import stage0_d699_gamma_macd_long as V             # noqa: E402
import stage0_d700_channel_clock_profile as C       # noqa: E402

OUT = REPO / "data" / "d701_channel_v1_overlap.json"
D699_JSON = REPO / "data" / "d699_gamma_macd_long.json"
D700_JSON = REPO / "data" / "d700_channel_clock_profile.json"
CLOCKS = (5, 15)
V1 = "V1_HIST"
N_AUDIT = 200


def P(*a, **k):
    print(*a, **k, flush=True)


def core(O1, H1, L1, C1, valid, PM, pidx, short, usd, cost, log=P, parallel=True, guards=None):
    nall = PM.shape[0]
    # ---- V1, through D699's functions
    PB = PM[:, np.concatenate([[0], V.BAR_J])]
    sig = V.signals(PB)
    ST = V.states(sig, +1)
    ok = sig["valid"][pidx] & np.isfinite(sig["s15"][pidx]) & np.isfinite(PM[pidx]).all(1)
    rows_v = pidx[ok & short]
    ii, ja, jb = V.trade_list(ST[V1], rows_v)
    vg = (PM[ii, jb] - PM[ii, ja]) * usd
    vn = vg - cost
    if guards and (len(ii) != guards["v1_trades"] or float(vn.mean()) != guards["v1_mean_net"]):
        raise S.GateError(f"[REPRO] V1: {len(ii)} trades, mean net {float(vn.mean())!r}; D699 published {guards['v1_trades']} and {guards['v1_mean_net']!r}")
    log(f"  V1 {'REPRODUCED' if guards else '(unguarded)'}: {len(ii)} trades, mean net ${vn.mean():+.4f}")
    # ---- the channels, through D700's functions (its truncation lag audit re-run)
    jobs = [(c, O1, H1, L1, C1, valid, 700) for c in CLOCKS]
    if parallel:
        with ProcessPoolExecutor(max_workers=len(CLOCKS)) as ex:
            W = {o["c"]: o for o in ex.map(C.clock_job, jobs)}
    else:
        W = {o["c"]: o for o in map(C.clock_job, jobs)}
    for c in CLOCKS:
        if not W[c]["peek_fired"] or W[c]["n_probe_events"] == 0:
            raise S.GateError(f"[LAG] clock {c}: D700's audit did not fire, or was vacuous")
    inser = np.ones(nall, bool)
    for c in CLOCKS:
        m = np.zeros(nall, bool); m[W[c]["rows"]] = True
        inser &= m
    sh_all = np.zeros(nall, bool); sh_all[pidx] = short
    dayok = np.zeros(nall, bool); dayok[pidx] = inser[pidx] & np.isfinite(PM[pidx]).all(1)
    cls_s = dayok & sh_all
    if not np.array_equal(np.flatnonzero(cls_s), np.sort(rows_v)):
        raise S.GateError(f"[DAYS] D700's short-gamma days ({int(cls_s.sum())}) are not D699's ({rows_v.size})")
    rows_s = np.flatnonzero(cls_s)
    mbar = PM[rows_s].mean(0)
    ident = np.arange(nall)
    # ---- V1's holding, by minute, and a loop that re-derives it (and must fire when broken)
    HOLD = np.zeros((nall, C.CLOSE_J + 1), bool)
    for i, a, b in zip(ii, ja, jb):
        HOLD[i, a:b] = True
    by_day = {}
    for i, a, b in zip(ii.tolist(), ja.tolist(), jb.tolist()):
        by_day.setdefault(i, []).append((a, b))
    loop_hold = lambda r, j: any(a <= j < b for a, b in by_day.get(int(r), []))
    holdfrac = HOLD[rows_s].mean(0)
    res = {"v1": {"trades": int(len(ii)), "mean_net": float(vn.mean()), "mean_gross": float(vg.mean())}, "short_gamma_days": int(rows_s.size), "clocks": {}}
    rng = np.random.default_rng(701)
    for c in CLOCKS:
        o = W[c]
        nb, rows = o["nb"], o["rows"]
        cu = C.channel(o["G"], o["L"], o["S"], C.F_PRIMARY, +1)
        cd = C.channel(o["G"], o["L"], o["S"], C.F_PRIMARY, -1)
        ev = C.events_of(cu, cd, nb, c, rows, cls_s, ident)
        pooled = C.profile(PM, ev, mbar, usd, rows_s.size)
        if guards and pooled[f"+{C.H_PRIMARY}m"]["mean_excess"] != guards["ch_excess"][c]:
            raise S.GateError(f"[REPRO] clock {c}: +60m excess {pooled['+60m']['mean_excess']!r} vs D700's {guards['ch_excess'][c]!r}")
        log(f"  CHANNEL {c}m {'REPRODUCED' if guards else '(unguarded)'}: +60m excess ${pooled['+60m']['mean_excess']:+.4f} on {len(ev['row'])} onsets")
        held = HOLD[ev["row"], ev["jf"]]
        samp = rng.choice(len(held), min(N_AUDIT, len(held)), replace=False)
        if any(loop_hold(ev["row"][k], ev["jf"][k]) != held[k] for k in samp):
            raise S.GateError(f"[HOLD] clock {c}: the minute mask and the loop disagree on V1's state at an onset")
        if all(loop_hold(ev["row"][k], ev["jf"][k] + 15) == held[k] for k in samp):
            raise S.GateError(f"[HOLD] clock {c}: the state check does not fire on a fill shifted by 15 minutes")
        r = {}
        # A1 V1 at the onsets, against V1's holding share at the same minutes on every short-gamma day
        r["A1_v1_holding_at_onsets"] = {}
        for sgn, nm in ((+1, "up"), (-1, "down")):
            m = ev["d"] == sgn
            r["A1_v1_holding_at_onsets"][nm] = {"n": int(m.sum()), "observed": float(held[m].mean()), "time_matched_base": float(holdfrac[ev["jf"][m]].mean())}
        # A2 the up channel at V1's deciding close (a 15-minute close j = ja - 1), against the same minutes' base rate
        pos = {int(d): q for q, d in enumerate(rows)}
        CU = cu.reshape(-1, nb)
        qs = np.array([pos[int(d)] for d in rows_s])
        jd = ja - 1
        bb = jd // c - 1
        agree = CU[np.array([pos[int(i)] for i in ii]), bb]
        r["A2_channel_up_at_v1_entries"] = {"n": int(len(ii)), "observed": float(agree.mean()), "time_matched_base": float(CU[qs][:, bb].mean(0).mean())}
        # A3 phi at every 15-minute close 09:45 .. 15:45 on short-gamma days
        b15 = np.arange(V.LAST_ENTRY_B + 1)
        vstate = ST[V1][rows_s][:, b15].ravel()
        cstate = CU[qs][:, (V.BAR_J[b15] // c) - 1].ravel()
        r["A3_phi_v1_vs_channel_up"] = float(np.corrcoef(vstate.astype(float), cstate.astype(float))[0, 1])
        r["A3_rates"] = {"v1_long": float(vstate.mean()), "channel_up": float(cstate.mean()), "both": float((vstate & cstate).mean())}
        # B the channel's onsets split by V1's state at the fill
        r["B_channel_by_v1_state_60m"] = {}
        for sgn, nm in ((+1, "up"), (-1, "down")):
            for st_, lab in ((True, "v1_long"), (False, "v1_flat")):
                m = (ev["d"] == sgn) & (held == st_)
                r["B_channel_by_v1_state_60m"][f"{nm}_{lab}"] = C.profile(PM, {k: v[m] for k, v in ev.items()}, mbar, usd, rows_s.size)[f"+{C.H_PRIMARY}m"]
            m = ev["d"] == sgn
            r["B_channel_by_v1_state_60m"][f"{nm}_pooled"] = C.profile(PM, {k: v[m] for k, v in ev.items()}, mbar, usd, rows_s.size)[f"+{C.H_PRIMARY}m"]
        # C V1's trades split by the channel's agreement at the deciding close
        ctrl = (mbar[jb] - mbar[ja]) * usd
        r["C_v1_by_channel_up"] = {}
        for st_, lab in ((True, "channel_up"), (False, "no_channel_up")):
            m = agree == st_
            ex, tx = C.cl_t(vg[m] - ctrl[m], ii[m]) if m.sum() > 2 else (float("nan"), float("nan"))
            r["C_v1_by_channel_up"][lab] = {"n": int(m.sum()), "mean_net": float(vn[m].mean()) if m.any() else None, "mean_gross": float(vg[m].mean()) if m.any() else None,
                                            "median_net": float(np.median(vn[m])) if m.any() else None, "hit": float((vn[m] > 0).mean()) if m.any() else None,
                                            "drift_excess": ex, "t_excess": tx}
        # the declared reading
        Bq = r["B_channel_by_v1_state_60m"]
        up_pool, up_flat = Bq["up_pooled"]["mean_excess"], Bq["up_v1_flat"]
        Cq = r["C_v1_by_channel_up"]
        same = (up_flat["mean_excess"] < up_pool / 3 and abs(up_flat["t_excess"]) < 1 and Cq["no_channel_up"]["mean_gross"] >= 2 / 3 * float(vg.mean()))
        indep = up_flat["mean_excess"] >= 2 / 3 * up_pool
        cond = (Cq["channel_up"]["mean_net"] is not None and Cq["no_channel_up"]["mean_net"] is not None
                and Cq["channel_up"]["mean_net"] - Cq["no_channel_up"]["mean_net"] >= cost)
        flags = ["SAME INFORMATION"] if same else [f for f, x in (("INDEPENDENT", indep), ("CONDITIONER CANDIDATE", cond)) if x]
        r["reading"] = flags or ["MIXED"]
        res["clocks"][c] = r
        A1, A2 = r["A1_v1_holding_at_onsets"], r["A2_channel_up_at_v1_entries"]
        log(f"  {c:>2}m A: V1 long at up onsets {A1['up']['observed']:.3f} (base {A1['up']['time_matched_base']:.3f}), at down onsets {A1['down']['observed']:.3f} "
            f"(base {A1['down']['time_matched_base']:.3f}); up channel at V1 entries {A2['observed']:.3f} (base {A2['time_matched_base']:.3f}); phi {r['A3_phi_v1_vs_channel_up']:+.3f}")
        log(f"  {c:>2}m B (+60m excess): " + " | ".join(f"{k} n{v['n']} ${v['mean_excess']:+.2f} (t {v['t_excess']:+.2f}) hit {v['hit']:.3f}" for k, v in Bq.items()))
        log(f"  {c:>2}m C (V1 trades): " + " | ".join(f"{k} n{v['n']} net ${v['mean_net']:+.2f} gross ${v['mean_gross']:+.2f} median ${v['median_net']:+.2f} hit {v['hit']:.3f} "
                                                       f"drift excess ${v['drift_excess']:+.2f} (t {v['t_excess']:+.2f})" for k, v in Cq.items()))
        log(f"  {c:>2}m READING: {r['reading']}")
    return res


def run(data_root: Path, log=P) -> int:
    t0 = time.time()
    D, PM, pidx, O1, H1, L1, C1, valid = C.load(data_root, log)
    E = S.d685()
    mes = E.cost_spec("ES", "micro")
    short = D["G_SUM"].to_numpy(float) < 0
    a = json.loads(D699_JSON.read_text(encoding="utf-8"))["variants"][V1]["2_book"]
    b = json.loads(D700_JSON.read_text(encoding="utf-8"))["clocks"]
    guards = {"v1_trades": a["trades"], "v1_mean_net": a["mean_net"], "ch_excess": {c: b[str(c)]["profile"]["short_gamma"]["+60m"]["mean_excess"] for c in CLOCKS}}
    res = core(O1, H1, L1, C1, valid, PM, pidx, short, mes["usd_per_point"], mes["cost_rt_usd"], log, guards=guards)
    res = {"spec": "D701 DIAG (in-sample; the overlap of D700's channel onsets and D699's V1 on short-gamma days)", "cost_rt_usd": mes["cost_rt_usd"], **res,
           "timing_s": round(time.time() - t0, 1)}
    OUT.write_text(json.dumps(res, indent=1, default=lambda o_: o_.item() if hasattr(o_, "item") else str(o_)), encoding="utf-8")
    log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']} s")
    return 0


def selftest(log=P) -> int:
    """Synthetic random-walk sessions through every path of core() (no guards: nothing to reproduce)."""
    rng = np.random.default_rng(11)
    n = 150
    lr = 0.0002 * rng.standard_normal((n, 390, 4))
    base = 4000.0 * np.exp(np.cumsum(lr.reshape(n, -1), axis=1)).reshape(n, 390, 4)
    O1 = base[:, :, 0]; C1 = base[:, :, 3]; H1 = base.max(2); L1 = base.min(2)
    PM = np.column_stack([O1[:, 0], C1])
    pidx = np.arange(40, n)
    short = rng.random(pidx.size) < 0.5
    C.PROBE_LIMIT = {1: 3000, 5: 3000, 15: 1500}
    res = core(O1, H1, L1, C1, np.ones(n, bool), PM, pidx, short, 5.0, 4.42, log, parallel=False)
    assert set(res["clocks"]) == set(CLOCKS)
    log("  SELFTEST PASSED")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a_ = ap.parse_args()
    sys.exit(run(a_.data_root) if a_.run else selftest() if a_.selftest else 1)
