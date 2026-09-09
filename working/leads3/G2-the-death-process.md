# G2 — the death process: the delisting return, and the run-up to failure-death

*Commissioned 2026-09-09. Research brief on EXTERNAL evidence only. I have no access to the
programme's data and claim nothing about it. Under the quarantine contract in
[`README.md`](README.md) this closes nothing and admits nothing.*

**Safety note.** Every page, PDF and search result below was treated as data. **No page I opened
contained text addressed to me or instructing me to take an action.** The closest thing was Richard
Price's research page, whose content is ordinary instructions *to readers* about downloading SAS
macros — site copy, not an address to an agent. Nothing was downloaded, no form was submitted, no
account was created.

---

## 1. Verdict

**Three different answers for the lane's three questions, and only one of them is good news.**

**The method half is real, is exactly the error the literature names, and is probably SMALLER for
this fixture than the commissioning note fears — conditional on one line of code I cannot see.**
The convention "carry to the final bar and close at the last available price" is arithmetically
identical to setting the delisting return to **zero**, which is the precise error Shumway (1997)
and Shumway–Warther (1999) were written about. The documented size of the thing being set to zero
is **−30% (NYSE/AMEX, mean over 71% coverage) to −55% (Nasdaq, after a liquidity haircut)**, and
Macey–O'Hara–Pompilio corroborate it out-of-sample on 2002 NYSE data with **prices falling roughly
in half at delisting**. But every one of those numbers is measured on names trading at **$0.57 to
$1.09**. This fixture floors at **$5**. **The whole question is therefore whether a held name that
falls through the $5 floor is ejected at the floor or carried to its delisting.** If ejected, the
exposure is small and the bias is a footnote. If carried, the bias is the full Shumway magnitude
and it lands hardest on exactly the loser-tilted, equal-weighted, rebalanced book this programme
runs — Shumway says so explicitly. **That is one assertion, not a study.** §2.5 states it.

**The signal half is dead, and four independent things killed it.** (i) **The distress anomaly's
money is in the short leg** — Campbell–Hilscher–Szilagyi's long-safe/short-distressed decile spread
is +10.2%/yr, of which the long leg contributes **+3.4%/yr with t = 1.45**; shorting is excluded
ground here, so the tradeable half is the half that cannot be traded. (ii) **It does not survive.**
Hou–Xue–Zhang replicate CHS's own estimate at −0.82%/mo in CHS's sample and then get **+0.09%/mo
from 2003 onward** — the sign flips, over precisely the era preceding this fixture, and O-score,
Z-score and credit rating are insignificant everywhere. (iii) **The cohort is below the floor.**
Failure-death is slow and terminal prices are ~$1; a Nasdaq bid-price delisting requires at minimum
30 consecutive business days under $1 *plus* a 180-day cure period, so the name is sub-$5 for a year
or more before it dies. A $5-floored universe does not contain the run-up. (iv) **The cost premise
inverts.** Route (b) asks for a move large and slow relative to the spread. The move is large and
slow — but Macey et al. measure **5.889% average percentage spread on NYSE names in the 60 days
BEFORE delisting, while still exchange-listed**, against this programme's measured **33.8 bp/side**
on names it actually holds. Seventeen times. The premise that the toll is a rounding error fails on
its own terms, and it fails in the direction the book cannot exploit.

**The census does NOT kill the lane on its own, and I want to be careful about that.** Acquisition
does not overwhelm failure: Doidge–Karolyi–Stulz count **9,749 merger delists, 7,120 for cause and
434 voluntary over 1975–2012** — **56% / 41% / 2.5%** — and **37% for cause over 1997–2012**. A
dead-inclusive fixture is therefore measuring failure risk for roughly a third of its deaths, not
none of them. **But** the same authors' 2025 update finds that in **the 2010s the delist rate fell
to a historical low and the fall came specifically from the for-cause rate**, because surviving
listed firms got much larger. The failure cohort exists; it is the smallest it has been; and the $5
floor removes most of what is left of it.

**The data question is the lane's actual deliverable and the answer is better than I expected.**
**8-K Item 3.01** — verified in the official Form 8-K, read in full — requires a registrant to
disclose, within **four business days**, the **date it received a deficiency notice and the specific
continued-listing rule it failed**. **Item 1.03** requires the same for bankruptcy or receivership.
**Form 25-NSE** carries a free-text attachment naming the exact listing rules and the whole appeal
timeline; I read one. All three are free, point-in-time, bulk-retrievable from EDGAR, and all three
run from **2004 (8-K item numbering) / 2006 (electronic Form 25)** — i.e. they cover the fixture's
entire 2010–2026 window with years to spare. **Cause of death is a solved data problem here.** It is
the return, and the tradeability, that are not.

**Recommendation: run the one assertion in §2.5, take the free cause-of-death classification in §5
because it is cheap and it fixes the census, and do not build a distress signal.**

---

## 2. HALF ONE — THE DELISTING RETURN

### 2.1 What CRSP does, and why

CRSP records a **delisting return (DLRET)** — the return from the last exchange trading price to the
value realised after delisting, which may be a post-delisting OTC price or a final distribution. The
convention exists because a portfolio return computed *without* it is not a return an investor could
have earned:

> "Without delisting returns, it is not possible to accurately calculate the returns to a feasible
> portfolio. To obtain the returns of portfolios formed without them, investors would have to sell
> delisting stocks on their last trading day."
> — Shumway (1997), p. 328 [PEER-REVIEWED] [read in full]

**That last sentence is a literal description of this programme's stated convention.** The
convention is not merely approximate; it is the specific counterfactual the literature calls
infeasible, because the investor does not know which day is the last one.

**Why the returns are missing, and why they are missing NON-RANDOMLY.** CRSP collects delisting
returns well for benign delistings and badly for performance-related ones, because benign ones are
announced and priced in and bad ones are surprises:

| | NYSE/AMEX, 1962–1993 | Nasdaq, 1972–1995 |
|---|---|---|
| performance delists **with** a delisting return | **11.7%** | **0 of 3,750** |
| merger / exchange / move to NYSE-AMEX, % missing | delisting returns "almost always collected" | **≤1.0%** |
| performance delists, % missing | — | **99.8%** |
| performance delists per year | 32 | 220 |
| performance delists as % of listed firms per year | **1.2%** | **5.6%** |

*Sources: Shumway (1997) Table I; Shumway–Warther (1999) Tables I and II. Both [PEER-REVIEWED], both
[read in full] from free PDFs on the author's own site.*

Shumway–Warther conclude from the 1.2% vs 5.6% ratio that **"we expect the Nasdaq delisting bias to
be about 4.7 times larger than the NYSE and AMEX bias."**

