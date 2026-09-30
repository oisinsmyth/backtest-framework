# D711 RESULT — A1 UNRESOLVED: the midday clocks carry about a third of F2's per-trade information, most of it at 13:30. A2 MIXED: NQ transfers (it is the same trade), YM half does, RTY does not. ES F2 still clears a correctly sized null (rank 0.991)

*2026-09-30. In-sample to 2023-12-29 on every root; nothing dated 2024-01-01 or later was read.*
- ***The spec:** [D711 PRE-REG](D711-PRE-REG-f2-placebo-clocks-and-other-index-roots.md) (`a39ec041`), with
  D711-A1 (`fcddabee`).*
- ***The runner:** `scripts/stage1_d711_f2_mechanism.py` (`20aa18ff`), run once in 2.45 min.*
- ***Output:** `data/stage1_d711_f2_mechanism.json`, statistics only.*
- ***Known answers held:***
  - *D618 §3c (1,960 sessions);*
  - *the generic loader equals D707's frame on ES 15:30 in every column;*
  - ***D707's frozen answer is reproduced exactly** (252 trades, +$13.208968, the same take-session hash).*
- ***Nothing here changes D707** or its vault look.*

## The answer in one line

**Neither reading came out as predicted.**
- **A1 (the placebo clocks) is UNRESOLVED.**
  - The flow-into-the-close story is not cleanly supported: 13:30 → 14:00 carries almost F2's information per trade.
  - The generic story is not supported either: the pooled midday clocks carry less than half of it.
- **A2 (the other roots) is MIXED.**
  - NQ transfers strongly, but it is the same trade as ES F2 (ρ 0.87).
  - YM passes the edge gate but not the rotation; RTY fails both.
- **One piece of news for F2 itself:** under D711-A1's correctly sized null, ES F2's direction efficiency ranks
  **0.991** (p95 0.235 against its 0.279). D705's "beats the null" survives the correction.

## 1. A1 — the placebo clocks on ES

*The common window is 2018-05-14 → 2023-12-29. z is gross in units of the clock's own take-everything sd (s_T).*

| clock (held 30 min) | s_T | F2-rule trades | mean z | mean gross / net | gross HAC t | take-everything z | lift | daily Sharpe (Sortino), net |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 10:30 | $47.7 | 250 | +0.103 | +$4.91 / +$0.49 | 1.20 | −0.002 | +0.104 | +0.04 (+0.06) |
| 11:30 | $38.1 | 250 | +0.016 | +$0.61 / −$3.82 | 0.18 | +0.030 | −0.014 | −0.38 (−0.50) |
| 12:30 | $33.2 | 251 | +0.056 | +$1.87 / −$2.55 | 0.66 | +0.017 | +0.039 | −0.30 (−0.41) |
| **13:30** | $36.1 | 250 | **+0.273** | **+$9.88 / +$5.45** | **2.41** | +0.059 | **+0.215** | +0.55 (+0.95) |
| 14:30 (shoulder) | $42.5 | 241 | +0.048 | +$2.02 / −$2.40 | 0.45 | +0.055 | −0.008 | −0.20 (−0.24) |
| **15:30 (F2)** | $58.4 | 252 | **+0.302** | **+$17.63 / +$13.21** | **3.31** | +0.072 | **+0.230** | **+0.80 (+1.37)** |

**The pooled placebo (10:30–13:30, 1,001 trades on 454 sessions):**
- G_P = **+0.112**, SE 0.044 (session-clustered), t 2.56;
- the upper 95 % bound is 0.184.
- F2's G_F2 is 0.302, so **H = 0.151**.

**The declared rule gives UNRESOLVED:**

| reading | needs | here |
|---|---|---|
| CLOSE-SPECIFIC | upper bound < H | 0.184, not below 0.151 |
| GENERIC | G_P ≥ H | 0.112, below 0.151 |

**Reading the clocks, descriptively (none of this is a test):**
- **Midday (11:30, 12:30) is nothing.** The filter's lift is −0.01 and +0.04.
- **13:30 → 14:00 is the exception:** +0.273, a lift of +0.215, and 2021–2023 positive. It carries most of the placebo's
  mean.
