# D728 STAGE 0 RESULT — cross-asset agreement does not sharpen NQ's continuation (all three groups NOTHING); if anything NQ continues MORE when the other index futures disagree; and NQ leads: its move since the open predicts the rest of the day on YM and RTY (rank 0.986 / 0.991) while YM gives back its own move

*2026-10-01. The run: one run of `scripts/stage0_d728_cross_asset_agreement.py` (0.2 min), via `uv run --with pyarrow`
with `--data-root` set to the main checkout.*
- **The order:** the [pre-registration](D728-STAGE-0-PRE-REG-does-cross-asset-agreement-sharpen-nq.md) was committed
  first, and the runner (`26613d5b`) before the run.
- **A first launch** stopped at the fixture read, with no pyarrow in the project environment. NQ's objects had been
  built and checked, but no statistic had been computed and nothing was written. The same code was relaunched with
  pyarrow.
- **The audits:**
  - NQ's objects reproduce D727's known answer (1,941 days, β 10:00);
  - each asset's lag audit passed and its canary fired;
  - each date join passed its audit, and a shifted join fired it.
- **The data:** asset days ES 1,975, YM 1,970, RTY 1,598, ZN 1,975 and 6E 1,984. Nothing dated 2024-01-01 or later was
  read.
- **The output:** `data/stage0_d728_cross_asset.json`.

## 1. S1 — does agreement sharpen NQ's continuation β? (pooled over D727's eleven clocks)

| group | share of rows agree / neither / disagree | β agree | β disagree | Δβ | rotation p05 / p50 / p95; rank | Holm p (high / low) | reading |
|---|---|---:|---:|---:|---|---|---|
| G_eq (ES, YM, RTY) | 0.65 / 0.19 / 0.16 | +0.033 | **+0.103** | **−0.071** | −0.066 / −0.001 / +0.064; **0.043** | 1.00 / 0.13 | NOTHING |
| G_rates (ZN) | 0.27 / 0.38 / 0.35 | +0.031 | +0.035 | −0.003 | −0.076 / −0.000 / +0.078; 0.47 | 1.00 / 0.59 | NOTHING |
| G_usd (6E) | 0.34 / 0.38 / 0.28 | +0.037 | +0.061 | −0.025 | −0.076 / −0.000 / +0.073; 0.30 | 1.00 / 0.59 | NOTHING |

- **No group sharpens.** Every Δβ is negative.
- **The equity group points the wrong way.** Its Δβ sits below its rotation's p05 (rank 0.043), though not after Holm
  (0.13).
  - When ES, YM and RTY are moving against NQ, NQ's continuation slope is three times the slope when they agree. At
    10:00 it is +0.396 against +0.113.
  - **NQ's own moves, the ones the rest of the market does not share, are the ones that continue.**

## 2. S2 — D727's NQ book split by agreement at entry (one MNQ, $4.07)

**At k 1.0, the primary** (the full book: 1,505 trades, +$7.14 net, net Sharpe +0.47):

| group | agree: trades, mean gross | silent | disagree | agree − disagree (rotation p05 / p95; rank) | agree-only book: net, net Sharpe (Sortino), years + |
|---|---|---|---|---|---|
| G_eq | 1,210, +$11.48 | 135, +$1.14 | 160, **+$17.62** | −$6.13 (−18.73 / +19.13; 0.29) | +$7.41, +0.43 (+0.60), 5/8 |
| G_rates | 421, +$13.66 | 441, +$20.54 | 643, +$3.20 | +$10.46 (−21.36 / +24.22; 0.77) | +$9.59, +0.28 (+0.39), 4/8 |
| G_usd | 575, **+$23.80** | 502, +$5.50 | 428, +$0.99 | **+$22.81** (−22.68 / +23.26; **0.945**) | **+$19.73, +0.73 (+1.09)**, 5/8 |

- **None of the splits clears its rotation.**
- **The dollar split comes closest:** NQ follow-trades taken when the euro moves with NQ (the dollar against it)
  gross +$23.80 against +$0.99 when they diverge.
  - Its rank is 0.945, just under 0.95.
  - S1 does not support it (Δβ for G_usd is negative), so it is a book-level lead with no slope behind it.
  - It is also one of 3 groups × 3 k. Not evidence.
- **The equity split repeats S1.** Entries where the other index futures disagree gross the most (+$17.62 at k 1.0,
  +$33.58 at k 1.5), but on few trades (160 / 72).

## 3. S3 — the Dow question: NQ leads

The pooled regression of a root's rest of the day on its own move since the open and on NQ's:

| root | its own move | NQ's move | rotation of NQ's series: p05 / p95; rank | its own move alone |
|---|---:|---:|---|---:|
| YM | **−0.020** | **+0.038** | −0.028 / +0.027; **0.986** | +0.005 |
| RTY | +0.003 | **+0.037** | −0.025 / +0.026; **0.991** | +0.024 |

- **NQ's move since the open predicts the rest of the day on the Dow and the Russell,** above the 95th percentile of
  its rotation on both.
- **With NQ's move in the regression, YM's own move turns negative.** The Dow gives back what it has done on its own,
  and drifts the way NQ has gone.
- **RTY's own continuation (D727's morning echo) disappears** once NQ's move is in. It was NQ's.
- **Answer to the principal's question:** NQ leads the index complex intraday. The Dow does not continue because its
  own move is the noise around NQ's lead.
- This was declared as reported, and gates nothing.

## 4. What it says

1. **Cross-asset agreement does not make NQ's continuation more reliable.** No equity, rates or dollar agreement
   sharpens it.
2. **NQ's continuation looks idiosyncratic.**
   - It is strongest when the other index futures are NOT moving with it.
   - Consistent with a mechanism specific to NQ, whether its constituents' news, or its own options and ETF complex,
     and not with a market-wide risk-on/risk-off day.
3. **NQ leads YM and RTY intraday.**
   - This is a new structural fact: NQ's move since the open predicts their rest of the day.
   - Whether it is tradeable has not been measured: MYM is $0.50 a point, so the move must be large to clear $3.80.
     That would be its own pre-registration.
4. **The dollar-agreement split** (+$23.80 against +$0.99, rank 0.945) is the only book-level lead. It is unsupported
   by the slope and selected among nine cells.
5. **Proposed, not decided:**
   - (a) the principal's step 3, the volume profile (high volume early, then steady): a new, outside-the-price
     variable for trend days, now queued;
   - (b) the NQ-leads-the-Dow trade on MYM/M2K as its own premise check;
   - (c) the slot-10 vault pre-registration of D727's NQ follow, which needs the principal's explicit word.
