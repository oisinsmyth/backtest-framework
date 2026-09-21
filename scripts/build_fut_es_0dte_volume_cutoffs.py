"""The ES-family option volume panel in ET CLOCK BUCKETS, so a conditioner can be fixed at any
cutoff instead of only at 15:30.

    python scripts/build_fut_es_0dte_volume_cutoffs.py --selftest          # every gate raises on its break
    python scripts/build_fut_es_0dte_volume_cutoffs.py --bars [--workers 6]  # decode, cached per file
    python scripts/build_fut_es_0dte_volume_cutoffs.py --build             # the fixture + meta + gates

SYSTEM PYTHON, not the venv: `databento` is installed only there.

WHY THIS FIXTURE EXISTS
-----------------------
`data/fixtures/fut_es_options_eod.csv.gz` (D581) carries `vol_to_1530`, the traded contracts
before 15:30 ET on an option's own expiry session. That single cutoff is 15:30, which is also the
moment a close-window study conditions at, so the conditioner accumulates right up to the window
it predicts and cannot be separated from the move it chased. An adversarial review of the pin
design measured the consequence: the 15:30 centroid carries a correlation of -0.45 with the
09:30 -> 15:30 return, 23 % of its variance is the day's move, and the sign of the pull
coefficient flips with the control set. A cutoff fixed EARLIER is the identification this study
needs, and the raw minute bars already on disk carry it.

So this panel emits volume per (session, option) in five ET clock buckets. Any cutoff is then a
sum of buckets, the 15:30 cutoff reproduces D581's committed column exactly (gate G4), and the
volume inside the scored window is kept separately so it can never be used as a conditioner by
accident.

THE ET CALENDAR-DATE CONVENTION, STATED BECAUSE IT IS NOT THE TRADING SESSION
----------------------------------------------------------------------------
`session` is the ET CALENDAR DATE of the bar's start, which is what D581's builder used. The CME
trading session for date D actually opens at 18:00 on D-1, so the 18:00-24:00 Globex hours that
belong to session D are filed here under date D-1. That is why `v_1800_2400` is a separate bucket
and not folded into anything: a study wanting the true session-aligned accumulation adds the prior
date's `v_1800_2400`, and a study wanting D581's convention does not. Neither is silently chosen.

RESERVED SLICE, ENFORCED AT THE FILE LEVEL
------------------------------------------
Nothing from 2024-01-01 on may be read. That is enforced by never OPENING a source file whose span
reaches 2024, not by filtering rows afterwards, and the excluded filenames are recorded in the
meta. Files ending before 2016-01-01 are skipped too: they are outside the ES day session's usable
span (`fut_index_1m.meta.json` gate G5) and decoding them would cost 15 % more for nothing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"
FIX = REPO / "data" / "fixtures"
TEMP = REPO / "temp" / "es_0dte_cutoffs"
OUT = FIX / "fut_es_0dte_volume_cutoffs.csv.gz"
META = FIX / "fut_es_0dte_volume_cutoffs.meta.json"
D581_FIXTURE = FIX / "fut_es_options_eod.csv.gz"

SPEC = "D613"
OPTION = re.compile(r"^(ES|EW|EW[1-4]|E[1-5][A-D])([FGHJKMNQUVXZ])(\d{1,2}) ([CP])(\d+)$")   # D581's, verbatim
SPAN = re.compile(r"glbx-mdp3-(\d{8})-(\d{8})\.ohlcv-1m\.dbn\.zst$")
CHUNK = 5_000_000
IN_FROM, IN_TO = "2016-01-04", "2023-12-29"
RESERVED_FROM = "2024-01-01"
FIRST_USEFUL, LAST_USEFUL = "20160101", "20231231"
EDGES = ("00:00", "12:00", "15:30", "16:00", "18:00", "24:00")
BUCKETS = ("v_0000_1200", "v_1200_1530", "v_1530_1600", "v_1600_1800", "v_1800_2400")
KEYS = ["raw_symbol", "session"]


def log(*a):
    print(*a, flush=True)


def expect_raise(fn, what, say=log):
    try:
        fn()
    except AssertionError as e:
        say(f"    gate RAISES on {what}: {str(e)[:70]}")
        return True
    raise AssertionError(f"gate did not raise on {what}")


# ------------------------------------------------------------------ which files may be opened
def source_files():
    """Every ohlcv-1m file whose span overlaps [2016-01-01, 2023-12-31]; the rest NAMED, not silently dropped."""
    keep, skip_reserved, skip_early, unparsed = [], [], [], []
    for p in sorted(RAW.glob("*/*.ohlcv-1m.dbn.zst"), key=lambda q: q.name):
        m = SPAN.search(p.name)
        if not m:
            unparsed.append(p.name)
            continue
        lo, hi = m.group(1), m.group(2)
        if hi >= "20240101":
            skip_reserved.append(p.name)
        elif hi < FIRST_USEFUL:
            skip_early.append(p.name)
        else:
            keep.append(p)
    if unparsed:
        raise AssertionError(f"a source filename does not carry a parseable span: {unparsed}")
    if not keep:
        raise AssertionError("no source file overlaps the in-sample span")
    return keep, skip_reserved, skip_early


def audit_no_reserved_file(names):
    """RAISES if any file about to be opened reaches 2024. The reserved rule, enforced before the read."""
    bad = [n for n in names if (SPAN.search(n) and SPAN.search(n).group(2) >= "20240101")]
    if bad:
        raise AssertionError(f"a source file reaching the reserved slice would be opened: {bad}")


# ------------------------------------------------------------------ the decode
def bars_worker(path):
    """One file -> (raw_symbol, session) x five ET clock buckets. D581's mapping-window logic, verbatim."""
    import databento as db
    t0 = time.time()
    store = db.DBNStore.from_file(path)
    rows = []
    for sym, ivs in store.metadata.mappings.items():
        if OPTION.match(str(sym)):
            for iv in (ivs if isinstance(ivs, list) else [ivs]):
                sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
                s = iv["start_date"] if isinstance(iv, dict) else getattr(iv, "start_date")
                e = iv["end_date"] if isinstance(iv, dict) else getattr(iv, "end_date")
                if sid:
                    rows.append((int(sid), str(sym), np.uint64(pd.Timestamp(s, tz="UTC").value),
                                 np.uint64(pd.Timestamp(e, tz="UTC").value)))
    if not rows:
        return dict(file=Path(path).name, rows_in=0, rows_kept=0, secs=round(time.time() - t0, 1), table=None)
    w = pd.DataFrame(rows, columns=["iid", "raw_symbol", "w0", "w1"])
    keys = np.unique(w["iid"].to_numpy(np.uint32))
    parts, n = [], 0
    for arr in store.to_ndarray(count=CHUNK):
        n += len(arr)
        a = arr[np.isin(arr["instrument_id"], keys)]
        if not a.size:
            continue
        raw = pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32),
                            "ts": a["ts_event"].astype(np.uint64), "_i": np.arange(len(a))})
        j = raw.merge(w, on="iid", how="inner")
        j = j[(j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])]
        if j["_i"].duplicated().any():
            raise AssertionError("[IDS] an option bar claimed by two mapping windows")
        k = j["_i"].to_numpy()
        ts = pd.to_datetime(a["ts_event"][k], utc=True).tz_convert("US/Eastern")
        day = np.asarray(ts.strftime("%Y-%m-%d"))
        hhmm = np.asarray(ts.strftime("%H:%M"))
        vol = a["volume"][k].astype(np.int64)
        d = {"raw_symbol": j["raw_symbol"].to_numpy(), "session": day}
        for name, lo, hi in zip(BUCKETS, EDGES[:-1], EDGES[1:]):
            d[name] = np.where((hhmm >= lo) & (hhmm < hi), vol, 0)
        parts.append(pd.DataFrame(d))
    t = (pd.concat(parts, ignore_index=True).groupby(KEYS, sort=False)[list(BUCKETS)].sum().reset_index()
         if parts else None)
    return dict(file=Path(path).name, rows_in=n, rows_kept=int(len(t)) if t is not None else 0,
                secs=round(time.time() - t0, 1), table=t)