- **The shoulder (14:30 → 15:00) is nothing** (lift −0.008).
- **So the pattern is not monotone into the close,** which the simple flow story would predict. It is two islands,
  13:30 and 15:30, with nothing at 14:30 between them.
- **13:30 is not a candidate.**
  - It was found by looking at five placebo clocks.
  - Its window ends at 14:00, when FOMC statements are released on eight days a year. That was not checked here.
  - Any use of it needs its own pre-registration, and would say so.

## 2. A2 — F2 unchanged on NQ, YM and RTY at 15:30

| | NQ (MNQ, $4.07) | YM (MYM, $3.80) | RTY (M2K, $3.76) |
|---|---:|---:|---:|
| window | 2018-04-20 → 2023-12 | 2018-04-25 → 2023-12 | 2019-11-11 → 2023-12 |
| trades (a year) | 274 (48) | 271 (48) | 224 (54) |
| mean gross / net | **+$24.74 / +$20.67** | +$9.94 / +$6.15 | +$4.39 / +$0.64 |
| gross HAC t; Holm p | **3.53; 0.0006 ✓** | 2.83; 0.005 ✓ | 1.53; 0.063 ✗ |
| efficiency E; rotation p50 / p95; rank | **0.267; 0.107 / 0.232; 0.984 ✓** | 0.222; 0.104 / 0.233; 0.936 ✗ | 0.120; 0.041 / 0.173; 0.839 ✗ |
| rotation count range | 276–369 | 274–353 | 188–234 |
| mean-gross rotation rank (reported; anti-conservative) | 1.000 | 0.996 | 0.958 |
| **verdict** | **TRANSFERS** | DOES NOT TRANSFER (b) | DOES NOT TRANSFER |
| mean z (ES: 0.302) | 0.304 | 0.232 | 0.129 |
| take-everything gross / net | +$5.84 / +$1.78 | +$3.09 / −$0.70 | +$1.01 / −$2.75 |
| hit (net), median net, payoff | 0.555, +$11.43, 1.27 | 0.513, +$1.70, 1.25 | 0.496, −$0.76, 1.05 |
| skew | +0.57 | +0.06 | +0.37 |
| per-trade Sharpe (Sortino), net | 1.08 (1.81) | 0.63 (0.98) | 0.09 (0.14) |
| **daily Sharpe (Sortino), net** | **0.92 (1.56)** | 0.54 (0.85) | 0.07 (0.11) |
| max drawdown | $990 | $621 | $509 |
| 1 % trims: ex-top / ex-bottom / both | 16.26 / 23.94 / 19.52 | 4.25 / 8.37 / 6.47 | −1.22 / 1.97 / 0.12 |
| long / short net | +$19.53 / +$21.85 | +$5.71 / +$6.63 | +$0.51 / +$0.78 |
| before / after 2022-05-16 | +$21.92 / +$14.15 | +$7.06 / +$1.89 | +$1.83 / −$2.15 |
| 2022's share of net | **67 %** | 53 % | more than all of it (the total is small) |
| **ρ with ES F2, daily net** | **0.87** | 0.86 | 0.75 |
| ρ with the MACD arm | +0.02 | −0.02 | +0.04 |

**By year** (n, net a trade):

| | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|
| NQ | 26, +0.9 | 19, −1.5 | 79, +15.4 | 50, +10.2 | 65, **+58.0** | 35, +4.8 |
| YM | 18, +14.4 | 25, −5.1 | 71, +6.1 | 50, +3.7 | 70, +12.7 | 37, +0.7 |
| RTY | — | 3, −8.6 | 67, −2.6 | 48, +2.0 | 56, +5.2 | 50, −0.9 |

**The A2 reading is MIXED** (one of three transfers).
- **NQ is not a second component.** ρ 0.87 with ES F2 fails the ledger's C-b by a wide margin: it is the same trade on
  a bigger-moving contract.
