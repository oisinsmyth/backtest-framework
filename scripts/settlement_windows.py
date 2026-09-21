"""D586 -- the CME settlement-window table, with effective dates, and the loader that RAISES
rather than guess.

    uv run python scripts/settlement_windows.py --selftest            # G1..G6 pass a clean case AND raise on a deliberate break
    uv run --with pyarrow python scripts/settlement_windows.py --measure   # volume share inside each window vs its 5-minute flanks
    uv run python scripts/settlement_windows.py --selftest --measure  # both, then write data/settlement_windows.meta.json

The table is `data/settlement_windows.csv`, one row per (root, effective period). NOTHING in this
module hardcodes a window: every time comes off that file, every row carries the URL it was read
from, and a product with no row is UNMAPPED -- `window_for` raises for it rather than falling back
to a default. The ledger doc's "about 14:28-14:30 ET for NG and CL" was a hypothesis; it is
confirmed here for the ACTIVE month by SER-4867, and it is EASTERN time, not Central.

`history_status` is one of:
  dated_notice   a Special Executive Report or market notice gives the change date; `effective_from`
                 is that date and `window_for` serves the row from it.
  current_only   only the present procedure page was found; `effective_from` is the access date,
                 `effective_to` is empty, and history before that date is UNKNOWN -- `window_for`
                 raises below it.
  record_only    a superseded window read verbatim from a dated source whose own start (ES/NQ) or
                 end (the CBOT ags) is NOT sourced. Carried so the record is not lost; NEVER served
                 by `window_for`, and excluded from the G5 overlap check.

Micros inherit their parent's row through MICRO_PARENT, not through duplicate rows.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TABLE = REPO / "data" / "settlement_windows.csv"
META = REPO / "data" / "settlement_windows.meta.json"
FIXTURE = REPO / "data" / "fixtures" / "fut_day1m.parquet"
CACHE = REPO / "temp" / "d586_volume_measurement.json"
SPEC = "D586"

REQUIRED_OUTPUTS = ("spec", "written_utc", "table", "products", "unmapped", "micro_parent",
                    "history", "not_fetched", "gates", "dst_check", "measurement", "timing_s")

#: Micros and minis that settle off a parent's price. Encoded here, NOT as duplicate CSV rows.
MICRO_PARENT = {"MNG": "NG", "MCL": "CL", "MGC": "GC", "SIL": "SI", "MHG": "HG",
                "MES": "ES", "MNQ": "NQ"}

#: Products this table was asked to cover. A product named here with no CSV row is UNMAPPED and the
#: meta must say why -- silence is what "never assume a window" forbids.
PRODUCTS_REQUESTED = ("NG", "CL", "HO", "RB", "GC", "SI", "HG",
                      "ZC", "ZS", "ZW", "KE", "ZL", "ZM", "LE", "HE", "ES", "NQ")

#: The fixture's own band: bar 0 is 09:00 ET, bar 419 is 15:59 ET (data/fixtures/fut_day1m.meta.json).
BAR0_ET_MIN, N_BARS = 9 * 60, 420
MEASURE_YEARS = tuple(range(2016, 2024))
FLANK = 5

SERVED = ("dated_notice", "current_only")
ALL_STATUS = SERVED + ("record_only",)


# ----------------------------------------------------------------------------- the served object
@dataclass(frozen=True)
class SettlementWindow:
    root: str
    exchange: str
    product_name: str
    start_ct: str
    end_ct: str
    start_et: str
    end_et: str
    basis: str
    effective_from: str
    effective_to: str
    history_status: str
    source_url: str
    accessed_utc: str
    notes: str


class UnmappedProduct(KeyError):
    """Raised for a product with no row in the table. Never a silent default."""


class UnsourcedDate(ValueError):
    """Raised for a date before the earliest SOURCED effective date of a mapped product."""


# --------------------------------------------------------------------------------------- loading
def _hhmmss(s: str) -> int:
    h, m, sec = (int(x) for x in s.split(":"))
    if not (0 <= h < 24 and 0 <= m < 60 and 0 <= sec < 60):
        raise ValueError(f"not a clock time: {s!r}")
    return h * 3600 + m * 60 + sec


def _date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def load_rows(path: Path = TABLE) -> list[SettlementWindow]:
    """Read the table. Raises on a malformed row rather than dropping it."""
    with path.open(newline="", encoding="utf-8") as fh:
        raw = list(csv.DictReader(fh))
    if not raw:
        raise ValueError(f"{path} has no rows")
    rows = []
    for i, r in enumerate(raw):
        w = SettlementWindow(
            root=r["root"].strip(), exchange=r["exchange"].strip(),
            product_name=r["product_name"].strip(),
            start_ct=r["window_start_ct"].strip(), end_ct=r["window_end_ct"].strip(),
            start_et=r["window_start_et"].strip(), end_et=r["window_end_et"].strip(),
            basis=r["basis"].strip(), effective_from=r["effective_from"].strip(),
            effective_to=r["effective_to"].strip(), history_status=r["history_status"].strip(),
            source_url=r["source_url"].strip(), accessed_utc=r["accessed_utc"].strip(),
            notes=r["notes"].strip())
        if w.history_status not in ALL_STATUS:
            raise ValueError(f"row {i}: history_status {w.history_status!r} not in {ALL_STATUS}")
        for f in (w.start_ct, w.end_ct, w.start_et, w.end_et):
            _hhmmss(f)
        if _hhmmss(w.end_ct) <= _hhmmss(w.start_ct):
            raise ValueError(f"row {i} ({w.root}): CT window does not advance")
        rows.append(w)
    return rows


def served_rows(rows: list[SettlementWindow] | None = None) -> list[SettlementWindow]:
    return [w for w in (rows if rows is not None else load_rows()) if w.history_status in SERVED]


def earliest_sourced(root: str, rows: list[SettlementWindow] | None = None) -> dt.date:
    served = [w for w in served_rows(rows) if w.root == root]
    if not served:
        raise UnmappedProduct(root)
    return min(_date(w.effective_from) for w in served)


def resolve_root(root: str) -> str:
    """Map a micro to its parent. An unknown symbol is returned unchanged and fails later."""
    return MICRO_PARENT.get(root, root)


def window_for(root: str, date) -> SettlementWindow:
    """The settlement window in force for `root` on `date`.

    RAISES `UnmappedProduct` for a product with no served row (including every micro whose parent
    is unmapped), and `UnsourcedDate` for a date before the product's earliest SOURCED effective
    date -- the case a `current_only` row creates, and the whole point of the file.
    """
    if isinstance(date, str):
        date = _date(date)
    elif isinstance(date, dt.datetime):
        date = date.date()
    if not isinstance(date, dt.date):
        raise TypeError(f"date must be a date or an ISO string, got {type(date).__name__}")

    parent = resolve_root(root)
    rows = load_rows()
    served = [w for w in rows if w.root == parent and w.history_status in SERVED]
    if not served:
        recorded = [w for w in rows if w.root == parent]
        if recorded:
            raise UnmappedProduct(
                f"{root!r} (parent {parent!r}) has only record_only rows: its window is recorded "
                f"but no effective period is sourced, so nothing may be served")
        raise UnmappedProduct(
            f"{root!r} is not in {TABLE.name}; add a SOURCED row before any study reads it")

    floor = min(_date(w.effective_from) for w in served)
    if date < floor:
        raise UnsourcedDate(
            f"{root!r} (parent {parent!r}): {date} is before the earliest sourced effective date "
            f"{floor}. History before it is NOT sourced -- source it, do not assume it")

    hits = [w for w in served
            if _date(w.effective_from) <= date
            and (not w.effective_to or date <= _date(w.effective_to))]
    if len(hits) != 1:
        raise UnsourcedDate(
            f"{root!r} on {date}: {len(hits)} effective periods match, expected exactly 1")
    return hits[0]


# ------------------------------------------------------------------------------------------ bars
def window_bars(w: SettlementWindow) -> tuple[int, int]:
    """The fut_day1m bar indices covering the ET window, inclusive.

    A sub-minute window (livestock 30 s, equity 30 s) maps to the ONE minute containing it: the
    1-minute fixture cannot resolve it, and that is stated rather than papered over.
    """
    s, e = _hhmmss(w.start_et) // 60, _hhmmss(w.end_et) // 60
    b0 = s - BAR0_ET_MIN
    b1 = (e - 1 if _hhmmss(w.end_et) % 60 == 0 else e) - BAR0_ET_MIN
    return b0, max(b0, b1)


def inside_fixture_band(w: SettlementWindow) -> bool:
    b0, b1 = window_bars(w)
    return 0 <= b0 and b1 < N_BARS


# ----------------------------------------------------------------------------------------- gates
def expect_raise(fn, what, log=print):
    """D581's idiom: a gate that cannot fail is worse than none, so prove each one RAISES."""
    try:
        fn()
    except (AssertionError, UnmappedProduct, UnsourcedDate, ValueError, KeyError) as e:
        log(f"    RAISES on {what}: {type(e).__name__}: {str(e)[:78]}")
        return True
    raise AssertionError(f"gate did not raise on {what}")


