# F5 — retail execution and cost reduction: external evidence

Research only. Nothing here was run, backtested, or verified against this
programme's own data. All web sources fetched **2026-09-09**. Provenance tags on
every claim; §10 lists URLs.

Two mechanical notes that shape everything below:

- IBKR's public pages 403 the standard fetch tool but serve fine to a browser
  user-agent. The block is a UA exclusion, not a host block — the pages are
  public. (Recording this because a "blocked source" here has twice been a UA
  exclusion.)
- IBKR's commission page carries **no effective date** and states "IBKR may
  change these rates at any time in its sole discretion." Every IBKR number
  below is *as published on 2026-09-09*, not a dated schedule.

---

## 1. Verdict

**The programme's cost model is about right for how it currently executes, and
probably slightly too KIND on the cheap illiquid names where its edge lives —
the opposite of the premise.** Three findings drive this. (i) On the fee
schedule alone, moving IBKR Pro Fixed → Tiered is worth roughly **0.2–2.0
bp/side**, almost all of it from the lower per-order minimum ($0.35 vs $1.00),
and it is a *pure* saving with no execution-quality cost at the auction
[BROKER OFFICIAL DOC]. (ii) The one large number available — a real-money,
peer-reviewed experiment finds **IBKR Pro's effective/quoted spread ratio ≈ 0.62
on small marketable orders**, i.e. a SmartRouted market order pays ~62% of the
quoted half-spread, not 100% [PEER-REVIEWED] — **is not available to this
programme as it trades**, because it enters and exits in the opening and closing
auctions, and IBKR's own Rule 606 filing states it receives no order-flow payment
and does no wholesaler internalisation for On Open / On Close orders
[PRIMARY REGULATORY]. In the auction there is no NBBO to price-improve against,
and the auction print itself "typically match[es] pre-close bid or ask prices"
[PEER-REVIEWED] — i.e. roughly a full half-spread, which is what the model
already charges. (iii) Cutting the other way, the estimator the model uses is
documented to be **biased downward for small and less liquid stocks**:
Corwin–Schultz "underestimate[s] the effective spread for small and less liquid
stocks" and its bias worsens as trading gets infrequent [PEER-REVIEWED]. So the
model's *level* on the cheap tail is more likely too low than too high. Honest
ceiling: **~0.5–1.5 bp/side is genuinely and immediately saveable from the fee
schedule and position sizing; a further ~4–7 bp/side is available ONLY by
abandoning auction execution for SmartRouted continuous marketable orders, which
is a different strategy and must be re-backtested, not re-costed.** If the
programme keeps executing at the open and close, the answer to "how many bp are
on the table" is **small — about one, maybe two**. That is the valuable result:
**the cost model is not the problem.**

---

## 2. IBKR's cost stack: fixed vs tiered

[BROKER OFFICIAL DOC] — <https://www.interactivebrokers.com/en/pricing/commissions-stocks.php>,
fetched 2026-09-09. US stocks/ETFs/warrants, IBKR Pro, direct client.

### Published schedule

| | IBKR Pro **Tiered** | IBKR Pro **Fixed** | IBKR **Lite** |
|---|---|---|---|
| ≤ 300,000 sh/month | USD 0.0035/sh | USD 0.0050/sh | USD 0.0020/sh |
| 300,001–3,000,000 | USD 0.0020 | — | — |
| 3,000,001–20,000,000 | USD 0.0015 | — | — |
| 20,000,001–100,000,000 | USD 0.0010 | — | — |
| > 100,000,000 | USD 0.0005 | — | — |
| **Minimum per order** | **USD 0.35** | **USD 1.00** | USD 0.003 |
| **Maximum per order** | 1% of trade value | 1% of trade value | USD 0.00 |
| Third-party fees added | Regulatory + Exchange + Clearing + Pass-Through | **Regulatory only** | Regulatory only |

Volume tiers are marginal within a calendar month and summed across US+Canada
shares. At a few thousand dollars per name this programme lives permanently in
the top row: **0.0035/share Tiered, 0.0050/share Fixed.**

### The add-ons that only Tiered pays

**Regulatory (paid under BOTH schemes — not a lever):**
- SEC Transaction Fee: `0.0000206 × value of aggregate sales` → **0.206 bp of
  notional, sells only**
- FINRA Trading Activity Fee: `0.000195 × quantity sold`
- FINRA CAT: `0.000003 × quantity` (both sides)

At $13/share a sell therefore carries ~0.206 + 0.152 = **~0.36 bp of
unavoidable regulatory cost**; a buy carries ~0.002 bp. No routing or pricing
choice touches this.

**Clearing (Tiered only):** NSCC/DTC `USD 0.00020 per share`.

**Pass-through (Tiered only):** NYSE `commissions × 0.000175`, FINRA
`commissions × 0.000565` — jointly ~0.00074 × commission, i.e. ~$0.0000026/share.
Numerically irrelevant; listed for completeness.

