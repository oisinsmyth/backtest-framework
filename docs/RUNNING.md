# Running it

*What happens when you actually run this suite, on this machine and on a fresh clone.*

Everything here is operational: how long it takes, what a `git clone` does on Windows, and what
the tests that skip are waiting for. It lives on its own page because none of it is about the
framework, and forty-two consecutive lines of it used to sit between the front page's two
commands and its first real explanation ([D548](decisions/D548-the-front-page-stops-explaining-the-checkout.md)).

Start here:

```bash
uv sync
uv run pytest -q tests/golden     # 331 ledger-anchored tests, under a second
```

That runs on a bare clone — the golden masters use synthetic bars and need no market data. The
full suite is `uv run pytest -q`.

## How long it takes

**Wall-clock runtimes live on this page and nowhere else (D544).** A test count is the same on
any machine at a given commit; a runtime is a property of the machine and the moment, so it has
one home and a date on it.

**The reason D544 gave for that rule was too generous, and moving this page measured it.** The
claim was that runtimes are *the only* numbers no gate can hold. Seven figures from this page were
perturbed one at a time — the clone's pass and skip counts, the 85-character path limit, "49 of
the 53", the manifest's panel and blob-id counts, D536's 844 MB — and the suite stayed green on
**all seven**. The counts sweep checks quantities it can compute from the git index, and none of
these was one of them.

Three of the seven are computable and are now pinned by
[`tests/unit/test_running_page_figures.py`](../tests/unit/test_running_page_figures.py), which
also names the eight panels that have no blob id rather than only counting them. The rest are
properties of a machine, of a clone, or of history, and nothing but this page's date stands behind
them. [`docs/VERIFICATION.md`](VERIFICATION.md) carries the same clone figures for its own
argument, and **nothing stops those two drifting apart** — which is worth knowing when you read
either. **Measured 2026-09-18, eight runs on this machine: 3m48s
to 5m52s**, the spread being how loaded the laptop was rather than anything about the suite. Two
documents used to quote this and they disagreed in both directions — one said 3m31s here and 5m45s
on a clone, the other 6–7.5 min here and 2m56s on a clone, which cannot both be true about which is
faster. [`CONTRIBUTING.md`](../CONTRIBUTING.md) and [`README.md`](../README.md) both point here.

## Cloning it

**On a clone it was 2,055 passed and 126 skipped in 4m46s** — measured on 2026-09-19, on a
**Windows** clone. The platform is part of that figure: the Linux CI runner skips one more,
because it has no API key for `tests/unit/test_us_shorts_fixture.py:583` to scan for
([D551](decisions/D551-a-snapshot-id-that-depended-on-the-os.md)).

**73 of those 126 are the Binance purge** — tests that passed on a clone until the two crypto
price panels left the index and the history
([D554](decisions/D554-the-binance-panels-leave-too.md)). That is the cost of not redistributing
them, stated rather than absorbed. Measured by cloning this
repository into an empty directory and running it, not by reasoning about one from inside the
working copy. That distinction has **three** times earned its keep: the first clone failed three
tests the working copy could not, on a line-ending convention the working copy predates; the
second found five links that resolve only on the author's disk; and the third would not check out
at all. Every tracked path is now 85 characters or shorter and a test says so
([D540](decisions/D540-local-config-a-clone-never-receives.md)) — before that the longest was
209, and on Windows a default `git clone` aborted the checkout, **reported exit code 0**, and left
an empty index. If you are on an older git and want the belt and braces:

```bash
git clone -c core.longpaths=true <url>
```

That flag is set in *this* repository's `.git/config`, which is why the failure was invisible here
for 539 decisions: **`git clone` does not copy local config.** Three separate defects have now had
that same cause.

## What the skips want

**Every skip that wants a file names it — 122 of the 126 (2026-09-19).** The other four name no
file and say why: **three** want a git identity, which no clone has and which is the same defect
class as [D540](decisions/D540-local-config-a-clone-never-receives.md), and **one** wants a trial
registry, which is gitignored and local. Until this measurement that sentence said all four were
the git identity, which was wrong by one. This sentence used to say all
53 named a file and 16 did — the 33 that did not were saying "fixture not built", or in four cases
nothing at all, about panels that are fully recoverable. The panels left git in
[D536](decisions/D536-manifest-only-storage-for-the-bulk-panels.md) at 844 MB — which is what
a **checkout** no longer carries; they remain in the history, so a `git clone` is about 1.1 GB, of
which 969 MB is `.git`. Two of the smallest came back into the index in
[D538](decisions/D538-two-small-panels-return-to-the-index.md) for 6.9 MB and, because their
blobs were already in history, no extra bytes at all — which is what took the skips from 136 to 49
(2026-09-16). [`data/data_manifest.json`](../data/data_manifest.json) carries the sha256 of all 128
panels and the git blob id of **115** of them. The thirteen without one —
`data/d377_ensemble.npz`, `data/d382_scores.npz`, `data/fixtures/fut_day1m.parquet`, the two
settlement panels D556 built on 2026-09-19, `data/fixtures/fut_settle_strip.csv.gz` and
`data/fixtures/fut_curve_front_next.csv.gz`, the one-minute bitcoin panel D580 built on
2026-09-20, `data/fixtures/fut_btc_1m.csv.gz`, and the ES option end-of-day panel D581 built on
2026-09-21, `data/fixtures/fut_es_options_eod.csv.gz`, the CME session calendar D589 built the
same day, `data/fixtures/cme_session_calendar.csv.gz`, the order-book depth panel D604 built the
same day, `data/fixtures/fut_book_depth_1m.csv.gz`, the two panels the basis-momentum closure
programme built the same day, `data/fixtures/fut_cleared_volume_cm_daily.csv.gz` and
`data/fixtures/hkm_factors.csv.gz`, the ES option volume panel in ET clock buckets D613 built
on 2026-09-21, `data/fixtures/fut_es_0dte_volume_cutoffs.csv.gz`, and the ES option signed flow
census D617 built on 2026-09-22, `data/fixtures/fut_es_0dte_signed_flow.csv.gz` — were never tracked
in the first place, so
the checksum is all the manifest can offer for them.

**The blob ids no longer resolve, and cannot be made to.** They record what each panel's blob was
in the pre-publication history, and
[D549](decisions/D549-the-history-a-public-clone-receives.md) purged those objects — they are the
CME- and Alpha-Vantage-derived panels this repository may not redistribute. **113 of the 115 are
dangling in any clone**; the two that resolve are the Binance panels still tracked. Restoring them
would undo the licence fix, so the recovery path and the purge are mutually exclusive and the
purge won. What the manifest still offers is the **sha256**: obtain a panel elsewhere and it tells
you whether you have the right bytes
([D552](decisions/D552-the-recovery-path-the-purge-removed.md)).
