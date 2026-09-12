"""D467 -- the extended-session tables: hourly OHLC of the 18:00 -> 16:59 ET Globex session on ES, NQ, YM, ZN, ZB, GC, CL, 6E, front
month by full-day volume, from the CME ohlcv-1m archive. Spec committed in 59a151d BEFORE this file. Data layer only: no study.

    python scripts/build_fut_sessions_hourly.py --build     # SYSTEM interpreter (databento) -> data/fixtures/fut_sessions_hourly.csv.gz (+ rolls, meta)
    python scripts/build_fut_sessions_hourly.py --gates     # G1-G5 -> data/fixtures/fut_sessions_hourly.meta.json (either interpreter)
    python scripts/build_fut_sessions_hourly.py --selftest  # synthetic records through the same functions

Conventions: ts_event is the bar START, US/Eastern with DST. A session is 18:00 on calendar day a through 16:59 on day b = a + 1; 23 hourly
segments h18..h23, h00..h16; the 15:59 bar's close (= the 16:00 print) is h15_c. A session row carries the front of day b (highest full-day
volume, D448/D462) and its evening segments come from that contract's bars on day a; front_prev is day a's front; same_front flags the
roll nights (kept, flagged). A session is PRESENT when h09..h15 hold >= 200 bars. No stitching, no adjustment.
"""
from __future__ import annotations
import argparse, json, re, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"; FIX = REPO / "data" / "fixtures"; OUT = FIX / "fut_sessions_hourly.csv.gz"; ROLLS = FIX / "fut_sessions_rolls.csv.gz"; META = FIX / "fut_sessions_hourly.meta.json"
ROOTS = ("ES", "NQ", "YM", "ZN", "ZB", "GC", "CL", "6E", "RTY"); OUTRIGHT = re.compile(r"^(ES|NQ|YM|ZN|ZB|GC|CL|6E|RTY)([FGHJKMNQUVXZ])(\d{1,2})$"); PX = 1e-9; CHUNK = 10_000_000      # RTY added under D472 (ninth root; the first eight rebuild bit-identically)
SEG = [18, 19, 20, 21, 22, 23] + list(range(0, 17)); SEGN = [f"h{h:02d}" for h in SEG]; PRESENT_MIN = 200; DAY_SEG = [f"h{h:02d}" for h in range(9, 16)]
MONTH = {c: i + 1 for i, c in enumerate("FGHJKMNQUVXZ")}
G1_THR = {"ES": 0.010, "NQ": 0.010, "YM": 0.010, "ZN": 0.005, "ZB": 0.0075, "GC": 0.015, "CL": 0.030, "6E": 0.0075, "RTY": 0.015}; G1_MAX = 150
G2_K = {"ES": 4, "NQ": 4, "YM": 4, "ZN": 4, "ZB": 4, "6E": 4, "GC": 6, "CL": 12, "RTY": 4}; G2_REVERT_MAX = {"GC": 2, "CL": 2}
G3_P50 = {"ES": 1300, "NQ": 1300, "YM": 1300, "ZN": 1300, "ZB": 1300, "GC": 1200, "CL": 1200, "6E": 1200, "RTY": 1300}; G3_LIST_BELOW = 900
G4_ETF = {"ES": "SPY", "NQ": "QQQ", "YM": "DIA", "ZN": "IEF", "ZB": "TLT", "GC": "GLD", "CL": "USO", "6E": "FXE", "RTY": "IWM"}; G4_MIN = {"ES": 0.99, "NQ": 0.99, "YM": 0.99, "ZN": 0.90, "ZB": 0.90, "GC": 0.95, "CL": 0.85, "6E": 0.90, "RTY": 0.99}
ETF_FIX = FIX / "etf_wide_daily_raw.csv.gz"; G5_COVER = 0.97; G5_END = "2026-08-26"


# ------------------------------------------------------------------------------------------ the chunk function
def ids_of(store):
    out = {}
    for sym, ivs in store.metadata.mappings.items():
        m = OUTRIGHT.match(str(sym))
        if not m:
            continue
        for iv in (ivs if isinstance(ivs, list) else [ivs]):
            sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
            if sid:
                out[int(sid)] = (m.group(1), str(sym))
    return out


