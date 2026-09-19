# D553 — The two panels stay, and the guarantee that rested on one of them no longer does

*Filename shortened on creation ([D540](D540-local-config-a-clone-never-receives.md)). The H1 above
is the full title.*

**Status:** Result
**Date:** 2026-09-19
**Category:** Infrastructure
**Source:** The one item [D549](D549-the-history-a-public-clone-receives.md) left open after
publication: two vendor-derived panels that remain tracked and are therefore published.

**They stay. And the thing that made the decision expensive to reverse has been removed, so it is
now a decision rather than a dependency.**

---

## What is published

| panel | size | source |
|---|---:|---|
| `data/fixtures/crypto_universe_2015_2025_raw.csv.gz` | 6.35 MB | Binance |
| `data/fixtures/crypto_daily_2015_2025_raw.csv.gz` | 0.21 MB | Binance |

These are the pair [D538](D538-two-small-panels-return-to-the-index.md) deliberately returned to
the index after [D536](D536-manifest-only-storage-for-the-bulk-panels.md) took the bulk panels
out — chosen because their blobs were already in history, so re-tracking them cost **no extra
clone bytes at all**. That reasoning is unaffected by publication.

## Why removing them was not free, measured rather than assumed

**`crypto_universe_2015_2025_raw` is the only entry in `_FIXTURE_SNAPSHOT_IDS` that a clone
receives.** The other two pinned fixtures — `crypto_intraday_1h_raw` and
`universe_daily_2015_2024_raw` — are manifested out and skip.

So until today, the **absolute value** of a snapshot id was verified on CI by exactly one file.
Every other test in `test_snapshot_store.py` checks a *relationship*: idempotence on identical
content, a new id after a restatement, refusal to load a tampered payload. Each of those would
pass unchanged if the id algorithm were replaced wholesale.

[D551](D551-a-snapshot-id-that-depended-on-the-os.md) is the proof that this matters: the writer's
newline handling made the same payload freeze to two different ids depending on the operating
system, and **the fixture pin is the only thing that caught it**.

Removing the panel would therefore have retired the gate that found the last defect, in the same
week it found it. Seven test files reference the pair besides.

## What changed, so that the decision is reversible

`test_a_snapshot_id_built_from_code_is_frozen` pins
`e77fe8e910a5521a5f63fa74f90209dfe7c660b2c89b08da3709ed58e9360a71` for a payload **built in
code** — two symbols so ordering matters, volumes, and a dividend and a split, which are what go
through the `events.json` writer D551 fixed. It owes nothing to any data file.

**That is the substantive output of this record.** The panels staying is a judgement; the
guarantee no longer depending on them is a fact. If the licence assessment ever changes, the
fixtures can go without taking the snapshot identity's only CI-exercised check with them.

**The class is worth naming: a gate whose only CI-exercised instance is a licence-contingent
file.** Coverage that rests on a decision someone might revisit is coverage with an expiry date
nobody has written down. This is the second instance this week — D548 found the counts sweep
checking only what it can recompute, and this found a pin resting on a file that might have to
leave.

## What this record does not settle, and deliberately

**Whether Binance's terms permit redistribution.** That is the principal's assessment and not this
record's to make. What can be said is what is structurally different about these two and the 113
that were purged: `docs/data-available.md:285` draws the line at *"every CME product here"*, and
Binance is not one; the purged panels were Databento `GLBX.MDP3` and Alpha Vantage; and Binance
publishes historical klines for public download, which is a fact about the vendor rather than a
reading of a contract.

**If that assessment comes out the other way**, the removal is now: delete two files, let seven
test files skip through `requires_panel`, re-measure the skip counts in `README.md`,
`docs/RUNNING.md` and `docs/VERIFICATION.md` — which are platform-dependent anyway (D551) — and
nothing else. The snapshot gate keeps working.

**Whether the other small tracked fixtures deserve the same look.**
`data/fixtures/xle_xop_daily_2015_2024*.csv` (1.1 MB) are ETF daily bars, and the `*_events.json`
and `*_deals.json` files are derived event lists rather than price series. D549 named them; nothing
since has examined them, and this record does not either.

---

## ADDENDUM 2026-09-19 — SUPERSEDED the same day

The principal reversed this. The two panels were purged from the index and the history in
[D554](D554-the-binance-panels-leave-too.md), at a cost of 73 tests on every clone.

Nothing above is edited. The measurement that made the case for keeping them is the same
measurement that made removing them affordable: this record pinned a snapshot id from a payload
built in code, so the guarantee D551 fixed no longer depended on the file that has now gone.
