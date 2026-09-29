# D686 PRE-REGISTRATION (DEVELOPMENT) — thirteen profit projections, overlays and lags on D685's month-end mechanism, scored as one family against a best-of-13 null

*Renumbered from D678 to D686 on 2026-09-29 before this branch (`wt/after-d674`) merged main, which holds a different D678. Commit messages and the recorded outputs in `data/` keep the old number.*

*Drafted 2026-09-29 on the principal's word. The principal asked "I think we can examine some other profit projection
mechanisms for this and test on in-sample?", then asked for combinations of the projections ("I meant a combination of
the P's but maybe those are good too?"), then said "Ok now lets write, build and run those 13". Committed alone,
before its runner exists (R8).*

**DEVELOPMENT, NOT EVIDENCE.** D685 has already read this window, so any variant chosen here is a hypothesis until it
is confirmed on unread data. The family null guards the selection inside this record. It cannot stand in for data this
record has not read.

## 0. What it asks

**D685's verdict was MECHANISM ONLY.**
- **Gate 1 passed:** the lagged 60/40 drift predicts ES over the last five trading days at −14.06 bp per 1-SD,
  NW t −3.22.
- **Gate 2 failed:** the expected-profit-filtered MES book netted $4.06 per active day at t 1.04.
- **The failure was noise and fade, not cost**, and the sign book lost money in each of 2019–2022.

**This record asks two questions:**
1. Do month-ends whose flow **the mechanism** says should hit harder carry more of the edge, so that a projection
   built from it concentrates the book? Or do overlays and entry timing reduce the noise?
2. **Does the square-root impact law explain the fade?** If ES liquidity grew faster than the rebalancing flow, the law
   predicts smaller impact after 2018.

## 1. The base, imported unchanged from D685

The runner imports D685's `load`, `drift_signal`, `month_blocks`, `outcome_days`, `cost_spec` and statistics from
`scripts/stage0_d685_month_end_rebalancing.py`:
- same-contract ES and ZN settlement returns on the common grid;
- the within-month 60/40 drift s;
- the lagged position −sign(s(o−2)) over the last five trading days;
- MES at $4.42 a round trip;
- the window 2010-07 → 2023-12;
- nothing on or after 2024-01-01.

**Its definitions:**
- **Book gross per active day:** `g(o) = −sign(s(o−2)) · y(o)`, where y is ES's same-contract return in bp.
- **z:** `s / σ_s`, with σ_s taken over the prior 36 months (at least 12).
- **Costs:** half a round trip per contract changed. A run's exit is charged to its last active day.

## 2. The thirteen variants

### Projections (P0–P7): filters on the base

Each builds a size predictor X ≥ 0 known at entry (the settlement of o−1), and one or more pass-throughs.
- **The pass-through π:** a through-origin regression of g on X over the active days of months **strictly before**
  o's month. It needs a 24-month burn-in with finite X; where π is by group, each group needs at least 20 prior
  observations.
- **The projected gross:** `G = π·X` bp, or in dollars `G/1e4 × $5 × S_{o−1}`.
- **The trade:** take the base position on day o only when π > 0 and G ≥ 2 × the MES round-trip cost. Otherwise
  stay flat.

