"""D710: D585's FOMC fetch, extended back to 2010 (the principal's choice (a), 2026-09-30: "Fetch them").

    python scripts/fetch_fomc_2010_2015.py --fetch      # fomchistorical2010..2015 + each statement -> data/raw/fomc_ext/
    python scripts/fetch_fomc_2010_2015.py --build      # reproduce D585 2016-2023 EXACTLY, then write the extension
    python scripts/fetch_fomc_2010_2015.py --selftest   # every gate passes a clean case and RAISES on its own break

WHAT THIS IS
------------
D585's fetcher (`scripts/fetch_release_calendar.py`), imported and UNMODIFIED, pointed at years it never fetched. Its
`acquire`, `read_raw`, `meeting_last_day`, `build_fomc` and `parse_fomc_cal` are used as they are. Two things about the
2010-2015 pages are new, and this file handles them without touching D585's:

1. **The older page layout.** fomchistorical2010 uses `<div class="panel panel-default">` + `<h5>` and links its
   statements by the legacy path /newsevents/press/monetary/20100127a.htm; 2010-2011 carry "Conference Call"
   headings; 2012 writes "July 31-August 1". `parse_hist_ext` reads all of them. It normalises the legacy statement
   path to the canonical /newsevents/pressreleases/monetaryYYYYMMDDa.htm, which is what is fetched and cited.
2. **No clock on the statements.** Every 2010-2015 statement page says "For immediate release"; none states "For
   release at ...", so D585's rule (a row needs a SOURCED clock) cannot be met. D710 needs only the DAY (the whole
   session is excluded). So the extension writes the sourced DATE and leaves `release_clock_et` EMPTY with
   `clock_source = "not stated on the statement page"`. No clock is invented. Its schema is therefore its own, not
   D585's, and it is written beside D585's file, never merged into it.

THE ORDER IS THE RULE (gate R)
------------------------------
Before any 2010-2015 row is used, over D585's OWN raw cache (`data/raw/calendar/`):
  R1 D585's build_fomc with D585's own parser reproduces events.csv's FOMC and FOMC_UNSCHEDULED rows 2016-01-01 ..
     2023-12-31, every column, row for row;
  R2 the same with `parse_hist_ext` in place of D585's parser -- so the extension's parser reproduces 2016-2020 from
     the same fomchistorical pages;
  R3 this file's own date builder (`build_dates`), run on D585's 2016-2020 pages, gives exactly events.csv's
     (date, event) pairs for 2016-2020.
If any of the three fails, the build raises and nothing is written.

OUTPUT (tracked): `data/calendar/fomc_2010_2015.csv` (date_et, event, release_clock_et, clock_source, statement_url,
meeting_panel, meeting_last_day, method, accessed_utc) and `.meta.json`. D710's runner unions its dates with
events.csv's FOMC and FOMC_UNSCHEDULED dates.

GATES (each proven to raise by --selftest)
------------------------------------------
  R   the three reproductions above are exact
  G1  every row has a statement_url, accessed_utc and method 'fetched'
  G2  8 scheduled FOMC statements a year, 2010..2015 (a short year must be named with a reason)
  G3  a scheduled statement falls on the meeting's last day, and the statement page's own dateline names that date
  G4  no duplicate (event, date_et); no row outside 2010..2015
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from d710_paths import REPO, data_root, tracked  # noqa: E402

EXT_YEARS = (2010, 2011, 2012, 2013, 2014, 2015)
REPRO_SPAN = ("2016-01-01", "2023-12-31")
OUT_CSV = tracked("calendar", "fomc_2010_2015.csv")
OUT_META = tracked("calendar", "fomc_2010_2015.meta.json")
D585_CSV = tracked("calendar", "events.csv")
EVENTS = ("FOMC", "FOMC_UNSCHEDULED")
COLUMNS = ("date_et", "event", "release_clock_et", "clock_source", "statement_url", "meeting_panel",
           "meeting_last_day", "method", "accessed_utc")
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
               "November", "December"]


def _load_d585():
    spec = importlib.util.spec_from_file_location("frc_d585", REPO / "scripts" / "fetch_release_calendar.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


R = _load_d585()

PANEL_SPLIT = re.compile(r'<div class="panel panel-default(?: panel-padded)?">')
HEADING_EXT = re.compile(
    r"^(?P<mon>[A-Za-z]+(?:/[A-Za-z]+)?)\s+(?P<days>[\d–-]+)\*?\s*"
    r"(?:\((?P<tag>[^)]*)\))?\s*(?P<kind>Meeting|Conference Call)?\s*(?:-\s*(?P<yr>\d{4}))?\s*$")
STATEMENT_EXT = re.compile(r'href="(/newsevents/press(?:releases/monetary|/monetary/)(\d{8})a\.htm)"')


class GateError(AssertionError):
    pass


def gate(cond, msg):
    if not cond:
        raise GateError(msg)


def parse_hist_ext(html, year):
    out = []
    for chunk in PANEL_SPLIT.split(html)[1:]:
        h = re.search(r"<h5[^>]*>(.*?)</h5>", chunk, re.S)
        if not h:
            continue
        head = R.strip_tags(h.group(1))
        # 'July 31-August 1 Meeting - 2012' is D585's 'July/August 31-1' written out; normalised to that form
        m = HEADING_EXT.match(re.sub(r"^([A-Za-z]+)\s+(\d+)\s*[–-]\s*([A-Za-z]+)\s+(\d+)", r"\1/\3 \2-\4", head))
        assert m, f"FOMC {year}: unparsed panel heading {head!r}"
        stamps = sorted({s for _, s in STATEMENT_EXT.findall(chunk)})
        assert len(stamps) <= 1, f"FOMC {year}: {head!r} has {len(stamps)} statement links"
        tag = (m.group("tag") or "").strip().lower()
        if (m.group("kind") or "") == "Conference Call":
            tag = (tag + " conference call").strip()
        out.append({"heading": head, "tag": tag,
                    "last_day": R.meeting_last_day(m.group("mon"), m.group("days"), int(m.group("yr") or year)),
                    "statement": f"/newsevents/pressreleases/monetary{stamps[0]}a.htm" if stamps else None})
    return out


def _with_ext_parser(fn, *a):
    saved = R.parse_fomc_hist
    R.parse_fomc_hist = parse_hist_ext
    try:
        return fn(*a)
    finally:
        R.parse_fomc_hist = saved


def _point(raw_dir: Path):
    """D585's helpers read the module globals RAW and MANIFEST at call time; point them at one cache."""
    R.RAW = raw_dir
    R.MANIFEST = raw_dir / "_manifest.json"


