# D362 — the sink filter on the gated gap-up fade: five losing conditions found in the trade export, as a filter and as a sizer, re-simulated with their own nulls

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). Nothing here is a
result. **No holdout data is read.** The five conditions and their thresholds were found
on this fixture's own trades (the D361 export), so this record is a within-sample
confirmation with nulls and a cross-era check, not an out-of-sample test; it says so in
every number. The signal criterion is R15's: gross mean per trade above the controls.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

D361's G2 × T2 cell — a gap in the top 2% of the day on top-decile relative volume, in a
name eligible after the gap, shorted at the next open and held ten bars while the floored
market is below its 200-day mean — is +42.3 gross a trade on 3,977 trades, above the gate
rotation, its own names in the regime, the same-day name and random direction. The
principal asked for every trade in hand, and a screen of about forty entry-time features on
those trades found five whose losing edge quintile is monotone across the profile and below
the signal's mean in both era halves. Removing any of the five in a row-drop raises the mean
to +87 on 1,654 trades; the first two alone give +77 on 2,641; halving size per hit gives +68
per unit of capital at t 3.9. Thresholds fit on one era and applied to the other hold
(+92 against +55 in era 2; +121 against +19 in era 1). This record makes those numbers
honest: the filter is applied to the **signal** and re-simulated (dropping a trade changes
which later events the kernel can take), the thresholds are fixed before the run, and the
filter gets a null of its own.

**Multiplicity, stated.** The five features were chosen from about forty on this sample.
Three arms here. The record's own controls cannot remove the selection; the cross-era check
is the only out-of-bin evidence and it is reported, not counted.

## 1. The construction

**Base:** D361's G2 × T2 exactly, cap 10, reproduced to 1e-9 before anything else.

**The five sinks**, each a condition on a feature known at the entry bar (t−1 information,
as the D361 export defines them; a NaN never hits):

