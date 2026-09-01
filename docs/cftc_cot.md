# CFTC Commitments of Traders: the positioning provider

**The only source in the futures data layer that may be committed to this
repository**, and the free first rung of
[the data-purchase proposal's ladder](research/futures-data/data-purchase-proposal.md).

Fetcher: [`scripts/fetch_cftc_cot.py`](../scripts/fetch_cftc_cot.py) ·
Fixture: `data/fixtures/cftc_cot_raw.csv.gz` · Gates:
[`tests/unit/test_cftc_cot_fixture.py`](../tests/unit/test_cftc_cot_fixture.py)

---

## Why this provider at all

The CFTC requires every trader holding a position above a reporting threshold to
declare it, and publishes the aggregate weekly, **split by trader type**, for every
US futures market.

**That is not a proxy for institutional positioning. It is the official
measurement of it**, produced under legal compulsion rather than inferred from a
tape, and it runs back to **1986**.

Every other candidate in [the twelve-lane free-data search](research/futures-data/00-SYNTHESIS.md)
was a price source. **This one surfaced in none of them, because they were all
looking for bars.**

## Licence — the reason this fixture is committed

**COT is a work of the United States government and is in the public domain.**

That is not a detail. Every CME-derived product in this project is
exchange-licensed and forbidden from redistribution, which is why `.gitignore`
carries `data/raw/databento/` and why the pattern elsewhere is gitignored cache
plus committed re-fetch script. **COT has no such constraint, so the derived
fixture lives in the repo like any Alpha Vantage fixture.** The raw cache under
`data/raw/cftc/` is still gitignored, per D191 — cache the raw, commit the derived.

## The endpoint

Socrata open data. **No key, no account, no registration.** An app token exists and
only raises throttling limits; none is used, because the whole job is ~84 requests.

```
https://publicreporting.cftc.gov/resource/{dataset}.json
```

| dataset | id | covers | from |
|---|---|---|---|
| **Legacy, futures only** | `6dca-aqww` | every market | **1986-01-15** |
| **Disaggregated, futures only** | `72hh-3qpy` | physical commodities | 2006-06-13 |
| **TFF, futures only** | `gpe5-46if` | financial contracts | 2006-06-13 |

**The futures-AND-options combined variants exist** — `jun7-fc8e`, `kh3c-gbw2`,
`yw9f-hn96` — **and are deliberately not used.** An options-inclusive position is
not a futures position, and mixing them would make `open_interest` mean two
different things depending on the row.

SoQL is supported and used: `$select`, `$where ... like '%X%'`, `$group`,
`$order`, `$limit` (50,000 ceiling for JSON), `$offset`.

## What the documentation does not state — measured

**The published start dates are wrong, in our favour.** The CFTC's own page says
disaggregated begins September 2009 and TFF begins 2010-07-20. **Both datasets
actually serve back to 2006-06-13.** Recorded as a discrepancy rather than
silently banked, because a provider fact that stops being checkable stops being a
fact.

**The report date is not always a Tuesday**, and the release convention that
depends on it is not a flat offset. Measured across the full 1986–2026 span:

| era | report weekday |
|---|---|
| 1986 | **46.8% Friday**, 16.2% Monday, 16.2% Wednesday, 12.3% Tuesday |
| 1992 | 51.6% Tuesday — the schedule is changing |
| **1993 onward** | **Tuesday on 98–100% of weeks** |

The post-1993 exceptions are **holiday shifts**: `2007-01-03` is a Wednesday
because 2007-01-02 was the National Day of Mourning for President Ford and the
markets were closed. **Four Friday-dated reports survive after 1993** —
1997-12-19, 2001-12-21, 2001-12-28, 2003-02-14 — all year-end anomalies, and all
pinned by name in the tests so a fifth one fails loudly.

**Contracts enter the report far later than they start trading.** A contract
appears only once it has enough *reportable* traders:

| contract | listed | first COT report | lag |
|---|---|---|---|
| MES | 2019-05-06 | **2020-07-28** | 1.2 y |
| MNQ | 2019-05-06 | 2020-08-04 | 1.2 y |
| M2K | 2019-05-06 | **2021-11-30** | 2.6 y |
| MYM | 2019-05-06 | **2022-07-26** | 3.2 y |
| MSI / MHG | 2022 | **2026-01** | ~4 y |

## A correction worth keeping

**The open-interest identity is not `OI == sum(long)`.** That was the first
version of the gate and it failed on **94% of rows**.

A **spread** position is one long *and* one short held by the same trader: it sits
inside open interest and outside the directional columns. The identity is

```
open_interest == sum(long) + sum(spread) == sum(short) + sum(spread)
```

and it then holds on **55,661 of 55,661 checked rows, exactly**. Both sides are
checked, because requiring both is strictly stronger — a transposition preserving
one side would still break the other. **It is the cheapest available proof that
every column landed in its right slot.**

## The provider's own typos are part of the contract

Read off live records, not assumed:

```
swap__positions_short_all       DOUBLE underscore
swap__positions_spread_all      DOUBLE underscore
noncomm_postions_spread_all     "postions"
```

**They look like defects and someone will eventually correct them.** If that
happens our columns go silently empty rather than erroring, so the exact spellings
are asserted by test — along with an assertion that the *plausible corrected*
spellings are **not** what we ask for.

## Three reports, and they are not comparable

| family | categories |
|---|---|
| **Legacy** | commercial · non-commercial · non-reportable |
| **Disaggregated** | producer-merchant · swap-dealer · managed-money · other-reportable · non-reportable |
| **TFF** | dealer · asset-manager · leveraged-money · other-reportable · non-reportable |

**A financial contract has no producer-merchant and a physical has no
asset-manager.** The fixture is **tidy** — one row per `(report, category)` — and
carries `family` on every row, so a study cannot average categories that do not
mean the same thing. Legacy is fetched for every symbol as the long-history spine.

## Why the symbol map is derived and never typed

`--map` resolves each symbol against the live API and **refuses ambiguity**,
because a hand-typed contract code is a silent wrong answer: it returns a full,
plausible, well-formed series for the wrong market.

**Two traps justify it, and the second is worse than the first.**

**`%CRUDE OIL%` matches seven contracts:**

| code | name |
|---|---|
| **067411** | **CRUDE OIL, LIGHT SWEET-WTI** ← the one |
| 06741Q | WTI CRUDE OIL 1ST LINE |
| 067655 | E-MINI CRUDE OIL, LIGHT SWEET |
| 06765A / 06765I | WTI FINANCIAL / WTI CRUDE OIL FINANCIAL |
| 06765G | DUBAI CRUDE OIL CALENDAR |
| 067DU1 | OMAN CRUDE OIL |

**`%NATURAL GAS%` matches the main contract not at all.** The CFTC abbreviates, so
the pattern returns `E-MINI NATURAL GAS` and `NATURAL GAS INDEX: EP SAN JUAN` —
**two plausible wrong answers and no right one.** The liquid NYMEX Henry Hub
contract is **`023651` "NAT GAS NYME"**.

Resolution rules, all loud:

```
exact given and found      -> use it
exact given and MISSING    -> HARD FAIL, the provider renamed something
no exact, one candidate    -> use it, and PRINT it for promotion to exact
no exact, many candidates  -> HARD FAIL, listing every candidate
```

## The micros have their own series — the finding

**MES `13874U`, MNQ `209747`, M2K `239747`, MYM `124608`, MICRO GOLD `088695`,
MICRO SILVER `084694`, MICRO COPPER `085699`** — each reported separately from its
full-size sibling, with the full trader-category breakdown and its own
`nonrept_positions_*` small-trader column.

**The proposal costs rung 2 — separating retail from institutional flow — at
$14.28 of Databento minute bars, inferring the split from contract choice. The
CFTC classifies the traders directly, weekly, for nothing.**

It does not replace the paid version: weekly resolution cannot support an intraday
rule, and the inception lags above mean only **ES/MES and NQ/MNQ carry ~6 years**,
with M2K ~4.7, MYM ~4, and the metal micros unusable. **But the premise can be
falsified for £0 before any purchase.**

## Release lag is data, not a footnote

Surveyed at **Tuesday's close**, published **Friday 15:30 ET**. A study keying on
`report_date` reads Tuesday's positions on Tuesday and is **three days of
look-ahead** — exactly what [R9](RULES.md) forbids of a conditioning variable.

`release_date_nominal` is therefore **the Friday of the report's week**, not a flat
+3 days: the survey day shifts on holidays, and +3 from a Wednesday report would
land on a Saturday. A Friday-dated report is pushed to the **following** Friday,
since a report cannot be published before it is surveyed and **erring late is the
only safe direction**.

**Before 1993 the field is EMPTY.** There was no weekly schedule, so there is no
convention to apply, and a fabricated release date would look usable.

**Two limits stated rather than buried:** publication is **suspended during
government shutdowns and released in batches afterwards** — 2018-12 to 2019-02 and
2013-10 — so the nominal date is optimistic across those windows; and a study
should carry margin regardless.

## Provenance traps

**`6E` predates the euro.** Legacy rows run from 1986-01-15 under the name
`EURO FX`, but **the euro did not exist until 1999-01-01** and continuous coverage
begins exactly **1999-01-05**, after a 644-week gap. Code `099741` carries a
back-labelled predecessor. **Use 1999-01-05 onward.**

**`RTY` spans a venue change.** Not pre-inception — but the Russell 2000 E-mini
traded on **ICE between 2008 and 2017** before moving to CME, so pre-2017 rows
describe a contract on a different exchange from the one the prop track would
trade.

## This project's settings, and why each

| setting | value | why |
|---|---|---|
| pacing | **30 req/min** | far under any published limit; the whole job is ~84 requests |
| page size | `$limit=50000` | Socrata's JSON ceiling; every series fits inside it |
| datasets | futures-**only** | combined would change what `open_interest` means |
| shape | **tidy** | one row per `(report, category)`; `family` on every row |
| cache | `data/raw/cftc/` | gitignored, D191 |
| gzip mtime | **0** | otherwise identical rebuilds hash differently — D252's defect |

## Rate limits

Socrata throttles unauthenticated clients by IP on a rolling window. **Not
documented as a specific number**, and never approached here. An app token would
raise it and is unnecessary.

## Still unknown

- **The exact pre-1993 publication schedule.** Reports exist from 1986 but the
  cadence and release lag are not documented anywhere reachable. This is why
  `release_date_nominal` is empty there rather than guessed.
- **Whether the 644-week `6E` gap hides a documented contract substitution** or is
  simply sparse early reporting under a reused code.
- **Whether disaggregated/TFF back-history to 2006 is authoritative** or a
  retrospective reconstruction by the CFTC.

## See also

- [`docs/research/futures-data/data-purchase-proposal.md`](research/futures-data/data-purchase-proposal.md) — §7.5, the ladder this is rung 1 of
- [`docs/alpha_vantage_api.md`](alpha_vantage_api.md) — the equity provider, same document shape
- [`docs/databento_api.md`](databento_api.md) — the futures bar provider, not yet purchased