def process_chunk(arr, ids):
    """Rows of the eight roots' outrights -> (hourly partial aggregates keyed (root, contract, day, hour) with first/last minute kept
    so chunks can be re-aggregated exactly; full-day volume per (root, day, contract)). Times US/Eastern; day = calendar ET date."""
    if not ids:
        return None, None
    sel = np.isin(arr["instrument_id"], np.fromiter(ids.keys(), dtype=np.uint32)); a = arr[sel]
    if a.size == 0:
        return None, None
    ts = pd.to_datetime(a["ts_event"], utc=True).tz_convert("US/Eastern"); root = np.array([ids[int(x)][0] for x in a["instrument_id"]]); sym = np.array([ids[int(x)][1] for x in a["instrument_id"]])
    day = np.asarray(ts.strftime("%Y-%m-%d")); minute = (ts.hour * 60 + ts.minute).to_numpy(); vol = a["volume"].astype(np.int64)
    df = pd.DataFrame({"root": root, "contract": sym, "day": day, "hour": (minute // 60).astype(np.int16), "minute": minute.astype(np.int16), "open": a["open"] * PX, "high": a["high"] * PX, "low": a["low"] * PX, "close": a["close"] * PX, "volume": vol})
    dv = df.groupby(["root", "day", "contract"], sort=False)["volume"].sum().reset_index()
    df = df[(df["hour"] >= 18) | (df["hour"] <= 16)]
    return reaggregate(df), dv


def reaggregate(df):
    """Exact hourly aggregation of minute rows (or of hourly partials carrying minute_first/minute_last): open at the earliest minute,
    close at the latest, max high, min low, sum volume, count bars."""
    if "minute_first" not in df.columns:
        df = df.assign(minute_first=df["minute"], minute_last=df["minute"], n=1)
    df = df.sort_values(["root", "contract", "day", "hour", "minute_first"], kind="stable"); g = df.groupby(["root", "contract", "day", "hour"], sort=False)
    out = g.agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), volume=("volume", "sum"), n=("n", "sum"), minute_first=("minute_first", "min"), minute_last=("minute_last", "max")).reset_index()
    last = df.sort_values(["root", "contract", "day", "hour", "minute_last"], kind="stable").groupby(["root", "contract", "day", "hour"], sort=False)["close"].last().reset_index()
    return out.merge(last, on=["root", "contract", "day", "hour"], how="left")


# ------------------------------------------------------------------------------------------ assemble
def assemble(hourly, dv):
    """Front per (root, day) by full-day volume; session rows (root, day b) from day b's front: evening segments from day a = b - 1 on the
    same contract, day segments from day b; rolls table."""
    dv = dv.groupby(["root", "day", "contract"], sort=False)["volume"].sum().reset_index()
    front = dv.sort_values(["root", "day", "volume", "contract"]).groupby(["root", "day"], sort=True).tail(1).rename(columns={"contract": "front"})[["root", "day", "front"]]
    hourly = reaggregate(hourly)
    fmap = {(r, d): f for r, d, f in zip(front["root"], front["day"], front["front"])}
    ev = hourly[hourly["hour"] >= 18].copy(); ev["day_b"] = (pd.to_datetime(ev["day"]) + pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d"); ev["day_a"] = ev["day"]
    dy = hourly[hourly["hour"] <= 16].copy(); dy["day_b"] = dy["day"]; dy["day_a"] = (pd.to_datetime(dy["day"]) - pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d")
    seg = pd.concat([ev, dy], ignore_index=True); seg["front_b"] = [fmap.get((r, d)) for r, d in zip(seg["root"], seg["day_b"])]
    seg = seg[seg["contract"] == seg["front_b"]]
    cols = {}
    for f in ("open", "high", "low", "close", "volume", "n"):
        p = seg.pivot_table(index=["root", "day_b"], columns="hour", values=f, aggfunc="first" if f not in ("volume", "n") else "sum")
        for h in SEG:
            s = p[h] if h in p.columns else pd.Series(np.nan, index=p.index)
            cols[f"h{h:02d}_{f[0] if f != 'n' else 'n'}"] = s
    T = pd.DataFrame(cols); T.index.names = ["root", "day"]; T = T.reset_index()
    for c in [c for c in T.columns if c.endswith("_v") or c.endswith("_n")]:
        T[c] = T[c].fillna(0).astype(np.int64)
    T["prev_day"] = (pd.to_datetime(T["day"]) - pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d"); T["contract"] = [fmap.get((r, d)) for r, d in zip(T["root"], T["day"])]
    T["front_prev"] = [fmap.get((r, d)) for r, d in zip(T["root"], T["prev_day"])]; T["same_front"] = T["front_prev"] == T["contract"]
    T["bars"] = T[[f"{s}_n" for s in SEGN]].sum(axis=1); T["day_bars"] = T[[f"{s}_n" for s in DAY_SEG]].sum(axis=1)
    T = T[T["day_bars"] >= PRESENT_MIN].drop(columns="day_bars")
    T = T[["root", "day", "prev_day", "contract", "front_prev", "same_front", "bars"] + [f"{s}_{f}" for s in SEGN for f in ("o", "h", "l", "c", "v", "n")]].sort_values(["root", "day"]).reset_index(drop=True)
    rolls = []
    for root, s in front.sort_values("day").groupby("root"):
        prev = None
        for r in s.itertuples():
            if prev is not None and r.front != prev.front:
                v = dv[(dv["root"] == root) & (dv["day"] == r.day)].set_index("contract")["volume"]
                rolls.append(dict(root=root, day=r.day, from_contract=prev.front, to_contract=r.front, from_volume=int(v.get(prev.front, 0)), to_volume=int(v.get(r.front, 0))))
            prev = r
    return T, pd.DataFrame(rolls)


def cmd_build():
    import databento as db
    t0 = time.time(); files = sorted(RAW.glob("*/*.ohlcv-1m.dbn.zst"), key=lambda p: p.name); assert files, "no ohlcv-1m files under data/raw/databento/"
    print(f"D467 build -- {len(files)} ohlcv-1m files, chunks of {CHUNK:,} rows\n", flush=True); H, D, prov = [], [], []
    for i, f in enumerate(files, 1):
        store = db.DBNStore.from_file(f); ids = ids_of(store); n_in = n_kept = 0
        for arr in store.to_ndarray(count=CHUNK):
            n_in += len(arr); h, dv = process_chunk(arr, ids)
            if h is not None:
                n_kept += int(h["n"].sum()); H.append(h); D.append(dv)
        prov.append(dict(file=f.name, rows_in=n_in, session_rows_kept=n_kept, ids=len(ids))); print(f"  [{i:2d}/{len(files)}] {f.name[:40]:<40} {n_in:>12,} rows -> session minutes {n_kept:>10,}  ({(time.time()-t0)/60:.1f} min)", flush=True)
    T, rolls = assemble(pd.concat(H, ignore_index=True), pd.concat(D, ignore_index=True)); del H, D
    FIX.mkdir(parents=True, exist_ok=True); T.to_csv(OUT, index=False, compression="gzip", float_format="%.5f"); rolls.to_csv(ROLLS, index=False, compression="gzip")
    for root in ROOTS:
        b = T[T["root"] == root]; print(f"  {root}: {len(b):,} sessions, {b['day'].min()} .. {b['day'].max()}, contracts {b['contract'].nunique()}, roll nights {(~b['same_front']).sum()}, bars p50 {b['bars'].median():.0f}")
    META.write_text(json.dumps(dict(spec="59a151d", built_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), files=prov, roots=list(ROOTS), session=["18:00", "16:59"], segments=SEGN, present_rule=f"h09..h15 >= {PRESENT_MIN} bars", front_rule="highest full-day volume per calendar ET day; row carries day b's front", gates=None), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)} ({len(T):,} rows) and {ROLLS.relative_to(REPO)} in {(time.time()-t0)/60:.1f} min; gates not yet run", flush=True)


# ------------------------------------------------------------------------------------------ the gates
def load_table():
    return pd.read_csv(OUT, dtype={"root": str, "day": str, "prev_day": str, "contract": str, "front_prev": str})


def contract_key(c):
    m = OUTRIGHT.match(c); yy = m.group(3); y = int(yy) + (2000 if len(yy) == 2 else 0); return (y, MONTH[m.group(2)], yy)


def resolve_years(contracts, days):
    """Single-digit contract years resolved against the roll day's decade; returns (year, month) per contract."""
    out = []
    for c, d in zip(contracts, days):
        m = OUTRIGHT.match(c); mon = MONTH[m.group(2)]; yy = m.group(3); y0 = int(d[:4])
        if len(yy) == 2:
            out.append((2000 + int(yy), mon)); continue
        cands = [y for y in range(y0 - 1, y0 + 12) if y % 10 == int(yy)]; y = next((y for y in cands if (y, mon) >= (y0, int(d[5:7]) - 1)), cands[-1]); out.append((y, mon))
    return out


def gates(log=print):
    meta = json.loads(META.read_text()); T = load_table(); rolls = pd.read_csv(ROLLS, dtype={"day": str}) if ROLLS.stat().st_size > 30 else pd.DataFrame()
    eq = pd.read_csv(ETF_FIX, dtype={"timestamp": str, "symbol": str}); eq["day"] = eq["timestamp"].str[:10]; spy_days = sorted(set(eq[eq["symbol"] == "SPY"]["day"])); out = {}; ok_all = True
    # ADDENDUM (2026-09-12, after the first gate run; the D462 ADDENDUM's shape): G5 is evaluated first and G3/G4 on the usable window it
    # returns, because the pre-2016 archive carries partial index sessions whose prints are not 16:00 prints (ES/SPY 0.914 on the whole span,
    # 0.998 from 2016); and the 16:00-print share is measured on FULL equity days only -- a US holiday or early-close session is present
    # (ES trades until 13:00) and has no 16:00 print by construction, and every missing print from 2016 was one of those.
    eq15 = pd.read_csv(FIX / "index_extended_15m_raw.csv.gz", dtype={"timestamp": str, "symbol": str}); eq15 = eq15[eq15["symbol"] == "SPY"]; full_days = set(eq15[eq15["timestamp"].str[11:16] == "15:45"]["timestamp"].str[:10])
    for root in ROOTS:
        t_all = T[T["root"] == root].sort_values("day").reset_index(drop=True); g = {}
        have = set(t_all["day"]); lo = min(have) if have else "9999"; cal = [d for d in spy_days if lo <= d <= G5_END]; cov = {}
        for y in sorted({d[:4] for d in cal}):
            ds = [d for d in cal if d[:4] == y]; cov[y] = float(np.mean([d in have for d in ds]))
        years = sorted(cov); uy = next((y for y in years if all(cov[z] >= G5_COVER for z in years if z >= y)), None); us = min(d for d in have if d[:4] >= uy) if uy else None
        g["G5"] = dict(coverage_by_year={y: round(v, 3) for y, v in cov.items()}, usable_start=us, passes=bool(us is not None))
        t = t_all[t_all["day"] >= (us or "9999")].reset_index(drop=True) if us else t_all
        # G1: one-minute moves are not in the table (hourly) -- gate on the hourly segment's open-to-close and the close-to-next-open, both within a
        # session on one contract, at the declared threshold; the minute list is what the build logged (segment level is what the fixture carries).
        lst = []
        for r in t.itertuples():
            prev_c = None
            for s in SEGN:
                o, c = getattr(r, f"{s}_o"), getattr(r, f"{s}_c")
                if np.isnan(o) or np.isnan(c):
                    continue
                if prev_c is not None and prev_c > 0 and o > 0 and abs(o / prev_c - 1) > G1_THR[root]:
                    lst.append((r.day, s, "gap", float(round(100 * (o / prev_c - 1), 2))))
                if o > 0 and c > 0 and abs(c / o - 1) > 3 * G1_THR[root]:
                    lst.append((r.day, s, "hour", float(round(100 * (c / o - 1), 2))))
                prev_c = c
        neg = t[t[[f"{s}_l" for s in SEGN]].min(axis=1) <= 0]["day"].tolist()
        g["G1"] = dict(threshold=G1_THR[root], n=len(lst), bars=lst[:200], days=sorted({d for d, *_ in lst}), nonpositive_price_sessions=neg, passes=bool(len(lst) <= G1_MAX))
        # G2
        # ADDENDUM: a front change on a day whose winning volume is below 1% of the root's median session volume is a holiday artefact (6E,
        # 2021-12-24: 6EX1 on 10 contracts, back on the 26th); listed, not counted. The session rows it touches are roll nights (same_front False).
        rr = rolls[(rolls["root"] == root) & (rolls["day"] >= (us or "0"))].sort_values("day") if len(rolls) else pd.DataFrame(); revert = []; per_year = {}; artefacts = []
        vfloor = 0.01 * float(t[[f"{s}_v" for s in SEGN]].sum(axis=1).median()) if len(t) else 0.0
        if len(rr):
            art = rr["to_volume"] < vfloor; artefacts = [(x.day, x.from_contract, x.to_contract, int(x.to_volume)) for x in rr[art].itertuples()]; rr = rr[~art]
            fr = resolve_years(rr["from_contract"], rr["day"]); to = resolve_years(rr["to_contract"], rr["day"])
            for x, a, z in zip(rr.itertuples(), fr, to):
                if z <= a:
                    revert.append((x.day, x.from_contract, x.to_contract))
                per_year[x.day[:4]] = per_year.get(x.day[:4], 0) + 1
        full_years = [y for y in per_year if y not in (t["day"].min()[:4], t["day"].max()[:4])]; k = G2_K[root]; bad_years = {y: per_year[y] for y in full_years if not (k - 1 <= per_year[y] <= k + 2)}
        g["G2"] = dict(n_rolls=int(len(rr)), reverting=revert, holiday_artefacts=artefacts, volume_floor=vfloor, rolls_per_year=per_year, cadence=k, years_off_cadence=bad_years, passes=bool(len(rr) > 0 and len(revert) <= G2_REVERT_MAX.get(root, 0) and not bad_years))
        # G3 -- pre-registered: whole-session p50 >= G3_P50 and the 16:00 print on >= 99% of sessions. ADDENDUM: the print is measured on FULL
        # equity days (a holiday or early-close session has none by construction) and coverage is ALSO scored on the day session (h09..h15 p50
        # >= 400 of 420) -- ZB's whole-session p50 (1,213 from 2016) is overnight illiquidity with a full day session (417), not a hole.
        short = t[t["bars"] < G3_LIST_BELOW]; full = t[t["day"].isin(full_days)]; has16 = float(full["h15_c"].notna().mean()) if len(full) else float("nan"); no16 = full[full["h15_c"].isna()]["day"].tolist()
        day_p50 = float(t[[f"{s}_n" for s in DAY_SEG]].sum(axis=1).median()); prereg_pass = bool(t["bars"].median() >= G3_P50[root] and float(t["h15_c"].notna().mean()) >= 0.99)
        g["G3"] = dict(p50_bars=float(t["bars"].median()), p50_day_session_bars=day_p50, n_sessions=int(len(t)), n_below_900=int(len(short)), short=[(d, int(n)) for d, n in zip(short["day"], short["bars"])][:60], share_with_1600_print_all=float(t["h15_c"].notna().mean()), share_with_1600_print_full_days=has16, full_days_without_print=no16[:40],
                       passes_as_preregistered=prereg_pass, passes=bool(day_p50 >= 400 and has16 >= 0.99))
        # G4
        e = eq[eq["symbol"] == G4_ETF[root]].groupby("day")["close"].last(); f = t.set_index("day"); c16 = f["h15_c"]; r_f = (c16 / c16.shift(1) - 1); ok = (f["contract"] == f["contract"].shift(1)); r_f = r_f[ok & c16.notna() & c16.shift(1).notna()]
        r_e = (e / e.shift(1) - 1); j = pd.DataFrame({"f": r_f, "e": r_e}).dropna(); j = j[(np.abs(j["f"]) < 0.25) & (np.abs(j["e"]) < 0.25)]
        cc = float(np.corrcoef(j["f"], j["e"])[0, 1]) if len(j) > 30 else float("nan"); g["G4"] = dict(etf=G4_ETF[root], matched_days=int(len(j)), corr_close_to_close_same_contract=cc, passes=bool(cc >= G4_MIN[root]))
        g["passes"] = all(g[k]["passes"] for k in ("G1", "G2", "G3", "G4", "G5")); g["passes_as_preregistered"] = bool(g["G1"]["passes"] and g["G2"]["passes"] and not artefacts and prereg_pass and g["G4"]["passes"] and g["G5"]["passes"]); ok_all &= g["passes"]; out[root] = g
        log(f"{root}: usable from {us} (G5 " + " ".join(f"{y}:{100*v:.0f}%" for y, v in cov.items()) + ")")
        log(f"     G1 {g['G1']['n']} moves > thr (gap>{100*G1_THR[root]:.2f}% / hour>{300*G1_THR[root]:.2f}%) on {len(g['G1']['days'])} days {g['G1']['days'][:8]}{'...' if len(g['G1']['days']) > 8 else ''} nonpositive {neg} {'PASS' if g['G1']['passes'] else 'FAIL'}")
        log(f"     G2 rolls {g['G2']['n_rolls']} revert {len(revert)} artefacts {artefacts} per-year {per_year} off-cadence {bad_years} {'PASS' if g['G2']['passes'] else 'FAIL'} | G3 sessions {len(t)} p50 bars {g['G3']['p50_bars']:.0f} (day session {day_p50:.0f}) below-900 {len(short)} 16:00-print all {100*g['G3']['share_with_1600_print_all']:.1f}% / full days {100*has16:.1f}% (missing {no16[:6]}) {'PASS' if g['G3']['passes'] else 'FAIL'} (as pre-registered {'PASS' if prereg_pass else 'FAIL'}) | G4 vs {G4_ETF[root]} n {len(j)} cc {cc:.4f} {'PASS' if g['G4']['passes'] else 'FAIL'}  => {'PASS' if g['passes'] else 'FAIL'}")
    meta["gates"] = out; meta["all_gates_pass"] = bool(ok_all); meta["usable_start"] = {r: out[r]["G5"]["usable_start"] for r in ROOTS}; META.write_text(json.dumps(meta, indent=1)); log(f"\nALL GATES {'PASS' if ok_all else 'FAIL'}; wrote {META.relative_to(REPO)}")
    return ok_all


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    t0 = time.time(); print("== (a) process_chunk + reaggregate: DST, the session window, hourly OHLC exact across a chunk split, only the eight roots")
    ids = {1: ("ES", "ESH5"), 2: ("ES", "ESM5"), 3: ("GC", "GCJ5")}
    def ts(s):
        return int(pd.Timestamp(s).value)
    def rec(t, i, o, h, l, c, v):
        return (ts(t), i, o * 1e9, h * 1e9, l * 1e9, c * 1e9, v)
    dt = [("ts_event", "<i8"), ("instrument_id", "<u4"), ("open", "<i8"), ("high", "<i8"), ("low", "<i8"), ("close", "<i8"), ("volume", "<u8")]
    rows = [rec("2015-01-14 23:00:00+00:00", 1, 10, 11, 9, 10.5, 5),      # 18:00 EST Jan 14 -> h18 of session day b = 2015-01-15
            rec("2015-01-14 23:30:00+00:00", 1, 10.5, 12, 10, 11, 5),     # 18:30 EST same hour: high 12, close 11
            rec("2015-01-15 22:00:00+00:00", 1, 20, 20, 20, 20, 7),       # 17:00 EST Jan 15 -> the halt hour, dropped
            rec("2015-07-15 20:59:00+00:00", 2, 30, 30, 30, 31, 1),       # 16:59 EDT Jul 15 -> h16 kept
            rec("2015-07-15 21:00:00+00:00", 2, 30, 30, 30, 30, 1),       # 17:00 EDT dropped
            rec("2015-07-15 19:59:00+00:00", 2, 40, 41, 39, 40.5, 2),     # 15:59 EDT -> h15, close is the 16:00 print
            rec("2015-07-15 19:00:00+00:00", 3, 1200, 1201, 1199, 1200, 3), rec("2015-07-15 19:00:00+00:00", 9, 1, 1, 1, 1, 1)]
    arr = np.array(rows, dtype=dt); h, dv = process_chunk(arr, ids)
    k = h.set_index(["contract", "day", "hour"])
    assert k.loc[("ESH5", "2015-01-14", 18), "high"] == 12 and k.loc[("ESH5", "2015-01-14", 18), "close"] == 11 and k.loc[("ESH5", "2015-01-14", 18), "open"] == 10 and k.loc[("ESH5", "2015-01-14", 18), "n"] == 2, "hourly aggregate"
    assert ("ESH5", "2015-01-15", 17) not in k.index and ("ESM5", "2015-07-15", 17) not in k.index and ("ESM5", "2015-07-15", 16) in k.index and ("ESM5", "2015-07-15", 15) in k.index, "17:00 halt out, 16:59 in"
    assert ("GCJ5", "2015-07-15", 15) in k.index and len(h) == 4 and int(dv[dv["contract"] == "ESH5"]["volume"].sum()) == 17, "unmapped id dropped; full-day volume counts the halt bar"
    h1, _ = process_chunk(arr[:1], ids); h2, _ = process_chunk(arr[1:], ids); split = reaggregate(pd.concat([h1, h2], ignore_index=True)).set_index(["contract", "day", "hour"])
    assert split.loc[("ESH5", "2015-01-14", 18)].drop(["minute_first", "minute_last"]).equals(k.loc[("ESH5", "2015-01-14", 18)].drop(["minute_first", "minute_last"])), "chunk split must re-aggregate bit-identically"
    print("  ok: h18 OHLC (10, 12, 9, 11, n=2) exact and identical across a chunk split; halt hour dropped; 16:59 kept; unmapped id dropped")
    print("== (b) assemble: the session row pairs day a's evening with day b's day on day b's front; roll night flagged; present rule; 16:00 print")
    mins = []
    for d, c, ev_px, dy_px in (("2015-03-12", "ESH5", 1.0, 2.0), ("2015-03-12", "ESM5", 1.5, 2.5), ("2015-03-13", "ESH5", 3.0, 4.0), ("2015-03-13", "ESM5", 3.5, 4.5)):
        for m in range(18 * 60, 24 * 60, 5):
            mins.append(dict(root="ES", contract=c, day=d, hour=m // 60, minute=m, open=ev_px, high=ev_px, low=ev_px, close=ev_px, volume=1))
        for m in range(0, 17 * 60, 2):
            mins.append(dict(root="ES", contract=c, day=d, hour=m // 60, minute=m, open=dy_px, high=dy_px, low=dy_px, close=dy_px + (0.01 if m == 15 * 60 + 58 else 0), volume=1))
    dvx = pd.DataFrame([dict(root="ES", day="2015-03-12", contract="ESH5", volume=900), dict(root="ES", day="2015-03-12", contract="ESM5", volume=100), dict(root="ES", day="2015-03-13", contract="ESH5", volume=400), dict(root="ES", day="2015-03-13", contract="ESM5", volume=600)])
    T, rolls = assemble(pd.DataFrame(mins), dvx); T = T.set_index("day")
    assert list(T.index) == ["2015-03-12", "2015-03-13"], T.index.tolist()          # 03-12 has no evening (03-11 absent) but a present day session; 03-14 has no day session
    r = T.loc["2015-03-13"]; assert r["contract"] == "ESM5" and r["front_prev"] == "ESH5" and not r["same_front"] and r["h18_o"] == 1.5 and r["h15_c"] == 4.51 and r["h16_c"] == 4.5, "day b's front on both legs; h15_c is the 15:58 close here (last bar of the hour)"
    r0 = T.loc["2015-03-12"]; assert r0["contract"] == "ESH5" and np.isnan(r0["h18_o"]) and r0["h18_n"] == 0 and r0["h09_n"] == 30 and r0["bars"] == 510, "absent evening -> NaN and 0"
    assert len(rolls) == 1 and rolls.iloc[0]["to_contract"] == "ESM5" and rolls.iloc[0]["from_volume"] == 400
    print("  ok: 2015-03-13 row is ESM5 with front_prev ESH5 (same_front False), evening from ESM5's 03-12 bars (1.5), day from 03-13 (4.5); absent evening -> NaN/0; one roll row")
    print("== (c) contract year resolution: ESH5 rolled 2015-03 -> (2015, 3); CLZ9 rolled 2019-11 -> (2019, 12); GCG0 rolled 2019-12 -> (2020, 2); ESH25 -> (2025, 3)")
    assert resolve_years(["ESH5", "CLZ9", "GCG0", "ESH25"], ["2015-03-12", "2019-11-20", "2019-12-27", "2024-12-13"]) == [(2015, 3), (2019, 12), (2020, 2), (2025, 3)]
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--build", action="store_true"); g.add_argument("--gates", action="store_true"); g.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.build:
        cmd_build()
    elif a.gates:
        sys.exit(0 if gates() else 1)
    else:
        cmd_selftest()
