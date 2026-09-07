# The signal hunt, part 2 — eight candidates, and the constraint that reorders them

**Status: RESEARCH RECORD. Not a pre-registration, not a result, and it closes nothing.**
No runner exists for anything below. No null has been run. No number in this file is new —
every figure is quoted from an existing record and attributed. **Only the principal closes a
research avenue (R15);** this file opens nothing either, it enumerates.

**Date:** 2026-09-07 · **Area:** signal research · **personal track**
**Holdout reads spent by this record: 0. Programme total: 1** (D371, 2026-09-07).

---

## 0. Why this record exists

The programme's event screen is exhausted in one specific sense and untouched in another.
D350 screened **46 scores × 3 crossing shapes = 138 long events**; D352 screened 139 short
events. Between them they covered every *single-score, single-crossing* event the catalogue
can express. What they did not touch is (a) quantities the catalogue does not compute at all,
and (b) compounds of two axes.

This file is the candidate list for both, with the principal's rulings of 2026-09-07 recorded
where they changed the ranking.

---

## 1. The principal's rulings, 2026-09-07

Recorded before any design, because two of them reorder the list.

| | ruling |
|---|---|
| **P1** | **The deliverable is a FLAT-BY-DEFAULT sleeve** — out of the market most of the time, incorporable into the current book. This is a requirement, not a preference. **§2 is written around it.** |
| **P2** | **A1 (path efficiency) is the first thing to run**, and its application is an open question the principal raised: confirmation-on-a-trend, or standalone reversal detection, or both, long and short. The principal also names the likely obstacle: **the spread on the short side of the reversal.** §4.1 answers with a recommendation and prices the short leg. |
| **P3** | **A2 (sign sequences) is worth the test, with doubts.** Kept, ranked below B1. |
| **P4** | **A3 (path curvature) is the weakest of the set and still worth testing.** Kept, ranked last, gated on one measurement. |
| **P5** | **High hopes for groups B and C.** |

**The order of work in §8 follows P2 (A1 first), not this record's own ranking.**

---

## 2. THE CONSTRAINT THAT REORDERS EVERYTHING — flatness is a time gate, and this is measured

**P1 asks for a sleeve that is out of the market most of the time. The programme has already
measured that a cross-sectional trigger cannot deliver that, however rare the trigger is.**

[FINDINGS §38](../FINDINGS.md) / [D358](../decisions/D358-RESULT-the-sleeve-is-never-flat-name-level-rarity-does-not-make-time-level-flatness.md), on six cells of `rev_5` and `hist_L` entering the
bottom 2%, 5% and 10%:

```
entries per bar  ×  hold  =  open positions
```

A fresh entry into the bottom **2%** of ~1,000 eligible names — a genuinely rare event at the
name level — fires **5.2 times a bar**. At a 40-bar hold that is **120 open positions on the
average bar and never zero: 100% exposure.** Under the 7-bar invalidation exit the book still
holds 30 names on every bar. **To be flat half the time the product would have to be 0.7 —
about five entries a year — which is not a signal.**

> **Rarity in the cross-section says WHICH NAMES. It cannot say WHEN.**
> — D358's own sentence, and §38 rule 1: *any "flat-by-default" construction must name its
> time-series gate and test the gate with its own null (rotate the gate, keep the trigger).*

### 2a. The two concentrations are different, and only one is a defect

This distinction is new to the record and it is the reason P1 does not conflict with D373's
new shape criterion.

| | what it means | verdict |
|---|---|---|
| **Concentration in NAMES** | a handful of names carry the P&L; the median trade loses | **the defect.** D371: mean +114.97, median −36.57, top-5 share 142%, **2 of 255 names to half the P&L**. This is what failed out of sample |
| **Concentration in TIME** | the sleeve is flat most bars and on in a minority of episodes | **the requirement (P1).** D361's gated fade runs **28% exposure**; §41 rule 4 records gated event books at 28–42% |

**These are compatible: many names, few days.** A gate supplies the flatness; the trigger
supplies the breadth. My earlier framing — "signals that fire on common mild conditions" —
was about the *name* axis and was silent on the *time* axis; P1 is about the time axis.
Nothing is retracted, but the ranking changes:

> **Group C stops being optional. Every candidate in Groups A and B now needs a named
> time-series gate before it is a proposal at all, and the gate needs its own null.**

### 2b. What this costs, stated honestly

The record already prices the gated form, and it is not free:

- D361's gated gap-up fade: **+42.3 gross, net PB +3.3, net PUB −47.2**, and the p95 margins
  against its controls are **5 to 6 bp**. It is the first short above all its nulls and it is
  the third cell of four, with the primary failed.
- D362's two-sink filter on the same ledger: **+61.7 gross, net PB +20, net PUB −30** — but
  with the calm-market sink on, the cell falls **inside the gate rotation's p95**. Two market
  conditions can do the same job, and D362 names the deciding cell as unrun (§4.8 below).

**A gate is a second thing that can be fitted.** D366's gate cleared every null and D371 read
it out of sample and retired it. The gate's null (rotate the gate, keep the trigger) is not
optional bookkeeping here — it is the main defence.

---

## 3. What the catalogue already contains

**49 scores in 8 families**, all ranked cross-sectionally on the lagged, floored (`keep_v2`),
deal-filtered (F0) percentile at t−1, all screened at E1/E2/E3.

| family | module | scores |
|---|---|---|
| price | `ragged_price_scores` | macd_line, macd_hist, trailing_return, rsi, impulse_nodz |
| anomaly | `ragged_anomaly_scores` | max_ret_21, ivol_21, beta_63, rev_5, rev_21, mom_252_21, skew_63, amihud_21, price_log, dist_52w_high |
| intrabar | `ragged_features` | upper_wick, lower_wick, wick_asym, body_frac, close_in_range, range_frac, gap_frac |
| structure | `ragged_structure_scores` | fvg_dist, fvg_signed, struct_trend, retrace_leg, choch_dist, park_vol_21, gk_minus_cc, gap_reversal |
| vol level | `ragged_vol_scores` | atr_norm, cs_spread, rvol21, vol_ratio, range_over_atr |
| session | `ragged_session_scores` | on_mean, id_mean, on_share, on_minus_id, on_persist |
| volume | `ragged_features` | rel_vol, vol_z, dollar_vol, vol_trend, signed_vol |
| profile | `ragged_profile` | dist_hvn, dist_lvn, mass_here, mass_imbalance |

### 3a. Two structural properties of that table, and they are the whole design brief

1. **Every one of the 49 is a magnitude summary of a window.** Not one reads the *order* of
   returns within the window, and not one crosses two axes. The screens exhausted single-score
   crossings; sequences and compounds are untouched.
2. **The independence work says where to dig.** [D268](../decisions/D268-score-independence.md): nine price scores
   carry **2.87 effective inputs** — RSI is trailing return at ρ +0.78, RSI↔macd_line +0.85.
   [D280](../decisions/D280-the-forecast-precheck.md): sixteen OHLC-derivative terms carry
   **13.50–15.76 effective inputs**, and *as levels they carry no predictive power*.
   **The intrabar axis is independent and uninformative alone; the structure axis is
   informative; nothing has ever crossed them.** That is B1.

### 3b. Closed, and not revisited here

| | closed by |
|---|---|
| DEMA / velocity / acceleration / jerk extrapolation | D280 — loses to naive persistence in **all 48** level comparisons, all 9 delta, all 9 range |
| the volume profile, three ways | D272 (as input, ρ 0.085, 0 of 6), D273 (as travel estimator) |
| volume as a **ranking** input | D270 — orthogonal at ρ 0.09, best cell 0.92× the bar |
| time-based exits | D274 — **a random exit bar beats a fixed one** |
| structural exits | D276 — exposure 47% → 4.5% killed it |
| intraday overlays on a daily construction | D280 — the edge is entirely overnight |
| more monotone transforms of trailing return | D268 |

**Volume's one surviving form is event CONFIRMATION, not ranking** — D361's gap-up fade
requires top-decile volume and survived; every ranking use of volume has failed. Any candidate
below that wants volume must use it that way and say so.

---

## 4. The candidates

Each carries: the quantity, why it is not already in the catalogue, the mechanism, the
declared direction, the **gate** (P1), the predicted shape, the null that decides it, and the
Stage 0 measurement that could kill it before any design.

### 4.1 A1 — path efficiency (Kaufman ER) ⭐ FIRST, per P2

**The quantity.** Over a window of n bars:

```
ER_n(t)  =  |c_t − c_{t−n}|  /  Σ |c_j − c_{j−1}|          n ∈ {21, 63, 252}
```

**Why it is not in the catalogue.** Every momentum score in the table *is* the numerator. ER
divides it out by construction. It is the first score in this programme designed to be
orthogonal to trailing return rather than hoped to be — which is exactly what D268 says the
catalogue lacks.

