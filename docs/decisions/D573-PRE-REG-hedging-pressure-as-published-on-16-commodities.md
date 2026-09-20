# D573 — PRE-REGISTRATION: **hedging pressure** as published (Basu & Miffre 2013), a cross-sectional sort of 16 commodity roots on hedgers' hedging pressure from the CFTC legacy report, long the roots whose hedgers are most net short, short the roots whose hedgers are most net long; with a **de-meaned cell** and a **name-randomised null** declared to separate the tilt from the timing

**Pre-registration. Committed before the runner exists (R8). Result in a separate file.** In
sample 2016-01-04 → 2023-12-29; the long window 2011-01-03 → 2023-12-29 is a declared
diagnostic; **the 2024+ slice is RESERVED AND NOT READ** on the breadth fixture, the curve
table and the COT fixture alike (each filtered to sessions or releases before 2024-01-01 at
load, asserted). Nothing admitted (R15).

*2026-09-20. The deposit (`PUBLISHED_STRATEGIES.md` §0) names hedging pressure as "the other
documented commodity premium" and parks it; the five it lists are scored (D555–D559) and the
trend and carry lines are closed (D563). The mechanism is Keynes's normal backwardation with a
measurement: producers and merchants who must hedge pay speculators to take the other side, so
a commodity whose hedgers are net short carries a premium for the long, and one whose hedgers
are net long a premium for the short. Basu and Miffre (2013, JBF, "Capturing the risk premium
of commodity futures: the role of hedging pressure") measure it from the CFTC's commercial
positions and find a long-short sort on it earns a premium that is not trend and is not carry
in construction, though it is correlated with carry in mechanism. The COT fixture was extended
in D572 so that the sort ranks the same commodity roots the three earlier sorts ranked. What
this record does not state is D555's, D556's and D557's; the runner imports their functions.*

**Probe, positioning only, no outcome read (D572's handoff).** On the 16 roots with a COT
series, the legacy commercial category is complete 2010-06 → 2023-12 (709 reports each, no gap
over ten days, a release date on every row). Hedgers' hedging pressure persists at the monthly
horizon (13-week autocorrelation from 0.27 on RB to 0.87 on PA), so a monthly hold of a
13-week average is not conditioning on noise (the Stage 0 premise check). **And 53 % of the
cross-sectional variance of the 13-week mean is the root's own long-run mean**: the metals
(PL 0.25, GC 0.31, PA 0.33, SI 0.36) sit permanently in the low-pressure third and NG (0.56)
and ZW (0.54) permanently in the high-pressure third. The published sort is therefore, in
large part, a **static tilt** — long the precious metals, short natural gas and wheat — and
whether the premium is in the level or in the movement of hedging pressure is the question
this record is built to answer, not to assume.

---

## 0. Universe, windows, data

| | |
|---|---|
| **roots** | **16**: the 17 of D555's `SECTOR["CM"]` less **BZ**, which has no CFTC series (ICE Brent is not a CFTC-reported market) and was D557's untraded slot anyway. CL HO RB NG GC SI HG PL PA ZC ZS ZW ZL ZM LE HE, all live from 2011 |
| **ranked and traded** | all 16; legs of `ceil(16/3)` = **6 long / 4 flat / 6 short** |
| **windows** | PRIMARY 2016-01-04 → 2023-12-29; LONG 2011-01-03 → 2023-12-29; eras D555's. **2024+ never read** |
| **positioning** | `data/fixtures/cftc_cot_raw.csv.gz`, family **legacy**, category **commercial**, futures only — Basu and Miffre's hedgers. Keyed on **`release_date_nominal`** (the Friday of the report's week), never on the report date (three days of look-ahead, R9) |
| **prices** | the breadth fixture and D556's curve table as D557 read them |

## 1. The signal and the sort — fixed from the paper, nothing tuned

At each month-end session m:

1. **Hedgers' hedging pressure** for root i on a report: `HP = commercial long ÷ (commercial
   long + commercial short)`. **The signal is the mean of HP over the last 13 reports whose
   release date is ≤ the month-end session's date** (Basu and Miffre's ranking period R = 13
   weeks, the middle of their 4 / 13 / 26 / 52 grid; declared, not scanned). Eligible if ≥ 10
   of the 13 are present; the probe found all 13 present at every month-end 2011–2023.
2. **Rank the eligible ascending by the signal.** **Long the lowest 6** (hedgers most net short:
   the backwardation side), **short the highest 6** (hedgers most net long), the middle 4 flat.
   Ties by root symbol, alphabetically; counted. Fewer than 9 eligible → the month is flat.
3. **Held from session m+1 to the next month-end inclusive** (D555's `hold_from_month_ends`;
   Basu and Miffre's H = 4 weeks, monthly here on the fixture's calendar).

## 2. The cells — the declared family

| cell | position per root | book |
|---|---|---|
| **(1) EW / published — PRIMARY** | membership sign ∈ {+1, 0, −1}, held | D555's `book_return`: 0.5 × (EW long − EW short), equal-weight, dollar-neutral in weight space |
| **(2) vol-scaled / published** | sign × 0.40 / σ_i (D555's EW vol), held | the same equal average; risk-weighted within the legs and not dollar-neutral, as D557's cell (2) |
| **(3) dollar** | one minimum-size contract per positioned root (D556's `min_size`), all 16 traded | D555's `dollar_book`: $3 / $6 a round trip + one tick, rolls as two sides; **scored NET** |
| **(4) de-meaned / published — SECONDARY, the timing cell** | the sort of §1 on **`HP_13 − HP_52`**, the 13-report mean less the trailing 52-report mean of the same root (eligible if ≥ 40 of 52 present); same legs, same hold | the same book as (1). It removes the root's level and ranks on where hedgers are *relative to their own year*. Declared because the probe found the level is half the cross-section |
| diagnostic: the C-d-eligible sub-book | cell (3) restricted to D564's six roots at σ ≤ $500 a contract (CL GC HG NG SI ZC) | reported, not a family member; a subset is not a construction |

**Family for N2: cells (1), (2), (3) net and (4).**

## 3. The statistic

> **PRIMARY: gross annualised Sharpe of cell (1)'s daily return, 2016-01-04 → 2023-12-29**,
> monthly block-bootstrap SE; **Sortino beside it (R17)**.

## 4. Nulls — three, and each says what it destroys

- **N1 — time rotation** (D555's, D557's): the held membership grid rotated by a common offset
  within the shared span, purged 252 sessions both ends, enumerated (SE 0), legs 6/4/6 at every
  offset; the exactness guard on 20 offsets. It destroys the *timing* of the membership and keeps
  every root's *share of time* in each leg. A static tilt survives it.
- **N3 — name randomisation** (the null none of D557–D562 ran; 2,000 draws, seed declared,
  bootstrap SE of the p95 with D373's UNRESOLVED rule): at every month-end, keep the leg counts
  and draw which eligible roots fill the long and short legs uniformly at random. It destroys
  *which* root is long and keeps the calendar and the leg sizes. A static tilt does **not**
  survive it; a timing effect does not either. Its median is the equal-weight commodity
  cross-section's long-short return under random membership, expected near zero.
- **N2 — the family maximum** at each N1 offset.

**PASS requires: the primary > 0, above its N1 p95 AND above its N3 p95 (margin more than 2 SE
of the N3 p95), AND the family maximum above its N2 p95.** A primary above N1 and below N3 is
recorded as **TILT** — a premium that lives in which roots the hedgers are permanently short of,
which is a level claim and not a timing claim, and the RESULT says so in those words.

## 5. Predictions — in the runner's quantities, each with a boolean

| # | prediction | source |
|---|---|---|
| **P-1** (primary) | cell (1) gross Sharpe 2016–2023 **> 0**; point **0.2 – 0.5** | Basu and Miffre's hedgers'-HP long-short on 27 commodities, 1992–2011, at roughly 0.5–0.8 before the deposit's §1 haircuts (in-sample, institutional cost, larger universe) |
| **P-2** (same mechanism as carry) | daily ρ, 2016–2023, between cell (1) and **D557's term-structure primary rebuilt in-process** (BZ dropped from its ranking so the two universes match): **> 0.4** | normal backwardation: hedgers net short ⇔ backwardation; the two sorts should pick the same roots often |
| **P-3** (the tilt) | the four precious and industrial metals PL, GC, PA, SI are in the **long** leg in **≥ 70 %** of month-ends, and NG and ZW in the **short** leg in ≥ 70 % | the probe's level ordering; a prediction of what the sort *is* |
| **P-4** (level vs movement) | cell (4)'s gross Sharpe **< cell (1)'s**; and cell (4) **above its own N3 p95 only if** the primary is | the premium as Keynes states it is paid on the level of hedging demand, not its change; if (4) beats (1) the premium is in the movement and the paper's construction was the wrong one |
| **P-5** (breadth) | the long leg's root-month mean contribution **> the short leg's** | the backwardated side pays; the short leg holds NG and ZW, whose contango D557 already paid for |
| **P-6** (shape) | daily skew of cell (1) **≤ 0** | concentrated legs |
| **P-7** (component) | the dollar book **fails C-d** (σ > $500); the sub-book's σ ≤ $500 | eleven full-size contracts among the 16 |
| **P-8** (falsifiers) | primary **below N1 p50** → the sort did badly here; primary above N1 p95 and **below N3 p95** → TILT, recorded as a level claim; primary above both and cell (4) above its N3 → the movement carries it and the level was a passenger | |

## 6. Cost line and component line — both lenses, before the run

As D557 §6: turnover, modelled bp/yr at D555's per-root bp/side, gross and net side by side,
breakeven bp/side, for cells (1), (2), (4); the dollar cell's cost total and sides; **the dollar
book decomposed by root — per-root net totals sorted, the top contributor's share, the range of
per-contract σ — printed BEFORE the component line**; the C-d-eligible sub-book beside it.
Component line per cell: C-a net Sharpe (SE) with gross, Sortino, hit, skew (C-c), σ (C-d), ρ
with entry #2 ABSENT (the arm's daily P&L is not on disk). **Every cell gets a component line
whether or not it clears.** If the primary PASSES and the dollar book or its sub-book clears
C-a, C-c, C-d, it is the ledger's **fourth entry** on its numbers (#3 removed in D566); a cell
that clears C-a below its family null's p95 is PROVISIONAL under D468.

## 7. Reporting — the four groups

1. Net and gross with SE, ann. vol, max drawdown (negative convention, D542), hit, skew,
   kurtosis, turnover, cost, breakeven; Sortino beside every Sharpe.
2. Root-month distribution — n, mean, median, ex-top-1 %, ex-bottom-1 %, symmetric-trim mean,
   win rate, payoff, skew — long leg, short leg, combined.
3. Concentration — per-root totals, top-1/5/10 share, roots to half the P&L; per-year and
   per-era; per month-end `n_eligible`, leg sizes, ties, flat months; **the share of month-ends
   each root spends in each leg** (the tilt table).
4. N1, N2, N3 per cell with p05 / p50 / p95 / rank, `purge_sessions`, the N3 p95's bootstrap SE.

## 8. Runner assertions — each proven in `--selftest` to RAISE on a break that hits what the assertion reads

| | audit | deliberate break |
|---|---|---|
| **(a)** | D555's `audit_lag`: the held grid against a second pandas implementation of the month-end membership (pandas `rank` on the eligible signals, never the runner's sort), shifted by an independent hold | the unlagged grid |
| **(b)** | D555's `audit_sign_in_money` on the dollar book's gross grid | negated AND mis-lagged grids |
| **(c)** | D555's `audit_right_quantity` | a daily grid |
| **(d)** | **NEW — the signal from the raw fixture by a second path:** at 300 random (root, month-end) cells the 13-report mean HP recomputed with pandas from the raw rows **using the release-date rule**; exact | the same recomputation **keyed on the report date** — three days of look-ahead — must differ at some cell and the audit must raise |
| **(e)** | D557's leg-membership audit: the pandas path's long/short/flat sets equal the runner's at every month-end | one long/short pair swapped at one month-end |
| **(f)** | N3's draws keep the leg counts: at every month-end and draw, the randomised long and short legs have exactly the runner's leg sizes and are subsets of the eligible set | a draw with one extra long |

Plus `REQUIRED_OUTPUTS`, `max_drawdown_convention` first, `encoding="utf-8"` everywhere, the
20-offset exactness guard. **Time:** 20 offsets timed before the enumeration, the projected wall
printed; four cells over 16 roots and ~2,064 offsets plus 2,000 N3 draws should sit under five
minutes; over ten, one hoist/skip pass; never a sampled N1, never a re-ordered sum.

## 9. What is read, and what is not

The breadth fixture and curve table through 2023-12-29; the COT fixture, legacy commercial, for
the 16 roots through the last release before 2024-01-01 (warm-up from 2010-06 for the 52-report
mean). **Not read: any session or release from 2024-01-01 onward.** Not read at all: the
disaggregated and TFF families (a producer/merchant cell would be a second construction and is
not declared); speculators' hedging pressure (Basu and Miffre's second sort); the double sort.

## 10. What this record does not do

No ranking-period scan; no holding-period scan; no speculators' cell; no double sort; no
netting with the carry sort. If the result is TILT, the level claim is scored on its own
numbers and the record says what it is: long the precious metals, short natural gas and wheat,
held for eight years — a portfolio, not a signal — and it goes to the ledger only on the bars,
with its ρ to the carry sort stated.
