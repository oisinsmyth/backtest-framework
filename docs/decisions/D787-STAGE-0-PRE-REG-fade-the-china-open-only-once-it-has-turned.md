# D787 STAGE 0 PRE-REG: fade the China open only once it has turned. Mark the open's extreme, and enter at 09:46 only if the 09:45 price is back inside it

*2026-10-03. The principal: "Ok what if we mark the peak of the open and only enter if after 15min from the 'close' of
the open the price is lower than that?", then "Ok prereg it".*

- **What it is:** a Stage 0 test of a confirmation entry on D765's gold China-open fade. The principal proposed it
  after D770's finding that a resting fade is filled into continuation and misses the fastest reversals.
- **The order (R8):** this record is committed before the runner exists, the runner before its one run, and the
  result separately.
- **The prop book's rules:** one MGC, fully algorithmic, flat well before 16:10 ET (the exit is 15:00 Beijing).
- **The primary book is passive,** by the principal's ruling of 2026-10-03 (D786's addendum). Taker is reported beside
  it.
- **It admits nothing.** 2016–2023 has been read for this fade by D765, D767, D770, the 210-verdict debate and D786. A
  SUPPORTED reading can only nominate for a separately pre-registered 2024+ confirmation. The principal decides
  whether to spend it.
- **Nothing on or after 2024-01-01 is read.** Every input is asserted.

## 0. What is known

- **The fade (D765/D767):** 1,697 MGC candidates.
  - Taker, 09:31 entry: +\$3.14 gross, t 2.49, −\$2.79 net.
  - Passive at the 09:30 touch (D770): +\$2.12 gross, −\$0.92 net.
- **The reversal's shape (D765 §5):** ρ(x, P(t) − entry) is +0.017 to 10:15, −0.042 to 11:30, −0.063 to 15:00. The
  open continues slightly for about 45 minutes, then reverts into the SHFE close.
- **D770's adverse selection:** the 8% of passive orders that never filled carried the taker fade's best sessions
  (+\$10.44 gross, against +\$2.56 on the filled 92%). The resting order is filled when the open keeps going.
- **Unknown:** whether the open's state at 09:45 (still at its extreme, or turned) sorts the rest of the session.
  - No record has conditioned on the 09:30–09:45 path.
  - The debate's timing slot was never used. Candidate 41 moved the entry to 10:31 without a price condition.

## 1. The mechanism and the prediction

- **The account:** an open that is still at its extreme 15 minutes after the window is a move still being pushed, by
  continuation or news, and fading it is fading a trend. An open back inside its extreme has stopped. If the fade's
  edge is liquidity being given back, it is concentrated in the opens that have stopped.
- **Prediction:** the kept sessions earn more per trade than the unconditional 09:46 entry, and the skipped sessions
  earn less, or lose. The effect shows in both execution books.
- **The cost of confirming:** entering at 09:46 gives up whatever reversal happened between 09:31 and 09:46 on the
  kept sessions. Against the unconditional 09:46 entry that cost is common to both, which is why the control is at
  09:46 and not 09:31.

## 2. The construction

- **Sessions:** D767's MGC candidate set (D765-eligible, x ≠ 0), built exactly as in D786 (`build()`).
- **The side,** as D765: −sign(x), with x = P(09:30) − P(09:00) Beijing.
- **The open's extreme, from D765's one-minute GC bars** (P(t) is the close of the bar starting at t − 1 minute,
  D765's `Px`):
  - for an up-open (x > 0), PEAK = the maximum of P(t) over t = 09:01 … 09:30;
  - for a down-open, TROUGH = the minimum.
  - Closes, not bar highs: the comparison price P(09:45) is a close, and D765's isolated-print voiding is defined on
    closes.
- **The primary condition (K1, "back inside its extreme"):** keep the session if P(09:45) < PEAK (up-open) or
  P(09:45) > TROUGH (down-open), strictly.
- **The secondary condition (K2, "turned past the 09:30 price"):** keep if P(09:45) < P(09:30) (up) or P(09:45) >
  P(09:30) (down), strictly. Declared now; reported, not gated for nomination.
- **Validity:** every price read for the session (P(09:00) … P(09:30), P(09:45), the 09:46 open, P(15:00)) is on one
  contract and not void, by D765's `Px` rules. A session failing this leaves every 09:46 book, kept or not, and is
  counted.
- **The taker book (reported):** enter at the 09:46 bar's open, exit at P(15:00); gross = side × (P15 − O(09:46)) ×
  \$10; \$5.93 a round trip.
- **The passive book (primary):** D770's rules at the new clock, through a copy of D770's `session_micro` with the
  clock as the only change.
  - Rest at the 09:45 touch, from the paid GC tbbo and bbo-1m window: sell at the ask for an up-open, buy at the bid
    for a down-open.
  - Filled on a trade-through within 30 minutes, [09:45, 10:15).
  - Exit at the 15:00 touch, as D770 prices it.
  - Cost: \$3.00 plus D770's MGC exit adjustment, recomputed as D786 did.
  - The GC tape's last price before 09:45 must agree with the bar P(09:45) within 2 ticks (D770's mismatch rule),
    else the session is excluded and counted.