**Mechanism.** The *manner* of a completed move, not its size. A name up 40% in a straight
line is one-sided flow; one that chopped to the same place is noise wearing a momentum label.

#### The application question (P2), answered

The principal named two uses. There are three, and they are not equally good:

| use | form | assessment |
|---|---|---|
| **(i) confirmation / cohort state** | ER as the **state** in a D373-shaped construction: `top decile of mom_252_21 **AND** top half of ER`, trigger unchanged | **RECOMMENDED, and it is where I would spend the first run** |
| **(ii) standalone reversal detection** | low ER = chop = mean-reverting; rank on ER directly, or an E1 crossing into the bottom decile | **second, and scored on the same screen rather than asserted** |
| **(iii) exhaustion** | **high** ER that stalls — an efficient move whose efficiency breaks down | **third; it is a compound (§4.6's hazard applies) and needs a mechanism before a threshold** |

**Why (i) first, and it is a reason about ER's own shape, not a preference.** ER is a windowed
ratio — slow, smooth, and with a denominator that is a sum of absolute moves. A percentile
crossing on a quantity like that fires on denominator noise, which is the exact defect that
produced `retrace_leg` over [−2295, +1207] and `fvg_dist` at 829 ATRs before both were
rebuilt. **A slow smooth ratio is a state variable; treating it as a trigger is a known way to
select on noise in this repo.**

**And there is a live reason to want (i) specifically.** [D373](../decisions/D373-the-winners-dip-long-and-the-median-criterion.md)
is pre-registered with Q1 load-bearing: that the winners' dip carries timing **inside** the
winner pool and is not the cohort's own **+3.85 bp/bar** drift re-expressed (D359 §7). **If
B_c fails, ER is the ready successor** — it re-slices the same cohort on an axis that is not
momentum, so the follow-up is one state swap rather than a new construction. That is worth
having built before D373 reports, not after.

#### The short side of the reversal, priced before it is proposed (P2)

The principal names the spread as the obstacle. **The spread is the second problem; the first
one closes it earlier and cheaper:**

- **[FINDINGS §33](../FINDINGS.md) / D352: no short event at any extreme beats random
  direction.** 139 short events, 23 beat their own names at random eligible times, 4 pass the
  gate, and **none is above random direction** — means −11.5 to +25.6 bp a trade. §33 rule 1:
  *the short side of this universe has no event trigger; any pair book's short leg is the
  ranking's own extreme or nothing.*
- **[FINDINGS §39](../FINDINGS.md) / D359: on the floored universe the loser decile
  RISES.** Every short since D335 has been timing inside a pool that rises.
- **Then the spread, and the principal's instinct is right about its size.** D358 measured the
  held half-spread on names that have just fallen hard at **30–38 bp a side under PUB**, against
  an event round trip of 62–106 bp. D285's lesson applies: measure it with Corwin–Schultz off
  the OHLC on the names actually held, never assume it.

**So: ER's short-reversal leg is declared DEAD ON ARRIVAL by §33 and §39 unless it is the
ranking's own extreme,** and the honest form of the short question is the one exception the
record already owns — a gated fade (D361/D362), not an event trigger. **Direction declared for
A1: LONG.** Any short reading is reported as a mechanism check and counts against the
mechanism if it inverts.

**Gate (P1).** ER's own construction offers none — it is a name-level state. The gate must come
from §5. Default proposal: **C1's breadth/dispersion state**, tested with its own rotation.

**Predicted shape.** Common, mild → high n, mean ≈ median, low top-name share. Strong on
D373's H2 chain and on breadth-relative H4.

**Stage 0, which can kill it in one measurement — specified in §7.**

### 4.2 A2 — sign-sequence statistics (P3: worth the test, with doubts)

**The quantity.** Over 21 bars: longest consecutive up-run; count of sign changes; up-day
fraction. **Magnitude-free entirely.**

**Why it is not in the catalogue.** Nothing reads the sign pattern or the order of returns.
All 49 scores are magnitude summaries.

**Why it is interesting here specifically, and it is not a momentum argument.**
[FINDINGS §14](../FINDINGS.md) spent a whole section on the fact that a cross-sectional rank
on a quantity carrying units ranks those units — and its own remedy failed (`hist_L` is
dimensionless and still tilts). **A count of sign changes is unit-free, price-free and
volatility-free by construction.** It is the one family here that cannot tilt on price, which
is what killed D284 and forced the D339 universe floor.

**The doubt, which is the principal's and which I share, stated as a prediction rather than a
hedge:** magnitude-free may also be edge-free. A signal that discards how far price moved has
discarded most of what a return is. **This is a cheap screen with a weak prior, and it should
be run as a screen and read as one.**

**Direction:** undeclared until Stage 0 — the sign is a choice under R14's fourth amendment and
there is no mechanism here strong enough to declare one in advance. **That is itself a reason
to rank it below B1**, since a candidate whose direction cannot be declared is a candidate
whose mechanism is not yet written.

**Gate:** §5, as with everything.

### 4.3 A3 — path curvature (P4: weakest, still worth testing)

**The quantity.** `mom_126 − mom_252_126` — accelerating versus decelerating winner. Or the
curvature of cumulative log return against time within the window.

**The objection, which is why it ranks last.** It is a linear combination of trailing returns,
so D268 applies directly and it may collapse into `mom_252_21`. The counter-argument is that
it is a **contrast**, not a level, and contrasts can be orthogonal when their parts are not.

**That argument is testable in one measurement and worth nothing until it is made.** Run the
effective-input test (§7) against `mom_252_21` and `trailing_return` first. If it collapses,
it is `mom_252_21` wearing a hat and the record says so and stops.

### 4.4 B1 — undercut-and-reclaim at a confirmed pivot ⭐ strongest of the set

**The gap in the catalogue, precisely.** `ragged_structure_scores._structure_features` already
runs `market_structure(bars, K=3)` and holds `last_low` / `last_high` with a ≥0.5-ATR leg guard
and a 252-bar freshness guard. But `retrace_leg` is a **close-based position ratio** and
`choch_dist` a **close-based log distance** — neither knows the bar's intrabar excursion.
`lower_wick` and `wick_asym` measure the excursion and have no idea where the level is.
**The two families are computed in the same file and never meet.**

**This is the cross §3a.2 points at:** the intrabar axis is measured independent (13.50–15.76
effective inputs of 16 terms) and uninformative as a level; the structure axis is informative.
Their product has never been formed.

**The event (long).**

```
low[t] < last_low      (confirmed pivot, real leg ≥ 0.5 ATR, ≤ 252 bars old)
close[t] > last_low
entry at the next open (D340)
```

**Mechanism.** A stop-run: price takes out the obvious level, finds no supply, closes back
inside. **It is a two-part condition that no single-score crossing can express**, which is why
138 long events did not contain it.

**Direction declared: LONG.** The mirror (`high[t] > last_high` and `close[t] < last_high`,
short) is reported as a mechanism check only, per §33 rule 1 — I would rather have that rule
confirmed than quietly re-tested as a candidate.

**The null that decides it, and it is NOT in the standard suite.** A′/B/B_c/C ask whether the
*timing* is real. The load-bearing question here is different: **does the RECLAIM carry the
information, or only the LEVEL?** The control is the same-pivot population that undercut and
closed **below**. If the reclaim arm is not above that arm's p95, the pattern is `choch_dist`
re-expressed and it is dead. **This control must be built; it does not exist.**

**Predicted shape.** Moderate n, mean ≈ median, low top-name share. The mechanism does not
concentrate in lottery names the way `dist_52w_high` (+123 bp timing) or GME-driven
`gap_reversal` did — three of D350's survivors have GME in January 2021 as their top trade.

**Gate (P1):** §5. A stop-run is plausibly a *dispersion* phenomenon, which makes C1 the
first gate to try rather than an arbitrary one.

### 4.5 B2 — the gap that does not fill

**What exists.** `gap_frac` and `gap_reversal` are in the catalogue, and **`gap_reversal/E1`
was one of three D350 survivors** — +47.1 / +27.0 bp per trade, above A′, B and C, net −22 PUB
/ +17 PB.

**What is absent.** The **intrabar path of the gap day**: for a down-gap, did the session low
ever revisit the prior close? `gap_reversal` is `−intraday / gap`, a close-based ratio; it
cannot see whether the gap was tested and held.

**The prior in the record is positive and it comes from a failed short.** D360 found the
news-gapped name **bounces** — reported as the closure of the short side on tape signals.
**The gap-down-that-holds long is that finding's unclaimed mirror**, and D361 owns the
gap-*up* fade on the short side, so the gap object is half-mined in exactly one direction.

**Cost:** OHLC only, no new data, and `gap_reversal`'s own guard (`|gap| > 5e-3`, because a
1 bp "gap" is not a gap and the first run ranged over [−14338, +1880]) transfers directly.

