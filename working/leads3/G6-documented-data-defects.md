# G6 — Documented defects in the data this programme already owns

**Round 3, lane G6. External evidence only.** I have no access to this programme's files and
claim nothing about them. Every "assert" below is a check somebody would have to go and run;
not one has been run.

**The bar for this lane:** a defect is a finding only if it converts to *"assert X about the
data"*. Findings are ranked by that bar, not by how alarming they sound. Section 5 is the
scrapheap of things that did not clear it, kept visible so nobody re-researches them.

**Headline.** The single most valuable thing in this brief is not a document — it is a
**measurement I was able to make on Alpha Vantage's own published listing files**, which the
public demo key served in full. Two of the three corporate-action / instrument-basis incidents
already on this programme's record have a **documented vendor mechanism**, and one of them is
**reproducible from files anyone can pull without an API key**:

1. `TIME_SERIES_DAILY_ADJUSTED` returns **as-traded OHLCV** with adjustment carried *only* in a
   separate `adjusted close` column, while `TIME_SERIES_INTRADAY` returns **fully adjusted OHLC
   by default**. The vendor documents both, on the same page, and its own FAQ contradicts the
   endpoint doc. That is the documented mechanism for "15m is fully adjusted, daily is not".
2. `LISTING_STATUS` is **keyed on ticker with no point-in-time identity discipline**. I measured
   **28 of 425** tickers delisted on or before 2014-07-10 as *active today under a different
   issuer*, and found **delisted rows carrying the name and `assetType` of a fund that did not
   exist when the row's own delisting happened**. Two of the 425 have windows that literally
   overlap an active record on the same ticker.
3. `assetType` has exactly **two** values across 14,408 active symbols — `Stock` and `ETF`.
   There is no closed-end fund, ADR, REIT, preferred, warrant, unit, right, or note category.
   **905 of 5,801** `ETF`-classified rows do not have "ETF" or "ETN" anywhere in their name;
   **628** of those carry closed-end-fund naming. That is the vendor-side mechanism for the
   "ETF fixture was 27% closed-end funds" discovery — and it is present in the **active** list,
   not only the delisted one.

---

## 0. What I pulled, and what it is

| artefact | how obtained | type | established |
|---|---|---|---|
| `LISTING_STATUS&apikey=demo` (active, latest) | WebFetch, public demo key, 1.06 MB CSV, 14,408 data rows | [PRIMARY DATA DOC] | **[read in full]** — parsed locally, counts below |
| `LISTING_STATUS&date=2014-07-10&state=delisted&apikey=demo` | WebFetch, public demo key, 29.4 KB CSV, 425 data rows | [PRIMARY DATA DOC] | **[read in full]** — parsed locally |
| Alpha Vantage endpoint documentation | WebFetch `alphavantage.co/documentation/` and `#dailyadj` | [VENDOR OFFICIAL DOC] | [read in full] for the Core Stock section; **the page is JS-assembled and WebFetch could not reach the Corporate Action / LISTING_STATUS anchors** (§4) |
| Alpha Vantage support FAQ | WebFetch `alphavantage.co/support/` | [VENDOR OFFICIAL DOC] | [read in full] |
| CRSP *Data Description Guide*, "Factor to Adjust Price" / "Factor to Adjust Shares Outstanding" (pp. 61–62) | WebFetch → PDF saved → Read | [PRIMARY DATA DOC] | **[read in full]** |
| CRSP *Data Description Guide*, Ch. 5 "CRSP Calculations" (pp. 117–119) | WebFetch → PDF saved → Read | [PRIMARY DATA DOC] | **[read in full]** |
| NMS Plan for the Selection and Reservation of Securities Symbols (ISRA), Appendix A | WebFetch `nyse.com/publicdocs/...` → PDF saved → Read | [PRIMARY DATA DOC] | **[read in full]**, all 10 pages |
| `RomelTorres/alpha_vantage` issues #115, #215, #252, #332 | WebFetch each thread | [USER REPORT] | [read in full] |
| `cafim.sssup.it/~giulio/other/alpha_vantage/` — third-party AV-vs-CRSP comparison | WebFetch | [USER REPORT] (careful, academic-hosted, not peer-reviewed) | [read in full] |
| Portfolio Optimizer, "Selecting a Stock Market Data (Web) API" | WebFetch | [USER REPORT] | [read in full] |
| Nasdaq minimum-bid / reverse-split rule changes | WebSearch, law-firm summaries | [UNVERIFIED] secondary; the rule text itself not read | **[snippet only]** |

**A note on my own method, since this programme holds itself to it.** My first pass at counting
mis-classified `ETF` rows matched the string "ETF" against the *whole CSV line*, which contains
`,ETF,` as the `assetType` field, and returned **0**. The correct count, matching the name field
only, is **905**. The first number was an artefact of my grep, not a property of the file. Every
count in §2 is from field-addressed `awk`, and I print the raw rows that back the claims.

---

## 1. TIER A — defects with an assertion runnable on files this programme already holds

### A1. The vendor serves **as-traded** daily OHLC and **fully adjusted** intraday OHLC, and says so in two places that contradict each other

**Endpoint documentation** [VENDOR OFFICIAL DOC] [read in full]:

- `TIME_SERIES_DAILY` — *"This API returns raw (as-traded) daily time series (date, daily open,
  daily high, daily low, daily close, daily volume)"*.
- `TIME_SERIES_DAILY_ADJUSTED` — *"This API returns **raw (as-traded)** daily open/high/low/close/
  volume values, adjusted close values, and historical split/dividend events"*.
- `TIME_SERIES_INTRADAY` — the `adjusted` parameter **defaults to `true`**, applying *"historical
  split and dividend events"* to the returned OHLC.

**Support FAQ** [VENDOR OFFICIAL DOC] [read in full], flatly contradicting the endpoint doc:

> "We adjust our open, high, low, close, and volume data by both splits and cash dividend events,
> which is considered an industry standard methodology."

These two vendor statements cannot both describe `TIME_SERIES_DAILY_ADJUSTED`. On the endpoint
doc's reading — which is the one the field layout supports — **only the `adjusted close` column
is adjusted; `open`, `high`, `low`, `close` and `volume` are as-traded, forever.** On the FAQ's
reading, all five are adjusted. A reader who takes the FAQ at its word and a reader who takes the
endpoint doc at its word build different fixtures from the same endpoint.

**Two independent user reports corroborate the as-traded reading — and neither is a defect.**
This matters, because the instinct is to file them as complaints:

