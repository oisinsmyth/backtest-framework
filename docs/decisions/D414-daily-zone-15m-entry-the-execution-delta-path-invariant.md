# D414 — daily zone, 15-minute entry: the execution delta, path-invariant

**Status:** design and bar committed BEFORE the runner exists (R8). Result separately.
**Date:** 2026-09-10
**Area:** Strategy research · execution

**Number.** `D414`, by PICKUP's three-command procedure: D400–D413 used, `D407–D410` reserved
(`044f839`), `D390–D399` reserved for `worktree-signal-hunt-part2` (`945cbb5`, live 13 hours ago).
Master takes D414.

---

## 1. WHAT THIS CAN AND CANNOT BE — decided by a count, before the design

This is the step D403 named on its first line: *draw the map daily, trade it on 15 minutes.* The
construction is D413's distance-armed departure zone; the question is what a 15-minute entry buys
over a daily-close entry on **the same events**.

**The 15-minute fixtures decide the scope, and they decide it narrowly:**

```
cell 2, full universe                         26,024   gross +30.26 +-3.74 bp
cell 2 & 15m names                             2,409
cell 2 & 15m names & >= 2018                   1,357   gross  -2.20 +-17.07 bp
ALL zones & 15m names & >= 2018                4,528   gross -11.48 +-10.31 bp
```

Thirty-two names, **survivor-only and not by choice** (the fixtures' own metadata: the intraday
endpoint refuses delisted tickers), 2018 onward. [ADDENDUM 1](D413-ADDENDUM-the-distribution-the-confounds-resolved-and-the-cost.md)
found the daily edge concentrated in cheap names and in 2010–2013; these are large caps from 2018.
**On the only data where 15-minute bars exist, the daily signal is not visible, and at ±17 bp it
cannot be refuted either.**

**So D414 does not test the signal.** It tests **execution**: a paired comparison of two entries on
identical events, whose difference has far lower variance than either leg because it is a property
of the price path in the hours around a touch, not of the signal. That number is needed whichever
universe the signal is eventually confirmed in, and this is the only place it can be measured.

**The signal's own confirmation is a separate act on a separate fixture** (`holdout2`, unspent, not
read here) and nothing in D414 substitutes for it.

---

## 2. Data, and the window that stays shut

| | |
|---|---|
| daily | `us_shorts_daily_raw.csv.gz`, zones exactly as D413 (`delta = 1.0`, `theta = 1.0`, `life = 60`) |
| 15m | `cohort3_intraday_15m_raw.csv.gz` (8 names) and `cohort4_intraday_15m_raw.csv.gz` (24), regular session 09:30–15:45, 26 bars, **timestamps mark the interval's OPEN** — a bar stamped `t` is not complete until `t + 15m` |
| **MINING** | **2018-01-02 → 2023-12-31** |
| **RESERVED** | **2024-01-01 → 2026-08. Untouched.** D383 reserved it on its ETF panel and D403 inherited the same line for these cohorts; D414 keeps it, and it is this study's out-of-sample window if the mining window clears |

---

## 3. THE PAIRED OBJECT

For every D413 zone whose first touch falls on day `t` in the mining window on a 15m name:

```
E_daily   enter at C[t], the touch day's daily close           -- D413's entry, unchanged
E_15m     enter on day t at the FIRST 15m bar trading into the zone
            (a) MARKET   at that bar's close                       -- conservative: crosses the spread
            (b) LIMIT    at the zone's near edge (H_u for demand,   -- optimistic: filled at the edge
                         L_u for supply), which every touch reaches    with no queue
```

**Both exit at the close of daily bar `t + 5`.** With the exit held fixed the exit cancels, and the
paired delta is nothing but the entry:

```
delta = sign * ( log C[t] - log P_entry )         positive = the 15m entry was BETTER
```

This is the intraday move from the touch to the close, in the zone's direction. **It is exactly the
component the daily-close entry throws away** — or the loss it avoids. D413's hold sweep found
`h = 1` underperforming `h = 2` per bar, which is a hint about its sign.

**THE DIRECTION IS DECLARED HERE:** the trading claim is that the touch is the better entry, so
**`delta` is expected POSITIVE.** My own prediction is in §7 and it is not the same thing.

**Path-invariant throughout.** Every touch is scored as its own trade; no slot cap, no book, no
refill. CLAUDE.md §"both lenses" — this is the per-trade lens only.

---

## 4. THE BASIS, WHICH IS WHERE THIS STUDY CAN DIE SILENTLY

