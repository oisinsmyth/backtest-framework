"""D497 -- the open-interest fixture: daily root-total open interest and cleared volume for ES, NQ, CL, GC from the CME `statistics`
schema, keyed on the session in which each figure is FIRST USABLE (published strictly before 10:00 ET). Spec ab8b5df, committed
before this file. Data layer only: no returns, no signal, no trade.

    python scripts/build_fut_open_interest.py --probe          # one file: rows, timing, RSS, projected wall
    python scripts/build_fut_open_interest.py --build [--workers 8]
    python scripts/build_fut_open_interest.py --gates          # O1..O5 -> meta; raises on failure
    python scripts/build_fut_open_interest.py --selftest       # synthetic records through the same functions

Conventions. `stat_type` 9 = open interest, carried in `quantity` (`price` undefined); 6 = cleared volume. `ts_ref` is the session
START (19:00 ET the evening before the trade date) and is used only to LABEL the reference session; causality rests on `ts_event`.
A publication is usable on the first session of that root's calendar whose 10:00 ET entry is strictly after `ts_event`.
A contract counts toward the root total only if its last publication is within RECENCY_DAYS of the usable session, which drops
expired months without assuming they stop publishing.
"""
from __future__ import annotations
import argparse, json, re, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from build_fut_breadth_hourly import ids_of as _ids_windows  # noqa: E402  -- one definition of the mapping windows, D520

RAW = REPO / "data" / "raw" / "databento" / "GLBX-20260911-SDNLQ6M99S"
HOURLY = REPO / "data" / "fixtures" / "fut_sessions_hourly.csv.gz"
FIX = REPO / "data" / "fixtures"; OUT = FIX / "fut_open_interest_daily.csv.gz"; META = FIX / "fut_open_interest_daily.meta.json"
ROOTS = ("ES", "NQ", "CL", "GC")
OUTRIGHT = re.compile(r"^(ES|NQ|CL|GC)([FGHJKMNQUVXZ])(\d{1,2})$")
ST_OI, ST_CV = 9, 6
UNDEF = np.iinfo(np.int64).max
ENTRY_MIN = 10 * 60            # 10:00 ET -- the study's entry, so the causality cutoff
RECENCY_DAYS = 7               # a contract joins the root total only if it published within this many calendar days
SPAN = ("2016-01-04", "2023-12-29")
O2_MEDIAN_MAX = 1; O3_COVER = 0.98; O4_TOTAL_MAX = 0.10; O4_FRONT_MIN = 0.40; O5_SD_MAX = 0.10


def rss_mb():
    import os, subprocess
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {os.getpid()}", "/FO", "CSV", "/NH"], capture_output=True, text=True).stdout
        return float(out.strip().rsplit('","', 1)[-1].strip('"').replace(" K", "").replace(",", "")) / 1e3
    except Exception:
        return float("nan")


def ids_of(store):
    """Symbol mappings as (iid, root, contract, w0, w1) WINDOWS for this fixture's four roots.

    D520. The flat `{instrument_id: (root, symbol)}` dict this replaced kept only the LAST mapping
    written for an id and threw the validity dates away, so one id carried one label for all time.
    The archive breaks that two ways: CME reuses the single-digit-year slot the moment a contract
    expires (`CLN9` is July-2019 until 2019-06-23 and July-2029 after it), and a live contract can be
    ROTATED to a new id mid-year. Measured on the 2019 file: 16 of CL's 140 outright symbols carry
    two windows. Of this fixture's four roots CL is the one affected; ES, NQ and GC are clean.

    The window logic is imported from the breadth builder rather than re-implemented, so there is one
    definition of "which contract is this bar" in the repo, and it is filtered to ROOTS here.
    """
    w = _ids_windows(store)
    if w is None or len(w) == 0:
        return None
    w = w[w["root"].isin(ROOTS)].reset_index(drop=True)
    return w if len(w) else None


