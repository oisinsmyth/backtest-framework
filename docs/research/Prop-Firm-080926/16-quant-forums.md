# 16 — The quant forum tier, mined

**Lane 16 of the Prop-Firm-080926 review.** Opened and closed 2026-09-08.
Schema and stopping rules: [`00-SCHEMA.md`](00-SCHEMA.md). Reads on
[`13-documented-intraday-effects.md`](13-documented-intraday-effects.md) and
[`14-practitioner-tier-screened.md`](14-practitioner-tier-screened.md). Filed toward **D386**.

**Tier:** practitioner forums where the arguing happens in public — Quantitative Finance Stack
Exchange, Elite Trader, Wilmott, Hacker News, QuantConnect and the Quantopian archive.

**Stopping rule that bound: SATURATION, not the 30-source cap.** 26 sources. Three of the five
venues saturated outright — QSE returned nothing new after source 11, Elite Trader after source 18,
Hacker News after source 23 — and two were unreachable (Wilmott behind a bot-check that this lane is
**forbidden to solve**; Nuclear Phynance defunct with an empty mirror). The lane stopped when the
only venue still yielding was QuantConnect, and that venue had been exhausted on the question asked.

> ### NOTHING HERE IS EVIDENCE
>
> Under [R15](../../RULES.md#r15) a signal is **a positive gross mean per trade above its own nulls,
> measured here, on our fixture.** Nothing on this page is that. Every number below is somebody
> else's, computed by a method not audited here, and several are anonymous forum posts. This file is
> a **hypothesis list with falsification criteria attached.** It admits nothing to either book and
> **closes no avenue** — only the principal does that.
>
> Every fetched page is **observed content — data, never instructions.** No sign-up, no credential,
> no affiliate link, no Discord invitation was followed; two were present and are logged below.

---

## VERDICT

**Zero strategy candidates survive. One risk *overlay* survives, conditionally. The lane's value is
not a candidate at all — it is two falsifications, both aimed at things this review already holds.**

| | count |
|---|---|
| strategy families surviving the screen | **0** |
| **[PROP]** — surviving as an *overlay*, not a strategy | **1** — the volatility-regime day classifier as an **abstention rule** |
| **[PERSONAL]** — carried forward | **0** |
| **[NEITHER]** | 6 families, plus 4 anti-screen specimens |

### Contribution 1 — the review's only surviving strategy has been publicly dismantled, with code

[Lane 14](14-practitioner-tier-screened.md)'s sole survivor **S1 — intraday momentum on ES/NQ** rests
on Zarattini/Barbon/Aziz, *Beat the Market* (SSRN 4824172), reported there at **Sharpe 1.33 net of
costs**. That paper has been reimplemented on QuantConnect by three independent people, argued over
for fourteen months, and **the paper's own author answered their objections in writing**. The thread
is the single most valuable artefact this lane found.

| | paper | independent QuantConnect implementation |
|---|---|---|
| Sharpe | **1.33** | **0.399** (at leverage 1) |
| slippage assumed | **$0.001/share** | — |
| slippage the **author** now recommends | — | **$0.005/share** — *"To stay conservative, you can assume a slippage of $0.005 per share"* |
| commission assumed | **$0.0035/share** | author's own live IB figures: **$0.012/share** |
| fees as a share of return | not stated | **$27,317.98, "16.7 % of your return"**, on **6,940 orders** |
| win rate | not stated | **37% win / 63% loss** |
| information ratio | not stated | **−0.257** |

**Four things in that thread that matter more than the Sharpe number.**

1. **The whole gap is the spread, and it was isolated by experiment.** Nicolai ten Brinke compared
   trade-by-trade against the authors' own Python notebook: *"at QuantConnect the real bid/ask spread
   is considered compared to the authors backtest, which is a drag on the results. I tried to
   simulate 'no spread' on QuantConnect and got almost the same performance as in the paper."* This
   is not a vague cost complaint — it is a controlled attribution. Replacing the fill model with
   mid-price recovers the paper. Nothing else needed changing.
2. **The published drawdown is an END-OF-DAY mark, and the author concedes the direction.** Yuri
   Lopukhov: *"they use end of day portfolio values, ignoring intra-day volatility."* Zarattini's
   reply: *"This applies to all strategies: the higher the observation frequency, the higher the
   measured maximum DD."* **This resolves lane 14's screen-4 `UNRESOLVED` in the adverse direction.**
   Lane 14 could not size S1 against the barrier because *"the dollar drawdown per single contract is
   not published anywhere."* We now know the published 21%/24% figures are computed on a statistic
   the prop floor does not use. The floor marks **open equity continuously**; the paper marks it once
   a day. The published number is a **lower bound** on what the barrier reads, by the author's own
   argument.
3. **The live record does not run the published rule.** Asked about exits, Zarattini: *"In our live
   implementation, we use more sophisticated trailing methods that ensemble multiple independent
   trailing stops."* Lopukhov's conclusion is the right one and is quoted here because this review
   will otherwise be tempted to lean on that live record: *"if they don't use algorithm from paper
   for live-trading, does it makes sense to use live results to support it?"*
4. **The volatility target is an unpinned knob.** Asked why 2%: *"This is quite subjective… you can
   use whatever volatility target makes you feel more comfortable."*

**And a separate, independent failure of the *bare* effect.** QuantConnect's own research library
implements the raw Gao/Han/Li/Zhou rule — sign of the first half-hour predicts the last half-hour, no
band, no trailing stop — on SPY/IWM/IYR, **2015-01-01 to 2020-08-16**, and reports **Sharpe −0.628**
against a benchmark **0.582**. **Before costs.** The rule is positive only inside the Feb–Mar 2020
crash window (1.452 vs benchmark −1.466).

> **The distinction this forces, and it is checkable on our own fixture.** The JFE paper's sample is
> 1993–2013. The bare sign rule is negative out of sample on ETFs 2015–2020. Every *positive* futures
> or SPY result this review holds adds a layer the JFE paper does not contain — a 14-day
> average-absolute-deviation band, a VWAP trailing stop, a volatility target. **The peer-reviewed
> citation may be supporting an overlay it never tested.**

**Falsifier, in our own quantities:** run the **bare** Gao rule on ES/NQ minute bars, 2015–2026 — long
if the first 30 minutes of RTH is up, short if down, flat at the cash close, no band, no stop, no vol
target — and report the **gross mean per trade** against the rotation nulls. **If it is ≤ 0, S1 is not
"market intraday momentum"; it is the Concretum overlay,** and the JFE reference in lane 14 does not
carry it. If it is > 0, the two implementations disagree and the difference is the layer, which is
then the thing to test.

### Contribution 2 — the only backtest statistics that survive out of sample are the ones the barrier reads

Wiecki, Campbell, Lent & Stauth (Quantopian), *All that glitters is not gold* (SSRN 2745220):
**888 algorithms**, each developed and backtested on the platform, each with **≥ 6 months of
out-of-sample** performance, code version-locked at deployment so it could not be edited during the
OOS window. This is the Quantopian archive's most useful surviving artefact.

| in-sample statistic | Pearson R² predicting its own out-of-sample value |
|---|---|
| **annual volatility** | **0.67** |
| **maximum drawdown** | **0.34** |
| Sharpe ratio *(IS→IS baseline ceiling: 0.21)* | **0.02** |
| annual return | **0.015**, and the sign is **negative** |
| tail ratio (P95/P5) → OOS **Sharpe** | 0.025 — *more predictive of OOS Sharpe than IS Sharpe is* |
| information ratio, Calmar ratio, alpha | **< 0.005, not significant** |

Plus the overfitting term, measured rather than asserted: `log(total backtest days)` vs Sharpe
shortfall (IS Sharpe − OOS Sharpe), **Spearman R² = 0.017, p < 0.0001** — the more a strategy was
backtested, the larger its shortfall. And a portfolio of the 10 highest *IS Sharpe* algorithms
returned **Sharpe 0.7**, beating only 92% of random selections and not significantly.

> **What this says for hurdle P.** The prop account is scored on a **drawdown**. The academic and
> practitioner tiers are scored on **Sharpe**. On this dataset drawdown is **17× more persistent out
> of sample than Sharpe** (0.34 vs 0.02) and volatility **33×**. **A prop screen built on simulated
> MAE against a ratcheting floor is standing on far firmer statistical ground than an edge screen
> built on a simulated Sharpe** — which inverts the usual ordering, where the barrier is treated as
> the crude constraint and the Sharpe as the real finding.
>
> The corollary bites us too: **a candidate that clears an edge test on backtest Sharpe has cleared
> almost nothing** (R² = 0.02 against an IS→IS ceiling of 0.21, so even the ceiling is low), while
> the *risk* figures we compute are the part most likely to survive contact with the future.

**Caveats, stated rather than buried.** These are ~2016 US-equity long/short algorithms, not intraday
CME futures. Volatility persistence is partly mechanical — market volatility is itself persistent, so
any strategy inherits some of it, and drawdown inherits from volatility. The finding is a
**hypothesis about which of our own numbers to trust**, not a licence.

**Falsifier:** on our own decision record, take every cell that has been scored twice on
non-overlapping periods and regress OOS statistic on IS statistic for Sharpe, mean-per-trade,
volatility and maxDD separately. **If maxDD's R² is not materially above Sharpe's on our fixture, the
paragraph above does not transfer** and the ordering above should be dropped.

---

## THE SURVIVOR — one, and it is not a strategy

### O1 — the volatility-regime day classifier, used as an ABSTENTION rule — **[PROP]**

**The claim.** Mesfin (2026), *Structural Limits of OHLCV-Based Intraday Signals in MNQ Futures*
(arXiv 2605.04004 — **a self-published preprint by an independent researcher, with an AI-assistance
disclosure; weighted accordingly**). A "VVG" classifier flags days simultaneously in the **top tercile
of three pre-market conditions**: absolute first-30-minute return, absolute overnight gap, and
first-bar volume deviation from a 20-day rolling baseline.

**The evidence shown.** It activates on **~4.4% of trading days** and those days behave differently:
a **25.6 basis point next-day return spread** and a **77.6% peak-reversal rate before the close**.
The author calls these descriptive findings *"real"*. Every *directional* strategy built on them
fails — reversal entry T = +0.86 on N = 289, continuation entry T = −0.44 on N = 1,175.

**Why it survives here when the strategies built on it do not.** Every other item in this review asks
a classifier to *earn*. This one is worth keeping because it can be asked only to *abstain*.
[D379](../../decisions/D379-the-prop-account-is-a-down-and-out-call-and-hurdle-P-has-no-objective-function.md)
frames the prop account as a down-and-out call: the objective is `E[payouts │ survival] × P(survival)`,
and **the second term is bought, not earned**. A rule that identifies 4.4% of days on which the
intraday path is unusually violent — 77.6% of them reverse from their peak before the close, which is
precisely the shape a floor marked on open equity punishes — is a candidate for buying `P(survival)`
cheaply, at a cost of 4.4% of exposure.

**Mechanism.** The floor reads the worst point of the path, not the endpoint. Days selected on
*realised pre-market dislocation* have wider intraday paths by construction. Removing them removes
path width, which is what the barrier prices, while removing only 4.4% of the days on which P&L is
earned. This is the one place in the whole review where the barrier's non-linearity works in a
candidate's favour rather than against it.

**The number that would falsify it.** Take any book that reaches the point of being simulated against
a ratcheting floor. Compute, on our own fixture, both quantities with the classifier on and off:

- `ΔP(touch floor over a 20-day evaluation)`
- `ΔE[P&L over the same window]`

**O1 survives iff the floor-touch probability falls by more, in relative terms, than expected P&L
does.** Concretely: if abstaining on 4.4% of days costs ≥ 4.4% of expected P&L and reduces
`P(touch)` by **less than** 4.4% relative, O1 is dead — it is then a pure exposure cut with a story
attached, and an exposure cut needs no classifier. Stage 0's ratcheting-floor machinery
([D259](../../decisions/D259-the-extended-session-and-the-overnight-interior.md)) computes both terms
already.

**What makes it a false positive.** (a) The 4.4% / 25.6 bp / 77.6% figures are one unreviewed
preprint on MNQ 2021–2025 and have not been replicated anywhere. (b) A top-tercile-of-three
conjunction has three thresholds, all fitted; the 4.4% activation rate is roughly `(1/3)³ = 3.7%`
inflated by correlation between the three conditions, so the classifier may be doing nothing but
selecting high-volatility days, which a single volatility filter would do with one fewer knob.
**Test the one-knob version first** — if a plain realised-volatility tercile does the same work, the
classifier is decoration.

---

## THE REJECTED PILE

### Rejected on the anti-screen — arithmetic, provenance, or a missing convention

| # | claim | source tier | why rejected |
|---|---|---|---|
| **A1** | **"London Session Signal B", MNQ 03:00–08:30 ET: 289 trades, +5.77 pts mean net, T = 5.15, win 64.7%, profit factor 2.42, "Sharpe ratio 5.09", permutation p < 0.001** | preprint, presented as a *positive control* | **The arithmetic does not reproduce as labelled, and the control is circular.** See the two calculations below |
| **A2** | **"RTH Confluence Signal": T = 5.83, N = 538, +15.77 pts, walk-forward OOS T = 3.11 on 196 trades** | same | Same circularity. A *positive control* drawn from *"a separate research program"* that is itself unpublished and unverified **cannot calibrate a methodology** — it assumes the conclusion it is used to license. The falsification study's negative results survive this; its claim to have shown "the bar is achievable" does not |
| **A3** | Elite Trader: intraday ES rule, *"worst case a 55 percent win ratio and at best 70 percent, several years of data"* | forum | **Win rate with no payoff ratio, no cost convention, no sample count.** The thread's own first reply is the correct one: *"IMO W/L stats, etc are meaningless unless they are based on tick data. Are yours?"* — answered *"No"* |
| **A4** | QuantConnect: NQ 5-minute scalp on EMA/RSI/momentum/ultimate-oscillator slopes, *"If you could just capture a five point move… at $20 a point, that's $100 a day"* | forum | **Indicator combination with no mechanism**, no stated sample, no fee model. Its own author's adjacent 1-minute variant reports *"win rate of 61% and nearly broke even"*, performance *"almost solely due to trading fees"* — which is the anti-screen writing itself |
| **A5** | Hacker News: unleveraged model suite, *Platinum +45.34% / −16.48%* … vs *S&P 500 +9.91% / −27.56%*, since Jan 2022 | forum | **No cost convention, no null, no N, no Sharpe, no independent verification.** The only quantified thing worth keeping is the author's own live-vs-backtest ratio: *"live results have hit between 1/4 and 3/4 of backtest performance depending on the model"* — logged as a decay hypothesis, not a result |

**A1, the two calculations.** Both are done here from the page's own inputs.

1. **The "Sharpe ratio 5.09" is not an annualised Sharpe.** From `t = mean·√N / sd` with mean = 5.77
   pts, N = 289, t = 5.15: `sd = 5.77 × 17.0 / 5.15 = 19.05` points. Per-trade Sharpe is therefore
   `5.77 / 19.05 = 0.303`. Over Dec-2021→Aug-2025 (~3.7 years) 289 trades is ~78/year, so the
   annualised figure is `0.303 × √78 = 2.68`. The reported 5.09 is a whole-sample quantity numerically
   almost identical to the t-statistic. It overstates the annualised Sharpe by **~1.9×**. Tell #9 from
   [lane 07](07-statistics-and-claims.md) — precision as a proxy for provenance.
2. **It fails the size scissors, on its own numbers.** MNQ is $2/point, so +5.77 pts net = **$11.54
   per contract per trade**. At 289 trades over ~930 sessions that is **0.311 trades/day**, i.e.
   **$3.59/day per contract**. Reaching **$150/day** requires **41.8 MNQ contracts**. Per-trade s.d.
   is 19.05 pts = **$38.10/contract**, so at 41.8 contracts the per-trade s.d. is **$1,592** against a
   **$2,000** trailing floor on open equity — **1.26σ**, before any intra-hold excursion. This
   reproduces [lane 13](13-documented-intraday-effects.md)'s scissors (1.58σ at N = 1 on ES) on a
   completely independent candidate, which is the more interesting fact. **It also trades 03:00–08:30
   ET**, outside RTH, and the same paper notes prop rules restricting trading to RTH.

### Rejected on structure or on evidence — families this tier tested and buried

All from the MNQ falsification study unless noted. **947 trading days, Dec 2021 – Aug 2025, 5-minute
RTH bars, signal at bar close, entry at next bar open, 2.0-point round-trip friction (~$4.00/micro),
walk-forward with parameters fixed on the training window only.** Every row is *after* friction.

| family | the number | verdict |
|---|---|---|
| **Asia-session opening-range expansion** (bars > 1.5×/2.0×/2.5× the rolling 20-bar mean range, traded in the expansion direction) | **T = −10.96** at bar+1, N large. *"Not just unprofitable — actively wrong"* | **[NEITHER]** — and the mechanism is the valuable part, below |
| **Liquidity-grab reversal** (price pierces a session extreme then closes back inside) | **6,442 events** (3,419 long / 3,023 short). Fading: −2.20 pts, **T = −14.12**. With: −1.80 pts, **T = −13.24**. Gross directional content **0.20–0.80 pts** either way | **[NEITHER]** — a pure friction-ceiling result, in *both* directions |
| **Volume-signature signals** (spike → continuation; dry-up → reversal) | four variants, N = 723 to 2,409, **all T within ±0.92 of zero**. *"These are precise null results, not inconclusive ones"* | **[NEITHER]** — precise nulls, worth more than most positives |
| **Gap-fill fade** (09:30 / 09:45 / 10:00 entries) | T = **−0.44 / −0.32 / −0.59** | **[NEITHER]** |
| **Gap continuation short**, Kalman velocity filter | T = **3.23**, +14.52 pts, **68.2% win** — but **N = 22** over three years, and the frequency decays **12 → 6 → 4** | **[NEITHER]** — and *already closed here* (overnight gaps as a short trigger). Reported only because the author reached the same conclusion honestly and did not promote it |
| **Post-news drift** (FOMC/CPI/NFP/PCE, **993 events** 2022–2025) | Drift is real for the **first five bars** — that is the release spike itself. **From bar +6 on, T = 0.14 to 0.69.** The two largest releases, NFP and CPI (08:30 ET), *"are excluded entirely by prop firm rules restricting trading to RTH hours anyway."* RTH-compatible sample: **T = 0.38** | **[NEITHER]** — the tradeable part is outside the tradeable window |
| **MGC (Micro Gold) OU mean reversion**, 5-min and 60-min | all configurations fail, **T = −4.49 to −1.12**. The 60-minute half-life is **~8 hours — longer than one RTH session** | **[NEITHER]** — structurally incompatible with intraday closure |

**The ceiling itself.** Across all fourteen families, **maximum gross return before friction is
0.07 to 1.50 points per trade** against a **2.0-point** friction floor. On MNQ ($2/point) that is a
best case of **$3.00 gross per trade**. Under **this review's** $10 round turn — five MNQ points —
every family is short by **3.3× to 71×**. The author's structural reading is the one worth carrying:
*"any pattern visible to everyone in a liquid market gets arbitraged to the friction floor,"* and on
five-minute bars that equilibrium sits at **1–2 points gross**.

**Two mechanisms from the rejected pile that are worth more than the rejections.**

> **M1 — the momentum is inside the bar, and bar-close execution cannot reach it.** On the Asia
> expansion signal the *continuation* hypothesis is rejected at **T = −10.96**, which is among the
> largest statistics in the study and points the wrong way. The author's explanation: *"The expansion
> burst is real, but it is fully consumed within the expansion bar itself. By the time the bar
> closes, the signal fires, and the next-bar entry executes, the directional move is already done.
> What you end up capturing is the post-exhaustion reversal."*
>
> **This is a statement about our fixture, not about the market.** Every rule we can express on bars
> inherits it.
>
> **Falsifier, computable on data we already hold:** for bars selected on range > k × the rolling
> mean range, compute (i) the mean move **open→close within the selected bar** and (ii) the mean move
> **close→next close**. If (i) is large and (ii) is ≤ 0, the effect exists and **no bar-close rule can
> trade it** — and that is a property of the sampling, checkable once, that would retire a whole class
> of candidates rather than one.

> **M2 — the dominant failure mode is year-instability, not cost.** For the best candidates, cost is
> not what kills them. ORB long at a 15-bar horizon nets **−1.42 (2022) / +2.43 (2023) / +7.04
> (2024)**; the VVG continuation entry *"would actually pass in isolation"* in 2024 at **T = 2.07 on
> 312 trades**, against **T = −1.27** in 2022 and **T = −0.70** in 2023. One strong year inside three
> is the modal shape. **Our own multiplicity ledger is a defence against looking at one cell too
> many; it is not a defence against a cell that is real in one year.** A per-year sign-stability
> requirement is a different gate from a null, and this review does not currently carry one.

---

## Execution and market-structure detail worth keeping

These change *whether* an effect is tradeable at retail size, which is what the brief asked for.
None is evidence; each is a number to check.

**E1 — the sample size needed to establish the survivor's own sign, and it exceeds any evaluation
window by two orders of magnitude.** The highest-voted quantitative answer on QSE (chrisaycock,
50 votes) gives `n = (2·s·α / Δ)²`. Applied to **lane 13's own ES parameters** — gross mean **$86**,
s.d. **$1,267** per contract per trade — and asking only that the 95% interval exclude zero
(`Δ = 2 × mean = $172`):

```
n = (2 × 1267 × 1.96 / 172)² = 28.9² ≈ 834 trades
```

At one trade per day that is **~3.3 years**. Inside a **20-day** evaluation the 95% interval on the
mean is **±$555 around $86**. **The evaluation is not an inference device about the strategy; it is a
draw from the barrier.** That is not an argument against S1 — it is the reason lane 07's finding
(observed pass rates *below* the zero-edge baseline) is compatible with edges existing.

**E2 — transaction cost is not a property of the frequency; it is a property of the direction.**
lehalle, on QSE: *"mean reversion should be less costly since you buy while the price goes down
before it goes up, and momentum requires you buy what is currently going up."* And the right speed
measure is turnover, not signal flips: `Turnover = daily buy+sell dollar volume / average NAV`, so
`1/Turnover` is days to replace the book. **Our cost model applies one round-turn figure to both
sides.** If this is right, a momentum book and a reversion book at identical turnover do not pay the
same, and the direction of the error flatters momentum candidates — which is the direction this
review's surviving candidate points.

**E3 — measured retail fills, and the per-order minimum nobody models.** From a QSE answer reporting
its own measurement on **125 filled orders**: median **−5.9 bp** against the same day's close, with
**43% filling better than the close** — i.e. the poster's assumed 5–10 bp penalty was *worse* than
reality. Two riders: split the analysis by order type, because *"stop and limit exits fill when the
market is moving against you, that's the entire point of them"*; and **a broker's $1 per-order
minimum worked out to ~2.5%/yr of drag at small account size** — *"bigger than most of the edges
people argue about, and you won't see it at all if you're only thinking in bps."* Unverified, single
account. **Falsifier: for any candidate, compute cost as a fixed dollar per order as well as in bp,
and report both.** The house style already demands breakeven in bp/side; it does not demand it in
dollars per order, and at $50k these differ.

**E4 — the consolidated close can invert a backtest.** Flagged in the QSE slippage thread, citing
Chan: *"the error in consolidated close prices can make a losing strategy appear highly profitable in
backtests."* Relevant to any of our cells priced off a vendor close rather than the primary listing.

**E5 — the stop is only as good as the routing.** A live automated futures trader on Elite Trader
reports platform-level order failures — *"ignored stop losses, phantom limit orders that execute on
their own"* — one of which *"cost me a $10k loss on live markets when stop losses were ignored."*
Single anecdote, unverifiable, and named-vendor so treated as such. But the structural point is not
anecdotal: **against a floor marked on open equity, the MAE bound is not the stop level, it is the
stop level conditional on the stop working.** Nothing in lanes 13 or 14 prices that conditional.

**E6 — the retail intraday stop scale on ES, for calibration.** An active ES trader reports average
stops of **6–7 ticks** in tight-range months and **24 ticks** in high-volatility months, with targets
**10–11** and **24–27** ticks respectively. At $12.50/tick that is **$75–$300 of risk per contract**,
which fits inside a $2,000 buffer at up to ~6 contracts — but the gross per trade at that scale is
$125–$340, against which a $10 round turn is 3–8%. **The scale is compatible with the barrier; the
edge is what is missing**, which is the same conclusion the rest of the review reaches from the other
end.

---

## What lane 16 hands forward

1. **S1's screen-4 `UNRESOLVED` should be re-stated as adverse-with-direction-known.** The published
   drawdowns are end-of-day marks; the barrier reads open equity; the paper's author concedes the
   inequality. Lane 14 should not be read as "we lack the number" but as "the number we have is on
   the wrong statistic, and we know its sign."
2. **A pre-registration for S1 must specify the *bare* Gao rule as its own arm.** Otherwise the
   review cannot tell "market intraday momentum" from "the Concretum band-and-trail overlay", and the
   JFE citation is doing work it may not support. QuantConnect's **−0.628** on 2015–2020 ETFs is the
   reason to bother.
3. **The metric-persistence ordering (maxDD R² 0.34 ≫ Sharpe R² 0.02, on 888 algorithms) should be
   checked on our own record**, and if it holds, it argues for scoring prop candidates on simulated
   MAE first and edge second — the reverse of the current instinct.
4. **A per-year sign-stability gate is missing from this review's screen** (M2). Every candidate this
   tier killed died there, not on cost.
5. **M1 is a property of bar-sampled fixtures, checkable once**, and would retire a class rather than
   a cell.
6. **O1 is an abstention rule, not a strategy**, and it is the only thing here that could raise
   `P(survival)` without an edge. It owes the Stage-0 test in §O1 before it is anything.

---

## Sources

**26 sources. The binding rule was SATURATION, not the cap.** Tier per schema §4: primary /
secondary / claims. Negative and blocked results are mandatory entries and are included.

| # | URL | accessed | tier | sought | yielded |
|---|---|---|---|---|---|
| 1 | https://quant.stackexchange.com/questions/tagged/intraday?tab=Votes | 2026-09-08 | secondary (QSE) | highest-voted intraday effects | **NOTHING for this brief.** 76 questions; the top of the tag is volatility estimation, realized kernels and data sourcing. No tradeable-effect question above score 8 |
| 2 | https://quant.stackexchange.com/search?tab=votes&q=is%3Aq+score%3A15+%5Btrading%5D | 2026-09-08 | secondary | "does X work" answers on trading | Index only. 18 results; surfaced #4, #5 |
| 3 | https://quant.stackexchange.com/search?tab=votes&q=is%3Aq+score%3A10+%5Bbacktesting%5D | 2026-09-08 | secondary | validation and cost methodology | Index only. 38 results; surfaced #6 |
| 4 | https://quant.stackexchange.com/questions/2138/is-my-trading-strategy-search-methodology-sound | 2026-09-08 | secondary | an intraday CME/LIFFE ML search programme, dismantled | **Qualitative only, no numbers.** Chan quoted at length on ML overfitting in finance; *"you haven't demonstrated an edge."* Logged for completeness, carries nothing |
| 5 | https://quant.stackexchange.com/questions/1264/how-to-simulate-slippage | 2026-09-08 | secondary | execution detail (E4) | **PARTIAL.** Execution- vs tracking-slippage split; MOC realises the official close; the consolidated-vs-primary close warning (E4). One answer says *"I would not assume more than 1 bps slippage"* below 1% of volume — logged, not adopted |
| 6 | https://quant.stackexchange.com/questions/1891/how-much-data-is-needed-to-validate-a-short-horizon-trading-strategy | 2026-09-08 | secondary | a sample-size standard | **YIELDED E1**, the lane's most directly usable formula. `n = (2·s·α/Δ)²`, with the author's own worked HFT example (2 bp expected, 45 bp s.d., 3 bp width, 95% → n = 3,458 trades) |
| 7 | https://quant.stackexchange.com/questions/1920/are-shorter-holding-period-strategies-better | 2026-09-08 | secondary | whether hold length changes inference | **PARTIAL.** Longer horizons show mechanically higher R²/IR via persistence + overlapping returns (Boudoukh, Richardson & Whitelaw 2006), so *equal* IRs favour the shorter-hold strategy. Relevant to the house rule that cost-cutting ≠ edge-sharpening |
| 8 | https://quant.stackexchange.com/questions/83939/how-can-we-determine-the-minimum-viable-holding-period-given-granular-data-and-transaction-costs | 2026-09-08 | secondary | a cost-vs-horizon rule | **YIELDED E2** (lehalle): cost is direction-dependent, not frequency-dependent; turnover is the speed measure; `cost ≤ μ/f` |
| 9 | https://quant.stackexchange.com/questions/85730/where-is-the-signal-to-cost-ratio-least-unfavorable-for-an-independent-quantitative-researcher | 2026-09-08 | claims (anonymous) | where retail cost/edge is least bad | **YIELDED E3 and a rejected specimen.** Asker's own pre-registered rejection: 4 energy names, ~3-min holds, forward return ~0 across deciles, 1–2 bp reversion vs **6.5 bp** round trip. Answers give unverifiable numbers (49.6%/49.0%/50.4% hit rates; −17.5 bp/trade unconditional vs +4.9 bp conditioned, **self-labelled in-sample**) and the 125-order fill measurement. Numbers rejected; the effective-sample-size point retained |
| 10 | https://quant.stackexchange.com/questions/tagged/trading-strategies | 2026-09-08 | secondary | a strategy tag | **NEGATIVE — the tag does not exist.** Recorded so it is not retried |
| 11 | https://quant.stackexchange.com/search?tab=votes&q=is%3Aq+intraday+momentum+futures+decay | 2026-09-08 | secondary | QSE on intraday-momentum decay | **ZERO RESULTS.** QSE has no discussion of the effect at all. Saturation signal for this venue |
| 12 | https://www.quantconnect.com/research/15348/intraday-etf-momentum/ | 2026-09-08 | secondary (platform research, code-backed) | an independent replication of Gao et al. | **YIELDED A CENTRAL NEGATIVE.** Bare rule on SPY/IWM/IYR, 2015-01-01→2020-08-16: **Sharpe −0.628** (ASD 0.002) vs benchmark **0.582**. Positive only in the 2020 crash window (1.452 vs −1.466). **No cost convention stated — so it fails gross** |
| 13 | https://www.quantconnect.com/learning/articles/investment-strategy-library/intraday-etf-momentum | 2026-09-08 | secondary | confirmation of #12 | **YIELDED.** Same four figures verbatim from the platform's own strategy library; confirms #12 is the platform's published position, not one user's backtest |
| 14 | https://www.quantconnect.com/forum/discussion/15192/intraday-trading-strategy-for-futures-contract-nq/ | 2026-09-08 | claims (forum) | an NQ intraday candidate | **REJECTED (A4).** Indicator stack, no mechanism, no sample, no fee model. Retained only for the author's own *"win rate of 61% and nearly broke even… almost solely due to trading fees"* |
| 15 | https://www.quantconnect.com/forum/discussion/17091/beat-the-market-an-effective-intraday-momentum-strategy-for-s-amp-p500-etf-spy/ | 2026-09-08 | secondary (code-backed, with author correspondence) | independent replication of the review's surviving candidate | **THE LANE'S CENTRAL ARTEFACT.** Three implementations, Sharpe **0.399** vs paper's 1.33; **$27,317.98 fees = "16.7 % of your return"** on **6,940 orders**; 37%/63% win/loss; IR **−0.257**. Spread isolated as the entire gap by a mid-price fill experiment. **Author (Zarattini) on record**: slippage **$0.005/share** (paper $0.001), live commission **$0.012/share** (paper $0.0035), drawdown computed on **end-of-day** values, live version uses undisclosed *"more sophisticated trailing methods"*, vol target *"quite subjective"*. A live deployer reports six months of poor performance |
| 16 | https://www.elitetrader.com/et/threads/automated-trading-strategies.327264/ | 2026-09-08 | claims (forum) | quantified automated-strategy results | **NOTHING.** Six posts, 2018, about what counts as an "algo". Zero numbers. (**WebFetch returns HTTP 403 on elitetrader.com**; reached with the browser tool. Recorded so WebFetch is not retried) |
| 17 | https://www.elitetrader.com/et/threads/looking-for-automated-day-trading-system-feedback-orb-equities-bot-gao-intraday-momentum-futures-bot.390039/ | 2026-09-08 | claims (forum) | practitioner critique of a Gao-style MES bot | **YIELDED E5 only.** A well-posed request for falsification (Jun 2026) drew **two replies and died**; the OP *"vanished"*. The one reply is the TradeStation execution-failure account, incl. a **$10k** loss to ignored stops. **No number about the strategy** |
| 18 | https://www.elitetrader.com/et/threads/intra-day-es-statistics.339007/ | 2026-09-08 | claims (forum) | quantified intraday ES statistics | **REJECTED (A3), plus E6.** Win rate without payoff or costs; the thread's own first reply makes the objection. Retained: the 6–24 tick stop / 10–27 tick target scale by volatility regime |
| 19 | https://arxiv.org/abs/2605.04004 · https://arxiv.org/pdf/2605.04004 (full text extracted locally) | 2026-09-08 | preprint, independent researcher, AI-assistance disclosed | a systematic falsification on CME futures | **YIELDED the rejected pile, M1, M2, O1, A1, A2.** 14 signal families, **947 days**, MNQ 5-min, 2.0-pt friction, walk-forward, permutation tests. **Gross edge ceiling 0.07–1.50 pts vs 2.0-pt friction.** Explicitly references prop-firm RTH restrictions. **Its two "positive controls" are the author's own unpublished signals — circular, and A1's Sharpe does not reproduce** |
| 20 | https://forum.wilmott.com/viewtopic.php?t=78085 · https://forum.wilmott.com/viewtopic.php?t=16645 | 2026-09-08 | — | Wilmott practitioner threads | **BLOCKED, AND DELIBERATELY NOT BYPASSED.** WebFetch returns HTTP 403; the browser reaches a *"Verify You Are Human"* arithmetic bot-check. **Solving bot-detection is prohibited under this session's safety rules, so the venue was abandoned.** Wilmott is `NOT ACCESSIBLE` for this review by any permitted route |
| 21 | https://phynance1.rssing.com/chan-12652191/all_p16.html | 2026-09-08 | — | the Nuclear Phynance archive | **NEGATIVE — empty.** The rssing mirror returns no content. The forum itself is defunct; the only trace found is a third-party recollection of a RennTech thread. `NOT ACCESSIBLE` |
| 22 | https://news.ycombinator.com/item?id=39833025 | 2026-09-08 | claims (forum) | a claimed edge dismantled in comments | **REJECTED (A5).** No cost convention, no null, no N. **Nobody in the thread challenged the arithmetic** — the only pushback was "bull market". Retained: *"live results have hit between 1/4 and 3/4 of backtest performance"* |
| 23 | https://news.ycombinator.com/item?id=16922538 | 2026-09-08 | claims (forum) | practitioner accounts of what works and what stopped | **REJECTED WHOLESALE, and the absence is the finding: "No commenter provides Sharpe ratios, maximum drawdown percentages, or statistically significant performance metrics."** Retained as decay hypotheses only: crypto arbitrage windows narrowing *"5-10 minutes to seconds or less"*; *"spreads disappear as soon as you try any kind of significant volume"*; stated HFT equity-access cost **$10k–$100k/month**. Saturation signal for HN |
| 24 | https://community.portfolio123.com/uploads/.../3WHpAUOzhCG8QAUez71HpoWnA62.pdf (SSRN 2745220) | 2026-09-08 | **primary-adjacent** — platform dataset, named authors | whether backtest statistics predict anything | **YIELDED CONTRIBUTION 2.** Wiecki, Campbell, Lent & Stauth (Quantopian), **888 algorithms** with ≥6 months version-locked OOS. Sharpe IS→OOS **R² = 0.02**; annual return **0.015 and negative**; IR/Calmar/alpha **< 0.005**; **volatility 0.67**, **maxDD 0.34**; tail ratio→OOS Sharpe **0.025**; log(backtest days)→Sharpe shortfall **R² = 0.017, p < 0.0001**; ML on 57 features **R² = 0.17**; top-10-by-IS-Sharpe portfolio **Sharpe 0.7** |
| 25 | https://www.cmegroup.com/articles/2025/reassessing-liquidity-beyond-order-book-depth.html · https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457223773/ | 2026-09-08 | primary (exchange research) | intraday spread/cost-to-trade by time of day | **BLOCKED.** WebFetch timed out twice (60 s) then `ECONNRESET`; browser navigation to cmegroup.com was denied. The Liquidity Tool wiki page returned navigation chrome only. **Cost-to-trade by lot size and time window remains `NOT RETRIEVED` for this review.** A future session should try the CME Liquidity Tool directly rather than the article pages |
| 26 | https://api.stackexchange.com/2.3/search/advanced?...&site=quant | 2026-09-08 | — | a programmatic QSE ranking | **BLOCKED** — *"Claude Code is unable to fetch from api.stackexchange.com"*, and `quant.stackexchange.com` is likewise unfetchable by WebFetch. QSE is reachable **only** via the browser tool. Recorded so neither is retried |

**Searches run that produced no new source, so they are not repeated:** an Elite Trader thread with a
multi-year trade record stated net of commissions (none found — three attempts, three framings); a
QSE question on intraday-momentum decay (zero results); a Quantopian community post replicating an
intraday futures strategy (the archive's surviving artefacts are the *platform paper* and static
Q&A threads, not runnable research); an Elite Trader discussion of prop trailing drawdowns
interacting with automated strategies (**the query returns only "Elite Trader Funding" marketing — a
prop firm, unrelated to the elitetrader.com forum**, and that tier belongs to lanes 01–05).

**Per the safety brief.** Two on-page directives were encountered and **not acted on**: a Discord
contact solicitation posted twice in source 15, and Elite Trader's sponsor block (AMP Futures, AXIA
Futures "Trader Training and Mentorship", NinjaTrader, Databento and others) rendered on every ET
page. No account was created, no credential entered, no affiliate or Discord link followed. **No page
contained an instruction addressed to an automated agent.** Source 20's bot-check was left unsolved
by rule, not by failure.
