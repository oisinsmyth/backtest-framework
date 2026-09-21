# D589 — FIXTURE: the **CME session calendar and event flags** for the 36 breadth roots — 205,428 (root, ET calendar day) rows 2010-06-07 → 2026-09-09, of which 135,179 are trading sessions, with each root's own session band measured from its settlement volume cliff, 142 market-wide early closes derived rather than hardcoded, and 34 short days rejected as feed dropouts and named

> **Amendment, 2026-09-21 (same day, before commit): the committed fixture was rebuilt with
> `--events data/calendar/events.csv`**, the D585 sourced release calendar, in place of
> `data/macro_release_calendar.json`. The `fomc`, `cpi` and `empsit` flags now span 2016-01 →
> 2026-09-09 (ES: 91 FOMC, 127 CPI, 128 EMPSIT trading days flagged) and are null only before
> 2016, where D585 has no rows; the "90,516 rows carry a null FOMC" figure below describes the
> first build and is superseded. Rows, gates and every other column are unchanged (all five
> runnable gates pass; G6 still `not_fetched`). Fixture sha256 now begins `1164a241`.

*2026-09-21. A data record, not a study. **This record was written as D584; by the time it was
filed D584, D587 and D588 had been taken by work running in parallel, so it is D589 and D585/D586
are free.** Built for the four deposit pre-registrations that all ask the same thing of a calendar
and none of which can source it — `SHOCK_CLASSIFIER_PREREG.md` §3.2–3.4 (roll days excluded from
shock detection, an event flag, DST-aware ET), `LETF_CLOSE_FLOW_PREREG.md` §3.4 (exclude early
closes; flag FOMC, CPI, quad witching, quarter-ends), `OPENING_AGENT_STATE_PREREG.md` §3 (exclude
early closes and missing opens; flag month-end), `SETTLEMENT_FLOW_LEDGER_PREREG.md` §3.5 (flag
expiries and index rolls). Builder `scripts/build_cme_session_calendar.py` (system python for
pyarrow; `--selftest`, `--build`, `--events PATH`, `--holidays PATH`), 0.5 min. **Nothing here
computes a return, and no column is windowed to anyone's in-sample slice** — a calendar is a fact,
so it spans the full held range to the latest bar.*

## What the sources give

| joined, never re-derived | from | what it settles |
|---|---|---|
| `front_contract`, `roll_day` | `fut_breadth_hourly.csv.gz` (`contract`, `same_front`) | 4,408 roll sessions — **the same 4,408 `fut_day1m.meta.json` records**, and `~same_front` reproduces `fut_sessions_rolls.csv.gz` **exactly, both directions, on all nine roots it covers** |
| `rth_bars` for ES NQ YM RTY | `fut_index_sessions.csv.gz` (`bars`) | 390 on a full 09:30–15:59 session |
| `expiry_day`, `days_to_expiry` | `data/fut_expiries_from_definition.json` | nearest expiry at or after the session date (single-digit year codes are recycled — D581) |
| `fomc`, `cpi`, `empsit` | `data/macro_release_calendar.json`, or `--events PATH` | FOMC 2016-01-27 → 2024-12-18; CPI and employment 2016 → 2023-12 |

Everything else is derived from each root's own minute bars in `fut_day1m.parquet`.

**The session band is measured, not templated.** `fut_day1m` is cut to a 09:00–15:59 ET template,
so a 23-hour root keeps printing bars for hours after its market has settled — the trap that gave
D530 a spurious z = −12.6 "closing reversion" off the bid-ask bounce. The close is taken from the
**settlement volume cliff**: the minute whose mean volume is ≥ 4× the mean of the next 30, and ≥ 10 %
of the root's busiest minute. It recovers nine distinct bands with no calendar hardcoded anywhere:

