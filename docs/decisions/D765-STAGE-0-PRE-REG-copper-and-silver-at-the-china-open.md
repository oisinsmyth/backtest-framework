# D765 STAGE 0 PRE-REG — copper and silver at the China open: does the first half hour after Shanghai's 09:00 open on MHG and SIL carry on, or reverse, into the SHFE close?

*2026-10-02. The principal: "Lets look at copper and silver at the china open?"; then "Yes to all three questions":*
1. *the carry-on-or-reverse check, with the US-afternoon catch-up reported inside it;*
2. *MHG and SIL assumed prop-eligible;*
3. *a Fable agent's design in parallel with Opus's.*

- **The design:**
  - It merges two independent designs, each written before its author read the other's.
  - Both are in the session scratchpad (`fable_china_open.md`, `opus_china_open.md`).
  - Where they differed, §9 says which was taken and why.
- **What it is:** a premise check. It chooses no rule.
- **The order (R8):** this record is committed before the extraction and the runner exist; the runner before its one
  run; the result separately.
- **The prop book's rules:**
  - one micro (MHG or SIL), inside one Globex session, flat before 16:10 ET;
  - fully algorithmic;
  - no hedging (one position at a time).
  - The eligibility of MHG and SIL is the principal's assumption, not verified.

## 0. What is known

- **The size table** (descriptive, 2016–2023, `fut_breadth_hourly`; AITODO, 2026-10-02):
  - copper's and silver's evening size spike follows Beijing's clock, not New York's;
  - the one-hour |move| / 2c peaks at 21:00 ET under EDT and 20:00 ET under EST, both 09:00 Beijing, the Shanghai
    Futures Exchange (SHFE) day open. MHG 2.62 in both regimes; SIL 3.54 and 3.27;
  - copper has a second spike at 13:30 Beijing (the SHFE lunch reopen);
  - MGC shifts the same way but smaller (1.84 / 1.67). CL and 6E barely shift.
  - Holds of 20:00 → 03:00 ET are 5.2 × 2c (MHG) and 6.5 × 2c (SIL).
- **SHFE's hours (Beijing):**
  - the day session runs 09:00–10:15, 10:30–11:30 and 13:30–15:00;
  - the night session runs 21:00–01:00 for copper and 21:00–02:30 for gold and silver (China Finance and Economic
    Review, 2016, Table 1);
  - night trading was suspended 2020-02-03 → 2020-05-05.
- **The literature:**
  - **Jin, Kearney, Li and Yang** (J. Futures Markets 2020; MPRA 97134, text checked):
    - on SHFE copper, 2,655 days (July 2002 → June 2013), the first half-hour's return predicts the last half-hour's
      with slope 0.067 (t 4.26, R² 1.36%);
    - the effect is strongest when the first half-hour's volume or volatility is high;
    - their mechanism is day traders' positions unwound into the close.
  - **Liu and An** (JIMF 2011): copper's information shares are 38.6% Chinese futures and 43.5% US futures.
  - **Iwatsubo, Watkins and Xu** (2017): liquidity trading dominates the Tokyo day session for gold and platinum.
  - **Lee and Park** (2020): SHFE has no significant influence on international copper prices even after its night
    session. That is the counter-prior.
- **The repo:**
  - D499 (off-hours hourly reversal: real, under a tick);
  - D678 (the HG overnight gap carries no direction);
  - D761 (round numbers: real at \$1–1.5, too small).
  - No study has read the China clock.
- **The prize arithmetic, which shapes the design:**
  - a signed follow earns about 0.8 · ρ · sd(y);
  - at ρ 0.06 on MHG that is about \$2 against \$4.25;
  - so the prize needs ρ of about 0.12 inside the traded third. Hence the |x| condition and the hold to the SHFE
    close.
- **The priors** (before any run):
  - PREMISE HOLDS about 10% (MHG) and 8–12% (SIL);
  - a direction (either sign) on at least one cell about 50%, positive given a pass about 60%.

## 1. Data, seal, conventions

- **Prices:** full-size HG, SI, GC and 6A one-minute front bars, all hours, from the raw Databento ohlcv-1m archive.
  These are the micros' prices, read through the deeper book.
  - The front per trade date is `fut_breadth_hourly`'s.
  - One contract per session.
  - **The roll week is excluded:** the 5 sessions before the front changes, because HG and SI are physically
    delivered (the standing rule).
- **The window:** trade dates 2016-01-04 → 2023-12-29. 2016 on because 6E's raw minute bars before 2016 carry
  off-market prints (D761 §1).
- **The seal:** nothing dated 2024-01-01 or later is decoded. The builder asserts it, and the self-test proves the
  assertion raises.
- **The clocks:**
  - UTC → ET by zoneinfo, checked against the statutory US rule on every bar;
  - UTC → Beijing is a fixed +8.
  - A CME trade date's session holds the Beijing date of the same name at 09:00 Beijing.
- **The price at time t:**
  - P_t = the close of the bar starting at t − 1 minute, forward-filled within 3 minutes;
  - otherwise the session is dropped and counted.
