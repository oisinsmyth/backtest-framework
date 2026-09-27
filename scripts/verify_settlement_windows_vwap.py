"""Which settlement window was in force? Measured from the trades themselves, for the index-reweight model's C0
(IR-A9; the principal, 2026-09-27: "source the settlement windows").

A CME active-month settlement is the VWAP of the outright trades in the settlement window, rounded to the tick. So on
every in-sample day, for each root, this rebuilds the VWAP of the most-traded Sierra contract from its 1-tick file,
over each candidate window, rounds it to the tick, and counts the days it equals the published settlement
(`fut_settle_strip`; KE from `ke_settle_strip`). The window that reproduces the settlement year after year is the
one in force; a change shows as a break between years.

Candidates per root: the documented current window (`data/settlement_windows.csv`, current_only rows); the same
window shifted -60 and +60 minutes; and each root's known or plausible predecessor (the grains' 13:59-14:00 CT of
SER-6245R; a 1-minute and a 2-minute livestock window ending 13:00 CT). CL and NG are the control: their window is
dated (SER-4867, 14:28-14:30 ET), so it must win.

Reads: trade prices and sizes inside the candidate windows only, and settlements. No signed flow, no relation to any
predicted flow, no return. Every read is cut at 2025-03-01 (IR-A1).

    uv run python scripts/verify_settlement_windows_vwap.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from backtest_framework.data.panels import load_panel  # noqa: E402

REC = REPO / "data" / "index_reweight" / "sierra_download_record.json"
KE_STRIP = REPO / "data" / "index_reweight" / "ke_settle_strip.csv.gz"
OUT = REPO / "data" / "settlement_windows_vwap_check.json"
SC = Path(r"C:\SierraChart\Data")
CUT = "2025-03-01"
HDR = 56
DT = np.dtype([("t", "<i8"), ("o", "<f4"), ("h", "<f4"), ("l", "<f4"), ("c", "<f4"), ("n", "<u4"), ("v", "<u4"),
               ("bv", "<u4"), ("av", "<u4")])
ORIGIN = pd.Timestamp("1899-12-30", tz="UTC")
TICK = {"GC": 0.1, "SI": 0.005, "HG": 0.0005, "ZC": 0.25, "ZS": 0.25, "ZW": 0.25, "KE": 0.25, "ZL": 0.01,
        "ZM": 0.1, "LE": 0.025, "HE": 0.025, "CL": 0.01, "NG": 0.001}
CT, ET = "America/Chicago", "America/New_York"
# (label, tz, start, end): the documented current windows (data/settlement_windows.csv) and the candidates
DOC = {"GC": (ET, "13:29:00", "13:30:00"), "SI": (CT, "12:24:00", "12:25:00"), "HG": (ET, "12:59:00", "13:00:00"),
       "ZC": (CT, "13:14:00", "13:15:00"), "ZS": (CT, "13:14:00", "13:15:00"), "ZW": (CT, "13:14:00", "13:15:00"),
       "KE": (CT, "13:14:00", "13:15:00"), "ZL": (CT, "13:14:00", "13:15:00"), "ZM": (CT, "13:14:00", "13:15:00"),
       "LE": (CT, "12:59:30", "13:00:00"), "HE": (CT, "12:59:30", "13:00:00"),
       "CL": (ET, "14:28:00", "14:30:00"), "NG": (ET, "14:28:00", "14:30:00")}
EXTRA = {r: [("SER-6245R 13:59-14:00 CT", CT, "13:59:00", "14:00:00")] for r in ("ZC", "ZS", "ZW", "KE", "ZL", "ZM")}
EXTRA.update({r: [("1 min 12:59-13:00 CT", CT, "12:59:00", "13:00:00"),
                  ("2 min 12:58-13:00 CT", CT, "12:58:00", "13:00:00")] for r in ("LE", "HE")})


def shift(hhmmss: str, minutes: int) -> str:
    t = pd.Timestamp("2000-01-01 " + hhmmss) + pd.Timedelta(minutes=minutes)
    return t.strftime("%H:%M:%S")


def candidates(root: str) -> list[tuple[str, str, str, str]]:
    tz, a, b = DOC[root]
    out = [("documented", tz, a, b), ("documented -60 min", tz, shift(a, -60), shift(b, -60)),
           ("documented +60 min", tz, shift(a, 60), shift(b, 60))]
    return out + EXTRA.get(root, [])


def us(day: str, tz: str, hhmmss: str) -> int:
    ts = pd.Timestamp(f"{day} {hhmmss}", tz=tz).tz_convert("UTC")
    return int((ts - ORIGIN) / pd.Timedelta(microseconds=1))


def strip_code(sym: str) -> tuple[str, str]:
    root, mon, yy = sym[:2], sym[2], sym[3:5]
    return root, f"{root}{mon}{int(yy) % 10}"


def main() -> int:
    rec = json.loads(REC.read_text(encoding="utf-8"))["contracts"]
    st = load_panel("fut_settle_strip", reserved_from=CUT, usecols=["root", "contract", "ref", "settle"]).frame
    ke = pd.read_csv(KE_STRIP, encoding="utf-8", dtype={"root": str, "contract": str, "ref": str})
    strip = pd.concat([st, ke], ignore_index=True)
    strip = strip[(strip["ref"] >= "2015-12-01") & (strip["ref"] < CUT)]
    settle = {(r, c, d): float(s) for r, c, d, s in zip(strip["root"], strip["contract"], strip["ref"], strip["settle"])}
    res: dict[str, Any] = {}
    for root in DOC:
        cands = candidates(root)
        syms = sorted(s for s, v in rec.items() if v["root"] == root)
        per_day: dict[str, dict[str, Any]] = {}
        for sym in syms:
            p = SC / f"{sym}.scid"
            if not p.exists() or p.stat().st_size <= HDR:
                continue
            a = np.memmap(p, dtype=DT, mode="r", offset=HDR)
            t = a["t"]
            code = strip_code(sym)[1]
            first = pd.Timestamp(int(t[0]), unit="us", tz="UTC") + (ORIGIN - pd.Timestamp("1970-01-01", tz="UTC"))
            last = pd.Timestamp(int(t[-1]), unit="us", tz="UTC") + (ORIGIN - pd.Timestamp("1970-01-01", tz="UTC"))
            for day in pd.bdate_range(first.date(), min(last.date(), pd.Timestamp(CUT).date() - pd.Timedelta(days=1))):
                d = day.strftime("%Y-%m-%d")
                s = settle.get((root, code, d))
                if s is None:
                    continue
                vw = {}
                for lab, tz, x, y in cands:
                    i, j = np.searchsorted(t, [us(d, tz, x), us(d, tz, y)])
                    if j > i:
                        v = a["v"][i:j].astype(np.float64)
                        c = a["c"][i:j].astype(np.float64)
                        if v.sum() > 0:
                            vw[lab] = (float((c * v).sum() / v.sum()), float(v.sum()))
                if "documented" not in vw:
                    continue
                # the active month: the contract with the most volume in the documented window that day
                if d in per_day and per_day[d]["vol"] >= vw["documented"][1]:
                    continue
                per_day[d] = {"sym": sym, "settle": s, "vol": vw["documented"][1], "vwap": vw}
        tick = TICK[root]
        years: dict[str, dict[str, Any]] = {}
        for d, x in per_day.items():
            y = years.setdefault(d[:4], {"days": 0, **{lab: 0 for lab, *_ in cands}})
            y["days"] += 1
            for lab, *_ in cands:
                if lab in x["vwap"]:
                    r = round(x["vwap"][lab][0] / tick) * tick
                    if abs(r - x["settle"]) <= tick / 2 + 1e-9:
                        y[lab] += 1
        table = {}
        for yr, y in sorted(years.items()):
            shares = {lab: round(y[lab] / y["days"], 4) for lab, *_ in cands}
            table[yr] = {"days": y["days"], "exact_share": shares, "best": max(shares, key=lambda k: shares[k])}
        res[root] = {"candidates": [list(c) for c in cands], "by_year": table}
        print(root, {yr: (v["days"], v["best"], v["exact_share"]["documented"]) for yr, v in table.items()}, flush=True)
    OUT.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