### 4.6 B3 — compression → directional expansion (state × trigger, inside the name)

**What exists.** `vol_ratio` = fast σ / slow σ, screened as a level and as a crossing.

**What is absent.** Compression as a **state** with a range-expansion **trigger on a different
score**: `vol_ratio` bottom decile, then `range_over_atr` top decile with `close_in_range` in
the top quartile. **This is D361's gate × trigger form moved from the market level to the name
level** — the obvious generalisation, and unrun.

> **THE HAZARD, and it is the main risk of Group B as a direction, not just of this idea.**
> 46 states × 138 triggers = **6,348 compounds**. That space cannot be mined: no measurement
> clears a best-of-6,348 floor, and R13's corollary forbids summing into a floor nothing could
> clear. **Compounds must be pre-specified by mechanism, one or two at a time, with the count
> disclosed.** D373 does this correctly with one compound and prices it at best-of-5.

### 4.7 C1 — breadth and dispersion, from the panel itself (P5, and now load-bearing under P1)

**Where the record stands.** D361 gated on the floored market's 63-bar compounded return and
found it forecasts a **rebound, not a fall** (loser cohort +96.2 bp per 20 bars gated on,
−15.9 off; block correlation −0.23 against a shuffled |r| p95 of 0.16). D362 then found a
calm-market sink does part of the same job, and left **which of the two is the state variable**
unrun.

