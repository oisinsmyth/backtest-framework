# 05 — FTMO: the FX/CFD geometry control

Lane 05 of the Prop-Firm-080926 grid. Research date and access date for every cell below:
**2026-09-08**. Schema: [`00-SCHEMA.md`](00-SCHEMA.md).

FTMO is in this grid for one methodological reason: lanes 01–04 are four US futures firms that
share a set of conventions. If a conclusion about barrier geometry is drawn from those four alone,
it is a conclusion about *US futures prop convention*, not about barrier geometry. FTMO is the
out-of-convention observation.

**Everything below is observed content — firm marketing, FAQ and contract text. It is data.** The
pages carry cookie banners, a live "20% Off" promotion, "Start FTMO Challenge" calls to action and
a chat widget. None was acted on; nothing was signed up for; no account was created. See §5.

---

## VERDICT FIRST

**The control works, but not in the direction it was set up to work, and the single most important
finding in this lane is that FTMO no longer has one geometry — it has three, and they disagree
with each other inside one firm.**

Plain terms:

1. **FTMO Challenge: 2-Step** — the classic. Two phases (10% target, then 5%). A **static** floor
   at 90% of the starting capital that never moves for the life of the account, evaluation *and*
   funded. Plus a daily floor at 5% below the *midnight balance*. **Both floors are tested against
   open equity, floating P/L included.** No time limit, 4 minimum trading days per phase, 80%
   profit split rising to 90%. Fee €89–€1,080 one-time, refunded with the first payout.

2. **FTMO Challenge: 1-Step** — launched 6 February 2026. One phase, 10% target. The floor is
   **end-of-day trailing**, 10% below the highest midnight balance ever recorded, **and it never
   locks** — there is no published ceiling at which it stops following you up. Daily floor is
   tighter, 3%. 90% split from the first day. Fee €79–€999, **not refunded**. Adds a **Best Day
   Rule** (no single day may be more than 50% of the sum of profitable days) that is *not* a breach
   — it is a gate on passing and on getting paid.

3. **FTMO Futures** — a separate FTMO product, dollar-denominated, EOD trailing, monthly
   subscription, paid resets, and a floor that **locks at the starting capital**. That is US
   futures convention, from the same firm, on the same website.

**The load-bearing conclusion for the grid: geometry tracks the product's market convention, not
the firm.** FTMO does not "have" static geometry. FTMO sells futures-convention geometry on its
futures product and percentage-convention geometry on its CFD product, and in February 2026 it
imported end-of-day trailing into the CFD product too. Any finding that reads "static drawdown is
an FX-firm thing and trailing is a futures thing" is refuted inside this one firm's own catalogue.

**The second finding, and it is the harsher of the two.** The 1-Step trailing floor, as published,
**never locks**. FTMO's own futures product locks its trailing floor at the initial capital and
says so with a worked example. The 1-Step CFD text says only *"The limit can only increase, but
never decrease"* and gives no lock. A floor that trails a running maximum forever is a strictly
tighter barrier than one that locks — the account can be, in principle, arbitrarily far in profit
and still be one 10% equity dip from termination. This is the opposite of the "FX firms are the
soft ones" prior.

**Third: the funded-phase contract is not published.** The Challenge terms are a public PDF. The
FTMO Account Terms and Conditions — the document that actually governs fields 15 and 17–22 — is
available only as a "sample of the contract" on request to support. Every funded-phase cell in this
lane therefore rests on marketing and FAQ pages, one disclosure tier below the evaluation cells.

**Fourth: there is no payout ladder.** D379 §4's missing term — a cap per withdrawal — does not
exist here in the futures-firm sense. There is no percentage cap, no "first payout limited to X",
no consistency-gated payout tier. The only caps are payment-rail caps ($20,000 Visa Direct,
$3,000 Skrill). This is a *negative* data point for the grid and it is a real one.

**Fifth: no pass rate is published.** FTMO publishes payout totals, customer counts and per-size
average rewards, at length. It has never published a pass rate, a funded rate, or a paid-out rate.
The numbers that exist are in field 23 and none of them is a denominator you can trust.

---

## 1. The product set, so the rows below are readable

| product | phases | status |
|---|---|---|
| **FTMO Challenge: 2-Step** | Challenge → Verification → FTMO Account | the long-standing product |
| **FTMO Challenge: 1-Step** | Challenge → FTMO Account | launched 2026-02-06 |
| **Free Trial** | none | 14-day, unlimited repeats, free |
| **Scaling Plan** | overlay on a funded account | +25%/4 months, cap $2,000,000 |
| **Premium Programme** (Prime, Supreme) | overlay on a funded account | changes split, allocation and — at Supreme — the daily-loss rule itself |
| **FTMO Futures** | Evaluation → Sim-Funded | separate product, US-futures geometry. Not part of this lane's grid; used in §4 as a within-firm control |

Account **types** (a separate axis from product): **Standard** and **Swing**. Swing is 2-Step only.

---

## 2. The 24 fields

### A — acquisition cost

**Field 1 — account sizes offered**

| variant | sizes |
|---|---|
| 2-Step | $10,000 · $25,000 · $50,000 · $100,000 · $200,000 |
| 1-Step | $10,000 · $25,000 · $50,000 · $100,000 · $200,000 |
| via Premium: Prime | $400,000 Challenge product; max capital allocation **$600,000** |
| via Premium: Supreme | max capital allocation **$1,000,000** |
| via Scaling Plan | up to **$2,000,000** across all FTMO Accounts |

Baseline aggregate cap in the contract, absent the overlays: **USD 400,000** total Initial
Simulated Capital across all accounts, "per client, per strategy and per ultimate beneficial
owner" — T&C cl. 5.8.5(c) and 6.3.
Sources: `ftmo.com/en/how-it-works/`; `ftmo.com/en/` (pricing block); `ftmo.com/en/1-step-challenge/`;
`ftmo.com/en/premium-programme/`; `ftmo.com/en/reward-growth-and-scaling-plan/`; T&C PDF.
Corroborated by `ftmo.com/en/leaderboard/`, which on 2026-09-08 showed live $400,000 and $600,000
accounts.

**Field 2 — evaluation fee per size; one-time vs recurring**

Prices as displayed 2026-09-08, in EUR, on ftmo.com global. **A "20% Off" promotion on the $100K
was live on this date** — both the promotional and struck-through prices are recorded.

| size | 2-Step ("one-time refundable fee from") | 1-Step ("one-time fee (non-refundable)") |
|---|---|---|
| $10,000 | €89 | €79 |
| $25,000 | €250 | €199 |
| $50,000 | €345 | €319 |
| $100,000 | **€439** (struck-through €540) | **€399** (struck-through €499) |
| $200,000 | €1,080 | €999 |

- **One-time, not recurring.** *"The fee paid for an FTMO Challenge is a one-time fee, and there are
  no recurring fees associated with our products."* — `ftmo.com/en/faq/are-the-fees-recurrent/`
- **Refund, 2-Step:** *"the paid fee is refunded with your first Reward withdrawal."* Homepage
  table: "Refund — Yes 100%".
- **Refund, 1-Step:** *"the paid fee is not refunded."* Comparison table: "Refund — –".
- **CONTRADICTION, recorded as required.** The contract says the opposite of the marketing.
  T&C cl. 3.12: *"Unless expressly agreed otherwise, once paid, you are not entitled to a refund of
  the FTMO Challenge Fee under any circumstances."* The reconciliation is almost certainly that the
  "refund" is paid by **FTMO Trading Global s.r.o.** as part of the first Reward, not by **FTMO
  Evaluation Global s.r.o.** as a refund of the fee — the two are separate legal entities under
  cl. 21 and cl. 6.1 — but **no page states this**, and the FTMO Account Terms that would settle it
  are not published. Both readings are logged; neither is adopted.
