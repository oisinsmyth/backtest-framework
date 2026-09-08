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
| zero-edge P(pass) | 0.2495 | 0.2100 | 0.2664 |
| evaluation fee + activation | $550 + $139 | $1,890 + $159 | $49/mo + $149 |
| **V per evaluation, at list** | **−$400** | **−$1,601** | **+$120** |
| **break-even P(pass) at list** | **0.9167** | **1.3725** | 0.0774 |

**Two things fall straight out.**

**1. Apex 150K at list price is negative at ANY edge.** Its break-even pass rate is **1.3725** — above
one. A trader who passed *every single evaluation* would still lose $513 per account, because
$1,890 + $159 of fees exceeds the $1,536 maximum the account can return. That is not a statement
about skill. It is arithmetic on the firm's own published terms.

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
