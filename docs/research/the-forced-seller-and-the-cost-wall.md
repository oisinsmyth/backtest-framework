# The forced seller and the cost wall — round 2 external evidence

**Round 2 of the lead scan.** Six territories commissioned 2026-09-09 under
[`working/leads2/README.md`](../../working/leads2/README.md); its exclusion list is the durable
record of what round 2 was kept off. Round 1 is [`the-negative-space-scan.md`](the-negative-space-scan.md)
§9a–§9b.

**STATUS: COMPLETE — all six briefs are in.** The record was opened when three had landed and
extended in place as the rest arrived; §§2–4c carry one territory each.

**THE HEADLINE, AND IT IS THE SAME SHAPE AS ROUND 1: the most valuable returns are not leads.**
Four of the six most consequential findings below are about **method, data or cost** — a biased
spread estimator, a survivors-only identifier trap, a spin-off adjustment that explains a defect
already on our record, and a hard auction cut-off — and **not one of them is a strategy.** Of the
four signal territories, **`F1`'s premise was inverted, `F3`'s window sits inside the claimed dead
zone, `F2`'s anomaly has no cost-honest post-2010 survival, and `F6` ranks three of its four
families as resolving overnight, where daily bars cannot reach them.**

**The reading rule, unchanged from round 1.** Every claim about *this programme's* data or methods
is re-measured here before being recorded. **Every claim about the outside world is attributed, and
tagged with how well it was actually established** — `[read in full]`, `[abstract only]`,
`[snippet only]`, `[UNVERIFIED]`. An agent's summary of a paper is not a reading of the paper, and
citing anything below in a decision record requires reading the source. Under
[R15](../RULES.md#r15) **nothing here closes or admits anything.**

---

## 1. The findings that are not about any territory

These are worth more than the territory verdicts, which is the same shape round 1 took.

### 1.1 A DATA FINDING THAT APPLIES TO EVERY EDGAR STUDY THIS PROGRAMME WILL EVER RUN

**`company_tickers.json` is survivors-only and must not be used to map our universe.** The
programme already owns an EDGAR puller ([D331](../decisions/D331-the-deal-filter.md)), and the
fixture is **35.7% dead** — a survivors-only crosswalk silently deletes the cohort the fixture
exists to keep.

**The fix is better than a crosswalk, and it is free.** `F2` verified live that
**`ISSUERTRADINGSYMBOL` is NOT NULL inside every Form 4** (`<issuerTradingSymbol>AAPL</…>`). The
ticker is *what the issuer said it was on the filing date*, so **dead names carry their own tickers
forever and the mapping is point-in-time by construction** — no external file, no vintage problem.
`F3` found the same hazard from the opposite side: on `data.sec.gov/submissions/CIK…json`,
**delisted issuers have empty `tickers` arrays**, so ticker→CIK *is* the survivorship risk, while
the filings themselves survive (verified on SVB Financial, delisted 2023, still serving its Item
2.02 8-Ks).

**Residual hazard, stated:** ticker recycling. Join on `(ticker, date-within-listing-interval)`,
never on ticker alone. **This is the same class of finding as round 1's FTD/CUSIP crosswalk (`N2`)
— an INPUT, not a signal**, and it is worth keeping whether or not any lead below survives.

### 1.2 AN ANALYTIC COLLAPSE TRANSFERS; A MEASURED SHARPE DOES NOT

The single most useful distinction to come out of `F4`, and it governs how the rest of this record
should be read.

**Risk parity degenerates here as a matter of algebra, not of evidence.** Under constant
correlation, equal-risk-contribution **is** inverse-volatility weighting; add equal volatilities and
it **is** `1/N`. This programme's fixture carries **10.06 effective independent instruments over a
held book** ([`FINDINGS.md`](../FINDINGS.md)) — *"at ~10 effective instruments there is no third
thing for it to find."* Minimum-variance is worse: provably unstable in exactly that regime.

**That argument needs no paper to be true of us**, which matters, because the Roncalli source
behind it could not be read (TLS failure) and is tagged `[UNVERIFIED]` below. **A derivation we can
check ourselves survives an unreadable citation; a reported Sharpe does not.** Every number in §4
attributed to a paper's table is in the second category.

### 1.3 THE PROP HURDLE IS A DEMAND FOR A DIFFERENT DISTRIBUTION, NOT A SIZING SETTING

**Calmar is invariant to the leverage scalar.** Return and `E[MaxDD]` both scale linearly with
exposure, so **vol targeting, fractional Kelly and risk parity's leverage step are all
Calmar-neutral.** Via the Magdon-Ismail–Atiya closed form `[read in full]`, **Calmar 18.9 ≈ Sharpe
7 over one year and ~5 over two.**

The book runs at **Sharpe 0.92** ([`FINDINGS.md`](../FINDINGS.md) §7, from the prop-firm review).
**No sizing rule closes that gap, because no sizing rule can.** This is a structural answer to a
question the programme has asked repeatedly, and it says the prop track needs a different *payoff*,
not a better *fraction*.

### 1.4 AN OUTSIDE ACCOUNT OF A DEFECT ALREADY ON OUR RECORD — and it names the correct fix

`F6` went looking for spin-off *returns* and came back with something better: **a mechanical
account of the spin-off price defect this programme has already been bitten by.**

> **CORRECTION, 2026-09-09, made after this section was first written and kept visible rather than
> silently edited.** This section originally said the mechanism below explained D403's **5×
> ServiceNow shape**. **IT DOES NOT.** D403 measured **NOW at 15m ÷ daily = 0.20000 flat, which is
> a genuine 5:1 SPLIT read across two fixtures on different corporate-action bases** — a basis
> mismatch, not a misfiled distribution. **The spin-off in that same measurement is ILMN at
> 0.97276, the GRAIL spin-off, and it is NOT an integer** — which is exactly why `raw_price_factor`
> fixes NOW and leaves ILMN 2.7% out. I tied a new claim to an existing record without reading the
> object it pointed at. **The integer mechanism below is a real hazard that we have NOT observed
> here.** The correction previously existed only in commit `7611123`'s message; it belongs in the
> research record, which is where it now is.

**The defect.** At the ex-date the parent gaps down by the distributed stub. **That is a fake crash,
and a reversal book will buy it.** The programme has an observed version of the *scalar-factor*
half: `raw_price_factor` could not repair a spin-off, leaving **ILMN 2.7% out** while fixing a name
whose discrepancy was a true split.

**Why a scalar cannot fix it, stated mechanically.** The correct adjustment is a **multiplicative
step applied to all PRIOR bars**, `f = (P_cum − r·P_child) / P_cum` — **date-dependent by
construction**, which is exactly what a single scalar factor cannot express. And **the child has no
pre-when-issued history at all**, so for the child it is missing data rather than mis-scaled data.

**A hazard we have NOT observed, and it would look like an integer.** Vendors log spin-off factors
in the **split table**. A distribution ratio read as a split ratio **shifts the whole series by a
clean integer multiple.** **This is not what happened in D403** (see the correction above) — but it
is worth knowing that **an integer discrepancy has two possible causes**, a real split on a
different basis and a misfiled distribution, **and the number alone does not distinguish them.**
Round 3's `G6` later found the same forcing from the schema side: a two-field corporate-action
schema has **only one place to put a spin-off's value**
([`the-plumbing-round.md`](the-plumbing-round.md) §7).

`[Sourced from CRSP's *Factor to Adjust Price* documentation and the Nasdaq corporate-actions
manual; the Nasdaq PDF would not render for the agent and is `[not read]`.]` **This is an
explanation, not a measurement — no fixture was touched. Whether to act on it is the principal's
call.**

### 1.5 ONE BRIEF ANSWERED ANOTHER'S OPEN QUESTION

`F6` lists as unverified: *"whether `data.sec.gov` submissions JSON exposes 8-K item codes — not
checked live."* **`F3` checked it live and it does** — the `items` field carries `"2.02,8.01,9.01"`
alongside `reportDate` and `acceptanceDateTime`. Recorded here so the gap is not re-researched.

### 1.6 THE HOUSE SPREAD ESTIMATOR IS BIASED IN THE DIRECTION THAT MATTERS MOST

**`CLAUDE.md` instructs estimating the spread of held names with Corwin–Schultz off the OHLC**, and
that instruction is load-bearing — it is how D285's **33.8 bp/side** was obtained, and that number
is the cost bar used in §2 and §4 of this record.

**Ardia, Guidotti & Kroencke (JFE 2024) find Corwin–Schultz UNDERESTIMATES effective spreads for
small, illiquid stocks** — exactly this programme's tail, and exactly the population where its leads
keep dying. **If that holds here, 33.8 bp/side is a FLOOR rather than an estimate, and every
breakeven comparison in the record is more lenient than it looks.**

**There is a closed-form drop-in replacement on the same OHLC inputs — EDGE, with published code
(`bidask` on PyPI).** `F5`'s recommended order of work, and it is right: **recompute D285's 33.8 bp
under EDGE before anything else, because it sets the SIGN of every cost conclusion downstream** —
including `F5`'s own savings estimate.

**`[NOT COMPUTED — this record is research only.]`** This is a finding about an estimator, not a
measurement. **Whether to re-open D285 is the principal's call.**

### 1.7 A HARD OPERATIONAL CONSTRAINT ON ANY CLOSE-DECIDED BOOK

**The NYSE MOC/LOC hard cut-off is 3:50 pm** (Nasdaq: MOC 3:55, LOC 3:58, IO 4:00), from the
exchanges' own fact sheets. **A signal computed FROM the close cannot fill IN that close.**

The programme's edge is overnight and a fill convention has already inverted a result once (D280).
**This is a constraint on construction, not a preference**, and it should be checked against any
book that decides at the close and assumes it trades there.

**Related, and unpriced here:** opening auctions carry the **largest price impact of the three
mechanisms** (Goyal, Jegadeesh & Wu, JFQA 2026) — **close beats open**. Their pooled figure is
**square-root impact 17.7 bp at 1% ADV against 2.35 bp modelled linearly**; the per-size-bucket
figures are `[UNVERIFIED]` and are not used.

---

## 2. `F2` — SEC Form 4 insiders

**Verdict: the data is excellent; the anomaly probably is not.**

**The canonical magnitudes are all pre-2008, gross, and small-cap.** Jeng–Metrick–Zeckhauser ~6%/yr
on purchases, 1975–96 `[abstract only]`; Cohen–Malloy–Pomorski 180 bp/mo equal-weighted and 82
bp/mo value-weighted long–short, 1986–2007 `[read in full]`. **They live exactly where the `$5`
floor and per-share commissions bite.**

**Post-2010 there is no clean, cost-honest, peer-reviewed survival — three negatives against one
weak positive.**

| | |
|---|---|
| Oenschläger & Möllenhoff (FRL 2025) `[abstract only]` | filing-date profits *"vanish and even become negative when limiting the tradable dollar amount to a reasonable size"*, negatively correlated with liquidity — **and that is BEFORE costs** |
| Ozlen & Batumoglu `[UNVERIFIED]` | 70–80% of alpha dissipates between transaction date and next session |
| best neutral post-2010 measurement | **+1.0% at 5 days**; 21- and 63-day CIs contain zero; **no costs applied** |
| Schroeder & Krause (*J. Investing* 2026) `[paywalled — read via a summary]` | the one positive: assumes **10 bp/side**, holds ≤12 concurrent small-caps at 29.3% vol, and **its claimed Sharpe 1.88 does not reconcile with its own 17.4% CAGR / 29.3% vol** |

**Against this programme's own measured cost that is decisive.** D285 measured **33.8 bp/side on
the names actually held** (Corwin–Schultz off the OHLC, `CLAUDE.md`). A +1.0% five-day gross gives
roughly **1.5× coverage of a round trip at 5 bars and none at 21** — and the one paper claiming
survival assumes a cost **3.4× better than we have measured on our own holdings**.

**A structural break inside the fixture, dated exactly:** the 10b5-1 checkbox exists only from
**2023-04-01**. Any study using it splits its own sample.

**Look-ahead rule the runner must follow:** enter at the open of `FILING_DATE + 1`. Verified on a
filing **accepted 18:30:44 ET on its filing date** — after the close.

**Stage 0 before any return is computed: the dead-name versus live-name ticker hit rate.**

**Not measured here, and it matters:** `F2` found **no published breakdown of the insider effect by
nominal share price.** Price is the axis that has killed leads in this programme repeatedly, and
**its absence from the literature is itself worth knowing.**

---

## 3. `F3` — earnings on real announcement dates

**Verdict: PEAD does not transfer, the premium is contested, and the timing finding is the prize.**

**PEAD.** Martineau (*Critical Finance Review* 2022, 1984–2019) `[read in full]` finds it
**non-existent for all-but-microcap US stocks since 2006**, and for microcaps **since 2016**. What
survives is a five-day effect in microcaps with no analyst coverage — **the exact population the
`$5` floor deletes.** Chordia et al. (FAJ 2009, 1972–2005) `[abstract verbatim]`: **0.04%/mo in the
most liquid decile against 2.43% in the most illiquid**, with costs at 70–100% of paper profits.

**The announcement premium, and why it is only half-open.** It needs no surprise measure — 
Frazzini–Lamont forecast the announcement *month* from fiscal year-end alone `[read in full]`, so a
calendar suffices: 7–18%/yr, 72 bp/mo, 1973–2004; Barber et al. (JFE 2013) `[read in full]` 59.7
bp/mo globally, 1990–2009. **But the published US premium ends at 2004**, and
Heitz–Narayanamoorthy–Zekhnini claim it has **disappeared in the US** after the 2004 disclosure
rule, migrating to 8-K filing dates. A cited 2025 CAR paper puts it at **0.30% (1990s) → −0.30%
(2010s)** — `[UNVERIFIED]`, neither paper retrievable. **The fixture's 2010–2026 window sits
entirely inside the claimed dead zone.**

**And it may not be a new state at all.** The premium tracks the announcement-window
**idiosyncratic-volatility spike** (Barber et al., instrumented) — **under this programme's own
house rule that is not a new conditioner**, it is volatility wearing a calendar.

### 3.1 THE CONVERGENCE WORTH NOTICING — an outside measurement of our own central fact

deHaan, Shevlin & Thornock (JAE 2015, 2000–2011, **four corroborating timestamp sources**)
`[read in full]` place earnings announcements at:

```
before the open   34.6%
after the close   45.4%
during RTH         7.0%      -> ~80% land OUTSIDE regular trading hours
```

**The announcement return IS a close-to-open gap.** The programme's own most load-bearing empirical
fact is that **the edge is overnight** (D280), and this is an entirely independent measurement
arriving at a compatible place. It is corroboration of a *mechanism*, not of a *return*, and it is
recorded as such.

**The hazard that comes with it, and it is a lag audit `[L]`.** Berkman & Truong (JAR 2009)
`[summary only]`: for after-hours announcements **the return lands one trading day later**.
**Misassigning it flips the result between sessions** — which is precisely the failure mode that
killed D279's first result and inverted D280.

**Data: free and dead-inclusive, verified live.** `data.sec.gov/submissions/CIK…json` exposes
`items` (`"2.02,8.01,9.01"`), `reportDate` and `acceptanceDateTime`; **Item 2.02 runs from August
2004**. Two caveats: **Item 2.02 Instruction 4 exempts firms disclosing only via 10-Q**, and Alpha
Vantage's `EARNINGS` (which does carry `reportTime`) could not be tested for delisted coverage on
the demo key — **prior should be against it**.

**One thing to verify before building anything on it: the `acceptanceDateTime` timezone.** One
Apple case reconciles as UTC against the index page's ET string; **an SVB February filing does
not.** Check ~100 filings **across both DST regimes** before splitting sessions on that field.

---

## 4. `F4` — sizing and portfolio construction

**Verdict: equal weight is close to right, and now for a reason rather than by default.** That was
the whole point of commissioning it — the truth file's *"sizing was never chosen."*

**Why `1/N` is hard to beat here specifically.** DeMiguel–Garlappi–Uppal's critical estimation
window `[read in full]`: **>3,000 months at N=25, >6,000 at N=50** on US calibration. At 1,573 names
against ~199 months-equivalent, full mean-variance is **two to three orders of magnitude out of
reach.**

**But that negative only reaches rules that need MEANS.** The live corner is **variances-only**
weighting (Kirby–Ostdiek) — the one rule reported to beat `1/N` net of costs, at **+0.01 to +0.06
Sharpe on the paper's `1/N` base of 0.510** `[secondary source — NOT read from the paper]`.

**Vol targeting, quantified, and it dies on our own cost number.** From Moreira–Muir Table IV
`[read in full]`:

| overlay | turnover | breakeven |
|---|--:|--:|
| `1/RV²` | **73% of notional/month** | **56 bp** |
| scale by vol, not variance | 38% | 84 bp |
| plus a leverage cap | 16% | **110 bp** |

**56 bp does not survive D285's measured 33.8 bp/side. The leverage-capped variant might** — and
that is the only cell of this axis worth a premise number.

**The benefit is drawdown, not return, and the literature is mostly negative on the return half.**
Harvey et al. report a Sharpe gain only in equity/credit `[UNVERIFIED — see §5]`;
Barroso–Santa-Clara's 0.53→0.97 is a **kurtosis fix** (18.24→2.68) `[snippet only]`; Cederburg et
al. (103 strategies) and Barroso–Detzel are decisive negatives — vol management fails OOS and, net
of costs, **everything but the market gives zero alpha** `[snippet only]`.

**The drawdown barrier has a closed-form answer.** Grossman–Zhou: size the Kelly fraction of the
**cushion** `(W − λM)`, not of equity `[snippet only]`. Busseti–Boyd give the computable bound
`Prob(W_min < α) < α^λ`, `λ = log β / log α` `[read in full]` — **0.047 against 0.035 growth at
matched risk versus fractional Kelly**, and a 10% cap on a 30% drawdown costs about a quarter of
growth.

**The real lever is cost-aware construction, not weighting.** Novy-Marx–Velikov `[read in full]`:
a 10%/20% buy/hold band cuts **turnover −41% and costs −42%**. Theory (Abel–Eberly) says band width
scales with the **cube root** of cost — so **bands should be wide, and should NOT be tuned against
a noisy cost estimate.** That is a design rule this programme can adopt without measuring anything.

**The premise number to compute first, and it is cheap: the arithmetic ÷ harmonic mean of
held-name realised volatility. If it is ≈1.0 the entire inverse-vol axis is dead before a runner
exists.** `[NOT COMPUTED — this record is research only.]`

---

## 4a. `F6` — corporate supply events

**Ranking returned: (1) buyback EXECUTION, (2) lockup expiries, (3) SEOs, (4) spin-offs — dead.**

**Three of the four fail on the same wall, and it is not decay — the supply event resolves
OVERNIGHT.** Buyback announcement (**2-day CAR 1.7% since 2000, down from 4.7% in 1999**), SEO
(**−2 to −3%**) and spin-off (**~3%**) all land in the open. **On daily bars we are a bar late by
construction.** This is the same structural fact that `F3` measured from the earnings side and that
D280 found from ours — **and here it cuts against us rather than for us**, because it is the
*announcement* that is overnight, not the *drift*.

**MY COMMISSIONING PREMISE FOR BUYBACKS WAS WRONG, AND THIS IS THE CORRECTION.** I sent `F6` to look
at granular buyback disclosure. **The 2023 rule that would have produced it — daily table, Item
601(b)(26), Inline XBRL — was VACATED by the Fifth Circuit on 2023-12-19 before producing usable
data**, with technical amendments (Rel. 34-99778) effective 2024-04-08. **The entire fixture is
governed by pre-existing Item 703: monthly aggregate, HTML, untagged, filed 40–45 days after
quarter end.** Everything I assumed about the resolution of this data was wrong.

**And the long-run drift is refuted by the literature the lead rests on.** Fu & Huang (*Management
Science* 2016) `[snippet/abstract]`: post-repurchase **and** post-SEO drift *"disappear for the
events in 2003–2012."* Mitchell & Stafford kills the methodology behind the older results.
**Spin-offs have a direct peer-reviewed refutation of their own mechanism** — Abarbanell, Bushee &
Raedy (*J. Business* 2003) found the mandate-driven rebalancing **is not associated with abnormal
price movement**, which is the forced-selling story this lane was commissioned on.

**Event counts, `F6`'s in-universe estimates against a 100-event gate:**

| family | US-wide 2010–2026 | in-universe estimate | verdict |
|---|--:|--:|---|
| buyback **execution** | — | **~15–35k firm-quarters** | it is a **STATE, not an event** |
| buyback announcements | ~12–20k | 2,000–5,000 | passes |
| SEOs | ~15k FROs | 500–1,500 | passes |
| lockups | ~4,000 IPOs | 200–500, **usable 100–250** | **passes, barely** |
| spin-offs | ~250–400 | **50–150** | **fails the gate** |

**The cost regime splits them.** Lockups and SEOs both concentrate in the **sub-$10 tail** — where
cost in bp is worst and where this programme has been killed before. **Buybacks are the one family
on the right side: profitable, higher-priced mid/large caps.**

**Lockups have no post-2010 US replication.** Field & Hanka is **1988–1997**, −1.5% over three days
with over half on unlock day `[paper not opened — SSRN 403, JF paywalled]`. `F6` found **no
post-2010 US peer-reviewed replication and says so as a gap in the literature rather than as
evidence the effect died.** Worse for construction: **modern deals engineer the single date away**
(staggered tranches, 20–50% price triggers, blackout pull-forward), so **"+180 days" is often simply
the wrong date.**

**The one lane it recommends, and it is a conditioner rather than a signal.** Buyback *execution* as
a **state** on the existing reversal book. Premise check: `P(repurchase > 0 in q+1 | q)` against the
base rate, flagged-bar coverage under an acceptance-timestamp+1 rule, price/ADV/dead-alive
composition, and repurchase dollars as a share of quarterly dollar volume. **Data route:** XBRL
`PaymentsForRepurchaseOfCommonStock` is free, tagged and dead-inclusive **but contaminated by RSU
tax-withholding retirements**; Item 703 column (c) is the clean discriminator and is **HTML-only**.
**A free bonus:** the Item 703 footnote gives plan announcement dates **retrospectively** —
look-ahead-safe, and it removes the need to hunt 8-Ks.

---

## 4b. `F5` — retail execution cost

**Verdict: honestly saveable, 0.5–1.5 bp/side as the programme currently executes. Not 5, not
10.** That is the answer to the question the lane was commissioned on — *a basis point saved is
worth as much as a basis point found* — and **the honest answer is that there are not many to
save.**

**Why the published price-improvement numbers do not apply to us, and this is the good part.** Two
peer-reviewed effective/quoted measures exist: a population Rule 605 study (Dyhrberg, Shkilko &
Werner, JFE 2025) giving **0.97 at exchanges and 0.76 at wholesalers**, and a **real-money
85,000-order broker experiment** (Schwarz, Barber, Huang, Jorion & Odean, JF 2025) putting **IBKR
Pro at E/Q ≈ 0.62** — the worst price-improver of five brokers tested, but far better than pure
exchange execution.

**None of it reaches an auction-only book.** IBKR's own Rule 606 filing states it receives **no
order-flow payment for On Open and On Close orders**, and that the auction print *"typically
match[es] pre-close bid or ask"* — **a full half-spread. The cost model's full-half-spread charge is
therefore CORRECT at the auction**, and the programme's existing assumption survives contact with
the literature.

**The one concrete, actionable change: switch Fixed → Tiered.** 0.0035/share + venue against
0.0050/share; at auctions Tiered is 0.0047 (NYSE MOC/MOO) against 0.0050 Fixed. **The real win is
the per-order minimum — $0.35 against $1.00.**

**And this corrects a number already recorded in this programme.** The recorded lead says the
minimum binds below *"$2,100 notional"*. **The rule is a SHARE COUNT, not a notional**: Fixed binds
below **200 shares**, Tiered below **100 shares**. `$2,100` is right only at a $10.50 share price.
While binding, commission in bp is `10,000 / notional` — so **a $2,000 order pays 5.0 bp Fixed
against 1.75 bp Tiered.**

**Would any verdict move? Two go UNRESOLVED and neither flips.** D285's 11.36 bp breakeven (E/Q 0.62
gives 10.5 bp — **but only under continuous execution, and only if Corwin–Schultz is unbiased,
which §1.6 says it is not**) and the widest-two-deciles cell (216.6 bp round trip → ~134 bp).
**The 1.92 bp intraday cell STANDS: Tiered gives 1.81 bp against a 1.06 bp bar. It still loses at a
zero spread.**

