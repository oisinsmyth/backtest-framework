# The reversal round — round 6 external evidence

**Round 6 of the lead scan.** Six territories prepared and commissioned 2026-09-10; contract,
selection principle and the exclusion list every prompt carried:
[`working/leads6/README.md`](../../working/leads6/README.md). Index: [`README.md`](README.md).

**STATUS: COMPLETE — all six briefs in** (`K1`–`K6` in [`working/leads6/`](../../working/leads6/)),
with derived evidence promoted into [`data/`](../../data/) under `k2_`, `k3_`, `k4_` and `k5_`
prefixes.

---

## THE HEADLINE

**`K6` reverses this programme's central operating assumption, and the correction is to a premise I
put into its own prompt.**

> **For the anomalies that actually survive post-2005, COST IS NOT THE BINDING CONSTRAINT. And this
> programme's 33.8 bp/side is NOT above the cost-honest literature — IT IS THAT LITERATURE'S OWN
> NUMBER.**

The cost-honest literature **measures** the average effective spread paid by **204 academic anomaly
implementations** post-2005 at **68 bp**, and charges **half per trade: 34 bp/side.** It separately
measures **67 bp paid against 16 bp for the average NYSE stock** — a factor of four, because that is
what an anomaly portfolio actually trades. **Any lane rejected because this programme's costs looked
unusually high was rejected on a false premise.** I wrote that premise into `K6`'s prompt myself.

**And `K3`'s mandated negative control caught a broken route before it produced a brief.** The
retrieval path I suggested **silently ignores the parameter the whole census depends on** — an
impossible code returned the identical count to no filter at all. **Had the lane trusted it, every
code and every year would have shown the same number.**