- **A cost that is not a fee.** T&C cl. 5.3.4: where a position's P/L is denominated in a currency
  other than the account's, *"a flat adjustment fee of 0.7% from the realised profit and loss at the
  moment the position is closed will be applied. The adjustment reduces a realised profit and
  increases a realised loss accordingly."* This is a per-trade cost term and belongs in any
  breakeven-cost calculation on this firm.
- The word **"from"** in "one-time refundable fee **from** €89" indicates the displayed price is a
  floor across the option set (platform, account type, currency). No Swing surcharge figure was
  observed. See §5 ambiguities.
- **Free Trial:** 14 days, free, *"As many Free Trials as you need"*.
  Sources: `ftmo.com/en/1-step-challenge/`, `ftmo.com/en/`.

**Field 3 — reset fee**

**NOT PUBLISHED — and the evidence is that no reset product exists on the CFD side.**
What was tried: `ftmo.com/en/faq/` category index (read in full, 60+ entries — no reset entry);
`ftmo.com/en/faq/are-the-fees-recurrent/`; the T&C PDF searched for "reset", "repeat", "retry"
(no fee clause of that kind); a site-restricted WebSearch for a reset/retry product on ftmo.com.
The historical **"free repeat"** (a free retry if a phase ended its Trading Period with a positive
balance) was withdrawn on 2023-07-13 together with the time limit: *"free repeats and 14-day
extensions are also no longer needed"* — `ftmo.com/en/blog/trade-without-any-time-limit-and-take-as-long-as-you-want-to-pass/`.
A failed Challenge is replaced by buying a new Order.
**Note the asymmetry:** FTMO's *futures* product explicitly has a **"Reset Fee"**
(`ftmo.com/en/futures/trading-objectives-and-rules/`). The CFD product does not.

**Field 4 — activation / funded-account fee**

**None.** *"No, we do not charge any additional or hidden fees."* — `ftmo.com/en/faq/are-the-fees-recurrent/`.
No activation fee, no monthly funded-account fee, no data fee. FTMO also states it charges no
commission on Reward withdrawals (`ftmo.com/en/faq/how-do-i-withdraw-my-profits/`).
Contrast with FTMO Futures, which is a **monthly subscription**.

---

### B — evaluation geometry

**Field 5 — profit target**

| variant | phase | target | $10k | $25k | $50k | $100k | $200k |
|---|---|---|---|---|---|---|---|
| 2-Step | FTMO Challenge | **10%** of Initial Simulated Capital | $1,000 | $2,500 | $5,000 | $10,000 | $20,000 |
| 2-Step | Verification | **5%** | $500 | $1,250 | $2,500 | $5,000 | $10,000 |
| 2-Step | FTMO Account | **none** | — | — | — | — | — |
| 1-Step | FTMO Challenge | **10%** | $1,000 | $2,500 | $5,000 | $10,000 | $20,000 |
| 1-Step | FTMO Account | **none** | — | — | — | — | — |

Verbatim: *"You will meet this objective once your account balance exceeds the Initial Simulated
Capital by the required Profit Target with all positions closed."* — note the target is scored on
**balance with everything closed**, while the loss limits are scored on open equity. The asymmetry
is deliberate and is stated on the page.
Source: `ftmo.com/en/trading-objectives/`.

**Field 6 — number of phases**

2-Step: **2** (FTMO Challenge Phase, Verification Phase). 1-Step: **1**.
T&C cl. 21 definition of "FTMO Challenge" states this in the contract, not only in marketing.
Sources: T&C PDF cl. 21; `ftmo.com/en/comparison-table/`.

**Field 7 — drawdown type: static / EOD trailing / intraday trailing**

| variant | type | FTMO's own word |
|---|---|---|
| **2-Step** (both phases and the funded FTMO Account) | **STATIC** | *"The Maximum Loss rule establishes a **static** limit (the Maximum Loss Limit)…"* |
| **1-Step** (Challenge and the funded FTMO Account) | **END-OF-DAY TRAILING** | *"The Maximum Loss rule establishes an **end-of-day trailing** limit (the Maximum Loss Limit)…"* |

Neither is intraday-trailing. The 1-Step limit is recomputed **once a day at 00:00 CE(S)T** off the
**highest account balance achieved at 00:00 CE(S)T of any preceding trading day**, i.e. it follows
midnight balances, not intraday equity peaks.
Comparison table states it flatly: "Max Loss type — Static | End-of-day-trailing".
Sources: `ftmo.com/en/trading-objectives/`; `ftmo.com/en/comparison-table/`.

**Field 8 — drawdown amount**

**10% of the Initial Simulated Capital, in both products, at every phase.**

| size | Maximum Loss Amount | 2-Step floor (fixed) | 1-Step Day-1 floor |
|---|---|---|---|
| $10,000 | $1,000 | $9,000 | $9,000 |
| $25,000 | $2,500 | $22,500 | $22,500 |
| $50,000 | $5,000 | $45,000 | $45,000 |
| $100,000 | $10,000 | $90,000 | $90,000 |
| $200,000 | $20,000 | $180,000 | $180,000 |

Source: `ftmo.com/en/trading-objectives/` (worked example given for $100,000 in both sections).

**Field 9 — drawdown basis: OPEN equity or CLOSED balance** *(hurdle P1)*

**OPEN EQUITY, including floating P/L, for both the Maximum Loss and the Maximum Daily Loss, in
both products, in every phase.** The wording is identical in all four places it appears:

> *"…establishes a limit (the Maximum Daily Loss Limit) below which your **account equity (i.e.,
> Balance + Open Positions P/L ± Swaps – Commissions)** cannot drop. If the equity drops below this
> limit, the rule is considered violated."*

> *"The Maximum Loss rule establishes a static limit / an end-of-day trailing limit (the Maximum
> Loss Limit) below which your **account equity (i.e., Balance + Open Positions P/L ± Swaps –
> Commissions)** cannot drop. If the equity drops below this limit, the rule is considered
> violated."*

**The mixed basis is the point and must not be collapsed.** The *test* is on open equity. The
*anchor* is on closed balance:

- Daily limit anchor = **the account balance recorded at 00:00 CE(S)T of the current day** (Day 1:
  the Initial Simulated Capital).
- 1-Step Maximum Loss anchor = **the highest account balance achieved at 00:00 CE(S)T of any
  preceding trading day**, or the Initial Simulated Capital if higher.
- 2-Step Maximum Loss anchor = the Initial Simulated Capital, fixed.

So floating profit **raises no limit** — it must be closed and survive to midnight — while floating
loss **can breach both**. For a path-variant study this is the operative asymmetry.
Source: `ftmo.com/en/trading-objectives/`.

**Field 10 — whether the floor locks, and at what level**

- **2-Step: nothing trails, so nothing locks.** The floor is a constant, `0.90 × Initial Simulated
  Capital`, for the whole life of the evaluation and of the funded account. Confirmed, not assumed —
  the page uses the word "static" and gives a single-value example with no daily recalculation.
