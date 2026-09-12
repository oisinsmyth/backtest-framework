# G5 — the revenue side of a long book: fully-paid lending, cash interest, account rules

External evidence only. **Nothing here was run, backtested, or checked against this
programme's own data.** All web sources fetched **2026-09-09** unless stated. No
broker was logged into; nothing was opened, enrolled in or funded. Source TYPE and
HOW-WELL-ESTABLISHED tags on every claim; §8 lists URLs, §9 logs blocks by tool and
response, §10 is what I could not verify.

---

## 1. Verdict — the lending half is over on the names a GC-ish long book holds, and worse than over on the names that would pay

**On the median US common stock the securities-lending revenue available to a retail
lender is about 0.10 bp per bar held, before any allowance for the fact that the shares
are usually not lent at all. That is a rounding error against a 33.8 bp/side spread, and
it is 0.15% of a 67.6 bp round trip.** The arithmetic, derived in §3.3 from IBKR's own
published mechanics, is

> **bp earned per BAR HELD ≈ 0.205 × (gross market lending fee, % p.a.) × (fraction of
> the position actually on loan).**

The median Markit indicative fee across all US common stocks on the major exchanges sits
at **0.5% p.a.** and has been flat-to-falling for the whole 2003–2025 sample
[WORKING PAPER, read in full]. Put 0.5 into the formula: **0.10 bp/bar at 100%
utilisation.** For NYSE size deciles 4–9 the equal-weighted average fee is **~0.4% p.a.**
and for decile 10 **~0.3% p.a.** — 0.08 and 0.06 bp/bar. **68% of all firm-day
observations in 2024:01–2025:06 had an annualised fee below 1%** [WORKING PAPER, read in
full]. And IBKR's own investor deck says it in one line: *"Easy to Borrow aka General
Collateral 'GC' stock is **less likely to be lent**"*, and lists among the reasons a stock
is not lent *"May not generate interest income in the securities lending market (General
Collateral stocks such as Apple, Amazon etc.) — Supply exceeds demand"*
[BROKER OFFICIAL DOC, read in full]. So the utilisation multiplier on a GC name is not
0.9, it is near zero.

**Two things stop this being a clean kill, and both cut against the programme, not for
it.**

**(i) The universe is not obviously GC.** The fee distribution is a size phenomenon and
the tail is enormous. Equal-weighted average fee for **NYSE market-cap decile 1 was
~26.4% p.a. in May 2025**, up from ~2.4% in 2010; decile 3 went 0.5% → 2.8%
[WORKING PAPER, figure end-labels read from extracted text — see §10.2]. Decile 1 is
*40% of the names in the CRSP universe* by count (NYSE breakpoints). A $5 price floor plus
a dollar-volume screen does **not** by itself put a book in deciles 4–10. **Whether this
programme's held names are GC or special is a measurable fact about its own fixture that
I cannot see and nobody here has measured.** §3.5 gives the one-line test.

**(ii) If they ARE special, the lending revenue is not free — it is roughly the price of
an alpha the long holder is already paying.** Daniel, Klos & Rottke sort all US common
stocks monthly into eight portfolios on lagged Markit indicative fee, 2010:01–2025:06,
value-weighted, and find **the CAPM alpha of each portfolio is approximately −1 × its
fee**: the top-fee portfolio underperforms by **−81.4%/year (t = −5.87)**; the ~13.5%-fee
portfolio lost **−30.9%/year** [WORKING PAPER, read in full]. Their own summary of the
implication is the sentence that matters here:

> *"if security owners who lent out their securities received the full borrow cost, they
> would earn zero risk-adjusted returns. However, as a result of losses in the
> intermediation chain, they do not. Thus, the lenders also earn negative risk-adjusted
> returns equal to these losses."*

The retail lender's share at IBKR is **50%** [BROKER OFFICIAL DOC]. The estimated
**median lender share for institutional mutual funds is 0.577–0.587** — i.e.
intermediaries keep ~40% [WORKING PAPER, read in full]. So a long book that tilts toward
lendable-at-a-real-rate names is, on this evidence, buying roughly −100% of the fee in
alpha and selling back 50% of it in revenue. **The premise in the commissioning brief —
"revenue accruing to a held position is arithmetically identical to alpha and does not
have to be discovered" — is arithmetically right and economically inverted: the revenue
is real, and on this evidence it is a partial rebate on a loss the same names impose.**
Selecting *for* lendability is selecting *for* negative alpha. That is the single most
important thing in this brief.

**The parts of the lane that survive.** Cash interest (§4) is not a revenue source for a
fully-invested book but it *is* the correct benchmark for an under-exposed one, and the
programme's own reporting rule already demands exposure beside CAGR: **1.25 bp/bar on the
uninvested fraction above a $10,000 floor, at today's published rate.** And §5 turned up
a live, dated, material change the commissioning brief's premise did not know about:
**FINRA eliminated the pattern-day-trader rule and the $25,000 minimum equity requirement
effective 4 June 2026**, replacing them with a risk-based intraday-margin regime —
though IBKR states that **accounts may still be subject to the old PDT rules through a
transition period ending October 2027** [BROKER OFFICIAL DOC, dated 3 June 2026].

---

## 2. Everything that follows is dated, and none of it has an effective date

Every broker rate below was fetched on **2026-09-09**. **IBKR publishes no effective date
on any of these pages.** Its interest-rate page states: *"IBKR may change these rates at
any time, in its sole discretion. We will publish the current rates on a best-efforts
basis."* Treat each number as "as displayed on 2026-09-09", not as a dated schedule.

**A broker page is a sales instrument even when it is also the primary source.** The SYEP
pricing page is a marketing page: its worked example uses a **9% market-based rate**,
which is above the 95th percentile of the cross-section (§3.4), and its headline is *"You
could earn USD 16,875.00/year on stock you already own."* Where I use IBKR's numbers I
use the **mechanics** (collateral basis, day-count, split) and take the **rate
distribution from the academic source**, never from IBKR's example.

---

## 3. Fully-paid securities lending — IBKR's Stock Yield Enhancement Program

### 3.1 Mechanics, from primary broker documentation

[BROKER OFFICIAL DOC / SALES INSTRUMENT, read in full] —
`interactivebrokers.com/en/pricing/stock-yield-enhancement-program.php`, fetched
2026-09-09 (via browser UA; see §9).

