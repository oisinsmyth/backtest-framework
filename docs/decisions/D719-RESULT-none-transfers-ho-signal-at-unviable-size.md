# D719 RESULT — NONE TRANSFERS: F2 at the commodity settlement windows carries nothing on metals, grains or natural gas; heating oil clears the edge, the rotation and the fee (+$109 net a full contract) but is UNRESOLVED because one contract is too big for a $50k prop account

*2026-09-30. In-sample 2016-01-04 → 2023-12-29 (scored from 2018-06/08 after burn-in); nothing dated 2024-01-01 or
later was read.*
- ***The spec:** [D719 PRE-REG](D719-PRE-REG-f2-at-the-commodity-settlement-windows.md) (`f4930141`), with A1
  (`a1e0a7ed`: KE deferred) and A2 (`b00f59b7`: the GC and SI cost lines).*
- ***The runner:** `scripts/stage1_d719_commodity_settlement_f2.py` (`b028f0e8`), run once in 6.5 min. The bars come
  from the `build_d719_commodity_bars.py` cache.*
- ***Known answer held:** the generic core reproduced D711's NQ 15:30 book exactly (274 trades, +$20.670105), and every
  root's cache matched the fixture's column totals.*
- ***KE:** UNRESOLVED (deferred, A1).*

## The answer in one line

**Family: NONE, over all twelve and over the eight independent roots.**
- No root clears all three gates at its size.
- **Heating oil (HO) is the one root with the signal:**
  - +$119.41 gross a full contract (t 2.74, Holm p 0.037);
  - direction efficiency rank 0.991;
  - +$109.21 net on 239 trades.
- **But HO reads UNRESOLVED.** Its burn-in 1-in-100 hold loss per full contract is $1,117, above the $1,000 daily
  limit, and HO has no micro, so §2 gives NOT VIABLE.

## 1. Per root (one contract of the §2 type; gross and net per contract)

| root | §2 size (q99 per full contract) | trades | gross (HAC t) | Holm p | efficiency (rotation p95; rank) | net | verdict |
|---|---|---:|---:|---:|---|---:|---|
| CL | 1 full ($892) | 236 | +$49.79 (1.35) | 0.80 | 0.123 (0.143; 0.910) | +$28.33 | DOES NOT TRANSFER |
| NG | 2 full ($391) | 230 | −$37.52 (−1.11) | 1.00 | −0.117 (0.159; 0.109) | −$53.52 | DOES NOT TRANSFER |
| **HO** | **NOT VIABLE ($1,117; no micro)** | 239 | **+$119.41 (2.74)** | **0.037** | **0.252 (0.203; 0.991)** | **+$109.21** | **UNRESOLVED (size)** |
| RB | NOT VIABLE ($1,151; no micro) | 242 | +$76.69 (1.85) | 0.35 | 0.161 (0.138; 0.974) | +$66.49 | DOES NOT TRANSFER (a) |
| HG | 1 full ($539) | 251 | −$12.00 (−1.15) | 1.00 | −0.085 (0.052; 0.409) | −$30.50 | DOES NOT TRANSFER |
| GC | 1 full ($662) | 259 | +$10.15 (0.54) | 1.00 | 0.046 (0.160; 0.551) | −$37.02 | DOES NOT TRANSFER |
| SI | 1 full ($925) | 273 | +$45.60 (1.78) | 0.38 | 0.175 (0.130; 0.984) | +$14.60 | DOES NOT TRANSFER (a) |
| ZC | 4 full ($238) | 239 | −$0.94 (−0.12) | 1.00 | −0.011 (0.126; 0.514) | −$19.44 | DOES NOT TRANSFER |
| ZS | 1 full ($667) | 249 | +$4.87 (0.35) | 1.00 | 0.032 (0.073; 0.860) | −$13.63 | DOES NOT TRANSFER |
| ZW | 3 full ($288) | 218 | −$0.23 (−0.01) | 1.00 | −0.002 (0.142; 0.510) | −$18.73 | DOES NOT TRANSFER |
| ZL | 4 full ($229) | 266 | −$6.61 (−0.96) | 1.00 | −0.076 (0.099; 0.277) | −$18.61 | DOES NOT TRANSFER |
| ZM | 1 full ($555) | 245 | −$5.31 (−0.57) | 1.00 | −0.048 (0.149; 0.214) | −$21.31 | DOES NOT TRANSFER |

**The split is by complex:**
- **The refined products and crude continue:** HO, RB and CL, plus SI.
- **Natural gas, copper, gold and every grain do not.** Their filtered gross is zero or negative.
- ρ of each root's daily net with NQ F2 is −0.03 to +0.09 (prediction 6 held).

## 2. Heating oil in full (one full HO, $10.20 a round trip, NOT VIABLE under §2)

**The four reporting groups:**

| | HO |
|---|---:|
| trades (a year) | 239 (about 44) |
| gross / net | +$119.41 / +$109.21 |
| net HAC t | 2.74 |
| hit (net), median net | 0.548, +$61.2 |
| net at a 10 % two-tailed trim | +$65.2 |
| daily Sharpe (Sortino), net | 0.92 (1.72) |
| before / after 2022-05-16 | +$96.1 / +$197.4 |
| without the January index-roll days | +$114.4 on 235 |
| take everything (unfiltered, gross) | +$22.9 (t 1.38) |

**By year** (n, net a trade): 2018 28, +138 · 2019 32, +118 · **2020 54, +1 · 2021 48, −1** · **2022 60, +286** ·
2023 17, +77.
- **2022 is about two-thirds of the net.**
- **2020–21 are flat.**

