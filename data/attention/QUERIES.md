# `data/attention/QUERIES.md` — the fixed query definitions for the attention layer

*Record: **D612**. Written **2026-09-22**, **before any feature code existed**, because
`SETTLEMENT_FLOW_LEDGER_PREREG.md:116` says so:*

> Query definitions (keyword lists, article titles, tickers) are fixed in `data/attention/QUERIES.md`
> **before** any feature is computed, and not changed afterwards without a doc edit.

**This file is the hashed object.** `attention.queries_hash()` is the sha256 of these bytes with
newlines pinned to LF (`validation/frozen.py`'s `sha256_file(text_normalise=True)`, D550/D551), and
the digest is committed beside it in `QUERIES.sha256`. `attention.load_queries()` re-hashes on every
load and raises `QueriesTampered` when the two disagree. Ledger unit test **25** stores that digest
on every `trials.csv` row, so a trial whose queries were edited is identifiable from the trial log
alone.

**Editing this file is a doc edit and changes the hash.** That is the intended cost: every result
computed under the old list becomes distinguishable from every result computed under the new one.
Nothing in `attention.py` or `scripts/fetch_attention.py` writes to this file.

---

## 1. The Wikipedia article list (`wiki_n`)

Ledger `:252` — *"`wiki_n(h)`: pageviews summed over the fixed article list in the last completed
hour."* The project is **en.wikipedia**. Every candidate below was probed **once** against the
Wikimedia REST per-article **daily** endpoint on **2026-09-22**, over `2019110400`–`2019111000`:

    https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{ARTICLE}/daily/2019110400/2019111000

Status and probe date are recorded beside each title. **An article that does not resolve is listed
as `unresolved`, not dropped silently**, so a later reader can see what was asked for and what the
encyclopedia actually holds.

### 1a. IN THE LIST — the eight that resolved

| # | article | probe | date | views in the probe window | note |
|---|---|---|---|---|---|
| 1 | `Natural_gas` | **200** | 2026-09-22 | 15,574 | the NG anchor |
| 2 | `Henry_Hub` | **200** | 2026-09-22 | 490 | the NG delivery point; the deposit's own word |
| 3 | `Natural_gas_prices` | **200** | 2026-09-22 | 1,589 | |
| 4 | `Price_of_oil` | **200** | 2026-09-22 | 3,359 | the CL anchor |
| 5 | `West_Texas_Intermediate` | **200** | 2026-09-22 | 1,574 | |
| 6 | `Petroleum` | **200** | 2026-09-22 | 21,590 | broad; the highest-traffic member, and a general-interest page rather than a price page |
| 7 | `United_States_Oil_Fund` | **200** | 2026-09-22 | 75 | USO, one of the deposit's six US ETFs |
| 8 | `ProShares` | **200** | 2026-09-22 | 49 | the issuer page; the only page that names BOIL/KOLD/UCO/SCO's sponsor |

### 1b. NOT IN THE LIST — `unresolved`, recorded rather than dropped

| candidate | probe | date | what came back |
|---|---|---|---|
| `United_States_Natural_Gas_Fund` | **404** | 2026-09-22 | *"we either do not have data for those date(s)"*; `en.wikipedia.org/w/api.php?action=query&titles=…` returns `missing=True`. **The page does not exist.** UNG has no en.wikipedia article. |
| `BOIL` | **404** | 2026-09-22 | same; `missing=True`. **No such page.** |
| `ProShares_Ultra_Bloomberg_Natural_Gas` | **404** | 2026-09-22 | same. The fund has no article under its own name. |

### 1c. NOT IN THE LIST — resolved, and EXCLUDED as contaminants

**This is the trap the brief's "four ProShares fund pages if they exist" was pointing at, and three
of the four tickers walk into it.** `KOLD`, `UCO` and `SCO` all return **HTTP 200** with real
traffic. None of them is a fund page:

| candidate | probe | date | views | what the page actually is (REST `page/summary`, 2026-09-22) |
|---|---|---|---|---|
| `KOLD` | 200 | 2026-09-22 | 20 | `type=disambiguation` — *"KOLD-FM, a radio station licensed to serve Cold Bay, Alaska"*, and a Tucson television station |
| `UCO` | 200 | 2026-09-22 | 44 | `type=disambiguation` |
| `SCO` | 200 | 2026-09-22 | 495 | `type=disambiguation` — the highest-traffic of the three, and none of that traffic is about crude oil |

**A 200 is not a resolution.** Admitting these three would have added ~559 views of radio stations
and software companies to an oil-and-gas attention series, with `SCO` alone larger than `Henry_Hub`.
They stay out, by name, so that nobody re-adds them from the ticker list.

### 1d. The dump projects that count as "en.wikipedia"

Per-article **hourly** pageviews do **not** exist on the REST API (see `README.md` in this directory
and the D612 record's erratum). The hourly route is the dumps, whose line format is

    <project> <article> <views> <bytes_returned>

**The projects summed for `wiki_n` are exactly `en` and `en.m`** — en.wikipedia desktop and
mobile-web, which is what the REST endpoint's `all-access` aggregates. Any other project code
carrying one of the eight titles (`en.b`, `en.d`, `commons.m`, …) is **recorded in the raw residue
and not summed**, so the residue stays auditable while the series stays one encyclopedia's.

| project | summed into `wiki_n` |
|---|---|
| `en` | yes |
| `en.m` | yes |

Article titles are matched **exactly and case-sensitively** against the dump's second field. The
dump does not resolve redirects and neither does this list.

---

## 2. The GDELT queries (`news_n`, `news_tone`)

Ledger `:251` — *"`news_n(τ)`: GDELT article count matching the fixed query in the last 60 min.
`news_tone(τ)`: mean tone of those articles."*

### 2a. The documents

The unit of `news_n` is a **GKG document**, one row of `{SLOT}.gkg.csv.zip`, keyed on its
`V2.1DATE` — **the file slot's own timestamp**, which is the publication timestamp the deposit's
`:267` and unit test 23 require. The event date in the `export` file is **not** used for keying.

### 2b. The match rule, stated before any count was taken

A GKG row is normalised into three haystacks:

* **title** — the `<PAGE_TITLE>` element of field 27 (`V2EXTRASXML`), lowercased, every run of
  characters outside `[a-z0-9]` replaced by one space, with one leading and one trailing space;
* **url** — field 5 (`V2DOCUMENTIDENTIFIER`), normalised the same way, so
  `…/The-Next-Natural-Gas-Superpower.html` becomes `… the next natural gas superpower html `;
* **themes** — field 8 (`V1THEMES`), split on `;`, kept as exact uppercase tokens.

A query matches a row when its own rule fires. **A row matches a query at most once**, so `news_n`
is a document count and never a mention count.

| id | kind | literal | rule | precision |
|---|---|---|---|---|
| `natural_gas` | phrase | `natural gas` | `" natural gas "` in **title or url** | high |
| `crude_oil` | phrase | `crude oil` | `" crude oil "` in **title or url** | high |
| `henry_hub` | phrase | `henry hub` | `" henry hub "` in **title or url** | high |
| `wti` | phrase | `wti` | `" wti "` in **title or url** | high |
| `theme_env_naturalgas` | theme | `ENV_NATURALGAS` | exact token in `V1THEMES` | high |
| `theme_env_oil` | theme | `ENV_OIL` | exact token in `V1THEMES` | high |
| `theme_econ_oilprice` | theme | `ECON_OILPRICE` | exact token in `V1THEMES` | high |
| `theme_econ_natgasprice` | theme | `ECON_NATGASPRICE` | exact token in `V1THEMES` | high |
| `tk_boil` | ticker | `boil` | whole word in **title only** | **low** |
| `tk_kold` | ticker | `kold` | whole word in **title only** | **low** |
| `tk_uco` | ticker | `uco` | whole word in **title only** | **low** |
| `tk_sco` | ticker | `sco` | whole word in **title only** | **low** |
| `tk_ung` | ticker | `ung` | whole word in **title only** | **low** |
| `tk_uso` | ticker | `uso` | whole word in **title only** | **low** |

**Why the four themes are in the list and why they are not an afterthought.** Measured on the
`20191104121500` slot (1,887 rows): the title-only phrase rule fires **once** for `natural gas` and
**once** for `crude oil`, while `ENV_OIL` fires on **69** rows, `ECON_OILPRICE` on **20** and
`ENV_NATURALGAS` on **17**. A phrase-only `news_n` on this corpus would be a count of near-zeros,
and a z-score of a near-zero count is noise with a denominator. The theme tokens were **verified to
exist in the data before being written here**, not taken from documentation.

**Why the six tickers are marked `low` and why they are kept anyway.** `boil`, `sco`, `uco` and
`ung` are ordinary English or ordinary abbreviations; `uso` is Spanish and Portuguese for "use".
Matching them on the URL as well would make it worse — a path segment `/uso/` appears on
Portuguese-language sites that have nothing to do with the fund. They are matched on the **title
only**, they are **flagged `precision: low` in this file and in every fixture row**, and the D612
record says plainly that they are recorded, not trusted. Removing them would hide the ambiguity;
using them as a primary series would import it.

**`news_tone`** is the mean over the matched rows of the **first comma-component of field 16**
(`V1.5TONE`), which is the document tone. A slot with no matched row has **no tone**, recorded as
`NaN`, and never as `0.0` — a zero tone is neutral coverage and an absent tone is no coverage.

### 2c. The DOC 2.0 API encoding — the FORWARD route only

The historical route is the raw files above. The DOC 2.0 API is the forward route (see the D612
record on why: the files are a static host with no observed limit, the API is **one request per
5 seconds** and 429s with a long cooldown after any burst). The `query=` value for each phrase, URL
encoded exactly as `scripts/fetch_attention.py --gdelt-doc` sends it:

| id | `query=` |
|---|---|
| `natural_gas` | `%22natural+gas%22` |
| `crude_oil` | `%22crude+oil%22` |
| `henry_hub` | `%22Henry+Hub%22` |
| `wti` | `WTI` |
| `tk_boil` | `BOIL` |
| `tk_kold` | `KOLD` |
| `tk_uco` | `UCO` |
| `tk_sco` | `SCO` |
| `tk_ung` | `UNG` |
| `tk_uso` | `USO` |

The API autoscales its own bucket width and reports it in `query_details.date_resolution`. Ledger
`:251` asks for a count over the **last 60 min** and `:265` for 15-minute blocks, so
`--gdelt-doc` **refuses any response coarser than 15 minutes** for a feature value rather than
silently accepting hourly buckets. The four theme queries have no DOC-API spelling here: theme
search on the API uses a different operator, and no encoding is written down that has not been sent.

---

## 3. Social — `disabled (Q12)`

| id | source | state |
|---|---|---|
| `social_reddit` | Reddit archive | **disabled (Q12)** |
| `social_stocktwits` | StockTwits archive | **disabled (Q12)** |

Ledger `:113` makes these **Optional:** *"only if a timestamped archive covering the sample is
obtained lawfully and within platform terms (Q12)"*, and `:253` gates `social_n(τ)` on the same
question. Q12 is unresolved, so no ticker list, no keyword list and no endpoint is written here.
`att_breadth` counts the sources that are **present**, so a disabled source lowers the possible
breadth rather than contributing a zero — the deposit's `:263` counts *"sources with z > 2"*, and a
source with no data has no z.

**Google Trends is excluded from modelling entirely** (`:114`), and has no id in this file at all.

---

## 4. What is NOT fixed here

Nothing in this file names a **feature threshold**. The `z > 2` of `att_breadth` and the `z > 3` of
`headline_burst` are the deposit's (`:263`, `:265`) and live in `attention.py` as module constants
with the line numbers beside them; the 60-day trailing window and the 15-minute publication buffer
are the deposit's too (`:255`, `:267`). This file fixes **what is counted**, not **how the count is
scored**, and the two are hashed separately: the query list by `QUERIES.sha256`, the code by the
frozen protocol's `frozen_sha256`. A `trials.csv` row carries both.