def cmd_bars(workers):
    files, skip_res, skip_early = source_files()
    names = [f.name for f in files]
    audit_no_reserved_file(names)
    log(f"  opening {len(files)} files ({sum(f.stat().st_size for f in files)/1e6:.0f} MB); "
        f"{len(skip_res)} excluded as reserved, {len(skip_early)} as pre-{FIRST_USEFUL}")
    TEMP.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    from multiprocessing import Pool
    with Pool(workers) as pool:
        res = pool.map(bars_worker, [str(f) for f in sorted(files, key=lambda p: -p.stat().st_size)], chunksize=1)
    res.sort(key=lambda r: r["file"])
    tabs = [r["table"] for r in res if r["table"] is not None]
    t = pd.concat(tabs, ignore_index=True).groupby(KEYS, sort=False)[list(BUCKETS)].sum().reset_index()
    (TEMP / "buckets.pkl").write_bytes(pickle.dumps({"table": t, "files": names,
                                                     "excluded_reserved": skip_res, "excluded_early": skip_early}))
    sec = sum(r["secs"] for r in res)
    wall = time.time() - t0
    for r in res:
        log(f"  {r['file'][:44]:<44} {r['rows_in']:>12,} rows -> {r['rows_kept']:>9,} option-days  {r['secs']:>6.1f}s")
    log(f"[SPEED] sum(item time)/wall = {sec/wall:.2f}x on {workers} workers ({100*sec/wall/workers:.0f}%); "
        f"{len(t):,} (option, session) rows; {wall/60:.1f} min")
    if sec / wall / workers < 0.70:
        log("[SPEED] below the 70 % floor -- say so in the record")
    return 0