- Issue #115 [USER REPORT] [read in full]: reporter says *"AAPL never touch 600"*, having pulled
  `TIME_SERIES_DAILY&symbol=AAPL&outputsize=full` and got open 601.80 / high 604.4099 on
  2014-05-06. AAPL genuinely traded near $600 in May 2014, before its 7:1 June 2014 split. **The
  API was right and the reporter was wrong.**
- Issue #332 [USER REPORT] [read in full]: reporter says of NVDA on 2021-01-14, *"I can't find
  evidence that this stock was over $500"*. NVDA genuinely traded above $500 in January 2021,
  before its 4:1 (2021) and 10:1 (2024) splits. **The API was right and the reporter was wrong.**

Two users, two different tickers, two different decades, both surprised in the *same direction*.
That is stronger evidence for the as-traded semantics than a confirmed bug report would have
been, because it is the semantics reproducing itself in the wild. I record them as
**corroboration of documented behaviour, not as defects.**

**Why this is the top finding for this programme.** The record already contains *"15m is fully
adjusted, daily is not; NOW sat at 5x its own prices"*. That is exactly what the two endpoint
descriptions above predict, and nobody had to guess it: it is on the vendor's public page. The
same page also means the **$5 as-traded floor is safe if and only if it is applied to the `close`
column of the daily endpoint** — apply it to `adjusted close`, or to any intraday-derived close,
and the floor silently becomes an *adjusted* floor. §A5 is why that is a selection defect and not
just a returns defect.

**ASSERTIONS.**

- **A1.1** — assert that for every name and every bar, `close` from the daily fixture is the
  as-traded close: **assert that on the ex-date of every split in the corporate-action file,
  `close[t-1] / close[t]` is within tolerance of the split ratio** (i.e. the raw series *jumps*).
  If the series does *not* jump at splits, the column is adjusted and is not what the $5 floor
  believes it is. Run it on a name with a large known split (AAPL 2014-06-09 7:1, NVDA
  2024-06-10 10:1).
- **A1.2** — assert the converse for any intraday fixture: **assert `close[t-1] / close[t]` at the
  same split ex-dates is within tolerance of 1.0** (i.e. the intraday series does *not* jump).
  A1.1 and A1.2 must both hold, in *opposite* directions, on the same event. If they hold in the
  same direction, the two fixtures are on one basis and one of them is mislabelled.
- **A1.3** — assert `adjusted_close[T] == close[T]` at the last bar of every name (the adjustment
  base date convention), and assert `adjusted_close[t] <= close[t] * k` monotonically resolves to
  a **non-increasing cumulative factor** going backwards. A name where `adjusted_close > close`
  historically has had a reverse split; a name where the ratio is non-monotone has an event the
  factor cannot represent (see A6).
- **A1.4 — the cheap one, and the one that would have caught the 5x incident.** For every name
  present in **both** fixtures, on every date present in both: **assert
  `|daily_close(d) / intraday_derived_close(d) − 1| < 1e-6`**, and assert the count of names
  failing it is **zero**. Report the failures by name and by the *size* of the ratio — a ratio
  near a round number (2, 3, 4, 5, 7, 10, 1/8) names the split.

---

### A2. Ticker reuse is measurable in the vendor's own two files, and it is not rare

**Measured, from the two CSVs in §0.** Active list: 14,408 rows, **zero duplicate symbols**.
Delisted-as-of-2014-07-10 list: 425 rows, **zero duplicate symbols**. So reuse is invisible
*within* a snapshot and only appears *across* them.

**Intersection of the two: 28 tickers (6.6% of the 425)** were already delisted by mid-2014 and
are active today under an unrelated issuer. Raw rows, delisted first:

```
ACOM  Ancestry.com Inc            2009-11-05 → 2013-01-14   |  Harbor Active Commodity ETF   2026-06-17 (NYSE ARCA, ETF)
ADCT  ADC TELECOMMUNICATIONS INC  2001-01-02 → 2010-12-20   |  Adc Therapeutics SA           2020-05-15
ALC   Assisted Living Concepts    2006-11-10 → 2013-10-17   |  Alcon Inc                     2019-04-09
DNA   GENENTECH INC               2001-01-02 → 2010-04-05   |  Ginkgo Bioworks Holdings A    2021-04-19
LZ    LUBRIZOL Corp               2001-01-02 → 2011-11-30   |  LegalZoom.com Inc             2021-06-30
MIR   MIRANT CORP                 2006-12-28 → 2010-12-03   |  Mirion Technologies A         2020-08-20
PATH  NuPathe Inc                 2010-08-06 → 2014-03-03   |  UiPath Inc - Class A          2021-04-21
SWIM  THINKORSWIM GROUP INC.      2002-11-14 → 2009-06-26   |  Latham Group Inc              2021-04-23
MEMS  MEMSIC INC.                 2007-12-14 → 2013-09-17   |  MATTHEWS EM DISCOVERY ETF     2024-01-11 (ETF)
MBND  Multiband Corp              2006-12-28 → 2013-08-30   |  STATE STREET NUVEEN MUNI ETF  2021-02-04 (ETF)
XRTX  Xyratex Ltd                 2006-12-28 → 2014-03-31   |  XORTX Therapeutics Inc        2018-11-28
SUPX  Supertex Inc                1990-03-27 → 2014-04-09   |  Super X AI Technology Ltd     2024-04-17
...   (28 in total; also ACCL CEG CHRD CNH CSR DOLE DRS FMFC GIW INMD LSE MRX PRM ROMA SWTX WAVE)
```

**Two of the 28 have windows that literally overlap**, which is the case a date filter alone will
not save you from:

```
CNH   CNH GLOBAL N V Foreign  2001-01-02 → 2013-10-17   |  CNH Industrial NV   ipoDate 2013-09-30
      → 17 days in which the same ticker has two live records at the vendor.

CSR   CHINA SECURITY & SURVEILLANCE  2007-10-29 → 2011-09-15  |  Centerspace  ipoDate 1997-10-17
      → the ACTIVE record claims CSR has been listed since 1997; the DELISTED record says CSR
        was a Chinese surveillance company from 2007 to 2011. The two vendor records on the same
        ticker directly contradict each other.
```

`CSR` shows *why*: Alpha Vantage's `ipoDate` follows the **entity**, not the **ticker**.
Centerspace is the former IRET, which listed in 1997 and only took the ticker `CSR` in 2021. So
the vendor's own active record asserts a 1997–2026 life for a ticker that belonged to somebody
else for four years in the middle. **Any price series keyed on ticker over that span is a splice
candidate.** `DNA` is the frightening one: Genentech at ~$95 until April 2010, then Ginkgo
Bioworks — which itself did a 1-for-40 reverse split in 2024.

