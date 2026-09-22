# D609 — The panel loader becomes a chokepoint, and seven roots stop being 100x wrong

**Status:** Committed
**Date:** 2026-09-22
**Category:** Data
**Source:** Round 4 of the deposit infrastructure. Shared item 2 of
`docs/internal/DEPOSIT_INFRASTRUCTURE_TRACKER.md` — *"Vault guard. Loader refuses 2025-03-01 to
2026-09-18 unless a frozen model and one-shot open flag exist"* — whose helpers D594 built and
whose **loader** nothing had. Builds on D594 (`filter_before`, `assert_none_at_or_after`,
`window_record`, `refuse_without_word`, `sha256_file`), D536/D538 (the manifest and the
honest-skip rule), D519 (`build_fut_breadth_hourly.py`'s notional test), D591 (the cost table),
D604 (the impact table, which RECORDED the seven-root disagreement and resolved none), D606 (a
runner is compiled, never imported), D550/D551 (newline pinning), D48 (raise loudly) and R16
(exact reproduction). Supersedes, in writing, §6(iii) of
`tests/golden/test_futures_costs_ledger.hand.txt` and the *"Six roots' `tick_usd` are flagged,
not corrected"* paragraph of
[D591](D591-futures-cost-bricks-and-the-reconciled-cost-table.md).

## Decision

Two halves, and they share one cause: **a fact about a data file that lived in whichever call
site happened to need it.** Part A is the column a reserved-slice cut reads; part B is the
multiplier a dollar figure is computed with. Both were retyped per site, both were wrong
somewhere, and neither had a place to be right once.

No runner is migrated. No strategy return is computed. No fixture row dated 2024-01-01 or later
is read for any return, and the one panel that is entirely inside the reserved slice is read
through the new door and returns **zero rows**.

---

# Part A — the loader chokepoint

## 1. Why a chokepoint, and the measurement that says one was missing

D594's module docstring names its helpers as the thing *"a new runner can import instead of
retyping"*. Measured on 2026-09-22: **no runner imports any of them.** The importers are their
own tests, `scripts/freeze.py`, and `validation/track3.py`'s `assert_frozen`. Zero runners.

Against that: **232 raw `read_csv` / `read_parquet` calls across 122 scripts** (0 in `src/`);
**26 scripts reference `RESERVED_FROM`**, of which four define it at top level
(`run_d555_tsmom_replication.py:43`, `stage0_d577_cl_hedging_flow_p9.py`,
`stage0_d580_funding_clock.py`, `stage0_d581_gamma_close.py:230`) and the rest take it from
`run_d555` by hand (`PRIMARY, LONG, RESERVED_FROM = R55.PRIMARY, R55.LONG, R55.RESERVED_FROM`,
`run_d565_ng_winter_spread.py:43`); and **seven `--principals-word` runners** hand-roll the
refusal that `frozen.refuse_without_word` (`frozen.py:972`) prints.

*(The brief for this record said "nine RESERVED_FROM runners". It is 26 files, 25 of them
runners. The number had grown through the basis-momentum programme and nobody had recounted.)*

**A helper nobody calls is not a guard.** `src/backtest_framework/data/panels.py` is the call
site: one function a runner uses INSTEAD of `pd.read_csv`, which **cannot be called without
naming a cut**, and which carries the three layers, the manifest digest and the window record
on every read.

## 2. `load_panel`, and the two things the helpers could not know

```
load_panel(name, *, reserved_from, word=False, usecols=None, instruction=None, read_log=None)
    -> LoadedPanel(name, path, frame, record, sha256, status, spec)
```

| | |
|---|---|
| **`reserved_from` has NO DEFAULT** | see §5 |
| which column | `panel_catalogue.py`, hand-declared from a read of all 126 manifest panels' own headers |
| which file, and is it the file | `data/data_manifest.json`, re-hashed on every read with `frozen.sha256_file(text_normalise=False)` — bit-identical to `build_data_manifest.py:63` and `run_d555:79`, and the only hashing route here |
| blocked (`word=False`) | `filter_before` → `assert_none_at_or_after` → `window_record`, in that order, unchanged |
| opened (`word=True` + `instruction`) | the panel is read WHOLE, then the blocked read runs AGAIN, independently, and the opened frame's rows before the cut must equal it |
| asked to open without the word | `PanelRefused`, carrying `refuse_without_word`'s own message verbatim |
| `word=True`, no instruction | raises: the principal's words are what make an opening a record |
| `usecols` without the date column | raises — a projection that drops it leaves the guard nothing to read |
| `read_log` | one JSON line per read, LF-pinned; **writes nothing by default** |
| `LoadedPanel.windows_update(existing)` | MERGES the six keys into a runner's `"windows"` block and raises rather than overwriting |

**The opened path reads the file twice, deliberately.** `run_d574:106-108` asserts the opened
frame's in-sample rows equal the blocked loader's on `["root","day","close"]`; this does it on
the WHOLE frame, so a column the author did not think to list cannot differ unnoticed. Checking
a filter with the same expression that built it proves only that the expression is
self-consistent, which is D594's own reason for keeping layers 1 and 2 apart.

**`windows_update` merges because replacing would delete evidence.** `run_d555:848-850` writes a
`"windows"` block with keys `primary, long, reserved_from, sessions_primary, sessions_long,
month_ends`. The intersection with `window_record`'s six is exactly `{reserved_from}`, and both
say `2024-01-01`, so the merge is 6 + 6 − 1 = **11 keys** and the five the pre-registration names
survive. A second read at a different cut raises.

## 3. The catalogue, and the four traps that make a table beat a convention

`panel_catalogue.py` carries **one row per manifest panel, all 126**, with `name`, `path`,
`date_col`, `date_format`, `reader`, `wrong_cuts` and `dtype_hints`. Counts, all asserted:

| | |
|---|---|
| date column spellings | `day` 59, `timestamp` 29, `session` 5, `filing` 3, `ref` 3, `date` 2, `avail_date` 2, `report_date` 1, `date_entry` 1, `filed` 1, `period` 1 — **eleven spellings over 107 panels**, four of them on one panel each |
| formats | `iso_day` 76, `iso_ts` 29, `date32` 1, `year_prefix` 1, `none` 19 |
| readers | csv 103, npz 16, parquet 7 |
| panels with a declared wrong cut | 20, over 17 distinct column names |

**`wrong_cuts` names the columns that must never receive `reserved_from`**, and the four that
motivated it are silent failures in both directions:

1. `fut_micro_flow_5m.bucket_start` is `2025-09-10 20:00:00` on session `2025-09-11` — the prior
   EVENING, because Globex opens at 18:00 ET. A cut on it keeps the first reserved session's
   overnight leg.
2. `fut_btc_1m.ts_utc` is the same shape (`2017-12-17T23:00` on day `2017-12-18`).
3. `fut_es_options_eod.expiry_date` is in the FUTURE of its `session` — wrong the other way, and
   just as invisible.
4. `prev_day`, on eight session panels, is one session EARLIER than `day`: a cut on it lets
   exactly one reserved session through.

Plus a family of KNOWN-AT columns — `published_at_et`, `published_et`, `oi_pub_et`,
`release_date_nominal`, `ref_session` — which say when a number was published, not which session
it belongs to. They are listed so the loader refuses to be pointed at them, rather than left out
and therefore available.

**`date32` is its own trap.** `D2_US_factors_SAS.parquet`'s `date` is an arrow `date32[day]`, so
pandas hands back a datetime and `frozen._day_strings` REFUSES it rather than coercing — because
a coerced `datetime64` stringifies to `2024-01-01T00:00:00.000000000`, which sorts **after**
`2024-01-01`, so the row at the cut survives the filter that exists to drop it. The loader does
that conversion at the door, once, exactly as frozen's error message prescribes.

**Nineteen panels declare no date column and are REFUSED, not waved through** — sixteen `.npz`
arrays, `d506_cells`, `d508_quintiles` and `D2_sas_vs_py_summ_stats.parquet`. `date_col=None` is
the declaration that a cut cannot be applied; a loader that returned them unfiltered would be a
chokepoint with a hole in it.

## 4. The finding the loader made within a minute of first running

**`data/fixtures/hkm_factors.csv.gz` is two panels stacked under one `period` column.** It was
declared `yyyymm` on the strength of its first row, `197001`, which is what the brief said it
was. The file holds **664 MONTHLY rows keyed `YYYYMM` and 220 QUARTERLY rows keyed `YYYYQ`** —
`19701` is 1970 Q1, five characters — told apart by the `freq` column. The loader's fixed-width
invariant fired on the first real read.

Against a `202401` cut the mixed-width lexical comparison happens to give the right answer for
every row in this file. That is a coincidence of where the digits fall, not a property. The
panel is declared **`year_prefix`**: the comparison key is the leading four digits, the cut must
be 1 January, and the two frequencies are compared on the one field they genuinely share. A cut
the format cannot express raises rather than rounding, because rounding moves the cut by up to a
year in a direction nobody chose.

*(The other non-ISO panel the brief named, `oecd_ir3tib_monthly.csv` with `period = 2000-01`, is
a plain `.csv` and therefore **not a manifest panel** — `build_data_manifest.py:57` selects by
bulk suffix. `yyyy_mm` is supported and exercised on a synthetic panel instead.)*

## 5. What this record does NOT do, and the seal date it refuses to pick

**No runner is migrated.** The migration set is written down so a later record migrates a named
list rather than whatever it notices: the 26 `RESERVED_FROM` scripts of §1, and the seven
`--principals-word` runners `d503_forward_book.py`, `run_d473_downleg_component.py`,
`run_d490_range_reversion.py`, `run_d498_k8_and_second_clocks.py`,
`run_d566_joint_forward_read.py`, `run_d574_basis_momentum_forward.py`,
`run_d578_sd_net_short_forward.py`.

**The read log has no committed home.** `read_log=` appends wherever the caller points it and the
default is to write nothing.

**IT PICKS NO SEAL DATE, AND THE OMISSION IS SHARPER THAN D594'S.** The deposit seals
2025-03-01 → 2026-09-18; this repository reserves 2024-01-01 onward; and
`data/fixtures/fut_book_depth_1m.csv.gz` — D604's own depth panel — spans 2026-08-11 to
2026-09-09, which is **inside the deposit's vault window AND after this repository's seal**.
`depth_bar` (`costs/futures_impact.py:361`) handles it by passing `reserved_from = day`, i.e. by
asserting nothing. Read through this door at `reserved_from="2024-01-01"` the panel returns
**zero rows, with `first_session_read` None** — correct, and useless to anyone who wanted the
depth. That is the case that proves a default would be a wrong answer for someone, and the
reconciliation is the principal's decision, not a library's.

## 6. The honest-skip rule moved, and it moved because it had been retyped twice

`tests/conftest.py:39-115` held the present / absent-but-listed / absent-and-unlisted
distinction. It is now `panels.panel_status`, with `absent_reason` and `unlisted_message`
carrying the two sentences verbatim; `tests/conftest.py` is a four-line adapter. It moved
because two other places had retyped it by hand:

* `scripts/futures_impact_table.py:293` — a hard-coded sentence that said *"It is one of D536's
  untracked bulk panels"* whether or not the manifest listed the file, which for a renamed
  artefact or a typo'd constant is a false explanation attached to a real failure. It now calls
  `panel_status` and says which.
* `tests/unit/test_fut_book_depth.py:58-74` — a transitional double-skip whose first branch went
  dead the moment the manifest listed `fut_book_depth_1m.csv.gz`. Deleted; the listing is now
  asserted, so a missing row is loud.

**The skip count did not move.** `uv run pytest -q tests/unit/test_fut_book_depth.py
tests/unit/test_futures_impact.py` reported **113 passed, 0 skipped** before the refactor and
113 passed, 0 skipped after.

---

# Part B — the seven-root multiplier fix

## 7. What was wrong, and since when

`data/fut_specs_from_definition.json` entered the repository in **`7d03311`, 2026-09-13** — its
only commit, and the sole author of the file — by `scripts/probe_definition_specs.py --specs`.
That commit's own subject line is *"plus the cents/percent trap that would have silently made
every grain and livestock root untradeable"*, and the trap it names is the one it shipped: the
formula divides by 100 when `unit_of_measure == "USD"` and never otherwise. **The probe's
docstring says that rule is not the rule** — *"`HG` and `ZL` share `UOM == "LBS"` and differ by a
factor of 100 ... the decidable test is the NOTIONAL"* — and the code never caught up with the
docstring. **The trap was written down, and then fallen into, in one commit.** Nine days, D591
and D604.

| root | uom | committed `tick_usd` | truth | |
|---|---|---:|---:|---|
| ZC, ZS, ZW | BU | 1250.0 | **$12.50** | cents per bushel, never divided |
| ZL | LBS | 600.0000000000001 | **$6.00** | cents per pound |
| LE, HE | LBS | 1000.0 | **$10.00** | cents per pound |
| SR3 | USD | 0.0625 | **$6.25** | divided when it should not have been: `uom_qty` is already $/point |

Six 100x high, one 100x low. **Every one of the seven has `known_tick_usd: null`** — nothing had
ever verified them against CME. `ZM` (uom TON) agrees and is why the count is seven, not eight.

**`Future.__post_init__`'s product identity could not catch this, and that is structural.** It
asserts `usd_per_point * tick_points == tick_usd`; `from_specs` DERIVES `usd_per_point` as
`tick_usd / tick_points`, so the identity holds by construction at any scale. Measured:
`Future(root="ZC", tick_points=0.25, usd_per_point=5000.0, tick_usd=1250.0)` constructs without
complaint. `known_tick_usd` was in the file and was never read.

## 8. The fix reads a number, it does not type one

The corrected value is not invented. `data/fixtures/fut_breadth_hourly.meta.json` has carried
`tick_usd_full_contract` per root **since D519**, decided by
`build_fut_breadth_hourly.py:decide_scaling` — a NOTIONAL test on the observed price, where
exactly one of {undivided, /100} must land in `[10,000, 800,000]` and **ambiguity raises**. The
builder was reading the wrong field of the wrong file.

`probe_definition_specs.py --rescale` compiles `decide_scaling`, `NOTIONAL_LO/HI` and `MICRO_OF`
out of the breadth builder's own committed source (D606's pattern: compiled, not imported) and
adds four keys per root — `tick_usd_raw_formula` (the undivided product), `scaling_divisor`,
`scaling_reason`, `tick_usd_full_contract`. The 36 breadth roots get the price from the breadth
meta's own `last_price`; the five micros the breadth fixture does not carry (MES, MNQ, M2K, MYM,
MBT) **inherit their parent's divisor**, exactly as `specs_for` does, because a micro quotes its
parent's price and its own notional is too small for the band.

