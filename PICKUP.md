# PICKUP — handoff for the next session

**Written 2026-09-01 at the end of a session that built the free half of the futures data layer.**

Read this first, then [`docs/decisions/D262-the-futures-data-layer-and-the-free-rung.md`](docs/decisions/D262-the-futures-data-layer-and-the-free-rung.md).
Everything below is verifiable from the repo; nothing here is a plan I intend to be trusted on faith.

---

## 1. State of the tree

**Working tree is CLEAN. Everything is committed.** Nine commits this session, `520e71b..0b40695`.

```
0b40695  WP4: the 2010-2017 backfill lands, and the 57-ETF extended fixture is REFUSED
8df1bc1  fetch_databento: close the two guard gaps found by reviewing the guards
0b99ac1  fetch_etf_intraday: --extended writes its OWN fixture, and 64 bars not 26
1043544  D262: the futures data layer documented, and three corrections to the proposal
02d8277  Continuous-contract stitcher, and the gates that reject a bad splice
4ef9a61  Databento client: verify-first, and structurally unable to spend
c18a4e6  CFTC Commitments of Traders: rung 1 of the ladder, built and committed
b1af940  futures-data: close lane 01, and close the forum search entirely
520e71b  data-purchase-proposal.md: the full costing, with the tick figure corrected
```

**Suite: 1,831 passing, 5 deselected, 1 failing.** The failure is
`tests/property/test_structure_invariants.py::test_every_gap_is_a_non_empty_band_that_price_left_behind`
and it is **PRE-EXISTING and explicitly not to be fixed.** Do not "helpfully" repair it.

**Next decision number is D263.** The README counter was stale at D260 and is now correct.

---

## 2. THE ONE THING BLOCKING PROGRESS, and it is not yours to unblock

`scripts/fetch_databento.py --verify` **cannot run: there is no Databento key on this machine**, and
no account behind it.

```
key file expected at:  C:\Users\O\.config\databento\key        (does not exist)
or env var:            DATABENTO_API_KEY                        (not set)
```

**Do not create the account. Do not handle, write, or ask for the key.** The principal has been given
the two steps (sign up choosing **usage-based $0/mo, NOT Standard**; save the key to that path). If
they say it is done, run `--verify` — it is free, metadata endpoints only, ~7 calls, ~4 seconds.

### What `--verify` settles, and why it matters more than it looks

**The single inferred number the entire $181.81 costing rests on.** We derived **$28.00/GiB** from
Databento's own two worked examples. **Their published `list_unit_prices` example shows `ohlcv-1m` at
280.0** for an unnamed dataset — ten times that. Unit prices are per-dataset so it is *probably* not a
contradiction, but the spread is **$182 against $1,820** and probably is not good enough.

It also resolves `ES.c.0` / `ES.v.0` / `ES.n.0` to settle whether the roll-rule letters mean what
`databento-python`'s `RollRule` enum implies. **See §5 — this one nearly cost real money.**

---

## 3. What now exists that did not before

| | |
|---|---|
| `scripts/fetch_cftc_cot.py` + fixture | **rung 1 of the ladder, free, BUILT** |
| `scripts/futures_continuous.py` | the stitcher §12 requires, tested against **no vendor data** |
| `scripts/fetch_databento.py` | a client that **cannot spend by accident** |
| `docs/cftc_cot.md`, `docs/databento_api.md` | provider references |

**`data/fixtures/cftc_cot_raw.csv.gz` — 210,717 rows, 28 symbols, three report families,
1986-01-15 → 2026-08-25, 3.1 MB, COMMITTED.** It is the only source in the futures data layer that
may be committed, because COT is a work of the US government and is public domain.

**Also durable:** the Alpha Vantage 15-minute cache is now **complete at 11,400 slices** (526 MB,
gitignored), including the 2010–2017 backfill. **Any future extended-hours study starts at zero
requests.**

---