- **1-Step: the floor trails and, as published, NEVER LOCKS.** Verbatim: *"The limit can only
  increase, but never decrease."* There is **no** statement of a ceiling, no lock at the Initial
  Simulated Capital, no lock at capital-plus-buffer. It is stated to apply *"to the FTMO Challenge:
  1-Step as well as the FTMO Account (1-Step)"*.
  The one thing that moves it **down** is a payout — see field 21.
- **The contrast that proves this is a real reading, not an omission.** FTMO's own futures product
  spells out a lock, in the same house style, on the same site:
  *"Once the Maximum Drawdown Limit reaches the Initial Simulated Capital, it locks permanently at
  that figure for the remaining duration of the Evaluation…"* — `ftmo.com/en/futures/trading-objectives-and-rules/`.
  FTMO knows how to write a lock clause. It did not write one for the 1-Step CFD product.

Source: `ftmo.com/en/trading-objectives/`; contrast source `ftmo.com/en/futures/trading-objectives-and-rules/`.

**Field 11 — daily loss limit: amount and basis**

| variant | Maximum Daily Loss Amount | basis of the test | anchor | reset |
|---|---|---|---|---|
| **2-Step** (both phases + funded) | **5%** of Initial Simulated Capital | **open equity** | account **balance** at 00:00 CE(S)T | daily, 00:00 CE(S)T |
| **1-Step** (Challenge + funded) | **3%** of Initial Simulated Capital | **open equity** | account **balance** at 00:00 CE(S)T | daily, 00:00 CE(S)T |
| **Premium: Supreme** | *"No Maximum Daily Loss limit"* | — | — | — |

Worked example given by FTMO for a $100,000 2-Step account: Day 1 limit $95,000; if the midnight
balance is $102,000 the Day 2 limit is $97,000; if it is $101,000 the Day 3 limit is $96,000. Note
the daily limit **falls again** when the balance falls — unlike the Maximum Loss, the daily anchor
is not a running maximum.
Sources: `ftmo.com/en/trading-objectives/`; `ftmo.com/en/premium-programme/`.

**Field 12 — minimum trading days**

| variant | requirement |
|---|---|
| 2-Step, FTMO Challenge phase | **4 Trading Days** |
| 2-Step, Verification phase | **4 Trading Days** |
| 2-Step, FTMO Account | **none** — *"There is no Minimum Trading Days rule on the subsequent FTMO Account (2-Step)."* |
| 1-Step | **none** — the rule is scoped to the 2-Step; the comparison table gives "Min Trading Days — 4 days / –" |

Definition: *"A Trading Day is defined as any day – measured from 00:00:00 to 23:59:59 CE(S)T –
during which at least one position is **opened**."* FTMO's own example makes the trap explicit: four
positions spread across three calendar days of *opening* is three Trading Days, not four.
Sources: `ftmo.com/en/trading-objectives/`; `ftmo.com/en/comparison-table/`.

**Field 13 — time limit / maximum days**