**A dated freebie, and it is weeks away.** Amended Rule 605 compliance was **1 August 2026**;
IBKR's **first broker-level report (August 2026), with E/Q by order size and an S&P/non-S&P split,
is due published before the end of September 2026.** That is a free, primary, broker-specific
measurement of the exact quantity this lane had to estimate.

**One thing that will NOT arrive:** the tick-size and access-fee amendments are **delayed to
November 2027** and exclude stocks quoted wider than 1.5 cents — **i.e. precisely the programme's
problem names.**

---

## 4c. `F1` — index reconstitution

**Verdict: the territory's premise is INVERTED, and that inversion is the result.**

**I commissioned this lane on the reasoning that forced index flow happens in large, liquid,
high-priced names — the one population our per-share cost model can trade.** The evidence says
**large-and-liquid is exactly where the effect is dead, and where it survives is exactly where our
cost model is worst.** That is my premise, not the agent's, and it was wrong.

**The decay is real and sourced.** Greenwood & Sammon, *Journal of Finance* 80(2), April 2025: S&P
500 additions **7.4% (1990s) → 0.3% (2010–2020)**; deletions from large negative → **+0.1%**.
Announcement→effective return in 2010–2020 was **+0.209%, insignificant**, against +3.68% in the
1990s. **The leg that died is the forced-flow leg.** The only significant residual is the
announcement jump, which requires anticipating a discretionary committee.

