# D608 — The forward data recorder: raw bytes under a `fetched_at` name, a gap log nothing fills, and a host the record does not choose

**Status:** Committed
**Date:** 2026-09-21
**Category:** Data
**Source:** `docs/internal/User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md` §13A.3 "Track 2:
forward data recorder" and its §12 unit tests 31, 32 and 33; deposit decision D23 (`fetched_at`
used as availability time) and deposit question Q17 (recorder hosting). Governed by
[D191](D191-manifest-only-storage-for-large-archives.md) — cache the raw, commit the derived,
verify hashes loudly. Reuses [D585](D585-FIXTURE-sourced-us-economic-release-calendar-with-times.md)'s
fetcher shape and its sourced URLs, and [D586](D586-FIXTURE-cme-settlement-windows-with-effective-dates.md)'s
provenance assertion and settlement-window table. Sibling of
[D594](D594-the-frozen-protocol-layer.md), built the same day for the same deposit: D594 freezes
the PARAMETERS a forward test runs under, this record captures the DATA it will run on.
[D48](D48-no-false-affordances-enum-values-and.md) (raise loudly),
[D78](D78-property-test-conventions.md) as amended by
[D537](D537-derandomize-does-not-mean-deterministic.md),
[D550](D550-what-CI-found-in-its-first-run.md) (newline pinning), R8 and R16 in
[`../RULES.md`](../RULES.md).

## Decision

`src/backtest_framework/data/recorder.py` — new module, stdlib only, no numpy and no pandas.
`scripts/recorder.py` is its command line. `data/recorder/jobs.json` is the schedule and
`data/recorder/GAPS.md` the gap log. `data/raw/README.md` states the cache contract. Nothing else
in the repository is touched: no runner, no README, no `VERIFICATION.md`, no `CHANGELOG.md`, no
`data-available.md`, no `docs/decisions/README.md`, and `validation/__init__.py` stays empty.

**1. What it is for.** Track 2 of the ledger document starts **immediately** — before any stage is
tested — because several of its stages have no usable history and the only way to get history is
to begin having it. A recorder is therefore not infrastructure that supports a study; for six of
the deposit's stages it *is* the study's data acquisition, and every look-ahead defence downstream
rests on one field it writes: `fetched_at`.

**2. The API, with units.**

| | |
|---|---|
| `Recorder(root, *, clock=utc_now)` | `root` is `data/raw/recorder`; `clock` returns a tz-aware UTC instant and is injected everywhere |
| `.record(job, key, fetch, *, ext, published_at=None, source_url=None, method="fetched", parse=None) -> Record` | writes `<root>/<job>/<key>__<YYYYMMDDTHHMMSSZ>.<ext>` with `open(..., "xb")`; **never overwrites** |
| `.records(job, *, verify=True) -> list[Record]` | write order; re-hashes every file and raises on a mismatch or a missing file |
| `.jobs_on_disk() -> list[str]` · `.health_path` · `.append_health(line)` | |
| `availability_time(record) -> str` | **`fetched_at`, unconditionally** (deposit D23) |
| `Record` | frozen: `job, key, path, fetched_at, published_at, bytes, sha256, source_url, method, headers, parsed_path, parsed_rows`. `bytes` is a byte count; `fetched_at`/`published_at` are ISO-Z UTC, 20 characters; `sha256` is hex over the raw bytes |
| `Job(name, cadence, window_et, source_url, parser, status, weekday=None, window_basis="", frequency="", content="", ext="html", note="")` | `cadence` ∈ {daily, weekly, intraday}; `window_et` is `("HH:MM","HH:MM")` ET wall clock, **closed-closed**; `status` ∈ {ready, needs_source, needs_key}; `weekday` 0 = Monday |
| `.window_utc(day) -> (open, close)` | through IANA `America/New_York`, so DST needs no special case |
| `load_jobs(path) -> list[Job]` | raises on an unknown key, a duplicate name or a bad schema |
| `check_gaps(jobs, records_by_job, now_utc, *, since=None) -> list[Gap]` | every **closed** window with no record inside it, sorted `(date_et, job)` |
| `check_gaps_scope(jobs) -> dict` | `checked` / `not_checked_intraday` / `not_checked_not_ready`, named rather than implied |
| `Gap` | frozen: `job, cadence, date_et, window_et, window_close_utc, reason` |
| `gap_line(gap, logged_utc) -> str` · `append_gaps(path, gaps, *, now_utc=None) -> int` | seven columns; appends, never rewrites; de-duplicates on `(date_et, job)` against the file **and** the batch; returns lines added |
| `health_line(run) -> dict` · `append_health(path, line)` | `schema, start, end, attempted, ok, ok_jobs, failed, bytes, gaps, host`; `failed` carries the exception **class name** and 200 characters of detail |
| `http_get(url, *, timeout=120, attempts=4, limiter=None, opener=None, sleep=None)` | the calendar fetcher's ladder: 4 tries, backoff doubling from 3 s, **404 never retried** |
| `RateLimiter(min_interval, *, sleep, monotonic)` · `fetcher(url, **kw)` | a floor on the gap between request starts |

