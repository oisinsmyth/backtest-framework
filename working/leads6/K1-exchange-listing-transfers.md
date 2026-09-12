# K1 — Exchange listing transfers (Nasdaq ↔ NYSE, and to/from NYSE American)

**Round 6 lead brief. External evidence only.** I have no access to this
programme's fixture and claim nothing about it. Under
[R15](../../docs/RULES.md#r15) nothing here closes or admits anything.

Written 2026-09-10. Every source is tagged by TYPE and by HOW WELL I ESTABLISHED
IT. Counts I produced myself are marked **[OWN CENSUS]** and every parameterised
harvest carries a negative control beside it.

**Evidence promoted into `data/`** (the 2,700-document raw SEC cache stays in
`temp/`):

| file | what it is |
|---|---|
| `data/k1_exchange_transfers_census.tsv` | the 343-row directed transfer census, 2010–2026Q3 |
| `data/k1_exchange_transfers_census.log` | the census run including every control and the listed events |
| `data/k1_exchange_transfers_prices.tsv` | the 213 recovered prices and dollar volumes |
| `data/k1_exchange_transfers_fts_census.log` | the EDGAR full-text phrase census and the earnings co-filing test |
| `data/k1_exchange_transfers_fts_tiermove.log` | the intra-Nasdaq tier-move share |
| `data/k1_harvest_edgar_form_index.py` | stage 1: harvest 71 quarterly `form.gz` indices |
| `data/k1_fetch_sec_docs_sharded.py` | stage 2: the polite sharded SEC fetcher |
| `data/k1_pair_8a12b_with_form25.py` | stage 3: pairing plus the placebo control |
| `data/k1_classify_transfer_direction.py` | stage 4: direction classification, self-test and deliberate break |
| `data/k1_transfer_price_distribution.py` | the price/dollar-volume and survivor-map measurement |
| `data/k1_fts_earnings_cofiling.py`, `data/k1_fts_tier_move_share.py` | the two full-text-search measurements |

One correction recorded rather than silently fixed: stage 1 split the fixed-width
index line two characters early, so `date` and `file` together hold `line[86:]`.
Stage 3 re-splits them (`K1_pair.py:TAIL`). No row was lost — 77,101 parsed, 0
unparseable — but the harvest file as written is wrong in those two columns and the
downstream scripts carry the repair.

---

## 0. The one-paragraph answer

**The territory survives the earnings confound — decisively, and it is the only
round-6 signal lane I can say that about — and it dies on count and on
mechanism.** Transfer 8-Ks co-file with Item 2.02 in **1.7–3.6%** of cases
against **36–80%** for J1/J2's events, so the event really is announced in its
own filing. **It also passes the price screen in its best direction**:
Nasdaq→NYSE transferees have a median close of **$31.51** with **none below $5**.

**It dies on count.** My own dead-inclusive EDGAR census over 2010-01 to 2026-Q3
finds **343 operating-company common-equity transfers in 16.7 years = 20.5/year
across all four venues and both directions**, of which **7.0/year Nasdaq→NYSE** and
**6.9/year NYSE→Nasdaq**. After a $5 close plus $1m dollar-volume screen that is
**≈6.7 and ≈5.0 events per year**, and both are upper bounds. The peer-reviewed
count for the reverse direction is **53 switches in 16 years** (Dang, Michayluk &
Pham 2018). The exchanges' own marketing, which has every incentive to inflate,
agrees: NYSE claims **20** operating-company transfers in for 2023 and **five** for
all of H1 2025.

**And the mechanism question resolves badly: the Nasdaq Composite
methodology says a security "must be listed exclusively on the Nasdaq Stock
Exchange" and that securities are added and removed DAILY, so 100% of
Nasdaq↔NYSE transfers are simultaneously index-membership changes**, and the
Nasdaq-100 carries an explicit "recently switched its listing" fast-entry rule
and an explicit "transferring to an ineligible exchange" deletion trigger. Index
membership is permanently excluded ground. The honest qualification is that the
*economically material* index event (NDX, QQQ ≈ $490bn) touches only the handful
of top-40-by-cap switchers, while the 100%-overlap event (Composite, ONEQ ≈
$10.4bn over >2,000 names) carries trivial flow — so this is not a pure duplicate
of the index lane, it is a tiny-N lane whose largest members are duplicates.

Separately, and this is the part a reader would otherwise get wrong: **the $5
screen is free for the up-move and fatal for the down-move, and the listing
standards explain why.** The standard a transfer must clear is **$4.00**, not $5
(NYSE Rule 102.01C(II) for currently-traded companies: $200m market cap and a
$4.00 close for 90 consecutive trading days before applying; Nasdaq $4 bid), and
**NYSE American only moved to $4.00 in 2026 — it was $2/$3 for the whole 2010–2025
sample.** Measured outcome: 0.0% of Nasdaq→NYSE transferees were below $5, against
37–44% of the moves down to NYSE American.

**What I would tell the principal in one line:** this is the first round-6 signal
lane that is clean on the earnings confound and clean on price, and it still
cannot be run, because 5–7 events a year in the best direction is not a sample and
because the largest events in it are Nasdaq-100 flow events wearing a different
name. The reusable output of this lane is not a signal — it is the
**transfer-identification recipe in §5**, which is free, point-in-time,
dead-inclusive, and would serve any future study that needs to know which venue a
name was listed on at a given date.

---

## 1. What is documented about returns around a listing transfer

### 1.1 The classic era, and it is genuinely an era

| source | sample | what it found |
|---|---|---|
| Kadlec & McConnell (1994) *J. Finance* 49(2) — [PEER-REVIEWED] [abstract only] | Nasdaq→NYSE, 1980s | "stocks earned abnormal returns of 5 percent in response to the listing announcement"; listing associated with more shareholders and lower bid-ask spreads; cross-sectional support for **both** investor recognition (Merton 1987) **and** liquidity (Amihud–Mendelson 1986) |
| Sanger & McConnell (1986) *JFQA* — [PEER-REVIEWED] [abstract only] | OTC→NYSE, 1966–1977, spanning the birth of NASDAQ | positive announcement abnormal returns **pre-NASDAQ**; "in the post-NASDAQ period, abnormal returns in response to listing announcements are statistically significantly lower"; in both sub-periods positive returns *before* listing and **significant negative returns immediately after listing** |
| Elyasiani, Hauser & Lauterbach (2000) *Financial Review* — [PEER-REVIEWED] [snippet only] | 895 stocks Nasdaq→NYSE/Amex, 1971–1994 | reductions in % spread and in Hasbrouck pricing-error volatility "can explain most of the stock market's positive response to exchange listing" |
| Dharan & Ikenberry (1995) *J. Finance* 50(5), 1547–1574 — [PEER-REVIEWED] [abstract only] | listings on AMEX/NYSE 1962–1990 | post-listing returns are **poor**; not fully explained by the equity-issuance puzzle; consistent with **managers timing their application**; the drift is in **smaller** firms and "poor post-listing performance is **not** observed in larger firms" |

Read these four together and the classic result is already hostile to this
programme: the up-move's announcement gain was a **1980s dealer-market
liquidity** story, the drift after it is **negative**, and the drift is absent in
exactly the large, tradable half.

### 1.2 What survives after the reforms

| source | sample | what it found |
|---|---|---|
| Jain & Kim (2006) *Financial Management* 35(2), 21–42 — [PEER-REVIEWED] [abstract only] | Nasdaq→NYSE, post-reform | "**Although the average Nasdaq spreads are now comparable to the average NYSE spreads**, we find that firms continue to switch from Nasdaq to the NYSE, and that they experience positive cumulative abnormal returns on listing. Using a simultaneous system of equations approach, we establish that **enhanced investor recognition mainly explains this phenomenon**" |
| Cheng (2005), *J. Corporate Finance*, "Post-listing underperformance: Is it really bad to move trading locations?" — [PEER-REVIEWED] [snippet only] | listing firms | "matched four-factor regressions demonstrate that the listing firms do **not** underperform" — a direct challenge to Dharan–Ikenberry |
| Kedia & Panchapagesan (2011) *J. Financial Markets* 14(1), 109–126 — [PEER-REVIEWED] [abstract only] | Nasdaq→NYSE movers + matched controls, 1986–1998 | "firms are more likely to move to NYSE **when they are raising external financing or engaging in acquisition activity**… firms that move to NYSE issue more debt and equity, and engage in more asset transactions following their move relative to control firms" |

**Jain & Kim is the load-bearing paper for the "does it survive" question and its
answer is the worst possible one for a tradable signal: yes, the CAR survives,
and the surviving channel is *investor recognition*, which is not a dated flow.**
Kedia & Panchapagesan is the contamination result: the transfer is *selected* by
firms that are about to issue debt/equity or do deals — **SEOs and
merger-arbitrage are both on this programme's exclusion list**, so the up-move
event set is partly a repackaging of spent ground.

**Conflict recorded, not adjudicated.** Dharan & Ikenberry (negative post-listing
drift, 1962–1990) vs Cheng (2005) (no underperformance under four-factor
matching). I would weight Cheng's direction on method — long-run abnormal-return
tests of that era are exactly what Barber–Lyon / Lyon–Barber–Tsai showed to be
badly specified — while noting Cheng has 18 citations to Dharan–Ikenberry's
several hundred, i.e. the field did not treat it as settling the matter. **Neither
is post-2010.**

### 1.3 Decay, and I could not find the post-2010 replication

**I found no study that measures announcement or effective-date abnormal returns
for US inter-exchange transfers using a post-2010 sample.** The most recent
peer-reviewed work on either direction is Dang, Michayluk & Pham (2018), and it
is a market-quality paper, not a returns paper. This is the single biggest gap in
the brief and I flag it rather than filling it with inference.

What I can establish about decay is indirect but strong and it is about the
*mechanism*, not the effect:

- **The liquidity channel was built on a spread gap that closed.** Decimalisation
  (NYSE 2001-01-29, Nasdaq 2001-04-09) plus the 1997 order-handling rules
  collapsed the Nasdaq–NYSE spread differential; Jain & Kim state the spreads are
  "now comparable".
- **Where a stock is *listed* now determines well under a third of where it
  *trades*.** FIA PTG, *Regulation NMS: A Renewed Call for Reform* (Sept 2025) —
  [PRACTITIONER] [read in full, local pypdf]: "**The primary listing exchanges had
  a combined market share of less than 30% over the first half of 2025**", "no
  exchange had more than 20% market share based on notional volume", 20 exchanges
  with SRO licences. In 2005 there were seven exchanges and "the listing
  exchanges, NYSE and Nasdaq, maintain[ed] dominant market share". A 1980s study
  of "the effect of moving where a stock trades" is measuring a variable that
  mostly no longer moves.
- **The comparable flow effect decayed to nothing.** Greenwood & Sammon, *The
  Disappearing Index Effect*, HBS WP 23-025, revised Nov 2023 — [WORKING PAPER]
  [read in full, local pypdf]: S&P 500 addition abnormal return "has fallen from
  an average of 7.4% in the 1990s to 0.3% over the past decade", deletions "only
  0.1% between 2010 and 2020", and specifically for the index that a transfer
  actually moves you in and out of: "a steady decline in the effect of being added
  to the Nasdaq 100, going from **3.9% in the 1990s to 2.6% in the 2000s and 2.0%
  in the 2010s. The deletion effects are consistently minimal, hovering near zero
  for the past 30 years**… none of these declines from the 2000s to the 2010s are
  statistically significant."

### 1.4 Cost-honest treatments

**None found.** I found no paper on US exchange transfers that nets transaction
costs out of a transfer-based trading rule. Clyde, Schultz & Zaman (1997) is the
closest thing to a cost-aware result and it is a *warning*, not a net return —
see §3.

---

## 2. THE MECHANISM QUESTION — and (c) is a large part of the answer

### 2.1 (c) Index / ETF membership: the overlap is 100% by construction

This is the part the commission asked me to say loudly, so I measured it from the
index methodologies rather than reasoning about it.

**Nasdaq Composite Index methodology** — [PRIMARY DATA DOC] [read in full, local
pypdf of `indexes.nasdaqomx.com/docs/methodology_comp.pdf`]:

> "The Nasdaq Composite Index includes all domestic and international common type
> stocks listed on the Nasdaq Stock Market."
> "**A security must be listed exclusively on the Nasdaq Stock Exchange.**"
> "There is no market capitalization eligibility criterion." / "There is no
> liquidity eligibility criterion." / "There is no float eligibility criterion."
> "**Securities that are no longer eligible are removed daily from the Index.
> Index Securities that are eligible for the Index are added daily.**"

So **every** Nasdaq→NYSE transfer is a Nasdaq Composite **deletion** and **every**
NYSE→Nasdaq transfer is a Nasdaq Composite **addition**, mechanically, with
next-day application and no size or liquidity gate. The overlap fraction asked
for in kill number (b) is, for this index, **100%**, and it is not an empirical
estimate — it is the index definition.

**Nasdaq-100 methodology** — [PRIMARY DATA DOC] [read in full, local pypdf of
`indexes.nasdaq.com/docs/Methodology_NDX.pdf`]:

> "A company must be primarily listed on a U.S. Nasdaq-affiliated exchange."
> Deletion triggers include "**Delisting or transferring to an ineligible
> exchange**"; initial-inclusion bars include "**A plan to delist or to transfer
> to an ineligible exchange**".
> "**For a company that has recently switched its listing to an eligible
> exchange:** • The company will normally be ranked and evaluated as of the end of
> its seventh trading day on the eligible exchange… • Typically, such a security
> will be added to the Index **after 15 trading days** on the eligible exchange
> **with announcement to occur after the close of business on its tenth trading
> day**."
> Fast Entry: "A security that is not already an index constituent may be added to
> the Index on an expedited basis ("Fast Entry") if its Full Market Capitalization
> ranks within the top 40 current index constituents."

So a transfer to Nasdaq by a large enough issuer creates a **dated, pre-announced
QQQ-scale flow event** on trading day 10/15 after the effective date, and a
transfer away from Nasdaq by an NDX member creates a deletion. NYSE says **"10
Nasdaq-100 companies transferred to NYSE"** since 2008 ([SALES INSTRUMENT]
[read in full] — nyse.com/listings/transfers).