**Two non-obvious findings survive, and they are why this is not simply a negative.**

1. **The S&P 500 zero is a COMPOSITION ARTEFACT.** Over 80% of changes are now MidCap↔500
   migrations that net out. **Direct additions still averaged +5.40% and direct deletions −6.86% in
   2010–2020.**
2. **The effect lives down-cap.** In the 2010s: **S&P SmallCap 600 additions +6.03%, deletions
   −12.18%; MidCap additions +5.67%; Russell 2000 direct additions +3.15%** — all significant, while
   Russell 1000 additions (t = 1.67) and the Nasdaq 100 are not.

**Four reasons `F1` gives for not reading that as a green light, and they are good ones.** The
windows **start before the announcement**, so they contain the selection that caused the index
change; **nothing is net of costs**; the flow is a **closing-auction event** — roughly **30% of the
month's volume on one print** — which **daily bars cannot resolve**; and the one bullish
"hundreds of bp" claim is **a game-theory model, not a measurement**.

**THE GENUINE GAP, and it is ours specifically.** Every modern study **excludes names "delisted for
reasons other than acquisition" — which drops ~66% of S&P 500 deletions.** Greenwood & Sammon say
outright they skip Russell 3000 deletions *"as these are often firms that are delisting."*
**A dead-inclusive fixture is the right instrument for a question nobody has published** — and it
lands directly on round 3's `G2`. **The `$5` floor probably removes the sample anyway**, which is
the count to get before anything else.

