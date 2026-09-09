# The forced seller and the cost wall — round 2 external evidence

**Round 2 of the lead scan.** Six territories commissioned 2026-09-09 under
[`working/leads2/README.md`](../../working/leads2/README.md); its exclusion list is the durable
record of what round 2 was kept off. Round 1 is [`the-negative-space-scan.md`](the-negative-space-scan.md)
§9a–§9b.

**STATUS: PARTIAL — three of the briefs are in (`F2`, `F3`, `F4`); `F1`, `F5`, `F6` are still
running.** This record is written now rather than held, and will be extended in place as the rest
land. **Sections for the outstanding three do not exist yet; their absence is not a verdict.**

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
- **`F1`, `F5` and `F6` are missing and their absence is not a verdict.** This record will be
  extended in place.
- **Both books are unchanged. Nothing is closed and nothing is admitted** — that remains the
  principal's call under [R15](../RULES.md#r15).
