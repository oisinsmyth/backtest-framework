# D689 STAGE 0 — short-gamma continuation on ES survives the volatility control (98.5th percentile), holds in all eight years and is not the 2020 crash; but it pays only at full ES size, and the clean 2024 slice cannot confirm it (expected t 1.1)

*2026-09-29. In-sample development on D688's panel (1,989 sessions, 2016-01-05 → 2023-12-29), plus a
conditioner-only premise count on 2024-01 → 2025-02. It is a go/no-go for a pre-registration, not a verdict, and no
outcome slice was spent. The principal: "go after short-gamma days with volatility is controlled".*
- **The script** `scripts/stage0_d689_short_gamma_continuation.py` was committed before its run (`dba4d126`), with its
  object, statistics and decision rule in its docstring. It ran once, in 268 s. Output:
  `data/d689_short_gamma_continuation.json` (statistics only, no per-date GEX).
- **D688's β_G reproduced exactly.**

## The answer in one line

**The declared outcome is UNCONFIRMABLE ON THE CLEAN SLICE:** tests 1 and 2 pass, and test 3 fails.
- **The effect is a gamma effect, not a volatility effect.** On short-gamma days (G_SUM < 0), following the last hour
  for the next hour earns +2.12 bp gross, against +0.12 on long-gamma days. Within deciles of the day's own realised
  variance the short-minus-long difference is **+1.48 bp, the 98.5th percentile** of 1,970 enumerated rotations of the
  short-gamma label.
- **It is not one episode:** +$4.06 a MES trade without the 2020 crash (t 3.24), positive gross in **all 8 years**.
- **It pays only at full ES size,** where the round trip is cheaper per point: net Sharpe +0.51 (Sortino +0.75), ρ −0.05
  with the MACD arm. On MES it is −0.18.
- **The clean 2024 slice has 66 short-gamma sessions.** That gives an expected t of 1.12, under the 1.5 the power rule
  requires.

## 1. The object (fixed before the run)

- **When:** at each decision time t = 10:30, 11:30, 12:30, 13:30, 14:30, on a day whose G_SUM (D688's SPX GEX plus
  the ES options book at the prior settlement, known before the open) is below zero.
- **What:** hold sign(m) for 60 minutes, where m is the move over the last 60 minutes.
- **The primary cell:** h = 60, k = 0 (every decision with m ≠ 0). Secondary cells: h = 30, and k = 0.5.

## 2. V — the volatility control (the principal's condition)

| cell | raw gross, bp: short / long | V1: same-day RV strata, short − long (p50 / p95, percentile) | V2: trailing-σ strata (percentile) | V3: regression, bp (t) |
|---|---|---|---|---|
| **h60 k0 (primary)** | **+2.12 / +0.12** | **+1.48** (−0.03 / +1.00, **0.985**) | +1.83 (0.996) | +2.13 (2.67) |
| h60 k0.5 | +2.60 / +0.06 | +0.93 (−0.04 / +1.63, 0.826) | +2.39 (0.987) | +2.81 (2.36) |
| h30 k0 | +0.62 / −0.20 | +1.04 (−0.02 / +0.54, 1.000) | +1.02 (0.999) | +1.16 (2.97) |
| h30 k0.5 | +0.53 / −0.03 | +1.34 (−0.02 / +0.84, 0.996) | +0.91 (0.949) | +1.44 (2.26) |

**Within the same-day volatility deciles** (h60 k0), mean g in bp, short / long:

| decile | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| short / long | +2.0 / +0.5 | −1.4 / −0.3 | +1.3 / +0.1 | +3.5 / +0.5 | +0.9 / −1.2 | +0.6 / +0.4 | +3.2 / −0.1 | +3.7 / +0.2 | +3.7 / +0.1 | +0.2 / +2.5 |

- Short-gamma rows exceed long-gamma rows in 8 of the 10 deciles.
- **The exception is the most volatile decile** (731 short rows), where long-gamma days continue more.
- **The effect lives in ordinary-to-high volatility, not at the extreme.** That is the opposite of a crash artefact.

## 3. C — concentration (h60 k0, gross per MES trade, day-clustered t)

| sample | mean $ | t | n |
|---|---:|---:|---:|
| all short-gamma trades | +3.77 | 2.93 | 2,988 |
| without 2020-02-20 → 04-30 | +4.06 | 3.24 | — |
| without 2020 | +4.01 | — | — |
| without 2022 | +3.76 | 3.02 | — |
| without the top 1% of \|trades\| | +3.56 | 3.05 | 2,957 |

**By year:** 2016 +2.4 (n 276), 2017 +0.1 (152), 2018 +3.4 (478), 2019 +1.9 (342), 2020 +0.9 (228), 2021 +5.5 (204),
2022 +3.8 (790), 2023 +7.7 (518). **Positive in 8 of 8.** The largest trades are all 2022; the biggest is 2022-01-26
at −$429.

## 4. B — the books and the four groups (h60 k0)

| book | trades/yr | net Sharpe (Sortino) | gross Sharpe (Sortino) | mean net/trade | median | hit (net) | max DD | ρ with the arm |
|---|---:|---|---|---:|---:|---:|---:|---:|
| **unfiltered, 1 full ES ($19.24)** | 379 | **+0.51 (+0.75)** | +1.04 (+1.59) | +$18.47 | +$18.26 | 51.8% | $15,412 | −0.046 |
| unfiltered, 1 MES ($4.42) | 379 | −0.18 (−0.25) | +1.04 (+1.59) | −$0.65 | −$0.67 | 49.3% | $5,911 | −0.048 |
| EP-filtered, full ES | 10 | −0.39 (−0.49) | −0.31 (−0.40) | −$90.96 | −$19.24 | 47.4% | $13,517 | −0.046 |
| EP-filtered, MES | 0.5 | — (4 trades) | | | | | | |

