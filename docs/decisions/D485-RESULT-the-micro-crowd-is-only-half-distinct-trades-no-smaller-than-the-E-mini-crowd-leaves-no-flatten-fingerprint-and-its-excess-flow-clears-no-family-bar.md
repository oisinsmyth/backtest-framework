# D485 — RESULT: the micro crowd is only half distinct, trades no smaller than the E-mini crowd, leaves no flatten fingerprint, and its excess flow clears no family bar

**2026-09-12.** Spec [D485 PRE-REG](D485-PRE-REG-retail-flow-stage-0-is-the-micro-contract-crowd-a-distinct-population-on-the-ES-and-NQ-tape-and-does-its-divergence-from-the-E-mini-flow-carry-a-signed-intraday-edge.md)
(`0651bb9`, before the code). Fixture `scripts/build_fut_micro_flow.py` → `data/fixtures/fut_micro_flow_5m.csv.gz`
(283,248 bucket rows, 259 sessions 2025-09-11 → 2026-09-10, four contracts; meta with gates).
Runner `scripts/run_d485_micro_flow.py`; numbers `data/d485_micro_flow_stage0.json`; logs
`temp/d485_build.log`, `temp/d485_run.log`. **In-sample only (206 sessions to 2026-06-30); the
reserve is unread; no holdout of any line touched; nothing admitted.**

## 0. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| 1 T5 scale | micro 20–45% of E-mini volume | **ES 0.82, NQ 3.44 contracts per E-mini contract** (median session; 8% and 34% of notional). The prediction confused contracts with notional and is **wrong as written**; the read is right (T2 agrees with the ohlcv-1m schema to 0.00000 on 1,032 contract-sessions) |
| 2 P1 | micro 1-lot share 55–75% vs mini 25–45%; within-session corr 0.35–0.70 | **1-lot share is LOWER on the micro: ES 16.7% vs 18.1%, NQ 33.1% vs 50.4%.** Corr median **0.71 (ES), 0.76 (NQ)**, p10–p90 0.58–0.83 — above the band, below the 0.80 pass line, below the 0.90 abandon. **Lot clause wrong; correlation clause passed; the full P1 fails on the lot clause** |
| 3 P2 | micro corr with the prior session −0.15..0, more negative than the mini | ES micro +0.01 vs mini −0.07 (**fails**); NQ micro −0.06 vs mini −0.05 (passes by 0.01, SE 0.07 — **noise**) |
| 4 P3(a) | last-30 micro sell share 2–6 pp above the day | **−0.3 pp (ES), −0.0 pp (NQ)** — no fingerprint at all |
| 4 P3(b) | cumulative micro flow vs last-hour return −0.05..−0.20, larger than the mini | ES −0.05 vs mini +0.00 (diff −0.05 ± 0.10); NQ −0.02 vs +0.05 (diff −0.07 ± 0.10) — **inside noise** |
| 5 return read | F2 the likelier; no cell clears both nulls | **F1 was the larger** and **no cell clears both nulls** — held |

## 1. The premise (in-sample, both pairs)

| | ES | NQ |
|---|---|---|
| micro / mini RTH volume (contracts, median session; p10–p90) | 0.82 (0.68–1.05) | 3.44 (2.65–5.04) |
| 1-lot share of volume, mini / micro | 18.1% / **16.7%** | 50.4% / **33.1%** |
| within-session corr(OI_micro, OI_mini), median [p10, p90], n | **0.710** [0.58, 0.80], 199 | **0.758** [0.65, 0.83], 199 |
| P2 corr(OI_day, r_prev): micro / mini (SE ≈ 0.07) | +0.009 / −0.066 | −0.056 / −0.047 |
| P3a micro sell share, last 30 min − rest of day | −0.34 pp (SE 0.14) | −0.03 pp (SE 0.09) |
| P3b corr(cum micro flow 09:30–15:00, last-hour return); mini | −0.053 (SE 0.07); +0.001 | −0.021 (SE 0.07); +0.048 |

