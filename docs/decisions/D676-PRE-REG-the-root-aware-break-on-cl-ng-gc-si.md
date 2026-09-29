# D676 — PRE-REGISTRATION: the root-aware break of yesterday's day-session range on CL, NG, GC and SI, four roots never run through it

*2026-09-29.*
- *The plan is `docs/planning/ROOT_AWARE_BREAK_PLAN.md` (`ea05c32b`, decisions `5a6f0fe9`).*
- *The principal's decisions:*
  - *the primary is the root-aware plain break, with quiet overnight as the secondary;*
  - *index-roll windows are skipped in the primary;*
  - *treasuries are deferred;*
  - *"queue the data needed for the root-aware test — then run the insample tests on the data that is on the disk".*
- *Numbered D676 because the other session holds D674 and D675.*
- ***Committed alone, before its runner and before any outcome on these roots is read.***

## 1. Why these roots, and what the index roots taught

- **The plain break beats random entry at the same clock on NQ (+3.9 bp) and ES (+2.1), and barely or not at all on
  YM (+1.2) and RTY (+0.8)** (D668's evidence run). The edge follows the root's participants and information
  structure; it is not a property of futures.
- **Energy and metals:**
  - they have in-session information (EIA: crude on Wednesday 10:30 ET, gas storage on Thursday 10:30 ET);
  - trend-chasing flow (CTAs; the UCO/SCO and BOIL/KOLD leveraged ETFs);
  - and mechanical front-month flows (index and ETF rolls).
- **None of the four has been run through this construction.** Their in-sample data is clean evidence.

## 2. The rule, per root; nothing fitted

**Sessions (ET), from `cme_session_calendar.session_close_et` and CME's day-session opens:**

| root | open (arm) | settlement minute | flat at (5 min before settlement) | last entry | micro | tick | cost line (`futures_costs.json`) |
|---|---|---|---|---|---|---|---|
| CL | 09:00 | 14:30 | 14:25 | 13:55 | MCL | 0.01 ($1) | `d508_exec` 2.031 ticks |
| NG | 09:00 | 14:30 | 14:25 | 13:55 | MNG | 0.001 ($1) | `d556_one_tick` |
| GC | 08:20 | 13:30 | 13:25 | 12:55 | MGC | 0.1 ($1) | `d508_exec` 2.933 ticks |
| SI | 08:25 | 13:25 | 13:20 | 12:50 | SIL | 0.005 ($5) | `d556_one_tick` |

**Levels:**
- yesterday's **day-session** high and low, from the open to the flat time, on the same contract;
- A = the 20-session ATR of the day session (high, low, and the close at the flat time), prior sessions only.

**The break:**
- a stop at yesterday's high + 0.25 A and at yesterday's low − 0.25 A, armed from the open;
- the day's first fill, at the stop (or the open through it) + one tick;
- no entry after the last-entry time.

**The exit (E4):**
- initial stop at yesterday's level, then trailing 0.25 A behind the best price;
- otherwise flat at the close of the bar starting at the flat time;
- stops fill at the stop (or the open through it) − one tick.

**Cost:** one micro. $3 commission + the crossing + one tick of slippage, in bp of the entry.

## 3. Root-aware adjustments (primary; each declared from its mechanism)

| # | adjustment | roots | rule |
|---|---|---|---|
| R1 | **roll** | all | Skip a session whose front (`fut_breadth_hourly`) differs from the previous session's; yesterday's range would be another contract's |
| R2 | **delivery buffer** (the principal's standing rule) | all | Skip if the session is within 10 business days of the front's first notice day, or of its last trade date if earlier. CL/NG: `cme_session_calendar.days_to_expiry` ≤ 10. GC/SI: first notice day = the last business day of the month before the contract month |
| R3 | **commodity-index roll window** (GSCI business days 5–9, BCOM 6–10 → business days 5–10) | CL, NG: every month. GC: Jan, Mar, May, Jul, Sep, Nov (the months before its active contracts Feb/Apr/Jun/Aug/Oct/Dec). SI: Feb, Apr, Jun, Aug, Nov (before Mar/May/Jul/Sep/Dec) | **Skip** (the principal's decision 2). Business days are counted on the root's own session calendar. An approximation of the published schedules, stated as such |
| R4 | **EIA release** (`data/calendar/events.csv`: EIA_WPSR for CL, EIA_NGSR for NG, each release's own `datetime_et`) | CL, NG | On a release day the break is armed only from **the release minute + 1**. A fill before it is not taken |

**Considered and dropped:** the plan's FOMC rule for GC falls away, because GC's day session ends at 13:30, before the
14:00 statement.

**Every adjustment reports what it removed:** the E4 gross and net of the trades it skipped, against what it kept (the
D671 lesson).

## 4. Data (built before the run; no outcome read)

- **`fut_opening_globex_1m_cl_ng_gc_si`**, from the CME ohlcv-1m archive on disk, via `scripts/build_fut_opening_1m.py
  --roots CL,NG,GC,SI --breadth`:
  - the breadth builder's windowed id table and front election;
  - sessions from 18:00 on the previous calendar day through 16:59;
  - no session on or after 2025-03-01.
- **Gates before the run:**
  - **(i) Identity:** the fixture's 09:00 → flat-time bars equal `fut_day1m`'s on the same (root, day, minute), in
    OHLC.
  - **(ii) Coverage:** by root and year. A session missing its open bar, or with < 80% of its day-session minutes, is
    excluded and listed.
  - **(iii) The seal.**
- **Windows:** from each root's first clean year in `fut_day1m`'s coverage, and never before 2016-01-04 (CL is gated
  there by `fut_sessions_hourly` G5), after the ATR20 warm-up, through 2025-02-28.
- **Seals:** CL/NG post-vault data stays sealed until D626's read on 2026-10-10. The vault (2025-03-01 → 2026-09-18) is
  not read on any root. HO/RB (D626's sibling year) are not used.

## 5. Statistics

**Gate 1, the MECHANISM** (per root, primary book, E4 gross; Holm across the four):
- gross > 0, one-sided HAC t;
- above **N1**'s p95 by 2 bootstrap SE. N1 draws, on every eligible session, a random entry minute from the root's
  own break-entry minutes and a side at the break's long share, with the same exit (D668 §5); 1,000 draws, seed 676;
- gross > 0 without February–April 2020.

**Gate 2, TRADEABILITY** (on a root that passed Gate 1; Holm across the Gate-1 roots):
- net > 0, one-sided HAC t;
- net > 0 at +1 extra tick on every fill;
- at least 100 trades;
- net > 0 without February–April 2020.

**Verdicts:** SUPPORTED / MECHANISM ONLY / NOT SUPPORTED, each with its power (§7).

**The declared SECONDARY (quiet overnight):**
- the overnight two-way range = (the high − low of the session's bars from 18:00 to the minute before the open,
  − |open − the previous flat-time close|)/A;
- its walk-forward percentile among the root's previous 250 sessions;
- the quietest third against the rest (E4 gross), against an enumerated rotation of the tier (rank and p95).

**Reported only:**
- **what each adjustment R1–R4 removed**, and the book without each (one at a time);
- **NG with a 0.5 A trail** (declared variant);
- **CPI and employment-situation days**, GC and SI;
- **long / short**;
- **the E2 exit** (stop at yesterday's level, flat at the flat time);
- **by year**;
- **the four groups** for the primary book;
- **the component line:** daily $ Sharpe at one micro; ρ with the rebuilt K8, with the NG winter-spread ledger entry
  (#3; rebuilt if its daily P&L can be, else named missing), and between the roots.

**The runner's assertions, each raising in `--selftest` on a broken input:**
- the lag audit on the ATR, the levels and the tier;
- the fill tick per root;
- the EIA arm minute (a pre-release fill must be refused);
- the delivery buffer (a session inside it must be refused);
- the flat time (no bar at or after it is used for the exit);
- the overnight window ending before the open.

## 6. Predictions (from the root stories)

1. **NG and CL pass Gate 1.** Information arrives in-session, and the flows chase it.
2. **SI:** gross > 0 but fails Gate 2 (the SIL cost).
3. **GC fails Gate 1.** It is globally priced, like ES and YM.
4. **The quiet-overnight secondary has positive tier − rest on at least 3 of the 4.**
5. **On EIA days (CL, NG), breaks taken after the release beat the pre-release breaks the rule refuses.**

## 7. Power (assumed per-trade σ ≈ 0.3 × ATR, as NQ's 45 bp on about 150 bp; ≈ 150 trades a year; about 8–9 in-sample years, fewer after the skips)

| root | ATR (bp, rough) | σ per trade | trades (after skips, ≈ 60–70%) | MDE (80%, Holm α 0.0125) | NQ-equivalent effect (2.9% of ATR) |
|---|---:|---:|---:|---:|---:|
| CL | ≈ 250 | ≈ 75 bp | ≈ 850 | ≈ 7.9 bp | ≈ 7 bp (power ≈ 0.7) |
| NG | ≈ 450 | ≈ 135 bp | ≈ 850 | ≈ 14 bp | ≈ 13 bp (≈ 0.7) |
| GC | ≈ 100 | ≈ 30 bp | ≈ 900 | ≈ 3.1 bp | ≈ 2.9 bp (≈ 0.7) |
| SI | ≈ 200 | ≈ 60 bp | ≈ 900 | ≈ 6.2 bp | ≈ 5.8 bp (≈ 0.7) |

**Costs against ATR:** about 3.4% (CL), 3.7% (NG), 3.5% (GC) and 2.6% (SI), against NQ's 1.7%. **Gate 2 is
harder here than on NQ.**

## 8. Routing

- **SUPPORTED on any root:** a component candidate. The vault's joint run is its confirmation (CL/NG only after
  2026-10-10). No physical contract is held near delivery (R2).
- **MECHANISM ONLY:** recorded, with the cost failure named. A cheaper execution route is the only lever.
- **NOT SUPPORTED on all four:** the opening-break line closes on energy and metals as it did on the index roots
  (D668, D673).

## Amendment D676-A1, before the run (2026-09-29): R2 counts business days

§3 R2 states the principal's rule as "within 10 **business** days". For CL/NG it then names
`cme_session_calendar.days_to_expiry` ≤ 10. That field counts **calendar** days: CLG9 reads 20 on 2019-01-02
and expired on 2019-01-22.

**R2 is therefore implemented as the rule states:**
- **CL/NG:** the expiry date is the session plus `days_to_expiry` calendar days. The session is skipped when 10
  weekdays or fewer remain to it.
- **GC/SI:** the same count, to the first notice day.

**Context:** the front election already rolls CL about 4 business days before expiry. So R2 skips about the last week
of each CL/NG front.

**Written after** the runner's selftest (4 canaries fire), and **before** its data gates or any outcome on these roots.
