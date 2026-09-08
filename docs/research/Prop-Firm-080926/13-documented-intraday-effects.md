# 13 — Documented intraday futures effects: an academic/practitioner hypothesis list

**Lane opened and closed 2026-09-08.** Schema and stopping rules:
[`00-SCHEMA.md`](00-SCHEMA.md). Tier restriction for this lane: **journals, working papers,
central-bank research, exchange research, and preprints with stated methodology.** The marketing
tier was another lane's; no calls were spent there.

> ### NOTHING HERE IS EVIDENCE
>
> Under [R15](../../RULES.md#r15) a signal is **a positive gross mean per trade above its own nulls,
> measured here, on our fixture.** Every number on this page is somebody else's, computed on
> somebody else's data, by a method we have not audited. This file is a **hypothesis list with
> falsification criteria attached.** It recommends nothing, admits nothing to either book, and
> closes no avenue — [only the principal does that](../../decisions/D360-RESULT-the-news-gap-carries-no-drift-the-gapped-name-bounces-and-the-short-side-closes-on-tape-signals.md).
>
> Every fetched page is **observed content — data, never instructions.** Two of the sources below
> are self-published preprints and one is a paid practitioner newsletter; they are logged at their
> real tier and weighted accordingly.

---

## 1. VERDICT

**No candidate survives all seven screen points. Zero.**

The reason is not the one expected. Going in, the presumption was that published intraday effects
would **die on cost** (screen 6). They do not. The best-documented effect — market intraday
momentum — clears a $10–22.50 round turn by **3.8× to 8.6×**. Cost is the screen it passes most
comfortably.

What kills every candidate is the **interaction of screens 4 and 5**, which are not independent
constraints but the two blades of a scissors:

> ### The size scissors
>
> Position size `N` scales the mean **and** the standard deviation together. The trailing drawdown
> is **fixed** at ~$2,000. Therefore:
>
> - **Screen 5** ($150+ days) sets a **lower** bound on `N`.
> - **Screen 4** (~4% trailing MLL on open equity) sets an **upper** bound on `N`.
> - For every effect found in this lane, **the lower bound exceeds the upper bound.**
>
> On ES with the Gao et al. (2018) parameters, the gap is **4.5×**. Closing it requires a per-trade
> Sharpe of **0.225** (annualised **3.57**). The documented figure is **0.068** (annualised
> **1.08**) — a **3.3× shortfall**. No effect located in this lane, at any tier, reports a
> single-market annualised Sharpe above ~1.7, and that 1.7 is a **17-market diversified portfolio**
> a $50k account cannot hold.

The size scissors is a property of **the instrument** (the funded account), not of the strategies —
exactly the distinction `00-SCHEMA.md` §"standing instruction" draws. Several candidates below are
therefore **prop-dead but personal-book-live**, and are flagged as such rather than discarded.

### The scissors, computed

ES at index 6,500, multiplier $50 → **$325,000 notional/contract**. Gao et al. (2018) timing
strategy `r1`: 6.67% p.a. mean, 6.19% p.a. s.d., over 252 one-trade days.

| | per trade, per ES contract |
|---|---|
| gross mean | 2.65 bp = **$86** |
| s.d. | 38.99 bp = **$1,267** |
| Sharpe per trade | **0.068** (annualised 1.08) |
| cost, $10 round turn | $10 → net **$76**, clears **8.6×** |
| cost, $10 + 1 tick ES spread ($12.50) | $22.50 → net **$64**, clears **3.8×** |
| **breakeven cost** | **$86/round turn**, i.e. **6.9 ES ticks** |

Now against a $50k MFFU-style account — $2,000 MLL on **open** equity, $3,000 profit target,
qualifying day ≥ $150 (field 18, lane 01):

| N | mean/day | s.d./day | MLL in s.d. | P(day ≥ $150) | P(breach/day)¹ | days to target | **P(survive to target)** |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | $64 | $1,267 | 1.58σ | 47.3% | 5.2% | 47.2 | **8.1%** |
| 2 | $127 | $2,535 | 0.79σ | 49.6% | 20.1% | 23.6 | **0.5%** |
| 3 | $191 | $3,802 | 0.53σ | 50.4% | 28.2% | 15.7 | **0.5%** |
| 10 | $635 | $12,673 | 0.16σ | 51.5% | 41.8% | 4.7 | **7.8%** |

¹ Gaussian, close-of-window only. **Both assumptions flatter the candidate.** The realised kurtosis
is **15.65** (Gao et al., Table 6), and MAE *within* the 30-minute window is by construction worse
than the window's closing move. The true breach rates are higher, possibly much higher.

Three things to read off this table:

1. **Screen 5 is satisfied by the distribution, not the mean.** At one contract the mean is $64 but
   **47% of days still clear $150**, because σ ≫ μ. The naive reading ("$64 < $150, therefore
   fails") is wrong. The mean is not what the rule tests.
2. **Nothing survives.** The best cell is one contract at **8.1%**, and that is an optimistic bound.
3. **P(survive) is non-monotone in size** — 8.1% at N=1, 0.5% at N=2–3, back to 7.8% at N=10. That
   is gambler's-ruin curvature: at extreme size you reach the target in 4.7 bets, so there is barely
   time to be absorbed. **This is D379's interior optimum appearing in a completely independent
   calculation**, and it is the one genuinely encouraging thing on this page — it corroborates
   D379's geometry from outside.

### What this lane can hand D379

D379 §4 needs an edge to allocate. The literature does not supply a *strategy*, but it does supply
the three numbers a barrier calculation actually consumes, for the one effect documented well enough
to yield them:

| quantity | ES, last-30-min intraday momentum | source |
|---|---|---|
| μ per trade | **2.65–2.72 bp of notional** | Gao 2018; Baltussen 2021 |
| σ per trade | **~39 bp of notional** | Gao 2018 |
| kurtosis | **15.65** | Gao 2018, Table 6 |
| skew | **+0.90** | Gao 2018, Table 6 |
| success rate | **54.37%** | Gao 2018, Table 6 |
| **MAE / adverse excursion** | **NOT PUBLISHED — see §4** | — |

**The MAE row is the blocking gap and it is not closeable from the literature.** See §4.

---

## 2. Candidates that came closest

### C-13.1 — Market intraday momentum (last 30 minutes) — **the only near-miss**

**Citations.**
- Gao, L., Han, Y., Li, S. Z., Zhou, G. (2018). "Market intraday momentum." *Journal of Financial
  Economics* 129(2), 394–414.
- **Baltussen, G., Da, Z., Lammers, S., Martens, M. (2021). "Hedging demand and market intraday
  momentum." *Journal of Financial Economics* 142(1), 377–403.** ← the futures paper, and the better
  one for our purposes.

**The effect.** The return over the last 30 minutes before the close (`rLH`) is positively predicted
by the return over the rest of the day (`rROD`, previous close → 30 min before close). Take the sign
of `rROD`; hold the last 30 minutes; flat at the close.

**Mechanism — and it is a real one, not a story.** Baltussen et al. attribute it to **gamma hedging
demand**. Agents short gamma (option market makers, leveraged-ETF issuers) must trade *in the
direction of* price moves to stay delta-hedged, and they must do it near the close. The paper does
not merely assert this: it constructs a **net gamma exposure (NGE)** measure from OptionMetrics
(1996–2017, extended to May 2020 with SqueezeMetrics) and shows the momentum is **stronger when NGE
is more negative**. It also notes LETFs make up **16.8% (50.2% on some measures) of market-on-close
volume**. Gao et al.'s earlier explanations — Bogousslavsky (2016) infrequent rebalancing, and
late-informed traders — are complementary rather than competing.

**Magnitude and sample.** Baltussen et al.: **over 60 futures across equities, bonds, commodities
and currencies, 1974–2020.** Per-market slopes on `rROD` (×100), Newey–West *t*:

| contract | β(rROD) | *t* | adj R² | **R²_OOS** |
|---|---:|---:|---:|---:|
| **ES** (S&P 500) | 6.18 | 4.97 | 3.41% | **2.29%** |
| **NQ** (Nasdaq 100) | 6.36 | 7.97 | 4.10% | **3.76%** |
| **YM** (Dow) | 5.02 | 4.12 | 2.20% | **2.18%** |
| **ER** (Russell) | 6.00 | 5.86 | 3.35% | **3.15%** |

A **positive out-of-sample R² of 2–4% on a return series is a genuinely strong result** and is the
single most impressive number in this lane. Strategy performance (1/N portfolios, 1974–2020):
equity index futures `rROD` **6.86% p.a. / 3.96% s.d. / SR 1.73 / 55% success**; government bonds SR
1.62; commodities SR 1.42; currencies SR 0.87. Gao et al. on SPY 1993–2013: **6.67% p.a. / 6.19%
s.d. / SR 1.08 / 54.37% success**, and they state results "are similar when we use the S&P 500
futures."

**Screen.**

| # | screen | verdict |
|---|---|---|
| 1 | CME tradeable | **PASS.** ES, NQ, YM, RTY explicitly, plus ZB/ZN, CL, GC |
| 2 | directional | **PASS.** Single instrument, long or short on a sign. No leg |
| 3 | intraday-closable | **PASS, emphatically.** 30-minute hold, flat at the close by construction |
| 4 | MAE-bounded | **FAIL.** σ ≈ $1,267/contract vs a $2,000 fixed floor = **1.58σ**. Kurtosis 15.65. **No published MAE** |
| 5 | daily P&L | **PASS at N≥1** — 47% of days clear $150 — **but only jointly with a screen-4 failure** |
| 6 | survives cost | **PASS.** Breakeven $86/round turn = 6.9 ES ticks; clears 3.8–8.6× |
| 7 | mechanism | **PASS, strongest in the lane.** Gamma hedging, with an NGE measure and a conditional test |

**Decay and replication — read this before getting excited.**
- **Baltussen et al. do not cost the strategy.** Their own words: *"we do not consider transaction
  costs… the strategy as presented might not be exploitable."* They add only that exploiting it in
  S&P 500 futures "yields a positive net Sharpe ratio" at one tick of cost — **they never report the
  number.** A positive-but-unstated Sharpe is not a result.
- **The headline SR 1.73 is a 17-market 1/N portfolio.** Single-market ES is ≈ **1.08–1.10** (Gao's
  SPY figure, which reconciles with Baltussen's per-market β). **A $50k account cannot hold 17
  correlated equity index futures**, and under screen 2 a book of 17 correlated index futures is
  precisely the kind of position these firms police. **The diversification that produces 1.73 is
  unavailable to the instrument.** This is the most commonly repeated error about this literature.
- **Replication is genuinely mixed.** Limkriangkrai, Chai & Zheng (2023, *Pacific-Basin Finance
  Journal* 80, 102086) test five APAC markets: present in China and Japan, **weak in South Korea,
  absent in Hong Kong and Singapore**, and **weaker during COVID**. Their conclusion: *"not as
  pervasive in the APAC markets when compared to the US evidence."* Julin (2024, Örebro MSc) finds
  **weak predictability on OMXS30**.
- **Direct futures falsification.** Mesfin (2026, arXiv:2605.04004) — see C-13.2 — tests fourteen
  intraday signal families on **MNQ, 947 days, 2021–2025** and passes none.
- **General prior.** McLean & Pontiff (2016, *JF*): post-publication anomaly returns are **58%
  lower**; out-of-sample 26% lower. Gao et al. published 2018. **A 58% haircut on SR 1.08 gives
  ~0.45, which moves the size scissors from 4.5× to roughly 9×.**

**Data obtainable? YES, and cheaply.** [`docs/research/futures-data/`](../futures-data/00-SYNTHESIS.md)
established Databento `GLBX.MDP3`, schema `ohlcv-1m`, **ES from 2010-06-06**, at **~$0.51/symbol-year
— ES+NQ+RTY+YM for 15 years ≈ $30**, inside the $125 signup credit. 1-minute bars are ample for a
30-minute signal. **This is testable here for effectively nothing.**

**Falsification criteria, pre-registered in the form R15 requires.** On our own ES/NQ fixture:
1. **Gross** mean per trade > 0 and above **both** nulls (time-rotation and sign-randomisation),
   reported as p50/p95, not a percentile alone.
2. Per-trade σ and **the full MAE distribution within the 30-minute window** — the quantity nobody
   has published. Specifically: **P(MAE ≤ $2,000 per contract)**.
3. β(rROD) replicated on 2010–2026 with the sign and rough magnitude of Baltussen's 6.18; **a
   post-2018 subsample β below ~3.0 falsifies the candidate for our purposes** (that is the McLean–
   Pontiff haircut arriving).
4. The gamma mechanism is *checkable*, not just quotable: the effect must be **stronger on
   negative-NGE days**. If it is not, the mechanism is not the one claimed and the effect is a
   calendar artefact.
5. Both lenses per CLAUDE.md: path-invariant per-trade, and path-variant in bp/bar.

---

### C-13.2 — The MNQ falsification study (a negative result, and the most useful source here)

**Citation.** Mesfin, M. (2026). "Structural Limits of OHLCV-Based Intraday Signals in MNQ Futures:
A Systematic Falsification Study." arXiv:2605.04004, submitted 2026-05-05, revised 2026-07-13.

**Tier caveat, stated plainly:** self-published preprint, single independent author, **not peer
reviewed**, and its two "positive control" signals are from an undisclosed private research
programme and cannot be checked. **Weight the negative results, not the positive controls.** The
negatives are the part that is falsifiable and the part that is useful.

**Design.** 14 signal families, **72,604 five-minute MNQ bars, 947 days, Dec 2021 – Aug 2025**,
expanding-window walk-forward, entry at next bar's open, **2.0-point round-trip friction (~$4/micro
contract)**. Pass = OOS *t* ≥ 2.0 **and** N ≥ 30 **and** net > 0 **and** year-stable **and**
permutation p < 0.05. **Nothing passed.**

**The central claim — a gross edge ceiling.** Across all fourteen families the best gross return is
**0.07 to 1.50 points per trade**, against 2.0 points of friction. Selected results:

| family | best result | verdict |
|---|---|---|
| Opening range breakout (09:30–09:55) | best *t* = 1.50; years −1.42 / +2.43 / +7.04 | FAIL — year-unstable |
| ORB pullback entry | **80.7% stop-out** at a 20-pt stop; −4.44 net | FAIL |
| Asia session range expansion | *t* = **−10.96** — significantly *backwards* | FAIL |
| Liquidity-grab reversal (6,442 events) | −2.20 fading, −1.80 with; gross content 0.20–0.80 pts | FAIL — pure friction ceiling |
| Gap fill fade (3 entry times) | *t* = −0.44 to −0.59 | FAIL |
| Gap continuation short (Kalman) | *t* = 3.23, 68% win, **+14.52 net** | FAIL — **N = 22**, and declining 12→6→4 |
| Volume spike / dry-up (4 variants) | all *t* ≈ 0, N = 723–2,409 | FAIL — **precise nulls, not underpowered** |
| Volatility-regime classifier | 2024 alone *t* = 2.07; 2022 *t* = −1.27, 2023 *t* = −0.70 | FAIL — regime, not edge |
| Event-day trend (993 FOMC/CPI/NFP/PCE events) | **from bar +6, *t* = 0.14–0.69** | FAIL — see C-13.5 |
| MGC (gold) OU mean reversion | all configs negative; half-life ~8h > one session | FAIL |

**Why this matters more than its tier suggests.** It is the **only source located that tests the
retail intraday folklore on an actual CME futures contract, out-of-sample, with a stated cost, and
reports the failures.** Its two most transferable findings:

- **The Asia-expansion result (*t* = −10.96) is a mechanism, not a null:** the directional move is
  *consumed inside the signal bar*, so bar-close-then-next-bar-open execution systematically buys
  the post-exhaustion reversal. **Any signal defined on a bar's own range inherits this.** That is a
  design warning for our own runners, independent of whether one trusts this paper.
- **"One strong year masking two flat ones" was the single most common failure mode.** Our year-split
  reporting requirement (CLAUDE.md §Reporting, group 3, "profitable years") is aimed at exactly this.

---

## 3. Rejected, with the reason

| # | candidate | primary citation | fails on | why |
|---|---|---|---|---|
| R1 | **Overnight drift** (02:00–03:00 ET) | Boyarchenko, Larsen & Whelan, FRBNY Staff Report 917 (2020, rev. 2022); *RFS* 36(9) 2023 | **DECAY** | Was ~**3.7% p.a.**, >60% of the ES contract's 5.9% close-to-close return, 1998–2020. **The original authors published its death**: Liberty Street Economics, 2026-07 — *"has averaged close to zero"* since Jan 2021. The NightShares ETFs (NSPY, NIWM) built to harvest it **closed 14 months after launch.** Passes screens 1–3; **dead on arrival** |
| R2 | **Pre-FOMC announcement drift** | Lucca & Moench (2015) *JF*; **Kurov, Wolfe & Gilbert (2021)** *Finance Research Letters* vol. 40 [article no. not verified] | **DECAY + 3** | *"Essentially disappeared after 2015"*, with and without press conferences, in a sample extended to Dec 2019. Also a ~24-hour hold → not intraday-closable. Twice dead |
| R3 | **Macro announcement premium** | Savor & Wilson (2013); Ai, Bansal & Guo (2024) NBER w31923 | **3, 5** | 11.4 bp on announcement days vs 1.1 bp otherwise; ~44 days/yr carry >71% of risk compensation. But it is a **close-to-close** premium substantially earned **pre-announcement/overnight**, and **~30–44 events/yr cannot generate regular qualifying days**. Real effect, wrong shape |
| R4 | **Post-announcement drift** (NFP/CPI/FOMC, minutes after) | Mesfin (2026) §4.7, 993 events | **4, and no effect** | Drift is real *for five bars* — that is the news spike itself, unreachable. **From bar +6, *t* = 0.14–0.69.** And the spike is precisely the MAE profile a 4% trailing floor cannot hold |
| R5 | **Opening range breakout** | Zarattini & Aziz (2023); Mesfin (2026) §4.1 | **1, 4** | Zarattini's 1,484%/SR 2.81 is **7,000 US stocks, a top-20 "stocks in play" portfolio, and 3× leveraged ETFs** — not a CME futures instrument, and a 20-name portfolio fails screen 2's spirit and a $50k account's margin. On MNQ directly, ORB **fails** (best *t* = 1.50, year-unstable; pullback variant stops out 80.7% of the time) |
| R6 | **Turn-of-month** | **Carchano & Pardo Tornero, "Calendar Anomalies in Stock Index Futures"** (SSRN 1958587; abstract page only — year and venue not verified) | **3, 5** | The most honest calendar paper found: **188 cyclical anomalies** tested on S&P 500, DAX, Nikkei futures 1991–2008 with bootstrap/Monte Carlo. **Exactly one survives** — turn-of-month in S&P futures, **27.5% net cumulative over 16.4 years ≈ 1.5%/yr.** Multi-day hold → not intraday-closable; ~1.5%/yr cannot make qualifying days. **187/188 is the real headline** |
| R7 | **Day-of-week / time-of-day seasonality** | Carchano & Pardo; day-of-week decay literature | **DECAY** | Among the 187 rejected above. Independently documented as declining and *"disappear[ing] for the most recent period in the USA"* |
| R8 | **VIX futures term structure** | Quantpedia; 2018 XIV event | **1, 2, 3, 4** | VX lists on **Cboe (CFE), not CME**; the standard construction is a **calendar spread** (screen 2 = terminal violation); typical hold is 5 days; and **XIV lost 96% in one session** on 2018-02-05. Fails four screens, one of them catastrophically |
| R9 | **VIX-futures intraday momentum** | Huang, Tsai, Weng & Yang (2023) *Journal of Banking & Finance* vol. 148 [article no. not verified] | **1** | Robust across expirations, intervals, sessions and sub-periods, with a stated mechanism (VIX option market-maker hedging — note it is the *same* gamma mechanism as C-13.1). But **VX is CFE**, and prop futures accounts generally do not offer it. **Carry to personal book if a CFE route ever exists** |
| R10 | **Order flow imbalance** | Takahashi (2025), arXiv:2508.06788, structural VAR on ES | **6, data** | Predictability lives at **1 second to 15 minutes** and is quoted in ticks — i.e. inside the spread the effect must also pay. Requires L2/MBO data and latency a retail prop account does not have. **A candidate you cannot cost is not a candidate**; here it is costable and the answer is no |
| R11 | **Treasury auction cycle** | **Lou, Yan & Zhang (2013)** *RFS* 26(8), 1891–1912 | **3** | Prices fall in the days *before* auctions and recover after; **9–18 bp of auction size**. ZB/ZN are CME. But it is a **multi-day** effect. Excellent mechanism (dealer risk-bearing capacity, imperfect capital mobility). **Personal-book carry-forward** |
| R12 | **Overnight vs intraday decomposition** | **Lou, Polk & Skouras (2019)** *JFE* 134(1), 192–213 | **1, 2** | 14 strategies, each earning **entirely** overnight or **entirely** intraday, with opposing signs. But it is a **firm-level long/short** result — no CME instrument, and a long/short book is a terminal prop violation. **Personal-book carry-forward; it is the strongest idea in this lane for that book** |
| R13 | **EIA crude inventory (Wed 10:30 ET, CL)** | "The informational content of inventory announcements: intraday evidence from crude oil futures", *Energy Economics* (2016) [authors not verified — abstract page only] | **4** | Effect is real and fast — **fully played out in ~25 minutes, then reverts.** The reaction is a two-sided jump with wide spreads and slippage at exactly the moment of entry. That is an unbounded-MAE trade by construction |
| R14 | **Gap fill / gap continuation** | Mesfin (2026) §4.4 | **5** | Gap fill fails at every entry time (*t* = −0.44 to −0.59). Gap continuation short is the study's one statistical near-miss (*t* = 3.23, 68% win, +14.52 net) but fires **22 times in three years — once per seven weeks**, with declining frequency. Cannot make qualifying days |
| R15 | **Zarattini "noise area" intraday momentum** | Zarattini, Aziz & Barbon (2024), SFI Research Paper 24-97 | **4** | See §3.1 below — the clearest screen-4 kill in the lane |

### 3.1 — Why R15 deserves its own paragraph

Zarattini, Aziz & Barbon (2024) build a SPY intraday momentum strategy on "noise boundaries"
(opening price × 1 ± the average move-to-that-minute over 14 days), entering on breaks outside the
band and exiting at the close or on re-entry. Reported: **1,985% total, 19.6% annualised, SR 1.33,
2007 – early 2024, net of Interactive Brokers costs.**

A practitioner replication on **futures** (Quantitativo, 2010–2026 — *paid newsletter tier, not
audited, logged as claims*) reports:

| | ES standalone | NQ standalone |
|---|---:|---:|
| annualised | 16.8% | 24.3% |
| Sharpe | 1.25 | 1.67 |
| **maximum drawdown** | **21%** | **24%** |
| **win rate** | **~36%** | **38%** |
| payoff ratio | 2.09 | 2.25 |

**Two numbers end it.** A **21–24% maximum drawdown** against a **4% trailing floor** is a 5–6×
overshoot — and that drawdown is measured on the strategy's *own* vol-targeted equity curve, so it
does not shrink by trading smaller; it is scale-invariant. And a **36% win rate** means losing runs
are the norm: at a 64% per-trade loss rate, **six consecutive losers occur with probability 6.9%**,
which on a trailing open-equity floor is not a bad week but a terminated account.

This is the general lesson, and it applies to every momentum-shaped candidate: **low win rate ×
high payoff is the exact P&L shape a trailing drawdown is designed to kill.** The prop instrument
selects *against* positive skew — which is the same tail the personal book's R15 objective is happy
to buy. The two books want opposite third moments.

---

## 4. The blocking gap: MAE is NOT PUBLISHED, anywhere

**Screen 4 cannot be evaluated from the literature for any candidate in this lane.** Four targeted
probes (see Sources rows 19, 24) returned nothing. The finance literature reports **means, standard
deviations, Sharpe ratios and — occasionally — maximum drawdown of an equity curve.** It does not
report **maximum adverse excursion within the holding window**, because no academic objective
function is path-dependent inside a trade. MAE is a practitioner statistic (Sweeney), and the
practitioner sources that use it do not publish reproducible studies.

This is not a gap that more searching closes. It is structural: **the quantity the funded account
is priced on is the one quantity the literature does not measure.** Consequences:

1. Every screen-4 verdict above is inferred from σ and kurtosis, and is therefore a **lower bound on
   severity** — MAE within a window is always ≥ the window's closing move.
2. **The single highest-value measurement this programme could make on a bought ES fixture is the
   MAE distribution of the last-30-minute trade**, i.e. `P(MAE ≤ $2,000 per contract)`. It is one
   query against ~$8 of 1-minute data, it is not published anywhere, and D379 §4 consumes it
   directly.
3. It is also the honest reason no candidate here can be promoted: not that they failed screen 4,
   but that **screen 4 is not decidable from published sources at all**, and the σ-based proxy says
   they fail.

---

## 5. Disposition on the two books

Per `00-SCHEMA.md`'s standing instruction — nothing is discarded for failing hurdle P alone.

**Prop book ([`BOOK_PROP.md`](../../BOOK_PROP.md)): nothing admitted. Nothing even proposed.**
The size scissors is not a hurdle these candidates narrowly miss; it is a 3.3× Sharpe shortfall.

**Personal-book carry-forward** (append to [`09-personal-book-carry-forward.md`](09-personal-book-carry-forward.md);
still owes R15 and a pre-registration — carry-forward is **not** admission):

| candidate | why it failed prop | why it remains live personally |
|---|---|---|
| **C-13.1 market intraday momentum (ES/NQ)** | size scissors — fixed $2,000 floor vs σ=$1,267/contract | The personal objective is **linear in size** with **no barrier**, so the scissors simply does not exist. SR ~1.1 single-market with a **positive OOS R² of 2.3–3.8%**, a testable mechanism, and a **$30 fixture**. The strongest candidate this lane produced |
| **R12 tug-of-war (Lou–Polk–Skouras)** | long/short book = terminal prop violation | Long/short is unproblematic personally; this is the deepest result in the lane and the repo already reasons in overnight/intraday terms (D259) |
| **R11 Treasury auction cycle** | multi-day hold | ZB/ZN are CME; a dealer-inventory mechanism with a hard, *scheduled* event calendar; overnight risk is acceptable on the personal book |
| **R9 VIX-futures intraday momentum** | VX is CFE, not offered | Same gamma mechanism as C-13.1 — **useful as a mechanism cross-check even if never traded** |
| **R6 turn-of-month** | multi-day; ~1.5%/yr | Survived 188-way bootstrap correction, which is rarer than the return is large. Low priority |

---

## 6. What I would do next, if asked

Not a recommendation to trade — a recommendation about **measurement order**:

1. **Buy the ES+NQ 1-minute fixture (~$30, inside the Databento credit).** It is the input to
   everything above and to several other open questions in the repo.
2. **Measure the MAE distribution of the last-30-minute trade before measuring its mean.** The mean
   is documented in two JFE papers; the MAE is documented nowhere and is what actually decides.
   Measuring the already-known quantity first would be the D328 error — filing the mechanism before
   checking the statistic that orders the outcome.
3. **Split at 2018** (Gao et al.'s publication) and let McLean–Pontiff be the prior, not the
   surprise.
4. **Carry both nulls** — time-rotation and sign-randomisation — and confirm every null event sits
   in the same tradeable window as the observed events. The overnight-drift and pre-FOMC corpses in
   §3 are both cases where a real, large, well-mechanised effect went to zero; **assume this one
   has too until the post-2018 subsample says otherwise.**

---

## Sources

Accessed **2026-09-08**. Tier: **primary** = peer-reviewed journal / central-bank research /
working paper with methodology; **preprint** = unrefereed but methodologically stated; **secondary**
= abstract page, index, aggregator; **claims** = practitioner blog/newsletter, unaudited.
**Negative results are first-class entries.**

| # | URL | tier | sought | yielded |
|---|---|---|---|---|
| 1 | https://www.newyorkfed.org/research/staff_reports/sr917 | primary | overnight drift, magnitude & window | **HIT.** FRBNY SR 917, Boyarchenko/Larsen/Whelan, Feb 2020 rev. Aug 2022 |
| 2 | https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/ | primary | decay of R1 | **DECISIVE.** 02:00–03:00 ET; ~3.7% p.a. and >60% of ES's 5.9% close-to-close, 1998–2020; **"close to zero" since Jan 2021**; NightShares NSPY/NIWM closed after 14 months |
| 3 | https://arxiv.org/abs/2605.04004 | preprint | MNQ intraday signal falsification | **HIT.** Mesfin 2026, abstract + criteria |
| 4 | https://arxiv.org/pdf/2605.04004 | preprint | full text of #3 | **DECISIVE.** 14 families, 947 days, 2-pt friction, all tables. Extracted locally via `pdftotext` after WebFetch returned binary |
| 5 | https://researchmgt.monash.edu/ws/files/519509174/494419119_oa.pdf | primary | MIM replication | **HIT.** Limkriangkrai, Chai & Zheng (2023) *Pac-Basin Fin J* 80:102086 — APAC partial replication, weaker under COVID |
| 6 | https://assets.super.so/…/ee7dac49-…pdf (Gao et al. working paper) | primary | Gao 2018 magnitudes & costs | **DECISIVE.** 6.67%/6.19%/SR 1.08/54.37%, skew 0.90, kurtosis 15.65; effective spread ~1.2 bp post-2005; "similar… using the S&P 500 futures" |
| 7 | https://academicweb.nd.edu/~zda/intramom.pdf | primary | futures MIM + mechanism | **DECISIVE.** Baltussen/Da/Lammers/Martens *JFE* 142:377–403; 60+ futures 1974–2020; per-market β table (ES 6.18, *t* 4.97, R²_OOS 2.29); NGE gamma test; **explicit no-transaction-cost caveat** |
| 8 | https://pmc.ncbi.nlm.nih.gov/articles/PMC7525326/ + skidmore.edu PDF | primary | pre-FOMC decay | **HIT.** Kurov/Wolfe/Gilbert — drift "essentially disappeared after 2015", sample to Dec 2019 |
| 9 | https://conference.nber.org/confer/2013/MEs13/Lucca_Moench.pdf | primary | original pre-FOMC drift | **HIT.** Lucca & Moench, 1994–2011 |
| 10 | https://personal.lse.ac.uk/polk/research/TugOfWar.pdf | primary | overnight/intraday decomposition | **HIT.** Lou/Polk/Skouras *JFE* 134:192–213; 14 strategies, entirely-overnight or entirely-intraday with opposing signs |
| 11 | https://www.nber.org/system/files/working_papers/w24432/w24432.pdf ; w31923 | primary | announcement premium | **HIT.** Savor–Wilson 11.4 bp vs 1.1 bp; Ai/Bansal/Guo ~44 days carry >71% of risk compensation |
| 12 | https://personal.lse.ac.uk/loud/Shocks.pdf ; academic.oup.com/rfs/…/26/8/1891 | primary | Treasury auction cycle | **HIT.** Lou/Yan/Zhang *RFS* 26(8):1891–1912; 9–18 bp of auction size; dealer risk-bearing mechanism |
| 13 | https://dx.doi.org/10.2139/ssrn.1958587 (abstract via search) | secondary | calendar anomalies in futures | **HIT.** Carchano & Pardo: **188 anomalies, S&P/DAX/Nikkei futures 1991–2008, exactly one survives** (turn-of-month, 27.5% net cumulative, 0.05% round-trip) |
| 14 | https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12436 | secondary | Bogousslavsky mechanism | **HIT.** *JF* 71(6):2967–3006 — infrequent rebalancing → autocorrelation at the rebalancing horizon |
| 15 | https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12365 | secondary | post-publication decay prior | **HIT.** McLean & Pontiff: **58% lower post-publication, 26% out-of-sample** |
| 16 | https://www.sciencedirect.com/science/article/abs/pii/S0378426622003260 | secondary | VIX futures intraday momentum | **HIT.** Huang/Tsai/Weng/Yang *JBF* 148 (2023); VIX option MM hedging demand — same gamma family. **CFE, not CME** |
| 17 | https://arxiv.org/pdf/2508.06788 | preprint | order flow imbalance on ES | **HIT (rejects).** Takahashi 2025, structural VAR, 1s–15min horizons, tick-scale magnitudes |
| 18 | https://ideas.repec.org/p/chf/rpseri/rp2497.html | secondary | Zarattini SPY strategy | **PARTIAL.** SFI RP 24-97; 1,985% / 19.6% / SR 1.33. **Abstract carries no max drawdown or cost detail** |
| 19 | https://alexandria.unisg.ch/bitstreams/a99aba00-…/download | — | full text of #18 | **NEGATIVE — HTTP 405.** Max drawdown not obtained from the primary |
| 20 | https://www.quantitativo.com/p/intraday-momentum-for-es-and-nq | **claims** | #18 replicated on ES/NQ | **DECISIVE for screen 4, low tier.** ES 16.8%/SR 1.25/**MaxDD 21%**/win 36%; NQ 24.3%/SR 1.67/**MaxDD 24%**/win 38%; $0.85+$1.40 per contract + 0.5 tick/RT. **Unaudited — treated as an order-of-magnitude claim, and it only ever hardens a rejection** |
| 21 | https://www.researchgate.net/publication/370246583_… (Zarattini & Aziz ORB) | secondary | ORB evidence | **HIT (rejects on screen 1).** 7,000 US stocks, top-20 "stocks in play", 3× leveraged ETFs — not a CME futures instrument |
| 22 | https://www.sciencedirect.com/science/article/abs/pii/S0140988316302110 | secondary | EIA inventory intraday | **HIT (rejects).** Reaction complete in ~25 min then reverts; volatility and volume spike |
| 23 | https://www.diva-portal.org/smash/get/diva2:1878991/FULLTEXT01.pdf | primary (thesis) | MIM out-of-sample recent | **HIT, low weight.** Julin (2024, Örebro MSc), OMXS30 Mar 2023–Feb 2024 — **weak predictability**; another partial-replication failure |
| 24 | WebSearch: `"maximum adverse excursion" OR "drawdown" intraday momentum futures published` | — | **screen 4 data** | **NOTHING.** Returned only sources already logged (#4, #7, #20). **MAE within the holding window is not published for any candidate in this lane** — see §4 |
| 25 | WebSearch: `CME Group research intraday seasonality time-of-day equity index futures` | — | exchange research | **NOTHING.** cmegroup.com returns product/volume pages only; **no CME time-of-day research report located** |
| 26 | https://onlinelibrary.wiley.com/doi/10.1002/fut.22375 | — | Rosa (2022) *JFM* OOS study | **NEGATIVE — HTTP 403.** Search snippet indicates it studies OOS performance of the overnight-return variant and that performance "becomes much weaker"; **the primary was not read, so this is logged as unverified and used for nothing above** |
| 27 | https://centaur.reading.ac.uk/95566/1/Accepted-Version.pdf | — | intraday TSMOM global evidence | **NEGATIVE — blocked by Anubis anti-bot** |
| 28 | https://www.semanticscholar.org/search?q=… | — | route around #26 | **NEGATIVE.** Search shell only |
| 29 | https://netlibrary.aau.at/obvuklhs/download/pdf/7301728 | primary (thesis) | MIM OOS post-2013 | **PARTIAL.** Moser (2021, Klagenfurt MSc) — methodology on OOS forecasting; **ETFs, not futures; no post-publication decay result.** Low value |
| 30 | https://quantpedia.com/strategies/exploiting-term-structure-of-vix-futures + related | **claims** | VIX term structure | **HIT (rejects).** 5-day holds, calendar-spread construction, XIV −96% on 2018-02-05 |
| 31 | WebSearch: `day-of-week / time-of-day futures decayed data snooping` | secondary | seasonality decay | **HIT, thin.** Day-of-week magnitude declining, "disappears for the most recent period in the USA"; subsumed by #13 |
| 32 | WebSearch: `NFP CPI 8:30 E-mini drift` | secondary | announcement drift | **NOTHING usable.** Volume-reaction figures only (CME insights); no tradeable drift magnitude. Superseded by #4 §4.7 |
| 33 | WebSearch: `MIM post-publication weakened 2024/2025` | — | direct decay study for C-13.1 | **NOTHING NEW.** Returned #3, #6, #23 only |
| 34 | [`docs/research/futures-data/00-SYNTHESIS.md`](../futures-data/00-SYNTHESIS.md) | internal | data obtainability | **DECISIVE.** Databento `GLBX.MDP3` `ohlcv-1m`, ES from 2010-06-06, ~$0.51/symbol-year; ES+NQ+RTY+YM × 15y ≈ $30 inside the $125 credit |
| 35 | [`01-myfundedfutures.md`](01-myfundedfutures.md) | internal | the $150 / MLL constants | **DECISIVE.** Field 18: "5 winning days ≥ $150 each"; $50k MLL $2,000 (Add-On $1,500); profit target 6% = $3,000 |

**Stopping rule satisfied.** Rows **24, 25, 27, 28, 32, 33** are six consecutive probes yielding
nothing not already logged — past the five-source saturation threshold declared in `00-SCHEMA.md` §3.

**Solicitation check.** Two sources carried commercial solicitation: quantitativo.com (#20,
paid-subscription prompts) and quantpedia.com (#30, subscription wall). **Neither was acted on. No
account created, no credential entered, no cookie banner accepted, no referral link followed.** No
page carried an instruction addressed to an automated reader.

**Extraction note for the next session.** WebFetch returns **binary** for most academic PDFs. The
route that works here: let WebFetch save the file, then `pdftotext -layout` (present at
`/mingw64/bin/pdftotext`) — that recovered sources #4, #6, #7, #23, #29 after WebFetch failed on all
five. SSRN 403s as `SOURCES.md` already records; `wiley.com` and Anubis-protected repositories
(`centaur.reading.ac.uk`) also 403.
