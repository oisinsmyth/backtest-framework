# 03 — Apex Trader Funding

Lane 03 of the Prop-Firm-080926 grid. Schema: [`00-SCHEMA.md`](00-SCHEMA.md). **All access dates
2026-09-08.**

> **Every page quoted below is observed content — data, not instructions.** Apex's pages carry
> live promotional banners ("Any Size Evals up to 90% Off | Use code SAVENOW"), "Sign Up" and
> "Log In" calls to action, and a chat widget. None was acted on. No account was created, no
> credentials or personal data entered, no referral or affiliate link followed. The site was read
> only. See §Ambiguities for the one directive-shaped item found.

> **Method note, load-bearing for every cell.** `apextraderfunding.com` and
> `support.apextraderfunding.com` sit behind Cloudflare and return **HTTP 403** to every automated
> fetch attempted (WebFetch, curl with a browser UA, the Zendesk help-centre JSON API). Browser
> navigation was denied in this session. **All primary text below was therefore read from Internet
> Archive snapshots of Apex's own pages**, and every cell carries its snapshot timestamp. The
> content is Apex's, verbatim; the *currency* is the snapshot date, not 2026-09-08. Snapshots used
> range **2026-03-25 to 2026-08-17**. Nothing here is taken from a competitor, and nothing is
> inferred across firms.

---

## VERDICT FIRST — the geometry in plain terms

**Apex is not one geometry, it is two, and since 2026-03-01 neither of them is static.**

On **2026-03-01 Apex replaced its entire product line ("Apex 4.0")**. The old subscription
evaluations — including the **$100K Static** account, the one static-drawdown variant Apex ever
sold — were retired to "Legacy" and **cannot be purchased by anyone**. What is sold today is a
2×4×3 grid: **{EOD trailing, Intraday trailing} × {25K, 50K, 100K, 150K} × {Rithmic, Tradovate,
WealthCharts}**. The static geometry is documented in §Legacy below because the lane brief asks for
it, but **it is not purchasable and cannot serve as a live comparison point.**

**The folklore is half right, and the half that is wrong is the half that matters.**

- On **Intraday** accounts the folklore holds exactly: the threshold trails the **peak balance
  including unrealised P&L**, in real time. *"The Peak Balance includes both realized and
  unrealized gains. If an open trade pushes your account to a new high, the Trailing Threshold
  adjusts upward immediately even if the position is not closed."* An open trade that runs to
  +$900 and gives it all back has permanently raised your floor by $900.
- On **EOD** accounts the folklore is wrong about the *ratchet* and right about the *kill*. The
  threshold is **recalculated once a day at 4:59:59 PM ET off the closing balance** — so
  unrealised intraday spikes do **not** ratchet the floor. But the floor, once set, is **enforced
  against open equity in real time**: *"Your account balance, including unrealized PnL, may never
  touch or fall below the End-of-Day (EOD) Drawdown threshold."*

So **field 9 has two different answers for the two halves of the same firm**, and both halves
breach on open equity. The EOD product is a *ratchet-on-close, kill-on-open-equity* barrier. That
is a distinct object from either a pure closed-balance barrier or a pure open-equity trailing one,
and it is the specific thing this lane existed to pin down.

**The floor does lock, and the lock level differs between the funded account and the evaluation —
and inside the evaluation it differs by platform vendor.**

| where | trailing stops when threshold reaches | so the floor ends at |
|---|---|---|
| **Performance Account** (both families) | Starting Balance + $100 | e.g. **$50,100** on a 50K |
| **Evaluation, Rithmic / WealthCharts** | Profit Target Balance | e.g. **$53,000** on a 50K |
| **Evaluation, Tradovate** | **never — trails indefinitely** | no lock |

The PA lock is the important one: **once locked at start + $100, the funded account's floor never
moves again**, so the account is a barrier option whose barrier is fixed just $100 above par, and
every dollar of retained profit is pure buffer. The evaluation lock is close to vacuous — the
evaluation ends the moment the target is hit, so the eval floor only locks if you overshoot past
target + max drawdown without stopping.

**The consistency rule is 50%, not 30%.** The 30% rule is the *Legacy* rule and still binds legacy
accounts. Current accounts: *"No single profitable trading day may account for 50% or more of total
profit earned since your last approved payout."* It gates the payout button, not the account — it
never fails you. It resets on each approved payout. **It does not apply to evaluations at all**
(both eval tables say Consistency: "Not Applied").

**The payout ladder is capped and finite, and this is the D379 §4 term.** Each PA gets **at most 6
payouts, ever**, on a rising per-request cap, and **after the sixth the PA is closed** — you must
buy and pass a new evaluation. Lifetime extraction per Performance Account:

| account | EOD lifetime cap | Intraday lifetime cap | eval + activation (list) |
|---|---|---|---|
| 25K | **$6,000** | **$6,000** | $450+$119 / $167+$59 |
| 50K | **$13,000** | **$14,500** | $550+$139 / $249+$59 |
| 100K | **$18,000** | **$18,500** | $990+$149 / $399+$59 |
| 150K | **$20,500** | **$21,500** | $1,890+$159 / $599+$59 |

**A payout does not reset the drawdown buffer; it consumes it.** The threshold is locked at start +
$100 and does not move on a payout. The Safety Net (drawdown + $100) *"must be maintained for the
lifetime of the Performance Account"* and *"does not disappear after your first payout."* So a
payout drops the balance and leaves the floor where it was: **the buffer above the barrier shrinks
by exactly the payout amount.** In Apex's own 50K worked example, the post-payout balance is
$52,500 against a $50,100 floor.

**There is no reset.** On 4.0 the evaluation is a one-time purchase with 30 calendar days of
access; a breach permanently fails it and *"There are no reset fees. If an Evaluation fails, the
only way to continue is by purchasing a new one."* Resets survive only on Legacy accounts.

---

## The field table — current products (Apex 4.0, on sale since 2026-03-01)

