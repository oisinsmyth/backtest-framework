"""D584 -- the CME session calendar: one row per (root, ET calendar day) for the 36 breadth roots.

    python scripts/build_cme_session_calendar.py --selftest    # SYSTEM python; every gate passes a clean case and RAISES on a break
    python scripts/build_cme_session_calendar.py --build       # SYSTEM python (pyarrow); ~1 min -> data/fixtures/cme_session_calendar.csv.gz + .meta.json
    python scripts/build_cme_session_calendar.py --build --events data/calendar/events.csv

**Data layer only. No study, no signal, no return.** A calendar is a fact, so it spans the full held
range to the latest bar and nothing here is windowed to a study's in-sample slice.

WHAT IS JOINED AND WHAT IS DERIVED
----------------------------------
JOINED, never re-derived (the `fut_day1m.meta.json` rule -- two fixtures must not be able to
disagree about the front month):

  front_contract, roll_day   <- data/fixtures/fut_breadth_hourly.csv.gz  (`contract`, `same_front`)
  rth_bars  (ES NQ YM RTY)   <- data/fixtures/fut_index_sessions.csv.gz  (`bars`, 390 on a full session)
  expiry_day, days_to_expiry <- data/fut_expiries_from_definition.json   (nearest expiry at or after the day)
  fomc, cpi, empsit          <- data/macro_release_calendar.json, or --events PATH

DERIVED HERE, from the root's OWN minute bars in data/fixtures/fut_day1m.parquet:

  is_trading, session_open_et, session_close_et, is_early_close, rth_bars (the other 32 roots)

and the three pure-calendar flags month_end, quarter_end, dst_transition_week, plus quad_witching
from the ES expiry list.

WHY THE CLOSE IS NOT 15:59 FOR EVERY ROOT (D530)
------------------------------------------------
`fut_day1m` is cut to a 09:00-15:59 ET template, 420 bars. A 23-hour root keeps printing bars long
after its market has settled -- D530 got a spurious z = -12.6 "closing reversion" out of exactly
that. So the regular-session close is taken from the SETTLEMENT VOLUME CLIFF in each root's own
mean minute-volume profile: the minute whose volume is at least CLIFF_RATIO times the mean of the
next CLIFF_W minutes. That recovers COMEX metals at 13:00-13:30, NYMEX energy at 14:30, the CBOT
grains at 14:20, livestock at 14:00 and the FX/Treasury 15:00 settlement, and finds no decisive
cliff on the index roots -- whose session runs to or past the 15:59 window edge.

WHY AN EARLY CLOSE IS A MARKET-WIDE FACT (the `_half_days` pattern of scripts/fetch_etf_intraday.py)
----------------------------------------------------------------------------------------------------
A short session has two causes that need opposite treatment: the calendar (the whole exchange shut)
and liquidity (one thin root did not trade). So a root is `is_early_close` only when it is short AND
the day is short across the complex. The archive adds a third cause, and it is the one that bites:
2020-06-30 truncates 22 of 36 roots at 10:10 and 2020-02-27 truncates 22 of them at 13:20. Both look
exactly like a market-wide early close on counts alone. They are separated by a property of the
object rather than a threshold -- **an exchange session ends on a five-minute boundary and a feed
dropout does not** -- and every day the rule rejects is listed in the meta.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "data" / "fixtures"
DAY1M = FIX / "fut_day1m.parquet"
BREADTH = FIX / "fut_breadth_hourly.csv.gz"
IDXSESS = FIX / "fut_index_sessions.csv.gz"
ROLLS = FIX / "fut_sessions_rolls.csv.gz"
EXPIRIES = REPO / "data" / "fut_expiries_from_definition.json"
MACRO = REPO / "data" / "macro_release_calendar.json"
OUT = FIX / "cme_session_calendar.csv.gz"
META = FIX / "cme_session_calendar.meta.json"

SPEC = "D584"
TZ = "US/Eastern"
BAR0_MIN = 9 * 60                 # fut_day1m bar 0 is 09:00 ET
N_BARS = 420                      # ... and bar 419 is 15:59 ET
INDEX_ROOTS = ("ES", "NQ", "YM", "RTY")

# -- the settlement cliff (regular-session close, per root)
CLIFF_W = 30                      # minutes of "after" the cliff is measured against
CLIFF_LO, CLIFF_HI = 60, 389      # candidate minutes 10:00 .. 15:29 (CLIFF_W minutes of tail must fit)
CLIFF_RATIO = 4.0                 # v[m] / mean(v[m+1 .. m+CLIFF_W]) at or above this is a close
CLIFF_MIN_SHARE = 0.10            # ... and v[m] must be >= this share of the root's busiest minute
CLIFF_FROM = "2016-01-04"         # profile measured on the clean span (D462 G5), applied to all years

# -- the early close
SHORT_MIN = 30                    # a root is short when it stops >= 30 min before its own band close
WIDE_MIN_ROOTS = 10               # a day needs this many roots trading before it can be classified
WIDE_MIN_SHORT = 4                # ... and this many short ones
WIDE_CONC = 0.40                  # ... whose stop minutes agree within CONC_TOL of their mode
CONC_TOL = 5
BOUNDARY = 5                      # an exchange session ends on a five-minute boundary

FULL_SESSION_BARS_INDEX = 390     # 09:30-15:59 on ES/NQ/YM/RTY, from fut_index_sessions
G1_FROM = "2016-01-04"            # the index roots' usable start (D462 G5); before it, absence is the archive

COLUMNS = ("root", "day", "is_trading", "session_open_et", "session_close_et", "rth_bars",
           "is_early_close", "front_contract", "roll_day", "expiry_day", "days_to_expiry",
           "quad_witching", "month_end", "quarter_end", "fomc", "cpi", "empsit", "dst_transition_week")

REQUIRED_OUTPUTS = ("spec", "built_utc", "builder", "rows", "roots", "span", "row_grid", "columns",
                    "sources", "bands", "flag_notes", "dropped_buckets", "special_sessions",
                    "holiday_disagreements", "gates", "all_gates_pass", "gates_not_run", "files")

# Fetching cmegroup.com failed from this machine on every route tried; G6 is recorded not_fetched
# rather than sourced from a third party. Every entry carries the URL and the access time.
CME_FETCH_ATTEMPTS = [
    {"source_url": "https://www.cmegroup.com/tools-information/holiday-calendar.html",
     "accessed_utc": "2026-09-21T19:29:00Z", "via": "WebFetch", "result": "timeout after 60 s"},
    {"source_url": "https://www.cmegroup.com/files/good-friday.pdf",
     "accessed_utc": "2026-09-21T19:29:40Z", "via": "WebFetch", "result": "ECONNRESET"},
    {"source_url": "https://www.cmegroup.com/trading-hours.html",
     "accessed_utc": "2026-09-21T19:29:40Z", "via": "WebFetch", "result": "timeout after 60 s"},
    {"source_url": "https://www.cmegroup.com/tools-information/holiday-calendar/files/2025-new-years-advisory.pdf",
     "accessed_utc": "2026-09-21T19:30:10Z", "via": "WebFetch", "result": "timeout after 60 s"},
    {"source_url": "https://www.cmegroup.com/tools-information/holiday-calendar/files/2025/2025-christmas-clearing-advisory.pdf",
     "accessed_utc": "2026-09-21T19:31:30Z", "via": "WebFetch", "result": "ECONNRESET"},
    {"source_url": "https://www.cmegroup.com/files/good-friday.pdf",
     "accessed_utc": "2026-09-21T19:30:30Z", "via": "curl", "result": "HTTP 403 (602-byte WAF page)"},
    {"source_url": "https://www.cmegroup.com/tools-information/holiday-calendar.html",
     "accessed_utc": "2026-09-21T19:30:30Z", "via": "curl", "result": "HTTP 403 (602-byte WAF page)"},
    {"source_url": "https://investor.cmegroup.com/static-files/1047cbcc-7569-40ab-bb6b-6973eea07ea3",
     "accessed_utc": "2026-09-21T19:32:20Z", "via": "WebFetch", "result": "timeout after 60 s"},
]


def log(*a):
    print(*a, flush=True)


def expect_raise(fn, what):
    """A self-test that cannot fail is worse than none (CLAUDE.md). The break must hit the scalar compared."""
    try:
        fn()
    except AssertionError as e:
        log(f"    RAISES on {what}: {str(e)[:90]}")
        return True
    raise AssertionError(f"the check did not raise on {what}")


def hhmm(bar) -> str:
    """fut_day1m bar index -> ET wall clock. Bar 0 is 09:00, bar 419 is 15:59."""
    m = BAR0_MIN + int(bar)
    return f"{m // 60:02d}:{m % 60:02d}"


# ------------------------------------------------------------------------------------- calendar rules
def easter(year: int) -> pd.Timestamp:
    """Anonymous Gregorian algorithm. Good Friday is this minus two days."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    L = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 19 * L) // 433
    month = (h + L - 7 * m + 90) // 25
    day = (h + L + 114 - 31 * month - 7 * m) % 31 + 1
    return pd.Timestamp(year=year, month=month, day=day)