**The size of the two index channels is very different and I would not collapse
them:**

| index | overlap with transfers | tracking AUM | measured effect |
|---|---|---|---|
| Nasdaq Composite | **100%**, by definition, applied daily | ONEQ ≈ **$10.4bn** over >2,000 holdings — [UNVERIFIED] [snippet only, Morningstar/etfdb] | not measured anywhere I found; per-name weight is ~0.0x% so the dollar flow on a median name is trivial |
| Nasdaq-100 | only the handful that rank top-40 by cap, plus member departures | QQQ ≈ **$490bn** — [UNVERIFIED] [snippet only] | addition **2.0%** in the 2010s, deletion **≈0**, neither decline significant (Greenwood & Sammon) |

**Verdict on (c): a transfer study in this programme is not a *pure* duplicate of
the index lane, because the 100%-overlap index carries almost no flow. But the
subset where the flow is real — large-cap moves into the Nasdaq-100 — IS the
index lane, it is the subset that would pass a price-and-dollar-volume screen, and
it is also the subset where the published effect has decayed to an insignificant
2.0%. You cannot orthogonalise: the Composite change is the transfer, with
probability one.**

### 2.2 (a) Liquidity / market quality vs (b) certification

The literature has repeatedly tried to decompose exactly this and the answer has
**flipped with the era**:

- **1971–1994 (Elyasiani–Hauser–Lauterbach):** spread and pricing-error reductions
  explain *most* of the positive response → channel (a).
- **Post-reform (Jain & Kim 2006):** spreads are comparable across venues, yet the
  CAR persists, and a simultaneous-equations decomposition attributes it to
  **investor recognition** → channel (b).
- **1986–1998 (Kedia & Panchapagesan):** the *decision* to move is endogenous to
  financing and acquisition plans → neither (a) nor (b), but selection.

So the honest reading is that **the channel the field now believes in is
certification/recognition, which has no dated flow and no mechanical release
date** — the opposite of what this programme needs. And the decomposition is
contested enough that no single paper should be leaned on.

---

## 3. The reverse direction — reported SEPARATELY, never pooled

### 3.1 NYSE → Nasdaq (large caps, cost-motivated, recent phenomenon)

- **Dang, Michayluk & Pham (2018), *J. Financial Markets* 41, 17–35** —
  [PEER-REVIEWED] [abstract only, verbatim from RePEc]:
  > "Voluntarily switching trading location from the New York Stock Exchange to
  > the NASDAQ is a new phenomenon, with **53 companies making the switch since
  > 2000**. We examine the stated reasons for the move… We find **the move to the
  > NASDAQ increases trading costs**, improves visibility, attracts more liquidity
  > providers in the long term, explaining the subsequent increase in trading
  > volume and supporting many of the management statements justifying the move."
- The first voluntary NYSE→Nasdaq move was Aeroflex in 2000; Kalay & Portniaguina
  (2001) report a positive abnormal return on it — [PEER-REVIEWED] [snippet only],
  n=1, and I would not carry a single-firm result.
- Two-thirds of NYSE→Nasdaq movers state they move to reduce trading costs and
  improve liquidity — [snippet only]; Dang et al. find costs went **up**, i.e. the
  stated motive was not realised.

**53 switches in 16 years is 3.3/year.** That is the peer-reviewed count for this
direction and it is a kill number on its own.

### 3.2 Down-moves: NYSE/Nasdaq → NYSE American, and the AMEX→Nasdaq analogue

- **Clyde, Schultz & Zaman (1997), *J. Finance* 52(5), 2103–2112** —
  [PEER-REVIEWED] [abstract only, verbatim]:
  > "forty-seven stocks that voluntarily left the American Stock Exchange from
  > 1992 through 1995 and listed on the NASDAQ… **both effective and quoted
  > spreads increase by about 100 percent** after listing on the NASDAQ. These
  > spread changes are consistent across stocks. In contrast, **excess returns are
  > positive** when firms announce a switch… **The authors are unable to explain
  > this apparent contradiction.**"

  An unresolved contradiction in the *Journal of Finance* is worth stating
  plainly: the announcement pays, and the stock becomes twice as expensive to
  trade. Against this programme's measured 33.8 bp/side on held names, a doubling
  takes the round trip from ~67.6 bp to ~135 bp.
- **Tse & Devos (2004), *J. Banking & Finance* 28(1), 63–83**, Amex↔Nasdaq both
  directions, 1992–1995 and 1998–2000 — [PEER-REVIEWED] [snippet only]; RePEc
  carries **no abstract** for it and I could not reach the full text (see §8).
- **This direction lands exactly where the commission feared.** Since early 2023
  hundreds of small issuers have been in breach of the $1 minimum bid price; "as
  of Dec. 8, 2023, **557 companies** listed on these exchanges were trading below
  $1 per share, up from fewer than a dozen in early 2021, with **464** of these on
  Nasdaq" — [PRACTITIONER] [snippet only, Bloomberg Law / Olshan]. The
  dominant modern use of transfer language is a deficiency-driven tier move, not a
  certification move (§5.3). **That is the delisting/distress anomaly, which is
  excluded ground, and it is the cheap tail.**

### 3.3 Never pool them

The two directions differ in sign of the liquidity change, in the index
consequence (Composite deletion vs addition; NDX deletion vs possible Fast
Entry), in the motive (certification/financing vs cost/visibility), and in the
price distribution. Pooling them would average a certification event against a
distress event. Nothing in this brief should be read as a single "transfer
effect".

---

## 4. Market-quality evidence after a transfer — and the two exchanges contradict each other

**This is a case where the two loudest sources are both [SALES INSTRUMENT] and
they disagree about the same event.** Recorded, not adjudicated.

| claim | source | type |
|---|---|---|
| after switching **to Nasdaq**: "spreads around **12% lower**… **35% more depth** at the NBBO"; opening-auction volatility lower by 3%, closing-auction volatility lower by 17%; exchange switches are "a unique and unbiased means of comparing listing venues" | Nasdaq Economic Research, 2020/2024 | [SALES INSTRUMENT] [snippet only — nasdaq.com blocked, see §7] |
| "**NYSE stocks are 50 to 65 bps less volatile than Nasdaq stocks** across all market conditions"; "The NYSE full day average spread size was **46% smaller than Nasdaq** in the early weeks of the sell-off"; NYSE closing process "saving investors over $10 million dollars a day" | NYSE, *New Data Confirms Stocks Trade Better on NYSE*, 2020 | [SALES INSTRUMENT] [read in full] |
| **trading costs INCREASE** after moving to Nasdaq | Dang, Michayluk & Pham (2018) | [PEER-REVIEWED] [abstract only] |
| "The NYSE offers more depth" in closing auctions; 3–5 days for the temporary price-impact component to dissipate | Jegadeesh & Wu (2022), *J. Financial Economics* 143(3) | [PEER-REVIEWED] [abstract only — SSRN PDF blocked, §7] |

**Which I would weight and why.** Dang–Michayluk–Pham and Jegadeesh–Wu, because
they are peer-reviewed and neither exchange paid for them. NYSE's own analysis
concedes it does **not** use exchange switches as the identification (it compares
all issuers above $500m market cap across venues), which is precisely the
confound Nasdaq's switch-based design avoids — so on *design* Nasdaq's is better
and on *incentive* neither is usable. Note also that Nasdaq's own headline
elsewhere is "the average spread decreased **0.3 basis points**" — a 0.3 bp
change is irrelevant against a 67.6 bp round trip, whichever direction it goes.