**The prop geometry at one contract:**
- the closed-trade trailing drawdown is **$4,304**, against a $2,000 limit;
- **9 days lose more than $1,000.**

**Why §2 reads it NOT VIABLE:** HO has no micro, and one full contract is twice the account's drawdown budget.

**Two caveats on the +$109:**
1. **The exit price is the close of the window's last minute.** On HO it sits a median of **9 ticks** from the official
   settlement (§4), so a TAS exit would differ.
2. **The cost line's crossing is one tick ($4.20).** The repo also records a quoted HO crossing of about 12 ticks
   (`d507_exec`, unverified). At that crossing ($6 + 12.2 × $4.20 = $57.24) the net is about +$62.

**RB** is the same shape, weaker: +$76.69 gross, t 1.85, efficiency rank 0.974, NOT VIABLE.

## 3. The oracle profile (reported; the evidence for any later filter design)

- **Take-everything gross is small or negative on every root** (HO +$22.9 is the largest). The filter's lift on HO is
  real by its rotation: rank 0.991.
- **The D630-style direction** (the return since the prior window close), take-everything:

  | root | gross (t) |
  |---|---:|
  | **NG** | **+$29.6 (2.36)** |
  | **SI** | **+$29.1 (2.98)** |
  | ZW | +$6.7 (1.59) |
  | HO | −$24.4 (−1.48) |
  | RB | −$24.3 (−1.46) |

  - **On NG and SI the day's direction since the last settlement carries, and the prior hour's does not.** This
    matches D630 and D709.
  - **On HO and RB the reverse holds:** the prior hour carries and the day's return fades.
- The full terciles and the aligned-against-opposed split are in the JSON.

## 4. A disclosed bug: the exit check (reported only, never gating)

**The runner's "exit against the official settlement" is void.** It divided the price gap by the tick's DOLLAR value
instead of its price size, so it read "100 % within 2 ticks" on every root.

**Recomputed correctly** (`scripts/diag_d719_exit_check_fix.py`, `data/diag_d719_exit_check_fix.json`):

| root | median ticks | share within 2 ticks |
|---|---:|---:|
| HO, RB | 9 | 0.17 |
| CL | 3 | 0.48 |
| NG | 2 | 0.54 |
| ZL | 2 | 0.65 |
| HG, GC | 1 | 0.72–0.74 |
| ZM | 1 | 0.79 |
| SI | 1 | 0.81 |
| ZW, ZS, ZC | 1 | 0.80–0.95 |

- Under §5, eight roots are **flagged** (below 0.8), not dropped.
- **No gate reads the exit check,** so no verdict changes.
- **What it means:** on the energy roots the window's last one-minute close is not the settlement price (the VWAP of a
  two-minute window). The trade as defined exits at that close.

## 5. Predictions

| # | prediction | outcome |
|---|---|---|
| 1 | gross positive on at least 9 of 13 | **failed**: 6 of 12 |
| 2 | NG, CL and SI gate (a) positive | **failed**: NG is negative; CL and SI are positive but short of Holm |
| 3 | full-size for the grains and HG, micros for NG, CL, GC and SI | **failed**: every sized root got full contracts, and HO and RB were NOT VIABLE |
| 4 | one to three transfer, one SIGNAL, NOT FEE | **failed**: none transfers; HO is UNRESOLVED on size |
| 5 | 2022 above 40 % on energy transfers | vacuous (none transfers) |
| 6 | ρ with NQ F2 below 0.2 | **held** |

## 6. Meaning and routing

- **F2's rule does not transfer to the commodity settlement windows as a family.** The grains, copper, gold and natural
  gas carry nothing on it.
- **Heating oil is a signal at a size the account cannot hold.** One HO contract's hold loss exceeds the daily limit,
  and its drawdown is twice the budget.
- **The honest routes, each the principal's call:**
  - a larger account;
  - a stop inside the hold (a new construction, pre-registered, which changes the rule);
  - or accepting it as a non-prop (personal-book) line.
- **In every case, confirmation would be on HO's held 2024-01 → 2025-02 slice and the vault,** under a new
  pre-registration.
- **Nothing is carried automatically.** No slot is spent.

## CLOSED by the principal, 2026-09-30: heating oil

**The principal:** "Ok close, Heating Oil".

**A correction first: "HO has no micro" (§2) was imprecise.**
- A micro exists: Micro NY Harbor ULSD (MHO), 4,200 gallons, $0.42 a tick, cash-settled against the HO futures price.
  CME's own contract-spec service confirms it.
- The repo's "no micro" came from `data/futures_contract_specs.json`, which fetched nine micros and never looked for
  one on HO.
- **The micro does not trade.** CME's volume service shows zero MHO volume on all 32 sessions from 2026-08-14 to
  09-29, with 2 contracts open, against about 187,000 a day on HO. The E-mini (QH, also 4,200 gallons) traded 13
  contracts in 31 sessions. Micro RBOB (MRB) returned no volume rows.
- Evidence: `data/d719_ho_micro_volume_check.json`.
- **So §2's NOT VIABLE reading stands:** no sub-size heating-oil contract can be traded, and one full contract is
  twice the drawdown budget.

**What the closure means:**
- None of §6's three routes is taken: no larger-account sizing, no stop-inside-the-hold construction, no personal-book
  line.
- HO's held 2024-01 → 2025-02 slice and its vault stay unread for this line. No slot is spent.
- RB, the same shape but weaker (fails Holm), closes with it.
- KE stays deferred, as before; it is not part of this closure.
- Reopening needs the principal's word and a new pre-registration. Re-tuning the in-sample result is not a route.
