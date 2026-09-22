# D612 — The attention layer: a hashed query file, two parsers, four point-in-time guards, and an erratum on the deposit's hourly Wikipedia row

**Status:** Committed
**Date:** 2026-09-22
**Category:** Data
**Source:** `docs/internal/User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md` §3.3c (its lines
105–116, "News and attention data") and §P3.7 (its lines 249–267, "News and virality detector"),
with its §12 unit tests 21, 22, 23, 24 and 25 (its lines 727–731) and its `trials.csv` column
list (its line 700). The deposit is an **untracked, read-only** source: it is quoted verbatim with
line numbers here and is neither staged, copied nor edited. **Deposit** question Q12 (a lawful
timestamped social archive) and **deposit decision D15** (only sources with reproducible
historical timestamps) bound what is built — the deposit numbers its own decisions and questions,
and its D15 is not this repository's
[D15](D15-fx-as-plumbing-not-strategy-venue.md). Built on [D608](D608-the-forward-data-recorder.md)'s `Recorder` — every network
read in this record goes through it — and on [D594](D594-the-frozen-protocol-layer.md)'s
newline-pinned hashing. Governed by [D191](D191-manifest-only-storage-for-large-archives.md)
(cache the raw, commit the derived, verify hashes loudly),
[D48](D48-no-false-affordances-enum-values-and.md) (raise loudly),
[D78](D78-property-test-conventions.md) as amended by
[D537](D537-derandomize-does-not-mean-deterministic.md),
[D550](D550-what-CI-found-in-its-first-run.md) (newline pinning), and R6 and R9 in
[`../RULES.md`](../RULES.md).

## Decision

Six new files and one edited line of schedule:

| | |
|---|---|
| `data/attention/QUERIES.md` | **written first, before any feature code existed** — the deposit's line 116 says so, and the order is recorded here because it is the only part of that rule a reader cannot verify afterwards |
| `data/attention/QUERIES.sha256` | its LF-pinned digest; `load_queries` raises `QueriesTampered` when the two disagree |
| `data/attention/README.md` | the directory contract and the erratum below |
| `src/backtest_framework/data/attention.py` | the loader, the two parsers, the four point-in-time guards, the four detector features, and the `trials.csv` row shape. **No writer of any kind** |
| `scripts/fetch_attention.py` | `--wiki-daily`, `--wiki-hourly-dump`, `--gdelt-files`, `--gdelt-doc`, `--sample`, `--gates`, `--selftest` |
| `data/fixtures/attention_sample.csv.gz` + `.meta.json` | a bounded two-day sample, gitignored by suffix, meta committed |
| `data/recorder/jobs.json` | the `attention` job flipped `needs_source` → `ready`; every other job byte-identical |

Tests: `tests/unit/test_attention.py` (40), `tests/golden/test_attention_ledger.py` (7) with its
`.hand.txt`, `tests/property/test_attention_property.py` (7). **Ledger unit tests 21, 22, 23, 24
and 25 are claimed** — all five stood at `missing` in `data/deposit_test_map.json` before this
record.

**No strategy return is computed, no signal is scored, and no fixture row dated 2024-01-01 or
later is read by anything here.** The sample week is 2019, in-sample by five years.

---

## 1. What the deposit asks for, quoted

§3.3c, its line 107 and the table at its lines 109–114:

> Only sources with **reproducible historical timestamps** are eligible for the primary model
> (decision D15):
>
> | Source | Granularity | Use |
> | GDELT (global news events and tone) | 15 min, from 2015 | Primary: news volume, tone, headline bursts |
> | Wikimedia hourly pageviews | Hourly, from 2015 | Primary: public attention |
> | Reddit / StockTwits archives | Per post | **Optional:** only if a timestamped archive … (Q12) |
> | Google Trends | Varies | **Excluded** from modelling … Qualitative checks only |

its line 116:

> Query definitions (keyword lists, article titles, tickers) are fixed in
> `data/attention/QUERIES.md` **before** any feature is computed, and not changed afterwards
> without a doc edit.

and §P3.7's lines 251–252, 255, 262 and 267:

