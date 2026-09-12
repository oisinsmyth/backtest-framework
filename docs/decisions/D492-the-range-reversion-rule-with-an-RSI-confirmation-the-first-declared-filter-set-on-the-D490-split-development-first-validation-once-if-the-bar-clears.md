# D492 — the range-reversion rule with an RSI confirmation: the first declared filter set on the D490 split (development first; validation once, only if the bar clears)

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. This is
the first **declared filter set** under D490 §0's three-way split: designed and scored on the
development slice (2016-02-01 → 2020-12-31); **the validation slice (2021-01-04 → 2023-12-29) is
read once, under this record, only if the development bar clears, with the filter fixed here;**
the final slice (2024+) stays unread. Written as D491 and renumbered to D492 before commit: the
other session took D491 in the same minute (their conditional-hold record); D492 was free on disk,
in `git log --all` and in the other worktree.

## 0. Why

D490's rule lost gross on both sides (ES −$3.48 a trade, net Sharpe −1.14), with a stale-range
control at ≈ $0 and three fifths of the longs below yesterday's low on a volume spike — a
breakdown with flow, not a stretched tape. The principal asked for **an RSI that would confirm
the mean reversion**: the entry should require the oscillator to say the tape is stretched, not
only the level.

## 1. The filter (declared; one definition, not searched)

- **RSI(14), Wilder's smoothing, on the five-minute regular-hours closes** (bucket ends 09:34,
  09:39, … 15:59; 78 a session), computed as one continuous series across sessions so it is
  defined from the first bars of a day (the overnight gap enters as one five-minute move, as on
  any regular-hours chart). At a one-minute trigger bar the RSI is that of the **last completed
  five-minute bucket at or before the bar**.
- **Long confirmation: RSI ≤ 30. Short: RSI ≥ 70.**
- **Cell A (primary, the principal's ask):** D490's rule unchanged (bottom 5% of yesterday's
  range on a 2× spike; target the top 5%; trail from the last swing past the midpoint; else the
  close) **and** the RSI confirmation.
- **Cell B (secondary):** the RSI confirmation **in place of** the volume spike (bottom 5% and
  RSI ≤ 30), because D490 §2 identified the spike as the breakdown-flow signature.
- Everything else as D490: ES one MES the candidate, NQ the check root, $3 plus the fills, one
  entry per side per day, no initial stop, the no-trail ablation reported.

**ADDENDUM (2026-09-12, before the development run; only the self-test had run):** the principal
specified a much higher timeframe — the holds run for hours (D490 median ≈ 300 minutes), so a
five-minute RSI(14), a 70-minute lookback, is not the oscillator meant. **The RSI is Wilder's
RSI(14) on the regular-hours HOURLY closes** (bucket ends 10:29, 11:29, 12:29, 13:29, 14:29,
15:29 and the 15:59 half-bucket; seven a session), one continuous series across sessions, so 14
buckets span about two sessions — the horizon of "yesterday's range". At a trigger bar the RSI is
that of the last completed hourly bucket at or before the bar. Thresholds unchanged (long ≤ 30,
short ≥ 70). The five-minute version was never run and is not reported.

## 2. Statistics, nulls, bar

D490's, unchanged: the ledger's line per side and pooled; the descriptive splits; N1 (the
wrong-range control, offsets 3–22), N2 (random entries with the same count, time-of-day and
exits), N3 (sign flip). **The development bar: pooled gross mean per trade above N1 p95 and
above N2 p95 + 2 SE, and net Sharpe at one MES > 0.3.** Cell A is the bar's subject; cell B is
reported. **If A (or B) clears in development, the same cell is run once on 2021–2023 with the
same statistics and the rule: PROVISIONAL if the validation gross mean is positive, clears N2
p95 + 2 SE and the net Sharpe is > 0; otherwise recorded as failed at validation.**

## 3. Predictions

- **X-a** The RSI confirmation removes **50–70%** of D490's trades (ES long from 491 to
  150–250).
- **X-b** It does **not** change the sign: at a breakdown below yesterday's low on a spike the
  five-minute RSI is already under 30, so cell A keeps the same trades D490 lost on. Cell A long
  gross **−$6 to +$2**, short **−$6 to 0**; net Sharpe **−0.8 to 0**.
- **X-c** Cell B (no spike) is **better than A by $2–6 a trade** and still **not** above the
  wrong-range control's p95; its net Sharpe **−0.4 to +0.2**.
- **X-d** The bar is **not cleared**; no validation read happens.
- **X-e** The trail's effect is as in D490 (hit up, mean down).
- **X-f** Runtime under 5 min.

## 4. Files

This record · `scripts/run_d492_rsi_filter.py` (`--dev`, `--validate --filter-declared`, `--selftest`) ·
`data/d492_rsi_filter_dev.json` · trade files · RESULT.
