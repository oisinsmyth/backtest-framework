"""D462 -- the intraday index-futures fixtures: ES, NQ, YM, RTY at one minute, regular hours (09:30-15:59 ET), front month by
measured daily volume, from the CME ohlcv-1m archive. Spec committed in de75a63 BEFORE this file. Data layer only: no study.

    python scripts/build_fut_index_1m.py --build       # SYSTEM interpreter (databento lives there, as D448/D449) -> data/fixtures/fut_*.csv.gz
    python scripts/build_fut_index_1m.py --gates       # G1-G4 on the written fixtures -> data/fixtures/fut_index_1m.meta.json (either interpreter)
    python scripts/build_fut_index_1m.py --selftest    # synthetic records through the same chunk function; DST; the 15:59 bar; front-by-volume; roll logic

Conventions: ts_event is the bar START, converted US/Eastern with DST; RTH = hhmm 09:30..15:59 (390 bars; the 15:59 close is the 16:00
print); front month per (root, calendar ET day) = the outright with the highest volume over the whole day (D448); every fixture bar
belongs to that day's front contract; no stitching, no adjustment.
"""
from __future__ import annotations
import argparse, json, re, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"; FIX = REPO / "data" / "fixtures"; META = FIX / "fut_index_1m.meta.json"
ROOTS = ("ES", "NQ", "YM", "RTY"); OUTRIGHT = re.compile(r"^(ES|NQ|YM|RTY)([FGHJKMNQUVXZ])(\d{1,2})$"); PX = 1e-9; CHUNK = 10_000_000
RTH_LO, RTH_HI = "09:30", "15:59"; MONTH = {c: i + 1 for i, c in enumerate("FGHJKMNQUVXZ")}; QUARTERLY = "HMUZ"
G1_THR = {"ES": 0.010, "NQ": 0.010, "YM": 0.010, "RTY": 0.015}; G1_MAX = 40; G3_FULL = 380; G5_PRESENT = 200; G4_OC = {"ES": 0.995, "NQ": 0.995, "YM": 0.995, "RTY": 0.99}; G4_CC = 0.99
ETF = {"ES": "SPY", "NQ": "QQQ", "YM": "DIA", "RTY": "IWM"}; EQ_FIX = FIX / "index_extended_15m_raw.csv.gz"


def fixture_path(root):
    return FIX / f"fut_{root}_rth_1m.csv.gz"


# ------------------------------------------------------------------------------------------ the chunk function (the whole build is this, repeated)
def ids_of(store):
    """instrument_id -> (root, symbol) for the four roots' outrights, from the file's symbology mappings."""
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
    """Rows of the four roots' outrights -> (rth DataFrame, day-volume DataFrame). Times US/Eastern; day = calendar ET date."""
    if not ids:
        return None, None
    sel = np.isin(arr["instrument_id"], np.fromiter(ids.keys(), dtype=np.uint32)); a = arr[sel]
    if a.size == 0:
        return None, None
    ts = pd.to_datetime(a["ts_event"], utc=True).tz_convert("US/Eastern"); root = np.array([ids[int(x)][0] for x in a["instrument_id"]]); sym = np.array([ids[int(x)][1] for x in a["instrument_id"]])
    day = ts.strftime("%Y-%m-%d"); hhmm = ts.strftime("%H:%M"); vol = a["volume"].astype(np.int64)
    dv = pd.DataFrame({"root": root, "day": day, "contract": sym, "volume": vol}).groupby(["root", "day", "contract"], sort=False)["volume"].sum().reset_index()
    rth = (hhmm >= RTH_LO) & (hhmm <= RTH_HI)
    bars = pd.DataFrame({"root": root[rth], "day": np.asarray(day)[rth], "hhmm": np.asarray(hhmm)[rth], "contract": sym[rth], "open": a["open"][rth] * PX, "high": a["high"][rth] * PX, "low": a["low"][rth] * PX, "close": a["close"][rth] * PX, "volume": vol[rth]})
    return bars, dv