**Known-answer first, and it is what makes this checkable rather than asserted:**

* all **17** roots with a non-null `known_tick_usd` reproduce it exactly;
* the scaling agrees with the breadth meta's committed `scaling_divisor`, `scaling_reason` and
  `tick_usd_full_contract` on **all 36** shared roots;
* the divisors are exactly `{ZC, ZS, ZW, ZL, LE, HE: 100, SR3: 1}` and
  `scaling_corrections == ["HE", "LE", "SR3", "ZC", "ZL", "ZS", "ZW"]`.

**The file was transformed, not regenerated, and the reason is stated rather than assumed.** A
full `--specs` rebuild re-reads 166 MB of DBN under the system python and would still have to
reach for the breadth meta, because the NOTIONAL test needs an observed PRICE and the
`definition` schema carries none. Everything added is a function of the committed table and the
committed breadth meta. The same `rescale()` is wired into `do_specs()`, so a future regeneration
from the archive produces the same keys instead of silently dropping them.

**`tick_usd` is left exactly as it was written.** D591's record and this hand file quote it; a
record's evidence is not edited under it. `Future.from_specs` reads `tick_usd_full_contract` and
**raises** on an entry that lacks it, so no reader reaches the old number through the instrument.

**And a check that cannot be satisfied by construction was added**: `tick_usd_full_contract`
against `known_tick_usd` at 1e-9 relative, where one exists. Unlike the product identity, it
compares the one number that matters against a value from a different source for the same root.

