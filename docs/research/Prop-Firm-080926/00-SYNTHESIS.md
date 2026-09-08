# 00 — SYNTHESIS: you cannot extract more in expectation than the amount they let you lose

**Nine lanes, 2026-09-08.** Schema and stopping rules committed **before** any searching
([`00-SCHEMA.md`](00-SCHEMA.md), `3e656c7`). Ledger and dead ends: [`SOURCES.md`](SOURCES.md).
Decision record: **[D386](../../decisions/D386-the-prop-account-is-worth-its-buffer.md)**.

**Nothing here is a result under [R15](../../RULES.md#r15).** No cell was scored, no strategy tested,
no avenue closed.

---

## VERDICT

The question the principal put is *is the payout large enough for the risk to be worth it*. It has a
closed-form answer, and the answer does not depend on any of the marketing.

> **At zero edge the expected lifetime extraction from a funded account equals the drawdown buffer,
> exactly.** Optional stopping: the balance is a martingale, total extracted plus final balance
> equals the start, and the final balance at ruin is the floor. So `E[extracted] = b`, **whatever the
> payout ladder says.**

**The payout ladder is decoration.** Verified at ratio 1.0000 against the renewal closed form and a
direct simulation. Apex's ladder — six rungs from $1,500 to $3,000 — realises $1,974 against a $2,000
buffer, so the entire six-rung structure is worth **−1.3%** relative to no ladder at all. The one
thing a ladder does is *cap* extraction when the buffer is large relative to the rungs.

So the ceiling on a funded account is the buffer, and the buffer is **the amount the firm permits you
to lose**. On a 50K account that is $2,000. **You cannot extract more in expectation than the amount
they let you lose** — and you only reach the payout regime at all with probability 0.37.

### The arithmetic, every term from a lane file, list prices

| | Apex 50K EOD | Apex 150K EOD | Topstep 50K XFA |
|---|---:|---:|---:|
| `E[extracted]` (= buffer, less the ladder cap) | $1,974 | $3,902 | $2,000 |
| × P(reach the lock) | **0.3743** | **0.3936** | **0.3911** |
| = `E[payout │ funded]` | **$739** | **$1,536** | **$782** |
| zero-edge P(pass) | 0.2495 | **0.1348** | 0.2664 |
| evaluation fee + activation | $550 + $139 | $1,890 + $159 | $49/mo + $149 |
| **V per evaluation, at list** | **−$400** | **−$1,706** | **+$120** |
| **break-even P(pass) at list** | **0.9167** | **1.3725** | 0.0774 |

**Two things fall straight out.**

**1. ~~Apex 150K at list price is negative at ANY edge.~~ WITHDRAWN — see
[D386 §2a](../../decisions/D386-the-prop-account-is-worth-its-buffer.md).** The break-even *pass
rate* is 1.3725, above one, and I read that as impossible. **It is not.** That quantity holds
`E[extracted]` at its zero-edge value, but **edge raises both terms** — you cannot lift `P(pass)`
without drift, and drift also makes each payout cycle survive more often. A break-even pass rate
above 1 means "unreachable by moving one term while pretending the other is fixed", not
"impossible".

**The right question is what edge is required**, with all three terms recomputed at that edge:

| break-even annual Sharpe | Apex 50K @ $250/day | Apex 150K @ $750/day | Topstep 50K @ $250/day |
|---|---:|---:|---:|
| at list price | **≈ 0.55** | **≈ 1.60** | below zero |
| at the ~90% discount | below zero | ≈ 0.01 | n/a |

**Also corrected:** Apex 150K's zero-edge `P(pass)` was entered as 0.2100 and never computed. Its
true value at a $9,000 target against a $4,005 drawdown is **0.1348**, which makes V per evaluation
**−$1,706**, not −$1,601. Every other pass rate in the table was computed and checks out.

**For scale:** a sustained annual Sharpe of 1.60 on a single futures account is not a number this
programme has ever produced. D378 put its entry-timing increment at 0.19–0.47× a round trip, and
both admitted arms of BOOK.md are not at capital.

**2. The discount is not a promotion, it is the price.** At the ~90% codes standing on Apex's own
pages, break-even falls to 0.0917 and 0.1373 against a zero-edge pass rate of 0.2495 and 0.2100 — so
the product goes from *impossible* to *positive with no skill whatsoever*. The list price exists to
make the discount look like a deal. **Caveat: the 90% figure is claims-tier observation, not a term.**

**Topstep looks best and the model flatters it.** Its $49 is **monthly**, not one-time, and the model
charges it once. At the ~58-day mean time-to-resolution the true acquisition cost is nearer $147,
which lifts break-even to about 0.23 against a zero-edge 0.2664 — still positive, but marginal rather
than comfortable.

**And all of the above is at ZERO edge, which flatters the real population.** Topstep's own published
per-Combine completion rate is **16.8%**, against a zero-edge baseline of **26.6–31.7%** at the true
geometry — **86 to 124 standard errors below a coin flip.** The marginal evaluation buyer has
*negative* edge, so every V above is an overstatement.

---

## The instrument, as the lanes actually found it

### The geometry table

| firm | evaluation floor | funded floor | locks? | payout cap |
|---|---|---|---|---|
| **Topstep** | EOD trailing | EOD trailing | **+$2,000** (of a $3,000 target) | flat $2,000, no ladder; **payout resets the MLL to $0 — it destroys the buffer** |
| **MyFundedFutures** | EOD trailing, every plan | **intraday** (Rapid) or EOD (Rapid EOD) | **+$2,100** | Rapid **uncapped**; Builder flat 5 rungs; Pro **$100k then profits forfeited** |
| **Apex** | EOD or intraday | same type, floor now locks at **+$100** | eval: at the target on Rithmic, **never on Tradovate** | rising 6-rung ladder, then **the account is closed** |
| **Take Profit Trader** | **EOD** trailing | **intraday** trailing | at `start + drawdown` | **uncapped** — "no maximum withdrawal amount" |
| **FTMO** (FX control) | 2-Step **static**; 1-Step EOD trailing | same | 2-Step n/a; **1-Step never locks** | **no ladder at all** |

**Five findings from that table.**

**Field 9 is a split basis everywhere, and it was found independently at three firms.** The floor
*rises* on the closed end-of-day balance but is *breached* on open intraday equity including
unrealised P&L. Modelling either as plain "EOD drawdown" understates the kill rate: an intraday spike
raises no floor, but an intraday dip still kills. This is D379's identification of hurdle P1 as a
continuously-monitored barrier, confirmed verbatim from the sources.

**The two largest futures firms sell the same instrument.** Topstep 50K and MFFU Rapid 50K agree to
within 0.3 points of zero-edge pass rate at every risk level. They differentiate on everything except
the geometry.

**A bigger account is a harder evaluation, and nobody markets it.** MFFU Rapid 100K passes 19.2% at
zero edge against the 50K's 26.3% — seven points. The target is a flat 6% of account size at every
tier while the drawdown *tightens*: 4% → 3% at MFFU, and independently 4.0/4.0/3.0/2.67% at Apex, so
the target-to-drawdown ratio rises 1.5 → 2.25. Two of the three largest firms price a flat percentage
target against a shrinking percentage barrier. **The direction is the opposite of what a buyer would
assume.**

**One firm sells a strictly dominated product at the same price as its alternative.** MFFU's Rapid and
Rapid EOD are identically priced and identical in the evaluation; they differ only in the funded
stage, where Rapid trails intraday. That term is worth **+0.0149 (9.5 SE)** of pass rate at 0.5% daily
risk, rising to **+0.0451 (27.4 SE)** at 2%. **Rapid EOD strictly dominates Rapid.**

**The FX control refuted its own premise, which is why it was kept.** FTMO has *three* geometries that
disagree inside one firm: 2-Step static, 1-Step EOD-trailing that **never locks**, and FTMO Futures
dollar-denominated EOD-trailing *with* a lock and a worked example. So "static is the FX convention,
trailing is a futures artefact" is false — geometry tracks the **product's** market convention, not
the firm. FTMO demonstrably knows how to write a lock clause, because it wrote one for futures and not
for the 1-Step CFD, which makes the 1-Step a **tighter** barrier than the US futures products, sold as
the easier one. It also carries a second absorbing band nobody markets: T&C 13.2.3(b) permits
termination of an account maintaining a loss between 8% and 10% for longer than thirty calendar days —
a **time-dependent absorbing region above the floor**.

### What the counterparty is

Three regulators independently describe one mechanism, in primary documents. **FSMA (Belgium):**
*"The consumer never makes any actual trades… The prop trading firm alone decides what simulated
transactions it will copy. This is how prop trading firms earn money from them."* **OSC (Ontario):**
"virtually no real trading", rules "designed to benefit TGG to the detriment of investors", each
account an **investment contract**. **CONSOB (Italy):** evaluations *"congegnati per spingere i
«giocatori» a ritentare"*. The OSC allegations were never adjudicated.

**The sharpest correction to D379's object: the barrier is administered by the counterparty.** D379
models it as exogenous geometry. It is a term the issuer sets, interprets and enforces — and at
**two of five firms the governing contract is not published at all** (MFFU's Simulated Trader
Agreement, which its own Terms §29 ranks *above* the Terms; FTMO's funded-phase T&C, "sample on
request"). The 2024 collapse cluster makes **issuer default a priced term, not a tail**.

**And 0.71% of Topstep Express Funded accounts ever reach live capital.** Over 99% of "funded"
accounts never touch real money. Topstep publishes this and it is almost never quoted.

---

## What this changes in our own records

| record | change |
|---|---|
| **[D379](../../decisions/D379-the-prop-account-is-a-down-and-out-call-and-hurdle-P-has-no-objective-function.md) §6 item 2** | **CLOSED.** The payout terms are recorded. §4 is computable, and computing it gives `E[payout] = b` |
| **D379 §4** | assumed a ladder. **Two of five firms have none**, and the ladder is worth −1.3% where it exists |
| **D379 §2** | models **one** barrier option. It is **two in sequence** — MFFU's funded account starts at **$0**, not the account size, so the funded phase is a second down-and-out with its barrier below zero, on terms that differ from the one bought |
| **D379 §5** | Hodder & Jackwerth (2007) splits it: risk-*reduction* near an **exogenous** barrier, risk-*increase* near an **endogenous** one, discriminated by continuation value — and **D379 A1's `fee ÷ P(pass)` IS that continuation value.** Neither section cites the other. Separately the canonical risk-shifting result (Brown–Harlow–Starks 1996) **did not replicate** (Busse 2001, an autocorrelation bias in a monthly vol estimator), so §5 must be argued from truncation, not the convex kink |
| **[PICKUP](../../../PICKUP.md) §0d item 8** | C1's sweep should extend **an order of magnitude** below 0.48×, not a factor of two: `(1−x)^(2/f−1)` says a 4% floor needs about **1/9 Kelly** for an even chance of surviving |
| **[BOOK_PROP](../../BOOK_PROP.md)** | unchanged. **No candidate reopened, no hurdle amended, nothing admitted** |

**Personal book:** [`09-personal-book-carry-forward.md`](09-personal-book-carry-forward.md). No
strategy surfaced and none was prop-rejected, so that list is empty of strategies and says so. Five
items carry, all sizing theory or modelling correction — the strongest being that **Grossman–Zhou is a
fifth challenger [D372](../../decisions/D372-equal-weight-is-the-incumbent-sizing-and-the-hurdle.md)
does not list**, and that **Broadie–Glasserman–Kou puts a number (0.5826 daily sigmas) on
[D381](../../decisions/D381-RESULT-a-stop-is-a-late-trigger-and-the-median-mean-exchange-rate-is-fixed.md)'s
"a stop is a late trigger"**.

---

---

# PART TWO — lanes 10–14, added 2026-09-08

The first nine lanes priced **the instrument**. These five ask whether anything can be **put in it**,
and what the conduct rules permit.

## The strategy search: zero families survive, and the reason is geometric

Two lanes searched independently — [13](13-documented-intraday-effects.md) the evidenced tier,
[14](14-practitioner-tier-screened.md) the practitioner tier — against a seven-point screen (CME
tradeable · directional not hedged · intraday-closable · MAE-bounded · produces $150+ days ·
survives ~$10/round turn · has a mechanism). **Both returned zero survivors and the same single
conditional near-miss.**

**The expected killer was wrong. Cost is the screen these effects pass most easily** — the
best-documented clears a $10–22.50 round turn by **3.8–8.6×**.

**What kills them is that two screens are the blades of a scissors.** Position size scales mean and
standard deviation together while the drawdown stays fixed at ~$2,000:

| | |
|---|---|
| the **$150+ qualifying-day rule** | sets a **lower** bound on contracts |
| the **4% trailing MLL on open equity** | sets an **upper** bound |
| **for every effect found** | **the lower bound EXCEEDS the upper bound — by 4.5× on ES** |

Closing it needs per-trade Sharpe **0.225** (annualised 3.57). Gao et al. document **0.068**
(annualised 1.08) — a **3.3× shortfall**. The best cell is one ES contract at ~8% survival to a
$3,000 target, and that is optimistic: Gaussian, close-only, ignoring kurtosis of 15.65.

**Lane 14's independent framing: the rule set is a vice, not a hurdle series.** The open-equity floor
kills **negative** skew by marking the worst point of an excursion before it resolves; the
consistency rule kills **positive** skew by capping the best day at 50% of total profit. What
survives in the middle is near-symmetric low-variance daily P&L — exactly what a fixed-dollar round
turn destroys. Its scale-free check: **P&L per unit of drawdown budget per day**, where the prop
account demands **0.075** and the verified short-term CTA tier delivers **0.00125** — a **19×–60×
gap**, falsifiable by any audited intraday CME programme with return ÷ maxDD ≥ 18.

**The near-miss, converged on from three directions:** market intraday momentum on ES/NQ, flat at the
cash close — Baltussen, Da, Lammers & Martens (*JFE* 142, 2021), 60+ futures 1974–2020, ES β = 6.18,
t = 4.97, **out-of-sample R² 2.29%**, 30-minute hold, gamma-hedging mechanism validated against an
option net-gamma measure. Two traps in how it is cited: the headline **Sharpe 1.73 is a 17-market 1/N
portfolio** a $50k account cannot hold (single-market ES ≈ 1.08), and **the authors explicitly
decline to cost it**. Lane 12 found D258 had already flagged this same literature as clearing futures
cost by an order of magnitude and never testing it.

### The blocking gap is structural, not a search failure

**Maximum adverse excursion within the holding window is not published for any candidate, anywhere** —
four targeted probes. Finance reports means, SDs and Sharpes because no academic objective is
path-dependent *inside* a trade. **The one quantity the funded account is priced on is the one
quantity the literature does not measure.** Every screen-4 verdict is therefore a σ-based lower bound
on severity, not a measurement.

**The cheapest thing that would change the answer: `P(MAE ≤ $2,000/contract)` for the
last-30-minute trade — one query against ~$8 of Databento `GLBX.MDP3`, inside the existing signup
credit.**

### A prior on decay, and an independent check on D379

Three documented corpses: the 2–3am overnight drift, once 3.7% p.a., **whose original FRBNY authors
published its death in July 2026** ("close to zero" since 2021; the ETFs built to harvest it closed
in 14 months); the pre-FOMC drift, gone after 2015; and **187 of 188 calendar anomalies** in index
futures (Carchano & Pardo).

And lane 13's survival probability came out **non-monotone in size** — 8.1% at N=1, 0.5% at N=2–3,
back to 7.8% at N=10 — reproducing D379 §2's interior optimum from an entirely separate calculation.

### The two books want opposite third moments

These strategies run **36–38% win rates at 2.1–2.25 payoff**. Low win rate × high payoff is precisely
the P&L shape a trailing drawdown kills, so **the prop instrument selects against positive skew — the
same tail the personal book's R15 objective is happy to buy.** The principal's standing instruction
of 2026-09-08, derived independently from the literature rather than from the rulebooks.

## Conduct: what the rules actually permit

**Apex's one-direction rule** ([lane 10](10-apex-conduct-rules.md)) is the binding constraint on
running more than one account. Every open position **and every resting order** you control must point
the same way in any correlated market — in that account, **your other accounts, and your
household's**. It names cross-account, correlated (*"you may not be short NQ while long ES"*),
cross-size (*"long Micro ES while short Mini ES"*), and *"opposite positions with other traders in
the same household."* **It reaches orders, so a two-sided bracket violates it before anything fills.**
Penalty: account closure. It binds evaluations and was the only one of Apex's four conduct rules to
survive the 4.0 reset. **Different strategies across your own accounts are explicitly encouraged;
only opposing sign is banned.** Cap: **20 active PAs per household.**

**Cross-firm** ([lane 11](11-cross-firm-policy.md)): four of five firms never mention a competitor.
**FTMO is the exception** and bans opposite positions *"between connected accounts, accounts held
with various operators/providers…"*. FTMO's clause and Topstep's §27 are the same boilerplate with
one variable slot — FTMO widened it, Topstep narrowed it to its own affiliates and **then published
the unnarrowed form** in the help centre carrying "final and cannot be appealed". **Same-direction
replication across firms is prohibited by nobody in writing**, and no firm requires disclosure of
funding elsewhere. So a multi-firm book is **un-prohibited and un-protected** — an unpriced
discretionary tail rather than a modellable constraint.

### Corrections to Part One

- **Topstep's hedging penalty is a graduated ladder, not a first-strike kill.** Rewritten
  2026-07-27: warning modal with cure window → same-day liquidation → forced typed acknowledgement →
  immediate liquidation → day-long violation → permanent closure only *"after numerous warnings"*.
  The unappealable language attaches to a **confirmed** violation. **Apex's one-direction closure has
  no such ladder.**
- **Topstep's ToU now reads "Last updated: September 8, 2026"** — newer than every source lane 02
  used. That lane may already be stale.
- **Apex is the third of five firms whose governing contract is unpublished** (its User Agreement
  *"shall prevail"*, 403 live and **zero Wayback captures**), joining MFFU's Simulated Trader
  Agreement and FTMO's Account T&C.
- **`SOURCES.md`'s Apex dead-end entry was wrong** and is corrected there.

## Prior art: what this programme has already closed

[Lane 12](../../decisions/D386-the-prop-account-is-worth-its-buffer.md) audited our own records.
**No study in this repo has ever read a CME futures price bar** — every prop result ran on ETF,
index-ETF or crypto proxies, so C1–C4 failed **on proxies**.

**Do not propose:** intraday mean reversion (C2, negative in all seven asset classes), opening-range
breakouts (C3, skew −0.51 to −0.80 — and lane 14 independently killed it on a placebo-controlled
replication), index spreads (D261, category closed), overnight gaps as a short trigger (D250),
volume-at-price levels (D189/D194/D196), weekly COT sorts (D263), or **anything single-name** — no
futures contract exists on the names our equity books trade, so that lineage is out permanently.

**Three things worth more than the exclusion list:**

1. **D163's cost wall is stale by ~400×.** It killed the 15-minute breakout at *"~315% of capital a
   year in fees"* — a **crypto taker fee of 40 bp/side**. At ES cost (~0.1 bp/side) the same 786×
   turnover costs **~0.8%/yr**. R11 carries a standing corollary requiring re-costing, undischarged.
2. **The prop track has been screening at a third of the available breadth** — a diversified futures
   complex is **3.00** effective against **1.17** for four equity indices, worth **1.6× on IR**. C1
   and C2 were both screened at 1.17.
3. **D383 is designed, pre-registered and unrun** — 600 cells at 15 minutes, reserved window
   untouched. The only intraday directional screen this programme has built and not executed.

---

---

# PART THREE — the strategy sweep, lanes 15–19

Eight lanes were sent at the strategy question across Reddit, quant forums, open source, practitioner
research, and non-English communities. **Five have landed. The prop verdict did not change; the
useful output is a set of tools and one shape constraint.**

## The tool that makes every claim comparable

**Per-trade Sharpe is recoverable from any published t-statistic as `t/√N`.** That makes lane 13's
threshold of **0.225** applicable to every claim in the review, not just those reporting per-trade
moments:

| candidate | per-trade Sharpe | vs 0.225 |
|---|---:|---|
| Gao et al. intraday momentum — lane 13's best | 0.068 | **0.30× — fails** |
| **C19-2, last 15 min, CSI 300** (t = 10.1, N ≈ 945) | **0.329** | **1.46× — clears** |

## The shape constraint — the first actionable one in the review

**C19-2 clears structurally, not by having a bigger edge.** A 15-minute window carries ~18 bp of
standard deviation, so **one ES contract makes a $150 day and the fixed $2,000 floor sits 3.4σ away.**

> **The scissors close on LONG WINDOWS, not on small edges.**

Every prop rejection so far has been a *size* rejection driven by a short holding window forcing
contract count up against a fixed floor. **Widening the window relaxes the lower bound without
touching the upper one.** That is the first structural guidance the review has produced on what
*shape* of effect can pass hurdle P.

*Largest threat, stated: C19-2 is measured on the INDEX, not the future. Stale-price and
closing-auction contamination is the falsifier to run first.*

## The finding that bears on our own C1

**China runs the natural experiment the US cannot.** Haitong measures the overnight return on **T+1
cash** and **T+0 futures** — same underlying, same days, 2016-01-11 → 2019-11-29 — and gets
**opposite signs, both significant**: index **−0.073% (t = −4.03)**, IF future **+0.055% (t = +3.19)**.
The Chinese literature names the mechanism with an A/H same-company design behind it.

**Claim: the overnight drift is a property of the SETTLEMENT RULE, not of the passage of time.**

C1 — this programme's session-boundary hold — was an overnight *futures* hold measured on *equity*
extended-hours bars. **If the drift is a T+1 settlement artefact it does not exist in a T+0 future at
all, and C1's premise was never the thing its proxy measured.** Falsifier computable on any fixture
holding both SPX and ES.

## The calibration specimen worth more than most candidates

**C19-4: a clock-effect replication at 0.781 basis points per half-hour leg, with t = 62.71.** The
cleanest specimen in the review of *statistically overwhelming and economically dead*. Keep it as a
size calibration — **anything in that family reporting more than ~2 bp should be reconciled against
it before being believed.**

## What the sweep says about the sources themselves

- **The one prop candidate that survived lanes 13/14 was dismantled by lane 16** — three independent
  reimplementations returning Sharpe 0.399 against a published 1.33, **with the paper's author
  answering in writing**, and the entire gap isolated to the bid/ask spread.
- **Cost was never the binding constraint** (lane 17): every prop rejection is a *size* rejection;
  cost is 15–20% of the gross mean.
- **Drawdown is 17× more persistent out-of-sample than Sharpe** (Quantopian's 888 algorithms:
  R² = 0.02 for Sharpe, 0.34 for max drawdown). **The statistics the barrier reads are the ones that
  survive.**
- **Year-instability, not cost, is the modal failure**, and our screens carry no per-year
  sign-stability gate.
- **The regional-fashion premise was half right** (lane 19): the Russian, Japanese, German, French and
  Nordic *retail* layers publish the same effects with *worse* disclosure than the English claims
  tier. Only the Chinese **sell-side research and academic** tier is a genuinely different literature,
  and it did not saturate.

## And the ledger lesson, which was learned twice

**Two recorded "this host blocks us" entries turned out to be USER-AGENT exclusions rather than
blocks** — Apex returned HTTP 200 on 28 of 28 pages to a browser-headered `curl`, and Reddit is
reachable by RSS. In both cases the wrong entry sent a later lane down a route that could not reach
the material. The rule is recorded in [`SOURCES.md`](SOURCES.md): **a logged block must name the tool
and the headers that failed, never just the host.**

---

## The honest bounds

- **`E[extracted] = b` assumes zero edge and a static floor after the lock.** With positive edge it
  rises; the drifted two-sided exit gives the correction and is in
  [`d386_account_value.py`](../../../scripts/d386_account_value.py).
- **The pre-lock climb is modelled, but the funded phase's other rules are not** — consistency rules,
  minimum-profit days, inactivity closure and scaling limits all bind and all reduce `E[extracted]`.
  **Every number here is an upper bound.**
- **Apex's cells are Internet Archive snapshots** (2026-03-25 → 2026-08-17) because the site 403s all
  automated fetch. The content is Apex's verbatim; the currency is the snapshot.
- **The 90% discount is claims-tier**, observed on-page, not a published term.
- **The iid-normal assumption understates ruin**, as D379 already says: real P&L is fat-tailed and
  autocorrelated, and volatility clustering is measured at **2.01×** in
  [youtube-lessons §5](../../youtube-lessons.md).
- **Research allocates an edge, it does not supply one.** C1–C4 is exhausted. This work makes the
  instrument computable; it does not produce something to put in it.
