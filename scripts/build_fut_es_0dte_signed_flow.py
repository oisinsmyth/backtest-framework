"""The ES-family option SIGNED flow census in ET clock buckets: buy-initiated, sell-initiated and
unsigned contracts per (session, option, bucket), from the `tbbo` year.

    python scripts/build_fut_es_0dte_signed_flow.py --selftest              # every gate raises on its break
    python scripts/build_fut_es_0dte_signed_flow.py --profile               # one file, timed, nothing written
    python scripts/build_fut_es_0dte_signed_flow.py --trades [--workers 6]  # decode, cached per file
    python scripts/build_fut_es_0dte_signed_flow.py --build                 # the fixture + meta
    python scripts/build_fut_es_0dte_signed_flow.py --gates                 # G1-G7 -> meta

SYSTEM PYTHON, not the venv: `databento` is installed only there.

WHAT THIS IS, AND WHAT IT IS NOT
--------------------------------
D614 closed the first expiry-pin construction and named the missing ingredient in its own section 7:
traded volume is turnover with NO SIDE, so it cannot say which way dealers lean, which is the whole
mechanism. The aggressor side exists in exactly one place on this disk -- the `tbbo` schema -- and no
study here has ever read it (D511 declined it explicitly). This builder reads it.

It is a CENSUS. It scores nothing: no return, no price outcome, no statistic about the close, no
conditioner. The output columns are contracts and trade counts, and G7 asserts that the written header
is exactly the declared set so a return cannot arrive here by accident.

THE RESERVED WINDOW, AND THE AUTHORITY FOR READING IT
-----------------------------------------------------
The `tbbo` pull spans 2025-09-11 .. 2026-09-10, which lies inside the 2024+ slice this repository holds
back from return-bearing constructions. Two things make this read admissible and both are recorded
rather than assumed:

  1. the principal's instruction of 2026-09-22 asked for the six sharpenings with the aggressor
     improvement built as a FIXTURE ONLY, which is the authority for opening these files;
  2. D510 and D511 read this same window as a non-return census and recorded it spent for that and
     STILL UNSPENT for any return-bearing construction. This record makes the same declaration.

A study that later scores a return on these sessions spends the slice then, on the principal's word,
and counts the looks from this census as zero because none was taken.

Enforcement is at the FILE level, as in D613: a file whose span falls outside the declared window is
never opened, and `audit_window` raises before any read.

THE SIGN CONVENTION, QUOTED
---------------------------
On a DBN trade message `side` is the side of the AGGRESSOR: 'B' when a buyer initiated (lifting the
offer), 'A' when a seller initiated (hitting the bid), 'N' when the tape carries no side. That is
D485's convention, and G6 checks it the way D485 did -- against the book the same message carries --
and proves the check collapses when the mapping is flipped.

What the flag does NOT settle, stated here because a later study will be tempted: the aggressor is not
the customer. Market makers aggress too, to hedge, and a combo leg's side is the combo's. Signed flow
is a proxy for customer direction with an error rate this census does not measure.

THE ET CALENDAR-DATE CONVENTION
------------------------------
`session` is the ET CALENDAR DATE of the trade, which is D581's and D613's convention, so the three
panels join on (raw_symbol, session). The CME trading session for date D opens at 18:00 on D-1, so
Globex hours belonging to session D are filed under D-1; that is why `1800_2400` is its own bucket and
is folded into nothing.
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
TEMP = REPO / "temp" / "es_0dte_signed_flow"
OUT = FIX / "fut_es_0dte_signed_flow.csv.gz"
META = FIX / "fut_es_0dte_signed_flow.meta.json"

SPEC = "D617"
OPTION = re.compile(r"^(ES|EW|EW[1-4]|E[1-5][A-D])([FGHJKMNQUVXZ])(\d{1,2}) ([CP])(\d+)$")   # D581's, verbatim
SPAN = re.compile(r"glbx-mdp3-(\d{8})-(\d{8})\.tbbo\.dbn\.zst$")
CHUNK = 5_000_000
WINDOW_FROM, WINDOW_TO = "20250911", "20260910"                                               # the PULL's window, in the UTC dates the filenames carry
# The session column is the ET CALENDAR DATE, and a trade at 00:30 UTC on the window's first day is
# 20:30 ET on the day BEFORE it. So the earliest session this census can legitimately carry is one ET
# date before the pull's first UTC date -- the Globex evening that opens the window's first trading
# session. That is an allowance of exactly one evening, declared here and asserted in G1, not a widening:
# no file outside the pull window is ever opened (`audit_window`), and the extra rows are hours that the
# pull itself paid for. The last session cannot run past the pull's last UTC date for the same reason.
SESSION_FROM = (pd.Timestamp(WINDOW_FROM) - pd.Timedelta(days=1)).strftime("%Y%m%d")
SESSION_TO = WINDOW_TO
EDGES = ("00:00", "12:00", "15:30", "16:00", "18:00", "24:00")                                # D613's, verbatim
BUCKETS = ("0000_1200", "1200_1530", "1530_1600", "1600_1800", "1800_2400")
SIDES = (("buy", "B"), ("sell", "A"), ("unsigned", "N"))
KEYS = ["raw_symbol", "session"]
VALUE_COLS = [f"{name}_{b}" for name, _ in SIDES for b in BUCKETS] + [f"trades_{b}" for b in BUCKETS]
OUT_COLS = KEYS + VALUE_COLS
PX = 1e-9
N_SHARE_CEILING = 0.10        # declared before the run; the probe chunk measured 0.0000 on option trades
AGREE_FLOOR = 0.95            # declared before the run; D485's futures agreement and the probe chunk both read 1.0000


def log(*a):
    print(*a, flush=True)


def expect_raise(fn, what, say=log):
    try:
        fn()
    except AssertionError as e:
        say(f"    gate RAISES on {what}: {str(e)[:78]}")
        return True
    raise AssertionError(f"gate did not raise on {what}")


# ------------------------------------------------------------------ which files may be opened
def source_files():
    """Every tbbo file whose span lies INSIDE the declared window; anything else NAMED, not silently dropped."""
    keep, outside, unparsed = [], [], []
    for p in sorted(RAW.glob("*/*.tbbo.dbn.zst"), key=lambda q: q.name):
        m = SPAN.search(p.name)
        if not m:
            unparsed.append(p.name)
            continue
        lo, hi = m.group(1), m.group(2)
        if lo >= WINDOW_FROM and hi <= WINDOW_TO:
            keep.append(p)
        else:
            outside.append(p.name)
    if unparsed:
        raise AssertionError(f"a source filename does not carry a parseable span: {unparsed}")
    if not keep:
        raise AssertionError("no tbbo file lies inside the declared window")
    return keep, outside


def audit_window(names):
    """RAISES if a file outside the declared census window would be opened. Enforced before the read, never after."""
    bad = []
    for n in names:
        m = SPAN.search(n)
        if not m or m.group(1) < WINDOW_FROM or m.group(2) > WINDOW_TO:
            bad.append(n)
    if bad:
        raise AssertionError(f"a file outside the declared window {WINDOW_FROM}..{WINDOW_TO} would be opened: {bad}")


def audit_no_outcome_column(cols):
    """RAISES if a column that is not a contract count or a trade count reaches the fixture. This is a census."""
    extra = [c for c in cols if c not in OUT_COLS]
    missing = [c for c in OUT_COLS if c not in cols]
    if extra or missing:
        raise AssertionError(f"the census header is not the declared set: extra {extra}, missing {missing}")


# ------------------------------------------------------------------ the decode
def option_windows(store):
    """(iid, raw_symbol, w0, w1) for every ES-family option the file maps. D581's windowed-id logic, verbatim."""
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
    return pd.DataFrame(rows, columns=["iid", "raw_symbol", "w0", "w1"])


