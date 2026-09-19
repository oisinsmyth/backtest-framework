# D549 — The history a public clone receives, and the seam that rewriting it leaves in 760 records

*Filename shortened on creation ([D540](D540-local-config-a-clone-never-receives.md)). The H1 above
is the full title.*

**Status:** Result (the act and its measurements; there was no separable pre-registration because
the decision, the criterion and the verification all belong to one irreversible operation)
**Date:** 2026-09-19
**Category:** Infrastructure
**Source:** The principal's decision to publish this repository publicly.

**962.67 MiB → 46.57 MiB on a clone. All 1,458 commits preserved. The working tree is
byte-identical: the same tree hash before and after.**

---

## Why history had to be rewritten, in the repository's own words

[`docs/data-available.md:285-288`](../data-available.md) already drew the line, eight days before
there was a remote to draw it for:

> `cftc_cot_raw` … US government public domain, so **unlike every CME product here it may live in
> the repo**.

The current tree honoured that — [D536](D536-manifest-only-storage-for-the-bulk-panels.md)
manifested the bulk panels out of the index. **Git history does not care what the index says.** The
panels were still in it, and a public repository publishes its history:

| blob | size | source | entered |
|---|---:|---|---|
| `fut_day5m.parquet` | 97.7 MB | Databento `GLBX.MDP3` | 2026-09-12 |
| `us_shorts_daily_raw.csv.gz` | 66.0 MB | Alpha Vantage | 2026-08-28 |
| `es_minute_bars.parquet` | 54.9 MB | Databento `GLBX.MDP3` | 2026-09-12 |
| `etf_intraday_15m_raw.csv.gz` | 46.7 MB | Alpha Vantage | 2026-08-27 |
| `fut_breadth_hourly.csv.gz` | 33.2 MB | Databento `GLBX.MDP3` | 2026-09-13 |

`NOTICE` is thorough about third-party **prose** — 4,061 quoted passages, measured and classified
into four licence classes — and says nothing about market data, because until today the question
could not arise.

## The criterion was the manifest, not a size threshold

A `--strip-blobs-bigger-than 20M` rule would have been a **second line, differently drawn**, that
happens to overlap the first. D536 already decided which panels do not belong in a checkout and
[D538](D538-two-small-panels-return-to-the-index.md) brought two back. That decision is the
criterion, and `data/data_manifest.json` is its written form:

| | |
|---|---:|
| manifest panels | **118** |
| currently tracked, therefore kept | **2** |
| never committed, so nothing to purge | **3** |
| **purged from history** | **113** |

**And nothing large fell outside it.** A census of every blob over 3 MB that the manifest does not
account for returned **zero**. The manifest is complete, which is the strongest thing that can be
said for a criterion: it needed no exceptions.

## What was verified, and in what order

