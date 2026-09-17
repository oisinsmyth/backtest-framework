# D524 — `fut_day5m` verifies clean by two routes, and the flat id dict turns out to be **non-reproducibly** wrong

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D524-the-day5m-fixture-verifies-clean-and-a-flat-id-dict-is-non-reproducibly-wrong.md`. The H1 above is the full title.*

*2026-09-13, on the principal's instruction to rebuild and diff the day5m fixture after
[D521](D521-the-three-remaining-flat-id-builders-are-ported-and-the-open.md).
Data layer only: no study, no signal, nothing admitted to any book or ledger (R15). The fixture and
its builder were committed by a concurrent session in `e773167`; nothing here changes either.*

---

## The one-line answer

**The committed fixture is correct, and the thing worth writing down is about the defect it avoided:
a flat `{instrument_id: symbol}` dict does not even give the SAME wrong answer twice.** Every one of
the eight ambiguous ids in the 2019 file can take a *different* surviving label from one process to
the next, because `store.metadata.mappings` iterates in an order that varies with Python's string
hash seed. A fixture built on a flat dict is therefore not reproducible and not auditable after the
fact.

| check | result |
|---|---|
| `--build` re-run from cache, diffed | **byte-identical** — 10,384,830 rows, 0 differing values, sha256 `aa2eb147…` both ways, 1.0 min |
| 5-minute bars folded to hours vs `fut_breadth_hourly` | **906,905 root-session-hours, 0 differences** in open/high/low/close/volume/trade-count, 0 orphans either way |
| what a flat dict would have done to these 36 roots | **29** mislabelled outright windows of 27,420; **14,139** foreign windows, in all 26 files |
| is the flat dict's answer reproducible? | **no — the surviving label is a coin flip per process** |

---

## 1. There was nothing to port, and that is exactly why this was still worth doing

`build_fut_day5m.py` already imports the windowed `ids_of` from the breadth builder — D521 recorded
it as one of the three already-correct builders. What it had never had is the check D520 and D521
applied to every other futures builder: **rebuild, and diff.**

Two things make that non-trivial here, and they are why the verification has three parts rather
than one:

**`--build` reads a CACHED decode.** The id mapping is applied during `--decode`, which costs 88
minutes and writes `temp/day5m_decode/*.5m.parquet`; `--build` concatenates those and inner-joins the
breadth fixture. **So a rebuild-from-cache proves the build is reproducible and says nothing
whatsoever about the mapping.** Reporting it as "rebuilt and identical" without that sentence would
have been the kind of result that is true and misleading at once.

**A concurrent session is active in this repository.** The rebuild therefore went to a temp path
with `OUT`/`META` redirected in-process (`do_build` is single-process, so module globals work — unlike
a spawn-based builder), and the committed parquet was never opened for writing.

## 2. The build is reproducible

10,384,830 rows, twelve columns, compared row for row: **0 differing values**, and the whole parquet
hashes identically — `aa2eb1474d8368e9`, 102,453,907 bytes, both ways. 1.0 minute.

## 3. The decode agrees with a separately decoded fixture, to the last tick

Rather than spend 88 minutes re-decoding, the 5-minute bars were folded into hours (twelve slots to
the hour) and compared against `fut_breadth_hourly`, which is a **separate decode pass over the same
archive**:

| | |
|---|---|
| root-session-hours compared | **906,905** |
| hours in day5m but not breadth / in breadth but not day5m | **0 / 0** |
| differing open / high / low / close / volume / **trade count** | **0 / 0 / 0 / 0 / 0 / 0** |

The trade count matters more than the prices here: `n` would move if even one minute-bar were
attributed to a different contract, so agreeing on `n` across 906,905 hours is a statement about the
*labelling*, not just the arithmetic.

**What this does not establish.** day5m *imports* `ids_of` from the breadth builder, so this is an
independent decode **pass**, not an independent **implementation**. It rules out a stale cache, a
chunking difference and a file-order difference; it cannot catch an error inside `ids_of` itself,
because both sides would make it identically. That is what §4 is for.

## 4. What a flat dict would have done to THESE roots — and why index-1m saw none of it

| | index 1m (4 roots, D521) | **day5m (36 roots)** |
|---|---|---|
| mapping windows | 1,262 | **27,420** |
| outright windows a flat dict **mislabels** | **0** | **29**, in 12 of 26 files |
| foreign windows it would **ingest** | 712 | **14,139**, in **all 26** files |

**The four index roots never collide with each other; the 36-root list does**, because it contains CL
(the decade-slot reuse D467 measured) and the whole FX complex. Resolved to objects, from the two
worst files:

    2019   iid 178362   CLN9  <-> CLN29         the decade-slot swap, six of the eight are CL
           iid  73454   NKDU0 <-> SIF9          Nikkei and SILVER, different roots entirely
           iid    162   6CX9  <-> 6CZ4
    2020   iid   1318   6BU5  <-> 6AQ0          STERLING and the AUSSIE DOLLAR
           iid   7084   6AM5  <-> 6AK0
           iid   6905   6BM5  <-> 6BK0
           iid    859   6CU5  <-> 6CQ0

By root across those two files: **CL 6, 6C 2, 6B 2, 6A 1, NKD 1.**

## 5. The finding: a flat dict is not even deterministic

I ran the naming code twice and **the two runs contradicted each other** about which of iid 436191's
two windows a flat dict mislabels — one said it keeps `CLZ9`, the other `CLZ29`. Rather than publish
whichever answer I happened to get, I tested it: the same file read in six processes under six
`PYTHONHASHSEED` values.

    seed 4: first five outright symbols  6CH9, BZM1, BZZ1, 6AK0, 6EQ9
    seed 5: first five outright symbols  HGK9, 6CH3, NKDH2, BTCG0, ZMV9

    iid    162   6CZ4,  6CX9,  6CX9,  6CZ4,  6CZ4,  6CZ4
    iid 178362   CLN9,  CLN9,  CLN9,  CLN9,  CLN29, CLN29
    iid 178468   CLU29, CLU29, CLU9,  CLU29, CLU9,  CLU29
    iid 213372   CLQ9,  CLQ29, CLQ9,  CLQ9,  CLQ29, CLQ29
    iid 405691   CLV9,  CLV29, CLV9,  CLV29, CLV9,  CLV29
    iid 436191   CLZ9,  CLZ9,  CLZ29, CLZ9,  CLZ29, CLZ29
    iid 628562   CLX9,  CLX29, CLX9,  CLX29, CLX29, CLX29
    iid  73454   NKDU0, NKDU0, NKDU0, NKDU0, NKDU0, SIF9

**The symbol iteration order itself varies between processes**, so "the last write wins" picks a
different winner each time. **All 8 of the ambiguous ids in this one file flip: 8 observed of 8, with
0 appearing stable against 0.25 expected by chance.**

**Read that count correctly, because I got it wrong twice before running enough draws.** An id
carrying two labels is unstable *in principle*; a finite probe only catches it when two draws happen
to differ, so at n draws an unstable id **looks** stable with probability 2^-(n-1). At three seeds
that is 25 %, and a three-seed probe duly reported "5 of 8" once and "6 of 8" the next time **with a
different set of ids** — two numbers that are the same finding. The script now reports
`expected_false_stable` beside the observed count so the rate cannot be misread.

**iid 73454 is the case that should worry a reader**: `NKDU0` five times in a row and then `SIF9` on
the sixth. A five-read probe would have called it stable — and it is the Nikkei being labelled
**silver**.

Three consequences, and the third is the one that matters:

1. The **count** of mislabelled windows is stable (an id with two labels has exactly one wrong window
   whichever way the coin lands), which is why §4's 29 reproduces exactly — 29 of 27,420 windows and
   14,139 foreign windows on two independent 20-minute passes. The **identities** are not.
2. Two builds of the same flat-dict code over the same archive on the same machine would produce
   **different fixtures**.
3. So a fixture built on a flat dict **cannot be reproduced, and therefore cannot be audited after
   the fact** — you cannot recover which labelling it used without the original artefact. Where D521
   found the open-interest fixture wrong on twelve CL sessions, re-running that flat build might
   have produced a *different* twelve. **This is a reason to distrust any pre-D520 flat-built
   artefact beyond the specific rows a diff happened to catch**, and a reason the windowed
   mapping's determinism is a property worth having in its own right, separate from correctness.

## 6. Where this leaves the family

Every futures builder has now been rebuilt and diffed against its committed fixture:

| builder | mapping | verified |
|---|---|---|
| `build_fut_breadth_hourly` | windowed (original) | reference for §3 |
| `build_fut_sessions_hourly` | windowed (D520) | byte-identical, 2 roll rows removed |
| `build_fut_day5m` | windowed (imported) | **byte-identical (D524)** |
| `build_fut_open_interest` | windowed (D521) | **12 CL rows corrected** |
| `build_fut_micro_flow` | windowed (D521) | byte-identical |
| `build_fut_index_1m` | windowed (D521) | byte-identical |

**One open item, deliberately not done:** the 88-minute decode was not re-run, so day5m's cache is
verified by agreement with breadth rather than by regeneration. If the cache is ever deleted, the
next decode is the stronger check and should be diffed against the committed parquet.

Everything here is recomputed by
[`scripts/d524_day5m_verification.py`](../../scripts/d524_day5m_verification.py)
(`--rebuild-diff`, `--aggregate`, `--precheck`, `--determinism`, `--name`) into
[`data/d524_day5m_verification.json`](../../data/d524_day5m_verification.json).
