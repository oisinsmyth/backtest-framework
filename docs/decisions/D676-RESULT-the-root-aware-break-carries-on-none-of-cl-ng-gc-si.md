# D676 RESULT: NOT SUPPORTED on CL, NG, GC and SI. The root-aware break of yesterday's day-session range has no gross edge on any of the four; each sits inside its same-clock random-entry null, and net is negative at t −2.9 to −5.9. The opening-break line closes on energy and metals as it did on the index roots

*2026-09-29.*
- *One run of `scripts/stage0_d676_root_aware_break.py --run` under D676 (`df1865cc`) and D676-A1 (`7860ab11`); runner `f8fa1372`; 1.0 min.*
- *In-sample through 2025-02-28. The vault is not read; CL/NG post-vault data stays sealed for D626.*
- *Output: `data/stage0_d676_root_aware_break.json`.*

**Inputs, gated before the run:**
- The fixture `fut_opening_globex_1m_cl_ng_gc_si` (meta `0a6c033f`).
- **The first build failed the identity gate.**
  - The builder wrote prices at `%.2f`, which rounded NG (tick 0.001) and SI (tick 0.005).
  - 2,845,069 NG and 1,264,504 SI OHLC mismatches, on fully matched keys. None on CL or GC.
  - The runner raised in its gates, so no outcome was read.
  - Fixed in `97e04a16` (`%.5f` on the `--breadth` path; the index fixtures keep `%.2f`) and rebuilt (19.5 min).
- **Rebuilt fixture:**
  - Identity with `fut_day1m` is exact on all four: CL 791,549 bars, NG 790,607, GC 648,037, SI 633,695. There are 0 mismatches and 0 unmatched bars.
  - Coverage: ≥ 0.969 of sessions usable in every root-year. Excluded: CL 40, NG 39, GC 2, SI 6.
  - The seal held.
- **Environment:** the runner ran under `uv run --with pyarrow`. The project environment lacks pyarrow, which the identity gate's parquet read needs.

## 1. Gate 1, the mechanism (E4 gross on the primary book; Holm across four)

| | CL | NG | GC | SI |
|---|---|---|---|---|
| trades / a year | 883 / 96 | 662 / 72 | 1,037 / 111 | 1,092 / 117 |
| gross, bp (HAC t) | +0.53 (0.15) | −1.16 (−0.26) | +0.45 (0.46) | −2.48 (−1.64) |
| N1 (same clock, same side mix, every eligible session): p50 / p95 (SE) / rank | −1.05 / +4.30 (0.20) / **0.70** | −5.12 / +2.39 (0.28) / **0.82** | −0.79 / +0.64 (0.05) / **0.92** | −4.46 / −1.65 (0.17) / **0.88** |
| without Feb–Apr 2020 | −0.94 | −0.53 | +0.35 | −2.17 |
| Holm p | 1.0 | 1.0 | 1.0 | 1.0 |
| **Gate 1** | **fails** | **fails** | **fails** | **fails** |
| MDE (80%) | 9.7 | 12.3 | 2.7 | 4.2 |
| one-sided 95% upper bound on gross | +6.2 | +6.1 | +2.0 | +0.0 |
| NQ-equivalent effect (§7: 2.9% of ATR) | ≈ 7 | ≈ 13 | ≈ 2.9 | ≈ 5.8 |

**No root carries the break.**
- Each root's gross is inside its random-entry null, the best rank being GC's 0.92.
- **An edge of NQ's size relative to ATR is excluded on all four at one-sided 95%:** each upper bound is below its NQ-equivalent.
- This is a negative result with power, not an underpowered miss.

## 2. Gate 2, tradeability (no root reached it; reported)

| | CL | NG | GC | SI |
|---|---|---|---|---|
| cost, bp (1 micro: MCL / MNG / MGC / SIL) | 10.3 | 17.6 | 4.4 | 6.6 |
| net, bp (HAC t) | −9.79 (−2.87) | −18.74 (−4.27) | −3.91 (−4.06) | −9.05 (−5.90) |
| net at +1 tick a fill | −13.21 | −25.78 | −5.16 | −14.11 |
| net without Feb–Apr 2020 | −10.93 | −17.83 | −4.01 | −8.70 |

**Verdicts: CL NOT SUPPORTED; NG NOT SUPPORTED; GC NOT SUPPORTED; SI NOT SUPPORTED.**

## 3. What each root-aware adjustment removed

The base book is the break armed at the open on every session where its levels exist. Each skip is read one at a
time against the same base.

