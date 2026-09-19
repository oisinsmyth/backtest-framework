# D559 — PRE-REGISTRATION: the momentum × term-structure DOUBLE SORT **as published** (Fuertes, Miffre & Rallis 2010) on the 17 commodity roots of the breadth fixture

**Pre-registration. Committed before the runner exists (R8). Result in a separate file.**
**In sample 2016-01-04 → 2023-12-29; the long window 2011-01-03 → 2023-12-29 is a declared
diagnostic; the 2024+ slice is RESERVED AND NOT READ** (the fixtures hold it; `df` and the curve
table are filtered below `RESERVED_FROM` before anything is computed, and the runner asserts it and
reports the last session read). Nothing admitted (R15).

*2026-09-19. Third study from the deposit folder (`docs/internal/User-Doc-Deposit/PUBLISHED_STRATEGIES.md`
§6, strategy 5), taken after D555 (trend, harness ρ = 0.815 against AQR) and D556 (carry, the
settlement strip gated against D526). The deposit calls FMR's 21% headline "the least reliable number
in this document" because a double sort on ~37 commodities leaves 2–4 names a leg, and it expects a
net Sharpe of 0.25–0.40 "roughly the same as either single sort, at higher concentration risk". Two
sibling studies — **the cross-sectional term-structure sort** and **the cross-sectional momentum
sort** — score the single sorts as their own primaries; this record rebuilds both single sorts
in-process as an UNPROMOTABLE diagnostic so that the orchestrator can check the three studies
against each other. Every function that is not the double sort itself is imported from D555's and
D556's runners, never re-implemented.*

---

## 0. The construction — one, fixed from the paper and the deposit, nothing tuned

| | |
|---|---|
| **fixtures** | `data/fixtures/fut_breadth_hourly.csv.gz` (D555's loader: placeholder rows and weekend stubs dropped, same-contract log returns, `live`/`span` masks) and `data/fixtures/fut_curve_front_next.csv.gz` + `fut_settle_strip.csv.gz` (D556's carry, gated `all_gates_pass`) |
| **universe** | the **17 roots of `SECTOR["CM"]`**: CL BZ HO RB NG GC SI HG PL PA ZC ZS ZW ZL ZM LE HE — all live from 2011 under D555's rule. Grids are built on all 36 roots exactly as D555 builds them (so the session grid is D555's and D556's, 2,065 sessions on the primary window) and then **subset to the 17 rows**; nothing about the other 19 roots is read again |
| **ranking universe vs. dollar universe** | ranks are taken over **all 17**; the dollar book trades **16** — BZ is in D555's `DOLLAR_EXCLUDED` (802 front changes) and **its slot is left untraded**, not refilled |
| **momentum signal** | at month-end session m: **12-1 momentum = `tot12 − tot1`** from D555's `signal_at_month_ends` with L = 12 and L = 1 — the sum of daily same-contract log returns over the **11 calendar months ending the month BEFORE m's month**. Eligible where the 12-month cell is finite (≥ 240 returns in the 12 months, live at m); the 1-month cell is finite whenever the month carries ≥ 20 returns, and the count of month-ends where the 12-month cell is finite and the 1-month cell is not is reported (such a name is ineligible, since `tot12 − tot1` is then undefined) |
| **term-structure signal** | at the same month-end m: **`carry_ann`** from D556's `carry_grid` + `carry_at_month_ends` — `(F_front − F_next)/F_next × 12/months_between`, positive in backwardation, the last settlement within 5 sessions ending at m; **no de-seasonalisation** (as D556) |
| **eligibility** | a root missing EITHER signal at m is **ineligible for every sort that month** — excluded from the ranking, never placed mid-rank. Fewer than **9** eligible names → a **flat month** (counted) |
| **the double sort — SEQUENTIAL (conditional), as FMR** | rank the eligible names by momentum **descending**; `n_leg = ceil(n_eligible / 3)` names in the top and in the bottom momentum tercile, the rest in the middle (17 → 6 / 5 / 6). **Within the top momentum tercile** rank by carry descending and take `ceil(n_tercile / 3)` most-backwardated → **LONG** (6 → 2). **Within the bottom momentum tercile** take `ceil(n_tercile / 3)` most-contangoed → **SHORT** (6 → 2). The middle tercile is never positioned. An empty corner → flat month (counted; structurally impossible at n ≥ 9, and the guard stays) |
| **ties** | broken by **root symbol, alphabetically** — in every ranking the sort key is `(−signal, root)`, so of two tied names the alphabetically earlier one ranks higher. Boundary ties (a tie straddling a tercile edge or a corner edge) are **counted and reported** per month-end |
| **holding and lag** | membership decided at month-end m is **held from session m + 1 to the next month-end** (D555's `hold_from_month_ends` on the span mask); no same-day fill; monthly rebalance |
| **returns** | futures excess returns off the same-contract chain; no financing, no collateral yield |

**Corner sizes, tercile sizes, `n_eligible`, boundary ties, flat months and the roots missing a
signal are reported at EVERY month-end.** The record will name the corners' typical occupancy.

## 1. Cells — the declared family is THREE

| cell | position per root | book | note |
|---|---|---|---|
| **(1) EW / published — PRIMARY** | membership sign ∈ {+1, 0, −1}, held from m + 1 | D555's `book_return`: the equal average over positioned names of `sign × simple return` — with equal corners that is **0.5 × (EW long − EW short)**; equal-weight, dollar-neutral in weight space, **not risk-weighted** | the paper's object |
| **(2) vol-scaled / published** | `sign × 0.40 / σ_i` via D556's `positions_from_signs` (MOP's EW vol, centre of mass 60 days, read at m and held) | the same equal average over positioned names | **risk-weighted, therefore NOT dollar-neutral** — a book whose long corner is in a quieter market than its short corner carries net notional; declared so it is scored, not chosen |
| **(3) dollar / minimum size** | one minimum-size contract per positioned root: the micro where CME lists one (MCL MGC SIL MNG MHG), the full contract otherwise; BZ untraded | D555's `dollar_book`: **$3 / $6 a round trip + one tick crossed**, a front change while positioned is two sides; **scored NET in the family** | the component question. **A vol-scaled dollar cell would be the same object as (3)** — one contract is one contract — and is not a fourth cell |

