"""D782 FIXTURE: the other BLS releases at 08:30 ET, from the BLS year pages D585 already cached.

    python scripts/build_bls_0830_calendar.py --selftest
    python scripts/build_bls_0830_calendar.py --build

Writes data/calendar/events_bls_0830.csv (+ .meta.json): PPI, IMPEXP (U.S. Import and Export Price Indexes), ECI
(Employment Cost Index), PROD_P and PROD_R (Productivity and Costs, preliminary and revised), each row's date and clock
read off `bls.gov/schedule/<year>/home.htm` as D585 cached it (data/raw/calendar/, main checkout). Nothing is fetched.

D585's rule holds: a row exists only where its date AND its clock came off the page, and the page's own weekday word
must agree with the parsed date. `events.csv` is not touched: it is read by D775 and by D776's frozen vault line.
The parser is D585's `parse_bls_year` with the event map as a parameter; G1 proves it reproduces events.csv's CPI and
EMPSIT rows exactly before any new row is written.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import fetch_release_calendar as F  # noqa: E402

MAIN = Path("C:/Users/O/Desktop/Projects/Backtest Framework")
F.RAW = MAIN / "data" / "raw" / "calendar"                 # the raw cache lives in the main checkout (gitignored)
F.MANIFEST = F.RAW / "_manifest.json"                      # set at F's import from its own RAW; repointed with it
OUT = REPO / "data" / "calendar" / "events_bls_0830.csv"
META = REPO / "data" / "calendar" / "events_bls_0830.meta.json"
EVENTS_CSV = REPO / "data" / "calendar" / "events.csv"
NEW = {"Producer Price Index": "PPI", "U.S. Import and Export Price Indexes": "IMPEXP",
       "Employment Cost Index": "ECI", "Productivity and Costs (P)": "PROD_P", "Productivity and Costs (R)": "PROD_R"}
OLD = {"Consumer Price Index": "CPI", "Employment Situation": "EMPSIT"}
FULL_YEARS = tuple(range(2016, 2025))                    # 2025 is disrupted (D585); 2026 is partly forward
PER_YEAR = {"PPI": 12, "IMPEXP": 12, "ECI": 4, "PROD_P": 4, "PROD_R": 4}
COLS = ["datetime_et", "datetime_utc", "event", "source_url", "release_date_nominal", "holiday_shift", "method",
        "accessed_utc"]


class CalError(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise CalError(msg)


def parse_year(html: str, year: int, events: dict[str, str]) -> list[dict]:
    """D585's parse_bls_year with the event map as a parameter: exact-name match on the <strong> title, the page's
    weekday word asserted against the parsed date, the row's year asserted."""
    body = html[html.find("MAIN CONTENT BEGIN"):]
    out = []
    for date_cell, time_cell, desc in F.BLS_ROW.findall(body):
        m = re.match(r"\s*<strong>(.*?)</strong>", desc)
        if not m or m.group(1).strip() not in events:
            continue
        txt = F.strip_tags(date_cell)
        wk, _, rest = txt.partition(",")
        d = F.parse_us_date(rest)
        need(d.strftime("%A") == wk.strip(), f"BLS {year}: the page says {wk.strip()} for {d}, a {d:%A}")
        need(d.year == year, f"BLS {year} page carries a {d.year} row: {txt}")
        hh, mm = F.parse_clock(F.strip_tags(time_cell))
        out.append({"event": events[m.group(1).strip()], "date": d, "hh": hh, "mm": mm})
    return out


def rows_for(man: dict, events: dict[str, str]) -> tuple[list[dict], list[int]]:
    rows, years = [], []
    for y in F.BLS_YEARS:
        key = f"bls_schedule_{y}"
        if key not in man:
            continue
        html, rec = F.read_raw(man, key)
        years.append(y)
        for r in parse_year(html, y, events):
            nominal = F.first_friday(r["date"].year, r["date"].month) if r["event"] == "EMPSIT" else ""
            rows.append(F.row(r["event"], r["date"], r["hh"], r["mm"], rec["url"], nominal,
                              bool(nominal) and nominal != r["date"], rec["method"], rec["accessed_utc"]))
    return rows, years


