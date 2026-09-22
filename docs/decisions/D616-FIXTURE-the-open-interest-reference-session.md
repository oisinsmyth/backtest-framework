# D616 FIXTURE — the open interest's reference session on the ES option panel

*A one-column amendment to `data/fixtures/fut_es_options_eod.csv.gz` (D581), built from the cache already
on disk: no pull, no re-decode, and the existing twelve columns unchanged. Data layer only — no gamma, no
signal, no return.*

## 1. What was missing, and why it matters now

The sharpened-ladder study that follows this fixture conditions on the **change** in open interest,
`oi(t) − oi(t−1)`, because [D614](D614-STAGE-0-RESULT-not-pinning-ten-sessions-carry-the-whole-pull.md)
closed on the finding that traded volume is turnover without a side and therefore cannot carry the
mechanism. (That study's pre-registration is committed after this record and cites it; naming its number
here would be a citation to a record that does not yet exist.) A difference is only a one-session position
change if the two numbers describe **adjacent sessions**, and the panel as committed could not establish
that.

It carried `oi_pub_et`, the publication time. That column cannot do the job, and the reason is
structural rather than a shortfall of precision: a publication is usable on exactly one session under
D497/D521's rule, so **publication times are never equal across adjacent sessions** — measured at
**0.0000** — and a repeat is therefore invisible in it. CME publishes preliminary and then final open
interest, so two adjacent usable sessions can carry two publications for the **same** business date (a
revision, which makes a difference of exactly zero that is not a zero position change) or can skip an
evening (a two-session difference that looks like one). Only the reference date separates those cases.

`scripts/build_fut_open_interest.py` already derives exactly this for futures (`staleness_sessions`).
The options panel did not, and the ingredient was on disk all along.

## 2. What was added, and what it cost

`ts_ref` on a statistics message is **midnight UTC on the business date the statistic describes**. It is
kept in the cached `stats_*.pkl` (`build_fut_es_options_eod.py:120`) and was simply never read, so this
is a `--build` from cache: **no pull, nothing billable, no re-decode of the 47.7 + 336.2 GB of source**.

Measured on the cached publications before anything was written: `ts_ref` is **never UNDEF and never
zero** on these rows, and its ET clock time is 19:00 or 20:00 — both exactly midnight UTC — with 252
distinct dates a year, which is the trading calendar. So the reference session is the **UTC date** of
`ts_ref`, not its ET date, and the builder says so at the line that derives it.

```
t["oi_ref_session"] = t["oi_ts_ref"].to_numpy("int64").astype("datetime64[ns]").astype("datetime64[D]").astype(str)
```

The publication **kept is unchanged** — still the last by `ts_event` within the usable session — so `oi`
itself does not move and D581's and D614's committed results reproduce off the amended file. **That is
proven, not asserted:** the amended file with its final field stripped from every line hashes to
`32804fcfbe2cec969c316f3e7e09494df758d2c6e6c2ba3ca1db7e44cc9d6a1a`, which is the pre-amendment file's own
hash, over all 19,225,750 lines — the twelve original columns are byte for byte what they were, the row
count and session count are the committed 19,225,749 and 2,658, and no row's reference session is empty.
The rebuild took 42.3 min from cache.

That byte-identity was a constraint on the design, not an outcome: a better selection rule is available now that the reference
date is visible (prefer the latest reference session, break ties by publication time), and it is **not
taken here**, because taking it would silently alter two committed records. It is named in §5 as a
candidate amendment instead.

## 3. What the column shows: the revision rate rises sharply with the era

Measured per year on the cached OI publications, at the (instrument, usable session) level:

| year | reference date is an ES session | kept row's gap is exactly one session | cells with >1 publication | **cells with >1 distinct reference date** | **adjacent pairs whose reference span is 0 — a spurious zero delta** |
|---|---:|---:|---:|---:|---:|
| 2016 | 0.9945 | 0.9976 | 0.9976 | 0.1875 | **0.0024** |
| 2019 | 0.9897 | 0.9946 | 0.9695 | 0.0343 | **0.0055** |
| 2023 | 0.9883 | 0.9961 | 0.8790 | 0.1632 | **0.0041** |
| 2025 | 0.9759 | 0.9765 | 0.8244 | **0.3945** | **0.0253** |

Three things follow, and the last is the one that bites.

**The difference is usable.** The kept publication describes the immediately preceding ES session on
97.7–99.8 % of rows, so `oi(t) − oi(t−1)` is a one-session position change on the overwhelming majority
of pairs, and the exceptions are now countable instead of silent.

**The zero deltas are real, not stale.** The stress test measured a **0.428** share of exactly-zero
deltas on 0DTE PM rows. The revision rate that could manufacture a false zero is **0.24 %–2.5 %** of
adjacent pairs. So the zero deltas are overwhelmingly genuine "no position change at that strike", which
is a fact about the instrument and not a data defect.

