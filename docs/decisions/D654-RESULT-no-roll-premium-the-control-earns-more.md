# D654 RESULT — there is no reverting roll premium in the gold and silver spreads: the trade earns +0.44 bp gross against a placement median of +0.80, the same trade at month-ends with no roll earns more, the receiving month cheapens during the drain rather than richening, and the expected-profit filter never trades

*Pre-registration [D654](D654-PRE-REG-selling-the-metals-roll-after-first-notice.md) (`b0d456b`), committed alone
before the runner existed; runner and POWER `f4b784c`, committed before the run. Runner
`scripts/run_d654_metals_roll.py`; numbers [`data/d654_metals_roll.json`](../../data/d654_metals_roll.json) and
[`data/d654_power.json`](../../data/d654_power.json). In-sample cycles only, last settlement 2023-12-29; the 2024+ slice
is unread for this line. **Disclosed:** the first `--run` invocation crashed constructing the component line
(`DailyPnL` needs `source_sha256`) after the statistics were computed and **before anything was printed or
written**; the argument was added and the run repeated, identical by construction (a deterministic computation on
the same inputs).*

## The answer in one line

**Route: B2 or B3 fails, so the forced roll leaves no reverting premium in these spreads, and the recommendation is to
close the delivery line** (principal, R15). Four of five bars fail. The fifth (B5) passes only because the median is
zero to twelve decimal places.

## 1. The primary: GC and SI pooled, 79 cycles

| | outcome |
|---|---|
| gross per cycle | **+0.44 bp** (t 0.51); +$9.75 a spread |
| net per cycle (base cost 12.8 bp) | **−12.39 bp** (t −7.77); −$127.06 a spread |
| net at stress cost | −24.19 bp |
| placement null, 68 enumerated offsets | p05 −0.82, **p50 +0.80**, p95 +2.58: **rank 0.37**, below the null's median |
| **the no-roll control** (101 serial-month placements) | **+2.37 bp**, t 2.39: the same trade at month-ends with no forced roll earns **more** (Welch t of primary − control **−1.67**) |
| years with positive gross | 4 of 8 against the null's p95 of 7.65 |
| median, trimmed mean | 1.4 × 10⁻¹² (zero), +0.30 |
| hit rate (gross) | 50.6 % |

| bar | outcome |
|---|---|
| B1 net t ≥ 2 | **FAIL** (−7.77) |
| B2 above placement p95 | **FAIL** (+0.44 against +2.58) |
| B3 above control, Welch t ≥ 2 | **FAIL** (−1.67) |
| B4 year count at the null's p95 | **FAIL** (4 against 7.65) |
| B5 median and trimmed mean > 0 | passes, **degenerately**: the median is floating-point zero |

**By root:** GC +1.38 bp gross against 5.45 bp of cost (net −4.07); SI −0.48 bp against 20.02 (net −20.50).

## 2. The mechanism went the other way

Over the drain, d = −10 → −1, the pre-registration predicted that the rollers' buying would push R up against H.
**R cheapened: −1.68 bp** (t −2.02; GC −1.39, SI −1.96). The short-R/long-H position earned during the drain, not
after it, and it earned about what the same position earns at any month-end: the control's +2.37 bp and the
placement median's +0.80 bp.

The simplest reading is a **drift, not a flow**. Short the near month against the far month in gold and silver
gains as the contango widens, which it did across 2016–2023 as rates rose twice. The roll adds nothing measurable
to that drift in either direction. Exits at +1, +3 and +10 read +0.25, +0.51 and −0.03 bp.

## 3. The expected-profit filter

After an eight-cycle burn-in per root, 63 cycles were eligible, and **the filter traded none**. The pass-through b was
positive, but b × x never reached twice the cost (5–20 bp against a gross of about 1 bp). Verdict: **UNRESOLVED
(0 traded)**. The filter was promotable only with B2 and B3, which failed. It did what the principal's rule is for:
it refused every trade whose projected size did not cover its cost.

## 4. The four reporting groups

1. **Performance, one GC and one SI spread, daily book 2016–2023:**

   | | Sharpe | Sortino | per year | vol | max drawdown |
   |---|---:|---:|---:|---:|---:|
   | **gross** | +0.45 | +0.83 | +$96 | $216 | −$625 |
   | **net** | −2.35 | −2.46 | −$1,257 | $534 | −$10,143 |

   Exposure 18 %. Mean move per trade: +$9.75 against a round trip of $136 (the GC/SI mean). **Breakeven round trip:
   $9.75.**
2. **Trade distribution (gross bp):** n 79, mean +0.44, median 0.00, hit 50.6 %, payoff 1.14, skew +1.00, kurtosis
   5.2. Ex-top +0.11, ex-bottom +0.63, trimmed +0.30. The largest cycle is GC May 2020 (+26.0 bp, +$450, the COVID
   dislocation in gold's curve); without it the mean is +0.11.
3. **What it depends on:** GC's +1.38 against SI's −0.48; positive in four of eight years; one COVID cycle carries
   three quarters of the mean.
4. **The null:** p50 +0.80 and p95 +2.58 against +0.44: **not decisive for, decisive against.** The construction sits
   below its own placement median.

**Component line (personal book, one spread each):** net Sharpe −2.35, net Sortino −2.46, gross Sharpe +0.45,
gross Sortino +0.83, exposure 18 %, hit on active days 41 %, skew −4.35. ρ with the MACD arm is **not computable**:
the arm's daily series is not on disk (D590's gap).

## 5. The secondary cells

- **HG:** gross +1.49 bp, net −6.87 (t −2.73), placement rank 0.59, and its no-roll control earns more (+3.34).
- **6C:** gross −0.45 bp, net −3.53, placement rank **0.04**, control +0.25.

Neither could pass anything without the primary. Both say the same thing.

## 6. The predictions

| | prediction | outcome |
|---|---|---|
| 1 | the drain pushes R up against H on both roots | **FAILED**: R cheapened on both (−1.39, −1.96 bp) |
| 2 | the gross is small and positive | held (+0.44 bp) |
| 3 | B1 fails | held |
| 4 | the control sits inside its placement null | held, at the edge (+2.37 against p95 +2.58) |
| 5 | the filter trades under half, few silver | held trivially: it traded nothing |
| 6 | gold carries whatever there is | held (+1.38 against −0.48) |

## 7. What this closes, and what it does not

D653 showed that forced roll flow in gold and silver is **large** (a quarter of the receiving contract's volume),
**late**, **outside the index window** and **mostly a roll**. D654 shows that it **leaves no price footprint** a
no-expiring-leg spread can collect: not during the drain, not after it, not at five, one, three or ten sessions.
The month's curve moves the same with or without the roll.

**Recommended:** close the delivery-period line (the principal's word, R15). The Stage 0 fixture and the per-row
contract resolver stay as instruments. The resolver fixes a defect that D653's builder shares on far-dated recycled
codes: 729, 378 and 669 rows of GC, SI and HG, none of them a cycle's expiring, receiving or hedge month.