**Reading.** Half the micro crowd's imbalance is the E-mini's (r² ≈ 0.5–0.6 bucket by bucket),
and the other half is not identifiably retail by any of the three declared fingerprints: micro
trades are not smaller (the NQ E-mini has *more* one-lots than the micro, because one NQ is
$450k of notional), the micro crowd is not more contrarian than the E-mini crowd on the prior
day, and there is no sell-side bulge into the flatten window and no relation between the day's
accumulated micro flow and the last hour. The proxy is not abandoned by the letter of the
pre-registration (0.71–0.76 < 0.90) and it is not a retail identification either.

## 2. The return read (against the micro crowd's excess flow, one micro, $3 round trip)

| cell | n | gross $/session | net | SE | median | hit | trim 1% | worst (session) | Spearman(Dv, move) | side diff $ | N1 exact p50 / p95 | terciles b / m / t |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ES/F1 10:30→16:00 | 199 | **+26.1** | +23.1 | 10.9 | +7.5 | 0.528 | +25.0 | −986 (2025-10-10) | −0.049 | **+69.9** | 0.5 / **66.3** | +33.8 / −16.0 / −36.0 |
| ES/F2 15:00→16:00 | 199 | +4.6 | +1.6 | 7.1 | +5.0 | 0.528 | +3.8 | −265 | −0.069 | +13.4 | −0.1 / 24.2 | +0.5 / +1.1 / −12.8 |
| NQ/F1 | 199 | +9.4 | +6.4 | 42.0 | +22.0 | 0.533 | +3.5 | −1,617 (2026-06-05) | −0.030 | +57.9 | 1.0 / 118.1 | +20.4 / +21.3 / −37.5 |
| NQ/F2 | 199 | +2.1 | −0.9 | 12.6 | +11.5 | 0.518 | +3.2 | −674 | −0.096 | +11.8 | 0.6 / 44.8 | +2.3 / +16.2 / −9.6 |

Family-maximum side difference (N2, common offset, 198 offsets, four cells): **p50 33.9, p95 118.1.**
ES/F1's own-cell N1 p95 for the mean P&L is 26.07 against a score of 26.14.

**ES/F1 sits exactly at its own single-cell p95 on both statistics** (side difference 69.9 vs
66.3; mean 26.14 vs 26.07) **and at the 58th percentile of the family maximum.** By the declared
criterion (above N1 p95 **and** above the family-max p95, gross and net positive) **no cell is a
pick.** It is what a best-of-four looks like on 199 sessions: a monotone tercile split on one
cell, Spearman −0.05, and the null saying that one in twenty random alignments does the same.

## 3. Audits carried

[T1] tape aggressor side vs the price-side rule: 0.99999 agreement on every class-month.
[T2] tbbo volume = ohlcv-1m volume to 0.00000 on all 1,032 fully-covered contract-sessions; the
four contract-sessions of 2026-09-10 fall outside the ohlcv-1m span and are listed, not compared
(the gate encodes the coverage invariant — [[assert-code-not-data]]). [T3] 498/516 pair-sessions
present; the 18 absent are the nine exchange holidays on both pairs. [T4] direct rebuild of a
bucket from raw trades with `ts < end` equals the aggregate; chunk split == whole bit-identical.
[S] sign in money; [M] vectorised P&L == loop on all four cells; [X] flipping the aggressor sign
negates the side difference exactly and gives 0.0000 on T1; [F] every formation window ends at
or before its hold's start by construction. Build: 8 processes, one worker's peak RSS 0.7–1.7 GB
printed before the pool, `[SPEED] 6.96× on 8 workers (87%)`, 3.3 min wall for 37 GB.

## 4. What this settles, and what it does not

- **The micro tape is not a retail identifier.** It is the E-mini crowd at a tenth of the size
  plus a residual that carries none of the three fingerprints declared for it. The line's
  futures arm has no population to hunt with this proxy. That is the value of the record.
- **It does not close "retail flow".** The equity sources identify the population by
  construction rather than by contract size: Robintrack counts the holders (on disk, draft
  pre-reg in `working/DRAFT-robintrack-stage-0.md`), and the Nasdaq tracker tags the trades.
  The line continues there, on the principal's word for each record.
- The **reserve** (2026-07-01 → 2026-09-10) stays unread: there is no pick to read it on.
- Closing the futures arm is the principal's call; my recommendation is to close it on this
  record and spend nothing further on the micro proxy.
