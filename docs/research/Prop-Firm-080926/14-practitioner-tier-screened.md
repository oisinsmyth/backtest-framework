# 14 — The practitioner tier, screened

**Lane 14 of the Prop-Firm-080926 review.** Opened and closed 2026-09-08.
Schema and stopping rules: [`00-SCHEMA.md`](00-SCHEMA.md). Reads on
[`07-statistics-and-claims.md`](07-statistics-and-claims.md). Filed toward **D386**.

**Stopping rule that bound: the HARD CAP OF 25 SOURCES.** Saturation was reached separately, and
earlier, on one sub-question — *"what do people who pass evaluations actually run?"* — where four
independent search framings and three fetches returned marketing with zero mechanism. The cap is what
formally bound; that sub-question was already dead before it did.

**NOTHING HERE IS EVIDENCE.** Everything below is a hypothesis with a falsification criterion. No
strategy is recommended, no avenue is opened or closed, and no look is added to any multiplicity
ledger.

---

## VERDICT

**One candidate family survives, conditionally, and the condition is the one that matters. Nine are
rejected. Zero survive cleanly.**

| | count |
|---|---|
| families surviving all seven screen items | **0** |
| surviving 1,2,3,6,7 and **unresolved** on 4 and 5 | **1** — intraday momentum on ES/NQ |
| rejected on evidence (family is real, the record does not hold) | **1** — opening-range breakout |
| rejected on **structure** (cannot fit the barrier by construction) | **7** |
| rejected on the anti-screen alone | **1** — DOM/tick scalping as marketed |

### The finding this lane was built to produce

**The rule set selects for a P&L shape that does not exist.**

The two binding rules cut from opposite sides and the survivors' band between them is narrow:

- The **~4% trailing floor on OPEN equity** kills **negative skew.** Any book that pays small and
  often while occasionally holding a large adverse excursion is marked at the worst point of that
  excursion, before the trade resolves. Mean reversion, fading extremes, DCA, grid and martingale all
  die here — not on expectancy, on marking convention.
- The **consistency rule** kills **positive skew.** Topstep's is quoted verbatim by a practitioner who
  hit it: *"your best trading day can't be better than 50% of your total"* — he exceeded the $9,000
  target on a $150,000 account by $123, over 11 days at a 64% win rate, and was handed an *additional*
  $2,205 requirement because his best two days were 49.7% of the total. A book whose right tail does
  the work is penalised exactly where it earns.

What is left is **near-symmetric, low-variance daily P&L** — which is precisely the shape that a
**$10 round turn** destroys, because low variance per trade means low gross per trade and the cost is
a fixed dollar subtraction. The three constraints are not three hurdles in series; they are a vice.

### The scale-free number, and it is the strongest thing in this lane

Comparing a prop account to a managed-futures programme on *return* is invalid — $50k is a **risk
budget**, not AUM. So compare the one ratio that is unit-free on both sides: **P&L per unit of
drawdown budget, per day.**

| | daily P&L required or delivered | drawdown budget | ratio/day |
|---|---|---|---|
| **$50k prop account, this screen** | **$150** | **$2,000** (4% trailing) | **0.075** |
| **NilssonHedge Systematic Short-Term CTA index** — the most-verified intraday/short-hold CME tier there is | ~6.3%/yr (VAMI 125.34, Jan-2023 → Sep-2026) | 10–30% typical programme; take 20% | **0.00125** |
| **a good individual programme**, Calmar 1.0 (generous) | — | — | **0.004** |

**The prop account demands 19× to 60× the daily return-per-unit-of-drawdown that the audited
short-term futures tier delivers.** The 19× figure already assumes a Calmar of 1.0, which is better
than the index by 3×. This survives every reasonable re-parameterisation of the inputs.

**Falsifier, stated so it can kill this:** produce one audited or broker-verified intraday CME futures
programme with **annualised return ÷ maximum drawdown ≥ 18**. If one exists, the paragraph above is
wrong. None was found in this lane; IASG's own framing is that *"returns targeted in the 20% range
with 10% drawdowns are often ideal"* (Calmar 2.0) and that *"a 30% drawdown will end most programs."*

### The base rate nobody in this tier states

Barber, Lee, Liu & Odean, on the Taiwan population (3.7 billion transactions, 1992–2006): about
**5%** of active day traders were persistently profitable; the average day trader lost **7 bp/day
gross and 23.9 bp/day net** — *transaction costs more than tripled the gross loss* — and aggregate
performance was reliably negative in **14 of 15 years**. Survival at 1/2/3 years: 44% / 24% / 15%.

