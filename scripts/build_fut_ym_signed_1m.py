"""D760 fixture: YM aggressor-signed volume per regular-session minute, 2016-01-04 -> 2023-12-29, from Sierra Chart's
YM tick files. It reuses D695's ES builder (`build_fut_es_signed_1m.py`): the same record layout, session slice, minute
convention, cutoff and validation. The one difference is the file suffix: Sierra holds YM as `-CBOT.scid`, so the
per-contract decoder is restated here with that suffix (D695's hardcodes `-CME`); its body is otherwise D695's.

    uv run --no-sync python scripts/build_fut_ym_signed_1m.py --data-root "<main checkout>/data"

Source: C:\\SierraChart\\Data\\YM{H,M,U,Z}{16..24}-CBOT.scid, each session's front contract (fut_index_sessions, root YM),
09:30-16:00 ET only. Output (gitignored, the data root's fixtures): fut_YM_signed_1m.csv.gz and its meta.
VALIDATION (declared in D760 s.2a, before this builder): against fut_YM_rth_1m, V1 median volume ratio in [0.98, 1.02],
V2 per-minute volume correlation >= 0.98, V3 signed share >= 0.99, V4 last trade = bar close on >= 95 % of minutes
(one YM tick is 1.0 point, for the within-one-tick share).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_fut_es_signed_1m as B   # noqa: E402  (D695's builder; importing defines, never runs)

REPO = Path(__file__).resolve().parents[1]
ROOT, SUFFIX, TICK = "YM", "-CBOT.scid", 1.0


def build_contract(args):
    """D695's build_contract with the CBOT suffix."""
    contract, days = args
    path = B.SC_DATA / f"{contract}{SUFFIX}"
    with open(path, "rb") as fh:
        head = fh.read(12)
    if head[:4] != b"SCID":
        raise B.BuildError(f"{path.name}: not an SCID file")
    hdr, rs = int.from_bytes(head[4:8], "little"), int.from_bytes(head[8:12], "little")
    if rs != B.REC.itemsize:
        raise B.BuildError(f"{path.name}: record size {rs} != {B.REC.itemsize}")
    mm = np.memmap(path, dtype=B.REC, mode="r", offset=hdr)
    dt_all = mm["dt"]
    out = []
    for day in days:
        rec = B.slice_session(mm, dt_all, day)
        if len(rec) == 0:
            continue
        k = ((rec["dt"] - B._us(pd.Timestamp(f"{day} 09:30", tz="America/New_York"))) // 60_000_000).astype(np.int64)
        if k.min() < 0 or k.max() > 389:
            raise B.BuildError(f"{contract} {day}: a trade falls outside 09:30-16:00")
        n = np.bincount(k, weights=rec["n"].astype(np.float64), minlength=390)
        v = np.bincount(k, weights=rec["v"].astype(np.float64), minlength=390)
        sell = np.bincount(k, weights=rec["bv"].astype(np.float64), minlength=390)
        buy = np.bincount(k, weights=rec["av"].astype(np.float64), minlength=390)
        lastpos = np.full(390, -1, dtype=np.int64)
        np.maximum.at(lastpos, k, np.arange(len(k)))
        live = v > 0
        mins = np.flatnonzero(live)
        out.append(pd.DataFrame({"day": day, "hhmm": [B.MINUTES[x] for x in mins], "contract": contract,
                                 "trades": n[live].astype(np.int64), "volume": v[live].astype(np.int64),
                                 "buy": buy[live].astype(np.int64), "sell": sell[live].astype(np.int64),
                                 "last": rec["c"][lastpos[live]].astype(np.float64)}))
    del dt_all, mm
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def main(data_root: Path) -> int:
    t0 = time.time()
    fx = data_root / "fixtures"
    sess = pd.read_csv(fx / "fut_index_sessions.csv.gz", usecols=["root", "day", "contract"], dtype=str, encoding="utf-8")
    sess = sess[(sess["root"] == ROOT) & (sess["day"] >= B.FIRST) & (sess["day"] < B.CUTOFF)]
    if (sess["day"] >= B.CUTOFF).any():
        raise B.BuildError("a session on or after the cutoff reached the builder")
    sess = sess.assign(sc=[B.sierra_code(c, d) for c, d in zip(sess["contract"], sess["day"])])
    jobs = [(c, sorted(g["day"])) for c, g in sess.groupby("sc")]
    missing = [c for c, _ in jobs if not (B.SC_DATA / f"{c}{SUFFIX}").exists()]
    if missing:
        raise B.BuildError(f"no Sierra file for {missing}")
    print(f"  {len(sess)} {ROOT} sessions over {len(jobs)} contracts", flush=True)
    parts = []
    with ProcessPoolExecutor(max_workers=B.N_WORKERS) as ex:
        futs = {ex.submit(build_contract, jb): jb[0] for jb in jobs}
        for f in as_completed(futs):
            parts.append(f.result())
            print(f"    {futs[f]} done ({len(parts)}/{len(jobs)}, {time.time() - t0:.0f} s)", flush=True)
    t = pd.concat(parts, ignore_index=True).sort_values(["day", "hhmm"]).reset_index(drop=True)
    if (t["day"] >= B.CUTOFF).any():
        raise B.BuildError("a row on or after the cutoff survived")
    b = pd.read_csv(fx / f"fut_{ROOT}_rth_1m.csv.gz", usecols=["day", "hhmm", "contract", "close", "volume"], dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
    b = b[(b["day"] >= B.FIRST) & (b["day"] < B.CUTOFF)]
    b = b.assign(contract=[B.sierra_code(c, d) for c, d in zip(b["contract"], b["day"])])
    j = t.merge(b, on=["day", "hhmm", "contract"], how="inner")
    ratio = j["volume_x"] / j["volume_y"].where(j["volume_y"] > 0)
    val = {"minutes_sierra": int(len(t)), "minutes_databento": int(len(b)), "minutes_matched": int(len(j)),
           "V1_median_volume_ratio": float(ratio.median()), "V1_ratio_p10_p90": [float(ratio.quantile(0.1)), float(ratio.quantile(0.9))],
           "V2_volume_correlation": float(np.corrcoef(j["volume_x"], j["volume_y"])[0, 1]),
           "V3_signed_share": float((t["buy"] + t["sell"]).sum() / t["volume"].sum()),
           "V4_last_equals_close_share": float((np.abs(j["last"] - j["close"]) < 1e-6).mean()),
           "V4_within_one_tick_share": float((np.abs(j["last"] - j["close"]) <= TICK + 1e-9).mean())}
    val["pass"] = bool(0.98 <= val["V1_median_volume_ratio"] <= 1.02 and val["V2_volume_correlation"] >= 0.98 and val["V3_signed_share"] >= 0.99 and val["V4_last_equals_close_share"] >= 0.95)
    print("  VALIDATION: " + json.dumps(val), flush=True)
    t.drop(columns=["last"]).to_csv(fx / f"fut_{ROOT}_signed_1m.csv.gz", index=False, compression="gzip", encoding="utf-8")
    meta = {"record": "D760", "builder": "scripts/build_fut_ym_signed_1m.py", "reuses": "scripts/build_fut_es_signed_1m.py (D695)", "source": str(B.SC_DATA),
            "root": ROOT, "sessions": int(sess["day"].nunique()), "span": [t["day"].min(), t["day"].max()], "cutoff": B.CUTOFF,
            "contracts": [c for c, _ in jobs], "validation": val,
            "columns": {"trades": "Sierra NumTrades", "volume": "TotalVolume", "buy": "AskVolume (buyer-initiated)", "sell": "BidVolume (seller-initiated)"},
            "built_seconds": round(time.time() - t0, 1)}
    (fx / f"fut_{ROOT}_signed_1m.meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"  wrote fut_{ROOT}_signed_1m in {time.time() - t0:.0f} s; validation pass {val['pass']}", flush=True)
    return 0 if val["pass"] else 2


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    sys.exit(main(a.data_root))
