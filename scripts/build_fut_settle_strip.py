"""D556 -- the settlement-strip fixture: every settlement of every listed month for the 36 breadth roots,
from the CME `statistics` schema, and the derived front/next curve table that carry reads.

Spec: docs/decisions/D556-PRE-REG-carry-timing-as-published-on-36-CME-roots-and-the.md, committed
before this file (R8). Data layer only: no returns, no signal, no trade.

    python scripts/build_fut_settle_strip.py --probe                 # SYSTEM python (databento): one file, RSS, projected wall
    python scripts/build_fut_settle_strip.py --extract [--workers 8]  # SYSTEM python -> data/fixtures/fut_settle_strip.csv.gz
    uv run python scripts/build_fut_settle_strip.py --derive         # -> data/fixtures/fut_curve_front_next.csv.gz
    uv run python scripts/build_fut_settle_strip.py --gates          # G1..G4 -> the two .meta.json; raises on failure
    uv run python scripts/build_fut_settle_strip.py --selftest       # synthetic strip through derive() and ym()

Conventions (D526): `stat_type` 3 is the settlement, carried in `price` (x 1e-9); UNDEF (INT64_MAX) and
EXACT ZERO are both missing markers and are dropped; negatives are kept (CL settled -37.63 on
2020-04-20). A settlement is labelled with the session `ts_ref` + 1 day in ET, exactly as D526's strip.
Ids come from the WINDOWED mapping (D520/D521) via build_fut_open_interest.ids_of / label_rows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
FIX = REPO / "data" / "fixtures"
STRIP = FIX / "fut_settle_strip.csv.gz"
STRIP_META = FIX / "fut_settle_strip.meta.json"
CURVE = FIX / "fut_curve_front_next.csv.gz"
CURVE_META = FIX / "fut_curve_front_next.meta.json"
BREADTH = FIX / "fut_breadth_hourly.csv.gz"
D526_STRIP = REPO / "data" / "d526_curve_strip_CL_GC.csv.gz"
RAW = REPO / "data" / "raw" / "databento" / "GLBX-20260911-SDNLQ6M99S"
SPEC = "D556"
ST_SETTLE = 3
PX = 1e-9
UNDEF = np.iinfo(np.int64).max
MONTH = {c: i + 1 for i, c in enumerate("FGHJKMNQUVXZ")}
ROOTS = ("6A", "6B", "6C", "6E", "6J", "6S", "BTC", "BZ", "CL", "ES", "GC", "HE", "HG", "HO", "LE", "NG",
         "NKD", "NQ", "PA", "PL", "RB", "RTY", "SI", "SR3", "TN", "UB", "YM", "ZB", "ZC", "ZF", "ZL", "ZM",
         "ZN", "ZS", "ZT", "ZW")
RE_C = re.compile(r"^(" + "|".join(sorted(ROOTS, key=len, reverse=True)) + r")([FGHJKMNQUVXZ])(\d{1,2})$")
LIVE_START = {r: 2011 for r in ROOTS}; LIVE_START.update({"TN": 2016, "BTC": 2018, "RTY": 2018, "SR3": 2019})
G2_FRONT, G2_NEXT, G3_MEDIAN_MAX, G3_RAISE = 0.98, 0.95, 0.005, 0.02
SEGS = ["h18", "h19", "h20", "h21", "h22", "h23", "h00", "h01", "h02", "h03", "h04", "h05", "h06", "h07",
        "h08", "h09", "h10", "h11", "h12", "h13", "h14", "h15", "h16"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rss_mb():
    import os, subprocess
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {os.getpid()}", "/FO", "CSV", "/NH"], capture_output=True, text=True).stdout
        return float(out.strip().rsplit('","', 1)[-1].strip('"').replace(" K", "").replace(",", "")) / 1e3
    except Exception:
        return float("nan")


# ------------------------------------------------------------------ extraction (system python)
def worker(path):
    """One statistics file -> every settlement of the 36 roots' outrights, labelled by window."""
    import databento as db
    import build_fut_open_interest as OI                  # label_rows: the window join, generic over roots
    from build_fut_breadth_hourly import ids_of as ids36  # the 36-root windows; OI.ids_of is filtered to ITS four roots
    t0 = time.time()
    store = db.DBNStore.from_file(path)
    w = ids36(store)
    if w is None:
        return dict(file=Path(path).name, rows_in=0, rows_kept=0, secs=round(time.time() - t0, 1), rss_mb=round(rss_mb()), table=None)
    w = w[w["root"].isin(ROOTS)].reset_index(drop=True)
    keys = w["iid"].to_numpy(np.uint32)
    parts, n_in = [], 0
    for arr in store.to_ndarray(count=5_000_000):
        n_in += len(arr)
        a = arr[np.isin(arr["instrument_id"], keys) & (arr["stat_type"] == ST_SETTLE)]
        if not a.size:
            continue
        j = OI.label_rows(a, w)
        if not len(j):
            continue
        k = j["_i"].to_numpy()
        px = a["price"][k].astype("int64")
        ok = px != UNDEF
        if not ok.any():
            continue
        ts = pd.to_datetime(a["ts_ref"][k][ok].astype("int64"), utc=True).tz_convert("US/Eastern")
        parts.append(pd.DataFrame({"root": j["root"].to_numpy()[ok], "contract": j["contract"].to_numpy()[ok],
                                   "ref": (ts + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                                   "settle": px[ok] * PX}))
    d = pd.concat(parts, ignore_index=True) if parts else None
    return dict(file=Path(path).name, rows_in=n_in, rows_kept=int(len(d)) if d is not None else 0,
                secs=round(time.time() - t0, 1), rss_mb=round(rss_mb()), table=d)


def cmd_probe():
    fs = sorted(RAW.glob("*.statistics.dbn.zst"))
    f = fs[-2]
    r = worker(f)
    tot = sum(x.stat().st_size for x in fs)
    print(f"{f.name}: rows_in {r['rows_in']:,} kept {r['rows_kept']:,} in {r['secs']}s, worker RSS {r['rss_mb']} MB")
    print(f"projected: {tot / f.stat().st_size * r['secs'] / 60:.1f} min single-process; /8 workers ~ "
          f"{tot / f.stat().st_size * r['secs'] / 60 / 8 * 1.15:.1f} min; 8 workers x {r['rss_mb']} MB RSS")


def cmd_extract(workers):
    from multiprocessing import Pool
    fs = sorted(RAW.glob("*.statistics.dbn.zst"))
    print(f"D556 extract -- {len(fs)} statistics files ({sum(f.stat().st_size for f in fs) / 1e9:.1f} GB), {len(ROOTS)} roots, {workers} workers", flush=True)
    probe = worker(fs[0])
    print(f"  one worker measured before the pool: {probe['secs']}s, RSS {probe['rss_mb']} MB on {fs[0].name}", flush=True)
    t0 = time.time()
    with Pool(workers) as pool:
        res = pool.map(worker, [str(f) for f in fs])
    wall = time.time() - t0
    sec = sum(r["secs"] for r in res)
    print(f"[SPEED] sum(item time)/wall = {sec / wall:.2f}x on {workers} workers ({100 * sec / wall / workers:.0f}%)", flush=True)
    for r in res:
        print(f"  {r['file'][10:18]}  rows_in {r['rows_in']:>12,}  kept {r['rows_kept']:>9,}  {r['secs']:6.1f}s  RSS {r['rss_mb']} MB")
    D = pd.concat([r["table"] for r in res if r["table"] is not None], ignore_index=True)
    n_raw = len(D)
    D = D.drop_duplicates(["root", "contract", "ref"], keep="last")
    z = D["settle"] == 0.0
    n_zero = int(z.sum())
    zero_by_root = D[z].groupby("root").size().to_dict()
    D = D[~z]
    # a handful of settlements carry a weekend `ref` (a holiday-shifted ts_ref); they are not sessions
    wk = pd.to_datetime(D["ref"]).dt.dayofweek >= 5
    weekend = D[wk][["root", "ref"]].drop_duplicates().to_dict("records")
    D = D[~wk]
    # NEGATIVE settlements are kept only where the front-month trade itself printed negative -- CL in
    # April 2020 (-37.63 on 2020-04-20). The first build found nine others, each a single print on a
    # far-deferred month (6AN5 -0.0052 in January 2025, three 2019 soybean-meal months at -1.10 in
    # March 2016, TNZ0 -0.875, UBZ5 -117) with the magnitude of a daily CHANGE, not a price. They
    # are dropped and every dropped row is recorded here.
    neg = (D["settle"] < 0) & ~((D["root"] == "CL") & (D["ref"] >= "2020-04-17") & (D["ref"] <= "2020-04-22"))
    dropped_neg = D[neg].to_dict("records")
    D = D[~neg].sort_values(["root", "ref", "contract"]).reset_index(drop=True)
    D.to_csv(STRIP, index=False, compression="gzip", encoding="utf-8")
    meta = dict(spec=SPEC, built_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), builder="scripts/build_fut_settle_strip.py",
                source="GLBX.MDP3 statistics schema, stat_type 3 (settlement), windowed ids (D520/D521)",
                session_label="ts_ref + 1 day in US/Eastern, as D526's strip", rows=int(len(D)), rows_raw=n_raw,
                dropped_exact_zero=n_zero, dropped_exact_zero_by_root=zero_by_root, dropped_weekend_refs=weekend,
                dropped_negative_non_CL=dropped_neg, roots=list(ROOTS),
                per_root={r: dict(rows=int(len(g)), sessions=int(g["ref"].nunique()), contracts=int(g["contract"].nunique()),
                                  first=str(g["ref"].min()), last=str(g["ref"].max()), settle_min=float(g["settle"].min()),
                                  settle_max=float(g["settle"].max())) for r, g in D.groupby("root")},
                files=[{k: v for k, v in r.items() if k != "table"} for r in res], workers=workers, wall_min=round(wall / 60, 2),
                speed_ratio=round(sec / wall, 2), probe_rss_mb=probe["rss_mb"], sha256=sha256(STRIP), gates=None)
    STRIP_META.write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"\nwrote {STRIP.relative_to(REPO)} ({len(D):,} rows; {n_zero} exact zeros dropped) in {wall / 60:.1f} min; gates not yet run")