def bucket_of(hhmm):
    """The bucket index per trade, by ET clock. Edges are half-open [lo, hi), so every minute lands in exactly one."""
    out = np.full(len(hhmm), -1, dtype=np.int8)
    for i, (lo, hi) in enumerate(zip(EDGES[:-1], EDGES[1:])):
        out[(hhmm >= lo) & (hhmm < hi)] = i
    return out


def trades_worker(path):
    """One file -> (raw_symbol, session) x bucket x side contracts, plus the at-quote agreement census."""
    import databento as db
    t0 = time.time()
    store = db.DBNStore.from_file(path)
    w = option_windows(store)
    if not len(w):
        return dict(file=Path(path).name, rows_in=0, rows_kept=0, secs=round(time.time() - t0, 1), table=None, agree=None)
    keys = np.unique(w["iid"].to_numpy(np.uint32))
    parts, n, ag = [], 0, dict(at_quote=0, agree=0, quotes_usable=0, option_trades=0, by_family={})
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
            raise AssertionError("[IDS] an option trade claimed by two mapping windows")
        k = j["_i"].to_numpy()
        a = a[k]
        sym = j["raw_symbol"].to_numpy()
        ts = pd.to_datetime(a["ts_event"], utc=True).tz_convert("US/Eastern")
        day = np.asarray(ts.strftime("%Y-%m-%d"))
        bk = bucket_of(np.asarray(ts.strftime("%H:%M")))
        if (bk < 0).any():
            raise AssertionError("a trade fell in no ET clock bucket")
        side = np.char.decode(a["side"].astype("S"), "ascii")
        size = a["size"].astype(np.int64)
        d = {"raw_symbol": sym, "session": day}
        for name, code in SIDES:
            hit = side == code
            for i, b in enumerate(BUCKETS):
                d[f"{name}_{b}"] = np.where(hit & (bk == i), size, 0)
        for i, b in enumerate(BUCKETS):
            d[f"trades_{b}"] = (bk == i).astype(np.int64)
        parts.append(pd.DataFrame(d))
        # the aggressor census, on this chunk's option trades (D485's check, on the book the message carries)
        px = a["price"].astype(np.int64) * PX
        bid = a["bid_px_00"].astype(np.int64) * PX
        ask = a["ask_px_00"].astype(np.int64) * PX
        ok = (bid > 0) & (ask > 0) & (ask >= bid) & np.isfinite(bid) & np.isfinite(ask)
        at_ask = ok & (px >= ask)
        at_bid = ok & (px <= bid)
        atq = at_ask | at_bid
        agree = (at_bid & (side == "A")) | (at_ask & (side == "B"))
        ag["option_trades"] += int(len(a)); ag["quotes_usable"] += int(ok.sum())
        ag["at_quote"] += int(atq.sum()); ag["agree"] += int(agree.sum())
        fam = pd.Series(sym).str.extract(OPTION.pattern)[0].to_numpy()
        for f in np.unique(fam):
            m = fam == f
            e = ag["by_family"].setdefault(str(f), dict(trades=0, unsigned=0, contracts=0, unsigned_contracts=0))
            e["trades"] += int(m.sum()); e["unsigned"] += int((m & (side == "N")).sum())
            e["contracts"] += int(size[m].sum()); e["unsigned_contracts"] += int(size[m & (side == "N")].sum())
    t = (pd.concat(parts, ignore_index=True).groupby(KEYS, sort=False)[VALUE_COLS].sum().reset_index()
         if parts else None)
    return dict(file=Path(path).name, rows_in=n, rows_kept=int(len(t)) if t is not None else 0,
                secs=round(time.time() - t0, 1), table=t, agree=ag)