Per-root, per-year, per-era, per-leg and per-corner figures are **diagnostic and unpromotable**.

## 2. The statistic

> **PRIMARY: gross annualised Sharpe of cell (1)'s daily return, 2016-01-04 → 2023-12-29**
> (mean/sd × √252, D555's monthly block-bootstrap SE).

The long window 2011-01-03 → 2023-12-29 is reported for every cell as a diagnostic and is not nulled.

## 3. Nulls — D555's purged rotation, declared here from the start

**N1** — the held membership grid of each cell is rotated cyclically by a common offset k within
each root's `span & wP` index set (D555's `rotate_signs`); the live mask is in place and, for cell
(2), the vol scale is in place. **For the EW cell the scale passed to the enumerator is 1.0 on every
session of the root's span** (the live mask), so the rotated sign alone is the position — this, and
not the in-place membership mask, is what keeps the corners intact: the 17 roots share one span on
the primary window (asserted), so at every offset the session's cross-section is exactly some other
session's cross-section and **the long and short corner sizes are preserved at every offset**
(asserted on the guarded offsets). The rotation destroys the alignment between the month-end read
and the month that follows it and nothing else. **Offsets within 252 sessions of either end of the
cycle are purged** (D555 §2's amendment: look-ahead on one side, a staler copy of the same signal on
the other). Every surviving offset is scored, so **the p95 carries SE exactly 0**. The full
`offset_profile_primary` is stored. **Exactness guard:** 20 offsets bit-identical against D555's
`book_return_loop` before any percentile is read. The dollar cell is rotated on its own held sign
grid and scored net, as in D555 and D556.

**N2** — the family maximum across the three cells at each surviving offset.

**PASS requires: the primary > 0, above its N1 p95, AND the family maximum above its N2 p95.** p05,
p50, p95 and the rank are reported beside every cell.