def full_closure_days(years) -> dict:
    """The three days a year on which the CME equity index day session does not exist at all.

    The observance rule is NOT symmetric and the asymmetry is real, not a convenience: Christmas on a
    Saturday is taken on the preceding Friday (2021-12-24 is in the data as a closure), New Year's Day
    on a Saturday is NOT taken on the preceding Friday (2021-12-31 trades a full session). That is the
    NYSE/SIFMA rule the CME follows, and G1 asserts this set reproduces the observed closures exactly,
    so a wrong rule fails the build rather than being absorbed.
    """
    out = {}
    for y in years:
        gf = easter(y) - pd.Timedelta(days=2)
        out[gf.strftime("%Y-%m-%d")] = "Good Friday"
        xmas = pd.Timestamp(year=y, month=12, day=25)
        if xmas.dayofweek == 5:
            xmas -= pd.Timedelta(days=1)
        elif xmas.dayofweek == 6:
            xmas += pd.Timedelta(days=1)
        out[xmas.strftime("%Y-%m-%d")] = "Christmas Day"
        ny = pd.Timestamp(year=y, month=1, day=1)
        if ny.dayofweek == 6:
            ny += pd.Timedelta(days=1)
        if ny.dayofweek < 5:
            out[ny.strftime("%Y-%m-%d")] = "New Year's Day"
    return out


def dst_transition_weeks(days: pd.DatetimeIndex) -> set:
    """The seven ET days beginning with each US DST transition.

    The transition day is the first ET day on the new UTC offset -- always a Sunday, because the change
    is at 02:00 local. The week marked therefore RUNS FORWARD from it, covering the Monday-to-Friday
    sessions that trade on the new offset while Europe has not yet moved, rather than the Mon-Sun week
    that merely ends on the transition and whose sessions all trade on the old one.

    The transitions are found from the tz database, not from the second-Sunday / first-Sunday rule, so
    the pre-2007 dates and any future change are picked up rather than asserted.
    """
    d0, d1 = min(days), max(days)
    idx = pd.date_range(d0, d1, freq="D")
    off = np.asarray(idx.tz_localize(TZ, nonexistent="shift_forward", ambiguous=True).map(lambda t: t.utcoffset()))
    out = set()
    for i in np.flatnonzero(off[1:] != off[:-1]) + 1:
        # idx[i] is the first day whose MIDNIGHT is on the new offset; the change is at 02:00, so the
        # transition falls on the day before it -- the Sunday.
        d = idx[i] - pd.Timedelta(days=1)
        out |= {(d + pd.Timedelta(days=k)).strftime("%Y-%m-%d") for k in range(7)}
    return out


# ------------------------------------------------------------------------------------- bands
def band_close_from_profile(v: np.ndarray) -> tuple:
    """The regular-session close as the settlement volume cliff, or the window edge when there is none.

    Returns (bar, ratio) with bar = N_BARS - 1 and ratio = None when no minute qualifies -- which is
    the right answer for a root whose session runs past 16:00 ET, not a failure.
    """
    assert v.shape == (N_BARS,), f"profile must be {N_BARS} minutes, got {v.shape}"
    peak = float(v.max())
    best, bm = 0.0, None
    for m in range(CLIFF_LO, CLIFF_HI + 1):
        if v[m] < CLIFF_MIN_SHARE * peak:
            continue
        tail = float(v[m + 1:m + 1 + CLIFF_W].mean())
        ratio = float(v[m] / tail) if tail > 0 else float("inf")
        if ratio >= CLIFF_RATIO and ratio > best:
            best, bm = ratio, m
    return (bm, best) if bm is not None else (N_BARS - 1, None)


def market_wide_early_closes(sess: pd.DataFrame) -> tuple:
    """Which days are calendar early closes, and which short days are rejected and why.

    `sess` carries root, day, last (the day's last traded minute, clipped to the root's band) and
    band_close. A day qualifies when enough roots trade, enough of them are short, their stop minutes
    agree, and the modal stop is the minute before a five-minute boundary.
    """
    s = sess.copy()
    s["short"] = s["last"] <= s["band_close"] - SHORT_MIN
    accepted, rejected = {}, []
    for day, g in s.groupby("day", sort=True):
        sh = g[g["short"]]
        n, k = len(g), len(sh)
        if k == 0:
            continue
        mode = int(sh["last"].mode().iloc[0])
        conc = float((np.abs(sh["last"] - mode) <= CONC_TOL).mean())
        bdry = (BAR0_MIN + mode + 1) % BOUNDARY == 0
        ok = n >= WIDE_MIN_ROOTS and k >= WIDE_MIN_SHORT and conc >= WIDE_CONC and bdry
        if ok:
            accepted[day] = dict(n_trading=n, n_short=k, modal_close_et=hhmm(mode), concentration=round(conc, 3))
        elif k >= WIDE_MIN_SHORT and n >= WIDE_MIN_ROOTS:
            rejected.append(dict(day=day, n_trading=n, n_short=k, modal_stop_et=hhmm(mode),
                                 concentration=round(conc, 3), on_five_minute_boundary=bool(bdry),
                                 short_roots=sorted(sh["root"])[:40]))
    return accepted, rejected


# ------------------------------------------------------------------------------------- loads
def load_day1m():
    """Per (root, day): the first and last traded minute, the traded-bar count, and the mean minute profile."""
    import pyarrow.parquet as pq

    roots = sorted(json.loads((FIX / "fut_day1m.meta.json").read_text(encoding="utf-8"))["roots"])
    sess, prof = [], {}
    for r in roots:
        tb = pq.read_table(DAY1M, columns=["root", "day", "bar", "volume"],
                           filters=[("root", "==", r)]).to_pandas()
        nz = tb[tb["volume"] > 0]
        g = nz.groupby("day")["bar"].agg(first="min", last="max", traded_bars="size").reset_index()
        g["root"] = r
        sess.append(g)
        p = tb[tb["day"] >= CLIFF_FROM].groupby("bar")["volume"].mean()
        prof[r] = p.reindex(range(N_BARS), fill_value=0.0).to_numpy(float)
        # the day1m bar index must be the 09:00-15:59 template it claims to be, or every clock here is wrong
        assert int(tb["bar"].min()) >= 0 and int(tb["bar"].max()) <= N_BARS - 1, f"{r}: bar index outside 0..{N_BARS-1}"
    return roots, pd.concat(sess, ignore_index=True), prof