Errors, all subclasses of `RecorderError`: `OverwriteRefused`, `ChecksumMismatch`,
`MissingRawFile`, `ManifestError`, `JobConfigError`.

**3. THE BYTES ARE NEVER NORMALISED, AND THAT IS THE ONE PLACE THIS RECORD DEPARTS FROM D594.**
D594's `sha256_file` LF-pins text before hashing, because code is text and a checkout's newline
handling must not move a frozen identity. **A recorded response is not source.** It is what a
server sent. Normalising it would mean the bytes on disk no longer hash to the checksum stored
beside them, which is the one thing a cache's checksum exists to detect. So every digest here is
over the bytes exactly as received, every raw file is written with `open(..., "xb")`, and the
property test quantifies it over arbitrary binary. The two rules are not in tension: D594 hashes
*what we wrote*, D608 hashes *what arrived*.

**4. There is no `fill_gap`, and the absence is tested.** §13A.3: *"Gaps are **never** filled with
estimates."* A guarantee about code that does not exist can only be an assertion about the
namespace, so `FORBIDDEN_NAME_RE` matches `fill|backfill|impute|interpolate|estimate|synthes` and
the unit test, the golden and the `--selftest` each assert that exactly one public name matches it
— `FILL_IS_FORBIDDEN`, the string that says so.

**5. HOSTING IS NOT BUILT, AND THAT IS A DECISION.** Deposit Q17 asks *"which always-on machine or
server, with what backup?"*, and it is the principal's to answer. **This record installs no
scheduled task, service, cron entry or startup item**, and a unit test parses both files and
asserts neither imports `subprocess`, `os`, `winreg`, `multiprocessing`, `signal` or `ctypes`, so
neither *can* install one. `scripts/recorder.py --run` is **one pass** — the shape
`scripts/run_futures_acquisition.py:57` states as *"one pass; the harness re-invokes on exit"* —
and exits 0 **even when it finds gaps**, because a run that aborts on the first hole records
nothing about the rest. What the host has to supply, stated so the principal can price it:

1. invoke `uv run python scripts/recorder.py --run` on a timer, at whatever cadence the jobs need;
2. start that timer **on boot** — "survive reboots" is a property of the host, not of a process
   that exits in seconds;
3. keep `data/raw/recorder/` on a backed-up disk: it is a **cache and not disposable**, and some
   of what it will hold is free to fetch only briefly;
4. watch the last line of `data/raw/recorder/health.jsonl`. **A recorder that is not being invoked
   writes nothing at all**, and only something outside the recorder can tell that apart from a
   recorder with nothing to do. That is the whole reason the health line exists.