## 9. Which committed numbers moved: two artefacts, no study result

**`data/futures_costs.json` (D591).** Diffed value by value: exactly **seven roots moved**, and
nothing else.

| root | `tick_usd` | `usd_per_point` | D556 min-size round trip |
|---|---|---|---|
| ZC, ZS, ZW | 1250.0 → **12.5** | 5000.0 → **50.0** | $1,256.00 → **$18.50** |
| LE, HE | 1000.0 → **10.0** | 40000.0 → **400.0** | $1,006.00 → **$16.00** |
| ZL | 600.0000000000001 → **6.000000000000001** | 60000.0 → **600.0000000000001** | $606.00 → **$12.00** |
| SR3 | 0.0625 → **6.25** | 25.0 → **2500.0** | $6.0625 → **$12.25** |

Those are the figures §6(iii) of the hand file itself said they ought to be. Every other root's
tick, multiplier and published round trip is byte-identical, and the builder's `--selftest`
reproduces NQ 3.50, ES 4.25, CL 4.00, SI 8.00, ZN 21.625, ZB 37.25 and ZF 13.8125 unchanged.
**D591's table was contaminated in seven roots nobody had yet charged** — no study in this
repository has ever priced ZC, ZS, ZW, ZL, LE, HE or SR3 off it.