- **YM** passes the edge gate (t 2.83) but its efficiency ranks 0.936, short of 0.95.
- **RTY has no edge.**
- **The order NQ > ES > YM > RTY is descriptive and was not predicted in this form.** It matches the size of each
  index's leveraged-ETF and options complex, largest for the Nasdaq-100. That fits a close-flow reading, but it was not
  tested here.

## 3. Predictions

| # | prediction | outcome |
|---|---|---|
| 1 | the ES known answer reproduces | **held** |
| 2 | A1 reads CLOSE-SPECIFIC, each placebo near its take-everything | **failed**: UNRESOLVED; 13:30 and 10:30 are not near theirs |
| 3 | the shoulder sits between the placebo and F2 | **failed**: 14:30 (0.048) is below the pooled placebo (0.112) |
| 4 | A2 SUPPORTS: NQ and YM transfer, RTY weakest | **failed**: MIXED. NQ transfers; YM misses (b); RTY is weakest |
| 5 | ρ above 0.6 for NQ and YM, lower for RTY | **held** (0.87, 0.86, 0.75) |
| 6 | every transferring root's 2022 share above 40 % | **held** (NQ 67 %) |

## 4. What it means for F2 (D711 §4's declared meanings)

| finding | meaning |
|---|---|
| **A1 UNRESOLVED** | the flow-into-the-close story is **neither confirmed nor refuted**. F2 is not the only clock where the rule works: 13:30 comes close, and 10:30 carries some. But the rule is also not generic across the day: 11:30, 12:30 and 14:30 are nothing. **D707 §0's mechanism sentence is weaker than written.** |
| **A2 MIXED** | the rule works on NQ as strongly as on ES, but NQ is the same trade, so this is closer to a replication than an independent confirmation. YM half-replicates and RTY does not. **The prior on F2's vault look neither rises nor falls much.** |
| **the corrected null** | **ES F2's direction efficiency ranks 0.991 against the correctly sized rotation.** D711-A1's concern about D705's gate (b) does not change F2's standing. |

**Nothing changes D707.**
- The vault look (slot 7) happens under its frozen rule.
- **The only follow-up this record suggests is NQ F2 as a candidate. It would be the same trade**, so it would sit
  beside ES F2 as a sizing choice (one MES or one MNQ, or both), not as a second component. That is the principal's
  call.

## Addendum (post hoc, 2026-09-30): the extremes stripped out, and where ES and NQ overlap

*The principal: "I would like the extremes striped out for the decision time comparison and the other comparisons to
the other roots. I would also like to have a statistical breakdown of where the trades overlap between NQ and ES and
where they disagree?"*
- *Descriptive, on the same in-sample data. Nothing gates, nothing is fitted, and nothing above changes.*
- ***Script:** `scripts/diag_d711_trims_and_overlap.py`. **Output:** `data/diag_d711_trims_and_overlap.json`.*
- *It reproduces D711's lines and pooled placebo exactly, and D707's frozen answer, before any statistic.*

### A. The extremes stripped out

**How the trims work:**
- The trades are ranked by net, and the same share is cut from **both** tails.
- z is measured on the same trades, in D711's units (each line's take-everything sd).
- **"Lift"** is the filter's z minus take-everything's z under the same trim.
- The top-5 share is the five best trades' share of the line's total net.

**The decision times (ES):**