**6. `window_basis` is a required field, and it is the guard against a fabricated clock.** Most of
the seeded jobs are schedule pages that can be fetched at any hour; their window is an
**operational band this record chose**, not a published release time. A band that looked sourced
would eventually be quoted as one. So every job states where its two clock times came from, the
constructor raises on an empty basis, and exactly two jobs say `SOURCED`: `cftc_cot_weekly`
(15:30 ET Friday, from `scripts/fetch_cftc_cot.py:89`) and `mbo_around_windows` (13:30–14:30 ET,
the deposit's own "13:30 ET to W_end" with W_end resolved through D586's energy settlement window).

**7. The schedule, `data/recorder/jobs.json`: 16 jobs, 7 ready, 9 not.** No URL is invented; a
`ready` job's URL is copied from a file in this repository and its `note` cites the line.

| ready | URL copied from |
|---|---|
| `bls_cpi_schedule`, `bls_empsit_schedule` | `scripts/fetch_release_calendar.py:552-553` |
| `fed_fomc_calendar` | `scripts/fetch_release_calendar.py:562,593` |
| `eia_wpsr_schedule`, `eia_ngsr_schedule` | `scripts/fetch_release_calendar.py:99,101` |
| `cme_settlement_times` | the cached Confluence response's own `_links.self`, `data/raw/cme_settlement/confluence_457085528_*.json` |
| `cftc_cot_weekly` | `scripts/fetch_cftc_cot.py:137` + `DATASETS["disaggregated"]` (:146), composed as :358 composes it |

The deposit's ten are all present. **One of them is `ready`** (CFTC COT). **Two are `needs_key`** —
TAS summary and MBO around windows, both Databento and both gated on an unanswered question (Q3,
Q22). **Seven are `needs_source`**, because this repository holds no URL for them and none is
written down here to make the file look complete.

## What was reproduced exactly

* **`acquire()`'s filename and manifest shape** (`scripts/fetch_release_calendar.py:185-202`):
  `{key}__{YYYYMMDDTHHMMSSZ}.ext`, bytes written exactly as received, `{url, path, method,
  accessed_utc, bytes, sha256}` per entry, manifest saved after **every** record.
* **`_get`'s retry ladder** (:131): 4 attempts, backoff doubling from 3 s, 404 raised on the first
  try. Asserted with an injected opener: the 404 path makes exactly **1** call, and the recovering
  path sleeps exactly `[3.0, 6.0]`.
* **`RateLimiter`** (`scripts/run_futures_acquisition.py:130`) and the **atomic `.part` → replace**
  state write (:157), both unchanged.
* **The provenance assertion** of `scripts/settlement_windows.py:70-82` — `accessed_utc`
  `endswith("Z") and len == 20` — as `assert_iso_z`, applied to `fetched_at` and `published_at`.
* **Two independent SHA-256 calculators** agreed on every digest in
  `tests/golden/test_recorder_ledger.hand.txt`, which was written **before the module existed**:
  GNU `sha256sum` fed by `printf`, and .NET `System.Security.Cryptography.SHA256` over a literal
  `[byte[]]`. The empty-string anchor `e3b0c442…` is asserted first.
* **A live smoke of one ready job**, end to end: `--run --job bls_cpi_schedule` fetched
  `https://www.bls.gov/schedule/news_release/cpi.htm`, **55,572 bytes**, sha256
  `36b83ba3723ac4e1d96431214b22f22bb4240718dab1ec2b6289fef9e7829580`, at
  **2026-09-21T21:16:21Z**, into
  `data/raw/recorder/bls_cpi_schedule/bls_cpi_schedule__20260921T211621Z.html` with its manifest
  entry and one health line. The digest was re-computed by a separate `hashlib` call over the file
  on disk and matched. The file is **kept** — it is a cache, not a test artefact.

## Findings and disagreements, each recorded rather than smoothed over

**1. The spec asks for Parquet and this checkout cannot write Parquet.** §13A.3: *"Save the raw
response (HTML/CSV/JSON) unmodified, plus a parsed Parquet copy."* `pyarrow` is in neither the
project dependencies nor the dev group, and `.gitignore` excludes `/data/**/*.parquet` from the
index besides. **`record(parse=...)` writes the parsed copy as UTF-8 CSV** beside the raw file,
under the same stamp. The raw response — the part that cannot be recomputed — is unaffected by the
choice, and a columnar format is a later decision that costs a dependency. No seeded job has a
parser today, so no parsed copy exists yet.

