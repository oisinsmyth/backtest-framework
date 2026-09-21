# D585 — FIXTURE: the **sourced US economic release calendar, with times** — 1,501 releases 2016-01-06 → 2026-12-31 (CPI, Employment Situation, FOMC, EIA petroleum and gas), every row carrying the official page or Wayback capture its date **and its clock** came off, and a builder that refuses a row it cannot source

*2026-09-21. A data record, not a study. Nothing here reads a market bar or computes a return.
Built for `SHOCK_CLASSIFIER_PREREG.md` §3.4, which asks for `data/calendar/events.csv` and says in
its own §0: "Never fabricate data. This includes economic calendar dates. If a source can't be
found, stop and report." The same file is the flag list for `LETF_CLOSE_FLOW_PREREG` §3.4,
`OPENING_AGENT_STATE_PREREG` §3 and `SETTLEMENT_FLOW_LEDGER_PREREG` §3.5. Fetcher
`scripts/fetch_release_calendar.py` (stdlib only; `--probe`, `--fetch` resumable into
`data/raw/calendar/`, `--build` cache → fixture, `--selftest` proving every gate raises).*

## What is in the file

`data/calendar/events.csv`, tidy, one row a release:
`datetime_et, datetime_utc, event, source_url, release_date_nominal, holiday_shift, method, accessed_utc`.

| event | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | rows |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `CPI` | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | **11** | 12 | 131 |
| `EMPSIT` | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | **11** | 12 | 131 |
| `FOMC` | 8 | 8 | 8 | 8 | **7** | 8 | 8 | 8 | 8 | 8 | **6** | 85 |
| `FOMC_UNSCHEDULED` | · | · | · | 1 | 5 | · | · | · | · | 1 | · | 7 |
| `EIA_WPSR` | 52 | 52 | 52 | 52 | 53 | 52 | **51** | 52 | 52 | 53 | 52 | 573 |
| `EIA_NGSR` | 52 | 52 | 52 | 52 | 53 | 52 | 52 | 52 | 52 | 53 | 52 | 574 |

**473 rows `fetched`, 1,028 `archived`** (the EIA years before the live pages' two-year exception
window). 262 KB tracked, plus a 80 KB meta and 196 raw responses in the gitignored cache.

**The four bold cells are not gaps in the fetch; they are what the sources say.** G2 refuses to
pass a year outside its declared range unless the meta *names* the year with a reason:

* **CPI and EMPSIT 2025 = 11.** BLS's own 2025 page carries no October CPI and no October
  Employment Situation — the funding lapse of 2025-10-01 to 2025-11-12 cancelled the one and folded
  the other into a Thursday 2025-11-20 release. This contradicts the brief's verification fact
  "CPI count 12 in each of 2016-2025"; the page is the authority and 2025 is 11.
* **FOMC 2020 = 7.** The Fed's own page marks March 17-18 cancelled.
* **FOMC 2026 = 6.** October and December 2026 have not met, so no statement and no published
  clock exists — see below.
* **EIA_WPSR 2022 = 51.** Two data weeks were published at one instant — see below.

## The rule the whole thing is built around

A row exists only where **both** its date and its clock came off a source. `method` is `fetched`
(the live official page) or `archived` (a Wayback capture of that same official URL, recorded as
the `source_url`). **The builder refuses `method=inferred` and `--selftest` proves the refusal
raises.** `release_date_nominal` is the single derived column — the date the release *would* fall
on under the source's own standard rule — and it is a descriptor computed *from* the sourced date,
never a source of one.

The clock is where this bit hardest. It would have been easy to stamp FOMC at 14:00 and EIA at
10:30 and call the dates sourced. Instead:

* **Every FOMC row's time is read from that meeting's own press release** ("For release at 2:00
  p.m. EST"), 92 of them fetched, and the page's stated `EST`/`EDT` is asserted against
  `America/New_York` for that date. That is what puts **2020-03-15 at 17:00 ET on a Sunday** and
  **2020-03-23 at 08:00** in the file as measured facts rather than assumptions.
* **EIA's standard day and clock are parsed off the page's own sentence**, not hard-coded, and the
  build asserts the parsed day matches the series. `parse_eia_standard` raises if the sentence is
  absent.

## Five things found on the way

1. **`data/macro_release_calendar.json` is wrong on nine dates.** G4 compares the 2016-2024 sets
   and lists every difference. Eighteen of the 23 difference rows are eight CPI dates and one EMPSIT
   date (each counted twice, once from each side) where the older hand-recorded file is off by a day or three weeks — including
   **`2016-01-18` for CPI, which is Martin Luther King Jr. Day**, against BLS's `2016-01-20`; and
   **`2023-01-27` for EMPSIT** against BLS's `2023-01-06`. Every one of my dates carries the BLS
   page's own weekday word, checked against the parsed date. The remaining five are the
   unscheduled-FOMC convention (below). **`data/macro_release_calendar.json` is not edited here** —
   it is read by `scripts/run_d494_outside_path.py` and the differences are recorded, not applied.
2. **The brief's EIA verification fact is two things at once, and the schedule was revised.** The
   petroleum report has **no** Independence Day exception in 2019 — 2019-07-04 was a Thursday, so
   the Wednesday 2019-07-03 10:30 release was untouched, and the file says so with
   `holiday_shift=False`. The **gas** report did shift that week, and EIA changed its mind: every
   capture up to 2019-01-11 says **Friday 2019-07-05 10:30**; every capture from 2019-06-13 on,
   including three taken *after* the event, says **Wednesday 2019-07-03 12:00**. The later
   statement wins, the conflict is in `conflicts_between_captures`, and the row is 2019-07-03 12:00.
3. **EIA can publish two data weeks at one instant.** After the June 2022 systems outage the
   week-ending 2022-06-17 and 2022-06-24 petroleum reports both came out at **2022-06-29 10:30**
   (EIA's own later page moved the 06-17 row from "June 23, Thursday, 11:00" to "June 29,
   Wednesday, 10:30"). That is one release *event*, so the rows collapse to one and both nominals
   go in `eia_release_instants_covering_more_than_one_data_week`. G6 stays absolute rather than
   growing an exception — which is why WPSR 2022 is 51.
4. **"Nearest Thursday" is the wrong rule for the gas exception table**, and it fails exactly where
   it matters. That table gives only the alternate date. At the end of 2025 the alternates are
   **Mon 2025-12-29 (Christmas)** and **Wed 2025-12-31 (New Year)**, and the Thursday nearest
   12-29 is 2026-01-01 — which belongs to 12-31. The assignment is a minimum-cost
   **order-preserving** match, and where the older table prints the holiday's own date the match is
   asserted against it (displaced Thursday within 2 days). Both the right answer and the wrong rule
   it avoids are pinned in `tests/unit/test_release_calendar.py`.
5. **Seventeen Wayback captures parsed as garbage and it was not the parser.** A Wayback `id_`
   replay hands back the original response *including* its `Content-Encoding: gzip`, so 17 of the
   cached files are gzip members. They are decompressed on read; the cache stays byte-for-byte, as
   a raw cache must. Before the fix those 17 sat in `schedule_pages_unparsed` looking like EIA page
   redesigns — a silent 17-page hole in the exception union that the meta's own count made visible.

## What could not be sourced, and is recorded rather than filled in

`not_fetched` is empty — nothing in scope failed to fetch. What does not exist yet is listed
instead:

* **10 FOMC meetings whose release clock has not been published**: 2026-10-28, 2026-12-09 and all
  eight 2027 meetings. Their **dates are sourced** (`fomccalendars.htm`) and sit in
  `fomc_meetings_with_no_published_release_clock` for the forward recorder, but a meeting that has
  not happened has no press release and therefore no clock, and the builder will not invent one.
  Also there: 2020-03-19, a notation vote that issued no statement.
* **2019-10-04.** The Fed labels the panel `October 4 (unscheduled)` and attaches a statement dated
  **2019-10-11**. The statement is the row; the meeting is in
  `fomc_unscheduled_meetings_without_a_same_day_statement`. This is why the file has
  `FOMC_UNSCHEDULED 2019-10-11` where `macro_release_calendar.json` has `2019-10-04`.
* **BLS 2027**: `bls.gov/schedule/2027/home.htm` is a 404 and the forward per-release pages stop at
  the December 2026 release. The BLS span ends 2026-12-10.
* **A published schedule cannot show an unannounced delay.** The EIA rows are EIA's scheduled
  release datetimes as EIA published them, and the meta says so in `conventions`.

## Gates (in the meta, each proven to raise by `--selftest`)

| | rule | result |
|---|---|---|
| G1 | every row has a `source_url` and a `method` in {fetched, archived} | 1,501 / 1,501 |
| G2 | per-year counts in range (CPI 12, EMPSIT 12, FOMC 8, each EIA 50–53); a short year must be **named with a reason** | 4 named, listed above |
| G3 | CPI/EMPSIT on weekdays at 08:30; EMPSIT on a Friday unless `holiday_shift`; FOMC statement on the meeting's last day | 0 violations; 23 EMPSIT rows flagged (incl. the 2019 shutdown's 2019-03-08 and 2025's 11-20 and 12-16) |
| G4 | 2016-2024 CPI/EMPSIT/FOMC equal `macro_release_calendar.json` **or every difference is listed** | 23 differences, all listed |
| G5 | 08:30 ET → 13:30 UTC in January, 12:30 UTC in July — asserted in code *and* over all 44 such rows | pass |
| G6 | no duplicate `(event, datetime_et)` | 0 |

Two more checks that are not gates but are in the meta: the BLS year pages against the BLS forward
per-release pages (**26 agreements, 0 disagreements, 0 rows only the forward page has**), and the
weekday word BLS prints beside every date against the parsed date (**262 rows, all agree** — the
parser raises if one does not).

## Files

`data/calendar/events.csv` (1,501 rows, 262 KB, tracked — plain csv stays tracked under the
manifest's own rule), `data/calendar/events.meta.json` (80 KB: per-source url/method/accessed/sha256
for all 196 raw responses, the gates, the EIA governing page per year, every capture conflict, every
disagreement), `data/calendar/SOURCES.md`, `scripts/fetch_release_calendar.py`,
`tests/unit/test_release_calendar.py` (25 offline tests, 1 `live_fetch`). Raw in
`data/raw/calendar/` (gitignored, 196 files + `_manifest.json`). Licence: US federal government
public domain (BLS, Federal Reserve, EIA); Wayback captures of those same pages.

Wall time: probe ~1 min, fetch **11 min** (196 responses, 1 s between government requests and 2.5 s
between Wayback requests, one pass, resumable), build **under 1 s**.

---

## Proposed paragraph for `docs/data-available.md` (not applied here)

> `data/calendar/events.csv`: **the sourced US economic release calendar with times — 1,501
> releases, 2016-01-06 → 2026-12-31**, one row per release: CPI (131) and the Employment Situation
> (131) at 08:30 ET from the BLS year schedules; the FOMC statement (85 scheduled, 7 unscheduled)
> at the clock printed on that meeting's own press release; and the EIA weekly petroleum (573) and
> natural-gas storage (574) reports at 10:30 ET with every published holiday shift. US government
> public domain. Built by `scripts/fetch_release_calendar.py` from `data/raw/calendar/` (196 raw
> pages, gitignored); provenance per row (`source_url`, `method` ∈ {fetched, archived},
> `accessed_utc`) and six gates in `events.meta.json`; `SOURCES.md` beside it. See D585. **What
> bites:** (i) **the file is a schedule, not a log** — EIA's rows are what EIA published, so an
> unannounced delay is invisible, and the last exception either EIA page lists is 2026-11-11
> (petroleum) / 2026-11-26 (gas); (ii) **2025 has 11 CPI and 11 EMPSIT rows**, not 12 — the
> 2025-10-01 funding lapse — and **2026 has 6 FOMC rows**, because the October and December 2026
> meetings have no published release clock yet (their dates are in the meta, not the CSV, and all
> eight 2027 meetings likewise); (iii) it **disagrees with `data/macro_release_calendar.json` on
> nine 2016-2023 CPI/EMPSIT dates**, which that older file gets wrong (it puts the January 2016 CPI
> on MLK Day) — the differences are enumerated in the meta and neither file is derived from the
> other.
