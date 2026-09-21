# `data/raw/` — the raw cache. Gitignored, and **not disposable**.

*Governed by [D191](../../docs/decisions/D191-manifest-only-storage-for-large-archives.md) —
**cache the raw, commit the derived, and verify hashes loudly.** Written by
[D608](../../docs/decisions/D608-the-forward-data-recorder.md).*

**What is here:** responses exactly as they arrived — HTML, JSON, CSV, PDF, `.dbn` — under a
`fetched_at` name, beside a `_manifest.json` carrying each file's URL, access time, byte count and
sha256. Nothing here is edited after it lands; a re-fetch is a **new file**, never a rewrite.

**Gitignored (`/data/raw/` in `.gitignore`), and that is not the same as disposable.** `temp/` is
the disposable directory, by its own contract: *"if deleting a file would cost something, it does
not belong here"*. These bytes cost something. Some are free to re-fetch only for a window — 111 GB
of CME futures was moved out of `temp/` for exactly that reason, free until ~2026-10-11 and $7,719
after — and some can never be re-fetched at all, because a live page is a **snapshot of today** and
the version it replaced is gone. Deleting a directory here costs money, hours, or a fact.

**What is committed instead:** the derived fixture, its `.meta.json`, and the sha256 in
`data/data_manifest.json`. A record that quotes a number is evidence and belongs in `data/`; the
bytes it was computed from belong here.

**The recorder's layout** (`data/raw/recorder/`, D608, ledger doc §13A.3):

    recorder/health.jsonl                     one JSON line per run: start, end, attempted, ok,
                                              failed (exception class names), bytes, gaps, host
    recorder/<job>/_manifest.json             every record for that job, in write order
    recorder/<job>/<key>__<stamp>.<ext>       the raw response, byte for byte
    recorder/<job>/<key>__<stamp>.parsed.csv  the derived copy, when a parser was supplied

`<stamp>` is `YYYYMMDDTHHMMSSZ` and **is** the record's `fetched_at` — which is the availability
time for any forward test (deposit decision D23). A second record inside one second appends `-1`,
`-2` to the stamp; nothing is ever overwritten. `uv run python scripts/recorder.py --check` reports
windows that closed empty into `data/recorder/GAPS.md`, and **no gap is ever filled with an
estimate.**

**If a file here goes missing**, `Recorder.records()` raises rather than skipping it, and a file
whose bytes no longer match its manifest checksum raises too. Re-fetching is a new record with a
new `fetched_at`; it is not a repair of the old one.
