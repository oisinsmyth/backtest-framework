# D581 STAGE 0 DESIGN — **the gamma-conditioned close on ES: does the sign of dealer net gamma, computed from public option open interest under the stated dealer convention, decide whether the last half-hour continues or reverts the hour before it?** The deposit's §4 discriminator as a premise check, with the 0DTE era split and the wrong-sign kill declared, on 2016-01 → 2023-12; no reserved session read

**Stage 0 design, committed before the options fixture, its builder and the runner exist.
Diagnostic on 2016-01-04 → 2023-12-29; no ES session, option row or quote from 2024-01-01 on is
read; no cost, no book.** Nothing admitted (R15).

*2026-09-20. `GAMMA_CONDITIONED_CLOSE.md` derives a mechanical flow: dealers delta-hedge the
options they are short, the hedge per unit of price move is their net gamma, and its sign says
whether the hedge amplifies (negative gamma: buy rallies, sell dips) or dampens (positive:
the reverse) the underlying — largest in the final half-hour, every day, because 0DTE gamma
peaks at the bell. Its §4 says the study has an edge only if the gamma regime predicts which of
continuation and reversion the close shows; its §9 makes no regime dependence terminal (kill 2),
forbids flipping a wrong sign (kill 3), and says an effect equally strong before 2022 is a
generic close effect, not this mechanism (kill 4). Its premise correction of 18 Sep 2026 says
prior-close open interest sees only the carried minority of 0DTE gamma; the intraday 0DTE
build needs intraday options data. This record tests the carried mechanism the deposit calls
"real but weaker", carries the era split and the wrong-sign rule from the start (the D578
lesson), and adds one thing the deposit thought it lacked: the archive on disk holds every ES
option's one-minute bars, so an intraday 0DTE volume build is available as a declared,
unpromotable diagnostic.*

**What is on disk, and what is quoted.** ES regular-hours one-minute bars 2016-01-04 → (D462,
`fut_ES_rth_1m.csv.gz`, gates green). ES settlements by session (the settlement strip, D556).
One-minute bars for **every ES-family option** — quarterlies (ES), end-of-month (EW), Friday
weeklies (EW1–EW4), and the Monday–Thursday dailies (E1A–E5A, E1B–E5B, E1C–E5C, E1D–E5D) —
inside the raw `ohlcv-1m` archive (864,813 option instruments in the 2025 file; 35,690 in the ES
family), with the aggressor-flagged `tbbo` for 2025-09-11 → 2026-09-11 only. **Not on disk:**
option open interest and the strike/expiry table, which live in the `statistics` and
`definition` schemas the 2026-09-11 pull took for the 41 futures roots and not their options.
**Quoted on 2026-09-20** (`scripts/quote_es_options_pull.py`, metadata calls only, artifact
`data/es_options_pull_quote.json`): `ES.OPT` parent, 2016-01-01 → 2026-09-11, **statistics 37.41
GB and definition 10.28 GB, 47.69 GB, USD 0.00 under the CME Standard subscription** that runs to
about 2026-10-11 (the last twelve months alone: 5.3 GB, also USD 0.00). The pull is the
principal's call; it moves no bytes until given.

---

## 0. The fixture this design needs, built and gated before the runner reads it

