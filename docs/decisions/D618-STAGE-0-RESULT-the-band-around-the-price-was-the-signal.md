# D618 STAGE 0 RESULT — five cells survive the construction screens, none survives its own null, and the thing that looked like an interior solution was the band being centred on the price it predicts from

**Pre-registration:** [`D618`](D618-PRE-REG-the-sharpened-0DTE-ladder-range-or-independence.md), committed
before the runner existed and amended once (also before the runner) to carry its control set.
**Runner:** `scripts/stage0_d618_sharpened_ladder.py` · **artifact:** `data/stage0_d618_sharpened_ladder.json`
· 60 s · in-sample 2016-01-04 → 2023-12-29, 1,993 ES sessions, a 0DTE PM ladder on 1,263 of them,
267,676 (session, strike) cells. **No session at or after 2024-01-01 was read.**

## 0. AMENDED 2026-09-22 — the first version of this record reported a verdict that rested on a broken screen

The principal asked whether the construction screens were too harsh. They were worse than harsh: **one of
them was invalid, and a known-answer case proved it.** A conditioner built from the **actual 16:00 close** —
perfect information about the thing this study predicts — was **rejected**, as were all 72 real cells, by
screen S1b.

**What was wrong.** S1b as pre-registered required `sd(LADDER) ≥ 3 × sd` of the same cell with **flat
weights over its positive-weight strikes**. For any smooth weight the positive-weight set is the whole
220-strike ladder, whose centroid sits about **23σ** from the price, so the ratio asks "is this as dispersed
as the entire listed ladder" and therefore **penalises precisely the concentration a real signal has**. The
oracle scored 0.05, a diluted oracle 0.03, and pure grid arithmetic 1.00 — the intended ordering inverted. A
within-session permutation comparator fails the same way and for the same reason (oracle 0.04, grid 1.00): a
reshuffle scatters weight across the ladder, so every informative object is *narrower* than its own
permutations.

**What replaced it.** The question S1b was for — *is this distinguishable from the unweighted centroid of the
same eligible strikes* — is answered directly by **`|corr(LADDER, PING)| ≤ 0.50`**. The grid control **is**
PING, so it scores exactly **1.0000** by construction; the oracle, diluted and weak oracles score
**0.0605, 0.0359 and 0.0196**. The ceiling is the midpoint of that calibrated gap and was read **only off
the synthetic controls, never off the real cells**. PING also remains a regression control, so partial
overlap is caught a second time at scoring.

**This is a post-hoc change to a pre-registered screen, which is what pre-registration exists to prevent**,
so three things are stated plainly. The justification is a **validity failure demonstrated on a
known-answer case**, not a preference about the outcome. The replacement was calibrated on synthetic objects
alone. And the change runs **against** the convenient answer: it takes the number of scoreable cells from
**0 to 5** and gives the hypothesis more chances, including its own pre-registered primary, rather than
fewer.

**What changed, and what did not.**

| claim in the first version | status now |
|---|---|
| "of 72 cells not one passes the screens" | **wrong** — five pass, including the pre-registered primary |
| "no return was scored for any cell in the specified family" | **wrong** — five cells were scored |
| "the weights do nothing, flat-weight ratio 1.00" | **withdrawn** — that statistic was malformed |
| "a third source of variance, the listed ladder's extent" | **withdrawn as stated.** The Δ-OI cell's status is now settled by *scoring* it — coefficient −0.0006 at t −0.01 — which is better evidence for the same conclusion |
| the band-around-the-price artefact | **stands**, on statistics the broken screen never touched |
| nothing goes forward; the line stays closed | **stands** |

## 1. The screens, which are still the study

Applied to every cell before any return is read. The band is centred on the **prior settlement**, as the
record specifies.

**Five cells pass all five conditions:**

| cell | sd (σ) | corr(PING) | corr(DAY0) | grid R² | strikes |
|---|---:|---:|---:|---:|---:|
| **`gamma_doi \| all \| w30 \| now`** — the pre-registered primary | 0.529 | +0.0371 | −0.048 | 0.003 | 220 |
| `gamma_doi \| all \| w10 \| now` | 0.805 | +0.0361 | −0.049 | 0.003 | 220 |
| `doi \| all \| w30` | 13.077 | +0.1321 | −0.134 | 0.003 | 220 |
| `doi \| all \| w10` | 19.012 | +0.1107 | −0.142 | 0.002 | 220 |
| `gamma_oi \| all \| w10 \| now` | 0.273 | +0.1085 | −0.014 | 0.000 | 220 |

The 67 rejections fall into two clean groups, and both are substantive rather than threshold artefacts.

**The day's move rejects every pre-session-anchored cell.** `gamma_doi|all|w30|pre` reads corr(DAY0)
**−0.507**, `gamma|all|w30|pre` −0.533, `gamma_oi|all|w30|pre` −0.532, and D614's own volume centroid
**−0.480** — against a ceiling of 0.40. Measured against the *full* 09:30 → 15:30 move rather than the
morning leg the screen uses, those become **−0.729, −0.738, −0.738 and −0.742**, so the rejections are not
marginal in either measure.

