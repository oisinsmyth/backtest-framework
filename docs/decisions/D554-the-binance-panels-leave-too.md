# D554 — The Binance price panels leave the index and the history, at a cost of 73 tests on every clone

*Filename shortened on creation ([D540](D540-local-config-a-clone-never-receives.md)). The H1 above
is the full title.*

**Status:** Result — **supersedes [D553](D553-the-two-panels-that-stay.md)**
**Date:** 2026-09-19
**Category:** Infrastructure
**Source:** The principal's decision, taken after D553 recorded the opposite.

**D553 said the two panels stay. They do not. The record is superseded rather than edited, because
what D553 built is the reason this was cheap.**

---

## What was removed

| path | size | disposition |
|---|---:|---|
| `data/fixtures/crypto_universe_2015_2025_raw.csv.gz` | 6.35 MB | purged from index **and history** |
| `data/fixtures/crypto_daily_2015_2025_raw.csv.gz` | 0.21 MB | purged from index **and history** |

A second `git filter-repo` pass, then a force-push. Removing them from the index alone would have
left them downloadable from history — the exact gap
[D549](D549-the-history-a-public-clone-receives.md) existed to close.

| | |
|---|---:|
| commits before / after | 1,464 / **1,464** (`--prune-empty never`) |
| clone size | 46.65 → **40.30 MiB** |
| commits still referencing either panel | **0** |
| a clone, Windows, 2026-09-19 | **2,055 passed, 126 skipped, 0 failed, 0 errors** |

The files remain on disk, untracked, exactly like the other 116 manifested panels, and
`data/raw/binance` holds 486 MB of raw klines, so the fixtures are rebuildable from source
independently of any backup. A fresh mirror was taken and verified at 1,464 commits before the
rewrite.

## What it cost, stated rather than absorbed

**73 of the 126 skips on a clone are this decision.** Those tests passed until today. The skip
count went 53 → 126 and the passing count 2,125 → 2,055.

That is the price of not redistributing the data, and it is the honest way to hold it: a skip
count that rises because a panel left is not the suite getting worse, it is the suite reporting
what a checkout actually carries.

## What D553 built, which is why this was a decision and not a demolition

D553 measured that `crypto_universe_2015_2025_raw` was **the only entry in
`_FIXTURE_SNAPSHOT_IDS` a clone receives**, so the absolute value of a snapshot id was verified on
CI by exactly one file — the guarantee [D551](D551-a-snapshot-id-that-depended-on-the-os.md) had
just fixed. It then pinned `test_a_snapshot_id_built_from_code_is_frozen`, a payload built in code
owing nothing to any data file.

**That is the only reason today's removal does not retire the gate that caught D551.** D553 was
written to justify keeping the panels and its lasting value is that it made removing them safe. A
record whose conclusion is reversed a day later can still be the reason the reversal was
affordable.

## I over-removed, and a clone said so before I did

The rewrite took **four** paths: the two price panels and their two `.meta.json` files. The
metadata should never have gone. It contains **no price data** — `symbols_requested`, `cohorts`,
`symbols_included`, `symbols_excluded`, `fetch_failures`, `status_by_symbol`, `selection_policy`,
and a `roster_provenance` note recording that the universe was hand-assembled from the 2017/18 and
2021 market-cap tables. That is **survivorship-bias evidence about how the universe was chosen**,
which is this project's own output and precisely what D549 kept when it kept the `*_events.json`
and `*_summary.json` files.

The framing that caused it was mine: the option put to the principal said the meta files *"describe
files that will not exist"*. They describe the **study**, not the panel.

**The clone caught it in the only way it could.** `tests/unit/test_breakout_universe.py:272` reads
the meta through a module-scoped fixture rather than through `requires_panel`, so its absence
raised `FileNotFoundError` instead of skipping: **two errors**, on tests that need the meta and not
the panel. Restored in `454b416`.

**And the local suite reported nothing.** It ran 2,180 passed, 1 skipped — unchanged — because the
files were restored to disk and `requires_panel` checks presence, not tracking. Taking that as
confirmation would have been the fourth instance this week of measuring the author's machine
instead of the repository (D550, D551, D552).

## The commit map, and a chaining error worth recording

`docs/prepublication-commit-map.tsv` had to survive a second rewrite. I assumed the new map was
v2 → v3 and composed it with the published v1 → v2 map. **It is not.** `git filter-repo` keeps its
metadata between runs, so the second run's map is keyed on the *original* pre-publication hashes:
it is already v1 → v3. My composition mapped `8cfdfa3` to a commit that no longer existed.

It was caught because the chaining script ended by resolving `NOTICE`'s hash against the live
history and printing the answer, which came back `False`. The map now published is the one
`filter-repo` produced, and `8cfdfa3 → 9a4a69ca` resolves.

## What else moved

Re-measured on the clone rather than adjusted by arithmetic: `docs/RUNNING.md`,
`docs/VERIFICATION.md`, `CONTRIBUTING.md` and `docs/TUTORIAL.md`.

**Two corrections fell out of the re-measurement**, neither of them about Binance:

1. *"The other four want a git identity"* was wrong by one. Three want a git identity; the fourth
   wants a gitignored trial registry, and says so.
2. **`docs/VERIFICATION.md:203` still promised blob-id recovery** — a fourth site
   [D552](D552-the-recovery-path-the-purge-removed.md) missed when it corrected the other three.
   Fixed here.

## What this does not settle

**The force-push rewrote about four hours of public history.** Anyone who cloned in that window
has a divergent copy and will need `git fetch --all && git reset --hard origin/main`. That is the
unavoidable cost of publishing before the licence question was fully settled, and the lesson is
the ordering: **decide what may be published before publishing, not after.**

**Whether the remaining small fixtures deserve the same look.**
`data/fixtures/xle_xop_daily_2015_2024*.csv` (1.1 MB) are ETF daily bars, still tracked, still
unexamined. D549 named them, D553 named them, and this record names them a third time without
resolving them.
