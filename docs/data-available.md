# Data available

**Inventory taken 2026-09-12, measured from disk rather than recalled.** What exists, what
it covers, where it lives, and — for each — the thing that will bite a study that reads it
without checking.

**This is an inventory of THIS MACHINE, not of the repository.** The largest entry below is
111.0 GB under `data/raw/`, which is gitignored: **a clone receives none of it.** What a clone
does receive is [`data/data_manifest.json`](../data/data_manifest.json), which carries the sha256
of every bulk panel, and the git blob id each one carried *before publication*. Those objects
were purged with the vendor data (D549), so 113 of the 115 do not resolve in a clone — **the
sha256 is the usable field** (D552).

> **This is an index, not a licence.** Several fixtures carry holdout status, adjustment
> quirks or licence restrictions that decide whether a given study may read them at all.
> Those constraints live in [`RULES.md`](RULES.md), [`FINDINGS.md`](FINDINGS.md) and each
> fixture's own `.meta.json`, and this page defers to them.

---

## 1. CME futures — NEW, acquired 2026-09-11/12

**111.0 GB, 129 files, `data/raw/databento/<job-id>/*.dbn.zst`.** Databento `GLBX.MDP3` under a
one-month CME Standard subscription. Every job quoted **$0.00** against **$7,719** at
published per-schema rates; the only cost was the $199 subscription.

| schema | scope | window | on disk | files |
|---|---|---|---:|---:|
| `ohlcv-1m` | **every instrument** | 2010-06-06 → 2026-09-10 | 12.22 GB | 26 |
| `mbo` full order book | ES NQ RTY YM CL GC ZN ZB | 2026-08-11 → 2026-09-10 | 39.39 GB | 26 |
| `tbbo` trade + quote before it | **every instrument** | 2025-09-11 → 2026-09-11 | 37.30 GB | 13 |
| `statistics` OI, settlements | 41 roots | 2010-06-06 → 2026-09-11 | 10.87 GB | 17 |
| `bbo-1m` quoted spread | 41 roots | 2025-09-11 → 2026-09-11 | 8.00 GB | 13 |
| `definition` roll calendar | 41 roots | 2010-06-06 → 2026-09-11 | 2.67 GB | 17 |
| `status` halts, auctions | 41 roots | 2010-06-06 → 2026-09-11 | 0.56 GB | 17 |

**"Every instrument" means every instrument** — each contract month, each calendar spread
and each option on a future, not one stitched continuous series. That is where term
structure and carry would come from, and it is also why a naive load is not a panel.

**Verified, not assumed** ([`futures_acquisition_verification.json`](../data/futures_acquisition_verification.json)):
129/129 byte counts match Databento's manifest, 129/129 sha256 hashes match, 16/16 DBN
headers state the requested dataset and schema, and the ten `ohlcv-1m` slices **tile
2010-06-06 → 2026-09-10 with zero interior gaps and zero overlaps.**

**Committed fixtures built over it:** `fut_sessions_hourly.csv.gz` (D467, hourly session tables,
nine roots, 2016 →); **`fut_open_interest_daily.csv.gz` (D497: daily root-total open interest and
cleared volume for ES, NQ, CL, GC from the `statistics` schema, keyed on the session each figure
is first USABLE — published strictly before a 10:00 ET entry; 100% coverage, staleness one session,
builder `scripts/build_fut_open_interest.py`, 3.3 min). **CORRECTED 2026-09-13 by [D521](decisions/D521-the-three-remaining-flat-id-builders-are-ported-and-the-open.md) — re-pull any CL total you cached before that commit.** The builder used a **FLAT `{instrument_id: symbol}` lookup** (the D520 defect) and it did bite here: instrument 42007396 was `6AF4` until 2024-01-21 and was reissued as `CLG36` in November, so the flat dict counted **an Australian-dollar contract as a 61st crude contract on 2024-01-03 … 2024-01-19**, overstating `oi_total` by 235–401 contracts (0.014–0.026%). `oi_front` was never touched — the volume rule protects it — which is exactly why the CURVE, read from `oi_total` and `oi_n_contracts`, was the exposed part. Now windowed; the other three roots and every other session are unchanged and all 63 gate scalars are identical. And **2025-07-28 is a bad session**: ES, GC and NQ simultaneously report 326, 9,158 and 82 contracts of total open interest with truncated strip counts — a one-day source dropout, unrelated to the mapping; drop it or treat it as missing. What bites: `ts_ref` is the session START,
**AND THE `statistics` SCHEMA CARRIES A SECOND MISSING-VALUE SENTINEL THAT NOTHING FILTERS — [D526](decisions/D526-the-curve-story-fails-stage-0-the-level-is-a-regime-and-the.md).** `UNDEF` is `INT64_MAX` and every builder here filters it. **Zero is a second marker**: a settlement price of exactly `0.0` appears on **646 occasions** across CL and GC in 2016-2023 alone (CL 344, GC 302, every year, concentrated in deferred months like `CLF30`…`CLF35`). It is positive-adjacent, so no existing guard catches it — and **the fix cannot be "drop non-positive", because CL legitimately settled −37.63 on 2020-04-20.** Drop exact zeros, keep genuine negatives. The same caution applies to any `stat_type` read from this schema, not just settlements. What bites: `ts_ref` is the session START,
the evening BEFORE the trade date it describes, so a naive read is off by a day; open interest for
trade date T is first published ≈ 21:00 ET on T itself; and a per-contract series must drop expired
months or the root total carries dead open interest forever;** and **`fut_micro_flow_5m.csv.gz` (D485: signed 5-minute order flow of ES/MES
and NQ/MNQ from `tbbo`, exchange aggressor side, front month per session, 259 sessions
2025-09-11 → 2026-09-10; gates T1–T5 in its meta; builder `scripts/build_fut_micro_flow.py`,
3.3 min on 8 processes).** What bites: the ohlcv-1m span ends one session before the tbbo span,
so session 2026-09-10 cannot be cross-checked; nine holiday sessions are absent by the presence
rule and listed. And **`fut_{ES,NQ,YM,RTY}_rth_1m.csv.gz` + `fut_index_sessions.csv.gz` +
`fut_index_rolls.csv.gz` (D462: the index day session at ONE MINUTE, 09:30–15:59 ET, front month by
full-day volume, no stitching and no adjustment; ES/NQ/YM 2010-06-07 →, RTY 2017-07-10 →; builder
`scripts/build_fut_index_1m.py`, 6.2 min on 6 workers). **ALL GATES PASS as of D522** — RTY joined
the committed set there, having failed G4 on a single session until the gate was amended.** What
bites: **usable from 2016-01-04 for ES/NQ/YM** (G5 — the archive carries the evening bars but not
the day session on most earlier days: 21% coverage in 2010, 89% in 2015), and the **three
circuit-breaker sessions of March 2020 (09, 12, 16) have no continuous open** — one print at 09:30
and nothing until 09:45 — so an open-to-close study must drop them or read the open at 09:45.

