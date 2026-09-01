# D262 — The futures data layer, and the free rung of the ladder

**Status:** Data acquisition — fixture built and committed; two modules built against no data at all
**Date:** 2026-09-01
**Area:** Data layer ([`docs/research/futures-data/data-purchase-proposal.md`](../research/futures-data/data-purchase-proposal.md))

**No strategy run, no cell scored, no rule proposed, no hurdle claimed.** The ledger does not move.

---

## What this is

The implementable half of the data-purchase proposal: **everything that could be built without
spending money.** Three deliverables, of which only the first involved a vendor at all.

| | |
|---|---|
| **`scripts/fetch_cftc_cot.py`** + fixture | **rung 1 of §7.5, free and now screenable** |
| **`scripts/futures_continuous.py`** | the stitcher §12 requires, built and tested with **no vendor data** |
| **`scripts/fetch_databento.py`** | a client that **cannot spend by accident** |

---

## 1. CFTC Commitments of Traders — built, committed

**210,717 rows · 28 symbols · three report families · 1986-01-15 → 2026-08-25 · 3.1 MB.**

**Committed, unlike every other futures source in this project.** COT is a work of the US
government and is public domain, so §12's redistribution constraint does not attach. The raw cache
stays gitignored per D191.

### The finding that makes this more than rung 1

**The CFTC reports the MICROS as their own contracts** — MES `13874U`, MNQ `209747`, M2K `239747`,
MYM `124608`, plus micro gold, silver and copper — **each with the full trader-category breakdown
and its own `nonrept` small-trader column.**

> The proposal costs **rung 2** — separating retail from institutional flow — at **$14.28** of
> Databento minute bars, on the argument that ten MES cost ~3x the fees of one ES so anyone trading
> size uses ES. **That argument infers the split from contract choice. The CFTC classifies the
> traders directly, weekly, for nothing.**

**It does not replace the paid rung 2** — weekly resolution cannot support an intraday rule — **and
it is bounded harder than expected.** A contract enters COT only once it has enough *reportable*
traders, which lags listing by years:

| | listed | first COT report | lag |
|---|---|---|---|
| MES | 2019-05-06 | **2020-07-28** | 1.2 y |
| MNQ | 2019-05-06 | 2020-08-04 | 1.2 y |
| M2K | 2019-05-06 | **2021-11-30** | 2.6 y |
| MYM | 2019-05-06 | **2022-07-26** | 3.2 y |
| MSI / MHG | 2022 | **2026-01** | ~4 y |

**So it is ES/MES and NQ/MNQ at ~6 years, not four pairs at seven. But the premise can be falsified
for £0 before any purchase decision**, which is the ladder's own logic taken one step further than
the proposal took it.

### Five things measured that were not assumed

**1. The symbol map is DERIVED and refuses ambiguity**, because a hand-typed contract code returns a
full, plausible, well-formed series for the *wrong market* and nothing downstream errors.

- **`%CRUDE OIL%` matches SEVEN contracts** — WTI light sweet `067411` is the one; the others are
  1st-line, E-mini, two financials, Dubai and Oman.
- **`%NATURAL GAS%` matches the main contract NOT AT ALL.** The CFTC abbreviates, so the pattern
  returns `E-MINI NATURAL GAS` and a San Juan index — **two plausible wrong answers and no right
  one.** The liquid contract is `023651` **"NAT GAS NYME"**. This is the worse trap: the first has
  six wrong answers and one right one, the second has no right one at all.

**2. The open-interest identity, and the first version of the gate was wrong.** `OI == sum(long)`
fails on **94% of rows**, because a **spread position is one long AND one short held by the same
trader** — inside open interest, outside the directional columns. The identity is

```
open_interest == sum(long) + sum(spread) == sum(short) + sum(spread)
```

and it then holds on **55,661 of 55,661 rows, exactly.** Both sides are checked, since a
transposition preserving one would still break the other. **It is the cheapest available proof that
every column landed in its right slot.**

**3. The release convention is week-based, not a flat offset.** COT is surveyed Tuesday and
published Friday, so keying on `report_date` is **three days of look-ahead — what R9 forbids of a
conditioning variable.** But measured across 1986–2026:

