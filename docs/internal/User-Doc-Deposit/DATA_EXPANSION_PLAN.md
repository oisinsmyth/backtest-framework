# Data Expansion Plan

**Status:** proposal, pre-implementation
**Current state:** Databento (GLBX.MDP3), ~2016–2026, futures
**Objective:** increase effective sample size and regime coverage without contaminating
the research already done, and without conflating data used for *signal validation* with
data used for *execution modelling*.

---

## 1. Why this is the highest-leverage change available

The binding constraint on this programme is not compute, not framework quality, and not
strategy ideas. It is sample size. Everything downstream — overfitting risk, drawdown
estimation, confidence in any feature — is a function of how much independent data exists.

**Current effective sample, honestly accounted:**

| Axis | Nominal | Effective |
|---|---|---|
| Calendar history | ~10 years | ~10 years |
| Instruments | ~40 liquid contracts | ~5–6 independent blocks (rates, equity, FX, energy, metals, ags) |
| Independent observations for a 60-day signal | ~40 per instrument | ~40 × 6 ≈ 240 |
| Major inflation shocks observed | 1 (2021–22) | 1 |
| Major liquidity crises observed | 1 (2020) | 1 |
| Rate-hiking cycles observed | 1 | 1 |

That last block is the real problem. Almost every regime-dependent claim you can make from
2016–2026 rests on a sample of one. A trend system validated on this window has never seen
1994, 1998, 2000–02, or 2008. A carry system has never seen a pre-ZIRP rate environment
for most of the sample.

**Deeper history is commercially available, cheap, and the single biggest improvement
available to this project.** The current 2016 start is a vendor and product limitation,
not a fact about the world.

---

## 2. Vendor landscape

### 2.1 What Databento is and is not good for

Databento's CME Globex (GLBX.MDP3) coverage now extends back to **June 6, 2010**, backfilled
from CME's legacy FIX/FAST feed via CME DataMine. Two provenance caveats apply to the
pre-May-2017 portion:

- The legacy protocol did not carry full MBO granularity, so **MBP-10 is the deepest
  schema available before May 2017**.
- Timestamps in the backfill (both `ts_recv` and `ts_event`) derive from the feed's
  SendingTime field rather than a capture timestamp, because CME does not hold PCAPs for
  that period.

**Immediate action, zero cost:** if the current pipeline starts at 2016, it is probably
starting there by default rather than by necessity. Extending the pull to 2010 adds ~60% more
history including the euro crisis, the 2011 downgrade, and the 2014–16 oil collapse, for the
price of a re-pull. Do this before anything else.

Beyond that, Databento's strength is granularity, not depth. It is the right tool for
execution modelling, cost calibration and microstructure features, and the wrong tool for
long-horizon feature validation.

### 2.2 Norgate Data — the primary recommendation

- ~100 futures markets across 11 exchange groups, coverage selective toward contracts with
  an established liquidity record.
- **History back to around 1980**, or to first trading day.
- Close prices are the official **settlement price**, not last trade. This matters: settlement
  is the price that determines margin and mark-to-market, and it is the correct close for
  daily research.
- Provides individual contracts *and* spot-month continuous series in **both unadjusted and
  back-adjusted form**, which is exactly the pair needed to keep signal generation and P&L
  computation separated.
- Back-adjustment is arithmetic (difference). Roll convention: business day prior to last
  trading day for cash-settled contracts, business day prior to First Notice Day for
  deliverable contracts.
- Native Python package (`norgatedata` on PyPI), plus a Zipline integration.
- **USD 270 / 12 months** for the futures package (USD 148.50 for 6 months). Cash commodities
  are included with a futures subscription.

**Operational constraints to plan around:**

- The database is local and **Windows-only** (or a Windows VM). Given a Linux/WSL research
  environment, budget for a VM or a Windows box that runs the updater and exports.
- **Access to the database ends when the subscription lapses.** Historical data is not sold
  standalone. Therefore: on day one, export the full history to Parquet and treat that
  export as the durable research artefact. Re-export on a schedule.
- Check the licence terms before publishing anything derived from the data.

### 2.3 CSI Data

The other established futures EOD vendor, commonly used alongside or instead of Norgate by
systematic futures traders. Worth a quote as a second source, mainly for the cross-vendor
reconciliation described in §5. Deep history, global coverage, long track record.

### 2.4 Pinnacle Data (CLC Database)

- Continuously-linked commodity contracts covering ~98 markets, with history starting
  **1969** for the oldest series (corn from 1970, coffee 1974, British pound 1976, crude oil
  1984, and so on).
- Also sells historical **Commitments of Traders** data and a deep individual-contract
  package (~10,000 historical contracts).
- Delivery format and website are dated; expect ASCII/MetaStock rather than an API.

Relevant only if you want pre-1980 depth — specifically the 1970s inflation regime and the
commodity shocks of that era. Genuinely valuable for validating carry and trend claims,
because those decades look nothing like the sample you have. Second-phase purchase, not first.

### 2.5 Free sources worth wiring in regardless

