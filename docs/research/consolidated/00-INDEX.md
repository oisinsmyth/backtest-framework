# Consolidated research index

**What this is.** A topic-first view over `docs/research/`, built 2026-09-10. The two campaigns are
organised by *round*; this tree is organised by *subject*, so a reader looking for "what do we know
about spread estimation" reads one short file instead of six round records.

**What this is NOT.** Not a replacement, not a summary that supersedes anything, and **not an
adjudication.** Every source file stays where it is, unedited. Nothing here elevates anything into
[`FINDINGS.md`](../../FINDINGS.md), [`RULES.md`](../../RULES.md) or the books — [R15](../../RULES.md#r15)
and the standing ruling at the top of [`../README.md`](../README.md) both still hold.

**One rule added for this tree, and it is the principal's instruction of 2026-09-10:**

> **Where research disagrees with a study already run in this repo, THE REPO'S MEASUREMENT IS TAKEN
> AS TRUE and the research reading is KEPT beside it, marked.** Research-versus-research conflicts
> stay unadjudicated exactly as before. Only the principal retires either side.

---

## Start here

| | |
|---|---|
| **[Conflicts vs the repo](conflicts/02-versus-repo-measurements.md)** | the 11 places external research and a measured study here point different ways |
| **[Agreements with the repo](conflicts/03-agreements.md)** | the 9 places an outside route landed on a number we had already measured |
| **[Conflict register](conflicts/01-register.md)** | all 51 cross-lane conflict IDs, one line each |
| **[Open questions](99-open-questions.md)** | what is unmeasured, and which are cheap |

## Topics

### [`signals/`](signals/00-index.md) — what might pay, and what died
[profitability family](signals/01-profitability-family.md) ·
[long leg vs short leg](signals/02-long-leg-versus-short-leg.md) ·
[construction dispersion](signals/03-construction-dispersion.md) ·
[decay and era](signals/04-decay-and-era.md) ·
[arrival and drawdown](signals/05-arrival-and-drawdown.md) ·
[share count and issuance](signals/06-share-count-and-issuance.md) ·
[short-side cross-section](signals/07-short-side-cross-sectional.md) ·
[structural decay instruments](signals/08-structural-decay-instruments.md) ·
[intraday and overnight](signals/09-intraday-and-overnight.md) ·
[**dead-lane register**](signals/10-dead-lanes.md)

### [`cost/`](cost/00-index.md) — what trading actually costs
[spread estimation](cost/01-spread-estimation.md) ·
[what anomalies pay](cost/02-what-anomalies-pay.md) ·
[the price floor](cost/03-price-floor-and-screens.md) ·
[equal-weight rebalancing bias](cost/04-equal-weight-bias.md) ·
[borrow and short financing](cost/05-borrow-and-financing.md)

### [`data/`](data/00-index.md) — what can be obtained, and what is broken in it
[SEC XBRL fundamentals](data/01-sec-xbrl-fundamentals.md) ·
[filing text and timestamps](data/02-filing-text-and-timestamps.md) ·
[corporate actions and splits](data/03-corporate-actions-and-splits.md) ·
[fixture and vendor defects](data/04-fixture-and-vendor-defects.md) ·
[futures data sources](data/05-futures-data-sources.md) ·
[purchase proposals](data/06-purchase-proposals.md)

### [`method/`](method/00-index.md) — how to measure it without fooling ourselves
[benchmark choice](method/01-benchmark-choice.md) ·
[nulls and block length](method/02-nulls-and-block-length.md) ·
[replication and multiple testing](method/03-replication-and-multiple-testing.md) ·
[research tooling hazards](method/04-tooling-hazards.md)

### [`venues/`](venues/00-index.md) — where a book could be run
[prop account arithmetic](venues/01-prop-account-arithmetic.md) ·
[prop rules and conduct](venues/02-prop-rules-and-conduct.md)

---

## Reading tags used throughout

| tag | meaning |
|---|---|
| `[REPO]` | measured in this repo. Under the ruling above, this is the true value |
| `[EXT]` | external evidence only. Never measured on this fixture |
| `[BRIEF]` | an agent measured a **public** file or endpoint — not this fixture |
| `[OPEN]` | nobody has measured it, here or outside |
| `[CONFLICT Xn]` | recorded in the [register](conflicts/01-register.md); **not settled** |

**Two provenance warnings that apply to every `[EXT]` line in this tree.** A figure obtained
through a summariser is **weaker** than `[snippet only]`, not stronger — four independent
fabrications were caught this way. And an **HTTP 200 can be wrong**: nine flavours catalogued,
including a CDN that replays another query's results and a host that serves a 404 page at a `.pdf`
URL. See [tooling hazards](method/04-tooling-hazards.md).

## Where the primary records live

| | |
|---|---|
| campaign 1 — six rounds, flat files | [`../README.md`](../README.md) §"The lead scan" |
| campaign 2 — `Scan-100926`, four rounds | [`../Scan-100926/00-SCHEMA.md`](../Scan-100926/00-SCHEMA.md) |
| earlier standalone work | [`../shorts/`](../shorts/) · [`../futures-data/`](../futures-data/) · [`../Prop-Firm-080926/`](../Prop-Firm-080926/) · [`../the-signal-hunt-part2.md`](../the-signal-hunt-part2.md) |
| the briefs themselves | `working/leads/` … `working/leads6/` — quarantined; a brief is evidence about the outside world, never a measurement on this fixture |
