# D572 — FIXTURE: the CFTC Commitments of Traders fixture extended to the **six commodity roots the first fetch did not request** — soybean oil, soybean meal, heating oil, gasoline, platinum, palladium — so every one of the breadth fixture's 17 commodities has its positioning series

*2026-09-20. A data record, not a study. Written so that the hedging-pressure pre-registration
that follows it ranks the same 17 roots the three cross-sectional sorts (D557–D559) and basis-momentum
(D564) ranked, rather than the eleven the fixture covered. Fetched with the existing fetcher's
`--map`, `--fetch`, `--build` modes; no code path other than the symbol table changed.*

## What was added

| symbol | contract (resolved on the live API, never typed) | code | legacy from | disaggregated from |
|---|---|---|---|---|
| ZL | SOYBEAN OIL | 007601 | 1986-01-15 | 2006-06-13 |
| ZM | SOYBEAN MEAL | 026603 | 1986-01-15 | 2006-06-13 |
| HO | **NY HARBOR ULSD** | 022651 | 1986-01-15 | 2006-06-13 |
| RB | **GASOLINE RBOB** | 111659 | 2006-02-14 | 2006-06-13 |
| PL | PLATINUM | 076651 | 1986-01-15 | 2006-06-13 |
| PA | PALLADIUM | 075651 | 1986-01-15 | 2006-06-13 |

None has a TFF series (physical commodities), as expected and recorded as "no rows".

**Two more resolution traps, in the fetcher's own style.** `%HEATING OIL%` matches **only two
spread contracts** on the disaggregated dataset — ULSD versus heating oil, and heating oil versus
Rotterdam gasoil — and not the outright at all, which has been named `NY HARBOR ULSD` since the
2013 specification change; the map mode refused the pattern and the outright is pinned. `%RBOB%`
matches **ten** contracts (crack spreads, calendars, a first-line, a financial, regional
blendstock spreads); the outright is `GASOLINE RBOB`, pinned. Both refusals were the fetcher
doing what D262 built it to do: a hand-typed code for either would have returned a full,
plausible series for the wrong market.

## The fixture after the build

| | before (D262) | after |
|---|---:|---:|
| symbols | 28 | **34** |
| rows | 210,717 | **274,473** |
| span | 1986-01-15 → 2026-08-25 | 1986-01-15 → **2026-09-15** |
| families | legacy / disaggregated / TFF | unchanged; every row still carries its family |
| gates | 23 | 23, all green |
| identity `long + short + spread ≤ OI` | 100 % | 100 % |

**The span is uneven and the record says so.** The six new symbols were fetched on 2026-09-20 and
run to the 2026-09-15 report; the 28 original symbols' raw cache ends at the 2026-08-25 report
and was not re-fetched (the cache is the raw; re-fetching it to align three weekly reports would
be a change to the original series for no study's benefit). A study that pools symbols across the
last three weeks of the span must know this; every study in this programme filters to releases
before 2024-01-01 and is unaffected.

The panel itself is gitignored for size since D536 and is recorded in `data/data_manifest.json`
by hash; the map and the sidecar meta are tracked. The manifest is rebuilt in this commit.

## What this does not change

Nothing read by any earlier study: the 28 original symbols' rows are byte-identical (the build
is reproducible with `mtime=0` and the original series were not re-fetched). The hedging-pressure
pre-registration reads the legacy commercial category on the 17 commodity roots through 2023.