def assemble(bars, dv):
    """Front month per (root, day) by full-day volume; keep the front's RTH bars; sessions and rolls tables."""
    dv = dv.groupby(["root", "day", "contract"], sort=False)["volume"].sum().reset_index()
    front = dv.sort_values(["root", "day", "volume", "contract"]).groupby(["root", "day"], sort=True).tail(1).rename(columns={"contract": "front", "volume": "day_volume"})
    bars = bars.merge(front[["root", "day", "front"]], on=["root", "day"], how="inner"); bars = bars[bars["contract"] == bars["front"]].drop(columns="front")
    bars = bars.sort_values(["root", "day", "hhmm"]).drop_duplicates(["root", "day", "hhmm"]).reset_index(drop=True)
    g = bars.groupby(["root", "day"], sort=True); first = g.first(); last = g.last()
    sess = pd.DataFrame({"contract": first["contract"], "bars": g.size(), "p0930": np.where(first["hhmm"] == RTH_LO, first["open"], np.nan), "p1600": np.where(last["hhmm"] == RTH_HI, last["close"], np.nan), "rth_volume": g["volume"].sum()}).reset_index()
    sess = sess.merge(front[["root", "day", "day_volume"]], on=["root", "day"], how="left"); sess["roll"] = sess.groupby("root")["contract"].shift(1).ne(sess["contract"]) & sess.groupby("root")["contract"].shift(1).notna()
    rolls = []
    for root, s in sess.groupby("root"):
        prev = None
        for r in s.itertuples():
            if prev is not None and r.contract != prev.contract:
                v = dv[(dv["root"] == root) & (dv["day"] == r.day)].set_index("contract")["volume"]
                rolls.append(dict(root=root, day=r.day, from_contract=prev.contract, to_contract=r.contract, from_volume=int(v.get(prev.contract, 0)), to_volume=int(v.get(r.contract, 0))))
            prev = r
    return bars, sess, pd.DataFrame(rolls)


def cmd_build():
    import databento as db
    t0 = time.time(); files = sorted(RAW.glob("*/*.ohlcv-1m.dbn.zst"), key=lambda p: p.name); assert files, "no ohlcv-1m files under data/raw/databento/"
    print(f"D462 build -- {len(files)} ohlcv-1m files, chunks of {CHUNK:,} rows\n"); B, D, prov = [], [], []
    for i, f in enumerate(files, 1):
        store = db.DBNStore.from_file(f); ids = ids_of(store); n_in = n_kept = 0
        for arr in store.to_ndarray(count=CHUNK):
            n_in += len(arr); bars, dv = process_chunk(arr, ids)
            if bars is not None:
                n_kept += len(bars); B.append(bars); D.append(dv)
        prov.append(dict(file=f.name, rows_in=n_in, rth_rows_kept=n_kept, ids=len(ids))); print(f"  [{i:2d}/{len(files)}] {f.name[:40]:<40} {n_in:>12,} rows -> RTH rows {n_kept:>9,}  ({(time.time()-t0)/60:.1f} min)", flush=True)
    bars, sess, rolls = assemble(pd.concat(B, ignore_index=True), pd.concat(D, ignore_index=True)); del B, D
    FIX.mkdir(parents=True, exist_ok=True)
    for root in ROOTS:
        b = bars[bars["root"] == root].drop(columns="root"); b.to_csv(fixture_path(root), index=False, compression="gzip", float_format="%.2f"); print(f"  {root}: {len(b):,} bars, {b['day'].nunique():,} sessions, {b['day'].min()} .. {b['day'].max()}, contracts {b['contract'].nunique()}")
    sess.to_csv(FIX / "fut_index_sessions.csv.gz", index=False, compression="gzip", float_format="%.2f"); rolls.to_csv(FIX / "fut_index_rolls.csv.gz", index=False, compression="gzip")
    META.write_text(json.dumps(dict(spec="de75a63", built_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), files=prov, roots=list(ROOTS), rth=[RTH_LO, RTH_HI], front_rule="highest full-day volume per calendar ET day", gates=None), indent=1))
    print(f"\nwrote fixtures in {(time.time()-t0)/60:.1f} min; gates not yet run (python scripts/build_fut_index_1m.py --gates)")


# ------------------------------------------------------------------------------------------ the gates
def third_friday(y, m):
    d = pd.Timestamp(year=y, month=m, day=1); off = (4 - d.dayofweek) % 7; return d + pd.Timedelta(days=off + 14)


