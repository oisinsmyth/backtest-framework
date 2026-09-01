# Databento: the futures bar provider

**Nothing has been purchased.** This is the reference for a client that exists,
is tested, and is structurally unable to spend money until someone decides to
let it.

Client: [`scripts/fetch_databento.py`](../scripts/fetch_databento.py) ·
Tests: [`tests/unit/test_databento_client.py`](../tests/unit/test_databento_client.py) ·
Costing: [the purchase proposal](research/futures-data/data-purchase-proposal.md)

---

## How this reference was established, and why that matters

**Databento's documentation site is JavaScript-rendered and defeats plain
fetching** — it truncates under `WebFetch` and two separate browser routes failed
outright. So the surface below was **not** read off the docs site.

It comes from **three independent sources that agree**:

| tag | source |
|---|---|
| **[PY]** | `databento-python` client source, `main` |
| **[RS]** | `databento-rs` client source — **including its wiremock tests, which assert exact paths, methods and parameters** |
| **[DOC]** | the official docs served as plain text via Context7, including verbatim `curl` examples and response JSON |

**Every fact below is tagged VERIFIED or INFERRED.** That distinction is the point
of the document: a confidently wrong parameter name is worse than an admitted gap,
because it fails on a paid call.

## Four assumptions this project held that were WRONG

Recorded because they were wrong for long enough to reach a costed proposal.

| we assumed | actually |
|---|---|
| `list_unit_prices` returns a dict keyed by mode | **a JSON ARRAY of `{mode, unit_prices}` objects** |
| `mode` is a request parameter | **it is a RESPONSE field.** `get_cost(mode=…)` in the Python client is client-side and deprecated; it never enters the request |
| `symbols` is a repeated parameter | **a single COMMA-SEPARATED string**, max 2,000 symbols |
| encoding/compression default sensibly | **the raw HTTP API defaults to `csv` / `none`.** The official clients always send `dbn` / `zstd`. Omit them and you are billed for, and receive, something other than what you expected |

The client parses **both** unit-price shapes. A client that dies on the shape it
expected teaches nothing.

## Base URL and authentication

```
https://hist.databento.com/v0
```

**VERIFIED ×3** — [PY] `HistoricalGateway.BO1`, [RS] `HistoricalGateway::Bo1`,
[DOC] curl examples. Only one gateway exists (BO1, Boston).

**HTTP Basic, API key as USERNAME, EMPTY password. VERIFIED ×3.** The trailing
colon in the docs' `-u $YOUR_API_KEY:` *is* the empty password. No bearer token,
no `X-API-Key` header.

The key is read from `DATABENTO_API_KEY` or `~/.config/databento/key` — **outside
the repo** — and is sent as a header, so **nothing this client prints can leak
it**, including an error containing a URL. Asserted by test.

## Endpoint paths use DOTS, not slashes

**VERIFIED.** Paths are `{prefix}.{slug}` under `/v0/`.

| endpoint | method | notes |
|---|---|---|
| `metadata.list_datasets` | GET | takes `start_date`/`end_date`, **not** `start`/`end` |
| `metadata.list_schemas` | GET | `dataset` |
| `metadata.list_unit_prices` | GET | `dataset` only |
| `metadata.get_dataset_range` | GET | `dataset` only |
| `metadata.get_cost` | **POST** | see the conflict below |
| `metadata.get_billable_size` | **POST** | same |
| `timeseries.get_range` | **POST**, form-encoded | VERIFIED |
| `batch.submit_job` | **POST**, form-encoded | VERIFIED |
| `batch.list_jobs` | GET | |
| `symbology.resolve` | POST | |

**One genuine conflict, recorded rather than smoothed.** For `get_cost`,
`get_billable_size` and `get_record_count`: **[PY] and [RS] both POST** with a form
body; **[DOC] documents GET** with a `curl -G` example. The Python client's own
docstrings say GET while the code directly beneath calls `_post` — the code wins.

**INFERRED: the endpoints accept both.** This client POSTs, matching what ships in
production. These are **free** endpoints, so a wrong guess costs nothing to
discover — which is exactly why `--verify` exercises one before `--submit` exists.

## The roll rule, and why the proposal's `ES.c.0` is probably wrong

Continuous symbology is `[ROOT].[ROLL_RULE].[RANK]`, e.g. `ES.c.0`. **VERIFIED**
via [DOC]'s `symbology.resolve` example. `stype_in=continuous` is **VERIFIED**;
`parent` must never be used, since it resolves to every outright *plus* every
calendar spread.

All three of `ES.c.0`, `ES.v.0`, `ES.n.0` appear in official examples and are
accepted. **The letter→rule mapping is INFERRED**, from [PY]'s
`RollRule = volume | open_interest | calendar`:

| letter | inferred meaning |
|---|---|
| `c` | calendar |
| **`v`** | **volume** |
| `n` | open interest |

> **If that is right, `ES.c.0` rolls on the CALENDAR — at expiry.**
>
> That is precisely the failure this programme measured in Yahoo's `ES=F`:
> rolling at expiry rather than at volume crossover leaves the last 4–5 days of
> each quarter tracking the dying contract (volume 1,996k → 532k), **contaminating
> 7–8% of the sample.** §12 of the proposal requires crossover rolling.

**§11 of the proposal hard-codes `ES.c.0`. This client defaults to `ES.v.0`**, and
`--verify` resolves all three letters on a free call so the inference is settled
before any byte is bought. [`futures_continuous.py`](../scripts/futures_continuous.py)
defaults to volume rolling to match.

