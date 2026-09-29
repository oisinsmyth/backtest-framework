# D671 STAGE 0 RESULT (development, ES and NQ): the day-size forecast predicts the day's range well, but NQ's breaks pay on the days it calls QUIET, so the construction is worse than the plain break; on ES only the short-side veto helps

*2026-09-29.*
- *One run of `scripts/stage0_d671_break_construction.py` (`f8806731`) under D671 (`38c33823`), in 0.7 min.*
- *In-sample only. The evaluation window is 2018-01-09 → 2025-02-28 (where the size tier exists). It reproduces
  D668's development E4 exactly.*
- *Dealer gamma (GEX): SqueezeMetrics.*
- *Output: `data/stage0_d671_break_construction.json`.*
- *DEVELOPMENT: no verdict.*

## 1. The size forecast: it works, as a forecast of the day's range

| | NQ | ES |
|---|---:|---:|
| out-of-sample Spearman, forecast against ln(range/ATR) | **0.417** | **0.455** |
| persistence only (rv5) | 0.343 | 0.368 |
| rotation null p50 / p95 | −0.00 / 0.05 | −0.00 / 0.07 |
| realised range/ATR, bottom → top decile | 0.69 → 1.38 | 0.64 → 1.44 |
| P(hold) by tier: bottom / middle / top | 0.58 / 0.52 / 0.50 | 0.59 / 0.54 / 0.48 (**leak flag**) |

- The forecast is well calibrated.
- Every slope is positive in 81–100% of refits. The overnight range, rv5 and |gap| carry most of it.
- Expectation 1 held. The Spearman came in above the 0.20–0.35 expected.

## 2. …but the trade pays where it predicts a SMALL day

**E4 by size tier, NQ** (net per trade, 1 micro, 2018 →):

| tier | trades a year | net (t) | P(hold) | $ a year | daily Sharpe |
|---|---:|---|---:|---:|---:|
| **bottom (quiet forecast)** | 44 | **+7.71 (2.29)** | 0.58 | **+946** | **1.11** |
| middle | 54 | +0.72 | 0.52 | +88 | 0.10 |
| top (busy forecast) | 62 | −0.42 | 0.50 | +53 | 0.06 |

On ES all three tiers are negative (−1.82 / −0.60 / −2.24).

**Why the size oracle (D668, `f769c43c`) misled.**
- The oracle graded trades by the day's REALISED range, and a trend day *creates* range. Part of "big realised day"
  was the break succeeding.
- A forecast built from the vol state (the overnight range, rv5, |gap|) calls busy days. On those days:
  - yesterday's level is broken by noise;
  - the 0.25-ATR stop and trail (ATR is a 20-day lag) are small against the day's swings.
- A break on a day forecast to be QUIET is the surprise: it comes from new information, and it runs.

**This is a new, post hoc hypothesis:** *breaks carry when they are unexpected given the vol state.* It was found on
NQ's development sample, and fits D487 (the quiet tercile trends most). It is not a result, and it needs YM/RTY.

## 3. The ablation (same window)

| | NQ net (t), trades/yr, $/yr, Sharpe | ES net (t), trades/yr, $/yr, Sharpe |
|---|---|---|
| B0 the break | +2.18 (1.50), 161, +1,086, 0.69 | −1.58 (−1.42), 159, −428, −0.48 |
| B1 + hard skips | +1.86, 146, +858, 0.58 | **+0.11**, 79, −3, −0.01 |
| B2 + score veto | +1.87, 139, +824, 0.56 | +0.14, 79, +5, 0.01 |
| **B3 + size tier (the construction)** | **−0.61 (−0.34)**, 103, −33, −0.03 | +0.30 (0.19), 55, −26, −0.05 |
| B3w (wider trail on top tier) | −0.28, 103, +145, 0.10 | −0.46, 55, −100, −0.18 |

**What each layer removed** (a layer is worth keeping only if what it removes loses):
- **NQ:**
  - hard skips +5.52 (FOMC/opex days were GOOD on NQ);
  - score veto +1.58;
  - **size tier +8.95 (t 2.28)**.
  - Every NQ layer removed winners.
- **ES:**
  - **hard skips −3.26 (t −2.05): the short-side veto is the one layer that helped.** ES longs-only is about 0 net;
  - score veto −5.79 (3 trades);
  - size tier −0.22.