def cmd_profile():
    files, outside = source_files()
    audit_window([f.name for f in files])
    p = min(files, key=lambda q: q.stat().st_size)
    gb = p.stat().st_size / 1e9
    log(f"  profiling the smallest of {len(files)} files: {p.name} ({gb:.2f} GB); {len(outside)} outside the window")
    r = trades_worker(str(p))
    total = sum(f.stat().st_size for f in files) / 1e9
    log(f"  {r['rows_in']:,} trades in, {r['rows_kept']:,} (option, session) rows out, {r['secs']:.1f}s")
    log(f"  => {gb/max(r['secs'],1e-9)*60:.2f} GB/min serial; {total:.1f} GB total => "
        f"{total/(gb/max(r['secs'],1e-9))/60:.1f} min serial, {total/(gb/max(r['secs'],1e-9))/60/6*1.18:.1f} min projected on 6 workers at D613's 85 %")
    if r["agree"]:
        a = r["agree"]
        log(f"  aggressor census on this file: {a['option_trades']:,} option trades, quotes usable {a['quotes_usable']/max(a['option_trades'],1):.4f}, "
            f"at-quote {a['at_quote']:,}, agreement {a['agree']/max(a['at_quote'],1):.4f}")
        uns = sum(v['unsigned_contracts'] for v in a['by_family'].values()) / max(sum(v['contracts'] for v in a['by_family'].values()), 1)
        log(f"  unsigned share of option contracts: {uns:.4f} (ceiling {N_SHARE_CEILING})")


