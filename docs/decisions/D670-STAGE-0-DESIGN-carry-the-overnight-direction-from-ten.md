# D670 STAGE 0 DESIGN — the MACD arm's mechanism built directly: carry the direction of the move since yesterday's close from 10:00 to the close, with an expected-profit forecast made at 10:00; the evidence on YM and RTY, which have never seen the rule

*Drafted 2026-09-29.*
- *The principal: "Can we reshape it to aim at exactly the underlying mechanism?", then "Ok go for the Stage 0
  Pre-Reg".*
- *It follows D669, which named the mechanism on NQ in sample.*
- *Committed alone, before any runner exists (R8). **No outcome of this rule has been computed on any root.** D669
  measured the sign on the arm's own windows and as a free-running hourly book on NQ, 2016–2023. Nothing here has
  been run on ES, YM or RTY, or on the one-minute fixture.*

## 1. Why this, and what is already known

**What D669 found on NQ, 2016–2023, for the admitted MACD arm:**
- **The direction.** The arm's direction is, on 76 % of trades, the sign of the move from the prior 16:00 close to the
  decision. That sign on the arm's own windows earns 92 % of its gross. Where the MACD departs from it, it earns
  nothing measurable (t 0.23).
- **Where it earns.** On days that trend efficiently from 10:00 to 16:00. The top fifth of days by move carries 114 %
  of the gross (efficiency t 6.6, volatility t 0.6). It is wrong more often than a coin on quiet days.
- **The 15:00 exit.** A quarter of trades exit at 15:00 when the signal has turned, skipping a last hour that would have
  lost $4,455 (t −2.1). That is consistent with D581/D640: the close continues its prior hour.
- **The arm itself was selected.** Its median neighbour scores 0.24 net, and its deflated Sharpe fails. So the
  mechanism, not the arm, is what is worth building.

**What counts against it:**

| known | what this design does |
|---|---|
| found on NQ, and NQ's 2024+ is spent (D503); NQ's 2016–2023 is where it was found | **NQ and ES are development only, with no verdict. The evidence is YM and RTY**, which have never seen this rule |
| the arm was signal-dead on YM: gross negative (D513) | YM is kept as an evidence root. It is the hardest test that the mechanism is not NQ's alone (prediction 2) |
| nothing before the open sees a trend day (D647: AUC 0.506) | the forecast is made at **10:00**, with the first half hour known. Whether that sees anything is P2's question, and the oracle is measured first |
| volatile days that chop are the arm's worst cell (D669 §4), so a size filter can select both the best and the worst days | P2's target is the **trade's profit**, not the size of the move. Its value must show as discrimination (β_disc) |
| the first half hour reverses into the last on ES (D487) | the halves of the direction (overnight gap alone, first half hour alone) are reported beside it on every root |
| the other session's plain-break design (unmerged, on its branch `wt/after-d643`) takes a direction from a break of yesterday's range and uses YM and RTY as its evidence | a separate line with a different direction rule. Both read the same in-sample fixture per line. Its correlation with that break is named as missing until both are merged (§6) |

## 2. The rule (P1)

**Per root r ∈ {YM, RTY} (evidence) and {ES, NQ} (development).** The day session, from D462's one-minute
`fut_{r}_rth_1m` (09:30–15:59 ET, front month by full-day volume, no stitching). The session table is
`fut_index_sessions`.

- **The direction:** D = sign(C₀₉:₅₉ − C′₁₅:₅₉), where C′₁₅:₅₉ is the prior session's last close. This is the move since
  yesterday's close: overnight plus the first half hour of the cash session. D = 0 is no trade.
- **Entry:** at the open of the 10:00 bar.
- **Exit, primary (P1):** at the close of the 15:59 bar.
- **Sessions dropped, declared:**
  - a session whose contract differs from the prior session's (a roll): its direction would carry the calendar
    spread;
  - the three circuit-breaker sessions of March 2020 (09, 12, 16), which have no continuous open;
  - any session missing its 09:59, 10:00 or 15:59 bar, or its prior session's 15:59 bar.
