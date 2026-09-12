# A2 — the PERSISTENT-CHARACTERISTIC family

External-evidence brief. Scan-100926, round 1, lane `A2`. Written 2026-09-10.
Contract and the rules this lane carries: [`00-SCHEMA.md`](00-SCHEMA.md); slate:
[`R1-00-slate.md`](R1-00-slate.md).

**I have no access to the programme's data and claim nothing about it.** Every number below is
either from a cited external source — tagged by TYPE and, in the same sentence, by HOW WELL I
ESTABLISHED IT — or is my own measurement on a **public** dataset, tagged `[MEASURED IN BRIEF]`
with the endpoint named so it can be re-run. Under [R15](../../RULES.md#r15) nothing here closes or
admits anything.

**Scope boundary honoured.** This brief does not research momentum, calendar/seasonality effects,
reversal of any kind, lead–lag, short interest, options, earnings dates or PEAD, signal combination,
or multiple-testing methodology as lanes. Where a family lands on the exclusion list I **say so and
say whether it is excluded rather than unavailable**, because the slate asked for exactly that
distinction. Where an excluded family appears in a table it is there as a *benchmark for the
non-excluded ones*, flagged `EXCLUDED`, and nothing is proposed on it.

---

## 0. THE HEADLINE, IN FOUR SENTENCES

1. **The family is real, it is named, and it is two families, not eight.** What survives post-2005
   under a cost-honest bar is **profitability** (annual accounting) and **external
   financing / share issuance** (annual, and one of its members needs only a split-adjusted
   **share count** on top of price). Everything else in the characteristic zoo is either dead in
   modern data, on this programme's exclusion list, or needs data the programme does not have.
2. **The monthly-or-slower horizon is NOT load-bearing in the way the slate assumed — something
   worse is.** I measured the *same* 209 predictors at holding periods of 1, 3, 6 and 12 months:
   the slow families are **almost flat** across that range (fundamentals median 18.3 → 19.8 → 18.2
   → 15.5 bp/month). Flatness means the premium accrues at a **roughly constant rate per month**,
   and that is precisely why shortening the hold is fatal: **you divide the numerator and keep the
   round trip.** At the programme's 67.6 bp round trip plus `50/P` commission, an annual rebalance
   must clear **6.5 bp/month**; a ten-bar hold must clear **155 bp/month**. The best long-only
   characteristic I can measure earns **15 bp/month**. The gap at ten bars is a **factor of ten**,
   not a margin.
   **And I then measured the same thing directly on DAILY returns** (§4.4): apart from a **negative
   first day of the month** — which is the one non-uniform piece of the month and it is a **loss** of
   −11 to −17 bp for the best candidates — the premium accrues **evenly across days 2–21**. The
   method's positive control works: it detects short-term reversal as front-loaded (**11×**) and
   momentum as back-loaded, so "uniform" for the slow families is a measurement and not a lack of
   resolution. **A ten-bar hold earns ~7 bp gross against a 77.6 bp round trip — short by 11×.**
3. **And the public record has no rung below one month.** Across the 331-signal Chen–Zimmermann
   census the **fastest documented rebalance for any published characteristic is 1 month**
   (`[MEASURED IN BRIEF]`, §2). Hou–Xue–Zhang's 447-anomaly replication ladders holding periods at
   **1, 6 and 12 months** and goes no shorter. Chen & Welch state in terms that their result uses
   "the standard monthly-rebalanced long-short portfolios" and hand the rebalancing-frequency
   question back to the reader. **There is no cost-honest evidence at this programme's horizon
   because nobody has published a characteristic premium at a sub-monthly hold.**
4. **The one finding that cuts the programme's way, and it is a correction to an inherited
   premise.** Round 6 carried forward that *"long-minus-market Var(t) = 0.98, below the null, so
   every survivor's long-only return shrinks to 0.00%/month."* That statistic is measured against
   the **value-weighted** market. I recomputed the same luck diagnostic against **the name-weighted
   average of each sort's own bins** — which is what an *equal-weighted* long-only book actually
   competes with — and got **Var(t) = 1.35 to 1.81, not 0.98**, implying a signal share of
   **0.26–0.45 rather than zero** (`[MEASURED IN BRIEF]`, §7). **The long leg is UNRESOLVED, not
   zero.** It is still small: the best shrunk long-only figure under the programme's own `$5` floor
   is **15 bp/month gross** on cash-based operating profitability, against **6.5 bp/month** of
   amortised cost — **~8 bp/month net, ≈1%/yr over the universe, and it needs the ANNUAL income
   statement and balance sheet, which the programme does not have.**

**So the answer to the bar.** §9 is the ranked shortlist: **two honest entries and a third I am
reporting in order to argue against it.** The price-and-volume-only subset is **not closed, but it
is the worst-evidenced corner of the cross-section** — 27 members, 10 of them negative over
2010–2024, 2 of them above *t* = 2 — and its best member's long leg is worth about
**2–4 bp/month shrunk, which does not pay one round trip** (§6). And §8 answers the uncomfortable
question: **yes, it is a different activity**, and I quantify which parts of the apparatus survive
the change and which do not.

---

## 1. SOURCES — TYPE, AND HOW WELL ESTABLISHED

| # | source | type | established |
|---|---|---|---|
| `S1` | Chen & Welch, *What Useful Alphas?*, arXiv 2607.06502 v1, 8 Jul 2026, targeting FAJ | [WORKING PAPER] | **[read in full]** — 24pp PDF extracted locally with pypdf; Tables 2 and 3 and the methodology §II–§IV read verbatim |
| `S2` | Hou, Xue & Zhang, *Replicating Anomalies*; text read = NBER w23394 (May 2017); published RFS 33(5) 2020 | [WORKING PAPER] for the text I read | **[read in full]** — 130pp extracted; §3.2.6 (trading frictions) and §2's holding-period convention read verbatim |
| `S3` | Novy-Marx & Velikov, *A Taxonomy of Anomalies and Their Trading Costs*; text read = NBER w20721 (Dec 2014); published RFS 29(1) 2016 | [WORKING PAPER] for the text I read | **[read in full]** — Table 3 Panel A read verbatim |
| `S4` | Chen & Zimmermann, *Open Source Cross-Sectional Asset Pricing* dataset + `SignalDoc.csv`, v2.0.0 / October-2025 release, `openassetpricing.com` | [SOFTWARE DOC] / primary data | **[read in full]** — 331-row `SignalDoc.csv` and six 25 MB portfolio sets downloaded and parsed locally; see §2 |
| `S5` | Engelberg, McLean & Pontiff, *Anomalies and News*; text read = the authors' 27 Jul 2017 draft at `rady.ucsd.edu`; published JF 73(5) 2018 | [WORKING PAPER] for the text I read | **[read in full]** — 65pp extracted; §2.2–§2.4 and Tables 3–5 discussion read verbatim |
| `S6` | Asness & Frazzini, *The Devil in HML's Details*, FAJ 69(4) 2013; text read = a PDF mirror at `stoxray.com` | [PEER-REVIEWED] — **both authors are AQR, treat as interested** | **[read in full]** — 21pp extracted; abstract and construction §read verbatim |
| `S7` | Novy-Marx & Velikov, *Assaying Anomalies* (SSRN 4338007) — **the paper itself I could not obtain** (§12.1). What I read was the accompanying **MATLAB toolkit source** at `github.com/velikov-mihail/AssayingAnomalies` and the companion site `sites.psu.edu/assayinganomalies` | [SOFTWARE DOC] for what I read | **[read in full]** of `test_signal.m`, `runTestSignal.m`, `makeBasicSortsResults.m` and the repo's 1,476-path tree; **the paper is [UNVERIFIED]** |
| `S8` | Clarke, de Silva & Thorley, *Portfolio Constraints and the Fundamental Law of Active Management*, FAJ 58(5) 2002 | [PEER-REVIEWED] | **[snippet only — via a search summariser]**; the transfer-coefficient range 0.3–0.8 is therefore the weakest-established number in this brief and is used only qualitatively (§5) |
| `K6` | `../../working/leads6/K6-what-the-survivors-share.md` — this programme's own round-6 brief | internal | read in full; **its numbers are inherited, and where I re-derived one myself I say so** |

**No vendor or sell-side material is used as evidence for a return anywhere in this brief.** Three
pages surfaced by search were **[SALES INSTRUMENT]** (`alphaarchitect.com` ×3, `cxoadvisory.com`,
`investresolve.com`, `kitces.com`, `microalphas.com`, `vanguardmexico.com`) and **none is cited for
any figure**. Two arXiv items returned by a horizon search (`2605.23905` on "AI-driven alpha decay",
and a Medium post claiming "signal half-lives of 18 months versus 5–7 years pre-AI") are
**[UNVERIFIED]** — I did not open them, they are not cited, and the 18-month figure is recorded here
only so that nobody later mistakes it for something this lane established.

`S6` is AQR-authored and `S1`/`S4` share an author (A. Y. Chen), which is the same
non-independence `K6` self-flagged. **It matters less here than it did for `K6`, because my
load-bearing numbers are my own measurements on `S4`'s public portfolio files rather than on any
author's summary of them** — but the *portfolios themselves* are still one group's construction, and
that is in §12.

---

## 2. WHAT I MEASURED MYSELF, THE ENDPOINT, AND THE CONTROLS

**Every number in this section and in §3.2, §4.2, §4.4, §5.1, §7 and §11 is committed as evidence at
[`data/a2_persistent_characteristics_measured.json`](../../../data/a2_persistent_characteristics_measured.json)**
(289,347 bytes) — per `00-SCHEMA.md`'s rule that a file a record quotes belongs in `data/`. It carries
every measurement per signal, every control, the endpoint, and each source file's byte count, so all
of it can be re-run.

`[MEASURED IN BRIEF]` throughout. **Endpoint:** `openassetpricing.com/data/` → Google Drive folder
`1qQDuTsnyvWfEJR6nPBQZ8xxlq6bkLG_y`, October-2025 release (v2.0.0), which I enumerated by parsing
the folder's `_DRIVE_ivd` blob (method taken from the `openassetpricing` package's own
`gdrive_parse.py`). Files pulled and their byte checks:

| file | Drive id | bytes | `file -b` |
|---|---|---|---|
| `SignalDoc.csv` (via the repo mirror) | `raw.githubusercontent.com/OpenSourceAP/CrossSection/master/SignalDoc.csv` | 181,712 | `CSV ASCII text` |
| monthly LS returns, OP construction | `10sOryk_ddjkXagaajTKUk1nwJs2ZLRiI` | 3,293,172 | `CSV ASCII text` |
| `PredictorAltPorts_HoldPer_1` | `1Hr10yn1XRq-AYvKpfNLMy5hxY8oOyKYy` | 24,714,265 | `Zip archive data` |
| `PredictorAltPorts_HoldPer_3` | `1pri4os1PUtpuimffXoS37iOGn9xSK48h` | 24,936,076 | `Zip archive data` |
| `PredictorAltPorts_HoldPer_6` | `1Fl44F1GEk8nS9uJpyVWZKhxWYS0CWV23` | 24,950,941 | `Zip archive data` |
| `PredictorAltPorts_HoldPer_12` | `1tjiW2IpogUpujNNgoFAcCk_Yedpfsr-H` | 24,850,017 | `Zip archive data` |
| `PredictorAltPorts_LiqScreen_Price_gt_5` | `1mL44YJHwiLt_ZRdjmiU7-_i4QVtWURLD` | 24,987,135 | `Zip archive data` |
| `PredictorAltPorts_LiqScreen_ME_gt_NYSE20pct` | `1Q4YatQ3soRU_V7VeACwUn2bnCnmhDUI2` | 24,381,719 | `Zip archive data` |
| **`DailyPortfolios/Predictor.zip`** (daily returns, 212 CSVs) | `1dpiDCCS1Uk-CiB6eU1Hc1pI22fTtcRKn` | **232,600,633** | `Zip archive data` |

