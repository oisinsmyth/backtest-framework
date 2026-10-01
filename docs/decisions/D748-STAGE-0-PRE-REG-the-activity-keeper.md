# D748 STAGE 0 PRE-REGISTRATION — the activity keeper: one placeholder trade on the financial micro with the smallest forecast dollar risk, fired only when a prop firm's inactivity window would otherwise lapse

*2026-10-01.*
- *The principal asked for an "In-between/Idle" strategy to meet prop firms' minimum-activity requirements. Then:
  "breaking even on this strategy is ok, this is not a money making one … it's only requirement is to meet minimum
  trade/activity requirements, and it can never* (highly unlikely) cause an account to die."*
- *The principal's design: "a place holder trade that takes the vol\*tick size and picks the smallest root". Made
  exact here as forecast σ in points × dollars per point.*
- *The principal's choices: "Financial micros only"; "Yes, Stage 0".*
- *Numbered D748. D746 and D747 belong to the documentation-review session, which confirmed 748.*
- ***Committed alone, before its runner exists.** In-sample only (≤ 2023-12-29).*

## 0. What the keeper is for, and what it is not

**The problem.** The components abstain by design, and a prop account can die of inactivity as surely as of
drawdown. MyFundedFutures' Terms §7 treat no trade in 7 consecutive calendar days as dormancy and a breach.

**The firms' activity rules, as researched:**
- **Primary sources, read 2026-09-08:** `docs/research/Prop-Firm-080926/01–04, 10, 11`.
- **Rule aggregators, 2026-10-01, UNVERIFIED:** Tradeify, Bulenox, Alpha Futures, Lucid.

| cadence | rule | firm |
|---|---|---|
| **C7** | a trade within 7 calendar days of the last | MyFundedFutures (Terms §7, primary) |
| **W1** | a trade in every Mon–Fri week | Tradeify (unverified) |
| **T5** | a trade within 5 trading sessions of the last | Bulenox (unverified; read conservatively) |
| **T10** | a trade within 10 trading sessions of the last | Alpha Futures (unverified) |
| **C30** | a trade within 30 calendar days of the last | Topstep XFA/LFA (primary); Lucid (unverified) |

**What the keeper cannot do, by construction:**
- **Profit-day rules.** These are Apex's inactivity rule (two \$50 net-profit days per 30 calendar days) and every
  payout "winning day" (\$150–\$350). They need edge or size, and the second conflicts with "never kills the
  account". They are out of scope.
- **Minimum days to pass an evaluation** (Take Profit Trader 3, MyFundedFutures 1–4). The keeper can add those days;
  they are not a gap rule, so they are not scored here.

**The standard** is the principal's exception: it may break even, and it must (almost) never threaten the account
(memory `an-idle-strategy-may-break-even`). **No Sharpe bar applies. It is not a component and does not enter
`COMPONENTS_PROP.md`.**

**The premise is already sized** (scratch, POST HOC: `temp/idle/size_roots.py`, `temp/idle/window_1330.py`):
- **The choice of root dominates.** The 30-minute σ\$ at one micro spans about 7× across roots (M6E \$6.5 to MNQ
  \$47.5 at their quietest windows).
- **Within a root, the yearly RMS varies about 1.7–5×.**
- **The commodity micros' quiet windows fall after their settlement, and they are physically delivered.** The
  principal excluded them.
- **M6E is permitted at Topstep** (its brokerage help article on permitted products). **NOT verified at Apex or
  MyFundedFutures,** hence the index-only variant (§2).

## 1. The data and windows

- **Bars:** `data/fixtures/fut_day5m.parquet`, front month, `present & same_front`. Bar b covers 09:00 + 5b ET.
- **Calendar:** `data/fixtures/cme_session_calendar.csv.gz` (`is_trading`, `is_early_close`, `fomc`).
- **Cost:** `data/futures_costs.json`, each micro's entry: `commission_rt_usd` (\$3.00) + `crossing_ticks_rt.d507_exec` ×
  `tick_usd`.
- **The scored window:** 2018-05-14 → 2023-12-29, the span on which all three components exist in-sample.
- **Forecasts warm up on the bars from 2018-01-01.** Nothing on or after 2024-01-01 is read.

## 2. The keeper (fixed now)

**The clock.**
- Decide at **13:30 ET**: enter at bar 54's open; time exit at bar 59's close (14:00).
- It sits after D737's 10:00 decision and before F2's last hour. It is among the quietest windows (M6E \$8.08).

**The candidates (cash-settled, financial):**

| variant | roots | role |
|---|---|---|
| **F, primary** | M6E, M2K, MYM, MES, MNQ | the principal's selector |
| **I** | M2K, MYM, MES, MNQ | for a firm that does not permit FX |
| **M** | M6E always | the control; says whether the forecast adds anything |

**The selector:**
- On session s, each root's forecast is σ̂\$(root, s) = √(mean of (close₅₉ − open₅₄)² over that root's previous 20
  sessions with the window complete, strictly before s) × its micro dollars per point.
- Points carry the price level, so the forecast tracks today's notional.
- The keeper trades **1 contract of the candidate with the smallest σ̂\$** among roots whose window bars exist that
  session (`present & same_front`, bars 54–59 all present). The next-smallest is the fallback.

**Direction:**
- The sign of open₅₄ − open₀ on the chosen root (the move since 09:00), long on zero.
- A stated directional rule: there is no edge claim, but Apex requires a directional bias and bans two-sided brackets.

**The stop:**
- 4 × σ̂\$, in points, from the entry, checked on bars 54–59's highs and lows.
- When touched, the exit is at the stop level **minus one tick of slippage**. Otherwise the time exit.

**Cost:** one round trip on every keeper trade.