## 4. The immediate next step, and it is NOT a purchase

**Screen rung 1.** The ladder in §7.5 of the proposal says test the cheap instruments before buying
the expensive one, and rung 1 is now sitting in the repo.

> **This is a STUDY, so it needs its own pre-registration under R8 before anything is scored.**
> D262 is a *data acquisition* record — it deliberately scored nothing. Do not read the fixture and
> report a number without registering first. That is the whole discipline of this repo.

**The question worth registering:** does institutional-versus-retail positioning, as the CFTC
classifies it, carry information at a weekly horizon?

**Two constructions are available and they are not the same test:**

1. **Category positioning** — `leveraged_money` / `asset_manager` / `dealer` net positioning and its
   changes, per contract. Available on the widest history.
2. **The micro/mini split** — the free weekly form of rung 2. **THIS IS THE FINDING OF THE SESSION:**
   the CFTC reports micros as their own contracts (MES `13874U`, MNQ `209747`, M2K `239747`,
   MYM `124608`, plus micro metals), each with its own `nonrept` small-trader column. The proposal
   costs this at $14.28 of Databento minute bars to *infer* the split from contract choice; the CFTC
   classifies the traders directly.

**BUT READ THIS BEFORE SCOPING IT.** A contract enters COT only once it has enough *reportable*
traders, which lags listing by years:

| | listed | first COT report |
|---|---|---|
| MES | 2019-05-06 | **2020-07-28** |
| MNQ | 2019-05-06 | 2020-08-04 |
| M2K | 2019-05-06 | **2021-11-30** |
| MYM | 2019-05-06 | **2022-07-26** |
| MSI / MHG | 2022 | **2026-01** — unusable |

**So it is ES/MES and NQ/MNQ at ~6 years, not four pairs at seven.** Scope the registration to the
pairs that have history, and state the breadth honestly — two correlated pairs is thin, and R10
applies.

**Rung 3 is also free** and needs no new data: open interest against volume, in the fixture already.

---

## 5. Traps found this session that will bite you if you do not know them

**The symbol map is derived for a reason. Never type a CFTC contract code.**
`%CRUDE OIL%` matches **seven** contracts. Worse, **`%NATURAL GAS%` matches the main Henry Hub
contract NOT AT ALL** — the CFTC abbreviates it to `NAT GAS NYME`, so the pattern returns two
plausible wrong answers and no right one. A wrong code returns a full, well-formed series for the
wrong market and **nothing downstream errors**.

**The COT open-interest identity is not `OI == sum(long)`.** That fails on 94% of rows. A **spread
position is one long AND one short held by the same trader** — inside open interest, outside the
directional columns. It is `OI == sum(long) + sum(spread) == sum(short) + sum(spread)`, and it then
holds on **55,661/55,661 rows exactly**.

**Key COT dates on `release_date_nominal`, never `report_date`.** Report is Tuesday, release is the
**Friday of that week** — not a flat +3, because the survey day shifts on holidays. Rows before 1993
carry **no release date at all**, deliberately: there was no weekly schedule then and a fabricated
date would look usable.

**`6E` predates the euro.** Legacy rows run from 1986 under the name `EURO FX`; the euro began
1999-01-01 and continuous coverage starts exactly **1999-01-05** after a 644-week gap. **Use
1999-01-05 onward.** `RTY` separately spans an ICE venue change (2008–2017).

**The provider's typos are load-bearing.** `swap__positions_short_all` and
`swap__positions_spread_all` have **double underscores**; `noncomm_postions_spread_all` says
**"postions"**. Pinned by test. If you "fix" them the columns go silently empty.

**`ES.c.0` is almost certainly the CALENDAR roll — rolling at expiry.** §11 of the proposal
hard-coded it. That is precisely the defect §12's acceptance tests were written to catch in Yahoo's
`ES=F`. **The default is now `ES.v.0`.** Do not revert it on the basis of the proposal's text.