**Data: free and dead-inclusive for S&P, not for Russell.** `press.spglobal.com` carries
announcement date, effective date and removed names **from 2012**; PR Newswire via the **Wayback CDX
API** fills 2010–2011; Wikipedia's *Historical components* page is the skeleton — **its
`List of S&P 500 companies` sibling is current-members-only and useless**, which is the same
survivorship trap as §1.1. Siblis sells the history at ~$576/yr. **For Russell there is no free
announcement archive and no name lists before ~2015. The repo holds none of this.**

---

## 5. Sources

**Tags:** `[PEER-REVIEWED]` · `[WORKING PAPER]` · `[PRIMARY DATA DOC]` · `[SALES INSTRUMENT]` ·
`[UNVERIFIED]`. Where a brief read the full text it is marked; **everything else is an abstract,
a snippet or a secondary summary and is marked as such.** Full per-source detail, including exact
URLs, is in the briefs under [`working/leads2/`](../../working/leads2/).

### F2 — insiders

**Primary data documentation, all fetched live.** SEC Insider Transactions Data Sets and its readme
(field, trans-code and timeliness definitions); the quarterly `form345.zip` pattern **verified HTTP
200 for 2010q1–2026q2, 66 files, 8–14 MB each** (the newest quarter sits on a different path);
EDGAR Webmaster FAQ (**10 req/s**, User-Agent required); Accessing EDGAR Data; EDGAR APIs; Final
Rule Release 33-11138 and the small-entity compliance guide (**Forms 4/5 compliance 2023-04-01**);
one worked look-ahead example, accession `0001140361-26-035636`, **accepted 18:30:44**.

