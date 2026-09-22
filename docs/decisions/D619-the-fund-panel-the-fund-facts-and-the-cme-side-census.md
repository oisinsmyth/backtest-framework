# D619 — The fund panel, the fund-facts SOURCES, and the CME-side census: TAS exists, options OI does not, and UCO is three quarters swap

**Status:** Committed
**Date:** 2026-09-22
**Category:** Data
**Source:** `docs/internal/User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md` (v1.9, an
untracked read-only source: never staged, never copied, quoted with line numbers) — §3.1 lines
56–70 (the fund universe and the panel schema), §3.1b lines 72–84 (the P9 products), §3.2 lines
86–92 (the four facts), §3.3 line 97 and Q3 (TAS), §P8a lines 326–329 (the roll schedules), §12
line 756 (unit test 50), Gate 0 at line 534, and §13A.3 line 821 (the `fund_snapshot` and
`tas_summary` jobs). Every fetch goes through
[D608](D608-the-forward-data-recorder.md)'s `Recorder.record`; governed by
[D191](D191-manifest-only-storage-for-large-archives.md) (cache the raw, commit the derived,
verify hashes loudly). Shaped on [D586](D586-FIXTURE-cme-settlement-windows-with-effective-dates.md)'s
SOURCES file — *"read out of the RAW response bytes … not out of a summary"* — and on
[D581](D581-STAGE-0-DESIGN-gamma-conditioned-close-on-ES-the-discriminator.md)'s quote-first,
probe-the-parent discipline. Reuses [D497](D497-RESULT-the-four-quadrant-open-interest-read-carries-nothing.md)'s
causality rule by compiling it rather than restating it, and
[D331](D331-the-deal-filter.md)'s SEC user agent and rate floor the same way.
[D48](D48-no-false-affordances-enum-values-and.md) (raise loudly),
[D550](D550-what-CI-found-in-its-first-run.md) (newline pinning),
[D604](D604-futures-sqrt-impact-depth-scaling-and-the-book-depth-fixture.md) (the holdout sentence).

## Decision

Six new scripts, one gitignored fixture with its meta, a fund-facts pair, and two census
artifacts. **No strategy return is computed and nothing is scored.** The panel is NAV, shares and
AUM; the gates are arithmetic on those three.

| file | what it is |
|---|---|
| `scripts/fetch_fund_nav.py` | the four ProShares historical NAV CSVs through `Recorder.record`, job `proshares_nav` |
| `scripts/fetch_fund_holdings.py` | one live GET per fund page, job `proshares_holdings`, plus `parse_holdings`, `f_fut`, `f_fut_derivatives` and a `--selftest` |
| `scripts/fetch_fund_facts.py` | the SEC filings behind `SOURCES.md`, job `sec_fund_filings`, plus `validate_fund_facts` |
| `scripts/build_fund_panel.py` | `--build`, `--gates`, `--selftest`; also `usable_oi`, the deposit's test-50 join |
| `data/fixtures/fund_nav_daily.csv.gz` + `.meta.json` | 16,402 rows, four funds, 2008-11-24 → 2026-09-18 |
| `data/fund_facts/SOURCES.md` + `fund_facts.json` | the §3.2 facts, 30 sourced and 10 unknown, with a validator that raises |
| `scripts/probe_energy_options_parents.py` | what every candidate CL/NG option parent and TAS symbol resolves to; metadata calls only |
| `scripts/quote_energy_options_pull.py` | `get_billable_size` + `get_cost` only; `submitted: false` |
| `data/tas_symbology_probe.json`, `data/energy_options_parents_probe.json`, `data/energy_options_pull_quote.json` | the census output |
| `tests/unit/test_fund_panel.py`, `tests/golden/test_fund_panel_ledger.py` + `.hand.txt` | 40 unit, 10 golden |