This is the null for the entire practitioner tier, it is peer-reviewed, it is on **futures** in the
companion paper, and **not one commercial page in this lane cited it or anything like it.** It is also
mechanically consistent with lane 07's central result — Topstep's observed 16.8% per-attempt pass rate
sitting *below* D379's 26.5% zero-edge trailing baseline.

### What kills funded accounts in practice — the honest answer is that no one knows

**No methodology-disclosed breach post-mortem dataset exists.** This lane looked for one specifically
and did not find it. What exists:

- The widely-cited **"~70% of failures come from loss limits, not missed profit targets"** is
  circular. hoc-trade's own page attributes its 71% to *"a widely cited industry breakdown"* with no
  upstream source, no sample period and no date range, on a page selling a behavioural-analytics
  product (TradeMedic™ AI). Lane 07 already logged it as **WEAK**; this lane traced it to its claimed
  origin and it does not resolve to data.
- hoc-trade's **behavioural** breakdown does at least name mechanisms with prevalence figures:
  *"fail to call it a day"* 75.6% of traders, *overtrading* 49.5% (~25% of losses), *revenge trading*
  37.1% (~12%), *doubling down* (~20% of losses, 5.3% profit rate when it is the top issue),
  *refusing to cut losses / widening stops*. **Three of these five are risk-shifting**, which is what
  our own records predict near a barrier — but the source cannot carry the claim, so this is a
  hypothesis, not a confirmation.
- Notably **absent** from every source found: oversizing, news events, and slow bleed as *measured*
  categories. The one thing the tier agrees on is that the fatal event is a **rule breach on open
  equity**, not a strategy that stopped working.

**Falsifier / what would settle it:** a firm-published breach-cause breakdown with a stated
denominator and date range. Field 23 in the schema is already `NOT PUBLISHED` for four of five firms;
breach causes are not published by any of the five.

---

## THE SURVIVOR (one, conditional)

### S1 — Intraday momentum on ES/NQ, exited at the cash close

**Mechanism, stated and peer-reviewed.** Gao, Han, Li & Zhou, *Market Intraday Momentum*, JFE 2018
(SPY high-frequency data 1993–2013): the first half-hour return predicts the last half-hour return;
predictability is significant **out of sample**, stronger on high-volatility, high-volume, recession
and macro-release days, and present in ten other actively traded ETFs. Two mechanisms are offered —
Bogousslavsky (2016) **infrequent portfolio rebalancing**, and **late-informed traders** acting near
the close. This is a stated mechanism, not an indicator combination.

**Futures implementation with a stated cost convention.** Zarattini, Barbon & Aziz, *Beat the Market*
(SSRN 4824172): SPY 2007–early 2024, +1,985% total, **19.6% annualised, Sharpe 1.33, net of costs**.
The ES/NQ port (Quantitativo, Databento minute data since 2010) states costs explicitly —
**"$0.85/contract in commissions + $1.40/contract in fees (per transaction)" plus "0.25 tick in
slippage in every transaction"**, i.e. ~$4.50 per round turn — and reports:

| | ES | NQ |
|---|---|---|
| annualised | 16.8% | 24.3% |
| Sharpe | 1.25 | 1.67 |
| max drawdown | **21%** | **24%** |
| win rate | n/s | 38% |
| payoff | n/s | 2.25 |
| E[return]/trade | +2 bp | +6 bp |

Positions are *"closed either at the market close or when the price reverses back into the Noise
Area."* A control is run and the signal/non-signal distributions differ at *"P-value well below
0.05."*

**How it fares on each screen item:**

| # | screen | verdict |
|---|---|---|
| 1 | CME futures tradeable | **PASS** — ES/MES, NQ/MNQ |
| 2 | directional, not hedged | **PASS** — single outright leg, no offsetting instrument. No hedging-clause exposure |
| 3 | intraday-closable | **PASS** — flat at the cash close **by construction**, not by convention |
| 4 | MAE-bounded | **UNRESOLVED — this is the condition.** Per-*trade* MAE is bounded by the Noise-Area stop, which is the good news. But the published 21%/24% drawdown is a percentage of a notional-scaled equity curve; **the dollar drawdown per single contract is not published anywhere**, and that is the only number the barrier reads |
| 5 | $150+/day on $50k | **UNRESOLVED, and in tension with 4** — see the arithmetic below |
| 6 | survives $10/RT | **PASS, comfortably.** At ES = P index points, notional = $50P; +2 bp ≈ $0.10P per contract per trade — ~$65 at P = 6,500. A $10 round turn is **~15% of gross**. NQ at +6 bp is far safer. Note the sector's own quoted retail rate is ~$4.00–4.50/RT, so the $10 in this screen is ~2.2× conservative |
| 7 | stated mechanism | **PASS** — two, both published, one peer-reviewed in JFE |

