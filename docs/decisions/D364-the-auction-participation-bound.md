# D364 — the auction participation bound: the opening minute is 1.4% of the day, so the fade's order is 2.5% of it, and D363's "liquidity is not the constraint" was measured against the wrong denominator

**Status:** MEASUREMENT. **No predictions were registered and none are claimed** — this is a
census in the shape of D339's, run because D363 left a 100 bp question resting on a number
nobody had measured. Nothing here is a strategy result, a null, or a book entry.
**Date:** 2026-09-07
**Area:** Cost model · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**No orders were placed. Nothing is promoted. The avenue is the principal's (R15).**

---

## 1. What was measured and why

D363 bounded the two-sink gated gap-up fade's execution at **−49 bp a trade if both fills
cross the spread, +3 if one does, and +55 if neither does**, the last being the case where
both fills are auction prints. It then argued that liquidity was not the constraint on that
+55, because at $25k a position the trade is **0.0386% of the entry day's dollar volume**.

That denominator is the whole day. The order goes into an auction. This record measures the
right denominator by pulling **1-minute bars with extended hours** for a stratified sample of
the fade's own trades, and reading the volume in the **09:30 bar** (the opening auction print
plus one minute of continuous trade) and the **16:00 bar** (the closing auction plus a
minute). Both are **upper bounds on the auction's own size**, so every participation figure
below is a **lower bound on the truth**.

**Sample:** 100 A2 trades drawn `default_rng(364)`, 20 per PUB half-spread quintile, from the
3,028-trade row-drop A2 arm (mean +60.97, asserted against `data/d362_sink_filter.json`);
146 distinct (symbol, month) Alpha Vantage requests, 141 served in 6.5 minutes. **78 trades
are complete on all four measures** and carry the headline.

## 2. The finding

| minute / whole-day dollar volume, same bar | p25 | **median** | p75 | p90 |
|---|--:|--:|--:|--:|
| **09:30 minute** | 0.88% | **1.44%** | 2.36% | 4.09% |
| **16:00 minute** | 2.73% | **7.85%** | 13.58% | 28.44% |

**The honest denominator is 69× smaller at the open and 13× smaller at the close.**
Participation scales by the same factors:

| at $25k a position, median | entry fill | exit fill |
|---|--:|--:|
| D363's whole-day figure | 0.0386% | — |
| whole day, this sample | 0.0243% | 0.0532% |
| **the minute the fill actually happens in** | **2.494%** | **0.645%** |

At $25k, **two thirds of entries are above 1% of the opening minute and a third are above
5%**. At $50k it is 81% and 50%. And the widest PUB quintile — the one D363 showed carries
the entire edge (+225 gross a trade against +13 for the middle three) — is **the thinnest**:

| PUB quintile, $25k, entry | median participation | above 1% | above 5% |
|---|--:|--:|--:|
| 0 tightest | 1.90% | 62% | 23% |
| 1 | 0.83% | 44% | 33% |
| 2 | 1.78% | 62% | 25% |
| 3 | 3.10% | 81% | 31% |
| **4 widest** | **4.20%** | **87%** | **47%** |

The opening minute in that quintile carries a median $596k against $1.3M in the tightest, and
its whole-day volume is a third of the tightest quintile's. **Where the edge is, the auction
is thinnest.**

## 3. What this does and does not say about the +55

**It does not measure impact.** Participation is not slippage; this record has no fills and
makes no claim about what a print moves by. What it does is remove the premise the +55 rested
on. D363's auction bound is the arithmetic of a fill **at the print with no impact**, and
"0.04% of the day" was the argument that such a fill was plausible. At **2.5% of the opening
minute in the median trade, and 4.2% in the quintile that carries the edge**, that argument
does not hold, and the honest position is that **the auction cost is unmeasured and is not
zero**. The three D363 bounds stand as arithmetic; the reason for preferring the top of the
range is gone.

**It also sharpens what a live test needs to answer.** The fill log and slippage instrument
(`scripts/d364_slippage.py`) measures exactly this: fill minus print in bp. The number it
would produce is the one this record shows is missing.