**The practical conclusion for a cost model: the post-transfer change in trading
cost is, in the modern era, somewhere between −12% and +(something) of a ~34
bp/side spread, i.e. a few basis points, and nobody disinterested has pinned the
sign.** It does not rescue a thin-N signal and it does not kill one either.

---

## 5. THE DATA QUESTION — how to identify transfers, free, dead-inclusive, point-in-time

I verified this by fetching real filings, not by reasoning about form names. **The
recipe works and it is genuinely dead-inclusive**, because everything below comes
out of the EDGAR quarterly full index, which is an archive of what was filed and
cannot drop a company that later died.

### 5.1 The four primary documents, and what each actually carries

Worked example, verified end to end: **PepsiCo, NYSE → Nasdaq, December 2017**
(CIK 77476).

| doc | date | what it carries | verified by |
|---|---|---|---|
| **8-K Item 3.01(d)** | 2017-12-08 | the **announcement**. Verbatim: "PepsiCo… determined to **voluntarily withdraw** the principal listing of PepsiCo's common stock… from the New York Stock Exchange… and **transfer the listing to The Nasdaq Global Select Market**. PepsiCo expects that listing and trading of its common stock on NYSE will **end at market close on December 19, 2017**, and that trading will **begin on Nasdaq at market open on December 20, 2017**." Also flags that the **Senior Notes stay on NYSE** — i.e. the issuer can be on both venues at once | [PRIMARY DATA DOC] [read in full] |
| **Form 25** (issuer-filed) | 2017-12-19 | removal from the **departing** exchange under Rule 12d2-2(c) | [PRIMARY DATA DOC] [read in full] |
| **Form 8-A12B** | 2017-12-19 | registration on the **destination** exchange. Cover page: "Name of each exchange on which each class is to be registered: **The Nasdaq Stock Market LLC**", alongside "Title of each class to be so registered: Common Stock, par value 1-2/3 cents per share" | [PRIMARY DATA DOC] [read in full] |
| **CERT** | 2017-12-19 | the destination exchange's certification of approval for listing | [PRIMARY DATA DOC] [index entry] |

**Second worked example, modern and mega-cap: Walmart, NYSE → Nasdaq, 2025** —
[PRIMARY DATA DOC] [read in full]. Press release filed as EX-99.3 to an 8-K, CIK
104169, 2025-11-20:

> "Bentonville, Ark., **Nov. 20, 2025** – Walmart Inc. (NYSE: WMT) today announced
> it will **transfer the listing of its common stock to The Nasdaq Stock Market
> LLC**… The company expects its common stock to **begin trading on the Nasdaq
> Global Select Market on December 9, 2025**, under its current ticker symbol
> "WMT"… In addition to its common stock listing, Walmart will also **transfer the
> listing of nine bonds to Nasdaq**."

**Announcement to effective date: 19 calendar days, ~12 trading days, fully
pre-announced, no uncertainty about whether or when.** And Walmart is precisely
the case where mechanism (c) bites hardest: a top-40-by-cap arrival on Nasdaq is
an NDX **Fast Entry** candidate, so the move manufactures a QQQ-scale index flow
~10–15 trading days after 9 December. **The largest transfers in this territory
are index events with extra steps.**

**A third of the modern population is SPACs, and I would not have guessed that.**
The ten highest-relevance hits for `"transfer its listing"` + `"New York Stock
Exchange"` in 8-Ks over 2023–2025 (23 hits total) are **all SPACs** — Williams
Rowland, Jaws Mustang, BlueRiver, Northern Star Investment Corp. II, Athena
Technology II, Athena Consumer — moving off the NYSE during the 2023 SPAC
wind-down, typically to Nasdaq or NYSE American, typically under continued-listing
pressure. **[OWN CENSUS]**, EDGAR FTS, control (`+ impossible phrase`) = 0. The
real operating-company names in the same window are SAIC (2024), Benson Hill
(2024), HomeTrust Bancshares, Virtu Financial, Triumph Financial, CSW Industrials,
Vince Holding, Abacus Global and Walmart (all 2025). **A text-identified transfer
set is, in the modern era, part SPAC trust-value shells at ~$10 and part
deficiency tier-moves — see §6.3.**

**Form 8-K Item 3.01 official text** — [PRIMARY DATA DOC] [read in full, local
pypdf of `sec.gov/files/form8-k.pdf`, 40pp]. The transfer trigger is paragraph
**(d)**, verbatim:

> "(d) If the registrant's board of directors, a committee of the board of
> directors or the officer or officers of the registrant authorized to take such
> action if board action is not required, has taken definitive action to cause the
> listing of a class of its common equity to be withdrawn from the national
> securities exchange, or terminated from the automated inter-dealer quotation
> system… **including by reason of a transfer of the listing or quotation to
> another securities exchange or quotation system**, describe the action taken and
> **state the date of the action**."

Paragraphs **(a), (b) and (c) are all deficiency or reprimand** notices. **That
is the central hazard in the item code: Item 3.01 mixes the transfer with the
delisting-deficiency notice, and the deficiency notices vastly outnumber the
transfers** (§5.3). The 8-K is due within four business days, and (d) requires the
**date of the action** to be stated — so the filing date can lag the true
announcement by up to four business days and **the runner must key on the stated
action date, not the filing date**. PepsiCo's filed same-day.

**Form 25 / 25-NSE structure** — [PRIMARY DATA DOC] [read in full]. Exchange-filed
25-NSEs are **structured XML** (`xslF25X02/primary_doc.xml`) carrying exactly the
three fields a census needs:

```
<exchange><entityName>Nasdaq Stock Market LLC</entityName>    <- DEPARTING exchange
<descriptionClassSecurity>0.250% Senior Notes due 2024</...>  <- class, so notes can be dropped
<ruleProvision>17 CFR 240.12d2-2(a)(2)</ruleProvision>        <- WHY it was removed
```

The `ruleProvision` is the discriminator: **12d2-2(c)** is the issuer's voluntary
withdrawal (transfers, going dark/private), **12d2-2(b)** is exchange-initiated
(deficiency delisting), and **12d2-2(a)(1)–(4)** are redemption, maturity,
expiry and substitution (notes, warrants, M&A). Issuer-filed Form 25s are
free-form HTML and need parsing.

### 5.2 A free departing-exchange key nobody needs to fetch **[OWN CENSUS]**

The 25-NSE is filed *by the exchange*, so its **accession-number prefix is the
exchange's own filer CIK**. Mapping those prefixes off 233 cached XMLs gives a
complete, zero-fetch departing-exchange key:

| accession prefix | exchange | purity in the 233-doc calibration |
|---|---|---|
| `0000876661` | NEW YORK STOCK EXCHANGE LLC | 130/133 (3 NYSE Arca leak) |
| `0001354457` | Nasdaq Stock Market LLC | 27/27 |
| `0001143362` | NYSE ARCA, INC. | 51/52 |
| `0001143313` | NYSE AMERICAN LLC / NYSE MKT / NYSE Amex | 9/9 |
| `0001417835` | Cboe BZX Exchange (ex-BATS) | 12/12 |