**The fixture:** sha256 `54c2ee9f0bf2a0470d0036bc5f0727fa62ed4bbecf5bd0b3cc538e46532a3ce2`,
**323,613 bytes**, uncompressed CSV sha256
`e3a2f9d347fb34b0c4fc77394fea8dd530b91b035bab638cd9d9282bec85e744` (the meta's
`sha256_uncompressed_csv`). The gzip stream is **deterministic**
(`mtime=0`, no stored filename, `build_fut_book_depth.py:589`'s pattern) — three consecutive
builds of the same rows gave three different digests before that line existed, which would have
made the meta's sha256 a fact about when the build ran.

---

## 1. What exists, what does not, and the three routes that are blocked

**Before this record the repository had no fund fetcher, no NAV series, no holdings and no fund
SOURCES: §3.2 stood at 0 of 4.** It now stands at 30 facts sourced and 10 unknown across six
funds, with one day of holdings and no history of them.

| source | verdict |
|---|---|
| `accounts.profunds.com/etfdata/ByFund/{BOIL,KOLD,UCO,SCO}-historical_nav.csv` | **works.** HTTP 200 `text/csv`, 2008/2011 → 2026-09-18. The UCO form of the link is printed on the UCO fund page as its "Historical NAV" download; the other three are that template. **UNG and USO 404** — they are USCF funds. |
| `www.proshares.com/our-etfs/leveraged-and-inverse/{slug}` | **works, and FORWARD ONLY.** The holdings table is server-rendered; there is no historical archive. |
| `www.uscfinvestments.com/holdings/{uso,ung}` | **HTTP 200 and unusable.** The table is loaded by JavaScript from `assets/javascript/api_key.php`. `…/uso` carries no NAV or CSV link. **No URL is recorded as ready** — a URL is never invented. |
| `www.sec.gov/cgi-bin/browse-edgar?…&output=atom` | **HTTP 503 `text/html`**, `urllib.request.urlopen`, three header combinations (the repository's SEC agent alone; plus `Accept-Encoding: gzip, deflate`; plus `Accept: application/atom+xml,text/xml,*/*` and an explicit `Host`), four attempts each. `data.sec.gov/submissions/CIK{cik}.json` answers **200 to the same headers** and carries the same index. Nothing is scraped around the block. |
| `www.sec.gov/Archives/edgar/data/…` | **works.** The three 10-Ks are recorded, 8.4 MB + 2.1 MB + 2.1 MB. |

**N-PORT does not apply, and that is an answer rather than a gap in the search.** All six funds
are commodity pools, not '40-Act funds. ProShares Trust II files `424B3, EFFECT, 8-K, CORRESP,
UPLOAD, 10-Q, POS AM, S-1/A, S-1, FWP` and the two USCF partnerships the same set — **zero N-PORT
between them**. The free historical holdings route is the **Schedule of Investments inside the
quarterly 10-Q and the annual 10-K, at a 40–90 day lag**, and there is no monthly position file
to be had at any price from the SEC.

**The ProShares CIK ambiguity is resolved, not inherited.** `0001415311` (ProShares Trust II)
lists `AGQ, BOIL, EUO, GLL, KOLD, SCO, SVXY, UCO, UGL, ULE, UVXY, VIXM, VIXY, YCL, YCS, ZSL`.
**`0002019448` is ProShares Trust III and has filed only `DRS`, `S-1` and `RW`** — it files for
none of the four.

**One content-negotiation trap, recorded because it cost a fetch.** `www.proshares.com`
negotiates on `Accept`: the recorder's own header (`text/html,application/json`) returns **7.8 KB
of Optimizely CMS JSON with no holdings**, and `Accept: text/html` returns the 270 KB page. Both
are in the manifest — the JSON records of 23:14Z are kept, not deleted, because they carry the
prospectus, SAI and annual-report URLs this repository had no link to. `fetch_fund_holdings.py`
builds its own request; `recorder.http_get` takes no headers argument and was not edited.

---

## 2. The scale audit — and the brief's premise was wrong in an instructive way

The brief said *"the earliest rows are on another scale"*. **They are not on another scale. The
whole series is fully back-adjusted for reverse splits**, and the early rows are what that looks
like at the far end of a 2× natural-gas fund's life.

BOIL's first row is `NAV 8,000,000`, `Shares Outstanding (000) 0`, `AUM 4,000,400`. The tell is
one division: **`AUM / NAV` = 0.50005 shares.** No fund holds half a share. NAV and the share
count have been multiplied and divided by the cumulative reverse-split factor; AUM, in dollars,
has not. Three measurements close it:

- `NAV[t] / PriorNAV[t] == 1 + NAV Change (%)/100` on **every one of the 16,484 rows**, to 2e-4;
- `max |NAV[t-1]/PriorNAV[t] − 1|` is **3.2e-5 (BOIL), 7.5e-5 (KOLD), 5.9e-3 (UCO), 1.5e-2 (SCO)**
  — four orders of magnitude below any split ratio;
- therefore the split search returns **[] on all four funds**, and that empty list is falsifiable:
  `test_split_detector_finds_a_planted_split_and_reports_the_inverse_match` plants a 1-for-10 and
  the detector finds it, with `nav_ratio` 10.0, `shares_ratio` 0.1 and `inverse_match` true.

**No split source other than the series itself was available.**
`data/raw/alphavantage/daily_adjusted_etf/` holds UNG and USO only — neither is one of these four
— and carries prices, not corporate actions.

### The seed-row rule: `shares_out == 0`, and why not `nav > 1e4`

| rule | rows it takes |
|---|---|
| **`shares_out == 0`** (chosen) | **82, all BOIL's, contiguous at the head, 2011-10-04 → 2012-01-31.** Zero in KOLD, UCO and SCO. |
| `nav > 1e4` (rejected) | **2,327 of BOIL's 3,761 rows and 7 of SCO's** — 62% of BOIL, and ordinary rows of a back-adjusted series. |

What makes the 82 unusable is not their scale: **a published share count of zero beside a
four-million-dollar AUM cannot carry per-share arithmetic, and differencing it for creation flow
reads a flat zero across the fund's whole seed period.** They are dropped and named in the meta.
**Nothing is rescaled.** 16,484 − 82 = 16,402.

### G1: the AUM identity, and why the brief's 1 bp is reported and not gated

The brief's gate was `aum ≈ nav × shares_out × 1000` within 1 bp on ≥ 99% of rows. **The data
refuses it, for a reason about the source and not about the parse.** `Shares Outstanding (000)`
is published to two decimals of thousands — **ten shares** — so when BOIL held five shares in
February 2012 the rounding is the whole quantity.

| fund | within 1 bp (reported) | within half a rounding unit (**gated**) | worst tolerance use | worst 1-bp row |
|---|---:|---:|---:|---|
| BOIL | **29.87%** | **100.000%** | 0.99979 | 2012-02-01, implied 5.00005 shares against 10 published |
| KOLD | **71.42%** | **100.000%** | 0.93981 | 2017-12-07, 12.9 bp |
| SCO | **99.20%** | **100.000%** | 0.99980 | 2008-12-05, 1.40 bp |
| UCO | **99.89%** | **100.000%** | 0.79984 | 2008-11-28, 1.40 bp |

So G1 is `|nav × shares_out − aum| ≤ |nav| × (10/2 + 1e-3)` on ≥ 99% of rows, which is
**100.000% on all 16,402**. It is still a known-answer check on the parse — swapping the shares
and AUM columns takes it to 0.000% and raises — and `assert code, not data` is the rule that
chose it. **`worst_tolerance_use` is reported beside the pass rate on purpose**: a 100% pass says
the parse is consistent and only that number says how much room it had, and on BOIL's 2012-02-01
row it had 0.02% of it. A gate whose strength is invisible is a gate that can rot quietly.

The other four: **G2** dates strictly increase per fund; **G3** no duplicate `(date, fund)`;
**G4** exactly the four funds, each non-empty; **G5** spans reported —
BOIL 2012-02-01 → 2026-09-18 (3,679), KOLD 2011-10-04 → 2026-09-18 (3,761),
SCO and UCO 2008-11-24 → 2026-09-18 (4,481 each). `--selftest` breaks each one at the scalar it
compares: **10 breaks, 10 fired, 0 silent.**

### What the panel does NOT carry

Deposit §3.1 line 67 asks for `date, fund, nav, shares_out, aum,
futures_notional_by_contract_month, swap_notional, source, published_at`. This source carries six
of the nine. **The other three are ABSENT COLUMNS, not null-filled ones**, and the meta names
them: a column of nulls reads as data that happened to be missing on those days; an absent column
says the source never had it. `shares_out` is stored in **shares** (the source column × 1000), and
the meta says so, because a column called `shares_out` holding thousands is a trap.

**The holdout note is carried in the meta**, in the words of
`data/fixtures/fut_book_depth_1m.meta.json#holdout`: the span runs through the deposit's sealed
vault window (2025-03-01..2026-09-18) **and** past this repository's 2024-01-01 seal, the
principal has reconciled neither with the other, and nothing here may score anything until that
reconciliation is in writing.

---

## 3. The live holdings day — the one measurement that changes a flow model

Holdings **as of 9/18/2026**, parsed from the recorded pages:

| fund | futures share of DERIVATIVE exposure | contract months | lines |
|---|---:|---|---|
| BOIL | **1.000** | NOV26 | 1 futures, +25,857 contracts, $786,828,510 |
| KOLD | **1.000** | NOV26 | 1 futures, −7,042, −$214,288,060 |
| **UCO** | **0.249** | DEC26, JUN27, DEC27 | 3 futures ($218,081,730) against **4 swap lines** ($657,673,266) |
| SCO | **1.000** | DEC26, JUN27, DEC27 | 3 futures, −7,822 / −8,883 / −9,286 |

**Two things here matter more than the fact that §3.2's first bullet is now sourced.**

1. **UCO is three quarters swap and SCO, its −2× partner on the same index, is zero.** So three
   quarters of UCO's rebalance flow does not reach the CME order book as UCO's order at all — it
   reaches it, if at all, as a counterparty's hedge, at the counterparty's timing. **A flow model
   that maps UCO's daily rebalance onto CME futures one-for-one is wrong by a factor of four on
   this date**, and the factor is not constant, because nothing published says it is. The deposit
   already routes on `f_fut` (test 3, *"`f_fut = 0` routes all rebalance to P2"*); this is the
   first measurement of what `f_fut` actually is, and it is neither 0 nor 1.
2. **UCO and SCO hold DEC26, JUN27 and DEC27, not the front month** — the Bloomberg Commodity
   Balanced WTI index's three schedules showing through. Deposit §3.1 line 69
   (*"Contract months matter … which may **not** be the front month"*), made concrete.

`f_fut` as the brief defines it — futures over TOTAL exposure, collateral included — is 0.5959 for
BOIL on this day; `f_fut_derivatives` is the §3.2 number and is 1.000. **Both are computed and
both are reported, because they answer different questions and the denominator is the whole
difference.** The parser carries the swap branch and **a swap line IS live today** (UCO's four),
so it is exercised against real bytes as well as against the synthetic row the `--selftest` uses.

**A parse that finds no `Holdings as of` date or no futures row RAISES.** Seven guards, all seven
proved to fire, including on the real CMS-JSON response.

---

## 4. The §3.2 facts — 30 sourced, 10 unknown, and Gate 0 does not clear

Full table with quotes and accessions in [`data/fund_facts/SOURCES.md`](../../data/fund_facts/SOURCES.md);
machine-readable in `fund_facts.json`, validated by `validate_fund_facts`, which **raises** on a
missing key, a `sourced` fact with no source, an `unknown` fact carrying a value, `lag_c` outside
{0, 1, null}, or a quote over fifteen words.

| fact (§3.2) | BOIL | KOLD | UCO | SCO | UNG | USO |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| futures/swap split | ●¹ | ●¹ | ●¹ | ●¹ | ○ | ○ |
| creation cut-off + `lag_c` | ● | ● | ● | ● | ● | ● |
| settlement-price vs TAS | ○ | ○ | ○ | ○ | ● | ● |
| index roll schedule | ○ | ○ | ○ | ○ | ● | ● |
| expense ratio | ● | ● | ● | ● | ● | ● |
| NAV strike basis (Q10) | ● | ● | ● | ● | ● | ● |
| index construction | ● | ● | ● | ● | — | — |

● sourced · ○ unknown, value `null` · ¹ point-in-time only; **no issuer publishes the split over
time**

**`lag_c = 0` for all six.** Every one transacts creations on the order date. And the clocks are
not one clock:

| | cut-off | NAV strike |
|---|---|---|
| BOIL, KOLD, UCO, SCO | **2:00 p.m. ET** | **2:30 p.m. ET** |
| UNG, USO | **12:00 p.m. ET** (or the earlier Arca close) | futures at the 2:30 p.m. settlement; basket NAV at **4:00 p.m. ET** |

**The ProShares clock lands exactly on the deposit's own window.** 2:30 p.m. ET is the CLOSE of
the NYMEX energy settlement window, 14:28:00–14:30:00 ET (D586), so the cut-off leaves **28
minutes** between the last order the fund can accept and the first second of the window its NAV
will be struck in — which is the interval `Q_rem` is about. **The USCF cut-off is two and a half
hours ahead of the window and their basket NAV is struck ninety minutes after it.** A study that
treats the six as one cohort is averaging over a 2½-hour spread in when the order is known.

**TAS appears ZERO times** in all three filings — 1,151,333 + 542,935 + 516,020 characters of
extracted text. That is evidence on deposit Q2 and **it is not proof of absence**; a fund can
transact a TAS instrument without naming it in a 10-K, and the USO filing names a third
possibility explicitly: the AP may be required to *"enter into or arrange for a block trade, an
exchange for physical or exchange for swap"* at the closing settlement price, **so some creation
flow is priced by the window without ever being in it.**

**Rolls.** UNG's rule is now attached to an accession: four days beginning two weeks from
expiry, with the filing spelling out 75/25, 50/50, 25/75 and then the next month — **the
deposit's §P8a line 327 is correct.** USO is the new fact: **five trading days at the start of
each month, changed from TEN on 2026-01-01.** §P8a line 328 listed USO under *"Do not assume"*;
it is sourced, and the regime change is the load-bearing half — **any fit of USO roll flow across
2026-01-01 is fitting two schedules as one, and the per-day fraction differs by a factor of two
either side of that date.** For the four ProShares funds the filing gives the index construction
and **no roll dates and no per-day fractions**; those are Bloomberg's methodology, which is not
on disk. **Q19 stays open for BOIL, KOLD, UCO and SCO.**

**Expense ratios**, which the fund model's `er` field leaves `None`: ProShares Geared Funds
**0.95%**, USO **0.45%**, UNG **0.60%** to $1bn and 0.50% above. Each is the management fee, not
the all-in ratio. **One filing contradiction recorded and not resolved:** UNG's Item 1 table gives
the breakpoint as $1,000,000,000 and its MD&A sentence as *"average net assets of $1,000,000 or
less"*.

**P9: nothing sourced.** All eight products (BetaPro HNU/HND/HOU/HOD via Global X Canada;
WisdomTree 3NGL/NGXL, 3NGS, 3OIL, 3OIS via WisdomTree Europe) are `status: not_sourced` with the
issuer site named. **Q14 and Q16 are open.** The US half took the round, and the BetaPro caveat
travels with the row: leverage is *"up to 2×" at manager discretion*, so a modelled 2× is an
assumption about a discretionary quantity.

**Gate 0 (line 534) does NOT clear.** All §3.2 facts sourced: **no**, ten holes. Holdings
point-in-time: **no** — one day exists and no history does. AUM point-in-time: **yes for the four
ProShares funds, no for UNG and USO.** Settlement windows: **yes** (D586). TAS available:
**symbology settled, data not pulled.**

---

## 5. The CME-side census — TAS is PRESENT and the tracker was wrong about options OI

**Metadata calls only. No batch job was submitted and nothing was downloaded, at any price.**

### TAS: deposit Q3 is answered — **present**

CME publishes Trade-at-Settlement as its own Globex products, **`CLT` for WTI crude and `NGT` for
Henry Hub natural gas**, under NYMEX/COMEX rules effective 14 September 2009, priced at the
settlement or within ten ticks of it
(`https://www.cmegroup.com/tools-information/lookups/advisories/market-regulation/NYMEX_COMEX_RA0909-4.html`,
read 2026-09-22). Probed on GLBX.MDP3 over 2016-01-04..08 and 2026-09-01..10:

| candidate | conclusion | evidence |
|---|---|---|
| **`CLT.FUT`** | **present** | 14 instruments in Jan 2016 (`CLTG6`, `CLTH6`, and TAS calendar spreads such as `CLTG6-CLTH6`), **60** in Sep 2026 |
| **`NGT.FUT`** | **present** | 88 instrument ids across the two windows |
| `CLTV6`, `CLTF7`, `NGTX6`, `NGTF7` | present | one instrument each — the outright spelling is `{root}{month}{year}` |
| `CLT`, `NGT` bare | absent | the API answers and resolves nothing: these are roots, not outrights |
| `CLT.OPT`, `NGT.OPT` | invalid_symbol | 422 `symbology_invalid_request` |
| `CL.TAS`, `NG.TAS` | invalid_symbol | 400 `symbology_invalid_symbol` — *"expected format: `[ROOT].OPT`, `[ROOT].FUT`, or `[ROOT].SPOT`"* |

**So the exploration's "0 TAS hits in 20.0 M definition records" was right about the archive and
wrong as a verdict about the venue.** The two pulls on disk used `{root}.FUT` parents for the 36
roots, and **`CLT` and `NGT` are their own roots** — nothing on disk was ever going to contain
them. The probe's verdict field distinguishes `present | absent | invalid_symbol | unresolved`
precisely so that an API refusal is not filed as a negative and a transport error is not filed as
anything: **an error is silence, not an answer.**

### Options: fifteen parents resolve, and **`CL.OPT` and `NG.OPT` do not exist**

| family | resolved parents | instruments across the two windows |
|---|---|---:|
| CL | `LO.OPT`, `LO1`–`LO5.OPT` | **59,845** on `LO` alone; 1,214 / 926 / 508 / 424 / 112 on the weeklies |
| NG | `ON.OPT`, `ON1`–`ON5.OPT`, `LN1`–`LN3.OPT` | **11,942** on `ON`; 247 / 248 / 248 / 240 / 112 and 254 / 262 / 249 |
| refused | `CL.OPT`, `NG.OPT`, `LN.OPT`, `WA.OPT` | 422 `symbology_invalid_request` — not families in this symbology |

**D581's lesson repeats exactly**: `LN.OPT` is refused while `LN1`–`LN3.OPT` resolve, so the
family is not where its name says it is. The quote's symbol list is **read out of the probe's
output at run time and never written by hand.**

### The quote — `submitted: false`

2016-01-01 → 2026-09-10, `stype_in="parent"`:

| block | schema | billable | USD |
|---|---|---:|---:|
| options (15 parents) | `definition` | **60.45 GB** | **0.00** |
| options | `statistics` | **117.76 GB** | **0.00** |
| options, last 12 months | `definition` / `statistics` | 6.23 / 20.26 GB | 0.00 / 0.00 |
| TAS (`CLT.FUT`, `NGT.FUT`) | `definition` | 0.30 GB | 0.00 |
| TAS | `statistics` | 0.26 GB | 0.00 |
| **TAS** | **`trades`** | **0.14 GB** | **3.17** |
| TAS, last 12 months | `trades` | 0.02 GB | 0.01 |
| **total** | | **178.91 GB** | **USD 3.17** |

**The one non-zero line is the one the deposit actually needs.** §13A.3 line 821 wants *"TAS
volume, aggressor split, premium ticks"*, which is `trades`, and `trades` is the only schema of
the five that prices above zero — **$3.17 for the full decade on both roots, $0.01 for the last
twelve months.** Everything else quotes at $0.00 **under the current CME Standard subscription,
whose free re-fetch window runs to roughly 2026-10-11**; a $0.00 quote today is not a $0.00 quote
in November, and that sentence is in the artifact beside the number. **Nothing was submitted:
`batch.submit_job` is not called, not imported and does not appear in the file.**

---

## 6. Deposit unit test 50, and the rule it composes

`usable_oi(oi_table, session)` in `build_fund_panel.py`, claimed by
`test_ledger_50_options_oi_is_joined_at_the_prior_days_publication`. **Two rules compose here and
they are not the same rule**, so the function names both:

- **D497's causality rule**, `usable_session`, **compiled out of
  `scripts/build_fut_open_interest.py` by AST rather than restated** — one definition of "when
  is this figure first usable" in the repository. Not imported: that module's body inserts
  `scripts/` on `sys.path` and imports a second runner, and D606 recorded what running a runner's
  module body costs. `ENTRY_MIN` is compiled with it and asserted to still be 10:00 ET, so a
  change at the source turns this red instead of drifting.
- **The deposit's extra conservatism**: test 50 says *"the prior day's published values only"*,
  which is a condition on the **publication day**, not on the usable day. A figure published at
  09:00 ET on the session itself is usable under D497 and **is excluded here**. A
  settlement-window study fills at 14:28–14:30 ET, where such a figure genuinely would be
  available, **so the two rules disagree, the deposit is stricter, and this function takes the
  stricter one and says so.**

The test runs on a **synthetic** OI table and its docstring says why: **no CL or NG options open
interest exists on this disk.** Four publications straddle both boundaries, and the join is
shown to move forward with the session rather than being a fixed filter.

---

## 7. Corrections owed to `DEPOSIT_INFRASTRUCTURE_TRACKER.md` (drafted; not edited here)

```diff
@@ lines 90-91 @@
 - NG and CL 1-minute bars for all held months ✓; trades with aggressor side ◐ (vault only); TAS
-  instrument symbology to check in the definition file ◐.
+  instruments checked: ABSENT under any symbol in the definition archive on disk, because both
+  pulls used `{root}.FUT` parents and CLT/NGT are their own roots. The D619 symbology probe
+  concludes PRESENT on GLBX.MDP3: `CLT.FUT` and `NGT.FUT` resolve (74 and 88 instrument ids over
+  2016-01 and 2026-09), quoted at 0.70 GB / USD 3.17 for definition + statistics + trades,
+  2016-2026; `CL.TAS` and `NG.TAS` are not symbols. Nothing pulled. ◐
@@ lines 95-96 @@
 - CFTC disaggregated COT ✓ (raw on disk), swap dissemination records ✗, NG and CL options open
-  interest ◐ (statistics schema held, not built), MBO ◐.
+  interest ✗ (NOT HELD: both Databento pulls used `.FUT` parents, and the 2026 definition file
+  decodes to security_type {FUT: 9,138,835, OOF: 1} — the "statistics schema held, not built"
+  line was wrong. Needs a pull; quoted in D619 at 178.21 GB / USD 0.00 across fifteen resolved
+  option parents, subscription window to ~2026-10-11), MBO ◐.
```

Two more rows the integrator may want to move: **"Point-in-time fund panel … ✗"** becomes ◐ (NAV,
shares and AUM for four of six; no holdings history, no UNG/USO), and **"Fund facts in
`SOURCES.md` … ✗"** becomes ◐ (30 of 40 facts).

---

## 8. What this record did NOT do

- **No P9 product was fetched.** Q14 and Q16 open, eight rows `not_sourced`.
- **No UNG or USO NAV, shares or holdings series exists.** The JS gate is the reason and no
  workaround was attempted.
- **No holdings history for any fund.** One day, 2026-09-18. The 10-Q/10-K Schedule of
  Investments was identified as the free backward route and was not parsed.
- **Nothing was downloaded from Databento.** Not the options, not the TAS, not at $0.00.
- **`data/recorder/jobs.json` was not edited** — D612 owns it this round; the split is drafted at
  §10 below.
- **No strategy return was computed and no bar from 2024-01-01 on was read for any return.**

---

## 9. Footer drafts for the integrator

### `docs/data-available.md` — a §4 paragraph

> **`fund_nav_daily` — the leveraged-commodity-ETF NAV panel (D619).** Daily `date, fund, nav,
> shares_out, aum, source, fetched_at` for **BOIL, KOLD, UCO and SCO**, 16,402 rows,
> 2008-11-24 → 2026-09-18 (BOIL from 2012-02-01, KOLD from 2011-10-04), from ProShares' own
> historical-NAV CSVs recorded through the D608 recorder. `shares_out` is in **shares**; the
> source publishes thousands to two decimals, so **every value is a multiple of 10 and 10 is the
> rounding unit** — the AUM identity is gated to half that unit, not to a basis point, and the
> naive 1 bp test passes on only 29.9% of BOIL's rows for that reason alone. **The series is
> fully back-adjusted for reverse splits**: BOIL's earliest rows read `NAV 8,000,000` against
> `0.50005` implied shares, no discontinuity exists to find, and nothing was rescaled — the 82
> rows whose published share count rounds to zero (BOIL, 2011-10-04..2012-01-31) are excluded and
> named. **Three columns the deposit asks for are ABSENT, not null:**
> `futures_notional_by_contract_month`, `swap_notional`, `published_at` — this source has none of
> them. **UNG and USO are not here** (USCF, not ProShares; their holdings page is JS-gated) and
> **no holdings history exists for any fund** — ProShares publishes today's only. The span runs
> through the deposit's sealed vault window and past the 2024-01-01 seal; the meta carries D604's
> holdout sentence and nothing here may score anything. Facts about the funds themselves —
> creation cut-offs, `lag_c`, roll schedules, fees — are in `data/fund_facts/SOURCES.md`.

### `CHANGELOG.md` — a bullet

> - **D619 — the fund panel, the fund-facts SOURCES and the CME-side census.**
>   `data/fixtures/fund_nav_daily.csv.gz` (16,402 rows, four ProShares funds, 2008–2026, five
>   gates, deterministic gzip) plus `data/fund_facts/{SOURCES.md,fund_facts.json}` (30 facts
>   sourced from three 10-Ks, 10 unknown and never inferred, a validator that raises, `lag_c = 0`
>   on all six funds, USO's roll **changed from ten days to five on 2026-01-01**, UCO **0.249
>   futures / 0.751 swap** on 2026-09-18 across three non-front months). Census: **TAS is present
>   on GLBX.MDP3** under `CLT.FUT`/`NGT.FUT` (deposit Q3 answered), **CL/NG options OI is not on
>   disk at all** (both pulls used `.FUT` parents — the tracker's "statistics schema held" line was
>   wrong), fifteen option parents resolve and `CL.OPT`/`NG.OPT` do not exist. Quoted at 178.91 GB
>   / **USD 3.17**, all of it the TAS `trades` schema; **nothing submitted, nothing downloaded**.
>   Deposit ledger test 50 claimed. 50 tests.

---

## 10. Drafted `data/recorder/jobs.json` split — the `fund_snapshot` job becomes four

**Not applied here.** D612 owns `jobs.json` this round. The existing `fund_snapshot` job
(`needs_source`, deposit job 1) is replaced by the four below: two are now **ready** with URLs
copied from this record's own verified fetches, and two keep `needs_source` with the reason named.

```json
[
 {
  "name": "proshares_nav",
  "cadence": "daily",
  "window_et": ["17:00", "23:00"],
  "source_url": "https://accounts.profunds.com/etfdata/ByFund/BOIL-historical_nav.csv",
  "parser": "scripts.build_fund_panel.read_nav_csv",
  "status": "ready",
  "window_basis": "declared here (D619): an evening band, after the deposit's 'after each fund's publication'. ProShares publishes no NAV posting clock that this repository has sourced, so the band is operational and is not to be read as a release time.",
  "frequency": "Daily, after each fund's publication",
  "content": "NAV, shares outstanding and AUM for BOIL, KOLD, UCO and SCO (the whole history, re-fetched each run)",
  "ext": "csv",
  "note": "Deposit job 1, the US NAV half. URL template verified in D619 by fetching all four; the UCO form is the 'Historical NAV' link printed on the UCO fund page. THE KEY IS THE TICKER and this row carries BOIL's URL only because a Job holds ONE source_url -- scripts/fetch_fund_nav.py substitutes the other three from PROSHARES_FUNDS. UNG and USO 404 on this host: they are USCF funds (see uscf_fund_snapshot). The file is the FULL history every time, so a missed day is recoverable and a gap line here means the host stopped, not that data was lost."
 },
 {
  "name": "proshares_holdings",
  "cadence": "daily",
  "window_et": ["17:00", "23:00"],
  "source_url": "https://www.proshares.com/our-etfs/leveraged-and-inverse/boil",
  "parser": "scripts.fetch_fund_holdings.parse_holdings",
  "status": "ready",
  "window_basis": "declared here (D619): an evening band. The page states a holdings AS-OF date and no publication clock, so the band is operational.",
  "frequency": "Daily, after each fund's publication",
  "content": "Holdings by contract month with futures and swap notional, for BOIL, KOLD, UCO and SCO",
  "ext": "html",
  "note": "Deposit job 1, the holdings half, and THE REASON THE RECORDER EXISTS: ProShares publishes ONE day of holdings and no archive (six URL patterns 404), so this series can only be started, never back-filled -- which is deposit 3.1 line 70, 'Never back-fill today's composition across history'. Key is the ticker; the slug is the lowercase ticker. MUST BE FETCHED WITH Accept: text/html -- the recorder's default Accept returns 7.8 KB of CMS JSON with no holdings (D619), which is why scripts/fetch_fund_holdings.py builds its own request. The parse RAISES on a missing as-of date or a missing futures row."
 },
 {
  "name": "uscf_fund_snapshot",
  "cadence": "daily",
  "window_et": ["17:00", "23:00"],
  "source_url": null,
  "parser": null,
  "status": "needs_source",
  "window_basis": "declared here (D619): the same evening band as the ProShares jobs, for when a source exists.",
  "frequency": "Daily, after each fund's publication",
  "content": "NAV, units outstanding and holdings for UNG and USO",
  "ext": "json",
  "note": "Deposit job 1, the USCF half. https://www.uscfinvestments.com/holdings/{uso,ung} returns HTTP 200 and THE TABLE IS NOT IN THE RESPONSE: it is loaded by JavaScript from assets/javascript/api_key.php. https://www.uscfinvestments.com/uso carries no NAV or CSV link, and accounts.profunds.com 404s for both tickers. No URL is invented. The free historical route is the Schedule of Investments in the 10-Q/10-K (CIK 0001327068 for USO, 0001376227 for UNG), 40-90 days late; D619 records the filings themselves under the job sec_fund_filings."
 },
 {
  "name": "p9_snapshot",
  "cadence": "daily",
  "window_et": ["17:00", "23:00"],
  "source_url": null,
  "parser": null,
  "status": "needs_source",
  "window_basis": "declared here (D619): an evening band in ET for products listed in Toronto, London, Frankfurt and Milan -- whose own publication clocks are part of Q14 and are not sourced.",
  "frequency": "Daily, after each fund's publication",
  "content": "NAV, units or notes outstanding and effective leverage for BetaPro HNU/HND/HOU/HOD and WisdomTree 3NGL/NGXL, 3NGS, 3OIL/3OIS",
  "ext": "json",
  "note": "Deposit job 1, the P9 half, and deposit Q14 is the open question: 'For each P9 product: daily NAV, units or notes outstanding, and actual exposure/leverage history. Where published, and how far back?' D619 fetched NOTHING for any P9 product and lists all eight as not_sourced in data/fund_facts/fund_facts.json with the issuer sites to look at (Global X Canada for BetaPro, WisdomTree Europe). BetaPro leverage is 'up to 2x' at manager discretion (deposit 3.1b line 77), so a stated 2x is an assumption and not a rounding; Q16 asks for the WisdomTree restrike wording."
 }
]
```

The `tas_summary` job (deposit job 3, `needs_key`) keeps its status — it is a purchase, not a
missing URL — and its `note` should gain: *"D619 settles the symbology half of Q3: `CLT.FUT` and
`NGT.FUT` resolve on GLBX.MDP3 back to at least 2016-01-04, quoted at USD 3.17 for the `trades`
schema over 2016–2026. Nothing pulled."*

## Consequences

**What is now available that was not.** A 16,402-row NAV panel for four of the deposit's six
funds; the first `f_fut` measurement anyone here has made, and it is 0.249 on UCO; every
creation cut-off and `lag_c`; USO's roll-period regime change; and an answer to Q3.

**What is now known to be harder than the tracker said.** CL/NG options open interest is **not on
disk**, and getting it is a 178 GB pull inside a subscription window that closes in about three
weeks. Holdings history does not exist for free at daily frequency for any of the six.

**The sharpest single number is 0.249.** If UCO's swap share is typical rather than exceptional,
the deposit's central object — predicted rebalance flow reaching the CME order book — is a
fraction of the fund's notional, and which fraction is unobservable except one day at a time,
forward, from today.