The daily fixture and the 15m fixtures are **not on the same price basis** — D403 found ServiceNow
at five times its own prices and Illumina at 0.97276 under `raw_price_factor`, which cannot repair a
spinoff. The zone is in the daily basis; the touch has to be found in the 15m one.

The repair is D403's, reused: **`phi[t] = (15m last close of session t) / (daily close of t)`**,
per session, forward-filled, units not information. The zone `[L_u, H_u]` is carried into day `t`'s
15m basis as `[L_u, H_u] * phi[t]`.

- **`[ALIGN]`** — D403's assertion, unchanged: after the repair, the median 15m/daily ratio per name
  is within 0.5% of 1.0 and fewer than 1% of sessions differ by more than that.
- **`[BASIS]`** — for every event, **`phi[u] == phi[t]`**: no corporate action landed between the
  zone's creation and its touch. Events that straddle a step are **dropped and counted**, not
  repaired.
- **`[SAME-DAY]`** — the first 15m bar trading into the zone must fall on the daily touch day `t`.
  If the daily bar says the low reached the zone and the 15m bars say otherwise, the basis is wrong,
  and the runner stops rather than quietly using a different day.

---

## 5. THE BAR

| | condition |
|---|---|
| **G1** | `[ALIGN]`, `[BASIS]`, `[SAME-DAY]` all hold; at least **500** paired events survive |
| **T1** | mean `delta` (market arm) **> 0 by more than 2 paired SE** |
| **T2** | mean `delta` (limit arm) **> 0 by more than 2 paired SE** |
| **N** | both arms **net of cost**, reported beside gross: market pays a half-spread at entry; limit pays none. The spread is the **neutral** Corwin–Schultz of [ADDENDUM 2](D413-ADDENDUM-2-the-cost-estimate-was-wrong-and-path-efficiency.md), not the event-bar one |

**T1 is the honest bound and T2 the optimistic one.** A resting limit at the edge assumes the fill
with no queue; a market order at the touch bar's close assumes the worst of the bar. Reality sits
between, and **both are reported whatever they say.**

**The cell-2 stratum is reported, not gated.** At ~900 events in the mining window it cannot carry
a gate of its own; its delta is shown beside the pooled one so the interaction is visible.

---

## 6. Stage 0

| | check |
|---|---|
| **P1** | counts: zones on 15m names in the window, touched, `[BASIS]`-dropped, resolved; cell-2 stratum size |
| **P2** | `[ALIGN]` per name, printed — 32 medians and 32 off-shares |
| **P3** | time-of-day of the first 15m touch: how much of the day has elapsed when the entry fires. A touch that is nearly always in the first bar is the daily open, not an intraday entry |
| **P4** | **look at the object** — one named event printed in full: zone, creation, arming, the 15m bar that touched it, both entry prices, the close |

---

## 7. Predictions

| | prediction | confidence |
|---|---|---|
| **X-a** | `[ALIGN]` passes on all 32 after the repair, and **`[BASIS]` drops fewer than 2%** | high |
| **X-b** | **T1 fails** — the market-arm delta is within 2 SE of zero. D413's T4 found levels are not consumed on contact and its sweep found the first bar weakest; the touch-to-close move should be noise | moderate |
| **X-c** | **T2 passes** — the edge-fill delta is positive, because the edge is by construction the best price of the touch bar and the close is rarely there | moderate-high |
| **X-d** | the cell-2 stratum's delta is **not distinguishable** from the pooled one | moderate |
| **X-e** | **P3 shows the first touch inside the first hour for more than a third of events** | moderate |

**X-b against X-c is the whole study.** If the market arm is flat and the limit arm is positive,
the 15-minute entry's value is *entirely* the spread saved and the queue assumed — an execution
gain, not a timing gain — and the honest number for a plan is somewhere between the two.

---

## 8. What this does not do

- **Does not confirm, weaken or touch the signal.** §1.
- **Does not read 2024+.** §2.
- **No holdout read.** `holdout2` is untouched.
- No book, no slot cap, no path-variant lens.
- **Does not model queue position, partial fills or impact.** Two bounds, and the truth between.
- **Does not recommend a disposition.** That is the principal's.

---

## 9. R13

**Fourteenth look by object on price levels; the first on execution rather than signal.** The 32
names and 2018–2023 window have been read before by D403 (four of the 24 cohort-4 names) and D383
(the ETF panel, not these). The ledger carries regardless.

**Cost if it fails: minutes on fixtures already on disk.**
