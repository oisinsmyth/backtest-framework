"""D273 -- the volume profile as a travel estimator.
Pre-registered in `docs/decisions/D273-the-profile-as-a-travel-estimator.md`,
commit 241c304, BEFORE this file was written.

    uv run python scripts/run_travel_estimator.py

Conditional on a short signal having fired, does the room below -- the distance
to the next high-volume node -- predict how far the trade travels?

T4 IS THE HURDLE THAT MATTERS. Node spacing scales with ATR by construction, so
"lots of room" may simply mean "high ATR", which trivially means large moves.
This programme has been fooled by exactly that twice: rel_vol was a volatility
selector (D270), mass_imbalance was impulse_md at -0.83 (D272). So the room
effect must survive WITHIN ATR terciles, not merely across them.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.research.terrain import VolumeProfileSensor  # noqa: E402


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


P = _load("d272", "run_volume_profile.py")
A = _load("d271", "d271_trade_anatomy.py")
V, C, R, M, D = P.V, P.C, P.R, P.M, P.D

OUT = REPO / "data" / "d273_travel_summary.json"
ARMS = ("S1_short_intra", "S2_short_intra")
N_Q, N_TERCILE, N_SIMS, SEED = 5, 3, 300, 0
HVN_Q = P.HVN_Q


def trades_with_room(pos, closes, rets, syms, start, sess_end, sensor, bars_by_sym, vol):
    """Every trade, with the room to the next mapped HVN below its entry.

    R9: the profile is built at `index = t - 1` and the entry price is read at
    `t - 1`; `density()` slices everything after `index` before any arithmetic."""
    out, unmapped = [], 0
    n, T = pos.shape
    for i in range(n):
        s = pos[i]
        ent = np.flatnonzero((s[start:] != 0.0) & (s[start - 1:-1] == 0.0)) + start
        dens, built_at = None, -10 ** 9
        for t in ent:
            if t - built_at >= P.REBUILD_EVERY:
                try:
                    dens = sensor.density(bars_by_sym[i], t - 1, list(vol[i]))
                    built_at = t
                except (ValueError, IndexError):
                    dens = None
            if dens is None:
                continue
            px = float(closes[i, t - 1])
            atr = dens.bucket_width / P.BUCKET_ATR
            if atr <= 0:
                continue
            below = [h for h in dens.levels(HVN_Q, "hvn") if h < px]
            if not below:
                unmapped += 1
                continue
            close = int(sess_end[t])
            z = np.flatnonzero(s[t:close] == 0.0)
            ex = t + int(z[0]) if z.size else close
            path = -np.cumsum(rets[i, t:ex])           # SHORT: profit when price falls
            target = (px - max(below)) / px            # fractional fall to the support
            out.append({"sym": syms[i], "room_atr": (px - max(below)) / atr,
                        "atr_frac": atr / px,
                        "pnl_bp": float(path[-1]) * 1e4 if path.size else 0.0,
                        "mfe_bp": float(path.max()) * 1e4 if path.size else 0.0,
                        "reached": bool(path.size and path.max() >= target),
                        "bars": int(ex - t)})
    return out, unmapped


def qmeans(vals, keys, nq=N_Q):
    v, k = np.asarray(vals, float), np.asarray(keys, float)
    edges = np.quantile(k, np.linspace(0, 1, nq + 1)[1:-1])
    idx = np.searchsorted(edges, k, side="right")
    return [v[idx == q] for q in range(nq)]


def main() -> int:
    rp, rc = R.load_full()
    panel, cleaned = R.subset(rp, rc, R.STRATA["ALL"])
    first, _ = D.session_structure(panel.dates)
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    T = panel.closes.shape[1]
    sess_end, _ = A.session_maps(first, T)
    vol_all, _, _ = V.load_volume(panel)
    sensor = VolumeProfileSensor(P.LOOKBACK_BARS, P.BUCKET_ATR, P.VOLUME_UNITS,
                                 atr_window=P.ATR_WINDOW)

    payload, cells = {"cells": {}}, {}
    for st in ("ALL", "LOW", "HIGH"):
        p, cl = ((panel, cleaned) if st == "ALL" else R.subset(rp, rc, R.STRATA[st]))
        keep = [panel.symbols.index(s) for s in p.symbols]
        books = R.build_books(p, cl, start, first)
        c2 = 2.0 * float(np.mean(p.cost_fraction) * 1e4)
        bars_by_sym = [cl[s] for s in p.symbols]
        print("=" * 86)
        print(f"{st}   cost bar 2c = {c2:.2f} bp")
        print("=" * 86)
        for arm in ARMS:
            tr, unmapped = trades_with_room(books[arm], p.closes, p.total_log_returns,
                                            p.symbols, start, sess_end, sensor,
                                            bars_by_sym, vol_all[keep])
            if len(tr) < N_Q * 30:
                print(f"  {arm:16s} only {len(tr)} trades -- too thin, skipped")
                continue
            room = [x["room_atr"] for x in tr]
            pnl = [x["pnl_bp"] for x in tr]
            mfe = [x["mfe_bp"] for x in tr]
            reached = [1.0 * x["reached"] for x in tr]
            atr = [x["atr_frac"] for x in tr]

            qp = qmeans(pnl, room)
            mns = np.array([q.mean() if q.size else np.nan for q in qp])
            dd = np.diff(mns)
            t1 = bool(np.all(dd > 0) or np.all(dd < 0))
            t2 = bool(mns[-1] >= c2)
            # correlation of the score with the thing that could be faking it
            rho_atr = float(np.corrcoef(np.argsort(np.argsort(room)),
                                        np.argsort(np.argsort(atr)))[0, 1])
            qm = np.array([q.mean() for q in qmeans(mfe, room)])
            qr = np.array([q.mean() for q in qmeans(reached, room)])

            # ---- T4: the ATR control ----
            te = np.quantile(atr, [1 / 3, 2 / 3])
            tid = np.searchsorted(te, atr, side="right")
            spreads = []
            for g in range(N_TERCILE):
                m = tid == g
                if m.sum() < N_Q * 20:
                    spreads.append(np.nan)
                    continue
                qg = qmeans(np.array(pnl)[m], np.array(room)[m])
                spreads.append(float(qg[-1].mean() - qg[0].mean())
                               if qg[-1].size and qg[0].size else np.nan)
            t4 = bool(np.nansum(np.array(spreads) > 0) >= 2)

            key = f"{st}:{arm}"
            cells[key] = {"n": len(tr), "unmapped": unmapped, "cost_bp": c2,
                          "quintile_pnl_bp": mns.tolist(),
                          "quintile_mfe_bp": qm.tolist(),
                          "quintile_reached": qr.tolist(),
                          "spread_bp": float(mns[-1] - mns[0]),
                          "rho_room_atr": rho_atr,
                          "atr_tercile_spreads": spreads,
                          "T1": t1, "T2": t2, "T4": t4,
                          "room": room, "pnl": pnl}
            print(f"\n  {arm}   {len(tr):,} trades ({unmapped:,} with no mapped support below)")
            print(f"    room quintile ->  " + "  ".join(f"Q{i+1}" for i in range(N_Q)))
            print(f"    P&L bp            " + "  ".join(f"{m:+6.2f}" for m in mns)
                  + f"   spread {mns[-1]-mns[0]:+6.2f}   T1 {'YES' if t1 else 'no'}"
                    f"  T2 {'YES' if t2 else 'no'}")
            print(f"    MFE bp            " + "  ".join(f"{m:+6.2f}" for m in qm))
            print(f"    reached support   " + "  ".join(f"{m:6.1%}" for m in qr))
            print(f"    rho(room, ATR) = {rho_atr:+.3f}")
            print(f"    T4 ATR terciles: " + "  ".join(
                f"{s:+.2f}" if s == s else "  n/a" for s in spreads)
                + f"   -> {'PASS' if t4 else 'FAIL'}")
        print()

    # ---- T3: shuffle floor, one shared draw across all cells ----
    print("computing the T3 shuffle floor ...", flush=True)
    rng = np.random.default_rng(SEED)
    best = np.empty(N_SIMS)
    for s in range(N_SIMS):
        seed = int(rng.integers(0, 2 ** 31 - 1))
        vals = []
        for k, c in cells.items():
            r2 = np.random.default_rng(seed)
            sh = r2.permutation(np.asarray(c["room"]))
            q = qmeans(c["pnl"], sh)
            vals.append(abs(float(q[-1].mean() - q[0].mean())))
        best[s] = max(vals) if vals else 0.0
        if (s + 1) % 100 == 0:
            print(f"  {s + 1}/{N_SIMS}", flush=True)
    floor = float(np.percentile(best, 95))
    print(f"\nT3 floor (p95 of best-of-{len(cells)} |spread|): {floor:.2f} bp\n")

    print(f"  {'cell':22s} {'spread':>8s} {'T1':>4s} {'T2':>4s} {'T3':>4s} {'T4':>4s}  ALL FOUR")
    surv = []
    for k, c in cells.items():
        c["T3"] = abs(c["spread_bp"]) > floor
        c["clears_all"] = c["T1"] and c["T2"] and c["T3"] and c["T4"]
        if c["clears_all"]:
            surv.append(k)
        for f in ("room", "pnl"):
            c.pop(f)
        print(f"  {k:22s} {c['spread_bp']:7.2f}b "
              + "  ".join(f"{'YES' if c[x] else 'no':>3s}" for x in ("T1", "T2", "T3", "T4"))
              + f"   {'** YES **' if c['clears_all'] else 'no'}")
    print(f"\n  SURVIVORS: {surv or 'NONE'}")

    payload.update({"preregistration": "docs/decisions/D273-the-profile-as-a-travel-estimator.md",
                    "commit": "241c304", "T3_floor_bp": floor,
                    "cells": cells, "survivors": surv})
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