def _dateline(d: date) -> str:
    return f"{MONTH_NAMES[d.month - 1]} {d.day}, {d.year}"


def build_dates(man: dict, years, notes: dict, check_dateline: bool = True) -> list[dict]:
    """One row per statement: the sourced DATE, and the clock only where the page states it."""
    rows = []
    for y in years:
        html, src = R.read_raw(man, f"fomc_hist_{y}")
        for p in parse_hist_ext(html, y):
            if p["tag"] == "cancelled":
                notes["panels_excluded"].append({"panel": p["heading"], "reason": "cancelled, no statement"})
                continue
            if not p["statement"]:
                notes["meetings_without_a_statement"].append(
                    {"panel": p["heading"], "meeting_last_day": p["last_day"].isoformat(), "source_url": src["url"],
                     "consequence": "no statement was issued, so there is no market event; no row"})
                continue
            stamp = p["statement"][-13:-5]
            sd = date(int(stamp[:4]), int(stamp[4:6]), int(stamp[6:]))
            key = f"fomc_pr_{stamp}"
            gate(key in man, f"G1: statement {p['statement']} not in the raw cache")
            page, rec = R.read_raw(man, key)
            txt = R.strip_tags(page[:200_000])
            if check_dateline:
                padded = f"{MONTH_NAMES[sd.month - 1]} {sd.day:02d}, {sd.year}"      # 'May 09, 2010' also occurs
                gate(_dateline(sd) in txt or padded in txt,
                     f"G3: the statement page for {sd} does not carry the dateline {_dateline(sd)!r}")
            clk = R.PR_TIME.search(txt)
            if clk:
                hh, mm = R.parse_clock(clk.group(1))
                clock, csrc = f"{hh:02d}:{mm:02d}", f"'For release at' on the statement page ({clk.group(2)})"
            else:
                clock, csrc = "", "not stated on the statement page ('For immediate release')"
            scheduled = p["tag"] == ""
            if scheduled:
                gate(sd == p["last_day"], f"G3: scheduled statement {sd} is not the meeting's last day {p['last_day']}")
            rows.append({"date_et": sd.isoformat(), "event": "FOMC" if scheduled else "FOMC_UNSCHEDULED",
                         "release_clock_et": clock, "clock_source": csrc,
                         "statement_url": "https://www.federalreserve.gov" + p["statement"],
                         "meeting_panel": p["heading"], "meeting_last_day": p["last_day"].isoformat(),
                         "method": "fetched", "accessed_utc": rec["accessed_utc"]})
    rows.sort(key=lambda r: (r["date_et"], r["event"]))
    return rows


