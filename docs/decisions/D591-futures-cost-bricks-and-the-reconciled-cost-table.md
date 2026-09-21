# D591 — A futures round trip is two bricks, commission and tick crossing, built from one reconciled table whose every number is copied from a committed artefact

**Status:** Committed
**Date:** 2026-09-21
**Category:** Cost architecture
**Source:** The sixth of the deposit-infrastructure components (D585–D589 were the first five).
Extends D1/D2 (the brick interfaces), D102 (declarative stack config), D48 (no false
affordances), D587 (`Future`, whose `carry_components()` is empty and stays empty), and R16
(reproduce a published number exactly on its own build). Reconciles the cost literals of
D258, D465, D466, D468, D469, D507, D508, D510, D527, D531, D532, D533, D535, D555 and D556.

## Decision

**1. Two bricks, not one number.** `costs/futures_bricks.py` adds `FuturesCommission(
per_round_trip_usd)` and `TickCrossing(ticks_per_round_trip)` against the D1 `TradeCostBrick`
interface. Each charges **half per fill, per contract**, so two fills of one contract cost
exactly `commission_rt_usd + crossing_ticks_rt × tick_usd` — to the bit, because 0.5 is a
power of two. Both **raise `TypeError` unless the instrument is a `Future`**.
`FuturesRoundTrip` composes them and keeps `.commission` and `.crossing` addressable;
`round_trip_usd(instrument, bricks)` is the two-fill helper.

**They are two bricks because they fail differently.** Commission is **declared** — a
brokerage assumption nothing in this repository has measured. Crossing is **measured**, from
the exchange's own quotes. A study that dies on cost needs to know which half did it: a
cheaper broker fixes one and nothing fixes the other.

**2. Crossing is carried in TICKS, never in basis points.** A tick is fixed in price terms.
D465's 0.364 bp *is* one ES tick divided by a particular median price, and quoting it in bp
makes the charge drift with the index level while the real cost does not. Ticks also make the
micro's problem visible: the same 1.0086 ticks is $12.61 on ES and $1.26 on MES, while the
commission does not shrink at all.

**3. One table, `data/futures_costs.json`, built by `scripts/futures_cost_table.py --build`.**
36 parent roots, 47 traded symbols (a `micro` and a `full` entry where CME lists a micro,
`full` alone otherwise), 7 crossing lines, 289 cited values. **Every value is copied** — from
a committed artefact at a named key path, from a named runner literal read through `ast`, or
derived from those with the derivation written beside it. The builder **refuses to write a
value it cannot find**; `--selftest` proves the four refusal paths fire. The file carries **no
timestamp**, so `--build` is deterministic and `--selftest` compares the committed bytes
against a fresh build by sha256.

**4. The default line is `d508_exec` where D508 measured the contract, and the D556 one-tick
convention everywhere else — never D507.** D507 and D510 report a **quoted** spread, which is
a *floor*; D465 and D508 report the **effective** crossing, which is what an aggressor paid.
Falling back from one to the other would serve two different statistics under one name and
would make an unmeasured root look systematically cheaper than a measured one. The one-tick
rule is also what the seen ledger charges (`run_d555:dollar_book`, `cost per side =
comm_rt/2 + 0.5 × tick_usd`), so a construction scored on the default reproduces the ledger's
cost line rather than quietly improving on it. Both statistics stay in the table and
`crossing_lines_for(root)` returns all of them.

**5. `futures_round_trip` joins the declarative config** (`config/cost_stack.py`), additively:
one `registry.register`, one `BRICK_KEYS` row (`type, commission_rt_usd, crossing_ticks_rt,
root, line`), one docstring block. It is declared **either** by naming a contract
(`{"type": "futures_round_trip", "root": "MES"}`, resolving through the table, `root` on its
own giving the **minimum tradable size** `COMPONENTS_PROP.md` scores at) **or** by writing
both numbers out. **A mixture raises**: a config carrying both would hash as one thing and
build as another, which is the drift D102 exists to close.

## Rationale

**The literals had already forked, and nothing could see it.** Twelve futures cost numbers
were scattered across eleven runners — `COST_USD = 4.21`, `COST = {"CL": 4.00, …}`,
`COMMISSION_RT` twice with different values, and the `comm_rt/2 + 0.5*tick` rule written
inline. Reconciling them found **five disagreements**, recorded in the table's own
`disagreements` block and reproduced in the golden ledger:

| what | the two values | resolution |
|---|---|---|
| full-size commission | $4.00 (`d469:83`, from D258's "~$4-5") vs **$6.00** (`run_d555:56`, "D468's convention") | `full` entries carry 6.00; D469's 4.00 survives in ES's `runner_lines.d469` so its published bar still reproduces |
| D533's GC | charged $5.00; the one-tick rule on MGC gives $4.00 | **charged, not derived** — no line in the table produces 5.00 |
| D533's NG | charged $5.00; the one-tick rule on MNG gives $4.00 | **charged, not derived**; MNG is in no crossing census on disk at all |
| D527's crossing ticks, carried twice | 2.4110232735988832 vs 2.4110232735988824 | one ULP; both give $4.205511636799441 exactly on MNQ's $0.50 tick, and would not on a $31.25 one |
| D465's crossing ticks on ES and MES | 1.0085687251930604 vs 1.0085687251930602 | one ULP — the same dollar figure over two different ticks. **Each size entry keeps its own**, or one of D469's two published bars stops reproducing |

**A table of numbers with no provenance is a second set of literals.** Hence artefact + key
path + decision + measurement window on every cited value, and the digests of all nine
artefacts and six runner sources recorded once in `_provenance`. The reason the window is not
decoration: **every crossing census on disk was measured on 2025-09..2026-09 and is applied by
its callers to 2016–2023.** D507 and D508 both say so in their own `limitations` — a tick is
fixed in price terms, so a recent spread on an older, cheaper window is *optimistic*.

**A brick that ignores the price must say so.** `round_trip_usd` takes an optional `price` and
**raises** when a brick that does not declare `price_independent` is handed none: defaulting
it to 0.0 would silently zero a `PercentOfNotionalSpread` and return a number that looks like
an answer. That is the D48 failure `SqrtImpact._params_for` names, arriving from the other
direction.

**What the record does not do:** no strategy return is computed and no bar is read, here or
by the builder. Nothing is admitted, closed, re-scored or re-costed. The finding in
*Consequences* about the seen ledger's cost line is a **statement about two cost numbers**,
not a re-scoring of anything.

## Consequences

**The reproduction results (R16 — exactly, or the first mismatch named).**

| published bar | source | reproduced from the bricks | verdict |
|---|---|---|---|
| MNQ on the D527 line, $4.205511636799441 | `d527…json::reprice.scored.measured.rt_usd` | `3.00 + 2.4110232735988832 × 0.50` | **exact**, `0x4010d271a47c010e`, by both routes |
| D531's `COST_USD = 4.21` | `run_d531:41` | `round(4.205511636799441, 2)` | **exact**; the runner is 0.107% pessimistic |
| D556 round trips: MNQ 3.50, MES 4.25, MCL 4.00, SIL 8.00, ZN **21.625**, ZB 37.25, ZF **13.8125** | `run_d555:dollar_book` + `d556…::dollar_book.min_size` | `comm_rt + tick_usd` | **exact** on all seven |
| D469 ES breakeven 1.3285687251930602 ticks / $16.607109064913253 | `d469…json::cost_bars.ES` | `4.00 + 1.0085687251930604 × 12.50` | **exact**, and equal to `d469.breakeven_ticks("ES", 6919.5)` |
| D469 MES breakeven 3.40856872519306 ticks / $4.260710906491325 | `d469…json::cost_bars.MES` | `3.00 + 1.0085687251930602 × 1.25` | **exact**, and equal to `d469.breakeven_ticks("MES", 6919.5)` |
| MES crossing dollars a round trip | `d469…json::cost_bars.MES.crossing_usd` | 1.2607109064913251 vs published **1.2607109064913253** | **ONE ULP, the only mismatch** — D469 forms it as bp × notional, the brick as ticks × tick_usd. It does not reach `total_usd` or `breakeven_ticks`, both of which are exact above. ES has no such gap. |

**ZN's `21.63` is a rounding tie and `round()` does not produce it.** 21.625 is exactly
representable, so two decimals is a genuine tie: half-up gives the 21.63 the records print,
half-even (Python's `round`) gives 21.62. The tests assert the exact 21.625 and record both.

**The measured default costs more than the seen ledger charges, on every micro where a
measurement exists.** Round trip at minimum size, `d508_exec` against the one-tick convention:

| MNQ | MGC | MCL | MBT | MYM | M2K | M6E | MES |
|---|---|---|---|---|---|---|---|
| 4.07 / 3.50 | 5.93 / 4.00 | 5.03 / 4.00 | 4.31 / 3.50 | 3.80 / 3.50 | 3.76 / 3.50 | 4.38 / 4.25 | 4.42 / 4.25 |
| +16% | **+48%** | +26% | +23% | +8% | +7% | +3% | +4% |

and on the full contracts the gap is larger still (GC $47.17 against $16.00, NQ $21.23 against
$11.00). **This is not a re-scoring and nothing here recomputes a return.** It is the size of
an assumption that was previously invisible because it lived in an inline expression, and it
is now one call away from any study that wants it. The measurement window caveat above cuts
the other way and is recorded beside every line.

**Six roots' `tick_usd` are flagged, not corrected.** `data/fut_specs_from_definition.json`
computes `tick_usd = tick_price_units × unit_of_measure_qty`, which is dollars only where the
price is quoted in dollars per unit. **ZC/ZS/ZW read 1250.0 and HE/LE 1000.0 and ZL 600.0 —
those are CENTS** ($12.50, $10.00, $6.00), so D556's min-size line for them reads $1,256 /
$1,006 / $606. Within a root it is self-consistent (`run_d555`'s gross uses the same price
units) so it is a unit and not an error, but a **one-contract book across roots is mixing
dollars with cents on six of its thirty-four**. SR3 is the opposite sign — 0.0625 against
CME's $6.25, a factor of 100 small, because the percent-of-par divisor is applied to a
`unit_of_measure_qty` that is already dollars per index point; D555/D556 exclude SR3 from the
dollar book, so nothing published rests on it. **The table writes the artefact's own number
and flags it in `spec_flags`.** Correcting it would be typing a value no source carries, which
is the one thing the builder must not do. 24 rows carry a flag; 6 of them carry a unit note.

**Gates.** `tests/golden/test_futures_costs_ledger.py` (+ `.hand.txt`, arithmetic written
first, by a calculator that never imports the codebase) — 40 tests. `tests/unit/
test_futures_bricks.py` — 36, including four hypothesis properties (`derandomize=True`,
`max_examples=40`, D78/D537) of which the load-bearing one is *an entry and an exit cost
exactly one round trip, for every commission, tick count, tick value, price and side*.
`tests/unit/test_futures_costs_table.py` — 43, including the byte-for-byte rebuild, the four
refusals, a break of the min-size cross-check that proves the guard fires, and **every legacy
brick shape still validating**: the pre-D591 `BRICK_KEYS` mapping is snapshotted in the hand
file and asserted unchanged, because a key lost from a row turns 176,592 stored trial configs
into raises and four of those rows are exercised by nothing else.

**Five mutations, five caught** (crossing charging a full tick per fill; commission not
halved; commission ignoring quantity; the `Future` door guard removed; the default line
falling back to `d507_exec`). A gate that cannot fail is worse than none.

**Not built, deliberately.** No carry brick — `Future.carry_components()` is empty and D587
says why (the cost of carry is already in the basis). No exchange/clearing fee split — every
commission line on disk is an all-in round-trip figure, and decomposing it would invent a
breakdown no source carries. No queue, partial-fill or adverse-selection model; that is
D587's fill model's ground, not a cost brick's.

---

## Proposed paragraph for `docs/data-available.md`

> **`data/futures_costs.json`** — the reconciled futures **cost** table (D591). 36 parent
> roots (the D556 breadth set) × a `micro` and a `full` entry where CME lists a micro, 47
> traded symbols, 289 cited values. Per entry: `tick_points` / `usd_per_point` / `tick_usd`
> from the exchange specification files, a **declared** `commission_rt_usd` ($3.00 micro /
> $6.00 full, D468's convention), every **measured** `crossing_ticks_rt` line the contract
> appears in (`d465`, `d508_exec`, `d508_all`, `d510`, `d507_all`, `d507_exec`, plus the
> `d556_one_tick` convention), the `default_line` the bricks serve, and the round-trip dollars
> each runner actually charged (`d469`, `d527`, `d531`, `d533`, `d535`, `d556_min_size`).
> **Every number is copied** from a committed artefact at a named key path or from a runner
> literal read through `ast`; each carries its provenance, its decision and its **measurement
> window**, and the builder (`scripts/futures_cost_table.py --build`, deterministic, no
> timestamp) refuses to write a value it cannot find. Read it through
> `costs/futures_bricks.FuturesRoundTrip.from_table`, never by hand.
>
> **The thing that bites.** (i) **Every crossing census in it was measured on
> 2025-09..2026-09** and most studies here run 2016–2023 — a tick is fixed in price terms, so
> a recent spread on an older, cheaper window is *optimistic*. (ii) `d507_*` and `d510` are
> **quoted** spreads (a floor) and `d465`/`d508_*` are **effective** crossing (what an
> aggressor paid); they are different statistics and must not be averaged or substituted —
> which is why the default falls back to the one-tick convention rather than to D507. (iii)
> **Commission is declared, never measured** (`"measured": false` on every such row). (iv)
> `tick_usd` for **ZC/ZS/ZW (1250), HE/LE (1000) and ZL (600) is in CENTS**, and SR3's 0.0625
> is CME's $6.25 a hundredfold small — inherited from the definition snapshot, listed in
> `spec_flags`, written unchanged and never silently corrected. (v) The default `d508_exec`
> line is **4–48% dearer per round trip than the one-tick convention D555/D556 charged** on
> the eight micros where both exist; check which line a number was computed on before
> comparing two of them.