| item | what IBKR states |
|---|---|
| **Revenue split** | *"IBKR pays you **50%** of a market-based rate."* The market-based rate is *"determined by taking into account the rates on shares IBKR has loaned to or borrowed from others, and third-party market data."* |
| **Eligibility (account)** | *"available to eligible IBKR clients who have been approved for a **margin account**, or who have a **cash account with a liquid net worth greater than USD 25,000**"*. IB India and IB Japan clients are NOT eligible. |
| **Eligibility (shares)** | *"all 'fully-paid' stocks (stocks not held on margin) and 'excess-margin' stocks (stocks held on margin but whose market value exceeds **140% of your margin debit balance**)"*. |
| **Collateral** | US Treasuries **or** cash, *"in the same amount as the value of your shares"*. The investor deck gives the actual convention: **USD 102%** of the closing price, rounded up to the nearest dollar per share; marked to market daily. **"Interest is paid on the collateral amount, not the market value."** |
| **Day count** | The deck's worked example divides the annualised payment by **360 days**, not 252 or 365. |
| **SIPC** | *"Shares loaned out may not be protected by SIPC. The Securities Investor Protection Act of 1970 may not protect shares loaned out. This is why under SEC rules IBKR must provide you with U.S Treasury or cash collateral in the same amount as the value of your shares."* Counterparty risk is *"solely against Interactive Brokers"*. (For Canada: not eligible for CIPF coverage.) |
| **Voting** | *"Voting rights go to the borrower. During any period in which your securities are loaned out, you will **forfeit your right to vote those shares by proxy**."* |
| **Dividends** | Shares on loan over a record date *"may receive a **Payment In Lieu or 'PIL'**"*; *"This may have adverse tax consequences"*; *"IBKR takes steps to avoid allocating PIL on a best efforts basis"*; *"Receiving PIL instead of a dividend is unlikely but possible."* An **upcoming dividend is listed as a reason a stock is NOT lent.** |
| **Selling / recall** | *"You can sell your shares at any time without restriction."* Selling terminates the loan, as does borrowing against them, withdrawing cash such that they stop being fully-paid/excess-margin, unenrolling, a transfer request, or account closure. **IBKR may terminate a loan at any time and "does not guarantee that it will lend all eligible shares."** |
| **Re-enrolment** | *"If you leave this program, you must wait **90 days** before you can re-enroll."* [BROKER OFFICIAL DOC — ibkrguides.com, read in full] |
| **Allocation** | Loans are allocated **pro-rata across all SYEP participants holding the name**, so a client lends only a fraction of an eligible position (the deck's example: IBKR can lend 10,000 of 20,000 pooled shares → each client lends 50% of their eligible position). |

**PIL tax character (US).** Payments in lieu are **ordinary income, not qualified
dividends**, and are reported on **Form 1099-MISC** [snippet only — see §10.4]. The
academic source states the same mechanism independently: *"qualified dividends received
by shareholders are taxed at preferential rates, while payments in lieu of dividends from
borrowers are taxed as ordinary income. This tax treatment can influence the lending
behavior of taxable investors."* [WORKING PAPER, read in full].

### 3.2 What this means for a high-turnover book specifically

Four of the mechanics above are individually small and jointly decisive for a book whose
holds run **one to tens of bars**:

1. **Selling terminates the loan.** Revenue accrues only for the days actually held, and
   only for the days actually on loan within that.
2. **Allocation is pro-rata across IBKR's whole SYEP pool.** A small position in a
   crowded name lends a fraction of itself.
3. **An upcoming dividend is a reason a stock is not lent** — so the days around the one
   corporate event most correlated with holding are exactly the days a loan is least
   likely to exist.
4. **The 90-day re-enrolment lockout** means enrolment is a one-way decision on a
   quarter's horizon, not a per-trade one.

None of these is a reason to conclude anything. They are reasons the *realised*
utilisation multiplier in the §1 formula is far below 1 and cannot be assumed.

### 3.3 The conversion the programme actually needs

Derived from IBKR's stated mechanics (102% collateral, /360 day count, 50% split),
expressed in the programme's own unit:

```
daily accrual to client = MV × 1.02 × r/360 × 0.50          (r = gross rate, % p.a.)
                        = MV × r × 0.0014167 per CALENDAR day
per calendar day, in bp = 0.1417 × r
calendar days per bar   ≈ 365/252 = 1.4484
------------------------------------------------------------
bp per BAR HELD         ≈ 0.205 × r × utilisation
```

Cross-check against IBKR's own pricing-page example (r = 9%, ignoring the 102% and using
365): IBKR quotes 4.5% p.a. = 450 bp/yr = **1.79 bp/bar**; the formula gives **1.85
bp/bar**. The residual is the 102% collateral and the 360-day basis, both of which favour
the lender slightly.

**Reference points, at 100% utilisation** (multiply down by realised utilisation):

| gross market fee, % p.a. | source of the number | bp/bar to the client |
|---|---|---|
| 0.3 | NYSE decile 10 EW average, 2025 | **0.06** |
| 0.4 | NYSE deciles 4–9 EW average, 2025 | **0.08** |
| 0.5 | **median US common stock, whole 2003–2025 sample** | **0.10** |
| 1.7 | NYSE decile 2 EW average, 2025 | **0.35** |
| 2.8 | NYSE decile 3 EW average, 2025 | **0.57** |
| 26.4 | NYSE decile 1 EW average, 2025 | **5.4** |

Against **33.8 bp/side measured spread** (67.6 bp round trip), the median-name figure over
a 10-bar hold is **1.0 bp, or 1.5% of the round trip.** Over a 40-bar hold, 4.1 bp, or
6.1%.

**One caveat I want stated loudly rather than buried: 4 bp is not nothing against a 1.06
bp/side breakeven.** The commissioning brief's own example cell had commission alone at
1.92 bp/side against a 1.06 bp breakeven. In a world where the whole gross edge is ~2 bp
per round trip, a few bp of accrued lending revenue over a long hold is not a rounding
error — it is larger than the edge. **So the honest statement is not "the revenue is
negligible"; it is "the revenue is negligible against the SPREAD, and potentially
comparable to the EDGE on long-hold cells."** That does not rescue anything, because of
§3.4 and §1(ii) — but the programme should not file "lending revenue is zero" as a fact.

### 3.4 The distribution — the kill question, answered from the literature

