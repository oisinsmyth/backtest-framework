# D495 — stage 0: the day session after a daily state — fade the next day session after a top-decile day, and after a daily RSI(2) extreme, on ES and NQ, intraday only

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D495-stage-0-the-day-session-after-a-daily-state-fade-the-next-day-session-after-a-top-decile-day-and-after-a-daily-RSI-2-extreme-on-ES-and-NQ-intraday-only.md`. The H1 above is the full title.*

**Pre-registration of a STAGE-0 premise check. Committed before the runner exists (R8).** Result
in a separate file. In-sample **2016-01-04 → 2023-12-29** on the D462 one-minute regular-hours
fixtures (full sessions); **2024-01 onward unread** — the day session's forward slice is clean
for this family and the runner raises if a row past 2023 reaches the measurement. D495 taken
after `ls docs/decisions` and `git log --all` on both worktrees showed D492 as the highest of mine; D493–D494 were taken by the other session between the check and the write, so this record is D495.

## 0. Why, and what is already seen

D490 and D492 showed that a print at yesterday's extreme is not where the intraday reversion
lives (a stale range does as well). D487 measured where it does: the index tape mean-reverts
within quiet days, and **on NQ the day session after a top-decile day-session move gives back
≈ 25 bp** (2.2 SE, outside its rotation null, calm and stress years alike; ES −7 bp, inside).
The principal asked to test the constructions that sit on that. Both are **intraday**: the state
is read at yesterday's close, the position runs from the 09:30 open to the 16:00 close, flat by
the plan's 16:10 rule, exposed to no untraded window.

**Overlap, stated:** cell A's statistic on 2016–2023 was printed once in D487 (as a correlation
and a top-decile mean); this record re-derives it as a trade at one micro with costs, MAE and
by-year, and adds cell B, which nothing has read. The honest forward test for both is 2024+.

## 1. The two cells (declared; nothing added after the numbers)

- **Cell A — fade the big day.** State at yesterday's close: |R_{t−1}| in the **top decile** of
  the trailing 252 day-session absolute returns (causal; at least 120 sessions of history), where
  R is the session's 09:30 open → 15:59 close return. Direction: **opposite to sign(R_{t−1})**.
- **Cell B — the daily RSI(2) extreme.** Wilder RSI with n = 2 on the continuous series of 16:00
  prints (full sessions), read at yesterday's close: **long if ≤ 10, short if ≥ 90**.
- **The trade (both cells):** enter at the 09:30 bar's open plus one tick in the direction
  above; exit at the 15:59 close; one MES / one MNQ; $3 a round trip plus the entry tick.
  No target, no stop — this is the premise, not the rule; the MAE distribution is reported so
  that any later stop is designed on the data.
- **Roots:** ES and NQ, both scored; sides reported separately; the family is **2 cells × 2 sides
  × 2 roots = 8** and the null in §3 is sized to it.

## 2. Statistics

Per cell, side, root: trades and share of sessions; gross mean and median $ per trade and in
bp; net mean; hit rate; payoff; skew; the 1%-trimmed mean; MAE quantiles (p50, p95, worst) from
the one-minute lows/highs and the count of days below −2% of $50k at one micro; **the net Sharpe
of the daily series on the session calendar** with its block-bootstrap SE (the ledger's line);
by year; by the D490 development/validation sub-periods (2016–2020 / 2021–2023) as a
consistency split; the **other side**: the day-session return in the same direction on the
days the state did NOT fire.

## 3. Nulls

- **N1 — exact rotation** of the state series against the day-session returns (every offset ≥ 2):
  destroys the day-to-day alignment, keeps both series. Statistic: the gated mean in the
  trade direction. p50, p95 (SE 0).
- **N2 — the family maximum on a difference statistic centred on zero** (D472's lesson): for each
  cell-side-root, z = (gated mean − other-side mean in the trade direction) / SE of the
  difference; under a **common rotation offset across all eight cells**, the maximum z per
  offset; p50 and p95 of that maximum. A cell above the family p95 is a concentration; one
  above its own N1 p95 but below the family p95 is a pick.
- **N3 — sign flip** of the daily series for the Sharpe.

## 4. The bar (declared)

A cell **PROCEEDS to a construction record** (exits designed for shape on the same in-sample
window, then the 2024+ read on the principal's word) if, on at least one root: gross mean per
trade > N1 p95; **z above the family-maximum p95**; net Sharpe at one micro > 0.3; and the sign
holds in both sub-periods. A cell that clears N1 and the Sharpe but not the family bar is
recorded as a **PICK** and does not proceed without the principal's word. Otherwise closed.

## 5. Predictions

- **X-a** Cell A fires on ~10% of sessions (≈ 200 trades); cell B long on 8–14%, short on 8–14%.
- **X-b** Cell A on NQ: gross **+15 to +30 bp** a trade (≈ $30–60 on one MNQ), hit **53–58%**,
  clears N1, **z 2.0–2.8** against a family p95 of **2.3–2.6** — marginal; net Sharpe **+0.3 to
  +0.6**. ES: **0 to +12 bp**, inside N1.
- **X-c** Cell B: long after RSI(2) ≤ 10 **+5 to +20 bp**; short after ≥ 90 **−5 to +5 bp** (the
  index drift fights it); NQ larger than ES; neither clears the family bar.
- **X-d** MAE: median **−50 to −80 bp**, p95 **−180 to −260 bp**; no day below −2% at one micro.
- **X-e** By year, NQ cell A's sign holds in **≥ 6 of 8** and in both sub-periods; the 2020–2022
  years carry most of the dollars.
- **X-f** The other side (the state did not fire) is within ±3 bp of zero in the trade direction
  on cell A; on cell B the long side's other side is the unconditional drift.
- **X-g** Runtime under 3 min.

## 6. Files

This record · `scripts/run_d495_daily_state_stage0.py` (`--run`, `--selftest`) ·
`data/d495_daily_state_stage0.json` · trade files · RESULT.