**And the vendor is inconsistent about it:** `CEG` gets it *right* (Constellation Energy
Corporation, `ipoDate` 2022-02-02, the spin-off date) while `CSR` gets it wrong. So you cannot
assume either convention.

**What the rulebook actually says — and the widely-repeated "90 days" is WRONG.**
NMS Plan for the Selection and Reservation of Securities Symbols, **Section IV(d) "Reuse of a
Symbol"** [PRIMARY DATA DOC] **[read in full]**:

> "if a party ceases to use a symbol (due, for example, but not limited to, the delisting of a
> security through merger or otherwise), such party automatically shall have that symbol reserved
> for a period of 24 months... If the party does not place the symbol on List A, and if the party
> does not use the symbol within 24 months, the symbol shall be released for use... A symbol may
> not be reused by a party to identify a new security (other then the security that has been
> trading under such symbol), unless the party reasonably determines that such use would not cause
> investor confusion."

Three things follow, and all three differ from the folklore:

1. **The reservation is 24 months, not 90 days.** A WebSearch result asserted a 90-day rule; the
   90 days in this Plan is the period after Commission approval before the Plan became the
   exclusive allocation mechanism, nothing to do with reuse. I record the search result's claim as
   **[UNVERIFIED] and contradicted by the primary document I read in full.**
2. **There is no minimum waiting period at all for the exchange that held the symbol.** It may
   reuse it immediately for a new security subject only to a subjective *"would not cause investor
   confusion"* test. So the 24 months is a *reservation floor for other exchanges*, not a
   *quarantine on the ticker*.
3. Symbols may be placed on **List A perpetually**, so a ticker can also sit dead for decades.
   Reuse latency has **no useful lower bound and no useful upper bound** — which means you cannot
   defend against reuse with a time gap. You defend with an identity.

**The free point-in-time identifier that survives a name's death.** There is not a good one.
CRSP `PERMNO` is the standard and is not free. The realistic free defences are (a) the **SEC
EDGAR CIK**, which this programme already has a source for, is entity-permanent, is never
recycled, and survives ticker changes and delisting — EDGAR's `company_tickers.json` and the
submissions API carry the CIK↔ticker mapping, though only for SEC registrants and only for the
*current* mapping unless historical filings are walked; and (b) **CUSIP/ISIN**, which are
security-permanent but are licensed and not freely redistributable. Neither is a drop-in for
PERMNO. The honest position is: **there is no free, point-in-time, death-surviving identifier for
US equities; CIK is the closest and it is entity-scoped, not security-scoped.** I did not verify
EDGAR's historical-mapping coverage myself (§6.4).

**ASSERTIONS.**

- **A2.1 — the decisive one, and it needs nothing new.** For every name in the fixture, assert
  **`min(bar_date) >= ipoDate`** and **`max(bar_date) <= delistingDate + k`** (k a small trading-day
  slack for the settlement of the final tape). **Assert the count of names with any bar outside
  `[ipoDate, delistingDate]` is zero.** A bar outside that window is either a wrong listing record
  or a series spliced from a different issuer, and both are the thing you are hunting. Print the
  offenders with the size of the excursion in bars.
- **A2.2** — assert **`symbols(active) ∩ symbols(delisted) == ∅`** at the ticker level across the
  vendor's two listing files. It will not be empty. Assert instead that **every ticker in the
  intersection is either absent from the fixture, or present as two disjoint series with a
  documented cut at the earlier `delistingDate`** — and assert the count of intersection tickers
  carried as one continuous series is zero.
- **A2.3** — for each name, assert **`ipoDate` is consistent with the ticker, not merely with the
  entity**: assert there is no *other* listing row for the same ticker whose
  `[ipoDate, delistingDate]` window intersects this one. `CNH` and `CSR` fail this. Two rows whose
  windows overlap on one ticker is a hard contradiction in the vendor's own file and can be
  detected with a single interval-overlap pass.
- **A2.4** — assert every fixture name carries a **CIK** (or an explicit `null` with a recorded
  reason), and assert the CIK is **constant across the whole series**. A CIK change mid-series on
  one ticker is a splice. This is the only one of the four that needs a join to EDGAR, which this
  programme already pulls.
- **A2.5 — the self-test.** Per this programme's own rule that an audit which cannot fail is worse
  than none: deliberately splice two known-reused tickers (`DNA`: Genentech bars followed by Ginkgo
  bars; `PATH`: NuPathe followed by UiPath) into one series and **assert A2.1 raises**. Break the
  *scalar the assertion compares*, not its name.

---

### A3. `LISTING_STATUS` delisted rows carry the **current** ticker-holder's name and `assetType`, stamped onto a **historical** record

This is A2's mechanism seen from the other side, and it is the finding I would put in front of
the principal first, because it is provable **without any external source at all** — the rows
contradict themselves.

All six `assetType == "ETF"` rows in the 425-row delisted-as-of-2014-07-10 file, verbatim:

```
ACTV  LEADERSHARES(R) ACTIVIST LEADERS(R) ETF          NYSE   ETF  2011-05-25  2013-11-18  Delisted
IPAL  Velocity Shares 2X Inverse Palladium Etn ...     NYSE   ETF  2011-10-17  2013-10-17  Delisted
NFS   GRANITESHARES 2X SHORT NFLX DAILY ETF            NYSE   ETF  1997-03-06  2010-01-08  Delisted
PAS   GRANITESHARES 2X SHORT PANW DAILY ETF            NYSE   ETF  2001-01-02  2011-03-07  Delisted
RISK  GLOBAL X RISK PARITY ETF                         NYSE   ETF  2010-01-22  2011-06-09  Delisted
SUPR  CAMBRIA SUPERINVESTORS ETF                       NASDAQ ETF  2011-04-27  2013-07-15  Delisted
```

**Rows 3 and 4 are internally impossible, and you need no outside knowledge to see it:**

- `NFS` — a fund whose name references **NFLX** is recorded as having IPO'd **1997-03-06**.
  Netflix itself did not go public until May 2002. A NFLX-referencing product cannot predate NFLX.
- `PAS` — a fund whose name references **PANW** is recorded as delisting **2011-03-07**. Palo Alto
  Networks did not go public until July 2012. A PANW-referencing product cannot have died before
  PANW existed.