**The settlement strip and the curve table (D556, 2026-09-19).** **`fut_settle_strip.csv.gz`**: every
settlement of every listed month for the 36 breadth roots, 2010-06-07 → 2026-09-10, **3,319,301 rows**
from the `statistics` schema (`stat_type` 3) on the windowed ids; builder
`scripts/build_fut_settle_strip.py --extract` (system python, 0.7 min on 8 processes); gitignored by
suffix and in the data manifest, sidecar tracked. **`fut_curve_front_next.csv.gz`** (`--derive`,
143,113 root-sessions): the breadth fixture's own front, its settlement, the nearest later delivery
month with a settlement that session, `months_between` and the annualised carry
`(F_front − F_next)/F_next × 12/months`. **Gates in both metas:** the CL and GC rows reproduce
`data/d526_curve_strip_CL_GC.csv.gz` **exactly** (263,983 rows, settlements identical); coverage among
settling sessions ≥ 99.97% front / 98.7% next; the front settlement sits within a median 0.31% (BTC,
the worst) of the breadth session close. **What bites:** *(i)* **a session on which a root publishes
no settlement is that root's exchange holiday** — the breadth fixture carries the holiday's
abbreviated Globex session, CME books it into the next trade date, and the calendar differs by
exchange group (5–6 a year on CME/NYMEX/COMEX roots, ~0.2 on the CBOT grains and livestock); the
column `root_settles` marks it, and a carry read on such a session must take the last settlement
within a few sessions. *(ii)* Exact-zero settlements (18,349) are the second missing marker and are
dropped (D526); **negative settlements are kept only for CL in April 2020** — nine other negatives,
each a single print on a far-deferred month with the magnitude of a daily change, are dropped and
listed in the meta. *(iii)* Two settlements carried a weekend `ref` and are dropped. *(iv)* The
derive step is a 4–5 minute Python loop; the extract is the fast part.

And the two **breadth** fixtures, which cover **36 roots** rather than a hand-picked few:
**`fut_breadth_hourly.csv.gz`** (the hourly day session, 170,643 root-sessions, 2010-06-07 →;
builder `scripts/build_fut_breadth_hourly.py`; it is the source of the windowed `ids_of` and of
the front-month election every later futures fixture inherits; **two things bite a reader**: it
carries a placeholder row for every Sunday and a few holidays with no close, which must be dropped
before chaining returns or a fifth of every root's returns vanish (D555), and **from 2026-05-30 BTC
has genuine weekend-dated sessions** — CME's weekend crypto trading, up to 22 hourly closes on a
Saturday or Sunday — which D555's loader refuses and D562's drops so the Monday return spans the
weekend as every other root's does; and **two sessions in its calendar are not settlement days**:
**2021-05-31**, Memorial Day, present on a Globex evening bar with no closes and no settlements,
and **2020-06-30**, a truncated archive day with 12 of 36 closes and a third of the settlement
strip's rows — a month-end signal formed on either session alone is empty, and a twelve-month
lookback then voids twelve month-ends for every root; read the last settlement within a window
of sessions, as D556 and D564 do) and **`fut_day5m.parquet`**
(the same 36 roots at **FIVE minutes**, 10,384,830 bars over 135,179 root-sessions, 84 bars per
full session in the 09:00–15:59 ET window, 98 MiB; builder `scripts/build_fut_day5m.py`, decode
88 min then a 2-minute build). It exists because 7 hourly bars pin a non-overlapping past/future
pair to H=3 and one observation per session; 84 bars fit the pair at every H in {3,4,6,8,12,16,20}.
It takes the front month and the `same_front`/`present` flags from the hourly fixture **by inner
join, not re-derived**, so the two cannot disagree about the front (the join keeps 26.5% of 39.2 M
raw bars; the rest are back months). Its **135,179** root-sessions are fewer than the hourly
fixture's **170,643** because the hourly session is 18:00→16:59 and counts sessions that have
overnight bars but nothing inside the day window; the 5-minute fixture holds only sessions with at
least one 09:00–15:59 bar. The 35,464-session gap is **front-loaded exactly where the archive gap
is** — 4,223 in 2011 and 3,665 in 2012 against ~1,600 a year from 2016, heaviest on CL, YM, ES, NQ,
NKD and HO — and no day5m session lies outside the hourly fixture, the inner join being exact.