- **The print check:** a used price (P_t, or an entry open) that sits 20 or more ticks from BOTH neighbouring closes
  voids the session. The voids are counted per year.
- **China's calendar:** `data/calendar/china_exchange_holidays.csv`.
  - It holds 141 weekday closures of the Shanghai exchanges, 2016–2023, in 53 blocks.
  - The source is `exchange_calendars`' XSHG list (source text at commit `20ed4736`).
  - It was checked against the State Council notices for 2018, 2020 (the COVID-extended Spring Festival; SHFE reopened
    2020-02-03) and 2023.
  - The assumption is that SHFE closes on the SSE's national-holiday weekdays.
- **Costs:**
  - MHG: \$4.25 a round trip (2c \$8.50; MHG is 2,500 lb, tick \$0.0005 = \$1.25).
  - SIL: \$8.00 (2c \$16.00; SIL is 1,000 oz, tick \$0.005 = \$5).
  - MGC: \$5.93.
  - The thin-book line (+1 tick a side) adds \$2.50 for MHG and \$10 for SIL. It is reported.

## 2. The quantities (Beijing-aligned)

| | definition |
|---|---|
| **x** (the opening move) | P(09:30) − P(09:00) Beijing |
| **entry** | the open of the bar starting 09:31 Beijing |
| **y, primary** | P(15:00 Beijing) − entry: the SHFE day close, 03:00 ET under EDT and 02:00 ET under EST |
| y at 10:15 / 11:30 (reported) | the shape |
| y_last (reported) | P(15:00) − P(14:30): Jin et al.'s object, replicated on CME |
| **the traded set** | the walk-forward top third of \|x\|: the threshold is the 2/3 quantile of \|x\| over the cell's prior 250 eligible sessions, strictly prior |
| **the side** | sign(x) under continuation, −sign(x) under reversal, set by C2's sign (§3) |
| \$ | points × the micro's multiplier (MHG 2,500, SIL 1,000, MGC 10) |

- **One trade a session, one position.** The two lenses coincide (every candidate is traded, and nothing overlaps). The
  record says so.
- **Eligible session:**
  - an SHFE trading day (not in the calendar);
  - not in the roll week;
  - every used price present;
  - no print void.

## 3. Checks (per primary cell; MHG and SIL)

- **C1, size:** the mean |y| in \$ at one micro on the traded third, against 2 × 2c (MHG \$17.00, SIL \$32.00).
  - Also reported: sd(y), the mean |y| at 10:15 and 11:30, and the mean |x| on trading days against holidays.
- **C2, direction:** Spearman ρ(x, y) over every eligible session, against the **exact enumerated rotation** of y.
  - The rotation shifts y circularly by k = 1 … n − 1 eligible sessions, so SE 0. p2.5, p50 and p97.5 are reported.
  - **It is two-sided:** it passes if ρ is outside [p2.5, p97.5], with Holm over MHG and SIL at α 0.05 (p is the
    two-sided enumerated rank).
  - The predicted sign is positive (continuation).
  - Reported beside it: the OLS slope with its Newey-West (5) t, and ρ within the traded third.
- **C3, China's open:** two controls that break the ingredient.
  - **(a) The holiday control:** CME sessions on China's closure days (about 130 after the US-holiday overlap), at the
    same clock.
    - Passes if the treatment's mean |x| exceeds the holidays' by more than 2 SE (Welch).
    - ρ on holidays is reported with its SE (about 0.09). It cannot gate, and the record says so.
    - The first session after Spring Festival and after Golden Week is reported as the extreme case.
  - **(b) The daylight-saving control:** the identical (x, entry, y-to-15:00-Beijing) construction anchored at the ET
    hour of the China open in the OTHER regime:
    - 21:00 ET in EST months, which is 10:00 Beijing;
    - 20:00 ET in EDT months, which is 08:00 Beijing.
    - It has the same ET clock and the same y end, with no China open at the anchor.
    - The margin is ρ(treatment) − ρ(placebo), signed in C2's direction, with SE from a paired bootstrap over month
      blocks (2,000 draws, seed 765).
    - It passes at a margin above 2 SE.
    - The 2×2 (Beijing-aligned against ET-fixed, EDT against EST) is printed.
- **C4, not generic intraday momentum:** two same-day placebos with the same y end (15:00 Beijing) and the same rule:
  - **the Tokyo open:** x = P(08:30) − P(08:00) Beijing, entry 08:31. 09:00 Tokyo: is it China, or just Asia?
  - **the post-break:** x = P(11:00) − P(10:30) Beijing, entry 11:01.
  - The treatment's signed ρ must exceed each placebo's by more than 2 SE (the same paired bootstrap).
  - Within 2 SE is UNRESOLVED.
- **C5, the prize:** the traded third, side per C2's sign.
  - It passes at mean NET > 0 with t ≥ 2, a one-sided p Holm-adjusted over MHG and SIL below 0.05, and net > 0
    without its best two years.
  - If C2 failed, C5 is scored on the predicted sign (continuation) and reported, in no reading.

## 4. Readings (declared now, per primary cell, in this order)