- **The windows (in sample; the vault from 2025-03-01 is sealed):**
  - ES, NQ and YM: 2016-01-04 → 2025-02-28;
  - RTY: 2017-07-10 → 2025-02-28.
- **Cost:** the micro round trip in dollars from `data/futures_costs.json`'s default line (`d508_exec`), computed by the
  runner: $3 commission plus the effective crossing (MES 1.135, MNQ 2.134, MYM 1.594, M2K 1.514 ticks). That is about
  $4.42, $4.07, $3.80 and $3.76. It is expressed in bp of the entry notional per trade. The micros launched in May
  2019; the same micro cost is applied before that, as in every opening study.
- **The trade's gross** is g = D × (C₁₅:₅₉ − O₁₀:₀₀) / O₁₀:₀₀ in bp, and in dollars at one micro.

**Reported beside the rule on every root, not gated:**
- **the halves:** D_gap = sign(O₀₉:₃₀ − C′₁₅:₅₉) and D_open = sign(C₀₉:₅₉ − O₀₉:₃₀), each on the same windows;
- **C0:** long in every window;
- **long against short.**

## 3. The controls for P1

**N1, the direction permutation within ISO week** (D669's finest stratum). D is permuted among the root's traded
sessions of the same ISO week. Every window, the week's long count and the cost stay the same; only the pairing of a
direction with its own session's move is broken.
- 10,000 draws, seed 670.
- Statistic: mean gross per trade.
- Reported: p50, p95, the p95's bootstrap SE (1,000 resamples), and the percentile.
- **N1-month** (the same, within calendar month) is reported beside it.

**The exact drift carry** of each stratum (Σ over strata of n × mean D × mean move) is printed. The runner asserts
the draw mean lies within 3 SE of it.

## 4. Can the profit be forecast at 10:00? (P2)

**P2a, the prize, before any model.**
- **The oracle:** the rule's gross on the sessions in the top two-fifths of realised |10:00 → 16:00 move| (within
  root), and on the top two-fifths of realised efficiency (|Σ r| / Σ |r| over the twelve 30-minute returns from 10:00).
- **The attainable bound:** the mean gross that a filter keeping 40 % of sessions would earn at a rank correlation of
  0.1, 0.2 and 0.3 with the realised trade gross. This is computed by ranking on a noisy copy of the realised gross,
  200 draws per level.

These are measurements, not bars.

**P2b, the walk-forward expected-profit forecast** (the programme's D649 template, and the other session's plain-break form).

The features, each known at 10:00 and, where directional, signed by D. The list is capped at seven:

| # | feature | definition | why |
|---|---|---|---|
| f1 | size of the move | \|C₀₉:₅₉ / C′₁₅:₅₉ − 1\| / A | a larger accepted move |
| f2 | agreement | 1 if D_gap = D_open | the open followed through on the overnight move (an opening drive) |
| f3 | opening range | (H − L over 09:30–09:59) / (A × C′₁₅:₅₉) | an early range expansion |
| f4 | opening efficiency | \|C₀₉:₅₉ − O₀₉:₃₀\| / (H − L over 09:30–09:59) | a first half hour that went one way |
| f5 | dealer gamma | 1 if SPX GEX < 0, from the row dated before the session (SqueezeMetrics), for all four roots | the other session's gamma diagnostic (`wt/after-d643`): short gamma predicts a bigger move, never its sign |
| f6 | trailing volatility | the standard deviation of the root's 10:00 → 16:00 returns over the prior 20 sessions, in bp | the size term |
| f7 | side | 1 if long | **the drift term**, declared. N1 absorbs it; the model may use it |

A is the mean of the prior 20 sessions' RTH (high − low) / close.

**The target:** the trade's gross in bp.

