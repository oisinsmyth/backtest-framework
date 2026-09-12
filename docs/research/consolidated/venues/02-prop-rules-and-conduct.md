# Prop rules and conduct — what the terms actually permit

[← venues index](00-index.md) · prev: [prop account arithmetic](01-prop-account-arithmetic.md)

**Read [the arithmetic](01-prop-account-arithmetic.md) first.** The rules below only matter if the
instrument is worth entering at all, and the arithmetic says it is worth its buffer.

**All of this is `[EXT]`, from primary terms documents. None is legal advice and none was verified
here.**

---

## The one-direction rule is the binding constraint on multiple accounts

**Apex's rule** ([lane 10](../../Prop-Firm-080926/10-apex-conduct-rules.md)):

> **Every open position AND EVERY RESTING ORDER you control must point the same way in any correlated
> market** — in that account, **your other accounts, and your household's.**

It names it explicitly: **cross-account**, **correlated** (*"you may not be short NQ while long ES"*),
**cross-size** (*"long Micro ES while short Mini ES"*), and *"opposite positions with other traders in
the same household."*

| | |
|---|---|
| **it reaches ORDERS** | **a two-sided bracket violates it before anything fills** |
| penalty | **account closure** |
| scope | **binds evaluations too**, and was the only one of Apex's four conduct rules to survive the 4.0 reset |
| cap | **20 active PAs per household** |
| explicitly allowed | **different strategies across your own accounts. Only opposing SIGN is banned** |

> **This kills spread, curve and calendar strategies on a RULE, not on a return** — recorded that way
> in the candidate ledger.

## Cross-firm policy

**Four of five firms never mention a competitor**
([lane 11](../../Prop-Firm-080926/11-cross-firm-policy.md)). The exception, and the full clause-level
comparison, is in that lane.

## The firm grid

| lane | firm |
|---|---|
| [01](../../Prop-Firm-080926/01-myfundedfutures.md) | MyFundedFutures |
| [02](../../Prop-Firm-080926/02-topstep.md) | Topstep |
| [03](../../Prop-Firm-080926/03-apex.md) · [10](../../Prop-Firm-080926/10-apex-conduct-rules.md) | Apex, and its conduct rules |
| [04](../../Prop-Firm-080926/04-take-profit-trader.md) | Take Profit Trader |
| [05](../../Prop-Firm-080926/05-ftmo-fx-control.md) | **FTMO — the FX/CFD geometry control.** A different instrument, kept as a control on the geometry |

**The geometry table** — evaluation floor, funded floor, whether it locks, and the payout cap — is in
[`00-SYNTHESIS.md`](../../Prop-Firm-080926/00-SYNTHESIS.md) §"The instrument, as the lanes actually
found it".

## Counterparty risk, and the claims tier

| lane | what it holds |
|---|---|
| [06](../../Prop-Firm-080926/06-regulatory-and-litigation.md) | **regulatory and litigation** |
| [22](../../Prop-Firm-080926/22-filings-and-enforcement.md) | **compelled disclosure** — enforcement actions, exchange rules, securities filings. *The only tier where a firm has to say something true* |
| [07](../../Prop-Firm-080926/07-statistics-and-claims.md) | **published statistics and the claims tier** — treat as marketing until a filing corroborates it |
| [20](../../Prop-Firm-080926/20-verified-track-records.md) | **the audited tier**, and what it actually delivers |

**The one number that survives the marketing:** Topstep's own published per-Combine completion rate of
**16.8%**, against a zero-edge baseline of 26.6–31.7% — **86 to 124 standard errors below a coin
flip.**

## The `$25,000` pattern-day-trader rule was struck on 2026-06-04

`[EXT]`, from [`the-plumbing-round.md` §1.9](../../the-plumbing-round.md). **Not verified here.** It
changes what a small *equities* account may do intraday, which is a separate question from the futures
prop instrument — **recorded here because it is the only other venue-rule finding in the tree.**

## What decay looks like in this space `[EXT]`

**Three documented corpses**, worth carrying as a prior on any futures calendar effect:

1. **The 2–3 am overnight drift**, once 3.7% p.a. — **its original FRBNY authors published its death
   in July 2026** (*"close to zero"* since 2021), **and the ETFs built to harvest it closed in 14
   months.**
2. **The pre-FOMC drift** — gone after 2015.
3. **187 of 188 calendar anomalies** in index futures.

## The method lessons this campaign produced

[`23-method-lessons.md`](../../Prop-Firm-080926/23-method-lessons.md) — *"what transfers, regardless of
whether anyone ever trades a prop account"*. Two that generalise:

- **A logged block must name the tool and the headers that failed, never just the host.** Apex
  returned **HTTP 200 on 28 of 28 pages** to a browser-headered `curl`; Reddit is reachable by RSS.
  **In both cases the wrong ledger entry sent a later lane down a route that could not reach the
  material.** → [tooling hazards](../method/04-tooling-hazards.md)
- **When a family is closed, close it with the arithmetic** (§3b), not with a summary.

---

**Sources.** [`Prop-Firm-080926/`](../../Prop-Firm-080926/) — the firm grid, conduct, regulatory and
claims lanes · [`SOURCES.md`](../../Prop-Firm-080926/SOURCES.md) — the anti-redundancy source ledger ·
[`00-SCHEMA.md`](../../Prop-Firm-080926/00-SCHEMA.md) — the stopping rules, declared **before** any
search.