| band (ET) | roots | cliff ratio |
|---|---|---|
| 09:00–12:59 | HG PA | 18.5, 11.8 |
| 09:00–13:04 | PL | 12.7 |
| 09:00–13:24 | SI | 11.4 |
| 09:00–13:29 | GC | 8.1 |
| 09:00–14:29 | BZ CL HO NG RB | 8.6–26.4 |
| 09:00–14:59 | 6A 6B 6C 6E 6J 6S · TN UB ZB ZF ZN ZT | 5.6–19.0 |
| 09:00–15:59 | BTC ES NKD NQ RTY SR3 YM | **no cliff** — the session runs to or past the window edge |
| 09:30–13:59 | HE LE | 12.8, 9.6 |
| 09:30–14:19 | ZC ZL ZM ZS ZW | 608–1,056 (nothing at all trades after) |

**The early close is a market-wide fact, not a short root** (the `_half_days` pattern of
`fetch_etf_intraday.py`). A root is `is_early_close` only when it stops ≥ 30 min before its own band
close **on a day when ≥ 4 of ≥ 10 trading roots stopped together**, their stop minutes agreeing
within 5 minutes of their mode, and **that mode is the minute before a five-minute boundary**. 142
such days: 97 at 13:00 (the seven federal holidays that trade an abbreviated session — MLK,
Presidents, Memorial, Juneteenth, Independence, Labor, and Thanksgiving Day itself), 33 at 13:15
(the day after Thanksgiving and Christmas Eve), 5 at 11:15 (the Good Fridays that carry a payroll
release), 3 at 13:05 (the CBOT agricultural complex alone), one at 12:00 (2012-10-29, Sandy), one
at 09:30 (2018-12-05, the Bush day of mourning — **four roots short out of 29, which no market-wide
*fraction* test would have caught**; the equity complex closed and nothing else did), and two at
13:30 which are **almost certainly wrong**: 2010-07-26 and 2010-08-23 carry CL HO NG RB alone and
belong to the early-archive pattern in point 1 below, passing only because their modal stop landed
one minute earlier than the 31 days the same rule rejects. The rule is **not** tuned to exclude
them — a threshold chosen after seeing the answer is selection — so they are named in the meta.

## Things that bite

1. **A feed dropout is shaped exactly like an early close, and counts cannot tell them apart.**
   2020-06-30 truncates 22 of 36 roots at 10:10 with concentration 1.00; 2020-02-27 truncates 17 at
   ~13:20. Both out-score most genuine holidays on every count statistic. They are separated by a
   property of the object rather than a threshold — **an exchange session ends on a five-minute
   boundary and a dropout does not** — and all 34 rejected days are listed in the meta with their
   modal stop. **2020-02-27 is a second archive dropout of the 2020-06-30 family and
   `data/data-available.md` does not carry it**: 17 roots stop between 13:14 and 13:20 with a final
   minute carrying 0.03–0.11 of that day's median minute volume, on one of the largest volume days
   of the Covid selloff. A third family: **CL HO NG RB (and once BZ) stop at 13:30 on 31 Mondays
   from 2010-06-07 to 2011-01-18**, inside the known early-archive gap.
2. **"COMEX metals close 13:30" is true of gold only.** Measured from the settlement cliff: GC
   13:30, **SI 13:25, PL 13:05, HG 13:00, PA 13:00**. A study applying one COMEX close to five
   metals reads 5 to 30 minutes of post-settlement tape as session. Livestock is the mirror case:
   the cliff is at **14:00** (the settlement) and the last traded minute is 14:04, so
   `data-available.md`'s 14:05 is the last trade and 14:00 is the close.
3. **`session_close_et` is the settlement minute, and for FX and Treasuries that is not the end of
   trading.** The twelve FX and rate roots read 14:59 — the 15:00 ET settlement — after which Globex
   runs to 17:00 and this fixture still carries bars to 15:59; D530 measured 11.0 % of ZN's session
   volume and 11.6 % of ZB's in that hour. For the index roots the value is the 15:59 **window
   edge**, not a close at all. The meta says so per flag.