**2. The deposit's "CME settlement" job is NOT D586's pages, and the repository has only D586's.**
The deposit's row is *"Settlement prices for all held contract months"*. D586's Confluence pages
are *"Daily Settlement Time Details"* — **when the settlement window is**, not what settled in it.
They are two different objects and the schedule carries both: `cme_settlement_times` is `ready`,
`cme_settlement_prices` is `needs_source`. Compounding it, **D586 records that `curl` to
`www.cmegroup.com` returns HTTP 403 from this machine** (*"This IP address is blocked due to
suspected web scraping activity"*), so even a known price URL would need the browser route. Two of
the deposit's `needs_source` rows — settlement prices and options OI — sit behind that same 403.

**3. A filename sort is not a time sort inside one second, and the golden caught it on its first
run.** The hand ledger was written claiming it was. `-` is 0x2D and `.` is 0x2E, so
`k__20260921T143000Z-1.html` sorts **ahead of** `k__20260921T143000Z.html`: the second record of a
second would read back first. Across seconds the name sort is correct, because the stamp is fixed
width and zero padded. `Recorder.records` therefore sorts on `(fetched_at, collision index, path)`
with the index extracted as a **number**, and the hand ledger carries the correction rather than a
deletion — the wrong version is what a reader would have assumed.

**4. `append_gaps` deduplicated against the file and not against its own batch, and a property
test found it.** `append_gaps(path, [g, g])` wrote two lines for one window. `check_gaps` cannot
emit a window twice, so no unit case would have reached it, but the function is public and the
invariant `GAPS.md` offers a reader — one line per `(date, job)` — must not depend on the caller.
Fixed, and pinned by a unit test that names the property test that found it.

**5. A record that arrived after its window closed does not satisfy the window.** The job *ran*
and there *is* a file, and the day is still a gap. The window is the observation; a file that
arrived an hour late is not that observation. The hand ledger's Case 3 is built around exactly this
row, because the natural implementation — "was there a record on that date?" — is wrong and looks
right.

**6. Gap detection covers `daily` and `weekly`, and says so out loud.** §13A.3's rule is written
for a job with one window a day (*"alert if any daily job misses its window"*). An intraday job's
own miss rate is a different statistic and this module does not invent one. `check_gaps_scope`
returns the three lists by name, because **a gap report that silently omits a job reads exactly
like a job with no gaps.**

**7. `availability_time` has no branch, deliberately.** It does not compare `fetched_at` with
`published_at`, does not take a maximum, and does not fall back when `published_at` is None. A rule
with a branch is a rule that can take the wrong branch, and the wrong branch here is a look-ahead.
The property test quantifies over a `published_at` up to 4,000 hours either side of the fetch,
including *after* it, and the answer never moves.

**8. `published_at` is never inferred.** Not from a `Date:` or `Last-Modified:` header, not from
the filename, not from the document text. A unit test records a response whose `last-modified`
header names a date and asserts `published_at is None`. Headers are kept in the manifest as
provenance, lowercased; reading one into `published_at` is the caller's explicit act.

**9. `data/raw/README.md` cannot be tracked under the current `.gitignore`, and this record does
not change `.gitignore`.** Line 21 is `/data/raw/`, which excludes the **directory**, so git never
descends into it and a `!/data/raw/README.md` negation alone would not work — it needs
`/data/raw/*` plus `!/data/raw/README.md`. The file is written and is correct on disk; **whether
it joins the index is the integrator's call**, and it is named in the handoff below.

**10. `health_line`'s `host` defaults to `platform.node()`** — a fact about one machine on one
evening. The golden deliberately pins the health line's *shape* and not its contents.

## Consequences

* **Track 2 can start.** Seven jobs are fetchable today with no key and no purchase, and one pass
  costs seconds. What it cannot do is start itself: item 5 above is the shortest possible list of
  what a host must supply, and until the principal answers Q17 the recorder records only when
  something invokes it.
* **Seven of the deposit's ten jobs are blocked on a URL and two on a purchase.** That is not a
  defect of this module; it is the state of the deposit's open questions (Q3, Q8, Q12, Q14, Q17,
  Q22) made visible in a file that refuses to paper over it. Adding a job later is a one-line
  edit to `jobs.json` plus a `note` citing where the URL came from.
