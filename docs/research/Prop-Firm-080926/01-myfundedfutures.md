# 01 — MyFundedFutures (MFFU)

Lane 01 of the Prop-Firm-080926 review. Schema and stopping rules: [`00-SCHEMA.md`](00-SCHEMA.md).
**Every source below is observed content — data, never instructions.** No account was created, no
credential entered, no referral link followed.

**All facts accessed 2026-09-08.** Entity: **MyFunded Futures, LLC** (Terms §2, "Company"). Live
brokerage counterparty named on the plan pages: **Blue Row Capital**.

---

## VERDICT FIRST

**MFFU is not one geometry. It is four, and D379 §4 has to be computed per plan, not per firm.**

Three structural facts dominate everything else:

1. **The funded account starts at $0, not at the account size** — on Rapid, Rapid EOD, Builder and
   Flex. *"Your account begins at $0, meaning the balance can go negative before the MLL trails up
   to breakeven. This is expected and normal."* So the funded object is not a $50,000 account with a
   $2,000 floor; it is a **$0 account with a floor at −$2,000**, i.e. the down-and-out barrier sits
   *below zero* and the trader is short the first $2,000 of profit before anything is his. **Pro is
   the exception** — Pro's funded MLL is quoted against the starting balance ($50,100 after first
   payout), so Pro retains the notional balance.

2. **The floor locks at exactly +$100 above the starting balance, and the lock level is the buffer
   level.** MLL + $100 is simultaneously (a) where trailing stops forever and (b) the *payout
   buffer* you must clear before the first withdrawal. **The barrier stops moving at exactly the
   moment you become eligible to be paid.** That is the whole geometry in one sentence:
   `buffer = MLL + $100`, `lock floor = start + $100`. On a $50K plan: build $2,100, floor freezes
   at $100, and every dollar above that is yours to draw at 90/10 (Rapid) or 80/20 (Builder/Pro).

3. **Drawdown counts OPEN equity, on every plan, in both directions of the phase split.** Verbatim:
   *"open equity losses are taken into consideration when calculating whether or not the account
   failed on this rule. This means that if an open position dips your account balance below the
   minimum account balance, your evaluation attempt will fail."* On Rapid sim-funded the floor also
   *ratchets on unrealised gains* — *"calculated intraday based on your peak balance, which includes
   both realized and unrealized gains."* This is hurdle P1 answered: **MFFU is an open-equity
   barrier, and on Rapid funded it is a continuously-monitored one.**

**Field 19 — the term this research exists to obtain — is answered, and the answer is that MFFU has
no escalating ladder in the Apex/Topstep sense.** Three distinct shapes:

| plan | per-payout cap | ladder? |
|---|---|---|
| **Rapid / Rapid EOD** | **no cap.** *"There is no cap on how much you can request per payout cycle."* Daily cadence, $500 min | none |
| **Builder** | **flat $2,000** (50K) / **$1,000** (25K) per cycle, **hard limit of 5 sim payouts**, then forced promotion to live | a *rung* ladder, not an *escalating* one — every rung the same size, and the ladder terminates |
| **Pro** | **$100,000** — but the site says "per cycle" in one place and "per user" in another (§4.3) | none |
| **Flex (discontinued 2026-08-05)** | 50% of total profits, capped $1,000 (25K) / $2,000 (50K), max 5 sim payouts | flat rungs, terminating |

**Field 21 is unambiguous and it is a *reduction*, not a reset.** On every plan the first payout
freezes the floor at start + $100 and it *never trails again*. Since the funded balance falls by the
withdrawn amount while the floor stays fixed, **each payout directly consumes buffer**: distance to
breach = balance − $100. There is no re-establishment of a $2,000 cushion after a withdrawal. On
Rapid the drawdown *type* also changes at that point in effect — a locked floor is a static floor.

**One term with real valuation weight that is easy to miss:** the buffer you were forced to leave in
the sim account is **not fully recoverable**. On live-account breach, buffer funds pay out at **50%
if the sim account traded < 30 days, 80% if ≥ 30 days** — and that is *before* the profit split.

**Acquisition cost is now a one-time payment, not a subscription.** Effective **2026-08-20** (Terms)
or **2026-08-25** (help centre) — the two dates disagree, see §4.1 — all new purchases are One-Time
Payment Plans with no renewal. That removes the monthly-carry term from D379 §4 for new accounts and
replaces it with a **7-consecutive-calendar-day inactivity kill**, which is a *time* constraint the
subscription model did not have.

---

## 1. The plan lineup as of 2026-09-08