# ------------------------------------------------------------------ derive (uv python)
def ym(contract: str, session: str):
    """(year, month) of a contract code resolved against the session (D526's rule): a one-digit year is
    the nearest delivery not more than one month behind the session; two digits are explicit."""
    m = RE_C.match(contract)
    if not m:
        return None
    mon = MONTH[m.group(2)]
    y = m.group(3)
    sy, sm = int(session[:4]), int(session[5:7])
    if len(y) == 2:
        return (2000 + int(y), mon)
    for cand in range(sy - 1, sy + 12):
        if cand % 10 == int(y) and (cand * 12 + mon) >= (sy * 12 + sm) - 1:
            return (cand, mon)
    return None


def breadth_sessions():
    cols = ["root", "day", "contract"] + [s + "_c" for s in SEGS]
    b = pd.read_csv(BREADTH, usecols=cols, encoding="utf-8")
    C = b[[s + "_c" for s in SEGS]].to_numpy(dtype=float)
    fin = np.isfinite(C)
    has = fin.any(1)
    last = C.shape[1] - 1 - np.argmax(fin[:, ::-1], axis=1)
    b = b[["root", "day", "contract"]].copy()
    b["close"] = np.where(has, C[np.arange(len(C)), np.clip(last, 0, None)], np.nan)
    b = b[b["close"].notna()]
    b = b[pd.to_datetime(b["day"]).dt.dayofweek < 5]           # the 69 weekend stubs (D555)
    return b.rename(columns={"day": "ref", "contract": "front"}).reset_index(drop=True)