**What bites, and the meta carries all of it computed rather than asserted.** *(i)* **A root's
SPAN IS NOT ITS USABLE SPAN, and it fails in two different ways that one flag cannot tell apart**,
so `coverage.per_root` reports both: `first_full_bars_year` (the root's own session band ≥90%
populated) and `first_clean_year` (that **and** ≥240 sessions). **ES, NQ and YM read 2011 / 2016** —
the early sessions that exist have *complete* bars and there are merely few of them (ES holds 33
sessions in 2010, 73 in 2011, 113 in 2012, 212 in 2013, 258 from 2016), which is a wholly different
object from **SR3 in 2020: 257 sessions with no five-minute slot present in more than 38% of them**
(SR3 is clean only from 2022). Others: the six FX roots, GC HG SI UB ZB ZF ZN ZT **2010/2011**; the
five grains **2013/2014**; BZ 2015; CL HE HO LE NG NKD PL RB TN **2016**; RTY 2018; BTC 2020; and
**PA NEVER** — palladium tops out at 0.80 fill and carries intermittent interior slots.
*(ii)* **The band is per root, measured not assumed:** 84 slots 09:00–16:00 for the 23-hour
markets, **58 at 09:30–14:20 for the five grains, 55 at 09:30–14:05 for livestock**. A study
applying the 84-slot window to ZC silently reads 26 empty slots.
*(ii-b)* **AND THE WORSE CASE IS THE ROOT WITH FULL BARS AND DEAD VOLUME — [D530](decisions/D530-avenue-3-closed-the-leveraged-ETF-reset-flow-is-real-and.md).**
The grains are obviously empty; **crude is not**. Share of each root's session volume in the
**15:00–15:59** hour, against the 14.3% an evenly-traded root would show: **RTY 21.1%, ES 20.4%,
NQ ~18%, YM 15.7%** (the equity closing hump, 1.10–1.48× even) · UB/TN/NKD/BTC/ZF/ZT/SR3 9.8–14.4% ·
ZN 11.0%, ZB 11.6% · the six FX 6.6–8.3% · **GC 5.4%, SI 4.4%, NG 3.9%, CL 3.1%, HG 2.6%** ·
PL/HO/PA/RB/BZ 2.7–3.4% · **LE and HE 0.02% on 18–19 sessions** · **ZC ZS ZW ZL ZM 0.00%, zero bars.**
COMEX metals close 13:30 ET, NYMEX energy 14:30, grains 14:20, livestock 14:05 — so **16 of 36 roots
have that hour essentially outside their market while still returning bars**. A close measured in an
illiquid tail bounces on the spread, and **bid-ask bounce is indistinguishable from mean reversion**:
D530 got a spurious **z = −12.6 "closing reversion"** across 19 such roots before checking this.
**Any cross-root study on this fixture must use each root's OWN session, not the 09:00–15:59
template** — and note that every price-action statistic computed over the template on a commodity
root in this programme, D515's CL and GC rows included, carries the same contamination.
*(iii)* **`present=False` does NOT mean the bar is missing.** All **443,124** such rows carry real
OHLC and **non-zero volume**; zero have a NaN close. It is the *hourly* fixture's session flag,
`isfinite(hourly_open × hourly_close)` over the root's h09..h15 window, so it marks holidays,
half-days and thin sessions — 6A on 2010-07-05 trades 29 contracts in the opening bar. 8,349 of
135,179 root-sessions (6.2%), heaviest on RB NG HO CL. `same_front=False` marks 4,408 root-sessions,
the rolls, and a return across that boundary is a roll rather than a move.

**The session calendar ([D589](decisions/D589-FIXTURE-cme-session-calendar-and-event-flags-36-roots.md), 2026-09-21).** **`cme_session_calendar.csv.gz`**: one row per (root,
ET calendar day) for the 36 breadth roots, 2010-06-07 → 2026-09-09, **205,428 rows** of which
135,179 are trading sessions; `is_trading`, `session_open_et`, `session_close_et`, `rth_bars`,
`is_early_close`, `front_contract`, `roll_day`, `expiry_day`, `days_to_expiry`, `quad_witching`,
`month_end`, `quarter_end`, `fomc`, `cpi`, `empsit`, `dst_transition_week`. Builder
`scripts/build_cme_session_calendar.py` (system python, 0.3 min; the committed build used
`--events data/calendar/events.csv`, the D585 release calendar). The front month, the roll days
and the index `rth_bars` are **joined from `fut_breadth_hourly` and `fut_index_sessions`, never
re-elected**, so the calendar cannot disagree with them: `roll_day` reproduces
`fut_sessions_rolls.csv.gz` exactly on all nine roots it covers and totals the same 4,408 roll
sessions `fut_day1m.meta.json` records. **What bites:** *(i)* **`session_close_et` is each root's
own settlement minute, measured from its volume cliff, and the nine bands are not the four
`day5m` reports** — **SI closes 13:25, PL 13:05, HG and PA 13:00**, only GC 13:30, and the
livestock cliff is 14:00 with the last trade at 14:04; for the twelve FX and rate roots the value
is the 15:00 ET *settlement*, after which Globex runs to 17:00 (ZN keeps 11.0 % of its session
volume in that hour), and for the seven index-and-crypto roots it is the 15:59 *window edge*, not
a close. *(ii)* **`is_trading=False` is the archive, not the exchange**, before a root's clean
year: eleven of the 65 quad-witching days have no ES day session and all eleven are 2010–2014.
*(iii)* **Two archive dropouts are shaped exactly like market-wide early closes and are rejected
by name** — 2020-06-30 (22 roots stop at 10:10) and, **newly found here and not previously
recorded, 2020-02-27** (17 roots stop at ~13:20 on a Covid-selloff session) — together with 31
Mondays in 2010-06 → 2011-01 on which CL HO NG RB stop at 13:30. What separates them from a
holiday is not a count: an exchange session ends on a five-minute boundary and a feed dropout does
not. All 34 rejected days are listed in the meta, as are the two the rule accepts and probably
should not. *(iii-b)* **There is a fourth incomplete March-2020 ES session: 2020-03-18** (377 of
390 bars), alongside the documented 09, 12 and 16; those four are the only ordinary ES sessions
below 390 bars in the whole 2016+ span. *(iv)* **`fomc`, `cpi` and `empsit` are null, not False,
before 2016**, where the D585 events file has no rows; from 2016-01 to 2026-09-09 they are the
sourced release days (ES: 91, 127 and 128 flagged trading days). *(v)* **`expiry_day` is the
root's expiry calendar and `days_to_expiry` is the front contract's**, so `expiry_day` is *not*
`days_to_expiry == 0` — the volume-elected front rolls one to two weeks early and never reaches
expiry. *(vi)* **`quad_witching` comes from the ES expiry file, not the third-Friday rule:
2026-06-18 is a Thursday** because the third Friday of June 2026 is Juneteenth. *(vii)*
**Thanksgiving Day is a trading day** (ES 09:00–13:00 ET); the full closures are Good Friday,
Christmas and New Year's, and the observance rule is asymmetric — Christmas on a Saturday moves to
the Friday, New Year's Day does not. *(viii)* **Gate G6, the cross-check against CME's own holiday
page, did not run**: cmegroup.com returns 403 to this machine and the fetch attempts are logged in
the meta; the holiday set is the one derived from the bars.