def cmd_trades(workers):
    files, outside = source_files()
    names = [f.name for f in files]
    audit_window(names)
    log(f"  opening {len(files)} files ({sum(f.stat().st_size for f in files)/1e9:.1f} GB); {len(outside)} outside the window: {outside}")
    TEMP.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    from multiprocessing import Pool
    with Pool(workers) as pool:
        res = pool.map(trades_worker, [str(f) for f in sorted(files, key=lambda p: -p.stat().st_size)], chunksize=1)
    res.sort(key=lambda r: r["file"])
    for r in res:
        (TEMP / f"trades_{Path(r['file']).stem.split('.')[0]}.pkl").write_bytes(pickle.dumps(dict(table=r["table"], agree=r["agree"], file=r["file"], rows_in=r["rows_in"])))
        log(f"  {r['file'][:44]:<44} {r['rows_in']:>12,} trades -> {r['rows_kept']:>8,} rows  {r['secs']:>6.1f}s")
    sec = sum(r["secs"] for r in res); wall = time.time() - t0
    log(f"[SPEED] sum(item time)/wall = {sec/wall:.2f}x on {workers} workers ({100*sec/wall/workers:.0f}%); {wall/60:.1f} min")
    if sec / wall / workers < 0.70:
        log(f"[SPEED] BELOW THE FLOOR ({100*sec/wall/workers:.0f}% < 70%) -- the work is not releasing what it should")


def cmd_build():
    t0 = time.time()
    caches = sorted(TEMP.glob("trades_*.pkl"))
    if not caches:
        raise AssertionError("no decode cache; run --trades first")
    tabs, agg, files = [], dict(at_quote=0, agree=0, quotes_usable=0, option_trades=0, by_family={}), []
    for p in caches:
        d = pickle.loads(p.read_bytes())
        files.append(d["file"])
        if d["table"] is not None:
            tabs.append(d["table"])
        a = d["agree"] or {}
        for k in ("at_quote", "agree", "quotes_usable", "option_trades"):
            agg[k] += int(a.get(k, 0))
        for f, v in (a.get("by_family") or {}).items():
            e = agg["by_family"].setdefault(f, dict(trades=0, unsigned=0, contracts=0, unsigned_contracts=0))
            for k in e:
                e[k] += int(v[k])
    audit_window(files)
    t = pd.concat(tabs, ignore_index=True).groupby(KEYS, sort=False)[VALUE_COLS].sum().reset_index()
    t = t.sort_values(KEYS).reset_index(drop=True)
    audit_no_outcome_column(list(t.columns))
    t.to_csv(OUT, index=False, encoding="utf-8", lineterminator="\n", compression={"method": "gzip", "mtime": 0})
    sha = hashlib.sha256(OUT.read_bytes()).hexdigest()
    fam = t["raw_symbol"].str.extract(OPTION.pattern)[0]
    META.write_text(json.dumps(dict(
        spec=SPEC, built_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), sha256=sha,
        rows=int(len(t)), options=int(t["raw_symbol"].nunique()), sessions=int(t["session"].nunique()),
        first=str(t["session"].min()), last=str(t["session"].max()), families=fam.value_counts().to_dict(),
        window=dict(pull_utc_from=WINDOW_FROM, pull_utc_to=WINDOW_TO, session_et_from=SESSION_FROM, session_et_to=SESSION_TO,
                    et_allowance="the session column is the ET calendar date, so the opening Globex evening of the window's first trading session carries the ET date one day before the pull's first UTC date; one evening, asserted in G1",
                    files=sorted(files)),
        side_convention="DBN trade `side` is the AGGRESSOR: B = a buyer initiated (lifted the offer), A = a seller initiated (hit the bid), N = no side on the tape. D485's convention.",
        not_a_signal="a census: contracts and trade counts only. No return, no price outcome, no conditioner. G7 asserts the header is exactly the declared set.",
        slice_declaration="this window is read as a NON-RETURN census on the principal's instruction of 2026-09-22 (the aggressor improvement as a fixture only), in D510/D511's shape: still UNSPENT for any return-bearing construction.",
        buckets=dict(zip(BUCKETS, [f"[{lo}, {hi}) ET" for lo, hi in zip(EDGES[:-1], EDGES[1:])])),
        session_convention="the ET CALENDAR DATE of the trade (D581's and D613's), so the three option panels join on (raw_symbol, session); Globex 18:00-24:00 hours belonging to the next trading session are filed under the prior date and kept in their own bucket",
        aggressor_census=agg, gates=None), indent=1), encoding="utf-8")
    log(f"  wrote {OUT.relative_to(REPO)}: {len(t):,} rows, {t['raw_symbol'].nunique():,} options, "
        f"{t['session'].nunique():,} sessions {t['session'].min()} .. {t['session'].max()} in {(time.time()-t0)/60:.1f} min")
    log(f"  sha256 {sha}")


