# D558 — PRE-REGISTRATION: cross-sectional 12-1 momentum **as published** (Miffre–Rallis 2007; Fuertes–Miffre–Rallis 2010; Asness–Moskowitz–Pedersen 2013) on the 17 commodity roots of the breadth fixture

**Pre-registration. Committed before the runner exists (R8). Result in a separate file.**
**In sample 2016-01-04 → 2023-12-29 (the ledger's window); the long window 2011-01-03 → 2023-12-29
is a declared diagnostic; the 2024+ slice is RESERVED AND NEVER READ** (the runner filters the
fixture below `RESERVED_FROM`, asserts nothing later survives, and reports the last session read).
Nothing admitted (R15).

*2026-09-19. Third study from the deposit folder (`docs/internal/User-Doc-Deposit/
PUBLISHED_STRATEGIES.md` §5), after D555 (time-series momentum, harness calibrated against AQR at
ρ 0.815) and D556 (carry timing). The deposit calls this "the weakest of the five as a standalone"
and records the source's own multiple testing (Miffre–Rallis report the 13 of 32 ranking/holding
pairs that worked). Two sibling studies — the cross-sectional term-structure sort and the double
sort — are written separately and share nothing with this record but the fixture. Everything not
stated here is D555's, and the runner imports D555's and D556's functions rather than
re-implementing them: `load_fixture`, `live_start_by_rule`, `build_grids`, `month_ends`, `ew_vol`,
`signal_at_month_ends`, `hold_from_month_ends`, `book_return`, `book_return_loop`, `sharpe`,
`block_boot_se`, `stats_block`, `max_drawdown`, `cost_bp_per_side`, `published_cost`, `dollar_book`,
the three audits, `rotate_signs`, `enumerate_null`, `NULL_PURGE`, `window_mask`, `sha256`; from D556
`positions_from_signs` and `min_size`. One instance of each module, D556's `_load` pattern.*

---

## 0. The construction — one, fixed from the papers, nothing tuned

