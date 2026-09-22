# `data/attention/` — the fixed query definitions for the attention layer

*Record: [D612](../../docs/decisions/D612-the-attention-layer-and-its-point-in-time-guards.md).
Spec: the settlement-flow ledger deposit, §3.3c (its lines 105–116) and §P3.7 (its lines
249–267).*

| file | tracked | what it is |
|---|---|---|
| [`QUERIES.md`](QUERIES.md) | yes | **the hashed object.** The en.wikipedia article list, the GDELT queries and their match rule, the dump projects, and the social ids that are disabled under deposit Q12 |
| [`QUERIES.sha256`](QUERIES.sha256) | yes | sha256 of `QUERIES.md` with newlines pinned to LF. `attention.load_queries` re-hashes on every load and raises `QueriesTampered` when the two disagree |

**Why a digest file at all.** The deposit's line 116: *"Query definitions (keyword lists, article
titles, tickers) are fixed in `data/attention/QUERIES.md` **before** any feature is computed, and
not changed afterwards without a doc edit."* A rule enforced only in prose gets skipped — that is
[R6](../../docs/RULES.md#r6)'s whole content — so the rule is enforced by a hash that moves when
the file moves, and unit test 25 puts that hash on every row of `trials.csv`, where a trial run
under an edited query list becomes identifiable from the log alone.

**Editing `QUERIES.md` is a doc edit and rewrites `QUERIES.sha256`.** That is the intended cost.
Nothing in `src/backtest_framework/data/attention.py` or `scripts/fetch_attention.py` writes to
either file.

## The erratum on the deposit's line 112 — read this before planning a fetch

The deposit's 3.3c table says **"Wikimedia hourly pageviews | Hourly, from 2015"**. The Wikimedia
REST per-article endpoint **does not serve hourly data.** Probed 2026-09-22:

    .../per-article/en.wikipedia/all-access/user/Natural_gas/hourly/2023010100/2023010223
      -> HTTP 400 {"detail":"granularity should be equal to one of the allowed values:
                             [daily, monthly]"}
    .../per-article/en.wikipedia/all-access/user/Natural_gas/daily/2019110400/2019111000
      -> HTTP 200, items[].views

Per-article **hourly** exists only in the dumps, one file per hour covering every project and
every article on earth:

    https://dumps.wikimedia.org/other/pageviews/{YYYY}/{YYYY-MM}/pageviews-{YYYYMMDD}-{HH}0000.gz

~47–66 MB gzipped an hour, ~4× that decompressed, from 2015-05-01. **The deposit is not edited**
(it is a read-only source here); the erratum is recorded in the D612 record, and the price it
implies — ~2.5 TB over 70,128 files for 2016–2023 — is recorded there too, beside the alternative
the principal may prefer: a **daily** `wiki_n` off the REST route, which would re-derive
`att_accel` on a different clock and void unit test 22 as the deposit writes it.

## Where the bytes go

Every fetch routes through D608's `Recorder`, so raw responses live in the gitignored cache
`data/raw/recorder/{wiki_daily,wiki_hourly_dump,gdelt_files,gdelt_doc}/` under a `fetched_at`
name, beside a sha256 and the source URL. Two of those four store a **filtered residue** rather
than the whole file — the hourly dumps and the GKG slots — and
[`scripts/fetch_attention.py`](../../scripts/fetch_attention.py)'s module docstring says exactly
what is kept and why. The derived fixture is `data/fixtures/attention_sample.csv.gz`, gitignored
by suffix, with its `.meta.json` committed beside it.