**The arithmetic that decides items 4 and 5, and why it is tight.**

At one trade per day and ~$65 net per ES contract per trade, expecting **$150/day requires ~2.3 ES
contracts** (~$750k notional). The Noise-Area stop is a volatility band typically on the order of
0.3–0.6% of price; at 0.4% of $325,000 that is **~$1,300 of risk per contract**, so ~**$3,000 of
per-trade risk at the size required** — against a **$2,000** total drawdown buffer that is marked on
*open* equity and **ratchets up but never down**.

> **At the size required to expect $150/day, the family's own per-trade stop is ~1.5× the entire
> drawdown budget.** Micros do not help: MES scales P&L and risk by the same 1/10.

**Falsification criterion, in our own quantities.** Run the ES intraday-momentum rule on 2010–2026
minute bars and compute, per single contract, the **realised distribution of intraday MAE in dollars**
and the **trades per day**. Let `k` = contracts needed for `E[daily P&L] ≥ $150` after a $10 round
turn. Then simulate `k` contracts against a **ratcheting floor on open equity** (D259's machinery),
initialised at $2,000 below the starting balance. **S1 survives iff the probability of touching the
floor over a 20-day evaluation is materially below D379's 26.5% zero-edge trailing baseline.** If it
is not, S1 is dead on hurdle P — and per the schema's standing instruction it goes to
`09-personal-book-carry-forward.md` rather than being discarded, because on the personal book there is
no barrier and a Sharpe-1.25 intraday-only book with a stated mechanism is worth an R15 test.

**What would make S1 a false positive.** (a) The +2 bp figure is a single vendor's implementation of
another party's published rule — no independent replication of the *futures* version was found.
(b) The SPY paper's sample (2007–2024) overlaps the JFE discovery sample (1993–2013) only partly, but
Concretum is a commercial research shop and the paper is its own follow-on. (c) Nothing here has been
run against a null on our own fixture.

---

## THE REJECTED LIST

Structural rejections are the durable output; evidence rejections could in principle reverse.

### Rejected on STRUCTURE — cannot fit the barrier by construction

| family | screen item failed | why, precisely |
|---|---|---|
| **R1 — mean reversion / fading intraday extremes** | **4** | Negative skew by construction: many small wins, occasional large adverse excursion. The floor marks **open equity including unrealised P&L**, so the position is marked at the worst point of the excursion *before* it resolves. MFFU states it verbatim: *"if your equity, including open trades, falls below the most recently adjusted drawdown limit, your account will breach."* Expectancy is irrelevant to this failure |
| **R2 — DCA / averaging down / grid / martingale** | **4** | R1's failure, amplified. Position size rises exactly as MAE rises. Also the hoc-trade behavioural list's *"doubling down"* — a 5.3% profit rate when it is the trader's top issue |
| **R3 — spread trading: calendar, inter-market, pairs, cash-futures basis** | **2 — terminal** | Directly prohibited. Topstep names *"coordinated trading"* (pooling risk or hedging positions) and *"cross-account hedging (single-user)"* as prohibited conduct. The industry reading is blunter: *"every personal account must trade the same direction, and hedging correlated instruments is prohibited… a hedging clause that one partial fill can break."* This kills an otherwise entirely legitimate CME family — the classic curve/spread trades — on rule, not on merit. **Carry-forward candidate for the personal book** |
| **R4 — overnight, gap, carry, roll-yield, term-structure** | **3, and 4** | Fails intraday-closable outright. Worse, the trailing floor marks open equity *through* the overnight session, when the position cannot be managed |
| **R5 — volatility selling / options structures** | **1, and 4** | These are futures-only firms; options on futures are not in scope on the platforms surveyed. And unbounded MAE against a $2,000 buffer |
| **R6 — news / event-release trading** | **4** | The stop is not honoured through a release; realised slippage on a macro print is unbounded relative to a $2,000 buffer. Rule status is also firm-dependent (Topstep permits with standard risk rules; Apex has historically restricted around events), so it is not portable across the grid |
| **R7 — any book whose right tail does the work** (a small number of large winning days) | the **consistency rule**, which the seven-item screen does not even contain | Best day capped at 50% of total profits. The one practitioner post found who documented hitting it cleared the target and was still refused: *"The consistency rule is punishing excellence rather than preventing gambling."* **This is the screen item our own list was missing**, and it is the mirror image of item 4 |
| **R8 — systematic short-term / intraday trend-following (the CTA family)** | **4** | This is the *only* family in the whole survey with third-party-verified records, and it is disqualified by the very fact that makes it verifiable: it runs 10–30% drawdowns, **2.5×–7.5× the 4% barrier**, at ~6.3%/yr. See the scale-free table above. **Carry-forward candidate for the personal book** — its problem is the instrument, not the strategy |

### Rejected on EVIDENCE

| family | why |
|---|---|
| **R9 — opening-range breakout (ORB)** | The family has a real literature (Zarattini & Aziz 2023, SSRN 4416622) *and* an independent replication with a placebo control and bootstrap CIs — and the replication is a **negative**. Jan 2016 → Feb 2023, 1,775 trades (paper: 1,795). Gross edge **$0.070/share**; **"net PnL crosses zero at ~2.2¢/share"** of slippage, i.e. the edge lives inside a ~1¢ spread. The NQ-confirmation variant reaches t = 2.05, but **"76% of the filtered PnL is 2022 alone"** — a single high-volatility regime — and portfolio Sharpe 0.77 vs buy-and-hold 0.72 with overlapping CIs. Screen item 7 passes; items 5 and 6 fail on the family's own numbers. **This replication is the single best-constructed source in the lane and it kills the strategy it replicates.** |
| **R10 — DOM / tape / 2–4 tick scalping, as marketed** | Fails the anti-screen on four counts simultaneously; see the specimen below. On the arithmetic alone: at the screen's **$10** round turn, a 3-tick ES win ($37.50) surrenders **27% of gross**, and a 2-tick win ($25.00) surrenders **40%**. No verified track record for any version of this was located anywhere in the survey |

---

## ANTI-SCREEN SPECIMENS

Logged per instruction. Lane 07's twelve tells are the reference; **one new tell** is added.

**Specimen 1 — TradeAlgo, "ES Futures Scalping: A Professional's Guide."** Hits four anti-screen
triggers in one page:

- *win rate quoted with no payoff ratio* — **"a consistent 60%+ win rate"** with "3-4 tick average
  winners" and **no stated stop**, so the payoff ratio is unstated and unrecoverable;
- *equity/profit claim with no sample period* — **"$500-$2,000 per day in gross profits"**,
  **"net monthly returns typically range from $5,000-$15,000"**, with no backtest, no sample period,
  no track record, no null;
- *attached to a paid service* — **"upgrade to Premium starting at $149/year"**, plus its "Dark Market
  Activity (DMA) tracking" and "TradeGPT" products;
- and it introduces a tell not on lane 07's list.

> **NEW TELL 13 — internal arithmetic that does not reproduce from the page's own stated inputs.**
> The page states **"$4.00 round-trip per ES contract"** and calls this **"32% of a 2-tick scalp"** and
> **"10.7% of a 3-tick scalp."** The ES tick is $12.50. The 3-tick figure checks out exactly:
> 4.00 ÷ 37.50 = **10.67%** ✓. The 2-tick figure does not: 4.00 ÷ 25.00 = **16.0%**, not 32%. It is
> **exactly 2× too large**, from the same sentence, using the same commission input. One of the two
> numbers was not computed. This is cheaper to check than any of lane 07's twelve tells and it is
> decisive: a page that cannot divide by its own stated commission has not measured anything.

**Specimen 2 — hoc-trade.** N of 500,000+ asserted; **no sample period, no collection dates, no
methodology**; the load-bearing 71% attributed to *"a widely cited industry breakdown"*; sells
TradeMedic™ AI throughout. Lane 07's tells #1 (rate with no denominator) and #10 (the statistic and
the sales instrument on the same page).