**Externally confirmed for `PAS`** [VENDOR/ISSUER FILINGS, via WebSearch] [snippet only]:
`PAS` on NYSE was **PepsiAmericas, Inc.**, which merged into a PepsiCo subsidiary and ceased to
be independently listed in **February 2010**. So the row's *dates* are (approximately) the old
operating company's, while its *name* and *`assetType`* belong to a GraniteShares single-stock
leveraged ETF launched more than a decade later. GraniteShares' US single-stock leveraged range
did not exist before 2022. **The vendor has joined on ticker and taken the identity from the
current holder.** `SUPR` (Cambria Superinvestors, a 2022 launch, recorded as delisted 2013) and
`ACTV` (LeaderShares, a 2019 launch, recorded as delisted 2013) are the same shape.

Note also the *date* accuracy: PepsiAmericas ceased trading Feb 2010; the vendor's
`delistingDate` is **2011-03-07**. That is roughly a year late, on a name whose merger date is
in the acquirer's own 8-K. I did not test how general that error is (§6.2).

**One more corrupt row, from the same file:**

```
SWTX  NASDAQ   NASDAQ  Stock  2011-03-30  2011-12-16  Delisted
```

The `name` field is the literal string `NASDAQ`. And in the active list the first data row is:

```
-P-HIZ  Presurance Holdings Inc  NASDAQ  Stock  2023-08-30  null  Active
```

— a symbol beginning `-P-`, which is the vendor's *preferred-share suffix* convention appearing
as a *prefix*. A mangled symbol.

**ASSERTIONS.**

- **A3.1** — assert **no fixture name's metadata (`name`, `assetType`, sector, anything
  descriptive) was read from a listing snapshot taken after the name stopped trading.** Concretely:
  assert the metadata source for each dead name is a `LISTING_STATUS&date=<D>` pull with
  `D` inside that name's own trading window, and record `D` alongside the name. Metadata taken
  from today's file for a name that died in 2013 is, on the evidence above, not that name's
  metadata.
- **A3.2 — the anachronism check, and it is cheap.** For every name in the fixture, extract
  ticker-like tokens from the `name` string and **assert that no referenced ticker's own
  `ipoDate` is later than this row's `delistingDate`**. This catches `NFS` and `PAS` mechanically,
  with no human in the loop, using only the listing file joined to itself.
- **A3.3** — assert every `name` field is well-formed: **assert `name` is not equal to any value in
  the `exchange` column** (catches `SWTX`), and assert `name` is non-empty and not a pure exchange
  or status token.
- **A3.4** — assert every `symbol` matches `^[A-Z]{1,5}([-.][A-Z]{1,3})*$` and **assert the count
  of symbols beginning with a separator is zero** (catches `-P-HIZ`).
- **A3.5** — assert the fixture's `delistingDate` for each dead name is within `k` trading days of
  the **last bar** in its own price series, and report the distribution of the gap. A systematically
  late `delistingDate` (as `PAS` suggests) shows up as a one-sided distribution, and a name whose
  last bar is *far* before its recorded delisting is a name that stopped being served, not a name
  that stopped trading.

---

### A4. `assetType` has two values, so instrument class is not in the data at all

**Measured on the 14,408-row active file.**

```
assetType   Stock  8,607   ETF  5,801        status   Active 14,408 (all)
exchange    NASDAQ 6,294 | NYSE 5,835 | BATS 1,673 | AMEX 325 | NYSE ARCA 229 | NYSE MKT 52
```

There is **no category for** closed-end funds, ADRs, REITs, preferred shares, warrants, units,
rights, ETNs, exchange-traded notes/baby bonds, or trusts. They are distributed across the two
buckets by no rule I can find.

**Inside `assetType == "Stock"` (8,607 rows), 814 are not common stock** — identified by the
vendor's own symbol suffixes:

```
preferred (-P-)      394        warrants (-WS)   138        warrants (-W)   89
units (-U)            76        rights (-R)       50        share class (-X) 65
other dash             2                                    → 814 of 8,607 = 9.5%
```

Separately, **78** `Stock` rows have `Notes due`, `Preferred` or `Depositary` in the name — i.e.
corporate debt and depositary receipts filed as `Stock`.

**Inside `assetType == "ETF"` (5,801 rows), 905 do not contain "ETF" or "ETN" in the name at
all, and 628 of those carry closed-end-fund naming** (`Trust` / `Fund` / `Income` / `Municipal`).
Raw rows, verified against the file:

```
ADX    Adams Diversified Equity Fund                                    NYSE   ETF  1984-07-19
AFB    AllianceBernstein National Municipal Income Fund Inc             NYSE   ETF  2002-01-29
ABLLL  Abacus Global Management Inc. 9.875% Fixed Rate Sr Notes 2028   NASDAQ  ETF  2026-05-28
AIFEU  Aifeex Nexus Acquisition Corp Unit                              NASDAQ  ETF  2026-05-28
```

`ADX` is a genuine closed-end fund. `ABLLL` is a **corporate bond** classified as an ETF.
`AIFEU` is a **SPAC unit** classified as an ETF — while `PGACU`, another unit of the *same*
issuer, is classified `Stock`. The vendor is not merely coarse; it is inconsistent within one
issuer.

**This is the vendor-side mechanism for the finding this programme already made.** The earlier
discovery that an "ETF" fixture was 27% closed-end funds whose deaths were fund wind-ups rather
than failures is not a one-off sampling accident: `assetType == "ETF"` **is** a mixed bucket at
source, in the *active* file, today, at a rate of at least 628/5,801 ≈ **10.8%** by name pattern
alone — and name-pattern matching is a floor, not a ceiling, because CEFs with ETF-shaped names
are not counted.

**ASSERTIONS.**

- **A4.1** — assert **every fixture name's instrument class was determined by something other than
  `assetType`**, and assert the class is recorded per name. `assetType` has two values and cannot
  carry the distinction the universe depends on.
- **A4.2** — assert **no fixture symbol matches the vendor's non-common-stock suffix patterns**:
  `-P-` (preferred), `-WS` / `-W` (warrant), `-U` (unit), `-R` (rights), trailing `-[A-Z]`
  (alternate share class). Assert the count is zero, or that each survivor is individually
  whitelisted in writing. This is a pure regex over the symbol column and catches 814 of 8,607
  vendor rows.
- **A4.3** — assert **no fixture name matches closed-end-fund / debt / unit naming**: `Fund`,
  `Trust`, `Municipal`, `Notes due`, `% Fixed Rate`, `Preferred`, `Depositary`, ` Unit`, ` Right`.
  Assert every match is individually adjudicated, and record the adjudication. Report the count,
  because the count is the number this programme was previously surprised by.
- **A4.4** — assert the **cause of death** is recorded for every dead name, and assert that no dead
  name's death is a *fund wind-up*, *liquidation of a pooled vehicle*, or *ETF closure* unless the
  study intends to include them. A wind-up is not a failure and this programme has already been
  caught treating it as one.
