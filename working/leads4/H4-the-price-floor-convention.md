# H4 — The price floor as an undeclared stop-loss: what the literature actually states

External evidence only. I have no access to this programme's data or code and claim
nothing about either. The code check that created this lane is not mine and I did not
do it.

---

## HEADLINE

**The lane clears its bar, but not in the direction the commissioning premise expected.**

Three findings, in order of how much they should change what the programme does:

1. **The academic cross-sectional literature does not state a mid-hold convention. It
   states a DATE.** The convention that exists is not "eject" or "carry" — it is that the
   screen is evaluated at a named instant ("at the beginning of the holding period", "at
   the end of year y−1", "at portfolio formation") and the sample is then fixed. What
   happens to a name that violates the screen *after* that instant is, in every academic
   paper I read verbatim, **never addressed**. The formation-dating is explicit and
   quotable; the mid-hold rule is absent, not implicit-but-obvious.

2. **The most-used open-source implementation of that literature ejects.** In Chen &
   Zimmermann's Open Source Asset Pricing code — the reference implementation of 212
   published predictors — the price screen `abs(prc) > 5` is applied to **every stock-month
   of the panel**, before the holding-period carry-forward. A held name that falls through
   $5 is dropped for that month and re-enters when it recovers. This is exactly the
   undeclared-stop behaviour the lane was created to ask about, in public code, applied to
   **20 of 212 published predictors whose original papers combine a price screen with a
   multi-month hold**. It is nowhere stated in their prose. **The gap between what the
   papers date and what the code does is real, live, and unremarked.**

3. **The one literature that DOES state an explicit mid-hold convention is index
   methodology, and it is unanimous: CARRY, with a buffer.** MSCI, S&P and FTSE Russell all
   state in writing that eligibility screens bind on *additions* and that existing
   constituents are held under looser or absent thresholds. All three are explicit, quotable
   and primary. **Not one of them ejects a constituent for falling through a price or
   liquidity screen.** They remove only on corporate events.

So: an ejecting floor is **against the stated convention of every methodology document that
states one**, and **consistent with the unstated behaviour of the reference academic
implementation**. That is an uncomfortable split and the brief reports it as such rather
than resolving it.

**Direction of the bias, stated up front** (§3): a floor that ejects after the fall
**overstates a long-only book** and **understates a short-only book**. On a long-short
spread the two partially cancel and the net sign depends on which leg holds the fallen
names.

---

## SOURCES RANKED BY HOW EXPLICIT THEY ARE

The bar for this lane was a stated convention with a citation. Ranked strongest first.

| # | Source | Says what, exactly | Type / establishment |
|---|---|---|---|
| 1 | MSCI GIMI Methodology §3.1.2.4 | Existing constituent **may remain** below the liquidity minimum, down to 2/3 of it | [PRIMARY DATA DOC] [read in full — relevant sections verbatim] |
| 2 | S&P U.S. Indices Methodology, Eligibility Criteria | "**Current constituents have no minimum requirement.**" | [PRIMARY DATA DOC] [read in full — relevant sections verbatim] |
| 3 | FTSE Russell Russell US Indexes §5.8.1 | Existing member below $1.00 on rank day **stays eligible** on a 30-day average | [PRIMARY DATA DOC] [read in full — relevant sections verbatim] |
| 4 | Chen & Zimmermann, OSAP source code | Price screen applied to **every stock-month**, before hold carry-forward ⇒ **ejects** | [PRIMARY DATA DOC] [read in full — code read line by line, not executed] |
| 5 | Jegadeesh & Titman (2001), NBER WP 7159 | Screen dated "**at the beginning of the holding period**"; mid-hold not addressed | [WORKING PAPER — published version JF 2001] [read in full] |
| 6 | Amihud (2002), J. Fin. Markets | Screen dated "**at the end of year y−1**", sample then fixed for 12 months | [PEER-REVIEWED] [read in full] |
| 7 | Hou, Xue & Zhang (2020), RFS / NBER w23394 | Characterises the literature's screen as "**at portfolio formation**" | [PEER-REVIEWED] [read in full] |
| 8 | Chen & Zimmermann (2021), CFR, fn. 19 | "**Most papers do not provide precise explanations of these details**" | [PEER-REVIEWED] [read in full] |
| 9 | Dickerson, Robotti & Rossetti (2026), arXiv | Formal decomposition of the bias from asymmetric ex-post filtering, by leg | [WORKING PAPER] [read in full] |

---

## 1. WHAT PUBLISHED CROSS-SECTIONAL STUDIES DO WHEN A HELD NAME VIOLATES THE SCREEN

### 1.1 The answer is: they don't say. They say *when*, not *what then*.

Every paper I read verbatim dates the screen and stops. Below are the sentences, exactly
as written.

**Jegadeesh & Titman (2001)**, "Profitability of Momentum Strategies: An Evaluation of
Alternative Explanations", NBER WP 7159, p. 6. [WORKING PAPER] [read in full]

> "We follow JT and include all NYSE/AMEX stocks and exclude NASDAQ stocks. We also
> exclude all stocks priced below $5 at the beginning of the holding period. At the end of
> each month we rank the stocks in the sample based on their past six-month returns (month
> —5 to month 0) and then group the stocks into ten equally weighted portfolios based on
> these ranks. Each portfolio is held for six months (month 1 to month 6) following the
> ranking month."

And their table notes, repeated identically across four tables:

> "All stocks priced less than $5 at the beginning of the holding period are excluded from
> the sample."

This is as explicit as the timing gets anywhere in the academic literature I found. The
exclusion condition is **dated at the beginning of the holding period**, and the holding
period is six months. A name that falls through $5 in month 3 satisfies the stated
exclusion condition nowhere — it was above $5 when the condition was evaluated. **The
natural reading is carry-to-term. But JT never say so, and there is no sentence in the
paper that would fail if they in fact ejected.** I record this as *formation-dated,
mid-hold silent*, not as *stated carry*.

**Amihud (2002)**, "Illiquidity and stock returns: cross-section and time-series effects",
*Journal of Financial Markets* 5, p. 36. [PEER-REVIEWED] [read in full]

> "Stocks are admitted to the cross-sectional estimation procedure in month m of year y if
> they have a return for that month and they satisfy the following criteria: (i) The stock
> has return and volume data for more than 200 days during year y−1 … (ii) The stock price
> is greater than $5 at the end of year y−1: Returns on low-price stocks are greatly
> affected by the minimum tick of $1/8, which adds noise to the estimations."

Note the structure: admission is decided **for month m of year y** on the basis of the
price **at the end of year y−1**. A stock admitted in January on a 31-December price of
$6 stays admitted through December, whatever it does in between. This is the closest thing
in the academic literature to a *stated* carry rule — and even here the carry is a
consequence of how the criterion is dated, not a sentence about what happens when a name
falls.

**Hou, Xue & Zhang**, "Replicating Anomalies", NBER w23394, p. 12. [PEER-REVIEWED — RFS
2020] [read in full]

> "Cohen and Lou use NYSE-Amex-NASDAQ breakpoints, and also impose a price screen of $5 at
> portfolio formation. We use NYSE breakpoints with no price screen."

HXZ are describing someone else's method, so this is second-hand — but they are the
literature's most systematic replicators, they read the papers, and the phrase they reach
for is **"at portfolio formation"**. Their own construction (Appendix A.1.4) uses the
standard overlapping sub-portfolio scheme:

> "The holding period that is longer than one month as in, for instance, R66, means that
> for a given decile in each month there exist six sub-deciles, each of which is initiated
> in a different month in the prior six-month period."

— under which any screen is naturally evaluated at initiation. HXZ themselves impose no
price screen at all, and say so twice:

> "Some studies exclude stocks with prices per share lower than $1 or $5. We do not impose
> such a sample screen."

> "We do not impose a price screen to exclude stocks with prices per share below $5 as in
> Jegadeesh and Titman (1993). These stocks are mostly microcaps. Value-weighting returns
> assigns only tiny weights to these stocks, which in turn do not need to be excluded."

That last sentence is worth the programme's attention on its own: HXZ's stated reason for
not needing a price screen is **value-weighting**. This programme is equal-weighted, so
that escape is not available to it — which is precisely why the floor exists and precisely
why the floor's behaviour matters more here than it does in HXZ.

**Ken French's Data Library**, portfolio formation detail page. [PRIMARY DATA DOC]
[read in full — the page is one sentence]

> "The portfolios are constructed at the end of each June using the June market equity and
> NYSE breakpoints."

No price screen, no liquidity screen, and nothing about the interval between formations.
Recorded here because it is the field's most-used reference construction and it is **silent
by design**, not by oversight.

### 1.2 A credible source says outright that the literature is silent

Chen & Zimmermann (2021), "Open Source Cross-Sectional Asset Pricing", *Critical Finance
Review* 11(2) (FEDS working-paper version 2021-037), footnote 19. [PEER-REVIEWED]
[read in full]

> "Following the cross-sectional literature, our portfolios are always rebalanced monthly
> in the sense that stock weights are adjusted every month to provide equal- or
> value-weighting. **Most papers do not provide precise explanations of these details, but
> in our experience this procedure is required for replicating papers.**"

That is the strongest direct evidence for the commissioning suspicion. Two authors who
hand-replicated 212 published predictors state that the papers do not explain the
portfolio-maintenance details, and that they had to reconstruct them from what made the
numbers replicate.

### 1.3 I quantified the silence from Chen & Zimmermann's own hand-collected record

`SignalDoc.csv` in the OSAP repository is Chen & Zimmermann's hand-collected transcription
of each original paper's stated filter and holding period. [PRIMARY DATA DOC] [downloaded
and tabulated by me — the counts below are my computation on their file, not their claim]