* **Any forward test built on these files gets its availability rule for free**, and gets it
  conservatively. `availability_time` is the only door.
* **The gap log is evidence, not a to-do list.** A line in `GAPS.md` is a hole that stays a hole.
  A study reading a job with gaps must say so; nothing here will quietly make the series look
  continuous.

## Gates

`tests/unit/test_recorder.py` (**113**), `tests/golden/test_recorder_ledger.py` +
`.hand.txt` (**11**), `tests/property/test_recorder_property.py` (**9**) — 133 in all —
and `uv run python scripts/recorder.py --selftest`, which asserts the **good case first** (three
records, three files, two digests; a schedule with every window satisfied and zero gaps) and then
proves **ten** guards fire on a deliberate break: an existing path, a manifest whose sha does not
match the bytes, a malformed `published_at`, a job name that could escape its directory, `ready`
with no `source_url`, `weekly` with no weekday, a window that closes before it opens, an empty
`window_basis`, a `since` after now, and a `fetch()` returning `str`. `ruff check` and `mypy`
clean on the module. No strategy return is computed and no fixture row from 2024-01-01 on is read
for any return.

---

## For the integrator

**Proposed `docs/data-available.md` paragraph:**

> **`data/recorder/` — the forward data recorder's schedule and gap log (D608).**
> `jobs.json` declares 16 jobs for the settlement-flow ledger's Track 2 (§13A.3): **7 `ready`** —
> the BLS CPI and Employment Situation schedule pages, the Fed FOMC calendar, the EIA petroleum
> and gas schedule pages, CME's "Daily Settlement Time Details" Confluence page and the CFTC
> disaggregated COT resource, every URL copied from `scripts/fetch_release_calendar.py`,
> `scripts/fetch_cftc_cot.py` or a cached response's own `_links.self` — and **9 not**, being the
> deposit's own ten-job table minus COT: seven `needs_source` (no URL exists in this repository and
> none is invented) and two `needs_key` (Databento TAS and CME MBO, both paid, both gated on an
> open deposit question). Each job carries its ET window, a **`window_basis`** saying whether that
> clock was sourced or declared here, and the deposit's own frequency and content cells verbatim.
> `GAPS.md` is the append-only log of windows that closed without a record; **gaps are never filled
> with estimates and the module has no `fill_gap`.** The raw responses live under
> `data/raw/recorder/<job>/` (gitignored cache, byte-for-byte, `{key}__{fetched_at}.{ext}`, one
> `_manifest.json` per job with a sha256 per file, `health.jsonl` per run). `fetched_at` — the
> filename stamp — is the **availability time** for any forward test (deposit D23), never
> `published_at`. One pass: `uv run python scripts/recorder.py --run`; gap check only: `--check`.
> Nothing schedules it: hosting is deposit Q17 and the principal's decision.

**Proposed `CHANGELOG.md` bullet:**

> - **D608 — the forward data recorder** (`src/backtest_framework/data/recorder.py`,
>   `scripts/recorder.py`, `data/recorder/jobs.json`, `data/recorder/GAPS.md`,
>   `data/raw/README.md`): raw responses kept byte-for-byte under a `fetched_at` name that is never
>   overwritten, a sha256 per file verified loudly on read, `availability_time` returning
>   `fetched_at` unconditionally, DST-correct window gap detection appending to `GAPS.md` and
>   filling nothing, a per-run health line, and a 16-job schedule seeding the ledger doc's §13A.3
>   table with seven keyless URLs copied from this repository and nine jobs honestly marked
>   `needs_source` or `needs_key`. No scheduler is installed: hosting is deposit Q17. 133 tests;
>   deposit unit tests 31, 32 and 33 named in the test functions.

