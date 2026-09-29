"""D686 L1 input: ES's price at 15:45 ET per session, 2016-01-04 -> 2023-12-29 (design: D686 s.2, L1).

    python scripts/build_d686_es_1545.py --data-root "<main checkout>/data"      # SYSTEM python (needs pyarrow)

`fut_day1m.parquet` bars count minutes from 09:00 ET (`day_session_et_minutes` [540, 959]), so bar 404 is
15:44-15:45 and its close is the last trade before 15:45:00. ES settles at 16:00 ET, so the price is strictly before
the settlement. If bar 404 printed nothing, the last bar at or before it is used, and its index is recorded.
Writes the gitignored `data/d686_es_1545.csv.gz` (day, contract, bar, close) and prints its SHA-256.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d686_es_1545.csv.gz"
BAR_1545 = 404                       # minute 540 + 404 = 944 -> 15:44-15:45; its close is before 15:45:00
FIRST, CUTOFF = "2016-01-04", "2024-01-01"


def main() -> int:
    import pyarrow.compute as pc
    import pyarrow.dataset as ds
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    meta = json.loads((a.data_root / "fixtures" / "fut_day1m.meta.json").read_text(encoding="utf-8"))
    if meta["day_session_et_minutes"][0] != 540 or meta["bar_minutes"] != 1:
        raise SystemExit(f"[BARS] unexpected bar clock: {meta['day_session_et_minutes']}, {meta['bar_minutes']}")
    d = ds.dataset(a.data_root / "fixtures" / "fut_day1m.parquet")
    f = (pc.field("root") == "ES") & (pc.field("day") >= FIRST) & (pc.field("day") < CUTOFF) & \
        (pc.field("bar") <= BAR_1545)
    t = d.to_table(filter=f, columns=["day", "contract", "bar", "close"]).to_pandas()
    if len(t) and t["day"].max() >= CUTOFF:
        raise SystemExit("[WINDOW] a 2024 row survived the filter")
    if (t["bar"] > BAR_1545).any():
        raise SystemExit("[CAUSALITY] a bar at or after 15:45 survived the filter")
    t = t.sort_values(["day", "bar"]).groupby("day", as_index=False).last()
    t.to_csv(OUT, index=False, compression="gzip")
    h = hashlib.sha256(OUT.read_bytes()).hexdigest()
    print(f"{len(t)} sessions {t['day'].min()} -> {t['day'].max()}; bar 404 on {int((t['bar'] == BAR_1545).sum())}, "
          f"earlier bar on {int((t['bar'] < BAR_1545).sum())}; wrote {OUT.relative_to(REPO)} sha256 {h}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