4. **`is_trading=False` does not mean the exchange was shut** before a root's clean year. It means
   the archive holds no day-session bar, and the archive is the binding constraint until 2016 for
   ES/NQ/YM (D462 G5), 2022 for SR3 and never for PA. **Eleven of the 65 in-span quad-witching days
   have no ES day session and all eleven are 2010–2014**, which is the gap, not a closure.
5. **There is a FOURTH incomplete March-2020 ES session and `data-available.md` names three.** G3
   finds exactly four ordinary ES sessions below 390 bars in the whole 2016+ span, and they are
   2020-03-09 (377), 2020-03-12 (377), 2020-03-16 (376) **and 2020-03-18 (377)**. All four carry a
   full 09:00–15:59 band with an interior hole, which is why none is an early close; the documented
   warning about no continuous open should cover the 18th as well. They are the only four: the share
   of ordinary ES sessions at exactly 390 bars is **0.9985 of 2,665**.
6. **Thanksgiving Day is a trading day.** ES trades 09:00–13:00 ET on it in every year; marking it a
   holiday because the cash market is shut would delete a real session. The full closures are three
   a year and the observance rule is **asymmetric**: Christmas on a Saturday moves back to the Friday
   (2021-12-24 is closed) and New Year's Day on a Saturday does not (2021-12-31 trades a full
   session). A symmetric rule gets one of the two wrong whichever way it is written.
7. **`quad_witching` comes from the expiry file, not from the third-Friday rule, and they differ.**
   **2026-06-18 is a Thursday quad witching**, because the third Friday of June 2026 is Juneteenth.
   One of the 65 in-span ES expiries disagrees with the third-Friday rule, and it is that one; the
   rule in turn names 2026-06-19, on which nothing expires.
8. **`expiry_day` is not `days_to_expiry == 0`.** They are different objects on purpose: `expiry_day`
   is the root's expiry calendar, `days_to_expiry` is the *front* contract's, and the front is
   elected by volume and rolls one to two weeks early, so it never reaches zero (the per-root minimum
   runs 1 to 29 days and is in the meta).
9. **`fomc`, `cpi` and `empsit` are EMPTY, not False, outside the sourced span.** 90,516 rows carry a
   null FOMC and 103,611 a null CPI. A `False` in 2012 would assert there was no release; there is no
   source. `fomc` is the scheduled statement day only — the three unscheduled meetings are not folded
   in.
10. **`2021-05-31` is a real 09:00–13:00 ET session**, 210 bars on the 09:30–15:59 count.
   `data-available.md`'s "present on a Globex evening bar with no closes and no settlements" is true
   of the **hourly** fixture, which cannot form a row without an h15 close; it is not an empty day.
   `2020-06-30` by contrast is a *full* 390-bar ES session whose truncation hits 22 other roots.

## Gates (in the meta, proven to raise by `--selftest`)

| | rule | measured |
|---|---|---|
| **G1** | the holiday rule **equals** the observed non-trading weekdays from 2016-01-04, on ES NQ YM RTY — set equality, not containment, so a rule that closed every Tuesday would fail | 30 holiday weekdays, 27 non-trading, the 3 Good Fridays that traded named as partial sessions; 0 holidays that traded, 0 closures outside the rule, on all four roots |
| **G2** | ES `is_early_close` on the day after Thanksgiving and on Christmas Eve, every year 2016+ in which that date is a weekday ES traded | 20 dates checked, **15 required, all 15 true**; the five excused are named with their weekday and traded flags — 2016/2022 Christmas Eve on a Saturday, 2017/2023 on a Sunday, and **2021-12-24 a weekday ES did not trade** because Christmas was observed on it |
| **G3** | ES `rth_bars == 390` on an ordinary session | modal 390, **share 0.9985 of 2,665** sessions; the **four** below are named, and they are the whole of March 2020's incomplete set |
| **G4** | `roll_day` equals `fut_sessions_rolls.csv.gz`, per root | set equality on all 9 roots, both directions, 0 disagreements |
| **G5** | the documented special cases are classified as described and counted | the four March-2020 sessions trade, are not early closes, carry < 390 bars ✓ · 2021-05-31 trades and is an early close ✓ · both archive truncations rejected ✓ · 30 BTC weekend sessions from 2026-05-30, none an early close, **0 for any other root** ✓ |
| **G6** | every derived early close from 2016 appears on the CME holiday calendar and vice versa, disagreements listed never resolved | **`not_fetched`** — see below |