def fetch(log=print) -> int:
    raw = data_root() / "raw" / "fomc_ext"
    _point(raw)
    man = R.load_manifest()
    for y in EXT_YEARS:
        R.acquire(man, f"fomc_hist_{y}", f"https://www.federalreserve.gov/monetarypolicy/fomchistorical{y}.htm",
                  "fetched", R.PAUSE_GOV, log)
    hrefs = set()
    for y in EXT_YEARS:
        html, _ = R.read_raw(man, f"fomc_hist_{y}")
        panels = parse_hist_ext(html, y)
        log(f"  {y}: {len(panels)} panels, {sum(1 for p in panels if p['statement'])} with a statement link")
        hrefs |= {p["statement"] for p in panels if p["statement"]}
    for href in sorted(hrefs):
        stamp = href[-13:-5]
        R.acquire(man, f"fomc_pr_{stamp}", "https://www.federalreserve.gov" + href, "fetched", R.PAUSE_GOV, log)
    R.save_manifest(man)
    log(f"fetch done: {len(man)} raw responses in {raw}")
    return 0


def _read_d585_rows(path: Path, lo: str, hi: str) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f) if r["event"] in EVENTS and lo <= r["datetime_et"][:10] <= hi]


def reproduce(built: list[dict], committed: list[dict], cols=None, tag="R") -> dict:
    cols = cols or R.COLUMNS
    a = sorted((tuple(r[c] for c in cols) for r in built))
    b = sorted((tuple(r[c] for c in cols) for r in committed))
    only_built = sorted(set(a) - set(b))
    only_committed = sorted(set(b) - set(a))
    gate(a == b, f"{tag}: the D585 reproduction is not exact: {len(a)} built vs {len(b)} committed; "
                 f"only built {only_built[:2]}, only committed {only_committed[:2]}")
    return {"rows": len(a), "exact": True}


def gates(rows: list[dict], short_years: dict[str, str] | None = None) -> dict:
    short_years = short_years or {}
    bad = [r for r in rows if not r["statement_url"] or not r["accessed_utc"] or r["method"] != "fetched"]
    gate(not bad, f"G1: {len(bad)} rows without a statement_url, access time or method 'fetched'")
    keys = [(r["event"], r["date_et"]) for r in rows]
    gate(len(keys) == len(set(keys)), "G4: duplicate (event, date_et)")
    outside = [r for r in rows if not (str(EXT_YEARS[0]) <= r["date_et"][:4] <= str(EXT_YEARS[-1]))]
    gate(not outside, f"G4: {len(outside)} rows outside {EXT_YEARS[0]}..{EXT_YEARS[-1]}")
    per = {str(y): 0 for y in EXT_YEARS}
    for r in rows:
        if r["event"] == "FOMC":
            per[r["date_et"][:4]] += 1
    off = {y: n for y, n in per.items() if n != 8 and y not in short_years}
    gate(not off, f"G2: scheduled FOMC statements a year must be 8 (or named): {off}")
    return {"G1": {"rows": len(rows), "pass": True},
            "G2": {"scheduled_per_year": per, "named_short_years": short_years, "pass": True},
            "G3": {"scheduled_on_meeting_last_day": True, "dateline_on_statement_page": True, "pass": True},
            "G4": {"pass": True}}