### Six things that will bite a study reading this

1. **NOT COMMITTED, AND CANNOT BE.** CME's terms forbid redistributing archived data, so
   the bars live in gitignored `data/raw/databento/`. What *is* committed is the re-fetch
   script, the manifest, the verification artifact and every hash.
   **It is re-downloadable free only until roughly 2026-10-11**, 30 days after each job
   completed; after that it is a fresh purchase at $7,719 of published rates.

   > **It was first written to `temp/databento/` and moved on 2026-09-12.** `temp/`'s own
   > README says *"if deleting a file would cost something, it does not belong here"*, and
   > 111 GB on a 30-day re-fetch clock costs plenty. `data/raw/` is the repo's established
   > home for a gitignored raw cache — D191, cache the raw and commit the derived.
2. **The last session is missing.** The pull ends **2026-09-10**, not 2026-09-11. The final
   bars slice was resubmitted with a backed-off end while chasing a stall. Any study
   quoting "through 2026-09-11" is wrong by one session.
3. **Prices are UNADJUSTED and there is no continuous series.** Databento: *"the continuous
   contract prices returned are the original, unadjusted prices."* These are raw symbols, so
   there is no roll at all yet — the roll calendar must be built from `definition`, and
   [`futures_continuous.py`](../scripts/futures_continuous.py) plus its acceptance gates
   exist for exactly that.
4. **`ohlcv-1m` arrived in TEN jobs, not one.** Two wide jobs stalled and were split. The
   slices tile cleanly, but a loader must read all ten directories, and the job-to-window
   map is in the manifest rather than inferable from filenames.
5. **FILTERING TO "FRONT MONTH" NEEDS ID *WINDOWS*, NOT AN ID SET.** ES trades its deferred
   contract thinly for months before the roll, so a mask of the form
   `isin(instrument_id, front_month_ids)` admits **two expiries at once**, priced ~60 index
   points apart — the calendar basis. This bit twice on 2026-09-12, in
   [`d465`](../scripts/d465_es_spread_and_mae_bias.py) and again in
   [`d469`](../scripts/d469_scalping_feasibility.py):

   - **Only 3.9% of records were wrong, and it moved a published number by ~1 pp**, because
     the statistic was a **running max**. A max reads the extremes, so a *sparse* contaminant
     dominates it. Per-record measurements (a spread reads bid and ask off the same record)
     were barely touched; anything walking a path across records was wrecked.
   - The tell was **a p99 that did not move with the horizon** — 240 ticks at 10 s and at
     15 min alike, against a median of 2. A constant tail across horizons is a basis, not
     a move.
   - **Clip every id to its own date window, then assert at most one `instrument_id` per
     second**, and drop any pair whose two ends are different contracts. Both scripts now
     carry that gate and prove it fires.

   > **AND IT BITES IN THE OTHER DIRECTION TOO — [D520](decisions/D520-the-sessions-builder-labelled-bars-from-a-flat-id-dict-and-it.md).**
   > A `{instrument_id: symbol}` dict built from `store.metadata.mappings` with the
   > `start_date`/`end_date` discarded is the same defect wearing the opposite hat: an id is
   > **not** a stable handle on a contract. CME reuses the single-digit-year slot at expiry
   > (`CLN9` is July-2019 then July-2029) *and* rotates a live contract onto a new id — but the
   > large term is that an id which is one of your outrights in one window is an **option, a
   > calendar spread or a different product** in another, for which no window exists at all.
   > Measured over the whole `ohlcv-1m` archive on nine roots: **229,206 of 77,151,155 bars
   > (0.297%, and 4.31% on the worst file)**, including 79,479 bars of Micro AUD/USD labelled
   > `6EF3` and spreads at **negative prices** labelled `NQM3`. **Build the windows, label each
   > bar from the window containing its timestamp, and raise if one id's windows overlap** —
   > `scripts/build_fut_breadth_hourly.py` and `scripts/build_fut_sessions_hourly.py` both do.
   > A front-by-volume rule happens to be insulated (the reused slots are the months nothing
   > trades), **except on a holiday**, where ten spurious contracts elected the euro's front
   > month on 2021-12-24.
   >
   > **[D521](decisions/D521-the-three-remaining-flat-id-builders-are-ported-and-the-open.md) finished the job: NO builder in the repository labels a bar from a flat dict any
   > more**, and the three it ported were rebuilt and diffed. `fut_micro_flow_5m` and all six
   > `fut_index_1m` outputs came back **byte-identical** — the index build ingested **16,077
   > foreign RTH bars (0.229%, 18 of 26 files)** and the front-by-volume rule dropped every
   > one, insulated exactly as above. **`fut_open_interest_daily` did NOT**: it is the one
   > fixture here with a column that has no volume filter in front of it (`oi_total`), and it
   > was wrong on 12 CL sessions. **The rule of thumb: front-month columns are insulated,
   > totals and strip counts are not.**
   >
   > **AND THE FLAT DICT IS NOT DETERMINISTIC — [D524](decisions/D524-the-day5m-fixture-verifies-clean-and-a-flat-id-dict-is-non.md).**
   > `store.metadata.mappings` iterates in a different order in every process, so "the last
   > write wins" picks a different winner each run: on the 2019 file **all 8 ambiguous ids get a
   > different label depending on the process** (8 of 8 over six hash seeds, 0 appearing stable
   > against 0.25 expected by chance) — id 73454 reads the Nikkei `NKDU0` five times and then
   > **silver `SIF9`** on the sixth, so a five-read probe would have called it stable. The
   > *count* of mislabelled windows is stable; the
   > *identities* are not. Two flat-dict builds of the same code over the same archive therefore
   > produce **different fixtures**, and **a flat-built fixture cannot be reproduced or audited
   > after the fact** — distrust any pre-D520 flat-built artefact beyond the rows a diff happened
   > to catch. The exposure is far larger on the **36-root** list than on the index roots:
   > **29 mislabelled outright windows and 14,139 foreign windows**, against **0 and 712** for
   > ES/NQ/YM/RTY. `fut_day5m` itself verifies clean: rebuilt byte-identical, and its 5-minute
   > bars fold into the hourly fixture with **0 differences across 906,905 root-session-hours**
   > in o/h/l/c/v **and trade count**.