def g1_every_row_sourced(rows):
    for w in rows:
        assert w.source_url.startswith("https://"), f"{w.root}: no source_url"
        assert w.accessed_utc.endswith("Z") and len(w.accessed_utc) == 20, f"{w.root}: accessed_utc"
        assert len(w.basis) > 20, f"{w.root}: basis is not a quoted procedure"
    return len(rows)


def _must_raise(fn, what):
    """G2 and G3 PASS by raising, so the gate asserts the raise happened."""
    try:
        fn()
    except (UnmappedProduct, UnsourcedDate):
        return True
    raise AssertionError(f"window_for did NOT raise on {what}")


def g2_unmapped_raises(rows, probe=("XX", "2023-06-01")):
    return _must_raise(lambda: window_for(*probe), f"the unmapped product {probe[0]!r}")


def g3_before_earliest_raises(rows, root="GC", back=1):
    floor = earliest_sourced(root, rows)
    d = floor - dt.timedelta(days=back)
    return _must_raise(lambda: window_for(root, d), f"{root} on {d}, below its floor {floor}")


def g4_ct_et_is_one_hour(rows):
    for w in rows:
        for ct, et, which in ((w.start_ct, w.start_et, "start"), (w.end_ct, w.end_et, "end")):
            d = (_hhmmss(et) - _hhmmss(ct)) % 86400
            assert d == 3600, f"{w.root} {which}: ET-CT is {d}s, not 3600"
    return len(rows)


