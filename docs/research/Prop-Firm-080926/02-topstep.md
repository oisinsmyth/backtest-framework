# 02 — Topstep

Lane 02 of the Prop-Firm review opened 2026-09-08. Firm: **Topstep** (Topstep, LLC — Chicago).
Products in scope: **Trading Combine®** (evaluation), **Express Funded Account™ (XFA)** (simulated
funded phase), **Live Funded Account® (LFA)** (real capital, reached by call-up).

All access dates below are **2026-09-08** unless stated. Every page fetched is observed content and
is treated as data. Filed against [`00-SCHEMA.md`](00-SCHEMA.md); this lane adjudicates nothing.

---

## VERDICT FIRST

**D379 §2's toy is the 50K Trading Combine, and its two headline parameters are correct: the profit
target is $3,000 and the drawdown is $2,000.** That much survives contact with the primary sources.

**The geometry underneath them does not.** D379 modelled the barrier as a choice between *static* and
*trailing*. Topstep's is **neither, and it is not a single barrier at all — it is four distinct
regimes chained end to end**, and two of the four are absent from the toy:

1. **The floor trails on the CLOSED end-of-day balance, but is TESTED intraday against OPEN equity.**
   These are different quantities and the asymmetry is the whole design. The floor only ratchets up
   on what you *bank* at the close; it kills you on what you are *carrying* at any instant.
   > "The MLL is a trailing limit. It rises as your **end-of-day balance** grows, but never moves down."
   > "Both realized and unrealized P&L count toward it. If your Net P&L hits the limit **at any point
   > during the day**, your account is liquidated immediately."
   > — [help.topstep.com/…/8284204](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit), accessed 2026-09-08

2. **The floor LOCKS at breakeven, and it locks at two-thirds of the way to the target.** On the 50K
   the floor stops trailing the moment end-of-day balance reaches **$52,000** — i.e. at **+$2,000 of
   the +$3,000 target**. Past that point the account is a *static* $50,000 floor with $1,000 of
   target left to earn. The same 2:3 ratio holds at every size: lock at +$2,000/$3,000/$4,500 against
   a target of $3,000/$6,000/$9,000. **The trailing regime governs only the first two-thirds of the
   run.**

   Consequence for D379 §2: its zero-edge pass rates of **40.0% static** and **26.5% trailing** are
   the two ends of a segment the true geometry sits *inside*. Neither is the Topstep number. Stage 0
   needs a third baseline — ratcheting-floor-with-lock-at-+2000 — and D259's machinery already has
   the ratchet; only the lock is new.