**`data/futures_impact_params.json` (D604).** Only `multiplier_disagreements` changed: seven rows
to `[]`. Every measured number — ADV, σ, notional, `usd_per_point` — is unchanged, because that
builder always used the breadth value. D604 recorded the seven and resolved none, by its own
statement that *"the fix belongs in the spec file, not here"*. This is that fix.

**Nothing published moved, and it is checkable.**
`data/d555_tsmom_replication.json#dollar_book.usd_per_point` already read ZC 50, ZS 50, ZW 50,
ZL 600.0000000000001, LE 400, HE 400, SR3 2500 — the corrected values — because `run_d555` read
the breadth meta and not the definition file. Its bytes are asserted unchanged (LF-pinned sha256
`7811e322bc6e6cb15d3903e2b3c38721a76b265f448710eb014b47e81906fc61`), and if the correction had
moved a published result that is where it would show.

## 10. The runtime exposure, and the test that used to pass while both sides were wrong

`costs/futures_bricks.py:253` builds a `Future` out of the cost table, so
`FuturesRoundTrip.from_table("ZC").instrument.tick_usd` was **1250.0** yesterday and is **12.5**
today; `Future.from_specs("SR3").tick_usd` was 0.0625 and is 6.25.

`tests/unit/test_futures_costs_table.py:test_tick_usd_agrees_with_the_instrument_the_specs_file_builds`
is why this had to be a two-sided change: **both sides read the same wrong field, so it agreed at
1250.0**, and correcting either alone would have turned it red. Both moved in one record, which
is why it is still green and why green now means something it did not mean before. The three
pinning tests are updated and the empty `multiplier_disagreements` list is pinned **beside the
seven corrected `usd_per_point` values**, because the list is built by iterating the 36 breadth
roots and a table that had LOST those seven would also report `[]`.

