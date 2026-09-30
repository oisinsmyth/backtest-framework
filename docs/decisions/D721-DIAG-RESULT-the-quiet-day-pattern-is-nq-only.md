# D721 DIAG RESULT — the quiet-day F2 pattern is NQ's alone: ES, YM and RTY lean the same way but none clears its rotation (H-a not supported), and it does not follow volatility. RTY is the most volatile root and shows it weakest, and within every root, big last-hour moves on forecast-big days continue more, not less. CLOSED on the principal's word

*2026-09-30. One run of `scripts/diag_d721_quiet_day_f2_roots.py` (1.9 min).*
- **The order:** the [design](D721-DIAG-DESIGN-the-quiet-day-f2-pattern-on-other-roots.md) was committed first,
  and the runner (`3a10aac3`) before the run.
- **Output:** `data/diag_d721_quiet_day_f2.json`.
- **Known answers reproduced exactly:**

  | root | trades | mean net | source |
  |---|---:|---|---|
  | ES | 252 | +$13.208968 | D707's frozen answer |
  | NQ | 274 | +$20.670105 | D716 |
  | YM | 271 | +$6.147695 | D711 |
  | RTY | 224 | +$0.635786 | D711 |

- **Audits:** on every root the forecast and tier audits fired on their leaked canaries; the overnight audit, the
  date join and the seal (nothing dated 2024-01-01 or later) all held.
- **Window:** 2018-01 → 2023-12 (RTY from 2019-08, because its overnight bars start in 2017-07).

## 1. G1 — does F2 earn less on the days the size forecast calls big? (M0, the primary label)

| root | median σ20 (bp) | Spearman(τ, gross) | rotation p05 / p50 / p95 | rank | reading | efficiency, quiet − big (rank) |
|---|---:|---:|---|---:|---|---|
| RTY | **125.5** | −0.071 | −0.101 / 0.001 / 0.105 | 0.13 | NOT SIMILAR | 0.089 (0.66) |
| **NQ** (the reference) | 107.8 | **−0.125** | −0.092 / 0.001 / 0.097 | **0.011** | **SIMILAR** | 0.349 (0.97) |
| ES | 78.9 | −0.066 | −0.090 / 0.001 / 0.089 | 0.11 | NOT SIMILAR | 0.260 (0.91) |
| YM | 75.5 | −0.035 | −0.089 / −0.001 / 0.095 | 0.27 | NOT SIMILAR | 0.328 (0.96) |

- **M1 (with IV/RV), reported:**
  - ES: −0.054, rank 0.13, NOT SIMILAR;
  - NQ: −0.173, rank 0.001, SIMILAR (D720's figure, reproduced).
  - On NQ the IV/RV term sharpens the pattern (the big tercile nets −$0.61 under M1, against +$15.00 under M0). On
    ES it does not.
- **By tercile, quiet / mid / big (M0):**

  | root | mean net | efficiency |
  |---|---|---|
  | ES | +$20.68 / +$1.10 / +$17.34 | 0.55 / 0.10 / 0.29 |
  | NQ | +$38.11 / +$17.16 / +$15.00 | 0.52 / 0.28 / 0.18 |
  | YM | +$14.23 / −$0.41 / +$6.26 | 0.53 / 0.08 / 0.20 |
  | RTY | +$1.82 / +$2.32 / −$0.63 | 0.17 / 0.16 / 0.08 |

**H-a (the pattern generalises): NOT SUPPORTED.**
- 0 of ES, YM and RTY read SIMILAR; two were needed.
- **But the sign agrees everywhere.** All four Spearmans are negative, and quiet-day efficiency is the highest
  tercile on ES, NQ and YM. The efficiency gap sits at the 91st–97th percentile on those three.
- **Why the dollars don't follow:** on ES and YM, forecast-big days carry bigger moves, so the net per trade barely
  falls (ES: $20.68 quiet, $17.34 big). A faint common lean, no dollar pattern outside NQ.

## 2. H-b — is it volatility? Not in these data

- **Across roots:**
  - The most volatile root, RTY (σ20 125 bp), shows the pattern weakly and insignificantly.
  - NQ (108 bp) shows it strongest.
  - ES and YM (76–79 bp) show it weakly.
  - The strength does not follow volatility. RTY is also where F2 itself barely works (+$0.64 net), so its
    reading is weak evidence either way.
- **Within each root, the principal's mechanism** (in a high-volatility regime, bigger moves revert more) would show
  as a lower, or negative, slope of F2's gross on its last-hour move size a on the forecast-big days. It shows the
  opposite. Spearman(a, gross) on big days against quiet days:

  | root | big days | quiet days |
  |---|---:|---:|
  | ES | +0.22 | +0.21 |
  | NQ | **+0.25** | +0.14 |
  | YM | +0.11 | +0.15 |
  | RTY | +0.09 | +0.04 |

  On forecast-big days, bigger last-hour moves continue at least as much as on quiet days, and on NQ more.
  **Nothing reverts.** Big-day F2 trades are weaker because the median trade is smaller relative to the noise
  (NQ big-tercile median gross $5.00 against $37.50 quiet), not because big moves turn around.

## 3. The books, reported (one micro; nothing chosen)

| root | F2: net Sharpe (Sortino); gross; net $ a year | F2 on quiet days only (τ < 1/3) |
|---|---|---|
| ES | +0.90 (+1.55); +1.20; $562 | 48 trades: +0.98 (+2.16); $168; 3 of 6 years positive |
| NQ | +1.05 (+1.78); +1.25; $957 | 59 trades: +1.09 (+1.87); $380; 5 of 6 years positive |
| YM | +0.61 (+0.96); +0.99; $282 | 59 trades: +0.94 (+2.36); $142; 3 of 6 years positive |
| RTY | +0.09 (+0.13); +0.62; $33 | 53 trades: +0.15 (+0.20); $22 |

- **No quiet-only book improves on its line in dollars.** Each keeps 19–24% of the trades.
- **F2's trade distribution, by root:**
  - ES: median $6.21, both trimmed $12.50;
  - NQ: median $11.43, both trimmed $19.52;
  - YM: median $1.70, both trimmed $6.47;
  - RTY: median −$0.76, both trimmed $0.12.

## 4. What it says

1. **The quiet-day pattern is NQ's.** It is significant only on NQ, it is sharpest with NQ's IV/RV term, and on
   the other roots it is a same-signed lean inside chance. As a filter it would be a selection on one root's
   in-sample history, which is D717's failure shape.
2. **The volatility explanation does not fit.** RTY, the more volatile root, shows it least, and within each root
   big moves on big-forecast days continue rather than revert.
3. **What does fit, as a description, not a claim:** F2 is a relative-size filter. On a day forecast to be quiet, a
   large last hour stands out from the day's expected noise. On a day forecast to be loud, the same relative move
   is a smaller part of a noisier day, so the continuation is a smaller share of the noise. This is D720's "the
   forecast is a volatility forecast" seen from F2's side.

## CLOSED, 2026-09-30, on the principal's word

The principal: "Close the quiet-day pattern on F2 after check for similar patterners in other roots."
- The check is done: H-a is not supported, and H-b does not fit.
- **Closed under R15:** conditioning F2 (on any root) on a forecast of the day's size, whether as a filter, a skip,
  or a size rule. This includes the quiet-day subset.
- **Kept as market structure:** on ES, NQ and YM, F2's direction efficiency is highest on forecast-quiet days.
  This is a description, not a filter.