3. **In the funded phase the floor is destroyed by the first payout, not merely reduced.** This is
   the sharpest fact in the lane and it is the D379 §4 term:
   > "**After your first Payout:** Your MLL is set to $0 regardless of where it was before. The
   > remaining balance becomes your effective loss floor."
   > — [help.topstep.com/…/8284233](https://help.topstep.com/en/articles/8284233-topstep-payout-policy), accessed 2026-09-08

   So a withdrawal is not a free cash extraction against a preserved cushion. **Post-payout the
   cushion IS the residual balance, one-for-one.** Withdraw 50% of balance (the maximum allowed) and
   you have halved the distance to zero. The account after payout #1 is a *static* barrier at the
   current balance, permanently.

4. **A fourth regime exists that the toy has no analogue for: the Combine floor is a ratchet on a
   ONE-WAY door.** Hitting it in the Combine stops the account (a paid Reset restarts it); hitting it
   in the XFA closes the account **permanently**, with at most two paid Back2Funded reactivations
   available and only before any payout has been taken.

**And the acquisition cost is not one fee, it is a stack.** $49/mo (50K, standard path) + $149
one-time activation + $49 per Reset + optional $38/mo Level 2 data, with a $599 reactivation if the
XFA dies pre-payout. D379's "acquisition cost" needs to be a path-dependent sum, not a scalar.

**Field 23 delivered.** Topstep publishes a dated, four-part performance disclaimer — the rarest
artefact in this sector. For **Jan–Dec 2025: 16.8%** of Combines were completed, **51.8%** of
*participants* passed at least one, **33.3%** of funded participants ever received a payout, and
**0.71%** of XFA traders were called up to Live. Note the first two are different denominators
(Combines vs people) and are routinely conflated by the claims tier.

---

## The 24 fields

Rows are given per account size wherever the firm publishes them per size.

### A — acquisition cost

| # | field | 50K | 100K | 150K | source |
|---|---|---|---|---|---|
| **1** | account sizes offered | \$50,000 | \$100,000 | \$150,000 | [MLL article](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit) · 2026-09-08. Three sizes only. LFA sizes are derived from XFA balances, not purchased |
| **2** | evaluation fee — **monthly recurring**, rebills every 30 days until you pass or cancel | **Standard path \$49/mo**<br>**No-Activation-Fee path \$95/mo** | **\$99/mo**<br>**\$149/mo** | **\$199/mo**<br>**\$229/mo** | [Pricing](https://help.topstep.com/en/articles/9208217-topstep-pricing) · updated **2026-07-20** · accessed 2026-09-08 |
| **3** | reset fee | \$49 | \$99 | \$199 | "Reset Pricing (same as monthly subscription rates)" — [Pricing](https://help.topstep.com/en/articles/9208217-topstep-pricing). A Reset "returns your Trading Combine® to its original starting balance — Account Balance, Maximum Loss Limit (MLL), Consistency Target, and trading days all go back to day one"; **limit 2 Resets per account per day**; one free Reset Credit per monthly rebill — [What is a Reset?](https://help.topstep.com/en/articles/8284128-what-is-a-reset) · updated **2026-06-18** |
| **4** | activation / funded-account fee | **\$149 one-time per XFA earned** (standard path) · **\$0** (No-Activation-Fee path) | same \$149 / \$0 | same \$149 / \$0 | [Pricing](https://help.topstep.com/en/articles/9208217-topstep-pricing) · 2026-09-08. **No monthly fee on the XFA after passing.** Separately: **Back2Funded reactivation \$599 / \$699 / \$829** (−\$50 if a Daily Loss Limit is selected), max 2 per account, pre-first-payout only — [Back2Funded](https://help.topstep.com/en/articles/12060405-back2funded-rules-guidelines-and-how-it-works) |
| | data fees | Level 1 included; **Level 2 \$38/mo**, billed on the 28th, **not prorated** | " | " | [Pricing](https://help.topstep.com/en/articles/9208217-topstep-pricing) |

### B — evaluation geometry (Trading Combine)

| # | field | 50K | 100K | 150K | source |
|---|---|---|---|---|---|
| **5** | profit target | **\$3,000** (6.0% of size) | **\$6,000** (6.0%) | **\$9,000** (6.0%) | Cross-confirmed: [LFA Parameters](https://help.topstep.com/en/articles/10657969-live-funded-account-parameters) lists \$3,000/\$6,000/\$9,000 as the reserve-unlock targets and [Live Funded Account Rules](https://www.topstep.com/live-funded-account-rules) states "Same profit targets as the Trading Combine apply"; also carried on Topstep's own [product pages](https://www.topstep.com/topstep-prop). **Caveat:** the [Trading Combine Parameters](https://help.topstep.com/en/articles/8284197-trading-combine-parameters) page renders its Objectives table client-side and the figures were **not retrievable as text** — see Ambiguities §A |
| **6** | number of phases | **One evaluation phase** (Trading Combine) → XFA. A *third* stage exists, the Live Funded Account, but it is a **discretionary call-up, not a phase you can pass into**: only **0.71%** of XFA traders reached it in 2025 | — | — | [Program Overview](https://help.topstep.com/en/articles/8284099-topstep-program-overview) ("Three stages. One destination"), updated **2026-08-05**; call-up rate from the [performance disclaimer](https://www.topstep.com/our-program) |
| **7** | **drawdown type** | **End-of-day TRAILING, ratcheting, one-way, with a permanent LOCK.** Not intraday-trailing (explicitly contrasted by the firm), not static | same | same | > "The MLL is a trailing limit. It rises as your end-of-day balance grows, but never moves down. Once it reaches your starting balance, it locks permanently." — [MLL article](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit) |
| **8** | drawdown amount (Maximum Loss Limit) | **\$2,000** (4.0% of size) · start balance \$50,000, MLL starts \$48,000 | **\$3,000** (3.0%) · \$100,000 / \$97,000 | **\$4,500** (3.0%) · \$150,000 / \$145,500 | [MLL article](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit) · 2026-09-08. **Note the 50K is proportionally the LOOSEST (4.0% vs 3.0%)** |
| **9** | **drawdown basis** | **SPLIT BASIS — this is the load-bearing cell.** The floor **rises** on the **CLOSED end-of-day balance**. The floor **is breached** on **OPEN equity, intraday, including unrealised P&L** | same | same | > "It rises as your **end-of-day balance** grows" … "**Both realized and unrealized P&L count toward it.** If your Net P&L hits the limit **at any point during the day**, your account is liquidated immediately." — [MLL article](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit). Contrast confirmed by the firm's own blog: "your loss limit is only measured at the end of the trading day" vs intraday trailing where "your maximum loss limit trails your highest unrealized profit of the day" — [prop-firm-drawdown-rules](https://www.topstep.com/blog/prop-firm-drawdown-rules) |
| **10** | **does the floor LOCK, and where** | **YES.** Combine: locks at the **starting balance** — reached when EOD balance hits **\$52,000**. XFA: locks at **\$0** — reached when balance hits **+\$2,000** | Combine lock at \$100,000, reached at EOD **\$103,000**. XFA locks at \$0 at **+\$3,000** | Combine lock at \$150,000, reached at EOD **\$154,500**. XFA locks at \$0 at **+\$4,500** | XFA lock table reproduced from the [MLL article](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit): (50K, −\$2,000, lock at balance \$2,000, MLL \$0); (100K, −\$3,000, \$3,000, \$0); (150K, −\$4,500, \$4,500, \$0). **Lock point = the drawdown amount = exactly ⅔ of the profit target at 50K and ½ at 100K/150K** |
| **11** | daily loss limit | **\$1,000** — **OPTIONAL** in Combine and XFA, **automatic** in LFA | **\$2,000** | **\$3,000** | [Daily Loss Limit](https://help.topstep.com/en/articles/10490293-daily-loss-limit-in-the-trading-combine-and-express-funded-account) · updated **2026-06-30**. Basis: "Net P&L hits or exceeds the DLL during the trading day" — i.e. **live net P&L, not closed balance**. Session 5 PM CT – 3:10 PM CT, resets daily. **SOFT:** "Open positions are flattened", "Pending orders are canceled", "No new trades until 5 PM CT next session", "Account stays eligible for funding". Selecting a DLL earns a \$50 Back2Funded discount. **In the LFA the DLL is different and larger: \$2,000 / \$3,000 / \$4,500** — [LFA Parameters](https://help.topstep.com/en/articles/10657969-live-funded-account-parameters) |
| **12** | minimum trading days | **No explicit minimum is stated. The binding constraint is the Consistency Target, which forces ≥2 days.** Firm's wording: "you can pass in as few as two days, but keep your best day below 50% of your Profit Target" | same | same | [Trading Combine Parameters](https://help.topstep.com/en/articles/8284197-trading-combine-parameters) · updated **2026-06-24** |
| **13** | time limit / maximum days | **NONE.** The Combine has no expiry; the subscription rebills every 30 days and the account persists until you pass or cancel | same | same | [Trading Combine Subscriptions](https://help.topstep.com/en/articles/8284121-trading-combine-subscriptions) · 2026-09-08. **NOT PUBLISHED:** no inactivity-closure rule for the *Combine* was found on any Topstep page (the 30-day inactivity closure applies to XFA and LFA) — see Ambiguities §C |
| **14** | position-size cap and scaling | **Combine: 5 minis / 50 micros** — fixed, no scaling | **10 / 100** | **15 / 150** | [Trading Combine Parameters](https://help.topstep.com/en/articles/8284197-trading-combine-parameters) · updated **2026-06-24**. **XFA: a balance-keyed Scaling Plan, and its numeric thresholds are `NOT PUBLISHED` in text** — the [Scaling Plan article](https://help.topstep.com/en/articles/8284223-what-is-the-scaling-plan) (updated **2026-07-16**) carries the table only as an embedded image (`XFA charts - hc.png`). Prose rules that ARE published: "As your balance grows, so does your buying power"; "**Your max contracts do not increase mid-session.** Hit the threshold to release more buying power? Wait for the next session."; "Errors corrected in under 10 seconds are ignored. Leave too many contracts on for 10+ seconds and your account may be reviewed." |

### C — funded-phase geometry (Express Funded Account)

| # | field | value | source |
|---|---|---|---|
| **15** | funded-phase drawdown where it differs | **Balance starts at \$0, not at the account size.** MLL starts at **−\$2,000 / −\$3,000 / −\$4,500**, trails EOD upward as before, and **locks at \$0** once balance reaches \$2,000 / \$3,000 / \$4,500. **No profit target** in the XFA — payout paths replace it. **LFA differs again:** hard floor of \$1,000 ("If your Live Funded Account balance drops below \$1,000, the account may be immediately liquidated and closed at end of the trading day"), only 20% of balance tradeable at first (minimum \$10,000), 80% held in Reserve released in four 25% increments against the Combine profit targets | [MLL article](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit); [LFA Parameters](https://help.topstep.com/en/articles/10657969-live-funded-account-parameters); [LFA Rules](https://www.topstep.com/live-funded-account-rules) · all 2026-09-08 |
| **16** | **consistency rule — exact definition and threshold** | **TWO DIFFERENT RULES, with different formulae, thresholds and penalties.**<br><br>**(a) Trading Combine — Consistency Target, 50%.** Formula: `Best Day Profit ÷ Total Profit = Best Day %`. Threshold: best day must be **at or below 50% of your Profit Target**. Penalty is **not** failure: "your Profit Target increases. You'll need to earn more to pass." Firm's example: "\$1,200 best day ÷ \$2,800 total profit = 43% ✅".<br><br>**(b) XFA — Consistency Objective, 40%, and it applies ONLY to the Consistency payout path.** Formula: `Largest Single-Day Net Profit ÷ Total Net Profit = Consistency %`. Threshold: "Your Consistency % must be 40% or below to be Payout eligible." Penalty is **not** failure: "keep trading. As you earn more net profit, the percentage will naturally come down." Example: "\$3,600 largest day ÷ \$9,500 total net profit = 37.9% ✅". **Reset:** "After a Payout is requested, your consistency calculation resets to \$0".<br><br>**The XFA Standard path has NO consistency requirement** — confirmed on [express-funded-account-rules](https://www.topstep.com/express-funded-account-rules) | [Consistency at Topstep](https://help.topstep.com/en/articles/8284208-consistency-at-topstep) · updated ~2026-08 ("over 3 weeks ago") · accessed 2026-09-08. **Note the formula in (a) mixes denominators**: prose says best day ÷ *total profit* but the threshold is stated against the *Profit Target* — see Ambiguities §B |
| **17** | profit split | **90/10 — trader keeps 90%.** Exception: "you receive **100% of your first \$10,000** in lifetime profits" for users on the new dashboard before **2026-01-12** | [Payout Policy](https://help.topstep.com/en/articles/8284233-topstep-payout-policy) · 2026-09-08 |
| **18** | first-payout eligibility | **XFA Standard path:** "5 winning days of \$150+ Net P&L", **non-consecutive**; plus "Positive net profit since your last Payout" (min \$0.01, **waived for the first payout**).<br>**XFA Consistency path:** "3 trading days with at least 1 trade per day" + Consistency % ≤ 40%.<br>**LFA:** "5 winning days of \$150+ Net P&L per Payout cycle (not consecutive)", minimum 5 days since activation or last payout; Benchmark Days are earned in the LFA only and do not carry over from the XFA.<br>**No calendar waiting period is imposed beyond the day-count.** | [Payout Policy](https://help.topstep.com/en/articles/8284233-topstep-payout-policy); [XFA Parameters](https://help.topstep.com/en/articles/8284215-express-funded-account-parameters); [LFA Rules](https://www.topstep.com/live-funded-account-rules) · all 2026-09-08 |
| **19** | **payout ladder / cap per withdrawal** | **Base rule: "Max Payout per request: 50% of your account balance up to the cap below."** Caps, by size × path — **50K:** \$2,000 Standard / \$3,000 Consistency · **100K:** \$3,000 / \$4,000 · **150K:** \$5,000 / \$6,000.<br><br>**There is NO escalating ladder.** The cap is a function of (account size × path) only, **not of payout sequence** — the same cap applies to payout #1, #2 and #n. **Live Funded Account payouts are not capped**, subject only to the constraint that "total payouts do not exceed 90% of the Starting Balance plus net Trading Profits" | [Payout Policy](https://help.topstep.com/en/articles/8284233-topstep-payout-policy) · 2026-09-08; caps cross-checked against [XFA Parameters](https://help.topstep.com/en/articles/8284215-express-funded-account-parameters) ("50% of balance, up to \$5,000" Standard / "up to \$6,000" Consistency — the 150K maxima) and [Topstep's own blog](https://www.topstep.com/blog/topstep-express-funded-account-consistency) |
| **20** | payout frequency and minimum | **Minimum payout: \$125.** Requests accepted "during CME market hours: Sunday 5 PM CT – Friday 5 PM CT". **No mandatory waiting period between requests** — you may request again as soon as the day-count is re-earned (the 5-day / 3-day counter restarts at each payout). In the **LFA**, after 30 Benchmark Trading Days a payout may be taken **once per business day**; before 30 Benchmark Days the trader may take only "50% of your share of Trading Profits". Claimed processing: 99.26% approval, ~9 seconds for auto-approved US requests via RTP/Aeropay | [Payout Policy](https://help.topstep.com/en/articles/8284233-topstep-payout-policy); [LFA Rules](https://www.topstep.com/live-funded-account-rules); [instant-payouts](https://www.topstep.com/instant-payouts) · all 2026-09-08 |
| **21** | **does a payout reduce or reset the drawdown buffer** | **YES — it DESTROYS it, and permanently.** Verbatim: "**After each Payout:** Your Maximum Loss Limit (MLL) resets to \$0 permanently, and your 5-day count restarts." And: "Your MLL is set to \$0 after your first Payout. If it's already at \$0, it stays there. **The remaining balance becomes your effective loss floor.**"<br><br>**Mechanically:** pre-payout the buffer is `balance − MLL` (≥ balance, since MLL ≤ 0). Post-payout the MLL is pinned at \$0 forever, so the buffer is exactly the **residual balance**. Withdrawing the maximum 50% of balance therefore **halves the cushion, dollar for dollar**. The consistency calculation and the winning-day counter also reset to zero at each payout | [Payout Policy](https://help.topstep.com/en/articles/8284233-topstep-payout-policy); [MLL article](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit); [Consistency](https://help.topstep.com/en/articles/8284208-consistency-at-topstep) · all 2026-09-08 |
| **22** | hard breach vs soft breach | **HARD (account-ending):**<br>· Touching the MLL in the **XFA** → "If your account ever drops to or below the Maximum Loss Limit, the account will be **permanently closed**." Back2Funded may reactivate it (≤2 times, pre-first-payout only, \$599/\$699/\$829, 7-day eligibility window).<br>· Touching the MLL in the **Combine** → "If you hit your Maximum Loss Limit, trading on that account will stop." Recoverable only by a paid Reset.<br>· **LFA** balance below \$1,000 → immediate liquidation and closure at end of day.<br>· Prohibited conduct — coordinated/group trading, account sharing, **cross-account hedging**, latency or platform-deficiency exploitation, mass data entry. "Confirmed hedging violations are final and cannot be appealed" and such accounts "cannot be reopened or reinstated."<br>· 30+ days of no trading activity may close an XFA or LFA.<br><br>**SOFT (session-ending only):** hitting the **Daily Loss Limit** — flatten, cancel, lock out until 5 PM CT next session, "Account stays eligible for funding."<br>**SOFT (target-adjusting only):** breaching either **Consistency** threshold — raises the Combine profit target, or defers XFA payout eligibility. Neither fails the account | [express-funded-account-rules](https://www.topstep.com/express-funded-account-rules); [FAQ](https://www.topstep.com/faq/); [Daily Loss Limit](https://help.topstep.com/en/articles/10490293-daily-loss-limit-in-the-trading-combine-and-express-funded-account); [Prohibited Conduct](https://help.topstep.com/en/articles/10296582-prohibited-conduct); [Understanding Hedging](https://help.topstep.com/en/articles/13747047-understanding-hedging); [Back2Funded](https://help.topstep.com/en/articles/12060405-back2funded-rules-guidelines-and-how-it-works) · all 2026-09-08 |

### D — disclosure

| # | field | value | source |
|---|---|---|---|
| **23** | **published pass-rate / payout statistics** | **PUBLISHED, dated, four-part, and carried in the site-wide footer disclaimer.** Verbatim:<br>> "From January through December 2025, (a) **16.8%** of all Trading Combines initiated were successfully completed and afforded the opportunity to advance to the Funded Level, (b) **51.8%** of individual participants who entered one or more Trading Combines advanced to the Funded Level in at least one of their Trading Combines, (c) **33.3%** of all individual participants at the Funded Level received a payout, and (d) **0.71%** of individual participants trading in an Express Funded Account were called up to a Live Funded Account."<br><br>**Read the denominators.** (a) counts **Combines** (attempts); (b) counts **people**. The gap (16.8% vs 51.8%) is the multiple-attempt effect, not disagreement. (c) is conditional on reaching funded, so the unconditional payout rate per *participant* is ≈ 0.518 × 0.333 ≈ **17.3%** of entrants ever receiving a payout — and that is per person across unlimited attempts, not per fee paid.<br><br>Marketing figures, lower tier: **"\$1.4B+"** paid all-time; **99.26%** payout approval rate; ~**9 s** average auto-approved payout time (US, RTP/Aeropay). Also carried: "Simulated results do not represent actual trading." | [our-program](https://www.topstep.com/our-program) and [instant-payouts](https://www.topstep.com/instant-payouts), both accessed 2026-09-08; identical disclaimer text appears on [faq](https://www.topstep.com/faq/) |
| **24** | terms version / last-updated dates | **Help-centre articles (primary, current):** Pricing **2026-07-20** · Scaling Plan **2026-07-16** · Daily Loss Limit **2026-06-30** · Trading Combine Parameters **2026-06-24** · What is a Reset **2026-06-18** · Program Overview **2026-08-05** · MLL article and Payout Policy both "updated this week" (≈ 2026-09-01/08, **no explicit date shown**) · Consistency and Back2Funded "over 3 weeks ago" (≈ 2026-08, **no explicit date**) · LFA Parameters "over a month ago" (**no explicit date**).<br><br>**Marketing rules pages (stale):** [express-funded-account-rules](https://www.topstep.com/express-funded-account-rules) carries **"Last updated: June 26, 2025"** — **fifteen months older** than the help-centre articles covering the same rules. Where they disagree, prefer the help centre and note both | as listed · all accessed 2026-09-08 |

---

## Ambiguities, contradictions and gaps

**§A — the Trading Combine Parameters table is not retrievable as text.**
[help.topstep.com/…/8284197](https://help.topstep.com/en/articles/8284197-trading-combine-parameters) is
the canonical parameters page and its "Objectives" table (profit target, MLL, DLL) renders
client-side; four fetches returned the page headings and the Maximum Position Size table but the
Objectives values came back empty. The profit targets in field 5 are therefore **cross-derived from
two other primary Topstep pages** ([LFA Parameters](https://help.topstep.com/en/articles/10657969-live-funded-account-parameters)
listing \$3,000/\$6,000/\$9,000 as reserve-unlock targets, plus [LFA Rules](https://www.topstep.com/live-funded-account-rules)
stating "Same profit targets as the Trading Combine apply"), and corroborated on Topstep's own
product pages. They are **not** taken from a competitor or an aggregator. Flagged rather than
asserted.

**§B — the Combine consistency formula states two different denominators.**
The help centre gives the formula as `Best Day Profit ÷ Total Profit = Best Day %` but states the
threshold as "your best day must stay at or below **50% of your Profit Target**". Total *profit* and
profit *target* are the same quantity only at the exact moment of passing. The firm's own worked
example uses total profit (\$1,200 ÷ \$2,800 = 43%) on a 50K Combine whose target is \$3,000 — so the
example is consistent with the *formula*, not with the *threshold wording*. **Both readings are
recorded; neither is picked.** The practical difference matters: under the target reading the cap is
a fixed \$1,500 on a 50K; under the total-profit reading it is a moving 50% of realised profit.

**§C — no inactivity rule published for the Combine.**
A 30-day inactivity closure is documented for the XFA and the LFA. No equivalent was found for the
Trading Combine on any Topstep page. Marked `NOT PUBLISHED` in field 13. Tried: the Trading Combine
Parameters page, Trading Combine Subscriptions, the FAQ collection, and two site-scoped searches.

**§D — the XFA Scaling Plan thresholds are published only as an image.**
Field 14. The article text names the chart file (`XFA charts - hc.png`) but no numeric
balance→contract mapping appears in the HTML. Marked `NOT PUBLISHED (image only)`. Tried: direct
fetch of the Scaling Plan article, the XFA Parameters article, the express-funded-account-rules
marketing page, and a site-scoped search.

**§E — "MLL locks at \$0" vs "locks at your starting balance" is the same rule in two coordinate
systems, not a contradiction.** The Combine displays balance in absolute dollars (\$50,000 start);
the XFA displays balance as profit-from-zero (\$0 start). "Locks at your starting balance" and "locks
at \$0" both mean *the floor stops at breakeven*. Recorded here because the two sentences sit in the
same article and read as inconsistent.

**§F — headline subscription price depends on which path is quoted.**
Topstep's marketing pages quote **\$95/\$149/\$229** (the No-Activation-Fee path); the pricing help
article lists both, with the Standard path at **\$49/\$99/\$199 plus a \$149 activation fee**. Both
are reported in field 2. On the 50K the paths cross at ≈3.2 months of subscription.

**§G — one fetch was refused on copyright grounds.**
The WebFetch summariser declined to reproduce
[express-funded-account-rules](https://www.topstep.com/express-funded-account-rules) verbatim in
full, returning a partial numeric summary instead. The page was re-fetched successfully with
targeted questions rather than a reproduction request; the facts in fields 16, 22 and 24 come from
that second pass.

**§H — safety note, as required by the lane brief.** No page fetched in this lane contained text
directed at the agent, instructions to act, or attempted prompt injection. All Topstep pages carry
sign-up calls-to-action and affiliate-style conversion links; **none were followed, no account was
created, and no personal data was entered.** The only conversion-adjacent content encountered was
ordinary marketing copy.

---

## Sources

| URL | accessed | tier | what was sought | what it yielded |
|---|---|---|---|---|
| https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit | 2026-09-08 | primary | fields 7, 8, 9, 10, 21 | **The core of the lane.** Exact trailing/testing wording, MLL per size, XFA lock table for all three sizes, post-payout MLL reset, worked example (\$50,000 → \$50,500 balance, \$48,000 → \$48,500 MLL). Fetched 3×; no explicit date, header says "updated this week" |
| https://help.topstep.com/en/articles/8284233-topstep-payout-policy | 2026-09-08 | primary | fields 17, 18, 19, 20, 21 | Profit split 90/10 and the \$10k/100% exception; both payout paths' eligibility; the full cap table by size × path; confirmation that **caps do not escalate by payout sequence**; \$125 minimum; post-payout MLL → \$0 permanently. Fetched 2× |
| https://help.topstep.com/en/articles/8284208-consistency-at-topstep | 2026-09-08 | primary | field 16 | Both consistency rules verbatim with formulae, thresholds, penalties, worked examples and reset timing. Also surfaced the denominator ambiguity in §B |
| https://help.topstep.com/en/articles/10490293-daily-loss-limit-in-the-trading-combine-and-express-funded-account | 2026-09-08 | primary | field 11 | DLL \$1,000/\$2,000/\$3,000; optional in Combine+XFA, automatic in LFA; net-P&L basis; soft-lockout consequences; session window. Dated **2026-06-30** |
| https://help.topstep.com/en/articles/9208217-topstep-pricing | 2026-09-08 | primary | fields 2, 3, 4 | Full price list both paths, activation fee, reset = monthly rate, Level 2 \$38/mo. Dated **2026-07-20** |
| https://help.topstep.com/en/articles/8284197-trading-combine-parameters | 2026-09-08 | primary | fields 5, 8, 11, 12, 13, 14 | **PARTIAL.** Max Position Size table (5/50, 10/100, 15/150) and "pass in as few as two days". **Objectives table did not render — profit target, MLL and DLL values ABSENT.** Fetched 2× with different prompts, same result. Dated **2026-06-24**. See §A |
| https://help.topstep.com/en/articles/10657969-live-funded-account-parameters | 2026-09-08 | primary | fields 5, 15 | Profit targets \$3,000/\$6,000/\$9,000; LFA DLL \$2,000/\$3,000/\$4,500; \$1,000 hard floor; 20%/80% reserve structure. **This is where the profit-target figures were recovered** |
| https://www.topstep.com/live-funded-account-rules | 2026-09-08 | primary | fields 5, 15, 19, 20 | "Same profit targets as the Trading Combine apply"; LFA uncapped payouts subject to the 90%-of-starting-balance ceiling; Benchmark Trading Days; 30-day rule; 3:10 PM CT flatten |
| https://www.topstep.com/express-funded-account-rules | 2026-09-08 | primary | fields 16, 19, 22, 24 | **First fetch REFUSED verbatim reproduction on copyright grounds** (partial numbers only) — see §G. Second targeted fetch yielded: permanent closure on MLL touch, no consistency rule on the Standard path, **max 5 active/pending XFAs**, Back2Funded 7-day eligibility window, and the page's stale **"Last updated: June 26, 2025"** |
| https://help.topstep.com/en/articles/8284215-express-funded-account-parameters | 2026-09-08 | primary | fields 15, 19, 20 | Both payout paths with headline caps (\$5,000 Standard / \$6,000 Consistency), 90/10 split, "No monthly subscription fee after passing", one-time Activation Fee. **Numeric MLL/DLL/contract tables ABSENT — page links out rather than reproducing** |
| https://help.topstep.com/en/articles/8284223-what-is-the-scaling-plan | 2026-09-08 | primary | field 14 | **NEGATIVE for the numbers.** Prose rules only ("max contracts do not increase mid-session"; 10-second error tolerance). **Table is an embedded image `XFA charts - hc.png`; thresholds not in text.** Dated **2026-07-16**. See §D |
| https://help.topstep.com/en/articles/8284128-what-is-a-reset | 2026-09-08 | primary | field 3 | What a Reset restores (balance, MLL, Consistency Target, trading days); 2 per account per day; one free Reset Credit per rebill. **Fee amounts absent — links to pricing.** Dated **2026-06-18** |
| https://help.topstep.com/en/articles/12060405-back2funded-rules-guidelines-and-how-it-works | 2026-09-08 | primary | fields 4, 22 | \$599/\$699/\$829 reactivation, −\$50 with DLL selected, max 2 per account, pre-first-payout only, everything resets to zero |
| https://help.topstep.com/en/articles/8284099-topstep-program-overview | 2026-09-08 | primary | fields 6, 12, 13 | "Three stages. One destination"; 5 winning days of \$150+ at both funded stages. **Profit targets, min days and time limit ABSENT.** Dated **2026-08-05** |
| https://help.topstep.com/en/articles/8284121-trading-combine-subscriptions | 2026-09-08 | primary | field 13 | Subscription rebills every 30 days, active until pass or cancel — the basis for "no time limit". Reached via site-scoped search, not fetched directly |
| https://www.topstep.com/our-program | 2026-09-08 | primary | field 23 | **The full 2025 four-part performance disclaimer, verbatim.** Also "Earn payouts up to \$12,000 in as little as 3 days" (marketing) |
| https://www.topstep.com/instant-payouts | 2026-09-08 | primary/claims | field 23 | Same 2025 disclaimer verbatim (independent confirmation of placement); \$1.4B+ all-time, 99.26% approval, ~9 s processing (US RTP/Aeropay only) |
| https://www.topstep.com/faq/ | 2026-09-08 | primary | fields 5, 12, 13, 22 | "If you hit your Maximum Loss Limit, trading on that account will stop"; "Simulated results do not represent actual trading"; repeats the 16.8% figure. **Profit targets, time limits and min days ABSENT** |
| https://www.topstep.com/blog/prop-firm-drawdown-rules | 2026-09-08 | primary (firm blog) | fields 7, 9 | The firm's own EOD-vs-intraday contrast and its worked example (up \$5K, pulls back \$2K, closes +\$3K: dead under intraday trailing, alive under EOD). **Does not restate Topstep's own MLL numbers** |
| https://www.topstep.com/blog/topstep-express-funded-account-consistency | 2026-09-08 | primary (firm blog) | fields 16, 19 | Corroborated the Consistency-path caps \$3,000/\$4,000/\$6,000 by size and the 3-day / 40% requirement |
| https://help.topstep.com/en/articles/10296582-prohibited-conduct | 2026-09-08 | primary | field 22 | Coordinated trading, account sharing, AI/HFT/mass-data-entry, platform-deficiency exploitation. Reached via site-scoped search |
| https://help.topstep.com/en/articles/13747047-understanding-hedging | 2026-09-08 | primary | field 22 | Cross-account hedging prohibited; violations final, not appealable, accounts not reinstatable. Reached via site-scoped search |
| https://www.topstep.com/pricing | 2026-09-08 | primary | field 2 | **NEGATIVE — HTTP 404.** No such path. Pricing lives in the help centre article instead |
| https://www.topstep.com/how-it-works/ | 2026-09-08 | primary | field 5 | **NEGATIVE.** No account-comparison table retrievable; narrative copy only |
| https://www.topstep.com/topstep-prop | 2026-09-08 | claims (marketing) | field 5 | Corroborated \$3,000/\$6,000/\$9,000 targets against \$95/\$149/\$229 (No-Activation-Fee path) and 5/50, 10/100, 15/150 contracts. Reached via search snippet; used only as corroboration, never as sole source |
| WebSearch: "Topstep Trading Combine rules trailing drawdown maximum loss limit" (site-scoped) | 2026-09-08 | — | locating primaries | Located the MLL, DLL, Combine-parameters, XFA-parameters, payout-policy and rules pages |
| WebSearch: "Topstep Express Funded Account payout ladder consistency rule" | 2026-09-08 | — | fields 16, 19 | Located the consistency and payout primaries; also surfaced the claims tier (fundedfuturesfamily, futureshive, fortraders, proptradingvibes) — **none used as a source for any cell** |
| WebSearch: "Topstep pass rate statistics percentage of traders funded payouts paid total" | 2026-09-08 | — | field 23 | Surfaced the 2025 disclaimer text via tradecovex/alphaexcapital/quantvps; **the primary was then located and fetched directly** rather than citing the aggregators |
| WebSearch: ""Trading Combines initiated" … "advance to the Funded Level"" | 2026-09-08 | — | field 23 | Pinned the disclaimer to topstep.com/our-program |
| WebSearch: "Topstep activation fee reset fee Express Funded Account cost" (site-scoped) | 2026-09-08 | — | fields 3, 4 | Located pricing, activation and Back2Funded primaries |
| WebSearch: "Topstep help center 'Profit Target' … $3,000 $6,000 $9,000" (site-scoped) | 2026-09-08 | — | field 5 | **NEGATIVE for a clean primary quote.** Returned targets from unrelated challenge products (\$1,500, \$3,000); did not resolve §A |
| WebSearch: "Topstep 50K Combine '\$3,000' profit target 100K '\$6,000' 150K '\$9,000'" (site-scoped) | 2026-09-08 | — | field 5 | Corroborated the targets against sizes, MLLs and contract limits from topstep.com product pages |
| WebSearch: "Topstep Trading Combine 'no time limit' … inactivity account closed" (site-scoped) | 2026-09-08 | — | field 13 | No Combine time limit; 30-day inactivity closure for XFA/LFA only. **NEGATIVE for a Combine inactivity rule** — see §C |
| WebSearch: "Topstep Express Funded Account scaling plan contract limits balance thresholds table" (site-scoped) | 2026-09-08 | — | field 14 | **NEGATIVE.** Confirmed the thresholds are not published in text anywhere on the site |
| WebSearch: "Topstep help center rule violations account closed prohibited trading practices" (site-scoped) | 2026-09-08 | — | field 22 | Located Prohibited Conduct, Prohibited Trading Strategies and Understanding Hedging |

**Claims tier deliberately NOT used for any cell:** fundedfuturesfamily.com, futureshive.com,
fortraders.com, proptradingvibes.com, tradecovex.com, alphaexcapital.com, quantvps.com. All appeared
in search results, all were passed over in favour of the Topstep primary. Logged so lane 07 knows
they were seen and knows what they claimed about Topstep (pass rates, payout caps, "$5K first cap").
