# The plumbing round — round 3 external evidence

**Round 3 of the lead scan.** Six territories commissioned 2026-09-09 on the principal's
instruction, after all six round-2 briefs had landed. Contract, territory selection and the
exclusion list every prompt carried: [`working/leads3/README.md`](../../working/leads3/README.md).
Round 1: [`the-negative-space-scan.md`](the-negative-space-scan.md) §9a–§9b. Round 2:
[`the-forced-seller-and-the-cost-wall.md`](the-forced-seller-and-the-cost-wall.md).

**STATUS: COMPLETE — all six briefs in** (`G1`–`G6` in [`working/leads3/`](../../working/leads3/)).

---

## THE HEADLINE

**All six lanes returned negative on the signal, and the round is the most valuable of the three
anyway.** Every lane was told to name the number that would kill it before measuring a return, and
**five of the six were killed by that number rather than by a return** — a count, an `n_eff`, a
cost, a floor interaction. That is the premise-first design working exactly as intended.

**And the pattern is now three rounds old and no longer deniable: THE PLUMBING OUTLIVES THE LEADS.**
Round 1 produced a floor-methodology hole and a fixture-composition defect. Round 2 produced a
biased spread estimator, an auction cut-off and a spin-off adjustment mechanism. **Round 3 produced
two live bugs in code this programme already runs, a measured account of the vendor defect behind
two separate incidents on the record, and a reduction of the delisting-return question to a single
code check.** Not one of the three rounds produced a strategy, and **all three produced things the
programme was wrong about.**

