"""D461 stage 0 -- is prop-firm FORCED FLOW visible at the flatten minutes?

    python scripts/d461_flatten_flow.py --build    # raw DBN -> data/fixtures/micro_minute_volume.csv.gz
    python scripts/d461_flatten_flow.py --test

PRE-REGISTRATION: docs/decisions/D461-PRE-REG-stage-0-prop-firm-forced-flow-at-the-flatten-minutes.md

STAGE 0: NO RETURN IS READ. Volume shares and ranks only.

The statistic is each minute's share of the 16:00-17:00 ET hour's volume, and then the target
minutes' RANK among all 60 -- a rank rather than a threshold, because a threshold is a number I
would be choosing.

16:10 is the clean test (Topstep's 3:10 PM CT flatten and MFFU's 16:10 window; nothing structural
happens on CME at 16:10). 16:59 is the last minute before the 17:00 halt, so ANY squaring lands
there and it CANNOT identify -- it is reported as declared.

ABANDON CONDITIONS, from the pre-registration:
  A1  neither target minute in the TOP 5 of 60 in MES 2019-2026            -> abandon
  A2  MES's rank no better than ES's at the same minute                    -> abandon
  A3  ES 2010-2018 ranks the same as ES 2019-2026 at 16:10                 -> abandon
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

RAW = REPO / "data" / "raw" / "databento"
FIX = REPO / "data" / "fixtures" / "micro_minute_volume.csv.gz"
OUT = REPO / "data" / "d461_flatten_flow.json"

ROOTS = ("ES", "MES", "NQ", "MNQ", "M2K", "MYM")
SYM = re.compile(r"^([A-Z0-9]{1,4})[FGHJKMNQUVXZ][0-9]{1,2}$")
TARGETS = ("16:10", "16:59")
HOUR = [f"16:{m:02d}" for m in range(60)]


def build() -> int:
    import databento as db

    files = sorted(RAW.glob("*/*.ohlcv-1m.dbn.zst"))
    print(f"D461 build -- {len(files)} files, roots {ROOTS}\n")
    acc = []
    for i, f in enumerate(files, 1):
        store = db.DBNStore.from_file(f)
        ids = {}
        for sym, ivs in store.metadata.mappings.items():
            m = SYM.match(str(sym))
            if not m or m.group(1) not in ROOTS:
                continue
            for iv in (ivs if isinstance(ivs, list) else [ivs]):
                sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
                if sid:
                    ids[int(sid)] = m.group(1)
        arr = store.to_ndarray()
        a = arr[np.isin(arr["instrument_id"], np.fromiter(ids, dtype=np.uint32))]
        ts = pd.to_datetime(a["ts_event"], utc=True).tz_convert("US/Eastern")
        hh = ts.strftime("%H:%M")
        keep = np.isin(hh, HOUR)
        if not keep.any():
            print(f"  [{i:2d}/{len(files)}] no 16:xx bars")
            continue
        d = pd.DataFrame({"day": ts.strftime("%Y-%m-%d")[keep], "hhmm": hh[keep],
                          "root": [ids[int(x)] for x in a["instrument_id"][keep]],
                          "volume": a["volume"][keep].astype(np.int64)})
        # sum across contract months -- the root is the participant class, not the contract
        acc.append(d.groupby(["day", "hhmm", "root"], as_index=False)["volume"].sum())
        print(f"  [{i:2d}/{len(files)}] {len(d):>8,} bars in the hour")
    out = pd.concat(acc, ignore_index=True)
    FIX.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(FIX, index=False, compression="gzip")
    print(f"\n  wrote {FIX.relative_to(REPO)}  ({len(out):,} rows, "
          f"{out['day'].min()} .. {out['day'].max()})")
    return 0


def shares(g: pd.DataFrame) -> pd.Series:
    """Each minute's share of the hour's volume, averaged over DAYS (not pooled), so one
    enormous session cannot set the profile."""
    tot = g.groupby("day")["volume"].transform("sum")
    g = g.assign(share=np.where(tot > 0, g["volume"] / tot, np.nan))
    s = g.groupby("hhmm")["share"].mean()
    return s.reindex(HOUR)


def report(g: pd.DataFrame, label: str, rows: list) -> dict:
    s = shares(g)
    rank = s.rank(ascending=False, method="min")
    n_days = g["day"].nunique()
    out = {"label": label, "days": n_days}
    for t in TARGETS:
        out[f"share_{t}"] = float(s.get(t, np.nan))
        out[f"rank_{t}"] = int(rank.get(t, 99)) if np.isfinite(s.get(t, np.nan)) else 99
    base = float(np.nanmedian(s.drop(index=[t for t in TARGETS if t in s.index])))
    out["baseline"] = base
    for t in TARGETS:
        out[f"lift_{t}"] = float(s.get(t, np.nan) / base) if base else float("nan")
    print(f"  {label:<22}{n_days:>7,}"
          + "".join(f"{out[f'rank_{t}']:>7}{100 * out[f'share_{t}']:>8.2f}%"
                    f"{out[f'lift_{t}']:>7.2f}x" for t in TARGETS))
    rows.append(out)
    return out


def test() -> int:
    g = pd.read_csv(FIX)
    g["year"] = g["day"].str.slice(0, 4).astype(int)
    print("D461 stage 0 -- forced flow at the flatten minutes\n")
    print(f"  {len(g):,} root-minute-days  {g['day'].min()} .. {g['day'].max()}")
    print(f"  roots present: {sorted(g['root'].unique())}\n")

    print(f"  {'cell':<22}{'days':>7}" + "".join(f"{'rk ' + t:>7}{'share':>9}{'lift':>10}"
                                                 for t in TARGETS))
    rows = []
    mes = report(g[(g["root"] == "MES") & (g["year"] >= 2019)], "MES 2019-2026", rows)
    es_new = report(g[(g["root"] == "ES") & (g["year"] >= 2019)], "ES  2019-2026", rows)
    es_old = report(g[(g["root"] == "ES") & (g["year"] <= 2018)], "ES  2010-2018", rows)
    for r in ("MNQ", "M2K", "MYM", "NQ"):
        sub = g[(g["root"] == r) & (g["year"] >= 2019)]
        if len(sub):
            report(sub, f"{r:<4}2019-2026", rows)

    print("\n  THE ABANDON CONDITIONS, as declared")
    a1 = min(mes["rank_16:10"], mes["rank_16:59"]) <= 5
    print(f"    A1  MES top-5 of 60 at either target:  "
          f"16:10 rank {mes['rank_16:10']}, 16:59 rank {mes['rank_16:59']}  -> "
          f"{'SURVIVES' if a1 else 'ABANDON'}")
    a2 = (mes["rank_16:10"] < es_new["rank_16:10"]) or (mes["rank_16:59"] < es_new["rank_16:59"])
    print(f"    A2  MES beats ES at the same minute:   "
          f"16:10 {mes['rank_16:10']} vs {es_new['rank_16:10']}, "
          f"16:59 {mes['rank_16:59']} vs {es_new['rank_16:59']}  -> "
          f"{'SURVIVES' if a2 else 'ABANDON'}")
    a3 = es_old["rank_16:10"] != es_new["rank_16:10"]
    print(f"    A3  ES 2010-2018 differs at 16:10:     "
          f"{es_old['rank_16:10']} vs {es_new['rank_16:10']}  -> "
          f"{'SURVIVES' if a3 else 'ABANDON'}")
    verdict = "CONTINUE to stage 1" if (a1 and a2 and a3) else "ABANDONED at stage 0"
    print(f"\n  A1 {'ok' if a1 else 'FAIL'}   A2 {'ok' if a2 else 'FAIL'}   "
          f"A3 {'ok' if a3 else 'FAIL'}   ->  {verdict}")

    print(f"\n  THE TOP 8 MINUTES IN MES 2019-2026, for shape")
    s = shares(g[(g["root"] == "MES") & (g["year"] >= 2019)]).sort_values(ascending=False)
    for m, v in s.head(8).items():
        flag = "  <- TARGET" if m in TARGETS else ""
        print(f"    {m}  {100 * v:>6.2f}%{flag}")

    rows.append({"label": "VERDICT", "A1": bool(a1), "A2": bool(a2), "A3": bool(a3),
                 "verdict": verdict})
    pd.DataFrame(rows).to_json(OUT, orient="records", indent=1)
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.build:
        return build()
    if a.test:
        return test()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
