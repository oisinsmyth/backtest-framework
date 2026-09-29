# D678 — PRE-REGISTRATION: going with the overnight gap through yesterday's day-session range at the open, on HO, RB, BZ, HG and PL, five roots never run through the break

*2026-09-29.*
- *The principal: "Ok do the fix then the test", after D677's lead (a) was recommended as the one thread worth a
  single test.*
- *Numbered D678: D676 and D677 are this session's; no other branch holds D676+.*
- ***Committed alone, before its runner and before any outcome on these roots is read.*** *The one-minute fixture is
  being built as this is written. The build reads no outcome.*

## 1. The claim and where it comes from

- **D677 §4 (post hoc, on CL, NG, GC and SI):**
  - when the day session **opens already through** yesterday's day-session high + 0.25 A (or low − 0.25 A), the break
    trade made +3.5 to +14.2 bp at the level, about 2–3.4% of ATR;
  - the **fresh intraday break** made −5.3 to +1.6.
- **D668's open classes point the same way on the index roots:** the "through" class was YM's best (+1.88 bp
  against +1.13 with no gap) and above RTY's no-gap class (+1.43 against −2.40), though RTY's "inside" class was
  higher (+1.89).
- **The mechanism story:** these roots trade about 23 hours, and their information (Asia, London, overnight inventory
  and macro news) arrives outside the CME day session.
  - A gap through yesterday's day range at the open is the overnight market's verdict, carried into the day session's
    liquidity.
  - A fresh intraday break of a stale day-session level is not.
- **The claim is a mechanism of the family of 23-hour energy and metals roots,** tested on five of them that no break
  construction has read.
- **It is not a CL/NG/GC/SI result re-dressed:** those four are spent and are not used here.

## 2. The rule, per root; nothing fitted (D676's levels and exit, unchanged)

| root | open | settlement | flat at (5 min before) | contract (full size) | tick | cost: $6 + measured crossing (`d507_exec`, round trip) |
|---|---|---|---|---|---|---|
| HO | 09:00 | 14:30 | 14:25 | 42,000 gal | 0.0001 ($4.20) | 12.25 ticks → $57.4 |
| RB | 09:00 | 14:30 | 14:25 | 42,000 gal | 0.0001 ($4.20) | 7.38 ticks → $37.0 |
| BZ | 09:00 | 14:30 | 14:25 | 1,000 bbl | 0.01 ($10) | 2.91 ticks → $35.1 |
| HG | 08:10 | 13:00 | 12:55 | 25,000 lb | 0.0005 ($12.50) | 2.26 ticks → $34.3 |
| PL | 08:20 | 13:05 | 13:00 | 50 oz | 0.1 ($5) | 8.75 ticks → $49.7 |

- **Settlement minutes** are from `cme_session_calendar.session_close_et` (14:29 / 12:59 / 13:04 last bars).
- **Opens** are the CME open-outcry openings.

**Levels (as D676):**
- yesterday's day-session high and low, from the open to the flat time, **on the same contract**;
- A = the 20-session ATR of the day session, prior sessions only.

**The trade:**
- If the open bar's **open** is above yesterday's high + 0.25 A, **buy at the open**. If it is below yesterday's
  low − 0.25 A, **sell at the open**. Otherwise no trade.
- One trade a session at most.

**Exit (E4, as D676):**
- initial stop at yesterday's level (L);
- trailing 0.25 A behind the best price;
- otherwise flat at the close of the flat-time bar.
- A stop fills at the stop, or at the bar's open if it opens through it.

**Friction, counted once (D668-A2):**
- trades are scored at the fill prices above, with no extra tick;
- each is charged $6 commission plus the root's **measured** round-trip crossing (`d507_exec`, execution hours,
  `data/futures_costs.json`), in bp of the entry.
- The file's default line for these roots (`d556_one_tick`, 1 tick) is not measured and is **not** used.
- **Sensitivity:** +1 tick on every fill.
- **Full size, not micro:** only HG has a micro, and the thread's premise (D677) is that micro commissions dominate.
- **Caveat:** the crossing was measured 2025-09 → 2026-09 and may not represent 2016–2024.

