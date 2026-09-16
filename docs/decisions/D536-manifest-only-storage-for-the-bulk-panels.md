# D536 — The bulk panels leave the index; the committed artifact is a manifest carrying sha256 **and the git blob id**

**Status:** Committed · **AMENDED 2026-09-16 by
[D538](D538-two-small-panels-return-to-the-index.md)**
**Date:** 2026-09-15
**Category:** Data layer
**Source:** Portfolio repack session. Extends [D191](D191-manifest-only-storage-for-large-archives.md);
amends the *implementation* of [D24](D24-immutable-data-snapshots-fetch-once-freeze.md) and
[D70](D70-committed-csv-fixture-as-frozen-snapshot.md), not their requirement.

> **Amendment, 2026-09-16 (D538).** The sentence below — *"Every bulk panel under `data/` —
> `*.csv.gz`, `*.parquet`, `*.npz`, `*.zip` — is **gitignored and dropped from the index**"* — **is
> narrowed: it is now true of 116 of the 118, not of all of them.** Two are tracked again by an
> explicit `!` negation inside this record's own `.gitignore` block:
> `data/fixtures/crypto_daily_2015_2025_raw.csv.gz` (0.2 MB) and
> `data/fixtures/crypto_universe_2015_2025_raw.csv.gz` (6.7 MB). 6.9 MB, under 5% of the index,
> and between them they unblock 73 of a fresh clone's 136 skips. The reasoning is that this
> record's rule is **by suffix while every number it argues from is a size**, so the suffix was a
> proxy that misfired at the bottom of the distribution; D538 has the full argument, including why
> the three large panels (`us_shorts_daily_raw`, `etf_intraday_15m_raw`, `index_extended_15m_raw`)
> are deliberately left untracked and must not be re-proposed as slices.
>
> **Everything else here stands**, including the manifest as the committed artifact, the
> `git_blob` field as its load-bearing half, history not being rewritten, and the rule's
> application to the other 116. Both re-tracked panels **stay listed in
> `data/data_manifest.json`**: `--verify` hashes the disk and never consults git, so a tracked
> panel gets a stronger check than an absent one, not a redundant one. The builder's `note` field,
> which asserted the "dropped from the index" claim of every entry, was corrected accordingly.
>
> **Two test counts below are also stale** — *"~64 of their tests ERROR rather than skip"* at `:68`
> and *"a clone runs 1,768 of 1,832 tests"* at `:72`. Both predate the guard work that was named
> there as the immediate follow-up. The measured figure today is **1,909 passed and 136 skipped**;
> the post-D538 figure is being re-measured on a fresh clone and is deliberately not stated here.
>
> The original text is left unedited below, per the amend-in-writing convention.

## Decision

Every bulk panel under `data/` — `*.csv.gz`, `*.parquet`, `*.npz`, `*.zip` — is **gitignored and
dropped from the index**. 115 files, 844 MB. The files stay on disk; nothing is deleted and
**history is not rewritten**.

What is committed in their place:

1. **`data/data_manifest.json`** — one entry per panel: `path`, `bytes`, `sha256`, the **`git_blob`
   id the file carried at the last commit that tracked it**, and which `.meta.json` / `_events.json`
   sidecars sit beside it. 118 panels, 1,465.5 MB accounted for.
2. **`scripts/build_data_manifest.py`** — `--build`, `--verify` (re-hashes what is on disk and exits
   non-zero on any change), `--status`.

**What stays tracked, deliberately:** every plain `.csv` (the largest under `data/` is 0.6 MB),
every `.json` artifact a decision record quotes, and the `.meta.json` / `_events.json` provenance
sidecars beside each panel. A file a record quotes is evidence, and evidence is not a panel.

## Rationale

**The numbers that force the question**, in the same shape D191 used — because this is D191's
own argument arriving one level up, at the derived fixtures D191 explicitly preserved:

| | D191 (2026-08-22) | D536 (today) |
|---|---|---|
| The whole `.git` directory | 17.3 MB | **964 MB** |
| Largest committed fixture | 6.65 MB | **97.7 MB** |
| Tracked bytes under `data/` | — | **962.6 MB → 118.5 MB** |
| Whole index | — | **~990 MB → 147.4 MB** |
| What is committed instead | the provider's SHA256 manifest + fetch script | `data_manifest.json` (sha256 **+ git blob id**) + its builder |