**Specimen 3 — the firm-published trader-interview tier is empty.** Fetched Topstep's own
"funded trader mindset" piece expecting field-level detail on what funded traders run. It contains
**no instrument, no setup, no holding time, no stop rule, no trade frequency** — the only concrete
trading detail in the entire article is that Dr. Steenbarger switched *"from one-minute bars to
15-second charts,"* offered explicitly as a personal adaptation. The only quantitative content is the
payout split. **This tier was the lane's best hope for the "what do winners actually run" question and
it yields nothing.** Three attempts, zero mechanism — that is the saturation signal noted at the top.

**Specimen 4 — Collective2, which disqualifies itself honestly.** Several intraday ES/NQ strategies
are listed with real AutoTrader fills, but the platform states plainly that **track records "must
still be considered hypothetical"** because no single real brokerage account matches a Model Account,
AutoTraders start and stop at will, and they apply their own stops and targets. This is better
disclosure than anything in the commercial tier — and it is exactly why the records cannot be used.

**Specimen 5 — Striker Securities, the near-miss.** The one venue found that reports **actual client
fills**: *"based on actual trades with commissions, monthly vendor fees, and exchange/nfa fees
included."* Rankings are published (top past-year net: Edvardus Breakout Gold $76,149.64; Abacus
Upside RTY $21,999.00; Abacus Advance $33,047.68). **But no drawdown, no trade count, no average
trade, no MAE, and no per-system holding convention is public** — the detail sits behind a client
login — and the published P&L is *"a compilation of several accounts over time,"* not one account.
So the tier that has the right evidentiary property does not publish the two fields (screen items 4
and 5) that the barrier actually reads. Recorded as the highest-value **blocked** avenue in this lane.

