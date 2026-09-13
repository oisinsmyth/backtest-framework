"""STAGE 0, step 3: what does it actually COST to cross in the micro metals and gas?

Steps 1-2 found MNG, MHG and SIL exist and trade 3,191 / 5,090 / 24,932 lots a day-session against
our one-lot trade. That is ample volume. It is NOT the cost. The affordability screen assumed a
crossing of 1.009 ticks, which was measured on LIQUID roots (D485/D504); if these micros quote two
or three ticks wide the screen's 4.8-8.3% becomes 10-20% and the story dies here.

Measured from the tbbo tape, which carries the BBO standing before each trade:
  * the quoted spread in TICKS at trade time -- p50, and the share of trades at exactly one tick
  * the effective half-spread |price - mid| in ticks, which is what a taker actually pays
  * depth at the touch, because a one-tick quote on 2 lots is not a one-tick quote for us

NO RETURN IS READ AS A P&L (R15). References: MGC, MCL, MNQ -- micros we already price.

    python working/stage0_micro_spread.py            # SYSTEM python (databento)
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
# tick in POINTS, measured from the archive in step 2; the dollar value needs the contract unit
TICK_PTS = {"MNG": 0.001, "MHG": 0.0005, "SIL": 0.005, "MGC": 0.1, "MCL": 0.01, "MNQ": 0.25, "MES": 0.25}
ROOTS = list(TICK_PTS)
RE_ROOT = re.compile(r"^(" + "|".join(sorted(ROOTS, key=len, reverse=True)) + r")([FGHJKMNQUVXZ])(\d{1,2})$")
DAY_LO, DAY_HI = 540, 959


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
            rows.append((int(sid), m.group(1), str(sym),
                         np.uint64(pd.Timestamp(s, tz="UTC").value), np.uint64(pd.Timestamp(e, tz="UTC").value)))
    w = pd.DataFrame(rows, columns=["iid", "root", "contract", "w0", "w1"])
    assert not w.duplicated(["iid", "w0"]).any(), "[IDS] repeated (instrument_id, window start)"
    return w


def main():
    tb = sorted((REPO / "data" / "raw" / "databento").glob("*/*.tbbo.dbn.zst"))
    assert tb, "no tbbo files"
    f = tb[-1]
    print(f"decoding {f.name} ({f.stat().st_size/1e9:.1f} GB)\n", flush=True)
    t0 = time.time()
    store = db.DBNStore.from_file(f)
    w = windows(store)
    print(f"{w['root'].nunique()} roots, {len(w):,} mapping windows\n", flush=True)

    parts = []
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
        # databento writes UNDEF_PRICE = INT64_MAX for a missing side. It is POSITIVE and enormous, so
        # `bid > 0` does not exclude it -- it produced a mean spread of 6.05e9 ticks on MHG before this.
        UNDEF = np.int64(2) ** 62
        good = (bid > 0) & (ask > 0) & (ask > bid) & (bid < UNDEF) & (ask < UNDEF)
        if not good.any():
            continue
        ts = pd.to_datetime(a["ts_event"][good], utc=True).tz_convert("US/Eastern")
        minute = ts.hour * 60 + ts.minute
        day = (minute >= DAY_LO) & (minute <= DAY_HI)
        if not day.any():
            continue
        parts.append(pd.DataFrame({
            "root": j["root"].to_numpy()[good][day],
            "spread_pts": (ask[good][day] - bid[good][day]) * PX,
            "half_pts": np.abs(a["price"][good][day].astype(np.int64) - (bid[good][day] + ask[good][day]) / 2.0) * PX,
            "bsz": a["bid_sz_00"][good][day].astype(np.int64),
            "asz": a["ask_sz_00"][good][day].astype(np.int64),
            "size": a["size"][good][day].astype(np.int64)}))
    T = pd.concat(parts, ignore_index=True)
    print(f"{len(T):,} day-session trades with a two-sided quote, {(time.time()-t0)/60:.1f} min\n")

    rows = []
    for root, g in T.groupby("root", sort=True):
        tk = TICK_PTS[root]
        sp = g["spread_pts"].to_numpy() / tk
        hf = g["half_pts"].to_numpy() / tk
        touch = np.minimum(g["bsz"].to_numpy(), g["asz"].to_numpy())
        rows.append(dict(root=root, trades=len(g), spread_p50=float(np.median(sp)),
                         spread_p90=float(np.quantile(sp, 0.90)), spread_mean=float(np.mean(sp)),
                         one_tick_share=float(np.mean(sp <= 1.0 + 1e-9)),
                         half_mean=float(np.mean(hf)), half_p50=float(np.median(hf)),
                         touch_p50=float(np.median(touch)),
                         touch_p10=float(np.quantile(touch, 0.10)), trade_p50=float(np.median(g["size"]))))
    d = pd.DataFrame(rows).sort_values("spread_mean")
    print(f"{'root':<6}{'trades':>10}{'sprd p50':>10}{'p90':>7}{'mean':>7}{'1-tick %':>10}{'half p50':>10}{'mean':>7}{'touch p50':>11}{'p10':>6}")
    for r in d.itertuples():
        star = "  <-- candidate" if r.root in ("MNG", "MHG", "SIL") else ""
        print(f"{r.root:<6}{r.trades:>10,}{r.spread_p50:>10.2f}{r.spread_p90:>7.2f}{r.spread_mean:>7.2f}"
              f"{100*r.one_tick_share:>9.1f}%{r.half_p50:>10.2f}{r.half_mean:>7.2f}{r.touch_p50:>11,.0f}{r.touch_p10:>6,.0f}{star}")
    print("\nspread and half-spread are in TICKS. The screen assumed 1.009 ticks round trip;")
    print("read 'mean' against that, and 'touch p10' against our one-lot trade.")
    d.to_csv(REPO / "working" / "stage0_micro_spread.csv", index=False)


if __name__ == "__main__":
    main()
