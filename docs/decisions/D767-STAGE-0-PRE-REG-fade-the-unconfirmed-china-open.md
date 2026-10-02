# D767 STAGE 0 PRE-REG — fade the unconfirmed China open: does a filter that keeps the opening moves the AUD and the other metals do not confirm turn D765's reversal into a trade worth one micro?

*2026-10-02. The principal:*
- *"Let do a selection filter on the whole set of trades not just winter months … Do oracle filter first, find
  monthly distribution of trades";*
- *"can you check and reason which you think will work?";*
- *"Would it be worth combining some?";*
- *"Pre-reg that, build and run it".*

- **What it is:** an expected-profit filter study on one base construction. It admits nothing.
- **The order (R8):** this record is committed before the runner exists, the runner before its one run, and the
  result separately.
- **The prop book's rules:** one micro (MGC, SIL or MHG), flat before 16:10 ET, fully algorithmic, one position.
  MHG's and SIL's eligibility is the principal's assumption.

## 0. What is already known, and what this test cannot claim

- **The base construction** is D765's, with the sign chosen from D765's data.
  - The trade: fade the 09:00 → 09:30 Beijing move, entering at the 09:31 open, exiting at 15:00 Beijing.
  - D765 found reversal on gold (ρ −0.063, p 0.007), borderline on silver (−0.046, p 0.054), none on copper.
  - **The fade's sign was read from in-sample data, and this test is in-sample (2016–2023) on data D765 has read.**
  - A pass therefore earns only a confirmation on unseen data: the joint vault or the forward recorder, on the
    principal's word.
- **The oracle** (scratchpad `d765_oracle.py`, descriptive):
  - fading every session, the oracle (net > 0) takes 39–55% of trades in every calendar month and every year;
  - its monthly shares match the candidates' within about 1.5 points. **Winners exist evenly across the year.**
  - The unfiltered fade's monthly means swing between +\$10 and −\$8 (gold), with SE about \$4.4 a month.
- **The partial-oracle curve** (keep the top third by a forecast of rank correlation ρ):
  - net t ≈ 2 needs ρ ≈ 0.13 (MGC), 0.09 (SIL) and 0.11 (MHG);
  - break-even is ρ ≈ 0.05, 0.02 and 0.05.
  - Real filters here have reached 0.04–0.06 (D690).
- **The filter's choice was made without its outcomes** (scratchpad `d765_filter_checks.py`, which reads no y):
  - F3 (AUD unconfirmed) is nearly size-free (ρ with |x| −0.14 to −0.23), overlaps D765's |x| third only 24–26%, and
    selects evenly by month (max deviation 0.8–2.6 points) and year;
  - F4 (metals unconfirmed) is related to F3 at 0.27–0.31;
  - F1 and F5b re-select D765's |x| third (67–87% overlap); F5 and F6 select small moves; F7 is a volatility-regime
    gate (year deviation 11–16 points).
  - D765's reported numbers (the AUD correlation, the 2×2s) were seen before this choice. Nothing else of the
    outcome was.
- **The priors:** a SUPPORTED cell about 15% (mostly silver, if its overnight cost holds); gold about 8%.

## 1. Universe, trade, costs

- **The candidates:** D765's eligible sessions (2016-01-04 → 2023-12-29; China's holidays, the roll week, missing
  prices, isolated prints and two-contract sessions excluded, exactly as D765), with x ≠ 0.
- **The trade:** side = −sign(x); entry at the open of the bar starting 09:31 Beijing; exit at P(15:00 Beijing).
  - gross = side × y × multiplier (MGC 10, SIL 1,000, MHG 2,500);
  - net = gross − the micro's round trip (MGC \$5.93, SIL \$8.00, MHG \$4.25).
  - The thin-book line (+1 tick a side: +\$2, +\$10, +\$2.50) is reported.
- **The prices and clocks are D765's runner functions,** imported unchanged.

## 2. The filter scores (all known at 09:31 Beijing; higher = less confirmed)

- **The scale of each opening move:** z_k = x_k / median(|x_k| over the prior 60 metal-eligible sessions, at least
  40 finite, strictly prior).
- **A partner's x is valid** when finite, from one contract, and touching no isolated print (on any of its sessions,
  eligible or not).