Two variants per row where they differ. **EOD** = End-of-Day trailing drawdown; **INT** = Intraday
(real-time) trailing drawdown. Platform = Rithmic / Tradovate / WealthCharts, identical rules
except where noted.

### A — acquisition cost

| # | field | EOD | INT | source |
|---|---|---|---|---|
| **1** | account sizes | **$25K, $50K, $100K, $150K** | same | [EOD Evaluations](https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-evaluations/) (snap 2026-05-27); [Intraday Evaluations](https://apextraderfunding.com/help-center/intraday-trailing-drawdown-accounts/intraday-trailing-drawdown-evaluations/) (snap 2026-05-06) |
| **2** | evaluation fee, **one-time, not a subscription** | 25K **$450** · 50K **$550** · 100K **$990** · 150K **$1,890** | 25K **$167** · 50K **$249** · 100K **$399** · 150K **$599** | product JSON embedded in [apextraderfunding.com/](https://apextraderfunding.com/) (snap **2026-08-17**), fields `price`, `is_subscription:false` |
| 2b | "No Activation Fee" eval variants (activation prepaid) | 25K $990 · 50K $1,190 · 100K $1,590 · 150K $2,490 | 25K $690 · 50K $490 · 100K $590 · 150K $1,690 | same JSON, `free_activation:true` |
| 2c | 5-packs | e.g. 25K $1,950 · 50K $2,450 · 100K $4,450 · 150K $8,950 | 25K $749.50 · 50K $950 · 100K $1,750 · 150K $2,450 | same JSON, `subcategory:"bundlepack"` |
| 2d | list vs paid | Apex runs a permanent site-wide coupon banner ("up to 90% Off", code SAVENOW). **Prices above are list.** The transacted price is behind checkout and was not reachable read-only. | | homepage banner, snaps 2026-05-27 → 2026-08-17 |
| **3** | **reset fee** | **NONE — resets do not exist on 4.0.** *"There are no reset fees. If an Evaluation fails, the only way to continue is by purchasing a new one."* A failed eval is permanently closed. | same | [Evaluation Plan Fees and Access](https://apextraderfunding.com/help-center/billing/evaluation-plan-fees-and-access-explained/) (snap 2026-07-13) |
| 3b | contradiction | The product JSON still carries `"reset_fee":49` on every 4.0 product. The help-centre prose says resets do not exist. **Both reported.** | | JSON (snap 2026-08-17) vs fees page (snap 2026-07-13) |
| **4** | activation / funded-account fee | **one-time, per PA**, due within **7 calendar days** of passing: 25K **$119** · 50K **$139** · 100K **$149** (Tradovate **$139**) · 150K **$159** | **$59, all four sizes** | JSON `pa_features.price` (snap 2026-08-17); window from [PA Activation Process](https://apextraderfunding.com/help-center/billing/pa-activation-process-deadline-explained/) (snap 2026-07-30) |
| 4b | is it recurring? | **No.** *"The activation fee is a one-time payment per account. It does not renew monthly."* Not refundable, transferable or reversible. | same | PA Activation Process (snap 2026-07-30) |
| 4c | market-data fees | Level 1 data **included**. DOM/depth is extra and billed by the vendor. Selecting "Professional" status on Rithmic costs "$115 or more per calendar month per exchange". | same | fees page (snap 2026-07-13); Legacy Evaluation Rules (snap 2026-06/07) |

### B — evaluation geometry

| # | field | EOD | INT | source |
|---|---|---|---|---|
| **5** | profit target | **$1,500 / $3,000 / $6,000 / $9,000** — a flat **6%** of account size at every size | identical | EOD Evaluations; Intraday Evaluations |
| **6** | phases | **one.** Evaluation → activate PA. No second phase. | same | both eval pages |
| **7** | **drawdown TYPE** | **End-of-day trailing.** *"The EOD Threshold is recalculated once per trading day at 4:59:59 PM ET, based on the account's closing balance. It always trails the highest achieved EOD balance and never moves downward."* | **Intraday (real-time) trailing.** *"The threshold follows the account's highest intraday balance (Peak Balance) … It maintains a fixed dollar distance behind the peak based on account size and never decreases."* | [EOD Drawdown Explained](https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-drawdown-explained/) (snap 2026-05-27); [Intraday Trailing Drawdown Explained](https://apextraderfunding.com/help-center/intraday-trailing-drawdown-accounts/intraday-trailing-drawdown-explained/) (snap **2026-07-14**) |
| **8** | drawdown AMOUNT | **$1,000 / $2,000 / $3,000 / $4,000**. **Not a flat percentage** — 4.0% / 4.0% / **3.0%** / **2.67%** of account size. The drawdown tightens in relative terms as the account grows, while the target stays at 6%, so **the target-to-drawdown ratio rises with size: 1.5 / 1.5 / 2.0 / 2.25** | identical | both eval pages; corroborated by JSON `features.trailing_threshold` |
| **9** | **drawdown BASIS — the load-bearing cell** | **Ratchet on CLOSED balance; kill on OPEN equity.** The threshold is set off the closing balance only. But: *"The account may experience temporary drawdowns throughout the trading session, but it may never touch the EOD Threshold level itself. If at any moment during the trading session the account balance touches or falls below the EOD Threshold, all open positions are automatically liquidated, and the evaluation is immediately failed."* And on the funded side, explicitly: *"Your account balance, **including unrealized PnL**, may never touch or fall below the End-of-Day (EOD) Drawdown threshold."* | **Ratchet AND kill on OPEN equity.** *"The threshold is enforced in real time, including unrealized PnL."* And: *"Does unrealized profit move the Trailing Threshold? **Yes.** The Peak Balance includes both realized and unrealized gains. If an open trade pushes your account to a new high, the Trailing Threshold adjusts upward immediately even if the position is not closed."* | EOD Drawdown Explained + [EOD PA](https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-performance-accounts-pa/) (snap 2026-05-27); Intraday Explained (snap 2026-07-14) + [Intraday PA](https://apextraderfunding.com/help-center/intraday-trailing-drawdown-accounts/intraday-trailing-drawdown-performance-accounts-pa/) (snap 2026-05-27) |
| 9b | can you dip below and recover? | **No, in both.** *"Can my account dip below the threshold intraday if it later recovers? No, the account may experience intraday drawdown, but it may never touch or cross the EOD Threshold level at any time."* Liquidation fills may land above or below the level; *"Once the threshold is touched, the account is considered breached."* | same | both explained pages |
| **10** | **does the floor LOCK, and where** | **PA: yes.** *"Once the EOD Threshold reaches Starting Balance + $100, it stops increasing."* 50K → floor fixes at **$50,100**, reached when the highest EOD balance hits **$52,100** (= start + max DD + $100). **Eval, Rithmic/WealthCharts: yes** — *"stops trailing and becomes fixed when it reaches an amount equal to the Target Profit balance"* (50K → **$53,000**, when the highest EOD balance closes above $55,000). **Eval, Tradovate: NO** — *"EOD Drawdown trails indefinitely with the peak EOD account balance."* | Identical structure. **PA:** *"Once the Intraday Threshold reaches Starting Balance + $100, it stops increasing"* (50K → **$50,100**, at peak balance realised-or-unrealised of **$52,100**). **Eval Rithmic/WealthCharts:** locks at Profit Target Balance (50K → **$53,000**, at peak $55,000). **Eval Tradovate:** *"Intraday Drawdown trails indefinitely with the peak account balance."* | EOD Drawdown Explained; Intraday Explained |
| **11** | daily loss limit | **YES in eval, fixed for the session, not trailing:** 25K **$500** · 50K **$1,000** · 100K **$1,500** · 150K **$2,000**. Basis is **open equity**: *"It is monitored in real time and applies to total account equity, including both realized and unrealized losses."* Soft: hitting it flattens and pauses to next session; the account survives. Resets **6:00 PM ET**. | **NONE.** *"There is no DLL for Intraday Drawdown Evaluations."* | [Daily Loss Limit Explained](https://apextraderfunding.com/help-center/additional-helpful-items/daily-loss-limit-explained/) (snap 2026-07-14); Intraday Evaluations |
| **12** | minimum trading days | **NONE.** *"No minimum trading days required, may pass in one trading day."* | same | both eval pages; JSON `trading_days_til_eligible:1` |
| **13** | time limit | **30 consecutive calendar days** from purchase, weekends and holidays included, expiring **6:00 PM ET on Day 30**. No extensions, no carry-over of balance. | same | fees page (snap 2026-07-13); both eval pages |
| **14** | position-size cap & scaling | **Fixed for the whole evaluation — no scaling** ("Scaling: Not Applied"). Max contracts **4 / 6 / 8 / 12** minis, or **40 / 60 / 80 / 120** micros. Cap is across all instruments combined. | identical | both eval pages; JSON `contract_choices` |
| 14b | session boundary | Trading day runs **6:00 PM ET → 4:59 PM ET**; the day resets at 6:00 PM ET. | same | EOD Evaluations FAQ; DLL page |

### C — funded-phase geometry (Performance Account, "Sim Funded")

| # | field | EOD | INT | source |
|---|---|---|---|---|
| **15** | how the funded phase differs from the eval | Same drawdown **type** and **amount**. Differences: floor now locks at **start + $100** (not at target); **contracts halve at entry and then scale** — max **2 / 4 / 6 / 10** vs 4/6/8/12 in the eval; **DLL becomes tier-based**; **50% consistency now applies**; **inactivity rule applies**; no 30-day clock. | same, plus the intraday PA now **has a DLL** (the intraday *eval* had none) | [EOD PA](https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-performance-accounts-pa/), [Intraday PA](https://apextraderfunding.com/help-center/intraday-trailing-drawdown-accounts/intraday-trailing-drawdown-performance-accounts-pa/) (both snap 2026-05-27) |
| 15b | tier scaling table (contracts / DLL by profit) | **25K:** $0–999 → 1 ct, $500 DLL · $1,000–1,999 → 2 ct, $500 · $2,000+ → 2 ct, $1,250. **50K:** $0–1,499 → 2 ct, $1,000 · $1,500–2,999 → 3 ct, $1,000 · $3,000–5,999 → 4 ct, $2,000 · $6,000+ → 4 ct, $3,000. **100K:** $0–1,999 → 3 ct, $1,750 · $2,000–2,999 → 4 ct, $1,750 · $3,000–4,999 → 5 ct, $1,750 · $5,000–9,999 → 6 ct, $2,500 · $10,000+ → 6 ct, $3,500. **150K:** $0–1,999 → 4 ct, $2,500 · $2,000–2,999 → 5 ct, $2,500 · $3,000–4,999 → 7 ct, $2,500 · $5,000–9,999 → 10 ct, $3,000 · $10,000+ → 10 ct, $4,000. | identical | DLL page + [Scaling Levels (PA)](https://apextraderfunding.com/help-center/additional-helpful-items/scaling-levels-pa-explained/) (both snap 2026-07-14) |
| 15c | how tiers move | Set **once per day off the 4:59:59 PM ET closing balance**, applied to the next session, fixed for that session. Tiers move **down** as well as up, floored at Level 1. Oversized orders are **rejected**, not penalised. | same | Scaling Levels (PA) |
| **16** | **consistency rule — exact wording** | **50%.** *"The 50% Consistency ensures that no single trading day accounts for more than 50% of your total accumulated profit at the time of a payout request. This applies to profits earned since your last approved payout, or since account inception if no payout has been made."* Formula given by Apex: **Highest Profit Day ÷ 0.5 = minimum net profit required**; equivalently Highest Day ÷ Total Profit must be **< 50%**. **Losing days count against you** — Apex's own example: +$1,000 then −$200 gives $1,000 ÷ $800 = 125%, non-compliant. **It does not fail the account** — *"being above the 50% consistency does not fail your account. However, the payout request option will just not be available."* **Resets on each approved payout.** **Not applied during evaluations.** | identical | [50% Consistency Requirement](https://apextraderfunding.com/help-center/additional-helpful-items/50-consistency-requirement/) (snap **2026-07-26**); both payout pages |
| **17** | profit split | **100%.** *"Approved payouts are issued at a 100% payout split, you receive 100% of the approved payout amount."* No split tier, no 90/10 step on current products. | same | [EOD Payouts](https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-payouts/) (snap 2026-05-27); [Intraday Payouts](https://apextraderfunding.com/help-center/intraday-trailing-drawdown-accounts/intraday-trailing-drawdown-payouts/) (snap 2026-07-14) |
| **18** | first-payout eligibility | **5 qualifying trading days**, non-consecutive allowed, **no deadline**. A day only qualifies if it clears the **minimum daily profit** for the size — EOD: **$100 / $250 / $300 / $350**; INT: **$100 / $200 / $250 / $300**. Plus: balance ≥ **Min Balance to Request**, and 50% consistency satisfied. No waiting period beyond the 5 days, so **weekly payouts are reachable**. | see figures at left | EOD Payouts; Intraday Payouts |
| 18b | Safety Net / min balance | Safety Net = **max drawdown + $100** → **$26,100 / $52,100 / $103,100 / $154,100**. Min Balance to Request = Safety Net + the $500 minimum payout → **$26,600 / $52,600 / $103,600 / $154,600**. *"Only profit above the safety net is eligible to be requested for a payout."* | identical | both payout pages |
| **19** | **payout ladder / cap per withdrawal** | Payout # → 25K / 50K / 100K / 150K:<br>**1:** $1,000 / $1,500 / $2,000 / $2,500<br>**2:** $1,000 / $1,500 / $2,500 / $3,000<br>**3:** $1,000 / $2,000 / $2,500 / $3,000<br>**4:** $1,000 / $2,500 / $3,000 / $3,000<br>**5:** $1,000 / $2,500 / $4,000 / $4,000<br>**6:** $1,000 / $3,000 / $4,000 / $5,000<br>**Lifetime: $6,000 / $13,000 / $18,000 / $20,500** | Payout # → 25K / 50K / 100K / 150K:<br>**1:** $1,000 / $1,500 / $2,000 / $2,500<br>**2:** $1,000 / $2,000 / $2,500 / $3,000<br>**3:** $1,000 / $2,500 / $3,000 / $3,000<br>**4:** $1,000 / $2,500 / $3,000 / $4,000<br>**5:** $1,000 / $3,000 / $4,000 / $4,000<br>**6:** $1,000 / $3,000 / $4,000 / $5,000<br>**Lifetime: $6,000 / $14,500 / $18,500 / $21,500** | EOD Payouts (snap 2026-05-27); Intraday Payouts (snap 2026-07-14). Lifetime totals are this lane's column sums of Apex's own tables |
| 19b | what happens at 6 | *"PAs are limited to the max payouts specified below, regardless of the total profit generated in the account. **After 6 payouts, the PA is closed**, and you will be able to obtain another PA by qualifying for another evaluation."* | same | both payout pages |
| **20** | frequency & minimum | **Up to weekly.** Minimum **$500 per request, all sizes.** Trading may continue immediately after a request; if the balance then falls below the required threshold the request is **auto-denied** with no penalty. | same | both payout pages |
| **21** | **does a payout reduce or reset the drawdown buffer** | **It reduces it, and nothing resets.** The threshold is already locked at start + $100 and does not move on a payout. *"The Safety Net … **must be maintained for the lifetime of the Performance Account**"* and *"remains in place for the lifetime of the Performance Account and **does not disappear after your first payout**."* Apex's own worked example on the consistency page opens with *"After a payout, your new balance is $52,500"* on a 50K — against a floor of $50,100. **The payout is drawn straight out of the buffer above the barrier.** Only the *consistency* calculation resets on an approved payout. | identical | both payout pages; 50% Consistency Requirement |
| **22** | hard breach vs soft breach | **HARD (ends the account):** touching the drawdown threshold — *"all positions are automatically liquidated and the PA is permanently closed"*; hedging / correlated-instrument violation — *"immediate Performance Account closure"*; **inactivity** — *"If you do not record at least two $50 net profit days within 30 consecutive calendar days, the account will be closed"*; **exhausting the 6th payout**. In an evaluation, breach = immediate permanent fail, no reset available. **SOFT (pauses only):** hitting the **DLL** — flattens and stops trading for the session, *"The account remains active and resets at the next session open"*; **failing 50% consistency** — hides the payout button only; a **denied payout** — account stays active. | same | EOD PA; Intraday PA; DLL page; both payout pages |
| 22b | account caps | Max **20 active PAs** per household, combined across Legacy + EOD + Intraday. No limit on the number of evaluations. | same | EOD PA / Intraday PA FAQs; Legacy Products Overview |
| 22c | discretionary closure surface | Beyond the mechanical rules, Apex's **Prohibited Activities** list includes judgement-laden clauses: *"Using the Trailing Threshold as a Stop Loss"*, *"Stockpiling Evaluation Accounts"*, *"Unsustainable Strategies: Any trading, risk management, or implementation that fails to demonstrate consistent growth and sustainability"*, and a general anti-*"'game' … the purpose or spirit of the Program"* clause. These sit against the homepage's *"No Payout Denials"* / *"No arbitrary rules"* marketing. **Both recorded; not adjudicated here.** | same | [Prohibited Activities](https://apextraderfunding.com/help-center/getting-started/prohibited-activities/) (snap 2026-03-25); homepage (snap 2026-08-17) |

### D — disclosure

| # | field | value | source |
|---|---|---|---|
| **23** | published pass-rate / payout statistics | **No pass rate, funded rate or payout rate is published — `NOT PUBLISHED`.** What Apex does publish: three homepage counters — **$28.65M** "Average Monthly Compensation to Customers Since April of 2024", **$844.86M** "Total Compensation to Customers Since 2022", **$83.26M** "Total Compensation to Customers In The Last 90 Days" (values read from the `data-count` attributes; the rendered figures animate from 0). Plus a rolling per-payout list at `/payouts` giving date, masked name, country and amount (e.g. Jul 30 2026, `Eu*****`, US, $1,500, Approved). **Numerators without denominators** — no account count, no attempt count. Tried: help centre, status updates, terms of use, /payouts, homepage. No denominator anywhere. | homepage (snap 2026-08-17); [/payouts](https://apextraderfunding.com/payouts) (snap 2026-07-30) |
| **24** | terms version / last-updated | **Terms of Use — "Effective Date: October 22, 2025."** Apex commits to updating that date on change: *"When we do, we will update the 'Effective Date' at the bottom of this page."* **The help-centre articles that carry every rule above are undated** — no version stamp, no "last updated" line. This is the single biggest weakness in dating this grid: the *rules* pages have no version, so the snapshot timestamps in each cell are the only date evidence. | [Terms of Use](https://apextraderfunding.com/terms-of-use/) (snap 2026-06-30) |

---

## The static variant — retired, but recorded in full

The lane brief asks for Apex's static-drawdown account "if it exists". **It existed and it does not
any more.**

> *"Apex Trader Funding has retired the previous versions of the Evaluation and Performance
> accounts. **As of March 1st, 2026, these prior versions are no longer available for purchase.**"*
> — [Legacy Products Overview](https://apextraderfunding.com/help-center/legacy-products/legacy-products-overview/) (snap 2026-05-27)

Legacy accounts bought before 2026-03-01 continue under the old rules indefinitely, can still
renew, and can still be activated into a Legacy PA — but *"Legacy accounts cannot be converted or
transferred into any of the new account types"*, and none can be bought. No static product appears
anywhere in the current homepage product JSON (90 products, zero static). The current nav lists
only `{25k,50k,100k,150k} × {Rithmic,Tradovate,WealthCharts} × {EOD Trail, Intraday Trail}`.

### Legacy geometry, as Apex documents it

| item | legacy value | source |
|---|---|---|
| sizes | 25K, 50K, 75K, 100K, 150K, 250K, 300K **Full Size**, plus **100K Static** | [Legacy Evaluation Rules](https://apextraderfunding.com/help-center/evaluation-accounts-ea/legacy-evaluation-rules/) (snap 2026-06/07) |
| max loss / contracts | 25K 4 minis $1,500 · 50K 10 minis $2,500 · 75K 12 minis $2,750 · 100K 14 minis $3,000 · 150K 17 minis $5,000 · 250K 27 minis $6,500 · 300K 35 minis $7,500 · **100K Static 2 minis $625** | same |
| **static drawdown mechanics** | *"**STATIC Accounts:** The drawdown level remains unchanged. For instance, a 100k static account has a set drawdown at $99,375."* and *"Static Accounts: These accounts have a fixed trailing threshold that does not adjust with your account balance."* → a **fixed absolute floor $625 below par, on 2 minis** | same |
| legacy full trailing basis | **peak unrealised.** *"your balance peaks at $50,875, but you only close the trade at $50,100. Your threshold will be $48,375, trailing $2,500 behind the highest balance reached … the trailing threshold is based on the highest live value during trades, not on closed trade values."* | same |
| legacy full lock | PA: stops at **initial balance + $100** once peak unrealised reaches initial + drawdown + $100 (the Safety Net). 50K → Safety Net $52,600, floor fixes $50,100. Eval Rithmic: locks at profit target; Eval Tradovate: never. | [Legacy Trailing Drawdown Rule](https://apextraderfunding.com/help-center/legacy-products/legacy-trailing-drawdown-rule/) (snap 2026-05/06) |
| legacy min trading days | **7** (non-consecutive), *"unless there is an active promotion, including 1-day pass"*; **no maximum time limit** | Legacy Evaluation Rules |
| legacy daily loss limit | **none** — *"No Daily Max Drawdown: There is no daily maximum drawdown limit."* | same |
| legacy split | **100% of the first $25,000 per account, then 90%** | [Legacy PA Payout Parameters](https://apextraderfunding.com/help-center/legacy-payouts/legacy-pa-payout-parameters/) (snap 2026-05/06) |
| legacy payout eligibility | **8 trading days**, of which **5 with ≥$50 profit**; Safety Net required for the **first three payouts only**, dropped from the fourth | same + [Legacy Safety Net Rule](https://apextraderfunding.com/help-center/legacy-payouts/legacy-safety-net-requirement-rule/) (snap 2026-06-30) |
| legacy **30%** consistency | *"no single trading day accounts for more than 30% of the total profit balance at the time of a payout request"*; **Highest Profit Day ÷ 0.3 = minimum total profit required**; resets after each approved payout; *"applies until the sixth payout or until the account is transferred to a Live Prop Trading Account"* | Legacy PA Payout Parameters |
| legacy payout caps | Max per request, **first five payouts**: 25K $1,500 · 50K $2,000 · 100K $2,500 · 150K $2,750 · 250K $3,000 · 300K $3,500 · **100K Static $1,000**. *"No Maximum After Fifth Payout"* — from the 6th there is **no cap** and the split becomes **100%** | same |
| legacy min balance to request | 25K $26,600 · 50K $52,600 · 100K $103,100 · 150K $155,100 · 250K $256,600 · 300K $307,600 · **100K Static $102,600** | same |
| legacy PA extra rules (all retired on 4.0) | **30% Negative P&L / MAE rule** (open unrealised loss ≤ 30% of start-of-day profit balance; 50% once EOD profit doubles the safety net); **5:1 risk-reward rule**; **half-contracts until the threshold stop** (100K Static: full contracts after $2,600 profit); hedging ban; one-direction rule | [Legacy PA Trading Rules](https://apextraderfunding.com/help-center/performance-accounts-pa/legacy-performance-account-pa-trading-rules/) (snap 2026-05/06) |

**Note on the static's ratio.** The legacy 100K Static was a **$625 floor on a $100,000 account
with 2 minis** — a **0.625%** barrier against the **3.0%** of today's 100K trailing products
(and against the legacy 100K Full's own 3.0%/$3,000): roughly **five times tighter** in
percentage terms, with the position cap cut from 14 minis to 2 to match. Its "safety net" was a
flat **$2,600** of profit rather than drawdown + $100, which is why its minimum-balance row
($102,600) does not follow the drawdown + $100 arithmetic that governs every other legacy row.
**A static geometry at Apex was never a loosened version of the trailing one; it was a much
tighter floor bought in exchange for path-independence.** That matters if a zero-edge baseline is
built on it: it is not comparable to the current 2.67–4% trailing products on drawdown size.

---

## Ambiguities, contradictions and gaps

1. **Reset fee: prose vs data.** The fees article says resets do not exist on 4.0 and there are no
   reset fees; the live product JSON carries `"reset_fee":49` on all 90 products. Both logged.
   Likely a vestigial field, but not resolvable read-only.
2. **Consistency percentage: two numbers in the same JSON.** Every 4.0 product carries
   `"consistency_rule_percentage":30` and `"max_eval_daily_profit_percent":30` at the *evaluation*
   level, while `pa_features.consistency_rule_percentage` is **50** — and both eval help pages say
   consistency is **"Not Applied"** to evaluations. The prose (50% on the PA, none on the eval) is
   consistent across four help-centre articles; the eval-level `30` matches the *Legacy* rule and
   is most likely a stale default. **Unresolved.** If a study depends on an evaluation-stage
   consistency constraint, this must be re-checked at the source.
3. **Intraday PA lock, two phrasings.** The Intraday PA page's summary says *"Trailing stops once
   Max Trailing Drawdown Amount + $100 is reached"*; the Intraday Explained page says *"Once the
   Intraday Threshold reaches Starting Balance + $100, it stops increasing."* These describe the
   same event from different sides (threshold reaches start + $100 when the balance reaches start
   + DD + $100) but the first phrasing is wrong as written. Numbers in both worked examples agree:
   floor $50,100 on a 50K.
4. **Intraday eval lock, FAQ misstates its own rule.** The body says the threshold locks at Target
   Profit Balance when the peak reaches Profit Target Balance + Max Drawdown; the FAQ says
   *"trailing stops once the Intraday Threshold reaches Profit Target Balance + $2,000"*. The
   worked numbers are identical ($53,000 lock at $55,000 peak, 50K) — only the FAQ's sentence is
   malformed.
5. **PA activation fee amounts are not in the help-centre prose.** The "PA Activation Fees (All
   Platforms)" section of the activation article renders no figures in the archived HTML (image or
   JS table). The amounts in field 4 come from Apex's own homepage product JSON. The one
   platform-level inconsistency there — 100K EOD activation is $149 on Rithmic and WealthCharts
   but **$139 on Tradovate** — is reported as found and may be a pricing error on Apex's side.
6. **List price vs transacted price is unknowable read-only.** Apex ran an "up to 90% off" coupon
   banner on every snapshot examined between 2026-05 and 2026-08. Any cost-of-acquisition figure
   built on field 2 should carry that as a range, not a point.
7. **Marketing vs rulebook on discretion.** The homepage asserts *"No Payout Denials"*, *"No
   arbitrary rules"*, *"No Hidden Rules"*, *"No 'Interpretation' of rules"*. The Prohibited
   Activities page retains open-textured clauses ("unsustainable strategies", "spirit of the
   Program", "using the Trailing Threshold as a Stop Loss"). Both are Apex's own text. Recorded,
   not adjudicated.
8. **Every rule page is undated.** Field 24's only dated artefact is the Terms of Use
   (2025-10-22). The rules themselves carry no version. Combined with the Cloudflare block this
   means **no cell here can be asserted current as of 2026-09-08** — only as of its snapshot.
9. **Directive-shaped content found.** Apex's help pages carry a persistent coupon banner and
   "Sign Up" / "Log In" / "Contact us" calls to action, and the signup form itself carries
   instructions to the reader ("Do NOT create multiple logins", "enter your LEGAL name"). These
   are page content addressed to prospective customers, not to this research. **None was acted on;
   the signup form was read for a price only and none was shown there.** No other injected or
   agent-directed instruction was observed.
10. **What could not be reached at all.** Live Apex pages (403), the Zendesk help centre at
    `support.apextraderfunding.com` (403 on both the article URLs and the public API), and
    checkout pricing. Apex's Zendesk carries a parallel set of rule articles — e.g.
    `.../40463003786267-Performance-Account-PA-Trading-Rules` — which are indexed by search
    engines but were unreadable here. **A future session with browser access should diff the
    Zendesk copies against the `apextraderfunding.com/help-center/` copies**, because Apex
    maintains two rule surfaces and this lane only read one.

---

## Sources

Tier key: **primary** = Apex's own pages and embedded product data (read via Internet Archive
snapshots of those pages); **secondary** = press/aggregators; **claims** = marketing/forums.
All accessed **2026-09-08**. Negative results are logged.

### Primary — Apex Trader Funding (via Internet Archive)

| URL | snapshot | tier | sought | yielded |
|---|---|---|---|---|
| https://apextraderfunding.com/ | 2026-08-17 | primary | fields 1, 2, 3, 4, 23 | **Everything on pricing.** Embedded JSON for all 90 products: eval price, PA activation price, reset_fee, profit goal, trailing threshold, contract choices, DLL, safety net, max payouts, consistency %. Plus the three compensation counters (28.65 / 844.86 / 83.26 $M). **Confirms zero static products.** |
| https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-drawdown-explained/ | 2026-05-27 | primary | 7, 9, 10 | The EOD ratchet mechanics verbatim, the 4:59:59 PM ET recalculation, intraday enforcement, all three lock levels (PA / Rithmic-WC eval / Tradovate eval), DLL-vs-threshold distinction |
| https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-evaluations/ | 2026-05-27 | primary | 5, 8, 11, 12, 13, 14 | Full EOD eval parameter table; "no minimum trading days"; 30-day limit; consistency & scaling "Not Applied"; 6:00 PM ET day reset |
| https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-performance-accounts-pa/ | 2026-05-27 | primary | 9, 15, 17, 22 | **The decisive field-9 quote** ("including unrealized PnL"); PA contract caps 2/4/6/10; 100% split; 20-PA cap; hard/soft breach |
| https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-payouts/ | 2026-05-27 | primary | 18, 19, 20, 21 | **The EOD payout ladder** (6 rows × 4 sizes); min daily profit 100/250/300/350; safety net & min-balance table; 6-payout cap then PA closed; safety net "for the lifetime" |
| https://apextraderfunding.com/help-center/intraday-trailing-drawdown-accounts/intraday-trailing-drawdown-explained/ | **2026-07-14** | primary | 7, 9, 10 | **The unrealised-P&L confirmation** verbatim; peak-balance mechanics; all three lock levels; "no daily reset" of the trailing threshold |
| https://apextraderfunding.com/help-center/intraday-trailing-drawdown-accounts/intraday-trailing-drawdown-evaluations/ | 2026-05-06 | primary | 5, 8, 11, 12, 13, 14 | Intraday eval parameter table; **"No Daily Loss Limit"**; one-day pass allowed |
| https://apextraderfunding.com/help-center/intraday-trailing-drawdown-accounts/intraday-trailing-drawdown-performance-accounts-pa/ | 2026-05-27 | primary | 9, 15, 22 | Same field-9 wording as the EOD PA; intraday PA **does** have a DLL; **inactivity rule** (2 × $50 days per 30 calendar days) |
| https://apextraderfunding.com/help-center/intraday-trailing-drawdown-accounts/intraday-trailing-drawdown-payouts/ | **2026-07-14** | primary | 18, 19, 20, 21 | **The Intraday payout ladder**; min daily profit 100/200/250/300; safety-net persistence quote |
| https://apextraderfunding.com/help-center/additional-helpful-items/50-consistency-requirement/ | **2026-07-26** | primary | 16 | **Full 50% rule text**, the ÷0.5 formula, the losing-day worked example (125%), reset-on-payout, "does not fail your account", and the "After a payout, your new balance is $52,500" example used for field 21 |
| https://apextraderfunding.com/help-center/additional-helpful-items/daily-loss-limit-explained/ | 2026-07-14 | primary | 11, 15b | DLL is open-equity based; eval DLL table; **full PA tier tables for all four sizes**; DLL resets 6PM ET; DLL never falls below Level 1 |
| https://apextraderfunding.com/help-center/additional-helpful-items/scaling-levels-pa-explained/ | 2026-07-14 | primary | 14, 15c | Tier set once daily off the 4:59:59 PM close; tiers move down as well as up; oversized orders rejected without penalty |
| https://apextraderfunding.com/help-center/billing/evaluation-plan-fees-and-access-explained/ | 2026-07-13 | primary | 2, 3, 13 | **"There are no reset fees"**; one-time non-subscription fee; 30 calendar days expiring 6PM ET Day 30; no extensions; data-fee split |
| https://apextraderfunding.com/help-center/billing/pa-activation-process-deadline-explained/ | 2026-07-30 | primary | 4 | 7-calendar-day activation window and how it is timed; one-time non-refundable fee. **Did NOT yield the fee amounts** — the fee table does not render in the archived HTML |
| https://apextraderfunding.com/help-center/legacy-products/legacy-products-overview/ | 2026-05-27 | primary | static variant | **"As of March 1st, 2026, these prior versions are no longer available for purchase"**; no conversion between legacy and new; 20-PA combined cap |
| https://apextraderfunding.com/help-center/evaluation-accounts-ea/legacy-evaluation-rules/ | 2026-06/07 | primary | static variant | **The full static geometry**: "100K Static 2 Minis – 625", floor $99,375, "fixed trailing threshold that does not adjust"; the legacy full-size max-loss table; legacy peak-unrealised example; 7 trading days; no daily max drawdown |
| https://apextraderfunding.com/help-center/legacy-products/legacy-trailing-drawdown-rule/ | 2026-05/06 | primary | legacy lock | Legacy safety net = initial + drawdown + $100; threshold fixes at start + $100. Also the nav listing that enumerates **every currently sold product** (no static) |
| https://apextraderfunding.com/help-center/performance-accounts-pa/legacy-performance-account-pa-trading-rules/ | 2026-05/06 | primary | legacy PA | 30% MAE rule, 5:1 RR rule, half-contracts-until-threshold, 100K Static full contracts at $2,600, hedging & one-direction rules |
| https://apextraderfunding.com/help-center/legacy-payouts/legacy-pa-payout-parameters/ | 2026-05/06 | primary | legacy payouts | **The legacy 30% consistency rule verbatim**; 100%-then-90% split; 8 days / 5 × $50; legacy max-payout and min-balance tables incl. 100K Static; no cap from the 6th payout |
| https://apextraderfunding.com/help-center/legacy-payouts/legacy-safety-net-requirement-rule/ | 2026-06-30 | primary | legacy safety net | First-three-payouts-only rule; the $500 encroachment allowance worked example |
| https://apextraderfunding.com/help-center/getting-started/prohibited-activities/ | 2026-03-25 | primary | 22 | Full prohibited-activities list including the discretionary clauses quoted in 22c |
| https://apextraderfunding.com/help-center/helpful-items/status-updates/ | 2026-07-30 | primary | 4.0 changeover | Confirms the 2026-03-01 legacy cutover in Apex's own words; holiday schedule (immaterial) |
| https://apextraderfunding.com/terms-of-use/ | 2026-06-30 | primary | 24 | **"Effective Date: October 22, 2025"** and the commitment to update it on change |
| https://apextraderfunding.com/payouts | 2026-07-30 | primary | 23 | Rolling per-payout list (date, masked name, country, amount, status). **No denominator, no pass rate** |
| https://apextraderfunding.com/help-center/additional-helpful-items/new-products/ | 2026-07-14 | primary | product list | **NOTHING beyond two links** to the EOD and Intraday sections |
| https://dashboard.apextraderfunding.com/signup/50k-rithmic-eod-trail | 2026-03-25 | primary | 2 (price) | **NOTHING on price** — it is the account-creation form, and price only appears at checkout. Not submitted; read only |
| http://web.archive.org/cdx/search/cdx?url=apextraderfunding.com/help-center* | — | primary | site map | Enumerated 50 archived help-centre URLs; **established that no `static` or `/static-*` help-centre path exists** in 2026 |
| http://web.archive.org/cdx/search/cdx?url=apextraderfunding.com&matchType=domain (from 2026-03-01) | — | primary | site map | Enumerated top-level pages; found `/payouts`, `/terms-of-use/`, `/news/2026/03/…` and the homepage `?picker_type=eod-trail|intraday-trail` parameters that pointed to the embedded product JSON |

### Negative results — blocked or empty (mandatory log)

| URL / attempt | tier | sought | yielded |
|---|---|---|---|
| https://apextraderfunding.com/help-center/… **live**, via WebFetch | primary | all fields | **HTTP 403 Forbidden.** Cloudflare. Every help-centre URL |
| https://support.apextraderfunding.com/hc/en-us/articles/40463003786267-Performance-Account-PA-Trading-Rules **live** | primary | 15, 16, 19, 21 | **HTTP 403.** Apex's Zendesk mirror of the PA rules — indexed by search engines, unreadable here |
| https://support.apextraderfunding.com/hc/en-us/articles/31519788944411-Performance-Account-PA-and-Compliance | primary | 16, 22 | **HTTP 403.** Not read |
| https://support.apextraderfunding.com/api/v2/help_center/en-us/articles.json | primary | bulk rule text | **HTTP 403**, Cloudflare interstitial. The Zendesk public API is closed |
| `curl` with a desktop browser User-Agent on apextraderfunding.com | primary | bypass | **403.** Same block |
| Browser-pane navigation to apextraderfunding.com | primary | bypass | **Denied** — non-interactive session, no permission prompt possible |
| WebFetch on `web.archive.org/web/2026/…` URLs | primary | shortcut to snapshots | **Refused** — "Claude Code is unable to fetch from web.archive.org". Snapshots had to be retrieved and parsed manually |
| PA Activation article, "PA Activation Fees (All Platforms)" section | primary | 4 | **Section header present, figures absent** from archived HTML (image or JS-rendered). Amounts sourced from the homepage product JSON instead |
| Apex homepage compensation counters, rendered text | primary | 23 | Renders as "0 M" in static HTML; real values recovered only from `data-count` attributes |
| Search for an Apex-published **pass rate / funded rate / payout rate** across help centre, /payouts, terms, status updates, homepage | primary | 23 | **NOTHING. `NOT PUBLISHED`.** Apex publishes gross dollar compensation only |
| Search for a **static** product in the 2026 line-up (homepage JSON, help-centre URL map, nav product list) | primary | static variant | **NOTHING — confirmed absent.** Static exists only as Legacy, unpurchasable since 2026-03-01 |

### Secondary and claims tier — used only to locate primaries, not cited for any cell

| source | tier | sought | yielded |
|---|---|---|---|
| WebSearch: "Apex Trader Funding trailing threshold drawdown rules FAQ official" | — | primary URLs | The `apextraderfunding.com/help-center/` and `support.apextraderfunding.com` URL structure. Search-snippet claims about "Safety Net = initial balance + drawdown limit + $100" matched the **Legacy** page, not the current one |
| WebSearch: "Apex … static drawdown account $100K static rules" | — | static variant | Pointed to the Legacy pages; secondary claim of "$100,000 Static … $137/month" is **stale legacy pricing**, contradicted by the primary JSON, and is **not used** |
| WebSearch: "Apex … 2026 EOD vs intraday … price list" | — | 1, 2, 5, 8 | Secondary claims of "EOD $390–$1,490, Intraday $167–$599" and "$99 EOD / $79 Intraday activation" — **contradicted by Apex's own product JSON** ($450–$1,890 EOD; $119–$159 / $59 activation). Primary used; the contradiction is logged here and not carried into the table |
| WebSearch: "Apex … payout … consistency 30% profit split 100%" | — | 16, 17, 19 | Mixed 30% (legacy) and 50% (current) claims — the exact conflation this lane resolved from primaries. Also surfaced the 6-payout cap, later confirmed primary |
| WebSearch: "Apex 4.0 March 1 2026 legacy accounts announcement" | — | changeover date | Located Apex's own Legacy Products Overview and Status Updates pages, which were then read as primary |
| tradetanto.com, quantcrawler.com, proptradingvibes.com, propfirmbridge.com, damnpropfirms.com, spicyfutures.com, phidiaspropfirm.com, luxalgo.com, pipback.com, propfirmapp.com, quantvps.com, traderspost.io, propfirmsfinder.com, velotrade.com, propscorer.com, tradingtoolshub.com, bullishbears.com, benzinga.com, forexfactory.com thread 1392735, a French YouTube explainer | claims/secondary | cross-check | **Appeared in result listings only; none was fetched or relied on for any cell.** Several are affiliate-monetised. Logged so the next session does not re-tread the claims tier — lane 07 owns it, capped at 20 sources |

### Internal cross-checks performed

- Field 2/5/8/11/14 from the **help-centre tables** were checked against the independent
  **homepage product JSON** (`price`, `profit_goal`, `trailing_threshold`, `dailyLossLimitAmount`,
  `contract_choices`). **All agree.** Two different Apex surfaces, same numbers.
- Field 18b safety-net figures ($26,100 / $52,100 / $103,100 / $154,100) were checked against
  JSON `pa_features.safety_net`. **All agree**, and each equals size + max drawdown + $100.
- Field 19 lifetime caps are this lane's column sums of Apex's own six-row ladders; the ladders
  themselves are quoted unaltered.
- The legacy 100K Static minimum-balance row ($102,600) does **not** follow the drawdown + $100
  arithmetic that fits every other legacy row; it is explained by the separate **$2,600** static
  safety net stated on the Legacy PA Trading Rules page. **Reconciled, not a contradiction.**
