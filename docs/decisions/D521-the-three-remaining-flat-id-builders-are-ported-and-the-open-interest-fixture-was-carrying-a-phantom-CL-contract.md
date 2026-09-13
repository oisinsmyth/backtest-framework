# D521 — the three remaining flat-id builders are ported to the windowed mapping, and the open-interest fixture was carrying a **phantom CL contract** for twelve sessions

*2026-09-13, on the principal's instruction "port the windowed mapping to the three flat builders",
after the audit in [`working/AUDIT-flat-id-map-exposure.md`](../../working/AUDIT-flat-id-map-exposure.md).
Data layer only: no study, no signal, no edge, nothing admitted to any book or ledger (R15).*

---

## The one-line answer

**Two of the three fixtures are unchanged and the third was wrong.** The open-interest fixture had an
Australian-dollar contract counted as crude for twelve January 2024 sessions, because CME reissued its
instrument_id to `CLG36` ten months later and a flat dict keeps only the last label. The overstatement
is **0.014 %–0.026 % of CL's total open interest** — too small for any distributional check to see,
which is exactly what the audit warned and why the rebuild-and-diff was the only way to know.

| builder | fixture | rebuilt | verdict |
|---|---|---|---|
| `build_fut_open_interest.py` | `fut_open_interest_daily.csv.gz` | 3.3 min, 8 workers | **12 CL rows changed**, front month untouched, all 63 gate scalars identical |
| `build_fut_micro_flow.py` | `fut_micro_flow_5m.csv.gz`, `_rolls.csv.gz` | 6.1 min, 8 workers (87 %) | **byte-identical** (same decompressed sha256) |
| `build_fut_index_1m.py` | `fut_{ES,NQ,YM,RTY}_rth_1m.csv.gz`, sessions, rolls | 6.2 min, 6 workers (94 %) | **byte-identical**; 16,077 foreign bars ingested, 0 survived |

Every figure below is recomputed by
[`scripts/d521_flat_vs_windowed_audit.py`](../../scripts/d521_flat_vs_windowed_audit.py) into
[`data/d521_flat_vs_windowed_audit.json`](../../data/d521_flat_vs_windowed_audit.json). It reads the
flat-map side **from git**, not from `temp/`, so it reproduces after `temp/` is deleted; pass
`--baseline <rev>` to point it at this commit's parent once this is committed. The one fixture it
cannot compare that way is `fut_RTY_rth_1m.csv.gz`, which is uncommitted (see §4) — its decompressed
sha256 is `60d613bf749410d7` before and after, checked against the pre-rebuild copy directly.

---

## 1. The phantom, named

From the mapping table of `glbx-mdp3-20240101-20241231.statistics.dbn.zst` itself:

    iid 42007396   6AF4    2024-01-01 .. 2024-01-21     Australian dollar, January 2024
                   CLG36   2024-11-07 .. 2025-01-01     February 2036 crude

`ids_of` wrote `{42007396: ("CL", "CLG36")}` — the last mapping the loop reached — and threw the
validity dates away. Every statistics record 6AF4 published in its last three trading weeks was
therefore ingested as a 61st CL contract and its open interest added to CL's total. It stops on
2024-01-19 because that is when 6AF4 stopped trading, not because anything noticed.

One other id in that file has the same shape and does **not** bite: `42002896` was `BTCN4-MBTH5`
(a bitcoin spread, so the outright regex never matched it) before becoming `CLN35`.

**This is not a rare accident — it is the archive's normal behaviour, and it is only this case that
cost anything.** Across all 17 statistics files there are **57 ids whose flat label belongs to one of
the four roots while an earlier window of the same id does not**: 26 on GC, 15 on CL, 10 on NQ, 6 on
ES, in every year from 2010 to 2026, and **43 of the 57 cross roots entirely** (a gold id later
labelled copper, a Nasdaq id that was silver). Yet the flat map ingested only **34 foreign statistics
records in the whole archive** — 0.0019 %, all in the 2024 file, all of them 6AF4's. The other 56
reuse events contributed **nothing**: their instruments published no open-interest or cleared-volume
record inside the foreign window at all. The defect is ubiquitous; what made 6AF4 bite is that it
is an *outright future that reports open interest daily*, and the label it was handed — `CLG36`,
February 2036 — had no genuine record of its own on those sessions, which is what the contract count
going 61 → 60 says: the phantom was an extra contract, not a substituted one.

| | committed (flat) | rebuilt (windowed) |
|---|---|---|
| rows / keys | 13,843 | 13,843, none gained or lost |
| CL sessions changed | — | **12**, 2024-01-03 … 2024-01-19 |
| `oi_n_contracts` those days | 61 | **60** |
| `oi_total` overstated by | 235 … 401 contracts | **0.0144 % … 0.0257 %** |
| `cv_total` overstated by | 42 … 240 contracts | — |
| `oi_front` | — | **unchanged on every row of every root** |
| `published_at_et` | — | one row, CL 2024-01-09, 09:33 → 09:32 |
| CL distinct contracts (meta) | 148 | **147** |
| gate scalars (O1–O5, 63 of them) | — | **63 of 63 identical** |

**Front month is untouched**, which is why D497's four-quadrant read is unaffected and why the
audit's distributional checks — total/front ratio, contracts per day, low-total days — all passed on
a contaminated series. A front-month rule filters the contamination out *by volume*; a curve study
would not, and that is the case §5 of the audit said to fix before doing curve work.

