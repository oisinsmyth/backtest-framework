"""D719's bar cache: the twelve roots' one-minute bars from fut_day1m.parquet, cut at 2023-12-29, into temp/.

    python scripts/build_d719_commodity_bars.py          # SYSTEM interpreter (pyarrow), as build_shock_phase2.py

Data layer only: no return, no signal. Writes temp/d719_bars/<ROOT>.csv.gz (day, contract, bar, open, close; bars 0 ..
the root's settlement-window end) and temp/d719_bars/meta.json, keyed on the fixture's size and mtime so
stage1_d719_commodity_settlement_f2.py refuses a stale cache. The seal: nothing dated 2024-01-01 or later is written, and
the reader asserts it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pyarrow.compute as pc
import pyarrow.dataset as ds

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "data" / "fixtures" / "fut_day1m.parquet"
OUT = REPO / "temp" / "d719_bars"
END, SEAL = "2023-12-29", "2024-01-01"
# the last bar needed per root: the bar starting W - 1 (bar 0 = 09:00 ET)
W_BAR = {"CL": 329, "NG": 329, "HO": 329, "RB": 329, "HG": 239, "GC": 269, "SI": 264,
         "ZC": 314, "ZS": 314, "ZW": 314, "ZL": 314, "ZM": 314}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    st = FIX.stat()
    meta = {"fixture": str(FIX.relative_to(REPO)), "size": st.st_size, "mtime_ns": st.st_mtime_ns, "end": END, "roots": {}}
    d = ds.dataset(FIX)
    for r, wb in W_BAR.items():
        f = (pc.field("root") == r) & (pc.field("day") <= END) & (pc.field("bar") <= wb)
        t = d.to_table(columns=["day", "contract", "bar", "open", "close"], filter=f).to_pandas()
        if (t["day"] >= SEAL).any():
            raise SystemExit(f"seal: {r} holds a day on or after {SEAL}")
        t = t.sort_values(["day", "bar"], kind="stable")
        t.to_csv(OUT / f"{r}.csv.gz", index=False, encoding="utf-8", compression="gzip")
        meta["roots"][r] = {"rows": int(len(t)), "days": int(t["day"].nunique()), "first": str(t["day"].min()),
                            "last": str(t["day"].max()), "close_sum": float(t["close"].sum()), "w_bar": wb}
        print(r, meta["roots"][r])
    (OUT / "meta.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
