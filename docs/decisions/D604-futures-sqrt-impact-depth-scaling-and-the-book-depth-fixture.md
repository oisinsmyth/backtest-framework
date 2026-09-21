# D604 — A futures square-root impact brick, its depth-scaled variant, and the first order-book depth fixture: the repository could not charge size on a future, and had never read an MBO message

**Status:** Committed
**Date:** 2026-09-21
**Category:** Cost architecture
**Source:** One of the deposit-infrastructure components' third round (D585–D589 were the first
five, D590–D594 the second; D608 and D605–D607 are this round's other four, built in parallel).
Implements `SETTLEMENT_FLOW_LEDGER_PREREG.md` §5.3 (the impact
model) and §8A.4 (depth-based impact, Stage H), and discharges that document's required unit
tests **7**, **45** and **46** together with `INDEX_REWEIGHT_FLOW_PREREG.md`'s required unit
test **18**. Extends D1/D2 (the brick interfaces), D3/D66 (the square-root law), D48 (no false
affordances), D102 (declarative stack config), D520/D521 (windowed instrument-id maps), D536
(untracked bulk panels), D550 (newline pinning), D586 (the settlement-window table), D587
(`Future`) and D591 (the futures cost table and its `BRICK_KEYS` row). R16 governs every number
reproduced below.

## Decision

**1. `costs/futures_impact.py` adds `FuturesSqrtImpact`, keyed on `Future.root`.** It is the
same law as `costs/equity_bricks.py:SqrtImpact` — `Y × σ_d × sqrt(|Q| / V_d)`, charged on the
trade's own notional — with a futures parameter set. The default coefficient is the ledger's
fixed **Y = 0.7** (§5.3, decision D6), not `SqrtImpact`'s order-of-magnitude 1.0.

`impact_fraction(future, quantity)` is dimensionless. `impact_for_flow(future, q_rem, price)`
returns the ledger's `I`: the **signed** move in quoted price points, zero at zero
(required unit test 7). `impact_usd` / `cost` return dollars on `Future.notional`. A non-`Future`
raises `TypeError` naming `equity_bricks`; an unknown root raises `FuturesImpactError` naming the
root and the known roots.

**2. `depth_scaled(impact, depth_t0, depth_bar)` is §8A.4, and the identity is arithmetic.**
`I_D = I × sqrt(D̄ / D(t0))`, taking the impact rather than recomputing it, so that `D(t0) = D̄`
gives `I_D == I` **exactly** — `sqrt(x/x)` is `1.0` and a finite double times 1.0 is itself.
That is required unit test 46 and index-reweight 18, and both are asserted with `==` on the
fraction, the signed points and the dollars, at three depths and five impacts. A non-positive or
non-finite depth raises; returning `inf` for a zero measured depth would charge an infinite
impact on a book the panel merely failed to read.

**3. `depth_bar(observations, day, lookback_days, stat)` computes D̄ from PRIOR days only, and a
same-day row RAISES.** Not filtered out quietly: a silent filter leaves the caller believing a
guard ran. It also raises on a short window, on a repeated day and on a non-positive depth.
**The default statistic is the median, because §8A.4 says median**; D604's brief asked for the
mean, `stat="mean"` is offered beside it, and the two are measured against each other on the new
fixture below.

**4. `data/futures_impact_params.json`, built by `scripts/futures_impact_table.py --build`.**
36 parent roots, **three measurement lines**, every number copied from a source key path or
computed by the builder from the minute panel, every line carrying its window and its provenance.
No timestamp, so `--build` is deterministic and `--selftest` re-derives the whole file and
compares the committed bytes by sha256.

| line | roots | window | carries |
|---|---|---|---|
| `d511` | 9 | 2025-09-11 … 2026-09-10 | ADV (`v_bar`), σ in dollars per FULL contract (`sigma_sess`); price level from the breadth meta's last bar, in the same window |
| `breadth_meta` | 36 | 2010-06-06 … 2026-09-09 | a day-session σ and a notional. **NO VOLUME AT ALL** |
| `day1m_2016_2023` | 36 | 2016-01-04 … 2023-12-29 | ADV and σ computed here from `fut_day1m.parquet`. **THE DEFAULT** |

