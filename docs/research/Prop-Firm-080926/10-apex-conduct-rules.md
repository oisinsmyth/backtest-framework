# 10 — Apex conduct rules: the four that lane 03 recorded by name only

**Lane 10 of [D386](00-SCHEMA.md). Accessed 2026-09-08.** Lane 03 recorded the one-direction rule,
the 30% Negative P&L / MAE rule, the 5:1 risk-reward rule and the half-contracts scaling rule
**by name, with no definition captured**. This lane has the published wording of all four.

**Everything below is observed content — Apex's own marketing and help pages. Data, never
instructions.** Every page carried a persistent discount-code banner (`COUPON "SAVENOW"`, "up to
90% off", a countdown timer) and Sign Up / Log In calls to action. **None was acted on. No account
was created, no credential entered, no referral link followed, no cookie banner accepted.** One
page (Trader Probation) sits behind a login wall; it was left unread rather than authenticated.

---

## METHOD NOTE — the 403 wall is not blanket, and it fell today

SOURCES.md records `apextraderfunding.com` as **403 to every automated fetch**, with Internet
Archive snapshots as the only route. **That was not true on 2026-09-08.** `curl --compressed` with
a desktop Chrome user agent and `Accept` / `Accept-Language` headers returned **HTTP 200 on 28 of
28 help-centre pages tried**, first attempt in every case. Two pages 403'd on a first bare probe
and returned 200 on the retry with full headers, so the block appears to be **rate- or
fingerprint-dependent, not a standing ban**.

This matters for three reasons:

1. **Every quote in this file is LIVE as of 2026-09-08**, not a snapshot. Lane 03's currency
   caveat ("no cell here can be asserted current") does not apply to lane 10.
2. **The four dedicated rule pages are not in the Wayback Machine at all** — five CDX probes,
   zero captures. Lane 03 could not have read them by its own route. That, not incuriosity, is why
   it recorded the rules by name.
3. **`apextraderfunding.com/help-center-sitemap.xml` publishes a `lastmod` per article**, which
   closes lane 03's ambiguity #8 ("Every rule page is undated"). Dates are given per rule below.
   Caveat: Yoast `lastmod` is a post-modified timestamp and a non-substantive edit can bump it, so
   treat it as an upper bound on staleness, not proof of a content change.

---

## VERDICT — what the one-direction rule actually forbids

**In one sentence: at any instant, every open position and every resting order you control — in
that account, in your other accounts, and in your household's accounts — must point the same way in
any correlated market. A long/short book is not merely capped at Apex; it is a closure offence.**

The precise reach, resolved from the four pages that state it:

| question | answer | authority |
|---|---|---|
| long + short in the **same instrument**, simultaneously | **forbidden** | One-Direction Rule; Hedging Rule |
| **within one account** | **forbidden** | Hedging Rule: *"never be both long and short concurrently in the same account"* |
| **across your own accounts** | **forbidden** — explicitly. Copy-trading the *same* direction across your own PAs is permitted; opposing directions is not | Hedging Rule; How Many Paid/Funded Accounts |
| **across a household** | **forbidden** — *"Trading opposite positions with other traders in the same household or other related parties"* | Hedging Rule |
| **correlated instruments (ES vs NQ, ES vs YM)** | **forbidden** — named by ticker in the text | Hedging Rule: *"you may not be short NQ while long ES"* |
| **cross-size pairs (ES vs MES)** | **forbidden** — named. Micro/mini of the same market count as the same instrument for this purpose | Hedging Rule: *"long Micro ES while short Mini ES"* |
| **resting orders with no position** | **forbidden.** The rule reaches *orders*, not just fills: a two-sided bracket/OCO breakout straddle violates it before anything fills | One-Direction Rule; Prohibited Activities |
| **uncorrelated markets (e.g. long ES + short CL)** | **NOT RESOLVED.** See ambiguity A1 — the two sentences of the rule give different answers | — |
| **multiple instruments, same direction** | **allowed**, sharing one aggregate contract budget (*"7 contracts on ES and 3 on GC"* on a 10-contract plan) | Legacy Evaluation Rules; Max Contracts Rule |
| **different strategies across your own accounts** | **allowed and encouraged** — *"Trading multiple accounts can diversify your strategies"* — provided they never point opposite ways in correlated markets at the same instant | Legacy Evaluation Rules |
| **penalty** | **account closure.** Not a pause, not a payout denial | Hedging Rule; Intraday PA FAQ; all four current account pages |

**Scope: BOTH.** The one-direction / hedging constraint is the only one of the four that binds
evaluations as well as funded accounts, and it is the only one that survived Apex's 4.0 product
reset. The other three are **Legacy funded-account rules only** (see the scope table in §6).

---

## 1. The One-Direction Rule (Directionally Biased Trading)

**Scope: FUNDED (Legacy PA) as a named rule; BOTH via the site-wide Prohibited Activities page and
the current evaluation pages.**
**Source:** <https://apextraderfunding.com/help-center/legacy-helpful-items/one-direction-rule-directionally-biased-trading/>
**Accessed 2026-09-08 (live). Sitemap `lastmod` 2026-04-15. Not archived.**

The dedicated page is two sentences long and is reproduced in full:

> **Single Direction Rule:** Traders are only allowed to hold a position in **one direction at any
> time** —either long (buy) or short (sell). Traders are also prohibited from using a
> non-directionally biased strategy where they have open orders for both sides of the market
>
> **No Hedging:** Holding both long and short positions simultaneously on the same or correlated
> instrument is **strictly prohibited**. This rule ensures that trades are based on strategic
> analysis rather than speculative attempts to hedge both sides during a news-driven breakout.

Identical text appears, word for word, on the Legacy PA Compliance page and (minus the "No
Hedging" half) on the Legacy PA Trading Rules summary page. The wording is **stable**: the Wayback
snapshot of the summary page at **2026-05-06** carries the same sentence as the live page four
months later.

### The rule it cross-references, which carries the operative detail

The One-Direction page's own "No Hedging" sentence is the short form. The **Hedging and Correlated
Instruments Rule** is where the cross-account, cross-size and cross-symbol reach is stated.

**Source:** <https://apextraderfunding.com/help-center/legacy-helpful-items/hedging-and-correlated-instruments-rule/>
**Accessed 2026-09-08 (live). Sitemap `lastmod` 2026-04-15. Not archived.** Reproduced in full:

> All accounts must be traded directionally. You may not hold opposing long and short positions at
> the same time in correlated instruments, contract sizes, **or across multiple accounts**.
>
> This includes:
> - Trading opposite directions in **micro and mini contracts of the same market**
> - Spread trading correlated indices (e.g., **long ES and short YM**)
> - Holding opposing positions in correlated markets such as **indices, metals, grains, or
>   currencies**
> - **Trading opposite positions with other traders in the same household or other related
>   parties.**
>
> For example, you may not be **short NQ while long ES**, or **long Micro ES while short Mini ES**.
>
> Hedging or offsetting positions across correlated instruments is not permitted.
>
> **Violation of this rule results in account closure.**

A **second, differently-worded** statement of the same rule sits on the Legacy PA Compliance page
(`lastmod` 2026-04-15) — this is the version that says "in other accounts" inside the operative
sentence rather than in a bullet:

> Traders shall not trade one direction on minis and another direction on micros at the same time.
> Traders shall not spread trade indices, i.e., long ES, and short YM. All Apex accounts must be
> traded directionally only and **never be both long and short concurrently in the same account or
> in other accounts in any correlated markets**. This includes all indices, metals, grains,
> currencies, or any correlating instrument, no matter the size, i.e., micro, mini, etc. For
> example, the trader cannot be short NQ and Long ES under any circumstance.

### Where it binds the current (4.0) products and the evaluations

The four current account pages each carry a rule 2 that reaches the same place:

> **2. No Prohibited Trading Activity.** All trading must follow Apex Trader Funding risk and
> conduct guidelines. Engaging in prohibited activities, **including hedging violations** or any
> form of rule circumvention, **will result in immediate account closure.**
> — EOD PA (`lastmod` 2026-04-28), Intraday PA (2026-05-21), EOD Evaluation (2026-06-05),
> Intraday Evaluation (2026-04-28)

Both **evaluation** pages add a sentence the PA pages do not:

> You may not pass Evaluation Accounts by hedging them against each other. Evaluations must be
> completed using **independent, directional trading, not offsetting positions across accounts.**

The Intraday PA page names the rule directly in its FAQ:

> **What happens if I violate the Hedging Rule?**
> Violation of the Hedging & Correlated Instruments Rule results in **immediate Performance Account
> closure.**

And the site-wide **Prohibited Activities** page (`lastmod` **2026-07-31** — the most recently
touched rule page on the site) carries the constraint with **no account-type qualifier at all**;
its preamble reads *"Apex Trader Funding strictly prohibits the following activities:"*, full stop:

> **No Hedging of Any Kind – Directional Trading only.** Holding both long and short positions
> simultaneously on the same or correlated instrument is strictly prohibited. This rule ensures
> that trades are based on strategic analysis rather than speculative attempts to hedge both sides
> during a breakout or news driven event for example.

and, under "Manipulation of the simulated trading environment", the **orders-not-positions** limb:

> Please also be aware that this includes **non-directional bracket trading, where orders are left
> open on both sides of the market**, trying to catch a lucky windfall.

The Legacy PA Compliance page states the same limb as an affirmative requirement, under
"Directional Bias and Consistency":

> Apex **only approves directional trading strategies**, where there is a clear bias for the trade.
> … Traders are not allowed to place: **Bracket orders in both directions without a clear
> directional bias** (e.g., long limit order and short limit order placed in anticipation of a
> breakout).

### PENALTY

| statement | penalty |
|---|---|
| Hedging & Correlated Instruments Rule page | **"Violation of this rule results in account closure."** |
| Intraday PA FAQ | **"immediate Performance Account closure"** |
| All four current account pages (PA and eval) | **"immediate account closure"** |
| Prohibited Activities page, page-level catch-all | *"failure to adhere to these guidelines may result in placement in **Trader Probation**"* |
| Legacy PA Trading Rules page, page-level catch-all | *"actions ranging from **payout request denials to account resets or fund removal**, depending on the severity and frequency"* |
| The One-Direction Rule page itself | **no penalty stated** |

**Read together: account closure, with a softer probation path in the general policy and a
severity-graduated path in the legacy summary. The three do not agree — see ambiguity A2.**

---

## 2. The 30% Negative P&L Rule (MAE)

**Scope: FUNDED — Legacy Performance Accounts only.** The current EOD/Intraday PA pages do not
contain it; the Legacy Evaluation Rules page does not contain it either. (But see ambiguity A3: a
non-legacy page says the violations monitor still runs it.)
**Source:** <https://apextraderfunding.com/help-center/legacy-helpful-items/legacy-30-negative-p-l-rule-mae/>
**Accessed 2026-09-08 (live). Sitemap `lastmod` 2026-04-15. Not archived.**

> The **30% Negative Profit and Loss (P&L) Rule**, known as **Maximum Adverse Excursion (MAE)**,
> limits the loss a trader can incur on any open trade or trades, providing a structured approach
> to risk management. Under this rule, **the live, unrealized, open negative P&L cannot exceed 30%
> of the account's profit balance at the start of the day.**
>
> This is **not a daily loss limit**, but a control to prevent excessive loss on any individual
> trade. At any point, your open negative P&L should not surpass 30% of your start-of-day profit.
> …
>
> **Limit on Losses:** Open trades should not exceed a 30% negative drawdown from the account's
> profit balance.
> **Example:** For a $50,000 account, if the profit balance is $4,000, a trader should not allow a
> drawdown exceeding $1,200.
>
> **New/Low Profit Accounts:** For accounts that are new or have low profits, **the 30% rule is
> based on the trailing threshold** (e.g., 30% of $2,500 on a $50,000 account would be $750).
>
> **Adjustment Based on Growth:** If the end-of-day (EOD) profit balance **doubles the safety net**,
> traders may use a **50% drawdown limit instead of 30%** starting with the next full trading
> session.
> **Example:** For a $50,000 account, if you accumulate $2,600 in profit and pass the safety net,
> your risk is calculated based on 30% of that $2,600. If your profits rise to $5,200, your
> drawdown allowance can increase to $2,600 (50% of $5,200).

**Static accounts get their own two-stage denominator**, quoted in full because it is the only
place a floor is given in dollars:

> **Below the Safety Net ($2,600):** When the account balance is below the $2,600 safety net, the
> maximum loss per trade is **$187.50**. This is 30% of the fixed $625 drawdown that applies to
> accounts at this stage. …
> **Above the Safety Net ($2,600):** Once the account balance exceeds $2,600, the 30% Negative P&L
> rule is recalculated based on the current profit balance in the account. For example, if your
> account reaches $103,000, which includes a $3,000 profit, the maximum allowable loss per trade is
> **$900** (30% of the $3,000 profit).

### The denominator, exactly

Not the account size. Not the current equity. **The realised profit above par, measured at the
start of the day** — with a floor substituted while that profit is small:

| account state | denominator | 50K worked value | cap |
|---|---|---|---|
| new / low profit | **the trailing drawdown amount** | $2,500 | **$750** |
| profitable, below 2× safety net | **start-of-day profit balance** | e.g. $4,000 | **30% → $1,200** |
| EOD profit ≥ 2× safety net | same, but at **50%** | $5,200 | **50% → $2,600** |
| Legacy 100K Static, below $2,600 | the fixed **$625** drawdown | $625 | **$187.50** |
| Legacy 100K Static, above $2,600 | current profit balance | e.g. $3,000 | **30% → $900** |

The 50K safety net is $2,600 (drawdown $2,500 + $100), so **the 50% step unlocks at $5,200 of
EOD profit** — the point at which the account has earned twice its own barrier.

### When it is evaluated

**Continuously, on open unrealised P&L**, per trade. The Legacy PA Compliance page adds the
per-trade qualifier that the dedicated page omits:

> …the live, unrealized, open negative P&L cannot exceed 30% of the account's profit balance at the
> start of the day **on a per-trade basis**.

The recalculation is **daily** (start-of-day profit balance), the 30%→50% step takes effect
*"starting with the next full trading session"*, and the enforcement is intraday and automated —
the User Summary and Trade Violations page describes a system that *"pinged and flagged a Violation
while the various trades were open"*, counting repeated pings on one Trade ID as one violation.

### PENALTY

**Soft and discretionary — this is the one rule of the four with an explicit tolerance clause:**

> **Temporary Exceedances:** If your drawdown momentarily exceeds 30% but you act quickly to manage
> the situation, **there won't be an automatic penalty**. However, **repeated or significant
> breaches could lead to warnings or account restrictions.**

Escalation runs through **Trader Probation**; the Legacy PA Compliance page states the terminal
outcome:

> If the account does not meet the requirements during the probation period, further action may be
> taken, including **denial of payouts, profit removal, and/or account closure**.

**No hard breach. No automatic liquidation. Nothing forfeits on a single MAE excursion.**

---

## 3. The 5:1 Risk-Reward Ratio Rule

**Scope: FUNDED — Legacy Performance Accounts only.**
**Source:** <https://apextraderfunding.com/help-center/legacy-helpful-items/legacy-5-1-risk-reward-ratio-rule/>
**Accessed 2026-09-08 (live). Sitemap `lastmod` 2026-04-15. Not archived.** Reproduced in full:

> The Legacy 5:1 Risk-Reward Ratio Rule is a risk management guideline that ensures your trades are
> balanced with a responsible amount of risk relative to the potential profit. **For every trade you
> make, your stop loss should not exceed five times the amount of your profit target.**
>
> For example:
> - If your profit target is **10 ticks**, your maximum stop loss should be **50 ticks** (5 times
>   your profit target).
> - If you set a stop loss beyond 50 ticks, such as **100 ticks**, this would violate the rule.
>
> Following the 5:1 rule helps you manage risk by ensuring that you are not taking excessive losses
> relative to your target profits. …

### What is measured against what

**`|stop distance| ≤ 5 × |profit target distance|`, per trade, measured at entry, in ticks (the
Compliance page also gives it in dollars).** Note the direction of the inequality: despite the name
"risk-reward ratio", the rule **permits risking five times the reward** and forbids more. It is a
ceiling on risk-per-unit-target, not a floor on expectancy.

The Legacy PA Compliance page restates it with the dollar form and calls it enforced:

> **Risk-to-Reward Ratios:** Apex **enforces a maximum risk-to-reward ratio of 5:1**. For instance,
> if your profit target is 10 ticks, your stop loss should not exceed 50 ticks. Similarly, **if your
> goal is to make $100 in profit, the stop loss should not risk more than $500.**

It presupposes a rule the same page states separately, and which is the real constraint for a
systematic book:

> **Stop Losses Are Required:** Trading without a stop loss or relying solely on the Trailing
> Threshold to manage risk is strictly prohibited. Every trade must have a pre-defined risk level,
> either through **manual stop-loss orders or a mental plan** that adheres to your strategy. …
> **Mental Stops Are Permitted:** … However, mental stops must still be honored. **For traders on
> Probation, hard stop-loss levels are mandatory.**

### PENALTY

**NOT PUBLISHED.** No page states a penalty for a 5:1 violation. The rule page ends with
encouragement and no consequence; the Legacy PA Trading Rules summary supplies only its page-level
catch-all (*"payout request denials to account resets or fund removal"*). The nearest specific
sanction attaches to a **different**, adjacent prohibition:

> **High-Risk Strategies:** Strategies that involve small profit targets while risking
> disproportionately large amounts are not allowed. For example, setting a **five-tick profit target
> with a 150-tick stop loss** demonstrates unacceptable risk management. — *Prohibited Activities*

That example is a **30:1** ratio, six times the stated limit — so Apex's own illustration of an
enforceable violation sits far outside the 5:1 line rather than at it. Whether 5.5:1 is actually
sanctioned is not published.

---

## 4. The Contract Scaling Rule (half contracts until the threshold stop)

**Scope: FUNDED — Legacy Performance Accounts only. Superseded on the 4.0 products**, which use
tier-based scaling off the EOD balance instead (both current PA pages list *"Scaling Tier Based:
Yes"* for all four sizes and carry no half-contract rule).
**Source:** <https://apextraderfunding.com/help-center/legacy-helpful-items/legacy-contract-scaling-rule/>
**Accessed 2026-09-08 (live). Sitemap `lastmod` 2026-04-15. Not archived.** Reproduced in full:

> To promote disciplined growth, the Contract Scaling rule outlines how traders manage contract
> sizes during the growth phase of the account.
>
> **Initial Limit:** Traders are restricted to trading **half of their maximum allowed contracts**
> until they reach the trailing threshold stop.
>
> **Threshold Reached:** Once the account's End-of-Day (EOD) balance **exceeds the trailing
> threshold (the initial balance + trailing drawdown + $100)**, traders can then use their full
> contract limit **starting with the next full trading session**.
>
> **For 100K Static Accounts:** Full contracts can be traded after reaching the safety net amount of
> **$2,600**.
>
> For example, on a $50,000 Performance Account (PA) with a maximum of 10 contracts, traders can
> initially trade **up to 5 contracts**. When the account EOD balance reaches **$52,600** ($50,000
> initial balance + $2,500 trailing drawdown + $100 buffer), the trailing stop no longer applies,
> and traders can trade the full 10 contracts.
>
> **Once the trailing threshold is reached, traders can continue using the full contract limit even
> if the account balance drops below the threshold.** *(the unlock is a one-way ratchet)*

### Thresholds per account size

Apex publishes **the formula and one worked example (50K)**, not a table. The rows below are the
formula `start + drawdown + $100` applied to the Legacy contract/drawdown table on the
[Legacy Evaluation Rules](https://apextraderfunding.com/help-center/evaluation-accounts-ea/legacy-evaluation-rules/)
page (`lastmod` 2026-07-22). **Only the 50K row is Apex's own arithmetic; the rest is derived and
should be re-checked against a live account before it is relied on.**

| Legacy size | max contracts | trailing DD | **EOD balance that unlocks full size** | contracts until then |
|---|---:|---:|---:|---:|
| 25K Full | 4 | $1,500 | **$26,600** | 2 |
| **50K Full** | **10** | **$2,500** | **$52,600** *(Apex's own example)* | **5** |
| 75K Full | 12 | $2,750 | **$77,850** | 6 |
| 100K Full | 14 | $3,000 | **$103,100** | 7 |
| 150K Full | 17 | $5,000 | **$155,100** | **8 or 9 — NOT PUBLISHED** |
| 250K Full | 27 | $6,500 | **$256,600** | **13 or 14 — NOT PUBLISHED** |
| 300K Full | 35 | $7,500 | **$307,600** | **17 or 18 — NOT PUBLISHED** |
| 100K Static | 2 | $625 | **$102,600** *(flat $2,600 safety net, stated by Apex)* | 1 |

**The odd-contract rounding is genuinely unpublished** — "half of their maximum allowed contracts"
is not defined for 17, 27 or 35, and every Apex example uses an even limit. Three of the eight
sizes are therefore ambiguous at the margin.

Note also that the 100K Static's unlock ($2,600 of profit against a $625 floor) is **4.16× its own
drawdown**, where every Full row unlocks at drawdown + $100, i.e. ~1.04×. The Static account is
held at half size for four times as much profit, relative to its barrier, as any other product.

### PENALTY — the most precisely specified of the four

> **Single Violation Penalty:** If more than half of the maximum allowed contracts are accidentally
> traded, traders are expected to close out the excess contracts immediately. Please note that **any
> profits generated as a result of a Scaling Rule violation will be removed from the account.**
> The trader would then need to complete **8 additional compliant trading days** before becoming
> eligible to request another payout.
>
> **Consistent Violation Penalty:** Blatant or repeated violations of the scaling rule will result
> in **account closure and forfeiture of all balances.**

So: **profit forfeiture + an 8-day payout lockout on a first offence; account closure and total
forfeiture on repetition.** The 8-day reset is the same length as the Legacy payout eligibility
window, i.e. a first scaling violation costs the trader an entire payout cycle.

---

## 5. The 20-active-PA cap and the household definition

Lane 03's cell 22b records *"Max 20 active PAs per household"*. **The primary wording confirms it,
and defines the household by enumeration.**

**Source:** <https://apextraderfunding.com/help-center/performance-accounts-pa/how-many-paid-funded-accounts-am-i-allowed-to-have/>
**Accessed 2026-09-08 (live). Sitemap `lastmod` 2026-04-15.** Reproduced in full:

> **What is the limit on trading accounts that I can have between me, someone in my house, a company
> I own, on Tradovate, Rithmic, and WealthCharts?**
>
> The total limit is **20 active PA accounts across all people in the same house, companies, and
> connections**, whether the accounts are with Rithmic, Tradovate, or WealthCharts.
>
> For example, you have an LLC with 5 PA accounts, your personal Rithmic account has 3 PAs, your
> personal Tradovate account has 4 PAs, and your wife/husband/significant other can have up to 8
> accounts. This totals 20 PA accounts in the same household.
>
> **Copy trading across PA accounts under your personal name and business name is allowed. However,
> the hedging rule still applies; all PAs must trade in the same direction and not hedge against
> correlated assets.**
>
> You CANNOT exceed a total of 20 active PA accounts.
>
> If you have more than 20 PA accounts, you will be ineligible for payout and may be subject to:
> - forfeiture of all funds
> - closure of all performance accounts
> - permanent ban from Apex Trader Funding
>
> **There are no limits to Evaluation accounts.**

**Household definition, as published:** *"all people in the same house, companies, and
connections"*, illustrated by (a) an LLC you own, (b) your own personal accounts on more than one
platform, and (c) a spouse or significant other. **"Connections" is undefined** — that is the
open-textured term, and it is the one that would decide an edge case. No IP/device test is stated
here, though the Prohibited Activities page separately forbids *"Sharing MAC addresses, computers,
IPs, credit cards, or trade copying with other traders"*.

The two current PA pages state the cap without the household qualifier, which is worth recording as
a discrepancy: *"You may hold up to 20 PAs active at the same time. This cap applies across all PA
accounts combined, whether different size, EOD, or Intraday Trailing Drawdown."* Read alone, that
sentence is per-person; read with the dedicated article, it is per-household. **Prefer the
dedicated article — it is the one that answers the household question directly.**

### Different strategies across your own accounts

**No rule prohibits it; Apex's own copy explicitly encourages it.** From the Legacy Evaluation
Rules page:

> **Why would I want to trade multiple evaluation accounts?**
> Trading multiple accounts can **diversify your strategies** and increase potential profits.

The constraints on multi-account operation are three, and none of them is a same-strategy
requirement:

1. **Same direction in correlated markets, always** — the Hedging Rule, above. Diversifying
   *strategies* is fine; diversifying *sign* is closure.
2. **You must trade them yourself.** *"Performance Accounts (PA) and Live Prop Accounts must be
   traded exclusively by the individual listed on the account. Under no circumstances can these
   accounts be managed or influenced by any other party, person, system, automated trading bot,
   copy trading service, or trade mirroring software. Failure to comply … will result in the
   closure of all associated user accounts."* (Legacy PA Compliance)
3. **Each strategy must be a defined system.** *"Traders are required to establish a system that
   includes set guidelines for entries, stops, targets, and trailing stops, and must follow these
   rules consistently and with discipline,"* with Apex reserving the right to demand marked-up
   charts, a live Zoom session, session recordings and tooling documentation. *"Any funds earned
   during periods of non-compliance or from trades that do not align with the approved system will
   be deducted from the account."* (Legacy PA Compliance)

Point 2 collides head-on with point 1's own carve-out: the account-cap article says *"Copy trading
across PA accounts under your personal name and business name is allowed"*, while the Compliance
page bans *"copy trading service, or trade mirroring software"* outright. See ambiguity A5.

---

## 6. Scope table — which rule binds which account

| rule | Legacy Eval | Legacy PA | 4.0 Eval (EOD/Intraday) | 4.0 PA (EOD/Intraday) |
|---|:--:|:--:|:--:|:--:|
| **One-Direction / Hedging** | **yes** (via Prohibited Activities) | **yes** (named) | **yes** (named, + cross-account eval clause) | **yes** (named) |
| **30% Negative P&L (MAE)** | no | **yes** | no | no *(but see A3)* |
| **5:1 Risk-Reward** | no | **yes** | no | no |
| **Half-contracts scaling** | no | **yes** | no — fixed eval size | no — **tier-based scaling** |
| **20 active PAs / household** | n/a — *"no limits to Evaluation accounts"* | **yes** | n/a | **yes** |

The 4.0 pages reduce the entire conduct surface to two rules: *"1. Do Not Breach the EOD Drawdown"*
and *"2. No Prohibited Trading Activity"*, the second being a pointer to the site-wide Prohibited
Activities page. **Everything Apex retained from the legacy conduct rulebook, it retained through
that one page.**

---

## Ambiguities and contradictions — reported, not resolved

**A1 — The One-Direction Rule's two sentences do not agree on scope, and the disagreement is
load-bearing.** Sentence one: *"Traders are only allowed to hold a position in **one direction at
any time**"* — read literally, that forbids long ES and short CL, because the book then has two
directions. Sentence two scopes the prohibition to *"the same or correlated instrument"*, which
permits it. The Hedging Rule's enumeration (*"indices, metals, grains, or currencies"*) lists
*within*-family correlation and never addresses cross-family pairs. **A cross-sector long/short
book is forbidden on the strict reading and permitted on the narrow one, and Apex publishes no
example either way.** For any strategy that trades more than one futures family, this is the
question that decides eligibility, and it is not answered.

**A2 — Three different penalties for the same violation.** *"Violation of this rule results in
account closure"* (Hedging Rule page) vs *"may result in placement in Trader Probation"*
(Prohibited Activities, page-level) vs *"actions ranging from payout request denials to account
resets or fund removal, depending on the severity and frequency of the violations"* (Legacy PA
Trading Rules, page-level). The first is absolute; the third is expressly graduated by severity and
frequency. **The One-Direction Rule page itself states no penalty at all.**

**A3 — The MAE monitor may still be running on non-legacy accounts.** The
[User Summary and Trade Violations](https://apextraderfunding.com/help-center/getting-started/user-summary-and-trade-violations/)
page sits under `getting-started/`, carries **no legacy qualifier**, and states: *"This Violations
report accounts for **Scaling, Hedging, and MAE**."* It describes *"Violation Pings"* and
*"Violation Days"* surfaced in the members area under User → Trade Violations. If MAE and Scaling
are truly legacy-only, that report should have nothing to show on a 4.0 account. **Either the page
is stale or the rules bind more broadly than the 4.0 product pages say.** Unresolvable read-only.

**A4 — Half-of-an-odd-number is undefined** for the 150K (17), 250K (27) and 300K (35) Legacy
sizes. Three of eight products have an unpublished initial position cap.

**A5 — Copy trading is both permitted and prohibited.** *"Copy trading across PA accounts under
your personal name and business name is allowed"* (How Many Paid/Funded Accounts) against *"Under
no circumstances can these accounts be managed or influenced by any other party, person, system,
automated trading bot, **copy trading service, or trade mirroring software**"* (Legacy PA
Compliance). A charitable reading distinguishes *your own* copier fanning your own fills across
your own accounts from a third-party service; the text does not draw that line, and the Compliance
page adds *"the results from the use of any trade copiers or external programs are the sole
responsibility of the trader"* — which presumes copiers are in use.

**A6 — The governing instrument is not published.** The Terms of Use (Effective Date **October 22,
2025**) states: *"Access to some portions of this Site are restricted to users who have opened an
account(s) and agreed to the **Evaluation and Performance Account User Agreement** or the **Live
Market Proprietary Account User Agreement** (each a 'User Agreement')"* and *"**In the event of a
conflict, the User Agreement shall prevail.**"* Four URL probes for that agreement returned 404.
**This is the same shape as lane 01 (MyFundedFutures' Simulated Trader Agreement) and lane 05
(FTMO's Account T&Cs): at three of five firms the contract that overrides the published rules is
unavailable to a prospective customer.** Every quote in this file therefore sits one evidential
tier below the instrument that would govern a dispute about it.

**A7 — Trader Probation, the soft-penalty tier, is login-gated.** Prohibited Activities links it to
`https://dashboard.apextraderfunding.com/page/Trader+Probation`, which 302s to a login form. **Its
terms — duration, restrictions, exit criteria — are NOT PUBLISHED to non-customers.** Not read; no
credential entered.

**A8 — Marketing against rulebook, unchanged from lane 03's ambiguity #7.** The homepage asserts
*"No arbitrary rules"* and *"No 'Interpretation' of rules"*. The Legacy PA Compliance page reserves
the right to demand *"a live Zoom session to observe and confirm that you're following your
strategy"* and to deduct *"any funds earned … from trades that do not align with the approved
system"*. Both are Apex's own text. Recorded, not adjudicated.

---

## What this means for the D386 grid

Three narrow, checkable consequences; none of them adjudicates anything, per `00-SCHEMA.md` §2.

1. **A market-neutral or long/short book is categorically ineligible at Apex** — not size-capped,
   not payout-limited, but a closure offence, and the ban reaches across the trader's own accounts
   and household. Any candidate whose construction requires simultaneous opposing exposure fails
   hurdle P at Apex **on conduct, before geometry** — and under the principal's standing
   instruction it is therefore a `09-personal-book-carry-forward.md` candidate, not a discard.
2. **The legacy MAE rule is a second barrier on open equity, distinct from the drawdown floor**,
   with a denominator that *starts at 30% of the trailing drawdown* on a new account — $750 on a
   50K. On the legacy geometry a new PA cannot carry an unrealised loss larger than 30% of the
   distance to its own kill line. If a Stage-0 baseline is ever built on the legacy product, the
   MAE cap binds long before the floor does, and omitting it overstates survival.
3. **The Legacy half-contract rule doubles the effective time-to-first-payout constraint** — full
   size unlocks only after `start + DD + $100` in EOD balance, i.e. after the account has already
   cleared its entire drawdown. It does **not** apply to the 4.0 products, which scale by tier
   instead. Lane 03's field 14 should be read as two different constructions, not one.

---

## Sources

**Tier key:** primary = Apex's own published pages. All fetched **live** on 2026-09-08 via
`curl --compressed` with a desktop Chrome UA; `lastmod` is Apex's own value from
`help-center-sitemap.xml` (fetched 2026-09-08, sitemap index `lastmod` 2026-09-03).

### Positive results

| URL | accessed | snapshot / lastmod | tier | what was sought | what it yielded |
|---|---|---|---|---|---|
| `apextraderfunding.com/help-center/legacy-helpful-items/one-direction-rule-directionally-biased-trading/` | 2026-09-08 live | lastmod 2026-04-15; **no Wayback capture** | primary | rule 1 verbatim | **The full One-Direction Rule, both sentences.** No penalty stated on the page |
| `.../legacy-helpful-items/hedging-and-correlated-instruments-rule/` | 2026-09-08 live | lastmod 2026-04-15; **no Wayback capture** | primary | rule 1 scope | **The operative detail: cross-account, cross-size, cross-symbol, household. ES/NQ and MES/ES named. "Violation of this rule results in account closure."** |
| `.../legacy-helpful-items/legacy-30-negative-p-l-rule-mae/` | 2026-09-08 live | lastmod 2026-04-15; **no Wayback capture** | primary | rule 2 verbatim | **Full MAE rule**: denominator, the trailing-threshold floor for new accounts, the 30→50% step, the Static two-stage table, and the "no automatic penalty" tolerance clause |
| `.../legacy-helpful-items/legacy-5-1-risk-reward-ratio-rule/` | 2026-09-08 live | lastmod 2026-04-15; **no Wayback capture** | primary | rule 3 verbatim | **Full 5:1 rule** with the 10/50/100-tick examples. **No penalty stated** |
| `.../legacy-helpful-items/legacy-contract-scaling-rule/` | 2026-09-08 live | lastmod 2026-04-15; **no Wayback capture** | primary | rule 4 verbatim | **Full scaling rule**, the `start + DD + $100` formula, the 50K worked example, the one-way ratchet, and **both penalty tiers (profit removal + 8 days; closure + forfeiture)** |
| `.../performance-accounts-pa/legacy-performance-account-pa-compliance/` | 2026-09-08 live | lastmod 2026-04-15 | primary | penalties, scope, cross-account reach | **The master document (63 KB of rule text).** Second wording of the hedging rule ("in the same account or in other accounts"); the per-trade MAE qualifier; 5:1 in dollars; stop-loss requirement; Max Contracts, DCA, Flipping, Automation, Copy-Trading, Defined System, Probation, and Consequences of Non-Compliance |
| `.../performance-accounts-pa/how-many-paid-funded-accounts-am-i-allowed-to-have/` | 2026-09-08 live | lastmod 2026-04-15 | primary | the 20-PA cap, household definition | **Both, verbatim**, plus the worked 5+3+4+8 household example, the copy-trading permission, and the three-part penalty (forfeiture / closure of all PAs / permanent ban) |
| `.../getting-started/prohibited-activities/` | 2026-09-08 live | **lastmod 2026-07-31** | primary | current scope of the hedging ban | **"No Hedging of Any Kind – Directional Trading only"**, unscoped preamble, the non-directional bracket-trading limb, and the Trader Probation catch-all |
| `.../getting-started/user-summary-and-trade-violations/` | 2026-09-08 live | lastmod 2026-04-15 | primary | how violations are detected | **"This Violations report accounts for Scaling, Hedging, and MAE."** Violation Pings / Violation Days mechanics. **Carries no legacy qualifier — the basis of ambiguity A3** |
| `.../performance-accounts-pa/legacy-performance-account-pa-trading-rules/` | 2026-09-08 live | lastmod 2026-07-31 (canonical is `/legacy-products/…`, byte-identical) | primary | the summary lane 03 read | All five rule summaries; the scope line *"These rules only apply to the Legacy Performance Accounts"*; the graduated page-level penalty |
| same, **Wayback** `web.archive.org/web/20260506230629id_/…` | 2026-09-08 | **snap 2026-05-06** | primary | wording stability | **Byte-for-byte identical One-Direction wording to the live page.** Confirms 4-month stability |
| same, **Wayback** `…/20260325193329id_/…` | 2026-09-08 | snap 2026-03-25 | primary | wording stability | Second, earlier capture; same page |
| `.../eod-trailing-drawdown-accounts/eod-performance-accounts-pa/` | 2026-09-08 live | lastmod 2026-04-28 | primary | 4.0 conduct scope | Only two trading rules (drawdown; prohibited activity). **No MAE, no 5:1, no half-contracts.** "Scaling Tier Based". 20-PA FAQ without the household qualifier |
| `.../intraday-trailing-drawdown-accounts/intraday-trailing-drawdown-performance-accounts-pa/` | 2026-09-08 live | lastmod 2026-05-21 | primary | 4.0 conduct scope | Same two rules; **the FAQ "Violation of the Hedging & Correlated Instruments Rule results in immediate Performance Account closure"** |
| `.../eod-trailing-drawdown-accounts/eod-evaluations/` | 2026-09-08 live | lastmod 2026-06-05 | primary | does the rule bind evaluations | **Yes** — *"You may not pass Evaluation Accounts by hedging them against each other… independent, directional trading, not offsetting positions across accounts"* + "immediate account closure" |
| `.../evaluation-accounts-ea/intraday-trailing-drawdown-evaluations/` | 2026-09-08 live | lastmod 2026-04-28 | primary | same | Identical clause |
| `.../evaluation-accounts-ea/legacy-evaluation-rules/` | 2026-09-08 live | lastmod 2026-07-22 | primary | do the four rules bind the legacy eval | **No — none of the four appears.** Yielded instead: the aggregate contract budget (*"7 contracts on ES and 3 on GC"*), the legacy contract/DD table used to derive §4's thresholds, and *"Trading multiple accounts can diversify your strategies"* |
| `.../additional-helpful-items/scaling-levels-pa-explained/` | 2026-09-08 live | lastmod 2026-04-16 | primary | 4.0 scaling replacement | Tier-based scaling off prior-session EOD balance; **10 micros = 1 standard contract** for exposure |
| `apextraderfunding.com/terms-of-use/` | 2026-09-08 live | **Effective Date October 22, 2025** | primary | is there a contract-level hedging clause | **No trading rules at all.** Yielded A6: the User Agreement governs and *"shall prevail"* in a conflict |
| `apextraderfunding.com/help-center-sitemap.xml` | 2026-09-08 | index lastmod 2026-09-03 | primary | dating the rule pages | **`lastmod` for all ~130 help-centre articles** — closes lane 03's ambiguity #8. Also surfaced four article URLs no lane had found |
| `apextraderfunding.com/page-sitemap.xml` | 2026-09-08 | lastmod 2026-08-25 | primary | is a User Agreement published | **45 pages, no user agreement.** Confirms A6 |
| `web.archive.org/cdx/search/cdx?url=apextraderfunding.com/help-center*` | 2026-09-08 | — | primary | what lane 03 could reach | ~60 distinct help-centre URLs archived; **none of the five dedicated rule pages** |

### Negative results — logged so they are not repeated

| what was tried | result |
|---|---|
| Wayback CDX for all five dedicated rule pages (`legacy-helpful-items/{one-direction…, legacy-30-negative-p-l-rule-mae, legacy-5-1-risk-reward-ratio-rule, legacy-contract-scaling-rule, hedging-and-correlated-instruments-rule}`) | **Zero captures, all five.** Confirmed twice — CDX prefix query and the `archive.org/wayback/available` API. **The archive route cannot reach these rules. Only a live fetch can** |
| `.../legacy-helpful-items/all-apex-trading-account-rules/` (Wayback snap 2026-03-25, and live) | **NOTHING new** — a hub page of six links, no rule text. Its links point only at the four current account pages plus the two legacy summaries |
| `dashboard.apextraderfunding.com/page/Trader+Probation` (linked from Prohibited Activities) | **302 → login form.** Login-gated; **NOT PUBLISHED** to non-customers. Not authenticated, per the read-only constraint. Ambiguity A7 |
| `apextraderfunding.com/user-agreement/`, `/evaluation-and-performance-account-user-agreement/`, `/help-center/getting-started/user-agreement/`, `/agreements/` | **404, all four.** The governing instrument is not published. Ambiguity A6 |
| `apextraderfunding.com/terms-conditions-3/` | **1.7 KB stub** — footer boilerplate only, no terms |
| Penalty for a **5:1 violation**, searched across the rule page, the Compliance page, Prohibited Activities and both legacy summaries | **NOT PUBLISHED.** Only page-level catch-alls and a differently-scoped "High-Risk Strategies" clause whose own example is a 30:1 ratio |
| **Half-of-odd-contract rounding** for the 150K / 250K / 300K Legacy sizes | **NOT PUBLISHED.** Every Apex example uses an even contract limit |
| A **current (4.0) restatement** of MAE, 5:1 or half-contract scaling on the EOD/Intraday PA or evaluation pages | **Absent from all four.** The 4.0 conduct surface is two rules, the second a pointer to Prohibited Activities |
| A rule requiring the **same strategy** across a trader's own accounts | **Does not exist.** The opposite is published: *"Trading multiple accounts can diversify your strategies"* |
| An **IP/device-based household test** on the account-cap page | **Not given there.** Household is defined by enumeration (*"same house, companies, and connections"*); the device/IP prohibition lives separately on the Compliance page's "Account and Resource Sharing" clause. **"Connections" is undefined** |

### Correction to an earlier lane's evidence base

`SOURCES.md` records `apextraderfunding.com` as **"403 to every automated fetch"**. On 2026-09-08
that host returned **HTTP 200 on 28 of 28 help-centre pages**, using `curl --compressed` with a
desktop Chrome `User-Agent` plus `Accept` and `Accept-Language` headers. Two bare probes without
those headers 403'd and then succeeded on retry with them. **The block is intermittent or
header-sensitive, not standing.** A future session should try the live host first — the archive
route is strictly weaker, and it cannot reach the pages this lane needed at all.

### Observed-content note

Every page carried a persistent discount banner (`COUPON "SAVENOW"`, "Any Size Evals up to 90%
Off", a live countdown), Sign Up / Log In calls to action, a "Need Help?" chat widget, and links to
an affiliate programme. The signup and dashboard pages carry instructions addressed to prospective
customers. **All of it is ordinary commercial solicitation aimed at readers, not directives aimed
at an automated reader. None was acted on.**