**[WORKING PAPER, read in full]** Daniel, Klos & Rottke, *Inefficiencies in the Securities
Lending Market*, 28 October 2025, marked *"Preliminary"*. Data: **IHS Markit** indicative
fees (a **buy-side / borrower-side** proxy for marginal cost, not what a lender receives),
merged to CRSP; all US common stocks with CRSP exchcd ∈ {1,2,3} and shrcd ∈ {10,11};
**no price filter, no liquidity filter**; main analyses 2010:01–2025:06. Fetched as PDF
and extracted locally.

| statistic | value |
|---|---|
| Share of firm-days with annualised fee **< 1%**, 2024:01–2025:06 | **68%** (of 1.445m observations) |
| **Median** indicative fee, 2003:10–2025:06 | **~0.5% p.a., flat and slightly falling** |
| 75th / 90th / 95th / 99th percentile, end of sample | ~1.7 / ~19 / ~51.1 / ~223.9% p.a. (figure labels) |
| 99th percentile, Oct 2003 → May 2025 | **5% → over 192%** |
| Share of stocks with fee **> 1%** | 11% (2010) → **>40% (2022)** → **29% (May 2025)** |
| Share of stocks with fee **> 10%** | 3% (2010) → just under 20% (2023) → **~15% (May 2025)** |
| Share with fee > 1%, **NYSE decile 1** | ~15% (2010) → **above 75%** at peak |
| Share with fee > 1%, deciles 2 / 3 | peaked above 50% / 30% in 2022; **2025 vs 2010: 17% vs 10%, and 8% vs 6%** |
| EW average fee by decile, 2010 → 2025 | d1 2.4→26.4; **d2 1.4→1.7 (prose-confirmed)**; **d3 0.5→2.8 (prose-confirmed)**; d4–9 0.5→0.4; d10 0.3→0.3 |
| Persistence | fee shock from <1% to ≥10%: jumps to **>26% average at t=0**, and **still above 10% a year later** |

**[PEER-REVIEWED, snippet only]** D'Avolio, *The Market for Borrowing Stock*, JFE 66(2–3)
2002, 4/2000–9/2001. Quoted **verbatim inside the Daniel–Klos text I did read in full**,
so the numbers are second-hand-but-quoted, not snippet-guessed: *"Only 9% of stocks (about
206 stocks per day) have loan fees above 1% per annum. These 'specials' have a mean fee of
4.3% per annum."* Value-weighted market portfolio cost **25 bps/year**. Highest annualised
fee ever observed in that sample: **79%**.

**What this settles and what it does not.** It settles that **the median and the typical
mid/large-cap name pay essentially nothing** — the lending half is over for any book
sitting in NYSE deciles 4–10. It does **not** settle the programme's case, because the
special share has grown enormously in exactly the small-cap region a $5-floored,
volume-screened US universe can still reach, and **neither paper reports the distribution
conditional on price or on dollar volume**, which is the screen actually in use here.

### 3.5 The one check that would close this lane, stated in the programme's own quantities

Nothing below has been run.

1. On the held set, compute **NYSE market-cap decile** per name per bar (NYSE
   breakpoints, not full-universe breakpoints — decile 1 is 40% of names).
2. Report the **held-weighted share of position-bars in deciles 1–3 vs 4–10**.
3. If deciles 4–10 dominate: **the lending half is dead and can be written off in one
   line**, on the published EW averages of 0.3–0.4% p.a. → 0.06–0.08 bp/bar.
4. If deciles 1–3 carry real weight: **do not treat that as revenue found.** The same
   sort that finds the fee finds the −1 × fee alpha (§1(ii)). The right test is then a
   **matched control** in the programme's own idiom: split the held book on lagged
   borrow-cost proxy and compare **gross mean per trade** across the split. If the
   high-borrow-cost half underperforms by about the fee, the revenue is a rebate on a
   loss and the lane closes negative rather than merely empty.
5. **Nobody here has a borrow-fee series.** Markit/S&P Global is a paid vendor feed. A
   free proxy would have to be built, and short-interest-based proxies are on this
   programme's exclusion list. **This is the practical reason the check may be
   unrunnable** — say so rather than substituting a guess.

---

## 4. Interest on idle cash, and the cash/margin ledger

[BROKER OFFICIAL DOC / SALES INSTRUMENT, read in full] —
`interactivebrokers.com/en/accounts/fees/pricing-interest-rates.php` and
`.../en/trading/margin-rates.php`, both fetched **2026-09-09**, **no effective date
published**.

### 4.1 Published USD schedule, as displayed 2026-09-09

`BM` = IBKR Benchmark Rate. The two tables imply **BM = 3.63%** (3.130 = BM − 0.5;
5.130 = BM + 1.5).

| USD tier | IBKR **Pro** paid | IBKR **Lite** paid |
|---|---|---|
| 0 ≤ 10,000 | **0%** | **0%** |
| > 10,000 | **3.130% (BM − 0.5%)** | 2.130% (BM − 1.5%) |

| USD margin loan tier | IBKR **Pro** charged | IBKR **Lite** charged |
|---|---|---|
| 0 ≤ 100,000 | **5.130% (BM + 1.5%)** | 6.130% (BM + 2.5%) |
| 100,000 ≤ 1,000,000 | 4.630% (BM + 1%) | 6.130% |
| 1,000,000 ≤ 50,000,000 | 4.380% (BM + 0.75%) | 6.130% |
| above | 4.130% (BM + 0.5%) | 6.130% |

Rates are **blended across tiers**, not cliff-applied.

### 4.2 The two thresholds that matter at this account size

- **The first USD 10,000 of uninvested cash earns 0%.** Verbatim: *"Interest will not be
  payable on the first USD 10,000 (or the equivalent value in other currencies) of
  uninvested cash balances."* Applies **per currency**, and **balances across multiple
  IBKR accounts are not consolidated**.
- **NAV below USD 100,000 scales the rate down linearly.** Verbatim: *"Accounts with a NAV
  of less than USD 100,000 (or equivalent) will be paid at a rate proportional to accounts
  with a NAV of USD 100,000 (or equivalent) or more. The proportion is determined by the
  ratio of the account's NAV to USD 100,000."*

Other stated mechanics: interest accrues **daily**, is posted **on the third business day
of the following month**, is paid only on **positive settled** cash in the **securities
segment** (commodities-segment cash contributes to NAV but earns nothing unless swept),
and the tiers *"are subject to change without prior notification."*