6. **THE ENERGY DAY SESSION IS NOT IN THE ARCHIVE BEFORE JUNE 2015** (D520, extending D462's
   index-futures finding). **CL, NG, RB and HO** carry the same pre-2016 gap on hours 21→14 ET
   that ES/NQ/YM do, **and additionally lose 15:00–16:59 ET entirely until 2015-06**: in 2013
   the front contract's bars run out at **14:30–15:17 ET** and hour 15 is populated on **0 of
   308 days**, against 250 for GC, SI, ZN, ZB and 6E, which are complete from 2010. The
   switch-on is abrupt — 0–7 days a month carry an h15 bar through May 2015, then **22 in June
   2015**. BZ is unaffected, and GC had a pit and is complete, so "pit-traded products" is not
   the rule; the mechanism is unknown and the coverage is the fact. Anything computing a
   day-session statistic on the energy complex must start at 2015-06 or later, and
   `fut_sessions_hourly`'s G5 already gates CL to 2016-01-04.

### Compression measured per schema, and it spans 10x

`status` 27.99x · `definition` 29.39x · `statistics` 5.24x · `ohlcv-1m` 4.21–4.92x ·
`bbo-1m` 4.05x · `tbbo` 3.09x · `mbo` 2.89x

**Never apply one schema's ratio to another.** Doing so once would have under-reserved disk
by roughly tenfold; see [`decode_pipeline_bench.json`](../data/decode_pipeline_bench.json).

### Reading it costs more than it looks

Profiled on this machine: **zstd decompression is the bottleneck at 754 MB/s per core,
while the numpy parse runs 8,755 MB/s** — the DBN format is nearly free to read and the
decompression is the whole cost. One worker consumes 254 MB/s of compressed disk read, so
twelve workers want ~3 GB/s. Against 31.7 GB of RAM and a ~200 GiB universe, **this is
out-of-core work**: studies stream rather than load once.

### Not bought, and why

`mbp-1` (212 h of download, and `tbbo` answers the spread question) · `mbp-10` (Databento's
own docs say derive it from `mbo`) · `ohlcv-1s` (excluded by the principal; 1-minute only) ·
`definition`/`statistics` at full universe (520 B per instrument **per day** traded or not —
496 GiB, larger than the bars) · `bbo-1m` at full universe (**3,190 GiB**, 12.5 GiB/day,
because it snapshots every option strike every minute).

**Path resolution is a staircase:** 2010–2025 is 1-minute only, the last 12 months are
trade-by-trade, the last month is order-by-order.

---

## 2. US equities and ETFs — committed fixtures

`data/fixtures/*.csv.gz`, each with a `.meta.json` and usually an `_events.json`.
**`ragged_panel.py:76-111` refuses to load any fixture whose meta lacks a passing `gates`
block** — that is the chokepoint, not a convention.

### Single names, daily

| fixture | names | rows | span |
|---|---:|---:|---|
| `us_shorts_daily_raw` | **1,573** | 4.14 M | 2010-01-04 → 2026-08-26 |
| `us_shorts_daily_holdout` | 803 | 2.16 M | same |
| `us_shorts_daily_holdout2` | 576 | 1.53 M | same |

**Both daily holdouts are SPENT** — 2026-09-10, by the D412–D433 second-zone line. The
touch effect reproduced at +10/+10/+13 bp gross on three name sets and net Sharpe was ~0 on
all three. **Never re-read these fixtures for that construction.** Holdout spend is per
line, though: a holdout spent by an unrelated strategy is still unseen by a new one, so
this is not a blanket ban.

### ETFs

| fixture | symbols | rows | span | session |
|---|---:|---:|---|---|
| `etf_wide_daily_raw` | **551** | 2.22 M | 2010-01-04 → 2026-08-26 | daily |
| `etf_intraday_15m_raw` | 57 | 3.19 M | 2018-01 → 2026-08 | **regular hours only** |
| `index_extended_15m_raw` | 4 (SPY QQQ IWM DIA) | 0.96 M | 2010-01 → 2026-08 | **extended 04:00–19:45** |
| `wide_extended_15m_raw` | 11 | 2.44 M | 2010-01 → 2026-08 | extended |
| `universe_daily_2015_2024_raw` | 57 | | 2015 → 2024 | daily |
| `universe_holdout_daily_raw` | 60 | 0.15 M | | daily |
| `universe_wide_w1/w5_raw` | ~96 / ~95 | | | daily |

**The 15-minute and daily fixtures disagree on corporate-action basis** — 15m is fully
adjusted, daily is not. That has already put one name at 5x its own prices, and
`raw_price_factor` cannot repair a spinoff. Check the basis before crossing them.

### Intraday cohorts

`cohort3` (8 names, 0.45 M rows) · `cohort4` (24, 1.35 M) · `single_name_intraday_15m_raw`
(8, 0.45 M) · `holdout_intraday_15m_raw` (16, 0.90 M) — all 15-minute, 2018-01 → 2026-08.

### Crypto

`crypto_universe_2015_2025_raw` (63 coins, daily) · `crypto_binance_15m_raw` (25 MB, 15m,
2017 → 2026) · 30m and 1h slices · `crypto_book_2018_raw`.