def build() -> int:
    man = F.load_manifest()
    need(sum(k.startswith("bls_schedule_") for k in man) >= 9, f"the raw cache's manifest has no BLS year pages: {F.MANIFEST}")
    # G1: the parameterised parser reproduces events.csv's CPI and EMPSIT rows exactly
    old, _ = rows_for(man, OLD)
    with open(EVENTS_CSV, encoding="utf-8", newline="") as fh:
        ref = [r for r in csv.DictReader(fh) if r["event"] in ("CPI", "EMPSIT")]
    key = lambda r: (r["event"], r["datetime_et"])  # noqa: E731
    need(sorted(([r[c] for c in COLS] for r in old), key=lambda x: (x[2], x[0])) ==
         sorted(([r[c] for c in COLS] for r in ref), key=lambda x: (x[2], x[0])),
         "G1: the parser does not reproduce events.csv's CPI/EMPSIT rows")
    new, years = rows_for(man, NEW)
    need(len({key(r) for r in new}) == len(new), "a duplicated (event, datetime)")
    # G2: counts per event in the full years
    cnt = Counter((r["event"], r["datetime_et"][:4]) for r in new)
    short = {f"{e} {y}": cnt.get((e, str(y)), 0) for e in PER_YEAR for y in FULL_YEARS if cnt.get((e, str(y)), 0) != PER_YEAR[e]}
    need(not short, f"G2: a full year with the wrong count: {short}")
    clocks = Counter((r["event"], r["datetime_et"][11:16]) for r in new)
    old_days = {r["datetime_et"][:10]: r["event"] for r in ref}
    same_day = sorted(f"{r['event']} {r['datetime_et'][:10]} = {old_days[r['datetime_et'][:10]]}"
                      for r in new if r["datetime_et"][:10] in old_days)
    new.sort(key=lambda r: (r["datetime_et"], r["event"]))
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(new)
    meta = {"decision": "D782", "builder": "scripts/build_bls_0830_calendar.py", "source": "bls.gov/schedule/<year>/home.htm "
            "as cached by D585 (data/raw/calendar/_manifest.json); nothing fetched",
            "events": NEW, "years_parsed": years, "rows": len(new),
            "rows_by_event": dict(Counter(r["event"] for r in new)),
            "clocks": {f"{e} {c}": n for (e, c), n in sorted(clocks.items())},
            "G1_reproduces_events_csv_cpi_empsit_rows": len(ref),
            "G2_full_years_checked": [FULL_YEARS[0], FULL_YEARS[-1]], "per_year": PER_YEAR,
            "same_day_as_cpi_or_empsit": same_day,
            "by_year": {f"{e} {y}": cnt.get((e, str(y)), 0) for e in PER_YEAR for y in years}}
    META.write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in meta.items() if k != "by_year"}, indent=1))
    return 0


def selftest() -> int:
    page = ('MAIN CONTENT BEGIN <td class="date-cell"><p>Wednesday, March 13, 2019</p></td>\n'
            '<td class="time-cell"><p>08:30 AM</p></td>\n<td class="desc-cell"><p><strong>Producer Price Index'
            '</strong> for February 2019</p></td>\n'
            '<td class="date-cell"><p>Thursday, March 14, 2019</p></td>\n<td class="time-cell"><p>08:30 AM</p></td>\n'
            '<td class="desc-cell"><p><strong>Producer Price Index Detailed Report</strong></p></td>')
    r = parse_year(page, 2019, NEW)
    need(len(r) == 1 and r[0]["event"] == "PPI" and str(r[0]["date"]) == "2019-03-13" and (r[0]["hh"], r[0]["mm"]) == (8, 30),
         f"the parser: {r}")
    try:
        parse_year(page.replace("Wednesday, March 13", "Tuesday, March 13"), 2019, NEW)
    except CalError:
        pass
    else:
        raise CalError("a wrong weekday word did not raise")
    try:
        parse_year(page, 2020, NEW)
    except CalError:
        pass
    else:
        raise CalError("a row from another year did not raise")
    print("selftest OK: exact-name match (a near-name is skipped), the weekday word check raises, the year check raises")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--build", action="store_true")
    a = ap.parse_args(argv)
    return selftest() if a.selftest else build()


if __name__ == "__main__":
    sys.exit(main())