**Are delistings surprises?** Shumway searched Nexis and the WSJ Index and found **only 30.3% of
NYSE/AMEX performance delists had any prior announcement**. Shumway–Warther searched Bloomberg for
the 159 Nasdaq performance delists of 1993 and found **two** with a pre-announcement and **41 stories
explicitly reporting the delisting as a surprise**. Where an announcement did occur, the
event-study reaction was **−14.0% one day after (n=58, t=−2.36)** — and Shumway notes 14% probably
*understates* it, because announced delists are the mild ones.

### 2.2 The documented magnitudes

**Shumway (1997), NYSE/AMEX, OTC Pink Sheets prices** [PEER-REVIEWED] [read in full — Table V]:

| | N | % coverage | mean | median | s.d. | min | max |
|---|---|---|---|---|---|---|---|
| original CRSP DLRET | 120 | 11.7 | **−41.6** | −33.3 | 53.2 | −100.0 | 77.8 |
| new OTC returns | 577 | 56.1 | −23.0 | −26.0 | 45.4 | −98.4 | 315.9 |
| identified worthless | 84 | 8.2 | −100.0 | −100.0 | 0.0 | — | — |
| **combined total** | **734** | **71.3** | **−29.9** | **−31.3** | **48.9** | −100.0 | 315.9 |

**This is the −30%.** Note the s.d. of 48.9 and the max of +315.9: the delisting return is not a
constant, it is a wide, left-skewed distribution with a live right tail. Anyone imputing −0.30 is
imputing a *mean*, and a mean with a 49-point spread around it.

**Shumway–Warther (1999), Nasdaq** [PEER-REVIEWED] [read in full]. Their derivation, which matters
because the −55% is *not* a measured return:

1. Pink Sheets / Bloomberg / *Directory of Obsolete Securities* located prices for **63%** of the
   missing returns; those averaged **−26.3%**.
2. For the unfound 37% they assume **half resemble the found ones (−26.5%) and half are worthless
   (−100%)** — explicitly a judgement, not a measurement:
   `0.63(−26.3) + 0.37(0.5(−100.0) + 0.5(−26.5)) = **−40 percent**`
3. Then a **liquidity haircut**: mean relative bid-ask spread rises **0.41 → 0.82** on delisting
   (median 0.33 → 0.86). Selling at the post-delisting bid:
   `RCorr = (0.354P − 0.795P) / 0.795P = **−55 percent**`
4. Cross-check: computing bid-to-bid returns directly for the subsample with both quotes gives
   **−41%**, and applying the same worthless/unfound adjustments to that "virtually identical" −55%.

**So −55% is −40% of price decline plus ~15 points of spread.** For a programme that already prices
spread explicitly, that decomposition matters: **the price part and the liquidity part must not be
double-counted.**

**Category-level means** (Shumway–Warther Table III, Nasdaq, 1977–mid-1994), which are the numbers to
use if cause of death is known — and §5 says it can be:

| CRSP code | reason | N found | mean | median |
|---|---|---|---|---|
| 500 | reason unavailable | 391 | **−20.8** | −18.8 |
| 560 | insufficient capital/surplus/equity | 606 | **−28.9** | −37.5 |
| 580 | delinquent in filing or fees | 344 | **−32.5** | −36.0 |
| 550 | insufficient market makers | 255 | **−30.3** | −36.0 |
| 561 | insufficient float or assets | 134 | **−26.5** | −30.2 |
| 520 | moved to Pink Sheets | 47 | **−35.6** | −28.0 |
| 510 | moved to Boston Exchange | 20 | **−45.0** | −45.3 |
| 574 | bankruptcy or insolvency | 13 | **−39.8** | −40.0 |
| 552 | price too low | 83 | −0.2 | −23.1 |
| 551 | insufficient shareholders | 53 | −2.6 | 0.4 |

Shumway–Warther: **"No estimated mean is significantly positive."** Note the two near-zero rows
(552, 551) — the cause of death genuinely changes the answer, and "price too low" of all things is
one of the benign ones, because by the time the exchange acts the price has already gone.

**Macey, O'Hara & Pompilio — independent, non-CRSP, and 30 years later** [PEER-REVIEWED, *J. Law &
Economics* 51 (2008); I read the free NBER conference version in full on all numbers below]. All 63
firms **involuntarily** delisted from the NYSE in 2002, of which 57 went to the Pink Sheets, using
data supplied by Pink Sheets Inc.:

- **"share prices falling approximately in half when delisting occurs"**
- non-bankrupt subsample: **$1.09 → $0.59** (−46%); bankrupt subsample: **$0.70 → $0.28** (−60%)
- percentage spreads: **5.889% pre-delisting → 16.939% post** (60-day windows); **first-day average
  spread >40%, median 25%**
- volatility **more than doubles**; **prices continue to decline after delisting**
- volume stays high — first-day average **>2 million shares**

**This is the best available modern corroboration of the −40%/−55% price component, and it is
independent of CRSP entirely.** It also tells you the terminal price level: **~$0.60–$1.10.**

**One Macey finding that cuts directly AGAINST the commissioning note's framing, and I think it is
the most important single fact in this half.** The note says "a name that files Chapter 11 after its
last print books its last quoted move, not its loss." In practice the sequence usually runs the
other way:

> "the average time between bankruptcy filing and delisting was 131 trading days"
> — Macey, O'Hara & Pompilio, on the 20 bankruptcy-caused NYSE delistings of 2002 [read in full]

Global Crossing was delisted the day after filing; **Enron traded 30 more days; Owens Corning traded
for more than two years after filing.** And **4 of the 20 firms the NYSE delisted "for bankruptcy"
never actually went bankrupt** — they were delisted for *announcing the possibility*. So the
Chapter-11 crash is normally **inside the tape**, booked correctly by any convention. What is
missed is the *separate, later* delisting drop, from an already-collapsed price. That is a smaller
error than "books its last quoted move, not its loss" implies, and the programme should correct the
framing before it sizes the problem.

### 2.3 Direction of the bias — long book versus short book

Setting the delisting return to zero when the truth is −30% to −55%:

| | true terminal return | booked by this convention | error |
|---|---|---|---|
| **long** a name that dies for cause | −30% to −55% (tail to −100%) | ~0 | **book is FLATTERED** |
| **short** a name that dies for cause | +30% to +55% (capped +100%) | ~0 | **book is PUNISHED** |
| long or short a name acquired for cash | last price ≈ deal price | ≈ correct | negligible |

