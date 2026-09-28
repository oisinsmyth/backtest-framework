# D663 — STAGE 0 DESIGN: per root, does the opening-range break carry further when dealers are short gamma, and does the cash market's own signed flow at the open multiply it?

*2026-09-28. The principal: "commit as drafted". It is committed alone, before its runner (R8).*

*The principal asked for "the per-root redesign" after D662. There the pre-registered shock × gamma products were
NOT SUPPORTED (powered nulls). A post hoc, unpromotable control showed breaks carrying about 2.7 bp further when ES
dealers were short gamma, measured on the carried ES options book (+0.48 bp per unit g, t 2.30, rotation rank 0.98,
midday placebo nothing). This design:*
1. *measures gamma properly per root;*
2. *measures the shock as each root's own cash-market signed flow;*
3. *tests the break × gamma form as a primary hypothesis;*
4. *tests each root separately, because the mechanisms differ by root.*

## 1. Why per root

The two indices' opening mechanisms differ. D662's pooled and ES-only forms could not see that.

| | ES | NQ |
|---|---|---|
| where dealer gamma sits | SPX/SPXW/SPY options | NDX/NDXP/QQQ options |
| leveraged-ETF rebalancing per 1% move, over the root's daily volume | ≈ 0.3% | ≈ 1.2% (about 4× ES) |
| cash-market breadth that trades the index | the S&P 500 constituents | the Nasdaq-100 constituents |
| micro round trip (recent) | 2.2 bp | 1.3 bp |

Each root is therefore tested with **its own** gamma, **its own** shock and **its own** coefficients, with Holm across
roots. Nothing is pooled.

## 2. Data and seal

**Bars and the break:** D645's B3 per root: the opening range is 09:30–09:59; the break is the first close beyond it
from 10:00 to 11:29; entry is B3's. The data come through `run_opening_v2.load_inputs` (sealed at 2025-03-01).
In-sample: **2016-01-04 → 2025-02-28**, the usable sessions of each root.

**Gamma (the multiplier):**
- **ES, primary: SqueezeMetrics GEX** (the SPX complex, naive sign), `data/raw/squeezemetrics/DIX.csv`.
  - Licensed ([note](../research/licences/squeezemetrics-dix-gex.md)); credited here.
  - The data and any per-date series from it stay in gitignored paths. Code and results are tracked.
  - **Session s uses the GEX row dated before s** (the last one on or before the prior session). The row for day t
    is taken to be computed from day t's close.
  - GEX is read as dollars of hedge per 1% move. The unit is the vendor convention and unconfirmed (D661 C1). Only
    the size claim (§4.4) depends on it, and it is flagged there.
- **NQ, primary:** A4's G from the NQ options fixture (`data/opening/agents.csv`), in dollars per 1% (G × $20 × F² ×
  0.01). It is a thin book, 2–5% of ES's open interest, and no NDX/QQQ gamma is affordable (quote `d2f0b60`).
- **NQ, secondary:** SPX GEX as a market-wide proxy. Dealers' index hedging moves NQ through the ES–NQ correlation.
- **g** = −(gamma $ per 1%) / V₂₀ × 100: short gamma as a percentage of the root's prior 20 sessions' mean day-session
  dollar volume. g > 0 means dealers are short.

**The shock: the cash market's signed flow at the open.** It comes from Sierra Chart market statistics
(`C:\SierraChart\Data`, one-second records, from 2013-11):

| root | primary shock | secondary |
|---|---|---|
| ES | **TICK-SP**: net upticks among the S&P 500 constituents | NYSE up minus down volume (UVOL-NYSE, DVOL-NYSE) |
| NQ | **TICK-NQ**: net upticks among the Nasdaq-100 constituents | NASDAQ up minus down volume (UVOL-NASDAQ, DVOL-NASDAQ) |

- **The window:** from 09:30:00 to the close of the break's signal bar, so it is known at entry.
- **TICK:** s = D × the window's mean TICK, over the sd of the same window's mean across the prior 20 sessions.
- **Volume:** s = D × (up − down) / (up + down) over the window.
- **Gate F (format), run first and reading no outcome.** The runner establishes each file's record meaning:
  - whether up/down volume is cumulative within the session (non-decreasing from 09:30);
  - that records exist from 09:30:00;
  - that every in-sample session has at least 90% of its seconds.

  If a field's meaning cannot be established, that shock is dropped **before** any outcome is read, and the record
  says so.

**Already read on this window:**
- D645 (the first hour, all days), D652, D660, D661's size oracle;
- **D662, including its post hoc ES break × gamma on carried ES gamma.**

The ES primary here uses a different gamma measurement on the same sessions. **It is a re-measurement, not an
independent confirmation.** Confirmation can only come from the vault (§6).

## 3. Variables

- **F:** the 60-minute follow-through after the break, D × ln(P₆₀ / P_entry) × 10⁴, no stop (as D662).
- **g:** as §2.
- **s:** as §2, signed by the break direction D. Positive means the cash market is buying into an up-break (or selling
  into a down-break).

## 4. Hypotheses and statistics, per root r ∈ {ES, NQ}

