# D614 STAGE 0 RESULT — **the verdict the pre-registration's own bars return is REAL BUT NOT TRADEABLE, and the line closes; the reading is that this is not pinning.** The noon 0DTE volume centroid's signed distance from the 15:30 price carries **−5.08 bp per sigma** on the last half hour — *repulsion*, not the attraction the mechanism predicts — at Newey-West t **−2.11** under the pre-registered estimator and **−1.96 under White's leverage-adjusted one**, and **76.6 % of the coefficient comes from ten of 1,132 sessions** whose mean absolute close move is 142 bp against 19.9 bp overall; it is **−5.73 before May 2022 and −0.16 after**, when 0DTE became the dominant flow; it is non-monotone in distance and largest where the centroid is *furthest*; the two mechanically sensible strike bands read nothing (ranks 0.905 and 0.453); the grid-only placebo, carrying no option information at all, **clears the rank bar at 0.987**; and a one-lot book on it loses money in both directions

**Stage 0 result. In sample 2016-01-04 → 2023-12-29 only; no session, option row or quote from
2024-01-01 on was read.** Nothing admitted (R15). The ES 2024+ slice stays reserved and unread: the
pre-registration made the forward read conditional on passing **both** the statistical and the
economic bar, and the economic bar fails, so there is nothing to confirm. The line closes on the
principal's reading of this record; the ruling is theirs (R15).