**Reading rules unchanged.** Claims about the outside world are attributed and tagged for how well
they were established; **a figure from a summariser is weaker than `[snippet only]`**; **an HTTP 200
can be wrong**, so a parameterised harvest carries a negative control; `[MEASURED IN BRIEF]` means an
agent measured a **public** file or endpoint. **Conflicts are recorded, not adjudicated** (§10).
Under [R15](../RULES.md#r15) **nothing here closes or admits anything.**

---

## 1. The findings that are not about any territory

### 1.1 COST IS NOT WHAT BINDS THE SURVIVORS — AND THREE OTHER THINGS DO

**From `K6`.** Survivors are annually rebalanced with one-sided turnover of **1.2–7.2%/month**, which
at 33.8 bp/side costs **~1.4 bp/month.** What binds instead:

```
THE GROSS EDGE IS GONE      post-2005, top 90% of market cap, ~200 published anomalies:
                            MEDIAN 7 bp/month GROSS, MEDIAN t = 0.45
                            against 48 bp in the all-stock / pre-2006 cell.
                            ~85% of published alpha required BOTH pre-2006 data AND microcaps.
WHAT REMAINS IS MOSTLY LUCK Var(t) = 1.09 vs a luck-only 1.00 -> signal share 0.08
                            best survivor 66 bp -> 6 bp.
                            A second study reaches 6 bp BY A DIFFERENT ROUTE.
IT LIVES IN THE SHORT LEG   long-minus-market Var(t) = 0.98, BELOW the null
                            -> every survivor's long-only return shrinks to 0.00%/month.
                            162 anomalies: +0.14%/month before borrow fees, -0.01% AFTER.
```

**`[read in full]` for the first two; the borrow-fee figure is `[abstract only]`.**

### 1.2 ZERO OF THE SURVIVORS ARE COMPUTABLE FROM THE DATA THIS PROGRAMME IS PERMITTED

**From `K6`, and it is the sharpest single sentence of the round.** Of the ten strongest post-2005
survivors: **seven need Compustat fundamentals, two of the three price-only ones are on this
programme's own exclusion list, and one needs options.**

> **Zero are computable from permitted free daily price and volume data.**

**This is not a claim that nothing is tradeable.** It is a claim about **the published survivors**,
and `K6` says so. The shared features it did extract — low turnover, holds in months, a **persistent
characteristic rather than a dated event**, a short leg, ≥20 names per leg, and a
turnover×illiquidity interaction under which **costs are immaterial even in microcaps for annually
rebalanced signals** — are the deliverable, and they describe a different kind of strategy from
anything this programme has built.

### 1.3 SURVIVAL IS CLOSE TO RANDOM WITH RESPECT TO OBSERVABLE FEATURES — AND THE FREE DRAFT SAYS THE OPPOSITE OF THE PUBLISHED PAPER

**`K6` was given permission to reach this and reached it.** It also caught the trap inside it:

> **A working-paper draft reports that turnover reliably predicts post-2005 net returns. The
> PUBLISHED version says no predictor is reliable and that turnover enters WITH THE WRONG SIGN. THE
> DRAFT IS THE FREELY-INDEXED ONE.**

**The only feature that does predict persistence — being expensive and hard to arbitrage — is the
same feature that makes an effect untradeable here.**

**`K6`'s own largest fragility, self-flagged:** one author writes four of its load-bearing sources
and they share one dataset. **The post-2005 collapse is corroborated across different cuts but not by
an independent group with independent portfolio construction.**

### 1.4 THE EQUAL-WEIGHT BIAS IS PAID PER REBALANCE, NOT PER BAR — AND `J3` RECONCILES TO 2%

**From `K5`, which answered the decisive question first.** A multi-bar-hold book does **not** carry
the large version of the bias: it comes from a noisy **denominator reset only at entry**, and the
generalised estimator's bias term is **exactly zero for every bar after the first of a hold** when
noise is serially uncorrelated — so bias per bar ≈ `(1/H)·σ²(1−ρ)`.

> **THE CHECK THAT SETTLES IT HERE: does the weight array get recomputed from the current bar's close
> for names already held, or only at entry?**

**And round 5's measurement reconciles with the mechanism.** Inverting the verified closed form,
`J3`'s **+0.30%/yr implies 34.5 bp/side** against this programme's measured **33.8** — agreement to
**2%**. Two independent briefs, one cross-validation, **and the mechanism is bid-ask bounce.**

**Four further results.** The bias lives almost entirely in **gross** — a factor of ~300 against a
cost already charged. **The floor's leverage is quadratic (`∝ 1/P²`)**, sharper than this repo's
existing note that cost scales inversely with price. **In a RANKED book the bias is the difference of
the legs' noise variances** — 0.09%/mo for a book-to-market sort but **0.61%/mo for a share-price
sort, which kills that premium outright — and that risk does not shrink with holding period**, because
it comes from the selector covarying with spread. And **a Corwin–Schultz σ is a lower bound on total
price noise**, so `K5`'s own reassuring arithmetic is lower-bound reassurance.

**The canonical 1983 paper could not be obtained, and the failure is committed as evidence:** the
host returned **HTTP 200, `text/html`, 1,651 bytes, `<title>404Handler</title>`** — reproducing
`J3`'s failure exactly — and the only archive capture is that same page.
[`data/k5_rotman_blume_stambaugh_404_at_http200.html`](../../data/k5_rotman_blume_stambaugh_404_at_http200.html).
`K5` read the generalised form elsewhere and **derived the bid-ask form itself rather than trust a
summariser**, catching that summariser's worked number wrong — **0.3% claimed, 0.2506% computed.**

### 1.5 A SECOND SOURCE FOR THE EX-DATE IS UNAVAILABLE IN PRINCIPLE, NOT MERELY NOT FOUND

**From `K4`, and it is a structural answer rather than a failed search.** Eleven candidates probed
live, all failed. But:

> **17 CFR § 240.10b-17(b)(1) enumerates every field an issuer must notify — declaration, record,
> pay-or-delivery, amount, rate, fractional settlement, conditions, transfer agent — AND THE EX-DATE
> IS NOT AMONG THEM.** The ex-date is *designated* by the exchange under FINRA 11140(a), not declared
> by the issuer. **So EDGAR — the only free, CIK-keyed, dead-inclusive candidate — structurally
> cannot carry the one field a price file joins on.**

**Verified here rather than taken:** a grep of the committed rule text for `ex-date`, `ex date` and
`ex-dividend` returns **nothing**
([`data/k4_ecfr_10b-17_notification_fields.xml`](../../data/k4_ecfr_10b-17_notification_fields.xml)).

**Two free dead-inclusive cross-checks DO work**, both CIK-keyed XBRL facts — **for ratios and
amounts only, never dates.** One split is tagged to a whole month and its real ex-date falls outside
it.

**One issuer, one document, two conventions:** a single 8-K carries its split at `ex − record = +2`
and its cash dividend at `0`, and the issuer's own headline calls a date *"effective"* that sits one
business day from the market's ex-date. **And you cannot audit a split file against Rule 11140(b)(2)
— which sends any distribution ≥25% ex AFTER the pay date — because the split records carry no pay
date.** The rule's only input is absent from the file.

**`K4` delivered 25 numbered assertions**, with the four it could not reduce labelled `[WORRY]` per
the rule. **The cheapest pair is elegant: assert the two declared ex-dividend holes are empty — a
RECOMPUTED ex-date column cannot produce them, and a PUBLISHED one cannot avoid them.**

**One thread worth chasing:** the rule page shows an amendment **effective 2010-12-15 — inside this
window.** If it touched (b)(1) or (b)(2) there is a **fourth regime boundary eleven days after the
first bar.** One document away.

### 1.6 THE EARNINGS-ABSORPTION FINDING DOES NOT GENERALISE BY ITEM CODE — AND THAT DOES NOT REFUTE ROUND 5

**`K3` was commissioned to turn round 5's meta-finding into a screen. It cannot be done by that
route, and the reason matters.**

> **Dividend initiations, dividend cuts and stock splits HAVE NO 8-K ITEM CODE.** They are prose
> inside 8.01, 7.01 and 2.02 bodies. **So a census of item codes cannot reproduce, confirm or refute
> `J2`'s 62.2%/59.2% or `J1`'s 36–68%** — and `K3` states plainly that **it would not have caught
> the two lanes that died.**

**Round 5's finding is a TEXT-level phenomenon; `K3` measured an ITEM-CODE-level one. Both stand,
neither displaces the other, and a text-level measurement is what would generalise `J1` and `J2`.**

**At item-code granularity, absorption is small.** Substantive event codes — 5.02, 1.01, 2.03, 3.02,
5.07 — co-file with 2.02 in only **1–4.5%** of cases, rising **+0.3 to +1.5 pp** in sixteen years.
**Three codes moved the other way: 5.07, 3.01 and 2.06.**

**The census is complete, not sampled:** all **1,185,352** 8-K submissions, 2010-01-01 to 2026-09-08,
33 codes, dead-inclusive. **Sampling error zero.**
[`data/k3_census.json`](../../data/k3_census.json), [`data/k3_tables.md`](../../data/k3_tables.md).

### 1.7 ITEM 7.01 IS THE ONE LARGE CLEAN ABSORPTION TREND

**From `K3`.** Reg FD disclosure rose from **12.85% to 24.04%** of earnings submissions, **up in 16 of
16 steps**, and it survives a **constant-issuer panel of 2,342 filers at +8.49 pp.**

> **Treat any Item 7.01 filing as earnings-contaminated by default.**

**And the reverse view undercuts the tidy story, which is the honest part.** Mean codes per earnings
submission went **2.200 → 2.355 (+7.0%)** — **but non-earnings 8-Ks accreted codes slightly FASTER
(+0.167 against +0.151), so "earnings submissions are becoming bundles" is not specific to
earnings.**

### 1.8 TWO FREE POINT-IN-TIME DATA ROUTES WERE BUILT THIS ROUND

**Neither is a signal, and both are reusable.**

**`K2` reconstructed a free point-in-time GICS sector history.** The eleven Select Sector SPDRs
**partition** the S&P 500 by GICS sector — the sponsor's methodology says *"one and only one Select
Sector Index"* — so their N-PORT filings give **28 quarter-end snapshots, 2019-09-30 → 2026-06-30, 27
consecutive transitions, zero gaps.** A CUSIP in fund A at `t−1` and fund B at `t` is a sector change
**with index membership unchanged — add/delete excluded by construction rather than by filtering.**
[`data/k2_migrations.json`](../../data/k2_migrations.json) and its scripts.

**`K1` produced a dead-inclusive identification recipe for listing transfers:** 8-K Item 3.01(d)
keyed on the **stated action date** (the filing may lag four business days), plus **Form 25/25-NSE**
for the departing exchange and **8-A12B** for the destination, all from the EDGAR quarterly index.
**Bonus: the 25-NSE accession prefix is the exchange's own filer CIK**, resolving the departing venue
free for **99.8% of 28,544 rows.**

### 1.9 THE WRONG-HTTP-200 CATALOGUE REACHES NINE FLAVOURS

**Every one measured in this programme. Five were on the record before this round; four are new.**

| | what returned 200 | what it was | round |
|---|---|---|---|
| 1 | a parameterised census | **a CDN cache replaying another query** | R4 |
| 2 | a dead ticker's price series | **a different company's prices** | R4 |
| 3 | a paper's PDF | **a 404 handler page**, 1,651 bytes | R5 |
| 4 | a paging parameter | **silently ignored, replaying page 1** | R5 |
| 5 | a field named `fullCount` | **an array index** | R5 |
| **6** | **an eCFR rule request** | **a 171-byte error body** — *"requires response compression"* | **R6 `K4`** |
| **7** | **a dead ticker's split history** | **TWO ISSUERS BLENDED IN ONE DOCUMENT** — ETF title, Sears' business text, Sears' split factors, the ETF's 2023 inception in the return block | **R6 `K4`** |
| **8** | **a gated vendor symbol** | **valid JSON, 220 bytes, NO `data` KEY** — a status-checking loop would write the whole dead cohort as dividend-free | **R6 `K4`** |
| **9** | **a bogus fund ticker** | **a plausible 56 KB fund-page shell** | **R6 `K2`** |

**Plus two parameters silently ignored by primary sources:** the **EDGAR full-text search `items`
filter** (`K3` — the route this round's own prompt recommended) and **`Range` headers on SEC
Archives** (`K1` and `K3`, independently).

**Bodies committed as evidence:**
[`data/k4_two_issuers_blended_at_http200_SHLD.html`](../../data/k4_two_issuers_blended_at_http200_SHLD.html),
[`data/k4_vendor_gated_200_valid_json_no_data_key.json`](../../data/k4_vendor_gated_200_valid_json_no_data_key.json),
[`data/k4_ecfr_endpoint_error_body_at_http200.html`](../../data/k4_ecfr_endpoint_error_body_at_http200.html).

### 1.10 RESEARCH METHOD — three of this repo's own rules were applied unprompted, and two operational facts

**`K3` proved chunk == whole bit-identically** — a twelve-way parallel run against a single-process
rerun, sha256 match, **and the check was proved able to fail.** That is `CLAUDE.md`'s speed rule and
its `[X]` rule, neither of which was in the prompt. It also **re-derived every published figure by
assertion script, which caught two overstated prose claims in its own text.**

**`K2` caught a 2.5× count error by looking at the names rather than the count** — cash-sweep lines
sharing one CUSIP across all eleven funds, and foreign issuers under placeholder CUSIP `000000000`
colliding into absurd pairings. **That is the name-the-top-trade rule, applied unprompted.**

**`K3` recorded its own wrong answers:** two earlier timezone samples returned 0% because they
concentrated in a few large filers.

**Two operational facts about this harness and this programme's own habits:**

> **A STOPPED BACKGROUND TASK IS NOT A STOPPED PROCESS.** `K1` reports that `TaskStop` killed two
> wrappers **and left their Python children fetching**; three of its processes then competed for one
> IP's SEC rate limit, earned a 429 and dragged throughput to 0.73/s.

> **SEC RATE LIMITING IS CUMULATIVE, NOT BURST.** `K3` earned a 429 **across all of sec.gov** from
> total volume rather than burst rate, and `K2` lost **286 of 352 filings SILENTLY** under four
> unpaced threads. Round 5 had already found the 10 req/s limit applies **across all hosts, not per
> host.**

**And the lane-unique filename rule worked** — 77 `K2_` files, ~45 `K3_` files and ~20 `K4_` files
coexisted in one scratchpad with no collision, after round 5's two agents overwrote each other's
helper script.

### 1.11 `company_tickers.json` — SIXTH CONFIRMATION, AND A NEW FAILURE MODE

**`K1` measured it dropping 108 of 330 transfer CIKs — 32.7%.** `K4` measured **10,407 rows with zero
of four dead probes.** **And `K1` found a worse mode than omission: it returns SUCCESSOR tickers for
renamed issuers**, one of which yields a 2015 "close" of **$2,187,900**.

**Also from `K4`:** EDGAR renders one failed bank as `SIVBQ` — **the terminal symbol, not the
in-panel one.**

### 1.12 THE `acceptanceDateTime` TIMEZONE DEFECT IS INDEPENDENTLY REPRODUCED

**`K3`, on 51 filings across 33 CIKs: 32 (62.7%) carry Eastern wall clock mislabelled as `Z`** —
consistent with round 4's 35 of 60. **Neither filer agent nor era predicts it reliably, so the field
needs a per-filing header check rather than a rule.** No census figure is affected, because `K3`
buckets on `filingDate`. [`data/k3_tz_stratified.json`](../../data/k3_tz_stratified.json).

**Two more route facts:** `-index-headers.html` returns **404 for every 2010–2013 filing** — use the
dissemination `.txt`.

---

## 2. `K1` — exchange listing transfers · **PASSES MORE KILLERS THAN EXPECTED; `K1` REPORTS IT DIES ON COUNT**

**It passes the earnings confound decisively — the first territory in six rounds to do so.** Transfer
8-Ks co-file with Item 2.02 in **1.7–3.6%** (n = 1,187 / 232 / 110), against `J2`'s 62.2%/59.2% and
`J1`'s 36–68%. **Controls returned 0.**

**It passes the price screen going up.** Nasdaq→NYSE transferees: **median close $31.51, 0.0% below
`$5`.** **My "transferring companies are established" premise is false going down:** moves to the
lower tier run **$7.02/$7.41 median with 37–44% already below `$5`** — because **the listing standard
is `$4.00`, not `$5`** (read off the exchange's own rule PDF), and the lower tier was `$2`/`$3` until
2026. One 2014 move was announced at a **$2.59** close.

**Kill number (a), measured** `[MEASURED IN BRIEF]` from a dead-inclusive EDGAR census — 71 quarterly
indices, 77,101 rows, ~2,700 primary documents read: **343 operating-company common-equity transfers
over 16.7 years = 20.5/year** (7.0 Nasdaq→NYSE, 6.9 NYSE→Nasdaq). **After `$5` + $1m dollar-volume:
≈6.7 and ≈5.0 events/year, both upper bounds.** No trend. Corroborated by a published count (53
NYSE→Nasdaq switches in 16 years) and by the exchange's own marketing.

**Kill number (b) is 100%, and it is a tautology** — the Nasdaq Composite requires exclusive Nasdaq
listing and is reconstituted **daily**, so **every Nasdaq↔NYSE transfer IS a Composite membership
change**, and the Nasdaq-100 carries an explicit switched-listing fast-entry rule. **The
qualification that stops it being a pure index duplicate:** the 100%-overlap index carries negligible
flow (~$10.4bn over >2,000 names) while the material one (~$490bn) touches **~0.6–1.5 transfers a
year — and those are exactly the ones that pass a liquidity screen.**

**The finding it did not expect:** of 1,187 8-Ks saying *"transfer the listing"*, **796 (67%) also
say "Nasdaq Capital Market"** and 33% say **"minimum bid price"** — the **intra-Nasdaq tier move a
sub-$1 issuer uses to buy a second compliance period.** The 2022–24 surge is **the sub-$1 wave, not
certification transfers**, the top modern hits for the NYSE phrasing are **all SPACs**, and Item 3.01
overall is **95% deficiency notices**.

**Stated honestly and load-bearing: there is no post-2010 returns study on US inter-exchange
transfers.** `K1`'s decay case rests on **mechanism evidence** — spread convergence, primary listing
venues below 30% of consolidated volume in H1 2025, and a published Nasdaq-100 addition effect
decaying 3.9% → 2.6% → 2.0% with deletions ≈ 0 — **not on a replication that measured post-2010
transfer CARs.**

## 3. `K2` — sector reclassification · **`K2` RECOMMENDS CLOSING IT, ON TWO MEASURED NUMBERS**

**Kill number (a)** `[MEASURED IN BRIEF]`: **20 migrations total — but 17 are ONE structure change**
(14 legs at March 2023 plus a three-name tail), so that is **n = 1 event with 14 legs, not 14
observations.** **Idiosyncratic reclassifications: 3 in 6.75 years = 0.44/year**, and **the last
twelve consecutive quarters contain zero.** The floor removes **nothing** — min price **$74.39**, min
ADV **$71M/day**. **For once the floor is not the problem; there is almost nothing there.**

**Kill number (b):** for the median S&P 500 name the holding SPDR would sell **0.92 × ADV** (q95
2.82) — **but the flow is two-sided at the same close**, so the tradeable quantity is the difference:
across all twenty events, **net median 0.33 × ADV, max 0.70 ×.** An order of magnitude below a
one-sided index addition.

**Three findings that close off my "survives all six on paper" premise.** The 2023 change was
announced **351 days** ahead and the full affected-name list **92 days** ahead. **The flow is
deliberately staggered** — S&P-tracking funds moved 2023-03-17, **MSCI-tracking funds (including
$332bn) at the May review, 2.5 months later — so even the sum of families never lands on one date.**
**The second-largest sector-ETF suite is not GICS at all** (it tracks a different classification and
does not move on GICS dates), **so every headline sector-ETF AUM figure overstates the mandated
pool.** And **idiosyncratic moves lag disclosed news** — one followed the company's own divestiture,
which its 10-K says it re-benchmarked for.

**One point genuinely in the lane's favour, recorded because it is real:** the announcement is an
index-provider press release, so **zero earnings co-filing**, and price is clean (median $147.98,
commission ~0.34 bp/side). **It does not matter at 0.44 events a year against ~10 effective
instruments.**

**Unprompted cross-validation:** the sponsor independently states "14 large cap stocks" for 2023 and
the N-PORT count returns **exactly fourteen, same names**; AUM backed out of holdings × price agrees
with the filed `netAssets` to **1.3%**, and six per-fund estimates to **<0.005%**.

**The gap, in `K2`'s own words and the right framing:** the **2018 Communication Services
restructuring is outside the N-PORT window** and no event study of it was found — *"the one event
that could carry real flow, and I have failed to find evidence rather than ruled it out."* It names
the free route (21 EDGAR N-Q filings) for anyone who wants it.

## 4–7. `K3`, `K4`, `K5`, `K6`

Their findings are in §1.1–§1.12, because none is about a territory.

---

## 8. Sources

Full per-source detail is in the six briefs under [`working/leads6/`](../../working/leads6/).

**`[MEASURED IN BRIEF]` — public data measured by the agents, with artefacts in `data/`.** `K3`'s
complete 1,185,352-submission 8-K census plus three control outputs and four scripts; `K2`'s 352-filing
N-PORT harvest reduced to a 27-transition migration table and a 20-event flow table; `K1`'s 71-index
EDGAR transfer census; `K4`'s eleven live source probes; `K5`'s closed-form enumeration.

**`[read in full]`.** Chen & Welch (arXiv 2607.06502, Jul 2026 draft) · Chen & Velikov (JFQA 2023) ·
Canina, Michaely, Thaler & Womack (1998) — **the primary source for `J3`'s name-count table** ·
Asparouhova, Bessembinder & Kalcheva · Fisher, Weaver & Webb (2012) · Anderson, Eom, Hahn & Park ·
17 CFR 240.10b-17 · FINRA Rule 11140 · the Nasdaq Daily List specification · NYSE Rule 102.01C(II) ·
S&P's Select Sector index methodology · SEC Release 34-81446 and Cboe notice C2024051400.

**`[abstract only]` / `[snippet only]`, flagged where used.** Muravyev et al. (JF 2025) on borrow
fees · Jain & Kim (2006) — **`K1`'s CARs unread** · Blume & Stambaugh (1983), Roll (1983), Conrad &
Kaul — **all unobtainable or unread, so round 4's 52%-vs-97% conflict is left open.**

**`[SALES INSTRUMENT]`, none used for a number.** Exchange listing marketing; index-provider
performance material; fund sponsor pages.

---

## 9. Blocks — tool and response, not host

`urllib → sec.gov`: **HTTP 429 across all hosts, from cumulative volume not burst rate** ·
`curl → jstor.org`: HTML where a PDF was requested · `curl → stooq`: **HTTP 200 carrying a JS
proof-of-work challenge**, not defeated · `curl → sectorspdrs.com`: 200 after redirecting elsewhere ·
`curl → ssga.com` / Yahoo / Vanguard on bogus tickers: 404 / 404 / 403 **(the controls that worked)**
· SSRN and Wiley 403s · **two 200s returning a 19,490-byte faculty page instead of a PDF, caught by
`file` and not by status** — costing `K6` the one published artefact that is literally a screening
protocol.

---

## 10. CONFLICTS — RECORDED UNRESOLVED, NOT ADJUDICATED

Per the principal's standing instruction. **All readings stand; an agent's preference is reported as
its preference.**

| # | question | readings |
|---|---|---|
| **C9** | **the doubled day at the ex-date transitions** | `J6` (R5): a doubled **ex-date** · `K4` (R6): a doubled **settlement** date (2017-09-07, 2024-05-29), **no primary found declaring a doubled ex-date**, and both recovered transition mappings injective. `K4` names a one-line check on this programme's own file |
| **C10** | **how many declared ex-dividend holes** | `J6`: one (2017-09-05) · `K4`: **two** — 2017-09-05 **and** 2024-05-28, both verbatim primary |
| **C11** | **anomaly survival rate** | **35%** vs **85%** from two large replication efforts. **`K6` weights NEITHER, because neither applies costs** |
| **C12** | **is the surviving return in the short leg?** | Chen & Welch: yes, long-minus-market Var(t) below the null · Blitz et al.: contested. **Different statistics AND different samples** |
| **C13** | **cost levels** | Frazzini–Israel–Moskowitz vs Novy-Marx–Velikov. **`K6` resolves it by quoting one side's own text**: their number describes a **patient** trader in a microcap-free universe, while TAQ-based measures capture *"retail traders, liquidity demanders, and impatient traders"* |
| **C14** | **months-positive for the EW bias** | Canina et al.: **99.2%** · `J3` (R5): **92%** |
| **C15** | **EW bias magnitude** | ABK implied **36.4 bp/month** · FWW measured **12.67 bp/month**. Different universes and eras |
| **C16** | **two coefficient signs in the EW-bias literature** | **Canina et al. report two signs coming out BACKWARDS versus Roll (1983) and versus Blume & Stambaugh (1983)** — stated explicitly in their own paper |
| **C17** | **daily EW autocorrelation** *(C5 extended, not replaced)* | `H6` (R4): none citable · `J3` (R5): one figure, 1964–93, judged unusable · **`K5` (R6): a MODERN figure exists — +0.01 to +0.06 full-sample on a $2-floored TAQ panel, INDISTINGUISHABLE FROM ZERO in 2001–08 with the significant values NEGATIVE.** A modern figure for the EW **index** specifically remains a confirmed absence. **All three readings stand** |

**And one apparent conflict that is NOT one, recorded so it is not mistaken for one.** `K3`'s
item-code census finding "absorption is small" **does not contradict** `J1`/`J2`'s text-level 36–68%
and 62.2%/59.2%. **The events those lanes measured have no item code at all**, so the two
measurements are of different objects at different granularities. **Neither displaces the other.**

---

## 11. What this record does not claim

- **Nothing here was measured on this programme's fixture.** `[MEASURED IN BRIEF]` means a public
  file or endpoint. Figures restated from our own record — 33.8 bp/side, the 67.6 bp round trip,
  `keep_v2`'s clauses, ~10 effective instruments — are quoted, not recomputed.
- **Nothing was backtested, no null was drawn, no cell was scored, no candidate exists.**
- **Nothing is repaired.** Every reported defect from rounds 3–6 stands unrepaired, including the
  `SC 13D` filter, the mixed `acceptanceDateTime`, both Corwin–Schultz findings, `adjusted=false`,
  the `LISTING_STATUS date=` call, the four-date bar check, and the equal-weight rebalance check.
- **No territory is closed.** `K1` reports dying on count and `K2` recommends closing; **closure
  remains the principal's under [R15](../RULES.md#r15)**, and `K2` explicitly distinguishes *failing
  to find evidence* from *ruling out*.
- **FIVE of my own premises were wrong this round**, and all five are recorded as mine: **33.8
  bp/side described as above the cost-honest literature** (§1.1 — it *is* that literature's number);
  **the earnings-absorption finding assumed to generalise by item code** (§1.6 — those events have no
  item code); **"transferring companies are established"** (§2 — false for down-moves, and the
  standard is `$4.00`); **the EDGAR `items` filter assumed to work** (§1.9 — silently ignored); and
  **the "size is not price" instruction assumed satisfiable from the anomaly literature** (`K6`: **no
  paper it read reports the nominal price distribution of any anomaly's legs** — the literature
  screens on size, liquidity, spread and turnover, never price).
- **Both books are unchanged. Nothing is elevated out of the research folder.**
