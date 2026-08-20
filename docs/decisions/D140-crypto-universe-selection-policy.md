# D140 — The crypto-universe fixture: a pre-stated selection policy that deliberately admits assets that died

**Status:** Committed
**Date:** 2026-08-18
**Category:** Data layer
**Source:** Breakout universe session ([`docs/results/breakout_universe.md`](../results/breakout_universe.md))

## Decision

`data/fixtures/crypto_universe_2015_2025_raw.csv.gz` (+ events JSON + meta): 63 crypto
symbols, 2015–2025 daily, fetched raw by `scripts/fetch_crypto_universe.py` over the same
calendar range as the BTC/ETH fixture (D108) so the two studies' overlapping symbols are
directly comparable.

The candidate roster is **77 tickers in three cohorts**, chosen for point-in-time
prominence rather than present size:

- `top30_at_2018_01` (29 attempted) — roughly the market-cap table at the first mania's
  peak, including the many members that never came back;
- `prominent_at_2021_peak` (33 attempted) — roughly the table at the second mania's peak,
  plus the DeFi and metaverse tokens of that year;
- `sought_failures` (15 attempted) — chosen **because** they failed: Terra/LUNA under both
  tickers the provider serves, TerraUSD, FTX's FTT, Celsius, Serum, plus OKB and LEO as the
  surviving exchange-token control for FTT.

**Coverage policy (the D88 pattern, applied to crypto).** One implementation,
`research.breakout_universe.apply_policy`, run at fetch time to decide the fixture's
contents and run **again** by the study on the committed fixture, so a symbol that fails
cannot reach the engine by being quietly present in a CSV. It screens the **cleaned**
series (D25), because the engine trades cleaned bars. In order:

1. **All prices strictly positive** after cleaning — log returns and inverse-vol sizing
   are undefined otherwise.
2. **Peg screen** — see [D144](D144-peg-screen-added-after-first-run.md).
3. **Minimum history: 520 bars.** The mechanical floor is 315 (train 252 + test 63; the
   warm-up prefix comes from *inside* window 0's training slice, so even a 201-bar lookback
   fits). 315 would also be useless — one 63-bar test window is ten weeks of out-of-sample
   data for a strategy whose median trade lasts about four weeks. 520 is the shortest
   history yielding four windows and a full year (252 bars) out of sample.
4. **Liquidity floor: median daily volume ≥ 5,000,000 USD** over the symbol's own history.
   Median, not mean — crypto volume is spiked hard by launch weeks and collapse weeks.
   Level derived from the study's own capital: 100,000 USD starting cash with a 1.0×
   position cap makes the largest opening order ~2% of a 5,000,000 USD day, the region D95
   treats unmodelled impact as second-order in.

**Nothing in the screen touches a return, a Sharpe, a drawdown or a trade count.** That is
the whole difference between a universe rule and a survivorship filter, and it is why the
screen could be stated in full before any performance was computed.

**Classification, hindsight by construction and used only to split results:**
`delisted` (last bar >90 days before the fixture end date — checked first, because losing
the quote is the more specific fact), else `collapsed` (final close ≤10% of the symbol's
own peak close), else `survived`. Outcome: **20 survived, 41 collapsed, 2 delisted.**

**Every attempt is accounted for in the meta**: 63 included, 13 excluded with the statistic
that rejected them, 1 (`MIOTA-USD`) that yfinance would not serve at all. Coverage
statistics are recorded for excluded symbols too, so an exclusion can be audited without
re-fetching.

## Rationale

`BREAKOUT_RESULTS.md` names its own worst problem in its caveats: BTC and ETH are "the two
crypto assets that survived to be worth studying … the single largest un-deflatable bias in
this document". A universe of today's twenty largest coins would restate that bias at
greater scale — every member would be a survivor, and the cross-section would confirm the
original result for the same wrong reason.

A universe that contains assets which collapsed or died is what turns the study into a real
cross-sectional test, and it is what makes the bias **measurable**: every statistic is
reported split survived vs collapsed/delisted, so the reader can see exactly how much of
the BTC/ETH result was a property of BTC and ETH.

**The roster's honesty, stated where it cannot be missed.** It was assembled by hand, in
2026, from recollection of two past market-cap tables. It is *not* a reconstruction from an
archived point-in-time index — no such archive is wired into this repo, and claiming
otherwise would be the exact self-deception this framework exists to prevent. What can be
defended is narrower: two cohorts were chosen for past worth rather than present worth, the
third was chosen for failure (which biases *against* the strategy's flattering case), and
43 of the 63 admitted coins ended down 90%+ or unquoted. What remains unfixed is
survivorship inside the *provider*: a token yfinance never listed, or has since dropped,
cannot appear at any price — and those are the worst outcomes by construction. The report
states this as "less biased than BTC/ETH, not unbiased".

**Why exclusions are named rather than trimmed.** D88's coverage policy converted a silent
data-shape hazard into a named exclusion list; the same argument is sharper here, because
a silently omitted failed asset *is* the bias. `MIOTA-USD` — a genuine 2018 top-ten token
that fell ~99% — is recorded as a fetch failure with the attempt, so a reader can see that
its absence biases the cross-section toward the strategy looking worse, not better.

**Why the same calendar range as D108's fixture.** BTC-USD and ETH-USD appear in both
fixtures, fetched separately, from a provider that restates history — which is D24's entire
rationale. Running the same range makes them a *reconciliation target* rather than a near
miss: `reconcile_against_published` compares this study's `plateau_40_10` @ `taker_40bp`
rows against the values `BREAKOUT_RESULTS.md` prints, per metric, in units of that
document's own printed precision, and an integration test fails if any of them drifts by a
full last digit. They currently agree on every statistic. That is what licenses reading the
cross-section's numbers directly against the published ones — and if a future re-fetch
breaks it, the failure is a *data* event surfaced loudly rather than two documents quietly
quoting different BTC histories.

**Why the fixture is not inner-joined.** Each symbol runs as its own single-instrument
backtest (the N=1 case of D64), so D45's inner-join rule never binds. Inner-joining would
truncate all 63 coins to the youngest one's inception and delete most of the sample — the
finite-lived-instrument failure mode D84 identified, at cross-sectional scale.
