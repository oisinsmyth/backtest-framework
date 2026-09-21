# D613 FIXTURE — **the ES-family option volume panel in ET clock buckets**, so an option-ladder conditioner can be fixed at a cutoff of the study's choosing instead of only at 15:30: 5,313,336 (option, session) rows over 2016-01-04 → 2023-12-29, every traded expiry and not only the same-day ones, five buckets whose 15:30 sum reproduces D581's committed `vol_to_1530` exactly on all 140,361 rows it covers while every uncovered row is proven to be a genuine zero; **59.3 %** of the pre-15:30 0DTE volume is already in by noon; the eight source files reaching 2024 were never opened and are named

**Data layer only. No signal, no return, no statistic about the close.** The panel exists because
a conditioner that accumulates to 15:30 is contemporaneous with a 15:30 → 16:00 window and cannot
be separated from the move it chased; this makes an earlier cutoff available. Nothing admitted
(R15). **The reserved slice is enforced at the FILE level**: a source file whose span reaches
2024-01-01 is never opened, which is a stronger guarantee than filtering rows after the read, and
the eight excluded filenames are recorded in the meta.

*2026-09-21. Builder `scripts/build_fut_es_0dte_volume_cutoffs.py`, run under the system
interpreter because `databento` is installed only there. **Decode:** 11 files, 6,224 MB compressed,
`[SPEED] sum(item time)/wall = 5.09x on 6 workers (85 %)`, 4.0 min wall, 561,404,627 raw bars read.
Fixture `data/fixtures/fut_es_0dte_volume_cutoffs.csv.gz`, 30.0 MB, gitignored by suffix and
registered in the manifest by hash; sidecar `.meta.json` tracked. Every gate proven to raise on a
break inside the build. **Read:** `data/raw/databento` ohlcv-1m for 2016-01-01 → 2023-12-31, and
`fut_es_options_eod.csv.gz` for the reproduction gate. **Not read:** any source file whose span
reaches 2024-01-01 — eight of the twenty-six, named in the meta — and the seven files ending before
2016-01-01, which lie outside the ES day session's usable span and were skipped to save 15 % of the
decode.*

---

## 1. What it holds

One row per (option, session) that traded, with volume split into five ET clock buckets.

| column | meaning |
|---|---|
| `raw_symbol`, `session` | the CME option symbol, and the **ET calendar date** of the bar's start |
| `v_0000_1200` | contracts traded 00:00 → 11:59 ET |
| `v_1200_1530` | 12:00 → 15:29 |
| `v_1530_1600` | 15:30 → 15:59 — **inside a close window, so never a conditioner for one** |
| `v_1600_1800` | 16:00 → 17:59 |
| `v_1800_2400` | 18:00 → 23:59 |

Any cutoff is a sum of buckets: `v_to_1200 = v_0000_1200`, and
`v_to_1530 = v_0000_1200 + v_1200_1530`, which is the quantity D581 committed.

**The session convention, stated because it is not the trading session.** `session` is the ET
calendar date, which is what D581's builder used. The CME trading session for date *D* opens at
18:00 on *D−1*, so the Globex hours belonging to session *D* are filed here under *D−1*. That is
why `v_1800_2400` is its own bucket rather than folded into anything: a study wanting the
session-aligned accumulation adds the prior date's evening bucket, and a study wanting D581's
convention does not. Neither is chosen silently. The consequence for D581's own column, which this
panel reproduces, is that `vol_to_1530` is volume from **midnight** to 15:29 ET and excludes the
prior evening — a detail the committed fixture's own documentation does not state and which this
record now does.

**Coverage is every traded expiry, not only the same-day ones.** D581's `vol_to_1530` is populated
only where `expiry_date == session`. This panel has no such restriction, which is what makes a
**horizon-matched control** possible: a volume-weighted ladder of *later* expiries, with the
weighting held fixed and only the expiry horizon moved. On the committed fixture alone that control
cannot be built, and an adversarial review of the study this panel serves had recorded it as
unbuildable.

## 2. The gates, each proven to raise