- **A4.5 — the ADR one, which nothing above catches.** Assert whether foreign-domiciled ADRs are in
  or out, explicitly. `CNH GLOBAL N V Foreign` in the delisted file shows the vendor sometimes
  marks it in the *name* and never in a field. If ADRs are in, the corporate-action basis differs
  (ratio changes, foreign-currency dividends) and A6 applies with extra force.

---

### A5. Reverse splits make an adjustment error into a **selection** error, one-sided and concentrated in exactly the names that generate fat tails

This programme's universe is floored at **$5 as-traded close**. That makes the price column's
basis a **membership** question, not only a returns question — and this lane was told to treat
that as the more serious of the two. Here is why the exposure is asymmetric.

- A **forward** split (NVDA 10:1) makes back-adjusted historical prices *smaller*. A genuine $50
  stock in 2015 reads $5 on an adjusted basis. Effect: names get wrongly **excluded**.
- A **reverse** split makes back-adjusted historical prices *larger*, by the split ratio, for the
  entire prior history. A stock that genuinely traded at $0.10 reads $25 after a 250:1 cumulative
  reverse. Effect: names get wrongly **included**.

The second is far more dangerous, and it is not symmetric in frequency. Reverse splits are
overwhelmingly a **listing-compliance** instrument: Nasdaq Rule 5550(a)(2) requires a $1.00
minimum bid; failure for 30 consecutive business days triggers a deficiency notice and a 180-day
compliance period, and the standard cure is a reverse split. [UNVERIFIED — law-firm summaries,
**[snippet only]**; I did not read the rule text.] The same summaries report a 2024 rule change
in which Nasdaq will deny any compliance period to a company that has effected reverse splits
over the prior two years with a **cumulative ratio of 250 shares or more to one**. The
regulator's own threshold tells you the observed distribution: **cumulative reverse ratios in the
hundreds happen often enough to need a rule.**

So the population that gets wrongly lifted over a $5 floor by an adjusted-price basis is
precisely the population of **distressed, near-delisting, sub-$1 names** — which is also, on this
programme's own reported experience, the population that supplies the extreme tails of the trade
distribution. An adjusted-basis floor does not add noise. It adds a specific, one-sided,
tail-heavy cohort that was never tradeable at the size the floor was meant to guarantee.

**ASSERTIONS.**

- **A5.1 — the one that matters.** Assert the universe floor is evaluated on the **same column**
  A1.1 proved jumps at splits. Concretely: **assert `min(as_traded_close)` over each name's held
  bars is `>= 5.00`**, recomputed from the raw column, and assert it agrees name-for-name with the
  membership the study actually used. Report the count of names whose membership changes.
- **A5.2** — assert the **cumulative adjustment factor** for every name is computed and stored,
  and assert **no name enters the universe on a bar where `cumulative_factor > 1`** unless its
  as-traded price on that bar independently clears $5. Equivalently: **assert
  `as_traded_close = adjusted_close × cumfac` is reproduced exactly** for every bar, so the two
  bases can never be silently interchanged again.
- **A5.3** — assert the **count of reverse splits** in the fixture window, the distribution of
  their ratios, and the count of names with **cumulative** reverse ratios above 10, 50 and 250.
  Then assert **none of those names contributed a top-1% trade**. This programme's own reporting
  standard already requires naming the top trade; this makes the reverse-split cohort a named
  slice of that report.
- **A5.4** — assert the dollar-volume screen is on the **same basis** as the price floor. Volume is
  adjusted by a *different* factor from price (see A6), so a screen that mixes an adjusted price
  with a raw volume, or vice versa, is a third basis nobody declared.

---

### A6. A single multiplicative price factor **cannot** represent several common corporate actions — CRSP says so in the primary document

This is the clearest published statement of correct handling, and I read it in full.

**CRSP, *Data Description Guide*, "Factor to Adjust Price" (p. 61)** [PRIMARY DATA DOC]
**[read in full]**. CRSP splits distributions into cases where the price factor equals the share
factor and cases where it does not:

> "3. For stock dividends and splits, *Factor to Adjust Price* is the number of additional shares
> per old share issued: `facpr = (s(t) − s(t')) / s(t') = s(t)/s(t') − 1` ... In a reverse split,
> *Factor To Adjust Price* will be between -1 and 0."
>
> "4. In other less common distribution events, **spin-offs, non-total or non-final liquidating
> distributions, and rights**, *Factor to Adjust Price* is **not equal to** *Factor to Adjust
> Shares Outstanding*. *Factor to Adjust Price* is defined as the **Dividend Cash Amount divided
> by the stock price on the Ex-Distribution Date**: `facpr = DIVAMT / P(t)`."
>
> "5. Other cases where *Factor to Adjust Price* may not be equal to factor to adjust shares are
> **issuances and limited tender offers**. For issuances, *Factor to Adjust Price* is set to zero.
> For limited tender offers where a limited set percentage of shares are accepted in exchange for
> cash, *Factor to Adjust Price* is set to the ratio of shares accepted multiplied by -1."

And **"Factor to Adjust Shares Outstanding" (p. 62)**:

> "For **spin-offs**, *Factor to Adjust Shares Outstanding* is set to **zero**. For **rights
> issues**, *Factor to Adjust Shares Outstanding* is calculated based on all shareholders
> exercising the rights on the Ex-Distribution Date."

**CRSP, Ch. 5 "CRSP Calculations", "Adjusted Data" (p. 117)** [PRIMARY DATA DOC] **[read in
full]** — the sentence that matters most for a bar file:

> "Split events always include stock splits, stock dividends, and other distributions with price
> factors such as spin-offs, stock distributions, and rights. **Shares and volumes are only
> adjusted using stock splits and stock dividends.**"

and, on gaps:

> "**If there is a gap in trading where possible split events are not known, all adjusted values
> are set to missing** when the gap is between the observation and the adjustment base date."

**Per-class verdict on "can one multiplicative price factor represent it?"**

