# D494 — PRE-REG: direction from outside the price path on the day session — cross-instrument overnight moves, index-level retail sentiment, and release days as a gate on the MACD

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D494-PRE-REG-direction-from-outside-the-price-path-on-the-day-session-cross-instrument-overnight-moves-index-level-retail-sentiment-and-release-days-as-a-gate-on-the-MACD.md`. The H1 above is the full title.*

**2026-09-12. Committed before the runner exists (R8).** The principal: *"all in on the prop
book"*; D473's structural conclusion: ES is a random walk at every intraday scale on its own
path, so *"direction has to come from outside the price path."* One stage 0, one declared family,
three sub-families, all on the **day session**, all **one round trip a session**, scored in
dollars at one micro under the $3 round trip. **In-sample 2016-01-04 → 2023-12-29 on the D467
hourly tables; 2024 onward sealed; no holdout of any line touched; nothing admitted.**

## 1. Data (all committed or public and recorded)

- `data/fixtures/fut_sessions_hourly.csv.gz` (D467): hourly OHLC, 18:00 → 16:59 ET sessions,
  ES NQ YM ZN ZB GC CL 6E (RTY held back on G2), front by volume, `same_front` rows only.
- `data/raw/robintrack/popularity_export/` (gitignored, 2026-09-12): hourly Robinhood holder
  counts, 2018-05-02 → 2020-08-13; the two site outages masked.
- `data/macro_release_calendar.json` (this commit): FOMC statement days 2016–2024 (scheduled;
  the three unscheduled listed and excluded), CPI and Employment Situation release days
  2016–2023, read from the Fed's and the BLS's own pages; the 34 Nasdaq-100 core members that
  were in the index for the whole Robintrack span.
- D484's signal code (`scripts/d484_offdiagonal_and_macd.py`: `macd_hist`, `series_for`) —
  imported, not re-implemented.

## 2. The target, common to every cell

**The day leg:** enter at the 10:00 ET print (`h09_c`, the last minute of the 09:00 bar), exit at
the 16:00 print (`h15_c`), on ES and NQ. Every predictor below is known by 09:00 ET. One round
trip; flat before every venue's flatten time. P&L in dollars at one micro (MES $5, MNQ $2 a
point), net = gross − $3.

## 3. The three sub-families

**B1 — cross-instrument overnight moves (10 cells).** Predictor: the overnight log return
18:00 → 09:00 (`h18_o` → `h09_o`) of each of **ZN, ZB, 6E, GC, CL**, on the same session date.
Two targets (ES, NQ). No sign is assumed: the statistic is two-sided (§4).

**B2 — index-level retail sentiment (2 cells, 2018-05 → 2020-08 only).** Predictor: the
equal-weighted mean across the 34 core NQ members of the log change in `users_holding` from
the last observation ≤ 16:00 ET of session t−1 to the last observation ≤ 09:00 ET of session t;
sessions with an outage or fewer than 30 of 34 names are dropped and counted. Targets ES, NQ.
Weak prior, said so in advance; the ten-year RTAT version is a separate record once a key exists.

**B3 — release days as a gate on the MACD (6 cells).** D484's plain log-MACD histogram sign
(B2 there) on ES and NQ, evaluated at the 09:00 bar, traded on the day leg. Gate: the session
is (i) a CPI release day, (ii) an Employment Situation release day, (iii) a scheduled FOMC
statement day. The question is not the MACD's edge (D484 has it) but whether the edge is
**different on event days**: statistic = mean signed P&L on gated days − mean on a
**calendar-matched control** (the same weekday, non-event sessions, weighted to the gated
sessions' year distribution — a partner randomisation, not a re-drawn subset, D291). FOMC days
put the 14:00 announcement inside the hold; that is the point.

## 4. Statistics and nulls (declared)

- **Per cell:** n, gross and net mean $/session, monthly-block SE, median, hit rate, 1% symmetric
  trim, worst session, Spearman(predictor, move), and the **side difference** = mean day-leg
  move when the predictor is in its top tercile − bottom tercile, in $ at one micro (B1, B2);
  for B3 the gated-minus-control difference above.
- **N1, exact:** the predictor series rotated against the fixed target by every k ∈ [1, T−1]
  sessions (T ≈ 2,000; enumerated; SE 0). For B3 the gate mask is rotated.
- **N2, family maximum:** common-offset maximum of |side difference| (B1, B2) and of
  |gated − control| (B3) over **all 18 cells** — one bar for the whole record; the three
  sub-family maxima reported beside it.
- **Pass (a pick, not a component):** |statistic| above N1's p95 **and** above the 18-cell
  family-max p95, with the sign then declared for the reserve. A pick goes to the 2024+ slice
  only on the principal's word.
- **Audits:** [S] sign in money; [M] vectorised == loop; [F] every predictor is stamped ≤ 09:00
  ET and the target starts at 10:00 (asserted on the column choice, and a shifted-predictor
  control — predictor from session t+1 — must destroy nothing and everything, i.e. its own
  statistic sits inside the null); [X] a flipped predictor sign must negate the side
  difference exactly; [C] the calendar: every FOMC day is a Wednesday except the listed
  exceptions, every Employment Situation day a Friday except the listed exceptions (2016-01-08
  onward), asserted; [D] no session date after 2023-12-29 reaches the runner.

## 5. Predictions

1. **B1:** no cell clears the 18-cell family bar. The largest |side difference| is a bond
   predictor (ZN or ZB) on NQ, $10–30 a session at one MNQ, with N1 p95 near $15–25 and the
   family-max p95 near $30–45.
2. **B2:** inside noise both ways (n ≈ 550 sessions; SE of the side difference ≈ $25 on MNQ);
   |side difference| < $30.
3. **B3:** event days have a larger |move| (σ 1.4–2× the control) and a mean signed P&L that is
   **not** different from the control at 2 SE on five of six cells. If one cell differs, it is
   FOMC on NQ, and the difference is within its own N1 p95 once the family bar is applied.
4. The sub-family maxima are all below the 18-cell p95; the record's yield is a measured
   ceiling for "outside the price path" on the day session at this resolution, to be read
   against D493's gross-per-trade target.

## 6. What this record does not do

Nothing enters `COMPONENTS_PROP.md` or either book; the 2024+ slice is not read; the single-name
Robintrack herding test (personal book) is a separate draft and not run here; no RTAT data exists
in the repo.