**Exchange fees / rebates (Tiered only)** — this is the whole game. From IBKR's
own per-venue pass-through tables, US stocks ≥ $1.00
([NYSE](https://www.interactivebrokers.com/en/accounts/fees/NYSEstkfee.php),
[NASDAQ/INET](https://www.interactivebrokers.com/en/accounts/fees/INETstkfee.php),
[ARCA](https://www.interactivebrokers.com/en/accounts/fees/ARCAstkfee.php),
[IEX](https://www.interactivebrokers.com/en/accounts/fees/IEXstkfee.php)):

| Action | NYSE | NASDAQ | ARCA | IEX |
|---|---|---|---|---|
| Remove liquidity (displayed) | +0.0030 | +0.0030 | +0.0030 | +0.0030 |
| Remove, **retail-designated order** | — | — | — | **0.0000** |
| Add liquidity (Tape A retail / std) | −0.0032 / −0.0012 | −0.0013 to −0.0018 | −0.0016 to −0.0020 | 0.0000 |
| Add, midpoint (MPL) | −0.0030 retail / −0.0010 | −0.0010 | −0.0010 | +0.0010 (non-disp, both sides) |
| **Market-on-open** | **+0.0010** | **+0.0015** | +0.0015 ("At the Open") | +0.0003 (auction) |
| **Market-on-close** | **+0.0010** | **+0.0016** | +0.0012 ("At the Close") | +0.0003 (auction) |
| **Limit-on-close** | **+0.0011** | +0.0015–0.0016 | +0.0006 (closing auction limit) | +0.0003 |
| Sub-$1.00 remove | trade value × 0.0030 | trade value × 0.0030 | ×0.0030 | ×0.0020 |
| Routed away | +0.0035 | — | +0.0035 | — |

(Parentheses in IBKR's tables denote rebates. Rebates are passed to Tiered
clients but IBKR states volume-tier *enhancements* are not.)

### All-in per-share cost, ≤300k shares/month

| Order style | Tiered all-in | Fixed | Cheaper |
|---|---|---|---|
| Marketable, takes liquidity on a lit exchange | 0.0035+0.0030+0.0002 = **0.00670** | 0.0050 | **Fixed** by 0.0017 |
| Marketable, retail-designated to IEX | 0.0035+0.0000+0.0002 = **0.00370** | 0.0050 | Tiered by 0.0013 |
| **MOC / MOO, NYSE-listed** | 0.0035+0.0010+0.0002 = **0.00470** | 0.0050 | Tiered by 0.0003 |
| **MOC, Nasdaq-listed** | 0.0035+0.0016+0.0002 = **0.00530** | 0.0050 | Fixed by 0.0003 |
| **MOO, Nasdaq-listed** | 0.0035+0.0015+0.0002 = **0.00520** | 0.0050 | Fixed by 0.0002 |
| Passive limit that rests and is hit (NYSE Tape A retail) | 0.0035−0.0032+0.0002 = **0.00050** | 0.0050 | **Tiered by 0.0045 (10×)** |
| Passive limit, Nasdaq add | 0.0035−0.0013+0.0002 = **0.00240** | 0.0050 | Tiered by 0.0026 |

### The crossover

Per-share, ignoring minimums, the crossover is *not* an order size — it is an
**order style**. Fixed is cheaper for marketable exchange-routed orders; Tiered
is cheaper for auctions on NYSE-listed names and dramatically cheaper for
liquidity-adding orders.

Including the minimums (`C_fix = max(1.00, 0.005N)` capped at 1% of value;
`C_tier = max(0.35, 0.0035N) + venue·N + 0.0002N`), the **share-count**
crossovers are:

- **NYSE-listed auction orders: Tiered is cheaper at every share count.**
- **Nasdaq-listed auction orders:** Tiered cheaper below **≈189 shares**, Fixed
  cheaper above. (≈$2,500 at $13.19, ≈$945 at $5, ≈$9,450 at $50.)
- **Continuous marketable orders:** Tiered cheaper below **≈149 shares**, Fixed
  cheaper above. (≈$1,970 at $13.19.)

Since the programme's orders are a few thousand dollars, it straddles all three
crossovers depending on price. **Practical answer: switch to Tiered.** It is
never materially worse (max −0.23 bp/side at $13 on a Nasdaq MOC) and is up to
~2 bp/side better on higher-priced small-share-count orders, plus it opens the
rebate path in §5.

### Two traps worth knowing

- **API direct-routed orders cost USD 0.0075/share under Fixed, and cannot use
  Tiered at all** ("directed API orders cannot use the Tiered fee structure;
  SmartRouted API orders can use either"). If any live implementation ever
  direct-routes from the API, it silently pays 50% more than Fixed SmartRouted.
- **IBKR Lite's $0 commission does not apply to this programme.** Verbatim:
  "Trades resulting from OnClose, OnOpen, or outside regular trading hours … are
  commission-free for IBKR Lite clients so long as the total monthly volume of
  shares executed via any combination of Open auction, Close auction,
  Outside-RTH, or Sub-Dollar order(s) does not exceed **10% of an account's
  monthly US stock trading volume** … otherwise your account will be charged the
  lesser of (i) USD 0.005 per share or (ii) 1% of trade value." A strategy that
  executes ~100% at the open/close is charged **exactly the Fixed rate** on
  Lite, with none of Pro's routing control. Lite is not a free lunch here.

---

## 3. The per-order minimum and the smallest sensible position

The minimum is **per order and per share count, not per notional.** That is the
correction to the recorded "$1.00 minimum binds below roughly $2,100 notional".

**The rule:**
- **Fixed:** `0.005 × N < 1.00` ⇒ the minimum binds for **N < 200 shares**.
- **Tiered:** `0.0035 × N < 0.35` ⇒ the minimum binds for **N < 100 shares**.

Converted to notional, the binding threshold is `200 × P` (Fixed) — so the
"$2,100" figure is right only at a share price of $10.50. At the programme's
recorded $13.19 median it is **$2,638**; at $5 it is **$1,000**; at $50 it is
**$10,000**. **Verdict on the lead: approximately right by coincidence, wrong as
a rule. Restate it as a share count.**

**Commission in bp/side while the minimum binds** is simply
`10,000 × min / notional`, independent of price:

| Notional/order | Fixed ($1.00 min) | Tiered ($0.35 min) |
|---|---|---|
| $1,000 | 10.0 bp | 3.5 bp |
| $2,000 | 5.0 bp | 1.75 bp |
| $3,000 | 3.3 bp | 1.17 bp |
| $5,000 | 2.0 bp | 0.70 bp |
| $10,000 | 1.0 bp | 0.35 bp |

**Smallest sensible position:** to hold commission under **1 bp/side** you need
**≈$10,000/order on Fixed or ≈$3,500 on Tiered** *while the minimum binds*; once
it stops binding, commission bp = `0.005/P` (Fixed) or `~0.0047/P` (Tiered
NYSE auction), i.e. 3.8 bp at $13, 10 bp at $5, 1.0 bp at $50 — a floor that
size cannot fix and **that scales inversely with price**, exactly as the
programme already found.

Independent confirmation that this trap is real and large: the JF 2025 real-money
experiment [PEER-REVIEWED] paid IBKR Pro commissions averaging **$0.35 per
trade** on a median 5-share trade — "**$0.07 per share or 35 bp of notional**."
They were on Tiered and pinned to its minimum on every order.

Two secondary rules from the same page: **a modified order is treated as a
cancel-and-replace and can incur a fresh minimum**, and orders that persist
overnight count as new orders. Any live re-pricing logic pays the minimum again
each amendment.

---

## 4. Effective vs quoted spread for retail orders

This is the number the brief asked for. There are two credible measurements and
they disagree, for a reason that matters.

**(a) Rule 605 population study — Dyhrberg, Shkilko & Werner, JFE 2025**
[PEER-REVIEWED]. All US equities, Jan 2019–Mar 2022, 14 exchanges + 8
wholesalers, ~2.9tn shares (~40% of CRSP volume), liquidity-demanding orders,
≥100 shares (Rule 605 excluded odd lots then). Share-volume-weighted:

| | Wholesalers (PFOF route) | Exchanges |
|---|---|---|
| Quoted spread at execution | 64.92 bp | 48.67 bp |
| Effective spread | 49.06 bp | 46.98 bp |
| **Effective / quoted (E/Q)** | **0.76** | **0.97** |
| Price improvement, full sample | 24% of quoted spread | 3% |
| Price improvement, S&P 500 | 44% | 6% |
| % of marketable orders improved, S&P 500 | 75% | 12% |
| % improved / PI, size Tercile 2 | 64% / 27% | 9% / 5% |
| 5-min price impact | 32.53 bp | 47.32 bp |

Note the sign of the size effect: **exchange price improvement is ~5–6% of the
spread and roughly constant across size terciles**, while wholesaler improvement
falls as firms get smaller. And retail flow executes when quoted spreads are
**33% wider** than when institutions trade — retail does not time liquidity.

**(b) Broker-level real-money experiment — Schwarz, Barber, Huang, Jorion &
Odean, JF 2025** [PEER-REVIEWED]. 85,417 simultaneous market orders across six
accounts at five brokers, Dec 2021–Jun 2022, 113 days, funded with the authors'
own money; median share price ~$20, median spread $0.05 ≈ 25 bp; $100 target
size with robustness runs at $1,000 and $5,000 ("similar execution"). They
define PI% relative to the full quoted spread, so 50% = midpoint.

| Broker | % of trades improved | Avg PI (% of quoted spread) | Implied one-way E/Q |
|---|---|---|---|
| TD Ameritrade | 99.4% | 47.2% | **0.056** |
| Fidelity | — | 35.8% | 0.284 |
| E*Trade | ≈ Fidelity | ≈ 35% | ≈0.30 |
| Robinhood | — | 26.8% | 0.464 |
| **IBKR Pro** | **76%** | **18.8%** | **0.624** |
| IBKR Lite | — | "slightly worse" than Pro | ≈0.62–0.65 |

Round-trip cost excluding commissions ranged **−0.07% (TD) to −0.46%** across
accounts; worst-possible (NBO→NBB) was 61.9 bp. **IBKR Pro was the worst
price-improver in the study.**

**Reconciling (a) and (b):** IBKR Pro does not accept PFOF and does not route to
wholesalers, so it does not get the 0.76 wholesaler ratio — but SmartRouting does
reach eight dark pools and IBKR's own ATS, which is why it lands at 0.62 rather
than the 0.97 pure-exchange figure. **The best-supported single number for this
account type on marketable continuous orders is E/Q ≈ 0.62, i.e. ~62% of the
quoted half-spread, on order sizes up to at least $5,000.**

**The caveat that neutralises it for this programme.** IBKR's own Rule 606a
filing states verbatim: "For both marketable and non-marketable orders, **IBKR
receives no payments for executions outside of regular trading hours and
executions resulting from On Open and On Close orders**" [PRIMARY REGULATORY].
Auction orders go to the primary exchange's auction; there is no NBBO to improve
against, no wholesaler in the path, and none of the 0.62 applies. The programme
enters and exits at the open and the close. **The highest-value number in this
report is one the programme cannot currently collect.**

**A dated opportunity.** The amended Rule 605 extends reporting to every
broker-dealer introducing or carrying ≥100,000 customer accounts, adds odd-lot
and fractional size buckets, adds an explicit **average effective/quoted spread
statistic**, and requires a Summary Report split S&P 500 vs non-S&P 500 by order
type and size. **Compliance date 1 August 2026; the first monthly reports, for
August 2026, are due to be published before the end of September 2026**
[PRIMARY REGULATORY, SEC staff FAQ dated 2026-04-01]. That means **IBKR's own
E/Q for its own client flow, cut by order size and by S&P/non-S&P, becomes public
within weeks of this writing.** That is a free, exact, broker-specific
replacement for every estimate in this section. It is the single highest-value
follow-up here and it costs nothing but a download.

---

## 5. Order types and price improvement

**What IBKR documents [BROKER OFFICIAL DOC] — and what it does not.**

- **MidPrice order** (stocks/ETFs only): "attempts to fill at the current
  midpoint of the NBBO or better," optional price cap. Implementation: routed to
  the exchange with the highest fill probability as a **Pegged-to-Midpoint**
  order, or to **IEX as a Discretionary Peg (D-Peg)**; otherwise a native or
  simulated Relative order.
- **Adaptive Algo (IBALGO)**: "designed to ensure that both market and aggressive
  limit orders trade between the bid and ask prices," with Urgent / Normal /
  Patient priority. "On average, this order type should lead to better fills…
  most useful when the spread is wide." Not supported as GTC.
- **SmartRouting**: includes eight dark pools; for **Tiered ("Cost Plus") clients
  only**, non-marketable orders can be directed to the exchange with the highest
  rebate, the listing exchange, the highest-volume exchange with an add rebate,
  or the highest-volume exchange with the lowest take fee.

**Critical gap: IBKR publishes no quantified price improvement for any of these
order types.** Every claim above is qualitative. There is no per-order-type
effective/quoted statistic, no fill-rate table, no adverse-selection measure.
Treat "should lead to better fills" as **[UNVERIFIED]**.

**IBKR's headline execution claim is a sales instrument.** The Best Execution
page states that for **August 2026** IBKR Pro clients' total trading cost
"including commissions and regulatory fees" was **0.021% of trade value (0.025%
over the trailing 12 months)**, on 27.57m orders and an average trade size of
**$22,288** [SALES INSTRUMENT]. The benchmark is *the daily VWAP*: "if all our
clients' buy and sell orders were executed each day at the daily VWAP … then
their trading cost would be zero." A roughly balanced book of buys and sells
crossing spreads at random times through the day nets to ~zero against daily
VWAP by construction. **2.1 bp is not a spread estimate and must not be used as
one.** The average trade size is also ~7× this programme's. Separately-circulated
figures of "$0.31 price improvement per 100 shares vs an industry $0.26" trace to
a Transaction Auditing Group study cited in IBKR marketing — **[SALES
INSTRUMENT], not independently verified, and flatly inconsistent with the JF 2025
experiment that ranked IBKR Pro last of five brokers on price improvement.**

**Rebate harvesting is not free money.** Battalio, Corwin & Jennings, JF 2016
[PEER-REVIEWED], document a **negative relation between limit-order execution
quality and the level of the venue's rebate**: routing to maximise rebates does
not maximise limit-order execution quality. The 0.0005/share net cost of a
rebate-earning passive NYSE fill in §2 is real, but it is paid for in fill rate
and adverse selection, and the size of that payment is not measurable from
public data. If the programme ever tests passive execution, the rebate must be
scored *jointly with the unfilled-order cost*, not as a commission line.

**IEX is the one concrete, unconditional saving.** IBKR's IEX pass-through table
shows **USD 0.0000 both sides for retail orders ≥ $1.00**, and 0.0003 for
auction. A retail-designated marketable order routed to IEX costs
0.0035 + 0.0000 + 0.0002 = **0.0037/share all-in on Tiered — cheaper than Fixed's
0.0050 and 45% cheaper than the 0.0067 of a standard lit take.** IBKR's NYSE
table also lists distinct "Tape A Retail" rates, implying IBKR does submit
retail-designated flow. **[UNVERIFIED]**: whether the programme can force retail
designation and IEX routing from the API, and what it costs in fill probability.

---

## 6. Auction execution at the open and close

**Cut-off times** [exchange primary docs]:

| | NYSE | Nasdaq |
|---|---|---|
| MOC entry/modify/cancel | until **3:50 pm ET**; after 3:50 only contra-side of a published Significant Imbalance, until 4:00; no modify/cancel after 3:50 | MOC accepted until **3:55 pm**; from 3:50 cannot be cancelled/modified |
| LOC | same as MOC | until **3:58 pm**, no cancel/modify once posted |
| Imbalance-only | — | until 4:00 pm |
| Imbalance dissemination | from 3:50, every 1s | NOII |
| Opening | orders enterable/cancellable until the DMM opens the security; imbalance feed from 8:00 am | Opening Cross at 9:30; NOII from 9:28 (imbalance from 9:25) |

**Practical consequence: 3:50 pm is a hard commitment point on NYSE.** A signal
computed on the close cannot be executed in that close. Any live implementation
must either compute on a 3:50 snapshot or accept a one-day lag — and if the
backtest fills at the official close, the lag audit must cover this, because it
is exactly the class of error that killed D279.

**Fees: auctions are CHEAPER than continuous, under Tiered.** From §2: NYSE
MOC/MOO 0.0010/share and LOC 0.0011 versus 0.0030 to remove liquidity
continuously; Nasdaq MOC 0.0016, MOO 0.0015; ARCA closing/opening *auction limit*
orders 0.0006. **Saving vs a continuous marketable order: 0.0014–0.0024/share,
i.e. 1.1–1.8 bp/side at $13, 2.8–4.8 bp at $5, 0.3–0.5 bp at $50.** Under Fixed
this saving is invisible — exchange fees are bundled into the 0.005 — which is
by itself a reason to move to Tiered given that this programme is an
auction-only strategy.

**Effective-spread terms: the auction is roughly a full half-spread, not free.**
Bogousslavsky & Muravyev (*Journal of Financial Markets* 2023) [PEER-REVIEWED]:
closing auctions were 7.5% of daily volume in 2018 (3.1% in 2010); "closing
prices typically match pre-close bid or ask prices, and price impact is lower
than during continuous trading"; "auction price deviations revert quickly and
almost completely." A print at the bid or the offer is a full half-spread away
from the mid. **So charging a full quoted half-spread at the close is
approximately correct — the programme's model is right here.**

**Price impact at the auction — the number to use for sizing.** Goyal, Jegadeesh
& Wu, *JFQA* 2026 [PEER-REVIEWED], NYSE+Nasdaq auction data, TAQ, CRSP,
2012–2021:

- Price impact in auctions follows a **square-root** law in order size, not a
  linear one. For a **1% ADV** order the closing-auction impact is **17.7 bp**
  under the square-root fit versus **2.35 bp** under the linear fit — i.e. the
  linear models the industry uses **understate small-order-scaled costs by ~7×**
  in the relevant direction.
- **Price impact is lower in closing auctions than in the continuous market for
  all stocks except Nasdaq microcaps.**
- **Opening auctions have the largest price impact of the three mechanisms.**
- Annual two-way trading costs for low-turnover anomaly strategies (profitability,
  investment) executed in the closing auction: **2–15 bp/year**.
- Closing auctions are ~10% of ADV in recent years and attract uninformed flow.

A per-size breakdown by exchange and size bucket (e.g. NYSE micro 18.2 bp vs
Nasdaq micro 44.7 bp at 1% ADV) appeared in one automated read of the Cambridge
page but **could not be verified against the paper text — treat as
[UNVERIFIED]**. The pooled 17.7 bp figure was confirmed twice independently.

**Two directly actionable implications:**
1. **Close beats open.** Opening-auction impact is the largest of the three
   mechanisms. Any construction that enters at the open is paying more than the
   same construction entering at the close. The programme has never priced that
   difference; it should.
2. **Square-root scaling means small orders are relatively dearer than a linear
   model implies.** At 0.01% of ADV the square-root law gives
   17.7 × √(0.0001/0.01) = **1.8 bp**, where the linear law would give 0.02 bp.
   And this programme has already found one case where its order was **2.5% of
   the opening minute's volume** despite being 0.04% of daily volume — the
   opening auction's own volume is a small fraction of ADV, so *% of auction
   volume*, not *% of ADV*, is the correct denominator at the open.

---

## 7. Cheap stocks and the 2024 tick-size / access-fee amendments

**The tick floor, exactly.** Rule 612 sets a $0.01 minimum quoting increment for
NMS stocks priced ≥ $1.00. That is a hard floor on the quoted spread, and in
basis points it scales as `100/P`:

| Price | One-cent spread, in bp | Half-spread |
|---|---|---|
| $2 | 50.0 bp | 25.0 bp |
| **$5** | **20.0 bp** | **10.0 bp** |
| $10 | 10.0 bp | 5.0 bp |
| **$13.19** (programme median) | **7.6 bp** | **3.8 bp** |
| $25 | 4.0 bp | 2.0 bp |
| $50 | 2.0 bp | 1.0 bp |

The SEC's own framing [PRIMARY REGULATORY]: "For low-priced securities, the fixed
tick accounts for a greater percentage of the share price." The SEC also
estimates that **up to 74.3% of NMS share volume is tick-constrained**, and the
final rule defines tick-constrained as a **time-weighted-average quoted spread of
$0.015 or less** (commenters argued for $0.011).

**What the 2024 amendments change** (adopted 18 September 2024; fact sheet
34-101070) [PRIMARY REGULATORY]:

| Minimum pricing increment | If the stock's Time Weighted Average Quoted Spread during the Evaluation Period was |
|---|---|
| **$0.005** | **$0.015 or less** |
| $0.01 | greater than $0.015 |

- Evaluation periods: Jan–Mar (operative 1 May – 31 Oct) and Jul–Sep (operative
  1 Nov – 30 Apr). Measured by the primary listing exchange.
- **Access fee cap under Rule 610(c) cut from $0.0030 to $0.0010 per share** for
  protected quotations in stocks ≥ $1.00 (0.1% of price for stocks < $1.00), and
  all exchange fees and rebates must be **determinable at the time of execution**
  (volume tiers must be based on a prior period).
- Round-lot definition accelerated; odd-lot information added to the SIP,
  including a new "best odd-lot order" element.

**Status as of 2026-09-09 — this is NOT in force.** Original compliance date was
the first business day of November 2025. Nasdaq and Cboe litigated; the D.C.
Circuit **upheld the rule (opinion 14–15 October 2025)**, but the SEC granted
temporary exemptive relief on **31 October 2025** pushing Rules 612, 610(c) and
600(b)(89)(i)(F) to **the first business day of November 2026**, and then on
**11 June 2026** Chairman Atkins extended that again to **the first business day
of November 2027**, while directing staff to review Rules 610(c) and 612 "by the
end of the year, including whether potential changes … may be appropriate." The
Commission separately proposed to rescind Rule 611 the same day. **Odd-lot
information was not delayed and had a compliance date of the first business day
of May 2026.**

**What this means for the cost model:**
1. **Nothing changes historically.** Every backtest to date sits entirely in the
   one-cent regime. There is no historical comparison to adjust.
2. **Forward, the help is aimed at the wrong names.** The half-penny tick only
   reaches stocks whose TWA quoted spread is **≤ 1.5 cents** — i.e. names that
   are *already* tight. A $13 name quoted a penny wide qualifies and its spread
   floor could halve from 7.6 bp to 3.8 bp. But the programme's problem names —
   the $1.92-tenth-percentile, 33.8 bp-spread tail — quote far wider than 1.5
   cents and **are explicitly excluded**. The reform helps the names the
   programme least needs help on.
3. **The access-fee cut is a genuine but small forward saving under Tiered.**
   0.0030 → 0.0010 on removing liquidity is 0.0020/share, ~1.5 bp/side at $13 —
   but it applies to *continuous marketable* orders, not auctions, and add
   rebates will compress correspondingly, so the passive path in §5 gets worse.
4. **Sub-$5 and sub-$1 names.** The universe is floored at $5, so the sub-$1
   regimes (0.0001 increments; exchange fees charged as *trade value × 0.0030*
   rather than per share; IBKR's explicit warning about "ECN charges for removing
   liquidity when sending marketable orders for low priced stocks (under USD
   2.50)") do not bite today. They would bite immediately if the floor were ever
   relaxed, and the fee basis flips from per-share to per-value at $1.00 — a
   discontinuity any future cost model must encode.
5. **All of this is contingent.** Two delays and an open Commission review mean
   November 2027 should be treated as a plan, not a date.

---

## 8. The honest ceiling

Baseline being improved on: "full quoted half-spread + IBKR Fixed commission."
Per side, for a few-thousand-dollar order in a $5–50 US stock.

| Lever | bp/side saved | Confidence | Cost / condition |
|---|---|---|---|
| Fixed → Tiered, NYSE-listed auction orders | **0.2 (at $13) to 1.9 (at $50)** | High — published schedule arithmetic | None. Slight loss (−0.23 bp at $13) on Nasdaq-listed MOC |
| Not tripping the per-order minimum (size ≥ 200 sh Fixed / 100 sh Tiered) | **0 to 8+** depending on how small the orders are | High | Position-sizing change, concentrates the book |
| Regulatory floor that no choice removes | **−0.36 bp on every sell** at $13 | High | Unavoidable |
| Route retail-designated marketable flow to IEX (0.0000 take fee) | **0.2 (at $13)** | Medium — schedule is published; retail designation unverified | Fill probability unknown |
| Enter at the close rather than the open | **positive, unquantified** | Medium — GJW find opening impact largest of the three | Changes the construction |
| Continuous SmartRouted marketable instead of auction: E/Q 1.00 → 0.62 | **~4–7 bp** on a 25–34 bp-spread name | Medium — one peer-reviewed real-money study, $20 median price, 2021–22 | **This is a different strategy.** Fill price is no longer the open/close; the signal must be re-backtested, not re-costed |
| Passive limit / rebate harvesting (0.0050 → 0.0005/share, plus earning the spread) | up to a full half-spread + 0.35 bp | **Low** | Battalio et al.: rebate-maximising routing degrades limit-order execution quality; unfilled-order cost unmeasured |
| Half-penny tick + access-fee cap | ~1.5 bp on continuous takes, 0 on auctions | Low | Not before Nov 2027, twice delayed, under review; excludes wide cheap names |

**The honest answer, without changing what the strategy does:
0.5–1.5 bp/side.** Take the top of that range only for the higher-priced,
smaller-share-count names where the $1.00 minimum currently binds. It is real,
it is free, and it is roughly one-tenth of what would be needed to rescue the
constructions that died.

**The honest answer if the programme is willing to stop trading the auction:
plausibly 4–7 bp/side more.** But that is not a cost-model correction; it is a
new execution regime whose fills are not the open or the close, and it must be
pre-registered and re-run, not applied as a multiplier to existing numbers.

**And the correction pointing the other way.** Ardia, Guidotti & Kroencke
(*JFE* 2024) [PEER-REVIEWED] show that Roll, **Corwin–Schultz** and Abdi–Ranaldo
all "underestimate the effective spread for small and less liquid stocks," that
the continuous-time assumption behind CS causes "a significant downward bias when
trading is infrequent," and that their EDGE estimator is on average **twice as
accurate** as the best available alternative across 1.6m stock-months, while
producing 10–50% fewer negative estimates (whose truncation to zero biases
spreads *up*). CS is therefore biased in *both* directions depending on segment:
**downward on the illiquid cheap tail** (where this programme's edge is), upward
on tick-tight large caps whose true spread is tiny. **The programme's spread
input is more likely too low than too high on the names that matter.** EDGE is a
closed-form OHLC drop-in with a maintained Python package (`bidask`, PyPI) — the
same inputs the current model already has. Recomputing D285's 33.8 bp
Corwin–Schultz figure under EDGE is a half-day of work and is the *first* thing
to do, because it determines the sign of everything in §9.

**Bottom line: yes, the honest answer is "very little" — for the strategy as
executed. The cost model is not the thing that is wrong.**

---

## 9. What this implies for the programme's existing numbers

Three recorded verdicts are worth re-examining. None flips on this evidence
alone; two become **UNRESOLVED** pending one recomputation each.

**(a) The 11.36 bp breakeven vs the 15 bp floor and the 33.8 bp measured spread
(D285).** Two opposing corrections.
- *Toward the strategy:* the 15 bp assumption was a guess; a SmartRouted
  continuous marketable order pays ~0.62 of the quoted half-spread. On a 33.8 bp
  quoted spread that is 0.62 × 16.9 = **10.5 bp/side — below the 11.36 bp
  breakeven.**
- *Against:* 33.8 bp was measured with Corwin–Schultz, which AGK show is biased
  **down** for exactly this kind of name; and the 0.62 was measured on
  *continuous market orders*, which is not how D285 filled.
- **Disposition: UNRESOLVED.** The recomputation that settles it is
  EDGE-vs-Corwin–Schultz on the held names, and then the same breakeven under an
  explicit continuous-execution assumption. Do not amend the record until both
  are computed.

**(b) The intraday cell losing 15.84%/yr with 1.92 bp/side commission against a
1.06 bp breakeven.** 1.92 bp/side is precisely `0.005 / 25.9` — a ~$26 stock at
Fixed pricing with ≥200 shares. Under Tiered on a NYSE-listed auction it becomes
0.0047/25.9 = **1.81 bp — still above the 1.06 bp breakeven.** Only a
rebate-earning passive fill (0.0005/share = 0.19 bp) clears it, and passive fills
are precisely what a cell needing immediacy cannot rely on.
**Disposition: verdict stands. Tiered does not rescue it.**

**(c) Gross +219.8 bp/trade against a 216.6 bp round trip on the widest two
deciles.** A 216.6 bp round trip is ~108 bp/side — overwhelmingly spread, not
commission, so no pricing-scheme change touches it. At E/Q 0.62 the round trip
would fall to ~134 bp against +219.8 bp gross, which **is** a different verdict.
But (i) the 0.62 was measured at a $20 median price on a 25 bp median spread —
the widest two deciles are a different animal and the E/Q there is
**[UNVERIFIED]** and plausibly worse; (ii) CS understates spreads most severely
in exactly that tail, so 216.6 bp may itself be too low; (iii) the whole
adjustment requires continuous execution rather than the auction.
**Disposition: UNRESOLVED, and the single highest-value re-test in this
report** — but it is a re-test, not a re-costing.

**Two things that require no re-test and should just be done.**
1. **Switch the commission model from Fixed to Tiered, and encode the minimum as
   a share count (200 / 100), not a notional.** The cost model currently uses one
   scheme; the arithmetic in §2–§3 is fully published and deterministic.
2. **Encode the auction fee tier separately from the continuous take fee.** They
   differ by 0.0014–0.0024/share and the programme is an auction-only strategy —
   this is the only place its execution style is *cheaper* than the default
   assumption, and Fixed pricing hides the difference entirely.

**One thing to diarise.** IBKR's first amended-Rule-605 report, covering
**August 2026**, is due published **before the end of September 2026**, with
effective/quoted spread by order-size bucket and an S&P 500 / non-S&P 500 split.
That replaces every estimate in §4 with IBKR's own measured number for its own
flow. It is free and it is weeks away.

---

## 10. Sources

**[PRIMARY REGULATORY]**
- SEC, *SEC Adopts Amendments to Enhance Disclosure of Order Execution
  Information* (Rule 605), 6 Mar 2024 — <https://www.sec.gov/newsroom/press-releases/2024-32>
- SEC final rule 34-99679, *Disclosure of Order Execution Information* —
  <https://www.sec.gov/files/rules/final/2024/34-99679.pdf>
- SEC staff, *Frequently Asked Questions: Rule 605 of Regulation NMS*, dated
  1 Apr 2026; **compliance date 1 Aug 2026** —
  <https://www.sec.gov/rules-regulations/staff-guidance/trading-markets-frequently-asked-questions/frequently-asked-questions-rule-605-regulation-nms>
- SEC Federal Register, *Extension of Compliance Date for Disclosure of Order
  Execution Information*, 2 Oct 2025 —
  <https://www.federalregister.gov/documents/2025/10/02/2025-19316/extension-of-compliance-date-for-disclosure-of-order-execution-information>
- SEC fact sheet 34-101070, *Tick Sizes, Access Fees, and Transparency of Better
  Priced Orders* — <https://www.sec.gov/files/34-101070-fact-sheet.pdf>
- SEC final rule 34-101070 — <https://www.sec.gov/files/rules/final/2024/34-101070.pdf>
- SEC, *Tick Sizes — A Small Entity Compliance Guide* —
  <https://www.sec.gov/resources-small-businesses/small-business-compliance-guides/tick-sizes>
- SEC exemptive order 34-104172, 31 Oct 2025 (compliance → Nov 2026) —
  <https://www.sec.gov/files/rules/exorders/2025/34-104172.pdf> ; press release —
  <https://www.sec.gov/newsroom/press-releases/2025-130-sec-issues-exemptive-order-regarding-compliance-certain-rules-under-regulation-nms>
- Chairman Atkins, *Statement Regarding Minimum Pricing Increments and Access Fee
  Caps*, 11 Jun 2026 (compliance → **first business day of November 2027**) —
  <https://www.sec.gov/newsroom/speeches-statements/atkins-statement-minimum-pricing-increments-access-fee-caps-061126>
- Interactive Brokers, *Held NMS Stocks and Options Order Routing Public Report*
  (Rule 606a), Q2 2025 — PFOF terms for Lite (12% of the NBBO spread on
  marketable; $0.27/100 sh on non-marketable), and "**no payments … for
  executions resulting from On Open and On Close orders**" —
  <https://www.interactivebrokers.com/ibkr606Reports/IBKR_606a_2025_Q2.pdf>
- NYSE, *Opening and Closing Auctions Fact Sheet* (3:50 pm MOC/LOC cut-off) —
  <https://www.nyse.com/publicdocs/nyse/markets/nyse/NYSE_Opening_and_Closing_Auctions_Fact_Sheet.pdf>
- Nasdaq, *Closing Cross FAQ* (MOC 3:55, LOC 3:58, IO 4:00) —
  <https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf>

**[BROKER OFFICIAL DOC]** — all fetched 2026-09-09, no effective date published
- IBKR US stock commissions (Fixed/Tiered/Lite schedule, minimums, maximums,
  regulatory + clearing + pass-through fees, Lite auction 10% rule, modified-order
  rule) — <https://www.interactivebrokers.com/en/pricing/commissions-stocks.php>
- IBKR NYSE exchange fee pass-through —
  <https://www.interactivebrokers.com/en/accounts/fees/NYSEstkfee.php>
- IBKR NASDAQ/INET — <https://www.interactivebrokers.com/en/accounts/fees/INETstkfee.php>
- IBKR NYSE Arca — <https://www.interactivebrokers.com/en/accounts/fees/ARCAstkfee.php>
- IBKR IEX (0.0000 for retail orders; 0.0003 auction) —
  <https://www.interactivebrokers.com/en/accounts/fees/IEXstkfee.php>
- IBKR ATS fees and rebates —
  <https://www.interactivebrokers.com/en/accounts/fees/IBKRATSFees.php>
- IBKR *United States — Alternate Exchange Commissions* (API direct-routed
  0.0075/sh Fixed, no Tiered; FOX RIVER +0.0030/sh) —
  <https://www.interactivebrokers.com/en/accounts/fees/alternate-exchange-commissions.php>
- IBKR MidPrice order type —
  <https://www.interactivebrokers.com/docs/general/order-types/algorithmic-orders/ib-algorithms/midprice>
- IBKR Adaptive Algo —
  <https://www.interactivebrokers.com/en/trading/orders/adaptive-algo.php>
- IBKR Rule 605 report index —
  <https://www.interactivebrokers.com/en/general/about/IBKR-ATS-605-Reports.php>

**[PEER-REVIEWED]**
- Dyhrberg, Shkilko & Werner, *The Retail Execution Quality Landscape*, JFE 2025
  (Rule 605, Jan 2019–Mar 2022; E/Q 0.76 wholesalers vs 0.97 exchanges) —
  <https://www.sciencedirect.com/science/article/pii/S0304405X25000595> ;
  working paper PDF <https://afajof.org/management/viewp.php?n=13580>
- Schwarz, Barber, Huang, Jorion & Odean, *The "Actual Retail Price" of Equity
  Trades*, JF 80(5) 2025 (85,417 real orders; **IBKR Pro PI 18.8% ⇒ E/Q ≈ 0.62**;
  round-trip cost 7.0–46.2 bp across brokers) —
  <https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13467> ; working paper
  <https://microstructure.exchange/papers/Schwartz_et_al_,_2022_WP,_The_'Actual_Retail_Price'_of_Equity_Trades.pdf>
- Goyal, Jegadeesh & Wu, *Price Impact in Closing Auctions, Opening Auctions, and
  Continuous Markets*, JFQA 2026 (square-root impact 17.7 bp at 1% ADV vs 2.35 bp
  linear; opening auction dearest) —
  <https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/price-impact-in-closing-auctions-opening-auctions-and-continuous-markets-a-benchmark-for-cost-of-trading-on-anomalies/0F72910A79C5B42CF6E85F55164CE846>
  ; summary <https://jfqa.org/2026/01/08/price-impact-in-closing-auctions-opening-auctions-and-continuous-markets-a-benchmark-for-cost-of-trading-on-anomalies/>
- Bogousslavsky & Muravyev, *Who trades at the close?*, J. Financial Markets 66
  (2023) — <https://ideas.repec.org/a/eee/finmar/v66y2023ics1386418123000502.html>
- Ardia, Guidotti & Kroencke, *Efficient Estimation of Bid-Ask Spreads from Open,
  High, Low, and Close Prices*, JFE 2024 (EDGE; CS underestimates spreads for
  small/illiquid stocks) —
  <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3892335> ; code
  <https://github.com/eguidotti/bidask> (PyPI `bidask`)
- Battalio, Corwin & Jennings, *Can Brokers Have It All? On the Relation between
  Make-Take Fees and Limit Order Execution Quality*, JF 71(5) 2016 —
  <https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12422>
- Corwin & Schultz, *A Simple Way to Estimate Bid-Ask Spreads from Daily High and
  Low Prices*, JF 2012 (the estimator currently in use) —
  <https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2012.01729.x>

**[SALES INSTRUMENT]**
- IBKR, *Dedicated to Best Price Execution* — "total trading cost was 0.021% of
  trade value" for Aug 2026, benchmarked to **daily VWAP**, average trade size
  $22,288 — <https://www.interactivebrokers.com/en/trading/smart-routing.php>
- IBKR marketing / Transaction Auditing Group figures ("$0.31 vs industry $0.26
  price improvement per 100 shares") — cited in third-party broker reviews; not
  independently verified and inconsistent with the JF 2025 experiment.

**[UNVERIFIED]**
- Per-size-bucket auction impact figures attributed to Goyal–Jegadeesh–Wu (NYSE
  micro 18.2 bp, Nasdaq micro 44.7 bp at 1% ADV) — could not be confirmed against
  the paper text; only the pooled 17.7 bp figure is confirmed.
- Whether IBKR flags this account's orders as retail-designated, and whether IEX
  routing (0.0000 take fee) can be forced from the API.
- Any quantified price improvement for MidPrice, Pegged-to-Midpoint, D-Peg or the
  Adaptive Algo. IBKR publishes none.
- Current-year SEC Section 31 and FINRA TAF rates were taken from IBKR's page,
  not cross-checked against the SEC/FINRA fee-rate advisories.