Applied to the full harvest: **28,544 25-NSE rows, 2009–2026Q3, departing
exchange resolvable from the prefix for 28,500 = 99.8%**; the 44 unmapped rows sit
on two prefixes with 24 and 20 rows. Measured misclassification from the
calibration is ~2–3%, concentrated in NYSE↔NYSE Arca.

**The destination exchange is NOT free after 2017.** The CERT form subtype used to
name it (`CERTNYS`, `CERTNAS`, `CERTARCA`, `CERTPAC`, `CERTBATS`, `CERTCBO`), but
**those subtypes stop dead in 2017/2018 and from 2018 every certification is the
generic `CERT` form type** — measured **[OWN CENSUS]**:

```
form          2009 2010 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 ... 2026
CERT             0    0    0    0    1    0    0    1   64  792  849 1183 ... 1158
CERTNAS        131  213  167  198  259  352  280  259  254   12    0    0 ...    0
CERTNYS        225  362  354  448  490  376  296  357  380    0    0    0 ...    0
CERTARCA         0   72  113   31   56   31   31   22    6    0    0    0 ...    0
```

So for 2018 onward the destination must come from the **8-A12B cover page**, which
is one fetch per event.

### 5.3 The 8-K Item 3.01 population is overwhelmingly NOT transfers **[OWN CENSUS]**

EDGAR full-text search over 8-Ks, 2010–2026, one query per year, **with controls
reported beside the counts**:

| control | result |
|---|---|
| impossible phrase, all years | **0** ✓ |
| a transfer phrase restricted to 1995 (pre-FTS-coverage) | **0** ✓ |
| transfer phrase AND an impossible second phrase | **0** ✓ |
| the Item 2.02 heading alone, 2015 (must be large) | 10000+ ✓ |

| phrase (8-K) | 2010 | 2015 | 2020 | 2023 | 2024 | 2025 | total 2010–2026 |
|---|---|---|---|---|---|---|---|
| `"transfer of listing"` (= the Item 3.01 **heading**, so ≈ the Item 3.01 count) | 982 | 854 | 960 | 2382 | 2317 | 1576 | **19,453** |
| `"transfer the listing"` | 69 | 31 | 40 | 186 | 153 | 111 | **1,187** |
| `"transfer its listing"` | 10 | 7 | 9 | 36 | 27 | 24 | **232** |
| `"transfer of its listing"` | 9 | 2 | 2 | 13 | 7 | 8 | **110** |
| `"voluntarily withdraw the listing"` | 0 | 0 | 9 | 11 | 16 | 13 | **111** |

Two things fall out. First, **the Item 3.01 count is ~19,450 over the window and
the transfer-language count is ~1,200 — the item code is ~95% deficiency
notices**, and its growth from ~950/year to ~2,380 in 2023 tracks the sub-$1
small-cap wave, not transfer activity. An Item-3.01 event set is a
delisting/distress event set, which is excluded ground. Second, **even the
transfer-language count surges after 2022**, which is the wrong era to believe a
certification story — see §6.3 for what that surge actually is.

### 5.4 The survivors-only ticker-map hazard, measured **[OWN CENSUS]**

See §6.4. The hazard is real and I put a number on it rather than restating it.

---

## 6. THE KILL NUMBERS

### 6.1 What the exchanges themselves claim (all [SALES INSTRUMENT])

| claim | source | established |
|---|---|---|
| "**347 companies have transferred from Nasdaq to NYSE Group**" and "$1.5T in market cap transferred… since 2000"; "**10 Nasdaq-100 companies transferred to NYSE**" since 2008 | nyse.com/listings/transfers | [read in full] |
| "**In 2023, the NYSE led the industry in listing transfers with 32 transfers** totaling $120 billion in new market capitalization. **Of those, 20 were operating companies**, nearly triple the number of operating companies transferring to competing exchanges" | NYSE, Dec 2023 | [snippet only] |
| "the NYSE has continued its four-year leadership position in **operating company transfers welcoming five companies year to date**, including Virtu (NYSE: VIRT) and QXO (NYSE: QXO)" | NYSE, *Leads Globally… First Half of 2025*, q4cdn PDF | [PRIMARY-ish] [read in full, local pypdf] |
| 34 transfers to NYSE in 2022, "the highest number since 2002", $83bn market cap | NYSE, Dec 2022 | [snippet only] |
| Nasdaq: **35** exchange transfers (2021), **29** (2022), **26** (2023), **30** (2024, >$181bn); 500 switched from NYSE by 2024, $2.7tn; "76% of all switches since 2005" | ir.nasdaq.com release titles + article snippets | [snippet only — host blocked, §7] |

**The single most informative of these is NYSE's own 2023 breakdown: 32 transfers,
of which 20 operating companies, against "nearly triple" → ~7 operating companies
going the other way.** And NYSE's H1-2025 figure is **five**. So the
operating-company total across both directions is on the order of **25–30 per
year**, from sources that want the number to look big.

### 6.2 My own dead-inclusive census **[OWN CENSUS]**

**Method.** Harvested the EDGAR quarterly `form.gz` index for **2009Q1–2026Q3, 71
of 71 quarters, 0 failures, 77,101 rows** kept on form types `25*`, `8-A12B*`,
`8-A12G*`, `CERT*`. Paired each 8-A12B with a Form 25/25-NSE on the same CIK,
then read the **destination** off the 8-A12B cover page and the **origin** off the
25-NSE accession prefix (or the issuer-filed Form 25 document), and kept only
pairs where the 8-A12B registers **common equity** and the two venues differ.

**Controls.**

| control | result |
|---|---|
| index rows for the non-existent form type `ZZ-NOTAFORM` | **0** ✓ |
| three syntactically valid but non-existent accession paths | **all HTTP 404** ✓ |
| **placebo pairing** — the same ±120d window with the CIK labels on the removal side **shuffled** | **734 pairs vs 4,943 real = 14.8%**, i.e. the raw window has a ~15% accidental-pair rate, which is why document-level classification (not the window) does the work |
| **self-test on a known event** — PepsiCo 2017 must come out NYSE→NASDAQ | **PASS**: `orig=NYSE dest=NASDAQ cls=' Common Stock, par value 1-2/3 cents per share '` ✓ |
| **deliberate break** — the destination parser run on a document with no exchange column header must return nothing, not a guess | **PASS (returned None)** ✓ |

Funnel: 3,117 pairs (|gap| ≤ 45d, 2010+) → 1,492 with both documents read → **509
where the 8-A12B registers common equity** → 508 not fund/ETF-named → **351
directed** between the three operating-company venues → **343 after removing 8
repeat filings of the same move**.

**TRANSFERS PER YEAR BY DIRECTION, operating-company common equity, 2010-01-01 to
2026-Q3 (16.7 years):**