**`fut_es_options_eod.csv.gz` + `fut_es_options_eod.meta.json` ([D581](decisions/D581-STAGE-0-DESIGN-gamma-conditioned-close-on-ES-the-discriminator.md), 2026-09-21; panel gitignored by pattern, in the manifest by hash):**
one row per (usable ES session, ES-family option): family, right, strike, expiry date and time,
underlying future, **open interest as of the prior close**, the prior settlement, the OI's
publication time, and for the same-day-expiring option its minute-bar volume to 15:30 ET;
**19,225,749 rows over 2,658 sessions 2016-01-04 → 2026-09-09**, 25 families (ES quarterly, EW
end-of-month, EW1–EW4 Fridays, E1A–E4A Mondays from 2017-04, E1C–E4C Wednesdays from 2016-10,
E1B–E5B Tuesdays and E1D–E4D Thursdays from 2022-05). Built by `scripts/build_fut_es_options_eod.py`
(`--defs`, `--stats`, `--bars`, `--build`, `--gates`, `--selftest`) over two Databento batch pulls
recorded in `data/es_options_pull_jobs*.json` (`statistics` + `definition`, quoted at 47.7 GB and
336.2 GB billable, **USD 0.00 each** under the subscription; ~67 GB compressed under
`data/raw/databento/GLBX-20260920-*`). Keyed on the session a publication is first USABLE
(D497/D521: the OI published ~21:00 ET on T−1 is session T's). **What bites:** *(i)* **the
`ES.OPT` parent is the quarterly family alone** — the weeklies and dailies are their own parents
(`EW.OPT`, `EW1.OPT` … `E4D.OPT`; `E5A` does not resolve); *(ii)* **single-digit year codes
recycle** — `ESZ6 C2200` is December 2016 and December 2026 — so an option's strike and expiry
must come from the definition of its instrument id in force at the publication (D520's windowed
rule), never from the raw symbol; *(iii)* a definition record is republished every session, so
the first record per (id, symbol) is the window start and the last is the expiry-day record;
*(iv)* an expired option's final OI is published on its last evening and is usable the next
session — drop rows whose expiry is before the session, or 1.49M contracts of expired ESM2
options sit in 2022-06-21; *(v)* the quarterly expires at 09:30 ET (AM settlement), every other
family at 16:00; *(vi)* `settle` is missing on 0.5 % of rows (no settlement published).

**`fut_btc_1m.csv.gz` + `fut_btc_1m.meta.json` ([D580](decisions/D580-STAGE-0-RESULT-not-supported-a-five-minute-unsigned-burst.md), 2026-09-20; panel gitignored by pattern, in the manifest by hash):**
BTC and MBT outright bars at one minute, **every session, keyed in UTC** (bar start), front month
per (root, CME trade date) by full-date volume through D462's windowed id labelling; BTC
1,936,567 bars over 2,286 sessions 2017-12-18 → 2026-09-10, MBT 1,386,977 bars from 2021-05-03.
Trade date = US/Eastern date of ts + 7 h (the 18:00 ET open belongs to the next date, the breadth
fixture's own convention). Builder `scripts/build_fut_btc_1m.py` (`--verify`, `--build` on the
system interpreter, 3 min on six workers, `--gates`, `--selftest`). **What bites:** *(i)* **a bar
prints only when the contract trades** — BTC has bars on 59 % of open minutes, MBT 53 %, so a
"bars present" rule is a liquidity filter, not a session test; define presence as the minutes
between a trade date's first and last bar and treat an untraded open minute as volume 0; *(ii)*
the schema has no trade count; *(iii)* from 2026-05-30 Saturday and Sunday trade dates exist
(CME weekend crypto sessions); *(iv)* the daily halt (21:00–22:00 or 22:00–23:00 UTC by DST) sits
inside any window that spans the US evening.

**`perp_funding.csv` + `perp_open_interest_daily.csv` + `perp_funding.meta.json` ([D579](decisions/D579-FIXTURE-perpetual-funding-rates-and-open-interest-three-venues.md), 2026-09-20):**
perpetual-swap funding rates, tidy, one row per (venue, symbol, settlement UTC): Binance USDT-M
BTC/ETH from 2019-09-10 / 2019-11-27, Bybit linear from 2020-03-25, **Bybit inverse BTCUSD from
2018-11-15 (deepest)**, OKX three months only; 46,892 rows to 2026-09-20, every series 100 % of
its 8-hour slots; Bybit daily open interest for the four swaps from 2020-08-04 (8,876 rows).
Fetcher `scripts/fetch_perp_funding.py`, stdlib, free, raw cache `data/raw/perp_funding/`.
**What bites:** *(i)* Binance's settlement timestamps carry a **+1 ms offset on the wire** on
6,640 rows — the build floors keys to the minute, or a cross-venue join loses half its rows;
*(ii)* **a third to a half of every series is exactly +0.0001**, the venues' clamp at zero
premium, so a signed mean over all events is biased positive by construction — exclude defaults
in any signed test; *(iii)* the rate settled at S is the period's average premium, known only
to within the last minutes, so the strictly-in-advance rate is the one settled at S−8h; *(iv)*
open-interest history is Bybit's alone (Binance serves 30 days, OKX refuses old ranges).

### Positioning — the one price-free, fully committable series

`cftc_cot_raw`: **34 symbols, 274,473 rows, 1986-01-15 → 2026-09-15** (28 symbols to
2026-08-25; ZL ZM HO RB PL PA added in D572 to 2026-09-15, so every one of the 17 commodity
roots has its series). US government public domain, so unlike every CME product here it may
live in the repo (the panel is gitignored for size since D536 and carried by hash in the
manifest; the map and meta are tracked). Commercial / non-commercial / non-reportable open
interest per contract. See [`cftc_cot.md`](cftc_cot.md).

`wasde_grains_su.csv`: **USDA WASDE supply and use for corn, soybeans and wheat — 1,170
(release, commodity, marketing-year) rows over 195 monthly releases, 2010-04-09 → 2026-09-11**,
ending stocks, total use, production (million bushels) and stocks-to-use, keyed by the report's
own release date so a study can read it point in time (D567). Public domain. Built by
`scripts/stage0_d567_grains_harvest.py` from the raw monthly CSVs in `data/raw/usda/wasde/`
(2010-04 → 2015-12 archive, 2016–2020 filtered in a browser session, monthly files from 2021;
**the 2025-10 report is absent**). **What bites:** the file holds releases past 2024-01-01 —
a study on the reserved slice's rules filters it by `ReleaseDate` before anything else and
asserts the count (D568: 978 rows, 163 releases); some monthly source files write the release
date month/day/year and the builder normalises and checks it against the report month.

---

## 3. Raw caches — gitignored, re-fetchable

| cache | files | size | what |
|---|---:|---:|---|
| `data/raw/alphavantage` | 50,886 | 1,584 MB | every 15-min and daily slice ever pulled; a cached slice is never re-fetched, so a run resumes |
| `data/raw/edgar` | 1,592 | 1,088 MB | SEC filings behind the 8-K and insider lines |
| `data/raw/binance` | 279 | 486 MB | crypto |
| `data/raw/cftc` | 84 | 21 MB | COT |
| `data/raw/databento` | 129 | 111 GB | **the futures, above** |
| `data/raw/robintrack` | 8,597 + archive | 4.0 GB | **Robinhood holder counts, hourly, 8,597 tickers, 2018-05-02 → 2020-08-13** (the Barber–Huang–Odean–Schwarz data); two ~10-day site outages ending 2019-01-30 and 2020-01-16; 959 / 512 / 341 names overlap the three daily fixtures; the 504 MB `.tar.gz` from robintrack-data.ameo.design is kept beside the extraction. Re-fetchable while the mirror lives; treat as not |

---

## 4. Reference data committed alongside

[`futures_contract_specs.json`](../data/futures_contract_specs.json) — multiplier, tick size
and tick value for 29 CME products, read from CME's own contract-spec service. **The 4% MLL
is a dollar limit, so a path in index points is unusable without this.**

[`cme_product_census.json`](../data/cme_product_census.json) — all 1,592 listed CME futures
products by open interest. **1,069 carry zero open interest**; only 246 carry 1,000
contracts or more; the 41-root buy list is 92.3% of all CME futures open interest.

Plus ~622 committed JSON artifacts in `data/` holding the numbers decision records quote.

**The CME settlement-window table ([D586](decisions/D586-FIXTURE-cme-settlement-windows-with-effective-dates.md), 2026-09-21).** [`settlement_windows.csv`](../data/settlement_windows.csv) — 24 rows,
one per (root, effective period), for 17 products across NYMEX, COMEX, CBOT and CME: window start
and end in **both** CT and ET, the basis quoted from CME's own procedure page, `effective_from` /
`effective_to`, `history_status`, `source_url` and `accessed_utc`. Read it through
`scripts/settlement_windows.py:window_for(root, date)`, which **RAISES** for an unmapped product
and for any date before that product's earliest *sourced* effective date; micros inherit their
parent's row through `MICRO_PARENT`, never a duplicate row. **What bites:** *(i)* **CME publishes
only half of these in Chicago time** — CME and CBOT products (livestock, grains, equity index) in
CT, NYMEX and COMEX products (energy, metals) in ET, and silver appears in both zones on two CME
pages; read the wrong one and you are an hour out. *(ii)* **Only energy (2009-06-01, SER-4867) and
equity index (2020-10-26, SER-8591) have a sourced history**; the eleven metals, grain and
livestock rows are `current_only`, so `window_for("GC", "2023-06-01")` **raises** by design —
source the history before a study reads it, do not assume it. *(iii)* **Two windows are thirty
seconds long** (livestock 12:59:30–13:00:00 CT, equity index 14:59:30–15:00:00 CT) and cannot be
resolved on a one-minute bar. *(iv)* The energy window is the **active month's**; the expiring
month on its last day uses 14:00:00–14:30:00 ET instead. *(v)* **KE is in the table but not in
`fut_day1m.parquet`**, so it carries no volume measurement. The measurement that is there, in the
meta: **in-window volume per minute is 2.53×–16.9× the five minutes before it on all 16 measurable
roots in all 8 years 2016–2023, 128 of 128** (HE 13.5–16.9×, LE 11.2–14.6×, ES 6.0–8.2×, CL
2.5–3.9× the weakest), and 3.5×–40.7× each root's own session mean minute — the window carries
0.83% (GC) to 9.7% (HE) of the whole session's volume in one or two minutes. Every window sits inside the fixture's
09:00–15:59 ET band; **the ES and NQ post-window flank does not exist** (their window is bar 419).
Sources sentence by sentence in `data/settlement_flow/SOURCES.md`; raw pages cached, gitignored,
under `data/raw/cme_settlement/`. The three COMEX metals do **not** settle together (HG 13:00, SI
13:25, GC 13:30 ET), so a basket across metals, grains, livestock, energy and equity has window
ends three hours apart.

**The sourced US economic release calendar, with times ([D585](decisions/D585-FIXTURE-sourced-us-economic-release-calendar-with-times.md), 2026-09-21).** [`calendar/events.csv`](../data/calendar/events.csv): **1,501
releases, 2016-01-06 → 2026-12-31**, one row per release: CPI (131) and the Employment Situation
(131) at 08:30 ET from the BLS year schedules; the FOMC statement (85 scheduled, 7 unscheduled)
at the clock printed on that meeting's own press release; and the EIA weekly petroleum (573) and
natural-gas storage (574) reports at 10:30 ET with every published holiday shift. US government
public domain. Built by `scripts/fetch_release_calendar.py` from `data/raw/calendar/` (196 raw
pages, gitignored); provenance per row (`source_url`, `method` ∈ {fetched, archived},
`accessed_utc`) and six gates in `events.meta.json`; `SOURCES.md` beside it. **What
bites:** *(i)* **the file is a schedule, not a log** — EIA's rows are what EIA published, so an
unannounced delay is invisible, and the last exception either EIA page lists is 2026-11-11
(petroleum) / 2026-11-26 (gas); *(ii)* **2025 has 11 CPI and 11 EMPSIT rows**, not 12 — the
2025-10-01 funding lapse — and **2026 has 6 FOMC rows**, because the October and December 2026
meetings have no published release clock yet (their dates are in the meta, not the CSV, and all
eight 2027 meetings likewise); *(iii)* it **disagrees with `data/macro_release_calendar.json` on
nine 2016-2023 CPI/EMPSIT dates**, which that older file gets wrong (it puts the January 2016 CPI
on MLK Day) — the differences are enumerated in the meta and neither file is derived from the
other; `scripts/run_d494_outside_path.py` still reads the older file, and D494's event gates were
built on those nine wrong dates; *(iv)* **the 2019-07-04 week shows a schedule revision**: captures
before June 2019 put the gas report on Friday 07-05, every later capture on Wednesday 07-03 at
12:00, and the later statement wins, with the conflict recorded.

**The prop-firm venue terms ([D590](decisions/D590-hurdle-p-and-the-component-series-become-library-code.md), 2026-09-21).** [`prop_venues.json`](../data/prop_venues.json) — the 14 plans
`scripts/d386_full_lifecycle.py` carried as a Python literal (Apex 25/50/100/150K, MyFundedFutures
Rapid and Rapid EOD 25–150K, Topstep 50K, Take Profit Trader 25–150K), keyed `apex_50k`,
`mffu_rapid_eod_50k`, `topstep_50k` and so on. **Every one of the 24 plan fields carries `{"value",
"provenance"}`**: the four assumed values name the D386 ASSUMPTION they come from, the MFFU lock
levels quote the two `help.myfundedfutures.com` pages from `data/d445_floor_lock_sources.md`. Each
venue also carries `flatten_time_et` (R11 P2 — Apex 16:59, MFFU and Topstep 16:10),
`automation_permitted_funded` (R11 P6 — Topstep and MFFU only) and `daily_loss_limit`. **Two
things in it are `null`, and the `null` is the finding:** Take Profit Trader's flatten time appears
in no source this repository holds, and **no venue carries a daily loss limit at all**, which leaves
R11's P3 justification ("daily loss limits run 2–3%") unverified, as its own 2026-09-13 amendment
flagged. Read it through `validation.hurdle_p.load_venue(key)`; `p2_flatten` and `load_venue`
**raise** on a `null` or an unknown key. **Beside it, a convention: `data/components/`** is where a
component's **daily P&L in dollars** lives — `<name>_daily_usd.csv` (`date,usd`, zero on a flat
day, LF newlines, floats written with `repr`) plus `<name>_daily_usd.meta.json` (size, cost line in
dollars per round trip, window, producing record, sha256 of the source and of the CSV).
`validation.component_series.read` **refuses a CSV whose bytes no longer match the recorded hash.**
Three rows of `docs/COMPONENTS_PROP.md` read "ρ not computable — the arm's daily P&L is not on
disk" because `run_d466_components.py` writes summaries only; this is the artefact they were
missing. **The directory is empty at the time of writing** — write a series from the runner that
computed it, never by re-deriving it elsewhere (the D466 error).