**The 57-ETF extended-hours fixture is REFUSED, on measurement.** Only **2 of 57 symbols** reach a
median 58 of 64 session slots; the tail is at 27–28; the raggedness is **liquidity-correlated**,
which is disqualifying for anything volume-related. And an unfiltered **+428.52%** bad print survives
(EWJ 2018-05-23 08:15 prints 11.46 on 912 shares against ~60.60 either side). `--extended` refuses
with the numbers as the reason. **Use `fetch_index_extended.py`**, which applies D259's
corroboration filter and carries a `suspect` column.

---

## 6. Two mistakes I made, so you do not repeat the shape of them

**I overwrote a committed fixture's meta.** The commit *before* it existed specifically to stop
`--extended` clobbering the regular-hours artifact. It parameterised the fixture path and the events
path and **missed the meta.** Caught only because `git status` flagged the committed file as
modified. Fixed by giving one function (`build_targets`) all three paths, plus a test asserting
`do_build` reaches for no unparameterised output constant. **Three constants with two swapped hides
the one you forget.**

**I wrote gates that were wrong before they were right** — the open-interest identity passed on 5.82%
of rows on its first version, and the release convention put a Friday report's release on itself
(zero lag, look-ahead by construction). Both were found by *looking at the output*, not by reasoning.
**Run the gate and read the number before believing it.**

**Practical note:** `Bash` heredocs on this machine mangle backslashes — a `"\n"` inside a Python
heredoc became a literal newline and silently broke a string, and an earlier `str.replace` missed for
the same reason. **Use the Edit/Write tools for anything containing escapes.**

---

## 7. Standing constraints — these do not lapse

**Alpha Vantage key** at `C:\Users\O\.config\alphavantage\key`, read via `ALPHAVANTAGE_API_KEY`
first. **Never inlined, never printed, never logged, redacted from any displayed URL.** Pace at
**66 req/min** against the 75 ceiling. Cache every response; hard stop after 5 consecutive failures.
**The ToS requires this repo stay private.**

**Exchange-licensed data is NEVER committed.** CME, Sierra Chart and NinjaTrader all forbid
redistribution. `.gitignore` carries `data/raw/databento/`, `data/raw/futures/`,
`data/fixtures/*futures*`, `data/fixtures/*glbx*`. The pattern is **gitignored cache + committed
re-fetch script + committed `.meta.json`**. CFTC COT is the sole exception and only because it is
public domain.

**Raw caches are not committed (D191); derived fixtures are.**

**No purchase without the principal's explicit decision.** `--submit` refuses without a passed
`--verify` *and* an accepted figure, and is then deliberately unwired. **Leave it that way** until
the purchase is actually decided — wire it up in the same commit, not before.

---

## 8. Where things are

| | |
|---|---|
| the costed purchase | `docs/research/futures-data/data-purchase-proposal.md` |
| the twelve-lane free search | `docs/research/futures-data/00-SYNTHESIS.md` |
| this session's record | `docs/decisions/D262-...md` |
| standing rules R1–R12 | `docs/RULES.md` |
| the two books | `docs/BOOK.md` (personal), `docs/BOOK_PROP.md` (prop — **admitted arms: none**) |
| substantive findings | `docs/FINDINGS.md` |
| providers | `docs/alpha_vantage_api.md`, `docs/cftc_cot.md`, `docs/databento_api.md` |

**Prop track status: every candidate so far is closed.** C1, C2, C3 and D261's spreads all failed —
three of them on **shape** rather than return, which is why the smart-money detector was worth
reaching for: order flow and positioning are among the few signal families with the shape hurdle P
wants. **Rung 1 is the cheapest available test of that idea and it is ready to screen.**

---

## 9. If you do only one thing

**Pre-register the COT screen and run it.** It costs nothing, the data is committed, and a negative
result is worth as much as a positive one — it would tell the principal not to spend £205 on the
Databento purchase at all.
