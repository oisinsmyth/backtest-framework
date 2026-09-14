"""D527 -- what does the admitted arm's crossing ACTUALLY cost, at the moments it actually fills?

The ledger charges the MACD day-session arm $3 + 1.009 ticks = $3.50 a round trip on MNQ. 1.009
ticks is one full quoted spread, and it is a market-wide average. The arm does not fill at an average
moment: d491_conditional_hold fills at the OPEN of an hourly segment and is forced flat at the CLOSE
of h15, so its fills land at hh:00 ET and at 15:59.

    python scripts/d527_arm_crossing_cost.py --spread    # SYSTEM python (databento), ~14 min: the tbbo census
    python scripts/d527_arm_crossing_cost.py --reprice   # seconds: the arm's fill clock, and the arm re-run at the measured cost

THE LIMITATION, first. tbbo spans 2025-09-11..2026-09-11; the arm's in-sample window is 2016-2023.
THERE IS NO QUOTE DATA AT THE ARM'S HISTORICAL ENTRIES and this cannot price the backtest. Worse for
the finding, the bias runs in the ARM'S FAVOUR: NQ was ~4,000 in 2016 and ~27,000 now against a
FIXED $0.50 tick, so the tick was relatively ~7x coarser then and a coarser tick locks the market at
one tick more often. The historical spread in TICKS was probably tighter than measured here. The
sound reading is forward-looking -- what the arm costs to trade TODAY.

Trade-weighting is the right weighting for this question and not a compromise: the arm's fill IS a
trade print, because the segment open is the hour's first trade.

NO new signal, no new construction, nothing admitted (R15). The arm's code is not touched -- the
instrumented copy of `simulate` is asserted bit-identical before its histogram is believed, and
everything is restricted to the in-sample window so the spent 2024+ slice is not re-read.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import re
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
OUT = REPO / "data" / "d527_arm_crossing_cost.json"
PX = 1e-9
CHUNK = 5_000_000
TICK_PTS = 0.25                          # MNQ, CME-verified
COMMISSION_RT = 3.00
TICK_USD = 0.50
ASSUMED_CROSS = 1.009
RE_ROOT = re.compile(r"^(MNQ)([FGHJKMNQUVXZ])(\d{1,2})$")
ENTRY_HOURS = (10, 11, 12, 13, 14, 15)
DAY_LO, DAY_HI = 540, 959
N_FILES = 3
INS_LO, INS_HI = "2016-01-04", "2023-12-29"


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ the spread census
def cmd_spread():
    import databento as db
    import build_fut_breadth_hourly as B  # noqa: F401  (kept: ohlcv_files convention)
    tb = sorted((REPO / "data" / "raw" / "databento").glob("*/*.tbbo.dbn.zst"))
    pick = [tb[i] for i in np.linspace(0, len(tb) - 1, N_FILES).astype(int)]
    print(f"{len(tb)} tbbo files; using {N_FILES}: {[f.name[10:18] for f in pick]}", flush=True)
    t0 = time.time()
    parts = []
    for f in pick:
        store = db.DBNStore.from_file(f)
        rows = []
        for sym, ivs in store.metadata.mappings.items():
            if not RE_ROOT.match(str(sym)):
                continue
            for iv in (ivs if isinstance(ivs, list) else [ivs]):
                sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
                if not sid:
                    continue
                s_ = iv["start_date"] if isinstance(iv, dict) else getattr(iv, "start_date")
                e_ = iv["end_date"] if isinstance(iv, dict) else getattr(iv, "end_date")
                rows.append((int(sid), str(sym), np.uint64(pd.Timestamp(s_, tz="UTC").value),
                             np.uint64(pd.Timestamp(e_, tz="UTC").value)))
        w = pd.DataFrame(rows, columns=["iid", "contract", "w0", "w1"])
        assert not w.duplicated(["iid", "w0"]).any(), "[IDS] repeated (instrument_id, window start)"
        for arr in store.to_ndarray(count=CHUNK):
            raw = pd.DataFrame({"iid": arr["instrument_id"].astype(np.uint32),
                                "ts": arr["ts_event"].astype(np.uint64),
                                "_i": np.arange(len(arr), dtype=np.int64)})
            j = raw.merge(w, on="iid", how="inner")
            j = j[(j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])]
            if not len(j):
                continue
            a = arr[j["_i"].to_numpy()]
            bid = a["bid_px_00"].astype(np.int64); ask = a["ask_px_00"].astype(np.int64)
            UND = np.int64(2) ** 62      # UNDEF_PRICE is INT64_MAX: POSITIVE, so `bid > 0` does not exclude it
            good = (bid > 0) & (ask > 0) & (ask > bid) & (bid < UND) & (ask < UND)
            if not good.any():
                continue
            ts = pd.to_datetime(a["ts_event"][good], utc=True).tz_convert("US/Eastern")
            minute = ts.hour * 60 + ts.minute
            day = (minute >= DAY_LO) & (minute <= DAY_HI)
            if not day.any():
                continue
            parts.append(pd.DataFrame({
                "contract": j["contract"].to_numpy()[good][day], "day": ts.strftime("%Y-%m-%d")[day],
                "hour": ts.hour[day], "minute": ts.minute[day], "second": ts.second[day],
                "spread_tk": (ask[good][day] - bid[good][day]) * PX / TICK_PTS}))
        print(f"  {f.name[10:18]} done ({(time.time()-t0)/60:.1f} min)", flush=True)
    T = pd.concat(parts, ignore_index=True)
    top = T.groupby(["day", "contract"]).size().reset_index(name="n").sort_values("n")
    T = T.merge(top.groupby("day").tail(1)[["day", "contract"]], on=["day", "contract"], how="inner")

    def stat(m):
        s = T.loc[m, "spread_tk"].to_numpy()
        return dict(n=int(len(s)), p50=float(np.median(s)), mean=float(s.mean()),
                    one_tick=float(np.mean(s <= 1.0 + 1e-9))) if len(s) else None

    res = dict(files=[f.name for f in pick], sessions=int(T["day"].nunique()), trades=int(len(T)),
               baseline=stat(np.ones(len(T), bool)),
               forced_flat_1559=stat((T["hour"] == 15) & (T["minute"] == 59)),
               entry_hours={}, entry_first30=stat(T["hour"].isin(ENTRY_HOURS) & (T["minute"] == 0) & (T["second"] < 30)))
    for h in ENTRY_HOURS:
        res["entry_hours"][str(h)] = stat((T["hour"] == h) & (T["minute"] == 0) & (T["second"] < 30))
    print(f"\n  baseline mean {res['baseline']['mean']:.3f} tk; entry moments {res['entry_first30']['mean']:.3f} tk; "
          f"forced flat {res['forced_flat_1559']['mean']:.3f} tk")
    for h, v in res["entry_hours"].items():
        print(f"    {h}:00 first 30s  n {v['n']:>8,}  p50 {v['p50']:.2f}  mean {v['mean']:.2f}  one-tick {100*v['one_tick']:.1f}%")
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    prev["spread_census"] = res
    OUT.write_text(json.dumps(prev, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


# ------------------------------------------------------------------ the arm's fill clock, and the reprice
def simulate_traced(D491, O, C, sig, first_decide, M, cost_ticks, tick_pts):
    """A verbatim copy of D491.simulate with the fill segments recorded. Equality is asserted by the caller."""
    n = O.shape[0]
    pos = np.zeros(n); entry_px = np.zeros(n); entry_t = np.full(n, -1, dtype=np.int64)
    pnl = np.zeros(n); trips = np.zeros(n)
    s_all = np.nan_to_num(sig, nan=0.0)
    entries, exits = [], []
    for t in range(first_decide, D491.LAST_SEG):
        s = s_all[:, t]; px = O[:, t + 1]
        live = pos != 0
        ex = live & ((t - entry_t) >= M) & (s * pos <= 0) & np.isfinite(px)
        pnl = np.where(ex, pnl + pos * (px - entry_px) / tick_pts - cost_ticks, pnl)
        trips = np.where(ex, trips + 1, trips); pos = np.where(ex, 0.0, pos)
        exits += [t + 1] * int(ex.sum())
        en = (pos == 0) & (s != 0) & np.isfinite(px)
        entry_px = np.where(en, px, entry_px); entry_t = np.where(en, t, entry_t); pos = np.where(en, s, pos)
        entries += [t + 1] * int(en.sum())
    cpx = C[:, D491.LAST_SEG]
    still = (pos != 0) & np.isfinite(cpx)
    pnl = np.where(still, pnl + pos * (cpx - entry_px) / tick_pts - cost_ticks, pnl)
    trips = np.where(still, trips + 1, trips)
    return pnl, trips, np.array(entries), np.array(exits), int(still.sum())


def cmd_reprice():
    art = json.loads(OUT.read_text())
    cen = art["spread_census"]
    SPREAD_AT = {int(h): v["mean"] for h, v in cen["entry_hours"].items()}
    FLAT = cen["forced_flat_1559"]["mean"]
    D491 = _load("d491x", "d491_conditional_hold.py")
    ARM = _load("d504x", "d504_arm_full_history.py")
    meta = json.loads(ARM.META.read_text(encoding="utf-8"))
    spec = json.loads(ARM.SPECS.read_text(encoding="utf-8"))
    b = ARM.build(pd.read_csv(ARM.FIX), meta, spec)
    days = np.asarray(b["days"], dtype=str)
    ins = (days >= INS_LO) & (days <= INS_HI)
    assert ins.sum() < len(days), "[WINDOW] the restriction selected everything"
    print(f"[WINDOW] {len(days):,} sessions built, {int(ins.sum()):,} in sample "
          f"({min(days[ins])}..{max(days[ins])}); {int((~ins).sum()):,} outside are NOT read")
    O, C, sig = b["O"][ins], b["C"][ins], b["AGREE"][ins]
    fd, M, cost, tick_pts, tick_usd = D491.DAY_FIRST_DECIDE, ARM.M_HOLD, b["cost"], b["tick_pts"], b["tick_usd"]
    p0, t0 = D491.simulate(O, C, sig, fd, M, cost, tick_pts)
    p1, t1, ent, exi, n_forced = simulate_traced(D491, O, C, sig, fd, M, cost, tick_pts)
    assert np.array_equal(p0, p1) and np.array_equal(t0, t1), "[TRACE] the copy is not the committed simulate"
    print(f"[TRACE] the instrumented copy reproduces simulate() bit-identically: "
          f"{len(p0):,} sessions, {t0.sum():,.0f} round trips\n")

    hour_of = lambda s: 9 + (s - fd)          # noqa: E731  segments are hourly; fd is the h09 segment
    e = pd.Series([hour_of(s) for s in ent]).value_counts().sort_index()
    tot = int(e.sum())
    print(f"  {'hour':>6}{'entries':>10}{'share':>9}{'spread tk':>11}")
    w = 0.0
    for h, n in e.items():
        w += (n / tot) * SPREAD_AT[h]
        print(f"  {h:>6}{n:>10,}{100*n/tot:>8.1f}%{SPREAD_AT[h]:>11.2f}")
    fshare = n_forced / t0.sum()
    exit_sp = fshare * FLAT + (1 - fshare) * w
    rt = 0.5 * w + 0.5 * exit_sp
    print(f"\n  entry-weighted {w:.3f} tk; exit-weighted {exit_sp:.3f} tk ({100*fshare:.0f}% forced flat)")
    print(f"  ROUND-TRIP CROSSING {rt:.3f} ticks against the assumed {ASSUMED_CROSS}")
    rows = {}
    for label, ct in (("assumed", cost), ("measured", COMMISSION_RT / tick_usd + rt)):
        p, tr = D491.simulate(O, C, sig, fd, M, ct, tick_pts)
        sc = D491.score(p, tick_usd)
        rows[label] = dict(cross_ticks=float(ct - COMMISSION_RT / tick_usd), rt_usd=float(COMMISSION_RT + (ct - COMMISSION_RT / tick_usd) * tick_usd),
                           sharpe=float(sc["sharpe"]), mean_usd=float(sc["mean_usd"]), total_usd=float(sc["mean_usd"] * len(p)))
        r = rows[label]
        print(f"  [{label:>8}] cross {r['cross_ticks']:.3f} tk = ${r['rt_usd']:.2f} RT   "
              f"net Sharpe {r['sharpe']:+.3f}   mean ${r['mean_usd']:+.2f}/session   total ${r['total_usd']:+,.0f}")
    art["reprice"] = dict(window=[INS_LO, INS_HI], sessions=int(len(p0)), trips=int(t0.sum()),
                          entries_by_hour={str(h): int(n) for h, n in e.items()},
                          forced_flat_share=float(fshare), entry_weighted_spread=float(w),
                          exit_weighted_spread=float(exit_sp), round_trip_crossing_ticks=float(rt),
                          assumed_crossing_ticks=ASSUMED_CROSS, scored=rows)
    OUT.write_text(json.dumps(art, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--spread", action="store_true")
    ap.add_argument("--reprice", action="store_true")
    a = ap.parse_args()
    if a.spread:
        cmd_spread()
    elif a.reprice:
        cmd_reprice()
    else:
        ap.error("pick --spread or --reprice")