**Peer-reviewed.** Cohen, Malloy & Pomorski, *Decoding Inside Information*, JF 67(3) 2012
`[full text read via NBER w16454]` · Jeng, Metrick & Zeckhauser, REStat 85(2) 2003
`[abstract only — PDF extracted poorly]` · Lakonishok & Lee, RFS 14(1) 2001 `[UNVERIFIED — the
widely-quoted 4.8% not confirmed against the paper]` · Rozeff & Zaman, *J. Business* 61(1) 1988 ·
Cziraki & Gider, *Rev. Finance* 25(5) 2021 `[full text read]` · Oenschläger & Möllenhoff, FRL 72(C)
2025 `[abstract only — paywalled]` · Jagolinzer, *Management Science* (10b5-1) · *Insider Trading
After the 2022 Rule 10b5-1 Amendment*, JAE 2026 `[abstract only]` · Alldredge et al., JFR 2019 ·
Schroeder & Krause, *J. Investing* 2026 `[paywalled — read only via a Swedroe summary]` · Hou, Xue
& Zhang, *Replicating Anomalies*.

**`[UNVERIFIED]`.** Ozlen & Batumoglu, SSRN 5966834 — **SSRN 403 twice; the load-bearing claim of
the decay section and it is unverified**; the one secondary source reached carried the quote and no
sample, universe or method · an Aalto master's thesis replicating CMP on 2008–2024 (**403 twice,
zero numbers verified**) · arXiv 2602.06198 on microcap insider signals `[low confidence]` · a
QuantInsti blog event study · Kang, Kim & Wang cluster magnitudes (**from a search snippet; sample
period not established**).

**`[SALES INSTRUMENT]` — cited as evidence of CROWDING only, never of returns.** VerityData /
InsiderScore and its own literature review · 2iQ Research · Quiver Quantitative. Plus two
primary-source data points on crowding: the Direxion insider-sentiment fund liquidation notice on
EDGAR, and Invesco's 42-fund closure including NFO `[UNVERIFIED, trade press]`.