**The reserved year is the worst year.** The share of cells carrying more than one distinct reference
date reaches **0.3945 in 2025** against 0.1875 in 2016, and spurious zero deltas reach **2.53 %** against
0.24 %. Any later study that scores a signed or Δ-based conditioner on the `tbbo` window — which is
exactly where [D617](D617-FIXTURE-the-ES-option-signed-flow-census-from-the-tbbo-year.md)'s census lives —
inherits a ten-fold worse revision rate than the in-sample era, and must drop those pairs rather than
average over them. That is recorded here so it cannot be discovered afterwards.

Also visible and worth naming: 2019 carries 6,204 publications whose reference session **equals** the
usable session. A number describing session *t* cannot be known on session *t*, so those are either
mis-stamped or a boundary case of the trading-day roll; either way they are look-ahead if used, they are
0.5 % of that year, and G7 caps their share rather than trusting them.

## 4. G7, and why it reports rather than enforces

The six existing gates are unchanged and re-proven on the rebuilt file. **G7** is new:

- the reference session is recoverable — it is a date in the ES calendar;
- it is strictly **before** the session the number is used on, with the at-or-after share under a
  declared ceiling of **0.01**;
- the gap from reference session to usable session is exactly **one** ES session on at least 0.95 of rows;
- and, per option on adjacent fixture sessions, the **reference span is also one session** — the
  quantity a differencing study actually needs — reported beside the share whose span is **zero**, which
  is the revision.

**Measured on the whole panel, G7 green:** the reference session is recoverable on **0.9850** of the
19,225,749 rows, it is one ES session back on **0.9979** of those, and it is at-or-after the session it
serves on **0.0006** — against the declared ceiling of 0.01, so the look-ahead residue is six rows in ten
thousand rather than the 0.5 % one year's probe suggested. Across **18,466,010** adjacent per-option pairs
the reference span is exactly one session on **0.9675** and **zero — a revision — on 0.0021**. The six
existing gates are unchanged and re-proven: G2 still reads 1.0000, G5's second path still agrees on 10/10
seeded sessions, and G6's settlement IV still inverts on 1.0 of 6,818 near-money rows.

It reports the residue rather than refusing the file, because the residue is real, era-dependent and
irreducible from this source. The enforcement belongs in the study: **the differencing study drops every
pair whose reference sessions are not adjacent and declares how many it dropped, and its
pre-registration says so.** A gate that failed the whole
panel over 2.5 % of pairs would throw away the 97.5 % that are sound.

The self-test proves G7 both ways. It passes clean input; it **raises** when a reference session is moved
to at-or-after the session it serves (the look-ahead break); and the revision break — two sessions
restating one business date — takes the pair-span-zero share to exactly 0.5 on a two-pair frame. The
synthetic `assemble` case now also carries the trap itself: two publications usable on one session, the
later one restating the **older** business date, asserting that the last by `ts_event` wins and brings
its own reference date with it, that `oi_pub_et` cannot reveal the restatement because publication times
differ, and that `oi_ref_session` can because the reference dates repeat.

## 5. What this does not fix

- **The selection rule is untouched.** Where a usable session carries publications for two business
  dates, the last by publication time wins even when an earlier one describes the more recent session.
  Preferring the latest reference session is the defensible rule and is left as a candidate amendment,
  because adopting it would change `oi` and therefore two committed results.
- **Same-day 0DTE positioning is still invisible.** A contract opened and expiring on the same session
  never reaches a close, so it never appears in any open-interest print at all. No column fixes that;
  the study's pre-registration states it as a limit of the conditioner rather than of the panel.
- **Nothing here is a signal.** No gamma, no centroid, no return. The 2024+ slice remains unread for
  returns; this rebuild reads only cached publications that D581 already paid for.

## 6. Reproduction

```
python scripts/build_fut_es_options_eod.py --selftest
python scripts/build_fut_es_options_eod.py --build      # from temp/es_options_eod caches; no pull
python scripts/build_fut_es_options_eod.py --gates       # G1-G7 -> meta
```

The panel is gitignored by pattern and carried in `data/data_manifest.json` by hash; the manifest entry
moves with this rebuild, from
`f84ce2e692ade0d6d7f89abc295f810e204275c9bf9ea76547e9214535fa6f58` to
`1e516365d2712a04dae6cbac66f94255140d90cda0c74e84d7e57c315dd5bea4`.

**Anyone merging this branch must re-run `--build`.** The manifest now records the amended file's hash
while an unrebuilt worktree still holds the twelve-column one, so `--verify` will disagree there until the
rebuild runs. It is a `--build` from the `temp/es_options_eod` caches — free, no pull — and it is the
ordinary consequence of manifest-only panel storage (D536/D538) rather than anything specific to this
change.

One operational note, recorded because it nearly went wrong: the panel in this worktree was a **hardlink**
to the shared worktree's copy, so writing the rebuild would have modified another session's file through
the shared inode. The link was broken before the write. A worktree that hardlinks gitignored panels to save
disk shares their bytes, and a builder that rewrites one in place writes into every worktree holding it.