def expiry_of(contract, roll_day):
    m = OUTRIGHT.match(contract); mon = MONTH[m.group(2)]; yy = int(m.group(3)); y0 = int(roll_day[:4])
    cands = [y for y in range(y0 - 1, y0 + 12) if (y % 10 == yy if len(m.group(3)) == 1 else y % 100 == yy)]
    for y in cands:
        e = third_friday(y, mon)
        if e >= pd.Timestamp(roll_day) - pd.Timedelta(days=5):
            return e
    return third_friday(cands[-1], mon)


def gates(log=print):
    meta = json.loads(META.read_text()); sess = pd.read_csv(FIX / "fut_index_sessions.csv.gz", dtype={"day": str, "contract": str}); rolls = pd.read_csv(FIX / "fut_index_rolls.csv.gz", dtype={"day": str}) if (FIX / "fut_index_rolls.csv.gz").stat().st_size > 30 else pd.DataFrame()
    eq = pd.read_csv(EQ_FIX, dtype={"timestamp": str, "symbol": str}); eq["day"] = eq["timestamp"].str[:10]; eq["hhmm"] = eq["timestamp"].str[11:16]; out = {}; ok_all = True
    for root in ROOTS:
        b = pd.read_csv(fixture_path(root), dtype={"day": str, "hhmm": str, "contract": str}); s = sess[sess["root"] == root].sort_values("day").reset_index(drop=True); g = {}
        # G1 unexplained bars
        c = b["close"].to_numpy(); same = (b["day"].to_numpy()[1:] == b["day"].to_numpy()[:-1]) & (b["contract"].to_numpy()[1:] == b["contract"].to_numpy()[:-1]); r = np.abs(c[1:] / c[:-1] - 1); big = np.flatnonzero(same & (r > G1_THR[root])) + 1
        lst = [(b["day"].iat[i], b["hhmm"].iat[i], float(round(100 * (c[i] / c[i - 1] - 1), 2))) for i in big]; g["G1"] = dict(threshold=G1_THR[root], n=len(lst), bars=lst, days=sorted({d for d, _, _ in lst}), passes=bool(len(lst) <= G1_MAX))
        # G2 rolls
        rr = rolls[rolls["root"] == root].sort_values("day") if len(rolls) else pd.DataFrame(); fwd = revert = 0; dbe = []; per_q = {}
        for x in rr.itertuples():
            a, z = OUTRIGHT.match(x.from_contract), OUTRIGHT.match(x.to_contract); ea, ez = expiry_of(x.from_contract, x.day), expiry_of(x.to_contract, x.day)
            fwd += ez > ea; revert += ez < ea; dbe.append(int(np.busday_count(np.datetime64(x.day), np.datetime64(str(ea.date()))))); q = f"{ea.year}Q{(ea.month-1)//3+1}"; per_q[q] = per_q.get(q, 0) + 1
        multi = sum(v > 1 for v in per_q.values()); dbe = np.array(dbe)
        g["G2"] = dict(n_rolls=int(len(rr)), forward=int(fwd), reverting=int(revert), quarters_with_more_than_one=int(multi), days_before_expiry_p50=float(np.median(dbe)) if dbe.size else None, days_before_expiry_min=int(dbe.min()) if dbe.size else None, days_before_expiry_max=int(dbe.max()) if dbe.size else None,
                      passes=bool(len(rr) > 0 and revert == 0 and multi == 0 and dbe.min() >= 0 and dbe.max() <= 15))
        # G3 coverage
        short = s[s["bars"] < G3_FULL]; early = short[short["bars"].between(200, 220)]; hh = b.groupby("hhmm").size(); full_days = int((s["bars"] >= G3_FULL).sum()); present = float((hh >= 0.99 * full_days).mean())
        g["G3"] = dict(p50_bars=float(s["bars"].median()), n_sessions=int(len(s)), n_short=int(len(short)), n_early_close_like=int(len(early)), other_short=[(d, int(n)) for d, n in zip(short[~short.index.isin(early.index)]["day"], short[~short.index.isin(early.index)]["bars"])][:40], share_hhmm_present_on_99pct=present, passes=bool(s["bars"].median() == 390 and present >= 0.99))
        # G4 cross-check
        e = eq[eq["symbol"] == ETF[root]]; eo = e[e["hhmm"] == "09:30"].groupby("day")["open"].first(); ec = e[e["hhmm"] == "15:45"].groupby("day")["close"].last(); ed = pd.DataFrame({"eo": eo, "ec": ec}).dropna()
        f = s.set_index("day")[["p0930", "p1600", "contract"]].dropna(); j = f.join(ed, how="inner"); oc_f = j["p1600"] / j["p0930"] - 1; oc_e = j["ec"] / j["eo"] - 1; oc = float(np.corrcoef(oc_f, oc_e)[0, 1]) if len(j) > 30 else float("nan")
        same_c = (j["contract"].shift(1) == j["contract"]); cc_f = (j["p1600"] / j["p1600"].shift(1) - 1)[same_c]; cc_e = (j["ec"] / j["ec"].shift(1) - 1)[same_c]; cc = float(np.corrcoef(cc_f.dropna(), cc_e.dropna())[0, 1]) if same_c.sum() > 30 else float("nan")
        g["G4"] = dict(etf=ETF[root], matched_days=int(len(j)), corr_open_to_close=oc, corr_close_to_close_same_contract=cc, passes=bool(oc >= G4_OC[root] and cc >= G4_CC))
        # G5 (added 2026-09-12 after the build, see the D462 ADDENDUM): sessions against the equity calendar, per year. The early archive
        # carries the index futures' evening bars but not their day session on most days before 2016 -- G3 counts bars per PRESENT
        # session and could not see a missing session. usable_start = the first year from which every later year has >= 97% of the
        # equity calendar's days as full (>= G3_FULL bars) sessions.
        # a session is PRESENT when it has a day session at all (>= G5_PRESENT bars: early closes and the March-2020 halted days count);
        # G3 already scores short sessions -- G5 scores absent ones
        spy_days = sorted(set(eq[eq["symbol"] == "SPY"]["day"])); have = set(s[s["bars"] >= G5_PRESENT]["day"]); lo = min(have) if have else "9999"; cal = [d for d in spy_days if d >= lo and d <= "2026-08-26"]
        cov = {}
        for y in sorted({d[:4] for d in cal}):
            ds = [d for d in cal if d[:4] == y]; cov[y] = float(np.mean([d in have for d in ds]))
        years = sorted(cov); usable_year = next((y for y in years if all(cov[z] >= 0.97 for z in years if z >= y)), None)
        usable_start = min(d for d in have if d[:4] >= usable_year) if usable_year else None
        g["G5"] = dict(coverage_by_year={y: round(v, 3) for y, v in cov.items()}, usable_start=usable_start, passes=bool(usable_start is not None))
        log(f"     G5 coverage vs the equity calendar: " + " ".join(f"{y}:{100*v:.0f}%" for y, v in cov.items()) + f"  -> usable from {usable_start}")
        g["passes"] = all(g[k]["passes"] for k in ("G1", "G2", "G3", "G4", "G5")); ok_all &= g["passes"]; out[root] = g
        log(f"{root}: G1 {g['G1']['n']} bars > {100*G1_THR[root]:.1f}% on days {g['G1']['days'][:12]}{'...' if len(g['G1']['days']) > 12 else ''} {'PASS' if g['G1']['passes'] else 'FAIL'} | G2 rolls {g['G2']['n_rolls']} fwd {g['G2']['forward']} revert {g['G2']['reverting']} multi-per-quarter {g['G2']['quarters_with_more_than_one']} days-before-expiry p50 {g['G2']['days_before_expiry_p50']} [{g['G2']['days_before_expiry_min']},{g['G2']['days_before_expiry_max']}] {'PASS' if g['G2']['passes'] else 'FAIL'} | G3 p50 {g['G3']['p50_bars']:.0f} short {g['G3']['n_short']} (early-close-like {g['G3']['n_early_close_like']}, other {len(g['G3']['other_short'])}) {'PASS' if g['G3']['passes'] else 'FAIL'} | G4 vs {ETF[root]} n {g['G4']['matched_days']} oc {oc:.4f} cc {cc:.4f} {'PASS' if g['G4']['passes'] else 'FAIL'}")
    meta["gates"] = out; meta["all_gates_pass"] = bool(ok_all); META.write_text(json.dumps(meta, indent=1)); log(f"\nALL GATES {'PASS' if ok_all else 'FAIL'}; wrote {META.relative_to(REPO)}")
    return ok_all


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    t0 = time.time(); print("== (a) process_chunk: DST, the RTH window, the 15:59 bar in and 16:00 out, only the four roots' outrights")
    ids = {1: ("ES", "ESH5"), 2: ("ES", "ESM5"), 3: ("NQ", "NQH5")}
    def ts(s):
        return int(pd.Timestamp(s).value)
    rows = [(ts("2015-01-15 14:30:00+00:00"), 1), (ts("2015-01-15 13:30:00+00:00"), 1), (ts("2015-07-15 13:30:00+00:00"), 2), (ts("2015-07-15 19:59:00+00:00"), 2), (ts("2015-07-15 20:00:00+00:00"), 2), (ts("2015-07-15 13:30:00+00:00"), 3), (ts("2015-07-15 13:30:00+00:00"), 9)]
    arr = np.array([(t, i, 2000 * 1e9, 2001 * 1e9, 1999 * 1e9, 2000.5 * 1e9, 100) for t, i in rows], dtype=[("ts_event", "<i8"), ("instrument_id", "<u4"), ("open", "<i8"), ("high", "<i8"), ("low", "<i8"), ("close", "<i8"), ("volume", "<u8")])
    bars, dv = process_chunk(arr, ids); key = set(zip(bars["contract"], bars["day"], bars["hhmm"]))
    assert ("ESH5", "2015-01-15", "09:30") in key and ("ESH5", "2015-01-15", "08:30") not in key, "EST conversion"       # 14:30 UTC in January is 09:30 EST; 13:30 UTC is 08:30
    assert ("ESM5", "2015-07-15", "09:30") in key and ("ESM5", "2015-07-15", "15:59") in key and ("ESM5", "2015-07-15", "16:00") not in key, "EDT / 15:59 in / 16:00 out"
    assert ("NQH5", "2015-07-15", "09:30") in key and not any(c not in ("ESH5", "ESM5", "NQH5") for c in bars["contract"]) and len(bars) == 4
    assert int(dv[(dv["contract"] == "ESM5")]["volume"].sum()) == 300, "day volume counts the 16:00 bar too"
    print("  ok: 4 RTH bars kept of 7 (08:30 EST, 16:00 EDT and the unmapped instrument dropped); DST both ways; full-day volume 300 for ESM5")
    print("== (b) assemble: front by full-day volume, the roll row, p0930/p1600, bars per session")
    b = pd.DataFrame([dict(root="ES", day=d, hhmm=h, contract=c, open=1.0, high=1.0, low=1.0, close=1.0 + k, volume=1) for d in ("2015-03-12", "2015-03-13") for c in ("ESH5", "ESM5") for k, h in enumerate(("09:30", "12:00", "15:59"))])
    dvx = pd.DataFrame([dict(root="ES", day="2015-03-12", contract="ESH5", volume=900), dict(root="ES", day="2015-03-12", contract="ESM5", volume=100), dict(root="ES", day="2015-03-13", contract="ESH5", volume=400), dict(root="ES", day="2015-03-13", contract="ESM5", volume=600)])
    bars2, sess, rolls = assemble(b, dvx); assert list(sess["contract"]) == ["ESH5", "ESM5"] and len(rolls) == 1 and rolls.iloc[0]["to_contract"] == "ESM5" and rolls.iloc[0]["from_volume"] == 400 and list(sess["bars"]) == [3, 3]
    assert sess.iloc[0]["p0930"] == 1.0 and sess.iloc[0]["p1600"] == 3.0 and bool(sess.iloc[1]["roll"]) and not bool(sess.iloc[0]["roll"]) and len(bars2) == 6 and (bars2[bars2["day"] == "2015-03-13"]["contract"] == "ESM5").all()
    print("  ok: front flips to ESM5 on the higher-volume day, one roll row with both volumes, p0930/p1600 from the 09:30 open and 15:59 close")
    print("== (c) expiry arithmetic: third Fridays; single-digit years resolved by the roll year; ESH5 -> 2015-03-20; ESZ9 rolled in 2019 -> 2019-12-20; NQU0 rolled 2020-09 -> 2020-09-18")
    assert str(third_friday(2015, 3).date()) == "2015-03-20" and str(expiry_of("ESH5", "2015-03-12").date()) == "2015-03-20" and str(expiry_of("ESZ9", "2019-12-13").date()) == "2019-12-20" and str(expiry_of("NQU0", "2020-09-11").date()) == "2020-09-18"
    assert str(expiry_of("ESM0", "2010-06-07").date()) == "2010-06-18" and str(expiry_of("ESH1", "2020-12-11").date()) == "2021-03-19", "year wrap"
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
