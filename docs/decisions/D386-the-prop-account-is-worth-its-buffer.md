# D386 — a funded prop account is worth its drawdown buffer, and the payout ladder is decoration

**Status:** REVIEW. **Nothing here is a result under [R15](../RULES.md#r15).** No cell was scored, no
strategy tested, no avenue closed, **no looks added to any multiplicity ledger** — the category
[D374](D374-is-the-breadth-hurdle-reachable.md) and
[D375](D375-the-hurdle-audit-the-stage-one-gates-are-sound-and-hurdle-P-is-half-untested.md)
established.
**Date:** 2026-09-08
**Area:** the instrument · **prop track**

**No holdout testing. Holdout reads spent: 0. Programme total: 1.**

**Schema and stopping rules committed BEFORE any searching** (`3e656c7`), so the grid could not
shrink to whatever turned out to be findable. Research: [`docs/research/Prop-Firm-080926/`](../research/Prop-Firm-080926/00-SYNTHESIS.md),
nine lanes, 120 cells, all filled or explicitly `NOT PUBLISHED` with what was tried. Ledger and dead
ends: [`SOURCES.md`](../research/Prop-Firm-080926/SOURCES.md).

---

## 0. The question, and it is the principal's

[D379](D379-the-prop-account-is-a-down-and-out-call-and-hurdle-P-has-no-objective-function.md) named
the objective — `V = N × [P(pass) × E[payout|funded] − fee]` — and could not evaluate it. Its §6 says
why, in writing:

> **Record the payout ladder terms** for MyFundedFutures. §4 is not computable without them, and no
> record here holds them.

The principal put the question that makes those terms matter: *every prop account eventually hits the
firm's constraints; what decides it is whether the payout is large enough for the risk to be worth
it.* This record answers that.

## 1. The answer is a closed form, and it does not depend on the marketing

**At zero edge the expected lifetime extraction from a funded account is the drawdown buffer,
exactly.**

Optional stopping. After the floor locks it is static, and at zero edge the balance is a martingale,
so `E[total P&L] = 0` over the account's life. Total extracted plus final balance equals the start,
and the final balance at ruin is the floor, `start − b`. Therefore

> **`E[extracted] = b`, whatever the payout ladder says.**

**So the payout ladder is decoration.** Verified at ratio **1.0000** against the renewal closed form
and against direct simulation ([MC] in
[`scripts/d386_account_value.py`](../../scripts/d386_account_value.py)). Apex's six-rung ladder
realises **$1,974 against a $2,000 buffer** — the whole structure is worth **−1.3%** relative to
having none. The only thing a ladder does is *cap* extraction when the buffer is large relative to
the rungs.

**The buffer is the amount the firm permits you to lose.** So the finding states plainly as: **you
cannot extract more in expectation than the amount they let you lose** — and you reach the payout
regime at all with probability **0.37**.

## 2. The arithmetic, every term from a lane file

List prices, 2026-09-08, zero edge. `E[payout|funded] = b × P(reach the lock)`.

| | Apex 50K EOD | Apex 150K EOD | Topstep 50K XFA |
|---|---:|---:|---:|
| `E[extracted]` | $1,974 | $3,902 | $2,000 |
| × P(reach the lock) | 0.3743 | 0.3936 | 0.3911 |
| **`E[payout │ funded]`** | **$739** | **$1,536** | **$782** |
| zero-edge P(pass) | 0.2495 | **0.1348** | 0.2664 |
| fees (eval + activation) | $550 + $139 | $1,890 + $159 | $49/mo + $149 |
| **V per evaluation** | **−$400** | **−$1,706** | **+$120** |
| **break-even P(pass)** | **0.9167** | **1.3725** | 0.0774 |

> **⚠ TWO NUMBERS IN THIS TABLE ARE WRONG AND ONE CONCLUSION DRAWN FROM IT IS FALSE.
> See [§2a](#2a-correction-2026-09-08-the-break-even-pass-rate-was-the-wrong-question).** Apex 150K's
> zero-edge P(pass) is **0.1348**, not 0.2100, and its V per evaluation is **−$1,706**, not −$1,601.
> The claim below that it is "negative at any edge" is **WITHDRAWN**. The rest of the table stands.

**~~Apex 150K at list price is negative at ANY edge.~~ WITHDRAWN — see §2a.** Break-even *pass rate*
is 1.3725, above one, and I read that as impossible. It is not: the break-even pass rate holds
`E[extracted]` at its zero-edge value, and **edge raises both terms.** The account needs an annual
Sharpe of about **1.60**, which is demanding but finite.

**The discount is not a promotion, it is the price.** At the ~90% codes standing on Apex's own pages,
break-even falls to 0.0917 and 0.1373 against zero-edge pass rates of 0.2495 and 0.2100 — from
*impossible* to *positive with no skill at all*. The list price exists to make the discount look like
a deal. *(The 90% is claims-tier observation, not a published term.)*

**Topstep looks best and the model flatters it:** its $49 is **monthly** and is charged once here. At
the ~58-day mean resolution the true cost is nearer $147, lifting break-even to ~0.23 against a
zero-edge 0.2664 — positive, but marginal.

**And zero edge flatters the real population.** Topstep's own 2025 disclosure puts per-Combine
completion at **16.8%** against a zero-edge **26.6–31.7%** at the true geometry — **86 to 124 standard
errors below a coin flip.** The marginal buyer has negative edge, so every V above is an
overstatement.

## 2a. CORRECTION, 2026-09-08 — the break-even pass rate was the wrong question

**Appended the same day, after computing the required edge. Nothing above this heading was edited
except the withdrawal marks.**

### The error of substance

§2 reported a **break-even P(pass)** per account and read Apex 150K's value of 1.3725 as meaning the
account is "negative at any edge". **That is false, and the mistake is structural rather than
arithmetic.**

`breakeven_pass_rate()` solves `fee = P × (E[extracted] − activation)` for `P` **while holding
`E[extracted]` at its zero-edge value.** But you cannot raise `P(pass)` without drift, and drift
raises `E[extracted]` too — each payout cycle survives more often. So the quantity being solved for
describes a state of the world that cannot occur: a trader with a high pass rate and no edge in the
funded account. **A break-even pass rate above 1 does not mean "impossible"; it means "unreachable by
moving one term while pretending the other is fixed".**

**The right question is what EDGE is required**, with all three terms — `P(pass)`, `P(reach the
lock)` and `E[extracted]` — recomputed at that edge. Edge is stated as an annual Sharpe on the
account's own P&L, and **it is conditional on the risk level**, because the barrier is a fixed dollar
amount while Sharpe is dimensionless.

### The required edge, at the risk levels stated

| Sharpe | Apex 50K @ $250/day | Apex 150K @ $750/day | Topstep 50K @ $250/day |
|---:|---:|---:|---:|
| 0.0 | −$400 | −$1,706 | +$120 |
| 0.5 | −$78 | −$1,462 | +$511 |
| 1.0 | +$656 | −$1,001 | +$1,470 |
| 1.5 | +$1,937 | −$227 | +$3,358 |
| 2.0 | +$3,680 | +$953 | +$6,302 |
| **break-even Sharpe, LIST** | **≈ 0.55** | **≈ 1.60** | **below zero** |
| **break-even Sharpe, discounted** | below zero | **≈ 0.01** | n/a |

### The error of fact

**Apex 150K's zero-edge `P(pass)` was entered as 0.2100 and never computed.** The correct value for
its actual geometry — a flat 6% target of $9,000 against a 2.67% drawdown of $4,005 — is **0.1348**.
That is the failure this programme's own memory names: *my runner asserts encode data expectations*.
Every other pass rate in §2 was computed and checks out (Apex 50K 0.2495 vs 0.2497; Topstep 0.2664 vs
0.2668).

Corrected: Apex 150K zero-edge `P(pass)` **0.1348**, V per evaluation at list **−$1,706**, cost per
funded account **$14,180**.

### What survives unchanged

- **`E[extracted] = b` at zero edge.** Untouched — it is a martingale identity and no sweep bears on
  it. But it is a **zero-edge** statement, and this record's title should be read as such: at Sharpe
  1.0 Apex 50K's `E[extracted]` is **$4,640** against a $2,000 buffer. **The account is worth its
  buffer to a trader with no edge, and more to one with an edge.**
- **The payout ladder is decoration** — also a zero-edge statement, on the same footing.
- **The discount is the price.** Strengthened, if anything: at list the two Apex products need a
  sustained annual Sharpe of 0.55 and 1.60; at the ~90% codes they need none.
- **The direction of every comparison.** The bigger account is still the harder one; Topstep is still
  the best of the three; the observed 16.8% is still far below the zero-edge baseline.

**And the scale that matters:** an annual Sharpe of 1.60 sustained on a single futures account is not
a number this programme has ever produced. [D378](D378-RESULT-the-entry-day-does-matter-and-it-survives-losing-its-best-trade.md)
put its entry-timing increment at **0.19–0.47× a round trip**, and both admitted arms of
[BOOK.md](../BOOK.md) are not at capital.

---

## 3. What it changes in D379

| | |
|---|---|
| **§6 item 2** | **CLOSED.** The terms are recorded; §4 is computable and computing it gives `E[payout] = b` |
| **§4** | assumed a ladder. **Two of five firms have none** (Take Profit Trader, FTMO), and where one exists it is worth −1.3% |
| **§2** | models **one** barrier option. It is **two in sequence**: MFFU's funded account starts at **$0**, not the account size, so the funded phase is a second down-and-out with its barrier below zero, on terms differing from the one bought |
| **§5** | Hodder & Jackwerth (2007) splits it — risk-*reduction* near an **exogenous** barrier, risk-*increase* near an **endogenous** one, discriminated by continuation value — and **D379 A1's `fee ÷ P(pass)` IS that continuation value.** Neither section cites the other. The canonical risk-shifting result (Brown–Harlow–Starks 1996) **did not replicate** (Busse 2001: an autocorrelation bias in a monthly volatility estimator), so §5 must be argued from **truncation**, not from the convex kink |
| **the object itself** | **the barrier is administered by the counterparty**, not exogenous geometry — and at two of five firms the governing contract is **not published at all** |

## 4. The instrument, and five things the lanes established about it

1. **Field 9 is a split basis, found independently at three firms.** The floor *rises* on the closed
   end-of-day balance and is *breached* on open intraday equity. Modelling either as "EOD drawdown"
   understates the kill rate. This is D379's identification of hurdle P1, confirmed verbatim.
2. **The two largest futures firms sell the same instrument** — Topstep 50K and MFFU Rapid 50K agree
   within 0.3 points of zero-edge pass rate at every risk level.
3. **A bigger account is a harder evaluation, and nobody markets it.** Target is a flat 6% at every
   tier while drawdown tightens — 4%→3% at MFFU, 4.0/4.0/3.0/2.67% at Apex — so the target/drawdown
   ratio rises 1.5 → 2.25 and MFFU Rapid 100K passes **19.2%** against the 50K's **26.3%**.
4. **MFFU sells a strictly dominated product at the same price as its alternative.** Rapid and Rapid
   EOD differ only in the funded stage; the intraday term costs **0.0149 (9.5 SE)** of pass rate at
   0.5% daily risk rising to **0.0451 (27.4 SE)** at 2%. **Rapid EOD dominates Rapid.**
5. **The FX control refuted its own premise, which is why it was kept.** FTMO runs three geometries
   that disagree inside one firm — 2-Step static, 1-Step EOD-trailing that **never locks**, FTMO
   Futures EOD-trailing *with* a lock. Geometry tracks the **product's** convention, not the firm,
   and the never-locking 1-Step is a **tighter** barrier than the US futures products, sold as the
   easier one.

## 5. The runners, and the assertion that caught me

Two committed: [`d386_pass_rate.py`](../../scripts/d386_pass_rate.py) (`d157f70`) and
[`d386_account_value.py`](../../scripts/d386_account_value.py). Eight and six assertions
respectively, each including one that must be **able** to fail.

**Three assertions fired on the first run of the pass-rate runner and the simulator was right every
time.** All three encoded the expectation that a 252-day horizon approximates an infinite one. It does
not: absorption for +3,000/−2,000 at $250/day is `a·b/σ² = 96` days, so 6.2% of paths were unresolved
and counted as neither pass nor breach — biasing the rate down, and **more at low vol**, which is what
the scale-invariance check caught. Rewritten to the invariants underneath rather than to the
parameter choice. The same defect then survived into the first published Stage 0 table, which carried
a $100/day row reading **0.2614 for a static floor whose true value is 0.4000**; the row is withdrawn
and every cell now reports and asserts its own timeout.

**Lane 08's horizon warning was tested rather than accepted.** It held that a non-locking trailing
floor is breached with probability 1, so every trailing rate is horizon-dependent. That is true of the
**drawdown process alone** and false of the **race**: an evaluation resolves in finite time almost
surely, so `P(pass)` has a positive limit. Tripling the horizon moved every row by less than 4 SE with
timeout 0.00000 at both. **The published cells are the limits.** Where the warning does bite is
FTMO's 1-Step, which never locks *and* has an unlimited trading period.

## 6. What does not change

- **[BOOK_PROP.md](../BOOK_PROP.md) is unchanged. No candidate reopened, no hurdle amended, nothing
  admitted.** C1–C4 remain exhausted.
- **No avenue is closed.** Only the principal does that.
- **Hurdle P stands as written.** P3, P4 and P5 remain uncomputed and under [R6](../RULES.md#r6) that
  is still a live defect.
- **Nothing transfers to the personal book except sizing theory** —
  [`09-personal-book-carry-forward.md`](../research/Prop-Firm-080926/09-personal-book-carry-forward.md),
  written under the principal's standing instruction that a prop-ineligible candidate is still worth
  keeping. **No strategy surfaced and none was prop-rejected**, so that list is empty of strategies
  and says so.

## 7. Owed next, each needing a pre-registration ([R8](../RULES.md#r8))

1. **Extend C1's size sweep an order of magnitude below 0.48×**, not a factor of two — `(1−x)^(2/f−1)`
   puts an even chance of surviving a 4% floor at about **1/9 Kelly**. Corrects PICKUP §0d item 8.
2. **Look-ahead audit of C1's volatility estimator** before that sweep. The vol-managed literature's
   headline result was a look-ahead artefact in exactly such an estimator (Liu–Tang–Zhou), and C1's
   evidence is a vol-target sweep ([D260](D260-the-vol-targeted-overnight-hold.md)).
3. **Declare an abandonment convention.** Topstep's denominator is Combines *initiated* and
   abandonment is undisclosed, while the simulation runs every path to absorption.
4. **Settle whether MFFU's Rapid floor lock is automatic or purchased** — its own pages contradict
   each other, and it is a live fork for the valuation.

## 8. The honest bound

`E[extracted] = b` assumes zero edge and a static floor after the lock. The pre-lock climb is
modelled; consistency rules, minimum-profit days, inactivity closure and scaling limits are **not**,
and all of them reduce `E[extracted]`. **Every number here is an upper bound.** The iid-normal frame
understates ruin, as D379 already says and as volatility clustering — measured at **2.01×** in
[youtube-lessons §5](../youtube-lessons.md) — confirms.

**And D379's own bound stands: this is a valuation framework, not an edge.** It makes the instrument
computable. It does not produce anything to put in it.

---

## Artifacts

Nine lane files and the ledger under [`docs/research/Prop-Firm-080926/`](../research/Prop-Firm-080926/00-SYNTHESIS.md).
Runners `scripts/d386_pass_rate.py` and `scripts/d386_account_value.py`, both with `--selftest`.
Evidence [`data/ftmo_challenge_terms_2026-08-04.txt`](../../data/ftmo_challenge_terms_2026-08-04.txt),
retained because lane 05 quotes it and its CDN URL is a content hash. **Apex's cells are Internet
Archive snapshots** (2026-03-25 → 2026-08-17) because the site 403s all automated fetch — the content
is Apex's verbatim, the currency is the snapshot.
