# D350 RESULT — three long triggers beat every honest control, the reversal family has timing, and none pays the published spread

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D350-RESULT-three-long-triggers-beat-every-honest-control-and-none-pays-the-published-spread.md`. The H1 above is the full title.*

**Status:** RESULT. Pre-registered at `0f768d3`, runner at `86047b0` with the kernel stage
extended to both rotation domains at `1fe5101` (declared in D351's pre-registration
`c291a7a`) — all before this file existed (R8). `keep_v2`, F0, next-open fill, hedged
against the floored market, D345's kernel, cap exit primary; PUB primary, PB beside.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is a book. Nothing is promoted. Three candidate long triggers are named, with multiplicity 138.**

---

## 1. The verdict

**One of eight as pre-registered, and every failure is the one D351 predicts.** The
pre-registration's kernel control A was D347's, which D351 showed rotates events onto the
excluded tail; under it no survivor passes, so Q1 fails on its letter. Under the same
rotation confined to the floored universe — A′, the control the grid used from the start —
**three of the five gate survivors are above A′, B and C**, and the screen's other
predictions failed in the direction of *more* timing than false discovery would give, which
is what a screen run against a sound control on a family with real timing looks like.

| kernel, long, cap exit, bp/trade | n | mean | median | t | **A′** p50 / p95 | B p50 / p95 | C p95 | above A′ / B / C | A (finT) p50 |
|---|--:|--:|--:|--:|--:|--:|--:|---|--:|
| **`rev_5`/E1** | 27,316 | **+43.4** | +41.8 | 4.8 | +19.0 / +30.1 | +26.6 / +36.8 | +14.0 | **yes / yes / yes** | +62.3 |
| **`gap_reversal`/E1** | 18,714 | **+47.1** | +27.0 | 4.0 | +27.3 / +41.5 | +21.1 / +33.9 | +19.9 | **yes / yes / yes** | +73.9 |
| **`cs_spread`/E2** | 7,812 | **+71.6** | +31.1 | 3.4 | +12.4 / +46.1 | +15.6 / +33.1 | +33.4 | **yes / yes / yes** | +87.1 |
| `rev_5`/E3 | 27,291 | +34.7 | +38.6 | 3.8 | +20.7 / +29.3 | +25.6 / +35.2 | +15.2 | yes / no / yes | +60.5 |
| `gap_reversal`/E3 | 19,029 | +29.9 | +16.5 | 2.5 | +24.4 / +37.7 | +19.5 / +31.4 | +20.1 | no / no / yes | +72.9 |

100 draws for A and A′ and B, 1,000 for C. Every survivor's grid mean (+46 to +99) is above
its kernel mean (+30 to +72): the kernel drops the events that fire while the name is
already held — 54 to 62% of them for these members — and those clustered repeats are the
better ones. That is the overlap the pre-registration named as the first suspect, and it
did not decide anything: the ranking under the kernel is the ranking on the grid.

## 2. Stage 1 — the grid, 138 members

43 of 138 members are above their own names at random eligible times at p ≤ 0.05, against
7 to 9 that false discovery alone gives (`M_eff` Li–Ji 108, Cheverud–Nyholt 136); BH at q =
0.10 rejects 34; the family-wise grid-max p of the best member is 0.000 (its z of 6.5
against a shared-offset max-z whose p95 is 3.3). **Every E1 member on a reversal-type
score has positive timing** — `hist_L` +46, `md` +56, `rsi` +23, `rev_5` +42, `rev_21` +38,
`mom_252_21` +39, `dist_52w_high` +123 — so Q3, written on D347's artefact, is falsified
the way D351 says. D347's three members rank 6th, 18th and 28th. The oracle cleared at
p = 0.001 and the noise series did not; the hurdle has teeth.

## 3. The four groups, per trade, on the three that pass

| | `rev_5`/E1 | `gap_reversal`/E1 | `cs_spread`/E2 |
|---|--:|--:|--:|
| trades / names | 27,316 / 1,130 | 18,714 / 1,106 | 7,812 / 869 |
| mean / median / win / payoff | +43.4 / +41.8 / 51.5% / 1.02 | +47.1 / +27.0 / 51.0% / 1.05 | +71.6 / +31.1 / 51.0% / 1.07 |
| skew / kurtosis | +0.4 / 8 | +1.0 / 21 | +0.4 / 4 |
| ex-top 1% / ex-bottom 1% / **trimmed** | −18.1 / +96.9 / **+35.3** | −18.4 / +103.7 / **+38.1** | +1.7 / +130.9 / **+60.9** |
| names to half the P&L; top-1/5/10 share | 27; 3 / 12 / 23% | 20; 6 / 18 / 30% | 12; 6 / 28 / 45% |
| profitable years (of 14) | 71% | 64% | 50% |
| era 1 / era 2 | +0 / +65 | +22 / +56 | −8 / +108 |
| down-years | +58 | +27 | −22 |
| dead / alive | +5 / +51 | +51 / +47 | +39 / +80 |
| below / above the median price | +70 / +17 | **+95 / −1** | +103 / +41 |
| top trade | AAOI 2026-02-19 at $46.98, DV pct 66, +15,701 bp, 1.3% | **GME 2021-01-19 at $39.36**, DV pct 89, +37,501 bp, 4.3% | GME 2024-04-19 at $10.42, DV pct 49, +18,230 bp, 3.3% |
| net per trade, cap: PUB / PB | **−18.6 / +17.9** | −21.7 / +17.2 | −34.7 / +27.9 |
| net per trade, invalidation: PUB / PB | −43.3 / −3.7 | −71.6 / −21.6 | −32.9 / +30.2 |

**`rev_5`/E1 is the cleanest signal this programme has scored on the event lens**: a
one-week reversal entering the bottom decile, mean equal to median, t = 4.8 on 27,316
trades, 27 names to half the P&L, profitable in ten of fourteen years, positive in the
down-years, and its top trade 1.3% of the total. Its mirror loses. `gap_reversal`/E1 is a
two-sided fat-tailed book whose symmetric trim is +38 but whose top trade, and the top trade
of two other survivors, is GME in January 2021; **it earns +95 below the median price and
−1 above it**, and dropping its top 1% turns it negative. `cs_spread`/E2 — a name entering
the top decile of *spread* — is the floor's own illiquid edge, with half its P&L in twelve
names and a first era of −8; it is what D339's tail looks like from inside the floor.

**None nets positive after the published spread.** The cap-exit round trip is 62 to 106 bp
PUB; the three net −19, −22 and −35. Under PB they net +18, +17 and +28. The invalidation
exit is worse for all three (hold 4 to 7 bars, the mean falls faster than the cost).

## 4. The interaction with the `rsi` ranking

Q7 was written against D347's pattern and is falsified, but not reversed to the pair-book
premise either: `rev_5`/E1's interaction is **−65 in the bottom 2%** by `rsi`, −57 to −10
through the middle, and **+66 and +150 in the (75, 95] buckets** — a one-week reversal on a
name that is *not* oversold on the two-week `rsi` is a pullback, and on a name that is
oversold on both it is a falling knife. `gap_reversal`/E1 is flat across the middle. **On
every long signal tested in D347 and here, the bottom of the `rsi` ranking is where the
signal does worst.** A pair book that fires its long trigger on the most-oversold names is
firing it in the wrong place; the trigger's names should be paired with the ranking's
*short* extreme without being selected by the ranking's long extreme.

## 5. Predictions

| | | outcome |
|---|---|---|
| **Q1** | *(load-bearing)* a gate survivor above A, B and C under the kernel | **FALSIFIED** on the pre-registered A (D347's, defective per D351); **three of five above A′, B and C** |
| **Q2** | survivors at p ≤ .05 within false discovery | **FALSIFIED** — 43 vs 7 to 9 |
| **Q3** | no reversal-type E1 has TV > 0 | **FALSIFIED** — all seven do |
| **Q4** | some E3 has TV > 0 at p ≤ .05 | **CONFIRMED** — `gap_reversal`/E3 +61, `rev_5`/E3 +33 |
| **Q5** | grid-max p > 0.05 | **FALSIFIED** — 0.000 |
| **Q6** | BH rejects zero | **FALSIFIED** — 34 |
| **Q7** | *(against)* survivor interaction positive mid, negative bottom | **FALSIFIED** — bottom negative for `rev_5`, mid negative too; the top buckets positive |
| **Q8** | *(against)* a survivor nets > 0 after PUB under invalidation | **FALSIFIED** — −33 to −78 |

One of eight.

## 6. Stop conditions, executed

- **Q1 as pre-registered fails → on the letter, the long-timing search would close on this
  family.** It does not close: the control the letter named was shown defective by D351
  before this stage was read, the corrected control was declared and run beside it, and
  under it three members pass. The record says both and takes the corrected one, with the
  pre-registered one printed beside it in every table.
- **Under A′, Q1 holds → `rev_5`/E1, `gap_reversal`/E1 and `cs_spread`/E2 are candidate long
  triggers**, multiplicity 138 with `M_eff` 108 stated, each carrying its four groups above,
  each netting negative at the published spread. **`rev_5`/E1 leads.** A D347-style full
  record on it, with the invalidation and target exits and the slot-capped variant, is the
  next long-side study; the pair book's pre-registration waits on D336's quoted spreads
  because none of the three pays PUB.
- Nothing is promoted. Book: empty.

## 7. Deviations and what the run found

- **The kernel stage runs both rotation domains.** The pre-registered kernel control was
  D347's `rotate_confined` (within `finT`); D351 found it lands 8–13% of rotated events on
  the excluded tail. The stage was extended, before any kernel result was read, to run A′
  (within `elig`) per draw beside it, and the report evaluates Q1 under both. The grid had
  rotated within `elig` from the pre-registration, so stages 1 and 2 were on different
  domains as written; the extension makes them consistent.
- Control B on `rsi`/E1 and E2 keeps 3.7% of names by the declared fallback — their events
  sit in the smallest `rsi` buckets and the same-day pool is exhausted; [B] asserts every
  replaceable event was replaced. Every other member replaces 99.99–100%.
- `M_eff` by Li–Ji is reported on the verbatim formula (108.0) and on |λ| (108.5); three
  eigenvalues of the pairwise-complete correlation matrix are negative (min −0.79).
- Threads were slower than serial on the screen (GIL-bound rejection sampling); the
  per-score controls run in an 8-process spawn pool, verified against the in-process result
  on a 6-member subset. The screen took 814 s; a kernel stage 4 to 6 min per member.

## 8. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** · **[F]** | via the shared prep; grid == direct recomputation on 3,000 cells to 7.8e-15 |
| **[G]** | `hist_L`/E1, `rev_21`/E1, `rsi`/E1 event and mirror matrices equal D347's exactly (23,491 / 35,108 / 44,661) |
| **[E]** | 2,700 sampled events hold on the raw lagged percentile at t−1 and t−2 and fail unlagged |
| **[SP]** | the sparse control-A gather equals the dense rotation on 20 draws × 5 members and a tie-heavy synthetic grid |
| **[A]** / **[B]** | counts preserved; date and bucket preserved, name changed wherever the pool allows |
| **[O]** | the oracle clears A at p = 0.001; the noise series is below 0.05 on 1 of 20 seeds |
| **[M]** · **[BH]** | symmetric, unit diagonal, 1 ≤ M_eff ≤ 138; four textbook BH vectors recovered |
| **[A′]** | every kernel-stage A′ draw keeps every name's count and lands only on eligible bars |
| **[X]** | on every survivor the buckets partition the trades and Σ n_b (E_sb − E_s) = 0 |
| **[6]** | [O] raises when the oracle is replaced by noise; [SP] raises on a whole-grid roll |

## 9. What this establishes

1. **The reversal family has long timing on the floored universe**: every E1 member on a
   reversal-type score beats its own names at random eligible times, and `rev_5`/E1 beats
   all three controls under the kernel with the cleanest distribution in the programme's
   event record.
2. **Three candidate long triggers exist and none pays the published spread.** The long
   side's problem is cost, as it has been since D285, not signal.
3. **The screen's multiplicity instruments agree with the kernel**: BH, `M_eff` and the
   grid-max all say the family carries far more timing than false discovery, and the
   kernel confirms the top of the ranking.
4. **The bottom of the `rsi` ranking is where every long signal does worst**, on the
   fourth table to show it; the pair book must not select its long trigger there.
5. **A pre-registered control can be wrong, and the record has to say so rather than let
   the letter of Q1 close a real signal.** Both controls are printed in every table.

## 10. Files

`data/d350_screen.json` · `data/d350_ctrl_*_p0.json` (five) · `data/d350_long_timing_screen.json` ·
`scripts/run_d350_long_timing_screen.py` · reuses `scripts/d348_prep.py`, `scripts/d345_event_book.py`,
`scripts/run_d347_long_signal_controls.py`, `scripts/d321b_effective_tests.py`