Long format: `signalname, port, date, ret, signallag, Nlong, Nshort`. Returns are **percent per
month**. `Nlong`/`Nshort` give **leg breadth**, which is how §5 is measured rather than asserted.

### 2.1 The controls, because a harvest with no negative control is not a measurement

**`[C1]` A value that must return zero.** `Cat.Data == 'Telepathy'` → **0 rows** of 331.
`'NoSuchPredictor'` in the returns file's columns → **False**. Months dated ≥ 2099 → **0** of 1,188.

**`[C2]` A second implementation of the load-bearing quantity.** The alt-port files carry their own
`LS` portfolio. I never read it; I computed **highest bin minus lowest bin** myself from the
component bins, then compared. Across **18 signals × 3 constructions the largest monthly
discrepancy is `0.0000`** — exact agreement, 54 of 54 cells. This is the lag-audit pattern applied
to someone else's file, and it is the reason I trust the rest.

**`[C3]` The pipeline must reproduce a PUBLISHED number before it is allowed to produce a new one.**
`S1`'s abstract reports, for the All-Stocks universe, a **median 48 bp/month through 2005 and 19
bp/month post-2005**, with **99% positive** in the first cell.

| cell | my measurement | `S1` published [read in full] |
|---|---|---|
| through 2005, All Stocks | **53.4 bp median**, 60.6 mean, **98.6% positive**, N=212 | 48 bp median, 99% positive |
| post-2005, All Stocks | **20.3 bp median**, 28.1 mean, N=209 | 19 bp median |
| post-2005 cross-sectional `Var(t)` | **2.07**, median *t* **1.15**, N=209 | 1.09 and 0.45 **in their smaller Standard universe** — mine should be larger, and is |

The residual 53.4 vs 48 is what you expect from my using all 212 published columns where they keep
~170 after their sparsity screens. **The pipeline reads the file correctly.**

**`[C4]` A published QUALITATIVE result must come back.** `K6` read Chen & Zimmermann's finding that
the **`$5` price screen is the SOFTEST of the liquidity adjustments**, softer than an NYSE-only
screen, a market-equity screen, or forced value weighting. My medians over 2010–2024:
baseline **21.0 bp/month** → **price > `$5`: 16.1 bp (77% kept)** → **ME > NYSE 20th pct: 14.9 bp
(71% kept)**. The ordering comes back. **But note the level: both screens cost about a quarter of
the median premium, so "softest" is not "free."**

**Two further controls, `[C6]` and `[C7]`, belong to the daily measurement and are stated at
§4.4 — a reconciliation of daily against monthly, and a positive control proving the method has the
resolution to detect non-uniform accrual where it exists.**

**`[C5]` And one control FAILED in a way worth recording.** `std_turn` (turnover volatility) has a
baseline 2010+ return of **23.5 bp/month, t = 0.42**, which the `$5` screen *raises* to **81.0
bp/month, t = 4.93**. A screen that multiplies a premium by 3.4× is a red flag, not a discovery: it
says the unscreened and screened objects are not the same strategy. `CoskewACX` behaves the same way
(13.6 bp → 40.5 bp). **I am naming both and using neither.** Across 209 signals × 6 constructions I
am looking at ~1,250 cells, and §9 applies `S1`'s own shrinkage to every number I rank rather than
quoting raw cell maxima.

### 2.2 The census of what is published, and at what frequency

From `S4`'s `SignalDoc.csv`: **331 rows — 212 `Predictor`, 114 `Placebo`, 5 `Drop`.** Cross-tabbing
the 212 predictors by the data class they need against their documented rebalance period in months:

```
Cat.Data          1m     3m     6m    12m    36m     NA    tot
Accounting        25      1      0     72      0      1     99
Price             31      4      2      7      1      0     45
Analyst           12      1      0      5      0      0     18
Trading            8      0      0      5      0      0     13
Other              9      0      0      3      0      0     12
Options            9      0      0      0      0      0      9
13F                7      1      0      0      0      0      8
Event              8      0      0      0      0      0      8
TOTAL            109      7      2     92      1      1    212
```

Three things fall straight out, and all three are answers to the slate's questions.

- **The fastest documented rebalance anywhere in the census is ONE MONTH.** Over all 331 rows the
  distinct `Portfolio Period` values are exactly `{1, 3, 6, 12, 36}` months. **Zero sub-monthly
  entries.** This is the cleanest statement of the horizon gap I can make and it is measured, not
  argued.
- **Accounting characteristics are ANNUAL (72 of 99); price characteristics are MONTHLY (31 of 45).**
  The "annual rebalance" shape the slate identified is specifically the *fundamentals* shape. The
  price/volume corner of the same literature is a *monthly* shape.
- **A quarter of the published predictors — 58 of 212 — need only `Price` or `Trading` data.** That
  is the pool §6 interrogates, and it is much larger than "two of three price-only survivors," which
  is what `K6`'s top-ten cut implied. **`K6`'s statement was about the top ten; it was not a census,
  and the census is more favourable.**

**One caution on `S4`'s labels, because taking them at face value would be wrong.** `Cat.Data ==
'Price'` means *CRSP price data*, which includes **shares outstanding** and **dividend-inclusive
total returns** — neither of which is raw daily OHLCV. I therefore re-derived the data requirement
of all 58 by hand from `SignalDoc`'s `Detailed Definition` field, and that re-derivation is what §6
reports. Four of the 58 need a share count; one needs intraday trade data; one needs the VIX; one
needs a market-wide liquidity factor; **21 need nothing but daily OHLCV.**

---

## 3. Q1 — THE FAMILIES, NAMED, WITH DATA REQUIREMENT AND COST-HONEST POST-2005 EVIDENCE

### 3.1 The survivor set, and what each member actually needs

`S1`'s Table 2 — the ten highest post-2005 long-short returns in the Standard (top-3,000 ∩ top-90%
of cap) universe — **which I read in full and transcribe here rather than inherit**, with the data
requirement taken from `S4`'s `Detailed Definition` for each signal:

| rank | signal | raw LS %/mo | long−mkt %/mo | **shrunk LS** | rebal | what it actually needs |
|---|---|---|---|---|---|---|
| 1 | Cash-based operating profitability | 0.66 | 0.40 | 0.06 | annual | `revt, cogs, xsga, xrd, rect, invt, drc, drlt, ap, xacc, at` — **full income statement + balance sheet** |
| 2 | Operating profitability (R&D-adj) | 0.60 | 0.26 | 0.05 | annual | `revt, cogs, xsga, xrd, at` |
| 3 | Realized-implied vol spread | 0.59 | 0.35 | 0.05 | monthly | **options** — EXCLUDED ground |
| 4 | Off-season momentum | 0.54 | 0.13 | 0.05 | monthly | prices only — **EXCLUDED** (momentum + calendar) |
| 5 | Net external financing | 0.48 | 0.15 | 0.04 | annual | `sstk, dv, prstkc, dltis, dltr, at` — **cash-flow statement** |
| 6 | Seasonal momentum (16yr+) | 0.48 | 0.21 | 0.04 | monthly | prices + **≥16yr history** — **EXCLUDED** (calendar) |
| 7 | Gross profitability | 0.44 | 0.14 | 0.04 | annual | `sale, cogs, at` — **three line items** |
| 8 | R&D over market cap | 0.41 | 0.33 | 0.03 | annual | `xrd` + market cap |
| 9 | Net equity financing | 0.39 | 0.16 | 0.03 | annual | `sstk, prstkc, at` — **two cash-flow lines** |
| 10 | Operating leverage | 0.38 | −0.01 | 0.03 | annual | `xsga, cogs, at` |

**So the family, named specifically, is two families and a tail:**

**`F-PROFIT` — PROFITABILITY.** Gross profits / assets (Novy-Marx 2013); operating profitability,
R&D-adjusted (Ball et al. 2016); cash-based operating profitability (Ball et al. 2016). Annual
rebalance. **Needs three to eleven annual accounting line items.** `S1`'s category table, which I
read in full, makes this the **only** category with a healthy post-2005 median: mean 0.25, **median
0.24 %/month, 78% positive, N = 9**, against Value/Fundamentals at −0.02/−0.04/47% and Momentum at
0.01/—/53%. `S3`'s cost-honest panel, read in full: gross profitability **gross 0.40 → net 0.37
%/month, net *t* 2.74, one-sided monthly turnover 1.96%, T-costs 0.03 %/month** (1963–2012, VW NYSE
deciles, Hasbrouck spreads).

**`F-FINANCE` — EXTERNAL FINANCING AND SHARE ISSUANCE.** Net external financing and net equity
financing (Bradshaw–Richardson–Sloan 2006) need the cash-flow statement. **But the same economic
family contains three members that need no financial statement at all** — only a **split-adjusted
share count**, because they are defined on the share count itself:

- `ShareIss1Y` — *"growth in number of shares between t−18 and t−6; number of shares is
  `shrout/cfacshr` to adjust for splits"* (`S4` `Detailed Definition`, read in full). **Annual
  rebalance, quintiles, equal-weighted.**
- `ShareIss5Y` — five-year growth in the same split-adjusted share count. Annual, quintiles, EW.
- `CompEquIss` — *"5-year growth rate of market value of equity minus 5-year stock return"*
  (Daniel–Titman composite issuance). Needs market cap and total return; **monthly**.

**This is the single most operationally important sentence in the brief: the share-issuance
sub-family is one number away from being free.** Not a statement about the programme's data — a
statement about the signal's definition.

**The tail.** `S3`'s low-turnover panel (verified by me, `[read in full]`, w20721 Table 3 Panel A,
1963–2012, VW NYSE deciles) also clears costs for **ValProf** (gross 0.82 → net **0.77**, *t*
**4.82**, TO 2.94%), **Investment** (0.56 → **0.46**, *t* 3.60, TO 6.40%), **Value B/M** (0.47 →
**0.42**, *t* 2.39, TO 2.91%), **Asset growth** (0.37 → **0.26**, *t* 1.75), **Accruals** (0.27 →
**0.18**, *t* 1.43), **Size** (0.33 → **0.28**, *t* 1.44) and **Piotroski F** (0.20 → **0.09**, *t*
0.45). **The one-sided monthly turnover band across that whole panel is 1.23% (Size) to 7.24%
(Piotroski F)** — I verified those two endpoints in the table myself, and they are the "1.2–7.2%"
the slate carried. **But that panel's sample ends in 2012 and starts in 1963, and §3.2 shows what
happens to most of it afterwards.**

### 3.2 The same families measured over the programme's own window — and most of the tail is gone

`[MEASURED IN BRIEF]`, long-short %/month, 2010-01 → 2024-12 (180 months), three constructions.
`hold12` = the alt-port set with a 12-month holding period; `price_gt5` and `me_gt_nyse20` are the
same predictors under a share-price > `$5` screen and a market-equity > NYSE-20th-percentile screen.

| signal | family | hold12 | *t* | price>`$5` | *t* | ME>NYSE20 | *t* |
|---|---|---|---|---|---|---|---|
| `XFIN` net external financing | `F-FINANCE` | **1.40** | 3.67 | **0.80** | 2.57 | **0.63** | 1.99 |
| `ShareIss1Y` | `F-FINANCE` (share count) | **1.06** | 3.18 | **0.48** | 2.37 | **0.53** | 2.46 |
| `NetEquityFinance` | `F-FINANCE` | **1.10** | 2.93 | **0.60** | 2.53 | **0.56** | 2.11 |
| `ShareIss5Y` | `F-FINANCE` (share count) | **0.98** | 3.32 | **0.53** | 3.55 | **0.50** | 2.77 |
| `OperProfRD` | `F-PROFIT` | **0.80** | 2.15 | **0.74** | 2.21 | **0.67** | 2.00 |
| `GP` gross profitability | `F-PROFIT` | **0.79** | 2.71 | **0.70** | **3.14** | **0.77** | **3.39** |
| `AssetGrowth` | investment | 0.52 | 2.07 | 0.41 | 2.22 | 0.52 | 2.45 |
| `CBOperProf` | `F-PROFIT` | 0.50 | 1.41 | 0.49 | 1.45 | 0.51 | 1.52 |
| `VolumeTrend` | price/volume only | **0.51** | 4.22 | **0.27** | 3.52 | **0.38** | 3.65 |
| `ChEQ` | `F-FINANCE` (share count) | 0.43 | 2.13 | 0.21 | 1.60 | 0.34 | 2.13 |
| `CompEquIss` | `F-FINANCE` (share count) | 0.29 | 2.17 | 0.31 | 2.09 | 0.30 | 1.73 |
| `BM` book-to-market | value | **−0.00** | **−0.01** | 0.18 | 0.72 | 0.05 | 0.18 |
| `Accruals` | accruals | **−0.09** | −0.67 | −0.09 | −0.67 | −0.02 | −0.12 |
| `Illiquidity` Amihud | price/volume only | **−0.09** | −0.71 | −0.19 | −1.57 | −0.04 | −0.27 |
| `Size` | share count | **−0.32** | −1.46 | −0.13 | −0.95 | −0.14 | −0.91 |
| `Price` nominal price | price/volume only | **−0.62** | −1.30 | −0.36 | −1.70 | −0.43 | −1.40 |

**Note on `CBOperProf`, because it is `#1` on the shortlist and its long-short *t* here is only
1.41.** Its long-short is weak precisely because its premium is **almost entirely in the long leg**
(§7): 44 bp long at *t* 2.48 against 5 bp short. A long-short *t* of 1.41 and a long-leg *t* of 2.48
are consistent, and for a long-only programme the second is the relevant one. **`GP` is the more
robust long-short member of the same family — *t* 3.14 and 3.39 under the two screens.**