**Two free state candidates neither study used, both from the existing panel:**

- **breadth** — share of the floored universe above its own 50-day mean
- **dispersion** — cross-sectional IQR of 21-day returns

Both are price action at the universe level; both cost zero data; both are genuinely different
objects from the index return.

**Under P1 this is no longer one candidate among eight — it is the component every other
candidate needs.** §5 is the inventory.

**Stage 0 is the design and is mandatory.** Block correlation of the state's level against the
target's forward drift on **non-overlapping** blocks, with the shuffled-|r| p95 beside it,
**measured before the design is written** — §41 rule 1, and the standing memory rule (*measure
the conditioner's own persistence before designing a study that conditions on it*). **A split
by era or year is not a state.**

### 4.8 C2 — the one cell D362 named and did not run

**The gated gap-up fade's trigger with the calm-market condition alone and no 200-day gate.**

Not a new signal — **the cheapest owed measurement in the record**, and D362 names it in
writing. It decides whether the 200-day gate and the calm-market sink are two states or one,
which currently makes D362's headline ambiguous: with the calm-market sink on, the filtered
cell sits **inside the gate rotation's p95** (+79.3 against p50 +30.6).

---

## 5. The gate inventory — because P1 makes every candidate need one

Every proposal above is a name-level trigger. Under P1 none of them is a sleeve until it names
a time-series gate, and §38 rule 1 requires the gate to carry **its own null: rotate the gate,
keep the trigger.**

| gate | status | note |
|---|---|---|
| market 63-bar return < 0 | **measured** (D361) | forecasts a **rebound**; it is a long-side object on this universe. 28.5% of bars, 98 episodes, median run 3 bars |
| market below its 200-day mean | **measured** (D361) | the gate the surviving fade uses; worth ~+27 bp a trade over a random gate of the same shape |
| calm market | **measured** (D362) | does part of the 200-day gate's job; **C2 decides which is the state** |
| **breadth** (share above own 50-day mean) | **unmeasured** | C1 |
| **cross-sectional dispersion** (IQR of 21-bar returns) | **unmeasured** | C1 |

**Exposure arithmetic, to be computed before any prediction** (§38 rule 2, and the standing
memory rule that predictions must be checkable): `entries per bar × hold × P(gate on)`. D350's
and D358's files already hold the entry rates. **A pre-registered exposure that is not computed
from the record before the run is not a prediction.**

---

## 6. The tension P1 does not remove, stated

A gate delivers flatness. **It does not fix the cost line, and it can make it worse** by
cutting the trade count that amortises fixed work.

The record's own numbers on the long side:

| | gross/trade | net PUB | net PB |
|---|--:|--:|--:|
| `rev_5/E1` (cleanest signal on the record: mean +43.4, median +41.8, 27 names to half P&L, top trade 1.3%, 10 of 14 years) | +43.4 | **−19** | +18 |
| `gap_reversal/E1` | +47.1 | −22 | +17 |
| `cs_spread/E2` | +71.6 | −35 | +28 |
| D359 mirror, cap 40 (D373's primary) | +160.5 | **+82.9** | +129.0 |

**Every clean, high-breadth long trigger on the record fails PUB, and the one that clears it is
the concentrated one.** That is the same trade-off in a different coordinate, and it is the
reason D373's H2 chain exists.

Three routes, and they are different bets — **naming which one a proposal takes is part of the
proposal:**

1. **Longer holds amortise the round trip.** `CLAUDE.md`'s warning binds: per-bar edge usually
   falls faster than cost, so say which moved — edge per unit exposure, or cost per trade.
2. **Size per hit rather than filter** — D362 rule 3: every trade kept, the highest t,
   two-thirds of the gain, no threshold bet. Also where D372's equal-weight question lands.
3. **Accept it at stage 1.** Under R15 cost decides nothing at the signal stage — but something
   must eventually pay a 62–106 bp round trip, and **nothing on the long side of this record
   has, except the cell D373 is testing now.**

---

## 7. Stage 0 for A1, specified — the measurement that can kill it before any design

**Instrument:** `scripts/d268_score_independence.py`, unchanged, on the mining fixture
(`us_shorts_daily_raw.csv.gz`, 1,573 names, 2010-01-04 → 2026-08-26, 35.7% delisted), on the
lagged floored deal-filtered panel the screens use.

**Inputs:** `ER_21`, `ER_63`, `ER_252` against `mom_252_21`, `trailing_return`, `rvol21`,
`atr_norm`, `vol_ratio`, `max_ret_21`.

**Reported:** the pairwise correlation matrix **and** the effective-input count (Li-Ji and
Cheverud-Nyholt, as D268 and D350 report them), so the answer is a number and not an
impression.

**The kill conditions, written before the run:**

| | condition | verdict |
|---|---|---|
| **K1** | \|ρ\| > 0.5 against `rvol21`, `atr_norm` or `vol_ratio` | **ER is a volatility proxy. Drop it.** The programme already owns five volatility levels |
| **K2** | \|ρ\| > 0.5 against `mom_252_21` or `trailing_return` | **ER is momentum re-expressed** — D268's finding for the sixth time. Drop it |
| **K3** | ER_21/63/252 carry < 2.0 effective inputs among themselves | one window, not three. **Pick one and say which**, rather than screening all three |

**And the guard that outranks all three:** ER's denominator is a sum of absolute moves and
**collapses on a frozen tape** — the exact defect that gave `fvg_dist` 829 ATRs on AVNS's four
identical $24.99 closes and `retrace_leg` a range of [−2295, +1207]. **Assert a denominator
floor and inspect ER's extreme tail by name before ranking anything on it.** A rank book
selects the tail, so a score whose tail is denominator noise selects on denominator noise.

**Cost:** minutes. **This is why A1 runs first (P2) — the cheapest measurement with the highest
chance of closing its own candidate.**

---

## 8. Order of work

| | what | why here |
|---|---|---|
| **1** | **A1 Stage 0** (§7) | P2, and it can close A1 in minutes |
| **2** | **C1 Stage 0** — block correlation of breadth and dispersion against forward drift | P1 makes a gate a precondition for *every* candidate; the premise check must precede the design (§41 rule 1) |
| **3** | **C2** — D362's unrun cell | cheapest owed measurement in the record; resolves an ambiguity in a published headline |
| **4** | **B1** — undercut-and-reclaim, with its reclaim-vs-level control built | strongest candidate; needs a control that does not exist yet |
| **5** | **A1 use (i)** as a cohort state, if Stage 0 clears — and immediately if D373's B_c fails | the successor is one state swap rather than a new construction |
| **6** | **B2**, then **A2**, then **B3** (mechanism-specified, count disclosed), then **A3** | ranked; A3 gated on its own effective-input test |

**Nothing on this list spends a holdout read.** The second slice (`order[5100:]`, never fetched,
never scored) is not cut for a stage-1 signal test, and D357's short candidate has a prior claim
on it.

---

## 9. What this record does not claim

- **No candidate here is a signal.** R15's bar is a positive gross mean per trade above its
  nulls, and nothing below has been run against a null.
- **Nothing here is closed.** §4.1's short-side assessment quotes §33 and §39; it does not
  close the short side, which is the principal's to close.
- **No pre-registration is implied.** Each candidate needs its own record, committed before its
  runner exists (R8), with direction declared (R14's fourth amendment), the four groups with
  the top trade **named and its bar printed**, both lenses, and the search cost stated.
- **The multiplicity of this file is disclosed, not summed.** Eight candidates enumerated is a
  look at the space, not a test of it. **Anything mined out of §4.6's 6,348-compound space
  carries that count and cannot be presented as multiplicity one.**