| gate | what it asserts | result | the break that fires it |
|---|---|---|---|
| **G1** | rows, span, buckets present and non-negative | **5,313,336 rows**, 2,485 sessions, 416,627 distinct options, 2016-01-04 → 2023-12-29 | a negative volume; a dropped bucket column |
| **G2** | one row per (option, session) | 0 duplicates | a duplicated first row |
| **G3** | the cutoffs are monotone: `v(12:00) ≤ v(15:30) ≤ v(16:00)` | 0 violations in 5,313,336 rows; **share of pre-15:30 volume already in by noon 0.593** | a later bucket made negative |
| **G4** | **the reproduction gate.** `v(15:30)` equals D581's `vol_to_1530`, and a committed row this panel lacks must carry **zero** | **140,361 rows covered, 0 disagreeing**; 263,597 committed rows absent, **all of them zero, none positive** | the noon bucket shifted by one contract; 2,000 traded rows dropped from the panel, which leaves 150 committed positive-volume rows uncovered |
| **G5** | a **scalar-loop second path** on named sessions: one bar at a time, no vectorised id filter, no array `strftime` | **79,255 option bars walked** across 2018-10-11, 2018-10-12 and 2018-12-31; pre-noon volume **417,121 / 302,762 / 162,497** contracts, agreeing exactly | the noon bucket shifted by one contract per row |
| **G6** | no session at or after 2024-01-01, and no opened file reaching it | max session 2023-12-29; **11 files opened, 8 excluded as reserved** | a session set to 2024-01-01; a reserved filename offered for opening |

**On G4's coverage of 0.347, which is the number a reader should not misread.** The committed
fixture zero-fills every 0DTE row whether or not the option traded; this panel holds a row only
where something traded. So the two disagree in *row count* by construction, and the gate's second
clause is the one that matters: of the 263,597 committed rows this panel does not carry, **every
single one has `vol_to_1530 = 0`, and none has positive volume**. The traded 0DTE universe is
therefore covered in full, and the gate raises if 2,000 traded rows are removed.

**On G5's three sessions.** The scalar path walks only the bars of the named sessions, bounded by a
UTC nanosecond window computed from them, because a one-bar-at-a-time loop over a whole year's
50 million bars would cost an hour and a gate nobody runs is not a gate. The sessions are chosen
from those **carrying positive pre-noon volume**: a session with zero on both paths agrees
trivially, and the first draft of this gate picked a Sunday, which is exactly the failure mode this
repository has recorded before — a check that cannot disagree.

## 3. What it cost, and what bites

**Cost.** £0 and no pull: the ohlcv-1m archive was already on disk, bought for the 41-root futures
work, and it happens to contain every ES-family option. 4.0 minutes of wall time on six processes
at 85 % efficiency, above the 70 % floor. 30 MB on disk.

**The write is reproducible.** Two independent builds produced the identical sha256
(`34001e2620de974dfcb2136ba7200e5f3e6dfbccbf8d0ed04b21dd13efb11974`), because the gzip member's
mtime is pinned to 0 rather than left to the clock. A fixture whose hash moves on a rebuild cannot
be verified by the manifest, and D550 already recorded the newline half of that lesson.

**What bites a study that reads this unchecked**, in the order it will bite:

1. **`session` is the ET calendar date, not the trading session** (§1). Adding the prior date's
   `v_1800_2400` is the session-aligned form; not adding it is D581's.
2. **A missing row means zero, not unknown.** The panel is sparse by design. A study must reindex
   against the option universe it cares about and fill zero, or it will silently drop the strikes
   that did not trade — which for a ladder statistic changes the denominator.
3. **Strike, right and expiry are NOT here.** They live in `fut_es_options_eod.csv.gz`, and the join
   is on (`session`, `raw_symbol`). A row with no committed match has no known strike and is
   unusable; those rows are a small share of volume but a study should measure it, not assume it.
4. **The symbol is not the identifier.** Single-digit year codes recycle — `ESZ6` is both December
   2016 and December 2026 — so the mapping from instrument id to symbol is windowed by the
   definition schema's own validity intervals, as D581 established. This builder carries that logic
   verbatim and raises if a bar is claimed by two windows.
5. **Volume is contracts traded, not position, and carries no side.** 0DTE volume is largely
   intraday round trips that leave nothing at the close. No aggressor flag exists before 2025-09,
   and that year is reserved. Any study calling this a dealer-position proxy must say so and report
   the gap.
6. **The quarterly ES family is AM-settled at 09:30**, so on its expiry session it holds no position
   into the close. A same-day filter that does not also require `expiry_hhmm >= "15:30"` will
   include it, and the mistake is silent on about 97 % of sessions.

## 4. What this record does not do

It computes no return, no signal and no statistic about the close: the study that reads it is
pre-registered separately. It does not rebuild or alter `fut_es_options_eod.csv.gz` — that fixture's
bytes, hash and gates are untouched, and this panel reproduces its column rather than replacing it.
It does not extend past 2023-12-29, and the eight source files that would have done so were never
opened.