**The default is the in-sample line, and that is the point of having three.** The other two are
measured on 2025-09…2026-09, inside the deposit's sealed vault window and after this
repository's 2024-01-01 holdout. A study that reaches for one is making a claim the table cannot
make for it, and now has to name the line to do so.

**5. `breadth_meta` is stored with a hole in it and refused at the point of use.** Its source has
no volume field, so `adv_contracts` is absent and `FuturesSqrtImpact.__post_init__` raises,
naming the line and the missing field. That is the D48 shape: the alternative is either dropping
a measured σ or filling the ADV from a different window and letting the join disappear into a
float.

**6. `futures_sqrt_impact` joins the declarative config** (`config/cost_stack.py`), additively:
one `registry.register`, one `BRICK_KEYS` row (`type, root, coefficient, line`), one docstring
block. **Table-resolved only** — there is no explicit form. An ADV and a σ written into a config
would be two numbers with no measurement window and no provenance, which is exactly what the
artefact exists to carry.

**7. `data/fixtures/fut_book_depth_1m.csv.gz` — the first reader of the MBO schema in this
repository.** One row per (root, day, ET minute) for the front contract of the eight parents in
the only MBO pull on disk: `root, day, minute_et, contract, mid, spread_ticks, best_bid_lots,
best_ask_lots, bid_depth_5tk, ask_depth_5tk, bid_orders_5tk, ask_orders_5tk, n_events`, where
depth is resting size within ±5 ticks of the mid — §8A.4's own band. Built by
`scripts/build_fut_book_depth.py` by replaying the limit-order book from MBO actions.

**It is a BOOK-STATE artefact. It computes no return, no signal and no trade.** The pull spans
**2026-08-11 … 2026-09-09**, which lies inside the deposit's sealed vault window
(2025-03-01 → 2026-09-18). **That window has not been reconciled in writing with this
repository's 2024-01-01 holdout**, and D594 already left the same reconciliation open. Nothing in
this panel may score anything until the principal rules. The panel's meta says so in its own
`holdout` field and `tests/unit/test_fut_book_depth.py` asserts the wording is there.

## Rationale

**Every futures result on disk was computed with no impact term at all, and nothing could have
noticed.** `SqrtImpact._params_for` reads `instrument.symbol`; `Future` carries `root` and has no
`symbol`. So `SqrtImpact` applied to a `Future` does not charge a default — it **raises**, and no
futures runner ever called it. Commission and tick crossing (D591) are both per-contract linear:
they are the whole cost model at one contract and they are the whole cost model at a thousand.
The size question could not be asked. It can now, and `test_the_equity_brick_still_cannot_price_a_future_which_is_the_gap_closed`
pins the raise, because a suite that did not could not tell a closed gap from one that never
existed.

**The same law, not a second one.** The futures fraction is asserted **bit-identical** to
`SqrtImpact.impact_fraction` on the same two doubles, over 200 hypothesis-drawn
(σ, ADV, Q, coefficient) tuples. The expression is written in the same association for that
reason: change the bracketing and a ULP appears. A second implementation of a published formula
that merely agreed to a tolerance would be a new formula.

**A parameter without a window is not a measurement.** Three sources held pieces of `V_d` and
`σ_d` on two different windows, and none held both for all 36 roots. Keeping all three side by
side, each with its own window and provenance, is what lets the default be chosen on the holdout
rather than on convenience — and what makes the vault-window lines visible when one is named.

**The replay rests on one convention, and gate G2 is the test of it, not a sentence.** In MBO,
`A` adds, `C` removes its own size, `M` reprices, `R` clears the instrument's book, and **`T`,
`F` and `N` do not change resting depth** — a fill's book effect arrives as a separate cancel or
modify. If that were wrong and this replay ignored an `F` that really removed size, traded-through
orders would stay resting and the book would cross within seconds of the open. G2 requires a
strictly positive spread at every emitted minute of every live session. It is also why the
builder reports `unknown_ref` — a `C` or `M` naming an order the book has never seen — and why
**that count is 0 across all 22 days and 1.13 billion front-contract messages**: with Databento's head-of-file
`F_SNAPSHOT` the book is complete from the first record, and every cancel finds its order.

