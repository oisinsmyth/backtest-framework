# D694 STAGE 1 RESULT — NOT SUPPORTED on ES and NQ: coiled days are bigger, but the options market's own information does not pick better breaks; on ES the lift is the label's realised part, and on NQ coiled breaks earn less than quiet ones

*2026-09-29. In-sample development, 2018-01-09 → 2025-02-28; the vault was never read. The principal: "build the runner
and run it". Pre-registration [D694 STAGE 1 DESIGN](D694-STAGE-1-DESIGN-the-break-on-coiled-days.md) (`8cffb181`),
committed alone before its runner.*
- **The runner** `scripts/stage1_d694_coiled_break.py` was committed before any outcome (`ba51df29`). It ran once
  (`955db2ef`, 5.2 min). Output: `data/stage1_d694_coiled_break.json`, statistics only.
- **Dealer gamma (GEX) is SqueezeMetrics',** read to < 2025-03-01 and credited.
- **Known answers held before anything was scored:**
  - D672's C1 was reproduced on both roots (NQ 387 trades, +7.558 bp single-count net; ES 385, +2.778);
  - D680's at-level NQ gross +9.4189 was reproduced;
  - D691's d̄ was reproduced to 1e-12;
  - D691's IV lag audit passed on real data, and its canary fired.

## The answer in one line

**Both roots are NOT SUPPORTED. The implied-volatility ingredient fails on both.**
- **The label does select bigger days.** COILED sessions have a larger ln(range/ATR20) than QUIET ones on both roots.
- **Bigger days do not make the break pay more than realised volatility already implies.**
  - On ES the coiled cell's lift over QUIET is matched by a count-matched label with IV's own information scrambled.
  - On NQ, coiled breaks earn *less* than quiet ones.
- **Under D694 §7, the implied-volatility line closes for the break on ES and NQ.**

## 1. The gates

The object is D668's E4 plain break, one micro, friction once ($4.418 MES, $4.067 MNQ). All figures are gross at the
level, in bp per trade.

| | ES | NQ |
|---|---:|---:|
| B0 / C1 / **COILED** / QUIET trades | 1,118 / 384 / **120** / 264 | 1,110 / 384 / **127** / 257 |
| **(a)** COILED mean gross (HAC t; Holm p) | **+8.30** (2.63; 0.009) ✓ | **+6.96** (2.09; 0.018) ✓ |
| **(b)** ingredient null, 2,229 / 2,179 offsets: p50 / p95 | +6.64 / +10.64 | +8.46 / +12.93 |
| **(b)** rank of COILED | **0.765** ✗ | **0.298** ✗ |
| **(c)** COILED − QUIET (Welch t) | +4.43 (1.02) ✓ | **−3.12** (−0.56) ✗ |
| **(d)** COILED without Feb–Apr 2020 | +8.30 ✓ | +6.96 ✓ |
| **Gate 2:** EP-filtered COILED: trades, net (HAC t; Holm p) | 36, +4.20 (0.74; 0.23) ✗ | 87, +6.02 (1.30; 0.19) ✗ |
| **verdict** | **NOT SUPPORTED** | **NOT SUPPORTED** |

**The ingredient null does its job.** It rotates only the part of ln IV not explained by ln RV20, rv5, the overnight
range and ln(ATR/price), and keeps the rest. It is count-matched.
- **On ES its median (+6.64) sits above C1's own mean (+5.26).** A label built from the realised part alone already
  picks better-than-average C1 trades.
- **The realised-only label says the same:** C1 with the RV20 percentile ≥ 1/2 earns +5.12 (185 trades) on ES and
  +5.93 (177) on NQ.
- **What IV adds beyond that is within the null's body on both roots.** The secondary null (rotating ivrv whole) agrees:
  ranks 0.835 (ES) and 0.302 (NQ).

**Bounds (95 %, upper):**
- COILED − QUIET: **+13.0 bp (ES) and +7.8 bp (NQ)**;
- COILED's mean: +14.5 and +13.5.

**Power came in better than projected on NQ.** COILED's SE is 3.16 (ES) and 3.33 (NQ), against the design's 3.5 and
6.9. The 80 % minimum detectable effect is 7.9 and 8.3 bp. NQ's per-trade SD in this cell is about 38 bp, not the
~74 the design took from all of C1.

## 2. Reported, never gating

**The manipulation check (sessions, mean ln(range/ATR20)):** the premise holds inside C1.

| | COILED | QUIET |
|---|---:|---:|
| ES (147 / 440 sessions) | −0.124 | −0.464 |
| NQ (173 / 414 sessions) | −0.094 | −0.405 |

**The 3 × 2 grid** (gross bp; n). *Descriptive and unregistered: see §4.*

| ctier \ IV/RV | ES low | ES high | NQ low | NQ high |
|---|---:|---:|---:|---:|
| 1 (C1) | +3.87 (264) | **+8.30 (120)** | +10.08 (257) | **+6.96 (127)** |
| 2 | +3.86 (157) | +2.88 (207) | +2.19 (167) | +4.69 (187) |
| 3 | **−7.37 (85)** | +0.59 (280) | **−14.71 (99)** | +6.61 (270) |

**B0 by IV/RV half:** ES +1.98 (506) / +2.82 (612); NQ +2.87 (523) / +5.95 (587).

**The drift control (always-long open → 15:59, bp):**
- ES: COILED sessions +2.07, QUIET +6.08;
- NQ: COILED sessions **+10.65**, QUIET +0.86.

NQ's coiled days drifted up; its coiled breaks nonetheless earned less, with shorts +11.35 and longs +4.80.