| check | result |
|---|---|
| tree hash before | `7e4ad814e467bf14a0ea7f52a6ea8ef153647f89` |
| tree hash after | **identical** |
| commits before / after | 1,458 / **1,458** (`--prune-empty never`) |
| largest blob remaining | 14.93 MB (`data/d388_rare_event_levels.json`, this project's own output) |
| a real clone | **46.57 MiB**, 1,458 commits, no manifest panel present |
| full suite after | **2,178 passed, 1 skipped** — unchanged |

**A full mirror backup was taken first** and verified at 1,458 commits before a single object was
rewritten.

**The size was measured from a clone, not from `.git`.** Locally the pack is still 697 MiB, because
unreachable copies of the purged blobs are pinned by the reflog of a linked worktree
(`.claude/worktrees/signal-hunt-part2`). They are unreachable from any ref, so a push never sends
them and a clone never receives them — which the clone measurement is what proves. Deleting that
worktree is the principal's call; it is someone's working state, not garbage.

**`git filter-repo` ends with a `reset --hard`, which restored six files the principal had deleted
in the worktree and not yet staged.** The deletions were recorded before the rewrite and re-applied
after. That is the second time in this programme an operation has silently reached into the
principal's in-flight state, and it is the reason the list was written down first.

---

## The seam: 760 records cite hashes that no longer exist

Every commit hash quoted in this repository was quoted from the pre-publication history. `NOTICE`
opens its measurement with *"Measured at `8cfdfa3` on 2026-09-17"*; D546 cites `8c2b0a5`, D547
cites `d204284` and `bcf5c55`, D548 cites `6675ab2` and `08e98e6`. **None of them resolves in the
published repository.**

**They are not rewritten, and the reason is not laziness.** Rewriting a citation changes the
content of the record that carries it, which changes that record's own commit hash, which is
itself cited elsewhere. The fixed point does not exist. Any pass that appears to solve it has
simply stopped before the contradiction.

So the mapping is published instead: **[`docs/prepublication-commit-map.tsv`](../prepublication-commit-map.tsv)**,
1,458 rows of `old<TAB>new`, exactly as `git filter-repo` emitted it.
`8cfdfa31003f0508566c73e7274c67f879d31da9 → 27deba540f7dc92eab41e6d0d0eb6f9b078313a0`. A reader who
finds a hash in a record and cannot resolve it looks it up there.

**This is a seam and it is left visible.** The alternative was to publish a repository whose
records cite hashes that silently fail, which is the failure mode this project spends most of its
effort on.

---

## What is still published that came from a vendor

Named here rather than left for a reader to notice, because the licence question does not stop
being real once the big files are gone:

- **`data/fixtures/crypto_universe_2015_2025_raw.csv.gz`** (6.35 MB) and
  **`crypto_daily_2015_2025_raw.csv.gz`** (0.21 MB) — Binance. These are the two panels D538
  deliberately returned to the index, so they are a standing decision rather than an oversight.
- **`data/fixtures/xle_xop_daily_2015_2024*.csv`** (1.1 MB total) — ETF daily bars.
- The `*_events.json` and `*_deals.json` fixtures — derived event lists, not price series.

**These are the principal's to weigh.** They are small, they are what several tests read, and
removing them changes the current tree rather than only its history — a different and larger
operation than this one.

## The CI workflow was carrying stale numbers, and nothing was checking

`.github/workflows/tests.yml` quoted **2,163 passed** (now 2,178), **313 tracked runners** (now 399
of 601) and **1,180 call sites** (the ratchet counts 1,126). It is a `.yml`, and
`tests/unit/test_quoted_counts_are_current.py` sweeps `.md`, so nothing ever looked — the same gap
[D548](D548-RESULT-none-of-the-figures-had-a-gate.md) measured on `docs/RUNNING.md`, in the file
that is about to run for the first time.

Two of the three are now replaced by a pointer to the file that **owns** the number rather than a
second copy of it; the third is re-measured and dated.

## Predictions

| # | Prediction | Confidence |
|---|---|---|
| **P1** | A clone of the published repository is **under 60 MiB** and contains no path listed in `data/data_manifest.json`. | High |
| **P2** | The push is accepted with **no file-size rejection** — the largest object is 14.93 MB against GitHub's 100 MiB limit — and **no secret-scanning block**; the only credential-shaped string in the tree is the literal `"ZZTOPSECRETKEY99"` in a test fixture. | High |
| **P3** | CI's **first ever run** reports roughly **2,125 passed, 53 skipped** — this machine's 2,178 less the 53 that want a manifested panel — and passes. The two figures are committed, so this is arithmetic rather than a guess. | Medium |
| **P4** | No published number changes. The tree is byte-identical to the pre-rewrite tree. | High |

**P3 is the one worth being wrong about.** The 53 was measured on 2026-09-17 and tests have been
added since; if the skip count has moved, the README, `docs/RUNNING.md` and
`docs/VERIFICATION.md` all quote it and all three are wrong together. **That is the first thing
this repository will have learned from a machine that has never seen it** — which is what
`tests.yml`'s own opening comment says the workflow is for.

## What this record does not settle

**Whether the purge was sufficient for the licences involved.** It removes every panel the
repository's own data document says may not live here. It does not constitute advice about
Databento's or Alpha Vantage's terms, and the residual list above is deliberately explicit so the
principal can weigh it.

**Whether the backup should be kept.** `_backtest-framework-prepublish-backup.git` holds the
complete pre-rewrite history including every vendor panel. It is the only copy of that history and
it must never be pushed anywhere.

**Whether `refs/heads/worktree-signal-hunt-part2` should be published.** It is a research branch
from a prior session, rewritten along with everything else. It will be pushed only if branches are
pushed explicitly; `git push -u origin main` sends `main` alone.

---

## ADDENDUM 2026-09-19 — two figures in the CI section above are wrong

The section *"The CI workflow was carrying stale numbers"* gives **399 of 601** tracked runners
and says the ratchet counts **1,126**. Both were read off the author's worktree, which is missing
two scripts the principal has deleted without staging. The index holds **401 of 603** and
**1,128**.

Corrected in the workflow and in `docs/VERIFICATION.md`; the cause, the fix and the full scoring
are in [D550](D550-what-CI-found-in-its-first-run.md). That this record's own numbers came from a
worktree, in a record whose subject is *the history a clone receives*, is the joke the first CI
run made at its author's expense.

---

## ADDENDUM 2026-09-19 (second) — what else pointed at the objects this purge removed

This record verified the tree hash, the commit count, the clone size and the absence of every
purged path. **It did not ask what else referenced the blobs it was deleting.**
`data/data_manifest.json` carries a git blob id for 115 panels, and three documents described
those ids as what makes a skipped test recoverable. After the purge, 113 of them dangle.

The purge was right — those blobs are the vendor data — and the recovery path could not have
survived it. Both facts were settled by this record, which noticed neither.
[D552](D552-the-recovery-path-the-purge-removed.md) has the measurement and the corrections.