| E4 gross, bp (trades): removed / kept | CL | NG | GC | SI |
|---|---|---|---|---|
| base (no skips) | +0.98 (1,445) | −4.19 (1,495) | −0.39 (1,493) | −2.45 (1,505) |
| R1 roll | — (0) | — (0) | — (0) | — (0) |
| R2 delivery buffer | −0.88 (542) / +2.10 (903) | −3.81 (501) / −4.39 (994) | −5.15 (244) / +0.54 (1,249) | −6.74 (234) / −1.67 (1,271) |
| R3 index-roll window | +0.12 (429) / +1.34 (1,016) | **−15.68 (425) / +0.37 (1,070)** | +1.09 (214) / −0.64 (1,279) | +2.65 (189) / −3.19 (1,316) |

**R1 removed nothing by construction.**
- §2 takes yesterday's range "on the same contract", so a roll session has no levels and never enters the base.
- The roll skip is enforced by the level definition. Its separate read is empty, not failed.

**R2, the principal's delivery rule, removed worse-than-kept trades on CL, GC and SI** (−0.9 to −6.7 bp). On NG,
removed and kept are about equal.
- It costs the book nothing, and it keeps the book off expiring physical contracts, which is its purpose.

**R3 splits:**
- **On NG, breaks inside business days 5–10 were strongly negative:** −15.7 bp gross over 425 trades, against +0.4 kept.
  - Net t −7.1 on the removed set. The gross difference is roughly t −2.7 (computed from the reported SEs, not by the
    runner).
- On CL it removed about zero. On GC and SI it removed the better trades.
- **The NG read is a post-hoc lead** (§8), not a result: R3 was declared as a skip, not as a test.

**R4, EIA arming:**

| | CL | NG |
|---|---|---|
| EIA days | 477 | 478 |
| pre-release breaks the rule refused | +1.00 (217) | −3.98 (218) |
| breaks armed after the release | −1.23 (293) | −3.89 (282) |

Arming after the release did not help. On CL the refused pre-release breaks were the better ones; on NG the two are
equal.

## 4. The declared secondary: the quiet overnight (tier = the quietest third of the overnight two-way range)

| E4 gross, bp | CL | NG | GC | SI |
|---|---|---|---|---|
| quiet third (trades) | +0.32 (297) | +7.00 (232) | +1.39 (368) | +0.53 (403) |
| rest (trades) | −0.39 (506) | −5.32 (379) | −0.67 (584) | −4.62 (604) |
| quiet − rest | +0.70 | +12.31 | +2.05 | +5.15 |
| enumerated rotation: p50 / p95 / rank | −0.85 / 13.69 / 0.56 | −0.29 / 16.25 / 0.88 | 0.02 / 3.47 / 0.84 | 0.09 / 5.85 / 0.93 |
| quiet third, net | −9.57 | −10.24 | −2.90 | −5.83 |

- **Quiet − rest is positive on all four roots (prediction 4 held). None clears its rotation's p95.**
- Combining the four rotation ranks by Fisher gives p ≈ 0.06 (computed here, not by the runner; not a declared test).
- With D673's post-hoc reads on ES, NQ, YM and RTY, the sign is now positive on **8 of 8 roots**.
- **The quiet third is net-negative everywhere.**

## 5. Reported only