| | feature | hits when | threshold (fit on era 1 of the D361 export, fixed here) |
|---|---|---|--:|
| S1 | `pcto_mass_imbalance` (share of the name's traded volume above the price, less below, over the total) | ≥ θ1 | 86.84 |
| S2 | `mkt_vol_20` (the floored market's trailing 20-bar volatility, bp) | ≤ θ2 | 99.03 |
| S3 | `pcto_beta_63` | ≥ θ3 | 87.22 |
| S4 | `pcto_mass_here` (how much of the name's volume history sits at the current price) | ≤ θ4 | 18.77 |
| S5 | `pcto_gk_minus_cc` (intraday-range volatility less close-to-close volatility) | ≤ θ5 | 6.38 |

**Three arms**, each re-simulated through the kernel on the gated signal:

- **A2** *(primary)*: the signal with events hitting S1 or S2 removed.
- **A5**: the signal with events hitting any of the five removed.
- **W**: the unfiltered signal, each position sized `0.5^hits`; the deployed base is the
  hedged return per bar **weighted** over open positions (Σ wᵢ (vᵢ − m) / Σ wᵢ), and the
  per-trade statistic is the return per unit of capital Σ w·pnl / Σ w, with the capital
  used stated.

Beside each: the **row-drop** version (the same filter applied to D361's ledger without
re-simulation), so the concurrency effect is measured and not guessed.

## 2. Nulls, on the primary arm

- **Filter rotation** *(load-bearing for the filter)*: two constructions. **DROP** — the same
  number of events removed at random, 200 draws (matched count). **FROT** — each name's
  sink-hit flags rotated in time across its own gated events, 200 draws (matched per-name
  count; keeps the name's share of hits). Statistic: gross mean per trade of the
  re-simulated filtered ledger.
- **Gate rotation**, 200, and **A′ within the gate**, 100, exactly as D361, on the filtered
  signal: the filtered cell must still clear its parents' nulls.
- **C**, 1,000, on the filtered ledger.

Seeds `[SEED, 362, arm_index, null_index, part]`.

## 3. Cost, beside and deciding nothing

`2c` at the held names' median half-spread on each arm's own ledger, PUB and PB; GC/HTB
borrow; net after both; breakeven half-spread; the deployed base with the 4- and 2-crossing
lines; exposure. Four groups on A2 with the top trade named, the symmetric 1% trim, names
to half the P&L; by-year and by-era splits; each sink's own hit count and hit mean on the
re-simulated base.

## 4. Predictions

Q1 is load-bearing. Q5 is against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* A2's re-simulated gross mean per trade **exceeds the unfiltered +42.3 and is above the p95 of DROP and of FROT.** |
| **Q2** | A2 is above the p95 of the gate rotation and of A′ within the gate. |
| **Q3** | A5's gross mean exceeds A2's. |
| **Q4** | A5 keeps fewer than half the unfiltered trades; A2 keeps more than half. |
| **Q5** | *(against)* A2 nets > 0 per trade after the PUB `2c` and borrow. |
| **Q6** | W's t-statistic on return per unit capital exceeds A2's t on its mean. |
| **Q7** | A2's symmetric 1% trimmed mean exceeds the unfiltered trimmed mean (+35). |
| **Q8** | A2's era-2 mean exceeds the unfiltered era-2 mean (+55) — era 2 did not set the thresholds. |
| **Q9** | A2's exposure is below the unfiltered 28% of defined bars. |
| **Q10** | the re-simulated A2 mean is within 10 bp of the row-drop A2 mean: concurrency does not carry the effect. |
| *check* | the unfiltered ledger reproduces D361 (3,977, +42.3296); the row-drop A5 with these thresholds reproduces the export analysis on era 2 (1,221 trades, +91.5) to 1e-9; the five features at the entry bar equal the export's columns. |

## 5. Stop conditions

These state the construction's status; **the avenue is the principal's (R15).**

- **Q1 holds** → the filter is real within this sample beyond a random or name-matched
  removal of the same size; it is the version of the fade the principal can choose to
  carry forward (cost engineering, confluences), knowing its selection history.
- **Q1 fails on DROP or FROT** → the five sinks are a description of this sample's losers
  and no more; the unfiltered fade stands as D361 left it.
- **Q2 fails** → the filter improved the mean by removing what the regime and the trigger
  already explained; stated.
- Nothing is promoted. Book: empty.

## 6. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[ID]** | the unfiltered gated ledger == D361's G2 × T2 (3,977, +42.3296) to 1e-9 |
| **[FEAT]** | the five features at (entry bar, name) equal the D361 export's columns on 300 sampled events exactly; NaN patterns equal |
| **[HIT]** · **[RD]** | hit counts per sink under the fixed thresholds equal a direct recomputation; the row-drop arms equal the export analysis's cross-era numbers to 1e-9 |
| **[W]** | the weighted deployed series with all weights 1 equals the unweighted to 1e-12; Σ w·pnl / Σ w equals a direct recomputation; capital used == Σ w / n |
| **[DROP]** · **[FROT]** | every draw removes exactly the observed count (DROP) / keeps every name's hit count (FROT); the removed set is never the observed one |
| **[ROT]** · **[A′]** · **[C]** | as D361: on-share and circular run multiset kept; every rotated event eligible and gate-on; C at 3 SE with the observed outside the band |
| **[S]** · **[HX]** | 300 A′ short trades == the open-fill recomputation to 0.0; +50 bp on one held short moves that trade by −50.000 and no other; the hedged deployed series == the ledger per bar to 1e-12 on every arm |
| **[6]** | [ID] raises on a perturbed ledger; [FEAT] on a perturbed feature; [DROP] on a wrong count; [W] on a perturbed weight; [S] on a sign-flipped ledger |

## 7. Files

`docs/decisions/D362-the-sink-filter-on-the-gated-gap-up-fade.md` (this record) ·
`scripts/run_d362_sink_filter.py` (stages `--selftest`, `--arm A2|A5|W --draws N --draws-rot R
--part p`, `--report`) · `data/d362_ctrl_*.json`, `data/d362_sink_filter.json` (to follow).
Reuses `scripts/run_d361_regime_gated_short.py`, `scripts/d361_export_trades.py` (the feature
definitions), `scripts/run_d360_news_gap_short.py`, `scripts/run_d359_loser_rally_short.py`,
`scripts/run_d358_flat_sleeve.py`, `scripts/d345_event_book.py`, `scripts/d348_prep.py`,
`scripts/d322_four_group_report.py`. The holdout fixture is not read.
