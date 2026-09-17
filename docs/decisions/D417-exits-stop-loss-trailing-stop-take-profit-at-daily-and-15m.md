# D417 — exits: stop loss, trailing stop, take profit, at daily and 15-minute resolution

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D417-exits-stop-loss-trailing-stop-take-profit-at-daily-and-15m-resolution.md`. The H1 above is the full title.*

**Status:** design and bar committed BEFORE the runner exists (R8). Result separately.
**Date:** 2026-09-10
**Area:** Strategy research · execution

**Number.** `D417`, by PICKUP's three-command procedure: D400–D416 used, `D407–D410` reserved
(`044f839`), `D390–D399` reserved for `worktree-signal-hunt-part2` (`945cbb5`, live 14 hours ago).
Master takes D417.

**The principal's standing decision, recorded:** *no holdout is read until there is a tradeable
indicator.* `holdout2` stays unspent through this study and every study until that bar is met.

---

## 1. What this asks, and the two warnings it is built around

Three execution studies located the entry: the touch-day close, with a fixed five-day hold
([D416 §8](D416-RESULT-the-close-is-the-sweet-spot-located-from-the-third-side.md)). This asks
whether the **exit** can be improved on — a stop loss, a trailing stop, a take profit — with the
fixed time stop kept as the backstop in every case.

**Two warnings from CLAUDE.md govern the design:**

1. *"A tighter exit raises the win rate while lowering the mean."* **The gate is mean per trade,
   paired against the fixed exit on the same events.** Win rate is reported and flagged as what
   it is.
2. *"Cost-cutting ≠ edge-sharpening… say which moved: edge per unit exposure, or cost per trade."*
   Every trade is one round trip whatever the exit, so cost *per trade* is unchanged and every
   paired delta is net of matched costs — but an early exit shortens the hold, so **cost per unit
   time rises.** Mean hold and bp per day held are reported beside every mean.

**And the reason for two arms.** The only 15-minute bars are D414's 32 survivor names from 2018,
where the daily signal is not visible (cell-2 gross −2.20 ± 17 bp). An exit rule's value depends
on the shape of the return path *during the hold*: on a zero-mean sample a stop measures its
whipsaw cost and not its protective benefit. So:

| arm | events | resolution | role |
|---|---|---|---|
| **DAILY** | D413's 180,050 resolved touches, full universe | daily high/low triggers | **primary — the population where the signal lives** |
| **15m** | D414's 3,023 paired events, 32 names, 2018–2023 | 15-minute triggers | **precision check** — does intraday triggering change the daily-bar answer on the same events? |

The 15m arm runs the daily-bar rules on its own events too, so the intraday-vs-daily difference
is paired.

---

## 2. THE RULES — three families, one primary parameter each, no knob beyond that

Distances in the name's own **ATR₂₀ at the touch day** — the construction's own ATR, fixed for the
trade (D388: thresholds in the name's σ, never percentages). For a demand zone (long); supply is
the mirror via `sign`. **Every rule keeps the time stop: exit at the close of `t + 5` if nothing
fired.** Entry is the touch-day close; nothing can fire before the first bar of `t + 1`.

| family | rule | primary | shape |
|---|---|---|---|
| **SL** | exit when price trades at or beyond `entry − a·ATR` | **a = 1.5** | 1.0, 2.5 |
| **TS** | exit when price trades at or beyond `best − b·ATR`, `best` = the running best price since entry | **b = 1.5** | 1.0, 2.5 |
| **TP** | exit when price trades at or beyond `entry + c·ATR` | **c = 2.0** | 1.0, 3.0 |
| SLTP | SL 1.5 and TP 2.0 together | — | shape only, cannot clear |

**Three families is three tests at 2 SE, and the record will say so.** Each family clears only its
own gate; the shape values and the combination clear nothing (R14).

### 2a. Fill conventions — declared, and conservative in the direction that hurts

- **Daily arm.** A rule fires on day `d ∈ [t+1, t+5]` if the day's LOW reaches the stop (HIGH the
  target). Fill at the trigger price — **unless the day's OPEN is already through it, in which case
  fill at the OPEN.** A gap through a stop fills worse; a gap through a target fills better; both
  are taken as they fall. **The trailing best is updated at each daily close and checked against
  the next day's low** — never updated and checked inside the same bar. **If a stop and a target
  are both reachable on the same day, the stop fires.**
- **15m arm.** Identical logic on 15m bars from the first bar of `t+1` to the last bar of `t+5`,
  with the trail updated at each 15m close and checked against the next bar. Same-bar ambiguity
  resolves stop-first. The 15m arm inherits D414's `phi` basis and its `[ALIGN]`, `[BASIS]`,
  `[SAME-DAY]` assertions.

**`[FILL]`** — no stop fills better than its trigger and no target fills worse than its trigger,
asserted on every exit. A fill convention that could leak in the favourable direction is not
conservative, and this is the check that it did not.

---

## 3. Quantities, per rule, per arm

```
r_rule      = sign × (log P_exit − log P_entry)        the rule's trade
r_base      = sign × (log C[t+5] − log C[t])           D413's fixed exit, same event
delta       = r_rule − r_base                          PAIRED, the gate's quantity
hold        = bars (or days) from entry to exit
early       = share of trades the rule exited before t+5
cf_early    = r_base on the trades the rule exited early      what those trades would have made
cf_held     = r_base on the trades it held to t+5
std_ratio   = std(r_rule) / std(r_base)                the variance the rule bought, if any
bp_per_day  = mean(r_rule) / mean(hold)                edge per unit exposure
max_loss    = the worst single r_rule                  what the stop actually capped
```

**`cf_early` is the D415/D416 accounting applied to exits:** a stop that exits trades which would
have recovered is measured by what they would have made, not by the fact that they were stopped.

---

## 4. THE BAR — per family, primary parameter, DAILY arm pooled

| | condition |
|---|---|
| **T1(SL)** | `mean(delta_SL) > 0` by more than **2 paired SE** |
| **T1(TS)** | `mean(delta_TS) > 0` by more than **2 paired SE** |
| **T1(TP)** | `mean(delta_TP) > 0` by more than **2 paired SE** |

**A family clears its gate if and only if its primary raises the mean per trade.** `std_ratio`,
`bp_per_day`, `max_loss`, win rate and `cf_early` are **reported beside every gate and gate
nothing** — a rule that fails T1 while halving the tail is a risk tool, and whether that is worth
its mean cost is the principal's judgement, made with the numbers in front of them rather than
folded into a composite the runner chose.

### 4a. Cell 2 — declared SECONDARY, cannot clear

The same three tests on D413's 26,024 cell-2 events, labelled secondary, unable to clear D417 on
their own — the treatment every study since D414 has given it.

### 4b. The 15m arm — a precision check, not a gate

On the 3,023 D414 events: each family's paired delta at 15m and at daily resolution, and **the
paired difference between the two on the same events.** Reported: whether each family's sign
agrees across arms. **No gate** — 32 survivor names on a signal-free window cannot carry one — but
if a family's sign *flips* between arms, that is recorded as the finding it would be.

---

## 5. Stage 0

| | check |
|---|---|
| **P1** | counts reproduce exactly: 180,050 / 26,024 (daily), 3,023 / 900 (15m) |
| **P2** | trigger rate per rule per arm, and the distribution of the exit day / bar — a stop that fires on 90% of trades on day 1 is a different object from one that fires on 20% across the week |
| **P3** | the 15m arm's inherited assertions, reproduced; `[FILL]` on every exit in both arms |
| **P4** | **look at the object** — one cell-2 event printed end to end: entry, the five-day path, each rule's exit bar and price, each `r_rule` beside `r_base` |

---

## 6. Predictions

| | prediction | confidence |
|---|---|---|
| **X-a** | SL at 1.5 ATR fires on **20–35%** of daily-arm trades — the path out of a touch is volatile | moderate |
| **X-b** | **T1(SL) fails** — the mean falls, and `std_ratio` falls by more than 20%. ADDENDUM 3's marginals are positive through bar 5, so most stopped trades were recovering: whipsaw exceeds protection | moderate-high |
| **X-c** | **T1(TS) fails** — a 1.5-ATR trail on a five-day hold fires mostly on noise, for the same reason | moderate-high |
| **X-d** | **T1(TP) fails, pooled** — the average win is +410 bp, roughly two ATR for these names, so a 2-ATR target clips the winners that balance the −399 bp average loss | moderate |
| **X-e** | **the 15m arm agrees in sign with the daily arm on all three families** — intraday precision changes fill prices, not answers | moderate-high |
| **X-f** | **in cell 2, TP is the family closest to clearing**, because the bounce's marginals turn negative from bar 6 and a target caught near the peak exits before the give-back | low-moderate |

**X-b and X-d are the study.** If a stop lowers the mean, it is a variance tool with a price and
the price is printed; if a target lowers the mean, the right tail is doing work the fixed exit
already captures. **X-f is the one place a rule has a mechanism on its side**, and it is the one
this line has been circling since the hold sweep.

---

## 7. What this does not do

- **No holdout read**, by the principal's standing decision.
- **Does not read 2024+ on the 15m fixtures** — still reserved.
- No book, no slot cap, no path-variant lens. **No parameter sweeps beyond the declared shape
  values; no combined optimisation** of stop and target.
- **Does not gate on variance, Sharpe or win rate.** §4.
- **Does not recommend a disposition.** That is the principal's.

---

## 8. R13

Seventeenth look by object on price levels; fourth on execution; no new data spent.

**Cost: seconds on fixtures already on disk.**
