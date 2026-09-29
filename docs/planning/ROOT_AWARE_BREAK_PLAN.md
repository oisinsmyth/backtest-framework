# Plan: the root-aware break on CL, NG, GC, SI, ZN and ZB

*Recorded 2026-09-29 at the principal's request ("record that plan in a doc so we can reference that"). **This is a plan, not a pre-registration.** Nothing here has been tested. The pre-registration is written only after:*
- *D668's YM/RTY evidence run is finished (the principal: "wait for the current tests to finish");*
- *the three open decisions in §7 are made.*

*It will take the next free D-number. The other session holds D669 and D670, so D674 is the likely number.*

## 0. Where this comes from

- **D666/D667:** the plain break of yesterday's range with a trailing stop beats random entry at the same clock on ES and NQ (8 of 9 years). It pays on NQ only.
- **D671/D672:** a "compression" filter looked strong on NQ (+6.93 bp, Sharpe 0.97) but was found and checked on the same sample.
- **D673:** it **failed to transfer** to YM and RTY; RTY's compressed third was its worst. Split into halves, across all four index roots:
  - **quiet overnight** is positive gross on every root (NQ +7.3, ES +4.8, RTY +4.9, YM +3.3);
  - quiet recent days helped NQ only.

  That is a post hoc direction, not a result.
- **The principal's direction:** run *root-aware* versions on energy, metals and treasuries, allowing for "their particular flavour of index rotations, rolls and whatever else that can move the price".

**Why these six:**
- None has been run through this construction, so each is **clean evidence**.
- Energy has in-session information releases (EIA) and trend-chasing flow (CTAs, leveraged ETFs).
- The others are the contrasts: SI is high-beta and retail-heavy; GC is globally priced; ZN/ZB are rates, which mean-revert intraday.

## 1. The shared shape (the same on every root; nothing fitted)

| Part | Rule |
|---|---|
| Levels | Yesterday's **day-session** high and low. A = the 20-session ATR of the day session. |
| Entry | A stop at yesterday's high + 0.25 A and at yesterday's low − 0.25 A, armed from the root's day-session open (or later, where §2 says so). The first fill of the day, at the stop (or the open through it) plus one tick of the root's own size. |
| Exit | Initial stop at yesterday's level. The stop then trails 0.25 A behind the best price. Otherwise flat **5 minutes before the root's settlement minute** (§2). |
| Size | One contract. Micros: MCL, MNG, MGC, SIL. **ZN/ZB are full-size only** (no micro line in `futures_costs.json`); see §7. |
| Cost | `futures_costs.json`, each root's default line (MCL `d508_exec` 2.03 ticks; MGC `d508_exec` 2.93; MNG/SIL/ZN/ZB the `d556` one-tick convention) + $3 commission + one tick of stop slippage. |
| Primary | The plain break **with the root-aware adjustments of §2** (decision §7-1). |
| Declared secondary | The **quiet-overnight** filter. It trades only when the walk-forward percentile of the overnight two-way range (18:00 → the day-session open) is in its quietest third. |

## 2. Root-aware adjustments, declared from mechanism before any data is read