## 2. Micro flow: identical, and the committed bytes were kept

`fut_micro_flow_5m.csv.gz` (283,248 rows) and `fut_micro_flow_rolls.csv.gz` decompress to the same
sha256 before and after (`10ea4ce1…` and `43c2a40a…`), so the committed blobs were restored rather
than churning 12 MB of binary for identical content — the same decision D520 recorded for the
sessions fixture. What is committed from that rebuild is the **meta** (re-gated) and the **builder**.
This was the expected outcome: the fixture spans one year, 2025-09 to 2026-09, on ES/MES/NQ/MNQ, and
a reuse needs a contract to die and its slot to be reissued inside the same file.

## 3. Where the definition lives, and why it is not one import

`build_fut_day5m` and `build_fut_open_interest` **import** `ids_of` from `build_fut_breadth_hourly`.
The other two keep a local copy, each saying why in its own docstring:

- **`build_fut_micro_flow`** — the breadth builder's `ROOTS` has no MES or MNQ. Importing its
  `ids_of` here would silently drop every micro contract, which is half of this fixture's purpose.
- **`build_fut_index_1m`** — its roots include RTY, which the breadth fixture gates differently.

A copy that says what it would break if shared is safer than an import that is silently wrong for
half its rows.

## 4. Index 1m: 16,077 foreign bars ingested, **not one of them in the fixture**

This is the D520 outcome again, and it took a full rebuild to earn it.

**The metadata could not settle it.** A pre-check over all 26 ohlcv-1m files
([`temp/index1m_map_precheck.py`](../../temp/index1m_map_precheck.py), 20 min) found **0 index ids
ever reused for a different INDEX contract** — the flat dict never confused `ESH5` with `ESM5` — but
**712 non-index mapping windows whose id also holds an index window in the same file**, in 25 of 26
files, peaking at 106 in 2021. Those rows would be ingested wearing an index label. Whether any
*survives* depends on the front-month vote, and no reading of the mapping table answers that.

| | flat map | windowed map |
|---|---|---|
| archive rows read | 1,022,999,573 | identical, file by file |
| RTH rows ingested | **7,009,518** | **6,993,441** |
| difference | — | **16,077 foreign bars, 0.2294 %**, in 18 of 26 files |
| worst single file | — | 2022-01: 4,921 extra of 346,468 (1.42 %); 2026-01: 3.25 % |
| `fut_{ES,NQ,YM,RTY}_rth_1m.csv.gz` | — | **byte-identical** (decompressed sha256, all four) |
| `fut_index_sessions.csv.gz`, `fut_index_rolls.csv.gz` | — | **byte-identical** |

**The front-month-by-volume rule threw away all 16,077.** A foreign bar carries whatever index symbol
the flat dict happened to leave on its id; to reach the fixture that symbol would have to *win* its
root's daily volume vote, and a stray instrument's few hundred lots never outvotes a front month
trading hundreds of thousands. That is the same mechanism that protected the sessions panel in D520
and the open-interest **front** column in §1 — and precisely why the **total** column in §1, which
has no volume filter in front of it, was the one that moved.

As in §2 the committed blobs were restored rather than re-committed; the meta (re-gated) and the
builder are what change. **All 173 gate scalars are identical**, G1 through G5 on all four roots —
including RTY's standing G4 failure (open-to-close correlation with IWM 0.98985 against a 0.99 bar,
`all_gates_pass: False` in the committed meta too). That failure predates this work, is untouched by
it, and is why `fut_RTY_rth_1m.csv.gz` is still uncommitted; it is not in scope here.

### 4a. The rebuild needed the builder parallelised first, and that had to be proved harmless

At 1.02 billion rows the builder was single-process and projected **~20 min**. It now uses a `Pool`
over files like the other three builders — fed largest-file-first, results **re-sorted into archive
order** by `collect()`, because `assemble` de-duplicates `(root, day, hhmm)` after a non-stable sort
and a reshuffled input could silently keep a different bar. Measured: **6.2 min on 6 workers, 5.67×,
94 %**.

That made the rebuild a two-variable change, which would have confounded the diff. So
`--verify N` runs the serial loop and the pool over the N smallest real files and asserts equality
with `check_exact=True` at three levels — per-file frames, the concatenated frames, and the assembled
front-month bars. On 0.49 GB: **258,288 bar rows, 2,975 day-volume rows and 181,824 assembled bars
identical**, in 1.3 min. The parallelism is a speed change only, so the byte-identical fixture above
is a statement about the mapping and nothing else.

## 5. What is now true of the data layer

| builder | mapping |
|---|---|
| `build_fut_breadth_hourly.py` | windowed (original) |
| `build_fut_sessions_hourly.py` | windowed (D520) |
| `build_fut_day5m.py` | windowed (imports the breadth definition) |
| `build_fut_open_interest.py` | **windowed (D521)**, imports the breadth definition |
| `build_fut_micro_flow.py` | **windowed (D521)**, local copy, micros |
| `build_fut_index_1m.py` | **windowed (D521)**, local copy, RTY |

**No builder in the repository now labels a bar from a flat `{instrument_id: symbol}` dict.**

Each ported builder's selftest gained a check that *can fire*: a reused id must read one contract
inside its first window and another inside its second, the flat dict's surviving label is asserted to
disagree with at least one of them (so a silently-correct flat dict could not pass it), the bar in
the gap between windows is dropped, and two overlapping windows raise.