**When it fires (the deadline rule):**
- **Sessions:** the ES `is_trading` days.
- **Eligible sessions:** not `fomc`, and not `is_early_close` on ES or on the chosen root.
- **The decision on session s:**
  - It sees D737's trades (decided at 10:00).
  - It does **not** see C1's or F2's trades. Their in-sample books carry no entry times, so the keeper is
    conservative about them.
  - It fires if s is eligible, no known component trade is on s, and **at most one further eligible session**
    remains before the cadence's deadline. That leaves one backup session.
- **Account start:** the first session of the window counts as a trade day.
- **A fire with no candidate's window bars that day** is a failed fire, counted, and the backup applies.

**Overlap, live only:** in variant I, if a component signals an entry while the keeper is open, the keeper flattens
first. The in-sample books carry no entry times, so this is declared, not scored.

## 3. The book calendars

The component trade sessions come through `scripts/vault_d745_abstention_principle.py`'s `in_sample_books()`, read
only. Its asserted known answers are F2 271, C1 328, D737 1,699.

| calendar | trades on | case |
|---|---|---|
| **FULL** | D737 ∪ C1 ∪ F2 | the planned book |
| **NO_D737** | C1 ∪ F2 | D737 not admitted at the vault |
| **NONE** | nothing | the keeper alone; the worst case for cost |

## 4. Readings (declared now)

Every variant × calendar × cadence is scored. **The primary is variant F.**

| | criterion |
|---|---|
| **K1** | worst single keeper trade, net ≥ **−\$50** |
| **K2** | worst rolling 30-calendar-day keeper sum ≥ **−\$150** (7.5 % of a 50K's \$2,000 buffer) |
| **K3** | keeper cost a year (−net sum / years) ≤ **\$300** on the most frequent cadence under NONE |
| **K4** | **zero breaches** of the cadence, every calendar × cadence, counting failed fires |

- **READY:** K1–K4 all hold for variant F.
- **NOT READY:** any fails; the failing K is named.
- **Variant I** gets the same four, reported as **INDEX-ONLY READY / NOT READY**: the fallback for a firm without FX.
- **The forecast's value:** F against M on mean |net|, worst trade and K2. If F picks M6E on ≥ 95 % of fires, the
  record says **"the selector is M6E"**.

**Reported for every cell:**
- fires a year, failed fires, and redundant fires (on a session where C1 or F2 also traded);
- per keeper trade: count, mean, median, worst, best and stop-hit rate, net and gross;
- the root shares;
- keeper P&L a year;
- the daily correlation of keeper P&L with the FULL book's daily net (a statement, not a gate).

## 5. Assertions (each canary must raise in the self-test)

1. **Known answers:**
   - the 13:30–14:00 σ\$ over 2016–2023 on the same filters: M6E **8.079** (n 1,983), M2K **22.318** (1,598), MYM
     **24.298** (1,970), MES **31.971** (1,975), MNQ **50.368** (1,972), each to ±0.001;
   - `in_sample_books()`'s own asserted counts.
2. **Lag:**
   - a second implementation of σ̂\$ (a plain loop over prior sessions) agrees on 200 sampled root-sessions;
   - a canary that includes session s must disagree.
3. **Sign in money:** a long trade on a rising window pays positively, a short pays negatively, and the stop exit
   loses exactly stop + one tick.
4. **The deadline rule:**
   - an independent breach checker (gap arithmetic, not the firing loop) agrees with the loop's count;
   - with the keeper switched off under NONE it must report breaches.
5. **The seal:** an assertion that no bar or calendar row on or after 2024-01-01 is read.

## 6. Predictions (Opus)

- **P1:** variant F picks M6E on ≥ 95 % of fires (P ≈ 0.85).
- **P2:** under FULL, at most 5 fires a year on every cadence (D737 trades most sessions), P ≈ 0.8. Under NONE with
  T5, about 50 a year.
- **P3: READY** (P ≈ 0.85). The likeliest failure is K4 in a holiday-dense week under T5, if the one-session margin
  is not enough.
- **P4:** mean net per keeper trade about −\$4 (the cost), within ±\$1.5.
- **P5:** variant I is INDEX-ONLY READY, with a worst trade near −\$40 to −\$50 (MYM/M2K σ about 3× M6E).

## 7. After the reading

**READY:** the keeper's rules are recorded as an execution rule for the prop account. It is not a component and has
no slot. Before it is relied on:
- each firm's activity rule and permitted products are confirmed at the source;
- M6E especially.

**NOT READY:** the failing K says what to change, under a new record.

## A1 (2026-10-01, committed before the scored run): the crossing line is `d508_exec`, not `d507_exec`

**What happened.** The first `--run` stopped at the cost lookup with a `KeyError`. It read no bars, calendar or books,
and wrote no output.
- §1 named `crossing_ticks_rt.d507_exec` for each micro.
- That line does not exist for M6E. It is in any case the wrong statistic: a QUOTED spread, which is a floor.
- `data/futures_costs.json`'s own rule (`conventions.default_line_rule`) charges `d508_exec`: the EFFECTIVE crossing an
  aggressor paid, measured over the execution hours 10–15 ET. It is never to be replaced by a fallback to D507.

**The amendment:**
- §1's cost is **`commission_rt_usd` + `crossing_ticks_rt.d508_exec` × `tick_usd`**, each micro's `default_line`
  (asserted by the runner).
- The ticks a round trip:

  | M6E | M2K | MYM | MES | MNQ |
  |---|---|---|---|---|
  | 1.106 | 1.514 | 1.594 | 1.135 | 2.134 |

- Measured 2025-09 → 2026-09, so optimistic on the older window (the table's `window_caveat`).

Nothing else changes. The scratch sizing quoted in §0 used the same wrong lookup; its cost column is superseded.