**The reading rule is unchanged.** Every claim about the outside world is attributed and tagged with
how well it was established — `[read in full]` · `[abstract only]` · `[snippet only]` ·
`[UNVERIFIED]`. **No claim below was measured on this programme's fixture.** Where a brief measured
something on a *public* file, it is tagged `[MEASURED IN BRIEF]` and the file is named. Under
[R15](../RULES.md#r15) **nothing here closes or admits anything.**

---

## 1. The findings that are not about any territory

### 1.1 TWO LIVE BUGS IN A SCRIPT THIS PROGRAMME ALREADY RUNS — `scripts/d331_edgar_deals.py`

**From `G4`.** These are the highest-value items in the round because they are **not** about a lane
that was rejected; they are about a code path that is in use.

**Bug one — `filingDate` is a look-ahead.** The SEC moved the 13D/G EDGAR cut-off from **5:30 pm to
10:00 pm ET on 2024-02-05**, so **a filing dated `D` can be accepted six hours after `D`'s close.**
`acceptanceDateTime` exists in the submissions API (in UTC); the brief reports that
`d331_edgar_deals.py` **uses `filingDate` only and never touches acceptance.**

**Bug two — a form-type string changed and will silently zero the modern sample.** Verified four
ways in the brief: the EDGAR index string is **`SC 13D` in 2015 and `SCHEDULE 13D` in 2025**; an
EDGAR full-text query for `forms=SC 13D` over March 2025 returns **0 hits**; and SEC DERA's own CSV
dates the switch precisely — **2024: 1,024 old + 76 new; 2025: 0 old + 1,115 new.**

> **A filter on `form == "SC 13D"` returns nothing after roughly 2024-12-18 AND DOES NOT RAISE.**

**That is the failure mode this programme has a standing rule about**: an empty result that looks
like an answer. **Neither bug is repaired here and neither should be repaired without the
principal's instruction** — but both are stated in the form an assertion could be written against.

**A third item, structural rather than a bug.** `G4` establishes that the correct pull direction is
**full-index → accession → subject CIK**, which is **dead-inclusive by construction** and avoids
`company_tickers.json` entirely. The existing puller goes **symbol → CIK**, which is the
survivorship-exposed direction. Also: **each accession appears on two index rows** (issuer and
filer) **with no label saying which**, so the header must be fetched to tell them apart.

### 1.2 THE VENDOR DOCUMENTS TWO DIFFERENT ADJUSTMENT BASES ON ONE PAGE

**From `G6`, and this is the mechanism behind an incident already on the record.**

`TIME_SERIES_DAILY_ADJUSTED` returns **"raw (as-traded)"** OHLCV, with adjustment confined to a
separate `adjusted close` column. `TIME_SERIES_INTRADAY` has **`adjusted` defaulting to `true`.**
**That is the documented mechanism for "the 15m fixture is fully adjusted and the daily fixture is
not"** — a difference this programme discovered empirically and could not attribute.

**The vendor's own support FAQ contradicts its API documentation**, saying it adjusts open, high,
low, close and volume. **Two vendor bases and two vendor documents that disagree is the finding.**

**A negative that strengthens it.** Two GitHub issues alleging bad prices (AAPL at $601 in 2014,
NVDA above $500 in 2021) turn out **not** to be defects — **both users were wrong and the API was
right**, which corroborates the as-traded semantics *more* strongly than a bug report would have.
**`G6` reports this against its own interest and it is the most credible item in the brief.**

### 1.3 TICKER REUSE, MEASURED — AND THE FOLKLORE WAS WRONG

**From `G6`, `[MEASURED IN BRIEF]` on Alpha Vantage's own published listing files**, which the
public demo key served in full before rate-limiting.

**28 of 425 tickers delisted by 2014-07-10 are active today under unrelated issuers** — DNA
(Genentech → Ginkgo Bioworks), PATH (NuPathe → UiPath), SWIM (thinkorswim → Latham). **Two have
literally OVERLAPPING windows — CNH (17 days) and CSR — where the vendor's two records directly
contradict each other.**

**The correction:** the waiting period is **24 months, not 90 days** (NMS symbology plan §IV(d),
`[read in full]`), **and the holding exchange faces no waiting period at all** — only an
investor-confusion test.

**And `LISTING_STATUS` delisted rows carry the CURRENT ticker-holder's identity.** Provable with no
external source: a row named for a 2×-short NFLX ETF has an **ipoDate of 1997**, eleven years before
Netflix listed; a row named "2X SHORT PANW" is dated **delisted 2011**, a year before Palo Alto
listed. The brief also found a row whose `name` field is the literal string `NASDAQ`, and a symbol
`-P-HIZ`.

### 1.4 THE SOURCE-SIDE MECHANISM FOR ROUND 1'S CEF DISCOVERY, AND IT IS LIVE TODAY

**From `G6`, `[MEASURED IN BRIEF]`.** `assetType` has **exactly two values across 14,408 rows.**

```
814 of 8,607 "Stock" rows are preferreds, warrants, units or rights, by the vendor's own suffixes
905 of 5,801 "ETF"   rows have no "ETF"/"ETN" in the name -- 628 with closed-end-fund naming
                     including a corporate bond and a SPAC unit
```

**Round 1 found that a fixture labelled ETF was 27% closed-end funds. This is where that comes
from, and it is present in the ACTIVE list today** — so it is not a historical artefact of one
build. `G6` also notes it caught and corrected one of its own broken measurements mid-analysis
(a grep matching the `assetType` field rather than the name, returning 0 instead of 905).

### 1.5 `data.sec.gov/submissions/` IS SURVIVORS-ONLY FOR TICKERS — TWO AGENTS, TWO ROUNDS

**Convergence worth recording because the agents were on different territories and did not see each
other's work.** Round 2's `F3` found delisted issuers carry **empty `tickers` arrays** while their
filings survive (verified on SVB Financial). Round 3's `G1` fetched three records independently:
**Sears Holdings and Bed Bath & Beyond both return empty `tickers[]` and `exchanges[]`; Apple
returns `["AAPL"]`.**

**So the trap is one layer deeper than `company_tickers.json`, in the per-CIK API as well.**

**And the obvious workaround does not hold.** BBBY's CIK is now named `20230930-DK-Butterfly-1,
Inc.`, so **name-keyed joins are silently point-in-time-wrong**. `formerNames` carries dated ranges
and is the one genuinely point-in-time field — **but it was populated for BBBY and EMPTY for
Sears.** `G1` found **no free, dead-inclusive, point-in-time CUSIP↔ticker bridge**; FIGI is the best
candidate and is **optional, and only from 2023-01-03.**

**The one place this is already solved** is round 2's `F2` finding: `ISSUERTRADINGSYMBOL` is NOT
NULL *inside* every Form 4, so the ticker is what the issuer said it was on the filing date. **That
solution is form-specific and does not generalise to 13D/G or 8-K.**

### 1.6 THE DELISTING-RETURN QUESTION REDUCES TO ONE CODE CHECK, AND BOTH ANSWERS FLATTER A LONG BOOK

**From `G2`, and it corrects my own framing of the lane.**

The convention *"positions are carried to the final bar and closed there"* **is arithmetically
identical to setting the delisting return to zero** — the exact error Shumway (1997) and
Shumway–Warther (1999) were written about. Both `[read in full]`: **−29.9% mean (median −31.3, s.d.
48.9, 71.3% coverage) NYSE/AMEX, and −55% Nasdaq**, the latter decomposing as **−40% price plus
~15 points of spread haircut — so it must NOT be double-counted against a Corwin–Schultz cost
model.** Macey–O'Hara–Pompilio corroborate independently of CRSP.

**The mitigant nobody named: every one of those numbers is measured on names priced $0.57–$1.09,
and this fixture floors at $5.** So the whole method half reduces to one question:

> **Does a held name that falls through the $5 floor get EJECTED, or CARRIED to its delisting?**

**Both answers flatter a long book, and the second is the more interesting.** If it is carried, the
missing terminal return is the Shumway bias. **If it is ejected, that is an UNDECLARED STOP-LOSS AT
$5 truncating every trade's left tail** — which is a live methodological issue independent of any
delisting question. **This is settleable with no external data and no measurement of returns.**

**And my commissioning premise was overstated.** I wrote that a name filing Chapter 11 after its
last print *"books its last quoted move, not its loss."* Macey et al.: **average time from
bankruptcy filing to delisting is 131 trading days** (Enron 30, Owens Corning 2+ years). **The
Chapter 11 crash is normally INSIDE the tape.**

**Direction, stated:** omitting the delisting return **flatters a long book unambiguously and
punishes a short book** — there is no wash-out, because the missing returns are nearly all negative.

### 1.7 TOOLING — one hazard, two corrections

**THE HAZARD, and it is serious.** `G3` reports that **WebFetch's PDF summariser FABRICATED a table
of reversal percentages that does not appear in the source document.** It caught this by
re-extracting every cited PDF locally with `pypdf`. **A summariser that invents a number is worse
than one that fails**, because the failure is silent and looks like a reading.

**Consequence for this record and the last:** any figure sourced through an HTML or PDF summariser
is **weaker than `[snippet only]`, not stronger.** Round 2's `F4` already flagged summariser-derived
content as *"one step weaker"* — **that was more right than it knew.**

**CORRECTION ONE, and it is useful.** `G1` and `G2` independently report that **WebFetch's
"corrupted PDF" response is NOT a block** — the bytes land on disk and `pypdf` reads them. `G2`
converted **seven "unreadable" fetches into full readings** this way; `G1` read six sources so.
**Several `[UNVERIFIED]` tags in round 2 may have been avoidable.**

**CORRECTION TWO.** `G5` reports **every IBKR 403 was a User-Agent exclusion, not a host block** —
curl with a browser UA returned 200. That matches the standing rule that a logged block names the
tool, not the host, and is the second time it has been confirmed.

### 1.8 A PRIVACY SLIP, DISCLOSED BY THE AGENT ITSELF

**`G5` discloses that its first successful `sec.gov` fetch used a User-Agent containing the
principal's personal email address**, before it switched to a neutral contact string. SEC
fair-access requires an email-shaped token in the User-Agent, which is why it reached for one.
**It should have used a project address and says so itself.**

**The committed code is clean and was checked here rather than assumed.**
`scripts/d331_edgar_deals.py` sends `BacktestFramework research script
research@backtest-framework.org`, and its own docstring says *"this is a project mailbox, not a
personal one."* **The address appears nowhere in `scripts/`, `docs/` or `data/`.** The exposure is
one request in one agent session, not a standing leak.

### 1.9 THE $25,000 PATTERN-DAY-TRADER RULE WAS STRUCK ON 2026-06-04

**From `G5`, read directly in the deletion text of the SEC-hosted Exhibit 5.** FINRA **struck Rule
4210(f)(8)(B) in full** — the pattern-day-trader definition, the $25,000 minimum and 4×
day-trading buying power are **Reserved**; the $25,000 carve-out in 4210(b)(4) is gone, leaving
plain **$2,000**. The replacement is a risk-based **intraday margin deficit** regime, with a 90-day
freeze for a *"practice"* of unmet deficits and a de minimis carve-out at the lesser of 5% of equity
or $1,000.

**But it is not yet safe to assume it applies:** IBKR's own page, dated 2026-06-03, says accounts
*"may still be subject to existing PDT rules during FINRA's transition period, which ends in October
2027."* **And the old rule only ever bit same-session round trips** — cells holding ≥2 bars were
never exposed.

---

## 2. `G1` — forced institutional flow · **DEAD TWICE OVER, INDEPENDENTLY**

**Kill one, in our own currency.** The only paper that ever produced a tradeable forced-sale effect
(Dyakov & Verbeek, JBF 2013, `[read in full]`) states its own breakeven: **0.35%/side.** Against
**33.8 bp/side that is 1 bp of margin**, before commissions, on a **1990–2010** sample. Its own
**2001–2010** subperiod already shows monthly alpha at **−0.08% (SE 0.23)** — zero — and the daily
path is **−55 bp at 10 days (SE 22)**, reverting to −21 bp by day 20. **55 bp gross against a 67.6
bp round trip fails by 12.6 bp, in the decade that ends where this fixture begins.** It existed only
in below-mean-NYSE-size names — where per-share cost in bp is largest.

**Kill two — the premise number, and it lands on our own null standard.** Free structured N-PORT
starts **2019-10**, giving **27 formation dates**, not 67. Monthly public N-PORT **does not exist
and may never**: the 2024 amendments were delayed in April 2025 to **Nov 2027 / May 2028**, and the
SEC **proposed in Feb 2026 to restore quarterly publication permanently.** After an autocorrelation
haircut, `N_eff ≈ 20–68` against 4,190 bars — a **~600× overstatement, ≈24× t-stat inflation**.
Decisively:

> **The rotation group is 26 offsets, not ~4,000. At n = 26 a sample p95 has no resolving power, so
> under D373's 2-SE rule NOTHING on the free window can be resolved.** The lane fails this
> programme's own null standard before a return is measured.

**The finding to read first, because it is about the flagship paper.** Lou (2012) `[read in full]`:
**realised flow-induced trading has no forward return.** The decile spread is **+5.19% (t = 7.77)
in the ranking quarter — contemporaneous, not tradeable** — and *"indistinguishable from zero in the
following year."* The forward-predictive variable is built from **lagged fund performance**, and Lou
states it *"accounts for about half of the price momentum effect."* **The tradeable half of the
canonical result is a momentum proxy, which is on the exclusion list.**

Wardlaw (JF 2020) `[abstract only — SSRN/Wiley/RG/UGA all 403]`: the standard measure *"is
inadvertently a direct function of a stock's actual realized return"*; corrected, outflows give a
negligible decline *"with no subsequent reversal."* Huang–Ringgenberg–Zhang `[abstract only]`:
managers **choose** which names to dump and discretionary trades **contain fundamental information**
— which attacks route (a)'s premise where a per-name variable lives.

**The ETF leg has a published negative in our own universe.** Ben-David–Franzoni–Moussawi (JF 2018)
`[read in full]`: 1-SD ETF flow → **−15.6 bp over 20 days** on the S&P 500, needing **4.3 SD** to
clear a 67.6 bp round trip. **For the Russell 3000 the mispricing reversal is "close to zero and
statistically insignificant" and the first-day flow impact is WRONG-SIGNED.** And high ETF ownership
widens Corwin–Schultz spreads by **+1.7%** — the cost term moves against us.

**One thread not killed, and labelled honestly:** a 2026 arXiv preprint reports **160 bp at 3
months** with turnover surviving 33.8 bp/side. It is **unrefereed, single-author, no stated
affiliation**, and **its own author calls it "a way to locate the premium rather than as a scalable
arbitrage."** It is a quarterly tilt — route (b) smuggled into a route (a) lane — and the
observation-count objection still applies.

## 3. `G2` — the death process · **METHOD HALF LIVES (see §1.6), SIGNAL HALF DEAD FOUR WAYS**

**(i)** Campbell–Hilscher–Szilagyi's +10.2%/yr is almost entirely the **short leg**; the long leg is
**+3.4%/yr, t = 1.45**. **(ii)** Hou–Xue–Zhang: **+0.09%/month from 2003 onward — sign flipped**;
O-score, Z-score and credit rating all insignificant. **(iii)** The cohort is below the floor —
bid-price death takes **210–390 days under $1**. **(iv)** Macey measures **589 bp/side spread on
names STILL LISTED in the 60 days before delisting**, against this programme's 33.8, with commission
scaling as `50/P`.

**The census kill condition was NOT met, so the cohort exists.** Doidge–Karolyi–Stulz: **9,749
merger / 7,120 for cause / 434 voluntary — 56% / 41% / 2.5%**, 1975–2012, with **37% for cause over
1997–2012.** Not overwhelmingly acquisition. **But their 2025 update finds the 2010s for-cause rate
fell to a historical low, and the exact 2010–2026 numbers are in a CHART the agent could not read.**
**So the census is answered for the wrong window and remains open for ours.**

**The data answer is the lane's real deliverable, verified against the actual SEC documents.**
**8-K Item 3.01** requires the deficiency-notice receipt date **and the specific rule failed**,
within four business days. **8-K Item 1.03(b)** gives equity cancellation at plan confirmation — **a
free, true −100%.** **Form 25-NSE** carries a reason attachment naming exact listing rules (the
agent read one). **Coverage runs from 2004/2006 — the whole fixture window.** Form 25's checkboxes
separate involuntary from voluntary, **but (a)(4) conflates bankruptcy wipeout with cash merger.**

## 4. `G3` — halts and resumption · **DIES ON ARITHMETIC**

**The premise count is low double digits over 2010–2026 — and roughly three independent episodes,
not N events.** Nobody publishes the count, so the brief **constructs** it from primary sources
and **flags its two weakest terms as its own unsourced assumptions**, which is the correct way to
hand over a constructed number.

**The decisive evidence was a live primary feed, not a paper.** The Nasdaq halt RSS on 2026-09-09
carried **12 open halts older than one session — eleven T12, one H11 — and not one had a resumption
time.** The oldest has been halted since **2019-02-22**. Cooley reports **14** exchange-listed
Asia-IPO names SEC-suspended Sept 2025–Apr 2026, kept halted past the ten days, **none resumed** as
of 2026-04-27.

> **The modal multi-day US exchange halt is not an event with a resumption. It is a waiting room
> for delisting.**

**Three further kills, each independent.** **LULD is a 15-second phenomenon** — DERA (Moise &
Flaherty 2017, `[read in full]`) finds limit states *"are reversed within 15 seconds for both
tiers"*, and **there is no daily field that records a pause at all.** **A multi-day halt reprices
entirely inside one halt-cross auction**, so a daily-bar system's earliest fill is the resumption
close — **route (b)'s premise fails on its own terms: the move is large but not slow.** And **the
liquidity floor and the event are the same measurement** — trailing ADV over the halt window reads
zero; over the pre-halt window it describes a market state the halt destroyed.

**Data: there is no free, dead-inclusive, point-in-time halt history for 2010–2026.** Nasdaq halt
search is **1 year, verbatim**; NYSE **1 year, News-Pending and LULD only**. The Cboe "historical
downloads" archive is a trap — the agent fetched two files directly and found **19 and 12 rows,
Cboe-listed only.** SEC §12(k) suspensions are free and complete (**1,349 orders, oldest
1995-10-13**) but are **OTC-dominated and are orders, not issuers.**

**Two items worth more than the verdict.** **The count is computable from this programme's own
fixture today** — count tickers with ≥1 entirely missing session followed by a bar — **but only if
the fixture preserves missing sessions rather than forward-filling.** That is a `G6`-class
assertion and it decides whether the event is even visible. And **the population is one regulatory
episode, not a base rate**: SEC Rel. 34-105494 fn.28 gives Nasdaq manipulation referrals of
**10 (2022), 8 (2023), 52 (2024), 91 (2025), 46 (2026 to date)** — a ~10× shift — with Nasdaq now
raising the listing bar that generates them.

**An open reconciliation on our own record, NOT a correction.** D343 describes NBIS as *"the former
Yandex's first day back after an eight-month halt."* `G3` puts the public record at **YNDX halted
2022-02-28, resumed as NBIS 2024-10-21 — about 32 months.** **Neither figure has been verified
against the fixture here.** It stands flagged and unresolved.

## 5. `G4` — 13D/13G · **FOUR INDEPENDENT KILLS, AND THE DATA SECTION OUTLIVES THEM (§1.1)**

**1. The famous 7% decomposes badly.** Brav–Jiang–Partnoy–Thomas (2008) `[read in full]`: *"a
run-up of about 3.2% between 10 days to 1 day prior to filing. The filing day and the following day
see a jump of about 2.0%."* **The run-up is the accumulator and is not buyable. The tradeable jump
is ~2.0%.**

**2. What survives lives exactly where the floor cuts.** deHaan, Larcker & McClure (RAS 2019,
`[read in full]`): equal-weighted long-run returns are driven by **the smallest 20% of targets,
average market cap $22 million.** The larger 80% go insignificant **within three months** and sit at
an insignificant −1.6% at two years. **Value-weighted, every long-run horizon is zero.** Brav's own
Table VI showed it in 2008 — **EW (1,3) alpha 1.09%/mo (t = 2.01) against VW 0.14% (t = 0.28).**
**A $5-close plus dollar-volume screen is close to a filter that deletes the only quintile that
works.**

**3. The premise count collapses.** SEC DERA primary data — **the agent parsed the raw CSV after
finding the fetch tool's summary of it had shifted every year by one row** — gives **a mean of 1,397
initial 13Ds per year, 2010–2025.** But the SEC's own Table 2 finds **80% are "corporate action"
filings, not campaigns**, and Table 1 reports **60 initial 13Ds by prominent activists in 2022, from
22 filers.** Much of the 80% is deal-related, i.e. excluded ground.

**4. The lag is a completed trade.** SEC Table 3: **80% of activist filers had accumulated their
full stake within five business days of crossing 5%** — before the filing existed. Median
trigger-to-filing is 9–10 days.

**The caveat that matters most, in the agent's own words:** it **could not measure the floor-pass
rate** — "a few dozen per year" is an inference from median market caps, not a measurement, **and it
is the number to check first.** And **there is no post-2020 return measurement in the brief from any
source**; the strongest post-2010 positives reached it only as the SEC's footnote characterisations
of three papers it did not open, flagged in the same sentence as each number.

## 6. `G5` — the revenue side of a long book · **NO SIGNAL, AS PRE-AUTHORISED**

**The conversion, derived from the broker's own published mechanics** (102% collateral, /360 day
count, 50% split):

```
bp per bar held  ≈  0.205 × gross market fee (% p.a.) × utilisation
```

**The median US common stock's indicative fee has been ~0.5% p.a., flat, 2003–2025**; 68% of
firm-days in 2024:01–2025:06 were below 1%; NYSE deciles 4–9 average ~0.4% p.a. **That is
0.08–0.10 bp/bar at full utilisation against a 33.8 bp/side spread.** The broker's own investor deck
says general-collateral stock is *"less likely to be lent"* at all.

**The non-obvious part, and it inverts my commissioning premise.** The universe is **not** obviously
general collateral — **NYSE decile 1, 40% of names by count, averaged 26.4% p.a. in 2025**, and a $5
floor plus a volume screen does not exclude it. **But fee-sorted portfolios have CAPM alpha ≈ −1 ×
fee** (top portfolio **−81.4%/yr, t = −5.87**, `[working paper, read in full]`), and the lender's
share is 50%.

> **Selecting for lendability selects for negative alpha. The revenue is a partial rebate on a
> loss.** My premise — *revenue accruing to a held position is arithmetically identical to alpha* —
> is right arithmetically and **inverted economically.**

**And the brief refuses to over-dismiss, which is worth as much as the kill.** Against a **1.06 bp**
breakeven, **4 bp accrued over a 40-bar hold is larger than the edge.** The honest headline is
*"negligible against the spread, potentially comparable to the edge on long-hold cells"* — **not
"zero."**

**Cash interest is a hurdle, not a prize:** ~1.25 bp/bar on uninvested cash **above a $10,000
zero-rate floor**, scaled linearly below $100,000 NAV — **arithmetically nil at $25,000 NAV.** Its
real use is making "CAGR at 40% exposure" interpretable, which this programme's own reporting rule
already demands.

**Wash sales are a TIMING distortion, not a cost**, except at the year boundary and on same-day
netting of identical blocks — **US treatment presented as US treatment, with the jurisdictional
caveat stated loudly, because this programme's records do not state a jurisdiction.**

## 7. `G6` — documented data defects · **THE STRONGEST RETURN OF THE ROUND**

Findings are in §1.2, §1.3 and §1.4 above, because they are not about a territory. Two more:

**Reverse splits turn an adjustment error into a ONE-SIDED SELECTION error** against a $5 as-traded
floor — **concentrated in exactly the distressed cohort that supplies tail trades.** The floor is
defined on as-traded prices, so an adjustment defect is a **membership** defect, which is the more
serious of the two.

**CRSP's primary documentation, `[read in full]`, explains the fabricated-dividend class.** For
spin-offs, rights and partial liquidations `facpr = DIVAMT / P(t) ≠ facshr`, and *"shares and
volumes are only adjusted using stock splits and stock dividends."* **A two-field schema — split
coefficient plus dividend amount — has only ONE place to put that DIVAMT.** That is the forcing that
produces corporate actions booked as dividends.

**The bar this lane was set, and whether it cleared:** every finding was required to come with the
assertion that would catch it, in the form *"assert X about the data"* rather than *"be careful
about X"*. **It cleared.** It also states plainly that it **read zero peer-reviewed sources** and
never read the vendor's `LISTING_STATUS`, `SPLITS` or `DIVIDENDS` docs verbatim.

**Safety:** the demo-key response **contains text instructing the reader to register for an API
key**. The agent **quoted and flagged it and did not act on it**, which is the required behaviour.

---

## 8. Sources

Full per-source detail, with exact URLs and per-source tags, is in the six briefs under
[`working/leads3/`](../../working/leads3/). Consolidated here by strength.

**`[read in full]` — the load-bearing readings.** Lou (2012) · Dyakov & Verbeek (JBF 2013, via the
author's thesis chapter) · Ben-David, Franzoni & Moussawi (JF 2018) · Brown, Davies & Ringgenberg ·
Israeli, Lee & Sridharan · Shumway (1997) and Shumway–Warther (1999) · Macey, O'Hara & Pompilio ·
Campbell, Hilscher & Szilagyi · Hou, Xue & Zhang · Doidge, Karolyi & Stulz · Moise & Flaherty (SEC
DERA 2017) · Brav, Jiang, Partnoy & Thomas (2008) · deHaan, Larcker & McClure (RAS 2019) ·
Daniel, Klos & Rottke `[working paper]` · CRSP *Factor to Adjust Price* and CRSP Calculations ·
the NMS symbology plan §IV(d).

**`[PRIMARY DATA DOC]`, fetched live.** SEC N-PORT `FUND_REPORTED_INFO` readme — **`SALES_FLOW_MON1/2/3`
and `REDEMPTION_FLOW_MON1/2/3` (Item B.6) make per-fund MONTHLY flows free from 2019-10, no CRSP
needed** · SEC DERA 13D/G statistics CSV · SEC Rel. 34-105494 · SEC §12(k) suspension orders ·
8-K Items 3.01 and 1.03(b) · Form 25 and Form 25-NSE with a reason attachment · the EDGAR
submissions API · FINRA Rule 4210 deletion text in the SEC-hosted Exhibit 5 · Nasdaq and NYSE halt
feeds and archives · Cboe halt files · Alpha Vantage API documentation and support FAQ · the
`LISTING_STATUS` files served by the public demo key.

**`[abstract only]` / `[snippet only]` — and each is flagged where used.** Wardlaw (JF 2020) —
**never opened, and it carries a load-bearing claim** · Huang, Ringgenberg & Zhang · Coval &
Stafford · Beaver, McNichols & Price — **`G2` names this as its biggest gap** · Greenwood & Schor ·
the three post-2010 activism papers `G4` knows only through SEC footnote characterisations.

**`[UNVERIFIED]` / `[USER REPORT]`.** A 2026 arXiv preprint on flow-induced pressure — unrefereed,
single-author, no stated affiliation · two GitHub issues alleging Alpha Vantage price errors,
**both of which turned out to be user error** · a claimed CRSP imputation table which **`G2`
explicitly says not to use.**

**`[SALES INSTRUMENT]`, none used for a number.** Broker investor decks and marketing pages;
activism-tracking products; paid halt vendors (algoseek, Databento), cited only as cost.

---

## 9. Blocks — tool and response, not host

`WebFetch → papers.ssrn.com`: HTTP 403, repeatedly · `WebFetch → onlinelibrary.wiley.com`: 403 ·
`WebFetch → researchgate.net`, `uga.edu`: 403 · `WebFetch → investor.gov`: 403 ·
`WebFetch → federalregister.gov`: 302 to an interstitial · `WebFetch → listingcenter.nasdaq.com`:
403 · Alpha Vantage demo key: empty `{}` responses after rate-limiting, which **stopped `G6`
confirming delisted-list coverage**.

**Two entries that are NOT blocks and are recorded so they are not mistaken for blocks again:**
**WebFetch's "corrupted PDF" response** — the bytes land on disk and `pypdf` reads them; and
**every IBKR 403**, which was a **User-Agent exclusion** (curl with a browser UA returned 200).

**And one entry that is worse than a block: WebFetch's PDF summariser FABRICATED a table** (§1.7).

---

## 10. What this record does not claim

- **Nothing here was measured on this programme's fixture.** The only figures restated from our own
  record are **33.8 bp/side**, the **67.6 bp** round trip implied by it, the **1.06 bp** intraday
  breakeven, the **$5** floor, **4,190 bars**, and D343's NBIS description — all quoted, none
  recomputed.
- **`[MEASURED IN BRIEF]` means an agent measured a PUBLIC file**, named in the brief. It does not
  mean anything was measured here.
- **Nothing was backtested, no null was drawn, no cell was scored, no candidate exists.**
- **The two bugs in §1.1 are REPORTED, NOT REPAIRED**, and the delisting-floor question in §1.6 is
  **stated, not answered.** Both are the principal's call.
- **No territory is closed.** Five lanes returned negative on the signal and the sixth was never a
  signal hunt; closure remains the principal's under [R15](../RULES.md#r15).
- **Three of my own commissioning premises were wrong** and are recorded as mine: the Chapter 11
  timing (§1.6), the lending-revenue economics (§6), and route (b)'s applicability to halts (§4).
- **Both books are unchanged.**