| clock | full: net ($) / z / t | 1 % | 2.5 % | 5 % | 10 % | median net / z | top-5 share | lift at 10 % |
|---|---|---|---|---|---|---|---:|---:|
| 10:30 | +0.48 / 0.103 / 0.12 | +0.36 / 0.100 | +0.63 / 0.106 | +1.77 / 0.130 | +2.88 / 0.153 (t 1.19) | +3.08 / 0.157 | >100 % | 0.153 |
| 11:30 | −3.82 / 0.016 / −1.14 | −3.54 / 0.023 | −3.40 / 0.027 | −2.91 / 0.040 | −2.13 / 0.060 | −0.67 / 0.098 | — | 0.024 |
| 12:30 | −2.55 / 0.056 / −0.90 | −2.98 / 0.044 | −2.71 / 0.052 | −2.49 / 0.058 | −2.08 / 0.071 | −3.17 / 0.038 | — | 0.068 |
| **13:30** | +5.45 / 0.273 / 1.33 | +4.69 / 0.252 | +3.48 / 0.219 | +2.62 / 0.195 | **+2.00 / 0.178 (t 0.85)** | +0.58 / 0.138 | **79 %** | 0.150 |
| 14:30 | −2.40 / 0.048 / −0.53 | −1.11 / 0.078 | +0.17 / 0.108 | +1.24 / 0.133 | +2.17 / 0.155 | +1.83 / 0.147 | — | 0.099 |
| **15:30 (F2)** | +13.21 / 0.302 / 2.48 | +12.50 / 0.290 (t 2.89) | +12.27 / 0.286 | +11.21 / 0.268 (t 2.92) | **+9.79 / 0.243 (t 3.14)** | +6.21 / 0.182 | 51 % | 0.206 |

**The pooled placebo (10:30–13:30), with a session-clustered SE:**

| trim | G_P (z) | t | F2's z | ratio to F2 |
|---|---:|---:|---:|---:|
| none | 0.112 | 2.56 | 0.302 | 0.37 |
| 1 % | 0.100 | 2.50 | 0.290 | 0.35 |
| 2.5 % | 0.100 | 2.48 | 0.286 | 0.35 |
| 5 % | 0.103 | 2.95 | 0.268 | 0.39 |
| 10 % | 0.114 | 3.69 | 0.243 | 0.47 |
| median | 0.105 | | 0.182 | 0.58 |

**The other roots at 15:30:**

| root | full: net / z / t | 1 % | 5 % | 10 % | median net | ex-top-5 / ex-bottom-5 | top-5 share | lift at 10 % |
|---|---|---|---|---|---:|---|---:|---:|
| ES | +13.21 / 0.302 / 2.48 | +12.50 (t 2.89) | +11.21 (t 2.92) | +9.79 (t 3.14) | +6.21 | +6.63 / +19.03 | 51 % | 0.206 |
| **NQ** | +20.67 / 0.304 / 2.95 | +19.52 (t 3.11) | +19.43 (t 3.53) | **+18.94 (t 4.00)** | +11.43 | +12.39 / +27.76 | 41 % | 0.247 |
| YM | +6.15 / 0.232 / 1.75 | +6.47 (t 1.92) | +5.29 (t 1.99) | +3.72 (t 2.04) | +1.70 | +1.98 / +10.47 | 68 % | 0.143 |
| RTY | +0.64 / 0.129 / 0.22 | +0.12 | +0.37 | −0.07 | −0.76 | −2.89 / +3.79 | >100 % | 0.092 |

**What stripping the extremes shows:**
1. **ES F2 does not rest on a few trades.** It keeps +$9.79 a trade with 10 % cut from each tail, and its t RISES
   (2.48 → 3.14), because the tails were adding noise, not edge.
2. **NQ is the most robust line in the record:** +$18.94 at a 10 % trim, t 4.00.
3. **13:30 was a few trades.** Its five best trades are 79 % of its net, its median is +$0.58, and at a 10 % trim it
   keeps +$2.00 (t 0.85). The headline "13:30 nearly matches F2" does not survive the trims.
4. **But the midday clocks' small positive z is broad, not a tail effect.** The pooled placebo sits at 0.10–0.11 z
   under every trim, its t rises to 3.7, and its ratio to F2 rises from 0.35 to 0.47 as F2's own tails are cut. So
   the rule picks up a small continuation all day, about a third to a half of F2's per-trade size, and **only at
   15:30 does that clear the fee.** 11:30 and 12:30 are net-negative under every trim.
5. **YM's edge is thin** (median +$1.70, top-5 share 68 %). **RTY has none** under any trim.

**The reading of A1 moves toward F2's story** (the last half-hour is where the size is), with a qualifier: a smaller
continuation exists at every clock. It stays UNRESOLVED as registered.

### B. Where ES F2 and NQ F2 overlap and where they disagree