| Force | Roots | Mechanism | Handling |
|---|---|---|---|
| **Contract rolls** | all | A return across a roll is a roll, not a move | Skip roll sessions (`same_front` False) |
| **Physical delivery** | CL, NG, GC, SI, ZN, ZB (treasuries are physical too) | Delivery-month liquidity and squeezes | Never hold a contract within 10 business days of its first notice (the principal's standing rule). Assert it against `days_to_expiry` and the settlement strip. |
| **Commodity-index rolls** (GSCI business days 5–9, BCOM 6–10) | CL, NG, GC, SI | Index funds sell the front month and buy the next: mechanical, front-month pressure | **Skip in the primary** (decision §7-2); report the window as a split |
| **Leveraged-ETF and ETF rolls** (USO/UNG; BOIL/KOLD, UCO/SCO at BCOM business days 5–9, per the settlement ledger) | CL, NG | The same front-month pressure, partly overlapping the index windows | Reported as a split |
| **EIA reports** (crude Wednesday 10:30, gas storage Thursday 10:30; `data/calendar/events.csv`: EIA_WPSR 573, EIA_NGSR 574) | CL (WPSR), NG (NGSR) | The day's information arrives at 10:30 | On report days, arm the break **only after the release** (10:31). Breaks before the release on those days are not taken. |
| **FOMC** (14:00) | ZN, ZB, GC | The expansion arrives at 14:00 | Flat before 14:00 on FOMC days (`cme_session_calendar.fomc`) |
| **CPI / employment situation** (08:30) | GC, SI, ZN, ZB | Released before or at the metals/treasury open; already in the opening price | Reported as a split (`cpi`, `empsit`) |
| **Settlement window** (TAS and settlement flows, D625–D627) | all | The flows that set the settlement are not the trend | Exit 5 minutes before each root's settlement minute (`cme_session_calendar.session_close_et`): CL/NG 14:30, GC 13:30, SI 13:25, ZN/ZB 15:00 |
| **Month-end index extension** | ZN, ZB | Bond indices extend duration at month-end, so there is mechanical duration demand | Reported as a split (the last business day of the month) |
| **Treasury auctions** (13:00) | ZN, ZB | Supply events | **Not on disk.** Named as a limitation, not used |
| **Trail width** | NG | NG's intraday noise is far larger than the index roots' | One declared variant at 0.5 A, reported and never gated |

## 3. Data

**On disk and committed:**
- `fut_day1m.parquet`: one-minute bars, 09:00–15:59 ET, all 36 roots, with the front from `fut_breadth_hourly` and the `same_front` and `present` flags;
- `fut_breadth_hourly.csv.gz`: hourly OHLC 18:00 → 16:59, for the overnight range;
- `cme_session_calendar.csv.gz`: settlement minutes, roll and expiry days, and the FOMC/CPI/employment flags;
- `fut_settle_strip.csv.gz`;
- `data/calendar/events.csv`: the EIA release times.

**The gap:**
- The one-minute fixture starts at 09:00, but **metals and treasuries open at 08:20**, so their first 40 minutes are missing.
- Plan: build an **08:00-onward one-minute fixture for GC, SI, ZN and ZB** from the CME ohlcv-1m archive on disk, with the same front and id rules, in about 20–30 minutes.
- Gates, before any outcome:
  - identity with `fut_day1m` on the overlapping minutes;
  - coverage by year, using each root's `first_clean_year`;
  - the seal.
- Energy's 09:00 open is already covered.

**Windows and seals:**
- The in-sample window is from each root's first clean year (CL is gated to 2016-01-04 by `fut_sessions_hourly` G5) to **2025-02-28**.
- **The vault is not read.** CL/NG post-vault data stays sealed until D626's read on 2026-10-10.
- HO/RB (D626's sibling year) are not used.
- Nothing from SqueezeMetrics is needed.

## 4. Statistics (the D673 standard)

- **Gate 1, the mechanism:** the root-aware break's gross against **N1**, a random entry on every session at the break's own clock distribution and side mix, with the same exit (D668 §5), p95 + 2 SE. Its gross > 0, HAC t. Holm across the six roots.
- **Gate 2, tradeability:** net > 0 (HAC t); above a within-year random-subset placebo; still > 0 at +1 tick; at least 60 trades; positive without February–April 2020.
- **The quiet-overnight secondary:** tier − rest against an enumerated rotation of the tier.
- **The four groups** for every book, and **by year**.
- **The component line:** daily $ Sharpe, and ρ with K8, with the **NG winter-spread** ledger entry (#3) and between the roots.
- **Every root-aware skip reports what it removed:** a skip is kept only if what it removes loses (the D671 lesson).

## 5. Predictions, from the root stories (to be restated in the pre-registration)

1. **NG and CL carry:** Gate 1, and possibly Gate 2 on NG, whose cost/ATR is small.
2. **SI is marginal:** gross positive, net not.
3. **GC, ZN and ZB are flat:** globally priced, and treasuries mean-revert intraday.
4. **The quiet-overnight secondary** points the same way as on the index roots, on at least 4 of the 6.
5. **The EIA arm-after-release rule** beats breaks taken before the release on report days (CL, NG).

## 6. Order of work (after D668's YM/RTY run)

1. Build the 08:00 metals/treasury one-minute fixture, and pass its gates (about 30 min).
2. Write the pre-registration (D674 likely), with the §7 decisions filled in. **Committed alone, after the principal's review.**
3. Write the runner and its selftest (lag, sign, quantity, root tick, delivery buffer, the EIA arm time, the settlement-exit canaries). About 45 min.
4. One run (about 5 min).
5. A RESULT record.

## 7. Open decisions (for the principal)

1. **The primary rule:** the root-aware plain break, with quiet-overnight as a secondary (recommended), or quiet-overnight as the primary?
2. **Index-roll windows:** skip them in the primary (recommended), or report them as a split only?
3. **ZN/ZB at full size:** acceptable (their dollar risk per trade is several times a micro index's), or leave treasuries out until a micro-equivalent cost line exists?

## 8. Decisions (the principal, 2026-09-29)

> "On the first two, I'll go with your recommendations. and will defer the treasuries until later"

1. **The primary rule is the root-aware plain break.** The quiet-overnight filter is the declared secondary.
2. **Index-roll windows** (GSCI business days 5–9, BCOM 6–10) are **skipped in the primary** and reported as a split.
3. **Treasuries (ZN, ZB) are deferred.**

**The scope is therefore CL, NG, GC and SI.** Consequences for the plan:
- **§3:** the 08:00 one-minute build is needed for **GC and SI** only.
- **§2:** the FOMC flat-before-14:00 rule applies to GC only. The month-end-extension and auction rows fall away with the treasuries.
- **§4:** Holm runs across the four roots.
- **§5:** prediction 3 covers GC alone.
