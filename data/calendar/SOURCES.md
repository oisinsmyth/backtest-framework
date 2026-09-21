# `data/calendar/events.csv` — where every row came from

*D585. Built by `scripts/fetch_release_calendar.py` (`--probe` / `--fetch` / `--build` /
`--selftest`). Raw responses in `data/raw/calendar/` (gitignored cache, 196 files, kept
byte-for-byte under a `fetched_at` name, indexed by `_manifest.json`). Per-row provenance is in the
CSV itself; per-source provenance, the gates and everything that could not be sourced are in
`events.meta.json`.*

## The rule

**A row exists only where its date AND its clock came off a source.** `method` is `fetched` (the
live official page) or `archived` (a Wayback capture of that same official URL, and that capture's
URL is the `source_url`). The builder **refuses** `method=inferred`, and `--selftest` proves the
refusal raises. Anything that could not be sourced is in the meta's `not_fetched` or in one of the
named lists below — never filled in from a rule.

`release_date_nominal` is the one derived column: the date the release *would* fall on under the
source's own standard rule. It is a **descriptor computed from the sourced date, never a source of
one**, and `holiday_shift` is simply `date != nominal`.

## Per event

| event | rows | span | clock | source |
|---|---:|---|---|---|
| `CPI` | 131 | 2016-01-20 → 2026-12-10 | 08:30 ET, from the page | `bls.gov/schedule/{2016..2026}/home.htm` |
| `EMPSIT` | 131 | 2016-01-08 → 2026-12-04 | 08:30 ET, from the page | same 11 BLS year pages |
| `FOMC` | 85 | 2016-01-27 → 2026-09-16 | **from each statement's own press release** | `fomchistorical{2016..2020}.htm`, `fomccalendars.htm`, then `newsevents/pressreleases/monetaryYYYYMMDDa.htm` |
| `FOMC_UNSCHEDULED` | 7 | 2019-10-11 → 2025-08-22 | same | same |
| `EIA_WPSR` | 573 | 2016-01-06 → 2026-12-30 | 10:30 ET standard, exceptions 11:00/12:00/13:00/17:00 | `eia.gov/petroleum/supply/weekly/schedule.php` + 42 Wayback captures |
| `EIA_NGSR` | 574 | 2016-01-07 → 2026-12-31 | 10:30 ET standard, exceptions 12:00 | `ir.eia.gov/ngs/schedule.html` + 41 Wayback captures |

473 rows are `fetched`, 1,028 `archived`.

## BLS — one page a year, with a free second derivation

`bls.gov/schedule/<year>/home.htm` lists every BLS release of that year as **weekday word, date,
clock time**. The builder parses the date and then asserts the page's own weekday word agrees with
it, so a misparse cannot pass silently. `<strong>Employment Situation</strong>` is matched exactly,
which is what keeps *Employment Situation of Veterans* out.

2027 is a 404; `bls.gov/schedule/news_release/{cpi,empsit}.htm` runs only to the December 2026
release. Both forward pages are fetched anyway and used **only** to cross-check the year pages —
the result is in the meta under `bls_year_page_vs_forward_page` (26 agreements, 0 rows the forward
page has and the year page lacks).

**2025 has 11 CPI and 11 EMPSIT rows, not 12.** BLS's own 2025 schedule carries no October CPI and
no October Employment Situation: the funding lapse of 2025-10-01 to 2025-11-12 cancelled one and
folded the other into 2025-11-20. The year is named in the meta's `partial_or_disrupted_years`, and
G2 refuses to pass a short year that is *not* named there.

## Federal Reserve — the clock is fetched, not assumed

The meeting panels give the meeting days; the statement link gives the statement day; and the
statement's own press release says **"For release at 2:00 p.m. EST"**. So every FOMC row's time is
read from that meeting's own release, and the stated `EST`/`EDT` is asserted against
`America/New_York` for that date. 92 statement press releases were fetched.

* **G3 asserts the scheduled statement day is the meeting's last day.** It holds for all 85.
* `FOMC_UNSCHEDULED` is any panel the Fed labels `(unscheduled)` or `(notation vote)` that has a
  statement: 2019-10-11, 2020-03-03, 2020-03-15 (a **Sunday**, 17:00 ET), 2020-03-23, 2020-03-31,
  2020-08-27, 2025-08-22.