**Banding makes a cell into its own grid centroid.** Every banded cell anchored pre-session reads
corr(PING) between **+0.998 and +1.000**: with a median of 6 strikes in a ±3-step band the weighted centroid
*is* the band's midpoint. That is the honest version of what the first draft of this record tried to say
with a broken ratio — not "the weights do nothing" in general, but "inside a tight band centred away from
the price, the weighted centroid carries no more than the band's own position".

## 2. The band around the price, which is the finding that survives

The pre-registered **break** is centring the band on P1530. The runner's first pass did exactly that. Under
the corrected screens the comparison is sharper, not weaker:

| the same cell | band on the prior settle (specified) | band on P1530 (the break) |
|---|---:|---:|
| `gamma_oi \| 3step \| w10 \| pre` sd | 5.590σ | 0.913σ |
| …corr(DAY0) | **−0.543** | **−0.210** |
| …corr(PING) | **+0.998** | **+0.312** |
| cells passing all five screens | **5** | **15** |

Centring the selection on the current price does two things at once: it **removes the day's-move confound**
(−0.54 → −0.21) and it **makes the object distinguishable from its own grid centroid** (+1.00 → +0.31).
Both are properties of the *selection*, not of the option data, and they treble the number of cells that
appear admissible. **A band is a selection, and a selection centred on the outcome's own starting price is
D614's grid artefact one level up.** The two bands pick different strike sets on **90.7 %** of the 1,263
sessions, median Jaccard overlap **0.333**, so they are not variants of one object.

## 3. The five scored cells: none clears its null

| cell | c | NW t | shift-null rank | flip-null rank | expected move | tail bar |
|---|---:|---:|---:|---:|---:|---|
| **`gamma_doi\|all\|w30\|now`** (primary) | **+1.663** | +0.96 | 0.757 | 0.508 | $0.66 | held |
| `gamma_doi\|all\|w10\|now` | −0.262 | −0.55 | 0.321 | 0.299 | $0.16 | **failed** |
| `doi\|all\|w30` | −0.0006 | −0.01 | 0.008 | 0.009 | $0.02 | **failed** |
| `doi\|all\|w10` | −0.062 | −1.93 | 0.938 | **0.959, above p95** | $2.43 | held |
| `gamma_oi\|all\|w10\|now` | −2.300 | −0.39 | 0.725 | 0.317 | $0.15 | **failed** |

**The pre-registered primary has the predicted sign.** `gamma_doi|all|w30|now` reads **+1.663** —
*attraction*, which is what the pinning mechanism predicts and the opposite of D614's −5.08 — and it is
**statistically nothing**: NW t +0.96, rank 0.757 in its own shift null and 0.508 in the sign-flip null,
with an expected move of **$0.66 against a $4.25 round trip**. The tail bar holds, so it is not a crisis-day
artefact; there is simply no effect.

**No cell clears both nulls.** `doi|all|w10` clears the flip null at 0.959 and fails the shift null at
0.938; nothing else is close. The family maximum |t| is **1.961** against a family-max null p95 of
**2.714** (rank 0.798), while each cell's own p95 runs **1.86–2.13** — so looking at five correlated cells
costs about 0.6 of t, and the largest t in the family does not reach even a single-cell bar.

**No cell clears the economic bar.** The best expected move is $2.43 against $4.25.

## 4. The predictions, against what happened

| # | prediction | outcome |
|---|---|---|
| 1 | no cell has both range (sd ≥ 1.0σ) and independence (\|corr(DAY0)\| ≤ 0.40) | **falsified** — `doi\|all\|w30` (13.08σ, −0.134) and `doi\|all\|w10` (19.01σ, −0.142) have both, pass every screen, and were scored. They carry no information about the close (t −0.01 and −1.93). The prediction was wrong; its conclusion was reached by scoring instead. |
| 2 | `\|gamma\|×\|Δoi\|` unbanded passes the measurement floor | **held** — sd **0.529σ**, corr(DAY0) −0.048, corr(PING) +0.037. The review predicted ≈0.24σ; it is twice that, and it is the primary. |
| 3 | every band of 2 steps or fewer fails S3 or S4 | **held, all eighteen** — 2-step bands hold a median of 4 strikes against a floor of 5; 1-step bands hold 2. Under the corrected screen they also fail on corr(PING) ≈ 1.000. |
| 4 | Δ-OI is not independent of the conditioners already measured | **held** — corr **+0.523** with the OI-weighted centroid and **+0.335** with the volume centroid. |
| 5 | if a cell is scored the coefficient is positive | **supported in sign by the primary** (+1.663) and by nothing else; four of the five are negative, and none is distinguishable from zero. |

## 5. The Δ-OI gate

The residualised coefficient is **+0.0820** against **−0.0008** with the OI and volume centroids removed,
so the raw association is nil and the two controls absorb offsetting parts. Scored directly, the Δ-OI
centroid reads **−0.0006 at t −0.01** on the half-hour: the one improvement that addressed D614's named
defect measures **position rather than turnover, is genuinely independent of the day's move, and carries no
information about the close.** That is a cleaner negative than the first version of this record gave.