| Source | What it gives | Depth |
|---|---|---|
| **CFTC Commitments of Traders** | Weekly positioning by trader category | Back to 1986 (legacy format) |
| **FRED** | Rates, inflation, macro series for regime tagging | Decades |
| **AQR Data Library** | Published factor return series incl. time-series momentum and carry | Long, monthly |
| **Ken French Data Library** | Equity factor returns for cross-checks | Back to 1926 |
| **Exchange roll/expiry calendars** | Ground truth for roll schedule validation | Current + historical |
| **Index methodology PDFs (GSCI, BCOM)** | Published roll windows — forced-flow feature inputs | Current |

The AQR series in particular is a free, independent benchmark: if your TSMOM replication
does not correlate strongly with their published series over the overlapping period, your
harness has a bug. That is a cheap and decisive test.

---

## 3. Role separation (the architectural point)

The most important design decision here is to stop treating "market data" as one thing.
Three distinct jobs, three distinct datasets:

| Job | Dataset | Frequency | Why |
|---|---|---|---|
| **Feature validation** — does this signal predict returns? | Norgate (+ Pinnacle later) | Daily settlement | Depth and regime coverage dominate; granularity is irrelevant at 5–60 day horizons |
| **Execution and cost modelling** — what will this actually cost to trade? | Databento | Tick / MBP-10 | Granularity is the whole point; 2010 depth is ample for cost estimation |
| **Regime tagging and conditioning** | FRED, COT, cash indices | Weekly / monthly | Context variables, not price |

**Rule:** a feature is validated on deep daily data. A strategy's cost model is calibrated
on Databento. The two never swap roles. Writing this down now prevents the failure where a
promising daily signal quietly gets re-tested on intraday data and the extra history is lost.

---

## 4. Integration design

Keep the existing `data/` layer's shape and add vendor adapters behind one interface.

```
data/
    vendors/
        base.py              # VendorAdapter protocol
        databento.py         # existing wrapper, refactored to the protocol
        norgate.py           # new
        csi.py               # optional second source
        pinnacle.py          # optional, file-based loader
    contracts.py             # contract specs: point value, tick, currency, FND, LTD
    continuous.py            # roll schedule + back-adjustment, vendor-independent
    reconcile.py             # cross-vendor validation (see §5)
    store.py                 # Parquet layout, versioned
```

**Canonical schema.** One table shape regardless of vendor:

```
symbol, contract, date, open, high, low, close(settlement), volume, open_interest,
point_value, currency, first_notice_date, last_trading_date, vendor, ingest_version
```

Carrying `vendor` and `ingest_version` on every row is not optional. When results shift
after a data change you need to be able to attribute the shift.

**Store both series on the same row.** Follow the convention of keeping adjusted and
unadjusted prices together, so signal generation (adjusted) and execution/P&L (unadjusted,
actual contract) can coexist without ambiguity about which price was used where. This is
the single most common source of silent futures errors and the schema should make it
impossible to get wrong.

**Roll schedule as versioned configuration.** The roll rule is a research parameter.
Store it as a table with an explicit version, and record which version produced any given
result. Norgate's own convention (day before LTD / day before FND) is a reasonable default
and has the advantage of being documented, but do not let it be implicit.

---

## 5. Cross-vendor reconciliation (do this before trusting anything)

You will have **2016–2026 in both Databento and Norgate**. That overlap is an asset: it is a
free, decisive test of the data layer, and it will find the class of silent error that has
already bitten you.

Reconciliation suite:

1. **Settlement vs last-trade divergence.** Norgate closes are official settlements;
   Databento-derived closes are trade-based. Quantify the difference per contract. Large or
   systematic divergence in illiquid contracts is a signal that any feature relying on the
   close in those markets is suspect.
2. **Roll date agreement.** Compare vendor roll dates against your own volume/OI crossover
   rule. Every disagreement is a case to inspect manually.
3. **Back-adjustment reconstruction.** Recompute the adjusted series from unadjusted prices
   plus roll gaps, and check it reproduces the vendor's adjusted series. If it doesn't, your
   understanding of the adjustment is wrong — better to find that here than in a backtest.
4. **Contract spec agreement.** Point value, tick size, currency. A wrong point value
   silently rescales P&L and is invisible in a returns plot.
5. **Return distribution comparison.** Daily return moments per contract, both vendors.
   Differences beyond rounding indicate an alignment or timezone problem.
6. **Timezone and session alignment.** Contracts across exchanges do not settle
   simultaneously. Confirm which timestamp each vendor stamps a bar with. Misalignment here
   manufactures fake lead-lag relationships that look like excellent alpha.

Each of these becomes a test in the suite, run on every ingest. This is the futures
equivalent of sensor validation: cheap, unglamorous, and the reason the control loop doesn't
act on a bad reading.

---

## 6. The strategic point: the new history is a holdout you already own

This matters more than the engineering.

Everything researched so far has used 2016–2026. Once 1980–2015 arrives, **it is
uncontaminated out-of-sample data for every hypothesis formed to date** — 35 years of it,
spanning regimes the current sample does not contain. That is far more valuable than any
in-sample refinement.

