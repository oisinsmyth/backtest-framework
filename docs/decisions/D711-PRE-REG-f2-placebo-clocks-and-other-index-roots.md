# D711 PRE-REGISTRATION — two mechanism tests of F2 that leave the vault unspent: (A1) does its rule work at midday clocks on ES, or only into the close? (A2) does it work unchanged on NQ, YM and RTY?

*2026-09-30.*
- *The principal: "A1 and A2 as one pre-registration go please", after the research menu that followed
  [D707](D707-PRE-REG-f2-last-hour-filter-for-the-joint-vault.md).*
- *Numbered D711: the other session holds the three numbers from D708 on (its Stage 0 round) and was told before writing.*
- ***Committed alone, before its runner exists.** Nothing here reads a price dated 2024-01-01 or later on any root.*

**What this record does.**
- **F2 is frozen** (D707, programme slot 7), and only the joint vault run can confirm it. **Nothing here changes D707,
  its rule or its vault look.**
- **These two tests use data that played no part in choosing F2:**
  - the midday clocks on ES (A1);
  - three other index roots (A2).
- **They ask whether F2's story is right:**
  - that big hours continue **into the close**, because flow is concentrated there (dealer hedging, leveraged-ETF
    rebalancing, closing orders);
  - and that this is a property of the US index complex, **not of one contract.**

