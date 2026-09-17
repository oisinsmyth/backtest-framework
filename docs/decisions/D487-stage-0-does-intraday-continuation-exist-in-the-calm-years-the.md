# D487 — stage 0: does intraday continuation exist in the calm years? The by-year split, the within-day shuffle null, the next-day reversal signature, and the trend-day frequency, on ES and NQ

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D487-stage-0-does-intraday-continuation-exist-in-the-calm-years-the-by-year-split-the-shuffle-null-the-next-day-reversal-and-the-trend-day-frequency-on-ES-and-NQ.md`. The H1 above is the full title.*

**Pre-registration of a STAGE-0 premise check. Committed before the runner exists (R8).** Result
in a separate file. In-sample **2016-01-04 → 2023-12-29** on the D462 one-minute regular-hours
fixtures (`fut_ES_rth_1m`, `fut_NQ_rth_1m`), full 390-bar sessions only; **2024-01 onward
unread** (the day session's forward slice is the one clean reserve left for this family and it
stays so). D487 taken after `ls docs/decisions` and `git log --all` on both worktrees showed
D486 as the highest number (D474–D486 are the other session's; note also that both sessions
have a D473 on master — theirs the cost-structure record, mine the K7 component — a clash
recorded, not resolved).

## 0. Why, and what is already measured

The principal asked about opening-range breakouts. The literature (memory
*intraday-continuation-mechanisms-orb*) says an ORB has no mechanism of its own: it is a wrapper
on intraday continuation, whose documented drivers — short-gamma hedging demand
(Baltussen–Da–Lammers–Martens 2021), delayed rebalancing to the close (Bogousslavsky 2016;
Gao–Han–Li–Zhou 2018) and order-flow long memory — put the continuation **late in the day**, make
it **a regime property** (negative gamma, high volatility), give it a **next-day reversal**
(price pressure, not information), and have it **flat in the 0DTE era**.

**The other session has measured the pooled premise on ES already**, and this record does not
repeat it: the variance ratio is 0.82–1.02 across five time grids and four volume grids (their
D471/D473 §4: "the price path itself carries nothing"); conditioned on volatility state the
continuation edge shows a mild gradient with volatility and horizon (hit rate 49.9% → 55.5% from
15 to 195 minutes in the top volatility quintile) that is **UNRESOLVED** against a 40-cell
family null (their D474); and the gradient **does not transfer** to seven other roots (their
D475: the sign flips). D463 measured the first-30 → last-30 slope at a third of its published
size, inside the sign null.

**What is not yet measured, and what an ORB decision needs:** whether continuation exists in the
**calm years** at all (their split was by volatility state, not calendar year, and the ORB
replication's P&L was 76% one year); a null that **destroys within-day continuation and keeps
each day's volatility** (a shuffle, not a sign flip); the **next-day reversal** of the day's move,
which the hedging mechanism predicts and information does not; the **trend-day frequency**, which
is the quantity a breakout's payoff actually depends on; and **NQ** as a second index root.

## 1. Data and the day-session objects

Per full session: the 26 fifteen-minute returns `r_1..r_26` from the fixture's one-minute
closes (the first from the 09:30 open), the day-session return `R = Σ r_i`, the path high and
low, the first-30 return `f = r_1 + r_2`, the last-30 return `l = r_25 + r_26`, the rest-of-day
`m = R − l`. Calm years: **2016, 2017, 2018, 2019, 2023**; stress years: **2020, 2022**; 2021
reported with neither label. Realised-vol tercile of the trailing 21 day-session returns, causal,
as D470.

## 2. Statistics (all by year, by calm/stress, and by vol tercile; ES primary, NQ check)

- **S1 variance ratio** `VR = var(R) / (26 · var(r))` pooled over the days of the group (Lo–MacKinlay;
  1 under no autocorrelation).
- **S2 half-day continuation** `corr(Σ r_1..13, Σ r_14..26)`.
- **S3 rest-of-day → last-30 slope** (Baltussen's statistic) and **first-30 → last-30 slope**
  (Gao's; D463's), with SE.
- **S4 trend-day frequency** `F = share of days with |R| / (path high − low) > 0.5` (the close
  in the outer half of the range in the direction of the move), and the mean of that ratio.
- **S5 next-day reversal** `corr(R_t, R_{t+1})` and, after top-decile |R_t| days,
  `E[sign(R_t) · R_{t+1}]` in bp with SE.

## 3. Nulls (named by what they destroy and what they keep)

- **N-shuffle (primary):** within each day, permute the order of the 26 fifteen-minute returns;
  1,000 draws. Destroys within-day autocorrelation; keeps every day's return set, hence its
  volatility, its R and its calendar. Gives the null of S1, S2, S3, S4 per group; p50, p95 with
  the p95's bootstrap SE (D373: within 2 SE is UNRESOLVED). S1 and S4 are the primaries.
- **N-rotate (for S5):** the day-session series rotated by every offset ≥ 2 (exact); destroys the
  day-to-day alignment; keeps the series.

## 4. The decision rule (declared)

**PROCEED to an ORB construction record only if, on ES, S1 or S4 is above the shuffle p95 + 2 SE
pooled over the five calm years AND above it in at least three of those five years individually,
AND NQ agrees on the pooled calm-year statistic.** Otherwise **CLOSE the ORB line before a
breakout is tested**: continuation confined to 2020 and 2022 is a regime bet the account cannot
carry (three years in eight), and the family multiplicity of a range/stop/target grid would
only add to it. The stress-year and vol-tercile results are reported as the mechanism's
fingerprint, not as a gate.

## 5. Predictions

- **X-a** Pooled 2016–2023 ES: VR **0.90–1.02**, inside the shuffle null (the other session's
  0.82–1.02 reproduces); S2 within **±0.03**.
- **X-b** Calm years: VR **≤ 1.02**, S4 within the null, in **every** calm year on ES; NQ the
  same. Stress years: VR **1.05–1.20** and S4 above the null p95 in 2020 and in 2022.
- **X-c** S3 rest-of-day → last-30 slope positive pooled but **under 2 SE** in the calm years;
  above 2 SE in 2020 (Baltussen's effect lives in stress).
- **X-d** S5: `corr(R_t, R_{t+1})` **−0.06 to 0** pooled; after top-decile days
  `E[sign(R_t)·R_{t+1}]` **−5 to −20 bp** in the stress years and within ±5 bp in the calm ones —
  the price-pressure signature where the continuation is, absent where it is not.
- **X-e** Vol terciles: the top tercile carries whatever continuation exists (VR top > mid > low).
- **X-f** **Decision: CLOSE.** Runtime under 3 min.

## 6. Files

This record · `scripts/run_d487_continuation_stage0.py` (`--run`, `--selftest`) ·
`data/d487_continuation_stage0.json` · RESULT.