**Three things outside my allowlist:**

1. **`data/raw/README.md` is gitignored** by `.gitignore:21` (`/data/raw/`). To track it the rule
   must become `/data/raw/*` plus `!/data/raw/README.md`; I did not edit `.gitignore`.
2. `docs/data-available.md`, `CHANGELOG.md`, `docs/decisions/README.md` and the living documents'
   quoted test counts need the paragraph, the bullet, the register row and **+133** tests
   (113 unit, 11 golden, 9 property). One of the 113 **skips** when
   `docs/internal/User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md` is not on disk — it is the
   verbatim-quote comparison, and the deposit documents are a read-only source this record does
   not own. If the integrator commits the deposit, the skip count is unchanged; if not, the
   suite's skip count rises by one and that is the reason. **Two gates are red until that
   integration happens**, and both are the mechanism working rather than a defect:
   `test_readme_counts_are_current.py::test_the_counts_come_from_the_index_and_not_the_filesystem`
   (632 scripts in the index against 637 on disk — every parallel agent's new runner, including
   `scripts/recorder.py`, is untracked) and
   `test_quoted_counts_are_current.py::test_the_quoted_raise_count_is_the_non_bare_one`.
3. `data/raw/recorder/bls_cpi_schedule/` holds one real smoke fetch and is gitignored. **It is a
   cache and is not to be deleted** — `temp/` is the disposable directory, not this one.

**Full suite on this tree: 3,329 passed, 26 failed, 1 skipped, 6 deselected (10 min 37 s).**
**None of the 26 is this record's** — `tests/unit/test_recorder.py`,
`tests/golden/test_recorder_ledger.py` and `tests/property/test_recorder_property.py` are green,
together and alone. The 26 are the counts, index, register and running-page gates reacting to five
parallel agents' untracked in-flight files, which is the mechanism working; the one that names a
decision number is `test_cited_decisions_exist::test_every_cited_decision_number_has_a_record`,
dangling on **D604** at `src/backtest_framework/config/cost_stack.py:40`, which is another agent's.
`test_tracked_json_parses` and `test_nothing_outside_tests_is_collectable` fail in the full run and
**pass in isolation**, i.e. they caught a file mid-write.

**Two further failures seen on this tree that are NOT this record's** and touch no part of
`data.recorder`:

* `tests/golden/test_futures_costs_ledger.py::test_no_pre_existing_brick_key_row_moved` —
  `set(BRICK_KEYS) - set(BRICK_KEYS_BEFORE_D591)` is now `{"futures_round_trip",
  "futures_sqrt_impact"}` against the `{"futures_round_trip"}` D591 asserted. A **second** brick
  row has been added since D591 snapshotted the eight legacy rows, by a session concurrent with
  this one. D591's gate is doing exactly its job; the snapshot needs extending by whoever added
  the row. It **passed** when the full suite swept that file and **fails now**, which dates the
  edit to the intervening ten minutes — this is a live tree.
* `tests/property/test_hurdle_p_property.py::test_enforcing_p3_never_lengthens_the_account` —
  falsifying example `xs=[-2000.0, 0.0, -1000.0]` gives `life_with_p3 = 1.5` against
  `life_dd_only = 1.0`. Enforcing P3 **lengthened** the account on that series, which the property
  says cannot happen. Either D590's life computation or the property's statement of it is wrong,
  and D501's finding — that a same-day stop at the P3 level buys **zero** account life — says the
  question is worth resolving rather than re-seeding. **It did not reproduce in the full-suite run
  and does not reproduce on a re-run of its own file** — which is D537 exactly: `derandomize=True`
  fixes the seed and not the example set. The falsifying input is written down here because this
  record is now the only place it survives.