| year | Nasdaq→NYSE | NYSE→Nasdaq | NYSE Amer→NYSE | NYSE Amer→Nasdaq | Nasdaq→NYSE Amer | NYSE→NYSE Amer | total |
|---|---|---|---|---|---|---|---|
| 2010 | 7 | 5 | 5 | 7 | 1 | 0 | 25 |
| 2011 | 10 | 7 | 8 | 1 | 2 | 0 | 28 |
| 2012 | 11 | 5 | 2 | 1 | 1 | 0 | 20 |
| 2013 | 5 | 3 | 6 | 5 | 1 | 1 | 21 |
| 2014 | 5 | 3 | 2 | 2 | 0 | 0 | 12 |
| 2015 | 2 | 3 | 1 | 0 | 0 | 1 | 7 |
| 2016 | 2 | 10 | 1 | 3 | 0 | 0 | 16 |
| 2017 | 5 | 4 | 3 | 3 | 0 | 0 | 15 |
| 2018 | 3 | 11 | 1 | 0 | 0 | 0 | 15 |
| 2019 | 2 | 6 | 3 | 2 | 0 | 0 | 13 |
| 2020 | 2 | 10 | 1 | 0 | 0 | 0 | 13 |
| 2021 | 13 | 10 | 3 | 7 | 3 | 0 | 36 |
| 2022 | 13 | 6 | 0 | 2 | 2 | 2 | 25 |
| 2023 | 14 | 6 | 0 | 1 | 3 | 9 | 33 |
| 2024 | 8 | 8 | 0 | 1 | 1 | 1 | 19 |
| 2025 | 10 | 14 | 3 | 3 | 0 | 0 | 30 |
| 2026 (to Q3) | 5 | 4 | 3 | 2 | 1 | 0 | 15 |
| **total** | **117** | **115** | **42** | **40** | **15** | **14** | **343** |
| **per year** | **7.0** | **6.9** | **2.5** | **2.4** | **0.9** | **0.8** | **20.5** |

**20.5 transfers per year across all four venues and both directions, of which 7.0
Nasdaq→NYSE and 6.9 NYSE→Nasdaq.** No trend: 2010–2013 averaged 23.5/year and
2022–2025 averaged 26.8/year, and the 2023 bulge is the 9 NYSE→NYSE American
moves, which are the SPAC wind-down (§5.1). My count lands in the same place as
NYSE's own operating-company numbers (20 to NYSE in 2023, five in H1 2025), which
is the cross-check I would want.

**Recall caveat, stated rather than buried.** 398 pairs were dropped because my
parser could not find the exchange column header on the 8-A12B, and 1,223 because
I never fetched the 8-A12B (those were fund/ETF-named candidates, excluded anyway).
I did not hand-classify the 398, so **343 is a floor, not a point estimate**; the
agreement with NYSE's own figures suggests the shortfall is modest but I did not
measure it.

### 6.3 The post-2022 surge is an INTRA-Nasdaq tier move, not an inter-exchange transfer **[OWN CENSUS]**

This matters because it is the difference between a certification event and a
distress event, and the text-based identification cannot tell them apart. EDGAR
FTS, 8-Ks, one query per year, co-mention of each phrase with `"transfer the
listing"`. **Controls: `"transfer the listing"` AND an impossible phrase over
2010–2026 → 0; `"Nasdaq Capital Market"` AND an impossible phrase in 2023 → 0.**

| year | `"transfer the listing"` | also `"Nasdaq Capital Market"` | also `"minimum bid price"` | also `"New York Stock Exchange"` | also `"NYSE American"` |
|---|---|---|---|---|---|
| 2010 | 69 | 53 | 29 | 15 | 0 |
| 2013 | 49 | 27 | 9 | 24 | 0 |
| 2016 | 41 | 29 | 17 | 12 | 0 |
| 2019 | 59 | 38 | 18 | 20 | 6 |
| 2021 | 54 | 23 | 4 | 43 | 10 |
| 2022 | 100 | 69 | 45 | 34 | 6 |
| **2023** | **186** | **139 (75%)** | **65 (35%)** | 44 | 13 |
| 2024 | 153 | 119 (78%) | 64 | 32 | 4 |
| 2025 | 111 | 74 | 37 | 37 | 4 |
| **2010–2026** | **1,187** | **796 = 67%** | **393 = 33%** | **396 = 33%** | **55 = 4.6%** |

(Full year-by-year table in `temp/` working files; the rows above are every year
that carries the argument plus the totals.)

**Two-thirds of every 8-K in the window that says "transfer the listing" also says
"Nasdaq Capital Market", and a third of them also say "minimum bid price".** That
is the **intra-Nasdaq tier move** — Global Select / Global Market → Capital Market
— which a sub-$1 issuer uses to buy a second 180-day bid-price compliance period.
It is not an inter-exchange transfer, it is a deficiency manoeuvre, it is the
cheap tail, and it is the delisting/distress anomaly this programme has already
excluded. Only **33%** of the phrase population mentions the NYSE at all.

**The 2022–2024 surge in "transfer the listing" is therefore the sub-$1 wave, not
a revival of certification transfers.** The inter-exchange component
(`+New York Stock Exchange`) is essentially flat at 8–44/year across the whole
window with no trend: 15 in 2010, 24 in 2013, 18 in 2020, 44 in 2023, 37 in 2025.
**That flat line is the real count, and it is an upper bound**, because it counts
any 8-K that mentions both strings — including deficiency notices that merely name
the NYSE.

### 6.4 Price, not size — and the survivors-only hazard, measured **[OWN CENSUS]**

**First, the hazard, measured.** The commission flagged that free ticker-to-issuer
maps are survivors-only. Against my 343-transfer census:

> `company_tickers.json`: 10,407 entries, 8,013 distinct CIKs. **Of the 330
> distinct CIKs in the census, 222 are present (67.3%) and 108 are absent
> (32.7%).** Control: the impossible CIK 9999999999 is absent, as it must be.

**The free map silently drops a third of the transfer population** — and 32.7% is
uncomfortably close to this programme's 35.7% dead rate, i.e. the map drops
essentially the dead names and nothing else. **But it is worse than dropping**,
which is the part I had not expected: for CIKs whose issuer was renamed or
acquired, the map returns the **successor's current ticker**, which is a silent
wrong-entity match rather than a miss. Named examples from my own run:

- CIK 1357459, **Neuralstem Inc** (NYSE→Nasdaq 2015) → the map gives `PALI`
  (Palisade Bio), and the 2015 "close" comes back as **$2,187,900**
- CIK 1066923, **SkyPeople Fruit Juice** (NYSE American→Nasdaq 2010) → `FTFT`
  (Future FinTech), "close" **$172,544**
- CIK 1486159, **Oasis Petroleum** (NYSE→Nasdaq 2019) → `CHRD` (Chord Energy)
- CIK 1347858, **22nd Century Group** (NYSE American→Nasdaq 2021) → `XXII`,
  "close" **$811,522,816**

The absurd numbers are **reverse-split back-adjustment**: Yahoo's `close` series is
split-adjusted, and these are serial reverse-splitters, so the adjustment inflates
the historical price without limit. **Four rows exceed $5,000 and are unusable; the
upper tail of every distribution below is contaminated, so I report medians and
below-threshold shares and do NOT report means.** Because the contamination is
always *upward*, the "share below $5" figures are **understated**.

**Second, the price distribution of the names carrying the event** — split-adjusted
close on the 8-A12B date, for the 213 of 343 census rows where a price could be
recovered at all. Control: Yahoo on an impossible symbol returns **HTTP 404 with
"symbol may be delisted"**, an explicit error rather than a price.

