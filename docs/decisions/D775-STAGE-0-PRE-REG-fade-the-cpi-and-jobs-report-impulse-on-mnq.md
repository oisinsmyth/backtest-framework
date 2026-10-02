# D775 STAGE 0 PRE-REG — fade the 08:30 CPI and jobs-report impulse on MNQ: does the cash open reprice a US tier-1 headline set in the futures-only book?

*2026-10-02. The principal: "Pre-reg the CPI/NFP fade as D775".*

- **What it is:** a Stage 0 test of D772's Opus Lead 1, fixing one construction, its nulls and the principal's
  year-by-year test before anything unseen is read. It admits nothing.
- **The order (R8):** this record is committed before the runner exists, the runner before its one run, and the
  result separately.
- **The prop book's rules:** one MNQ, entry 08:35 ET and exit 11:01 ET (flat long before 16:10), fully algorithmic,
  one position.

## 0. What is already known, and what this test can and cannot claim

- **The in-sample data has been read.** D772's Opus pair found this construction in a search (about 15 cells a root
  on six roots, plus a 36-cell entry-and-exit grid). The main session re-derived the primary exactly:
  - MNQ, 186 events 2016–2023: mean +\$34.88 gross, median +\$12.75, t 2.73;
  - non-release weekdays at the same clock: −\$3.32 (n 1,824);
  - **by year:** 2016 −\$1.57, 2017 +\$0.35, 2018 +\$21.79, 2019 +\$11.08, 2020 +\$45.41, 2021 +\$42.91, 2022
    +\$35.85, 2023 +\$123.17;
  - CPI t 1.94 (93), jobs reports t 1.91 (93); best trade +\$735 (2021-12-03), worst −\$583.50 (2022-09-13).
- **So this Stage 0 is not evidence that the effect exists.** Its jobs are:
  1. to fix the construction (one entry minute, one exit, one cost line) before any confirmation;
  2. to run the null the repo trusts (an exact rotation, §4), not only random draws;
  3. to apply the principal's test for a book whose dollars grow with volatility (D772 §1: "does it keep a even win
     rate or a vol adjusted return");
  4. to fix the confirmation's design and its power before anyone asks for a slot (§7).
- **What would earn admission:** only a pass on data none of this has read (§7), on the principal's word.

## 1. The mechanism (what the test is about)

- **At 08:30 the CPI or Employment Situation headline is priced in seconds** by headline-reading algorithms, in a
  futures-only book: the cash equity market is shut until 09:30.
- **The composition then re-prices it:** core against headline, revisions, wages, participation. So does the 09:30
  cash open, which brings full liquidity and the cash/ETF arbitrage.
- **Prediction:** the headline impulse overshoots and gives back, mostly after 09:30.
- **The in-sample falsifiers that already point this way (D772):**
  - large 08:30 moves on non-release days continue;
  - Treasuries, whose cash market is open at 08:30, continue after the same releases;
  - the ECB decision impulse in the same cash-shut window continues;
  - the ISM release at 10:00, after the open, does not revert.

## 2. The candidates and the trade

- **Release days:** every CPI and Employment Situation ("EMPSIT", the jobs report) release at 08:30 ET in
  `data/calendar/events.csv` (D585), sessions 2016-01-01 → 2023-12-31. 192 in the calendar.