- Tuesday on 98–100% of weeks **from 1993**; the exceptions are **holiday shifts** (2007-01-03 is a
  Wednesday because the markets closed for President Ford's National Day of Mourning)
- **four Friday-dated reports survive after 1993**, pinned by name so a fifth fails loudly
- a Friday report under a flat +3 would release on a **Saturday**; under "Friday of the week" it
  would release **on itself — zero lag, look-ahead by construction** — so it is pushed to the
  following Friday. **Erring late is the only safe direction.**
- **before 1993 there was no weekly schedule at all** (1986 is 46.8% Friday), so
  `release_date_nominal` is **EMPTY** there. A fabricated release date would look usable.

**4. Two provenance traps recorded rather than discovered later.** `6E` carries rows from
**1986-01-15 under the name `EURO FX`, though the euro did not exist until 1999-01-01**; continuous
coverage begins exactly **1999-01-05** after a 644-week gap, so code `099741` back-labels a
predecessor. And `RTY` **spans a venue change** — the Russell E-mini traded on ICE 2008–2017.

**5. The provider's own typos are part of the contract.** `swap__positions_short_all` and
`swap__positions_spread_all` carry a **double underscore**; `noncomm_postions_spread_all` says
**"postions"**. They look like defects, and a helpful correction would empty our columns silently.
Asserted by test, along with an assertion that the *plausible corrected* spellings are not what we
request.

**Also:** TFF and disaggregated serve back to **2006-06-13**, earlier than the CFTC's published
2010-07-20 and 2009-09. Recorded as a discrepancy rather than silently banked.

---

## 2. The continuous-contract stitcher — built against nothing

**Every external source consulted said the same thing: the hard part of futures data is stitching,
not acquisition.** All four r/algotrading threads, and §12.

**It needs no vendor data to build or to test**, which is why it exists now — the acceptance gates
have to exist *before* the fixture, or the fixture is what decides whether they pass.

Rolls on **volume or open-interest crossover, never the calendar**, with persistence required (a
one-day blip is usually an expiry-week spread trade). Back-adjusts by **ratio** (preserves returns
exactly — the default, since returns are what this programme scores) or **difference** (preserves
price differences; survives negative prices, which is not hypothetical — **CL settled at −$37.63 on
2020-04-20**). The **unadjusted series is always retained**, because back-adjustment restates the
whole history at every new roll.

### The two tests that carry the weight

**A. Synthetic ground truth.** Contracts built from a known true path, so the stitcher is checked
for **exactness rather than plausibility** — plausible is what a broken stitcher already looks like.
Ratio adjustment recovers the true return series to **1e-12**; difference adjustment recovers an
additive-basis path to **1e-9**.

**B. The measured Yahoo signature, reconstructed and rejected.** **A gate suite that has never
rejected anything is not evidence.** The specific `ES=F` failure this programme measured is rebuilt
— rolling at expiry with the front month at ~21% volume share, no back-adjustment, a +2.77% splice
gap — and each gate must catch its own symptom, including the divergence test that actually caught
Yahoo (**15 of the top 16 ES-vs-SPY divergences on quarterly expiries**).

**With the complement: a correctly stitched series must PASS every gate.** A suite that rejects
everything is no better than one that rejects nothing.

---

## 3. The Databento client — verify-first, unable to spend

Written against a surface established from **three independent sources that agree** — the
`databento-python` source, the `databento-rs` source *including its wiremock tests, which assert
exact paths, methods and parameters*, and the official docs served as plain text via Context7 after
the JS-rendered site defeated every direct fetch.

### The correction that matters most

> **§11 of the proposal hard-codes `ES.c.0`.** The roll-rule letters are undocumented, but
> `databento-python` carries `RollRule = volume | open_interest | calendar`, which makes **`c` =
> CALENDAR — rolling at expiry.**
>
> **That is precisely the failure §12 measures in Yahoo's `ES=F`.** We would have paid for the
> defect the acceptance tests were written to catch.

The client defaults to **`ES.v.0`**, and `--verify` resolves all three letters on a free call to
settle the inference before any byte is bought.

### Four assumptions that were wrong

| assumed | actually |
|---|---|
| `list_unit_prices` is a dict keyed by mode | **a JSON ARRAY of `{mode, unit_prices}`** |
| `mode` is a request parameter | **a RESPONSE field**; the client-side one is deprecated |
| `symbols` is repeated | **a single comma-separated string** |
| encoding defaults sensibly | **the raw API defaults to `csv`/`none`** where clients send `dbn`/`zstd` |

### And a rounding correction to our own costing

`--plan` computes **$181.81**, not the proposal's **$182.58**: $0.51 per symbol-year was a rounded
intermediate and the exact rate is **$0.5079**. **The 26 symbols and 358.0 symbol-years reproduce
exactly.**

### It cannot spend

`--plan` touches no network and needs no key — **asserted by a test that fails if the request
function is reached.** `--verify` and `--cost` call only free endpoints. `--submit` refuses without
both a passed verify and an explicitly accepted figure, **and is then deliberately not wired up**:
a spending path that exists is a spending path that can be run by accident, so it gets written in
the same commit as the purchase decision.

**`--verify`'s first job is the one inferred number the whole costing rests on.** Databento's docs
show an `ohlcv-1m` unit price of **280.0** for an unnamed dataset against our derived **$28.00/GiB**.
Unit prices are per-dataset so it is probably not a contradiction — **but "probably" is not good
enough when the difference is $182 against $1,820.**

---

## What is NOT done, and why

- **Nothing purchased.** The ladder says screen rungs 1–3 first, and rung 1 now exists.
- **No study.** Screening COT for a smart-money signal is a study and needs its own pre-registration
  under R8 — the same separation D252 used.
- **`--submit` unwired**, as above.
- **The Databento HTTP layer is untested against the live service.** `--verify` is built to catch
  every assumption on the first free call, but until it runs against a real key this is code that
  has never spoken to the server. **It is designed so that being wrong costs an error message
  rather than money.**

## Ledger

**Unchanged.** No cell was scored.