`scripts/build_fut_es_options_eod.py` → `data/fixtures/fut_es_options_eod.csv.gz` (gitignored by
pattern, in the manifest by hash; meta tracked). One row per (usable session, option instrument):
product family, expiry date, strike, put/call, **open interest as of the prior close**, the
prior settlement, and the option's minute-bar volume on the session to 15:30 ET (from the
archive already on disk). Keyed the way D497 and D521 key the futures open interest: **on the
session each figure is first USABLE** — the `statistics` row published on the evening of T−1
describes T−1's close and is usable for session T; a row published on T is not. The id → (family,
expiry, strike, right) map comes from `definition` through **windowed** mappings, never a flat
dict (D520), and the two missing-value sentinels are filtered (`UNDEF`, and the exact 0.0
settlement D526 found). Gates: (G1) OI ≥ 0 and settlement > 0 on every kept row, the two sentinel
counts reported; (G2) every session's usable OI date is strictly before the session (a
known-answer session asserted); (G3) the expiry calendar — a same-day-expiring family present on
every Friday from 2016, every Monday and Wednesday from their launches, every weekday from
2022-05 (the Tuesday/Thursday launch), with the first date of each family reported and the
share of sessions with a 0DTE family; (G4) the number of strikes with OI per session, its
median and the sessions under 20 listed; (G5) on ten sessions chosen by seed, the sum of OI by
family recomputed by a second path from the raw statistics rows (pandas pivot, never the
builder's loop); (G6) the settlement-implied volatility inverts for ≥ 99 % of near-the-money
rows (|K/S − 1| < 5 %), the failures counted. **The builder writes the whole pull; the runner
filters `session < 2024-01-01` and asserts the last session it reads.** Decode on the system
interpreter, cached per file; the statistics decode is the cost — projected at 40–60 minutes on
six workers from D497's rate over its 10.9 GB, stated before launch and measured on the first
file first.

## 1. The quantities

- **The session and the windows.** ES regular hours, 09:30–16:00 ET, sessions from the RTH
  fixture with ≥ 380 bars. `P(t)` is the close of the minute bar ending at *t*.
  **F5 = log P(15:30) − log P(14:30)** (the move the dealer has to hedge), and the outcomes
  **R2 = log P(16:00) − log P(15:30) (primary)**, R1 = to 15:50, R3 = from 15:45, in bp.
- **Carried net gamma, F1.** For every option with prior-close OI on session *d*, Black-76
  gamma at 15:30 ET with the futures price P(15:30), the volatility implied from the prior
  settlement (inverted by bisection; a row that will not invert within [1 %, 400 %] is dropped
  and counted), rate 0, and time to expiry the remaining trading time to the option's 16:00 ET
  expiry (the same-day expiry at 15:30 has τ = 30 min of a 252 × 6.5 h year — the deposit's §2
  time-of-day weighting, with no free parameter). Then
  `F1 = Σ_K gamma_K × (C_K − P_K) × 50 × P(15:30)² × 0.01`, dollars of dealer hedge per 1 %
  move, under the **stated dealer convention: customers are net long puts and net short calls,
  so dealers hold the opposite; calls enter +, puts −.** That convention is an assumption, the
  one place the sign can be wrong, and kill 3 governs it. **F2 = sign(F1)**; **F3** = (P(15:30)
  − flip level) / ATR(20 sessions), the flip level the price at which F1 crosses zero, found by
  re-evaluating F1 on a grid of ±5 % in 0.1 % steps; **F4** = the same-day expiry's share of
  Σ|gamma × OI|.
- **The 0DTE volume build, F1b, diagnostic.** For the same-day-expiring families, the minute
  bars' cumulative volume to 15:30 by strike and right, entered with the same sign convention
  and the same 15:30 gamma. It has no aggressor side (the archive's bars do not carry one before
  2025-09), so it assumes every 0DTE contract traded was bought by a customer; it is reported
  beside F1 and never decides anything. The `tbbo` year that could sign it is inside the reserved
  period and is not read.
- **The premise's persistence** ([[stage-0-premise-check]], [[slow-conditioners-have-n-eff-in-years]]):
  the day-to-day autocorrelation of F2, the number of regime switches per year, the share of
  sessions with F2 < 0, and the magnitude of F1 by year (the level path). A conditioner that
  switches ten times a year has n_eff in years and the record must say so before T1 is read.

## 2. The tests, with predictions

| # | test | statistic | predicted | falsifier |
|---|---|---|---|---|
| **T1 — the discriminator** (§4, kill 2 and kill 3) | `R2 = a + b·F5 + c·F5·F2 + d·F2 + e`, Newey–West lag 5, on all sessions with F1; and the slope of R2 on F5 within F2 < 0 and within F2 > 0 sessions separately | **c < 0** (positive gamma dampens: the F5-slope is lower when F2 = +1), **NW t ≥ 2**, and **rank ≥ 0.95 in the day-shift null** — the F2 series shifted against the (F5, R2) pairs by every k ∈ [10, N−10] sessions, enumerated (it keeps F2's persistence and destroys its alignment); the within-regime slopes ordered `b_neg > b_pos` | **c ≥ 0 within the null → no regime dependence, TERMINAL (kill 2). c > 0 above the null's p95 → the convention is wrong; the sign is NOT flipped, the record says so and stops (kill 3)** |
| **T2 — scale** | R2's slope on F5 by tercile of |F1| within each regime; Spearman of |F1| with the signed conformity `−F2 · sign(F5) · R2` | effect monotone in |F1|; top tercile ≥ 2× bottom | flat in |F1| → the sign is not carrying the size; diagnostic |
| **T3 — the 0DTE era** (kill 4; the D578 lesson) | T1's c, t and rank within **2016–2021** and within **2022–2023** (every weekday has a same-day expiry from 2022-05); and within 2023 alone | **stronger in 2022–2023**; **2023 alone holds at rank ≥ 0.90**; and c within 2016–2021 not larger in magnitude than within 2022–2023 | equal or stronger before 2022 → a generic close effect, not this mechanism: **NOT SUPPORTED as this study** (kill 4), whatever the pooled number says |
| **T4 — 0DTE days against the rest** | T1 within sessions that have a same-day expiry and within those that do not (only 2016–2021 has both) | the effect lives on 0DTE sessions; on non-0DTE sessions c inside the null | present equally on non-0DTE sessions → the same as kill 4 |
| **T5 — the flip level** (open question 3) | T1 with F2 taken from the sign of F3 at 15:30 (which side of the flip the price is) in place of sign(F1); the share of sessions where the two disagree | agreement ≥ 90 %; T1 unchanged in sign | diagnostic |
| **T6 — the diagnostic build** | T1 with F1b in place of F1, and with F1 + F1b | reported; no prediction, no gate | |

**Nulls.** T1's null is the enumerated day-shift of F2 (SE 0); beside it the day-shift of F5
(which destroys the pairing and keeps F2 in place) as the second lens, and the sign-flip of F2
on random halves is NOT used (it would erase the regime's persistence, which is part of what is
being tested). The within-regime slopes carry week-block bootstrap SEs.

**Decision rule, declared.**
- **SUPPORTED** — T1 holds pooled; T3 holds (stronger in 2022–2023, 2023 alone ≥ 0.90); the
  within-regime slopes ordered. Next, in separate records and in this order: the cost gate on
  MES in the 15:30–16:00 window at the quoted spread (`tbbo` 2025-09 → 2026-09: a quote read
  inside the reserved period, **put to the principal first**); then the pre-registration of the
  conditioned close as a flat-by-default construction, choosing between continuation and
  reversion legs on this record's window ([[choose-the-object-on-the-pre-registrations-own-window]]).
- **WRONG SIGN** — c > 0 above the null. Terminal by kill 3; the record names the convention as
  the failed assumption and nothing is flipped.
- **GENERIC** — T1 holds but T3 or T4 fails. The close has a conditional effect that is not the
  0DTE mechanism; the record says what it is co-moving with and stops; no construction on it
  here (it is the more crowded study the deposit declines).
- **NOT SUPPORTED** — T1 inside the null. Terminal by kill 2.

**Chance.** T1 has one declared sign, one bar and an exact null; T3 and T4 are declared
directions. The joint claim is a sign, a size ordering and an era ordering.

## 3. Reported beside, diagnostic, unpromotable

The premise's persistence block from §1 before any T-statistic; F1's magnitude and F4's 0DTE
share by year; R1 and R3 in place of R2; the within-regime means of R2 by sign of F5 (the
2 × 2 table, in bp and in MES ticks: $1.25 a tick, ~0.25 bp at $5,000); the trimmed means
([[tail-carried-per-trade-edge-does-not-book]]); the ten largest |R2| sessions named with their
F2 and F5 ([[name-the-top-trade]]); the sessions dropped for a missing OI row or a failed
inversion, counted by year; and D463's last-half-hour predictor `rROD` beside F5, so that
whatever T1 finds is placed against the market-intraday-momentum effect already scored on ES
(K3: gross +0.62, net −0.29 at micro cost, D466).

**Audits, each proven to RAISE on a break that hits what the assertion reads:** (a) Black-76
gamma against a closed-form known answer (at-the-money, one-year, 20 % vol) and by a second
implementation (scipy's normal pdf against a hand-written one); break = a negated d1; (b) the
implied-volatility inversion round-trips a price made from a known vol to 1e-6; break = the
price shifted one tick; (c) the OI keying — on a known-answer session the OI used is the row
published on T−1's evening, by `merge_asof` against the builder's key; break = the OI series
shifted one session; (d) sign in money — a synthetic panel in which negative-gamma sessions
continue F5 and positive-gamma sessions revert it must give c < 0, and its negation c > 0; (e)
the day-shift null's zero offset reproduces the observed c; (f) right quantity — F1 and F1b are
different arrays, and R2 differs from R1 and R3. `REQUIRED_OUTPUTS` guard first.

## 4. What is read, and what is not

The ES regular-hours minute bars 2016-01-04 → 2023-12-29; the options fixture's sessions to
2023-12-29 (built over the whole pull to 2026-09-11 and filtered, the last session read
asserted); the option minute bars to 2023-12-29 for F1b. **Not read: any session, option row or
quote from 2024-01-01 on; the `tbbo` year; no cost, no book, no P&L.** R2 is a 30-minute return
of ES signed by nothing — the premise's own outcome; the control is the day-shift null of the
conditioner, which keeps everything about the close except which days the regime label sits on.
**Seen-ness declared:** ES's daily closes 2024-01 → 2026-09 were read by D562; ES five-minute
order flow and returns 2025-09 → 2026-09 by D485; the ES last half-hour 2016–2023 by D463/D466
(K3). The reserved slice for this line is 2024-01-01 → 2026-09-10 at one minute, unread by any
line at that resolution ([[holdout-multiplicity-is-per-line]]).

## 5. What this record does not do

It does not source intraday options quotes (the deposit's F1b proper); it does not run the cost
gate; it does not treat NQ or NDX options (open question 2); it does not fit the dealer
convention, the time-of-day weighting or any parameter — the deposit fixes both from the
literature and this record keeps them fixed; it does not decide the construction. If the
principal declines the 47.7 GB pull, the record stands as a design with its fixture unbuilt, and
the only version runnable on disk is T6 alone (the unsigned 0DTE volume build), which this
record does not promote to a test.

**Runtime.** The pull is the principal's; the statistics decode is the cost and is projected in
§0; the Stage 0 itself is ~2,000 sessions × a few thousand options a day for the gamma sum —
minutes with numpy — and the day-shift null is ~2,000 regressions on a vector, seconds.