def build(log=print) -> int:
    root = data_root()
    # ---- R: reproduce D585 2016-2023 from D585's own cache before anything earlier is used
    _point(root / "raw" / "calendar")
    man585 = R.load_manifest()
    assert man585, "D585's raw cache is missing"
    committed = _read_d585_rows(D585_CSV, *REPRO_SPAN)
    inspan = lambda rs: [r for r in rs if REPRO_SPAN[0] <= r["datetime_et"][:10] <= REPRO_SPAN[1]]  # noqa: E731
    r1 = reproduce(inspan(R.build_fomc(man585, defaultdict(list), log)), committed, tag="R1")
    r2 = reproduce(inspan(_with_ext_parser(R.build_fomc, man585, defaultdict(list), log)), committed, tag="R2")
    mine = build_dates(man585, R.FOMC_HIST_YEARS, defaultdict(list))
    want = [{"date_et": r["datetime_et"][:10], "event": r["event"]} for r in committed if r["datetime_et"][:4] <= "2020"]
    r3 = reproduce(mine, want, cols=("date_et", "event"), tag="R3")
    per_year = {}
    for r in committed:
        per_year[r["datetime_et"][:4]] = per_year.get(r["datetime_et"][:4], 0) + 1
    log(f"  R1/R2: D585's FOMC rows 2016-2023 reproduced EXACTLY by both parsers ({r1['rows']} rows {per_year})")
    log(f"  R3: this file's date builder gives D585's 2016-2020 (date, event) pairs exactly ({r3['rows']} rows)")

    # ---- the extension
    raw = root / "raw" / "fomc_ext"
    _point(raw)
    man = R.load_manifest()
    assert man, "no extension cache; run --fetch first"
    notes = defaultdict(list)
    rows = build_dates(man, EXT_YEARS, notes)
    rep_g = gates(rows)
    ext_sources = {k: {kk: v[kk] for kk in ("url", "method", "accessed_utc", "bytes", "sha256")}
                   for k, v in sorted(man.items())}
    meta = {
        "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "builder": "scripts/fetch_fomc_2010_2015.py", "record": "D710 (extends D585's FOMC fetch back to 2010)",
        "span": {"from": rows[0]["date_et"], "to": rows[-1]["date_et"]},
        "reproduction_of_d585": {"span": list(REPRO_SPAN), "rows": r1["rows"], "rows_per_year": per_year,
                                 "R1_d585_parser": r1, "R2_extension_parser_in_build_fomc": r2,
                                 "R3_extension_date_builder_2016_2020": r3},
        "rows": len(rows),
        "rows_per_event_per_year": {ev: {str(y): sum(1 for r in rows if r["event"] == ev and r["date_et"][:4] == str(y))
                                         for y in EXT_YEARS} for ev in EVENTS},
        "clocks_stated": sum(1 for r in rows if r["release_clock_et"]),
        "why_no_clock": "every 2010-2015 statement page reads 'For immediate release' and states no clock; D710 "
                        "excludes the whole session, so only the sourced date is used. No clock is filled in.",
        "legacy_links": "fomchistorical2010 links statements by /newsevents/press/monetary/YYYYMMDDa.htm; the "
                        "canonical /newsevents/pressreleases/monetaryYYYYMMDDa.htm was fetched and is cited, and "
                        "each page's dateline was checked against the date (G3)",
        "gates": rep_g,
        "sources": ext_sources,
        "raw_cache": "data/raw/fomc_ext/ (gitignored; _manifest.json beside the responses)",
        **{k: v for k, v in notes.items()},
    }
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    OUT_META.write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    log(f"  wrote {OUT_CSV.relative_to(REPO)} ({len(rows)} rows) and {OUT_META.relative_to(REPO)}")
    log(f"  per year: {meta['rows_per_event_per_year']}; clocks stated: {meta['clocks_stated']}")
    log(f"  meetings without a statement: {[m['meeting_last_day'] for m in notes['meetings_without_a_statement']]}")
    log(f"  sha256 csv {hashlib.sha256(OUT_CSV.read_bytes()).hexdigest()[:16]}")
    return 0


# --------------------------------------------------------------------------- selftest

def _clean():
    rows = []
    for y in EXT_YEARS:
        for m in (1, 3, 4, 6, 7, 9, 10, 12):
            rows.append({"date_et": f"{y}-{m:02d}-15", "event": "FOMC", "release_clock_et": "", "clock_source": "x",
                         "statement_url": "u", "meeting_panel": "p", "meeting_last_day": f"{y}-{m:02d}-15",
                         "method": "fetched", "accessed_utc": "t"})
    return rows


def expect(fn, g, what, log=print) -> int:
    """The break must raise AND raise at the gate it was built to break -- not at some other gate."""
    try:
        fn()
    except GateError as e:
        assert str(e).startswith(g), f"{what}: raised at the wrong gate: {str(e)[:80]}"
        log(f"    {g} RAISES on {what}: {str(e)[:90]}")
        return 1
    raise AssertionError(f"{g} did not raise on {what}")


def _fake_man(tmp: Path, hist_html: str, pr_html: str, stamp: str) -> dict:
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "h.html").write_text(hist_html, encoding="utf-8")
    (tmp / "p.html").write_text(pr_html, encoding="utf-8")
    return {"fomc_hist_2010": {"path": "h.html", "url": "hist", "accessed_utc": "t"},
            f"fomc_pr_{stamp}": {"path": "p.html", "url": "pr", "accessed_utc": "t"}}


