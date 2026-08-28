# 05 — Prop-Firm Reality Check

**Question:** does the prop-firm route actually support the stated goal — replace a full-time income in
roughly two years via prop payouts of about $50,000/yr, plus retained profit to grow the account?

**Date:** 2026-08-28. **Type:** desk research, external sources only. No backtests were run.

**Short answer:** No, not as the programme currently understands it. The binding constraint is not skill
and not the profit split — it is the **trailing drawdown**, which is roughly 4–5% of account notional and
is a ratcheting absorbing barrier. Our measured book has a −10% max drawdown. It would be liquidated.
Sized down to fit, the income per account collapses to a few hundred to a few thousand dollars per year.
Separately, **every major futures prop firm auto-flattens at the close**, which deletes the +8.59%/yr
overnight drift that both of our swing arms depend on.

Everything below is the working.

---

## 0. Reading guide — the three things that decide the answer

If you read nothing else:

1. **Trailing drawdown is ~5% of notional and it ratchets.** Apex trails on *unrealized* intraday equity
   (worst case). Topstep trails on *end-of-day closed* balance but is *breached* on unrealized P&L. Both
   are absorbing: for a process with positive drift, a fixed trailing barrier is hit with probability 1
   given enough time. The only question is how much you extract first, and the answer is computed in §3.
2. **No overnight holds anywhere in futures prop.** Topstep flattens at 3:10pm CT, Apex at 4:59pm ET,
   MyFundedFutures at 4:10pm ET. This is not negotiable and not plan-dependent.
3. **Automation is banned at the funded stage at two of the three largest firms.** Apex bans it on
   Performance Accounts (allowed in evaluation only — i.e. you can pass with an algo and then must stop
   using it). Take Profit Trader bans EAs at every stage. Topstep permits it in sim but bans API
   automation on the Live account. MyFundedFutures permits it, with a 200 trades/day HFT ceiling.

---

## 1. The three categories — do not conflate them

These are three unrelated businesses that share a word.

### 1a. Futures "prop" firms (evaluation / funded-account model)

Topstep, Apex Trader Funding, Take Profit Trader, MyFundedFutures, Tradeify, Bulenox, TradeDay,
Alpha Futures, Elite Trader Funding, FundedNext Futures.

