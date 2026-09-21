"""D585 FIXTURE (manual, NETWORK): the sourced US economic release calendar, with times.

    uv run python scripts/fetch_release_calendar.py --probe     # metadata only: what each source offers, nothing written
    uv run python scripts/fetch_release_calendar.py --fetch     # raw pages -> data/raw/calendar/, resumable, one pass, polite
    uv run python scripts/fetch_release_calendar.py --build     # raw -> data/calendar/events.csv + events.meta.json (gates)
    uv run python scripts/fetch_release_calendar.py --selftest  # synthetic: every gate passes a clean case and RAISES on a break

Sibling of `fetch_cftc_cot.py` and `fetch_perp_funding.py`: stdlib only, cache the raw (D191), commit the derived.

WHY THIS EXISTS
---------------
`docs/internal/User-Doc-Deposit/SHOCK_CLASSIFIER_PREREG.md` 3.4 needs `data/calendar/events.csv` with
scheduled release TIMESTAMPS, and says in its own section 0: "Never fabricate data. This includes
economic calendar dates. If a source can't be found, stop and report." The flag lists in
LETF_CLOSE_FLOW_PREREG 3.4, OPENING_AGENT_STATE_PREREG 3 and SETTLEMENT_FLOW_LEDGER_PREREG 3.5 read the
same file (FOMC / CPI / payrolls days; EIA crude-Wednesday and gas-Thursday days). Nothing here reads a
market bar or computes a return.

THE ONE RULE THAT SHAPES EVERY LINE BELOW
-----------------------------------------
A row exists only where BOTH its date AND its time came off an official page (`method=fetched`) or off a
Wayback capture of an official page (`method=archived`). `method=inferred` is REFUSED by the builder and
the selftest proves the refusal fires. What cannot be sourced is recorded in the meta's `not_fetched`
with the reason -- never filled in from a rule.

WHAT EACH SOURCE ACTUALLY GIVES, AS PROBED ON 2026-09-21
--------------------------------------------------------
  BLS  /schedule/{year}/home.htm          2016..2026 (2027 is 404). ONE page a year, every release with
                                          its weekday, date and clock time. The row's own weekday text is
                                          cross-checked against the parsed date (G3).
  BLS  /schedule/news_release/{cpi,empsit}.htm
                                          the forward 13 months, used ONLY as a second source to
                                          cross-check the year pages; disagreements go to the meta.
  Fed  /monetarypolicy/fomchistorical{2016..2020}.htm and /monetarypolicy/fomccalendars.htm (2021..2027)
                                          the meeting panels. The statement's own press release states
                                          "For release at 2:00 p.m. EST" -- so the FOMC time is FETCHED
                                          per meeting, not assumed, and the stated EST/EDT is checked
                                          against America/New_York for that date.
  EIA  /petroleum/supply/weekly/schedule.php  and  ir.eia.gov/ngs/schedule.html
                                          EIA publishes its weekly schedule as a STANDARD SENTENCE plus an
                                          EXCEPTION TABLE, not as a list of weeks. Both are read off the
                                          page (the standard day and time are parsed, never hard-coded --
                                          see `parse_eia_standard`), and the live page carries only about
                                          two years of exceptions, so prior years come from Wayback
                                          captures of the same two URLs (`method=archived`).

WHAT THE EIA SCHEDULE IS AND IS NOT
-----------------------------------
It is the schedule EIA PUBLISHED. An unannounced delay does not appear on it. A Wednesday with no
exception row is a row whose date and time come from the page's own standard sentence plus the absence of
that week from the page's own exception table -- that is how EIA publishes the schedule, and the meta
names the governing page for every year.

THE NATURAL-GAS EXCEPTION TABLE DOES NOT SAY WHICH THURSDAY IT REPLACES
-----------------------------------------------------------------------
The petroleum table has a "Data for the week ending" column, so the nominal Wednesday is week_ending + 5.
The gas table has only the alternate date. "Nearest Thursday" is WRONG: at the end of 2025 the alternates
are Mon 2025-12-29 (Christmas) and Wed 2025-12-31 (New Year), and the nearest Thursday to 12-29 is
2026-01-01, which belongs to 12-31. The assignment is therefore a minimum-cost ORDER-PRESERVING match of
alternates onto Thursdays (`match_alternates_to_thursdays`), and where the source's holiday cell carries
an explicit date the match is checked against it (the displaced Thursday is within 2 days of the holiday).
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "calendar"
OUTDIR = REPO / "data" / "calendar"
CSV = OUTDIR / "events.csv"
META = OUTDIR / "events.meta.json"
MANIFEST = RAW / "_manifest.json"
MACRO = REPO / "data" / "macro_release_calendar.json"

ET = ZoneInfo("America/New_York")
UA = {"User-Agent": "backtest-framework-fetch/1.0 (personal research; contact via repository)",
      "Accept": "text/html,application/json"}
PAUSE_GOV = 1.0          # be polite: one pass, a second between requests
PAUSE_WB = 2.5           # web.archive.org is slower and shared
TIMEOUT = 120
SPAN_START = date(2016, 1, 1)
BLS_YEARS = tuple(range(2016, 2027))          # 2027 is a 404 as of the probe
FOMC_HIST_YEARS = (2016, 2017, 2018, 2019, 2020)
WB_CAPTURES_PER_YEAR = 5

SCHEDULE_PAGES = {
    "EIA_WPSR": ("eia_wpsr", "https://www.eia.gov/petroleum/supply/weekly/schedule.php",
                 "eia.gov/petroleum/supply/weekly/schedule.php", 2),     # 2 = Wednesday
    "EIA_NGSR": ("eia_ngsr", "https://ir.eia.gov/ngs/schedule.html",
                 "ir.eia.gov/ngs/schedule.html", 3),                     # 3 = Thursday
}

COLUMNS = ("datetime_et", "datetime_utc", "event", "source_url", "release_date_nominal",
           "holiday_shift", "method", "accessed_utc")
VALID_METHODS = ("fetched", "archived")
COUNT_RANGE = {"CPI": (12, 12), "EMPSIT": (12, 12), "FOMC": (8, 8),
               "EIA_WPSR": (50, 53), "EIA_NGSR": (50, 53)}
REQUIRED_OUTPUTS = ("built_utc", "fetcher", "span", "conventions", "sources", "rows",
                    "rows_per_event_per_year", "gates", "not_fetched",
                    "disagreements_with_macro_release_calendar_json")

MONTHS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"])}


def expect_raise(fn, what, log=print):
    """The selftest idiom of scripts/stage0_d581_gamma_close.py:39."""
    try:
        fn()
    except AssertionError as e:
        log(f"    gate RAISES on {what}: {str(e)[:80]}")
        return True
    raise AssertionError(f"gate did not raise on {what}")


# --------------------------------------------------------------------------- network + raw cache

def _get(url, timeout=TIMEOUT):
    """web.archive.org answers 503 when it is asked too often, so it gets a long, growing backoff."""
    req = urllib.request.Request(url, headers=UA)
    delay = 15.0 if "web.archive.org" in url else 3.0
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code == 404:
                raise
            if attempt == 3:
                raise RuntimeError(f"GET {url} failed after 4 attempts: {type(exc).__name__}: {exc}") from exc
            time.sleep(delay)
            delay *= 2
    return b""


def _head(url):
    req = urllib.request.Request(url, headers=UA, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.headers.get("Content-Length", "?")
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 405, 503):      # eia.gov's edge refuses HEAD; a GET answers
            try:
                return f"{200} (HEAD refused {exc.code}, GET used)", str(len(_get(url)))
            except Exception:  # noqa: BLE001
                return exc.code, "-"
        return exc.code, "-"
    except Exception as exc:  # noqa: BLE001 -- a probe reports the tool that failed
        return f"ERR {type(exc).__name__}", "-"


def now_stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def iso_utc(stamp):
    """20260921T143000Z -> 2026-09-21T14:30:00Z"""
    return f"{stamp[0:4]}-{stamp[4:6]}-{stamp[6:8]}T{stamp[9:11]}:{stamp[11:13]}:{stamp[13:15]}Z"


def load_manifest():
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {}


def save_manifest(man):
    RAW.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(man, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def acquire(man, key, url, method, pause, log, fetch_url=None):
    """Fetch `url` once and keep the response bytes UNMODIFIED under a fetched_at name. Resumable."""
    rec = man.get(key)
    if rec and (RAW / rec["path"]).exists():
        return rec
    stamp = now_stamp()
    body = _get(fetch_url or url)
    path = f"{key}__{stamp}.html"
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / path).write_bytes(body)
    rec = {"url": url, "fetch_url": fetch_url or url, "path": path, "method": method,
           "accessed_utc": iso_utc(stamp), "bytes": len(body),
           "sha256": hashlib.sha256(body).hexdigest()}
    man[key] = rec
    save_manifest(man)
    log(f"    {key}: {len(body)} bytes")
    time.sleep(pause)
    return rec


def read_raw(man, key):
    """The cached bytes are the response EXACTLY as it arrived. A Wayback `id_` replay hands back the
    original response including its `Content-Encoding: gzip`, so 17 of these files are gzip members;
    they are decompressed HERE, on read, and never rewritten -- the cache stays byte-for-byte."""
    rec = man[key]
    body = (RAW / rec["path"]).read_bytes()
    if body[:2] == b"\x1f\x8b":
        body = gzip.decompress(body)
    return body.decode("utf-8", "replace"), rec


# --------------------------------------------------------------------------- Wayback

def cdx(url_key, log=print):
    """Capture timestamps for one URL. /web/timemap/json answers where /cdx/search/cdx 503s under load;
    the collapse and the status filter are done here rather than asked of the server."""
    q = "https://web.archive.org/web/timemap/json?" + urllib.parse.urlencode(
        {"url": url_key, "fl": "timestamp,digest,statuscode", "matchType": "exact"})
    time.sleep(PAUSE_WB)
    rows = json.loads(_get(q).decode("utf-8"))
    out, seen = [], set()
    for ts, digest, status in rows[1:] if rows else []:
        if status != "200" or digest in seen or not (2014 <= int(ts[:4]) <= 2027):
            continue
        seen.add(digest)
        out.append(ts)
    return sorted(out)


def pick_captures(timestamps, per_year=WB_CAPTURES_PER_YEAR):
    """First and last of each year plus evenly spaced middles -- the first capture of a year carries the
    PREVIOUS year's completed exception table, the last carries that year's."""
    by_year = {}
    for ts in sorted(timestamps):
        by_year.setdefault(ts[:4], []).append(ts)
    out = []
    for _, ts in sorted(by_year.items()):
        if len(ts) <= per_year:
            out += ts
        else:
            idx = sorted({round(i * (len(ts) - 1) / (per_year - 1)) for i in range(per_year)})
            out += [ts[i] for i in idx]
    return out


def wb_urls(ts, original):
    cite = f"https://web.archive.org/web/{ts}/{original}"
    return cite, f"https://web.archive.org/web/{ts}id_/{original}"


# --------------------------------------------------------------------------- small parsing helpers

def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).replace("&nbsp;", " ").replace("&amp;", "&").strip()


def parse_us_date(text):
    """'January 15, 2016' | 'Jan. 15, 2016' | '11/27/2013' | 'January 8, 2025 - (Updated)' -> date."""
    t = text.split(" - ")[0].replace("–", "-").strip().rstrip(".")
    t = re.sub(r"\s+", " ", t)
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", t)
    if m:
        return date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
    m = re.match(r"^([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})$", t)
    if m:
        name = m.group(1).lower()
        for full, num in MONTHS.items():
            if full.startswith(name):
                return date(int(m.group(3)), num, int(m.group(2)))
    raise AssertionError(f"unparsable date {text!r}")


def parse_clock(text):
    """'08:30 AM' | '10:30 a.m.' | '12:00 p.m.' | '5:00 p.m. EDT' -> (hour, minute)."""
    m = re.search(r"(\d{1,2}):(\d{2})\s*([ap])\.?\s*m\.?", text, re.I)
    if not m:
        raise AssertionError(f"unparsable clock {text!r}")
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3).lower()
    if h == 12:
        h = 0
    if ap == "p":
        h += 12
    return h, mi


def et_pair(d, hh, mm):
    """(datetime_et ISO with offset, datetime_utc ISO Z). The ONLY place a clock becomes a timestamp."""
    local = datetime(d.year, d.month, d.day, hh, mm, tzinfo=ET)
    return local.isoformat(), local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def first_friday(y, m):
    d = date(y, m, 1)
    return d + timedelta(days=(4 - d.weekday()) % 7)


def row(event, d, hh, mm, source_url, nominal, shift, method, accessed):
    et, utc = et_pair(d, hh, mm)
    return {"datetime_et": et, "datetime_utc": utc, "event": event, "source_url": source_url,
            "release_date_nominal": nominal.isoformat() if isinstance(nominal, date) else (nominal or ""),
            "holiday_shift": "True" if shift else "False", "method": method, "accessed_utc": accessed}


# --------------------------------------------------------------------------- BLS

BLS_ROW = re.compile(
    r'<td class="date-cell"><p>(.*?)</p></td>\s*'
    r'<td class="time-cell"><p>(.*?)</p></td>\s*'
    r'<td class="desc-cell"><p>(.*?)</p></td>', re.S)
BLS_EVENTS = {"Consumer Price Index": "CPI", "Employment Situation": "EMPSIT"}


def parse_bls_year(html, year):
    """The year page's Date/Time/Release table. The weekday WORD on the page is checked against the
    parsed date -- BLS writes both, so their agreement is a free second derivation (G3)."""
    body = html[html.find("MAIN CONTENT BEGIN"):]
    out, weekday_checked = [], 0
    for date_cell, time_cell, desc in BLS_ROW.findall(body):
        m = re.match(r"\s*<strong>(.*?)</strong>", desc)
        if not m or m.group(1).strip() not in BLS_EVENTS:
            continue
        event = BLS_EVENTS[m.group(1).strip()]
        txt = strip_tags(date_cell)
        wk, _, rest = txt.partition(",")
        d = parse_us_date(rest)
        assert d.strftime("%A") == wk.strip(), f"BLS {year}: page says {wk.strip()} for {d} which is a {d:%A}"
        weekday_checked += 1
        assert d.year == year, f"BLS {year} page carries a {d.year} row: {txt}"
        hh, mm = parse_clock(strip_tags(time_cell))
        out.append({"event": event, "date": d, "hh": hh, "mm": mm, "desc": strip_tags(desc)})
    assert weekday_checked == len(out)
    return out


BLS_SERIES_ROW = re.compile(r"<tr[^>]*>\s*<t[dh][^>]*>(.*?)</t[dh]>\s*<t[dh][^>]*>(.*?)</t[dh]>\s*<t[dh][^>]*>(.*?)</t[dh]>\s*</tr>", re.S)


def parse_bls_series(html):
    """The forward per-release page: Reference Month | Release Date | Release Time. Cross-check only."""
    out = []
    for ref, rel, tm in BLS_SERIES_ROW.findall(html[html.find("MAIN CONTENT BEGIN"):]):
        ref, rel, tm = strip_tags(ref), strip_tags(rel), strip_tags(tm)
        if not re.match(r"^[A-Za-z]{3}", rel) or "Release Date" in rel:
            continue
        try:
            d = parse_us_date(rel)
            hh, mm = parse_clock(tm)
        except AssertionError:
            continue
        out.append({"ref": ref, "date": d, "hh": hh, "mm": mm})
    return out


# --------------------------------------------------------------------------- FOMC

HEADING = re.compile(
    r"^(?P<mon>[A-Za-z]+(?:/[A-Za-z]+)?)\s+(?P<days>[\d–-]+)\*?\s*"
    r"(?:\((?P<tag>[^)]*)\))?\s*(?:Meeting)?\s*(?:-\s*(?P<yr>\d{4}))?\s*$")
STATEMENT = re.compile(r'href="(/newsevents/pressreleases/monetary(\d{8})a\.htm)"')


def meeting_last_day(mon_text, days_text, year):
    """'April/May' + '30-1' -> 1 May; 'January' + '26-27' -> 27 January; 'October' + '4' -> 4 October."""
    months = [m for m in mon_text.split("/") if m.strip()]
    # the calendars page marks a meeting with a Summary of Economic Projections as '17-18*'
    parts = [p for p in re.split(r"[–-]", re.sub(r"[^\d–-]", "", days_text)) if p.strip()]
    day = int(parts[-1])
    name = months[-1].strip().lower()
    mnum = next((v for k, v in MONTHS.items() if k.startswith(name)), None)
    assert mnum, f"unknown month {mon_text!r}"
    y = year
    if len(months) > 1 and MONTHS[[k for k in MONTHS if k.startswith(months[0].strip().lower())][0]] == 12 and mnum == 1:
        y += 1
    return date(y, mnum, day)


def parse_fomc_hist(html, year):
    """One panel a meeting: `<h5 class="panel-heading...">January 26-27 Meeting - 2016</h5>`."""
    out = []
    for chunk in html.split('<div class="panel panel-default panel-padded">')[1:]:
        h = re.search(r'panel-heading[^>]*>(.*?)</h5>', chunk, re.S)
        if not h:
            continue
        head = strip_tags(h.group(1))
        m = HEADING.match(head)
        assert m, f"FOMC {year}: unparsed panel heading {head!r}"
        stmts = sorted({s for s, _ in STATEMENT.findall(chunk)})
        assert len(stmts) <= 1, f"FOMC {year}: {head!r} has {len(stmts)} statement links"
        out.append({"heading": head, "tag": (m.group("tag") or "").strip().lower(),
                    "last_day": meeting_last_day(m.group("mon"), m.group("days"), int(m.group("yr") or year)),
                    "statement": stmts[0] if stmts else None})
    return out


FOMC_CAL_ROW = re.compile(
    r'fomc-meeting__month[^>]*>(?:\s*<strong>)?(.*?)(?:</strong>\s*)?</div>\s*'
    r'<div class="fomc-meeting__date[^>]*>(.*?)</div>(?P<rest>.*?)(?=<div class="row fomc-meeting|'
    r'<div class="fomc-meeting--shaded row fomc-meeting|<div class="panel-footer|<div class="panel panel-default">|\Z)', re.S)


def parse_fomc_cal(html):
    """fomccalendars.htm: one `<div class="panel panel-default">` a YEAR, `fomc-meeting` rows inside."""
    out = []
    for chunk in html.split('<div class="panel panel-default">')[1:]:
        ym = re.search(r"<h4><a id=\"\d+\">(\d{4}) FOMC Meetings</a></h4>", chunk)
        if not ym:
            continue
        year = int(ym.group(1))
        for mon, days, rest in FOMC_CAL_ROW.findall(chunk):
            mon, days = strip_tags(mon), strip_tags(days)
            if not mon or not days:
                continue
            stmts = sorted({s for s, _ in STATEMENT.findall(rest)})
            assert len(stmts) <= 1, f"FOMC {year}: {mon} {days} has {len(stmts)} statement links"
            # the date cell carries the label too: '22 (notation vote)', '17-18*'
            tagm = re.search(r"\(([^)]*)\)", f"{mon} {days}")
            out.append({"heading": f"{mon} {days} - {year}",
                        "tag": (tagm.group(1).strip().lower() if tagm else ""),
                        "last_day": meeting_last_day(mon, days, year),
                        "statement": stmts[0] if stmts else None})
    return out


PR_TIME = re.compile(r"[Ff]or release at\s+(\d{1,2}:\d{2}\s*[ap]\.?\s*m\.?)\s*(E[SD]T)")


def parse_fomc_pr(html, url):
    """The statement press release states its own release clock AND its own zone abbreviation."""
    txt = strip_tags(html[:200_000])
    m = PR_TIME.search(txt)
    assert m, f"no 'For release at' line in {url}"
    hh, mm = parse_clock(m.group(1))
    return hh, mm, m.group(2)


# --------------------------------------------------------------------------- EIA

EIA_STANDARD = re.compile(
    r"standard release time and day of the week will be at\s+(?P<clock>\d{1,2}:\d{2}\s*[ap]\.?\s*m\.?)\s*"
    r"\(?[Ee]astern(?:\s+time)?\)?\s+on\s+(?P<day>[A-Za-z]+)s", re.S)
WEEKDAY_NUM = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4}


def parse_eia_standard(html):
    """The standard day and clock are READ OFF THE PAGE. Nothing downstream hard-codes Wednesday/Thursday."""
    txt = strip_tags(html)
    m = EIA_STANDARD.search(txt)
    assert m, "EIA page does not state its standard release day and time"
    hh, mm = parse_clock(m.group("clock"))
    day = m.group("day").strip().lower()
    assert day in WEEKDAY_NUM, f"EIA standard day {day!r} unknown"
    return WEEKDAY_NUM[day], hh, mm


TR = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
TD = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S)


def parse_eia_exceptions(html):
    """The holiday table. Petroleum has 5 columns (the first is 'Data for the week ending'); gas has 4."""
    out = []
    i = html.find("Holiday Release Schedule")
    assert i >= 0, "EIA page has no Holiday Release Schedule section"
    for tr in TR.findall(html[i:]):
        cells = [strip_tags(c) for c in TD.findall(tr)]
        cells = [c for c in cells if c not in ("", "&nbsp;")]
        if len(cells) not in (4, 5):
            continue
        if any(re.search(r"week ending|alternate release", c, re.I) for c in cells):
            continue
        try:
            if len(cells) == 5:
                wk, alt, day, clock, holiday = cells
                week_ending = parse_us_date(wk)
            else:
                week_ending = None
                alt, day, clock, holiday = cells
            alt_d = parse_us_date(alt)
            hh, mm = parse_clock(clock)
        except AssertionError:
            continue
        assert alt_d.strftime("%A").lower() == day.strip().lower(), \
            f"EIA exception: page says {day} for {alt_d} which is a {alt_d:%A}"
        hol = None
        m = re.match(r"^(\d{1,2}/\d{1,2}/\d{4})", holiday)
        if m:
            hol = parse_us_date(m.group(1))
        out.append({"week_ending": week_ending, "alt": alt_d, "hh": hh, "mm": mm,
                    "holiday": holiday, "holiday_date": hol})
    return out


def match_alternates_to_thursdays(alts, std_weekday, window=6):
    """Minimum-cost ORDER-PRESERVING assignment of alternate dates onto standard-weekday slots.

    Nearest-slot is wrong at a year end: 2025 has alternates Mon 12-29 (Christmas) and Wed 12-31 (New
    Year), and the Thursday nearest 12-29 is 2026-01-01, which belongs to 12-31. Strictly increasing
    assignment with a +-`window` day bound resolves it, and the caller checks the result against the
    source's own holiday dates where it prints them."""
    alts = sorted(alts)
    if not alts:
        return {}
    lo, hi = alts[0] - timedelta(days=window), alts[-1] + timedelta(days=window)
    slots = []
    d = lo
    while d <= hi:
        if d.weekday() == std_weekday:
            slots.append(d)
        d += timedelta(days=1)
    n, m = len(alts), len(slots)
    INF = 10 ** 9
    # best[i][j] = min cost assigning alts[i:] into slots[j:]
    best = [[INF] * (m + 1) for _ in range(n + 1)]
    choice = [[-1] * (m + 1) for _ in range(n + 1)]
    for j in range(m + 1):
        best[n][j] = 0
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            cost = abs((alts[i] - slots[j]).days)
            take = cost + best[i + 1][j + 1] if cost <= window else INF
            skip = best[i][j + 1]
            if take <= skip:
                best[i][j], choice[i][j] = take, 1
            else:
                best[i][j], choice[i][j] = skip, 0
    assert best[0][0] < INF, "EIA: an alternate release date has no standard slot within the window"
    out, i, j = {}, 0, 0
    while i < n and j < m:
        if choice[i][j] == 1:
            out[slots[j]] = alts[i]
            i += 1
            j += 1
        else:
            j += 1
    assert len(out) == n, "EIA: order-preserving match did not place every alternate"
    return out