def selftest(log=print) -> int:
    import tempfile
    log("selftest: the gates pass a clean case and RAISE on a deliberate break, at the gate named")
    clean = _clean()
    gates(clean)
    n = 0
    n += expect(lambda: gates(clean[1:]), "G2", "a year with 7 scheduled statements", log)
    n += expect(lambda: gates(clean + clean[:1]), "G4", "a duplicate row", log)
    n += expect(lambda: gates([{**clean[0], "method": "inferred"}] + clean[1:]), "G1", "method inferred", log)
    n += expect(lambda: gates(clean + [{**clean[0], "date_et": "2016-01-27"}]), "G4", "a 2016 row in the extension", log)
    gates(clean[1:], short_years={"2010": "named in the test"})
    log("    G2 passes the same short year once it is NAMED with a reason")
    comm = [{c: str(i) for c in R.COLUMNS} for i in range(5)]
    reproduce(comm, comm)
    n += expect(lambda: reproduce(comm, comm[:4], tag="R1"), "R1", "a committed row missing from the rebuild", log)
    n += expect(lambda: reproduce([{**comm[0], "datetime_et": "X"}] + comm[1:], comm, tag="R2"), "R2",
                "a rebuilt row one field off", log)
    # the parser and date builder on a synthetic 2010-style page (legacy link, conference call, month-spanning days)
    hist = ('<div class="panel panel-default"><div class="panel-heading"><h5>January 26-27 Meeting - 2010</h5></div>'
            '<a href="/newsevents/press/monetary/20100127a.htm">Statement</a></div>'
            '<div class="panel panel-default panel-padded"><h5 class="panel-heading">May 9 Conference Call - 2010</h5>'
            '</div><div class="panel panel-default"><h5>July 31-August 1 Meeting - 2010</h5></div>')
    ps = parse_hist_ext(hist, 2010)
    assert [(p["last_day"].isoformat(), p["tag"], p["statement"]) for p in ps] == [
        ("2010-01-27", "", "/newsevents/pressreleases/monetary20100127a.htm"),
        ("2010-05-09", "conference call", None), ("2010-08-01", "", None)], ps
    log("    parse_hist_ext: legacy link normalised, conference call tagged, 'July 31-August 1' -> 2010-08-01")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _point(tmp)
        good = "<p>January 27, 2010</p><p>FOMC statement For immediate release</p>"
        man = _fake_man(tmp, hist, good, "20100127")
        rows = build_dates(man, (2010,), defaultdict(list))
        assert len(rows) == 1 and rows[0]["date_et"] == "2010-01-27" and rows[0]["release_clock_et"] == ""
        log("    build_dates: the sourced date written, the unstated clock left EMPTY (never filled)")
        man = _fake_man(tmp, hist, "<p>January 28, 2010</p>", "20100127")
        n += expect(lambda: build_dates(man, (2010,), defaultdict(list)), "G3",
                    "a statement page whose dateline is another day", log)
        bad_hist = hist.replace("20100127a", "20100126a")
        man = _fake_man(tmp, bad_hist, "<p>January 26, 2010</p>", "20100126")
        n += expect(lambda: build_dates(man, (2010,), defaultdict(list)), "G3",
                    "a scheduled statement off the meeting's last day", log)
    assert n == 8
    log(f"selftest: PASS ({n} breaks raised at their own gates)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.fetch:
        return fetch()
    if a.build:
        return build()
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