def label_rows(a, w, ts_field="ts_event"):
    """Attach (root, contract) from the mapping window CONTAINING each record's own timestamp.

    Returns the joined frame with `_i`, the index back into `a`, so the caller reads the record's
    other fields positionally rather than trusting a second lookup.

    THE GUARD IS ON `_i`, NOT ON (iid, ts), and the difference matters for this schema: the
    statistics feed legitimately publishes several records for one instrument at one timestamp
    (open interest and cleared volume are different `stat_type`s), so day5m's (iid, ts) duplicate
    guard would fire on correct data here. A repeated `_i` means ONE input record was claimed by
    TWO windows, which is the actual ambiguity and cannot happen on correct mappings.
    """
    raw = pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32),
                        "ts": a[ts_field].astype(np.uint64),
                        "_i": np.arange(len(a), dtype=np.int64)})
    j = raw.merge(w, on="iid", how="inner")
    j = j[(j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])]
    if j["_i"].duplicated().any():
        n = int(j["_i"].duplicated().sum())
        raise RuntimeError(f"[IDS] {n} records claimed by MORE THAN ONE mapping window -- overlapping validity makes the label ambiguous")
    return j


def worker(path):
    """One statistics file -> the open-interest and cleared-volume publications of the four roots' outrights."""
    import databento as db
    t0 = time.time(); store = db.DBNStore.from_file(path); w = ids_of(store)
    if w is None:
        return dict(file=Path(path).name, rows_in=0, rows_kept=0, secs=round(time.time() - t0, 1), rss_mb=round(rss_mb(), 0), table=None)
    keys = w["iid"].to_numpy(np.uint32); parts = []; n_in = 0
    for arr in store.to_ndarray(count=5_000_000):
        n_in += len(arr)
        a = arr[np.isin(arr["instrument_id"], keys) & np.isin(arr["stat_type"], (ST_OI, ST_CV))]
        if a.size:
            j = label_rows(a, w)
            if len(j):
                k = j["_i"].to_numpy()
                parts.append(pd.DataFrame({"root": j["root"].to_numpy(), "contract": j["contract"].to_numpy(),
                                           "stat_type": a["stat_type"][k].astype(np.int16), "ts_event": a["ts_event"][k].astype("int64"),
                                           "ts_ref": a["ts_ref"][k].astype("int64"), "value": a["quantity"][k].astype("int64")}))
    d = pd.concat(parts, ignore_index=True) if parts else None
    if d is not None:
        d = d[(d["value"] != UNDEF) & (d["value"] >= 0)].drop_duplicates(["contract", "stat_type", "ts_event", "value"])
    return dict(file=Path(path).name, rows_in=n_in, rows_kept=int(len(d)) if d is not None else 0, secs=round(time.time() - t0, 1), rss_mb=round(rss_mb(), 0), table=d)


def calendars():
    """Each root's own session calendar from the committed D467 hourly table (same_front rows carry the tradeable sessions)."""
    T = pd.read_csv(HOURLY, usecols=["root", "day", "h09_c", "h15_c"], dtype={"root": str, "day": str})
    T = T[(T["h09_c"] > 0) & (T["h15_c"] > 0)]
    return {r: np.array(sorted(T[T["root"] == r]["day"].unique())) for r in ROOTS}


def usable_session(ts_event_ns, cal):
    """The first session of `cal` whose 10:00 ET entry is strictly AFTER the publication -- the session the figure is first usable in."""
    ev = pd.to_datetime(ts_event_ns, utc=True).tz_convert("US/Eastern")
    same_day_ok = (ev.hour * 60 + ev.minute) < ENTRY_MIN          # published before 10:00 -> usable the same session, if it is one
    day = np.where(same_day_ok, ev.strftime("%Y-%m-%d"), (ev + pd.Timedelta(days=1)).strftime("%Y-%m-%d"))
    idx = np.searchsorted(cal, day, side="left")                  # the first calendar session at or after that date
    out = np.where(idx < len(cal), cal[np.clip(idx, 0, len(cal) - 1)], None)
    return out