| direction | n | p10 | p25 | **MEDIAN** | p75 | share < $5 | share < $10 |
|---|---|---|---|---|---|---|---|
| **Nasdaq→NYSE** | 73 | 13.30 | 19.57 | **$31.51** | 55.03 | **0.0%** | 1.4% |
| **NYSE→Nasdaq** | 77 | 4.67 | 9.41 | **$28.51** | 84.02 | **10.4%** | 28.6% |
| NYSE Amer→NYSE | 22 | 9.23 | 11.15 | **$20.77** | 31.74 | 4.5% | 22.7% |
| NYSE Amer→Nasdaq | 24 | 4.94 | 10.88 | **$17.66** | — | 12.5% | 25.0% |
| **Nasdaq→NYSE Amer** | 9 | 2.56 | 3.30 | **$7.02** | 9.65 | **44.4%** | 77.8% |
| **NYSE→NYSE Amer** | 8 | 2.58 | 4.95 | **$7.41** | 34.51 | **37.5%** | 62.5% |

**This is the cleanest confirmation of "size is not price" I could have asked for,
and it cuts the lane's way on the up-direction.** Nasdaq→NYSE transferees have a
**median price of $31.51 and literally none below $5** — the $5 screen costs this
direction nothing. NYSE→Nasdaq is a median $28.51 but with a real cheap tail
(10.4% below $5, 28.6% below $10) because it contains the SPACs and the small
financials. And **the down-moves to NYSE American are the cheap tail outright**,
medians around $7 with 37–44% already below $5 before any survivor correction —
exactly the distress population the programme has excluded.

Named example of why this matters: **Advanced Micro Devices** announced NYSE→Nasdaq
in December 2014 at a **$2.59** close. The single most famous transfer in the
sample would have failed the $5 screen.

**Third, dollar volume is the binding constraint, not price.** Close × volume on
the same date, $m:

| direction | n | p25 | **MEDIAN** | share < $5m | share < $10m |
|---|---|---|---|---|---|
| Nasdaq→NYSE | 73 | 3.99 | **$10.6m** | 28.8% | 46.6% |
| NYSE→Nasdaq | 75 | 4.45 | **$44.1m** | 25.3% | 32.0% |
| NYSE Amer→NYSE | 22 | 0.77 | **$4.2m** | 54.5% | 68.2% |
| NYSE Amer→Nasdaq | 23 | 0.51 | **$1.7m** | 65.2% | 82.6% |
| Nasdaq→NYSE Amer | 8 | 0.06 | **$1.4m** | 62.5% | 87.5% |
| NYSE→NYSE Amer | 8 | 0.10 | **$0.24m** | **100%** | 100% |

**Fourth, the joint screen — and this is kill number (a):**

| direction | census n | passing $5 close **and** $1m dollar volume | pass rate | **events/year after the screen** |
|---|---|---|---|---|
| **Nasdaq→NYSE** | 73 priced | 69 | **95%** | **≈6.7** |
| **NYSE→Nasdaq** | 77 priced | 56 | **73%** | **≈5.0** |
| NYSE Amer→NYSE | 22 | 14 | 64% | ≈1.6 |
| NYSE Amer→Nasdaq | 24 | 12 | 50% | ≈1.2 |
| Nasdaq→NYSE Amer | 9 | 2 | 22% | ≈0.2 |
| NYSE→NYSE Amer | 8 | 0 | **0%** | **0.0** |