**A wrong tick is the error that no downstream check can see**, so the multiplier is read from a
scaled source and cross-checked, not taken. That cross-check found a live defect; see below.

**What this record does not do:** no strategy return is computed and no bar is read for any
return, here or by either builder. Nothing is admitted, closed, re-scored or re-costed.

## Consequences

### The reproductions (R16 — exactly, or the first mismatch named)

Hand-worked in `tests/golden/test_futures_impact_ledger.hand.txt` before the assertions existed,
by a calculator that never imports the codebase. All assert with `==`.

| quantity | hand file | value | verdict |
|---|---|---|---|
| `1519.9726384933488 / 163066.35443037972` | §1 | `0.00932119101946498` | **exact** — the stored σ fraction is the stored division |
| `1000 / 1253830.165063291` | §2 | `0.0007975561825389021` | exact |
| `sqrt` of it | §2 | `0.02824103720720792` | exact |
| `0.7 × σ × sqrt` | §2 | `0.00018426807167734195` | exact, = `FuturesSqrtImpact.from_table("ES").impact_fraction(ES, 1000)` |
| in bp | §2 | `1.8426807167734196` bp | exact |
| `impact_usd`, 1,000 ES at 4,000 | §3 | `36853.61433546839` on `200000000.0` notional | exact |
| `impact_for_flow`, ±1,000 | §3 | `±0.7370722867093678` index points | exact, equal and opposite |
| CL, Q = 500 | §5 | `0.0005770820364171101` | exact through all three intermediates |
| `I_D == I` at `D = D̄` | §4 | 5 impacts × 3 depths | **exact**, `==` |
| fraction vs `SqrtImpact` | §6 | same doubles | **bit-identical**, 200 drawn tuples |

`2 × 0.00018426807167734195 == 0.0003685361433546839` holds exactly on these particular doubles —
recorded as a coincidence of the numbers, not a property of the law, so that a later reader does
not build on it.

### A live defect in `Future.from_specs`: dollars per point is 100× wrong on seven of the 36 roots

The builder derives each root's multiplier from the breadth fixture's **scaled**
`tick_usd_full_contract / tick_price_units` and cross-checks it against `Future.from_specs`
(D587). Seven disagree, every one of them a root that `Future.from_specs` resolves through the
`data/fut_specs_from_definition.json` fallback:

| root | breadth (scaled) | `Future.from_specs` | ratio |
|---|---|---|---|
| ZC, ZS, ZW | 50.00 | 5,000.00 | **100×** |
| ZL | 600.00 | 60,000.00 | **100×** |
| LE, HE | 400.00 | 40,000.00 | **100×** |
| SR3 | 2,500.00 | 25.00 | **1/100×** |

The definition snapshot states `tick_usd = mpi × display_factor × uom_qty`, with no allowance for
a cents quote (ZC's `uom: "BU"`, price in cents a bushel) or a percent-of-par quote (SR3's own
entry carries `percent_of_par: true`). **All seven have `known_tick_usd: null`** — nothing ever
verified them, and the twenty roots where a verified value exists all agree. The consequence is
not confined to this record: `Future.tick_usd` is what D591's `TickCrossing` prices a crossing
off, so a `TickCrossing` charged on `Future.from_specs("ZC")` is 100× too dear. **Recorded, not
resolved** — the fix belongs in the spec file, and this builder uses the breadth value and stores
all seven disagreements in `data/futures_impact_params.json#multiplier_disagreements`, gated by a
test.

### The 2025–26 window is not the 2016–23 window, and the ADV ratio says by how much

`adv_ratio_d511_over_day1m`, the vault-window ADV over the in-sample one, on the nine roots that
have both:

| 6E | CL | ES | GC | NQ | RTY | YM | ZB | ZN |
|---|---|---|---|---|---|---|---|---|
| 1.72 | 0.74 | 1.11 | 1.62 | 1.45 | 1.36 | 0.72 | **2.23** | **2.11** |

An impact fraction scales as `1/sqrt(V_d)`, so charging ZN's recent ADV on a 2016–23 study
understates the impact by `sqrt(2.23) = 1.49`, and charging YM's understates it the other way.
**Studies must use the default `day1m_2016_2023` line.** The table's `why_default` says so and
the naming of any other line is now an explicit act.