`--selftest` proves each of these raises on a break that hits the scalar compared: G4 with the roll
flag cleared, G3 on a 387-bar session, G2 with the Thanksgiving-Friday flag cleared, G1 with an
ordinary Friday marked non-trading, G6 with one day the page does not carry; and, below the gates,
the cliff on a flat profile, the early-close rule on a 10:10 dropout and on a two-root short day, the
asymmetric observance rule, the DST week off by one, the clock left in UTC, a fixed −5 offset through
the summer, and `REQUIRED_OUTPUTS` short of its `gates` block.

**G6 could not be sourced.** `cmegroup.com` is unreachable from this machine: eight attempts over
five URLs, each recorded in the meta with its URL, access time and failure — WebFetch timed out at
60 s on the holiday calendar, the trading-hours page, the 2025 New Year advisory and the investor
static-file calendar, returned ECONNRESET on `files/good-friday.pdf` and the 2025 Christmas
advisory, and curl got HTTP 403 (a 602-byte WAF page) on both the PDF and the calendar. **No
third-party calendar was substituted**; the gate does not run, does not pass, and does not fail
silently: `gates.G6.passes` is `null`, `status` is `not_fetched`, `gates_not_run` is `["G6"]`, and
`holiday_disagreements` reads `"not_fetched -- G6 did not run"`. `all_gates_pass` is `true` over the
five that ran. `--holidays PATH` takes a `{day: label}` JSON whenever the page can be reached, and
the disagreement logic is tested both ways.

## Files

`data/fixtures/cme_session_calendar.csv.gz` (**205,428 rows**, 1.35 MB, 18 columns,
2010-06-07 → 2026-09-09; 135,179 trading rows, 70,249 non-trading; `is_early_close` 2,699,
`roll_day` 4,408, `expiry_day` 3,430, `quad_witching` 2,088, `month_end` 6,737, `quarter_end` 2,269,
`dst_transition_week` 5,091, all counted on trading rows; sha256
`1354252359082d9c225ec9a0818f0798b486c734ca9f72e3de9a87f47419b5c9`, newline pinned to `\n` before
compression and `mtime=0` in the gzip header so the bytes reproduce off this machine — D550) and
`data/fixtures/cme_session_calendar.meta.json` (63 kB: the per-root bands with their cliff ratios,
the 142 early-close days, the 34 rejected short days with their modal stops and short roots, the
special sessions, a paragraph per flag saying what it does **not** mean, the six gates and the eight
G6 fetch attempts). Builder `scripts/build_cme_session_calendar.py`; tests
`tests/unit/test_cme_session_calendar.py` (24, offline, 1.6 s). `docs/data-available.md`, the
CHANGELOG, `docs/decisions/README.md` and `data/data_manifest.json` are **not** touched by this
record — the proposed paragraph is below. **Three things are owed by whoever commits this:** the
fixture is gitignored by suffix (`.gitignore:106`, `/data/**/*.csv.gz`) so like
`fut_settle_strip.csv.gz` it needs a `data/data_manifest.json` entry with its sha256 while the
sidecar stays tracked; `docs/decisions/README.md` needs its index line, or
`tests/unit/test_decision_index_is_complete.py` reddens the moment the record is staged; and the
data-available paragraph below needs applying.

---