def derive(strip: pd.DataFrame, sessions: pd.DataFrame) -> pd.DataFrame:
    """Per (root, session): the breadth front, its settlement, the nearest later delivery month with a
    settlement that session, and the annualised carry. Pure function of its two inputs."""
    strip = strip.copy()
    strip["ym"] = [ym(c, s) for c, s in zip(strip["contract"], strip["ref"])]
    strip = strip[strip["ym"].notna()].copy()
    strip["ymi"] = [y * 12 + m for y, m in strip["ym"]]
    by = {k: g for k, g in strip.groupby(["root", "ref"], sort=False)}
    rows = []
    for r, ref, front, close in sessions[["root", "ref", "front", "close"]].itertuples(index=False):
        g = by.get((r, ref))
        # `root_settles`: the root published at least one settlement for this session. False marks
        # an exchange holiday under the ROOT's calendar (the breadth fixture carries the holiday's
        # abbreviated Globex session; CME books it into the next trade date and settles nothing).
        # NYMEX/COMEX settle on days CME equity, FX and rates do not, so the flag is per root.
        settles = g is not None and len(g) > 0
        f_settle = np.nan; nxt = None; n_settle = np.nan; months = np.nan
        if g is not None:
            gf = g[g["contract"] == front]
            if len(gf):
                f_settle = float(gf["settle"].iloc[0])
                f_ymi = int(gf["ymi"].iloc[0])
                later = g[g["ymi"] > f_ymi].sort_values("ymi")
                if len(later):
                    nxt = str(later["contract"].iloc[0]); n_settle = float(later["settle"].iloc[0])
                    months = int(later["ymi"].iloc[0] - f_ymi)
        carry = (f_settle - n_settle) / n_settle * 12.0 / months if (np.isfinite(f_settle) and np.isfinite(n_settle) and n_settle != 0 and months) else np.nan
        rows.append((r, ref, front, f_settle, nxt, n_settle, months, carry, close, settles))
    return pd.DataFrame(rows, columns=["root", "ref", "front", "front_settle", "next", "next_settle", "months_between", "carry_ann", "breadth_close", "root_settles"])


