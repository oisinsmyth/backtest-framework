# D506 RESULT — stage 1, CLOSE: in-play selection buys 0.85 points of fee dilution and costs 2.09 points of directional accuracy. It fails as alpha and works as drawdown management

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D506-RESULT-stage-1-CLOSE-in-play-selection-costs-more-accuracy-than-the-fee-it-saves-but-it-cuts-the-breach-rate-3-to-5-fold.md`. The H1 above is the full title.*

**Result of D506** (spec `2bea9d9`). Runner `scripts/run_d506_inplay_accuracy.py --run`
(`--selftest` passes, eight checks; 0.4 min), artefact `data/d506_inplay_accuracy.json`, cell table
`data/d506_cells.csv.gz`. Eight roots, ~1,700 usable sessions each, **2016-01-04 → 2023-12-29;
2024+ not read.** Primary declared in advance: `Δ = T(in play) − T(the rest)` for S2 (the log MACD)
on YM, with `T = (2p − 1) − fee/E|M|`.

## 0. The answer

**The fee lever is exactly as large as the premise said, and it is swallowed by an accuracy loss the
design did not anticipate.** Across all 16 cells (8 roots × 2 signals):

| | mean | median | sign |
|---|---:|---:|---|
| the fee term, `fee/E|M|(rest) − fee/E|M|(in play)` | **+0.85 points** | +0.85 | **positive in 16 of 16** |
| the accuracy term, `p(in play) − p(rest)` | **−2.09 points** | −1.32 | negative in **11 of 16** |
| **Δ, the primary statistic** | **−0.0334** | −0.0149 | negative in 9 of 16 |

**Directional accuracy falls by about two percentage points on the sessions the filter selects, and
that is more than twice the fee it saves.** The premise's arithmetic was right and its assumption
was wrong.

**The primary cell, YM-S2:**

| | in play | the rest | all |
|---|---:|---:|---:|
| sessions | 173 | 1,488 | 1,661 |
| accuracy `p` | **47.98%** | 51.05% | 50.73% |
| E\|M\| | $116 | $81 | $85 |
| fee as a share of E\|M\| | **2.59%** | 3.69% | 3.53% |
| `T` | −0.0664 | −0.0160 | −0.0208 |
| gross / net per trade | **−$10.61 / −$13.61** | +$2.10 / −$0.90 | +$0.78 / −$2.22 |
| median, 1% symmetric trim | −$5.00, −$11.45 | +$1.00, +$1.32 | +$1.00, +$0.08 |
| hit, skew, kurtosis | 48.0%, +0.20, +2.07 | 50.8%, +0.37, +5.26 | 50.5%, +0.31, +4.73 |
| σ, net Sharpe on traded sessions | $163, **−1.32** | $119, −0.12 | $124, −0.28 |
| worst day (share of the 4% budget) | −$524 (26%) | −$680 (34%) | −$680 (34%) |
| P3a | 0.00 a year | 0.00 | 0.00 |

**Δ = −0.0504.** Its own exact rotation has p50 −0.0025 and p95 +0.1351, and **73.4% of the 2,035
offsets exceed the observed value.** The N2 family bar over 16 cells and 1,978 common offsets is
p50 **+0.1415**, p95 **+0.2192**, p99 +0.2496, against an observed family maximum of **+0.0620**
(ZN-S1) — **97.8% of offsets beat the best real cell.** Verdict by the pre-registered rule:
**CLOSE.**

## 1. Three disclosures, before the reading

**(a) The primary statistic overstates every edge, by 2× to 13×, and the pre-registration said it
might.** `(2p − 1)·E|M|` is the edge only when winners and losers are the same size, and on these
roots they are not:

| cell | `p` | `(2p−1)·E|M|` | actual gross | ratio | skew |
|---|---:|---:|---:|---:|---:|
| YM-S1 | 54.38% | +$7.46 | **+$0.56** | 13.4× | −0.38 |
| ZB-S1 | 51.82% | +$18.25 | +$4.26 | 4.3× | −0.94 |
| ES-S1 | 55.66% | +$12.46 | +$3.20 | 3.9× | −0.33 |
| NQ-S1 | 55.18% | +$18.90 | +$4.80 | 3.9× | −0.30 |

The long day-session drift wins often and loses big. **The dollar means, not `T`, are the operative
numbers**, and they say the same thing: the in-play cell on the primary is −$10.61 gross a trade
against +$2.10 on the rest.

**(b) The decision rule's control term passed vacuously and must not be read as confirmation.** The
rule required control V to "show the same sign at a comparable size"; V and Δ are both negative on
YM, so the term returned True. It was written expecting a positive Δ. **What V actually shows is
noise:** within the top realised-range decile, the high-score minus low-score difference runs −0.47
to +0.37 across roots at n ≈ 29–46 a side, which is −2.16 to +1.75 standard errors. V neither
confirms nor refutes anything at this sample size, and the record says so rather than claiming a
passed control.

**(c) Prediction X-b mis-sized the family bar by five-fold, for an instructive reason.** I predicted
p95 in [+0.020, +0.045] from the fee term; it came in at +0.2192. The family bar is the **maximum of
16 cells**, and its scale is set by the per-cell sampling noise of `(2p − 1)` on ~170 in-play
sessions — SD ≈ 2 × 0.5/√170 ≈ 0.077 — whose 16-fold maximum has expectation ≈ 0.077 × 1.77 ≈ 0.14.
The null's p50 of +0.1415 matches that to two decimals. **The null was behaving exactly as a
max-of-16 should; my prediction had simply sized it from the wrong quantity.**

## 2. What the result says

**(a) The mechanism runs the wrong way, and it is consistent with the last two records.** A large,
high-volume overnight session is followed by a day session whose direction is *harder*, not easier.
That is the same finding as D504 (the Asian channel clears entirely in the opening gap, +25.65 bp
into the gap against −1.65 into the day) and D499 (the off-hours move partly reverts in the next
hour) seen from a third angle: **by 09:30 the information is spent, and a night that moved a lot has
spent more of it.** The in-play filter selects, precisely, the sessions with the least left to give.

**(b) The fee lever is real, measurable and too small to matter.** It delivered +0.85 points of
`(2p−1)`-equivalent on average, positive on 16 of 16 cells, exactly the +0.4 to +2.0 the premise
predicted. At the Sharpe conversion of `√252/c` with `c ≈ 1.4` that is **+0.10 of Sharpe** — the
number the draft advertised, confirmed, and irrelevant once accuracy moves twice as far the other
way.

**(c) The accuracy bar from FINDINGS §69 is not sufficient, and this record corrects how it was
quoted.** The long drift on the index roots reaches **55.7% (ES), 55.2% (NQ), 54.4% (YM)** — above
the "53.6% for a component Sharpe of 0.5" figure — and its net Sharpe is **+0.02, +0.11, −0.31**.
The 53.6% was derived assuming symmetric payoffs. **Accuracy alone does not determine the Sharpe;
the payoff ratio does, and on these roots it is adverse.** Any future use of §69's accuracy targets
must carry the payoff ratio beside them.

**(d) And the half of the draft that survives is the half about drawdown.** The exposure-day
argument holds on every root where breaches exist at all:

| cell | P3a, all sessions | P3a, in play only |
|---|---:|---:|
| ZB-S1 | **14.00 a year** | **2.71** |
| ZB-S2 | 13.57 | 3.14 |
| ZN-S1 / ZN-S2 | 2.00 / 2.00 | 0.71 / 0.86 |
| NQ-S1 / NQ-S2 | 0.57 / 0.29 | 0.00 / 0.14 |

**Trading a tenth of the sessions cuts the breach rate by three to five times**, even though each
session traded is more dangerous. The filter is a drawdown instrument that happens to be a bad
selector. That is worth keeping separately from the signal question, because R11's P3a bar of 1.0 a
year is what ZN and ZB fail on all sessions and pass on in-play sessions alone.

**(e) The σ-by-year table earns D503's point emphatically.** On one micro, the traded day move's σ:

| root | 2017 | 2020 | 2022 | 2023 |
|---|---:|---:|---:|---:|
| NQ | $60 | $287 | **$452** | $274 |
| ES | $42 | $203 | $264 | $154 |
| ZB | $475 | $920 | $929 | $727 |

**A 4× to 7× swing inside the in-sample window.** Any C-d, P3 or P4 figure quoted as a single
pooled number over 2016–2023 is a price-level artefact, as D503 said. This record therefore reports
σ per year, and does not attempt a 2026 figure: the 2024+ slice is the declared forward slice for
the six unspent roots and was not read.

## 3. Predictions

| | predicted | observed | |
|---|---|---|---|
| X-a | \|Δp\| < 1.5 pts on the primary; Δ in [+0.005, +0.020] | Δp **−3.07 pts**; Δ **−0.0504** | **wrong**, and wrong in the informative direction |
| X-b | family p95 in [+0.020, +0.045]; Δ does not clear it | p95 **+0.2192**; does not clear | verdict right, **size wrong by 5×** (see §1c) |
| X-c | control V near zero, \|diff\| < 0.010 | −0.1320, i.e. −0.65 SE | **wrong as stated**; V is noise at this n, not zero |
| X-d | the untradeable bound U ≥ +0.03 on the primary | **−0.0018** | **wrong** — even perfect foreknowledge of the day's size is worth nothing here |
| X-e | S1 `p` in [50, 53]%, S2 in [50, 52]%, none reaching 53.6% | S1 **55.7 / 55.2 / 54.4**, S2 51.2 / 50.3 / 50.7 | S2 right; **S1 wrong and above 53.6% with a Sharpe of ~0** |
| X-f | P3a higher per traded session, lower per year | confirmed wherever breaches exist (§2d) | right |
| X-g | the verdict is CLOSE | CLOSE | right |

**Four of seven predictions were wrong**, and X-d is the one that matters most: the untradeable
upper bound — conditioning on the day's *realised* range, which no one can do — is −0.0018 on the
primary. **There was no prize to win even with perfect foreknowledge of the day's size**, which
disposes of the whole family rather than only the causal version of it.

## 4. What stands

- **CLOSE recommended for in-play selection as an alpha filter on the prop book**, on eight roots
  and two signals; the principal closes. Stage 2 (root selection) is **not** run: the draft made it
  conditional on stage 1, and stage 1 says the state predicts worse direction, not better.
- **Kept as a measurement** (to FINDINGS): the in-play state raises E|M| and lowers the fee share
  exactly as measured, and lowers directional accuracy by more; the information is spent by the
  open; and selectivity cuts the breach rate three to five times, which is a drawdown instrument
  independent of any signal.
- **A correction to §69's accuracy targets**: they assume symmetric payoffs, and on these roots the
  long drift clears 53.6% accuracy with a Sharpe of ~0. Quote the payoff ratio beside the accuracy.
- **Spent:** nothing. 2024+ was not read on any root.

## 5. Files

Runner · this record · the artefact · the cell table · the ledger row · PICKUP · FINDINGS ·
`working/DRAFT-in-play-on-the-prop-book.md` (the design this tested).