---

## Gates

| | |
|---|---|
| `tests/unit/test_panels.py` | **153** (126 of them the per-panel header check, parametrised; 27 others) |
| `tests/golden/test_panels_ledger.py` + `.hand.txt` | **9**, hand file written first |
| `tests/property/test_panels_property.py` | **7**, `derandomize=True, max_examples=40, deadline=None` |
| `scripts/panel_catalogue_check.py --selftest` | 12 numbered steps, the good case before the break in every pair |
| `scripts/panel_catalogue_check.py --audit` | 126 panels, **0 disagreements**, under both interpreters |
| added to `tests/unit/test_future_instrument.py` | **+5** (41 total) |
| added to `tests/unit/test_futures_costs_table.py` | **+3** (46 total) |
| added to `tests/golden/test_futures_costs_ledger.py` | **+1**, one rewritten (41 total) |
| `tests/unit/test_futures_impact.py` | the disagreement test became two (93 total) |
| `scripts/futures_cost_table.py --selftest` | PASSED after regeneration |
| `scripts/futures_impact_table.py --selftest` | re-derived == committed, byte for byte, 14 s |

**The golden reproduces D555's own published number (R16).** The loader's digest for
`fut_breadth_hourly.csv.gz` is
`c64dfe70211242368772da005e05e11ed2f2e779e6599d0e0a6a2bbabee355de` — the manifest's `sha256` AND
`data/d555_tsmom_replication.json#fixture_sha256`, three routes to one value. And the row counts
reconcile through the runner's own drop counts, exactly:

```
load_panel rows                        140,814
- attrs["rows_dropped_no_close"]        22,531
- attrs["rows_dropped_weekend_stub"]         69
  = run_d555.load_fixture() rows       118,214     (118,214 == 118,214)
frame["day"].max()   both routes    '2023-12-29'
```

`load_panel` cuts and nothing else; dropping a non-session is a study's judgement about its own
fixture, not a property of the file, so the two counts are NOT asserted equal.

## Disagreements and what is NOT resolved

1. **The brief's date-column survey was of the fixtures, not of the manifest.** It named
   `eia_weekly_stocks`, `wasde_grains_su`, `perp_funding`, `perp_open_interest_daily`,
   `oecd_ir3tib_monthly` and `xle_xop_*` as panels with one-off date columns. None of them is a
   manifest panel — all are plain `.csv`, below `build_data_manifest.py`'s bulk-suffix threshold.
   Conversely the manifest holds 16 `.npz` arrays and ~45 `dNNN_*` study artefacts the survey did
   not mention. The catalogue follows the manifest, which is what the loader checks digests
   against.
2. **`reader` and `date_format` each needed a value the brief's enum did not have** — `npz` and
   `none`, for the 19 panels with no date column, and `year_prefix` for the stacked-frequency
   panel of §4. Both are additions, not substitutions.
3. **`PanelSpec`'s field order is `(..., reader, wrong_cuts, dtype_hints)`**, not the brief's
   `(..., reader, dtype_hints, wrong_cuts)`. `wrong_cuts` is set on 20 panels and `dtype_hints`
   on four, so the commoner one is positional.
4. **The seal date is not reconciled and this record does not reconcile it.** §5. The depth
   panel reads as zero rows and says so rather than choosing.
5. **The read log's home is deferred.** It works and nothing writes to it by default.
6. **No numbered deposit test is claimed.** Ledger unit test 64 — *"Vault guard: the loader
   raises on any date from 2025-03-01 to 2026-09-18 unless `FROZEN_VAULT.json` exists and the
   vault-open flag is set"* — is the one this loader half-serves, and it is **already claimed by
   D594** (`tests/unit/test_frozen.py:398`). `load_panel` refuses an opening without the word; it
   does not require a frozen model, and it does not know the deposit's window. Claiming 64 here
   would be claiming the half that is not built.
7. **`.parquet` schemas cannot be read in the venv** (no pyarrow; `futures_impact_table.py`
   already runs under the system python for this reason). The seven parquet rows are checked by a
   FOOTER SCAN instead — the file's own trailer, length-prefixed and magic-checked, searched for
   the thrift-encoded column name. That confirms a name and cannot list them, and it is not
   nothing; a name that is not a column does not match, which is asserted. Under the system
   python the schema is read outright, and both invocations report 0 disagreements. **No test
   skips on this**, which is why the venv fallback exists at all.
8. **`scripts/d508_micro_crossing_tbbo.py:98` still reads the definition file's `tick_usd`** as a
   fallback. Its roots are the index, metal and FX micros and their parents — none of the seven —
   so nothing it published is affected, and it is a frozen runner that produced a published
   number. Left alone, named here so the next reader knows.
9. **`tick_usd` in the definition file is still the wrong number for those seven.** It is kept
   because D591 and D604 quote it, and it is now flanked by `tick_usd_raw_formula`,
   `scaling_divisor`, `scaling_reason`, `tick_usd_full_contract`, a per-root
   `tick_usd_superseded: true`, a top-level `scaling_rule` that says *"Read
   tick_usd_full_contract"*, and a `from_specs` that raises without the corrected field.
10. **Neither `data/futures_costs.json` nor `data/futures_impact_params.json` was re-derived on a
    machine other than this one.** Both builders' `--selftest` compares the committed bytes to a
    fresh build, and both pass here; nothing has run them on the CI image.

## Draft `docs/data-available.md` paragraph (for the integrator)