### The depth fixture: what the probe found, and what the replay cost

`--probe` on 2026-08-14 (1.29 GB), before any fan-out:

| | |
|---|---|
| schema / dataset | `mbo` / `GLBX.MDP3`, one UTC day per file |
| parent symbols | ES, NQ, RTY, YM, CL, GC, ZN, ZB (8) |
| symbol mappings / outright windows | 2,697 / 215 |
| messages | **67,384,291**, decoded in 9.5 s |
| actions | `A` 22,209,131 · `C` 22,119,988 · `M` 13,985,438 · `N` 6,043,209 · `F` 1,951,980 · `T` 1,073,838 · `R` 707 |
| `F_SNAPSHOT` records | **114,379**, all at the head of the file |
| schema fields | 15 (`length, rtype, publisher_id, instrument_id, ts_event, order_id, price, size, flags, channel_id, action, side, ts_recv, ts_in_delta, sequence`) |
| files | 26, of which **22 carry a 09:30–16:00 ET session** (four are Sunday UTC dates: the week opens 18:00 ET that evening, which is inside the same UTC day, so the file is real and holds no day session) |

Across the 22 replayed days: **2,022,164,750 messages decoded, 1,129,606,247 belonging to the
eight front contracts, 1,328,506 snapshot records — and 0 `unknown_ref` and 0 undefined prices,
on every single file.** A cancel or modify naming an order the book has never seen would be the
symptom of a mis-sequenced or snapshot-less replay; there are none.

**The projection was wrong by 3.3×, and that is the number that belongs here.** One worker was
measured before the fan-out, as the memory rule requires: 50.1 s and **332 MB RSS** on
2026-08-14, projecting 22 files ÷ 6 workers × 50.1 s = **3.1 min**. The actual was **610.6 s
(10.2 min)**, because 2026-08-14 is the second-smallest session file: per-file time ranges
42.9 s to 216.2 s. The parallelism itself was fine — `[SPEED] sum(item time)/wall = 3317/611 =
5.43× on 6 workers (91%)`, well above the 70% floor, and peak worker RSS 356 MB. **The
projection failed on the sample, not on the scaling**, which is the same shape as D385 arriving
from the other side: one item's cost is not the fleet's.

The replay is cached in `temp/d604_book_depth_replay.pkl`, **keyed on a sha256 of the source of
the replay functions** rather than on the file's mtime. Keying on mtime would discard a correct
10-minute replay on every gate edit; keying on the fixture alone is D288's stale-cache trap. The
key is the replay path's source text and nothing else, and `--verify` re-replays from scratch and
compares against it. **`--verify 2` on the two smallest session files: serial == pool
bit-identically on 6,256 rows, and both equal the cached replay of the same two days, also
bit-identically.** ("Smallest session files", not smallest files: the four smallest are Sundays
and emit no row, and a comparison of two empty frames proves nothing.)

### What the panel says, and one gate that had to be restated

`data/fixtures/fut_book_depth_1m.csv.gz`: **65,688 rows = 391 minutes × 21 days × 8 roots**,
1,062,781 bytes, sha256 `df64af132b1449115ad995708101063d86a4a24e51c9fc909ff6e66f4da89559` — and **that digest is reproducible**: the gzip stream is written with `mtime=0` and no stored filename, so two builds of the same rows give the same bytes, which a default gzip header (wall clock + source name) would not. The meta also carries the digest of the uncompressed CSV, `ec8c7cb815bcf5931adcf7f9acce88a66a4095fa208cb24788f139c4627c4c2c`.

**2026-09-07 is excluded whole, and the rule that excludes it is liveness, not the book gates.**
A day is kept only when every front contract prints at least one message in every emitted minute.
On Labor Day, **917 of the day's 3,128 minute-rows carry no message at all**, across all eight
roots — the session ends early and the grid runs on past it. A day that fails is dropped for all
roots, because a half-day kept for the roots that survived it would make §8A.4's trailing
same-time window ragged across roots with nothing able to see it. **The same day holds all 538
crossed-or-locked minutes and 69 of the 76 over-wide minutes in the entire replay** — after the
close the matching engine is not running, so a new bid above the best ask simply rests. That
coincidence is reported, not used as the definition; the other 21 days contain **zero** crossed
or locked minutes in 65,688 rows, which is what gate G2 asserts and what tests the `T`/`F` fill
convention.