### F3 — earnings dates

**Read in full.** Frazzini & Lamont, NBER WP 13090 `[WORKING PAPER]` · Barber, De George, Lehavy &
Trueman, JFE 108(1) 2013 · Savor & Wilson, Dec 2011 draft `[WORKING PAPER]` · Martineau, *Rest in
Peace Post-Earnings Announcement Drift*, CFR 11(3–4) 2022 · **deHaan, Shevlin & Thornock, JAE 60(1)
2015 — the source of the 34.6/45.4/7.0 timing split** (note: the host is a data vendor; the paper is
not) · Lou, Polk & Skouras (2024), which **contains no earnings analysis at all — market-level
only**, recorded so nobody re-fetches it.

**Abstract or summary only.** Chordia, Goyal, Sadka, Sadka & Shivakumar, FAJ 65(4) 2009
`[abstract verbatim; tandfonline 403]` · Ng, Rusticus & Verdi, JAR 46(3) 2008 · Berkman & Truong,
JAR 47(1) 2009 — **the source of the day-0 hazard** · Cohen, Dey, Lys & Sunder, JAE 43 2007 ·
Christensen, Timmermann & Veliyev, arXiv 2601.08962 `[PDF exceeded the fetch size limit]` ·
Bogousslavsky, JFE 141(1) 2021 `[not read; no earnings decomposition found]` · a Pacific-Basin
Finance Journal 2023 paper `[title/abstract snippet]`.

**`[UNVERIFIED]` — and both carry the section's most consequential claim.**
Heitz, Narayanamoorthy & Zekhnini, *The Disappearing Earnings Announcement Premium*, SSRN 3296537
(**SSRN 403; Rotman mirror 500 twice; Semantic Scholar 429** — abstract taken from an author's own
page) · Heater et al., CAR 2025 (**Wiley 403** — the **0.30% → −0.30%** figure is unverified) ·
Chan & Marsh, SSRN 4765828, on overnight PEAD and 8-K disclosures (**SSRN 403**).

**Primary data documentation, fetched live.** SEC Form 8-K General Instruction B and **Item 2.02
with its Instructions, read verbatim** · EDGAR APIs (submissions JSON, bulk `submissions.zip`,
nightly ~3 a.m. ET) · Accessing EDGAR Data · **the delisted-issuer verification on SVB Financial,
CIK 0000719739** · the timezone reconciliation pair (Apple submissions JSON against its index page)
· Alpha Vantage `EARNINGS` and `EARNINGS_CALENDAR` live responses and API docs.

**`[SALES INSTRUMENT]`.** sec-api.io's Item 2.02 dataset (its survivorship-free claim is consistent
with what was verified directly on EDGAR, **but it is a vendor claim about a paid product**) ·
Quantpedia · Alpha Architect (summarises Barber et al., which was read directly). Plus one
`[UNVERIFIED THIRD-PARTY BLOG]` on Alpha Vantage delisted coverage, which addresses `LISTING_STATUS`
only and says nothing about fundamentals for delisted names.

### F4 — sizing

**Read in full (PDF body extracted and read).** DeMiguel, Garlappi & Uppal, *Optimal Versus Naive
Diversification* (conference version of RFS 2009 22(5)) — **all the estimation-window numbers** ·
Novy-Marx & Velikov, *A Taxonomy of Anomalies and their Trading Costs*, NBER w20721 / RFS 2016 —
**all the no-trade-band numbers and the Abel–Eberly cube-root result** · Busseti, Ryu & Boyd,
*Risk-Constrained Kelly Gambling*, *J. Investing* 2016 — **the `α^λ` bound and Tables 1–3** ·
Moreira & Muir, *Volatility-Managed Portfolios*, JF 2017 — **Table IV turnover and breakeven** ·
Magdon-Ismail & Atiya, *An Analysis of the Maximum Drawdown Risk Measure*, Risk 2004 — **the E[MDD]
and Calmar closed forms** · Curran, O'Sullivan & Zalla, arXiv 2005.03204v4 — the **N ≈ 10** design
constraint.

**Read via an HTML summariser — one step weaker than a reading.** *Fragility of Minimum-Variance
Portfolios*, arXiv 2607.18624 · *Which Portfolios? The Construction Dependence of Factor Model
Performance*, arXiv 2606.19550 (**pricing errors on identical stock sets range ~10 bp to 490 bp
purely on weighting choices; no cost treatment**).

**`[snippet only]` — numbers NOT verified against the paper.** Cederburg, O'Doherty, Wang & Yan,
JFE 138(1) 2020 · Barroso & Detzel, JFE 140(3) 2021 · Barroso & Santa-Clara, JFE 2015 (the
0.53→0.97 and kurtosis figures) · **Kirby & Ostdiek, JFQA 47(2) 2012 — the 0.510 base and the
0.52–0.57 range come from a secondary literature review, NOT the paper; verify before citing** ·
Grossman & Zhou, *Math. Finance* 3 1993, plus its published counterexample · Gârleanu & Pedersen,
JF 68(6) 2013 · Novy-Marx & Velikov, *Comparing Cost-Mitigation Techniques*, FAJ 75(1) 2019 ·
Detzel, Novy-Marx & Velikov, JF 78(3) 2023 · Brandt, Santa-Clara & Valkanov, RFS 22(9) 2009 · Hou,
Xue & Zhang, RFS 2020 · Plyakha, Uppal & Vilkov · Asness, Frazzini & Pedersen, FAJ 68(1) 2012
(**note: the authors are AQR principals and AQR sells risk-parity products**).

**`[UNVERIFIED]`, and each one is load-bearing somewhere above.**
**Harvey, Hoyle, Korgaonkar, Rattray, Sargaison & Van Hemert, *The Impact of Volatility Targeting*,
JPM 2018 — NOT A SINGLE NUMBER COULD BE VERIFIED.** SSRN, Alpha Architect and QuantPedia all
returned 403 or contentless pages; the only page reachable was **Man Group's own**
`[SALES INSTRUMENT]` — *the authors' employer* — which gives the qualitative findings, **no
figures, and no turnover or transaction-cost discussion at all.** ·
**Maillard, Roncalli & Teiletche, JPM 36(4) 2010 — the author's own PDF failed TLS verification.**
The constant-correlation collapses are stated from snippets plus standard derivation; see §1.2 for
why that particular claim still stands · **MacLean, Ziemba & Blazenko — `[UNVERIFIED AND
INTERNALLY INCONSISTENT]`**: two secondary sources gave incompatible half-Kelly figures (75% vs 50%
volatility reduction); cite neither without reading *Management Science* 1992 ·
DeMiguel, Martín-Utrera & Nogales, JF 2024 — **403; title known only. `F4` names it as the most
likely counterweight to the vol-targeting negatives and the first thing to read if that axis is
pursued.**