# --------------------------------------------------------------------------- probe

def probe(log=print):
    log("probe -- metadata only, nothing is written")
    log("  BLS year schedules:")
    for y in range(2016, 2029):
        st, n = _head(f"https://www.bls.gov/schedule/{y}/home.htm")
        log(f"    {y}: HTTP {st}  {n} bytes")
        time.sleep(0.3)
    for u in ("https://www.bls.gov/schedule/news_release/cpi.htm",
              "https://www.bls.gov/schedule/news_release/empsit.htm"):
        st, n = _head(u)
        log(f"    {u.rsplit('/', 1)[-1]}: HTTP {st}  {n} bytes")
        time.sleep(0.3)
    log("  Federal Reserve:")
    for y in FOMC_HIST_YEARS:
        st, n = _head(f"https://www.federalreserve.gov/monetarypolicy/fomchistorical{y}.htm")
        log(f"    fomchistorical{y}: HTTP {st}  {n} bytes")
        time.sleep(0.3)
    st, n = _head("https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm")
    log(f"    fomccalendars: HTTP {st}  {n} bytes")
    log("  EIA live schedules and their Wayback depth:")
    for ev, (_, url, key, _) in SCHEDULE_PAGES.items():
        st, n = _head(url)
        caps = cdx(key)
        by_year = {}
        for ts in caps:
            by_year[ts[:4]] = by_year.get(ts[:4], 0) + 1
        log(f"    {ev}: live HTTP {st} {n} bytes; {len(caps)} distinct Wayback digests "
            f"{ {k: v for k, v in sorted(by_year.items())} }")
        time.sleep(1.0)
    return 0