- **Bars:** NQ one-minute bars from `fut_opening_globex_1m` (the session's front contract, D462), stamped at the
  bar's START. "The close of bar hh:mm" is the last price before hh:mm + 1 minute.
- **Exclusions (counted):** more than one contract among the bars used, a missing bar, or a zero impulse.
- **The impulse:** x = close(08:34 bar) − close(08:29 bar). The 08:29 bar closes before the release; the 08:34 bar
  closes at about 08:35:00.
  - D772's text called the entry "the 08:34 print" (the close of the 08:33 bar). Its scripts, and the main session's
    re-derivation, used the close of the 08:34 bar. **This record fixes the measured version.**
- **The trade:**
  - side = −sign(x), entered at the close of the 08:34 bar, exited at the close of the 11:00 bar;
  - gross = side × (exit − entry) × \$2 (one MNQ);
  - net = gross − \$4.07 (the repo's MNQ line: \$3 commission plus the one-tick convention, as D737).
- **Every in-sample session also gets the same-clock fade** (side −sign of its own 08:29 → 08:34 move). That is what
  the nulls draw on.

## 3. The gates (in order)

| gate | condition |
|---|---|
| **G1, the effect** | mean gross > 0 with t ≥ 2 |
| **N, the null** | mean gross above the p95 of the exact rotation (§4) |
| **Y, the principal's test** (D772 §1) | **either** (i) the win rate ≥ 50% in at least 6 of the 8 years, **or** (ii) the volatility-adjusted mean > 0 in at least 6 of 8 years AND the 2016–2019 volatility-adjusted mean ≥ half the 2020–2023 one |
| **G2, the prize** | mean net > 0 with t ≥ 2; net > 0 without its best two years; mean gross without 2022 ≥ 2 × \$4.07 |

- **The volatility-adjusted return:** each trade's gross divided by σ, where σ is the standard deviation of the
  unsigned same-clock dollar move (close of the 11:00 bar − close of the 08:34 bar, × \$2) over the 60 prior sessions
  (at least 40; strictly before the day).
- **The readings, in order:**

| reading | condition |
|---|---|
| **NO EFFECT** | G1 fails |
| **NOT ABOVE NULL** | N fails |
| **CONCENTRATED** | Y fails: a book that earns only with the dollar volatility of 2020–23 |
| **NO PRIZE** | G2 fails |
| **SUPPORTED** | all pass |

- **GO = SUPPORTED.** It starts the confirmation conversation in §7. It admits nothing.

## 4. The nulls

- **N, primary: the exact rotation of the release-day labels.**
  - Over the ordered list of in-sample sessions with a valid same-clock fade, the 186 release labels are shifted
    circularly by k sessions, for every k = 1 … S − 1.
  - Each offset scores the mean fade over the labelled days. Offset 0 is the observed.
  - The group is enumerated, so the p95's SE is 0. The full group is kept, including offsets whose labels land near
    the monthly release days (D763: dropping overlapping offsets makes a near-periodic label's null
    anti-conservative).
- **Reported beside it, not gated:**
  - **year-and-weekday-matched draws:** 10,000 draws of 186 non-release days with the release days' count in each
    year and each weekday. This controls for the jobs report always being a Friday. The p50 and p95 carry the p95's
    bootstrap SE;
  - **the matched-impulse draws:** non-release days matched to each release day's year and decile of |x|, 10,000
    draws. This asks whether release days revert more than equally large non-release moves.
- **All three report p50, p95 and the rank.**

## 5. Reported beside the gates (not gated)

- **The declared secondary:** the same side, entered at the close of the 09:29 bar (the 09:30 print), exited at the
  11:00 close. **A pass on the secondary alone is not a pass.**
- **CPI and jobs reports separately.**
- **The split around the cash open,** signed by the impulse: 08:35 → 09:30, then 09:30 → 11:01.
- **The transfers,** with the same rules and nulls:
  - MES (\$5 a point, \$4.42);
  - MYM (\$0.50 a point, \$3.80);
  - M2K (\$5 a point, \$3.76), from `fut_opening_globex_1m_ym_rty`.
- **The sensitivity grid,** as a plateau check: entry K ∈ {3, 5, 10, 15, 30} minutes after the release, exit ∈
  {10:30, 11:00, 11:30, 12:00}. K = 1 is reported as the known continuation.
- **All four groups for the primary book:**
  - **Performance:** gross and net, Sharpe and Sortino (daily, zero on flat days), maximum drawdown, the mean |move|
    against the cost, the breakeven cost.
  - **Trade distribution:** count, mean, median, win rate, payoff, skew, kurtosis, the symmetric 1% trims (ex-top,
    ex-bottom, trimmed), and the five largest trades named.
  - **What the winners depend on:** years, CPI against jobs reports, the impulse's sign, the size of |x|, the
    2016–19 and 2020–23 halves, and the NQ price level.
  - **Nulls:** as §4.
- **The component line:** net Sharpe and Sortino, hit rate, skew, gross beside net, and the daily ρ with D737's twin,
  NQ F2 and C1 (`temp/d755_other_lines.csv`, as D770).

## 6. Predictions and priors

- **G1:** passes (the number is known).
- **N:** the rotation p95 near +\$12 to +\$15, so a pass.
- **Y is the gate at risk.** 2016–17 earned about nothing in dollars, so (i) the win rate is uncertain. For (ii), the
  2016–19 half's volatility-adjusted mean against 2020–23's is the open question.
- **The prior:** SUPPORTED about 40%. The failure expected is CONCENTRATED.

## 7. The confirmation (designed here; it needs the principal's word)

- **No unread in-sample slice exists for NQ.** NQ 2024-01-01 → 2026-09-18 is D737's vault window (programme slot 1),
  read only in the joint run. 2016–2023 is read.
- **The options, each needing the principal's word:**
  - **V, the joint vault:** a programme family in a free slot (2 or 10), NQ 2024-01-01 → 2026-09-18, **64 release
    days** in the calendar.
    - The proposed pass: mean gross > \$4.07, one-sided t ≥ 1.2816, and above the vault-window rotation p95.
    - **Power at the in-sample effect:** an expected t of 1.60, so P(t ≥ 1.2816) ≈ 0.63. At half the effect, 0.80
      and about 0.32.
    - On the strict vault (2025-03 → 2026-09-18, 36 days), expected t 1.20, so ≈ 0.47 and about 0.25.
  - **F, the forward recorder:** its full Globex minutes (from 2026-10-01) carry the 08:29–11:00 bars. At 24 days a
    year, power 0.8 at the full effect needs about 110 days, so about 4.5 years.
- **One overlap to state now:** the trade's first 25 minutes (08:35 → 09:00) sit inside the 18:00 → 09:00 NQ leg
  whose 2024+ slice is spent (BOOK_PROP, 2026-09-12).
  - That reading used the leg's returns (the 18:00 and 09:00 prices), not these minutes. The give-back is measured
    mostly after 09:30.
  - The vault read would report the 09:30 → 11:01 part on its own as well.

## 8. Runner assertions

- **Lag:**
  - the impulse and side use bars closed by the entry print;
  - the volatility scale uses prior sessions only;
  - a second implementation (explicit loops over the raw bars) re-derives x, the side and the gross on 40 sampled
    release days.
- **Sign, in money:** an up-impulse followed by a fall pays the fade; a mirrored book raises.
- **Right quantity:**
  - rotation offset 0 equals the observed;
  - release days read = used + each exclusion;
  - the placebo differs from the treatment;
  - nothing on or after 2024-01-01.
- **The self-test:**
  - a synthetic session fades correctly, and the audit raises on a broken side;
  - chunk = whole for the rotation on processes.

## 9. Output

- `scripts/stage0_d775_cpi_nfp_fade.py`;
- `data/stage0_d775_cpi_nfp_fade.json` (statistics only).
- The result is a separate record.
