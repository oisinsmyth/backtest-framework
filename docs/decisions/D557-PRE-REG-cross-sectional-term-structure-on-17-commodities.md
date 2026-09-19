# D557 — PRE-REGISTRATION: cross-sectional **term structure** on commodities, as published (Erb & Harvey 2006; Fuertes, Miffre & Rallis 2010), on the 17 commodity roots of the breadth fixture

**Pre-registration. Committed before the runner exists (R8). Result in a separate file.** **In
sample 2016-01-04 → 2023-12-29; the long window 2011-01-03 → 2023-12-29 is a declared diagnostic;
the 2024+ slice is RESERVED AND NEVER READ** (the breadth fixture and the curve table are filtered
to sessions before 2024-01-01 at load, the filter is asserted, and the last session read is
reported). Nothing admitted (R15).

*2026-09-19. Third study from the deposit folder (`docs/internal/User-Doc-Deposit/
PUBLISHED_STRATEGIES.md` §4), after D555 (trend, harness ρ 0.815 against AQR) and D556 (carry
timing, −0.20 on 2016–2023). The deposit's §4 rule: each month rank commodities by roll yield, go
long the most backwardated, short the most contangoed, equal-weight the legs, hold one month. Two
sibling studies — the cross-sectional momentum sort and the double sort — are separate records with
their own numbers. Everything this record does not state is D555's and D556's, and the runner
imports their functions rather than re-implementing them: `load_fixture`, `live_start_by_rule`,
`build_grids`, `month_ends`, `ew_vol`, `hold_from_month_ends`, `book_return`, `book_return_loop`,
`sharpe`, `block_boot_se`, `stats_block`, `max_drawdown`, `cost_bp_per_side`, `published_cost`,
`dollar_book`, the three audits, `rotate_signs`, `enumerate_null` and the constants from D555;
`carry_grid`, `carry_at_month_ends`, `positions_from_signs`, `min_size`, `audit_carry_from_strip`
and the fixture paths from D556.*

---

## 0. Universe, windows, data

| | |
|---|---|
| **roots** | the 17 of D555's `SECTOR["CM"]`: CL BZ HO RB NG GC SI HG PL PA ZC ZS ZW ZL ZM LE HE — all live from 2011 under D555's rule. The pre-registration probe (readable slice only) found that all 17 share one span: **2,065 sessions on the primary window for every root** |
| **ranked** | all 17 |
| **traded in the dollar book** | 16: **BZ is in D555's `DOLLAR_EXCLUDED`** (802 front changes, not holdable at one contract under the volume front rule) and **its slot is untraded** — BZ is still ranked, and a leg containing BZ trades one name fewer in dollars. Declared here, not chosen after |
| **windows** | PRIMARY 2016-01-04 → 2023-12-29; LONG 2011-01-03 → 2023-12-29 (diagnostic); eras D555's three. **2024+ never read** |
| **carry** | `carry_ann` from `fut_curve_front_next.csv.gz` as D556 defines it: `(F_front − F_next) / F_next × 12 / months_between`, positive in backwardation, **the annualised basis**; both fixture metas must carry `all_gates_pass` |
| **month-end read** | D556's: the last settlement within **5 sessions** ending at the month-end (`carry_at_month_ends`), NaN if the root is not live at the month-end |
| **no de-seasonalisation** | as D556: NG (mean month-end carry −0.22 on 2011–2023 in the probe) and HE (−0.18) will sit in the contango leg most months; the per-root table will show what that costs |

## 1. The sort — fixed from the deposit, nothing tuned

At each month-end m:

1. **Eligible** = the roots with a finite month-end carry. A root with no value is **excluded from
   the ranking** — never placed mid-rank, never carried forward beyond the 5-session read.
2. **Rank the eligible by carry, descending**; `n_leg = ceil(n_eligible / 3)`. **Long the top
   `n_leg`** (most backwardated), **short the bottom `n_leg`** (most contangoed), the middle flat.
   17 eligible → **6 long / 5 flat / 6 short** (Erb & Harvey's 6/6 of 12 and FMR's terciles both
   land here at this cross-section). 10 eligible → 4/2/4; 12 → 4/4/4.
3. **Ties at either boundary are broken by root symbol, alphabetically** (the earlier symbol takes
   the higher rank). The probe found **0** boundary ties on 2011–2023; the runner counts them anyway.
