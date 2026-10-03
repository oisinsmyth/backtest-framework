# D783 STAGE 0 PRE-REG — D775's fade on the other BLS releases at 08:30 (PPI primary): is "the cash open reprices a headline set in the futures-only book" general, or a CPI/jobs-report fact?

*2026-10-03. The principal: "Lets go with option 1"; on scope, "BLS first, then decide".*

- **What it is:** a Stage 0 test of D775's mechanism on releases D775 never touched. It uses D775's construction,
  gates and nulls unchanged. It admits nothing.
- **The order (R8):** this record is committed before the runner exists, the runner before its one run, and the
  result separately.
- **The prop book's rules:** as D775. One micro, entry at the 08:34 bar's close and exit at the 11:00 bar's close;
  flat long before 16:10; fully algorithmic.
- **Programme slots are full.** A supported cell could go only to the forward recorder or to an amendment, not to this
  joint run.

## 0. What is already known, and what is not

- **D775 (in-sample, read):** on CPI and jobs-report days, fading the 08:29 → 08:34 NQ impulse to 11:00 earned
  +\$34.88 gross per MNQ (t 2.73, 186 days). That passed G1, N, Y and G2, and it is frozen as D776.
- **The releases here have never been scored by anyone,** on any root, with any construction. The new calendar
  (D782) was built today, before this record; no price was read for it.
- **The falsifiers D772 found** (large 08:30 moves on non-release days continue; Treasuries, whose cash market is open,
  continue) say the effect needs a release and a shut cash venue. They do not say which releases.

## 1. The mechanism and the prediction

- **The mechanism (D775 §1):** an 08:30 headline is priced in seconds in a futures-only book; the 09:30 cash open
  re-prices it.
- **Prediction:**
  - If the mechanism is general, PPI behaves like CPI: a smaller impulse, so a smaller dollar fade, but positive and
    above its null.
  - The minor releases (import prices, productivity, the ECI) move NQ little at 08:30. If they fade at all, it is
    below the cost.
  - **The mechanism's own dose check:** within each cell, the fade grows with |impulse| (the |x| terciles).

## 2. The release sets (from D782's calendar; sessions 2016-01-01 → 2023-12-31; 08:30 ET only)

| cell | events | days in the calendar | role |
|---|---|---|---|
| **PPI (primary)** | PPI | 96 | gated |
| IMPEXP | import and export prices | 96 | reported |
| PROD | productivity, preliminary and revised | 64 | reported |
| ECI | the Employment Cost Index | 32 | reported |
| ALL | the four above, pooled | 288 | reported |

- **D775's own days are removed from the panel.** Every CPI and Employment Situation session (D775's
  `release_days()`) has its bars dropped before the panel is built. They are neither treatment nor control here.
  - The 60-session volatility window then runs over the remaining sessions.
  - PPI on NQ with D775's days kept is reported beside the primary.
- **A session in another D782 cell stays in a cell's control pool** (it is not that cell's release).
- **No D782 day falls on a CPI or Employment Situation day** (D782's meta).

## 3. The construction, the gates and the nulls: D775's, imported unchanged

- **The code:** `stage0_d775_cpi_nfp_fade.study(bars, root, release_days, primary)`, unchanged. Only the release-day
  dict differs.
  - impulse x = close(08:34 bar) − close(08:29 bar); side = −sign(x); entry at the 08:34 close, exit at the 11:00
    close;
  - MNQ \$2 a point and \$4.07; the transfers MES \$5/\$4.42, MYM \$0.50/\$3.80, M2K \$5/\$3.76;
  - the exclusions D775 counts: two contracts, a missing bar, a zero impulse.
- **The gates (D775 §3), on PPI × MNQ:**
  - **G1:** mean gross > 0, t ≥ 2.
  - **N:** above the p95 of the exact rotation of the release labels over the panel's sessions (every offset, SE 0).
  - **Y, the principal's test:** the win rate ≥ 50% in at least 6 of 8 years, OR the volatility-adjusted mean > 0 in at
    least 6 of 8 years AND 2016–19's ≥ half of 2020–23's.
  - **G2:** mean net > 0 with t ≥ 2; net > 0 without the best two years; mean gross without 2022 ≥ 2 × \$4.07.
- **The readings,** in D775's order: NO EFFECT, NOT ABOVE NULL, CONCENTRATED, NO PRIZE, SUPPORTED.
- **Reported beside the gates (all from D775's study):**
  - the matched draws (year × weekday; year × impulse decile);
  - the 09:30 secondary and the split around the cash open;
  - years, sign, |x| terciles and the price terciles;
  - the K × exit grid;
  - the four groups, the five best and worst trades;
  - the component line on the primary (labelled `d775` inside D775's code).
- **The cells:** PPI on all four roots (MNQ primary; MES, MYM, M2K transfers). IMPEXP, PROD, ECI and ALL on MNQ only.

## 4. The decision this test feeds (fixed now)

- **"Then decide" (the principal):** whether to source Census (retail sales), BEA (GDP, personal income) and DOL (jobless
  claims) schedules.
  - **Recommend fetching them** if PPI × MNQ passes G1 and N, OR the pooled cell passes N with mean gross ≥ 2 × \$4.07.
    Either says the mechanism reaches beyond the two headline releases.
  - **Recommend not fetching them** if PPI and the pool are NO EFFECT or NOT ABOVE NULL. The effect would then be
    specific to CPI and the jobs report, and D776 stays the line's only instance.
- **Either way, the D776 vault read is unchanged.** This test reads no 2024+ price.

## 5. Predictions and priors

- **PPI:** an impulse about a third to a half of CPI's, so a mean fade of +\$8 to +\$15 if the mechanism holds. The t
  is near 1 on 96 days.
  - G1 is the gate at risk.
  - Prior: G1 and N pass about 30%; SUPPORTED about 10%.
- **IMPEXP, PROD, ECI:** NO EFFECT expected (the impulse is near zero at the cost).
- **The dose check:** the high-|x| tercile carries the PPI cell if anything does.

## 6. Runner assertions

- **Right quantity, first:** the imported `study` on the unfiltered bars with D775's own release days reproduces D775's
  primary (186 trades, mean gross +\$34.88) before any D783 cell is scored.
- **The panel:**
  - no CPI or Employment Situation session remains in the D783 panel;
  - every cell's release days are 08:30 rows of D782's calendar within 2016–2023.
- **D775's own assertions run inside `study`:** the lag audit on 40 sampled release days, rotation offset 0, read =
  used + exclusions, and the placebo differs from the treatment. Its loader raises on a session on or after
  2024-01-01.
- **The self-test:**
  - the calendar loader keeps only 08:30 rows in the window;
  - the removal drops exactly the CPI/EMPSIT sessions;
  - D775's sign audit raises on a mirrored book.

## 7. Output

- `scripts/stage0_d783_bls_0830_fade.py`;
- `data/stage0_d783_bls_0830_fade.json` (statistics only).
- The result is a separate record.
