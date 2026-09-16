# D538 — Two panels come back into the index: D536's suffix rule was a proxy for size, and on its two smallest members the proxy was wrong

**Status:** Committed
**Date:** 2026-09-16
**Category:** Data layer
**Source:** Clone-skip triage. Amends [D536](D536-manifest-only-storage-for-the-bulk-panels.md) — its
universal suffix claim, and nothing else. Does not touch
[D191](D191-manifest-only-storage-for-large-archives.md),
[D24](D24-immutable-data-snapshots-fetch-once-freeze.md) or
[D70](D70-committed-csv-fixture-as-frozen-snapshot.md), whose requirement D536 kept and this record
keeps harder.

## Decision

Two of D536's 118 panels are **tracked again**, by an explicit `!` negation inside D536's own
`.gitignore` block:

| panel | on disk | clone skips it unblocks |
|---|---|---|
| `data/fixtures/crypto_daily_2015_2025_raw.csv.gz` | **0.2 MB** (216,422 B) | **47** |
| `data/fixtures/crypto_universe_2015_2025_raw.csv.gz` | **6.7 MB** (6,654,222 B) | **26** |

6.9 MB, taking the index from 147.7 MB to 154.6 MB — **under 5%** — and unblocking **73 of the 136
tests a fresh clone currently skips**. Their consumers are seven test files
(`test_breakout_study.py`, `test_breakout_universe_study.py`, `test_breakout_intraday_study.py`,
`test_crypto_pairs_study.py`, `test_breakout_era_analysis.py`, `test_breakout_universe.py`,
`test_snapshot_store.py`).

Three things about the mechanism, because each was a choice:

1. **The exception lives beside the rule, not in a flag.** `git add -f` would have produced the same
   two tracked files and left no trace in `.gitignore`, so the next reader of `:102` would read a
   universal rule that is not universal and would have no way to find out why. The negation and its
   comment are at `.gitignore:107-119`, inside the reasoned bulk-panel block, in the shape
   `/temp/*` + `!/temp/README.md` at `:56-58` already set. The suffix rules are written as path
   patterns (`/data/**/*.csv.gz`) rather than directory excludes, so a `!` can re-include a file
   under them; `git check-ignore -v` on both paths now returns the negation line rather than
   `:102`, and the same command still returns `:102` for `us_shorts_daily_raw.csv.gz` and
   `crypto_intraday_15m_raw.csv.gz`.
2. **Both panels stay in `data/data_manifest.json`.** `scan()` selects by suffix and has no
   tracked/untracked filter, so they were never at risk of falling out; the point is that keeping
   them is **right**, not merely automatic. `cmd_verify()`
   (`scripts/build_data_manifest.py:162-183`) hashes what is on disk and never consults git, so a
   tracked panel gets a *stronger* check than an absent one — an absent panel is only `MISSING`,
   a present one is `CHANGED` or not. And `git_blobs()` (`:71-92`) now records a **live** blob id
   for these two rather than the historical id frozen at the repack, so the `git cat-file blob`
   recovery line in the manifest keeps pointing at the bytes actually committed.
   `tests/conftest.py:39-53` builds its panel-skip allowlist from manifest **basenames**; a tracked
   panel in that set is inert while the file is present, and is exactly the behaviour wanted if it
   ever is not.
3. **The manifest `note` was false for these two and is fixed at the source.**
   `build_data_manifest.py:130-133` asserted that every file below it had been *"dropped from the
   index on 2026-09-15 and recoverable from history"*. That now describes 116 of 118. The builder's
   string was rewritten and the manifest regenerated with `--build`; the JSON was not hand-edited,
   because it is generated and a hand-edit survives exactly until the next rebuild.

**What is deliberately NOT done, which is the more interesting half.** The three large panels stay
untracked and should not be re-proposed:

| panel | size |
|---|---|
| `data/fixtures/us_shorts_daily_raw.csv.gz` | 69.2 MB |
| `data/fixtures/etf_intraday_15m_raw.csv.gz` | 48.9 MB |
| `data/fixtures/index_extended_15m_raw.csv.gz` | 14.3 MB |

131 MB against this record's 6.9 MB: they would roughly double the index on their own, which is
D536's argument unchanged and needs no new one. **The reason worth recording is the one that also
kills the obvious compromise** — commit a slice.

## Rationale

**What D536 actually claimed, quoted.** `:12-14`:

> Every bulk panel under `data/` — `*.csv.gz`, `*.parquet`, `*.npz`, `*.zip` — is **gitignored and
> dropped from the index**. 115 files, 844 MB.

That is universal, and it is **by suffix**. There is no size criterion anywhere in D536 — not in the
Decision, not in the Rationale, not in the Consequences. And yet every number D536 argues from is a
size: 964 MB of `.git`, a 97.7 MB largest fixture, "14.7× the object D191 was measuring against",
"844 MB across 115 files, in a repository whose source is 21k lines". **The suffix was standing in
for size the whole time**, and it was a good proxy at the top of the distribution and a wrong one at
the bottom. `crypto_daily_2015_2025_raw.csv.gz` is 0.2 MB. It is 1/465th of the largest thing D536
measured, and **67 tracked `.json` artifacts under `data/` are larger than it** — the largest,
`d388_rare_event_levels.json` at 16.2 MB, by a factor of 75. Calling it a bulk panel is a category
error that the word *bulk* itself refuses.

