"""The settlement-window flow panel for D635 (Gate C0): for every (root, contract, business day) with Sierra Chart
coverage, 2015-11-01 -> 2025-02-28, the Sierra-signed net aggressor volume, total volume and trade count inside the
settlement window served by `settlement_windows.window_for`, plus two prices for C0's price clause: the last trade at
or before t0 = W_start - 10 min (within 3 hours of it), and the last trade before W_end.

This is an INPUT. It prints coverage counts only: no flow statistic, and nothing set against any roll or predicted
flow. D635's POWER step reads its non-hedge-day rows (BD12-BD20) only; the runner reads the rest in its one run.
Every file is read only before 2025-03-01 (IR-A1). A (root, day) with no served window is skipped and counted.

    uv run python scripts/build_index_window_flow_panel.py      # -> data/index_reweight/window_flow_daily.csv.gz
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import settlement_windows as SW  # noqa: E402

REC = REPO / "data" / "index_reweight" / "sierra_download_record.json"
OUT = REPO / "data" / "index_reweight" / "window_flow_daily.csv.gz"
META = REPO / "data" / "index_reweight" / "window_flow_daily.meta.json"
SC = Path(r"C:\SierraChart\Data")
FIRST, CUT = "2015-11-01", "2025-03-01"
HDR = 56
DT = np.dtype([("t", "<i8"), ("o", "<f4"), ("h", "<f4"), ("l", "<f4"), ("c", "<f4"), ("n", "<u4"), ("v", "<u4"),
               ("bv", "<u4"), ("av", "<u4")])
ORIGIN = pd.Timestamp("1899-12-30", tz="UTC")
LETTER = "FGHJKMNQUVXZ"


def us(ts: pd.Timestamp) -> int:
    return int((ts - ORIGIN) / pd.Timedelta(microseconds=1))


def main() -> int:
    rec = json.loads(REC.read_text(encoding="utf-8"))["contracts"]
    rows = []
    skipped: dict[str, int] = {}
    for sym, meta in sorted(rec.items()):
        root = meta["root"]
        p = SC / f"{sym}.scid"
        if not p.exists() or p.stat().st_size <= HDR:
            continue
        a = np.memmap(p, dtype=DT, mode="r", offset=HDR)
        t = a["t"]
        first = ORIGIN + pd.Timedelta(microseconds=int(t[0]))
        last = ORIGIN + pd.Timedelta(microseconds=int(t[-1]))
        lo = max(pd.Timestamp(FIRST), first.tz_localize(None).normalize())
        hi = min(pd.Timestamp(CUT) - pd.Timedelta(days=1), last.tz_localize(None).normalize())
        ym = (2000 + int(sym[3:5]), LETTER.index(sym[2]) + 1)
        for day in pd.bdate_range(lo, hi):
            d = day.strftime("%Y-%m-%d")
            try:
                w = SW.window_for(root, d)
            except (SW.UnmappedProduct, SW.UnsourcedDate):
                skipped[root] = skipped.get(root, 0) + 1
                continue
            ws = pd.Timestamp(f"{d} {w.start_ct}", tz="America/Chicago").tz_convert("UTC")
            we = pd.Timestamp(f"{d} {w.end_ct}", tz="America/Chicago").tz_convert("UTC")
            t0 = ws - pd.Timedelta(minutes=10)
            i0, i, j = np.searchsorted(t, [us(t0 - pd.Timedelta(hours=3)), us(ws), us(we)])
            k0 = int(np.searchsorted(t, us(t0), side="right"))
            if j <= i and k0 <= i0:
                continue  # no trade in the window and none near t0: not a trading day for this contract
            v = a["v"][i:j].astype(np.int64)
            net = int((a["av"][i:j].astype(np.int64) - a["bv"][i:j].astype(np.int64)).sum())
            px0 = float(a["c"][k0 - 1]) if k0 > i0 else float("nan")
            px1 = float(a["c"][j - 1]) if j > int(np.searchsorted(t, us(t0 - pd.Timedelta(hours=3)))) else float("nan")
            rows.append((root, sym, ym[0], ym[1], d, w.start_ct, w.end_ct, net, int(v.sum()), j - i, px0, px1))
    df = pd.DataFrame(rows, columns=["root", "sym", "year", "month", "day", "window_start_ct", "window_end_ct",
                                     "net", "volume", "trades", "px_t0", "px_end"])
    if (df["day"] >= CUT).any():
        raise RuntimeError("a row on or after the cut")
    df.to_csv(OUT, index=False, encoding="utf-8", lineterminator="\n", compression={"method": "gzip", "mtime": 0})
    cov = {r: {"contracts": int(g["sym"].nunique()), "rows": int(len(g)), "days": int(g["day"].nunique()),
               "first": str(g["day"].min()), "last": str(g["day"].max())} for r, g in df.groupby("root")}
    META.write_text(json.dumps({"rows": len(df), "coverage": cov, "skipped_no_served_window": skipped,
                                "cut": CUT, "note": "an input: coverage only is reported"}, indent=1,
                               sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(df)} rows; skipped (no served window): {skipped}")
    for r, c in cov.items():
        print(f"  {r}: {c}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