> **The definition snapshot's scaling, corrected ([D609](decisions/D609-the-panel-loader-chokepoint-and-the-seven-root-multiplier-fix.md), 2026-09-22).**
> [`fut_specs_from_definition.json`](../data/fut_specs_from_definition.json) now carries
> `tick_usd_raw_formula`, `scaling_divisor`, `scaling_reason` and **`tick_usd_full_contract`**
> per root, the divisor decided by the same NOTIONAL test
> [`build_fut_breadth_hourly.py`](../scripts/build_fut_breadth_hourly.py) has used since D519.
> **Read `tick_usd_full_contract`, never `tick_usd`:** the original field divides by 100 on
> `unit_of_measure == "USD"` alone and is 100x high on ZC, ZS, ZW, ZL, LE, HE (cents per bushel
> or per pound) and 100x low on SR3, all seven of them with `known_tick_usd: null`. It is kept
> unchanged because D591 and D604 quote it. `Future.from_specs` raises on an entry without the
> corrected field. `data/futures_costs.json` and `data/futures_impact_params.json` were rebuilt:
> seven roots' tick and multiplier moved in the first, `multiplier_disagreements` went from seven
> rows to `[]` in the second, and no measured number and no published study result moved
> (`d555_tsmom_replication.json`'s dollar book already held the corrected multipliers).
>
> **Reading a panel through the door.**
> `backtest_framework.data.panels.load_panel(name, reserved_from=...)` is the one loader that
> knows which column a cut applies to — `panel_catalogue.py` declares it for all 126 manifest
> panels, along with 17 columns that must NEVER receive the cut (`prev_day`, `bucket_start`,
> `ts_utc`, `expiry_date`, the `published_*` family) and the 19 panels with no date column at
> all, which it refuses. `reserved_from` has no default. `scripts/panel_catalogue_check.py
> --audit` re-reads every header and reports disagreements; `--selftest` proves the guards fire.

## CHANGELOG bullet (draft, for the integrator)

- **D609 — the panel loader chokepoint, and seven roots that were 100x wrong.** *Part A:*
  `data/panels.py` and `data/panel_catalogue.py` — one door onto every bulk panel, with
  `reserved_from` as a keyword argument that **has no default**, D594's three layers in order,
  the manifest sha256 re-derived on every read, and a catalogue declaring the date column for
  **all 126 manifest panels** plus the 17 columns that must never receive the cut
  (`fut_micro_flow_5m.bucket_start` and `fut_btc_1m.ts_utc` are the prior EVENING of their
  session; `fut_es_options_eod.expiry_date` is in the future; `prev_day` is one session early on
  eight panels). Opening on the principal's word re-runs the blocked read and compares the whole
  frame, making `run_d574:106-108` free and generic. The honest-skip rule moved out of
  `tests/conftest.py` into `panel_status` and the two places that had retyped it by hand now call
  it; **the skip count did not change** (113 passed / 0 skipped either side). **No runner is
  migrated** — the 26 `RESERVED_FROM` scripts and the seven `--principals-word` runners are
  listed as the migration set — and **no seal date is picked**: D604's `fut_book_depth_1m` spans
  2026-08-11..09-09, inside the deposit's vault window AND after this repo's seal, and reads as
  zero rows rather than as a default. Found on the first real read:
  **`hkm_factors.csv.gz` is two panels stacked**, 664 monthly `YYYYMM` rows beside 220 quarterly
  `YYYYQ` ones, so it is cut on the year the two share. *Part B:* the definition snapshot's
  `unit_of_measure == "USD"` divide is wrong on seven roots — ZC/ZS/ZW/ZL/LE/HE 100x high,
  SR3 100x low, all seven with `known_tick_usd: null`, and `__post_init__`'s product identity
  cannot catch it because `usd_per_point` is derived from `tick_usd`. `tick_usd_full_contract`
  added per root by the breadth builder's own NOTIONAL test (17 known answers reproduced, 36
  roots agreeing with the breadth meta); `Future.from_specs` reads it and raises without it;
  `futures_costs.json` and `futures_impact_params.json` rebuilt — **seven roots' multipliers moved
  and `multiplier_disagreements` went to `[]`; no measured number and no study result moved**, and
  `d555_tsmom_replication.json`'s bytes are asserted unchanged. 179 tests (unit 161, golden 10,
  property 7). No strategy return computed; no fixture row from 2024-01-01 read for any return.

## Deposit unit tests claimed

**None.** See disagreement 6.