Of **212 replicated predictors**:

| | count | share |
|---|---|---|
| No filter recorded from the original paper at all | 144 | 67.9% |
| Original paper states a `price > $5` filter | 29 | 13.7% |
| Original paper states a `price > $1` filter | 10 | 4.7% |
| **Any price filter** | **39** | **18.4%** |
| Holding period longer than one month | 102 | 48.1% |
| **Price filter AND hold > 1 month** — the cell where the question bites | **20** | **9.4%** |
| `price > $5` AND hold > 1 month | 14 | 6.6% |

The 20 include Sloan (1996) accruals (12-month hold, `abs(prc)>5`), Pástor & Stambaugh
(2003) liquidity beta (12m, `>5`), Kelly & Jiang (2014) tail risk (12m, `>5`), Amihud
(2002) illiquidity (12m, `>5` and NYSE-only), Penman-Richardson-Tuna (2007) EBM (12m,
`>5`), Soliman (2008) (12m, `>5`), Hafzalla et al. (2011) percent accruals (12m, `>5`).

Two things follow. First, **the mid-hold question is a live methodological hole across
roughly one in ten published cross-sectional predictors**, not a corner case. Second, the
67.9% "no filter recorded" figure should be read carefully: it means *Chen & Zimmermann
recorded no filter from that paper*, which is consistent with the paper stating none, and
is not proof the paper is silent. I am not claiming 144 papers said nothing; I am claiming
the reference transcription of the literature has nothing to transcribe for them.

### 1.4 The reference implementation of that literature EJECTS — and does not say so

This is the single most consequential thing I found, and it is a code reading, not a stated
sentence. Chen & Zimmermann, OSAP repository (`OpenSourceAP/CrossSection`), read at
`master`. [PRIMARY DATA DOC] [read in full — read line by line; **not executed**, I have
no CRSP data]