- **The control:** the same book on every valid session at the 09:46 clock, with no condition.
- **The reference (reported):** the 09:31 books as published (D767 taker, D770 passive).

## 3. The gates (passive kept book, K1)

- **G1:** mean gross > 0 and t ≥ 2.
- **N:** the kept book's Σgross / Σ|gross| above the p95 of the exact rotation of the K1 flag over the candidate
  sequence.
  - Every offset 1 … n−1 (SE 0); a rotated book is the rotated flag ∩ filled.
  - Σg/Σ|g| is the size-invariant statistic (D711-A1): a flag that leans toward large opens cannot pass on size.
  - Mean net against the same rotation is reported beside it.
- **Y (the principal's year test, as D775):** a win rate ≥ 50% in at least 6 of 8 years, OR the volatility-adjusted
  mean > 0 in at least 6 of 8 years AND 2016–19's ≥ half of 2020–23's.
  - Volatility-adjusted = gross / σ, where σ is the standard deviation of the unsigned same-clock move (P15 − entry)
    × \$10 over the prior 60 valid sessions (at least 40), strictly prior.
- **G2:** mean net > 0 and net t ≥ 2, AND net total without the best two years > 0.
- **The readings, in order:**
  - **NO EFFECT:** G1 fails;
  - **NOT ABOVE NULL:** N fails;
  - **CONCENTRATED:** Y fails;
  - **NO PRIZE:** G2 fails;
  - **SUPPORTED.**
- **Reported beside the gates, not gated:**
  - B1 (the largest month-share gap of the kept set against all valid sessions; the debate's 5-point line);
  - net outside Dec–Mar (the debate's B2);
  - the same gates on the taker book;
  - the same gates on K2.
- **Nomination:** only K1 on the passive book, only if SUPPORTED.
  - K2, or taker alone, passing is reported as a lead, not a nomination: two conditions and two books are four
    looks, and the primary is fixed now.

## 4. Power (stated before the run)

- **G2 is the gate at risk.** The per-trade sd is about \$50. On about 1,000–1,400 kept trades, net t ≥ 2 needs a
  passive mean net of about +\$2.7 to +\$3.2, a passive gross near +\$6.
- **The 09:30 passive book grosses +\$2.12.** If the 09:46 control is similar and K1 keeps about three-quarters of
  sessions, the skipped quarter would have to average about −\$10 gross.
- **N is reachable at much smaller effects:** the flag's p95 sits at about 1.65 SE.
- **Prior:**
  - N passes about 25%;
  - SUPPORTED about 3%;
  - the likeliest reading is NOT ABOVE NULL or NO PRIZE.

## 5. Reported (all from the run)

1. **Counts:**
   - valid sessions at the 09:46 clock and the exclusions by reason;
   - the K1 and K2 kept shares, and their correlation with |x|;
   - the passive fill rate at 09:45, and D770's adverse-selection table at the new clock (taker gross on filled
     against unfilled).
2. **Kept against skipped,** taker and passive, overall and within |x| terciles (the size check).
3. **The cost of waiting:**
   - the 09:31 taker book against the 09:46 taker book on the same sessions;
   - the side-signed 09:31 → 09:46 move, kept against skipped.
4. **Splits:**
   - EST against EDT;
   - Dec–Mar against Apr–Nov;
   - by year;
   - before and after the SHFE day-session auction (2023-05-26). That split matters most here, since the condition
     reads the open's first 45 minutes.
5. **The four groups** for every gated book:
   - net and gross, Sharpe and Sortino annualised by the book's own trades a year;
   - the trade distribution with the three 1% trimmed means;
   - profitable years, net without the best year, the five best and worst trades;
   - the null's p50 and p95.
6. **The component line** for the K1 passive book:
   - net Sharpe at its cost, hit rate, skew, gross beside net;
   - daily ρ with the unfiltered D765 MGC fade, D775 and D777's MNQ book (as D786);
   - D755's other-lines file no longer exists.

## 6. Runner assertions

- **Right quantity, first:**
  - D786's build reproduces D767's taker pool and D770's passive book exactly;
  - the 09:46 taker book on every valid session differs from the 09:31 book;
  - the new passive book at 09:45 differs from D770's at 09:30.
- **Outcome-blind condition:** the K1 and K2 flags are built from prices stamped no later than 09:45, asserted by a
  price reader that raises on any later request.
- **The lag audit,** a second implementation on 40 sampled sessions:
  - PEAK/TROUGH and P(09:45) by explicit loops over the bar arrays;
  - the 09:45 resting fill by an explicit loop over the raw tbbo records (as D770's `audit_session`).
- **The sign audit in money:** a filled passive sell followed by a fall pays; a mirrored book raises.
- **The rotation:** offset 0 reproduces the observed statistic; exactly n − 1 offsets are enumerated; processes over
  offsets[i::N], with chunk == whole proven bit-identically in the self-test.
- **The seal:** a planted 2024 row raises in the bar reader, the paid reader and the session tables.
- **The self-test:**
  - a planted path where a turned open reverts and an extended one continues passes N;
  - a shuffled flag fails it;
  - a K1 flag built with P(09:46) in place of P(09:45) is caught by the outcome-blind reader.

## 7. Output, and the decision it feeds

- `scripts/stage0_d787_china_open_turned_fade.py`; `data/stage0_d787_china_open_turned_fade.json` (statistics only).
  The result is a separate record.
- **If K1 passive reads SUPPORTED:** recommend a pre-registered 2024+ confirmation, split at the SHFE auction change,
  with its power stated. The principal decides.
- **Otherwise:** the confirmation entry is recorded at its measured size, and the China-open fade's in-sample stays
  where D770 left it: positive gross, negative net at micro cost.

## Amendment (2026-10-03, before any runner or data read): reworked into a disclosed in-sample exploration grid

*The principal: "Why is anything froxen?", then "Yes, rework it into the grid and run it".*

- **Why:** RULES.md (the correction to R14 at lines 751–772): "in-sample numbers are free for SELECTION and expensive
  as EVIDENCE", and the ledger counts holdout reads, not in-sample looks.
  - R8 binds the withheld data only. This slice has already been read for this fade, so a single frozen cell buys
    nothing. Freezing belongs to the one 2024+ read, if any.
  - This record therefore becomes TRIAGE: does any cell deserve a holdout read?
- **Superseded:** the single primary, the nomination rule and the four-look restriction (§3 "Nomination") are
  withdrawn.
- **Kept:** the construction, the gates as readings, the controls, the null, the safeguards (§6) and the seal.
- **The grid, every cell reported (no cell is dropped after seeing):**
  - **delay L after 09:30:** 5, 10, 15, 20, 30 minutes. The check is at T = 09:30 + L; the taker enters at the open of
    the bar at T + 1; the passive book rests at the touch at T, filled on a trade-through within 30 minutes, exit at
    the 15:00 touch;
  - **the condition:**
    - K1c: back inside the extreme, with the extreme the maximum (minimum) one-minute close, 09:01–09:30;
    - K1h: the same, with the extreme the 1-minute bar high (low) over the bars 09:00–09:29;
    - K2: past the 09:30 price;
  - **the book:** passive and taker.
  - That is 5 × 3 × 2 = 30 cells.
- **The controls:** each delay × book unconditionally, on the same valid sessions (10 control rows). L = 0 is run
  too, as a reproduction check only: unconditional, it must reproduce D767's taker book and D770's passive book
  exactly.
- **Per cell:**
  - the kept count and share;
  - kept, skipped and control: mean gross, mean net, t;
  - kept minus control;
  - the gates as readings (G1, N, Y, G2);
  - B1 and the net outside Dec–Mar.
- **The null:**
  - each cell's flag is rotated exactly over the candidate sequence (all n − 1 offsets);
  - the cell's statistic is Σgross / Σ|gross| over kept ∩ valid, with its p95 and rank;
  - **a family-max null across the 30 cells:** the same offset rotates every cell's flag. For each offset, the
    largest within-cell percentile across cells forms the distribution that the observed best rank is compared
    against. This is the grid's own multiplicity, stated in the result.
- **For the best passive cell and the best taker cell (by family-adjusted rank):**
  - the four groups;
  - kept against skipped within |x| terciles;
  - the EST/EDT, season, year and SHFE-auction splits;
  - the component line.
- **What a cell needs to justify a 2024+ read (stated now, a triage bar, not admission):**
  - passive, N above its own p95 AND the family-max p95;
  - G2's net t ≥ 2;
  - Y passes.
  - If a cell clears it, the result recommends one frozen cell for a separately pre-registered holdout read, with the
    grid disclosed. The principal decides.
- **Output:** as §7.