def g5_no_overlap(rows):
    for root in {w.root for w in rows}:
        per = sorted((w for w in rows if w.root == root and w.history_status in SERVED),
                     key=lambda w: w.effective_from)
        for a, b in zip(per, per[1:]):
            end = _date(a.effective_to) if a.effective_to else None
            assert end is not None and end < _date(b.effective_from), (
                f"{root}: period from {a.effective_from} is open or overlaps {b.effective_from}")
    return len(rows)


def g6_micros_map(rows):
    mapped = {w.root for w in rows if w.history_status in SERVED}
    for micro, parent in MICRO_PARENT.items():
        assert parent in mapped, f"micro {micro} maps to unmapped parent {parent}"
    return len(MICRO_PARENT)


GATES = (("G1", "every mapped row has a URL, an access time and a basis", g1_every_row_sourced),
         ("G2", "window_for on an unmapped product raises", g2_unmapped_raises),
         ("G3", "window_for before the earliest sourced effective date raises", g3_before_earliest_raises),
         ("G4", "CT->ET is exactly +1 hour on every row", g4_ct_et_is_one_hour),
         ("G5", "no overlapping effective periods within a root", g5_no_overlap),
         ("G6", "every micro maps to a mapped parent", g6_micros_map))


# ------------------------------------------------------- G4's teeth: both DST transition weeks
def _try_zoneinfo():
    from zoneinfo import ZoneInfo
    return ZoneInfo("America/Chicago"), ZoneInfo("America/New_York")


def dst_transition_dates(year: int) -> tuple[dt.date, dt.date]:
    """US DST: second Sunday in March, first Sunday in November."""
    mar = dt.date(year, 3, 1)
    spring = mar + dt.timedelta(days=(6 - mar.weekday()) % 7 + 7)
    nov = dt.date(year, 11, 1)
    fall = nov + dt.timedelta(days=(6 - nov.weekday()) % 7)
    return spring, fall