def load_events(path: Path | None):
    """Release-day flags. Either the JSON the repo already consumes, or a --events CSV of datetime_et,event."""
    if path is None:
        m = json.loads(MACRO.read_text(encoding="utf-8"))
        sets = {"fomc": set(m["fomc_statement_days"]), "cpi": set(m["cpi_release_days"]),
                "empsit": set(m["empsit_release_days"])}
        src = {"kind": "macro_release_calendar.json", "path": str(MACRO.relative_to(REPO)),
               "provenance": m["_provenance"], "accessed_utc": None,
               "note": "fomc_unscheduled (2019-10-04, 2020-03-03, 2020-03-15) is NOT folded into the fomc flag; "
                       "the flag is the scheduled statement day only, as run_d494_outside_path.py reads it"}
    else:
        df = pd.read_csv(path, dtype=str, encoding="utf-8")
        assert {"datetime_et", "event"} <= set(df.columns), f"--events needs datetime_et and event, got {list(df.columns)}"
        df["day"] = df["datetime_et"].str[:10]
        e = df["event"].str.upper()
        sets = {"fomc": set(df.loc[e.str.contains("FOMC"), "day"]),
                "cpi": set(df.loc[e.str.contains("CPI"), "day"]),
                "empsit": set(df.loc[e.str.contains("PAYROLL|EMPLOYMENT SITUATION|NFP|EMPSIT"), "day"])}
        src = {"kind": "events csv", "path": str(path), "rows": int(len(df)),
               "accessed_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "match": {"fomc": "FOMC", "cpi": "CPI", "empsit": "PAYROLL|EMPLOYMENT SITUATION|NFP|EMPSIT"}}
    src["covers"] = {k: ([min(v), max(v)] if v else None) for k, v in sets.items()}
    return sets, src


def expiry_map():
    """{root: {symbol: [ET dates ascending]}} from the definition file. A symbol carries several
    expiries because single-digit year codes are recycled (D581); the resolve rule picks the nearest
    at or after the session date, which is what makes the recycling harmless."""
    e = json.loads(EXPIRIES.read_text(encoding="utf-8"))
    out = {}
    for root, syms in e["expiries"].items():
        out[root] = {s: sorted(pd.Timestamp(v, tz="UTC").tz_convert(TZ).strftime("%Y-%m-%d") for v in vs)
                     for s, vs in syms.items()}
    return out, e["source"]


def resolve_expiry(exp_root: dict, symbol, day: str):
    """The nearest expiry at or after `day` for this symbol, or None."""
    if symbol is None or symbol != symbol or symbol not in exp_root:
        return None
    for d in exp_root[symbol]:
        if d >= day:
            return d
    return None


# ------------------------------------------------------------------------------------- assemble
def assemble(roots, sess, prof, breadth, idx, events, exp, last_day):
    bands = {}
    for r in roots:
        bc, ratio = band_close_from_profile(prof[r])
        s = sess[sess["root"] == r]
        bo = int(s["first"].mode().iloc[0])
        bands[r] = dict(open_bar=bo, close_bar=int(bc), open_et=hhmm(bo), close_et=hhmm(bc),
                        cliff_ratio=(round(ratio, 2) if ratio else None),
                        close_from=("settlement volume cliff" if ratio else "window edge 15:59 -- no decisive cliff"),
                        sessions=int(len(s)))
    sess = sess.copy()
    sess["band_open"] = sess["root"].map(lambda r: bands[r]["open_bar"])
    sess["band_close"] = sess["root"].map(lambda r: bands[r]["close_bar"])
    sess["first"] = np.maximum(sess["first"], sess["band_open"])
    sess["last"] = np.minimum(sess["last"], sess["band_close"])
    accepted, rejected = market_wide_early_closes(sess)
    sess["short"] = sess["last"] <= sess["band_close"] - SHORT_MIN
    sess["is_early_close"] = sess["short"] & sess["day"].isin(accepted)

    # rth_bars inside the root's OWN band -- the index roots take the committed 09:30-15:59 count instead
    import pyarrow.parquet as pq
    rth = []
    for r in roots:
        lo, hi = bands[r]["open_bar"], bands[r]["close_bar"]
        tb = pq.read_table(DAY1M, columns=["root", "day", "bar", "volume"],
                           filters=[("root", "==", r), ("bar", ">=", lo), ("bar", "<=", hi)]).to_pandas()
        g = tb[tb["volume"] > 0].groupby("day").size().rename("rth_bars").reset_index()
        g["root"] = r
        rth.append(g)
    sess = sess.merge(pd.concat(rth, ignore_index=True), on=["root", "day"], how="left")
    ix = idx.rename(columns={"bars": "index_bars"})[["root", "day", "index_bars"]]
    sess = sess.merge(ix, on=["root", "day"], how="left")
    sess["rth_bars"] = np.where(sess["index_bars"].notna(), sess["index_bars"], sess["rth_bars"])

    # the row grid: every ET calendar day from the root's first breadth day to the last bar in the panel
    first_day = breadth.groupby("root")["day"].min()
    frames = []
    for r in roots:
        d = pd.date_range(first_day[r], last_day, freq="D")
        frames.append(pd.DataFrame({"root": r, "day": d.strftime("%Y-%m-%d")}))
    cal = pd.concat(frames, ignore_index=True)

    cal = cal.merge(sess[["root", "day", "first", "last", "rth_bars", "is_early_close"]], on=["root", "day"], how="left")
    cal["is_trading"] = cal["first"].notna()
    cal["session_open_et"] = cal["first"].map(lambda b: hhmm(b) if b == b else None)
    cal["session_close_et"] = cal["last"].map(lambda b: hhmm(b) if b == b else None)
    cal["rth_bars"] = cal["rth_bars"].astype("Int64")
    cal["is_early_close"] = cal["is_early_close"].fillna(False).astype(bool)

    b = breadth.rename(columns={"contract": "front_contract"})[["root", "day", "front_contract", "same_front"]]
    cal = cal.merge(b, on=["root", "day"], how="left")
    cal["roll_day"] = (cal["same_front"] == False) & cal["front_contract"].notna()  # noqa: E712
    cal = cal.drop(columns=["same_front"])

    # days_to_expiry is the FRONT contract's; expiry_day is the ROOT's expiry calendar. They are
    # deliberately different objects and expiry_day is NOT days_to_expiry == 0: the front is elected by
    # volume and rolls a week or two early, so a front contract is essentially never held to expiry.
    dte = []
    for r, d, c in zip(cal["root"], cal["day"], cal["front_contract"]):
        x = resolve_expiry(exp.get(r, {}), c, d)
        dte.append((pd.Timestamp(x) - pd.Timestamp(d)).days if x else None)
    cal["days_to_expiry"] = pd.array(dte, dtype="Int64")
    root_expiries = {r: {d for ds in exp.get(r, {}).values() for d in ds} for r in roots}
    cal["expiry_day"] = [d in root_expiries.get(r, ()) for r, d in zip(cal["root"], cal["day"])]

    # quad witching: an ES expiry in Mar/Jun/Sep/Dec, taken from the definition file, not from the
    # third-Friday rule -- 2026-06-18 is a THURSDAY because the third Friday is Juneteenth.
    qw = {d for ds in exp["ES"].values() for d in ds if d[5:7] in ("03", "06", "09", "12")}
    cal["quad_witching"] = cal["day"].isin(qw)

    # the root's OWN last trading day of the ET month and quarter -- a (root, day) pair, not a day:
    # the exchange groups keep different holidays, so the roots do not share a month-end (D556).
    t = cal[cal["is_trading"]]
    mon = t["day"].str[:7]
    qtr = t["day"].str[:4] + "Q" + ((pd.to_datetime(t["day"]).dt.month - 1) // 3 + 1).astype(str)
    me = set(zip(t["root"], t.groupby([t["root"], mon])["day"].transform("max")))
    qe = set(zip(t["root"], t.groupby([t["root"], qtr])["day"].transform("max")))
    key = list(zip(cal["root"], cal["day"]))
    cal["month_end"] = [k in me for k in key]
    cal["quarter_end"] = [k in qe for k in key]
    assert cal["month_end"].sum() > 0 and cal["quarter_end"].sum() > 0, "month_end/quarter_end fired on nothing"
    assert not (cal["month_end"] & ~cal["is_trading"]).any(), "a month end landed on a non-trading day"

    for f in ("fomc", "cpi", "empsit"):
        lo, hi = (min(events[f]), max(events[f])) if events[f] else (None, None)
        v = cal["day"].isin(events[f])
        cal[f] = pd.array(np.where(cal["day"].between(lo, hi), v, None), dtype="boolean") if lo else pd.array([None] * len(cal), dtype="boolean")
    cal["dst_transition_week"] = cal["day"].isin(dst_transition_weeks(pd.DatetimeIndex(sorted(set(cal["day"])))))

    cal = cal[list(COLUMNS)].sort_values(["root", "day"], ignore_index=True)
    return cal, bands, accepted, rejected, qw


# ------------------------------------------------------------------------------------- gates
def g1_holidays(cal: pd.DataFrame) -> dict:
    """Known US market holidays are is_trading=False on ES/NQ/YM/RTY -- and nothing else is.

    Gated as set EQUALITY, not containment: the rule set must reproduce the observed non-trading
    weekdays exactly. Containment alone would pass a rule that closed the market every Tuesday.
    """
    years = range(int(cal["day"].min()[:4]), int(cal["day"].max()[:4]) + 1)
    hol = full_closure_days(years)
    out, ok = {}, True
    for r in INDEX_ROOTS:
        c = cal[(cal["root"] == r) & (cal["day"] >= G1_FROM)]
        wd = c[pd.to_datetime(c["day"]).dt.dayofweek < 5]
        observed = set(wd.loc[~wd["is_trading"], "day"])
        expect = {d for d in hol if d in set(wd["day"])}
        # Good Friday is a partial session in the years a payroll report lands on it: ES prints
        # 09:00-09:14 and then halts. Those days ARE trading days, and they are named, not waived.
        partial = {d for d in expect & set(wd.loc[wd["is_trading"], "day"]) if hol[d] == "Good Friday"}
        miss, extra = sorted(expect - observed - partial), sorted(observed - expect)
        out[r] = dict(n_holiday_weekdays=len(expect), n_non_trading=len(observed),
                      good_friday_partial_sessions=sorted(partial), holidays_that_traded=miss,
                      non_trading_days_not_in_the_rule=extra, passes=bool(not miss and not extra))
        ok &= out[r]["passes"]
    return dict(rule="full_closure_days(): Good Friday, Christmas Day (Sat->Fri, Sun->Mon), New Year's Day (Sun->Mon)",
                threshold="set equality against the observed non-trading weekdays from " + G1_FROM,
                measured=out, passes=bool(ok))


def g2_early_close(cal: pd.DataFrame) -> dict:
    """The day after Thanksgiving and Christmas Eve are is_early_close on ES in every year 2016+."""
    es = cal[(cal["root"] == "ES")].set_index("day")
    years = range(2016, int(cal["day"].max()[:4]) + 1)
    rows, ok = [], True
    for y in years:
        nov = pd.Timestamp(year=y, month=11, day=1)
        thu = nov + pd.Timedelta(days=(3 - nov.dayofweek) % 7) + pd.Timedelta(days=21)   # 4th Thursday
        assert thu.month == 11 and 22 <= thu.day <= 28, f"Thanksgiving {y} computed as {thu.date()}"
        fri = thu + pd.Timedelta(days=1)
        xeve = pd.Timestamp(year=y, month=12, day=24)
        for label, d in (("day after Thanksgiving", fri), ("Christmas Eve", xeve)):
            k = d.strftime("%Y-%m-%d")
            if k not in es.index:
                continue
            r = es.loc[k]
            weekday = d.dayofweek < 5
            traded = bool(r["is_trading"])
            need = weekday and traded
            got = bool(r["is_early_close"])
            rows.append(dict(year=y, what=label, day=k, weekday=weekday, traded=traded,
                             is_early_close=got, close_et=r["session_close_et"], required=need))
            ok &= (got if need else True)
    return dict(rule="ES is_early_close on the day after Thanksgiving and on Christmas Eve, in every year 2016+ "
                     "in which that date is a weekday ES traded",
                threshold="required=True implies is_early_close=True", measured=rows, passes=bool(ok))


def g3_full_bars(cal: pd.DataFrame) -> dict:
    """A full ES session is 390 bars. Gated on the modal count and on the share of ordinary sessions."""
    es = cal[(cal["root"] == "ES") & cal["is_trading"] & ~cal["is_early_close"] & (cal["day"] >= G1_FROM)]
    mode = int(es["rth_bars"].mode().iloc[0])
    share = float((es["rth_bars"] == FULL_SESSION_BARS_INDEX).mean())
    short = es[es["rth_bars"] < FULL_SESSION_BARS_INDEX]
    return dict(rule=f"ES rth_bars == {FULL_SESSION_BARS_INDEX} on an ordinary session",
                threshold=f"modal count == {FULL_SESSION_BARS_INDEX} and share >= 0.97",
                measured=dict(modal_rth_bars=mode, share_at_390=round(share, 4), n_sessions=int(len(es)),
                              n_below=int(len(short)),
                              below=[(d, int(n)) for d, n in zip(short["day"], short["rth_bars"])][:40]),
                passes=bool(mode == FULL_SESSION_BARS_INDEX and share >= 0.97))


def g4_rolls(cal: pd.DataFrame, rolls: pd.DataFrame) -> dict:
    """roll_day reproduces fut_sessions_rolls.csv.gz exactly, per root, both ways."""
    out, ok = {}, True
    for r in sorted(rolls["root"].unique()):
        want = set(rolls.loc[rolls["root"] == r, "day"])
        got = set(cal.loc[(cal["root"] == r) & cal["roll_day"], "day"])
        out[r] = dict(n_rolls_fixture=len(want), n_roll_day=len(got),
                      in_fixture_not_flagged=sorted(want - got), flagged_not_in_fixture=sorted(got - want))
        out[r]["passes"] = bool(want == got)
        ok &= out[r]["passes"]
    return dict(rule="the roll_day column equals fut_sessions_rolls.csv.gz, per root",
                threshold="set equality on all 9 roots the rolls fixture covers",
                measured=out, passes=bool(ok))


def g5_special(cal: pd.DataFrame, rejected: list) -> dict:
    """The sessions data-available.md warns about are handled as documented and counted."""
    m = {}
    es = cal[cal["root"] == "ES"].set_index("day")
    cb = {}
    # data-available.md names three March-2020 sessions with no continuous open. A FOURTH ES session
    # that month is equally incomplete -- 2020-03-18, the 12:56 ET halt -- and is gated with them.
    for d in ("2020-03-09", "2020-03-12", "2020-03-16", "2020-03-18"):
        r = es.loc[d]
        cb[d] = dict(is_trading=bool(r["is_trading"]), is_early_close=bool(r["is_early_close"]),
                     rth_bars=(int(r["rth_bars"]) if r["rth_bars"] is not pd.NA else None),
                     close_et=r["session_close_et"])
    m["march_2020_circuit_breakers"] = cb
    m["march_2020_note"] = ("docs/data-available.md names 2020-03-09, 12 and 16. 2020-03-18 is a fourth ES "
                            "session of the same shape -- 377 of 390 bars, a full 09:00-15:59 band with an "
                            "interior hole -- and it is gated here with the other three.")
    ok = all(v["is_trading"] and not v["is_early_close"] and v["rth_bars"] < FULL_SESSION_BARS_INDEX for v in cb.values())

    r = es.loc["2021-05-31"]
    m["2021-05-31_memorial_day"] = dict(is_trading=bool(r["is_trading"]), is_early_close=bool(r["is_early_close"]),
                                        close_et=r["session_close_et"],
                                        note="a real abbreviated 09:00-13:00 ET session in the minute bars; the "
                                             "HOURLY breadth fixture cannot form a row for it and no root settles")
    ok &= bool(r["is_trading"] and r["is_early_close"])

    rj = {x["day"]: x for x in rejected}
    m["archive_truncations_rejected"] = [rj[d] for d in ("2020-06-30", "2020-02-27") if d in rj]
    ok &= all(d in rj for d in ("2020-06-30", "2020-02-27"))
    m["n_short_days_rejected"] = len(rejected)

    bt = cal[(cal["root"] == "BTC") & cal["is_trading"]]
    we = bt[pd.to_datetime(bt["day"]).dt.dayofweek >= 5]
    other = cal[(cal["root"] != "BTC") & cal["is_trading"]]
    other_we = other[pd.to_datetime(other["day"]).dt.dayofweek >= 5]
    m["btc_weekend_sessions"] = dict(n=int(len(we)), first=(we["day"].min() if len(we) else None),
                                     last=(we["day"].max() if len(we) else None),
                                     n_early_close=int(we["is_early_close"].sum()),
                                     other_roots_with_weekend_sessions=int(len(other_we)))
    ok &= bool(len(we) > 0 and we["day"].min() >= "2026-05-01" and int(we["is_early_close"].sum()) == 0 and len(other_we) == 0)
    return dict(rule="the five documented special cases are classified as described and counted",
                threshold="circuit breakers trade and are not early closes with rth_bars < 390; 2021-05-31 is a "
                          "trading early close; both archive truncations are rejected short days; BTC weekend "
                          "sessions exist from 2026 and are not early closes, and no other root has one",
                measured=m, passes=bool(ok))


def g6_cme_page(accepted: dict, holidays: dict | None) -> dict:
    """Cross-check the derived calendar against a sourced CME holiday page for 2016+.

    `holidays` is {day: label} parsed from cmegroup.com. Every disagreement is LISTED, in both
    directions, and never silently resolved. When the page could not be fetched the gate does not
    run and does not pass: it is reported `not_fetched` with every attempt, its URL and its time.
    """
    if not holidays:
        return dict(rule="every derived market-wide early close from 2016 on appears on the CME holiday "
                         "calendar, and every CME modified-schedule day from 2016 on is derived",
                    threshold="no disagreement in either direction",
                    status="not_fetched", attempts=CME_FETCH_ATTEMPTS, measured=None, passes=None)
    der = {d for d in accepted if d >= G1_FROM}
    src = {d for d in holidays if d >= G1_FROM}
    dis = ([dict(day=d, derived="early close", cme=None) for d in sorted(der - src)] +
           [dict(day=d, derived=None, cme=holidays[d]) for d in sorted(src - der)])
    return dict(rule="every derived market-wide early close from 2016 on appears on the CME holiday calendar, "
                     "and every CME modified-schedule day from 2016 on is derived",
                threshold="no disagreement in either direction", status="sourced",
                measured=dict(n_derived=len(der), n_cme=len(src), n_agree=len(der & src)),
                disagreements=dis, passes=bool(not dis))


def check_required(meta: dict) -> None:
    """Declared outputs need a guard, not prose: nothing is written until every key is present."""
    missing = [k for k in REQUIRED_OUTPUTS if k not in meta]
    assert not missing, f"REQUIRED_OUTPUTS missing from the meta, refusing to write: {missing}"


def run_gates(cal, rolls, accepted, rejected, holidays):
    g = {"G1": g1_holidays(cal), "G2": g2_early_close(cal), "G3": g3_full_bars(cal),
         "G4": g4_rolls(cal, rolls), "G5": g5_special(cal, rejected), "G6": g6_cme_page(accepted, holidays)}
    ran = [k for k, v in g.items() if v["passes"] is not None]
    return g, ran


# ------------------------------------------------------------------------------------- build
def cmd_build(events_path: Path | None, holidays_path: Path | None):
    t0 = time.time()
    roots, sess, prof = load_day1m()
    log(f"  day1m: {len(sess):,} root-sessions over {len(roots)} roots  ({time.time()-t0:.0f}s)")
    breadth = pd.read_csv(BREADTH, usecols=["root", "day", "contract", "same_front"], dtype={"day": str}, encoding="utf-8")
    idx = pd.read_csv(IDXSESS, usecols=["root", "day", "bars"], dtype={"day": str}, encoding="utf-8")
    rolls = pd.read_csv(ROLLS, dtype={"day": str}, encoding="utf-8")
    events, esrc = load_events(events_path)
    exp, exp_src = expiry_map()
    holidays = json.loads(holidays_path.read_text(encoding="utf-8")) if holidays_path else None
    last_day = max(breadth["day"].max(), sess["day"].max())

    cal, bands, accepted, rejected, qw = assemble(roots, sess, prof, breadth, idx, events, exp, last_day)
    log(f"  assembled {len(cal):,} rows, {int(cal['is_trading'].sum()):,} trading  ({time.time()-t0:.0f}s)")
    gates, ran = run_gates(cal, rolls, accepted, rejected, holidays)
    for k in sorted(gates):
        log(f"    {k}: {gates[k]['passes']}  {gates[k]['rule'][:88]}")

    meta = {
        "spec": SPEC,
        "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "builder": "scripts/build_cme_session_calendar.py",
        "rows": int(len(cal)),
        "roots": roots,
        "span": [cal["day"].min(), cal["day"].max()],
        "row_grid": "one row per (root, ET calendar day) from the root's first day in fut_breadth_hourly to the "
                    "last day in the panel, weekends and holidays included. A calendar is a fact, so it is not "
                    "windowed to any study's in-sample slice.",
        "columns": {
            "is_trading": "the root has at least one 09:00-15:59 ET minute bar with volume > 0 in fut_day1m.parquet",
            "session_open_et": "that day's first traded minute, floored at the root's band open (HH:MM ET)",
            "session_close_et": "that day's last traded minute, capped at the root's regular-session close (HH:MM ET)",
            "rth_bars": "ES/NQ/YM/RTY: fut_index_sessions.bars, the 09:30-15:59 count, 390 on a full session. "
                        "The other 32 roots: traded minutes inside the root's OWN band, so the scale differs by root",
            "is_early_close": "the root stopped >= 30 min before its band close ON A DAY THE COMPLEX WAS SHORT",
            "front_contract": "fut_breadth_hourly.contract, joined, never re-elected",
            "roll_day": "fut_breadth_hourly.same_front == False; the front changed at or during the session",
            "expiry_day": "SOME listed contract of this root expires this ET day (the root's expiry calendar)",
            "days_to_expiry": "calendar days (not sessions) from this day to the FRONT contract's expiry -- a "
                              "different object from expiry_day, see flag_notes",
            "quad_witching": "an ES expiry falling in March, June, September or December",
            "month_end": "the root's OWN last trading day of that ET month",
            "quarter_end": "the root's OWN last trading day of that ET quarter",
            "fomc": "scheduled FOMC statement day", "cpi": "CPI release day", "empsit": "employment situation release day",
            "dst_transition_week": "the ET Mon-Sun week containing a US DST transition",
        },
        "sources": {
            "day1m": str(DAY1M.relative_to(REPO)), "breadth": str(BREADTH.relative_to(REPO)),
            "index_sessions": str(IDXSESS.relative_to(REPO)), "rolls": str(ROLLS.relative_to(REPO)),
            "expiries": {"path": str(EXPIRIES.relative_to(REPO)), "source": exp_src,
                         "resolve": "the nearest expiry at or after the session date; single-digit year codes are "
                                    "recycled, so a symbol carries several (D581)"},
            "events": esrc,
            "cme_holiday_page": {"status": ("sourced" if holidays else "not_fetched"), "attempts": CME_FETCH_ATTEMPTS},
        },
        "bands": {"rule": f"open = the modal first traded minute; close = the settlement volume cliff "
                          f"(v[m] >= {CLIFF_RATIO}x the mean of the next {CLIFF_W} minutes and >= "
                          f"{CLIFF_MIN_SHARE} of the root's busiest minute, profile measured from {CLIFF_FROM}), "
                          f"or the 15:59 window edge where no minute qualifies",
                  "per_root": bands},
        "early_close_rule": {"short": f"the day's last traded minute is >= {SHORT_MIN} min before the band close",
                             "market_wide": f">= {WIDE_MIN_ROOTS} roots trading, >= {WIDE_MIN_SHORT} of them short, "
                                            f">= {WIDE_CONC} of the short stops within {CONC_TOL} min of their mode, "
                                            f"and that mode is the minute before a {BOUNDARY}-minute boundary",
                             "n_days": len(accepted),
                             "known_false_positives": "2010-07-26 and 2010-08-23 are accepted with four short "
                                                      "roots -- CL HO NG RB, stopping at 13:29/13:30. They belong "
                                                      "to the same early-archive pattern as the 31 NYMEX Mondays "
                                                      "the boundary rule rejects (2010-06-07 to 2011-01-18) and "
                                                      "are almost certainly archive, not calendar; they pass only "
                                                      "because the modal stop landed one minute earlier. The rule "
                                                      "is NOT tuned to exclude them -- that would be a threshold "
                                                      "chosen after seeing the answer -- so they are named here.",
                             "days": accepted},
        "flag_notes": {},
        "dropped_buckets": {},
        "special_sessions": {},
        "holiday_disagreements": (gates["G6"].get("disagreements") if holidays else "not_fetched -- G6 did not run"),
        "gates": gates,
        "all_gates_pass": bool(all(gates[k]["passes"] for k in ran)),
        "gates_not_run": [k for k in gates if gates[k]["passes"] is None],
        "files": {"fixture": str(OUT.relative_to(REPO)), "meta": str(META.relative_to(REPO))},
    }

    # the habit of fut_day1m.meta.json: a paragraph per flag saying what it does NOT mean
    first_clean = {r: bands[r]["sessions"] for r in roots}
    meta["flag_notes"] = {
        "is_trading": "is_trading=False does NOT mean the exchange was shut. It means this archive holds no "
                      "09:00-15:59 ET minute bar with volume for that root that day, and before a root's clean "
                      "start the archive is the binding constraint, not the calendar: the day session is missing "
                      "on most days before 2016 for ES/NQ/YM (21% coverage in 2010, 89% in 2015 -- D462 G5), SR3 "
                      "is clean only from 2022 and PA never reaches a full fill. Read is_trading as a calendar "
                      "fact only from the root's own first clean year in fut_day5m.meta.json.",
        "session_close_et": "NOT the last minute the root can be traded. For the six FX and six Treasury roots "
                            "the derived close is the 15:00 ET SETTLEMENT, after which Globex runs to 17:00 and "
                            "the fixture still carries bars to 15:59 -- D530 measured 11.0% of ZN's session volume "
                            "and 11.6% of ZB's in the 15:00-16:00 hour. For the index roots it is the 15:59 window "
                            "edge, not a close at all: their session ends at 16:00, outside this fixture. It IS "
                            "the regular-session close for the metals (13:00-13:30), energy (14:30), grains "
                            "(14:20) and livestock (14:00, which trade five more minutes to 14:05).",
        "rth_bars": "NOT comparable across roots. On ES/NQ/YM/RTY it is the committed 09:30-15:59 count from "
                    "fut_index_sessions (390 full). On the other 32 it is traded minutes inside that root's own "
                    "band, so a full CL session is ~330 and a full ZC session ~290. Compare a root with itself.",
        "is_early_close": "NOT 'this root had a short day'. A root that simply did not trade late is short but not "
                          "flagged; the flag needs the complex to have been short on a boundary-aligned minute. "
                          "That is deliberate -- the two causes need opposite treatment (the fetch_etf_intraday "
                          "_half_days pattern) -- and every short day the rule rejects is listed below.",
        "month_end / quarter_end": "the root's own last OBSERVED trading day, so inside the archive gap it can "
                                   "name the last day the archive holds rather than the last day the market "
                                   "traded. And a month-end here is not a settlement day: 2021-05-31 and "
                                   "2020-06-30 are in this calendar and neither settles (D556, D564).",
        "fomc / cpi / empsit": "EMPTY, not False, outside the sourced span. The JSON covers FOMC 2016-01-27 to "
                               "2024-12-18 and CPI/employment 2016 to 2023-12; every row outside that window "
                               "carries a null so a reader cannot mistake absent sourcing for an absent release. "
                               "fomc is the SCHEDULED statement day only; the three unscheduled meetings "
                               "(2019-10-04, 2020-03-03, 2020-03-15) are not folded in.",
        "quad_witching": "taken from the ES expiry list, not from the third-Friday rule, because the two differ: "
                         "2026-06-18 is a THURSDAY expiry because the third Friday of June 2026 is Juneteenth. "
                         "It is a day-level flag, True on every root's row, including roots that did not trade.",
        "expiry_day / days_to_expiry": "NOT the same object, and expiry_day is NOT days_to_expiry == 0. "
                                       "expiry_day is the ROOT's expiry calendar -- any listed contract expiring "
                                       "that ET day, which for CL or the grains is most months and for ES is "
                                       "quarterly. days_to_expiry is the FRONT contract's, in CALENDAR days not "
                                       "sessions, and the front is elected by volume and rolls one to two weeks "
                                       "early, so it essentially never reaches zero: the minimum reached per root "
                                       "is recorded in days_to_expiry_min_per_root below. On a roll day it jumps "
                                       "to the new front's expiry rather than counting down to the old one's.",
    }
    meta["dropped_buckets"] = {
        "breadth_root_days_with_no_day_session": int(len(breadth) - len(sess)),
        "note": "fut_breadth_hourly carries 170,643 root-days on an 18:00-16:59 session, including a placeholder "
                "row for every Sunday; fut_day1m holds only the 135,179 with a 09:00-15:59 bar. The difference is "
                "is_trading=False here and is front-loaded exactly where the archive gap is.",
        "short_days_rejected_by_the_boundary_rule": rejected,
    }
    meta["special_sessions"] = gates["G5"]["measured"]
    meta["quad_witching_days"] = sorted(d for d in qw if cal["day"].min() <= d <= cal["day"].max())
    meta["quad_witching_days_outside_the_span"] = sorted(d for d in qw if not cal["day"].min() <= d <= cal["day"].max())
    meta["quad_witching_days_with_no_ES_day_session"] = sorted(
        d for d in qw if d <= last_day and not bool(cal[(cal["root"] == "ES") & (cal["day"] == d)]["is_trading"].any()))
    meta["sessions_per_root"] = first_clean
    tr = cal[cal["is_trading"]]
    meta["days_to_expiry_min_per_root"] = {r: (int(v) if v == v else None) for r, v in
                                           tr.groupby("root")["days_to_expiry"].min().items()}
    meta["flag_counts"] = {c: int(tr[c].sum()) for c in ("is_early_close", "roll_day", "expiry_day",
                                                         "quad_witching", "month_end", "quarter_end",
                                                         "dst_transition_week")}
    meta["flag_counts"]["is_trading"] = int(cal["is_trading"].sum())
    meta["flag_counts"]["non_trading_rows"] = int((~cal["is_trading"]).sum())
    for f in ("fomc", "cpi", "empsit"):
        meta["flag_counts"][f] = dict(true=int(cal[f].fillna(False).sum()), null_unsourced=int(cal[f].isna().sum()))

    check_required(meta)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    buf = cal.to_csv(index=False, lineterminator="\n", encoding="utf-8").encode()   # pin the newline before compressing (D550)
    with gzip.GzipFile(OUT, "wb", mtime=0) as fh:
        fh.write(buf)
    META.write_text(json.dumps(meta, indent=1), encoding="utf-8")
    log(f"\nwrote {OUT.relative_to(REPO)} ({len(cal):,} rows) and {META.relative_to(REPO)} in {(time.time()-t0)/60:.1f} min")
    log(f"ALL GATES {'PASS' if meta['all_gates_pass'] else 'FAIL'} (ran {ran}; not run {meta['gates_not_run']})")
    return meta["all_gates_pass"]


# ------------------------------------------------------------------------------------- selftest
def _synth():
    """A two-root, hand-built calendar: one index root on a 15:59 band, one grain root on a 14:19 band.

    The days are the real shapes this fixture has to get right: an ordinary session; Thanksgiving,
    which IS a trading day on CME (09:00-13:00 ET) however closed the cash market is; the day after
    it, a market-wide 13:15 close; Christmas Day, a full closure; a roll; and Christmas Eve on a
    Tuesday. Every gate has to pass this and raise on a break of it.
    """
    rows = [
        # root day            trading open   close  rth  early  front  roll
        ("ES", "2019-11-27", True, "09:00", "15:59", 390, False, "ESZ9", False),
        ("ES", "2019-11-28", True, "09:00", "12:59", 210, True, "ESZ9", False),
        ("ES", "2019-11-29", True, "09:00", "13:14", 225, True, "ESZ9", False),
        ("ES", "2019-12-12", True, "09:00", "15:59", 390, False, "ESH0", True),
        ("ES", "2019-12-13", True, "09:00", "15:59", 390, False, "ESH0", False),
        ("ES", "2019-12-24", True, "09:00", "13:14", 225, True, "ESH0", False),
        ("ES", "2019-12-25", False, None, None, None, False, "ESH0", False),
        ("ZC", "2019-11-27", True, "09:30", "14:19", 290, False, "ZCH0", False),
        ("ZC", "2019-11-28", False, None, None, None, False, "ZCH0", False),
        ("ZC", "2019-11-29", True, "09:30", "12:04", 155, True, "ZCH0", False),
        ("ZC", "2019-12-12", True, "09:30", "14:19", 290, False, "ZCH0", False),
        ("ZC", "2019-12-13", True, "09:30", "14:19", 290, False, "ZCH0", False),
        ("ZC", "2019-12-24", True, "09:30", "13:04", 215, True, "ZCH0", False),
        ("ZC", "2019-12-25", False, None, None, None, False, "ZCH0", False),
    ]
    cal = pd.DataFrame(rows, columns=["root", "day", "is_trading", "session_open_et", "session_close_et",
                                      "rth_bars", "is_early_close", "front_contract", "roll_day"])
    cal["rth_bars"] = cal["rth_bars"].astype("Int64")
    for c in ("expiry_day", "quad_witching", "month_end", "quarter_end", "dst_transition_week"):
        cal[c] = False
    cal["days_to_expiry"] = pd.array([None] * len(cal), dtype="Int64")
    for c in ("fomc", "cpi", "empsit"):
        cal[c] = pd.array([None] * len(cal), dtype="boolean")
    return cal[list(COLUMNS)]


def cmd_selftest():
    log(f"{SPEC} selftest -- every check passes a clean case and RAISES on a deliberate break\n")

    log("  timezone (the only clock this fixture has):")
    for utc, want, zone in (("2019-01-15 14:30", "09:30", "EST"), ("2019-07-15 13:30", "09:30", "EDT")):
        got = pd.Timestamp(utc, tz="UTC").tz_convert(TZ)
        assert got.strftime("%H:%M") == want and got.tzname() == zone, f"{utc} UTC -> {got}, wanted {want} {zone}"
        log(f"    {utc} UTC -> {got.strftime('%H:%M')} {got.tzname()}")
    # the break is the mistake this guards: leaving the stamp in UTC, which reads 09:30 as 14:30 in January
    expect_raise(lambda: _assert_eq(pd.Timestamp("2019-01-15 14:30", tz="UTC").strftime("%H:%M"), "09:30",
                                    "a bar left in UTC was read as an ET wall clock"),
                 "reading the bar in UTC instead of ET")
    # ... and the other half: a fixed -5 offset all year, which puts the July open at 08:30
    expect_raise(lambda: _assert_eq(pd.Timestamp("2019-07-15 13:30", tz="UTC").tz_convert("Etc/GMT+5").strftime("%H:%M"),
                                    "09:30", "a fixed EST offset was used through the summer"),
                 "a DST-blind fixed -5 offset")

    log("\n  the bar index -> ET clock:")
    assert hhmm(0) == "09:00" and hhmm(389) == "15:29" and hhmm(N_BARS - 1) == "15:59", "bar index maps wrong"
    log(f"    bar 0 -> {hhmm(0)} , bar {N_BARS-1} -> {hhmm(N_BARS-1)}")

    log("\n  the settlement cliff:")
    v = np.zeros(N_BARS)
    v[0:330] = 100.0
    v[329] = 2000.0
    v[330:] = 20.0
    bar, ratio = band_close_from_profile(v)
    assert bar == 329 and ratio > CLIFF_RATIO, f"clean cliff at 14:29 read as {hhmm(bar)} ratio {ratio}"
    log(f"    a 14:29 settlement spike is read as {hhmm(bar)} (ratio {ratio:.1f})")
    flat = np.full(N_BARS, 100.0)
    bar2, ratio2 = band_close_from_profile(flat)
    assert bar2 == N_BARS - 1 and ratio2 is None, f"a flat profile must fall back to the window edge, got {hhmm(bar2)}"
    log(f"    a flat profile falls back to the window edge {hhmm(bar2)} with no cliff")
    expect_raise(lambda: _assert_eq(band_close_from_profile(np.zeros(N_BARS - 1))[0], 329,
                                   "a profile of the wrong length"), "a profile that is not 420 minutes")
    expect_raise(lambda: _assert_eq(band_close_from_profile(flat)[0], 329,
                                   "a flat profile must not report a cliff"), "a flat profile read as a 14:29 close")

    log("\n  the early-close rule (the break must hit the scalar compared):")
    n = 12
    base = pd.DataFrame({"root": [f"R{i}" for i in range(n)], "day": "2019-11-29",
                         "last": [254] * 6 + [419] * 6, "band_close": [419] * n})
    acc, rej = market_wide_early_closes(base)
    assert "2019-11-29" in acc, "a six-of-twelve 13:14 stop is an early close"
    log(f"    six of twelve stopping at 13:14 -> accepted {acc['2019-11-29']}")
    drop = base.copy()
    drop["last"] = [70] * 6 + [419] * 6          # 10:10, the 2020-06-30 shape: not on a 5-minute boundary
    acc2, rej2 = market_wide_early_closes(drop)
    assert not acc2 and len(rej2) == 1 and not rej2[0]["on_five_minute_boundary"], "a 10:10 dropout must be rejected"
    log(f"    six of twelve stopping at 10:10 -> rejected: {rej2[0]['modal_stop_et']}, boundary "
        f"{rej2[0]['on_five_minute_boundary']}")
    thin = base.copy()
    thin["last"] = [254] * 2 + [419] * 10        # only two short: a thin root, not a calendar fact
    assert not market_wide_early_closes(thin)[0], "two short roots is liquidity, not a calendar"
    log("    two of twelve stopping at 13:14 -> not an early close (liquidity, not the calendar)")
    expect_raise(lambda: _assert_eq(len(market_wide_early_closes(drop)[0]), 1,
                                   "a 10:10 feed dropout became an early close"), "a dropout classified as a close")
    expect_raise(lambda: _assert_eq(len(market_wide_early_closes(thin)[0]), 1,
                                   "a two-root short day became an early close"), "a thin root classified as a close")

    log("\n  the holiday rule:")
    h = full_closure_days([2021, 2022])
    assert h.get("2021-12-24") == "Christmas Day", "Christmas on a Saturday is taken on the Friday"
    assert "2021-12-31" not in h, "New Year's on a Saturday is NOT taken on the preceding Friday"
    assert h.get("2021-04-02") == "Good Friday" and h.get("2022-04-15") == "Good Friday", "Good Friday is Easter - 2"
    log(f"    2021: {sorted(k for k in h if k.startswith('2021'))}")
    log(f"    2022: {sorted(k for k in h if k.startswith('2022'))}")
    expect_raise(lambda: _assert_eq(full_closure_days([2022]).get("2021-12-31"), "New Year's Day",
                                   "a symmetric observance rule closed 2021-12-31"), "a symmetric observance rule")

    log("\n  DST:")
    w = dst_transition_weeks(pd.DatetimeIndex(pd.date_range("2019-01-01", "2019-12-31")))
    assert "2019-03-10" in w and "2019-03-16" in w and "2019-03-17" not in w, f"March DST week wrong: {sorted(w)}"
    assert "2019-11-03" in w and "2019-11-09" in w and "2019-03-04" not in w, f"November DST week wrong: {sorted(w)}"
    assert len(w) == 14, f"two transitions, seven days each: {sorted(w)}"
    log(f"    2019 -> {sorted(w)}")
    expect_raise(lambda: _assert_eq("2019-03-04" in w, True,
                                    "the week BEFORE the March transition was marked"), "an off-by-one-week DST mark")
    expect_raise(lambda: _assert_eq(len(dst_transition_weeks(
        pd.DatetimeIndex(pd.date_range("2019-04-01", "2019-09-30")))), 14,
        "a span with no transition reported two"), "DST weeks found in a span that has none")

    log("\n  the gates, on a synthetic calendar:")
    cal = _synth()
    r = pd.DataFrame([dict(root="ES", day="2019-12-12", from_contract="ESZ9", to_contract="ESH0",
                           from_volume=1, to_volume=2)])
    g4 = g4_rolls(cal, r)
    assert g4["passes"], f"G4 must pass a clean case: {g4}"
    log(f"    G4 clean: {g4['measured']['ES']}")
    broken = cal.copy()
    broken.loc[(broken["root"] == "ES") & (broken["day"] == "2019-12-12"), "roll_day"] = False
    expect_raise(lambda: _assert_eq(g4_rolls(broken, r)["passes"], True, "G4 passed with the roll flag cleared"),
                 "G4 with the roll day cleared")

    g3 = g3_full_bars(cal)
    assert g3["passes"], f"G3 must pass a clean case: {g3}"
    log(f"    G3 clean: modal {g3['measured']['modal_rth_bars']} share {g3['measured']['share_at_390']}")
    b3 = cal.copy()
    b3.loc[(b3["root"] == "ES") & (b3["day"] == "2019-11-27"), "rth_bars"] = 389
    b3.loc[(b3["root"] == "ES") & (b3["day"] == "2019-12-12"), "rth_bars"] = 388
    b3.loc[(b3["root"] == "ES") & (b3["day"] == "2019-12-13"), "rth_bars"] = 387
    expect_raise(lambda: _assert_eq(g3_full_bars(b3)["passes"], True, "G3 passed on a 387-bar ES session"),
                 "G3 with the ES bar count broken")

    g2 = g2_early_close(cal)
    assert g2["passes"], f"G2 must pass a clean case: {g2}"
    log(f"    G2 clean: {[r_['day'] for r_ in g2['measured'] if r_['required']]}")
    b2 = cal.copy()
    b2.loc[(b2["root"] == "ES") & (b2["day"] == "2019-11-29"), "is_early_close"] = False
    expect_raise(lambda: _assert_eq(g2_early_close(b2)["passes"], True,
                                   "G2 passed with the Thanksgiving-Friday flag cleared"),
                 "G2 with the day-after-Thanksgiving flag cleared")

    g1 = g1_holidays(cal)
    log(f"    G1 clean: 2019-12-25 is the one holiday weekday in the span and it is the one non-trading day "
        f"-> passes={g1['passes']}")
    b1 = cal.copy()
    b1.loc[(b1["root"] == "ES") & (b1["day"] == "2019-12-13"), "is_trading"] = False
    expect_raise(lambda: _assert_eq(g1_holidays(b1)["passes"], True,
                                   "G1 passed with a non-holiday weekday closed"),
                 "G1 with an ordinary Friday marked non-trading")

    g6 = g6_cme_page({"2019-11-29": {}, "2019-12-24": {}}, {"2019-11-29": "day after Thanksgiving"})
    assert not g6["passes"] and len(g6["disagreements"]) == 1, f"G6 must list the disagreement: {g6}"
    log(f"    G6 with a one-day disagreement: passes={g6['passes']} listed={g6['disagreements']}")
    g6b = g6_cme_page({"2019-11-29": {}}, {"2019-11-29": "day after Thanksgiving"})
    assert g6b["passes"], "G6 must pass when the two agree"
    log("    G6 with agreement: passes=True")
    assert g6_cme_page({"2019-11-29": {}}, None)["passes"] is None, "an unfetched G6 must not report a pass"
    log("    G6 unsourced: passes=None, status=not_fetched (it does not pass and it does not fail silently)")
    expect_raise(lambda: _assert_eq(g6_cme_page({"2019-11-29": {}, "2019-12-24": {}},
                                                {"2019-11-29": "x"})["passes"], True,
                                   "G6 passed with a day the CME page does not carry"), "G6 with a disagreement")

    log("\n  REQUIRED_OUTPUTS:")
    check_required({k: None for k in REQUIRED_OUTPUTS})
    log(f"    a complete meta passes; {len(REQUIRED_OUTPUTS)} keys are checked before the fixture is written")
    expect_raise(lambda: check_required({k: None for k in REQUIRED_OUTPUTS if k != "gates"}),
                 "a meta written without its gates block")
    log("\nSELFTEST PASS")
    return True


def _assert_eq(got, want, msg):
    assert got == want, f"{msg} (got {got!r}, wanted {want!r})"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--build", action="store_true")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--events", type=Path, default=None, help="CSV of datetime_et,event replacing macro_release_calendar.json")
    p.add_argument("--holidays", type=Path, default=None, help="JSON {day: label} parsed from the CME holiday calendar, for G6")
    a = p.parse_args()
    if a.selftest:
        return 0 if cmd_selftest() else 1
    if a.build:
        return 0 if cmd_build(a.events, a.holidays) else 1
    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