**Root-aware adjustments:**
- **R1, roll:** structural. Same-contract levels mean a roll session never trades.
- **R2, delivery (the principal's standing rule):** skip a session within 10 business days of:
  - HO and RB's last trading day (the last business day of the month before delivery);
  - HG and PL's first notice day (the last business day of the month before the contract month).
  - **BZ is financially settled:** no R2.
- **R3 and R4 are not applied.**
  - D677 found the index-roll window unsupported outside NG.
  - The trade enters at the open, before the 10:30 Wednesday EIA release. EIA days are reported separately for HO and
    RB.

## 3. Data (built before the run; no outcome read)

- **`fut_opening_globex_1m_ho_rb_bz_hg_pl`,** from the CME ohlcv-1m archive on disk, via `build_fut_opening_1m.py
  --roots HO,RB,BZ,HG,PL --breadth`: `%.5f` prices, the breadth front election, and no session on or after
  2025-03-01.
- **Gates before the run:**
  - **(i) Identity:** the fixture's bars from 09:00 to the flat time equal `fut_day1m`'s in OHLC. HG and PL's
    08:10/08:20 → 09:00 bars have no second source; their opens are checked for presence.
  - **(ii) Coverage:** a session missing its open bar, or with < 80% of its day minutes, is excluded and listed, by root
    and year.
  - **(iii) The seal.**
- **Window:** 2016-01-04 (after the ATR warm-up) → 2025-02-28.
- **Seals:**
  - the vault (2025-03-01 → 2026-09-18) is not read on any root;
  - HO/RB data after 2026-09-18 is D626's and is not read;
  - CL/NG post-vault data stays sealed until 2026-10-10 and is not used.

## 4. Statistics

**The unit.** Each trade's gross and net in bp and in % of its A. The family statistic works in % of A, so roots of
different volatility weigh alike.

**Gate 1, the MECHANISM (family):**
- **The statistic:** for each date, the mean gross (% of A) over the roots that traded; the family statistic is the
  mean over dates.
  - (a) > 0, one-sided HAC t (`R.nw_t`) on the date series, α = 0.05;
  - (b) above the **sign-flip null's** p95 by 2 bootstrap SE;
  - (c) > 0 without February–April 2020.
- **The sign-flip null:**
  - on the **same** gap days, each root's trade is replaced by a trade from the same open with a random side, with its
    own long share preserved;
  - the opposite side's initial stop mirrors the distance to L, and the trail and flat are the same;
  - **one uniform draw per date, shared by all roots** (root r goes long if u < its long share), so the energy roots'
    co-movement is kept and the null is not narrowed;
  - 10,000 draws, seed 678; the p95's SE from 500 bootstraps.
  - It shares the treatment's days, clock, gap size, stop distance and side mix. It breaks only the claimed ingredient:
    the gap's direction.

**Gate 2, TRADEABILITY** (per root, only if Gate 1 passes; Holm across the five):
- net > 0, one-sided HAC t;
- net > 0 at +1 tick on every fill;
- at least 100 trades;
- net > 0 without February–April 2020.

**Verdicts:**
- family: **MECHANISM** / **NO MECHANISM**;
- per root: **SUPPORTED** / **MECHANISM ONLY** / **NOT SUPPORTED**.

**The declared SECONDARY:** gap vs the fresh intraday break.
- The fresh break is D676's rule on the sessions that did not gap: the first break after the open, entered at the stop
  (no tick), E4, until 30 min before the flat time.
- Gap − fresh in % of A, per root and for the family, with HAC SEs.

**Per root, reported only:**
- the gross vs the root's own sign-flip null (p50, p95, rank);
- long / short;
- by year;
- gap size (through the stop by < 0.25 A vs more);
- EIA days (HO, RB);
- R2's removed trades against the kept;
- the four groups;
- the **component line:** daily $ Sharpe net at one full contract, gross beside it; ρ with the rebuilt K8 and between
  the five. The MACD arm (#2) and the NG winter spread (#3) are named as not rebuilt.

**The runner's assertions, each raising in `--selftest` on a broken input:**
- the ATR lag;
- a gap trade that is not entered at the open bar's open;
- a stop fill with an extra tick (the double count);
- a bar after the flat time;
- a session inside R2's buffer;
- the null's side mix differing from the book's by more than 0.02.

## 5. Power (rough, stated before the run)

**Assumptions:**
- per-trade σ ≈ 0.3 A (D677: 0.27–0.38);
- about 55 gap trades a root a year (D677: ~42% of D676's ~160 base breaks, less R2), so ≈ 500 a root over 9.15 years;
- ATR roughly HO 2.3%, RB 2.6%, BZ 2.1%, HG 1.6%, PL 1.6%.

**Family (Gate 1).** Five roots, about 2,500 trades; with the energy roots' co-movement, effective N ≈ 1,500:
- SE ≈ 0.8% of A;
- at D677's in-sample gap effect (≈ 2.8% of A), power ≈ 0.95;
- at half of it, ≈ 0.55.

**Per root (Gate 2):**

| | HO | RB | BZ | HG | PL |
|---|---|---|---|---|---|
| cost, bp (rough, at mean in-sample prices) | 6.2 | 4.4 | 5.4 | 4.3 | 10.5 |
| cost, % of A | 2.7 | 1.7 | 2.6 | 2.7 | 6.6 |

- Net at a 2.8%-of-A gross is about 0 to +1.1% of A (PL negative), with SE ≈ 1.3% of A a root.
- **Gate 2's power is below 0.10 on every root.**
- **This test answers whether the overnight verdict is a mechanism of these markets. It is very unlikely to certify a
  tradeable root, and the prize, if the mechanism is real, is thin.**

## 6. Predictions

1. **The family passes Gate 1.**
2. **No root passes Gate 2.**
3. **Gap − fresh > 0 on at least 4 of the 5 roots.**
4. **The gap trade's gross is > 0 on at least 4 of the 5 roots.**

## 7. Routing

- **MECHANISM:**
  - recorded as a property of 23-hour energy and metals;
  - the cheapest execution (full size, and the best-measured crossing) is the only lever;
  - a vault confirmation is proposed only for roots whose in-sample net is positive, and is left to the principal.
- **NO MECHANISM:** D677 lead (a) is closed. The opening-break line has nothing left on energy and metals.