## 4. What the measurement costs itself, stated

- **The endpoint is short of the consolidated tape.** Summed 1-minute dollar volume is a
  median **82%** of the daily fixture's (86% on complete 391-bar sessions). If the 09:30 and
  16:00 bars are short by the same fraction, every participation figure above is overstated
  by about **1.22×** — and that correction runs the same way through both denominators, so it
  **does not touch the ratio**, which is the finding. 86 of 198 (symbol, date) pairs fall
  outside a [0.8, 1.2] dollar band and every one is named in the output and the JSON.
- **The extreme share-ratio outliers are a frame artefact, not an error.** The fixture is
  split-adjusted and the intraday bars are as-traded, so `dollar / share` recovers the split
  factor — ORLY 14.86, MSTR 10.2, several at 2–4. The dollar ratio is split-invariant and is
  what the assertion uses.
- **Survivor-only, and the tilt is small.** The intraday endpoint refuses delisted tickers,
  so **676 of 3,028 A2 trades (22.3%) are unreachable**. The kept trades are barely different
  on what matters: gross **+61.31** against **+59.81** excluded, PUB half-spread **51.95**
  against **50.81**. The liquidity tilt is real but modest (median gap-day dollar volume
  1.65× higher on the kept), and exclusion is near-flat across the quintiles.
- **17 of 97 fetched exit sessions have no 16:00 bar at all** (complete to 15:59, post-market
  bars after). They are dropped from the closing-minute column and named; they skew to the
  tightest quintile, so the closing-minute figures are if anything mildly overstated.
- **n = 78.** A stratified sample of a 3,028-trade arm, not a census of it.

## 5. The probe that had to pass first

Before the fetch: `extended_hours=true` on a 1-minute request returns a **16:00 bar on every
one of 23 full sessions** of the probe name, and a regular session is **391 bars** — 09:30 to
15:59 continuous plus the 16:00 auction bar, stamps marking the interval's open. On the probe
date the 16:00 minute was 4.45% of the session's share volume. **No 15:59 was ever
substituted for a missing 16:00**; a missing bar is a dropped row and is counted.

## 6. Assertions

| | |
|---|---|
| **[HOLDOUT-GUARD]** | 184 file opens audited, none containing "holdout"; the probe path refused |
| **[S]** | the arm is 3,028 trades at **+60.9727** — D362's stored **row-drop** A2 exactly (not the re-simulated 3,079 / +61.71, which the export cannot produce; the +51-trade, +0.74 bp gap is reported rather than asserted away) |
| **[K]** · **[AX]** | the sample payload's sha256 matches and all 100 rows re-derive from the export; the date axis reproduces 49,500 of the export's (bar, date) pairs |
| **[TZ]** | US/Eastern, stamped at the interval's open, 09:30…15:59 plus the 16:00 auction bar |
| **[REC]** | the dollar ratio's median inside [0.5, 2.0] with per-pair order-of-magnitude and positive-volume checks; the [0.8, 1.2] band is a **reporting** band, every name outside it listed. **The measured median is 0.79 — outside that band — and the record says so rather than crashing on a real measurement** |
| **[6]** | a global ×5 raises; a single perturbed pair is named without raising |

## 7. What this changes in the record

- **FINDINGS §43 rule 3 and its "liquidity is not the constraint" clause are amended**, and
  STACK §0's D363 paragraph with them. The whole-day figure was not wrong; it was the wrong
  denominator for a fill that happens in an auction.
- **D363's three execution bounds stand.** Only the reason for believing the top of the range
  was reachable is withdrawn.
- **The next number is a fill.** Not another estimate.

## 8. Files

`data/d364_auction_sample.json` · `data/d364_probe.json` · `data/d364_auction_bound.json` ·
`scripts/d364_auction_bound.py` · raw 1-minute bars cached under
`data/raw/alphavantage/1min/` (gitignored, exchange terms). Reuses the committed export
`data/d361_trades_gap_up_fade.csv`, `data/d362_sink_filter.json`, and
`scripts/fetch_single_name_intraday.py`'s client conventions. The holdout fixture was not
opened.