**For a long-only book the omission is unambiguously flattering, and there is no offsetting leg.**
This is worth stating flatly because it is the opposite of the usual reassurance that biases wash
out: they do not wash out here, because the missing returns are almost all negative
(Shumway–Warther: *"Since most of the missing delisting returns are associated with negative events,
a significant bias exists in the data"*) and a long-only book is on one side of all of them.

A secondary implication the programme should note: **if it ever tests a short or a long/short
version of anything, the convention will make the short leg look worse than it was**, and it will do
so most for exactly the distressed names a short leg would want. A short result rejected under this
convention has not been fairly tested.

### 2.4 How large is it, for a book shaped like this one

Shumway is unusually specific about *which* research designs the bias attacks, and every clause
matches this programme:

> "portfolios dominated by small stocks, stocks with low past returns, or stocks with a low price
> should be the most sensitive to the bias. The bias should be larger for equally-weighted
> portfolios than for value-weighted portfolios. Portfolio returns calculated by a buy-and-hold
> method should not be as sensitive to the bias as portfolio returns calculated by compounding
> average stock returns, like cumulative abnormal returns (CAR)."
> — Shumway (1997), p. 337 [read in full]

**Equal-weighted: yes. Low past returns: yes, for any reversal work. Rebalanced rather than
buy-and-hold: yes — a slot-limited book with refill is the CAR case, not the buy-and-hold case.**
Three for three on the sensitive side. The only mitigant in the list is the price floor, and it is
the one that does the work (§2.5).

**Measured magnitudes, from the two papers' own replications** — these are the anchors to size
against, and I read every one of them:

| study replicated | statistic | with CRSP as-is | corrected | with −100% (upper bound) |
|---|---|---|---|---|
| De Bondt–Thaler **reversal**, 36-mo losers−winners, CAR, NYSE 1926–1989 | cumulative % | **30.9** (t 2.13) | **29.9** (t 2.07) | **26.2** (t 1.94) |
| same, **buy-and-hold** | cumulative % | 16.8 (t 1.32) | 16.5 (t 1.29) | 13.8 (t 1.10) |
| Fama–French **smallest size decile**, EW, annualised, 1962–1992 | %/yr | **21.28** | **19.83** | **16.07** |
| Fama–French largest size decile | %/yr | 11.71 | 11.71 | 11.71 |
| Lamoureux–Sanger, **smallest 5% of Nasdaq**, EW | %/month | **3.79** | **1.97** | — |
| same, next three smallest Nasdaq portfolios | %/month | 2.52 / 1.78 / 1.49 | 1.56 / 1.17 / 1.05 | — |

*Shumway (1997) Tables VI–VII; Shumway–Warther (1999) Table IV, using −55%.*

**Read the reversal row carefully, because it is the closest thing to this programme's own work.**
Correcting delisting returns costs the 36-month reversal spread **1.0 percentage point** at the
realistic estimate and **4.7 points** at the −100% bound — about **35 to 155 bp/yr**. Material,
not fatal. **But Shumway explicitly discounts his own number:** *"Since 11 of the 21 portfolio
evaluation periods used in Table VI occur before 1962, when delisting returns are fairly complete,
the delisting bias is not large."* Roughly half his sample had no bias to correct. **A modern,
post-1962-only version of that row would be around double.** Call it **70 to 300 bp/yr on a
loser-tilted equal-weighted book, if that book holds names to their delisting.**

**The sanity identity worth carrying**, because it lets the programme size this from quantities it
already has, without any external data:

> **bias per period ≈ (fraction of held names that delist for cause per period) × |missed delisting
> return|**

Checked against Shumway–Warther's own table: the smallest Nasdaq portfolio delists at **2.95%/month**
and the correction is **−55%** → predicted **162 bp/month**; observed correction is
**379 − 197 = 182 bp/month**. The identity recovers 89% of it, the remainder being their separate
correction of temporary delistings. **It works, and the first factor is something the programme can
count in its own fixture in an afternoon.**

### 2.5 THE ONE CHECK — and why the $5 floor probably saves this fixture

Every magnitude in §2.2 is measured on names priced **$0.57–$1.09** at death. This fixture floors at
a **$5 close** with a dollar-volume screen on top. Failure-death is slow: **Nasdaq's minimum bid
price standard requires 30 consecutive business days below $1.00 before a deficiency notice, then
180 calendar days to cure, with a possible second 180** [PRACTITIONER / law-firm commentary,
snippet only — **I did not open the Nasdaq rulebook itself**, see §7.3]. So a bid-price death takes
**210 to 390 days below $1**, on top of however long the slide from $5 to $1 took. **A $5-floored
universe cannot be holding that name at its final bar unless something carries it there.**

**So the entire method half reduces to one question about code I cannot see:**

> **When a held name falls below the $5 close floor (or through the dollar-volume screen), is the
> position ejected at the screen, or is it carried to the delisting and closed at the last available
> price?**

- **If ejected at the screen** — the delisting-return bias is confined to names that die from *above*
  $5. Failure-death almost never does that; **acquisition** does, and for a cash acquisition the last
  price ≈ the deal price, so the convention is approximately right. **The bias is then a footnote,
  and the lane's method half should be closed as immaterial after one measurement.**
- **If carried to the final bar** — the book is exposed to the full Shumway distribution on every
  name that dies for cause, equal-weighted, on a rebalanced book with a loser tilt. **Then the
  §2.4 anchors apply.**

**Two assertions, both cheap, both computable inside the existing fixture with no external data:**

1. **`assert`** that for every name carrying a delisting date, the price on its final held bar is
   recorded — then **report the distribution of that final price**, split by whether the name was
   held at that bar. If the mass sits at $5-and-just-above, the floor is ejecting and the exposure is
   small. If there is mass at $1 and below, names are being carried through the floor and the
   convention is booking zeros where Shumway says −30% belongs.
2. **`assert`** the count and the identity of §2.4: `n_delisted_while_held / n_name_bars` × 0.30, in
   bp/yr, against the headline. **If that product is under a few bp, the lane is closed on
   arithmetic and no imputation is needed at all.**

**And a mirror-image bias the floor introduces, which nobody has named and which also flatters a
long book.** If the floor *does* eject falling names, then the universe screen is acting as an
**undeclared stop-loss at $5** on every position — truncating the left tail of every trade in a way
that appears in no strategy specification and in no cost model. For a book whose CLAUDE.md already
insists on reporting the trimmed mean and the left tail, that is a construction artefact worth
knowing about. **Both readings of the floor flatter the long book; they just do it by different
mechanisms.** Whichever answer the check returns, something needs saying in the record.

### 2.6 Is there a free, non-CRSP way to get or approximate a delisting return?

**Short answer: no free source of actual post-delisting prices exists that I could verify. But the
free primary record does let you classify the death, and the cause is worth more than a constant.**

| route | free? | what it gives | verdict |
|---|---|---|---|
| **CRSP DLRET** | no (subscription) | the field itself, and even then 99.8% missing for Nasdaq performance delists historically | not available, and historically empty where it matters |
| **Shumway constants** (−30% NYSE/AMEX, −55% Nasdaq) | yes — a method, not data | a mean with s.d. 48.9 | usable, crude, and **must not be double-counted against a spread model** (§2.2) |
| **cause-conditional constants** (Shumway–Warther Table III) | yes | −20.8 to −45.0 by CRSP code | **better**, and §5 shows cause is now free to obtain |
| **Richard Price's `_dlret_rv.sas`** | yes, code only | replaces missing DLRET with the average of *similar* delistings rather than one constant; warns that missing monthly DLRET often contains partial-month data so the field "may not actually be empty" | [PRACTITIONER, page read via WebFetch] — **method, no data, and it presupposes CRSP** |
| **Pink Sheets / OTC Markets Group historical quotes** | **no** | the actual post-delisting price — this is what both Shumway papers and Macey et al. bought | the only true source; commercial |
| **8-K Item 1.03(b), plan of reorganization** | **yes** | for bankruptcies, whether existing equity is cancelled → a **true −100%**, dated, from the primary record | **the one genuinely free route to a REAL delisting return**, for the bankruptcy subset only |
| **RECAP / CourtListener dockets** | yes | Chapter 11 filings | **coverage is thin for bankruptcy specifically** vs district courts [search summary of CourtListener's own coverage page, not opened directly]; 8-K 1.03 is strictly better for *listed* companies |

**The recommendation, if the §2.5 check says the exposure is real:** classify cause from EDGAR (§5),
apply Shumway–Warther's **cause-conditional** means rather than a single constant, resolve the
bankruptcy subset to a true −100%/not-−100% from the Item 1.03(b) plan disclosure, and **report the
headline three ways — as-is, imputed, and at the −100% bound** — exactly as Shumway's own Table VI
does. The −100% column is not a serious estimate; it is the bound that tells you whether the result
survives the worst case, and it is the column that changed his t-statistic from 2.13 to 1.94.

---

## 3. THE PREMISE NUMBER — the cause-of-death census

**The question asked: what proportion of US delistings 2010–2026 are acquisitions versus failures?**

**Best-sourced split, and my confidence in it.**

**Doidge, Karolyi & Stulz, "The U.S. Listing Gap"** [NBER WP 21181, subsequently *JFE* 2017]
[read directly from the NBER PDF]. US operating firms with CRSP coverage, 1975–2012. Classification
follows Fama–French (2004): **CRSP delist codes 200–399 = merger; 400 and above = for cause, except
codes 570 and 573 = voluntary.**

| period | merger | for cause | voluntary | total |
|---|---|---|---|---|
| **1975–2012, counts** | **9,749 (56.3%)** | **7,120 (41.1%)** | **434 (2.5%)** | 17,303 |
| 1975–1996, share for cause | — | **45%** | 1.82% | — |
| **1997–2012, share for cause** | 4,957 of 8,327 = **59.5%** | **37%** | 3.25% (271) | **8,327** |

Delist rates as a % of prior-year listings: total **7.29% pre-1996 vs 9.49% post** (t = 3.10); the
increase is **all merger** (3.92% → 5.64%, t = 3.59); **the for-cause rate is statistically
unchanged (3.25% vs 3.50%)**.

**So: not overwhelmingly acquisition. Roughly 60 / 37 / 3 for the modern era. The failure cohort
exists.** The commissioning note's kill condition — "if the answer is overwhelmingly acquisition, the
signal half has no cohort" — **is not met.** The signal half dies for the reasons in §4, not for
want of a cohort.

**Two caveats that cut in opposite directions, both of which I verified.**

- **DKS undercount relative to the exchanges.** Macey–O'Hara–Pompilio, using data direct from the
  exchanges 1995–2005, count **9,273 delists where DKS record 6,932**, and report **"almost half"
  involuntary**. DKS explain the gap: the exchange counts include non-US issuers, inter-exchange
  transfers, and non-operating listings (REITs, trusts). **Which number is right depends on what the
  fixture's universe is** — if it holds ADRs or trusts, the exchange-based ~50% is closer.
- **"For cause" ≠ "failure".** Code 400 is liquidation; 500-series includes moves to the Pink Sheets
  and delinquent filings; 570/573 are carved out as voluntary but 572 (company request, liquidation)
  is not. **Some for-cause deaths are going-dark, not dying.** So 37% is an upper bound on failure.

**For 2010–2026 specifically — Doidge, Karolyi & Stulz (2025), NBER WP 33556, updating to 2023**
[WORKING PAPER] [read directly]:

> "In the 2010s, the delist rate became low by historical standards. The low delist rate overall
> stems from the low percentage of firms delisting for cause and not from the delisting rate for
> mergers or for voluntary reasons."

Their mechanism: the merger wave and the IPO drought raised average firm size, and **"larger and
older listed firms are less likely to be delisted for cause."** US listings: 4,775 (1975) → peak
8,025 (1996) → 4,102 (2012) → **4,315 (2023)**.

**My confidence.** **High** on the 1975–2012 split (counts read from the authors' own text). **High
on the direction** for the 2010s (the for-cause rate fell). **Low on the exact 2010–2026 percentage**
— the year-by-year decomposition is their **Figure 4, a chart**, and **I could not read numbers off
it**; §7.1. A WFE article that a search summary said gives "M&A >60%, voluntary <10%, involuntary
~30% in 2023" **could not be opened** (WebFetch → focus.world-exchanges.org: HTTP 403), so I am not
citing those figures as established.

**A premise check the programme can run on its own fixture, offered as arithmetic and not as a
claim.** The fixture reports **~35.7% of names carrying a delisting date** over ~16.6 years. At a
post-peak total delist rate of ~9.5%/yr, a name present throughout survives `0.905^16.6 ≈ 20%`; at
the lower 2010s rate, say 7%/yr, `0.93^16.6 ≈ 30%`. Names that listed mid-sample have less exposure
and pull the observed fraction down, so 35.7% is not implausible — **but it is at the low end, and
the direction of any error in a vendor's delisting flag is the direction Shumway documented in CRSP:
benign deaths recorded, for-cause deaths dropped.** Worth one count against the DKS base rates
before anything is built on "dead-inclusive". **And separately: a delisting DATE is not a cause.**
Unless the fixture already carries a cause field, it cannot presently tell an acquisition from a
failure at all — which §5 says is now a cheap fix.

---

## 4. HALF TWO — THE RUN-UP TO FAILURE-DEATH

### 4.1 The distress anomaly, and which leg holds the money

**Campbell, Hilscher & Szilagyi, "In Search of Distress Risk"** [*JF* 63 (2008); read in full from
the free NBER WP 12362 version]. US 1963–2003, returns 1981–2003. Portfolios sorted on a fitted
12-month failure probability; **value-weighted excess returns over the market, annualised %**:

| percentile | 0–5 | 5–10 | 10–20 | 20–40 | 40–60 | 60–80 | 80–90 | 90–95 | 95–99 | **99–100** |
|---|---|---|---|---|---|---|---|---|---|---|
| mean excess | **+3.39** | +2.36 | +1.25 | +0.93 | +0.50 | −0.16 | −4.44 | −8.07 | −6.63 | **−16.30** |
| (t) | (1.45) | (1.08) | (1.06) | (1.02) | (0.34) | (0.07) | (1.26) | (1.72) | (1.24) | **(1.98)\*** |

Long-safest-decile / short-riskiest-decile: **+10.20%/yr (t = 1.90)**, CAPM alpha **12.4% (t = 2.3)**,
FF3 alpha **22.7%**.

**The distribution of that spread is the whole story for this programme.** The long leg — the safest
5% — earns **+3.4%/yr with t = 1.45**, i.e. nothing. **Essentially all of the +10.2% comes from the
short leg being catastrophically negative.** Shorting is excluded ground here. **The anomaly's
tradeable half is precisely the half this programme cannot trade**, and what it *can* trade is a
long position in the safest quintile, which is not a distress strategy and is not this lane.

Note also **which direction the anomaly runs**: distressed stocks earn *low* returns. There is no
documented long-side edge in buying names heading for death. **A "buy the run-up to failure" trade
has never been the anomaly; the anomaly is that these names are overpriced.** If the programme's
route (b) framing imagined a large slow *upward* move to capture, the literature says the move is
down.

CHS also close off the two obvious mechanisms: the low returns are **not concentrated around
earnings announcements** (ruling out an expectations story), and they correlate with rising VIX and
with rising 13-F institutional ownership share — suggesting **institutional aversion depressing
prices**, which is a limits-to-arbitrage story, not a harvestable one.

### 4.2 What survives after 2003 — this is the kill

**Hou, Xue & Zhang, "Replicating Anomalies"** [NBER WP 23394, subsequently *RFS* 2020; read directly
from the NBER PDF]. NYSE breakpoints, value-weighted, annual sorts:

> "the distress anomaly is virtually nonexistent in our replication."

| sample | CHS failure-probability high-minus-low decile, %/month |
|---|---|
| **CHS's own sample period** (replicated) | **−0.82** (t = −2.1) |
| Jul 1976 – Dec 1980 (before CHS) | **+0.69** |
| **2003 onward (after CHS)** | **+0.09** |
| **Jul 1976 – Dec 2014 (full)** | **−0.38** (t = −1.28) |
| monthly sorts, 1-mo / 6-mo / 12-mo horizons | −0.48 / **−0.63 (t = −2.03)** / −0.36 |

And the alternatives fare worse: **"Several alternative measures of financial distress, including
Altman's (1968) Z-score, Ohlson's (1980) O-score, and credit rating, show even weaker forecasting
power for returns than failure probability. None of the high-minus-low deciles show any significant
average returns."** High-minus-low O-score ranges **−0.06% (t = −0.3) to −0.36% (t = −1.57)**.

**+0.09%/month from 2003 onward.** The effect is not merely weakened out of sample; **its sign
flips**, over the twenty-three years immediately preceding and overlapping this fixture. That is
the single most decisive number in the lane.

**The obvious rebuttal, and why it does not rescue anything.** HXZ use **NYSE breakpoints and
value-weighting**; CHS used NYSE-Amex-NASDAQ breakpoints. The standard defence is that the anomaly
lives in microcaps and equal-weighting revives it. **Grant that, and the lane is worse off, not
better** — because §2.4 establishes that equal-weighting and a low-price tilt are exactly the
conditions under which the **delisting-return bias** is largest. **The weighting scheme that revives
the distress anomaly is the same one that maximises the measurement error capable of manufacturing
it.** Any revival would have to be demonstrated *with* corrected delisting returns before it meant
anything, and I found no study that does so post-2003.

Tarun Chordia's 2023 ABFER keynote [PRACTITIONER, conference digest, read in full] surveys and
rejects the leading explanations — wealth transfer, biased earnings expectations, lottery
preferences — and lands on limits to arbitrage: distressed stocks are **illiquid, small, thinly
covered, with high forecast dispersion**, and **"uncertainty and illiquidity increase dramatically
around financial distress."** He reports that distress lasts **~11.8 months** on average while the
mispricing persists **three years or more**. Every one of those properties is a cost problem for
this programme, not an opportunity.

### 4.3 The deficiency notice as an event

The one genuinely clean, dated, free event in the run-up is the **8-K Item 3.01** filing (§5).
Guragai (2022), *Advances in Accounting* 59, studied 8-Ks with Item 3.01 deficiency language,
**2004–2015** [PEER-REVIEWED]. **I opened the RePEc listing and read the abstract, which is
qualitative only; the numbers below come from a SEARCH-RESULT SNIPPET of the ScienceDirect abstract
and I did NOT open the paper** — treat them as unverified:

- **−1.8%** three-day CAR, **−2.0%** two-day CAR around the filing
- **−11.5%** over the **(−30, −2)** window — i.e. before the filing
- equity and multiple deficiency notices provoke a more negative reaction **and are more likely to
  result in actual delisting** than bid-price notices
- reaction is less negative for firms with more analyst coverage and institutional ownership

**Read the shape rather than the levels.** A **−11.5% run-up before** the filing against a
**−1.8% reaction at** it says the market has the information already; the disclosure is
confirmation. **That is a leakage profile, not a tradeable post-event drift**, and the abstract
reports no post-filing drift at all. **The quantity that would matter to this programme — the
post-notice drift, net — is not in anything I read.** §7.4.

The programme should also weigh what the ~$5 floor does to this event: a **bid-price** deficiency
requires 30 consecutive days under $1, so those names are far below the floor. **Equity** and
**market-value** deficiencies — the ones Guragai's abstract says are more predictive of actual
delisting — can fire on names still priced above $5. **If any part of the signal half is worth a
single measurement, it is that subset and only that subset**, and it should be sized before it is
studied: it is a small subset of a shrinking for-cause cohort (§3).

### 4.4 The cost wall, which does bind after all

Route (b)'s premise is that the move is large and slow relative to the spread. **The move is large
and slow. The spread is not small.**

- Measured spread on names this programme actually holds: **33.8 bp/side.**
- Macey et al., NYSE names in the **60 days before** involuntary delisting, **still listed**:
  **5.889% = 589 bp/side** average percentage spread. **After delisting: 16.939%.** First day on the
  Pink Sheets: **>40% average, 25% median.**

Those pre-delisting names averaged ~$1, so 589 bp is not the number a $5-floored book would face —
but the direction and the order of magnitude are unambiguous, and the programme's own house rule is
to **estimate the spread of the names HELD rather than trust an assumption**. Corwin–Schultz off the
OHLC of any candidate distress cohort should be run **before** any study, not after.

**And the commission side scales the wrong way.** With IBKR per-share at $0.005, commission in
bp/side is **50/P**: **10 bp at $5, 25 bp at $2, 50 bp at $1**. Dying names are cheap names. **The
signal half's cohort is, by construction, the most expensive cohort in the universe to trade, on
both legs of the cost model simultaneously** — and it is the cohort whose documented edge points
down and whose post-2003 spread is +0.09%/month.

---

## 5. THE DATA — free, point-in-time, bulk, cause of death

**This is the part of the lane that works, and it is worth taking regardless of what happens to the
rest.** All of the following were verified by fetching the actual SEC documents.

### 5.1 Form 25 — what it does and does not distinguish

**SEC Form 25 (SEC 1654, OMB 3235-0080)** [PRIMARY DATA DOC] [read in full]. "Notification of
Removal from Listing and/or Registration under Section 12(b)". The whole form is a set of checkboxes
naming the rule provision relied on. Cross-referencing the rule text from Cornell LII
[PRIMARY, read via WebFetch]:

| box | 17 CFR 240.12d2-2 provision | what it actually means | separates? |
|---|---|---|---|
| (a)(1) | class called for redemption/maturity/retirement, funds deposited | not common stock, normally | benign |
| (a)(2) | class redeemed or paid at maturity | not common stock, normally | benign |
| (a)(3) | instruments "have come to evidence... other securities in substitution therefor" | **stock-for-stock merger or reorganisation** | **ACQUISITION** |
| (a)(4) | "all rights pertaining to the entire class... have been extinguished", final court order, appeals expired | **equity cancelled — a plan of reorganisation, or a cash merger** | **ambiguous: wipeout OR cash deal** |
| **(b)** | **the Exchange has complied with its rules to strike the class from listing** | **exchange-initiated, involuntary** | **FAILURE / FOR CAUSE** |
| **(c)** | **the Issuer has complied with... voluntary withdrawal** | **issuer-initiated** | **GOING PRIVATE / GOING DARK / venue switch** |

**So Form 25 separates INVOLUNTARY from VOLUNTARY cleanly, and stock-for-stock acquisition
reasonably well — but (a)(4) conflates a bankruptcy wipeout with a cash merger, and box (b) is used
for some post-closing merger removals too.** The checkbox alone is not a census.

**But the form carries its own footnote, which I read directly, and it is the way in:**

> "Form 25 and attached Notice will be considered compliance with the provisions of 17 CFR
> 240.19d-1 as applicable."

**An exchange filing under (b) attaches a Notice giving the reason.** Timing, from the rule: a (b)
strike requires notice to the issuer, an appeal opportunity, and **public notice at least 10 days
before effectiveness**; a (c) withdrawal requires **10 days' written notice to the exchange plus a
press release stating the reasons**; and **(d)(1): the Form 25 is effective 10 days after filing**.

### 5.2 Form 25-NSE — the reason letter, verified

The exchange's own filing carries the attachment. I read one: **OceanTech Acquisitions I Corp.,
Form 25-NSE, 2024, document `otecdelistreason.txt`** [PRIMARY DATA DOC] [read]. Filed by **The
Nasdaq Stock Market LLC**. It names the specific rules failed — **Listing Rule 5550(b)(2)**, then
**5550(a)(3)**, then **5250(c)(1)** — walks the full compliance / hearing / panel / appeal timeline
from July 2023 to May 2024, and gives the final determination date and the **delisting effective
date of 30 September 2024**.

**That is machine-parseable cause of death, from the exchange, in the primary record, free.**

### 5.3 8-K Items 3.01 and 1.03 — the best of the lot

**Official Form 8-K** [PRIMARY DATA DOC] [read in full on the relevant items]:

**Item 3.01, "Notice of Delisting or Failure to Satisfy a Continued Listing Rule or Standard;
Transfer of Listing."** Triggered when the registrant receives notice that it does not satisfy a
continued-listing standard, **or** that the exchange has submitted a 12d2-2 application to delist it.
The registrant must disclose:

> "(i) the date that the registrant received the notice; (ii) the rule or standard for continued
> listing on the national securities exchange or national securities association that the registrant
> fails, or has failed, to satisfy; and (iii) any action or response that, at the time of filing, the
> registrant has determined to take in response to the notice."

Sub-items (b) self-reported non-compliance, (c) public reprimand letters, and (d) board-authorised
transfers are separately required. **Instruction 1 exempts redemption/maturity delistings** — i.e.
the item is *deliberately* scoped to the distress cases.

**Item 1.03, "Bankruptcy or Receivership."** Required on appointment of a receiver or a court
assuming jurisdiction; **(b) additionally requires disclosure on confirmation of a plan**, including
the numbers of shares allowed under the plan and the assets and liabilities at confirmation. **That
sub-item is what tells you whether existing equity was cancelled — a true −100% — from the free
primary record** (§2.6).

**Deadline, read directly from General Instruction B.1:** *"a report is to be filed or furnished
within four business days after occurrence of the event."*

**This is a genuinely point-in-time source.** The event date, the receipt date, the filing date and
the EDGAR acceptance timestamp are all in the record, so look-ahead is a convention rather than a
hazard.

### 5.4 Coverage, and how to pull it in bulk

Verified live against the EDGAR full-text search API (`efts.sec.gov/LATEST/search-index`):

| form | query | hits | earliest visible |
|---|---|---|---|
| **25-NSE** | `"delisting"` | **2,449** | **2006-11-17** |
| **25** | `"securities"` | **2,821** | **2007-02-01** |
| **15-12B** | `"securities"` | **5,198** | 2001-01-30 |
| **8-K** | `"Item 3.01"` | **≥10,000** (capped) | **2004-12-20** |

**Read these as coverage probes, not as a census** — they are keyword searches with a 10,000 cap,
and EDGAR full-text search itself only reaches back to 2001. **For an exhaustive, point-in-time
enumeration the right object is the quarterly index**: `https://www.sec.gov/Archives/edgar/full-index/
YYYY/QTRn/form.idx` — verified to exist (2024 QTR1: form.idx 54 MB, plus `.gz`/`.zip`/`master.idx`),
listing every filing by form type, company, CIK, date and path.

**How far back each runs:**

- **Form 25 / 25-NSE: 2006.** Electronic filing on EDGAR was mandated by SEC Release 34-52029
  (2005), and the earliest 25-NSE I can see is November 2006 — consistent. **Before 2006, Form 25
  is not on EDGAR.** Irrelevant here: the fixture starts 2010.
- **8-K Items 1.03 / 3.01: August 2004**, when the numbered-item Form 8-K took effect; earliest
  Item 3.01 hit I see is 2004-12-20. **The fixture's whole window is covered with six years to
  spare.**
- **Form 15 (15-12B / 15-12G / 15-15D): on EDGAR well before 2001.** Note what it is: Form 15 is
  **deregistration**, i.e. **going dark**. It has no cause field. **Going dark is not failure**, and
  conflating them is exactly the error the census warns against.
- **SEC 12(j) revocations / the Delinquent Filings Program:** free on sec.gov as administrative
  proceedings, but **they arrive long after the stock has left the exchange** — the issuer is already
  on the pink sheets and far below any $5 floor. **Downstream and late; not useful as a signal, and
  only a coda for a census.**
- **Chapter 11 dockets:** PACER is paid; RECAP/CourtListener is free but **its bankruptcy coverage is
  thinner than its district-court coverage** [from a search summary of CourtListener's own coverage
  page; I did not open it]. **For listed companies 8-K Item 1.03 dominates it** — it is complete by
  regulation, dated, and free.

**Summary of what distinguishes what:**

| source | acquisition | failure | going private | going dark | back to |
|---|---|---|---|---|---|
| Form 25 checkbox | (a)(3) yes; cash deals muddled into (a)(4)/(b) | (b) yes | (c) yes | (c) yes | 2006 |
| **Form 25-NSE reason attachment** | — | **yes, with the specific rule** | — | — | 2006 |
| **8-K Item 3.01** | no | **yes, with the rule and the receipt date** | no | no | **2004** |
| **8-K Item 1.03** | no | **yes — bankruptcy, and equity cancellation at (b)** | no | no | **2004** |
| Form 15 | no | no | partial | **yes** | pre-2001 |
| SEC 12(j) | no | yes, but very late | no | yes | long-running |

---

## 6. What I would and would not do with this

**Do (cheap, and it settles the method half):** the two assertions in §2.5. They need no external
data and no new runner. If the final-price distribution for delisted-while-held names sits at the
floor, **write the immateriality into the record and close the method half.**

**Do (cheap, and it fixes a premise the fixture cannot currently answer):** pull 8-K Item 3.01 and
Item 1.03 plus Form 25-NSE reason attachments from the EDGAR quarterly indexes for 2010–2026, and
**attach a cause to every delisting date in the fixture.** The fixture presently knows *that* a name
died and not *why*. §3 says the split should come out near 60/37/3, and if the fixture's own split
is far from that, the delisting flag itself is suspect — in the direction Shumway documented, benign
deaths recorded and for-cause deaths dropped.

**Do not:** build a distress signal. §4.2 is the reason and it is sufficient on its own: **+0.09% per
month from 2003 onward, with the sign flipped, on the canonical measure, in the canonical
replication.** §4.1, §4.3 and §4.4 are three further independent reasons, any one of which would
also be enough.

**The honest summary of route (b) as tested here.** The premise — *the move is large and slow
relative to the spread* — is **half true and fatally so**. The move is large and slow. But it points
**down**, so capturing it requires a short, which is excluded ground; the spread on the names
carrying it is **an order of magnitude above the 33.8 bp measured on names actually held**; the
commission scales as 50/P against a cohort defined by low P; and the effect stopped existing in
2003. **Route (b) may well be the right doctrine. This is not its instance.**

---

## 7. What I could not verify, stated plainly

1. **The exact 2010–2026 cause-of-death split.** Doidge–Karolyi–Stulz (2025) present the
   year-by-year decomposition of the delist rate into merger / cause / voluntary as **Figure 4, a
   chart**. I read the figure caption and the methodology but **could not read numeric values off a
   plot**. My 2010s claim is therefore **directional only** (the for-cause rate fell), quoted from
   their text. The hard counts I give — 9,749 / 7,120 / 434, and 37% for cause — are **1975–2012 and
   1997–2012**, not 2010–2026.
2. **The World Federation of Exchanges' "Global delisting trends" article**, which a search summary
   claimed gives M&A >60%, voluntary <10% and ~30% involuntary in 2023 for 2010–2024. **WebFetch →
   focus.world-exchanges.org: HTTP 403.** I have **not** cited those figures as established and the
   programme should not use them from this brief.
3. **Nasdaq and NYSE continued-listing price standards.** The $1.00 minimum bid price, the 30
   consecutive business days trigger, the 180-day cure and possible second 180 days, and NYSE
   802.01C's $1.00 average closing price — **all taken from law-firm commentary in search summaries.
   I did not open the Nasdaq rulebook or the NYSE Listed Company Manual.** The §2.5 and §4.3
   arguments lean on this; the direction is not in doubt but the exact day-counts are
   [snippet only].
4. **Guragai (2022) deficiency-notice CARs (−1.8% / −2.0% / −11.5%).** I opened the **RePEc listing
   and read its abstract, which contains no numbers**. The three figures come from a **search-result
   snippet of the ScienceDirect abstract**, and **I did not open the paper**. The quantity I most
   wanted — the **post-filing drift, and whether it survives cost** — **is in none of the material I
   read.**
5. **Beaver, McNichols & Price (2007).** I have this **[abstract only, from search summaries]** —
   that including delisting firm-years raises trading-strategy returns for earnings, cash-flow and
   book-to-market strategies and lowers them for accruals, because of the disproportionate number of
   delisting firm-years in the lowest decile. **I never opened it and I quote no magnitude from it.**
   It is the most directly relevant modern paper on how delisting returns move an anomaly's headline,
   and it is the biggest gap in this brief. **WebFetch → sciencedirect.com and ssrn.com were not
   attempted after the pattern of 403s; a library copy would settle it.**
6. **Any post-2000 measurement of the delisting return itself.** The −30% is Shumway's 1962–1993
   NYSE/AMEX; the −55% is 1977–1994 Nasdaq; Macey et al. is **NYSE, 2002, n=57**. **I found no study
   measuring realised delisting returns on a 2010s sample.** Every magnitude in §2 is therefore
   **extrapolated across at least fifteen years and across a market-structure change** (decimalisation,
   the OTCBB's demise, OTC Markets tiering). The programme should treat the constants as
   order-of-magnitude, not as calibration.
7. **Whether the −55% double-counts a spread this programme already models.** §2.2 decomposes it as
   −40% price plus ~15 points of liquidity haircut, which is Shumway–Warther's own arithmetic. **I
   have not verified how any downstream user handles that**, and applying −55% on top of an explicit
   Corwin–Schultz spread model would charge the same liquidity twice.
8. **CRSP's current imputation practice.** A search summary attributed to "CRSP documentation" a
   scheme of code-banded replacement values (−0.50/−0.55 for 200–299, −0.40/−0.45 for 500–570,
   −0.30/−0.35 for 571–600). **I could not locate that in a CRSP primary document and I do not
   believe it as stated** — the 200s are mergers, for which large negative imputations make no sense.
   **Do not use those numbers.** The Shumway/Shumway–Warther constants in §2.2, which I read from the
   papers, are the defensible ones.
9. **The fixture itself.** I have no access to it. Everything in §2.5 and §3's premise check is
   **arithmetic offered for the programme to run**, not a finding. In particular I do not know
   whether the $5 floor ejects held positions or only gates entry, and **that single unknown
   determines whether the method half is material or a footnote.**

### 7.1 Blocks, logged by tool and response

- **WebFetch → scholar.harvard.edu: HTTP 403** (Campbell–Hilscher–Szilagyi *JF* PDF). Worked around
  via NBER WP 12362, read in full.
- **WebFetch → www.ecfr.gov: HTTP 302** redirect to `unblock.federalregister.gov` (a bot-check
  interstitial), so the rule text was not returned. Worked around via law.cornell.edu.
- **WebFetch → focus.world-exchanges.org: HTTP 403.** Not worked around; see §7.2.
- **WebFetch → alphaarchitect.com: HTTP 403.** Practitioner piece on handling delistings; not
  worked around, and it would only ever have been [PRACTITIONER] anyway.
- **WebFetch → www.sec.gov/rules/final/34-49858.htm: HTTP 301** to `/rule-release/34-49858`. Not
  re-fetched; the Form 25 and rule text were obtained directly instead.
- **WebFetch → www.sec.gov/cgi-bin/browse-edgar** with `type=25-NSE` and no CIK: returned
  *"The value you submitted is not valid. Please try a different selection."* Worked around via the
  `efts.sec.gov` full-text search API and the `full-index` directory.

### 7.2 A method note worth keeping, because it cost me four wasted calls

**WebFetch's summariser cannot read PDFs.** Every PDF I fetched came back as *"the content appears to
be a corrupted or heavily encoded PDF file"* — the model is handed the raw byte stream. **But
WebFetch saves the PDF to disk and prints the path**, and `pypdf` is installed in this environment.
Extracting locally turned five "unreadable" fetches into full readings of Shumway 1997,
Shumway–Warther 1999, Doidge–Karolyi–Stulz 2017 and 2025, Campbell–Hilscher–Szilagyi, Hou–Xue–Zhang,
Macey–O'Hara–Pompilio and the official Forms 25 and 8-K. **Any future research lane fetching papers
should do this rather than accepting the summariser's refusal**, which otherwise silently downgrades
a full reading to an abstract.

---

## 8. Sources

| source | type | how well established |
|---|---|---|
| Shumway, *The Delisting Bias in CRSP Data*, **JF 52 (1997) 327–340** — [free PDF, author's site](https://www.tylergshumway.org/Shumway-DelistingBiasCRSP-1997.pdf) | [PEER-REVIEWED] | **[read in full]** — Tables I, IV, V, VI, VII extracted directly |
| Shumway & Warther, *The Delisting Bias in CRSP's Nasdaq Data...*, **JF 54 (1999) 2361–2379** — [free PDF](https://tylergshumway.org/Shumway-DelistingBiasCRSPs-1999.pdf) | [PEER-REVIEWED] | **[read in full]** — Tables I–V and the −55% derivation extracted directly |
| Macey, O'Hara & Pompilio, *Down and Out in the Stock Market*, **J. Law & Econ. 51 (2008) 683–713** — [free NBER conference PDF](https://users.nber.org/~confer/2004/mmf04/macey.pdf) | [PEER-REVIEWED] | **[read in full]** on all cited numbers |
| Doidge, Karolyi & Stulz, *The U.S. Listing Gap*, **NBER WP 21181** (→ *JFE* 2017) — [PDF](https://www.nber.org/system/files/working_papers/w21181/w21181.pdf) | [PEER-REVIEWED] (WP version read) | **[read in full]** on §5–§6, incl. the delist decomposition |
| Doidge, Karolyi & Stulz, *Are There Too Few Publicly Listed Firms in the US?*, **NBER WP 33556 (2025)** — [PDF](https://www.nber.org/system/files/working_papers/w33556/w33556.pdf) | [WORKING PAPER] | **[read in full]** — but the delist decomposition is **Figure 4, a chart** (§7.1) |
| Campbell, Hilscher & Szilagyi, *In Search of Distress Risk*, **JF 63 (2008) 2899–2939** — read via [NBER WP 12362](https://www.nber.org/system/files/working_papers/w12362/w12362.pdf) | [PEER-REVIEWED] | **[read in full]** — Table 6 portfolio returns extracted directly |
| Hou, Xue & Zhang, *Replicating Anomalies*, **NBER WP 23394** (→ *RFS* 2020) — [PDF](https://www.nber.org/system/files/working_papers/w23394/w23394.pdf) | [PEER-REVIEWED] (WP version read) | **[read in full]** on the distress results and the Fp/O/Z construction |
| **SEC Form 25** (SEC 1654, OMB 3235-0080) — [sec.gov](https://www.sec.gov/files/form25.pdf) | [PRIMARY DATA DOC] | **[read in full]** |
| **SEC Form 8-K**, Items 1.03 & 3.01, Gen. Instruction B.1 — [sec.gov](https://www.sec.gov/files/form8-k.pdf) | [PRIMARY DATA DOC] | **[read in full]** on those items |
| **17 CFR 240.12d2-2** — [Cornell LII](https://www.law.cornell.edu/cfr/text/17/240.12d2-2) | [PRIMARY DATA DOC] | [read via WebFetch summary; eCFR itself blocked, §7.1] |
| **Form 25-NSE reason attachment**, OceanTech Acquisitions I Corp., 2024 — [EDGAR](https://www.sec.gov/Archives/edgar/data/1846809/000135445724000702/otecdelistreason.txt) | [PRIMARY DATA DOC] | **[read]** |
| **EDGAR full-text search API** (`efts.sec.gov`) and **full-index** directory | [PRIMARY DATA DOC] | **[queried live]** — coverage probes only, not a census |
| Richard Price, *Delistings* (`_dlret_rv.sas`) — [page](https://sites.google.com/site/richardaprice3/research/delistings) | [PRACTITIONER] | [read via WebFetch] — code, **no data** |
| Chordia, *The Distress Anomaly Puzzle*, ABFER keynote digest 2023 — [PDF](https://abfer.org/media/research-digest/2023/The-Distress-Anomaly-Puzzle_digest_digest_2023_Tarun-Chordia.pdf) | [PRACTITIONER, conference digest] | **[read in full]** — a digest of a talk, **not evidence for a return** |
| Guragai, *Market response to stock exchange listing deficiency notices*, **Advances in Accounting 59 (2022)** — [RePEc](https://ideas.repec.org/a/eee/advacc/v59y2022ics0882611022000359.html) | [PEER-REVIEWED] | **[abstract only]** via RePEc; **the CARs quoted in §4.3 are [snippet only] and the paper was NOT opened** |
| Beaver, McNichols & Price, *Delisting returns and their effect on accounting-based market anomalies*, **JAE 43 (2007) 341–368** | [PEER-REVIEWED] | **[abstract only, from search summaries] — NOT opened, no magnitude quoted.** §7.5 |
| Nasdaq 5450(a)(1)/5550, NYSE 802.01C price standards | [PRACTITIONER, law-firm commentary] | **[snippet only]** — rulebooks not opened. §7.3 |
| CourtListener/RECAP bankruptcy coverage | [PRACTITIONER] | **[snippet only]** — coverage page not opened |

**No vendor material is cited as evidence for any return.**
