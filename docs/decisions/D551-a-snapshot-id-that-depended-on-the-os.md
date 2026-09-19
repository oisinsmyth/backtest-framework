# D551 — The snapshot id, which is this project's provenance identifier, was a function of the operating system that computed it

*Filename shortened on creation ([D540](D540-local-config-a-clone-never-receives.md)). The H1 above
is the full title.*

**Status:** Result
**Date:** 2026-09-19
**Category:** Correctness
**Source:** The second failure of `.github/workflows/tests.yml`, on `ebe4ae2`
([D550](D550-what-CI-found-in-its-first-run.md) fixed the first).

**The same fixture froze to `51756f0d…` on Windows and `1bb6fe9c…` on Linux. A snapshot id is
logged with every trial and printed in results documents.**

---

## What failed

Run #3, **2m 19s** — faster than run #2's 3m 47s, which is what said it was a different fault:

```
test_committed_fixtures_still_freeze_to_their_original_snapshot_id[crypto_universe_2015_2025_raw]
E  AssertionError: assert '1bb6fe9c077d...c90fc8bf5f410' == '51756f0d66b0...88798da90776d'
```

The log was supplied by the principal; this session cannot read GitHub's logs.

## The cause, proved by reconstruction rather than inferred

`SnapshotStore.create` writes `bars.csv` and `events.json` into a staging directory and hashes
those bytes. `bars.csv` was never at risk — `_open_text` passes `newline=""` on all four of its
paths. **`save_events_json` did not:**

```python
Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
```

`Path.write_text` opens in text mode with default newline handling, so `json.dumps`'s newlines
became **CRLF on Windows and stayed LF on Linux**. For this fixture that is 131 newlines in a
2,616-byte file.

**Reconstructed locally before anything was changed**: take the payload this machine writes,
replace `\r\n` with `\n` in `events.json` alone, re-hash.

```
payload hash with LF events.json: 1bb6fe9c077d8b635bb7c4abb1b69bedf1139ca2d0dc4a74bd3c90fc8bf5f410
CI on Linux produced:             1bb6fe9c077d8b635bb7c4abb1b69bedf1139ca2d0dc4a74bd3c90fc8bf5f410
```

Byte for byte. Not a plausible cause — **the** cause.

**My first hypothesis was wrong and is recorded because it was cheap to check.** I expected
`csv.writer`'s `\r\n` terminator interacting with text-mode translation in `bars.csv`. Reading
`_open_text` killed it in one minute: `newline=""` is passed on every branch, including the
three-layer gzip stack. The defect was in the writer nobody had thought about, not the one with
the known hazard.

## The fix: CRLF, deliberately, and not LF

```python
with open(path, "w", encoding="utf-8", newline="\r\n") as f:
    f.write(json.dumps(payload, indent=2, sort_keys=True))
```

`newline="\r\n"` translates on **every** platform, so the bytes are now a function of the content
alone.

**LF would have been tidier and would have renumbered every snapshot id this project has
published.** The ids are cited in [D70](D70-committed-csv-fixture-as-frozen-snapshot.md),
[D72](D72-content-addressed-snapshot-store.md),
[D143](D143-sanity-gate-overridden-for-crypto-cross-section.md),
[D193](D193-the-binance-fetcher-and-the-fixture-schema-extension.md) and
[D541](D541-clean-returns-bars-without-their-volumes.md), printed in results documents, and
logged with every trial ever run. CRLF is the convention they were frozen under.

So this is the programme's standing rule applied to an identity rather than a number: **fix the
defect, do not move a published value.** All three pinned ids still pass unchanged, and now pass
on Linux too.

`save_fixture_csv`'s own docstring had already warned that a change here *"would silently
renumber every snapshot id in the project"*. It was guarding the CSV writer. The JSON writer
beside it had no such comment and no such care.

## The gate, and what it cannot do

`test_the_events_file_is_byte_identical_on_every_platform` pins the bytes: CRLF present, zero bare
LF.

**It cannot fail on Windows, and the docstring says so.** Before the fix, Windows already produced
CRLF by translation, so the assertion would have passed for the wrong reason. Its failing case is a
Linux runner — a gate whose entire value is in CI, on a repository whose front page argues that a
suite which only runs on the author's laptop is convention.

## A correction to D550

D550 reports *"Measured on a clone: **2,125 passed, 53 skipped**"* and scores D549's P3 as holding
exactly. **That was a Windows clone.** The Linux runner reports **2,124 passed, 54 skipped** — one
test that runs here skips there:

```
SKIPPED tests/unit/test_us_shorts_fixture.py:583: no key available on this machine to scan for
```

So P3 held against a clone on the author's operating system and is off by one against the machine
it was actually a prediction about. The prediction said *"CI's first ever run"*; I verified it
against the nearest thing I could run and reported the two as the same.

**And the skip count in three documents is platform-dependent.** `README.md`, `docs/RUNNING.md`
and `docs/VERIFICATION.md` all say 53, measured on 2026-09-17 on a Windows clone. On Linux it is
54. `docs/RUNNING.md` now names the platform, because it is the page that owns clone facts.

## What this does not settle

**`snapshot_store.py:96` has the same shape.** `meta.json` is written with `Path.write_text` and
is therefore CRLF here and LF there. It is written *after* `_hash_payload` and is explicitly not
part of the identity (D72), so nothing depends on its bytes — but it is the same defect in a place
where it happens not to matter, and that is worth knowing rather than discovering.

**Whether any other tracked artifact's identity is platform-dependent.** Two were found in two
days by one CI runner: an encoding ratchet that counted a worktree, and a content hash that
counted an operating system. Both were invisible to every local run this project has ever done.
There is no reason to believe the set is now empty; there is now a machine that will say so.