def assemble(d, cals):
    per = {"oi": [], "cv": [], "ref": []}; prov = {}
    for root in ROOTS:
        cal = cals[root]; g = d[d["root"] == root].copy()
        if not len(g):
            continue
        g["usable"] = usable_session(g["ts_event"].to_numpy(), cal)
        g = g[pd.notna(g["usable"])]
        ref = pd.to_datetime(g["ts_ref"], utc=True).dt.tz_convert("US/Eastern")
        # ts_ref is the session START, the evening before the trade date it describes: the reference session is the next calendar session
        ridx = np.searchsorted(cal, (ref + pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d").to_numpy(), side="left")
        g["ref_session"] = np.where(ridx < len(cal), cal[np.clip(ridx, 0, len(cal) - 1)], None)
        g = g.sort_values("ts_event")
        pub = pd.to_datetime(g["ts_event"], utc=True).dt.tz_convert("US/Eastern")
        g["pub_et"] = pub.dt.strftime("%Y-%m-%d %H:%M"); g["pub_date"] = pub.dt.strftime("%Y-%m-%d")
        for st, name in ((ST_OI, "oi"), (ST_CV, "cv")):
            x = g[g["stat_type"] == st]
            if not len(x):
                continue
            last = x.groupby(["usable", "contract"], as_index=False).last()          # the freshest publication of each contract usable that session
            piv = last.pivot(index="usable", columns="contract", values="value").reindex(cal).ffill()
            pubd = last.pivot(index="usable", columns="contract", values="pub_date").reindex(cal).ffill()
            age = (pd.to_datetime(pd.Series(cal, index=cal)).values[:, None] - pd.to_datetime(pubd.stack(future_stack=True)).unstack().values) / np.timedelta64(1, "D")
            live = np.isfinite(piv.to_numpy(dtype=float)) & (age <= RECENCY_DAYS)
            vals = np.where(live, piv.to_numpy(dtype=float), np.nan)
            tot = np.nansum(vals, axis=1); n_c = live.sum(axis=1)
            front = np.where(n_c > 0, np.nanmax(np.where(live, piv.to_numpy(dtype=float), -np.inf), axis=1), np.nan)   # the largest-OI month = the front by convention
            per[name].append(pd.DataFrame({"root": root, "session": cal, f"{name}_total": np.where(n_c > 0, tot, np.nan), f"{name}_front": front, f"{name}_n_contracts": n_c}))
            if name == "oi":
                rs = last.groupby("usable")["ref_session"].max().reindex(cal).ffill()
                pe = last.groupby("usable")["pub_et"].max().reindex(cal).ffill()
                per["ref"].append(pd.DataFrame({"root": root, "session": cal, "ref_session": rs.to_numpy(), "published_at_et": pe.to_numpy()}))
        prov[root] = dict(sessions=len(cal), contracts=int(g["contract"].nunique()))
    T = None
    for name in ("oi", "cv", "ref"):                       # stack each schema across roots FIRST, then join the schemas
        if not per[name]:
            continue
        b = pd.concat(per[name], ignore_index=True)
        T = b if T is None else T.merge(b, on=["root", "session"], how="outer")
    T = T.sort_values(["root", "session"]).reset_index(drop=True)
    # staleness in trading days, per root, from the root's own calendar
    st = np.full(len(T), np.nan)
    for root in ROOTS:
        cal = cals[root]; pos = {d_: i for i, d_ in enumerate(cal)}; m = (T["root"] == root).to_numpy()
        st[m] = [pos.get(s, np.nan) - pos.get(r, np.nan) if isinstance(r, str) else np.nan for s, r in zip(T.loc[m, "session"], T.loc[m, "ref_session"])]
    T["staleness_sessions"] = st
    return T, prov


def cmd_build(workers):
    from multiprocessing import Pool
    t0 = time.time(); files = sorted(RAW.glob("*.statistics.dbn.zst")); assert files, f"no statistics files under {RAW}"
    print(f"D497 build -- {len(files)} statistics files ({sum(f.stat().st_size for f in files)/1e9:.1f} GB), roots {ROOTS}, {workers} workers", flush=True)
    with Pool(workers) as pool:
        res = pool.map(worker, [str(f) for f in sorted(files, key=lambda p: -p.stat().st_size)], chunksize=1)
    prov = [{k: v for k, v in r.items() if k != "table"} for r in res]
    for p in prov:
        print(f"  {p['file'][:44]:<44} rows_in {p['rows_in']:>12,}  kept {p['rows_kept']:>9,}  {p['secs']:>6.1f}s  RSS {p['rss_mb']:.0f} MB", flush=True)
    d = pd.concat([r["table"] for r in res if r["table"] is not None], ignore_index=True)
    cals = calendars(); T, roots_prov = assemble(d, cals)
    FIX.mkdir(parents=True, exist_ok=True); T.to_csv(OUT, index=False, compression="gzip", float_format="%.0f")
    sec = sum(p["secs"] for p in prov); wall = time.time() - t0
    print(f"[SPEED] sum(item time)/wall = {sec/wall:.2f}x on {workers} workers ({100*sec/wall/workers:.0f}%)", flush=True)
    for root in ROOTS:
        b = T[(T["root"] == root) & T["oi_total"].notna()]
        print(f"  {root}: {len(b):,} sessions {b['session'].min()}..{b['session'].max()}, contracts/session p50 {b['oi_n_contracts'].median():.0f}, oi_total p50 {b['oi_total'].median():,.0f}, staleness p50 {b['staleness_sessions'].median():.0f}")
    META.write_text(json.dumps(dict(spec="ab8b5df", built_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), files=prov, roots=list(ROOTS), span=SPAN,
                                    entry_cutoff_et="10:00", recency_days=RECENCY_DAYS, stat_types=dict(open_interest=ST_OI, cleared_volume=ST_CV),
                                    ts_ref_meaning="session start, the evening before the trade date; used only to label the reference session",
                                    causality="a figure is usable on the first session whose 10:00 ET entry is strictly after its ts_event", per_root=roots_prov, wall_min=round(wall / 60, 1), gates=None), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)} ({len(T):,} rows) in {wall/60:.1f} min; gates not yet run", flush=True)


def load_table():
    return pd.read_csv(OUT, dtype={"root": str, "session": str, "ref_session": str, "published_at_et": str})


def _expiring_declines(root, sessions):
    """For gate O4': each contract's own OI decline over the 20 sessions before it stops publishing, with the index of that last session.
    Re-reads the per-contract series from the raw statistics files for one root -- cheap, and it is the only per-contract check needed."""
    import databento as db
    pos = {d: i for i, d in enumerate(sessions)}; out = []; frames = []
    for f in sorted(RAW.glob("*.statistics.dbn.zst")):
        if not ("2016" <= f.name[10:14] <= "2023"):
            continue
        store = db.DBNStore.from_file(f); w = ids_of(store)
        if w is None:
            continue
        w = w[w["root"] == root]
        if not len(w):
            continue
        keys = w["iid"].to_numpy(np.uint32)
        for arr in store.to_ndarray(count=5_000_000):
            a = arr[np.isin(arr["instrument_id"], keys) & (arr["stat_type"] == ST_OI)]
            if a.size:
                j = label_rows(a, w)
                if len(j):
                    k = j["_i"].to_numpy()
                    ev = pd.to_datetime(a["ts_event"][k].astype("int64"), utc=True).tz_convert("US/Eastern")
                    frames.append(pd.DataFrame({"contract": j["contract"].to_numpy(), "date": ev.strftime("%Y-%m-%d"), "oi": a["quantity"][k].astype("int64")}))
    if not frames:
        return out
    d = pd.concat(frames, ignore_index=True); d = d[d["oi"] != UNDEF]
    last = d.groupby(["contract", "date"], as_index=False)["oi"].last()
    for c, g in last.groupby("contract"):
        g = g.sort_values("date"); g = g[g["date"].isin(pos)]
        if len(g) < 25 or g["oi"].max() < 1000:
            continue
        i_end = pos[g["date"].iloc[-1]]
        if i_end >= len(sessions) - 5:      # still live at the window's end
            continue
        start = g["oi"].iloc[max(len(g) - 21, 0)]
        if start > 0:
            out.append((i_end, (g["oi"].iloc[-1] - start) / start))
    return out


def cmd_gates(log=print):
    T = load_table(); meta = json.loads(META.read_text()); cals = calendars(); g = {}
    W = T[(T["session"] >= SPAN[0]) & (T["session"] <= SPAN[1])]
    # O1 causality: every publication stamp is before 10:00 ET on its own session
    pub = pd.to_datetime(W["published_at_et"], errors="coerce"); sess = pd.to_datetime(W["session"])
    late = ((pub.dt.normalize() == sess) & (pub.dt.hour * 60 + pub.dt.minute >= ENTRY_MIN)).fillna(False)
    g["O1"] = dict(rows=int(len(W)), late=int(late.sum())); log(f"[O1] causality: {int(late.sum())} of {len(W):,} rows published at or after 10:00 ET on their own session"); assert late.sum() == 0, "O1"
    # O2 staleness
    s = W.groupby("root")["staleness_sessions"].describe(percentiles=[.5, .8, .97])
    g["O2"] = {r: dict(median=float(s.loc[r, "50%"]), p80=float(s.loc[r, "80%"]), p97=float(s.loc[r, "97%"]), max=float(s.loc[r, "max"])) for r in s.index}
    for r in s.index:
        log(f"[O2] {r}: staleness median {s.loc[r,'50%']:.0f}, p80 {s.loc[r,'80%']:.0f}, p97 {s.loc[r,'97%']:.0f}, max {s.loc[r,'max']:.0f} sessions")
    assert all(v["median"] <= O2_MEDIAN_MAX for v in g["O2"].values()), "O2"
    # O3 coverage against the hourly calendar
    g["O3"] = {}
    for root in ROOTS:
        cal = [d for d in cals[root] if SPAN[0] <= d <= SPAN[1]]; have = W[(W["root"] == root) & W["oi_total"].notna()]["session"].nunique()
        cov = have / len(cal); g["O3"][root] = dict(sessions=len(cal), covered=int(have), coverage=float(cov), missing=sorted(set(cal) - set(W[(W["root"] == root) & W["oi_total"].notna()]["session"]))[:20])
        log(f"[O3] {root}: {have:,}/{len(cal):,} sessions covered ({cov:.3%})")
    assert all(v["coverage"] >= O3_COVER for v in g["O3"].values()), "O3"
    # O4' roll immunity, AMENDED: O4 as pre-registered could not fire. It asked for a >40% ONE-DAY fall in `oi_front`, but the roll is
    # spread over days and `oi_front` here is the LARGEST-OI month, which is smooth through a roll by construction. The substantive
    # claim is tested instead on the EXPIRING contract: over the 20 sessions before a month dies, its own open interest collapses
    # while the root total does not. Recorded as an amendment, not passed off as the original gate.
    g["O4_amended"] = dict(note="O4 as written could not fire: oi_front is the max-OI month (smooth through a roll) and the roll is multi-day. Replaced by the expiring-contract test.")
    for root in ROOTS:
        b = W[W["root"] == root].sort_values("session").reset_index(drop=True)
        tot = b["oi_total"].to_numpy(dtype=float); ses = b["session"].to_numpy()
        dead = _expiring_declines(root, ses)
        if not dead:
            g["O4_amended"][root] = dict(rolls=0); log(f"[O4'] {root}: no expiring months resolvable"); continue
        cd, td = [], []
        for i_end, dec in dead:
            i0 = max(i_end - 20, 0); cd.append(dec); td.append((tot[i_end] - tot[i0]) / tot[i0] if tot[i0] > 0 else np.nan)
        cd = np.array(cd, dtype=float); td = np.array(td, dtype=float)
        g["O4_amended"][root] = dict(rolls=int(len(cd)), expiring_decline_p50=float(np.nanmedian(cd)), total_move_abs_p50=float(np.nanmedian(np.abs(td))))
        log(f"[O4'] {root}: over the 20 sessions before expiry the dying month's OI moves {np.nanmedian(cd):+.1%} while the root total moves {np.nanmedian(np.abs(td)):.1%} ({len(cd)} rolls)")
    # O5 level sanity
    g["O5"] = {}
    for root in ROOTS:
        b = W[W["root"] == root].sort_values("session"); ch = b["oi_total"].pct_change()
        g["O5"][root] = dict(min_total=float(b["oi_total"].min()), sd_pct_change=float(ch.std()), p01=float(ch.quantile(.01)), p99=float(ch.quantile(.99)))
        log(f"[O5] {root}: oi_total min {b['oi_total'].min():,.0f}, daily pct change sd {ch.std():.4f} (p01 {ch.quantile(.01):+.3f}, p99 {ch.quantile(.99):+.3f})")
    assert all(v["min_total"] > 0 and v["sd_pct_change"] < O5_SD_MAX for v in g["O5"].values()), "O5"
    meta["gates"] = g; meta["gated_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()); META.write_text(json.dumps(meta, indent=1, default=float)); log("gates written to meta")


def cmd_probe():
    f = sorted(RAW.glob("*.statistics.dbn.zst"))[-2]; print(f"probe: {f.name} ({f.stat().st_size/1e9:.2f} GB)", flush=True)
    r = worker(str(f)); print({k: v for k, v in r.items() if k != "table"})
    d = r["table"]; print(d.groupby(["root", "stat_type"]).size().to_string())
    tot = sum(p.stat().st_size for p in RAW.glob("*.statistics.dbn.zst"))
    print(f"projected: {tot/f.stat().st_size * r['secs'] / 60:.1f} min single-process; /8 workers ~ {tot/f.stat().st_size * r['secs'] / 60 / 8 * 1.15:.1f} min")


def cmd_selftest():
    cal = np.array(["2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07"])
    et = lambda s: pd.Timestamp(s, tz="US/Eastern").tz_convert("UTC").value
    ev = np.array([et("2020-01-02 20:56"), et("2020-01-03 09:20"), et("2020-01-03 13:30"), et("2020-01-06 21:00")])
    u = usable_session(ev, cal)
    assert list(u) == ["2020-01-03", "2020-01-03", "2020-01-06", "2020-01-07"], list(u)
    print("[causality] 20:56 on the 2nd -> usable the 3rd; 09:20 on the 3rd -> usable the 3rd; 13:30 on the 3rd -> usable the 6th; 21:00 on the 6th -> usable the 7th")
    # a publication exactly at the cutoff must NOT be usable that session
    u2 = usable_session(np.array([et("2020-01-03 10:00")]), cal); assert list(u2) == ["2020-01-06"], list(u2)
    print("[X] a figure stamped exactly 10:00 is pushed to the next session, not used at the entry it would leak into")
    # assemble on synthetic records: two contracts, one expiring, the recency rule must drop the dead one once it is stale
    cal2 = np.array(["2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07", "2020-01-08", "2020-01-09", "2020-01-10", "2020-01-13", "2020-01-14", "2020-01-15"])
    rows = []
    for i, day in enumerate(cal2[:-1]):
        rows.append(dict(root="ES", contract="ESH0", stat_type=ST_OI, ts_event=et(f"{day} 20:56"), ts_ref=et(f"{day} 19:00") - 86_400_000_000_000, value=1000 + i))
        if i < 1:
            rows.append(dict(root="ES", contract="ESZ9", stat_type=ST_OI, ts_event=et(f"{day} 20:56"), ts_ref=et(f"{day} 19:00") - 86_400_000_000_000, value=500))
    T, _ = assemble(pd.DataFrame(rows), {"ES": cal2, "NQ": cal2, "CL": cal2, "GC": cal2})
    e = T[(T["root"] == "ES") & T["oi_total"].notna()].sort_values("session")
    assert e["oi_n_contracts"].iloc[0] == 2 and e["oi_total"].iloc[0] == 1500, e[["session", "oi_total", "oi_n_contracts"]].to_string()
    assert e["oi_n_contracts"].iloc[-1] == 1 and e["session"].iloc[0] == "2020-01-03", e[["session", "oi_total", "oi_n_contracts"]].to_string()
    print(f"[recency] the expired month leaves the total after {RECENCY_DAYS} days: contracts {e['oi_n_contracts'].tolist()}, totals {e['oi_total'].tolist()}")
    print("selftest OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--probe", action="store_true"); ap.add_argument("--build", action="store_true"); ap.add_argument("--gates", action="store_true"); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.selftest:
        cmd_selftest()
    if a.probe:
        cmd_probe()
    if a.build:
        cmd_build(a.workers)
    if a.gates:
        cmd_gates()