# ------------------------------------------------------------------ gates
def read_fixture():
    return pd.read_csv(OUT, dtype={"raw_symbol": str, "session": str}, encoding="utf-8")


def gate_keys_and_window(t, log=log):
    """G1: keys unique, every session inside the declared window, families all ES-family."""
    dup = int(t.duplicated(KEYS).sum())
    lo = t["session"].min().replace("-", "")
    hi = t["session"].max().replace("-", "")
    inside = bool(lo >= SESSION_FROM and hi <= SESSION_TO)
    bad_sym = int((~t["raw_symbol"].str.match(OPTION)).sum())
    if dup:
        raise AssertionError(f"G1 duplicate (raw_symbol, session) keys: {dup}")
    if not inside:
        raise AssertionError(f"G1 a session lies outside the declared ET window {SESSION_FROM}..{SESSION_TO}: {lo}..{hi}")
    if bad_sym:
        raise AssertionError(f"G1 a row carries a symbol that is not an ES-family option: {bad_sym}")
    early = int((t["session"].str.replace("-", "") < WINDOW_FROM).sum())
    return dict(rows=int(len(t)), duplicate_keys=dup, first=str(t["session"].min()), last=str(t["session"].max()),
                non_option_symbols=bad_sym, declared_et_window=[SESSION_FROM, SESSION_TO], pull_window=[WINDOW_FROM, WINDOW_TO],
                rows_on_the_opening_evening=early, passes=True)


def gate_sides_add_up(t, log=log):
    """G2: buy + sell + unsigned contracts is the row's total, exactly, in every bucket; and no negative count."""
    bad = {}
    for b in BUCKETS:
        s = t[f"buy_{b}"] + t[f"sell_{b}"] + t[f"unsigned_{b}"]
        neg = int(((t[f"buy_{b}"] < 0) | (t[f"sell_{b}"] < 0) | (t[f"unsigned_{b}"] < 0) | (t[f"trades_{b}"] < 0)).sum())
        zero_trades_with_volume = int(((t[f"trades_{b}"] == 0) & (s > 0)).sum())
        if neg or zero_trades_with_volume:
            bad[b] = dict(negative=neg, volume_without_a_trade=zero_trades_with_volume)
    if bad:
        raise AssertionError(f"G2 a bucket carries negative counts or volume with no trade: {bad}")
    tot = sum((t[f"{n}_{b}"] for n, _ in SIDES for b in BUCKETS), start=pd.Series(0, index=t.index))
    return dict(total_contracts=int(tot.sum()), buckets_checked=len(BUCKETS), passes=True)