# ------------------------------------------------------------------ the gates
def gate_g1(t):
    """Rows, span, and the bucket columns present and non-negative."""
    if t.empty:
        raise AssertionError("G1: the panel is empty")
    miss = [c for c in BUCKETS if c not in t.columns]
    if miss:
        raise AssertionError(f"G1: bucket columns missing: {miss}")
    if (t[list(BUCKETS)].to_numpy() < 0).any():
        raise AssertionError("G1: a negative volume")
    return {"rows": int(len(t)), "sessions": int(t["session"].nunique()),
            "options": int(t["raw_symbol"].nunique()),
            "span": [str(t["session"].min()), str(t["session"].max())]}


def gate_g2(t):
    """One row per (option, session)."""
    d = int(t.duplicated(KEYS).sum())
    if d:
        raise AssertionError(f"G2: {d} duplicate (option, session) keys")
    return {"duplicate_keys": 0}


def gate_g3(t):
    """The cutoffs are monotone by construction: v(12:00) <= v(15:30) <= v(16:00)."""
    c12 = t["v_0000_1200"].to_numpy()
    c1530 = c12 + t["v_1200_1530"].to_numpy()
    c1600 = c1530 + t["v_1530_1600"].to_numpy()
    bad = int(((c12 > c1530) | (c1530 > c1600)).sum())
    if bad:
        raise AssertionError(f"G3: {bad} rows where a later cutoff holds less volume")
    return {"rows_checked": int(len(t)), "violations": 0,
            "share_of_pre1530_in_by_noon": float(c12.sum() / max(c1530.sum(), 1))}


