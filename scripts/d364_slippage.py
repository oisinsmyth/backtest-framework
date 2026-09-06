"""D364 SLIPPAGE -- what a hand-filled fill log says about the gap between a modelled print and a real one.

    uv run python scripts/d364_slippage.py                    data/d364_fill_log.csv
    uv run python scripts/d364_slippage.py --log PATH         elsewhere
    uv run python scripts/d364_slippage.py --selftest         the synthetic case, both signs, and the empty path

THIS IS A MEASUREMENT INSTRUMENT, NOT A TRADING SYSTEM. It reads fills the principal obtained by placing orders
themselves, joins each to the daily fixture's own print for the same (symbol, date), and reports the difference.
Nothing here is a result, nothing here is a book entry (R8), and nothing here places an order.

WHAT IT MEASURES
----------------
Every cost line in this programme charges a MODELLED half-spread (D363's PUB / PB, Corwin-Schultz off the OHLC)
against a print taken from the daily fixture. Nothing has ever measured the distance between that print and a
price actually obtainable at the open or the close. `fill_price - the day's official print, in bp` is that
distance, and it is the one number this file exists to produce.

THE SIGN CONVENTION, WHICH IS THE WHOLE THING
---------------------------------------------
**POSITIVE = THE FILL WAS WORSE FOR THE STRATEGY.**

    short_entry  sells to open.  A HIGHER sell is better, so filled BELOW the print is worse:  slip = (print - fill) / print
    cover_exit   buys to close.  A LOWER buy is better, so filled ABOVE the print is worse:    slip = (fill - print) / print

i.e. slip_bp = SIDE_SIGN[side] * (fill - print) / print * 1e4 with SIDE_SIGN = {short_entry: -1, cover_exit: +1}.
A sign asserted in prose inverted D280, so it is asserted here in money on both sides ([SIGN]) and the audit is
itself checked to RAISE under a flipped convention ([6]) -- a self-test that cannot fail is worse than none.

WHICH PRINT
-----------
`intended_print` decides it and is not renegotiable after the fact: an MOO fill is measured against the day's
OPEN, an MOC against the day's CLOSE. Scoring an MOO against the close manufactures a slippage number out of the
day's drift.

THE PRICE FRAME: AS-TRADED
--------------------------
`data/fixtures/us_shorts_daily_raw.csv.gz` is SPLIT-ADJUSTED (its meta says so, and D361's [FIX] asserts its
open / close equal the prep's adjusted CLOSE grid bit-identically). A hand-filled log records what the principal
actually paid, so the join is done in the AS-TRADED frame:

    as-traded close(t, i) = P['RAW_CLOSE'][t, i]                (= CLOSE * RAW, the prep's own product)
    as-traded open (t, i) = fixture_open(t, i) * P['RAW'][t, i]  (the D361 export's price_open_entry, exactly)

the fixture read being `d361_export_trades.stream_bars` -- the same reader behind that export's [FIX] pass,
imported rather than re-written. [JOIN] asserts fixture_close * RAW == RAW_CLOSE exactly on every joined row.

NOTE THE BP IS FRAME-INVARIANT and the notional is not: a ratio (fill - print) / print is unchanged by a common
split factor, so the headline slippage would be identical in the adjusted frame. What the frame buys is a
readable print beside it and a correct `shares x fill_price` notional for the commission line.

BESIDE IT, D363's COST LINES
----------------------------
`half_spread_PUB_bp` and `half_spread_PB_bp` at the same (symbol, date), read from the prep's own HALF grids --
what the model CHARGED at that bar, so a measured fill can be read against it. A fill inside the modelled
half-spread is a fill the cost model already paid for.

EMPTY LOG
---------
The committed log has a header and no data rows, which is the honest state until orders are placed. On an empty
log this prints the schema, says nothing is recorded, and EXITS 0 -- it does not load the prep, does not open the
fixture, and does not report a mean of nothing.

ASSERTIONS: [SIGN] [JOIN] [EMPTY] [6].
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]

# ------------------------------------------------------------------ the holdout guard, before any module of the chain loads
_OPENED = dict(n=0, refused=0)


def _audit(event, args):
    if event != "open":
        return
    p = args[0]
    if isinstance(p, bytes):
        p = p.decode(errors="replace")
    elif not isinstance(p, (str, os.PathLike)):
        return
    low = os.fspath(p).replace("\\", "/").lower()
    _OPENED["n"] += 1
    if "holdout" in low:
        _OPENED["refused"] += 1
        raise RuntimeError(f"[HOLDOUT-GUARD] refused to open {os.fspath(p)}")


sys.addaudithook(_audit)

sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

LOG = REPO / "data" / "d364_fill_log.csv"
EXPORT_CSV = REPO / "data" / "d361_trades_gap_up_fade.csv"

# The schema, in file order. (name, required, kind, allowed)
SCHEMA = (
    ("date",           True,  "date",   None),
    ("symbol",         True,  "str",    None),
    ("side",           True,  "enum",   ("short_entry", "cover_exit")),
    ("intended_print", True,  "enum",   ("open", "close")),
    ("order_type",     True,  "enum",   ("MOO", "MOC", "LMT", "MKT")),
    ("shares",         True,  "int+",   None),
    ("limit_price",    False, "float+", None),
    ("fill_price",     True,  "float+", None),
    ("fill_time",      False, "time",   None),
    ("venue",          False, "str",    None),
    ("commission_usd", False, "float0", None),
    ("note",           False, "str",    None),
)
COLS = tuple(c[0] for c in SCHEMA)

# THE CONVENTION. Positive = worse for the strategy.
SIDE_SIGN = {"short_entry": -1.0, "cover_exit": +1.0}
PRINT_OF = {"open": 0, "close": 1}          # index into the (open, close) pair the book stores


# ------------------------------------------------------------------ the log
def read_log(path):
    """The log as a list of dicts with typed values. Raises SystemExit on a malformed header or cell -- a fill log
    that half-parses is worse than one that refuses."""
    path = Path(path)
    if not path.exists():
        raise SystemExit(f"no such log: {path}")
    with open(path, encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f)
        try:
            head = next(r)
        except StopIteration:
            raise SystemExit(f"{path.name}: the file is empty; it must carry the header row")
        raw = [x for x in r if any(c.strip() for c in x)]
    head = [h.strip() for h in head]
    if tuple(head) != COLS:
        raise SystemExit(f"{path.name}: header is\n  {head}\nexpected\n  {list(COLS)}")
    out = []
    for k, x in enumerate(raw, start=2):
        if len(x) != len(COLS):
            raise SystemExit(f"{path.name} line {k}: {len(x)} fields, expected {len(COLS)}")
        rec = {"_line": k}
        for (name, req, kind, allowed), cell in zip(SCHEMA, x):
            v = cell.strip()
            if v == "":
                if req:
                    raise SystemExit(f"{path.name} line {k}: {name} is required and is blank")
                rec[name] = None
                continue
            rec[name] = _coerce(path.name, k, name, kind, allowed, v)
        if rec["order_type"] == "LMT" and rec["limit_price"] is None:
            raise SystemExit(f"{path.name} line {k}: order_type LMT with no limit_price")
        if rec["order_type"] != "LMT" and rec["limit_price"] is not None:
            raise SystemExit(f"{path.name} line {k}: limit_price on a {rec['order_type']} order")
        out.append(rec)
    return out


def _coerce(fname, k, name, kind, allowed, v):
    where = f"{fname} line {k}: {name}={v!r}"
    if kind == "enum":
        if v not in allowed:
            raise SystemExit(f"{where} is not one of {list(allowed)}")
        return v
    if kind == "str":
        return v
    if kind == "date":
        if len(v) != 10 or v[4] != "-" or v[7] != "-" or not (v[:4] + v[5:7] + v[8:]).isdigit():
            raise SystemExit(f"{where} is not YYYY-MM-DD")
        return v
    if kind == "time":
        p = v.split(":")
        if len(p) != 3 or not all(q.isdigit() for q in p) or not (0 <= int(p[0]) < 24 and 0 <= int(p[1]) < 60 and 0 <= int(p[2]) < 61):
            raise SystemExit(f"{where} is not HH:MM:SS (US/Eastern)")
        return v
    try:
        x = float(v)
    except ValueError:
        raise SystemExit(f"{where} is not a number")
    if kind == "int+":
        if x != int(x) or x <= 0:
            raise SystemExit(f"{where} must be a positive whole number of shares")
        return int(x)
    if not np.isfinite(x):
        raise SystemExit(f"{where} is not finite")
    if kind == "float+" and x <= 0:
        raise SystemExit(f"{where} must be > 0")
    if kind == "float0" and x < 0:
        raise SystemExit(f"{where} must be >= 0")
    return x


def print_schema():
    print("  SCHEMA (data/d364_fill_log.README.md carries the types in full)")
    for name, req, kind, allowed in SCHEMA:
        note = "required" if req else "optional"
        if allowed:
            note += " | " + " | ".join(allowed)
        elif kind == "date":
            note += " | YYYY-MM-DD"
        elif kind == "time":
            note += " | HH:MM:SS US/Eastern"
        elif kind == "int+":
            note += " | positive integer"
        elif kind == "float+":
            note += " | float > 0"
        elif kind == "float0":
            note += " | float >= 0"
        print(f"    {name:16}{note}")


# ------------------------------------------------------------------ the sign
def slip_bp(side, fill, print_px, sign=None):
    """The realised fill minus the intended print in bp, POSITIVE = WORSE FOR THE STRATEGY."""
    s = (sign or SIDE_SIGN)[side]
    return s * (fill - print_px) / print_px * 1e4


def assert_SIGN(sign=None, tag="[SIGN]"):
    """In money, on both sides, on a probe whose direction is not in doubt:
       a short entry filled 50 bp BELOW a $100 open is 50 bp WORSE (positive);
       a short entry filled 50 bp ABOVE it is 50 bp BETTER (negative);
       a cover filled 20 bp ABOVE a $50 close is 20 bp WORSE (positive);
       a cover filled 20 bp BELOW it is 20 bp BETTER (negative).
    Every one of the four is checked, so a flipped mapping cannot pass on the strength of one side."""
    checks = (("short_entry", 99.50, 100.00, +50.0), ("short_entry", 100.50, 100.00, -50.0),
              ("cover_exit",  50.10,  50.00, +20.0), ("cover_exit",   49.90,  50.00, -20.0))
    for side, fill, px, want in checks:
        got = slip_bp(side, fill, px, sign)
        assert abs(got - want) < 1e-9, f"{tag} {side} fill {fill} vs print {px}: {got:+.6f} bp, expected {want:+.6f}"
    return ("positive = the fill was WORSE for the strategy. short_entry filled BELOW the intended print is worse "
            "(sold cheap); cover_exit filled ABOVE it is worse (bought dear). "
            "slip_bp = SIDE_SIGN[side] x (fill - print) / print x 1e4, SIDE_SIGN = {short_entry: -1, cover_exit: +1}")


def assert_6(tag="[6]"):
    """The sign audit must RAISE on a deliberately flipped convention. An audit that cannot fail is not an audit."""
    flipped = {k: -v for k, v in SIDE_SIGN.items()}
    try:
        assert_SIGN(flipped)
    except AssertionError as exc:
        return str(exc)[:150]
    raise AssertionError(f"{tag} the sign audit PASSED under a flipped convention -- it checks nothing")


# ------------------------------------------------------------------ the join
def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def prints_from_fixture(keys, verbose=True):
    """{(symbol, date): dict(open, close, PUB, PB)} in the AS-TRADED frame, for the wanted keys only.

    open  = the fixture's own (split-adjusted) open x P['RAW']  -- the D361 export's price_open_entry, exactly
    close = P['RAW_CLOSE']                                      -- the D361 export's price_close_g, exactly
    PUB / PB = P['HALF'][cv], D363's cost lines at the same bar (bp per side).

    [JOIN] asserts fixture_close x RAW == RAW_CLOSE on every joined key, so the two independent reads of the
    same bar (the streamed fixture and the prep's grid) are proved to be the same bar before anything is scored.
    """
    import memo_load
    memo_load.install()
    PREP = _load("d348p", "d348_prep.py")
    EXP = _load("d361x", "d361_export_trades.py")
    P = PREP.prep(need_grids=True, verbose=verbose)
    ti = {d: t for t, d in enumerate(P["dates"])}
    si = {s: i for i, s in enumerate(P["symbols"])}
    RAW, RAW_CLOSE, CLOSE = np.asarray(P["RAW"]), np.asarray(P["RAW_CLOSE"]), np.asarray(P["CLOSE"])
    HALF = {cv: np.asarray(P["HALF"][cv]) for cv in ("PUB", "PB")}
    want = {k for k in keys if k[0] in si and k[1] in ti}
    bars = EXP.stream_bars(want) if want else {}
    book, miss = {}, []
    for k in sorted(keys):
        s, d = k
        if k not in want or k not in bars:
            miss.append((k, "symbol not in the fixture universe" if s not in si else
                         ("date is not a fixture session" if d not in ti else "no bar for that name on that session")))
            continue
        t, i = ti[d], si[s]
        o_adj, _hi, _lo, c_adj, _v = bars[k]
        assert c_adj * RAW[t, i] == RAW_CLOSE[t, i], \
            f"[JOIN] {s} {d}: streamed close {c_adj!r} x RAW {RAW[t, i]!r} != the prep's RAW_CLOSE {RAW_CLOSE[t, i]!r}"
        assert c_adj == CLOSE[t, i], f"[JOIN] {s} {d}: streamed close != the prep's adjusted CLOSE"
        book[k] = dict(open=float(o_adj * RAW[t, i]), close=float(RAW_CLOSE[t, i]),
                       PUB=float(HALF["PUB"][t, i]), PB=float(HALF["PB"][t, i]),
                       adj_open=float(o_adj), adj_close=float(c_adj), raw_factor=float(RAW[t, i]))
    return book, miss, dict(n_keys=len(keys), n_joined=len(book), fixture=Path(EXP.FIXTURE).name,
                            frame="as-traded (fixture open x RAW; RAW_CLOSE)")


def assert_JOIN_against_export(book, tag="[JOIN]"):
    """A second, independent check of the same join: for any joined key that also appears in the committed D361
    export, the as-traded open at date_entry must equal that row's `price_open_entry` and the as-traded close at
    date_g must equal its `price_close_g` -- to the character, off a file this script did not write."""
    if not EXPORT_CSV.exists() or not book:
        return None
    keys = set(book)
    hits = 0
    with open(EXPORT_CSV, encoding="utf-8", newline="") as f:
        r = csv.reader(f)
        head = next(r)
        c = {k: head.index(k) for k in ("symbol", "date_g", "date_entry", "price_open_entry", "price_close_g")}
        for x in r:
            s = x[c["symbol"]]
            ke, kg = (s, x[c["date_entry"]]), (s, x[c["date_g"]])
            if ke in keys:
                mine, theirs = book[ke]["open"], float(x[c["price_open_entry"]])
                assert mine == theirs, f"{tag} {ke}: as-traded open {mine!r} != the export's price_open_entry {theirs!r}"
                hits += 1
            if kg in keys:
                mine, theirs = book[kg]["close"], float(x[c["price_close_g"]])
                assert mine == theirs, f"{tag} {kg}: as-traded close {mine!r} != the export's price_close_g {theirs!r}"
                hits += 1
    return hits


# ------------------------------------------------------------------ the report
def score(rows, book):
    """Per row: the print, the slippage in bp, the commission in bp of notional, and D363's two cost lines."""
    out, unjoined = [], []
    for rec in rows:
        k = (rec["symbol"], rec["date"])
        b = book.get(k)
        if b is None:
            unjoined.append(rec)
            continue
        px = b["close"] if rec["intended_print"] == "close" else b["open"]
        notional = rec["shares"] * rec["fill_price"]
        comm = rec["commission_usd"]
        out.append(dict(rec, print_px=px, slip_bp=slip_bp(rec["side"], rec["fill_price"], px),
                        notional=notional, comm_bp=(None if comm is None else comm / notional * 1e4),
                        PUB=b["PUB"], PB=b["PB"]))
    return out, unjoined


def stats(vals):
    a = np.asarray(vals, float)
    if a.size == 0:
        return None
    return dict(n=int(a.size), mean=float(a.mean()), median=float(np.median(a)),
                p90=float(np.percentile(a, 90)), total=float(a.sum()))


def report(scored, unjoined, join_meta, sign_line, six_line, export_hits):
    print(f"\n[SIGN] {sign_line}")
    print(f"[6]    the sign audit RAISES under a flipped convention: {six_line}")
    print(f"[JOIN] {join_meta['n_joined']} of {join_meta['n_keys']} (symbol, date) keys joined to {join_meta['fixture']} "
          f"in the {join_meta['frame']} frame; the streamed bar and the prep's grid proved to be the same bar"
          + (f"; {export_hits} of them re-checked against data/{EXPORT_CSV.name}" if export_hits else ""))
    print("       the bp is FRAME-INVARIANT (a common split factor cancels in (fill - print) / print); the "
          "as-traded frame is what makes the printed price and the shares x fill notional right")
    if unjoined:
        print(f"\n  {len(unjoined)} row(s) NOT joined and excluded from every statistic below:")
        for rec in unjoined:
            print(f"    line {rec['_line']}: {rec['symbol']} {rec['date']}")
    if not scored:
        print("\n  no joined fills to score.")
        return

    print(f"\n  {'date':12}{'symbol':9}{'side':13}{'ord':5}{'shares':>8}{'fill':>11}{'print':>11}"
          f"{'slip_bp':>10}{'PUB_bp':>9}{'PB_bp':>9}{'comm_bp':>9}  time      venue")
    for s in scored:
        cb = "-" if s["comm_bp"] is None else f"{s['comm_bp']:+.2f}"
        print(f"  {s['date']:12}{s['symbol']:9}{s['side']:13}{s['order_type']:5}{s['shares']:>8}"
              f"{s['fill_price']:>11.4f}{s['print_px']:>11.4f}{s['slip_bp']:>+10.2f}"
              f"{s['PUB']:>+9.2f}{s['PB']:>+9.2f}{cb:>9}  {(s['fill_time'] or '-'):9} {s['venue'] or '-'}")

    print(f"\n  {'group':13}{'n':>5}{'mean_bp':>11}{'median_bp':>11}{'p90_bp':>11}{'total_bp':>11}"
          f"{'comm_n':>8}{'comm_bp':>10}{'PUB_bp':>9}{'PB_bp':>9}")
    groups = [("short_entry", [s for s in scored if s["side"] == "short_entry"]),
              ("cover_exit", [s for s in scored if s["side"] == "cover_exit"]),
              ("POOLED", scored)]
    for name, g in groups:
        st = stats([s["slip_bp"] for s in g])
        if st is None:
            print(f"  {name:13}{0:>5}{'-':>11}{'-':>11}{'-':>11}{'-':>11}{0:>8}{'-':>10}{'-':>9}{'-':>9}")
            continue
        cb = [s["comm_bp"] for s in g if s["comm_bp"] is not None]
        cm = f"{float(np.mean(cb)):+.4f}" if cb else "-"
        print(f"  {name:13}{st['n']:>5}{st['mean']:>+11.4f}{st['median']:>+11.4f}{st['p90']:>+11.4f}"
              f"{st['total']:>+11.4f}{len(cb):>8}{cm:>10}"
              f"{float(np.mean([s['PUB'] for s in g])):>+9.2f}{float(np.mean([s['PB'] for s in g])):>+9.2f}")
    n_blank = sum(1 for s in scored if s["comm_bp"] is None)
    if n_blank:
        print(f"\n  {n_blank} row(s) carry a BLANK commission and are absent from the commission column "
              "(blank is not zero and is not averaged as zero).")
    print("\n  PUB_bp / PB_bp are D363's modelled half-spread at that (symbol, date), bp per side -- what the cost "
          "model CHARGED.\n  A fill inside it is one the model already paid for; a fill outside it is a cost the "
          "record has never carried.\n  Nothing above is a result and nothing above is a book entry (R8).")


def run(log_path, verbose=True):
    rows = read_log(log_path)
    sign_line = assert_SIGN()
    six_line = assert_6()
    print(f"\nd364_slippage  log={Path(log_path)}  rows={len(rows)}")
    if not rows:
        print_schema()
        print(f"\n[SIGN] {sign_line}")
        print(f"[6]    the sign audit RAISES under a flipped convention: {six_line}")
        print(f"[EMPTY] {Path(log_path).name} carries the header and NO data rows: no fills are recorded yet, so "
              "there is nothing to measure.\n        The prep was not loaded and the fixture was not opened. This "
              "is the honest state of the log until the\n        principal places orders and fills it in by hand; "
              "exit 0.")
        return 0
    keys = {(r["symbol"], r["date"]) for r in rows}
    book, miss, meta = prints_from_fixture(keys, verbose=verbose)
    for k, why in miss:
        print(f"  [JOIN] no print for {k[0]} {k[1]}: {why}")
    hits = assert_JOIN_against_export(book)
    scored, unjoined = score(rows, book)
    report(scored, unjoined, meta, sign_line, six_line, hits)
    return 0


# ------------------------------------------------------------------ the self-test
SYNTH_BOOK = {
    # (symbol, date): the as-traded prints and D363's cost lines. Round numbers so the answer is hand-computable.
    ("FOO", "2020-01-02"): dict(open=100.00, close=101.00, PUB=12.0, PB=8.0),
    ("BAR", "2020-01-03"): dict(open=49.00, close=50.00, PUB=30.0, PB=25.0),
}
SYNTH_ROWS = (
    "2020-01-02,FOO,short_entry,open,MOO,1000,,99.50,09:30:00,XNAS,9.95,sold below the open",
    "2020-01-03,BAR,cover_exit,close,MOC,500,,50.10,16:00:00,XNYS,2.505,bought above the close",
)


def selftest():
    t0 = time.time()
    print("\nd364_slippage --selftest")

    # ---- 1. the sign, in money, on both sides, and the audit's own failure mode
    sign_line = assert_SIGN()
    six_line = assert_6()
    print(f"  [SIGN] {sign_line}")
    print(f"         checked in money on FOUR probes: short_entry 99.50 vs 100.00 = +50.00 bp (worse) and 100.50 = "
          f"-50.00 (better); cover_exit 50.10 vs 50.00 = +20.00 (worse) and 49.90 = -20.00 (better)")
    print(f"  [6]    the same audit under a FLIPPED SIDE_SIGN raises, as it must: {six_line}")

    tmp = Path(tempfile.mkdtemp(prefix="d364_selftest_"))
    try:
        # ---- 2. the two-row synthetic log, hand-computed
        p = tmp / "two_rows.csv"
        p.write_text(",".join(COLS) + "\n" + "\n".join(SYNTH_ROWS) + "\n", encoding="utf-8")
        rows = read_log(p)
        assert len(rows) == 2, "[SELFTEST] the two-row log did not parse as two rows"
        scored, unjoined = score(rows, SYNTH_BOOK)
        assert not unjoined and len(scored) == 2, "[SELFTEST] a synthetic row failed to join"

        # HAND-COMPUTED, written out here rather than recomputed:
        #   row 1  short_entry, intended_print=open -> print = 100.00; fill 99.50 -> SOLD 0.50 BELOW the open = WORSE
        #          slip = -1 x (99.50 - 100.00) / 100.00 x 1e4 = -1 x (-0.005) x 1e4 = +50.0000 bp
        #          notional = 1000 x 99.50 = 99,500.00; commission 9.95 -> 9.95 / 99,500 x 1e4 = +1.0000 bp
        #   row 2  cover_exit,  intended_print=close -> print = 50.00; fill 50.10 -> BOUGHT 0.10 ABOVE the close = WORSE
        #          slip = +1 x (50.10 - 50.00) / 50.00 x 1e4 = +1 x 0.002 x 1e4 = +20.0000 bp
        #          notional = 500 x 50.10 = 25,050.00; commission 2.505 -> 2.505 / 25,050 x 1e4 = +1.0000 bp
        #   pooled n = 2; mean = (50 + 20) / 2 = 35.0000; median of {20, 50} = 35.0000
        #          p90 (linear interpolation on 2 points) = 20 + 0.9 x (50 - 20) = 47.0000; total = 70.0000
        WANT = dict(slip=(50.0, 20.0), comm=(1.0, 1.0), notional=(99_500.0, 25_050.0), print_px=(100.00, 50.00),
                    pooled=dict(n=2, mean=35.0, median=35.0, p90=47.0, total=70.0),
                    short=dict(n=1, mean=50.0, median=50.0, p90=50.0, total=50.0),
                    cover=dict(n=1, mean=20.0, median=20.0, p90=20.0, total=20.0))
        for j, s in enumerate(scored):
            for key, want in (("slip_bp", WANT["slip"][j]), ("comm_bp", WANT["comm"][j]),
                              ("notional", WANT["notional"][j]), ("print_px", WANT["print_px"][j])):
                assert abs(s[key] - want) < 1e-9, f"[SELFTEST] row {j + 1} {key} = {s[key]!r}, hand-computed {want!r}"
        for name, sel, want in (("POOLED", scored, WANT["pooled"]),
                                ("short_entry", [s for s in scored if s["side"] == "short_entry"], WANT["short"]),
                                ("cover_exit", [s for s in scored if s["side"] == "cover_exit"], WANT["cover"])):
            st = stats([s["slip_bp"] for s in sel])
            for k, v in want.items():
                assert abs(st[k] - v) < 1e-9, f"[SELFTEST] {name} {k} = {st[k]!r}, hand-computed {v!r}"
        print(f"  [SELFTEST] two-row synthetic log, hand-computed and reproduced EXACTLY:")
        print(f"         row 1  FOO short_entry MOO 1,000 @ 99.50 vs open 100.00 -> -1 x (99.50-100.00)/100.00 x 1e4 "
              f"= +50.0000 bp WORSE; comm 9.95 / (1,000 x 99.50) x 1e4 = +1.0000 bp")
        print(f"         row 2  BAR cover_exit  MOC   500 @ 50.10 vs close 50.00 -> +1 x (50.10-50.00)/50.00 x 1e4 "
              f"= +20.0000 bp WORSE; comm 2.505 / (500 x 50.10) x 1e4 = +1.0000 bp")
        print(f"         pooled n=2 mean +35.0000 median +35.0000 p90 +47.0000 total +70.0000; per side "
              f"+50.0000 / +20.0000")

        # the mirrored log: the same magnitudes on the FAVOURABLE side of each print must come back NEGATIVE
        mirror = ("2020-01-02,FOO,short_entry,open,MOO,1000,,100.50,09:30:00,XNAS,9.95,sold above the open",
                  "2020-01-03,BAR,cover_exit,close,MOC,500,,49.90,16:00:00,XNYS,2.505,bought below the close")
        pm = tmp / "two_rows_mirror.csv"
        pm.write_text(",".join(COLS) + "\n" + "\n".join(mirror) + "\n", encoding="utf-8")
        sm, _ = score(read_log(pm), SYNTH_BOOK)
        assert abs(sm[0]["slip_bp"] - (-50.0)) < 1e-9 and abs(sm[1]["slip_bp"] - (-20.0)) < 1e-9, \
            f"[SELFTEST] the mirrored fills are not the negatives: {sm[0]['slip_bp']!r} {sm[1]['slip_bp']!r}"
        print(f"         mirrored (99.50->100.50, 50.10->49.90): -50.0000 / -20.0000 bp, the exact negatives -- "
              f"the convention is not one-sided")

        # ---- 3. the empty-log path
        pe = tmp / "empty.csv"
        pe.write_text(",".join(COLS) + "\n", encoding="utf-8")
        assert read_log(pe) == [], "[EMPTY] an empty log did not parse as zero rows"
        rc = run(pe, verbose=False)
        assert rc == 0, f"[EMPTY] the empty-log path returned {rc}, expected 0"
        assert not any("d348p" in k or "d361x" in k for k in sys.modules), \
            "[EMPTY] the empty-log path loaded the prep or the fixture reader; it must load neither"
        print(f"  [EMPTY] the header-only log parses as zero rows, prints the schema, loads NEITHER the prep NOR "
              f"the fixture reader, and exits 0")

        # ---- 4. the real join, on two committed (symbol, date) pairs
        real = {("ISSI", "2010-04-06"), ("WPRT", "2010-04-06")}
        book, miss, meta = prints_from_fixture(real, verbose=False)
        assert not miss and len(book) == 2, f"[JOIN] the real pairs did not join: {miss}"
        hits = assert_JOIN_against_export(book)
        w = book[("WPRT", "2010-04-06")]
        print(f"  [JOIN] the same two pairs through the real path: {meta['n_joined']} joined from "
              f"{meta['fixture']} in the {meta['frame']} frame; {hits} cells re-checked against "
              f"data/{EXPORT_CSV.name} and equal to the character")
        print(f"         WPRT 2010-04-06 is the frame's own witness: fixture (adjusted) open {w['adj_open']!r} x RAW "
              f"{w['raw_factor']!r} = as-traded {w['open']!r} == the export's price_open_entry; "
              f"ISSI 2010-04-06 as-traded open {book[('ISSI', '2010-04-06')]['open']!r} (RAW = 1.0, the frames agree)")
    finally:
        for f in sorted(tmp.glob("*")):
            f.unlink()
        tmp.rmdir()
    print(f"\n  SELFTEST PASSED [SIGN] [JOIN] [EMPTY] [6]  ({time.time() - t0:.0f}s)")
    return 0


def main():
    ap = argparse.ArgumentParser(description="measure a hand-filled fill log against the fixture's own prints")
    ap.add_argument("--log", default=str(LOG), help=f"the fill log (default {LOG.relative_to(REPO)})")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    # No --quiet: d348_prep prints its own [K] / [F0] / [R] banner unconditionally on a cache hit, so a flag
    # promising silence would not deliver it, and an inert switch is worse than none.
    return run(a.log)


if __name__ == "__main__":
    raise SystemExit(main())