**On-page directives observed and NOT acted on**, per the safety brief: TradeAlgo's
"upgrade to Premium starting at $149/year"; hoc-trade's "connect your accounts" CTA; Topstep's
sign-up CTAs; Striker's "contact us / client section" prompts. None was an instruction addressed to
an automated agent — all were ordinary commercial solicitation. **Nothing was signed up for, no
account created, no Discord joined, no affiliate or referral link followed, no data entered.**

---

## What lane 14 hands forward

1. **A seventh screen item is missing from the brief.** The seven-item screen has no **consistency-rule**
   test. R7 shows it is not redundant with item 4: item 4 excludes negative skew, the consistency rule
   excludes positive skew, and a candidate can pass item 4 and still be unpayable. **Recommend adding
   it before this screen is reused.**
2. **The scale-free ratio (0.075/day of drawdown budget, vs 0.00125–0.004 for the verified tier) is
   the number to carry into D379 §4.** It is unit-free, so it sidesteps the risk-budget-vs-AUM
   confusion that makes every return comparison in this sector meaningless, and it is 19–60× with a
   stated falsifier.
3. **Two carry-forwards to `09-personal-book-carry-forward.md`**, prop-ineligible but not
   personal-book-ineligible: **R3 (spread/curve trading)**, killed purely by a hedging *rule*; and
   **R8 (short-term systematic trend)**, killed purely by a drawdown *budget*. Both still owe R15 and
   a pre-registration; being carried forward is not admission.
4. **S1's falsification criterion is computable on machinery this repo already has** (D259's
   ratcheting floor, D379's zero-edge baseline). It needs ES minute bars and the Noise-Area rule; it
   is the only thing in this lane that could be settled rather than argued.
5. **The "what do people who pass actually run" question is UNANSWERABLE from public sources.** Not
   under-researched here — structurally unavailable. Firms publish payout *dollars* and testimonials,
   never strategy attribution; aggregators rank firms, not traders; the one venue with real fills
   (Striker) withholds the risk fields. Record this as a **`NOT PUBLISHED`**, not as a gap in this
   lane's effort.

---

## Sources

**25 sources — the cap, which is the rule that bound.** Tier per schema §4: primary (firm T&Cs,
rules pages) / secondary (press, peer-reviewed literature, independent replications) / claims
(marketing, vendor content, forums). **Fetched** = full page retrieved; **search-surface** = content
recovered via search index only, not independently fetched. Negative results are mandatory entries.