# --------------------------------------------------------------------------- fetch

def fetch(log=print):
    t0 = time.time()
    man = load_manifest()
    log("fetch: BLS year schedules")
    for y in BLS_YEARS:
        acquire(man, f"bls_schedule_{y}", f"https://www.bls.gov/schedule/{y}/home.htm", "fetched", PAUSE_GOV, log)
    log("fetch: BLS forward per-release schedules (cross-check)")
    for name in ("cpi", "empsit"):
        acquire(man, f"bls_forward_{name}", f"https://www.bls.gov/schedule/news_release/{name}.htm",
                "fetched", PAUSE_GOV, log)
    log("fetch: FOMC meeting pages")
    for y in FOMC_HIST_YEARS:
        acquire(man, f"fomc_hist_{y}", f"https://www.federalreserve.gov/monetarypolicy/fomchistorical{y}.htm",
                "fetched", PAUSE_GOV, log)
    acquire(man, "fomc_calendars", "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            "fetched", PAUSE_GOV, log)

    log("fetch: FOMC statement press releases (each states its own release clock)")
    hrefs = set()
    for y in FOMC_HIST_YEARS:
        html, _ = read_raw(man, f"fomc_hist_{y}")
        hrefs |= {p["statement"] for p in parse_fomc_hist(html, y) if p["statement"]}
    html, _ = read_raw(man, "fomc_calendars")
    hrefs |= {p["statement"] for p in parse_fomc_cal(html) if p["statement"]}
    for href in sorted(hrefs):
        stamp = re.search(r"monetary(\d{8})a\.htm", href).group(1)
        acquire(man, f"fomc_pr_{stamp}", "https://www.federalreserve.gov" + href, "fetched", PAUSE_GOV, log)

    log("fetch: EIA live schedules")
    for ev, (slug, url, _, _) in SCHEDULE_PAGES.items():
        acquire(man, f"{slug}_live", url, "fetched", PAUSE_GOV, log)
    log("fetch: Wayback captures of the same two EIA URLs (prior-year exception tables)")
    for ev, (slug, url, key, _) in SCHEDULE_PAGES.items():
        caps = pick_captures(cdx(key))
        log(f"  {ev}: {len(caps)} captures selected")
        for ts in caps:
            cite, fetch_url = wb_urls(ts, url)
            try:
                acquire(man, f"{slug}_wb_{ts}", cite, "archived", PAUSE_WB, log, fetch_url=fetch_url)
            except (RuntimeError, urllib.error.HTTPError) as exc:
                log(f"    {ts}: SKIPPED ({type(exc).__name__})")
    save_manifest(man)
    log(f"fetch done in {time.time() - t0:.0f} s; {len(man)} raw responses cached")
    return 0


# --------------------------------------------------------------------------- build

def build_bls(man, notes, log):
    rows, seen_years = [], []
    for y in BLS_YEARS:
        key = f"bls_schedule_{y}"
        if key not in man:
            notes["not_fetched"].append({"what": f"BLS schedule {y}", "reason": "not in the raw cache; run --fetch"})
            continue
        html, rec = read_raw(man, key)
        seen_years.append(y)
        for r in parse_bls_year(html, y):
            d = r["date"]
            if r["event"] == "EMPSIT":
                nominal = first_friday(d.year, d.month)
            else:
                nominal = ""
            rows.append(row(r["event"], d, r["hh"], r["mm"], rec["url"], nominal,
                            bool(nominal) and nominal != d, rec["method"], rec["accessed_utc"]))
    # second source: the forward per-release pages
    cross = {"agree": 0, "only_on_the_forward_page": [], "disagree": []}
    have = {(x["event"], x["datetime_et"][:10]) for x in rows}
    for name, event in (("cpi", "CPI"), ("empsit", "EMPSIT")):
        key = f"bls_forward_{name}"
        if key not in man:
            continue
        html, rec = read_raw(man, key)
        for r in parse_bls_series(html):
            if r["date"].year not in seen_years:
                continue
            if (event, r["date"].isoformat()) in have:
                cross["agree"] += 1
            else:
                cross["only_on_the_forward_page"].append({"event": event, "date": r["date"].isoformat(),
                                                          "source_url": rec["url"]})
    notes["bls_year_page_vs_forward_page"] = cross
    return rows


def build_fomc(man, notes, log):
    panels = []
    for y in FOMC_HIST_YEARS:
        key = f"fomc_hist_{y}"
        if key not in man:
            notes["not_fetched"].append({"what": f"FOMC historical {y}", "reason": "not in the raw cache"})
            continue
        html, rec = read_raw(man, key)
        for p in parse_fomc_hist(html, y):
            panels.append({**p, "src": rec})
    if "fomc_calendars" in man:
        html, rec = read_raw(man, "fomc_calendars")
        for p in parse_fomc_cal(html):
            panels.append({**p, "src": rec})

    rows, no_time, tags, mismatches = [], [], {}, []
    for p in panels:
        tags[p["tag"] or "scheduled"] = tags.get(p["tag"] or "scheduled", 0) + 1
        if p["tag"] == "cancelled":
            notes["fomc_panels_excluded"].append({"panel": p["heading"], "reason": "cancelled, no statement"})
            continue
        if not p["statement"]:
            no_time.append({"meeting_last_day": p["last_day"].isoformat(), "panel": p["heading"],
                            "source_url": p["src"]["url"]})
            continue
        stamp = re.search(r"monetary(\d{8})a\.htm", p["statement"]).group(1)
        key = f"fomc_pr_{stamp}"
        if key not in man:
            no_time.append({"meeting_last_day": p["last_day"].isoformat(), "panel": p["heading"],
                            "source_url": p["src"]["url"], "reason": "statement press release not in the raw cache"})
            continue
        html, rec = read_raw(man, key)
        hh, mm, zone = parse_fomc_pr(html, rec["url"])
        sd = date(int(stamp[:4]), int(stamp[4:6]), int(stamp[6:]))
        want = "EDT" if datetime(sd.year, sd.month, sd.day, 12, tzinfo=ET).dst() else "EST"
        assert zone == want, f"FOMC {sd}: page says {zone}, America/New_York says {want}"
        scheduled = p["tag"] == ""
        gap = abs((sd - p["last_day"]).days)
        if scheduled:
            if sd != p["last_day"]:
                mismatches.append({"panel": p["heading"], "meeting_last_day": p["last_day"].isoformat(),
                                   "statement_date": sd.isoformat()})
            event = "FOMC"
        else:
            event = "FOMC_UNSCHEDULED"
            if gap > 1:
                notes["fomc_unscheduled_meetings_without_a_same_day_statement"].append(
                    {"panel": p["heading"], "meeting_last_day": p["last_day"].isoformat(),
                     "statement_the_fed_attaches": sd.isoformat(), "source_url": p["src"]["url"],
                     "consequence": "the CSV row is the statement, not the meeting; no clock was ever "
                                    "published for the meeting day, so no row is written for it"})
        rows.append(row(event, sd, hh, mm, "https://www.federalreserve.gov" + p["statement"],
                        p["last_day"], sd != p["last_day"], "fetched", rec["accessed_utc"]))
    notes["fomc_panel_tags"] = tags
    notes["fomc_statement_day_not_the_meetings_last_day"] = mismatches
    notes["fomc_meetings_with_no_published_release_clock"] = sorted(no_time, key=lambda r: r["meeting_last_day"])
    assert not mismatches, f"G3: {len(mismatches)} scheduled FOMC statements not on the meeting's last day: {mismatches[:3]}"
    return rows


def build_eia(man, notes, log):
    rows = []
    for event, (slug, live_url, _, want_weekday) in SCHEDULE_PAGES.items():
        pages = []
        if f"{slug}_live" in man:
            pages.append((f"{slug}_live", man[f"{slug}_live"]))
        pages += sorted(((k, v) for k, v in man.items() if k.startswith(f"{slug}_wb_")), key=lambda kv: kv[0])
        if not pages:
            notes["not_fetched"].append({"what": event, "reason": "no schedule page in the raw cache"})
            continue
        std = None
        # nominal date -> {alt, hh, mm, holiday, src, order}. Later pages win; conflicts recorded.
        exc, conflicts, by_year_sources = {}, [], {}
        for order, (key, rec) in enumerate(sorted(pages, key=lambda kv: kv[1]["url"])):
            html, _ = read_raw(man, key)
            try:
                wd, shh, smm = parse_eia_standard(html)
                raw_exc = parse_eia_exceptions(html)
            except AssertionError as e:
                notes["schedule_pages_unparsed"].append({"key": key, "url": rec["url"], "reason": str(e)[:120]})
                continue
            assert wd == want_weekday, f"{event}: page states a {wd} standard day, expected {want_weekday}"
            if std is None:
                std = (wd, shh, smm)
            assert std == (wd, shh, smm), f"{event}: schedule pages disagree on the standard release slot"
            if raw_exc and raw_exc[0]["week_ending"] is not None:
                pairs = [(e["week_ending"] + timedelta(days=5), e) for e in raw_exc]
                for nom, e in pairs:
                    assert nom.weekday() == want_weekday, \
                        f"{event}: week ending {e['week_ending']} implies {nom}, a {nom:%A}"
            else:
                mapping = match_alternates_to_thursdays([e["alt"] for e in raw_exc], want_weekday)
                rev = {v: k for k, v in mapping.items()}
                pairs = [(rev[e["alt"]], e) for e in raw_exc]
                for nom, e in pairs:
                    if e["holiday_date"]:
                        assert abs((nom - e["holiday_date"]).days) <= 2, \
                            f"{event}: matched {e['alt']} to {nom} but the page names {e['holiday_date']}"
            # the page ordinal: a capture's timestamp sorts, the live page is newest
            # the live page is the newest statement of the schedule; a capture ranks by its timestamp
            rank = 99_999_999_999_999 if key.endswith("_live") else int(key.rsplit("_", 1)[-1])
            for nom, e in pairs:
                by_year_sources.setdefault(nom.year, {}).setdefault(rec["url"], 0)
                by_year_sources[nom.year][rec["url"]] += 1
                prev = exc.get(nom)
                if prev and (prev["alt"], prev["hh"], prev["mm"]) != (e["alt"], e["hh"], e["mm"]):
                    new = {"alt": e["alt"].isoformat(), "time": f"{e['hh']:02d}:{e['mm']:02d}", "source_url": rec["url"]}
                    old = {"alt": prev["alt"].isoformat(), "time": f"{prev['hh']:02d}:{prev['mm']:02d}",
                           "source_url": prev["src"]["url"]}
                    later = rank >= prev["rank"]
                    conflicts.append({"nominal": nom.isoformat(),
                                      "kept": new if later else old, "dropped": old if later else new,
                                      "rule": "the later statement of the schedule wins"})
                if prev is None or rank >= prev["rank"]:
                    exc[nom] = {**e, "src": rec, "rank": rank}
        assert std is not None, f"{event}: no page stated the standard release slot"
        wd, shh, smm = std

        # which years does a schedule page actually govern? the page with the most exception rows for
        # that year, latest capture breaking a tie -- its standard sentence is what a normal week cites.
        governing = {}
        for y, urls in by_year_sources.items():
            governing[y] = max(sorted(urls.items()), key=lambda kv: kv[1])[0]
        url_to_rec = {rec["url"]: rec for _, rec in pages}
        years = sorted(set(list(governing) + [n.year for n in exc]))
        covered = [y for y in years if y >= SPAN_START.year]
        if not covered:
            continue
        end = date(max(covered), 12, 31)
        d = SPAN_START
        while d.weekday() != wd:
            d += timedelta(days=1)
        while d <= end:
            e = exc.get(d)
            if e is not None:
                rec = e["src"]
                rows.append(row(event, e["alt"], e["hh"], e["mm"], rec["url"], d, True,
                                rec["method"], rec["accessed_utc"]))
            else:
                gurl = governing.get(d.year)
                if gurl is None and governing:
                    # a year with no exception at all: the nearest year's page states the same standard
                    near = min(governing, key=lambda y: (abs(y - d.year), y))
                    gurl = governing[near]
                    notes["eia_years_governed_by_a_neighbouring_pages_table"].append(
                        {"event": event, "year": d.year, "governing_year": near, "source_url": gurl})
                if gurl is None:
                    notes["not_fetched"].append({"what": f"{event} {d.isoformat()}",
                                                 "reason": "no schedule page covering this year"})
                    d += timedelta(days=7)
                    continue
                rec = url_to_rec[gurl]
                rows.append(row(event, d, shh, smm, rec["url"], d, False, rec["method"], rec["accessed_utc"]))
            d += timedelta(days=7)
        # EIA can publish two data weeks at ONE instant -- after the June 2022 systems outage the
        # week-ending 2022-06-17 and 2022-06-24 petroleum reports both came out on 2022-06-29 10:30.
        # That is one release EVENT, so the rows collapse and the nominals both go in the meta; G6
        # stays absolute rather than growing an exception.
        by_instant = {}
        for r in rows:
            if r["event"] != event:
                continue
            by_instant.setdefault(r["datetime_et"], []).append(r)
        for when, group in sorted(by_instant.items()):
            if len(group) == 1:
                continue
            keep = min(group, key=lambda r: r["release_date_nominal"])
            for r in group:
                if r is not keep:
                    rows.remove(r)
            notes["eia_release_instants_covering_more_than_one_data_week"].append(
                {"event": event, "datetime_et": when,
                 "nominal_dates_collapsed": sorted(r["release_date_nominal"] for r in group),
                 "kept_nominal": keep["release_date_nominal"], "source_url": keep["source_url"]})

        notes["eia_schedule_pages"][event] = {
            "standard": f"{shh:02d}:{smm:02d} ET on {['Monday','Tuesday','Wednesday','Thursday','Friday'][wd]}s, "
                        f"read from the page's own sentence",
            "pages_used": len(pages), "exceptions_found": len(exc),
            "exceptions_per_year": {str(y): sum(1 for n in exc if n.year == y) for y in sorted({n.year for n in exc})},
            "governing_page_per_year": {str(y): governing[y] for y in sorted(governing)},
            "last_exception_listed": max(exc).isoformat() if exc else None,
            "conflicts_between_captures": conflicts,
        }
    return rows


def gates(rows, notes, log=print):
    """G1..G6. Every one raises; the selftest proves each raise fires."""
    report = {}
    # ---- G1: provenance on every row
    bad = [r for r in rows if not r["source_url"] or r["method"] not in VALID_METHODS]
    assert not bad, f"G1: {len(bad)} rows without a source_url or with method not in {VALID_METHODS}: {bad[:2]}"
    report["G1"] = {"rule": "every row carries a source_url and a method in {fetched, archived}",
                    "rows": len(rows), "by_method": {m: sum(1 for r in rows if r["method"] == m) for m in VALID_METHODS}}
    # ---- G6: no duplicate key
    keys = [(r["event"], r["datetime_et"]) for r in rows]
    dupes = sorted({k for k in keys if keys.count(k) > 1}) if len(set(keys)) != len(keys) else []
    assert not dupes, f"G6: duplicate (event, datetime_et): {dupes[:5]}"
    report["G6"] = {"rule": "no duplicate (event, datetime_et)", "duplicates": 0}
    # ---- G2: per-year counts
    per = {}
    for r in rows:
        per.setdefault(r["event"], {}).setdefault(r["datetime_et"][:4], 0)
        per[r["event"]][r["datetime_et"][:4]] += 1
    failing = []
    for ev, (lo, hi) in COUNT_RANGE.items():
        for y, n in sorted(per.get(ev, {}).items()):
            if not (lo <= n <= hi):
                failing.append({"event": ev, "year": y, "count": n, "declared": [lo, hi]})
    known = {(f["event"], f["year"]) for f in failing} <= {(k["event"], k["year"]) for k in notes["partial_or_disrupted_years"]}
    assert known, ("G2: a year is outside its declared count range and is not named in "
                   f"partial_or_disrupted_years: {[f for f in failing if (f['event'], f['year']) not in {(k['event'], k['year']) for k in notes['partial_or_disrupted_years']}][:4]}")
    report["G2"] = {"rule": {k: list(v) for k, v in COUNT_RANGE.items()},
                    "years_outside_the_declared_range": failing}
    # ---- G3: weekday audits
    w = {"cpi_or_empsit_on_a_weekend": [], "empsit_not_on_a_friday_and_not_flagged": [],
         "cpi_or_empsit_not_at_0830": []}
    for r in rows:
        if r["event"] not in ("CPI", "EMPSIT"):
            continue
        d = date.fromisoformat(r["datetime_et"][:10])
        if d.weekday() >= 5:
            w["cpi_or_empsit_on_a_weekend"].append(r["datetime_et"])
        if r["datetime_et"][11:16] != "08:30":
            w["cpi_or_empsit_not_at_0830"].append({"event": r["event"], "when": r["datetime_et"]})
        if r["event"] == "EMPSIT" and d.weekday() != 4 and r["holiday_shift"] != "True":
            w["empsit_not_on_a_friday_and_not_flagged"].append(r["datetime_et"])
    assert not w["cpi_or_empsit_on_a_weekend"], f"G3: CPI/EMPSIT on a weekend: {w['cpi_or_empsit_on_a_weekend'][:4]}"
    assert not w["empsit_not_on_a_friday_and_not_flagged"], \
        f"G3: EMPSIT off a Friday without holiday_shift: {w['empsit_not_on_a_friday_and_not_flagged'][:4]}"
    fomc_bad = [r["datetime_et"] for r in rows if r["event"] == "FOMC"
                and r["datetime_et"][:10] != r["release_date_nominal"]]
    assert not fomc_bad, f"G3: FOMC statement not on the meeting's last day: {fomc_bad[:4]}"
    report["G3"] = {"rule": "CPI/EMPSIT on weekdays; EMPSIT on a Friday unless holiday_shift; "
                            "FOMC statement on the meeting's last day", **w,
                    "empsit_rows_flagged_holiday_shift": sum(1 for r in rows if r["event"] == "EMPSIT" and r["holiday_shift"] == "True")}
    # ---- G4: agreement with data/macro_release_calendar.json, 2016-2024
    dis = notes["disagreements_with_macro_release_calendar_json"]
    report["G4"] = {"rule": "for 2016-2024 the CPI, EMPSIT and FOMC date sets equal "
                            "data/macro_release_calendar.json, or every difference is listed",
                    "differences": len(dis)}
    # ---- G5: DST, asserted in code
    jan_et, jan_utc = et_pair(date(2016, 1, 20), 8, 30)
    jul_et, jul_utc = et_pair(date(2016, 7, 15), 8, 30)
    assert jan_utc.endswith("13:30:00Z"), f"G5: 08:30 ET in January is not 13:30 UTC: {jan_utc}"
    assert jul_utc.endswith("12:30:00Z"), f"G5: 08:30 ET in July is not 12:30 UTC: {jul_utc}"
    assert jan_et.endswith("-05:00") and jul_et.endswith("-04:00"), "G5: ET offsets wrong"
    winter = [r for r in rows if r["datetime_et"][5:7] == "01" and r["datetime_et"][11:16] == "08:30"]
    summer = [r for r in rows if r["datetime_et"][5:7] == "07" and r["datetime_et"][11:16] == "08:30"]
    assert all(r["datetime_utc"][11:16] == "13:30" for r in winter), "G5: a January 08:30 ET row is not 13:30 UTC"
    assert all(r["datetime_utc"][11:16] == "12:30" for r in summer), "G5: a July 08:30 ET row is not 12:30 UTC"
    report["G5"] = {"rule": "08:30 ET -> 13:30 UTC in January, 12:30 UTC in July",
                    "january_0830_rows": len(winter), "july_0830_rows": len(summer)}
    return report


def compare_macro(rows, notes):
    if not MACRO.exists():
        notes["not_fetched"].append({"what": "macro_release_calendar.json comparison", "reason": "file missing"})
        return
    macro = json.loads(MACRO.read_text(encoding="utf-8"))
    ours = {}
    for r in rows:
        ours.setdefault(r["event"], set()).add(r["datetime_et"][:10])
    theirs = {"CPI": set(macro.get("cpi_release_days", [])),
              "EMPSIT": set(macro.get("empsit_release_days", [])),
              "FOMC": set(macro.get("fomc_statement_days", [])),
              "FOMC_UNSCHEDULED": set(macro.get("fomc_unscheduled", []))}
    out = notes["disagreements_with_macro_release_calendar_json"]
    for ev, t in theirs.items():
        if not t:
            continue
        years = {d[:4] for d in t}
        o = {d for d in ours.get(ev, set()) if d[:4] in years}
        for d in sorted(t - o):
            out.append({"event": ev, "date": d, "in": "macro_release_calendar.json only"})
        for d in sorted(o - t):
            out.append({"event": ev, "date": d, "in": "data/calendar/events.csv only"})
    notes["macro_release_calendar_json_span"] = {ev: (min(t)[:4] + ".." + max(t)[:4]) for ev, t in theirs.items() if t}


def build(log=print):
    t0 = time.time()
    man = load_manifest()
    assert man, "no raw responses cached; run --fetch first"
    notes = {"not_fetched": [], "fomc_panels_excluded": [],
             "fomc_unscheduled_meetings_without_a_same_day_statement": [],
             "schedule_pages_unparsed": [], "eia_schedule_pages": {},
             "eia_years_governed_by_a_neighbouring_pages_table": [],
             "eia_release_instants_covering_more_than_one_data_week": [],
             "disagreements_with_macro_release_calendar_json": [],
             "partial_or_disrupted_years": []}
    rows = build_bls(man, notes, log) + build_fomc(man, notes, log) + build_eia(man, notes, log)
    rows.sort(key=lambda r: (r["datetime_utc"], r["event"]))

    # years the sources themselves show as short, named BEFORE G2 reads them
    per = {}
    for r in rows:
        per.setdefault(r["event"], {}).setdefault(r["datetime_et"][:4], 0)
        per[r["event"]][r["datetime_et"][:4]] += 1
    for ev, (lo, hi) in COUNT_RANGE.items():
        for y, n in sorted(per.get(ev, {}).items()):
            if lo <= n <= hi:
                continue
            if ev in ("CPI", "EMPSIT") and y == "2025":
                why = ("the federal funding lapse of 2025-10-01..2025-11-12: BLS's own 2025 schedule "
                       "carries no October CPI and no October Employment Situation")
            elif ev == "FOMC" and y in ("2026", "2027"):
                why = ("meetings scheduled but not yet held: no statement press release exists, so no "
                       "release clock has been published -- see fomc_meetings_with_no_published_release_clock")
            elif ev == "FOMC" and y == "2020":
                why = "the Fed's own 2020 page lists seven scheduled meetings; March 17-18 was cancelled"
            else:
                why = "see the per-year source coverage above"
            notes["partial_or_disrupted_years"].append({"event": ev, "year": y, "count": n, "reason": why})

    compare_macro(rows, notes)
    report = gates(rows, notes, log)

    meta = {
        "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fetcher": "scripts/fetch_release_calendar.py",
        "record": "D585",
        "span": {"from": SPAN_START.isoformat(),
                 "to": max(r["datetime_et"][:10] for r in rows),
                 "per_event": {ev: {"first": min(r["datetime_et"][:10] for r in rows if r["event"] == ev),
                                    "last": max(r["datetime_et"][:10] for r in rows if r["event"] == ev),
                                    "rows": sum(1 for r in rows if r["event"] == ev)}
                               for ev in sorted({r["event"] for r in rows})}},
        "conventions": {
            "datetime_et": "ISO 8601 with the America/New_York offset; the clock is the source's own",
            "datetime_utc": "the same instant in UTC",
            "release_date_nominal": "the date the release WOULD fall on under the source's own standard "
                                    "rule: EMPSIT the first Friday of the month, EIA the standard weekday, "
                                    "FOMC the meeting's last day. A DESCRIPTOR computed from the sourced "
                                    "date, never a source of one. Empty for CPI, which has no day rule.",
            "holiday_shift": "the sourced date differs from release_date_nominal. For EIA it is exactly "
                             "the page's own holiday exception table; for EMPSIT it also covers the 2019 "
                             "and 2025 funding lapses, which are named in partial_or_disrupted_years.",
            "method": "fetched = off the live official page; archived = off a Wayback capture of that "
                      "same official URL, which is the source_url. 'inferred' is REFUSED by the builder.",
            "eia_rows_without_an_exception": "EIA publishes a standard sentence plus an exception table, "
                                             "not a list of weeks. A normal week's date and time come from "
                                             "the standard sentence parsed off the governing page for that "
                                             "year and that page's table not listing the week. Unannounced "
                                             "delays are not visible to any published schedule.",
        },
        "sources": {k: {"url": v["url"], "method": v["method"], "accessed_utc": v["accessed_utc"],
                        "bytes": v["bytes"], "sha256": v["sha256"]} for k, v in sorted(man.items())},
        "rows": len(rows),
        "rows_per_event_per_year": {ev: dict(sorted(per[ev].items())) for ev in sorted(per)},
        "gates": report,
        **{k: v for k, v in notes.items()},
    }
    missing = [k for k in REQUIRED_OUTPUTS if k not in meta]
    assert not missing, f"REQUIRED_OUTPUTS missing from the meta: {missing}"

    OUTDIR.mkdir(parents=True, exist_ok=True)
    with open(CSV, "w", encoding="utf-8", newline="\n") as f:
        f.write(",".join(COLUMNS) + "\n")
        for r in rows:
            f.write(",".join(('"' + r[c].replace('"', '""') + '"') if "," in r[c] else r[c] for c in COLUMNS) + "\n")
    META.write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    log(f"  wrote {CSV.relative_to(REPO)} ({len(rows)} rows) and {META.relative_to(REPO)}")
    for ev in sorted(per):
        log(f"    {ev}: " + " ".join(f"{y}:{n}" for y, n in sorted(per[ev].items())))
    if notes["partial_or_disrupted_years"]:
        log("  years outside the declared count range (each named with a reason):")
        for p in notes["partial_or_disrupted_years"]:
            log(f"    {p['event']} {p['year']}: {p['count']}")
    log(f"  disagreements with macro_release_calendar.json: {len(notes['disagreements_with_macro_release_calendar_json'])}")
    log(f"  build done in {time.time() - t0:.0f} s")
    return 0


# --------------------------------------------------------------------------- selftest

def _clean_rows():
    """A synthetic year that passes every gate: 12 CPI, 12 EMPSIT (first Fridays), 8 FOMC, 52 of each EIA."""
    out = []
    for m in range(1, 13):
        ff = first_friday(2020, m)
        out.append(row("CPI", ff + timedelta(days=7), 8, 30, "u", "", False, "fetched", "t"))
        out.append(row("EMPSIT", ff, 8, 30, "u", ff, False, "fetched", "t"))
    for m in (1, 3, 4, 6, 7, 9, 11, 12):
        d = first_friday(2020, m) + timedelta(days=12)   # a Wednesday, inside the month
        out.append(row("FOMC", d, 14, 0, "u", d, False, "fetched", "t"))
    for ev, wd in (("EIA_WPSR", 2), ("EIA_NGSR", 3)):
        d = date(2020, 1, 1)
        while d.weekday() != wd:
            d += timedelta(days=1)
        while d.year == 2020:
            out.append(row(ev, d, 10, 30, "u", d, False, "fetched", "t"))
            d += timedelta(days=7)
    return out


def _notes():
    return {"disagreements_with_macro_release_calendar_json": [], "partial_or_disrupted_years": []}


def selftest(log=print):
    log("selftest: the gates pass a clean case and RAISE on a deliberate break")
    clean = _clean_rows()
    rep = gates(clean, _notes(), log)
    assert rep["G1"]["rows"] == len(clean)
    log(f"  clean case: {len(clean)} rows, all six gates pass")

    expect_raise(lambda: gates([{**clean[0], "method": "inferred"}] + clean[1:], _notes()),
                 "method=inferred (G1) -- the builder REFUSES an inferred row", log)
    expect_raise(lambda: gates([{**clean[0], "source_url": ""}] + clean[1:], _notes()),
                 "an empty source_url (G1)", log)
    expect_raise(lambda: gates(clean + [clean[0]], _notes()), "a duplicate (event, datetime_et) (G6)", log)
    expect_raise(lambda: gates([r for r in clean if r["event"] != "CPI"][:] +
                               [r for r in clean if r["event"] == "CPI"][:11], _notes()),
                 "11 CPI rows in a year (G2)", log)
    sat = date(2020, 2, 15)
    assert sat.weekday() == 5
    expect_raise(lambda: gates([row("CPI", sat, 8, 30, "u", "", False, "fetched", "t")] +
                               [r for r in clean if not (r["event"] == "CPI" and r["datetime_et"][5:7] == "02")],
                               _notes()), "a CPI row on a Saturday (G3)", log)
    thu = date(2020, 5, 7)
    assert thu.weekday() == 3
    expect_raise(lambda: gates([row("EMPSIT", thu, 8, 30, "u", thu, False, "fetched", "t")] +
                               [r for r in clean if not (r["event"] == "EMPSIT" and r["datetime_et"][5:7] == "05")],
                               _notes()), "an unflagged non-Friday EMPSIT (G3)", log)
    bad_fomc = [{**r, "release_date_nominal": "2020-01-01"} if r["event"] == "FOMC" else r for r in clean]
    expect_raise(lambda: gates(bad_fomc, _notes()), "an FOMC statement off the meeting's last day (G3)", log)
    broken = [{**r, "datetime_utc": r["datetime_utc"].replace("13:30", "14:30")}
              if r["datetime_et"][5:7] == "01" and r["datetime_et"][11:16] == "08:30" else r for r in clean]
    expect_raise(lambda: gates(broken, _notes()), "a January 08:30 ET row stamped 14:30 UTC (G5)", log)

    log("  parsers:")
    bls = parse_bls_year(
        'MAIN CONTENT BEGIN<table><tr><td class="date-cell"><p>Wednesday, January 20, 2016</p></td>'
        '<td class="time-cell"><p>08:30 AM</p></td>'
        '<td class="desc-cell"><p><strong>Consumer Price Index</strong> for December 2015</p></td></tr>'
        '<tr><td class="date-cell"><p>Tuesday, March 22, 2016</p></td><td class="time-cell"><p>10:00 AM</p></td>'
        '<td class="desc-cell"><p><strong>Employment Situation of Veterans</strong> for Annual 2015</p></td></tr>'
        '</table>', 2016)
    assert len(bls) == 1 and bls[0]["event"] == "CPI" and bls[0]["date"] == date(2016, 1, 20), bls
    log("    parse_bls_year keeps 'Consumer Price Index' and drops 'Employment Situation of Veterans'")
    expect_raise(lambda: parse_bls_year(
        'MAIN CONTENT BEGIN<tr><td class="date-cell"><p>Monday, January 20, 2016</p></td>'
        '<td class="time-cell"><p>08:30 AM</p></td>'
        '<td class="desc-cell"><p><strong>Consumer Price Index</strong> for x</p></td></tr>', 2016),
        "a BLS row whose weekday word contradicts its date", log)

    assert meeting_last_day("April/May", "30-1", 2019) == date(2019, 5, 1)
    assert meeting_last_day("January", "26-27", 2016) == date(2016, 1, 27)
    assert meeting_last_day("October", "4", 2019) == date(2019, 10, 4)
    log("    meeting_last_day: 'April/May 30-1' -> 2019-05-01, 'January 26-27' -> 2016-01-27")

    wd, hh, mm = parse_eia_standard(
        "<p>The standard release time and day of the week will be at 10:30 a.m. eastern time on "
        "Wednesdays with the following exceptions.</p>")
    assert (wd, hh, mm) == (2, 10, 30)
    expect_raise(lambda: parse_eia_standard("<p>no such sentence</p>"),
                 "an EIA page that does not state its standard slot", log)

    # the year-end case the nearest-Thursday rule gets wrong
    got = match_alternates_to_thursdays([date(2025, 12, 29), date(2025, 12, 31)], 3)
    assert got == {date(2025, 12, 25): date(2025, 12, 29), date(2026, 1, 1): date(2025, 12, 31)}, got
    log("    match_alternates_to_thursdays: Mon 2025-12-29 -> Thu 2025-12-25, Wed 2025-12-31 -> Thu 2026-01-01")
    expect_raise(lambda: match_alternates_to_thursdays([date(2025, 12, 1)], 3, window=1),
                 "an alternate with no standard slot in range", log)

    assert et_pair(date(2016, 1, 20), 8, 30)[1] == "2016-01-20T13:30:00Z"
    assert et_pair(date(2016, 7, 15), 8, 30)[1] == "2016-07-15T12:30:00Z"
    log("    et_pair: 08:30 ET is 13:30 UTC in January and 12:30 UTC in July")
    log("selftest: PASS")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.probe:
        return probe()
    if a.fetch:
        return fetch()
    if a.build:
        return build()
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
