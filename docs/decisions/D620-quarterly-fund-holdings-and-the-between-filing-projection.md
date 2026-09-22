# D620 — The quarterly fund holdings from EDGAR, and the between-filing projection: the filings give 415 fund-quarters back to 2006, and the projection between them is worth a third of the level and nothing at all of the flow

**Status:** Committed
**Date:** 2026-09-22
**Category:** Data
**Source:** The principal, 2026-09-22, on estimating fund futures holdings and flow from the
10-Q/10-K Schedule of Investments — *"Go for this I like it"* — and *"Can we project this
backwards / in between the filings based on current AUM and shares?"*, which is answered here by
**measurement** rather than by argument.
Spec: `docs/internal/User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md` (v1.9, an untracked
read-only source: never staged, never copied) §3.1 lines 56–70 (the fund universe, the panel
schema, *"Contract months matter"* and the point-in-time rule) and §3.2 lines 86–92 (the
futures/swap split).
Builds directly on [D619](D619-the-fund-panel-the-fund-facts-and-the-cme-side-census.md), which
established that these six funds file **zero N-PORT** and that the Schedule of Investments inside
the quarterly 10-Q and the annual 10-K is the only free historical holdings route, and which left
*"No holdings history for any fund. One day, 2026-09-18."* Every fetch goes through
[D608](D608-the-forward-data-recorder.md)'s `Recorder.record`; the SEC user agent and rate floor
are [D331](D331-the-deal-filter.md)'s, reused through `scripts/fetch_fund_facts.py` rather than
restated. The validation reads `fund_nav_daily` through
[D609](D609-the-panel-loader-chokepoint-and-the-seven-root-multiplier-fix.md)'s
`load_panel(..., reserved_from="2024-01-01")`.
[D191](D191-manifest-only-storage-for-large-archives.md) (cache the raw, commit the derived),
[D48](D48-no-false-affordances-enum-values-and.md) (raise loudly),
[D550](D550-what-CI-found-in-its-first-run.md) (newline pinning),
[D604](D604-futures-sqrt-impact-depth-scaling-and-the-book-depth-fixture.md) (the holdout
sentence), [D606](D606-the-error-budget-the-fitting-helpers-and-the-parameter-budget.md)
(importing a runner's module body).

## Decision

Three scripts, two gitignored fixtures with their metas, a sources list, and three test files.
**No strategy return is computed and nothing is scored.** Every error number quoted below is
measured on rows dated **2023-12-29 or earlier**.

| file | what it is |
|---|---|
| `scripts/fetch_fund_filings.py` | all 231 10-Q/10-K primary documents plus XBRL companyfacts, job `sec_fund_filings`; `--index --plan --facts --documents --prices --report --selftest` |
| `scripts/build_fund_holdings_quarterly.py` | the Schedule-of-Investments parse, six gates, `--build --gates --one ACC --selftest` |
| `scripts/project_fund_panel.py` | the principal's question: three methods × two clocks against daily truth; `--premium --validate --build --selftest` |
| `data/fixtures/fund_holdings_quarterly.csv.gz` + `.meta.json` | **2,139 rows, 415 fund-quarters with holdings, six funds, 2006-12-31 → 2026-06-30** |
| `data/fixtures/fund_panel_projected.csv.gz` + `.meta.json` | **9,598 rows**, UNG and USO, daily estimated shares and AUM, `est_flag = 1` on every row |
| `data/fund_facts/FILINGS.md` | the sources list: 231 filings, accession, form, period, filed date, bytes, parsed |
| `tests/unit/test_fund_holdings_quarterly.py`, `tests/unit/test_fund_panel_projection.py`, `tests/golden/test_fund_projection_ledger.py` + `.hand.txt` | **39 + 24 + 21 = 84 tests** |

**The fixtures:** `fund_holdings_quarterly.csv.gz` sha256
`491dd40199f3481601c1d262dc3f219b5bfaea7fd338ca915d20abef1785f210`, 44,674 bytes;
`fund_panel_projected.csv.gz` sha256
`5c78e88cf1a52cdf3309ac97e5eb9c45f3ef8aadeae48172e5fa08c3c004a643`, 29,022 bytes. Both gzip
streams are deterministic (`mtime=0`, no stored filename, D619's pattern), so a digest is a fact
about the rows and not about when the build ran.

**`--selftest` final lines: 10 breaks / 10 fired / 0 silent** (`fetch_fund_filings.py`),
**10 / 10 / 0** (`build_fund_holdings_quarterly.py`), **11 / 11 / 0**
(`project_fund_panel.py`).

---

## 1. The answer to the principal's question, in one sentence and then in numbers

> **No — not usefully.** Between filings, the point-in-time projection of a fund's share count is
> wrong by a **median 36–44%** and its AUM by a **median 18–33%**, and the quantity the
> settlement ledger actually consumes — the daily creation flow — is **uncorrelated with the
> truth (−0.05 to −0.001)** because the estimate moves on **46 to 56 days out of 2,979–3,714**
> while the fund's real share count moves on **840 to 2,037**. Backwards is a different question
> and the answer there is **yes**: the filings themselves reach back to 2006 and are actual
> observations, four a year.

Measured on the four funds that have BOTH a filing history and a daily truth series (`fund_nav_daily`,
D619), on rows to 2023-12-29:

| method / clock | | BOIL | KOLD | SCO | UCO |
|---|---|---:|---:|---:|---:|
| **`step` / `filed`** — the only fully point-in-time cell | shares, median rel | **0.363** | **0.401** | **0.444** | **0.369** |
| | shares, p95 | 2.836 | 2.289 | 2.337 | 1.197 |
| | **AUM, median rel** | **0.273** | **0.325** | **0.296** | **0.180** |
| | AUM, p95 | 1.005 | 1.095 | 1.047 | 0.701 |
| | Δshares correlation | −0.006 | −0.050 | −0.010 | −0.001 |
| | days the estimate moves / days the truth moves | **46 / 934** | **44 / 840** | **56 / 1,700** | **56 / 2,037** |
| `price_implied` / `filed` | AUM, median rel | 0.361 | 0.405 | 0.443 | 0.370 |
| `step` / `period` — **no filing lag**, unattainable | AUM, median rel | 0.181 | 0.217 | 0.193 | 0.126 |
| `linear` / `period` — **hindsight bound** | AUM, median rel | 0.134 | 0.206 | 0.158 | 0.095 |

Three readings, and the second and third are the ones that matter.

1. **The level is a third wrong and the flow is nothing.** A 30% error on AUM is survivable for a
   sizing input and fatal for a flow input, and the flow column says why: differencing a
   piecewise-constant estimate gives a whole quarter's creations on one day and zero on the other
   sixty. The ledger's P3 consumes ΔH, which is built from Δshares. **This panel must not be
   differenced.**
2. **Half of the level error is the FILING LAG, not the interpolation.** Moving from the `filed`
   clock to the `period` clock — pretending each 10-Q arrives the day its quarter closes — cuts
   the median AUM error from 0.27/0.33/0.30/0.18 to 0.18/0.22/0.19/0.13. The remaining half is
   what a quarterly observation cannot know about the intervening days, and **perfect hindsight
   interpolation only takes it to 0.13/0.21/0.16/0.10.** There is no method to find here; the
   information is not in the filings.
3. **Carrying today's close forward makes AUM WORSE, and the mechanism was tested rather than
   told.** `price_implied` (stale shares × today's close) is worse than `step` (stale shares ×
   stale NAV) on all four funds — 0.36 against 0.27 on BOIL. The explanation is that creations
   are contrarian, so a stale share count and a stale NAV err in opposite directions and partly
   cancel, while a stale share count times a current price errs twice the same way. That is a
   claim about a sign, so it is computed: the daily correlation of Δlog(shares) against
   Δlog(NAV) is **−0.76 (BOIL), −0.40 (KOLD), −0.51 (SCO), −0.72 (UCO)**, Spearman −0.27 to
   −0.32. The story holds, and the written panel uses `step`.

**`linear` is measured and cannot be written.** It interpolates towards an anchor published 40–90
days after the period it closes, so a panel built with it is a one-quarter look-ahead on every
row and nothing downstream would reveal it. `build("linear")` raises, and so does
`build("step", clock="period")`.

---

## 2. What the filings give, and it is more than the brief expected

231 documents, **573.2 MB**, 240 recorder requests in total (231 primary documents + 3
companyfacts + D619's 3 submissions indices and 3 10-Ks), one thread at `MIN_INTERVAL = 0.5 s`,
GET only. **224 of the 231 accessions yielded at least one parsed holdings row.**

| fund | periods with holdings | span | periods with an anchor | periods with a futures NOTIONAL | unparsed rows |
|---|---:|---|---:|---:|---:|
| BOIL | **59** | 2011-12-31 → 2026-06-30 | 59 | 59 | 56 |
| KOLD | **59** | 2011-12-31 → 2026-06-30 | 59 | 59 | 56 |
| SCO | **71** | 2008-12-31 → 2026-06-30 | 70 | 71 | 54 |
| UCO | **71** | 2008-12-31 → 2026-06-30 | 69 | 71 | 53 |
| UNG | **77** | 2007-06-30 → 2026-06-30 | 77 | **37** | 52 |
| USO | **78** | 2006-12-31 → 2026-06-30 | 78 | **37** | 55 |

So the quarterly split and the held months exist back to inception for all six — **415
fund-quarters** — with the futures/swap split computable on **256** of them.

**The two right-hand columns are the honest part.** USO's and UNG's Condensed Schedule of
Investments carried **no notional column at all** before ~2016: the 2008 row reads `Crude Oil
Futures contracts, expires May 2008  7,122  $ (13,349,470)  (1.84)`, which is contracts,
unrealized gain and percent of partners' capital. `notional_usd` is **null** there and `f_fut` is
null with it, rather than being computed off the unrealized column — a number that would have
looked entirely reasonable. Of 2,139 rows, **326 are `kind="unparsed"`**, and 297 of those are
the benign kind: a filing's comparative column supplies an anchor for a period whose Schedule of
Investments it does not carry. The other 29 are pre-inception filings (BOIL and KOLD launched in
October 2011, twelve ProShares filings predate them) and USO's 2006 pre-launch shell, which holds
$1,000 in cash and no schedule. **Every one carries a reason and the meta counts them; none is
skipped.**

### `f_fut` over time, and the 0.249 of D619 is not a one-day fact

D619's single measurement — UCO 0.249 futures / 0.751 swap on 2026-09-18 — now has a history
behind it. Across all rows where it is computable, `f_fut` runs from **0.054 to 1.000**. At
2026-06-30 the parse reads **UCO 0.183 with four swap lines** and **SCO 1.000 with none**, against
D619's live-page 0.249 and 1.000 nine weeks later. **That agreement is gate G5**, and it is a
real known-answer check: two different documents, two different hosts, two different parsers, and
it raises rather than warns if UCO loses its swaps or SCO gains any.

### Four things the documents say that a summary would have lost

1. **The month a line names is not the same word in the two families.** USCF writes
   `NG August 2026 contracts, expiring July 2026` — delivery month and expiry month, separately.
   ProShares writes only `expires March 2025`, and the evidence that this is the **delivery**
   month is the June/December pattern of the Bloomberg Commodity Balanced index: UCO's three legs
   read March, June and December 2025, and a balanced index's deferred legs are the June and
   December *contracts*, which expire in May and November. The reading is an inference from that
   pattern and every row carries `month_basis ∈ {stated_contract, expires_label, cme_code}` so a
   study can filter on it instead of inheriting a guess.
2. **The 2011–2013 ProShares filings name the contract by its CME code** — `WTI Crude Future
   11/15/2012 (CLX2)` — and the date beside it is **not** the contract's expiry (CLX2 expired
   2012-10-22). The code is used and the date is discarded; `cme_code_month` resolves the single
   year digit against the period the contract is held at.
3. **One filing states a contract month before its own period end.** USO's 2013-09-30 10-Q
   (`0001144204-13-060424`) says *"NYMEX WTI Crude Oil Futures CL August 2013 contracts, expiring
   July 2013"* in the September schedule. It is **transcribed as filed with a reason on the row**,
   and gate G2 is a SHARE test (bar 1%, observed 1 of 835 = 0.12%) so that one bad sentence does
   not block a build while a column read in the wrong order still does.
4. **One filing misspells its own fund's name.** A heading reads `PROSHARES ULTR ASHORT BLOOMBERG
   CRUDE OIL`. It was found by the unmapped-series audit — every `PROSHARES … SCHEDULE OF
   INVESTMENTS` header in every document is returned whether or not it maps to one of the four —
   and the alias patterns now match against the name with every space removed. The audit's other
   24 unmapped names are the trust's other series (ULTRAPRO 3X CRUDE OIL, ULTRA BLOOMBERG
   COMMODITY, the VIX funds, the currency funds) and are correctly excluded; `fullmatch` on
   space-free patterns is what keeps `ULTRA` off `ULTRASHORT` and `ULTRAPRO`.

### The optimisation pass, and what companyfacts could and could not do

Projected before the run: 231 documents at 0.5 s pacing is 116 s plus roughly half a gigabyte of
transfer; measured **573.2 MB and about seven minutes**. One pass was made first:
`data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json` is **one call per registrant** and carries
every XBRL-tagged share count and net-asset figure with its period end, filing date and
accession — which would remove the balance-sheet parse entirely.

**It works for USO and UNG and it does not work for ProShares, and the reason is worth recording.**
The companyfacts API exposes only the non-dimensional facts, so for a **multi-series trust it
returns the REGISTRANT TOTAL**: ProShares Trust II's `CommonStockSharesOutstanding` at 2024-12-31
is **89,221,884 shares** and `StockholdersEquity` **$3,025,133,601** — sixteen funds added
together, with no `LegalEntityAxis` to split them. (It is also restated across filings: the same
2024-12-31 share count reads 89,221,884, then 98,048,396, then 86,352,499 as the trust's series
list changes.) So **per-fund anchors for BOIL, KOLD, UCO and SCO have to come out of the document
itself**, and the balance-sheet parse was built anyway. The three companyfacts calls are recorded
and are the anchor route for the two USCF funds if the document parse ever needs a second opinion.

The optimisation that did pay is duller: the fetch is **resumable and idempotent by accession**, so
a second `--documents` run makes zero requests.

---

## 3. The measurement the projection could not have been made without: the split basis

**`fund_nav_daily` is fully back-adjusted for reverse splits (D619) and a filing states the count
as published.** Compared directly, the measured share error on BOIL was **6,548×** — a factor, not
a fit. D619 recorded that *"No split source other than the series itself was available"*. **There
is one**: Alpha Vantage's `8. split coefficient`, already on disk for UNG and USO and fetched here
for the four ProShares tickers. With

    k(t) = product of every split coefficient effective strictly after t
    nav_published(t)    = nav_backadjusted(t) * k(t)
    shares_published(t) = shares_backadjusted(t) / k(t)
    aum(t)              = unchanged, because k cancels

BOIL's first row — D619's own example, `NAV 8,000,000` against `0.50005` implied shares — has
`k = 5.0e-6` across seven splits and becomes **$40.00 a share and 100,010 shares**, which is what
a 2× natural-gas fund looks like at launch.

**The known-answer check on the whole reconstruction is external.** The converted daily NAV is
compared to the NAV per share the filing printed for the same period end — two sources with
nothing in common — and agrees to a **median relative error of 1.3e-4 (BOIL), 6.8e-5 (KOLD),
1.2e-4 (SCO), 1.1e-4 (UCO)** over 32–43 period ends each, which is the filings' own two-decimal
rounding. The p95 and max are large on KOLD and UCO (0.36, 2.0) and those are period ends within
a day or two of a split ex-date, where the two sources' effective dates differ; they are reported
and not smoothed. The conversion is additionally asserted against D619's AUM identity, which `k`
must cancel out of exactly, and that assertion raises.

**k(t) for a pre-seal date uses split ratios from after the seal**, and that is correct rather than
a leak: those splits are already inside every pre-seal row of `fund_nav_daily` — that is what
"fully back-adjusted" means — and a split ratio is a corporate action, not a price or a return.

### The restatement, and why every anchor is taken as FIRST PUBLISHED

UNG's FY2023 10-K footnotes *"On January 23, 2024 there was a 1-for-4 reverse share split.
Historical shares outstanding, net asset value per share, and market value per share have been
adjusted … on a retroactive basis."* Its 2022-12-31 share count is published **four times as
30,184,588** and a fifth time, in that 10-K, as **7,546,147**.

`anchors()` therefore takes each field from the **earliest filing that carries it non-null**, with
that filing's own date. Across the six funds there are **26 restated share counts and 25 restated
NAVs**, and **every single ratio is exactly a split ratio** — 0.5, 0.25, 0.2, 0.1, 0.125, 0.05 —
matching the Alpha Vantage coefficients one for one (UNG 2010-12-31 ×0.5, 2011-12-31 ×0.25,
2022-12-31 ×0.25; USO 2019-12-31 ×0.125). A panel anchored on the latest filing would carry those
factors across whole years **with no discontinuity to notice**. One restated net-asset figure
(UCO) is the only non-split restatement in eighteen years.

### The premium, which is what `price_implied` pays for using a close where a NAV belongs

`|close − NAV| / NAV` on the four funds where both are known, on the as-published basis, to
2023-12-29:

| fund | days | median | p95 | max |
|---|---:|---:|---:|---:|
| BOIL | 2,998 | **52.4 bp** | 232.0 bp | 700.9 bp |
| KOLD | 3,078 | **51.3 bp** | 233.6 bp | 717.5 bp |
| SCO | 3,799 | **37.1 bp** | 161.7 bp | 1,730.9 bp |
| UCO | 3,799 | **37.3 bp** | 166.9 bp | 2,222.5 bp |

Median signed premium is +6.4, −7.2, +4.3 and −6.2 bp, so there is no systematic side. **Half a
percent at the median and over two percent at the p95** is the size of the error a study inherits
by treating the market close as the fund's NAV, and it is small beside the 18–44% the share count
contributes — which is the point: **the projection's error is the share count, not the price.**

---

## 4. What UNG and USO now have, and what is still absent

`data/fixtures/fund_panel_projected.csv.gz`: **9,598 rows**, 4,799 each for UNG and USO,
**2007-08-09 → 2026-09-04**, `date, fund, shares_out_est, aum_est, nav_proxy, method, clock,
anchor_period_end, anchor_filed_date, est_flag`. Method `step`, clock `filed`, `est_flag = 1` on
every row, and on every row the anchor was published **before** the date it is used on.

**Its stated uncertainty is the measured ProShares error, carried in the meta**: shares median
0.36–0.44, AUM median 0.18–0.33, p95 0.70–2.84, with the flow numbers and the premium table
beside them. That is an honest label rather than a bound — UNG and USO are +1× funds and the four
measured ones are ±2×, so their creation behaviour is not the same process, and the meta says the
error is *carried* rather than *derived*.

**Nothing is written back into `fund_nav_daily`** and the projected panel is a separate fixture
with its own meta.

**What is still absent.**

- **UNG and USO have no daily NAV truth and this record did not find one.** USCF's holdings page
  is JavaScript-gated (D619), `accounts.profunds.com` 404s for both tickers, and no URL was
  invented. The panel above is an estimate with a measured error and it is not a substitute.
- **No holdings history at daily frequency for any of the six.** Quarterly is what the SEC has;
  ProShares publishes today's and no archive.
- **P9 — the eight non-US leveraged ETPs — remains at zero sourced.** Q14 and Q16 open, exactly
  as D619 left them.
- **`f_fut` is null on 594 of 2,139 rows**, all of them USCF filings from the era with no notional
  column. USO's and UNG's futures/swap split before ~2016 is not obtainable from the Schedule of
  Investments.
- **Gate 0 still does not clear.** Holdings point-in-time is now **partly** satisfied — 415
  fund-quarters at a 40–90 day lag, against the daily series §3.1 asks for — and the four §3.2
  facts are unchanged from D619's 30 sourced / 10 unknown.

---

## 5. Defects found and fixed while building, because both were silent

1. **`\s*#?` ate the column separator.** The USCF share-count and NAV patterns were written
   `...(?P<a>[\d,]+)\s*#?(?:\s+(?P<b>[\d,]+))?`. The `\s*` consumes the space whether or not a
   footnote marker follows, so the optional second group could never match its own leading `\s+`,
   and **every USCF filing returned the current period's share count and a null for the
   comparative column**. The frame was well formed and every gate passed. It was caught by the
   hand file, which types both columns out. Now `(?:\s*#)?`.
2. **A later partial match blanked an anchor inside one filing.** Both families repeat the phrase
   "Statements of Financial Condition" in the front index and again in the notes, so a section
   walk finds three matches where one carries the table. Replacing on every match let the notes —
   which restate total partners' capital and nothing else — erase a share count the real table had
   already supplied. `_merge_anchor` now keeps the **first** non-null per field.

Both are the same shape: a projection anchor with a hole in it, produced by code that raised
nothing.

---

## 6. Footer drafts for the integrator

### `docs/data-available.md` — two §4 paragraphs

> **`fund_holdings_quarterly` — every fund-quarter's Schedule of Investments, 2006–2026 (D620).**
> `period_end, fund, kind ∈ {futures, swap, cash, other, unparsed}, contract_month, month_basis,
> contracts, notional_usd, month_weight, description, counterparty, shares_out, net_assets,
> nav_per_share, f_fut, n_fut_lines, n_swap_lines, n_months_held, futures_notional_total,
> swap_notional_total, source_accession, filed_date, form, issuer, sign_basis, reason` — 2,139
> rows over **415 fund-quarters** for BOIL, KOLD, UCO, SCO, UNG and USO, parsed out of all **231**
> 10-Qs and 10-Ks the three registrants have filed (573 MB of recorded HTML under
> `data/raw/recorder/sec_fund_filings/`). **`filed_date` is the known-at date and is the cut
> column**; `period_end` is the as-of and is a *wrong cut*, because every fund's 2023-12-31
> holdings were published in 2024. **`contracts` and `notional_usd` are SIGNED** (long positive,
> short negative) and `notional_usd` is **null across the USCF era before ~2016, which published
> no notional column at all** — `f_fut` is null there too rather than computed off the unrealized
> gain, which is why `f_fut` exists on 1,545 of 2,139 rows. **A period that could not be parsed is
> a row with `kind="unparsed"` and a reason, never a gap**: 326 of them, 297 being a filing's
> comparative column supplying an anchor without a schedule. **All publications of a period are
> kept**, because 26 share counts are restated by later filings and every restatement ratio is
> exactly a reverse-split ratio. `contract_month` carries `month_basis` saying whether the filing
> named the delivery month, the CME code, or only an "expires" label. The span runs through the
> deposit's sealed vault window and past the 2024-01-01 seal; the meta carries D604's holdout
> sentence and nothing here may score anything.

> **`fund_panel_projected` — estimated daily shares and AUM for UNG and USO (D620).**
> `date, fund, shares_out_est, aum_est, nav_proxy, method, clock, anchor_period_end,
> anchor_filed_date, est_flag` — 9,598 rows, 2007-08-09 → 2026-09-04, **`est_flag = 1` on every
> row**. The two USCF funds have quarterly filings and no daily truth, so their shares and AUM are
> carried forward from the last filing **published** on or before each date (method `step`, clock
> `filed`). **This is not a truth series and must not be differenced for creation flow.** Its
> uncertainty is measured rather than asserted: the same method run on the four ProShares funds,
> which do have a daily truth series, is wrong by a **median 36–44% on shares and 18–33% on AUM**
> (p95 0.70–2.84), and its day-to-day Δshares is **uncorrelated with the truth** (−0.05 to −0.001)
> because it moves on 46–56 days where the real count moves on 840–2,037. Half the level error is
> the 40–90 day filing lag and the rest is what a quarterly observation cannot know; perfect
> hindsight interpolation only reduces the median AUM error to 0.10–0.21. Nothing is written back
> into `fund_nav_daily`. The meta carries D604's holdout sentence.

### `CHANGELOG.md` — a bullet

> - **D620 — the quarterly fund holdings from EDGAR, and the between-filing projection.** All
>   **231** 10-Qs and 10-Ks of the six funds' registrants recorded (573 MB, 240 requests, SEC-paced
>   through D608's recorder) and parsed into `data/fixtures/fund_holdings_quarterly.csv.gz`: **415
>   fund-quarters** of futures and swap lines with signed contracts, notional, contract months and
>   counterparties back to 2006, six gates, and **every unparsed period written down with a reason**
>   rather than skipped. `data/fixtures/fund_panel_projected.csv.gz` answers the principal's
>   question — *"Can we project this backwards / in between the filings?"* — **backwards yes, in
>   between no**: the point-in-time projection is wrong by a **median 36–44% on shares and 18–33% on
>   AUM**, and its creation flow is **uncorrelated with the truth** (−0.05 to −0.001, moving on 46
>   of 2,979 days where the truth moves on 934). Along the way: `fund_nav_daily` put on an
>   as-published basis using Alpha Vantage split coefficients (D619 recorded none were available),
>   verified against the filings' own NAV per share to **1e-4**; **26 restated share counts, every
>   ratio exactly a split ratio**; the close-versus-NAV premium measured at **37–52 bp median,
>   162–234 bp p95**; and creations shown to be **contrarian** (Δlog-shares against Δlog-NAV,
>   −0.40 to −0.76), which is why stale shares × today's close is worse than stale shares × stale
>   NAV. `companyfacts` gives per-fund anchors for USO and UNG and **registrant totals only** for
>   ProShares Trust II. `data/fund_facts/FILINGS.md` is the sources list. 84 tests.

### `src/backtest_framework/data/panel_catalogue.py` — two rows

```python
PanelSpec("fund_holdings_quarterly", "data/fixtures/fund_holdings_quarterly.csv.gz",
          "filed_date", "iso_day", "csv", ("period_end",)),
PanelSpec("fund_panel_projected", "data/fixtures/fund_panel_projected.csv.gz",
          "date", "iso_day", "csv", ("anchor_filed_date", "anchor_period_end")),
```

**The cut column on the holdings panel is `filed_date` and `period_end` is the wrong cut**, which
is the reverse of what a holdings table usually wants. A row's `period_end` is its as-of; its
`filed_date` is when it existed. They differ by 40–90 days, so a reserved-slice cut on `period_end`
lets through rows whose only publication is after the seal. `period_end` may still be **read** —
`wrong_cuts` forbids being the cut, not being a column — and a study that wants the as-of is
expected to read both.

### Deposit tests claimed

**None.** The deposit's §12 has no filings test, ledger 3 and ledger 12 are D610's, and nothing in
the crosswalk fits this record without stretching. `data/deposit_test_map.json` is not edited.

---

## 7. What this record did NOT do

- **No strategy return was computed and no bar from 2024-01-01 on was read for any return.** The
  validation reads `fund_nav_daily` through `load_panel(reserved_from="2024-01-01")` and every
  error number is measured at or before 2023-12-29.
- **Nothing was purchased and no key was used except the existing Alpha Vantage one**, whose value
  never reaches a manifest: the recorded `source_url` carries `apikey=REDACTED`.
- **`data/recorder/jobs.json` was not edited**, nor `data/data_manifest.json`,
  `panel_catalogue.py`, `data/deposit_test_map.json` or any file in the staged round-4 index. The
  catalogue rows and the data-available paragraphs above are drafts for the integrator.
- **No UNG or USO daily NAV was found.** The JS gate stands and no workaround was attempted.
- **`linear` was measured and never written.** The written panel uses `step` on the `filed` clock,
  and both other combinations raise.

## Consequences

**What is now available that was not.** A quarterly holdings history for all six deposit funds
back to inception — 415 fund-quarters of contract months, signed contract counts, notional and
counterparties — where D619 had one day. The first `f_fut` time series anybody here has had. A
split-reconstruction that puts D619's back-adjusted NAV panel and the filings on one basis and
agrees with them to 1e-4. And an estimated daily panel for the two funds that had nothing.

**What is now known to be harder than it looked.** The between-filing projection the principal
asked about is worth a third of the level and none of the flow, and **the limit is information
rather than method**: hindsight interpolation with no filing lag still misses 10–21% of AUM. If
the settlement ledger needs daily creations for UNG and USO, it needs a daily source — which this
repository does not have and which the SEC does not supply — not a better interpolation.

**The sharpest single number is 46 against 934.** That is how many days the projected share count
of BOIL changes, against how many days its real one does, over the same 2,979 sessions. A
projection can carry a level. It cannot invent an event.
