# 24 — the candidate ledger, BOTH books, one table

**Written 2026-09-08.** Every candidate any lane surfaced, dispositioned on **both** books
separately, under the principal's standing instruction that a strategy failing the prop constraints
is still worth keeping if it is a personal-book candidate.

**NOTHING HERE IS ACTIONED, and nothing is evidence under [R15](../../RULES.md#r15).** No cell
scored, no avenue opened or closed, nothing admitted to either book. Every row owes a
pre-registration.

**The reason the two columns differ is structural, not administrative.** These strategies run
**36–38% win rates at 2.1–2.25 payoff**. Low win rate × high payoff is exactly the P&L shape a
trailing drawdown destroys, because the floor marks the worst point of an excursion before the trade
resolves. **The prop instrument selects against positive skew; the personal book's R15 objective is
happy to buy that tail.** The two books want **opposite third moments**.

---

## The ledger

| # | candidate | prop | personal | the number that decides it |
|---|---|---|---|---|
| **C19-2** | late-day drift, last 15 min, CSI 300 (t = 10.1, N ≈ 945) | **the only [PROP] survivor** | yes | measured on the **index**, not the future — run the stale-price / closing-auction contamination test first |
| **C6** | short-horizon direction on **large-tick** CME outrights (ZN, ZB) | no — ZN's whole daily range is $310–390, so $150/day needs size the floor forbids | **the strongest [PERSONAL] lead** | `τ = tick/σ`, ranked monthly, split at median: survives iff large-tick beats small-tick by more than the bootstrap SE, post-2009 |
| **O1** | volatility-regime day classifier as an **abstention rule**, not a strategy | [PROP], and it is not an edge | n/a | survives iff floor-touch probability falls **relatively more** than expected P&L; else it is an exposure cut with a story |
| **C7** | Gotobi Tokyo-fix flow, 9:55 JST, dates divisible by 5 | no | yes | decompose the P&L into **move-into-the-fix vs swap carry** — the longest-holding config was the sole survivor, which is what carry predicts |
| **C1(r15)** | MNQ+MGC, 8,747 trades, splits and PF reproduce exactly | **conditional** — survives $10/RT at $15.63/trade | yes | **open-equity MAE**, which it does not report; it gives *closed-trade* drawdown, the wrong statistic against a trailing floor |
| **C5** | Carver's ~35-market trend + carry | no — breadth and holding period | yes | retail ES costs **13–17×** his cheapest-equity-index benchmark; any Sharpe at institutional cost is not ours |
| **C19-1** | close-vs-VWAP + closing-book imbalance conditioning the overnight on a **T+0** future | no — overnight hold | yes | 0.13–0.20%/trade on 72.5% of days vs 0.055% unconditional |
| **C19-3** | momentum in China: intraday and overnight halves **cancel** | no | yes | the **off-diagonal sign flip** (OC→OV −2.74% t=−13.89 against OV→OV +3.76% t=18.84). No cost assumption stated anywhere in the paper |
| — | spread / curve / calendar | **terminal on a rule**, not a return | yes | killed purely by the one-direction and hedging rules |
| — | short-term systematic trend | no — drawdowns 2.5–7.5× the barrier | yes | killed purely by a drawdown budget |
| **~~S1~~** | ~~intraday momentum, ES/NQ~~ | **WITHDRAWN** | **cautionary only** | three reimplementations return **Sharpe 0.399** against a published 1.33, gap isolated entirely to the bid/ask spread, **with the author answering in writing** |

---

## The one shape constraint, which is worth more than any single row

**The scissors close on LONG WINDOWS, not on small edges.**

Every prop rejection in this review is a **size** rejection: a short holding window forces contract
count up against a fixed dollar floor. Cost is only 15–20% of the gross mean and was never binding.
**Widening the holding window relaxes the lower bound without touching the upper one** — which is why
C19-2, on a 15-minute window carrying ~18 bp of s.d., puts one ES contract at a $150 day with the
$2,000 floor 3.4σ away, while a 30-minute-hold effect at three times its per-trade Sharpe cannot.

**So the search was mis-specified.** We were looking for a bigger edge; the binding variable is the
hold.

---

## What is missing for BOTH books, and it is the same quantity

**Maximum adverse excursion within the holding window**, measured on **open equity**.

Four independent confirmations that nobody publishes it:

| source | what it stores instead |
|---|---|
| the academic literature (lane 13) | means, SDs, Sharpes — **no academic objective is path-dependent inside a trade** |
| the open-source implementations (lane 17) | `equity_by_day[day] = equity` — no intraday equity in any repo read |
| the best-documented candidate (lane 16) | **end-of-day** portfolio drawdown, with its author conceding *"the higher the observation frequency, the higher the measured maximum DD"* |
| the best retail record found (lane 15) | **closed-trade** drawdown |

**The prop book is priced on it.** And the personal book has never measured it either — so it is not
a prop quantity that happens to be missing, it is a gap in how both books are evaluated.

---

## Two premises now in doubt that neither book had questioned

1. **The overnight drift may be a property of the SETTLEMENT RULE, not of time.** T+1 cash and T+0
   futures on the same underlying and the same days give **opposite signs, both significant** —
   index −0.073% (t = −4.03), future +0.055% (t = +3.19). **C1 was an overnight futures hold measured
   on equity extended-hours bars**, so its premise may never have been the thing its proxy measured.
2. **The prop track has been screened at a third of the available breadth** — 1.17 effective against
   3.00 for a diversified futures complex, worth **1.6× on IR**. C1 and C2 were both screened at 1.17.

---

## Closed by lanes 21 and 22, with computed reasons

**Order flow / microstructure — closed, and the arithmetic is committed** (`data/lane21_horizon_cost.py`).
**There is no horizon where edge exceeds cost, and the two move in opposite directions.** The signal's
life is **~1 second**, from four convergent measurements including one on ES itself — CME BBO files,
1,490 days, 34.5M one-second samples: *"shocks dissipate almost entirely within a second."* Meanwhile
**ES is a pinned one-tick book** (spread p1 through p75 all exactly 0.25), so a taker's round turn is
one full tick: **$16.50 = 1.32 ticks** at retail commission. Required directional accuracy is **0.72
at the single most generous cell, and exceeds 1.0 in seven of twelve** — where a perfect forecaster
still loses. Documented accuracy from the literature's own R² of 1–5% is **0.53–0.57**.

- **The famous "order flow explains 65% of price moves" is a CONTEMPORANEOUS regression** — same
  10-second interval, with the authors flagging the tautology themselves. The *predictive* R² for the
  identical quantity is **1–5%**. Every page citing 65% is citing the wrong number.
- **"Retail is too slow" is false here** — 25 ms against a 1-second signal is 2.5% of its life. **Cost
  binds, not speed**, so a Chicago VPS diagnoses it wrong.
- **Absorption is real and quantified** (an iceberg cuts impact ~80%, 2.2 → 0.3 bp) **but no paper
  tests whether it predicts a reversal**, and the nearest directional evidence has the **opposite
  sign**: detected icebergs fill *faster* because they attract market orders.
- **Stop runs die three ways.** The round-number effect is *continuation*, not reversal. Stops are
  **0.9% of ES volume** and **98% of executed ES stops are stop-limit** with protection points — wrong
  order type, not enough fuel. And where stop-hunting is proven, the trader knew the levels because
  the stop was placed through his own bank.

**A LIVE DISCONFIRMATION of the family lanes 13/14 nearly kept.** **HFSP (Tidal Trust III)** is a
registered ETF whose *compelled* Principal Investment Strategies section describes it almost word for
word — intraday ES long/short, minutes to hours, flat by the close. **Audited NAV $20.00 → $15.32,
−23.4% over ~16 months, $766k net assets.** N of one and prior-moving rather than dispositive, but it
is the only instance anywhere in this review of the strategy being run for real money under audit.

**And the regulated tier does not run intraday at all.** In an eight-advisor managed-futures
prospectus the shortest disclosed average hold is **2–3 days**. EDGAR full-text for
`"holding period" "less than one day" "trading approach"` returns **zero documents corpus-wide since
2015.**

## A NEW TERM FOR D379 THAT NOTHING HAS COMPUTED

**The barrier is administered against a market that can suspend your exit.** CME Velocity Logic halts
ES on a move exceeding the price band within a rolling **millisecond**, producing a five-second
pre-open in which *"trade matches will not occur"*; Dynamic Circuit Breakers run 2 minutes overnight
to 15 minutes in RTH. The Joint CFTC–SEC report on 2010-05-06 states the ES Stop Logic pause existed
**specifically to prevent a stop-loss cascade**.

**A prop floor marked on open equity keeps moving through exactly those windows.** So D379's
down-and-out call is written on an underlying subject to **random trading suspension at peak
volatility** — strictly value-reducing, and uncomputed in every valuation this session produced.
Falsifier is specified: count the halts, measure the cross-halt price change.

**And impact is not the constraint people assume.** ES whole-book buy-side depth averages ~100,000
contracts in the opening half-hour; 20 contracts is **0.02%** of it. **Impact scales √N while the
drawdown constraint scales N — they cannot cross in the retail range.** The size scissors confirmed
from a third independent direction, with no execution-side fix available.

## And the bound that has not moved all day

**Research allocates an edge; it does not supply one.** Eight lanes across the literature, forums,
open source, code, verified records and five languages produced **one prop-eligible candidate with a
known contamination risk**, and a set of personal-book leads that each owe a pre-registration.
Nothing here changes what is in either book, and nothing should be read as recommending that it does.