| | |
|---|---|
| **fixture** | `data/fixtures/fut_breadth_hourly.csv.gz`, read through D555's `load_fixture` (placeholder and weekend-stub rows dropped, 2024+ filtered) |
| **universe** | the **17 roots of `SECTOR["CM"]`**: CL BZ HO RB NG GC SI HG PL PA ZC ZS ZW ZL ZM LE HE — every one live from 2011 under D555's rule (re-derived on the full 36-root frame, then the grids are built on the 17). The session index is the union of the 17 roots' sessions: **3,498 sessions 2010-06-07 → 2023-12-29, 2,063 on the primary window** against D555's 2,065 — the four sessions absent are Good Fridays (2012-04-06, 2015-04-03, 2021-04-02, 2023-04-07) on which no commodity printed a close; every month-end session coincides with D555's |
| **daily return** | D555's same-contract log return: `log(C_t/C_{t−1})` on a same-front session, `log(C_t/O_h18,t)` on a front change; `rsimple = expm1(rlog)` for the book |
| **signal at month-end m** | **momentum 12-1** `= tot12 − tot1`: `(_, tot12) = signal_at_month_ends(rlog, live, days, me, 12)` is the sum of daily log returns over the 12 calendar months ending with m's month (finite only with ≥ 240 returns in the window and the root live at m — D555's rule); **`tot1` is the sum over m's own calendar month with NO count floor**, read as the difference of the same cumulative sums over the same `_window_start(days, m, 1)` boundary, and the runner asserts it equals `signal_at_month_ends(…, 1)`'s `tot1` bit-for-bit wherever that one is finite. **So the signal is the sum of daily log returns over the 11 calendar months ending the month BEFORE m** — AMP's 12-1 |
| **why the floor is lifted on the 1-month cell only** | `signal_at_month_ends(L=1)` carries a floor of 20 returns (240 × 1/12). Probed on the 17 roots: that floor voids **277 root-months where the 12-month cell is finite** — all 17 roots in April 2017 and April 2023 (Good-Friday months of 19 sessions), 16 in February 2013 and 2014, 7–8 in most Februaries — and would flatten whole months of the sort for a calendar artefact. The eligibility rule is the 12-month cell's, as the papers' is |
| **eligibility** | a root is ranked at m only where `tot12` is finite; ineligible roots are **excluded from the ranking, never placed mid-rank** |
| **legs** | rank eligible roots by momentum **descending**; `n_leg = ceil(n_eligible / 3)`; **long the top `n_leg`, short the bottom `n_leg`, middle flat** (17 eligible → 6 / 5 / 6; 16 → 6 / 4 / 6; 15 → 5 / 5 / 5; 14 → 5 / 4 / 5; 10 → 4 / 2 / 4). **Ties** in momentum are broken by root symbol **alphabetically** (declared; the runner counts month-ends with a tie at either leg boundary). **Fewer than 9 eligible → a flat month** (declared; counted) |
| **expected eligibility, from the probe** | on the 96 primary month-ends: 17 eligible on 75, 16 on 8, 15 on 10, 14 on 2, 10 on 1 (2021-01-29); **no flat month expected**. HE and LE are ineligible on 17 month-ends each and the five grains on 1–3: a day-session root has no 18:00 open on a front-change session, so that return is undefined, and when rolls cluster (2016, 2020–21) the trailing count dips under 240. That is D555's rule applied as written, and it is reported per root |
| **execution lag** | membership decided at month-end m is held from session m+1 to the next month-end (`hold_from_month_ends`, masked by the root's span); no same-day fill |

Futures returns are excess returns; no financing, no collateral yield.

## 1. The three cells — the declared family

| cell | position per root | portfolio | note |
|---|---|---|---|
| **(1) EW / published — PRIMARY** | membership sign ∈ {+1, 0, −1}, held from m+1 | `book_return` = the equal average over positioned roots of sign × return = **0.5 × (EW long − EW short)** when the legs are equal, which they always are here | equal-weight, **dollar-neutral in weight space, not risk-weighted** — the papers' construction |
| **(2) vol-scaled / published** | sign × 0.40 / σ_i via D556's `positions_from_signs` (MOP's EW vol, centre of mass 60 days, read at m and held) | the same equal average | **risk-weighted within legs and NOT dollar-neutral** (a low-vol long against a high-vol short is net long in weight) — declared as the diagnostic the deposit's TSMOM convention would produce |
| **(3) dollar** | **one minimum-size contract** per positioned root (D556's `min_size`: MCL, MGC, SIL, MHG, MNG micros; full contracts for HO RB PL PA ZC ZS ZW ZL ZM LE HE); `dollar_book` at **$3 / $6 a round trip + one tick crossed, a roll = two sides**; scored **NET** in the family | | **BZ is in `DOLLAR_EXCLUDED` (802 front changes)**: it is ranked with the 17 and its slot is untraded, so the dollar book holds at most 16 roots. The vol-scaled dollar cell would be the same object as (3) — one contract per root is one contract per root — so there is no fourth cell |

> **PRIMARY statistic: cell (1)'s gross annualised Sharpe of the daily book return, 2016-01-04 →
> 2023-12-29**, mean/sd × √252, with a monthly block-bootstrap SE.

Per-root, per-year, per-era, per-leg figures are diagnostic and unpromotable.

## 2. Nulls — exact, enumerated, purged as D555 amended and D556 declared

**N1 — rotation of the held membership grid.** For each offset k, every root's held membership
series is rotated cyclically by the **common** k within `span & wP` via `rotate_signs`; the vol
scale (cell 2) and the live mask stay in place. **The 17 roots share one index set on the primary
window (probed: all 17 `span & wP` sets identical, 2,063 sessions)**, so the rotated grid at
session t is the original grid at session t+k mod L: **the legs at every offset are the legs of
some observed session** — 6/6 where the observed month had 17 or 16 eligible, 5/5, 4/4 otherwise —
and the rotated book is a persistent equal-weight long/short commodity book whose only broken
ingredient is the alignment between the 11-month read and the month that follows it. For cell (1)
`scale_held` is 1.0 on every in-span session, so sign × scale is the ±1 membership before and after
rotation; for cell (2) it is the in-place 0.40/σ; the dollar cell rotates `sign(s_rot)` and is
scored net. **Offsets within `NULL_PURGE` = 252 sessions of either end of the cycle are purged**
(D555 §2's amendment, declared here from the start: the near-end offsets are look-ahead on one side
and a staler copy of the same signal on the other; the momentum lookback is 12 months). Every
surviving offset is scored, **SE 0 by enumeration**; the full offset profile of the primary is
stored (`offset_profile_primary`). **Exactness guard**: 20 offsets bit-identical against
`book_return_loop` before any percentile is printed.

**N2 — the family maximum** at each surviving offset across the three cells (published cells
gross, the dollar cell net — D555's convention).

**PASS requires: the primary > 0, above its N1 p95, AND the family maximum above its N2 p95.**
p05, p50, p95 and the rank are reported beside every cell.

## 3. Predictions — in the runner's own quantities, each with a boolean `holds`

| # | prediction | source |
|---|---|---|
| **P-1** (primary) | cell (1) gross Sharpe 2016–2023 **> 0 and above N1 p95**; the deposit's point range is **0.15–0.35 net**. Judged gross: the modelled cost at ~1 bp/side on a book that turns over a few weight-units a year is under 0.02 Sharpe, so the **gross equivalent is 0.17–0.37**; `in_point_range` is on that. A Sharpe above it is a miss of the prediction, not a better result | deposit §5: 0.6 × 0.55 × 0.75 × 0.85 ≈ 0.21 |
| **P-2** (related, not the same object) | daily ρ of cell (1) with D555's 12-month time-series momentum book restricted to the 17 commodities — rebuilt in-process via `build_positions(g, sig, me, (12,))` and `book_return` on the CM grid — **> 0 and < 0.7**; the monthly ρ reported beside it | MOP: TSMOM is not explained by XS momentum but the two are strongly correlated |
| **P-3** (breadth) | the **long leg's mean root-month P&L contribution > the short leg's** (contribution = the root's book weight × its return, summed over the holding month, so the two legs are compared in the same P&L units) | commodities rallied 2016–2023 (2021–22); the deposit's own warning that reversals "destroy the short leg" |
| **P-4** (momentum crash) | the primary's **worst calendar month is a reversal month**: the CM time-series-momentum book's return in that month is **also negative** (both reported) | the momentum-crash literature: the sort's losers rally when the trend breaks |
| **P-5** (weighting) | cell (2)'s gross Sharpe within **±0.15** of cell (1)'s | same signs, a vol tilt on 17 names of similar vol |
| **P-6** (component) | the dollar book **fails C-d**: daily σ > $500 (PA alone measured $4,344 a day at full size in D555; HO $2,387, RB $1,956) | D555/D556 |
| **P-7** (falsifier) | gates green (audits raise on their breaks, `tot1` identity holds, reserved slice unread) and the primary **below N1 p50** → **the sort did badly on this window**; nothing about the fixture is implicated | |

## 4. Reporting — the four groups, all in the json and the RESULT

1. **Performance, net and gross side by side**, per cell: Sharpe with SE, ann. vol, max drawdown
   (negative convention, D542), hit, skew, kurtosis; for the published cells turnover in weight
   units/yr, cost bp/yr, **breakeven bp/side**; for the dollar cell cost total, sides, roll sides.
   Long-window gross beside the primary.
2. **Root-month distribution** of the primary's P&L contributions, **for the long leg, the short leg
   and combined**: n, mean, median, ex-top-1%, ex-bottom-1%, symmetric-trim mean, win rate, payoff,
   skew.
3. **Concentration**: per-root totals, top-1 / top-5 / top-10 root share, roots to reach half the
   P&L; per-year and per-era (`ERAS`) Sharpe; per month-end `n_eligible`, leg sizes, boundary
   ties, flat months, and per-root ineligible counts.
4. **Nulls**: N1 per cell with p05 / p50 / p95 / rank, `purge_sessions`, `offsets_after_purge`;
   N2.

**The dollar book decomposed by root BEFORE the component line is quoted** (D556's palladium
lesson): per-root dollar totals sorted, the top contributor's share of the total, the per-contract
daily σ range; and the **C-d-eligible sub-book** (roots with σ ≤ $500 — from D555's measurement
that is CL GC SI HG NG ZC at minimum size, re-measured here). **Component line**: C-a net Sharpe
(SE) with gross beside it, hit, skew (C-c ≥ −0.5), daily σ (C-d ≤ $500); ρ with the ledger's live
entry stated **ABSENT** (its P&L is not on disk). Every cell gets the line whether or not it clears.

**Comparability**: daily and monthly ρ (2016–2023) of the primary with the CM-restricted TSMOM
book, and that book's Sharpe, quoted beside D555's own per-sector CM figure (−0.056 on 2,065
sessions; the rebuild here runs on 2,063, the two Good Fridays being zero-return days in D555's
series, so any difference is attributed to that and must be small).

## 5. Runner assertions — each proven in `--selftest` to RAISE on a break that hits what it reads

| | audit | deliberate break |
|---|---|---|
| **(a)** | `audit_lag`: a **second implementation** of the month-end membership in pandas — resample the live log returns to calendar months, 12-month rolling sum minus the last month, 12-month rolling count ≥ 240, then per month-end rank the eligible roots with the same tie rule — **never calling the runner's ranking function**, held by `audit_lag`'s own independent hold, must equal the held grid exactly | the **unlagged** grid (membership placed on the sessions up to and including m) |
| **(b)** | `audit_sign_in_money` on the dollar book's gross grid | the **negated** grid AND a **mis-lagged** grid (`dP` rolled one session) |
| **(c)** | `audit_right_quantity`: the held grid changes only on the session after a month-end | a **daily** grid |
| **(d)** | **NEW — leg membership**: the runner's long/short/flat membership at every month-end equals the independent pandas path's, cell for cell | **one long/short pair swapped at one month-end** |

Plus: `REQUIRED_OUTPUTS` declared and raised on before writing; `max_drawdown_convention` as the
first key of the json; every text IO call declares `encoding="utf-8"`; the `tot1` identity assert
of §0; the reserved-slice assert; the exactness guard of §2. **Timing**: 20 offsets are timed and
the projected wall stated before the enumeration (expected under 3 minutes for 3 cells × 2,062
offsets on 17 roots); over 10 minutes means one hoist/skip pass, over 15 means stop.

## 6. What is read, and what is not

The fixture from 2010-06-07 for the 12-month warm-up; **scored 2011-01-03 (diagnostic) and
2016-01-04 (primary) through 2023-12-29**; D555's json is read only for the per-sector CM Sharpe
quoted in §4. **Not read: any session from 2024-01-01 onward.** No published cross-sectional
commodity momentum factor is freely available for a correlation check; the harness rests on
D555's AQR calibration of the same data layer and on the audits above.

## 7. What this record does not do

No sweep of ranking or holding period (the source's 32 pairs are exactly what the deposit warns
about), no tercile other than the ceiling rule above, no term-structure conditioning (that is the
double sort, a separate record), no vol cap on cell (2), no universe chosen after seeing per-root
results. A primary inside its null is a finding about this sort on these 17 roots and this window.