**G3 and G4 are stated as identities, not as thresholds.** Seven minutes of the 65,688 have a
spread wider than the band itself, so the best quotes are outside it and **nothing rests within
±5 ticks — the depth is exactly zero, which is the true answer to the question the column asks.**
The rows stay, are enumerated in the meta's `band_empty_minutes`, and the gates say: a minute
outside the band reports exactly zero in-band depth (G3), and depth ≥ the best quote's own size
on every minute inside it (G4). Neither can be tuned by looking at the data.

**Five of those seven are at exactly 10:00 ET**, one at 09:45 and one at 14:00 — the macro-release
instants. GC 2026-08-28 10:00 reaches 21 ticks with 24,651 messages in that minute and an empty
band; the minute before it is 2 ticks with 18 and 9 lots resting.

**The pre-stated sanity gate "ES depth within ±5 ticks is the largest of the eight" is FALSE, and
decisively.** Median two-sided depth within the band:

| | ZN | ZB | ES | RTY | NQ | YM | GC | CL |
|---|---|---|---|---|---|---|---|---|
| lots | **74,717** | 19,581 | 701 | 169 | 42 | 48 | 26 | 92 |
| notional | **$8.07bn** | $2.14bn | $270M | $25.5M | $24.7M | $12.8M | $11.7M | $7.95M |
| band half-width | 7.20 bp | **14.34 bp** | 1.62 bp | 1.66 bp | **0.42 bp** | 0.93 bp | 1.12 bp | 5.90 bp |

ZN is 30× ES in dollars. **A ±5-tick band is not a comparable object across roots:** it is
14.34 bp wide on ZB and 0.42 bp on NQ, a factor of 34, so "depth within 5 ticks" asks a different
question of every root. G6 was restated to what is true and still a check — **ES is the deepest
EQUITY-INDEX root** — and the false expectation is recorded here with the number that refutes it.

### D̄: median and mean are close but not interchangeable, and neither dominates

§8A.4 says median; D604's brief said mean. Over the **3,123** (root, minute) same-time windows of
20 prior days the panel supports, `mean / median` has median **1.0073**, a 5th–95th range of
**0.9596 – 1.0887**, a maximum of **1.7218**, and sits above 1 in only **58.8%** of windows.
`I_D` takes the square root of that ratio, so the choice moves the impact by about ±4.4% at the
tails and by up to +31% at the extreme. **Neither is the conservative one**, which is why
`depth_bar` offers both, defaults to the document's median, and a study must name which.

## What this does not settle

- **The sealed-vault reconciliation.** The MBO month is inside the deposit's
  2025-03-01 → 2026-09-18 vault window and this repository holds a 2024-01-01 holdout. D594 left
  the same question open in writing and it is still open. The depth panel is book state, which
  is why it could be built at all; **it cannot be joined to a return until the principal rules.**
- **`D̄`'s statistic.** §8A.4 says median, D604's brief said mean, both exist and they differ on
  the real fixture. A study must name which.
- **The ledger's own `V_d` and `σ_d` are 20-day TRAILING quantities; every line in the table is a
  WINDOW average.** The table carries the windows so the caller can see the extrapolation; the
  brick is arithmetic and claims nothing about it.
- **Temporary versus permanent impact, decay, and the participation rate.** Not modelled, and
  §5.3 does not model them either.
- **`Future.from_specs`'s seven wrong multipliers.** Recorded above; not fixed here.
- **The one-line widening `tests/golden/test_futures_costs_ledger.py` needs.** See the handoff.

## Files

