"""D520 defect 2 -- WHY the h09..h15 both-ends share reads 55.6% on CL, NG, RB and HO.

    python scripts/d520_day_session_coverage.py            # SYSTEM interpreter (databento)
    python scripts/d520_day_session_coverage.py --no-archive   # fixture terms only, either interpreter

    -> data/d520_day_session_coverage.json

Data layer only: this counts bars and hours. Nothing here computes a return.

THE THREE TERMS IT SEPARATES, because the 55.6% is not one thing
---------------------------------------------------------------
1. **Sunday rows.** A builder that keys a session row on every calendar day carrying volume makes a
   row for Sunday -- Globex reopens 18:00 ET Sunday -- and that row can NEVER have a day session:
   its day hours are Sunday daytime and its evening is Saturday. Those bars belong to Monday's row.
   Measured on the 36-root breadth fixture, which keeps such rows (D467's PRESENT rule drops them).
2. **A pre-June-2015 hole in the archive** on CL, NG, RB and HO specifically: the 1-minute bars stop
   at 14:30-15:17 ET and hours 15 and 16 are all but empty, while GC, SI, ZN, ZB, 6E and BZ are
   complete from 2010. Measured from the archive itself, per ET hour, on the FRONT contract.
3. **The known index gap** (D462): the archive holds 21-42% of the index day session before 2016.
   The energy roots sit in that gap too, on hours 21->14, and lose 15->16 on top of it.

It also NAMES the object behind D467's G2 "holiday artefact" on 6E, because a count is not an
object: instrument_id 2584's ten-lot on 2021-12-24.

The per-hour tables re-decode a handful of archive files with THIS script's own root list -- the
D467 builder only carries nine roots and NG, RB and HO are not among them -- and cache to temp/.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_fut_sessions_hourly as B      # noqa: E402  (et_days, PX, CHUNK -- no builder change)

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"
FIX = REPO / "data" / "fixtures"
CACHE = REPO / "temp" / "d520_hours"
OUT = REPO / "data" / "d520_day_session_coverage.json"

ENERGY = ("CL", "NG", "RB", "HO")
ROOTS = ENERGY + ("BZ", "GC", "SI", "ZN", "ZB", "6E", "ES", "NQ", "ZC")
RE_OUT = re.compile(r"^(" + "|".join(sorted(ROOTS, key=len, reverse=True))
                    + r")([FGHJKMNQUVXZ])(\d{1,2})$")
HRS = list(range(18, 24)) + list(range(0, 18))
# one file per era the tables need, plus the two that bracket the June-2015 cutover
FILES = ("glbx-mdp3-20100606-20101231", "glbx-mdp3-20130101-20131231",
         "glbx-mdp3-20140630-20141231", "glbx-mdp3-20150101-20151231",
         "glbx-mdp3-20160101-20161231", "glbx-mdp3-20200101-20201231")
NAMED_FILE = "glbx-mdp3-20210101-20211231"
NAMED_ID = 2584


def ids_of(store):
    """The same window table as the builder's, over THIS script's wider root list."""
    rows = []
    for sym, ivs in store.metadata.mappings.items():
        m = RE_OUT.match(str(sym))
        if not m:
            continue
        for iv in (ivs if isinstance(ivs, list) else [ivs]):
            sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
            if not sid:
                continue
            s = iv["start_date"] if isinstance(iv, dict) else getattr(iv, "start_date")
            e = iv["end_date"] if isinstance(iv, dict) else getattr(iv, "end_date")
            rows.append((int(sid), m.group(1), str(sym),
                         pd.Timestamp(s, tz="UTC").value, pd.Timestamp(e, tz="UTC").value))
    w = pd.DataFrame(rows, columns=["iid", "root", "contract", "w0", "w1"]).astype(
        {"iid": np.int64, "w0": np.int64, "w1": np.int64})
    assert not w.duplicated(["iid", "w0"]).any(), "[IDS] repeated (instrument_id, window start)"
    return w


def hours_of(stem: str) -> pd.DataFrame:
    """Per (root, contract, ET day, ET hour): bars, volume, last minute. Cached."""
    cp = CACHE / f"{stem}.parquet"
    if cp.exists():
        return pd.read_parquet(cp)
    import databento as db
    hits = sorted(RAW.glob(f"*/{stem}.ohlcv-1m.dbn.zst"))
    assert len(hits) == 1, f"{stem}: {len(hits)} matches"
    store = db.DBNStore.from_file(hits[0])
    w = ids_of(store)
    parts = []
    for arr in store.to_ndarray(count=B.CHUNK):
        sel = np.isin(arr["instrument_id"], w["iid"].to_numpy(np.int64))
        a = arr[sel]
        if not a.size:
            continue
        raw = pd.DataFrame({"iid": a["instrument_id"].astype(np.int64),
                            "ts": a["ts_event"].astype(np.int64),
                            "volume": a["volume"].astype(np.int64)})
        j = raw.merge(w, on="iid", how="inner")
        j = j[(j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])]
        assert not j.duplicated(["iid", "ts"]).any(), "[IDS] a bar claimed by two windows"
        ts = pd.to_datetime(j["ts"].to_numpy(), utc=True).tz_convert("US/Eastern")
        minute = (ts.hour * 60 + ts.minute).to_numpy()
        parts.append(pd.DataFrame({"root": j["root"].to_numpy(), "contract": j["contract"].to_numpy(),
                                   "day": B.et_days(ts), "hour": (minute // 60).astype(np.int16),
                                   "minute": minute.astype(np.int16),
                                   "volume": j["volume"].to_numpy()}).groupby(
            ["root", "contract", "day", "hour"], sort=False).agg(
            bars=("volume", "size"), volume=("volume", "sum"), last_min=("minute", "max")).reset_index())
    H = pd.concat(parts, ignore_index=True).groupby(
        ["root", "contract", "day", "hour"], as_index=False).agg(
        bars=("bars", "sum"), volume=("volume", "sum"), last_min=("last_min", "max"))
    CACHE.mkdir(parents=True, exist_ok=True)
    H.to_parquet(cp, index=False)
    return H


def front_of(H: pd.DataFrame, root: str) -> pd.DataFrame:
    d = H[H["root"] == root]
    v = d.groupby(["day", "contract"], as_index=False)["volume"].sum()
    return v.sort_values(["day", "volume"], kind="stable").groupby("day").tail(1)[["day", "contract"]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-archive", action="store_true", help="skip the terms that re-read the archive")
    a = ap.parse_args()
    rep: dict = {}

    # ---- term 1: the Sunday rows, on the fixture that keeps them -------------------------------
    Bf = pd.read_csv(FIX / "fut_breadth_hourly.csv.gz", usecols=["root", "day", "h09_o", "h15_c"],
                     dtype={"root": str, "day": str})
    Bf["p"] = np.isfinite(Bf["h09_o"].to_numpy(float) * Bf["h15_c"].to_numpy(float))
    Bf["wd"] = pd.to_datetime(Bf["day"]).dt.dayofweek
    t1 = {}
    print("=== term 1: the breadth fixture keys a row on every day with volume, Sundays included ===")
    print(f"{'root':>5} {'rows':>6} {'Sunday':>7} {'share':>7} {'all':>7} {'<2016':>7} {'2016+':>7} "
          f"{'2016+ M-F':>10} {'Sun w/ day':>11}")
    for r in list(ENERGY) + ["BZ", "GC", "SI", "ZN", "ZB", "6E", "ES", "NQ"]:
        d = Bf[Bf["root"] == r]
        if not len(d):
            continue
        pre = (d["day"] < "2016-01-01").to_numpy()
        post = d[~pre]
        t1[r] = {"rows": len(d), "sunday_rows": int((d["wd"] == 6).sum()),
                 "both_ends_all": float(d["p"].mean()),
                 "both_ends_pre2016": float(d["p"].to_numpy()[pre].mean()) if pre.any() else None,
                 "both_ends_2016plus": float(post["p"].mean()),
                 "both_ends_2016plus_mon_fri": float(post[post["wd"] < 5]["p"].mean()),
                 "sunday_rows_2016plus_with_day_session": int(post[post["wd"] == 6]["p"].sum()),
                 "sunday_rows_2016plus": int((post["wd"] == 6).sum())}
        x = t1[r]
        print(f"{r:>5} {x['rows']:>6} {x['sunday_rows']:>7} {x['sunday_rows'] / x['rows']:>7.1%} "
              f"{x['both_ends_all']:>7.3f} {x['both_ends_pre2016']:>7.3f} "
              f"{x['both_ends_2016plus']:>7.3f} {x['both_ends_2016plus_mon_fri']:>10.3f} "
              f"{x['sunday_rows_2016plus_with_day_session']:>5} /{x['sunday_rows_2016plus']:>5}")
    rep["term1_sunday_rows"] = t1
    cl = t1["CL"]
    n_pre = int(round(cl["rows"] * 0 + (Bf[(Bf["root"] == "CL")]["day"] < "2016-01-01").sum()))
    rep["term1_arithmetic"] = {
        "note": "the headline share is the two eras' shares weighted by their row counts",
        "n_pre2016": n_pre, "n_2016plus": cl["rows"] - n_pre,
        "reconstructed": (cl["both_ends_pre2016"] * n_pre
                          + cl["both_ends_2016plus"] * (cl["rows"] - n_pre)) / cl["rows"],
        "reported": cl["both_ends_all"]}
    print(f"  CL check: {cl['both_ends_pre2016']:.3f}*{n_pre} + "
          f"{cl['both_ends_2016plus']:.3f}*{cl['rows'] - n_pre} over {cl['rows']} = "
          f"{rep['term1_arithmetic']['reconstructed']:.4f}  (reported {cl['both_ends_all']:.4f})")

    # ---- the same question on THIS fixture, which drops those rows -----------------------------
    S = pd.read_csv(FIX / "fut_sessions_hourly.csv.gz", usecols=["root", "day", "h09_o", "h15_c"],
                    dtype={"root": str, "day": str})
    S["p"] = np.isfinite(S["h09_o"].to_numpy(float) * S["h15_c"].to_numpy(float))
    t1b = {}
    print("\n=== the nine-root fixture (PRESENT rule drops the thin rows); G5 gates the pre-2016 era out ===")
    for r in sorted(S["root"].unique()):
        d = S[S["root"] == r]
        pre = (d["day"] < "2016-01-01").to_numpy()
        t1b[r] = {"rows": len(d), "both_ends_all": float(d["p"].mean()),
                  "both_ends_pre2016": float(d["p"].to_numpy()[pre].mean()) if pre.any() else None,
                  "both_ends_2016plus": float(d["p"].to_numpy()[~pre].mean()),
                  "sessions_per_year": {y: int(n) for y, n in d["day"].str[:4].value_counts().sort_index().items()}}
        print(f"{r:>5} rows {t1b[r]['rows']:>5}  both-ends all {t1b[r]['both_ends_all']:.3f}  "
              f"<2016 {str(round(t1b[r]['both_ends_pre2016'], 3)) if pre.any() else '   -  '}  "
              f"2016+ {t1b[r]['both_ends_2016plus']:.3f}")
    rep["nine_root_fixture"] = t1b

    if a.no_archive:
        OUT.write_text(json.dumps(rep, indent=1, default=float), encoding="utf-8")
        print(f"\nwrote {OUT.relative_to(REPO)} (fixture terms only)")
        return 0

    # ---- term 2 and 3: the archive's own per-hour coverage, on the FRONT contract ---------------
    rep["term2_hour_coverage"] = {}
    for stem in FILES:
        H = hours_of(stem)
        era = stem[10:]
        print(f"\n=== {era}: days on which the FRONT contract carries a bar, per ET hour ===")
        print(f"{'root':>5} " + " ".join(f"{h:>3}" for h in HRS) + "   ndays")
        blk = {}
        for r in ROOTS:
            if not (H["root"] == r).any():
                continue
            fr = front_of(H, r)
            m = H[H["root"] == r].merge(fr, on=["day", "contract"], how="inner")
            per = m.groupby("hour")["day"].nunique()
            tail = H[(H["root"] == r) & (H["hour"] <= 17)].groupby("day")["last_min"].max()
            blk[r] = {"front_days_per_hour": {int(h): int(per.get(h, 0)) for h in HRS},
                      "n_days": int(fr["day"].nunique()),
                      "session_tail_last_min_p50": float(tail.median()),
                      "all_contract_days_per_hour": {
                          int(h): int(H[(H["root"] == r) & (H["hour"] == h)]["day"].nunique()) for h in HRS}}
            print(f"{r:>5} " + " ".join(f"{blk[r]['front_days_per_hour'][h]:>3}" for h in HRS)
                  + f"   {blk[r]['n_days']:>5}  tail p50 "
                    f"{int(blk[r]['session_tail_last_min_p50']) // 60:02d}:"
                    f"{int(blk[r]['session_tail_last_min_p50']) % 60:02d} ET")
        rep["term2_hour_coverage"][era] = blk

    # ---- the cutover month, from the two files that bracket it ---------------------------------
    print("\n=== days per month carrying an h15 bar (any contract): the cutover is June 2015 ===")
    cut = {}
    for stem in ("glbx-mdp3-20140630-20141231", "glbx-mdp3-20150101-20151231"):
        H = hours_of(stem)
        h = H[H["hour"] == 15]
        for r in list(ENERGY) + ["BZ", "GC", "ES"]:
            d = h[h["root"] == r]
            if not len(d):
                continue
            cut.setdefault(r, {}).update({k: int(v) for k, v in
                                          d.groupby(d["day"].str[:7])["day"].nunique().items()})
    for r, v in cut.items():
        print(f"  {r:>4} " + " ".join(f"{k[2:]}:{n}" for k, n in sorted(v.items())))
    rep["cutover_h15_days_per_month"] = cut

    # ---- name the 6E "holiday artefact" --------------------------------------------------------
    import databento as db
    hits = sorted(RAW.glob(f"*/{NAMED_FILE}.ohlcv-1m.dbn.zst"))
    store = db.DBNStore.from_file(hits[0])
    carried = {}
    for sym, ivs in store.metadata.mappings.items():
        for iv in (ivs if isinstance(ivs, list) else [ivs]):
            sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
            try:
                sid = int(sid)
            except (TypeError, ValueError):
                continue
            if sid == NAMED_ID:
                carried[str(sym)] = [str(iv["start_date"]), str(iv["end_date"])]
    rows = [arr[arr["instrument_id"] == NAMED_ID] for arr in store.to_ndarray(count=B.CHUNK)]
    arr = np.concatenate([x for x in rows if x.size])
    ts = pd.to_datetime(arr["ts_event"].astype(np.int64), utc=True).tz_convert("US/Eastern")
    d = pd.DataFrame({"day": B.et_days(ts), "close": arr["close"] * B.PX,
                      "volume": arr["volume"].astype(np.int64)})
    g = d.groupby("day").agg(bars=("volume", "size"), volume=("volume", "sum"), px=("close", "median"))
    xmas = {k: dict(bars=int(v.bars), volume=int(v.volume), price=float(v.px))
            for k, v in g.loc[[x for x in g.index if x >= "2021-12-15"]].iterrows()}
    rep["named_6E_holiday_artefact"] = {
        "instrument_id": NAMED_ID, "file": NAMED_FILE, "symbols_carried": carried,
        "only_outright_among_them": [s for s in carried if RE_OUT.match(s)],
        "days_with_bars_in_2021": int(len(g)), "total_bars": int(g["bars"].sum()),
        "total_volume": int(g["volume"].sum()), "december_days": xmas}
    print(f"\n=== D467's G2 'holiday artefact' on 6E, named ===\n  id {NAMED_ID} carried: {carried}")
    print(f"  the only outright among them: {rep['named_6E_holiday_artefact']['only_outright_among_them']}"
          f"  -> the flat dict's label for EVERY bar of this id")
    for k, v in xmas.items():
        print(f"    {k}  {v['bars']:>3} bars  {v['volume']:>6} contracts  price {v['price']:.4f}")

    OUT.write_text(json.dumps(rep, indent=1, default=float), encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