**Performance.**
- **Gross:** $37.72 an ES trade, which is 0.98 × 2c. The breakeven round trip is $37.72 at ES and $3.77 at MES.
- **Size and risk:** annual net vol at 1 ES is $13,681, and the maximum drawdown is $15,412.
- **Cost:** it clears the full-ES round trip roughly twice over, and does not clear the micro one.

**Trade distribution (full ES, net).**
- n 2,988; mean +$18.47 ≈ median +$18.26; win rate 51.8%; payoff 1.01; skew +0.08; kurtosis 7.4.
- Trimming 1%: ex-top −$8.21; ex-bottom +$44.14; both tails +$17.45.
- **Symmetric trimming leaves it intact,** and the median carries it. Dropping only the winners flips the sign, which on
  a two-sided fat-tailed book is a flag, not a verdict (CLAUDE.md).

**Dependence.**
- **Longs +$56,534, shorts −$1,337.**
- **By year (net, full ES):** 2016 +1.4k, 2017 −2.7k, 2018 +6.8k, 2019 0, 2020 −2.3k, 2021 +7.3k, 2022 +14.9k,
  2023 +29.8k. **2022–23 hold 81% of the net.**
- The top 10 trades are 63% of the net.

**The expected-profit filter failed.** Its declared projection, π·|m| (a pass-through proportional to the size of the
last hour), selects the largest moves, and those do not continue: −$91 a trade. The continuation lives in the sign, not
in the magnitude. D684 S1's weak linear slopes against its strong sign-trade already showed this. A filter for this
object would have to project a per-trade constant by regime, not scale with |m|. That is a design point for any
pre-registration, not something this record may tune.

**Nulls:** §2's V1 and V2 are the enumerated rotation nulls (p50 and p95 given, SE 0).

## 5. Two caveats the declared statistics do not settle

1. **Half of the per-trade profit is drift, not continuation.**
   - Longs earn and shorts are flat. With E[f | m > 0] = μ + c and E[f | m < 0] = μ − c, that means μ ≈ c: on
     short-gamma days the next hour drifts UP by about as much as the continuation.
   - The pure continuation is about half the per-side figure. The rest is a long bias on short-gamma days, which are
     mostly post-selloff days. An in-sample window that was largely a bull market rewards that.
   - An always-long-on-short-gamma-days control (CLAUDE.md's always-on control) was not declared and has not been run.
2. **The confirmation population differs.**
   - In 2016–23 the short-gamma days were a mix of SPX-short and ES-book-short days (SPX short 12.5%, ES book 43%).
   - The 66 short-gamma days of 2024-01 → 2025-02 are almost all ES-book-driven: SPX GEX was short on one day, and the
     ES book on 101.
   - Whether the effect lives on ES-book-only short days (SPX long) in-sample was not declared and has not been run. If
     it does not, the clean slice tests a different object.

## 6. P — the confirmation premise (conditioner only)

**2024-01-02 → 2025-02-28:** 300 sessions, 288 with both books.
- **Short-gamma sessions:** G_SUM **66**, SPX **1**, ES book **101**.
- **By month:** 1, 1, 0, 9, 5, 0, 7, 8, 6, 6, 4, 5, 7, 7.
- **What was read:** SqueezeMetrics GEX, ES options OI and settlements, and ES settlements, from 2023-11 to
  2025-02-28. No ES bar, intraday price or return was read, and nothing from 2025-03-01 on.

**Power:**
- 66 days × 4.96 trades a day gives 327 expected trades.
- The in-sample mean without the crash is $4.06 a MES trade, with a per-trade sd of $65.40.
- **The expected t is 1.12** (unclustered, so optimistic), under the power rule's 1.5.
- **With the vault** (joint run only; its G_SUM count cannot be read without reading vault prices), a similar short
  share would give roughly 1.7. That is an estimate, not a count.

## 7. What this decides, for the principal

- **Declared outcome: UNCONFIRMABLE ON THE CLEAN SLICE.** A standalone confirmation on 2024-01 → 2025-02 would spend
  the slice at a power of about 1.1, and the power rule forbids that.
- **What it is, in-sample.** This is the first gamma construction with direction in it that survives:
  - a volatility-matched control;
  - an enumerated null;
  - removal of the crash;
  - a year count.

  The mechanism is D683/D684's: short-gamma dealers hedge with the move, and the damping that long gamma supplies is
  absent.
- **As a component** it is a full-ES book: net Sharpe 0.51 at ρ −0.05 with the arm, but a $15k drawdown and $13.7k
  annual vol per contract. That is the prop account's size problem ("one micro has grown into the prop barrier"). At
  MES size it is a zero.

**Options, the principal's call:**
1. **Two cheap in-sample checks first** (§5):
   - an always-long-on-short-gamma-days control, to separate drift from continuation;
   - the effect on ES-book-only short days, the population the confirmation would test.
2. **If both hold, a pre-registration for the joint vault run.** The frozen rule would be tested on 2024-01 → 2025-02
   plus the vault together, where the power estimate is about 1.7. It would need a programme slot; slots 7 and 10 are
   free.
3. **Or park it:** mechanism-level evidence and a size note for the expected-profit filter.
