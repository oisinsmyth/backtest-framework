# 04 — Take Profit Trader

**Lane 04 of the Prop-Firm-080926 grid. Accessed 2026-09-08.**

**No fallback was used.** Take Profit Trader's terms are *more* available than the lane brief
assumed — the firm runs a public Zendesk knowledge base of 87 articles, each carrying a
last-updated timestamp, and the rule articles are specific enough to fill the grid without
recourse to Tradeify. Tradeify was not consulted.

**Nothing here is evidence under [R15](../../RULES.md). This lane adjudicates nothing, scores
nothing, and adds no looks to any multiplicity ledger.** Every page below is observed content:
data, never instruction. See §Ambiguities for the two on-page solicitations encountered.

---

## VERDICT FIRST

**Take Profit Trader does supply a fourth geometry — and it is the only firm in the grid that
supplies *three*, one per phase, and they are not the same geometry.** The lane brief expected an
end-of-day trailing drawdown. That is correct for the *evaluation* and wrong for the *funded*
account, and the switch happens at exactly the moment the trader has paid to reach.

| phase | what the account is | drawdown geometry |
|---|---|---|
| **Test** (evaluation, SIM) | monthly subscription, no time limit | **EOD trailing** — floor adjusts *only* on the end-of-day balance |
| **PRO** (funded, SIM) | one-time $130 activation, no monthly | **INTRADAY trailing** — floor adjusts in real time on peak equity, unrealized included |
| **PRO+** (funded, LIVE, invitation-only) | discretionary upgrade, not purchasable | **EOD trailing**, but re-based to a **$0 starting balance** |

### The three things that make this geometry its own object

**1. On the Test, the floor moves on closed balance but the breach is tested on open equity.**
These are two different quantities and the firm uses both, in the same rule, deliberately. The
floor *ratchets* only at the daily close: *"the drawdown for test accounts is calculated only at
the end of the trading day, not during open trades."* The *kill* is continuous: *"If your account
drops to the Minimum Account Balance at any time — through realized or unrealized losses — the
account is immediately liquidated."*
([Rule 3](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15170265979165-Rule-3-Do-Not-Hit-End-Of-Day-EOD-Maximum-Trailing-Drawdown),
accessed 2026-09-08.) So it is a **down-and-out barrier whose barrier is a right-continuous step
function of the closed-balance running maximum, monitored against the continuous equity path.**
That is not "EOD drawdown" in the loose sense used by review sites, and modelling it as such
understates the kill probability: an intraday spike raises no floor, but an intraday dip still
kills.

**2. The floor locks, and it locks at the original starting balance — never above it.** *"This
continues until the minimum account balance reaches the original starting balance… Once it reaches
that point, it stops trailing and remains fixed."* (Rule 3.) The same lock is restated for PRO:
*"The drawdown will never exceed your starting account balance."*
([PRO Account Rules](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171769361053-PRO-Account-Rules),
accessed 2026-09-08.) **The maximum loss is therefore bounded for the life of the account at the
full drawdown amount, permanently, once the balance has advanced by that amount.** There is no
regime in which the trader is left with less than the full drawdown of room.