*2026-09-22. Pre-registration `aeceba9` predates the runner (R8); fixture
[D613](D613-FIXTURE-the-ES-option-volume-panel-in-ET-clock-buckets.md) predates both. **Runner**
`scripts/stage0_d614_expiry_pin.py`, artifact `data/stage0_d614_expiry_pin.json`, 45 s.
**Harness first:** the rebuilt `R2` and `F5` equal D581's own loader to **1e-12 on all 1,993 shared
sessions** before any statistic is scored. Every audit passed its clean case and raised on its break
inside the run: the column mapping (the named level reads +5.09 on a level-only panel where the
positional read D581 uses returns −0.01, and reading the level at the interaction's index raises);
sign in money (+4.69, raising at −4.69 negated); the centroid by an algebraic second path (raising
when the weight total is replaced by the count, 459,394.90 against 2,176.14); the trailing lag
(raising when `.shift(1)` is dropped, 23.7627 against 23.7954 at 2023-11-01); commensurability
(raising when the contract map is shifted one session); right quantity; the singularity guard; the
shift null's zero offset; and the declared-outputs guard. **Read:** the ES minute fixture and the
0DTE clock-bucket panel to 2023-12-29, the committed option fixture for strike, right and expiry,
the hourly sessions fixture and the contract specs for the component correlation, and D581's
artifact for the harness. **Not read:** anything at or after 2024-01-01, and the aggressor-flagged
year, which is the only slice that could sign the flow and is itself reserved.*

---

## 1. Six corrections made inside this run, before any number was believed

The pre-registration named five defects found in a first design. Running it found five more, three of
them in my own code, and they are recorded here because two of them changed the verdict.

| # | what was wrong | how it was found | consequence |
|---|---|---|---|
| 1 | the shift null rolled `PIN` but left `F5·PIN` built from the **unrolled** copy | reading the code after the null's spread looked impossible | bug; the null now rebuilds every derived column from each candidate |
| 2 | the pre-registered null is **anti-conservative by construction**: `PIN` shares R² 0.72 with the momentum controls and a rolled copy shares none, so the null's design is better conditioned than the observed one | its spread, 0.298, matched the textbook *simple*-regression standard error 0.333 while the fitted one was 0.586 | **amendment**: a norm-preserving Frisch-Waugh null added, spread 0.665, which matches the fitted standard error. Both are reported |
| 3 | the placebo cell carried the grid centroid **as a control and as the target**, a singular design | its null's `\|c\|` p95 came back as **6.4e13** | bug; the placebo's partner is now `PIN`. A **singularity guard** raises on any design holding one variable twice, and is proven to |
| 4 | the void check tested the placebo's **rank alone**, stricter than the pre-registration, which voids only if the placebo passes **B1–B3** | comparing the code against the record's own verdict table | **the verdict moved twice**: rank-only would have voided the trial; the pre-registered conjunction does not |
| 5 | one standard error was quoted where six disagree | asking why a rank of 1.000 sat on a t of −2.11 | **the estimator ladder is now reported**, and it does not agree |
| 6 | the economic bar was pre-registered in **bp per sigma of `PIN`** assuming sd(`PIN`) ≈ 0.3, and the unbanded primary has **sd(`PIN`) = 3.07** | comparing the bar to the expected move | the threshold is about ten times tighter relative to the move than intended. Both readings are reported and the component line settles it |

Corrections 1, 3 and 5 are ordinary bugs. Correction 2 is a **recorded amendment to a pre-registered
null**, in D555's form. Correction 4 is a correction *toward* the pre-registration, not away from it.
Correction 6 is a pre-registration defect that cannot be fixed after the fact and is disclosed
instead.

## 2. The primary

`PIN` = (the volume-weighted centroid of same-day PM-expiring ES option volume accumulated to
**12:00 ET**, minus `P1530`) ÷ `sigma30`, on the whole listed ladder. 1,132 sessions, after dropping
33 rolls, 89 sessions whose 0DTE ladder is quoted on a different future than the minute bars (7.0 %,
the pre-registered 5–9 %), and every session without a lagged `sigma30` or a traded noon ladder.

| statistic | value |
|---|---|
| coefficient | **−5.078 bp per sigma of `PIN`** (repulsion) |
| Frisch-Waugh, no interaction | −4.995 |
| Newey-West lag 5, **the pre-registered estimator** | t **−2.109** |
| week-block bootstrap (1,000 draws) | se 1.993, t **−2.548** |
| amended norm-preserving shift null, 1,113 offsets | rank **1.000**, `\|c\|` p95 1.094 |
| pre-registered shift null (anti-conservative) | rank 1.000, `\|c\|` p95 0.586 |
| **sign-flip null, 2,000 draws, seed 614** | rank **0.9555**, `\|c\|` p95 4.954 |
| the interaction, a declared diagnostic | +0.090, t 0.175 |
| expected move at mean `\|PIN\|` (2.623) | 13.32 bp |

**The sign-flip null is the one to read**, and it is the marginal one. It destroys only the direction
while keeping each session's `|PIN|` paired with that session's own volatility, which is exactly the
pairing the heavy tails live in. It puts the observed coefficient at **0.956**, a whisker over 0.95,
where the two rotation nulls say 1.000. Rotation decouples the regressor from the residual it
co-moves with, so neither rotation null can see the concentration documented in §3.

## 3. Why the coefficient is not an effect

**It does not survive the choice of standard error.** The same coefficient, six ways:

| estimator | se | t | clears \|t\| ≥ 2 |
|---|---|---|---|
| OLS, homoskedastic | 0.586 | −8.66 | yes |
| White HC0 | 2.043 | −2.49 | yes |
| **White HC3, leverage-adjusted** | 2.589 | **−1.96** | **no** |
| Newey-West lag 1 | 2.080 | −2.44 | yes |
| **Newey-West lag 5, pre-registered** | 2.408 | **−2.11** | yes |
| Newey-West lag 10 | 2.765 | −1.84 | **no** |

The gap from 0.59 to 2.41 is **heteroskedasticity, not autocorrelation**: White alone accounts for
it, and the autocorrelation of `PIN·residual` is +0.023. The finding sits *on* the bar and changes
sides with the estimator, and the estimator that clears it is the one the record happened to name.

**Ten sessions carry it, and really three do.** A slope is `Σx̃ỹ / Σx̃²`, so each session's weight is
its own extremeness in the regressor and its contribution is that weight *times* its outcome. The ten
largest-`|PIN|` sessions are heavy twice over: their distance is 6.1× typical, giving them **33.6 %**
of the denominator, and their mean absolute close move is **142.3 bp** against 18.8 bp for everyone
else, 7.6× typical. Their share of the numerator is **78.7 %**, and dropping them moves the
coefficient from −5.078 to **−1.189**. `corr(PIN², residual²)` is +0.381 with `R2`'s kurtosis at 38.8.

**They are crisis afternoons, and they are named** (D322 asks for the bar, not the count):

| session | `PIN` | `R2` | share of the numerator | what the day was |
|---|---|---|---|---|
| **2020-02-28** | −17.55 | **+265.8 bp** | **+0.379** | the first COVID crash week |
| **2020-03-13** | −17.73 | **+457.8 bp** | **+0.356** | the Friday of the circuit-breaker week |
| 2020-03-02 | −15.36 | +188.7 bp | +0.073 | the Monday rebound |
| 2018-02-07 | −17.59 | −98.4 bp | −0.068 | volmageddon week |
| 2016-11-09 | −19.22 | −20.8 bp | −0.012 | the US election night |

**Three sessions are 81 % of the numerator and all three are the February-March 2020 crash.** Every
one of the ten is a crisis day — the election, volmageddon, the Christmas 2018 bottom, the COVID
crash. On each the ladder sat far below the price and the close rallied violently, and the product of
those two is the entire coefficient. This is not a marginal statistical effect; it is a crisis-day
artefact. The repository's rule applies with force: predict a book from the trimmed statistic, not
the full one (D431).

**And the trades do not cluster at zero**, which is the other way a slope like this can be misread.
Only 1.6 % of sessions capture exactly nothing and 12.4 % fall inside one round trip; the quartiles
are −$22 and +$20 and the 5th-to-95th range is about ±$80. The median is zero because the signed
distribution is near-symmetric, not because of a pile at the origin. The typical session captures
nothing directional with roughly $20 of noise either way, against a $4.25 cost, and whatever edge
exists lives in the same tail as the coefficient.

**The shape is wrong for a pull.** By tercile of `|PIN|`:

| tercile | mean `\|PIN\|` | coefficient | n |
|---|---|---|---|
| nearest | 0.650 | −1.705 | 377 |
| middle | 2.002 | **+0.108** | 377 |
| furthest | 5.210 | **−7.202** | 378 |

Non-monotone, sign-inconsistent in the middle, and largest where the centroid is *furthest* from the
price. A hedging pull toward a strike is strongest near it. The pre-registered prediction P-5 said
so and fails.

**It is absent in the era the mechanism needs.** Before 2022-05-02 the coefficient is **−5.728** on
750 sessions; after, when the Tuesday and Thursday families filled the week and 0DTE became the
dominant flow, it is **−0.160** on 382. That is the opposite of P-8. And the mechanical artefact runs
the same way: the grid centroid's dispersion is 26.6 pre-2022 against 11.8 after, and the half-step
sawtooth is 0.378 sigma pre-2022, because five points was 23 bp at ES 2100 and 10.5 bp at 4767.

**The sensible bands read nothing.** The primary deliberately used no band, because any band centred
on the price truncates the side the price came from. The two banded members of the family, which are
the mechanically motivated ones, are inside their nulls:

| band | coefficient | NW t | amended rank | expected move |
|---|---|---|---|---|
| no band (primary) | −5.078 | −2.11 | 1.000 | 13.32 bp |
| ± 4 sigma | −2.967 | −1.00 | 0.905 | 1.93 bp |
| ± 2 sigma | −2.028 | −0.49 | 0.453 | 0.61 bp |

**And the rank bar is clearable with no option information at all.** The grid-only placebo — the
equal-weighted centroid of the same listed strikes, carrying no volume — earns +0.127 bp per sigma
at **rank 0.987**, above its own `|c|` p95. It fails the pre-registered conjunction, because every
robust t on it is below 2 (HC0 1.93, HC3 1.64, HAC(5) 1.64, HAC(10) 1.51, against OLS 2.99), so B4
does not void the trial. But a bar that a no-information conditioner clears on rank is not doing
work, which is what the review predicted before the run and what §1's correction 2 explains.

**The controls are clean, which is the one thing that went right.** All three sit inside their nulls,
including the horizon-matched arm that only the D613 panel makes buildable:

| control | holds fixed | coefficient | NW t | amended rank |
|---|---|---|---|---|
| open interest, same 0DTE strikes | horizon, strike set | +0.024 | +0.35 | 0.338 |
| **volume, nearest later expiry** | weighting, ladder | −0.198 | −1.23 | 0.940 |
| open interest, nearest later expiry | ladder, moneyness | +0.078 | +1.16 | 0.907 |

So whatever the primary is reading, it is not the strike ladder's geometry and not the option
activity of a neighbouring expiry. It is ten sessions in the pre-0DTE era.

**And the noon cutoff bought less blindness than hoped.** `corr(PIN, PIN1530)` is **0.979**: the noon
ladder and the 15:30 ladder are nearly the same object, 61.9 % of the pre-15:30 volume being in by
noon. The pre-registration set the prior low for this reason and was right to. The 15:30 version,
whose in-sample reading was already known and is carried here as description only, gives −5.418 at
t −1.82.

## 4. The variance block, descriptive, and null on its one clean measure

Reported with no verdict weight: an adversarial review measured this block in sample before the
pre-registration, so it is not blind. The close is **louder** than the mid-afternoon on **82.5 %** of
sessions, log ratio +0.606; the bipower ratio agrees at +0.565 with correlation 0.925, so bid-ask
bounce is not driving it.

| concentration measure | tercile difference in the variance ratio | corr with sigma30 (guard ≤ 0.40) | corr with 1/n (guard ≤ 0.60) |
|---|---|---|---|
| raw Herfindahl | +0.175 | **−0.493 fails** | **+0.675 fails** |
| floor-normalised | +0.185 | **−0.489 fails** | **+0.649 fails** |
| **nearest nine strikes, fixed count** | **+0.067** (year-block SE 0.164) | −0.172 passes | +0.250 passes |

The two guards that replaced D409's Dg1 — which the review showed could not fire — **do** fire, on
exactly the measures the review said were contaminated. And on the only measure that passes both,
the effect is **+0.067 against a standard error of 0.164**: nothing. So the declared consistency test
A-4 has no significant variance leg to be consistent with, and no claim about dealer gamma's sign is
made from this block.

## 5. Component line, as CLAUDE.md requires whatever the verdict

One MES, in at 15:30 in the cell's direction, flat at 16:00, cost computed by the runner at
**$4.25 a round trip** ($3 commission plus one crossed tick at $1.25 with MES at $5 a point);
breakeven **1.208 bp a side**. Both directions, because both signs were to be scored.

| | gross/session | net/session | **gross Sharpe · Sortino** | **net Sharpe · Sortino** | hit | payoff | median | skew · kurtosis | trimmed 1 % both tails | ex-top 1 % | ex-bottom 1 % | maxDD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| attraction | −$2.49 | **−$6.74** | −0.69 · −0.78 | −1.87 · −2.19 | 0.433 | 0.888 | −$4.25 | −1.31 · 18.2 | −$6.15 | −$8.93 | −$3.96 | −$7,729 |
| repulsion, the sign found | +$2.49 | **−$1.76** | **+0.69 · +1.00** | −0.49 · −0.72 | 0.443 | 1.135 | −$4.25 | +1.31 · 18.2 | −$2.35 | −$4.54 | +$0.43 | −$2,698 |

**Both ratios on both lines** (R17): an earlier pass of this runner reported gross Sharpe without its
Sortino, which is exactly the substitution the rule forbids, and the omission is recorded rather than
silently repaired. The repulsion book's **gross Sortino of +1.00 exceeds its gross Sharpe of +0.69**,
because the skew is +1.31 and the downside deviation is therefore the smaller denominator — gross,
the construction looks respectable. **Cost is what destroys it**, taking the pair to −0.49 and −0.72,
and the gross itself is the crisis-day tail of §3 rather than a repeatable edge.

Exposure is every session in the panel, 30 minutes each, so exposure does not separate the two
directions. Drawdown is in **negative dollars from the running peak** of the cumulative net series,
not a fraction of peak: a one-lot book has no equity base to divide by, and the convention is stated
because the repository holds both signs and D542 requires each file to say which it carries.

**ρ with the admitted MACD arm: −0.136** on 1,130 overlapping sessions, computed inside this runner
at MNQ minimum size rather than quoted from another record's window — the error D466 caught.

The economics are decisive and they reconcile the apparent contradiction in §2. The regression's
13.32 bp expected move is magnitude-weighted and lives in the far tail; a **sign-only** book, which
is all a one-lot MES position can express, realises **1.16 bp of gross move a session** against a
2.4 bp round trip. The median session for both directions is exactly minus the cost, meaning the
median trade earns nothing gross. Not a candidate, in either direction, and entered here for the
ledger's completeness only.

## 6. The predictions, and what the bars returned

| # | prediction | outcome |
|---|---|---|
| P-1 | primary above the amended null's `\|c\|` p95 with `\|NW t\| ≥ 2` | **holds** on the pre-registered estimator, **fails** on HC3 and HAC(10) |
| P-2 | the placebo fails the same conjunction | **holds** — but it clears the rank bar alone at 0.987 |
| P-3 | all three controls inside their nulls | **holds** |
| P-5 | stronger where `\|PIN\|` is small | **fails**, and in the informative direction |
| P-6 | the commensurability drop is 5–9 % | **holds** at 7.0 % |
| P-7 | the sawtooth is larger pre-2022 | **holds**, 26.6 against 11.8 |
| P-8 | at least as strong after 2022-05 | **fails**: −5.73 against −0.16 |
| B-5 | the economic bar, `\|c\| ≥ 15` bp per sigma | **fails** at 5.08 |

**Verdict as the pre-registered bars return it: REAL BUT NOT TRADEABLE, and the line closes.** The
reading this record puts beside that verdict is stronger and points the same way: **this is not
pinning.** The sign is repulsion where the mechanism predicts attraction; the magnitude is 77 % ten
sessions; the shape rises with distance instead of falling; the effect is absent in the era 0DTE
dominates; the bands that make mechanical sense read nothing; and the rank bar is clearable without
any option content. What survives is a description, not a mechanism: on ten pre-2022 sessions the
full-ladder volume centroid sat far from the price and the close moved violently, in the direction
away from the centroid.

## 7. What this record does not do

It does not read the reserved slice, and does not pre-register a forward test: the pre-registration
made that conditional on both bars and the economic bar failed. It does not re-specify the
conditioner, the band, or the window on this data, which is spent for a blind test of this
construction. It does not claim a dealer-positioning convention: with no aggressor side the sign
identifies nothing, and §4's variance leg is null on its one clean measure. It does not test NQ or
the weekly families separately. **What a real test of index-option pinning would now need** is the
aggressor-flagged flow that signs who bought the 0DTE contracts — the 2025-09 → 2026-09 `tbbo` year,
which is inside the reserved period — or a market where the position, not the turnover, is
observable. Neither is available to this line without the principal's word.

**Design amendments, recorded:** the norm-preserving null of §1 correction 2; the placebo's control
partner and the singularity guard of correction 3; the estimator ladder and tail diagnostics of
correction 5, added as reporting rather than as tests. The D613 panel, the runner, its audits and the
six corrections above are what this trial leaves behind.