**What they actually are:** you pay a fee for access to a *simulated* futures account. You trade sim.
If your sim P&L clears a target without touching a drawdown floor, you are given a second, larger sim
account. If that sim account's P&L stays positive under further rules, the firm pays you real money out
of its own revenue. Topstep is explicit about this in its own copy: the Combine and Express Funded
Accounts are *"realistic simulations of trading under actual market conditions"* and *"Topstep pays you
real money based on your simulated trading results"*
([Topstep](https://www.topstep.com/)). Only Topstep's third-stage *Live Funded Account* routes orders to
a real exchange, and access to it is gated behind Express performance
([Topstep Live Funded Account Rules](https://www.topstep.com/live-funded-account-rules)).

This is the category the goal implicitly assumes, so it gets most of this document.

### 1b. Retail CFD / forex prop firms

FTMO, FundedNext, The5ers, Funding Pips, E8, City Traders Imperium, Phidias, GoatFundedTrader, and the
long tail. Same evaluation model, but the underlying is CFDs, and the counterparty is usually an
offshore broker rather than a US futures FCM. This is the category that produced the My Forex Funds
litigation (§4) and the ~80–100 firm die-off of 2024–25 (§5). **Not relevant to us** except as the source
of the only large-sample outcome statistics that exist (§3a), and as the reason regulators are circling.

### 1c. Genuine proprietary trading firms

Two sub-species, also unrelated to each other:

- **Market-makers / quant shops** — Jane Street, Optiver, DRW, SIG, Jump, IMC, Tower Research, Old
  Mission. These *hire* you, pay a salary, and trade their own balance sheet. They do not sell
  evaluations. Entry is via campus recruiting or a demonstrable institutional track record. Not a route
  from a home research programme.
- **Licensed retail trading arcades** — T3 Trading Group (SEC-registered broker-dealer, requires SIE and
  Series 57, typically a first-loss capital contribution), Maverick Trading (remote, ~$5,000 capital bond
  plus a training programme, no challenge fee), SMB Capital. These are real but require licensing and/or
  posted capital, and splits are often worse (SMB ~50%) than the evaluation firms' headline splits
  ([Maverick Trading listing](https://weworkremotely.com/remote-jobs/maverick-trading-remote-stock-options-trader-funded-capital-program)).

The rest of this document is about 1a, with 1c noted in the verdict as the only structurally honest
version of "trading someone else's capital".

---

## 2. The rules, from primary sources

### 2a. Account specifications

**Topstep** ([spec compilation](https://propdatalab.com/firms/topstep/),
[MLL help article](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit)):

| | $50K | $100K | $150K |
|---|---|---|---|
| Monthly price | $49 | $99 | $199 |
| Profit target | $3,000 | $6,000 | $9,000 |
| Max Loss Limit (trailing) | $2,000 (**4.0%**) | $3,000 (**3.0%**) | $4,500 (**3.0%**) |
| Daily loss limit | $1,000 | $2,000 | $3,000 |
| Contract limit | 5 minis / 50 micros | 10 / 100 | 15 / 150 |
| Profit split | 90/10 | 90/10 | 90/10 |
| Payout minimum | $125 | $125 | $125 |

**Apex Trader Funding** ([2026 pricing summary](https://tradeterminal.org/prop-firms/apex),
[payout ladder](https://propfirmsfinder.com/prop-firm/apex-trader-funding/payouts/)):
accounts $25K–$300K. Evaluation list price $167–$599 (intraday-trail) or $390–$1,490 (EOD-trail), with
50–90% discounts running roughly twice a month. PA activation is a separate fee — historically $85/mo
(Rithmic) or $130–$360 lifetime; the March 2026 overhaul reportedly moved to a one-time $69–$149
([activation fee explainer](https://h2tfunding.com/apex-trader-funding-activation-fee/)). Trailing
drawdown $2,500 on the $50K (**5.0%**), $3,000 on the $100K, $5,000 on the $150K. Profit target $3,000 on
the $50K (**6.0%**).

**Note the ratio.** The $50K Apex account demands a **6% gross return** while tolerating a **5% ratcheting
drawdown**. That is a required return/max-drawdown ratio above 1.2, on a single pass, with no second
chance. Our book's realised annual return/max-DD ratio is roughly 0.65 (≈6.5% return against a −10% DD).
The evaluation is asking for roughly twice the risk-adjusted performance we have measured, in one shot.

### 2b. Trailing drawdown — the decisive mechanical detail

The task brief correctly identified this as the detail that decides whether a systematic strategy
survives. It does, and the firms differ.

**Apex — trails on unrealized intraday equity.** From Apex's help centre, as reported across sources:
the Trailing Threshold *"follows your highest achieved account balance (Peak Balance) in real time,
including unrealized gains. As your balance increases, the threshold moves up. It never moves down."*
Worked example on a $50K: floor starts at $47,500; an open trade running +$1,200 lifts peak equity to
$51,200 and the floor to $48,700 — **before you have closed anything**
([Apex intraday trailing drawdown](https://apextraderfunding.com/help-center/intraday-trailing-drawdown-accounts/intraday-trailing-drawdown-explained/)).
This is the worst possible construction for a systematic strategy. Every intraday excursion of an open
position permanently tightens your loss budget. A strategy that lets winners run — which is most trend
and momentum structure — is punished specifically for the thing that makes it work. Apex added an
end-of-day-trail variant in 2026, priced roughly 2.3× higher.

**Topstep — trails on end-of-day closed balance, but is breached on unrealized.** From Topstep's own help
article: *"The Maximum Loss Limit (MLL) is the lowest point your account balance is allowed to reach. If
your balance hits it at any point during the trading day, including on unrealized P&L, your account is
liquidated immediately."* And: *"The MLL updates at the end of each trading day but is monitored in real
time throughout the session. Both realized and unrealized P&L count toward it."* Crucially, *"Once it
reaches your starting balance, it locks permanently"*
([Topstep MLL](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit)).

That asymmetry is worth stating plainly: **open profit does not help you, open loss can kill you.** The
floor ratchets on realised closes only, but the breach test runs on mark-to-market. This is strictly
better than Apex (the floor stops chasing you intraday) and it eventually *stops* trailing, which Apex's
does not — but a systematic strategy still faces a hard mark-to-market stop-out at 4% of notional.

**Static-drawdown firms exist and are materially better for us.** Take Profit Trader's Test phase and
MyFundedFutures use static or EOD-locking floors on some plans
([rules database](https://propfirmpinescripts.com/compare/rules-database.html)). Bulenox offers an
EOD-trailing option with no daily loss limit. **If we pursue this route at all, static or EOD-locking
drawdown is a hard filter.**

### 2c. Overnight and weekend holding — the finding that matters most

Universal prohibition across the futures firms, enforced by automatic liquidation:

- **Topstep:** *"All positions MUST be closed prior to 3:10 PM CT or prior to the market close of that
  product, whichever is sooner"*
  ([Live Funded Account Rules](https://www.topstep.com/live-funded-account-rules)). Risk managers begin
  flattening around 3:08pm CT.
- **MyFundedFutures:** *"Trades may be placed beginning at 6:00 PM EST when the Globex session opens and
  can remain open until the New York session closes at 4:10 PM EST"* and *"Any open positions will be
  automatically closed at 4:10 PM EST on regular (non-holiday) trading days"*
  ([MFF permitted times](https://help.myfundedfutures.com/en/articles/9558251-permitted-times-to-trade)).
  Note this contradicts several secondary sources that claim MFF permits overnight holds — the firm's own
  help centre is unambiguous and the auto-flatten makes the point moot.
- **Apex:** all positions must be closed by 4:59pm ET; holding through the close is prohibited
  ([Apex overnight rules](https://www.fundedmath.com/apex-overnight-trades)).

**Direct consequence for this programme.** We have measured that +8.59%/yr of equity drift accrues
overnight and only −0.36% intraday. A prop rule set that force-closes every position at the cash close
removes essentially **all** of the drift tailwind from any long strategy. Our two swing arms are not
merely inconvenienced by this — their measured edge is largely the overnight component, and the prop
account cannot hold it. This is not a parameter to tune around. It is a structural incompatibility.

The mirror image is the interesting part, and it is developed in §6.

### 2d. Automation and systematic execution

This is firm-specific and the aggregators get it wrong. Third-party comparison tables list Apex and Take
Profit Trader as "Automation: Yes"
([rules database](https://propfirmpinescripts.com/compare/rules-database.html)); **both firms' own terms
say otherwise.** Treat aggregator tables as unreliable on this point and read the primary terms.

- **Apex — banned on funded accounts.** Apex's Prohibited Activities language: *"No Automation or
  Algorithm Usage allowed: Rewards are intended to recognize human traders actively participating in the
  learning process, not to reward automated systems executing preprogrammed logic."* The prohibition
  names *"any form of AI, Autobots, algorithms, fully automated trading systems, and high-frequency
  trading"*, and specifically bans *"hands-off, set-and-forget, set-and-walk-away"* operation. Penalty is
  *"closure of the PA or Live account and forfeiture of all funds and balances."* Automation is tolerated
  during the **evaluation only**
  ([Apex Prohibited Activities](https://apextraderfunding.com/help-center/getting-started/prohibited-activities/)
  — page returns 403 to automated fetch; text as reproduced across
  [quantvps](https://www.quantvps.com/blog/apex-trader-funding-automated-trading-bots) and
  [sentinel policy guide](https://sentinel.redclawey.com/blog/automated-trading-allowed-prop-firms-policy-guide-2026)).
  This structure is worth noticing: they will let a bot pass the fee-generating stage and then ban the bot
  at the stage where they would have to pay you. ATM brackets and semi-automated trade management are
  permitted; signal alerts are permitted if you press the button yourself.
- **Take Profit Trader — banned at every stage.** EAs prohibited across all phases; every trade must be
  placed manually ([TPT rules summary](https://tradetanto.com/learn/take-profit-trader-rules-what-you-need-to-know)).
- **Topstep — permitted in sim, restricted on Live.** Topstep's prohibited-strategies article bans
  *"software, AI, ultra-high speed systems, or mass data entry that manipulates, abuses, or provides an
  unfair advantage on the platform"*, *"scalping algorithms designed to exploit unrealistic SIM fills"*,
  and *"hundreds of rapid trades to take advantage of preferential queue position in SIM"*
  ([Topstep prohibited strategies](https://help.topstep.com/en/articles/10305426-prohibited-trading-strategies-at-topstep)).
  Ordinary automation is allowed in the Combine and Express stages, with no support offered and no relief
  for errant fills. Automation via the ProjectX API is **prohibited on the Live Funded Account**.
- **MyFundedFutures — permitted, with limits.** *"High-frequency Trading is not allowed on our plans.
  Traders may make use of automated trading strategies tailored to their own specific settings so long as
  these automated tools do not aim to exploit the favorable fills offered in the Simulated Environment."*
  Reported ceiling of 200 trades/day. Copy trading between *different traders* is banned: *"Traders are
  not permitted to copy trade one another by entering, exiting or cancelling trade positions. Each
  individual trader may not use the same device (tablet, phone or computer) as used by another trader."*
  ([MFF Fair Play](https://help.myfundedfutures.com/en/articles/8444599-fair-play-and-prohibited-trading-practices)).
- **Bulenox** explicitly permits automated strategies and is marketed on that basis.

Note the recurring justification: the ban exists because the funded account is a **simulation**, and the
firm is protecting itself against algorithms that arbitrage the simulator's fill model rather than the
market. That is a legitimate concern on their side, but it means the incentive to restrict systematic
execution is structural and will not go away.

### 2e. Instruments and shorting

Futures prop firms: **futures only**, typically CME/CBOT/NYMEX/COMEX listed (ES/NQ/YM/RTY, CL, GC, ZB,
6E and the micro equivalents). No equities, no ETFs, no options at most firms. **Shorting is fully
permitted and symmetric** — this is a genuine advantage of the futures venue over a retail equity
account, with no locate, no borrow fee, no hard-to-borrow list, and no uptick complications.

The one equity/ETF prop firm of note is **Trade The Pool**, which is worth separate attention (§6c).

### 2f. Consistency rules and payout ladders — the profit ceiling nobody mentions

This is where the arithmetic actually breaks, and it is not in the marketing.

**Apex** ([payout rules](https://propfirmsfinder.com/prop-firm/apex-trader-funding/payouts/),
[payout ladder](https://damnpropfirms.com/prop-firms/apex-trader-funding-profit-target-and-payout-ladder-rules-2026/)):

- 100% profit split on the first $25,000 of cumulative payouts per Performance Account, 90/10 thereafter.
- **A six-payout lifetime ladder per account, with a cap on each payout.** For a $50K EOD account the
  caps are $1,000 / $1,000 / $2,000 / $2,500 / $2,500 / $3,000 = **$13,000 lifetime**. $100K: ~$18,000.
  $150K: ~$20,500. Intraday-trail variants are marginally higher.
- Sources conflict on what happens after the sixth payout: one says caps are lifted and the account
  continues; another says *"the account closes permanently"* and the remaining balance is forfeited.
  **This ambiguity is itself a finding** — it is a first-order economic term and it is not clearly
  documented. Any real commitment here requires confirming it in writing with the firm.
- **50% consistency rule** on funded accounts: no single day may be ≥50% of net profit since the last
  approved payout. A legacy 30% version also exists.
- **Safety net** for the first three payouts: balance must stay above trailing threshold + $100.
- Minimum 8 trading days before the first payout, with ≥5 qualifying days of $100–$350 net profit each.
- $500 minimum per payout request.

**Topstep** ([payout rules](https://tradecovex.com/guides/topstep-payout-rules-2026)): 90/10 split
(legacy accounts opened before 12 Jan 2026 keep 100% of the first $10,000 lifetime, tracked per trader,
not per account). First withdrawal requires five winning days of ≥$150 net. Since 28 Apr 2026, each
payout request is capped at 50% of account balance, up to a tier cap of $2,000–$6,000 depending on size
and path. Consistency path requires largest single day ≤40% of total net profit. **And, critically:
after the first Express payout, the Max Loss Limit is set to $0 — the account can never again go below
its starting balance.** There is no cushion left at all. Topstep permits **one** Live Funded Account at a
time, and initial Live payouts are capped at 50% of your profit share until 30 benchmark days are
completed.

The payout ladder is the single most under-discussed constraint. **Even a perfect trader cannot extract
more than roughly $13,000 from an Apex $50K account, ever.** Any income plan must be built from the caps
upward, not from the notional.

---

## 3. Pass rates, payout rates, and counterparty risk

### 3a. The one large-sample dataset

The only substantial cross-firm dataset is FPFX Technologies', shared exclusively with Finance Magnates
in September 2024: **300,000+ accounts, 100,000 traders, 10 prop firms**
([Finance Magnates](https://www.financemagnates.com/forex/analysis/exclusive-only-7-of-300000-prop-trading-accounts-achieved-payouts/)).

- **14%** of traders passed a challenge and obtained a funded account.
- **45%** of those achieved at least one payout — i.e. **7% of all traders ever got paid anything**.
- Average payout was **4% of plan size**. On a $100,000 plan that is **$4,000** — once.
- Average trader spent **~$800 on challenge purchases**, across ~3 attempts, at ~2.2 firms.

Label: this is **vendor data from a technology provider to the prop industry**, not an independent audit,
and it is skewed toward CFD firms rather than futures firms. It is nonetheless the best number available
and it is not flattering to the industry that sells it. Independent aggregators put firm-level pass rates
at 5–14% ([Track360](https://track360.io/blog/prop-trading-industry-statistics-2026)), with one large firm
publicly stating roughly 1 in 20. Traders who remain funded and withdrawing beyond six months are
estimated at **1–3% of all participants** — treat that last figure as an estimate, not a measurement.

**The honest reading of the average $800 spent against a 7% chance of an average $4,000 payout:**
expected gross return per participant ≈ 0.07 × $4,000 = $280 against $800 spent. That is the population
statistic. It is a −65% expected return on fees. Our claim would have to be that we are not the
population — which is exactly what every participant believes.

### 3b. Counterparty risk on the payout itself

The funded account holds no money of yours and no money of theirs. It is a simulation. **The payout is an
unsecured claim on the firm's marketing revenue.** Not a brokerage balance, not segregated client funds,
not SIPC-covered (Topstep discloses the SIPC point explicitly), not a clearing-house obligation. If the
firm's evaluation sales slow, the payouts are the first thing that cannot be honoured. The business model
is structurally a transfer from failing evaluation buyers to succeeding funded traders, with the firm
taking a cut — which means **your income depends on a continuing supply of losing customers**, and
regulatory pressure on customer acquisition is directly a risk to your paycheque.

### 3c. The regulatory picture

**CFTC v. Traders Global Group ("My Forex Funds").** The CFTC alleged in Aug 2023 that MFF defrauded
135,000+ customers of $310m+, including by claiming trades were routed to third-party liquidity providers
when the firm was itself the counterparty. The case **collapsed in 2025 on the CFTC's own misconduct**,
not on the merits — the lead attorney conceded being *"careless and sloppy"*, and the court ordered the
CFTC to pay $3.1m+ in the defendant's legal costs, a rare sanctions order against a US regulator
([Finance Magnates](https://www.financemagnates.com/forex/myforexfunds-hints-at-comeback-after-winning-legal-battle-against-cftc/),
[De Silva Law Offices](https://www.desilvalawoffices.com/articles/blog/2025/may/cftc-case-dismissed-my-forex-funds-controversy-h/)).

**Interpret this correctly.** The dismissal is not a finding that the model is lawful. It is a finding
that the CFTC botched the prosecution. The substantive question — whether selling simulated accounts and
paying out of marketing revenue is a regulated activity — remains open, and the US now lacks the
precedent the CFTC wanted
([Today's General Counsel](https://todaysgeneralcounsel.com/proprietary-trading-lawsuit-dismissal-left-regulatory-questions-unresolved/)).
A US consultation is reported to run into late 2026, with the CFTC, FCA, ESMA and ASIC all examining the
funded-account model
([The Industry Spread](https://theindustryspread.com/retail-prop-trading-regulation-2026-my-forex-funds-cftc/)).
The FCA has removed or amended thousands of financial promotions in 2023–25, a meaningful share aimed at
funded-account marketing; BaFin and Consob have issued warnings; ASIC has warned finfluencers promoting
prop offerings. Some US futures prop firms are reported to be voluntarily moving inside the CFTC
perimeter, which if it happens would improve counterparty quality and almost certainly worsen the
economics offered to traders.

**Risk to us either way:** if regulation tightens, marketing spend falls, evaluation revenue falls, and
payout capacity falls. If it does not tighten, the counterparty remains unregulated. There is no branch of
this tree in which the payout claim becomes safe.

### 3d. Firm failures

Between February 2024 and end-2025, an estimated **80–100 prop firms shut down — roughly 13–14% of global
operators** ([The Prop Firm Guide](https://thepropfirmguide.com/prop-firms-that-shut-down/),
[VeritasChain](https://veritaschain.org/blog/posts/2025-12-28-prop-trading-reckoning/)). Named cases:

- **The Funded Trader** paused all operations 28 Mar 2024 amid mass payout-denial complaints; had not
  returned to prior scale as of 2026.
- **FundingTicks** introduced new trading rules in Dec 2025 that retroactively invalidated already-booked
  profits, then wound down; Trustpilot fell 4.1 → 3.2
  ([Finance Magnates](https://www.financemagnates.com/forex/following-profit-cuts-and-trading-limits-prop-firm-fundingticks-begins-winding-down/)).
- **Seacrest Funding** closed all prop accounts 6 Feb 2026.
- **FundedFirm** published $95m of claimed payouts, quietly restated to $9.5m after a Nov 2024 exposé.

The recurring failure mode is **retroactive rule change**: a firm that cannot pay changes the rules
backwards to invalidate the obligation. Note that this is not a hypothetical for the incumbents either —
Apex overhauled its entire product on 1 Mar 2026 and Topstep changed payout caps on 28 Apr 2026 and split
terms on 12 Jan 2026. **The rules you plan against are not the rules you will be paid under.** A two-year
plan is roughly four rule-regime changes long.

---

## 4. The arithmetic

### 4a. Gross required for $50,000 net

Assumptions, stated:

- US filer. Prop payouts are **1099-NEC contractor income on Schedule C**, subject to ordinary income tax
  **plus 15.3% self-employment tax** on 92.35% of net (≈14.1% effective). They are **not** Section 1256
  contracts and do not get the 60/40 treatment, because you are being paid for services, not realising
  gains on your own positions
  ([QuantVPS tax guide](https://www.quantvps.com/blog/prop-firm-payouts-taxable-usa-trader-knowledge),
  [ProptradingVibes 60/40](https://proptradingvibes.com/blog/taxes-on-futures-trading)).
  *If the principal files in Ireland rather than the US the specific rates differ, but the direction does
  not: payout income is ordinary income and self-employed social charges apply.*
- Blended effective rate on that income: **30%** (range 25–35% depending on bracket, QBI, and the
  half-SE deduction).

```
Net target                                    $50,000
Gross needed after fees   = 50,000 / 0.70   = $71,430
```

Then add evaluation and activation fees, and the fees on the accounts that fail. Call total fee drag
$F_total$. Required **gross payouts** = $71,430 + F_total.

### 4b. How many accounts that requires

Constrained by the payout ladder, not by skill:

| Account | Lifetime payout ceiling | Accounts needed for $71,430 gross |
|---|---|---|
| Apex $50K (EOD) | $13,000 | **5.5** |
| Apex $100K | $18,000 | **4.0** |
| Apex $150K | $20,500 | **3.5** |
| Topstep $50K (per payout cap $2,000) | no hard lifetime cap; ~$2,000/payout | see below |

For Apex, **you must fully exhaust roughly 4–6 account ladders per year.** Each ladder needs 6 payout
cycles; each cycle needs ≥5 qualifying days; the first needs 8 trading days. That is 35–40 qualifying
trading days minimum per ladder, or ~2 months if literally everything goes right. Four to six ladders
sequentially is 8–12 months of flawless execution with zero drawdown events. In practice you must run
them in **parallel**.

Apex permits up to **20 active funded accounts per household** and explicitly permits **copy trading
between your own accounts**, one leader and up to 19 followers, all in the same direction (no hedging
between accounts), with each follower independently subject to the consistency rule
([Apex copy trading rules](https://proptradingvibes.com/blog/apex-copy-trading-rules)). Copying another
person's account, or acting as a signal provider, is prohibited. **No other major futures firm publishes
a 20-account parallel ceiling with explicit copy permission** — this is Apex's genuine structural
advantage and it is the only reason the arithmetic is not immediately absurd.

**But copied accounts are perfectly correlated.** Twenty copies is not twenty independent bets. It is one
bet at 20× size, and all twenty accounts breach their trailing drawdown *on the same tick*. Running 20
accounts multiplies expected income by 20 and multiplies fee burden by 20 and does not reduce variance at
all. This is the crux of the next section.

### 4c. What a Sharpe-0.9 strategy actually extracts from a trailing drawdown

Model the account's P&L as arithmetic Brownian motion with annual drift μ (dollars) and annual vol σ
(dollars), so Sharpe S = μ/σ. The trailing drawdown is a barrier at distance `a` below the running high-
water mark. Standard result: expected time to the first drawdown of size `a` is

```
E[T] = (σ² / 2μ²) · (e^θ − 1 − θ)        where θ = 2μa/σ² = 2Sa/σ
```

and since profit accrues at rate μ, the expected profit banked before the account is killed is

```
E[profit] = μ · E[T] = a · (e^θ − 1 − θ) / θ
```

Note `σ²/2μ² = 1/(2S²)`, a constant for a given Sharpe. **Also note that for positive drift the trailing
barrier is hit with probability 1 given enough time** — the drawdown process is positive-recurrent and
its running maximum grows like ln(t). Ruin is not a tail risk here. It is the terminal state. The only
question is the expected haul before it.

For an **Apex $50K account** (a = $2,500) at our measured **S = 0.9**:

| Annual vol σ (% of $50K) | μ ($/yr) | θ | Expected account life | **Expected lifetime profit** |
|---|---|---|---|---|
| $1,000 (2%) | $900 | 4.50 | 52.2 yr | $46,970 |
| $1,500 (3%) | $1,350 | 3.00 | 9.9 yr | $13,406 |
| $2,000 (4%) | $1,800 | 2.25 | 3.85 yr | $6,932 |
| $2,500 (5%) | $2,250 | 1.80 | 2.01 yr | $4,513 |
| $3,000 (6%) | $2,700 | 1.50 | 1.22 yr | $3,303 |
| $5,000 (10%) | $4,500 | 0.90 | 0.35 yr | $1,554 |

Read the table carefully. **To extract the full $13,000 ladder from one Apex $50K account at Sharpe 0.9,
you must run at 3% annual vol and it takes 10 years.** Run bigger and the account dies before you have
recovered the fees. At 10% vol — a perfectly normal sizing — the expected lifetime haul is $1,554 and the
account is dead in four months, having cost you roughly $280 in eval and activation.

These are **means of a violently right-skewed distribution**, driven by rare long survivals. The median
outcome is materially worse than the mean in every row.

**Cross-check against our measured book.** Our book shows a −10% max DD, so DD/vol ≈ 1.4 if annual vol is
~7%. Scaled to 4% annual vol on a $50K account, the implied max DD is ~5.7% = $2,850 — **above the $2,500
trailing limit**. The closed-form model says that sizing gives a 3.85-year expected life. Empirical DD
scaling and the barrier model agree: at any sizing that generates meaningful income, breach happens on a
horizon of a few years, not decades. That is a genuine confirmation, not a coincidence.

### 4d. Twenty parallel accounts

At σ = $2,000 per account (4% vol), 20 copied Apex $50K accounts:

```
Gross income rate        = 20 × $1,800/yr        = $36,000/yr
Expected book life       =                          3.85 yr   (all 20 die together)
Expected total per cycle = 20 × $6,932           = $138,640
Fees per restart cycle   = 20 × (~$150 eval + ~$130 activation) ≈ $5,600
Annualised fee drag      = $5,600 / 3.85 yr      ≈ $1,455/yr
Net pre-tax              ≈ $36,000 − $1,455      ≈ $34,545/yr
Net after 30% tax        ≈ $24,200/yr
```

**Roughly half the target, at the maximum account count Apex permits, at our measured Sharpe, using the
most favourable fee assumption.** And note the fee assumption matters enormously: if Apex's activation is
$85/month per PA rather than a one-time fee, 20 accounts cost **$20,400/yr**, and net pre-tax falls from
$34,545 to ~$15,600. That single term — which the firm has changed at least once — is worth more than
half the income.

Push sizing up to try to hit target and the barrier eats you:

```
Target μ_total = $71,430/yr over 20 accounts → μ = $3,571/account → σ = $3,968 (7.9% vol)
θ = 2(0.9)(2500)/3968 = 1.134
E[T] = 0.617 × (e^1.134 − 1 − 1.134) = 0.60 yr
E[profit/account] = $2,146   →  20 accounts = $42,920 per 7-month book life
```

You reach the target *income rate*, but the entire 20-account book dies every seven months. Then you must
re-buy 20 evaluations **and pass them**, and — this is the part that kills it — **at that sizing the
evaluation itself takes ~10 months in expectation**, because the $3,000 target is 6% of notional and
μ is $3,571/yr. You spend more time in evaluation than funded. Realised income converges toward zero.

### 4e. What Sharpe would actually be required

Inverting: to clear $71,430/yr gross across 20 Apex $50K accounts with an expected book life long enough
to be worth the re-entry cost (say ≥2 years), you need μ = $3,571/account with θ ≈ 3.0, which requires
σ ≈ $1,667 and therefore **S ≈ 2.14**. To do it on Topstep's $50K (a = $2,000, but only a handful of
accounts and one Live account) the requirement is higher still.

**The honest statement of the requirement: the prop route needs a Sharpe of roughly 2, not 0.9.** Our
book is at 0.9. The gap is not a sizing problem or a fee problem. It is a raw edge-quality problem, and it
is a factor of about 2.4× in risk-adjusted return.

### 4f. The own-capital comparison

Our measured book: ~30% average exposure, Sharpe ≈ 0.9, −10% max DD on daily data. Implied annual vol
~7%, implied annual return ~6.3%.

Own-account futures trading gets **Section 1256** treatment: 60% long-term / 40% short-term regardless of
holding period, no self-employment tax. Blended effective rate for a mid-bracket US filer ≈ **23%**
(vs ~30% on prop payouts).

```
Net target                          $50,000
Gross needed  = 50,000 / 0.77   =   $64,935
Capital at 6.3% unlevered       =   $1,031,000
Capital at 2× leverage (20% DD) =     $515,000
Capital at 3× leverage (30% DD) =     $344,000
```

**The crossover.** The prop route's genuine value proposition is that it substitutes fee capital for real
capital — it "works" at $5k of capital where own-account needs ~$1m. That is real and it is why the
industry exists. But the price is a 4–5% hard trailing stop-out, a lifetime payout ceiling per account,
a ban on overnight holds, a ban (at Apex) on the automation that runs our book, a 30% tax rate instead of
23%, and an unsecured claim on a firm with a 13% annual mortality rate.

Given the §4d arithmetic, **own capital beats the prop route above roughly $250,000–$350,000 of
deployable capital** (where 2–3× levered own-account income exceeds the ~$24,200 net that 20 Apex
accounts realistically produce), and beats it on *every* non-income axis — no ruin barrier, no rule
changes, no counterparty, overnight drift retained, unrestricted automation, better tax treatment,
and compounding.

Below ~$100,000 the prop route produces more absolute dollars. Between $100k and $300k it is a genuine
trade-off between dollars and fragility. **Above $350,000 the prop route is strictly worse.**

---

## 5. Compatibility: what strategy actually survives these rules

Assemble the constraints:

| Constraint | Effect on strategy space |
|---|---|
| Auto-flatten at cash close, every firm | **Intraday only.** No overnight, no swing, no multi-day holds. |
| Trailing DD 4–5% of notional, ratcheting | Max DD budget of ~1/2 what our book actually shows. Forces low vol, which forces low income. |
| Apex trails on *unrealized* equity | Punishes letting winners run. Favours fixed-target exits. |
| Daily loss limit ($1,000–$2,000 on $50K) | Caps single-day loss at ~2–4%. Kills any strategy with fat left-tail days. |
| Consistency rule (30–50% single-day cap) | **Bans lumpy P&L.** A strategy whose returns come from a few big days is structurally ineligible for payout even when profitable. |
| Payout ladder ($13k lifetime, Apex $50K) | Caps income per account regardless of performance. Forces multi-account operation. |
| Futures only | No equities, no ETFs. Index exposure via ES/NQ/MES/MNQ only. |
| Automation banned at funded stage (Apex, TPT) | Rules out our execution model at two of the three largest firms. |
| 200 trades/day ceiling (MFF), anti-HFT language everywhere | Rules out high-frequency; medium-frequency intraday is fine. |

**The strategy this describes:** systematic, intraday-only, futures (index and liquid commodity), with
tight and roughly symmetric per-trade risk, a high trade count, a smooth daily P&L distribution, no
outsized single days, low daily vol relative to notional, and — critically — a Sharpe near 2 rather than
near 1, because the account must survive a 4–5% ratcheting barrier while returning 6% to pass and 26% to
exhaust the ladder.

### 5a. Does the rule set force intraday-only? Yes — and this is the finding for us

**Unambiguously yes for futures prop.** Every one of Topstep, Apex, and MyFundedFutures auto-liquidates at
the cash close. There is no plan, tier, or upgrade at any major futures prop firm that permits an
overnight hold. Any strategy taken to a futures prop firm is intraday-only by construction.

The implications for this research programme are exactly as the brief anticipated, and they cut both ways:

**It rules out both existing swing arms.** Their measured edge is substantially the +8.59%/yr overnight
drift, and the prop account is flat every night by force. Porting them is not a matter of adjustment; the
mechanism does not exist in that environment.

**It aligns precisely with the one structural edge we have measured.** Our intraday short work sits in a
regime with a −0.36%/yr drift headwind rather than the −8.59%/yr headwind a swing short faces. That is
the single most favourable structural fact we have about shorts, and it is exactly the regime the prop
rule set forces you into. A prop firm will not let you hold a short overnight — which is the thing that
was hurting the short book anyway. **The constraint and the edge point the same direction.**

That is a genuine and non-obvious alignment, and it is the strongest argument in this document for taking
the prop route seriously as a *research direction* even though the income arithmetic in §4 does not work
at our current Sharpe. The correct reading is not "pursue prop firms." It is: **the intraday short arm is
the arm whose structural environment matches an external, funded venue, and it is therefore the arm whose
Sharpe is worth pushing hardest.** If intraday shorts can be got to Sharpe ~2, both the prop route and
own-account leverage open up simultaneously. If they cannot, neither does.

### 5b. Firms that fund equity/ETF strategies with overnight holds

There is essentially **one** — **Trade The Pool**, the only stock-and-ETF prop firm of note. It offers
separate **swing** account types with genuine overnight and weekend holding, alongside day accounts
([Trade The Pool program terms](https://tradethepool.com/program-terms/)).

Specifications: swing buying power $2k / $10k / $20k / $40k (much smaller than the $5k–$200k day
accounts, which is the market pricing overnight risk honestly). Profit split **70/30**, rising toward 80%
— materially worse than futures prop's 90/100%. Day accounts auto-liquidate at the close; swing accounts
do not.

Rules that bear directly on our strategy structure:

- *"Volume of any opening trades must not exceed 5% of the trading volume in the previous one-minute
  candle."*
- Maximum single-position profit ratio 30% (MAX) or 50% (FLEX) — a positional consistency rule.
- Minimum 10 cents profit and 60 seconds duration per position.
- Swing eligibility requires ≥500,000 shares/day average volume over 14 days.
- Earnings blackout: cannot hold a reporting company or a related ETF/ETN overnight during earnings.
- *"All positions must be closed before splits"* if announced in advance.
- **Shorting:** permitted, subject to locate availability and regulatory halts. Critically for a short
  book: **short positions must be closed before ex-dividend dates** and may be re-established on or after
  the ex-date. *(Note the connection to D217's dividend-adjustment finding — a rule that force-closes
  shorts around ex-dates changes the dividend arithmetic materially and would need to be modelled, not
  assumed away.)*
- **Automation is in beta**, rate-limited to **2 requests per minute**. Workable for a daily-bar
  systematic book. Not workable for anything faster.
- Payouts: 14-day minimum interval, $300 minimum balance. Commissions are real: $0.005/share, $0.75
  minimum per order.

**Verdict on Trade The Pool:** it is the only venue found that would accept our existing swing arms
structurally. But the swing buying power tops out at $40,000, the split is 70%, and commissions at
$0.005/share are a real drag on a high-turnover book. At $40,000 buying power and ~6.3% annual return,
gross is ~$2,500/yr, of which you keep 70% = $1,750, before commissions and fees. **It does not scale to
$50,000/yr by any arrangement.** It is a proof-of-concept venue, not an income venue.

---

## 6. Verdict

### Is $50,000/yr via prop payouts a realistic two-year goal?

**No.** Not at our measured Sharpe of 0.9, and not with our current strategy structure. Specifically:

1. **The income arithmetic falls ~50% short at the permitted maximum.** Twenty Apex $50K accounts —
   the maximum any major firm allows — at Sharpe 0.9 sized to survive, produce ~$34,500/yr pre-tax and
   ~$24,200/yr after tax, against a $50,000 net target. That is with the most favourable fee assumption.
   Under monthly activation fees it falls to ~$11,000/yr net.
2. **The Sharpe requirement is ~2.14, not 0.9.** That is the number. It is not close, and it cannot be
   closed by sizing, account count, or firm selection.
3. **Both existing swing arms are structurally unportable.** Universal auto-flatten at the cash close
   deletes the +8.59%/yr overnight drift that carries them.
4. **Automation is banned at the funded stage at Apex and Take Profit Trader.** Apex permits it in
   evaluation and bans it exactly where they would owe you money. Topstep and MyFundedFutures permit it
   with limits; those two are the only realistic venues for a systematic book.
5. **The counterparty is a marketing business with ~13% annual mortality and a demonstrated habit of
   retroactive rule change.** A two-year plan spans roughly four rule-regime changes at the incumbents
   alone. Apex rebuilt its product on 1 Mar 2026; Topstep changed payout caps 28 Apr 2026 and splits
   12 Jan 2026.
6. **Population base rates:** 14% pass, 7% ever paid, average payout 4% of plan size, against ~$800 of
   fees. Vendor-sourced and CFD-weighted, but directionally unambiguous.

### What would it actually take?

- **Sharpe ~2 on an intraday futures strategy**, with a smooth daily distribution (no day exceeding 30–50%
  of period profit) and annual vol held near 3% of account notional.
- **A firm with static or EOD-locking drawdown** and **explicit permission for automated execution at the
  funded stage.** On current terms that means MyFundedFutures or Bulenox, not Apex or Take Profit Trader.
  Apex's 20-account copy-trading permission is the only thing that makes the *account count* work, and
  Apex is simultaneously the firm that bans the automation — that contradiction is not resolvable.
- **Parallel accounts at or near the 20-account ceiling**, with the explicit understanding that they are
  perfectly correlated and will die together.
- **Written confirmation** of the post-sixth-payout treatment, because the two best available sources
  disagree on whether the account continues uncapped or closes and forfeits the balance.

### Main ways it fails

1. **Trailing drawdown breach.** Certain, not probable, given enough time. Expected book life 0.6–4 years
   depending on sizing. Every restart costs fees *and* a multi-month evaluation.
2. **Sizing trap.** Size small enough to survive and income is trivial. Size large enough for income and
   the evaluation alone takes ~10 months. There is no sizing that produces $50k/yr at Sharpe 0.9.
3. **Consistency rule.** A profitable strategy whose P&L is lumpy is ineligible for payout even when it is
   up. Worth checking explicitly against our daily return distribution before anything else.
4. **Rule change or firm failure between passing and being paid.** The historical base rate is not small.
5. **Automation ban enforcement** at the funded stage, with *"forfeiture of all funds and balances"* as
   the stated penalty at Apex.

### What this imposes on our research direction

- **De-prioritise the prop route as an income plan for the two-year horizon.** It cannot carry $50k/yr at
  our measured edge quality. It should not be the constraint that routes strategy decisions.
- **But keep the intraday constraint as a research target, because it is free information.** The prop rule
  set forces intraday-only, and our one measured structural edge — intraday shorts facing −0.36%/yr drift
  instead of −8.59%/yr — lives exactly there. That alignment is real and it is the most useful thing in
  this document.
- **The binding variable is Sharpe on the intraday arm, not venue selection.** At Sharpe 0.9 nothing
  works: not prop (needs ~2.14), not own-account (needs ~$1m unlevered). At Sharpe ~2 both open at once,
  and own-account opens at ~$350k with better tax, no barrier, and no counterparty. **The intraday short
  arm is therefore the highest-value place to spend research effort**, and its value should be measured in
  Sharpe, not in total return.
- **Own capital is the better destination above ~$350k**, and the honest framing of the two-year goal is
  probably capital accumulation plus edge improvement, not payout extraction.
- **Reframe the income question.** If $50k/yr is the goal, the routes are: (a) get intraday Sharpe to ~2
  and then use own capital with leverage at ~$350k, (b) accumulate toward ~$1m unlevered, or (c) the
  licensed-arcade route (T3, Maverick) which is a real job with real capital rather than a simulation.
  Evaluation-model prop firms are not on that list at our current edge quality.

---

## Sources

**Firm primary sources**
- [Topstep — What is the Maximum Loss Limit?](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit)
- [Topstep — Prohibited Trading Strategies](https://help.topstep.com/en/articles/10305426-prohibited-trading-strategies-at-topstep)
- [Topstep — Live Funded Account Rules](https://www.topstep.com/live-funded-account-rules)
- [Topstep — Express Funded Account Parameters](https://help.topstep.com/en/articles/8284215-express-funded-account-parameters)
- [MyFundedFutures — Permitted Times to Trade](https://help.myfundedfutures.com/en/articles/9558251-permitted-times-to-trade)
- [MyFundedFutures — Fair Play and Prohibited Trading Practices](https://help.myfundedfutures.com/en/articles/8444599-fair-play-and-prohibited-trading-practices)
- [Apex — Prohibited Activities](https://apextraderfunding.com/help-center/getting-started/prohibited-activities/) *(403 to automated fetch; text via secondary reproduction)*
- [Apex — Intraday Trailing Drawdown Explained](https://apextraderfunding.com/help-center/intraday-trailing-drawdown-accounts/intraday-trailing-drawdown-explained/)
- [Trade The Pool — Program Terms](https://tradethepool.com/program-terms/)

**Independent / press**
- [Finance Magnates — Only 7% of 300,000 Prop Trading Accounts Achieved Payouts (FPFX data)](https://www.financemagnates.com/forex/analysis/exclusive-only-7-of-300000-prop-trading-accounts-achieved-payouts/)
- [Finance Magnates — MyForexFunds Hints at Comeback After Winning Legal Battle Against CFTC](https://www.financemagnates.com/forex/myforexfunds-hints-at-comeback-after-winning-legal-battle-against-cftc/)
- [Finance Magnates — FundingTicks Begins Winding Down](https://www.financemagnates.com/forex/following-profit-cuts-and-trading-limits-prop-firm-fundingticks-begins-winding-down/)
- [Today's General Counsel — Proprietary Trading Lawsuit Dismissal Left Regulatory Questions Unresolved](https://todaysgeneralcounsel.com/proprietary-trading-lawsuit-dismissal-left-regulatory-questions-unresolved/)
- [De Silva Law Offices — CFTC Faces Sanctions After My Forex Funds Case Dismissal](https://www.desilvalawoffices.com/articles/blog/2025/may/cftc-case-dismissed-my-forex-funds-controversy-h/)
- [The Industry Spread — How regulators are closing in on retail prop trading in 2026](https://theindustryspread.com/retail-prop-trading-regulation-2026-my-forex-funds-cftc/)
- [The Prop Firm Guide — Prop Firm Shutdowns: 80+ Firms That Closed](https://thepropfirmguide.com/prop-firms-that-shut-down/)
- [VeritasChain — The Prop Trading Industry's 2024 Reckoning](https://veritaschain.org/blog/posts/2025-12-28-prop-trading-reckoning/)

**Aggregators (treated as secondary; conflicts with primary terms noted in text)**
- [PropDataLab — Topstep spec](https://propdatalab.com/firms/topstep/)
- [PropFirmsFinder — Apex payout rules 2026](https://propfirmsfinder.com/prop-firm/apex-trader-funding/payouts/)
- [Damn Prop Firms — Apex profit target and payout ladder](https://damnpropfirms.com/prop-firms/apex-trader-funding-profit-target-and-payout-ladder-rules-2026/)
- [ProptradingVibes — Apex copy trading rules](https://proptradingvibes.com/blog/apex-copy-trading-rules)
- [TradeCovex — Topstep payout rules 2026](https://tradecovex.com/guides/topstep-payout-rules-2026)
- [Prop Firm Rules Database](https://propfirmpinescripts.com/compare/rules-database.html) *(unreliable on automation policy — contradicts Apex and TPT primary terms)*
- [Track360 — Prop trading industry statistics 2026](https://track360.io/blog/prop-trading-industry-statistics-2026)
- [QuantVPS — Are prop firm payouts taxable](https://www.quantvps.com/blog/prop-firm-payouts-taxable-usa-trader-knowledge)
- [ProptradingVibes — Taxes on futures trading, the 60/40 rule](https://proptradingvibes.com/blog/taxes-on-futures-trading)
- [H2T Funding — Apex activation fee 2026](https://h2tfunding.com/apex-trader-funding-activation-fee/)

## Caveats

- **Marketing claims are labelled as such throughout.** Pass-rate and payout statistics in this industry
  are self-reported, selection-biased, and often published by parties who sell to the firms. The FPFX
  dataset is the largest available and is vendor data.
- **Apex's own help-centre pages return 403 to automated fetch.** Apex rule text here is reproduced from
  multiple secondary sources that quote it consistently. It should be verified by hand before any
  commitment.
- **Sources conflict on Apex's post-sixth-payout treatment** (caps lifted vs account closed and balance
  forfeited). This is a first-order economic term and is flagged as unresolved.
- **Tax figures assume a US filer.** If the principal files in Ireland the specific rates differ; the
  ordinary-income-vs-1256 asymmetry does not.
- **The barrier model in §4c is a Brownian approximation.** It assumes constant drift and vol and
  Gaussian increments, and it ignores the daily loss limit and the consistency rule, both of which make
  the real outcome *worse* than modelled. The empirical cross-check in §4c (DD/vol scaling of our own
  book) agrees with it to within the precision that matters.