| class | one factor? | why not |
|---|---|---|
| Forward split | **yes** | `facpr = s(t)/s(t') − 1`; ratio is known and exact |
| Reverse split | **yes** | same formula, `facpr ∈ (−1, 0)`; but see A5 — it is the *selection* consequence that bites |
| Stock dividend | **yes** | CRSP treats it identically to a split |
| Ordinary cash dividend | **yes, for total return; no, for price** | CRSP sets `facpr = 0` and carries the cash in `DIVAMT` separately. Folding a dividend into a *price* factor is a different object from the price series |
| Special / large cash dividend | **yes mechanically, dangerous in practice** | still `facpr = 0` + `DIVAMT`, but a large special dividend produces a raw price gap that a naive gap-detector reads as a split |
| **Spin-off** | **NO** | `facpr = DIVAMT / P(t)` — a *value* ratio, not a share ratio, requiring the **cash-equivalent value of the distributed stub on the ex-date**. That number is not derivable from the parent's own price series. And `facshr = 0`, so price and shares/volume move on *different* factors |
| **Rights issue** | **NO** | same `DIVAMT / P(t)` form; `facshr` assumes full exercise. The theoretical ex-rights price depends on subscription price and take-up, neither of which is in a bar file |
| **Return of capital / non-ordinary distribution** | **NO, if treated as a dividend** | CRSP: *"Dividend Amount can be divided into nonordinary and ordinary types. Nonordinary dividends include return of capital distributions."* Booked as an ordinary dividend it inflates total return; booked as a price factor it corrupts the price |
| **Partial / non-final liquidating distribution** | **NO** | explicitly in CRSP's case 4 |
| Total liquidation / merger / full exchange | **NO — it is a terminal event** | CRSP sets `facpr = −1` **by convention**; the economics live in the **delisting return**, not the factor |
| Share-class consolidation / redenomination | **case by case** | if the exchange ratio is fixed it reduces to a split; if it involves a cash element or a class-specific dividend it does not |
| Limited tender offer | **NO** | `facpr` = (share ratio accepted) × −1; a partial cash-out is not a price rescaling |

**The line that connects this to this programme's record.** Spin-offs, rights and partial
liquidations all have `facpr = DIVAMT / P(t)`. A vendor whose corporate-action schema offers only
a `split coefficient` and a `dividend amount` has **exactly one place to put that `DIVAMT`: the
dividend field.** That is not a hypothesis about a vendor — it is what the schema forces. And
"thirty fabricated return days from corporate actions booked as dividends" is that forcing,
observed. The right response is not to distrust dividends generally; it is to **separate ordinary
from non-ordinary**, which is precisely the distinction CRSP names and a two-field schema cannot
express.

**Third-party corroboration that the vendor's `adjusted close` specifically diverges from CRSP**
[USER REPORT — careful, academic-hosted, not peer-reviewed] **[read in full]**: an analyst
compared Alpha Vantage to CRSP and concluded *"In general, I'd advise against using the 6th column
of the data obtained with `TIME_SERIES_DAILY_ADJUSTED`"*, recommending instead that the user build
the factor from the **split coefficient** column, and noting *"sometimes Alpha Vantage seems to
return un-adjusted quantities, sometimes the adjusted ones"*. This is **one** careful report, not
two; I record it as a lead, not a fact. But it points the same way as A1: the raw columns and the
split coefficient are the trustworthy part; the derived `adjusted close` is the part to rebuild.

**ASSERTIONS.**

- **A6.1 — the core one.** Assert that **every day on which the raw close-to-close gap exceeds a
  threshold (say 20%) is explained by a record in the corporate-action file** — a split, a
  dividend, or a written exception. Assert the count of unexplained gaps is zero, and print the
  survivors by name and date. This is the general net that catches spin-offs, rights, special
  dividends and return-of-capital in one pass, without needing to know which is which.
- **A6.2 — the one that separates the classes.** For each explained gap, assert the **implied
  factor from prices** matches the **stated factor from the action**:
  `assert |(close[t-1] − divamt) / close[t] × split_coef − 1| < tol`. Where it fails, the action
  is one of CRSP's case-4 classes and the two-field schema has mis-booked it. **The failures are
  the finding.**
- **A6.3 — volume, which nothing else checks.** Per CRSP, *"Shares and volumes are only adjusted
  using stock splits and stock dividends."* So: **assert volume is rescaled on split ex-dates and
  is NOT rescaled on spin-off / rights / dividend ex-dates.** Concretely, assert
  `median(volume) ` is continuous across every non-split corporate action, and discontinuous by the
  split ratio across splits. A vendor that applies one factor to both price and volume fails this.
- **A6.4 — gaps, per CRSP's own rule.** Assert that for any name with a trading gap longer than `k`
  bars, **either the corporate-action file covers the gap, or the adjusted values across it are set
  to MISSING** — CRSP's stated behaviour. Assert the count of gaps carried silently is zero. A
  halted or suspended name that resumes at a different basis is the classic case.
- **A6.5 — dividends split by type.** Assert every dividend in the corporate-action file is
  classified **ordinary vs non-ordinary**, and assert the count of unclassified ones is zero.
  Then assert that no *single* dividend exceeds some fraction (say 5%) of the prior close without
  being individually adjudicated — a large "dividend" in a two-field schema is the signature of a
  spin-off or a return of capital wearing a dividend's clothes.
- **A6.6 — the terminal return, which a price file does not contain.** CRSP: *"Delisting Return is
  the return of security after it is delisted... If there is no opportunity to trade a stock after
  delisting before it is declared worthless, the value after delisting is zero... If information
  after delisting is insufficient to generate a return a missing value is reported."* A bar file's
  last bar is the last *trading* price, not the terminal payoff. **Assert every dead name has an
  explicit terminal treatment recorded** — an applied delisting return, or an explicit "exit at
  last close" with that choice written down — and assert the count of dead names with no terminal
  record is zero. On a dead-inclusive panel this is a first-order P&L question, not hygiene.
- **A6.7 — the self-test.** Assert A6.1 **raises** on a book where one known spin-off's price gap
  has had its corporate-action record deleted, and assert A6.3 **raises** on a book where volume
  has been rescaled at a spin-off. Break the compared scalar, not the assertion's name.

---

## 2. TIER B — documented, but the assertion needs one extra public pull first

### B1. The point-in-time delisted list looks **thin**, and I could not confirm whether that is the list or the query

`LISTING_STATUS&date=2014-07-10&state=delisted` returned **425 rows total**, covering delistings
from **1997-04-01 to 2014-07-09**, distributed:

```
1997:1  2006:1  2007:2  2008:4  2009:39  2010:43  2011:75  2012:56  2013:145  2014:59 (to 09 Jul)
```

Roughly 40–145 delistings a year across all US exchanges. That is **implausibly low** against any
reasonable prior for US equity delistings, which run in the several hundreds per year. But I
cannot turn "implausible" into a finding without the comparison, and **I could not get the
comparison**: my attempt to pull the *current* full delisted list was blocked (§4), and I did not
read a peer-reviewed delisting-count series to benchmark against. Two readings remain open:

- **(a)** the vendor's historical `LISTING_STATUS` backfill is genuinely thin, in which case a
  dead-inclusive universe built from it is *survivorship-biased despite being labelled
  dead-inclusive* — the worst kind, because the label defeats the suspicion; or
- **(b)** the `date=` parameter returns something narrower than "all names delisted on or before
  D" — e.g. only names the vendor was tracking at that time.

**ASSERTION, once the comparison exists.** Pull `state=delisted` with no date and with
`date=<end of fixture>`, and **assert the two agree on every delisting with a date before the
fixture end**. If the dateless list has materially more pre-2014 delistings than the
`date=2014-07-10` list does, reading (b) is right and **the point-in-time query is not
point-in-time** — which would be a finding of the same class as A3. Then, separately, **assert
the fixture's dead fraction is within a stated band of an independent delisting count** for the
same window and the same exchange/price/volume screens.

### B2. The `adjusted close` column has at least one reproducible corruption report, and it is a **column-alignment** shape

Issue #215 [USER REPORT] [read in full]: a single reporter (`PolVW`) on `VIX` reports an
`ADJUSTED CLOSE` of **245397** on **2004-12-31** — *"completely out of a possible range"* — and,
crucially, that repeated identical requests return **different** values for the same day:
*"with the same request, I get different results for the ADJUSTED CLOSE, for the same day"*.
Issue closed with no maintainer or vendor response visible.

**This is one report, not two, and it is on an index rather than an equity.** I record it as
**evidence of a complaint, not of a defect**, per this lane's rule. But the *shape* is worth an
assertion because a value of 245397 in a price column is almost certainly a **volume** value
landing in the wrong field, and non-determinism across identical requests points at a serving
bug rather than a methodology choice — and both are cheaply detectable.

**ASSERTIONS.**
- **B2.1** — assert every price field is within a sane range: `0 < price < 1e5`, and assert
  `low <= min(open, close) <= max(open, close) <= high` on every bar. Assert the count of
  violations is zero. This is a one-line pass that would have caught 245397.
- **B2.2 — determinism.** Pull a fixed set of ~20 names twice, some hours apart, and **assert the
  two pulls are bit-identical on every historical bar before the last week.** Any difference on an
  old bar is either a revision (B3) or the non-determinism #215 describes. Both need to be known.

### B3. Adjusted series are **necessarily** restated, so a cached fixture goes stale in a specific, predictable way

Not a complaint — a mechanical consequence of A1 plus CRSP's base-date convention. Every new
split or dividend rewrites the *entire prior history* of `adjusted close` for that name. A fixture
pulled in year Y and re-used in year Y+2 has an `adjusted close` column that is stale for every
name that has since had a corporate action, while its raw OHLC columns are unchanged. **The two
columns in one file therefore drift onto different vintages.** This programme's own habit of
keying caches on estimator mtimes does not catch this, because nothing in the repo changed.

**ASSERTION.** Assert the fixture records its **pull date**, and assert `pull_date` is later than
the **last corporate action** of every name in it. Then, periodically: re-pull a sample and
**assert raw OHLC is bit-identical** while allowing `adjusted close` to move; assert the set of
names whose raw OHLC moved is empty. Raw bars changing retroactively is a vendor revision and a
different, worse problem than restatement.

---

## 3. TIER C — worries, explicitly labelled as such, because they do not convert to an assertion

Recorded so nobody spends a round re-finding them.

1. **"Alpha Vantage sometimes has missing days."** Issue #74 and scattered forum reports
   [USER REPORT] [snippet only]. Generic, undated, no reproducible case, and true of every
   vendor. A calendar-completeness check is worth having anyway, but it is hygiene, not this
   lane's product, and I will not dress it up as a finding.