**`[SALES INSTRUMENT]`, none used for a number.** MSCI weighting commentary · Man Group ·
ReSolve/Invest Resolve · QuantPedia · Alpha Architect. **`F4` notes this area is unusually thick
with them** — vendor material dominated the first page of results for all seven of its questions.

### F6 — corporate supply events

**Primary regulatory, and this is where the lane's premise was corrected.** **17 CFR 240.10b-18**
and the SEC's Rule 10b-18 staff FAQ · **Item 703 of Reg S-K, 17 CFR 229.703** — the rule that
actually governs our whole span · **Rel. 34-97424** (Share Repurchase Disclosure Modernization,
adopted 2023-05-03) · **SEC Corp Fin announcement of 2024-02-09 following the vacatur** · **Rel.
34-99778**, technical amendments reflecting the vacatur, **effective 2024-04-08** · CRS R47397 on
the 1% repurchase excise tax · **SEC free statistics: Follow-on Registered Offerings 2000Q1–2026Q1
and IPOs 2000Q1–2026Q2, both xlsx** · EDGAR Filer Manual Vol. II ch.10 (**17:30 ET cutoff**) · Form
25 / exchange delistings · Form 10-12B `[UNVERIFIED — Wikipedia]`.

**Peer-reviewed — the negatives are the strong ones.** **Mitchell & Stafford, *J. Business* 73(3)
— the strongest methodological negative** · **Fu & Huang, *Management Science* 62(4) 2016 — the
strongest empirical negative, covering repurchases AND SEOs** · **Abarbanell, Bushee & Raedy,
*J. Business* 76(2) 2003 — the direct refutation of the spin-off forced-selling mechanism** ·
Ikenberry, Lakonishok & Vermaelen · Manconi, Peyer & Vermaelen, JFQA 54(5) `[non-US sample]` ·
Ben-Rephael, Oded & Wohl · Dittmar & Field, JFE `[abstract only]` · Hillert, Maug & Obernberger,
JFE 119(1) · Busch & Obernberger, RFS 30(1) · Cusatis, Miles & Woolridge, JFE 1993 · McConnell &
Ovtchinnikov, JOIM 2(3) · Veld & Veld-Merkoulova, IJMR 2009 · Loughran & Ritter, JF 1997 · Corwin,
JF 2003 `[via secondary]` · **Field & Hanka, JF 56(2) — the lockup canon, `[paper NOT opened: SSRN
403, JF paywalled]`** · Brav & Gompers, RFS 16(1) · Bradley, Jordan, Roten & Yi, JFR · Ofek &
Richardson · Gibbs & Hao, JBF 88 `[PDF unreadable]` · a JRFM 13(8) paper `[low-tier,
single-sourced]`.

**Corporate-action documentation — the source of §1.4.** **CRSP, *Factor to Adjust Price*, and CRSP
Calculations** · Nasdaq *Corporate Actions and Events Manual — Equities* `[not read — PDF
unreadable]` and its spin-off index handling page `[fetch failed]` · Xignite/QUODD corporate-actions
handling `[VENDOR DOC]`.

**`[PRACTITIONER]`, on deal terms rather than returns.** Cooley CapitalXchange on early lock-up
releases · Mayer Brown lock-up market trends `[not read]` · Debevoise on the Fifth Circuit vacatur.

**`[SALES INSTRUMENT]` / `[UNVERIFIED]`, none used for a number.** Wall Street Horizon's
Birinyi-derived buyback counts (**figures unreconciled — `F6` says do not cite**) ·
stockanalysis.com spin-off lists (counts only) · assorted spin-off explainers · a CBS student
lockup study.

**`F6`'s own nine unverified items** include Field & Hanka's sample size (1,948 vs 3,217 — three
PDFs would not render), Ritter's per-year IPO counts, US buyback announcement counts per year
(**the only figures found were vendor-derived and mutually inconsistent**), and the share of a broad
US panel repurchasing in a given quarter — **which is one of the things its own premise check
measures.**

### F5 — execution cost

**Primary regulatory, all fetched 2026-09-09.** SEC press release 2024-32 and **final rule 34-99679**
(Rule 605 amendments) · **SEC staff Rule 605 FAQ, dated 2026-04-01, compliance 2026-08-01** ·
Federal Register extension of the compliance date · **fact sheet and final rule 34-101070** (tick
sizes, access fees) and the small-entity guide · **exemptive order 34-104172** · **Chairman Atkins'
statement of 2026-06-11 moving compliance to the first business day of November 2027** ·
**NYSE *Opening and Closing Auctions Fact Sheet* — the 3:50 pm MOC/LOC cut-off** · **Nasdaq
*Closing Cross FAQ* — MOC 3:55, LOC 3:58, IO 4:00**.

**Broker official documentation `[BROKER OFFICIAL DOC]`, all fetched 2026-09-09.** **IBKR's Rule
606a report, Q2 2025 — the source of "no payments … for executions resulting from On Open and On
Close orders"** · the US stock commission schedule (Fixed/Tiered/Lite, minimums, maximums,
pass-through fees) · per-venue fee pages for NYSE, NASDAQ/INET, Arca, IEX and the IBKR ATS ·
alternate-exchange commissions · MidPrice and Adaptive Algo pages · the Rule 605 report index.

**Peer-reviewed.** **Dyhrberg, Shkilko & Werner, *The Retail Execution Quality Landscape*, JFE 2025
— E/Q 0.76 wholesalers against 0.97 exchanges** · **Schwarz, Barber, Huang, Jorion & Odean, *The
"Actual Retail Price" of Equity Trades*, JF 80(5) 2025 — 85,417 REAL orders; IBKR Pro E/Q ≈ 0.62;
round-trip 7.0–46.2 bp across brokers** · **Ardia, Guidotti & Kroencke, JFE 2024 — EDGE, and the
finding behind §1.6**, with code at `bidask` on PyPI · Goyal, Jegadeesh & Wu, JFQA 2026 (auction
price impact) · Bogousslavsky & Muravyev, *Who trades at the close?*, JFM 66 2023 · Battalio,
Corwin & Jennings, JF 71(5) 2016 · **Corwin & Schultz, JF 2012 — the estimator currently in use.**