def dst_audit(rows, years=(2020, 2021, 2022, 2023)) -> dict:
    """ledger unit test 13. CT and ET must stay exactly one hour apart on every day of BOTH
    transition weeks, so the two stored spellings of one window never disagree -- including on the
    Sunday the clocks move and the trade dates either side of it."""
    ct, et = _try_zoneinfo()
    checked, days = 0, []
    for y in years:
        for pivot in dst_transition_dates(y):
            for off in range(-3, 4):
                d = pivot + dt.timedelta(days=off)
                days.append(d.isoformat())
                for w in rows:
                    for cts, ets in ((w.start_ct, w.start_et), (w.end_ct, w.end_et)):
                        h, m, s = (int(x) for x in cts.split(":"))
                        hh, mm, ss = (int(x) for x in ets.split(":"))
                        a = dt.datetime.combine(d, dt.time(h, m, s), tzinfo=ct)
                        b = dt.datetime.combine(d, dt.time(hh, mm, ss), tzinfo=et)
                        assert a == b, (
                            f"{w.root} on {d}: {cts} CT is {a.astimezone(et):%H:%M:%S} ET, "
                            f"not {ets} -- the two spellings disagree")
                        checked += 1
    return {"days": sorted(set(days)), "pairs_checked": checked,
            "years": list(years), "tz": ["America/Chicago", "America/New_York"]}


def run_selftest(log=print) -> dict:
    rows = load_rows()
    out = {}
    log(f"  table {TABLE.name}: {len(rows)} rows, "
        f"{len({w.root for w in served_rows(rows)})} served roots")
    for name, what, fn in GATES:
        fn(rows)
        log(f"  {name} PASS  {what}")
        out[name] = {"what": what, "passed": True}

    log("  -- each gate must be able to FIRE; break what the assertion reads --")
    bad_url = [SettlementWindow(**{**asdict(rows[0]), "source_url": "http://not-https"})]
    expect_raise(lambda: g1_every_row_sourced(bad_url), "G1 / a row with no https source", log)
    expect_raise(lambda: g2_unmapped_raises(rows, probe=("MNG", "2023-06-01")),
                 "G2 / a probe that IS mapped, so the gate's own raise never fires", log)
    expect_raise(lambda: g3_before_earliest_raises(rows, root="NG", back=-1),
                 "G3 / a probe ABOVE the floor, so the gate's own raise never fires", log)
    bad_ct = [SettlementWindow(**{**asdict(rows[0]), "start_ct": "13:29:00"})]
    expect_raise(lambda: g4_ct_et_is_one_hour(bad_ct), "G4 / a row whose CT is not ET-1h", log)
    base = asdict(next(w for w in rows if w.history_status == "dated_notice"))
    dup = [SettlementWindow(**base),
           SettlementWindow(**{**base, "effective_from": "2021-01-01"})]
    expect_raise(lambda: g5_no_overlap(dup), "G5 / two open periods on one root", log)
    expect_raise(lambda: g6_micros_map([w for w in rows if w.root != "NG"]),
                 "G6 / a micro whose parent row is gone", log)
    bad_dst = [SettlementWindow(**{**asdict(rows[0]), "start_et": "12:29:00"})]
    expect_raise(lambda: dst_audit(bad_dst, years=(2023,)),
                 "DST / a row whose ET spelling is an hour wrong", log)
    for name in out:
        out[name]["raises_on_break"] = True

    d = dst_audit(rows)
    log(f"  DST PASS  {d['pairs_checked']} CT/ET pairs over {len(d['days'])} days in both "
        f"transition weeks of {d['years']}")
    return {"gates": out, "dst_check": d}