## 4. Diagnostic, UNPROMOTABLE, outside the family: the two single sorts, rebuilt in-process

Under json key **`single_sort_check`**, on the identical eligibility mask, tie rule, `ceil`, n ≥ 9
gate and month-end hold:

- **(i) term-structure terciles alone** — rank eligible names by carry descending, long the top
  `n_leg = ceil(n/3)`, short the bottom `n_leg` (17 → 6 long / 6 short);
- **(ii) momentum terciles alone** — the same on 12-1 momentum;

each as an EW/published book (cell (1)'s construction). Stored: gross Sharpe on 2016–2023 (six
decimals), ann. mean return and ann. vol, per-year Sharpes, and each one's daily ρ with the primary.
These are what the orchestrator checks against the two sibling studies' primaries. They enter no
family and no verdict here.

## 5. Predictions — in the runner's own quantities, each with a boolean `holds`

The deposit's expectation is **net 0.25–0.40**. The EW book rebalances at most twice its notional a
month (≈ 24 weight-units a year) at the commodity minimum-size cost of roughly 1–4 bp a side, so the
turnover drag on the Sharpe is about 0.03–0.05; **the gross equivalent judged is 0.28–0.45**, and
the runner reports the actual gross − net so the equivalence is checkable.

| # | prediction | quantity in the runner |
|---|---|---|
| **P-1** (primary) | cell (1) gross Sharpe 2016–2023 **> 0 and above N1 p95**; point range **0.28–0.45 gross** (deposit §6 net 0.25–0.40 plus the drag above) | `predictions.P-1`; `holds` on the first clause, `in_point_range` reported beside it. **A result above the range is a miss of the prediction, not a better result** |
| **P-2** (the deposit's scepticism) | the double sort's **Sharpe uplift** over the better single sort is **smaller than its mean-return uplift** — with the mean uplift expressed in the better single sort's own vol units so the two are commensurable: `holds` iff `SR_ds − SR_best < (μ_ds − μ_best) / σ_best` (annualised). Both uplifts are reported. Stated plainly: for a positive double-sort mean this holds exactly when σ_ds > σ_best, i.e. when concentration raised the vol faster than it raised the return | `predictions.P-2` |
| **P-3** (concentration) | cell (1)'s **ann. vol > both** single sorts' ann. vol | `predictions.P-3` |
| **P-4** (concentration of P&L) | **top-1 root share of the primary's P&L > 30%**, where share = largest \|per-root total\| / Σ\|per-root totals\| on 2016–2023 (evaluable whatever the sign of the book's total; the D555-style share of the book's total is reported beside it) | `predictions.P-4` |
| **P-5** (the same two mechanisms) | daily ρ of cell (1) with **each** single sort **> 0.4** on 2016–2023 | `predictions.P-5` |
| **P-6** (component) | the 16-root dollar book **fails C-d**: daily σ > $500 | `predictions.P-6` |
| **P-7** (falsifier) | gates green (D556's fixture metas `all_gates_pass`, every audit raised on its break) and the primary **below N1 p50** → the sort did badly on this window; the data layer is not the reason | `predictions.P-7` |

## 6. Cost line and component line — both lenses, declared before the run

**Published cells (1) and (2):** D555's return-space cost — per root per session, bp of notional
per side at minimum size, `(commission/2 + 0.5 × tick_usd)/(price × usd_per_point)`; turnover in
weight units charged at that rate; rolls as a separate add-on. Reported: gross and net Sharpe side
by side with SE, ann. vol, max drawdown, hit, skew, kurtosis, turnover in weight units a year, cost
in bp a year, **breakeven bp/side**.

**Dollar cell (3):** gross and net Sharpe with SE, cost total, sides, roll sides; hit, skew, daily σ;
**the book decomposed by root — per-root dollar totals sorted, the top contributor's share, the
per-contract daily σ range — printed and written BEFORE the component line** (D556's palladium
lesson); the **C-d-eligible sub-book** (roots with σ ≤ $500 at minimum size) beside it; and the
component line: **C-a** net Sharpe (SE) with gross beside it, hit, **C-c** skew ≥ −0.5, **C-d**
daily σ ≤ $500, **ρ with the ledger's live entry stated ABSENT** (the MACD arm's per-session P&L is
not on disk). The line is written whether or not anything clears.

## 7. Reporting — the four groups, in the json and the RESULT

1. **Performance**, per cell: gross and net side by side as in §6, and the long window.
2. **Root-month distribution** of the primary's contributions (`sign × simple return / n_positioned`,
   summed within the month, so the contributions sum to the book's monthly return): n, mean, median,
   ex-top-1%, ex-bottom-1%, symmetric-trim mean, win rate, payoff, skew — **long leg, short leg, combined**.
3. **Concentration**: per-root totals; top-1/5/10 root share; roots to reach half the P&L; per-year
   and per-era (D555's `ERAS`) Sharpe; per month-end `n_eligible`, tercile sizes, corner sizes,
   boundary ties, flat months, roots missing a signal.
4. **Nulls**: N1 per cell with p05/p50/p95/rank, `purge_sessions` = 252, `offsets_after_purge`; N2.

## 8. Runner assertions — each proven in `--selftest` to RAISE on a break that hits what the assertion reads

| | audit | the deliberate break |
|---|---|---|
| **(a)** | **lag audit** — D555's `audit_lag` against a **second implementation of the month-end corner membership in pandas** (per month-end: `rank` for momentum, `groupby` tercile, `rank` for carry within, never calling the runner's sort) shifted to the session after the month-end | the **unlagged** grid (membership applied to the month it was read in) |
| **(b)** | **sign audit, in money** — D555's `audit_sign_in_money` on the dollar cell's gross grid | the **negated** grid, AND a **mis-lagged** grid (`dP` rolled one session) |
| **(c)** | **right quantity** — D555's `audit_right_quantity`: the held grid changes only on the session after a month-end | a **daily** grid |
| **(d)** | **carry from the strip** — D556's `audit_carry_from_strip` on the carry SIGN read at the month-ends for the 17 roots, rebuilt from the raw settlement strip | the **negated** sign |
| **(e)** | **NEW — corner-membership audit**: long/short/flat membership at every month-end recomputed by the independent pandas path of (a) and asserted equal to the runner's | **one long/short pair swapped at one month-end** |

Plus: the primary's scored P&L differs from the unlagged one; the corner sizes are preserved under
rotation; `REQUIRED_OUTPUTS` declared and the runner raises before writing if any is missing; the
`max_drawdown_convention` block (`sign: "negative"`, D542) is the first key of the json; every text
read and write declares `encoding="utf-8"`.

## 9. Time

Before the full enumeration the runner times 20 offsets and states the projected wall; the
expectation is **under 3 minutes** (2,064 offsets × 3 cells on 17 roots; D556 did 6 cells on 36 roots
in 89 s). If the projection exceeds 10 minutes, one optimisation pass — hoist or skip only, never a
reordered float sum, never a sampled null; over 15 minutes, stop and report.

## 10. What is read, and what is not

The breadth fixture and the strip from 2010-06-07 for warm-up; **scored 2011-01-03 (diagnostic) and
2016-01-04 (primary) through 2023-12-29**. **Not read: any session from 2024-01-02 onward** — `df`
and the curve table are filtered below `RESERVED_FROM` before any grid is built, the runner asserts
no reserved row survives, and the RESULT states the last session read. No published double-sort
series exists for a harness check like D555's; the harness rests on D555's (AQR ρ 0.815) and D556's
(G1–G4) checks of the same two inputs.

## 11. What this record does not do

No de-seasonalisation of carry, no vol cap, no cross-sectional z-score combination (the deposit's
§8 is a different construction), no choice between conditional and independent sorting after seeing
either (the conditional form is FMR's and is the one declared), no choice of tercile count, no
universe chosen after per-root results. A finding that the double sort is flat on 2016–2023 is a
finding about the double sort on these 17 roots and this window; the deposit's own reading — that
the insight belongs in a combined continuous forecast, not a filter — is what a null result here
leaves standing.