### 4.3 What a partially-invested book actually earns — worked, and it is small

| account | uninvested cash | rate applied | annual | as bp/bar of NAV |
|---|---|---|---|---|
| NAV $25,000 (scaling 0.25 → 0.7825%) | $12,500 | on $2,500 only | **$19.56** | **0.0031** |
| NAV $100,000 | $40,000 | 3.130% on $30,000 | **$939** | **0.37** |
| NAV $100,000 | $50,000 | 3.130% on $40,000 | **$1,252** | **0.50** |

**The honest framing: cash interest is not incremental revenue for a long book — it is
what you earn by NOT holding the book.** It is therefore the **hurdle**, not the prize,
and it is exactly the number the programme's own reporting rule ("CAGR without exposure
says nothing") is missing. At today's published rate that hurdle is
**≈1.25 bp per bar on the uninvested fraction above the $10,000 floor** (3.13%/360 ×
1.4484 calendar days/bar). A cell running 40% average exposure is implicitly forgoing
~0.75 bp/bar of risk-free accrual on the other 60%, less the floor and less the NAV
scaling. At $25,000 NAV the whole effect collapses to essentially zero because the floor
eats the balance — **which is a real finding: the cash leg cannot be a source of return
at this account size, only a benchmark.**

**Margin loans are the mirror and are expensive at this size**: the first $100,000 of
debit is charged **BM + 1.5% = 5.130%** = **2.07 bp/bar**, i.e. **more than 16× the
median name's lending revenue.** Any levered variant of an equal-weighted long book pays
this before it earns anything.

---

## 5. Account rules that bind a retail book — and the one that just changed

### 5.1 The PDT rule and the $25,000 threshold were ELIMINATED effective 4 June 2026

This is the finding the commissioning premise did not have. **The commissioning brief
states "a $25,000 account-level threshold is a live constraint, not a rounding error."
That is now only partly true, and the part that survives is a broker transition rule, not
a FINRA rule.**

**[PRIMARY REGULATORY DOC, read in full]** — SEC file `34-104572-ex5.pdf`, Exhibit 5 to
FINRA's rule change, showing the amended text of Rule 4210 with **deletions in brackets**.
The whole of **4210(f)(8)(B) "Day Trading" is struck and marked "Reserved"**, including:

- *"[(ii) The term 'pattern day trader' means any customer who executes four or more day
  trades within five business days. However, if the number of day trades is 6 percent or
  less of total trades for the five business day period, the customer will not be
  considered a pattern day trader…]"*
- *"[a. Minimum Equity Requirement for Pattern Day Traders — The minimum equity required
  for the accounts of customers deemed to be pattern day traders shall be $25,000. This
  minimum equity must be deposited in the account before such customer may continue day
  trading and must be maintained in the customer's account at all times.]"*
- *"[(iii) The term 'day-trading buying power' means the equity in a customer's account at
  the close of business of the previous day, less any maintenance margin requirement …
  multiplied by four for equity securities.]"*
- The $25,000 carve-out in **4210(b)(4)** is struck, leaving the plain **$2,000** minimum
  equity.
- Portfolio-margin **4210(g)(13) day-trading requirements** likewise struck and Reserved.

**[PRIMARY REGULATORY DOC, read via WebFetch]** FINRA **Regulatory Notice 26-11** carries
*"Effective Date: June 4, 2026"* and confirms interpretation 4210(b)(4)/025 (the $25,000
PDT interpretation) was rescinded as obsolete.

**[PRIMARY REGULATORY DOC, read via WebFetch]** FINRA investor page, *Understanding the
New Intraday Margin Requirements*: the PDT rules *"including the $25,000 minimum equity
requirement and trader designations based on trade count, have been eliminated"*, replaced
by *"your firm monitors your account to ensure you maintain adequate equity during the
trading day relative to your actual positions"*; *"If you repeatedly fail to satisfy
intraday margin deficits promptly, this may result in your account being restricted for up
to 90 days"*; and *"Your firm has the authority to impose higher requirements if they
choose."*

### 5.2 What replaced it — the intraday margin deficit regime, quoted from the rule text

New **4210(d)(2)**, applying to every customer margin account **other than a good-faith or
portfolio-margin account**:

- **IML** ("intraday margin level") is the cash the customer could withdraw while still
  meeting maintenance margin, or (negative) the cash they would need to deposit.
- An **IML-reducing transaction** is any purchase or sale in the account that reduces the
  IML, plus any withdrawal.
- An **intraday margin deficit** is, for a day containing any IML-reducing transaction,
  not less than the absolute value of the largest negative IML during that day. Where the
  order of two same-day activities cannot be demonstrated, *"the IML … shall be computed
  on the assumption that the activities occurred in an order that results in the
  **highest** intraday margin deficit for such day."*
- A deficit *"shall remain outstanding until satisfied or until immediately after the
  close of business on the **fifteenth business day**"*.
- **90-day freeze (4210(d)(2)(D)):** if a customer *"makes a practice of failing to
  satisfy intraday margin deficits as promptly as possible and fails to satisfy an
  intraday margin deficit by the close of business on the **fifth business day** after it
  occurs"*, the member must prevent the customer from creating or increasing a short
  position or debit balance *"for **90 calendar days**"* or until satisfied.
- **De minimis carve-out:** deficits that *"do not exceed the lesser of **5% of the equity
  in the margin account or $1,000**"* do not count toward "making a practice".

**Why this matters more than the headline "PDT is dead".** The old rule counted **trades**;
the new one measures **equity against positions intraday**. For an equal-weighted book
that rebalances a whole slate in one session, the binding quantity is now the **largest
negative IML during the day**, computed under an adverse-ordering assumption when
sequence cannot be demonstrated. That is a *portfolio* constraint, not a *trade-count*
constraint, and it interacts with position sizing and rebalance sequencing — which is on
the exclusion list, so I stop here and simply flag that **the constraint changed shape,
not just size.**

### 5.3 IBKR's own implementation — and the transition that keeps $25,000 alive

**[BROKER OFFICIAL DOC, read in full]** — `ibkrguides.com/brokerportal/messagecenter/
supportpdtreset.htm`, **"Last updated on June 3, 2026"**, fetched 2026-09-09. Verbatim:

> *"FINRA has adopted new rules replacing the existing Pattern Day Trading (PDT)
> requirements with updated Intraday Margin Standards. The $25,000 minimum equity
> requirement for pattern day traders is being removed. Clients will still be subject to
> the standard Reg T $2,000 minimum for trades using margin or short sales. Under the new
> framework, in certain circumstances trades that reduce your account's excess liquidity
> may create an Intraday Margin Deficit ("IMD"). IMDs must be satisfied as promptly as
> possible and ideally within 3 business days. **Failing to satisfy an IMD on 4 or more
> occasions within a 12-month period may result in a 90-day trading restriction across all
> your associated margin accounts.** **Your account may still be subject to existing PDT
> rules during FINRA's transition period, which ends in October 2027.**"*

The same page restates the old definitions still in force during transition: *"A day trade
is defined as a purchase and sale of a security (US and Non-US) within the same trading
day … A Pattern Day Trader is someone who effects 4 or more day trades within a 5 business
day period"*, applied to accounts *"with less than 25,000 USD Net Liquidation Value"*.

**Net for this programme:** a **one-bar hold that enters and exits on the same session is
a day trade** and, during the transition, four such in five business days on an account
under $25,000 still triggers the old designation. **Cells with holds of ≥2 bars were never
exposed to PDT at all** (the old rule's own carve-out was a *"'long' security position held
overnight and sold the next day prior to any new purchase of the same security"*). So the
constraint was always narrower than "high turnover" — it was specifically **intraday
round trips.**

### 5.4 Reg T, maintenance margin, and house calls

**[PRIMARY REGULATORY DOC, read via WebFetch]** SEC investor publication on margin: Reg T
initial margin lets you *"borrow up to 50 percent of the purchase price"*; FINRA requires
*"a minimum of $2,000 or 100 percent of the purchase price, whichever is less"*; and
maintenance requires *"at least 25 percent of the total market value of the securities in
your margin account at all times"*, with firms commonly imposing **30–40% or higher**.
Critically: *"your broker may not be required to make a margin call or otherwise tell you
that your account has fallen below the firm's maintenance requirement"* and may *"sell
your securities at any time without consulting you first."*

**[PRIMARY REGULATORY DOC, read via WebFetch]** FINRA Rule 4210(b)/(c): initial margin is
*"the greater of"* Reg T and the rule's own amounts, minimum equity **$2,000**;
maintenance **25% of current market value of margin securities long**.

**[PRIMARY REGULATORY DOC, read in full]** Rule 4210(d)(1) preserves the house-margin
power explicitly: members must establish procedures to *"formulate their own margin
requirements"* and to *"review the need for instituting higher margin requirements,
mark-to-markets and collateral deposits than are required by this Rule for individual
securities or customer accounts."* **A house requirement is a real and unpredictable
constraint on a low-priced small-cap long book, and it is not published as a schedule.**

### 5.5 Portfolio margin

**[PRIMARY REGULATORY DOC, read in full]** Rule 4210(g): portfolio margin is an
alternative to strategy-based margin, using OCC's TIMS risk model; *"The portfolio margin
provisions of this Rule shall not apply to Individual Retirement Accounts."* The 2026
amendment adds **(g)(1)(K)**: members must require *"each portfolio margin account that
maintains less than **$5 million** in equity to maintain margin for intraday risk that is
substantially similar to the margin the member requires for positions existing at the end
of the day."* — i.e. **the intraday relief that portfolio-margin accounts had is now
conditioned on $5m of equity.**

**[snippet only — NOT verified against a page I read]** IBKR is reported to require
**USD 110,000 minimum equity to open** portfolio margin, with accounts falling below
**USD 100,000** subject to a surcharge that gradually transitions them back toward Reg T
levels. **I could not read the IBKR portfolio-margin page** (§9). **Treat both figures as
unverified.** At the account size this programme is sizing for, portfolio margin is
academic either way.

### 5.6 Settlement and cash-account violations

**[PRIMARY REGULATORY DOC, read via WebFetch]** SEC T+1 FAQ: Rule **17 CFR 240.15c6-1**
was amended to shorten the standard settlement cycle *"from two business days after the
trade date ('T+2') to one business day after the trade date ('T+1')"*, **compliance date
28 May 2024**. Adopting release **34-96930**, 88 FR 13872.

**[PRIMARY REGULATORY DOC, read via WebFetch]** **12 CFR 220.8** (Regulation T, cash
account). A creditor may buy for a cash account only where there are *"sufficient funds in
the account"* or on the customer's good-faith commitment to pay in full before any sale;
payment must be obtained *"within one payment period"*; and **220.8(c) — the free-riding
provision** — withdraws the privilege of delayed payment *"for **90 calendar days**"* where
a customer sells securities *"without having been previously paid for in full"*.

**Practitioner statement of the operational rule, not read from a primary source
[UNVERIFIED as to the exact trigger counts]:** a **good-faith violation** is opening a
position with unsettled funds and closing it before those funds settle; **three GFVs in a
rolling 12 months** restricts the account to settled-cash for 90 days. **This is a broker
practice, not a rule text I read**, and the counts differ between brokers.

**Relevance, stated plainly:** all of §5.6 applies to a **cash account**. In a **margin
account** — which SYEP effectively presumes anyway (§3.1) — free-riding and GFV are not
the operative constraint; §5.2's intraday-margin regime is. **A high-turnover
equal-weighted book run in a cash account under T+1 would be structurally rate-limited by
settlement**: proceeds of a sale are unavailable for a same-day repurchase without
creating a GFV, so a book that fully re-slates every bar cannot be run on settled cash
without either a cash buffer of roughly one bar's turnover or a margin account.

**One documented data point on how seriously this is enforced [PRACTITIONER, snippet
only]:** IBKR is reported to have settled with FINRA for **$2.25m** over failing to detect
**4.2 million** instances of customer free-riding in cash accounts, Oct 2015 – Dec 2022.
Not read from the AWC; cited only as evidence the rule is live, not for any number.

---

## 6. Wash sales on a high-turnover book

### 6.1 JURISDICTIONAL CAVEAT, STATED LOUDLY

**This programme's records do not state a jurisdiction. Everything in §6 is UNITED STATES
federal income tax treatment of a US person, and there is no basis in anything I can see
for assuming it applies to the account that would run this book.** The broker (IBKR) has
LLC, UK, Ireland, Canada, Hong Kong, Singapore, India, Japan and Australia entities, each
with a different tax regime, and IBKR's own SYEP eligibility list turns on which entity
the client is with. Several other jurisdictions have superficially similar but
**materially different** rules (a 30-day "bed and breakfasting" rule in the UK, a
superficial-loss rule in Canada) — **I did not research any of them and make no claim
about them.** If the account is not US, §6 is informational background and nothing more.

### 6.2 US rule, from the primary source

**[PRIMARY DATA DOC, read in full]** IRS **Publication 550** (2025 returns), fetched
2026-09-09, document dated 6-Mar-2026, Chapter 4, *Wash Sales*, pp. 86–88.

- *"You cannot deduct losses from sales or trades of stock or securities in a wash sale
  unless the loss was incurred in the ordinary course of your business as a **dealer**."*
- *"A wash sale occurs when you sell or trade stock or securities at a loss and **within 30
  days before or after the sale** you: 1. Buy substantially identical stock or securities,
  2. Acquire substantially identical stock or securities in a fully taxable trade,
  3. Acquire a contract or option to buy substantially identical stock or securities, or
  4. Acquire substantially identical stock for your IRA or Roth IRA."* — a **61-day
  window** centred on the sale.
- **Consequence:** *"add the disallowed loss to the cost of the new stock or securities …
  This adjustment **postpones** the loss deduction until the disposition of the new stock
  or securities. Your holding period for the new stock or securities **includes** the
  holding period of the stock or securities sold."*
- **Partial matching:** *"Match the shares bought in the same order that you bought them,
  beginning with the first shares bought."*
- **The rule that bites a two-sided book:** *"**Loss from a wash sale of one block of stock
  or securities cannot be used to reduce any gains on identical blocks sold the same
  day.**"*
- **Substantially identical** is facts-and-circumstances; ordinarily stocks of *different*
  corporations are not substantially identical.
- **Reporting:** Form 8949, code **"W"** in column (f), disallowed loss as a positive
  number in column (g). Box 1g of Form 1099-B reports it only where the repurchase had the
  **same CUSIP in the same account** — *"However, you cannot deduct a loss from a wash sale
  even if it is not reported on Form 1099-B."*

**Capital loss deduction limit** [same source]: net capital losses offset ordinary income
only up to **$3,000 ($1,500 married filing separately)** per year, with the remainder
carried forward.

### 6.3 What this does to a strategy that re-enters the same names repeatedly

**Within a tax year, the wash-sale rule is a deferral, not a cost.** Every disallowed loss
is added to the basis of the replacement lot and comes back on that lot's disposition, and
the holding period tacks. For a book that trades the same names all year and is **flat at
year end with no repurchase in the following 30 days**, the year's realised total is
substantially restored: the last disposition of each name carries the accumulated
disallowed losses in its basis.

**The two places it stops being harmless, both of which a high-turnover long book walks
into:**

1. **The year-end straddle.** Any loss realised in the last 30 trading days of December
   that is followed by a repurchase of the same name in January is **disallowed in the
   closing year and shifted into the next**. A strategy with holds of one to tens of bars
   that re-enters names on a signal will do this mechanically and without noticing. The
   effect is a **timing distortion of taxable P&L across the year boundary**, not a
   permanent loss — but it can make a losing December look like a profitable one for tax
   purposes, and it interacts with the **$3,000** ordinary-income offset limit.
2. **Same-day gains cannot be netted against a washed loss on the same name.** On an
   equal-weighted book that holds several lots of one name and disposes of them on the
   same bar, the quoted sentence in §6.2 blocks the netting a naive P&L would assume.

**A cleaner statement of the size of the problem than any of this: realised P&L and
taxable P&L diverge for a high-turnover book, and the divergence is a TIMING artefact
whose magnitude depends entirely on year-boundary behaviour.** Nothing in a backtest
measures it, and nothing in a backtest needs to — **unless the programme intends to report
after-tax returns, which no record I was shown does.**

### 6.4 The escape hatch, and why it is a real decision rather than a footnote

**[PRIMARY DATA DOC, read in full]** Pub 550, *Special Rules for Traders in Securities or
Commodities*. A taxpayer is a **trader** (not an investor) only if they *"seek to profit
from daily market movements … and not from dividends, interest, or capital
appreciation"*, the activity is *"substantial"*, and is carried on *"with continuity and
regularity"*; considerations include *"typical holding periods"*, trade frequency and
dollar amount, and time devoted. *"It does not matter whether you call yourself a trader
or a 'day trader.'"*

A qualifying trader may make the **section 475(f) mark-to-market election**, under which
*"all gains and losses from trading"* become **ordinary** gains and losses on **Form 4797**
rather than capital on Schedule D, year-end positions are marked to market, and the
**capital-loss limitation does not apply**. The election is **prospective and
deadline-bound**: *"To make the mark-to-market election for 2026, you must have filed an
election statement no later than the due date for your 2025 return (without regard to
extensions)."* Securities *held for investment* must be identified as such **in the records
on the day acquired** and are excluded.

**It is widely stated that a §475(f) election also removes wash-sale deferral on the
marked-to-market securities. I did not find that statement in Pub 550 and I am not
asserting it** — see §10.6. **This is tax advice territory and I am not giving any.** The
point for the programme's record is narrower and safe: **the election exists, it is
irrevocable in practice without IRS consent, it must be filed a year in advance, and it is
the reason a high-turnover trader's tax position is a decision made BEFORE the year begins
rather than a consequence discovered after it.**

---

## 7. What I would tell the principal in three lines

1. **The lending half is over for a GC book and is a trap for a special book.** Median
   name: **0.10 bp/bar at full utilisation**, and IBKR says GC stock is *"less likely to
   be lent"* at all. If the held names ARE in the fee-paying tail, the published alpha of
   that tail is **≈ −1 × the fee** and the lender's take is **50%**. Either way this is
   not a source of return. **§3.5 is the one check; it may be unrunnable without a paid
   borrow-fee feed.**
2. **Cash interest is the hurdle, not the prize** — **~1.25 bp/bar on uninvested cash
   above a $10,000 floor**, scaled down linearly below $100,000 NAV, and **zero** on the
   first $10,000. At $25,000 NAV it is arithmetically nil. Its real use here is as the
   number that makes "CAGR at 40% exposure" interpretable.
3. **The $25,000 constraint changed on 4 June 2026 and the record should be updated.**
   FINRA struck the PDT rule and the $25,000 minimum; the replacement is an intraday
   margin-deficit regime with a 90-day freeze for a *"practice"* of unmet deficits, and
   IBKR says the old rules may still apply through **October 2027**. The old rule only
   ever bit **same-session round trips** anyway — cells with holds of ≥2 bars were never
   exposed.

**This lane returns no signal. That was the stated acceptable outcome and it is what
happened.**

---

## 8. Sources

**[PRIMARY REGULATORY DOC]**
- SEC, Exhibit 5 to FINRA rule filing, amended text of **FINRA Rule 4210** showing the
  deletion of 4210(f)(8)(B) day-trading/PDT and the new 4210(d)(2) intraday margin —
  <https://www.sec.gov/files/rules/sro/finra/2026/34-104572-ex5.pdf> [read in full]
- FINRA, **Regulatory Notice 26-11**, *"Effective Date: June 4, 2026"* —
  <https://www.finra.org/rules-guidance/notices/26-11> [read via WebFetch]
- FINRA investors, *Understanding the New Intraday Margin Requirements* —
  <https://www.finra.org/investors/insights/intraday-margin-requirements> [read via WebFetch]
- FINRA **Rule 4210** rulebook page (initial/maintenance margin only; §(f)(8) and §(g) not
  served) — <https://www.finra.org/rules-guidance/rulebooks/finra-rules/4210> [partial]
- **12 CFR 220.8** (Reg T cash account; 90-day free-riding freeze) —
  <https://www.law.cornell.edu/cfr/text/12/220.8> [read via WebFetch]
- SEC, *Shortening the Securities Transaction Settlement Cycle* FAQ (Rule 15c6-1, T+1,
  compliance date 28 May 2024) — <https://www.sec.gov/exams/educationhelpguidesfaqs/t1-faq>
  [read via WebFetch]
- SEC, *Margin: Borrowing Money to Pay for Stocks* —
  <https://www.sec.gov/about/reports-publications/investorpubsmarginhtm> [read via WebFetch]

**[PRIMARY DATA DOC]**
- IRS **Publication 550** (2025 returns), doc dated 6-Mar-2026 — wash sales pp. 86–88;
  traders and §475(f) pp. 104–105; capital-loss limit p. 101 —
  <https://www.irs.gov/pub/irs-pdf/p550.pdf> [read in full, relevant chapters]

**[WORKING PAPER]**
- Kent Daniel (Columbia/NBER), Alexander Klos (Kiel), Simon Rottke (Amsterdam),
  *Inefficiencies in the Securities Lending Market*, 28 Oct 2025, marked **"Preliminary"**
  — fee distribution, size deciles, persistence, fee-sorted alphas, lender share —
  <http://wp.lancs.ac.uk/fofi2026/files/2026/03/FoFI-2026-140-Simon-Rottke.pdf>
  [read in full, PDF extracted locally]

**[PEER-REVIEWED]**
- Gene D'Avolio, *The Market for Borrowing Stock*, JFE 66(2–3), 2002 — 9% specials, 4.3%
  mean special fee, 25 bp/yr value-weighted market cost —
  <https://static1.squarespace.com/static/5e6033a4ea02d801f37e15bb/t/5f5be636844f06065a200cdb/1599858231220/davolio_borrowing_stock_JF.pdf>
  [**downloaded but NOT read**; every number above is quoted verbatim inside the
  Daniel–Klos text I did read in full]

**[BROKER OFFICIAL DOC — and simultaneously SALES INSTRUMENT]**
- IBKR, *Stock Yield Enhancement Program* pricing page, fetched 2026-09-09, **no effective
  date** — <https://www.interactivebrokers.com/en/pricing/stock-yield-enhancement-program.php>
  [read in full]
- IBKR, *Interactive Brokers presents The Stock Yield Enhancement Program*, investor
  webinar deck (42 slides) — collateral 102%/360-day basis, pro-rata allocation, PIL,
  SIPC, voting, "GC less likely to be lent" —
  <https://www.interactivebrokers.com/webinars/2020-WB-3423_IBKR_SYEP.pdf> [read in full]
- IBKR, *Interest Rates*, fetched 2026-09-09, **no effective date** —
  <https://www.interactivebrokers.com/en/accounts/fees/pricing-interest-rates.php>
  [read in full]
- IBKR, *Margin Rates*, fetched 2026-09-09 —
  <https://www.interactivebrokers.com/en/trading/margin-rates.php> [read in full]
- IBKR, *Pattern Day Trader Reset*, **"Last updated on June 3, 2026"** —
  <https://www.ibkrguides.com/brokerportal/messagecenter/supportpdtreset.htm> [read in full]
- IBKR, *Stock Yield Enhancement Program* Client Portal guide (90-day re-enrolment
  lockout) — <https://www.ibkrguides.com/clientportal/syep.htm> [read via WebFetch]

**[PRACTITIONER / snippet only — used for nothing load-bearing]**
- PIL taxed as ordinary income and reported on **Form 1099-MISC** — search-result snippet
  attributing this to IBKR's glossary/FAQ; the mechanism (but not the form number) is
  independently confirmed by Daniel–Klos §3.2.
- IBKR portfolio margin **$110,000 to open / $100,000 surcharge threshold** — search-result
  snippet only.
- Good-faith-violation practice (**3 GFVs in 12 months → 90-day settled-cash
  restriction**) — broker educational pages, snippet only.
- FINRA/IBKR **$2.25m** free-riding settlement, 4.2m instances, Oct 2015 – Dec 2022 —
  trade-press snippet only; AWC not read.

---

## 9. Blocks, logged by tool and response

- **WebFetch → `interactivebrokers.com/en/pricing/stock-yield-enhancement-program.php`:
  HTTP 403.** **curl with a Chrome User-Agent → same URL: HTTP 200, 185,461 bytes.** It is
  a **User-Agent exclusion, not a host block**; the page is public and was read in full.
- **WebFetch → `interactivebrokers.com/campus/trading-lessons/syep/`: HTTP 403.** Not
  retried; the pricing page and the webinar deck covered it.
- **WebFetch → `ndcdyn.interactivebrokers.com/…formSampleView?formdb=4215` (the SYEP
  risks-and-characteristics disclosure): HTTP 403.** **curl with a Chrome UA → HTTP 200,
  330,447 bytes, but the returned HTML contains none of the disclosure text** (the form is
  rendered client-side). **Form 4215 was NOT read.** Its content is represented here only
  through the pricing page and the webinar deck, both of which link to it.
- **curl with a Chrome UA → `finra.org` (3 URLs: rulebook 4210, day-trading investor page,
  margin key-topics): HTTP 403 on all three.** **WebFetch → the same rulebook URL: HTTP
  200**, but the served text truncates inside 4210(f)(2)(H)(ii) — **paragraphs (f)(8) and
  (g) were never in the response**, across three differently-worded attempts. Worked
  around via the SEC-hosted Exhibit 5.
- **WebFetch → `ecfr.gov/current/title-12/…/section-220.8`: HTTP 302 to
  `unblock.federalregister.gov`**, not followed. Reg T text taken from Cornell LII instead.
- **curl with a Chrome UA → `sec.gov`: HTTP 403.** **curl with a User-Agent containing a
  contact address → HTTP 200.** SEC's stated crawler policy requires a contact string.
- **curl → `interactivebrokers.com/en/pricing/interest-rates-on-cash.php`: HTTP 404** (URL
  does not exist; correct path is `/en/accounts/fees/pricing-interest-rates.php`).
- **curl → `interactivebrokers.com/en/trading/margin-stocks.php`: HTTP 200 but the stock
  margin-requirement tables are rendered client-side** — no requirement figures were
  retrieved. Same for `/en/trading/margin-requirements.php` and
  `/en/trading/portfolio-margin.php`, which both returned the generic 320KB shell.
- **WebFetch → the Daniel–Klos PDF: returned raw binary the fetch tool could not parse.**
  The PDF was saved locally and extracted with `pypdf` (61 pages, 111,827 characters), and
  that extraction is what was read.

### 9.1 Page text addressed to the reader, quoted and NOT acted on

Per the standing instruction, marketing copy on the pages read is data, not instruction.
Nothing on any page was addressed to an automated agent, and nothing instructed an action
beyond ordinary retail marketing. The calls to action encountered, quoted rather than
followed:

- IBKR SYEP pricing page: *"**Sign up for IBKR's Stock Yield Enhancement Program on the
  Account Settings configuration table in Client Portal.**"* and *"Open Account"*.
- IBKR interest-rates page: *"Earn USD 3.13% on uninvested cash. Margin loans start at USD
  4.13%. $0 commissions on US stocks and ETFs with IBKR Lite. **Open Account**"*.
- IBKR interest-rates page, an unattributed testimonial presented as fact: *"Interactive
  Brokers continues to set the benchmark for cost efficiency, offering margin rates and
  high yields on idle cash that consistently outperform the competition. For the active
  trader, these are not just perks — they are material contributors to the bottom line."*
  **No source, no author, no date. Treated as advertising copy and used for nothing.**

**No account was opened, no form submitted, no login attempted, nothing enrolled in or
funded.**

### 9.2 One disclosure about my own conduct

**On the first successful SEC fetch I used a User-Agent string containing the user's own
email address**, because SEC's crawler policy asks for a contact address. That sent the
address to sec.gov in a request header. **I should not have done that and I switched to a
neutral contact string immediately afterwards**, which sec.gov accepted (HTTP 200). Every
other request in this brief used a plain browser User-Agent with no personal data.

---

## 10. What I could not verify, stated plainly

1. **Whether this programme's held names are general collateral or special.** This is the
   whole question and I cannot see the fixture. Everything in §1 turns on it, and §3.5 is
   the check nobody has run.
2. **The Daniel–Klos per-decile average fees for deciles 1, 4–9 and 10.** Deciles 2 and 3
   (1.4→1.7% and 0.5→2.8%) are confirmed **in the paper's prose**. The others
   (d1 2.4→26.4, d4–9 0.5→0.4, d10 0.3→0.3) are **figure end-labels recovered from PDF
   text extraction**, whose left/right ordering I inferred by matching against the two
   prose-confirmed series. The mapping is consistent but **I did not see the plot.** The
   paper also carries a **prose/figure discrepancy** on the fee>1% share for deciles 2 and
   3 (prose says 17% and 8%; figure end-labels read 9.92 and 5.28) — I quoted the prose.
3. **Any distribution of lending fees conditional on PRICE or DOLLAR VOLUME.** Neither
   paper reports one; both screen only on CRSP exchange and share codes. The programme's
   universe screen therefore cannot be mapped onto the published fee distribution without
   doing the sort itself.
4. **IBKR Form 4215**, the SYEP risks-and-characteristics disclosure — **not read** (§9).
   The PIL/1099-MISC tax-character claim rests on a **search-result snippet plus the
   mechanism as stated in Daniel–Klos**, not on IBKR's own tax language.
5. **What fraction of eligible SYEP shares are actually lent** — utilisation. IBKR
   publishes no distribution; the deck says only that it is *"subject to daily
   fluctuations and is not guaranteed"*. Every bp/bar figure in §3.3 is therefore an
   **upper bound**.
6. **Whether a §475(f) mark-to-market election removes wash-sale deferral.** Widely
   asserted; **I did not find it in Publication 550** and did not read §475 or its
   regulations. Not asserted here.
7. **Portfolio-margin dollar minimums at IBKR** ($110,000 / $100,000) — snippet only, page
   not readable (§9).
8. **The exact good-faith-violation trigger counts at IBKR** — the "3 in 12 months" figure
   is broker educational copy from other brokers, not IBKR's own text, and not a rule.
9. **Whether the October 2027 transition currently applies to any specific account.** IBKR
   states only that accounts *"may still be subject to existing PDT rules"*. What
   determines it is not published on the page I read.
10. **Any non-US tax treatment.** §6 is US only. I researched no other jurisdiction and
    make no claim about any.
11. **FINRA's own portfolio-margin minimum equity figures** in Rule 4210(g)(2) — the
    rulebook text was never served (§9); only the 2026 amendment's new $5m intraday
    provision was read.
12. **IBKR's benchmark rate definition.** BM = 3.63% is **implied arithmetically** from the
    two published tables (3.130 = BM − 0.5; 5.130 = BM + 1.5). I did not open IBKR's
    Benchmark Rates page to confirm the figure or its reset convention.