**The reconciled futures cost table ([D591](decisions/D591-futures-cost-bricks-and-the-reconciled-cost-table.md), 2026-09-21).** [`futures_costs.json`](../data/futures_costs.json) — the 36 breadth roots, a `micro` and a
`full` entry where CME lists a micro (47 traded symbols), **289 cited values**. Per entry: tick
geometry from the specification files, a **declared** `commission_rt_usd` ($3.00 micro / $6.00
full, D468's convention), every **measured** `crossing_ticks_rt` line the contract appears in
(`d465`, `d508_exec`, `d508_all`, `d510`, `d507_all`, `d507_exec`, and the `d556_one_tick`
convention), the `default_line` the bricks serve, and the round-trip dollars each runner actually
charged (`d469`, `d527`, `d531`, `d533`, `d535`, `d556_min_size`). Every number is copied from a
committed artefact at a named key path or from a runner literal read through `ast`, with its
decision and measurement window; the builder (`scripts/futures_cost_table.py --build`, no
timestamp, `--selftest` compares the committed bytes by sha256) refuses a value it cannot find.
Read it through `costs/futures_bricks.FuturesRoundTrip.from_table(root, size, line)`, which
**raises** on a line the contract was never measured on rather than serving another root's number.
**What bites:** *(i)* **every crossing census was measured on 2025-09..2026-09** and most studies
run 2016–2023 — a tick is fixed in price, so a recent spread on an older, cheaper window is
optimistic; *(ii)* `d507_*`/`d510` are **quoted** spreads (a floor) and `d465`/`d508_*` are
**effective** crossing — different statistics, never averaged or substituted, which is why the
default falls back to one tick and not to D507; *(iii)* commission is declared, never measured;
*(iv)* `tick_usd` for **ZC/ZS/ZW (1250), HE/LE (1000) and ZL (600) is in CENTS** and SR3's 0.0625
is CME's $6.25 a hundredfold small — inherited from the definition snapshot, listed under
`spec_flags`, written unchanged; *(v)* the measured default is **4–48% dearer per round trip than
the one-tick line D555/D556 charged** on the eight micros where both exist (MGC +48%, MCL +26%,
MBT +23%, MNQ +16%) — check which line a number was computed on before comparing two studies;
*(vi)* five disagreements between runners are recorded, not resolved: full-size commission $4
(D469) against $6 (D468/D555), D533's GC and NG $5.00 that no line derives, and two 1-ULP splits
in D527's and D465's tick counts. ZN's published `21.63` is a rounding tie on 21.625.

**The programme α registry ([D592](decisions/D592-programme-alpha-registry-trial-counter-and-episode-checks.md), 2026-09-21).** [`programme_registry.json`](../data/programme_registry.json) is the
state and [`docs/results/PROGRAMME_REGISTRY.md`](results/PROGRAMME_REGISTRY.md) is rendered from
it — the deposit's `results/` root does not exist here, so its `results/PROGRAMME_REGISTRY.md`
maps to `docs/results/`. α = 0.05 in **ten slots of 0.005**; seven families seeded in slots 1–7
(dated 2026-09-21), slots 8–10 reserved, 0.035 allocated. `validation.programme.Registry.register`
**refuses an eleventh family without an amendment flag**; a markdown table cannot, which is why the
page is never the source of truth. The programme trial count the DSR reads is **83,074** under a
two-clause rule (distinct de-duplicated sqlite configs from `data/trial_registries.json`, plus rows
of every `trials.csv` under `data/`); **no `trials.csv` exists yet**, so the futures line starts
at zero logged trials, and a test asserts that zero so it stops being true out loud.

---

## 5. What is still missing

- **No futures fixture yet.** 111 GB of DBN sits decoded-by-nobody. The next phase needs the
  seven validation gates in [`fetch_futures_1m.py`](../scripts/fetch_futures_1m.py) reworked:
  they were written for a *continuous stitched* series and this is *raw-symbol full-universe
  across seven schemas*, so the roll gates do not transfer.
- **No equity options.** [D84](decisions/D84-options-scoping-writeup.md) scoped it: chain data
  at 100–1000x volume plus 6–10 weeks of engine surgery for the expiry lifecycle.
- **Nothing pre-2010-06-06 on futures.** `GLBX.MDP3` starts there; it does not exist to buy.
- **No `mbo` before 2017-05-21** even inside the subscription — that is the schema's own start.
