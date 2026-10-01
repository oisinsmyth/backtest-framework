# D743 STAGE 0 RESULT — NOT SUPPORTED, all six: skipping busy nights and release days does not select D735's trades, and on EQ k1.5 it removes the better ones

*2026-10-01.*
- *Spec:* [D743-STAGE-0-PRE-REG](D743-STAGE-0-PRE-REG-skip-busy-nights-and-release-days-on-d735.md), committed
  before its runner (21e0fe29).
- *Runner:* `scripts/stage0_d743_skip_layer.py` (`--selftest` passed; `--run` once, 0.7 min).
- *Output:* `data/stage0_d743_skip_layer.json`.
- *In-sample only:* nothing dated 2024-01-01 or later was read.

## 0. Checks

**Known answers:**
- YM k1.0 1σ_rem through D737's own `cell` and `check_known`: 1,699 trades, mean net D735's to 1e-9;
- EQ k1.5 1σ_rem through D735's functions: 1,131 trades, +\$18.1118766142761 to 1e-9.

**Audits, all passed:**
- **Lag:**
  - the overnight canary (a 09:30 bar included) fired;
  - p_on matched a loop re-implementation on 40 sessions;
  - D671's `tier_audit` raised on the leaky tiers.
- **Join:** 50 days matched a direct lookup, and the shifted join raised.
- **Sign:** 40 sampled trades per cell re-derived by D735's `e1_loop` to 1e-9; a rising day pays long + and short −.
- **Right quantity** and **the rotation's offset 0**: both passed.

**The window:** 2016-12-30 → 2023-12-29, once p_on has its 250 earlier sessions.
- YM k1.0 loses 182 burn-in trades and keeps 1,517.
- EQ k1.5 starts no earlier, so all of its 1,131 trades are in the window.
- 181 release sessions are in the panel.

## 1. The oracle, first

| cell | take-all | O1: keep the winners | O2 same-size ceiling: V1 / V2 / V3 |
|---|---:|---:|---:|
| YM k1.0 | 1,517 trades, \$24,895 | 769, \$125,025 | +\$94,439 / +\$47,483 / +\$97,904 |
| EQ k1.5 | 1,131, \$20,485 | 575, \$101,204 | +\$75,535 / +\$36,567 / +\$78,882 |

**Every veto's capture of its same-size ceiling is negative:** −0.07 to −0.17. Each veto costs money that a perfect
skip of the same size would have made.

## 2. The six tests

Kept against skipped, mean net per MNQ. "Rot" is the S2 efficiency's exact-rotation p with its null p50 / p95; "wy"
is the within-year p.

| cell · veto | skipped | kept / skipped \$ | kept S2 · rot p (p50 / p95) | Holm | wy p | kept Sharpe vs all | maxDD vs all | reading |
|---|---:|---:|---|---:|---:|---|---|---|
| YM · V1 busy night | 34 % | 18.15 / 12.98 | .154 · .258 (.138 / .179) | 1.00 | .232 | 1.07 vs 1.16 | 2,613 vs 2,690 | NOT SUPPORTED |
| YM · V2 release | 10 % | 15.73 / **22.86** | .133 · .668 (.138 / .157) | 1.00 | .652 | 1.05 vs 1.16 | 2,540 vs 2,690 | NOT SUPPORTED |
| YM · V3 either | 39 % | 18.00 / 13.98 | .151 · .330 (.138 / .183) | 1.00 | .293 | 1.00 vs 1.16 | 2,511 vs 2,690 | NOT SUPPORTED |
| EQ · V1 busy night | 34 % | 11.95 / **30.00** | .106 · .856 (.138 / .185) | 1.00 | .849 | 0.59 vs 1.03 | 4,946 vs 4,747 | NOT SUPPORTED |
| EQ · V2 release | 10 % | 15.55 / **42.38** | .123 · .873 (.138 / .160) | 1.00 | .873 | 0.85 vs 1.03 | 4,747 vs 4,747 | NOT SUPPORTED |
| EQ · V3 either | 40 % | 11.05 / **28.72** | .098 · .878 (.137 / .192) | 1.00 | .868 | 0.51 vs 1.03 | 4,789 vs 4,747 | NOT SUPPORTED |

