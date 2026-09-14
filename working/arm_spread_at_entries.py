"""Is the admitted arm's 1.009-tick crossing assumption defensible AT THE MOMENTS IT ACTUALLY TRADES?

The arm enters at the OPEN of an hourly segment (d491_conditional_hold: `px` is the segment open)
and is forced flat at the CLOSE of h15. So its fills land at hh:00 ET and at the 15:59 close -- not
at a random moment. The cost line charges $3 + 1.009 ticks = $3.50 round trip on MNQ, and 1.009
ticks is one full quoted spread.

The census in working/stage0_micro_spread.py found MNQ's spread at trade time has a MEDIAN of 1.00
tick but a MEAN of 1.55, with only 56.8% of trades seeing a one-tick market. That is trade-weighted
over the whole day session. This asks the narrower question: are the arm's OWN moments wider?

THE LIMITATION, stated first: tbbo spans 2025-09-11..2026-09-11 and the arm's in-sample window is
2016-2023. THERE IS NO QUOTE DATA AT THE ARM'S HISTORICAL ENTRIES. This cannot price the backtest.
What it can do is test whether the hourly open is a systematically worse moment than the baseline
the 1.009 figure was drawn from -- which is a property of the convention, not of the window.

NO P&L, no position (R15).

    python working/arm_spread_at_entries.py            # SYSTEM python (databento)
"""
from __future__ import annotations
import re
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
import databento as db

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import build_fut_breadth_hourly as B  # noqa: E402

PX = 1e-9
CHUNK = 5_000_000
TICK_PTS = 0.25                       # MNQ, CME-verified in futures_contract_specs.json
ASSUMED = 1.009                       # the arm's crossing, in ticks, round trip
RE_ROOT = re.compile(r"^(MNQ)([FGHJKMNQUVXZ])(\d{1,2})$")
ENTRY_HOURS = (10, 11, 12, 13, 14, 15)     # the arm decides at h09..h14 close, fills at the next hour's open
DAY_LO, DAY_HI = 540, 959                  # 09:00..15:59 ET
N_FILES = 3                                # spread across the tbbo year; the comparison is WITHIN each file


def windows(store):
    rows = []
    for sym, ivs in store.metadata.mappings.items():
        m = RE_ROOT.match(str(sym))
        if not m:
            continue
        for iv in (ivs if isinstance(ivs, list) else [ivs]):
            sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
            if not sid:
                continue
            s = iv["start_date"] if isinstance(iv, dict) else getattr(iv, "start_date")
            e = iv["end_date"] if isinstance(iv, dict) else getattr(iv, "end_date")
            rows.append((int(sid), str(sym),
                         np.uint64(pd.Timestamp(s, tz="UTC").value), np.uint64(pd.Timestamp(e, tz="UTC").value)))
    w = pd.DataFrame(rows, columns=["iid", "contract", "w0", "w1"])
    assert not w.duplicated(["iid", "w0"]).any(), "[IDS] repeated (instrument_id, window start)"
    return w


