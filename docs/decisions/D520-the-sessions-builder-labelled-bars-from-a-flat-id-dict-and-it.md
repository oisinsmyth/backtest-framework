# D520 — the sessions builder labelled bars from a flat id dict; it was ingesting 229,206 foreign bars a decade of archive, and **not one of them reached the panel**

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D520-the-sessions-builder-labelled-bars-from-a-flat-id-dict-and-it-was-ingesting-a-quarter-million-foreign-bars-that-never-reached-the-panel.md`. The H1 above is the full title.*

*2026-09-13. Data layer only: no study, no signal, no edge. Nothing is admitted to any book or
ledger (R15). Fix, rebuild and audit of `scripts/build_fut_sessions_hourly.py` and
`data/fixtures/fut_sessions_hourly.*` — the D467 fixture, nine roots, with RTY added by D472.*

---

## The one-line answer

**The defect was real, it was bigger than the CL slot-reuse case that motivated it, and the
published nine-root panel is BYTE-IDENTICAL after the fix.** `fut_sessions_hourly.csv.gz` hashes
the same before and after; the only change anywhere is **two rows removed from
`fut_sessions_rolls.csv.gz`**, and those two rows turn out to be the "holiday artefact" D467's own
G2 ADDENDUM wrote up as a property of the euro market.

| | |
|---|---|
| bars the old flat dict accepted | **77,151,155** |
| of those, **claimed by no validity window of their instrument_id** | **229,206 — 0.297%** (4.31% on the worst single file) |
| of those, given the wrong OUTRIGHT symbol of one of our roots | **0** |
| session rows: gained / lost / changed | **0 / 0 / 0** |
| price cells changed (138 columns × 33,387 rows) | **0** |
| volume and bar-count cells changed | **0** |
| label cells changed (`contract`, `front_prev`, `same_front`, `prev_day`, `bars`) | **0** |
| roll-table rows removed | **2**, both 6E, 2021-12-24 and 2021-12-26 |
| gate verdicts changed | **none**; every G1–G5 scalar identical to six decimals except 6E's G2 roll count (43 → 42) and artefact count (1 → 0) |

Audit artifact: [`data/d520_fixture_diff.json`](../../data/d520_fixture_diff.json), from
[`scripts/d520_fixture_diff.py`](../../scripts/d520_fixture_diff.py). The old fixture was checked to
be the committed build before diffing — `git show HEAD:data/fixtures/fut_sessions_hourly.csv.gz`
hashes `1e4ec83a…`, identical to the copy in `temp/d520_old/` (R16: name the build).

**`fut_sessions_hourly.csv.gz` is deliberately NOT re-committed.** The rebuild's CSV is
byte-identical (decompressed sha256 `f6d95720…` both ways) and only the gzip container's header
differs, so the committed blob was restored rather than churning 9 MB of binary for zero content.
What is committed from the rebuild is the **rolls table** (2 rows fewer), the **meta** (the new
`id_rule`, the per-file `flat_dict_audit` and `multi_window_symbols`, re-run gates) and the
**builder**. If a future reader wants the rebuild's own bytes, `--build` reproduces them in 8.9 min.

---

## 1. The defect, and the part of it I did not expect

`ids_of` built `{instrument_id: (root, symbol)}` from `store.metadata.mappings` and **threw away
each mapping's `start_date`/`end_date`**. Two things in the archive break that, and the second is
the one that supplies almost all of the exposure.

**(a) CME reuses the single-digit-year symbol slot** the moment a contract expires, and **also
rotates a live contract onto a new instrument_id**. Both happen inside one year file:

    CLN9   117678   2019-01-01 .. 2019-06-23     July 2019 crude
           178362   2019-06-23 .. 2020-01-01     July 2029 -- the slot REUSED after expiry
    CLK8   545967   2019-01-01 .. 2019-06-09     May 2028
           454907   2019-06-09 .. 2020-01-01     May 2028 again -- the same contract, a NEW id

Measured over all 26 files: **27 symbol-instances carry more than one id, every one of them CL** —
1 each in 2011, 2012, 2013 and 2017, 5 and 2 in the two 2018 files, and **16 in 2019**. The other
eight roots of this fixture are clean in every year. That matches what the breadth builder recorded
and it is the case D465 already paid for.

**(b) The larger half: an instrument_id that is one of our outrights in one window is SOMETHING
ELSE in another, and that something else is usually not a future at all.** `ids_of` only ever
wrote a window for a symbol matching the outright regex, so a foreign symbol contributed no window
— and the flat dict, keyed on the id alone, therefore accepted **every bar that id ever carried**
and stamped it with our label. Measured by
[`scripts/d520_contaminant_anatomy.py`](../../scripts/d520_contaminant_anatomy.py): **58 of the 2022
file's 242 ids and 108 of the 2021 file's 271 carry more than one symbol**, and the affected labels
span all nine roots.

**Named, on the worst file (`glbx-mdp3-20220101-20220816`, 153,707 foreign bars, 4.31% of what the
old build ingested there) —** from
[`scripts/d520_contaminant_anatomy.py`](../../scripts/d520_contaminant_anatomy.py):

| the label the old build gave it | bars | what it actually was | its price | the real root's price |
|---|---:|---|---:|---:|
| **6EF3** | 79,479 | `M6AM2` — Micro AUD/USD | 0.683 – 0.767 | 6E ≈ 1.02 |
| **GCX2** | 60,755 | `E7M2` — E-mini EUR/USD | 1.036 – 1.154 | GC ≈ 1,800 |
| **NQU3** | 6,836 | `J7H2` — E-mini JPY | 0.00852 – 0.00882 | NQ ≈ 12,000 |
| **NQM3** | 3,404 | `CLTH2` — a crude SPREAD | **−10.00 – +7.00** | NQ ≈ 12,000 |
| **6EX2** | 2,664 | `NGTN2` — a gas SPREAD | **−10.00 – +10.00** | 6E ≈ 1.025 |
| ZN, ZB, YM, RTY tails | 10 – 279 each | options (`EW3J2 C4770`, `ZS1K2 C1980`, …) | 0.05 – 766.75 | — |

**A Nasdaq contract priced at 0.0086 and a euro contract priced at −10.** Four orders of magnitude
and a negative price, and **G1 — the print-jump gate — cannot see any of it**, because those
contracts were never the front month, so their bars never entered a session row's OHLC.

**Per root, whole archive, attributed to the root the OLD dict would have used:**

| root | bars accepted | foreign | share |
|---|---:|---:|---:|
| GC | 10,419,031 | 93,985 | **0.902%** |
| 6E | 7,073,363 | 84,673 | **1.197%** |
| NQ | 6,006,930 | 18,131 | 0.302% |
| CL | 26,226,880 | 17,962 | 0.069% |
| ES | 6,844,532 | 6,548 | 0.096% |
| YM | 5,483,272 | 3,116 | 0.057% |
| ZN | 6,148,624 | 2,647 | 0.043% |
| ZB | 5,567,947 | 2,123 | 0.038% |
| RTY | 3,380,576 | 21 | 0.001% |
| **all** | **77,151,155** | **229,206** | **0.297%** |

**CL is the LEAST affected root at bar level, at 0.069%**, despite owning every one of the 27
multi-window symbols. The exposure is (b), not (a), and (b) does not favour crude.

---

## 2. The fix

`ids_of` now returns **validity windows** — `(iid, root, contract, w0, w1)`, one row per mapping
interval — and `process_chunk` labels each bar from the window that **contains** its `ts_event`,
half-open `[w0, w1)`. This is the reference fix in `build_fut_breadth_hourly.py`, applied unchanged
in shape. The committed G1–G5 gates are untouched.

**Three guards, and each is shown to FIRE on a break that hits the scalar it compares** (a
self-test that cannot fail is worse than none; and the break must hit the number, not the
assertion's name):

| guard | the scalar | the break that fires it |
|---|---|---|
| `[IDS]` repeated `(iid, window start)` | `w.duplicated(["iid","w0"]).sum()` | a second outright mapped to id 117678 starting the same day → 1 |
| `[IDS]` empty `[w0, w1)` | `(w["w1"] <= w["w0"]).sum()` | `end_date` before `start_date` → 1 |
| `[IDS]` a bar claimed by more than one window | `j.duplicated(["iid","ts"]).sum()` | a second window on **the same id** covering one instant → 1 |

and the fourth check is behavioural rather than a guard: the selftest reproduces the **old flat dict
verbatim** on a seven-bar, real-shaped case and asserts **3 of 7 bars get a different label** (1
relabelled, 2 claimed by no window). That count is the scalar the fix moves.

**Two DIFFERENT ids whose windows overlap in time must NOT raise** — far months trade alongside
near ones — and that is asserted too. It is the trap the breadth builder recorded: the first
version of such a check could not fire.

### What the window fix does NOT reach, stated plainly

Labelling a bar from its containing window makes the **bar's** label right. It does not make the
**symbol string** unambiguous: `CLN9` still means July-2019 before 2019-06-23 and July-2029 after
it, and this fixture keys contracts by that string. The builder therefore writes every
multi-window symbol and its boundaries into the meta (`multi_window_symbols`, per file) so the
residual is measurable without re-reading the archive. **On this build it bites nothing** — no
`contract` cell moved — because a reused slot is a far-decade month that never wins the
volume vote.

### Speed — one optimisation pass, both halves proven bit-identical

Profiled before launching (**every guess here has been wrong**): decode was **1.2 s** of a file's
**17.3 s**, and `DatetimeIndex.strftime` was **9.52 s of process_chunk's 11.5 s** on a 10M-row
chunk. Replaced with `tz_localize(None) → datetime64[D] → str` (**0.32 s**, `et_days`), and
`assemble`'s three `pd.to_datetime(...).dt.strftime(...)` loops with `shift_days`. Both are
asserted equal to the expression they replaced — `et_days` over **26,600 instants spanning both
DST transitions**, `shift_days` over **9,867 consecutive days** for `k = ±1` — and each equality
check is shown to fail when fed the wrong input. **The `--limit 1` build is byte-identical across
the change.** Projected 11–13 min; ran in **8.9 min**, 1.02 billion rows.

`--build --limit N` now writes to `temp/`, never to the fixture: a profile must not be able to
overwrite a committed artifact.

---

## 3. The one thing that changed, and it was a finding

Two roll rows vanished:

    - 6E  2021-12-24  6EH2 -> 6EX1   (winning volume: 10 contracts)
    - 6E  2021-12-26  6EX1 -> 6EH2

**D467's G2 ADDENDUM wrote this up as a market fact:** *"a front change on a day whose winning
volume is below 1% of the root's median session volume is a holiday artefact (6E, 2021-12-24: 6EX1
on 10 contracts, back on the 26th)"*. **It was this defect.** Named exactly:

    instrument_id 2584, in 2021, carried FOUR symbols:
      VDLF122-PTLF122   2021-01-01 .. 2021-02-07    a spread
      CLTN1-CLTU1       2021-02-07 .. 2021-07-06    a crude spread
      6EX1              2021-07-06 .. 2021-11-30    <- the only OUTRIGHT, so the flat dict's label
      0AUZ2             2021-11-30 .. 2022-01-01

    on 2021-12-24 id 2584 traded 1 bar, 10 contracts, at a price of 0.0100

On Christmas Eve 2021 the euro's front month was decided by **one ten-lot of `0AUZ2` priced at a
cent**, wearing the label `6EX1`. It won because it was the only thing that "traded" 6E that day.
**A euro front month priced at 0.01 — and the volume floor the ADDENDUM added to tolerate it now
has nothing to tolerate: 6E's artefact count goes 1 → 0.**

YM's (2025-09-14, 1,448 contracts) and RTY's (2025-09-14, 1,063) artefacts **survive the fix** and
are genuine thin-Sunday flips. RTY still fails G2 on one reversion, exactly as D472 recorded.
`all_gates_pass` is `false` before and after, for the same single reason.

**The general lesson, because the escape was not luck:** the slots that get reused or rotated are
the ones **nothing trades** — `6EF3`, `GCX2`, `NQU3`, `CLN9`-as-2029 are non-active or far months,
which is *why* their mapping slot was free. A front-by-volume rule is therefore structurally
insulated from this defect **as long as the real front's volume dominates**. The 6E case is the
exception that proves the rule: on a holiday the real front's volume is a trickle, and 10 spurious
contracts are enough.

---

## 4. CL specifically — D495's +1.09 gross Sharpe is not touched by this

[D495](D495-RESULT-the-confluence-fails-decisively-and-produces-the-best.md) published
*"CL B2 has the highest GROSS Sharpe measured anywhere — +1.09"* off this panel. Sized:

| | |
|---|---|
| CL session rows in the fixture | 3,629 (2,756 inside G5's usable window, 2016-01-04 →) |
| rows with **any** changed price cell | **0** |
| rows with a changed bar count or volume | **0** |
| rows whose `contract` changed | **0** |
| CL bars the flat dict took that were not CL outrights | 17,962 of 26,226,880 — **0.069%**, the lowest share of the nine roots |

**No CL session carries a bar from the wrong contract, in the usable window or outside it, and the
panel D495 read is byte-for-byte the panel that exists now.** The +1.09 needs no re-run on this
account. It is worth being precise about what that does and does not say: this record checks the
**data**, and D495's own verdict stands on its own terms — net +0.108, cost eating 90% of it, C-a
failed, and *"no non-index root is net positive"*.

The 27 multi-window CL symbols are all far-decade reuses (`CLN9`-as-July-2029 and friends) whose
volume is a rounding error against the front, so they never won a front-month vote. **That is a
measurement, not an assumption: `contract` changed on zero of 3,629 rows.**

---

## 5. Defect 2 — the 55.6% day-session share on CL, NG, RB and HO is fully explained, and it is two things, neither of them the builder

The question was why the share of sessions carrying **both ends** of the h09..h15 window reads
**55.6% on CL, NG, RB and HO** against ~80% for metals, rates and FX and ~69% for the index roots.
**The four roots agreeing to three decimals is not a coincidence to be explained away — it is the
signature of a shared calendar and a shared cutover date.**

Evidence: [`scripts/d520_day_session_coverage.py`](../../scripts/d520_day_session_coverage.py) →
[`data/d520_day_session_coverage.json`](../../data/d520_day_session_coverage.json). It reads the
36-root breadth fixture and this fixture for the row-level terms and **re-decodes six archive files
with its own wider root list** for the hour tables, because the D467 builder carries nine roots and
NG, RB and HO are not among them. Nothing in it depends on another lane's cache.

### Term one: 16.5% of the rows are SUNDAYS and can never have a day session

The breadth builder keys a session row on **every calendar day that carries volume**, and Globex
reopens Sunday 18:00 ET — so Sunday is such a day. A Sunday-keyed row takes its day hours from
Sunday daytime (the market is shut) and its evening from Saturday (there is none); the Sunday
evening bars belong to **Monday's** row. Measured:

| | CL | GC | ES |
|---|---:|---:|---:|
| rows | 5,049 | 5,048 | 5,046 |
| Sunday rows | **832 (16.5%)** | 832 (16.5%) | 832 (16.5%) |
| 2016+ both-ends, all rows | 0.803 | 0.803 | 0.801 |
| **2016+ both-ends, Mon–Fri only** | **0.963** | **0.963** | **0.960** |
| 2016+ Sunday rows with both ends | **0 of 550** | 0 of 550 | 0 of 550 |

**The ~80% ceiling every root shares is the Sunday rows plus holidays and early closes. It is not a
defect and it is not root-specific** — all twelve roots measured read **0.960–0.974 Mon–Fri from
2016** and **0 of 550 Sunday rows** carry a day session. (BZ is the one root whose Sunday share is
lower, 754 of 4,968 = 15.2%, because it starts later.) This fixture never had the problem, because
D467's PRESENT rule (h09..h15 ≥ 200 bars) drops those rows; it reads **0.967–0.987** from 2016 on
every root.

### Term two: before June 2015 the archive's energy bars STOP at the pit close

Per-ET-hour, days on which the **front** contract carries a bar, 2013 (`n_days` = 308):

| root | h09 | h10 | h11 | h12 | h13 | h14 | **h15** | **h16** | h17 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **CL** | 210 | 210 | 210 | 210 | 210 | 209 | **0** | **0** | 54 |
| **NG** | 212 | 212 | 212 | 212 | 212 | 211 | **0** | **0** | 54 |
| **RB** | 215 | 215 | 215 | 215 | 215 | 213 | **0** | **0** | 54 |
| **HO** | 214 | 214 | 214 | 214 | 214 | 212 | **0** | **0** | 54 |
| BZ | 252 | 252 | 252 | 252 | 252 | 250 | **247** | 237 | 73 |
| GC | 252 | 252 | 252 | 252 | 252 | 250 | **250** | 250 | 250 |
| ZN | 252 | 252 | 252 | 252 | 252 | 250 | **250** | 250 | 2 |
| 6E | 252 | 252 | 252 | 252 | 252 | 250 | **250** | 250 | 1 |
| ES | 212 | 212 | 212 | 212 | 212 | 210 | 210 | 210 | 54 |

and the last minute of the session's tail, over **all** contracts, same year:

    CL 14:41 ET   RB 14:30 ET   HO 14:32 ET   NG 15:17 ET
    GC 17:14 ET   SI 17:14 ET   ZN 16:59 ET   6E 16:59 ET   BZ 16:59 ET   ES 16:00 ET
    ZC 14:14 ET   (grains end at 14:20 -- the known window, not a hole)

**The cutover is June 2015, and it is abrupt.** Days per month carrying an h15 bar:

| | Jan–May 2015 (per month) | **Jun 2015** | Jul–Dec 2015 (per month) |
|---|---:|---:|---:|
| CL | 0–5 | **22** | 19–22 |
| NG | 3–7 | **22** | 19–22 |
| RB | 1–4 | **22** | 19–22 |
| HO | 1–3 | **22** | 19–22 |
| GC | 19–21 | 22 | 19–22 |
| ES | 17–21 | 22 | 16–22 |

So the 55.6% decomposes exactly, and the script asserts the reconstruction against the reported
figure: `0.080 × 1,725 + 0.803 × 3,324` over 5,049 rows = **0.5561**, against a reported **0.5561**.
**Term one is the Sunday rows, term two is a pre-June-2015 archive hole specific to CL/NG/RB/HO, and
there is no third term.**

**The same shortfall IS present in this committed nine-root fixture, and it is already gated out.**
CL reads both-ends **0.158 before 2016 and 0.969 from 2016**, against 0.96–0.99 for every other
root in both eras; its session counts climb 34 (2010) → 73 → 113 → 210 → 212 → 231 → 258 (2016).
**G5 sets CL's usable start to 2016-01-04**, so a study reading the fixture as intended never sees
any of it. That verdict did not change in this rebuild.

### What I could NOT determine, and will not guess

**Why** the archive stops at 14:30–15:17 ET for these four roots. The times coincide with the NYMEX
floor close, which is suggestive and **which I did not verify and which two roots contradict**: GC
had a COMEX pit and its electronic data runs to 17:14, while BZ never had a pit and is complete.
So "pit-traded products" is not the rule. What is established is the **measurement** — the hole is
real, it is confined to CL, NG, RB, HO, it ends in June 2015, and it is a coverage hole rather than
a labelling problem (hours 15–16 carry 3–51 days of 252 in 2013 across *all* contracts, not zero,
so the data is thin rather than absent under another symbol — h15 on 10/51/10/20 days and h16 on
11/28/3/13 days for CL/NG/RB/HO). The mechanism is open.

**This extends a fact the programme already holds** — *"the GLBX archive lacks the index futures day
session before 2016"* (D462) — by adding: **the energy complex is in the same gap on hours 21→14,
and additionally loses 15:00–16:59 ET until June 2015.** ZN, ZB, GC, SI, 6E and BZ are complete
from 2010.

---

## 6. Things found that were not asked for

1. **`relabelled` is zero everywhere.** Over 77M bars the flat dict never once picked the wrong
   *outright* symbol for a bar it legitimately held. The whole defect is the foreign-instrument
   term. Worth knowing, because "the CL slot reuse" framing predicts the opposite.
2. **The first run of the diff reported 41 changed `front_prev` cells, and all 41 were false.**
   Under pandas' string dtype a missing value stays `NA`, `NA != NA` is `NA`, and a mask of `NA`
   counted 41 rows — every one a `front_prev` absent in **both** builds — as changed. `as_text`
   now fills a `<MISSING>` sentinel first. **A diff that cannot distinguish "absent in both" from
   "changed" is not a diff**, and it would have put a fabricated number in this record.
3. **The 2019 file is where multi-window symbols concentrate** (16 of the 27), all CL, and it is
   also where six instrument_ids map to two of our outrights at once (`CLN9`/`CLN29`,
   `CLV9`/`CLV29`, …) — Databento emitting both the CME raw symbol and a 2-digit-year form for the
   same contract. The window guards pass on it, which means those pairs have disjoint intervals;
   had they shared one, the `[IDS]` duplicate guard would have stopped the build.
4. **`--build` had no way to be run cheaply**, so every check of it cost a full archive pass. It
   now takes `--limit N`, writing to `temp/`.

## 7. What this record does not do

It does not re-run D495, D467 or D472 — none of their inputs moved. It closes no avenue (R15) and
admits nothing to any book or ledger. It leaves the symbol-string ambiguity **measured and
unresolved**, because resolving it needs the `definition` expiry table that another lane is
building; on this fixture it changes nothing.