| reading | condition |
|---|---|
| **SIZE FAILURE** | C1 fails. The component line is written anyway |
| **NO DIRECTION** | C2 fails |
| **NOT CHINA** | C2 passes, and C3(a) fails or C3(b)'s margin is ≤ 0 |
| **UNRESOLVED** | C2 and C3(a) pass, and C3(b)'s or a C4 margin is above 0 but within 2 SE |
| **GENERIC** | C2 and C3 pass, and a C4 placebo's ρ is at or above the treatment's |
| **NO PRIZE** | C2–C4 pass and C5 fails |
| **PREMISE HOLDS** | all pass |

- **GO = PREMISE HOLDS.** It starts a Stage 1 design conversation with the principal (a forward or vault slice). It
  admits nothing.
- **MGC (reported):** the dose contrast, on the same construction.
- **6A (reference, not traded):** ρ(x_HG, x_6A) at the open. Informed Chinese demand should co-move with the AUD.

## 5. The catch-up variant (the principal's "copper catching up the US afternoon"; reported, in no reading)

- **g** = P(09:00 Beijing) − P(SHFE night close): 01:00 Beijing for copper, 02:30 for silver.
- **g_US** = P(17:00 ET) − P(night close): the US afternoon alone.
- **Reported against the same rotation null:** ρ(g, x), ρ(g, y), ρ(g_US, y), and the 2×2 of sign(g) × sign(x) with
  mean y in each cell ("China agrees or disagrees with America").
- The night-suspension sub-era (2020-02-03 → 2020-05-05) is shown separately; then the open absorbed about 16 hours.

## 6. Reported, all four groups (per cell)

- **Performance:** gross and net, the thin-book line, Sharpe and Sortino, maximum drawdown, the mean move against 2c,
  and the breakeven cost.
- **Trade distribution:** count, mean, median, win rate, payoff, skew, kurtosis, the symmetric 1% trims, and the
  five largest trades named.
- **What the winners depend on:**
  - years, EDT against EST, Monday opens, long against short;
  - the 2020 night-suspension sub-era;
  - the 09:16 → 09:30 re-based x (the 09:15 PBoC yuan fix sits inside x; this variant is declared now so it is not
    a post hoc choice);
  - the auction move P(09:01) − P(08:55).
- **The nulls:** the rotation's p2.5 / p50 / p97.5, and every control and placebo with its SE.
- **The component line:** net Sharpe at one micro, Sortino, hit rate, skew, gross beside net, and the daily ρ with
  D737's twin, NQ F2 and C1 (D761's line file). The clock shares no clock with any ledger component.

## 7. Runner assertions

- **Lag:**
  - a raw-row loop over 40 sampled sessions per cell re-derives x, y, g, the traded-third flag and the holiday flag,
    without calling the runner's functions;
  - a third that includes the current session must raise;
  - an entry read from the 09:30 bar's close must raise.
- **Sign, in money:**
  - an up-move pays the long and a down-move the short; the audit raises on a mirrored book;
  - a planted continuation in the treatment window only passes C2–C4; noise fails C2 about 95% of the time.
- **Right quantity:**
  - Beijing-aligned ≠ ET-fixed on EST sessions, and identical on EDT sessions;
  - holiday ∩ treatment = ∅;
  - rotation offset 0 equals the observed ρ;
  - no kept row ≥ 2024-01-01; one contract per session;
  - sessions read = eligible + each exclusion, counted.
- **Speed:** the extraction fans out over processes, and the self-test proves chunked = whole.

## 8. Output

- the HG, SI, GC and 6A extraction (cache in `temp/`; a fixture a record quotes goes to `data/`);
- `scripts/stage0_d765_china_open.py`;
- `data/stage0_d765_china_open.json` (statistics only);
- the calendar `data/calendar/china_exchange_holidays.csv` and its `.meta.json` (committed with this record).
- The result is a separate record.

## 9. Where the two designs differed

- **The primary hold:**
  - Opus had the 11:30 lunch break (about 2 hours); Fable had the 15:00 close (about 5.5 hours).
  - **15:00 is taken:** it is Jin et al.'s mechanism (unwinding into the close), and a longer hold amortises one
    round trip.
  - 10:15 and 11:30 are reported.
- **The holiday control:**
  - Opus gated a 1.5× ratio of |x|; Fable gated a > 2 SE Welch drop.
  - **The Welch test is taken,** because the ratio was a number chosen without a distribution.
- **The daylight-saving control:**
  - Fable compared against the ET-fixed window in EST months only. Opus anchored at the other regime's China-open ET
    hour in both halves of the year.
  - **Opus's symmetric version is taken:** it uses every session, and in EDT months its anchor (08:00 Beijing) is
    also Fable's Tokyo placebo, so the two controls are disclosed as overlapping there.
- **Fable's additions are taken:** the Tokyo and post-break placebos (C4), y_last, the auction move, the re-based x,
  g_US, the 2020 sub-era, and the thin-book line.
- **Not taken:** Fable's split on NBS release days. No sourced calendar of them exists here, so it is noted as not
  built.
- **The 13:30 Beijing reopen** (Opus's within-China replication) is dropped from the reported list. It is
  inside y, and a second x would be a second test on the same y.