The price screen is a string passed into `import_signal`, in
`Portfolios/Code/30_PredictorAltPorts.R`:

```r
# create ME screen
# customscreen is used on the signal df, which is then lagged, so no look ahead here
  strategylist0 %>% mutate(filterstr = "abs(prc) > 5")
```

and applied in `Portfolios/Code/01_PortfolioFunction.R`, in `import_signal`, immediately
after the monthly CRSP price/exchange/market-equity panel is joined on:

```r
  ## apply filters and sign
  # note the signal dataset is lagged further down, so
  # filtering here does not look ahead
  if (!is.na(filterstr)){
    evalme = paste0('signal = signal %>% filter('
                    , filterstr
                    , ')')
    eval(parse(text=evalme))
  }
```

The holding period is imposed **afterwards**, further down the same function:

```r
  # make all na except  "rebalancing months", which is actually signal updating months
  # and then fill na with stale data
  ...
  signal =  signal %>%
    mutate(
      port = if_else(
        (yyyymm %% 100) %in% rebmonths
        , port
        , NA_integer_
      )
    ) %>%
    arrange(permno,yyyymm) %>%
    group_by(permno) %>%
    fill(port) %>%
    filter(!is.na(port))
```

**Order of operations, and what it means.** The filter runs first and deletes whole
stock-months from the panel. The hold is then implemented by carrying the portfolio
assignment forward (`fill(port)`) across the rows that survive. A stock-month where
`abs(prc) <= 5` **has no row**, therefore has no `port`, therefore is dropped by
`filter(!is.na(port))`, therefore contributes no return that month. When the price
recovers above $5 the row reappears, `fill` carries the old assignment down, and the name
**re-enters the same portfolio**.

That is an ejection with automatic re-entry — mechanically, a stop-out at $5 with a
re-entry rule — applied to a 12-month-hold portfolio, in the public reference
implementation of published papers whose own methodology sections date the screen to
formation. **Chen & Zimmermann's prose never describes this.** The nearest they come is
a design note about flexibility:

> "Figure 9 also illustrates the flexibility of our code. These various screens are made
> possible by the fact that we try to delay imposing screens until the portfolio generation
> step. As a result, the user can choose whether he or she wishes to take signal from all
> stocks, or just the more liquid ones."

and the figure caption, which is the closest they get to naming the behaviour:

> "'price > 5,' 'NYSE only,' and 'ME > NYSE 20 pct' **only take positions in stocks** if
> the share price exceeds $5, stock is listed on the NYSE, or if market equity exceeds to
> 20th percentile among NYSE stocks in the month."

"only take positions in stocks if the share price exceeds $5" — evaluated *in the month* —
is a continuous-enforcement statement, and it is buried in a figure caption. **Being
biased toward the negative: this is a code fact plus a caption, not a methodology
sentence. It is the strongest evidence I have that ejection happens in practice, and it is
still not a declared convention.**

---

## 2. THE $5 SCREEN: WHERE IT CAME FROM, WHAT JUSTIFIES IT, WHAT IT DOES

### 2.1 Origin — two roots, both documented, neither statistical

**Root 1, the minimum tick.** Amihud (2002) footnote 10 is the most explicit origin
statement I found anywhere. [PEER-REVIEWED] [read in full]

> "See discussion on the minimum tick and its effects in Harris (1994). **The benchmark of
> $5 was used in 1992 by the NYSE when it reduced the minimum tick.** Also, the
> conventional term of 'penny stocks' applies to stocks whose price is below $5."

with the body text giving the reason:

> "Returns on low-price stocks are greatly affected by the minimum tick of $1/8, which adds
> noise to the estimations."

So the primary academic justification is **microstructure noise from a fixed tick**: a
$1/8 tick on a $5 stock is 2.5%, on a $50 stock 0.25%. Note the direct relevance to this
programme's stated reason for its own floor (IBKR per-share cost scaling inversely with
price) — the mechanism is the same shape, but this justification is about *measurement
noise in the return*, not about *cost*. It also has an expiry date: decimalisation in 2001
removed the $1/8 tick that Amihud's justification rests on. **The screen outlived its
stated reason and nobody restated it.**

**Root 2, the regulatory definition.** The $5 line is the SEC's penny-stock threshold,
adopted under the Securities Enforcement Remedies and Penny Stock Reform Act of 1990 and
implemented in Exchange Act Rule 3a51-1, which exempts from "penny stock" status a security
with a bid price of $5.00 or more. [PRIMARY DATA DOC — statute and rule] [snippet only —
I did not read Rule 3a51-1 verbatim; established from SEC and FINRA secondary pages, see
§7]. Amihud's footnote points at this too ("the conventional term of 'penny stocks'
applies to stocks whose price is below $5"). The threshold is a *regulatory* line about
sales-practice abuse, not a return-measurement line, and it was imported into the empirical
literature by convention.

**Root 3, the empirical scare.** Jegadeesh & Titman's stated reason cites the contrarian
literature. [WORKING PAPER] [read in full]

> "Conrad and Kaul (1993) point out that much of the evidence of long horizon mean
> reversion in DeBondt and Thaler (1985) is due to the inclusion of low priced stocks. We
> screen out these low priced stocks to ensure that our results are not driven by extreme
> price movements in these low priced stocks."

Related and pointing the same way, Ball, Kothari & Shanken (1995), "Problems in measuring
portfolio performance: An application to contrarian investment strategies", *JFE* 38,
79–107: loser stocks are low-priced, their returns are skewed, and the headline 163% mean
loser return is driven by the lowest-price quartile — a small assumed price increase cuts
the mean by 25%. [PEER-REVIEWED] [**abstract/snippet only** — I did not obtain the full
text; the 163%/25% figures come from a search-result summary and I would not put weight on
them without reading the paper].

### 2.2 What the screen does to results — one measured number, in the right direction