# ----------------------------------------------------------------------------------- measurement
def run_measure(log=print) -> dict:
    """Share of session volume inside each stated window against the 5 minutes either side.

    Reported, NOT gated: the window is what CME publishes, and a root whose volume does not lift
    inside it is reported as such rather than having its window adjusted to fit the data.
    """
    import pyarrow.parquet as pq

    rows = served_rows()
    t0 = time.time()
    out, skipped = {}, {}
    for w in sorted(rows, key=lambda x: x.root):
        b0, b1 = window_bars(w)
        if not inside_fixture_band(w):
            skipped[w.root] = f"window bars {b0}..{b1} outside the fixture's 0..{N_BARS - 1} band"
            continue
        pre = [b for b in range(b0 - FLANK, b0) if 0 <= b < N_BARS]
        post = [b for b in range(b1 + 1, b1 + 1 + FLANK) if 0 <= b < N_BARS]
        try:
            t = pq.read_table(FIXTURE, columns=["day", "bar", "volume", "present"],
                              filters=[("root", "=", w.root)])
        except Exception as e:  # noqa: BLE001 -- a root absent from the fixture is a fact, not a bug
            skipped[w.root] = f"read failed: {e}"
            continue
        if t.num_rows == 0:
            skipped[w.root] = "root absent from data/fixtures/fut_day1m.parquet"
            continue
        import numpy as np

        day = np.asarray(t.column("day").to_numpy(zero_copy_only=False), dtype="U10")
        bar = t.column("bar").to_numpy(zero_copy_only=False).astype(np.int32)
        vol = t.column("volume").to_numpy(zero_copy_only=False).astype(np.int64)
        pres = t.column("present").to_numpy(zero_copy_only=False).astype(bool)
        year = day.astype("U4").astype(np.int32)
        keep = pres & (year >= MEASURE_YEARS[0]) & (year <= MEASURE_YEARS[-1])
        day, bar, vol, year = day[keep], bar[keep], vol[keep], year[keep]

        in_win = (bar >= b0) & (bar <= b1)
        in_pre = np.isin(bar, pre) if pre else np.zeros(bar.shape, bool)
        in_post = np.isin(bar, post) if post else np.zeros(bar.shape, bool)
        nw, npre, npost = b1 - b0 + 1, len(pre), len(post)

        per_year = {}
        for y in MEASURE_YEARS:
            sel = year == y
            if not sel.any():
                continue
            n = np.unique(day[sel]).size
            tot = int(vol[sel].sum())
            win = int(vol[sel & in_win].sum())
            prv = int(vol[sel & in_pre].sum())
            psv = int(vol[sel & in_post].sum())
            wpm = win / nw / n
            ppm = prv / npre / n if npre else 0.0
            qpm = psv / npost / n if npost else 0.0
            per_year[str(y)] = {
                "sessions": int(n),
                "share_in_window_pct": round(100 * win / tot, 4) if tot else None,
                "share_pre5_pct": round(100 * prv / tot, 4) if (tot and npre) else None,
                "share_post5_pct": round(100 * psv / tot, 4) if (tot and npost) else None,
                "vol_per_min_in": round(wpm, 1), "vol_per_min_pre5": round(ppm, 1),
                "vol_per_min_post5": round(qpm, 1),
                "in_vs_pre5": round(wpm / ppm, 3) if ppm else None,
                "in_vs_post5": round(wpm / qpm, 3) if qpm else None,
                "in_vs_session_mean": round(wpm / (tot / N_BARS / n), 3) if tot else None,
            }
        out[w.root] = {"window_et": f"{w.start_et}-{w.end_et}", "bars": [b0, b1],
                       "window_in_band": True, "sub_minute": nw == 1 and _hhmmss(w.end_et) - _hhmmss(w.start_et) < 60,
                       "pre5_bars": pre, "post5_bars": post,
                       "flank_truncated": "post5 is EMPTY: the window sits on the fixture's last "
                                          "bar (15:59 ET) and the five minutes after it are outside "
                                          "the 09:00-15:59 band" if not post else None,
                       "per_year": per_year}
        log(f"  {w.root:3s} bars {b0}-{b1}  " + "  ".join(
            f"{y}:{per_year[y]['in_vs_pre5']}" for y in sorted(per_year)))
    band = {"fixture_band_et": "09:00-15:59, bar 0..419",
            "windows_inside_band": sorted(r for r in out),
            "windows_outside_band": sorted(skipped),
            "d530_session_ends_et": {"grains": "14:20", "livestock": "14:05", "metals": "13:30",
                                     "energy": "14:30", "equity index": "16:00"},
            "verdict": ("every mapped window falls INSIDE the band, because each one sits at or "
                        "just before its own market's close, which is itself inside 09:00-15:59 "
                        "ET; what falls outside is the POST-window flank of ES and NQ")}
    return {"status": "ok", "years": list(MEASURE_YEARS), "flank_minutes": FLANK, "band": band,
            "fixture": str(FIXTURE.relative_to(REPO)).replace("\\", "/"),
            "fixture_mtime": FIXTURE.stat().st_mtime if FIXTURE.exists() else None,
            "per_root": out, "not_measured": skipped,
            "note": ("volume-weighted shares over present=True bars only; a sub-minute window is "
                     "scored on the ONE minute containing it, which OVERSTATES the window and is "
                     "the conservative direction for a spike claim"),
            "wall_s": round(time.time() - t0, 1)}