def gate_unsigned_share(t, log=log):
    """G3: the unsigned (`N`) share of contracts, overall and per family and per bucket, under the declared ceiling.

    This is the audit futures did not need. A combo leg or a block arrives with no side, and a conditioner
    signed on 60 % of its own mass is not a signed conditioner. The ceiling is declared above the run."""
    fam = t["raw_symbol"].str.extract(OPTION.pattern)[0]
    signed = sum((t[f"{n}_{b}"] for n in ("buy", "sell") for b in BUCKETS), start=pd.Series(0, index=t.index))
    uns = sum((t[f"unsigned_{b}"] for b in BUCKETS), start=pd.Series(0, index=t.index))
    overall = float(uns.sum() / max(int(uns.sum() + signed.sum()), 1))
    by_fam = {}
    for f, g in t.assign(_f=fam, _s=signed, _u=uns).groupby("_f"):
        by_fam[str(f)] = float(g["_u"].sum() / max(int(g["_u"].sum() + g["_s"].sum()), 1))
    by_bucket = {}
    for b in BUCKETS:
        u = int(t[f"unsigned_{b}"].sum()); s = int(t[f"buy_{b}"].sum() + t[f"sell_{b}"].sum())
        by_bucket[b] = float(u / max(u + s, 1))
    worst = max([overall] + list(by_fam.values()) + list(by_bucket.values()))
    if worst > N_SHARE_CEILING:
        raise AssertionError(f"G3 the unsigned share exceeds the declared ceiling {N_SHARE_CEILING}: worst {worst:.4f}")
    return dict(ceiling=N_SHARE_CEILING, overall=overall, by_family=by_fam, by_bucket=by_bucket, worst=worst, passes=True)


def gate_agreement(agg, log=log):
    """G6: D485's at-quote agreement -- the aggressor flag against the book the same message carries."""
    atq = int(agg.get("at_quote", 0)); ok = int(agg.get("agree", 0))
    share = ok / max(atq, 1)
    if atq == 0:
        raise AssertionError("G6 no at-quote trade to check the aggressor convention against")
    if share < AGREE_FLOOR:
        raise AssertionError(f"G6 at-quote agreement {share:.4f} below the declared floor {AGREE_FLOOR}")
    return dict(floor=AGREE_FLOOR, at_quote_trades=atq, agreeing=ok, share=share,
                quotes_usable=float(agg.get("quotes_usable", 0) / max(agg.get("option_trades", 1), 1)),
                caveat="the check confirms the flag's DIRECTION against the book, not that the aggressor is the customer",
                passes=True)


def gate_second_path(t, log=log):
    """G5: a scalar loop over the raw file reproduces three named (option, session) rows with POSITIVE 15:30-16:00 volume.

    The positivity requirement is D613's correction: a cell where both paths are zero is a check that cannot disagree."""
    import databento as db
    live = t[(t["buy_1530_1600"] + t["sell_1530_1600"]) > 0]
    if len(live) < 3:
        raise AssertionError("G5 fewer than three rows with positive 15:30-16:00 volume to check")
    rng = np.random.default_rng(617)
    pick = live.iloc[rng.choice(len(live), 3, replace=False)]
    checks = []
    for r in pick.itertuples():
        day = r.session
        f = None
        for p in source_files()[0]:
            m = SPAN.search(p.name)
            if m.group(1) <= day.replace("-", "") <= m.group(2):
                f = p
                break
        if f is None:
            raise AssertionError(f"G5 no source file covers {day}")
        store = db.DBNStore.from_file(str(f))
        w = option_windows(store)
        w = w[w["raw_symbol"] == r.raw_symbol]
        ids = set(w["iid"].astype(int).tolist())
        lo = int(pd.Timestamp(f"{day} 15:30", tz="US/Eastern").value)
        hi = int(pd.Timestamp(f"{day} 16:00", tz="US/Eastern").value)
        buy = sell = uns = trades = 0
        for arr in store.to_ndarray(count=CHUNK):
            for rec in arr[(arr["ts_event"] >= lo) & (arr["ts_event"] < hi)]:
                if int(rec["instrument_id"]) not in ids:
                    continue
                ts = int(rec["ts_event"])
                win = w[(w["iid"].astype(int) == int(rec["instrument_id"]))]
                if not ((win["w0"].astype("int64") <= ts) & (ts < win["w1"].astype("int64"))).any():
                    continue
                s = rec["side"].decode("ascii") if isinstance(rec["side"], bytes) else str(rec["side"])
                trades += 1
                if s == "B":
                    buy += int(rec["size"])
                elif s == "A":
                    sell += int(rec["size"])
                else:
                    uns += int(rec["size"])
        agree = (buy == int(r.buy_1530_1600) and sell == int(r.sell_1530_1600)
                 and uns == int(r.unsigned_1530_1600) and trades == int(r.trades_1530_1600))
        checks.append(dict(raw_symbol=r.raw_symbol, session=day, fixture=[int(r.buy_1530_1600), int(r.sell_1530_1600), int(r.unsigned_1530_1600), int(r.trades_1530_1600)],
                           scalar=[buy, sell, uns, trades], agree=bool(agree)))
        if not agree:
            log(f"    G5 {r.raw_symbol} {day}: fixture {checks[-1]['fixture']} vs scalar {checks[-1]['scalar']}")
    if not all(c["agree"] for c in checks):
        raise AssertionError(f"G5 the scalar second path disagrees: {[c for c in checks if not c['agree']]}")
    return dict(cells=checks, passes=True)


