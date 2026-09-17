# D351 — control A must rotate within the floored universe: an erratum study on D347 and D349

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D351-control-A-must-rotate-within-the-floored-universe-an-erratum-study-on-D347-and-D349.md`. The H1 above is the full title.*

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). This record exists
because D350's grid contradicted D347 and a five-second check on the cached grid found why.
Nothing here is a result; the output is the corrected control-A distributions for every
event signal D347 and D349 scored, and whether their verdicts survive.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. What was found, and why it is a defect

D347's control A — "each name's event series rolled by a random offset within its priced
bars" — rotates within `finT`, every bar on which the name has a price. The observed events
are confined to the floored universe (`elig = finT & keep_v2`, after the hedge is defined),
but the rotated events are not: a rotated event can land on a bar where the name's as-traded
close is below $5, or its dollar volume fails the cut, or its dollar-volume estimate does
not yet exist — bars the strategy is forbidden to trade. The kernel then trades them, because
it checks `finT` and not `keep`.

Those bars are the illiquid tail D339 removed from the universe, and on the cached forward
grid their mean hedged forward-40 excess is **+65 bp** against **+1.7** for eligible
name-bars. On the grid, rotating `hist_L`/E1's events within `finT` gives a control-A
median of **+73** with 13% of rotated events landing off the floor; rotating within `elig`
gives **+25**. D347's kernel control A for `hist_L` was +71. **D347's control A was the null
trading the sub-$5 tail.** D349's control A used the same `rotate_confined` and carries the
same defect in the short direction (shorting the tail loses it). D348 is unaffected: its
rotation was on a score already masked to the floor, which is why it found no "cohort drift"
in the slot books.

D350's grid, which rotated within `elig`, found 43 of 138 members above their own names at
random eligible times, `hist_L`/E1 among them at +68 against +25. That is the contradiction
that led here.

## 1. The corrected control

**Control A′:** each name's event series rolled by a random offset **within the bars on
which the name is eligible** (`elig`: priced, `keep_v2`, after the hedge is defined). The
score the kernel reads for ordering is rolled with it. Every rotated event is therefore a
bar the strategy could have traded. Same counts per name; different eligible dates.
Everything else — the kernel, the cap exit, the hedge, the seeds' structure — is D347's and
D349's, unchanged.

## 2. What is re-run

| study | signals | side | draws |
|---|---|---|---|
| D347 | `hist_L`, `rev_21`, `rsi` turn, `rsi` decile (bottom-decile / cross-up events) | long | 100 A′ each |
| D349 | `on_share`, `skew_63`, `close_in_range`, `rsi` decile, `rsi` turn (top-decile / cross-down events) | short | 100 A′ each |

Beside each: the recorded `finT` control A from the study's own data file, the **share of
its rotated events that landed off the floor**, and the mean forward hedged excess of the
name-bars they landed on. Controls B and C are unchanged by this and are not re-run;
the "above A / B / C" verdict is re-stated with A′.

D350's stage 2 runs both domains from its own runner (`--domain finT|elig`) and is reported
in D350's result, not here.

## 3. Predictions

Q1 is load-bearing. Q6 is against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* under A′, `hist_L` and `rev_21` long events are **above A′'s p95** on mean hedged excess, cap exit — D347's Q1 verdict inverts. |
| **Q2** | the recorded `finT` control A is reproduced bit-identically from D347's and D349's seeds by the same code path; for every signal more than **8%** of its `finT`-rotated events landed off the floor, and the mean forward excess of those landings exceeds **+40 bp**. |
| **Q3** | A′ for `hist_L` is centred within **±10 bp** of the grid's +25: the cohort premium of the names is a quarter of what D347 reported. |
| **Q4** | under A′ the short signals' timing values (`observed − A′ p50`) **shrink by more than half** for every one of the five, and at least two of five fall **inside** A′'s p95. |
| **Q5** | D349's verdict stands: no short signal has a positive mean, and none beats control C. |
| **Q6** | *(against)* A′ for at least one long signal is still centred above **+40 bp**: the cohort premium survives the correction at D347's scale. |
| **Q7** | the two `rsi` references remain **inside** A′'s p95 (D347's Q2 pattern: their edge is the cohort, not the timing). |
| *check* | A′ keeps every name's event count exactly (no confinement loss: every eligible bar is after the hedge is defined by construction); no rotated event lands off the floor; no NaN P&L. |

## 4. Stop conditions

- **Q1 holds → D347's verdict is withdrawn in writing**: "no long signal beats its own names at
  random times" was an artefact of the control trading the excluded tail. FINDINGS §28 and
  STACK item 18 are amended; D348 §2's mechanism ("cohort drift is a property of the
  decile-entry event") is corrected to "cohort drift at D347's scale was the null trading
  the tail"; the memory rule is rewritten. The pair book's long side reopens on D350's
  survivors.
- **Q1 fails → D347's verdict stands with corrected numbers**, and the cohort premium is
  real at whatever scale A′ shows.
- **Q4 holds → D349's "timing +26 to +67" is withdrawn** and replaced by A′'s numbers; its
  verdict (Q5) is expected to stand either way.
- Nothing is promoted. Book: empty.

## 5. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[R47]** / **[R49]** | D347's and D349's stored control-A arrays are reproduced to 0.0 by re-running their `stage_controls` code path with their seeds (part 0, first 5 draws) — the defect is in the code that ran, not in a re-implementation |
| **[OFF]** | for each signal, the off-floor landing share under the `finT` rotation is computed two ways (dense mask; sparse gather) and agrees; the mean forward excess of those landings equals a direct recomputation |
| **[A′]** | every A′ draw keeps every name's event count exactly; every rotated event satisfies `elig`; no NaN P&L |
| **[S]** | sign in money on an A′ ledger, long and short |
| **[6]** | [A′] raises on a draw rotated within `finT` (some landing fails `elig`) |

## 6. Files

`docs/decisions/D351-control-A-must-rotate-within-the-floored-universe-an-erratum.md`
(this record) · `scripts/run_d351_control_a_on_the_floor.py` (stages: `--selftest`,
`--rerun STUDY:SIGNAL --draws N`, `--report`) · `data/d351_aprime_*.json`,
`data/d351_control_a_on_the_floor.json` (to follow). Reuses `scripts/d348_prep.py`,
`scripts/d345_event_book.py`, `scripts/run_d347_long_signal_controls.py`,
`scripts/run_d349_short_signal_controls.py`. The five-second check that found it:
`temp/d350_rotation_domain_check.py` (temp; its numbers are re-derived by the runner).
