# The prop account, in closed form

[← venues index](00-index.md) · next: [rules and conduct](02-prop-rules-and-conduct.md)

**This is the one research stream whose central result has already crossed into the repo** — as
**D386** — and the crossing went in both directions: the decision record then **corrected the research
folder**, which was amended in place with the withdrawal visible.

---

## The result `[REPO]` D386 / `[EXT]` synthesis

> **At zero edge the expected lifetime extraction from a funded account equals the drawdown buffer,
> EXACTLY.**
> Optional stopping: the balance is a martingale, total extracted plus final balance equals the
> start, and the final balance at ruin is the floor. So **`E[extracted] = b`, whatever the payout
> ladder says.**

**Verified at ratio 1.0000** against a renewal closed form **and** a direct simulation.

**The payout ladder is decoration.** Apex's six rungs from `$1,500` to `$3,000` realise **`$1,974`
against a `$2,000` buffer** — the entire structure is worth **−1.3%** relative to no ladder at all.
**The one thing a ladder does is CAP extraction when the buffer is large relative to the rungs.**

> **The ceiling on a funded account is the buffer, and the buffer is the amount the firm permits you
> to lose.** On a 50K account that is `$2,000` — **and you reach the payout regime at all with
> probability 0.37.**

## The arithmetic, at list prices `[EXT]`

| | Apex 50K EOD | Apex 150K EOD | Topstep 50K XFA |
|---|---:|---:|---:|
| `E[extracted]` (= buffer, less the ladder cap) | $1,974 | $3,902 | $2,000 |
| × P(reach the lock) | **0.3743** | **0.3936** | **0.3911** |
| = `E[payout │ funded]` | **$739** | **$1,536** | **$782** |
| zero-edge P(pass) | 0.2495 | **0.1348** | 0.2664 |
| evaluation fee + activation | $550 + $139 | $1,890 + $159 | $49/mo + $149 |
| **V per evaluation, at list** | **−$400** | **−$1,706** | **+$120** |

**The break-even question, asked correctly:**

| break-even annual Sharpe | Apex 50K @ $250/day | Apex 150K @ $750/day | Topstep 50K @ $250/day |
|---|---:|---:|---:|
| at list price | **≈ 0.55** | **≈ 1.60** | below zero |
| at the ~90% discount | below zero | ≈ 0.01 | n/a |

**A withdrawn claim, kept visible:** *"Apex 150K at list is negative at ANY edge"* was **WITHDRAWN**.
A break-even *pass rate* above 1 means **"unreachable by moving one term while pretending the other is
fixed"**, not "impossible" — **edge raises both terms.**

**Two conclusions that survive.** **The discount is not a promotion, it is the price** — at the ~90%
codes the product goes from impossible to **positive with no skill whatsoever**, which is what the
list price exists for. *(Claims-tier observation, not a term.)* And **Topstep's `$49` is MONTHLY**;
at the ~58-day mean time-to-resolution the true acquisition cost is nearer `$147`, lifting break-even
to ~0.23 against a zero-edge 0.2664 — **marginal, not comfortable.**

> **And all of the above is at ZERO edge, which FLATTERS the real population.** Topstep's own
> published per-Combine completion rate is **16.8%** against a zero-edge baseline of 26.6–31.7% —
> **86 to 124 standard errors below a coin flip.** The marginal buyer has *negative* edge.

## Why zero families survive, and it is geometric `[EXT]` lanes 13/14

**Two lanes searched independently against a seven-point screen. Both returned zero survivors and the
same single conditional near-miss.**

**The expected killer was wrong — cost is the screen these effects pass most EASILY**, clearing a
`$10–22.50` round turn by **3.8–8.6×**.

> **What kills them is that two screens are the blades of a scissors.** Position size scales mean and
> standard deviation together while the drawdown stays fixed at ~`$2,000`:
> **the `$150+` qualifying-day rule sets a LOWER bound on contracts; the 4% trailing MLL on open
> equity sets an UPPER bound; and for every effect found the lower bound EXCEEDS the upper — by 4.5×
> on ES.**

Closing it needs per-trade Sharpe **0.225** (annualised 3.57). The best-documented candidate delivers
**0.068** — a **3.3× shortfall.**