def cmd_derive():
    t0 = time.time()
    strip = pd.read_csv(STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    ses = breadth_sessions()
    T = derive(strip, ses)
    T.to_csv(CURVE, index=False, compression="gzip", encoding="utf-8")
    meta = dict(spec=SPEC, built_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), builder="scripts/build_fut_settle_strip.py --derive",
                inputs=dict(strip=str(STRIP.relative_to(REPO)), strip_sha256=sha256(STRIP), breadth=str(BREADTH.relative_to(REPO)), breadth_sha256=sha256(BREADTH)),
                carry="(front_settle - next_settle) / next_settle * 12 / months_between; positive in backwardation",
                front="the breadth fixture's front-by-volume election", next="nearest later delivery month with a settlement that session",
                rows=int(len(T)), sha256=sha256(CURVE), gates=None)
    CURVE_META.write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"wrote {CURVE.relative_to(REPO)} ({len(T):,} rows) in {time.time() - t0:.0f}s; front settle present {T['front_settle'].notna().mean():.3f}, next {T['next_settle'].notna().mean():.3f}")


# ------------------------------------------------------------------ gates
def cmd_gates(log=print):
    strip = pd.read_csv(STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    T = pd.read_csv(CURVE, dtype={"root": str, "ref": str, "front": str, "next": str}, encoding="utf-8")
    g = {}
    # G1 -- exact agreement with D526's CL/GC strip on its window
    d526 = pd.read_csv(D526_STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    lo, hi = d526["ref"].min(), d526["ref"].max()
    mine = strip[strip["root"].isin(["CL", "GC"]) & (strip["ref"] >= lo) & (strip["ref"] <= hi)]
    a = d526.sort_values(["root", "ref", "contract"]).reset_index(drop=True)
    b = mine.sort_values(["root", "ref", "contract"]).reset_index(drop=True)
    same_rows = len(a) == len(b) and a[["root", "ref", "contract"]].equals(b[["root", "ref", "contract"]])
    same_px = same_rows and np.array_equal(a["settle"].to_numpy(), b["settle"].to_numpy())
    g["G1"] = dict(d526_rows=int(len(a)), mine_rows=int(len(b)), same_rows=bool(same_rows), same_settlements=bool(same_px), window=[lo, hi])
    log(f"[G1] D526 strip {len(a):,} rows vs mine {len(b):,}: rows {'equal' if same_rows else 'DIFFER'}, settlements {'identical' if same_px else 'DIFFER'}")
    if not same_px:
        raise AssertionError("G1: the extraction does not reproduce D526's strip")
    # G2 -- coverage from each root's live start (scored years only), AMONG the sessions on which the
    # root published any settlement; the sessions on which it published none are its exchange
    # holidays (breadth carries the abbreviated Globex session; CME settles nothing), counted beside
    T["year"] = T["ref"].str[:4].astype(int)
    T["root_settles"] = T["root_settles"].astype(str).str.lower().isin(["true", "1"])
    cov = {}
    for r, t in T.groupby("root"):
        t = t[(t["year"] >= LIVE_START[r]) & (t["ref"] <= "2023-12-29")]
        s = t[t["root_settles"]]
        cov[r] = dict(sessions=int(len(t)), no_settlement_sessions=int((~t["root_settles"]).sum()),
                      no_settlement_per_year=round(float((~t["root_settles"]).sum() / max(t["year"].nunique(), 1)), 1),
                      front=float(s["front_settle"].notna().mean()), next=float(s["next_settle"].notna().mean()))
    g["G2"] = cov
    bad = {r: v for r, v in cov.items() if v["front"] < G2_FRONT or v["next"] < G2_NEXT}
    log(f"[G2] coverage among settling sessions: min front {min(v['front'] for v in cov.values()):.4f}, min next "
        f"{min(v['next'] for v in cov.values()):.4f}; no-settlement sessions a year: "
        f"{ {r: v['no_settlement_per_year'] for r, v in cov.items()} }; below bar: {list(bad)}")
    if bad:
        raise AssertionError(f"G2: coverage below bar on {sorted(bad)}")
    # G3 -- front settlement against the breadth session close
    g3 = {}
    for r, t in T.groupby("root"):
        t = t[(t["year"] >= LIVE_START[r]) & (t["ref"] <= "2023-12-29")]
        ok = t["front_settle"].notna() & t["breadth_close"].notna() & (t["front_settle"] > 0) & (t["breadth_close"] > 0)
        d = np.abs(np.log(t.loc[ok, "front_settle"] / t.loc[ok, "breadth_close"]))
        g3[r] = dict(n=int(ok.sum()), median=float(d.median()), p99=float(d.quantile(0.99)))
    g["G3"] = g3
    worst = max(g3.items(), key=lambda kv: kv[1]["median"])
    log(f"[G3] |log(settle/close)| median: worst {worst[0]} {worst[1]['median']:.4%}; roots over {G3_MEDIAN_MAX:.1%}: {[r for r, v in g3.items() if v['median'] > G3_MEDIAN_MAX]}")
    if worst[1]["median"] > G3_RAISE:
        raise AssertionError(f"G3: {worst[0]} settlement is {worst[1]['median']:.2%} from the session close -- a labelling error")
    # G4 -- months, zeros, weekends, negatives
    mb = T["months_between"].dropna()
    wk = pd.to_datetime(strip["ref"]).dt.dayofweek >= 5
    neg = strip[strip["settle"] < 0]
    g["G4"] = dict(months_min=int(mb.min()), months_max=int(mb.max()), exact_zeros=int((strip["settle"] == 0).sum()),
                   weekend_rows=int(wk.sum()), negatives=neg.groupby("root")["ref"].agg(["min", "max", "size"]).to_dict("index") if len(neg) else {})
    log(f"[G4] months_between {int(mb.min())}..{int(mb.max())}; exact zeros {g['G4']['exact_zeros']}; weekend rows {int(wk.sum())}; negatives {g['G4']['negatives']}")
    if not (1 <= mb.min() and mb.max() <= 12) or g["G4"]["exact_zeros"] or wk.any():
        raise AssertionError("G4 failed")
    if len(neg) and not (set(neg["root"]) == {"CL"} and neg["ref"].min() >= "2020-04-17" and neg["ref"].max() <= "2020-04-22"):
        raise AssertionError(f"G4: unexpected negative settlements {g['G4']['negatives']}")
    for path in (STRIP_META, CURVE_META):
        m = json.loads(path.read_text(encoding="utf-8")); m["gates"] = g; m["all_gates_pass"] = True
        path.write_text(json.dumps(m, indent=1), encoding="utf-8")
    log("ALL GATES PASS; written to both meta files")


# ------------------------------------------------------------------ self-test
def cmd_selftest():
    print("D556 fixture SELF-TEST -- synthetic strip, no archive read")
    # D526's rule keeps a just-expired month for ONE month past the session (its final settlement can
    # still print), so CLZ5 quoted in January 2016 is still December 2015; in February it is 2025.
    assert ym("CLZ5", "2015-11-02") == (2015, 12) and ym("CLZ5", "2016-01-04") == (2015, 12)
    assert ym("CLZ5", "2016-02-01") == (2025, 12) and ym("CLZ25", "2016-01-04") == (2025, 12)
    assert ym("ESH0", "2019-12-20") == (2020, 3) and ym("6EH1", "2011-03-15") == (2011, 3)
    print("  [1] month-code resolution: one-digit years resolve to the nearest delivery not more than one month behind, two-digit years are explicit")
    strip = pd.DataFrame([("CL", "CLF6", "2015-12-01", 40.0), ("CL", "CLG6", "2015-12-01", 41.0), ("CL", "CLH6", "2015-12-01", 42.0),
                          ("CL", "CLG6", "2015-12-02", 41.5), ("CL", "CLJ6", "2015-12-02", 43.0),
                          ("GC", "GCG6", "2015-12-01", 1060.0), ("GC", "GCJ6", "2015-12-01", 1062.0)],
                         columns=["root", "contract", "ref", "settle"])
    ses = pd.DataFrame([("CL", "2015-12-01", "CLF6", 40.1), ("CL", "2015-12-02", "CLG6", 41.4), ("GC", "2015-12-01", "GCG6", 1061.0), ("GC", "2015-12-02", "GCG6", 1063.0)],
                       columns=["root", "ref", "front", "close"])
    T = derive(strip, ses)
    r0 = T.iloc[0]; assert r0["next"] == "CLG6" and r0["months_between"] == 1 and abs(r0["carry_ann"] - (40.0 - 41.0) / 41.0 * 12) < 1e-12
    r1 = T.iloc[1]; assert r1["next"] == "CLJ6" and r1["months_between"] == 2 and abs(r1["carry_ann"] - (41.5 - 43.0) / 43.0 * 6) < 1e-12
    r2 = T.iloc[2]; assert r2["next"] == "GCJ6" and r2["months_between"] == 2 and r2["carry_ann"] < 0
    r3 = T.iloc[3]; assert np.isnan(r3["front_settle"]) and np.isnan(r3["carry_ann"]) and not r3["root_settles"] and r0["root_settles"]
    print("  [2] derive: next is the nearest LATER month, months_between counts delivery months, contango reads negative, a session with no settlement is NaN and flagged")
    print("  ALL SELF-TESTS PASSED")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true"); ap.add_argument("--extract", action="store_true")
    ap.add_argument("--derive", action="store_true"); ap.add_argument("--gates", action="store_true")
    ap.add_argument("--selftest", action="store_true"); ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.probe:
        cmd_probe()
    elif a.extract:
        cmd_extract(a.workers)
    elif a.derive:
        cmd_derive()
    elif a.gates:
        cmd_gates()
    elif a.selftest:
        cmd_selftest()