(events/year = full-census count per year × that direction's pass rate.)

**So the answer to (a) is: roughly 7 Nasdaq→NYSE and 5 NYSE→Nasdaq tradable events
per year, and under 3 per year for everything involving NYSE American.** And those
are **upper** bounds, because the pass rates are computed on the 65% of CIKs that
survived into the free ticker map and the price series is adjusted in the direction
that flatters the screen. At a $1m dollar-volume floor a $5,000 clip is 0.5% of a
day's volume, which is generous; raising the floor to $10m takes Nasdaq→NYSE to
~3.7/year.

**Against effective breadth ~10 independent instruments, a territory that delivers
five to seven non-overlapping events a year in its best direction cannot support a
pre-registered out-of-sample test on a fixture it has never seen (R8), let alone
two directions tested separately as §3.3 requires.** That is the kill, and it is
arithmetic rather than judgement.

### 6.5 The earnings confound: this lane PASSES **[OWN CENSUS]**

EDGAR FTS, 8-Ks 2010–2026, transfer phrase AND the Item 2.02 heading "Results of
Operations and Financial Condition":

| phrase | alone | also contains the Item 2.02 heading | share |
|---|---|---|---|
| `"transfer the listing"` | 1,187 | 28 | **2.4%** |
| `"transfer its listing"` | 232 | 4 | **1.7%** |
| `"transfer of its listing"` | 110 | 4 | **3.6%** |
| `"voluntarily withdraw the listing"` | 111 | 10 | **9.0%** |
| `"transfer of listing"` (≈ all of Item 3.01) | 10,000+ (capped) | 351 | ~3.5%, and the numerator/denominator are both truncated by the 10,000 cap so treat this row as indicative only |

**Against J2's 62.2%/59.2% (rising to 72%/80% by 2024) and J1's 36–68%, a
1.7–3.6% co-filing rate is a different world.** The listing transfer is genuinely
announced in its own document. **This is the one killer of the six that K1
clearly survives**, and it is worth recording for K3's census as a case of an item
code that is *not* being absorbed.

Caveat on method: this measures co-*presence of the heading string*, not the item
tag. It will over-count slightly where an 8-K quotes the heading list, and
under-count where an issuer writes the item title differently. It is a screen, not
a tag-level count; K3 should redo it off the structured `items` field in
`data.sec.gov/submissions/CIK*.json`, which carries the real codes.

### 6.6 Kill number (b), answered in one place

**What fraction of transfers is accompanied by an index or ETF membership change?**

| index | fraction of Nasdaq↔NYSE transfers accompanied | basis |
|---|---|---|
| **Nasdaq Composite** | **100%** | the index definition: "must be listed exclusively on the Nasdaq Stock Exchange", added/removed **daily**, no size, liquidity or float gate. Not an estimate — a tautology |
| **Nasdaq-100** | the subset that is an NDX member departing, or that arrives ranking top-40 by cap (Fast Entry) | NYSE claims 10 NDX companies transferred to NYSE since 2008 ≈ **0.6/year**; arrivals large enough for Fast Entry are of the same order (Walmart 2025 is one) |
| NYSE Composite (NYA) | 100% of the same moves, inverted | negligible tracking AUM; not pursued |
| S&P 500/400/600, Russell 1000/2000, CRSP | **0%** | these are venue-agnostic: they require *a* US listing, not a particular one. A transfer does not move them |

**So: 100% of the population is not yours to claim in the strict sense, and ~3% of
it is not yours to claim in the sense that matters.** The 100% figure attaches to
an index whose per-name forced flow is negligible (ONEQ ≈ $10.4bn across >2,000
holdings); the economically material index event attaches to roughly **0.6–1.5
transfers a year**, which is also the subset most likely to pass any liquidity
screen. **Either way, the largest and most tradable members of this territory are
index-flow events, and index flow is permanently excluded ground. The residual —
small-and-mid Nasdaq↔NYSE moves whose only index consequence is a trivial
Composite reweight — is also the residual that fails the dollar-volume floor.**

---

## 7. Blocks, logged by TOOL AND RESPONSE

Never by host — several of these hosts served other URLs happily.

| tool | URL / endpoint | response |
|---|---|---|
| WebFetch | `nasdaq.com/newsroom/500-listings-have-switched…`, `ir.nasdaq.com/news-releases/…2023` | `read ECONNRESET` (twice, different URLs) |
| curl (browser UA) | 3× `ir.nasdaq.com/news-releases/news-release-details/…` | **HTTP 403**, Akamai "Access Denied" body with a `errors.edgesuite.net` reference |
| WebFetch | `sciencedirect.com/science/article/abs/pii/S0929119905000039`, `…/S0927538X96000200` | **HTTP 403 Forbidden**, body not retrieved |
| WebFetch | `businesswire.com/news/home/20221221005283/en/…` | **HTTP 403 Forbidden** |
| curl (browser UA) | `papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID3976675…` | **HTTP 403** with an 896 KB **HTML** body; `pypdf` → "invalid pdf header: b'<html'" |
| curl (browser UA) | `jstor.org/stable/pdf/30129850.pdf` | **HTTP 200** but `content_type: text/html`, 3,038 bytes — **a 200 that is wrong**: an interstitial served where a PDF was requested |
| curl (browser UA) | `stooq.com/q/d/l/?s=pep.us&…` | **HTTP 200** with a JavaScript SHA-256 **proof-of-work interstitial** and zero data — **a second 200 that is wrong**, and not a price source |
| curl + urllib | `www.sec.gov/Archives/...` with `Range: bytes=0-39999` | **HTTP 200, full 535,853-byte body** — the Range header is **silently ignored**, a third way a 200 misleads. Same for `Range` on `full-index/.../form.idx` |
| WebFetch | `ecfr.gov/current/title-17/…/section-240.12d2-2` | **HTTP 302** to `unblock.federalregister.gov/` |
| urllib | `api.semanticscholar.org/graph/v1/paper/search` | **HTTP 429** on 6 of 9 queries even with 4 s spacing and retries |
| urllib + curl | `www.sec.gov` | **HTTP 429** after I let three of my own processes fetch concurrently. **Self-inflicted** — two cancelled background jobs left orphan python processes running; `TaskStop` killed the wrapper, not the child. Fixed by `taskkill` and re-sharding to 3 × 2 req/s. Worth recording as an operational hazard: *a stopped background task is not a stopped process* |

Nothing I fetched contained text addressed to me or instructing me to take an
action. One formatting note, not an instruction: `NYSE_American_Initial_Listing_
Standards.pdf` is served from `nyse.com/publicdocs/` but carries a slide footer
reading "CONFIDENTIAL"; I treated it as the published standards summary it is and
quote only the quantitative table.

---

## 8. What I could not verify, stated plainly

1. **The actual CAR magnitudes in Jain & Kim (2006).** This is the load-bearing
   post-reform paper and I have only its abstract. I know the CARs are positive
   and attributed to investor recognition; **I do not know the number, the window,
   the sample size or the sample period.** Wiley, ProQuest and JSTOR were all
   behind paywalls or interstitials. Any number anyone attaches to "the modern
   Nasdaq→NYSE announcement effect" should be treated as unsourced until this
   paper is read.
2. **Any post-2010 returns study on US inter-exchange transfers.** I looked hard
   and found none. The decay argument in §1.3 is built on *mechanism* evidence
   (spread convergence, <30% primary-venue share, the disappearing index effect),
   **not** on a replication that measured post-2010 transfer CARs and found them
   smaller. Nobody has run that test in public as far as I can establish.
3. **Tse & Devos (2004) has no abstract on RePEc and I could not reach the full
   text.** I have only a third-party characterisation of its period (1992–1995,
   1998–2000) and none of its numbers. It is the only paper I found covering the
   Amex↔Nasdaq move in *both* directions.
4. **The Nasdaq annual transfer counts are title-level and snippet-level only.**
   "125 IPOs and 26 Exchange Transfers in 2023", "35 in 2021", "29 in 2022", "30
   in 2024" come from press-release **titles** and search snippets;
   `ir.nasdaq.com` returned 403 to curl and ECONNRESET to WebFetch, so I never
   read the bodies. I also do not know whether Nasdaq's "exchange transfers"
   counts ETFs, closed-end funds and debt alongside operating companies — NYSE's
   2023 release shows the distinction matters a lot (32 total vs 20 operating).
5. **ONEQ's $10.4bn and QQQ's ~$490bn AUM are snippet-level from
   Morningstar/etfdb.** I did not read a fund document. The *argument* they
   support — that the 100%-overlap index carries trivial per-name flow while the
   partial-overlap index carries large flow — does not depend on the exact
   figures, but the figures themselves are [UNVERIFIED].
6. **Elyasiani–Hauser–Lauterbach's citation is internally inconsistent in my
   source**, which gives "Financial Review, 41, February 2000, pages 1-14" —
   volume 41 would be 2006, not 2000. I report both halves and resolve neither.
7. **The Nasdaq market-quality numbers (12% tighter spreads, 35% more depth, 0.3
   bp average spread change) are snippet-level from a blocked host.** They are
   also vendor material about the vendor's own product and are not evidence for a
   return under this programme's rules.
8. **My price figures are split-adjusted and survivor-filtered, and I repaired
   neither.** Yahoo's `close` is back-adjusted for splits, so a later reverse split
   inflates the historical price without limit — four of 213 rows exceed $5,000 and
   one reads $811,522,816. I therefore report medians and below-threshold shares
   and **no means**. Because the contamination is always upward, the "share below
   $5" figures in §6.4 are **understated** and the pass rates are **overstated**.
   Separately, prices exist only for the 222 of 330 CIKs the free ticker map
   retained, so the whole distribution describes survivors. **A real study needs an
   as-traded, point-in-time price source; I did not have one** — `stooq.com` served
   a JavaScript proof-of-work wall at HTTP 200 (§7).
9. **I did not establish which of my census rows are NDX members or Fast-Entry
   candidates.** The 0.6–1.5/year figure in §6.6 is inferred from NYSE's "10
   Nasdaq-100 companies since 2008" plus the observation that Walmart-scale
   arrivals are rare. I did not reconstruct historical NDX membership, so the
   material-index-overlap fraction is an order-of-magnitude claim, not a count.
10. **I did not verify the SIC/entity type of every census row.** Operating-company
    status is inferred from the company name (a fund/ETF/trust word list) and from
    the 8-A12B registering common equity. REITs and LPs named "…Trust" are
    misclassified as funds by that filter, so the census **understates** the
    operating-company count by an amount I did not measure — and separately 398
    pairs were dropped because the 8-A12B cover page did not parse, which I also
    did not hand-classify. **343 is a floor.** The cross-check against NYSE's own
    operating-company figures suggests the shortfall is modest.
11. **I did not measure the pre-announcement run-up.** The only leakage evidence I
    found is for UK AIM→Main Market switches (significant abnormal returns 60
    trading days before announcement — [PEER-REVIEWED] [snippet only]), which is a
    different market and a different mechanism, and I do not carry it across.
12. **I did not verify the announcement-to-effective gap as a distribution.** I have
    it for exactly two events, both read in full: PepsiCo 2017 (8 trading days) and
    Walmart 2025 (~12 trading days). Item 3.01(d) guarantees the announcement exists
    and is dated, and both examples pre-announce the effective date, but I did not
    harvest the gap across the census, so "the move resolves over days, not in one
    print" is established for n=2 and asserted for the rest.
