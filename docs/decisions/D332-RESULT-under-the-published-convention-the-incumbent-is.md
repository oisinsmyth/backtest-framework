# D332 RESULT — under the estimator's published convention the incumbent is negative, concentration survives, and the leg-wise book still leads

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D332-RESULT-under-the-published-convention-the-incumbent-is-negative.md`. The H1 above is the full title.*

**Status:** RESULT. Pre-registered at `1d0b299`, runner at `b416d6d` — both
before this file existed (R8).
**Date:** 2026-09-05
**Area:** Strategy research · **personal track** · cost model

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted. Which convention is TRUE is not decided here.**

---

## 1. The one-array swap, and what it did to the stack

`PB` is the cost model every runner since D318 has used: the median across a
leg's entries of the single two-day Corwin–Schultz estimate, which is clamped
to zero on 43.2% of all live name-bars. `PUB` is the estimator as its authors
specify it — the trailing 21-bar mean of the clamped daily estimates, lagged
one bar — which this codebase already computed as the axis-E score
`cs_spread`. Nothing else changed: **`[S]` proves every ledger is bit-identical
under both, and `[1]` reproduces D329's four arms and D323's thirteen k=20
cells to 0.0e+00 under PB.**

**Part A — the levels.** Across the 92 costable legs, PUB charges **2.03×** PB
at the median (p10 1.40×, p90 3.31×). The spread is not uniform: legs that
select quiet names are charged the most relative to PB, because PB's median was
sitting on the zero clamp. The six legs PB charged **exactly zero** — the
vol-family long legs and `cs_spread`'s — are **2.5–4.3 bp** under PUB: costable,
and still the cheapest legs on the tape, because they are pinned deal stocks
(D330) whose real cost is borrow, not spread.

**Part B — the stack.**

| cell | PB net bp/bar | **PUB net bp/bar** | PB Sharpe | **PUB Sharpe** | held ½-spread PB → PUB |
|---|--:|--:|--:|--:|--:|
| **incumbent N=2 / target, k=5** | +14.57 | **−5.16** | +0.334 | **−0.118** | 18.3 → 38.8 |
| incumbent N=19 / target | −15.02 | −37.09 | −1.000 | −2.469 | 25.0 → 47.1 |
| incumbent N=2 + dv28 | +18.37 | −1.61 | +0.507 | −0.044 | 14.5 → 35.4 |
| `retrace_leg` k=20 | +20.91 | **+16.06** | +0.625 | **+0.480** | 19.8 → 32.1 |
| `dist_lvn` k=20 | +14.96 | +5.47 | +0.379 | +0.138 | 5.2 → 27.0 |
| `skew_63` k=20 | +12.60 | +4.97 | +0.421 | +0.166 | 8.4 → 26.8 |
| leg-wise LW k=20 | +17.49 | +5.58 | | | |
| leg-wise LW_f k=20 | +9.98 | −3.96 | | | |

*The harness's PB cell for the incumbent reproduces D321's base exactly
(+14.57, +0.334, 18.31) and its dv28 cell exactly (+18.37, +0.507) — so the
"rebuilt, not D321's" disclaimer in the pre-registration was unnecessary. It
differs from D318's +11.36 by the D318→D321 costing change STACK already
records (turnover by names held, per-name commission). The runner's `[H]` line
printed NaN because D318's field is `net`, not `net_bp`; informational only.*

## 2. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | the incumbent nets ≤ 0 bp/bar at N=2 under PUB *(load-bearing, against the stack)* | **CONFIRMED** — +14.57 → **−5.16**, Sharpe +0.334 → −0.118 |
| **Q2** | concentration survives: N2 − N19 within 5 bp/bar of its PB value | **CONFIRMED** — +29.59 → +31.93. Axis B's "basis-immune" holds for this basis too |
| **Q3** | the leg-wise book still beats both parents per trade under PUB | **CONFIRMED** — LW +35.99 against H −59.39 and S +8.14 |
| **Q4** | dv28's advantage widens under PUB *(directional)* | **FALSIFIED**, narrowly — +3.80 → +3.55. A trailing-mean spread is less sensitive to the per-name selection dv28 makes than a per-bar median was |
| **Q5** | D323's top-2 at k=20 changes under PUB *(against the shortlist)* | **FALSIFIED** — `retrace_leg` and `dist_lvn` lead under both. The ordering below them reshuffles: `price_log` +11.1 → +0.6, `rsi` +0.1 → −6.6 |
| **Q6** | the three degenerate cells are costable and none is top-10 | **FALSIFIED** — costable, yes; `on_share`'s short leg ranks **8th of 46** as a partner for `hist_L`-long (+7.9/trade). `dist_52w_high` 12th, `cs_spread` 20th |
| **Q7** | the half-tick floor moves no PUB cell by more than 1 bp per trade | **CONFIRMED** — under the published convention the floor is a formality |

Four of seven, and the four include both load-bearing ones and the two that
were against the stack.

## 3. What this establishes

1. **The stack's headline number was a cost-convention artefact.** Under the
   convention the estimator's authors specify, the incumbent book — the thing
   STACK §0 reported at +11.36 / +14.57 bp/bar — nets **−5.16**, and its short
   leg alone loses **−180.8 bp per trade**. Per the pre-registered stop
   condition, STACK §0 is rewritten under PUB with PB beside it.
2. **The programme's relative findings survive the swap.** Concentration
   (+32 bp N2−N19), the leg-wise construction beating its parents, and the
   D323 leaders (`retrace_leg`, `dist_lvn`) are unchanged in order. What the
   swap moves is the *level*: every net number falls by 8–20 bp/bar.
3. **`retrace_leg` at k=20 is now the best symmetric book in the programme
   under either convention** — +16.06 bp/bar, Sharpe +0.480 under PUB — and
   the only cell above +10 that remains above +10.
4. **PUB does not fix the pinned-name problem and was never going to.** The
   vol-family long legs are charged 4 bp under PUB because their names really
   do have tiny ranges. The estimator is right about the *spread* of a deal
   stock; the cost it misses is borrow (D330, FINDINGS §16).
5. **The floor was the wrong study and this record says so.** STACK §6 listed
   it; the stage-0 measurement replaced it with the convention question in the
   time it took to run.

## 4. What is NOT established, and the default

**Which convention is true.** PB and PUB are two summaries of the same noisy
estimator, and the fixture has no quoted spreads to test either against. The
pre-registration set the default: **PUB, because it is the one the estimator's
authors specify, and PB is the one the programme adopted without a record.**
That default holds until Part C — quoted BID_ASK bars from the principal's IBKR
session on a stratified sample of live names, PB vs PUB vs Abdi–Ranaldo,
selection by lowest median absolute log error, declared in advance — decides
it. **Every net number in the programme should now be read as a PB / PUB
pair until then.**

## 5. Assertions

All eight pass, all properties of the code or of the estimator's definition.

| | |
|---|---|
| **[U]** | universe median half-spread PB 14.2, PUB 31.7 — the stage-0 numbers |
| **[Z]** | PB 43.2% exactly zero; PUB 0.31% |
| **[C]** | PUB at bar t is `cs_spread` at t−1; causality inherited from axis E's truncation audit |
| **[F]** | the floor is ≥ half a tick over price wherever a close exists, untouched above it, untouched where no close exists, and changes no cell's finiteness. *The first form used `np.maximum`, which propagates NaN, and fired where the close is missing — a defect in the floor, caught by its own assertion* |
| **[1]** | D329's four arms and D323's thirteen k=20 cells reproduce to **0.0e+00** under PB |
| **[S]** | every arm's ledger is bit-identical under PUB — cost never touches selection |
| **[6]** | raises on a cell handed a free spread |

**Speed:** 136 s; 8.3 GB peak on the 46 rank arrays. No parallelism.

## 6. Files

`data/d332_spread_convention.json` · `scripts/run_d332_spread_convention.py` ·
`scripts/d332_cs_zero_rate.py` and `data/d332_cs_zero_rate.txt` (stage-0)
