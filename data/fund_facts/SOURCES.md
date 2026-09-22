# Fund facts — the settlement-flow deposit's §3.2 and §P8a, sourced — D619

**One entry per fact: the filing, the accession, the access time, and the sentence the issuer
wrote.** Every quoted sentence below was read out of the RAW response bytes cached under
`data/raw/recorder/sec_fund_filings/` (gitignored, unmodified, named with `fetched_at`), not out
of a summary — the discipline [`data/settlement_flow/SOURCES.md`](../settlement_flow/SOURCES.md)
(D586) states, for the same reason: this whole table turns on exact wording and clock times.

The machine-readable twin is [`fund_facts.json`](fund_facts.json), validated by
`validate_fund_facts` in [`scripts/fetch_fund_facts.py`](../../scripts/fetch_fund_facts.py),
which **raises** on a missing key, a `sourced` fact with no source, an `unknown` fact carrying a
value, a `lag_c` outside {0, 1, null}, or a quote over fifteen words.

**What the deposit asked for**, §3.2 lines 86–92, verbatim:

> For each fund, record in `SOURCES.md`:
> - Split of exposure between futures and swaps, over time.
> - **Creation/redemption order cut-off time** and **execution timing**: whether the fund
>   transacts creations the same day at settlement or the next day (the lag parameter
>   `lag_c` ∈ {0, 1}).
> - Whether the fund states it uses settlement-price or TAS execution for rebalancing.
> - Index roll schedule (dates and fractions rolled per day).

**Where it stands: 30 facts sourced, 10 unknown, across six funds** (five required facts plus
`nav_strike_basis` and, for the ProShares four, `index_construction`). The eight P9 products are
**not sourced at all** and are listed at the foot with the issuer sites to look at. Gate 0
(§ line 534: *"All Section 3.2 facts sourced"*) is therefore **NOT cleared**, and the ten holes
are named rather than smoothed over.

---

## 0. The sources, and the two that do not exist

| issuer | funds | route | what it gives |
|---|---|---|---|
| ProShares Trust II, CIK **0001415311** | BOIL, KOLD, UCO, SCO | 10-K `0001193125-26-077441`, filed 2026-02-26 for FY2025, and the live fund page | cut-off and NAV clocks, fee, index construction, the year-end Schedule of Investments; the live page gives ONE day of holdings |
| United States Oil Fund LP, CIK **0001327068** | USO | 10-K `0001104659-26-021501`, filed 2026-02-27 | cut-off, execution, roll schedule, fee |
| United States Natural Gas Fund LP, CIK **0001376227** | UNG | 10-K `0001104659-26-021507`, filed 2026-02-27 | cut-off, execution, roll schedule and its daily fractions, fee |

**The ProShares CIK is confirmed, not assumed.** Two entities' names match. `0001415311`'s
submissions index lists the tickers `AGQ, BOIL, EUO, GLL, KOLD, SCO, SVXY, UCO, UGL, ULE, UVXY,
VIXM, VIXY, YCL, YCS, ZSL`; **ProShares Trust III, CIK `0002019448`, has filed only `DRS`, `S-1`
and `RW`** and files for none of these four.