| file | what |
|---|---|
| `src/backtest_framework/costs/futures_impact.py` | new — the brick, `depth_scaled`, `depth_bar`, the table reader |
| `src/backtest_framework/config/cost_stack.py` | ADDITIVE — one `BRICK_KEYS` row, one factory, one docstring block |
| `data/futures_impact_params.json` | new, tracked — 36 roots × 3 lines, deterministic |
| `scripts/futures_impact_table.py` | new — `--build`, `--show`, `--selftest` (system python: pyarrow) |
| `scripts/build_fut_book_depth.py` | new — `--probe`, `--build`, `--verify`, `--gates`, `--diagnose`, `--selftest` (system python: databento) |
| `data/fixtures/fut_book_depth_1m.csv.gz` | new, 1.06 MB, gitignored by `/data/**/*.csv.gz` — the manifest row is the integrator's |
| `data/fixtures/fut_book_depth_1m.meta.json` | new, tracked |
| `tests/unit/test_futures_impact.py` | 92 tests |
| `tests/unit/test_fut_book_depth.py` | 21 tests — replay arithmetic (no panel needed) + the panel |
| `tests/golden/test_futures_impact_ledger.py` + `.hand.txt` | 37 tests, every bar `==` |

150 tests, all green. `ruff check` and `mypy` clean on both src files. `temp/d604_book_depth_replay.pkl`
is a `temp/` cache and is deletable at any time; losing it costs one 10-minute rebuild.

## Handoff

**One integration action is required and D604 could not perform it.**
`tests/golden/test_futures_costs_ledger.py:370` (D591) closes with

```python
assert set(BRICK_KEYS) - set(BRICK_KEYS_BEFORE_D591) == {"futures_round_trip"}
```

an equality over the whole set difference, so **any** additive tenth row fails it. D604's row is
additive and every one of the nine earlier rows is asserted unchanged, here and in D591's own
golden. The minimal widening that keeps the assertion's intent — D591's row is present and no
earlier row moved — is:

```python
assert "futures_round_trip" in set(BRICK_KEYS) - set(BRICK_KEYS_BEFORE_D591)
```

That file is outside D604's allowed set, so it is left red and named here rather than edited. It
is the **only** red left by D604's code; the 150 tests it adds are green, as is everything else
under `tests/unit` and `tests/golden` that touches cost or config (400 passed). The remaining
reds on this tree are integration gates reacting to untracked work — D604's and the concurrent
agents' — and are itemised below.

**The integrator also needs to:**

1. add the manifest row for `data/fixtures/fut_book_depth_1m.csv.gz` (1,062,781 bytes, sha256
   `df64af132b1449115ad995708101063d86a4a24e51c9fc909ff6e66f4da89559`) — until it exists,
   `tests/unit/test_fut_book_depth.py` skips the eight panel tests on a machine without the file
   rather than raising, and says so in its own docstring;
2. stage `data/futures_impact_params.json` and `data/fixtures/fut_book_depth_1m.meta.json`
   **by explicit path** — the `.csv.gz` is gitignored by `/data/**/*.gz` and must not be tracked;
3. regenerate the counts. **D604's own contribution to the integration gates, measured on this
   tree:** `src/backtest_framework/config/cost_stack.py` gains **3 non-bare `raise`s** (the only
   tracked file D604 modifies, so it is the only count that moves before staging); after staging,
   **+1 src module, +150 tests** (92 unit + 21 unit + 37 golden), +1 golden hand file, +2 scripts,
   +2 tracked data files, +1 decision record. The other stale-count failures on this tree
   (`tests/property/` 145→146, total 3,007→3,008, `docs/RUNNING.md` panels 123→125) are **not**
   D604's — it adds no property test and does not touch the manifest;
4. `tests/unit/test_cited_decisions_exist.py` fails today with exactly one dangling number, D604,
   and its own message says why: the record is on disk and untracked. Staging it is the whole fix;
5. decide where the `Future.from_specs` multiplier defect is routed. It is recorded here and in
   `data/futures_impact_params.json#multiplier_disagreements`, and it is **not** confined to this
   record: D591's `TickCrossing` prices a crossing off `Future.tick_usd`, so it is 100× too dear
   on ZC, ZS, ZW, ZL, LE and HE and 100× too cheap on SR3. Nothing on disk charges those roots
   today; the next thing that does will be wrong.

### `docs/data-available.md` paragraph