It is also spendable exactly once.

**Protocol for the transition:**

1. **Before ingesting the deep history**, freeze and write down the current state: every
   feature under consideration, its mechanism, its predicted sign, its expected horizon,
   and the parameter values as currently set. Commit it. Timestamped.
2. **Ingest and reconcile** (§5) using only the 2016–2026 overlap. Data-layer validation is
   not a strategy test and does not spend the holdout.
3. **Run the frozen set once** against 1980–2015. Record results whatever they are.
4. **Interpret honestly.** Effect sizes will shrink. Some features will fail entirely. A
   feature that survives 1980–2015 at roughly the predicted magnitude is enormously stronger
   evidence than anything available from the current sample.
5. **Only then** resume open-ended research, now with 45 years as the working sample and
   a fresh multiplicity budget — with the test counter reset and documented, not silently
   continued.

Skipping step 1 converts 35 years of pristine out-of-sample data into 35 more years of
training data, and it is irreversible. Ingest the data *after* the freeze is written, not
before, so the temptation does not arise.

---

## 7. Phased plan

### Phase 0 — free, immediate
- [ ] Re-pull Databento back to 2010-06-06; confirm schema availability pre-2017 (MBP-10 max).
- [ ] Ingest CFTC COT history with correct release-date lagging.
- [ ] Ingest FRED regime series.
- [ ] Download AQR TSMOM/carry series as a replication benchmark.
- [ ] **Write the pre-registration freeze (§6 step 1).**

*Acceptance:* current features re-run on 2010–2026; any that break between 2016 and 2010–16
are flagged before more data arrives.

### Phase 1 — USD 270
- [ ] Subscribe to Norgate futures. Set up Windows VM + updater.
- [ ] Build `norgate.py` adapter to the canonical schema.
- [ ] **Export full history to Parquet immediately** and version it. Re-export monthly.
- [ ] Build and pass the §5 reconciliation suite on the 2016–2026 overlap.
- [ ] Replicate TSMOM and carry on 1980–2026; check correlation against the AQR series.

*Acceptance:* reconciliation suite green; published effects replicate at roughly published
magnitude. If they don't, the harness is broken — fix that before anything else. This is the
instrument-calibration step and it is not optional.

### Phase 2 — after Phase 1 produces results
- [ ] Run the frozen hypothesis set on 1980–2015. Once.
- [ ] Write up what survived and what didn't. The failures are the more valuable half.
- [ ] Optional: CSI quote as third-source reconciliation.
- [ ] Optional: Pinnacle CLC for 1969–1980 depth, if the 1970s inflation regime turns out to
      matter for the surviving features.

### Phase 3 — execution layer
- [ ] Use Databento intraday exclusively for cost calibration: realised spread, depth at
      touch, impact by participation rate, per contract and time of day.
- [ ] Feed measured costs back into `CostStack` and re-run Phase 2 survivors net of
      calibrated costs.

---

## 8. Budget

| Item | Cost | Priority |
|---|---|---|
| Databento re-pull to 2010 | £0 (existing usage) | Do now |
| COT, FRED, AQR, French | £0 | Do now |
| Norgate futures, 12 months | USD 270 | Phase 1 |
| Windows VM (if needed) | ~£0–15/mo | Phase 1 |
| CSI Data | quote required | Optional |
| Pinnacle CLC | quote required | Phase 2, optional |

Roughly £250–350 in year one to go from 10 years to 45 across ~100 markets. Against the cost
of a single failed prop evaluation, and against the cost of trading a strategy that was only
ever validated in one regime, this is not a close call.

---

## 9. Risks and caveats

- **Licensing.** Vendor data is licensed, not owned. Do not commit raw vendor data to a
  public repository. For the portfolio repo, commit the *code*, the reconciliation tests,
  and derived results/charts — never the underlying series. Check each vendor's terms before
  publishing any derived output.
- **Subscription lapse.** Norgate access ends with the subscription. The Parquet export is
  the mitigation, and it needs to be automated rather than remembered.
- **Backfill provenance.** Databento's pre-2017 history comes from a different feed with
  different timestamp semantics. Do not build a latency-sensitive or timestamp-sensitive
  feature that spans the May 2017 boundary without accounting for it.
- **Survivorship in futures.** Less severe than equities but real — contracts that died
  (and exchanges that delisted products) are missing from most coverage. Note it as a
  limitation rather than pretending it is solved.
- **More data ≠ more truth.** A 45-year sample tested a thousand ways is worse than a 10-year
  sample tested ten ways. The expansion buys statistical power only if the multiplicity
  discipline holds. Expanding the data is not a substitute for §6 of `FEATURE_RESEARCH.md`;
  it raises the ceiling on what that discipline can deliver.

---

## 10. Portfolio framing

This document is itself a portfolio artefact. A reviewer who sees a candidate reason
explicitly about settlement-vs-last-trade, roll conventions, cross-vendor reconciliation,
and the deliberate preservation of deep history as an untouched holdout will conclude —
correctly — that the candidate has done real futures work. That is a much rarer signal than
a good equity curve, and a much harder one to fake.