| # | URL | accessed | tier | sought | yielded |
|---|---|---|---|---|---|
| 1 | https://www.quantitativo.com/p/intraday-momentum-for-es-and-nq | 2026-09-08 | secondary (fetched) | an ES/NQ implementation with a stated cost convention | **THE LANE'S CENTRAL ARTEFACT.** ES 16.8%/Sharpe 1.25/maxDD 21%/+2bp per trade; NQ 24.3%/1.67/24%/38% win/2.25 payoff/+6bp. Costs stated: $0.85 commission + $1.40 fees per contract per transaction, 0.25 tick slippage. Databento minute data since 2010. Flat at the close. Control run, "P-value well below 0.05" |
| 2 | https://github.com/giovannibrusco/zarattini-2023-orb-qqq | 2026-09-08 | secondary (fetched) | an independent replication of ORB | **BEST-CONSTRUCTED SOURCE IN THE LANE, AND A NEGATIVE.** Jan 2016–Feb 2023, 1,775 trades (paper 1,795). Gross $0.070/share; break-even at ~2.2¢/share slippage; NQ-filter t=2.05 but "76% of the filtered PnL is 2022 alone"; Sharpe 0.77 vs 0.72 buy-and-hold, overlapping CIs. Placebo control (QQQ's own 09:25 bar) + bootstrap CIs. **Kills R9** |
| 3 | https://ssrn.com/abstract=4824172 · https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/ | 2026-09-08 | secondary (search-surface) | the SPY/ES intraday-momentum record | **YIELDED.** 2007–early 2024: +1,985% total, 19.6% annualised, Sharpe 1.33, net of costs. ES port: maxDD 24% vs 34% NQ long-only, +2bp/trade, 36% win rate, 2.09 payoff. Trailing stops, unlimited upside |
| 4 | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866 · https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351 | 2026-09-08 | **secondary, peer-reviewed** (search-surface) | a stated mechanism for S1 | **YIELDED THE MECHANISM.** Gao/Han/Li/Zhou, *Market Intraday Momentum*, JFE 2018. SPY 1993–2013; first half-hour predicts last half-hour; significant **out of sample**; stronger on volatile/high-volume/recession/macro-news days; present in 10 other ETFs. Mechanisms: Bogousslavsky (2016) infrequent rebalancing + late-informed trading |
| 5 | https://assets.super.so/e46b77e7-ee08-445e-b43f-4ffd88ae0a0e/files/ee7dac49-530b-4950-b5d0-e0b5eee08f2e.pdf | 2026-09-08 | secondary | the Gao et al. PDF, for t-stats and R² | **BLOCKED — PDF retrieved but not renderable in this environment (no poppler).** Content taken from #4 instead. Logged so it is not re-attempted; a future session with PDF rendering should read this file for the t-statistics |
| 6 | https://faculty.haas.berkeley.edu/odean/papers/Day%20Traders/Day%20Trading%20and%20Learning%20110217.pdf · https://www.sciencedirect.com/science/article/abs/pii/S0378426613002331 | 2026-09-08 | **secondary, peer-reviewed** (search-surface) | the base rate for day-trading profitability | **YIELDED THE NULL THE WHOLE TIER OMITS.** Barber/Lee/Liu/Odean, Taiwan, 3.7bn transactions 1992–2006: ~5% persistently profitable; −7 bp/day gross, **−23.9 bp/day net** (costs more than triple the gross loss); negative in 14 of 15 years; survival 44%/24%/15% at 1/2/3 years; 2.5% drop out within a month. Companion paper is on the **Taiwan futures** market |
| 7 | https://nilssonhedge.com/index/cta-index/systematic-cta-index/systematic-cta-index-short-term/ | 2026-09-08 | secondary (fetched) | verified performance of the short-hold CME manager tier | **YIELDED the denominator for the scale-free ratio.** Systematic Short-Term CTA index: 36 programmes (2026), "exploit anomalies, mean reversion, or short-term trends", some intraday-closing. **VAMI 125.34** since Jan-2023 launch (~6.3%/yr). Composition includes survivorship. No headline vol/maxDD/Sharpe published in text |
| 8 | https://www.iasg.com/ · https://www.iasg.com/blog/2024/12/12/the-anatomy-of-a-cta-choosing-the-right-trader-for-your-portfolio | 2026-09-08 | secondary (search-surface) | CTA drawdown norms | **YIELDED the drawdown budget of the verified tier.** "Returns targeted in the 20% range with 10% drawdowns are often ideal"; **"a 30% drawdown will end most programs."** Stock Index Trader index: 36 programmes, mostly intraday or short-gamma. Directly supports R8 |
| 9 | https://striker.com/ranking.php | 2026-09-08 | secondary (fetched) | actual-fill futures system results | **PARTIAL — the near-miss.** Actual client fills, "commissions, monthly vendor fees, and exchange/nfa fees included." Net P&L only (Edvardus Breakout Gold $76,149.64; Abacus Upside RTY $21,999.00; Abacus Advance $33,047.68; Atlas Pro Futures −$156.02). **No drawdown, no trade count, no average trade.** "Not necessarily representative of a single account" |
| 10 | https://striker.com/systems.php | 2026-09-08 | secondary (fetched) | per-system CME index-futures detail | **BLOCKED — the detail is behind a client login.** "Actual trading performance records for many (day and swing) systems… in the client section." The two fields the barrier needs (max DD, average trade) are not public. **Highest-value blocked avenue in this lane** |
| 11 | https://trade.collective2.com/ · https://collective2.com/details/52737021 · https://es-nq.collective2.com/ | 2026-09-08 | claims/secondary (search-surface) | verified intraday ES/NQ track records | **YIELDED A DISQUALIFYING SELF-DISCLOSURE, which is the finding.** Intraday-only ES/NQ strategies exist with real AutoTrader fills (one at 1,247 real-brokerage trades), but C2 states records **"must still be considered hypothetical"** — no single real account matches a Model Account; AutoTraders start/stop at will and apply their own stops. Honest, and fatal for use as evidence |
| 12 | https://help.myfundedfutures.com/en/articles/12802721-intraday-drawdown-explained | 2026-09-08 | **primary** (fetched) | the marking convention behind screen item 4 | **YIELDED, verbatim.** "The trailing drawdown is calculated intraday based on your peak balance, which includes both realized and unrealized gains"; "if your equity, including open trades, falls below the most recently adjusted drawdown limit, your account will breach the maximum loss limit." Ratchets up, never down, capped at starting balance. **This is the sentence that kills R1/R2/R4/R5/R6** |
| 13 | https://help.topstep.com/en/articles/10296582-prohibited-conduct | 2026-09-08 | **primary** (fetched) | the hedging prohibition behind screen item 2 | **YIELDED, verbatim.** Prohibited: "coordinated trading" (trades with others to pool risk or hedge positions), **"cross-account hedging (single-user)"**, "price exploitation", "disruptive practices" incl. spoofing, "unfair technology" (software/AI/ultra-high-speed), "account stacking". **Nuance the brief should absorb:** Topstep states violations are "reviewed case-by-case based on severity and history" — outcomes range from warning to closure, so "terminal and unappealable" is the industry characterisation, not Topstep's own wording. Arbitrage, HFT, latency, DCA are **not** named |
| 14 | https://help.myfundedfutures.com/en/collections/9384339-rules | 2026-09-08 | primary | MFFU's full prohibited-practice list | **BLOCKED — HTTP 404.** Collection URL is wrong or retired. Logged so it is not re-attempted with this path; lanes 01–05 should locate MFFU's rules index by another route |
| 15 | https://automatedtradingstrategies.substack.com/p/the-prop-firm-paradox-win-too-much | 2026-09-08 | claims (fetched) | a first-person account of a rule bite | **YIELDED R7, the missing screen item.** Consistency rule quoted: "your best trading day can't be better than 50% of your total." $150k account, $9,000 target beaten by $123, 64% win rate over 11 days, best day 3.74% of account, best two days 49.7% of total → **additional $2,205 requirement imposed.** "The consistency rule is punishing excellence rather than preventing gambling." Sells nothing; solicits reader replies |
| 16 | https://hoc-trade.com/blogs/trading-psychology/prop-firm-challenge-why-fail | 2026-09-08 | claims (fetched) | the breach post-mortem dataset | **PARTIAL, AND THE CIRCULARITY IS THE FINDING.** Behaviours with prevalence: "fail to call it a day" 75.6%, overtrading 49.5% (~25% of losses), revenge trading 37.1% (~12%), doubling down (~20% of losses, 5.3% profit rate when top issue), refusing to cut losses. But the load-bearing 71% daily-drawdown figure is attributed to "a widely cited industry breakdown" — **no upstream source, no sample period, no dates.** Sells TradeMedic™ AI. Confirms lane 07's WEAK rating and traces it |
| 17 | https://www.tradealgo.com/trading-guides/futures/es-futures-scalping-guide | 2026-09-08 | claims (fetched) | the scalping tier's own arithmetic | **YIELDED ANTI-SCREEN SPECIMEN 1 AND NEW TELL 13.** "$4.00 round-trip per ES contract" called "32% of a 2-tick scalp" and "10.7% of a 3-tick scalp" — the second checks (4.00/37.50 = 10.67%), the first is **exactly 2× wrong** (4.00/25.00 = 16.0%). Plus "consistent 60%+ win rate" with no payoff, "$500-$2,000 per day", "$5,000-$15,000" monthly, no backtest/sample/null, and "upgrade to Premium starting at $149/year" |
| 18 | https://www.topstep.com/blog/funded-trader-mindset | 2026-09-08 | claims (fetched) | firm-published trader interviews, for strategy attribution | **YIELDED A CLEAN NEGATIVE — SPECIMEN 3.** No instrument, no setup, no holding time, no stop rule, no trade frequency. Sole concrete trading detail: Steenbarger switching "from one-minute bars to 15-second charts," offered as personal adaptation. Only quantitative content is the payout split ("first $10K", then 90/10). **The firm-interview tier does not carry strategy attribution** |
| 19 | https://blog.topsteptrader.com/topic/topstepfx-funded-traders · https://www.topstep.com/blog · https://www.topstep.com/topics/funded-trading | 2026-09-08 | claims (search-surface) | named funded-trader profiles with setups | **NOTHING USABLE — logged as one cluster.** Profiles exist (Corbett C., Nick M., Alex Ferreira) and are uniformly testimonial: tenure, discipline, routine. No instrument or setup attribution surfaced for any of them. Second of three attempts at this sub-question |
| 20 | https://www.reddit.com/r/FuturesTrading/search/?q=funded+account+strategy | 2026-09-08 | claims | practitioner threads on what funded traders run | **BLOCKED — "Claude Code is unable to fetch from www.reddit.com."** Not retryable by this route. Logged so the next session does not attempt it. The unmoderated-forum tier (Reddit, futures.io, EliteTrader) is therefore **unsampled** in this lane, and that is a real limitation of its coverage |
| 21 | https://x.com/TradersPrism/status/2084915899736469601 | 2026-09-08 | claims (search-surface) | how the hedging clause is enforced | **YIELDED a mechanism claim, unverified.** "Every personal account must trade the same direction, and hedging correlated instruments is prohibited"; "a hedging clause that one partial fill can break"; detection by "IP matching, hardware and browser fingerprinting, and millisecond timestamp clustering." **Hypothesis only** — no firm T&C confirms the fingerprinting claim. Cited for R3's severity, not relied on |
| 22 | https://traderssecondbrain.com/guides/futures-prop-firms-news-trading · https://copilink.com/articles/prop-firms-that-allow-trade-copying-2026 | 2026-09-08 | claims (search-surface) | per-firm news and copy-trading rules | **PARTIAL, and firm-dependent, which is itself the point for R6.** Topstep permits news trading with standard risk rules; Apex "has historically restricted near events"; Topstep built its own copier, Apex forbids copying *with other traders* but permits it across your own accounts. **Not portable across the grid — verify per firm in lanes 01–05, do not rely on this row** |
| 23 | https://crosstrade.io/learn/risk-management/trailing-drawdown-survival-guide · https://fundedfuturesnetwork.zendesk.com/hc/en-us/articles/46870383826587 | 2026-09-08 | claims / primary-adjacent (search-surface) | end-of-day vs intraday floor mechanics | **YIELDED the geometry distinction that changes screen item 4.** Under an **end-of-day** floor, "if your equity swings up $1,000 during the day but you close flat, the floor doesn't move" — so open-equity peaks do not ratchet. **This materially loosens item 4 for EOD-floor firms and S1's falsification test must be run separately for each geometry.** Under intraday floors it does not apply |
| 24 | https://propfirmmap.com/blog/prop-firm-payout-leaderboard-2026-who-actually-pays-verified-data · https://propfirmmatch.com/payouts-leaderboard · https://payoutjunction.com/alltime · https://propfirmsfinder.com/payouts-leaderboard/ | 2026-09-08 | claims (search-surface) | payout leaderboards, for strategy attribution of *paid* traders | **NOTHING FOR THIS LANE — logged as one cluster.** Every leaderboard ranks **firms by dollars**, never traders by method. Self-reported ("Tradeify Futures $346.6M across 169k payouts"; "one trader… $2,552,800.50"), TrustPilot-weighted, no denominator, no strategy field anywhere. Third and final attempt at the sub-question. **This is where saturation was declared** |
| 25 | https://www.quantvps.com/blog/prop-firms-allow-scalping · https://fortraders.com/blog/5-proven-strategies-to-pass-a-prop-firm-challenge · https://www.tradezella.com/blog/pass-prop-firm-challenge | 2026-09-08 | claims (search-surface) | "how to pass" strategy content | **NOTHING — logged as one cluster, and it is what the tier is made of.** Firm rankings by scalp-hold-time permissiveness; "5 proven strategies" with no sample, no cost convention, no null; risk-management frameworks with no data behind them. Zero mechanism, zero falsifiable content. Every page is attached to a vendor (VPS hosting, a prop firm, a journaling product) |

**Negative and blocked entries, per schema §4:** #5 (PDF unrenderable), #10 (Striker detail behind a
login — the most valuable block), #14 (404), #18/#19/#24 (three consecutive attempts at
"what do winners run", all empty — the saturation signal), #20 (Reddit unfetchable, so the
unmoderated-forum tier is unsampled), #25 (the how-to-pass tier yields nothing).

**Searches run that produced no new source, so they are not repeated:** firm-published breach-cause
breakdowns (none exists for any of the five firms); futures.io and EliteTrader threads on funded-account
strategy (not reachable via the search index used); an independent replication of the *futures*
intraday-momentum implementation (none found — #1 is unreplicated); options-on-futures availability at
futures prop firms (not stated on the pages reached; treat R5's scope claim as unconfirmed and verify
in lanes 01–05).