**The model:**
- OLS with an intercept on f1–f7 (standardisation does not change an OLS forecast, so none is applied);
- fitted per root on **every earlier session only**, refitted before each session;
- no tuning, no selection and no penalty;
- burn-in: the first **250 sessions** are fitting only.

**The pass-through and the filter** (the plain-break design's rule):
- **projected_i = π̂_i × ŷ_i**, where π̂_i is the through-origin slope of realised gross on ŷ over **all earlier
  forecasts**. It needs a burn-in of 40 forecasts; until then π̂ = 0 and nothing passes.
- **Trade when projected_i ≥ 2 × cost_i** (k = 2).

**Discrimination, β_disc:** the out-of-sample slope, with an intercept, of realised gross on ŷ over every forecast
session, with Newey-West t (5 lags).

**N2, the permuted-feature forecast:**
- the same pipeline with the feature rows shuffled across sessions within each year (targets fixed);
- 200 draws;
- the null for β_disc's t and for the filtered net.

**Reported beside it:**
- the correlation of ŷ with the realised |move| and with the realised efficiency, which says whether the forecast
  sees size, trend, or neither;
- the filter's pass rate and π̂'s path;
- the net of the sessions the filter removes;
- each coefficient's walk-forward path.

**The margin-hike flag (D657) is not a feature.** D657's table has no RTY, and NQ, YM and ES have holes from late
2016/2017 to mid-2020. It is reported as a diagnostic only (the rule's mean gross in the ten sessions after an
increase, where covered).

## 5. The 15:00 rule (P3)

- **P3's exit:** on each P1 trade, exit at the **open of the 15:00 bar** if the last completed hour moved against D:
  D × (C₁₄:₅₉ − C₁₃:₅₉) < 0. Otherwise hold to the 15:59 close.
- One round trip either way, so the cost is unchanged.
- **Statistic:** the paired difference (P3 gross − P1 gross) per trade, with Newey-West t (5 lags).
- **Secondary, reported:** exit at 15:00 if the trade is under water since entry.

## 6. The gates and what is reported

**Gate 1, the MECHANISM (P1, unfiltered, gross), per evidence root:**
- the mean gross per trade, one-sided Newey-West t, **Holm across YM and RTY**;
- **above N1-week's p95 by more than 2 bootstrap SE** (within 2 SE is UNRESOLVED);
- positive without February–April 2020.

**Gate 2, TRADEABILITY (P2, filtered, net), on a root that passed Gate 1:**
- the filtered book's net per trade at one micro, one-sided, Holm across the roots at Gate 2;
- **β_disc > 0 with t ≥ 2, and above N2's p95**;
- at least 30 filtered trades after both burn-ins, else UNRESOLVED;
- the filtered net stays > 0 at **+1 extra tick on each fill**.

**Gate 3, the EXIT (P3), per evidence root:** the paired difference > 0 with t ≥ 2, Holm across YM and RTY.

**The four groups, per root, for the unfiltered rule, the filtered book and the P3 variant:**
- net and gross side by side; Sharpe and Sortino, annualised by the book's own trades a year; exposure, σ, maxDD;
  breakeven cost; the mean move per trade against 2c;
- the trade distribution: count, mean, median, win rate, payoff, skew, kurtosis, and the three 1 %-trimmed means;
- what the winners depend on: by year, long against short, the halves, before and after 2022-05-16 (the 0DTE era),
  sessions to half the P&L, and the top trade named;
- the nulls as distributions: N1's and N2's p50 and p95, with SE, beside every score.

**The component line** (CLAUDE.md), computed by the runner, per root:
- daily $ net Sharpe at one micro, hit rate, skew, gross beside net;
- ρ with **K8** (rebuilt from the NQ session table, as the plain-break design's amendment does);
- ρ with **the MACD arm** (D508's `load_arm`, on the overlap 2016–2023);
- ρ with each other root's rule.
- **The plain-break book is named as missing** until both lines are merged.

**Power, before the run.** Assuming σ of the 10:00 → 16:00 return at about 70 bp for YM and 90 bp for RTY (ES-like and
NQ-like), with about 2,250 YM and 1,870 RTY sessions, the minimum detectable effect at 80 % power (one-sided, α 0.025)
is **about 4.1 bp on YM and 5.8 bp on RTY**. NQ's substitution on the arm's windows was about 5.6 bp a trade. **So
Gate 1 is decisive on YM, and marginal on RTY, if the rule transfers at NQ's size.** The runner prints the MDE from
each root's realised σ before any mean.

## 7. Verdict and routing

**Per evidence root:**
- Gates 1 and 2: **SUPPORTED**.
- Gate 1, with the **unfiltered** net > 0 (Holm across the roots that passed Gate 1), but Gate 2 failing: **RULE
  ONLY**. It routes as a plain component, without the forecast.
- Gate 1 only: **MECHANISM ONLY**. The direction carries but does not pay a micro's cost.
- Neither: **NOT SUPPORTED**.
- Gate 3 is reported beside each verdict and decides only whether the 15:00 rule goes into any later pre-registration.

**The construction:**
- **SUPPORTED or RULE ONLY on either evidence root:** a pre-registration for the joint vault run (the frozen rule, the
  forecast if it passed, the exit if Gate 3 passed, and the component line), to the principal with its vault power.
  Anything built on GEX informs only the principal's own trading (the SqueezeMetrics permission).
- **MECHANISM ONLY on both:** recorded as a real but untradeable effect at micro size.
- **NOT SUPPORTED on both:** D669's mechanism is recorded as NQ's alone in sample, which supports the principal's
  overfitting reading of the arm.

## 8. Data, seals, order of work

**Seals:**
- **The vault (2025-03-01 → 2026-09-18) is not read** on any root. The runner raises on any row at or after 2025-03-01.
- **SqueezeMetrics GEX** comes from `data/raw/squeezemetrics/DIX.csv` (the main checkout's raw cache, gitignored),
  prior row only. No per-date gamma leaves the runner (a licence guard raises on any list-valued output), and the
  RESULT credits SqueezeMetrics.
- CL/NG post-vault data stays sealed until D626's read; it is not touched.
- NQ's 2024-01 → 2025-02 was read by D503 for the arm. NQ is development, with no verdict.

**No download is needed.** Every input is on disk.

**The order of work:**
1. This record, committed alone.
2. `scripts/stage0_d670_overnight_direction.py`, with `--selftest`, then `--run` once.

**Speed, by design:** four roots fan out to processes. The walk-forward refit accumulates the normal equations (one
7 × 7 update per session). N2's 200 draws reuse the per-session targets.

**The self-test must show, each on a deliberately broken input:**
- a direction built from a bar after 09:59 raises (the causality canary);
- a roll session's direction raises;
- a fit that includes the session's own outcome raises;
- a π̂ that includes the session's own outcome raises;
- a GEX row dated the session itself raises;
- a row at or after 2025-03-01 raises;
- a sign audit in money: a long over a rising window pays positively;
- the permutation keeps each week's long count, and its draw mean sits within 3 SE of the exact carry;
- an oracle direction (sign of the realised move) beats N1's p95, and a random direction sits near p50.

## 9. Predictions, written before the run

1. **NQ (development) earns at least 4 bp a trade gross unfiltered, and clears N1-week.**
2. **YM fails Gate 1**, as the arm did on YM.
3. **At most one of YM and RTY passes Gate 1.**
4. **The full direction beats both of its halves** (gap alone, first half hour alone) on at least three of the four
   roots.
5. **β_disc has t < 2 on both evidence roots** (D647: trend days are hard to see).
6. **P3's paired difference is positive on NQ, but t < 2 on both evidence roots.**
7. **The long side's gross exceeds the short side's on every root.**

## 10. Outputs

- `scripts/stage0_d670_overnight_direction.py`;
- `data/stage0_d670_overnight_direction.json` (statistics only, licence-guarded);
- a RESULT record crediting SqueezeMetrics, with the component line.