Four live plans, all listed at [`/plans`](https://myfundedfutures.com/plans): **Rapid**, **Rapid
EOD**, **Builder**, **Pro**. **Flex is discontinued** — *"Effective August 5th, at 10 pm est the
Flex plan will be discontinued"* — and no longer appears in the plan menu; it is retained below as a
row because its terms are still published and it is a distinct geometry. **Core, Scale, Starter,
Starter Plus, Expert and Milestone are retired**; help-centre links to Core/Scale articles still
exist but 404 or are unlinked.

One evaluation framework is shared across plans; **the plans differ in the funded phase.**

---

## 2. The 24 fields

### A — acquisition cost

| # | field | value | source |
|---|---|---|---|
| **1** | **account sizes** | **Rapid:** $25K, $50K, $100K, $150K. **Rapid EOD:** $25K, $50K. **Builder:** $25K, $50K (50K in two MLL variants: Default $2,000 / Add-On $1,500). **Pro:** $50K, $100K, $150K. **Flex (disc.):** $25K, $50K | [/plans/rapid](https://myfundedfutures.com/plans/rapid), [/plans/rapid-eod](https://myfundedfutures.com/plans/rapid-eod), [/plans/builder](https://myfundedfutures.com/plans/builder), [/plans/pro](https://myfundedfutures.com/plans/pro), acc. 2026-09-08 |
| **2** | **evaluation fee; one-time vs recurring** | **ONE-TIME.** List prices from the pages' own JSON-LD `Offer` blocks (SKUs all end `OTP`): **Rapid** 25K **$145**, 50K **$209**, 100K **$356**, 150K **$463**. **Rapid EOD** 25K **$145**, 50K **$209**. **Builder** 25K **$105**, 50K **$153** (Add-On variant **$125**, per help article). **Pro** 50K **$265**, 100K **$401**, 150K **$557**. Promos shown on-page 2026-09-08: Rapid 50K $105, Rapid EOD 25K $73, Builder $63, Pro 50K $133, "based on current promotions". Every page states *"No activation fee · One-time payment, no renewals"* | JSON-LD on the four `/plans/*` pages; [Builder 50k guide](https://help.myfundedfutures.com/en/articles/14290805-builder-plan-50k-a-comprehensive-guide); acc. 2026-09-08 |
| | *legacy* | Purchases **prior to 2026-08-20** are **"Legacy Subscriptions"** — recurring, *"renew every 30 days at the price you originally paid"*, cancellable with ≥3 business days' notice. Help centre gives the cutover as **2026-08-25** instead (§4.1) | [Terms §2, §6.1.2](https://myfundedfutures.com/terms); [Inactivity Rule article](https://help.myfundedfutures.com/en/articles/16596524-inactivity-rule-one-time-payment-model) |
| **3** | **reset fee** | **NOT PUBLISHED.** MFFU documents *what* a reset is (*"restore your trading account to its original state… does not extend the life of your evaluation account"*) and that legacy subscribers got *"a reset credit if your evaluation account is not breached at the time of the rebilling (First month only)"* — but **publishes no price anywhere reachable without a login.** Tried: help-centre search `q=reset` (10 articles, no pricing); the four plan pages (string "reset" absent); Terms; Cancellation & Refund Policy (mentions resets only as non-refundable); `/challenge` and `/stats` (both redirect to login); the "Flex Plan – Sim Funded Reset" article, which now 404s. Secondary sources give **mutually contradictory** figures — $100 flat, "from $77", "$157 for a Rapid 50K", "$399/$499 for funded resets" — logged in Sources, **not adopted** | [Resets vs Renewals](https://help.myfundedfutures.com/en/articles/10244720-understanding-the-difference-between-account-resets-and-renewals); negative searches logged below |
| **4** | **activation / funded-account fee** | **$0, universally and explicitly.** *"all MFFU plans, regardless of account size, come with $0 activation fee."* Repeated in every plan article and on every plan page | [Activation fees article](https://help.myfundedfutures.com/en/articles/12398151-does-myfundedfutures-charge-activation-fees) |
| | *refund* | Refund available only if **no trades placed**, account active, requested **within 14 days**; refund = *"the amount paid minus a non-refundable USD $75.00 fee"*. Crypto purchases non-refundable. Breached accounts ineligible | [Cancellation & Refund Policy §1](https://myfundedfutures.com/cancellation) |

**One-time-payment note for the cost model:** there is no monthly carry on a new evaluation, but
there *is* a hard clock — §7 of the Terms, *"If a User does not execute at least one (1) trade per
seven (7) consecutive calendar day period… the Company may… deem the applicable account dormant,
close it, and treat such closure as a breach of these Terms."* **Dormancy is contractually a
breach**, not a pause.

### B — evaluation geometry

| # | field | value | source |
|---|---|---|---|
| **5** | **profit target** | Uniform **6% of account size** on every plan and size: 25K → **$1,500**; 50K → **$3,000**; 100K → **$6,000**; 150K → **$9,000**. **Exception:** Pro 50K with the free **One-Day Add-On** → **$4,000** (8%) | [Traders Evaluation Simplified](https://help.myfundedfutures.com/en/articles/11802636-traders-evaluation-simplified); [Pro 1Day Addon](https://help.myfundedfutures.com/en/articles/12879226-pro-plan-1day-addon) |
| **6** | **phases** | **One evaluation phase**, then a **Sim-Funded** phase, then (conditionally) a **Live** phase. MFFU calls it *"The Three Stages"*. Payouts begin in Sim-Funded; live capital is a separate, discretionary third stage | [Mastering the MFFU Evaluation](https://help.myfundedfutures.com/en/articles/11553890-mastering-the-mffu-evaluation-your-guide-to-funded-trading) |
| **7** | **drawdown TYPE (evaluation)** | **End-of-day trailing on EVERY plan's evaluation, without exception** — Rapid, Rapid EOD, Builder, Pro, Flex all list "Max EOD Drawdown / EOD Trailing" for the eval. *"We do not have a daily drawdown but we will have a Max EOD (End of Day) Drawdown."* **Intraday trailing appears only in the Rapid funded stage** (field 15) | [EOD Drawdown Explained](https://help.myfundedfutures.com/en/articles/8348565-end-of-day-eod-drawdown-explained); [Traders Evaluation Simplified](https://help.myfundedfutures.com/en/articles/11802636-traders-evaluation-simplified) |
| **8** | **drawdown amount** | 25K → **$1,000** (4%); 50K → **$2,000** (4%); 100K → **$3,000** (3%); 150K → **$4,500** (3%) — so the barrier is **proportionally tighter on the larger sizes**. **Builder 50K Add-On is the only variant: $1,500** (3%), sold at a lower price. Starting floor is stated absolutely: Builder 50K *"Starting Minimum Balance $48,000"*, Add-On *"$48,500"*, Builder 25K *"$24,000"* | [Builder 50k](https://help.myfundedfutures.com/en/articles/14290805-builder-plan-50k-a-comprehensive-guide); [Builder 25k](https://help.myfundedfutures.com/en/articles/15862870-builder-plan-25k-a-comprehensive-guide) |
| **9** | **drawdown BASIS — open equity or closed balance** | **OPEN EQUITY.** Verbatim, evaluation: *"You must be aware that open equity losses are taken into consideration when calculating whether or not the account failed on this rule. This means that if an open position dips your account balance below the minimum account balance, your evaluation attempt will fail."* Builder restates it: *"Open equity losses are counted when determining whether your account has breached the rule at the end of the trading day."* **So the floor can be breached intraday on unrealised loss even though it only *trails* at the close.** Rapid funded goes further — the floor also *ratchets* on unrealised gain: *"the trailing drawdown is calculated intraday based on your peak balance, which includes both realized and unrealized gains"* | [EOD Drawdown Explained](https://help.myfundedfutures.com/en/articles/8348565-end-of-day-eod-drawdown-explained); [Builder 50k](https://help.myfundedfutures.com/en/articles/14290805-builder-plan-50k-a-comprehensive-guide); [Intraday Drawdown Explained](https://help.myfundedfutures.com/en/articles/12802721-intraday-drawdown-explained) |
| **10** | **does the trailing floor LOCK, and where** | **YES, permanently, at starting balance + $100.** *"the Max EOD trailing locks in at $100 plus the initial starting balance."* Worked examples given verbatim: *"50k is 52k +$100 which is 52.1k … 100k is 103k +$100 which is 103.1k … 150k is 154.5k +100 which is 154.6k"* — i.e. **the lock triggers when the balance reaches `start + MLL + $100`, and the floor then rests at `start + $100` forever.** Rapid 25K eval states it directly: *"Once your trailing Max Loss reaches $25,100, it locks there… If your balance drops below $25,100 after the lock -> the account is breached."* Builder: *"The MLL locks permanently once it reaches $100 above the starting balance."* | as above, plus [Rapid 25k](https://help.myfundedfutures.com/en/articles/14116402-rapid-plan-25k-a-comprehensive-look) |
| **11** | **daily loss limit** | **NONE on Rapid, Rapid EOD, Pro, Builder 25K, Flex 25K/50K (default).** *"We do not have a daily drawdown."* **Builder 50K (both MLL variants): $1,000 — and it is a SOFT PAUSE, not a breach**: *"If intraday losses reach $1,000: Trading is paused for the remainder of the day. The account is not breached."* **Flex 50K:** identical $1,000 soft pause available as a **paid checkout add-on**, at a lower plan price. Builder's DLL is described as *"a coaching mechanism, not a kill switch."* Basis of the soft pause is stated as **intraday**, i.e. open equity | [Builder 50k](https://help.myfundedfutures.com/en/articles/14290805-builder-plan-50k-a-comprehensive-guide); [Flex 50k](https://help.myfundedfutures.com/en/articles/15072271-flex-plan-50-000-a-comprehensive-guide) |
| **12** | **minimum trading days** | **Builder: 1 day.** **Rapid, Pro, Flex: 2 days.** **Rapid EOD: 4 days.** Pro 50K One-Day Add-On: **1 day** (with the raised $4,000 target). *Separately*, the funded phase imposes its own per-cycle day counts — Builder **2 qualifying days per payout cycle**, Flex **5 winning days per cycle** (field 18) | [Traders Evaluation Simplified](https://help.myfundedfutures.com/en/articles/11802636-traders-evaluation-simplified); [Rapid EOD 50k](https://help.myfundedfutures.com/en/articles/16158363-rapid-eod-50k-a-comprehensive-look) |
| **13** | **time limit / maximum days** | **NONE.** *"Duration: Flexible, with no fixed max number of trading days."* Under the one-time-payment model there is no renewal clock either. **The only time constraint is the 7-consecutive-calendar-day inactivity rule**, which applies to evaluation *and* sim-funded accounts and is contractually treated as a breach | [Mastering the MFFU Evaluation](https://help.myfundedfutures.com/en/articles/11553890-mastering-the-mffu-evaluation-your-guide-to-funded-trading); [Terms §7](https://myfundedfutures.com/terms) |
| **14** | **position-size cap and scaling** | **No scaling on any evaluation** — *"Scaling rules are not present in the evaluation."* Full size from bar one. Evaluation caps: **Rapid** 25K 3/30, 50K 5/50, 100K 8/80, 150K 10/100 (mini/micro). **Rapid EOD** 25K 2/20, 50K 3/30. **Builder** 25K 2/20, 50K 4/40. **Pro** 50K 3/30, 100K 6/60, 150K 9/90. **Flex** 25K 2/20, 50K 3/30. **Balance-triggered scaling exists only in the Flex funded stage**: 50K → $0–1,499: 1 mini; $1,500–1,999: 2; $2,000+: 3. Exceeding the cap *"can result in a breach of the trading account"* | [Traders Evaluation Simplified](https://help.myfundedfutures.com/en/articles/11802636-traders-evaluation-simplified); the four `/plans/*` pages; [Flex 50k](https://help.myfundedfutures.com/en/articles/15072271-flex-plan-50-000-a-comprehensive-guide) |

### C — funded-phase geometry

**Field 15 is where the plans separate. Given per program.**

| # | field | **Rapid (intraday)** | **Rapid EOD** | **Builder** | **Pro** | **Flex (disc.)** |
|---|---|---|---|---|---|---|
| **15** | **funded drawdown, where it differs from eval** | **Starting balance $0.** MLL distance unchanged ($1,000/$2,000/$3,000/$4,500) but **type flips to INTRADAY trailing** — *"Your Max Loss trails your account equity high-water mark during the day"*, ratcheting on **realised *and* unrealised** highs. Floor locks at **$100** | **Starting balance $0.** MLL distance unchanged, **type stays END-OF-DAY**: *"It does not move intraday – only at the close of each trading session."* Floor locks at **$100** | **Starting balance $0**, floor starts at **−$2,000** (or −$1,500 / −$1,000). **EOD trailing**, open-equity-tested at the close. Locks at **$100** | **Starting balance retained** — MLL quoted as $2,000/$3,000/$4,500 **EOD trailing** against the account size; after first payout *"MLL moves to $50,100 / $100,100 / $150,100 and remains static"* | **Starting balance $0**, floor at **−$1,000 / −$2,000**. **EOD trailing.** After first payout MLL moves to **$100** and is *"fixed permanently"* |
| **16** | **consistency rule** | **Eval: 50%.** Funded: **NONE** | **Eval: 30%.** Funded: **NONE** | **Eval: NONE.** **Payout stage: 50%** | **Eval: 50%** (**none** on the One-Day Add-On). Funded: **NONE** | **Eval: 50%.** Payout stage: **NONE** |
| **17** | **profit split** | **90 / 10** (since 2026-01-12) | **90 / 10** | **80 / 20** | **80 / 20** | **80 / 20** |
| **18** | **first-payout eligibility** | **24 h after first trade**, buffer cleared, ≥ $500 | Buffer cleared; then **$500 net profit since last payout** ($250 on 25K) | **48 h after first trade**, buffer cleared, **≥ 2 qualifying days**, ≥ $500 net above buffer ($250 on 25K) | **14 calendar days from first trade**, buffer cleared, ≥ $1,000 | **5 winning days ≥ $150 each** (25K: ≥ $100), **≥ $500 total net profit** |
| **19** | **payout cap per withdrawal** | **NO CAP** | **NO CAP** — *"There is no cap on how much you can request per payout cycle."* | **$2,000 flat** (50K) / **$1,000 flat** (25K), **max 5 sim payouts** | **$100,000** (see §4.3 on "per cycle" vs "per user") | **50% of total profits**, hard-capped **$2,000** (50K) / **$1,000** (25K), **max 5 sim payouts** |
| **20** | **frequency; minimum** | **Daily** (every 24 h); min **$500** | **Daily**; min **$500** | **Every 48 h**; min **$500** (50K) / **$250** (25K) | **Every 14 calendar days**; min **$1,000** | Per cycle of 5 winning days; min **$500** (50K) / **$250** (25K) |
| **21** | **does a payout reduce/reset the buffer** | **Locks the floor at $100 and it never trails again** — so every subsequent withdrawal is a straight reduction of the surviving cushion | same | *"After your first payout, the Max Loss Limit resets to $100"* | *"After first payout, MLL moves to $50,100 and remains static"* | *"MLL moves to $100. MLL becomes fixed permanently after the first payout"* |
| **22** | **hard vs soft breach** | see below | | | | |

**Field 19, restated for the model.** The distinction that matters to D379 §4 is not the cap size but
**whether the payout stream terminates**. Rapid and Rapid EOD are uncapped and non-terminating —
daily draws, forever, until breach. **Builder and Flex terminate at 5 sim payouts**, at which point
the trader is *forced* into a live account with different parameters (Builder live: $1,000 DLL, EOD
trailing, *"static once MLL reaches $0"*). Pro terminates at the $100,000 ceiling, with the excess
*converted to live balance rather than paid* — capped at **$5,000 / $7,500 / $10,000** by size, and
*"Remaining profits are forfeited."*

**Field 22 — what ends the account.**

- **Hard breach (account over, no reset path stated):** touching the Maximum Loss Limit — including
  on **open equity**. Rapid plan page, verbatim: *"If you breach the max drawdown on a Rapid
  account, the account ends and you'll need to start a new evaluation. There is no reset — the max
  drawdown is a hard line."* Live: *"Reaching the Maximum Loss Limit results in immediate Live
  account closure."*
- **Also hard:** exceeding the contract cap (*"can result in a breach"*); failing to flatten before
  the 4:10 p.m. ET auto-close on holiday sessions (*"Failure to close the positions before the
  market closes will result in breaching of the account"*); trading on T1 news on a restricted
  account; hedging; trading within 2% of a CME price limit; **7 days without a trade** (Terms §7
  deems dormancy a breach).
- **Soft (account survives):** the Builder / Flex-add-on **$1,000 DLL is an explicit soft pause** —
  *"Trading is paused for the remainder of the day. The account is not breached."* Missing the
  **consistency** threshold is likewise **not** a breach — *"Exceeding the 50% consistency target
  does not breach the account. Instead, traders… simply need to trade additional days until
  consistency is met."*
- **Discretionary termination:** Terms §17.1 — *"The Company may suspend, restrict, or terminate
  your access… at any time and for any reason"*; §16.2.3 permits *"Withholding or forfeiture of
  funds, payouts, or rewards"*; §23.2.1 permits removing offending trades from history and
  cancelling all services *"without any compensation or refunds."*
- **Post-breach cooldown (live only):** a live MLL breach triggers a **21-calendar-day cooldown** in
  which all sim trading, new evaluations, resets and purchases are prohibited.

**Consistency rule, exact wording and threshold (field 16 in full).**

- *Evaluation, Rapid/Pro:* **50%**, computed as *"Total profit target / 2 = Max Daily Profit"* — no
  single day may exceed half the total evaluation profit. Not a breach; it just delays the pass.
  **Pro One-Day Add-On: no consistency rule.**
- *Evaluation, Rapid EOD:* **30%** — *"there is a 30% consistency rule in the evaluation phase of
  the Rapid EOD Plan, and it can be passed in as little as 4 days."*
- *Evaluation, Builder:* **none.**
- *Payout stage, Builder only:* **50%**, defined against the *cycle*, not the target — *"your single
  largest profit day cannot represent more than 50% of your total profits in the cycle. This
  calculation resets after each approved payout."* Worked example given: *"If your total net profits
  since the last payout are $1,000, your best single day cannot exceed $500."*
- *Everywhere else in the funded phase:* **none.** But Terms §12.4 imposes an unquantified
  behavioural standard — *"maintaining consistency in position sizing, trade frequency, and overall
  risk exposure"*, with §12.4.1–3 naming *"substantially larger position sizes than typical for your
  trading history"* as a violation. **That is a discretionary consistency rule with no published
  threshold**, and it sits above the numeric one.

### D — disclosure

| # | field | value | source |
|---|---|---|---|
| **23** | **published pass-rate / payout statistics** | **NOT PUBLISHED at the primary tier as of 2026-09-08.** MFFU operates a `/stats` page, but **it redirects to the login wall** when fetched (verified in a rendering browser; the raw HTML is an empty shell with only a `<title>`). Nothing on `/`, `/why-us`, `/how-it-works` or `/disclaimer` carries a number — only *"Trusted by over 100,000 traders"* and *"A track record of paying traders consistently and transparently."* **Secondary sources attribute a specific figure set to MFFU** — *"Across evaluations between January 2024 and July 2025, MFFU reports that 20.35% of evaluation accounts passed, 43.41% of participants reached the funded stage at some point, 28.56% of funded traders earned at least one payout, and 1.01% advanced to a live account"* — with no URL behind it; I could not reach a first-party publication of those numbers. Payout totals ($126M / 56,937 payouts; $180M / 114,000+) are likewise secondary and mutually inconsistent. **All of this is lane 07 material; nothing here is adopted** | `/stats` (login-gated, acc. 2026-09-08); [daytradingz](https://daytradingz.com/my-funded-futures-review/) for the attributed figures |
| **24** | **terms version / last-updated, and the URL** | **The Terms carry NO version number and NO last-updated date.** Only footer *"© 2023-2026"* and an internal date anchor — *"prior to August 20, 2026"* — that dates the current revision to on/after 2026-08-20. §28.4: *"the Company reserves the right… to modify, amend, or update these Terms at any time, with or without notice."* **Help-centre articles carry per-article dates**, which are the only versioning available: EOD Drawdown "Updated over 2 weeks ago"; Intraday Drawdown "January 8, 2026"; Payout Policy "Updated over 2 weeks ago"; Rapid 100k/150k "July 1, 2026"; Pro Highlights "June 30, 2026"; Builder 25k "July 14, 2026"; Flex 25k "August 5, 2026"; Live FAQ "November 10, 2025". **Critically: the document that actually binds the funded stage is not public** — Terms §29 gives precedence to *"the Simulated Trader Agreement and its Appendices"* over the Terms themselves, and neither is published. Probed `/simulated-trader-agreement`, `/sim-funded-agreement`, `/trading-rules`, `/rules` → all **404** | [Terms](https://myfundedfutures.com/terms); help-centre article headers |

---

## 3. The geometry restated in D379's terms

For a **Rapid 50K** (the modal cell), on a one-time **$209** (promo $105):

| stage | balance origin | barrier | barrier moves | monitoring |
|---|---|---|---|---|
| evaluation | $50,000 | $48,000 | up, at the close, to `EOD high − 2,000`; **locks at $50,100** | breach tested on **open equity** |
| target | $53,000 (6%) | — | — | — |
| sim funded | **$0** | **−$2,000** | up, **continuously**, to `equity HWM − 2,000`, HWM including unrealised; **locks at +$100** | **open equity, intraday** |
| payout gate | $2,100 buffer, then $500 min, daily, 90/10 | | | |
| post-first-payout | balance − withdrawal | **$100, static** | never | closed balance vs a static floor |

So the object is a **two-barrier down-and-out**: a $2,000 barrier below a $50,000 start for the
eval, then a *fresh* $2,000 barrier below a **$0** start for the funded phase, with the second
barrier ratcheting on unrealised gains until the $2,100 buffer is built. **The trader pays $209 for
a claim that requires clearing 6% and then re-clearing $2,100 before a single dollar is
withdrawable, on an open-equity barrier that tightens as he wins.**

Two asymmetries worth carrying into the model:

1. **The ratchet is faster than the payout.** On Rapid funded, the floor follows *unrealised* highs,
   so an intraday spike that later retraces raises the barrier permanently but adds nothing
   withdrawable. Rapid EOD removes exactly this term at the same price — it is the clean A/B.
2. **The buffer is a haircut, not a deposit.** It is never returned in full: on live breach it pays
   at 50% (< 30 sim trading days) or 80% (≥ 30), *"subject to standard profit-sharing
   arrangements"*, i.e. the split applies on top.

---

## 4. Contradictions and ambiguities — reported, not resolved

**4.1 The one-time-payment cutover date disagrees between two primary sources.**
Terms §2 and §6.1.2 both say **"prior to August 20, 2026"**. The help-centre article says
**"Effective August 25, 2026, MyFundedFutures will transition to a one-time payment model"**. Five
days apart, both first-party. Not resolved.
[Terms](https://myfundedfutures.com/terms) · [Inactivity Rule article](https://help.myfundedfutures.com/en/articles/16596524-inactivity-rule-one-time-payment-model)

**4.2 When the Rapid floor locks — automatically, or only after the first payout.**
The help article and the plan-page rules table say the lock is automatic on reaching the level:
*"Once your trailing Max Loss reaches $100, it locks there."* The **same plan page's FAQ** says
*"once your balance is +$100 above your starting balance **after your first payout**, the floor locks
and stops trailing upward permanently."* These are different rules — the second makes taking a
payout a *precondition* for freezing the barrier. Pro's page states the payout-conditional version
unambiguously: *"After your first approved payout, the MLL locks permanently at your starting
balance plus $100… Until that first payout, the MLL continues to trail."* **For the valuation model
this is a live fork: whether the barrier freeze is automatic or purchased.**
[Rapid 50k article](https://help.myfundedfutures.com/en/articles/13134709-rapid-plan-50k-a-comprehensive-look) · [/plans/rapid](https://myfundedfutures.com/plans/rapid) · [/plans/pro](https://myfundedfutures.com/plans/pro)

**4.3 Pro's $100,000 cap: per cycle, per user, or lifetime.**
The plan page's rules table: **"Max Payout per User $100,000"**. The same page's how-it-works:
*"up to $100,000 maximum per cycle."* The plan-selector blurb: *"Up to $100,000 per payout cycle."*
The help article: *"Maximum Request in Sim-Funded stage: $100,000"* and *"Request up to $100,000
(per user)"* in the same bullet list. The live-transition text — *"Traders who achieve profits in
excess of $100,000 maximum payout will have those excess profits moved to their live account"* —
reads as a **lifetime sim ceiling**, which is the interpretation that fits the mechanics. Reported
as unresolved.
[/plans/pro](https://myfundedfutures.com/plans/pro) · [Payout Policy Overview](https://help.myfundedfutures.com/en/articles/13745661-payout-policy-overview-best-and-fastest-prop-firm-payouts) · [Pro Highlights](https://help.myfundedfutures.com/en/articles/11802674-pro-plan-sim-funded-and-live-account-highlights)

**4.4 Pro's funded micro-contract cap is almost certainly a typo, and it is repeated.**
Both the Pro article and the Pro plan page give **"5 mini / 5 micro"**, **"10 / 10"**, **"15 / 15"**.
Every other plan states micros at 10× minis. Whether Pro genuinely caps micros at 5 or the tables
mean 50 is **not determinable from published text**. Flagged, not guessed.

**4.5 Builder 25K's FAQ contains a copy-paste from the 50K article.**
*"You need at least $250 in net profit above the buffer. For example, on the $2,000 option, your
account balance must reach at least $2,600 before you can submit your first payout request ($2,100
buffer plus $500 net profit above it)."* The 25K plan's actual numbers are a $1,100 buffer and $250,
i.e. $1,350. The table in the same article is internally consistent; the FAQ paragraph is not.

**4.6 Builder 25K daily loss limit.** The Builder 50K article and the Traders-Evaluation-Simplified
table both give Builder a *"$1,000 Soft-Pause"* DLL; the **Builder 25K** article's tables and FAQ
both say **"None"**, and the Builder plan page's by-size table agrees (25K: None; 50K: $1,000 soft
pause). Treating it as size-specific rather than contradictory, but recording it.

**4.7 Rapid live-account floor: $0 or $100.** Sim-funded locks at **+$100**; the Rapid **live**
tables say *"Max Loss threshold stops at $0"* and *"Rapid Live accounts start at $0, so balances may
go negative until the maximum loss limit trails up to $0."* Builder live says *"Static once MLL
reaches $0."* Flex live instead states a **$156** minimum balance. Three different live floors
across three plans.

**4.8 Account-limit tables disagree.** Traders-Evaluation-Simplified says up to **5** sim-funded
accounts on $25K/$50K sizes; the Moving-to-Sim-Funded article overrides with plan-specific caps
(Rapid EOD 25K/50K: 3; Builder 25K: 2; Builder 50K: 1) and notes *"These plan-specific limits apply
even if the general $25K/$50K allowance would otherwise permit more accounts."* The Rapid EOD
article separately says *"Max # of Funded Accounts: Three (3)."* Latest-dated source wins on its
face, but they are published concurrently.

**4.9 Rapid EOD 50K contract cap.** The Rapid EOD 50K article gives **3 mini / 30 micro** in both
eval and sim-funded tables; the general Rapid plan page's by-size table gives 50K as **5 / 50**
(sim) and **4 / 40** (live). The EOD variant appears to carry a tighter cap than standard Rapid at
the same size, but the two documents are not cross-referenced.

**4.10 Payout processing time.** *"most payout requests are approved instantly"* and *"Most payouts
are approved instantly. If a manual review is required, processing may take up to 6 to 12 business
hours"* (Payout Policy) vs *"All payouts are processed in 6-12 business hours excluding holidays"*
(First Payout guide) vs *"About 80% of payouts auto-approve"* (Rapid page).

**4.11 The refund terms differ between the policy page and the help centre.**
`/cancellation` §1.2: *"Eligible refunds will be issued as: The amount paid minus a non-refundable
USD $75.00 fee, which covers technology, platform, and market data costs."* The help article:
*"Refund Policy — Risk-Free if You Haven't Traded. Eligibility: A full refund is available when no
trades have been placed."* One says full, one says minus $75, on the same 14-day untraded condition.
The policy page is the one incorporated into the Terms by reference (§8), so it presumably controls
— but both are first-party and current.
[/cancellation](https://myfundedfutures.com/cancellation) · [Refund & Cancellation article](https://help.myfundedfutures.com/en/articles/11542523-refund-cancellation-policy-transparent-and-trader-first)

**4.12 One-page-content note, logged per the safety rule.** No fetched page contained text directed
at an automated reader or instructing an agent to take an action. Every plan page carries
call-to-action buttons ("Start Rapid Evaluation", "Take the Challenge") and a discount code
(`CLUB`, "4 uses of 50% off") — these are marketing copy addressed to a human purchaser, were
treated as data, and **nothing was purchased, signed up for, or clicked through**.

---

## 5. Explicitly NOT PUBLISHED

| field | what is missing | what was tried |
|---|---|---|
| **3** reset fee | any price, for evaluation or funded resets | help-centre search `q=reset`; all 4 plan pages; Terms; Cancellation policy; MyFundedClub article; Navigating-Your-Dashboard article; the (now-404) Flex Sim-Funded Reset article; `/challenge` and `/stats` (both login-gated). Secondary claims range $77–$499 and contradict each other |
| **23** statistics | first-party pass rate, funded rate, payout rate, payout total | `/stats` — **redirects to the login wall**; `/`, `/why-us`, `/how-it-works`, `/disclaimer` carry no numbers; site-restricted search returned no transparency report |
| **24** terms versioning | version number or last-updated date on the Terms | full read of `/terms`; only the embedded "prior to August 20, 2026" dates it |
| **—** the binding funded-stage contract | **the Simulated Trader Agreement and its Appendices**, which Terms §29 places *above* the Terms in precedence | probed `/simulated-trader-agreement`, `/sim-funded-agreement`, `/trading-rules`, `/rules` → all 404; not linked from Terms, Disclaimer, or the help centre. **Presumed to be presented at Riseworks signature on first payout.** This is the single largest documentary gap: **the numbers in this file all come from marketing and help-centre pages, not from the instrument that governs them.** |

---

## Sources

All accessed **2026-09-08**. Tier per `00-SCHEMA.md` §4.

### Primary — MyFundedFutures first-party

| URL | accessed | tier | what I sought | what it yielded |
|---|---|---|---|---|
| https://myfundedfutures.com/terms | 2026-09-08 | primary | fields 2, 13, 22, 24 | **HIT.** §2 defs incl. "Legacy Subscription… prior to August 20, 2026"; §6.1 one-time vs legacy billing; §7 dormancy = breach at 7 days; §12.4 unquantified consistency standard; §16.2.3 forfeiture; §17 discretionary termination; §29 Order of Precedence naming the unpublished Simulated Trader Agreement. **No version or last-updated date.** No numeric drawdown/payout terms at all |
| https://myfundedfutures.com/cancellation | 2026-09-08 | primary | fields 3, 4 | **HIT.** 14-day refund window, no trades placed, **minus a $75 non-refundable fee**; resets explicitly non-refundable; crypto non-refundable. **No reset price** |
| https://myfundedfutures.com/disclaimer | 2026-09-08 | primary | field 23 | Partial. Confirms all stages simulated, "no real capital is deployed at any stage", payout eligibility governed by the Simulated Trader Agreement. **No statistics** |
| https://myfundedfutures.com/plans | 2026-09-08 | primary | field 1 | **HIT.** Current lineup = Rapid, Rapid EOD, Builder, Pro. **Flex absent**, confirming discontinuation |
| https://myfundedfutures.com/plans/rapid | 2026-09-08 | primary | 1,2,5–14,15–21 | **HIT.** Full by-size rules table (eval / sim-funded / live / payout policy); JSON-LD prices $145/$209/$356/$463 (SKUs `…OTP`); "One-time payment, no renewals"; FAQ stating the lock is post-first-payout (**contradiction 4.2**); "no reset — the max drawdown is a hard line" |
| https://myfundedfutures.com/plans/rapid-eod | 2026-09-08 | primary | 1,2,7,15,19 | **HIT.** JSON-LD $145 (25K) / $209 (50K); promo $73; sizes 25K/50K only |
| https://myfundedfutures.com/plans/builder | 2026-09-08 | primary | 1,2,19 | **HIT.** JSON-LD $105 (25K) / $153 (50K); the **five-rung, $2,000-per-rung ladder** laid out step by step; live broker named as **Blue Row Capital** |
| https://myfundedfutures.com/plans/pro | 2026-09-08 | primary | 1,2,19,21 | **HIT.** JSON-LD $265/$401/$557; "Max Payout per User $100,000" vs "per cycle" elsewhere (**contradiction 4.3**); explicit statement that the Pro MLL lock is post-first-payout |
| https://myfundedfutures.com/why-us | 2026-09-08 | primary | field 23 | **NOTHING numeric.** "Trusted by 100,000+", "a track record of paying traders consistently and transparently", testimonials. No stats |
| https://myfundedfutures.com/ and /how-it-works | 2026-09-08 | primary | 1, 23 | Thin. Homepage names Rapid and Pro, "$100K in payouts", "90% of profits", promo code CLUB. No rules detail |
| https://myfundedfutures.com/stats | 2026-09-08 | primary | field 23 | **BLOCKED — redirects to the login wall.** Raw fetch returns a title-only shell; rendered in a browser it becomes "Login \| MyFundedFutures". **Did not sign in or sign up.** Field 23 marked NOT PUBLISHED on this basis |
| https://myfundedfutures.com/challenge | 2026-09-08 | primary | fields 1–4 | **NOTHING** — client-rendered shell, then login-gated. Pricing recovered from the `/plans/*` JSON-LD instead |
| https://myfundedfutures.com/{simulated-trader-agreement, sim-funded-agreement, trading-rules, rules} | 2026-09-08 | primary | the governing funded-stage contract | **ALL 404.** The Simulated Trader Agreement, which Terms §29 ranks *above* the Terms, is not published |
| https://myfundedfutures.com/{pricing, transparency, statistics, testimonials} | 2026-09-08 | primary | fields 2, 23 | **404** (pricing, transparency, statistics, testimonials). Recorded so they are not re-probed |

### Primary — MFFU help centre (Intercom)

| URL | accessed | tier | what I sought | what it yielded |
|---|---|---|---|---|
| https://help.myfundedfutures.com/en/ | 2026-09-08 | primary | index | **HIT.** 12 collections; gave every collection id used below |
| .../articles/8348565-end-of-day-eod-drawdown-explained | 2026-09-08 | primary | **fields 7, 9, 10** | **DECISIVE.** *"open equity losses are taken into consideration"*; *"the Max EOD trailing locks in at $100 plus the initial starting balance"*; worked lock examples 52.1k / 103.1k / 154.6k |
| .../articles/12802721-intraday-drawdown-explained | 2026-09-08 | primary | **fields 7, 9, 15** | **DECISIVE.** Rapid funded trails on *"peak balance, which includes both realized and unrealized gains"*; worked $50,000/$2,000 example; Tradovate column names for monitoring it |
| .../articles/11994562-consistency-rule-at-my-fundedfutures | 2026-09-08 | primary | **field 16** | **HIT.** 50% for Rapid & Pro evals; *"Total profit target / 2 = Max Daily Profit"*; **not a breach** — trade more days; Pro One-Day has none |
| .../articles/13745661-payout-policy-overview-… | 2026-09-08 | primary | **fields 17–21** | **DECISIVE — the single richest page.** Per-plan buffers, cadences, minimums, splits, the Builder $1,000/$2,000 per-request caps, Pro $100,000, *"After your first payout, the Max Loss Limit resets to $100"*, Pro 60%-of-profits pre-buffer withdrawal, all three live-transition triggers |
| .../articles/13134709-rapid-plan-50k-… | 2026-09-08 | primary | 5–21 for Rapid 50K | **HIT.** Eval + sim-funded parameter tables; *"Initial Balance: $0"*; $2,100 buffer; lock at $100 |
| .../articles/14116402-rapid-plan-25k-… | 2026-09-08 | primary | Rapid 25K | **HIT.** Adds the **eval-side lock statement**: *"Once your trailing Max Loss reaches $25,100, it locks there"* |
| .../articles/13286542-rapid-plan-100k-… | 2026-09-08 | primary | Rapid 100K | **HIT.** $6,000 target, $3,000 MLL, $3,100 buffer, 8/80 |
| .../articles/13286582-rapid-plan-150k-… | 2026-09-08 | primary | Rapid 150K | **HIT.** $9,000 target, $4,500 MLL, $4,600 buffer, 10/100 |
| .../articles/16158363-rapid-eod-50k-… | 2026-09-08 | primary | **field 19** | **DECISIVE for 19.** *"There is no cap on how much you can request per payout cycle."* Plus the 30% eval consistency and 4-day minimum unique to Rapid EOD |
| .../articles/16727601-rapid-eod-25k-… | 2026-09-08 | primary | Rapid EOD 25K | **HIT.** *"Max Payout per Cycle: No cap"*; $1,100 buffer; $250 inter-payout profit gate |
| .../articles/13134718-understanding-rapid-live | 2026-09-08 | primary | field 15 (live) | **HIT.** Live tables; $10,000-in-a-day auto-transition with **excess forfeited**; live floor "stops at $0" |
| .../articles/13286746-rapid-plan-reserve-program-… | 2026-09-08 | primary | fields 19, 21, 22 | **HIT, and materially so.** Reserve ≤ $5,000; performance-bonus unlock at 20 profitable live days + $10,000 gross live payouts; **buffer recovered at only 50% (< 30 sim days) or 80% (≥ 30) on live breach**; 21-day cooldown |
| .../articles/11802674-pro-plan-sim-funded-and-live-… | 2026-09-08 | primary | Pro, **field 21** | **DECISIVE for Pro 21.** *"After first payout, MLL moves to $50,100 and remains static"*; 60% pre-buffer withdrawal; live funding $2,000–$5,000 static; the 20-winning-day / 3-payout unlock of the live allocation down to $140 |
| .../articles/12879226-pro-plan-1day-addon | 2026-09-08 | primary | fields 5, 12, 16 | **HIT.** $4,000 target, one-day pass, **no consistency rule** |
| .../articles/8694840-balancing-freedom-…-consistency-for-sim-funded-pro-… | 2026-09-08 | primary | field 16 | Qualitative only. No threshold; lists consequences (restrictions, penalties, termination) for the *unquantified* consistency policy |
| .../articles/14290805-builder-plan-50k-… | 2026-09-08 | primary | **fields 2, 8, 11, 16, 19, 22** | **DECISIVE.** Prices $153/$125 and the two MLL variants; *"account begins at $0… can go negative"*; **$1,000 soft-pause DLL that does not breach**; the 50% payout-stage consistency rule with worked example; $2,000/5-payout ladder; 21-day live cooldown; *"Open equity losses are counted"* |
| .../articles/15862870-builder-plan-25k-… | 2026-09-08 | primary | Builder 25K | **HIT**, plus **contradiction 4.5** (copy-pasted 50K numbers in the FAQ) and **4.6** (DLL "None") |
| .../articles/15070844-flex-plan-25-000-… | 2026-09-08 | primary | Flex 25K | **HIT.** *"Effective August 5th… the Flex plan will be discontinued."* 5-winning-day gate, 50%-of-profits cap at $1,000, MLL→$100 after first payout |
| .../articles/15072271-flex-plan-50-000-… | 2026-09-08 | primary | Flex 50K | **HIT.** Paid **$1,000 soft-pause DLL add-on**; balance-tiered contract scaling; cap cut from $5,000 to $2,000 |
| .../articles/11802636-traders-evaluation-simplified | 2026-09-08 | primary | **fields 5, 7, 8, 11, 12, 14** | **DECISIVE — the master eval grid** for Builder / Rapid / Rapid EOD / Pro, all sizes, in one table. Also the account-limit rules |
| .../articles/8528339-understanding-evaluation-parameters-… | 2026-09-08 | primary | fields 7–11 | Definitional only; no numbers. Confirms MFFU uses both EOD-trailing and intraday-trailing language |
| .../articles/11553890-mastering-the-mffu-evaluation-… | 2026-09-08 | primary | **field 13** | **HIT.** *"Duration: Flexible, with no fixed max number of trading days"* — three-stage structure |
| .../articles/10244720-understanding-the-difference-between-account-resets-and-renewals | 2026-09-08 | primary | **field 3** | **PARTIAL / NEGATIVE.** Defines resets and renewals, the breached-at-rebill auto-restore, and the first-month reset credit — **but no price** |
| .../articles/12398151-does-myfundedfutures-charge-activation-fees | 2026-09-08 | primary | **field 4** | **HIT.** *"all MFFU plans, regardless of account size, come with $0 activation fee"* |
| .../articles/11542523-refund-cancellation-policy-… | 2026-09-08 | primary | fields 3, 4 | **HIT.** Full refund if untraded within 14 days (softer than the $75-deduction policy page — note the gap); crypto non-refundable; breached ineligible; chargebacks waived, AAA arbitration |
| .../articles/16596524-inactivity-rule-one-time-payment-model | 2026-09-08 | primary | **fields 2, 13** | **DECISIVE.** *"Effective August 25, 2026… one-time payment model for all new evaluation purchases"*; legacy subscribers grandfathered; 7-calendar-day inactivity closure incl. sim-funded. **Date conflicts with Terms (4.1)** |
| .../articles/16498635-moving-from-evaluation-to-sim-funded-account | 2026-09-08 | primary | fields 10, 15 | **HIT.** *"Your maximum drawdown will now lock at +$100 after the drawdown % + $100 has been reached"*; full account-limit matrix (**4.8**) |
| .../articles/11542406-guide-to-your-first-payout-… | 2026-09-08 | primary | fields 18, 20 | **HIT.** KYC + **Riseworks** rail; per-plan minimums; *"All payouts are processed in 6-12 business hours"* (**4.10**) |
| .../articles/12109396-comprehensive-faq-live-accounts-… | 2026-09-08 | primary | field 15 (live) | **HIT.** Live DLL is negotiable downward with a risk manager; no live inactivity rule; **exchange data fee charged monthly to live traders**; 11 a.m. ET payout cutoff; contracts set to 0 while a payout is pending; microscalping and DCA permitted live |
| .../articles/10101257-understanding-live-funded-account-… | 2026-09-08 | primary | field 15 | Background on the live stage; no new numeric terms |
| .../articles/8444599-fair-play-and-prohibited-trading-practices | 2026-09-08 | primary | **field 22** | **HIT.** HFT banned; automation permitted if not exploiting sim fills; **all hedging banned incl. cross-size (ES vs MES)**; no device sharing; no copy trading; profit confiscation; *"All passed evaluations are subject to review"* |
| .../articles/8230009-news-trading-policy | 2026-09-08 | primary | field 22 | **HIT.** T1 flat 2 min either side. **Restricted: Rapid Sim Funded, Pro Sim Funded. Unrestricted: all evaluations, Builder** |
| .../articles/9558251-permitted-times-to-trade | 2026-09-08 | primary | field 22 | **HIT.** 6:00 p.m.–4:10 p.m. ET; auto-flat at 4:10; **holiday sessions do NOT auto-flatten** and failure to close *"will result in breaching of the account"* |
| .../articles/9698984-2-price-limit-rule | 2026-09-08 | primary | field 22 | **HIT.** No participation within 2% of a CME price limit; enforced on **Sim Funded and Live** |
| .../articles/16130843-myfundedclub-membership-perks-… | 2026-09-08 | primary | field 3 | **NEGATIVE for price.** Points redeemable against *"new evaluations, resets"*; $2,000 rolling-12-month reward ceiling. No reset price |
| .../articles/8229980-navigating-your-dashboard | 2026-09-08 | primary | field 3 | **NOTHING** on reset pricing |
| .../collections/{5808821, 17350372, 18158247, 18640090, 19480282, 5808827, 5811873, 14650040, 13517838, 5687009} | 2026-09-08 | primary | article enumeration | **HIT** — complete article inventory per collection, which is how the article list above was built rather than by guessing slugs |
| https://help.myfundedfutures.com/en/search?q=reset | 2026-09-08 | primary | **field 3** | **NEGATIVE.** 10 articles returned, **none containing a reset price** |
| .../articles/13522130-flex-plan-sim-funded-reset | 2026-09-08 | primary | field 3 | **DEAD LINK** — returns the help-centre search fallback. Article referenced by search engines but withdrawn |

### Secondary and claims tier — consulted, **not adopted**

| URL | accessed | tier | what I sought | what it yielded |
|---|---|---|---|---|
| https://daytradingz.com/my-funded-futures-review/ | 2026-09-08 | secondary | **field 23**, field 3 | The attributed stat set — *"20.35% of evaluation accounts passed, 43.41% reached the funded stage… 28.56% of funded traders earned at least one payout, and 1.01% advanced to a live account"*, Jan 2024–Jul 2025 — credited only to *"MFFU reports"* with **no URL**. **No reset price.** Reported in field 23 as an unverified secondary attribution |
| https://proptradingvibes.com/blog/myfundedfutures-payout-proof | 2026-09-08 | claims | field 23 | **NOTHING.** Despite the title, carries **no payout total, count or pass rate** — only a Trustpilot score and the site's own 82/100 rating. Recorded so it is not re-fetched |
| search: "MyFundedFutures reset fee cost… 2026" | 2026-09-08 | claims | **field 3** | Contradictory: "from $77"; "Rapid 50K reset $157"; "$399 / $499 funded resets, 7-day window, max 2"; "$100 for any account size"; "Expert $165–$375". **All secondary, all mutually inconsistent, none adopted** |
| search: "MyFundedFutures published payout statistics…" | 2026-09-08 | claims | field 23 | Contradictory payout totals — "$126M across 56,937 payouts" vs "$180M across 114,000+". **Not adopted**; lane 07 material |
| search: "MyFundedFutures transparency report… site:myfundedfutures.com" | 2026-09-08 | secondary | field 23 | **NEGATIVE — no transparency report exists on the domain.** Only surfaced `/stats`, which is login-gated |
| search: "myfundedfutures.com FAQ… starter expert milestone" | 2026-09-08 | secondary | field 1 | Useful only as a pointer: confirmed the **July 2025 retirement of Starter / Starter Plus / Expert / Milestone**, superseded by Core/Rapid/Pro and then by the current four. Superseded by primary sources |
| https://x.com/MyFundedFutures/status/1957870177045082515 | 2026-09-08 | claims | **field 3** | **BLOCKED — HTTP 402.** X posts are not fetchable in this environment. Recorded so it is not retried |

### Dead ends, recorded so they are not repeated

1. **`/stats` is login-gated.** Do not re-probe for pass rates on the MFFU domain — verified in a
   rendering browser, not just by raw fetch.
2. **`/challenge` is a client-rendered shell.** Pricing lives in the **JSON-LD `Offer` blocks on the
   `/plans/*` pages** — that is the retrieval route.
3. **The Simulated Trader Agreement is not on the public site.** Four URL guesses all 404. It is
   almost certainly presented at Riseworks signature on first payout, i.e. only obtainable by
   holding an account through to a payout.
4. **X/Twitter returns HTTP 402** to WebFetch here. Any MFFU announcement only on X is unreachable.
5. **The reset price is not published anywhere public.** Ten distinct primary probes, all negative.
   Stop searching; it requires the dashboard.
6. **The help centre must be read through `curl` + HTML-strip, not summarising fetchers** — the
   summarising path silently conflated the lock *level* ($50,100) with the lock *trigger balance*
   ($52,100) on the single most load-bearing sentence in this lane. Verbatim retrieval is required
   for fields 9, 10 and 19.