**The four groups for COILED** (per trade unless stated):

| | ES | NQ |
|---|---:|---:|
| gross / net bp | +8.30 / +5.95 | +6.96 / +5.16 |
| gross / net $ per trade (breakeven cost = gross $) | $15.95 / $11.54 | $18.80 / $14.74 |
| daily Sharpe (Sortino), net | 0.69 (1.54) | 0.55 (1.19) |
| daily Sharpe (Sortino), gross | 0.94 (2.33) | 0.70 (1.59) |
| per-trade Sharpe (Sortino), net | 0.69 (1.58) | 0.49 (1.04) |
| exposure; daily vol; max drawdown | 6.8 % of sessions; $17.9; $285 | 7.3 %; $30.8; $562 |
| mean \|move\| vs 2c | 25.2 vs 4.7 bp | 33.5 vs 3.6 bp |
| median net; win rate; payoff | −4.5; 43 %; 2.10 | −11.7; 42 %; 1.90 |
| skew; excess kurtosis | 1.32; 1.64 | 1.21; 0.89 |
| 1 % trimmed net (k = 1): ex-top / ex-bottom / both | +4.79 / +6.47 / +5.30 | +4.08 / +5.69 / +4.61 |
| trades to half of gross; top 1 / 5 / 10 share | 5; 13 % / 53 % / 93 % | 4; 15 % / 70 % / 128 % |
| profitable years | 7 of 8 | 6 of 8 |
| long / short gross | +5.06 (77) / +14.11 (43) | +4.80 (85) / +11.35 (42) |
| before / after 2022-05-16 gross | +9.55 / +6.87 | +5.10 / +9.12 |

- **Named trades:**
  - ES's best is 2020-10-26 short (+147 bp) and its worst 2022-02-24 short (−54);
  - NQ's best is 2019-07-31 short (+143) and its worst 2022-06-15 long (−61).
- **Both books are right-tail books:** the mean is above the median, and a handful of trades carry the gross. That is
  the break's shape everywhere, not a feature of this cell.

**The component line** (CLAUDE.md; one micro, single-count $):
- **ES COILED:**
  - net Sharpe 0.69 (Sortino 1.54), gross 0.94;
  - hit 43 %, skew +1.32;
  - $4.42 a round trip against $15.95 gross a trade;
  - ρ with the MACD arm +0.02.
- **NQ COILED:**
  - net Sharpe 0.55 (Sortino 1.19), gross 0.70;
  - hit 42 %, skew +1.21;
  - $4.07 against $18.80;
  - ρ with the arm +0.04, **ρ with D680's C1 +0.46.**
- **On NQ, COILED is a subset of C1 that is worse than C1 itself:** C1's net Sharpe on the same window is 1.03, Sortino
  2.29. As a refinement of D680 it subtracts.

**ES C1 at the level, now on the record:** gross +5.18 bp (385 trades), from the known-answer block. The design quoted
+3.6 with the fill tick.

## 3. Predictions (§6 of the design)

| # | prediction | outcome |
|---|---|---|
| 1 | the manipulation check holds on both roots | **held** |
| 2 | NQ: COILED gross > QUIET gross | **failed** (−3.12 bp) |
| 3 | ES fails Gate 1(a) | **failed.** ES's COILED clears (a) at t 2.63; it fails on (b). |
| 4 | no root passes Gate 2 | **held** |
| 5 | NQ clears the ingredient null's p95 | **failed** (rank 0.30) |

## 4. A pattern in the grid, NOT tested (unregistered, one of six cells per root)

**The worst cell on both roots is ctier 3 with low IV/RV:** busy recent realised range that the options market does not
price forward.
- ES: −7.37 bp gross (85 trades);
- NQ: −14.71 (99).
- Its high-IV/RV neighbour earns +0.59 and +6.61.

**Why it fits, and why it is not a finding.** It is consistent with D691: a low ratio forecasts a smaller day, and a
break into a day that has already spent its range fails. But it was found by looking at a 3 × 2 grid after the run,
and it has not faced a null.
- **It is recorded as a lead only.** A veto of that cell would be a different construction.
- **It would need its own pre-registration, with the ingredient null, on a slice that has not seen this grid.** The
  in-sample window is now spent for any IV split of the break.

## 5. Deviations (none replaces a verdict)

1. **The first `--run` crashed** at a numpy string `min()` in the window check (`955db2ef` is the fix). That was after
   the C1 known answers and D691's reproduction had passed, and before any COILED statistic was computed. Nothing was
   printed or written.
2. **C1 holds 384 trades on each root here,** against D672's 387 (NQ) and 385 (ES). D694's window also requires a
   finite IV percentile and M1 forecast, which drops 3 NQ and 1 ES sessions. The known answers were checked on D672's
   own window.
3. **Holding time was not computed.** E4's exit function returns no bar index.
4. **The MACD arm's daily series** is D674's build, truncated below 2025-03-01 the moment it was built.
5. **The ingredient null's domain omits 5 (ES) and 3 (NQ) sessions** where IV/RV is finite but a regressor is not.
   Those keep their actual value.

## 6. Routing (the design's §7)

**NOT SUPPORTED on both roots closes the implied-volatility line for the break on ES and NQ.**
- **FINDINGS §99:** implied volatility predicts the day's size, but it does not select the break's trades beyond what
  realised volatility already selects.
- **`COMPONENTS_PROP.md`:** a scored-not-entered row.
- **D680 is untouched.** It stays frozen in slot 9, and D694 gives no reason to refine it.
- **The ctier-3 / low-IV/RV veto in §4 is open, untested, and needs its own pre-registration on the principal's word.**