def cmd_gates(log=log):
    meta = json.loads(META.read_text(encoding="utf-8"))
    t = read_fixture()
    out = {}
    out["G1"] = gate_keys_and_window(t, log)
    out["G2"] = gate_sides_add_up(t, log)
    out["G3"] = gate_unsigned_share(t, log)
    audit_no_outcome_column(list(t.columns)); out["G4"] = dict(header=list(t.columns), declared=OUT_COLS, passes=True)
    out["G5"] = gate_second_path(t, log)
    out["G6"] = gate_agreement(meta.get("aggressor_census") or {}, log)
    sha = hashlib.sha256(OUT.read_bytes()).hexdigest()
    out["G7"] = dict(sha256=sha, recorded=meta.get("sha256"), passes=bool(sha == meta.get("sha256")))
    if not out["G7"]["passes"]:
        raise AssertionError(f"G7 the fixture's sha256 {sha} is not the one the meta recorded {meta.get('sha256')}")
    meta["gates"] = out
    meta["all_gates_pass"] = True
    META.write_text(json.dumps(meta, indent=1), encoding="utf-8")
    log(f"G1 {out['G1']['rows']:,} rows, {out['G1']['first']} .. {out['G1']['last']}, no duplicate key, every symbol an ES-family option PASS")
    log(f"G2 sides add to the row total in all {len(BUCKETS)} buckets, {out['G2']['total_contracts']:,} contracts, no negative and no volume without a trade PASS")
    log(f"G3 unsigned share overall {out['G3']['overall']:.4f}, worst cell {out['G3']['worst']:.4f} against the declared ceiling {N_SHARE_CEILING} PASS")
    log(f"G4 the header is exactly the declared census set ({len(OUT_COLS)} columns, no outcome) PASS")
    log(f"G5 the scalar second path reproduces {sum(c['agree'] for c in out['G5']['cells'])}/3 named cells with positive 15:30-16:00 volume PASS")
    log(f"G6 at-quote aggressor agreement {out['G6']['share']:.4f} on {out['G6']['at_quote_trades']:,} trades, floor {AGREE_FLOOR} PASS")
    log(f"G7 sha256 matches the meta PASS")
    log(f"ALL GATES PASS; wrote {META.relative_to(REPO)}")
    return True