**Read this table for the negatives first.** Over the programme's own window: **book-to-market is
exactly zero, accruals is negative, size is negative, Piotroski-style composites and the nominal
price sort are negative, and Amihud illiquidity is negative.** Five of `S3`'s eight cost-honest
low-turnover survivors do not survive 2010–2024. **The families that do are `F-PROFIT` and
`F-FINANCE` and essentially nothing else.** That is a narrower answer than the slate's framing and
it is the right one.

**And read the screen columns as the warning they are.** `ShareIss1Y` falls from **1.06 to 0.48** under
a `$5` price screen — **more than half of its premium is in sub-`$5` stocks**, i.e. in names this
programme's universe floor excludes by construction. `XFIN` falls from 1.40 to 0.80. **The
headline numbers in column one are not available to this programme and I am not presenting them as
if they were.** §9 ranks on the screened columns, shrunk.

---

## 4. Q2 — HOLDING PERIOD AND REBALANCE FREQUENCY, AND WHAT HAPPENS AS THE HOLD SHORTENS

### 4.1 What the evidence supports, per family

| family | documented rebalance | documented hold | source |
|---|---|---|---|
| `F-PROFIT` | **annual** (72 of 99 accounting predictors are 12-month in `S4`) | 14–80 months average under `S3`'s turnover of 1.2–7.2%/mo | `S4` `[MEASURED IN BRIEF]`; `S3` `[read in full]` |
| `F-FINANCE` (statement-based) | **annual** | as above | `S4`, `S3` |
| `F-FINANCE` (share-count) | **annual** for `ShareIss1Y/5Y`, **monthly** for `CompEquIss` | — | `S4` `[read in full]` of the rows |
| price/volume characteristics | **monthly** (31 of 45 `Price` predictors) | 1 month | `S4` `[MEASURED IN BRIEF]` |
| value (B/M) | annual breakpoints, monthly value-weight maintenance | — | `S6` `[read in full]` |

**One documented result says faster signal refresh HELPS a slow characteristic, and it is the only
such result I found.** `S6` (Asness–Frazzini, FAJ 2013, AQR authors, `[read in full]`) refreshes the
price in B/P **monthly instead of annually** and reports alphas *"between 305 and 378 basis points
annually of statistically significant alpha"* against a five-factor model that already contains the
standard annual measure. **Three caveats, all of which I checked in the text:** (i) their portfolios
are **all rebalanced monthly** regardless — what varies is how often the *breakpoints* refresh, *"once
a year in for the annual measures, every month for the monthly measure—not to the rebalancing
frequency for value weighting"*; (ii) the mechanism is a **current price in the denominator**, which
is the value–momentum interaction and so imports excluded ground; (iii) the paper notes the higher
turnover of the timely version. **So: monthly beats annual for value's signal refresh. Nothing in
this literature goes below monthly.**

### 4.2 THE HOLDING-PERIOD LADDER, MEASURED — and it is flat where it matters

`[MEASURED IN BRIEF]`. The *same* predictors, the *same* window (2010-01 → 2024-12), four holding
periods. Median long-short %/month by group:

| group | N | hold 1m | hold 3m | hold 6m | hold 12m | 12m/1m |
|---|---|---|---|---|---|---|
| EXCLUDED momentum | 11 | 0.721 | 0.647 | 0.596 | 0.188 | **0.26** |
| EXCLUDED short interest/borrow | 5 | 0.667 | 0.771 | 0.699 | 0.605 | 0.91 |
| EXCLUDED short-term reversal | 1 | 0.579 | 0.270 | −0.101 | −0.242 | **−0.42** |
| **OPEN share-count only** | 5 | **0.513** | **0.517** | **0.499** | **0.425** | **0.83** |
| EXCLUDED earnings dates | 2 | 0.386 | 0.239 | 0.214 | 0.001 | **0.00** |
| EXCLUDED options | 9 | 0.246 | 0.082 | −0.017 | −0.051 | **−0.21** |
| **OPEN price/volume only** | 26 | **0.202** | 0.245 | 0.205 | **0.097** | 0.48 |
| needs Analyst | 17 | 0.192 | 0.103 | 0.073 | 0.145 | 0.75 |
| **needs fundamentals** | 90 | **0.183** | **0.198** | **0.182** | **0.155** | **0.85** |
| EXCLUDED calendar | 11 | 0.167 | 0.122 | 0.189 | 0.163 | 0.98 |
| EXCLUDED lead-lag | 9 | 0.048 | −0.074 | −0.148 | −0.115 | **−2.39** |

*(Grouping note so the counts reconcile with §6: `Size` is counted here with the share-count family
because market capitalisation needs a share count, which is why this row reads 26 where §6's census
of price-and-volume-computable predictors reads 27.)*

**This table is the core of the lane and it says four things.**

1. **The slow families are flat in the hold.** Fundamentals lose **15%** of their monthly rate going
   from a one-month to a twelve-month hold; the share-count family loses **17%**. Dated-event and
   fast families collapse: momentum keeps **26%**, options **−21%**, earnings-dated signals **0%**,
   lead-lag **inverts**. **This is the quantitative version of `K6`'s `F2` and it is now measured on
   a single consistent construction rather than inferred across papers.**
2. **Therefore the monthly rebalance is NOT load-bearing for the slow families.** Holding twelve
   months instead of one costs ~15% of the rate and cuts the cost by ~12×. **For `F-PROFIT` and
   `F-FINANCE`, longer is strictly better at this programme's cost level.** That is the direction
   the evidence supports, and it is the opposite direction from the programme's horizon.
3. **And that flatness is exactly why shortening the hold is fatal.** A premium that is invariant to
   holding period between 1 and 12 months is a premium that accrues at a **constant rate per month
   of exposure**. Shorten the hold and you take a pro-rata slice of the numerator while paying the
   same round trip. The arithmetic, at the programme's own **33.8 bp/side → 67.6 bp round trip plus
   `2 × 50/P` commission, `P = $10`, so 77.6 bp**:

   | hold | amortised round trip | what `F-PROFIT`'s best long-only leg earns (§7) |
   |---|---|---|
   | 12 months (annual rebalance) | **6.5 bp/month** | 15 bp/month → **clears, ~2.3×** |
   | 6 months | **12.9 bp/month** | 15 bp/month → clears, 1.2× |
   | 3 months | **25.9 bp/month** | 15 bp/month → **fails** |
   | 1 month | **77.6 bp/month** | 15 bp/month → fails by 5× |
   | ~10 daily bars | **155.2 bp/month** | 15 bp/month → **fails by 10×** |
   | ~5 daily bars | **310.4 bp/month** | fails by 21× |
   | 1 daily bar | **1,630 bp/month** | fails by 109× |

   **The breakeven hold for the strongest measurable long-only characteristic is between three and
   six months.** Not "months rather than bars" as a stylistic preference — **3 to 6 months as an
   arithmetic floor.** The programme's stated horizon is "one to tens of daily bars"; the top of that
   range (~60 bars) is about 3 months, so **the very top of the programme's existing range is the
   very bottom of this family's viability**, and everything below it fails.

4. **No published ladder goes below one month.** `S2` constructs 1-, 6- and 12-month holding-period
   variants for every monthly-sorted anomaly in its 447 — *"For monthly sorted anomalies, we include
   three different holding periods (1-, 6-, and 12-month)... it is economically interesting to study
   how monthly sorted anomalies vary across different holding periods"* `[read in full]` — and the
   shortest rung is one month. The only sub-monthly remark I found in 130 pages is that
   *"Hou (2007) shows stronger effects at shorter horizons using weekly cross-sectional
   regressions"* — and that is the **industry lead-lag effect**, which is excluded ground. `S1` says
   *"Our analysis uses the standard monthly-rebalanced long-short portfolios"* and closes by
   **handing the question back**: *"We encourage practitioners and researchers to examine their own
   universe definitions, rebalancing frequencies, and cost assumptions"* `[read in full]`.
   **The monthly-or-slower horizon is load-bearing in the weakest and most awkward sense: it is the
   only horizon anyone has measured.**

