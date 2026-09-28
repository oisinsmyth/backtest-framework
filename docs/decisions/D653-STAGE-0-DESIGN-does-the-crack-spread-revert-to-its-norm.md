# D653 STAGE 0 DESIGN — does the 3-2-1 crack spread revert to its own seasonal norm, at a horizon and size a trade could use?

*Renumbered 2026-09-28 from D652: the opening model's v2 pre-registration took D652 on main while this study sat on an unmerged branch, and the three studies of that branch (the crack spread, the open-interest Stage 0, the metals roll) each moved up one. Commits before the merge cite the old number.*

*Drafted 2026-09-28 on the principal's word ("The crack spread Stage 0"), after the recommendation that named
processing spreads as the one untested thread from the 2026-09-19 deposit with an unread forward slice. Committed
alone, before its runner exists (R8). **No return on any window at or after 2024-01-01 is read.***

## 0. What reopens, and why this is a Stage 0

`ALPHA_PROGRAMME.md` §3.2 names **processing spreads** — "crack, crush, spark — physical margin relationships
computable entirely from futures prices. Real mechanism, no external data, daily frequency" — as the place raw
fundamentals still add something. No record has tested one: a search of `docs/decisions/` finds the word only in
[D572](D572-FIXTURE-COT-extended-to-the-six-missing-commodity-roots.md)'s list of COT contracts and in
[D577](D577-STAGE-0-RESULT-P9-neither-declared-net-swap-dealer-responds.md)/[D578](D578-RESULT-does-not-transfer-no-weekly-instrument-in-the-COT.md)'s
note that producer/merchant longs in crude are refiners and consumers. [D582](D582-CLOSED-the-deposit-and-the-mechanism-programme-synthesis.md)
closed the deposit's list as a source of pre-registrations; **the principal's instruction reopens this one item**,
for the **personal book** (a spread held for weeks crosses the prop account's daily flat, the way the NG spread
failed hurdle P on P2 in `COMPONENTS_PROP.md`).

**The mechanism, in the filter's terms.** A refiner's margin is the crack. When it is high, refiners (a) raise runs,
which adds product supply and crude demand over weeks, and (b) sell the crack forward to lock the margin — both
push the crack back towards its norm. When it is low they cut runs. The counterparty that trades at a price it does
not like is the refiner hedging its margin; the constraint is physical capacity and the margin itself. The published
precedent is weak and old (Girma & Paulson 1999 on the 3-2-1; Dunis et al. 2006 on the gasoline crack); it is a
reason to measure, not a prior on the size.

**Why Stage 0.** The thing a trade would condition on is the crack's deviation from its norm, and **the premise is
that the deviation reverts at a usable horizon.** For an autoregressive quantity, the conditioner's persistence and
the predictability of its change are one statistic — measuring either reads the outcome. So nothing about the
crack's time path was computed before this record. What was read, all disclosed: the strip's session and contract
counts for CL, HO and RB by year (identical sessions on all three from 2010-06-07; HO lists 27–31 contracts a year in
2010–11 and 60 from 2012); the expiry file's coverage; and D651's quoted spreads at 14:00–14:30 ET for the three
roots (cost, §5).

## 1. The object

**Legs.** CL ($/bbl), HO and RB ($/gal × 42), all three 1,000-barrel contracts, settlements from
`fut_settle_strip.csv.gz` ([D556](D556-PRE-REG-carry-timing-as-published-on-36-CME-roots-and-the.md)). **The 3-2-1 crack
in $/bbl** is `C = (2 × 42 × RB + 42 × HO − 3 × CL) / 3`; one unit is 3 CL, 2 RB, 1 HO (3,000 bbl).

**Contract resolution.** Strip codes carry a one-digit year that recycles (`CLF1` is 2011 and 2021);
`data/fut_expiries_from_definition.json` gives every code's expiry per decade, and a row resolves to the expiry
at or after its session. **All three legs are the same delivery month.**

**Which month.** At weekly observation t and horizon h weeks, `m*(t, h)` = the nearest delivery month whose CL
expiry is at least **h + 1 weeks** after t, so the contract the signal is read on is still trading when the target
is read. HO and RB of that month expire at the end of the prior month, after CL's; the runner asserts all three
legs settle on both dates.

**The HO switch.** NYMEX's HO became NY Harbor ULSD from the **May 2013** delivery month; before that it was heating
oil, a different product. **The primary crack uses HO only for deliveries from 2013-05.**

**Weekly sampling.** t = the last session of each ISO week on which all three legs of `m*` settle. (CL and NG have no
settlement on 2020-02-27 and 2020-06-30, data-available (vi); the rule steps over them.)

## 2. The deviation, real-time only

The crack's level is seasonal by delivery month (summer-grade gasoline, winter distillate). The norm is the crack's
own history **for the same delivery calendar month**:

- `Cbar(m, y)` = the mean of the crack of delivery (m, y) over the weekly observations at which it was `m*(·, 4)`;
- `S(m, Y)` = the mean of `Cbar(m, y)` over **y = Y−1, Y−2, Y−3**, each required to have ≥ 3 observations and, for
  the primary, a ULSD delivery (so a norm first exists for May 2016 deliveries, and for January–April from 2017);
- **`D_t = C^{m*}(t) − S(month(m*), year(m*))`** in $/bbl.

Every quantity in S was settled before t (a delivery's weeks as `m*(·, 4)` end at least five weeks before its
expiry, and the norm uses prior delivery years only); the runner asserts it on every observation.