**D536 already stated the qualitative test, at `:26`:**

> A file a record quotes is evidence, and evidence is not a panel.

That test is about **role**, and role is what the suffix was approximating. A 0.2 MB gzip that 47
tests read, and that no reviewer would hesitate to open, is not on the panel side of that line for
any reason other than the four characters at the end of its name.

**The cost D536 named, and how much of it this buys back.** `:67`:

> A fresh clone no longer runs the whole suite.

and `:74-76`:

> The claim "clone and reproduce every number" is now false and the README must stop making it. That
> is a real reduction in self-containment and it is the price of a repository a reviewer can clone
> at all.

This record does not dispute that price. It observes that **the price is not uniform across the
118**, and that 6.9 MB of it — 0.5% of the 1,465.5 MB the manifest accounts for — was buying
roughly half the remaining skips. That is the worst exchange rate in the set, and it is the only
part of D536 being narrowed.

**Why the three large panels are different, beyond size.** Their builders —
`scripts/fetch_short_universe.py`, `scripts/fetch_etf_intraday.py`, `scripts/fetch_index_extended.py`
— all read `data/raw/alphavantage/`, which is gitignored at `.gitignore:43` under D191's *cache the
raw, commit the derived*, and all three `raise SystemExit` without an Alpha Vantage key. **So a
slice's sidecars cannot be regenerated by anyone who does not already hold the cache**, and a
hand-cut slice would arrive with a `.meta.json` describing a panel it is not.

And the gates are written precisely to catch that. `tests/unit/test_index_extended_fixture.py:164`
demands `len(months) == 200` — at least one bar in **every one of 200 months**, plus
`frame["day"].min() == "2010-01-04"` — and its docstring says why it exists:

> every slice would hold the same recent window and the fixture would cover a few weeks pretending
> to be sixteen years

A slice built to satisfy that gate *is the sixteen years*, so there is no slice; and a gate relaxed
to admit a slice is a gate that has stopped testing the thing it was written for. **Cutting these
three down is not a smaller version of this decision. It is the defect that gate was installed
against, arriving with a decision record attached.** The two panels in this record need none of
that: they come off `yfinance` (their `.meta.json`: *"yfinance `Ticker.history(auto_adjust=False,
actions=True)`"*), keyless, so their provenance path is not gated on a cache that only this machine
holds — and they are committed **whole**, at the exact bytes the manifest hashes, not as a sample.

**Why not `git add -f`.** It works, it is one line, and it is invisible. An exception recorded only
in the index is a fact about this repository that no file in this repository states. The negation
carries its reason in the comment beside it, which is how `/temp/*` + `!/temp/README.md` has been
readable since it was written.

**Why not drop the two from the manifest now that they are tracked.** Because `--verify` would then
stop checking them, and they are the two panels a clone actually reads. The manifest's job is *a
panel has not moved under a published result* (D536 Consequences), and that job is independent of
who stores the bytes. Listing by suffix rather than by tracked status also means the manifest does
not develop a second, quieter definition of "panel" that drifts from `.gitignore`'s.

## Consequences

- `scripts/build_data_manifest.py --verify` reports **118 listed, 0 missing, 0 changed** with both
  panels present and now tracked; `--status` reports 118 on disk and 115 with a blob id (the three
  never-committed files — `d377_ensemble.npz`, `d382_scores.npz`, `fut_day1m.parquet` — are
  unchanged by this record).
- **This is not a new rule that small panels get committed.** It is two named exceptions with their
  sizes and their skip counts written down. The next panel that wants in has to make the same
  argument with its own numbers: what it costs the index, what it unblocks, and whether it can be
  committed whole. If that argument starts being made routinely, the right answer is to replace
  D536's suffix rule with a size rule in writing, not to accumulate negations.
- **Do not re-propose slicing `us_shorts_daily_raw`, `etf_intraday_15m_raw` or
  `index_extended_15m_raw`.** The reasons are in the Rationale above and they are structural, not
  budgetary: no regenerable sidecars without the gitignored vendor cache, and a coverage gate whose
  whole purpose is to reject a slice.
- The measured suite figure at the time of writing is **1,909 passed, 136 skipped**. The post-change
  figure is being re-measured on a fresh clone after all of this round's changes land, and is not
  stated here; a number asserted before it is measured is the failure this repository's reporting
  rules exist to prevent.
- `.git` is not expected to grow by 6.9 MB. Both blobs are already in the object database from
  before the repack (`f48a2709…` and `83a0a4ae…`, the ids the manifest still carries), so unless the
  bytes have changed since that commit, re-tracking adds trees and an index entry and no new object.
  That is an expectation and not a measurement — this lane runs no git command except
  `git check-ignore -v` — and nothing depends on it.