# ---------------------------------------------------------------------------------------- output
def write_meta(payload: dict) -> None:
    missing = [k for k in REQUIRED_OUTPUTS if k not in payload]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing before write: {missing}")
    META.write_text(json.dumps(payload, indent=1, sort_keys=False) + "\n", encoding="utf-8")
    print(f"  wrote {META.relative_to(REPO)}")


def build_meta(selftest: dict | None, measurement: dict | None, t0: float) -> dict:
    rows = load_rows()
    served = served_rows(rows)
    mapped = sorted({w.root for w in served})
    return {
        "spec": SPEC,
        "written_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "table": str(TABLE.relative_to(REPO)).replace("\\", "/"),
        "products": {
            "requested": list(PRODUCTS_REQUESTED),
            "mapped": mapped,
            "rows": len(rows),
            "served_rows": len(served),
            "record_only_rows": len(rows) - len(served),
        },
        "unmapped": sorted(set(PRODUCTS_REQUESTED) - set(mapped)),
        "micro_parent": MICRO_PARENT,
        "history": {
            "dated_notice": sorted({w.root for w in rows if w.history_status == "dated_notice"}),
            "current_only": sorted({w.root for w in rows if w.history_status == "current_only"}),
            "record_only": sorted({w.root for w in rows if w.history_status == "record_only"}),
            "earliest_sourced": {r: earliest_sourced(r, rows).isoformat() for r in mapped},
        },
        "not_fetched": {
            "GC SI HG": "no dated notice establishing the COMEX metals windows was found; history "
                        "before 2026-09-21 is UNKNOWN and window_for raises for it",
            "ZC ZS ZW KE ZL ZM": "no dated notice for the move to 13:14:00-13:15:00 CT was found; "
                                 "the 2012 predecessor is carried as record_only",
            "LE HE": "no dated notice for the 12:59:30-13:00:00 CT livestock window was found; "
                     "the December 2014 transition off pit-only settlement is referenced in the "
                     "literature but no CME notice stating the window was located",
            "ES NQ pre-2020": "SER-8591 dates the END of the 15:14:30-15:15:00 CT window but not "
                              "its start; carried as record_only and never served",
            "KE volume": "KE is not among the 36 roots of data/fixtures/fut_day1m.parquet, so it "
                         "carries no volume measurement",
        },
        "gates": (selftest or {}).get("gates", {"status": "not_run"}),
        "dst_check": (selftest or {}).get("dst_check", {"status": "not_run"}),
        "measurement": measurement or {"status": "not_run"},
        "timing_s": round(time.time() - t0, 1),
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selftest", action="store_true", help="run G1..G6 and prove each raises")
    p.add_argument("--measure", action="store_true", help="volume share inside the window vs flanks")
    p.add_argument("--no-write", action="store_true", help="print only; do not touch the meta")
    a = p.parse_args(argv)
    if not (a.selftest or a.measure):
        p.error("nothing to do: pass --selftest and/or --measure")

    t0 = time.time()
    st = m = None
    if a.selftest:
        print("[selftest]")
        st = run_selftest()
    if a.measure:
        print("[measure]")
        m = run_measure()
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8")
    if m is None and CACHE.exists():
        cached = json.loads(CACHE.read_text(encoding="utf-8"))
        if FIXTURE.exists() and cached.get("fixture_mtime") == FIXTURE.stat().st_mtime:
            m = cached
            print(f"  reused {CACHE.relative_to(REPO)} (fixture mtime matches)")
    if not a.no_write:
        write_meta(build_meta(st, m, t0))
    print(f"[done] {round(time.time() - t0, 1)}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