*The common sessions are both roots' F2 windows, 2018-05-14 → 2023-12-29: 1,347 sessions. Net is per micro (MES
$4.42, MNQ $4.07).*

**Overlap:**

| | sessions |
|---|---:|
| both take | **217** |
| ES only | 33 |
| NQ only | 52 |
| neither | 1,045 |

- **The two filters pick nearly the same days.** The Jaccard is 0.72. P(NQ takes \| ES takes) is 0.87, and P(ES takes
  \| NQ takes) is 0.81. The φ of the take flags is 0.80.
- **Direction:**
  - on the days both take, the two agree in 216 of 217 (99.5 %);
  - across all common sessions, 89 %.
- **The days only one takes are near misses.** There, the other root's composite tier has a median of about 0.75
  against the 0.8 bar: 97 % of ES-only days had NQ's tier ≥ 0.6, and 83 % of NQ-only days had ES's.

**Where the money is:**

| cell | n | ES net (median, hit, t) | NQ net (median, hit, t) |
|---|---:|---|---|
| **both take, same direction** | 216 | **+$15.51** (+$8.08, 0.56, t 2.50) | **+$25.58** (+$15.68, 0.57, t 2.90) |
| both take, opposite direction | 1 | +$113.08 | −$223.57 |
| ES only (ES traded) | 33 | **−$4.50** (−$6.92, 0.39, t −0.73) | NQ untraded that day: +$7.93 (median −$7.07) |
| NQ only (NQ traded) | 52 | ES untraded that day: −$9.11 (median −$0.67) | **+$4.29** (−$7.82, 0.48, t 0.30) |
| neither (untraded, both) | 1,045 | −$3.11 (t −2.51) | −$3.32 (t −1.90) |

- **All of both books' profit comes from the days they agree:** 104 % of ES F2's net and 96 % of NQ F2's. The days
  only one root takes are about flat-to-negative for the root that trades them.
- **The agreement is descriptive and post hoc.** A both-take ES book earns +$15.96 against −$4.50 for ES alone
  (Welch t 1.92). For NQ it is +$24.43 against +$4.29 (t 1.06).
- **"Take only when both roots' tiers clear 0.8" is a new rule found by looking.** It is not tested here, and it could
  only be judged on data it has not seen.
- **On the days both take, the two trades are almost one trade:** ρ of gross 0.96, against 0.77 across all common
  sessions.

**The books on the common sessions** (daily, net):

| book | total | Sharpe (Sortino) | max drawdown |
|---|---:|---:|---:|
| ES F2, 1 MES | $3,315 | 0.95 (1.62) | $707 |
| NQ F2, 1 MNQ | $5,524 | **1.08 (1.83)** | $990 |
| both, 1 MES + 1 MNQ | $8,839 | 1.06 (1.82) | $1,538 |

- ρ of daily net is 0.87, so **holding both adds size, not diversification.** The combined Sharpe is NQ's alone.
- These Sharpes are higher than §2's, because the daily denominator here is only the common sessions.

**By year** (mean net a trade on agreement days; counts of the days only one root took):

| | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|
| both take (n) | 17 | 18 | 59 | 39 | 58 | 26 |
| ES net / NQ net, both take | +14.1 / +13.2 | −4.6 / −0.8 | +5.6 / +9.1 | +16.8 / +29.1 | **+37.9 / +59.7** | +1.0 / +8.1 |
| ES only / NQ only (n) | 1 / 6 | 3 / 1 | 6 / 19 | 9 / 11 | 7 / 6 | 7 / 9 |

**What it means:**
- **ES F2 and NQ F2 are one signal read on two contracts.** Where they differ, it is the tier landing either side of
  0.8, and those marginal days earn nothing.
- **NQ is the better contract for the same signal** in-sample: bigger per trade (MNQ moves more dollars for a similar
  cost), more robust under trims, and a higher Sharpe.
- **The rest is the principal's call, not a finding:**
  - ES's vault look is frozen (D707);
  - NQ would need its own pre-registration;
  - an agreement rule would need unseen data.
