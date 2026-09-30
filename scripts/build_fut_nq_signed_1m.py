"""D717 fixture: NQ aggressor-signed volume per regular-session minute, 2016-01-04 -> 2023-12-29, from Sierra Chart's
NQ tick files. It reuses D695's ES builder (`build_fut_es_signed_1m.py`) unchanged: the same record layout, session
slice, minute convention, cutoff and validation, with only the root changed.

    uv run python scripts/build_fut_nq_signed_1m.py --data-root "<main checkout>/data"

Source: C:\\SierraChart\\Data\\NQ{H,M,U,Z}{15..23}-CME.scid, each session's front contract (fut_index_sessions, root NQ),
09:30-16:00 ET only. Output (gitignored, the data root's fixtures): fut_NQ_signed_1m.csv.gz and its meta.
VALIDATION (declared in D717 s.2, before this builder): against fut_NQ_rth_1m, V1 median volume ratio in [0.98, 1.02],
V2 per-minute volume correlation >= 0.98, V3 signed share >= 0.99, V4 last trade = bar close on >= 95 % of minutes.
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
ROOT = "NQ"


def main(data_root: Path) -> int:
    t0 = time.time()
    fx = data_root / "fixtures"
    sess = pd.read_csv(fx / "fut_index_sessions.csv.gz", usecols=["root", "day", "contract"], dtype=str, encoding="utf-8")
    sess = sess[(sess["root"] == ROOT) & (sess["day"] >= B.FIRST) & (sess["day"] < B.CUTOFF)]
    if (sess["day"] >= B.CUTOFF).any():
        raise B.BuildError("a session on or after the cutoff reached the builder")
    sess = sess.assign(sc=[B.sierra_code(c, d) for c, d in zip(sess["contract"], sess["day"])])
    jobs = [(c, sorted(g["day"])) for c, g in sess.groupby("sc")]
    missing = [c for c, _ in jobs if not (B.SC_DATA / f"{c}-CME.scid").exists()]
    if missing:
        raise B.BuildError(f"no Sierra file for {missing}")
    print(f"  {len(sess)} {ROOT} sessions over {len(jobs)} contracts", flush=True)
    parts = []
    with ProcessPoolExecutor(max_workers=B.N_WORKERS) as ex:
        futs = {ex.submit(B.build_contract, jb): jb[0] for jb in jobs}
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
           "V4_within_one_tick_share": float((np.abs(j["last"] - j["close"]) <= 0.25 + 1e-9).mean())}
    val["pass"] = bool(0.98 <= val["V1_median_volume_ratio"] <= 1.02 and val["V2_volume_correlation"] >= 0.98 and val["V3_signed_share"] >= 0.99 and val["V4_last_equals_close_share"] >= 0.95)
    print("  VALIDATION: " + json.dumps(val), flush=True)
    t.drop(columns=["last"]).to_csv(fx / f"fut_{ROOT}_signed_1m.csv.gz", index=False, compression="gzip", encoding="utf-8")
    meta = {"record": "D717", "builder": "scripts/build_fut_nq_signed_1m.py", "reuses": "scripts/build_fut_es_signed_1m.py (D695)", "source": str(B.SC_DATA),
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