**Lane 14's independent framing: the rule set is a VICE, not a hurdle series.** The open-equity floor
kills **negative** skew by marking the worst point of an excursion before it resolves; the consistency
rule kills **positive** skew by capping the best day at 50% of total profit. **What survives in the
middle is near-symmetric low-variance daily P&L — exactly what a fixed-dollar round turn destroys.**

## THE SHAPE CONSTRAINT — the most actionable line in the stream `[EXT]`

> **THE SCISSORS CLOSE ON LONG WINDOWS, NOT ON SMALL EDGES.**
> **Every prop rejection in this review is a SIZE rejection**, driven by a short holding window
> forcing contract count up against a fixed floor. **Widening the window relaxes the lower bound
> without touching the upper one.**

A 15-minute window carrying ~18 bp of s.d. puts **one ES contract at a `$150` day with the `$2,000`
floor 3.4σ away** — while a 30-minute-hold effect at **three times** its per-trade Sharpe cannot.

> **So the search was mis-specified. We were looking for a bigger edge; the binding variable is the
> hold.**

## The tool that makes every published claim comparable `[EXT]`

**Per-trade Sharpe is recoverable from any published `t` as `t/√N`.** That makes the 0.225 threshold
applicable to **every** claim in the review, not only those reporting per-trade moments.

## The blocking gap, and it is structural `[OPEN]`

> **Maximum adverse excursion within the holding window is not published for ANY candidate,
> anywhere** — four targeted probes. **Finance reports means, SDs and Sharpes because no academic
> objective is path-dependent INSIDE a trade.**
> **The one quantity the funded account is priced on is the one quantity the literature does not
> measure.** Every screen-4 verdict is therefore a **σ-based lower bound on severity, not a
> measurement.**

**The cheapest thing that would change the answer:** `P(MAE ≤ $2,000/contract)` for the
last-30-minute trade — **one query against ~`$8` of Databento `GLBX.MDP3`, inside the existing signup
credit.** → [futures data sources](../data/05-futures-data-sources.md)

## The three corroborations of our own work `[REPO]`-adjacent

1. **Lane 13's survival probability is non-monotone in size** — 8.1% at N=1, 0.5% at N=2–3, back to
   7.8% at N=10 — **reproducing D379 §2's interior optimum from an entirely separate calculation.**
2. **The two books want opposite third moments.** These strategies run **36–38% win rates at 2.1–2.25
   payoff**; low win rate × high payoff is exactly the shape a trailing drawdown kills, **so the prop
   instrument selects AGAINST positive skew — the same tail the personal book's R15 objective is
   happy to buy.**
3. **Drawdown is 17× more persistent out-of-sample than Sharpe** (888 algorithms: R² 0.02 for Sharpe,
   0.34 for max drawdown). **The statistics the barrier reads are the ones that survive.**

## The candidate ledger, both books

[`24-candidate-ledger-both-books.md`](../../Prop-Firm-080926/24-candidate-ledger-both-books.md) — one
table, eleven rows, **each with the number that decides it.** Highlights:

- **`C19-2`** — the only `[PROP]` survivor, **and its falsifier is the stale-price / closing-auction
  contamination test.** *That test is what prompted D402 on our own book.*
  → [intraday and overnight](../signals/09-intraday-and-overnight.md)
- **`C6`** — large-tick CME outrights: **the strongest `[PERSONAL]` lead**, dead for prop because
  ZN's whole daily range is `$310–390`.
- **`~~S1~~`** — **WITHDRAWN**: three reimplementations return Sharpe **0.399** against a published
  **1.33**, the gap isolated **entirely to the bid/ask spread**, **with the paper's author answering
  in writing.**

**And the standing rule from memory:** *prop-ineligible is still worth keeping* — the barrier is a
property of the instrument, not of the strategy. **Disposition every candidate on both books
separately.**

---

**Sources.** [`00-SYNTHESIS.md`](../../Prop-Firm-080926/00-SYNTHESIS.md) ·
[`24-candidate-ledger-both-books.md`](../../Prop-Firm-080926/24-candidate-ledger-both-books.md) ·
lanes [13](../../Prop-Firm-080926/13-documented-intraday-effects.md),
[14](../../Prop-Firm-080926/14-practitioner-tier-screened.md),
[20](../../Prop-Firm-080926/20-verified-track-records.md) ·
repo: **D386**, `scripts/d386_account_value.py`, [`BOOK_PROP.md`](../../../BOOK_PROP.md).