### 4.3 Does the premium accrue uniformly in calendar time? One source says no, and the arithmetic says mostly yes

`S5` (Engelberg–McLean–Pontiff, `[read in full]` of the July-2017 draft; the published JF 2018
version may differ) is the one paper I found that decomposes a characteristic premium *within* the
hold. On 97 anomalies: **anomaly returns are 50% higher on corporate news days and 6.3× higher on
earnings-announcement days.** The worked figures, verbatim: for a composite signal value of 10,
expected returns are higher by **3.84 bp on non-announcement days and by an additional 21.64 bp on
announcement days, total 25.48 bp**, *"which is 6.3 times higher than anomaly returns on
non-earnings announcement days."* Decomposed by leg: **long-side anomaly returns are 872% higher and
short-side 753% lower** on announcement days. And, directly relevant to which family is which:
*"Fundamental anomalies are much stronger on earnings days, but weaker on news days... Market
anomalies are made only with market data, and no accounting data, so this may explain why they are
more affected by news than earnings announcements."*

**Now the arithmetic `S5` does not do, and it reverses the impression.** Earnings days are ~4 of
~252 trading days, i.e. **~1.6%**. So the announcement-day contribution is `0.016 × 25.48 ≈ 0.41
bp/day` against `0.984 × 3.84 ≈ 3.78 bp/day` from ordinary days. **Announcement days carry roughly
10% of the annual premium; about 90% still accrues on ordinary days.** The concentration is real and
it is large *per day*; it is **not** where the premium lives.

**Which closes the short-hold question from a second, independent direction.** If ~90% of a
characteristic premium accrues uniformly across ordinary days, then a short hold earns a pro-rata
slice — exactly what the flat holding-period ladder in §4.2 implies. **Two independent routes, same
answer.** And the 10% that *is* concentrated sits on **earnings-announcement days for the
fundamentals family — which is this programme's excluded ground, not merely unavailable** — and on
**news days for the price/volume family, which needs a news feed the programme does not have.**
There is no third door.

### 4.4 THE SAME QUESTION AT THE PROGRAMME'S OWN HORIZON — measured on DAILY returns, with a positive control

§4.2 and §4.3 both answer "what happens as the hold shortens" by inference. **`S4` also publishes
daily returns of these portfolios, so it can be measured directly, and I did.**

`[MEASURED IN BRIEF]`. Endpoint: the same Drive release → `DailyPortfolios/Predictor.zip`, Drive id
`1dpiDCCS1Uk-CiB6eU1Hc1pI22fTtcRKn`, **232,600,633 bytes, `file -b` = `Zip archive data`, 212 CSVs**,
each with `date, port01..portNN, portLS` in **percent per day**. For each signal I took the daily
long-short series over 2010-01-01 → 2024-12-31 (**3,774 trading days**) and bucketed every day by its
**ordinal trading day within the calendar month**.

**`[C6]` The reconciliation control.** `21 ×` the mean daily long-short must reproduce the monthly
long-short measured earlier from a *different* file:

| signal | daily bp/day | *t* | `21 ×` daily, %/mo | monthly file, %/mo | ratio |
|---|---|---|---|---|---|
| `ShareIss1Y` | 5.04 | 3.46 | 1.059 | 1.060 | **1.00** |
| `ShareIss5Y` | 4.68 | 3.57 | 0.983 | 0.977 | **1.01** |
| `XFIN` | 6.65 | 3.98 | 1.396 | 1.403 | **0.99** |
| `NetEquityFinance` | 5.27 | 3.15 | 1.107 | 1.102 | **1.00** |
| `CBOperProf` | 2.38 | 1.48 | 0.499 | 0.504 | **0.99** |
| `OperProfRD` | 3.71 | 2.18 | 0.779 | 0.795 | **0.98** |
| `GP` | 3.56 | 2.37 | 0.748 | 0.793 | 0.94 |
| `VolumeTrend` | 2.35 | **3.99** | 0.493 | 0.507 | **0.97** |
| `CompEquIss` | 1.50 | 2.13 | 0.314 | 0.309 | 1.02 |
| `Mom12m` *(EXCLUDED)* | 6.59 | 3.02 | 1.385 | 1.372 | **1.01** |

**Fifteen of sixteen reconcile within 0.90–1.07.** The one that does not is `BM`, whose monthly
return is **−0.003 %/month**, so the ratio is a division by approximately zero and carries no
information — recorded rather than hidden.

**Mean daily long-short, bp per day, by ordinal trading day of the month, 2010–2024:**

| signal | d1 | d2–3 | d4–5 | d6–10 | d11–15 | d16–21 | **first-5 / rest** |
|---|---|---|---|---|---|---|---|
| `ShareIss1Y` | **−11.51** | 4.37 | 6.41 | 8.37 | 4.20 | 5.53 | **−0.04** |
| `ShareIss5Y` | **−12.98** | 4.06 | 2.99 | 8.56 | 5.29 | 4.69 | **−0.32** |
| `XFIN` | **−16.68** | 6.13 | 8.21 | 11.02 | 4.11 | 9.39 | **−0.10** |
| `NetEquityFinance` | **−16.73** | 6.42 | 4.75 | 9.28 | 4.54 | 5.94 | **−0.28** |
| `CBOperProf` | −2.91 | 2.82 | 1.25 | 5.59 | 3.92 | −0.46 | 0.13 |
| `OperProfRD` | 2.29 | 6.08 | 3.72 | 6.84 | 4.33 | 0.16 | **1.07** |
| `GP` | −1.39 | 7.92 | 3.10 | 5.85 | 4.67 | 0.53 | 0.87 |
| `VolumeTrend` | −3.57 | 1.68 | −0.15 | 4.53 | 2.41 | 2.34 | −0.22 |
| `CompEquIss` | −3.85 | 0.50 | 0.73 | 2.37 | 2.65 | 1.39 | −0.41 |
| **POSITIVE CONTROL** `STreversal` *(EXCLUDED)* | **+27.97** | 1.02 | 8.26 | 2.31 | −3.69 | 4.76 | **11.01** |
| **POSITIVE CONTROL** `Mom12m` *(EXCLUDED)* | −9.88 | −5.05 | −4.91 | **7.17** | **12.50** | **10.13** | −0.67 |

**`[C7]` The positive control is the reason this table is worth anything.** A method that reports
"uniform" for everything has no resolution. **It does not:** short-term reversal is detected as
**massively front-loaded — +27.97 bp on day 1 and a first-5/rest ratio of 11.0** — and 12-month
momentum is detected as **back-loaded**, rising monotonically from −9.9 on day 1 to +12.5 by
mid-month. **Both are exactly the shapes those two effects are known to have.** So when the same
method reports near-uniform accrual for profitability and issuance, that is a measurement.

**Three conclusions, and the first is the one the slate asked for.**

1. **For every surviving slow family, the premium accrues roughly evenly across days 2–21 and
   nothing is front-loaded.** `ShareIss1Y` runs 4.4 / 6.4 / 8.4 / 4.2 / 5.5 bp/day through the month;
   `OperProfRD` 6.1 / 3.7 / 6.8 / 4.3 and then tails to 0.2 in the last week. **There is no
   concentration in the first bars for a short hold to harvest.** A ten-bar hold earns about ten
   days' worth and nothing more.
2. **The only thing that IS concentrated in the first bars is a LOSS, and it is largest for the best
   candidate.** Day 1 of the month is **−11.5 bp for `ShareIss1Y`, −13.0 for `ShareIss5Y`, −16.7 for
   `XFIN` and `NetEquityFinance`**, against a ~5 bp/day average. **A short hold entered at a
   month-end formation would eat the one clearly non-uniform piece of the month and it is negative.**
   I will not claim to know the mechanism — it is a turn-of-the-month pattern, which is **calendar
   effects, excluded ground**, and it may equally be a measurement artefact at the rebalance boundary
   where the day-1 return and the rebalance trade coincide. **Either way it is a reason against a
   short hold, not a lead.**
3. **The money arithmetic, now at daily resolution.** `CBOperProf`'s long leg, `$5`-screened and
   shrunk, is **15 bp/month ⇒ 0.71 bp/day**. A ten-bar hold earns **~7 bp gross** against a
   **77.6 bp round trip**: short by **11×**. `ShareIss1Y`'s long leg at 6 bp/month ⇒ 0.29 bp/day
   earns **~3 bp over ten bars**: short by **27×**. **This is the same factor of ten as §4.2's
   amortised-cost table, reached from daily data instead of monthly, and it is the answer to the
   slate's central sub-question.**

**What the daily data cannot tell me, and it matters here.** These are **close-to-close daily
returns**. The programme's stated edge is **overnight**, and **no public file in this release splits
the overnight from the intraday component of a characteristic portfolio.** I can say the premium is
uniform across *days*; **I cannot say anything about where inside a day it sits**, and nobody should
read §4.4 as evidence either way on the overnight question.

---

## 5. Q3 — CAPACITY AND BREADTH

### 5.1 Name counts: measured, and not the binding constraint

`[MEASURED IN BRIEF]` from the `Nlong`/`Nshort` columns, median over 2010+, baseline construction:

| group | N signals | median names, high leg | low leg |
|---|---|---|---|
| needs fundamentals | 90 | **427** | 442 |
| OPEN price/volume only | 26 | **780** | 786 |
| OPEN share-count only | 5 | **763** | 762 |
| EXCLUDED momentum | 11 | 397 | 397 |
| AMBIG long-term reversal | 6 | 500 | 500 |

Per-signal, with the sort's own universe size:

| signal | bins | universe | names per bin |
|---|---|---|---|
| `ShareIss1Y` | 5 (quintiles) | ~5,662 | ~806 each |
| `ShareIss5Y` | 5 | ~4,184 | ~598 each |
| `GP` | 5 | ~5,264 | ~760 each |
| `CBOperProf` | 10 (deciles) | ~4,034 | 939 / 262 / 194 / … / 290 |
| `VolumeTrend` | 5 | ~9,102 | ~1,300 each |
| `Illiquidity` | 5 | ~2,962 | ~423 each |

**`S1`'s own operational floor is 20 names per leg in ≥95% of months**, below which it sets the
return to zero, *"effectively assuming that the investor declines to trade due to insufficient
diversification"* `[read in full]`. **Every family clears that floor by one to two orders of
magnitude, and so would this programme**: a quintile of 1,573 names is ~315 per leg, a decile ~157.

**So on NAME COUNT every family here is breadth-feasible, and the slate's worry about "a hundred
independent bets" does not bite on leg size.** What does bite is that the published constructions
draw 400–1,300 names per leg from universes of **3,000–9,000**, which is **two to six times** the
programme's 1,573. A quintile of 1,573 is a *coarser* instrument than a quintile of 5,662: the same
per-name edge produces a less extreme characteristic spread between the extreme bins. **I cannot
quantify that degradation from public portfolio returns and I am not going to guess it.**