def gate_g4(t):
    """THE REPRODUCTION GATE: v(15:30) equals D581's committed `vol_to_1530` on every row it covers."""
    d = pd.read_csv(D581_FIXTURE, usecols=["session", "raw_symbol", "expiry_date", "vol_to_1530"],
                    dtype={"session": str, "raw_symbol": str, "expiry_date": str}, encoding="utf-8")
    d = d[(d["session"] >= IN_FROM) & (d["session"] <= IN_TO) & d["vol_to_1530"].notna()]
    if d.empty:
        raise AssertionError("G4: nothing to compare against in the committed fixture")
    m = d.merge(t.assign(v1530=t["v_0000_1200"] + t["v_1200_1530"])[KEYS + ["v1530"]], on=KEYS, how="left")
    covered = m["v1530"].notna()
    diff = (m.loc[covered, "v1530"].to_numpy() - m.loc[covered, "vol_to_1530"].to_numpy())
    nbad = int((diff != 0).sum())
    if nbad:
        worst = m.loc[covered].assign(d=diff).reindex((diff != 0).nonzero()[0]).head(3)
        raise AssertionError(f"G4: {nbad} rows disagree with the committed vol_to_1530, e.g. {worst.to_dict('records')}")
    # a row this panel does not carry means the option never traded, so the committed column must be ZERO there.
    # Without this clause the gate would pass on a panel that had silently dropped every traded option.
    missed = m.loc[~covered, "vol_to_1530"].to_numpy()
    nz = int((missed > 0).sum())
    if nz:
        raise AssertionError(f"G4: {nz} committed rows with POSITIVE volume are absent from the panel")
    return {"committed_rows_in_span": int(len(d)), "rows_covered": int(covered.sum()),
            "coverage": float(covered.mean()), "rows_disagreeing": 0,
            "rows_absent_all_zero": int((~covered).sum()), "absent_with_positive_volume": 0,
            "note": "the panel holds a row only where an option traded; the committed column zero-fills every "
                    "0DTE row, so absence must mean zero and is asserted to"}


def gate_g5(t, path, sessions):
    """Second path on NAMED sessions: a scalar Python loop over only those sessions' bars.

    Deliberately not the vectorised route -- no `np.isin` over ids, no merge, no `strftime` on an
    array, one bar at a time. Bounded to the named sessions by a UTC nanosecond window computed from
    them, because a scalar loop over a whole year's 50 M bars would cost an hour and a gate nobody
    runs is not a gate.
    """
    import databento as db
    lo = int(pd.Timestamp(min(sessions) + " 00:00", tz="US/Eastern").tz_convert("UTC").value)
    hi = int(pd.Timestamp(max(sessions) + " 23:59", tz="US/Eastern").tz_convert("UTC").value)
    store = db.DBNStore.from_file(path)
    wmap = {}
    for sym, ivs in store.metadata.mappings.items():
        if OPTION.match(str(sym)):
            for iv in (ivs if isinstance(ivs, list) else [ivs]):
                sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
                s = iv["start_date"] if isinstance(iv, dict) else getattr(iv, "start_date")
                e = iv["end_date"] if isinstance(iv, dict) else getattr(iv, "end_date")
                if sid:
                    wmap.setdefault(int(sid), []).append((pd.Timestamp(s, tz="UTC").value,
                                                          pd.Timestamp(e, tz="UTC").value, str(sym)))
    want = set(sessions)
    tot, seen = {}, 0
    for arr in store.to_ndarray(count=CHUNK):
        ts_all = arr["ts_event"].astype(np.int64)
        sel = np.flatnonzero((ts_all >= lo) & (ts_all <= hi))
        for i in sel:
            iid = int(arr["instrument_id"][i])
            if iid not in wmap:
                continue
            ts = int(ts_all[i])
            for w0, w1, sym in wmap[iid]:
                if w0 <= ts < w1:
                    e = pd.Timestamp(ts, unit="ns", tz="UTC").tz_convert("US/Eastern")
                    day = e.strftime("%Y-%m-%d")
                    if day in want:
                        seen += 1
                        if e.strftime("%H:%M") < "12:00":
                            tot[day] = tot.get(day, 0) + int(arr["volume"][i])
                    break
    if not seen:
        raise AssertionError(f"G5: the scalar loop found no option bars on {sessions}")
    mine = t[t["session"].isin(sessions)].groupby("session")["v_0000_1200"].sum()
    for d in sessions:
        a, b = int(mine.get(d, 0)), int(tot.get(d, 0))
        if a != b:
            raise AssertionError(f"G5: {d} pre-noon volume {a} by the panel vs {b} by the scalar loop")
    return {"file": Path(path).name, "sessions_checked": list(sessions), "option_bars_walked": int(seen),
            "pre_noon_volume": {d: int(tot.get(d, 0)) for d in sessions}}