**N-PORT does not apply and that is not a gap in the search.** All six funds are commodity pools,
not '40-Act funds. ProShares Trust II files `424B3, EFFECT, 8-K, CORRESP, UPLOAD, 10-Q, POS AM,
S-1/A, S-1, FWP`; the two USCF partnerships file the same commodity-pool set. **Zero N-PORT
between them.** The free historical holdings route is therefore the **Schedule of Investments
inside the quarterly 10-Q and the annual 10-K**, at a 40–90 day lag, and there is no monthly
position file to be had at any price from the SEC.

**Two routes that were tried and do not work**, recorded so nobody spends the hour again:

| route | result |
|---|---|
| `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=…&type=10-K&output=atom` | **HTTP 503 `text/html`**, from `urllib.request.urlopen` on 2026-09-21, on three header combinations — the repository's SEC user agent alone; that plus `Accept-Encoding: gzip, deflate`; and that plus `Accept: application/atom+xml,text/xml,*/*` and an explicit `Host`. Four attempts each. `https://data.sec.gov/submissions/CIK{cik}.json` answers **HTTP 200 to the same headers** and carries the same index, so that is the route used. |
| `https://www.uscfinvestments.com/holdings/{uso,ung}` | HTTP 200, and **the table is not in the response**: it is loaded by JavaScript from `assets/javascript/api_key.php`. `https://www.uscfinvestments.com/uso` carries no NAV or CSV link. **No URL is recorded as ready for either fund** — a URL is never invented (D608's first rule). |

**And one route that does:** `https://accounts.profunds.com/etfdata/ByFund/{BOIL,KOLD,UCO,SCO}-historical_nav.csv`,
HTTP 200 `text/csv`, 2008/2011 to 2026-09-18. The UCO form of that link is printed on the UCO
fund page as its "Historical NAV" download; the other three are the same template. **UNG and USO
404 on that host** — they are not ProShares funds.

---

## 1. Split of exposure between futures and swaps (§3.2 line 89)

**Sourced for the four ProShares funds at ONE POINT IN TIME, 2026-09-18, and unknown over time
for all six.** No issuer publishes a futures/swap split as a series; ProShares publishes today's
and nothing else, and USCF's equivalent is behind the JavaScript gate above.

Measured from `data/raw/recorder/proshares_holdings/*__20260921T2317*.html`, parsed by
`scripts/fetch_fund_holdings.py`, holdings **as of 9/18/2026**:

| fund | futures share of derivative exposure | contract months held | lines |
|---|---:|---|---|
| **BOIL** | **1.000** | NOV26 | 1 futures, +25,857 contracts, $786,828,510 |
| **KOLD** | **1.000** | NOV26 | 1 futures, −7,042 contracts, −$214,288,060 |
| **UCO** | **0.249** | DEC26, JUN27, DEC27 | 3 futures ($218,081,730) against **4 swap lines** ($657,673,266) |
| **SCO** | **1.000** | DEC26, JUN27, DEC27 | 3 futures, −7,822 / −8,883 / −9,286 contracts |

> "For swap agreements, a positive amount represents \"long\" exposure to the benchmark index"
>
> — ProShares Trust II 10-K, `0001193125-26-077441`, Notes to Financial Statements, Schedules of
> Investments footnotes · fetched 2026-09-21T23:24:07Z

**Two things in that table matter more than the fact that it was sourced.**

1. **UCO is three quarters swap and SCO is zero.** A +2× fund and its −2× partner, on the same
   index, on the same day, hedge differently. **Three quarters of UCO's rebalance flow does not
   reach the CME order book as UCO's order at all** — it reaches it, if at all, as the swap
   counterparty's hedge, at the counterparty's timing. Any flow model that maps UCO's daily
   rebalance onto CME futures one-for-one is wrong by a factor of four on 2026-09-18, and the
   factor is not constant, because nothing published says it is.
2. **UCO and SCO hold DEC26, JUN27 and DEC27 — not the front month.** That is the Bloomberg
   Commodity Balanced WTI index's three schedules showing through (§3 below), and it is deposit
   §3.1 line 69 (*"Contract months matter … which may **not** be the front month"*) made
   concrete.

**Unknown for UNG and USO.** Both filings name futures and "Other … Related Investments" without
a split; neither issuer publishes one that a GET can read.

---

## 2. Creation/redemption cut-off, execution timing and `lag_c` (§3.2 line 90)

**Sourced for all six. `lag_c = 0` for all six**, and the cut-off clocks differ by two hours
across the two issuers.

| fund | create/redeem cut-off | NAV strike | `lag_c` |
|---|---|---|---:|
| BOIL, KOLD, UCO, SCO | **2:00 p.m. ET** | **2:30 p.m. ET** | **0** |
| UNG, USO | **12:00 p.m. ET** (or the earlier NYSE Arca close) | futures at the 2:30 p.m. ET settlement; basket NAV at **4:00 p.m. ET** | **0** |

> "the day on which SEI receives a valid purchase order is the purchase order date"
>
> — ProShares Trust II 10-K, Item 1, Creation and Redemption of Shares · fetched 2026-09-21T23:24:07Z

and, from the same filing's *Final Net Asset Value for Fiscal Period* table, the rows
`Ultra Bloomberg Crude Oil | 2:00 p.m. | 2:30 p.m.`,
`Ultra Bloomberg Natural Gas | 2:00 p.m. | 2:30 p.m.`,
`UltraShort Bloomberg Crude Oil | 2:00 p.m. | 2:30 p.m.` and
`UltraShort Bloomberg Natural Gas | 2:00 p.m. | 2:30 p.m.`.

> "Purchase orders must be placed by 12:00 p.m. New York time"
>
> — USO 10-K `0001104659-26-021501` and UNG 10-K `0001104659-26-021507`, Item 1, Creation
> Procedures · fetched 2026-09-21T23:24:08Z and 23:24:09Z

**Why the ProShares clock is the interesting one.** Its **2:30 p.m. ET NAV strike is the CLOSE of
the NYMEX energy settlement window, 14:28:00–14:30:00 ET** (D586, sourced to SER-4867 and the CME
settlement-time page). So the cut-off at 2:00 p.m. leaves **28 minutes** between the last order a
fund can accept and the first second of the window its NAV will be struck in — which is exactly
the interval the deposit's `Q_rem` is about. **The USCF funds' cut-off is 12:00 p.m., two and a
half hours ahead of the window**, and their basket NAV is struck an hour and a half AFTER it.
Three different clocks, one flow model: a study that treats the six funds as one cohort is
averaging over a 2½-hour spread in when the order is known.

---

## 3. Settlement-price or TAS execution for rebalancing (§3.2 line 91; deposit Q2)

**Sourced for UNG and USO. Unknown for the four ProShares funds.** And one measurement applies to
all three filings:

> **The token `TAS` and the phrase `Trade at Settlement` appear ZERO times** in the ProShares
> Trust II 10-K (1,151,333 characters of extracted text), the USO 10-K (542,935) and the UNG 10-K
> (516,020).

That is evidence on Q2 and **it is not a proof of absence** — a fund can transact a TAS instrument
without naming it in a 10-K, and an EFP or a block trade is a third possibility the filings do
name. It is recorded as what it is: three documents that had every reason to mention TAS and do
not.

> "at the closing settlement price for such contracts on the purchase order date"
>
> — USO 10-K, Item 1, Creation Procedures · fetched 2026-09-21T23:24:08Z

> "at, or as close as possible to, the end of the day settlement price"
>
> — UNG 10-K, Item 7 MD&A · fetched 2026-09-21T23:24:09Z

**Read the USO sentence carefully, because it moves the flow off the screen.** The obligation is
the *Authorized Participant's*, "if required by USCF in its sole discretion", to "enter into or
arrange for a block trade, an exchange for physical or exchange for swap, or any other OTC energy
transaction". So creation-related futures flow can arrive at the exchange as an **EFP or a block
at the settlement price** rather than as an order in the settlement window — priced by the window
without ever being *in* it.

**For ProShares the question is simply not answered by the filing.** It states the valuation basis
(§5) and nothing about execution. `fund_facts.json` records `rebalance_execution` as
`status: "unknown"`, `value: null` — deposit §P8a line 328, *"Do not assume."*

---

## 4. Index roll schedule (§3.2 line 92, §P8a lines 326–329; deposit Q19)

**Sourced in full for UNG. Sourced for USO with a regime change. Unknown for BOIL, KOLD, UCO and
SCO.**

### UNG — the deposit's own statement, re-cited to its filing

> "during a four-day period beginning two weeks from expiration of the contract"
>
> — UNG 10-K, Item 1, the Benchmark Futures Contract · fetched 2026-09-21T23:24:09Z

and the filing spells out the fractions the deposit quotes at §P8a line 327: day 1 is 75% near
month plus 25% next, day 2 is 50/50, day 3 is 25/75, and on day 4 the next month **is** the
benchmark. **The deposit's "four days, 25% per day, beginning two weeks before expiry" is correct
and is now attached to an accession number.** The only part of the deposit's sentence the filing
does not carry is the issuer's CSV of anticipated roll dates, which is a website artefact.

### USO — five days, and **it was ten until 2026-01-01**

> "USO will roll its positions during the first 5 trading days"
>
> — USO 10-K, Item 1, the Benchmark Oil Futures Contract · fetched 2026-09-21T23:24:08Z

The filing states, in the next breath, that **before 1 January 2026 USO rolled over a ten-day
period**, and that the change altered neither the benchmark nor the investment objective. §P8a
line 328 listed USO under *"to source from each prospectus … Do not assume"*; it is sourced now,
**and the regime change is the load-bearing half.** Any study that fits USO roll flow across
2026-01-01 is fitting two schedules as one, and the per-day fraction differs by a factor of two
on either side of that date. The filing gives the number of days and **not** the daily fractions.

### BOIL, KOLD, UCO, SCO — unknown, and what the filing does give

The 10-K describes the indices and gives **no roll dates and no per-day fractions**. What it does
give is the construction, which explains the contract months in §1:

> "a monthly roll schedule two months beyond the nearby contract"
>
> — ProShares Trust II 10-K, Item 1, Bloomberg Commodity Balanced WTI Crude Oil Index · fetched
> 2026-09-21T23:24:07Z

in full, the index tracks three separate WTI schedules in equal thirds — one monthly two months
beyond the nearby, one on a June annual roll, one on a December annual roll — with the weights
reset semi-annually in March and September on the close of the first business day. **The
2026-09-18 holdings are exactly that: DEC26, JUN27, DEC27.**

> "a rolling position in natural gas futures contracts traded on the NYMEX"
>
> — same filing, Bloomberg Natural Gas Subindex · fetched 2026-09-21T23:24:07Z

**Deposit Q19 stays open for all four**, and where the answer lives is now specific: Bloomberg's
own Commodity Index methodology, which is not on disk and was not fetched.

---

## 5. NAV strike basis (deposit Q10) and the expense ratio

**NAV strike basis, sourced for all six.**

> "based upon the settlement price (for the VIX Funds and the Commodity Index Funds)"
>
> — ProShares Trust II 10-K, Notes to Financial Statements, valuation · fetched 2026-09-21T23:24:07Z

> "the settlement price of Oil Futures Contracts at 2:30 p.m. Eastern Time"
>
> — USO 10-K, Item 1, indicative fund value · fetched 2026-09-21T23:24:08Z

The USO filing adds that **ICE Futures also sets its settlement as of 2:30 p.m. ET**, so a USO
holding both venues strikes on two settlements at one clock.

**Expense ratio, sourced for all six.** `Fund` in `src/backtest_framework/…` carries `er = None`
for these names, and these are the numbers that fill it:

| fund | management fee | quote |
|---|---:|---|
| BOIL, KOLD, UCO, SCO | **0.95%** | "an amount equal to 0.95% per annum of its average daily NAV" |
| USO | **0.45%** | "a management fee based on 0.45% per annum on its average daily total net assets" |
| UNG | **0.60%** to $1bn, 0.50% above | "First $1,000,000,000 0.60% of NAV After the first $1,000,000,000 0.50% of NAV" |

Each is the **management fee**, not the all-in ratio: ProShares' own financial highlights say
*"The expense ratio would be 0.95% … if brokerage commissions and futures account fees were
excluded"*, and both USCF funds add roughly 0.10% of average net assets in brokerage at $3.50 per
buy or sell.

**One internal contradiction, recorded and not resolved.** UNG's Item 1 table gives the breakpoint
as **$1,000,000,000** and its MD&A sentence gives it as *"average net assets of $1,000,000 or
less"*. The table is taken as the term; the disagreement belongs to the filing, not to this file.

---

## 6. P9 — the eight non-US products, **none sourced**

Deposit §3.1b line 74: *"All figures are indicative and must be re-sourced point-in-time."*
**Nothing was fetched for any P9 product in D619** — the US half took the round — so all eight
are `status: not_sourced` in `fund_facts.json`, with where to look:

| product | listing | where to look |
|---|---|---|
| BetaPro HNU / HND (natural gas ±2×) | TSX (CAD) | <https://www.globalx.ca/> |
| BetaPro HOU / HOD (crude ±2×) | TSX (CAD) | <https://www.globalx.ca/> |
| WisdomTree 3NGL / NGXL (NG +3×) | LSE, Xetra, Borsa Italiana | <https://www.wisdomtree.eu/> |
| WisdomTree 3NGS (NG −3×) | as above | <https://www.wisdomtree.eu/> — existence itself is to verify |
| WisdomTree 3OIL / 3OIS (WTI ±3×) | as above | <https://www.wisdomtree.eu/> |

**Deposit Q14** (*"daily NAV, units or notes outstanding, and actual exposure/leverage history.
Where published, and how far back?"*) and **Q16** (the restrike wording) are both open. The
BetaPro caveat at §3.1b line 77 is the one to carry: leverage is *"up to 2×" at manager
discretion*, so a modelled 2× is an assumption about a discretionary quantity, not a rounding.

---

## 7. What Gate 0 still needs

§ line 534: *"All Section 3.2 facts sourced; holdings and AUM point-in-time; settlement windows
verified with effective dates; TAS data available (or P5/P6 formally disabled). **Fail → STOP**."*

| clause | state after D619 |
|---|---|
| all §3.2 facts sourced | **NO.** 30 sourced, 10 unknown. The futures/swap split over TIME is unavailable for all six; the roll schedule is unknown for the four ProShares funds; the rebalance execution is unknown for the four ProShares funds. |
| holdings point-in-time | **NO.** One day exists (2026-09-18, the four ProShares funds) and no history does. The forward recorder is how a series starts; the 10-Q/10-K Schedule of Investments is the only free backward route, quarterly and 40–90 days late. |
| AUM point-in-time | **YES for the four ProShares funds** — `data/fixtures/fund_nav_daily.csv.gz`, 16,402 rows, 2008-11-24 to 2026-09-18. **NO for UNG and USO.** |
| settlement windows verified with effective dates | **YES**, D586. |
| TAS data available | **Symbology settled, data not pulled.** `CLT.FUT` and `NGT.FUT` resolve on GLBX.MDP3 (74 and 88 instrument ids across the two probe windows); `data/energy_options_pull_quote.json` prices the history. Nothing is downloaded — the principal's decision of 2026-09-22 was quote only. |