Chen & Zimmermann (2021) is the only source I found that measures the price screen's effect
across a large body of predictors on a common construction. [PEER-REVIEWED] [read in full]

> "Intuitively, all liquidity adjustments lead to lower mean returns. **The price screen
> (limiting to stocks with share price > $5) appears to be the softest adjustment, producing
> the smallest decline in performance.** The other liquidity adjustments have relatively
> similar effects.
>
> Overall, simple liquidity adjustments reduce mean returns by a factor of about 1/3, on
> average. The typical mean return drops from around 60 bps per month to about 40 bps per
> month regardless of whether the adjustment is an NYSE only screen, a market equity screen,
> or the enforcement of value-weighting."

Read carefully: the "1/3, ~60→~40 bp/month" figure is stated for **simple liquidity
adjustments in general**, and the price screen is called the **softest** of them. The paper
does not give a separate number for the price screen alone in the text; Figure 9 carries
the distributions and I did not read the figure's plotted values. **So the honest
statement is: applying a $5 screen at formation reduces published anomaly mean returns, by
less than the other common screens do, and less than one third.** Anyone who reports "the
$5 screen costs a third of the mean return" is misreading this sentence.

Direction matters: the screen makes results **worse**, because the excluded low-priced
names carry high equal-weighted mean returns. Hou, Xue & Zhang make the same point about
microcaps generally:

> "Microcaps are on average only 3% of the market value of the NYSE-Amex-NASDAQ universe,
> but account for about 60% of the total [number of stocks]"

and their whole exercise turns on microcaps carrying the highest equal-weighted returns and
the largest cross-sectional dispersion.

**The contrast with an ejecting floor is the point of this whole brief.** A screen applied
at formation *removes candidates before entry* and lowers measured returns. A screen
applied continuously *removes positions after they have fallen* and raises them. Same
screen, opposite sign, and no source I found distinguishes the two.

---

## 3. THE LEFT-TAIL QUESTION — DIRECTION OF THE BIAS

### 3.1 Nothing in the equity literature measures this directly

I searched for a study of what happens when a price or liquidity screen is re-applied
mid-hold and found none. That is a negative finding and I report it as one. What exists
is (a) a formal decomposition of the closely-related asymmetric-ex-post-filtering bias in
another asset class, and (b) the delisting-return literature, which this lane treats as
known background.

### 3.2 The formal result, from the nearest thing to an on-point paper

Dickerson, Robotti & Rossetti (April 2026), "The Corporate Bond Factor Replication Crisis",
arXiv 2604.07880. [WORKING PAPER — arXiv, not peer-reviewed] [read in full]

Their Look-Ahead Bias section formalises exactly the mechanism, for winsorization rather
than for a screen. Verbatim, §4:

> "Consider a long-short factor formed by sorting bonds on signal ŝ_{i,t}, where the long
> leg holds bonds in the top portfolio, the short leg holds bonds in the bottom portfolio,
> and both legs are equal-weighted. … The winsorizing adjustment Δ_{i,t+1} ≡ r̃_{i,t+1} −
> r_{i,t+1} is positive when returns are floored (left tail) and negative when capped
> (right tail). The look-ahead bias is
>
>   LAB_{t+1} ≡ r̃^LS_{t+1} − r^LS_{t+1} = (1/N^L_t) Σ_{i∈Long} Δ_{i,t+1} − (1/N^S_t)
>   Σ_{i∈Short} Δ_{i,t+1}.
>
> The bias decomposes into contributions from each leg, with LAB^L capturing adjustments to
> long positions and LAB^S capturing adjustments to short positions. A positive LAB
> indicates that the reported factor return overstates achievable performance. **The
> direction of LAB depends on where extreme returns concentrate. If the long leg contains
> more left-tail returns (e.g., high-risk bonds that crash during stress), left-tail
> winsorizing benefits the long leg disproportionately, inflating the factor return. If the
> short leg contains more right-tail returns, right-tail winsorizing protects the short leg
> from losses, inflating the factor return.** The magnitude of LAB is largest during
> financial distress."

And their measured magnitudes, from the introduction:

> "For the six-month momentum factor, the 0.30% monthly premium is entirely attributable to
> asymmetric ex-post winsorization. Without winsorization, the premium is zero. For
> twelve-month momentum, the base premium is negative (−0.13%) and ex-post filtering
> converts a losing factor into an apparent winner, with the bias concentrated during
> periods of financial distress. Idiosyncratic volatility factors and downside risk measures
> show similar patterns, with 57–78% of the measured alpha attributable to asymmetric
> ex-post return filtering."