* **2019-10-04 has no row.** The Fed's 2019 page labels it `October 4 (unscheduled)` but attaches a
  statement dated **2019-10-11**; no clock was ever published for the meeting day itself. The
  statement is the row; the meeting is recorded in
  `fomc_unscheduled_meetings_without_a_same_day_statement`.
* **Meetings with no statement yet have no row**: 2026-10-28, 2026-12-09 and all eight 2027
  meetings. Their dates *are* sourced (`fomccalendars.htm`) and are listed in
  `fomc_meetings_with_no_published_release_clock` for a forward recorder — but the release clock is
  not published until the statement is, and the builder will not invent it. 2020-03-17/18 is
  excluded as cancelled; 2020-03-19 (notation vote) issued no statement.

## EIA — a standard sentence plus an exception table, not a list of weeks

Neither EIA report publishes a week-by-week schedule. Each page states

> "The standard release time and day of the week will be at 10:30 a.m. eastern time on
> Wednesdays [Thursdays] with the following exceptions."

and then tables the exceptions. **The standard day and clock are parsed off the page** (never
hard-coded; `parse_eia_standard` raises if the sentence is missing, and the build asserts the day
matches the series). A normal week's row therefore cites the page whose standard sentence and whose
exception table govern that year — the meta's `governing_page_per_year` names it for all 11 years.

The live pages carry roughly two years of exceptions, so earlier years come from Wayback captures
of the same two URLs, unioned: **86 petroleum exceptions (6–10 a year, 2016–2026) and 43 gas
exceptions**. Where two captures disagree, **the later statement wins** and both are recorded in
`conflicts_between_captures` (10 petroleum, 6 gas).

Three things this costs, all written down rather than smoothed over:

1. **A published schedule cannot show an unannounced delay.** These are EIA's scheduled release
   datetimes as EIA published them.
2. **The gas table does not say which Thursday an alternate replaces.** Nearest-Thursday is wrong:
   at the end of 2025 the alternates are Mon 2025-12-29 (Christmas) and Wed 2025-12-31 (New Year),
   and the Thursday nearest 12-29 is 2026-01-01, which belongs to 12-31. The assignment is a
   minimum-cost **order-preserving** match, checked against the explicit holiday date the older
   table prints (the displaced Thursday must be within 2 days of it).
3. **EIA can publish two data weeks at one instant.** After the June 2022 systems outage the
   week-ending 2022-06-17 and 2022-06-24 petroleum reports both came out at 2022-06-29 10:30. That
   is one release *event*, so the rows collapse to one and both nominals go in
   `eia_release_instants_covering_more_than_one_data_week` — G6 ("no duplicate `(event,
   datetime_et)`") stays absolute.

The last exception either page lists is 2026-11-11 (petroleum) and 2026-11-26 (gas). Rows after
those dates are normal weeks under the 2026 table; a Christmas or New-Year exception EIA has not
yet posted would change them.

## Gates

Declared in `events.meta.json → gates`, and `--selftest` proves each one raises on a deliberate
break.

| | rule | result |
|---|---|---|
| G1 | every row has a `source_url` and a `method` in {fetched, archived} | 1,501 / 1,501 |
| G2 | per-year counts in range (CPI 12, EMPSIT 12, FOMC 8, each EIA 50–53); short years must be **named** | 4 named: CPI 2025 = 11, EMPSIT 2025 = 11, FOMC 2020 = 7, FOMC 2026 = 6 |
| G3 | CPI/EMPSIT on weekdays at 08:30; EMPSIT on a Friday unless flagged; FOMC statement on the meeting's last day | 0 violations; 23 EMPSIT rows flagged |
| G4 | 2016–2024 CPI/EMPSIT/FOMC equal `data/macro_release_calendar.json` or every difference is listed | 23 differences, all listed |
| G5 | 08:30 ET → 13:30 UTC in January, 12:30 UTC in July, asserted in code and over the rows | 22 / 22 |
| G6 | no duplicate `(event, datetime_et)` | 0 |

## Not this file

`data/macro_release_calendar.json` is a different, older artifact (recorded 2026-09-12) and is read
by `scripts/run_d494_outside_path.py`. It is **not** edited by D585; the 23 places it differs are
listed in `events.meta.json → disagreements_with_macro_release_calendar_json`.
