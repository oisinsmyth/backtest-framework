# D680 PRE-REGISTRATION: the NQ compression break for the joint vault run. One MNQ on D672's compressed-third break, friction counted once, one look

*Drafted 2026-09-29.*
- *The principal: "No need, I am happy for the NQ compression to stay in queue for the big vault run"; then "Freeze
  the ones that where queued today".*
- *It is committed alone. Its runner (`scripts/vault_d680_nq_compression.py`) exists and has produced the power study
  below and the in-sample known answer. Neither is evidence.*
- *The vault is read once, in the joint run (A10), and not before.*

## 0. Where this comes from: a development finding, disclosed as one

**D672** found the compression break on NQ, in development, on the sample where the thread itself was found. **On
NQ it is close to circular.**
- C1 (the compressed third) netted +6.93 bp a trade (t 2.40) under D668's cost stack.
- With the friction counted once (D668-A2 / D672-A1) that is **+7.56 bp (t 2.62)**: 387 trades, 2018-01-09 →
  2025-02-28, about 55 a year; gross at the level +9.42.

**Outside NQ:**
- D673: it did not transfer to YM or RTY (RTY's compressed third was its worst).
- D679: on nine energy and metals roots the tier's sign held everywhere, at about a quarter of NQ's size, without
  clearing its declared bar.

**The in-sample number is therefore NOT evidence.** It is the reason to spend the look, and the vault is the first
sample it has not seen.

## 1. The rule: D672's C1, unchanged

- **The break:** D666's plain break of yesterday's NQ RTH high + 0.25 × ATR20, or low − 0.25 × ATR20, live from
  09:30 (D666's entry window), the first break only.
- **The exit:** E4, with the initial stop at yesterday's level, a trail 0.25 A behind the best price, and flat at the
  close.
- **The filter:** trade only when **ctier < 1/3**, where
  - comp = the mean of the walk-forward percentiles (the previous 250 sessions) of rv5 (the previous five sessions'
    mean RTH range in ATR units) and the overnight two-way range ((Globex high − low − |open − prior close|) / ATR);
  - ctier = comp's own walk-forward percentile.
  - All of these are D671's functions, imported unchanged. **The percentiles run through the in-sample into the vault,
    point-in-time.**
- **Money:** one MNQ.
  - The trade is scored **at the level**: the stop, or the open through it, with no fill tick.
  - Each trade is charged **$3 + the measured `d508_exec` crossing, once** (D668-A2).

## 2. The vault read

**Input:** NQ bars for 2015-09 → 2026-09-18 from the **vault-input path**: D644's one-minute fixture built through
2026-09-18, and G0's loader with the cut moved.
- That path is **not yet built**. It is a prerequisite before the principal calls the joint run, as D630 §8 is for
  D649.
- **`--vault` proves it first:** the bars' in-sample part must reproduce this record's known answer exactly (387 C1
  trades, +6.93 and +7.56 bp net) before any vault session is scored. **If it cannot be built or does not reproduce,
  this line is not scored**, and the gap is written up.

**The verdict:**

| verdict | condition |
|---|---|
| **PASS** | (i) at least **30 C1 trades** in the vault **and** (ii) C1's mean gross > 0 with **one-sided HAC t ≥ 1.2816** (p < 0.10, D649's bar) **and** (iii) C1's mean net > 0 |
| **FAIL** | otherwise |
| **UNRESOLVED (too few trades)** | below 30; the look is spent and nothing is concluded |

**Reported beside, never gating:**
- the programme promotion check (p ≤ 0.005, slot 9);
- B0, every break on the same vault days (D668's plain break, single count);
- C1 − rest gross;
- the trade distribution (CLAUDE.md's four groups);
- daily $ Sharpe and Sortino at one MNQ;
- ρ with the MACD arm's daily P&L if rebuilt, else named missing.

**One look.** `--vault` refuses:
- without the principal's word;
- unless this record's freeze verifies (`data/FROZEN_vault_d680_nq_compression.json`: the runner's sha256, this
  record's, those of the four modules it imports, and the parameters);
- a second opening.

## 3. Multiplicity and consequence

- **A new programme family, slot 9** (α 0.005, a reserved slot, no amendment): "opening compression break (NQ)". Its
  promotion check at the programme level uses 0.005 and is reported.
- **A PASS** is the out-of-sample confirmation R8 requires for this construction. It admits nothing by itself: the
  prop book still needs the components ledger and hurdle P.
- **A FAIL closes the NQ compression break,** with no re-tuning of the tier, the third, the trail or the size
  afterwards.
- **D668's plain break is not queued separately.** C1 is its subset, on the same clock and signal. B0 is reported
  beside C1 on the same days and spends no slot.

## 4. POWER (`data/vault_d680_power.json`, seed 680)

**Method:**
- the vault's 390 sessions are drawn in 20-session blocks from D672's in-sample window;
- C1 trades on about 21.7% of sessions, so about 85 trades;
- C1's gross is shifted so its mean is s × the in-sample's +9.42 bp;
- 2,000 draws per row.

| edge kept in the vault, s | PASS | FAIL | UNRESOLVED | programme promotion (p ≤ 0.005) | C1 trades, median (p10–p90) |
|---|---|---|---|---|---|
| 1 (the in-sample's) | **0.66** | 0.34 | 0.00 | 0.15 | 85 (72–99) |
| 0.5 | 0.30 | 0.70 | 0.00 | 0.03 | 85 (72–98) |
| 0.25 | 0.18 | 0.82 | 0.00 | 0.01 | 86 (73–99) |
| 0 (none) | 0.10 | 0.90 | 0.00 | 0.00 | 85 (72–99) |

**Read it as:** the look is decisive only if the vault keeps most of the in-sample edge. A development number on its
own discovery sample should be expected to shrink, and at half the edge the look is a coin toss weighted to FAIL. The
false-pass rate with no edge is 10%, the bar's own.

**Optimistic in one way:** the blocks resample the in-sample's regimes. The vault's NQ volatility and trend are
unknown (unread).

## 5. What this does not touch

- D672's and D673's records, runners and in-sample results are unchanged. This line imports D671's, D668's, D666's
  and D663's functions and hashes them at the freeze.
- No vault or post-vault NQ data is read before the joint run.
- **Deviations** are listed in the output and never replace a verdict.
