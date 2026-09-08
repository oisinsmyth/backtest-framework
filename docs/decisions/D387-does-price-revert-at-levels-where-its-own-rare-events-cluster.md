# D387 PRE-REGISTRATION — does price revert at levels where its own RARE events cluster?

**R8: committed before the runner exists. Result separately.**

**This is a SIGNAL test under [R15](../RULES.md#r15), not a premise check.** D384 and D385 were both
premise checks and both answered a question nobody asked. The criterion here is R15's: **a positive
GROSS mean per trade above the nulls.** Costs and confluences later. It admits nothing — admission
needs R8's separate out-of-sample test on holdout #2, which this record does not touch.

---

## 1. What D385 established, and why this study is different

D385 is **untested, not refuted** (`c4cd5ed`). Three faults, all mine, and this record fixes all three:

| D385's fault | fixed here |
|---|---|
| **Wrong statistic** — TV(density, shuffle) is a functional of the density ALONE and cannot see whether the density predicts returns (t=+4.62 signal, identical TV) | the statistic reads **FORWARD RETURNS** |
| **Wrong input** — swing lows occur on 24% of bars, so the event density reproduced its own calibration (ratio median 0.974, peak 1.46× median) | the two **RARE, non-definitional** cousins |
| **Wrong memory rule** — event-time decay forced `hl_bars = hl_ev/rate`, giving types 600-bar vs 218-bar coordinates | **construction (a)**: one calendar λ centres everything |

**THE DECAY FORK IS RESOLVED TO (a), PLAIN DECAY, AND THE PRINCIPAL WAS RIGHT.** He objected to
event-time decay on coherence grounds — the centring EMA runs on calendar time, so the two memories
come apart. I overrode it for one reason, constant `n_eff`, and **D385 showed `n_eff` was never the
binding constraint** (57.7–227.6, all adequate, nothing cleared). That single override produced the
600-vs-218-bar incomparability, the 6.1e-08 artefact, and the confound on the rarity reading.

```
g_t = λ g_{t-1} + (1-λ) A(u; x_t)                    every bar injects
f_t = λ f_{t-1} + (1-λ) A(u; x_t) · 1{event at t}    only an event bar injects
x_t = log P_t − log EMA_λ(P)_t                       ONE λ centres, calibrates and decays
```

**`∫f_t` is EXACTLY the EW event rate** (verified to 1.7e-16), so **shape and rate are separable**:
`f̂ = f/∫f` is where events sit, `∫f` is how often they happen. Rarity is information, not a filter.

---

## 2. Why these two event types, and only these two

Measured share of each event type sitting **below** its EMA, against a **36.0% base rate** across all
bars (`temp/d385_fork_and_cousins.py`, 20 names, half-life 60):

```
     highest in 60:    0.7%      lowest in 60:   91.5%     <- DEFINITIONAL
     highest in 20:   14.9%      lowest in 20:   68.4%     <- DEFINITIONAL
         swing low:   35.8%                                <- FLAT: equals the base rate
      reversal >1%:   58.4%       move >2%:      67.2%     <- NEITHER
```

**The extremes-in-N are excluded because their positional tilt IS their definition.** A 60-bar low is
below its EMA 91.5% of the time because that is what a 60-bar low means; a density built on them
mostly restates the definition, and any "excess" against a location-blind control is tautology. **A
first draft of this study measured exactly that tautology at 28–34 SE, and it was caught by asking
whether the tilt was definitional before reporting it.**

**`swing low` is excluded because it is flat** — 35.8% against a 36.0% base. That is D385's whole
null result, explained.

**`reversal >1%` and `move >2%` are neither.** Nothing in their definition says where they must
occur, yet both sit far below the EMA (58.4%, 67.2%). **That tilt is the only non-tautological,
non-flat positional fact this line has produced.** They are also the two types D385's §3 excluded —
my narrowing selected for statistical power and against information.

**Disclosed alternative explanation, which the null must settle:** the downward tilt may be plain
volatility asymmetry — big moves and reversals cluster in selloffs. **N2 preserves the return
distribution and the volatility path, so if that is all this is, N2 will match it.**

---

## 3. The signal, and its ONE declared direction

**The conditioner at bar `t`:**

```
R_t = f̂_t(x_t) / g_t(x_t)          excess past-event mass AT THE PRICE'S CURRENT LEVEL
```

`R_t` large means *price is now sitting where a disproportionate share of this name's past rare
events happened*. `R_t ≈ 1` means the level is unremarkable.

**Eligible bar:** `R_t` above that name's **expanding causal 90th percentile** of `R` over bars
`< t`. No threshold is estimated on data at or after the bar it gates.

**THE DECLARED DIRECTION IS REVERSION TOWARD THE EMA.** The hypothesis is support/resistance: a level
that has repeatedly produced rare events is a level price struggles to pass. So the trade is signed
**toward `x = 0`** — **long when `x_t < 0`, short when `x_t > 0`** — held `H` bars, scored gross.

**The opposite direction (continuation) is a SECOND LOOK and is declared as one**, reported beside the
primary and counted in §7's ledger. D382's gate 1h was under-specified in exactly this way — "extreme"
had two ends, both got scored, and the result became a best-of-152. **Not repeating it: one primary,
one declared secondary, both counted.**

---

## 4. The grid

| | |
|---|---|
| **event types** | `reversal >1%`, `move >2%` — 2 |
| **λ (centring, calibration and decay)** | **60, 120, 250 bars** — 3, swept, reported, never picked |
| **hold `H`** | **5, 10, 20 bars** — 3 |
| **direction** | **1 primary (revert)** + 1 declared secondary (continue) |
| **universe** | `us_shorts_daily_raw.csv.gz` — liquid US single names, **600 sampled** of 1,573 |
| **draws** | **N2: 20** (rebuilds everything, expensive) · **A′: 200** (reuses the density, cheap) |

**18 primary cells**, correlated through a shared construction.

**Single names, not ETFs, and that is the principal's call applied**: an ETF is a basket, so its
levels are the average of its constituents' levels and should wash out — and D382 already found the
daily ETF structure family was market drift. D384 and D385 both ran on ETFs; that was a second
reason the venue was unfavourable and I did not weigh it.

---

## 5. Split, and what is spent

**The mining prefix (`order[:3400]`, this fixture's 1,573 names) is "spent many times over; free to
mine further" per the holdout ledger.** The full date range 2010-01-04 → 2026-08-26 is mined.

**No date window is reserved, and the record says so rather than claiming a reserve it cannot
guarantee.** Prior studies have mined this fixture across its range; declaring part of it "unseen"
would be a fiction. **The cost is the prior, and admission requires holdout #2** (`order[5100:6300]`,
576 names, UNSPENT), which this study does not read.

**`[SPLIT]` is the default-deny audit hook** from `run_d365_momentum_buffer.py`: any path containing
"holdout" raises. **This runner never calls `allow_holdout`.**

---

## 6. What is measured — all four groups, per CLAUDE.md

**Primary (R15): GROSS mean per trade**, path-invariant lens — every eligible bar is a candidate
trade, no slot cap, scored **per TRADE**. The path-variant book lens is a separate study and this
record does not mix the two on one statistic (FINDINGS §10).

1. **Performance, gross AND net side by side** — plus exposure, mean move per trade against `2c`,
   and **breakeven cost in bp/side**. Spread estimated **Corwin–Schultz off the OHLC of the names
   actually held**, not a fee assumption (D285 missed a guessed bar by 0.65 and the held names
   measured 33.8).
2. **Trade distribution** — count, mean, **median**, win rate, payoff, holding run, skew, kurtosis,
   and the **1% two-tailed trim reported all three ways** (ex-top, ex-bottom, trimmed).
3. **What the winners depend on** — names to reach half the P&L, top-1/5/10 name share, profitable
   years, and the split by **dead vs alive**, **era**, and **price**.
4. **Nulls as distributions** — **p50 and p95 beside the score**, and an explicit statement of
   whether the null is decisive.

---

## 7. Nulls

| | |
|---|---|
| **N2 — LOAD-BEARING** | iid bootstrap of standardised returns rescaled by the observed volatility path. Regenerates the path, **and therefore the events, the EMA, `x`, `f`, `g`, `R` and the trades, by the identical code path.** Settles §2's volatility-asymmetry alternative |
| **A′ — the persistent-selector control** | **time-rotate the density**: decide bar `t` using `f̂` and `g` from bar `t−k`. Same bar count, same eligibility mask, same persistence. **Randomises the PARTNER, not the membership** — a random subset re-draws each bar and churns (D291: 2.4× the entries, 87 cells voided) |

**Every A′ draw must satisfy the observed events' own eligibility mask**, asserted, not assumed —
D347's rotation traded the excluded tail and its headline inverted when fixed (D351).

**R13 ledger:** 18 primary cells + 1 declared secondary direction, on the hypothesis *"price reverts
at levels where its own rare events cluster."* Correlated through one construction, so the effective
count is well below 18; the floor is the empirical best-of-N over this search, computed from the data
rather than assumed.

---

## 8. Assertions

| tag | what it proves |
|---|---|
| **`[LAG]`** | the held set at `t` is re-derived from `R[:, t-1]` in a **second implementation that never calls the selection function**. Killed D279's first result — ~93% of its edge was this bug |
| **`[SIGN]`** | asserted **in money**: a favourable move pays positively, and the long and short legs move **oppositely** on the same input. A sign asserted in prose inverted D280 |
| **`[QTY]`** | the scored grid differs from the one not meant to be scored |
| **`[MASS]`** | `∫f_t` equals the EW event-rate EMA to 1e-12 — the identity that makes shape and rate separable, and the whole reason the fork resolved to (a) |
| **`[CAUSAL]`** | `R_t` and the expanding quantile threshold read **no bar after `t`**, proved by shocking a future bar |
| **`[POOL]`** | every A′ draw satisfies the observed eligibility mask; **entry counts match within 1%** |
| **`[NULL]`** | N2 keeps the volatility clustering and the return distribution and destroys direction; the event function is literally the same object on observed and null |
| **`[REC]`** | `lfilter` equals the explicit loop bit-identically on a tie-heavy input |
| **`[SPLIT]`** | the holdout audit hook is installed and `allow_holdout` is never called |
| **`[X]`** | every audit raises on a break that **moves the exact scalar it compares** — three duds this session broke what the assertion was *named* for |

---

## 9. Predictions

| | |
|---|---|
| **Q1** | **the primary clears N2 somewhere**, and if it does not, the positional tilt of §2 was volatility asymmetry and the whole line is finished |
| **Q2** | **`move >2%` beats `reversal >1%`** — a 2% move is a cleaner event than a sign flip with two soft thresholds |
| **Q3** | **A′ is the harder null**, because the density is highly persistent, so rotating it by `k` bars changes little. If A′ is *easier* than N2 I have mis-built it |
| **Q4** | **the gross edge is smaller than the round trip.** D373's entry-timing effect was real and worth ≤ half a round trip; this is the same kind of effect and I expect the same fate |
| **Q5** | **shorter holds beat longer** — a level is a local object |
| **Q6** | **AGAINST myself: the mean exceeds the median**, i.e. a few big winners carry it, and the two-tailed trim will cut it hard |
| **Q7** | `[LAG]` and `[CAUSAL]` hold first time. **D384's Q7 and D385's Q7 both made this prediction; `[FRAME]` fired twice and `[STAT]`/`[CAUSAL]` fired once each. Third time asking.** |

---

## 10. What would make me abandon this

- **`[MASS]`, `[LAG]`, `[SIGN]`, `[CAUSAL]` or `[NULL]` fails** → the construction or the null is not
  what this record describes. Stop, fix, publish nothing.
- **The primary gross mean per trade is negative or inside N2 at every cell** → price does not revert
  at these levels; under R15 the positional tilt of §2 was volatility asymmetry. **Report it as the
  close of the density line, and this time on a statistic that could have detected the thing.**
- **The primary clears but the secondary (continuation) clears equally** → the conditioner is marking
  volatility, not direction. Report as such; it is a different and weaker claim.
- **`[POOL]` shows A′ churning** → the control is D291's broken one and no cell it judges is readable.

---

*Pre-registered 2026-09-08. Runner does not exist at the time of this commit (R8). Signal test under
R15: gross mean per trade above the nulls. Admits nothing — admission requires holdout #2, untouched
here. The decay fork of D385 §3 is resolved to (a) and the principal's objection is upheld.*