### 5.2 Effective breadth: the literature does not speak to it, and that is the finding

**No source I read reports anything resembling effective independent breadth for an anomaly
portfolio.** `S4` reports that pairwise correlations among 205 predictors and among their long-short
returns are close to zero (relayed through `K6`, which read it in full) — that is breadth *across
signals*, not *within* one. `S1`'s rule is a **name count**. `S2`'s and `S3`'s constructions are
decile and quintile sorts with no breadth diagnostic at all. **The programme's figure of ~10
effective independent instruments across 1,573 names has no counterpart anywhere in this
literature, so it can be neither confirmed nor contradicted by it.** `K6` reached the same
conclusion and I confirm it independently.

**The only relevant theory I could reach is `S8` (Clarke–de Silva–Thorley, FAJ 2002), and I have it
only `[snippet only — via a search summariser]`**, so I use it qualitatively and for one point only:
the **transfer coefficient** is a multiplicative scaling on the information ratio that absorbs
constraints, *"reduction in independent bets due to constraints"*, with practical values quoted as
**0.3 to 0.8**, and *"the greatest improvement in efficiency comes from the elimination of the
long-only constraint."* **I did not open the paper; that 0.3–0.8 range is the weakest-established
number in this brief and nothing in §9 depends on it.** Its only use here is to name the right
concept: if ~10 effective instruments is the programme's reality, the consequence is a scaling on
the *t*-statistic of whatever spread it measures, not a disqualification of the family.

### 5.3 Capacity is the one axis that favours this account

`S3`'s cost measure is explicitly *"the costs faced by a **small liquidity demander**… it assumes
market orders"* and is described by its authors as conservative for that reason `[read in full]`.
`S3`'s and `S2`'s cost models **omit price impact entirely.** So the cost-honest papers charge
roughly a small trader's cost and still reach the verdicts in §3.2. **The implication is the same
asymmetry `K6` found: a retail account suffers no capacity penalty, but it also cannot use "too
small to matter" as a defence — the published verdicts already apply at its scale.** Capacity does
not rescue a 15 bp/month long-only edge.

---

## 6. Q4 — THE PRICE-AND-VOLUME-ONLY SUBSET: EXCLUDED VERSUS UNAVAILABLE, STATED EXPLICITLY

The slate asked for this distinction and it is the section where it matters most. Of the **58 of 212
predictors** that need only `Price` or `Trading` data (§2.2), here is the disposition, with the
exclusion-list clause named in each case:

| disposition | count | members |
|---|---|---|
| **EXCLUDED — momentum** | 11 | `Mom12m`, `Mom6m`, `Mom6mJunk`, `MomVol`, `MomRev`, `IntMom`, `IndMom`, `High52`, `FirmAgeMom`, `ResidualMomentum`, `TrendFactor` |
| **EXCLUDED — calendar effects** | 10 | `MomSeason`, `MomSeason06/11/16YrPlus`, `MomSeasonShort`, `MomOffSeason`, `MomOffSeason06/11/16YrPlus`, `Mom12mOffSeason` |
| **EXCLUDED — lead-lag of every kind** | 5 | `PriceDelayRsq`, `PriceDelaySlope`, `PriceDelayTstat`, `IndRetBig`, `retConglomerate` |
| **EXCLUDED — short-term reversal** | 1 | `STreversal` |
| **EXCLUDED — short interest and borrow** | 1 | `ShortInterest` |
| **EXCLUDED — earnings dates / announcement premium** | 1 | `AnnouncementReturn` |
| **AMBIGUOUS — long-term reversal** | 2 | `LRreversal`, `MRreversal` (De Bondt–Thaler). **The exclusion list names short-term, industry-relative and residual reversal and return clustering; it does NOT name the 36–60-month version. I am flagging this as a boundary question for the principal rather than deciding it** — and §6.2 shows it is moot on the numbers |
| **OPEN** | **27** | below |

**So: 29 of 58 are EXCLUDED, not unavailable.** The price-and-volume corner of the published
cross-section is half spent ground. **That is a different statement from "closed", and the
difference is the principal's to use.**

### 6.1 The 27 OPEN members, and what each needs beyond daily OHLCV

| needs **nothing but daily OHLCV** (21) | needs one extra input (6) |
|---|---|
| `IdioVol3F`, `IdioVolAHT`, `RealizedVol`, `MaxRet` *(volatility)* | `std_turn`, `ShareVol`, `VolMkt` — **shares outstanding** (turnover) |
| `Beta`, `BetaTailRisk`, `CoskewACX`, `Coskewness`, `ReturnSkew`, `ReturnSkew3F`, `BetaFP` *(risk / beta / skew)* | `Size` — **shares outstanding** |
| `BidAskSpread`, `Illiquidity`, `VolSD`, `zerotrade1M/6M/12M` *(liquidity from OHLCV)* | `betaVIX` — **the VIX series** (free) |
| `DolVol`, `VolumeTrend` *(volume)* | `BetaLiquidityPS` — the **Pástor–Stambaugh market liquidity factor** |
| `Price` *(nominal price level)* | `ProbInformedTrading` — **intraday trade-by-trade data** |

**So the answer to Q4's literal question is YES: 21 published characteristics are computable from
daily price and volume alone, and 27 are within one cheap input.** `K6`'s "two of the three
price-only survivors are excluded" was a statement about a top-ten cut, and as a census it
understates the pool by an order of magnitude.

### 6.2 And the answer that matters is that the pool is the worst-evidenced corner of the cross-section

**Three independent lines of evidence, and they agree.**

**(i) `S2`'s replication verdict, which I verified in the text myself.** *"The biggest casualty of
p-hacking is the trading frictions (liquidity) category, with 95 out of 102 variables (93%)
insignificant"* — and the named casualties are precisely this pool: *"15 out of 16 volatility
measures earn insignificant average returns"*; idiosyncratic volatility from the FF3 model earns
−0.51%, −0.33%, −0.18%/month (*t* = −1.62, −1.11, −0.62) at 1/6/12 months; total volatility −0.40 /
−0.25 / −0.20 (*t* −1.16, −0.77, −0.62); *"Three market beta measures based on rolling window
regressions, the Frazzini-Pedersen (2014) method, and the Dimson (1979) method are all
insignificant"* with the **Frazzini–Pedersen beta deciles earning around −0.2%/month at all three
horizons, within one standard error of zero**; Amihud illiquidity only 0.28% and 0.37% (*t* 1.31,
1.73) at 1 and 6 months; share turnover −0.10% to −0.15%, *"all of which are within 0.6 standard
errors from zero"*; and *"none of the three Lm measures interacted with three holding periods (nine
measures in total) produce any significance."* `[read in full]` **`S2` kills this pool by name,
variable by variable, at every one of its three holding periods.**