> **`data/fixtures/fut_book_depth_1m.csv.gz` + `.meta.json` (D604)** — the first order-book depth
> fixture, and the first thing in this repository to read the MBO schema. **65,688 rows = 391 ET
> minutes (09:30–16:00) × 21 days × 8 roots**, one per (root, day, minute) for the front contract
> of **ES, NQ, RTY, YM, CL, GC, ZN, ZB**, from the only MBO pull on disk
> (`GLBX-20260911-NKFKU4AMHN`, 26 files, 39.4 GB, 2026-08-11 → 2026-09-09; 2.02 billion messages
> decoded, 1.13 billion on the eight front contracts). Each row carries the mid, the spread in
> ticks, the best size on each side, and the **resting size and order count within ±5 ticks of the
> mid** — `SETTLEMENT_FLOW_LEDGER_PREREG.md` §8A.4's own band — plus `n_events`, the front
> instrument's message count since the previous minute. The book is replayed order by order: `A`
> adds, `C` removes its own size, `M` reprices, `R` clears; **`T`, `F` and `N` do not move resting
> depth**, and the no-crossed-book gate is what tests that. **26 files, 22 day sessions, 21 days
> kept:** the four Sunday files hold no 09:30–16:00 ET session, and **2026-09-07 (Labor Day) is
> excluded whole** because 917 of its 3,128 minute-rows print no message at all — that day also
> holds every crossed or locked minute in the entire replay. **THE THING THAT BITES:** this is
> **book state, not a return series**, and its month lies inside the deposit's sealed vault window
> (2025-03-01 → 2026-09-18), which nobody has reconciled with this repository's 2024-01-01
> holdout. Nothing here may be joined to a price move until that reconciliation is in writing. And
> a ±5-tick band is **not a comparable object across roots** — it is 14.34 bp wide on ZB and 0.42
> bp on NQ, so ZN's 74,717 median lots and NQ's 42 are answers to different questions (meta:
> `band_half_width_bp_by_root`). Seven minutes have a spread wider than the band itself and
> therefore **zero in-band depth**; they are real, listed in `gates.band_empty_minutes`, and five
> of the seven are at exactly 10:00 ET.

> **`data/futures_impact_params.json` (D604)** — `V_d` and `σ_d` for
> `costs/futures_impact.py:FuturesSqrtImpact`, on the 36 breadth roots, in **three lines**:
> `day1m_2016_2023` (the default, computed from `fut_day1m.parquet` over front-contract sessions
> 2016-01-04…2023-12-29), `d511` (9 roots, 2025-09-11…2026-09-10) and `breadth_meta` (36 roots,
> **σ and notional only — its source has no volume column**, so the brick refuses it by name).
> **THE THING THAT BITES:** two of the three lines are measured inside the sealed vault window and
> after the 2024-01-01 holdout, and the recent ADV is up to **2.23×** the in-sample one on ZN —
> which moves an impact charge by `sqrt` of that. Use the default line unless you mean otherwise
> in writing. The file also records seven roots where `Future.from_specs` returns a
> dollars-per-point **100× wrong**.

### CHANGELOG bullet

> **D604 — the futures square-root impact brick, its depth-scaled variant, and the first
> order-book depth fixture.** `costs/futures_impact.py`: `FuturesSqrtImpact` keyed on
> `Future.root` at the ledger's fixed Y = 0.7, bit-identical to `SqrtImpact` on the same numbers
> (the equity brick raises on a `Future`, so no futures study here has ever charged impact at
> all); `depth_scaled` (§8A.4) with `I_D == I` at `D = D̄` asserted exactly; `depth_bar` raising on
> a same-day row. `data/futures_impact_params.json`: 36 roots × 3 measurement lines, each with its
> window and provenance, default the in-sample one. One additive `BRICK_KEYS` row,
> `futures_sqrt_impact`. `data/fixtures/fut_book_depth_1m.csv.gz`: ±5-tick resting depth at every
> ET minute of 22 day sessions, replayed from 2.02 billion MBO messages (1.13 billion on the eight front contracts) — book state only, inside
> the unreconciled vault window. Records a live defect: `Future.from_specs` returns a
> dollars-per-point 100× wrong on seven roots resolved through the definition fallback.
