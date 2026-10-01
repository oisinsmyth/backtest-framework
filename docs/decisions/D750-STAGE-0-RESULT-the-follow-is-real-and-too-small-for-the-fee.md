# D750 STAGE 0 RESULT — NOT POSITIVE: the 13:30 follow is a real edge (rotation p 0.008) but +\$1.12 gross against a \$3.8 fee; mean −\$2.68 (t −6.3), median −\$3.26, 0 of 8 years; M6E stays the keeper

*2026-10-01.*
- *Pre-registration: [D750](D750-STAGE-0-PRE-REG-a-positive-mean-keeper.md) (9a8cf775).*
- *Runner: `scripts/stage0_d750_positive_keeper.py` (b16dcc8a), committed before its one run.*
- *Output: `data/stage0_d750_positive_keeper.json`.*
- *The known answer held: with the cap disabled, D748's variant I reproduced exactly (K1 −\$102.46, K2 −\$174.83, K3
  \$99.62, 384 fires).*

## 0. The reading

| | criterion | result | |
|---|---|---|---|
| **E1** | mean net > 0 at t ≥ 2 | **−\$2.676, t −6.27** | **fails** |
| **E2** | direction-rotation p_high ≤ 0.05 | **0.0079** over 1,897 offsets (null mean p50 −\$3.70, p95 −\$2.98) | holds |
| **M1** | median net ≥ 0 | **−\$3.257** (null median p50 −\$3.80, p95 −\$3.30) | **fails** |
| K1 | worst trade ≥ −\$50 | −\$45.67 | holds |
| **K2** | worst 30 days ≥ −\$150 | **−\$229.45** (NONE × T5) | **fails** |
| K3 | ≤ \$300 a year | \$95.47 | holds |
| K4 | zero breaches | 0 | holds |

**NOT POSITIVE: E1, M1, K2.** The keeper stays M6E, as written in `BOOK_PROP.md`.

## 1. What it shows (every eligible session, 2016-02-02 → 2023-12-29, n 1,897)

**The edge is real, and too small for the fee:**
- The move-since-09:00 direction beats its own rotation: gross **+\$1.12** a trade, about \$1 above where a random
  direction with the same clustering lands. The continuation from the open is there in the half hour.
- The round trip costs \$3.76–\$4.42 (M2K and MYM, 96 % of trades). Net is −\$2.68.
- **No year is positive (0 of 8):** the yearly means run −\$1.54 to −\$3.82.
- **It is not a tail artefact.** The 1 % trims are −\$3.52 (ex-top), −\$2.52 (ex-bottom) and −\$3.37 (both). The
  win rate is 38.6 %.
- Annualised as a line: Sharpe −2.28, Sortino −3.12.

**The cap cost nothing in mean and bought the worst trade:**

| | gross | net mean | worst trade | stop hits |
|---|---|---|---|---|
| uncapped | +\$1.121 | −\$2.672 | −\$138.58 | |
| \$40 cap | +\$1.117 | −\$2.676 | −\$45.67 | 5.2 % |

**K2 fails anyway.** The cap bounds each trade, not a run of them. Keeper-alone on a 5-session cadence, the worst
30 days was −\$229.

**D748's +\$3.5 gross was its fire days.** On every session the same rule grosses +\$1.1. The deadline days are a
selected subset, not a sample of the edge.

## 2. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| P1 | gross +\$2 to +\$4 | **missed:** +\$1.12 |
| P2 | cap: stop hits 3–8 %, gross −\$0.5 to −\$1.5 | stop hits 5.2 % (held); gross −\$0.004 (**missed:** the cap cost almost nothing) |
| P3 | E1 fails | **held** (net −\$2.68) |
| P4 | E2 passes, P ≈ 0.5 | **held** (p 0.008) |
| P5 | K1–K4 hold | **missed:** K2 −\$229 |
| P6 | M1 fails | **held** |
| | P(POSITIVE) ≈ 0.08 | NOT POSITIVE |

## 3. What follows

- **M6E stays the keeper.** Nothing in `BOOK_PROP.md` changes.
- **The principal's idea fails on the fee, not the signal.** A recycled edge must earn more than a micro's round
  trip inside the keeper's half hour, and the strongest one on file earns about a third of it there. Two levers
  remain, and both conflict with the keeper's limits:
  - **a longer hold:** more edge, but a larger dollar risk per trade (D731's to-the-close version nets +\$11 with
    hundreds at risk);
  - **fewer, larger moves:** this is D748's root selection reversed, against the never-kills limit.
- **On file, consistent with** "the hourly clock cannot carry the micro fee" and "commission, not spread, binds at
  micro size".