**(ii) My own measurement over the programme's window agrees.** All 27 OPEN members have a
measurable 2010–2024 series. At a 12-month hold in the full universe the group median is
**9.6 bp/month** — the lowest of any non-excluded group — and **under a `$5` price screen it falls to
8.3 bp/month.** **Ten of the 27 are outright negative** over 2010–2024: `BetaFP`, `BetaLiquidityPS`,
`BidAskSpread`, `Illiquidity`, `MaxRet`, `Price`, `RealizedVol`, `Size`, `VolSD`, `betaVIX` —
including `Illiquidity` (−8.9 bp), `Size` (−31.7 bp), `BidAskSpread` (−25.6 bp) and `Price`
(−61.6 bp). **Exactly two of the 27 reach *t* > 2**: `VolumeTrend` (*t* 4.22), discussed below, and
`Coskewness` (*t* 2.02 at hold12 — but only **0.212 %/month, *t* 1.48** under the `$5` screen, so it
does not survive the programme's own floor and I am not proposing it).
**The nominal-price sort is the single worst-performing computable characteristic
in the census, which is worth noting because it is also the sort `K6`'s `F4`/`K5` independently
identified as carrying the largest equal-weight rebalancing bias (0.61%/month for a share-price
sort) — two unrelated reasons to leave it alone.**

**(iii) The one apparent exception, and why I am still ranking it third.** `VolumeTrend`
(Haugen–Baker 1996: *"rolling coefficient from regressing monthly trading volume on a linear time
trend over a window of 60 months (require that at least 30 exist), scaled by 60-month average of
trading volume"* — `S4` `Detailed Definition`, read in full) is **annual rebalance, quintiles,
equal-weighted, computable from volume alone**, and over 2010–2024 it measures **0.51%/month,
*t* = 4.22** at a 12-month hold, **0.27%/month, *t* = 3.52** under a `$5` screen, **0.38%/month,
*t* = 3.65** under the microcap screen. **It is the only price-and-volume-only characteristic in the
whole census that survives my own window, both screens, and every holding period.** Against it:
(a) `S1`'s post-2005 category cell for Trading/Liquidity has a median of only **0.11%/month** across
N = 13, and `VolumeTrend` is not in `S1`'s post-2005 top ten, whose cut-off is 0.38%/month — **so in
`S1`'s investable universe it is below 38 bp/month, and I cannot measure where.** *(That inference
assumes `VolumeTrend` is among `S1`'s 170 retained signals rather than dropped by their
fewer-than-20-names-per-leg screen. It is a quintile sort of ~9,100 names so it cannot plausibly have
been dropped for sparsity, but I did not verify it against a list of their 170 and the assumption is
stated rather than buried.)* The same inference applies to `ShareIss1Y`/`ShareIss5Y`: both measure
above 0.47%/month under a `$5` screen in the full universe yet neither is in `S1`'s top ten, **so
both are below 38 bp/month in `S1`'s investable universe too**; (b) after `S1`'s
own luck shrinkage applied to my own cross-section it is worth **12 bp/month long-short under the
`$5` screen and only 2 bp/month on the long leg alone** (§7), which does not pay a round trip at any
hold; (c) it needs **60 months of volume history**, so on a 16.6-year fixture it costs five years of
burn-in; (d) it is selected from 209 signals by me, which is the selection problem `[C5]` warns
about.

**So, stated the way the slate asked.** The price-and-volume-only family is **not closed — it is
open, large (27 members), half of it is EXCLUDED rather than unavailable, and the open half is the
one corner of this literature that two replication efforts and my own measurement all find
empty.** Its single best member does not clear one round trip on its long leg.

---

## 7. THE LONG LEG — WHERE I DISAGREE WITH AN INHERITED NUMBER, AND SHOW MY WORK

This programme carries from round 6 that *"long-minus-market Var(t) = 0.98, below the null's 1.00,
so every survivor's long-only return shrinks to 0.00%/month."* I verified that `S1` says exactly
that, in its Table 2 note `[read in full]`: *"For Long – Mkt returns, Var(t) = 0.98 is below 1, so
the factor is zero, and every adjusted mean is zero."*

**Two observations, the second of which changes the conclusion.**

**First, the zero is a property of a shrinkage estimator at its boundary, not a measurement about
any anomaly.** `S1`'s own *raw* long-minus-market column for its #1 survivor, cash-based operating
profitability, is **+0.40 %/month**. The zero arises because a cross-sectional variance of 0.98
cannot be distinguished from 1.00 and the implied signal share is truncated at zero. **A signal
share cannot be negative, so a sample `Var(t)` below 1 is as much a finite-sample artefact as a
statement about signal.** `S1` is entitled to that prior; it is not a measurement that the long leg
is zero.

**Second, and this is the substantive point: the benchmark is wrong for an equal-weighted book.**
`S1` subtracts the **raw value-weighted Fama–French market return** from each long leg. An
equal-ish-weighted long leg minus a value-weighted market carries a large, highly volatile common
size/weighting component in **every** series, which inflates each series' volatility, shrinks every
*t*-statistic toward zero, and drives the cross-sectional variance of those *t*'s toward the
null. **The benchmark an equal-weighted long-only programme actually competes with is an
equal-weighted hold of the same universe.**

So I recomputed the identical diagnostic with that benchmark. `[MEASURED IN BRIEF]`: for all 209
predictors, 2010-01 → 2024-12, long leg minus the **name-weighted average of every bin in that same
sort**:

| construction | `Var(t)` long−universe | signal share | `Var(t)` universe−short | `Var(t)` long-short |
|---|---|---|---|---|
| `hold1` | **1.804** | 0.446 | 1.954 | 2.046 |
| `hold12` | **1.808** | 0.447 | 1.723 | 1.746 |
| `price_gt5` | **1.503** | 0.335 | 1.845 | 1.869 |
| `me_gt_nyse20` | **1.347** | 0.258 | 1.377 | 1.546 |
| *`S1`, long − VW market, post-2005, Standard universe* | *0.98* | *0.00* | — | *1.09* |

**`Var(t)` is 1.35–1.81, not 0.98, and the implied long-only signal share is 0.26–0.45, not zero.**

The shrunk long-leg and short-leg figures, bp/month, 2010–2024, under the two screens that matter
to this programme:

| signal | price > `$5`: long *t* | **long, shrunk** | short, shrunk | ME > NYSE20: long *t* | **long, shrunk** | short, shrunk |
|---|---|---|---|---|---|---|
| `CBOperProf` | **2.48** | **15** | 2 | **2.53** | **11** | 2 |
| `OperProfRD` | **2.50** | **15** | 13 | 2.48 | **11** | 7 |
| `GP` | **2.22** | 9 | 20 | **2.51** | 8 | 12 |
| `ShareIss5Y` | **3.08** | 7 | 15 | **2.86** | 6 | 7 |
| `ShareIss1Y` | **2.14** | 6 | 14 | **2.34** | 5 | 9 |
| `OPLeverage` | 2.13 | 6 | 2 | 2.46 | 6 | 5 |
| `XFIN` | 2.15 | 6 | **29** | 1.68 | 4 | **14** |
| `VolumeTrend` | 1.65 | 2 | 9 | **3.50** | 4 | 6 |
| `AssetGrowth` | −0.05 | 0 | **19** | 0.64 | 3 | **12** |
| `BM` | 0.73 | 4 | 3 | 0.50 | 3 | 0 |
| `Accruals` | −1.33 | 0 | 2 | −0.61 | 0 | 1 |
| `Illiquidity` | −1.28 | 0 | 0 | −0.48 | 0 | 0 |
| *`Mom12m` (EXCLUDED, for scale)* | *0.83* | *6* | *24* | *0.90* | *5* | *14* |

**What this says, carefully.**

- **`F-PROFIT` is a LONG-SIDE family.** `CBOperProf`'s long leg carries **91%** of its long-short
  premium under the `$5` screen (44 bp long vs 5 bp short) and **86%** under the microcap screen.
  `OperProfRD` is similar. **This is the only family in the census whose return is on the side this
  programme can trade**, and it agrees to within 4 bp with `S1`'s own raw long-minus-market figure of
  40 bp for the same signal — an unplanned cross-validation between two different benchmarks.
- **`F-FINANCE` is a SHORT-SIDE family.** `ShareIss1Y` 35% long / 65% short; `XFIN` 22/78;
  `NetEquityFinance` 20/80; `ChEQ` −13/113; `AssetGrowth` ~0/100. **The best long-short numbers in
  §3.2 are mostly unavailable to a long-only account.** This is the inherited `F3` finding holding
  for one family and failing for the other, which is more useful than either blanket version.
- **`F-PROFIT`'s long leg is the only thing in this brief that clears its own cost.** 15 bp/month
  shrunk, under the programme's own `$5` floor, at an annual rebalance costing 6.5 bp/month ⇒
  **~8 bp/month net, about 1%/yr over the universe, gross of everything except the round trip.**
  **It needs the income statement and the balance sheet.**
- **`VolumeTrend`'s long leg is 2–4 bp/month shrunk and does not clear 6.5.** The free family does
  not pay for itself even at an annual rebalance.

**I am flagging this as a CONFLICT with an inherited premise, not a refutation** (§10.1). My
benchmark is not a tradeable instrument, I apply no costs to the long-leg figures, and I am
comparing against `S1`'s Standard universe with a different screen. **But the direction is clear
enough to matter: "the long-only return is zero" is not established, and the statistic that
established it is benchmark-dependent in a way that works against an equal-weighted book.** This is
also direct input to lane `A3`.

---

## 8. Q5 — THE UNCOMFORTABLE QUESTION, ANSWERED

**Yes. It is a different activity.** Not in one way — in five, and the honest thing is to say which
parts of the apparatus survive and which do not.

| layer | what the programme has | what this family needs | survives? |
|---|---|---|---|
| **Data** | daily OHLCV, a corporate-actions feed, EDGAR pulled directly | `F-PROFIT`: annual income statement + balance sheet, point-in-time, dead-inclusive. `F-FINANCE` (cheap members): a split-adjusted **share count** per name per month | **NO for `F-PROFIT`** — this is lane `A1`'s question, not a machinery question. **Nearly yes for the share-count members** |
| **Bar / clock** | daily bars, 4,187 of them | monthly formation, annual rebalance; the entire published record is monthly-or-slower and the census has **no sub-monthly rung** | **The daily panel is a superset** — a monthly book is a 21-bar resample of it. This layer survives, which is the cheapest good news in the brief |
| **Strategy object** | a **dated event** with an entry bar, a hold in bars, and an exit rule | a **characteristic carried continuously**, with membership changing only at rebalance and no event date at all | **NO.** There is no entry signal to lag, no event to align, no holding run to audit. `K6`'s `F2`, restated as a code problem |
| **Selection** | `sel = rank < N_SLOTS`, a slot-limited refill pool; the path-variant book | a **quantile sort of the whole eligible universe**: 315 names per leg at a quintile of 1,573, no slot cap, no refill | **NO.** The slot machinery is not a bottleneck to raise — it is the wrong object. `FINDINGS.md` §10's opportunity-cost framing does not apply to a sort that holds a fifth of the universe |
| **Weighting** | **equal-weighted**, and `K5` measured the rebalancing bias this carries | the literature is split: `S4`'s predictors are **184 EW / 28 VW**; `S3`'s cost-honest panel is **VW NYSE deciles**; `S3` says EW strategies' round-trip costs are *"generally two to three times as high"* as VW `[read in full]` | **Survives, at a cost.** EW is the literature's majority convention but the *cost-honest* results are VW, and `K5`'s finding that the EW bias is paid **per rebalance, not per bar** is strongly in an annual rebalance's favour: ~1 reset/year instead of ~50 |
| **Nulls** | bar-level path permutation; time rotation over `Td−1` offsets; per-name rotation | a characteristic sort has no event times to permute. The natural null is a **random quantile of the same size**, or a rotation of the *characteristic* across names at a fixed date | **NO.** And the programme's own rule bites here: *"a random subset is never a control for a persistent selector — it re-draws each bar, so it churns."* A null for an annually-rebalanced sort must itself be annually persistent. **This is the single largest piece of new machinery** |
| **Reporting** | per-trade statistics: count, mean, median, win rate, payoff, holding run, skew, trimmed means | there are **no trades** in the usual sense — there are monthly leg returns, a turnover rate, and a spread. `CLAUDE.md`'s four mandatory groups are written for a trade book | **PARTLY.** Group 1 (net/gross, exposure, breakeven) transfers directly. Group 2 (trade distribution) has no object to describe. Group 3 (winner concentration) becomes name-share of the spread. Group 4 (nulls) needs rebuilding with group 2 |
| **Horizon** | 1 to tens of daily bars; **the edge is overnight** | **3–6 months minimum** by §4.2's arithmetic, 12 months by the evidence's own preference | **NO — and this is the irreducible one.** An overnight edge and a six-month hold are not the same phenomenon measured differently |

**So the plain answer.** The daily bar survives, equal weighting survives at a cost, and **everything
between the bar and the report has to be rebuilt**: the strategy object, the selection layer, the
null, and two of the four reporting groups. **Plus the data, which is `A1`'s lane and is the gate.**

**And the honest framing of whether that is worth it.** The prize, measured as carefully as I can
measure it, is **~8 bp/month net on a long-only profitability sort under the programme's own `$5`
floor, ≈1%/yr over an equal-weighted hold of the same universe, before any further cost, gross of
the short leg the programme cannot run, using data the programme does not have, and shrunk for luck
using the same estimator that the literature applies to itself.** That is not nothing — it is a
positive, screened, cost-cleared, post-2010 number, which is more than eleven prior territories
produced. **It is also small enough that the rebuild is a data-acquisition decision first and a
machinery decision second**, and anyone who builds the machinery before `A1` answers will have built
it for a signal they cannot compute.

---

## 9. THE RANKED SHORTLIST — the bar

Ranked on **long-only, screened, shrunk, net of the programme's own amortised round trip**, because
that is the quantity this programme can actually earn. Shrinkage is `S1`'s own estimator applied to
my own 209-signal cross-section in that same construction. `$5` column = the `price_gt_5`
construction, which is the closest public analogue of this programme's universe floor.

### `#1` `F-PROFIT` — PROFITABILITY, annually rebalanced, long leg

| | |
|---|---|
| **Members** | cash-based operating profitability; operating profitability (R&D-adjusted); gross profits / assets. Novy-Marx (2013), Ball et al. (2016) |
| **Data requirement** | annual (or quarterly) **income statement + balance sheet**: `revt/sale, cogs, xsga, xrd, at`, plus `rect, invt, drc, drlt, ap, xacc` for the cash-based version. **Point-in-time and dead-inclusive, or it is a look-ahead.** NOT free today — this is lane `A1`'s gate |
| **Holding period** | **annual rebalance.** One-sided monthly turnover **1.96%** for gross profitability (`S3`, read in full), average holding 14–80 months across that panel. Flat in the hold: fundamentals lose only 15% of their monthly rate from a 1-month to a 12-month hold (`[MEASURED IN BRIEF]`) |
| **Breadth** | quintiles or deciles of a ~4,000–5,300-name universe ⇒ **760 names (quintile) or 194–939 (decile)** per bin, measured. A quintile of 1,573 is ~315/leg, far above `S1`'s ≥20 floor |
| **Cost-honest post-2005 evidence** | `S1`: the **only** category with a healthy post-2005 median — mean 0.25, **median 0.24 %/month, 78% positive, N=9** in the top-90%-of-cap universe `[read in full]`. `S3`: gross 0.40 → **net 0.37 %/month, net *t* 2.74** (1963–2012, VW NYSE deciles, Hasbrouck spreads) `[read in full]`. My own measurement, 2010–2024: `GP` **0.79%/mo *t* 2.71** (hold12), **0.70 *t* 3.14** under `$5`, **0.77 *t* 3.39** under the microcap screen; `OperProfRD` **0.80 / 0.74 / 0.67**, all *t* ≥ 2.00 |
| **The long leg specifically** | `CBOperProf` long-minus-universe **+44 bp/month, *t* 2.48** under the `$5` screen, **91% of the premium**; `OperProfRD` **+45 bp, *t* 2.50**. **Shrunk: 15 bp/month.** Net of 6.5 bp/month amortised round trip ⇒ **~8 bp/month, ≈1%/yr** |
| **Short leg needed?** | **NO.** This is the one family whose return is predominantly long-side |
| **Against it** | the data is the gate; the shrunk edge is 15 bp/month gross; `S2` replicates profitability better than most categories but the whole construction is one research group's; and **it is a 3–6-month minimum hold, which is outside the programme's stated horizon** |

### `#2` `F-FINANCE` — SHARE ISSUANCE, annually rebalanced — ranked second **on data cost, not on tradeability**

| | |
|---|---|
| **Members** | `ShareIss1Y` (growth in split-adjusted shares, t−18 → t−6), `ShareIss5Y` (5-year version), `CompEquIss` (Daniel–Titman composite issuance). And, needing the cash-flow statement, `XFIN` and `NetEquityFinance` — `S1`'s #5 and #9 survivors |
| **Data requirement** | **`ShareIss1Y`/`ShareIss5Y` need ONE number the programme does not have: a split-adjusted shares-outstanding series.** Nothing else — no income statement, no balance sheet. `CompEquIss` needs that plus total return. **This is the cheapest non-price input in the entire survivor set and it is the reason this entry is on the list** |
| **Holding period** | **annual rebalance**, quintiles, equal-weighted (`CompEquIss` is monthly). Flat in the hold: share-count group loses 17% from 1-month to 12-month |
| **Breadth** | quintiles of ~4,200–5,700 names ⇒ **598–806 per bin**, measured |
| **Cost-honest post-2005 evidence** | `S1`: net external financing **0.48** and net equity financing **0.39 %/month** post-2005 in the investable universe, ranks 5 and 9 `[read in full]`. `S3`: Net Issuance (M) gross 0.57 → **net 0.37, *t* 2.43** at 14.4% turnover `[read in full]`. My own, 2010–2024: `ShareIss5Y` **0.98%/mo *t* 3.32**, **0.53 *t* 3.55** under `$5`, **0.50 *t* 2.77** under the microcap screen; `ShareIss1Y` **1.06 → 0.48 → 0.53** |
| **Short leg needed?** | **YES, and this is why it is ranked second.** `ShareIss1Y` is **35% long / 65% short**; `XFIN` 22/78; `ChEQ` −13/113. The long leg shrinks to **6–7 bp/month**, which does **not** clear 6.5 bp/month with anything to spare |
| **Against it** | **more than half the raw premium is in sub-`$5` names** (1.06 → 0.48 under the price screen); the return is in the short leg, which is excluded ground; and the long-only residual is indistinguishable from the cost |

### `#3` `VolumeTrend` — reported so the principal can see it, and argued against

| | |
|---|---|
| **Data requirement** | **daily volume alone.** A 60-month rolling regression of monthly volume on a time trend, scaled by 60-month mean volume (Haugen–Baker 1996). Needs **60 months of burn-in** |
| **Holding period** | **annual rebalance, quintiles, EW.** Unusually, it *improves* with a longer hold: 0.443 (1m) → 0.507 (12m) |
| **Breadth** | quintiles of ~9,100 names ⇒ **~1,300 per bin** — the broadest sort in the census |
| **Evidence** | my own, 2010–2024: **0.51%/mo *t* 4.22** at hold12; **0.27 *t* 3.52** under `$5`; **0.38 *t* 3.65** under the microcap screen. **The only price/volume-only characteristic that survives my window, both screens and all four holds** — the only other one of the 27 to reach *t* > 2 anywhere, `Coskewness`, falls to *t* 1.48 under the `$5` screen |
| **Why it is still third** | **the long leg shrinks to 2 bp/month under the `$5` screen (4 bp under the microcap screen) against a 6.5 bp/month cost floor — it does not pay for itself.** It sits inside `S2`'s *"95 out of 102 (93%) insignificant"* trading-frictions category and inside `S1`'s Trading/Liquidity cell whose post-2005 median is **0.11%/month** across N=13. It is not in `S1`'s post-2005 top ten, so in their investable universe it is below 38 bp/month and I cannot say where. **And I selected it from 209 signals, which is the problem `[C5]` names** |

### Everything else, and why it is not on the list

**Value (B/M)** — `S1` post-2005 median **−0.04 %/month, 47% positive**; my measurement **−0.003
%/month** over 2010–2024. **Dead in the window, not merely thin.** **Accruals** — my measurement
**−0.09 %/month**. **Size** — **−0.32 %/month**. **Piotroski F** — `S3` net *t* **0.45** even in
1963–2012. **Amihud illiquidity / turnover / zero-trading-days** — `S2` kills all of them by name at
all three horizons; my measurement has `Illiquidity` at **−0.09 %/month**. **Idiosyncratic and total
volatility, MAX, beta, BAB, coskewness, tail risk** — `S2`'s 15-of-16 volatility failures and the
Frazzini–Pedersen beta deciles *"within one standard error from zero"*; my `BetaFP` measurement is
**−0.24 %/month** over 2010–2024. **Nominal share price** — worst computable characteristic in the
census at **−0.62 %/month**, and independently carrying the largest equal-weight rebalancing bias.
**Momentum, seasonality, lead-lag, short-term reversal, short interest, announcement returns,
options** — **EXCLUDED, not unavailable**, and named in §6 with the clause each falls under.

---

## 10. Q6 — THE WEEKS-LONG MIDDLE GROUND

**Briefly, because the evidence does not support one.** I looked for it three ways and found nothing
on the first two and a boundary on the third.

1. **In the census.** The distinct documented rebalance periods across all 331 Chen–Zimmermann
   signals are `{1, 3, 6, 12, 36}` months. **There is no weeks-long rung.**
2. **In the replication literature.** `S2`'s ladder is 1/6/12 months across 447 anomalies. The only
   sub-monthly reference in 130 pages is to Hou (2007)'s **weekly** cross-sectional regressions —
   the **industry lead-lag effect**, which is excluded ground. A targeted search for weekly- or
   sub-monthly-rebalanced value or profitability returned **nothing academic**; the hits were
   `[SALES INSTRUMENT]` pages and papers at monthly or annual frequency.
3. **In what the data support, which is the one place I did not have to interpolate.** §4.4 measures
   the accrual **day by day** over 3,774 days: **evenly across days 2–21 for every slow family, with
   a negative day 1.** So a weeks-long hold earns a weeks-long slice of the same rate and pays a full
   round trip. At a 3-week hold (~0.7 months) the amortised round trip is **~111 bp/month** against a
   15 bp/month long-only rate. **The middle ground is not an unexplored opportunity; it is the part
   of the curve where the measurement and the arithmetic agree and have already decided.** The method
   would have detected a weeks-long concentration had there been one — it found an 11× one in
   short-term reversal, which is excluded ground.

**The one genuinely weeks-long characteristic phenomenon I found is `S5`'s information-day
concentration**, and both of its doors are shut: the fundamentals family's concentration is on
**earnings-announcement days (excluded ground)** and the price/volume family's is on **news days
(no data)**. §4.3.

**A partial exception worth naming, since it is the only thing in the region with a positive
number.** `S3` examines **staggered partial rebalancing** at a **quarterly and half-quarterly**
frequency for mid-turnover strategies `[read in full]`, and `S3`'s **buy/hold spread** (trading
hysteresis) is its most effective cost mitigation. **But `K6` read `S2`'s tabulation of exactly that
and found it rescues high-turnover strategies only in combination with value weighting, does nothing
for low-turnover strategies, and never turns equal-weighted Q4 positive.** That is cost-cutting, not
edge-sharpening, and `CLAUDE.md` already names the distinction.

