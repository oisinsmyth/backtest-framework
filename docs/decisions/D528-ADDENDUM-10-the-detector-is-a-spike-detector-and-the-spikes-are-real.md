# D528 ADDENDUM 10 — the detector is a spike detector, the spikes are real, and the sign is inverted

Date: 2026-09-14. Runners: `working/d528_detector_diagnosis.py`,
`working/d528_spike_reality_check.py`.

**Nothing admitted (R15).** Micro universe, in sample only. **No holdout spent** — the reality
check reads `fut_day5m` (5-minute TRADE OHLC), a different fixture from the 1-minute quoted mid the
detector runs on, over the same sessions. The reserved slice (2026-04-11 → 2026-09-09) remains
UNREAD.

**The principal, reading the ten decile charts:** *"on every trade bar the top one, the price has
consolidated, triggered the detector, and then had a move that seems a bit sudden."* That
observation is confirmed exactly. Its causal reading is inverted.

---

## 1. The observation, quantified — the detector is a consolidation-then-spike detector

| | share of entries |
|---|---:|
| **one bar** built >50% of the excursion | **82.3%** |
| one bar built >80% | 44.6% |
| entry bar >3× the window's median bar | 41.0% |
| window quieter than its own 60-bar baseline | 63.3% |

Median `frac_last` is **0.760** — the typical entry has three-quarters of its excursion built by a
single bar. The mechanism is that σ is estimated **on the trailing window, which is the
consolidation**: price goes quiet, σ collapses, the `|y| ≥ 2σ` bar becomes trivially low in
absolute terms, and the first real move clears it.

## 2. But the spikes are the GOOD trades — the sign is inverted

Pool split into quartiles of each causal feature:

| feature | Q1 | Q2 | Q3 | Q4 | direction |
|---|---:|---:|---:|---:|---|
| `frac_last` (suddenness), gross $ | −1.42 | −6.19 | +0.29 | **+2.45** | more sudden is BETTER |
| `jump` (outsized bar), gross $ | −3.65 | −2.93 | +0.91 | +0.81 | bigger jump is BETTER |
| `vol_ratio`, P(target) | 13.4% | 12.8% | 10.1% | 8.3% | quieter is BETTER |

Mechanically this reads as a liquidity event: a lone spike out of a quiet book reverts, whereas a
**gradual** multi-bar move is genuine directional flow and continues.

### 2.1 So the four obvious repairs all fail, and one fails significantly

Against the ADDENDUM 9 control (real data, random count-matched selection):

| repair | n | gross $ | matched p5 / p95 | verdict |
|---|---:|---:|---|---|
| R1 σ-agreement (the dropped A1-σ test) | 546 | −2.03 | −2.19 / −0.18 | inside |
| R2 not-quiet | 263 | −2.96 | −3.42 / +1.23 | inside |
| **R3 no-jump** | 423 | −2.72 | **−2.60** / +0.21 | **below p5** |
| R4 gradual excursion | 127 | −2.45 | −4.81 / +3.02 | inside |
| R1+R2+R3+R4 | 44 | −3.77 | −7.53 / +6.20 | inside |

**Filtering the jumps out makes it measurably worse.** The instinct to "fix" the detector by
rejecting sudden moves is exactly backwards.

### 2.2 Selecting FOR the spike profile clears p95 at every rung

| filter | n | gross $ | matched p95 | net $ | verdict |
|---|---:|---:|---:|---:|---|
| `frac_last > 0.8` | 320 | +1.40 | +1.03 | −3.32 | above p95 |
| `vol_ratio < 0.913` | 358 | +1.05 | +0.45 | −3.70 | above p95 |
| quiet + sudden | 196 | +2.52 | +1.71 | −2.31 | above p95 |
| **quiet + sudden + jump** | 130 | **+3.66** | +2.65 | **−1.22** | above p95 |

First cell all session to clear its correct control repeatedly. **Still net-negative**, and the
four filters are nested, so they are closer to one look than four — on top of roughly thirty
in-sample looks today.

## 3. The artefact test: the spikes are REAL prices

The winning profile — a single-bar spike in the **quoted mid** out of a quiet period — is also the
signature of a momentary wide or stale quote, where the mid jumps and no tradeable price exists.
D523 has burned this programme on bid-ask effects before, so the cell was verified rather than
believed.

**Test:** for every entry, find the 5-minute TRADE bar containing that minute and ask whether the
entry's mid lies inside its `[low, high]`. A real price prints.

| cell | n | outside the trade range | 5m volume | spread tk |
|---|---:|---:|---:|---:|
| whole pool | 717 | 2.0% | 1,614 | 1.78 |
| `traverse` (causal) | 109 | **0.9%** | 2,608 | 1.71 |
| quiet + sudden + jump | 130 | **3.8%** | 1,608 | **1.95** |
| **GRADUAL (opposite profile)** | 127 | **3.9%** | 1,419 | 1.57 |
| random minutes (base rate) | 3,848 | 2.9% | 1,068 | 1.41 |

**The artefact hypothesis is rejected.** The decisive comparison is not against the base rate but
against the **opposite** profile: if suddenness bought artefacts, the sudden cell would be outside
far more often than the gradual one. It is not — 3.8% against 3.9%. And 3.8% against a 2.9% base
rate on n = 130 is **0.6 SE**. Volume corroborates: spike bars carry 1,608 contracts against 1,068
on random minutes, so these are not thin or stale moments.

### 3.1 But the check found a cost understatement in exactly this cell

Spike entries sit in hours whose volume-weighted spread is **1.95 ticks against 1.41 on random
minutes — about 38% wider.** The cost model charges each root a single full-year effective
crossing, so **it understates the cost for this cell specifically.** Correcting roughly for the
crossing portion moves the best spike cell from −$1.22 toward **≈ −$1.85** per trade.

**The artefact hypothesis was rejected and the cell got slightly worse.**

## 4. Disposition

1. **The detector's diagnosis is settled:** it is a consolidation-then-spike detector (82.3% of
   entries built by one bar), and that is not a defect to repair — the spikes are its best trades
   and its real prices.
2. **The classifier is pointed the wrong way for the third time.** `cross2` selected continuation
   (ADD 2), `traverse`'s premise was inverted (ADD 8, lift −0.0345 at t −25), and now the four
   natural repairs are all wrong-signed, one below p5. The consistent pattern is that **every
   filter built on "ranging looks orderly" intuition has been backwards**, while the
   microstructure reading (a lone spike from a quiet book reverts) is the one that holds.
3. **The spike direction is genuine and still does not pay.** Best cell −$1.22 modelled, ≈−$1.85
   once its own wider spread is charged, on n = 130, selected across ~30 in-sample looks.
4. **No component line, no promotion, no holdout spent.** The axis remains the principal's to
   close.

**The one thing worth carrying forward:** if this line is ever revisited, the entry should be built
on the spike profile — quiet window, single-bar excursion, outsized triggering bar — and **not** on
range-traversal, which has now been measured as anti-predictive. And the cost for such entries must
be charged at the spread prevailing in that hour, not at the root's annual average.