**D616's column earned its commit.** Of 12,594,319 option rows, **339,359 were refused because the two
`oi_ref_session` values were not adjacent**, against **31,589** refused by the session calendar alone — ten
times as many bad pairs invisible to the calendar, because a publication is usable on exactly one session
so publication times never repeat (0.0000) and CME's preliminary-then-final revision cannot be seen in
them. Zero-delta share **0.4850**, genuine against a revision rate under 2.5 %. Settlement-implied vol
inverted on **0.9809** of attempted rows, median **0.312**.

## 6. Corrections made to or inside this study — ten

1. **S1b was invalid** (§0). It rejected a perfect oracle and all 72 cells. Replaced, calibrated on
   controls, and **this changed the verdict's route**: 0 scoreable cells became 5.
2. **The band anchor.** The runner first banded on P1530, the pre-registered *break*. Fixed to the prior
   settlement — which is how §2's finding surfaced at all.
3. **The shift null compared a signed observed coefficient against an absolute null**, making every rank
   0.000 by construction. Fixed to |obs| against |null|.
4. **The verdict logic** conflated "has range and independence" with "passes the screens".
5. **`vol_to_1530` is not D614's comparator** — D614's object was the **noon** cutoff, which is why D613's
   panel exists. Both carried, named apart; the family is **72 cells, not 64**.
6. **S2's label in the pre-registration is wrong**: it says the 09:30 → 15:30 move and the statistic is the
   09:30 → 12:00 leg (D614's `DAY0`, faithfully). Measured both ways, **no screen verdict changes**, and the
   confound is *larger* on the full move (−0.73 where the record reports −0.51).
7. **The record's own internal tension** — §3 says a failing cell is not scored, §7 says the estimator
   ladder is reported for every cell — resolved toward §3.
8. **The additivity bar of 1e-12 is in log units** while the runner works in basis points; the runner uses
   1e-9, a decade stricter than the equivalent. Measured 1.4e-12 bp.
9. **The right-quantity check** first demanded R10 ≠ R30 on over 99 % of sessions and fired on real data,
   because a genuinely flat 15:30–15:50 leg makes them equal. Replaced by a declared ceiling on the
   coincidence share.
10. **The permutation audit's first break was wrong** (it asserted flat weights should raise); the break
    that tests something is a reduction that lost the strike-weight pairing. Plus a key-name error on
    `se_ladder`, and `maxDD_usd` escaping `label_drawdown_convention.py`'s end-anchored key regex, renamed
    to `maxdd` so the sign marker is derived rather than typed.

## 7. The component line

On the **pre-registered primary**, computed inside the runner at one MES and the cost that size pays
($4.25 a round trip), n 1,185. This one carries verdict weight.

| direction | gross Sharpe | gross Sortino | net Sharpe | net Sortino | net $/session | hit | maxdd |
|---|---:|---:|---:|---:|---:|---:|---:|
| attraction | +0.041 | +0.057 | **−1.218** | **−1.705** | −$4.11 | 0.478 | $5,149 |
| repulsion | −0.041 | −0.050 | **−1.301** | **−1.614** | −$4.39 | 0.503 | $5,266 |

ρ with the admitted MACD day-session arm: **+0.034** over the overlapping sessions. Gross is
indistinguishable from zero in both directions, so this is not a cost failure — there is nothing for cost to
destroy. Drawdown convention: **positive dollars from peak** (D542).

## 8. What is spent, and what this closes

Returns were scored for **five cells** in the specified family and for the endogenous-band diagnostic
cells, all disclosed above. The **ES day-session 2024+ slice stays unread**;
[D617](D617-FIXTURE-the-ES-option-signed-flow-census-from-the-tbbo-year.md)'s census window stays unspent
for every return-bearing construction.

**The axis of "signed distance from the price to a weighted strike" closes for ES 0DTE.** It closes on two
legs that are now independent of each other. The construction leg: a conditioner on this axis takes its
dispersion from the day's own move (−0.48 to −0.74 for every pre-session-anchored weight), or from the
band's own position (corr with the grid centroid 0.998–1.000 once banded), and the one construction that
escapes both — Δ-OI unbanded — carries no information about the close. The outcome leg: the pre-registered
primary has the right sign and a t of +0.96, the family maximum |t| of 1.961 does not reach a single-cell
bar let alone the family bar of 2.714, and the best expected move is $2.43 against $4.25.

Nothing on this axis is pre-registered again without a fixture that changes that arithmetic — per-strike
dealer inventory, which no source on this disk carries.

**And a method lesson this study paid for twice: a screen is a measuring instrument, so it needs a
known-answer case before it is trusted.** S1b was written to catch a real failure mode, was stated
plausibly, passed a synthetic unit test, rejected everything, and was wrong. What exposed it was building an
object whose answer was known in advance and checking that the screen admitted it. Any future gate that
*rejects* rather than *reports* should be shown to pass an oracle before its rejections are believed.