4. **Fewer than 9 eligible → the month is flat** for every root (a leg of fewer than 3 names is not
   a sort). The probe found no such month on 2011–2023: 17 eligible on 154 of 156 long-window
   month-ends, 12 once, and **10 on 2021-05-31** (the breadth fixture carries a session that day for
   the Globex energies and metals only; the CBOT grains and the livestock have no close, so they are
   not live and not eligible — that one primary-window month trades 4/2/4). The runner reports
   `n_eligible`, the leg sizes, the boundary ties, the flat months and the roots without carry, per
   month-end.
5. **Execution lag**: the membership decided at month-end m is held from session m+1 to the next
   month-end inclusive (D555's `hold_from_month_ends`); the month-end session's settlement is
   published that evening, as D556 §1 states.

## 2. The three cells — the declared family

| cell | position per root | book |
|---|---|---|
| **(1) EW / published — PRIMARY** | membership sign ∈ {+1, 0, −1}, held | D555's `book_return`: the equal average over the positioned names of sign × simple return = **0.5 × (EW long − EW short)**. Equal-weight, dollar-neutral in weight space, **not risk-weighted** — the deposit's "equal-weight the legs" |
| **(2) vol-scaled / published** | sign × 0.40 / σ_i (D555's EW vol, centre of mass 60 days), via D556's `positions_from_signs`, held | the same equal average. **Risk-weighted within the legs and NOT dollar-neutral** — a leg with lower-vol names carries more notional; scored so the deposit's "augment with daily vol updates" has a number beside the plain sort |
| **(3) dollar** | one minimum-size contract per positioned root (D556's `min_size`: the micro where one exists, MCL MGC SIL MNG MHG, the full contract otherwise), BZ's slot untraded | D555's `dollar_book`: $3 / $6 a round trip + one tick crossed, a roll charged as two sides; **scored NET in the family** (the component question) |

A vol-scaled dollar cell would be `sign(sign × 0.40/σ)` = the membership, i.e. **the same object as
cell (3)**, so it is not a fourth cell. **Family = 3 cells.** Per-root, per-leg, per-year and per-era
figures are diagnostic and unpromotable.

## 3. The statistic

> **PRIMARY: gross annualised Sharpe of cell (1)'s daily return, 2016-01-04 → 2023-12-29**, with a
> monthly block-bootstrap SE (D555's `block_boot_se`).

## 4. Nulls — D555's purged enumeration, declared here from the start

**N1** — enumerated rotation of the **held membership grid** by a common offset k within each
root's `span & wP` index set (`rotate_signs`), the vol scale (cell 2) and the live mask in place.
Because the 17 roots share one span, the rotated membership at any session is the membership of
one other month-end, so **the legs stay 6/5/6 at every offset** — for cell (1) the in-place
"scale" is therefore 1.0 on every session inside the root's span (the live mask), so that
sign × scale is the rotated ±1 membership; a scale equal to the *observed* membership mask would
thin the rotated book to two-thirds of its names and unbalance the legs, which is not this null.
**Offsets within 252 sessions of either end are purged** (D555 §2's amendment: near-end offsets
are look-ahead on one side and a stale copy of the same signal on the other), on the primary
window: ~2,064 offsets enumerated, ~1,562 surviving. SE exactly 0. The full offset profile of the
primary is stored. **Exactness guard**: 20 offsets bit-identical against `book_return_loop`
before any percentile is read.

**N2** — the family maximum (cell 1 gross, cell 2 gross, cell 3 net) at each surviving offset.

**PASS requires: the primary > 0, above its N1 p95, AND the family maximum above its N2 p95.**
p05, p50, p95 and rank reported for every cell.

## 5. Predictions — in the runner's quantities, each with a boolean

| # | prediction | source |
|---|---|---|
| **P-1** (primary) | cell (1) gross Sharpe 2016–2023 **> 0 and above N1 p95**; point range **net 0.2–0.4** (deposit §4). The runner judges the **gross** figure: the published cells' modelled cost has cost under 0.02 Sharpe in D555 and D556, so the gross equivalent is **0.2–0.45**. A figure above the range is a miss of the prediction, not a better result |
| **P-2** (same mechanism) | \|ρ\| daily, 2016–2023, between cell (1) and D556's cell A (carry timing) **restricted to the 17 commodities**, rebuilt in-process: **> 0.5** — "same signal, different expression" (deposit §4). The CM-restricted carry-timing Sharpe is reported beside it |
| **P-3** (breadth) | the **long leg's** root-month mean contribution **> the short leg's** (root-month = one positioned root in one month; contribution = Σ sign × simple return / positioned count, so the sum is the book) | the storage mechanism pays the backwardated side; the contango leg is where NG and HE live |
| **P-4** (shape) | daily skew of cell (1) **< 0** | concentrated legs, squeezes |
| **P-5** (weighting) | cell (2)'s gross Sharpe **within ±0.15** of cell (1)'s | risk-weighting a 6-name leg is not the signal |
| **P-6** (component) | the dollar book **fails C-d** (daily σ > $500) | 11 full-size contracts among the 16 (PA, PL, HO, RB, the grains, the livestock) |
| **P-7** (falsifier) | gates green and the primary **below N1 p50** → the sort did badly on this window. A fixture gate failing (`all_gates_pass` absent) → nothing interpretable | |

## 6. Cost line and component line — both lenses, before the run

**Published cells (1) and (2):** turnover in weight units per year, the modelled bp/yr at D555's
per-root, per-session bp/side at minimum size, gross and net Sharpe side by side, net including
rolls, and the **breakeven bp/side**.

**Dollar cell (3):** cost total, sides, roll sides; gross and net Sharpe (SE), hit, skew, daily σ.
**The dollar book is decomposed by root — per-root net dollar totals sorted, the top contributor's
share of the total, the range of per-contract daily σ — printed and written BEFORE the component
line is quoted** (D556: a one-contract book across mixed sizes can be one instrument). The
**C-d-eligible sub-book** (roots with σ ≤ $500 at minimum size) is reported beside it. Component
line: C-a net Sharpe (SE) with gross beside it, hit, skew (C-c ≥ −0.5), daily σ (C-d ≤ $500), and
ρ with the ledger's live entry stated **ABSENT** (the arm's daily P&L is not on disk). **Every cell
gets a component line whether or not it clears.**

## 7. Reporting — the four groups, in the json and the RESULT

1. Net and gross with SE, ann. vol, max drawdown (negative convention, D542), hit, skew, kurtosis,
   turnover, cost, breakeven.
2. Root-month distribution — n, mean, median, ex-top-1%, ex-bottom-1%, symmetric-trim mean, win
   rate, payoff, skew — **for the long leg, the short leg and combined**.
3. Concentration — per-root totals, top-1/5/10 root share, roots to reach half the P&L; per-year
   and per-era Sharpe; per month-end `n_eligible`, leg sizes, boundary ties, flat months, roots
   with no carry.
4. N1 per cell with p05/p50/p95/rank and `purge_sessions`; N2.

## 8. Runner assertions — each proven in `--selftest` to RAISE on a break that hits what the assertion reads

| | audit | deliberate break |
|---|---|---|
| **(a)** | D555's `audit_lag`: the held membership grid against a **second, pandas implementation** of the month-end membership (per month-end, `rank` on the eligible carries; never calling the runner's ranking function), shifted to the session after the month-end by an independent hold | the **unlagged** grid |
| **(b)** | D555's `audit_sign_in_money` on the dollar book's gross grid | a **negated** grid AND a **mis-lagged** grid (dP rolled one session) |
| **(c)** | D555's `audit_right_quantity` on the held grid | a **daily** grid |
| **(d)** | D556's `audit_carry_from_strip` on the carry **sign** read at the month-ends for the 17 roots, from the raw strip | a **negated** sign grid |
| **(e)** | NEW — leg membership: the long/short/flat membership at every month-end recomputed by the independent pandas path must equal the runner's exactly | **one long/short pair swapped at one month-end** |

Plus `REQUIRED_OUTPUTS` with a raise before writing; `max_drawdown_convention` as the first key of
the json (D556's block); every text read and write declares `encoding="utf-8"`; the 20-offset
exactness guard on the null.

**Time.** 20 offsets are timed before the enumeration and the projected wall is printed; expected
under three minutes (17 roots, 3 cells, ~2,064 offsets; D556's six cells over 36 roots took 89 s).
Over 10 minutes projected → one hoist/skip pass, never a re-ordered sum, never a sampled null;
over 15 → stop and report.

## 9. What is read, and what is not

The breadth fixture from 2010-06-07 for warm-up and the curve table, both filtered to sessions
**before 2024-01-01** at load and asserted; the raw strip, same filter, for audit (d). D556's cell A
signs rebuilt in-process for P-2. **Not read: any session from 2024-01-02 onward**, on any fixture.

## 10. What this record does not do

No de-seasonalisation, no quintiles or other leg fraction, no vol cap, no double sort with
momentum, no curve beyond the two nearest months, no universe chosen after the per-root table. A
flat or negative result is a result about this sort on these 17 roots and this window, not about
the fixture, provided both metas' gates hold.