- **F3 (the AUD):** F3 = −sign(x) × z_6A. The AUD moving with the metal is negative, and against it is positive.
- **F4 (the other two metals):** F4 = −sign(x) × mean(z of the other two metals' valid x).
- **U (primary):** U = (F3 + F4) / 2, equal weights, nothing fitted. It is undefined if either part is.
- **The selection:** the walk-forward top third.
  - A session is traded when its score exceeds the 2/3 quantile of the score over the prior 250 candidate sessions'
    finite values (at least 100, strictly prior).
- **The secondary:** S2 = D765's walk-forward |x| top third ∩ U's walk-forward top third.
- **Reported, in no reading:** F3 alone and F4 alone (each its own top third), and the unfiltered fade.

## 3. Gates (per cell; MGC, SIL and MHG are all primary, with Holm over the three)

- **G1, the mechanism (gross, unfiltered):** the fade of every candidate session, mean gross > 0 at t ≥ 2. This is
  the house rule: a filter on no mechanism selects noise.
- **N, the null (exact enumeration, SE 0):**
  - rotate U circularly against the candidate sessions by every offset k = 1 … n − 1, redo the walk-forward
    selection, and take the selected trades' mean net;
  - the filter passes above the rotation's p95. p50, p95 and its rank are reported.
  - The rotation keeps U's distribution and the trades; it breaks only their pairing.
- **B, the principal's balance tests:**
  - **B1:** the selected trades' calendar-month shares are within 5 points of the candidates' in every month (the
    oracle sits within 1.5);
  - **B2:** the selected book nets > 0 on its trades outside December–March.
  - Year shares within 5 points are reported.
- **G2, the prize (net, filtered):** mean net > 0, t ≥ 2, a one-sided p Holm-adjusted over the three cells below
  0.05, and net > 0 without its best two years.
- **Accuracy (reported):**
  - the Spearman of U with the gross over the candidates past the burn-in (placed on the partial-oracle curve);
  - the AUC against the oracle label (`filter_oracle.assess`);
  - the share of the oracle's net captured.

## 4. Readings (declared now, per cell, in this order)

| reading | condition |
|---|---|
| **NO MECHANISM** | G1 fails |
| **NOT ABOVE NULL** | G1 passes; the filtered mean net ≤ the rotation's p95 |
| **UNBALANCED** | G1 and N pass; B1 or B2 fails. The filter is a season gate |
| **MECHANISM ONLY** | G1, N and B pass; G2 fails |
| **SUPPORTED** | all pass |

- **GO = SUPPORTED on any cell.** It starts a confirmation conversation with the principal (the vault or the
  forward recorder). It admits nothing.
- **The secondary S2** gets the same gates and readings, with Holm over its three cells, and is reported as
  SECONDARY.

## 5. Reported, all four groups (per cell, for U's book; S2 beside it)

- **Performance:** gross and net, the thin-book line, Sharpe and Sortino, maximum drawdown, the mean |move| against
  2c, and the breakeven cost.
- **Trade distribution:** count, mean, median, win rate, payoff, skew, kurtosis, the symmetric 1% trims, and the
  five largest trades named.
- **What the winners depend on:** years, calendar months (with the month shares beside the candidates' and the
  oracle's), EDT against EST, long against short, and the 2020 night-suspension sub-era.
- **Nulls:** the rotation's p50 / p95 / rank.
- **The component line:** net Sharpe, Sortino, hit rate, skew, gross beside net, and the daily ρ with D737's twin,
  NQ F2 and C1.

## 6. Runner assertions

- **Lag:**
  - a second implementation recomputes z, F3, F4 and U on 40 sampled sessions per cell with explicit loops over the
    raw session tables;
  - a hand-written quantile re-derives every selection flag;
  - the flag audit must raise on a threshold that includes the current session.
- **Sign, in money:** an opening rise followed by a fall pays the fade (short), and a mirrored book raises.
- **Right quantity:**
  - U ≠ F3 ≠ F4;
  - the filtered book ≠ the unfiltered book;
  - rotation offset 0 = the observed selection;
  - no kept row ≥ 2024-01-01.
- **Speed:** the rotation's offsets fan out over processes, and the self-test proves chunked = whole bit for bit.
- **The self-test:** a planted filter (the outcome tied to U) clears the null; on noise the filter clears p95 about
  5% of the time.

## 7. Output

- `scripts/stage0_d767_china_open_fade_filter.py`;
- `data/stage0_d767_china_open_fade_filter.json` (statistics only).
- It reads D765's extraction cache (`temp/d765/`), rebuilt by D765's `--extract` if absent.
- The result is a separate record.
