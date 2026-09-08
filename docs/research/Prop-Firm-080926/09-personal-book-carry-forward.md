# 09 — What carries to the PERSONAL book

**Written 2026-09-08**, under the principal's standing instruction recorded in
[`00-SCHEMA.md`](00-SCHEMA.md):

> A strategy that surfaces here and cannot pass the prop constraints **is still worth keeping** if
> it is a candidate for the personal book.

---

## VERDICT FIRST

**No strategy surfaced, and none was prop-rejected, so the carry-forward list is empty of
strategies.** This research was about the *instrument's terms*, not about edges, and that is what it
delivered. Saying otherwise would inflate it.

**What does carry is five items of sizing theory and modelling correction, four of them from lane
08, and one of them lands on a result this programme produced yesterday.** None is evidence under
[R15](../../RULES.md#r15). Each owes a pre-registration ([R8](../../RULES.md#r8)) before any runner.

| # | item | bears on | strength |
|---|---|---|---|
| 1 | Grossman–Zhou sizing is a **fifth challenger** D372 does not list | [D372](../../decisions/D372-equal-weight-is-the-incumbent-sizing-and-the-hurdle.md) | **strong** — named gap in a live pre-registration |
| 2 | Broadie–Glasserman–Kou puts a **number** on D381's "a stop is a late trigger" | [D381](../../decisions/D381-RESULT-a-stop-is-a-late-trigger-and-the-median-mean-exchange-rate-is-fixed.md), [D169](../../decisions/D169-the-short-book-and-its-close-based-stop.md) | **strong** — quantifies a result committed yesterday |
| 3 | The vol-managed literature's headline was a **look-ahead artefact in the vol estimator** | D372 `IV`/`IVT`, [youtube-lessons §5](../../youtube-lessons.md) | **strong, and it is a warning about our own C1** |
| 4 | Bold-vs-timid play is a **theorem**, and it flips on the sign of the edge | D372 incumbent `EW` | moderate |
| 5 | `d386_pass_rate.py` is **reusable infrastructure** for any drawdown question | anything with a path constraint | infrastructure, not a finding |

---

## 1. Grossman–Zhou is a fifth challenger, and D372 does not list it

D372 declared equal weight (`EW`) the incumbent and named four challengers — `IV`, `IVT`, `RE`, `RW`.
**All four size on volatility or on rank. None sizes on distance from a drawdown constraint.**

The drawdown-constrained portfolio-choice literature (Grossman & Zhou 1993; Cvitanić & Karatzas 1995;
Cherny & Obłój 2013) gives a closed-form policy: **optimal risky exposure is proportional to the
surplus `W − αM`** above the constraint, and goes to **zero** at the floor. That is a genuinely
different sizing family from anything in D372's table — it is *path-dependent*, keyed to the book's
own running maximum rather than to a name's volatility.

**Why it belongs to the personal book and not the prop book, which is the whole point of this file.**
The literature's result is **sign-opposite to D379 §5**, which predicts risk-*shifting* near the
barrier. Both are right, and the discriminant is ownership: **GZ assumes the agent owns the wealth,
so ruin is a real loss. A prop trader's downside is truncated at a sunk fee, so it is not.** The
personal book is the case where the agent owns the wealth. So this is the frame for `BOOK.md`, and
D379 §6 states the wall only in the other direction.

**What it does NOT license.** D372 §3's prior stands: estimation error usually exceeds the
optimisation gain, and `EW` cannot be overfit while every challenger is a parameterised family. GZ
adds a *parameter* (`α`) and a *state* (the running max), so it is more exposed to that critique than
`IV`, not less. It also inherits D372 §5's trap — it must be scored on the already-floored universe.

---

## 2. Broadie–Glasserman–Kou puts a number on D381's "a stop is a late trigger"

[D381](../../decisions/D381-RESULT-a-stop-is-a-late-trigger-and-the-median-mean-exchange-rate-is-fixed.md)
concluded yesterday that **a stop is a late trigger by construction** — the threshold is only reached
*after* the adverse move, and cutting the worst 5% at a **random** bar (+226.52) beat cutting them at
−3,229 (+142.79). That is a statement about *ordering*. It carries no magnitude.

**BGK's continuity correction supplies the magnitude.** A barrier monitored at discrete intervals
prices like a continuous barrier displaced by `β·σ·√Δt`, with `β = −ζ(½)/√(2π) ≈ 0.5826`. For daily
monitoring that is **0.5826 σ_daily** — lane 08 computes **$291 at σ = $500/day**.

**Why this is a personal-book item.** [D169](../../decisions/D169-the-short-book-and-its-close-based-stop.md)
gives the short book a **close-based** stop. BGK says a close-monitored stop *behaves like a
continuous stop set roughly 0.58 daily sigmas further away* — so the effective stop is not the stop
in the record, and the gap is computable per name from its own volatility. That is a specification
question about machinery already in the books, and it is answerable without any new fixture.

**What it does NOT license.** BGK assumes geometric Brownian motion with a *constant* barrier. Our
stops are close-based on fat-tailed single names with gaps, where the correction understates the
displacement. Treat 0.5826 σ as a **lower bound on the lateness**, not an estimate of it. And D381 §5a
already warns that under a hard drawdown limit the criterion changes from mean to return-per-unit-
drawdown, which is a different question again.

---

## 3. The vol-managed headline was a look-ahead artefact — and our own C1 is a vol-target sweep

Lane 08 marks the volatility-managed-portfolio literature **decorative** for the prop question, and it
is right: the Moreira–Muir vs Cederburg dispute is about *return timing*, not barrier control.

**But one finding in it is not decorative for us.** Liu, Tang & Zhou found the headline vol-managed
result was a **look-ahead artefact in the volatility estimator**. That bears on three things here at
once:

1. **D372's `IV` and `IVT`** size on a trailing volatility estimate. D110 already pins the estimator
   to bars ending at t−1 (D44), so the specific defect is guarded — but the guard should be
   *asserted in the runner*, not inherited by assumption, because this is precisely the failure that
   killed a published literature.
2. **[youtube-lessons §5](../../youtube-lessons.md)** — the GARCH video — sits in the same family, and
   the measured result there was that a GARCH forecast is 0.9961 correlated with an EWMA and 0.8935
   with D110's existing 20-day trailing estimator. So the estimator choice buys little, and the
   look-ahead risk is the larger exposure of the two.
3. **BOOK_PROP's C1 evidence is itself a vol-target sweep** ([D260](../../decisions/D260-the-vol-targeted-overnight-hold.md)).
   Take that personally: the same class of defect that inflated a literature could inflate a sweep of
   ours. Worth an explicit look-ahead audit of C1's estimator before D379 §6's item 1 extends its
   size sweep.

---

## 4. Bold-vs-timid is a theorem, and it flips on the sign of the edge

Dubins & Savage: **bold play is optimal when the game is subfair.** Ross (1974) and Maitra–Sudderth:
**timid play is optimal when it is favourable.** My own Stage 0 run confirms the first half
empirically and independently of D379 §A2 — every trailing column rises monotonically with risk size
at zero edge.

**The carry-forward is the second half, and it is a caution against reading the prop result across.**
The personal book is the favourable case, where the theorem says *timid* — many small bets rather
than few large ones. `EW` across ~20 names per leg already is timid play, so this is a theoretical
justification for the incumbent that D372 §3 does not have. It argues **against** any challenger that
concentrates.

**What it does NOT license.** "Favourable" means a positive expected edge, and R15's standard for
that is a positive gross mean per trade **above its nulls** — which S1 and S2 have and which neither
is at capital for. The theorem says nothing about how large the edge is, and D378 already put the
entry-timing increment at **0.19–0.47× a round trip** under PUB. A theorem that says "bet small and
often" is not an argument that there is something worth betting on.

---

## 5. Infrastructure: `d386_pass_rate.py` is reusable beyond the prop question

[`scripts/d386_pass_rate.py`](../../../scripts/d386_pass_rate.py) computes P(reach a target before
breaching a floor) under static, EOD-trailing and intraday-trailing conventions, with an optional
lock, a daily-loss rule, a minimum-days rule and a time limit — validated against gambler's ruin
(0.4016 ± 0.0025 vs 0.4000) and the reflection principle.

**Nothing in it is prop-specific.** Any personal-book question with a path constraint — "what is
P(this book draws down 20% before doubling)", "how much does a close-based check cost against a
continuous one", "what drawdown tolerance does a given Kelly fraction imply" — is the same machinery
with different arguments. Lane 08's closed forms plug straight into it:

- the drifted two-sided exit `P = (1−e^{2μb/σ²})/(e^{−2μa/σ²}−e^{2μb/σ²})`, which **inverts an
  observed survival rate into `θ = 2μ/σ²`** (only that ratio is identified);
- `(1−x)^{2/f−1}`, which prices a drawdown tolerance into a Kelly fraction — **a 4% floor needs
  about 1/9 Kelly** for an even chance of surviving.

That second one has an immediate consequence for the prop track worth recording here because it
corrects a live queue item: **[PICKUP](../../../PICKUP.md) §0d item 8 says extend C1's size sweep
below 0.48×. The closed form says the value peak is an ORDER OF MAGNITUDE below, not a factor of
two.**

---

## What did NOT carry, and why the list is short

- **No strategy.** Lanes 01–05 recovered contract terms. Lane 07 surveyed the claims tier and found
  its recurring claims either unfalsifiable or already falsified — including *"risk 0.5% per trade to
  pass"*, which is wrong **in sign** at zero edge. Nothing in it was a candidate to reject on prop
  grounds, so nothing was rejected on prop grounds.
- **Lane 06 carries nothing to either book.** Its findings are about the counterparty, not about
  returns.
- **The barrier itself does not transfer.** D379's whole apparatus — `E[payouts | survival] ×
  P(survival)`, the interior optimum, the risk-shifting prediction — is a property of an instrument
  the personal book does not hold. D379 says so; this file agrees.

**Status: nothing scored, nothing admitted, no cell run.** Items 1–3 are the ones worth a
pre-registration; 4 is an argument, not a study; 5 is a tool.