**The placebo** (random within-year subsets of B0 of B3's count):
- NQ p50 +2.20, p95 +4.10. The construction's −0.61 ranks at **0.003**: it filters worse than random.
- ES p50 −1.58, p95 +0.91. The construction's +0.30 ranks at 0.887, inside the null.

## 4. The score's parts: right on NQ, reversed on ES, cancelling by construction

The net when a term fires, against when it does not (post-skip trades):

| term | NQ | ES |
|---|---|---|
| gap aligned (+) | +3.60 vs −2.48 ✓ | +0.46 vs −1.07 ✓ |
| breadth aligned (+, NQ) | +3.16 vs +1.27 ✓ | — |
| cross-index (+, ES) | — | −0.20 vs +0.39 ✗ |
| overnight probe (−) | −1.18 vs +2.02 ✓ | **+9.87** vs −0.31 ✗ (4% of trades) |
| exhausted gap (−) | −2.68 vs +3.52 ✓ | +1.65 vs −0.38 ✗ |
| spent flow (−, NQ) | −1.05 vs +2.15 ✓ | — |

**On NQ every term points the declared way.** The veto still removed winners, because:
- an exhausted gap is by definition also an aligned gap, so the two cancel (S = 0) and "exhausted" can never veto
  alone;
- S ≤ −1 caught only 53 trades.

That is a design flaw of the declared score, recorded for the successor.

**On ES the contraindications are reversed:** a probed level and a big gap are *good*. This fits lane D's mechanism
(ES is priced overnight, and its edge is the overnight move accepted at the open) and ES's gap-through class (D681).
**Those signs are root-specific, with a stated mechanism.**

## 5. By year and the four groups

**By year, B0 → B3 net:**
- NQ: 2019 +1.7 → +2.9; 2021 5.8 → 5.7; 2022 **+5.6 → −3.0**; 2023 −0.2 → −3.6; 2024 +9.0 → +6.3.
- ES: 2018 −3.5 → +4.5; 2021 +4.1 → +13.2; 2024 −2.3 → −7.2.

**NQ B3:**
- 726 trades, net −0.61, median −12.2, win 39%, payoff 1.53, skew +1.3;
- trimmed −1.46 / ex-top −2.61 / ex-bottom +0.55;
- Sharpe/Sortino −0.13/−0.22 (per trade).

**ES B3:**
- 387 trades, net +0.30, median −8.3, win 41%;
- trimmed −0.39.

**The component line (B3, daily $ at 1 micro):**
- NQ −0.03 (ρ K8 −0.08);
- ES −0.05 (ρ K8 +0.05);
- ρ between the roots 0.30.

## 6. Expectations (§6)

| # | expectation | outcome |
|---|---|---|
| 1 | the forecast beats persistence and the rotation null | **held** on both |
| 1b | Spearman 0.20–0.35 | failed: higher (0.42/0.46) |
| 2 | P(hold) flat by tier | NQ held (spread 0.08); **ES flagged** (0.11) |
| 3 | NQ B3 net +1–3 bp over B0 | **failed:** −2.8 bp |
| 4 | ES B3 at or below ~0 | held (+0.30) |
| 5 | placebo: NQ above p95, ES not | **failed:** NQ at 0.003 |
| 6 | some veto term removes non-negative net | held (ES's probe and exhausted gap; NQ's score veto) |

## 7. What this leaves, for the principal

1. **The construction as declared is rejected on development.** Skipping the forecast's bottom tier throws away NQ's
   best trades.
2. **The inverted size effect is the thread.** On NQ, breaks on days forecast to be quiet earn +7.7 net (t 2.3,
   44 a year, Sharpe 1.1): "a break the vol state did not expect".
   - This is post hoc on NQ.
   - It is testable cleanly on YM/RTY: the forecast is frozen, and the tier rule is declared *inverted*: trade the
     bottom tier, or size toward it.
3. **Root-specific signs with a mechanism:**
   - ES wants longs only, and its overnight-accepted moves (probe, big gap) as positives;
   - NQ wants the declared contraindications.
4. **Any successor score must avoid nested terms** (an exhausted gap inside an aligned gap).
5. **The calendar skips (FOMC, opex) should be dropped on NQ.**
