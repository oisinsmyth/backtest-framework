# D719 PRE-REGISTRATION — F2, unchanged, at the commodity settlement windows: a transfer test on thirteen roots (CL, NG, HO, RB, HG, GC, SI, ZC, ZS, ZW, KE, ZL, ZM), each at the biggest viable size for a $50k prop account, with the oracle profile reported beside

*2026-09-30.*
- *The principal: "Ok go for #5" (continuation into commodity settlement windows), then, on the prior-art sweep: "All
  roots, biggest viable size for a 50k prop account."*
- *Numbered D719: D718 is the other session's, and it was told before writing.*
- ***Committed alone, before its runner exists.** In-sample, 2016-01-04 → 2023-12-29.*
  - *Nothing dated 2024-01-01 or later is read on any root.*
  - ***2024-01-01 → 2025-02-28 is held.** CLAUDE.md names it the futures fixtures' confirmation slice ("the assembled
    book is confirmed only on a slice no component has seen"). It stays unread, as it did for F2. A root that
    transfers is confirmed there and in the vault, never here.*
  - *CL, NG, HO and RB after 2026-09-18 (D626's sample) are never read.*

## 0. What this is, and what is already known

**The question.**
- F2 (D707 §1; the vault line is now NQ F2, D716) takes the sign of the hour before the close and holds it into the
  close, on days when that hour and the day are big relative to their own history.
- **Does the same rule, unchanged, carry at the commodity settlement windows?** There, funds, index books and hedgers
  concentrate trade into a short VWAP window: window volume is 2.5–8.6 times the five minutes before it (D586).

**Why it is a transfer test, not a filter design.**
- The rule is fixed. The roots and the clock are the only change, and nothing is fitted.
- **The oracle profile the principal asks to see before any filter design is reported beside the verdict,** from the
  same one run. It is evidence for later filter designs, not for this verdict.

**Prior art** (the sweep of 2026-09-30, its load-bearing citations verified):

| roots | what is already known |
|---|---|
| **NG** | [D630](D630-RESULT-h2-ng-passes-and-the-move-reverts-after-the-settlement.md) followed the return since the prior settlement into the 14:28–14:30 window on predicted-fund-flow days: **PASS at full size** (+$66.02 gross, t 5.01), but **+$1.60 net at one MNG** (Sharpe 0.44), and 2022 carries it |
| **CL** | [D648](D648-RESULT-cl-t1-misses-by-0.01-t2-names-inventory-risk.md) is the same family on CL: t 2.230 against a 2.2414 bar, net −$3.00 |
| **SI, GC** | Included on the principal's "All roots"; the other session confirmed it uses neither window. [D709](D709-STAGE-0-RESULT-silver-moves-into-settlement-not-the-funds.md) read SI's window as a test and GC's as a predicted-null member. Their window history before 2026-09-21 is `current_only` in `settlement_windows.csv` (no dated notice); D709 used the same windows |
| **HO, RB, HG and the grains** | No settlement-window return construction has been read on them (D676–D679 read other constructions on HO, RB and HG) |

**The verdicts on NG, CL, GC and SI are reported but are NOT independent evidence,** because earlier records read
their windows for this family. The family reading (§3) is stated with and without them.

## 1. The construction, per root r (D707 §1 with the clock and the root replaced)

| item | definition |
|---|---|
| **data** | `data/fixtures/fut_day1m.parquet`: one-minute bars, front contract by volume per session, on each root's own band (energy and metals 09:00–; grains 09:30–14:20). **KE is not in it.** Its bars are built by the runner from the raw Databento `ohlcv-1m` with the fixture's own front-by-volume rule, and proved by §5's known answer or reported UNRESOLVED |
| **session** | at least 90 % of the root's band minutes present |
| **roll-guard** | a session is not traded if its contract is not the modal contract of the next 5 sessions. This keeps every trade at least 5 sessions from a roll, and so from delivery (the principal's no-expiring-physical ruling); the energy expiring-day window never arises |
| **window end W** | from `data/settlement_windows.csv`: CL, NG, HO, RB **14:30 ET**; HG **13:00**; GC **13:30**; SI **13:25**; ZC, ZS, ZW, KE, ZL, ZM **14:15** |
| **price at t** | the close of the one-minute bar that starts at t − 1; the band's open is the open of its first bar |
| **decision T** | **W − 30 minutes**: energy 14:00, HG 12:30, GC 13:00, SI 12:55, grains 13:45 |
| **signal** | F = 10⁴ · ln(P_T / P_{T−60}); d = sign(F); F = 0 is not a candidate |
| **trade** | at T in direction d, exit at P_W, the close of the settlement window's last minute. No stop, flat every day |
| **a** | \|F\| / σ_F, with σ over the previous 252 sessions of the frame (at least 60), shifted one session |
| **b** | ln √(Σ r²) of the 5-minute log returns (bp) from the band's open to P_T |
| **rule** | tₐ = tiers(a), t_b = tiers(b), t_c = tiers((tₐ + t_b) / 2), over the root's candidates in order (D671's `tiers`, 250). **TAKE when t_c ≥ 0.8** |
| **window** | the root's candidates with tₐ and t_c defined (about two years of burn-in: first trades about 2018; KE about 2019) → **2023-12-29** |

## 2. Size: the biggest viable for a $50k prop account, fixed before the scored window

**The account** (the repo's R11 plus the venue terms; P2 and P6 permit Topstep):
- a **$2,000 trailing drawdown** (P1's 4 % of $50k);
- a **daily loss limit of $1,000** (Topstep 50K, as published; R11 flags that daily limits are unverified in our own
  encoding);
- **at most 5 full-size or 50 micro contracts.**
- **P2 holds by construction:** every trade ends by 14:30 ET, before every venue's flatten time.

**The contracts:**

| root | full-size | micro, where CME lists one |
|---|---|---|
| CL | CL | MCL, one-tenth |
| NG | NG | MNG, one-tenth |
| HG | HG | MHG, one-tenth |
| GC | GC | MGC, one-tenth (10 oz) |
| SI | SI | SIL, **one-fifth** (1,000 oz) |
| HO, RB | HO, RB | none |
| ZC, ZS, ZW, ZL, ZM | full-size | MZC, MZS, MZW, MZL, MZM: one-tenth, cash-settled, tick twice the price increment. **Listed only from 2025-02-24, so in-sample they are one-tenth of the full bars** |
| KE | KE | none |

**The rule** (per root, from its burn-in sessions only, before its first scored trade):
- **q = the 99th percentile of \|P_W − P_T\| in dollars per full contract,** over the burn-in candidates whose a lies
  in the top fifth of the burn-in's own a (the days the rule would take).
- **n_full = min(5, ⌊$1,000 / q⌋).** If n_full ≥ 1, trade **n_full full contracts.**
- Otherwise, where a micro exists, **n_micro = min(50, ⌊$1,000 / (q · m)⌋)**, with m the micro's share of the full
  contract (one-tenth; SIL one-fifth). If that is ≥ 1, trade n_micro micros.
- **Otherwise NOT VIABLE.** The gross verdict is still read, and the net is reported per full contract.

**Why the count barely matters, and the contract type does.** Per-contract gross and net, and every t, do not change
with the count; only the drawdown does. The contract type sets the cost against the gross.

**The costs** (friction once, per round trip, per contract):

| contract | cost |
|---|---|
| full-size | `data/futures_costs.json`: $6.00 + the root's default-line crossing × its tick |
| KE, not in the table | ZW's line (the same 5,000 bushels and $12.50 tick), as an assumption |
| GC and SI full-size, not in the table | $6.00 + one tick (GC $10, SI $25), the `d556_one_tick` convention of the other roots, as an assumption |
| micros in the table (MCL, MNG, MHG, MGC, SIL) | their lines |
| micro grains, not in the table | **$3 + one micro tick** (MZC, MZS, MZW $2.50; MZL $1.20; MZM $2.00), from CME's twice-the-increment rule, reported with a two-tick band |

## 3. The verdict, per root and for the family (D711 A2's gates, with D711-A1's statistic)

**Per root:**

| gate | condition |
|---|---|
| (a) signal | filtered mean **gross per contract** > 0, one-sided HAC t (NW 5), **Holm across the thirteen roots at p < 0.05** |
| (b) the filter, not the day | the filtered book's direction efficiency Σgross / Σ\|gross\| above the **exact p95 of an enumerated joint rotation** of (a, b) against the root's fixed outcomes (every offset from 21 to n − 21; tiers and rule re-run) |
| (c) the fee | mean **net per contract** at the §2 contract > 0 |

| root verdict | condition |
|---|---|
| **TRANSFERS** | (a), (b) and (c) hold |
| **SIGNAL, NOT FEE** | (a) and (b) hold, (c) fails |
| **UNRESOLVED** | fewer than 60 filtered trades, or NOT VIABLE with (a) and (b) holding |
| **DOES NOT TRANSFER** | otherwise |

**The family reading:**

| reading | condition |
|---|---|
| **SUPPORTS** | at least 3 roots TRANSFER |
| **MIXED** | 1 or 2 transfer |
| **NONE** | none transfers |

It is stated twice: over all thirteen, and over the **nine independent roots** (excluding NG, CL, GC and SI, whose
windows earlier records read).

**What a TRANSFERS means.** A root that transfers is a candidate for its own joint-vault pre-registration, on the
principal's word (free programme slots 1, 2 and 10). Its unseen data would be 2024-01-01 onward. **Nothing here
spends a slot.**

## 4. Reported beside, never gating

- **The oracle profile, per root** (D702's form, hindsight and descriptive):
  - take-everything gross and net, and the size-only oracle's top 20 %;
  - terciles of a and of b against gross, win rate and the 2c bar;
  - the D630-style direction (the return since the prior settlement) as a variant;
  - the day's move to T, aligned against opposed.
- **The four reporting groups** at the §2 contract and count, net and gross side by side:
  - Sharpe with Sortino, per trade and daily; max drawdown;
  - hit, median and payoff; skew; the 1 / 5 / 10 % two-tailed trims;
  - by year and the 2022 share; before and after 2022-05-16; long against short.
- **The prop geometry:**
  - the trailing drawdown at the §2 size (P1's $2,000);
  - the days beyond a $1,000 loss (P3);
  - the largest single day's share of profit (P5).
- **The component line:** net daily Sharpe, and ρ with NQ F2 (D716), the MACD arm, and every other root.
- **Without the January index-roll hedge days** (business days 5–9, D636's trading days), reported.
- **The exit price against the official settlement** (`fut_settle_strip`): its median distance in ticks, per root.

## 5. The runner's assertions (each shown to raise in `--selftest`, or proved before any statistic)

- **Known answers:**
  - the generic clock code reproduces **D711's NQ 15:30 book** (274 trades, +$20.670105) when pointed at NQ;
  - per root, the one-minute data used is the fixture's (the column totals over the scored window);
  - **KE's built bars** reproduce `data/index_reweight/window_flow_daily.csv.gz`'s KE window prices on at least 95 %
    of sessions, or KE is reported UNRESOLVED.
- **The exit check:** P_W lies within 2 ticks of the official settlement on at least 80 % of scored sessions per root.
  Otherwise that root is flagged, not dropped.
- **Lag:**
  - `tier_audit` on every root's three tiers;
  - the realised-volatility audit to T, with a canary that reads the bar starting at T (must raise);
  - the σ canary that includes today (must raise);
  - **the sizing canary:** q computed with one scored session in it must raise.
- **Right quantity:** the entry is the close of the bar starting T − 1 and the exit the close of the bar starting
  W − 1, by minute arithmetic in a second implementation, on sampled sessions of every root.
- **Sign, in money,** on every root's full and micro multiplier.
- **The null:** offset 0 reproduces each book; chunk == whole across processes; synthetic calibration as D711-A1 (a
  no-direction world clears p95 about 5 % of the time; an injected effect clears it).
- **The seal:** no session ≥ 2024-01-01 reaches any build (the fixture holds later data, so the reader cuts it and
  asserts); run-once.

## 6. Power (rough)

- About 5.5 scored years at about 45 filtered trades a year gives **about 250 trades a root** (KE about 210).
- **At F2's per-trade gross Sharpe (about 0.19 on NQ),** the expected gross t is about 3.0 (about 1.5 at half the
  effect).
- **Holm across thirteen** puts the smallest bar at about t 2.7.
- **The fee is the binding question.** At micro size, D630 showed a real NG gross edge netting $1.60. Full-size
  contracts, where §2 allows them, carry the fixed cost over ten times the notional.

## 7. Predictions

1. **Gross is positive on at least 9 of the 13 roots** (the window's flow is a continuation force).
2. **NG, CL and SI read (a) positive,** consistent with D630, D648 and D709.
3. **§2 gives full-size contracts for the grains and HG** (one to five), and **micros for NG, CL, GC and SI.**
4. **One to three roots TRANSFER (MIXED)**, most likely among the grains and HG. **At least one root reads SIGNAL,
   NOT FEE.**
5. **2022 holds more than 40 % of the net on every energy root that transfers.**
6. **ρ with NQ F2 is below 0.2 on every root** (a different clock and a different flow).

## Amendment D719-A1 (2026-09-30), before the runner exists: KE deferred, and the bands stated exactly

*Found while inventorying the data for the runner; nothing has been read or run.*

**1. KE is deferred, and reads UNRESOLVED.**
- Its one-minute bars do not exist. `fut_day1m.parquet` was decoded from the raw `ohlcv-1m` archive (26 files, 12
  GB), and its front contract is taken from `fut_breadth_hourly`, which has no KE. The decode cache is gone.
- **Building KE needs a new decode and a new front-month rule.** That is a data build with its own gates, not part
  of this runner.
- **The family is therefore the twelve roots with bars,** and gate (a)'s Holm runs across twelve. KE is scored later,
  under this same rule, only if its bars are built and proved as §5 states. It is not a second look at anything here.

**2. The bands, stated exactly.** The fixture's bar index counts minutes from 09:00 ET (bar 0 = 09:00; the band is
09:00–15:59).

| roots | band open (for b) | session rule: at least 90 % of the minutes from band open to W carry a bar |
|---|---|---|
| CL, NG, HO, RB, HG, GC, SI | **09:00** (bar 0) | 09:00 → W |
| ZC, ZS, ZW, ZL, ZM | **09:30** (bar 30), CBOT's 08:30 CT open | 09:30 → W |

**3. The multipliers and ticks.**
- They are taken from `data/futures_costs.json` where it carries them.
- **GC and SI** come from `data/futures_contract_specs.json` (GC $100 a point, tick $10; SI $5,000 a point, tick
  $25).

**4. The exit check matches contracts by the strip's own label.** Where the fixture's contract label and the strip's
do not match, that session is left out of the check and the count is reported.

**Nothing else changes:** the rule, the clock, the size rule, the gates, the readings and the predictions. The family
readings now count out of twelve and out of eight independent roots.