**The target.** `Y_t = C^{m*}(t + h) − C^{m*}(t)` — the change of the **same** contract's crack over h weeks, $/bbl.
No roll inside the holding period.

**The in-sample window.** Every t whose target date is on or before **2023-12-29**, the repository's futures
holdout, from the first t with a primary norm (early 2016): about eight years, ~400 weekly observations. The loader
filters the strip before 2024-01-01 and **asserts** that nothing at or after it survived (`frozen.filter_before`
and `assert_none_at_or_after`). The programme vault (2025-03-01 → 2026-09-18) and D626's sample are not touched.

## 3. The statistics

Primary horizon **h = 4 weeks**. `Y_t = a + β D_t + e`, OLS.

| | statistic | how |
|---|---|---|
| β | the fraction of a deviation that reverts in four weeks (β < 0 = reversion) | OLS; **Newey–West, 4 lags** (overlap 3); the four non-overlapping phases reported |
| rotation null | β with D rotated against Y by k weeks | **every** offset k from 27 to N − 27 (a 26-week purge at both ends: a smaller shift keeps D's persistence, and one inside h puts the target's window into the signal), **enumerated**, so the p05 has SE 0; the full offset profile stored |
| years | β fitted within each calendar year of t | sign count |
| jackknife | β with each calendar year left out | every one reported |
| state count | years holding ≥ 8 weeks in each extreme tercile of D (terciles over the whole window) | [slow conditioners have n_eff in years] |
| half-life | AR(1) of D, weekly | `ln 2 / −ln ρ` |
| economics | `|β| × median |D|` against the round trip (§5) | $/bbl |

**Reported beside, not gating:** β at h = 2, 8 and 13; Spearman of D and Y; the decomposition of β into its legs
(the RB, HO and CL terms of Y regressed on D, which sum to β exactly); the **always-on control**, the mean Y of
holding the crack long regardless of D (the drift the intercept absorbs); the year-by-year table; D's distribution
and its five largest |D| weeks named; and two diagnostic objects on the same rules — the **gasoline crack**
`42 × RB − CL` (2013 on, needing no HO) and the **distillate crack** `42 × HO − CL` (ULSD deliveries). Neither can
pass or fail anything.

## 4. The bar, all six

- **B1** β(h=4) < 0 with Newey–West t ≤ −2.0.
- **B2** β below the enumerated rotation null's p05.
- **B3** β < 0 in at least 6 of the 8 calendar years 2016–2023.
- **B4** at least 6 of the 8 years hold ≥ 8 weeks in each extreme tercile of D (the tercile comparison is between
  states, not eras).
- **B5** `|β| × median |D|` ≥ 3 × the round trip in $/bbl.
- **B6** β < 0 in every leave-one-year-out fit (no single year, 2020 and 2022 included, carries the sign).

**Routing.** All six pass → a pre-registration of a personal-book construction (units of 3:2:1 on −D, weekly), with
its forward slice and power stated, put to the principal before any read of 2024+. B1 or B2 fails → the premise is
not supported and the recommendation is to close the crack line. B1 and B2 pass but any of B3, B4, B6 fails → the
reversion is an era or a year, reported as such, no construction recommended. B5 alone fails → real, not tradable.

## 5. Cost and power

**Cost.** From [D651](D651-RESULT-no-handoff-trough-the-night-is-one-ramp-from-the-reopen.md)'s map, the mean quoted
spread at 14:00–14:30 ET (the settlement window) is 1.45 ticks on CL, 6.92 on RB and 10.23 on HO; half of it per
leg plus the declared $3.00 commission per side (D591) is **$90.29 a side for a 3:2:1 unit, $180.59 a round trip,
$0.060 per barrel.** Quoted spread is a floor on what an aggressor pays; the bar in B5 carries a factor of 3 for that.

**Power of the forward read, before anyone spends it.** The runner computes, from the in-sample β, residual sd and
var(D), the chance that a forward read reaches t ≥ 2 at 100 % and 50 % of the in-sample β on **2024-01-01 →
2025-02-28** (about 60 weeks, the only slice outside the programme vault) and on **2024-01-01 → 2026-09-18** (the
same plus the vault, read only in the joint run). It reads no forward data to do so.

## 6. Predictions, written before the run

1. The half-life of D is between 4 and 26 weeks.
2. β(h=4) is between −0.05 and −0.30 and its t between −1.5 and −3.5: B1 is borderline either way.
3. B4 passes: the deviation changes state within years.
4. 2022 (the distillate crack after the invasion of Ukraine) is the most influential year in the jackknife.
5. Most of the reversion runs through the product legs (the RB + HO share of β above one half): a high crack is
   followed by products falling more than by crude rising.
6. The always-on drift is small beside the signal: `|mean Y| < 0.25 × |β| × median |D|`.
7. B5 passes by an order of magnitude (the move is dollars a barrel, the cost six cents).
8. The forward read on 2024-01 → 2025-02 has power below 0.5 at the in-sample β: that slice alone cannot decide.

## 7. Files

`scripts/stage0_d653_crack.py` (`--selftest`, `--run`; seconds, one process) → `data/stage0_d653_crack.json`.
The selftest must show: the contract resolver picks the right decade on a recycled code; `m*` never selects a
contract that expires inside the horizon; the norm refuses a year it would need from the future and a pre-ULSD HO
delivery; the leg decomposition sums to β to 1e-9; the rotation excludes the purged offsets; and the holdout guard
raises on a 2024 settlement.