## Parameters — VERIFIED names

`dataset`, `symbols`, `schema`, `start`, `end`, `stype_in`, `stype_out`,
`encoding`, `compression`, `limit`, `split_duration`, `split_size`,
`split_symbols`, `delivery`, `pretty_px`, `pretty_ts`, `map_symbols`.

Enum values, **VERIFIED** [PY] `databento/common/enums.py`:

```
encoding        dbn | csv | json
compression     none | zstd
split_duration  day | week | month | year | none      (default: day)
delivery        download                              (only value)
states          queued | processing | done | expired
```

`stype_in` accepts `instrument_id`, `raw_symbol`, **`continuous`**, `parent`,
`isin`, `figi`, and others — **VERIFIED** [DBN] `enums.rs`.

## Plans gate SCHEMA DEPTH, not volume

| tier | L0 (OHLCV, definition, statistics) | L1 (trades, MBP-1, TBBO, BBO) | L2/L3 |
|---|---|---|---|
| **Usage-based, $0/mo** | **16+ years** | last 12 months | last 1 month |
| Standard, $199/mo | 16+ years | 16+ years | last 1 month |
| Unlimited, $4,500/mo | 16+ years | 16+ years | 16+ years |

**Every schema the proposal wants is on the free usage-based tier**, so no
subscription is required. An earlier proposal recommended $199 Standard on the
mistaken belief that a subscription included volume.

## The one inferred number the whole costing rests on

Databento publishes two worked examples of the *same* query:

```
get_billable_size(GLBX.MDP3, ESM2, trades, 2022-06-06 → 2022-06-10T12:10)
    = 99,219,648 bytes
get_cost(…same…)
    = $2.587353944778
```

`99,219,648 / 2³⁰ = 0.0924055 GiB`, and `2.587353944778 / 0.0924055` = **exactly
$28.00/GiB** — which also proves their "GB" means 2³⁰.

**The INFERRED step is that `ohlcv-1m` bills at the same rate as `trades`.** The
published OPRA `list_unit_prices` example prices `trades`, `ohlcv-1s` and
`ohlcv-1m` identically, which is suggestive but is a different dataset.

> **[DOC]'s own `list_unit_prices` example shows `ohlcv-1m` at 280.0** for an
> unnamed dataset — **ten times our figure.** Unit prices are per-dataset, so it
> is probably not a contradiction. **"Probably" is not good enough when the
> difference is $182 against $1,820**, and it is the entire reason `--verify`
> exists and runs first.

Derived unit costs, `OhlcvMsg` being a fixed 56 bytes and `1,380 × 252 = 347,760`
bars per symbol-year an upper bound:

| schema | per symbol-year |
|---|---|
| **`ohlcv-1m`** | **$0.5079** |
| `ohlcv-1s` | ~$30.60 |
| `trades` | **$145.33** — measured, not extrapolated |

**Correction to the proposal:** §5 and §10 quote **$0.51** and **$182.58**. The
exact figures are **$0.5079** and **$181.81**; $0.51 was a rounded intermediate.
`--plan` computes the exact one and reproduces the 26 symbols and 358.0
symbol-years exactly.

## Coverage

`GLBX.MDP3` (CME Globex MDP 3.0) begins **2010-06-06** — **VERIFIED**, and
independently confirmed by a Databento staff account in an r/algotrading thread.
**Anything earlier does not exist to buy.** Plans cover CME/CBOT/NYMEX/COMEX only;
equities and OPRA are separate products at every tier.

## How the client is prevented from spending

| mode | what it touches |
|---|---|
| `--plan` | **nothing.** No network, no key. Asserted by a test that fails if `call` is reached |
| `--verify` | free metadata endpoints only |
| `--cost` | `get_cost` — free |
| `--submit` | refuses without a passed `--verify` **and** `--i-accept-the-cost <figure>`, and is then **deliberately not wired up** |

**A spending path that exists is a spending path that can be run by accident.**
Submission gets written in the same commit as the purchase decision, not before.

Two traps hard-coded because they are cheap to hit: **`stype_in=continuous`, never
`parent`**; and **`batch.submit_job`, never streaming** — streaming re-bills on
retry, batch bills once and allows 30 days of free re-downloads.

## Licence — why nothing from here may ever be committed

**CME data is exchange-licensed and redistribution is forbidden.** `.gitignore`
carries `data/raw/databento/`, `data/raw/futures/`, `data/fixtures/*futures*` and
`data/fixtures/*glbx*`. The pattern is **gitignored cache + committed re-fetch
script + committed `.meta.json`** — never committed bars.

This is the opposite of [CFTC COT](cftc_cot.md), which is public domain and
therefore the one futures-adjacent source that lives in the repo.

## Still unknown

- **Whether CME licence fees apply on top of usage-based historical.** The
  licensing pages would not load for any research lane. Ask at signup.
- **Fair-use caps on bulk L0 under usage-based.** Not documented.
- **Whether `bbo-1m` exists as a schema**, or only `bbo-1s`.
- **The roll-rule letter mapping**, which is inferred above and which `--verify`
  settles for free.

## See also

- [`docs/research/futures-data/data-purchase-proposal.md`](research/futures-data/data-purchase-proposal.md) — the costing
- [`docs/research/futures-data/00-SYNTHESIS.md`](research/futures-data/00-SYNTHESIS.md) — why this vendor, and the roll warning
- [`scripts/futures_continuous.py`](../scripts/futures_continuous.py) — the stitcher and its acceptance gates
- [`docs/cftc_cot.md`](cftc_cot.md) — the free positioning provider