**`[SALES INSTRUMENT]`, and the contradiction is recorded.** IBKR's own *Dedicated to Best Price
Execution* page claims total trading cost of **0.021% of trade value** for August 2026 — **but
benchmarked to daily VWAP**, at an average trade size of $22,288. IBKR/TAG price-improvement
marketing is **inconsistent with the JF 2025 experiment** and is not used.

**`[UNVERIFIED]`.** Per-size-bucket auction impact figures (only the pooled 17.7 bp is confirmed) ·
whether IBKR flags this account's orders as retail-designated, and whether IEX routing can be forced
from the API · **any quantified price improvement for MidPrice, Pegged-to-Midpoint, D-Peg or the
Adaptive Algo — IBKR publishes none** · current-year SEC Section 31 and FINRA TAF rates, taken from
IBKR's page rather than the regulators' own advisories.

### F1 — index reconstitution

**Read at source (PDF text extracted).** **Greenwood & Sammon, *The Disappearing Index Effect* —
three vintages, and the distinction matters.** Published in *Journal of Finance* **80(2), April
2025, 657–698** `[abstract only — Wiley 403]`; **HBS WP 23-025, revised November 2023 — READ AT
SOURCE**, and the source of the Russell/MidCap/SmallCap table in §4c; **NBER w30748, December 2022 —
READ AT SOURCE**, and the source of the decay tables. **The user-recalled "7.6% → under 1%" is the
earlier NBER vintage and the 7.4% → 0.3% is the published one — both correct, different
revisions.** · Tasitsiomi, arXiv 2506.21775 `[WORKING PAPER — a game-theory MODEL, not an empirical
study; this is the "hundreds of bp" claim and it is labelled]` · a Columbia student paper, arXiv
2412.12539 `[F1 recommends discarding it]`.

**Primary data documentation — FTSE Russell / LSEG.** *Russell US Equity Indexes, Construction &
Methodology* v7.2, August 2026 · the reconstitution calendar and June 2026 summary-of-changes ·
**two press releases that disagree on the semi-annual date — 2025-01-16 says November, the December
2025 update says December.** Recorded because a phase counter that takes the wrong date is wrong
for everything after it.

**Peer-reviewed.** Madhavan, FAJ 59(4) 2003 `[not read at source]` · Chang, Hong & Liskovich, RFS
28(1) 2015 `[not read at source — SSRN 403]` · **Wei & Young, *Critical Finance Review* 13(1–2) —
the strongest published negative on the Russell identification**, with replication files on OSF ·
Appel, Gormley & Keim.

**Membership history, and the survivorship trap repeats.** `press.spglobal.com` from 2012
`[PRIMARY]` · PR Newswire via the **Wayback CDX API** for 2010–2011 · Wikipedia *Historical
components of the S&P 500* as a skeleton — **and its `List of S&P 500 companies` sibling is
current-members-only and must not be used**, the same failure mode as §1.1's
`company_tickers.json` · Siblis Research at ~$576/yr `[SALES INSTRUMENT]`.

---

## 6. Blocks encountered — the tool and the response, not the host

Per the house rule that a logged block names the tool. **This is a record of what the fetcher got,
not a claim that any publisher blocks anyone.**

| tool → host | response |
|---|---|
| WebFetch → `papers.ssrn.com` / `www.ssrn.com` | **HTTP 403, repeatedly, across all three briefs** |
| WebFetch → `onlinelibrary.wiley.com` | HTTP 403 |
| WebFetch → `www.sciencedirect.com` | HTTP 403 |
| WebFetch → `www.tandfonline.com` | HTTP 403 |
| WebFetch → `www-2.rotman.utoronto.ca` (PDF) | HTTP 500, twice |
| WebFetch → `api.semanticscholar.org` | HTTP 429 |
| WebFetch → `arxiv.org/pdf/2601.08962` | exceeded the 10 MB fetch limit (abstract page served) |
| WebFetch → `alphaarchitect.com`, `quantpedia.com` | 403 or contentless |
| TLS → `thierry-roncalli.com` | certificate verification failure |
| Alpha Vantage `demo` key | serves IBM only; **delisted coverage of `EARNINGS` could not be tested** |

**Where a PDF did not parse through the fetcher and was cached locally, `F3` extracted the text with
`pypdf` and read it directly** — that is how six of its full readings were obtained.

**Safety.** All three briefs report the same thing explicitly: **no page, PDF or search result
contained text addressed to the researcher or instructing any action.** Nothing was downloaded
beyond cached PDFs and a handful of HEAD requests to `sec.gov` to verify file existence and size;
no forms submitted, no accounts created, no credentials entered.

---

## 7. What this record does not claim

- **No number here was measured on this fixture.** The only figures re-stated from our own record
  are D285's **33.8 bp/side** on held names, the **10.06** effective independent instruments, the
  book's **Sharpe 0.92**, and the fixture's **1,580 names / 35.7% dead** — all quoted from
  `CLAUDE.md` and [`FINDINGS.md`](../FINDINGS.md), none recomputed here.
- **Nothing was backtested, no null was drawn, no cell was scored, no candidate exists.**
- **The premise numbers named in §2, §3 and §4 have NOT been computed.** They are stated so that
  whoever runs a lane knows what would kill it before designing anything.
- **No territory below is closed.** `F1`'s premise being inverted kills *my reasoning for choosing
  it*, not the territory — and `F1` itself names a question **nobody has published**, on deletions
  of names that delist, for which a dead-inclusive fixture is the right instrument. Under
  [R15](../RULES.md#r15) closure is the principal's, not mine.
- **Two of my own commissioning premises were WRONG and are recorded as such**: the buyback
  granular-disclosure rule was vacated before producing data (§4a), and index flow does not live in
  large liquid names (§4c).
- **Both books are unchanged. Nothing is closed and nothing is admitted** — that remains the
  principal's call under [R15](../RULES.md#r15).