def main():
    tb = sorted((REPO / "data" / "raw" / "databento").glob("*/*.tbbo.dbn.zst"))
    pick = [tb[i] for i in np.linspace(0, len(tb) - 1, N_FILES).astype(int)]
    print(f"{len(tb)} tbbo files; using {N_FILES}: {[f.name[10:18] for f in pick]}")
    print(f"MNQ tick {TICK_PTS} points; the arm assumes {ASSUMED} ticks round trip\n", flush=True)
    t0 = time.time()
    parts = []
    for f in pick:
        store = db.DBNStore.from_file(f)
        w = windows(store)
        for arr in store.to_ndarray(count=CHUNK):
            raw = pd.DataFrame({"iid": arr["instrument_id"].astype(np.uint32),
                                "ts": arr["ts_event"].astype(np.uint64),
                                "_i": np.arange(len(arr), dtype=np.int64)})
            j = raw.merge(w, on="iid", how="inner")
            j = j[(j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])]
            if not len(j):
                continue
            k = j["_i"].to_numpy()
            a = arr[k]
            bid = a["bid_px_00"].astype(np.int64); ask = a["ask_px_00"].astype(np.int64)
            UND = np.int64(2) ** 62
            good = (bid > 0) & (ask > 0) & (ask > bid) & (bid < UND) & (ask < UND)
            if not good.any():
                continue
            ts = pd.to_datetime(a["ts_event"][good], utc=True).tz_convert("US/Eastern")
            minute = ts.hour * 60 + ts.minute
            day = (minute >= DAY_LO) & (minute <= DAY_HI)
            if not day.any():
                continue
            parts.append(pd.DataFrame({
                "contract": j["contract"].to_numpy()[good][day],
                "day": ts.strftime("%Y-%m-%d")[day],
                "hour": ts.hour[day], "minute": ts.minute[day], "second": ts.second[day],
                "spread_tk": ((ask[good][day] - bid[good][day]) * PX / TICK_PTS),
                "bsz": a["bid_sz_00"][good][day].astype(np.int64),
                "asz": a["ask_sz_00"][good][day].astype(np.int64)}))
        print(f"  {f.name[10:18]} done ({(time.time()-t0)/60:.1f} min)", flush=True)
    T = pd.concat(parts, ignore_index=True)
    # the arm trades the front month; take the busiest contract per day
    top = T.groupby(["day", "contract"]).size().reset_index(name="n").sort_values("n")
    front = top.groupby("day").tail(1)[["day", "contract"]]
    T = T.merge(front, on=["day", "contract"], how="inner")
    T["touch"] = np.minimum(T["bsz"], T["asz"])
    print(f"\n{len(T):,} front-month day-session trades over {T['day'].nunique()} sessions\n")

    def row(label, m):
        g = T[m]
        if not len(g):
            return
        sp = g["spread_tk"].to_numpy()
        print(f"  {label:<44}{len(g):>10,}{np.median(sp):>9.2f}{sp.mean():>8.2f}"
              f"{100*np.mean(sp <= 1.0 + 1e-9):>9.1f}%{np.median(g['touch']):>9.0f}"
              f"{sp.mean()/ASSUMED:>9.2f}x")

    print(f"  {'window':<44}{'trades':>10}{'p50':>9}{'mean':>8}{'1-tick':>10}{'touch':>9}{'vs 1.009':>10}")
    row("ALL day-session trades (the baseline)", np.ones(len(T), bool))
    inhour = T["hour"].isin(ENTRY_HOURS)
    for w_ in (1, 5, 30, 60):
        row(f"first {w_:>2}s of an entry hour (10:00-15:00)", inhour & (T["minute"] == 0) & (T["second"] < w_))
    row("the whole first minute of an entry hour", inhour & (T["minute"] == 0))
    row("the forced flat: 15:59", (T["hour"] == 15) & (T["minute"] == 59))
    row("09:30-09:31, the RTH open (not an arm moment)", (T["hour"] == 9) & (T["minute"].isin([30, 31])))

    print(f"\n  by entry hour, first 30 seconds:")
    print(f"  {'hour':<44}{'trades':>10}{'p50':>9}{'mean':>8}{'1-tick':>10}{'touch':>9}{'vs 1.009':>10}")
    for h in ENTRY_HOURS:
        row(f"{h:02d}:00:00-{h:02d}:00:29", (T["hour"] == h) & (T["minute"] == 0) & (T["second"] < 30))

    base = T["spread_tk"].mean()
    ent = T[inhour & (T["minute"] == 0) & (T["second"] < 30)]["spread_tk"].mean()
    print(f"\n  baseline mean {base:.3f} ticks; arm-moment mean {ent:.3f} ticks; "
          f"ratio {ent/base:.3f}  ->  the arm's moments are "
          f"{'WORSE' if ent > base * 1.05 else ('BETTER' if ent < base * 0.95 else 'no different')} than the baseline")
    print(f"  the assumption is {ASSUMED} ticks: baseline is {base/ASSUMED:.2f}x it, arm moments {ent/ASSUMED:.2f}x it")
    T.to_csv(REPO / "working" / "arm_spread_at_entries.csv.gz", index=False, compression="gzip")


if __name__ == "__main__":
    main()