## Proposed `docs/data-available.md` paragraph (not applied)

> **The session calendar (D589, 2026-09-21).** **`cme_session_calendar.csv.gz`**: one row per (root,
> ET calendar day) for the 36 breadth roots, 2010-06-07 → 2026-09-09, **205,428 rows** of which
> 135,179 are trading sessions; `is_trading`, `session_open_et`, `session_close_et`, `rth_bars`,
> `is_early_close`, `front_contract`, `roll_day`, `expiry_day`, `days_to_expiry`, `quad_witching`,
> `month_end`, `quarter_end`, `fomc`, `cpi`, `empsit`, `dst_transition_week`. Builder
> `scripts/build_cme_session_calendar.py` (system python, 0.5 min). The front month, the roll days
> and the index `rth_bars` are **joined from `fut_breadth_hourly` and `fut_index_sessions`, never
> re-elected**, so the calendar cannot disagree with them: `roll_day` reproduces
> `fut_sessions_rolls.csv.gz` exactly on all nine roots it covers and totals the same 4,408 roll
> sessions `fut_day1m.meta.json` records. **What bites:** *(i)* **`session_close_et` is each root's
> own settlement minute, measured from its volume cliff, and the nine bands are not the four
> `day5m` reports** — **SI closes 13:25, PL 13:05, HG and PA 13:00**, only GC 13:30, and the
> livestock cliff is 14:00 with the last trade at 14:04; for the twelve FX and rate roots the value
> is the 15:00 ET *settlement*, after which Globex runs to 17:00 (ZN keeps 11.0 % of its session
> volume in that hour), and for the seven index-and-crypto roots it is the 15:59 *window edge*, not
> a close. *(ii)* **`is_trading=False` is the archive, not the exchange**, before a root's clean
> year: eleven of the 65 quad-witching days have no ES day session and all eleven are 2010–2014.
> *(iii)* **Two archive dropouts are shaped exactly like market-wide early closes and are rejected
> by name** — 2020-06-30 (22 roots stop at 10:10) and, **newly found here and not previously
> recorded, 2020-02-27** (17 roots stop at ~13:20 on a Covid-selloff session) — together with 31
> Mondays in 2010-06 → 2011-01 on which CL HO NG RB stop at 13:30. What separates them from a
> holiday is not a count: an exchange session ends on a five-minute boundary and a feed dropout does
> not. All 34 rejected days are listed in the meta, as are the two the rule accepts and probably
> should not. *(iii-b)* **There is a fourth incomplete March-2020 ES session: 2020-03-18** (377 of
> 390 bars), alongside the documented 09, 12 and 16; those four are the only ordinary ES sessions
> below 390 bars in the whole 2016+ span. *(iv)* **`fomc`, `cpi` and `empsit` are empty,
> not False, outside `macro_release_calendar.json`'s span** (FOMC to 2024-12, CPI and payrolls to
> 2023-12): 90,516 rows carry a null FOMC. *(v)* **`expiry_day` is the root's expiry calendar and
> `days_to_expiry` is the front contract's**, so `expiry_day` is *not* `days_to_expiry == 0` — the
> volume-elected front rolls one to two weeks early and never reaches expiry. *(vi)* **`quad_witching`
> comes from the ES expiry file, not the third-Friday rule: 2026-06-18 is a Thursday** because the
> third Friday of June 2026 is Juneteenth. *(vii)* **Thanksgiving Day is a trading day** (ES
> 09:00–13:00 ET); the full closures are Good Friday, Christmas and New Year's, and the observance
> rule is asymmetric — Christmas on a Saturday moves to the Friday, New Year's Day does not.
> *(viii)* **G6, the cross-check against cmegroup.com's own holiday calendar, is `not_fetched`**:
> eight attempts over six URLs, all timeouts, resets or HTTP 403, each with its URL and access time
> in the meta; no third-party calendar was substituted and the gate reports `null`, not a pass.