> - `news_n(τ)`: GDELT article count matching the fixed query in the last 60 min. `news_tone(τ)`:
>   mean tone of those articles.
> - `wiki_n(h)`: pageviews summed over the fixed article list in the last completed hour.
>
> **Normalisation:** each series is converted to a z-score against the same hour-of-day and
> day-of-week over the trailing 60 days (prior data only) …
>
> | `att_accel` | Change in `att_level` over the last 3 hours vs the prior 3 hours | …
>
> **Point-in-time rules:** only data published before τ is used. Hourly pageviews enter only after
> the hour completes plus a 15-min publication buffer. GDELT enters with its publication
> timestamp, not the event time.

---

## 2. THE ERRATUM: the deposit's line 112 is wrong as written

> | Wikimedia hourly pageviews | Hourly, from 2015 | Primary: public attention |

**The Wikimedia REST per-article endpoint does not serve hourly data, and never has.** Probed
2026-09-22 from this machine:

    GET .../per-article/en.wikipedia/all-access/user/Natural_gas/hourly/2023010100/2023010223
      -> HTTP 400  {"detail":"granularity should be equal to one of the allowed values:
                               [daily, monthly]"}

    GET .../per-article/en.wikipedia/all-access/user/Natural_gas/daily/2019110400/2019111000
      -> HTTP 200, items[].views

**The deposit is not edited.** It is an untracked read-only source here, and the erratum is
recorded rather than applied. What exists instead:

| route | granularity | shape | cost |
|---|---|---|---|
| REST per-article | **daily** | one small JSON per article per span | free, instant |
| `dumps.wikimedia.org/other/pageviews/…` | **hourly** | one file per hour, **every project and every article on earth** | 47–66 MB gzipped an hour, ~4× decompressed |
| REST aggregate `…/aggregate/en.wikipedia/all-access/user/hourly/…` | hourly | project totals only | a denominator, not a series |

**So the deposit's hourly `wiki_n` is reachable, and its price is the whole encyclopedia.** For
the 2016–2023 span the deposit's §2 names, the hourly dumps are **≈ 2.5 TB over 70,128 files**,
and GDELT's GKG at 15 minutes is **≈ 1.64 TB over 280,320 files**. Nothing here launches a
backfill; `--sample` fetches two days.

**The alternative, left to the principal and not chosen here.** A **daily** `wiki_n` off the REST
route costs one small JSON per article and is instant. It is not a smaller version of the hourly
series, it is a different one:

1. `att_accel` is defined at line 262 over **three-hour** windows. On a daily `wiki_n` there is
   one `z_wiki` a day, so either `att_accel` is computed from `z_news` alone — which makes
   `att_level`'s two components disagree about what "now" means — or the whole feature moves to a
   daily clock and the detector stops being intraday.
2. **Unit test 22 becomes void as written.** *"an hourly pageview for 13:00–14:00 is unavailable
   at τ = 14:10 and available at τ = 14:15"* has no daily reading; the daily analogue is a
   next-day publication lag that the deposit does not state, and D612 does not invent it.

This record builds the **hourly** route because that is what the deposit specifies, and states the
daily alternative so that the choice is the principal's rather than a default.

---

## 3. `QUERIES.md`, and the trap three of its candidates walk into

**Written before `attention.py` existed.** Every candidate article was probed once against the
REST daily endpoint over 2019-11-04…10, and **the probe's status and date are recorded beside it
in the file**. The eight probes that returned 200 are also kept as raw responses under
`data/raw/recorder/wiki_daily/` — 1.0–1.1 kB each, through `Recorder.record` like everything else
— so the column is reproducible rather than merely asserted. Eight resolved and are the list. Three 404 and are listed as `unresolved` rather
than dropped: `United_States_Natural_Gas_Fund`, `BOIL` and
`ProShares_Ultra_Bloomberg_Natural_Gas` — confirmed absent by `en.wikipedia.org/w/api.php`, which
returns `missing=True` for the first two. **UNG and BOIL have no en.wikipedia article at all.**

**And then the trap.** `KOLD`, `UCO` and `SCO` all return **HTTP 200** with real traffic — 20, 44
and 495 views over the probe week. **None of them is a fund page.** All three are disambiguation
pages (`KOLD-FM`, a radio station in Cold Bay, Alaska; a Tucson television station; and for `SCO`
a disambiguation whose traffic has nothing to do with crude oil). A 200 is not a resolution.
Admitting them would have put ~559 views of radio stations into an oil-and-gas attention series
with `SCO` alone outweighing `Henry_Hub`. They are listed in `QUERIES.md` §1c **by name, as
excluded contaminants**, so that nobody re-adds them from the ticker list.

**The GDELT match rule is in the file, and the four themes are in it because of a measurement.**
On the real `20191104121500` slot (1,887 documents) a title-only phrase rule fires **once** for
`natural gas` and **once** for `crude oil`, while `ENV_OIL` fires on **69** rows, `ECON_OILPRICE`
on **20** and `ENV_NATURALGAS` on **17**. A phrase-only `news_n` on this corpus is a count of
near-zeros, and a z-score of a near-zero count is noise with a denominator. **The theme tokens
were verified to exist in the data before being written into the file**, not taken from
documentation. The six bare tickers are matched on the **title only** and carry
`precision: low` into every fixture row, because `boil`, `sco`, `uco` and `ung` are ordinary words
and `uso` is Spanish for "use" — recorded, not trusted.

**The digest is the enforcement of line 116.** `queries_hash()` is sha256 over the file's bytes
with newlines pinned to LF (D550/D551's shape, and bit-identical to
`validation.frozen.sha256_file(text_normalise=True)` — asserted). `load_queries` re-hashes on
every load, and a file with **no** digest beside it raises too: a query file nobody has committed
a hash for is exactly the file that can be edited quietly.

`QUERIES.md`'s parser reads the file's own markdown tables rather than a duplicated JSON block,
and where code must hold a copy of a rule — which haystack each query kind is matched in — **the
load asserts that the file's prose and the code's mapping agree** and raises when they do not.
Two copies of one fact is this repository's most repeated defect; a copy that is checked against
its original is not one.

---

## 4. The four guards, and why each is a refusal rather than a filter

R9 is the price list. An apparent effect spanning **465 percentage points**, monotone across five
quintiles, produced entirely by a conditioner that was not lagged — in a script upstream of every
null and hurdle the programme had. Each guard below therefore **raises** on a break.

| # | guard | the rule | the break that must raise |
|---|---|---|---|
| **21** | `zscore_matched` | same hour-of-day **and** weekday, days `t−60 … t−1`, sample sd | an observation dated **at or after** `t` → `LookaheadRefused`; fewer than 5 matched → `InsufficientHistory`; a constant window → `InsufficientHistory` (no denominator) |
| **22** | `wiki_available_at` | `hour_start + 1 h + 15 min`, unconditional | asserted at 14:09:59, **14:10:00**, **14:14:59**, 14:15:00 and 14:15:01 — the 14:14:59 probe is what stops an implementation that rounds to five minutes |
| **23** | `available(items, τ)` | `publication_ts <= τ`, and `event_ts` is **never read** | an item whose event is a year older and whose publication is one second later → excluded; re-stamping every event leaves the answer identical (property) |
| **24** | `att_accel` | mean of the last 3 hours minus mean of the prior 3 | a hole in the six hours → `InsufficientHistory`, never interpolated; on a constant the answer is **exactly 0.0**, asserted with no tolerance |

**Two choices that the deposit leaves open are written down rather than defaulted.**

* **ddof = 1.** The deposit says "z-score" and not which denominator. On the hand ledger's five
  matched Mondays, ddof = 0 gives `sd = √8` and `z = 2.1213…` against ddof = 1's `√10` and
  `1.8973665961010275` — **12% larger**, enough to move a `z > 2` breadth count and a `z > 3`
  burst flag. The sample sd is used because five observations *are* a sample of the matched-hour
  distribution, and the alternative is recorded in `tests/golden/test_attention_ledger.hand.txt`
  so the choice stays visible as a choice.
* **`MIN_MATCHED_OBS = 5`, and it is this repository's floor and not the deposit's.** 60 days of
  one weekday-hour is at most `ceil(60/7) = 9` observations, so the matched window is small by
  construction. Below five, `zscore_matched` raises rather than returning a ratio of two noisy
  numbers.

**`headline_burst`'s "since 09:30" is a New York wall clock**, derived through
`America/New_York`, because 09:30 ET is 13:30 UTC in summer and 14:30 UTC in winter and a constant
offset is wrong for half the year. The test asserts both halves of the year.

**One declared constant that is not the deposit's, named so it is not mistaken for it.**
`gdelt_available_at(slot) = slot + 15 min` is the **operational** time this repository could have
read a slot file, as opposed to the deposit's item-level publication rule that `available()`
implements. The file for slot `00:15` is posted some time after 00:15 and **this repository has
not measured how long after**; one full slot is a conservative stand-in in the same shape as line
267's own 15-minute pageview buffer. It is the fixture's `available_at_utc` and it is never
optimistic. Measuring the real posting lag is an open item.

---

## 5. Two findings about the data itself

**1. A GKG record is not a line.** `V2EXTRASXML` carries the source page's `<PAGE_LINKS>` verbatim
and a source page's link list can contain a raw newline. Splitting `20191104121500.gkg.csv` on
`\n` hands back fragments such as

    &HomeUrl=http://patft.uspto.gov/netacgi/nph-Parser?Sect1=PTO2%26Sect2=HITOFF%26p=1…

with one tab field. The first parse of a real slot raised on exactly this. `iter_gkg_rows` splits
on `GKGRECORDID` — 14 digits, `-`, an optional `T`, an index, a tab — and joins continuations back
with the newline they were split at, so a record is reassembled byte for byte. **A parser that had
merely skipped the fragments would have silently undercounted**, which is the worse failure and is
what a `try/except: continue` would have produced.

**2. The dump's project filter is doing real work, not ceremony.** The residue for the 13:00 hour
of 2019-11-04 holds 29 matched lines across **17 project codes** — `da`, `de`, `de.m`, `es`, `id.m`,
`it`, `ms.m`, `nl`, `nl.m`, `no`, `no.m`, `simple`, `simple.m`, `sv`, `sv.m` alongside `en` and
`en.m`. `Petroleum` alone appears under fourteen of them. `QUERIES.md` §1d fixes the summed projects
at exactly `en` and `en.m`, which is what the REST endpoint's `all-access` aggregates; everything
else stays in the residue and out of the series.

---

## 6. The sample: what it proves and what it does not

**Two days, 2019-11-04 … 2019-11-05** — 48 hourly dumps and 192 GDELT slots.

**The window was cut twice, and both cuts are measurements rather than preferences. This is the
part of the record worth reading.**

*Projection 1, from download rates measured before anything was launched:*

| window | streamed | projected |
|---|---:|---:|
| the full week 11-04…10 | 12,526 MB | **92.6 min** |
| **three days** | 5,442 MB | **40.2 min** |
| two days | 3,670 MB | 27.1 min |

The week was over the ~45-minute line, so the first build was **three days**. It was wrong twice
over, in opposite halves, and neither error was visible in a short probe:

1. **The GDELT half took 17.2 min against 8.7 projected.** Its own `[SPEED]` line read
   **`4,099s of work in 1029s wall on 4 workers — 3.98x, 100% efficiency`**. Every worker was
   busy the whole time and the phase still took twice as long as its bytes should cost. **Busy is
   not fast.** The projection priced the download at 2.34 MB/s and the worker also unzips a
   4.25 MB slot into ~13 MB of TSV and parses ~1,800 records out of it, which is GIL-bound and
   does not parallelise — so per-item time inflates until the efficiency ratio reads 100% while
   the throughput does not move. The measured end-to-end cost is **3.57 s a slot**, and that is
   what `project()` now uses. This is `CLAUDE.md`'s point in its purest form: **a per-call cost
   is not scaling, and a parallel-efficiency ratio is not throughput.**
2. **The pageview half collapsed.** Two workers had measured `1.96x, 98%` and 2.23 MB/s on a
   short probe. After roughly 17 minutes of sustained traffic, **one 47 MB file took 547 s —
   0.09 MB/s, twenty times slower** — and the run was stopped at 3 of 72 files. Re-measured
   immediately: **one connection 1.79 MB/s, two connections 1.54 MB/s aggregate — slower than
   one** — while a control fetch from GDELT on the same link held 2.32 MB/s, so it is the host
   and not the link. `dumps.wikimedia.org` throttles sustained concurrency and the throttle is
   invisible to a probe that runs for forty seconds.

*Projection 2, from the rates measured after that — one wiki worker at 1.79 MB/s and 3.57 s an
end-to-end GDELT slot:*

| window | streamed | projected |
|---|---:|---:|
| the full week | 12,526 MB | 129.7 min |
| three days | 5,442 MB | **56.1 min** |
| **two days 11-04…05** | **3,670 MB** | **37.7 min** |
| one day | 1,899 MB | 19.3 min |

**So the sample is two days, not the three the brief's fallback names, and the reason is on the
record: three days is 56 minutes at the rates this host actually sustains.** The cut costs
nothing the sample was for — two days is as far from the 60 days a real z-score needs as three is
— and 37.7 minutes is inside the line the brief drew.

**`WIKI_WORKERS = 1`, and the honest reading of three measurements on one day is that this host
gives one connection's worth of bandwidth however many you open.** The first two measurements
each said something different, which is the standing warning in `CLAUDE.md` — every guess here has
been wrong — applied to a measurement taken once.

**The optimisation pass, done before launch. Seven things, of which two were rejections:**

1. **One worker measured first**, not guessed: 47.0 MB gzipped → 168.4 MB decompressed in 27.8 s,
   **1.69 MB/s**, RSS 24 → 31 MB.
2. **`dumps.wikimedia.org` answers HTTP 429 to four concurrent connections.** Two ran at
   `[SPEED] 1.96x, 98%` and **2.23 MB/s** — *and this measurement did not survive contact with a
   sustained run; see the two cuts above.* One worker is what shipped.
3. **GDELT's static archive at four workers: `3.65x, 91%` — and the same 2.34 MB/s as one.** The
   link is the binding constraint on the download, so the four workers buy latency hiding and
   nothing else. Recorded so that nobody reads the 3.65× as a speed-up — which is exactly what
   the real run's `3.98x, 100%` would have been read as if this line were not here.
4. **A byte-level streaming filter instead of decode-and-split.** 168 MB of decompressed
   pageviews never becomes a `str`: each 1 MiB block is tested with `bytes.__contains__` (memchr)
   for `b" <Article> "` and dropped, and only a block that hits is split. One worker's resident
   set stays at ~31 MB and the GIL stays free for the other worker's socket.
5. **The GKG worker returns the residue, not the zip.** `parallel_map` holds every result until
   it returns, so a worker handing back 192 GKG bodies would put **1.5 GB** in resident memory —
   the slots average 7.9 MB across these two days. Verifying the md5 and filtering inside the
   worker keeps the peak at `workers × one slot`, and the measured end-of-run RSS is **49 MB**
   against 41 MB before the pool. *(The memory note: measure the worker before the fan-out.)*
6. **`masterfilelist.txt` — 127.8 MB — is streamed and only the sample's 864 lines kept**, and the
   residue is recorded because it is the provenance of every md5 this record checks.
7. **Rejected: `pagecounts-ez` merged**, which would have given a whole month's hourly data in one
   file instead of 720. Its filename is `…-views-ge-5-…`: it truncates low-traffic articles, and
   two of the eight (`ProShares` at 49 views and `United_States_Oil_Fund` at 75 over the probe
   week) are exactly that. **A cheaper source that silently drops rows is not a cheaper source.**
8. **Rejected: `mentions`.** `news_n` is a DOCUMENT count (line 251). GKG has one row per
   document; `mentions` has one row per (event, outlet) re-mention, so counting it would inflate
   a burst by the size of the syndication network. `export` is fetched for the **first slot of
   each day only** — three files, kept whole and unmodified — because it is the evidence that
   `DATEADDED` (publication) and `SQLDATE` (event) differ, which is unit test 23 on real data.

**Measured: 31.7 min against the 37.7 projected**, and the two halves missed in opposite
directions, which is the only reason the total landed where it did:

| | projected | measured |
|---|---:|---:|
| GDELT, 192 slots on 4 workers | 11.4 min | **9.1 min** (`[SPEED] 2,177s of work in 547s wall — 3.98x, 99%`) |
| `masterfilelist.txt` | 0.9 min | ~1.0 min |
| Wikimedia, 48 hours on 1 worker | 25.4 min | **21.8 min**, 2,773 MB at **2.12 MB/s** |
| **total** | **37.7** | **31.7** |

**And the byte projection was wrong by 20% in the other direction: 3,670 MB projected, 4,427 MB
streamed.** A GKG slot averages **7.9 MB** across these two days, not the 4.25 MB of the single
off-peak slot measured first — a slot at 04:00 UTC is not a slot at 16:00 UTC. The phase still
came in early because `project()` was re-based on the **end-to-end** 3.57 s a slot rather than on
its bytes, which is the only quantity that survived being measured twice.

Output: **3,072 rows, 24,498 bytes**, sha256
`30455a2b7c98cc93f4f6b9f6f0ef25db847932c7d3cbf65083161170143afa46`, and `--gates` passes on all
five checks.

**What the sample actually contains — looked at, not merely counted.** Totals over the two days:

| key | kind | documents / views | periods non-zero |
|---|---|---:|---:|
| `theme_env_oil` | theme | **11,974** | 192 of 192 |
| `Petroleum` | article | 6,377 | 48 of 48 |
| `Natural_gas` | article | 4,785 | 48 of 48 |
| `theme_econ_oilprice` | theme | 3,457 | 192 |
| `theme_env_naturalgas` | theme | 3,111 | 192 |
| `natural_gas` | **phrase** | **115** | 70 |
| `tk_boil` | ticker | **113** | 78 |
| `crude_oil` | **phrase** | **76** | 52 |
| `henry_hub` | **phrase** | **0** | **0** |
| `tk_kold`, `tk_uco` | ticker | **0** | 0 |
| `ProShares` | article | 19 | 19 |

Three things fall out of that table and each was predicted in `QUERIES.md` before the fetch:

1. **The themes carry the series and the phrases do not.** `theme_env_oil` is a hundred times
   `natural_gas`, and `henry_hub` as a phrase **never matched a single document title or URL in
   two days**. A phrase-only `news_n` would have been a column of zeros with a z-score on top.
2. **`tk_boil` at 113 is the verb.** It is the third-largest news key in the fixture and it is
   almost certainly about cooking and water advisories. This is why the six tickers carry
   `precision: low` into the meta and into every row, and why nothing here treats them as a series.
3. **`ProShares` at 19 views over 48 hours, and `United_States_Oil_Fund` at 22, are exactly the
   rows `pagecounts-ez`'s `views-ge-5` filter would have dropped** — the optimisation rejected in
   step 7 above. The rejection was right, and now it is measured rather than argued.

**What the sample proves.** That the two parsers read the real bytes; that every md5 in the window
matches; that 48 × 8 hourly article rows and 192 × 14 slot rows are complete with no hole; and that
every row's `available_at_utc` is strictly after its `observed_at_utc`.

**What it does not prove, and the list is the honest half.**

* **Nothing about whether attention predicts anything.** No return is computed, no z-score is
  taken on the sample, no feature is scored. The fixture is counts and tone.
* **Nothing about the 60-day z-score on real data.** 48 hours is not 60 days, so `zscore_matched`
  is exercised only on synthetic observations. The first real z needs ~61 days of hourly dumps —
  ~1,464 files, ~83 GB, and at the 1.79 MB/s this host sustains that is **~13 hours of
  downloading** — which is not launched here.
* **Nothing about the forward route on live data, and the reason is itself the finding.** Every
  `--gdelt-doc` attempt on 2026-09-22 answered **HTTP 429**, hours after the small burst of
  exploration probes that earned the cooldown, with the body

  > Please limit requests to one every 5 seconds or contact … for larger queries. All
  > high-traffic users should switch to our ngrams dataset …

  **The cooldown outlasts the session that triggered it.** `--gdelt-doc` honours the 5-second
  floor through D608's `RateLimiter` and still could not get a 200, which is the practical case
  for the files being the historical route and the API being a forward poll at a cadence measured
  in quarter-hours. `refuse_coarse_resolution` is therefore exercised on synthetic payloads
  (`15min` accepted, `hour`, `day`, `month`, `""` and `None` refused) and not yet on a live
  response.
* **Nothing about the social channel.** Deposit Q12 is unresolved and both social ids are
  `disabled (Q12)` in `QUERIES.md`. `att_breadth` counts the sources that are *present*, so the
  reachable maximum today is two, not three.
* **Nothing about coverage before 2015-05-01**, when the hourly dumps begin, or before
  2015-02-18, when GDELT v2 does.

---

## 7. The recorder job

`data/recorder/jobs.json`'s `attention` entry moves `needs_source` → `ready`. It keeps
`cadence: intraday`, so it stays outside gap detection and `check_gaps_scope` names it as
not-checked rather than omitting it silently. Its `source_url` is
`https://data.gdeltproject.org/gdeltv2/lastupdate.txt` — 320 bytes naming the three newest
15-minute files with their byte counts and md5s, which is exactly what a forward recorder needs
every quarter hour. **A `Job` carries one `source_url`**, so the second URL — the Wikimedia hourly
dump template — is named in the job's `note`, together with where both are copied from. The file's
own rule is honoured: *"A URL IS NEVER INVENTED. status 'ready' requires a source_url copied from
a file in this repository; the copy is cited in `note`."* Both URLs are now held here, in
`scripts/fetch_attention.py` (`GDELT_LAST`, `WIKI_DUMP`), in `data/attention/QUERIES.md` and in
this record. The other fifteen jobs are byte-identical; the schedule goes from 7 ready to 8.

**One thing D608's own gate caught, and it is worth writing down.**
`tests/unit/test_recorder.py::test_every_ready_url_is_https_and_cites_where_it_was_copied_from`
requires every ready job's URL to be `https://`, and the first draft of this job carried the
`http://` spelling that GDELT's own documentation and index files use. Probed rather than assumed:
`https://data.gdeltproject.org/gdeltv2/` answers **200** for `lastupdate.txt`,
`masterfilelist.txt` and a 2019 GKG slot, so `fetch_attention.py` fetches over TLS throughout.
**But `masterfilelist.txt`'s own lines still spell `http://`**, which is not ours to change — so
the md5 index is keyed on the **file name** rather than on the URL string. A checksum lookup that
has to guess which of two spellings the other side used is a checksum that can fail to find its
entry, and a checksum that silently finds nothing is worse than one that does not match. The
selftest asserts the lookup succeeds under both spellings.

## 8. Web access

GET and HEAD only. No login, no cookie, no personal data in any header, and no query parameter
carrying anything but a public search term. The user agent is this repository's own descriptive
one — `BacktestFramework research script research@backtest-framework.org` — because a contact
string is Wikimedia's stated condition for using its APIs and dumps. GDELT's DOC 2.0 API is
polled at no more than **one request per 5 seconds**, its own stated limit, and it is touched by
`--gdelt-doc` alone.

---

## 9. What would change this record

* **The principal choosing the daily `wiki_n`** (§2). That re-derives `att_accel` and voids unit
  test 22 as written, and it is a doc edit to the deposit, not a code change here.
* **A measured GDELT posting lag** replacing the declared one-slot stand-in (§4).
* **Q12 resolving**, which adds `social_n`, a third z to `att_level`, `lev_share`, and a third
  possible source for `att_breadth` — and needs a doc edit to `QUERIES.md`, hence a new digest.
* **A backfill being authorised.** The two prices are in §2 and neither is paid here.

---

## Footer drafts, for the integrator

**`docs/data-available.md` paragraph:**

> **`data/fixtures/attention_sample.csv.gz`** — the attention layer's bounded sample, D612.
> 2019-11-04 … 2019-11-05 UTC, in-sample: 48 hourly Wikimedia pageview rows for each of the eight
> `data/attention/QUERIES.md` articles (`en` + `en.m` summed) and 192 fifteen-minute GDELT GKG
> rows for each of its fourteen queries, with `observed_at_utc`, `available_at_utc`, a count and
> a tone (`NaN` on pageview rows and on any slot with no matched document — an absent tone is
> never 0.0). 3,072 rows, 24,498 bytes, sha256
> `30455a2b7c98cc93f4f6b9f6f0ef25db847932c7d3cbf65083161170143afa46`.
> **What bites a study that reads it unchecked:** it is *two days*, so nothing in it
> supports the deposit's 60-day matched z-score — the first real `z_wiki` needs ~1,464 hourly
> dumps and ~83 GB, about thirteen hours of downloading at the 1.79 MB/s `dumps.wikimedia.org`
> sustains here; the six `tk_*` keys are three-letter tickers matched on document titles and
> are marked `precision: low` in `QUERIES.md` and in the meta, because `boil`, `sco`, `uco` and
> `ung` are ordinary words; and `available_at_utc` on a `gdelt_15m` row is the slot stamp plus one
> declared slot, a conservative stand-in for an unmeasured file-posting lag rather than a measured
> one; and **the four `theme_*` keys carry the news series while the four phrase keys are nearly
> empty** — `theme_env_oil` totals 11,974 documents against `natural_gas`'s 115, and `henry_hub`
> as a phrase matched **zero** documents in two days. Per-article **hourly** Wikipedia data exists
> only in the `dumps.wikimedia.org` hourly files
> — the REST route is daily-or-monthly and answers HTTP 400 to an hourly request, which is D612's
> erratum on the deposit's line 112.

**`CHANGELOG.md` bullet:**

> - **D612 — the attention layer (ledger §3.3c, §P3.7).** `data/attention/QUERIES.md` written
>   before any feature code and hashed (`QUERIES.sha256`, LF-pinned; `load_queries` raises
>   `QueriesTampered`), `data/attention.py` with the Wikimedia dump and GDELT GKG parsers and the
>   four point-in-time guards — the 14:15 publication boundary, the publication-not-event key, the
>   `t−60 … t−1` matched z-score that *refuses* a same-day observation rather than filtering it,
>   and an `att_accel` that is exactly 0.0 on a constant — plus `scripts/fetch_attention.py`
>   routing every fetch through D608's `Recorder`. A **two-day** sample fixture (2019-11-04…05,
>   projected 37.7 min): the three-day build was abandoned mid-run when `dumps.wikimedia.org`
>   throttled two sustained connections from 2.23 MB/s to **0.09 MB/s** and then measured slower
>   on two than on one, and when the GDELT half read `3.98x, 100% efficiency` while taking 17 min
>   against 9 — **busy is not fast, and a parallel-efficiency ratio is not throughput.**
>   **Erratum recorded, deposit not edited:** its line 112's "Wikimedia hourly pageviews" has no
>   REST route — hourly exists only in the dumps, at ~2.5 TB for 2016–2023 against GDELT GKG's
>   ~1.64 TB, and no backfill is launched. Three of the four ProShares ticker pages resolve to
>   disambiguation pages and are excluded by name. Ledger unit tests 21–25 claimed; 54 tests.

**Numbered tests claimed:**

| deposit test | function |
|---|---|
| ledger 21 | `tests/unit/test_attention.py::test_ledger_21_zscores_use_only_the_prior_sixty_matched_days` |
| ledger 22 | `tests/unit/test_attention.py::test_ledger_22_an_hourly_pageview_is_unavailable_at_1410_and_available_at_1415` |
| ledger 23 | `tests/unit/test_attention.py::test_ledger_23_gdelt_items_are_keyed_on_publication_not_event_time` |
| ledger 24 | `tests/unit/test_attention.py::test_ledger_24_att_accel_is_positive_on_a_ramp_and_zero_once_flat` |
| ledger 25 | `tests/unit/test_attention.py::test_ledger_25_query_lists_load_from_queries_md_and_hash` and `::test_ledger_25_the_hash_is_stored_with_every_trial_in_trials_csv` |