D191 wrote: *"There is no version of 'commit the fixture' that survives this."* It said so about a
6.34 GB archive against a 6.65 MB largest fixture. The largest fixture is now **97.7 MB** — 14.7×
the object D191 was measuring against — and the repository it lives in has grown **55×**. The
derived fixture was the small thing that made D191's compromise work. It is no longer small.

**Why this keeps the property D70/D24 bought, rather than spending it.** What those decisions
actually purchase is: *the data behind a result cannot change without a visible diff.* Committing
bytes is one way to get it. Here the diff moves into `data_manifest.json`, and that is an
improvement in the only dimension that matters — **whether a reviewer sees it**. A changed panel
was previously a 46 MB gzip blob diff that no human opens; it is now one line of JSON.
`--verify` makes the check a command rather than an act of faith.

**Why the git blob id is the load-bearing field.** D191's manifest could point at a provider's
published hash because a provider existed. These panels are *ours* — derived, and in several cases
built from a vendor archive that is free to re-fetch only until ~2026-10-11. So the manifest points
at the place the bytes still are:

    git cat-file blob <git_blob> > <path>

Verified on `data/d291_null_surface.npz` → type `blob`, 384,215 bytes, exactly as recorded. **This
is why history is not rewritten, and the two decisions are one decision.** A `filter-repo` pass
would shrink the clone and simultaneously make every `git_blob` in this manifest a dangling
reference — it would convert a recoverable repack into a deletion. Three panels
(`d377_ensemble.npz`, `d382_scores.npz`, `fut_day1m.parquet`) were never committed and correctly
carry no blob id; the builder refuses to overwrite a known id with a blank.

**What this costs, stated plainly.** A fresh clone no longer runs the whole suite. 18 test files
read a committed panel, and **as of this commit ~64 of their tests ERROR rather than skip** —
unguarded module-scoped fixtures calling `load_fixture_csv_with_volumes(FIXTURE)` on a file that is
no longer there. Collection still succeeds; nothing reads a panel at import. Guarding those nine
call sites is the immediate follow-up and is a precondition for any CI job, after which a clone
runs 1,768 of 1,832 tests — including all 91 golden masters, offline, the golden tier in 0.58s.

The claim "clone and reproduce every number" is now false and the README must stop making it. That
is a real reduction in self-containment and it is the price of a repository a reviewer can clone at
all.

**Why not the alternatives.**

*Leave it.* A 964 MB `.git` for 21k lines of source. The data is 98.8% of the repository by weight
and 0% of what a reader comes for.

*Git LFS.* Rejected for the same reason D191 rejected it, plus a new one: a reviewer cloning
without LFS gets pointer files and a suite that fails in a way that looks like the project's fault.

*Rewrite history.* Shrinks the clone, which none of this does — and destroys the recovery path
above, breaks every hash in an append-only record, and is the one thing this project's norms
forbid. The clone-size problem gets a different answer (a curated public repository); it is not
this decision's to solve.

## Consequences

- `scripts/build_data_manifest.py --verify` is now the check that a panel has not moved under a
  published result. It belongs in any future CI job that has the panels available.
- Four JSON artifacts over 5 MB remain tracked — `d388_rare_event_levels.json` (15.5 MB),
  `d387_level_reversion.json` (15.4), `us_shorts_daily_raw_deals.json` (11.9),
  `us_shorts_daily_holdout_deals.json` (5.7). They are evidence-shaped, so they were left alone
  **by decision rather than by omission**; revisiting them is a separate call.
- `.git` remains 964 MB. Ignoring a tracked file does not remove its blobs, so **clone size is
  unchanged by this record** and no claim to the contrary should be made.
- The two `.gitignore` entries D191's successors added by hand (`d377_ensemble.npz`,
  `d382_scores.npz`, each with its own justification comment) are now covered by the general rule.
  Their comments are left in place: they record why those two were caught first.