def gate_g6(t, files, excluded):
    """No session at or after the reserved date, and no file reaching it was opened."""
    late = t[t["session"] >= RESERVED_FROM]
    if len(late):
        raise AssertionError(f"G6: {len(late)} rows at or after {RESERVED_FROM}, e.g. {late['session'].iloc[0]}")
    audit_no_reserved_file(files)
    return {"files_opened": len(files), "files_excluded_as_reserved": excluded,
            "max_session": str(t["session"].max())}


def cmd_build():
    blob = pickle.loads((TEMP / "buckets.pkl").read_bytes())
    t = blob["table"]
    t = t[(t["session"] >= IN_FROM) & (t["session"] <= IN_TO)].sort_values(KEYS, kind="stable").reset_index(drop=True)
    gates = {}
    gates["G1"] = gate_g1(t)
    expect_raise(lambda: gate_g1(t.assign(v_0000_1200=-1)), "a negative volume")
    gates["G2"] = gate_g2(t)
    expect_raise(lambda: gate_g2(pd.concat([t.head(1), t], ignore_index=True)), "a duplicated key")
    gates["G3"] = gate_g3(t)
    expect_raise(lambda: gate_g3(t.assign(v_1200_1530=-t["v_0000_1200"] - 1)), "a later cutoff holding less")
    gates["G4"] = gate_g4(t)
    expect_raise(lambda: gate_g4(t.assign(v_0000_1200=t["v_0000_1200"] + 1)), "the noon bucket shifted by one contract")
    traded = t[(t["v_0000_1200"] + t["v_1200_1530"]) > 0]
    expect_raise(lambda: gate_g4(t.drop(index=traded.index[:2000])), "2,000 traded rows dropped from the panel")
    small = min(source_files()[0], key=lambda q: q.stat().st_size)
    lo, hi = SPAN.search(small.name).group(1), SPAN.search(small.name).group(2)
    # only sessions that actually carry pre-noon volume: a session with zero on both paths agrees
    # trivially, and a gate that cannot disagree is not a gate
    inf = t[(t["session"] >= f"{lo[:4]}-{lo[4:6]}-{lo[6:]}") & (t["session"] <= f"{hi[:4]}-{hi[4:6]}-{hi[6:]}")]
    vol = inf.groupby("session")["v_0000_1200"].sum()
    live = sorted(vol[vol > 0].index)
    if len(live) < 3:
        raise AssertionError("G5: the chosen file covers fewer than three sessions with pre-noon volume")
    picked = [live[len(live) // 2], live[len(live) // 2 + 1], live[-1]]
    if min(int(vol[p]) for p in picked) <= 0:
        raise AssertionError(f"G5: a picked session carries no pre-noon volume: {[(p, int(vol[p])) for p in picked]}")
    gates["G5"] = gate_g5(t, str(small), picked)
    expect_raise(lambda: gate_g5(t.assign(v_0000_1200=t["v_0000_1200"] + 1), str(small), picked),
                 "the noon bucket shifted by one contract per row")
    gates["G6"] = gate_g6(t, blob["files"], blob["excluded_reserved"])
    expect_raise(lambda: gate_g6(t.assign(session=RESERVED_FROM), blob["files"], blob["excluded_reserved"]),
                 "a session in the reserved slice")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # one declared text site, and mtime pinned to 0 so two identical builds hash identically (D550)
    t.to_csv(OUT, index=False, encoding="utf-8", lineterminator="\n",
             compression={"method": "gzip", "mtime": 0})
    sha = hashlib.sha256(OUT.read_bytes()).hexdigest()
    meta = {"spec": SPEC, "built_utc": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": "data/raw/databento ohlcv-1m, the ES option families of D581's OPTION regex",
            "session": "the ET CALENDAR DATE of the bar's start (D581's convention); the 18:00-24:00 hours "
                       "belonging to the NEXT trading session are filed under this date and kept in their own bucket",
            "buckets_et": {b: [lo, hi] for b, lo, hi in zip(BUCKETS, EDGES[:-1], EDGES[1:])},
            "cutoffs": {"v_to_1200": "v_0000_1200",
                        "v_to_1530": "v_0000_1200 + v_1200_1530  (equals D581's vol_to_1530, gate G4)",
                        "inside_the_scored_window": "v_1530_1600 -- never a conditioner for a 15:30->16:00 study"},
            "coverage": "EVERY expiry, not only same-day: a row exists for any (option, session) that traded. "
                        "D581's vol_to_1530 is populated only where expiry_date == session, so this panel makes the "
                        "horizon-matched control (a volume-weighted centroid of LATER expiries) buildable, which on "
                        "the committed fixture alone it is not.",
            "span": [IN_FROM, IN_TO], "reserved_from": RESERVED_FROM,
            "rows": int(len(t)), "sha256": sha, "gates": gates, "all_gates_pass": True}
    META.write_text(json.dumps(meta, indent=1), encoding="utf-8")
    log(f"  wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e6:.1f} MB, {len(t):,} rows) and its meta")
    log(f"  G3 share of pre-15:30 volume already in by noon: {gates['G3']['share_of_pre1530_in_by_noon']:.3f}")
    log(f"  G4 reproduced D581's vol_to_1530 on {gates['G4']['rows_covered']:,} rows "
        f"({gates['G4']['coverage']:.3f} of the committed rows in span), 0 disagreeing")
    return 0


def selftest():
    log("  selftest: the gates on a synthetic panel")
    t = pd.DataFrame({"raw_symbol": ["ESZ8 C2700", "ESZ8 P2700", "EW1F9 C2500"],
                      "session": ["2018-12-03", "2018-12-03", "2019-01-02"],
                      "v_0000_1200": [10, 0, 5], "v_1200_1530": [7, 3, 0],
                      "v_1530_1600": [2, 1, 0], "v_1600_1800": [0, 0, 1], "v_1800_2400": [1, 0, 0]})
    log(f"  G1 {gate_g1(t)}")
    expect_raise(lambda: gate_g1(t.assign(v_0000_1200=-1)), "a negative volume")
    expect_raise(lambda: gate_g1(t.drop(columns=["v_1200_1530"])), "a missing bucket column")
    log(f"  G2 {gate_g2(t)}")
    expect_raise(lambda: gate_g2(pd.concat([t.head(1), t], ignore_index=True)), "a duplicated key")
    log(f"  G3 {gate_g3(t)}")
    expect_raise(lambda: gate_g3(t.assign(v_1200_1530=[-11, -1, -6])), "a later cutoff holding less")
    expect_raise(lambda: gate_g6(t.assign(session=RESERVED_FROM), [], []), "a session in the reserved slice")
    expect_raise(lambda: audit_no_reserved_file(["glbx-mdp3-20240101-20240828.ohlcv-1m.dbn.zst"]),
                 "a source file reaching 2024")
    files, res, early = source_files()
    audit_no_reserved_file([f.name for f in files])
    log(f"  file selection: {len(files)} to open, {len(res)} reserved, {len(early)} pre-{FIRST_USEFUL}")
    if any(SPAN.search(f.name).group(2) >= "20240101" for f in files):
        raise AssertionError("a reserved file survived selection")
    log("  selftest: every gate passes its clean case and raises on its break")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--bars", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else cmd_bars(a.workers) if a.bars else cmd_build() if a.build else 1)