**Headline: none. "Trading Period — Unlimited", both products, both phases.** The 30/60-day limits
were removed on **2023-07-13, 11:00 CEST** (*"The 30 or 60 calendar days to complete the Evaluation
Process are gone."*), applying to accounts created after that moment; earlier orders stayed on the
old rules.

**But three time constraints survive in the contract, and a study that models FTMO as untimed will
be wrong:**

| T&C clause | constraint |
|---|---|
| **5.8.4** | You must open the first simulated trade within **30 calendar days** of a phase being made available, or access is **suspended**. Renewal can be requested within 6 months; otherwise the Agreement terminates *"without any right to a refund of the FTMO Challenge Fee."* |
| **13.2.3(a)** | FTMO may terminate for prolonged inactivity: *"you do not open at least one simulated trade on the Trading Platform for a period of thirty (30) consecutive calendar days"*. |
| **13.2.3(b)** | FTMO may terminate if *"you maintain a loss in the FTMO Challenge Account in the amount between 8% and 10% (included) of the Initial Simulated Capital for a period longer than thirty (30) calendar days"* — and trading designed to circumvent this, meaning *"simulated trades not consistent with your previous Simulated Trading pattern"*, is deemed to satisfy the condition anyway. |

**13.2.3(b) is a deep-drawdown timeout and it has no analogue in the marketing.** An account parked
between 90% and 92% of capital for a month can be closed. The absorbing region is therefore not
just `equity ≤ floor`; there is a second, time-dependent absorbing band immediately above it.
Sources: T&C PDF (LAST UPDATED 4 AUGUST 2026), cl. 5.8.4, 13.2.3;
`ftmo.com/en/blog/trade-without-any-time-limit-and-take-as-long-as-you-want-to-pass/`;
`ftmo.com/en/comparison-table/`.

**Field 14 — position-size cap and scaling rules**

- **No published maximum lot size.** Size is bounded by margin, i.e. by leverage.
- **Leverage:** Standard *"up to 1:100"* and *"cannot be increased"*; Swing *"up to 1:30"*.
  Source: `ftmo.com/en/faq/what-are-the-account-specifications/`.
- **Swing is 2-Step only** (comparison table: "Account type — Standard, Swing | Standard").
- **Aggregate capital cap: USD 400,000** of Initial Simulated Capital across all accounts held by
  you or affiliated parties (T&C 5.8.5(c), 6.3), raised only through Premium ($600,000 Prime,
  $1,000,000 Supreme) or the Scaling Plan ($2,000,000).
- **Discretionary size constraints exist and are contractual.** T&C cl. 7.5 defines "market standard
  risk management rules" *"by us at our discretion"* and gives as examples avoiding *"opening
  substantially larger position sizes compared to your other simulated trades"*, *"substantially
  smaller or larger number of positions"*, and *"cumulative exposure in a specific symbol or
  correlated symbols"*. Cl. 7.6 lets FTMO respond by reducing leverage (7.6.5), capping **"Risk per
  Trade Idea"** as a percentage of Initial Simulated Capital (7.6.6), capping volume in a symbol or
  asset class (7.6.7), or *"temporary or permanent consistency measures"* (7.6.9).
  **There is therefore an unpublished, discretionary position-size and consistency envelope on top
  of the published rules.** Its threshold is not stated anywhere.

**Contract scaling (contracts-per-size ladders, as futures firms publish) does not exist here** —
the product is CFD/FX, sized in lots against margin, not in contracts.

---

### C — funded-phase geometry

**Field 15 — funded-phase drawdown where it differs from the evaluation**

**It does not differ, in either product.** The trading-objectives page states for each rule that it
*"applies to the FTMO Challenge: 1-Step as well as the FTMO Account (1-Step)"* / *"applies to both
phases … as well as the subsequent FTMO Account (2-Step)"*. The funded differences are these four:

1. **No Profit Target** on either FTMO Account.
2. **No Minimum Trading Days** on the 2-Step FTMO Account.
3. **1-Step Maximum Loss resets on payout** — field 21.
4. **2-Step allows rollover**: *"you have the option to keep the Reward on your account (rollover)
   to build a larger balance and drawdown buffer."* Because the 2-Step floor is static at
   `0.90 × Initial Simulated Capital`, rolled-over profit adds buffer one-for-one and never lifts
   the floor. Minimum rollover €20/$20/£20/20 AUD/20 CAD/20 CHF/500 CZK.
5. **Premium: Supreme removes the Maximum Daily Loss entirely.**

Sources: `ftmo.com/en/trading-objectives/`; `ftmo.com/en/faq/how-do-i-withdraw-my-profits/`;
`ftmo.com/en/premium-programme/`.

**Field 16 — consistency rule: exact definition and threshold**

**Two published answers that do not agree, plus a contractual reservation. All three logged.**

**(a) The FAQ says there is no consistency rule beyond the Trading Objectives.** Verbatim, in full:

> *"Your trading consistency is primarily evaluated based on the Trading Objectives. To fully
> understand rules such as Minimum Trading Days or Best Day Rule, please visit our Trading
> Objectives page… Provided you maintain sustainable risk management practices, there are no
> additional consistency requirements for your trading."*
> — `ftmo.com/en/faq/do-you-have-any-consistency-rules/`

**(b) The Best Day Rule — 1-Step only, threshold 50%, and it is a SOFT gate.** Verbatim:

> *"To pass the FTMO Challenge: 1-Step or to be eligible for a Reward on an FTMO Account, the Best
> Day Rule requires that your **Best Day does not represent more than 50% of your Positive Days'
> Profit**. The Positive Days' Profit is the sum of closed profits and losses from all profitable
> trading days, with each new trading day beginning at 00:00 CE(S)T. The Best Day is a single day
> with the highest profit, where the profit is calculated from closed trades: at the end of the
> trading day (00:00 CE(S)T), or when other Trading Objectives are fulfilled…
> **Exceeding the Best Day limit is not treated as a rule breach.** However, you need to continue
> trading to generate additional profit until your Best Day (the most profitable day) represents
> 50% or less of your Positive Days' Profit on the account."*

FTMO's worked example: days of −$2,000, +$10,000, −$2,000, −$2,000, +$6,000 give Positive Days'
Profit = $16,000 and a Best Day share of 62.5%; to satisfy the rule with Day 2 still the best day,
Positive Days' Profit must reach **at least $20,000**. **Note the denominator**: it is the sum over
*profitable* days only — losing days do not enter it — so losses do not help you satisfy it, and
the gate is on **closed** P/L per calendar day boundary at 00:00 CE(S)T.

**No Best Day Rule applies to the 2-Step product** — comparison table: "Best Day Rule — – | 50%".

**(c) The contract reserves a discretionary consistency power.** T&C cl. 7.6.9 permits FTMO to
*"introduce any other additional measures we deem necessary, advisable or adequate in order to
ensure your Simulated Trading activity reflects long term sustainability and is not aimed at the
mere exploitation of our model **including temporary or permanent consistency measures**."*

**(a) and (c) are in direct tension** — "no additional consistency requirements" in the FAQ against
a contractual right to impose consistency measures at discretion. Both are recorded; neither is
adopted.

**Field 17 — profit split %**

| variant | base | maximum | route to the maximum |
|---|---|---|---|
| **1-Step** | **90%** from the start | 90% | none needed — *"FTMO Traders who qualified through the FTMO Challenge: 1-Step start with a 90% simulated profit split from the beginning, so there is no increase of the reward split upon entering the Premium Programme."* |
| **2-Step** | **80%** | **90%** | *"increases to 90% if Scaling Plan or Premium Programme conditions are met"* |

**Scaling Plan conditions (all four must hold):** *"Minimum of 4 months trading as an FTMO Trader
(or since the last scale-up)"*; *"At least 10% net simulated profit above the starting balance,
generated within the prior 4 months"*; *"At least 2 processed Rewards within that same 4-month
period"*; *"Positive account balance at the time of scale-up"*. Reward: a **25% balance boost** every
4 months, up to **$2,000,000** across all FTMO Accounts, and the 90% ratio (stated *"valid for
2-Step only"*).

**Premium Programme, Prime tier:** *"Active FTMO Account"*, *"No failed FTMO Accounts in the past 4
months"*, *"At least 4 successful reward withdrawals (4% or more)"* → 90% split, max allocation
$600,000, a free Challenge in FTMO Points, 10% Challenge discount. **Supreme tier:** *"Active
$400,000 Prime FTMO Account"*, *"Prime Trader for at least 3 months"*, *"Processed 3 additional
rewards with at least 4% profit per reward"* → **no Maximum Daily Loss limit**, immediate
withdrawals, max allocation $1M. No fee for the programme.
Sources: `ftmo.com/en/faq/how-do-i-withdraw-my-profits/`; `ftmo.com/en/reward-growth-and-scaling-plan/`;
`ftmo.com/en/premium-programme/`.

**Field 18 — first-payout eligibility**

> *"You can request a Reward claim in the Account MetriX on the **14th or any following day after the
> first placed trade** on the specific account. All open positions and pending orders must be
> closed. After you submit the withdrawal request, we will review your account and notify you
> within 1–2 business days."*

- Clock starts on the **first trade placed**, not on funding.
- **No minimum days-traded requirement** and **no profit threshold** beyond the transaction minimum
  in field 20.
- For the **1-Step**, the Best Day Rule is an additional gate: it must be satisfied *"to be eligible
  for a Reward on an FTMO Account"*.
- Premium Supreme gets *"Immediate reward withdrawals"*.

Source: `ftmo.com/en/faq/how-do-i-withdraw-my-profits/`.

**Field 19 — payout ladder / cap per withdrawal** *(the D379 §4 term)*

**THERE IS NO PAYOUT LADDER AND NO PERCENTAGE CAP.** This is a positive finding, searched for
directly, not an absence of searching. The only caps published are payment-rail caps:

| method | cap |
|---|---|
| bank wire transfer | **none stated** |
| Visa Direct / Mastercard Send | *"up to $20,000"* |
| Skrill | *"up to $3,000"* |
| cryptocurrencies | **none stated** |

*"FTMO does not charge any additional commissions for Reward withdrawals."*
There is no first-payout cap, no tiered release schedule, no consistency-gated payout percentage,
and no requirement to leave a buffer behind. On the **1-Step**, the opposite constraint applies —
you cannot leave profit behind at all (field 21).
Source: `ftmo.com/en/faq/how-do-i-withdraw-my-profits/`. The FTMO Account Terms, which would be the
authoritative source for this field, are **not published** (field 24).

**Field 20 — payout frequency and minimum**

- **Frequency:** on request, from the 14th day after the first trade *"or any following day"*. FTMO
  does not publish a fixed cycle length in the FAQ text; the 14-day figure is an eligibility date,
  not a stated period between payouts. Payment lands *"typically within 1–2 business days after the
  invoice is approved"*, after a *"1–2 business days"* review.
- **Minimum:** *"a minimum closed profit requirement of at least **$20 for bank wire** withdrawals
  and **$50 for cryptocurrency** withdrawals, to cover the cost of the transaction."*
- **Rollover minimum (2-Step only):** €20 / $20 / £20 / 20 AUD / 20 CAD / 20 CHF / 500 CZK.

Source: `ftmo.com/en/faq/how-do-i-withdraw-my-profits/`.

**Field 21 — does a payout reduce or reset the drawdown buffer?**

**This is the field where the two products diverge most sharply, and both answers are explicit.**

**1-Step — YES, a payout resets the account and knocks the trailing floor back down.** Verbatim:

> *"However, when a Reward is withdrawn and a new FTMO Account is provided, the Maximum Loss Limit
> fully resets, returning the first-day limit to **90% of the Initial Simulated Capital**."*
> — `ftmo.com/en/trading-objectives/`

and

> *"FTMO Challenge: 1-Step: You receive 90% of the profit. **Rewards cannot be left on the account to
> grow the balance.**"* — `ftmo.com/en/faq/how-do-i-withdraw-my-profits/`

So the 1-Step funded account is a **repeating cycle**: trade up, withdraw, receive a *new* account
at the Initial Simulated Capital with the floor back at 90% of it. Accumulated buffer is not
carried. The trailing floor's monotone rise is reset at every payout — the only downward move it
ever makes.

**2-Step — NO.** The static floor sits at `0.90 × Initial Simulated Capital` and does not move at
all, in either direction, ever. A withdrawal lowers the balance toward that fixed floor, so it
**consumes** buffer; a rollover raises the balance away from it, so it **adds** buffer. FTMO says so:
rollover is *"to build a larger balance and drawdown buffer."*

**Field 22 — hard breach vs soft breach**

**Hard — ends the phase / the account immediately:**

| trigger | wording |
|---|---|
| equity below the **Maximum Loss Limit** | *"If the equity drops below this limit, the rule is considered violated."* |
| equity below the **Maximum Daily Loss Limit** | same wording |
| any Trading Objective unmet at evaluation | T&C 5.8.8: *"If any of the conditions under Clause 5.8.5 is breached we will evaluate the phase of the FTMO Challenge, and therefore the whole FTMO Challenge, as unsuccessful."* |
| exceeding the **USD 400,000** aggregate capital cap | T&C 5.8.5(c) — a pass condition, not a trading rule |

On a funded account, *"continuous compliance with applicable Trading Objectives is required at all
times."*

**Soft — does not end anything; you keep trading until it is satisfied:**

| trigger | wording |
|---|---|
| **Best Day Rule** (1-Step) | *"Exceeding the Best Day limit is **not treated as a rule breach**. However, you need to continue trading to generate additional profit until…"* |
| **Minimum Trading Days** (2-Step) | *"you will have to continue trading one more day."* |

**Discretionary — a menu, not a switch.** For Forbidden Trading Practices or breach of the Risk
Management Rules, T&C 7.6 permits any of: treating it as *"a failure to meet the Trading
Objectives"* (7.6.1); cancelling, consolidating, reclassifying or **removing trades from the
history** (7.6.2); immediate cancellation of all Services and termination (7.6.3); informing FTMO
Trading, who may cancel *"all of your FTMO Accounts or rewards thereunder"* (7.6.4); cutting
leverage (7.6.5); imposing Risk-per-Trade-Idea and volume caps (7.6.6–7.6.7); and consistency
measures (7.6.9). Cl. 7.7: *"we are not required to notify you before taking such action."*
Cl. 7.9: no compensation, no refund, and possible permanent exclusion.

**Termination triggers (T&C 13.2)** additionally include rejecting a Modification (13.2.1(a) — and
15.1 gives 7 days' notice of any change to the Terms, with rejection terminating all Agreements),
duplicate registration, non-personal use, the two 30-day inactivity/deep-loss rules of 13.2.3, and
either party's 5-business-day no-cause notice (13.2.4).

---

### D — disclosure

**Field 23 — published pass-rate / payout statistics**

**FTMO publishes no pass rate, no funded rate and no paid-out rate.** Searched: an ftmo.com-restricted
WebSearch for published pass-rate statistics; the "year in numbers" series; the payouts blog; the
homepage; the 1-Step product page; the leaderboard. **Negative result, logged.** The 2021 "year in
numbers" post is the closest FTMO has come to a statistical disclosure and it gives account counts
and payout totals with no pass denominator.

**What FTMO does publish, in full:**

*Site-wide, on nearly every page (2026-09-08):* **4.5M+ customers worldwide**; **$650M+ paid in
rewards worldwide**; **140+ countries served**; 300+ team members; 21 languages; 4.8/5 Trustpilot;
operating since 2015.

*Per-size average reward, on the 2-Step pricing block:*

| account | "Avg. Reward" |
|---|---|
| $10,000 | €680 |
| $25,000 | €1,431 |
| $50,000 | €2,805 |
| $100,000 | €5,957 |
| $200,000 | €12,234 |

*On the 1-Step product page:* **biggest 1-Step reward $20,765**; **average 1-Step reward $3,336.61**;
**shortest time to pass: 2 days**; most traders: Great Britain.

*Payouts blog (published 2024-02-09, updated 2025-11-04):* total payouts 2020 **$3,404,178** → 2023
**$75,170,210**; monthly average 2020 $851,044 → 2023 **$5,782,324**; best month January 2024
**$9,643,269**; daily average 2020 $39,584 → 2023 $209,973, exceeding $300,000 in early 2024;
payouts per month 305 (2020) → **1,713** (2023) → **2,753** (January 2024); highest single day 196
payouts totalling $628,317 on 2 January 2024; **"more than 138,000 FTMO Accounts"** created; largest
single payout **$964,980.55**.

*"The year 2021 in numbers" (published 2022-01-06):* **more than 960,000 trading accounts** created
through the platform in 2021; **more than 90,000,000 trades**; **$29,000,000** paid out in 2021;
**average $4,685** paid per trading period; **117.9 trades** per trading period on average; Normal
account type **~87%** of orders, Swing **>11%**.

**Do not build a pass rate out of these.** "138,000 FTMO Accounts" (cumulative, to early 2024) and
"4.5M+ customers" (cumulative, to 2026) are different denominators measured at different dates, and
"customers" includes Free Trial users and the shop. The ratio is not a pass rate and is not reported
here as one. A genuine pass rate for FTMO is **NOT PUBLISHED**; third-party estimates belong to
lane 07, not to this cell.

**Field 24 — terms version / last-updated date, and the URL each cell came from**

| document | last updated | URL |
|---|---|---|
| **FTMO Challenge Terms and Conditions (PDF)** | **"LAST UPDATED ON 4 AUGUST 2026"** — stated on page 1 | `cdn.ftmo.com/docs%2Fterms-and-conditions%2Ff8d5ca5086964c86a6ee2a77f20bdbd7` (linked from `ftmo.com/en/terms-and-conditions/`) |
| Trading Objectives | `dateModified` **2026-05-13** | `ftmo.com/en/trading-objectives/` |
| How It Works | `dateModified` **2026-07-23** | `ftmo.com/en/how-it-works/` |
| Reward Growth and Scaling Plan | `dateModified` **2026-08-13** | `ftmo.com/en/reward-growth-and-scaling-plan/` |
| Premium Programme | `dateModified` **2026-06-10** | `ftmo.com/en/premium-programme/` |
| 1-Step launch announcement | published **2026-02-06** | `ftmo.com/en/blog/introducing-the-1-step-ftmo-challenge/` |
| Time-limit removal | published **2023-07-13** | `ftmo.com/en/blog/trade-without-any-time-limit-and-take-as-long-as-you-want-to-pass/` |
| Payout statistics | published **2024-02-09**, updated **2025-11-04** | `ftmo.com/en/blog/we-pay-millions-in-payouts-to-our-ftmo-traders/` |
| Pricing, comparison table, FAQ pages | **no date published** | homepage, `/en/comparison-table/`, `/en/faq/*` |
| **FTMO Account Terms and Conditions** (the funded-phase contract) | — | **NOT PUBLISHED.** *"If you are interested in a sample of the contract, please contact us at support@ftmo.com."* — `ftmo.com/en/faq/what-is-the-legal-relationship-between-an-ftmo-trader-and-ftmo-after-signing-the-ftmo-account-agreement/` |

The undated pages are the ones carrying fields 1, 2, 6, 12, 17–20 and 23. Note also T&C cl. 15.1:
FTMO may amend the Terms on **7 calendar days' notice**, and cl. 21 defines the Trading Objectives
themselves as *"set out on the Website and may be updated from time to time"* — i.e. the geometry is
amendable outside the contract's own amendment procedure.

---

## 3. Two things about FTMO that no futures-firm row in this grid will have

**The counterparty is split in two, and the funded side is the undocumented one.**
`FTMO Evaluation Global s.r.o.` (ID 092 13 651) sells the Challenge under the public Terms.
`FTMO Trading Global s.r.o.` (ID 094 18 415) provides the FTMO Account under the unpublished FTMO
Account Terms. Cl. 6.1: passing *"does not guarantee your acceptance into the FTMO Trader
Program. We are not responsible for you not being admitted… for any reason."* The barrier problem
therefore has a step in it that is not a barrier at all: an unpriced admission gate between the
evaluation and the payoff.

**"Simulated" is the contractual frame, not a disclaimer.** Cl. 5.3.1–5.3.3: the trades are
*"purely fictional"*, the capital *"has no monetary value"*, and *"you will not be paid any
remuneration or profits based on the results of your Simulated Trading in the Evaluation Process."*
Cl. 2.1: *"None of the Services are subject to laws regulating the financial sector"*. The Reward is
consideration *"for the data you generate"* (cl. 6.1). This bears on lane 06 rather than on
geometry, but it is the frame the geometry sits inside.

---

## 4. How this geometry differs from the US futures firms

*The deliverable that justifies the lane. FTMO's own futures product is used as the within-firm
control wherever possible, so the contrast rests on primary sources I read rather than on lanes
01–04's results.*

| axis | FTMO CFD (this lane) | US futures convention (incl. **FTMO's own futures product**) |
|---|---|---|
| **Threshold denomination** | **Percentage of Initial Simulated Capital** — 10% max loss, 5%/3% daily. Scale-free: the $10k and the $200k account have *identical* geometry in return space. | **Dollar amounts** per account size ($2,000 on $50k, $3,500 on $100k, $5,000 on $150k for FTMO Futures Growth) — so the *percentage* barrier differs by size (4.0%, 3.5%, 3.3%) and geometry is not scale-free. |
| **Drawdown type** | **2-Step: static.** **1-Step: end-of-day trailing.** The firm sells both at once. | End-of-day trailing (FTMO Futures), with intraday-trailing variants elsewhere in the sector. |
| **Does the trailing floor lock?** | **1-Step: no lock published.** *"The limit can only increase, but never decrease"* — and nothing more. 2-Step: nothing trails. | **Yes, and explicitly:** *"Once the Maximum Drawdown Limit reaches the Initial Simulated Capital, it locks permanently at that figure…"* |
| **Basis of the test** | **Open equity, floating P/L included, for both the max loss and the daily loss, verbatim and in every phase.** | Also equity for FTMO Futures (*"Balance + Open Positions P&L – Commissions"*) — but the *anchor* is the close of the trading day, and the trading day is defined 18:00 ET → 16:10 ET, not 00:00 CE(S)T. |
| **Anchor for the daily limit** | Account **balance at 00:00 CE(S)T**; falls when the balance falls (not a running maximum). | Session-close balance on a US futures day boundary. |
| **Phases** | **Two** (10% then 5%) on the flagship; **one** on the 1-Step. Verification is a *second* target on a *fresh* account. | One evaluation phase, then sim-funded. |
| **Time** | Unlimited trading period — **but** 30 days to activate, 30 days' inactivity, and a **30-day timeout while sitting at an 8–10% loss** (T&C 13.2.3(b)). | Monthly subscription: the clock is the billing cycle, and a breach means *"wait for the next monthly subscription"*. |
| **Cost shape** | **One-time fee** (€79–€1,080), refunded on the 2-Step with the first payout, never on the 1-Step. **No reset product at all.** | **Recurring monthly subscription** plus an explicit **Reset Fee** that also unlocks the drawdown limit mid-evaluation. |
| **Consistency** | None on the 2-Step. **Best Day Rule 50%** on the 1-Step — a soft gate on passing *and* on payout eligibility, computed on closed daily P/L over profitable days only. | Consistency rules are a sector staple on the futures side. |
| **Payout ladder** | **None.** No percentage cap, no tiered release, no first-payout limit. Only payment-rail caps. | Ladders are precisely the D379 §4 term the futures lanes exist to record. |
| **Payout ↔ drawdown reference** | **1-Step: a payout resets the whole account** — new account, floor back to 90% of Initial Simulated Capital. **2-Step: floor never moves;** withdrawal consumes buffer, rollover adds it. | Payout typically drains toward a fixed or locked floor without re-issuing the account. |
| **Position sizing** | Leverage-bounded (1:100 Standard, 1:30 Swing). No lot cap. Discretionary Risk-per-Trade-Idea caps in the contract. | Contract-count ladders per account size, published as a table. |
| **Aggregate exposure** | **USD 400,000** across all accounts, contractually, unless Premium/Scaling lifts it. | Per-firm account-count limits. |

**The three conclusions this lane exists to license:**

1. **"Static drawdown is the FX convention" is false as of February 2026.** FTMO — the canonical FX
   prop firm — now sells an end-of-day trailing product alongside its static one. Any grid
   conclusion of the form *"trailing geometry is a futures artefact"* is refuted by a single firm's
   own catalogue.

2. **Percentage-vs-dollar denomination is the difference that actually survives.** It is the one
   axis on which FTMO's CFD product and every futures product in this grid, *including FTMO's own*,
   differ without exception. It has a direct modelling consequence: on FTMO CFD, account size is a
   pure multiplier and one zero-edge ruin simulation covers all five sizes; on the futures side,
   each size is a different barrier problem in return space and needs its own baseline. **For
   Stage 0, that is a five-to-one reduction in the number of distinct geometries to simulate on the
   FTMO side, and it does not transfer to the futures lanes.**

3. **The lock is the geometry parameter to interrogate, not the trail.** Static (2-Step), trailing-
   that-locks (FTMO Futures), and trailing-that-never-locks (1-Step) are three genuinely different
   absorbing-boundary problems, and this firm sells all three. The 1-Step is the tightest of the
   three and is marketed as the easier product. If Stage 0 runs one baseline per distinct geometry,
   this lane alone supplies three, and the never-locking variant is one no futures lane will produce.

---

## 5. Ambiguities, contradictions and things I could not settle

1. **The refund contradiction (field 2).** Marketing: *"Refund — Yes 100%"*, *"the paid fee is
   refunded with your first Reward withdrawal."* Contract cl. 3.12: *"once paid, you are not
   entitled to a refund of the FTMO Challenge Fee under any circumstances."* The two-entity
   structure is the likely reconciliation, but no page says so. **Both recorded, neither adopted.**
2. **The consistency contradiction (field 16).** FAQ: *"there are no additional consistency
   requirements for your trading."* Contract cl. 7.6.9: *"including temporary or permanent
   consistency measures."* Threshold for the latter: unstated.
3. **Whether the 1-Step Maximum Loss Limit locks anywhere.** The page says only that it can never
   decrease. It gives no lock, and FTMO writes explicit lock language for its futures product, so
   the natural reading is that it does not lock. **But this is a reading, not a quotation, and it is
   the single most consequential unresolved cell in the lane.** It should be settled by asking FTMO
   support directly, or by observing an account whose trailing limit passes the Initial Simulated
   Capital. Do not model it either way without settling it.
4. **The FTMO Account Terms and Conditions are not published.** Fields 15 and 17–22 therefore rest
   on FAQ and marketing pages. A "sample of the contract" is available from support@ftmo.com; I did
   not request one, since that requires contact and this lane is read-only.
5. **The word "from" in the pricing.** "One-time refundable fee **from** €89" implies the displayed
   price is a floor across the option set. **No Swing-account or platform surcharge figure was
   found** on any page. The checkout at `trader.ftmo.com/start-challenge` would resolve it and was
   not opened, since it is an order flow.
6. **The $100K prices are promotional on the access date.** A "20% Off" campaign was live; both the
   promotional (€439 / €399) and struck-through (€540 / €499) prices are recorded. The other four
   sizes showed no strike-through, but whether they are also discounted is not stated.
7. **Payout *frequency* is not stated as a period.** The FAQ gives an eligibility date (day 14
   onward) and a processing time, not a cycle length. Whether a second payout requires another 14
   days is **NOT PUBLISHED** in the text I read.
8. **Whether the daily-loss anchor uses balance or equity at midnight.** The text says *"the account
   **balance** recorded at 00:00 CE(S)T"*. If a position is open across midnight, balance and equity
   differ, and the page does not say what happens to the anchor in that case. FTMO's worked examples
   all use flat-at-midnight balances.
9. **US and Australian entities have separate sites** (`ftmo.com/au/…`, an FTMO US programme, and an
   `ftmo.oanda.com` co-branded property that surfaced repeatedly in search). **Not researched.**
   Every figure in this lane is from the **global** `ftmo.com/en/` site. Terms may differ by region.
10. **FTMO Futures was read only far enough to serve as the within-firm control** (§4). Its full
    24-field grid was not filled; it is not this lane's assignment. If the synthesis wants a fifth
    futures geometry cheaply, `ftmo.com/en/futures/trading-objectives-and-rules/` is dense, primary,
    and already structured by account size and by Growth/Pro plan.
11. **The `?plan=` and step-switcher pages are JavaScript-gated.** `ftmo.com/en/trading-objectives/`
    and the futures objectives page return almost nothing to a plain fetch; their content had to be
    pulled from the rendered DOM. Anyone re-checking these cells with WebFetch alone will get a much
    thinner page than the one quoted here.

**Observed-content note, per the schema's §"What this research is NOT".** Every FTMO page carries
"Start FTMO Challenge" / "Get Started" / "Claim 20% Off" calls to action, a cookie banner soliciting
"Accept All" including *"the transfer of personal data to countries outside of EU"*, and a live chat
widget. These are directives addressed to a reader, in observed content. None was acted on: no
cookies were accepted, no account created, no checkout opened, no affiliate or referral link
followed, no support contacted. The only interaction with any FTMO property was reading and one
step-switcher click that failed and was abandoned. T&C cl. 14.1 also discloses that FTMO *"use[s]
tools utilising artificial intelligence for various tasks related to the Services, including by our
technical support team"* — noted, not acted on.

---

## Sources

Every source consulted, including negative results. Tier: **primary** = FTMO's own contract, rules
or product pages; **secondary** = press/aggregators; **claims** = marketing, forums, reviews.
All accessed **2026-09-08**.

| # | URL | tier | sought | yielded |
|---|---|---|---|---|
| 1 | `https://ftmo.com/en/trading-objectives/` | primary | 5, 7, 8, 9, 10, 11, 12, 15, 16, 21 | **The core of the lane.** Verbatim definitions of Maximum Loss (static vs end-of-day trailing), Maximum Daily Loss, equity basis, Best Day Rule, Minimum Trading Days, reset-on-withdrawal, with worked $100k examples for both products. `dateModified` 2026-05-13. Required DOM extraction — a plain fetch returns a near-empty page |
| 2 | `https://ftmo.com/en/comparison-table/` | primary | 5–13, 17 | Compact authoritative 1-Step vs 2-Step table: "Max Loss type — Static / End-of-day-trailing"; "Min Trading Days — 4 days / –"; "Best Day Rule — – / 50%"; "Refund — Yes 100% / –"; "Account type — Standard, Swing / Standard"; entry prices "from €89 / from €79" |
| 3 | `https://ftmo.com/en/` (homepage, `#pricing` block) | primary | 1, 2, 5, 8, 11, 12, 13, 17, 23 | Full 2-Step price ladder €89/€250/€345/€439(€540)/€1,080, per-size "Avg. Reward" figures, "Trading Period — Unlimited", site-wide statistics (4.5M+ customers, $650M+ paid). JS-rendered; needed the browser |
| 4 | `https://ftmo.com/en/1-step-challenge/` | primary | 1, 2, 5, 8, 11, 13, 16, 17, 23 | Full 1-Step price ladder €79/€199/€319/€399(€499)/€999, all "non-refundable"; objectives summary; **1-Step statistics: biggest reward $20,765, average $3,336.61, shortest time to pass 2 days**; 14-day Free Trial |
| 5 | `https://cdn.ftmo.com/docs%2Fterms-and-conditions%2Ff8d5ca5086964c86a6ee2a77f20bdbd7` (FTMO Challenge Terms and Conditions PDF, "LAST UPDATED ON 4 AUGUST 2026") — **text extraction retained as evidence at [`data/ftmo_challenge_terms_2026-08-04.txt`](../../../data/ftmo_challenge_terms_2026-08-04.txt)**, since every clause quoted above comes from it and the CDN URL is a content hash that will change on the next amendment | primary | 2, 3, 6, 13, 14, 22, 24 | **The second most valuable source.** cl. 3.12 no-refund (contradicts marketing); cl. 5.3.4 the 0.7% currency adjustment; cl. 5.8.4 30-day activation; cl. 5.8.5(c)/6.3 USD 400,000 aggregate cap; cl. 5.8.8 breach = phase unsuccessful; cl. 6.1 the two-entity split and the discretionary admission gate; cl. 7.5–7.9 Risk Management Rules and the 7.6 discretionary menu incl. consistency measures; cl. 13.2.3(b) the 8–10%-loss 30-day timeout; cl. 15.1 seven days' notice to amend. Binary PDF — WebFetch could not read it; extracted with `pdftotext` |
| 6 | `https://ftmo.com/en/faq/how-do-i-withdraw-my-profits/` | primary | 17, 18, 19, 20, 21 | Verbatim payout terms: day-14 eligibility, 1–2 business day review, rail caps ($20,000 Visa Direct / $3,000 Skrill), $20 wire / $50 crypto minimums, 90% vs 80%→90%, **"Rewards cannot be left on the account"** (1-Step) vs rollover (2-Step) |
| 7 | `https://ftmo.com/en/faq/do-you-have-any-consistency-rules/` | primary | 16 | Verbatim: *"there are no additional consistency requirements for your trading"* — the half of the field-16 contradiction that the FAQ supplies |
| 8 | `https://ftmo.com/en/faq/are-the-fees-recurrent/` | primary | 2, 4 | Verbatim one-time-fee statement; 2-Step refunded with first Reward, 1-Step not refunded; no activation or monthly fee |
| 9 | `https://ftmo.com/en/faq/what-are-the-account-specifications/` | primary | 14 | Leverage "up to 1:100" Standard (*"cannot be increased"*), "up to 1:30" Swing. **No lot cap, no commission schedule, no margin table** — the page defers to the platform's own instrument specification |
| 10 | `https://ftmo.com/en/faq/what-is-the-legal-relationship-between-an-ftmo-trader-and-ftmo-after-signing-the-ftmo-account-agreement/` | primary | 15, 17–22, 24 | **The FTMO Account Agreement is not published**: *"If you are interested in a sample of the contract, please contact us at support@ftmo.com."* The disclosure gap that caps the funded-phase cells |
| 11 | `https://ftmo.com/en/reward-growth-and-scaling-plan/` | primary | 1, 17 | Scaling Plan: four conditions verbatim, +25% per 4 months, $2,000,000 cap, 90% ratio *"valid for 2-Step only"*. `dateModified` 2026-08-13 |
| 12 | `https://ftmo.com/en/premium-programme/` | primary | 1, 11, 15, 17, 18 | Prime and Supreme entry conditions and benefits; $600,000 / $1,000,000 allocations; **Supreme: "No Maximum Daily Loss limit"**; immediate withdrawals; no fee. `dateModified` 2026-06-10 |
| 13 | `https://ftmo.com/en/how-it-works/` | primary | 1, 5, 8, 11 | Account sizes verbatim; 2-Step targets and limits; *"Receive a 100% refund of your initial fee with your first reward withdrawal"*. `dateModified` 2026-07-23. **No fee figures on this page** |
| 14 | `https://ftmo.com/en/blog/introducing-the-1-step-ftmo-challenge/` | primary | 6, 7, 10, 13, 17 | 1-Step launch, **published 2026-02-06** — dates the arrival of EOD trailing into the CFD product. Confirms 10% target, 3% MDL, 10% EOD-trailing ML, 90% split, unlimited time, Best Day Rule |
| 15 | `https://ftmo.com/en/blog/trade-without-any-time-limit-and-take-as-long-as-you-want-to-pass/` | primary | 3, 13 | **Published 2023-07-13.** *"The 30 or 60 calendar days to complete the Evaluation Process are gone."* Applies to accounts created after 11:00 CEST that day; **free repeats and 14-day extensions withdrawn at the same time**; a "freeze" can be requested for planned inactivity |
| 16 | `https://ftmo.com/en/blog/we-pay-millions-in-payouts-to-our-ftmo-traders/` | primary | 23 | Published 2024-02-09, updated 2025-11-04. Payout totals by year, payout counts, **">138,000 FTMO Accounts"**, largest single payout $964,980.55. **No pass rate** |
| 17 | `https://ftmo.com/en/blog/year-2021-in-numbers/` | primary | 23 | Published 2022-01-06. 960,000+ accounts created in 2021, 90M+ trades, $29M paid, $4,685 average per trading period, 117.9 trades per period, Normal ~87% / Swing >11% of orders. **Explicitly no pass rate** |
| 18 | `https://ftmo.com/en/futures/trading-objectives-and-rules/` | primary | §4 within-firm control | **The lock clause**: *"Once the Maximum Drawdown Limit reaches the Initial Simulated Capital, it locks permanently at that figure…"*; dollar-denominated EOD trailing ($2,000/$3,500/$5,000 on $50k/$100k/$150k); Reset Fee; monthly subscription; 18:00–16:10 ET trading day. The evidence that FTMO's geometry tracks the product, not the firm |
| 19 | `https://ftmo.com/en/leaderboard/` | primary | 1, 23 | Corroborates live $400,000 and $600,000 account sizes. Shows only the top 3 publicly; the rest is gated to registered users. No aggregate statistics |
| 20 | `https://ftmo.com/en/terms-and-conditions/` | primary | 22, 24 | Navigation only — the page is a shell linking the PDF (source 5). Yielded the PDF URL and nothing else |
| 21 | `https://ftmo.com/en/terms-and-policies/` | primary | 15, 17–22 | **NOTHING for the funded phase.** Lists CFD Terms, CFD Trading Objectives, CFD Forbidden Trading Practices, and the three futures equivalents. **No FTMO Account Terms and Conditions is linked anywhere** — this is what establishes field 24's NOT PUBLISHED |
| 22 | `https://ftmo.com/en/pricing/` | primary | 1, 2 | **NOTHING — HTTP 404.** No such path; pricing lives in the homepage anchor `#pricing` |
| 23 | `https://ftmo.com/en/faq/what-will-be-the-size-of-my-ftmo-account/` | primary | 1, 14 | **NOTHING — "Page not found".** The FAQ index lists this title but the guessed slug is wrong; the aggregate cap came from the T&C instead |
| 24 | `https://ftmo.com/en/faq/` (category index, read via the sidebar on source 6) | primary | 3 | **Negative result, deliberate.** Full 60+ entry FAQ index read. There is **no reset-fee entry, no retry entry, no free-repeat entry.** Entries do exist for Trading Objectives, consistency, Swing, Premium, fees, withdrawals — all followed. This is the basis for field 3's NOT PUBLISHED |
| 25 | WebSearch: *FTMO Challenge rules maximum loss maximum daily loss trading objectives* | — | 7, 8, 9, 11 | Located sources 1 and 2. The result text itself was claims-tier and was not used for any cell |
| 26 | WebSearch: *FTMO pricing account sizes fee … refund* | — | 1, 2 | **Nothing usable.** Returned only affiliate-heavy aggregators (jptradingcapital, brokeranalysis, tradingtoolshub, luxalgo, aquafunded, thepayoutreport). Prices quoted there matched what the firm's own page later showed, but **no cell was filled from them** |
| 27 | WebSearch: *ftmo.com scaling plan profit split 90% withdrawal rules payout* | — | 17, 19, 20 | Located sources 6 and 11 |
| 28 | WebSearch: *FTMO leverage 1:100 swing account maximum lot size* | — | 14 | Located source 9. Third-party claims of a 1-lot-per-$10k rule were **not corroborated by any FTMO page and are not recorded** |
| 29 | WebSearch: *FTMO "trading period" unlimited no time limit removed minimum trading days 2026* | — | 12, 13 | Located source 15 |
| 30 | WebSearch: *ftmo.com faq what happens if I break a rule / breach* | — | 22 | Located `forbidden-trading-practices`; the substantive answer came from the T&C instead |
| 31 | WebSearch: *FTMO "free repeat" FAQ conditions positive balance* | — | 3 | Confirmed via source 15 that free repeats were **withdrawn in July 2023**. Negative result for a current reset product |
| 32 | WebSearch (site-restricted to ftmo.com): *FTMO account reset fee funded account failed* | — | 3 | **NOTHING.** No FTMO page offers a CFD reset product |
| 33 | WebSearch (site-restricted to ftmo.com): *FTMO Premium Programme conditions 90% profit split* | — | 17 | Located source 12 |
| 34 | WebSearch (site-restricted to ftmo.com): *FTMO published percentage of traders who pass* | — | 23 | **NOTHING. FTMO publishes no pass rate.** The only percentage surfaced was a trader's remark in a blog interview, which is not a firm statistic and is not recorded |
| 35 | WebSearch (site-restricted to ftmo.com): *FTMO "in numbers" 2024 OR 2025 statistics* | — | 23 | **Partial negative.** No "year in numbers" post exists after 2021; located source 16 instead |
| 36 | WebSearch: *FTMO pass rate statistics … 2026* (open web) | — | 23 | **Deliberately not used.** Returned only third-party estimates (4–15%, mutually inconsistent, all affiliate-adjacent). **Belongs to lane 07, not to field 23.** Logged so lane 07 knows this ground is already walked |
| 37 | WebSearch: *"ftmo.com" terms and conditions client agreement* | — | 22, 24 | Located sources 20 and 21, and surfaced the regional `ftmo.com/au/terms-conditions/` — **not researched**, see ambiguity 9 |