**H1 (primary): break × gamma.** A short-gamma dealer book makes whatever move is under way carry. With the break
supplying the direction:
- F_r = a + b₁ g_r + e, HAC (lag 5);
- predicted b₁ > 0.

**H2 (secondary): shock × gamma.** The cash market's signed flow into the break carries further when dealers are
short:
- F_r = a + b₁ g_r + b₂ s_r + b₃ (g_r × s_r) + e;
- predicted b₃ > 0.

**Controls, reported and not gating:**
- s alone;
- the piecewise slope of F on s, short-gamma days against long;
- H1 and H2 with the secondary shock;
- for NQ, H1 with SPX GEX.

**The size claim, per hypothesis:**
- β of F on the predicted push I = sign × σ_d √(|gamma $| × |move| / V₂₀), the square-root law as D662;
- a CI wholly below 0.5 is labelled a powered null against the claim;
- ES's claim depends on GEX's unit (§2).

**Nulls:**
- an enumerated circular rotation of each root's g series over its session calendar;
- **purged within ±10 sessions**, because gamma regimes last about a week;
- the rank of b₁ (H1) and b₃ (H2) is reported. It is exact, so there is no sampling SE.

**Placebo (D640's kill rule):** the same rules at midday: range 12:00–12:29, breaks 12:30–13:59, the shock over
12:00 → the midday signal bar.

**Tails and eras, reported:**
- without February–April 2020;
- without the top 1% of |F|;
- leave-one-year-out and by year, **each year count against its own null** (the rotation's year counts);
- before and after 2022-05-16;
- F's mean, median, trimmed means and ex-top/ex-bottom 1%.

**Power:** the MDE of each coefficient at 80%, and **the vault's power** at the in-sample estimate. That is about 360
breaks per root in 390 sessions, with the SE scaled by √(n_in / n_vault).

## 5. Verdicts

The primary family is {H1-ES, H1-NQ}, **Holm across the two** (one-sided). A root's H1 is **SUPPORTED** only if all of
these hold:
- b₁ > 0 with Holm p < 0.05;
- rotation rank ≥ 0.95;
- the midday placebo's b₁ with |t| < 2;
- b₁ > 0 without February–April 2020.

The secondary family is {H2-ES, H2-NQ}: Holm across the two, with the same four conditions on b₃ plus a steeper
short-gamma slope.

Otherwise the verdict is NOT SUPPORTED, stating whether the null is powered.

## 6. Routing

- **An H1 or H2 SUPPORTED for a root:**
  - first, the vault power (§4) is put to the principal;
  - if the principal wants it, a pre-registration of that root's trade follows: the break traded when the product
    predicts carry, with the expected-profit filter (k = 2 × cost), the four reporting groups and a component line;
  - then the vault, in the joint run, on the principal's word.
  - **Under the SqueezeMetrics permission, anything built on GEX may inform only the principal's own trading,
    including the prop account. Nothing built from it is shared with the firm.**
- **Nothing SUPPORTED:** the break × gamma line closes for both roots. With it, the opening line's closure (D658 H-O2;
  D652 without its vault look) is recommended again.

## 7. The runner's assertions, each proved to fire in `--selftest`

1. **Lag:**
   - GEX for session s is dated before s. A canary that uses same-day GEX must raise.
   - The shock window ends at the signal bar's close. A canary that reads the entry bar must raise.
   - g and s are rebuilt by a second implementation.
2. **Sign, in money:** F > 0 for a break followed by a move its way, in both directions.
3. **Right quantity:** F from the entry differs from F from 10:00, and the signed-product b₃ differs from the
   unsigned-product b₃.
4. **B3 reproduced per root** (the break, D and entry equal `b3_trade`'s), and **Gate F** (§2).
5. **Null exactness:** the batched OLS equals per-offset lstsq on a tie-heavy probe, and each fit equals statsmodels.
6. **Licence guard:** the runner writes no per-date GEX or gamma column to any tracked path, and its JSON output
   holds coefficients, statistics and verdicts only. A test fails if a dated gamma series appears in it.

**Speed, by design:** the four (root × hypothesis) analyses and the placebo fan out to processes, and each rotation
null is one batched solve (D662's code).

## 8. Predictions, written before the run

1. **H1-ES:** b₁ > 0 but **NOT SUPPORTED** (below Holm's bar, t < 2.24). D662's t 2.30 was selected post hoc, and a
   re-measurement on the same sessions should regress towards zero.
2. **H1-NQ: NOT SUPPORTED.** NQ's own gamma book is too thin to measure dealer positioning.
3. **H2 for both: NOT SUPPORTED.** D662's shock products were powered nulls.
4. **Every midday placebo is inside noise.**
5. **The vault's power for any supported cell is below 50%.**

## 9. Outputs

- `scripts/stage0_d663_per_root_gamma_break.py` (`--selftest`, `--dry-run`, `--run` once);
- `data/stage0_d663_per_root_gamma_break.json` (coefficients and statistics only);
- a RESULT record crediting SqueezeMetrics.

No trials rows are written.
