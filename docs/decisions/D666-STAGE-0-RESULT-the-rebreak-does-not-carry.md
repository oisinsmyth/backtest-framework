# D666 STAGE 0 RESULT — NOT SUPPORTED at Gate 1 on both roots: the re-break of yesterday's range does not carry before costs, and in every cell it does WORSE than a plain break at the same distance; on ES it is below random entry in the retest's own hour

*2026-09-29.*
- *One run of `scripts/stage0_d666_rebreak.py` (`811fc42`) under D666 (`0bfd9e7`) and D666-A1 (`e106fcf`), 1.4 min.*
- *In-sample 2016-01-04 → 2025-02-28 through the sealed loader. Sierra TICK was read before 2025-03-01 only. GEX came
  from the prior row. **Dealer gamma (GEX): SqueezeMetrics.***
- *Output: `data/stage0_d666_rebreak.json` (statistics only, licence-guarded).*

**Audits.** The selftest's six audits fired on broken inputs. In the run:
- the setup agreed with its array-based second path on every session of both roots;
- the GEX lag audit held.

**The setup:**
- ES: 652 re-breaks (71.9 a year; 294 long, 358 short). NQ: 700 (77.2 a year; 344 long, 356 short). Both are as the
  frequency count said.
- 2 same-minute touch-and-trigger cases per root were left out by the conservative arming.
- Plain breaks at the same distance: ES 1,432, NQ 1,435.

## Gate 1, the mechanism (unfiltered, GROSS per trade, bp; Holm across 8)

| cell | re-break gross (HAC t) | plain break gross | re-break − plain (Welch t) | random-entry null p50 / p95; rank | ex-COVID | MDE | vault power |
|---|---|---:|---|---|---:|---:|---:|
| ES E1 target+stop | −2.23 (−1.49) | −0.63 | −1.61 (−0.70) | −1.01 / +0.06; **0.03** | −1.47 | 4.2 | 1% |
| ES E2 hold+stop | −0.72 (−0.38) | −0.51 | −0.21 (−0.08) | −0.40 / +0.73; 0.29 | −0.09 | 5.3 | 2% |
| ES E3 60 min | −2.29 (−1.37) | −0.44 | −1.85 (−0.93) | −0.97 / −0.12; **0.01** | −2.32 | 4.7 | 1% |
| ES E4 trailing | −1.00 (−0.76) | **+1.20** | −2.20 (−1.35) | −1.20 / −0.40; 0.69 | +0.02 | 3.7 | 1% |
| NQ E1 | +0.99 (0.40) | **+3.46** | −2.47 (−0.84) | −0.11 / +1.25; 0.92 | +2.53 | 7.0 | 4% |
| NQ E2 | −0.23 (−0.09) | **+3.55** | −3.78 (−1.21) | −0.07 / +1.27; 0.41 | +1.28 | 7.3 | 2% |
| NQ E3 | −2.33 (−1.14) | −0.48 | −1.85 (−0.75) | −0.69 / +0.41; **0.01** | −1.28 | 5.7 | 1% |
| NQ E4 | +1.31 (0.79) | **+4.29** | −2.98 (−1.46) | +0.30 / +1.35; 0.94 | +2.27 | 4.6 | 5% |

**Every Holm p is 1.00. No cell passes a single Gate-1 condition beyond ex-COVID.**
- **The pullback-and-re-break is worse than simply buying the break, in all eight cells** (by 0.2–3.8 bp before
  costs).
- **On ES it is at or below the random-entry null's median in three of four exits.** With the 60-minute exit (E3)
  and the target exit (E1), entering on the re-break ranks 0.01–0.03 against entering at a random minute in the hour
  after the retest. The re-break is a *late* entry.

**The four groups** (1 micro; per-trade Sharpe annualised by trades a year):

| cell | net | median | win | payoff | skew | trimmed / ex-top / ex-bottom | Sharpe net / gross | Sortino | maxDD (bp) |
|---|---:|---:|---:|---:|---:|---|---|---:|---:|
| ES E1 | −5.78 | −21.9 | 35% | 1.35 | +1.03 | −6.20 / −7.61 / −4.37 | −1.07 / −0.41 | −1.58 | 3,874 |
| ES E2 | −4.27 | −22.2 | 33% | 1.63 | +2.12 | −5.81 / −7.22 / −2.84 | −0.67 / −0.11 | −1.16 | 2,858 |
| ES E3 | −5.85 | −5.0 | 41% | 0.96 | −0.49 | −5.68 / −7.70 / −3.82 | −1.15 / −0.45 | −1.45 | 3,875 |
| ES E4 | −4.55 | −11.3 | 34% | 1.35 | +1.14 | −5.06 / −6.16 / −3.44 | −1.15 / −0.25 | −1.69 | 3,081 |
| NQ E1 | −1.57 | −26.2 | 38% | 1.56 | +1.03 | −2.35 / −3.77 / −0.15 | −0.23 / +0.14 | −0.38 | 1,921 |
| NQ E2 | −2.80 | −27.6 | 35% | 1.66 | +1.46 | −4.00 / −5.40 / −1.38 | −0.39 / −0.03 | −0.67 | 3,513 |
| NQ E3 | −4.90 | −4.4 | 46% | 0.91 | −0.08 | −4.88 / −6.98 / −2.79 | −0.81 / −0.39 | −1.06 | 3,795 |
| NQ E4 | −1.26 | −11.8 | 37% | 1.54 | +1.49 | −2.19 / −3.24 / −0.20 | −0.26 / +0.27 | −0.44 | 1,674 |