| | CL | NG | GC | SI |
|---|---|---|---|---|
| long / short gross | −4.30 / **+6.23** | −1.47 / −0.87 | +0.09 / +0.87 | −3.13 / −1.74 |
| E2 exit gross (stop at yesterday's level, flat at the flat time) | −3.59 | +0.91 | −0.21 | −5.03 |
| NG with a 0.5 A trail (gross / net) | | +1.96 / −15.62 | | |
| CPI days: gross (trades) | (2) | (0) | −1.42 (49) | −5.28 (44) |
| employment days: gross (trades) | −27.82 (37) | −0.22 (32) | −1.38 (58) | −9.58 (71) |
| share of fills at the open, gapping through the stop | 0.42 | 0.47 | 0.42 | 0.41 |
| years with gross > 0, of 10 (2025 = Jan–Feb) | 5 | 5 | 6 | 4 |
| years with net > 0 | 1 (2021) | 1 (2021) | 2 (2021, 2025) | 1 (2025) |

- **Short ≥ long on all four roots**, the reverse of the index roots (D668 §1: long > short on every one).
- **CL's shorts carry a gross +6.2 bp over 405 trades**, but net −4.3. That is a post-hoc cut, not a result.
- The runner's by-year `trades_per_year` field divides each year's count by the whole span, so it is mislabelled. The
  by-year trade counts (86–128 a full year) are correct.

## 6. The four groups and the component line (primary book, 1 micro)

| | CL | NG | GC | SI |
|---|---|---|---|---|
| gross / net / median net, bp | +0.53 / −9.79 / −31.57 | −1.16 / −18.74 / −41.74 | +0.45 / −3.91 / −11.98 | −2.48 / −9.05 / −20.66 |
| win / payoff | 31% / 1.61 | 34% / 1.25 | 33% / 1.44 | 33% / 1.33 |
| skew, kurtosis | 6.63, 102.7 | 1.31, 2.7 | 1.66, 3.9 | 1.51, 3.8 |
| net trimmed / ex-top / ex-bottom | −13.07 / −15.47 / −7.35 | −21.21 / −23.52 / −16.41 | −4.66 / −5.19 / −3.37 | −10.26 / −11.48 / −7.82 |
| Sharpe net / gross (per trade, annualised) | −0.94 / +0.05 | −1.41 / −0.09 | −1.34 / +0.15 | −1.79 / −0.49 |
| Sortino net | −1.76 | −2.05 | −2.13 | −2.66 |
| breakeven cost vs cost, bp | 0.53 vs 10.3 | < 0 vs 17.6 | 0.45 vs 4.4 | < 0 vs 6.6 |
| top trade | 2020-04-02 long, +1,745 bp | 2018-12-31 short, +515 | 2021-02-26 short, +157 | 2024-09-24 long, +269 |
| **daily $ Sharpe net / gross** | **−1.12 / −0.05** | **−1.22 / −0.24** | **−1.19 / +0.13** | **−1.41 / −0.29** |
| Sortino (daily $, net) | −1.90 | −1.75 | −1.92 | −2.26 |
| $ a year; max drawdown $ | −$605; $5,834 | −$445; $4,111 | −$690; $7,793 | −$1,900; $20,821 |
| ρ with K8 (rebuilt) | 0.05 | 0.02 | 0.00 | −0.01 |
| ρ between roots | GC–SI 0.20; every other pair \|ρ\| ≤ 0.06 | | | |

**Every mean sits above its median** (skew positive): each median is far more negative than its mean.
- The book is a many-small-losses, few-large-wins shape. The wins do not pay for the losses.
- CL's mean rests on its tail: one trade, the 2 April 2020 crude rebound, is worth 1,745 bp.

**Not rebuilt, and named:**
- #2, the MACD day-session arm: its daily P&L is not rebuilt here.
- #3, the NG winter spread: a monthly calendar spread with its daily P&L missing.

**No component: every daily net Sharpe is below −1.**

## 7. Predictions (§6)

| # | prediction | outcome |
|---|---|---|
| 1 | NG and CL pass Gate 1 | **failed** (CL rank 0.70, NG 0.82) |
| 2 | SI: gross > 0, fails Gate 2 | **failed** (gross −2.48) |
| 3 | GC fails Gate 1 | held |
| 4 | quiet overnight positive on ≥ 3 of 4 | held (4 of 4; none decisive) |
| 5 | EIA-armed beats refused, CL and NG | **failed** (CL reversed; NG equal) |

**Two of five held.**
- The root stories that predicted CL and NG would carry the break — in-session information and flow that chases
  it — are not supported.
- The one that predicted GC would not carry it (global pricing, like ES and YM) held, but so did the null on every other
  root.

## 8. Routing (§8)

**NOT SUPPORTED on all four.** The opening-break line closes on energy and metals, as it did on the index roots:
- D668, the plain break;
- D666, the re-break;
- D671, the size tier;
- D672/D673, the compression break.

Only NQ carried the plain break, and its number is in-sample.

**Leads recorded, not promoted.** Each is post hoc or undeclared as a test, and would need its own pre-registration on
data it has not seen:
1. **Quiet overnight:**
   - positive tier − rest on 8 of 8 roots;
   - 4 of the 8 pre-registered here, with ranks 0.56–0.93 and Fisher p ≈ 0.06;
   - net-negative on every energy and metals root.
2. **NG breaks inside the index-roll window lose 15.7 bp gross (425 trades).** The mechanism story is that the roll
   flow is mechanical and absorbs a break. If the lead is real, it is a fade read, not a break read.
3. **CL shorts:** +6.2 bp gross against −4.3 for longs.

**Treasuries (ZN/ZB) stay deferred,** per the principal.
