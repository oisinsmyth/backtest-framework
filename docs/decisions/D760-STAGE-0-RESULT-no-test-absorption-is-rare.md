# D760 STAGE 0 RESULT — NO TEST: absorption on quiet long-gamma days fires only 129 times in eight years, below the 150-trade gate, and the +$3.83 mean is one FOMC trade. Arming alone, now read in-sample, loses $4.39 a trade

*2026-10-02. Prop book.*
- *Pre-registration: [D760](D760-STAGE-0-PRE-REG-flow-validated-quiet-gamma-fade.md) (`b0d97ef0`).*
- *YM fixture: `scripts/build_fut_ym_signed_1m.py` (`9f771ad6`), built and validated before any outcome was read
  (`b6b7efb5`).*
- *Runner: `scripts/stage0_d760_absorbed_fade.py` (`b94d65a9`), committed before its run.*
- *Output: `data/stage0_d760_absorbed_fade.json`. Wall 35 s.*

**The first launch stopped before any result.** Nothing was printed or written: a numpy min over the date-string
calendar in the component line, the bug D756 hit. The fix (`dbfb65ac`) was committed before the one complete run.

**The checks:**
- the known answer (D757's G ∧ ¬I cells on ES, NQ and YM) held;
- the lag audit (a plain loop over the raw rows on 40 armed days per root) passed;
- A0 reproduced D756's fade;
- nothing dated 2024-01-01 or later was read.

## 0. The YM fixture

`fut_YM_signed_1m`: 2,062 sessions, 2016-01-04 → 2023-12-29, from Sierra's `-CBOT` tick files, built in 22 s.

| check | gate | result |
|---|---|---|
| V1 median volume ratio | 0.98–1.02 | 1.00 |
| V2 volume correlation | ≥ 0.98 | 0.99993 |
| V3 signed share | ≥ 0.99 | 1.000 |
| V4 last = close | ≥ 95% | 98.7% (within one tick 99.7%) |

**PASS.** YM ran with ES and NQ in one run, as pre-registered.

## 1. The reading

| gate | result | passes |
|---|---|---|
| **T trades** | **129** (ES 33, NQ 22, YM 74) against ≥ 150 | **no: NO TEST** |
| G1 edge | mean net +$3.83, day-clustered t 0.44, median +$2.20 | no |
| G2 the flow carries it | efficiency 0.159 against the rotation's p50 −0.017 and p95 0.053 (506 exact offsets, rank 1.000) | yes, **but see §3: the null is mis-sized** |
| G3 more than arming | V +$3.83 against A0 −$4.39 | yes |
| G4 not one episode | 2021 alone carries 125% of the net; 3 of 5 eligible years positive | no |
| G5 across roots | ES +$7.85, NQ +$25.48, YM −$4.40 | yes |

**The declared reading is NO TEST.** Read past the trade gate, G1 and G4 fail as well.

## 2. The books (one micro; net beside gross)

| book | trades | net mean (median) | gross mean | win | skew | daily net Sharpe (Sortino) | daily gross Sharpe (Sortino) |
|---|---:|---|---:|---:|---:|---|---|
| **V, absorbed fade** | 129 | **+$3.83** (+$2.20) | +$7.83 | 51.9% | +1.31 | 0.17 (0.28) | 0.34 (0.59) |
| A0, arming alone (10:30 fade) | 1,545 | **−$4.39** (−$5.07); clustered t −1.26 | −$0.29 | 45.7% | +0.69 | −0.48 (−0.67) | |
| P0, no progress alone | 1,539 | −$5.64 (−$4.42) | −$1.54 | 45.8% | +0.64 | −0.66 (−0.89) | |

**V in full:**
- **Size and cost:**
  - exposure is 6.8% of sessions, and the maximum drawdown is $773;
  - the mean \|move\| is $49 against a cost of about $4;
  - the break-even cost is $7.83 a round trip.
- **The trade distribution:**
  - payoff 1.08, kurtosis 16.3;
  - **trimming 1%:** ex-top −$0.76, ex-bottom +$6.78, both +$2.18.
- **What the winners depend on: one trade.** NQ on 2023-02-01 (an FOMC day), entered at 13:00, netted **+$592**,
  which is 120% of V's total net of $494. One trade reaches half the net.
  - The rest of the top five: NQ 2023-01-25 +$299, YM 2023-02-01 +$166, ES 2022-03-29 +$121, ES 2021-03-15 +$112.
  - The worst: NQ 2023-08-04 −$374.
- **By year:**

  | | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
  |---|---:|---:|---:|---:|---:|---:|---:|
  | trades | 25 | 5 | 14 | 17 | 22 | 4 | 42 |
  | net | +$15 | +$78 | −$196 | −$358 | +$616 | −$141 | +$479 |

- **Long against short:** long +$8.48 (78), short −$3.28 (51).
- **By price tercile:** −$0.96, +$24.32, −$5.28.
- **Entry clocks:** spread from 11:00 to 14:00 (10–26 each).
- **Next-bar-open entry:** +$3.85, the same.
- **The reverting rate on V's days is 0.450,** against 0.37–0.40 on the armed days (ES 0.39, NQ 0.50, YM 0.46). With
  n 129 the SE is 0.044, so it is 1.6 SE above, and it only reaches D759's break-even.
- **The component line:** daily net Sharpe 0.17 (Sortino 0.28), hit rate 51.9%, skew +1.31. ρ with F2 −0.02, C1
  −0.01, D737 +0.06.

## 3. G2 passed on a null with the wrong trade count (disclosed; POST HOC)

**The flow rotation is not count-matched.** In the real data, heavy aggressive flow almost always moves the price,
so a window with A1 (aggressive in the morning's direction) and A2 (no progress) is rare:
- it fires on 0.7–2.3% of usable windows (ES 1.1%, NQ 0.7%, YM 2.3%);
- I had predicted 3–6%.

Rotating the flow across days breaks that coupling, so **the rotated books fire about 700 trades (p5 666, p95
742), not 129.** The efficiency of a 700-trade book varies far less than that of a 129-trade book, so the null's p95
of 0.053 is too narrow for the observed book.

**A count-matched version** (`temp/idle/d760_rotation_counts.py`, POST HOC): draw 129 trades from each rotated book,
20 draws per offset.

| | p50 | p95 | observed | rank |
|---|---:|---:|---:|---:|
| count-matched null | −0.018 | **0.209** | 0.159 | 0.90 |
| without the top trade | | | 0.072 | 0.74 |

**Against a null of its own size, the flow does not clear p95.** G2's declared pass is the null's artifact. It is the
same class of error as D711-A1's: an input rotation that changes what the filter selects is anti-conservative.

## 4. What it shows

- **True absorption is rare on the index futures.** Aggressive flow and price move together so tightly that "hard
  buying, no progress" happens about five times less often than chance would place it. On quiet long-gamma days it
  happens about 16 times a year across three roots: too few to trade, and too few to test in eight years.
- **When it does fire, nothing reliable follows:**
  - the mean is one FOMC afternoon;
  - YM, with the most trades, loses;
  - the year pattern alternates.
- **Arming alone is now measured in-sample.** The 10:30 fade on quiet long-gamma days loses $4.39 a trade (gross
  −$0.29). That is what D759's NO ROOM implied: q ≈ 0.38 against a break-even of 0.45. NQ alone is near zero
  (+$0.93).

## 5. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| P1 | NOTHING (G2 fails) (P 0.6) | **missed as declared:** G2 passed, but only on a mis-sized null (§3); count-matched it would fail. The reading is NO TEST |
| P2 | A0 nets between −$8 and +$2 (P 0.7) | **held** (−$4.39) |
| P3 | 250–450 V trades (P 0.6) | **missed** (129): I overestimated how often aggression and no-progress coexist |
| | P(PASS) ≈ 0.07 | NO TEST |

## 6. What follows

- **The reverting-day line (D756, D757, D759, D760) has now been tried four ways:**
  - the prize is real;
  - the detectors lift the reverting rate by 3–6 points;
  - absorption is too rare to carry a trade.

  **I recommend closing it** (the pre-registration's §4). That is the principal's call.
- **A lesson for any joint trigger:** when a trigger requires two inputs that are strongly coupled in the data,
  rotating one of them changes the trigger's count. The null must be count-matched, or the gate must use a
  count-invariant statistic whose spread does not shrink with n.
- **The YM signed-flow fixture stays** for later use. Its validation matches ES's and NQ's.
- **Intraday mean reversion on the index micros stays closed for trading.**