- Costs are 3.55 bp (ES) and 2.57 bp (NQ) a round trip, including one tick of stop slippage each way.
- Breakeven costs equal the gross means, all at or below 1.3 bp.
- The stop exits give low win rates, strongly negative medians and positive skew: the classic breakout profile,
  without the right tail to pay for it.

**Splits:**
- **Long against short:** long gross ES +0.2 to +2.9 and NQ −0.9 to +5.0; short ES −2.8 to −4.2 and NQ −1.2 to −5.3.
  That is the index's upward drift (D659, D660), not a property of the re-break.
- Before and after 2022-05-16: no consistent sign.

**A component line** (§6) was pre-registered with ρ against K1–K6. The runner omitted the correlations. With every
cell net negative the line is moot, and it is disclosed here.

## Gate 2, tradeability (walk-forward expected-profit filter): nothing reached it, and it confirms the null

No cell passed Gate 1. As a read only, the walk-forward pass-through π̂ settles near zero on all eight cells
(−0.03 to +0.02), so after the burn-in the filter blocks almost everything:
- ES: 0 filtered trades in every cell;
- NQ: E1 98 trades, net **−10.2**; E4 192 trades, net −4.7.

**The filter behaves as designed.** With no carry to pass through, it has nothing to select.

## The secondary layer: sizing and the fade veto

**Confluences:** aligned on 57–61% of trades (gap), 59–61% (A7) and 45–47% (TICK).

**The slope of net per trade on the confluence count:**

| cell | slope (t) |
|---|---|
| **ES E1** | **+4.14 (2.03)** |
| ES E2 | +2.00 (0.75) |
| **ES E3** | +3.87 (1.90) |
| **ES E4** | **+3.55 (2.19)** |
| NQ E1 | +1.62 (0.60) |
| NQ E2 | −0.07 (−0.03) |
| NQ E3 | −0.64 (−0.25) |
| NQ E4 | +1.13 (0.55) |

- **On ES, more aligned confluences mean better re-break trades, by about 4 bp each** (t 1.9–2.2 on three exits,
  which are one correlated test in effect). **It does not make the trade profitable:** the sized book's per-trade
  Sharpe is −0.06 to −0.09, against −0.11 to −0.12 flat.
- It is a pre-registered secondary with no gate. Across 8 cells, t of 2 is not beyond chance.
- It is the one pre-registered piece of this line that points the way the principal's idea does.

**The fade veto:** it removed 112 (ES) and 114 (NQ) trades. The vetoed trades were worse than the kept ones in 5 of 8
cells (for example NQ E3 −9.63 vs −3.98; ES E1 −7.75 vs −5.38), all within noise (|t| ≤ 1.2). The direction is right,
but it is not established.

## Predictions (§10)

| # | prediction | outcome |
|---|---|---|
| 1 | not supported at Gate 1 | **held** |
| 2 | re-break − plain within ±2 bp | **failed:** worse by up to 3.8 |
| 3 | no exit beats E3 | **failed:** E2 and E4 beat E3 on both roots |
| 4 | the sizing slope inside noise | **failed on ES:** t 1.9–2.2 |
| 5 | vault power below 50% | **held:** 1–5% |
| 6 | π̂ near 0 | **held** |

## Post hoc, unpromotable: the plain break on NQ

The control, a stop 0.25 ATR beyond yesterday's high or low with no pullback, grossed **+3.46 / +3.55 / +4.29 bp** on
NQ with the target, hold and trailing exits, over about 1,435 trades.
- That is above NQ's 2.57 bp cost, and fits the memory "index roots trend intraday".
- It was a control, not a hypothesis. Its own t was not computed, and ES's plain break is about zero.
- It is named here so nobody reads it later as a finding. Pursuing it would need its own pre-registration, on a
  sample it was not chosen on.

## Routing (§8)

**NOT SUPPORTED on ES and NQ.**
- The re-break line closes on this construction. The retest makes the entry later, and worse than the plain break.
- Per §8, other roots are not tried without a new reason.

**What stays open, named:**
- the ES confluence slope (a pre-registered secondary at t ≈ 2);
- the NQ plain-break gross above cost (post hoc).

Each would need its own design and a confirmation sample. The vault's power at these sizes is 1–5% per cell.