| # | X, and the pass-through | the mechanism |
|---|---|---|
| **P0** | \|z\|; one π | D685's own projection, in this uniform through-origin form (D685's slope-on-z form is reported beside) |
| **P1** | **σ20 · √(\|s\| · S / DV60)**; one π | **The square-root law.** Impact ∝ σ√(Q/V). The flow Q ∝ \|drift\| × the equity value that rebalances (∝ the index level S), against the liquidity V it lands in. |
| **P2** | \|z\|; π by {quarter-end month, other} | Quarterly rebalancers add to the monthly ones. |
| **P3** | \|z\| · 1[\|s\| ≥ 0.01]; one π, fitted on the threshold days | Threshold rebalancers trade only once drift passes a band (the paper's 0–2%, midpoint 1%). |
| **P4** | \|z\|; π by GEX regime {SHORT: GEX < 0, LONG: ≥ 0}. A day with no GEX row does not trade. | Short-gamma hedging amplifies the flow's impact. |
| **P5** | \|z\|; π by position in the window (days 1–5) | The flow may land on particular days. |
| **P6** | **structural:** X1 · m_Q · m_T · m_G, then one π | The whole mechanism at once. Each m is a ratio of prior-only pass-throughs on X1, the group against its complement: quarter-end, \|s\| ≥ 0.01, and SHORT gamma. m = 1 off-group, or when a group has fewer than 20 prior observations or the denominator π ≤ 0. Each is clipped to [0, 5]. |
| **P7** | **blend:** the mean of the available projected grosses G1–G5 (in $), with no weights fitted. A P3 day below its threshold counts as 0; a P4 day without GEX is excluded from the mean. | The agnostic check on P6. |

**The P1 inputs, all known at the settlement of o−1 and all taken through o−2:**
- **σ20:** the standard deviation of ES same-contract daily returns over the 20 trading days through o−2.
- **S:** ES's settlement at o−2.
- **DV60:** the median ES day-session contract volume (breadth hourly `h09_v … h16_v` summed) over the 60 trading
  days through o−2, needing at least 10 days with volume. Before 2013 ES day-session volume is sparse (33, 73 and 113
  sessions in 2010, 2011 and 2012), so P1 and P6 stand aside where DV60 cannot be formed. The coverage is reported.

**GEX:** the SqueezeMetrics row dated strictly before o−1 (2011-05 onward; licence: aggregates only are written).

### Overlays (O1–O3): on the unfiltered base

| # | overlay | why |
|---|---|---|
| **O1** | **Volatility-scaled size:** position −sign(s) × min(3, σ̄/σ20). σ̄ is the median of σ20 over the prior 252 trading days. Contracts are continuous (the large-account approximation); cost is proportional to the change in position. | Standard risk control on a book whose noise swings with regime. |
| **O2** | **Stand aside** on outcome days that are FOMC, CPI or Employment Situation release days (the D585 calendar via `cme_session_calendar`'s flags). The calendar exists only from 2016, so before 2016 the overlay changes nothing (disclosed). | The flow is the same size on those days, and the noise is larger. |
| **O3** | **Hold into the next month:** keep the month's last position over the first 10 trading days of the next month. | **Post hoc.** It comes from D685's in-sample continuation (−49 bp, t −1.97). Development only. |

### Lags (L1–L2)

| # | timing | why |
|---|---|---|
| **L1** | **The near-close signal.** The position for o is −sign(s′(o−1)). s′ takes ES's month-to-date return through **15:45 ET on o−1** (the close of `fut_day1m` bar 404 on the contract held, relative to that contract's settlement at o−2) and ZN's through its 15:00 settlement on o−1. Entry is at the settlement of o−1. **2016-01 → 2023-12 only:** ES's first clean 1-minute year is 2016. | The paper's unlagged form was stronger (−15.4 against −14.1), and this version stays executable. |
| **L2** | **The longer window:** outcome days are the last 10 trading days, with the lag-2 signal. | Front-runners may act earlier. |

**L1's 15:45 prices** come from `scripts/build_d686_es_1545.py`, run under the system Python, which has pyarrow; the
runner's venv does not. It writes a gitignored `data/d686_es_1545.csv.gz`, and its SHA-256 is recorded in the output.
For comparison, the base is also scored on L1's 2016–2023 window.

## 3. Statistics, nulls and the development gate

**For every variant, at MES (full ES reported beside):**
- **A_v, the net Sharpe:** daily net $ over every trading day in its window, zero when flat, × √252.
- **B_v:** the NW t (lag 4) of the net per active day. Active days are the base's window days: 5 a month; 10 for L2;
  15 for O3, counting its hold days. A day the variant stands aside counts as zero.
- **The traded-day count.**

**The null (enumerated, exact).** For each offset k = 2 … M−2, the **signal side** is rotated by k months against the
**time side**.
- **The signal side:** s, z, and everything computed from them.
- **The time side:** returns, σ20, DV60, S, GEX, the calendar flags, quarter-end, and the position in the window.
- **Every prior-only estimate** (σ_s, π, the m ratios, σ̄) **is recomputed inside each rotation.**
- **Scale:** M = 162 gives 159 offsets; L1 has M = 96, so 93.

**Reported for each variant:** A_v's own-null p50, p95 and percentile. **The family null** is the maximum over the 13
variants of A_v(k), each on its own window, at each k.

**The development gate, per variant.** **D-PASS** requires all three:
- A_v above its own null's p95;
- B_v ≥ 2.0;
- at least 60 traded days.

**The family gate:** the best variant's A_v above the p95 of the best-of-13 null. **A variant that passes its own
null but not the family's is noted as selection-exposed.**

**Power for confirmation (reported for every D-PASS variant):** the expected t on 2024-01 → 2025-02 is
`B_v × √(14 / months in window)`, and with the joint-run vault `× √(32.5 / months)`.

**The fade question (P1).**
- **The measure:** the yearly mean of P1's signal-free impact factor `F = σ20·√(S/DV60)` over active days, against
  the yearly realised base gross per unit |z|, as Spearman ρ over the years with both (2011–2023).
- **"P1 explains the fade"** requires both:
  - ρ ≥ +0.5;
  - F's 2020–23 mean below its 2013–15 mean. The first years with dense volume are 2013 onward.

## 4. Reported beside

- **The four CLAUDE.md groups:** for the best variant, and for every D-PASS variant.
- **Correlation with the MACD arm:** daily net, 2016–2023.
- **The base:** D685's unfiltered and filtered books, recomputed as the reference.
- **Per-year net** for every variant.

## 5. Predictions (mine, before the run)

1. **No variant clears the best-of-13 family null.** The selection gains available in a thin edge are small.
2. **P1's impact factor F falls from 2013–15 to 2020–23**, but its yearly Spearman with the realised edge is below
   0.5: it explains part of the fade, not all.
3. **O1 has the highest net Sharpe of the three overlays.**
4. **O3 raises the net Sharpe in-sample,** because it is built from this sample's own continuation.
5. **L1's net Sharpe exceeds the base's** on the shared 2016–2023 window.
6. **P6's net Sharpe is at least P7's.**
7. **Every D-PASS variant has an expected clean-slice t below 1.5,** so none is confirmable on 2024-01 → 2025-02 alone.

## 6. Runner assertions and self-test

1. **Base reproduction:** the unfiltered book's gross per active day equals D685's (+7.17 bp) exactly. The B1 slope
   reproduces −14.06.
2. **Prior-only audit:** every π and m used in month m is recomputed by an explicit loop over months strictly before m.
   It must agree to 1e-12. The self-test shows it fires on a π that includes month m.
3. **Rotation identity:** k = 0 reproduces every variant's observed A_v bit for bit.
4. **Window guard:** nothing on or after 2024-01-01, including in the 15:45 extract.
5. **The sign audit in money,** inherited from D685.
6. **L1 causality:** the 15:45 price is strictly before the settlement. The self-test shows it fires on bar 405 or
   later.

**Each audit is shown to fire on a broken input.**

**Output:** `data/d686_month_end_variants.json`, from `scripts/stage0_d686_month_end_variants.py`. **Projected wall
time:** a few minutes (13 variants × about 160 rotations with prior-only refits, vectorised over months).