---

## 11. SIZE IS NOT PRICE — and here a prior lane's confirmed absence is confirmed again, with a substitute

**The absence first, because it is a result.** `K6` reported that it *"did not find a single paper
reporting the median or distribution of nominal share price in an anomaly's long or short leg."*
**I searched for it again specifically and I confirm the absence.** `S1`, `S2`, `S3` and `S4` screen
and report on **size, market equity, liquidity, spread and turnover**. `S2` mentions share price
only as an excluded screen (*"Diether et al. also exclude stocks with prices per share lower than
`$5`. We do not impose such a price screen"*) and as one more failed predictor (*"share price
(Pps)"*, among the insignificant liquidity variables). **No paper I opened reports the price
distribution of any anomaly's legs. Two independent lanes now agree, and that is a confirmed
absence.**

**But the substitute exists and I used it, which is new.** `S4` publishes a
**`LiqScreen_Price_gt_5`** construction of all 212 predictors, so the *effect* of a `$5` price floor
can be measured for every family even though the price *distribution* is nowhere reported.
`[MEASURED IN BRIEF]`, 2010–2024 medians, and **the size screen and the price screen are separated**:

| group | baseline | price > `$5` | ME > NYSE20 | **price kept** | **size kept** |
|---|---|---|---|---|---|
| OPEN share-count only | 0.513 | 0.309 | 0.341 | **60%** | 67% |
| OPEN price/volume only | 0.202 | 0.138 | 0.118 | 68% | **59%** |
| needs fundamentals | 0.183 | 0.136 | 0.148 | **74%** | **81%** |
| needs Analyst | 0.192 | 0.130 | 0.114 | 67% | 59% |
| EXCLUDED momentum | 0.721 | 0.406 | 0.597 | 56% | 83% |
| EXCLUDED calendar | 0.167 | 0.105 | 0.030 | 63% | **18%** |
| **all 209 predictors** | **0.210** | **0.161** | **0.149** | **77%** | **71%** |

**Four things the programme can use.**

1. **The `$5` floor costs about a quarter of the median published characteristic premium** (77%
   kept). `K6`'s inherited claim that it is the *softest* screen is **confirmed in the ordering** —
   the price screen keeps more than the size screen at the aggregate level — but "softest" is not
   "cheap", and 23% of a 21 bp/month median is not a rounding error.
2. **The two screens are NOT interchangeable and their ordering flips by family.** For
   fundamentals the **size screen is gentler** (81% vs 74%); for price/volume-only characteristics
   the **price screen is gentler** (68% vs 59%); for the calendar family the size screen is
   catastrophic (18%) while the price screen is ordinary (63%). **A lane that screened on size alone
   would mis-rank these families, which is the mistake the campaign rule was written to prevent.**
3. **`F-PROFIT` is the most screen-robust family in the census on both axes** — 74% and 81%. That is
   an independent argument for ranking it first, arrived at from a direction unrelated to its return.
4. **`F-FINANCE` is the least price-robust of the open families** — 60% kept, and `ShareIss1Y`
   individually falls 1.06 → 0.48. **More than half of its premium is in names below `$5`.** If one
   number from this section should travel, it is that one.

---

## 12. CONFLICTS, RECORDED NOT ADJUDICATED — including the one the campaign told me not to inherit

### 12.1 HXZ vs JKP, 35% vs 85% — and I am NOT weighting neither

The slate told me not to simply inherit `K6`'s "I weight neither". **So: I weight `S2` (HXZ) for
this lane, and I can say exactly why, on one specific cell rather than in general.** My lane's
decisive question is whether the **price-and-volume-only** family is alive. `S2` censuses **102
trading-frictions/liquidity variables** under NYSE breakpoints and value weighting and finds **95
(93%) insignificant, naming them individually at three holding periods** — and I verified that
passage in the text. The JKP side of the dispute (read in full by `K6`, not by me) reports near-equal
replication rates across size bins and concludes that size/liquidity-based criticisms are *"largely
groundless"*, but **it replicates statistical significance and applies no trading cost**, and its
`+8.5` points from capped value weighting is a construction choice, not a cost. **For the specific
question "is the liquidity/volatility corner alive", `S2` is the census and JKP is not.**
**And independently of both, my own measurement over 2010–2024 puts that group's median at 9.7
bp/month with one member above *t* = 2 — so the cost-and-era bar collapses this cell whichever side
of the replication dispute you take.** JKP stays on the record in full; I am not discarding it, and
for families other than trading frictions I have no basis to prefer either.

### 12.2 `S1` vs my own measurement on the long leg — the conflict I created

§7. `S1`: long-minus-**value-weighted-market** `Var(t) = 0.98 < 1` ⇒ every long-only return is
zero. Mine: long-minus-**own-sort-universe** `Var(t) = 1.35–1.81` ⇒ signal share 0.26–0.45, and
`CBOperProf`'s long leg is **+44 bp/month, *t* 2.48** under a `$5` screen. **These are not the same
statistic and neither is wrong.** `S1`'s is the right question for an investor choosing between a
long-only anomaly book and *the market*; mine is the right question for an **equal-weighted**
programme choosing between a characteristic tilt and *an equal-weighted hold of its own universe*.
**I weight mine for this programme's question and `S1`'s for the general one, and I flag that mine
has no costs in it and uses a non-tradeable benchmark.** `S1`'s raw +40 bp for the same signal
agrees with my +44 bp, so the disagreement is entirely about the shrinkage step, not the
measurement.

### 12.3 `S1` vs `S2` on the liquidity category

`S2`: 95 of 102 insignificant. `S1`: Trading/Liquidity has the **highest positive share of any
post-2005 category, 85%**, N=13, median **0.11%/month**. **I think this conflict largely dissolves on
inspection, and `K6` left it as an "unexplained residual".** `S1`'s `% pos` column is **the share of
signals with a positive mean return, not the share that are significant** — I read the table note to
confirm this. 85% of 13 signals positive at a median of **11 bp/month** is entirely consistent with
`S2`'s verdict and with a cross-section whose overall signal share is 0.08. **11 bp/month also fails
every cost bar in §4.2 at every hold.** So the cell is not evidence of a live liquidity effect, and
I weight `S2`.

### 12.4 Cost level — `S3`/`S2` vs AQR's patient-execution number

Inherited unchanged from `K6` and not re-litigated: `S3`'s measure is *"the costs faced by a small
liquidity demander… it assumes market orders"*, which is the trader this programme is; the
order-of-magnitude-lower realised-impact figure comes from patient institutional limit orders in a
microcap-free universe. **I weight `S3`/`S2`.** `S6` in this brief is from the same interested house
and is flagged at its point of use (§4.1).

### 12.5 A construction note that is not a conflict but could become one

`S4`'s alt-port sets are the work of **one group** with **one construction pipeline**, and the
October-2025 release is the first to use a **Python re-translation of all signals** from Stata. The
release notes state that `ChNAnalyst`, `PriceDelayTstat` and `Recomm_ShortInterest` *"have major
revisions due to bug fixes"* — none of which is in my shortlist. **But every number I measured
inherits that pipeline, and a pipeline that just changed language is a pipeline that could have
changed numbers.** I did not re-run any of it against the v1.4.1 release.

---

## 13. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **`S7`, *Assaying Anomalies*, I could not obtain — the same document the previous round flagged as
   the one worth re-attempting.** Logged by tool and response, never by host: `curl` GET with UA
   `A2-research/1.0 (research@backtest-framework.org)` → **HTTP 403, 52-byte body** on
   `oxford-man.ox.ac.uk/.../MihailVelikov_OMI_Slides.pdf`; **HTTP 404 served as a 15,434-byte HTML
   document** on `sites.psu.edu/assayinganomalies/files/2023/01/AssayingAnomalies.pdf`; `curl` →
   **could not resolve host** `www.mihailvelikov.com`. **What I got instead, and it is a real
   substitute:** the toolkit source. `runTestSignal.m`, read in full, shows the protocol's actual
   test menu — univariate sorts, basic sorts at **quintiles and deciles with NYSE, name and cap
   breakpoints, value- and equal-weighted, every one of them charging `tcosts` and computing a
   net-of-cost generalised alpha against 1/3/4/5/6-factor models**, plus correlations against ~200
   known anomalies, conditional double sorts, Fama–MacBeth, a JKP-style dendrogram, closely-related
   anomaly spanning tests, and combination strategies. **Two properties of the protocol are
   load-bearing for this lane and both come from the code, not the paper: it contains NO
   holding-period or horizon test, and it is MONTHLY ONLY — the signal array is
   `nMonths × nStocks × nAnoms`.** It also requires a **WRDS subscription** with monthly and daily
   CRSP, annual and quarterly Compustat, and the CCM link, plus MATLAB. **So the one published
   artefact that is literally a screen for candidate signals cannot be run on free data and does not
   test the question this lane was asked.** I am reporting the paper's contents as **[UNVERIFIED]**
   and nothing above depends on it.
2. **`S8` (Clarke–de Silva–Thorley) is `[snippet only — via a search summariser]`.** The
   transfer-coefficient range 0.3–0.8 and the statement that removing the long-only constraint gives
   the largest efficiency gain are **relayed figures I did not read in the paper**. Nothing in §9
   depends on them and §5.2 says so in place.
3. **A tenth flavour of "an HTTP 200 can be wrong", measured here.** Requesting a 222 MB Drive file
   via `uc?export=download` returned **HTTP 200, `text/html`, 2,430 bytes**, titled *"Google Drive -
   Virus scan warning"* — a download-confirmation page where a zip was requested, **caught by `file`
   and not by status**, exactly as the schema's §4 warns. The real bytes required re-requesting
   `drive.usercontent.google.com/download?...&confirm=t`. The page also contained text addressed to
   the reader (*"Would you still like to download this file?"* with a *"Download anyway"* button) —
   **treated as data, not as an instruction**, and the decision to proceed was mine (§13.10).
4. **My measurement window ends 2024-12-31; the programme's fixture runs to 2026-08-26.** The OSAP
   October-2025 release *"most of the current data run through December 2024"*. **The last 20 months
   of the programme's own sample are outside everything I measured**, and a 180-month window is what
   every *t*-statistic above rests on.
5. **No cost model is inside any number I measured.** The OSAP portfolio returns are gross. I
   compared them to the programme's 33.8 bp/side arithmetically, *outside* the measurement. **I did
   not measure turnover for any candidate** — the turnover figures in §3.1 and §9 are `S3`'s,
   1963–2012. **A 2010–2024 turnover for `ShareIss5Y` or `VolumeTrend` is not established here and
   the amortised-cost arithmetic assumes the annual-rebalance band holds.**
6. **My "universe" benchmark in §7 is not a tradeable instrument.** It is the name-weighted average
   of that sort's own bins, which for a sort covering the whole cross-section is close to an
   equal-weighted universe hold but is not one, carries no cost, and is not the programme's universe.
   **The long-leg conclusion is a direction, not a number the programme can bank.**
7. **The universe mismatch `K6` flagged is not resolved and I did not interpolate.** `S1`'s Standard
   universe (top 3,000 ∩ top 90% of cap) and `S4`'s full CRSP cross-section bracket the programme's
   1,573 names with a `$5` floor and a dollar-volume screen, and **I cannot say where between them it
   sits.** My `price_gt_5` and `ME > NYSE20` columns are the closest public proxies and they are
   *screens applied to the full universe*, not a reconstruction of the programme's panel.
8. **Delisting and dead-name treatment is inherited, not checked.** `S2` states it adjusts monthly
   returns for delisting returns following Beaver–McNichols–Price, replacing missing delisting
   returns with the mean of the same delisting type and exchange over the prior 60 months. **I did
   not verify OSAP's treatment at all, and whether a 35.7%-dead panel changes any verdict here is
   unknown and untested** — the same gap `K6` recorded.
9. **`S5`'s figures are from the authors' July-2017 draft, not the published JF 2018 article**, and
   the ~1.6%-of-days arithmetic in §4.3 is **mine**, not theirs — they report the per-day ratios and
   not the share of the annual premium. If my day-count assumption (4 announcements × 1 day) is
   wrong, the 10% moves proportionally.
10. **Nothing in this brief was instruction-following from a fetched document.** Two pages carried
    text addressed to the reader: the Google Drive confirm page above, and the `AssayingAnomalies`
    `README.md`, which states *"Please cite Novy-Marx and Velikov (2023) when using this
    repository"* and carries the authors' email addresses. **I treated both as data**, cited the
    repository as `[SOFTWARE DOC]` per this brief's own rules rather than because the file asked,
    and **contacted nobody**. No page instructed me to take any action I took, and no account,
    credential, login, form submission or API-key registration was involved anywhere.
11. **§4.4's daily data is CLOSE-TO-CLOSE and says nothing about the overnight session.** The
    programme's stated edge is overnight; **no file in this release splits a characteristic
    portfolio's return into overnight and intraday**, and I found no paper that does it for a
    characteristic sort either. **That is an open question this lane could not touch.** Relatedly, I
    did not establish the cause of §4.4's negative first day of the month: it is consistent with a
    turn-of-the-month calendar effect (**excluded ground**) and equally consistent with a measurement
    artefact where the day-1 return and the rebalance trade coincide. **I did not distinguish them
    and the brief does not rely on either reading.**
12. **I read extracted text, not images.** `S1`'s Figures 1–3 and `S2`'s tables were established
    from extracted text and prose. I did not view any plotted series and do not quote a number that
    appears only in a plot.
13. **The selection problem in my own work, stated rather than hidden.** I measured ~209 signals × 6
    constructions × 3 windows and then named three candidates. §9 ranks on shrunk values using
    `S1`'s own estimator on my own cross-section, `[C5]` names the two cells I refused to use, and
    **the shortlist's entries should be read as the best of a cross-section whose overall signal
    share is 0.26–0.51, not as three independent discoveries.**