2. **"Free data is survivorship-biased."** True, widely written up, and **true of everyone's free
   data** — which this lane was told not to report as though it were specific. This programme's
   panel is already dead-inclusive at a stated ~35.7%. The *specific* version of this worry is
   B1, which is about whether the vendor's dead list is complete, and that is where it belongs.
   The numbers circulating in blog posts ("up to 75% of stocks excluded", "a strategy expected to
   yield 20% returned 8%") are [UNVERIFIED] blog-tier and I would not cite them.
3. **Endpoint availability and tier changes.** `TIME_SERIES_DAILY_ADJUSTED` is a premium function
   for `outputsize=full`; a third-party test [USER REPORT] [read in full] records being unable to
   evaluate Alpha Vantage at all because *"this endpoint was restricted a couple of months ago"*.
   Vendor coverage claims have also moved — an older library's docs say "20+ years", the current
   vendor page says "25+ years". This is a procurement risk and a reproducibility risk, not a data
   defect, and there is no assertion against a file that catches it.
4. **The vendor's competitor comparisons.** `alphavantage.co/best_stock_market_api_review/` and
   `alphavantage.co/iexcloud_shutdown_analysis_and_migration/` are **[SALES INSTRUMENT]** hosted
   on the vendor's own domain. I did not use them and would not.

---

## 4. Blocks, logged by tool and response

1. **WebFetch** → `https://www.alphavantage.co/query?function=LISTING_STATUS&state=delisted&apikey=demo`
   and `...&state=active&date=2014-07-10&apikey=demo` — **response body was empty (`{}`)**, on the
   3rd and 4th demo-key call, after two calls to the same host returned full CSVs. Consistent with
   a demo-key rate limit, but the response carried **no** rate-limit message, so I am recording the
   observed response (`{}`) and not the inferred cause. This is what prevents B1 from being Tier A.
2. **WebFetch** → `https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=IBM&outputsize=compact&apikey=demo`
   — returned a JSON object with a single `"1. Information"` field, quoted in §5 below. No time
   series. So I could **not** read the actual JSON field names of the daily adjusted response and
   could not empirically confirm A1 against live bars; A1 rests on the vendor's documentation and
   two user reports, not on data I pulled.
3. **WebFetch** → `https://www.alphavantage.co/documentation/#listing-status` and `#splits` —
   returned the Core Stock section only; the page is JS-assembled and the fragment anchors do not
   change what the fetcher receives. **I never read the LISTING_STATUS, SPLITS or DIVIDENDS
   documentation verbatim.** Everything I know about `LISTING_STATUS` comes from the CSVs I pulled
   and from the Excel add-in reference (below).
4. **WebFetch** → `http://www.crsp.com/products/documentation/distribution-codes` —
   `getaddrinfo ENOTFOUND www.crsp.com`. The **DISTCD four-digit coding scheme was never read.**
   The `terpconnect.umd.edu` mirror of the CRSP coding guide fetched successfully but the fetcher
   reported the distribution-code table was not in the extracted content. §A6's class table is
   therefore built from the two CRSP pages I *did* read in full, plus general knowledge — it is
   not a transcription of CRSP's code list.
5. **WebFetch** → `https://hexdocs.pm/alpha_vantage/AlphaVantage.StockTimeSeries.html` — 301 to
   `alpha-vantage.hexdocs.pm`; followed manually, fetched successfully.
6. **WebFetch** → two CRSP PDFs and the NYSE symbology PDF initially returned "content is raw
   binary"; all three were saved locally by the tool and **read in full via the Read tool**. Not
   blocks in the end, but logged because the first response looked like one.

---

## 5. Safety — text in fetched content addressed to the reader

Per the standing instruction, I quote and flag rather than act.

**Alpha Vantage, demo-key API response** [VENDOR OFFICIAL DOC]:

> "The **demo** API key is for demo purposes only. Please claim your free API key at
> (https://www.alphavantage.co/support/#api-key) to explore our full API offerings. It takes fewer
> than 20 seconds."

This is an instruction to the reader to register for an account. **I did not act on it and did not
sign up for an API key**, per the brief. It is the vendor's own funnel copy, not an attack, but it
is exactly the shape the rule exists for and it is the reason B1 and A1's empirical leg are
unfinished. Nothing else in anything I fetched was addressed to me or attempted to direct my
behaviour.

No file was downloaded by me; the four PDFs and two CSVs listed in §0 were saved automatically by
WebFetch into the session's own tool-results directory as a side effect of fetching public URLs,
and were read from there.

---

## 6. What I could not verify, stated plainly

1. **I never read Alpha Vantage's `LISTING_STATUS`, `SPLITS` or `DIVIDENDS` documentation.** The
   documentation page would not serve those sections to my fetcher (§4.3). Everything in A2/A3/A4
   about `LISTING_STATUS` is inferred from **the CSVs themselves**, which is stronger evidence for
   what the data *is* but tells me nothing about what the vendor *claims* it is. In particular I
   cannot quote the vendor on what the `date=` parameter means, so **B1's reading (b) is
   unresolved.** The only vendor statement I have on `date=` is the Excel add-in reference:
   *"Listing\_date: Object (Optional) Get listing status for this date. Default is most recent
   trading date"* [VENDOR OFFICIAL DOC] [read in full] — which does not disambiguate it.
2. **I did not establish how general the `delistingDate` error is.** I have exactly one case —
   `PAS` / PepsiAmericas, ceased trading Feb 2010, vendor says 2011-03-07 — and the Feb 2010 date
   itself is from search snippets of PepsiCo filings, **[snippet only]**, not from a filing I
   opened. One case is an anecdote. A3.5 is the assertion that would turn it into a number.
3. **I could not confirm the delisted-list coverage question at all** (§B1). The current full
   delisted list was blocked. I therefore do **not** claim Alpha Vantage's delisted coverage is
   thin; I claim the 2014 point-in-time slice *looks* thin and that the check is cheap.
4. **I did not verify that SEC EDGAR CIK is usable as a point-in-time identifier.** I asserted in
   A2 that CIK is entity-permanent and never recycled, which is standard, but I did **not** open
   EDGAR's documentation in this session, did not check whether a historical ticker↔CIK mapping is
   published (as opposed to only the current one), and did not check coverage for foreign private
   issuers or for companies that deregistered. **A2.4 rests on an unverified premise about EDGAR.**
5. **I did not read the Nasdaq or NYSE rule text on minimum bid price or reverse splits.** §A5's
   regulatory claims — the $1.00 minimum, the 30-day/180-day mechanics, the 250:1 two-year
   cumulative threshold — are from **law-firm client alerts via search snippets, [UNVERIFIED],
   [snippet only]**. The *argument* in A5 does not depend on those numbers being exact; it depends
   only on reverse splits being common among distressed names, which those sources agree on. But
   do not quote 250:1 as established.
6. **I did not read CRSP's DISTCD code table** (§4.4). A6's per-class table is my synthesis from
   the two CRSP pages I read in full; the class list is not a transcription of CRSP's enumeration
   and may omit classes CRSP codes separately.
7. **I read no peer-reviewed source in this lane.** Zero. Everything above is vendor
   documentation, primary market-structure documents, the vendor's own data files, and user
   reports. That is appropriate for the territory — there is no academic literature on one
   vendor's endpoint semantics — but it should be stated rather than glossed.
8. **I could not confirm A1 empirically against live bars.** The demo key would not serve
   `TIME_SERIES_DAILY_ADJUSTED` (§4.2). A1 is documented-plus-corroborated, not measured. **A1.1
   and A1.2 are the assertions that would measure it, and they need no new data — the fixtures
   already exist.**
9. **The 28-ticker reuse count is a lower bound of unknown tightness.** It is the intersection of
   *one* 425-row delisted snapshot with *one* active snapshot, twelve years apart. It says nothing
   about the reuse rate over a shorter horizon, and the 6.6% figure should not be extrapolated —
   short tickers recycle far faster than long ones, and 425 names is a small and possibly
   non-representative slice (see item 3).
10. **Issues #215 and #252 are single reports each, and #252 is unresolved with no maintainer
    reply.** Neither meets the two-independent-reports bar. I have carried #215 into Tier B only
    because the assertion it suggests (B2.1) is nearly free, not because I believe the report.
11. **I have made no claim about this programme's files.** Every count in this brief is from the
    vendor's public listing CSVs or from documents I read. Whether any of the assertions above
    would fire is unknown to me and unknowable from where I sat.

---

## 7. If only three things get run

Ranked by (evidence strength) × (cost to run) × (severity if it fires):

1. **A2.1** — `assert min(bar_date) >= ipoDate and max(bar_date) <= delistingDate + k`, count of
   violations zero. Catches ticker-reuse splices. Needs nothing new. The `DNA` case
   (Genentech → Ginkgo, with a 1-for-40 reverse split in the second life) is what it is for.
2. **A1.4** — `assert |daily_close(d)/intraday_close(d) − 1| < 1e-6` for every name-date in both
   fixtures, count of failures zero. Directly re-tests the incident already on the record, and
   the failure *size* names the split.
3. **A6.1 + A6.2** — every >20% raw gap is explained by a corporate action, **and** the implied
   factor reconciles to the stated one. The reconciliation failures are exactly CRSP's case-4
   classes — spin-offs, rights, partial liquidations, return of capital — which is the family that
   produced the fabricated return days.

Each of the three should be paired with its deliberate-break self-test (A2.5, A6.7), breaking the
**scalar the assertion compares**, not the assertion's name.