**Every condition fails in every row except the standard.**
- **Condition 1 (selection):** no raw p is below 0.25.
- **Condition 2 (the skipped trades do not earn):** the skipped trades earn \$3,314 to \$12,982 in every row.
- **Condition 3 (a better book):** the kept Sharpe is lower in all six.
- **Condition 4 (D736's standard):** the kept books still meet it, except YM · V2 (INTERMITTENT), because the cells
  themselves are strong.

**The pre-registered PICKS YEARS label fires on all six,** because the within-year p is above 0.10 wherever the
selection itself is absent. Here it carries no information.

**Two dimensions are the same picture.**
- **σ-normalised (S3, kept − skipped mean y):** −0.011 / −0.069 / −0.028 on YM and −0.055 / −0.119 / −0.068 on EQ.
- **The minimum detectable difference in mean net** is \$31–64 against observed differences of −\$27 to +\$5. The
  null is not "no power": the point estimates on EQ sit on the wrong side.

## 3. The four groups (take-all against the V3 kept book; the other rows are in the JSON)

| | YM all | YM kept V3 | EQ all | EQ kept V3 |
|---|---:|---:|---:|---:|
| total net / gross Sharpe | 1.16 / 1.45 | 1.00 / 1.22 | 1.03 / 1.27 | 0.51 / 0.70 |
| net Sortino | 1.95 | 1.71 | 1.77 | 0.84 |
| share of sessions | 0.885 | 0.53 | 0.659 | 0.40 |
| mean net / median / win | 16.41 / 1.93 / .51 | 18.00 / −3.57 / .49 | 18.11 / 1.93 / .51 | 11.05 / −1.57 / .49 |
| trimmed both / ex-top / ex-bottom | 13.24 / 7.90 / 21.78 | 14.49 / 9.23 / 23.29 | 14.43 / 9.26 / 23.32 | 7.28 / 2.62 / 15.75 |
| skew / mean gross ÷ 2c | 0.87 / 2.52 | 0.99 / 2.71 | 0.95 / 2.73 | 0.97 / 1.86 |
| max drawdown / Calmar | \$2,690 / 1.36 | \$2,511 / 0.97 | \$4,747 / 0.63 | \$4,789 / 0.23 |
| ex-two-best-years per year (D736) | \$1,308, EARNS | \$777, EARNS | \$1,713, EARNS | \$564, EARNS |

**The top trade** in both cells is 2022-02-24 (+\$1,248), the day Russia invaded Ukraine: a busy night.

**The component line:** a kept book is a gated subset of its cell, so it is the same component.
- ρ with D737's in-sample twin: 0.77–0.96 (YM), 0.54–0.68 (EQ).
- ρ with NQ F2: 0.00–0.06.

## 4. Predictions against the outcome

**Opus:**
- P(any SUPPORTED) ≈ 0.2: none.
- "V2 skips about 10 %": 9.5–9.6 % ✓.
- "V1 skips fewer than a third": 34 % ✗ — D735 trades busy nights in proportion.
- "If anything passes, V2 on EQ": ✗. **It is the most adverse row**: release-day trades earn \$42 against \$16.

**The Fable agent's** +2–4 bp a kept trade was for the range breaks the idea came from. On D735's legs the sign is
reversed on EQ and absent on YM.

## 5. Reading

**NOT SUPPORTED on all six. D735's legs have no skip layer in these two vetoes, and D737 stays exactly as frozen.**

**Why it did not transfer** (POST HOC, an interpretation):
- The veto's mechanism belonged to its construction. For a crossing of a fixed level (yesterday's extreme), a night or
  an 08:30 print that has already priced the news leaves the 09:30 crossing as the tail of a spent move.
- D735 trades something else: NQ moving *against the market* at 10:00. On a news day the whole market reprices, and
  NQ's divergence from it is, if anything, *more* informative. On EQ k1.5 the skipped trades earn \$29–42 against
  \$11–16; reversed, the S2 rotation p is about 0.13, so this is not a finding either way.
- It is the same lesson as [D739](D739-STAGE-0-RESULT-the-group-break-is-nq-only.md), seen from the
  other side: a mechanism travels with its construction, not with its market.

**Kept:**
- The C1 diagnostic's vetoes remain a description of NQ's range breaks (post hoc, the data they were found on). They
  are not a general "spent information" filter.
- **Not a lead:** "D735 earns more on news days" is the reverse of a declared hypothesis, at p ≈ 0.13, after the
  fact. It is recorded and not pursued.

## 6. CLOSED

*2026-10-01, the principal: "Ok close that and look at idea 2".*
- **The line is closed:** no skip layer on D735's legs, and D737 is unchanged.
- **Don't re-propose** the overnight or release-day skip for D735 or D737.
- **Next:** idea 2 of the C1 comparison (the post-shock consolidation break at the European open), designed with the
  principal under its own number.