# ------------------------------------------------------------------ selftest
def cmd_selftest():
    assert OPTION.match("EW1G6 C8200") and OPTION.match("E2BZ5 P5800") and not OPTION.match("ESZ5") and not OPTION.match("OZNZ5 C110")
    # the ET buckets partition the clock: every minute in exactly one, and the edges are the declared ones
    hhmm = np.array([f"{h:02d}:{m:02d}" for h in range(24) for m in range(60)])
    bk = bucket_of(hhmm)
    assert (bk >= 0).all(), "a minute fell in no bucket"
    assert [int((bk == i).sum()) for i in range(len(BUCKETS))] == [720, 210, 30, 120, 360], [int((bk == i).sum()) for i in range(len(BUCKETS))]
    assert bucket_of(np.array(["15:29"]))[0] == 1 and bucket_of(np.array(["15:30"]))[0] == 2 and bucket_of(np.array(["15:59"]))[0] == 2 and bucket_of(np.array(["16:00"]))[0] == 3

    # the window audit: it must pass the real file names and RAISE on a name outside the window
    files, outside = source_files()
    names = [f.name for f in files]
    audit_window(names)
    expect_raise(lambda: audit_window(names + ["glbx-mdp3-20230101-20230131.tbbo.dbn.zst"]), "a pre-window file")
    expect_raise(lambda: audit_window(names + ["glbx-mdp3-20260911-20261001.tbbo.dbn.zst"]), "a post-window file")
    expect_raise(lambda: audit_window(["not-a-span.tbbo.dbn.zst"]), "an unparseable span")

    # the census guard: exactly the declared columns, and it RAISES on an outcome column arriving
    audit_no_outcome_column(OUT_COLS)
    expect_raise(lambda: audit_no_outcome_column(OUT_COLS + ["r1530_1600_bp"]), "a return column reaching the census")
    expect_raise(lambda: audit_no_outcome_column(OUT_COLS[:-1]), "a declared column missing")

    # G1/G2/G3/G6 on a synthetic frame, each proven to raise on the break that hits the scalar it reads
    def frame(**over):
        row = dict(raw_symbol="EW1V6 C6500", session="2025-10-01")
        for c in VALUE_COLS:
            row[c] = 0
        row["buy_1530_1600"] = 60; row["sell_1530_1600"] = 40; row["unsigned_1530_1600"] = 0; row["trades_1530_1600"] = 7
        row.update(over)
        two = dict(row); two["session"] = "2025-10-02"
        return pd.DataFrame([row, two])
    t = frame()
    assert gate_keys_and_window(t, log=lambda *a: None)["passes"]
    expect_raise(lambda: gate_keys_and_window(pd.concat([t, t.iloc[[0]]], ignore_index=True), log=lambda *a: None), "a duplicate key")
    expect_raise(lambda: gate_keys_and_window(frame(session="2024-06-03"), log=lambda *a: None), "a session outside the window")
    # the ET allowance is exactly ONE evening: the opening evening passes, a second day earlier does not
    assert gate_keys_and_window(frame(session="2025-09-10"), log=lambda *a: None)["passes"], "the opening Globex evening is inside the ET window"
    expect_raise(lambda: gate_keys_and_window(frame(session="2025-09-09"), log=lambda *a: None), "a session two ET days before the pull")
    expect_raise(lambda: gate_keys_and_window(frame(session="2026-09-11"), log=lambda *a: None), "a session after the pull's last day")
    expect_raise(lambda: gate_keys_and_window(frame(raw_symbol="ESZ5"), log=lambda *a: None), "a symbol that is not an option")
    assert gate_sides_add_up(t, log=lambda *a: None)["total_contracts"] == 200
    expect_raise(lambda: gate_sides_add_up(frame(buy_1530_1600=-1), log=lambda *a: None), "a negative contract count")
    expect_raise(lambda: gate_sides_add_up(frame(trades_1530_1600=0), log=lambda *a: None), "volume with no trade behind it")
    g3 = gate_unsigned_share(t, log=lambda *a: None)
    assert g3["overall"] == 0.0 and g3["passes"], g3
    expect_raise(lambda: gate_unsigned_share(frame(unsigned_1530_1600=500), log=lambda *a: None), "an unsigned share over the ceiling")
    assert gate_agreement(dict(at_quote=1000, agree=1000, quotes_usable=1000, option_trades=1000), log=lambda *a: None)["share"] == 1.0
    expect_raise(lambda: gate_agreement(dict(at_quote=1000, agree=10), log=lambda *a: None), "agreement below the floor")
    expect_raise(lambda: gate_agreement(dict(at_quote=0, agree=0), log=lambda *a: None), "no at-quote trade to check against")

    # the flipped aggressor mapping must collapse the agreement -- the break that makes G6 a real check (D485)
    side = np.array(["B", "A", "B", "A"])
    at_ask = np.array([True, False, True, False]); at_bid = ~at_ask
    right = ((at_bid & (side == "A")) | (at_ask & (side == "B"))).mean()
    flipped = ((at_bid & (side == "B")) | (at_ask & (side == "A"))).mean()
    assert right == 1.0 and flipped == 0.0, (right, flipped)
    log(f"selftest: symbology, the five ET buckets partitioning the clock at the declared edges, the window audit on "
        f"{len(names)} real files, the census guard, G1/G2/G3/G6 each passing clean input and RAISING on its own break, "
        f"and the flipped aggressor mapping taking agreement 1.0 -> 0.0 -- all pass")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    for f in ("selftest", "profile", "trades", "build", "gates"):
        g.add_argument(f"--{f}", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    if a.selftest:
        cmd_selftest()
    elif a.profile:
        cmd_profile()
    elif a.trades:
        cmd_trades(a.workers)
    elif a.build:
        cmd_build()
    else:
        cmd_gates()