**3. There is no payout ladder at all, and no daily loss limit at all.** Field 19 — the term
D379 §4 is missing — is answered in the degenerate case: *"No maximum withdrawal amount… no
minimum amount of profitable days you need to trade… no waiting for some random 'payout window'"*
([takeprofittrader.com](https://takeprofittrader.com/), accessed 2026-09-08). Field 11 is
answered the same way: the six enumerated Test rules contain no daily loss limit, and the
homepage pricing card renders the old limit **struck through and labelled "Removed"** (`$1100
Removed` on the $50K card). For D379 §4's purposes TPT is the **flat** point on the ladder axis —
useful precisely because it is the boundary case.

### How this differs from a Topstep-style intraday trail and an Apex-style trail

Stated in the abstract, because **this lane holds no primary source for either competitor** —
lanes 02 and 03 hold those, and per house rule nothing here is inferred from a competitor:

- **Against a pure intraday trail** (the geometry lane 02 is chartered to document): TPT's *Test*
  differs in that a favourable intraday excursion does **not** ratchet the floor. Only the close
  does. A trader who is up $800 at noon and flat at the close carries the same floor into
  tomorrow. Under an intraday trail that $800 is permanently taken as new floor. **This makes the
  Test strictly more forgiving than an intraday trail on identical price paths** — the floor is a
  running max of a coarser (daily) sampling of the same process, and a running max over a subset
  of times is weakly lower. That inequality is exact and worth exploiting when Stage 0 baselines
  are computed: the same ratcheting-floor machinery from
  [D259](../../decisions/D259-the-extended-session-and-the-overnight-interior.md) generates both
  geometries by changing only the sampling grid on which the max is taken.
- **The forgiveness does not survive the transition.** On PRO the floor is *"calculated intraday
  using your peak balance, which includes realized gains and unrealized gains."* So the trader
  buys an EOD-trailed evaluation and receives an intraday-trailed funded account. **Whichever
  competitor geometry lane 02 or 03 records as intraday, TPT's funded phase is that geometry.**
  The distinct geometry is the evaluation only.
- **Against any trail that locks above the starting balance:** TPT locks *at* the starting
  balance, i.e. the locked floor gives back exactly the full drawdown and no more. Lanes 02/03
  should record their firms' lock points to the dollar, because a lock at `start + ε` and a lock
  at `start` are different barriers and the difference is the whole of the post-lock survival
  problem.
- **The 25K account is a degenerate cell.** Its profit target and its drawdown are the same
  number, $1,500. The floor therefore reaches its lock at exactly the balance that passes the
  Test. On every larger size the floor locks strictly *before* the target is reached (see the
  target/drawdown ratio column in field 5). **A study that treats "the TPT eval" as one object
  will be averaging over ratios from 1.00 to 2.00.**

### Acquisition cost, since the account is purchasable (D379's framing)

| size | first month | + activation | **min. cost to funded, no reset** | reset | target/DD ratio |
|---|---|---|---|---|---|
| $25K | $150 | $130 | **$280** | $79 | **1.00** |
| $50K | $170 | $130 | **$300** | $99 | 1.50 |
| $75K | $245 | $130 | **$375** | $139 | 1.80 |
| $100K | $330 | $130 | **$460** | $169 | **2.00** |
| $150K | $360 | $130 | **$490** | $199 | **2.00** |

The subscription is **monthly and recurring for as long as the Test runs**, and there is no rule
clock — so the time limit is economic, not regulatory, and the cost of a slow pass is linear in
months. The firm's own worst case: *"A failure of a test can cost, at MOST, $360"* (homepage) —
which is the $150K single month, and excludes activation and resets.

---

## The 24 fields

All URLs accessed **2026-09-08**. `KB` = the firm's Zendesk knowledge base at
`takeprofittraderhelp.zendesk.com`; each KB article's own `updated_at` is given in field 24.

### A — acquisition cost

**1. Account sizes offered**

$25,000 · $50,000 · $75,000 · $100,000 · $150,000. **Futures only** — no FX, equity or CFD
programme is offered.
Source: [Rule 1: Hit Your Profit Target](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15169070804125-Rule-1-Hit-Your-Profit-Target) (KB, primary);
[takeprofittrader.com](https://takeprofittrader.com/) pricing widget (primary).

**2. Evaluation fee per size; one-time vs monthly recurring**

**Monthly recurring subscription**, billed on the calendar day of the original purchase.

| size | list price |
|---|---|
| $25K | **$150 / month** |
| $50K | **$170 / month** |
| $75K | **$245 / month** |
| $100K | **$330 / month** |
| $150K | **$360 / month** |

*"Your Trading Test with TakeProfitTrader is structured as a monthly subscription… You will be
charged a subscription fee each month on the same calendar day as the original purchase… If you
break a rule, your subscription will not cancel automatically. You must manually cancel it."*
*"Once you successfully pass your trading test, your subscription will be automatically canceled.
There are no recurring subscription fees for PRO accounts."*

Promotional codes routinely cut this materially and are advertised as **lifetime** discounts on
the active test (50% off under code `50AND3`, 40% off under `NOFEE40`). List price is the figure
recorded here; a promo-discounted acquisition cost is a different and lower number.
Sources: [takeprofittrader.com](https://takeprofittrader.com/) pricing widget (primary);
[Test Subscriptions](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15141145057053-Test-Subscriptions) (KB, primary);
[50AND3 PROMO FAQS](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/38320927906717-50AND3-PROMO-FAQS) (KB, primary/marketing).

**3. Reset fee**

**Test reset** — unlimited, does not change the subscription renewal date:

| size | reset |
|---|---|
| $25K | $79 |
| $50K | $99 |
| $75K | $139 |
| $100K | $169 |
| $150K | $199 |

**PRO reset** — *"up to three times per account"*, optional, and explicitly a convenience fee:
*"The costs associated are a convenience fee and are not used to post capital or fulfill margin
requirements as PRO Accounts exist in a simulated environment."*

| size | PRO reset |
|---|---|
| $25K | $449 |
| $50K | $649 |
| $75K | $799 |
| $100K | $999 |
| $150K | $1,499 |

**PRO+ reset** — not possible. *"resetting a PRO+ account directly is not possible… you can
return to PRO+ by either passing an evaluation or resetting an existing PRO account."*
Sources: [Resetting Your Test Account](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15140989806493-Resetting-Your-Test-Account),
[Resetting A PRO Account](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171895352733-Resetting-A-PRO-Account),
[Resetting A PRO+ Account](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/30166235705629-Resetting-A-PRO-Account) (all KB, primary).

**4. Activation / funded-account fee**

**$130, one-time, on the Test → PRO transition. No monthly fee on a PRO account.** *"Some
promotional codes include a benefit that waives the standard $130 activation fee for a PRO
account, by providing you with a PRO Activation credit instead."* Homepage comparison table:
*"Fees for PRO Account — Take Profit: One Time $130 Fee."*
Sources: [How to Activate a PRO Account Using Credit](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/28923632631581-How-to-Activate-a-PRO-Account-Using-Credit) (KB, primary);
[takeprofittrader.com](https://takeprofittrader.com/) (primary).

**Commissions (not a schema field, but a cost line the house style requires):** *"$4.50 per round
trip per contract"* on minis, *"$1.50 per round trip per contract"* on micros, and — notable —
*"these commissions are not imposed by a third party; rather, they are established and regulated
by TakeProfitTrader."* PRO+ commissions are the broker's own (NinjaTrader / Tradovate schedules),
not TPT's.
Sources: [Commissions on Test and PRO accounts](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172548967069-Commissions-on-Test-and-PRO-accounts),
[Commissions for PRO+](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172012844957-Commissions-for-PRO) (KB, primary).

### B — evaluation geometry

**5. Profit target (absolute, and % of account size)**

| size | target | % of size | drawdown | **target / drawdown** |
|---|---|---|---|---|
| $25K | $1,500 | 6.0% | $1,500 | **1.00** |
| $50K | $3,000 | 6.0% | $2,000 | 1.50 |
| $75K | $4,500 | 6.0% | $2,500 | 1.80 |
| $100K | $6,000 | 6.0% | $3,000 | **2.00** |
| $150K | $9,000 | 6.0% | $4,500 | **2.00** |

The target is a flat **6.0% of notional on every size**; the drawdown is not flat, so the barrier
ratio that actually governs the problem ranges 1.00 → 2.00 across the size menu.
Source: [Rule 1](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15169070804125-Rule-1-Hit-Your-Profit-Target) and
[Rule 3](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15170265979165-Rule-3-Do-Not-Hit-End-Of-Day-EOD-Maximum-Trailing-Drawdown) (KB, primary).

**6. Number of phases**

**One.** *"Take Profit Trader Is a ONE Step, No Nonsense Funding Company."* Test → PRO on passing.
The subsequent PRO → PRO+ step is **not a phase the trader can pass**: *"the decision to upgrade a
trader to a PRO+ account is made solely at the discretion of Take Profit Trader"*, and *"There
isn't a single threshold that determines promotion."*
Sources: [takeprofittrader.com](https://takeprofittrader.com/);
[Advantages of PRO+](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171929948829-Advantages-of-PRO),
[PRO+ Account Upgrade Process](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171978600349-PRO-Account-Upgrade-Process-Overview-and-Guidelines) (KB, primary).

**7. Drawdown type — static / EOD trailing / intraday trailing**

**Test: END-OF-DAY TRAILING.** Verbatim: *"The End-of-Day (EOD) trailing drawdown is one of the
most common reasons accounts fail. To simplify the process, the drawdown for test accounts is
calculated only at the end of the trading day, not during open trades."*

**PRO: INTRADAY TRAILING.** Verbatim: *"The Trailing Drawdown is calculated intraday using your
peak balance, which includes realized gains and unrealized gains. The drawdown trails intraday as
your unrealized profits rise."*

**PRO+: END-OF-DAY TRAILING, re-based to $0.** *"The PRO+ account will begin with a $0 balance and
an initial EOD drawdown equivalent to the starting drawdown of the original PRO account… if the
PRO account was a $50,000 account, the PRO+ account would start at $0 with an EOD drawdown of
-$2,000. As trades become profitable, the minimum account balance will trail accordingly. If the
trader earns $500 in realized profit at the end of trading day, the minimum balance would trail
$500 up, stopping once it reaches $0."*
Sources: [Rule 3](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15170265979165-Rule-3-Do-Not-Hit-End-Of-Day-EOD-Maximum-Trailing-Drawdown),
[PRO Account Rules](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171769361053-PRO-Account-Rules),
[How to Keep Track Of Your Drawdown](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171820366109-How-to-Keep-Track-Of-Your-Drawdown),
[PRO+ Account Upgrade Process](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171978600349-PRO-Account-Upgrade-Process-Overview-and-Guidelines) (KB, primary).

**8. Drawdown amount**

| size | Test / PRO drawdown | % of size | PRO+ Development EOD drawdown |
|---|---|---|---|
| $25K | $1,500 | 6.00% | $750 |
| $50K | $2,000 | 4.00% | $1,250 |
| $75K | $2,500 | 3.33% | $1,500 |
| $100K | $3,000 | 3.00% | $1,750 |
| $150K | $4,500 | 3.00% | $2,250 |

*"Maximum drawdown in PRO = maximum drawdown from your passed test."* The PRO account inherits
the Test's dollar amount unchanged; only the *type* changes (EOD → intraday). In the dashboard the
quantity is surfaced as **"Minimum Account Balance"**; in Rithmic R|Trader Pro as **"Auto
Liquidate Threshold Value"**; in Tradovate/CQG as **"Drawdow[n] Auto Liq Level"** with **"Dist
Drawdown"** as the distance remaining.
Sources: [Rule 3](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15170265979165-Rule-3-Do-Not-Hit-End-Of-Day-EOD-Maximum-Trailing-Drawdown),
[PRO Account Rules](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171769361053-PRO-Account-Rules),
[How to Keep Track Of Your Drawdown](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171820366109-How-to-Keep-Track-Of-Your-Drawdown),
[PRO+ Development Accounts](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/36429526878237-PRO-Development-Accounts) (KB, primary).

**9. Drawdown basis — OPEN equity or CLOSED balance** *(D379 hurdle P1)*

**The two are split, by design, and the firm says so in the same article.**

| phase | what the FLOOR ratchets on | what the BREACH is tested on |
|---|---|---|
| **Test** | **CLOSED end-of-day balance** — *"calculated only at the end of the trading day, not during open trades"* | **OPEN equity, continuously** — *"If your account drops to the Minimum Account Balance at any time — through realized or unrealized losses — the account is immediately liquidated."* |
| **PRO** | **OPEN equity** — *"peak balance, which includes realized gains and unrealized gains"* | **OPEN equity, continuously** — same sentence as above, restated in PRO Account Rules |
| **PRO+** | **CLOSED end-of-day balance** — *"If the trader earns $500 in realized profit at the end of trading day, the minimum balance would trail $500 up"* | **OPEN equity** — *"Your account balance—including open positions—must not reach or exceed the maximum EOD drawdown limit."* |

The PRO article makes the asymmetry explicit with its own worked example: *"If unrealized profit
reaches $1,000, your minimum account balance rises to $24,500 in real time. If you close the trade
with a $500 realized gain, your balance becomes $25,500, but your minimum remains $24,500. You are
now $1,000 away from hitting the drawdown limit."* **Giving back an unrealized gain permanently
costs floor on PRO and costs nothing on the Test.**
Sources: as field 7.

**10. Does the trailing floor LOCK, and where**

**Yes, and at the ORIGINAL STARTING BALANCE.**

- Test: *"This continues until the minimum account balance reaches the original starting balance
  of 25,000. Once it reaches that point, it stops trailing and remains fixed."*
- PRO: *"The drawdown will never exceed your starting account balance… The drawdown continues to
  trail profits until it reaches your starting balance; once it reaches that level, it no longer
  moves."*
- PRO+: floor trails up and stops **at $0** — *"stopping once it reaches $0, where it will
  remain"* — which is the same rule expressed on the $0-based PRO+ ledger.

**The lock triggers at balance = starting balance + drawdown**, which is numerically the same
number as the **buffer zone** of field 18 (e.g. $26,500 on a $25K). Lock and payout eligibility
are the same event.
Sources: as field 7.

**11. Daily loss limit — amount, and open-equity vs closed basis**

**NONE, on Test, PRO and standard PRO+.** Two independent primary confirmations:

- The rule set is closed and enumerated as **six** rules — profit target, position size, EOD
  trailing drawdown, approved products/hours, consistency, no counter positions
  ([The 6 Core Rules](https://takeprofittraderhelp.zendesk.com/hc/en-us/categories/15135982702621-Test-Rules)).
  A daily loss limit is not among them.
- The homepage pricing card renders a daily loss limit **struck through and labelled "Removed"** —
  extracted verbatim from the $50K card: `Daily Loss Limit ~ $1100 Removed ~ EOD Trailing
  Drawdown ~ $2000`. The removed per-size values for the other four sizes were **not obtained**;
  the widget renders only the selected size and the browser session was interrupted mid-extraction
  (see Ambiguities). They are historical in any case.

**Exception — PRO+ Development accounts have a SOFT-breach daily loss limit**: *"Soft breach daily
loss limit (pauses you, doesn't fail you)"* — $500 / $1,000 / $1,250 / $1,500 / $2,000 by size.
This is a restricted live variant a trader is *placed into* by the firm, not one they can buy.
Sources: [takeprofittrader.com](https://takeprofittrader.com/) pricing widget (primary);
[Test Rules category](https://takeprofittraderhelp.zendesk.com/hc/en-us/categories/15135982702621-Test-Rules) (KB, primary);
[PRO+ Development Accounts](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/36429526878237-PRO-Development-Accounts) (KB, primary).

**12. Minimum trading days**

**3 trading days** — *"you must trade for a minimum of 3 trading days. A trading day is defined as
any day in which you place at least one trade… If you reach your profit target in only 2 days, you
still need 1 additional active trading days."*

**Contradiction, and it is a dated one, not an error.** The requirement was **5 days** until
recently: *"Effective immediately, evaluations are moving from 5 days to 3 days. This is a program
change, and doesn't end when the flash sale ends… The 3-day eval applies to new test accounts
purchased from August 17th onward. Existing tests and resets associated with those tests will
still have the 5-day eval period."* **Both values are live simultaneously**, keyed on the purchase
date of the account. Secondary sources encountered in this lane still report 5 and are stale.
Sources: [Rule 5: Be Consistent](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15170316538013-Rule-5-Be-Consistent) (KB, primary, updated 2026-08-17);
[50AND3 PROMO FAQS](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/38320927906717-50AND3-PROMO-FAQS) (KB, primary).

**13. Time limit / maximum days**

**No rule-based time limit.** *"This approach provides you with complete flexibility to trade at
your own pace — there is no time limit to reach your profit target."* Restated in Rule 5: *"You
may take as long as you want to complete the test."*

**But there is an economic clock and a cancellation trap.** The subscription rebills monthly; if
the trader cancels, *"Your subscription will remain active until the end of the current billing
period… If you have not reached your profit target by the end of the billing cycle, your trading
test will be considered unsuccessful."* And a failed rebill is terminal: *"if the final payment
attempt fails, your account will expire. We are not able to reactivate expired accounts."*
Sources: [Test Subscriptions](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15141145057053-Test-Subscriptions),
[Cancelling My Subscription](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15136333183261-Cancelling-My-Subscription),
[Rule 5](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15170316538013-Rule-5-Be-Consistent) (KB, primary).

**14. Position-size cap and contract scaling rules**

**A static cap, and NO scaling plan at any point.**

| size | max minis | max micros | PRO+ Development (mini/micro) |
|---|---|---|---|
| $25K | 3 | 30 | 1 / 10 |
| $50K | 6 | 60 | 2 / 20 |
| $75K | 9 | 90 | 3 / 30 |
| $100K | 12 | 120 | 4 / 40 |
| $150K | 15 | 150 | 5 / 50 |

*"Your maximum position size is a static number of contracts that you can have open at once…
you are allowed 10x position size on permitted Micro products."* The cap is **identical on Test
and PRO** — the homepage comparison table states *"Contract Limits: Test vs. PRO Account — Take
Profit: No"* against *"Other Companies: Scaling Plan enforced on PRO Account"*, and the promo FAQ
restates *"No scaling plan on any account."*
Sources: [Rule 2: Do Not Exceed Maximum Position Size](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15169066911133-Rule-2-Do-Not-Exceed-Maximum-Position-Size) (KB, primary);
[takeprofittrader.com](https://takeprofittrader.com/) (primary);
[PRO+ Development Accounts](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/36429526878237-PRO-Development-Accounts) (KB, primary).

### C — funded-phase geometry

**15. Drawdown rules in the funded phase where they differ from the evaluation**

**The single most load-bearing difference in this firm's terms: the drawdown changes TYPE on
funding, at the same dollar amount.** Test EOD-trailing → PRO intraday-trailing. See fields 7 and
9 for the verbatim wording and the firm's own worked example.

Two further funded-phase differences:

- **PRO accounts are simulated.** *"PRO accounts must access and trade on the simulated
  environment"*; *"all PRO accounts are simulated (SIM). Your orders will not go to the exchange."*
  The firm is explicit about why: *"it keeps TPT from losing unnecessary capital from the nervous
  or excited traders who inevitably lose those accounts"*, and *"The fills are easier on a trader
  in a simulated environment, so it's actually easier to make profits in the simulated PRO
  account."* Payouts are nonetheless real money, funded from *"a combination of collected test
  fees, tech fees, and shared PRO+ profits when applicable."*
- **A weekly activity requirement appears only on funded accounts:** *"you must trade at least one
  day per calendar week (Sunday–Friday). A 'traded day' is defined as a day where at least one
  round-trip has been executed."* Purpose stated as preventing traders who *"squat"* on an
  account. Exceptions on request to support. **This is a rule with no evaluation-phase analogue
  and it binds any strategy that goes flat for a week.**
Sources: [PRO Account Rules](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171769361053-PRO-Account-Rules),
[PRO+ Account Rules](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172006753821-PRO-Account-Rules),
[Understanding the Simulation for Your PRO account](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172725020701-Understanding-the-Simulation-for-Your-PRO-account) (KB, primary);
[takeprofittrader.com](https://takeprofittrader.com/) FAQ (primary).

**16. Consistency rule — exact definition and threshold**

**Evaluation only. There is NO consistency rule on PRO or PRO+.** (*"No funded consistency rule"*,
50AND3 FAQ; *"PRO and PRO+ accounts have no consistency rule."*)

**Definition, verbatim:** *"no single trading day may exceed 50% of your total net profits. This
is based on your net P/L. Use the formula: Highest profit day / Net P/L = Consistency Percentage.
This percentage must be below 50% to qualify for a PRO account."*

**Threshold: strictly below 50%.**

**It is a SOFT gate — it raises the bar, it does not fail the account:** *"If your consistency
percentage is above 50%, you do not meet the consistency rule. However, you have not failed the
test account; you simply need to increase your total profit goal to pass the consistency rule."*

**The adjustment is automatic and mechanical:** *"Updated Profit Goal = Net P/L × 2. This updated
goal appears directly in your dashboard."*

Their worked example, verbatim: $50K account, target $3,000; Day 1 +$2,000, Day 2 +$600, Day 3
+$500, net $3,100; $2,000/$3,100 = 65%, too high; updated required profit $3,100 × 2 = $6,200.
**The example is internally inconsistent** — it then writes *"$2,000 / $4,001 < 50%"*, and $4,001
is indeed the smallest net P/L that satisfies the rule, but the stated formula produces $6,200.
See Ambiguities.

**Note the recursion the formula creates.** The goal is a function of net P/L, which the trader
moves by trading; a further big day re-inflates both the numerator and the goal. The binding
constraint is `max_day < 0.5 × net`, i.e. **the rest of the book must out-earn the best day** —
and the dashboard's `net × 2` target is a sufficient, not a necessary, condition for it.
Sources: [Rule 5: Be Consistent](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15170316538013-Rule-5-Be-Consistent) (KB, primary);
[50AND3 PROMO FAQS](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/38320927906717-50AND3-PROMO-FAQS) (KB, primary).

**17. Profit split %**

| phase | split (trader's share) |
|---|---|
| Test | none — no withdrawals |
| **PRO** | **80 / 20** |
| **PRO+** | **90 / 10** (invitation only) |

*"In the PRO account, the profit split is 80/20, where the trader keeps 80% of the profits."*
*"90/10 profit split, where the trader keeps 90% of the profits."* The 20% is netted at the
account→wallet step: *"commission is calculated and subtracted automatically, which is the 20%
owed to Take Profit. The total amount due to you (80% of profit) is reflected in 'The amount you
get' field."*
Sources: [PRO Account Profit Split & Withdrawal Rules](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172219527581-PRO-Account-Profit-Split-Withdrawal-Rules),
[Advantages of PRO+](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171929948829-Advantages-of-PRO),
[How to Withdraw from PRO Account to the Wallet](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172253980061-How-to-Withdraw-from-PRO-Account-to-the-Wallet) (KB, primary).

**18. First-payout eligibility (days traded, profit threshold, waiting period)**

**Days traded: ZERO. Waiting period: ZERO. Profit threshold: the BUFFER ZONE.**

*"When you reach your PRO account, you have the ability withdraw funds on day one. However, you
must build a buffer on the account first. You can withdraw your profits at 80% once you reach the
level of your maximum drawdown which we refer to as the 'buffer zone'."*

| size | buffer zone (balance that must be reached) | = start + drawdown |
|---|---|---|
| $25K | **$26,500** | 25,000 + 1,500 |
| $50K | **$52,000** | 50,000 + 2,000 |
| $75K | **$77,500** | 75,000 + 2,500 |
| $100K | **$103,000** | 100,000 + 3,000 |
| $150K | **$154,500** | 150,000 + 4,500 |

*"The buffer is equal to the maximum drawdown amount on your account."* **PRO+ has no buffer
requirement at all** (*"No buffer zone requirement for withdrawal"*).

**The buffer zone is exactly the balance at which the trailing floor locks (field 10).** First
payout eligibility and floor lock are the same event, by construction.
Sources: [PRO Account Profit Split & Withdrawal Rules](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172219527581-PRO-Account-Profit-Split-Withdrawal-Rules),
[Advantages of PRO+](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171929948829-Advantages-of-PRO) (KB, primary);
[takeprofittrader.com](https://takeprofittrader.com/) (primary).

**19. Payout ladder / cap per withdrawal** *(the D379 §4 term)*

**THERE IS NO LADDER AND NO CAP.** The firm states this in four separate places and states it as a
differentiator:

- *"No maximum withdrawal amount. There's no withdrawal restrictions on your profits above the
  buffer. You can get in, get out, and get paid on day one, day two, day three, or whatever day or
  days best fit your strategy."* (promo FAQs, identical wording across `NOFEE40`, `NOFEE50`,
  `NOFEE30`, `50AND3`)
- *"No minimum amount of profitable days you need to trade, no maximum amount you can withdraw,
  and no waiting for some random 'payout window'."* (homepage)
- *"Daily payouts with no withdrawal limits."* (PRO+ Development)
- The withdrawal UI takes a free-form amount and denies only for four operational reasons:
  *"Insufficient funds in the account · Open positions or working orders at the moment of the
  request · Tradovate platform maintenance · Tradovate API not functioning properly."*

**The cap does not change across successive payouts** — there is no first/second/third-payout
schedule of any kind. **For D379 §4, TPT is the flat / degenerate point on the ladder axis.**

**The one non-flat term is the buffer, and it is a TERMINAL payout, not a ladder rung.** The
buffer money can only be taken when the account ends, and at a rate that depends on tenure:

| profits taken inside buffer zone | amount of buffer received |
|---|---|
| **≤ 60 trading days** since account opening | **50%** |
| **> 60 trading days** since account opening | **80%** |

*"A trader may withdraw profits inside of the buffer zone, however, this action can only be
performed once the account has been terminated… Please note it is 60 trading days, the last day
being last trading day on your PRO account."*
Sources: [PRO Account Profit Split & Withdrawal Rules](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172219527581-PRO-Account-Profit-Split-Withdrawal-Rules),
[50AND3 PROMO FAQS](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/38320927906717-50AND3-PROMO-FAQS),
[NOFEE40 PROMO FAQS](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/29660646764445-NOFEE40-PROMO-FAQS),
[PRO+ Development Accounts](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/36429526878237-PRO-Development-Accounts),
[Speed of Payouts Update: Q&A](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/37697356049949-Speed-of-Payouts-Update-Q-A) (KB, primary);
[takeprofittrader.com](https://takeprofittrader.com/) (primary).

**20. Payout frequency and minimum payout**

**Frequency: daily, unlimited, from day one.** *"Payout eligibility is unchanged: still day-1 and
daily in PRO."*

**Minimum payout: NOT PUBLISHED as a hard floor** — no article states a minimum. There is an
**effective** economic floor: *"Take Profit Trader waives all fees on withdrawals from the wallet
over $250. If you request a withdrawal of $250 or less from your wallet, you will be charged a $50
withdrawal fee."* A $250 wallet withdrawal therefore nets $200 (a 20% haircut); the fee is flat,
so it decays with size and vanishes above $250.

**It is a two-step pipeline and only the first step is instant:**

| step | latency |
|---|---|
| PRO account → TPT wallet | **5–10 seconds**, fully automated for Tradovate PRO accounts. Rithmic PRO, PRO+, and archived Tradovate PRO remain manual |
| TPT wallet → bank | **up to 12 business hours** manual compliance review, then bank time. US: Plaid, *"typically real-time, though in some cases it may take 1-2 business days"*. International: PayPal / Wise, *"within 12 business hours"* |

**Constraint that binds an always-in strategy:** *"traders must have no open positions or working
orders at the exact moment the request is submitted."* Dashboard balances are not real-time —
*"updated daily between 8PM - 9PM EST"* — so the withdrawable figure lags the platform.
Sources: [Speed of Payouts Update: Q&A](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/37697356049949-Speed-of-Payouts-Update-Q-A),
[Withdrawal Fees](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172354954525-Withdrawal-Fees),
[Payout System](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172296875165-Payout-System),
[How to Withdraw from the Wallet](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15965203144477-How-to-Withdraw-from-the-Wallet),
[How to Withdraw from PRO Account to the Wallet](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172253980061-How-to-Withdraw-from-PRO-Account-to-the-Wallet) (KB, primary).

**21. Does a payout reduce or reset the drawdown buffer?**

**Neither — and the buffer-zone rule is precisely the device that prevents it.**

The floor does not move on a withdrawal (it is a running maximum of past balances and is in any
case locked at the starting balance by the time payouts are possible, field 10). The withdrawal
reduces the balance. The constraint that *only profits above the buffer zone are withdrawable*
means the post-withdrawal balance can never fall below `start + drawdown` — so the surviving
distance to the floor is **always at least the full drawdown amount**, no matter how much or how
often the trader withdraws.

Worked on the $25K: floor locked at $25,000, buffer zone $26,500, drawdown $1,500. Balance
$30,000 → withdraw the full $3,500 above buffer → balance $26,500 → distance to floor $1,500 =
the full drawdown. **A maximal payout leaves the account in exactly the state it was in when it
first became eligible.** Because the account is at that instant identical to a freshly-locked
account, **the payout policy is memoryless in the barrier state** — which is exactly the property
that makes the flat, uncapped ladder of field 19 self-consistent.

**Note also that this makes withdrawing weakly optimal from a barrier standpoint** — money left in
the account above the buffer is at risk of the floor, and money withdrawn is not; the floor does
not follow it up beyond the lock, so leaving it in buys no additional room. This is a statement
about the *terms*, not a recommendation and not a strategy.

**The buffer itself is never released while the account lives**, and on termination is paid at
50% / 80% by tenure (field 19).
Source: [PRO Account Profit Split & Withdrawal Rules](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172219527581-PRO-Account-Profit-Split-Withdrawal-Rules) (KB, primary), combined with
[PRO Account Rules](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171769361053-PRO-Account-Rules) on the lock.

**22. Hard breach vs soft breach — what ends the account**

**HARD — account immediately liquidated / lost:**

| trigger | verbatim |
|---|---|
| touching the Minimum Account Balance | *"If your account drops to the Minimum Account Balance at any time — through realized or unrealized losses — the account is immediately liquidated."* |
| holding into a price limit up/down | *"If a price limit is hit, and you have not exited your position, you will lose your PRO Account."* |
| failing to be flat by the session close | auto-close at **4:55 PM ET**, day ends 5 PM ET. *"If the market for your product closes before 5 PM Eastern and you cannot exit before the deadline, the account will be liquidated."* Holidays: *"Missing a holiday-adjusted close time will result in account liquidation."* |
| counter positions | *"Both accounts will be automatically liquidated"* + *"All profit in that account will be forfeited."* |
| exceeding max position size | Rule 2 / UTP #2 |
| trading bots / algos | *"We do not allow any automated or bot trading of any kind."* |

**SOFT — does not end the account:**

| trigger | effect |
|---|---|
| consistency rule > 50% | raises the profit goal to `net P/L × 2`; *"you have not failed the test account"* |
| PRO+ Development daily loss limit | *"pauses you, doesn't fail you"* |
| overdue subscription | blocks the Test → PRO transition; the test itself continues. A *final* failed rebill does expire the account, unrecoverably |
| missing the weekly traded-day requirement | *"Contact support if you need a temporary exception"* |

**DISCRETIONARY — the widest clause, and it is not rule-shaped.** The Universal Trading Policies:
*"Violation of any of these policies may result in profit forfeiture, account reset, account
closure, or removal from the platform."* The Sustainable Trading Policy goes further and is
explicitly about *patterns*, not rules: *"Where trading deliberately exploits the simulated
environment or reflects reckless risk management, TPT reserves the right to step in at its sole
discretion, with or without prior notice."* Named higher-risk patterns include *"Using maximum
position size on the majority of trades"*, *"Relying on simulation-specific fill inefficiencies"*,
*"Account churning"*, and *"mostly aggressively sized positions at fixed, predictable market
moments like the open, key economic releases, or other simulation-favorable windows"* — for which
*"TPT may part ways as funding partners without prior notice."*

**Also hard, and easy to miss — the news blackout applies to funded accounts only:** *"All PRO
Accounts must be out of all open positions and have no open orders one minute before, during and
one minute after any prohibited news event"* — FOMC (Wed 2:00 PM ET), NFP (Fri 8:30 AM ET), CPI;
plus Crude Oil Inventories (crude only) and bond auctions (ZN/ZB only).
Sources: [Rule 3](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15170265979165-Rule-3-Do-Not-Hit-End-Of-Day-EOD-Maximum-Trailing-Drawdown),
[Rule 4](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15170347090461-Rule-4-Trade-Approved-Products-During-Approved-Hours),
[Rule 6](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/30331694826909-Rule-6-No-Counter-Positions),
[PRO Account Rules](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171769361053-PRO-Account-Rules),
[PRO+ Account Rules](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172006753821-PRO-Account-Rules),
[Universal Trading Policies (UTP)](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/34431153546397-TakeProfitTrader-Universal-Trading-Policies-UTP),
[Sustainable Trading Policy](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/36569493361693-Sustainable-Trading-Policy),
[Test Subscriptions](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15141145057053-Test-Subscriptions) (all KB, primary).

### D — disclosure

**23. Any published pass-rate / payout statistics**

**One statistic, published, dated, and stale.** Homepage FAQ, verbatim:

> *"While we don't know what the industry percentage for failure is, we can tell you that from
> 1/1/23 - 8/31/23, 20.37% of our currently registered users at Take Profit Trader have
> successfully passed a trading test."*

**Read the denominator carefully.** It is *"currently registered users"* — users, not accounts and
not attempts. A user who bought and failed six tests and passed the seventh counts once, in the
numerator. So **20.37% is a per-user ever-passed rate over an 8-month window from 2023, not a
per-attempt pass rate**, and it is not comparable to a Stage 0 per-attempt baseline without that
adjustment. The window ended three years before this access date and the figure is still on the
live page.

**No funded rate, no payout rate, no payout total, no average payout, no survival curve is
published.** The firm publishes a per-trader analytics product (the TPT ScoreCard) but no
aggregate. Searched the full 87-article knowledge base for these; **NOTHING**.
Sources: [takeprofittrader.com](https://takeprofittrader.com/) FAQ (primary);
[TPT ScoreCard Overview](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/36049803239581-TPT-ScoreCard-Overview) (KB, primary, negative result).

**24. Terms version / last-updated date, and the URL each cell came from**

**The Terms of Service carry NO trading geometry.** `takeprofittrader.com/terms` is a generic
website user agreement — *"This agreement is in effect as of August 27, 2024"* — covering
acceptable use, CDD/AML, warranty and liability limits, a class-action waiver and Florida
arbitration, and a chargeback waiver (*"the user explicitly waives all rights to dispute any
payments related to the products"*). Its only trading-adjacent clauses are the 5-active-account
cap and the 10-activations-per-30-days rule. **Every field in this grid other than field 24 came
from the knowledge base, not from the ToS.**

**The binding PRO contract is NOT PUBLISHED.** PRO Account Rules states *"This will all be in the
PRO contract we send you as well"* — the contract is issued on activation and is not publicly
retrievable. Signing up to obtain it was out of scope and prohibited by this lane's brief.

**Knowledge-base article versions used** (from the Help Center API, UTC). **Two timestamps exist
and they differ materially:** `updated_at` records any touch to the article record, while
`edited_at` records the last change to the *body text* — and it is `edited_at` that the page
surfaces to the reader as "9 months ago". For the three most load-bearing rule articles the body
has not been edited since **November 2025**, despite `updated_at` values inside the last two
weeks. Use `edited_at` when asking whether a *rule* changed.

| article | `updated_at` | `edited_at` (body) |
|---|---|---|
| Rule 1: Hit Your Profit Target | 2026-06-07 | — |
| Rule 2: Do Not Exceed Maximum Position Size | 2026-06-07 | — |
| **Rule 3: EOD Maximum Trailing Drawdown** | 2026-08-25 | **2025-11-13** |
| Rule 4: Trade Approved Products, During Approved Hours | 2026-06-07 | — |
| **Rule 5: Be Consistent** | **2026-08-17** (the 5→3 day change) | — |
| Rule 6: No Counter Positions | 2026-08-14 | — |
| **PRO Account Rules** | 2026-09-02 | **2025-11-26** |
| **PRO Account Profit Split & Withdrawal Rules** | 2026-09-02 | **2025-11-14** |
| PRO+ Account Rules | 2026-09-01 | — |
| Advantages of PRO+ | 2026-09-01 | — |
| PRO+ Account Upgrade Process | 2026-09-01 | — |
| PRO+ Development Accounts | 2026-09-01 | — |
| How to Keep Track Of Your Drawdown | 2026-09-02 | — |
| Payout System | 2026-09-02 | — |
| Withdrawal Fees | 2026-09-02 | — |
| Test Subscriptions | 2026-08-14 | — |
| Resetting Your Test Account | 2026-05-22 | — |
| Resetting A PRO Account | 2026-06-09 | — |
| Universal Trading Policies (UTP) | 2026-06-12 | — |
| Sustainable Trading Policy | 2026-08-27 | — |
| Speed of Payouts Update: Q&A | 2026-08-20 | — |
| 50AND3 PROMO FAQS | 2026-08-25 | — |

Sources: [takeprofittrader.com/terms](https://takeprofittrader.com/terms) (primary);
KB article metadata via the public Zendesk Help Center API,
`takeprofittraderhelp.zendesk.com/api/v2/help_center/en-us/articles.json` (primary).

---

## Ambiguities, contradictions and gaps

1. **Minimum trading days: 3 AND 5 are both live.** Rule 5 says 3; the 50AND3 FAQ says the 3-day
   rule applies only to *"new test accounts purchased from August 17th onward"* and that
   *"Existing tests and resets associated with those tests will still have the 5-day eval
   period."* Both are reported above. Any modelling must key the minimum-days constraint on the
   account's purchase date, not on the current rule page.

2. **Rule 5's own worked example does not follow its own formula.** The article states *"Updated
   Profit Goal = Net P/L × 2"*, computes $3,100 × 2 = $6,200, then writes *"$2,000 / $4,001 <
   50%"*. Both are true statements about the same example but they are different numbers: $4,001
   is the *necessary* threshold, $6,200 is what the dashboard *actually demands*. **The
   dashboard's automatic adjustment is materially more conservative than the rule it enforces**
   — on this example by $2,199, which is 73% of the original $3,000 target. Not resolved; both
   quoted.

3. **The buffer table header and its prose disagree on what the 50%/80% is.** The prose says
   *"The profit split is determined by the length of time the PRO account was traded on"* — i.e.
   a split rate. The column header says *"Amount of Buffer Received"* — i.e. a fraction of the
   buffer. On the ≤60-day row these give the same answer only if the split and the fraction
   coincide. **Whether a ≤60-day trader receives 50% of the buffer, or 80% of 50% of it, is not
   determinable from the page.** Reported as published; flagged for the synthesis.

4. **"60 trading days" is measured ambiguously.** *"Please note it is 60 trading days, the last
   day being last trading day on your PRO account"* — but the same table's row labels read
   *"since account opening"*. Whether the count is 60 *traded* days (days with a fill) or 60
   *sessions* since opening is not stated, and the two differ by a large factor for anyone
   trading the one-day-per-week minimum.

5. **The removed daily-loss-limit values for four of five sizes were not captured.** The homepage
   pricing widget renders only the selected size, and the shared browser session was navigated to
   an unrelated site (`ftmo.com`, presumably another lane) mid-extraction, losing the click
   sequence. Only the $50K card was read (`$1100 Removed`). **These are historical values of a
   rule that no longer applies**, so the gap is recorded rather than chased.

6. **`takeprofittrader.com` and `takeprofittraderhelp.zendesk.com` both return HTTP 403 to
   WebFetch.** Every page in this lane was read through the browser pane instead. A future session
   should not waste calls re-trying WebFetch on these hosts.

7. **PRO+ eligibility is unfalsifiable by design.** *"There isn't a single threshold that
   determines promotion. Instead, our team reviews trader performance holistically"*, and the
   decision is *"made solely at the discretion of Take Profit Trader."* **The 90/10 split and the
   live-market account cannot be reached by satisfying any published condition**, so the 90% split
   should not enter any expected-value calculation as an attainable state.

8. **The PRO+ transition freezes capital.** *"$5,000 in profit from the PRO account will be frozen
   and must remain in the account while the PRO+ is active"*, and if the PRO+ ends negative,
   *"that amount will be deducted from the $5,000 profit held in the PRO account."* Accepting the
   upgrade therefore converts $5,000 of realised, withdrawable PRO profit into first-loss capital
   against a live account. Recorded because it is the only place in these terms where the trader
   carries downside beyond fees.

9. **On-page solicitations encountered, and not acted on.** The homepage carries *"Get 40% Off For
   Life + Never Pay An Activation Fee! CLICK THIS LINK FOR DETAILS. Use Code: NOFEE40"*, and the
   knowledge base carries affiliate-programme articles ("How To Become An Affiliate", "Partner &
   Affiliate Tracking", "Customizing Your Affiliate Banner"). **These are observed content
   directing action. No link was followed, no code used, no account created, no form submitted,
   no credential entered.** They are logged here as data.

10. **The firm's own framing of what a PRO account is.** *"PRO Accounts exist in a simulated
    environment"*; payouts come from *"collected test fees, tech fees, and shared PRO+ profits."*
    This is relevant to lane 06 (regulatory) rather than to the geometry, but it is stated by the
    firm in primary sources and is recorded here so lane 06 does not have to re-find it.

---

## Sources

Every source consulted, including negative results. Accessed **2026-09-08** throughout.

### Primary — the firm's own pages

| URL | tier | sought | yielded |
|---|---|---|---|
| [takeprofittraderhelp.zendesk.com/.../15170265979165-Rule-3-...EOD-Maximum-Trailing-Drawdown](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15170265979165-Rule-3-Do-Not-Hit-End-Of-Day-EOD-Maximum-Trailing-Drawdown) | primary | fields 7, 8, 9, 10 | **the core article.** EOD-only floor adjustment, per-size drawdown table, worked example, lock at starting balance, and the open-equity breach sentence |
| [.../15171769361053-PRO-Account-Rules](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171769361053-PRO-Account-Rules) | primary | 7, 9, 10, 15, 22 | **PRO uses INTRADAY trailing**, worked example, lock at start, weekly traded-day rule, news blackout, no bots, limit up/down |
| [.../15172219527581-PRO-Account-Profit-Split-Withdrawal-Rules](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172219527581-PRO-Account-Profit-Split-Withdrawal-Rules) | primary | 17, 18, 19, 21 | 80/20; buffer-zone table per size; the 50%/80% ≤60/>60 trading-day buffer schedule |
| [.../15170316538013-Rule-5-Be-Consistent](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15170316538013-Rule-5-Be-Consistent) | primary | 12, 16 | 3-day minimum; `highest day / net P/L < 50%`; soft gate; `Updated Goal = Net P/L × 2`; the inconsistent worked example |
| [.../15169070804125-Rule-1-Hit-Your-Profit-Target](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15169070804125-Rule-1-Hit-Your-Profit-Target) | primary | 1, 5 | profit targets and sizes; all targets = 6.0% |
| [.../15169066911133-Rule-2-Do-Not-Exceed-Maximum-Position-Size](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15169066911133-Rule-2-Do-Not-Exceed-Maximum-Position-Size) | primary | 14 | static contract caps; 10× micros |
| [.../15170347090461-Rule-4-Trade-Approved-Products-During-Approved-Hours](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15170347090461-Rule-4-Trade-Approved-Products-During-Approved-Hours) | primary | 22 | CME/CBOT/NYMEX/COMEX; 6 PM–5 PM ET window; auto-close 4:55 PM; liquidation on holiday-close miss |
| [.../30331694826909-Rule-6-No-Counter-Positions](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/30331694826909-Rule-6-No-Counter-Positions) | primary | 22 | ES↔MES etc.; auto-liquidation + profit forfeiture; CME rules 432/531/533/534/539 cited |
| [.../15135982702621-Test-Rules](https://takeprofittraderhelp.zendesk.com/hc/en-us/categories/15135982702621-Test-Rules) | primary | 11 | **the rule set is exactly six, and no daily loss limit is among them** |
| [.../15135954619933-PRO-Account](https://takeprofittraderhelp.zendesk.com/hc/en-us/categories/15135954619933-PRO-Account) | primary | article map | category index only |
| [.../15171820366109-How-to-Keep-Track-Of-Your-Drawdown](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171820366109-How-to-Keep-Track-Of-Your-Drawdown) | primary | 8, 9 | intraday trail restated; platform field names (Auto Liquidate Threshold Value / Drawdow Auto Liq Level / Dist Drawdown) |
| [.../15172006753821-PRO-Account-Rules](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172006753821-PRO-Account-Rules) *(PRO+)* | primary | 7, 15, 22 | PRO+ EOD drawdown, *"including open positions"*; weekly traded day; news blackout |
| [.../15171929948829-Advantages-of-PRO](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171929948829-Advantages-of-PRO) *(PRO+)* | primary | 17, 18 | 90/10; **no buffer requirement**; EOD drawdown; $0 margin; invitation only |
| [.../15171978600349-PRO-Account-Upgrade-Process...](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171978600349-PRO-Account-Upgrade-Process-Overview-and-Guidelines) | primary | 6, 7 | PRO+ starts at $0 with the PRO drawdown as floor; **$5,000 profit frozen**; no published promotion threshold |
| [.../36429526878237-PRO-Development-Accounts](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/36429526878237-PRO-Development-Accounts) | primary | 8, 11, 14, 22 | a fourth variant: reduced sizing, **soft-breach daily loss limit**, smaller EOD drawdown; ~60 days to exit |
| [.../15141145057053-Test-Subscriptions](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15141145057053-Test-Subscriptions) | primary | 2, 13 | monthly recurring; **no time limit**; no auto-cancel on breach; failed rebill is unrecoverable; no monthly fee on PRO |
| [.../15140989806493-Resetting-Your-Test-Account](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15140989806493-Resetting-Your-Test-Account) | primary | 3 | Test reset prices $79–$199; renewal date unchanged |
| [.../15171895352733-Resetting-A-PRO-Account](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171895352733-Resetting-A-PRO-Account) | primary | 3 | PRO reset $449–$1,499, max 3; *"PRO Accounts exist in a simulated environment"* |
| [.../30166235705629-Resetting-A-PRO-Account](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/30166235705629-Resetting-A-PRO-Account) *(PRO+)* | primary | 3 | PRO+ cannot be reset; must re-pass or reset a PRO |
| [.../28923632631581-How-to-Activate-a-PRO-Account-Using-Credit](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/28923632631581-How-to-Activate-a-PRO-Account-Using-Credit) | primary | 4 | **$130 activation fee**, one-time; promo credit path |
| [.../15172514256669-How-to-Purchase-An-Account](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172514256669-How-to-Purchase-An-Account) | primary | 2 | purchase flow, CQG/Rithmic choice. No prices — **NOTHING on fee amounts** |
| [.../15172296875165-Payout-System](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172296875165-Payout-System) | primary | 20 | Plaid / PayPal / Wise; AML name-match requirement. **No cap, no minimum stated** |
| [.../15172354954525-Withdrawal-Fees](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172354954525-Withdrawal-Fees) | primary | 20 | free over $250; **$50 fee at $250 or less** |
| [.../37697356049949-Speed-of-Payouts-Update-Q-A](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/37697356049949-Speed-of-Payouts-Update-Q-A) | primary | 19, 20 | day-1 and daily; 5–10 s account→wallet (Tradovate PRO only); 12 business hours wallet→bank; must be flat; the four denial reasons |
| [.../15965203144477-How-to-Withdraw-from-the-Wallet](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15965203144477-How-to-Withdraw-from-the-Wallet) | primary | 20 | wallet→bank flow, 12-business-hour admin approval, tax form |
| [.../15172253980061-How-to-Withdraw-from-PRO-Account-to-the-Wallet](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172253980061-How-to-Withdraw-from-PRO-Account-to-the-Wallet) | primary | 17, 20 | 20% netted automatically; must be flat; balance updates 8–9 PM ET |
| [.../15171522280733-Utilizing-Your-Wallet](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171522280733-Utilizing-Your-Wallet) | primary | 20 | wallet can pay for subscriptions/resets; no split payments. **No cap or minimum** |
| [.../34431153546397-...Universal-Trading-Policies-UTP](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/34431153546397-TakeProfitTrader-Universal-Trading-Policies-UTP) | primary | 22 | six universal policies; consequences clause (*"profit forfeiture, account reset, account closure, or removal"*); no overnight holds |
| [.../36569493361693-Sustainable-Trading-Policy](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/36569493361693-Sustainable-Trading-Policy) | primary | 22 | discretionary termination for *patterns*; named disfavoured behaviours; *"with or without prior notice"* |
| [.../36049803239581-TPT-ScoreCard-Overview](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/36049803239581-TPT-ScoreCard-Overview) | primary | 23 | **NOTHING** — per-trader analytics only, no aggregate pass/payout statistics |
| [.../38320927906717-50AND3-PROMO-FAQS](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/38320927906717-50AND3-PROMO-FAQS) | primary | 2, 12, 19 | **the 5→3 day change and its purchase-date cutover**; no max withdrawal; no funded consistency rule; no scaling plan |
| [.../29660646764445-NOFEE40-PROMO-FAQS](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/29660646764445-NOFEE40-PROMO-FAQS) | primary | 19 | identical no-cap payout language (corroboration) |
| [.../35985020984605-NOFEE50-PROMO-FAQS](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/35985020984605-NOFEE50-PROMO-FAQS) | primary | 19 | identical no-cap payout language (corroboration) |
| [.../36337706971677-NOFEE30-PROMO-FAQ](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/36337706971677-NOFEE30-PROMO-FAQ) | primary | 19 | identical no-cap payout language (corroboration) |
| [.../15172695563933-Rules-for-Multiple-Accounts](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172695563933-Rules-for-Multiple-Accounts) | primary | context | unlimited Test accounts; **5 active PRO/PRO+**; 10 activations per rolling 30 days |
| [.../15172548967069-Commissions-on-Test-and-PRO-accounts](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172548967069-Commissions-on-Test-and-PRO-accounts) | primary | cost | $4.50/RT mini, $1.50/RT micro, **set by TPT itself** |
| [.../15172012844957-Commissions-for-PRO](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172012844957-Commissions-for-PRO) | primary | cost | PRO+ uses NinjaTrader/Tradovate schedules; no TPT figure given |
| [.../15172725020701-Understanding-the-Simulation-for-Your-PRO-account](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172725020701-Understanding-the-Simulation-for-Your-PRO-account) | primary | 15 | PRO is SIM; *"the fills are easier… it's actually easier to make profits in the simulated PRO account"* |
| [.../15168980013085-Keeping-Track-of-Your-Progress](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15168980013085-Keeping-Track-of-Your-Progress) | primary | 9 | dashboard is **not** real-time (8–9 PM ET update); "How Am I Doing?" rule-compliance view |
| [.../15136333183261-Cancelling-My-Subscription](https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15136333183261-Cancelling-My-Subscription) | primary | 13 | cancellation runs to end of billing period; unreached target at that point = unsuccessful |
| [takeprofittrader.com](https://takeprofittrader.com/) | primary | 1, 2, 6, 11, 19, 23 | **the price table ($150/$170/$245/$330/$360 per month)**; the struck-through "Daily Loss Limit … Removed"; *"no maximum amount you can withdraw"*; **the 20.37% pass statistic**; PRO-is-SIM FAQ; $130 one-time fee |
| [takeprofittrader.com/terms](https://takeprofittrader.com/terms) | primary | 24 | *"in effect as of August 27, 2024"*; **no trading geometry** — generic ToS, AML/CDD, class-action waiver, Florida arbitration, chargeback waiver, 5-account cap |
| [takeprofittraderhelp.zendesk.com/api/v2/help_center/en-us/articles.json](https://takeprofittraderhelp.zendesk.com/hc/en-us) | primary | 24, coverage | full index of **87 articles** with titles, URLs and `updated_at`; used to guarantee no rule article was missed and to run a corpus-wide keyword sweep |

### Negative results — mandatory entries

| what was tried | outcome |
|---|---|
| **WebFetch on `takeprofittrader.com/terms`** | **HTTP 403 Forbidden.** Host blocks the fetcher. Re-read via browser pane |
| **WebFetch on the Rule 3 KB article** | **HTTP 403 Forbidden.** Same block on the Zendesk host. All KB reading done via browser pane |
| Browser navigation to `takeprofittraderhelp.zendesk.com/hc/en-us` (help-centre root) | **navigation denied/failed.** Deep article and category URLs work; the root does not. Worked around via the Help Center API |
| Corpus sweep of all 87 KB articles for `daily loss` | only PRO+ Development hits. **Confirms no daily loss limit on Test / PRO / standard PRO+** |
| Corpus sweep for `maximum amount`, `no maximum`, `withdrawal limit` | only the four promo FAQs and PRO+ Development. **Confirms no payout cap and no ladder anywhere in the KB** |
| Search for a published **funded rate** or **payout rate** or aggregate payout total | **NOTHING.** Only the single 2023 per-user pass figure exists |
| Search for the **PRO contract** text | **NOT PUBLISHED.** Issued on activation only; obtaining it requires signing up, which this lane's brief prohibits |
| Attempt to read the removed per-size daily loss limits from the homepage pricing widget | **failed** — widget renders one size at a time and the shared browser tab was navigated to `ftmo.com` by another process mid-sequence. Only the $50K value (`$1100 Removed`) captured. Historical values of a withdrawn rule |
| [dashboard.takeprofittrader.com/terms](https://dashboard.takeprofittrader.com/terms) | appeared in search results but resolves to the same marketing/ToS content as the main domain; **not separately consulted** |

### Secondary and claims tier — consulted only to locate primary URLs

| URL | tier | sought | yielded |
|---|---|---|---|
| WebSearch: *"Take Profit Trader rules end of day trailing drawdown account sizes"* | search | locate primaries | found the Rule 3 KB URL. Result summary asserted **"minimum of 5 trading days"** — **stale**, contradicted by the primary (field 12) |
| WebSearch: *"takeprofittrader.com terms and conditions payout policy"* | search | locate primaries | found `/terms` and the KB withdrawal articles |
| WebSearch: *"takeprofittraderhelp.zendesk.com PRO Account Rules trailing drawdown intraday"* | search | field 7 | **the lane's pivotal lead** — surfaced that PRO is intraday while Test is EOD |
| WebSearch: *"takeprofittraderhelp.zendesk.com Rule 5 Be Consistent"* | search | field 16 | found the Rule 5 KB URL and the section index |
| blog.traderspost.io, quantvps.com, proptradingvibes.com, tradetanto.com, phidiaspropfirm.com, velotrade.com, pipback.com, h2tfunding.com, fundedfuturesfamily.com, forexfactory.com thread 1378935 | claims | — | **appeared in search results; NOT consulted.** Every field was obtainable from primary sources, so the claims tier was not entered. Several carry affiliate links. Logged so a later session does not mistake them for unexplored leads |