**Overlap with the other session's D708.** D708 (ES, short-gamma days) decides at 10:30, 11:30, 12:30, 13:30 and 14:30
on the raw prior hour's sign, held 60 minutes. A1 uses four of the same decision times, but with a different signal
(F2's relative-size composite, on every day) and a 30-minute hold. **The two are correlated at those clocks.** Neither
study's result is a confirmation of the other.

## 1. The construction, unchanged from D707 §1 except for the clock (A1) or the root (A2)

**Per root and per decision clock T:**

| item | definition (D707 §1, with 15:30 replaced by T) |
|---|---|
| frame | the root's `fut_{root}_rth_1m.csv.gz` sessions with at least 380 one-minute bars, from 2016-01-04 (RTY from its first session, 2017-07-10) to **2023-12-29**; each session's modal contract; a roll session is never traded |
| price at hh:mm | the close of the bar that starts one minute earlier; P09:30 is the open of the 09:30 bar |
| signal | F_T = 10⁴ · ln(P_T / P_{T−60}); d = sign(F_T); F_T = 0 is not a candidate |
| trade | at T in direction d, exit at T + 30 minutes; one micro |
| input a | \|F_T\| / σ(F_T), with σ over the previous 252 sessions of the frame (at least 60), shifted one session |
| input b | ln √(Σ r²) of 5-minute log returns (bp) from P09:30 to P_T |
| rule | tₐ = tiers(a), t_b = tiers(b), t_c = tiers((tₐ + t_b) / 2), each over that clock's candidates in order; **TAKE when t_c ≥ 0.8** |
| code | D671's `tiers`, D702's `rv_today` generalised to end at T, D703's `sigma_f5`; the runner's generic loader is proved equal to D618's `load_es` on ES |

- **At T = 15:30 this is F2 exactly.**
- **At 10:30, b covers the same hour as a** (twelve 5-minute returns), so the composite there is mostly a. This is
  disclosed; the rule is not changed.

**Costs (one micro, friction once, D668-A2's single line):**

| root | contract | $ a point | cost a round trip |
|---|---|---:|---:|
| ES | MES | 5 | **$4.42** (F2's line) |
| NQ | MNQ | 2 | $4.07 |
| YM | MYM | 0.5 | $3.80 |
| RTY | M2K | 5 | $3.76 |

Each root's cost is `cost_lines(root)["cost_single_usd"]`, from `data/futures_costs.json` via D668's `micro_costs`.
For ES, D705 and D707 round it to $4.42, and that rounding is kept.

## 2. A1 — the placebo clocks on ES

**The clocks:**
- **Placebo:** T = 10:30, 11:30, 12:30, 13:30, each held 30 minutes.
- **Reported only (the shoulder):** T = 14:30, held to 15:00.
- **The anchor:** T = 15:30, which is F2.

**Units: an information ratio per trade.** Dollar gross is smaller at midday because the half hour moves less. So every
clock's trades are measured in units of that clock's own risk:
- z_i = gross_i / s_T;
- s_T is the standard deviation of the gross of **every** candidate at clock T on the window (take everything).

**The window** is the sessions on which every clock's tiers are defined (one common window). It starts in about 2018,
as F2's does.

**The primary statistic:** G_P is the mean of z over **all placebo trades pooled** (the four clocks).
- **Its standard error is clustered by session:** the pooled residuals are summed within each session, and a
  Newey–West (5-lag) variance is taken over the session sums.
- The same estimator on one trade a session equals D691's `nw_t`, which the self-test asserts.
- **The anchor:** G_F2 is F2's mean z at 15:30 on the same window. **The bar is H = G_F2 / 2.**

| A1 reading | condition |
|---|---|
| **CLOSE-SPECIFIC** | G_P + 1.645 · SE_P < H: the placebo clocks carry less than half of F2's per-trade information, at 95 % one-sided |
| **GENERIC** | G_P ≥ H **and** G_P / SE_P ≥ 1.645: the rule works about as well at midday; F2 is momentum on volatile days, not flow into the close |
| **UNRESOLVED** | otherwise |

**Reported beside, per clock:**
- filtered mean z and dollars, gross and net, with the HAC t;
- take-everything at the clock, and the lift of the filter over it;
- trades and the 2022 share;
- the shoulder (14:30), stated against the pooled placebo and the anchor.

## 3. A2 — F2 unchanged on NQ, YM and RTY at 15:30

**Per root r, the gates:**

| gate | condition |
|---|---|
| (a) signal | filtered mean **gross** > 0, one-sided HAC t (NW 5), **Holm across the three roots at p < 0.05** |
| (b) the filter, not the day | filtered mean gross above the **exact p95 of an enumerated rotation**. The inputs (a, b) are rotated jointly against the root's fixed outcomes by every offset from 21 to n − 21, and the tiers and rule are re-run at each offset (D705's construction, one member). Count-matched by construction; the counts' range is reported |

**Per root:** it **TRANSFERS** if (a) and (b) hold, is **UNRESOLVED** below 60 filtered trades, and **DOES NOT TRANSFER**
otherwise.

**The A2 reading:**

| reading | condition |
|---|---|
| **SUPPORTS** | at least two of the three roots transfer |
| **ES-ONLY** | none transfers |
| **MIXED** | exactly one transfers |

**Reported beside, per root:**
- **the four reporting groups at the root's micro, net and gross side by side:**
  - Sharpe with Sortino, per trade and daily; max drawdown;
  - hit, median and payoff; skew; the 1 % trims;
  - by year and the 2022 share; before and after 2022-05-16; long against short;
- **the component line:** net daily Sharpe, and ρ with ES F2's daily net and with the MACD arm;
- **the information ratio** (mean z) beside ES's;
- **take-everything at 15:30** on the root, and the filter's lift.

## 4. What each outcome means (declared now)

**For A1:**

| outcome | meaning |
|---|---|
| **CLOSE-SPECIFIC** | the flow-into-the-close story survives a test it could have failed |
| **GENERIC** | F2 is volatility-day momentum. The story in D707 §0 is wrong even if the vault passes. Midday clocks then become a construction in their own right, which needs its own pre-registration |

**For A2:**

| outcome | meaning |
|---|---|
| **SUPPORTS** | a property of the index complex. NQ, YM and RTY versions become candidates only through their own pre-registration. Each root's ρ with ES F2 decides whether it is a second component (ρ < 0.3, the ledger's C-b) or the same trade |
| **ES-ONLY** | F2 is more likely a feature of one contract's history. The prior on the vault PASS falls, and that is recorded |

**None of these readings changes D707.** Its vault look happens regardless, under its own frozen rule.

## 5. The runner's assertions (each shown to raise in `--selftest`, or proved in `--run` before any statistic)

- **Known answers:**
  - the generic loader and T = 15:30 on ES reproduce **D707's frozen in-sample answer**: 252 trades, mean net
    +$13.208968, and the take-session sha256 `5427a6c8…`;
  - D618 §3c on ES (1,960 sessions, +0.6795 points, hit 0.4929).
- **Lag:**
  - `tier_audit` on every clock's and root's three tiers;
  - the realised-volatility audit, generalised to T, with a canary that reads the bar starting at T (must raise);
  - the σ canary that includes today (must raise);
  - a tier canary that ranks its own value (must raise).
- **Sign, in money:** a favourable continuation pays positively long and short, on every root's dollar multiplier.
- **Right quantity:** the 10:30 clock's entry is the close of the 10:29 bar, and its exit the close of the 10:59 bar.
  This is asserted on a sample of sessions by minute arithmetic in a second implementation.
- **The statistics:**
  - the session-clustered SE equals `nw_t` when each session holds one trade;
  - the rotation's offset 0 reproduces the observed book;
  - chunk == whole across processes;
  - on synthetic data, an injected relative-size effect TRANSFERS and a label with no effect passes (b) about 5 %
    of the time.
- **The seal:** no session ≥ 2024-01-01 reaches any build, on any root.
- **Run-once:** `--run` refuses if its output exists.

## 6. Power (rough, stated before the run)

**A1:**
- About 250 filtered trades a clock, so about 1,000 pooled placebo trades.
- **Filtered days are big days,** so the sd of z among filtered trades is about 1.5, and SE_P is about 0.05.
- **F2's in-sample mean z at 15:30 is about 0.3:**
  - gross +$17.63 against a take-everything sd of about $58;
  - that sd is from D705's take-everything per-trade gross Sharpe of 1.09 at 242 a year.
  - **So H is about 0.15.**
- **CLOSE-SPECIFIC needs G_P below about 0.07.** If the placebo clocks carry nothing (z ≈ 0), that holds with
  probability about 0.9.
- **GENERIC needs G_P ≥ 0.15.** At a midday z equal to F2's, it would read GENERIC with probability near 1.

**A2** (at F2's per-trade gross Sharpe of about 0.19, from D705's 1.24 annualised at 45 a year):

| root | filtered trades | expected gross t at full transfer | at half transfer |
|---|---:|---:|---:|
| NQ, YM | about 250 each (2018 → 2023) | about 3 | about 1.6 |
| RTY | about 190 (from about 2019-08, after its 2017 start and the burn-ins) | about 2.7 | about 1.4 |

## 7. Predictions

1. **The ES known answer reproduces.**
2. **A1 reads CLOSE-SPECIFIC.** Each placebo clock's filtered z is within one SE of that clock's take-everything.
3. **The 14:30 shoulder sits between the placebo clocks and F2.**
4. **A2 reads SUPPORTS: NQ and YM transfer, and RTY is the weakest** (it may not transfer). The index-options and
   leveraged-ETF complex is smallest there.
5. **ρ with ES F2's daily net** is above 0.6 for NQ and YM, and lower for RTY.
6. **Every transferring root's 2022 share is above 40 %.** 2022 was a volatile year on every index.