**Caveats I insist on.** This is corporate bonds, not equities. It is *winsorization of
returns*, not a *price screen*. Their filter is genuinely infeasible (thresholds computed
from the full sample, including the investor's future); an ejecting price floor evaluated
on a t−1 close is **not** infeasible (see §3.4). So the magnitudes do not transfer and I
am not transferring them. **What transfers is equation (6): the sign of the effect on a
long-short spread is the long-leg tail adjustment minus the short-leg tail adjustment.**

### 3.3 The direction, for this programme's two cases, stated separately

Applying that decomposition to a floor that ejects a held name once it prints below $5:

**LONG-ONLY BOOK — the measured result is BIASED UPWARD, unambiguously.**
The amputated segment is the continuation of the fall below $5. That is where the worst
outcomes live: the sub-$5 region is the antechamber of delisting and bankruptcy. Ejecting
truncates the left tail of every trade that reaches it. Consequences for the four reporting
groups this programme uses:
- Group 1: mean per trade overstated; vol understated; maxDD understated; breakeven cost
  overstated (the strategy looks like it can bear more cost than it can).
- Group 2: the *median* barely moves while the mean rises, so the mean-below-median tell
  that this programme relies on is **suppressed by the floor**; skew becomes less negative;
  the ex-bottom trimmed mean and the raw mean converge artificially, because the floor has
  already done part of the bottom-trim. **A trimmed-mean report on an ejecting book
  double-counts the left-tail removal and will read cleaner than the strategy is.**
- Group 3: the dead-vs-alive split is the one most distorted, because dead names are exactly
  the ones that transit $5 on the way out.
- Group 4: a null that shares the floor inherits the same truncation, so the null is
  *also* flattered and the comparison is less broken than the level is — but only if the
  null's events sit in the same eligibility mask.

**SHORT-ONLY BOOK — the measured result is BIASED DOWNWARD, unambiguously.**
The same amputated segment is, for a short, the profit. A short that rides a name from $8
to $0.40 is cut off at $5 and books a fraction of what it earned. **The floor destroys
precisely the short book's best trades.** A short book that looks marginal under an
ejecting floor may be materially better without one, and this is the one case where the
undeclared stop is *conservative*. The corresponding background number, treated as known
and cited in one line only: Eisdorfer (2008), "Delisted firms and momentum profits",
*Journal of Financial Markets* 11, 160–179, reports that about 40% of momentum profit comes
from delisting returns, mostly bankrupt firms in the short leg. [PEER-REVIEWED]
[**abstract/snippet only**].

**LONG-SHORT SPREAD — the two effects partially cancel and the net sign is an empirical
question about leg composition.** From equation (6): ejecting fallen names raises the long
leg's measured return (raises the spread) and raises the short leg's measured return
(lowers the spread). If the fallen names concentrate in the short leg — the usual case,
since the short leg is selected on the bad signal — the floor **understates** the spread.
If the strategy is one whose long leg holds distressed names, it **overstates**. This
cannot be settled from outside; it is settled by counting, per leg, how many held names
transit the floor.

### 3.4 The important distinction: this is NOT necessarily look-ahead bias

I want to be precise, because getting this wrong in either direction would mislead.

A floor evaluated on the **as-traded close at t−1** is observable at t. An ejection
triggered by it is **implementable**. A real trader could have placed that stop and could
have taken that exit. So the standard ex-post-conditioning / look-ahead framing —
Dickerson et al.'s LAB, the survivorship literature, the "conditioning on a variable
correlated with the outcome" framing in the commissioning brief — **does not automatically
apply**. Nothing about the future is being used.

The defect is different and, for this programme, arguably worse: **the reported statistics
belong to a strategy that is not the strategy described.** Every number carries an
undeclared stop-loss at $5 that appears in no pre-registration, no decision record and no
result table. The strategy is real; the description is wrong. That is a
specification-disclosure problem, not an econometric-bias problem, and the fix is to
declare the stop and report both variants — not to remove it.

Look-ahead *would* enter through three specific doors, all worth checking:
1. **The exit price.** If the ejected position is booked at $5, or at the t−1 close that
   triggered the test, rather than at a price actually reachable at t, the exit is
   optimistic. A name that gaps from $5.40 to $3.10 does not exit at $5.
2. **Adjusted vs as-traded.** The brief states the floor is on as-traded prices, which is
   the correct choice and closes the obvious version of this door.
3. **Re-entry.** If an ejected name re-enters when it crosses back above $5 (as the Chen &
   Zimmermann code does), the book systematically re-buys after recoveries. That is a
   distinct, undeclared *entry* rule, and it is not obviously implementable at the prices
   assumed.

### 3.5 The corporate-action interaction, which the commissioning brief was right to flag

A floor on as-traded prices fires on corporate actions as well as on returns, in both
directions:
- A **reverse split** lifts a sub-$5 name back over the floor with no economic change. This
  is not rare among exactly the population in question: sub-$1 and sub-$5 names reverse-split
  to regain exchange listing compliance. An ejected name can therefore be *re-admitted by a
  reverse split* at a price that has nothing to do with its prospects. [I did not verify
  exchange minimum-bid listing rules in this lane — flagged in §7.]
- A **forward split** or large special distribution can push a healthy name under the floor
  with no loss at all, ejecting a position for a non-event.

Neither direction is addressed by any source I found. Both are pure artefacts of defining
the floor on as-traded prices, and both are asymmetric with respect to distress.

---

## 4. THE MIRROR CASE — WHAT IS THE CONVENTION FOR CARRYING A NAME BELOW THE FLOOR?

**This is where the lane's bar is cleared most cleanly.** The index-methodology literature
states the convention explicitly, in writing, in three independent primary documents, and
all three say *carry*.

### 4.1 MSCI — carry, with a stated 2/3 buffer

MSCI Global Investable Market Indexes Methodology, August 2024, §3.1.2.4 "Minimum Liquidity
Requirement for Existing Constituents". [PRIMARY DATA DOC] [read in full — section verbatim]

> "Non constituents of the Investable Market Indexes are evaluated relative to the
> thresholds described in section 2.2.5.
>
> **An existing constituent of the Investable Market Indexes may remain in a Market
> Investable Equity Universe if its 12-month ATVR falls below the Minimum Liquidity
> Requirement as long as it is above 2/3rd of the minimum level requirement of 20% for
> Developed Markets and 15% for Emerging Markets, i.e., 13.3% and 10%, respectively.** In
> addition, in order to remain in the Investable Market Indexes the existing constituent
> must have:
> • The 3-month ATVR of at least 5%;
> • The 3-month Frequency of Trading of at least 80% for Developed Markets and 70% for
> Emerging Markets."

and on size, immediately above:

> "Non constituents of the IMI are evaluated relative to this updated threshold, **whereas
> all existing constituents will not be evaluated relative to this investability
> requirement.**"

### 4.2 S&P — carry, with no threshold at all for constituents

S&P Dow Jones Indices, "S&P U.S. Indices Methodology", December 2022, Eligibility Criteria
→ Liquidity. [PRIMARY DATA DOC] [read in full — section verbatim]

> "**Liquidity.** A float-adjusted liquidity ratio (FALR), defined as the annual dollar
> value traded divided by the float-adjusted market capitalization (FMC), is used to measure
> liquidity. … Eligibility differs depending on the index:
> • S&P Total Market Index
>   o Liquidity requirements are reviewed during the quarterly rebalancings. …
>   o FALR must be greater than or equal to 0.1.
>   o **Current constituents have no minimum requirement.**
> • S&P Composite 1500 …
>   o The stock should trade a minimum of 250,000 shares in each of the six months leading
>     up to the evaluation date.
>   o FALR must be greater than or equal to 1.0 at the time of addition to the Composite 1500.
>   o **Current constituents have no minimum requirement.**"

"Current constituents have no minimum requirement", stated twice, is the single most
explicit sentence I found on this whole question. Note also that the current S&P U.S.
methodology carries **no minimum price criterion at all** — I grepped the document and
found none. The screen this programme runs has no analogue in the largest US index family.

And on what actually removes a constituent:

> "**Deletions.** Deletions occur as follows:
> • A company is deleted from the index if it is involved in a merger, acquisition, or
> significant restructuring such that it no longer meets the eligibility criteria: …
> If a stock is moved to the pink sheets or the bulletin board, the stock is removed.
> • A company that substantially violates one or more of the eligibility criteria for the
> S&P Composite 1500 may be deleted from the respective component index at the Index
> Committee's discretion."

Removal for screen violation is **discretionary and requires a substantial violation**. It
is not automatic and it is not mechanical.

### 4.3 FTSE Russell — carry, with a stated 30-day averaging buffer, and this one is a PRICE screen

FTSE Russell, "Russell US Indexes — Construction and Methodology", §5.8 "Minimum closing
price". [PRIMARY DATA DOC] [read in full — section verbatim]

> "**5.8.1** A stock must have a close price at or above $1.00 (on its primary exchange) on
> rank day to be considered eligible for inclusion. **In order to reduce unnecessary
> turnover, if an existing index member's closing price is less than $1.00 on rank day, it
> will be considered eligible if the average of the daily closing prices (from its primary
> exchange) during the 30 days prior to the rank date is equal to or greater than $1.00.**
> If an existing index member does not trade on the rank day, it must price at $1.00 or
> above on another eligible US exchange to remain eligible. A stock added during the
> quarterly IPOs process is considered a new index addition and therefore must have a close
> price on its primary exchange at or above $1.00 on the last day of the IPO eligibility
> period in order to qualify for index inclusion."

This is the direct analogue of the programme's floor, on a price, with an explicitly stated
asymmetry between additions and existing members and an explicitly stated *reason* for the
asymmetry: **"In order to reduce unnecessary turnover."** Note also that membership is
determined only at the semi-annual reconstitution (§4.2.3, "the fourth Friday in June and
the second Friday in December") plus quarterly IPO additions — so a member that falls below
$1.00 in, say, September is **not removed at all** until the December rank day, and even
then gets the 30-day average buffer.

*(Boundary note: index-reconstitution trading effects are on this programme's exclusion
list and I did not research them. I used these documents purely as sources of stated
maintenance conventions, which is a different object.)*

### 4.4 At what price is a departed name marked?

Two explicit statements, both primary:

S&P, "Other Adjustments":

> "In cases where there is no achievable market price for a stock being deleted, it can be
> removed at a zero or minimal price at the Index Committee's discretion."

MSCI, §3.2.3.4 "Early Deletions of Existing Constituents":

> "Securities of companies that file for bankruptcy, companies that file for protection from
> their creditors and/or are suspended and for which a return to normal business activity
> and trading is unlikely in the near future are removed from the MSCI Global Investable
> Market Indexes as soon as practicable. Companies that fail stock exchange's listing
> requirements with announcements of delisting from the stock exchanges are treated in the
> same way. **When the primary exchange price is not available, the securities are deleted
> at an over-the-counter or equivalent market price when such a price is available and deemed
> relevant. If no over-the-counter or equivalent price is available, the company is deleted
> at the lowest system price (0.00001) in the security's price currency.**"

Both are unambiguous and both point the same way: **you mark it at what it is worth,
including at approximately zero, and you do not mark it at the screen threshold.** MSCI's
list of what triggers early deletion is bankruptcy, suspension, announced delisting,
corporate events, free-float collapse — **failing a liquidity or price screen is not on the
list.**

The academic mirror of this is the delisting return, which the lane treats as known
background. One line only, because it is the sentence the convention rests on — Amihud
(2002) footnote 9:

> "Specifically, the last return used is either the last return available on CRSP, or the
> delisting return, if available. Naturally, a last return for the stock of −100% is
> included in the study. A return of −30% is assigned if the deletion reason is coded by 500
> (reason unavailable), 520 (went to OTC), 551–573 and 580 (various reasons), 574
> (bankruptcy) and 584 (does not meet exchange financial guidelines). Shumway (1997) obtains
> that −30% is the average delisting return, examining the OTC returns of delisted stocks."

Note the direct relevance: DLSTCD 584 is "does not meet exchange financial guidelines" —
the population that transits a price floor on its way out — and the convention assigns it
**−30%**, not an exit at the floor.

---

## 5. THE SAME QUESTION FOR A DOLLAR-VOLUME / LIQUIDITY SCREEN

The programme's floor has a trailing-dollar-volume clause as well as a price clause, so
this section is short but the answer is cleaner than for price.

**The index methodologies are explicit and unanimous, and they are *more* generous on
liquidity than on price.** §4.1 and §4.2 above are both liquidity rules, not price rules:
MSCI lets an existing constituent sit at 2/3 of the minimum ATVR indefinitely; S&P says
current constituents have *no* FALR minimum at all. FTSE Russell's US methodology has no
standing liquidity screen for US constituents at all — its ADDTV tests apply to
non-US-incorporated companies establishing US index eligibility (§6, "liquidity: average
daily Dollar trading value (ADDTV) must exceed that of the global median").

**The academic convention is again a date, not a rule.** Amihud (2002) criterion (i):

> "The stock has return and volume data for more than 200 days during year y−1: This makes
> the estimated parameters more reliable. Also, the stock must be listed at the end of year
> y−1."

Evaluated on year y−1, fixed for all twelve months of year y. Same structure as the price
criterion, same silence about the interval.

**One asymmetry the programme should note, and no source addresses it.** Price and dollar
volume behave very differently as continuous screens:
- A **price** floor is monotone in the thing you are trying to measure. A held long that
  falls through the price floor has lost money; the ejection is perfectly correlated with
  the trade's own P&L. That is what makes it a stop.
- A **dollar-volume** floor is not monotone. Dollar volume *spikes* on distress, on news,
  on capitulation. A name collapsing toward delisting frequently trades *more* dollars, not
  fewer, right when it is falling. So a trailing-dollar-volume screen ejects on the *quiet*
  names, which is a different and largely orthogonal selection to the price screen's.
- But dollar volume is price × shares, so the two clauses are mechanically coupled: a
  halving of price halves dollar volume at constant share turnover. **A trailing-dollar-volume
  screen therefore contains a partial, lagged price screen inside it**, and the lag is the
  trailing window. If the programme's floor is `price >= $5 AND trailing dollar volume >= X`,
  the second clause can eject a name *after* the price clause would have, at a delay set by
  the window length — meaning the two clauses stop the same trade twice, at two different
  points, and the effective stop is whichever binds first.

No source I found discusses the interaction of a price clause and a volume clause in a
compound screen. That is a genuine gap and I record it as one.

---

## 6. SAFETY LOG

- **Prompt-injection:** No page, PDF or code file I read contained text addressed to me,
  instructions to take an action, or claims of authority. Nothing to quote or flag.
- **Contact string:** All fetches used the User-Agent
  `Mozilla/5.0 (compatible; AcademicResearch/1.0; research@backtest-framework.org)`.
  No personal address was used anywhere.
- **Downloads:** I downloaded public academic PDFs and public source-code text files to the
  session scratchpad in order to read them locally, per the summariser rule. Nothing was
  executed, no account was created, no credential entered, no form submitted.
- **Summariser discipline:** Every quoted methodology sentence in this brief was extracted
  locally with `pypdf` or read as raw text, **not** obtained through WebFetch's summariser.
  One WebFetch summariser call on the Chen & Zimmermann portfolio code
  (`01_PortfolioFunction.R`) returned **"The code provided does not contain explicit price
  screens (price > 5) or market equity screens."** — which is **false**; the screen is
  applied through the `filterstr` argument in the same file, and the string `abs(prc) > 5`
  is set in `30_PredictorAltPorts.R`. I found it by downloading the raw files and grepping.
  **The summariser would have caused this brief to reach the opposite conclusion on its most
  important finding.** Logged as further evidence for the rule.
- **Blocks, by tool and response:**
  - `curl` → `https://www.spglobal.com/spdji/en/documents/methodologies/methodology-sp-us-indices.pdf`
    → 2,011 bytes of HTML, `<title>Error | S&amp</title>`, referencing `stagingciq.com` assets.
    Not a bot block message; looks like a broken/moved path on their side.
  - `curl` → `https://www.spglobal.com/spdji/tc/documents/methodologies/methodology-sp-us-indices.pdf`
    → same 2,011-byte error page. Worked around by reading the December 2022 edition from a
    third-party mirror (betashares.com.au). **The S&P text I quote is therefore the December
    2022 edition from a mirror, not the current edition from S&P.** Flagged in §7.
  - No other fetch failed.

---

## 7. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **I could not find a single academic paper that states what happens to a held name that
   violates a price screen mid-hold — in either direction.** Not one says "the stock is
   dropped", not one says "the stock is held to the end of the holding period". I read
   Jegadeesh & Titman (2001), Amihud (2002), Hou-Xue-Zhang (2020) and Chen & Zimmermann
   (2021) in full and searched for the phrasing in several others. Absence of evidence
   after this much looking is meaningful, but it is not proof: I read four papers in full
   out of a literature of hundreds, and a statement may exist in one I did not open.

2. **I did not execute the Chen & Zimmermann code.** My conclusion that its price screen
   ejects mid-hold names is a reading of the order of operations in
   `01_PortfolioFunction.R` (filter in `import_signal` deletes stock-month rows; `fill(port)`
   carries assignments across surviving rows only), not an observed output. I have no CRSP
   data and no R environment. Someone with WRDS access could confirm or refute this in
   minutes by comparing `Nlong` for a 12-month-hold predictor with and without
   `filterstr = "abs(prc) > 5"`. **Until that is done, treat §1.4 as a strong code reading,
   not a demonstrated fact.**

3. **I did not verify the exact re-entry semantics** of `dplyr::fill()` against a constructed
   example. My claim that an ejected name re-enters its old portfolio on recovery follows
   from `fill()`'s documented downward-carry default plus the fact that failing months have
   no row. I did not test it.

4. **The S&P methodology I quote is the December 2022 edition, obtained from a third-party
   mirror**, because both S&P URLs returned an error page. The current edition may differ.
   The two sentences I lean on ("Current constituents have no minimum requirement") are
   long-standing S&P practice, but I did not confirm them in the current document.

5. **I did not read SEC Rule 3a51-1 verbatim.** The $5 penny-stock threshold and its origin
   in the 1990 Penny Stock Reform Act are established here from SEC and FINRA secondary
   pages via search snippets only. The Amihud footnote is my only *read-in-full* source on
   the $5 origin, and it attributes the benchmark to the NYSE's 1992 minimum-tick reduction,
   not to the SEC rule.

6. **Ball, Kothari & Shanken (1995) is abstract/snippet only.** The 163% loser mean and the
   "25% reduction from a small price increase" figures come from a search-result summary. I
   did not obtain the paper. Do not quote those numbers onward from this brief.

7. **Eisdorfer (2008) "40% of momentum profit from delisting returns" is snippet only.** I
   confirmed author, journal, volume and pages but did not read the paper.

8. **Chen & Zimmermann's separate effect size for the $5 screen alone is not in their text.**
   They say it is the "softest" adjustment and give ~1/3 / 60→40 bp per month for liquidity
   adjustments *as a class*. The price-screen-only number lives in Figure 9, which I did not
   read as plotted values. **Do not attribute "1/3" to the $5 screen specifically.**

9. **My SignalDoc.csv tabulation is my computation, not Chen & Zimmermann's published
   claim.** The counts (212 predictors; 144 with no filter recorded; 29 with `prc>5`; 20 with
   a price filter and a hold > 1 month) come from parsing their hand-collected file. The
   "no filter recorded" category means they recorded none from that paper — it does not
   establish that the paper stated none.

10. **The Dickerson-Robotti-Rossetti magnitudes do not transfer to equities and I did not
    transfer them.** Different asset class, different filter (return winsorization, not a
    price screen), and their filter is genuinely infeasible while a t−1 price floor is not.
    Only their equation (6) sign decomposition is used.

11. **I did not verify exchange minimum-bid listing standards** (the Nasdaq/NYSE $1 rule)
    or the reverse-split-for-compliance mechanism referenced in §3.5. That paragraph is
    reasoning about a mechanism I did not establish in this lane.

12. **No source I found addresses a compound price-AND-dollar-volume screen.** §5's closing
    argument about the two clauses stopping the same trade at two different points is my
    reasoning, not anyone's stated finding.

13. **I found no measured estimate, in any asset class, of the effect of ejecting a held
    name at a price floor.** The number the programme would most want — how much of a
    long-only result is the truncated left tail worth — does not exist in the literature I
    searched. It is measurable internally by carrying ejected names to their terminus and
    differencing, and that is the only way I can see to get it.

---

## SOURCES

- Jegadeesh, N. & Titman, S. (1999/2001). *Profitability of Momentum Strategies: An Evaluation of Alternative Explanations.* NBER Working Paper 7159. https://www.nber.org/system/files/working_papers/w7159/w7159.pdf — [WORKING PAPER] [read in full]
- Amihud, Y. (2002). *Illiquidity and stock returns: cross-section and time-series effects.* Journal of Financial Markets 5, 31–56. https://www.cis.upenn.edu/~mkearns/finread/amihud.pdf — [PEER-REVIEWED] [read in full]
- Hou, K., Xue, C. & Zhang, L. *Replicating Anomalies.* NBER Working Paper 23394 (published RFS 2020). https://www.nber.org/system/files/working_papers/w23394/w23394.pdf — [PEER-REVIEWED] [read in full]
- Chen, A. Y. & Zimmermann, T. (2021). *Open Source Cross-Sectional Asset Pricing.* Critical Finance Review 11(2), 207–264; FEDS 2021-037. https://www.federalreserve.gov/econres/feds/files/2021-037pap.pdf — [PEER-REVIEWED] [read in full]
- Chen, A. Y. & Zimmermann, T. *OpenSourceAP/CrossSection* repository: `Portfolios/Code/01_PortfolioFunction.R`, `Portfolios/Code/30_PredictorAltPorts.R`, `SignalDoc.csv`. https://github.com/OpenSourceAP/CrossSection — [PRIMARY DATA DOC] [read in full, not executed]
- Dickerson, A., Robotti, C. & Rossetti, G. (April 2026). *The Corporate Bond Factor Replication Crisis.* arXiv 2604.07880. https://arxiv.org/pdf/2604.07880 — [WORKING PAPER] [read in full]
- MSCI (August 2024). *MSCI Global Investable Market Indexes Methodology.* https://www.msci.com/indexes/documents/methodology/1_MSCI_Global_Investable_Market_Indexes_Methodology_20240812.pdf — [PRIMARY DATA DOC] [read in full, relevant sections]
- S&P Dow Jones Indices (December 2022). *S&P U.S. Indices Methodology.* Read from mirror: https://www.betashares.com.au/wp-content/uploads/2016/10/methodology-sp-us-indices.pdf (spglobal.com URLs returned an error page) — [PRIMARY DATA DOC] [read in full, relevant sections]
- FTSE Russell. *Russell US Indexes — Construction and Methodology.* https://research.ftserussell.com/products/downloads/Russell-US-indexes.pdf — [PRIMARY DATA DOC] [read in full, relevant sections]
- Fama, E. F. & French, K. R. *Data Library*, portfolio formation detail page. https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_port_form_sz.html — [PRIMARY DATA DOC] [read in full]
- Ball, R., Kothari, S. P. & Shanken, J. (1995). *Problems in measuring portfolio performance: An application to contrarian investment strategies.* JFE 38, 79–107. — [PEER-REVIEWED] [abstract/snippet only]
- Eisdorfer, A. (2008). *Delisted firms and momentum profits.* Journal of Financial Markets 11(2), 160–179. — [PEER-REVIEWED] [abstract/snippet only]
- SEC Exchange Act Rule 3a51-1 / Securities Enforcement Remedies and Penny Stock Reform Act of 1990. — [PRIMARY DATA DOC] [snippet only, via SEC and FINRA secondary pages]
- Alpha Architect, *Explaining the Performance of Low-Priced Stocks: The Penny Stock Anomaly.* https://alphaarchitect.com/low-priced-stocks/ — [PRACTITIONER] [snippet only; used only for background context, no claim in this brief rests on it]
